"""kl_lanes_1025.py - van lane clearance + loot fixes for DM01 / DM02 / DM03. Written 2026-10-25, OFFLINE; reads zips, writes only under a stage folder.

Owner: "van just clips ... even on dm01 it just clips through a police car". The escape van is key-framed (teleported, no collision response), so the fix is
a CLEAR LANE (tools/kl_vanlane_1025.py proves it). This module holds the map edits; every one is a member-level patch of a COPY of the live zip.

DM01  the three police cars (KL_Cars!\\Cars\\V_Santana_CopCar0N_00, MatPosAnim groups, visual only) drive in from the east street and used to stop at
      x 6850, z 20000 / 20550 / 21100 - car 2 stood IN the van's west-running leg (z ~ 20600). They now stop on the verge, off the van's swept footprint.
      Only the KEYS tables are rewritten IN PLACE in the .buf head (the position triple table offs[5], the int16 quaternion table offs[2]): no key
      is added or dropped, no entity moves, no id changes. Rule = kl_dm01cars_1025.cars(plan=...): every key sits at the same ARC FRACTION of the new
      polyline, every rotation key keeps its heading RELATIVE to the path tangent (worst error <= 1 degree is asserted).
usage (from tools/):  python kl_lanes_1025.py stage <root> [DM01 DM02 DM03]   -> <root>/<MAP>/{in,stage} (in/ holds the copied live zip)
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_map_escape as ME, kl_vanlane_1025 as VL
import kl_bots_kick_1025 as KK

TAG = '.before-1025lanes'
GAME = KK.GAME
MAPS = collections.OrderedDict([
    ('DM01', ('F01', 'F01_Main.zip', 'fbffea91fef4a4168bcc50453ad0e0c1')),
    ('DM02', ('F02', 'F02_Main.zip', '7ebc7e463b865c76abf79964694cd672')),
    ('DM03', ('F03', 'F03_Main.zip', '1ebff7bb919b517245e6032391570572'))])

# ---- DM01 cars. (road x, z of the turn, stop x). GUESS: the sites were searched by work/cand1.py (flat, y ~ 0, nothing 25..220 above the floor, main nav part,
# >= 250 from every cop post, inside the old KL_Cars! .oct item box x 6350..9050 z 16600..21600, resting gap to the van's swept footprint >= 250);
# CAR_BOX (half 240 x 100) is a GUESS for a Santana. The columns x 8250 / 8400 / 8550 and the start z 17100 are the live ones.
R_TURN = 450.0
OLD_START_Z = 17100.0     # the z where the live (stock-derived) car keys start
# Round 2: the cars spawn 250 further north. The van waits at its key 0 (8406, 16687) from the round's start (frames 0..49 in the stock van, re/map_escape.md 9.2), and a car at
# z 17100 overlapped that parked pose for the first 2 s (CopCar02: frames 0..52 of 321, measured with the CAR_BOX / van footprint); at 17350 no column touches it.
START_Z = 17350.0
# Round 2 (2026-10-25): the stops/columns come from a search over 392 drivable arc routes (work: scratchpad w/srch5..tri.py): each candidate keeps >= 330 of rest gap (376 the least of the three) to the van's
# whole path (VL.lane_check footprint, CAR_BOX = GUESS 500 x 220), and the triple is chosen so the cars keep >= -20 (a box overlap of 20 at the worst frame while both drive,
# using the real per-frame arc fractions of each car's own MatPosAnim; the round-1 columns had -70) and >= 700 between their rest poses.
CARS01 = collections.OrderedDict([
    ('V_Santana_CopCar01_00', (8150.0, 19800.0, 6600.0)),     # stop (6600, 19800)
    ('V_Santana_CopCar02_00', (8400.0, 21150.0, 7800.0)),     # stop (7800, 21150)
    ('V_Santana_CopCar03_00', (8600.0, 19650.0, 7550.0))])    # stop (7550, 19650)


def lane_path(xr, zt, xs, r=R_TURN, z0=START_Z):
    """North along x = xr, a quarter circle of radius r to the west, west along z = zt to x = xs -> [(x, z)] (kl_dm01fb_1025.lane_path)."""
    pts = [(xr, z0), (xr, zt - r)]
    for a in range(15, 91, 15):
        t = math.radians(a)
        pts.append((xr - r + r * math.cos(t), zt - r + r * math.sin(t)))
    pts.append((xs, zt))
    return pts


def lanes_dm01(name, pts, K):
    """DM01: the whole route is re-laid (lane_path) and every key sits at the same arc fraction."""
    xr, zt, xs = CARS01[name]
    old = ME.Poly(pts)
    new = ME.Poly([(x, 0.0, z) for x, z in lane_path(xr, zt, xs)])
    if abs(pts[0][2] - OLD_START_Z) > 1:     # (round 2: the start COLUMN and z move - the whole route is re-laid - the old keys start on the old spawn line)
        raise ValueError('%s: first key %s is not on the old spawn line z %d' % (name, pts[0], OLD_START_Z))
    return [new.at(old.cum[i] / old.len * new.len) for i in range(len(pts))]


# DM02 (round 2, 2026-10-25): CopCar01 (child Pos_Police01) STARTS 61 from the van's swept footprint and drives ALONG the van's street (gap < 0 for its first 2100 units of 4365),
# resting 1779 away. The cars cannot be shifted sideways (asphalt ends at x 2030, then a 28-high parking pavement: round 1), so its route is SHORTENED instead: the same keys
# are re-spread over the part of its own drivable route that stays >= DM02_CLEAR from the van (start pose included), the rest pose is untouched. GUESS: the car popping in
# 20 m later is not seen (the stock start is 3.5 m of road from where the players start); the drive-in lasts as long as before, only slower.
DM02_CAR = 'V_Santana_CopCar01_00'
DM02_CLEAR = 330.0


def dm02_start_s(zp, name=DM02_CAR, clear=DM02_CLEAR):
    """-> (s0, len, [(s, gap)]) the first arc length of the car's own route from which every pose keeps >= clear from the van's swept footprint."""
    L = ME.Level(zp)
    ends = VL.ends_of(L)
    van = VL.van_nodes(L)[0]
    K, cut, pts = VL.van_road(L, van, ends)
    back, front, half = VL.van_footprint(L, van)
    road = ME.Poly([(p[0], p[1] - ME.VAN_UP, p[2]) for p in pts])
    vs, s = [], 0.0
    while s <= road.len:
        p, t = road.at(s), road.tan(s)
        vs.append(VL.rect(p[0], p[2], math.atan2(t[0], t[1]), back, front, half))
        s += 20.0
    top = L.sc.top[van]
    for k, wp, Kc, Rc in VL.movers(L, ends, set(range(top, L.sc.end[top]))):
        if L.sc.names[k] != name:
            continue
        cp = ME.Poly(wp)
        prof, s = [], 0.0
        while True:
            s = min(s, cp.len)
            p, t = cp.at(s), cp.tan(s)
            b = VL.rect(p[0], p[2], math.atan2(t[0], t[1]), VL.CAR_BOX[0], VL.CAR_BOX[0], VL.CAR_BOX[1])
            prof.append((s, min(VL.gap(b, v) for v in vs)))
            if s >= cp.len:
                break
            s += 10.0
        s0 = 0.0
        for s, g in prof:
            if g < clear:
                s0 = s + 10.0
        return s0, cp.len, prof
    raise ValueError('no mover %s' % name)


def lanes_dm02(s0):
    def fn(name, pts, K):
        old = ME.Poly(pts)
        return [old.at(s0 + (old.cum[i] / old.len) * (old.len - s0)) for i in range(len(pts))]
    return fn


def relay_cars(zp, log=print, names=None, lane_fn=None):
    """-> ({'.buf': new bytes}, [report lines]). Re-lays the named cars' position and rotation keys (default: the three DM01 cop cars on the verge)."""
    names = CARS01 if names is None else names
    lane_fn = lane_fn or lanes_dm01
    with zipfile.ZipFile(zp) as z:
        nm = [n for n in z.namelist() if n.lower().endswith('.buf')]
        assert len(nm) == 1, nm
        buf = bytearray(z.read(nm[0]))
    L = ME.Level(zp)
    ends = VL.ends_of(L)
    head = L.scene.head
    assert bytes(buf[:len(head)]) == bytes(head), 'the .buf member does not start with the scene head'
    out = []
    todo = {}
    for k, wp, K, R in VL.movers(L, ends, set()):
        name = L.sc.names[k]
        if name not in names:
            continue
        if any(abs(R[i][j] - (1.0 if i == j else 0.0)) > 1e-6 for i in range(3) for j in range(3)):
            raise ValueError('%s: the parent frame is not the identity' % name)
        pts = [tuple(K.pos[i]) for i in range(K.npos)]
        while pts and pts[-1] == (0.0, 0.0, 0.0):
            pts.pop()
        old = ME.Poly(pts)
        lane = lane_fn(name, pts, K)
        new = ME.Poly(lane)
        first = {}
        for f in range(K.frames - 1, -1, -1):
            first[K.f2r[f]] = f
        rots, worst = [], 0.0
        for r, q in enumerate(K.rot):
            kp = K.f2p[first[r]]
            s_old = old.cum[min(kp, len(pts) - 1)]
            s_new = new.cum[min(kp, len(pts) - 1)]
            rel = ME._wrap(K.yaw(q) - ME._heading(old.tan(s_old, ME.AXLES)))
            want = ME._heading(new.tan(s_new, ME.AXLES)) + rel
            q2 = K.turned(q, want - K.yaw(q))
            worst = max(worst, abs(ME._wrap(K.yaw(q2) - want)))
            rots.append(q2)
        if worst > 1.0:
            raise ValueError('%s: a rotation key is %.1f degrees off its heading' % (name, worst))
        todo[name] = (K, lane, rots)
        out.append('%s: %d position keys, %d rotation keys; stop (%d, %d) -> (%d, %d); worst rotation error %.2f deg' % (
            name, len(lane), len(rots), pts[-1][0], pts[-1][2], lane[-1][0], lane[-1][2], worst))
    if sorted(todo) != sorted(names):
        raise ValueError('cars found: %s' % sorted(todo))
    for name, (K, lane, rots) in todo.items():
        for i, p in enumerate(lane):
            struct.pack_into('<3f', buf, K.offs[5] + 12 * i, *p)
        for i, q in enumerate(rots):
            struct.pack_into('<4h', buf, K.offs[2] + 8 * i, *q)
    return {nm[0]: bytes(buf)}, out


# ------------------------------------------------------------------ patch + stage
def md5(p):
    return KK.md5(p)


def patch_zip(src, dst, repl):
    return KK.patch_zip(src, dst, repl)
