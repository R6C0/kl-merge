r"""kl_vehroutes_street2_1108.py - DM01B (Hot Coffee II, slot F03): the escape van on the MAIN STREET (kl_vehroutes_street_1108's drive) AND a way there on foot and for bots.
Written 2026-11-08, OFFLINE: reads the live DM01B zip, writes NEW files (never the live ones). Replaces the stage DM01B_street (same live pins) and the reverse-out stage
(kl_vehroutes_1108): install ONE.

WHY (measured, kl_route bounded walk, see re/vehicle_routes_1108.md): in DM01B_street the van stops on the street (4458, 31907) but nobody can walk there: the 125-high planter
strip SO1103_M01_DonutShop_PlantD_01 (REF 23079, one object, x 1999..8000, z 31230..31610, 380 deep) and the invisible box InvisibleBlocker_06 (REF 22709, at 3839, 0, 31497) shut
the alley from the street, and the nav mesh holds the street as a five-polygon island (part 17) with no link to the alley (part 0).

WHAT THIS DOES (on top of the street stage's drive; nothing of it is re-timed)
  1. PLANTER: the strip is ONE model, it cannot be cut in two, so the whole piece is SUNK by 160 (its top 125 -> -35, under the tarmac at -15; render + .gms + .prp) and its
     collision placement is cut from the .HVK (kl_escape.cut_collision, the bank-vault way: a filler keeps the list codes valid). The bush rows (SO1103_M01_DonutShop_Bushes_12/13,
     z 31512..31723, their own objects) stay. The west planter PlantD_03 (x 1000..2000) stays. The alley's north side is now an open sidewalk onto the street.
  2. BLOCKER: InvisibleBlocker_06's collision is cut the same way (the object is sunk by 160 too: it has no model that draws).
  3. NAV: kl_nav_bridge adds three one-polygon areas, all APPENDED (no index moves):
       bridge 0  alley polygon 321 edge 2 (2238,31362)->(4660,31170), the whole edge, to a throat x 3500..4100 at z 31400
       bridge 1  throat -> street polygon 206 edge 1 (4481,31589)->(1235,31589), the whole edge
       bridge 2  street polygon 210 edge 0 (1235,32275)->(5364,32275) north to z 32480: the street mesh stopped 77..190 short of the 14 merc defend posts and AllyEscapeBox the street stage
                 turned onto z 32285..32465 (every cell of that rectangle is walkable floor, measured by the same walk).
     Alley part 0 and street part 17 become ONE part. Throat clear of the palm trunk (x 4480..4620, z 31580..31700) and the phone booth (x 4840..5000, z 31260..31400).
  4. The bots zip is re-derived (kl_botsonline.convert, eAllTypes) and the base md5 written.
NOT TOUCHED: the level's bound boxes (no LevelBound box lies within 3000 of z 31907: the 14 of the map are Dead Men's own, 8 parked at y -60000 and the rest at z <= 17000; the walls at
z ~32550 and x -400 / 10590 hold the street in: flood walk below), .oct / .rmi / .rmc, hooks, ini.
GUESSES: (1) a sunk entity + a cut placement opens the player's way (the DM02 shutter patch3 and the bank vault used the same pair; whether a static placement inside a shared list shape
stays cut at run time is the same open question there); (2) the nav bridge forms (kl_nav_bridge: portal vertex order, corner normals) are its documented GUESSES, run-time proof is the bench;
(3) the throat width (600) is enough for the engine's pathing; (4) sinking the whole 6000-long planter is acceptable looks (it is one piece).
usage: python kl_vehroutes_street2_1108.py stage <live DM01B dir> <out dir>      python kl_vehroutes_street2_1108.py check <F03_Main.zip> [<live F03_Main.zip>]"""
import hashlib, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F, kl_graft, kl_gms, kl_hvk, kl_escape, kl_nav_bridge as NB
import kl_vehroutes_street_1108 as S, kl_map_escape as ME

