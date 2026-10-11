#!/usr/bin/env python3
"""
Where a dead player comes back as a fed: the level's FRAGILE_ALLIANCE_AFTER_DEATH spawn points, judged against the
collision, the navigation mesh and the level's bounds, and a step that puts them right on a FINISHED build
(<slot>_Main.zip + the files beside it). Owner, 2026-10-11, after coming back on Retomoto Tower inside a shut lift
of the tower while the round was in the street: 'okay yeah spawn as a fed but in a lift'.
The rule as read in kl2.exe, the table of the five maps, the design and the live checks: re/fed_points.md.
OFFLINE: nothing here installs anything or starts the game. NOTHING OF THIS HAS RUN IN THE GAME.

    python kl_fa_fedpoints.py report <build folder>              read-only: every AFTER_DEATH point - floor, walk test,
                                                                 mesh part, bounds, who authored it, good / doubtful / bad
    python kl_fa_fedpoints.py plan   <build folder> [options]    what apply would do, nothing written
    python kl_fa_fedpoints.py apply  <build folder> <out folder> [options]
                                                                 the build with its points put right, in a NEW folder
    python kl_fa_fedpoints.py check  <build folder>              the rules of report as a verdict; exit 1 on a FAIL
    python kl_fa_fedpoints.py diff   <build folder> <out folder> what the step changed, member by member; exit 1 if
                                                                 anything but what it means to change differs. Compared:
                                                                 every member by CRC and size, every file beside the
                                                                 archive by sha1, every .prp node's properties and
                                                                 controller values, every .gms entity record (matrix,
                                                                 place, flags, type, model, aux, REF, raw block, group,
                                                                 parent, children, list key and list links). NOT read:
                                                                 the .gms tables outside the entity records (they are
                                                                 regenerated from the records) - a changed .buf FAILS
    python kl_fa_fedpoints.py way    <build folder> <N> [x,y,z]  for a scripted fed: way points on foot from point N
                                                                 (report's order) to the place given, or to the nearest
                                                                 place of the AI heisters, the boarding action and (START
                                                                 half of a map of two) the join box of KLJoin.ini
    options
      --all               move every point, the good ones too (default: the bad and the doubtful ones; on a map of two
                          halves every point is placed anew whatever it was)
      --only-bad          leave the doubtful ones where they are
      --first N           a map of two halves: how many of its points stay in the START half (default 3)
      --low N             a map of two halves: how many of those stand on the floor of the join box instead of the START
                          row's floor (default 3 = all of them, since the owner's 'it spawns at the very top, should
                          be at the elevator at the bottom' of 2026-10-11; 1 = the second form, one draw in three;
                          0 = all on the START row's floor, the first form). The round cannot go on until the human -
                          now police - has walked into the join box
      --lift-near D       ... and those stand within D on foot of the join box's middle, the free cells nearest the box first,
                          POST_FAR from every post of an enemy squad (default 2000: 'at the elevator'; 0 = the cells
                          of that floor farthest from the heisters' places, as before)
      --at box|jump       a map of two halves: what switches the points at the join. 'box' (default) = the trigger box
                          the crew arrives in (the street's own start box); 'jump' = the JumpPoint's own list - the exact
                          moment, but kl_fa_bots_rt.check then FAILs the build (it wants that list to hold the squads'
                          street steps and nothing else)
      --no-reset          a map of two halves: do not put the points back at the round's own once-a-round switch
      --place N=x,y,z     point N (1-based, in the order report prints) goes there, whatever the plan says; the place is
                          still checked, and a place that is not good is refused

HOW THE GAME PICKS THE PLACE (kl2.exe build 0490; re/fed_points.md 1)
  The respawn 0x4b28d0 calls rules slot 199 = 0x518e30(police player, 2, 0), which calls 0x5614f0(type 2):
  of the ZSpawnPoint objects registered with the spawn manager [0x168e9f8] (each enters itself in its constructor
  0x8c06f0) it takes every one whose type [point+0x14] is 2 = eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH and whose
  node [point+4] has bit 0x400 of its flags +0x3c CLEAR (not hidden), and draws ONE AT RANDOM, each with the same
  chance (the engine's generator [0xdd2640]+0xb30). No distance, no sight, no team, no 'used' test: where the dead
  man fell, where the crew or the police are, plays no part. Then 0x518e30 casts one ray down from 10 above the
  point over 200 (collision mask 0x20) and stands the player 2 above what it hits, or at the point's own height
  when it hits nothing, turned as the point's matrix is. With no candidate the body stays where the level put it.
  LEVEL DATA that decides: ZSpawnPoint field 8 (the type), ZGEOM[2] / [1] (place, facing), and hidden at the load
  (ZGEOM[3] = 1 with .gms flag 0x400, the stock pair). LIVE OBJECT: the type dword and the node's hidden bit, which
  is what ZGEOM's Show / Hide (vtable slots 22 / 21 = 0x8703e0 / 0x6edd50 -> 0x440290) clear and set - the calls the
  controllers ActivateGeom / DeactivateGeom make on every object of their list when they are sent 'AITrigger'
  (0x55c9f0 / 0x824950 -> session manager slots 8 / 9 = 0x4c4900 / 0x668160). Both controllers also SAVE and RESTORE
  the shown state of every object they name (slots 21 / 22: 0x899c50, 0x6e8c70 / 0x8d6750).
  So a point is switched off and on by level data alone. No stock level does it to a spawn point (9 FA levels: no
  point hidden, none named by anything): the form is stock, the use on a ZSpawnPoint is new.

WHAT A POINT IS JUDGED BY (report / check)
  floor    a floor of the collision under it within the game's ray (10 above .. 190 below), and no collision 55..165
           above that floor in its cell (he would stand inside something)
  walk     kl_escape.Walk's rules (floors within 45 degrees, steps of 45 up / 60 down, blocked by anything 55..165
           above the floor; convex shapes - crates, cars - are not in it; no door that opens), made a body wide (the
           cells beside a step must be free too) and with every floor of a cell kept apart (a tower has three), from
           the point to THE CREW'S GROUND = everything a man can walk to and back from a place of the crew's: the
           START row (the arrival places in the second half), every place a step of the AI heisters names, the
           boarding action. GOOD: he walks onto it. DOUBTFUL: only by a one-way drop (up to 550: the deepest drop
           link stock Dog Days gives its AI is 523), or only through a gap narrower than a body. BAD: closed in (a
           lift car, a pen), or a deeper drop. The grid is the level AS IT LOADS: what a blast or a script opens
           later (Retomoto's boardroom doors) is shut in it, so 'from it N of M places are reached' may be short.
  mesh     the navigation polygon under it: the crew's part, a part joined to it by a link, another part (BAD by
           the task's rule: the AI heisters cannot path to him), or none (said, not judged)
  bounds   inside a LevelBound box (BAD), one of its warning boxes (DOUBTFUL), a KillBox (BAD), on the escape
           vehicle's road (DOUBTFUL)
  halves   a map of two places joined only by the hook's jump (a KLJoin.ini [Join] whose entry stands on another
           mesh part than the START row: Retomoto Tower): a point of the START half must be SHOWN at the load and
           switched OFF at the join, a point of the jump half HIDDEN at the load and switched ON at the join.

WHAT apply DOES
  one place (M01 M02 M03 M06): every point that is bad or doubtful goes to the cell of the crew's ground nearest to
    where it was (Dead Men's own choice of side is kept), on the crew's mesh part, with a body's room, clear of the
    bounds and the vehicle's road, BOT_FAR from every place a step of the AI heisters names, START_FAR from the START
    row. Only .prp (ZGEOM[1] / [2]) and .gms (the same in the entity's record) change.
  two halves (Retomoto): all its points are placed anew. FIRST of them in the START half: on the START row's floor,
    off the way the AI heisters take (the cells farthest from every place their steps name), not within BLAST_FAR
    of the START row (the boardroom and its blast) - but the last LOW of them (default: all three) on the floor of
    the join box (the floor the tower's way ends on): JOIN_FAR or more from the box itself (a man put down inside
    it would be jumped in the same breath), BOT_FAR from the heisters' places, within LIFT_NEAR on foot of the box and
    POST_FAR from every post of an enemy squad, the nearest to the box first = Retomoto's lift hall, outside every
    lift car (a car's floor is closed in: not the crew's ground). The rest in the jump half, at the places of PLACES (the police
    side of the street: behind the road block where wave 2 starts, behind the SWAT truck where wave 3 stands, and
    two of the west pavement for a build whose heisters take both sides), each moved to the nearest cell that passes
    every test STREET_FAR from every place of the heisters - a place with no such cell within SNAP is left out for
    the next of the list - and HIDDEN at the load. The switch: one free helper box of
    the host level (a DeactivateGeom nobody names, list empty: F07's GeomDeactivator_DriveInVan, the node
    kl_fa_author keeps for this) gets the START half's points in its DeactivateGeom and a second controller, an
    ActivateGeom, with the jump half's - stock has 26 nodes with both on one message (L10's office windows,
    L03's minibus). It is named by the trigger box the crew arrives in (--at box) or by the JumpPoint (--at jump).
    The way back for the next round: the points are added to the lists of the level's own once-a-round pair (an
    ActivateGeom and a DeactivateGeom a timer of the AIMonitor's round-start list names: Retomoto's blast) - the
    START half's are shown again, the jump half's hidden again, whether or not the game restores them itself.
  files beside the archive: copied, but NOT audit.json / audit.txt (kl_maps.audit's verdict names the content id of
    the build it read: beside another archive it is a stale paper) - run `kl_maps.py audit <out folder>` on the output
    where the source had one; apply says so. preflight.* stays (the audit reads it).

NOT ON THE OWNER'S TAB BEFORE IT HAS LOADED: four things of a two-halves output have never happened in any level of
either game - a ZSpawnPoint in a DeactivateGeom / ActivateGeom list, a spawn point hidden at the load, two geom
controllers on this helper box, a third entry in the lobby box's list. Live checks P0, P1, P2 of re/fed_points.md 6
come first. And a build is one chain: this step is applied to the build that is to be installed (the street lanes'
build, not beside it) - two outputs of one source cannot both be on the tab.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import bisect, collections, heapq, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_hvk, kl_escape
import kl_fa_bots as KB
import kl_prpjoin as J

R_ = 'ROOT\\'
DEAD, START = kl_fa.DEAD, kl_fa.START
HIDDEN = 0x400                  # .gms record flag = node flag bit 10: the bit the pick 0x5614f0 tests (0x561557)
RAY_UP, RAY_DOWN = 10.0, 190.0  # kl2 0x518e30: the ray starts 10 above the point (0xb5cde8) and runs 200 down (0xb5ba0c)
PLAYER_BITS = 0x28              # collision flags that stop a player (kl_fa_author.HERO_BITS)
SYM = 45.0                      # steps of at most this both ways: the ground a man walks over and back
DROP_OK = 550.0                 # GUESS: a one-way drop a player survives (stock AI drop links: 44..523)
POINT_UP = 50.0                 # a moved point floats this much above its floor (Dead Men's: 90..97, kl_fa_author's: 1)
BOT_FAR = 600.0                 # GUESS: from every place a step of the AI heisters names
START_FAR = 1500.0              # kl_fa_fed.CREW_FAR: nearer to the START row he would appear among the starting crew
NPC_FAR = 200.0                 # from the place an enemy actor stands at the load
LANE_FAR = 300.0                # from the escape vehicle's road (its nose carries a KillBox)
SEP = 250.0                     # between two points
ROOM = 2                        # cells of 20 of level, free floor round a point: a body's room
EDGE = 50.0                     # from a mesh edge without a neighbour
NEAR_MAX = 9000.0               # 'nearest to where it was': not farther than this (then the plan stops and says so)
TOP_BAND = 200.0                # 'the START row's floor': floors within this of it
BLAST_FAR = 3000.0              # GUESS: the START half of Retomoto - not within this of the START row in the plan
SNAP = 400.0                    # an authored place may move this far to the nearest cell that passes
FIRST = 3                       # two halves: points that stay in the START half
LOW = 3                         # ... of which this many stand on the join box's floor (review S3: from the START row's
                                # floor it is 129 m of stairs to the box, and the round waits for him there).
                                # 3 = ALL OF THEM since 2026-10-11 20:15, the owner after coming back on the top gallery:
                                # 'yes but it spawns at the very top, should be at the elevator at the bottom' (was 1)
LIFT_NEAR = 2000.0              # GUESS: 'at the elevator' = a point of the join box's floor lies within this ON FOOT
                                # (cell by cell over the crew's ground, along x and z) of the floor under the box's
                                # middle, and of the cells that pass the NEAREST to the box are taken (the first
                                # form took the cells FARTHEST from the heisters' places: with three low points two of
                                # them came out 30 and 41 m away at the far end of the floor). 0 = that first form
POST_FAR = 250.0                # GUESS: ... and this far from every POST of an enemy squad on that floor - where a man
                                # of theirs stands at the load and every place a rout of theirs names
                                # (kl_fa_bots_rt.enemy_posts; NPC_FAR only knows the start places): the lift hall's
                                # guards are in the world from the load in a build `kl_map_ai.py spawnfix` has been through
JOIN_FAR = 300.0                # GUESS: a point of the join box's floor is this far outside the box (kljoin.c jumps a
                                # local player whose feet are inside it, whatever he is)
STALE = ('audit.json', 'audit.txt')    # papers that name the content id of the build they were written for
SQUAD = KB.SQUAD
# the jump half's places, by the map of result.json ('M'): (x, z, what). Measured on the build's collision (top views
# in re/fed_points.md 3); GUESS that these are the police side a player wants to come back on.
PLACES = {'M09_A': [(-4250.0, 5950.0, 'behind the road block, west lane (wave 2 starts 4 m south of it)'),
                    (-4550.0, 10950.0, 'behind the SWAT truck (wave 3 stands in front of it)'),
                    (-3350.0, 6350.0, 'behind the road block, at the median (wave 2 starts 6 m south of it)'),
                    (-4800.0, 10250.0, 'the west kerb beside the SWAT truck'),
                    # two more for a build whose heisters take both sides of the street (the lanes of kl_fa_bots_rt:
                    # its west lane runs through the first place and 6 m past the third) - the north-west quarter,
                    # which no lane enters (measured on z_lanes\retomoto_full: 21 m or more from every place of theirs)
                    (-5500.0, 9200.0, 'the west pavement north of the exit line, across both carriageways from the van'),
                    (-5300.0, 8300.0, 'the west pavement level with the place the van waits at')]}
STREET_FAR = 1500.0             # GUESS: an authored place of the jump half is this far from every place a step of the
                                # AI heisters names (BOT_FAR would let him appear 6 m from a hold of theirs)
VAN_NEAR = 6000.0               # no authored place left: within this of the boarding action (where the run ends)
DEFAULTS = {'all': False, 'only_bad': False, 'first': FIRST, 'low': LOW, 'lift_near': LIFT_NEAR, 'at': 'box', 'reset': True, 'place': {}}


def _archive(folder):
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def read_ini(folder):
    out, sec = collections.defaultdict(dict), None
    p = os.path.join(folder, 'KLJoin.ini')
    if os.path.isfile(p):
        for ln in open(p, encoding='latin1'):
            ln = ln.strip()
            if ln.startswith('[') and ln.endswith(']'):
                sec = ln[1:-1].lower()
            elif sec and '=' in ln and not ln.startswith(';'):
                k, v = ln.split('=', 1)
                out[sec][k.strip().lower()] = v.strip()
    return out


def vec(s):
    return tuple(float(x) for x in s.replace(',', ' ').split())


def hdist(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


# ------------------------------------------------------------------ the ground: collision made walkable
class Ground:
    """kl_escape.Walk over one box, read as states (cell, floor): a cell may hold several floors more than a step
    apart, and each is a place of its own (kl_escape.Walk.flood keeps one floor a cell, which loses the lower
    floors of a tower). spread() = the least 'deepest single drop' to every state from a start (Dijkstra)."""

    def __init__(self, hvk, box, skip):
        self.w = kl_escape.Walk(hvk, box, skip=skip)
        self.box = box
        self._info = {}

    def info(self, c):
        """(sorted floor heights, sorted heights of every sample) of a cell, or None."""
        r = self._info.get(c)
        if r is None:
            g = self.w.grid.get(c)
            r = self._info[c] = (sorted(y for y, f, _r in g if f), sorted(y for y, _f, _r in g)) if g else ((), ())
        return r

    def blocked(self, c, y):
        al = self.info(c)[1]
        i = bisect.bisect_right(al, y + self.w.LO)
        return i < len(al) and al[i] < y + self.w.HI

    def sight(self, a, b, step=12.0, slack=8.0, skip=45.0):
        """Is point b seen from point a? The straight line through the walk test's collision samples (every
        triangle of the static and key-framed shapes sampled every 10): no sample within `slack` of the line's height
        in any cell it crosses, the first and last `skip` of it left out. Convex shapes (crates, cars) are not in
        the samples; a pane of glass that has collision stops the line; outside the box nothing is known and the
        line is clear. A reading for 'the same room' and 'who pops into view', not the game's own test."""
        d = math.dist(a, b)
        if d <= 2 * skip:
            return True
        w, n = self.w, int(d / step) + 1
        for i in range(1, n):
            t = i / n
            if t * d < skip or (1.0 - t) * d < skip:
                continue
            x, y, z = (a[j] + (b[j] - a[j]) * t for j in range(3))
            if not (w.x0 <= x < w.x1 and w.z0 <= z < w.z1):
                continue
            al = self.info(w.cell(x, z))[1]
            j = bisect.bisect_left(al, y - slack)
            if j < len(al) and al[j] <= y + slack:
                return False
        return True

    def under(self, p):
        """(cell, the floor the game's ray finds under point p or None, the nearest floor of the cell or None)."""
        c = self.w.cell(p[0], p[2])
        fl = self.info(c)[0]
        hit = [y for y in fl if p[1] - RAY_DOWN <= y <= p[1] + RAY_UP]
        near = min(fl, key=lambda y: abs(y - p[1])) if fl else None
        return c, (max(hit) if hit else None), near

    def spread(self, c0, y0=None, wide=True, limit=None, par=None):
        """{(cell x, cell z, level): (deepest single drop on the best way, floor y)} from floor y0 of cell c0, or
        from every (cell, floor y) of the list c0 when y0 is None.
        level = floor y // 40 (two floors of a cell nearer than that are one place). par: a dict that takes
        {state: the state it was reached from} (way())."""
        w = self.w
        UP, DOWN = w.UP, w.DOWN
        seeds = [(c0, y0)] if y0 is not None else list(c0)
        best = {(c[0], c[1], int(y // 40)): (0.0, y) for c, y in seeds}
        steps = {k: 0 for k in best}                    # among the ways of the least drop the one of the fewest cells
        pq = [(0.0, 0, c[0], c[1], y) for c, y in seeds]
        heapq.heapify(pq)
        while pq:
            d, ns, cx, cz, y = heapq.heappop(pq)
            k0 = (cx, cz, int(y // 40))
            if (best[k0][0], steps[k0]) < (d, ns):
                continue
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cx + dx, cz + dz)
                fl = self.info(n)[0]
                if not fl:
                    continue
                i = bisect.bisect_right(fl, y + UP)
                if not i:
                    continue
                ny = fl[i - 1]
                nd = max(d, y - ny)
                if limit is not None and nd > limit:
                    continue
                key = (n[0], n[1], int(ny // 40))
                old = best.get(key)
                if old is not None and (old[0], steps[key]) <= (nd, ns + 1):
                    continue
                if self.blocked(n, ny) or (y - ny > DOWN and self.blocked(n, y)):      # (a rail at the edge he steps off)
                    continue
                if wide:
                    s1, s2 = ((n[0], n[1] + 1), (n[0], n[1] - 1)) if dx else ((n[0] + 1, n[1]), (n[0] - 1, n[1]))
                    if self.blocked(s1, ny) or self.blocked(s2, ny):
                        continue
                best[key], steps[key] = (nd, ny), ns + 1
                if par is not None:
                    par[key] = k0
                heapq.heappush(pq, (nd, ns + 1, n[0], n[1], ny))
        return best

    def state(self, best, p, dy=120.0, reach=3, drop=None):
        """The state of `best` at place p (a cell within `reach` of p's, its floor within dy of p's height; with
        `drop` only states reached by at most that drop) -> (key, (drop, y)) or None; the least drop wins."""
        c = self.w.cell(p[0], p[2])
        out = None
        for dx in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                for lv in range(int((p[1] - dy) // 40), int((p[1] + dy) // 40) + 1):
                    v = best.get((c[0] + dx, c[1] + dz, lv))
                    if v is not None and abs(v[1] - p[1]) <= dy and (drop is None or v[0] <= drop) and (out is None or v[0] < out[1][0]):
                        out = ((c[0] + dx, c[1] + dz, lv), v)
        return out

    def fence(self, best, names, limit):
        """What bounds the states of `best` reached by at most `limit`: {object name: cells it blocks}."""
        w, out = self.w, collections.Counter()
        for (cx, cz, _lv), (d, y) in best.items():
            if d > limit:
                continue
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                g = w.grid.get((cx + dx, cz + dz))
                for yy, _f, r in g or ():
                    if y + w.LO < yy < y + w.HI:
                        out[names.get(r, '?').split('!')[-1].split('\\')[-1]] += 1
                        break
        return out


class Polys:
    """The mesh's polygons in a hash of 400-unit squares: at() as kl_fa_bots.Nav.at, fast."""

    def __init__(self, nav):
        self.nav, self.h = nav, collections.defaultdict(list)
        for i, b in enumerate(nav.box):
            if nav.ok[i]:
                for gx in range(int(b[0] // 400), int(b[1] // 400) + 1):
                    for gz in range(int(b[2] // 400), int(b[3] // 400) + 1):
                        self.h[gx, gz].append(i)

    def at(self, x, y, z, lo, hi, part=None):
        nav, best = self.nav, None
        for i in self.h.get((int(x // 400), int(z // 400)), ()):
            b = nav.box[i]
            if b[0] <= x <= b[1] and b[2] <= z <= b[3] and (part is None or nav.part[i] == part) and nav.inside(i, x, z):
                h = nav.height(i, x, z)
                if lo <= h <= hi and (best is None or abs(h - y) < abs(best[1] - y)):
                    best = (i, h)
        return best


# ------------------------------------------------------------------ a build read for this step
class Half:
    def __init__(self, name, part, anchor, entry=None):
        self.name, self.part, self.anchor, self.entry = name, part, tuple(anchor), entry
        self.ground = self.sym = self.key = None


class Lv:
    def __init__(self, folder, log=print):
        self.folder, self.log = folder, log
        self.zip = _archive(folder)
        self.slot = os.path.basename(self.zip)[:-len('_Main.zip')]
        B = self.B = KB.Built(folder, self.slot)
        sc = self.sc = B.sc
        self.nav = KB.Nav(B.scene.nav, links=True)       # a drop link joins two parts (the bank's yard wall)
        self.polys = Polys(self.nav)
        self.S = KB.stations(B, self.nav)
        self.home, self.start = self.S['home'], tuple(self.S['start_mid'])
        self.hvk = kl_hvk.Hvk(B['.HVK'] if '.HVK' in B.ext else B['.hvk'])
        self.rname = {}
        for e in B.ents:
            self.rname.setdefault(e.ref, e.name.decode('latin1'))
        self.hidden = {e.ref for e in B.ents if e.flags & HIDDEN}
        self.soft = set()
        for s in self.hvk.shapes:
            fl = 0
            for _su, f, _n in s.sub:
                fl |= f
            if not fl & PLAYER_BITS:
                self.soft.update(kl_hvk.ref(i) for i in s.inst)
        self.map = B.result.get('M') or ''
        self.points, self.bots, self.npcs, self.boxes = [], [], [], []
        warn = set()
        for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
            self.boxes.append(('bound', k))
            warn.update(j for x in v if isinstance(x, list) for s in x if isinstance(s, str) for j in sc.resolve(s))
        self.boxes += [('warn', k) for k in sorted(warn) if sc.cls(k) == 'ZBoxPrimitive']
        self.boxes += [('kill', k) for k, _i, _v in kl_fa.controllers(sc, 'KillBox') if sc.cls(k) == 'ZBoxPrimitive']
        for k in range(1, len(sc.nodes)):
            cls = sc.cls(k)
            if cls == 'ZSpawnPoint':
                v = kl_fa.node_values(sc, k)
                if v[8] == DEAD:
                    self.points.append(k)
            elif cls == 'ZFFActor' and B.values(k).get('ZFFActor[0]') == 'Enemy':
                self.npcs.append(B.at(k))
            elif sc.names[k].startswith('Pos#') and sc.names[sc.top[k]].startswith(SQUAD):
                self.bots.append(B.at(k))
        self.lane = KB.lanes(B)
        self.ini = read_ini(folder)
        self.halves = [Half('map', self.home, self.start)]
        j = self.ini.get('join')
        if j and 'target' in j:
            t = vec(j['target'])
            hit = self.polys.at(t[0], t[1], t[2], t[1] - 300.0, t[1] + 100.0)
            if hit and self.nav.part[hit[0]] != self.home:
                crew = self.ini.get('crewjoin', {})
                arr = [vec(crew['place.%d' % (i + 1)]) for i in range(int(crew.get('places', 0))) if 'place.%d' % (i + 1) in crew]
                self.halves[0].name = 'START half'
                self.halves.append(Half('jump half', self.nav.part[hit[0]], arr[0] if arr else t, entry=t))
                self.arrive = arr
        self.ext = {}
        for h in self.halves:
            ys = [v[1] for i in range(len(self.nav.pv)) if self.nav.ok[i] and self.nav.part[i] == h.part for v in self.nav.pv[i]]
            self.ext[h.name] = (min(ys), max(ys))

    # ---- small things
    def at(self, k):
        return self.B.at(k)

    def hidden_at_load(self, k):
        """(ZGEOM[3], .gms flag 0x400) of a node."""
        return bool(kl_fa.node_values(self.sc, k)[3]), bool(self.B.ents[k - 1].flags & HIDDEN)

    def half_of(self, p):
        if len(self.halves) == 1:
            return self.halves[0]
        def off(h):
            lo, hi = self.ext[h.name]
            return 0.0 if lo - 300.0 <= p[1] <= hi + 700.0 else min(abs(p[1] - lo), abs(p[1] - hi))
        return min(self.halves, key=off)

    def join_rect(self):
        """The join box of KLJoin.ini [Join] -> (x0, x1, z0, z1, y0, y1) or None."""
        j = self.ini.get('join')
        if not j or 'min' not in j or 'max' not in j:
            return None
        a, b = vec(j['min']), vec(j['max'])
        return (min(a[0], b[0]), max(a[0], b[0]), min(a[2], b[2]), max(a[2], b[2]), min(a[1], b[1]), max(a[1], b[1]))

    def in_boxes(self, p):
        """[(kind, node name)] of the bound / warning / kill boxes place p (feet) lies in (its chest is tried too)."""
        out = []
        for kind, k in self.boxes:
            if any(self.B.in_box(k, (p[0], p[1] + dy, p[2])) for dy in (10.0, 100.0)):
                out.append((kind, self.sc.names[k].split('!')[-1]))
        return out

    def who(self, k):
        """Who put the point where it is."""
        n, p = self.sc.names[k], self.at(k)
        fj = os.path.join(self.folder, 'fedpoints.json')
        if os.path.isfile(fj):
            for m in json.load(open(fj)).get('moved', []):
                if m['node'] == self.sc.path[k][5:]:
                    return 'this step (kl_fa_fedpoints)'
        if n.startswith('FASpecials!SpawnPoint!'):
            try:
                import kl_fa_author as au
                if any(math.dist(p, q) < 2.0 for q in au.POLICE):
                    return "the host level F07's object, placed by kl_fa_author (its POLICE table)"
            except Exception:
                pass
            return "the host level F07's object"
        return "the Dead Men map's own Fragile Alliance data"

    # ---- the ground of a half
    def ground(self, h):
        if h.ground is not None:
            return h.ground
        more = [(x, h.anchor[1], z) for x, z, _w in PLACES.get(self.map, [])] if h is not self.halves[0] else []
        pts = [h.anchor] + [self.at(k) for k in self.points if self.half_of(self.at(k)) is h] + [p for p in self.bots if self.half_of(p) is h] + list(more)
        if h is self.halves[0]:
            pts.append(self.start)
        act = self.S['action']
        if act and self.half_of(self.at(act)) is h:
            pts.append(self.at(act))
        px = [v for i in range(len(self.nav.pv)) if self.nav.ok[i] and self.nav.part[i] == h.part for v in self.nav.pv[i]]
        box = (max(min(p[0] for p in pts) - 2500.0, min(v[0] for v in px) - 600.0), min(max(p[0] for p in pts) + 2500.0, max(v[0] for v in px) + 600.0),
               max(min(p[2] for p in pts) - 2500.0, min(v[2] for v in px) - 600.0), min(max(p[2] for p in pts) + 2500.0, max(v[2] for v in px) + 600.0))
        # the cells lie on ONE lattice of the world whatever the box is: a place found does not hang on where the
        # points stood before (the step applied to its own output changes nothing)
        c = kl_escape.Walk.CELL
        box = (math.floor(box[0] / c) * c, math.ceil(box[1] / c) * c, math.floor(box[2] / c) * c, math.ceil(box[3] / c) * c)
        h.ground = G = Ground(self.hvk, box, self.soft | self.hidden)
        # THE CREW'S GROUND: what a man walks to and back from a place of the crew's - the half's anchor, every place a
        # step of the AI heisters names, the boarding action - by steps of at most SYM both ways. (From the anchor
        # alone it would end at the crew's first one-way step: the bank's crew starts on a roof.)
        seeds, lost = [], 0
        for name, t in self.targets(h).items():
            c, fy, near = G.under((t[0], t[1] + 60.0, t[2]))
            if fy is None:
                c, fy, near = G.under((t[0], t[1] + 150.0, t[2]))
            if fy is None:
                if t is h.anchor or t == h.anchor:
                    raise ValueError('%s: no floor under its anchor %s (nearest floor of the cell: %s)' % (h.name, tuple(round(v) for v in h.anchor), near))
                lost += 1
                continue
            seeds.append((c, fy))
        h.sym = G.spread(seeds, wide=True, limit=SYM)
        h.key = (seeds[0][0][0], seeds[0][0][1], int(seeds[0][1] // 40))
        h.seeds, h.lost = len(seeds), lost
        return G

    def targets(self, h):
        """{name: place} of what the crew does in a half: the anchor, every place of the AI heisters' steps, the
        boarding action."""
        t = collections.OrderedDict()
        t['the START row' if h is self.halves[0] else 'the jump entry'] = h.anchor
        for i, p in enumerate(self.bots):
            if self.half_of(p) is h:
                t['bot place %d' % i] = p
        act = self.S['action']
        if act and self.half_of(self.at(act)) is h:
            t['the boarding action'] = self.at(act)
        return t

    # ---- one place judged
    def judge(self, p, cache=None):
        """A place (x, y, z as a spawn point stores it) -> dict: 'verdict' good / doubtful / bad, 'why' [text],
        and the numbers. cache: {} shared between the points of one call (points on one piece of ground are one flood)."""
        cache = {} if cache is None else cache
        h = self.half_of(p)
        G = self.ground(h)
        r = collections.OrderedDict(half=h.name, place=[round(v, 1) for v in p])
        bad, doubt, note = [], [], []
        c, fy, near = G.under(p)
        r['floor'] = None if fy is None else round(fy, 1)
        hit = self.polys.at(p[0], p[1], p[2], p[1] - 400.0, p[1] + 60.0)
        part = hit and self.nav.part[hit[0]]
        r['mesh'] = ('the crew\'s part' if part == h.part else 'part %d of %d polygons' % (part, self.nav.part_size[part])) if hit else 'none'
        if hit and part != h.part:
            bad.append('it stands on mesh part %d (%d polygons), which no polygon or link joins to the crew\'s part %d' % (part, self.nav.part_size[part], h.part))
        elif not hit:
            note.append('no mesh polygon under it')
        box = self.in_boxes((p[0], fy if fy is not None else p[1], p[2]))
        r['boxes'] = ['%s %s' % b for b in box]
        for kind, nm in box:
            (doubt if kind == 'warn' else bad).append('inside the %s box %s' % ({'bound': 'level bound', 'warn': 'bound\'s warning', 'kill': 'kill'}[kind], nm))
        ld = KB.lane_dist(self.lane, p) if self.lane else 1e9
        if ld < LANE_FAR:
            doubt.append('%d from the escape vehicle\'s road' % ld)
        if fy is None:
            bad.append('no floor within the game\'s ray (10 above .. 190 below): the nearest floor of its cell is %s' % (
                'none' if near is None else '%d %s it' % (abs(near - p[1]), 'above' if near > p[1] else 'below')))
            r.update(verdict='bad', why=bad + doubt + note, bad=bad, doubt=doubt, note=note)
            return r
        r['above_floor'] = round(p[1] - fy, 1)
        if G.blocked(c, fy):
            doubt.append('collision 55..165 above its floor in its own cell: he would stand in something')
        key = (c[0], c[1], int(fy // 40))
        res = None
        for k0, v in cache.items():
            if v[0] is h and key in v[1]:
                res = v
                break
        if res is None:
            wide = G.spread(c, fy, wide=True, limit=DROP_OK * 4)
            mine = {k for k, (d, _y) in wide.items() if d <= G.w.DOWN}
            into = 0.0 if key in h.sym else min((d for k, (d, _y) in wide.items() if k in h.sym), default=None)
            thin = None
            if into is None or into > G.w.DOWN:
                t = G.spread(c, fy, wide=False, limit=G.w.DOWN)
                thin = any(k in h.sym for k in t)
            tg = self.targets(h)
            got = {n: G.state(wide, t, drop=DROP_OK) for n, t in tg.items()}
            cover = (sum(1 for s in got.values() if s is not None and s[1][0] <= G.w.DOWN), sum(1 for s in got.values() if s is not None), len(tg),
                     next(iter(got.values())) is not None)
            res = cache[key] = (h, mine, into, thin, len(mine) * 0.04, G.fence(wide, self.rname, G.w.DOWN).most_common(5) if (into is None or into > G.w.DOWN) else [], cover)
        _h, mine, into, thin, area, fence, cover = res
        r.update(into=None if into is None else round(into), area_m2=round(area), fence=['%s x%d' % f for f in fence],
                 reaches=collections.OrderedDict(by_walking=cover[0], with_drops=cover[1], of=cover[2], the_anchor=cover[3]))
        if key in h.sym:
            r['walk'] = 'on the crew\'s ground'
        else:
            if into is not None and into <= G.w.DOWN:
                r['walk'] = 'walks onto the crew\'s ground%s' % (' (a step of %d down on the way: one way)' % into if into > SYM else '')
            elif thin:
                r['walk'] = 'only through a gap narrower than a body'
                doubt.append('the only way to the crew\'s ground is through a gap one cell (20) wide - the %d m2 he stands on are bounded by %s' % (area, ', '.join(f[0] for f in fence[:4])))
            elif into is not None and into <= DROP_OK:
                r['walk'] = 'a one-way drop of %d' % into
                doubt.append('the only way to the crew\'s ground is a drop of %d (%.1f m), one way; the %d m2 he stands on are bounded by %s' % (into, into / 100.0, area, ', '.join(f[0] for f in fence[:4])))
            else:
                r['walk'] = 'closed in' if into is None else 'a drop of %d' % into
                bad.append('%s: %d m2 of floor, bounded by %s' % ('closed in' if into is None else 'the only way out is a drop of %d (%.1f m)' % (into, into / 100.0),
                                                                 area, ', '.join('%s (%d cells)' % f for f in fence[:5]) or 'nothing the walk test sees'))
        if cover[2] > 1 and not cover[1]:
            doubt.append('from it none of the %d places of the crew is reached, drops of up to %d counted' % (cover[2], DROP_OK))
        elif cover[1] < cover[2]:
            note.append('from it %d of the %d places of the crew are reached by walking, %d with drops of up to %d%s' % (
                cover[0], cover[2], cover[1], DROP_OK, '' if cover[3] else '; not the %s (the crew\'s own way from there is one way)' % ('START row' if h is self.halves[0] else 'jump entry')))
        r['from_bots'] = round(min((math.dist(p, q) for q in self.bots), default=1e9))
        r['from_anchor'] = round(hdist(p, h.anchor))
        r.update(verdict='bad' if bad else 'doubtful' if doubt else 'good', why=bad + doubt + note, bad=bad, doubt=doubt, note=note)
        return r

    def survey(self):
        """Every AFTER_DEATH point -> [(node, dict of judge() + name / shown / who)]."""
        cache, out = {}, []
        for k in self.points:
            r = self.judge(self.at(k), cache)
            g3, fl = self.hidden_at_load(k)
            r.update(node=self.sc.path[k][5:], name=self.sc.names[k].split('!')[-1], hidden_at_load=fl, geom3=g3, who=self.who(k))
            out.append((k, r))
        return out


# ------------------------------------------------------------------ the switch of a map of two halves
def ctrl_values(sc, k, name):
    """[(index in the node's list, field values)] of the controllers `name` on node k."""
    from kl_prp import units
    return [(i, [kl_fa.value(sc, u) for u in units(b[1:-1])]) for i, (nm, b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == name]


def namers(sc):
    """{lower-case scene path: [(node, controller name, field)]} of every reference list entry of the level."""
    from kl_prp import units
    out = collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        for nm, b in sc.nodes[k]['ctrls']:
            for fi, u in enumerate(units(b[1:-1])):
                v = kl_fa.value(sc, u)
                if isinstance(v, list):
                    for s in v:
                        if isinstance(s, str):
                            out[s.lower()].append((k, sc.p.key(nm), fi))
    return out


def switches(L):
    """The level's nodes that hide or show an AFTER_DEATH point -> [dict(node, off [points], on [points], by [(node,
    controller)], when)] ; when = 'join' (named by the join entry's JumpPoint, or by a trigger box that holds the
    arrival places / stands at the jump entry), 'round' (named from a timer of the AIMonitor's round-start list),
    else 'other'."""
    sc, pts = L.sc, {L.sc.path[k].lower(): k for k in L.points}
    who = namers(sc)
    round_start = set()
    for k, _i, v in kl_fa.controllers(sc, 'AIMonitor'):
        for x in v:
            for s in x if isinstance(x, list) else ():
                for j in sc.resolve(s) if isinstance(s, str) else ():
                    for name in ('TriggerDelay2', 'TriggerDelay'):
                        for _ci, tv in ctrl_values(sc, j, name):
                            round_start.update(t.lower() for y in tv if isinstance(y, list) for t in y if isinstance(t, str))
    out = []
    for k in range(1, len(sc.nodes)):
        off = [pts[s.lower()] for _i, v in ctrl_values(sc, k, 'DeactivateGeom') for s in (v[1] if isinstance(v[1], list) else []) if s.lower() in pts]
        on = [pts[s.lower()] for _i, v in ctrl_values(sc, k, 'ActivateGeom') for s in (v[1] if isinstance(v[1], list) else []) if s.lower() in pts]
        if not off and not on:
            continue
        by = who.get(sc.path[k].lower(), [])
        when = 'other'
        if sc.path[k].lower() in round_start:
            when = 'round'
        for a, c, _f in by:
            if c == 'JumpPoint' and len(L.halves) > 1 and math.dist(L.at(a), L.halves[1].entry) < 20.0:
                when = 'join'
            elif c == 'TriggerBox' and len(L.halves) > 1 and arrival_box(L, a):
                when = 'join'
        out.append(dict(node=k, off=off, on=on, by=by, when=when))
    return out


def arrival_box(L, k):
    """Is trigger box k the one the crew arrives in: every [CrewJoin] place of KLJoin.ini inside it (the hook puts
    the AI heisters there in the tick of the jump), or - without such places - the jump entry within 600 of it."""
    if L.sc.cls(k) != 'ZBoxPrimitive' or len(L.halves) < 2:
        return False
    arr = getattr(L, 'arrive', [])
    if arr:
        return all(L.B.in_box(k, (a[0], a[1] + 90.0, a[2])) for a in arr)
    q = L.B.local(k, L.halves[1].entry)
    s = L.B.box(k)
    return all(abs(q[i]) <= s[i] + 600.0 for i in range(3))


def join_box(L):
    """The trigger box of arrival_box() a criminal fires (ECPS_FA_MERCONLY / BOTH) -> node or None; the smallest."""
    hit = []
    for k, _i, v in kl_fa.controllers(L.sc, 'TriggerBox'):
        if arrival_box(L, k) and any(x in ('ECPS_FA_MERCONLY', 'ECPS_BOTH', 'ECPS_FA_MERC_UCC') for x in v if isinstance(x, str)):
            s = L.B.box(k)
            hit.append((s[0] * s[1] * s[2], k))
    return min(hit)[1] if hit else None


def free_switch(L):
    """A helper box of the level to carry the switch: one DeactivateGeom controller and nothing else, its list
    empty, no child, named by nothing -> node or None (F07's GeomDeactivator_DriveInVan in a Retomoto build)."""
    sc, who = L.sc, namers(L.sc)
    for k in range(1, len(sc.nodes)):
        cs = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if cs == ['DeactivateGeom'] and sc.end[k] - k == 1 and not who.get(sc.path[k].lower()):
            v = ctrl_values(sc, k, 'DeactivateGeom')[0][1]
            if not v[1] and v[0] == 'AITrigger':
                return k
    return None


def round_pair(L):
    """The level's own once-a-round pair: (ActivateGeom node, DeactivateGeom node) that ONE timer of the AIMonitor's
    round-start list names -> (on node, off node, timer node) or None. Retomoto: the blast timer's GeomActivator_
    ChairPost and GeomDeactivator_ChairsPre (the room's chairs are swapped at the blast, every round)."""
    sc = L.sc
    for k, _i, v in kl_fa.controllers(sc, 'AIMonitor'):
        for x in v:
            for s in x if isinstance(x, list) else ():
                for j in sc.resolve(s) if isinstance(s, str) else ():
                    for name in ('TriggerDelay2', 'TriggerDelay'):
                        for _ci, tv in ctrl_values(sc, j, name):
                            tg = [t for y in tv if isinstance(y, list) for s2 in y if isinstance(s2, str) for t in sc.resolve(s2)]
                            on = [t for t in tg if [sc.p.key(nm) for nm, _b in sc.nodes[t]['ctrls']] == ['ActivateGeom']]
                            off = [t for t in tg if [sc.p.key(nm) for nm, _b in sc.nodes[t]['ctrls']] == ['DeactivateGeom']]
                            if on and off:
                                return on[0], off[0], j
    return None


# ------------------------------------------------------------------ the plan
def candidates(L, h, centre=None, radius=None, band=None, far_from_start=START_FAR, bot_far=BOT_FAR, step=2):
    """Cells of the crew's ground of half h a point may stand on -> [(x, floor y, z)]. centre / radius: only within
    that of a place in the plan; band: only floors within TOP_BAND of that height."""
    G, w, out = L.ground(h), L.ground(h).w, []
    for (cx, cz, lv), (_d, y) in h.sym.items():
        x, z = w.centre((cx, cz))
        if int(x // w.CELL) % step or int(z // w.CELL) % step:           # (thinned on the world's lattice, not the box's)
            continue
        if centre is not None and math.hypot(x - centre[0], z - centre[1]) > radius:
            continue
        if band is not None and abs(y - band) > TOP_BAND:
            continue
        p = (x, y, z)
        if hdist(p, h.anchor) < far_from_start and abs(y - h.anchor[1]) < 400.0:
            continue
        if any(math.dist(p, q) < bot_far for q in L.bots) or any(math.dist(p, q) < NPC_FAR for q in L.npcs):
            continue
        if not all(any(abs(h.sym.get((cx + dx, cz + dz, l), (0.0, 1e9))[1] - y) <= 12.0 * max(abs(dx), abs(dz), 1) for l in (lv - 1, lv, lv + 1))
                   for dx in range(-ROOM, ROOM + 1) for dz in range(-ROOM, ROOM + 1)):
            continue                                    # a body's room: level, free floor all round
        hit = L.polys.at(x, y, z, y - 120.0, y + 60.0, part=h.part)
        if hit is None or L.nav.clearance(x, hit[1], z, limit=EDGE + 1.0) < EDGE:
            continue
        if L.in_boxes(p) or (L.lane and KB.lane_dist(L.lane, p) < LANE_FAR):
            continue
        out.append(p)
    return out


def face_to(p, q):
    d = math.hypot(q[0] - p[0], q[2] - p[2]) or 1.0
    return ((q[0] - p[0]) / d, (q[2] - p[2]) / d)


def plan(L, opt=None, log=print):
    """What apply() writes -> dict: 'survey' (the points as they are), 'moves' [dict(node, to, face, hidden, why)],
    'switch' (two halves), 'notes'."""
    opt = dict(DEFAULTS, **(opt or {}))
    sc = L.sc
    sur = L.survey()
    P = collections.OrderedDict(folder=L.folder, map=L.map, options={k: v for k, v in opt.items()}, halves=[h.name for h in L.halves],
                                survey=[r for _k, r in sur], moves=[], switch=None, notes=[])
    taken = []
    def take(k, to, why, hidden=None, look=None):
        look = look or L.half_of(to).anchor
        P['moves'].append(collections.OrderedDict(node=sc.path[k][5:], was=[round(v, 1) for v in L.at(k)], to=[round(to[0], 1), round(to[1] + POINT_UP, 1), round(to[2], 1)],
                                                  floor=round(to[1], 1), face=[round(v, 3) for v in face_to(to, look)], hidden=hidden, why=why))
        taken.append(to)
    def free(c):
        return all(hdist(c, t) >= SEP or abs(c[1] - t[1]) > 300.0 for t in taken)
    def pinned(n):
        """--place N=x,y,z -> the cell of the crew's ground under it, or an error."""
        x, y, z = opt['place'][n]
        h = L.half_of((x, y, z))
        G = L.ground(h)
        st = G.state(h.sym, (x, y, z), dy=200.0, reach=1)
        if st is None:
            raise ValueError('--place %d: (%g, %g, %g) is not on the crew\'s ground of the %s' % (n, x, y, z, h.name))
        return (x, st[1][1], z)

    if len(L.halves) == 1:
        h = L.halves[0]
        todo = [(i, k, r) for i, (k, r) in enumerate(sur) if opt['all'] or r['verdict'] == 'bad' or (r['verdict'] == 'doubtful' and not opt['only_bad']) or (i + 1) in opt['place']]
        if any(r['hidden_at_load'] or r['geom3'] for _k, r in sur):
            P['notes'].append('a point is hidden at the load on a map of one place: apply shows it')
        if todo:
            keep = [L.at(k) for i, (k, r) in enumerate(sur) if i not in [t[0] for t in todo]]
            taken += keep
            mid = [sum(L.at(k)[a] for _i, k, _r in todo) / len(todo) for a in range(3)]
            cand = candidates(L, h, centre=(mid[0], mid[2]), radius=NEAR_MAX)
            log('  %d cell(s) of the crew\'s ground within %d of the points pass every test' % (len(cand), NEAR_MAX))
            for i, k, r in todo:
                if (i + 1) in opt['place']:
                    c = pinned(i + 1)
                    why = '--place'
                else:
                    p = L.at(k)
                    best = sorted((c for c in cand if free(c)), key=lambda c: (round(hdist(c, p), 1), abs(c[1] - p[1]), c[0], c[2]))
                    if not best:
                        raise ValueError('%s: no cell of the crew\'s ground within %d of it passes every test' % (sc.names[k], NEAR_MAX))
                    c = best[0]
                    why = '%s: %s -> the nearest cell of the crew\'s ground that passes every test, %d away in the plan, %d %s' % (
                        r['verdict'], '; '.join(r['why'][:2]), hdist(c, p), abs(c[1] + POINT_UP - p[1]), 'lower' if c[1] + POINT_UP < p[1] else 'higher')
                take(k, c, why, hidden=False if (r['hidden_at_load'] or r['geom3']) else None, look=L.start)
        return P

    # ---- two halves
    A, Bh = L.halves
    order = [k for k, _r in sur]
    n1 = max(1, min(len(order) - 1, int(opt['first'])))
    first, second = order[:n1], order[n1:]
    # the START half: its own floor, off the heisters' way, not at the START row
    cand = candidates(L, A, band=L.ground(A).under((A.anchor[0], A.anchor[1] + 60.0, A.anchor[2]))[1], far_from_start=BLAST_FAR)
    log('  %s: %d cell(s) of the START row\'s floor pass every test (not within %d of the START row, %d from the heisters\' places)' % (A.name, len(cand), BLAST_FAR, BOT_FAR))
    way = [q for q in L.bots if L.half_of(q) is A]
    # ... but the last LOW of them on the join box's floor: the round goes on only when the human - police now - has
    # walked into the box (the AI heisters never take the join without him), and from the START row's floor that is
    # the whole tower's stairs
    jb = L.join_rect()
    n_low = max(0, min(n1, int(opt['low']))) if jb else 0
    cand_low, jy = [], None
    if n_low:
        st = L.ground(A).state(A.sym, ((jb[0] + jb[1]) / 2, (jb[4] + jb[5]) / 2, (jb[2] + jb[3]) / 2), dy=(jb[5] - jb[4]) / 2 + 60.0, reach=6)
        if st is None:
            P['notes'].append('the join box of KLJoin.ini is not over the crew\'s ground of the %s: no point on its floor (--low ignored)' % A.name)
            n_low = 0
        else:
            jy = st[1][1]
            off = lambda c: max(jb[0] - c[0], c[0] - jb[1], jb[2] - c[2], c[2] - jb[3])
            cand_low = [c for c in candidates(L, A, band=jy, far_from_start=0.0) if off(c) >= JOIN_FAR]
            log('  %s: %d cell(s) of the join box\'s floor (y %d) pass every test (%d or more outside the box, %d from the heisters\' places)' % (A.name, len(cand_low), jy, JOIN_FAR, BOT_FAR))
            if abs(jy - L.ground(A).under((A.anchor[0], A.anchor[1] + 60.0, A.anchor[2]))[1]) <= TOP_BAND:
                n_low = 0                                # (the box is on the START row's own floor: nothing to gain)
    # 'at the elevator at the bottom' (owner, 2026-10-11): of the join floor's cells those within LIFT_NEAR of the box
    # and POST_FAR from every post of an enemy squad, the nearest to the box first
    jmid = ((jb[0] + jb[1]) / 2, 0.0, (jb[2] + jb[3]) / 2) if jb else None
    cand_lift = []
    if n_low and opt.get('lift_near', LIFT_NEAR) > 0:
        import kl_fa_bots_rt as RT
        posts = [q for _t, ps in RT.enemy_posts(L.B).items() for _w, q, _r in ps if abs(q[1] - jy) <= 300.0]
        # 'within LIFT_NEAR' is measured ON FOOT over the crew's ground, cell by cell from the floor under the box's
        # middle (steps along x and z: a little more than the straight way): the passage that leads to the hall is
        # near the box through a wall and far from it on foot
        w, near_by = L.ground(A).w, opt.get('lift_near', LIFT_NEAR)
        walk, todo = {st[0]: 0.0}, collections.deque([st[0]])
        while todo:
            k0 = todo.popleft()
            if walk[k0] + w.CELL > near_by:
                continue
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for lv in (k0[2] - 1, k0[2], k0[2] + 1):
                    k1 = (k0[0] + dx, k0[1] + dz, lv)
                    if k1 in A.sym and k1 not in walk and abs(A.sym[k1][1] - A.sym[k0][1]) <= SYM:
                        walk[k1] = walk[k0] + w.CELL
                        todo.append(k1)
        on_foot = lambda c: walk.get((*w.cell(c[0], c[2]), int(c[1] // 40)))
        cand_lift = [c for c in cand_low if on_foot(c) is not None and all(hdist(c, q) >= POST_FAR for q in posts)]
        log('  %s: %d of them within %d on foot of the join box\'s middle and %d from every post of an enemy squad on that floor (%d post(s))' % (
            A.name, len(cand_lift), near_by, POST_FAR, len(posts)))
    P['low'] = n_low
    for n, k in enumerate(first):
        i = order.index(k)
        low = n >= n1 - n_low
        if (i + 1) in opt['place']:
            c, why = pinned(i + 1), '--place'
        else:
            pool = [c for c in (cand_low if low else cand) if free(c)]
            if not pool and low:
                P['notes'].append('no cell of the join box\'s floor passes every test for point %d: it stays on the START row\'s floor' % (i + 1))
                low, pool = False, [c for c in cand if free(c)]
            if not pool:
                raise ValueError('%s: no free cell left for point %d' % (A.name, i + 1))
            lift = [c for c in cand_lift if free(c)] if low else []
            if low and cand_lift and not lift:
                P['notes'].append('no free cell within %d of the join box is left for point %d: it goes by the first form\'s rule (the cell of that floor farthest from the heisters\' places)' % (
                    opt.get('lift_near', LIFT_NEAR), i + 1))
            if lift:
                c = min(lift, key=lambda c: (round(on_foot(c) / 40.0), c[0], c[2]))
                why = 'at the elevator: on the join box\'s floor, the free cell nearest the box on foot - ' + '%d on foot (along x and z) and ' % on_foot(c) + '%d in a line from its middle, %d outside it, %d from the nearest place a step of the heisters names, %d or more from every post of an enemy squad' % (
                    hdist(c, jmid), max(jb[0] - c[0], c[0] - jb[1], jb[2] - c[2], c[2] - jb[3]), min(math.dist(c, q) for q in way) if way else -1, POST_FAR)
            else:
                score = lambda c: min([math.dist(c, q) for q in way] + [2.0 * hdist(c, t) for t in taken if abs(t[1] - c[1]) < 300.0] + [1e9])
                c = max(pool, key=lambda c: (round(score(c) / 40.0), -c[0], c[2]))
                why = 'on the %s floor, off the heisters\' way: %d from the nearest place a step of theirs names, %d from the %s' % (
                    'join box\'s' if low else 'START row\'s', min(math.dist(c, q) for q in way) if way else -1,
                    hdist(c, ((jb[0] + jb[1]) / 2, 0.0, (jb[2] + jb[3]) / 2)) if low else hdist(c, A.anchor), 'join box' if low else 'START row')
        near = min(way, key=lambda q: math.dist(c, q)) if way else A.anchor
        take(k, c, why, hidden=False, look=near)
    # the jump half: the authored places, each on the nearest cell that passes
    places = list(PLACES.get(L.map, []))
    L.ground(Bh)
    street = [q for q in L.bots if L.half_of(q) is Bh]
    look2 = (sum(q[0] for q in street) / len(street), 0.0, sum(q[2] for q in street) / len(street)) if street else Bh.anchor
    left = list(places)
    for k in second:
        i = order.index(k)
        if (i + 1) in opt['place']:
            take(k, pinned(i + 1), '--place', hidden=True, look=look2)
            continue
        c = None
        while left and c is None:
            x, z, what = left.pop(0)
            pool = sorted((c for c in candidates(L, Bh, centre=(x, z), radius=SNAP, step=1, bot_far=STREET_FAR) if free(c)), key=lambda c: (round(math.hypot(c[0] - x, c[2] - z), 1), c[0], c[2]))
            if pool:
                c = pool[0]
                why = '%s: (%d, %d) -> the nearest cell that passes every test, %d away; %d from the nearest place of the heisters, %d from the arrival places' % (
                    what, x, z, math.hypot(c[0] - x, c[2] - z), min(math.dist(c, q) for q in street) if street else -1, hdist(c, Bh.anchor))
            else:
                P['notes'].append('%s (%d, %d): no cell within %d of it passes every test (%d from every place of the heisters among them) - left out' % (what, x, z, SNAP, STREET_FAR))
        if c is None:
            # no authored place is left: where the run ends (within VAN_NEAR of the boarding action; without one, of
            # the arrival places), the cell farthest from the heisters' places. (The first form took the farthest
            # cell of the whole half: on the lanes build that was a corner 180 m from the van.)
            act = L.S['action']
            mid = L.at(act) if act and L.half_of(L.at(act)) is Bh else Bh.anchor
            pool = [c for c in candidates(L, Bh, centre=(mid[0], mid[2]), radius=VAN_NEAR, step=4) if free(c)]
            if not pool:
                raise ValueError('%s: no place for point %d' % (Bh.name, i + 1))
            c = max(pool, key=lambda c: (round(min([math.dist(c, q) for q in street] + [1e9]) / 40.0), -c[0], c[2]))
            why = 'no authored place left: within %d of %s, the cell farthest from the heisters\' places (%d)' % (
                VAN_NEAR, 'the boarding action' if mid is not Bh.anchor else 'the arrival places', min([math.dist(c, q) for q in street] + [1e9]))
            P['notes'].append('point %d has no authored place: %s at (%d, %d, %d) - LOOK at it before a live run' % (i + 1, why, *c))
        take(k, c, why, hidden=True, look=look2)
    # the switch
    sw = collections.OrderedDict(at=opt['at'])
    k = free_switch(L)
    old = switches(L)
    if old:                                             # a build this step has been through: its lists are made anew
        sw['replaces'] = [sc.path[s['node']][5:] for s in old]
    mine = [s['node'] for s in old if [sc.p.key(nm) for nm, _b in sc.nodes[s['node']]['ctrls']] == ['DeactivateGeom', 'ActivateGeom'] and s['when'] != 'round']
    if not mine and k is None:
        raise ValueError('no free helper box (a DeactivateGeom nobody names, its list empty) to carry the switch')
    sw['node'] = sc.path[mine[0] if mine else k][5:]
    if opt['at'] == 'jump':
        jp = [j for j, _i, _v in kl_fa.controllers(sc, 'JumpPoint') if math.dist(L.at(j), Bh.entry) < 20.0]
        if not jp:
            raise ValueError('no JumpPoint at the jump entry')
        sw['by'], sw['by_ctrl'], sw['by_field'] = sc.path[jp[0]][5:], 'JumpPoint', 0
    else:
        jb = join_box(L)
        if jb is None:
            raise ValueError('no trigger box a criminal fires holds the arrival places of KLJoin.ini [CrewJoin] (use --at jump)')
        v = ctrl_values(sc, jb, 'TriggerBox')[0][1]
        sw['by'], sw['by_ctrl'], sw['by_field'] = sc.path[jb][5:], 'TriggerBox', max(i for i, x in enumerate(v) if isinstance(x, list))
        sw['by_box'] = 'at (%d, %d, %d) half (%d, %d, %d), fired by %s' % (*L.at(jb), *L.B.box(jb), next(x for x in v if isinstance(x, str) and x.startswith('ECPS_')))
    sw['off_at_join'] = [sc.path[x][5:] for x in first]
    sw['on_at_join'] = [sc.path[x][5:] for x in second]
    rp = round_pair(L) if opt['reset'] else None
    if rp:
        sw['reset'] = collections.OrderedDict(shows=sc.path[rp[0]][5:], hides=sc.path[rp[1]][5:], timer=sc.path[rp[2]][5:],
                                              seconds=ctrl_values(sc, rp[2], 'TriggerDelay2')[0][1][0] if ctrl_values(sc, rp[2], 'TriggerDelay2') else None)
    elif opt['reset']:
        P['notes'].append('no once-a-round ActivateGeom / DeactivateGeom pair on the round-start list: the points are put back for the next round only by the game\'s own restore (the two controllers save and load what they name)')
    P['switch'] = sw
    return P


# ------------------------------------------------------------------ apply
def _set_point(L, k, pos, face, hidden):
    """A spawn point's place, facing and 'hidden at the load': .prp ZGEOM[2] / [1] / [3] and the .gms record
    (the stock pair, as kl_fa_author.place writes them)."""
    import kl_graft
    sc, e = L.sc, L.B.ents[k - 1]
    lab = J.labels('dd', sc.cls(k))
    m9 = KB.rot9(face[0], face[1]) if face is not None else None
    def fn(us):
        if m9 is not None:
            us[lab.index('ZGEOM[1]')] = [us[lab.index('ZGEOM[1]')][0]] + [(0x0a, struct.pack('<f', x)) for x in m9] + [us[lab.index('ZGEOM[1]')][-1]]
        if pos is not None:
            i = lab.index('ZGEOM[2]')
            us[i] = [us[i][0]] + [(0x0a, struct.pack('<f', float(x))) for x in pos] + [us[i][-1]]
        if hidden is not None:
            i = lab.index('ZGEOM[3]')
            us[i] = [(us[i][0][0], bytes([int(bool(hidden))]))]
    kl_graft.edit(sc.nodes[k], 'props', fn)
    if m9 is not None:
        e.rot = struct.pack('<9f', *m9) + bytes(12)
    if pos is not None:
        e.trans = struct.pack('<3f', *pos) + bytes(4)
    if hidden is not None:
        e.flags = e.flags | HIDDEN if hidden else e.flags & ~HIDDEN


def _set_list(sc, k, ci, fi, paths):
    def fn(us):
        us[fi] = kl_fa._refs(sc, paths)
    kl_fa.edit(sc, k, ci, fn)


def apply(src, dst, opt=None, log=print):
    """The build of folder `src` written to the NEW folder `dst` with its AFTER_DEATH points put right -> report."""
    import kl_graft
    if os.path.exists(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: this step writes into a new folder only' % dst)
    L = Lv(src, log)
    B, sc = L.B, L.sc
    if sc.p.serialize() != B['.prp']:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte: not changed')
    KB._roundtrip(B)
    _d0, bad0, paths0, _n0 = J.check(sc, log=lambda *_a: None)
    P = plan(L, opt, log)
    res = lambda s: sc.resolve(R_ + s)[0]
    for m in P['moves']:
        _set_point(L, res(m['node']), m['to'], m['face'], m['hidden'])
    sw = P['switch']
    if sw:
        full = lambda names: [R_ + s for s in names]
        for old in sw.get('replaces', []):              # a switch of an earlier run of this step: emptied first
            k = res(old)
            for name in ('DeactivateGeom', 'ActivateGeom'):
                for ci, v in ctrl_values(sc, k, name):
                    _set_list(sc, k, ci, 1, [s for s in v[1] if not any(s.lower() == sc.path[x].lower() for x in L.points)])
        k = res(sw['node'])
        ci = ctrl_values(sc, k, 'DeactivateGeom')[0][0]
        _set_list(sc, k, ci, 1, full(sw['off_at_join']))
        have = ctrl_values(sc, k, 'ActivateGeom')
        if have:
            _set_list(sc, k, have[0][0], 1, full(sw['on_at_join']))
        else:
            form = next(((nm, b) for j in range(1, len(sc.nodes)) for nm, b in sc.nodes[j]['ctrls'] if sc.p.key(nm) == 'ActivateGeom'), None)
            if form is None:
                raise ValueError('the build has no ActivateGeom controller to take the form of')
            sc.nodes[k]['ctrls'].append((form[0], list(form[1])))
            ci2 = len(sc.nodes[k]['ctrls']) - 1
            def fn(us):
                us[0] = [kl_fa._str(sc, 'AITrigger')]
                us[1] = kl_fa._refs(sc, full(sw['on_at_join']))
                us[2] = [(us[2][0][0], b'\0')]
            kl_fa.edit(sc, k, ci2, fn)
        me = (R_ + sw['node']).lower()
        for a, c, f in namers(sc).get(me, []):          # (an earlier run with the other --at: that name goes)
            if c in ('TriggerBox', 'JumpPoint'):
                for ci, v in ctrl_values(sc, a, c):
                    if isinstance(v[f], list) and any(s.lower() == me for s in v[f]):
                        _set_list(sc, a, ci, f, [s for s in v[f] if s.lower() != me])
        by = res(sw['by'])
        ci, v = ctrl_values(sc, by, sw['by_ctrl'])[0]
        _set_list(sc, by, ci, sw['by_field'], list(v[sw['by_field']]) + [R_ + sw['node']])
        if sw.get('reset'):
            for key, ctl, names in (('shows', 'ActivateGeom', sw['off_at_join']), ('hides', 'DeactivateGeom', sw['on_at_join'])):
                k2 = res(sw['reset'][key])
                ci, v = ctrl_values(sc, k2, ctl)[0]
                mine = {sc.path[x].lower() for x in L.points}
                _set_list(sc, k2, ci, 1, [s for s in v[1] if s.lower() not in mine] + full(names))
    data, bad, paths, _n = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0) or len(paths) > len(paths0):
        raise ValueError('after the change %d objects do not fit their class (%d before) and %d paths do not resolve (%d before)' % (len(bad), len(bad0), len(paths), len(paths0)))
    faults = B.scene.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    gms, buf = B.scene.write()
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    if not set(changed) <= {'.prp', '.gms'}:            # (no entity is added, removed or changes pool: the .buf stays)
        raise ValueError('members changed: %s' % changed)
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(L.zip)), [(n, new[n]) for n in B.order])
    for f in os.listdir(src):
        q = os.path.join(src, f)
        if os.path.isfile(q) and q != L.zip and not f.startswith('fedpoints.') and f not in STALE:
            shutil.copyfile(q, os.path.join(dst, f))
    stale = [f for f in STALE if os.path.isfile(os.path.join(src, f))]
    if stale:
        P['notes'].append('%s of the source are NOT copied (they name the source\'s content id): run `python tools\\kl_maps.py audit "%s"` on this folder' % (' / '.join(stale), dst))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['fedpoints'], st['final'] = changed, kl_maps.member_ids(dst, L.slot)
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    import hashlib
    rep = collections.OrderedDict(source=src, source_sha1=hashlib.sha1(open(L.zip, 'rb').read()).hexdigest(), out=dst, members_changed=changed, moved=P['moves'], switch=sw,
                                  notes=P['notes'], survey_before=P['survey'], options=P['options'])
    # the result read back and judged
    L2 = Lv(dst, log)
    rep['survey_after'] = [r for _k, r in L2.survey()]
    with open(os.path.join(dst, 'fedpoints.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    L2 = Lv(dst, log)                                   # (who() reads fedpoints.json)
    lines = ['kl_fa_fedpoints: %s (archive sha1 %s) -> %s' % (src, rep['source_sha1'], out), '  members changed: %s' % (' '.join(changed) or 'none')]
    lines += ['  %s: (%d, %d, %d) -> (%d, %d, %d)%s  %s' % (m['node'].split('!')[-1], *m['was'], *m['to'], ' HIDDEN at the load' if m['hidden'] else '', m['why']) for m in P['moves']]
    if sw:
        lines.append('  the switch %s, named by %s (%s%s): at the join OFF %s, ON %s' % (sw['node'], sw['by'], sw['by_ctrl'], ', ' + sw['by_box'] if sw.get('by_box') else '',
                     ', '.join(s.split('!')[-1] for s in sw['off_at_join']), ', '.join(s.split('!')[-1] for s in sw['on_at_join'])))
        if sw.get('reset'):
            lines.append('  put back every round by %s (shows) and %s (hides), which %s names %s s after the round-start event' % (
                sw['reset']['shows'].split('!')[-1], sw['reset']['hides'].split('!')[-1], sw['reset']['timer'].split('!')[-1], sw['reset']['seconds']))
    lines += ['  NOTE: ' + s for s in P['notes']]
    if sw:
        lines.append('  NOT RUN IN THE GAME: no spawn point was ever hidden or named by a geom controller in a level of either game - '
                     'live checks P0, P1, P2 of re/fed_points.md 6 before this build goes on the owner\'s tab')
    with open(os.path.join(dst, 'fedpoints.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    for s in lines:
        log(s)
    return rep


# ------------------------------------------------------------------ report / check
def table(L, sur, log=print):
    log('%s: map %s, %d AFTER_DEATH point(s); %s' % (L.folder, L.map or '?', len(sur), '; '.join(
        '%s = mesh part %d (%d polygons), anchor (%d, %d, %d)' % (h.name, h.part, L.nav.part_size[h.part], *h.anchor) for h in L.halves)))
    for i, (k, r) in enumerate(sur):
        log('  %d %-22s (%6d %6d %6d) %-10s %-8s floor %s%s; %s; mesh: %s%s; %s from a heister\'s place, %s from the %s' % (
            i + 1, r['name'], *r['place'], r['half'], r['verdict'].upper(), 'none' if r['floor'] is None else '%d (%d below it)' % (r['floor'], r.get('above_floor', 0)),
            ', HIDDEN at the load' if r['hidden_at_load'] else '', r.get('walk', '-'), r['mesh'], '; in ' + ', '.join(r['boxes']) if r['boxes'] else '',
            r.get('from_bots', '-'), r.get('from_anchor', '-'), 'START row' if r['half'] != 'jump half' else 'arrival places'))
        for w in r['why']:
            log('      %s' % w)
        log('      placed by: %s' % r['who'])


def report(folder, log=print):
    L = Lv(folder, log)
    sur = L.survey()
    table(L, sur, log)
    for s in switches(L):
        log('  switch %s (%s): OFF %s; ON %s; named by %s' % (L.sc.path[s['node']][5:], s['when'], [L.sc.names[x].split('!')[-1] for x in s['off']],
            [L.sc.names[x].split('!')[-1] for x in s['on']], ['%s @%s' % (L.sc.path[a][5:][-60:], c) for a, c, _f in s['by']]))
    return L, sur


def check(folder, log=print):
    """-> (list of ('FAIL' | 'NOTE', text), facts). FAIL: a point over no floor, closed in, on a mesh part not joined
    to the crew's, in a bound / kill box; a two-halves map whose points are on the wrong side of the join."""
    L, sur = report(folder, log)
    sc, out = L.sc, []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    if not sur:
        fail('no %s spawn point: a dead player who comes back stays where the level put the police body' % DEAD)
    for i, (k, r) in enumerate(sur):
        for w in r['bad']:
            fail('%s (%d, %d, %d): %s' % (r['name'], *r['place'], w))
        for w in r['doubt']:
            note('%s (%d, %d, %d): DOUBTFUL: %s' % (r['name'], *r['place'], w))
        for w in r['note']:
            note('%s (%d, %d, %d): %s' % (r['name'], *r['place'], w))
        if r['geom3'] != r['hidden_at_load']:
            fail('%s: ZGEOM[3] = %d but .gms flag 0x400 is %s (stock keeps the pair equal)' % (r['name'], r['geom3'], 'set' if r['hidden_at_load'] else 'clear'))
    sw = switches(L)
    named = {x for s in sw for x in s['off'] + s['on']}
    shown = [k for k, r in sur if not r['hidden_at_load']]
    if sur and not shown:
        fail('every point is hidden at the load: the pick finds none (kl2 0x5614f0), the police body stays where the level put it')
    facts = collections.OrderedDict(points=len(sur), good=sum(r['verdict'] == 'good' for _k, r in sur), doubtful=sum(r['verdict'] == 'doubtful' for _k, r in sur),
                                    bad=sum(r['verdict'] == 'bad' for _k, r in sur), halves=len(L.halves), switches=len(sw))
    if len(L.halves) == 1:
        for k, r in sur:
            if r['hidden_at_load']:
                fail('%s is hidden at the load and this map has one place: nothing has a reason to show it' % r['name'])
        for s in sw:
            note('%s switches AFTER_DEATH points on a map of one place' % sc.path[s['node']][5:])
    else:
        A, Bh = L.halves
        first = [k for k, r in sur if r['half'] == A.name]
        second = [k for k, r in sur if r['half'] == Bh.name]
        facts.update(start_half=len(first), jump_half=len(second))
        if not first:
            fail('no point in the %s: before the join a dead player can only come back in the half the round has not reached' % A.name)
        if not second:
            fail('no point in the %s: after the join a dead player comes back in the half the round has left' % Bh.name)
        for k, r in sur:
            if r['half'] == A.name and r['hidden_at_load']:
                fail('%s (START half) is hidden at the load: before the join it is not a candidate' % r['name'])
            if r['half'] == Bh.name and not r['hidden_at_load']:
                fail('%s (jump half, (%d, %d, %d)) is SHOWN at the load: a player who dies BEFORE the join may come back in the half the crew is not in (%d of the %d shown points)' % (
                    r['name'], *r['place'], len([x for x in shown if x in second]), len(shown)))
        joins = [s for s in sw if s['when'] == 'join']
        off = {x for s in joins for x in s['off']}
        on = {x for s in joins for x in s['on']}
        if set(first) - off:
            fail('%d point(s) of the START half are never switched off at the join (%s): a player who dies AFTER the join may come back in the half the round has left' % (
                len(set(first) - off), ', '.join(sc.names[x].split('!')[-1] for x in sorted(set(first) - off))))
        if set(second) - on:
            fail('%d point(s) of the jump half are never switched on at the join (%s)' % (len(set(second) - on), ', '.join(sc.names[x].split('!')[-1] for x in sorted(set(second) - on))))
        if off & set(second) or on & set(first):
            fail('the join\'s switch names a point of the wrong half')
        for s in joins:
            cs = [sc.p.key(nm) for nm, _b in sc.nodes[s['node']]['ctrls']]
            if any(c not in ('ActivateGeom', 'DeactivateGeom') for c in cs):
                fail('%s carries %s besides the two switches: the message it is sent reaches those too' % (sc.path[s['node']][5:], cs))
            for _ci, v in ctrl_values(sc, s['node'], 'DeactivateGeom') + ctrl_values(sc, s['node'], 'ActivateGeom'):
                if v[0] != 'AITrigger':
                    note('%s waits for %r (it also takes AITrigger: kl2 0x41a560 / 0x538e40)' % (sc.path[s['node']][5:], v[0]))
            how = sorted({c for _a, c, _f in s['by']})
            facts['join_switch'] = dict(node=sc.path[s['node']][5:], named_by=['%s @%s' % (sc.path[a][5:], c) for a, c, _f in s['by']])
            if how == ['TriggerBox']:
                note('the switch is fired by the trigger box the crew arrives in (%s), not by the jump itself: a criminal has to stand in it after the jump '
                     '(the AI heisters are put inside it by the hook; whether an AI actor fires a box is not read) - a police player who takes the join does not fire it, and has no second return to need it'
                     % ', '.join(sc.path[a][5:] for a, _c, _f in s['by']))
        rounds = [s for s in sw if s['when'] == 'round']
        back_on = {x for s in rounds for x in s['on']}
        back_off = {x for s in rounds for x in s['off']}
        facts['reset'] = bool(rounds)
        if joins and (set(first) - back_on or set(second) - back_off):
            note('nothing of the round-start list puts the points back (%d of the START half not shown again, %d of the jump half not hidden again): a second round on the same '
                 'loaded level rests on the game restoring them (ActivateGeom / DeactivateGeom save and load what they name: kl2 0x899c50, 0x6e8c70, 0x8d6750 - whether an Arcade round start runs that is not read)'
                 % (len(set(first) - back_on), len(set(second) - back_off)))
    try:                                # review M1 / S4 of re/retomoto_spawns_review.md: NOTEs only, they need kl_map_ai's audit
        import kl_map_ai
        rows = kl_map_ai.spawn_rows(L)
        for sq, d, nm in kl_map_ai.sleeping_near_fed(L, rows):
            note('SLEEPING MEN NEAR A FED POINT: %s has a man %d from %s and is hidden from the load (ZSquadScript field 3 = 0): a fed who comes back there sees them appear (kl_map_ai spawnfix puts the Retomoto tables in)' % (sq, d / 100.0 if False else round(d), nm))
        if L.map == 'M09_A' and len(L.halves) == 2:
            import kl_fa_author as au
            import kl_fa_street as st
            want = set(au.HALL_ACTIVE) | {n for v in st.ACTIVE.values() for n in v}
            asleep = [r['squad'] for r in rows if not r['active'] and any(r['squad'].endswith(w.split('!', 1)[-1]) or r['squad'] == w[5:] for w in want)]
            if asleep:
                note('%d squad(s) of kl_fa_author.HALL_ACTIVE / kl_fa_street.ACTIVE are still field 3 = 0 in this build (wire() / relay() do not write them): run kl_map_ai spawnfix' % len(asleep))
    except Exception as e:
        note('spawn audit not run: %s' % e)
    n_fail = sum(1 for a, _b in out if a == 'FAIL')
    for a, b in out:
        log('%s: %s' % (a, b))
    log('RESULT (kl_fa_fedpoints): %s (%d FAIL, %d NOTE); %d point(s): %d good, %d doubtful, %d bad%s' % (
        'FAIL' if n_fail else 'PASS', n_fail, len(out) - n_fail, facts['points'], facts['good'], facts['doubtful'], facts['bad'],
        '; START half %d, jump half %d' % (facts['start_half'], facts['jump_half']) if len(L.halves) > 1 else ''))
    return out, facts


def diff(src, dst, log=print):
    """What differs between a build and this step's output -> True when only what the step means to change does:
    members .prp and .gms and nothing else (a changed .buf is UNEXPECTED: this diff does not read it, and the step
    has no reason to change it), steps.json, fedpoints.*, audit.* gone or made anew; in the .prp only the
    AFTER_DEATH points' ZGEOM[1..3], the switch's two controllers and one more entry in the list that names it,
    and the two lists of the once-a-round pair; in the .gms only those points' entity records, and of those only
    matrix, place and flag 0x400 - every other field of every record is compared too: type, model, aux, REF, raw
    block, group, parent, children, list key, list links. The .gms tables outside the records (clusters, list pool,
    matrix pool) are regenerated by kl_scene from the records and are not compared one by one."""
    A, Bn = Lv(src, lambda *_a: None), Lv(dst, lambda *_a: None)
    ok = True
    def bad(s):
        nonlocal ok
        ok = False
        log('  UNEXPECTED: ' + s)
    with zipfile.ZipFile(A.zip) as a, zipfile.ZipFile(Bn.zip) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            bad('the member list changed')
        mem = [(i.filename.rsplit('_Main', 1)[-1], (i.CRC, i.file_size) == (j.CRC, j.file_size), i.file_size, j.file_size) for i, j in zip(ia, ib)]
    for e, same, sa, sb in mem:
        log('  member %-14s %s' % (e, 'same (CRC, %d bytes)' % sa if same else 'CHANGED %d -> %d bytes' % (sa, sb)))
        if not same and e not in ('.prp', '.gms'):
            bad('member %s differs%s' % (e, ' (this diff does not read a .buf: nothing of the step should change it)' if e == '.buf' else ''))
    import hashlib
    sha = lambda p: hashlib.sha1(open(p, 'rb').read()).hexdigest()
    fa, fb = set(os.listdir(src)), set(os.listdir(dst))
    for f in sorted(fa | fb):
        if f.lower().endswith('_main.zip'):
            continue
        if f not in fa:
            log('  beside: %-28s NEW' % f)
            if not f.startswith('fedpoints.') and f not in STALE:
                bad('file %s is new' % f)
        elif f not in fb:
            if f in STALE:
                log('  beside: %-28s NOT COPIED (it names the source\'s content id; no audit of the output yet)' % f)
            else:
                bad('file %s is gone' % f)
        elif sha(os.path.join(src, f)) != sha(os.path.join(dst, f)):
            log('  beside: %-28s CHANGED' % f)
            if f != 'steps.json' and not f.startswith('fedpoints.') and f not in STALE:
                bad('file %s differs' % f)
        elif f in STALE:
            bad('file %s is the source\'s own, byte for byte: a stale paper (it names another archive\'s content id)' % f)
    log('  beside: %d other file(s) equal' % len([f for f in fa & fb if not f.lower().endswith('_main.zip') and sha(os.path.join(src, f)) == sha(os.path.join(dst, f))]))
    # the property tree, node by node
    sa, sb = A.sc, Bn.sc
    if sa.names != sb.names or sa.tids != sb.tids:
        bad('the entities differ')
        return ok
    pts = set(A.points)
    lab = J.labels('dd', 'ZSpawnPoint')
    allowed = {lab.index('ZGEOM[%d]' % i) for i in (1, 2, 3)}
    mine = {sb.path[k].lower() for k in Bn.points}
    n_nodes = n_ctrl = 0
    from kl_prp import units
    txt = lambda s, toks: J.text(s, toks)
    for k in range(1, len(sa.nodes)):
        na, nb = sa.nodes[k], sb.nodes[k]
        if txt(sa, na['props']) != txt(sb, nb['props']):
            n_nodes += 1
            va, vb = kl_fa.node_values(sa, k), kl_fa.node_values(sb, k)
            d = {i for i in range(max(len(va), len(vb))) if i >= len(va) or i >= len(vb) or va[i] != vb[i]}
            if k not in pts or not d <= allowed:
                bad('node %s: properties %s differ' % (sa.path[k], sorted(d)))
        ca = [(sa.p.key(nm), [kl_fa.value(sa, u) for u in units(b[1:-1])]) for nm, b in na['ctrls']]
        cb = [(sb.p.key(nm), [kl_fa.value(sb, u) for u in units(b[1:-1])]) for nm, b in nb['ctrls']]
        if ca == cb:
            continue
        n_ctrl += 1
        strip = lambda cs: [(n, [[s for s in v if not (isinstance(s, str) and s.lower() in mine)] if isinstance(v, list) and all(isinstance(s, str) for s in v) else v for v in vs]) for n, vs in cs]
        sw_names = {sb.path[s['node']].lower() for s in switches(Bn)}
        strip2 = lambda cs: [(n, [[s for s in v if not (isinstance(s, str) and s.lower() in sw_names)] if isinstance(v, list) and all(isinstance(s, str) for s in v) else v for v in vs]) for n, vs in cs]
        a2, b2 = strip2(strip(ca)), strip2(strip(cb))
        if a2 == b2:
            continue                                    # only entries that name an AFTER_DEATH point or the switch came or went
        if sb.path[k].lower() in sw_names and a2 == [c for c in b2 if c[0] != 'ActivateGeom'] and [c[0] for c in cb].count('ActivateGeom') == 1:
            continue                                    # the switch: its ActivateGeom is new
        bad('node %s: controllers differ: %s -> %s' % (sa.path[k], [c[0] for c in ca], [c[0] for c in cb]))
    log('  .prp: %d node(s) with other properties (the AFTER_DEATH points: ZGEOM[1..3] only), %d node(s) with other controller values' % (n_nodes, n_ctrl))
    ne = 0
    if len(A.B.ents) != len(Bn.B.ents):
        bad('.gms: %d entity records -> %d' % (len(A.B.ents), len(Bn.B.ents)))
    ia, ib = {id(e): n for n, e in enumerate(A.B.ents)}, {id(e): n for n, e in enumerate(Bn.B.ents)}
    def rest(e, ix):
        """Everything of a record but matrix, place and flags; the tree and the list links by entity number."""
        at = lambda t: None if t is None else ix.get(id(t), -1)
        return (e.name, e.tid, e.model, e.aux, e.ref, e.raw, e.group, at(e.parent), [at(c) for c in e.kids], e.lkey,
                None if e.links is None else [(at(t), bits) for t, bits in e.links])
    for k, (ea, eb) in enumerate(zip(A.B.ents, Bn.B.ents), 1):
        ra, rb = rest(ea, ia), rest(eb, ib)
        if (ea.rot, ea.trans, ea.flags) != (eb.rot, eb.trans, eb.flags) or ra != rb:
            ne += 1
            if k not in pts or ra != rb or (ea.flags ^ eb.flags) & ~HIDDEN:
                bad('.gms record of %s differs%s' % (sa.path[k], ': ' + ', '.join(n for n, x, y in zip(
                    ('name', 'type', 'model', 'aux', 'REF', 'raw', 'group', 'parent', 'children', 'list key', 'list links'), ra, rb) if x != y) if ra != rb else ''))
    log('  .gms: %d entity record(s) differ (place, matrix, flag 0x400 of AFTER_DEATH points only; name, type, model, aux, REF, raw, group, parent, children, list key and list links compared on all %d)' % (ne, len(A.B.ents)))
    log('RESULT (kl_fa_fedpoints diff): %s' % ('only what the step means to change differs' if ok else 'UNEXPECTED DIFFERENCES'))
    return ok


def way(L, p, q, drop=None):
    """The way on foot from place p to place q over the walk test's ground -> ([(x, floor y, z)] way points a
    straight walk joins, the deepest single drop on it, its length) or None. For a scripted player: the walk test
    has no body radius beyond one cell, so a way point is a place to walk TO, not a promise."""
    h = L.half_of(p)
    G = L.ground(h)
    c, fy, _near = G.under(p)
    if fy is None:
        return None
    par = {}
    best = G.spread(c, fy, wide=True, limit=DROP_OK if drop is None else drop, par=par)
    st = G.state(best, q, dy=150.0, reach=4)
    if st is None:
        return None
    keys = [st[0]]
    while keys[-1] in par:
        keys.append(par[keys[-1]])
    keys.reverse()
    def has(cx, cz, y):
        return any(abs(best.get((cx, cz, l), (0.0, 1e9))[1] - y) < 50.0 for l in (int(y // 40) - 1, int(y // 40), int(y // 40) + 1))
    def clear(a, b):
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        if n * 20.0 > 1500.0:
            return False
        ya, yb = best[a][1], best[b][1]
        for t in range(1, n):
            cx, cz, y = round(a[0] + (b[0] - a[0]) * t / n), round(a[1] + (b[1] - a[1]) * t / n), ya + (yb - ya) * t / n
            if not all(has(cx + dx, cz + dz, y) for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
                return False
        return True
    pts, i = [keys[0]], 0
    while i < len(keys) - 1:
        j = len(keys) - 1
        while j > i + 1 and not clear(keys[i], keys[j]):
            j -= 1
        pts.append(keys[j])
        i = j
    out = [(G.w.centre((k[0], k[1]))[0], best[k][1], G.w.centre((k[0], k[1]))[1]) for k in pts]
    return out, st[1][0], sum(math.dist(out[n], out[n + 1]) for n in range(len(out) - 1))


def ways(folder, n, to=None, log=print):
    """The ways a scripted fed can be walked from AFTER_DEATH point n (1-based, report's order): to `to`, or to the
    nearest place of the AI heisters, the boarding action and - in the START half of a map of two - the join box."""
    L = Lv(folder, log)
    k = L.points[n - 1]
    p = L.at(k)
    h = L.half_of(p)
    goals = collections.OrderedDict()
    if to is not None:
        goals['the place asked for'] = tuple(to)
    else:
        near = [q for q in L.bots if L.half_of(q) is h]
        if near:
            goals['the nearest place of the AI heisters'] = min(near, key=lambda q: math.dist(p, q))
        act = L.S['action']
        if act and L.half_of(L.at(act)) is h:
            goals['the boarding action'] = L.at(act)
        j = L.ini.get('join')
        if j and len(L.halves) > 1 and h is L.halves[0] and 'min' in j and 'max' in j:
            a, b = vec(j['min']), vec(j['max'])
            goals['the join box of KLJoin.ini (x %d..%d, z %d..%d)' % (min(a[0], b[0]), max(a[0], b[0]), min(a[2], b[2]), max(a[2], b[2]))] = ((a[0] + b[0]) / 2, p[1] if not near else min(near, key=lambda q: hdist(q, ((a[0] + b[0]) / 2, 0, (a[2] + b[2]) / 2)))[1], (a[2] + b[2]) / 2)
    log('%s at (%d, %d, %d), %s:' % (L.sc.names[k].split('!')[-1], *p, h.name))
    for name, q in goals.items():
        r = way(L, p, q)
        if r is None:
            log('  to %s (%d, %d, %d): NO WAY on foot (drops of up to %d counted)' % (name, *q, DROP_OK))
            continue
        pts, drop, length = r
        log('  to %s (%d, %d, %d): %d way points, %.0f m%s' % (name, *q, len(pts), length / 100.0, ', deepest drop %d' % drop if drop > L.ground(h).w.DOWN else ''))
        for x, y, z in pts:
            log('      %7.0f %7.0f %7.0f' % (x, y, z))
    return L


def options(a):
    opt, rest, i = dict(DEFAULTS, place={}), [], 0
    while i < len(a):
        x = a[i]
        if x == '--all':
            opt['all'] = True
        elif x == '--only-bad':
            opt['only_bad'] = True
        elif x == '--no-reset':
            opt['reset'] = False
        elif x == '--first' and i + 1 < len(a):
            opt['first'] = int(a[i + 1]); i += 1
        elif x == '--low' and i + 1 < len(a):
            opt['low'] = int(a[i + 1]); i += 1
        elif x == '--lift-near' and i + 1 < len(a):
            opt['lift_near'] = float(a[i + 1]); i += 1
        elif x == '--at' and i + 1 < len(a) and a[i + 1] in ('box', 'jump'):
            opt['at'] = a[i + 1]; i += 1
        elif x == '--place' and i + 1 < len(a) and '=' in a[i + 1]:
            n, v = a[i + 1].split('=', 1)
            opt['place'][int(n)] = vec(v); i += 1
        elif x.startswith('--'):
            sys.exit('unknown option %s' % x)
        else:
            rest.append(x)
        i += 1
    return opt, rest


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    opt, rest = options(a[1:])
    if a[0] == 'report' and len(rest) == 1:
        report(rest[0])
    elif a[0] == 'check' and len(rest) == 1:
        out, _f = check(rest[0])
        sys.exit(1 if any(x == 'FAIL' for x, _t in out) else 0)
    elif a[0] == 'plan' and len(rest) == 1:
        L = Lv(rest[0])
        P = plan(L, opt)
        table(L, list(zip(L.points, P['survey'])))
        for m in P['moves']:
            print('  MOVE %s: (%d, %d, %d) -> (%d, %d, %d)%s\n       %s' % (m['node'].split('!')[-1], *m['was'], *m['to'], ' HIDDEN at the load' if m['hidden'] else '', m['why']))
        if P['switch']:
            print('  SWITCH %s' % json.dumps(P['switch'], indent=1))
        for s in P['notes']:
            print('  NOTE: ' + s)
    elif a[0] == 'apply' and len(rest) == 2:
        apply(rest[0], rest[1], opt)
    elif a[0] == 'diff' and len(rest) == 2:
        sys.exit(0 if diff(rest[0], rest[1]) else 1)
    elif a[0] == 'way' and len(rest) in (2, 3):
        ways(rest[0], int(rest[1]), vec(rest[2]) if len(rest) == 3 else None)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
