#!/usr/bin/env python3
"""
Dead Men guns as SWITCHABLE LOOKS of Dog Days guns (owner, 2026-10-09). Offline builder; NOT RUN IN THE GAME YET.

    python kl_guns.py survey                         the pairs below: both models' bones, parts, size
    python kl_guns.py build <base> <out folder> [--level=M01_FA_A] [--slot=F01]
                                                     base = a stock level name or a build folder. Writes the level
                                                     with the looks, KLGuns.ini and guns.json
    python kl_guns.py sheet <build folder> <out.png> every look next to and over its Dog Days gun (kl_view)

WHY LOOKS AND NOT NEW GUNS (kl2.exe build 0490, read 2026-10-09)
  - The game has exactly 64 weapon items (enum eFF2Item*, eFF2ItemCount = 64; tools/dd_enums.json) and the buy
    menu sells 36 of them: a table of 36 records of 24 bytes at 0xbd1f70 {price, unlock rank, tier, DLC id, item,
    ammunition} read as `[index * 24 + 0xbd1f70]` (0x6a5260 price, 0x8a3e40 rank, 0x808220 availability). The
    table is in .rdata inside a hashed range (klranges.h): it cannot be extended or re-pointed.
  - A gun is one template in the level's equipment tree: ZFFItemTemplateWeapon with a child `Ground` (ZLNKOBJ,
    variant 0) whose model is the gun. Stats, sounds and the animation set belong to the TEMPLATE.
  - The models of both games are the same thing: rigid parts (mesh sub type 2: +0x38 = 1, +0x3c = the bone the
    part hangs on), bones GROUND / w_bone_frame / w_bone_clip / w_bone_slide / w_bone_hammer / 'l hand attacher' /
    'spine1 attacher', the same axes, scale and grip place (seen with kl_view: MP5 over the Zastava).
  So a Dead Men gun becomes more PARTS of a Dog Days gun's model, hidden until asked for; price, rank, stats,
  sound and animation stay the Dog Days gun's.

WHAT A BUILD CHANGES
  .prm   the Dead Men gun models join the file (kl_chars.put with picks that have no target: converted model,
         materials, textures). For every Dog Days gun of LOOKS a NEW root = a copy of its root with an object
         table of  [the stock parts, variant 0] + per look [copies of that gun's parts, variant 100 + look number]
         A copy is 64 bytes; the geometry below is shared. Its bone is the Dog Days gun's bone of the same NAME
         (a bone that gun lacks - Dead Men's hammer on a rifle - is its nearest ancestor that exists; GROUND
         always does). ASSUMPTION: a part's vertices are in model space (the pictures agree), so a part on a bone
         that rests elsewhere sits right at rest and turns about the Dog Days gun's pivot when the bone moves.
  .oct   one record per new root (a copy of the stock root's empty tree).
  .gms / .prp  every entity that had the stock root gets the new one.
  A gun entity's variant is 0, so with nothing else done the level looks and plays as before: 100 + n matches
  nothing. ASSUMPTION (as for the heisters' variants, re/wardrobe.md): an object is drawn when its variant byte
  equals the entity's.
  KLGuns.ini  beside the archive: per gun its item number, root, and how many parts the stock gun and each look
         have, in object-table order. The hook (klhook/klchar.c, [Guns]) switches a look on by writing variant
         bytes in the loaded .prm: the chosen group gets 0, every other group its 100 + n. Heap data only.
         It changes the gun for EVERYONE who carries that item in the level - enemies and AI heisters too.

NOT DONE: the shop's name and picture of a switched gun (the name is a .LOC text of the level, the picture an
entity of the level's menu scene), moving parts tuned per gun (a Dead Men magazine turns about the Dog Days
gun's magazine pivot), the Ruger Mini-14 and the Taurus revolver (in no Dead Men level's equipment tree that was
read: all 20), the PKM (no machine gun is sold).
"""
import collections, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_chars as C, kl_gms, kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_prpjoin as J
from kl_prp import units

