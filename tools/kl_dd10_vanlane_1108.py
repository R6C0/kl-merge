#!/usr/bin/env python3
r"""kl_dd10_vanlane_1108.py - Flat Raid (DD10 = Dog Days L05 in the F07 slot): the escape van's lane. Stage built from the LIVE files
(2026-11-08, offline, stage only; nothing is installed, no game is launched).

AUDIT (tools/kl_vehaudit_1108.py, re/vehicle_routes_1108.md): the key-framed escape van V_Van_00 drives on z = 1100 for its whole drive (keys 0..390,
x 6280 .. 11800) and pierces the level's RENDER: BigFence_A_02 (the closed gate, key 94), SO0010_L05_Pillar_A_02 (keys 90..395: both pillar pairs, x 7935..8015
and x 9960..10040), PC1201_L05_Exit_01 (the wall sign, keys 271..277) and a thin "Plane01" curtain.
DATA FACTS (read from the live collision with kl_map_escape.Ground, MEASURED): the street between the SideWalls is z 797 .. 1200 (centre 998), walls
x 8000 .. 9600 at z 800 / 1200; gate #1 = pillars A_01 z 768..848 + A_02 z 1142..1222 at x 7935..8015 with the fence BigFence_A_02 (x 7999..8014, z 845..1145)
and a collision-only plane ColiObj_HERO_Plane01 (x 8017, z 652..1349); gate #2 = pillars at x 9960..10040 (z 759..839 / 1160..1239); the sign Exit_01 sits flush on
the north wall (z 1197..1200, y 215..242). The pillar gaps (z 848..1142 and 839..1160) are centred on z ~1000; the van's line z 1100 is 100 north of the centre.

FIX (three parts):
  (a) LANE: every position key of the drive gets z = lane(x): 1100 up to x 6500 (key 0, the baked Havok pose of the van's pieces, is untouched), a smoothstep to
      LANE_Z = 1030 at x 7500, then 1030 to the end. Same key count; only the z float of the keys of the main drive (the 12-byte triples) changes. The ROTATION
      keys of the drive are turned about Y by the change of the path's heading (FOLLOW = 1.0, <= 6 degrees), their sway is kept (kl_map_escape.VanKeys.turned).
      WHY 1030 and not 1000: the lane must pass the pillar pairs (gap centre ~995) AND the low dustbins B_01..B_03 (z up to 924, y 72) on the south side: 1030 leaves
      7 cm to pillar A_02 and 2 cm to the dustbins at half width 100 (the audit's), 70 to the sign, 130 to the south wall.
  (b) GATE: BigFence_A_02 (REF 31255) is HIDDEN (render only: .prp ZGEOM[3] = 1 and the .gms flag 0x400); its collision is NOT cut. Players keep exactly the wall
      they had (the plane ColiObj_HERO_Plane01 stands there too); the van drives through an open-looking gate. Evidence that a hidden entity keeps its collision:
      kl_l05_layer.py (the wall break's PrePost frame, 'hidden but live-collision', MEASURED). GUESS: the engine keeps the Havok static of a hidden node
      (the same GUESS the layer already relies on). The alternative (CLEAR_WHAT, the collision cut in the .HVK) would open the corridor for players and needs
      a rebuild of the join: not done.
  (c) STOP: the stop key (x 8640, the boarding place) moves from z 1100 to LANE_Z. The nodes that are rigid with the stopped van or lie on the drive move by the
      same dz (LANE_Z - 1100), exactly the nodes kl_map_escape.van_prepare moves with the stop: PathBlockerVan, CameraTrigger_InVan, CamPos_InVan_FocusPoint
      (stopped van), TriggerBox_RearDoors_Open, CameraTrigger01 (on the drive). NOT moved, on purpose: the layer's exit / POI boxes (450 half extent round
      (8300, 1100): the stop is 70 inside them), the 06_Exit jump point (a place, 70 off), the outro camera, the bots' AllyEscapeBox (350 half extent: the van is
      inside it either way) and the bots' own places (z ~900, built >= 200 off the old line: 130 off the new one, 20 outside the van's half width 110).
      WHY not stop at z 1100 with a lane of 1000 at the gates: the return from 1000 to 1100 has 285 cm between the gate window (origin x 8355) and the stop (8640)
      inside the 400 wide walls: a sideways slide of a whole metre or a yaw of 30 degrees (measured: walls pierced), see the numbers in 'lane' below.

Changes ONLY F07_Main.buf (the keys head), F07_Main.gms (5 translations + 1 flag) and F07_Main.prp (the same 5 ZGEOM[2] + 1 ZGEOM[3]) of the plain AND the bots zip.
F07_Main.bots.base.md5 = md5 of the plain staged zip. KLGuns.ini does not exist for DD10.

  python tools/kl_dd10_vanlane_1108.py stage [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_dd10_vanlane_1108.py check [--in-dir <map dir>] [--out-root C:/kl_build_1024]        (also runs 'lane')
  python tools/kl_dd10_vanlane_1108.py lane [--zip <F07_Main.zip>]       swept-box clearance per solid (collision tris), half width 100 and 110
  python tools/kl_dd10_vanlane_1108.py audit [--out-root ..] [--zip <zip>]   kl_vehaudit_1108 on the staged (or the given) zip (hard link, no copy), DD10 only
Never installs anything. REFUSES unless the live files are the expected md5s and the keys / nodes hold the pre-edit values."""
import collections, hashlib, math, os, re, shutil, struct, subprocess, sys, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))
import kl_fa
import kl_fa_bots as F
import kl_fa_author as A
import kl_gms
import kl_graft
import kl_map_escape as ME
import kl_prpjoin as J
import kl_skyline_1108 as SK

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DD10')
OUT_ROOT = 'C:/kl_build_1024'
MAP, SLOT = 'DD10', 'F07'
NAME, TAG, TITLE = 'dd10vanlane_1108', '.before-dd10vanlane1108', 'DD10VANLANE1108'
TEMPLATE = 'C:/kl_build_1024/citylights_1108/install.py'
ZIP, BOTS, BASE = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5'
LIVE_MD5 = {ZIP: 'bc4d0bc3e52889d4c333a52876767156', BOTS: '3cca3236eae7a88926de9775600f5040', BASE: '73d388ccf767cb81264c30cf98431e6a'}
HIDDEN = 0x400

