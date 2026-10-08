#!/usr/bin/env python3
"""
Convert Dead Men level property files (.prp) to the Dog Days layout.

What it does to each Dead Men level:
  1. Base-class fix: inserts the extra bool Dog Days added after the first int of
     every entity's shared base properties (value false, as in all Dog Days levels).
  2. Controllers Dog Days doesn't have are removed (listed in the log).
  3. Controllers whose saved layout changed are re-laid-out: fields are matched
     against the layout Dog Days' own levels use, matching fields are kept, new
     fields get the value Dog Days uses most often, removed fields are dropped.
  4. Everything is checked against Dog Days: each entity and controller is
     marked "known layout" if Dog Days levels use exactly that layout.

Nothing in either game folder is changed. Output goes to ./converted/<level>/.

    python kl_convert.py                 (Fragile Alliance maps, auto-finds games)
    python kl_convert.py --all           (every Dead Men level)
    python kl_convert.py --only M01_FA_A (one level folder)
"""
import collections, difflib, json, os, struct, sys, time, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_prp import Prp, signature
from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

FA_LEVELS = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A']
FALSE = (0x06, b'\x00')


def units(tokens):
    """Split an object's inner tokens into field units. Arrays/sub-objects are one unit, and so is
    a reference list: an int count n followed by n strings (both games write entity-reference
    lists that way, without array markers)."""
    out, i, n = [], 0, len(tokens)
    while i < n:
        op = tokens[i][0]
        if op in (0x01, 0x02):
            close = 0x7c if op == 0x01 else 0x7e
            j, depth = i + 1, 1
            while depth:
                o = tokens[j][0]
                if o == op: depth += 1
                elif o == close: depth -= 1
                j += 1
            out.append(tokens[i:j]); i = j
        elif op == 0x04:
            c = struct.unpack('<I', tokens[i][1])[0]
            j = i + 1 + c
            if 0 < c and j <= n and all(tokens[k][0] == 0x0c for k in range(i + 1, j)):
                out.append(tokens[i:j]); i = j
            elif 0 < c and i + 1 < n and tokens[i + 1][0] == 0x0d and len(tokens[i + 1][1]) == 4 + c:
                out.append(tokens[i:i + 2]); i += 2          # byte count + raw block
            else:
                out.append(tokens[i:i + 1]); i += 1
        else:
            out.append(tokens[i:i + 1]); i += 1
    return out

def unit_sig(u):
    u = list(u)
    if u[0][0] == 0x04:
        return 'i'                      # plain int or reference list
    return signature(u)

def is_list(u):
    return u[0][0] == 0x04 and len(u) > 1

def csig(obj):
    """Layout of an object with reference lists collapsed (what the reader actually expects)."""
    return '{' + ''.join(unit_sig(u) for u in units(body(obj))) + '}'

def body(obj):           # strip outer { }
    return obj[1:-1]

def wrap(inner):
    return [(0x02, b'')] + inner + [(0x7e, b'')]


def base_fix(props):
    """props: tokens incl. braces. Insert bool after e [..] [..] b I if not already there."""
    u = units(body(props))
    s = [unit_sig(x) for x in u]
    if len(s) >= 5 and s[0] == 'e' and s[1].startswith('[') and s[2].startswith('[') and s[3] == 'b' and s[4] == 'I':
        u.insert(5, [FALSE])
        return wrap([t for x in u for t in x]), True
    return props, False


from kl_gms import RETYPE
import kl_relayout as RL

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


def _load_enums():
    import json
    try:
        t = json.load(open(os.path.join(HERE, 'dd_enums.json')))
    except OSError:
        return {}
    out = {}
    for run in t:
        names = frozenset(s for _, s in run)
        for s in names:
            out[s] = out.get(s, frozenset()) | names
    return out

DD_ENUMS = _load_enums()         # value name -> every name of its Dog Days enum (from kl2.exe)


