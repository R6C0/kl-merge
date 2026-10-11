#!/usr/bin/env python3
"""
The route test: can a round be WALKED - asked of a level's collision (.HVK) and its navigation mesh, offline.
One tool for what the second agents of the campaign study each wrote for their own place (re/campaign_fa.md
'Gap closed: the route without a run-time event'; what was taken from which script, and every check with its
output: re/bank_campaign.md 'Stage T3'). Read only; nothing here builds, installs or starts anything.

    python kl_route.py walk <level> --from x,y,z --to x,y,z [--via x,y,z ...] [--open <REF or name>,...]
        is there a walkable way through the points; if not, the objects in the way by name and REF, nearest
        first, and whether the way is free once they are out; then the way an AI is given over the mesh,
        sampled against the collision                                              (exit 0 = free, 1 = not)
    python kl_route.py stations <level> <x,y,z | name=x,y,z> ... [--near N] [--open ...]
        each place: on the navigation mesh? on which part? reached from the FIRST place in the collision
        (the walk comes to a free floor within N of it, default 86; a money container is taken from 125)?
        and what stands before the ones that are not                               (exit 0 = all reached)
    python kl_route.py doors <level> --from x,y,z --to x,y,z [--via ...] [--open ...]
        the closures on the way in the order they are met, and of each whether it is NECESSARY: with every
        other one out and this one in its place the way is shut                    (exit 0 = free with all out)
  <level>      a build folder (its one *_Main.zip, or the study's walk_members.zip), an archive, or the name
               of a stock level of either game ('M03_A', 'F07': the copy in KL_PortBackup wins).
  a place      x,y,z in world units, y = the floor's or the mesh's height there (name=x,y,z to label it).
  --open       objects taken out for the test: a REF id, or text looked for in the entities' paths (case
               ignored) that stands for every match AND everything below it - a door group opens its leaves.
  --hidden-out leave out what is hidden at load      --who all|hero|npc   whose collision counts (below)
  --rigid      count rigid bodies and vehicles too   --down N             a drop a walker takes (default 60)
  --no-mesh    do not read the navigation mesh

For other tools (the same answers as dicts; `src` is <level> as above, or a Level from load()):
    route(src, pts, opened=(), ...)      {'free', 'length', 'legs': [{'free', 'length', 'crossed', 'off', ...}]}
    blockers(src, pts, opened=(), ...)   ([what is in the way, nearest first], free once they are out)
    stations(src, pts, opened=(), near=86, ...)   [{'at', 'mesh', 'part', 'reached', 'gap', 'in', 'behind', ...}]
    doors(src, pts, opened=(), ...)      {'closures': [{'refs', 'objects', 'necessary', 'set', ...}], 'sets', 'free'}
    mesh_way(src, pts, opened=(), ...)   the way an AI is given, sampled: [{'samples', 'nofloor', 'hit', 'blockers', ...}]
  options of all five: who='all', rigid=False, hidden=True (False = --hidden-out), down=60, mesh=True.

THE WALKER (whose number each one is, and what is not known)
  grid     Cells of 20 units, made only where a search comes (blocks of 16 x 16 cells). A cell's FLOORS are
           the triangles within 45 degrees of level (|normal y| > 0.7, either side up) under its middle;
           every other triangle is sampled every 10 units. Cell, pitch and floor rule are kl_escape.Walk's:
           the test that named the yard wall of the Fragile Alliance bank as the cut, which seven live tries
           bore out, and whose opened wall bots then crossed (re/escape.md 3; run H0_DM03).
  step     to one of the eight cells round it, onto the highest floor there that is at most 45 above and 60
           below (Walk's rule). ASSUMPTION: the step of Dog Days' character was never read in kl2.exe.
           No climbing, no vault, no drop of more than 60 (--down): a wall Dead Men's players climb is a wall.
  body     a column 60 x 60 (the cell and the eight round it: half width 30, the radius of the Havana and
           prison walks), from 55 to 165 above the floor stood on (Walk's heights); any counted collision in
           it stops the walker and is named. A gap of 80 always passes, one under 60 never. The bank and club
           walks of the study had NO width (one cell): their counts of reached cells are larger for it.
           ASSUMPTION: the game's real body was not read.
  counted  STATIC and KEYFRAMED placements. A mesh shape by its triangles; a convex shape by its plane
           equations (MEASURED on the 850 convex shapes of M03_A, M11_B and F07: every vertex of a shape
           satisfies n.v + d <= 0 for every plane, to 1e-5, and every plane touches a vertex), never beyond
           the box of its vertices (the planes of a flat shape, a car window, do not close it), tested on
           upright lines 5 apart: a plate thinner than that can slip through. A convex shape is never a
           floor. RIGID bodies, vehicles and weapons are left out (they move; --rigid counts the first two).
           A car's doors, wheels and windows are KEYFRAMED and DO count, where the file has the car.
  flags    EVERY sub-part counts whatever its collision flags say (the study's rule): a camera-only plane
           is a wall here. --who hero / npc applies a reading of the flag bits by OBJECT NAMES only (census
           of M03_A, M11_B, M08_A, F07; nothing read in the exe): 0x20 stops every character, 0x8 the heroes
           only (`ColiObj_Hero*`, `OnlyHero`, `ColiObj_Player*`), 0x40 the camera, 0x10 sight, 0x2 shots;
           hero = 0x20 or 0x8 counts, npc = 0x20. ASSUMPTION - and whether a Fragile Alliance player or an AI
           heister is a 'hero' to that filter is not known. Every object named is printed with its flags.
  a key-framed placement (a door leaf, a lift, a fence that falls) stands where the .HVK has it: the level
           file's place, the door SHUT. MEASURED: in stock M03_A and F07 and in the study's two built bank
           archives every STATIC / KEYFRAMED placement stands exactly where its entity's .gms chain puts it
           (0 of 3,653, 1,859, 3,467 and 3,479 are more than 2 units off). A leaf that was moved at build
           time while its placement stayed, or the other way round, is therefore reported ('MOVED'); which
           of the two the game then uses for a key-framed body is NOT known. The two traps of taking a
           closure out (re/campaign_fa.md G1.1: a leaf under a turned group, and .prp / .gms holding
           different local places under a group with flag 0x40000000) do not touch this test: it reads world
           places from the .HVK and names from the .gms, never a local place.
  a hidden twin (an entity hidden at load - flag 0x400 on it or above it - that owns a placement: the
           prison's `FenceFall` behind `FenceFall_Pre`, the bank's `Vault_POST`) COUNTS, because whether a
           hidden body collides is not known; its floors count too (the Capitol's broken corner is one, and
           the way out runs over it). --hidden-out leaves them out; a verdict that hangs on it says so.
  a place  is walked from / to GROUND: a free floor from which the walker gets 300 away and to more than 400
           floors (GUESS; the top of a table, a chair or a counter is a free floor too, and a place given at
           the mesh's height is as near to it as to the floor). Ground beside the place and within a step of
           its height: the ground within 86 of it, and never the far side of a wall (nothing may stand
           between). A place that stands IN something (the Capitol's checkpoint 5 lies in a rubble block):
           the ground nearest to it within 200, as the Havana walk took the nearest mesh cell within 2 m -
           and the leg says how far from the place it began or ended.
  thinnest crossing  when the way is shut the search goes on THROUGH objects, each cell entered at the price
           of the objects standing in it, and names what the cheapest way crosses (the Havana second agent's
           search; `doors` and `blockers` take those out and ask again until the way is free). With a mesh a
           crossing is taken only on a mesh polygon - where the designers let people walk: a doorway, not a
           wall - without one anywhere. One leaf of a double door is enough for it: `doors` names the leaf
           crossed and counts SETS by parent and name (less the number and LEFT / RIGHT).
  the mesh (Dog Days form; a Dead Men block goes through kl_pf4.convert): parts by the edges' neighbour
           fields, the negative-coded ones too (the engine walks them: re/campaign_fa_park.md Verification 8).
           A place is ON it when a polygon lies under it within 130 in height (kl_fa_bots.DY), or it lies on
           an edge of one (within 5: the bank's rope ends are 0.5 outside the yard's polygon). The WAY an AI
           is given: from the middle of the first place's polygon through the middles of the shared edges
           to the middle of the last one's (the park second agent's line; edges of 100 or more if there is
           such a way, the mesh's links - drops, one way, not sampled - only if there is no way without),
           sampled every 25: a collision floor within 90 of the mesh, and the body column free. A path
           blocker in state eBlocking whose box the line passes (in the plan, within 100 in height: GUESS,
           what a blocker does to the mesh was not read) is named: there the AI stops where a player walks
           through (the prison's cage door, re/campaign_fa.md G1.4). The verdict FREE / NOT FREE is the
           collision's; the mesh way is reported beside it.
LIMITS: all of the above. Nothing that moves is simulated; bullets and sight are not tested. A yes means 'the
collision leaves a way a body of that size can walk', a no names what is in it.
"""
import bisect, collections, heapq, math, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_hvk, kl_pf4, kl_scene