LIVE_MD5 = S.LIVE_MD5
PLANTER_REF, BLOCKER_REF = 23079, 22709
SINK = -160.0
MIN_FREE_MB = 300           # headroom the install keeps on the game drive besides backup + new file (C: is nearly full; 1024 would refuse)
THROAT_X, THROAT_Z = (3500.0, 4100.0), 31400.0
NORTH_Z = 32480.0
# pinned mesh edges (polygon, edge) with the corner pairs they must have: a different mesh refuses
ALLEY = (321, 2, (2238.0, 31362.0), (4660.0, 31170.0))
STREET = (206, 1, (4481.0, 31589.0), (1235.0, 31589.0))
NORTH = (210, 0, (1235.0, 32275.0), (5364.0, 32275.0))
BOX_OPEN = (1000.0, 7500.0, 30300.0, 32500.0)      # the bounded walk's box (kl_vehroutes_1108 walk: alley + street)
FLOOD_BOX = (-12000.0, 16000.0, 28000.0, 40000.0)


def md5(p):
    return S.md5(p)


def _edge(nav, spec):
    p, e, a, b = spec
    vs = nav.pv[p]
    v0, v1 = vs[e], vs[(e + 1) % len(vs)]
    for got, want in ((v0, a), (v1, b)):
        if abs(got[0] - want[0]) > 2 or abs(got[2] - want[1]) > 2:
            raise ValueError('nav polygon %d edge %d is (%d,%d)->(%d,%d), not the pinned (%d,%d)->(%d,%d)' % (
                p, e, v0[0], v0[2], v1[0], v1[2], a[0], a[1], b[0], b[1]))
    if nav.en[p][e] != -1:
        raise ValueError('nav polygon %d edge %d is not a border (neighbour %s)' % (p, e, nav.en[p][e]))
    return v0, v1


def nav_bridges(nav):
    """The bridge list kl_nav_bridge.add_bridges takes (3 areas), from the mesh nav (kl_fa_bots.Nav). Corner order: the old edge reversed first (corners[k] = the old edge's END),
    as kl_fa_v2_hotcoffee.nav_bridges. Heights: alley y 0, street y -15 (the meshes' own)."""
    a0, a1 = _edge(nav, ALLEY)
    b0, b1 = _edge(nav, STREET)
    c0, c1 = _edge(nav, NORTH)
    ty0, ty1 = a0[1], a0[1]
    t0, t1 = (THROAT_X[0], ty0, THROAT_Z), (THROAT_X[1], ty1, THROAT_Z)
    n0 = (c1[0], c1[1], NORTH_Z), (c0[0], c0[1], NORTH_Z)
    return [dict(corners=[a1, a0, t0, t1], joins={0: ('old', ALLEY[0], ALLEY[1]), 2: ('new', 1, 0)}),
            dict(corners=[t1, t0, b1, b0], joins={0: ('new', 0, 2), 2: ('old', STREET[0], STREET[1])}),
            dict(corners=[c1, c0, n0[1], n0[0]], joins={0: ('old', NORTH[0], NORTH[1])})]


def convex(P):
    """True when every turn of the polygon (a list of (x, z) pairs) has the stock (negative) sign."""
    n = len(P)
    for k in range(n):
        a, b, c = P[k], P[(k + 1) % n], P[(k + 2) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) >= 0:
            return False
    return True


def node_of(B, ref):
    ks = [k for k, e in enumerate(B.ents, 1) if e.ref == ref]
    if len(ks) != 1:
        raise ValueError('REF %d: %d nodes' % (ref, len(ks)))
    return ks[0]


def sink(B, k, dy):
    """ZGEOM[2].y += dy in the .prp and the .gms record of node k (its parents must be identity)."""
    e = B.ents[k - 1]
    t = struct.unpack('<3f', e.trans[:12])
    w = B.at(k)
    if any(abs(w[i] - t[i]) > 0.5 for i in range(3)):
        raise ValueError('%s: its parents are not identity at the origin (local %r, world %r)' % (B.sc.path[k], t, w))
    S.put(B, k, pos=(t[0], t[1] + dy, t[2]))
    return t


