#!/usr/bin/env python3
"""
COVER FOR THE AI HEISTERS WHERE THE MAP HAS NONE: a step on a FINISHED, NON-dynamic bots build, run BEFORE
tools/kl_fa_bots_dyn.py. It asks the dynamic step's own plan where a bot wanted to hold and found no cover box,
looks for REAL solid static collision near each such place, and puts a cover box on it - a clone of one of the
build's own cover boxes. Where nothing solid stands, nothing is added and the place is reported as a gap.
OFFLINE: nothing here installs anything or starts the game. Build notes: re/bots_dyn_build.md 12 and 13 (corners, form b only).

    python kl_fa_cover.py plan  <bots build folder> [options]         the boxes and the gaps, nothing written
    python kl_fa_cover.py build <bots build folder> <out folder> [options]
                                                                      the build with the boxes + cover.json / cover.txt;
                                                                      check and diff are run; exit 1 on a FAIL
    python kl_fa_cover.py check <folder>                              the boxes of a built folder (also of the dynamic
                                                                      build made from it); exit 1 on a FAIL
    python kl_fa_cover.py diff  <bots build folder> <out folder>      what the step changed; exit 1 if anything but the
                                                                      new group differs
    python kl_fa_cover.py all   <work>\\build [M01 ...]                z_gate\\M01, z_final\\M02 M03 M06, rt_full6\\
                                                                      retomoto_full -> z_cover2\\_pre\\<map> (this step),
                                                                      then kl_fa_bots_dyn.build (random routes) on it
                                                                      -> z_cover2\\<map>
    options
      --models b|ab   which of the build's cover boxes may be cloned (default b: the exact form; ab is the first run's,
                      kept for M01, whose plain boxes are all car-sized - 13.3).
                      b: boxes with flags 0x200 whose model root names no .oct record and that no room tree lists -
                         the form of stock F05's 203 and F08's 147 boxes and of 20..215 boxes of each of our builds
                         (re/bots_dyn_build.md 12.2). The clone is the same: in no tree.
                      a: UNPROVEN. boxes with flags 0x302, whose model root names a collision record and that tree 0 of their
                         ROOM lists (most stock boxes; 118 of M01's 139). The clone gets the same flags and model and
                         is listed in tree 0 of the ROOT's room set with its box in the world - where every level
                         lists the 134+ objects with a collision record that have no room above them (flags 0x102 /
                         0x182). ASSUMPTION: a cover box may be listed there instead of in a ZROOM's tree; no stock
                         cover box is (the stock ones without a room above them are in no tree at all)
      --near N        an object counts for a place when it is within N of it (default 600)
      --corner-near N a corner counts for a place when it is within N of it (default 800)
      --no-corners    objects only (the first run)
      --no-borrow     no box with the 100 cube of F07's camera objects (forms())
      --rounds N      plan / add boxes / plan again, at most N times (default 4)

WHAT A COVER IS (re/bots_dynamic.md 3.1, read in kl2.exe, nothing of it tried in the game): CFFCoverList slot 13
  (0x6d6a80) makes a cover of every ZSTDOBJ whose NAME matches *coverbox* (at most 5,000); *coverboxh* -> high,
  *coverboxm* / *coverboxl* -> low. 0x603830 builds the cover from the object's box, four sides. There is no list
  and no count in the level to bring up to date: the FFCoverList controller has no fields and its ZLIST is empty in
  every stock level; the run-time list is made at the load. The PLAYER's cover uses the same boxes.
  WHAT 0x603830 TAKES FROM THE ENTITY (read 2026-10-11, re/bots_dyn_build.md 13.2): its 128-byte slot ([obj + 4])
  and nothing else of its geometry - matrix +0x00 (no cover when [+0x10], the Y of its up axis, is under 0.717),
  place +0x24, BOX MIDDLE +0x30 and BOX HALF SIZE +0x40 (three floats each, the object's own frame), the parent
  chain +0x50; four corners = middle +- half size on the box's FLOOR, each through 0x7b3020 (matrix, place, parents)
  into the world; the cover's height = half height + 50. Not the mesh, not the collision record, not a room tree:
  FORM B IS A WHOLE COVER. The slot's box is not in the level files (the loader zeroes it, 0x8adb19..2b); for a
  ZSTDOBJ the only thing that can fill it is its model (the routine that does was NOT found: ASSUMPTION that it is
  the model root's box, chunk + 0x20). Every cover box of every stock level and of our builds has an unscaled
  matrix and a model with ONE HIDDEN mesh (draw mode 0x800000), so a box's SIZE is its model's: a new box can only
  have a size a box model of the build has. No model is added (the .prm must not grow).

WHAT IS ADDED
  One top-level ZGROUP 'KL_Cover!' (form: the build's first plain top-level group at the origin, e.g.
  Locations/<map>/..._Audio.zip; listed in the root's group tree with the box of its children, as that group is)
  and below it one ZSTDOBJ a box, 'CoverBoxH_KL_nn' / 'CoverBoxM_KL_nn': the properties, flags, pool group and model
  number of an existing cover box of the same build; only place and rotation are its own. Pool category 1 as every
  ZSTDOBJ; kl_scene.write() makes the cluster table, the type table and the list pool anew. Not listed in a room
  tree (the form the source box has). No controller (the build's boxes have none: every side on AUTO).

WHERE (all of it GUESS unless a stock number is named)
  - a place = a route place at which kl_fa_bots_dyn.plan asked for a hold and found none (its find_holds says so);
  - the static shapes of the .HVK (type 1; key-framed and rigid ones move) are cut by horizontal planes 45 / 75 /
    110 / 140 / 175 / 205 over the place's ground. What one ENTITY has in the 75 plane, joined up, is an 'object';
    its box is the smallest rectangle round that outline. It counts when it is 40..700 long, at least 10 thick
    (a single plane - a pane, a fence - is not), is there at 45 too (not a table top), and its name does not say
    glass / window / fence / rail / wire / bush / hedge / door / gate / camera / ColiObj (NOT_COVER);
    longer = a wall or a building: its CORNERS (below). An object over 400 long gets its box at the END nearest
    the place, and only when that end is free (no other collision within 80 beyond it: a wall piece that goes on in
    the next piece has no corner there);
  - CORNERS (corners(), consider_corner(); tried for a place that got no object box in the round): the 75 plane's
    cut segments of all entities (but the NOT_COVER names) joined into straight faces of at least 100, each with the
    side its triangles face. 'L' = two faces end together at 60..120 degrees and face away from one another (a
    building corner, a wide pillar); 'end' = two faces back to back 10..100 apart end side by side with nothing
    beyond (a wall end, a jamb). It must be there 45 over the floor too; there at 175 = a HIGH box, else LOW. The
    box sits as stock's do (measured on F05 and F08, 13.1): in the solid, a footprint corner ON the corner, along
    the face, no deeper than the solid behind the face (a wall end: its thickness; else up to the first mesh behind
    it) + 25. WHICH face: the one hidden from where the bot walks TOWARD on that leg (its normal against the way,
    under -0.3) with mesh before it and a hold place on that side - 'the threat is ahead on the bot's way' is a
    GUESS. Within 800;
  - 'the ground' is the collision's own floor under the place, not the mesh's height (Retomoto's street mesh lies
    40 under the road);
  - HIGH when the same entity is in the 175 plane over 60 % of the outline, else LOW (so 'low' is 75 .. 175 high:
    Dead Men's own car boxes are 110..150 high);
  - no box when a cover box is there already, inside a NoCoverBox, in a level exit box, within kl_fa_bots.LANE_CLEAR
    of the escape vehicle's road (Retomoto: in the van's lane), or when kl_fa_bots_dyn.hold_ok finds no place on
    the mesh 70..230 from it that the bot can walk to from the place that asked;
  - the box model: the largest of the build's box models that does not stick out of the object's rectangle by more
    than OVER on either axis; the box lies in the rectangle, pushed to the end / side NEAREST THE PLACE THAT ASKED =
    the side that faces back along the bot's way. Where enemies come from on that leg is not known to this step:
    which side of an object that is longer than the box gets it is a GUESS (the engine picks the side of the box).
"""
import collections, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_hvk, kl_scene
import kl_fa_bots as F
import kl_fa_bots_dyn as D
import kl_octree as O
import kl_prpjoin as J

GROUP = 'KL_Cover!'
TAG = '_KL_'                    # in the name of every box of this step: CoverBoxH_KL_01, CoverBoxM_KL_01
NEAR = 600.0                    # an object counts for a place when it is this near (the job: 'within ~6 m')
GATHER = 1400.0                 # collision is looked at this far round a place (an object up to LONG must fit in)
CELL = 10.0                     # raster of an outline
PLANES = (45.0, 75.0, 110.0, 140.0, 175.0, 205.0)
BASE, LOW, HIGH = 75.0, 45.0, 175.0
HIGH_SHARE = 0.6                # of the outline at BASE that is there at HIGH too: a high cover
LOW_SHARE = 0.5                 # ... at LOW: stands on the ground (not a table top, an awning)
LONG, SLIM, THIN = 700.0, 40.0, 10.0
OVER = 40.0                     # a box may stick out of its object by this on an axis (Dead Men's 220-wide boxes on 190-wide cars)
MODEL_MAX = 320.0               # no box model with a longer footprint (a truck's box on a planter)
MODEL_OFF = 80.0                # ... or whose box middle is further than this from its origin (kl_fa_bots_dyn measures from the origin)
LOW_Y, HIGH_Y = (95.0, 149.5), (149.5, 320.0)       # model heights used for a low / a high box
APART = 150.0                   # two cover boxes (middles) are at least this far apart
ROUNDS = 4
NOT_COVER = ('glass', 'window', 'fence', 'rail', 'wire', 'bush', 'hedge', 'leaves', 'door', 'gate', 'curtain', 'awning', 'cable',
             'water', 'trigger', 'stair', 'bicy', 'metal_barrier', 'collapse', 'remains', 'lamp',
             # collision that is not the thing one sees: the camera's, the players' own blockers ('ColiObj_World',
             # 'Coli_HeroOnly_01', '...!OnlyHero'): a blocker may stand where nothing is drawn
             'camera', 'coli', 'heroonly', 'onlyhero')
TIER_B = 0.6                    # GUESS: see fit()
BORROW_MAX = 130.0              # forms(): 'a small low model' has no longer footprint side
ENDS = 400.0                    # an object longer than this gets its box at an END (a corner), and only at a free one
END_GAP = 80.0                  # ... free = no other collision in the BASE plane this far beyond the end
# ---- wall corners (all GUESS but where a stock number is named: re/bots_dyn_build.md 13)
CORNER_NEAR = 800.0             # a corner counts for a place when it is this near (the job: 'within ~8 m')
WALL_RUN = 100.0                # a straight face of at least this length on each side of a corner (the job: 1 m)
RUN_GAP = 25.0                  # pieces of one face are joined over gaps up to this
JOIN = 25.0                     # two faces meet when their ends are this near
WALL_THICK = (10.0, 100.0)      # a wall end: two faces back to back this far apart (thicker: two 'L' corners)
CORNER_OVER = 25.0              # a corner box may stick out of the solid behind its face by this
CORNER_MIN = 60.0               # ... and is at least this long along its face
CORNER_AIM = 100.0             # the footprint a corner box should have when the build has the choice (stock: 13.1)
MAP_TOPS = ('Locations/', 'CloneGroup_Locations')
OUT = 'z_cover2'                # `all` writes <work>\\build\\z_cover2 (z_cover = the first run: form a boxes, no corners)
OWNER = (('z_gate', 'M01'), ('z_final', 'M02'), ('z_final', 'M03'), ('z_final', 'M06'), ('rt_full6', 'retomoto_full'))
DEFAULTS = {'models': 'b', 'near': NEAR, 'rounds': ROUNDS, 'corners': True, 'corner_near': CORNER_NEAR, 'borrow': True}
HELD = 'has a cover box (this step\'s or the map\'s) that another bot holds or that was refused'