OLD_Z = 1100.0
LANE_Z = 1030.0                         # see (a) above
LANE_FROM, LANE_TO = 6500.0, 7500.0     # x of the van's origin: where the lane starts to leave 1100 / where it is on LANE_Z
FOLLOW = 1.0                            # the drive's rotation keys follow the heading of the new path completely (<= 6 degrees)
FENCE_REF, FENCE_NAME = 31255, 'SO0700_ALL_BigFence_A_02'
FENCE_AT = (8007.0, 0.0, 996.0)
# the van's other nodes, by name (kl_map_escape._van_nodes): moved by dz of the lane at their x
MOVE_NODES = ('PathBlockerVan', 'CameraTrigger_InVan', 'CamPos_InVan_FocusPoint', 'TriggerBox_RearDoors_Open', 'CameraTrigger01')
GROUP = 'EscapeVehicle_Animation_F07'
# the swept box of the clearance proof: the van's own half width in the audit (kl_vehaudit_1108.body_lines: +-100), kl_map_escape.VAN_HALF (110), the length
# behind / before the origin (BOARD_BACK 337; GUESS: 260 for the nose, measured on the van's collision pieces in the earlier analysis), heights 25 .. 250 over the road
HALF_AUDIT, HALF_LANE = 100.0, ME.VAN_HALF
BACK, FRONT = 340.0, 260.0
Y_LO, Y_HI = 25.0, 250.0
MIN_CLEAR = {'SO0010_L05_Pillar_A_02': 5.0, 'SO0010_L05_Pillar_A_01': 40.0, 'SideWall_': 40.0, 'PC1201_L05_Exit_01': 40.0, 'PC0200_ALL_DrainPipe': 30.0}


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _ss(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lane(x):
    """The new lane z for a van origin at x."""
    return OLD_Z + (LANE_Z - OLD_Z) * _ss((x - LANE_FROM) / (LANE_TO - LANE_FROM))


# ------------------------------------------------------------------ reading
def van_keys(B):
    sc = B.sc
    ks = [k for k in range(1, len(B.ents) + 1) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k]]
    if len(ks) != 1:
        raise SystemExit('REFUSED: %d V_Van_00 nodes' % len(ks))
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    return ks[0], ME.VanKeys(B.scene.head, B.ents[ks[0] - 1].raw, ends, kl_graft.keys_tracks)