# ---- the van comes from, and leaves to, a place nobody can see or stand (owner 2026-11-08: "every vehicle comes from and leaves to a place nobody can see")
# Measured on the whole walkable flood (viewshed: every 5th flood cell as viewer, eye 170, targets at 150; occluders = drawn walls / buildings >150 high, foliage / glass / fences
# not counted = conservative): the street z 31907 is seen from everywhere, but behind the west block (side gap x -8900..-7300, south of z 31400) and behind the east block
# (x 10600..17600, z 30200..31000, entered from the east end x >= 16800) there are free, ground-covered, never-seen pockets (ground y -15 under both: measured).
WAIT_W = ((-8000.0, 30500.0), (-8000.0, 31500.0))   # the wait pocket W and the straight north out of it (yaw 0)
ARC_W = 407.0                                       # quarter turn onto the street (centre (-7593, 31500)); the wall x -7100..-6700 ends at z 31600
END_ARC_X = 17000.0                                 # the street is left at x 17000: quarter turn south at radius 400, then south into the east pocket
ARC_E = 400.0
END_E = (17400.0, 30400.0)
STEP_CAP = 116.0                                    # per-key step ceiling (the stock vans measure 60..118 per key; one key = one frame on the drive)
STOP_KEY_X = 4454.0                                 # the live drive's stop (key 156 of the street stage): arrival = keys 0..156, departure = keys 156..390


class Path:
    """A dense polyline (5 units) with arc length and the heading (degrees, atan2(dx, dz) = kl_map_escape.VanKeys.yaw's) of each sample."""
    def __init__(self, pts):
        self.p = [pts[0]]
        for q in pts[1:]:
            a = self.p[-1]
            n = max(1, int(math.dist(a, q) / 5.0))
            self.p += [(a[0] + (q[0] - a[0]) * k / n, a[1] + (q[1] - a[1]) * k / n) for k in range(1, n + 1)]
        self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.s.append(self.s[-1] + math.dist(a, b))
        self.L = self.s[-1]

    def at(self, d):
        d = max(0.0, min(self.L, d))
        import bisect
        i = min(max(1, bisect.bisect_left(self.s, d)), len(self.p) - 1)
        a, b = self.p[i - 1], self.p[i]
        t = (d - self.s[i - 1]) / ((self.s[i] - self.s[i - 1]) or 1.0)
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))


def arc(c, r, a0, a1, n=24):
    """Points of the arc about c, angles in degrees measured from +x towards +z."""
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def arrival_path():
    c = (WAIT_W[1][0] + ARC_W, WAIT_W[1][1])                       # turning right (north -> east) about a centre east of the straight
    return Path([WAIT_W[0], WAIT_W[1]] + arc(c, ARC_W, 180.0, 90.0)[1:] + [(STOP_KEY_X, 31907.0)])


def departure_path():
    c = (END_ARC_X, 31907.0 - ARC_E)                                # east -> south about a centre south of the street
    return Path([(STOP_KEY_X, 31907.0), (END_ARC_X, 31907.0)] + arc(c, ARC_E, 90.0, 0.0)[1:] + [END_E])


def relay_keys(K):
    """-> (positions, rotations): the drive's keys re-laid on the two paths. Arrival keys (before the stop) go along arrival_path, departure keys along departure_path,
    with the old per-key steps scaled to the new lengths (profile kept, peak capped at STEP_CAP). Rotation keys keep
    their sway and get the path's heading (K.turned by new yaw - old yaw). Crash keys (>= K.drive()) are left as the street stage had them."""
    cut = K.drive()
    a = next(i for i in range(cut) if K.pos[i][0] >= STOP_KEY_X)
    A, D = arrival_path(), departure_path()
    pos, yaw = list(K.pos), {}

    def dists(idx, L):
        """New arc length (from the leg's start) of each key of idx: the old per-key steps scaled to the new length, any step over STEP_CAP cut to the cap and the excess
        spread over the other steps in proportion (the speed profile keeps its shape, the peak does not exceed the stock one)."""
        st = [max(0.0, K.pos[i][0] - K.pos[j][0]) for j, i in zip(idx, idx[1:])]
        tot = float(sum(st))
        w = [x * L / tot for x in st]
        for _ in range(60):
            over = sum(max(0.0, x - STEP_CAP) for x in w)
            if over < 1e-6:
                break
            free = sum(x for x in w if x < STEP_CAP)
            w = [STEP_CAP if x >= STEP_CAP else x * (1 + over / free) for x in w]
        out = [0.0]
        for x in w:
            out.append(out[-1] + x)
        return out
    ia, id_ = list(range(0, a + 1)), list(range(a, cut))
    da, dd = dists(ia, A.L), dists(id_, D.L)
    for i in range(cut):
        (px, pz), h = A.at(da[i]) if i < a else D.at(dd[i - a])
        pos[i] = (px, K.pos[i][1], pz)
        yaw[i] = h
    # the rotation key of each drive frame follows the heading of that frame's position key (a rot key used by several frames: the last wins, all within a step)
    rot = list(K.rot)
    for f in range(len(K.f2p)):
        i = K.f2p[f]
        if i < cut:
            r = K.f2r[f]
            rot[r] = K.turned(K.rot[r], yaw[i] - K.yaw(K.rot[r]))
    return pos, rot, a