def enum_ok(value, seen):
    """value is valid where Dog Days levels used `seen`: either seen, or in the same exe enum."""
    if value in seen:
        return True
    return any(value in DD_ENUMS.get(v, ()) for v in seen)


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
    """Class id of every .prp node: ROOT (ZROOM) first, then the .gms entity table in order."""
    import kl_gms
    gms = prp_name[:-4] + '.gms'
    if gms not in zf.namelist():
        return None
    raw = kl_gms.unpack(zf.read(gms))
    t = struct.unpack_from('<I', raw, 0)[0]
    n = struct.unpack_from('<I', raw, t)[0]
    out = [0x100021]
    for i in range(n):
        decl = struct.unpack_from('<I', raw, t + 4 + 8 * i)[0]
        tid = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff) + 0x14)[0]
        out.append(RETYPE.get(tid, tid))
    return out


def node_types_raw(zf, prp_name):
    """Like node_types but with the Dead Men class ids as stored (no RETYPE)."""
    import kl_gms
    gms = prp_name[:-4] + '.gms'
    if gms not in zf.namelist():
        return None
    raw = kl_gms.unpack(zf.read(gms))
    t = struct.unpack_from('<I', raw, 0)[0]
    n = struct.unpack_from('<I', raw, t)[0]
    out = [0x100021]
    for i in range(n):
        decl = struct.unpack_from('<I', raw, t + 4 + 8 * i)[0]
        out.append(struct.unpack_from('<I', raw, 4 * (decl & 0xffffff) + 0x14)[0])
    return out


class DDReference:
    """Layouts and typical values from every Dog Days level."""
    def __init__(self, dd):
        self.node_sigs = collections.Counter()
        self.ctrl = collections.defaultdict(collections.Counter)       # name -> csig -> count
        self.samples = collections.defaultdict(list)                    # (key,csig) -> few unit lists
        self.cls = collections.defaultdict(collections.Counter)        # class id -> csig -> count
        self.enums = collections.defaultdict(set)                      # (key,csig,idx) -> enum values
        self.lists = collections.defaultdict(lambda: [0, 0])           # (key,csig,idx) -> [list seen, nonzero int seen]
        self.alen = collections.defaultdict(set)                       # (key,csig,idx) -> array lengths seen
        self.fam = {}                                                  # enum value -> family (union-find)
        zips = []
        for dp, _, fs in os.walk(os.path.join(dd, 'Scenes')):
            for f in fs:
                if f.lower().endswith('.zip'):
                    z = os.path.join(dp, f)
                    # a converted map installed into a Dog Days slot is not a Dog Days reference:
                    # read the backed-up original instead
                    bak = os.path.join(dd, 'KL_PortBackup', os.path.relpath(z, dd))
                    zips.append(bak if os.path.isfile(bak) else z)
        for k, z in enumerate(sorted(zips), 1):
            print('\r  learning Dog Days layouts %d/%d' % (k, len(zips)), end='', flush=True)
            with zipfile.ZipFile(z) as zf:
                for n in zf.namelist():
                    if not n.lower().endswith('.prp'):
                        continue
                    p = Prp(zf.read(n))
                    nodes = p.nodes()
                    types = node_types(zf, n)
                    if types is not None and len(types) != len(nodes):
                        types = None
                    for k, node in enumerate(nodes):
                        us = units(body(node['props']))
                        sg = csig(node['props'])
                        self.node_sigs[sg] += 1
                        if types:
                            key = ('<class>', types[k])
                            self.cls[types[k]][sg] += 1
                            self._learn(p, key, sg, us, 100)
                        self._learn(p, '<entity>', sg, us, 200)
                        for name, obj in node['ctrls']:
                            nm, sg = p.key(name), csig(obj)
                            self.ctrl[nm][sg] += 1
                            self._learn(p, nm, sg, units(body(obj)), 400)
        # values of one exe enum are one family even if levels use them in different places
        for names in set(DD_ENUMS.values()):
            known = [v for v in names if v in self.fam]
            for v in known[1:]:
                a, b = self._find(known[0]), self._find(v)
                if a != b:
                    self.fam[b] = a
        print()

    def _learn(self, p, key, sg, us, cap):
        sm = self.samples[(key, sg)]
        if len(sm) < cap:
            sm.append([_resolve(p, x) for x in us])
        prev = None
        for i, u in enumerate(us):
            op = u[0][0]
            if op == 0x0e and len(u) == 1:
                v = p.key(u[0])
                self.enums[(key, sg, i)].add(v)
                self._union(v, (key, sg, i))
            elif op == 0x01:
                self.alen[(key, sg, i)].add(struct.unpack('<I', u[0][1])[0])
            elif op == 0x04:
                if len(u) > 1:
                    self.lists[(key, sg, i)][0] = 1
                elif u[0][1] != b'\0\0\0\0':
                    self.lists[(key, sg, i)][1] = 1

    def _find(self, v):
        while self.fam.get(v, v) != v:
            v = self.fam[v]
        return v

    def _union(self, v, pos):
        a, b = self._find(v), self._find(pos)
        if a != b:
            self.fam[a] = b

    def label(self, unit, text=None):
        """Alignment label of a unit: enums carry their value family so that fields of different
        enum types never line up with each other."""
        u = list(unit)
        if u[0][0] == 0x0e and len(u) == 1:
            if text is None:
                pl = u[0][1]
                text = pl[1] if isinstance(pl, tuple) else None
            f = self._find(text) if text in self.fam else None
            if f is None:                       # unused in levels but listed in the exe enum
                for other in sorted(DD_ENUMS.get(text, ())):
                    if other in self.fam:
                        f = self._find(other); break
            return 'e:%r' % (f,) if f is not None else 'e?' + str(text)
        return unit_sig(u)

    def samples_keys(self, key):
        return {sg for (k, sg) in self.samples if k == key}

    def default_unit(self, name, sig, idx):
        c = collections.Counter(tuple(s[idx]) for s in self.samples[(name, sig)] if idx < len(s))
        return list(c.most_common(1)[0][0]) if c else None


