#!/usr/bin/env python3
"""
The escape vehicle of a Dead Men Fragile Alliance map under Dog Days: its route against the ground,
what stands in it, and the camera of a player aboard. A step on a FINISHED build folder. Offline;
nothing here installs anything or starts the game. Spec and evidence: re/map_escape.md.

Owner, 2026-10-10, after Late Night Opening (M02_FA_A): 'the late night van sometimes is a bit weird?
camera goes under the map when ur in it'.

    python kl_map_escape.py check <build folder>         the tables, nothing written
    python kl_map_escape.py fix <build folder> <out>     copy of the build with the repairs, the tables
                                                         before and after, <out>/escape.txt + escape.json
    python kl_map_escape.py all <folder of builds> <out root> [M01 M02 ...]    'fix' on each
    --level     (fix / all) also put down the route points that float more than HIGH over the ground

  THE KEY-FRAMED VAN in place of Dead Men's spline car (owner, 2026-10-10: 'the van is such a damn problem';
  re/map_escape.md 8 - 13; the long comment before van_plan() below is the spec):
    python kl_map_escape.py van <folder of finished builds> <out root> [M01 M02 M03]
                                   each map BUILT AGAIN with stock F07's first escape van on the road Dead Men's
                                   designers drew for their car: plan on <builds>/<map>, kl_maps.ready_one with the
                                   van kept and Dead Men's car left out -> <out>/_graft/<map>, kl_map_tune.build ->
                                   <out>/<map> (+ van.json, van.txt)
    python kl_map_escape.py van-plan <finished build>     only the plan: waiting place, stop, end, lane, camera
    python kl_map_escape.py van-check <folder>            the van of a built level from its files; exit 1 on a FAULT
                                                          ('check' runs it too when the level has ONE animated van).
                                                          Also the .HVK: its size against HVK_MAX and the largest
                                                          share one entity owns (the filler copies, D2 of
                                                          re/play_fixes_review.md)
    python kl_map_escape.py van-keys                      stock F07's key tables, decoded (the evidence)

WHAT IS WRONG (re/map_escape.md 1; read in both executables and measured on the four builds)
  THE CAMERA. A Dead Men map has  EscCameraSetup!CameraTrigger01 @OnlineEscCamTrigger -> EscCamera01
  @CCameraBox(mode eFMM_LookFromPosFA, field 9 -> EscCameraSetup!CamPos01).  The box EscCamera01 itself
  stands at the world origin (0, 0, 0); CamPos01 is the place the designers chose.
    Dead Men (kaneandlynch.exe 0x62da0d, mode 3 = LookFromPosFA): the eye is put at the place of FIELD 9
      (CamPos01) and looks at the player.
    Dog Days (kl2.exe 0x4471a1, mode 4 = LookFromPosFA): the eye is put at the place of the box's OWN node
      and looks at field 9. That is how all 60 stock uses (F01..F09) are built (SpawnCam 'Camera_000_A' -> its
      'CameraLookAt_000_A'; F02 'CameraOutside_01' -> the helicopter).
    Dog Days mode 3 = eFMM_LookFromPos (kl2.exe 0x447240): eye at field 9, looking at the player - Dead
      Men's meaning. Stock F01 / F04 / F05 / F07 / F09 use it for exactly this camera ('EscCamera01_0n' ->
      'CamPos01', same six floats, same 'message only' flag).
  So aboard, inside the camera trigger, Dog Days puts the eye at (0, 0, 0): on M02 that is the plane of
  the mall's atrium floor, on M03 104 under the street, on M06 100 under the water, on M01 outside the map.
  THE REPAIR: field 11 of those camera boxes becomes eFMM_LookFromPos. One enum in the .prp per camera.
  THE VEHICLE. No route point of the four maps is under the ground (lowest: 0.9 over it); the car is a
  Havok vehicle (hkVehicleInstance in both executables), not a key-framed one like Retomoto's van, so
  there is no baked height to be wrong. NO stock Dog Days level has a ZHavokCar, a
  VehicleMoveBehaviourRout or an OnlineVehicleOnSpline (census of all 21): the three car maps drive
  code the retail game never runs. Nothing in these four routes is repaired, because nothing measured
  is wrong with them; the route repair below is for a map where something is.
  THE ROUTE REPAIR ('heights'): a CAR's route point UNDER the ground is put REST over it (the height of
  the car's own origin where the level parks it). With --level a point more than HIGH over the ground is
  put down too - ASSUMPTION that this is harmless: right if the engine uses a point's height, without
  effect if it does not; OFF by default because Dead Men drove these floating points as they are.
  Helicopter routes are never changed.

THE CHECK (for every map, before and after)
  route      every point of the incoming and the escaping route: place, ground under it (the level's
             collision, .HVK static and key-framed triangles, a vertical ray), height over ground
  corridor   the route walked in 50-unit steps (straight between points: ASSUMPTION about the curve),
             five rays across the body: what stands 25..170 over the ground in it, steps of the ground
             over 25, convex bodies (rigid props, other vehicles, key-framed pieces) in the lane,
             LevelBound boxes it passes through
  camera     every escape camera: where Dog Days puts the eye, the ground under it, what is between the
             eye and the vehicle's stop
A check FAULT is: a point under the ground, a camera eye not over ground or within EYE_MIN of it.
"""
import collections, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_hvk, kl_maps, kl_scene
import kl_prpjoin as J
from kl_prp import units

SLOT = 'F01'
CELL = 400.0                    # triangle grid
REACH = 100.0                   # 'the ground under a point' = the highest floor not more than this above it
FLOOR = 0.7                     # a triangle is floor when its normal is within 45 degrees of up (as kl_escape.Walk)
STEP = 50.0                     # corridor sampling along the route
HALF = 100.0                    # half width of the body (the van's wheels stand at x -98 .. +96)
BODY = (25.0, 170.0)            # what counts as standing in the lane: this far over the ground
KERB = 25.0                     # a step of the ground between two samples that is worth a line
HIGH = 30.0                     # --level: a point farther than this over the ground is put down (ASSUMPTION)
REST = (3.0, 15.0)              # the car's origin over the ground where the level parks it, clamped to this
SHARE = 250.0                   # another car's route nearer than this to the escape route shares its road
EYE_MIN = 50.0                  # a camera eye nearer than this to the ground under it is a FAULT
FROM_FA, FROM_POS = 'eFMM_LookFromPosFA', 'eFMM_LookFromPos'
I3 = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


# ------------------------------------------------------------------ the level
class Level:
    """A finished build folder (or an archive): the .prp scene, the .gms entities with their world frames,
    the collision."""
    def __init__(self, src):
        self.zip = src if src.lower().endswith('.zip') else os.path.join(src, SLOT + '_Main.zip')
        self.sc, _snd, _loc = kl_fa.load(self.zip)
        with zipfile.ZipFile(self.zip) as z:
            self.ext = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
            self.scene = kl_scene.Scene(kl_gms.unpack(z.read(self.ext['.gms'])), z.read(self.ext['.buf']))
            self.hvk = kl_hvk.Hvk(z.read(self.ext['.hvk']))
            self.sizes = {e: z.getinfo(n).file_size for e, n in self.ext.items()}
        self.ents = list(self.scene.entities())
        if len(self.ents) + 1 != len(self.sc.nodes):
            raise ValueError('%d entities, %d nodes' % (len(self.ents), len(self.sc.nodes)))
        self.byref = {e.ref: e for e in self.ents}

    def frame(self, k):
        """(R, T) of node k: world = T + R . local. Composed down the tree as kl_maps.world() reads a
        record (the nine floats as rows, reversed, then transposed)."""
        chain, j = [], k
        while j > 0:
            chain.append(self.ents[j - 1]); j = self.sc.parent[j]
        R, T = I3, (0.0, 0.0, 0.0)
        for e in reversed(chain):
            r, t = struct.unpack('<9f', e.rot[:36]), struct.unpack('<3f', e.trans[:12])
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[b][a] for b in range(3)] for a in range(3)]
            T = tuple(T[i] + sum(R[i][b] * t[b] for b in range(3)) for i in range(3))
            R = [[sum(R[i][c] * m[c][b] for c in range(3)) for b in range(3)] for i in range(3)]
        return R, T

    def place(self, k):
        return self.frame(k)[1]

    def name(self, ref):
        e = self.byref.get(ref)
        return e.name.decode('latin1') if e else 'REF %d' % ref

    def values(self, k):
        return dict(zip(J.labels('dd', self.sc.cls(k)), kl_fa.node_values(self.sc, k)))

    def ctrl(self, k, name):
        """[(index, [values])] of the controllers `name` on node k."""
        return [(i, [kl_fa.value(self.sc, u) for u in units(body[1:-1])])
                for i, (nm, body) in enumerate(self.sc.nodes[k]['ctrls']) if self.sc.p.key(nm) == name]