def spin_m9(m9, deg):
    """ZGEOM[1] columns (stored 3rd, 2nd, 1st) turned by deg about world Y: c -> (c0 cos + c2 sin, c1, -c0 sin + c2 cos) (deg 180 = street stage's turn_m9)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    cols = [m9[6:9], m9[3:6], m9[0:3]]
    cols = [(v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c) for v in cols]
    return list(cols[2]) + list(cols[1]) + list(cols[0])


def build(src, log=print):
    """live zip -> {member: bytes} of the changed members + a report dict. The street stage's pass runs first (in memory, through a scratch zip), then the opening."""
    import tempfile
    scratch = tempfile.mkdtemp(prefix='street2_', dir=os.environ.get('KL_SCRATCH'))
    try:
        tmp = os.path.join(scratch, 'pass1.zip')
        S.write(src, tmp, log)
        B = F.Built(tmp)
        zin = zipfile.ZipFile(tmp)
        prp_name = B.ext['.prp']
        if B.sc.p.serialize() != B.files[prp_name]:
            raise ValueError('the .prp does not round-trip (stop: nothing was written)')
        orig_gms = kl_gms.unpack(B.files[B.ext['.gms']])
        if B.scene.write()[0] != orig_gms:
            raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
        kp, kb = node_of(B, PLANTER_REF), node_of(B, BLOCKER_REF)
        if not B.sc.names[kp].endswith('SO1103_M01_DonutShop_PlantD_01') or not B.sc.names[kb].endswith('InvisibleBlocker_06'):
            raise ValueError('REFs %d / %d are not the planter / blocker: %s / %s' % (PLANTER_REF, BLOCKER_REF, B.sc.names[kp], B.sc.names[kb]))
        before = [sink(B, kp, SINK), sink(B, kb, SINK)]
        # the van's keys: from the west pocket, to the east pocket
        top, kids, _stop, _posts = S.nodes_of(B)
        vk, K = S.van_keys(B)
        pass1 = (K.pos[K.f2p[0]], K.yaw(K.rot[K.f2r[0]]))
        npos, nrot, stopkey = relay_keys(K)
        head = bytearray(B.scene.head)
        for i, p in enumerate(npos):
            struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
        for i, q in enumerate(nrot):
            struct.pack_into('<4h', head, K.offs[2] + 8 * i, *q)
        B.scene.head = bytes(head)
        yaw0 = K.yaw(nrot[K.f2r[0]])
        pose0 = (npos[K.f2p[0]], yaw0)
        r9 = struct.unpack('<9f', B.ents[kids['V_Van_00'] - 1].rot[:36])
        S.put(B, kids['V_Van_00'], npos[K.f2p[0]], spin_m9(r9, yaw0 - pass1[1]))
        vanrefs = sorted({B.ents[j - 1].ref for j in range(kids['V_Van_00'], B.sc.end[kids['V_Van_00']])})
        steps = [math.dist(npos[i], npos[i - 1]) for i in range(1, K.drive())]
        log('kl_vehroutes_street2_1108: van keys re-laid: waits at (%d, %d) yaw %d, arrival keys 0..%d, departure ends at (%d, %d); max step per key %.0f (stock vans 60..118, old %.0f)' % (
            npos[K.f2p[0]][0], npos[K.f2p[0]][2], round(yaw0), stopkey, npos[K.drive() - 1][0], npos[K.drive() - 1][2], max(steps),
            max(math.dist(K.pos[i], K.pos[i - 1]) for i in range(1, K.drive()))))
        # nav
        nav = F.Nav(B.scene.nav)
        parts = {nav.part[ALLEY[0]], nav.part[STREET[0]], nav.part[NORTH[0]]}
        if len(parts) != 2 or nav.part[STREET[0]] != nav.part[NORTH[0]]:
            raise ValueError('the street is no longer a separate mesh island (parts %s)' % sorted(parts))
        bridges = nav_bridges(nav)
        for i, br in enumerate(bridges):
            if not convex([(c[0], c[2]) for c in br['corners']]):
                raise ValueError('bridge %d is not convex' % i)
        newnav, nrep = NB.add_bridges(B.scene.nav, bridges, log=lambda *a: None)
        n2 = F.Nav(newnav)
        if len({n2.part[ALLEY[0]], n2.part[STREET[0]], n2.part[NORTH[0]]}) != 1:
            raise ValueError('the mesh is still in islands after the bridges')
        B.scene.nav = newnav
        gms, buf = B.scene.write()
        # collision
        hn = B.ext['.HVK']
        hv = kl_hvk.Hvk(B.files[hn])
        if hv.serialize() != B.files[hn]:
            raise ValueError('the .HVK does not round-trip')
        ME.van_hvk(hv, dict(hvk=dict(static=[], van=vanrefs, old=[list(pass1[0]), pass1[1]], new=[list(pose0[0]), pose0[1]])), log)
        n0 = hv.static_count()
        for r in (PLANTER_REF, BLOCKER_REF):
            have = [s.type for s in hv.shapes for i in s.inst if kl_hvk.ref(i) == r]
            if have != [kl_hvk.STATIC]:
                raise ValueError('REF %d owns %s in the .HVK (want exactly one STATIC placement)' % (r, have))
        kl_escape.cut_collision(hv, {PLANTER_REF, BLOCKER_REF}, log)
        if hv.static_count() != n0 or any(kl_hvk.ref(i) in (PLANTER_REF, BLOCKER_REF) for s in hv.shapes for i in s.inst):
            raise ValueError('the cut left a placement or changed the static count')
        out = {prp_name: B.sc.p.serialize(), B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf, hn: hv.serialize()}
        members = [(n, out[n] if n in out else B.files[n]) for n in B.order]
        rep = dict(nav=nrep, sunk=before, statics=n0, parts=[len(set(n2.part))])
        log('kl_vehroutes_street2_1108: planter %d + blocker %d sunk %g and cut from the .HVK; %d nav areas appended (polygons %s); one mesh part for alley + street' % (
            PLANTER_REF, BLOCKER_REF, SINK, len(bridges), nrep['polygons']))
        return members, rep
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def write(src, dst, log=print):
    members, rep = build(src, log)
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    return rep