BS = chr(92)
HIDDEN = 100                                     # variant of a part that is not shown: 100 = stock parts, 100 + n = look n
# Dog Days template, item number (eFF2Item*), [(label, game, template of the gun whose parts it gets)]
LOOKS = [
    ('Rifle_zastavam85', 29, [('MP5', 'dm', 'Smg_MP5-A3_01'), ('AK-74', 'dd', 'Rifle_AK74')]),     # the starting rifle
    ('Rifle_FN_SCAR',    30, [('SG 552', 'dm', 'Rifle_SG552_01')]),                               # the owner's pairing: the SCAR's sound
    ('Rifle_AK47',       31, [('M4A1', 'dm', 'Rifle_M4A1_01')]),
    ('SMG_UMP',          20, [('P90', 'dm', 'Smg_FN_P90_01')]),
    ('SMG_MAC_10',       23, [('Steyr TMP', 'dm', 'Smg_SteyrTMP_01')]),
    ('HG_M9Beretta',      8, [('USP', 'dm', 'HG_HK_USP_01')]),
]


def gun_node(sc, template):
    """Node of <...>\\Weapon\\<template>\\Ground; exactly one."""
    tail = BS + 'Weapon' + BS + template + BS + 'Ground'
    hits = [k for k in range(1, len(sc.nodes)) if sc.path[k].endswith(tail)]
    if len(hits) != 1:
        raise ValueError('%s: %d weapon templates named %s' % (sc.label, len(hits), template))
    return hits[0]


def _retarget(sc, raw, models, k, new):
    off, was = models[k - 1]
    struct.pack_into('<I', raw, off, new)
    lab = J.labels('dd', sc.cls(k)); node = sc.nodes[k]
    us = [list(u) for u in units(node['props'][1:-1])]
    i = lab.index('ZGEOM[4]')
    us[i] = [(us[i][0][0], struct.pack('<I', new))]
    node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]


def _part(p, o, src_names, src_par, dst, variant, note):
    """A copy of rigid part `o` for the skeleton whose {lower-case bone name: index} is dst."""
    c = p.chunks[o]
    if len(c) != 64 or c[0x0c] != 2 or p.u32(o, 0x38) != 1:
        raise ValueError('object %d is not a rigid part on one bone' % o)
    b = p.u32(o, 0x3c)
    while src_names[b].lower() not in dst:
        b = src_par[b]; note['folded'] += 1
    c = c[:0x0f] + bytes([variant]) + c[0x10:]
    c = C._put(c, 0x3c, '<I', dst[src_names[b].lower()])
    i = C._new(p, c); p.refs[i] = p.refs[o]
    return i