def _resolve(p, unit):
    """Turn key-index payloads into ('KEY', text) so values can move between files."""
    out = []
    for op, pl in unit:
        if op in (0x0c, 0x0e):
            out.append((op, ('KEY', p.key((op, pl)))))
        else:
            out.append((op, pl))
    return tuple(out)

def _materialize(p, unit):
    out = []
    for op, pl in unit:
        if isinstance(pl, tuple) and pl and pl[0] == 'KEY':
            out.append((op, struct.pack('<I', p.key_index(pl[1]))))
        else:
            out.append((op, pl))
    return out


def _labels(p, ref, us):
    return [ref.label(u, p.key(u[0]) if (u[0][0] == 0x0e and len(u) == 1) else None) for u in us]


def _apply(p, ref, key, target, src):
    """Lay src units out as Dog Days layout `target`. Returns (obj or None, approximate?)."""
    tgt = ref.samples[(key, target)][0]
    tgt_lab = [ref.label(u) for u in tgt]
    src_lab = _labels(p, ref, src)
    sm = difflib.SequenceMatcher(a=src_lab, b=tgt_lab, autojunk=False)
    out, approx = [], False
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal':
            out += src[a0:a1]
            continue
        if tag != 'insert':
            approx = True            # a Dead Men field had no clean Dog Days match
        for bi in range(b0, b1):     # new / changed fields take Dog Days' typical value
            d = ref.default_unit(key, target, bi)
            if d is None:
                return None, approx
            out.append(_materialize(p, d))
    new = wrap([t for u in out for t in u])
    return (new, approx) if csig(new) == target else (None, approx)