# ------------------------------------------------------------------ checks
def flood(zp, opened=frozenset(), start=(3000.0, -15.0, 30800.0), box=FLOOD_BOX):
    """-> (the cell states the walker reaches from `start` inside `box`, the grid). Bounded only by the box; touching it = not closed."""
    import kl_route as R
    run = R._Run(zp, mesh=False)
    g = run.g
    orig = g.step

    def step(i, j, y, op):
        x, z = (i + 0.5) * R.CELL, (j + 0.5) * R.CELL
        if not (box[0] <= x <= box[1] and box[2] <= z <= box[3]):
            return None
        return orig(i, j, y, op)
    g.step = step
    try:
        cost, _prev, _end, _edge = R._search(g, g.feet(start, opened), None, None, opened, None)
    finally:
        g.step = orig
    return cost, run

VIEW_R = 7000.0
SOFT = ('Bush', 'Tree', 'Palm', 'Fence', 'Chainlink', 'Glass', 'Win_', 'Wire', 'Plant')      # GUESS: drawn see-through / thin: the "soft" variant lets sight pass them
SKIP = ('Mist', 'Glow', 'Backdrop', 'Distance', 'Fog', 'Smoke', 'Sky', 'Van', 'Escape', 'Light')


def viewshed(zp, log=print, step=12):
    """Who can see the van where it waits, on its way and where it ends? Viewers = EVERY reachable floor cell of the walk flood (one per 400 x 400 x 150 block; players
    move, so not only the spawn points; eye +170) within VIEW_R of the point; point = van position +100. Two occluder sets: SOLID (every drawn triangle but fog / glow / sky /
    the van itself) and SOFT (also without bushes, trees, fences, glass: GUESS names). -> dict(start, end, route=[(key, x, z, solid, soft)...], viewers)."""
    import numpy as np, kl_arrival_1107 as A, kl_vehroutes_1108 as V
    cost, _r = flood(zp)
    import kl_route as R
    seen = {}
    for i, j, y in cost:
        x, z = (i + .5) * R.CELL, (j + .5) * R.CELL
        seen.setdefault((int(x // 400), int(z // 400), int(y // 150)), (x, float(y), z))
    vs = list(seen.values())
    B, K = V.van_keys(zp)
    cut = K.drive()
    pts = [K.pos[K.f2p[0]]] + [K.pos[i] for i in range(0, cut, step)] + [K.pos[cut - 1]]
    lo = np.array([-10000.0, -1500.0, 28500.0])
    hi = np.array([18500.0, 4500.0, 34500.0])
    tr, ow, nm = A.geom(zp, region=(lo, hi), log=lambda *a: None)
    tr, ow = np.asarray(tr, np.float64), np.asarray(ow)
    bad = [i for i, x in enumerate(nm) if any(w in x for w in SKIP)]
    ok = np.isfinite(tr).all(axis=(1, 2)) & (np.abs(tr).max(axis=(1, 2)) < 2e5) & ~np.isin(ow, bad)
    tr, ow = tr[ok], ow[ok]
    soft = [i for i, x in enumerate(nm) if any(w in x for w in SOFT)]
    keep = ~np.isin(ow, soft)
    Ms = A.Mesh(tr.astype(np.float32), ow, nm)
    Mf = A.Mesh(tr[keep].astype(np.float32), ow[keep], nm)
    res = []
    for n, p in enumerate(pts):
        q = (p[0], p[1] + 100.0, p[2])
        near = [v for v in vs if math.dist(v, q) < VIEW_R]
        row = [sum(1 for v in near if not A.seg_hits(M, (v[0], v[1] + 170.0, v[2]), q)) for M in (Ms, Mf)]
        res.append((n, p[0], p[2], len(near)) + tuple(row))
    return dict(viewers=len(vs), route=res)


def print_viewshed(vr, log=print):
    log('  6 viewshed: %d viewers (every reachable floor block); per route sample: (x,z) within %d / seen solid / seen soft' % (vr['viewers'], VIEW_R))
    for n, x, z, near, a, b in vr['route']:
        log('    #%-3d (%6d,%6d) within %4d  solid %4d  soft %4d' % (n, x, z, near, a, b))

STRIP = (1900.0, 8100.0, 31150.0, 31700.0)       # the sunk planter strip's footprint (x 2000..8000, z 31230..31610) + a margin


def strip_ground(zp, log=print):
    """Is there drawn ground (an upward render face between y -60 and +20, the planter itself excluded) under every 300 x 100 sample of the sunk planter strip?
    -> list of the sample points without (empty = the sunk strip shows tarmac / grit, no hole to the void)."""
    import numpy as np, kl_arrival_1107 as A
    tr, ow, nm = A.geom(zp, region=(np.array([STRIP[0], -3000.0, STRIP[2]]), np.array([STRIP[1], 3000.0, STRIP[3]])), log=lambda *a: None)
    tr, ow = np.asarray(tr, np.float64), np.asarray(ow)
    n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    ny = np.abs(n[:, 1]) / np.maximum(np.linalg.norm(n, axis=1), 1e-9)
    own = [i for i, x in enumerate(nm) if 'PlantD_01' in x]
    m = (ny > 0.7) & ~np.isin(ow, own)
    T = tr[m]
    a, b, c = T[:, 0][:, [0, 2]], T[:, 1][:, [0, 2]], T[:, 2][:, [0, 2]]
    d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    d = np.where(np.abs(d) < 1e-9, np.nan, d)
    miss = []
    for x in range(int(STRIP[0]) + 150, 8000, 300):
        for z in range(31260, 31610, 100):
            l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z - c[:, 1])) / d
            l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z - c[:, 1])) / d
            l3 = 1 - l1 - l2
            hit = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
            y = l1 * T[:, 0, 1] + l2 * T[:, 1, 1] + l3 * T[:, 2, 1]
            if not (hit & (y > -60) & (y < 20)).any():
                miss.append((x, z))
    return miss


