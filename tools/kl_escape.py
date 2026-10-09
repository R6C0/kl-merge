#!/usr/bin/env python3
"""
The escape of a Dead Men Fragile Alliance map under Dog Days: what cuts the way from the loot to
the van, and the repairs. Spec and evidence: re/escape.md. Offline; nothing here installs anything
or starts the game.

    python kl_escape.py walls [level]            the walk test on Dead Men's own collision: is the exit
                                                 trigger reachable on foot, and which single object,
                                                 taken out, would make it so (default M03_FA_A)
    python kl_escape.py test <out> [S] [M]       build S + M (default F07 + M03_FA_A) into the scratch
                                                 folder <out> with the repairs, verify (kl_graft
                                                 verify 0 problems, kl_fa.check without CRASH /
                                                 BROKEN), walk test on the built .HVK, print the
                                                 route; exit 1 if anything fails
    python kl_escape.py route <archive>          walk test + route on a built level

WHAT IS WRONG (re/escape.md): Dead Men's player climbs walls up to 2.2 m (ZFFPlayerMovementClimb,
kaneandlynch.exe vtable 0x966c44; table of 120 / 170 / 220 built at 0x603340). kl2.exe has no such
class. M03_FA_A's way from the yard behind the bank to the van's street IS such a climb: the wall
SO0101_M03_Wall_Low_8m_05 / _01 / _02 / _03 (z -600, top y 404, yard y 200, street y 150). Nothing
of the level is dropped or mis-converted; the walkable area simply ends at that wall.

THE REPAIRS (functions in the style of kl_fa.repair: values of existing objects only, no new
entity, no controller added or removed, so kl_graft's controller indices stay valid)
  open_wall(Jn)        the wall pieces in OPEN[level] are SUNK until their top is level with the
                       yard (.prp ZGEOM[2]; a kerb is left where the 2 m wall was). -> {node: dy}
  place_entities(...)  the same move in the .gms records, and the REF ids of the moved entities
  cut_collision(hvk)   their static placements in the joined .HVK are replaced by a filler (a copy
                       of another kept static placement), as kl_hvk.remap does for a dropped map
                       object: the list MOPP addresses placements by position, so none may go.
                       The yard's asphalt (y 200) and the street's (y 150) meet at z -600 under
                       the wall, so the opened piece is a 50 cm step down - one way, like the climb.
  money_reach(Jn)      Dead Men's container triggers with a reach below Dog Days' 125 get 125
                       (GUESS; the garage boxes have 80 and gave nothing live at 78..138 units).
  repair(Jn, log)      open_wall + money_reach on the joined .prp scene.

FOR kl_graft.build (three lines; until then applied() patches the same three places from
outside, as kl_maps and kl_fa_author do):
    if fa:  kl_fa.repair(Jn, kept, log);  esc = kl_escape.repair(Jn, log)       # after dm_rename
    ...
    cut = kl_escape.place_entities(Jn, list(A.entities()), esc, log)            # before A.write()
    hvk = kl_escape.cut_collision(kl_hvk.join(...), cut, log).serialize()

GUESSES are marked where they are made. Not known and not knowable offline: whether Dog Days'
player falls the 50 cm step without trouble, and whether Dead Men's spline van (ZHavokCar +
OnlineVehicleOnSpline, kept as it is) drives when the exit trigger calls it.
"""
import collections, contextlib, heapq, math, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hvk, kl_fa, kl_gms, kl_scene
import kl_prpjoin as J
from kl_prp import units

