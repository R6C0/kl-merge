#!/usr/bin/env python3
"""
Convert Dead Men level property files (.prp) to the Dog Days layout.

An object in a .prp is the serialized properties of its class, in the order the engine's
reflection tables give and without names. kl_rtp.py reads those tables from both executables
(re/kaneandlynch.json, re/kl2.json), so each Dead Men object is rebuilt field by field into
exactly what Dog Days reads for that class:

  1. A field both games have keeps its value. Arrays whose length changed are padded with zeros
     or cut; enum values Dog Days lacks are replaced (listed in the log).
  2. A field only Dog Days has gets the value Dog Days' own levels store there most often, or
     zero/empty if its levels never store that class.
  3. A field only Dead Men has is dropped.
  4. Controllers Dog Days does not register are removed (listed in the log).

Fields are paired per class level (ZGEOM, ZSTDOBJ, ...) by type and enum, in order. The
executables hold no property names, so when a level gained a field next to others of the same
type, WHICH of them is the new one is an assumption (the pairing keeps the earlier ones); the log
lists those levels under "assumed". Nothing here is taken from level statistics except the
default values of rule 2.

Nothing in either game folder is changed. Output goes to <work folder>/converted/<level>/.

    python kl_convert.py                 (Fragile Alliance maps, auto-finds games)
    python kl_convert.py --all           (every Dead Men level)
    python kl_convert.py --only M01_FA_A (one level folder)
"""
import collections, difflib, json, os, struct, sys, time, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_prp import Prp, signature, units, kind
from kl_port_check import find, level_zips, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE
import kl_gms, kl_rtp
from kl_gms import RETYPE

FA_LEVELS = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A']
ROOT = kl_rtp.ROOT_TYPE
SCALAR = {'c': (0x05, 1), 'b': (0x06, 1), 'B': (0x07, 1), 'h': (0x08, 2), 'I': (0x09, 4),
          'f': (0x0a, 4), 'd': (0x0b, 8)}


def unit_sig(u):
    u = list(u)
    if u[0][0] == 0x04:
        return 'i'                      # plain int or reference list
    return signature(u)

def csig(obj):
    """Layout of an object with reference lists collapsed."""
    return '{' + ''.join(unit_sig(u) for u in units(body(obj))) + '}'

def body(obj):           # strip outer { }
    return obj[1:-1]

def wrap(inner):
    return [(0x02, b'')] + inner + [(0x7e, b'')]


