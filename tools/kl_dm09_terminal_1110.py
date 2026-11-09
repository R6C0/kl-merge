#!/usr/bin/env python3
r"""kl_dm09_terminal_1110.py - DM09 Retomoto, optional variant TERMINAL (2026-11-10; owner 11-09: "extend it to the original mission where you
gotta go down the steps to the van all the way down").  (optional variant, recommended off until benched)

OFFLINE: reads the COVER stage (default C:\kl_build_1024\dm09cover_1110: F06_Main.zip, F06_Main.bots.zip, F06_Main.bots.base.md5) and writes only a stage
folder (default C:\kl_build_1024\dm09terminal_1110). Starts nothing, installs nothing, never touches the game folder.

    python kl_dm09_terminal_1110.py plan   [<cover stage>]          what would move (old -> new), nothing written
    python kl_dm09_terminal_1110.py stage  [<out>] [--no-rehearse] [--cover <cover stage>] [--game <DD folder>]
                                                                    both zips + base md5 + install.py + INSTALL/UNDO.bat + README.txt + ini fragment;
                                                                    rehearses install / 2nd refused / undo byte-exact in <out>_scratch (deleted afterwards)

THE VARIANT: the heisters leave the street through the west corridor (the walkable crossing of the street's west bound slab), cross the stairs overpass
(re/dm09_terminal_1109.md: 279 m, 49 polygons, 0 steep hops) and escape at the campaign's bus terminal instead of at the street stop.
What changes (values of EXISTING entities only: no entity is added, so no slot id moves and .oct / .rmi / .rmc stay byte-identical):
  1. THE VAN: F07's Escape_Vehicle_01 group (24871 'EscapeVehicle_Animation_F07'; PathBlockerVan, boarding box, cameras, KillBox, sounds are its children)
     is moved RIGIDLY by one translation, so its stop lands at (LANE_X, FLOOR_Y + 2, STOP_Z); the drive is a straight lane along +z (kl_fa_van.straighten),
     wait 2100 before the stop, end 10200 after it. The van group sits identity at the origin, so the translation is the group's new position.
  2. THE EXIT: otrExitLevel (OnlineExitLevelTrigger) box and POI_TheEscapeArea follow the stop; the two RunToEscape trigger boxes go to the approach side.
  3. THE WEST BOUND 030_LevelBound_StreetLeft (x -7500..-6500, z -2500..14000, was a wall for the whole west side) is SPLIT around the walkable crossing
     (read from the nav mesh: the corridor polygons that cross the slab and reach west of it, +/- GAP_PAD): the existing trio keeps the south part, the
     parked spare trio 030_LevelBound_StreetRight (at y -60000 in the cover stage) takes the north part.
  4. THE CAMPAIGN PEN: Enemies!040_Busterminal!LevelBound (5 boxes, Bound / Bound#01 / Bound#02 + Warn01 / Warn02, x -25212 +- 1000 around the campaign van) cut the lane
     (x -25500, z 7900..10158): Bound#01 / Bound#02 parked at (0, -60000, 0) like every unused trio (kl_fa_author.PARK); Bound + Warn01 + Warn02 are reused (item 5).
  5. THE TERMINAL'S WALLS (TERM_TRIOS, CORRIDOR): with the slab open and the pen gone the collision flood from the street reached 837,528 cells west of the street (the whole hall,
     x -35010..-13950, z -5410..29610). Four LevelBound walls (the three parked trios AlleyRight x2 / AlleyLeft + the pen trio, values only, no new entity) confine play to the street,
     the overpass + stairs corridor (CORRIDOR C1 / C2) and the lane at the van (C3); the check floods again with the bounds as walls and counts cells outside (want 0).
  The campaign's own van (V_USA_GetawayVan_Chase_00, (-24630,-979,8958)) and EndOfLevel (-24400,-929,8986) stay (8.7 m east of the lane, outside its swath).

NOT changed (listed in the report): the police ring squads / their trigger boxes stay on the street (they fight the crew on the way out); the cover exclusion belt
(NoCoverBox#19/#20) stays round the old stop; [BotFillWay_DM09] is Dog Days' KLHook.ini (peer-owned): a FRAGMENT is shipped, not applied; the hook sites
(OnlineVanPosSane, klescort exit walk, kl_fa_street lane nodes) are in README.txt as a plan.

GUESSes (each also on its line below): LANE_X / STOP_Z, EXIT box size, RUN box place, GAP_PAD, the spare trio reuses the StreetLeft LevelBound controller values
(AlleyRight / StreetRight are stock copies of the same trio), the terminal walls' extent (CORRIDOR margins, BOUND_Y, 600 cm thick, Warn = Bound + 300) and that a LevelBound reused from AlleyRight / AlleyLeft / the pen keeps its own Warn
references (stock trios), the van's drive-in is not run over a waiting crew (stock layout: same as the street).
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
COVER = r'C:\kl_build_1024\dm09cover_1110'
OUT = r'C:\kl_build_1024\dm09terminal_1110'
MAP, SLOT = 'DM09', 'F06'
FILES = ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5')
TAG_BAK = '.before-dm09terminal1110'
FREE_KEEP = 2 << 30

# ------------------------------------------------------------------ the numbers
LANE_X = -25500.0                  # GUESS: the van's stop x. Measured: floor y -980 +-6 and nothing taller than +250 over the 5-point swath (-25750..-25250) from z 5400 to 19000 (HVK, kl_escape.Walk)
STOP_Z = 8100.0                    # GUESS: the stop's z; wait = STOP_Z - 2100 (6000), end = STOP_Z + 10200 (18300) both inside the clear lane
FLOOR_Y = -980.0                   # the terminal floor (HVK / nav, measured)
EXIT_BEFORE, EXIT_AFTER = 2500.0, 2000.0        # as kl_fa_street (stock: box from 25 m before to 20 m after the stop)
EXIT_HALF_X = 1350.0               # GUESS: the street box was 2700 half-wide (the carriageway); the terminal floor beside the lane is narrower
EXIT_X_OFF = -150.0                # the box spans lane x -1500 .. +1200 = x -27000 .. -24300: its east edge stays WEST of the facade wall (x -24190..-24230), so the stair-landing pocket is outside it
BARRICADE_REFS = (23098,)          # PC0100_JPN_InvisibleBarricade01 (node 11045): a static box that plugs the only doorway of the facade wall between the stair landing and the van pen (found by a Walk flood, review 11-09)
EXIT_Y_OFF, EXIT_HALF_Y = 500.0, 900.0         # as the street box (centre floor + 500, half 900); the street floor was -40: centre 500 = floor + 540. GUESS here: floor + 500
POI_Y_OFF = 195.0                  # the street POI stood 150 over a -45 floor
RUN_BEFORE = 2800.0                # 28 m before the stop along the walk (kl_fa_street 'run': 28 m before the stop)
RUN_HALF = (300.0, 400.0, 2700.0)  # a 6 m thick slab, 54 m wide (the street box: half 2700 across the road); axis = the approach direction
RUN_Y_OFF = 345.0
SLAB_X = (-7500.0, -6500.0)        # StreetLeft Bound: centre -7000 half 500
SLAB_Z = (-2500.0, 14000.0)        # centre 5750, half 8250
SLAB_Y = (-1000.0, 2000.0)         # centre 500, half 1500
GAP_PAD = 150.0                    # GUESS: 1.5 m each side of the corridor's polygons
WARN_X = (-7500.0, -6200.0)        # Warn01 / Warn02: centre -6850, half 650
PARK = (0.0, -60000.0, 0.0)
ST_HALF_Y = 1500.0

WEST = 'Specials!LevelBound!030_LevelBound_StreetLeft!'
SPARE = 'Specials!LevelBound!030_LevelBound_StreetRight!'
PEN = 'Enemies!040_Busterminal!LevelBound!'
# The terminal's own bounds (measured by a collision flood, kl_escape.Walk, from the street mouth with the west slab open: 837k cells west of the street, the whole hall
# x -35010..-13950, z -5410..29610). PLAY AREAS: the street (as before), the overpass + stairs corridor, the terminal lane. Rectangles (x0, x1, z0, z1) in cm:
CORRIDOR = (
    (-15500.0, -6400.0, 6400.0, 14200.0),    # C1 the whole overpass plateau (flood: x -14150..-6510, z 6650..13910) + the stairs head
    (-26700.0, -13200.0, 6400.0, 14600.0),   # C2 the hall under the stairs to the lane (path z 7992..13723, hall floor z 6730..18310)
    (-27000.0, -24000.0, 5400.0, 10100.0),   # C3 the lane at the van stop (-25500, 8100) and wait (-25497, 6000)
)
BOUND_Y = (-1500.0, 600.0)            # the hall floor is y -1000, the lane -980: 5 m below to 6 m above
# The four walls of the hall, outside CORRIDOR. (trio, x0, x1, z0, z1, side of the allowed area the Warn boxes grow toward: (dx, dz))
# The three parked LevelBound trios are reused, plus the pen trio (Bound / Warn01 / Warn02; the pen's Bound#01 / Bound#02 stay parked). No new entity, so no slot renumbering.
TERM_TRIOS = (
    ('Specials!LevelBound!020_LevelBound_AlleyRight!', 'north', -27400.0, -12700.0, 14600.0, 15200.0, (0.0, -1.0)),
    ('Specials!LevelBound!040_LevelBound_AlleyRight!', 'west upper', -27400.0, -26700.0, 10100.0, 14600.0, (1.0, 0.0)),
    ('Specials!LevelBound!040_LevelBound_AlleyLeft!', 'west lane', -27400.0, -27000.0, 5000.0, 10100.0, (1.0, 0.0)),
    ('Enemies!040_Busterminal!LevelBound!', 'south', -27000.0, -23600.0, 5000.0, 5400.0, (0.0, 1.0)),
)
WARN_GROW = 300.0                      # stock: Warn = the Bound grown ~3 m toward the allowed side
RUN_BOXES = ('Gameplay!RunToEscape!tbRunToEscape1Player', 'Gameplay!RunToEscape!tbRunToEscape')
OLD_STOP = (-1853.236083984375, 2.0, 10800.0)    # kl_fa_street.van_pose of the cover stage (read again at build time; asserted equal)


# ------------------------------------------------------------------ pure logic (kl_dm09_terminal_1110_test.py)
def lane_delta(stop, target_x, target_z, floor_y):
    """The rigid translation that puts the van's stop (x, y, z) at (target_x, y + floor_y, target_z): y is lifted by the floor (the drive is baked on a y = 0 floor)."""
    return (target_x - stop[0], floor_y, target_z - stop[2])