R = 'ROOT\\'
M03_OUT = 'Locations/M03_FA_A/M03FAA_Locations.zip\\Locations/M03_FA_A/M03FAA_LOC_Outside.zip\\M03_FAA_Outside_01A\\'
# Wall pieces to open, per Dead Men map: (scene path, how far down).
# M03_FA_A: the piece nearest the van of the four Dead Men's players climb (x -1900..-1100). Its
# model is 403.5 high and stands on y 0 (.prm bounds, .HVK box 0..404); the yard's asphalt is at
# y 200 (.HVK). Sunk by 203.5 its top is the yard's floor. GUESS: one piece is enough and this one
# is the best (a dumpster stands behind its east third, x -1454..-1200; the other 5.5 m are free).
OPEN = {'M03_FA_A': [(M03_OUT + 'SO0101_M03_Wall_Low_8m_05', -203.5)]}
REACH = 125.0                   # TriggerBox2 radius of all 117 stock money containers (F01, F03, F08)
# The round's boxes in Dead Men's M03_FA_A, world space, (centre, half extents) - re/escape.md 1
EXIT_BOX = ((408.0, 396.0, 460.0), (4000.0, 400.0, 1000.0))
BOARD_BOX = ((3252.0, 133.0, -20.0), (400.0, 200.0, 300.0))
VAN_STOP = (2970.0, 25.0, 41.0)                 # last point of VehicleMoveBehaviour_Incomming's spline
YARD = (300.0, 220.0, -4500.0)                  # behind the garage's roller doors
WEST_DOOR = (-1244.0, 220.0, -1243.0)           # a way point of f-live's rounds in the yard (RN10)
BOX_11 = (690.0, 241.0, -6190.0)                # beside PC0500_M03_MoneyBox_11 (containers() prints these)


# ------------------------------------------------------------------ repairs on the joined scene
def _node(sc, path):
    hit = sc.resolve(R + path)
    if len(hit) > 1:
        raise KeyError('%s: %d nodes named %s' % (sc.label, len(hit), path))
    return hit[0] if hit else None


def _level_of(sc):
    """The Dead Men map a scene holds, by the wall tables above (None: nothing to do)."""
    for level, walls in OPEN.items():
        if all(_node(sc, p) is not None for p, _dy in walls):
            return level
    return None


def _world(sc, k):
    """True if every parent of node k is unrotated at the origin (its ZGEOM[2] is a world place)."""
    k = sc.parent[k]
    while k > 0:
        v = kl_fa.node_values(sc, k)
        if any(abs(x) > 1.0 for x in v[2]) or [round(x) for x in v[1]] != [0, 0, 1, 0, 1, 0, 1, 0, 0]:
            return False
        k = sc.parent[k]
    return True


def open_wall(sc, log=print, walls=None):
    """Sink the wall pieces of OPEN (or `walls` = [(path, dy)]) in the .prp: ZGEOM[2].y += dy.
    -> {node index: dy}, for place_entities(). The .gms record and the collision follow there."""
    level = _level_of(sc)
    walls = walls if walls is not None else OPEN.get(level, [])
    out = {}
    for path, dy in walls:
        k = _node(sc, path)
        if k is None:
            raise KeyError('%s has no node %s' % (sc.label, path))
        if not _world(sc, k):
            raise ValueError('%s stands below a moved parent: its place is not a world place' % path)
        lab = J.labels('dd', sc.cls(k))
        def fn(us, dy=dy):
            i = lab.index('ZGEOM[2]')
            x, y, z = (struct.unpack('<f', t[1])[0] for t in us[i][1:-1])
            us[i] = [us[i][0]] + [(0x0a, struct.pack('<f', v)) for v in (x, y + dy, z)] + [us[i][-1]]
        kl_fa.edit(sc, k, None, fn)
        out[k] = dy
        log('  kl_escape: %s sunk by %g (its top is the yard\'s floor now)' % (path.rsplit('\\', 1)[1], -dy))
    return out


def money_reach(sc, log=print, reach=REACH):
    """OnlineMoneyContainer nodes whose own TriggerBox2 ('Open') reaches less than `reach`, and the
    TriggerBox2 of their loot: radius = reach. GUESS (re/escape.md 4.1): stock has 125 on all 117
    containers and Dead Men's cash drawers, which work, have 125; the garage boxes have 80."""
    n = 0
    def widen(k):
        nonlocal n
        for i, (nm, body) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) != 'TriggerBox2':
                continue
            v = [kl_fa.value(sc, u) for u in units(body[1:-1])]
            if len(v) == 7 and isinstance(v[2], float) and 0 < v[2] < reach:
                kl_fa.edit(sc, k, i, lambda us: us.__setitem__(2, [(0x0a, struct.pack('<f', reach))]))
                n += 1
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyContainer'):
        widen(k)
        for s in (v[0] if v and isinstance(v[0], list) else []):
            for j in sc.resolve(s):
                widen(j)
    if n:
        log('  kl_escape: %d money-container triggers with a reach below %g set to %g' % (n, reach, reach))
    return n


