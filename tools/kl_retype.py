#!/usr/bin/env python3
"""
Dead Men geometry classes that keep their own class in Dog Days (re/cars.md has the evidence).

kl_gms.RETYPE flattens six Dead Men classes. Five of them are still registered by kl2.exe with
the same own-level property list, the same pool category and live code, so they stay what they
are; only ZIngameMapGroup (not registered) needs another class:

    ZFFItemTemplateMultistage 0x100490   keep (systems side: a graft drops it with Dead Men's systems)
    ZSHADOWMESHOBJ            0x200110   keep
    ZPlant                    0x2000fd   keep (ZCloth-derived; HavokDeformation is owned by ZCloth)
    ZEnvSampler               0x20010f   keep
    ZHavokCar                 0x2000d4   keep (HavokCarScriptRout / VehicleWeapon are owned by it;
                                         VehicleEffects and PassengerAnimPos look for it by class)
    ZIngameMapGroup           0x100486   -> ZROOM, as before

What a kept object needs beyond "do not retype" (done here, each marked where it is a guess):
  * ZCloth gained a 3-float field in Dog Days (ZCloth[12]). kl_convert would fill it with Dog
    Days' most common value (0, 0, 8); a Dead Men cloth or plant gets (0, 0, 0): LEVEL_MAPS.
  * Sound handles (.SND offsets, type handlers 46 and 70: ZHavokCar[2] engine sound, ZLNKOBJ[1],
    ZCloth[10], ZCloth[11]) index Dead Men's bank: zeroed by finish(). kl_graft already zeroes
    them on every map node; a whole-level build (kl_package) does not.
  * ZLNKOBJ[2] of a car names an animation set. finish(have=...) empties the ones the shipped
    .ANM lacks (every stock Dog Days ZHeli, the only ZHavokLnkObj Dog Days levels use, has '').
Nothing else of a kept object is level-external data in the .prp: the chassis is the car's own
.HVK type 3 record (found through its REF id, kl2 0x86ad30), the wheel / engine set-up is a
table in the exe per EVehicleType (0x5d11b0), the cloth and plant blobs are .prm chunks whose
indices kl_prmgraph already follows (ZCloth[15], ZPlant[2]).

    python kl_retype.py table                 the classes of kl_gms.RETYPE in both executables
    python kl_retype.py test [maps]           convert with the classes kept and check; the last
                                              line must say "problems: 0" (exit code 1 otherwise)

Use from the converter (the change kl_gms / kl_convert / kl_graft need is in re/cars.md):
    with kl_retype.applied():                 kl_gms.RETYPE and kl_convert.LEVEL_MAPS as above
        conv = kl_retype.converter()
        data, tids, report = kl_retype.convert(prp_bytes, dm_tids, conv)
"""
import collections, contextlib, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_rtp, kl_hvk, kl_convert as K, kl_prmgraph as G, kl_prpjoin as J
from kl_prp import Prp, units
from kl_port_check import find, workdir, DD_GUESSES, DD_EXE

# the only retype that is still needed: Dog Days does not register ZIngameMapGroup; ZROOM is its
# base, it adds no properties and the .oct / .rmi name it as a room (kl_gms.RETYPE says the same)
RETYPE = {0x100486: 0x100021}
KEEP = {0x100490: 'ZFFItemTemplateMultistage', 0x200110: 'ZSHADOWMESHOBJ', 0x2000fd: 'ZPlant',
        0x20010f: 'ZEnvSampler', 0x2000d4: 'ZHavokCar'}
MAPS = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A', 'M09_A', 'M09_B']
SOUND_TYPES = (46, 70)          # re/kl2.json type handlers that hold a .SND offset (kl_graft.SOUND_TYPES)
ANMCOL = 'anmcol:animationdatabase#'
WHEELS = ('WheelLeftFront', 'WheelRightFront', 'WheelLeftRear', 'WheelRightRear')   # kl2 0xcf03d4..
VEHICLE = 3                     # .HVK shape type of a car / helicopter chassis (kl_hvk.VEHICLE)

# ZCloth: Dead Men has 15 stored fields, Dog Days 16. The new one is the float[3] at Dog Days
# index 12 (the only array, so the pairing itself is exact). Dog Days' ZCloth init (kl2 0x552ff0;
# Dead Men's 0x58d330 has no such step) sets a flag at +0xfc when the vector is longer than a
# threshold, i.e. the vector switches something on that Dead Men's cloth does not have.
# ASSUMPTION: (0, 0, 0) reproduces Dead Men's behaviour; what the vector is (wind, extra
# gravity) was not read. 124 of 694 stock Dog Days cloths store (0, 0, 0).
ZERO3 = [(0x01, struct.pack('<I', 3))] + [(0x0a, bytes(4))] * 3 + [(0x7c, b'')]
LEVEL_MAPS = {
    'ZCloth': {'map': {**{i: i for i in range(12)}, 13: 12, 14: 13, 15: 14}, 'values': {12: ZERO3}},
}