# ------------------------------------------------------------------ the ground
class Ground:
    """The MAP's collision as triangles: every non-convex static (type 1) and key-framed (type 4) shape
    of the .HVK whose entity stands below a 'Locations/' subtree, in world units (the file is in metres).
    Left out: the non-convex shapes of the systems (ten projectile templates lie at the world origin) and
    of the loot. Convex shapes - rigid props (2), vehicles (3), key-framed pieces (4) - are kept as boxes:
    they are what a physics car pushes or hits. Measured on M01 / M02: placements of types 1, 2, 4 and 5 are
    world places (equal to the entity's own within 2), a vehicle's (3) is relative to its entity."""
    def __init__(self, L):
        self.tris, self.grid, self.big, self.boxes = [], collections.defaultdict(list), [], []
        node = {e.ref: i + 1 for i, e in enumerate(L.ents)}
        def top(r):
            k = node.get(r)
            return L.sc.names[L.sc.top[k]] if k else ''
        for s in L.hvk.shapes:
            vs = [struct.unpack_from('<3f', s.verts, i * s.vstride) for i in range(len(s.verts) // s.vstride)]
            if s.convex or s.type not in (kl_hvk.STATIC, kl_hvk.KEYFRAMED):
                for inst in s.inst:
                    r, w = kl_hvk.ref(inst), self._world(inst, vs)
                    if not w or s.type not in (kl_hvk.RIGID, kl_hvk.VEHICLE, kl_hvk.KEYFRAMED) or r not in node:
                        continue
                    o = L.place(node[r]) if s.type == kl_hvk.VEHICLE else (0.0, 0.0, 0.0)
                    self.boxes.append((s.type, r, tuple(o[a] + min(v[a] for v in w) for a in range(3)),
                                       tuple(o[a] + max(v[a] for v in w) for a in range(3))))
                continue
            idx = struct.unpack('<%dH' % (len(s.idx) // 2), s.idx)
            for inst in s.inst:
                r, w = kl_hvk.ref(inst), self._world(inst, vs)
                if not top(r).startswith('Locations/'):
                    continue
                for t in range(0, len(idx) - 2, 3):
                    a, b, c = w[idx[t]], w[idx[t + 1]], w[idx[t + 2]]
                    e1, e2 = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                    n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
                    ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
                    if ln < 1e-6:
                        continue
                    k = len(self.tris)
                    self.tris.append((a, b, c, r, abs(n[1]) / ln))
                    x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
                    z0, z1 = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
                    if (x1 - x0) * (z1 - z0) > CELL * CELL * 400:
                        self.big.append(k)
                        continue
                    for i in range(int(x0 // CELL), int(x1 // CELL) + 1):
                        for j in range(int(z0 // CELL), int(z1 // CELL) + 1):
                            self.grid[i, j].append(k)

    @staticmethod
    def _world(inst, vs):
        p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)   # as kl_escape.Walk
        return [tuple(100 * (p[a] + m[3 * a] * v[0] + m[3 * a + 1] * v[1] + m[3 * a + 2] * v[2]) for a in range(3)) for v in vs]

    def hits(self, x, z):
        """[(y, upness, REF)] of a vertical line, low to high."""
        out = []
        for k in self.grid.get((int(x // CELL), int(z // CELL)), []) + self.big:
            a, b, c, r, up = self.tris[k]
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-9:
                continue
            u = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            v = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            out.append((u * a[1] + v * b[1] + (1 - u - v) * c[1], up, r))
        return sorted(out)

    def under(self, x, y, z):
        """(floor y, REF) of the highest floor not more than REACH above y; None when the line meets no
        floor there. With none below, the lowest floor above is returned: the point is UNDER the ground."""
        fl = [h for h in self.hits(x, z) if h[1] > FLOOR]
        low = [h for h in fl if h[0] <= y + REACH]
        h = low[-1] if low else fl[0] if fl else None
        return (h[0], h[2]) if h else None

    def between(self, p, q):
        """REF ids of the triangles the segment p -> q passes through, nearest first: [(distance, REF)]."""
        ln = math.dist(p, q)
        if ln < 1e-6:
            return []
        d = [(q[i] - p[i]) / ln for i in range(3)]
        ks, n = set(self.big), int(ln / (CELL / 2)) + 1
        for i in range(n + 1):
            x, z = p[0] + d[0] * ln * i / n, p[2] + d[2] * ln * i / n
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    ks.update(self.grid.get((int(x // CELL) + di, int(z // CELL) + dj), ()))
        out = []
        for k in ks:
            a, b, c, r, _up = self.tris[k]
            e1, e2 = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
            det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
            if abs(det) < 1e-9:
                continue
            s = [p[i] - a[i] for i in range(3)]
            u = (s[0] * h[0] + s[1] * h[1] + s[2] * h[2]) / det
            if u < 0 or u > 1:
                continue
            qv = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
            v = (d[0] * qv[0] + d[1] * qv[1] + d[2] * qv[2]) / det
            if v < 0 or u + v > 1:
                continue
            t = (e2[0] * qv[0] + e2[1] * qv[1] + e2[2] * qv[2]) / det
            if 1.0 < t < ln - 1.0:
                out.append((t, r))
        return sorted(out)


# ------------------------------------------------------------------ routes
def spline(L, k):
    """World points of the ZEditorSpline node k -> ([(x, y, z)], raw bytes, (R, T)). The raw field: 12
    bytes (a tag, the point count, 1), then 24 bytes a point: x, y, z in the node's frame, an angle, 10.0
    and four bytes the editor never set (0xcdcdcdcd); what follows the points is editor memory."""
    raw = L.values(k)['ZEditorSpline[0]']
    n = struct.unpack_from('<I', raw, 4)[0]
    if 12 + 24 * n > len(raw):
        raise ValueError('%s: %d points do not fit %d bytes' % (L.sc.path[k], n, len(raw)))
    R, T = L.frame(k)
    pts = []
    for i in range(n):
        p = struct.unpack_from('<3f', raw, 12 + 24 * i)
        pts.append(tuple(T[a] + sum(R[a][b] * p[b] for b in range(3)) for a in range(3)))
    return pts, raw, (R, T)


def vehicles(L):
    """[{'node', 'name', 'kind' ('car' | 'helicopter'), 'at', 'routes': {'incoming' | 'escaping': spline node}}]
    of every OnlineEscHavokCar whose routes are splines (Dead Men's form; a stock helicopter's are trigger lists)."""
    sc, out = L.sc, []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineEscHavokCar'):
        cls = {sc.cls(j) for j in range(k, sc.end[k])}
        kind = 'helicopter' if 'ZHeli' in cls else 'car' if 'ZHavokCar' in cls else None
        routes = {}
        for which, s in zip(('incoming', 'escaping'), v[:2]):
            for h in (sc.resolve(s) if isinstance(s, str) and s else []):
                sp = next((j for j in range(h, sc.end[h]) if sc.cls(j) == 'ZEditorSpline'), None)
                if sp is not None:
                    routes[which] = sp
        if kind and routes:
            out.append({'node': k, 'name': sc.path[k][5:], 'kind': kind, 'at': L.place(k), 'routes': routes})
    return out


def rest_height(L, G, v):
    """How far the vehicle's own origin stands over the ground where the level parks it, clamped to REST."""
    g = G.under(*v['at'])
    return min(max(v['at'][1] - g[0], REST[0]), REST[1]) if g else sum(REST) / 2


def route_rows(L, G, pts):
    """One row a point: (index, (x, y, z), ground y or None, height over ground or None, name of the ground)."""
    rows = []
    for i, p in enumerate(pts):
        g = G.under(p[0], p[1], p[2])
        rows.append((i, p, g[0] if g else None, p[1] - g[0] if g else None, L.name(g[1]) if g else ''))
    return rows


def corridor(L, G, pts, kind, bounds, own=()):
    """The route walked in STEP units, straight between its points (ASSUMPTION: the engine's curve through the
    points is not known; a straight walk shows what stands between them). -> dict:
      length, samples, low = (lowest height over ground, where),
      in_lane = {name: [first distance, last distance, lowest y over ground]}   static collision BODY over the
               ground on one of five rays across HALF (cars), or within 150 under a helicopter's point,
      kerbs = [(distance, step of the ground)], bodies = {name: (type, distance)}, bounds = {box: [from, to]}
    own: REF ids of the vehicle's own parts (its wheels and doors are convex bodies too)."""
    out = {'length': 0.0, 'samples': 0, 'low': None, 'in_lane': {}, 'kerbs': [], 'bodies': {}, 'bounds': {}}
    dist, last = 0.0, None
    for a, b in zip(pts, pts[1:]):
        ln = math.dist(a, b)
        hx, hz = b[0] - a[0], b[2] - a[2]
        hl = math.hypot(hx, hz) or 1.0
        px, pz = hz / hl, -hx / hl                          # across the heading
        n = max(1, int(ln / STEP))
        for i in range(n + (1 if b is pts[-1] else 0)):
            t = i / n
            p = tuple(a[j] + (b[j] - a[j]) * t for j in range(3))
            d = dist + ln * t
            out['samples'] += 1
            g = G.under(*p)
            if g:
                h = p[1] - g[0]
                if out['low'] is None or h < out['low'][0]:
                    out['low'] = (h, tuple(round(x) for x in p))
                if kind == 'car':
                    if last is not None and abs(g[0] - last) > KERB:
                        out['kerbs'].append((round(d), round(g[0] - last, 1)))
                    last = g[0]
                    for off in (-HALF, -HALF / 2, 0.0, HALF / 2, HALF):
                        x, z = p[0] + px * off, p[2] + pz * off
                        for y, _up, r in G.hits(x, z):
                            if g[0] + BODY[0] < y < g[0] + BODY[1]:
                                e = out['in_lane'].setdefault(L.name(r), [round(d), round(d), round(y - g[0])])
                                e[1], e[2] = round(d), min(e[2], round(y - g[0]))
                else:
                    for y, _up, r in G.hits(p[0], p[2]):
                        if p[1] - 150 < y < p[1] + 400:
                            e = out['in_lane'].setdefault(L.name(r), [round(d), round(d), round(y - p[1])])
                            e[1] = round(d)
            if kind == 'car' and g:
                for ty, r, lo, hi in G.boxes:
                    if r not in own and lo[0] - HALF < p[0] < hi[0] + HALF and lo[2] - HALF < p[2] < hi[2] + HALF and \
                            lo[1] < g[0] + BODY[1] and hi[1] > g[0] + 10:
                        out['bodies'].setdefault(L.name(r), (ty, round(d)))
            for nm, inside in bounds:
                if inside(p):
                    e = out['bounds'].setdefault(nm, [round(d), round(d)])
                    e[1] = round(d)
        dist += ln
    out['length'] = dist
    return out


def level_bounds(L):
    """[(name, inside(p))] of the boxes that carry a LevelBound (the box that ends it, not its two warnings)."""
    out = []
    for k, _i, _v in kl_fa.controllers(L.sc, 'LevelBound'):
        if L.sc.cls(k) != 'ZBoxPrimitive':
            continue
        v, (R, T) = L.values(k), L.frame(k)
        half = [v['ZBoxPrimitive[%d]' % i] for i in range(3)]
        def inside(p, R=R, T=T, half=half):
            return all(abs(sum(R[a][b] * (p[a] - T[a]) for a in range(3))) <= half[b] for b in range(3))
        out.append((L.sc.path[k][5:], inside))
    return out


def _apart(p, pts):
    """Horizontal distance of point p from the polyline pts."""
    best = 1e12
    for a, b in zip(pts, pts[1:]):
        dx, dz = b[0] - a[0], b[2] - a[2]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / ((dx * dx + dz * dz) or 1.0)))
        best = min(best, math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz))
    return best


def other_cars(L, v, routes):
    """The level's other physics cars (ZHavokCar outside the escape vehicle's group) against the escape
    routes {which: points}: -> [(car path, which route, what)] for a car PARKED within SHARE of a route and for
    a car whose own spline route (a sibling group with VehicleMoveBehaviourRout) runs within SHARE of one.
    Dead Men's design, the same in its own game - listed because two Havok cars on one road is where a
    physics car can be 'weird', and Dog Days ships no level with even one."""
    sc, out = L.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZHavokCar' or v['node'] <= k < sc.end[v['node']]:
            continue
        at, top = L.place(k), sc.top[k]
        for which, pts in routes.items():
            if _apart(at, pts) < SHARE:
                out.append((sc.path[k][5:], which, 'is parked %d from it, at (%d, %d, %d)' % (_apart(at, pts), *at)))
        for j in range(top, sc.end[top]):
            if sc.cls(j) == 'ZEditorSpline' and L.ctrl(sc.parent[j], 'VehicleMoveBehaviourRout'):
                own = spline(L, j)[0]
                for which, pts in routes.items():
                    dist, near = 0.0, []
                    for a, b in zip(pts, pts[1:]):
                        ln = math.dist(a, b)
                        n = max(1, int(ln / STEP))
                        for i in range(n):
                            q = tuple(a[c] + (b[c] - a[c]) * i / n for c in range(3))
                            if _apart(q, own) < SHARE:
                                near.append(dist + ln * i / n)
                        dist += ln
                    if near:
                        out.append((sc.path[k][5:], which, 'drives the same road: its route %s is within %d of this one from %d to %d along it '
                                    '(it ends at (%d, %d, %d))' % (sc.path[sc.parent[j]][5:], SHARE, min(near), max(near), *own[-1])))
    return out


# ------------------------------------------------------------------ cameras
def cameras(L, G, stops):
    """The escape cameras: every CCameraBox an OnlineEscCamTrigger names (Dog Days field 1). -> [dict]:
    node, name, trigger, mode, own = the box's place, target = the place of field 9, eye = where Dog Days
    puts the eye for that mode (kl2.exe 0x446c40: LookFromPosFA = the box's own node, LookFromPos = field 9),
    ground / over = the floor under the eye, sight = what the collision puts between the eye and the nearest
    vehicle stop, fault = why the eye is wrong or ''."""
    sc, out = L.sc, []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineEscCamTrigger'):
        for s in [x for x in v if isinstance(x, str) and x]:
            for c in sc.resolve(s):
                for ci, cv in L.ctrl(c, 'CCameraBox'):
                    own = L.place(c)
                    tgt = [L.place(j) for j in sc.resolve(cv[9])] if isinstance(cv[9], str) and cv[9] else []
                    mode = cv[11]
                    eye = own if mode == FROM_FA else tgt[0] if tgt and mode == FROM_POS else None
                    d = {'node': c, 'ctrl': ci, 'name': sc.path[c][5:], 'trigger': sc.path[k][5:], 'mode': mode,
                         'own': own, 'target': tgt[0] if tgt else None, 'target_name': cv[9] if tgt else '',
                         'message_only': bool(cv[12]), 'eye': eye, 'fault': ''}
                    if eye:
                        fl = [h for h in G.hits(eye[0], eye[2]) if h[1] > FLOOR]
                        below = [h for h in fl if h[0] <= eye[1] + 1.0]
                        d['ground'] = below[-1][0] if below else None
                        d['over'] = eye[1] - below[-1][0] if below else None
                        d['ground_name'] = L.name(below[-1][2]) if below else ''
                        above = [h for h in fl if h[0] > eye[1] + 1.0]
                        if not fl:
                            d['fault'] = 'the eye is outside the map: no collision above or below it'
                        elif not below:
                            d['fault'] = 'the eye is UNDER the map: the lowest floor there is %.0f above it (%s)' % (
                                above[0][0] - eye[1], L.name(above[0][2]))
                        elif d['over'] < EYE_MIN:
                            d['fault'] = 'the eye is %.0f over the floor %s: in the floor\'s plane' % (d['over'], d['ground_name'])
                        if stops:
                            st = min(stops, key=lambda q: math.dist(q, eye))
                            aim = (st[0], st[1] + 100.0, st[2])
                            hit = G.between(eye, aim)
                            d['stop'], d['far'] = st, math.dist(eye, aim)
                            d['sight'] = [(round(t), L.name(r)) for t, r in hit[:3]]
                    out.append(d)
    return out


# ------------------------------------------------------------------ the check
def check(L, log=print, title='check'):
    """Tables of one level -> {'vehicles': [...], 'cameras': [...], 'faults': [...]} (JSON form)."""
    G = L.G if hasattr(L, 'G') else Ground(L)
    L.G = G
    bounds = level_bounds(L)
    rep = {'vehicles': [], 'cameras': [], 'cameras_no_eye': [], 'faults': []}
    stops = []
    log('%s: %s' % (title, L.zip))
    for v in vehicles(L):
        rest = rest_height(L, G, v)
        log('  %s %s, parked at (%d, %d, %d)%s' % (v['kind'], v['name'], *v['at'],
                                                  ', its origin %.1f over the ground' % rest if v['kind'] == 'car' else ''))
        rv = {'name': v['name'], 'kind': v['kind'], 'rest': round(rest, 1), 'routes': {}}
        if v['kind'] == 'car':
            rv['other_cars'] = other_cars(L, v, {w: spline(L, sp)[0] for w, sp in v['routes'].items()})
        for which, sp in v['routes'].items():
            pts, _raw, _f = spline(L, sp)
            if which == 'incoming':
                stops.append(pts[-1])
            rows = route_rows(L, G, pts)
            own = {L.ents[j - 1].ref for j in range(v['node'], L.sc.end[v['node']])}
            cor = corridor(L, G, pts, v['kind'], bounds, own)
            log('    %s route, %d points, %.0f m:' % (which, len(pts), cor['length'] / 100))
            for i, p, g, h, nm in rows:
                log('      %2d (%7.0f %7.1f %7.0f)  ground %s  over it %s  %s' % (
                    i, *p, '%7.1f' % g if g is not None else '   none', '%7.1f' % h if h is not None else '      -', nm[:44]))
                if h is not None and h < 0:
                    rep['faults'].append('%s %s route point %d is %.1f UNDER the ground (%s)' % (v['name'], which, i, -h, nm))
            hs = [h for _i, _p, _g, h, _n in rows if h is not None]
            log('      over ground: %.1f .. %.1f at the points; lowest on the straight walk %s' % (
                min(hs), max(hs), '%.1f at %s' % cor['low'] if cor['low'] else '-'))
            if v['kind'] == 'car' and cor['low'] and cor['low'][0] < 0:
                log('      NOTE the straight walk between two points dips %.1f under the ground at %s (it matters only '
                    'if the engine moves the car along the points\' heights)' % (-cor['low'][0], cor['low'][1]))
            for nm, (d0, d1, y) in sorted(cor['in_lane'].items(), key=lambda x: x[1]):
                log('      in the %s: %-44s %5d .. %5d along it, %s' % (
                    'lane' if v['kind'] == 'car' else 'way', nm[:44], d0, d1,
                    'from %d over the ground' % y if v['kind'] == 'car' else '%d against the point' % y))
            for d, s in cor['kerbs'][:12]:
                log('      ground step %+.1f at %d along it' % (s, d))
            for nm, (ty, d) in sorted(cor['bodies'].items(), key=lambda x: x[1][1]):
                log('      body in the lane: %-40s %s, at %d along it' % (nm[:40], {2: 'rigid', 3: 'vehicle', 4: 'key-framed', 5: 'weapon'}.get(ty, ty), d))
            for nm, (d0, d1) in cor['bounds'].items():
                log('      passes through the level bound %s from %d to %d along it' % (nm, d0, d1))
            rv['routes'][which] = {
                'points': [[i, [round(x, 1) for x in p], None if g is None else round(g, 1), None if h is None else round(h, 1), nm]
                           for i, p, g, h, nm in rows],
                'length': round(cor['length']), 'low': cor['low'], 'in_lane': cor['in_lane'], 'kerbs': cor['kerbs'],
                'bodies': cor['bodies'], 'bounds': cor['bounds']}
        for car, which, what in rv.get('other_cars', []):
            log('    %s route: %s %s' % (which, car, what))
        rep['vehicles'].append(rv)
    for c in cameras(L, G, stops):
        log('  camera %s <- %s' % (c['name'], c['trigger']))
        log('    mode %s, the box at (%d, %d, %d), field 9 %s at %s' % (
            c['mode'], *c['own'], c['target_name'][5:] or '-', '(%d, %d, %d)' % c['target'] if c['target'] else '-'))
        if c['eye']:
            log('    Dog Days\' eye: (%d, %d, %d), %s; %s' % (
                *c['eye'], '%.0f over %s' % (c['over'], c['ground_name']) if c.get('over') is not None else 'no floor under it',
                'looks at the player' if c['mode'] == FROM_POS else 'looks at field 9, not at the player'))
            if 'sight' in c:
                log('    to the vehicle\'s stop (%d, %d, %d), %.0f m: %s' % (
                    *c['stop'], c['far'] / 100, 'clear' if not c['sight'] else 'through ' + ', '.join('%s at %d' % (n, t) for t, n in c['sight'])))
        if c['fault']:
            log('    FAULT ' + c['fault'])
            rep['faults'].append('camera %s: %s' % (c['name'], c['fault']))
        # a camera without a place of its own for the eye (eFMM_LookAtPos: the eye rides with the player - the key-framed
        # van's inside camera) is listed apart: kl_map_tune prints every camera of 'cameras' by its eye
        rep['cameras' if c['eye'] else 'cameras_no_eye'].append({k: c.get(k) for k in (
            'name', 'trigger', 'mode', 'own', 'target', 'target_name', 'eye', 'ground', 'over', 'ground_name', 'sight', 'fault')})
    log('  %d fault(s)' % len(rep['faults']))
    return rep


# ------------------------------------------------------------------ the repairs
def fix_cameras(L, log=print):
    """Escape cameras in Dead Men's form -> Dog Days' mode with the same meaning (the docstring's first
    part). A camera is taken when an OnlineEscCamTrigger names it, its mode is eFMM_LookFromPosFA, its own
    node stands within 1 of the world origin and field 9 names a node that does not: then the designers'
    camera place is field 9, and in Dog Days only eFMM_LookFromPos puts the eye there. -> names."""
    sc, done = L.sc, []
    for c in cameras(L, L.G, []):
        if c['mode'] != FROM_FA or not c['target'] or max(abs(x) for x in c['own']) > 1.0 or max(abs(x) for x in c['target']) <= 1.0:
            continue
        def fn(us):
            if us[11][0][0] != 0x0e:
                raise ValueError('%s: CCameraBox field 11 is not an enum' % c['name'])
            us[11] = [(0x0e, struct.pack('<I', sc.p.key_index(FROM_POS)))]
        kl_fa.edit(sc, c['node'], c['ctrl'], fn)
        done.append(c['name'])
        log('  kl_map_escape: camera %s: %s -> %s (the eye goes from the box at (%d, %d, %d) to %s at (%d, %d, %d))' % (
            c['name'], FROM_FA, FROM_POS, *c['own'], c['target_name'][5:], *c['target']))
    return done


def fix_heights(L, level=False, log=print):
    """On a CAR's routes a point under the ground - and with `level` (ASSUMPTION, module docstring) one more
    than HIGH over it - is put REST over the ground; a point with no ground under it is left. The point's y
    in the spline's raw field is rewritten in place (same length, nothing else touched).
    -> [(route, point, old y, new y)]."""
    sc, done = L.sc, []
    for v in vehicles(L):
        if v['kind'] != 'car':
            continue
        rest = rest_height(L, L.G, v)
        for which, sp in v['routes'].items():
            pts, raw, (R, T) = spline(L, sp)
            new = bytearray(raw)
            for i, p in enumerate(pts):
                g = L.G.under(*p)
                if not g or 0.0 <= p[1] - g[0] <= (HIGH if level else 1e9):
                    continue
                w = (p[0], g[0] + rest, p[2])
                loc = [sum(R[a][b] * (w[a] - T[a]) for a in range(3)) for b in range(3)]    # R is a rotation: its inverse is its transpose
                old = struct.unpack_from('<3f', raw, 12 + 24 * i)
                if abs(loc[0] - old[0]) > 0.05 or abs(loc[2] - old[2]) > 0.05:
                    raise ValueError('%s point %d: the spline node is tilted, a height is not one number' % (sc.path[sp], i))
                struct.pack_into('<f', new, 12 + 24 * i + 4, loc[1])
                done.append((which, i, round(p[1], 1), round(w[1], 1)))
            if bytes(new) != raw:
                lab = J.labels('dd', 'ZEditorSpline')
                def fn(us, new=bytes(new)):
                    u = us[lab.index('ZEditorSpline[0]')]
                    if u[1][0] != 0x0d or u[1][1][4:] != raw:
                        raise ValueError('%s: the raw field is not where it was read' % sc.path[sp])
                    u[1] = (0x0d, u[1][1][:4] + new)
                kl_fa.edit(sc, sp, None, fn)
    for which, i, a, b in done:
        log('  kl_map_escape: %s route point %d: y %.1f -> %.1f' % (which, i, a, b))
    return done


def repair(src, dst, level=False, log=print):
    """Build folder `src` -> folder `dst` with the repairs. Only the .prp member changes; every other member
    keeps its bytes, name, order, time stamp and packing method, and the files beside the archive are copied.
    -> report (also <dst>/escape.json; the lines in <dst>/escape.txt). audit.* of the source is not copied:
    run `python kl_maps.py audit <dst>` on the result."""
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('kl_map_escape: the output folder is the build\'s own')
    if 'kl_portbackup' in os.path.abspath(dst).lower() or 'dog days' in os.path.abspath(dst).lower():
        raise ValueError('kl_map_escape writes build folders only, never the game\'s')
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    L = Level(src)
    before = check(L, say, 'BEFORE')
    cams = fix_cameras(L, say)
    moved = fix_heights(L, level, say)
    prp = L.sc.p.serialize()
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, os.path.basename(L.zip))
    changed = []
    with zipfile.ZipFile(L.zip) as zi, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zo:
        for info in zi.infolist():
            data = zi.read(info.filename)
            if info.filename == L.ext['.prp'] and prp != data:
                data = prp
                changed.append(info.filename)
            ni = zipfile.ZipInfo(info.filename, info.date_time)
            ni.external_attr = info.external_attr
            zo.writestr(ni, data, info.compress_type, 1)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and os.path.abspath(p) != os.path.abspath(L.zip) and not f.startswith(('audit.', 'escape.')):
            shutil.copyfile(p, os.path.join(dst, f))
    L2 = Level(dst)
    after = check(L2, say, 'AFTER')
    with zipfile.ZipFile(L.zip) as a, zipfile.ZipFile(out) as b:
        differ = [x.filename for x, y in zip(a.infolist(), b.infolist()) if x.CRC != y.CRC or x.file_size != y.file_size]
        same_names = a.namelist() == b.namelist()
    side = {f: os.path.getsize(os.path.join(dst, f)) for f in os.listdir(dst) if f.upper().endswith('.WAV') and f.startswith(SLOT + '_Main.')}
    budget = {'before': {e: L.sizes[e] for e in ('.prm', '.anm', '.fxc') if e in L.sizes},
              'after': {e: L2.sizes[e] for e in ('.prm', '.anm', '.fxc') if e in L2.sizes}, 'WAV beside': side}
    say('members that differ from the build: %s (names and order %s)' % (', '.join(differ) or 'none', 'equal' if same_names else 'DIFFER'))
    say('budget, bytes before -> after: ' + ', '.join('%s %d -> %d' % (e, budget['before'][e], budget['after'][e]) for e in budget['before'])
        + '; ' + ', '.join('%s %d (copied)' % kv for kv in side.items()))
    rep = {'src': src, 'dst': dst, 'cameras_changed': cams, 'points_moved': moved, 'members_changed': differ,
           'before': before, 'after': after, 'budget': budget}
    if differ != changed or not same_names:
        raise ValueError('kl_map_escape: members %s changed, meant %s' % (differ, changed))
    # kl_maps.audit holds a finished folder to the member list its steps.json recorded ('final'). This step is one
    # more step after it: recorded as 'escape', and 'final' moved on - only when the source folder WAS the measured
    # one and the members that differ are the ones meant (tested just above).
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        st = json.load(open(sj))
        if st.get('final') == json.loads(json.dumps(kl_maps.member_ids(src, SLOT))):
            st['escape'] = [n.rsplit('_Main', 1)[1] for n in differ]
            st['final'] = kl_maps.member_ids(dst, SLOT)
            with open(sj, 'w') as f:
                json.dump(st, f, indent=1)
            say('steps.json: this step recorded (escape: %s), "final" is the new member list' % (' '.join(st['escape']) or 'nothing'))
        else:
            say('steps.json: NOT touched - the source folder is not the one its steps.json measured; kl_maps.audit will say so')
    with open(os.path.join(dst, 'escape.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    with open(os.path.join(dst, 'escape.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1, default=str)
    say('RESULT %s: %d camera(s) changed, %d route point(s) moved, faults %d -> %d' % (
        os.path.basename(os.path.normpath(dst)), len(cams), len(moved), len(before['faults']), len(after['faults'])))
    return rep


# ====================================================================================================
# THE KEY-FRAMED VAN IN PLACE OF DEAD MEN'S SPLINE CAR (2026-10-10, re/map_escape.md sections 8 - 13)
# ====================================================================================================
# Owner, after rounds on the four maps: 'the van is such a damn problem'; on Retomoto, where the escape is stock
# F07's key-framed van on a rewritten drive (kl_fa_van), 'almost perfect'. So the three car maps get THAT van:
#   plan      on a finished build that still has Dead Men's car: its two routes (the road the designers drew) joined
#             into one smooth curve, the stop, the waiting place, the end, the lane checked every LANE_STEP units
#   graft     kl_maps.ready_one with four things patched in from outside for the length of the build (as
#             kl_escape.applied does): F07's first escape van is KEPT (kl_fa.host_keep), its baked keys and the
#             things that stand beside its drive are rewritten on the stock Level before the graft, Dead Men's car,
#             its boarding action and its escape cameras are LEFT OUT (Select m_drop), the level's exit triggers
#             name the van (after kl_fa.repair), the van's collision placements are put right (after kl_hvk.join)
#   tune      kl_map_tune.build on the result, as every delivered map has had
# WHAT A VAN'S KEYS ARE (read on stock F07, `van-keys`): the KEYS chunk of V_Van_00 has six tables in the .buf head.
#   5 = positions (3 floats a key), 2 = rotations (4 x int16 / 32767 = a quaternion x y z w; the yaw of local +Z
#   computed from it follows the tangent of the positions within 8 degrees on the whole drive), 3 and 0 = for every
#   FRAME the index of its position / rotation key, bit-packed (first byte = bits a value, then the values, most
#   significant bit first), 4 and 1 = for every key its frame, packed the same way. 796 frames at 25 a second:
#   0..49 waiting, 50..230 the drive in (7.2 s), 230..273 standing, 273..485 the drive away (8.48 s), then the four
#   crash pieces (500.., 600.., 650.., 750..). So a key's place AND heading can be anything: the drive is NOT limited
#   to straight legs. What stays fixed without rewriting tables 0 / 1 / 3 / 4 (not done) is the timing: which
#   fraction of each leg the van has covered at each frame (its baked ease in and out).
VAN_HOST = 'F07'
VAN_TOP = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = VAN_TOP + '\\EscapeVehicle_Animation_F07'
VAN_KEEP = (VAN_TOP, 'Gameplay!EscapeSetup!RelayDestroyedEsc_01')   # the relay the kept monitor's list 3 names for this van
VAN_TAGS = ('M01', 'M02', 'M03')
VAN_UP = 2.0                    # the van's origin over the road: F07's keys are at y -198 on its road at -200
VAN_HALF = 110.0                # half width of the lane that is tested (kl_fa_van tests the same five rays)
VAN_BODY = (25.0, 220.0)        # collision this far over the road is in the van's way
VAN_NOSE = 600.0                # ... and the lane is tested this far beyond the last key (kl_fa_van: 6 m)
VAN_TAIL = 350.0                # ... and behind the first
LANE_STEP = 20.0
LIMIT_IN = 6000.0               # GUESS: the drive in is at most 60 m (7.2 s: 30 km/h on average; F07's own is 51 m)
LIMIT_OUT = 8000.0              # GUESS: the drive away at most 80 m (8.48 s; F07's own is 70 m with a top speed of 13 m/s, Retomoto's
                                # 102 m on a straight road; these roads bend - M02's at 50 m - and at 100 m the van took that at 19 m/s)
MIN_IN, MIN_OUT = 2000.0, 3000.0
GAP = 900.0                     # the drive ends this far before a thing in the lane (a wall, a gate that is not of
                                # the form gate_find() handles)
BOARD_BACK = 337.0              # the van's BoardingTrigger: 337 behind its origin (read on F07; tested in van_prepare)
SIDE = 120.0                    # a crash piece may leave the drive this far to either side (the lane's half width + 10)
AXLES = 140.0                   # the van's heading = the chord of the drive from its rear axle to its front one (wheels at -138 / +137)
REL_MAX = 6.0                   # van_check: degrees the nose may differ from that chord on the drive (stock F07: up to 9, its own
                                # baked lead and lag in ITS bends - not carried over: on another bend it is a slide)
PARK = (0.0, -60000.0, 0.0)     # where F07 pieces without a use go (kl_fa_author.PARK)
HVK_STOCK = 3165936             # the largest stock .HVK (L10)
HVK_MAX = 5002128               # van_check: the largest .HVK that has loaded and played in the game (Retomoto, v_rtbots)
HVK_SHARE = 1000000             # van_check: bytes of shape records one entity may own. Measured on the builds of 2026-10-10
                                # night: the packed filler 183 KB (1,757 placements); the largest single map object 29 KB;
                                # M02's PC0401_M02_FA_Wall_Bottom_01 878 KB in 330 placements = the padding kl_hvk.join puts
                                # between the map's static part and F07's (copies of the map's FIRST static placement, each
                                # with that wall's 2.6 KB MOPP code; not cut here: kl_hvk is not this module's).
                                # M02's unpacked filler of the afternoon owned 15.4 MB.
ST = {}                         # the state of one van build in this process (van_build)


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _heading(t):
    return math.degrees(math.atan2(t[0], t[1]))


class Poly:
    """A polyline of (x, y, z) with its length in the ground plane; at / tan extrapolate past the ends."""
    def __init__(self, pts):
        self.p, self.cum = [tuple(p) for p in pts], [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.cum.append(self.cum[-1] + math.hypot(b[0] - a[0], b[2] - a[2]))
        self.len = self.cum[-1]

    def at(self, s):
        import bisect
        c = self.cum
        i = min(max(bisect.bisect_right(c, s) - 1, 0), len(c) - 2)
        while i < len(c) - 2 and c[i + 1] - c[i] < 1e-6:
            i += 1
        while i > 0 and c[i + 1] - c[i] < 1e-6:
            i -= 1
        ln = c[i + 1] - c[i]
        t = (s - c[i]) / ln if ln > 1e-6 else 0.0
        a, b = self.p[i], self.p[i + 1]
        return tuple(a[j] + (b[j] - a[j]) * t for j in range(3))

    def tan(self, s, h=80.0):
        a, b = self.at(max(0.0, s - h)), self.at(min(self.len, s + h))
        n = math.hypot(b[0] - a[0], b[2] - a[2])
        return ((b[0] - a[0]) / n, (b[2] - a[2]) / n) if n > 1e-6 else (0.0, 1.0)

    def project(self, q):
        """(distance along, signed offset to the side) of q: the nearest place on the line; side > 0 = towards
        (tangent z, -tangent x), the +x side of a drive that heads +z (kl_fa_van.project's sign)."""
        best = None
        for i in range(len(self.p) - 1):
            a, b = self.p[i], self.p[i + 1]
            dx, dz = b[0] - a[0], b[2] - a[2]
            l2 = dx * dx + dz * dz
            if l2 < 1e-6:
                continue
            t = max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[2] - a[2]) * dz) / l2))
            d2 = (q[0] - a[0] - t * dx) ** 2 + (q[2] - a[2] - t * dz) ** 2
            if best is None or d2 < best[0]:
                ln = math.sqrt(l2)
                best = (d2, self.cum[i] + t * ln, ((q[0] - a[0]) * dz - (q[2] - a[2]) * dx) / ln)
        return best[1], best[2]

    def off(self, s, d, y=None):
        """The place d to the side of the line at s."""
        p, t = self.at(s), self.tan(s)
        return (p[0] + d * t[1], p[1] if y is None else y, p[2] - d * t[0])


def curve(pts, step=LANE_STEP):
    """A centripetal Catmull-Rom curve through the points (x, y, z) in the ground plane (y runs linearly between
    two points), sampled about every `step` units -> ([(x, y, z)], index in it of every given point).
    ASSUMPTION: it is not the curve Dead Men's engine laid through a route's points (that one was not read);
    it passes through every point, and the lane check walks THIS curve, which is the one the van's keys are put on."""
    pts = [p for i, p in enumerate(pts) if i == 0 or math.hypot(p[0] - pts[i - 1][0], p[2] - pts[i - 1][2]) > 1.0]
    q = [(2 * pts[0][0] - pts[1][0], 0.0, 2 * pts[0][2] - pts[1][2])] + pts + [(2 * pts[-1][0] - pts[-2][0], 0.0, 2 * pts[-1][2] - pts[-2][2])]
    out, marks = [], []
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        tj = lambda t, a, b: t + max(math.hypot(b[0] - a[0], b[2] - a[2]), 1e-6) ** 0.5
        t0 = 0.0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[2] - p1[2]) / step))
        marks.append(len(out))
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            lerp = lambda a, b, ta, tb: (a[0] + (b[0] - a[0]) * (t - ta) / (tb - ta), a[1] + (b[1] - a[1]) * (t - ta) / (tb - ta))
            a1, a2, a3 = lerp((p0[0], p0[2]), (p1[0], p1[2]), t0, t1), lerp((p1[0], p1[2]), (p2[0], p2[2]), t1, t2), lerp((p2[0], p2[2]), (p3[0], p3[2]), t2, t3)
            b1, b2 = lerp(a1, a2, t0, t2), lerp(a2, a3, t1, t3)
            c = lerp(b1, b2, t1, t2)
            out.append((c[0], p1[1] + (p2[1] - p1[1]) * k / n, c[1]))
    marks.append(len(out))
    out.append(pts[-1])
    return out, marks


def lane(L, G, path, s0, s1, skip=(), half=VAN_HALF, only=None):
    """The lane of a van on `path` (a Poly whose y is the road) from s0 to s1, every LANE_STEP units, five rays across
    `half`: -> [(s, what, name)] for collision of the map VAN_BODY over the road, a place with no road under a
    wheel, and a convex body (prop, parked car, key-framed piece) in the lane. skip: REF ids left out.
    only: a set of REF ids - then nothing but THEIR collision is listed (where the lane meets a gate)."""
    out, s = [], s0
    while s <= s1 + 1e-6:
        p, t = path.at(s), path.tan(s)
        for off in (-half, -half / 2, 0.0, half / 2, half):
            x, z = p[0] + off * t[1], p[2] - off * t[0]
            hs = [h for h in G.hits(x, z) if h[2] not in skip]
            road = lambda q: any(h[1] > FLOOR and abs(h[0] - p[1]) <= VAN_BODY[0] for h in q)
            # a ray that falls exactly on the joint of two ground tiles meets neither (M01, z 24300.1: SO1001_Alley_A_6x8m_09
            # ends, SO1001_Sidewalk_A_SpecialChunk_01 begins; road 1 unit before and 1 after). 'No road' is a ray that
            # finds none here AND none 2 units before and behind along the drive: a hole a wheel could meet still is one.
            if only is None and not road(hs) and not any(road([h for h in G.hits(x + d * t[0], z + d * t[1]) if h[2] not in skip]) for d in (-2.0, 2.0)):
                out.append((round(s), 'no road within %d of the drive\'s height %.0f at %+d across' % (VAN_BODY[0], p[1], off), ''))
            for y, _up, r in hs:
                if p[1] + VAN_BODY[0] < y < p[1] + VAN_BODY[1] and (only is None or r in only):
                    out.append((round(s), 'collision %d over the road at %+d across' % (y - p[1], off), L.name(r)))
        for ty, r, lo, hi in G.boxes:
            if r not in skip and (only is None or r in only) and lo[0] - half < p[0] < hi[0] + half and lo[2] - half < p[2] < hi[2] + half and \
                    lo[1] < p[1] + VAN_BODY[1] and hi[1] > p[1] + 10:
                out.append((round(s), '%s body in the lane' % {2: 'rigid', 3: 'vehicle', 4: 'key-framed', 5: 'weapon'}.get(ty, ty), L.name(r)))
        s += LANE_STEP
    return out


# ---- a gate Dead Men's car broke through on its way out (M01_FA_A; re/map_escape.md 19)
# Dead Men: Escape!EscapeCars\GateTrigger (a box the CAR enters, 5.6 m before the fence) -> RelayMsgList ->
#   GateDeactivator @DeactivateGeom('AITrigger', [the closed fence piece SO1001_Fence_A_5m_01, the trigger itself])
#   Activator @AIDWrapper([SO1001_Fence_A_5m_AnimGroup_00], 'Activate') -> the group's own RelayMessage -> its child
#   SO1001_Fence_A_5m_Attach @MatPosAnim('Activate', frames 0..41) + a KEYS chunk.
# The KEYS chunk is the van's own format and its six tables are in the built .buf, equal to Dead Men's key for key
# (measured): 42 frames in which the fence piece is thrown 9.3 m up the road and tumbles = the car RAMS the gate.
# It is NOT a clip of the .ANM (which is not carried). ASSUMPTION that Dog Days plays a Dead Men KEYS chunk as it
# plays its own: same chunk header, same table forms; the owner has seen Dead Men's garage doors open on the bank.
# For the van the same two things are done by the van's own leave message (gate_wire below).
GATE_NOSE = 250.0               # the van's nose before its origin (F07: the front lights stand 245 ahead)
GATE_EARLY = 2                  # the gate goes this many frames before the nose is at it (25 frames a second)
GATE_PAST = 400.0               # a drive that ends nearer than this behind a gate ends IN it: a fault
RELAY_EXIT = 'Relay_Stop_Audio_Idle'    # stock F07, in list 3 of the van's 'Activate_Exit' piece: its RelayMessage
                                        # hears 'Activate_Exit' when the van sets off (and stops the idle sound)


def gate_find(L, top):
    """In the subtree `top` of Dead Men's escape car: the gate it opened -> None or {'off': [nodes a DeactivateGeom of
    the car switches off, outside the subtree], 'knock': [(group, piece)]: an AIDWrapper 'Activate' target outside
    the subtree whose RelayMessage hands 'Activate' to a piece with MatPosAnim and a KEYS chunk, 'own': the car's
    trigger boxes that same DeactivateGeom switches off (the gate's trigger), 'refs': REF ids of all of it}.
    A gate is HANDLED only in this exact form; anything else the car switched keeps the GAP rule."""
    sc = L.sc
    inside = lambda j: top <= j < sc.end[top]
    res = lambda x: [j for s in (x if isinstance(x, list) else [x]) if isinstance(s, str) and s.startswith('ROOT\\') for j in sc.resolve(s)]
    off, own, knock = [], [], []
    for k in range(top, sc.end[top]):
        for _i, v in L.ctrl(k, 'DeactivateGeom'):
            tg = res(v[1])
            if any(not inside(j) for j in tg):
                off += [j for j in tg if not inside(j)]
                own += [j for j in tg if inside(j)]
        for _i, v in L.ctrl(k, 'AIDWrapper'):
            if v[1] != 'Activate':
                continue
            for g in res(v[0]):
                for _j, r in L.ctrl(g, 'RelayMessage'):
                    for piece in (res(r[2]) if r[0] == 'Activate' and r[1] == 'Activate' else []):
                        raw = L.ents[piece - 1].raw
                        if not inside(g) and g <= piece < sc.end[g] and raw and b'SYEK' in raw and \
                                any(m[0] == 'Activate' for _x, m in L.ctrl(piece, 'MatPosAnim')):
                            knock.append((g, piece))
    if not off or not knock:
        return None
    refs = {L.ents[j - 1].ref for j in off} | {L.ents[j - 1].ref for g, _p in knock for j in range(g, sc.end[g])}
    return {'off': sorted(set(off)), 'knock': sorted(set(knock)), 'own': sorted(set(own)), 'refs': refs}


def gate_wire(sc, P, delay, timer, log=print):
    """On the joined scene: the gate of plan P goes when the van's nose is at it. Three controllers are ADDED (at the
    end of three nodes' lists; no entity added, nothing removed) and one field is changed:
      van's Relay_Stop_Audio_Idle   + RelayMessage('Activate_Exit' -> 'AITrigger', to the TIMER node)   (the node
                                      hears 'Activate_Exit' at the start of the leave leg: its stock relay stops
                                      the idle sound on it)
      the timer node `timer`        + TriggerDelay2(delay, 0, -1, 0, [the gate's group])   (the form of 183 stock
                                      timers; armed by 'AITrigger' and by nothing else: kl2 0x71e25d; a node that
                                      has NO controller and that no message reaches: the kept camera's place box)
      the gate's group              + DeactivateGeom('AITrigger', [the closed piece], 0)   (Dead Men's own
                                      GateDeactivator, without the car's trigger)
                                    its own RelayMessage('Activate' -> 'Activate', to the animated piece): the
                                      in-message becomes 'AITrigger' (one field; no second relay)
    NO NODE SENDS TO ITSELF AND NO NODE IS REACHED TWICE (gate_read tests it). WHY, live 2026-10-11 (stack overflow
    c00000fd at the level's start, callers 008f1733 <- 0069733e <- 00759314 <- 004461b2 <- 006175ce <- 008f1733):
    ZRelayMessage's handler 0x8f1680 hands the message 'GetMatPosAnim' (id at 0x1538910, tested at 0x8f16bf) on to
    its target WHATEVER its in-message is, and a MatPosAnimProxy asks every node of its list for its MatPosAnim
    with that message when the level starts. Relay_Stop_Audio_Idle is in the list of the van's 'Activate_Exit'
    piece; the first form of this wiring had a relay on it that named its OWN node: node -> relay -> node, without
    end. (Stock has relays to their own node - AnimProxy_RearDoors_Close, F01's Wall_Explosion_Sound - but none
    of those nodes is in a proxy's list.) For the same reason nothing with a MatPosAnim may be reached from that
    node through relays alone: it would answer the van's proxy. The timer in between ends that message (0x71e2d4:
    anything but 'AITrigger' goes to the base class).
    ASSUMPTIONS: every controller of a node hears a message sent to the node; a relay -> TriggerDelay2 link (no
    stock F level has one; both ends read in the exe); a deactivated static piece loses its collision with its
    picture (it did in Dead Men).
    NOT ADDED: Dead Men's ActivateGeom on the group - the group is not hidden in the file (ZGEOM[3] 0, no .gms flag
    0x400, in Dead Men's own file too), so there is nothing to switch on.
    If the same van is called a second time the timer runs again and the piece is thrown again from the gate."""
    g = P['gate']
    host = sc.resolve('ROOT\\' + VAN_GROUP + '\\F07_Escape_Vehicle_01\\' + RELAY_EXIT)
    proxy = sc.resolve('ROOT\\' + VAN_GROUP + '\\F07_Escape_Vehicle_01')
    if len(host) != 1 or len(proxy) != 1:
        raise ValueError('kl_map_escape: the van has no %s' % RELAY_EXIT)
    host = host[0]
    heard = [v for _k, _i, v in [(proxy[0], i, [kl_fa.value(sc, u) for u in units(b[1:-1])]) for i, (nm, b) in enumerate(sc.nodes[proxy[0]]['ctrls'])
                                 if sc.p.key(nm) == 'MatPosAnimProxy'] if v[6] == 'Activate_Exit' and sc.path[host] in v[3]]
    stock = [[kl_fa.value(sc, u) for u in units(b[1:-1])] for nm, b in sc.nodes[host]['ctrls'] if sc.p.key(nm) == 'RelayMessage']
    if len(heard) != 1 or not any(v[0] == 'Activate_Exit' for v in stock):
        raise ValueError('kl_map_escape: %s is not in the list of the van\'s Activate_Exit piece with a relay on that message' % RELAY_EXIT)
    if len(g['knock']) != 1:
        raise ValueError('kl_map_escape: %d animated gate groups (one is wired)' % len(g['knock']))
    grp, piece = g['knock'][0]
    for p in [grp, piece, timer] + g['off']:
        if len(sc.resolve(p)) != 1:
            raise ValueError('kl_map_escape: the joined scene has %d nodes %s' % (len(sc.resolve(p)), p))
    gk, tk = sc.resolve(grp)[0], sc.resolve(timer)[0]
    if sc.nodes[tk]['ctrls'] or sc.cls(tk) != 'ZBoxPrimitive' or tk in (host, gk) or gk <= tk < sc.end[gk]:
        raise ValueError('kl_map_escape: the timer node %s is not a box without a controller outside the gate' % timer)
    if any(sc.p.key(nm) in ('DeactivateGeom', 'TriggerDelay2') for k in (host, gk) for nm, _b in sc.nodes[k]['ctrls']):
        raise ValueError('kl_map_escape: the gate is wired already')

    def add(k, name, cls, vals):
        us = [list(u) for u in units(kl_fa.blank(sc, cls)[1:-1])]
        for i, v in enumerate(vals):
            if isinstance(v, str):
                us[i] = [kl_fa._str(sc, v)]
            elif isinstance(v, list):
                us[i] = kl_fa._refs(sc, v)
            elif isinstance(v, float):
                us[i] = [(0x0a, struct.pack('<f', v))]
            elif v:
                raise ValueError('a flag that is set: not written here')
        sc.nodes[k]['ctrls'].append((kl_fa._str(sc, name), [(0x02, b'')] + [t for u in us for t in u] + [(0x7e, b'')]))

    add(host, 'RelayMessage', 'ZRelayMessage', ['Activate_Exit', 'AITrigger', timer, 0])
    add(tk, 'TriggerDelay2', 'ZTriggerDelay2', [float(delay), 0.0, -1.0, 0, [grp]])
    add(gk, 'DeactivateGeom', 'ZDeactivateGeom', ['AITrigger', list(g['off']), 0])
    # the group's own relay ('Activate' -> 'Activate', to the piece; Dead Men's Activator sent it 'Activate' and is
    # gone) gets the in-message 'AITrigger': a second relay to the same piece would be a node reached two ways
    own = [i for i, (nm, bd) in enumerate(sc.nodes[gk]['ctrls']) if sc.p.key(nm) == 'RelayMessage'
           and [kl_fa.value(sc, u) for u in units(bd[1:-1])][:3] == ['Activate', 'Activate', piece]]
    if len(own) != 1:
        raise ValueError('kl_map_escape: the gate group has %d relays Activate -> Activate to its piece' % len(own))
    kl_fa.edit(sc, gk, own[0], lambda us: us.__setitem__(0, [kl_fa._str(sc, 'AITrigger')]))
    log('  kl_map_escape: gate: the van\'s %s -> timer on %s, %.2f s -> %s: %s switched off, %s thrown (its own 42-frame keys)' % (
        RELAY_EXIT, timer[5:], delay, grp.rsplit('\\', 1)[1], ', '.join(p.rsplit('\\', 1)[1] for p in g['off']), piece.rsplit('\\', 1)[1]))
    return 3


def message_walk(L, start):
    """The nodes a message entering node `start` can be handed on to, by the controllers that hand messages on
    (RelayMessage field 2, RelayMessageList field 2, TriggerDelay2 field 4, AIDWrapper field 0) -> (order,
    faults). A FAULT is a node reached twice - by a loop or by two ways - and a node that names itself: a relay
    hands 'GetMatPosAnim' on whatever its in-message (kl2 0x8f16bf, 0x6e3cd6), so a loop of relays is endless
    (the stack overflow of 2026-10-11); two ways are refused too, the wiring this module writes is a chain.
    Also a FAULT: a node with MatPosAnim / MatPosAnimProxy reached from `start` through relays ALONE - it would
    get the 'GetMatPosAnim' of the proxy that has `start` in its list."""
    sc, seen, faults, order = L.sc, {start: None}, [], [start]
    def go(k, relays_only):
        for name, f in (('RelayMessage', 2), ('RelayMessageList', 2), ('TriggerDelay2', 4), ('AIDWrapper', 0)):
            for _i, v in L.ctrl(k, name):
                x = v[f]
                for s in (x if isinstance(x, list) else [x]):
                    for j in (sc.resolve(s) if isinstance(s, str) and s else []):
                        ro = relays_only and name.startswith('Relay')
                        if j in seen:
                            faults.append('message loop: %s (%s) hands on to %s, which %s' % (
                                sc.names[k], name, sc.names[j], 'is the node itself' if j == k else 'the wiring has reached already'))
                            continue
                        seen[j] = k; order.append(j)
                        if ro and (L.ctrl(j, 'MatPosAnim') or L.ctrl(j, 'MatPosAnimProxy')):
                            faults.append('%s has a MatPosAnim and is reached from %s through relays alone: it would answer the '
                                          'van\'s GetMatPosAnim' % (sc.names[j], sc.names[start]))
                        go(j, ro)
    go(start, True)
    return order, faults


def gate_read(L, top):
    """The gate wiring of a BUILT level, from its files -> None or {'delay', 'refs': REF ids that are gone or thrown
    when the timer fires, 'faults': [...], 'chain': [node names]}. top: the van's top-level node."""
    sc = L.sc
    N = _van_nodes(sc, top)
    host = next((k for k in range(top, sc.end[top]) if sc.names[k] == RELAY_EXIT), None)
    if host is None:
        return None
    rel = [v for _i, v in L.ctrl(host, 'RelayMessage') if v[0] == 'Activate_Exit' and v[1] == 'AITrigger']
    if not rel and not L.ctrl(host, 'TriggerDelay2'):
        return None
    out = {'delay': 0.0, 'refs': set(), 'faults': [], 'names': []}
    bad = out['faults'].append
    order, loops = message_walk(L, host)
    out['faults'] += ['gate: ' + x for x in loops]
    out['chain'] = [sc.names[k] for k in order]
    if L.ctrl(host, 'TriggerDelay2'):
        bad('gate: the timer sits on %s itself (it must be fed by a relay from it)' % RELAY_EXIT)
    tks = [j for v in rel for j in sc.resolve(v[2])]
    if len(rel) != 1 or len(tks) != 1 or tks[0] == host:
        bad('gate: %s does not hand Activate_Exit as AITrigger to ONE other node' % RELAY_EXIT)
        return out
    tk = tks[0]
    tm = L.ctrl(tk, 'TriggerDelay2')
    if len(tm) != 1 or len(sc.nodes[tk]['ctrls']) != 1 or tm[0][1][1:4] != [0.0, -1.0, 0]:
        bad('gate: %s does not carry one TriggerDelay2 of the stock form (d, 0, -1, 0) and nothing else' % sc.names[tk])
        return out
    out['delay'] = tm[0][1][0]
    if not any(v[6] == 'Activate_Exit' and sc.path[host] in v[3] for _i, v in L.ctrl(N['F07_Escape_Vehicle_01'], 'MatPosAnimProxy')):
        bad('gate: %s is not in the list of the van\'s Activate_Exit piece' % RELAY_EXIT)
    for s in tm[0][1][4]:
        hit = sc.resolve(s)
        if len(hit) != 1:
            bad('gate: the timer names %d nodes %s' % (len(hit), s))
            continue
        for _i, v in L.ctrl(hit[0], 'DeactivateGeom'):
            if v[0] == 'AITrigger':
                for t in v[1]:
                    for j in sc.resolve(t):
                        out['refs'].add(L.ents[j - 1].ref); out['names'].append(sc.names[j])
        for _i, v in L.ctrl(hit[0], 'RelayMessage'):
            if v[0] == 'AITrigger' and v[1] == 'Activate':
                for j in sc.resolve(v[2]):
                    raw = L.ents[j - 1].raw
                    if raw and b'SYEK' in raw and any(m[0] == 'Activate' for _x, m in L.ctrl(j, 'MatPosAnim')):
                        out['refs'] |= {L.ents[i - 1].ref for i in range(hit[0], sc.end[hit[0]])}
                        out['names'].append(sc.names[j])
                    else:
                        bad('gate: %s is handed Activate and has no MatPosAnim with keys' % sc.names[j])
    if not out['refs']:
        bad('gate: the timer switches nothing')
    return out


def _first(obst):
    """obstructions -> {name or what: (first s, last s, count)} in order of the first."""
    d = collections.OrderedDict()
    for s, what, nm in sorted(obst):
        e = d.setdefault(nm or what, [s, s, 0, what])
        e[1], e[2] = s, e[2] + 1
    return d


def _crossings(bounds, pts, dist):
    """[(level bound, from, to)]: every stretch of the points (their distance in `dist`) that is inside a LevelBound
    box, tested 100 over the point (a person's chest)."""
    out = []
    for nm, inside in bounds:
        run = None
        for p, d in zip(pts, dist):
            if inside((p[0], p[1] + 100.0, p[2])):
                run = [nm, round(d), round(d)] if run is None else run[:2] + [round(d)]
            elif run:
                out.append(run); run = None
        if run:
            out.append(run)
    return out


def van_plan(src, log=print):
    """A finished build that still has Dead Men's escape car -> the van's drive on that map (JSON form):
    'path' = [[x, road y, z]] every LANE_STEP units from the waiting place to the end, 'lin' / 'lout' = the lengths
    of the drive in and away along it, 'wait' / 'stop' / 'end' = the van's origin there, 'board' = where its
    boarding box stands at the stop, 'cam' = the escape camera's place, 'drop' = Dead Men's top-level objects the
    van replaces, 'faults' = why no van can be laid (then nothing is built)."""
    L = Level(src)
    G = Ground(L)
    sc = L.sc
    P = collections.OrderedDict(src=os.path.abspath(src), faults=[], notes=[])
    cars = [v for v in vehicles(L) if v['kind'] == 'car' and len(v['routes']) == 2]
    if len(cars) != 1:
        P['faults'].append('%d escape cars with two spline routes (one is wanted)' % len(cars))
        return P
    v = cars[0]
    top = sc.top[v['node']]
    own = {L.ents[j - 1].ref for j in range(top, sc.end[top])}
    pin, pout = spline(L, v['routes']['incoming'])[0], spline(L, v['routes']['escaping'])[0]
    car_stop = pin[-1]
    ahead = [p for p in pout if math.hypot(p[0] - car_stop[0], p[2] - car_stop[2]) > 150.0]
    dense, marks = curve(pin + ahead)
    C = Poly(dense)
    s_car = C.cum[marks[len(pin) - 1]]
    s_stop = s_car + BOARD_BACK                         # the van's REAR box stands where Dead Men's car stopped
    # the road under the curve, smoothed over +-100 (a kerb must not make the van hop)
    raw = []
    for p in dense:
        g = G.under(p[0], p[1], p[2])
        raw.append(g[0] if g else None)
    if any(r is None for r in raw):
        i = next(i for i, r in enumerate(raw) if r is None)
        P['notes'].append('no ground under the routes\' curve at %d along it (%d, %d): the last ground is kept' % (C.cum[i], dense[i][0], dense[i][2]))
        last = next(r for r in raw if r is not None)
        for i, r in enumerate(raw):
            last = raw[i] = last if r is None else r
    w = max(1, int(100.0 / LANE_STEP))
    road = [sum(raw[max(0, i - w):i + w + 1]) / len(raw[max(0, i - w):i + w + 1]) for i in range(len(raw))]
    R = Poly([(p[0], y, p[2]) for p, y in zip(dense, road)])
    P['rough'] = round(max(abs(a - b) for a, b in zip(raw, road)), 1)
    # how far each way
    s_wait, s_end = max(0.0, s_stop - LIMIT_IN), min(R.len - VAN_NOSE, s_stop + LIMIT_OUT)
    # things Dead Men's car switched on its way are closed for a van - but a gate of the form gate_find() knows
    # (M01: the fence it rammed) is opened by the van's own leave message (gate_wire) and does not end the drive
    gate = gate_find(L, top)
    gate_nodes = set(gate['off'] + gate['own'] + [j for g, _p in gate['knock'] for j in range(g, sc.end[g])]) if gate else set()
    gate_refs = gate['refs'] if gate else set()
    own = own | gate_refs if gate else own
    for k in range(top, sc.end[top]):
        for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']):
            name = sc.p.key(nm)
            if name not in ('ActivateGeom', 'DeactivateGeom', 'AIDWrapper', 'OnlineTriggerBox'):
                continue
            vals = L.ctrl(k, name)[0][1]
            tg = [j for x in vals for s in (x if isinstance(x, list) else [x]) if isinstance(s, str) and s.startswith('ROOT\\') for j in sc.resolve(s)]
            for j in ([k] if name == 'OnlineTriggerBox' else tg):
                if top <= j < sc.end[top] and name != 'OnlineTriggerBox':
                    continue
                if j in gate_nodes:
                    continue
                at = L.place(j)
                s, d = R.project(at)
                if abs(d) < 600.0 and max(abs(x) for x in at) > 1.0 and s > s_stop and s - GAP < s_end:
                    P['notes'].append('%s of Dead Men\'s car (%s) at (%d, %d, %d), %d along the drive away: the car switched it on its way, '
                                      'a van does not - the drive ends %d before it' % (name, sc.path[j][5:][-60:], *at, s - s_stop, GAP))
                    s_end = s - GAP
    ob = lane(L, G, R, s_wait - VAN_TAIL, s_end + VAN_NOSE, own)
    P['lane_first_pass'] = {k: e for k, e in _first(ob).items()}
    after = [s for s, _w, _n in ob if s > s_stop + 200]
    before = [s for s, _w, _n in ob if s < s_stop - 200]
    at_stop = [(s, w_, n) for s, w_, n in ob if abs(s - s_stop) <= 200]
    if after and min(after) - GAP - VAN_NOSE < s_end:
        nm = next(n or w_ for s, w_, n in sorted(ob) if s == min(after))
        P['notes'].append('the drive away is cut %d before \'%s\' (in the lane %d along it)' % (GAP, nm, min(after) - s_stop))
        s_end = min(after) - GAP - VAN_NOSE
    if before and max(before) + GAP + VAN_TAIL > s_wait:
        nm = next(n or w_ for s, w_, n in sorted(ob) if s == max(before))
        P['notes'].append('the drive in starts %d after \'%s\' (in the lane %d before the stop)' % (GAP, nm, s_stop - max(before)))
        s_wait = max(before) + GAP + VAN_TAIL
    for s, w_, n in at_stop:
        P['faults'].append('at the stop: %s %s' % (w_, n))
    if s_stop - s_wait < MIN_IN:
        P['faults'].append('only %d of clear lane before the stop (least %d)' % (s_stop - s_wait, MIN_IN))
    if s_end - s_stop < MIN_OUT:
        P['faults'].append('only %d of clear lane after the stop (least %d)' % (s_end - s_stop, MIN_OUT))
    n = int((s_end - s_wait) / LANE_STEP)
    path = [R.at(s_wait + (s_end - s_wait) * i / n) for i in range(n + 1)]
    V = Poly(path)
    lin = s_stop - s_wait
    P.update(car=v['name'], car_stop=[round(x, 1) for x in car_stop], lin=round(lin, 1), lout=round(V.len - lin, 1),
             path=[[round(x, 2) for x in p] for p in path])
    up = lambda p: [round(p[0], 1), round(p[1] + VAN_UP, 1), round(p[2], 1)]
    P['wait'], P['stop'], P['end'] = up(V.at(0.0)), up(V.at(lin)), up(V.at(V.len))
    P['heading'] = {k: round(_heading(V.tan(s, AXLES)), 1) for k, s in (('wait', 0.0), ('stop', lin), ('end', V.len))}
    t = V.tan(lin, AXLES)                               # the box rides 337 behind the origin of the STANDING van
    P['board'] = [round(P['stop'][0] - BOARD_BACK * t[0], 1), round(P['stop'][1] - VAN_UP, 1), round(P['stop'][2] - BOARD_BACK * t[1], 1)]
    P['lane'] = _first(lane(L, G, V, -VAN_TAIL, V.len + VAN_NOSE, own))
    for nm, (a, b_, cnt, what) in P['lane'].items():
        P['faults'].append('in the lane after the cut: %s (%s) at %d..%d' % (nm, what, a, b_))
    if gate:                                            # where the lane meets the gate (the key is only there with a gate:
        hit = sorted(lane(L, G, V, lin, V.len + VAN_NOSE, only=gate_refs))     # M02's and M03's plans stay as they were)
        if not hit:
            P['notes'].append('the gate Dead Men\'s car opened (%s) is not in the van\'s lane: left as it is' % sc.names[gate['off'][0]])
        else:
            at, last = hit[0][0] - lin, hit[-1][0] - lin
            P['gate'] = collections.OrderedDict(
                at=round(at), to=round(last), off=[sc.path[j] for j in gate['off']],
                knock=[[sc.path[g], sc.path[p]] for g, p in gate['knock']], names=sorted({n for _s, _w, n in hit}))
            if V.len - lin < last + GATE_PAST:
                P['faults'].append('the drive ends %d behind the gate %s (least %d): it would end in it' % (V.len - lin - last, sc.names[gate['off'][0]], GATE_PAST))
            P['notes'].append('gate %s, %d..%d along the drive away: Dead Men\'s car rammed it (%s); the van\'s leave message does the same '
                              '(gate_wire), so the drive does not end before it' % (', '.join(P['gate']['names']), at, last, sc.names[gate['knock'][0][1]]))
    # the level bounds the drive passes, the other cars that use the road (said, not repaired: Dead Men's own design)
    bounds = level_bounds(L)
    P['bounds'] = _crossings(bounds, path, [c - lin for c in V.cum])
    P['other_cars'] = ['%s %s' % (c, w_) for c, _which, w_ in other_cars(L, v, {'the van\'s drive': path})]
    # the camera: the designers' place nearest the stop, and what the car's objects are called
    cams = [c for c in cameras(L, G, [tuple(P['stop'])]) if c['target']]
    drop = [sc.names[top]]
    if cams:
        c = min(cams, key=lambda c: math.dist(c['target'], P['stop']))
        P['cam'] = [round(x, 1) for x in c['target']]
        P['cam_from'] = c['target_name'][5:]
        P['cam_sight'] = {'stop': [L.name(r) for _t, r in G.between(tuple(P['cam']), (P['stop'][0], P['stop'][1] + 100.0, P['stop'][2]))][:3],
                          'end': [L.name(r) for _t, r in G.between(tuple(P['cam']), (P['end'][0], P['end'][1] + 100.0, P['end'][2]))][:3]}
        near = c
        for c in cams:
            trig = sc.resolve('ROOT\\' + c['trigger'])[0]
            # a SECOND camera of the designers whose trigger box lies on the drive away, well after the van's own
            # fixed camera has come on (CameraTrigger01, 8.5 m after the stop), is KEPT: it films the road out
            # (M01: CamPos02 looks down the gate road). Same pattern as the first: OnlineEscCamTrigger(the van,
            # the box) -> CCameraBox eFMM_LookFromPos -> a place of its own; van_wire names the van in field 0.
            # ASSUMPTION as for the first (re/map_escape.md 14): what the trigger tests when field 0 names a vehicle.
            if c is not near and sc.cls(trig) == 'ZBoxPrimitive' and not c['fault'] and c['mode'] in (FROM_FA, FROM_POS):
                bv, (Rm, T) = L.values(trig), L.frame(trig)
                half = [bv['ZBoxPrimitive[%d]' % i] for i in range(3)]
                ins = [cs - lin for p, cs in zip(path, V.cum) if all(abs(sum(Rm[a][b] * ((p[a] + (100.0 if a == 1 else 0.0)) - T[a]) for a in range(3))) <= half[b] for b in range(3))]
                if ins and min(ins) > 1500.0:
                    P.setdefault('cams_keep', []).append(collections.OrderedDict(
                        trigger=sc.path[trig], camera=sc.path[c['node']], eye=[round(x, 1) for x in c['eye'] or c['target']],
                        on=[round(min(ins)), round(max(ins))],
                        sight_end=[L.name(r) for _t, r in G.between(tuple(c['target']), (P['end'][0], P['end'][1] + 100.0, P['end'][2]))][:3]))
                    continue
            for k in (c['node'], sc.resolve(c['target_name'])[0], trig):
                drop.append(sc.names[k])
    else:
        P['faults'].append('no escape camera with a place of its own in the build')
    for k, _i, vals in kl_fa.controllers(sc, 'PlayerAction'):
        if 'EnterVehicle' in vals:
            drop.append(sc.names[k])
            drop += [sc.names[j] for x in vals if isinstance(x, list) for s in x for j in sc.resolve(s) if kl_fa.has(sc, j, 'OnlineGamePlayTrigger')]
    for nm in drop:
        k = sc.resolve('ROOT\\' + nm)
        if len(k) != 1 or sc.parent[k[0]] != 0 or any(ch in nm for ch in '*?['):
            P['faults'].append('%s is not one top-level object: it cannot be left out by name' % nm)
    P['drop'] = list(collections.OrderedDict.fromkeys(drop))
    P['exits'] = [sc.path[k][5:] for k, _i, _v in kl_fa.controllers(sc, kl_fa.EXIT)]
    log('van plan for %s: Dead Men\'s %s stops at (%d, %d, %d)' % (src, v['name'], *car_stop))
    log('  waits (%d, %d, %d) heading %.0f -> %.0f m in 7.2 s -> stops (%d, %d, %d) heading %.0f (rear box at (%d, %d, %d)) -> %.0f m in '
        '8.48 s -> ends (%d, %d, %d) heading %.0f' % (*P['wait'], P['heading']['wait'], lin / 100, *P['stop'], P['heading']['stop'], *P['board'],
                                                  (V.len - lin) / 100, *P['end'], P['heading']['end']))
    log('  road under the drive y %.1f .. %.1f (raw against smoothed: at most %.1f apart); camera at (%d, %d, %d) (%s); sight to the stop: %s, to the end: %s' % (
        min(p[1] for p in path), max(p[1] for p in path), P['rough'], *P.get('cam', (0, 0, 0)), P.get('cam_from', '-'),
        ', '.join(P.get('cam_sight', {}).get('stop', [])) or 'clear', ', '.join(P.get('cam_sight', {}).get('end', [])) or 'clear'))
    for e in P['bounds']:
        log('  passes the level bound %s from %d to %d (0 = the stop)' % tuple(e))
    for x in P['other_cars']:
        log('  other car: ' + x[:230])
    for x in P['notes']:
        log('  note: ' + x)
    for c in P.get('cams_keep', []):
        log('  second camera kept: %s at (%d, %d, %d), its box %s holds the drive away from %d to %d; sight to the end: %s' % (
            c['camera'][5:], *c['eye'], c['trigger'][5:], *c['on'], ', '.join(c['sight_end']) or 'clear'))
    log('  left out of Dead Men\'s map: ' + ', '.join(P['drop']))
    for x in P['faults']:
        log('  FAULT ' + x)
    return P


# ---- the van's keys
class VanKeys:
    """The six tables of a KEYS chunk (module comment above). head: the .buf head; raw: the entity's data block;
    ends: every table offset of the level + the head's length (a table ends where the next one begins)."""
    def __init__(self, head, raw, ends, keys_tracks):
        (p, self.offs), = keys_tracks(raw)
        self.frames = struct.unpack_from('<I', raw, p - 0x10)[0]
        self.head = head
        size = lambda o: next(x for x in ends if x > o) - o
        self.f2p, self.f2r = self.bits(self.offs[3], self.frames), self.bits(self.offs[0], self.frames)
        self.npos, self.nrot = max(self.f2p) + 1, max(self.f2r) + 1
        if self.npos * 12 > size(self.offs[5]) or self.nrot * 8 > size(self.offs[2]):
            raise ValueError('KEYS: the frame tables name keys beyond the key tables')
        self.pos = [struct.unpack_from('<3f', head, self.offs[5] + 12 * i) for i in range(self.npos)]
        self.rot = [struct.unpack_from('<4h', head, self.offs[2] + 8 * i) for i in range(self.nrot)]

    def bits(self, o, n):
        w, out = self.head[o], []
        for i in range(n):
            v = 0
            for j in range(i * w, i * w + w):
                v = (v << 1) | ((self.head[o + 1 + j // 8] >> (7 - j % 8)) & 1)
            out.append(v)
        return out

    @staticmethod
    def yaw(q):
        """Heading (degrees, atan2(x, z)) of local +Z turned by the quaternion."""
        x, y, z, w = [c / 32767.0 for c in q]
        return math.degrees(math.atan2(2 * (x * z + w * y), 1 - 2 * (x * x + y * y)))

    @staticmethod
    def turned(q, deg):
        """The quaternion turned by `deg` about the world's Y (the body's own sway is kept)."""
        h = math.radians(deg) / 2
        a = (0.0, math.sin(h), 0.0, math.cos(h))
        b = [c / 32767.0 for c in q]
        r = (a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
             a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2])
        n = math.sqrt(sum(c * c for c in r)) or 1.0
        return tuple(max(-32767, min(32767, int(round(c / n * 32767)))) for c in r)

    def drive(self):
        """Number of keys of the main drive (wait -> stop -> away): the keys up to the first jump of over 400."""
        return next((i for i in range(1, self.npos) if math.dist(self.pos[i], self.pos[i - 1]) > 400), self.npos)


def _van_nodes(sc, top):
    name = lambda n: next(k for k in range(top, sc.end[top]) if sc.names[k] == n and 'Reflection' not in sc.path[k])
    d = {n: name(n) for n in ('EscapeVehicle_Animation_F07', 'V_Van_00', 'BoardingTrigger', 'PathBlockerVan', 'TriggerBox_RearDoors_Open',
                              'CameraTrigger01', 'CameraTrigger_InVan', 'CamPos01', 'CamPos_InVan_FocusPoint', 'F07_Escape_Vehicle_01',
                              'F07_EscapeVan_01')}
    d['EscCamera01'] = next(k for k in range(top, sc.end[top]) if sc.names[k].startswith('EscCamera01_'))
    d['strays'] = [k for k in range(top + 1, sc.end[top]) if sc.parent[k] == top and k != d['EscapeVehicle_Animation_F07']]
    return d


def _leg_frames(sc, k):
    """{message: (first frame, last frame)} of the MatPosAnimProxy controllers on node k."""
    out = {}
    for nm, body in sc.nodes[k]['ctrls']:
        if sc.p.key(nm) == 'MatPosAnimProxy':
            v = [kl_fa.value(sc, u) for u in units(body[1:-1])]
            out[v[6]] = (v[1], v[2])
    return out


def van_prepare(S, P, log=print):
    """Stock F07 (kl_graft.Level, unedited) -> its first escape van laid on the plan P: the position and rotation
    keys rewritten in place (no key added, dropped or re-timed), everything that stands beside the drive moved, the
    pieces that lie loose at F07's origin put away. -> report (also ST['van'])."""
    import kl_graft
    import kl_fa_author as au
    sc = S.prp
    top = au.node_of(sc, VAN_TOP)
    N = _van_nodes(sc, top)
    van, grp = N['V_Van_00'], N['EscapeVehicle_Animation_F07']
    for k in (grp, N['F07_Escape_Vehicle_01'], sc.parent[N['CameraTrigger01']], top):
        if any(abs(x) > 1e-3 for x in struct.unpack('<3f', S.ents[k - 1].trans[:12])):
            raise ValueError('kl_map_escape: %s does not stand at the origin: its children\'s places are not world places' % sc.path[k])
    bz = struct.unpack('<3f', S.ents[N['BoardingTrigger'] - 1].trans[:12])[2]
    if abs(-bz - BOARD_BACK) > 5.0:
        raise ValueError('kl_map_escape: the van\'s boarding box is %.0f behind its origin, BOARD_BACK says %.0f' % (-bz, BOARD_BACK))
    ends = sorted({o for e in S.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(S.scene.head)})
    K = VanKeys(S.scene.head, S.ents[van - 1].raw, ends, kl_graft.keys_tracks)
    legs = _leg_frames(sc, N['F07_Escape_Vehicle_01'])
    cut = K.drive()
    old = Poly(K.pos[:cut])
    k_stop = K.f2p[legs['Activate_Enter'][1]]
    s_stop, y0 = old.cum[k_stop], K.pos[0][1]
    new = Poly([tuple(p) for p in P['path']])
    lin, lout = P['lin'], new.len - P['lin']
    to = lambda s: lin * s / s_stop if s <= s_stop else lin + lout * (s - s_stop) / (old.len - s_stop)
    # positions
    where = []                                          # per position key: (distance on the old drive, new distance, side)
    for i, p in enumerate(K.pos):
        s, d = (old.cum[i], 0.0) if i < cut else old.project(p)
        where.append((s, to(s), max(-SIDE, min(SIDE, d))))
    pos = []
    for (s, s2, d), p in zip(where, K.pos):
        q = new.off(s2, d)
        pos.append((q[0], q[1] + VAN_UP + p[1] - y0, q[2]))
    # rotations: the nose keeps its angle to the drive (clamped on the drive itself), the sway stays
    rot, worst = [], 0.0
    first = {}
    for f in range(K.frames - 1, -1, -1):
        first[K.f2r[f]] = f
    for r, q in enumerate(K.rot):
        kp = K.f2p[first[r]]
        s, s2, _d = where[kp]
        rel = 0.0 if kp < cut else _wrap(K.yaw(q) - _heading(old.tan(s, AXLES)))    # a crash piece keeps its spin against the drive
        want = _heading(new.tan(s2, AXLES)) + rel
        q2 = K.turned(q, want - K.yaw(q))
        worst = max(worst, abs(_wrap(K.yaw(q2) - want)))
        rot.append(q2)
    if worst > 1.0:
        raise ValueError('kl_map_escape: a rewritten rotation key is %.1f degrees off its heading' % worst)
    head = bytearray(S.scene.head)
    for i, p in enumerate(pos):
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
    for i, q in enumerate(rot):
        struct.pack_into('<4h', head, K.offs[2] + 8 * i, *q)
    S.scene.head = bytes(head)                          # the same bytes in both places the tools read the .buf from
    buf = S.files[S.ext['.buf']]
    S.files[S.ext['.buf']] = S.scene.head + buf[len(head):]
    # what stands beside the drive
    road0 = y0 - VAN_UP
    yaw_stop_old, yaw_stop_new = K.yaw(K.rot[K.f2r[legs['Activate_Enter'][1]]]), _heading(new.tan(lin, AXLES))
    stop_old, stop_new = old.at(s_stop), new.at(lin)
    moved = []
    def box_turn(k, by):
        m = kl_fa.node_values(sc, k)[1]
        if abs(m[4] - 1.0) > 1e-3:
            raise ValueError('%s is not turned about Y only' % sc.path[k])
        h = math.radians(math.degrees(math.atan2(m[0], m[2])) + by)
        return (math.sin(h), math.cos(h))
    def put(k, p, turn=None):
        t = struct.unpack('<3f', S.ents[k - 1].trans[:12])
        au.place(S, k, p, turn=turn)
        moved.append((sc.names[k], tuple(round(x) for x in t), tuple(round(x) for x in p)))
    for n in ('PathBlockerVan', 'CameraTrigger_InVan', 'CamPos_InVan_FocusPoint'):      # rigid with the STOPPED van
        k = N[n]
        t = struct.unpack('<3f', S.ents[k - 1].trans[:12])
        a = math.radians(yaw_stop_new - yaw_stop_old)
        dx, dz = t[0] - stop_old[0], t[2] - stop_old[2]
        p = (stop_new[0] + dx * math.cos(a) + dz * math.sin(a), t[1] - road0 + stop_new[1], stop_new[2] - dx * math.sin(a) + dz * math.cos(a))
        put(k, p, box_turn(k, yaw_stop_new - yaw_stop_old))
    for n in ('TriggerBox_RearDoors_Open', 'CameraTrigger01'):                          # ON the drive, the same distance from the stop
        k = N[n]
        t = struct.unpack('<3f', S.ents[k - 1].trans[:12])
        s, _d = old.project(t)
        s2 = lin + (s - s_stop)
        q = new.at(s2)
        put(k, (q[0], t[1] - road0 + q[1], q[2]), box_turn(k, _heading(new.tan(s2)) - _heading(old.tan(s))))
    cam = tuple(P['cam'])
    t0, t1 = [struct.unpack('<3f', S.ents[N[n] - 1].trans[:12]) for n in ('CamPos01', 'EscCamera01')]
    put(N['CamPos01'], cam)
    put(N['EscCamera01'], tuple(cam[i] + t1[i] - t0[i] for i in range(3)))
    h0 = math.radians(K.yaw(rot[K.f2r[0]]))
    old_pose = (K.pos[K.f2p[0]], K.yaw(K.rot[K.f2r[0]]))
    put(van, pos[K.f2p[0]], (math.sin(h0), math.cos(h0)))       # the node's own place = the key of frame 0
    for k in N['strays']:                                       # the reflection template, the light smears, the shadow casters
        t = struct.unpack('<3f', S.ents[k - 1].trans[:12])
        put(k, tuple(PARK[i] + t[i] for i in range(3)))
    refs = lambda k: {S.ents[j - 1].ref for j in range(k, sc.end[k])}
    gate = None
    if P.get('gate'):                                   # the frame of the leave leg at which the nose is at the gate
        f0, f1 = legs['Activate_Exit']
        along = lambda f: to(old.cum[min(K.f2p[f], cut - 1)]) - lin
        f = next((f for f in range(f0, f1 + 1) if along(f) + GATE_NOSE >= P['gate']['at']), None)
        if f is None:
            raise ValueError('kl_map_escape: the van\'s nose never reaches the gate at %d' % P['gate']['at'])
        step = (along(f) - along(f - 1)) if f > f0 else 0.0
        gate = dict(frame=f, delay=round(max(0, f - f0 - GATE_EARLY) / 25.0, 2), speed=round(step * 25 / 100.0, 1))
    top_step = max(math.dist(a, b) for a, b in zip(pos[k_stop:cut], pos[k_stop + 1:cut]))
    rep = collections.OrderedDict(
        gate=gate, speed_out=dict(mean=round(lout / 100.0 / ((legs['Activate_Exit'][1] - legs['Activate_Exit'][0]) / 25.0), 1), top=round(top_step * 25 / 100.0, 1),
                                  stock_top=round(max(math.dist(a, b) for a, b in zip(K.pos[k_stop:cut], K.pos[k_stop + 1:cut])) * 25 / 100.0, 1)),
        keys=[K.npos, K.nrot, K.frames], drive_keys=cut, stop_key=k_stop, legs={k: list(v) for k, v in legs.items()},
        old=dict(wait=[round(x) for x in K.pos[0]], stop=[round(x) for x in stop_old], length_in=round(s_stop), length_out=round(old.len - s_stop)),
        scale=[round(lin / s_stop, 2), round(lout / (old.len - s_stop), 2)],
        crash_side=[round(min(d for _s, _s2, d in where[cut:])), round(max(d for _s, _s2, d in where[cut:]))], moved=moved,
        hvk=dict(static=sorted(refs(top)), van=sorted(refs(van)), old=[list(old_pose[0]), old_pose[1]],
                 new=[list(pos[K.f2p[0]]), K.yaw(rot[K.f2r[0]])]))
    log('  kl_map_escape: %s: %d position and %d rotation keys rewritten in place (%d of them the drive, stop at key %d); drive in %d -> %d '
        '(x %.2f), away %d -> %d (x %.2f); crash pieces %d..%d to the side; %d objects moved: %s' % (
            VAN_TOP, K.npos, K.nrot, cut, k_stop, s_stop, lin, lin / s_stop, old.len - s_stop, lout, lout / (old.len - s_stop),
            *rep['crash_side'], len(moved), ', '.join(n for n, _a, _b in moved)))
    if gate:
        log('  kl_map_escape: the drive away: %.1f m/s on average, %.1f at most (stock F07: %.1f); the nose is at the gate (%d along) at frame %d '
            'of %d..%d, doing %.1f m/s: the gate goes %.2f s after the van sets off' % (
                rep['speed_out']['mean'], rep['speed_out']['top'], rep['speed_out']['stock_top'], P['gate']['at'], gate['frame'],
                *legs['Activate_Exit'], gate['speed'], gate['delay']))
    ST['van'] = rep
    return rep


def van_wire(sc, P, log=print):
    """On the JOINED scene, after kl_fa.repair: every level exit trigger calls the van (Dog Days fields 2..5 are the
    random pick, kl2 0x6c3f64; field 0 false, field 1 empty). Dead Men's car is not in the scene any more."""
    want = 'ROOT\\' + VAN_GROUP
    if len(sc.resolve(want)) != 1 or not kl_fa.has(sc, sc.resolve(want)[0], 'OnlineEscAnimatedVehicle'):
        raise ValueError('kl_map_escape: the joined scene has no %s with OnlineEscAnimatedVehicle' % VAN_GROUP)
    n = 0
    for k, i, v in kl_fa.controllers(sc, kl_fa.EXIT):
        if len(v) != 6:
            raise ValueError('%s: OnlineExitLevelTrigger with %d fields' % (sc.path[k], len(v)))
        def fn(us):
            us[0] = [(us[0][0][0], b'\0')]
            us[1] = [kl_fa._str(sc, '')]
            us[2] = [kl_fa._str(sc, want)]
            for j in (3, 4, 5):
                us[j] = [kl_fa._str(sc, '')]
        kl_fa.edit(sc, k, i, fn)
        n += 1
        log('  kl_map_escape: exit trigger %s calls %s' % (sc.path[k][5:], VAN_GROUP))
    if not n:
        raise ValueError('kl_map_escape: no OnlineExitLevelTrigger in the joined scene')
    left = [sc.path[k] for k, _i, _v in kl_fa.controllers(sc, 'OnlineEscHavokCar') if any(sc.cls(j) == 'ZHavokCar' for j in range(k, sc.end[k]))]
    if left:
        raise ValueError('kl_map_escape: Dead Men\'s escape car is still in the scene: %s' % left)
    if P.get('gate'):
        # the timer's node: a box that has no controller and that nothing sends a message to - the kept second
        # camera's place box (CCameraBox field 9 reads its place; ASSUMPTION that it sends it nothing)
        spots = [v[9] for c in P.get('cams_keep', []) for k in sc.resolve(c['camera'])
                 for v in [[kl_fa.value(sc, u) for u in units(b[1:-1])] for nm, b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'CCameraBox']]
        if not spots:
            raise ValueError('kl_map_escape: no node for the gate\'s timer (a kept camera\'s place box is used)')
        gate_wire(sc, P, ST['van']['gate']['delay'], spots[0], log)
    for c in P.get('cams_keep', []):                    # the kept second camera follows the VAN (field 0, as the van's own two)
        hit = sc.resolve(c['trigger'])
        v = [x for k, _i, x in kl_fa.controllers(sc, 'OnlineEscCamTrigger') if hit and k == hit[0]]
        if len(hit) != 1 or len(v) != 1 or v[0][1] != c['camera']:
            raise ValueError('kl_map_escape: the kept camera trigger %s does not name %s in field 1' % (c['trigger'], c['camera']))
        i = next(i for i, (nm, _b) in enumerate(sc.nodes[hit[0]]['ctrls']) if sc.p.key(nm) == 'OnlineEscCamTrigger')
        kl_fa.edit(sc, hit[0], i, lambda us: us.__setitem__(0, [kl_fa._str(sc, 'ROOT\\' + VAN_GROUP + '\\F07_EscapeVan_01')]))
        log('  kl_map_escape: camera trigger %s names the van: %s films the drive away' % (c['trigger'][5:], c['camera'][5:]))
    ST['wired'] = n
    return n


def van_hvk(hvk, rep, log=print):
    """On the joined kl_hvk.Hvk: (1) the STATIC placements of the van's subtree go (kl_escape.cut_collision): F07 has
    nine small ones of the 'V_Van_Reflection' template at its world origin (-450, 6, 3), which in F07 is outside the
    map and in M02_FA_A is the floor of the mall's atrium; (2) the key-framed placements of the van's own parts
    are put at the waiting place. ASSUMPTION for (2): the game moves a key-framed body with its entity (Retomoto's
    van was left at F07's place in the file and collided where it drove); written so that the file is right
    either way."""
    import kl_hvk, kl_escape
    h = rep['hvk']
    st = {kl_hvk.ref(i) for s in hvk.shapes if s.type == kl_hvk.STATIC for i in s.inst} & set(h['static'])
    if st:
        kl_escape.cut_collision(hvk, st, log)
    (p0, y0), (p1, y1) = h['old'], h['new']
    a = math.radians(y1 - y0)
    c, s_ = math.cos(a), math.sin(a)
    R = ((c, 0.0, s_), (0.0, 1.0, 0.0), (-s_, 0.0, c))
    n, van = 0, set(h['van'])
    for s in hvk.shapes:
        if s.type == kl_hvk.STATIC:
            continue
        for j, inst in enumerate(s.inst):
            if kl_hvk.ref(inst) not in van:
                continue
            p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
            d = [100.0 * p[i] - p0[i] for i in range(3)]
            q = [(p1[i] + sum(R[i][b] * d[b] for b in range(3))) / 100.0 for i in range(3)]
            m2 = [sum(R[i][k] * m[3 * k + b] for k in range(3)) for i in range(3) for b in range(3)]
            s.inst[j] = struct.pack('<3f9f', *q, *m2) + inst[48:]
            n += 1
    log('  kl_map_escape: .HVK: %d static placements of the van\'s subtree cut, %d key-framed placements of the van put at its waiting place' % (len(st), n))
    ST['hvk'] = (len(st), n)
    return hvk


def van_build(tag, src_root, out_root, log=print):
    """One map: plan on <src_root>/<tag> (a finished build with Dead Men's car), then the map built again as
    kl_maps.ready_one builds it, with the van (module comment), into <out_root>/_graft/<tag>, then kl_map_tune.build
    -> <out_root>/<tag>. -> report (also <out_root>/<tag>/van.json, van.txt)."""
    import kl_graft, kl_hvk, kl_map_tune
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    src, graft, out = os.path.join(src_root, tag), os.path.join(out_root, '_graft'), os.path.join(out_root, tag)
    if 'kl_portbackup' in os.path.abspath(out).lower() or 'dog days' in os.path.abspath(out).lower():
        raise ValueError('kl_map_escape writes build folders only, never the game\'s')
    P = van_plan(src, say)
    if P['faults']:
        raise ValueError('%s: no van: %s' % (tag, '; '.join(P['faults'])))
    entry = next(r for r in kl_maps.READY if r[0] == tag)
    saved = (kl_graft.Level, kl_fa.host_keep, kl_fa.repair, kl_hvk.join, dict(entry[3]))
    ST.clear()

    class VanLevel(saved[0]):
        def __init__(self, name):
            super().__init__(name)
            if name == VAN_HOST and 'van' not in ST:
                van_prepare(self, P, say)
    def keep(S):
        return list(saved[1](S)) + [n for n in VAN_KEEP if n not in saved[1](S)]
    def repair(sc, kept=(), log=say):
        r = saved[2](sc, kept, log)
        van_wire(sc, P, say)
        return r
    def join(*a, **kw):
        return van_hvk(saved[3](*a, **kw), ST['van'], say)
    kl_graft.Level, kl_fa.host_keep, kl_fa.repair, kl_hvk.join = VanLevel, keep, repair, join
    entry[3]['m_drop'] = tuple(entry[3].get('m_drop', ())) + tuple(P['drop'])
    try:
        a = kl_maps.ready_one(graft, tag, log=say)
    finally:
        kl_graft.Level, kl_fa.host_keep, kl_fa.repair, kl_hvk.join = saved[:4]
        entry[3].clear(); entry[3].update(saved[4])
    rep = collections.OrderedDict(tag=tag, plan=P, van=ST.get('van'), wired=ST.get('wired'), hvk=ST.get('hvk'), ready_bad=a.get('bad'))
    if a.get('bad') or a.get('error') or not all(k in ST for k in ('van', 'wired', 'hvk')):
        raise ValueError('%s: the build with the van is not ready: %s' % (tag, a.get('error') or a.get('bad') or 'a step of the van did not run: %s' % sorted(ST)))
    t = kl_map_tune.build(os.path.join(graft, tag), out, kl_map_tune.options(()), say)
    rep['tune_ok'], rep['tune_failed'] = t['ok'], t.get('failed')
    L = Level(out)
    L.G = Ground(L)
    rep['check'] = van_check(L, say, P)
    with open(os.path.join(out, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(out, 'van.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    say('RESULT %s: van %s; kl_map_tune %s; van check: %d fault(s)' % (tag, 'built', 'PASS' if t['ok'] else 'NOT PASS (%s)' % t.get('failed'), len(rep['check']['faults'])))
    return rep


def van_check(L, log=print, P=None):
    """The key-framed van of a built level, from the written files alone -> {'faults': [...], ...}. Only for a level
    with ONE OnlineEscAnimatedVehicle (this module's builds; Retomoto's three are kl_fa_van.check's)."""
    import kl_graft
    sc, G = L.sc, (L.G if hasattr(L, 'G') else Ground(L))
    L.G = G
    out = collections.OrderedDict(faults=[], notes=[])
    bad = out['faults'].append
    vans = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle')
    if len(vans) != 1:
        out['notes'].append('%d OnlineEscAnimatedVehicle: not a build of this module, nothing tested' % len(vans))
        return out
    grp = vans[0][0]
    top = sc.top[grp]
    log('van check: %s' % L.zip)
    N = _van_nodes(sc, top)
    van = N['V_Van_00']
    # 1. who is called, and what of Dead Men's is left
    for k, _i, v in kl_fa.controllers(sc, kl_fa.EXIT):
        named = [x for x in v[1:6] if x]
        if v[0] or named != [sc.path[grp]]:
            bad('exit trigger %s names %s (field 0 = %s): not the van alone' % (sc.path[k][5:], named, v[0]))
    for k, _i, _v in kl_fa.controllers(sc, 'OnlineEscHavokCar'):
        if any(sc.cls(j) == 'ZHavokCar' for j in range(k, sc.end[k])):
            bad('Dead Men\'s escape car %s is still in the level' % sc.path[k][5:])
    acts = [k for k, _i, v in kl_fa.controllers(sc, 'PlayerAction') if 'EnterVehicle' in v]
    if acts != [N['BoardingTrigger']]:
        bad('boarding actions: %s (the van\'s own is wanted, alone)' % [sc.path[k][5:] for k in acts])
    if vans[0][2][0] != sc.path[N['BoardingTrigger']] or vans[0][2][12] != sc.path[van]:
        bad('OnlineEscAnimatedVehicle does not name its own boarding box and van')
    # a camera trigger outside the van's archive is the map's kept second camera (van_plan 'cams_keep'): it must name
    # the van as the van's own two do, and its box must hold a stretch of the drive away (tested below, with the keys)
    cams = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineEscCamTrigger') if not (top <= k < sc.end[top])]
    for k, v in cams:
        if v[0] != sc.path[N['F07_EscapeVan_01']]:
            bad('escape camera trigger outside the van that does not name the van in field 0: %s' % sc.path[k][5:])
    if not any('FAEscCameraLAST' in str(v) for _k, _i, v in kl_fa.controllers(sc, 'ZSetZDefine')):
        out['notes'].append('no define FAEscCameraLAST in the level (the box that releases the escape camera)')
    # 2. the keys
    ends = sorted({o for e in L.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(L.scene.head)})
    K = VanKeys(L.scene.head, L.ents[van - 1].raw, ends, kl_graft.keys_tracks)
    for k in (grp, N['F07_Escape_Vehicle_01'], top):
        if max(abs(x) for x in L.place(k)) > 1e-3:
            bad('%s does not stand at the origin: the keys are not world places' % sc.path[k][5:])
    legs = _leg_frames(sc, N['F07_Escape_Vehicle_01'])
    cut = K.drive()
    D = Poly(K.pos[:cut])
    k_stop = K.f2p[legs['Activate_Enter'][1]]
    lin = D.cum[k_stop]
    own = {L.ents[j - 1].ref for j in range(top, sc.end[top])}
    worst_y, steps, back = 0.0, 0.0, 0
    for i, p in enumerate(K.pos[:cut]):
        g = G.under(p[0], p[1] + 20.0, p[2])
        if g is None:
            bad('drive key %d at (%d, %d, %d): no ground under it' % (i, *p))
            continue
        worst_y = max(worst_y, abs(p[1] - VAN_UP - g[0]))
        if i:
            steps = max(steps, math.dist(p, K.pos[i - 1]))
    if worst_y > 6.0:
        bad('a drive key is %.1f off the height of the van on the ground (%.0f over it is wanted)' % (worst_y, VAN_UP))
    road = Poly([(p[0], p[1] - VAN_UP, p[2]) for p in K.pos[:cut]])
    # a gate in the lane is no fault when - and only when - the level's own wiring takes it away before the van's
    # nose is there (gate_read: the chain from the van's leave message, read from the files) and not more than a
    # second before; everything else in the lane is a fault as before
    gate = gate_read(L, top)
    skip = own
    if gate:
        out['faults'] += gate['faults']
        hit = sorted(lane(L, G, road, -VAN_TAIL, road.len + VAN_NOSE, only=gate['refs']))
        f0, f1 = legs['Activate_Exit']
        if not hit:
            bad('gate: the wiring switches %s, which is not in the van\'s lane' % gate['names'])
        elif hit[0][0] <= lin + 200:
            bad('gate: %s is in the lane %d along the drive, not after the stop (%d): it is closed when the van comes in' % (hit[0][2], hit[0][0], lin))
        else:
            fr = next((f for f in range(f0, f1 + 1) if D.cum[min(K.f2p[f], cut - 1)] + GATE_NOSE >= hit[0][0]), None)
            fire = f0 + gate['delay'] * 25.0
            if fr is None or D.len < hit[-1][0] + GATE_PAST:
                bad('gate: the drive ends at %d, the gate is at %d..%d: the van ends in it' % (D.len, hit[0][0], hit[-1][0]))
            elif fire > fr or fire < fr - 25:
                bad('gate: the nose is at the gate at frame %d, the gate goes at frame %.0f (wanted: 0..25 frames before)' % (fr, fire))
            else:
                skip = own | gate['refs']
                out['gate'] = dict(chain=gate['chain'], at=round(hit[0][0] - lin), frame=fr, fires=round(fire, 1), delay=gate['delay'], names=sorted(set(gate['names'])),
                                   speed=round((D.cum[K.f2p[fr]] - D.cum[K.f2p[fr - 1]]) * 25 / 100.0, 1))
    ob = _first(lane(L, G, road, -VAN_TAIL, road.len + VAN_NOSE, skip))
    for nm, (a, b, cnt, what) in ob.items():
        bad('in the van\'s lane: %s (%s) %d..%d along the drive' % (nm, what, a, b))
    for k, v in cams:                                   # the kept second camera's box on the drive away
        ins = [D.cum[i] - lin for i, p in enumerate(K.pos[:cut]) if D.cum[i] > lin and
               all(abs(sum(L.frame(k)[0][a][b] * ((p[a] + (100.0 if a == 1 else 0.0)) - L.frame(k)[1][a]) for a in range(3))) <= L.values(k)['ZBoxPrimitive[%d]' % b] for b in range(3))]
        if not ins or min(ins) < 1500.0:
            bad('the box of camera trigger %s does not hold a stretch of the drive away after the van\'s own camera has come on' % sc.path[k][5:])
        else:
            out.setdefault('cameras_kept', []).append([sc.path[k][5:], round(min(ins)), round(max(ins))])
    # the nose against the chord of the drive, frame by frame. A rotation key serves several frames where F07's own
    # drive was straight (19 keys of the drive are held 3..6 frames); between two keys the heading is taken to run
    # linearly (ASSUMPTION, from stock F07: in its bends a held key and its successor both sit on the tangent at
    # their OWN frames, and the tangent of the frames between them is the straight run from one to the other -
    # `van-keys` prints the table). 'held' = the same measure if the engine did not interpolate.
    firstf = {}
    for f in range(K.frames - 1, -1, -1):
        firstf[K.f2r[f]] = f
    yaw_off = yaw_held = 0.0
    for f in range(K.frames):
        kp, r = K.f2p[f], K.f2r[f]
        if kp < cut and 2.0 < D.cum[kp] < D.len - 2.0:
            want, y = _heading(D.tan(D.cum[kp], AXLES)), K.yaw(K.rot[r])
            yaw_held = max(yaw_held, abs(_wrap(y - want)))
            f1 = firstf.get(r + 1)
            if f1 is not None and f1 > f > firstf[r]:
                y += _wrap(K.yaw(K.rot[r + 1]) - y) * (f - firstf[r]) / (f1 - firstf[r])
            yaw_off = max(yaw_off, abs(_wrap(y - want)))
    out['nose_held'] = round(yaw_held, 1)
    if yaw_off > REL_MAX:
        bad('the van\'s nose is up to %.0f degrees off the drive\'s tangent' % yaw_off)
    crash = [K.pos[i] for i in range(cut, K.npos)]
    side = max((abs(D.project(p)[1]) for p in crash), default=0.0)
    if side > SIDE + 15.0:
        bad('a crash piece leaves the drive by %.0f' % side)
    low = [p for p in crash if (G.under(p[0], p[1] + 40.0, p[2]) or (p[1],))[0] > p[1] + 25.0]
    if low:
        bad('%d crash keys are more than 25 under the ground' % len(low))
    wait, stop, end = K.pos[K.f2p[0]], K.pos[k_stop], K.pos[cut - 1]
    out.update(keys=[K.npos, K.nrot, K.frames], drive_keys=cut, wait=[round(x) for x in wait], stop=[round(x) for x in stop], end=[round(x) for x in end],
               length_in=round(lin), length_out=round(D.len - lin), largest_step=round(steps), height_off=round(worst_y, 1), nose_off=round(yaw_off, 1),
               crash_side=round(side), seconds=[round((legs['Activate_Enter'][1] - legs['Activate_Enter'][0]) / 25.0, 2),
                                                round((legs['Activate_Exit'][1] - legs['Activate_Exit'][0]) / 25.0, 2)])
    if math.dist(L.place(van), wait) > 1.0:
        bad('the van\'s node stands at (%d, %d, %d), its first key is (%d, %d, %d)' % (*L.place(van), *wait))
    # 3. what stands at the stop
    hs = math.radians(K.yaw(K.rot[K.f2r[legs['Activate_Enter'][1]]]))
    board = (stop[0] - BOARD_BACK * math.sin(hs), stop[1], stop[2] - BOARD_BACK * math.cos(hs))
    out['board'] = [round(x) for x in board]
    def inside(k, p):
        v, (R, T) = L.values(k), L.frame(k)
        return all(abs(sum(R[a][b] * (p[a] - T[a]) for a in range(3))) <= v['ZBoxPrimitive[%d]' % b] for b in range(3))
    if math.hypot(L.place(N['PathBlockerVan'])[0] - stop[0], L.place(N['PathBlockerVan'])[2] - stop[2]) > 30.0:
        bad('PathBlockerVan is %d from the stop' % math.dist(L.place(N['PathBlockerVan']), stop))
    if not inside(N['CameraTrigger_InVan'], stop):
        bad('the stop is not inside CameraTrigger_InVan')
    after = D.at(lin + 850.0)
    if not inside(N['CameraTrigger01'], after):
        bad('the drive 8.5 m after the stop is not inside CameraTrigger01')
    doors = L.place(N['TriggerBox_RearDoors_Open'])
    if abs(D.project(doors)[1]) > 30.0 or not 0 < D.project(doors)[0] < lin:
        bad('TriggerBox_RearDoors_Open is not on the drive in')
    # 4. the camera
    for c in cameras(L, G, [tuple(stop)]):
        if c['fault']:
            bad('camera %s: %s' % (c['name'], c['fault']))
        if c['eye']:
            d = dict(eye=[round(x) for x in c['eye']], over=round(c['over']) if c.get('over') is not None else None,
                     far=round(c.get('far', 0)), sight=c.get('sight'))
            if top <= c['node'] < sc.end[top]:
                out['camera'] = d
            else:
                out.setdefault('cameras_more', []).append(dict(d, name=c['name'], mode=c['mode']))
                if c['mode'] != FROM_POS:
                    bad('kept camera %s has mode %s (only %s puts the eye at its place)' % (c['name'], c['mode'], FROM_POS))
    # 5. the collision file
    stat = sum(1 for s in L.hvk.shapes if s.type == kl_hvk.STATIC for i in s.inst if kl_hvk.ref(i) in own)
    if stat:
        bad('%d static collision placements belong to the van\'s subtree (they lie at F07\'s places)' % stat)
    node = {e.ref: i + 1 for i, e in enumerate(L.ents)}
    far, nk = 0.0, 0
    for s in L.hvk.shapes:
        if s.type != kl_hvk.STATIC:
            for i in s.inst:
                if kl_hvk.ref(i) in own:
                    p = struct.unpack_from('<3f', i, 0)
                    far = max(far, math.dist([100 * x for x in p], L.place(node[kl_hvk.ref(i)])))
                    nk += 1
    out['keyframed'] = [nk, round(far, 1)]
    if far > 30.0:
        bad('a key-framed collision placement of the van is %.0f from its entity' % far)
    # the file's size and who owns it (re/play_fixes_review.md D2: the filler copies kl_hvk.remap writes where F07's
    # map was were 2,087 whole copies of a 7 KB mall wall on M02 - 15.7 MB - and nothing here said so)
    import kl_escape
    sh = kl_escape.shares(L.hvk, L.name, 3)
    out['hvk'] = dict(bytes=L.sizes.get('.hvk'), static=L.hvk.static_count(), largest=[list(x) for x in sh])
    if L.sizes.get('.hvk', 0) > HVK_MAX:
        bad('the .HVK is %d bytes: over %d, the largest that has loaded in the game (Retomoto; the largest stock file is %d)' % (
            L.sizes['.hvk'], HVK_MAX, HVK_STOCK))
    if sh and sh[0][0] > HVK_SHARE:
        bad('one entity owns %d bytes of the .HVK in %d placements (%s): filler copies that were not packed' % sh[0])
    # 6. the loose pieces
    loose = [sc.names[k] for k in N['strays'] if L.place(k)[1] > PARK[1] / 2]
    if loose:
        bad('pieces of the van\'s archive lie loose in the map: %s' % loose)
    bounds = level_bounds(L)
    out['bounds'] = _crossings(bounds, K.pos[:cut], [c - lin for c in D.cum])
    if P is not None:
        for k in ('wait', 'stop', 'end'):
            if math.dist(P[k], {'wait': wait, 'stop': stop, 'end': end}[k]) > 25.0:
                bad('the %s place (%d, %d, %d) is not the plan\'s (%d, %d, %d)' % (k, *{'wait': wait, 'stop': stop, 'end': end}[k], *P[k]))
    log('  van %s: %d position / %d rotation keys, %d frames; waits (%d, %d, %d) -> %.0f m in %.2f s -> stops (%d, %d, %d) -> %.0f m in %.2f s '
        '-> (%d, %d, %d)' % (sc.path[grp][5:], K.npos, K.nrot, K.frames, *wait, lin / 100, out['seconds'][0], *stop, (D.len - lin) / 100,
                            out['seconds'][1], *end))
    log('  keys %.1f off the road height at most, largest step %d, nose up to %.1f degrees off the tangent (%.1f if a key is held, not '
        'interpolated), crash pieces up to %d to the side; lane (5 rays, every %d, %d before and %d beyond): %s' % (
            worst_y, steps, yaw_off, yaw_held, side, LANE_STEP, VAN_TAIL, VAN_NOSE, 'clear' if not ob else 'NOT CLEAR'))
    log('  boarding box at the stop: (%d, %d, %d); key-framed placements %d, at most %.1f from their entities; camera: %s' % (
        *board, nk, far, out.get('camera')))
    log('  .HVK %d bytes, %d static placements; the largest shares of one entity: %s' % (
        out['hvk']['bytes'], out['hvk']['static'], '; '.join('%s %d bytes in %d placements' % (nm, b, c) for b, c, nm in sh)))
    for e in out['bounds']:
        log('  the drive passes the level bound %s from %d to %d (0 = the stop)' % tuple(e))
    if out.get('gate'):
        g = out['gate']
        log('  gate %s, %d along the drive away: the van\'s leave message -> %.2f s -> off / thrown at frame %.0f; the nose is there at frame %d '
            'doing %.1f m/s' % (', '.join(g['names']), g['at'], g['delay'], g['fires'], g['frame'], g['speed']))
        log('  gate wiring, no node twice: ' + ' -> '.join(g['chain']))
    for c, m in zip(out.get('cameras_kept', []), out.get('cameras_more', [])):
        log('  second camera: %s, eye (%d, %d, %d) %d over the ground; its box %s holds the drive away from %d to %d' % (
            m['name'], *m['eye'], m['over'], c[0], c[1], c[2]))
    for x in out['notes']:
        log('  note: ' + x)
    for x in out['faults']:
        log('  FAULT ' + x)
    log('  %d fault(s)' % len(out['faults']))
    return out


def van_keys(level='F07', log=print):
    """The evidence for the module comment: the key tables of stock F07's first van."""
    import kl_graft
    import kl_fa_author as au
    S = kl_graft.Level(level)
    sc = S.prp
    N = _van_nodes(sc, au.node_of(sc, VAN_TOP))
    ends = sorted({o for e in S.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(S.scene.head)})
    K = VanKeys(S.scene.head, S.ents[N['V_Van_00'] - 1].raw, ends, kl_graft.keys_tracks)
    cut = K.drive()
    D = Poly(K.pos[:cut])
    legs = _leg_frames(sc, N['F07_Escape_Vehicle_01'])
    log('%s %s: %d frames, %d position keys (%d the drive), %d rotation keys; table offsets %s; legs %s' % (
        level, VAN_TOP, K.frames, K.npos, cut, K.nrot, list(K.offs), legs))
    k2f, r2f = K.bits(K.offs[4], 40), K.bits(K.offs[1], 40)
    log('  table 4 (position key -> frame) begins %s; table 1 (rotation key -> frame) begins %s' % (k2f[:12], r2f[:12]))
    for f in (0, 49, 50, 100, 150, 200, 230, 250, 273, 300, 400, 485, 500, 562, 600, 632, 650, 709, 750, 795):
        kp, kr = K.f2p[f], K.f2r[f]
        tn = '%6.1f' % _heading(D.tan(D.cum[kp])) if kp < cut else '     -'
        log('  frame %3d: position key %3d (%6d %5d %6d)  rotation key %3d %-28s yaw %6.1f  tangent of the drive %s' % (
            f, kp, *K.pos[kp], kr, K.rot[kr], K.yaw(K.rot[kr]), tn))
    firstf = {}
    for f in range(K.frames - 1, -1, -1):
        firstf[K.f2r[f]] = f
    log('  rotation keys of the drive that serve 3 frames or more: key, first frame, frames; its yaw -> the next key\'s; the drive\'s tangent at '
        'its first frame, the middle one, the next key\'s frame; the straight run from key to key at the middle frame')
    worst = 0.0
    for r in range(1, K.nrot - 1):
        f0, f1 = firstf.get(r), firstf.get(r + 1)
        if f0 is None or f1 is None or f1 - f0 < 3 or not (legs['Activate_Enter'][0] <= f0 < legs['Activate_Enter'][1] - 2 or
                                                         legs['Activate_Exit'][0] <= f0 < legs['Activate_Exit'][1]):
            continue
        fm = (f0 + f1) // 2
        tn = [_heading(D.tan(D.cum[K.f2p[f]], AXLES)) for f in (f0, fm, f1)]
        y0, y1 = K.yaw(K.rot[r]), K.yaw(K.rot[r + 1])
        mid = y0 + _wrap(y1 - y0) * (fm - f0) / (f1 - f0)
        lag = (_wrap(y0 - tn[0]) + _wrap(y1 - tn[2])) / 2
        worst = max(worst, abs(_wrap(mid - tn[1] - lag)))
        log('    key %3d frame %3d x%d  yaw %6.1f -> %6.1f   tangent %6.1f %6.1f %6.1f   run at the middle %6.1f (tangent + the two keys\' own lag %+.1f = %6.1f)' % (
            r, f0, f1 - f0, y0, y1, *tn, mid, lag, tn[1] + lag))
    log('  -> the straight run between two keys is the tangent of the frames between them within %.1f degrees' % worst)
    ks = K.f2p[legs['Activate_Enter'][1]]
    log('  the drive in: %d units to key %d; away: %d; non-yaw parts of the rotation keys up to %d / %d of 32767' % (
        D.cum[ks], ks, D.len - D.cum[ks], max(abs(q[0]) for q in K.rot), max(abs(q[2]) for q in K.rot)))


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    heights = '--level' in sys.argv
    if len(a) == 2 and a[0] == 'van-plan':
        P = van_plan(a[1])
        sys.exit(1 if P['faults'] else 0)
    elif a[:1] == ['van-keys']:
        van_keys(*a[1:2])
        return
    elif len(a) == 2 and a[0] == 'van-check':
        sys.exit(1 if van_check(Level(a[1]))['faults'] else 0)
    elif len(a) >= 3 and a[0] == 'van':
        bad = 0
        for tag in a[3:] or VAN_TAGS:
            print('=' * 20 + ' ' + tag, flush=True)
            try:
                r = van_build(tag, a[1], a[2])
                bad += bool(r['check']['faults']) or not r['tune_ok']
            except Exception:
                import traceback
                traceback.print_exc()
                bad += 1
        sys.exit(1 if bad else 0)
    if len(a) == 2 and a[0] == 'check':
        L = Level(a[1])
        rep = check(L)
        rep['faults'] += van_check(L)['faults']
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) == 3 and a[0] == 'fix':
        rep = repair(a[1], a[2], heights)
        sys.exit(1 if rep['after']['faults'] else 0)
    elif len(a) >= 3 and a[0] == 'all':
        bad = 0
        for tag in a[3:] or sorted(d for d in os.listdir(a[1]) if os.path.isfile(os.path.join(a[1], d, SLOT + '_Main.zip'))):
            bad += len(repair(os.path.join(a[1], tag), os.path.join(a[2], tag), heights)['after']['faults'])
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_map_escape
    kl_map_escape.main()