def repair(sc, log=print):
    """Everything above on the joined .prp scene -> {'sink': {node: dy}, 'reach': count}."""
    return {'sink': open_wall(sc, log), 'reach': money_reach(sc, log)}


def place_entities(sc, ents, done, log=print):
    """The .gms side of open_wall: ents = list(kl_scene.Scene.entities()) of the joined scene
    (entity k - 1 is node k). Moves each sunk entity's record like its .prp node and returns the
    REF ids whose collision has to go (cut_collision)."""
    refs = set()
    for k, dy in (done or {}).get('sink', {}).items():
        e = ents[k - 1]
        if e.name.decode('latin1') != sc.names[k]:
            raise ValueError('entity %d is %r, node %d is %s' % (k - 1, e.name, k, sc.names[k]))
        x, y, z = struct.unpack_from('<3f', e.trans, 0)
        e.trans = struct.pack('<3f', x, y + dy, z) + e.trans[12:]
        refs.add(e.ref)
    return refs


def cut_collision(hvk, refs, log=print):
    """Take the placements of the entities `refs` (REF ids of the joined level) out of a joined
    kl_hvk.Hvk, in place. A static placement is replaced by a copy of another kept static
    placement with that one's own MOPP code (kl_hvk.remap's filler): the list codes address static
    placements by their position in the file and return this one only inside the box of the object
    that was there - where the filler's own code finds nothing, unless the filler happens to
    overlap that box, and then it is geometry that collides there anyway. -> the Hvk."""
    if not refs:
        return hvk
    keep = {kl_hvk.ref(i): kl_hvk.ref(i) for s in hvk.shapes for i in s.inst if kl_hvk.ref(i) not in refs}
    n = collections.Counter(s.type for s in hvk.shapes for i in s.inst if kl_hvk.ref(i) in refs)
    before = hvk.static_count()
    hvk.shapes = kl_hvk.remap(hvk, keep, filler=kl_hvk.first_static(hvk.shapes, keep))
    if hvk.static_count() != before:
        raise ValueError('static placements %d -> %d: the list codes would address the wrong ones' % (before, hvk.static_count()))
    log('  kl_escape: collision of %d entities taken out of the .HVK (placements by shape type: %s)' % (len(refs), dict(n)))
    return hvk


@contextlib.contextmanager
def applied(log=print):
    """kl_graft.build with the repairs, patched in from outside: kl_fa.repair (the joined .prp),
    kl_scene.Scene.write (the joined .gms, just before it is written) and kl_hvk.join."""
    st = {}
    fa_repair, write, join = kl_fa.repair, kl_scene.Scene.write, kl_hvk.join
    def repair2(sc, kept=(), log=log):
        r = fa_repair(sc, kept, log)
        st['sc'], st['done'] = sc, repair(sc, log)
        return r
    def write2(self):
        if 'done' in st and 'refs' not in st:
            st['refs'] = place_entities(st['sc'], list(self.entities()), st['done'], log)
        return write(self)
    def join2(*a, **kw):
        return cut_collision(join(*a, **kw), st.get('refs'), log)
    kl_fa.repair, kl_scene.Scene.write, kl_hvk.join = repair2, write2, join2
    try:
        yield st
    finally:
        kl_fa.repair, kl_scene.Scene.write, kl_hvk.join = fa_repair, write, join