# Dead Men weapon/item enum -> Dog Days item enum (exe table; each Dog Days item may be bound
# once per level, except eFF2ItemNoItem). Items Dog Days has no equivalent for become NoItem.
ITEM_RENAME = {
    'eFF2ItemPistolHKUSP': 'eFF2ItemHG_SigSauer226',
    'eFF2ItemPistolHKUSPCarry': 'eFF2ItemHG_M9Beretta',
    'eFF2ItemPistolHKUSPLight': 'eFF2ItemHG_SW_MP45',
    'eFF2ItemPistolHKUSPSilenced': 'eFF2ItemHG_M9Beretta_Silenced',
    'eFF2ItemPistolTaurus': 'eFF2ItemHG_TaurusJudge',
    'eFF2ItemSMGFNP90': 'eFF2ItemSMG_UMP',
    'eFF2ItemSMGHKMP5': 'eFF2ItemSMG_Type05',
    'eFF2ItemSMGHKMP5Light': 'eFF2ItemSMG_Type79',
    'eFF2ItemSMGSteyrTMP': 'eFF2ItemSMG_MAC_10',
    'eFF2ItemRifleAK74': 'eFF2ItemRifle_AK74',
    'eFF2ItemRifleM4': 'eFF2ItemRifle_FN_SCAR',
    'eFF2ItemRifleM4Light': 'eFF2ItemRifle_Type81',
    'eFF2ItemRifleRugerMini14': 'eFF2ItemRifle_Zastavam85',
    'eFF2ItemRifleSG552': 'eFF2ItemRifle_Type95',
    'eFF2ItemFNMinimiSPW': 'eFF2ItemMG_MiniMi_SPW',
    'eFF2ItemFNMinimiSPWHeli': 'eFF2ItemMG_MiniMi_SPW_Heli',
    'eFF2ItemShotgunRemington870': 'eFF2ItemShotgun_Remington_870',
    'eFF2ItemShotgunSpas12': 'eFF2ItemShotgun_Spas_12',
    'eFF2ItemSniperRemington700': 'eFF2ItemSn_Rem700',
    'eFF2ItemSniperRemington700Silenced': 'eFF2ItemRifle_Type88_Scoped',
    'eFF2ItemGrenadeFrag': 'eFF2ItemGrenade_Frag',
    'eFF2ItemGrenadeGas': 'eFF2ItemGrenade_Gas',
    'eFF2ItemGrenadeIncendiary': 'eFF2ItemGrenade_Incendiary',
    'eFF2ItemGrenadeSmoke': 'eFF2ItemGrenade_Smoke',
    'eFF2ItemGrenadeLauncherFlare': 'eFF2ItemGrenadeLauncher_Flare',
    'eFF2ItemGrenadeLauncherGas': 'eFF2ItemGrenadeLauncher_Gas',
    'eFF2ItemRocketLauncherHind': 'eFF2ItemRocketLauncher_Hind',
    'eFF2ItemRocketLauncherInaccurate': 'eFF2ItemNoItem',
    'eFF2ItemPushblade': 'eFF2ItemNoItem',
    'eFF2ItemBombC4': 'eFF2ItemNoItem',
    'eFF2ItemClaymore': 'eFF2ItemNoItem',
    'eFF2ItemNotInUse': 'eFF2ItemNoItem',
}

# Pairings the executables cannot give. Key: the class level; value: Dog Days field index within
# that level -> Dead Men field index, plus fixed values for Dog Days fields that have no source.
#
# ZSquadScript: Dead Men has attitude, alertness, bool, 12 message lists, bool, uint. Dog Days
# added a game-type enum after attitude and 3 message lists. Which Dog Days list each Dead Men
# list became (SQUAD_LISTS) comes from the earlier comparison of both games' levels, not from
# the executables: treat it as a carried-over assumption.
SQUAD_LISTS = [0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13]
LEVEL_MAPS = {
    # The HUD. Dead Men: CharObj, fonts Text / Header / DebugText, ...; Dog Days: CharObj, fonts
    # H1 / H2 / H3 / DebugText, ... (seen in the values of both games' levels). Pairing by type
    # alone put the new font first and left CharObj empty: ZCheckpointDisplay then resolves REF 0
    # (kl2 0x742d6a). H3 has no Dead Men font: it reuses Header, which is a GUESS.
    'ZOnScreenDisplay2': {
        'map': {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8},
        'values': {},
    },
    'ZSquadScript': {
        'map': dict([(0, 0), (2, 1), (3, 2), (19, 15), (20, 16)] + [(4 + d, 3 + k) for k, d in enumerate(SQUAD_LISTS)]),
        'values': {1: [(0x0e, ('KEY', 'eAllTypes'))]},
    },
}


# Controllers Dog Days registers but that cannot work on converted data yet. They are removed and
# reported; each entry says what is missing.
UNSUPPORTED = {
    # Its two shorts index a table of physics-animation sets (0x5c bytes each, at [0xdd2598]+0x10)
    # that is empty for a converted level, so its init reads through null (kl2 0x5dafdd, 73 % load).
    # The table presumably comes from the level's Havok file, copied from Dead Men as it is - not
    # established. Without it the hanging lamps of M01 do not swing.
    'PhysicsBasedAnimated': 'needs the physics-animation table',
}


def rename_keys(p, table):
    """Rename strings in the .prp key table (every token using them follows)."""
    changed = 0
    for i, k in enumerate(p.keys):
        if k in table:
            p.keys[i] = table[k]; changed += 1
    if changed:
        p.keyblob = b''.join(k.encode('latin1') + b'\0' for k in p.keys)
    return changed