def check(zp, live=None, log=print, view=False):
    """Offline proofs on a staged zip; -> list of problems ([] = all pass).
    1 render check of the van's drive (0 close samples), 2 bounded walk alley -> boarding box -> stop -> street ends is FREE with NOTHING opened,
    3 the flood from the alley stays inside the map's walls (does not touch the flood box) and the street part is closed at its north / ends,
    4 the nav mesh: alley, boarding box, stop, posts, ally box on ONE part and on polygons, the mesh way (collision-sampled) alley -> stop is free,
    5 the cut planter / blocker leave no placement."""
    import kl_vehroutes_1108 as V, kl_route as R
    bad = []
    n = V.check(zp, log, True)
    log('  1 render check of the drive: %s close samples' % n)
    if n:
        bad.append('van render check: %s close samples' % n)
    run = R._Run(zp, mesh=True)
    g = run.g
    orig = g.step

    def step(i, j, y, op):
        x, z = (i + 0.5) * R.CELL, (j + 0.5) * R.CELL
        if not (BOX_OPEN[0] <= x <= BOX_OPEN[1] and BOX_OPEN[2] <= z <= BOX_OPEN[3]):
            return None
        return orig(i, j, y, op)
    g.step = step
    legs = [((3000, -15, 30800), (4121, -15, 31907), 'alley (3000,30800) -> boarding box (4121,31907)'),
            ((5000, -15, 30800), (4121, -15, 31907), 'alley east (5000,30800) -> boarding box'),
            ((3000, -15, 30800), (4458, -15, 31907), 'alley -> van stop (4458,31907)'),
            ((3000, -15, 30800), (6500, -15, 31800), 'alley -> street east (6500,31800)'),
            ((3000, -15, 30800), (2000, -15, 31907), 'alley -> street west (2000,31907)'),
            ((3000, -15, 30800), (4118, -15, 32352), 'alley -> AllyEscapeBox (4118,32352)')]
    for a, b, name in legs:
        leg = run.leg(a, b, opened=frozenset(), cross=False)
        log('  2 walk %-48s free=%s length=%s' % (name, leg['free'], leg.get('length')))
        if not leg['free']:
            bad.append('walk not free: ' + name)
    g.step = orig
    cost, _r = flood(zp)
    xs = [(s[0] + .5) * R.CELL for s in cost]
    zs = [(s[1] + .5) * R.CELL for s in cost]
    box = FLOOD_BOX
    touch = min(xs) < box[0] + 60 or max(xs) > box[1] - 60 or max(zs) > box[3] - 60
    log('  3 flood from the alley: %d cells, x %d..%d, z up to %d (box %r) touches the box: %s' % (len(cost), min(xs), max(xs), max(zs), box, touch))
    if touch:
        bad.append('the flood reaches the box edge: the map is open')
    if live:
        c0, _r0 = flood(live)
        x0 = [(s[0] + .5) * R.CELL for s in c0]
        z0 = [(s[1] + .5) * R.CELL for s in c0]
        log('    live (before): %d cells, x %d..%d, z up to %d' % (len(c0), min(x0), max(x0), max(z0)))
    # nav
    mesh = run.mesh
    B = F.Built(zp)
    N = F.Nav(B.scene.nav, links=True)
    pts = {'alley (3000,30800)': (3000, 0, 30800), 'boarding box': (4118, -15, 31907), 'stop': (4458, -15, 31907), 'ally box': (4118, -15, 32352)}
    sc = B.sc
    for k, e in enumerate(B.ents, 1):
        if sc.names[k] == 'Pos#01' and '051_DefendBehaviour_out' in sc.path[k] and 'merc_bot_squad' in sc.path[k]:
            w = B.at(k)
            pts['post %d (%d,%d)' % (k, w[0], w[2])] = (w[0], w[1], w[2])
    base = None
    for nm, p in pts.items():
        hit = mesh.at(p[0], p[1], p[2])
        poly = hit[0] if hit is not None else None
        part = N.part[poly] if poly is not None else None
        if base is None:
            base = part
        if poly is None or part != base:
            bad.append('nav: %s is %s' % (nm, 'off the mesh' if poly is None else 'on part %s, not %s' % (part, base)))
    log('  4 nav: %d places, %s' % (len(pts), 'all on polygons of one part' if not [b for b in bad if b.startswith('nav:')] else '; '.join(b for b in bad if b.startswith('nav:'))))
    mw = R.mesh_way(zp, [(3000, 0, 30800), (4118, -15, 31907), (4458, -15, 31907)])
    for leg in mw:
        log('    mesh way %s -> %s: parts %s portal %s samples %s nofloor %s hit %s' % (leg['from'], leg['to'], leg['parts'], leg['portal'], leg['samples'], leg['nofloor'], leg['hit']))
        if leg.get('hit') or leg.get('nofloor'):
            bad.append('mesh way sampled against collision: hit %s nofloor %s' % (leg.get('hit'), leg.get('nofloor')))
    with zipfile.ZipFile(zp) as z:
        hv = kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))
    left = [r for r in (PLANTER_REF, BLOCKER_REF) if any(kl_hvk.ref(i) == r for s in hv.shapes for i in s.inst)]
    log('  5 placements left of the cut REFs: %s' % left)
    if left:
        bad.append('placements left: %s' % left)
    miss = strip_ground(zp)
    log('  7 render ground under the sunk planter strip: %d sample points without' % len(miss))
    if miss:
        bad.append('no render ground under the sunk planter strip at %s' % miss[:5])
    if view:
        vr = viewshed(zp, log)
        print_viewshed(vr, log)
        r = vr['route']
        for lab, row in (('start', r[0]), ('end', r[-1])):
            if row[5]:
                bad.append('the van %s (%d,%d) is seen by %d viewers on the walkable floor (soft occluders)' % (lab, row[1], row[2], row[5]))
    log('PROBLEMS: %d' % len(bad))
    for b in bad:
        log('  ' + b)
    return bad