def build(base, level='M01_FA_A', log=print):
    """base: kl_chars.Lv (edited in place). -> report dict."""
    sc, raw = base.scene()
    for t, _item, looks in LOOKS:                   # all the Dog Days guns must be there before anything is changed
        gun_node(sc, t)
    src = C.Source.get(level, log)
    picks = [C.Pick((), level, src.sc.path[gun_node(src.sc, tpl)][5:], {0: 0}) for _t, _i, looks in LOOKS for _l, game, tpl in looks if game == 'dm']
    rep = C.put(base, picks, free='none', log=log)
    dm_root = {}
    it = iter(rep['picks'])
    for _t, _i, looks in LOOKS:
        for _l, game, tpl in looks:
            if game == 'dm':
                dm_root[tpl] = next(it)['new_model']
    sc, raw = base.scene(); raw = bytearray(raw)
    models = C.gms_models(raw)
    p, mat = G.read(base['.prm'], 'dd'), T.read_mat(base['.MAT'])
    oct_s = O.Oct.parse(base['.oct'])
    refs0 = oct_s.record_refs(); rec_of = {v: k for k, v in enumerate(refs0)}
    guns, note, new_roots = [], dict(folded=0), []
    for tpl, item, looks in LOOKS:
        k = gun_node(sc, tpl)
        old, var, _aset = C.person(sc, k)
        if var != 0 or {p.chunks[o][0x0f] for o in C.objects(p, old)} != {0}:
            raise ValueError('%s: the gun or its parts are not variant 0' % tpl)
        sk = C.skeleton(p, old)
        dst = {s.lower(): i for i, s in enumerate(C.bone_names(p, sk))}
        objs = list(C.objects(p, old)); counts = []
        for n, (label, game, stpl) in enumerate(looks, 1):
            sroot = dm_root[stpl] if game == 'dm' else C.person(sc, gun_node(sc, stpl))[0]
            ssk = C.skeleton(p, sroot)
            names, par = C.bone_names(p, ssk), C.bone_parents(p, ssk)
            parts = [_part(p, o, names, par, dst, HIDDEN + n, note) for o in C.objects(p, sroot)]
            objs += parts; counts.append((label, len(parts), sroot))
        root = C._new(p, p.chunks[old]); p.refs[root] = 1
        C._set_objects(p, root, objs)
        ref = p.u32(old, 0x1c)
        if ref:
            r = oct_s.records[rec_of[ref]]
            if r.tree.items:
                raise ValueError('%s: its .oct record is not an empty tree' % tpl)
            oct_s.records.append(O.Record(r.vtable, r.pointer, O.Tree(r.tree.origin, r.tree.scale, [list(x) for x in r.tree.nodes], [], r.tree.fill)))
        new_roots.append((root, bool(ref)))
        users = [j for j in range(1, len(sc.nodes)) if models[j - 1][1] == old]
        for j in users:
            _retarget(sc, raw, models, j, root)
        guns.append(dict(template=tpl, item=item, root=root, stock_root=old, stock_parts=len(C.objects(p, old)), bones=len(dst),
                         looks=[dict(label=l, parts=n, source_root=s) for l, n, s in counts], users=len(users)))
    refs1 = oct_s.record_refs()
    if refs1[:len(refs0)] != refs0:
        raise ValueError('appending .oct records moved the base level\'s records')
    new = iter(refs1[len(refs0):])
    for root, has in new_roots:
        if has:
            p.chunks[root] = C._put(p.chunks[root], 0x1c, '<I', next(new))
    prm = G.write(p)
    mat.refs = T.material_refs(prm)
    base['.prm'], base['.MAT'], base['.oct'] = prm, T.write_mat(mat), oct_s.pack()
    base['.gms'], base['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    rep.update(guns=guns, level=level, roots=[g['root'] for g in guns], extra_roots=sorted(dm_root.values()), bones_folded=note['folded'],
               chunks=(rep['chunks'][0], len(p.chunks) - 1), prm_bytes=(rep['prm_bytes'][0], len(prm)))
    return rep


def check(lv, rep):
    """What must hold for the gun models whatever the game does with them. -> problems."""
    bad = []
    p = G.read(lv['.prm'], 'dd'); sc, raw = lv.scene()
    for g in rep['guns']:
        r = g['root']; n = p.u32(C.skeleton(p, r), 0); objs = C.objects(p, r)
        groups = [g['stock_parts']] + [l['parts'] for l in g['looks']]
        if len(objs) != sum(groups):
            bad.append('%s: %d parts, the groups say %d' % (g['template'], len(objs), sum(groups))); continue
        i = 0
        for gi, cnt in enumerate(groups):
            for o in objs[i:i + cnt]:
                c = p.chunks[o]
                if c[0x0f] != (0 if gi == 0 else HIDDEN + gi) or c[0x0c] != 2 or p.u32(o, 0x3c) >= n:
                    bad.append('%s: part %d of group %d: variant %d, bone %d of %d' % (g['template'], o, gi, c[0x0f], p.u32(o, 0x3c), n))
            if gi and not any(p.chunks[o][0x0e] & 1 for o in objs[i:i + cnt]):
                bad.append('%s: look %d has no part at full detail' % (g['template'], gi))
            i += cnt
        if C.person(sc, gun_node(sc, g['template']))[0] != r:
            bad.append('%s: the template does not name the new model' % g['template'])
    return bad