def van_nodes(sc):
    """{name: node} of MOVE_NODES under the van group (exactly one each)."""
    out = {}
    for n in MOVE_NODES:
        ks = [k for k in range(1, len(sc.nodes)) if sc.names[k] == n and GROUP in sc.path[k] and 'Reflection' not in sc.path[k]]
        if len(ks) != 1:
            raise SystemExit('REFUSED: %d nodes %s under %s' % (len(ks), n, GROUP))
        out[n] = ks[0]
    return out


def fence_node(B):
    ks = [i + 1 for i, e in enumerate(B.ents) if e.ref == FENCE_REF]
    if len(ks) != 1:
        raise SystemExit('REFUSED: REF %d carried by %d entities' % (FENCE_REF, len(ks)))
    k = ks[0]
    at = B.at(k)
    if not B.sc.path[k].endswith(FENCE_NAME) or any(abs(a - b) > 5.0 for a, b in zip(at, FENCE_AT)):
        raise SystemExit('REFUSED: REF %d is %s at %r, not %s at %r: the ids moved' % (FENCE_REF, B.sc.path[k][-40:], tuple(round(v) for v in at), FENCE_NAME, FENCE_AT))
    return k


def rot_plan(K, cut):
    """-> {rot key: yaw delta (deg)} for the rotation keys of the main drive, and the per-position-key delta. Refuses a rot key shared with a non-drive frame."""
    first, users = {}, collections.defaultdict(set)
    for f in range(K.frames):
        users[K.f2r[f]].add(K.f2p[f] < cut)
        first.setdefault(K.f2r[f], f)
    delta = {}
    for r in range(K.nrot):
        kp = K.f2p[first[r]]
        if kp >= cut:
            continue
        if users[r] != {True}:
            raise SystemExit('REFUSED: rotation key %d is shared with a frame that is not the main drive' % r)
        delta[r] = kp
    return delta


def new_keys(K, cut):
    """-> (positions, rotations): new tuples for every key (non-drive keys unchanged)."""
    pos = [tuple(p) for p in K.pos]
    for i in range(cut):
        pos[i] = (pos[i][0], pos[i][1], lane(pos[i][0]))
    rot = list(K.rot)
    for r, kp in rot_plan(K, cut).items():
        a, b = max(0, kp - 1), min(cut - 1, kp + 1)
        if pos[b][0] == pos[a][0]:
            continue                                        # a stop (the hold keys): the heading does not change
        want = math.degrees(math.atan2(pos[b][0] - pos[a][0], pos[b][2] - pos[a][2]))
        old = math.degrees(math.atan2(K.pos[b][0] - K.pos[a][0], K.pos[b][2] - K.pos[a][2]))
        d = FOLLOW * (want - old)
        if abs(d) > 1e-6:
            rot[r] = ME.VanKeys.turned(K.rot[r], d)
    return pos, rot


# ------------------------------------------------------------------ writing
def pre_check(B, K, cut, log=print):
    """REFUSES unless this is the pre-edit state."""
    if any(abs(p[2] - OLD_Z) > 4.0 for p in K.pos[:cut]):
        raise SystemExit('REFUSED: the drive is not on z %d (the pre-edit lane)' % OLD_Z)
    k = fence_node(B)
    if B.ents[k - 1].flags & HIDDEN or kl_fa.node_values(B.sc, k)[J.labels('dd', B.sc.cls(k)).index('ZGEOM[3]')] != 0:
        raise SystemExit('REFUSED: the fence is already hidden')