CELL = 20.0                     # kl_escape.Walk's cell
PITCH = 10.0                    # ... and how often a triangle that is not a floor is sampled
FLOORISH = 0.7                  # |normal y| above this is a floor (Walk; 45.6 degrees)
UP, DOWN = 45.0, 60.0           # a step (Walk). ASSUMPTION: see the docstring
LO, HI = 55.0, 165.0            # the body column over the floor (Walk)
WIDE = 1                        # ... and its width: the cell and WIDE cells round it = half width 30 (the Havana walk's radius)
HULL = 5.0                      # a convex shape is tested on upright lines this far apart. GUESS (a quarter of a cell)
BLOCK = 16                      # cells along a block that is rasterized in one go
NEAR, NEAR_Y = 86.0, 100.0      # GUESS (argued, not measured: with 70 the bank's trolley place fails by 2 units). A place counts as
                                # reached from a free floor within 86 in the plan and 100 in height: the bank walk's
                                # rule (a floor within two cells: a square, 56 at its corners) was for a walker WITHOUT width; this
                                # one's half width (30) is added, because it cannot bring its middle that much nearer to a thing
GAP = 200.0                     # GUESS: how far round a place that stands IN something its floor is looked for (the Havana walk: 2 m)
ISLAND, ISLAND_N = 300.0, 400   # GUESS: a free floor is ground when the walker gets this far from it and to this many floors
                                # (a table top, a bank counter's 8 m and a shut room of 4 x 4 m do not)
CROSS = 1e7                     # price of a cell an object stands in, per object: far above any length in units
ROUNDS = 24                     # blockers(): at most this many times 'take out what was crossed and ask again'
MESH_DY = 130.0                 # a place is on a polygon within this height of it (kl_fa_bots.DY)
PORTAL = 100.0                  # the mesh way does not use a shared edge narrower than this (park second agent: a person is about 60 wide)
LINE, LINE_FLOOR = 25.0, 90.0   # ... is sampled this often, and wants a collision floor within this of the mesh height. GUESS: the
                                # 90 (the park agent's 25 gives the park's 1,271 samples)
PB_DY = 100.0                   # GUESS: a path blocker's box counts this far above and below itself
STATIC, RIGID, VEHICLE, KEYFRAMED = kl_hvk.STATIC, kl_hvk.RIGID, kl_hvk.VEHICLE, kl_hvk.KEYFRAMED
TYPE = {1: 'STATIC', 2: 'RIGID', 3: 'VEHICLE', 4: 'KEYFRAMED', 5: 'WEAPON'}
WHO = {'all': None, 'hero': 0x28, 'npc': 0x20}
BITS = ((0x40, 'camera'), (0x10, 'sight'), (0x2, 'shots'))     # the name census; 0x20 = characters, 0x8 = heroes only: _reading()
_BIG = 1 << 62
_NONE = frozenset()
_EIGHT = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


# ------------------------------------------------------------------ the level
def archive(src):
    """The archive of <level>: a build folder's one *_Main.zip (or the study's walk_members.zip), an archive
    path, or a stock level by name (kl_prpjoin.level_zip)."""
    if os.path.isdir(src):
        names = sorted(os.listdir(src))
        hit = [n for n in names if n.lower().endswith('_main.zip')] or [n for n in names if n.lower() == 'walk_members.zip']
        if len(hit) != 1:
            raise ValueError('%s: %d level archives (*_Main.zip) in the folder, need one' % (src, len(hit)))
        return os.path.join(src, hit[0])
    if os.path.isfile(src):
        return src
    import kl_prpjoin
    return kl_prpjoin.level_zip(src)