def fix_values(p, ref, key, obj):
    """Enum values Dog Days never uses at that field, and ints sitting where Dog Days expects a
    reference list (or the reverse), are replaced with Dog Days' typical value."""
    sg = csig(obj)
    us = units(body(obj))
    n = 0
    for i, u in enumerate(us):
        op = u[0][0]
        bad = False
        if op == 0x0e and len(u) == 1:
            vals = ref.enums.get((key, sg, i))
            bad = vals is not None and not enum_ok(p.key(u[0]), vals)
        elif op == 0x04:
            seen_list, seen_int = ref.lists.get((key, sg, i), (0, 0))
            if is_list(u) and not seen_list:
                bad = True
            elif not is_list(u) and u[0][1] != b'\0\0\0\0' and not seen_int:
                bad = True       # a count Dog Days never uses here: its reader would expect items
        if op == 0x01:
            fixed = resize_array(u, ref.alen.get((key, sg, i)))
            if fixed is not None:
                us[i] = fixed; n += 1
            continue
        if bad:
            d = ref.default_unit(key, sg, i)
            if d is not None:
                us[i] = _materialize(p, d); n += 1
    return (wrap([t for u in us for t in u]) if n else obj), n


def resize_array(u, lengths):
    """Dog Days readers of some arrays expect a fixed element count. If every Dog Days level uses
    one length here and ours differs, pad with zero-valued elements (or trim)."""
    if not lengths or len(lengths) != 1:
        return None
    want = next(iter(lengths))
    u = list(u)
    have = struct.unpack('<I', u[0][1])[0]
    inner = u[1:-1]
    if have == want or len(inner) != have or any(op in (0x01, 0x02, 0x0d, 0x0f) for op, _ in inner):
        return None                               # only flat scalar arrays
    if want < have:
        inner = inner[:want]
    else:
        op = inner[-1][0] if inner else 0x09
        size = {0x04: 4, 0x05: 1, 0x06: 1, 0x07: 1, 0x08: 2, 0x09: 4, 0x0a: 4, 0x0b: 8, 0x0c: 4, 0x0e: 4}[op]
        zero = (op, b'\0' * size)
        if op in (0x0c, 0x0e) and inner:
            zero = inner[-1]                      # keep key references valid
        inner = inner + [zero] * (want - have)
    return [(0x01, struct.pack('<I', want))] + inner + [u[-1]]


# Dead Men ZSquadScript: attitude, alertness, bool, 12 message lists, bool, uint.
# Dog Days added a mode enum after attitude and 3 message lists. Dead Men list k -> Dog Days list:
SQUAD_LISTS = [0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13]

def squad_script(p, obj):
    us = units(body(obj))
    if [unit_sig(u) for u in us] != list('eeb') + ['i'] * 12 + list('bI'):
        return obj
    lists = [[(0x04, b'\0\0\0\0')] for _ in range(15)]
    for k, d in enumerate(SQUAD_LISTS):
        lists[d] = us[3 + k]
    mode = [(0x0e, struct.pack('<I', p.key_index('eAllTypes')))]
    new = [us[0], mode, us[1], us[2]] + lists + us[15:]
    return wrap([t for u in new for t in u])


SPECIAL = {'ZSquadScript': squad_script}


def relayout_exact(p, ref, key, dm_cls, dd_cls, obj):
    """Field-by-field relayout from the exes' property schemas. None when a schema is missing."""
    dmf, ddf = RL.fields('dm', dm_cls), RL.fields('dd', dd_cls)
    if not dmf or not ddf:
        return None
    src = units(body(obj))
    pairs = RL.align(dmf, ddf, src)
    if pairs is None:
        return None
    target = '{' + RL.letters(ddf) + '}'
    if target not in ref.samples_keys(key):
        target = None                         # Dog Days never saved this class: defaults unknown
    out, approx = [], False
    for i, (f, u) in enumerate(pairs):
        if u is not None:
            out.append(list(u)); continue
        d = ref.default_unit(key, target, i) if target else None
        if d is None:
            d = zero_unit(f[1], p); approx = True
            if d is None:
                return None
        else:
            d = _materialize(p, d)
        out.append(d)
    new = wrap([t for u in out for t in u])
    if csig(new) != '{' + RL.letters(ddf) + '}':
        return None
    return new, ('approx' if approx else 'converted')