def patch_zip(src, dst, log=print):
    B = F.Built(src)
    sc = B.sc
    vk, K = van_keys(B)
    cut = K.drive()
    pre_check(B, K, cut, log)
    pos, rot = new_keys(K, cut)
    head = bytearray(B.scene.head)
    for i, p in enumerate(pos):
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
    for i, q in enumerate(rot):
        struct.pack_into('<4h', head, K.offs[2] + 8 * i, *q)
    shim = types.SimpleNamespace(prp=sc, ents=B.ents)
    moved = []
    for n, k in van_nodes(sc).items():
        t = struct.unpack('<3f', B.ents[k - 1].trans[:12])
        dz = lane(t[0]) - OLD_Z
        if abs(dz) < 1e-6:
            continue
        A.place(shim, k, (t[0], t[1], t[2] + dz))
        moved.append((n, tuple(round(v) for v in t), round(dz, 1)))
    fk = fence_node(B)
    lab = J.labels('dd', sc.cls(fk))
    kl_graft.edit(sc.nodes[fk], 'props', lambda us: A.setv(sc, us, lab.index('ZGEOM[3]'), 1))
    B.ents[fk - 1].flags |= HIDDEN
    prp = sc.p.serialize()
    gms, buf = B.scene.write()
    B.scene.head = bytes(head)
    nbuf = bytes(head) + B.files[B.ext['.buf']][len(head):]
    if B.files[B.ext['.buf']][:len(head)] != bytes(B.scene.head and B.scene.head[:0]) + B.files[B.ext['.buf']][:len(head)]:
        raise SystemExit('internal')
    if buf != B.files[B.ext['.buf']]:
        raise SystemExit('REFUSED: scene.write() does not reproduce the .buf: the splice below would be wrong')
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), nbuf
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))
    log('  %d position keys z -> lane(x) (key 0 untouched), %d rotation keys of the drive turned, %d nodes moved %s, fence node %d hidden (render only)'
        % (cut, len(rot_plan(K, cut)), len(moved), moved, fk))


def make_install(out, stage_md5):
    t = open(TEMPLATE, encoding='utf-8').read()
    rows = ["    ('%s', '%s', '%s')," % (n, LIVE_MD5[n], stage_md5[n]) for n in (ZIP, BOTS, BASE)]
    t, k = re.subn(r"FILES = \[.*?\n\]\n", lambda m: "FILES = [   # name, live md5 before, staged md5 after\n" + '\n'.join(rows) + "\n]\n", t, flags=re.S)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES block')
    t, k = re.subn(r"MAP, TAG = 'DM05A', '\.before-[a-z0-9]+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5[ZIP], t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single LIVE_ZIP_MD5 line')
    t = t.replace("DM05A CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)", "DD10 %s (bench only) (tools/kl_dd10_vanlane_1108.py)" % TITLE)
    t = t.replace('F01_Main', 'F07_Main').replace('.before-skyline1108', TAG)
    t = t.replace('DM05A', MAP)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)


def stage(in_dir, out_root, log=print):
    out = os.path.join(out_root, NAME)
    for n, want in LIVE_MD5.items():
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != want:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DD10 changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', want))
    if open(os.path.join(in_dir, BASE)).read().strip() != fmd5(os.path.join(in_dir, ZIP)):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')
    os.makedirs(out, exist_ok=True)
    log('stage -> %s' % out)
    for n in (ZIP, BOTS):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), log)
    with open(os.path.join(out, BASE), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, ZIP)) + '\n')
    sm = {n: fmd5(os.path.join(out, n)) for n in (ZIP, BOTS, BASE)}
    make_install(out, sm)
    for n in sorted(os.listdir(out)):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


# ------------------------------------------------------------------ the swept box
def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _inpoly(pt, poly):
    s = [_cross(poly[i], poly[(i + 1) % len(poly)], pt) for i in range(len(poly))]
    return all(v >= 0 for v in s) or all(v <= 0 for v in s)


def _segx(p, q, r, s):
    return _cross(r, s, p) * _cross(r, s, q) < 0 and _cross(p, q, r) * _cross(p, q, s) < 0


def _segd(p, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / ((dx * dx + dz * dz) or 1.0)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz)


def _dist(rect, tri):
    """distance (cm, 0 = touching or overlapping) between a convex quad and a triangle, both as (x, z) points; degenerate (line) triangles work."""
    if any(_inpoly(p, rect) for p in tri) or any(_inpoly(p, tri) for p in rect):
        return 0.0
    re_, te = [(rect[i], rect[(i + 1) % 4]) for i in range(4)], [(tri[i], tri[(i + 1) % 3]) for i in range(3)]
    if any(_segx(a, b, c, e) for a, b in re_ for c, e in te):
        return 0.0
    return min([_segd(p, a, b) for p in rect for a, b in te] + [_segd(p, a, b) for p in tri for a, b in re_])


def _rect(x, z, yaw, hw):
    h = math.radians(yaw)
    f, s = (math.sin(h), math.cos(h)), (math.cos(h), -math.sin(h))
    return [(x + f[0] * l + s[0] * w, z + f[1] * l + s[1] * w) for l, w in ((-BACK, -hw), (FRONT, -hw), (FRONT, hw), (-BACK, hw))]


