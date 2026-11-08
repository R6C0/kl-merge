#!/usr/bin/env python3
r"""kl_dm06b_traffic_1108.py - DM06B (Dead Men M06_A, F02 slot): the 7 TRAFFIC! CARS the graft dropped, put back and placed on the road (2026-11-08, STAGE ONLY, never installs).

WHY: the owner (11-07): the maps feel empty outside. Dead Men's M06_A holds 7 car models under ROOT\Traffic!Cars! (node 17287..17293: Civilian_A/B/D, Bus_A, Police_A/B, Taxi_A,
ZLNKOBJ 0x200006, group 0, flags 0x220182, all at the origin). They are SPAWN TEMPLATES of the ZTrafficFlow spawners (the level's road splines), not placed cars, and the
graft dropped them with the rest of the traffic layer. This step appends their model closures (.prm / .MAT / .TEX) to the finished live DM06B build and places ONE static car
of each model along the road, in the form kl_fa_ropevis proved drawn (pool group 2, flags 0x264182, in no room tree, ZGEOM[4] = the new model root, light list borrowed
from the nearest ZSTDOBJ that has one) under one new top group KL_Traffic! (listed in root tree 3, like KL_RopeVis!).

WHAT IS PLACED WHERE (all GUESSES, marked):
  Road = Dead Men's 'Curvedroad' ZEditorSpline (25 waypoints; world = waypoint + the spline entity's own place, checked against the Ramp_R72m / FreeW_* meshes of the live
  scene: p6 probe, 0..40 units off a road mesh). Cars stand on waypoints 9, 11, 13 ... 21 (descending ramp road, y ~1300 .. 790), heading along the spline (GUESS: all one way).
  Height: spline y minus the car mesh's lowest vertex (GUESS: the spline y is the road surface). Yaw: local +Z of the car = its LONG axis (measured from the mesh box; the sign,
  front or back, is a GUESS: rot9 puts local +Z along the heading).
  The model root's .oct record (+0x1c) is ZEROED: NO COLLISION, the cars are scenery (like the rope).

  python tools/kl_dm06b_traffic_1108.py stage [--in-dir <map dir>] [--out <dir>]   (default in-dir: the live DM06B, only READ; out C:\kl_build_1024\dm06b_traffic_1108)
  python tools/kl_dm06b_traffic_1108.py check <out> [--in-dir <map dir>]

Refuses unless the live plain zip is exactly LIVE_ZIP_MD5 (the base this was written against). BOTH zips (plain + .bots.zip: same members, only .prp differs) get the step;
F02_Main.bots.base.md5 = md5 of the staged PLAIN zip; KLGuns.ini Entries= follows the new .prm chunk count (only that line changes). install.py: chain-installer style, tag
.before-dm06btraffic1108, all or nothing, --undo, --dry.
"""
import collections, hashlib, json, math, os, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T, kl_gms, kl_scene
import kl_prpjoin as J
import kl_lastcall_chain_1106 as CH

MAPDIR = os.path.join(CH.GAME, 'KLExpansion', 'Maps', 'DM06B')
OUT = r'C:\kl_build_1024\dm06b_traffic_1108'
TAG = '.before-dm06btraffic1108'
SLOT = 'F02'
LIVE_ZIP_MD5 = 'a6c0aef188549d6072821ca5728f1270'        # the live DM06B plain zip this was staged on (11-08 02:32)
LIVE_BOTS_MD5 = 'e1ca6d93c80bedc8e1be5395e329681c'
FILES = ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5', 'KLGuns.ini')
GROUP = 'KL_Traffic!'
LEVEL = 'M06_A'
STOCK = 'M06_A_conv'
CARS = ('Ground_JPN_Civilian_A_00', 'Ground_JPN_Bus_A__00', 'Ground_JPN_Civilian_B_00', 'Ground_JPN_Civilian_D_00',
        'Ground_JPN_Police_A_00', 'Ground_JPN_Police_B_00', 'Ground_JPN_Taxi_A_00')