def zero_unit(letter, p):
    z = {'i': (0x04, b'\0' * 4), 'b': (0x06, b'\0'), 'B': (0x07, b'\0'), 'h': (0x08, b'\0\0'),
         'I': (0x09, b'\0' * 4), 'f': (0x0a, b'\0' * 4), 'd': (0x0b, b'\0' * 8), 'c': (0x05, b'\0'),
         's': (0x0c, struct.pack('<I', p.key_index(''))), 'k': (0x0f, b'\0' * 4)}
    if letter in z:
        return [z[letter]]
    if letter == '[f*]':
        return [(0x01, struct.pack('<I', 3))] + [(0x0a, b'\0' * 4)] * 3 + [(0x7c, b'')]
    if letter == '[I*]':
        return [(0x01, struct.pack('<I', 0)), (0x7c, b'')]
    return None


def relayout(p, ref, name, obj):
    """Controller -> (new_obj or None, how)."""
    known = ref.ctrl.get(name)
    if not known:
        return None, 'unknown'
    if name in SPECIAL:
        obj = SPECIAL[name](p, obj)
    ex = None
    if csig(obj) not in known:
        dm_cls, dd_cls = RL.controller_class('dm', name), RL.controller_class('dd', name)
        if dm_cls and dd_cls:
            ex = relayout_exact(p, ref, name, dm_cls, dd_cls, obj)
    if csig(obj) in known:
        new, how = obj, 'same'
    elif ex is not None:
        new, how = ex
        how = 'exact' if how == 'converted' else 'exact-approx'
    else:
        new, approx = _apply(p, ref, name, known.most_common(1)[0][0], units(body(obj)))
        if new is None:
            return None, 'failed'
        how = 'approx' if approx else 'converted'
    new, nfix = fix_values(p, ref, name, new)
    return new, how


def relayout_entity_cls(p, ref, props, tid, dm_tid=None):
    """Entity of known class -> Dog Days layout of that same class."""
    known = ref.cls.get(tid)
    if not known:
        return None
    key = ('<class>', tid)
    sig = csig(props)
    if sig in known:
        return fix_values(p, ref, key, props)[0], 'same'
    dm_cls, dd_cls = RL.class_name('dm', dm_tid if dm_tid is not None else tid), RL.class_name('dd', tid)
    if dm_cls and dd_cls:
        ex = relayout_exact(p, ref, key, dm_cls, dd_cls, props)
        if ex is not None:
            new, how = ex
            return fix_values(p, ref, key, new)[0], 'exact' if how == 'converted' else 'exact-approx'
    src = units(body(props))
    src_lab = _labels(p, ref, src)
    best, score = None, -1.0
    for cand in known:
        cu = [ref.label(u) for u in ref.samples[(key, cand)][0]]
        r = difflib.SequenceMatcher(a=src_lab, b=cu, autojunk=False).ratio()
        if r > score:
            best, score = cand, r
    new, approx = _apply(p, ref, key, best, src)
    if new is None:
        return props, 'unmatched'
    return fix_values(p, ref, key, new)[0], 'approx' if approx else 'converted'


_node_target = {}
def relayout_entity(p, ref, props):
    """Entity properties -> (new_props, how). Class isn't known, so pick the closest
    Dog Days layout that shares the base-class fields."""
    sig = csig(props)
    if sig in ref.node_sigs:
        return props, 'same'
    src = units(body(props))
    src_sig = [unit_sig(u) for u in src]
    if sig not in _node_target:
        best, score = None, 0.0
        for cand in ref.node_sigs:
            cu = [unit_sig(u) for u in ref.samples[('<entity>', cand)][0]]
            if cu[:6] != src_sig[:6]:
                continue
            r = difflib.SequenceMatcher(a=src_sig, b=cu, autojunk=False).ratio()
            if r > score:
                best, score = cand, r
        _node_target[sig] = best if score >= 0.75 else None
    target = _node_target[sig]
    if target is None:
        return props, 'unmatched'
    new, approx = _apply(p, ref, '<entity>', target, src)
    if new is None:
        return props, 'unmatched'
    return new, 'approx' if approx else 'converted'