def write_ini(rep, path):
    """KLGuns.ini beside the level archive (klhook/klchar.c): the roots are chunk numbers of THIS build's .prm."""
    with open(path, 'w', newline='\r\n') as f:
        f.write('; written by tools/kl_guns.py - belongs to the level archive beside it (klhook\\klchar.c)\n')
        f.write('; a gun model\'s parts in object-table order: Stock parts, then Look1Parts, Look2Parts ...; shown = variant 0, hidden = %d + group\n' % HIDDEN)
        f.write('[Guns]\nVersion=1\nCount=%d\nHidden=%d\n' % (len(rep['guns']), HIDDEN))
        for i, g in enumerate(rep['guns'], 1):
            f.write('[Gun.%d]\nTemplate=%s\nItem=%d\nRoot=%d\nStock=%d\nLooks=%d\n' % (i, g['template'], g['item'], g['root'], g['stock_parts'], len(g['looks'])))
            for n, l in enumerate(g['looks'], 1):
                f.write('Look%d=%s\nLook%dParts=%d\n' % (n, l['label'], n, l['parts']))


def _items(p, objs, col):
    out = []
    for o in objs:
        if p.chunks[o][0x0e] & 1:
            d = p.u32(p.u32(o, 0x28), 0); nv = p.u32(d, 0); v = p.chunks[p.u32(d, 4)]; st = len(v) // max(nv, 1)
            pos = [struct.unpack_from('<3f', v, st * i) for i in range(nv)]
            ix = p.chunks[p.u32(d, 0x18)]; n = struct.unpack_from('<H', ix, 2)[0]; ii = struct.unpack_from('<%dH' % n, ix, 4)
            out.append((pos, [(ii[i], ii[i + 1], ii[i + 2]) for i in range(0, n - 2, 3)], col))
    return out


def sheet(folder, out):
    import kl_view as V
    lv = C.Lv(folder); p = G.read(lv['.prm'], 'dd')
    rep = json.load(open(os.path.join(folder, 'guns.json')))
    panels = []
    for g in rep['guns']:
        objs = C.objects(p, g['root']); i = g['stock_parts']
        stock = _items(p, objs[:i], (200, 170, 150))
        box = (-32, 108, -30, 30) if g['template'][:2] != 'HG' else (-10, 50, -14, 14)
        for l in g['looks']:
            look = _items(p, objs[i:i + l['parts']], (150, 150, 220)); i += l['parts']
            panels += [('front', box, stock), ('front', box, look), ('front', box, stock + look)]
    V.sheet(out, panels, 330, 150, cols=3)
    return len(panels) // 3


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
    if a[:1] == ['build'] and len(a) == 3:
        lv = C.Lv(a[1])
        rep = build(lv, opt.get('level', 'M01_FA_A'))
        for g in rep['guns']:
            print('  %-18s item %2d  model %5d -> %5d (%d users)  %d stock parts, looks: %s' % (
                g['template'], g['item'], g['stock_root'], g['root'], g['users'], g['stock_parts'], ', '.join('%s (%d parts)' % (l['label'], l['parts']) for l in g['looks'])))
        print('  .prm %d -> %d chunks, %.1f -> %.1f MB; %d part(s) put on an ancestor bone' % (rep['chunks'] + tuple(x / 1e6 for x in rep['prm_bytes']) + (rep['bones_folded'],)))
        bad = check(lv, rep)
        for b in bad[:20]:
            print('  PROBLEM: ' + b)
        bad += C.check(lv, None, rep['roots'] + rep['extra_roots'], extra=rep['extra_roots'])
        path = lv.write(a[2], opt.get('slot', lv.name))
        write_ini(rep, os.path.join(a[2], 'KLGuns.ini'))
        with open(os.path.join(a[2], 'guns.json'), 'w') as fh:
            json.dump(dict(base=a[1], problems=bad, **rep), fh, indent=1, default=str)
        print('built %s (%.0f MB) + KLGuns.ini, problems: %d' % (path, os.path.getsize(path) / 1e6, len(bad)))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['sheet'] and len(a) == 3:
        print('%s: %d looks (stock, look, both)' % (a[2], sheet(a[1], a[2])))
    elif a[:1] == ['survey']:
        sc = J.Scene.load('F01', 'dd'); dm = C.Source.get(opt.get('level', 'M01_FA_A'))
        for tpl, item, looks in LOOKS:
            print('%-18s item %d: %s' % (tpl, item, ', '.join('%s (%s %s)' % l for l in looks)))
            for _l, game, stpl in looks:
                gun_node(sc if game == 'dd' else dm.sc, stpl)
        print('all templates found')
    else:
        print(__doc__); sys.exit(1)