SRC_PREFIX = 'ROOT\\Traffic!Cars!'
SPLINE_PATH = 'ROOT\\Traffic!Traffic_Curvedroad_Spawn_Spline#01'      # node 17295, 25 waypoints
WAYPOINTS = (9, 11, 13, 15, 17, 19, 21)                  # one per car, in CARS order (GUESS: spacing; ~2 .. 3 km apart)
VIS_FLAGS = 0x264182
VERTEX = 40
md5 = lambda b: hashlib.md5(b).hexdigest()


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def spline_world(M):
    """The Curvedroad waypoints in world space (waypoint + the spline entity's place; checked against the road meshes, p6) -> [(x, y, z)]."""
    import kl_fa
    sc = M.prp
    hit = sc.resolve(SPLINE_PATH)
    if len(hit) != 1:
        raise ValueError('%d nodes at %s' % (len(hit), SPLINE_PATH))
    k = hit[0]
    lab = J.labels('dd', sc.cls(k))
    vals = dict(zip(lab, kl_fa.node_values(sc, k)))
    blob = vals['ZEditorSpline[0]']
    if blob[:4] != b'1TPW':
        raise ValueError('spline blob is not WPT1')
    n = struct.unpack_from('<I', blob, 4)[0]
    pos = vals['ZGEOM[2]']
    pos = struct.unpack('<3f', pos) if isinstance(pos, (bytes, bytearray)) else tuple(float(v) for v in pos)
    return [tuple(struct.unpack_from('<3f', blob, 12 + 24 * i)[j] + pos[j] for j in range(3)) for i in range(n)]


def car_boxes(p, roots):
    """{root: (lo, hi)} of the model's BODY: the mesh with the most vertices, in the model's own frame. (The other parts are skinned in bone space: Civilian_A's
    union box is 380 x 1980 wide, its body mesh 206 x 435 = a car; GUESS: the body mesh stands on the ground at its lowest vertex.)"""
    out = {}
    for r in roots:
        kinds, _a = G.walk(p, [r])
        best = None
        for m, kd in kinds.items():
            if kd != 'mesh':
                continue
            sub = p.u32(m, 0x28); d = p.u32(sub, 0); nv, vtx = p.u32(d, 0), p.u32(d, 4)
            v = p.chunks[vtx]
            st = len(v) // nv
            if len(v) - st * nv >= 16 or st < 12:                   # the chunk is padded by a few bytes (52 * 283 + 4)
                raise ValueError('mesh %d: vertex chunk %d bytes for %d vertices' % (m, len(v), nv))
            if best is None or nv > best[0]:
                pts = [struct.unpack_from('<3f', v, st * j) for j in range(nv)]     # position first in every stride seen (40 static, 52 skinned)
                best = (nv, (tuple(min(q[i] for q in pts) for i in range(3)), tuple(max(q[i] for q in pts) for i in range(3))))
        out[r] = best[1]
    return out


def spots(wps, boxes, roots):
    """-> [(world position, rot9, heading)] for the 7 cars. rot9 puts local +Z (the car's long axis, measured) along the spline heading."""
    import kl_fa_bots as F
    out = []
    for car, w, r in zip(CARS, WAYPOINTS, roots):
        a, b = wps[w], wps[w + 1]
        dx, dz = b[0] - a[0], b[2] - a[2]
        lo, hi = boxes[r]
        ex, ez = hi[0] - lo[0], hi[2] - lo[2]
        if ex > ez:                                       # the long axis is local X: turn so X, not Z, follows the heading
            rot = F.rot9(-dz, dx)
        else:
            rot = F.rot9(dx, dz)
        pos = (a[0], a[1] - lo[1], a[2])                  # lowest vertex on the spline y (GUESS: spline y = road surface)
        out.append((pos, rot, (dx, dz), (round(ex), round(ez))))
    return out


TWIN_GLOW = True
TEX_LEVEL = 6      # MEASURED 11-08: the live DM06B zip holds .TEX at deflate level 6 (recompressing the live .TEX at 6 gives 102517856 vs 102517779 in the zip, level 1 gives 121 MB)
                   # and every other member at level 1 (.prm matches to the byte); kl_graft.write_zip packs all at 1, which grew the zip 19.7 MB.