def node_types(zf, prp_name):
    """Class id of every .prp node as the level's .gms stores it: ROOT (a ZROOM) first, then the
    entity table in order. None if the archive has no matching .gms."""
    gms = prp_name[:-4] + '.gms'
    if gms not in zf.namelist():
        return None
    return [ROOT] + [e[1] for e in kl_gms.entities(kl_gms.unpack(zf.read(gms)))]


def _resolve(p, unit):
    """Turn key-index payloads into text so values can move between files."""
    out = []
    for op, pl in unit:
        if op in (0x0c, 0x0e):
            out.append((op, ('KEY', p.key((op, pl)))))
        elif op == 0x0f:
            n = struct.unpack_from('<I', pl)[0]
            out.append((op, ('KEYS',) + tuple(p.keys[i] for i in struct.unpack_from('<%dI' % n, pl, 4))))
        else:
            out.append((op, pl))
    return tuple(out)

def _materialize(p, unit):
    out = []
    for op, pl in unit:
        if isinstance(pl, tuple) and pl[0] == 'KEY':
            out.append((op, struct.pack('<I', p.key_index(pl[1]))))
        elif isinstance(pl, tuple) and pl[0] == 'KEYS':
            out.append((op, struct.pack('<%dI' % len(pl), len(pl) - 1, *[p.key_index(s) for s in pl[1:]])))
        else:
            out.append((op, pl))
    return out


def label(schema, f):
    """What must agree for a Dead Men field and a Dog Days field to be the same property."""
    if f.kind in ('e', 'k'):
        return f.kind + ':' + (schema.enums[f.enum]['name'] if f.enum else '?')
    if f.kind and '*' in f.kind:
        return f.kind.split('*')[0] + '*'            # the length may differ: resized
    if f.kind in ('refs', 'raw', 'cont'):
        return 'list'
    return f.kind or '?'


def _levels(fields):
    """[(owner, [field indices])] in order."""
    out = []
    for i, f in enumerate(fields):
        if not out or out[-1][0] != f.owner:
            out.append((f.owner, []))
        out[-1][1].append(i)
    return out