@contextlib.contextmanager
def applied():
    """kl_gms.RETYPE (the dict kl_convert, kl_graft, kl_package and verify_levels all read) and
    kl_convert.LEVEL_MAPS as this module wants them, restored on exit. A Converter caches its
    plans, so make it inside (converter())."""
    saved, maps = dict(kl_gms.RETYPE), dict(K.LEVEL_MAPS)
    kl_gms.RETYPE.clear(); kl_gms.RETYPE.update(RETYPE)
    K.LEVEL_MAPS.update(LEVEL_MAPS)
    try:
        yield
    finally:
        kl_gms.RETYPE.clear(); kl_gms.RETYPE.update(saved)
        K.LEVEL_MAPS.clear(); K.LEVEL_MAPS.update(maps)


def converter():
    """A kl_convert.Converter for kept classes. Call inside applied(). Its table of Dog Days'
    usual values has its own cache file: the set of wanted fields differs from kl_convert's."""
    conv = K.Converter(kl_rtp.Schema.load('dm'), kl_rtp.Schema.load('dd'))
    conv.learn_typical(find(DD_GUESSES, DD_EXE), os.path.join(workdir(), 'dd_typical_retype.json'))
    return conv


def dd_tids(tids):
    """Dog Days class id per node for Dead Men ids (node 0 is ROOT and has no .gms record)."""
    return [tids[0]] + [RETYPE.get(t, t) for t in tids[1:]]


def finish(p, tids, dd, have=None):
    """What a kept object needs after kl_convert (module docstring). p: Prp of the converted
    level, tids: its Dog Days class ids, have: animation set names of the .ANM that ships, or
    None to leave ZLNKOBJ[2] alone. Changes p in place, returns a Counter of what it did."""
    done = collections.Counter()
    for tid, node in zip(tids[1:], p.nodes()[1:]):
        if tid not in KEEP:
            continue
        fs, obj = dd.fields(KEEP[tid]), node['props']
        at, pos = [], 1                                  # token index of each field's first token
        for u in units(obj[1:-1]):
            at.append(pos); pos += len(list(u))
        lab = J.labels('dd', KEEP[tid])
        for i, f in enumerate(fs):
            op, pl = obj[at[i]]
            if f.type in SOUND_TYPES and f.kind == 'I' and any(pl):
                obj[at[i]] = (op, bytes(len(pl)))        # a Dead Men .SND offset: no such sound here
                done['sound handle zeroed: %s %s' % (KEEP[tid], lab[i])] += 1
            elif have is not None and lab[i] == 'ZLNKOBJ[2]' and p.key((op, pl)).startswith(ANMCOL):
                name = p.key((op, pl))
                if name not in have and name[len(ANMCOL):] not in have:
                    # ASSUMPTION: a ZHavokCar with no animation set is as harmless as a ZHeli
                    # with none (21 of 21 stock Dog Days helicopters); its passengers' door
                    # clips (PassengerAnimPos '/Vehicles/<set>/...') are then missing anyway
                    obj[at[i]] = (op, struct.pack('<I', p.key_index('')))
                    done['animation set emptied: %s' % name[len(ANMCOL):]] += 1
    return done


def convert(prp, tids, conv, have=None):
    """Dead Men .prp bytes + Dead Men class ids -> (Dog Days .prp bytes, Dog Days class ids,
    Counter). Call inside applied() with a converter() made there."""
    if kl_gms.RETYPE != RETYPE:
        raise ValueError('kl_retype.convert must run inside kl_retype.applied()')
    data, st = K.convert_level(prp, conv, tids)
    p, out = Prp(data), dd_tids(tids)
    st.update(finish(p, out, conv.dd, have))
    return p.serialize(), out, st