def write_zip(path, members):
    """kl_graft.write_zip (same stamp, attrs, order) with the live level per member: .TEX at TEX_LEVEL, the rest as load_options() says."""
    import kl_graft, zipfile as zf
    opt = kl_graft.load_options()
    with zf.ZipFile(path, 'w', zf.ZIP_DEFLATED, compresslevel=opt['level']) as z:
        for name, data in members:
            zi = zf.ZipInfo(name, kl_graft.STAMP)
            zi.external_attr = 0o600 << 16
            z.writestr(zi, data, zf.ZIP_DEFLATED, TEX_LEVEL if name.endswith('.TEX') else opt['level'])
    return path


def stage_zip(zp, out_zp, M, log):
    """One zip: the 7 cars added -> report dict. Refuses unless the zip's members are what the live DM06B was."""
    import kl_fa_bots as F, kl_fa_cover as CV, kl_fa_climb2 as C2, kl_graft, kl_light
    import kl_octree as O
    B = F.Built(zp, SLOT)
    sc = B.sc
    if sc.resolve(F.R_ + GROUP):
        raise ValueError('the build already has %s' % GROUP)
    say = log
    mk = F.Maker()
    nodes = [mk.clone(STOCK, SRC_PREFIX + c) for c in CARS]
    sc7, ents7 = F.Maker.level(STOCK)
    roots = [ents7[sc7.resolve(SRC_PREFIX + c)[0] - 1].model for c in CARS]
    p7 = G.read(M['.prm'], 'dd')
    mat7, tex7 = T.read_mat(M['.MAT']), T.read_tex(M['.TEX'])
    boxes = car_boxes(p7, roots)
    wps = spline_world(M)
    sp = spots(wps, boxes, roots)
    # ---- .prm / .MAT / .TEX
    pD, matD, texD = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    kinds, args = G.walk(p7, roots)
    slots = {p7.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(mat7, slots))
    tex, tmap = T.merge_tex(texD, tex7, want)
    mat, mmap = T.merge_mat(matD, mat7, slots, tmap)
    prm, cmap = G.append(pD, p7, roots, mmap, None, tmap)
    zeroed = 0
    for old in kinds:                                     # NO COLLISION: every model root's .oct record reference (+0x1c) -> 0
        c = prm.chunks[cmap[old]]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0]:
            c = bytearray(c); struct.pack_into('<I', c, 0x1c, 0); prm.chunks[cmap[old]] = bytes(c); zeroed += 1
    say('  .prm: %d chunks appended (%d roots -> %s), %d .oct record refs zeroed; materials %d, textures %d' % (
        len(kinds), len(roots), [cmap[r] for r in roots], zeroed, len(slots), len(want)))
    # SHADER FIT (1108 review): a material without a compiled shader is NOT drawn (kl_fa_loot.dress), so fit like kl_fa_bank / kl_fa_club do:
    # kl_light.fit_shaders switches features off (or rebuilds as Standard/Standard) until every effect the material asks for is in the build's .fxc.
    new_slots = sorted(mmap[s] for s in slots)
    # GUESS: the 5 glow materials (headlight flare / beam / lamp, Standard/Glow, skinned) have no MESH_WEIGHTED variant in any .fxc we have, so they are rebuilt as
    # Standard/Standard (kl_light.plain_twin, blend state kept): a lit blended quad instead of a glow. kl_light.TWIN_CLASSES lists SkinCloth only because a glow
    # drawn lit 'may look worse than one that is missing' - the bench screenshots decide; set TWIN_GLOW = False to leave them undrawn (then check() fails on purpose).
    old_twin = kl_light.TWIN_CLASSES
    if TWIN_GLOW:
        kl_light.TWIN_CLASSES = old_twin + (('Standard', 'Glow'),)
    try:
        fit = kl_light.fit_shaders(mat, B['.fxc'], slots=new_slots, log=say, twin_on=('SPECULARENABLED', 'STDSAMPLERSTATE'))   # GUESS: the compiled skinned+blend Standard permutations are {BLEND, SPECULAR, STDSAMPLERSTATE}
    finally:
        kl_light.TWIN_CLASSES = old_twin
    if fit['unresolved']:
        raise ValueError('no compiled shader for %s' % [v[0] for v in fit['unresolved'].values()])
    lack = kl_light.missing_shaders(mat, B['.fxc'], new_slots)
    if lack:
        raise ValueError('shaders still missing after fit_shaders: %s' % lack)
    say('  shaders: every one of the %d car materials resolves to a compiled shader (fixed: %s)' % (
        len(new_slots), {s: v for s, v in fit['fixed'].items()} or 'none'))
    # ---- nodes
    gk = CV.group_form(B)
    topg = CV._node(mk, B, gk, GROUP)
    mk.place(topg, (0.0, 0.0, 0.0))
    for nd, r, (pos, rot, hd, ex) in zip(nodes, roots, sp):
        nd.name = 'KL_' + nd.name.replace('Traffic!Cars!', '') if isinstance(nd.name, str) else b'KL_' + nd.name.replace(b'Traffic!Cars!', b'')
        topg.add(nd)
        mk.place(nd, pos, rot)
        nd.model, nd.flags, nd.group = cmap[r], VIS_FLAGS, 2
        mk.set(nd, None, {'ZGEOM[4]': cmap[r]})
        best = None
        for e in B.ents:
            if e.tid == 0x200002 and e.links:
                P = B.fr[e][1]
                dd = sum((P[i] - pos[i]) ** 2 for i in range(3))
                if best is None or dd < best[0]:
                    best = (dd, e)
        nd.links = list(best[1].links) if best else []
        say('  %-26s at (%.0f, %.0f, %.0f) heading (%.2f, %.2f) car box x/z %s; light list of %s (%d, %.0f away)' % (
            nd.name if isinstance(nd.name, str) else nd.name.decode(), pos[0], pos[1], pos[2], hd[0], hd[1], ex,
            best[1].name.decode('latin1')[-30:] if best else '-', len(nd.links), math.sqrt(best[0]) if best else 0))
    q, order = mk.scene([topg])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'dm06btraffic')
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    misfit = J.misfits(Jn) if hasattr(J, 'misfits') else []
    if misfit:
        raise ValueError('schema misfits: %s' % (misfit[:3],))
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    A = B.scene
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    nxt = C2._write_ent(A, topg, None, nxt, made)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    pts = [s[0] for s in sp]
    lo = tuple(min(p[i] for p in pts) - 600.0 for i in range(3)); hi = tuple(max(p[i] for p in pts) + 600.0 for i in range(3))
    root3 = octn.rooms[0][3]
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree([(slot1[made[id(topg)]] + 2, lo, hi)], root3.origin, root3.scale))
        octn.rooms[0][3].check()
    move = {x: y for x, y in zip(octx.record_refs(), octn.record_refs()) if x != y}
    pm = bytearray(G.write(prm))
    repointed = 0
    if move:
        t, n = struct.unpack_from('<II', pm, 0)
        for i in range(1, n):
            o, size = struct.unpack_from('<II', pm, t + 16 * i)
            if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    prm_bytes = bytes(pm)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    lost = T.used_textures(T.read_mat(new[B.ext['.MAT']])) - set(T.read_tex(new[B.ext['.TEX']]).tex)
    if lost:
        raise ValueError('materials name textures the .TEX lacks: %s' % sorted(lost)[:5])
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    write_zip(out_zp, [(nm, new[nm]) for nm in B.order])
    say('written %s: %d entities added, members changed: %s; %d .prm roots re-pointed; chunks %d -> %d' % (
        out_zp, len(order), ' '.join(changed), repointed, len(pD.chunks), len(p2.chunks)))
    return dict(changed=changed, chunks=len(p2.chunks), roots=[cmap[r] for r in roots], spots=[[list(s[0]), s[3]] for s in sp], headings=[list(s[2]) for s in sp],
                shaders_fixed={str(k): [v[0], [str(x) for x in v[1]]] for k, v in fit['fixed'].items()}, order=B.order)