class Converter:
    """Dead Men object -> Dog Days object, by the two games' class schemas."""

    def __init__(self, dm, dd):
        self.dm, self.dd = dm, dd
        self.options = {k: set(n for n, _v in e['options']) for k, e in dd.enums.items()}
        self.typical = {}                            # Dog Days field key -> its usual value
        self._plans = {}
        self.assumed = {}                            # class level -> why its pairing is an assumption
        self.report = collections.defaultdict(collections.Counter)

    def plan(self, src_cls, dst_cls):
        """For each Dog Days field of dst_cls: the Dead Men field index it takes its value from,
        a fixed value, or None (use the default). None for the whole plan if either game lacks
        the class or Dog Days has a field whose shape is unknown."""
        key = (src_cls, dst_cls)
        if key in self._plans:
            return self._plans[key]
        src, dst = self.dm.fields(src_cls), self.dd.fields(dst_cls)
        plan = None
        if src is not None and dst is not None and all(f.kind for f in dst):
            plan = [None] * len(dst)
            mine = dict(_levels(src))
            for owner, didx in _levels(dst):
                sidx = mine.get(owner)
                if sidx is None:
                    continue                         # a class level Dead Men does not have
                if owner in LEVEL_MAPS:
                    m = LEVEL_MAPS[owner]
                    for j, i in m['map'].items():
                        plan[didx[j]] = sidx[i]
                    for j, value in m['values'].items():
                        plan[didx[j]] = value
                    continue
                a = [label(self.dm, src[i]) for i in sidx]
                b = [label(self.dd, dst[j]) for j in didx]
                for tag, a0, a1, b0, b1 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
                    if tag == 'equal':
                        for k in range(a1 - a0):
                            plan[didx[b0 + k]] = sidx[a0 + k]
                        continue
                    # a change next to a field of the same type could sit one place further along
                    near = set(a[max(0, a0 - 1):a0] + a[a1:a1 + 1] + b[max(0, b0 - 1):b0] + b[b1:b1 + 1])
                    if tag == 'replace' or near & (set(a[a0:a1]) | set(b[b0:b1])):
                        self.assumed[owner] = 'Dead Men %s -> Dog Days %s' % (','.join(a), ','.join(b))
        self._plans[key] = plan
        return plan

    def wanted(self):
        """Dog Days field keys whose usual value may be needed: fields Dead Men lacks, and enums
        (a Dead Men value Dog Days does not have is replaced by the usual one)."""
        keys = set()
        pairs = [(c, self.dd.geoms.get(RETYPE.get(t, t))) for t, c in self.dm.geoms.items()]
        pairs += [(e[1], d[1]) for n, es in self.dm.controllers.items() for e in es
                  for d in self.dd.controllers.get(n, [])]
        for s, d in pairs:
            plan = self.plan(s, d) if d else None
            if plan:
                keys.update(f.key for f, src in zip(self.dd.fields(d), plan) if src is None or f.kind == 'e')
        return keys

    def learn_typical(self, game, cache=None):
        """Count, over Dog Days' own levels, the value each wanted field holds."""
        want = self.wanted()
        stamp = self.dd.data['exe']['timestamp']
        if cache and os.path.isfile(cache):
            c = json.load(open(cache))
            if c.get('exe') == stamp and want <= set(c['seen']):
                self.typical = {k: tuple((op, tuple(pl) if isinstance(pl, list) else bytes.fromhex(pl)) for op, pl in v)
                                for k, v in c['values'].items()}
                return
        counts = {k: collections.Counter() for k in want}
        picks = {}
        def count(p, cls, obj):
            if cls not in picks:
                picks[cls] = [(i, f.key) for i, f in enumerate(self.dd.fields(cls) or []) if f.key in counts]
            if picks[cls]:
                us = units(body(obj))
                for i, k in picks[cls]:
                    counts[k][_resolve(p, us[i])] += 1
        zips = sorted(level_zips(game))
        for n, z in enumerate(zips, 1):
            print('\r  reading Dog Days default values %d/%d' % (n, len(zips)), end='', flush=True)
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    tids = node_types(zf, name) if name.lower().endswith('.prp') else None
                    if not tids:
                        continue
                    p = Prp(zf.read(name))
                    nodes = p.nodes()
                    if len(nodes) != len(tids):
                        continue
                    for tid, node in zip(tids, nodes):
                        cls = self.dd.geoms[tid]
                        count(p, cls, node['props'])
                        for nm, obj in node['ctrls']:
                            impl = self.dd.controller(p.key(nm), cls)
                            if impl:
                                count(p, impl, obj)
        print()
        self.typical = {k: c.most_common(1)[0][0] for k, c in counts.items() if c}
        if cache:
            json.dump({'exe': stamp, 'seen': sorted(want),
                       'values': {k: [(op, list(pl) if isinstance(pl, tuple) else pl.hex()) for op, pl in v]
                                  for k, v in self.typical.items()}}, open(cache, 'w'))

    def blank(self, f):
        """Zero / empty value of a field, for classes Dog Days' levels never store."""
        k = f.kind
        if k in SCALAR:
            return [(SCALAR[k][0], b'\0' * SCALAR[k][1])]
        if k == 's':
            return [(0x0c, ('KEY', ''))]
        if k == 'e':
            return [(0x0e, ('KEY', self.dd.enums[f.enum]['options'][0][0]))]
        if k == 'k':
            return [(0x0f, ('KEYS',))]
        if '*' in k:
            el, n = k.split('*')
            return [(0x01, struct.pack('<I', int(n)))] + [(SCALAR[el][0], b'\0' * SCALAR[el][1])] * int(n) + [(0x7c, b'')]
        return [(0x04, b'\0\0\0\0')]                 # refs / raw / cont

    def default(self, p, f, who):
        v = self.typical.get(f.key)
        if v is not None and any(isinstance(pl, tuple) and any(s.startswith('ROOT') for s in pl[1:]) for _op, pl in v):
            # Dog Days' usual value is a path to an object of ITS levels (a muzzle flash, an exit
            # vehicle): here it would dangle. Every scene path in a stock level resolves.
            self.report['default was a Dog Days scene path: left empty'][who + ' ' + f.owner] += 1
            v = self.blank(f)
        elif v is None:
            self.report['blank default (Dog Days levels never store this field)'][who + ' ' + f.owner] += 1
            v = self.blank(f)
        return _materialize(p, v)

    def value(self, p, u, sf, df, who):
        """A Dead Men value in the shape and range of the Dog Days field it was paired with."""
        u = list(u)
        if df.kind == 'e':
            name = p.key(u[0])
            if name not in self.options[df.enum]:
                self.report['enum value replaced'][name + ' (' + self.dd.enums[df.enum]['name'] + ')'] += 1
                return self.default(p, df, who)
        elif df.kind == 'k':
            names = _resolve(p, u)[0][1][1:]
            keep = tuple(n for n in names if n in self.options[df.enum])
            if len(keep) != len(names):
                self.report['flag dropped'][','.join(set(names) - set(keep))] += 1
                return _materialize(p, [(0x0f, ('KEYS',) + keep)])
        elif df.kind != sf.kind and '*' in df.kind:
            el, n = df.kind.split('*')
            inner = (u[1:-1] + [(SCALAR[el][0], b'\0' * SCALAR[el][1])] * int(n))[:int(n)]
            self.report['array resized'][who + ' ' + sf.kind + ' -> ' + df.kind] += 1
            return [(0x01, struct.pack('<I', int(n)))] + inner + [u[-1]]
        elif df.kind != sf.kind and kind(u) not in ('cont', df.kind):
            # refs / raw / cont: Dog Days stores another list type here, or never stores anything
            self.report['list data dropped'][who + ' ' + kind(u) + ' -> ' + df.kind] += 1
            return [(0x04, b'\0\0\0\0')]
        return u

    def object(self, p, src_cls, dst_cls, obj, who):
        """Rebuild one object. None when it cannot be converted (the report says why)."""
        plan = self.plan(src_cls, dst_cls)
        if plan is None:
            self.report['not convertible (class missing or a field of unknown shape)'][who] += 1
            return None
        src, dst = self.dm.fields(src_cls), self.dd.fields(dst_cls)
        us = units(body(obj))
        if len(us) != len(src):
            raise ValueError('%s: %d fields in the level, Dead Men class %s has %d' % (who, len(us), src_cls, len(src)))
        out = []
        for f, s in zip(dst, plan):
            if s is None:
                out += self.default(p, f, who)
            elif isinstance(s, list):
                out += _materialize(p, s)
            else:
                out += self.value(p, us[s], src[s], f, who)
        if any(f.owner in self.assumed for f in dst):
            self.report['assumed pairing'][who] += 1
        return wrap(out)