# ------------------------------------------------------------------ the walk test
class Walk:
    """Where a character can walk, from the collision alone. Every triangle of the non-convex
    static (type 1) and key-framed (type 4) shapes is sampled every STEP units into CELL-unit
    cells; a cell's floors are its samples on triangles within 45 degrees of level. A step to a
    neighbouring cell is allowed UP up / DOWN down and blocked by any sample LO..HI above the floor
    it would stand on. LIMITS: no character radius, no climbing, no doors that open, convex shapes
    (crates, rigid bodies) ignored - a yes means 'the collision leaves a way', nothing more."""
    CELL, STEP, UP, DOWN, LO, HI = 20.0, 10.0, 45.0, 60.0, 55.0, 165.0

    def __init__(self, hvk, box=(-5200.0, 6200.0, -13600.0, 2800.0), skip=()):
        self.x0, self.x1, self.z0, self.z1 = box
        self.grid = collections.defaultdict(list)       # cell -> [(y, is floor, REF id)]
        C, S = self.CELL, self.STEP
        for s in hvk.shapes:
            if s.type not in (kl_hvk.STATIC, kl_hvk.KEYFRAMED) or s.convex:
                continue
            vs = [struct.unpack_from('<3f', s.verts, i * s.vstride) for i in range(len(s.verts) // s.vstride)]
            idx = struct.unpack('<%dH' % (len(s.idx) // 2), s.idx)
            for inst in s.inst:
                r = kl_hvk.ref(inst)
                if r in skip:
                    continue
                p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
                w = [tuple(100 * (p[a] + m[3 * a] * v[0] + m[3 * a + 1] * v[1] + m[3 * a + 2] * v[2]) for a in range(3)) for v in vs]
                if max(v[0] for v in w) < self.x0 or min(v[0] for v in w) > self.x1 or \
                        max(v[2] for v in w) < self.z0 or min(v[2] for v in w) > self.z1:
                    continue
                for t in range(0, len(idx) - 2, 3):
                    a, b, c = w[idx[t]], w[idx[t + 1]], w[idx[t + 2]]
                    e1, e2 = (b[0] - a[0], b[1] - a[1], b[2] - a[2]), (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                    n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
                    ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
                    if ln < 1e-6:
                        continue
                    floor = abs(n[1]) / ln > 0.7
                    n1 = int(math.sqrt(e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2) / S) + 1
                    n2 = int(math.sqrt(e2[0] ** 2 + e2[1] ** 2 + e2[2] ** 2) / S) + 1
                    seen = set()
                    for i in range(n1 + 1):
                        u = i / n1
                        for j in range(int((1 - u) * n2 + 1e-9) + 1):
                            v = j / n2
                            x, z = a[0] + u * e1[0] + v * e2[0], a[2] + u * e1[2] + v * e2[2]
                            if not (self.x0 <= x < self.x1 and self.z0 <= z < self.z1):
                                continue
                            y = a[1] + u * e1[1] + v * e2[1]
                            key = (int((x - self.x0) // C), int((z - self.z0) // C), int(y // 10))
                            if key not in seen:
                                seen.add(key)
                                self.grid[key[0], key[1]].append((y, floor, r))

    def cell(self, x, z):
        return int((x - self.x0) // self.CELL), int((z - self.z0) // self.CELL)

    def centre(self, c):
        return self.x0 + (c[0] + .5) * self.CELL, self.z0 + (c[1] + .5) * self.CELL

    def floor(self, x, y, z):
        """The cell of a place and its floor nearest to y (None: no floor there)."""
        c = self.cell(x, z)
        fl = [yy for yy, f, _r in self.grid.get(c, ()) if f]
        return (c, min(fl, key=lambda v: abs(v - y))) if fl else (c, None)

    def flood(self, start, down=None):
        """-> ({cell: floor y}, {cell: the cell it was reached from}, {REF id: cells it blocked}).
        Breadth first, so the parents give a shortest way in cells."""
        down = self.DOWN if down is None else down
        c0, y0 = self.floor(*start)
        if y0 is None:
            raise ValueError('no floor at %s' % (start,))
        seen, par, block, q = {c0: y0}, {c0: None}, collections.defaultdict(set), collections.deque([c0])
        while q:
            c = q.popleft()
            y = seen[c]
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + d[0], c[1] + d[1])
                g = self.grid.get(n)
                if n in seen or not g:
                    continue
                cand = [yy for yy, f, _r in g if f and -down <= yy - y <= self.UP]
                if not cand:
                    continue
                ny = max(cand)
                bl = [r for yy, _f, r in g if ny + self.LO < yy < ny + self.HI]
                if bl:
                    for r in bl:
                        block[r].add(n)
                    continue
                seen[n], par[n] = ny, c
                q.append(n)
        return seen, par, block

    def inside(self, seen, box):
        (cx, cy, cz), (hx, hy, hz) = box
        return [c for c, y in seen.items() if abs(self.centre(c)[0] - cx) < hx and abs(self.centre(c)[1] - cz) < hz and abs(y - cy) < hy]

    def way(self, seen, start, goal, margin=6):
        """Way points (x, y, z) from start to goal over the reached cells: the cheapest path where
        a cell within `margin` cells of the region's edge costs more (keeps off walls), then
        thinned to the corners a straight walk cannot cut. None if the goal was not reached."""
        a, b = self.cell(start[0], start[2]), self.cell(goal[0], goal[2])
        if a not in seen or b not in seen:
            return None
        near = lambda c: sum((c[0] + i, c[1] + j) not in seen or abs(seen[(c[0] + i, c[1] + j)] - seen[c]) > self.UP
                             for i in range(-margin, margin + 1) for j in range(-margin, margin + 1))
        cost, dist, par, pq = {}, {a: 0.0}, {a: None}, [(0.0, a)]
        while pq:
            d, c = heapq.heappop(pq)
            if c == b:
                break
            if d > dist[c]:
                continue
            for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (c[0] + i, c[1] + j)
                if n not in seen or not -self.DOWN <= seen[n] - seen[c] <= self.UP:
                    continue
                if i and j and ((c[0] + i, c[1]) not in seen or (c[0], c[1] + j) not in seen):
                    continue
                if n not in cost:
                    cost[n] = 1.0 + 0.25 * near(n)
                nd = d + cost[n] * (1.414 if i and j else 1.0)
                if nd < dist.get(n, 1e18):
                    dist[n], par[n] = nd, c
                    heapq.heappush(pq, (nd, n))
        if b not in par:
            return None
        cells = []
        while b is not None:
            cells.append(b)
            b = par[b]
        cells.reverse()
        def clear(p, q):
            n = max(abs(q[0] - p[0]), abs(q[1] - p[1]))
            last = seen[p]
            for t in range(1, n + 1):
                c = (round(p[0] + (q[0] - p[0]) * t / n), round(p[1] + (q[1] - p[1]) * t / n))
                if c not in seen or not -self.DOWN <= seen[c] - last <= self.UP or near(c) > 0:
                    return False
                last = seen[c]
            return True
        pts, i = [cells[0]], 0
        while i < len(cells) - 1:
            j = len(cells) - 1
            while j > i + 1 and not clear(cells[i], cells[j]):
                j -= 1
            pts.append(cells[j])
            i = j
        # in a narrow place no straight cut is 'clear' and every cell stays: of such a run keep
        # only the points 120 units apart (the run is straight at this scale)
        out = [pts[0]]
        for c in pts[1:-1]:
            if math.dist(self.centre(c), self.centre(out[-1])) >= 120:
                out.append(c)
        out.append(pts[-1])
        return [(self.centre(c)[0], seen[c], self.centre(c)[1]) for c in out]


def _ref_names(zf_or_level, game=None):
    """{REF id: entity name} of a level archive (path) or a stock level name."""
    path = zf_or_level if os.path.isfile(zf_or_level) else J.level_zip(zf_or_level, game)
    with zipfile.ZipFile(path) as z:
        nm = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        sc = kl_scene.Scene(kl_gms.unpack(z.read(nm['.gms'])), z.read(nm['.buf']))
        hvk = kl_hvk.Hvk(z.read(nm['.hvk']))
    names = {}
    for e in sc.entities():
        names.setdefault(e.ref, e.name.decode('latin1'))
    return hvk, names


def report(hvk, names, log=print, yard=YARD, single=True):
    """The walk test of a level's collision: yard -> exit trigger -> boarding box. With `single`
    also which single object, taken out, would join the two sides. -> (Walk, cells reached from
    the yard, True if the exit trigger is reached)."""
    w = Walk(hvk)
    seen, _par, block = w.flood(yard)
    ex, bo = w.inside(seen, EXIT_BOX), w.inside(seen, BOARD_BOX)
    xs = [w.centre(c) for c in seen]
    log('walk test from the yard %s: %d cells, x %d..%d, z %d..%d; inside the exit trigger: %d, inside the boarding box: %d' % (
        tuple(int(v) for v in yard), len(seen), min(x for x, _z in xs), max(x for x, _z in xs), min(z for _x, z in xs), max(z for _x, z in xs), len(ex), len(bo)))
    if not ex and single:
        seen_b, _p, block_b = w.flood((3100.0, 5.0, 0.0))
        log('  from the van\'s street (3100, 5, 0): %d cells, %d inside the exit trigger; objects that bound BOTH sides:' % (len(seen_b), len(w.inside(seen_b, EXIT_BOX))))
        for r in sorted(set(block) & set(block_b), key=lambda r: -min(len(block[r]), len(block_b[r]))):
            w2 = Walk(hvk, (-5200.0, 6200.0, -5200.0, 2800.0), skip={r})
            s2, _p2, _b2 = w2.flood(yard)
            xa = [w.centre(c) for c in block[r]]
            log('    REF %-6d %-46s x %d..%d z %d..%d: taken out, the exit trigger is %s' % (
                r, names.get(r, '?'), min(x for x, _z in xa), max(x for x, _z in xa), min(z for _x, z in xa), max(z for _x, z in xa),
                'REACHED' if w2.inside(s2, EXIT_BOX) else 'still out of reach'))
    return w, seen, bool(ex)


def route(w, seen, log=print, legs=None):
    """Print the way points of each leg for klauto ('goto x z radius timeout sprint keep')."""
    stop = (BOARD_BOX[0][0] - 150.0, VAN_STOP[1], VAN_STOP[2] - 40.0)    # inside the boarding box, beside the van's stop
    legs = legs or [('yard, f-live\'s way point by the west door -> through the opened wall -> the van', WEST_DOOR, stop),
                    ('garage, at money box 11 -> west door -> yard -> the van', BOX_11, stop)]
    out = []
    for title, a, b in legs:
        pts = w.way(seen, a, b)
        log('route: %s' % title)
        if pts is None:
            log('  NOT REACHABLE in the walk test')
            continue
        first = next((p for p in pts if abs(p[0] - EXIT_BOX[0][0]) < EXIT_BOX[1][0] and abs(p[2] - EXIT_BOX[0][2]) < EXIT_BOX[1][2]), None)
        for p in pts:
            log('  goto %d %d 110 12000 sprint keep        ; y %d%s' % (p[0], p[2], p[1], '  <- first way point inside ExitTrigger_01' if p is first else ''))
        log('  length %d units; the van\'s spline ends at (%d, %d, %d), the boarding box is x %d..%d, z %d..%d' % (
            sum(math.dist((p[0], p[2]), (q[0], q[2])) for p, q in zip(pts, pts[1:])), *VAN_STOP,
            BOARD_BOX[0][0] - BOARD_BOX[1][0], BOARD_BOX[0][0] + BOARD_BOX[1][0], BOARD_BOX[0][2] - BOARD_BOX[1][2], BOARD_BOX[0][2] + BOARD_BOX[1][2]))
        out.append(pts)
    return out


def containers(sc, w, seen, log=print):
    """Where to stand for each money container: the reached cell nearest to the trigger's node
    whose floor is within 120 of it in height. World place = the sum of the node's and its
    parents' places (true while no parent is rotated: checked)."""
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyContainer'):
        pos, j, ok = [0.0, 0.0, 0.0], k, True
        while j > 0:
            nv = kl_fa.node_values(sc, j)
            # a rotated node turns what stands below it; only a guess if that is not at its origin
            ok = ok and (max(abs(x) for x in pos) < 1.0 or [round(x) for x in nv[1]] == [0, 0, 1, 0, 1, 0, 1, 0, 0])
            pos = [a + b for a, b in zip(pos, nv[2])]
            j = sc.parent[j]
        rad = next(([kl_fa.value(sc, u) for u in units(b[1:-1])][2] for nm, b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'TriggerBox2'), 0.0)
        c0 = w.cell(pos[0], pos[2])
        best = None
        for i in range(-8, 9):
            for jj in range(-8, 9):
                c = (c0[0] + i, c0[1] + jj)
                if c in seen and abs(seen[c] - pos[1]) < 120:
                    d = math.dist(w.centre(c), (pos[0], pos[2]))
                    if 40 <= d and (best is None or d < best[0]):
                        best = (d, c)
        log('  %-58s at (%d, %d, %d) reach %g%s: stand at %s' % (
            '\\'.join(sc.path[k].split('\\')[-2:]), pos[0], pos[1], pos[2], rad, '' if ok else ' (a parent is rotated: place is a GUESS)',
            'outside the walk region of the yard (the hall is not joined to it in the walk test)' if best is None else '(%d, %d), %d away, floor y %d' % (*w.centre(best[1]), best[0], seen[best[1]])))


# ------------------------------------------------------------------ command line
def test(out, s_name='F07', m_name='M03_FA_A', log=print):
    import kl_graft
    from kl_port_check import workdir
    out = os.path.abspath(out)
    if os.path.normcase(out).startswith(os.path.normcase(os.path.join(workdir(), 'build', 'install'))):
        raise SystemExit('refusing to build into the work folder\'s build\\install')
    os.makedirs(out, exist_ok=True)
    old = os.environ.get('KL_GRAFT_OUT')
    os.environ['KL_GRAFT_OUT'] = out
    try:
        with applied(log) as st:
            path, problems = kl_graft.build(s_name, m_name, 'F01', log)
    finally:
        if old is None:
            del os.environ['KL_GRAFT_OUT']
        else:
            os.environ['KL_GRAFT_OUT'] = old
    bad = len(problems)
    log('kl_graft verify: problems: %d' % len(problems))
    if not st.get('refs'):
        log('FAIL: no wall was opened'); bad += 1
    sc, snd, loc = kl_fa.load(path)
    fs = kl_fa.check(sc, snd, loc)
    for f in fs:
        log('  ' + str(f))
    worst = sum(f.sev <= kl_fa.BROKEN for f in fs)
    log('kl_fa.check: %d CRASH / BROKEN findings' % worst)
    bad += worst
    # the built files say what was done: the node's place, the entity's, the collision
    hvk, names = _ref_names(path)
    for p, dy in OPEN.get(m_name, []):
        k = _node(sc, p)
        y = kl_fa.node_values(sc, k)[2][1]
        here = [s.type for s in hvk.shapes for i in s.inst if names.get(kl_hvk.ref(i)) == sc.names[k] and kl_hvk.ref(i) in st['refs']]
        log('  built: %s .prp y %g; placements left in the .HVK under its REF: %d' % (sc.names[k], y, len(here)))
        bad += bool(here)
    w, seen, ok = report(hvk, names, log, single=False)
    if not ok:
        log('FAIL: the exit trigger is still out of reach in the walk test'); bad += 1
    else:
        route(w, seen, log)
        log('money containers (reach after money_reach):')
        containers(sc, w, seen, log)
    log('RESULT: %s' % ('ok' if not bad else '%d failures' % bad))
    return bad


def main():
    a = sys.argv[1:]
    if a[:1] == ['walls']:
        level = a[1] if len(a) > 1 else 'M03_FA_A'
        hvk, names = _ref_names(level, 'dm')
        report(hvk, names)
    elif a[:1] == ['test'] and len(a) >= 2:
        sys.exit(1 if test(a[1], *(a[2:4])) else 0)
    elif a[:1] == ['route'] and len(a) == 2:
        hvk, names = _ref_names(a[1])
        w, seen, ok = report(hvk, names, single=False)
        if ok:
            route(w, seen)
            containers(kl_fa.load(a[1])[0], w, seen)
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