class Level:
    """A level's scene (kl_scene) and collision (kl_hvk): entities by REF id with their paths, what is hidden
    at load, what each REF owns in the .HVK."""

    def __init__(self, src):
        self.stock = None if os.path.exists(src) else src       # a stock level's name
        self.zp = archive(src)
        with zipfile.ZipFile(self.zp) as z:
            m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
            self.scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
            self.hvk = kl_hvk.Hvk(z.read(m['.hvk']))
        self.ents = list(self.scene.entities())                 # scene order = .prp node k - 1
        self.label = self.stock or '/'.join(self.zp.replace('\\', '/').split('/')[-2:])
        self.path, self.by_ref, hid = {}, collections.defaultdict(list), {}
        for e in self.ents:                                     # a parent comes before its children
            nm = e.name.decode('latin1')
            self.path[e] = nm if e.parent is None else self.path[e.parent] + '\\' + nm
            hid[e] = bool(e.flags & 0x400) or (e.parent is not None and hid[e.parent])
            self.by_ref[e.ref].append(e)
        self.ent = {r: es[0] for r, es in self.by_ref.items()}  # the first of a REF id, as kl_escape._ref_names
        self.hidden = {r for r, es in self.by_ref.items() if all(hid[e] for e in es)}
        self.owns = collections.defaultdict(list)               # REF -> [(shape type, convex, sub-part flags)]
        for s in self.hvk.shapes:
            fl = tuple(sorted({f for _su, f, _n in s.sub})) or (s.flags,)
            for inst in s.inst:
                self.owns[kl_hvk.ref(inst)].append((s.type, bool(s.convex), fl))
        self._grid, self._mesh, self._frames, self._pb = {}, False, None, False

    # -- names
    def name(self, r, parts=2):
        """The last `parts` parts of the path of the entity with REF id r."""
        e = self.ent.get(r)
        return '(no entity)' if e is None else '\\'.join(self.path[e].split('\\')[-parts:])

    def kind(self, r):
        """What the REF id owns in the .HVK, as text: 'KEYFRAMED mesh 0x72'."""
        out = []
        for t, cv, fl in self.owns.get(r, ()):
            s = '%s %s %s' % (TYPE.get(t, t), 'convex' if cv else 'mesh', '+'.join('%#x' % f for f in fl))
            if s not in out:
                out.append(s)
        return ', '.join(out) or 'no placement'

    def refs(self, spec):
        """The REF ids `spec` stands for: a number (or a set / list of them) is taken as it is; text is looked
        for in the entities' paths, case ignored, and stands for every match and everything below it."""
        if isinstance(spec, (set, frozenset, list, tuple)):
            return set().union(*[self.refs(x) for x in spec]) if spec else set()
        if isinstance(spec, int) or str(spec).strip().isdigit():
            return {int(spec)}
        needle, out = str(spec).strip().lower(), set()
        for e in self.ents:
            if needle in self.path[e].lower() and not (e.parent is not None and needle in self.path[e.parent].lower()):
                out.update(c.ref for c in e.walk())             # the topmost match and its subtree
        return out

    # -- places
    def frames(self):
        """{entity: (R, T)}: world = T + R . local down the .gms chain (kl_maps.world's reading, as
        kl_fa_bots.frames)."""
        if self._frames is None:
            out, I = {}, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            for e in self.ents:
                R, T = out[e.parent] if e.parent is not None else (I, (0.0, 0.0, 0.0))
                r, t = struct.unpack('<9f', e.rot[:36]), struct.unpack('<3f', e.trans[:12])
                m = [r[6:9], r[3:6], r[0:3]]
                m = [[m[j][i] for j in range(3)] for i in range(3)]
                out[e] = ([[sum(R[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)],
                          tuple(T[i] + sum(R[i][j] * t[j] for j in range(3)) for i in range(3)))
            self._frames = out
        return self._frames

    def moved(self):
        """[(REF, units apart)] of the STATIC / KEYFRAMED placements that do NOT stand where their entity does
        (more than 2 units): stock and the study's builds have none. See the docstring."""
        fr, out = self.frames(), []
        for s in self.hvk.shapes:
            if s.type not in (STATIC, KEYFRAMED):
                continue
            for inst in s.inst:
                r = kl_hvk.ref(inst)
                p = [100 * v for v in struct.unpack_from('<3f', inst, 0)]
                d = min([math.dist(p, fr[e][1]) for e in self.by_ref.get(r, ())] or [0.0])
                if d > 2.0:
                    out.append((r, d))
        return out

    def path_blockers(self):
        """[(path, R, T, half extents, message, state)] of the PathBlocker boxes, or None when the property
        file cannot be read here (it needs the class schemas: kl_fa / kl_prpjoin)."""
        if self._pb is False:
            self._pb = None
            try:
                import kl_fa
                import kl_prpjoin as J
                if self.scene.game == 'dm' and not self.stock:  # kl_fa.load reads an archive with Dog Days' schemas
                    raise ValueError('a Dead Men archive given by path: name the stock level instead')
                sc = J.Scene.load(self.stock, self.scene.game) if self.stock else kl_fa.load(self.zp)[0]
                fr, out = self.frames(), []
                for k, _i, v in kl_fa.controllers(sc, 'PathBlocker'):
                    lab, nv = J.labels(sc.game, sc.cls(k)), kl_fa.node_values(sc, k)
                    half = [nv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3)]
                    R, T = fr[self.ents[k - 1]]
                    out.append((sc.path[k], R, T, half, v[0], v[1]))
                self._pb = out
            except Exception as ex:                             # no .prp in the archive, no schema: say so, go on
                self._pb_error = '%s: %s' % (type(ex).__name__, ex)
        return self._pb

    def mesh(self):
        """The navigation mesh (Mesh), or None with the reason in mesh_error."""
        if self._mesh is False:
            self._mesh = None
            try:
                if not self.scene.nav:
                    raise ValueError('the level has no mesh block')
                self._mesh = Mesh(self.scene.nav, self.scene.game)
            except Exception as ex:
                self.mesh_error = '%s: %s' % (type(ex).__name__, ex)
        return self._mesh

    def grid(self, who='all', rigid=False, down=DOWN):
        key = (who, bool(rigid), float(down))
        if key not in self._grid:
            self._grid[key] = Grid(self, who, rigid, down)
        return self._grid[key]


_OPEN = {}


def load(src):
    """A Level, read once per process (src: <level>, or a Level)."""
    if isinstance(src, Level):
        return src
    key = os.path.abspath(src) if os.path.exists(src) else src
    if key not in _OPEN:
        _OPEN[key] = Level(src)
    return _OPEN[key]


# ------------------------------------------------------------------ the collision as a grid
class Grid:
    """Floors and collision samples per 20-unit cell, rasterized block by block where they are asked for.
    fl[cell] / so[cell] = sorted [(y, REF)]: the floors / everything that is solid there (floors too)."""

    def __init__(self, lv, who='all', rigid=False, down=DOWN):
        self.lv, self.down = lv, float(down)
        if who not in WHO:
            raise ValueError('who is one of %s' % ', '.join(WHO))
        mask = WHO[who]
        types = (STATIC, KEYFRAMED) + ((RIGID, VEHICLE) if rigid else ())
        self.tris, self.hulls = [], []                  # (a, b, c, REF, steep) / (inverse rotation, position, planes, REF, world box, world vertices)
        self.todo = collections.defaultdict(list)       # block -> what touches it: a triangle k, a hull -1 - k
        self.done, self.whole = set(), set()            # blocks made / steep triangles and hulls sampled (they are sampled whole, once)
        self.fl, self.so, self._hit, self._ground = {}, {}, {}, {}
        self.counted, self.left = collections.Counter(), collections.Counter()
        S = BLOCK * CELL
        for s in lv.hvk.shapes:
            if s.type not in types:
                self.left[s.type] += len(s.inst)
                continue
            vs = [struct.unpack_from('<3f', s.verts, i * s.vstride) for i in range(len(s.verts) // s.vstride)]
            if s.convex:
                if not vs or (mask is not None and not s.flags & mask):
                    self.left['flags'] += len(s.inst)
                    continue
                planes = [struct.unpack_from('<4f', s.planes, 16 * i) for i in range(len(s.planes) // 16)]
            else:
                idx = struct.unpack('<%dH' % (len(s.idx) // 2), s.idx)
                fl = [f for _su, f, n in s.sub for _ in range(n)]       # a sub-part's flags for each of its triangles
                if 3 * len(fl) != len(idx):
                    fl = [s.flags] * (len(idx) // 3)
                tri = [(idx[t], idx[t + 1], idx[t + 2]) for t in range(0, len(idx) - 2, 3) if mask is None or fl[t // 3] & mask]
                if not tri:
                    self.left['flags'] += len(s.inst)
                    continue
            for inst in s.inst:
                r = kl_hvk.ref(inst)
                p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
                w = [(100 * (p[0] + m[0] * v[0] + m[1] * v[1] + m[2] * v[2]), 100 * (p[1] + m[3] * v[0] + m[4] * v[1] + m[5] * v[2]),
                      100 * (p[2] + m[6] * v[0] + m[7] * v[1] + m[8] * v[2])) for v in vs]
                self.counted[s.type] += 1
                if s.convex:
                    box = tuple(f(q[a] for q in w) for f in (min, max) for a in range(3))
                    self._touch(-1 - len(self.hulls), box[0], box[3], box[2], box[5], S)
                    self.hulls.append((_inverse(m), p, planes, r, box, w))
                    continue
                for i0, i1, i2 in tri:
                    a, b, c = w[i0], w[i1], w[i2]
                    e1x, e1y, e1z, e2x, e2y, e2z = b[0] - a[0], b[1] - a[1], b[2] - a[2], c[0] - a[0], c[1] - a[1], c[2] - a[2]
                    nx, ny, nz = e1y * e2z - e1z * e2y, e1z * e2x - e1x * e2z, e1x * e2y - e1y * e2x
                    n2 = nx * nx + ny * ny + nz * nz
                    if n2 < 1e-12:
                        continue
                    self._touch(len(self.tris), min(a[0], b[0], c[0]), max(a[0], b[0], c[0]), min(a[2], b[2], c[2]), max(a[2], b[2], c[2]), S)
                    self.tris.append((a, b, c, r, ny * ny <= FLOORISH * FLOORISH * n2))

    def _touch(self, k, x0, x1, z0, z1, S):
        for bx in range(int((x0 - 0.01) // S), int((x1 + 0.01) // S) + 1):      # the margin: a sample may land a hair outside its triangle's box
            for bz in range(int((z0 - 0.01) // S), int((z1 + 0.01) // S) + 1):
                self.todo[bx, bz].append(k)

    def _make(self, b):
        """Rasterize one block: floors by the cells' middles (this block only), everything else whole."""
        self.done.add(b)
        i0, j0 = b[0] * BLOCK, b[1] * BLOCK
        for k in self.todo.pop(b, ()):
            if k < 0:
                if k not in self.whole:
                    self.whole.add(k)
                    self._hull(self.hulls[-1 - k])
            elif self.tris[k][4]:
                if k not in self.whole:
                    self.whole.add(k)
                    self._steep(self.tris[k])
            else:
                self._flat(self.tris[k], i0, i0 + BLOCK - 1, j0, j0 + BLOCK - 1)
        for i in range(i0, i0 + BLOCK):                 # nothing can be added to this block's cells later: whatever
            for j in range(j0, j0 + BLOCK):             # reaches into it was on its list
                for d in (self.fl, self.so):
                    v = d.get((i, j))
                    if v:
                        v.sort()

    def _flat(self, t, i0, i1, j0, j1):
        a, b, c, r, _steep = t
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-9:
            return
        ua, ub, va, vb = (b[2] - c[2]) / d, (c[0] - b[0]) / d, (c[2] - a[2]) / d, (a[0] - c[0]) / d
        fl, so = self.fl, self.so
        for i in range(max(i0, int(min(a[0], b[0], c[0]) // CELL)), min(i1, int(max(a[0], b[0], c[0]) // CELL)) + 1):
            dx = (i + 0.5) * CELL - c[0]
            for j in range(max(j0, int(min(a[2], b[2], c[2]) // CELL)), min(j1, int(max(a[2], b[2], c[2]) // CELL)) + 1):
                dz = (j + 0.5) * CELL - c[2]
                u, v = ua * dx + ub * dz, va * dx + vb * dz
                if u < -1e-6 or v < -1e-6 or u + v > 1.000001:
                    continue
                e = (u * a[1] + v * b[1] + (1 - u - v) * c[1], r)
                fl.setdefault((i, j), []).append(e)
                so.setdefault((i, j), []).append(e)

    def _steep(self, t):
        a, b, c, r, _steep = t
        e1, e2 = (b[0] - a[0], b[1] - a[1], b[2] - a[2]), (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n1 = int(math.sqrt(e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2) / PITCH) + 1
        n2 = int(math.sqrt(e2[0] ** 2 + e2[1] ** 2 + e2[2] ** 2) / PITCH) + 1
        seen, so = set(), self.so
        for i in range(n1 + 1):
            u = i / n1
            for j in range(int((1 - u) * n2 + 1e-9) + 1):
                v = j / n2
                y = a[1] + u * e1[1] + v * e2[1]
                key = (int((a[0] + u * e1[0] + v * e2[0]) // CELL), int((a[2] + u * e1[2] + v * e2[2]) // CELL), int(y // 10))
                if key not in seen:
                    seen.add(key)
                    so.setdefault(key[:2], []).append((y, r))

    def _hull(self, h):
        inv, p, planes, r, box, w = h
        so = self.so
        for q in w:                                     # its corners, whatever the lines below meet
            so.setdefault((int(q[0] // CELL), int(q[2] // CELL)), []).append((q[1], r))
        dv = (inv[0][1] / 100, inv[1][1] / 100, inv[2][1] / 100)       # one unit up, in the shape's own space
        n = int(CELL / HULL)
        for i in range(int(box[0] // CELL), int(box[3] // CELL) + 1):
            for j in range(int(box[2] // CELL), int(box[5] // CELL) + 1):
                lo, hi = None, None
                for si in range(n):
                    x = (i * CELL + (si + 0.5) * HULL) / 100 - p[0]
                    for sj in range(n):
                        z = (j * CELL + (sj + 0.5) * HULL) / 100 - p[2]
                        o = [inv[k][0] * x - inv[k][1] * p[1] + inv[k][2] * z for k in range(3)]
                        t0, t1 = box[1], box[4]         # never beyond its vertices (the planes of a flat shape do not close it: car windows)
                        for pa, pb, pc, pd in planes:
                            f, g = pa * o[0] + pb * o[1] + pc * o[2] + pd, pa * dv[0] + pb * dv[1] + pc * dv[2]
                            if abs(g) < 1e-12:
                                if f > 0:
                                    t0, t1 = 1.0, 0.0
                                    break
                            elif g > 0:
                                t1 = min(t1, -f / g)
                            else:
                                t0 = max(t0, -f / g)
                            if t0 > t1:
                                break
                        if t0 <= t1:
                            lo, hi = (t0, t1) if lo is None else (min(lo, t0), max(hi, t1))
                if lo is not None:
                    y, cell = lo, so.setdefault((i, j), [])
                    while y < hi:
                        cell.append((y, r)); y += PITCH
                    cell.append((hi, r))

    # -- asking
    def cell(self, x, z):
        return int(x // CELL), int(z // CELL)

    def floors(self, i, j):
        b = (i // BLOCK, j // BLOCK)
        if b not in self.done:
            self._make(b)
        return self.fl.get((i, j), ())

    def hit(self, i, j, y):
        """REF ids of what stands in the body column of a walker on the floor y of cell (i, j)."""
        h = self._hit.get((i, j, y))
        if h is None:
            out, lo, hi = set(), (y + LO, _BIG), (y + HI, -1)
            for ii in range(i - WIDE, i + WIDE + 1):
                for jj in range(j - WIDE, j + WIDE + 1):
                    b = (ii // BLOCK, jj // BLOCK)
                    if b not in self.done:
                        self._make(b)
                    s = self.so.get((ii, jj))
                    if s:
                        for k in range(bisect.bisect_right(s, lo), bisect.bisect_left(s, hi)):
                            out.add(s[k][1])
            h = self._hit[i, j, y] = frozenset(out) if out else _NONE
        return h

    def step(self, i, j, y, opened):
        """The floor of cell (i, j) a walker at height y beside it steps onto (an int), or None."""
        f = self.floors(i, j)
        if f:
            k, lo = bisect.bisect_right(f, (y + UP, _BIG)) - 1, y - self.down
            while k >= 0 and f[k][0] >= lo:
                if f[k][1] not in opened:
                    return int(round(f[k][0]))
                k -= 1
        return None

    def stand(self, p, opened=_NONE, near=NEAR):
        """The floors at a place: [(i, j, y)] of those within `near` of it in the plan (its own cell always) and
        NEAR_Y in height. Order: a free body column before a shut one, a floor within a step (UP) of the
        place's height before one further off (the top of the crate it stands beside), then the nearest."""
        ci, cj = self.cell(p[0], p[2])
        out, n = set(), int(near // CELL) + 1
        for i in range(ci - n, ci + n + 1):
            for j in range(cj - n, cj + n + 1):
                d = math.hypot((i + 0.5) * CELL - p[0], (j + 0.5) * CELL - p[2])
                if d > near and (i, j) != (ci, cj):
                    continue
                for y, r in self.floors(i, j):
                    if r not in opened and abs(y - p[1]) <= NEAR_Y:
                        yq = int(round(y))
                        out.add((bool(self.hit(i, j, yq) - opened), abs(y - p[1]) > UP, d + abs(y - p[1]), i, j, yq))
        return [s[3:] for s in sorted(out)]

    def feet(self, p, opened=_NONE):
        """The floors a walk from or to a place may use: [(i, j, y)]; the search starts on all of them and ends
        on the first it comes to. Only GROUND counts (ground()): the top of a table, a chair or a display
        case is a free floor too, and a place given at the mesh's height (20 - 30 over the floor) is as near
        to it as to the floor. A place that is free ground itself (ground beside it, within a step of its
        height): the ground within NEAR of it at that height, and what is not beside it only when nothing
        stands between the two - never the far side of a wall. A place that stands IN something (a table, a
        rubble block: the campaign's own checkpoint 5 of the Capitol does): the ground nearest to it within
        GAP, as the Havana walk took the nearest mesh cell within 2 m - the caller says how far from the
        place the walk then began or ended. No ground at all: any free floor, then any floor."""
        st = self.stand(p, opened, GAP)
        free = [s for s in st if not self.hit(*s) - opened]
        pool = [s for s in free if self.ground(s, opened)] or free
        step = [s for s in pool if abs(s[2] - p[1]) <= UP]
        if any(self.off(s, p) <= 1.5 * CELL for s in step):
            return [s for s in step if self.off(s, p) <= 1.5 * CELL or (self.off(s, p) <= NEAR and self.between(s, p, opened))]
        pool = step or pool
        if pool:
            d0 = min(self.off(s, p) for s in pool)
            return [s for s in pool if self.off(s, p) <= d0 + 2 * CELL]
        return [s for s in st if self.off(s, p) <= NEAR]

    def ground(self, s, opened=_NONE):
        """True when the free floor s is ground and not the top of a thing: the walker can get ISLAND away
        from it and to more than ISLAND_N floors without crossing anything (a table top, a counter and a
        shut room of 4 x 4 m are not; a place in such a room falls back on its free floors all the same)."""
        memo = self._ground.setdefault(opened, {})
        if s in memo:
            return memo[s]
        seen, q, far, verdict = {s}, collections.deque([s]), False, None
        while q and verdict is None:
            i, j, y = q.popleft()
            for di, dj in _EIGHT:
                ny = self.step(i + di, j + dj, y, opened)
                if ny is None or abs(ny - y) > UP:      # only a step that can be taken back: a seat 54 high is left, never mounted
                    continue
                n = (i + di, j + dj, ny)
                if n in seen or self.hit(*n) - opened:
                    continue
                if n in memo:                           # it joins something already judged
                    verdict = memo[n]
                    break
                seen.add(n); q.append(n)
                far = far or abs(n[0] - s[0]) * CELL > ISLAND or abs(n[1] - s[1]) * CELL > ISLAND
            if verdict is None and far and len(seen) > ISLAND_N:
                verdict = True
        for n in seen:                                  # (the queue ran dry: an island)
            memo[n] = bool(verdict)
        return memo[s]

    def between(self, s, p, allowed):
        """True when the body columns on the straight line from the floor s to the place p hold nothing but
        `allowed` (walked at the height of s, a step up or down where there is a floor to take it)."""
        x0, z0, y = (s[0] + 0.5) * CELL, (s[1] + 0.5) * CELL, s[2]
        n = int(math.hypot(p[0] - x0, p[2] - z0) / (CELL / 2)) + 1
        for k in range(1, n + 1):
            i, j = self.cell(x0 + (p[0] - x0) * k / n, z0 + (p[2] - z0) * k / n)
            ny = self.step(i, j, y, allowed)
            y = y if ny is None else ny
            if self.hit(i, j, y) - allowed:
                return False
        return True

    def off(self, s, p):
        """Distance in the plan from the place p to the middle of the cell of state s."""
        return math.hypot((s[0] + 0.5) * CELL - p[0], (s[1] + 0.5) * CELL - p[2])

    def at(self, s):
        return ((s[0] + 0.5) * CELL, float(s[2]), (s[1] + 0.5) * CELL)


def _inverse(m):
    """Inverse of a 3 x 3 given row-major (a placement's rotation: world = position + m . v)."""
    a, b, c, d, e, f, g, h, i = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
            [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
            [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]


# ------------------------------------------------------------------ the navigation mesh
class Mesh:
    """Polygons (vertices x, y, z), the neighbour across each edge, connected parts. Edge k of a polygon runs
    from its vertex k to vertex k + 1 (kl_fa_bots.Nav.selftest: 100 % with that reading)."""

    def __init__(self, block, game='dd'):
        if game == 'dm':
            block = kl_pf4.convert(block)
        _n, A = kl_pf4.split(block, True)
        P = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        E = [struct.unpack('<iII', r) for r in A[9]]
        V = [struct.unpack('<5f', r) for r in A[6]]
        self.links = len(A[7])
        # a link (array 7: a drop, a ladder) leads ONE WAY from a waypoint to a waypoint of another polygon:
        # drops[polygon] = [(target polygon, from, to, kind)] (read as kl_fa_bots.Nav does)
        self.drops = collections.defaultdict(list)
        W = [struct.unpack('<3fIIIHH', r) for r in A[5]]
        first = [struct.unpack_from('<I', r, 20)[0] for r in A[4]]      # an area's first waypoint
        for w in W:
            for li in range(w[3], w[4]):
                _cost, _junk, num, area, kind, _head, _switch = struct.unpack('<hHiiBBH', A[7][li])
                t = W[first[area] + num]
                self.drops[w[5]].append((t[5], (w[0], w[2], w[1]), (t[0], t[2], t[1]), kind))
        self.pv, self.en = [], []
        for p in P:
            es = range(p[5], p[5] + p[0])
            self.pv.append([(V[E[e][1]][0], V[E[e][1]][2], V[E[e][1]][1]) for e in es])
            nb = [-2 - E[e][0] if E[e][0] < -1 else E[e][0] for e in es]
            self.en.append([j if 0 <= j < len(P) else -1 for j in nb])
        n = len(self.pv)
        self.ok = [len(vs) >= 3 for vs in self.pv]
        self.mid = [tuple(sum(v[a] for v in vs) / len(vs) for a in range(3)) if vs else (0.0, 0.0, 0.0) for vs in self.pv]
        self.part, k = [-1] * n, 0
        nb = [set() for _ in range(n)]
        for i in range(n):
            for j in self.en[i]:
                if j >= 0 and j != i:
                    nb[i].add(j); nb[j].add(i)
        for s in range(n):
            if self.part[s] < 0:
                self.part[s], st = k, [s]
                while st:
                    for j in nb[st.pop()]:
                        if self.part[j] < 0:
                            self.part[j] = k; st.append(j)
                k += 1
        self.size = collections.Counter(self.part)
        self.near = collections.defaultdict(list)       # 400-unit square -> polygons whose box touches it
        for i, vs in enumerate(self.pv):
            if self.ok[i]:
                for bx in range(int(min(v[0] for v in vs) // 400), int(max(v[0] for v in vs) // 400) + 1):
                    for bz in range(int(min(v[2] for v in vs) // 400), int(max(v[2] for v in vs) // 400) + 1):
                        self.near[bx, bz].append(i)
        self._plane = {}

    def inside(self, i, x, z):
        vs, sign = self.pv[i], 0
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            c = (b[0] - a[0]) * (z - a[2]) - (b[2] - a[2]) * (x - a[0])
            if abs(c) < 1e-6:
                continue
            if sign and (c > 0) != (sign > 0):
                return False
            sign = c
        return True

    def height(self, i, x, z):
        """Height of polygon i at (x, z): the least-squares plane through its vertices (a polygon is not
        always flat: a ramp and its landing in one)."""
        pl = self._plane.get(i)
        if pl is None:
            vs, (cx, cy, cz) = self.pv[i], self.mid[i]
            sxx = sum((v[0] - cx) ** 2 for v in vs); szz = sum((v[2] - cz) ** 2 for v in vs); sxz = sum((v[0] - cx) * (v[2] - cz) for v in vs)
            sxy = sum((v[0] - cx) * (v[1] - cy) for v in vs); szy = sum((v[2] - cz) * (v[1] - cy) for v in vs)
            d = sxx * szz - sxz * sxz
            pl = self._plane[i] = (0.0, 0.0) if abs(d) < 1e-6 else ((sxy * szz - szy * sxz) / d, (szy * sxx - sxy * sxz) / d)
        return self.mid[i][1] + pl[0] * (x - self.mid[i][0]) + pl[1] * (z - self.mid[i][2])

    def at(self, x, y, z, dy=MESH_DY):
        """(polygon, its height there) under the place, the one nearest in height and within dy; else None."""
        best = None
        for i in self.near.get((int(x // 400), int(z // 400)), ()):
            if self.inside(i, x, z):
                h = self.height(i, x, z)
                if abs(h - y) <= dy and (best is None or abs(h - y) < abs(best[1] - y)):
                    best = (i, h)
        return best

    def on(self, x, y, z):
        """at(), for a place somebody chose: one that lies ON an edge of the mesh (the bank's rope ends: 0.5
        outside) is on its polygon too -> (polygon, height) or None."""
        hit = self.at(x, y, z)
        if hit is None:
            d, i = self.nearest(x, y, z, MESH_DY)
            if i is not None and d <= 5.0:
                hit = (i, self.height(i, x, z))
        return hit

    def nearest(self, x, y, z, dy=300.0, part=None):
        """(distance in the plan, polygon) of the nearest polygon (of `part`, when given) whose middle is
        within dy of y; (1e30, None) when there is none."""
        best = (1e30, None)
        for i, vs in enumerate(self.pv):
            if not self.ok[i] or abs(self.mid[i][1] - y) > dy or (part is not None and self.part[i] != part):
                continue
            d = 0.0 if self.inside(i, x, z) else 1e30
            for k in range(len(vs)):
                if d == 0.0:
                    break
                ax, az, bx, bz = vs[k][0], vs[k][2], vs[(k + 1) % len(vs)][0], vs[(k + 1) % len(vs)][2]
                ex, ez = bx - ax, bz - az
                L = ex * ex + ez * ez
                t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * ex + (z - az) * ez) / L))
                d = min(d, math.hypot(x - ax - t * ex, z - az - t * ez))
            if d < best[0]:
                best = (d, i)
        return best

    def portal(self, i, j):
        """(width, middle) of the widest edge polygon i shares with j."""
        vs, best = self.pv[i], None
        for k, b in enumerate(self.en[i]):
            if b == j:
                a, c = vs[k], vs[(k + 1) % len(vs)]
                w = math.dist(a, c)
                if best is None or w > best[0]:
                    best = (w, tuple((a[t] + c[t]) / 2 for t in range(3)))
        return best

    def way(self, ia, ib, least=PORTAL, links=False):
        """The line an AI is given from polygon ia to ib: the polygons' middles joined through the middles of
        the shared edges, none narrower than `least` (the park second agent's sk_walk.route); with `links`
        also down the mesh's links, from their waypoint to the target's.
        -> ([points], the narrowest shared edge on it, [(from, to, kind)] of the links taken) or None."""
        dist, prev = {ia: 0.0}, {}
        pq = [(0.0, ia, self.mid[ia])]
        while pq:
            d, i, at = heapq.heappop(pq)
            if i == ib:
                break
            if d > dist.get(i, 1e18):
                continue
            for j in self.en[i]:
                if j < 0:
                    continue
                e = self.portal(i, j)
                if e[0] < least:
                    continue
                nd = d + math.dist(at, e[1])
                if nd < dist.get(j, 1e18):
                    dist[j], prev[j] = nd, (i, e, None)
                    heapq.heappush(pq, (nd, j, e[1]))
            for j, pa, pb, kind in self.drops.get(i, ()) if links else ():
                nd = d + math.dist(at, pa) + math.dist(pa, pb)
                if nd < dist.get(j, 1e18):
                    dist[j], prev[j] = nd, (i, None, (pa, pb, kind))
                    heapq.heappush(pq, (nd, j, pb))
        if ib not in dist:
            return None
        out, i, narrow, taken = [self.mid[ib]], ib, 1e30, []
        while i != ia:
            i, e, link = prev[i]
            if link:
                out += [link[1], link[0]]
                taken.append(link)
            else:
                out.append(e[1])
                narrow = min(narrow, e[0])
        out.append(self.mid[ia])
        return out[::-1], narrow, taken[::-1]


# ------------------------------------------------------------------ the search
def _search(g, starts, goal, target, opened, cross):
    """Cheapest way over the grid from any of the states `starts`: a step costs its length in units, a cell an
    object stands in CROSS per object (and is entered only where cross(state) allows it; cross None = never).
    goal: a set of states - the search ends at the first one it comes to (target: the place, for the estimate
    that steers it); None = go everywhere. -> (cost {state: ...}, previous {state: state}, the goal state come
    to or None, {REF: distance to the target of the nearest cell it shut the search out of})."""
    tx, tz = (target[0], target[2]) if target else (0.0, 0.0)
    slack = max(g.off(s, target) for s in goal) + CELL if goal else 0.0     # the estimate never says more than is left to walk
    est = (lambda s: max(0.0, math.hypot((s[0] + 0.5) * CELL - tx, (s[1] + 0.5) * CELL - tz) - slack)) if goal else (lambda s: 0.0)
    cost, prev, edge = {s: 0.0 for s in starts}, {}, {}
    pq = [(est(s), 0.0, s) for s in starts]
    heapq.heapify(pq)
    step, hit = g.step, g.hit
    while pq:
        _f, d, s = heapq.heappop(pq)
        if d > cost[s]:
            continue
        if goal and s in goal:
            return cost, prev, s, edge
        i, j, y = s
        for di, dj, w in ((1, 0, CELL), (-1, 0, CELL), (0, 1, CELL), (0, -1, CELL),
                          (1, 1, CELL * 1.414), (1, -1, CELL * 1.414), (-1, 1, CELL * 1.414), (-1, -1, CELL * 1.414)):
            ny = step(i + di, j + dj, y, opened)
            if ny is None:
                continue
            n = (i + di, j + dj, ny)
            h = hit(i + di, j + dj, ny)
            if h and opened:
                h = h - opened
            nd = d + w
            if h:
                if cross is None or not cross(n):
                    q = math.hypot((n[0] + 0.5) * CELL - tx, (n[1] + 0.5) * CELL - tz)
                    for r in h:
                        if q < edge.get(r, 1e30):
                            edge[r] = q
                    continue
                nd += CROSS * len(h)
            if nd < cost.get(n, 1e30):
                cost[n], prev[n] = nd, s
                heapq.heappush(pq, (nd + est(n), nd, n))
    return cost, prev, None, edge


def _crossed(g, prev, end, opened):
    """The way to state `end` as states, and what it crosses: [{'refs', 'cells', 'at', 'dist'}] in the order
    met - one entry per unbroken run of cells that objects stand in."""
    way = [end]
    while way[-1] in prev:
        way.append(prev[way[-1]])
    way.reverse()
    out, run, length = [], None, 0.0
    for k, s in enumerate(way):
        if k:
            length += CELL * (1.414 if s[0] != way[k - 1][0] and s[1] != way[k - 1][1] else 1.0)
        h = g.hit(*s) - opened
        if h:
            if run is None:                             # (a thing crossed a second time - the bank's round vault door - is one entry)
                run = next((c for c in out if h <= set(c['refs'])), None)
            if run is None:
                run = {'refs': [], 'cells': 0, 'at': tuple(round(v) for v in g.at(s)), 'dist': round(length / 100, 1)}
                out.append(run)
            run['cells'] += 1
            run['refs'] += [r for r in sorted(h) if r not in run['refs']]
        else:
            run = None
    return way, length, out


def _mesh_cross(g, mesh):
    """cross() for _search: a cell may be crossed where a mesh polygon lies under its middle."""
    memo = {}
    def cross(s):
        v = memo.get(s)
        if v is None:
            v = memo[s] = mesh.at((s[0] + 0.5) * CELL, s[2], (s[1] + 0.5) * CELL) is not None
        return v
    return cross


class _Run:
    """What every question needs: the level, its grid, the opened REF ids, where a crossing may be."""

    def __init__(self, src, opened=(), who='all', rigid=False, hidden=True, down=DOWN, mesh=True):
        self.lv = load(src)
        self.g = self.lv.grid(who, rigid, down)
        self.named = self.lv.refs(list(opened) if not isinstance(opened, (str, int)) else [opened])
        self.opened = frozenset(self.named | (set() if hidden else self.lv.hidden))
        self.mesh = self.lv.mesh() if mesh else None
        self.cross = _mesh_cross(self.g, self.mesh) if self.mesh else (lambda s: True)

    def describe(self, r):
        lv = self.lv
        e = lv.ent.get(r)
        fl = set().union(*[set(o[2]) for o in lv.owns.get(r, ())] or [set()])
        return {'ref': r, 'name': lv.name(r), 'path': lv.path[e] if e is not None else '', 'kind': lv.kind(r), 'hidden': r in lv.hidden,
                'reading': _reading(fl)}

    def leg(self, a, b, opened=None, cross=True):
        """One leg a -> b: {'free', 'length' (m), 'floor' (lowest, highest), 'crossed', 'edge', 'way', 'note'}."""
        g, opened = self.g, self.opened if opened is None else opened
        out = {'from': tuple(a), 'to': tuple(b), 'free': False, 'length': None, 'crossed': [], 'edge': [], 'note': '', 'off': []}
        sa, sb = g.feet(a, opened), g.feet(b, opened)
        if not sa or not sb:
            out['note'] = 'no floor within %d of %s' % (NEAR_Y, ' and '.join('(%d, %d, %d)' % tuple(p) for p, s in ((a, sa), (b, sb)) if not s))
            return out
        cost, prev, end, edge = _search(g, sa, set(sb), b, opened, self.cross if cross else None)
        if end is None:
            out['edge'] = [dict(self.describe(r), dist=round(q / 100, 1)) for r, q in sorted(edge.items(), key=lambda x: x[1])]
            out['reached'] = len(cost)
            return out
        way, length, crossed = _crossed(g, prev, end, opened)
        ys = [s[2] for s in way]
        # a place that stands in something is walked from / to the nearest free floor: say how far that is
        out['off'] = [(tuple(p), round(g.off(s, p))) for p, s in ((a, way[0]), (b, way[-1])) if g.off(s, p) > NEAR]
        out.update(free=not crossed, length=round(length / 100, 1), floor=(min(ys), max(ys)), way=way,
                   crossed=[dict(c, objects=[self.describe(r) for r in c['refs']]) for c in crossed])
        return out


def _reading(flags):
    """The sub-part flags of an object read by the name census (docstring 'flags'): what it stops, as text."""
    if not flags:
        return ''
    al = 0
    for f in flags:
        al |= f
    who = ['characters'] if al & 0x20 else ['heroes only'] if al & 0x8 else []
    return 'stops ' + (', '.join(who + [nm for bit, nm in BITS if al & bit]) or 'nothing known')


def route(src, pts, opened=(), **opt):
    """Is there a walkable way through the points, in their order -> {'free', 'length' (m), 'legs': [leg]}; a
    leg that is not free carries what its thinnest crossing goes through ('crossed', in the order met) or, when
    there is no way even through objects, what bounds the reached area ('edge', nearest to the goal first)."""
    run = _Run(src, opened, **opt)
    legs = [run.leg(a, b) for a, b in zip(pts, pts[1:])]
    return {'free': all(l['free'] for l in legs), 'length': sum(l['length'] or 0 for l in legs), 'legs': legs}


def blockers(src, pts, opened=(), **opt):
    """What stands in the way, nearest first: route() again and again, each time with the objects just crossed
    taken out, until the way is free -> ([{'ref', 'name', 'kind', 'leg', 'at', 'dist', ...}], free at the end)."""
    run = _Run(src, opened, **opt)
    out, gone = [], set(run.opened)
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        for _round in range(ROUNDS):
            leg = run.leg(a, b, frozenset(gone))
            if leg['free'] or not leg['crossed']:
                break
            for c in leg['crossed']:
                for o in c['objects']:
                    if o['ref'] not in gone:            # one object can be crossed at two places of one way
                        out.append(dict(o, leg=k, at=c['at'], dist=c['dist'], cells=c['cells']))
                gone.update(c['refs'])
        if not leg['free']:
            return out, False
    return out, True


def stations(src, pts, opened=(), near=NEAR, **opt):
    """Each place: is it on the navigation mesh and on which part, and is it reached from the FIRST place in
    the collision: does the walk come to a free floor within `near` of it (86; a money container is taken from
    125: kl_escape.REACH). -> [{'at', 'mesh' (None / True / False), 'part', 'part_size', 'off' (distance to the
    mesh when off it), 'floor', 'reached', 'gap' (how near the walk comes, looked for up to GAP), 'length' (m),
    'in' (what the place itself stands in), 'behind' (what the thinnest crossing to it goes through)}]."""
    run = _Run(src, opened, **opt)
    g, mesh, out = run.g, run.mesh, []
    start = g.feet(pts[0], run.opened)
    cost, prev = ({}, {})
    if start:
        cost, prev, _end, _edge = _search(g, start, None, None, run.opened, run.cross)
    home = None
    for p in pts:
        row = {'at': tuple(p), 'mesh': None, 'part': None, 'part_size': 0, 'off': None, 'floor': None, 'reached': False, 'gap': None, 'length': None,
               'behind': [], 'in': []}
        if mesh:
            hit = mesh.on(*p)
            if hit is None:
                d, i = mesh.nearest(*p, part=home)
                row.update(mesh=False, off=None if i is None else round(d), part=None if i is None else mesh.part[i])
            else:
                row.update(mesh=True, part=mesh.part[hit[0]])
                home = row['part'] if home is None else home
            row['part_size'] = mesh.size.get(row['part'], 0)
        off = lambda s: g.off(s, p)
        st = g.stand(p, run.opened, max(near, GAP))
        if st:
            own = g.cell(p[0], p[2])                                    # what the place itself stands in, if anything
            inside = set().union(*[g.hit(*s) for s in st if s[:2] == own] or [()]) - run.opened
            row['in'] = [run.describe(r) for r in sorted(inside)]
            # the free floors the walk came to; one that is not beside the place counts only when nothing
            # stands between the two but what the place itself stands in (not through a wall or bars)
            free = [s for s in st if cost.get(s, CROSS) < CROSS and (off(s) <= 1.5 * CELL or g.between(s, p, run.opened | inside))]
            thru = [s for s in st if s in cost and off(s) <= near]
            s = min(free, key=off) if free else min(thru, key=lambda s: cost[s]) if thru else st[0]
            row['floor'] = s[2]
            if free:
                row.update(gap=round(off(s)), reached=off(s) <= near or s[:2] == g.cell(p[0], p[2]), length=round(cost[s] / 100, 1))
            if thru and not row['reached']:
                _way, _length, crossed = _crossed(g, prev, min(thru, key=lambda s: cost[s]), run.opened)
                row['behind'] = [dict(c, objects=[run.describe(r) for r in c['refs']]) for c in crossed]
        out.append(row)
    return out


def _door(lv, r):
    """What an object belongs to as ONE door, for counting sets: its parent's path and its own name less a
    trailing number and LEFT / RIGHT - the two leaves of a glass door, the four slide leaves of one room.
    (A naming rule, nothing more: two doors of one name under one parent count as one set.)"""
    e = lv.ent.get(r)
    if e is None:
        return 'REF %d' % r
    stem = re.sub(r'_?(LEFT|RIGHT|Left|Right)$', '', re.sub(r'(_?\d+)+$', '', e.name.decode('latin1')))
    return lv.path[e][:len(lv.path[e]) - len(e.name)] + (stem or e.name.decode('latin1'))


def doors(src, pts, opened=(), **opt):
    """The closures on the way through the points, in the order met (a closure = what the thinnest crossing
    goes through at one place), found by taking out what was crossed and asking again until the way is free;
    then each one alone is put back: NECESSARY when the way is shut with it in its place and all the others
    out. -> {'closures': [{'refs', 'objects', 'leg', 'at', 'dist', 'necessary', 'set'}], 'sets': {name:
    [closure numbers]}, 'free': free with all of them out}."""
    run = _Run(src, opened, **opt)
    lv, legs = run.lv, list(zip(pts, pts[1:]))
    out, gone, free = [], set(run.opened), True
    for k, (a, b) in enumerate(legs):
        for _round in range(ROUNDS):
            leg = run.leg(a, b, frozenset(gone))
            if leg['free'] or not leg['crossed']:
                break
            for c in leg['crossed']:
                new = [r for r in c['refs'] if r not in gone]
                if new:                                 # (the bank's vault door is crossed twice by one way: one closure)
                    out.append({'refs': new, 'objects': [o for o in c['objects'] if o['ref'] in new], 'leg': k, 'at': c['at'], 'dist': c['dist'],
                                'cells': c['cells']})
                gone.update(new)
        free &= leg['free']
    sets = collections.OrderedDict()
    for n, c in enumerate(out):
        c['set'] = ' + '.join(sorted({_door(lv, r) for r in c['refs']}))
        sets.setdefault(c['set'], []).append(n)
        rest = frozenset(gone - set(c['refs']))
        c['necessary'] = not all(run.leg(a, b, rest, cross=False)['free'] for a, b in legs)
    return {'closures': out, 'sets': sets, 'free': free}


def mesh_way(src, pts, opened=(), **opt):
    """The way an AI is given through the points (Mesh.way), sampled every LINE units against the collision.
    -> None without a mesh, else per leg {'from', 'to', 'parts' (of the two ends), 'portal' (the narrowest
    shared edge on it), 'links' (taken: [(from, to, kind)]), 'length' (m), 'samples', 'nofloor': [(x, y, z)],
    'hit': [(object, samples, first place)], 'blockers': [(path, state, samples, first place)] - path blockers
    in state eBlocking whose box holds a sample - 'off': [(place, how far off the mesh)], 'note'}."""
    run = _Run(src, opened, **opt)
    g, mesh = run.g, run.mesh
    if not mesh:
        return None
    pbs = [b for b in run.lv.path_blockers() or () if b[5] == 'eBlocking']
    out = []
    for a, b in zip(pts, pts[1:]):
        row = {'from': tuple(a), 'to': tuple(b), 'parts': None, 'portal': None, 'links': [], 'length': None, 'samples': 0, 'nofloor': [], 'hit': [],
               'blockers': [], 'note': '', 'off': []}
        out.append(row)
        ends = []
        for p in (a, b):                                # a place off the mesh: the nearest polygon within GAP, as for the walk
            h = mesh.on(*p)
            if h is None:
                d, i = mesh.nearest(*p)
                if i is not None and d <= GAP:
                    h = (i, mesh.mid[i][1])
                    row['off'].append((tuple(p), round(d)))
            ends.append(h)
        ha, hb = ends
        if ha is None or hb is None:
            row['note'] = 'more than %d off the mesh: %s' % (GAP, ' and '.join('(%d, %d, %d)' % tuple(p) for p, h in ((a, ha), (b, hb)) if h is None))
            continue
        row['parts'] = (mesh.part[ha[0]], mesh.part[hb[0]])
        # a doorway's shared edge can be narrower than a person (the mesh is drawn in from the walls); a link
        # (a drop) is taken only when there is no way without one
        for least, links in ((PORTAL, False), (PORTAL / 2, False), (0.0, False), (0.0, True)):
            got = mesh.way(ha[0], hb[0], least, links)
            if got is not None:
                break
        if got is None:
            row['note'] = 'no way over the mesh, its links taken too (part %d and part %d)' % row['parts']
            continue
        line, row['portal'], row['links'] = got[0], None if got[1] > 1e29 else round(got[1]), got[2]
        row['length'] = round(sum(math.dist(p, q) for p, q in zip(line, line[1:])) / 100, 1)
        hit, first, pb = collections.Counter(), {}, collections.OrderedDict()
        jumps = {(l[0], l[1]) for l in got[2]}
        for p, q in zip(line, line[1:]):
            if (p, q) in jumps:                         # through the air: nothing to sample
                continue
            L = math.dist(p, q)
            for s in range(int(L // LINE) + 1):
                t = s * LINE / L if L else 0.0
                x, y, z = (p[i] + t * (q[i] - p[i]) for i in range(3))
                row['samples'] += 1
                for path, R, T, half, _msg, _state in pbs:
                    d = (x - T[0], y - T[1], z - T[2])
                    loc = [sum(R[i][j] * d[i] for i in range(3)) for j in range(3)]
                    if all(abs(loc[j]) <= half[j] + PB_DY * abs(R[1][j]) for j in range(3)):     # PB_DY up and down in the WORLD, however the box is turned
                        pb.setdefault(path, [0, (round(x), round(y), round(z))])[0] += 1
                ci, cj = g.cell(x, z)
                best = None
                for i, j in [(ci, cj)] + [(ci + di, cj + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]:
                    for fy, r in g.floors(i, j):
                        if r not in run.opened and abs(fy - y) <= LINE_FLOOR and (best is None or abs(fy - y) < abs(best[2] - y)):
                            best = (i, j, fy)
                    if best is not None:
                        break                           # the sample's own cell first, a cell beside it only without one
                if best is None:
                    row['nofloor'].append((round(x), round(y), round(z)))
                    continue
                for r in g.hit(best[0], best[1], int(round(best[2]))) - run.opened:
                    hit[r] += 1
                    first.setdefault(r, (round(x), round(best[2]), round(z)))
        row['hit'] = [(run.describe(r), n, first[r]) for r, n in hit.most_common()]
        row['blockers'] = [(path, 'eBlocking', n, at) for path, (n, at) in pb.items()]
    return out


# ------------------------------------------------------------------ the command line
def _point(s):
    """'x,y,z' or 'name=x,y,z' -> (name or None, (x, y, z))."""
    name, _eq, xyz = s.rpartition('=')
    v = tuple(float(x) for x in xyz.split(','))
    if len(v) != 3:
        raise ValueError('a place is x,y,z: %r' % s)
    return name or None, v


def _is_point(s):
    return re.fullmatch(r'(.*=)?\s*-?[\d.]+\s*,\s*-?[\d.]+\s*,\s*-?[\d.]+\s*', s) is not None


def _xyz(p):
    return '(%d, %d, %d)' % tuple(round(v) for v in p)


def _obj(o):
    return 'REF %-6d %s  [%s%s%s]' % (o['ref'], o['name'], o['kind'], '; ' + o['reading'] if o['reading'] else '', '; HIDDEN at load' if o['hidden'] else '')


def head(src, opened=(), log=print, **opt):
    """The lines every command starts with: what was read and what counts."""
    run = _Run(src, opened, **opt)
    lv, g = run.lv, run.g
    log('%s (%s form): %d entities, %d REF ids hidden at load; collision counted: %s; left out: %s' % (
        lv.label, 'Dog Days' if lv.scene.game == 'dd' else 'Dead Men', len(lv.ents), len(lv.hidden),
        ', '.join('%d %s' % (n, TYPE[t]) for t, n in sorted(g.counted.items())) or 'nothing',
        ', '.join('%d %s' % (n, TYPE.get(t, 'by their flags')) for t, n in sorted(g.left.items(), key=str)) or 'nothing'))
    hid = [r for r in lv.hidden if any(t in g.counted for t, _c, _f in lv.owns.get(r, ()))]
    log('  %d of the hidden ones own counted collision: %s' % (len(hid), 'left out (--hidden-out)' if lv.hidden <= run.opened and hid else
                                                              'it COUNTS (whether a hidden body collides is not known)' if hid else '-'))
    if run.mesh:
        m = run.mesh
        log('  navigation mesh: %d polygons in %d parts by their edges (largest %s), %d links' % (
            len(m.pv), len(m.size), ', '.join(str(n) for _p, n in m.size.most_common(4)), m.links))
    elif opt.get('mesh', True):
        log('  navigation mesh: NOT read (%s) - a crossing is taken anywhere, an object named may be a wall' % getattr(lv, 'mesh_error', '?'))
    mv = lv.moved()
    if mv:
        log('  MOVED: %d placement(s) do not stand where their entity does - the test uses the .HVK\'s place, which one the game uses is not known:' % len(mv))
        for r, d in sorted(mv, key=lambda x: -x[1])[:8]:
            log('     REF %-6d %s: %d units apart' % (r, lv.name(r), d))
    if run.named:
        own = [r for r in run.named if lv.owns.get(r)]
        log('  taken out (--open): %d REF ids, %d of them own collision: %s' % (len(run.named), len(own), ', '.join(lv.name(r, 1) for r in sorted(own)[:10]) + (' ...' if len(own) > 10 else '')))
    return run


def _say_crossed(crossed, log, pad='     '):
    for c in crossed:
        for o in c['objects']:
            log('%s%s  %d cell(s) at %s, %.0f m on' % (pad, _obj(o), c['cells'], _xyz(c['at']), c['dist']))


def report_walk(src, pts, opened=(), log=print, names=None, **opt):
    """`walk`: -> True when every leg is free."""
    head(src, opened, log, **opt)
    names = names or [None] * len(pts)
    lab = lambda k: ('%s ' % names[k] if names[k] else '') + _xyz(pts[k])
    res = route(src, pts, opened, **opt)
    for k, l in enumerate(res['legs']):
        if l['free']:
            log('  %s -> %s: FREE, %.0f m of cells, floor y %d..%d' % (lab(k), lab(k + 1), l['length'], l['floor'][0], l['floor'][1]))
        elif l['crossed']:
            log('  %s -> %s: BLOCKED - the thinnest crossing (%.0f m) goes through:' % (lab(k), lab(k + 1), l['length']))
            _say_crossed(l['crossed'], log)
        else:
            log('  %s -> %s: NO WAY%s' % (lab(k), lab(k + 1), ' - ' + l['note'] if l['note'] else
                                        ' even through objects (%d floors reached): the floors do not join - a climb, a drop of more than %d or a gap; '
                                        'what bounds the reached area, nearest to the goal first:' % (l.get('reached', 0), opt.get('down', DOWN))))
            for o in l['edge'][:8]:
                log('     %s  %.0f m from the goal' % (_obj(o), o['dist']))
        for p, d in l['off']:
            log('     (%s is not free ground itself: walked %s the nearest ground, %d from it)' % (_xyz(p), 'from' if p == l['from'] else 'to', d))
    free = res['free']
    if not free:
        objs, after = blockers(src, pts, opened, **opt)
        log('  in the way, nearest first (taking out what is crossed and asking again): %d object(s)' % len(objs))
        for o in objs:
            log('     leg %d  %s  at %s, %.0f m on' % (o['leg'] + 1, _obj(o), _xyz(o['at']), o['dist']))
        log('  with them out: %s' % ('FREE' if after else 'STILL NOT free'))
        if opt.get('hidden', True) and any(o['hidden'] for o in objs):
            log('  without what is hidden at load (--hidden-out): %s' % ('FREE' if route(src, pts, opened, **dict(opt, hidden=False))['free'] else 'not free either'))
    mw = mesh_way(src, pts, opened, **opt) if opt.get('mesh', True) else None
    ai = ''
    if mw is not None:
        log('  the way an AI is given (mesh polygons through the middles of their shared edges, a sample every %d):' % LINE)
        tot = nofloor = column = boxed = nolegs = 0
        for k, r in enumerate(mw):
            for p, d in r['off']:
                log('     (%s is %d off the mesh: the nearest polygon is taken)' % (_xyz(p), d))
            if r['length'] is None:
                log('     %s -> %s: %s' % (lab(k), lab(k + 1), r['note']))
                nolegs += 1
                continue
            n_hit = sum(n for _o, n, _at in r['hit'])
            tot += r['samples']; nofloor += len(r['nofloor']); column += n_hit; boxed += sum(n for _p, _s, n, _at in r['blockers'])
            log('     %s -> %s: part %d%s, %.0f m%s, %d samples; no floor within %d of the mesh at %d; something in the body column at %d' % (
                lab(k), lab(k + 1), r['parts'][0], '' if r['parts'][0] == r['parts'][1] else ' -> part %d' % r['parts'][1], r['length'],
                '' if r['portal'] is None else ', narrowest shared edge %d' % r['portal'], r['samples'],
                LINE_FLOOR, len(r['nofloor']), n_hit))
            for pa, pb, kind in r['links']:
                log('        by a LINK of the mesh (kind %d) from %s to %s: %d across, %d down - one way, not sampled' % (
                    kind, _xyz(pa), _xyz(pb), math.hypot(pb[0] - pa[0], pb[2] - pa[2]), pa[1] - pb[1]))
            for at in r['nofloor'][:4]:
                log('        no floor at %s' % _xyz(at))
            for o, n, at in r['hit'][:8]:
                log('        x%-3d first at %s: %s' % (n, _xyz(at), _obj(o)))
            for path, state, n, at in r['blockers']:
                log('        PATH BLOCKER %s (%s): %d samples in its box, first at %s' % ('\\'.join(path.split('\\')[-3:]), state, n, _xyz(at)))
        bad = nofloor + column + boxed + nolegs
        ai = '; the mesh way: %d samples, %s' % (tot, 'all free' if not bad else ', '.join(s for s in (
            '%d without a floor' % nofloor if nofloor else '', '%d with something in the body column' % column if column else '',
            '%d in the box of a path blocker' % boxed if boxed else '', '%d leg(s) without a mesh way' % nolegs if nolegs else '') if s))
        if load(src).path_blockers() is None:
            log('     (path blockers not read: %s)' % getattr(load(src), '_pb_error', '?'))
    log('RESULT: %s%s' % ('FREE' if free else 'NOT FREE', ai))
    return free


def report_stations(src, pts, opened=(), log=print, names=None, near=NEAR, **opt):
    """`stations`: -> True when every place is reached from the first."""
    run = head(src, opened, log, **opt)
    names = names or [None] * len(pts)
    rows = stations(src, pts, opened, near, **opt)
    log('  from %s%s; a place is reached when the walk comes to a free floor within %d of it:' % ('%s ' % names[0] if names[0] else '', _xyz(pts[0]), near))
    for nm, r in zip(names, rows):
        mesh = ('mesh: -' if r['mesh'] is None else 'on the mesh, part %d (%d polygons)' % (r['part'], r['part_size']) if r['mesh'] else
                'OFF the mesh%s' % ('' if r['off'] is None else ' by %d (part %d, %d polygons)' % (r['off'], r['part'], r['part_size'])))
        walk = ('no floor within %d' % NEAR_Y if r['floor'] is None else
                'REACHED%s, %.0f m' % ('' if r['gap'] <= 1.5 * CELL else ' to within %d' % r['gap'], r['length']) if r['reached'] else
                'NOT reached: the walk comes to within %d of it (%.0f m)' % (r['gap'], r['length']) if r['gap'] is not None else
                'NOT reached%s' % ('' if r['behind'] else ' even through objects'))
        log('  %-28s %-24s floor %-6s %-40s %s' % ((nm or '')[:28], _xyz(r['at']), '-' if r['floor'] is None else r['floor'], mesh, walk))
        if r['in'] and (not r['reached'] or r['gap'] > 1.5 * CELL):
            log('        the place itself stands in: %s' % '; '.join(_obj(o) for o in r['in'][:3]))
        _say_crossed(r['behind'], log, '        behind ')
    n = sum(1 for r in rows if r['reached'])
    off = [nm or _xyz(r['at']) for nm, r in zip(names, rows) if r['mesh'] is False]
    parts = {r['part'] for r in rows if r['mesh']}
    log('  -> %d of %d places reached from the first in the collision%s' % (n, len(rows), '' if n == len(rows) else
        '; NOT: %s' % ', '.join(nm or _xyz(r['at']) for nm, r in zip(names, rows) if not r['reached'])))
    if run.mesh:
        log('  -> %d of %d on the mesh, on %d part(s)%s' % (sum(1 for r in rows if r['mesh']), len(rows), len(parts), '' if not off else '; off it: %s' % ', '.join(off)))
    log('RESULT: %s' % ('ALL REACHED' if n == len(rows) else '%d NOT REACHED' % (len(rows) - n)))
    return n == len(rows)


def report_doors(src, pts, opened=(), log=print, names=None, **opt):
    """`doors`: -> True when the way is free with every closure out."""
    head(src, opened, log, **opt)
    names = names or [None] * len(pts)
    res = doors(src, pts, opened, **opt)
    log('  way: %s' % ' -> '.join(('%s ' % nm if nm else '') + _xyz(p) for nm, p in zip(names, pts)))
    if not res['closures']:
        log('  no closure on it')
    for n, c in enumerate(res['closures']):
        log('  %2d  leg %d, %.0f m on, at %s: %s' % (n + 1, c['leg'] + 1, c['dist'], _xyz(c['at']),
                                                   'NECESSARY' if c['necessary'] else 'not necessary (with the others out there is a way round it)'))
        for o in c['objects']:
            log('        %s' % _obj(o))
    need = sum(1 for c in res['closures'] if c['necessary'])
    log('  -> %d closure(s) in %d set(s); %d necessary; with all of them out the way is %s' % (
        len(res['closures']), len(res['sets']), need, 'FREE' if res['free'] else 'STILL NOT free'))
    for name, ns in res['sets'].items():
        log('     set %-90s closure %s' % (' + '.join('\\'.join(x.split('\\')[-3:]) for x in name.split(' + ')), ', '.join(str(n + 1) for n in ns)))
    log('RESULT: %s' % ('%d closures in %d sets, %d necessary' % (len(res['closures']), len(res['sets']), need) if res['free'] else 'NOT FREE'))
    return res['free']


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('walk', 'stations', 'doors'):
        print(__doc__)
        return 2
    cmd, src, rest = a[0], a[1], a[2:]
    opt, opened, frm, to, via, places, near = {}, [], None, None, [], [], NEAR
    k = 0
    while k < len(rest):
        x = rest[k]
        if x in ('--from', '--to', '--via', '--open', '--who', '--down', '--near'):
            if k + 1 == len(rest):
                raise ValueError('%s needs a value' % x)
            v = rest[k + 1]; k += 1
            if x == '--from':
                frm = _point(v)
            elif x == '--to':
                to = _point(v)
            elif x == '--via':
                via.append(_point(v))
            elif x == '--open':
                opened += [s for s in v.split(',') if s.strip()]
            elif x == '--who':
                opt['who'] = v
            elif x == '--near':
                near = float(v)
            else:
                opt['down'] = float(v)
        elif x == '--hidden-out':
            opt['hidden'] = False
        elif x == '--rigid':
            opt['rigid'] = True
        elif x == '--no-mesh':
            opt['mesh'] = False
        elif _is_point(x):
            places.append(_point(x))
        else:
            print('not understood: %s' % x)
            return 2
        k += 1
    if cmd == 'stations':
        if frm:
            places.insert(0, frm)
        if len(places) < 2:
            print('stations needs two places or more (the first is the start)')
            return 2
        ok = report_stations(src, [p for _n, p in places], opened, names=[n for n, _p in places], near=near, **opt)
    else:
        if not frm or not to:
            print('%s needs --from and --to' % cmd)
            return 2
        pts = [frm] + via + [to]
        ok = (report_walk if cmd == 'walk' else report_doors)(src, [p for _n, p in pts], opened, names=[n for n, _p in pts], **opt)
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError) as ex:       # a place that is not x,y,z, a level that is not there
        print('kl_route: %s: %s' % (type(ex).__name__, ex))
        sys.exit(2)