def convert_level(data, conv, tids):
    """Dead Men .prp bytes + its node class ids -> (Dog Days .prp bytes, counters)."""
    p = Prp(data)
    st = collections.Counter()
    st['items_renamed'] = rename_keys(p, ITEM_RENAME)
    nodes = p.nodes()
    if len(tids) != len(nodes):
        raise ValueError('scene file and property file disagree on entity count')
    dm, dd = conv.dm, conv.dd
    for k, (tid, node) in enumerate(zip(tids, nodes)):
        src = dm.geoms[tid]
        dst = dd.geoms.get(tid if k == 0 else RETYPE.get(tid, tid))       # node 0 is ROOT, not in the .gms
        new = conv.object(p, src, dst, node['props'], 'node ' + src) if dst else None
        if new is None:
            raise ValueError('no Dog Days class for Dead Men %s (%#x): add it to kl_gms.RETYPE' % (src, tid))
        node['props'] = new
        st['entities'] += 1
        st['entities_retyped'] += src != dst
        keep = []
        for name, obj in node['ctrls']:
            nm = p.key(name)
            simpl, dimpl = dm.controller(nm, src), dd.controller(nm, dst)
            if nm in UNSUPPORTED:
                conv.report['controller removed'][nm + ' (' + UNSUPPORTED[nm] + ')'] += 1
                st['ctrl_removed'] += 1
                continue
            new = conv.object(p, simpl, dimpl, obj, 'controller ' + nm) if simpl and dimpl else None
            if new is None:
                # not registered by Dog Days (the engine could not create it), or not convertible
                conv.report['controller removed'][nm + ('' if dimpl else ' (not in Dog Days)')] += 1
                st['ctrl_removed'] += 1
                continue
            st['ctrl_kept'] += 1
            keep.append((name, new))
        node['ctrls'] = keep
    out = p.serialize()
    Prp(out)        # must parse back
    return out, st