# ------------------------------------------------------------------ the map's static collision
class Solid:
    """Triangles of the static, non-convex shapes of the .HVK whose entity stands below a map subtree, in world
    units, with the entity (REF id) of each (placements as kl_map_escape.Ground reads them)."""
    GRID = 400.0

    def __init__(self, B):
        hv = kl_hvk.Hvk(B.files[next(n for e, n in B.ext.items() if e.lower() == '.hvk')])
        sc = B.sc
        self.node = {e.ref: i + 1 for i, e in enumerate(B.ents)}
        self.tris, self.grid, self.big = [], collections.defaultdict(list), []
        self.skipped = collections.Counter()
        for s in hv.shapes:
            if s.type != kl_hvk.STATIC or s.convex:
                self.skipped['not static (moves) or convex'] += len(s.inst)
                continue
            vs = [struct.unpack_from('<3f', s.verts, i * s.vstride) for i in range(len(s.verts) // s.vstride)]
            idx = struct.unpack('<%dH' % (len(s.idx) // 2), s.idx)
            for inst in s.inst:
                r = kl_hvk.ref(inst)
                k = self.node.get(r)
                if k is None or not sc.names[sc.top[k]].startswith(MAP_TOPS):
                    self.skipped['not of the map'] += 1
                    continue
                p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
                w = [tuple(100 * (p[a] + m[3 * a] * v[0] + m[3 * a + 1] * v[1] + m[3 * a + 2] * v[2]) for a in range(3)) for v in vs]
                for t in range(0, len(idx) - 2, 3):
                    a, b, c = w[idx[t]], w[idx[t + 1]], w[idx[t + 2]]
                    i = len(self.tris)
                    self.tris.append((a, b, c, r))
                    x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
                    z0, z1 = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
                    if (x1 - x0) * (z1 - z0) > self.GRID * self.GRID * 100:
                        self.big.append(i)
                        continue
                    for cx in range(int(x0 // self.GRID), int(x1 // self.GRID) + 1):
                        for cz in range(int(z0 // self.GRID), int(z1 // self.GRID) + 1):
                            self.grid[cx, cz].append(i)
        self._scan, self._runs = {}, {}

    def near(self, x, z, r):
        g, ks = self.GRID, set(self.big)
        for cx in range(int((x - r) // g), int((x + r) // g) + 1):
            for cz in range(int((z - r) // g), int((z + r) // g) + 1):
                ks.update(self.grid.get((cx, cz), ()))
        return ks

    def floor(self, x, y, z, reach=90.0):
        """The height of the collision's floor at (x, z) nearest to y (an up-facing triangle within `reach` of y), or
        None. The navigation mesh is not the ground: Retomoto's street mesh lies 40 under the road."""
        best = None
        for i in self.grid.get((int(x // self.GRID), int(z // self.GRID)), []) + self.big:
            a, b, c, _r = self.tris[i]
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-9:
                continue
            u = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            v = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            h = u * a[1] + v * b[1] + (1 - u - v) * c[1]
            e1, e2 = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
            n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
            if ln < 1e-9 or abs(n[1]) / ln < 0.7 or abs(h - y) > reach:
                continue
            if best is None or abs(h - y) < abs(best - y):
                best = h
        return best

    def scan(self, x, y, z, gather=GATHER):
        """The outlines of the collision round (x, z) in the planes PLANES over y ->
        {plane: {REF: set of raster cells}}, {REF: [segment (x0, z0, x1, z1)] in the BASE plane}."""
        key = (round(x / 20), round(y / 5), round(z / 20), gather)
        if key in self._scan:
            return self._scan[key]
        occ = {h: collections.defaultdict(set) for h in PLANES}
        segs = collections.defaultdict(list)
        for i in self.near(x, z, gather):
            a, b, c, r = self.tris[i]
            lo, hi = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
            for h in PLANES:
                yh = y + h + 0.37                       # (off every round height: a plane through a vertex cuts nothing twice)
                if not lo < yh < hi:
                    continue
                pts = []
                for p, q in ((a, b), (b, c), (c, a)):
                    if (p[1] - yh) * (q[1] - yh) < 0:
                        t = (yh - p[1]) / (q[1] - p[1])
                        pts.append((p[0] + t * (q[0] - p[0]), p[2] + t * (q[2] - p[2])))
                if len(pts) != 2:
                    continue
                (x0, z0), (x1, z1) = pts
                if max(abs(x0 - x), abs(z0 - z)) > gather and max(abs(x1 - x), abs(z1 - z)) > gather:
                    continue
                # a segment runs so that the triangle's normal points to its LEFT, (-dz, dx): the free side of the
                # face when the collision is wound outward (wall_runs() tests that against the mesh)
                nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
                nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                if -(z1 - z0) * nx + (x1 - x0) * nz < 0:
                    x0, z0, x1, z1 = x1, z1, x0, z0
                n = max(1, int(math.hypot(x1 - x0, z1 - z0) / (CELL / 2)))
                cells = occ[h][r]
                for j in range(n + 1):
                    cells.add((int((x0 + (x1 - x0) * j / n) // CELL), int((z0 + (z1 - z0) * j / n) // CELL)))
                if h == BASE:
                    segs[r].append((x0, z0, x1, z1))
        if len(self._scan) > 300:
            self._scan.clear()
        self._scan[key] = (occ, segs)
        return occ, segs


def _grow(cells, n=2):
    return {(c[0] + i, c[1] + j) for c in cells for i in range(-n, n + 1) for j in range(-n, n + 1)}


def min_rect(pts):
    """The smallest rectangle (in the plan) round the points -> (cx, cz, ux, uz, a, b): middle, the unit vector of
    its long side, half length, half width. Angles tried every 3 degrees, then every 0.5 round the best."""
    best = None
    def at(deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        us = [p[0] * c + p[1] * s for p in pts]
        vs = [-p[0] * s + p[1] * c for p in pts]
        return (max(us) - min(us)) * (max(vs) - min(vs)), deg, c, s, min(us), max(us), min(vs), max(vs)
    for d in range(0, 90, 3):
        r = at(d)
        if best is None or r[0] < best[0]:
            best = r
    for k in range(-5, 6):
        r = at(best[1] + 0.5 * k) if k else best
        if r[0] < best[0]:
            best = r
    _area, _deg, c, s, u0, u1, v0, v1 = best
    mu, mv = (u0 + u1) / 2, (v0 + v1) / 2
    cx, cz = mu * c - mv * s, mu * s + mv * c
    a, b = (u1 - u0) / 2, (v1 - v0) / 2
    if a >= b:
        return cx, cz, c, s, a, b
    return cx, cz, -s, c, b, a


def objects(S, B, x, y, z, near, gather=GATHER):
    """What stands round the place (x, y, z): [dict] - one per joined-up outline of one entity in the BASE plane that
    comes within `near` of the place: ref, name, rect, high (bool), and 'no' = why it is no cover (or None)."""
    occ, segs = S.scan(x, y, z, gather)
    sc, out = B.sc, []
    for r, cells in occ[BASE].items():
        k = S.node.get(r)
        name = sc.path[k][5:] if k else 'REF %d' % r
        left = set(cells)
        while left:
            seed = left.pop()
            comp, todo = {seed}, [seed]
            while todo:
                c = todo.pop()
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        q = (c[0] + i, c[1] + j)
                        if q in left:
                            left.discard(q); comp.add(q); todo.append(q)
            d = min(math.hypot((c[0] + 0.5) * CELL - x, (c[1] + 0.5) * CELL - z) for c in comp)
            if d > near:
                continue
            o = {'ref': r, 'name': name, 'dist': round(d), 'no': None}
            far = max(max(abs((c[0] + 0.5) * CELL - x), abs((c[1] + 0.5) * CELL - z)) for c in comp)
            pts = [(s[0], s[1]) for s in segs[r] if (int(s[0] // CELL), int(s[1] // CELL)) in comp] + \
                  [(s[2], s[3]) for s in segs[r] if (int(s[2] // CELL), int(s[3] // CELL)) in comp]
            if far > gather - 2 * CELL or len(pts) < 3:
                o['no'] = 'long (a wall or a building)' if len(pts) >= 3 else 'a scrap of collision'
                out.append(o); continue
            cx, cz, ux, uz, a, b = min_rect(pts)
            o['rect'] = [round(cx, 1), round(cz, 1), round(ux, 4), round(uz, 4), round(a, 1), round(b, 1)]
            cov = lambda h: len(comp & _grow(occ[h].get(r, ()))) / len(comp)
            o['high'] = cov(HIGH) >= HIGH_SHARE
            low = name.lower().split('\\')[-1]
            if any(t in low for t in NOT_COVER):
                o['no'] = 'its name says it is no cover (%s)' % next(t for t in NOT_COVER if t in low)
            elif 2 * a > LONG:
                o['no'] = 'long (a wall or a building)'
            elif 2 * a < SLIM:
                o['no'] = 'slimmer than %d' % SLIM
            elif 2 * b < THIN:
                o['no'] = 'a single plane (a pane, a fence)'
            elif cov(LOW) < LOW_SHARE:
                o['no'] = 'does not stand on the ground here (a table top, a ledge)'
            out.append(o)
    return out


# ------------------------------------------------------------------ wall corners
def wall_runs(S, B, x, y, z, reach):
    """The straight faces of the static collision in the BASE plane round (x, z) -> [dict a, b (ends), u (a -> b),
    n (unit normal, the side the triangles face), len, ref]. Cut segments of every entity whose name does not say it
    is no cover, joined when they lie on one line (5 off it, 10 degrees, gaps up to RUN_GAP); a run counts from
    WALL_RUN on and when at least 80 % of its length faces one way (a single two-sided plane has no side)."""
    key = (round(x / 20), round(y / 5), round(z / 20), reach)
    if key in S._runs:
        return S._runs[key]
    _occ, segs = S.scan(x, y, z)
    sc, items = B.sc, []
    for r, ss in segs.items():
        k = S.node.get(r)
        low = sc.names[k].lower() if k else ''
        if any(t in low for t in NOT_COVER):
            continue
        for s in ss:
            L = math.hypot(s[2] - s[0], s[3] - s[1])
            if L < 2.0 or min(max(abs(s[0] - x), abs(s[1] - z)), max(abs(s[2] - x), abs(s[3] - z))) > reach:
                continue
            items.append((L, s, r))
    items.sort(key=lambda it: -it[0])
    bins = collections.defaultdict(list)
    for i, (L, s, r) in enumerate(items):
        bins[int(math.degrees(math.atan2(s[3] - s[1], s[2] - s[0])) % 360 // 10)].append(i)
    used, runs = [False] * len(items), []
    for i, (L, s, r) in enumerate(items):
        if used[i] or L < 30.0:
            continue
        ux, uz = (s[2] - s[0]) / L, (s[3] - s[1]) / L
        ab = int(math.degrees(math.atan2(uz, ux)) % 360 // 10)
        got = []
        for sign, base in ((1.0, ab), (-1.0, (ab + 18) % 36)):
            for bb in (base - 1, base, base + 1):
                for j in bins.get(bb % 36, ()):
                    if used[j]:
                        continue
                    Lj, t, rj = items[j]
                    if abs((t[0] - s[0]) * -uz + (t[1] - s[1]) * ux) > 5.0 or abs((t[2] - s[0]) * -uz + (t[3] - s[1]) * ux) > 5.0:
                        continue
                    if sign * ((t[2] - t[0]) * ux + (t[3] - t[1]) * uz) < 0.985 * Lj:
                        continue
                    t0, t1 = (t[0] - s[0]) * ux + (t[1] - s[1]) * uz, (t[2] - s[0]) * ux + (t[3] - s[1]) * uz
                    got.append((min(t0, t1), max(t0, t1), sign * Lj, rj, j))
        got.sort()
        cur = None
        groups = []
        for g in got:
            if cur is not None and g[0] <= cur[1] + RUN_GAP:
                cur[1] = max(cur[1], g[1]); cur[2].append(g)
            else:
                cur = [g[0], g[1], [g]]; groups.append(cur)
        for t0, t1, gs in groups:
            if not any(g[4] == i for g in gs):
                continue                                # (the pieces of this line the seed is not part of wait for a seed of their own)
            for g in gs:
                used[g[4]] = True
            pos, neg = sum(g[2] for g in gs if g[2] > 0), -sum(g[2] for g in gs if g[2] < 0)
            if t1 - t0 < WALL_RUN or max(pos, neg) < 0.8 * (pos + neg):
                continue
            sg = 1.0 if pos >= neg else -1.0
            a, b = (s[0] + t0 * ux, s[1] + t0 * uz), (s[0] + t1 * ux, s[1] + t1 * uz)
            if sg < 0:
                a, b = b, a
            runs.append({'a': a, 'b': b, 'u': (sg * ux, sg * uz), 'n': (-sg * uz, sg * ux), 'len': t1 - t0, 'ref': max(gs, key=lambda g: abs(g[2]))[3]})
    if len(S._runs) > 300:
        S._runs.clear()
    S._runs[key] = runs
    return runs


def corners(S, B, x, y, z, near):
    """The convex vertical corners of solid static collision within `near` of the place (x, y, z) -> [dict]:
      kind 'L'   two faces of at least WALL_RUN meet (their ends within JOIN) at 60..120 degrees and each faces away
                 from the other (a building corner, a wide pillar; an inner room corner faces the other way);
      kind 'end' two faces back to back, WALL_THICK apart, end side by side (a wall end, a doorway jamb), and nothing
                 goes on beyond the end for END_GAP;
      at (x, z), faces [(end point, u = along the face away from the corner, n = the side it faces, length, REF)],
      thick ('end'), high (both faces are there in the HIGH plane too), grounded (... and in the LOW plane)."""
    runs = wall_runs(S, B, x, y, z, near + 350.0)
    occ, _segs = S.scan(x, y, z)
    ends = []
    for i, r in enumerate(runs):
        ends.append((r['a'], r['u'], r['n'], r['len'], r['ref'], i))
        ends.append((r['b'], (-r['u'][0], -r['u'][1]), r['n'], r['len'], r['ref'], i))
    def there(plane, p, u):
        hit = 0
        for t in (15.0, 50.0, 85.0):
            cx, cz = int((p[0] + t * u[0]) // CELL), int((p[1] + t * u[1]) // CELL)
            if any((cx + i, cz + j) in cells for cells in occ[plane].values() for i in (-2, -1, 0, 1, 2) for j in (-2, -1, 0, 1, 2)):
                hit += 1
        return hit >= 2
    out = []
    for i in range(len(ends)):
        p, u, n, L, ref, ri = ends[i]
        if math.hypot(p[0] - x, p[1] - z) > near:
            continue
        for j in range(i + 1, len(ends)):
            q, v, m, L2, ref2, rj = ends[j]
            if ri == rj:
                continue
            w = (q[0] - p[0], q[1] - p[1])
            d = math.hypot(*w)
            if d > WALL_THICK[1] + 25.0:
                continue
            c = u[0] * v[0] + u[1] * v[1]
            kind = thick = None
            if d <= JOIN and abs(c) <= 0.5 and n[0] * v[0] + n[1] * v[1] < -0.3 and m[0] * u[0] + m[1] * u[1] < -0.3:
                kind = 'L'
                # the corner = where the two lines cross
                det = u[0] * v[1] - u[1] * v[0]
                t = (w[0] * v[1] - w[1] * v[0]) / det
                at = (p[0] + t * u[0], p[1] + t * u[1])
                if math.hypot(at[0] - p[0], at[1] - p[1]) > JOIN:
                    at = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            elif c >= 0.96 and n[0] * m[0] + n[1] * m[1] <= -0.9 and abs(w[0] * u[0] + w[1] * u[1]) <= 20.0:
                thick = -(w[0] * n[0] + w[1] * n[1])
                if WALL_THICK[0] <= thick < WALL_THICK[1]:
                    kind = 'end'
                    at = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                    free = True
                    for step in range(2, int(END_GAP // CELL) + 1):
                        for k in range(0, int(thick // CELL) + 1):
                            px, pz = p[0] - step * CELL * u[0] - k * CELL * n[0], p[1] - step * CELL * u[1] - k * CELL * n[1]
                            if any((int(px // CELL), int(pz // CELL)) in cells for cells in occ[BASE].values()):
                                free = False
                    if not free:
                        continue
            if kind is None:
                continue
            out.append({'kind': kind, 'at': at, 'thick': thick, 'faces': [(p, u, n, L, ref), (q, v, m, L2, ref2)],
                        'high': there(HIGH, p, u) and there(HIGH, q, v), 'grounded': there(LOW, p, u) and there(LOW, q, v),
                        'dist': math.hypot(at[0] - x, at[1] - z)})
    return out


# ------------------------------------------------------------------ the build's own cover boxes
def _root(prm, model):
    t, n = struct.unpack_from('<II', prm, 0)
    if not 0 < model < n:
        return None
    o, size = struct.unpack_from('<II', prm, t + 16 * model)
    return prm[o:o + size] if size == 64 and prm[o:o + 4] == b'\0\1\7\0' else None


def all_boxes(B):
    """Every entity named *coverbox* -> [dict]: node, name, kind, flags, model, the middle of its model's box in the
    world (its origin when the model has no plain root), listed (in a room tree)."""
    sc, prm, out = B.sc, B['.prm'], []
    for k in range(1, len(sc.nodes)):
        low = sc.names[k].lower()
        if 'coverbox' not in low:
            continue
        e = B.ents[k - 1]
        root = _root(prm, e.model) if sc.cls(k) == 'ZSTDOBJ' else None
        bb = struct.unpack_from('<6f', root, 0x20) if root else None
        mid = B.world(k, tuple((bb[i] + bb[i + 3]) / 2 for i in range(3))) if bb else B.at(k)
        kind = 'car' if 'coverboxcar' in low else 'low' if ('coverboxm' in low or 'coverboxl' in low) else 'high' if 'coverboxh' in low else None
        out.append({'node': k, 'name': sc.names[k], 'cls': sc.cls(k), 'kind': kind, 'flags': e.flags, 'model': e.model, 'mid': mid, 'at': B.at(k),
                    'bb': bb, 'octrec': struct.unpack_from('<I', root, 0x1c)[0] if root else None})
    return out


def forms(B, boxes, tiers='b', borrow=True):
    """The box models a new box may take -> [dict]: node (the box that is cloned), model, tier ('b': flags 0x200, no
    collision record; 'a': flags 0x302 with one), size (x, y, z), mid (x, z of the model box's middle), lo_y."""
    sc, seen, out = B.sc, set(), []
    for c in boxes:
        k, e = c['node'], B.ents[c['node'] - 1]
        if c['cls'] != 'ZSTDOBJ' or c['kind'] not in ('high', 'low') or c['bb'] is None or c['model'] in seen or TAG.lower() in c['name'].lower():
            continue
        tier = 'b' if (e.flags == 0x200 and not c['octrec']) else 'a' if (e.flags == 0x302 and c['octrec']) else None
        if tier is None or tier not in tiers or sc.nodes[k]['ctrls'] or e.raw is not None or e.links is not None or e.aux or e.group:
            continue
        r9 = struct.unpack('<9f', e.rot[:36])
        if any(abs(math.sqrt(sum(v * v for v in r9[i:i + 3])) - 1.0) > 1e-3 for i in (0, 3, 6)):
            continue
        bb = c['bb']
        size = tuple(bb[i + 3] - bb[i] for i in range(3))
        mid = ((bb[0] + bb[3]) / 2, (bb[2] + bb[5]) / 2)
        if max(size[0], size[2]) > MODEL_MAX or math.hypot(*mid) > MODEL_OFF or min(size[0], size[2]) < 10:
            continue
        seen.add(c['model'])
        out.append({'node': k, 'path': sc.path[k][5:], 'model': c['model'], 'tier': tier, 'size': size, 'mid': mid, 'lo_y': bb[1], 'kind': c['kind']})
    # A SMALL LOW BOX WHERE THE BUILD HAS NONE OF ITS OWN (borrow): the box primitive of another object of the build.
    # Every build carries F07's hand-held camera objects (AllLevels/FA_Cam_Handheld.zip\Cam_Handheld\*_Cam): ZSTDOBJ
    # whose model is a 100 x 100 x 100 box with ONE hidden mesh and no collision record - the same kind of model a
    # form b cover box has (stock F05's commonest low form b box is 100 x 100 x 100: 20 of them). The new box is a
    # clone of one of the build's own form b cover boxes with that model number: flags 0x200, a model root without
    # a collision record, in no tree = form b. ASSUMPTION: a cover box may share its model with an object that is no
    # cover box (models are shared between entities everywhere; the cover list reads the entity's own box, 13.2).
    own_low = [f for f in out if f['tier'] == 'b' and LOW_Y[0] <= f['size'][1] < LOW_Y[1] and max(f['size'][0], f['size'][2]) <= BORROW_MAX]
    src = next((f for f in out if f['tier'] == 'b' and f['kind'] == 'low'), None) or next((f for f in out if f['tier'] == 'b'), None)
    if borrow and 'b' in tiers and not own_low and src is not None:
        prm = B['.prm']
        t, n = struct.unpack_from('<II', prm, 0)
        best = None
        for k in range(1, len(sc.nodes)):
            e = B.ents[k - 1]
            if sc.cls(k) != 'ZSTDOBJ' or 'coverbox' in sc.names[k].lower() or e.model in seen or (best and e.model >= best[0]):
                continue
            root = _root(prm, e.model)
            if root is None:
                continue
            cnt, objtab, octrec = struct.unpack_from('<III', root, 0x14)
            bb = struct.unpack_from('<6f', root, 0x20)
            size = tuple(bb[i + 3] - bb[i] for i in range(3))
            if octrec or cnt != 1 or not 0 < objtab < n or not LOW_Y[0] <= size[1] < LOW_Y[1] or not 60.0 <= min(size[0], size[2]) <= max(size[0], size[2]) <= BORROW_MAX \
                    or max(abs(bb[0] + bb[3]), abs(bb[2] + bb[5])) > 2.0:
                continue
            to, _ts = struct.unpack_from('<II', prm, t + 16 * objtab)
            m0 = struct.unpack_from('<I', prm, to)[0]
            if not 0 < m0 < n:
                continue
            mo, ms = struct.unpack_from('<II', prm, t + 16 * m0)
            if ms != 64 or not struct.unpack_from('<I', prm, mo + 0x1c)[0] & 0x800000:      # one plain mesh, hidden (kl2 0x67cf77)
                continue
            best = (e.model, k, size, bb)
        if best:
            model, k, size, bb = best
            out.append({'node': src['node'], 'path': src['path'], 'model': model, 'tier': 'b', 'size': size, 'mid': ((bb[0] + bb[3]) / 2, (bb[2] + bb[5]) / 2),
                        'lo_y': bb[1], 'kind': 'low', 'borrowed': sc.path[k][5:]})
    return out


def fit(o, fs, ask):
    """The box for object o (rect, high) seen from the place `ask` -> dict (form, heading of the box's local Z,
    middle x z, extents along the rect's axes) or None when no model of the build fits."""
    cx, cz, ux, uz, a, b = o['rect']
    vx, vz = -uz, ux
    lo, hi = HIGH_Y if o['high'] else LOW_Y
    best = {}
    for f in fs:
        if not lo <= f['size'][1] < hi:
            continue
        for along_u in (True, False):                   # the model's local Z along the rect's long side, or across it
            eu, ev = (f['size'][2], f['size'][0]) if along_u else (f['size'][0], f['size'][2])
            ou, ov = max(0.0, eu - 2 * a), max(0.0, ev - 2 * b)
            if ou > OVER or ov > OVER:
                continue
            key = (-(min(eu, 2 * a) * min(ev, 2 * b)), ou + ov, f['model'])     # most of the object covered, then least overhang
            if best.get(f['tier']) is None or key < best[f['tier']][0]:
                best[f['tier']] = (key, f, along_u, eu, ev)
    if not best:
        return None
    # tier b (the plain form) whenever one of its models covers at least TIER_B of what the best tier a model would
    pick = best.get('b')
    if pick is None or ('a' in best and pick[0][0] > TIER_B * best['a'][0][0]):     # (keys are minus the covered area)
        pick = best.get('a') or pick
    _k, f, along_u, eu, ev = pick
    du, dv = (ask[0] - cx) * ux + (ask[2] - cz) * uz, (ask[0] - cx) * vx + (ask[2] - cz) * vz
    tu = max(-max(0.0, a - eu / 2), min(max(0.0, a - eu / 2), du))
    if 2 * a > ENDS:                                    # a long thing: its END nearest the place (a corner to stand behind)
        tu = math.copysign(max(0.0, a - eu / 2), du)
    tv = max(-max(0.0, b - ev / 2), min(max(0.0, b - ev / 2), dv))
    mid = (cx + tu * ux + tv * vx, cz + tu * uz + tv * vz)
    head = (ux, uz) if along_u else (vx, vz)            # local +Z; local +X is then (head z, -head x) (kl_fa_bots.rot9)
    xax = (head[1], -head[0])
    org = (mid[0] - f['mid'][0] * xax[0] - f['mid'][1] * head[0], mid[1] - f['mid'][0] * xax[1] - f['mid'][1] * head[1])
    return {'form': f, 'head': head, 'mid': mid, 'origin': org, 'ext': (eu, ev)}


# ------------------------------------------------------------------ the plan
class Ctx(D.Ctx):
    def __init__(self, folder, log=print):
        D.Ctx.__init__(self, folder, log)
        B, sc = self.B, self.B.sc
        self.solid = Solid(B)
        self.boxes = all_boxes(B)
        self.nocover = [k for k in range(1, len(sc.nodes)) if kl_fa.has(sc, k, 'NoCoverBox') and sc.cls(k) == 'ZBoxPrimitive']
        self.real = len(self.covers)


def asks(ctx, opt_dyn=None):
    """One run of the dynamic step's plan -> (its hold tally, the places that asked for a hold and got none)."""
    ctx.misses = []
    P = D.plan(ctx, opt_dyn, log=lambda *a: None)
    seen, out = set(), []
    for m in ctx.misses:
        k = (round(m['at'][0] / 25), round(m['at'][1] / 50), round(m['at'][2] / 25), m['part'])
        if k not in seen:
            seen.add(k); out.append(m)
    ctx.misses = None
    return P['hold_search'], out


def consider(ctx, m, o, fs, new, near):
    """Object o for the place m -> a new box (dict) or a reason (str)."""
    B = ctx.B
    x, _my, z = m['at']
    y = m['ground']                                     # the collision's floor under the place (the mesh may lie under it)
    cx, cz, ux, uz, a, b = o['rect']
    vx, vz = -uz, ux
    for c in ctx.boxes + new:
        p = c['mid']
        if c.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ' or c['kind'] is None:      # ('NoCoverBoxPillar' is a no-cover box, not a cover)
            continue
        du, dv = (p[0] - cx) * ux + (p[2] - cz) * uz, (p[0] - cx) * vx + (p[2] - cz) * vz
        if abs(du) <= a + 60 and abs(dv) <= b + 60 and -150 <= p[1] - y <= 300:
            return 'has a cover box already (%s)' % c['name']
    got = fit(o, fs, m['at'])
    if got is None:
        return 'no box model of the build fits it (%s, %d x %d)' % ('high' if o['high'] else 'low', 2 * a, 2 * b)
    f, mid = got['form'], got['mid']
    if 2 * a > ENDS:
        # its end must be free: a wall piece that goes on in the next piece has no corner there
        sgn = 1.0 if (x - cx) * ux + (z - cz) * uz >= 0 else -1.0
        occ, _segs = ctx.solid.scan(x, y, z)
        for step in range(2, int(END_GAP // CELL) + 1):
            for w in range(-int(b // CELL), int(b // CELL) + 1):
                px, pz = cx + sgn * (a + step * CELL) * ux + w * CELL * vx, cz + sgn * (a + step * CELL) * uz + w * CELL * vz
                cell = (int(px // CELL), int(pz // CELL))
                if any(cell in cells for cells in occ[BASE].values()):
                    return 'long, and its end is joined to more collision (a wall in a row: no corner)'
    for c in ctx.boxes + new:
        if c.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ' or c['kind'] is None:
            continue
        if math.hypot(c['mid'][0] - mid[0], c['mid'][2] - mid[1]) < APART and abs(c['mid'][1] - y - f['size'][1] / 2) < 200:
            return 'a cover box stands within %d of where its box would be (%s)' % (APART, c['name'])
    e4 = ctx.p4(m['at'], dy=40.0)
    my = m['at'][1]
    if e4 is None:
        return 'the place that asked is not on the mesh'
    # the places a bot could be told to hold at it: kl_fa_bots_dyn's own ring and its own rules
    ctx.covers.append({'node': 0, 'at': (got['origin'][0], y - f['lo_y'], got['origin'][1]), 'kind': 'high' if o['high'] else 'low', 'hidden': False})
    ci = len(ctx.covers) - 1
    spots = sorted(ctx.spots(ci), key=lambda q: math.hypot(q[0] - x, q[2] - z))
    ok = next((q for q in spots[:10] if abs(q[1] - my) <= 200 and ctx.nav.part[q[3]] == m['part'] and D.hold_ok(ctx, m['part'], e4, q, None, m['post'])), None)
    ctx.covers.pop(); ctx._spots.pop(ci, None)
    if ok is None:
        return 'no place on the mesh to hold at it (%d places 70..230 from it, none the bot may walk to)' % len(spots)
    g2 = ctx.solid.floor(ok[0], ok[1], ok[2])           # the floor where the bot would stand at it
    ground = g2 if g2 is not None and abs(g2 - y) > 20.0 else y
    if abs(ground - y) > 20.0:
        # the object stands on other ground than the place that asked: look at it again from its own ground
        again = [p for p in objects(ctx.solid, B, mid[0], ground, mid[1], a + 100.0, a + 900.0) if p['ref'] == o['ref'] and not p['no']
                 and math.hypot(p['rect'][0] - cx, p['rect'][1] - cz) < 150 and p['high'] == o['high']]
        if not again:
            return 'on other ground (%+d) it is not the same object' % (ground - y)
    org = (got['origin'][0], ground - f['lo_y'], got['origin'][1])
    c3 = (mid[0], ground + f['size'][1] / 2, mid[1])
    foot = [(mid[0] + su * got['ext'][0] / 2 * ux + sv * got['ext'][1] / 2 * vx, ground + 50.0, mid[1] + su * got['ext'][0] / 2 * uz + sv * got['ext'][1] / 2 * vz)
            for su in (-1, 1) for sv in (-1, 1)] + [(mid[0], ground + 50.0, mid[1])]
    for k in ctx.nocover:
        if any(B.in_box(k, p) for p in foot) or B.in_box(k, ok[:3]):
            return 'inside a NoCoverBox (%s)' % B.sc.names[k]
    if ctx.exits and any(D.in_any_exit(ctx, p) for p in foot):
        return 'in a level exit box'
    if ctx.lane and min(F.lane_dist(ctx.lane, p) for p in foot) < F.LANE_CLEAR:
        return 'within %d of the escape vehicle\'s road' % F.LANE_CLEAR
    if ctx.rt is not None and m['part'] != ctx.home and any(ctx.rt.lane(p) for p in foot):
        return 'in the van\'s lane'
    return {'kind': 'high' if o['high'] else 'low', 'origin': [round(v, 2) for v in org], 'head': [round(v, 5) for v in got['head']],
            'mid': [round(v, 1) for v in c3], 'ext': [round(v, 1) for v in got['ext']], 'height': round(f['size'][1], 1),
            'model': f['model'], 'form': f['path'], 'form_node': f['node'], 'tier': f['tier'], 'borrowed': f.get('borrowed'),
            'object': o['name'], 'object_ref': o['ref'], 'object_rect': o['rect'], 'ask': m['at'], 'ground': round(ground, 1),
            'hold': [round(v, 1) for v in ok[:3]],
            'role': m['role'], 'name': None}


def consider_corner(ctx, m, cn, fs, new):
    got = _corner(ctx, m, cn, fs, new, 0)
    if isinstance(got, str):                            # its other face, when that one is hidden from ahead too
        g2 = _corner(ctx, m, cn, fs, new, 1)
        if not isinstance(g2, str):
            return g2
    return got


def _corner(ctx, m, cn, fs, new, which):
    """Corner cn (corners()) for the place m -> a new box (dict; HIGH when the corner is solid at 175 too) or a reason (str).
    How the box sits is what stock does (re/bots_dyn_build.md 13.1, measured on F05 and F08: 219 of 240 'L' boxes
    have a footprint corner within 15 of the wall corner, lie in the solid and along the face): in the solid, one
    footprint corner ON the corner, along the face. WHICH face is OURS and a GUESS: the one hidden from where the bot
    is walking TOWARD on this leg (m['dir']) - the threat is taken to be ahead on the bot's way."""
    B = ctx.B
    x, my, z = m['at']
    y = m['ground']
    d = m['dir']
    if not cn['grounded']:
        return 'a corner that does not stand on the floor here (nothing %d over it)' % LOW
    kind = 'high' if cn['high'] else 'low'              # low: a garden wall, a parapet (there at 75, not at 175)
    ky = HIGH_Y if cn['high'] else LOW_Y
    on = lambda px, pz: ctx.grid.at(px, my, pz, 60.0) is not None
    # the face to stand at: it faces back along the bot's way (n . dir most negative), and the ground before it is mesh
    faces = sorted(cn['faces'], key=lambda f: f[2][0] * d[0] + f[2][1] * d[1])
    p, u, n, L, ref = faces[which]
    other = faces[1 - which]
    if n[0] * d[0] + n[1] * d[1] > -0.3:
        return 'a corner with no face hidden from ahead on the bot\'s way'
    # (the mesh keeps off the walls: asked 50, 80 and 110 before the face; the hold place below is the real test)
    if not any(on(p[0] + a * u[0] + b * n[0], p[1] + a * u[1] + b * n[1]) for a, b in ((40.0, 50.0), (40.0, 80.0), (40.0, 110.0), (80.0, 80.0))):
        return 'a corner whose hidden face has no mesh before it'
    # how deep the solid is behind that face: a wall end = its thickness; a corner = up to the first mesh behind it
    # (a thin shell with a room behind it) or the length of the other face
    if cn['kind'] == 'end':
        depth = cn['thick']
    else:
        depth = min(MODEL_MAX, other[3] * abs(other[1][0] * n[0] + other[1][1] * n[1]))
        for s in range(20, int(depth) + 1, 20):
            if on(p[0] + 30.0 * u[0] - s * n[0], p[1] + 30.0 * u[1] - s * n[1]):
                depth = s - 10.0
                break
    best = None
    for f in fs:
        if not ky[0] <= f['size'][1] < ky[1]:
            continue
        for along_u in (True, False):                   # the model's local Z along the face, or across it
            eu, ev = (f['size'][2], f['size'][0]) if along_u else (f['size'][0], f['size'][2])
            # not out of the solid, not longer than the face, not a sliver (stock's corner boxes are 70..150 along the
            # face and as deep as the wall is thick, or 60..120 at a building corner: 13.1)
            if ev > depth + CORNER_OVER or eu > L or eu < CORNER_MIN or ev < min(CORNER_MIN, 0.7 * depth):
                continue
            key = (abs(ev - min(depth, CORNER_AIM)) + abs(eu - CORNER_AIM), f['model'])
            if best is None or key < best[0]:
                best = (key, f, along_u, eu, ev)
    if best is None:
        return 'no %s box model of the build fits the corner (%s, the solid behind its face is %d deep)' % (kind, 'a wall end' if cn['kind'] == 'end' else 'two faces', depth)
    _k, f, along_u, eu, ev = best
    mid = (p[0] + eu / 2 * u[0] - ev / 2 * n[0], p[1] + eu / 2 * u[1] - ev / 2 * n[1])
    head = u if along_u else n
    xax = (head[1], -head[0])
    org = (mid[0] - f['mid'][0] * xax[0] - f['mid'][1] * head[0], mid[1] - f['mid'][0] * xax[1] - f['mid'][1] * head[1])
    for c in ctx.boxes + new:
        if c.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ' or c['kind'] is None:
            continue
        reach = max(APART, (math.hypot(c['bb'][3] - c['bb'][0], c['bb'][5] - c['bb'][2]) / 2 + 60.0) if c.get('bb') else APART)
        if (math.hypot(c['mid'][0] - mid[0], c['mid'][2] - mid[1]) < APART or math.hypot(c['mid'][0] - cn['at'][0], c['mid'][2] - cn['at'][1]) < reach) \
                and -150 <= c['mid'][1] - y <= 300:
            return 'a cover box stands at the corner already (%s)' % c['name']
    e4 = ctx.p4(m['at'], dy=40.0)
    if e4 is None:
        return 'the place that asked is not on the mesh'
    ctx.covers.append({'node': 0, 'at': (org[0], y - f['lo_y'], org[1]), 'kind': kind, 'hidden': False})
    ci = len(ctx.covers) - 1
    spots = sorted((q for q in ctx.spots(ci) if (q[0] - p[0]) * n[0] + (q[2] - p[1]) * n[1] > 10.0), key=lambda q: math.hypot(q[0] - x, q[2] - z))
    ok = next((q for q in spots[:10] if abs(q[1] - my) <= 200 and ctx.nav.part[q[3]] == m['part'] and D.hold_ok(ctx, m['part'], e4, q, None, m['post'])), None)
    ctx.covers.pop(); ctx._spots.pop(ci, None)
    if ok is None:
        return 'no place on the mesh to hold at the corner\'s hidden face (%d places 70..230 from it)' % len(spots)
    g2 = ctx.solid.floor(ok[0], ok[1], ok[2])
    if g2 is not None and abs(g2 - y) > 20.0:
        return 'the corner stands on other ground than the place that asked (%+d)' % (g2 - y)
    c3 = (mid[0], y + f['size'][1] / 2, mid[1])
    foot = [(mid[0] + su * eu / 2 * u[0] + sv * ev / 2 * n[0], y + 50.0, mid[1] + su * eu / 2 * u[1] + sv * ev / 2 * n[1])
            for su in (-1, 1) for sv in (-1, 1)] + [(mid[0], y + 50.0, mid[1])]
    for k in ctx.nocover:
        if any(B.in_box(k, q) for q in foot) or B.in_box(k, ok[:3]):
            return 'inside a NoCoverBox (%s)' % B.sc.names[k]
    if ctx.exits and any(D.in_any_exit(ctx, q) for q in foot):
        return 'in a level exit box'
    if ctx.lane and min(F.lane_dist(ctx.lane, q) for q in foot) < F.LANE_CLEAR:
        return 'within %d of the escape vehicle\'s road' % F.LANE_CLEAR
    if ctx.rt is not None and m['part'] != ctx.home and any(ctx.rt.lane(q) for q in foot):
        return 'in the van\'s lane'
    k = ctx.solid.node.get(ref)
    return {'kind': kind, 'via': 'corner', 'origin': [round(org[0], 2), round(y - f['lo_y'], 2), round(org[1], 2)], 'head': [round(v, 5) for v in head],
            'mid': [round(v, 1) for v in c3], 'ext': [round(eu, 1), round(ev, 1)], 'height': round(f['size'][1], 1),
            'model': f['model'], 'form': f['path'], 'form_node': f['node'], 'tier': f['tier'], 'borrowed': f.get('borrowed'),
            'object': (B.sc.path[k][5:] if k else 'REF %d' % ref), 'object_ref': ref,
            'object_rect': [round(mid[0], 1), round(mid[1], 1), round(u[0], 4), round(u[1], 4), round(eu / 2, 1), round(ev / 2, 1)],
            'corner': {'kind': cn['kind'], 'at': [round(v, 1) for v in cn['at']], 'thick': cn['thick'] and round(cn['thick'], 1), 'depth': round(depth, 1),
                       'face_normal': [round(v, 3) for v in n], 'face_length': round(L), 'other_face_length': round(other[3]),
                       'way': [round(v, 3) for v in d]},
            'ask': m['at'], 'ground': round(y, 1), 'hold': [round(v, 1) for v in ok[:3]], 'role': m['role'], 'name': None}


def plan(ctx, opt=None, log=print):
    """-> dict: boxes [new box], gaps [place without a hold after the last round, with what stands there],
    holds_before / holds_after (the dynamic plan's tally), rounds."""
    opt = dict(DEFAULTS, **(opt or {}))
    B = ctx.B
    if B.sc.resolve(F.R_ + GROUP):
        raise ValueError('%s: the build already has %s (run this step on the bots build, not on its result)' % (ctx.folder, GROUP))
    fs = forms(B, ctx.boxes, opt['models'], opt['borrow'])
    log('%s: %d cover boxes (%d the game makes covers of); box models a new box may take (--models %s): %d - low %s, high %s'
        % (ctx.folder, len(ctx.boxes), len(ctx.covers), opt['models'], len(fs),
           sorted('%dx%dx%d' % (f['size'][0], f['size'][1], f['size'][2]) for f in fs if LOW_Y[0] <= f['size'][1] < LOW_Y[1]) or 'none',
           sorted('%dx%dx%d' % (f['size'][0], f['size'][1], f['size'][2]) for f in fs if HIGH_Y[0] <= f['size'][1] < HIGH_Y[1]) or 'none'))
    log('static collision: %d triangles of the map (left out: %s)' % (len(ctx.solid.tris), dict(ctx.solid.skipped)))
    new, rounds, first, tally, ms = [], [], None, None, []
    why = {}
    for rnd in range(int(opt['rounds']) + 1):
        tally, ms = asks(ctx)
        if first is None:
            first = dict(tally)
        rounds.append({'asked': tally.get('asked', 0), 'found': tally.get('found', 0), 'places_without': len(ms), 'boxes': len(new)})
        log('round %d: %d holds asked, %d found; %d places without one; %d new boxes so far' % (rnd, tally.get('asked', 0), tally.get('found', 0), len(ms), len(new)))
        if rnd == int(opt['rounds']):
            break
        added = 0
        for m in ms:
            g = ctx.solid.floor(*m['at'])
            m['ground'] = m['at'][1] if g is None else round(g, 1)
            here = 0
            for o in sorted(objects(ctx.solid, B, m['at'][0], m['ground'], m['at'][2], opt['near']), key=lambda o: o['dist']):
                key = (o['ref'], round(o['rect'][0] / 50), round(o['rect'][1] / 50)) if 'rect' in o else None
                if o['no']:
                    continue
                got = consider(ctx, m, o, fs, new, opt['near'])
                if isinstance(got, str):
                    why[(tuple(m['at']), key)] = got
                    continue
                got['via'] = 'object'
                got['name'] = 'CoverBox%s%s%02d' % ('H' if got['kind'] == 'high' else 'M', TAG, 1 + sum(c['kind'] == got['kind'] for c in new))
                new.append(got)
                ctx.covers.append({'node': 0, 'at': tuple(got['origin']), 'kind': got['kind'], 'hidden': False})
                added += 1; here += 1
            if here or not opt['corners']:
                continue
            # no object: the nearest corner of a wall, a building, a wide pillar (one box a place and round)
            for cn in sorted(corners(ctx.solid, B, m['at'][0], m['ground'], m['at'][2], opt['corner_near']), key=lambda c: c['dist']):
                got = consider_corner(ctx, m, cn, fs, new)
                if isinstance(got, str):
                    why[(tuple(m['at']), 'corner', round(cn['at'][0] / 20), round(cn['at'][1] / 20))] = got
                    continue
                got['name'] = 'CoverBox%s%s%02d' % ('H' if got['kind'] == 'high' else 'M', TAG, 1 + sum(c['kind'] == got['kind'] for c in new))
                new.append(got)
                ctx.covers.append({'node': 0, 'at': tuple(got['origin']), 'kind': got['kind'], 'hidden': False})
                added += 1
                break
        if not added:
            break
    # what is left: per place what stands there and why it got no box
    gaps = []
    for m in ms:
        g = ctx.solid.floor(*m['at'])
        m['ground'] = m['at'][1] if g is None else round(g, 1)
        objs = objects(ctx.solid, B, m['at'][0], m['ground'], m['at'][2], opt['near'])
        reasons = collections.Counter()
        for o in objs:
            key = (o['ref'], round(o['rect'][0] / 50), round(o['rect'][1] / 50)) if 'rect' in o else None
            reasons[o['no'] or why.get((tuple(m['at']), key)) or HELD] += 1
        near_new = [c['name'] for c in new if math.hypot(c['mid'][0] - m['at'][0], c['mid'][2] - m['at'][2]) < D.REACH]
        solid = [o for o in objs if not o['no']]
        cns = corners(ctx.solid, B, m['at'][0], m['ground'], m['at'][2], opt['corner_near']) if opt['corners'] else []
        creasons = collections.Counter(why.get((tuple(m['at']), 'corner', round(cn['at'][0] / 20), round(cn['at'][1] / 20))) or HELD for cn in cns)
        gaps.append({'at': m['at'], 'ground': m['ground'], 'why': m['why'], 'role': m['role'], 'solid_objects': len(solid), 'new_boxes_in_reach': near_new,
                     'what_stands_there': dict(reasons), 'corners': len(cns), 'corners_why': dict(creasons),
                     'open_ground': not solid and not cns and not any('wall' in k for k in reasons)})
    del ctx.covers[ctx.real:]
    ctx._spots.clear()
    if len(ctx.covers) + len(new) > 5000:
        raise ValueError('%d cover boxes: over the 5,000 the game\'s list takes' % (len(ctx.covers) + len(new)))
    P = collections.OrderedDict(folder=ctx.folder, options=opt, boxes=new, gaps=gaps, rounds=rounds, holds_before=first, holds_after=dict(tally),
                                models=[{k: (list(v) if isinstance(v, tuple) else v) for k, v in f.items()} for f in fs])
    describe(P, log)
    return P


def clusters(gaps, r=1000.0):
    """The gap places joined up (within r of one another) -> [(middle, [gap])], most places first."""
    left, out = list(gaps), []
    while left:
        grp, todo = [left.pop()], None
        grew = True
        while grew:
            grew = False
            for g in list(left):
                if any(math.hypot(g['at'][0] - h['at'][0], g['at'][2] - h['at'][2]) <= r and abs(g['at'][1] - h['at'][1]) < 300 for h in grp):
                    left.remove(g); grp.append(g); grew = True
        out.append(([sum(g['at'][i] for g in grp) / len(grp) for i in range(3)], grp))
    return sorted(out, key=lambda c: -len(c[1]))


def describe(P, log=print):
    new = P['boxes']
    log('new cover boxes: %d (%d low, %d high; %d on objects, %d at corners; form a %d, form b %d)'
        % (len(new), sum(c['kind'] == 'low' for c in new), sum(c['kind'] == 'high' for c in new), sum(c.get('via') != 'corner' for c in new),
           sum(c.get('via') == 'corner' for c in new), sum(c['tier'] == 'a' for c in new), sum(c['tier'] == 'b' for c in new)))
    for c in new:
        if c.get('via') == 'corner':
            k = c['corner']
            what = 'at a corner of %s (%s; faces %d and %d long, solid %d deep behind the face; the bot walks on toward %+.2f %+.2f)' \
                % (c['object'].split('\\')[-1], 'a wall end %d thick' % k['thick'] if k['kind'] == 'end' else 'two faces meet',
                   k['face_length'], k['other_face_length'], k['depth'], *k['way'])
        else:
            what = 'on %s (%d x %d)' % (c['object'].split('\\')[-1], 2 * c['object_rect'][4], 2 * c['object_rect'][5])
        log('  %-18s %-4s at (%6d %5d %6d) %3d x %3d, %3d high, %s; model %d of %s; asked from (%d, %d, %d)'
            % (c['name'], c['kind'], *c['mid'], *c['ext'], c['height'], what, c['model'], c['form'].split('\\')[-1], *c['ask']))
    a, b = P['holds_before'], P['holds_after']
    log('holds found / asked by the dynamic step\'s plan: %d / %d before -> %d / %d with the boxes' % (a.get('found', 0), a.get('asked', 0), b.get('found', 0), b.get('asked', 0)))
    gaps = P['gaps']
    log('places still without a hold: %d' % len(gaps))
    for mid, grp in clusters(gaps):
        rs, cr = collections.Counter(), collections.Counter()
        for g in grp:
            rs.update(g['what_stands_there'])
            cr.update(g.get('corners_why', {}))
        opn = sum(g['open_ground'] for g in grp)
        log('  round (%6d %5d %6d): %2d place(s), %d of them with NOTHING solid within %d m and no corner within %d m; what stands there: %s; corners: %s'
            % (*mid, len(grp), opn, P['options']['near'] / 100, P['options'].get('corner_near', 0) / 100, dict(rs.most_common(5)) or 'nothing',
               dict(cr.most_common(5)) or 'none'))


# ------------------------------------------------------------------ writing
def _node(M, B, k, name):
    sc, n = B.sc, B.sc.nodes[k]
    node = F.Node(name, sc.tids[k], M.adopt(n['props'], sc.p.keys), [], B.ents[k - 1])
    node.model = B.ents[k - 1].model
    return node


def group_form(B):
    """The build's first plain top-level group at the origin: no controller, no list, no raw data, pool group 0."""
    sc = B.sc
    for t in sc.tops():
        e = B.ents[t - 1]
        if sc.cls(t) == 'ZGROUP' and not sc.nodes[t]['ctrls'] and e.flags == 0x3000000 and not e.aux and e.links is None and e.raw is None \
                and not e.group and e.model == 0 and B.at(t) == (0.0, 0.0, 0.0) and list(B.values(t)['ZGEOM[1]']) == F.rot9(0.0, 1.0):
            return t
    raise ValueError('no plain top-level group to take the form of')


def box_corners(c):
    """World corners of a planned box (from its origin, heading and its model's box)."""
    hx, hz = c['head']
    xa = (hz, -hx)
    lo, hi = c['bb'][:3], c['bb'][3:]
    return [(c['origin'][0] + x * xa[0] + z * hx, c['origin'][1] + y, c['origin'][2] + x * xa[1] + z * hz)
            for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


def _tree(items):
    """[(slot id, lo, hi)] in the world -> a tree in a frame of its own (the items in the middle half of the 16-bit
    range, as kl_octree.join_trees lays a new frame out). build_tree() in ANOTHER tree's frame would clamp a box that
    lies outside that frame's range without a word; join_trees() then picks a frame that holds both."""
    lo = [min(i[1][k] for i in items) for k in range(3)]
    hi = [max(i[2][k] for i in items) for k in range(3)]
    half = max(max(hi[k] - lo[k] for k in range(3)) / 2.0, 1.0)
    return O.build_tree(items, tuple(O._f32((lo[k] + hi[k]) / 2.0) for k in range(3)), O._f32(16000.0 / half))


def apply(ctx, P, dst, log=print):
    """Write the plan's boxes into a copy of the build in folder dst -> report dict."""
    B, sc = ctx.B, ctx.B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if not P['boxes']:
        raise ValueError('no box to add')
    before = F.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']

    M = F.Maker()
    gk = group_form(B)
    grp = _node(M, B, gk, GROUP)
    M.place(grp, (0.0, 0.0, 0.0))
    pts = []
    for c in P['boxes']:
        n = grp.add(_node(M, B, c['form_node'], c['name']))
        M.place(n, c['origin'], F.rot9(*c['head']))
        if c.get('borrowed'):                           # the clone with another object's box primitive (forms())
            M.set(n, None, {'ZGEOM[4]': c['model']})
            n.model = c['model']
        if n.model != c['model'] or n.links is not None or n.flags not in (0x200, 0x302):
            raise ValueError('%s: not the form that was planned' % c['name'])
        c['bb'] = list(struct.unpack_from('<6f', _root(prm, c['model']), 0x20))
        pts += box_corners(c)
    q, order = M.scene([grp])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'cover')
    data = Jn.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made = nxt, {}
    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for k in n.kids:
            ent(k, e)
    ent(grp, None)
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
    moved = sum(1 for a, b in ids.items() if a != b)
    # the group in the root's group tree with the box of its children (the form group is listed there; kl_fa_bots
    # lists its squads the same way). The boxes themselves are in no room tree, as the boxes they are clones of.
    root3, root0 = octn.rooms[0][3], octn.rooms[0][0]
    listed = repointed = listed0 = 0
    new_prm = None
    form_listed = root3 is not None and slot0[B.ents[gk - 1]] + 2 in {it[0] for it in octx.rooms[0][3].items}
    items0 = []
    for c, n in zip(P['boxes'], grp.kids):              # tier a: flags 0x302 = in a tree, with a collision record
        if c['tier'] == 'a':
            cs = box_corners(c)
            items0.append((slot1[made[id(n)]] + 2, tuple(min(p[a] for p in cs) for a in range(3)), tuple(max(p[a] for p in cs) for a in range(3))))
    if items0:
        if root0 is None:
            raise ValueError('the root has no tree 0 to list the boxes in')
        octn.rooms[0][0] = O.join_trees(root0, _tree(items0))
        octn.rooms[0][0].check()
        listed0 = len(items0)
    if form_listed:
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3))
        hi = tuple(max(p[a] for p in pts) + 10.0 for a in range(3))
        octn.rooms[0][3] = O.join_trees(root3, _tree([(slot1[made[id(grp)]] + 2, lo, hi)]))
        octn.rooms[0][3].check()
        listed = 1
    if form_listed or items0:
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            pm = bytearray(prm)
            t, n = struct.unpack_from('<II', pm, 0)
            old = set(octx.record_refs())
            for i in range(1, n):
                o, size = struct.unpack_from('<II', pm, t + 16 * i)
                if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(pm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'cover.', 'cover_map')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    rep = collections.OrderedDict(
        source=B.folder, out=dst, members_changed=changed, entities_before=len(B.ents), entities=len(ents), entities_added=len(order),
        group=GROUP, group_form=sc.path[gk][5:], group_listed_in_root_tree_3=listed, boxes_listed_in_root_tree_0=listed0, ref_ids='%d..%d' % (ref0, nxt - 1), ref_slots=[B.scene.ref_slots, nxt],
        slot_ids_moved=moved, prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post,
        big_before=before, big_after=after)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):                              # kl_maps.audit compares the folder with what was measured
        import kl_maps
        st = json.load(open(sj))
        st['cover'] = changed
        st['bots'] = sorted(set(st.get('bots') or []) | set(changed))
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_cover: %d cover boxes (%d low, %d high) on solid objects where the AI heisters found no cover, group %s, from %s; options %s\n'
                % (len(P['boxes']), sum(c['kind'] == 'low' for c in P['boxes']), sum(c['kind'] == 'high' for c in P['boxes']), GROUP, B.folder,
                   json.dumps(P['options'], sort_keys=True)))
    log('written %s: %d entities added (1 ZGROUP, %d ZSTDOBJ), REF ids %s; members changed: %s; %d slot ids renumbered; the group listed in the '
        'root\'s group tree: %s; %d boxes (tier a) listed in the root\'s tree 0; %d model roots of the .prm re-pointed at their moved .oct records'
        % (zp, len(order), len(order) - 1, rep['ref_ids'], ' '.join(changed), moved, 'yes' if listed else 'no (its form is not)', listed0, repointed))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    if before != after:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    return rep


# ------------------------------------------------------------------ checks
def check(folder, log=print):
    """The boxes of this step in a built folder -> [(severity, text)]. FAIL must be none."""
    out = []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    B = F.Built(folder)
    sc = B.sc
    cj = os.path.join(B.folder, 'cover.json')
    plan_ = json.load(open(cj)).get('plan') if os.path.isfile(cj) else None
    g = sc.resolve(F.R_ + GROUP)
    if len(g) != 1:
        fail('%d groups %s' % (len(g), GROUP))
        for s, t in out:
            log('%s  %s' % (s, t))
        return out
    g = g[0]
    mine = [k for k in range(g + 1, sc.end[g])]
    boxes = all_boxes(B)
    by = {c['node']: c for c in boxes}
    others = [c for c in boxes if c['node'] not in mine]
    S = Solid(B)
    nocover = [k for k in range(1, len(sc.nodes)) if kl_fa.has(sc, k, 'NoCoverBox') and sc.cls(k) == 'ZBoxPrimitive']
    nav = F.Nav(B.scene.nav)
    exits = F.stations(B, nav)['exits']
    lane = F.lanes(B)
    octx = O.Oct.parse(B['.oct'])
    slot = B.scene.slots()
    listed = collections.Counter(it[0] for room in octx.rooms for t in room if t is not None for it in t.items)
    root0 = {it[0] for it in octx.rooms[0][0].items} if octx.rooms[0][0] is not None else set()
    root3 = {it[0] for it in octx.rooms[0][3].items} if octx.rooms[0][3] is not None else set()
    if sc.cls(g) != 'ZGROUP' or sc.nodes[g]['ctrls'] or sc.parent[g] != 0 or B.at(g) != (0.0, 0.0, 0.0):
        fail('%s is not a plain top-level group at the origin' % GROUP)
    if root3 and slot[B.ents[g - 1]] + 2 not in root3:
        note('%s is not in the root\'s group tree' % GROUP)
    models = collections.Counter(c['model'] for c in others if c['cls'] == 'ZSTDOBJ')
    forms_ = {c['model']: c for c in others if c['cls'] == 'ZSTDOBJ'}
    planned = {c['name']: c for c in (plan_ or {}).get('boxes', [])}
    seen = set()
    n_high = n_low = n_a = n_lent = 0
    for k in mine:
        nm, e, c = sc.names[k], B.ents[k - 1], by.get(k)
        low = nm.lower()
        if sc.parent[k] != g or c is None or sc.cls(k) != 'ZSTDOBJ' or TAG.lower() not in low or c['kind'] not in ('high', 'low'):
            fail('%s: not a cover box of this step (class %s)' % (nm, sc.cls(k))); continue
        if nm in seen:
            fail('%s: the name is there twice' % nm)
        seen.add(nm)
        n_high += c['kind'] == 'high'; n_low += c['kind'] == 'low'
        src = forms_.get(e.model)
        pl = planned.get(nm) or {}
        if pl.get('form_node') in by and by[pl['form_node']]['cls'] == 'ZSTDOBJ' and B.ents[pl['form_node'] - 1].model == e.model:
            src = by[pl['form_node']]       # the box this one was cloned from (several boxes share a model and differ in ZSTDOBJ[0])
        lent = False
        if src is None and pl.get('borrowed'):
            # a borrowed box primitive: the box is a clone of the cover box cover.json names, with the model of the
            # object it names; that model must be what forms() asks of one
            hit = sc.resolve(F.R_ + pl['form'])
            own = sc.resolve(F.R_ + pl['borrowed'])
            src = by.get(hit[0]) if len(hit) == 1 else None
            lent = len(own) == 1 and B.ents[own[0] - 1].model == e.model and sc.cls(own[0]) == 'ZSTDOBJ'
            if src is None or not lent:
                fail('%s: its borrowed model %d is not that of %s, or its form %s is not there' % (nm, e.model, pl['borrowed'], pl['form'])); continue
            n_lent += 1
        if src is None:
            fail('%s: model %d is no other cover box\'s' % (nm, e.model)); continue
        se = B.ents[src['node'] - 1]
        if (e.flags, e.group, e.aux, e.raw, e.links, e.tid) != (se.flags, se.group, se.aux, se.raw, se.links, se.tid) or sc.nodes[k]['ctrls'] or sc.nodes[src['node']]['ctrls']:
            fail('%s: its record is not that of the box it is a clone of (%s)' % (nm, src['name']))
        va, vb = B.values(k), B.values(src['node'])
        skip = ('ZGEOM[1]', 'ZGEOM[2]', 'ZGEOM[4]') if lent else ('ZGEOM[1]', 'ZGEOM[2]')
        if {f: v for f, v in va.items() if f not in skip} != {f: v for f, v in vb.items() if f not in skip}:
            fail('%s: a property other than place and rotation differs from %s' % (nm, src['name']))
        if va.get('ZGEOM[4]') != e.model:
            fail('%s: .prp and .gms disagree on its model (%s, %d)' % (nm, va.get('ZGEOM[4]'), e.model))
        if lent and (c['bb'] is None or c['octrec']):
            fail('%s: its borrowed model has a collision record or no plain root' % nm)
        if e.flags not in (0x200, 0x302) or e.flags & 0x400:
            fail('%s: flags %#x' % (nm, e.flags))
        if (e.flags == 0x200) != (not c['octrec']):
            fail('%s: flags %#x on a model %s a collision record' % (nm, e.flags, 'with' if c['octrec'] else 'without'))
        if e.flags == 0x302:
            n_a += 1
            if listed[slot[e] + 2] != 1 or slot[e] + 2 not in root0:
                fail('%s (flags 0x302) is not listed once, in the root\'s tree 0' % nm)
        elif listed[slot[e] + 2]:
            fail('%s (flags 0x200) is listed in a room tree' % nm)
        r9 = struct.unpack('<9f', e.rot[:36])
        if any(abs(math.sqrt(sum(v * v for v in r9[i:i + 3])) - 1.0) > 1e-4 for i in (0, 3, 6)) or abs(r9[4] - 1.0) > 1e-5:
            fail('%s: its matrix is scaled or tilted' % nm)
        if list(va['ZGEOM[2]']) != list(struct.unpack('<3f', e.trans[:12])) or list(va['ZGEOM[1]']) != list(r9):
            fail('%s: .prp and .gms disagree on its place' % nm)
        bb, mid = c['bb'], c['mid']
        kind_y = HIGH_Y if c['kind'] == 'high' else LOW_Y
        if not kind_y[0] <= bb[4] - bb[1] < kind_y[1]:
            fail('%s: a %s box %d high' % (nm, c['kind'], bb[4] - bb[1]))
        p = planned.get(nm)
        if plan_ is not None and (p is None or math.dist(p['mid'], mid) > 1.0):
            fail('%s: not where cover.json planned it' % nm)
        ground = mid[1] - (bb[4] - bb[1]) / 2
        cs = [B.world(k, (x, bb[1] + 50.0, z)) for x in (bb[0], bb[3]) for z in (bb[2], bb[5])] + [(mid[0], ground + 50.0, mid[2])]
        for j in nocover:
            if any(B.in_box(j, q) for q in cs):
                fail('%s is inside the NoCoverBox %s' % (nm, sc.names[j]))
        if any(F.in_exit(B, exits, q) for q in cs):
            fail('%s is in a level exit box' % nm)
        if lane and min(F.lane_dist(lane, q) for q in cs) < F.LANE_CLEAR:
            fail('%s is within %d of the escape vehicle\'s road (%d)' % (nm, F.LANE_CLEAR, min(F.lane_dist(lane, q) for q in cs)))
        near = [o for o in others if o['cls'] == 'ZSTDOBJ' and o['kind'] is not None            # (a 'NoCoverBox' is no cover box: the test above)
                and math.hypot(o['mid'][0] - mid[0], o['mid'][2] - mid[2]) < APART - 1 and abs(o['mid'][1] - mid[1]) < 200]
        if near:
            fail('%s stands within %d of the cover box %s' % (nm, APART, near[0]['name']))
        # is something solid in it? the BASE plane over its foot: static collision inside its footprint
        occ, _segs = S.scan(mid[0], ground, mid[2], 500.0)
        hx, hz = r9[0], r9[2]                           # local Z in the world (kl_fa_bots.rot9); local X = (hz, -hx)
        inside = 0
        for r, cells in occ[BASE].items():
            for cell in cells:
                dx, dz = (cell[0] + 0.5) * CELL - mid[0], (cell[1] + 0.5) * CELL - mid[2]
                lz, lx = dx * hx + dz * hz, dx * hz - dz * hx
                if abs(lx) <= (bb[3] - bb[0]) / 2 + CELL and abs(lz) <= (bb[5] - bb[2]) / 2 + CELL:
                    inside += 1
        if inside < 4 and not (planned.get(nm) or {}).get('freeside'):      # (a free-side tile, kl_cover_1026 FREESIDE 2026-10-26, stands on clear floor in front of its wall on purpose)
            fail('%s: no static collision in its footprint %d over its foot (thin air)' % (nm, BASE))
    if plan_ is not None and len(planned) != len(mine):
        fail('%d boxes in the build, %d in cover.json' % (len(mine), len(planned)))
    total = sum(1 for c in boxes if c['cls'] == 'ZSTDOBJ')
    if n_lent:
        note('%d of the boxes have the box primitive of an object that is no cover box (the 100 cube of F07\'s camera objects): ASSUMPTION (--no-borrow leaves them out)' % n_lent)
    if n_a:
        note('%d of the boxes are clones of boxes with a collision record (flags 0x302), listed in the root\'s tree 0: ASSUMPTION (--models b leaves them out)' % n_a)
    bad = F.room_sets_check(B.scene, octx, O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc']))
    known = (plan_ and json.load(open(cj)).get('slot_id_faults_before')) or []
    if bad != known:
        fail('slot ids of the room trees / room index: %s (the source build: %s)' % (bad, known))
    if total > 5000:
        fail('%d cover boxes: over the game\'s 5,000' % total)
    if plan_ is not None:
        want = json.load(open(cj)).get('big_after')
        if want and dict(F.sizes(B.folder)) != dict(want):
            fail('a large block is not the size cover.json recorded: %s' % dict(F.sizes(B.folder)))
    for s, t in out:
        log('%s  %s' % (s, t))
    log('cover boxes of this step: %d (%d low, %d high) below %s; %d cover boxes in all (the game takes 5,000)' % (len(mine), n_low, n_high, GROUP, total))
    log('RESULT: %s (%d FAIL, %d NOTE)' % ('FAIL' if any(s == 'FAIL' for s, _t in out) else 'PASS', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out)))
    return out


def diff(src, dst, log=print):
    """What differs between the bots build and this step's result -> list of UNEXPECTED differences (must be empty).
    Expected: one more top-level subtree, the last (the group and its boxes); the group in the root's group tree;
    slot ids that name the same entities; .oct record offsets in the .prm's model roots; the REF slot count."""
    A, Bn = F.Built(src), F.Built(dst)
    bad = []
    sa, sb = A.sc, Bn.sc
    ta, tb = sa.tops(), sb.tops()
    if [sa.names[t] for t in ta] + [GROUP] != [sb.names[t] for t in tb]:
        bad.append('the top-level subtrees are not the old ones + %s at the end' % GROUP)
    fa, fb = J.fingerprints(sa), J.fingerprints(sb)
    differ = [sa.names[t] for t, u in zip(ta, tb) if fa[t] != fb[u]]
    if differ:
        bad.append('.prp: old top-level subtrees differ: %s' % differ[:5])
    if J.text(sa, sa.p.settings) != J.text(sb, sb.p.settings):
        bad.append('.prp: the scene property block differs')
    key = lambda e: (e.name, e.tid, e.flags, e.group, e.model, e.rot, e.trans, e.raw, e.aux, e.ref)
    n0 = len(A.ents)
    if [key(e) for e in A.ents] != [key(e) for e in Bn.ents[:n0]]:
        bad.append('.gms: an old entity differs (record, order or REF id)')
    extra = Bn.ents[n0:]
    if not extra or extra[0].name.decode('latin1') != GROUP or any(e.parent is not extra[0] for e in extra[1:]):
        bad.append('.gms: the new entities are not %s and its children' % GROUP)
    refs = [e.ref for e in Bn.ents]
    if len(set(refs)) != len(refs) or max(refs) >= Bn.scene.ref_slots:
        bad.append('.gms: two entities share a REF id, or one is over the REF slot count')
    ia = {e: i for i, e in enumerate(A.ents)}
    ib = {e: i for i, e in enumerate(Bn.ents)}
    links = lambda X, ix: [(ix[e], [(None if t is None else ix[t], b) for t, b in e.links]) for e in X.ents if e.links]
    if links(A, ia) != links(Bn, ib):
        bad.append('.gms: the light lists differ')
    if [(a and ia[a], ia[b]) for a, b in A.scene.pairs] != [(a and ib[a], ib[b]) for a, b in Bn.scene.pairs]:
        bad.append('room pairs differ')
    if (A.scene.head, A.scene.tail, A.scene.dyn, A.scene.tags, A.scene.budget, A.scene.fdx, A.scene.nav) != \
            (Bn.scene.head, Bn.scene.tail, Bn.scene.dyn, Bn.scene.tags, Bn.scene.budget, Bn.scene.fdx, Bn.scene.nav):
        bad.append('.buf head / tail, dynamic list, tags, heap budget, FDX or the navigation mesh differ')
    log('.prp: the %d old top-level subtrees equal, %s added last; scene property block equal' % (len(ta), GROUP))
    log('.gms / .buf: %d old entities as they were (record, order, REF id); %d new (%s + %d boxes); REF slots %d -> %d; head, surface table, '
        'dynamic list, heap budget, navigation mesh equal' % (n0, len(extra), GROUP, len(extra) - 1, A.scene.ref_slots, Bn.scene.ref_slots))
    def trees(L, ix):
        by = {s + 2: ix[e] for e, s in L.scene.slots().items()}
        by[1] = '<root>'
        o = O.Oct.parse(L['.oct'])
        sets = [[None if t is None else (t.origin, t.scale, sorted((str(by.get(it[0], 'gone')), t.world(it[1:4]), t.world(it[4:7])) for it in t.items)) for t in room] for room in o.rooms]
        idx = [[(b.raw[:0x4c], by.get(b.room, 'gone'), by.get(b.second, 'gone') if b.second else 0) for b in O.RoomIndex.parse(L[e]).boxes] for e in ('.rmi', '.rmc')]
        return o, sets, idx
    oa_, sa_, xa = trees(A, ia)
    ob_, sb_, xb = trees(Bn, ib)
    grew = grew0 = 0
    for r, (ra, rb) in enumerate(zip(sa_, sb_)):
        for t, (x, y) in enumerate(zip(ra, rb)):
            if x == y:
                continue
            if (r, t) == (0, 3) and x and y:
                na, nb = collections.Counter(i[0] for i in x[2]), collections.Counter(i[0] for i in y[2])
                if nb - na != collections.Counter([str(n0)]) or na - nb:
                    bad.append('.oct: the root\'s group tree changed by more than the new group')
                grew = 1
            elif (r, t) == (0, 0) and x and y:
                na, nb = collections.Counter(i[0] for i in x[2]), collections.Counter(i[0] for i in y[2])
                want = collections.Counter(str(n0 + 1 + j) for j, e in enumerate(extra[1:]) if e.flags == 0x302)
                if nb - na != want or na - nb:
                    bad.append('.oct: the root\'s tree 0 changed by more than the new boxes with a collision record')
                grew0 = sum(want.values())
            else:
                bad.append('.oct: room set %d tree %d differs' % (r, t))
    if len(sa_) != len(sb_) or xa != xb:
        bad.append('.oct room sets or .rmi / .rmc boxes differ by entity')
    if [r.pack() for r in oa_.records] != [r.pack() for r in ob_.records] or oa_.tail != ob_.tail:
        bad.append('.oct collision records or tail differ')
    log('.oct: %d room sets, every item names the entity it named; the root\'s group tree has %d more item (the group), its tree 0 %d more (boxes with a '
        'collision record); %d collision records and the tail equal; .rmi / .rmc: %d + %d boxes name the rooms they named'
        % (len(sa_), grew, grew0, len(oa_.records), len(xa[0]), len(xa[1])))
    pa_, pb_ = A['.prm'], Bn['.prm']
    cells = 0
    if pa_ != pb_:
        if len(pa_) != len(pb_):
            bad.append('.prm: size differs')
        else:
            move = dict(zip(oa_.record_refs(), ob_.record_refs()))
            t, cnt = struct.unpack_from('<II', pa_, 0)
            spans = 0
            for i in range(1, cnt):
                o, size = struct.unpack_from('<II', pa_, t + 16 * i)
                if pa_[o:o + size] != pb_[o:o + size]:
                    va, vb = struct.unpack_from('<I', pa_, o + 0x1c)[0], struct.unpack_from('<I', pb_, o + 0x1c)[0]
                    if size != 64 or pa_[o:o + 0x1c] != pb_[o:o + 0x1c] or pa_[o + 0x20:o + 64] != pb_[o + 0x20:o + 64] or move.get(va) != vb:
                        spans += 1
                    cells += 1
            if spans or pa_[t:] != pb_[t:] or pa_[:16] != pb_[:16]:
                bad.append('.prm: %d chunks differ in more than their .oct record offset, or the table differs' % spans)
    log('.prm: %s' % ('byte for byte' if pa_ == pb_ else '%d model roots differ, each only in its .oct record offset (+0x1c), old record -> the same record' % cells))
    rest = [e for e in A.ext if e not in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm') and A[e] != Bn[e]]
    if rest or A.order != Bn.order:
        bad.append('other members differ: %s' % rest)
    skip = ('audit.', 'cover.', 'cover_map', 'dyn.', 'dyn_map', 'steps.json', 'graft.txt', F.SLOT + '_Main.zip')
    side = [f for f in os.listdir(A.folder) if os.path.isfile(os.path.join(A.folder, f)) and not f.startswith(skip)]
    def same_file(a, b):
        if not os.path.isfile(b) or os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, 'rb') as fa_, open(b, 'rb') as fb_:
            while True:
                x, y = fa_.read(1 << 22), fb_.read(1 << 22)
                if x != y:
                    return False
                if not x:
                    return True
    sdiff = [f for f in side if not same_file(os.path.join(A.folder, f), os.path.join(Bn.folder, f))]
    if sdiff:
        bad.append('files beside the archive differ: %s' % sdiff)
    log('the other %d members byte for byte; %d files beside the archive byte for byte (%s; steps.json and graft.txt get a line of this step)'
        % (len(A.ext) - 7, len(side), ', '.join(f for f in side if f.endswith('.ini')) or 'no .ini'))
    for x in bad:
        log('UNEXPECTED: ' + x)
    log('RESULT: %s' % ('only the cover group was added' if not bad else '%d unexpected differences' % len(bad)))
    return bad


def build(src, dst, opt=None, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    say('kl_fa_cover build %s -> %s' % (src, dst))
    ctx = Ctx(src, say)
    P = plan(ctx, opt, say)
    rep = apply(ctx, P, dst, say)
    rep['plan'] = P
    with open(os.path.join(dst, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out = check(dst, say)
    bad = diff(src, dst, say)
    out = out + [('FAIL', 'diff: ' + x) for x in bad]
    rep.update(check=[list(x) for x in out], diff=bad)
    with open(os.path.join(dst, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'cover.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def options(a):
    opt = {}
    if '--no-corners' in a:
        a.remove('--no-corners'); opt['corners'] = False
    if '--no-borrow' in a:
        a.remove('--no-borrow'); opt['borrow'] = False
    for flag, key, conv in (('--models', 'models', str), ('--near', 'near', float), ('--rounds', 'rounds', int), ('--corner-near', 'corner_near', float)):
        if flag in a:
            i = a.index(flag)
            opt[key] = conv(a[i + 1]); del a[i:i + 2]
    if opt.get('models', 'b') not in ('b', 'ab'):
        sys.exit('--models b | ab')
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 2 and a[0] == 'plan':
        plan(Ctx(a[1]), opt)
    elif len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if any(s == 'FAIL' for s, _t in check(a[1])) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2]) else 0)
    elif len(a) >= 2 and a[0] == 'all':
        res = {}
        for sub, d in OWNER:
            if a[2:] and d not in a[2:] and not (d == 'retomoto_full' and 'retomoto' in a[2:]):
                continue
            print('==== %s: the cover step' % d)
            pre, fin = os.path.join(a[1], OUT, '_pre', d), os.path.join(a[1], OUT, d)
            out, _rep = build(os.path.join(a[1], sub, d), pre, opt)
            ok = not any(s == 'FAIL' for s, _t in out)
            if ok:
                print('==== %s: the dynamic step (random routes) on it' % d)
                out2, _r = D.build(pre, fin, None)
                ok = not any(s == 'FAIL' for s, _t in out2)
                if ok:
                    print('==== %s: the cover boxes in the dynamic build' % d)
                    ok = not any(s == 'FAIL' for s, _t in check(fin))
            res[d] = ok
        for k, v in res.items():
            print('%s: %s' % (k, 'PASS' if v else 'FAIL'))
        sys.exit(0 if res and all(res.values()) else 1)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