def swept(zp, hws=(HALF_AUDIT, HALF_LANE), log=print):
    """Oriented box (half width hw, BACK behind / FRONT before the van origin, heights Y_LO..Y_HI over the key's y) swept along every key of the drive and
    its midpoints against the level's COLLISION triangles (kl_map_escape.Ground; flat ground (y <= 30) left out) in the band. -> {hw: {solid: (min cm, key, x, z)}}"""
    B = F.Built(zp)
    vk, K = van_keys(B)
    cut = K.drive()
    L = ME.Level(zp)
    G = ME.Ground(L)
    tris = collections.defaultdict(list)
    for a, b, c, r, _up in G.tris:
        xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
        if max(xs) < 6300 or min(xs) > 11900 or max(ys) <= 30 or min(ys) > 260:
            continue
        tris[r].append(((a[0], a[2]), (b[0], b[2]), (c[0], c[2]), min(ys), max(ys)))
    names = {r: L.name(r).split(chr(92))[-1][:48] for r in tris}
    yaw = [None] * K.npos
    for f in range(K.frames):
        if yaw[K.f2p[f]] is None:
            yaw[K.f2p[f]] = ME.VanKeys.yaw(K.rot[K.f2r[f]])
    out = {}
    for hw in hws:
        res = {}
        for i in range(cut - 1):
            j = i + 1
            for s in (0.0, 0.5):
                x, z = [K.pos[i][c] + (K.pos[j][c] - K.pos[i][c]) * s for c in (0, 2)]
                y0 = K.pos[i][1]
                yw = (yaw[i] if yaw[i] is not None else 90.0) * (1 - s) + (yaw[j] if yaw[j] is not None else 90.0) * s
                R = _rect(x, z, yw, hw)
                x0, x1, z0, z1 = min(p[0] for p in R) - 150, max(p[0] for p in R) + 150, min(p[1] for p in R) - 150, max(p[1] for p in R) + 150
                for r, tl in tris.items():
                    for t in tl:
                        if t[4] < y0 + Y_LO or t[3] > y0 + Y_HI:
                            continue
                        if max(q[0] for q in t[:3]) < x0 or min(q[0] for q in t[:3]) > x1 or max(q[1] for q in t[:3]) < z0 or min(q[1] for q in t[:3]) > z1:
                            continue
                        d = _dist(R, t[:3])
                        if d < res.get(names[r], (1e9,))[0]:
                            res[names[r]] = (d, i, x, z)
        out[hw] = res
    return out


def lane_report(zp, log=print):
    r = swept(zp)
    for hw, res in r.items():
        log('  swept box half width %d (length -%d..+%d, height %d..%d): closest solids' % (hw, BACK, FRONT, Y_LO, Y_HI))
        for n, (d, i, x, z) in sorted(res.items(), key=lambda t: t[1][0])[:12]:
            log('    %5.0f cm  %-48s key %d (origin %d, %d)' % (d, n, i, x, z))
    return r


# ------------------------------------------------------------------ audit / check
def node_diff(a, b):
    out = []
    if len(a.nodes) != len(b.nodes):
        return [('node count', len(a.nodes), len(b.nodes))]
    for k in range(1, len(a.nodes)):
        na, nb = a.nodes[k], b.nodes[k]
        if na['props'] != nb['props']:
            out.append(k)
        elif len(na['ctrls']) != len(nb['ctrls']) or any(x != y for x, y in zip(na['ctrls'], nb['ctrls'])):
            out.append((k, 'ctrls'))
    return out


def audit(out_root, zp=None, log=print):
    """kl_vehaudit_1108 on the staged zip: <scratch>/DD10/F07_Main.zip is a HARD LINK (no 265 MB copy). -> the audit result"""
    import kl_vehaudit_1108 as V
    zp = zp or os.path.join(out_root, NAME, ZIP)
    scratch = os.path.join(out_root, NAME, '_audit')
    d = os.path.join(scratch, MAP)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, ZIP)
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(zp, dst)
    except OSError:
        raise SystemExit('REFUSED: cannot hard-link %s (a copy would eat the disk)' % zp)
    try:
        r = V.audit_map(MAP, scratch, log=log)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    for v in r['vehicles']:                  # the audit's one-line summary stops at 4 pierced solids: print them all
        if v.get('pierce'):
            log('  FULL %s: ' % v['name'][-30:] + '; '.join('%s samples %d..%d x%d at %s' % (k, d['first'], d['last'], d['n'], d['at']) for k, d in v['pierce'].items()))
    return r