def converter(dd_dir, work=None):
    """A Converter with Dog Days' default values loaded (cached in the work folder)."""
    conv = Converter(kl_rtp.Schema.load('dm'), kl_rtp.Schema.load('dd'))
    conv.learn_typical(dd_dir, os.path.join(work or workdir(), 'dd_typical.json'))
    return conv


def main():
    args = sys.argv[1:]
    dm = find(DM_GUESSES, DM_EXE); dd = find(DD_GUESSES, DD_EXE)
    paths = [a for a in args if not a.startswith('--') and os.path.isdir(a)]
    if len(paths) >= 2: dm, dd = paths[:2]
    while not dm or not os.path.isfile(os.path.join(dm, DM_EXE)):
        dm = input('Path to Kane & Lynch: Dead Men folder: ').strip().strip('"')
    while not dd or not os.path.isfile(os.path.join(dd, DD_EXE)):
        dd = input('Path to Kane & Lynch 2: Dog Days folder: ').strip().strip('"')
    loc = os.path.join(dm, 'Scenes', 'Locations')
    if '--all' in args:
        levels = sorted(os.listdir(loc))
    elif '--only' in args:
        levels = [args[args.index('--only') + 1]]
    else:
        levels = FA_LEVELS
    t0 = time.time()
    work = workdir()
    conv = converter(dd, work)
    outroot = os.path.join(work, 'converted')
    summary = {}
    for lv in levels:
        for zname in sorted(os.listdir(os.path.join(loc, lv))):
            if not zname.lower().endswith('.zip') or 'loader' in zname.lower():
                continue
            with zipfile.ZipFile(os.path.join(loc, lv, zname)) as zf:
                for n in zf.namelist():
                    tids = node_types(zf, n) if n.lower().endswith('.prp') else None
                    if not tids:
                        continue
                    out, st = convert_level(zf.read(n), conv, tids)
                    od = os.path.join(outroot, lv); os.makedirs(od, exist_ok=True)
                    open(os.path.join(od, os.path.basename(n)), 'wb').write(out)
                    summary[lv + '/' + os.path.basename(n)] = dict(st)
                    print('%s: %s' % (lv + '/' + os.path.basename(n), dict(st)))
    for what, c in sorted(conv.report.items()):
        print('  %s: %s' % (what, c.most_common(40)))
    print('  assumed (new field next to same-typed ones; position not provable): %s' % sorted(conv.assumed))
    os.makedirs(outroot, exist_ok=True)
    json.dump({'levels': summary, 'report': {k: dict(v) for k, v in conv.report.items()}, 'assumed': conv.assumed},
              open(os.path.join(outroot, 'conversion_log.json'), 'w'), indent=1)
    print('done in %.0fs -> %s' % (time.time() - t0, outroot))


if __name__ == '__main__':
    main()
    if os.name == 'nt' and len(sys.argv) == 1:
        input('\nPress Enter to close...')