def stage(in_dir=MAPDIR, out=OUT, log=print):
    import kl_graft, kl_fa_bots as F
    zp, bp = os.path.join(in_dir, 'F02_Main.zip'), os.path.join(in_dir, 'F02_Main.bots.zip')
    live = {n: fmd5(os.path.join(in_dir, n)) for n in FILES}
    if live['F02_Main.zip'] != LIVE_ZIP_MD5:
        raise ValueError('REFUSED: the live DM06B plain zip is %s, not the pinned %s: re-pin after checking what changed it' % (live['F02_Main.zip'], LIVE_ZIP_MD5))
    if live['F02_Main.bots.zip'] != LIVE_BOTS_MD5:
        raise ValueError('REFUSED: the live DM06B bots zip is %s, not the pinned %s' % (live['F02_Main.bots.zip'], LIVE_BOTS_MD5))
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    M = kl_graft.DeadMen(LEVEL, log=lambda *a: None)
    F.Maker._stock[STOCK] = (M.prp, M.ents)
    reps = {}
    for name, src in (('F02_Main.zip', zp), ('F02_Main.bots.zip', bp)):
        log('== %s' % name)
        reps[name] = stage_zip(src, os.path.join(out, name), M, log)
    if reps['F02_Main.zip']['order'] != reps['F02_Main.bots.zip']['order']:
        raise ValueError('member order differs between the zips')
    plain = fmd5(os.path.join(out, 'F02_Main.zip'))
    open(os.path.join(out, 'F02_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    n = reps['F02_Main.zip']['chunks']
    if reps['F02_Main.bots.zip']['chunks'] != n:
        raise ValueError('.prm chunk count differs between the zips')
    import kl_club_doors_1106 as D
    ini, c = D.patch_entries(os.path.join(in_dir, 'KLGuns.ini'), n)
    if c != 1:
        raise ValueError('KLGuns.ini: %d Entries= lines' % c)
    open(os.path.join(out, 'KLGuns.ini'), 'wb').write(ini)
    files = {nm: (live[nm], fmd5(os.path.join(out, nm))) for nm in FILES}
    write_install(out, files)
    json.dump(dict(in_dir=in_dir, files=files, reports={k: {a: b for a, b in v.items() if a != 'order'} for k, v in reps.items()}),
              open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    bad = check(out, in_dir, log)
    for nm, (o, w) in files.items():
        log('  %-26s live %s -> %s%s' % (nm, o[:8], w[:8], '' if o != w else '  (unchanged, not installed)'))
    log('CHECK: %s' % ('PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


def check(out, in_dir=MAPDIR, log=print):
    import kl_fa_bots as F, kl_octree as O
    bad = []
    for name in ('F02_Main.zip', 'F02_Main.bots.zip'):
        a, b = zipfile.ZipFile(os.path.join(in_dir, name)), zipfile.ZipFile(os.path.join(out, name))
        if [i.filename for i in a.infolist()] != [i.filename for i in b.infolist()]:
            bad.append('%s: member list/order differs' % name)
            continue
        ch = sorted(i.filename.rsplit('_Main', 1)[1] for i in a.infolist()
                    if (b.getinfo(i.filename).CRC, b.getinfo(i.filename).file_size) != (i.CRC, i.file_size))
        want = ['.MAT', '.TEX', '.buf', '.gms', '.oct', '.prm', '.prp', '.rmc', '.rmi']
        if ch != sorted(want):
            bad.append('%s: members changed %s, expected %s' % (name, ch, sorted(want)))
        B = F.Built(os.path.join(out, name), SLOT)
        grp = B.sc.resolve(F.R_ + GROUP)
        if len(grp) != 1:
            bad.append('%s: %d %s nodes' % (name, len(grp), GROUP)); continue
        p = G.read(B['.prm'], 'dd')
        mat, tex = T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
        cars = [e for e in B.ents if e.name.decode('latin1') in ['KL_' + c for c in CARS]]
        if len(cars) != 7:
            bad.append('%s: %d car entities, not 7' % (name, len(cars)))
        import kl_light
        fxc_have = kl_light.shader_cache(B['.fxc'])
        rmi = O.RoomIndex.parse(B['.rmi'])
        for e in cars:
            kinds, _a = G.walk(p, [e.model])
            sl = {p.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
            if not sl or any(s not in mat.insts for s in sl):
                bad.append('%s: %s material slot unresolved' % (name, e.name))
            nolack = kl_light.missing_shaders(mat, fxc_have, sorted(sl))
            if nolack:
                bad.append('%s: %s materials without a compiled shader: %s' % (name, e.name, nolack))
            if T.used_textures(mat, sl) - set(tex.tex):
                bad.append('%s: %s texture missing' % (name, e.name))
            c = p.chunks[e.model]
            if len(c) == 64 and struct.unpack_from('<I', c, 0x1c)[0]:
                bad.append('%s: %s keeps an .oct record ref' % (name, e.name))
            if e.group != 2 or e.flags != VIS_FLAGS:
                bad.append('%s: %s form group %s flags %#x' % (name, e.name, e.group, e.flags))
            pos = B.fr[e][1]
            inside = []
            for i, bx in enumerate(rmi.boxes):
                f = struct.unpack_from('<19f', bx.raw, 0)
                ctr, half = f[10:13], f[16:19]
                if all(abs(pos[j] - ctr[j]) <= half[j] for j in range(3)):
                    inside.append(i)
            log('  %s %s at (%.0f, %.0f, %.0f) inside .rmi boxes (AABB, rotation ignored) %s' % (name, e.name.decode('latin1')[-26:], pos[0], pos[1], pos[2], inside))
            if not inside:
                bad.append('%s: %s is in no .rmi box (would not be drawn)' % (name, e.name))
    if open(os.path.join(out, 'F02_Main.bots.base.md5')).read().strip() != fmd5(os.path.join(out, 'F02_Main.zip')):
        bad.append('base.md5 is not the plain zip md5')
    for nm in ('KLGuns.ini',):
        a = open(os.path.join(in_dir, nm), 'rb').read().decode('latin-1').splitlines()
        b = open(os.path.join(out, nm), 'rb').read().decode('latin-1').splitlines()
        d = [(x, y) for x, y in zip(a, b) if x != y]
        if len(a) != len(b) or len(d) > 1 or any(not x.lower().startswith('entries') for x, y in d):
            bad.append('%s: more than the Entries= line differs' % nm)
    return bad


# ------------------------------------------------------------------ install.py (the chain installer, retargeted at DM06B / F02)
def write_install(st, files):
    txt = CH.INSTALL
    for a, b in (('LAST CALL CHAIN @@PASSES@@ (2026-11-06, tools/kl_lastcall_chain_1106.py) on the live DM05A files',
                  'DM06B TRAFFIC CARS 1108 (tools/kl_dm06b_traffic_1108.py) on the live DM06B files'),
                 ('<name>.before-chain1106', '<name>' + TAG), ("MAP, TAG = 'DM05A', @@TAG@@", "MAP, TAG = 'DM06B', @@TAG@@"),
                 ('F01_Main', 'F02_Main')):
        if a not in txt:
            raise ValueError('install template changed: %r not found' % a)
        txt = txt.replace(a, b)
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = txt.replace('@@FILES@@', fl).replace('@@PIN@@', repr(files['F02_Main.zip'][0])).replace('@@TAG@@', repr(TAG))
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL DM06B traffic 1108.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO DM06B traffic 1108.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if a[:1] == ['stage']:
        return 1 if stage(opt('--in-dir', MAPDIR), opt('--out', OUT)) else 0
    if a[:1] == ['check'] and len(a) >= 2:
        bad = check(a[1], opt('--in-dir', MAPDIR))
        print('CHECK:', 'PASS' if not bad else bad)
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