# ---------------------------------------------------------------- the classes in both executables
def table(log=print):
    """One block per class of kl_gms.RETYPE: registered, pool category, stored fields per class
    level in both games, and how kl_convert pairs them."""
    dm, dd = kl_rtp.Schema.load('dm'), kl_rtp.Schema.load('dd')
    conv = K.Converter(dm, dd)
    for old, new in kl_gms.RETYPE.items():
        name = dm.geoms.get(old)
        log('%s %#x (kl_gms.RETYPE -> %s)' % (name, old, dd.geoms.get(new)))
        log('  registered: Dead Men %s, Dog Days %s (instance size %s / %s); pool category %d, target %d' % (
            old in dm.geoms, old in dd.geoms, dm.data['geoms']['%#x' % old][1],
            dd.data['geoms'].get('%#x' % old, [None, None])[1], kl_gms.category(old), kl_gms.category(new)))
        if old not in dd.geoms:
            continue
        log('  bases: %s' % ' > '.join(dd.bases(name)[:-3]))
        sf, df = dm.fields(name), dd.fields(name)
        mine = dict(K._levels(sf))
        for owner, idx in K._levels(df):
            a = ' '.join(K.label(dm, sf[i]) for i in mine.get(owner, []))
            b = ' '.join(K.label(dd, df[i]) for i in idx)
            log('  %-26s %s' % (owner, 'same %d fields' % len(idx) if a == b else 'Dead Men: %s\n%29sDog Days: %s' % (a, '', b)))
        plan = conv.plan(name, name)
        new_fields = ['%s' % J.labels('dd', name)[i] for i, s in enumerate(plan) if s is None]
        log('  Dog Days fields with no Dead Men source: %s; assumed pairings: %s' % (
            new_fields, sorted(o for o, _ in K._levels(df) if o in conv.assumed) or 'none'))
        owned = sorted(n for n, es in dd.controllers.items() if any(e[0] == name for e in es))
        log('  controllers owned by the class itself: %s' % (owned or 'none'))


# ---------------------------------------------------------------- test
def _value(p, u):
    return K._resolve(p, u)


def expected(dm, dd, cls):
    """For each Dog Days field of a class both games have: the Dead Men field it must come from,
    or None for a field only Dog Days has. Worked out here without kl_convert (no difflib, no
    LEVEL_MAPS): per class level, Dead Men's field list has to be Dog Days' with fields left
    out, in exactly ONE way. Returns None when that does not hold (then nothing is 'exact')."""
    sf, df = dm.fields(cls), dd.fields(cls)
    mine, out = dict(K._levels(sf)), []
    for owner, didx in K._levels(df):
        sidx = mine.get(owner, [])
        a, b = [K.label(dm, sf[i]) for i in sidx], [K.label(dd, df[j]) for j in didx]
        ways = [[1] * (len(b) + 1)] + [[0] * (len(b) + 1) for _ in a]     # ways[i][j]: a[:i] inside b[:j]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                ways[i][j] = ways[i][j - 1] + (ways[i - 1][j - 1] if a[i - 1] == b[j - 1] else 0)
        if ways[len(a)][len(b)] != 1:
            return None
        i, part = len(a), []
        for j in range(len(b), 0, -1):                  # the one alignment, from the end
            if i and a[i - 1] == b[j - 1] and ways[i - 1][j - 1]:
                part.append(sidx[i - 1]); i -= 1
            else:
                part.append(None)
        out += part[::-1]
    return out


