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
    rep = {'vehicles': [], 'cameras': [], 'faults': []}
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
        rep['cameras'].append({k: c.get(k) for k in ('name', 'trigger', 'mode', 'own', 'target', 'target_name', 'eye', 'ground',
                                                      'over', 'ground_name', 'sight', 'fault')})
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


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    heights = '--level' in sys.argv
    if len(a) == 2 and a[0] == 'check':
        rep = check(Level(a[1]))
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