def stage(live_dir, out, log=print):
    import kl_botsonline
    src = os.path.join(live_dir, 'F03_Main.zip')
    for nm, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, nm)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (nm, h))
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, 'F03_Main.zip')
    write(src, final, log)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F03_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F03_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = [(nm, LIVE_MD5[nm], md5(os.path.join(out, nm))) for nm in LIVE_MD5]
    t = open(os.path.join(HERE, 'kl_vehroutes_street2_install_tmpl.py'), encoding='utf-8').read()      # the kit script (pins, backups, --undo, --dry, running-game refusal); only FILES is filled in here
    nl = chr(10)
    i, j = t.index('FILES = ['), t.index(nl + ']' + nl) + 3
    t = t[:i] + 'FILES = [   # name, live md5 before, staged md5 after' + nl + nl.join('    (%r, %r, %r),' % f for f in files) + nl + ']' + nl + t[j:]
    # DISK: the install's real peak need = one backup per file (= the live sizes) + ONE .tmp (the largest staged file) + --min-free-mb headroom (default and bat: MIN_FREE_MB).
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    open(os.path.join(out, 'INSTALL DM01B vehroutes street2 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%%~dp0install.py" --min-free-mb %d' % MIN_FREE_MB + cr + nl + 'pause' + cr + nl)
    open(os.path.join(out, 'UNDO DM01B vehroutes street2 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py" --undo' + cr + nl + 'pause' + cr + nl)
    for f in files:
        log('  %-24s %s -> %s' % f)
    return files


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3:
        stage(a[1], a[2])
    elif a[:1] == ['check'] and len(a) in (2, 3):
        sys.exit(1 if check(a[1], a[2] if len(a) == 3 else None, view=True) else 0)
    else:
        print(__doc__)
        sys.exit(2)