def check(level, conv, log=print):
    """Convert one Dead Men map with the classes kept and check it. Returns (problems, info):
    problems is a Counter that must be empty, info a Counter of what was seen."""
    dm, dd = conv.dm, conv.dd
    bad, info = collections.Counter(), collections.Counter()
    with zipfile.ZipFile(J.level_zip(level, 'dm')) as zf:
        stem = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0][:-4]
        prp, raw, buf = zf.read(stem + '.prp'), kl_gms.unpack(zf.read(stem + '.gms')), zf.read(stem + '.buf')
        hvk, prm = kl_hvk.Hvk(zf.read(stem + '.HVK')), G.read(zf.read(stem + '.prm'), 'dm')
    ents = kl_gms.entities(raw)
    tids = [kl_rtp.ROOT_TYPE] + [e[1] for e in ents]
    recs = [None] + [4 * (e[0] & 0xffffff) for e in ents]
    ref = lambda k: struct.unpack_from('<I', raw, recs[k] + 0x30)[0]
    name = lambda k: buf[struct.unpack_from('<I', raw, recs[k])[0]:].split(b'\0', 1)[0].decode('latin1')
    src = Prp(prp)
    src_nodes = src.nodes()
    parent, kids = {}, collections.defaultdict(list)
    for k, n in enumerate(src_nodes):                       # nodes() is depth first: children follow
        for c in n['children']:
            parent[id(c)] = k
    index = {id(n): k for k, n in enumerate(src_nodes)}
    for k, n in enumerate(src_nodes):
        for c in n['children']:
            kids[k].append(index[id(c)])
    up = {index[i]: k for i, k in parent.items()}

    data, out_tids, st = convert(prp, tids, conv)
    p = Prp(data)
    nodes = p.nodes()
    if len(nodes) != len(tids):
        bad['node count changed'] += 1
        return bad, info

    # 1. every object against Dog Days' classes, enums, registered controllers, item bindings
    import verify_levels
    bad.update(verify_levels.problems(conv, data, tids))

    # 2. kept objects: fit, exact values, owners of their controllers
    type3 = collections.Counter(kl_hvk.ref(i) for s in hvk.shapes if s.type == VEHICLE for i in s.inst)
    roots_dm = {(w[0], w[2]): (c, kind) for w, c, kind in G.prp_roots(src, tids, dm, 'dm') if w[0] != 'scene' and w[1] is None}
    roots_dd = {(w[0], w[2]): (c, kind) for w, c, kind in G.prp_roots(p, out_tids, dd, 'dd') if w[0] != 'scene' and w[1] is None}
    for k in range(1, len(tids)):
        tid = tids[k]
        cls = dd.geoms.get(out_tids[k])
        chain = dd.bases(cls)
        # controllers whose registered owner is not a base of the node (any class): the engine
        # does not enforce it (CLAUDE.md), stock levels have such pairs too, so this is counted,
        # and a problem only on a kept object
        for nm, body in nodes[k]['ctrls']:
            cn = p.key(nm)
            owners = set(e[0] for e in dd.controllers.get(cn, []))
            if owners and not owners & set(chain):
                if tid in KEEP:
                    bad['%s: controller %s is owned by %s' % (cls, cn, sorted(owners))] += 1
                elif owners & set(dd.geoms.values()):
                    info['other nodes: %s on a %s (owner %s)' % (cn, cls, sorted(owners))] += 1
        if tid not in KEEP:
            continue
        info['kept %s' % cls] += 1
        if cls != KEEP[tid] or dm.geoms[tid] != cls:
            bad['%s became %s' % (dm.geoms[tid], cls)] += 1
            continue
        why = dd.misfit(cls, nodes[k]['props'])
        if why:
            bad['%s: %s' % (cls, why)] += 1
            continue
        plan, want = conv.plan(cls, cls), expected(dm, dd, cls)
        su, du = units(src_nodes[k]['props'][1:-1]), units(nodes[k]['props'][1:-1])
        lab, fs = J.labels('dd', cls), dd.fields(cls)
        if want is None:
            bad['%s: the field lists of the two games do not align in one way only' % cls] += 1
            continue
        for i, s in enumerate(want):
            if (plan[i] if isinstance(plan[i], int) else None) != s:
                bad['%s %s: kl_convert takes it from %s, the field lists say %s' % (cls, lab[i], plan[i], s)] += 1
            elif s is None:
                info['%s %s: no Dead Men source, %s' % (cls, lab[i], 'fixed value' if isinstance(plan[i], list) else 'Dog Days default')] += 1
            elif _value(src, su[s]) != _value(p, du[i]):
                if fs[i].type in SOUND_TYPES and not any(list(du[i])[0][1]):
                    continue                             # zeroed by finish()
                bad['%s %s: value changed in conversion' % (cls, lab[i])] += 1
        if len(nodes[k]['ctrls']) != len(src_nodes[k]['ctrls']):
            lost = set(src.key(nm) for nm, _ in src_nodes[k]['ctrls']) - set(p.key(nm) for nm, _ in nodes[k]['ctrls'])
            info['%s: controllers the converter removed: %s' % (cls, sorted(lost))] += 1
        for nm, _ in nodes[k]['ctrls']:
            info['%s + %s' % (cls, p.key(nm))] += 1

        # 3. what each class needs from outside the .prp
        if cls == 'ZHavokCar':
            # the chassis: every .HVK type 3 shape placed on the car's own REF id (kl2 0x86ad30
            # collects them; one in 133 of 164 Dead Men cars, 4, 5 or 9 in the rest, never none).
            # Without one 0x72e160 returns before it builds the vehicle: a car with no body.
            if not type3[ref(k)]:
                bad['ZHavokCar %s: no .HVK vehicle shape for its REF id' % name(k)] += 1
            info['ZHavokCar: .HVK vehicle shapes on its REF id: %d' % type3[ref(k)]] += 1
            sib = [name(c) for c in kids[up[k]]]
            info['ZHavokCar: wheel entities among its siblings: %d of 4' % sum(w in sib for w in WHEELS)] += 1
            fx = [p.key(nm) for nm, _ in nodes[up[k]]['ctrls']]
            info['ZHavokCar: parent group has VehicleEffects: %s' % ('VehicleEffects' in fx)] += 1
            if dd.geoms.get(out_tids[up[k]]) != 'ZGROUP':
                info['ZHavokCar: parent is a %s' % dd.geoms.get(out_tids[up[k]])] += 1
            info['ZHavokCar: animation set %s' % _value(src, su[[i for i, l in enumerate(J.labels('dm', cls)) if l == 'ZLNKOBJ[2]'][0]])[0][1][1][len(ANMCOL):]] += 1
            if any(p.key(nm) == 'VehicleWeapon' for nm, _ in nodes[k]['ctrls']):
                info['ZHavokCar: has VehicleWeapon (fills the list at car +0x96c)'] += 1
        elif cls == 'ZPlant':
            fd = {l: i for i, l in enumerate(lab)}
            fm = {l: i for i, l in enumerate(J.labels('dm', cls))}
            for a, b, kind in (('ZCloth[14]', 'ZCloth[15]', 'cloth'), ('ZPlant[2]', 'ZPlant[2]', 'plant')):
                s, d = roots_dm.get((k, fm[a])), roots_dd.get((k, fd[b]))
                if s is None or d != s or s[1] != kind:
                    bad['ZPlant: %s chunk index not followed (%s -> %s)' % (kind, s, d)] += 1
            cloth, plant = roots_dm.get((k, fm['ZCloth[14]'])), roots_dm.get((k, fm['ZPlant[2]']))
            if cloth and plant:
                # plant blob: u32 n, n x {u16 a, b, c; u16; f32; f32} (the loop at kl2 0x7ab5c0 /
                # Dead Men 0x58e120, same in both), a, b, c = particles of the cloth blob (+0x0c)
                blob, pts = prm.chunks[plant[0]], prm.u32(cloth[0], 0x0c)
                n = struct.unpack_from('<I', blob, 0)[0]
                if (4 + 16 * n + 15) & ~15 != len(blob):
                    bad['ZPlant: plant chunk is not u32 n + 16 n bytes'] += 1
                elif any(v >= pts for i in range(n) for v in struct.unpack_from('<3H', blob, 4 + 16 * i)):
                    bad['ZPlant: plant chunk names a particle the cloth chunk does not have'] += 1
        elif cls == 'ZEnvSampler':
            info['ZEnvSampler: slot %d' % struct.unpack('<I', list(du[lab.index('ZEnvSampler[0]')])[0][1])[0]] += 1
        elif cls == 'ZSHADOWMESHOBJ':
            if any(list(du[lab.index('ZSHADOWMESHOBJ[0]')])[0][1]):
                info['ZSHADOWMESHOBJ[0] not zero'] += 1
    for what, n in st.items():
        if what.startswith(('sound handle', 'animation set')):
            info[what] += n

    # 4. the cloth / plant blobs in the converted .prm of kl_dmassets, if it was written
    done = os.path.join(workdir(), 'build', 'FA', level, os.path.basename(stem) + '.prm')
    if os.path.isfile(done) and any(t == 0x2000fd for t in tids):
        with open(done, 'rb') as f:
            q = G.read(f.read(), 'dd')
        for (k, _f), (c, kind) in roots_dm.items():
            if kind in ('cloth', 'plant') and tids[k] == 0x2000fd:
                same = c < len(q.chunks) and q.chunks[c] == prm.chunks[c]
                info['converted .prm: %s chunk of a ZPlant %s' % (kind, 'unchanged' if same else 'CHANGED OR MOVED')] += 1
                bad['converted .prm: %s chunk of a ZPlant changed or moved' % kind] += not same
    return +bad, info


def test(levels, log=print):
    total = 0
    with applied():
        conv = converter()
        for lv in levels:
            bad, info = check(lv, conv, log)
            total += sum(bad.values())
            log('%s' % lv)
            for what, n in sorted(info.items()):
                log('    %-74s %d' % (what, n))
            log('  problems: %d %s' % (sum(bad.values()), bad.most_common(12)))
        for what in ('blank default (Dog Days levels never store this field)', 'default was a Dog Days scene path: left empty',
                     'enum value replaced', 'list data dropped', 'array resized'):
            hit = {k: v for k, v in conv.report.get(what, {}).items() if any(c in k for c in KEEP.values())}
            if hit:
                log('%s (kept classes): %s' % (what, hit))
        log('assumed pairings on kept classes: %s' % (sorted(o for c in KEEP.values() for o, _ in K._levels(conv.dd.fields(c)) if o in conv.assumed) or 'none'))
    log('problems: %d' % total)
    return total


def main():
    args = sys.argv[1:]
    if args[:1] == ['table']:
        table()
    elif args[:1] == ['test']:
        sys.exit(1 if test(args[1:] or MAPS) else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