def convert_level(data, ref, log, types=None, raw_types=None):
    p = Prp(data)
    st = collections.Counter()
    st['items_renamed'] = rename_keys(p, ITEM_RENAME)
    nodes = p.nodes()
    if types is not None and len(types) != len(nodes):
        raise ValueError('scene file and property file disagree on entity count')
    for k, node in enumerate(nodes):
        st['entities'] += 1
        r = None
        if types and raw_types:
            # exact schema path first, on the untouched Dead Men layout
            key = ('<class>', types[k])
            dm_cls, dd_cls = RL.class_name('dm', raw_types[k]), RL.class_name('dd', types[k])
            if dm_cls and dd_cls and types[k] in ref.cls:
                ex = relayout_exact(p, ref, key, dm_cls, dd_cls, node['props'])
                if ex is not None:
                    new, how = ex
                    r = (fix_values(p, ref, key, new)[0], 'exact' if how == 'converted' else 'exact-approx')
        if r is None:
            node['props'], fixed = base_fix(node['props'])
            st['base_fixed'] += fixed
            r = relayout_entity_cls(p, ref, node['props'], types[k]) if types else None
        if r is None:
            r = relayout_entity(p, ref, node['props'])
            st['class_unknown_in_dd'] += 1
        node['props'], how = r
        st['entity_' + how] += 1
        keep = []
        for name, obj in node['ctrls']:
            nm = p.key(name)
            new, how = relayout(p, ref, nm, obj)
            log[nm][how] += 1
            if new is None:
                st['ctrl_removed'] += 1
                continue
            st['ctrl_' + how] += 1
            keep.append((name, new))
        node['ctrls'] = keep
    out = p.serialize()
    Prp(out)        # must parse back
    return out, st


def main():
    args = sys.argv[1:]
    dm = find(DM_GUESSES, DM_EXE); dd = find(DD_GUESSES, DD_EXE)
    paths = [a for a in args if not a.startswith('--')]
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
    ref = DDReference(dd)
    outroot = os.path.join(HERE, 'converted')
    summary = {}
    for lv in levels:
        for zname in sorted(os.listdir(os.path.join(loc, lv))):
            if not zname.lower().endswith('.zip') or 'loader' in zname.lower():
                continue
            with zipfile.ZipFile(os.path.join(loc, lv, zname)) as zf:
                for n in zf.namelist():
                    if not n.lower().endswith('.prp'):
                        continue
                    log = collections.defaultdict(collections.Counter)
                    out, st = convert_level(zf.read(n), ref, log, node_types(zf, n))
                    od = os.path.join(outroot, lv); os.makedirs(od, exist_ok=True)
                    open(os.path.join(od, os.path.basename(n)), 'wb').write(out)
                    summary[lv + '/' + os.path.basename(n)] = {'stats': dict(st), 'controllers': {k: dict(v) for k, v in sorted(log.items())}}
                    e = st['entities']
                    print('%s\n  entities    %6d: already matching %d, converted %d, approximate %d, unmatched %d (class not used by Dog Days: %d)'
                          % (lv + '/' + os.path.basename(n), e, st['entity_same'], st['entity_converted'], st['entity_approx'], st['entity_unmatched'], st['class_unknown_in_dd']))
                    print('  controllers %6d: already matching %d, converted %d, approximate %d, removed %d'
                          % (sum(st[k] for k in ('ctrl_same', 'ctrl_converted', 'ctrl_approx', 'ctrl_removed')),
                             st['ctrl_same'], st['ctrl_converted'], st['ctrl_approx'], st['ctrl_removed']))
    os.makedirs(outroot, exist_ok=True)
    json.dump(summary, open(os.path.join(outroot, 'conversion_log.json'), 'w'), indent=1)
    print('done in %.0fs -> %s' % (time.time() - t0, outroot))


if __name__ == '__main__':
    main()
    if os.name == 'nt' and len(sys.argv) == 1:
        input('\nPress Enter to close...')