def to_box(x0, x1, y0, y1, z0, z1):
    """(centre, half) of an axis-aligned box."""
    return (((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))


def corridor_gap(boxes, nb, allowed, x0, x1, ylo, yhi, pad, zr=None):
    """The z range (lo, hi) of the nav corridor that crosses the slab x0..x1: polygons of `allowed` (the street's reachable component) whose box overlaps the slab
    in x and whose height (box[4]) is within ylo..yhi, that reach west of the slab (box[0] < x0) or are joined to one that does through other such polygons.
    boxes[i] = (xmin, xmax, zmin, zmax, y). nb[i] = neighbour polygon ids. None when no polygon crosses."""
    inside = {i for i in allowed if boxes[i] and boxes[i][1] >= x0 and boxes[i][0] <= x1 and ylo <= boxes[i][4] <= yhi
              and (zr is None or (boxes[i][3] >= zr[0] and boxes[i][2] <= zr[1]))}   # zr = the slab's own z range: polygons elsewhere (far-off areas) are not this crossing
    seeds = [i for i in inside if boxes[i][0] < x0]
    seen, st = set(seeds), list(seeds)
    while st:
        for j in nb[st.pop()]:
            if j in inside and j not in seen:
                seen.add(j); st.append(j)
    if not seen:
        return None
    return (min(boxes[i][2] for i in seen) - pad, max(boxes[i][3] for i in seen) + pad)


def in_corridor(x, z, rects=CORRIDOR):
    return any(a <= x <= b and c <= z <= d for a, b, c, d in rects)


def warn_rect(x0, x1, z0, z1, side, grow=WARN_GROW):
    """The Warn box of a wall: the wall grown by `grow` toward the allowed side (dx, dz)."""
    dx, dz = side
    return (x0 - (grow if dx < 0 else 0.0), x1 + (grow if dx > 0 else 0.0), z0 - (grow if dz < 0 else 0.0), z1 + (grow if dz > 0 else 0.0))


def rects_overlap(a, b):
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def slab_split(z0, z1, gap):
    """The slab's z range (z0, z1) minus the gap (g0, g1) -> (south part or None, north part or None)."""
    g0, g1 = gap
    south = (z0, min(g0, z1)) if g0 > z0 else None
    north = (max(g1, z0), z1) if g1 < z1 else None
    return south, north


def in_box(p, centre, half, face=(0.0, 1.0)):
    """Is point p = (x, y, z) in the box with this centre / half (x, y, z) turned so that its local +Z faces `face` = (dx, dz) (kl_fa_author.rot9)?"""
    dx, dz = face
    n = math.hypot(dx, dz) or 1.0
    dx, dz = dx / n, dz / n
    rx, ry, rz = p[0] - centre[0], p[1] - centre[1], p[2] - centre[2]
    lz = rx * dx + rz * dz
    lx = rx * dz - rz * dx
    return abs(lx) <= half[0] and abs(ry) <= half[1] and abs(lz) <= half[2]


def sample_path(pts, step=50.0):
    """Points every `step` units along a polyline of (x, y, z)."""
    out = [tuple(pts[0])] if pts else []
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = max(1, int(d // step))
        out += [tuple(a[k] + (b[k] - a[k]) * j / n for k in range(3)) for j in range(1, n + 1)]
    return out


def path_before(pts, dist_end):
    """The point of the polyline `dist_end` before its end (along the line) and the walking direction (dx, dz) there -> (point, (dx, dz))."""
    acc, last = 0.0, pts[-1]
    for i in range(len(pts) - 1, 0, -1):
        seg = math.dist(pts[i], pts[i - 1])
        if acc + seg >= dist_end:
            t = (dist_end - acc) / seg if seg else 0.0
            p = tuple(pts[i][k] + (pts[i - 1][k] - pts[i][k]) * t for k in range(3))
            dx, dz = pts[i][0] - pts[i - 1][0], pts[i][2] - pts[i - 1][2]
            n = math.hypot(dx, dz) or 1.0
            return p, (dx / n, dz / n)
        acc += seg
        last = pts[i - 1]
    n = math.hypot(pts[1][0] - pts[0][0], pts[1][2] - pts[0][2]) or 1.0
    return last, ((pts[1][0] - pts[0][0]) / n, (pts[1][2] - pts[0][2]) / n)


def run_box(point, direction, floor_y, half=RUN_HALF, y_off=RUN_Y_OFF):
    """A slab across the walk at `point`: (centre, half, face) - thin along the walking direction, wide across it. Axis-aligned (the nearer axis); face = (dx, dz) of the box's local +Z."""
    dx, dz = direction
    if abs(dx) >= abs(dz):          # walking along x: thin in x, wide in z -> the unturned box
        return (point[0], floor_y + y_off, point[2]), (half[0], half[1], half[2]), (0.0, 1.0)
    return (point[0], floor_y + y_off, point[2]), (half[2], half[1], half[0]), (0.0, 1.0)


def exit_box(stop, floor_y, hx=EXIT_HALF_X, before=EXIT_BEFORE, after=EXIT_AFTER, y_off=EXIT_Y_OFF, hy=EXIT_HALF_Y, x_off=EXIT_X_OFF):
    z0, z1 = stop[2] - before, stop[2] + after
    return (stop[0] + x_off, floor_y + y_off, (z0 + z1) / 2), (hx, hy, (z1 - z0) / 2)


def way_fragment(old_points, new_tail):
    """[BotFillWay_DM09] data-only fallback within the hook's 8-point limit: keep the first (8 - len(new_tail)) old points, then the new tail. -> list of 'Pn=x y z' lines."""
    keep = old_points[:max(0, 8 - len(new_tail))]
    pts = keep + list(new_tail)
    return ['P%d=%d %d %d' % (i + 1, round(p[0]), round(p[1]), round(p[2])) for i, p in enumerate(pts[:8])]


def lane_bad(grid, cell, lane_x, floor_y, z0, z1, dxs=(-250, -110, 0, 110, 250), tol=6.0, tall=250.0, step=20):
    """kl_fa_van.check's swath test over a kl_escape.Walk grid: [(z, dx, heights)] of every sample where the floor is not within `tol` of floor_y or something is taller than +tall.
    grid[cell(x, z)] = [(y, flag, r)]."""
    bad = []
    for z in range(int(z0), int(z1), step):
        for dx in dxs:
            ys = [y for y, _f, _r in grid.get(cell(lane_x + dx, z), ()) if y < floor_y + tall]
            fl = [y for y in ys if y <= floor_y + tol]
            if not fl or abs(max(fl) - floor_y) > tol or len(fl) != len(ys):
                bad.append((z, dx, sorted(set(round(y) for y in ys))[:4]))
    return bad


# ------------------------------------------------------------------ plumbing
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _imports():
    import kl_fa, kl_fa_bots as KB, kl_fa_author as au, kl_fa_street as S, kl_gms, kl_graft, kl_fa_bank
    from kl_prp import Prp
    return kl_fa, KB, au, S, kl_gms, kl_graft, kl_fa_bank, Prp


class Ad:
    """What kl_fa_author.place / kl_fa_street.van_pose want of a level: .prp, .ents, .scene and ['.buf'] (kl_graft.Level's surface over a kl_fa_bots.Built)."""

    def __init__(self, B):
        self.B, self.prp, self.ents, self.scene = B, B.sc, B.ents, B.scene

    def __getitem__(self, k):
        return self.B[k]


def nodes_named(sc, part):
    return [k for k in range(1, len(sc.nodes)) if part in sc.names[k]]


def pos_half(B, k):
    v = B.values(k)
    return tuple(round(float(x), 1) for x in B.at(k)), tuple(None if v.get('ZBoxPrimitive[%d]' % i) is None else round(float(v['ZBoxPrimitive[%d]' % i]), 1) for i in range(3))


def read_nav(zp):
    kl_fa, KB, au, S, *_ = _imports()
    S.PLAY = ((-1e9, 1e9), (-1e9, 1e9), (-1e9, 1e9))        # every polygon counts (the stairs / terminal are outside the street's play box)
    nav = S.Nav.of_archive(zp)
    cen = [(sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs), sum(v[2] for v in vs) / len(vs)) if vs else None for vs in nav.pv]
    return nav, cen


def poly_at(nav, x, z, y=None):
    c = [i for i in range(len(nav.pv)) if nav.box[i] and nav.box[i][0] <= x <= nav.box[i][1] and nav.box[i][2] <= z <= nav.box[i][3] and nav.inside(i, x, z)]
    if y is not None and c:
        c.sort(key=lambda i: abs(nav.box[i][4] - y))
    return c


def component(nav, i):
    seen, st = {i}, [i]
    while st:
        for j in nav.nb[st.pop()]:
            if j not in seen:
                seen.add(j); st.append(j)
    return seen


def walk_path(nav, cen, a, b):
    """Dijkstra over polygon centres from polygon a to b -> ([polygon ids], length)."""
    import heapq
    dist, prev, q = {a: 0.0}, {}, [(0.0, a)]
    while q:
        d, i = heapq.heappop(q)
        if d > dist[i]:
            continue
        if i == b:
            break
        for j in nav.nb[i]:
            nd = d + math.dist(cen[i], cen[j])
            if nd < dist.get(j, 1e18):
                dist[j] = nd; prev[j] = i; heapq.heappush(q, (nd, j))
    if b not in dist:
        return None, None
    path = [b]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[b]


def levelbounds(B):
    """Every ACTIVE bound of a Built level: [(name, centre, half, face)] - nodes with a LevelBound controller; a box parked at y <= -50000 is not listed."""
    kl_fa, KB, au, *_ = _imports()
    out = []
    for k in range(1, len(B.sc.nodes)):
        if not any(B.sc.p.key(nm) == 'LevelBound' for nm, _b in B.sc.nodes[k]['ctrls']):
            continue
        c, h = pos_half(B, k)
        if c[1] <= -50000 or None in h:
            continue
        m = struct.unpack('<9f', B.ents[k - 1].rot[:36])
        out.append((B.sc.names[k], c, h, (m[0], m[2])))
    return out


# ------------------------------------------------------------------ the edit
def plan_edit(B, nav, cen, log=print):
    """-> (the list of edits [(label, node, old pos/half, new pos/half, kwargs for au.place)], the facts)."""
    kl_fa, KB, au, S, *_ = _imports()
    sc, A = B.sc, Ad(B)
    stop, head, board, wait = S.van_pose(A, 0)
    if math.dist(stop, OLD_STOP) > 1.0 or head != (0.0, 1.0):
        raise ValueError('the van is not where the cover stage has it (stop %s, heading %s)' % (stop, head))
    top = au.node_of(sc, au.VANS[0])
    grp = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'EscapeVehicle_Animation_F07')
    inside = [k for k in range(1, len(sc.nodes)) if grp < k < sc.end[grp]]
    t0 = S.trans(A, grp)
    if any(abs(v) > 1e-3 for v in t0):
        raise ValueError('the van group is not at the origin: %s' % (t0,))
    d = lane_delta(stop, LANE_X, STOP_Z, FLOOR_Y)
    new_stop = (stop[0] + d[0], stop[1] + d[1], stop[2] + d[2])
    edits = []
    edits.append(('van group', grp, pos_half(B, grp), ((d[0], d[1], d[2]), None), dict(pos=d)))
    # the exit box, the POI
    k_exit = au.node_of(sc, au.ROLE['exit'])
    c, h = exit_box(new_stop, FLOOR_Y)
    edits.append(('otrExitLevel', k_exit, pos_half(B, k_exit), (c, h), dict(pos=c, half=h, turn=S.IDENT)))
    k_poi = au.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea')
    edits.append(('POI_TheEscapeArea', k_poi, pos_half(B, k_poi), ((new_stop[0], FLOOR_Y + POI_Y_OFF, new_stop[2]), None), dict(pos=(new_stop[0], FLOOR_Y + POI_Y_OFF, new_stop[2]))))
    # the walk: road mouth -> the lane
    road_i = poly_at(nav, -5700, 9000, -45)[0]
    road = component(nav, road_i)
    goal_c = (new_stop[0], FLOOR_Y, new_stop[2])
    goal = min((i for i in road if cen[i]), key=lambda i: math.dist(goal_c, cen[i]))
    path, length = walk_path(nav, cen, road_i, goal)
    if path is None:
        raise ValueError('no nav walk from the road mouth to the terminal lane')
    pts = [cen[i] for i in path]
    p_run, direction = path_before(pts, RUN_BEFORE)
    rc, rh, _face = run_box(p_run, direction, FLOOR_Y)
    for name in RUN_BOXES:
        k = au.node_of(sc, name)
        edits.append((name.split('!')[-1], k, pos_half(B, k), (rc, rh), dict(pos=rc, half=rh, turn=S.IDENT)))
    # the west slab
    kb = au.node_of(sc, WEST + 'Bound')
    gap = corridor_gap(nav.box, nav.nb, road, SLAB_X[0], SLAB_X[1], SLAB_Y[0], SLAB_Y[1], GAP_PAD, SLAB_Z)
    if gap is None:
        raise ValueError('no nav corridor crosses the west bound slab')
    south, north = slab_split(SLAB_Z[0], SLAB_Z[1], gap)
    yc, yh = (SLAB_Y[0] + SLAB_Y[1]) / 2, ST_HALF_Y
    for trio, part in ((WEST, south), (SPARE, north)):
        for leaf, (x0, x1) in (('Bound', SLAB_X), ('Warn01', WARN_X), ('Warn02', WARN_X)):
            k = au.node_of(sc, trio + leaf)
            if part is None:
                edits.append((leaf + ' ' + trio.split('!')[-2], k, pos_half(B, k), (PARK, None), dict(pos=PARK)))
            else:
                c, h = to_box(x0, x1, SLAB_Y[0], SLAB_Y[1], part[0], part[1])
                edits.append((leaf + ' ' + trio.split('!')[-2], k, pos_half(B, k), (c, h), dict(pos=c, half=h, turn=S.IDENT)))
    # the campaign pen
    pen = nodes_named(sc, PEN)
    if len(pen) != 5:
        raise ValueError('expected the 5 Busterminal bound boxes, found %d' % len(pen))
    used = {t[0] + leaf for t in TERM_TRIOS for leaf in ('Bound', 'Warn01', 'Warn02')}
    for k in pen:
        if sc.names[k] not in used:
            edits.append(('pen ' + sc.names[k].split('!')[-1], k, pos_half(B, k), (PARK, None), dict(pos=PARK)))
    # the terminal's walls (reused trios): Bound = the wall, Warn01 = Warn02 = the wall grown toward the allowed side
    for trio, why, x0, x1, z0, z1, side in TERM_TRIOS:
        for leaf in ('Bound', 'Warn01', 'Warn02'):
            k = au.node_of(sc, trio + leaf)
            r = (x0, x1, z0, z1) if leaf == 'Bound' else warn_rect(x0, x1, z0, z1, side)
            c, h = to_box(r[0], r[1], BOUND_Y[0], BOUND_Y[1], r[2], r[3])
            edits.append(('terminal wall %s (%s)' % (why, leaf), k, pos_half(B, k), (c, h), dict(pos=c, half=h, turn=S.IDENT)))
    # van children must all be inside the moved group (they carry the PathBlockerVan, boarding box, cameras)
    # nodes of the van's top entity that sit OUTSIDE the moved group would stay behind
    stray = [k for k in range(top, sc.end[top]) if k != top and not grp <= k < sc.end[grp] and not any(sc.p.key(nm) in ('Group',) for nm, _b in sc.nodes[k]['ctrls']) and k not in (grp,)]
    facts = dict(stop_old=stop, stop_new=new_stop, delta=d, wait_new=(wait[0] + d[0], wait[1] + d[1], wait[2] + d[2]), board_new=(board[0] + d[0], board[1] + d[1], board[2] + d[2]),
                 group=grp, children=len(inside), gap=gap, slab_south=south, slab_north=north, path=pts, path_len_m=length / 100.0, polys=len(path), goal=goal,
                 run_point=p_run, run_dir=direction, strays=stray)
    return edits, facts


def apply_edits(B, edits):
    kl_fa, KB, au, *_ = _imports()
    A = Ad(B)
    for label, k, _old, _new, kw in edits:
        au.place(A, k, **kw)


def rebuild(src, dst, nav, cen, log=print):
    """One zip: Built -> round trip check -> edits -> .prp + .gms/.buf -> write, seal, reverify. -> report."""
    kl_fa, KB, au, S, kl_gms, kl_graft, kl_fa_bank, Prp = _imports()
    B = KB.Built(src, SLOT)
    g0, b0 = B.scene.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    edits, facts = plan_edit(B, nav, cen, log)
    # The van's 42 model / smear / shadow nodes are siblings of the group under F07_Escape_Vehicle_01.zip, not children: they are bound to the baked animation
    # (the .ANM drives them), exactly as kl_fa_street.place_escape / kl_fa_van.straighten move the van by this ONE group translation (GUESS carried over from that precedent, proven on the street).
    log('  van: %d model/smear nodes beside the group follow the animation, not the scene tree (precedent: kl_fa_street.place_escape)' % len(facts['strays']))
    old_stops = {}
    apply_edits(B, edits)
    prp = B.sc.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(B.sc.nodes) - 1 and len(back.nodes()) != len(B.sc.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    gms, buf = B.scene.write()
    new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
    # The nav mesh ignores collision: the .HVK still holds the invisible barricade in the facade wall's only doorway. Cut its placement (kl_escape.cut_collision, as the DM02 vault glass).
    import kl_hvk, kl_escape
    h = kl_hvk.Hvk(new[B.ext['.HVK']])
    for r in BARRICADE_REFS:
        got = [s_.type for s_ in h.shapes for i in s_.inst if kl_hvk.ref(i) == r]
        if got != [kl_hvk.STATIC]:
            raise ValueError('barricade: REF %d has placements of types %s in the .HVK (want exactly one static)' % (r, got))
    kl_escape.cut_collision(h, set(BARRICADE_REFS), lambda *a: None)
    if any(kl_hvk.ref(i) in BARRICADE_REFS for s_ in h.shapes for i in s_.inst):
        raise ValueError('barricade: still placed after the cut')
    new[B.ext['.HVK']] = h.serialize()
    work = tempfile.mkdtemp(prefix='dm09term_')
    rep = collections.OrderedDict()
    try:
        zp = kl_graft.write_zip(os.path.join(work, SLOT + '_Main.zip'), [(n, new[n]) for n in B.order])
        rep['sealed'] = kl_fa_bank.seal(work, log=lambda *_: None)
        probs = kl_fa_bank.reverify(work, log=lambda *_: None)
        rep['reverify'] = probs[:8]
        if probs:
            log('  reverify notes: %s' % probs[:5])
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep['members_changed'] = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    log('  written %s: members changed: %s' % (dst, ' '.join(rep['members_changed'])))
    return rep, edits, facts


# ------------------------------------------------------------------ checks on a STAGED zip
def check_staged(zp, facts, log=print):
    """Re-read a staged zip: edits in place, bounds, exit, lane (HVK), nav flood + path vs every active bound."""
    kl_fa, KB, au, S, *_ = _imports()
    B = KB.Built(zp, SLOT)
    sc = B.sc
    res = collections.OrderedDict()
    A = Ad(B)
    stop, head, board, wait = S.van_pose(A, 0)
    res['stop'] = tuple(round(v, 1) for v in stop); res['wait'] = tuple(round(v, 1) for v in wait); res['board'] = tuple(round(v, 1) for v in board)
    res['stop_ok'] = math.dist(stop, facts['stop_new']) < 1.0
    # one exit trigger, its box
    exits = [k for k in range(1, len(sc.nodes)) if any(sc.p.key(nm) == 'OnlineExitLevelTrigger' for nm, _b in sc.nodes[k]['ctrls'])]
    res['exit_triggers'] = len(exits)
    ek = au.node_of(sc, au.ROLE['exit'])
    c, h = pos_half(B, ek)
    res['exit_box'] = (c, h)
    res['old_stop_in_exit'] = in_box(OLD_STOP, c, h)
    res['new_stop_in_exit'] = in_box(facts['stop_new'], c, h)
    res['board_in_exit'] = in_box(facts['board_new'], c, h)
    res['wait_in_exit'] = in_box(facts['wait_new'], c, h)
    # the exit box in the nav mesh
    nav, cen = read_nav(zp)
    road_i = poly_at(nav, -5700, 9000, -45)[0]
    road = component(nav, road_i)
    in_ex = [i for i in road if cen[i] and in_box(cen[i], c, h)]
    res['road_polys_in_exit'] = len(in_ex)
    res['street_polys_in_exit'] = sum(1 for i in road if cen[i] and in_box(cen[i], c, h) and cen[i][0] > -8000)
    path, length = walk_path(nav, cen, road_i, min(in_ex, key=lambda i: math.dist(cen[i], facts['path'][-1]))) if in_ex else (None, None)
    res['walk_m'] = None if path is None else round(length / 100.0, 1)
    res['walk_polys'] = None if path is None else len(path)
    res['reachable'] = path is not None
    # the start: the real heister spawn when the level has one near the tower; else the road start
    start = poly_at(nav, -3000, -6000, -45)
    s_path = None
    if start and in_ex:
        s_path, s_len = walk_path(nav, cen, start[0], min(in_ex, key=lambda i: math.dist(cen[i], facts['path'][-1])))
        res['road_start_walk_m'] = None if s_path is None else round(s_len / 100.0, 1)
    # bounds: samples of the walk against every active LevelBound, here and in the cover stage
    wp = sample_path([cen[i] for i in (s_path or path or [])]) if (s_path or path) else []
    bounds = levelbounds(B)
    res['bounds_active'] = len(bounds)
    res['bounds_hit'] = sorted({n.split('!', 1)[-1] for p in wp for n, bc, bh, f in bounds if in_box(p, bc, bh, f)})
    res['samples'] = len(wp)
    # the same walk against the cover stage's bounds
    cover_zip = os.path.join(COVER, FILES[0]) if os.path.isfile(os.path.join(COVER, FILES[0])) else None
    if cover_zip and os.path.abspath(cover_zip).lower() != os.path.abspath(zp).lower():
        B0 = KB.Built(cover_zip, SLOT)
        b0 = levelbounds(B0)
        res['cover_bounds_hit'] = sorted({n.split('!', 1)[-1] for p in wp for n, bc, bh, f in b0 if in_box(p, bc, bh, f)})
    # the lane on the HVK
    import kl_hvk, kl_escape
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        hvk = kl_hvk.Hvk(z.read(m['.hvk']))
    w = kl_escape.Walk(hvk, box=(LANE_X - 2500.0, LANE_X + 3500.0, 4000.0, 20500.0))
    bad = lane_bad(w.grid, w.cell, LANE_X, FLOOR_Y, facts['wait_new'][2] - 600, facts['stop_new'][2] + 10200 + 700)
    res['lane_bad'] = len(bad)
    res['lane_bad_first'] = bad[:4]
    # collision reachability: a Walk flood from the street mouth must reach the lane (the nav mesh ignores collision), and the barricade must be gone
    res['barricade_placed'] = any(kl_hvk.ref(i) in BARRICADE_REFS for s_ in hvk.shapes for i in s_.inst)
    w2 = kl_escape.Walk(hvk, box=(LANE_X - 2500.0, -5000.0, 3000.0, 20500.0))
    seen, _par, _blk = w2.flood((-5700.0, -45.0, 9000.0))
    lane_cells = [c for c, y in seen.items() if abs(w2.centre(c)[0] - LANE_X) < 200 and abs(w2.centre(c)[1] - facts['stop_new'][2]) < 300 and abs(y - FLOOR_Y) < 30]
    res['hvk_street_to_lane_cells'] = len(lane_cells)
    res['hvk_pocket_cells_in_exit'] = len(w2.inside(seen, (c, h)))
    # the terminal's walls: flood from the street mouth over the whole hall window with every active bound as a wall; cells west of the street outside CORRIDOR must be 0
    w3 = kl_escape.Walk(hvk, box=(-40000.0, 9000.0, -16000.0, 32000.0))
    wall = collections.defaultdict(list)
    for n, bc, bh, f in bounds:
        if 'Bound' not in n.split('!')[-1]:
            continue
        r = max(bh[0], bh[2]) * 1.5
        i0, j0 = w3.cell(bc[0] - r, bc[2] - r)
        i1, j1 = w3.cell(bc[0] + r, bc[2] + r)
        for cx in range(i0, i1 + 1):
            for cz in range(j0, j1 + 1):
                px, pz = w3.centre((cx, cz))
                if in_box((px, bc[1], pz), bc, bh, f):
                    wall[(cx, cz)].append((bc[1] - bh[1], bc[1] + bh[1]))
    seen3 = flood_walls(w3, wall, (-5700.0, -45.0, 9000.0))
    pts3 = [w3.centre(c) for c in seen3]
    res['bounded_flood_cells'] = len(seen3)
    res['bounded_cells_outside'] = sum(1 for x, z in pts3 if x < -7100.0 and not in_corridor(x, z))
    res['bounded_x_range'] = (round(min(p[0] for p in pts3)), round(max(p[0] for p in pts3)))
    res['bounded_lane_cells'] = sum(1 for c, y in seen3.items() if abs(w3.centre(c)[0] - LANE_X) < 200 and abs(w3.centre(c)[1] - facts['stop_new'][2]) < 300 and abs(y - FLOOR_Y) < 30)
    res['bounded_exit_cells'] = len(w3.inside(seen3, (c, h)))
    ex = (c[0] - h[0], c[0] + h[0], c[2] - h[2], c[2] + h[2])
    res['walls_in_exit_box'] = [t[1] for t in TERM_TRIOS if rects_overlap(ex, t[2:6])]
    res['nav_polys_outside_corridor'] = sum(1 for i in (path or []) if cen[i] and cen[i][0] < -6500.0 and not in_corridor(cen[i][0], cen[i][2]))
    return res


def flood_walls(w, wall, start):
    """kl_escape.Walk.flood (4-neighbour) with `wall` = {cell: [(ylo, yhi)]}: a cell whose floor y is inside one of its spans is not entered. -> {cell: floor y}."""
    c0, y0 = w.floor(*start)
    seen, q = {c0: y0}, collections.deque([c0])
    while q:
        c = q.popleft()
        y = seen[c]
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + d[0], c[1] + d[1])
            g = w.grid.get(n)
            if n in seen or not g:
                continue
            cand = [yy for yy, f, _r in g if f and -w.DOWN <= yy - y <= w.UP]
            if not cand:
                continue
            ny = max(cand)
            if any(ny + w.LO < yy < ny + w.HI for yy, _f, _r in g):
                continue
            if n in wall and any(a <= ny <= b for a, b in wall[n]):
                continue
            seen[n] = ny
            q.append(n)
    return seen


# ------------------------------------------------------------------ stage
INSTALL_DOC = 'DM09 TERMINAL 1110 (tools/kl_dm09_terminal_1110.py): the escape van, exit box and west bound moved to the bus terminal (optional variant, recommended off until benched)'


def render_install(files, game=GAME):
    import kl_cover_dm09_1110 as C
    t = C.render_install(files, game)
    first = t.split('\n', 1)[0]
    return t.replace(first, '"""Installs / undoes ' + INSTALL_DOC + '.', 1).replace(C.TAG_BAK, TAG_BAK)


README = '''DM09 Retomoto TERMINAL 1110  (optional variant, recommended off until benched)
===========================================================================
The heisters run down the street, west through the (now open) corridor of the west bound, over the stairs overpass and escape at the bus terminal
(the campaign's end: the van waits at x %(lx)d, z %(sz)d on the terminal floor). Stock walk: %(walk)s m from the road mouth, %(polys)s nav polygons (nav flood on the STAGED zip).
Optional: undo puts the three files back byte for byte. NOT run in the game (the owner is on the PC): everything marked GUESS below is unproven.

Collision: the invisible barricade REF 23098 (PC0100_JPN_InvisibleBarricade01) in the facade wall's doorway is CUT out of the .HVK (kl_escape.cut_collision), so the .HVK member changes too.

Files (DM09 only: F06_Main.zip, F06_Main.bots.zip, F06_Main.bots.base.md5)
  Requires the COVER stage installed first (pins = its md5s: %(pins)s). install.py REFUSES on any other live state.
  Install: INSTALL.bat (or python install.py)    Undo: UNDO.bat (or python install.py --undo)    Check only: python install.py --dry
  Undo order: this first, then the cover stage's UNDO.bat.

What moved (values of existing entities only, no slot id changes): see moved.txt (old -> new for every entity).

[BotFillWay_DM09] (Dog Days KLHook.ini, peer-owned: NOT applied; fragment in ini_fragment.txt)
  The hook (work tree, uncommitted) now reads up to 16 points (KLBF_WAY_MAX 16; the DATA FALLBACK below also fits an older 8-point dll). The old route P1..P8 ends at the street stop; the fragment keeps P1..P6 and ends with the street mouth + the
  terminal lane. The engine paths between points over the mesh (GUESS: it takes the stairs on its own). A route with every corner needs KLBF_WAY_MAX raised (plan below).

HOOK PLAN (klhook C code, NOT changed here)
%(hook)s

ROUND TIMER PROPOSAL (re/dm09_timing_1102.md): the walk grows by about 279 m on foot (re/dm09_timing_1102.md; the staged nav walk is %(newwalk)s m from the road mouth, a different start from that doc's 274 m P2 -> street stop). Bots walk 1.1-1.5 m/s under fire,
players run ~4-5 m/s. Proposal: lobby Heist time 8 min default for this variant (6 min was Arcade parity for 274 m; +2 min covers the extra 279 m at 2.3 m/s) with [Lobby] TimeMax=10 (already allowed);
bots: OnlineLegSpeed=100 + OnlineLegNear=600 + OnlineLegMaxS=60 (RT5 rows of the doc); the van is called later: a per-map OnlineLateExit of 150 s would need code (global key today).
GUESS: the owner decides the lobby row; nothing here sets the clock.

Not changed (limits): police ring squads + RunToEscape squads stay round the old street stop (they fight the crew on the street); NoCoverBox#19/#20 stay at the old stop;
the terminal has no extra cops (see the owner's wish "SWAT dropped off by vans down there": a separate stage); the terminal is walled by 4 LevelBound boxes (street / overpass + stairs corridor / lane; reused parked trios, GUESS extents; going outside them = KILLED BY AN ACCIDENT after the Warn).
'''


HOOK_PLAN = '''  1. klhook/klbotfill.c:516  KLBF_WAY_MAX 8 -> 16 (static float klbf_way_p[KLBF_WAY_MAX][3], klbf_way_read 523-538 loops i <= KLBF_WAY_MAX; klbf_wv_idx clamp at 349 stays 0..7 unless raised).
     Then the full route (ini_fragment.txt "FULL") can be used. Until then the data fallback above is in range.
  2. klhook/klbotfill.c:1885-1895 klbf_van_ok (OnlineVanPosSane): kvp_sane(1, vp, nref, ref) uses KVP_ABS_CM 40000 / KVP_REF_CM 50000 (klhook/klgetup_logic.h:210).
     The new van (-25500, -978, 8100) has |x| 25500 < 40000 and stands within 50000 of the exit trigger / box frames (both moved with it): sane, NO change needed (checked arithmetic, not run).
  3. klhook/klescort.c exit walk / FollowOut: any hard-coded street constants for DM09 (the 'exit walk' goal = the exit trigger's frame): to be read by the hook owner; the goal follows the
     trigger frame, so it should follow the move (GUESS, not read here: klescort.c is not in this repo checkout path I read).
  4. tools/kl_fa_street.py lane_nodes / van_pose: build-time only; kl_fa_street.place_escape (603-) and EXIT_BEFORE/AFTER (134-136) describe the street stop; this variant does not call them.
  6. klhook/klbotfill.c:2296 (and 2392): REQUIRED for online bots. The vehicle object's node (scene node 25050, child of the moved van group 24871 at local 0) now reads the GROUP's translation
     (-23647, -980, -2700) before the van is called, not (0,0,0): the 'not here' guard (|coord| <= 1) passes and klbf_van_ok accepts it, so van_w is set and bots head for vpos (2640, 2807, 2537),
     87 m south of the wait point. Fix: a rest position the guard also treats as 'not here', e.g. new key [BotFill] OnlineVanRest=-23647 -980 -2700 (reject when within 100 cm of it), or accept the
     first-scan van only once the rules' vehicle slot ([rules+0x1e4], the 2392 path) is filled. Not done in data: moving node 25050's local position would shift the baked drive if the .ANM keys are relative (unproven).
  7. Bounds west / north / south of the terminal: DONE in the zips (4 reused trios, README); the bots must stay inside CORRIDOR too (a bot outside a bound is killed).
  5. [BotFill] OnlineLegWaitIdx (klbotfill.c:349): the hold leg is P2 (index 1); P1..P6 keep their meaning with the fragment.'''


def ini_fragment(facts, old_pts):
    nav_tail = [(-5700.0, -45.0, 9000.0), (facts['stop_new'][0] + 900.0, FLOOR_Y, facts['stop_new'][2])]
    lines = ['; [BotFillWay_DM09] TERMINAL variant: paste over the section in Dog Days KLHook.ini (peer-owned: not applied by install.py). GUESS: the engine paths between points over the mesh.',
             '[BotFillWay_DM09]  ; DATA FALLBACK (8 points): P1..P6 as today, P7 = the street mouth of the west corridor, P8 = the terminal lane (east edge of the van lane)']
    lines += way_fragment(old_pts, nav_tail)[:8]
    lines += ['', '; FULL route (needs KLBF_WAY_MAX 16): street mouth, west corridor, stairs overpass, terminal lane - corners from the staged zip walk']
    p = facts['path']
    pick = [p[i] for i in range(0, len(p), max(1, -(-len(p) // 8)))]      # <= 8 corners + the end, so P1..P6 + these fit in 16
    if pick[-1] != p[-1]:
        pick.append(p[-1])                       # the route must END at the lane (the stride alone stopped short)
    full = list(old_pts[:6]) + [(round(q[0]), round(q[1]), round(q[2])) for q in pick]
    lines += ['; P%d=%d %d %d' % (i + 1, round(q[0]), round(q[1]), round(q[2])) for i, q in enumerate(full[:16])]
    return '\n'.join(lines) + '\n'


def moved_text(edits, facts):
    out = ['DM09 TERMINAL 1110: every moved entity, old -> new (position x y z; half = ZBoxPrimitive half sizes)']
    for label, k, old, new, kw in edits:
        o = 'pos %s half %s' % old
        if label == 'van group':
            n = 'translation %s (the group sat at the origin: its children moved with it)' % (tuple(round(v, 1) for v in new[0]),)
        else:
            n = 'pos %s half %s' % (tuple(round(v, 1) for v in new[0]), None if new[1] is None else tuple(round(v, 1) for v in new[1]))
        out.append('%-34s node %-6s %s  ->  %s' % (label, k, o, n))
    out.append('')
    out.append('van: stop %s -> %s, wait -> %s, boarding box -> %s' % (tuple(round(v, 1) for v in facts['stop_old']), tuple(round(v, 1) for v in facts['stop_new']),
                                                                       tuple(round(v, 1) for v in facts['wait_new']), tuple(round(v, 1) for v in facts['board_new'])))
    return '\n'.join(out) + '\n'


def old_way_points(game):
    pts = {}
    try:
        sec = False
        for ln in open(os.path.join(game, 'KLHook.ini'), errors='replace'):
            s = ln.split(';')[0].strip()
            if s.startswith('['):
                sec = s.lower() == '[botfillway_dm09]'
            elif sec and s.startswith('P') and '=' in s:
                k, v = s.split('=', 1)
                pts[int(k[1:])] = tuple(float(x) for x in v.split())
    except OSError:
        pass
    return [pts[i] for i in sorted(pts)]


def stage(out, cover, game=GAME, rehearse=True, log=print):
    live = {n: os.path.join(cover, n) for n in FILES}
    for n, p in live.items():
        if not os.path.isfile(p):
            raise SystemExit('REFUSED: cover stage file missing: %s' % p)
    pins = {n: md5(p) for n, p in live.items()}
    if open(live[FILES[2]]).read().strip() != pins[FILES[0]]:
        raise SystemExit('REFUSED: the cover stage bots.base.md5 is not its plain zip md5')
    os.makedirs(out, exist_ok=True)
    need = 6 * os.path.getsize(live[FILES[0]]) + FREE_KEEP
    if shutil.disk_usage(out).free < need:
        raise SystemExit('REFUSED: less than %d MB free on the stage drive' % (need >> 20))
    for f in os.listdir(out):
        p = os.path.join(out, f)
        if os.path.isfile(p):
            os.remove(p)
    log('cover pins: %s' % pins)
    nav, cen = read_nav(live[FILES[0]])
    res = collections.OrderedDict()
    facts0 = edits0 = None
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        log('== %s' % name)
        rep, edits, facts = rebuild(live[name], os.path.join(out, name), nav, cen, log)
        res[key] = rep
        if facts0 is None:
            facts0, edits0 = facts, edits
        elif facts['gap'] != facts0['gap'] or facts['delta'] != facts0['delta']:
            raise SystemExit('REFUSED: the plain and bots zips disagree on the plan')
    base = md5(os.path.join(out, FILES[0]))
    open(os.path.join(out, FILES[2]), 'w', newline='\n').write(base + '\n')
    checks = {}
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        checks[key] = check_staged(os.path.join(out, name), facts0, log)
        log('%s check: %s' % (key, json.dumps(checks[key], default=str)))
        c = checks[key]
        if not (c['stop_ok'] and c['exit_triggers'] == 1 and c['new_stop_in_exit'] and c['board_in_exit'] and not c['old_stop_in_exit'] and c['reachable']
                and c['street_polys_in_exit'] == 0 and c['lane_bad'] == 0 and c['bounded_cells_outside'] == 0 and c['bounded_lane_cells'] > 0 and c['bounded_exit_cells'] > 0 and not c['walls_in_exit_box'] and c['nav_polys_outside_corridor'] == 0 and not c['bounds_hit'] and not c['barricade_placed'] and c['hvk_street_to_lane_cells'] > 0):
            raise SystemExit('REFUSED: %s failed its staged checks: %s' % (name, json.dumps(c, default=str)))
    files = [(FILES[0], pins[FILES[0]], base), (FILES[1], pins[FILES[1]], md5(os.path.join(out, FILES[1]))), (FILES[2], pins[FILES[2]], md5(os.path.join(out, FILES[2])))]
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(render_install(files, game))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    c = checks['plain']
    old_pts = old_way_points(game)
    open(os.path.join(out, 'README.txt'), 'w', newline=chr(10)).write(README % dict(
        lx=LANE_X, sz=STOP_Z, walk=c['walk_m'], polys=c['walk_polys'], pins=', '.join('%s %s' % (n, h[:8]) for n, h in pins.items()), hook=HOOK_PLAN, newwalk=c['walk_m']))
    open(os.path.join(out, 'ini_fragment.txt'), 'w', newline='\n').write(ini_fragment(facts0, old_pts))
    open(os.path.join(out, 'moved.txt'), 'w', newline='\n').write(moved_text(edits0, facts0))
    with open(os.path.join(out, 'build_report.json'), 'w') as f:
        json.dump(dict(pins=pins, files=files, built=res, checks=checks, gap=facts0['gap'], stop_new=facts0['stop_new']), f, indent=1, default=str)
    if rehearse:
        rehearsal(out, files, game, log)
    for n, o_, w in files:
        log('%-26s %s -> %s' % (n, o_, w))
    return dict(files=files, checks=checks, facts=facts0, edits=edits0)


def rmtree(p):
    shutil.rmtree(p, ignore_errors=True)


def rehearsal(out, files, game, log=print):
    """Install, --dry, 2nd install refused, undo byte-exact, 2nd undo refused, reinstall, final undo - on a COPY of the three cover-stage files in <out>_scratch (deleted afterwards)."""
    scratch = os.path.abspath(out) + '_scratch'
    assert os.path.abspath(scratch).lower() != os.path.abspath(game).lower()
    rmtree(scratch)
    g = os.path.join(scratch, 'game')
    d = os.path.join(g, 'KLExpansion', 'Maps', MAP)
    os.makedirs(d)
    try:
        for n, old, _new in files:
            shutil.copyfile(os.path.join(COVER_USED[0], n), os.path.join(d, n))
        run = lambda *x: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--root', g, '--skip-run-check'] + list(x), capture_output=True, text=True)
        steps = []
        t = run('--dry'); steps.append(('dry', t.returncode == 0 and 'would install' in t.stdout and all(md5(os.path.join(d, n)) == o for n, o, _w in files)))
        t = run(); steps.append(('install', t.returncode == 0 and all(md5(os.path.join(d, n)) == w for n, _o, w in files) and all(md5(os.path.join(d, n + TAG_BAK)) == o for n, o, _w in files)))
        t = run(); steps.append(('2nd install refused', t.returncode == 1 and 'REFUSED' in t.stdout and all(md5(os.path.join(d, n)) == w for n, _o, w in files)))
        t = run('--undo'); steps.append(('undo byte-exact', t.returncode == 0 and all(md5(os.path.join(d, n)) == o for n, o, _w in files) and not any(os.path.exists(os.path.join(d, n + TAG_BAK)) for n, _o, _w in files)))
        t = run('--undo'); steps.append(('2nd undo refused', t.returncode == 1 and 'REFUSED' in t.stdout))
        t = run(); steps.append(('reinstall after undo', t.returncode == 0))
        t = run('--undo'); steps.append(('final undo byte-exact', t.returncode == 0 and all(md5(os.path.join(d, n)) == o for n, o, _w in files)))
        for s, ok in steps:
            log('  rehearsal %-24s %s' % (s, 'PASS' if ok else 'FAIL'))
        if not all(ok for _s, ok in steps):
            raise SystemExit('rehearsal FAILED')
    finally:
        rmtree(scratch)
        log('  scratch %s %s' % (scratch, 'deleted' if not os.path.exists(scratch) else 'STILL THERE'))


COVER_USED = [COVER]


def main(argv):
    a = list(argv)
    if not a or a[0] not in ('plan', 'stage'):
        print(__doc__)
        return 2
    cmd, a = a[0], a[1:]
    game, cover, rest = GAME, COVER, []
    while a:
        x = a.pop(0)
        if x == '--game': game = a.pop(0)
        elif x == '--cover': cover = a.pop(0)
        else: rest.append(x)
    COVER_USED[0] = cover
    rehearse = '--no-rehearse' not in rest
    rest = [x for x in rest if x != '--no-rehearse']
    if cmd == 'plan':
        zp = os.path.join(rest[0] if rest else cover, FILES[0])
        kl_fa, KB, *_ = _imports()
        B = KB.Built(zp, SLOT)
        nav, cen = read_nav(zp)
        edits, facts = plan_edit(B, nav, cen)
        print(moved_text(edits, facts))
        print('walk %.0f m, %d polygons, gap %s, slab south %s north %s' % (facts['path_len_m'], facts['polys'], facts['gap'], facts['slab_south'], facts['slab_north']))
        return 0
    stage(rest[0] if rest else OUT, cover, game, rehearse)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