def check(in_dir, out_root, log=print, deep=True):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(ok, msg):
        log('  %s %s' % ('ok  ' if ok else 'FAIL', msg))
        if not ok:
            bad.append(msg)
    log('check (%s)' % out)
    for n in (ZIP, BOTS):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
            need(changed == ['.buf', '.gms', '.prp'], '%s: only .buf .gms .prp differ (changed: %s)' % (n, changed))
        Bb, Bs = F.Built(base), F.Built(stg)
        vb, Kb = van_keys(Bb)
        vs, Ks = van_keys(Bs)
        cut = Kb.drive()
        need(cut == Ks.drive() and (Kb.npos, Kb.nrot, Kb.frames) == (Ks.npos, Ks.nrot, Ks.frames) and Kb.f2p == Ks.f2p and Kb.f2r == Ks.f2r,
             '%s: key counts and frame tables unchanged (%d pos, %d rot, %d frames, drive %d)' % (n, Kb.npos, Kb.nrot, Kb.frames, cut))
        # keys: only z of the drive's position keys, and only the drive's rotation keys
        dpos = [i for i in range(Kb.npos) if Kb.pos[i] != Ks.pos[i]]
        need(all(i < cut for i in dpos) and all(Kb.pos[i][0] == Ks.pos[i][0] and Kb.pos[i][1] == Ks.pos[i][1] for i in dpos),
             '%s: %d position keys differ, all in the main drive (< %d), only their z' % (n, len(dpos), cut))
        need(all(abs(Ks.pos[i][2] - lane(Ks.pos[i][0])) < 0.01 for i in range(cut)), '%s: every drive key z = lane(x) (1100 up to x %d, %d from x %d)' % (n, LANE_FROM, LANE_Z, LANE_TO))
        need(Ks.pos[0] == Kb.pos[0], '%s: key 0 (the baked pose of the Havok pieces) untouched' % n)
        drot = [r for r in range(Kb.nrot) if Kb.rot[r] != Ks.rot[r]]
        allowed = set(rot_plan(Kb, cut))
        need(set(drot) <= allowed, '%s: %d rotation keys differ, all keys of the main drive only' % (n, len(drot)))
        worst = max(abs(ME.VanKeys.yaw(Ks.rot[r]) - ME.VanKeys.yaw(Kb.rot[r])) for r in drot) if drot else 0.0
        need(worst <= 6.5, '%s: largest yaw change %.1f degrees' % (n, worst))
        hb, hs = Bb.scene.head, Bs.scene.head
        keep = [i for i in range(len(hb)) if not (Kb.offs[5] <= i < Kb.offs[5] + 12 * cut or Kb.offs[2] <= i < Kb.offs[2] + 8 * Kb.nrot)]
        # (the 12-byte triples of the drive and the rotation table are the only bytes allowed to move: everything else of the head is equal)
        need(len(hb) == len(hs) and all(hb[i] == hs[i] for i in keep), '%s: every .buf head byte outside the drive\'s position keys and the rotation table equal' % n)
        need(Bb.files[Bb.ext['.buf']][len(hb):] == Bs.files[Bs.ext['.buf']][len(hs):], '%s: the .buf after the head is byte-equal' % n)
        # entities: .gms
        want = {Bb.ents.index(e) + 1 for e in ()}
        mv = van_nodes(Bb.sc)
        fk = fence_node(Bb)
        diff = []
        for k, (ea, eb) in enumerate(zip(Bb.ents, Bs.ents), 1):
            a = (ea.name, ea.tid, ea.flags, ea.group, ea.model, ea.rot, ea.trans, ea.raw, ea.ref)
            b = (eb.name, eb.tid, eb.flags, eb.group, eb.model, eb.rot, eb.trans, eb.raw, eb.ref)
            if a != b:
                diff.append(k)
        need(sorted(diff) == sorted(list(mv.values()) + [fk]), '%s: .gms: exactly the %d moved nodes and the fence differ (%s)' % (n, len(mv) + 1, diff))
        for k in mv.values():
            ea, eb = Bb.ents[k - 1], Bs.ents[k - 1]
            ta, tb = struct.unpack('<3f', ea.trans[:12]), struct.unpack('<3f', eb.trans[:12])
            need(abs(tb[0] - ta[0]) < 1e-3 and abs(tb[1] - ta[1]) < 1e-3 and abs(tb[2] - ta[2] - (lane(ta[0]) - OLD_Z)) < 1e-2 and ea.rot == eb.rot and ea.flags == eb.flags,
                 '%s: %s only z moved by %.1f' % (n, Bb.sc.names[k], tb[2] - ta[2]))
        ea, eb = Bb.ents[fk - 1], Bs.ents[fk - 1]
        need(eb.flags == ea.flags | HIDDEN and ea.trans == eb.trans, '%s: fence: only the flag 0x400 set' % n)
        # .prp: the same nodes only
        pd = node_diff(Bb.sc, Bs.sc)
        need(sorted(pd) == sorted(list(mv.values()) + [fk]), '%s: .prp: exactly those nodes differ (%s)' % (n, pd))
        for k in mv.values():
            lab = J.labels('dd', Bs.sc.cls(k))
            va, vb_ = kl_fa.node_values(Bb.sc, k), kl_fa.node_values(Bs.sc, k)
            same = all(x == y for i, (x, y) in enumerate(zip(va, vb_)) if lab[i] != 'ZGEOM[2]')
            need(same and abs(vb_[lab.index('ZGEOM[2]')][2] - va[lab.index('ZGEOM[2]')][2] - (lane(va[lab.index('ZGEOM[2]')][0]) - OLD_Z)) < 1e-2,
                 '%s: %s .prp only ZGEOM[2] z, equal to its .gms' % (n, Bb.sc.names[k]))
        lab = J.labels('dd', Bs.sc.cls(fk))
        va, vb_ = kl_fa.node_values(Bb.sc, fk), kl_fa.node_values(Bs.sc, fk)
        need(all(x == y for i, (x, y) in enumerate(zip(va, vb_)) if lab[i] != 'ZGEOM[3]') and vb_[lab.index('ZGEOM[3]')] == 1 and va[lab.index('ZGEOM[3]')] == 0,
             '%s: fence .prp only ZGEOM[3] 0 -> 1' % n)
        need(Bs.sc.p.serialize() == Bs['.prp'] and kl_gms.pack(Bs.scene.write()[0]) == Bs['.gms'], '%s: .prp and .gms round-trip' % n)
        need(Bs['.hvk' if '.hvk' in Bs.ext else '.HVK'] == Bb['.hvk' if '.hvk' in Bb.ext else '.HVK'], '%s: the .HVK (collision) is byte-equal: the fence keeps its collision' % n)
    md = open(os.path.join(out, BASE)).read().strip()
    need(md == fmd5(os.path.join(out, ZIP)), 'bots.base.md5 = md5 of the plain staged zip')
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in (ZIP, BOTS, BASE):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    need("'%s'" % TAG in inst and "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5[ZIP] in inst and "MAP, TAG = '%s'" % MAP in inst, 'install.py MAP %s, TAG %s and LIVE_ZIP_MD5 pinned' % (MAP, TAG))
    r = subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--dry', '--min-free-mb', '0'], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:120]
    # on a nearly full game drive the dry run stops at its free-space gate AFTER every md5 pin passed: that is not a pin failure
    need(r.returncode == 0 or 'MB free on the game drive' in last, 'install.py --dry pins ok (exit %d: %s)' % (r.returncode, last))
    if deep:
        res = lane_report(os.path.join(out, ZIP), log)
        for pat, lim in MIN_CLEAR.items():
            worst = min((v[0] for n_, v in res[HALF_AUDIT].items() if n_.startswith(pat)), default=None)
            need(worst is None or worst >= lim, 'swept box (half width %d) to %s* >= %d cm (min %s)' % (HALF_AUDIT, pat, lim, 'n/a' if worst is None else '%.0f' % worst))
    log('check: %s' % ('OK' if not bad else '%d FAIL' % len(bad)))
    return not bad


def main(a):
    if not a or a[0] not in ('stage', 'check', 'lane', 'audit'):
        print(__doc__)
        return 2
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    in_dir, out_root = get('--in-dir', LIVE), get('--out-root', OUT_ROOT)
    if a[0] == 'lane':
        lane_report(get('--zip', os.path.join(out_root, NAME, ZIP)))
        return 0
    if a[0] == 'audit':
        audit(out_root, get('--zip', None))
        return 0
    if a[0] == 'stage':
        stage(in_dir, out_root)
    return 0 if check(in_dir, out_root) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
