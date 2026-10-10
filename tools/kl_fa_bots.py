#!/usr/bin/env python3
"""
AI heisters for a FINISHED Dead Men map build: the squad stock Dog Days Arcade has ('merc_bot_squad', seven
ZFFActor of team Ally with a route) and every grafted map lacks (kl_fa.check: 'no bot squads').
Spec, routes as coordinates, what could not be done, live checks: re/bots.md. Research it is built on:
re/bots_squad.md (what a squad is, read in kl2.exe and measured on F01..F09), re/bots_behaviour.md (backstab,
driver, van, help up), re/bots_voice.md (the heisters' lines). OFFLINE: nothing here installs anything.

    python kl_fa_bots.py build <build folder> <out folder> [options]    the squad into a COPY of the build
    python kl_fa_bots.py check <folder>                                 every check on a finished folder; exit 1 on a FAIL
    python kl_fa_bots.py plan  <build folder> [options]                 only the plan: stations, routes, what is not possible
    python kl_fa_bots.py diff  <build folder> <out folder>              what the step changed, file by file; exit 1 if
                                                                        anything but the squad differs
    python kl_fa_bots.py stock [F01 ...]                                the control: the stock squads through this
                                                                        module's reading of mesh and trigger boxes
    python kl_fa_bots.py sizes <folder> [<folder> ...]                  the four large blocks (.prm .ANM .fxc .WAV)
    python kl_fa_bots.py owner <root of builds> <out root> [M01 ...]    every map folder of the root with its RECIPE =
                                                                        the squad as the owner asked for it on 2026-10-10
                                                                        (re/bots.md 12): loot stops, cases, the diner's
                                                                        exit boxes, the bank's drop, the car's road
    options of 2026-10-10 evening (all OFF by default: without them a build is byte for byte what it was; RECIPE sets them)
      --stops N                up to N loot stops, each with a wait of its own: every loot area that holds at least
                               STOP_SHARE of the richest one, the nearest next from the ENTERS_BANK place on (default 1)
      --cases off|glass|all    a loot object of type CONTAINER cannot be taken before its OnlineMoneyContainer is opened;
                               Dead Men's jewel and watch cases open only when their GLASS IS SHOT, and no AI shoots at
                               an object. glass: a timer 1 s after the step before the loot place sends 'Activate' to
                               the glass (kl2 0x8d1b60: it shatters as if shot) and 'Open' to the container (0x766e50),
                               per bot for the CASE_BOTS nearest bots of each case. all: 'Open' to every container of
                               the stop, also those somebody near them opens (stock form). check() FAILs a loot wait
                               that names loot in a glass-only case nobody opens
      --exit-boxes keep|cut    cut: the level exit boxes of EXIT_CUT are cut back so that the loot that stood in them
                               is outside (M01: the Senator and his flank; a crew member in such a box calls the car)
      --drop                   DROPS: one link of kind 2 (a drop, the only kind stock Dog Days has) in the navigation
                               mesh where a Dog Days player walks down and the mesh has a gap (M03: the sunk wall
                               piece), a gather place in front of it inside an AllyEscapeBox as the fall-back
      --lane                   the places of the way out keep LANE_CLEAR from the escape car's spline routes and stay on
                               the side the bots come from (the builds of the afternoon had bots waiting IN the road)
    A KEY-FRAMED VAN (a build of `kl_map_escape.py van`: ONE OnlineEscAnimatedVehicle; 2026-10-10 night, re/bots.md 13)
      needs no option: its lane is the line of its position keys (van_drives) and is always kept clear; the bots end
      in an AllyEscapeBox PARK_SIDE beside its boarding box AT THE STOP, on the side they come from (the box itself
      rides on the van and lies at the waiting place in the file; a place ON the line is where the van's nose
      passes). With --drop the gather place in front of the one-way drop gets a second AllyEscapeBox.
      check() FAILs a place of the way out or a last place nearer than LANE_HALF + LANE_MAN to the vehicle's line
      (spline car or van), and a place beyond a one-way drop whose place before it is in no AllyEscapeBox.
    options
      --ally-box auto|on|off   an AllyEscapeBox at the boarding place with every bot's last place inside it (the form of
                               stock F02 F06 F08). auto (default): on when the vehicle is a helicopter or when the
                               boarding action is not on the navigation part of the START row; else the bots are parked
                               near the boarding action and board through ZBoardEscapeVehicleTactic (stock F03's form)
      --wait-guards            a TriggerActorsDead (the map's Enemy actor groups near the loot) before the loot wait,
                               as F01 / F07 have; default: none, as F08 / F09 (a wait without a time limit)
      --loot-seconds N         field 1 of TriggerLootDepleted: leave the loot when it is empty or after N s (default 20)
      --start-delay N          Timer_start_bots (default 10.0, stock)
      --heal                   OWNER'S 'help you up', the one data-only lead (re/bots_behaviour.md 4.3 A): ZSoldier
                               field 2 = eSometimes on the bots, which makes the exe build their ZHealTactic.
                               ASSUMPTION throughout - what that tactic does was not read. Off by default.
      --park x,y,z             where the bots end, when it is not the boarding action: the place on the START row's mesh
                               part nearest to it, with an AllyEscapeBox there (a two-part map: the jump box of its
                               KLJoin.ini). Not used by any delivered build.
      --no-tree                do not list the new groups in the scene root's group tree: then the .oct keeps its layout
                               and the .prm is not touched at all (members changed: .prp .gms .buf .oct .rmi .rmc only).
                               For an A / B run if a load fault points at the .oct or the .prm.
      --no-stage               do NOT route the bots through the map's gameplay triggers (then no bot ever has a
                               heist stage: no looting, no boarding by tactic, no betrayal). For comparison runs only.
      --early-call             the plan as it was until 2026-10-10: the shortest order of the stations and the richest
                               loot, even when the way to the loot crosses a level exit box. A bot in such a box CALLS
                               THE ESCAPE VEHICLE (kl2 0x6c3d50 -> 0x6cd8e0: any crew member, bot or human), and the
                               round ends one vehicle cycle + 60 s later - on M01 that was 152..156 s after GO (runs
                               BOT1 / BOT2), whatever the loot wait. Default: the way to the loot, the loot place and
                               every place before the loot wait stay out of the level exit boxes; check() FAILs a
                               build whose bots enter one before their loot wait (a NOTE with this option).

WHAT A SQUAD IS HERE (re/bots_squad.md 8, the smallest form every link of which a stock level uses)
  Gameplay!merc_bot_squad!Timer_start_bots       ZBoxPrimitive + TriggerDelay2 {10 s -> the first step of each squad};
                                                 named by Gameplay!AIMonitor list 2 (the round-start event)
  Gameplay!merc_bot_squad!Squad#0N  (N = 2..8)   ZGROUP + ZSquadScript (eStayBack, eHeistOnly ...), cloned from F07
    Glazer_Bodyguard_0N \\ Ground                 ZGROUP \\ ZFFActor + ZSoldier, cloned from F07's own Squad#0N: team Ally,
                                                 rifle of the SYSTEMS part, animation set Kane_NPC / Lynch_NPC, name
                                                 FACharacters/C<N>. Rewritten: place, facing, model = the build's
                                                 Heroes!Hero_0N\\Ground (a bot costs no model), the two .SND offsets = that
                                                 hero's. THE NAME STAYS: its digit at index 18 is the bot's line voice and
                                                 a name without one is an int3 at 0x51ab2d (re/bots_voice.md 7).
    01x_DefendBehaviour_to_loot + Pos#nn         DefendBehaviourRout, field 1 = up to three boxes walked in order
    020_Timer_done_looting                       TriggerLootDepleted {the map's loot near the place, N s}  (or a
                                                 TriggerDelay2 when the map has no loot object there)
    03x_DefendBehaviour_out + Pos#nn             ... through the way out and the level exit to the vehicle (eDMS_Sprint)
    040_SquadModifier_tight_defense_van          SquadModifierBehaviour eDM_Tight, the end of the chain (as F01 F03 F04 F07)
  Gameplay!merc_bot_squad!AllyEscapeBox          (option) ZBoxPrimitive + AllyEscapeBox, cloned from F02
  Looting, boarding and turning traitor are NOT in this data: they are three tactics of the soldier script that
  every Ally actor gets in Arcade (kl2 0x6ab56d..). What the route gives them is the bot's heist STAGE: 1 inside an
  ENTERS_BANK trigger, 2 EXITS_BANK, 3 BOARDS or the OnlineExitLevelTrigger (0x5dd890). So every route passes a
  place INSIDE each of those boxes.

HOW THE ROUTE IS PLANNED (plan())
  The level's own navigation mesh (kl_pf4 arrays 3 / 9 / 6) is read as polygons with neighbours per edge; a shortest
  path over the polygons (Dijkstra, through the middles of the shared edges) joins START row -> ENTERS_BANK box ->
  loot -> EXITS_BANK box -> level exit box -> the boarding place. A route box is put only on a polygon of the
  START row's connected part, at the mesh's height there, with CLEAR to the nearest edge that has no neighbour (a
  wall, a drop, the end of the mesh); each of the seven bots gets its own place per station (SEP apart), as stock.
  Where a station is not on that part the plan says so and uses what is left (M03: the boarding action is beyond the
  yard wall the mesh does not cross -> the AllyEscapeBox stands on the bots' side of it).

WHAT IS WRITTEN (apply()): .prp (the subtrees appended, AIMonitor list 2), .gms + .buf (kl_scene: entities, cluster
  table, type table), .oct / .rmi / .rmc (every SLOT id renumbered: appending top-level groups moves every slot;
  the squad and step groups are listed in the scene root's group tree with the box of their places, as F07 lists
  them - measured: root set, tree 3, box = the places +- 10), and, because that tree grows and the collision records
  behind it move, .prm: the 4-byte record offset in each model root that names one, in place (same size; kl_graft
  does the same for S's records). Nothing else: no model, no animation, no sound, no shader.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, heapq, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene, kl_pf4, kl_rtp
import kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp, units

SLOT = 'F01'
R_ = 'ROOT\\'
SQUAD = 'Gameplay!merc_bot_squad!'          # the prefix F01 F04 F05 F07 F08 F09 use; kl_fa.host_keep keeps Gameplay!AIMonitor
BOTS = range(2, 9)                          # Squad#02..#08 = characters C2..C8; the human is crew record 0
GROUP_NAME = 'Glazer_Bodyguard_0%d'         # kl2 0x588980 reads the digit at index 18 of this name
BIG = ('.prm', '.ANM', '.fxc')              # + the .WAV beside the archive: each is read into one block (CLAUDE.md)

# ---- placing (units = the game's, 100 = 1 m)
CLEAR = 60.0            # GUESS: least distance of a route place from a mesh edge without a neighbour. A person's radius:
                        # kl_fa_loot.BODY = 30 (run J1); stock F07's places were not measured against its mesh
CLEAR_MIN = 10.0        # check(): below this a place counts as 'on the edge'. The mesh is already drawn in from the walls
                        # by about a person's radius (measured: M01's diner doors are strips 43..50 wide), so a
                        # place ON a polygon can be stood on; in a doorway 20 is all there is
SEP = 110.0             # stock: bots stand at least ~100 apart (re/bots_squad.md 6); places of one station likewise
START_NEAR, START_FAR = 110.0, 420.0    # stock: each bot 80..440 from the nearest START point, never on one
SPACING = 1800.0        # GUESS: a route box at least every 18 m of path (stock F07: 28 steps on ~250 m)
STEP_MAX = 3            # DefendBehaviourRout field 1 holds 1..3 boxes in every stock use (497 uses)
DY = 130.0              # a place counts as 'on' a polygon within this height of it
INSIDE = 0.45           # a place is put within this share of a trigger box's size values: inside whether the three
                        # values are half extents (re/bots_squad.md 8.5, kl_fa_street.half) or full ones
PARK = (150.0, 400.0)   # re/bots_squad.md 8.3: the last place 150..400 from the boarding action (tactic form)
ALLY_SIZE = (350.0, 416.0, 350.0)       # stock F02 / F06: BoardingTrigger_Heli0n_incoming_X
ALLY_UP = 200.0         # GUESS: the box's middle above the floor (its y size covers the floor either way)
GATE_BACK = 140.0       # GUESS: the gather place in front of a drop link lies this far back from the take-off
LANE_CLEAR = 250.0      # GUESS (option lane): a place on the way out is at least this far from the escape car's route
                        # in the plan (the van's wheels stand 98 to either side, tools/kl_map_escape.py; a man is 30)
LANE_REACH = 500.0      # ... and is looked for within this of the shortest path
LANE_HALF = 100.0       # half the width of the escape vehicle's body (kl_map_escape.HALF; the van's KillBox is 90 x 100 x 56)
LANE_MAN = 60.0         # GUESS: clearance of a standing bot from the body's side (a person's radius is 30, CLEAR is 60)
                        # check(): a way-out or park place nearer than LANE_HALF + LANE_MAN to the vehicle's line is a FAIL
PARK_SIDE = 420.0       # a key-framed van: the middle of the bots' AllyEscapeBox stands this far to the side of the van's
                        # line (the seven places lie within INSIDE x 350 = 157 of it: all at least LANE_CLEAR from the line)
PARK_REACH = 900.0      # ... and within this of the van's boarding box at the stop
PARK_NEAR = 3.0         # GUESS: weight of the distance to the boarding box against the length of the walk there
LOOT_LINK = 900.0       # loot objects nearer than this to one another are one loot area
LOOT_SNAP = 400.0       # a loot object farther than this from the START row's mesh part is not a bot's business
LOOT_MAX = 38           # most objects a stock TriggerLootDepleted names (F08)
GUARD_NEAR = 2500.0     # --wait-guards: Enemy actor groups within this of the loot place

SYSTEM_LEVELS = ('F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09')

# ---- the owner's round on the four maps, 2026-10-10 (re/bots.md 12): several loot stops, cases opened, a way over
STOP_SHARE = 0.10       # GUESS: a loot area is a stop of its own when it holds at least this share of the richest one
STOP_MAX = 4            # GUESS: at most this many stops (M06 has four people with money along one path)
CASE_BOTS = 3           # each case is opened by the three bots whose loot places are nearest to it (two may die)
CASE_DELAY = 1.0        # GUESS, seconds: the cases go this long after the bot finished the step BEFORE its loot place
DROP_COST = 1.0         # link cost = the distance x this (stock: 0.58 .. 1.01 of the distance, re/bots.md 12.3)
DROP_IN = 1.0           # a new waypoint lies this far inside its polygon from the border edge (stock: on the edge)
DROP_MAX = (240.0, 160.0)   # widest and highest drop this module writes: stock links reach 228 across; up to 160
                            # down the AI plays /Movement/Fall/Fall_1m, beyond it Fall_2m (kl2 0x4a52f6)

# The level exit boxes a map's rich loot stands in, cut back so that the loot is outside them and the boarding
# action still inside one. {map: {top-level node: (x from, x to)}}: the box keeps y, z and its other two sizes.
# M01 (measured, re/bots.md 12.2): CallExitVehicle_01 is x -8..3192 and holds FBI-Agents_01 (400,000) at x 3007 and
# BossFlank_02 at x 2791; CallExitVehicle_02 is x 3196..8796 and holds The_Senator (1,250,000) at x 3384, BossFlank_03
# at x 3290 and the diner's back door (LeavingHeist_01, x 4121). Nothing in kl2.exe gates the call (0x6cd8e0: any
# living crew member, bot or human, vehicle state 0) and no stock level gates the trigger by data (nine of nine: the
# box is shown, nobody names it) - so the only gate a level file has is the box itself. After the cut the yard
# between x 2400 and x 4600 (the Senator and his three men, both back doors) calls nothing; the car is called by
# whoever walks on toward its stop (boarding action at x 5884) or west along the back lot.
EXIT_CUT = {'M01_FA_A': {'Triggers!CallExitVehicle_01': (-8.0, 2400.0), 'Triggers!CallExitVehicle_02': (4600.0, 8796.0)}}

# A drop for the AI where a Dog Days player walks down but the navigation mesh has a gap. {map: [dict]}:
# at = a point between the two mesh borders (x, z); needs = (node name, 'its y is below this') - the object that
# must be out of the way, else nothing is written. The two waypoints are put on the border edges nearest to `at`,
# on the START row's part and on the part of the boarding action.
# M03 (re/escape.md, re/bots.md 12.3): kl_escape.open_wall sank SO0101_M03_Wall_Low_8m_05 (x -1900..-1100) to yard
# height; a dumpster stands on the street side of its east third (x -1454..-1200), x -1900..-1457 is free. The
# yard's mesh ends on the edge (-3645, 220, -693)..(-704, 220, -802) of polygon 527, the street's on z -535 between
# x -2559 and x -1487 (polygon 687, y 150): 70 down, about 230 across at x -1700.
DROPS = {'M03_FA_A': [{'at': (-1700.0, -650.0), 'needs': ('SO0101_M03_Wall_Low_8m_05', -100.0)}]}

# What the four maps are built with for the owner (python kl_fa_bots.py owner ...; re/bots.md 12). Every key is
# an option of build; the defaults (DEFAULTS) are the squad as it was before 2026-10-10 evening.
RECIPE = {'M01_FA_A': {'stops': STOP_MAX, 'cases': 'glass', 'exit_boxes': 'cut', 'loot_seconds': 30, 'lane': True},
          'M02_FA_A': {'stops': STOP_MAX, 'cases': 'glass', 'loot_seconds': 45, 'lane': True},
          'M03_FA_A': {'stops': STOP_MAX, 'cases': 'glass', 'drop': True, 'lane': True},
          'M06_FA_A': {'stops': STOP_MAX, 'cases': 'glass'}}


# ------------------------------------------------------------------ small things
def u32(t):
    return struct.unpack('<I', t[1])[0]


def rot9(dx, dz):
    """ZGEOM[1] of an object whose local +Z looks along (dx, dz): rows are local Z, Y, X in world space
    (kl_maps.world's reading; identity = 0 0 1 / 0 1 0 / 1 0 0; kl_fa_author's rot9, seen live on the START rows)."""
    n = math.hypot(dx, dz) or 1.0
    dx, dz = dx / n, dz / n
    return [dx, 0.0, dz, 0.0, 1.0, 0.0, dz, 0.0, -dx]


def frames(scene):
    """{entity: (R, T)}: world = T + R . local, composed down the tree exactly as kl_maps.world does."""
    out = {}
    def go(e, R, T):
        r = struct.unpack('<9f', e.rot[:36]); t = struct.unpack('<3f', e.trans[:12])
        m = [r[6:9], r[3:6], r[0:3]]
        m = [[m[j][i] for j in range(3)] for i in range(3)]
        p = tuple(T[i] + sum(R[i][j] * t[j] for j in range(3)) for i in range(3))
        R2 = [[sum(R[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        out[e] = (R2, p)
        for c in e.kids:
            go(c, R2, p)
    for e in scene.roots:
        go(e, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], (0.0, 0.0, 0.0))
    return out


def sizes(folder, slot=SLOT):
    """The four blocks a level reads in one piece: {'.prm': bytes, '.ANM', '.fxc', '.WAV'}."""
    with zipfile.ZipFile(os.path.join(folder, slot + '_Main.zip')) as z:
        out = collections.OrderedDict((e, next(i.file_size for i in z.infolist() if i.filename.endswith('_Main' + e))) for e in BIG)
    out['.WAV'] = os.path.getsize(os.path.join(folder, slot + '_Main.WAV'))
    return out


# ------------------------------------------------------------------ a built level
class Built:
    """A build folder read whole: members, property tree (kl_prpjoin.Scene), scene (kl_scene.Scene), frames."""

    def __init__(self, src, slot=SLOT):
        self.folder = src if os.path.isdir(src) else os.path.dirname(src)
        self.zp = os.path.join(src, slot + '_Main.zip') if os.path.isdir(src) else src
        with zipfile.ZipFile(self.zp) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
        raw, buf = kl_gms.unpack(self['.gms']), self['.buf']
        names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
        for decl, tid, _prio in kl_gms.entities(raw):
            o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        self.sc = J.Scene(Prp(self['.prp']), names, tids, 'dd', os.path.basename(self.zp))
        self.scene = kl_scene.Scene(raw, buf)
        self.ents = list(self.scene.entities())
        if [e.name.decode('latin1') for e in self.ents] != names[1:]:
            raise ValueError('%s: .gms and .prp disagree on the entities' % self.zp)
        self.fr = frames(self.scene)
        rj = os.path.join(self.folder, 'result.json')
        self.result = json.load(open(rj)) if os.path.isfile(rj) else {}

    def __getitem__(self, ext):
        return self.files[self.ext[ext]]

    def at(self, k):
        return self.fr[self.ents[k - 1]][1]

    def local(self, k, p):
        """World point p in node k's own frame."""
        Rm, T = self.fr[self.ents[k - 1]]
        d = [p[i] - T[i] for i in range(3)]
        return tuple(sum(Rm[i][j] * d[i] for i in range(3)) for j in range(3))

    def world(self, k, q):
        Rm, T = self.fr[self.ents[k - 1]]
        return tuple(T[i] + sum(Rm[i][j] * q[j] for j in range(3)) for i in range(3))

    def values(self, k):
        return dict(zip(J.labels('dd', self.sc.cls(k)), kl_fa.node_values(self.sc, k)))

    def box(self, k):
        """Size values of a ZBoxPrimitive node (its own frame)."""
        v = self.values(k)
        return tuple(v['ZBoxPrimitive[%d]' % i] for i in range(3))

    def in_box(self, k, p, share=1.0, size=None):
        s, q = size or self.box(k), self.local(k, p)
        return all(abs(q[i]) <= s[i] * share + 1e-3 for i in range(3))


# ------------------------------------------------------------------ the navigation mesh
class Nav:
    """A Dog Days-form mesh block as polygons (vertices x, y, z), the neighbour across each edge, connected parts,
    and the edges without a neighbour ('walls'). Edge k of a polygon runs from its vertex k to vertex k + 1: with
    that reading the neighbour named by an edge shares both ends of it (selftest(): 100 % on the four maps; the
    other reading, k - 1 -> k, 0 %). A neighbour < -1 is -2 - polygon (kl_pf4: an edge into another area); it is
    walked like any other, as kl_maps.NavParts does. Links (array 7: ladders, vaults) are not walked: the four maps
    have none after kl_pf4's conversion."""

    def __init__(self, block, links=False):
        _n, A = kl_pf4.split(block, True)
        polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        edges = [struct.unpack('<iII', r) for r in A[9]]
        verts = [struct.unpack('<5f', r) for r in A[6]]
        self.links = len(A[7])
        # links=True: the array-7 links are walked too, ONE WAY, from their waypoint to the target waypoint (stock
        # Dog Days: 192 links in 12 levels, all of kind 2 = a drop: the target is 44..523 lower in 182, level in 10,
        # never higher; no link has a reverse). self.drops[polygon] = [(target polygon, from, to, kind)].
        # Off by default: Retomoto's mesh keeps five of Dead Men's kind-2 links and its plans were made without them.
        self.drops = collections.defaultdict(list)
        if links:
            ways = [struct.unpack('<3fIIIHH', r) for r in A[5]]
            ars = [struct.unpack('<12I', r[:48]) for r in A[4]]
            for w in ways:
                for li in range(w[3], w[4]):
                    _cost, _junk, num, area, kind, _head, _switch = struct.unpack('<hHiiBBH', A[7][li])
                    t = ways[ars[area][5] + num]
                    self.drops[w[5]].append((t[5], (w[0], w[2], w[1]), (t[0], t[2], t[1]), kind))
        self.pv, self.en = [], []
        for p in polys:
            es = range(p[5], p[5] + p[0])
            self.pv.append([(verts[edges[e][1]][0], verts[edges[e][1]][2], verts[edges[e][1]][1]) for e in es])
            nb = []
            for e in es:
                j = edges[e][0]
                j = -2 - j if j < -1 else j
                nb.append(j if 0 <= j < len(polys) else -1)
            self.en.append(nb)
        n = len(self.pv)
        self.ok = [len(vs) >= 3 for vs in self.pv]
        self.box = [(min(v[0] for v in vs), max(v[0] for v in vs), min(v[2] for v in vs), max(v[2] for v in vs)) if vs else (0, 0, 0, 0) for vs in self.pv]
        self.mid = [tuple(sum(v[a] for v in vs) / len(vs) for a in range(3)) if vs else (0, 0, 0) for vs in self.pv]
        self.nb = [set() for _ in range(n)]
        for i in range(n):
            for j in self.en[i]:
                if j >= 0 and j != i:
                    self.nb[i].add(j); self.nb[j].add(i)
        # connected parts. A link joins two parts for this labelling (a drop is one way: path() knows that)
        both = [set(x) for x in self.nb]
        for i, ds in self.drops.items():
            for j, _a, _b, _k in ds:
                both[i].add(j); both[j].add(i)
        self.part, k = [-1] * n, 0
        for s in range(n):
            if self.part[s] >= 0:
                continue
            self.part[s], st = k, [s]
            while st:
                for j in both[st.pop()]:
                    if self.part[j] < 0:
                        self.part[j] = k; st.append(j)
            k += 1
        self.part_size = collections.Counter(self.part)
        # walls: edges without a neighbour (x0, z0, x1, z1, y)
        self.walls = []
        for i, vs in enumerate(self.pv):
            for e, j in enumerate(self.en[i]):
                if j < 0:
                    a, b = vs[e], vs[(e + 1) % len(vs)]
                    self.walls.append((a[0], a[2], b[0], b[2], (a[1] + b[1]) / 2))
        self._plane = [self._fit(vs) for vs in self.pv]

    @staticmethod
    def _fit(vs):
        """(a, b, c) with y = a x + b z + c through the polygon (first three vertices that span an area)."""
        for i in range(len(vs) - 2):
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = vs[0], vs[i + 1], vs[i + 2]
            d = (x1 - x0) * (z2 - z0) - (x2 - x0) * (z1 - z0)
            if abs(d) > 1e-3:
                a = ((y1 - y0) * (z2 - z0) - (y2 - y0) * (z1 - z0)) / d
                b = ((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)) / d
                return a, b, y0 - a * x0 - b * z0
        return 0.0, 0.0, sum(v[1] for v in vs) / max(1, len(vs))

    def selftest(self):
        """(edges with a neighbour, of them the neighbour has both ends of the edge)."""
        n = good = 0
        for i, vs in enumerate(self.pv):
            for e, j in enumerate(self.en[i]):
                if j < 0:
                    continue
                n += 1
                a, b = vs[e], vs[(e + 1) % len(vs)]
                near = lambda p: any(math.dist(p, q) < 1.0 for q in self.pv[j])
                good += near(a) and near(b)
        return n, good

    def height(self, i, x, z):
        a, b, c = self._plane[i]
        return a * x + b * z + c

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

    def at(self, x, y, z, dy=DY, part=None, lo=None, hi=None):
        """(polygon, its height at the point) under (x, z) whose height is nearest to y and within dy of it (or
        within lo..hi when given), of `part` only when given; None when the point is off the mesh."""
        best = None
        for i, b in enumerate(self.box):
            if self.ok[i] and b[0] <= x <= b[1] and b[2] <= z <= b[3] and (part is None or self.part[i] == part) and self.inside(i, x, z):
                h = self.height(i, x, z)
                if (lo is None and abs(h - y) <= dy) or (lo is not None and lo <= h <= hi):
                    if best is None or abs(h - y) < abs(best[1] - y):
                        best = (i, h)
        return best

    def clearance(self, x, y, z, limit=400.0):
        """Distance in the plan to the nearest wall edge at about this height (limit when none is nearer)."""
        best = limit
        for x0, z0, x1, z1, wy in self.walls:
            if abs(wy - y) > 150.0 or min(x0, x1) - best > x or max(x0, x1) + best < x or min(z0, z1) - best > z or max(z0, z1) + best < z:
                continue
            dx, dz = x1 - x0, z1 - z0
            L = dx * dx + dz * dz
            t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((x - x0) * dx + (z - z0) * dz) / L))
            best = min(best, math.hypot(x - x0 - t * dx, z - z0 - t * dz))
        return best

    def nearest(self, p, part):
        """Polygon of `part` whose middle is nearest to p."""
        return min((i for i in range(len(self.pv)) if self.ok[i] and self.part[i] == part), key=lambda i: math.dist(self.mid[i], p))

    def dist_map(self, i0, p0, ban=()):
        """Dijkstra over the polygons from point p0 on polygon i0, through the middles of the shared edges:
        ({polygon: distance to the portal it was entered by}, {polygon: (previous polygon, portal point)}).
        Polygons in `ban` are not entered (the start polygon may be one: it is left)."""
        dist, prev, at = {i0: 0.0}, {}, {i0: p0}
        pq = [(0.0, i0)]
        while pq:
            d, i = heapq.heappop(pq)
            if d > dist.get(i, 1e30):
                continue
            for j in self.nb[i]:
                if j in ban:
                    continue
                q = self.portal(i, j)
                nd = d + math.dist(at[i], q)
                if nd < dist.get(j, 1e30):
                    dist[j], prev[j], at[j] = nd, (i, q), q
                    heapq.heappush(pq, (nd, j))
            for j, pa, pb, _kind in self.drops.get(i, ()):          # a link: walk to its waypoint, land on the target's
                if j in ban:
                    continue
                nd = d + math.dist(at[i], pa) + math.dist(pa, pb)
                if nd < dist.get(j, 1e30):
                    dist[j], prev[j], at[j] = nd, (i, pb, pa), pb
                    heapq.heappush(pq, (nd, j))
        return dist, prev, at

    def portal(self, i, j):
        """Middle of the edge polygons i and j share."""
        for a, b in ((i, j), (j, i)):
            vs = self.pv[a]
            for e, n in enumerate(self.en[a]):
                if n == b:
                    p, q = vs[e], vs[(e + 1) % len(vs)]
                    return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2)
        return self.mid[j]

    def path(self, a, b, ban=()):
        """a, b = (x, y, z, polygon) -> (points from a to b through the portals, length) or None; `ban` as dist_map."""
        dist, prev, _at = self.dist_map(a[3], a[:3], ban)
        if b[3] not in dist:
            return None
        pts, i = [b[:3]], b[3]
        while i != a[3]:
            step = prev[i]
            i = step[0]
            pts += step[1:]                             # (portal,) or, for a link, (landing point, take-off point)
        pts.append(a[:3]); pts.reverse()
        return pts, sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))

    def spots(self, cands, n, sep, ref=None, clear=CLEAR):
        """Up to n of the candidate places [(x, y, z, polygon)], nearest to `ref` first (default: the first
        candidate), each with `clear` to the walls and `sep` from the ones already taken. When fewer than n have
        the clearance the best of the rest are taken (never below CLEAR_MIN)."""
        if not cands:
            return []
        ref = ref or cands[0]
        scored = sorted(((math.dist(c[:3], ref[:3]), self.clearance(c[0], c[1], c[2]), c) for c in cands), key=lambda s: s[0])
        out = []
        for need in (clear, (clear + CLEAR_MIN) / 2, CLEAR_MIN):
            for _d, cl, c in scored:
                if len(out) >= n:
                    return out
                if cl >= need and all(math.hypot(c[0] - o[0], c[2] - o[2]) >= sep for o in out):
                    out.append(c)
        return out

    def around(self, p, radius, part, step=40.0, dy=DY):
        """Candidate places on `part` within `radius` of p (a grid of `step`), each (x, y, z, polygon)."""
        out, k = [], int(radius // step)
        for ix in range(-k, k + 1):
            for iz in range(-k, k + 1):
                x, z = p[0] + ix * step, p[2] + iz * step
                if math.hypot(ix, iz) * step > radius:
                    continue
                hit = self.at(x, p[1], z, dy, part)
                if hit:
                    out.append((x, hit[1], z, hit[0]))
        return out


# ------------------------------------------------------------------ a link in the mesh (the bank's yard wall)
def border_points(nav, x, z, reach=600.0):
    """The border edges (no neighbour) within `reach` of (x, z) in the plan -> [(distance, part, polygon, point on
    the edge nearest to (x, z), the same point moved DROP_IN into the polygon)], nearest first, one per part."""
    best = {}
    for i, vs in enumerate(nav.pv):
        if not nav.ok[i]:
            continue
        for e, j in enumerate(nav.en[i]):
            if j >= 0:
                continue
            a, b = vs[e], vs[(e + 1) % len(vs)]
            dx, dz = b[0] - a[0], b[2] - a[2]
            L = dx * dx + dz * dz
            t = 0.0 if L < 1e-9 else max(0.02, min(0.98, ((x - a[0]) * dx + (z - a[2]) * dz) / L))
            p = (a[0] + t * dx, a[1] + t * (b[1] - a[1]), a[2] + t * dz)
            d = math.hypot(p[0] - x, p[2] - z)
            if d > reach or (nav.part[i] in best and best[nav.part[i]][0] <= d):
                continue
            m = nav.mid[i]                              # inward = toward the polygon's middle, across the edge
            nx, nz = -dz, dx
            if (m[0] - p[0]) * nx + (m[2] - p[2]) * nz < 0:
                nx, nz = -nx, -nz
            n = math.hypot(nx, nz) or 1.0
            q = (p[0] + nx / n * DROP_IN, p[1], p[2] + nz / n * DROP_IN)
            if not nav.inside(i, q[0], q[2]):
                q = p
            best[nav.part[i]] = (d, nav.part[i], i, p, (q[0], nav.height(i, q[0], q[2]), q[2]))
    return sorted(best.values())


def add_drop(block, frm, to, kind=2):
    """A Dog Days mesh block with ONE more link: two new waypoints, frm = (x, y, z, polygon) -> to, and one array-7
    record of `kind` (2 = the only kind stock Dog Days levels have: a drop). Everything that numbers waypoints is
    renumbered: 'waypoints before' of the later polygons, the area's count and the later areas' first waypoint,
    array 10, the link ranges of every waypoint, the targets of existing links. kl_pf4.check and kl_maps.nav_facts
    (the rules all 21 stock meshes obey) must hold on the result, else ValueError.
    Read, kl2 0x5cdd70 (the path search): a waypoint is a search node; its links lead to waypoint
    area[5] + number of the link's area at the link's cost (s16), unless the link's switch (u16, -1 = none) is
    blocked; the kind goes into the path node. 0x4a5160 (ZFFSpecialLink@Locomotion, the mover): kind 2 starts
    within 20 of the link's start and plays /Movement/Fall/Fall_1m, or Fall_2m when the two ends differ by more
    than 160 in height (table 0x15489e8, filled at 0x579920; both clips are in Kane_NPC / Lynch_NPC of every
    build). Kind 1 would be a climb UP (/Movement/Climb/Up/Low, Medium, High at 120 / 170) - Dog Days' animation
    files have no such clip, which is why this module writes drops only.
    A new waypoint may only go onto a polygon that has none: array 10 orders the waypoints of one polygon by a
    rule that was not established."""
    n, A = kl_pf4.split(block, True)
    A = [list(a) for a in A]
    polys = [list(struct.unpack('<BBHIIIIIII', r)) for r in A[3]]
    areas = [list(struct.unpack('<12I', r[:48])) for r in A[4]]
    ways = [list(struct.unpack('<3fIIIHH', r)) for r in A[5]]
    links = [list(struct.unpack('<hHiiBBH', r)) for r in A[7]]
    perm = [struct.unpack('<I', r)[0] for r in A[10]]
    tgt = [areas[l[3]][5] + l[2] for l in links]
    own = [wi for wi, w in enumerate(ways) for _ in range(w[3], w[4])]
    if len(own) != len(links):
        raise ValueError('the waypoints own %d links, array 7 has %d' % (len(own), len(links)))

    def put(p):
        poly = p[3]
        if any(w[5] == poly for w in ways):
            raise ValueError('polygon %d already has a waypoint: where a second one goes in array 10 is not established' % poly)
        i = polys[poly][6]
        ways.insert(i, [p[0], p[2], p[1], 0, 0, poly, 0, 0])            # stored x, z, y (as array 6)
        perm[:] = [v + (v >= i) for v in perm]
        perm.insert(i, i)
        tgt[:] = [v + (v >= i) for v in tgt]
        own[:] = [v + (v >= i) for v in own]
        for q in polys[poly + 1:]:
            q[6] += 1
        a = polys[poly][4]
        areas[a][0] += 1
        for b in areas[a + 1:]:
            b[5] += 1
        return i

    ia = put(frm)
    ib = put(to)
    if ib <= ia:
        ia += 1
    cost = max(1, min(32767, int(round(math.dist(frm[:3], to[:3]) * DROP_COST))))
    links.append([cost, 0, 0, 0, kind, 0, 0xffff])                      # heading byte 0: 48 of the 192 stock links; no reader found
    tgt.append(ib); own.append(ia)
    order = sorted(range(len(links)), key=lambda k: (own[k], k))
    at, out7 = 0, []
    for wi, w in enumerate(ways):
        mine = [k for k in order if own[k] == wi]
        w[3] = at
        for k in mine:
            l = links[k]
            ta = polys[ways[tgt[k]][5]][4]
            out7.append(struct.pack('<hHiiBBH', l[0], l[1], tgt[k] - areas[ta][5], ta, l[4], l[5], l[6]))
        at += len(mine)
        w[4] = at
    A[3] = [struct.pack('<BBHIIIIIII', *p) for p in polys]
    A[4] = [struct.pack('<12I', *a) + r[48:] for a, r in zip(areas, A[4])]
    A[5] = [struct.pack('<3fIIIHH', *w) for w in ways]
    A[7] = out7
    A[10] = [struct.pack('<I', v) for v in perm]
    data = kl_pf4.join(A)
    kl_pf4.check(data, kl_pf4.DD_LINK_KINDS)
    import kl_maps
    bad = {k: v for k, v in kl_maps.nav_facts(data).items() if v[0] != v[1]}
    if bad:
        raise ValueError('the mesh with the link breaks %s' % bad)
    return data, {'from_waypoint': ia, 'to_waypoint': ib, 'cost': cost, 'kind': kind}


def _roundtrip(B):
    """The build must come back byte for byte through the writers before anything of it is changed."""
    g0, b0 = B.scene.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    B.verified = True


def prepare(B, opt=None, log=print):
    """The edits of EXISTING level data a recipe asks for, made on the loaded build B (in memory) BEFORE the plan,
    so that the plan walks the level as it will be: the cut level exit boxes (EXIT_CUT, option exit_boxes = 'cut')
    and the drop link in the navigation mesh (DROPS, option drop). -> {'boxes': {...}, 'drops': [...]} for
    bots.json; diff() allows exactly these. Nothing is added or removed here: two fields of a trigger box
    (ZGEOM[2].x, ZBoxPrimitive[0]) with its .gms place, and three arrays of the mesh block."""
    opt = dict(DEFAULTS, **(opt or {}))
    out = collections.OrderedDict(boxes=collections.OrderedDict(), drops=[])
    if not getattr(B, 'verified', False):
        _roundtrip(B)
    sc, level = B.sc, B.result.get('M')
    if opt['exit_boxes'] == 'cut':
        for nm, (lo, hi) in EXIT_CUT.get(level, {}).items():
            hit = sc.resolve(R_ + nm)
            if len(hit) != 1 or sc.parent[hit[0]] != 0 or not kl_fa.has(sc, hit[0], 'OnlineExitLevelTrigger') or sc.cls(hit[0]) != 'ZBoxPrimitive':
                raise ValueError('%s: no top-level ZBoxPrimitive with an OnlineExitLevelTrigger' % nm)
            k = hit[0]
            Rm, T = B.fr[B.ents[k - 1]]
            s = B.box(k)
            if abs(abs(Rm[0][0]) - 1.0) > 0.01:
                raise ValueError('%s: its first size does not run along x' % nm)
            old = (T[0] - s[0], T[0] + s[0])
            if lo < old[0] - 1.0 or hi > old[1] + 1.0:
                raise ValueError('%s: %s is not inside the box as it is (%d..%d): a cut only' % (nm, (lo, hi), *old))
            lab = J.labels('dd', sc.cls(k))
            new_x, new_h = (lo + hi) / 2.0, (hi - lo) / 2.0
            def fn(us, new_x=new_x, new_h=new_h):
                i = lab.index('ZGEOM[2]')
                _x, y, z = (struct.unpack('<f', t[1])[0] for t in us[i][1:-1])
                us[i] = [us[i][0]] + [(0x0a, struct.pack('<f', v)) for v in (new_x, y, z)] + [us[i][-1]]
                us[lab.index('ZBoxPrimitive[0]')] = [(0x0a, struct.pack('<f', new_h))]
            kl_fa.edit(sc, k, None, fn)
            e = B.ents[k - 1]
            _x, y, z = struct.unpack_from('<3f', e.trans, 0)
            e.trans = struct.pack('<3f', new_x, y, z) + e.trans[12:]
            out['boxes'][nm] = {'x_was': [round(v) for v in old], 'x_is': [lo, hi]}
            log('level exit box %s: x %d..%d -> %d..%d (EXIT_CUT: the loot that stood in it is outside it now)' % (nm, *old, lo, hi))
        B.fr = frames(B.scene)
    if opt['drop']:
        for d in DROPS.get(level, []):
            nm, below = d['needs']
            hit = [k for k in range(1, len(sc.nodes)) if sc.names[k] == nm]
            if len(hit) != 1 or B.at(hit[0])[1] > below:
                log('  NOTE drop at %s NOT written: %s is not out of the way (kl_escape.open_wall sinks it)' % (d['at'], nm))
                continue
            nav = Nav(B.scene.nav)
            ends = border_points(nav, *d['at'])
            if len(ends) < 2:
                raise ValueError('drop at %s: the mesh has no two parts within reach' % (d['at'],))
            a, b = ends[0], ends[1]
            if a[4][1] < b[4][1]:
                a, b = b, a                                             # from the higher border to the lower one
            frm, to = a[4] + (a[2],), b[4] + (b[2],)
            across, down = math.hypot(frm[0] - to[0], frm[2] - to[2]), frm[1] - to[1]
            if across > DROP_MAX[0] or not 0.0 <= down <= DROP_MAX[1]:
                raise ValueError('drop at %s: %d across and %d down (stock links: up to 228 across; limits %s)' % (d['at'], across, down, DROP_MAX))
            B.scene.nav, info = add_drop(B.scene.nav, frm, to)
            info.update(at=list(d['at']), frm=[round(v, 1) for v in frm[:3]], to=[round(v, 1) for v in to[:3]], polygons=[frm[3], to[3]],
                        across=round(across), down=round(down), parts_joined=[nav.part_size[a[1]], nav.part_size[b[1]]],
                        clip='/Movement/Fall/Fall_1m' if down <= 160.0 else '/Movement/Fall/Fall_2m')
            out['drops'].append(info)
            log('navigation mesh: a drop link (kind 2) from (%d, %d, %d) on polygon %d to (%d, %d, %d) on polygon %d: %d across, %d down, cost %d; '
                'it joins the parts of %d and %d polygons, one way' % (*frm[:3], frm[3], *to[:3], to[3], across, down, info['cost'],
                                                                         nav.part_size[a[1]], nav.part_size[b[1]]))
    return out


def van_drives(B):
    """The key-framed escape vans of a build (OnlineEscAnimatedVehicle: stock F07's van as tools/kl_map_escape.py
    lays it on a Dead Men road, Retomoto's three) -> [dict], world space:
      line   the van's position keys from the first frame of its drive in to the last of its drive away, in order
             (field 1 / 2 of the controller name the two MatPosAnimProxy pieces on the node of field 11; the keys
             are decoded by kl_map_escape.VanKeys and stand in the frame of the van's parent)
      wait / stop / end   the key of frame 0, of the last frame of the drive in, of the last of the drive away
      board  where the van's boarding box (field 0, a child of the van) stands while the van is at the stop. IN THE
             FILE that box lies at the WAITING place, with the van - stations() reads the file
      seconds  (drive in, wait at the stop, drive away) = (frames / 25, field 15, frames / 25)
    A van whose pieces cannot be read is left out (the build is then planned as before 2026-10-10 night)."""
    sc, out = B.sc, []
    vans = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle')
    if not vans:
        return out
    import kl_graft
    import kl_map_escape as E
    ends = None
    for k, _i, v in vans:
        try:
            box, proxy, van = (sc.resolve(v[i])[0] for i in (0, 11, 12))
            legs = E._leg_frames(sc, proxy)
            (f0, f1), (g0, g1) = legs[v[1]], legs[v[2]]
            if ends is None:
                ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
            K = E.VanKeys(B.scene.head, B.ents[van - 1].raw, ends, kl_graft.keys_tracks)
        except (IndexError, KeyError, TypeError, ValueError, StopIteration):
            continue
        par = sc.parent[van]
        w = (lambda p: B.world(par, p)) if par > 0 else (lambda p: tuple(p))
        idx = list(dict.fromkeys(K.f2p[f] for f in range(f0, g1 + 1)))
        stop = w(K.pos[K.f2p[f1]])
        h = math.radians(K.yaw(K.rot[K.f2r[f1]]))
        back = -struct.unpack_from('<3f', B.ents[box - 1].trans, 0)[2] if sc.parent[box] == van else 0.0
        out.append({'node': k, 'name': sc.path[k][5:], 'line': [w(K.pos[i]) for i in idx],
                    'wait': w(K.pos[K.f2p[0]]), 'stop': stop, 'end': w(K.pos[K.f2p[g1]]),
                    'board': (stop[0] - back * math.sin(h), stop[1] - 2.0, stop[2] - back * math.cos(h)),
                    'heading': math.degrees(h), 'seconds': ((f1 - f0) / 25.0, v[15], (g1 - g0) / 25.0)})
    return out


def lanes(B):
    """The road of the map's escape vehicle in world space -> [[(x, y, z), ...]].
    A spline CAR (OnlineEscHavokCar over a ZHavokCar; incoming, escaping and the stretch between): the
    ZEditorSpline below each of fields 0 and 1 (12 bytes of header, then 24 bytes a point: x, y, z
    in the spline node's frame, an angle, 10.0, four unset bytes - tools/kl_map_escape.spline). A helicopter's
    routes are left out (nobody stands in its way).
    A key-framed VAN (OnlineEscAnimatedVehicle; re/play_fixes_review.md D3): the polyline of its position keys from
    the first frame of the drive in to the last of the drive away (van_drives). Until 2026-10-10 night a baked van
    gave no lane, and the bots of a van build were placed ON its drive with every checker passing."""
    sc, out = B.sc, [d['line'] for d in van_drives(B) if len(d['line']) > 1]
    for k, _i, v in kl_fa.controllers(sc, 'OnlineEscHavokCar'):
        if not any(sc.cls(j) == 'ZHavokCar' for j in range(k, sc.end[k])):
            continue
        mine = []
        for s in v[:2]:
            for h in (sc.resolve(s) if isinstance(s, str) and s else []):
                for j in range(h, sc.end[h]):
                    if sc.cls(j) != 'ZEditorSpline':
                        continue
                    raw = B.values(j)['ZEditorSpline[0]']
                    n = struct.unpack_from('<I', raw, 4)[0]
                    if 12 + 24 * n <= len(raw) and n > 1:
                        mine.append([B.world(j, struct.unpack_from('<3f', raw, 12 + 24 * i)) for i in range(n)])
        if len(mine) == 2:                              # from where it stops to where the drive away begins: its road too
            mine.append([mine[0][-1], mine[1][0]])
        out += mine
    return out


def _crosses(lane, u, w, dy=400.0):
    """Does the walk u -> w cross one of the lines `lane` in the plan (segments within dy of u's height)?"""
    o = lambda a, b, c: (b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0])
    for pts in lane:
        for a, b in zip(pts, pts[1:]):
            if min(abs(a[1] - u[1]), abs(b[1] - u[1])) > dy:
                continue
            if o(a, b, u) * o(a, b, w) < 0 and o(u, w, a) * o(u, w, b) < 0:
                return True
    return False


def lane_dist(lane, p, dy=400.0):
    """Least distance in the plan from p to the routes `lane` (segments within dy of p's height)."""
    best = 1e9
    for pts in lane:
        for a, b in zip(pts, pts[1:]):
            if min(abs(a[1] - p[1]), abs(b[1] - p[1])) > dy:
                continue
            dx, dz = b[0] - a[0], b[2] - a[2]
            L = dx * dx + dz * dz
            t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / L))
            best = min(best, math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz))
    return best


# ------------------------------------------------------------------ what the map offers
def stations(B, nav):
    """The round's places on a built map -> dict (everything in world space):
    starts [(place, forward)], home = the mesh part of the START row, triggers {'ENTERS' | 'EXITS' | 'BOARDS':
    [node]}, exits [node] (OnlineExitLevelTrigger), action = the node with PlayerAction 'EnterVehicle',
    vehicle (controller name, node, class of the vehicle), loot [(node, place, amount)], guards [(group node, place)],
    heroes {N: (model, ZLNKOBJ[1], ZLNKWHANDS[5])}, monitor = the AIMonitor node."""
    sc, st = B.sc, {'starts': [], 'triggers': collections.defaultdict(list), 'exits': [], 'action': None, 'vehicle': None,
                    'loot': [], 'guards': [], 'heroes': {}, 'monitor': None, 'notes': []}
    for k in range(1, len(sc.nodes)):
        cls = sc.cls(k)
        if cls == 'ZSpawnPoint':
            v = kl_fa.node_values(sc, k)
            if any(isinstance(x, str) and x == kl_fa.START for x in v):
                Rm = B.fr[B.ents[k - 1]][0]
                st['starts'].append((B.at(k), (Rm[0][2], Rm[2][2])))        # local +Z in the plan
        elif cls == 'ZFFActor':
            v = B.values(k)
            if v['ZFFActor[0]'] == 'Enemy' and sc.cls(sc.parent[k]) == 'ZGROUP':
                st['guards'].append((sc.parent[k], B.at(k)))
        elif cls == 'ZFFPlayer' and sc.names[sc.top[k]].startswith('Heroes!Hero_0') and sc.names[k] == 'Ground':
            v = B.values(k)
            st['heroes'][int(sc.names[sc.top[k]][13:14])] = (v['ZGEOM[4]'], v['ZLNKOBJ[1]'], v['ZLNKWHANDS[5]'])
    for k, _i, v in kl_fa.controllers(sc, 'OnlineGamePlayTrigger'):
        kind = next((x for x in v if isinstance(x, str) and x.startswith('eOGPT_PLAYER_')), '?')
        st['triggers'][kind[13:].replace('_BANK', '')].append(k)
    st['exits'] = [k for k, _i, _v in kl_fa.controllers(sc, 'OnlineExitLevelTrigger')]
    acts = [k for k, _i, v in kl_fa.controllers(sc, 'PlayerAction') if 'EnterVehicle' in v]
    st['action'] = acts[0] if acts else None
    for name in kl_fa.VEHICLES:
        for k, _i, v in kl_fa.controllers(sc, name):
            kind = next((sc.cls(j) for j in range(k, sc.end[k]) if sc.cls(j) in ('ZHavokCar', 'ZHeli', 'ZAnimatedVehicle')), sc.cls(k))
            st['vehicle'] = st['vehicle'] or (name, k, kind)
            if name == 'OnlineEscHavokCar' and len(v) > 2 and isinstance(v[2], str) and sc.resolve(v[2]):
                st['action'] = sc.resolve(v[2])[0]                          # the box the rules take: member +0x38 (kl2 0x8faebc)
    mons = [k for k, _i, _v in kl_fa.controllers(sc, 'AIMonitor')]
    st['monitor'] = next((k for k in mons if sc.names[k] == 'Gameplay!AIMonitor'), mons[0] if mons else None)
    if not st['starts']:
        raise ValueError('no %s spawn point' % kl_fa.START)
    mid = tuple(sum(p[0][i] for p in st['starts']) / len(st['starts']) for i in range(3))
    # the START points float about 100 above the floor (re/bots_squad.md 6): look for the floor below them
    parts = collections.Counter()
    for p, _f in st['starts']:
        hit = nav.at(p[0], p[1], p[2], lo=p[1] - 260.0, hi=p[1] + 40.0)
        if hit:
            parts[nav.part[hit[0]]] += 1
    if not parts:
        raise ValueError('no START point stands over the navigation mesh')
    st['home'] = parts.most_common(1)[0][0]
    st['start_mid'] = mid
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if any(isinstance(x, str) and 'DROP' in x for x in v):
            continue                                                        # the stacks a player drops: a pool, not loot
        amount = v[1] if len(v) > 1 and isinstance(v[1], (int, float)) else 0
        st['loot'].append((k, B.at(k), amount))
    return st


def box_places(B, nav, k, part, share=INSIDE, size=None, centre=None):
    """Places on `part` INSIDE box node k (or a box of `size` round `centre`, axis aligned): a grid in the box's own
    frame over its two horizontal axes, each point dropped onto the polygon under it whose height lies in the
    box's height range (a little below it too: a trigger box floats, a person's node is at his feet)."""
    s = size or B.box(k)
    def grid(step):
        def ax(a):
            if a * share < 20:
                return [0.0]
            m = max(2, int(2 * a * share // step))
            return [a * share * (2.0 * i / m - 1.0) for i in range(m + 1)]
        out = []
        for u in ax(s[0]):
            for w in ax(s[2]):
                p = B.world(k, (u, 0.0, w)) if centre is None else (centre[0] + u, centre[1], centre[2] + w)
                hit = nav.at(p[0], p[1], p[2], part=part, lo=p[1] - s[1] - 60.0, hi=p[1] + s[1])
                if hit:
                    out.append((p[0], hit[1], p[2], hit[0]))
        return out
    out = grid(40.0)
    if len(out) < 12 and max(s[0], s[2]) * share <= 1000:   # a box across a doorway: the mesh is a strip there, look closer
        out = grid(8.0)
    return out


CHEST = 90.0            # a walker is tested against a trigger box at his feet and this far above them


def in_exit(B, exits, p):
    """The OnlineExitLevelTrigger boxes of `exits` a walker standing at p is inside (feet or chest)."""
    return [k for k in exits if B.in_box(k, p) or B.in_box(k, (p[0], p[1] + CHEST, p[2]))]


def first_exit_entry(B, nav, exits, pts, dy=260.0):
    """Walk the shortest mesh path through the places `pts` in order (this module's stand-in for the game's
    pathfinder) and return where it FIRST is inside a level exit box: (path length up to there, index of the
    place it was walking to, the box node), or None. Sampled every 20 units."""
    run = 0.0
    for si in range(len(pts) - 1):
        a, c = pts[si], pts[si + 1]
        ha, hc = nav.at(a[0], a[1], a[2], dy=dy), nav.at(c[0], c[1], c[2], dy=dy)
        got = ha and hc and nav.path(tuple(a[:3]) + (ha[0],), tuple(c[:3]) + (hc[0],))
        poly = got[0] if got else [tuple(a[:3]), tuple(c[:3])]         # off the mesh: the straight line
        for p, q in zip(poly, poly[1:]):
            d = math.dist(p, q)
            n = max(1, int(d // 20))
            for t in range(n + 1):
                m = tuple(p[i] + (q[i] - p[i]) * t / n for i in range(3))
                hit = in_exit(B, exits, m)
                if hit:
                    return run + d * t / n, si + 1, hit[0]
            run += d
    return None


def plan(B, opt=None, log=print):
    """-> the plan (dict) for a squad on build B, or raises ValueError saying what the map lacks.
    plan['stations'] = the stations in order (what each one is, the seven places); plan['steps'] = the route steps as
    lists of station numbers; plan['bots'][N] = {'start', 'face', 'places': one per station, 'model', 'snd'};
    plan['loot'] / ['guards'] = scene paths for the waits; plan['ally_at'] = None or the AllyEscapeBox's place;
    plan['notes'] = what is not as stock."""
    opt = dict(DEFAULTS, **(opt or {}))
    nav = Nav(B.scene.nav, links=bool(opt['drop']))
    S = stations(B, nav)
    sc, home, notes = B.sc, None, []
    home = S['home']
    name = lambda k: sc.path[k][5:]
    n_e, good = nav.selftest()
    P = collections.OrderedDict(folder=B.folder, map=B.result.get('M'), systems=B.result.get('S'), options=opt,
                                mesh={'polygons': len(nav.pv), 'parts': len(nav.part_size), 'home_part_polygons': nav.part_size[home],
                                      'links': nav.links, 'edges_with_neighbour': n_e, 'neighbour_shares_the_edge': good})
    log('navigation mesh: %d polygons in %d parts; the START row is on a part of %d; %d of %d neighbour edges are shared edges'
        % (len(nav.pv), len(nav.part_size), nav.part_size[home], good, n_e))

    def on(p, lo=260.0, hi=60.0):
        hit = nav.at(p[0], p[1], p[2], part=home, lo=p[1] - lo, hi=p[1] + hi)
        return hit and (p[0], hit[1], p[2], hit[0])

    def snap(p, radius=LOOT_SNAP):
        """A place on the home part at p, else the nearest within radius (with clearance), else None."""
        c = nav.around(p, radius, home, dy=260.0)
        got = nav.spots(c, 1, 0.0, ref=p)
        return got[0] if got else None

    # ---- where the bots stand
    sm = S['start_mid']
    floor = [on(p) for p, _f in S['starts']]
    floor = [f for f in floor if f]
    fy = sum(f[1] for f in floor) / len(floor)
    fwd = (sum(f[0] for _p, f in S['starts']), sum(f[1] for _p, f in S['starts']))
    cands = [c for c in nav.around((sm[0], fy, sm[2]), START_FAR + 300.0, home)
             if START_NEAR <= min(math.hypot(c[0] - p[0], c[2] - p[2]) for p, _f in S['starts']) <= START_FAR]
    stand = nav.spots(cands, 7, SEP + 20.0, ref=(sm[0], fy, sm[2]))
    if len(stand) < 7:
        raise ValueError('only %d places for the seven bots near the START row' % len(stand))
    a0 = min(floor, key=lambda f: math.dist(f[:3], (sm[0], fy, sm[2])))

    # ---- the boarding place
    act = S['action']
    if act is None:
        raise ValueError('no boarding action (PlayerAction EnterVehicle)')
    ap = B.at(act)
    # a key-framed van (tools/kl_map_escape.py van): its boarding box rides on the van, so in the FILE it lies at the
    # waiting place (M01: 49 m from the stop, outside the level bound). The round's boarding place is the box's place
    # while the van STANDS AT THE STOP - on the van's own line, 337 behind its origin, where its nose passes on the
    # way in. So the bots do not end there (re/play_fixes_review.md D3) but in an AllyEscapeBox PARK_SIDE to the side.
    van = van_drives(B) if S['vehicle'] and S['vehicle'][0] == 'OnlineEscAnimatedVehicle' else []
    van = van[0] if len(van) == 1 else None             # (Retomoto's three vans are kl_fa_bots_rt's: planned as before)
    park_c = []
    if van:
        ap = van['board']
        P['van'] = {k: ([round(x, 1) for x in van[k]] if k != 'seconds' else list(van[k])) for k in ('wait', 'stop', 'end', 'board', 'seconds')}
        P['van']['keys_on_the_line'] = len(van['line'])
        log('escape van %s: waits (%d, %d, %d), stops (%d, %d, %d) after %.2f s, stands %.1f s, ends (%d, %d, %d) after %.2f s; its boarding box at the '
            'stop: (%d, %d, %d) (in the file it lies at the waiting place)' % (van['name'].split('\\')[-1], *van['wait'], *van['stop'], van['seconds'][0],
                                                                              van['seconds'][1], *van['end'], van['seconds'][2], *ap))
    park0 = on(ap, lo=B.box(act)[1] + 200.0, hi=B.box(act)[1])
    split = park0 is None
    if split:
        other = nav.at(ap[0], ap[1], ap[2], lo=ap[1] - B.box(act)[1] - 200.0, hi=ap[1] + B.box(act)[1])
        i = min((i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == home), key=lambda i: math.hypot(nav.mid[i][0] - ap[0], nav.mid[i][2] - ap[2]))
        park0 = snap(nav.mid[i], 300.0) or (nav.mid[i] + (i,))
        notes.append('SPLIT MESH: the boarding action %s at (%d, %d, %d) is %s; the START row\'s part ends %d from it at (%d, %d, %d). '
                     'A bot cannot path to the vehicle (ZBoardEscapeVehicleTactic\'s path test fails): the bots end on their side'
                     % (name(act), *ap, 'on another part of %d polygons' % nav.part_size[nav.part[other[0]]] if other else 'off the mesh',
                        math.hypot(park0[0] - ap[0], park0[2] - ap[2]), *park0[:3]))
    if opt.get('park'):
        s = snap(tuple(opt['park']), 400.0)
        if s is None:
            raise ValueError('--park %s: no place on the mesh part of the START row within 400 of it' % (opt['park'],))
        park0, split = s, True
        notes.append('--park: the bots end at (%d, %d, %d), %d from the boarding action in the plan and %d below / above it, in an AllyEscapeBox'
                     % (*park0[:3], math.hypot(park0[0] - ap[0], park0[2] - ap[2]), park0[1] - ap[1]))
    elif van:
        # every place beside the van's rear at the stop; the one of them the bots end at is chosen when the last
        # loot stop is known (below: the side they come from)
        park_c = [x for x in nav.around(ap, PARK_REACH, home, dy=260.0)
                  if lane_dist([van['line']], x) >= PARK_SIDE and nav.clearance(*x[:3]) >= CLEAR]
        if not park_c:
            raise ValueError('no place on the mesh part of the START row within %d of the van\'s boarding box at the stop (%d, %d, %d) that is %d '
                             'from the van\'s line: give --park x,y,z' % (PARK_REACH, *ap, PARK_SIDE))
        park0, split = min(park_c, key=lambda x: math.dist(x[:3], ap)), True
    heli = S['vehicle'] and S['vehicle'][2] == 'ZHeli'
    ally = {'on': True, 'off': False}.get(opt['ally_box'], bool(split or heli))
    if split and not ally:
        notes.append('--ally-box off on a split mesh: NO BOT CAN BOARD')

    # ---- loot: the area with the most money that the home part reaches
    loot = []
    for k, p, amount in S['loot']:
        s = snap(p)
        if s and math.hypot(s[0] - p[0], s[2] - p[2]) <= LOOT_SNAP:
            loot.append((k, p, amount, s))
    P['loot_objects'] = {'all': len(S['loot']), 'reachable': len(loot)}
    # ---- THE LEVEL EXIT BOXES CALL THE VEHICLE FOR A BOT TOO (found 2026-10-10, runs BOT1 / BOT2 on M01: the round
    # ended 152..156 s after GO whatever the loot wait was). Read: ZOnlineExitLevelTrigger slot 34 (0x6c3d50) hands
    # ANY activator to the rules' slot 44 (ZGameRulesHeist 0x6cd8e0), which takes a player OR an actor that has a
    # crew record (0x78f470) and, with the vehicle in state 0, calls it (0x8154f0). On M01 the diner's door
    # (EXITS_BANK LeavingHeist_01) and both rich loot people stand INSIDE the two CallExitVehicle boxes, and the
    # route 'way out before the loot' walked every bot into one 139..144 m after the start.
    # So, unless --early-call: the way to the loot, the loot place and every place before the loot wait stay out
    # of every polygon a level exit box touches; loot that can only be had inside a box is left to the tactic.
    exits = S['exits']
    calls = lambda p: in_exit(B, exits, p)
    ban = set()
    if exits and not opt['early_call'] and not opt['no_stage']:
        for k in exits:
            ban.update(c[3] for c in box_places(B, nav, k, home, share=1.0))
        ban.update(i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == home and any(calls(v) for v in nav.pv[i] + [nav.mid[i]]))
        free = nav.dist_map(a0[3], a0[:3], ban)[0]
        clean = lambda s: s[3] not in ban and s[3] in free and not calls(s)
        boxed = [x for x in loot if not (clean(x[3]) and not calls(x[1]))]
        if boxed and len(boxed) < len(loot):
            notes.append('%d loot object(s) worth %d stand INSIDE a level exit box (%s): a bot that walks there calls the escape vehicle '
                         '(kl2 0x6cd8e0), so the route does not go there; the bots\' own loot tactic may still (not established)'
                         % (len(boxed), sum(x[2] for x in boxed), ', '.join('%s %d' % (name(x[0]).split('\\')[-1], x[2]) for x in boxed[:4])))
            loot = [x for x in loot if x not in boxed]
        elif boxed:
            notes.append('CALLS EARLY: every loot object in reach stands inside a level exit box; the route is planned as with --early-call')
            ban = set()
    P['exit_boxes'] = {'nodes': [name(k) for k in exits], 'polygons_kept_clear_before_the_loot': len(ban)}
    okp = lambda c: not ban or (c[3] not in ban and not calls(c))
    areas, left = [], list(loot)
    while left:
        area, grow = [left.pop(0)], True
        while grow:
            grow = [x for x in left if any(math.dist(x[1], y[1]) <= LOOT_LINK for y in area)]
            area += grow
            left = [x for x in left if x not in grow]
        areas.append(area)
    areas.sort(key=lambda a: (-sum(x[2] for x in a), -len(a)))
    worth = lambda a: sum(x[2] for x in a)
    # ---- the loot STOPS (option stops; 1 = the richest area only, as every build before 2026-10-10 evening):
    # every area with at least STOP_SHARE of the richest one, each with a wait of its own. A stop = the area's
    # objects, the richest first; its place = the mesh place at that object.
    stops = []
    if areas:
        more = [a for a in areas[1:] if worth(a) >= STOP_SHARE * worth(areas[0])][:max(0, int(opt['stops']) - 1)]
        stops = [sorted(a, key=lambda x: (-x[2], x[0])) for a in areas[:1] + more]
        area, la = stops[0], stops[0][0][3]
        log('loot: %d objects (not DROP), %d within %d of the START row\'s mesh part, in %d areas; the richest: %d objects, %d (field 1 added up) round (%d, %d, %d)'
            % (len(S['loot']), len(loot), LOOT_SNAP, len(areas), len(area), sum(x[2] for x in area), *la[:3]))
        if int(opt['stops']) > 1:
            for a in areas[1:]:
                log('      another area: %d objects, %d, round (%d, %d, %d): %s' % (len(a), worth(a), *a[0][3][:3],
                    'a stop' if any(a[0] in s for s in stops) else 'no stop (under %d %% of the richest, or more than %d stops)' % (100 * STOP_SHARE, int(opt['stops']))))
    else:
        area = []
        notes.append('NO LOOT OBJECT within %d of the START row\'s mesh part: the loot wait is a plain TriggerDelay2 and the route turns '
                     'at the ENTERS_BANK trigger' % LOOT_SNAP)

    # ---- the trigger boxes a bot has to walk through for its stage (0x5dd890)
    def best_box(nodes, frm, to, what):
        """(node, its places on the home part, the one on the shortest way frm -> to) of the best of `nodes`."""
        df = nav.dist_map(frm[3], frm[:3])[0]
        dt = nav.dist_map(to[3], to[:3])[0] if to else {}
        best = None
        for k in nodes:
            c = box_places(B, nav, k, home)
            c = [x for x in c if x[3] in df]
            if not c:
                notes.append('%s %s at (%d, %d, %d): no place inside it on the START row\'s mesh part' % (what, name(k), *B.at(k)))
                continue
            cost = lambda x: df[x[3]] + math.dist(x[:3], nav.mid[x[3]]) + (dt.get(x[3], 0.0) if to else 0.0)
            least = min(cost(x) for x in c)
            x = max((x for x in c if cost(x) <= least + 120.0), key=lambda x: nav.clearance(*x[:3]))    # the middle of a doorway
            if best is None or least < best[3]:
                best = (k, c, x, least)
        return best and best[:3]

    target = la if area else None
    enter = None
    if not opt['no_stage']:
        enter = best_box(S['triggers'].get('ENTERS', []), a0, target, 'ENTERS_BANK')
        if not enter:
            notes.append('NO ENTERS_BANK trigger on the route: the bots get no stage 1 and ZLootTactic never runs (kl2 0x451920 needs stage >= 1)')
    e_item = enter and ('enter', 'ENTERS_BANK %s (stage 1)' % name(enter[0]), enter[2], enter[0], enter[1])
    head = [('start', 'the START row', a0, None, None)] + ([e_item] if e_item else [])
    if len(stops) > 1:
        # the order of the stops: the nearest next, from the ENTERS_BANK place on (a bot loots from stage 1 on only)
        cur, rest, order = head[-1][2], list(stops), []
        while rest:
            def far(s, cur=cur):
                got = nav.path(cur, s[0][3], ban)
                return got[1] if got else 1e30
            nxt_ = min(rest, key=far)
            rest.remove(nxt_); order.append(nxt_); cur = nxt_[0][3]
        stops = order
        area, la = stops[0], stops[0][0][3]
    one = len(stops) == 1
    l_items = [('loot', 'the loot (%d objects)' % len(a) if one else 'loot stop %d: %d objects, %d (%s)' % (
                    n + 1, len(a), worth(a), ', '.join(name(x[0]).split('\\')[-1] for x in a[:3]) + (' ..' if len(a) > 3 else '')),
                a[0][3], None, None) for n, a in enumerate(stops)]
    last = (l_items or head)[-1][2]                     # where the way out begins
    if park_c:
        # the van's park place: beside its boarding box, on the side the bots come from (path from the last loot stop
        # + PARK_NEAR x the distance to the box: a place across the van's line costs the way round its rear or nose,
        # a place up the road costs its distance from the doors)
        dm = nav.dist_map(last[3], last[:3])[0]
        cc = [x for x in park_c if x[3] in dm]
        if not cc:
            raise ValueError('no park place beside the van can be reached from the last loot stop: give --park x,y,z')
        park0 = min(cc, key=lambda x: dm[x[3]] + math.dist(x[:3], nav.mid[x[3]]) + PARK_NEAR * math.hypot(x[0] - ap[0], x[2] - ap[2]))
        notes.append('KEY-FRAMED VAN: the bots end at (%d, %d, %d), %d to the side of the van\'s line and %d from its boarding box at the stop '
                     '(%d, %d, %d), in an AllyEscapeBox: they are taken aboard from there when the van stands (kl2 0x907a50), they do not walk '
                     'to its doors' % (*park0[:3], lane_dist([van['line']], park0), math.hypot(park0[0] - ap[0], park0[2] - ap[2]), *ap))

    def tail(pos):
        """The EXITS_BANK station put after `pos` of the stops (0 = before the first: a map whose loot lies beyond
        its doors, M01's senator) and the level exit station -> (exit item or None, level item or None, notes)."""
        mute = len(notes)
        lev = best_box(S['exits'], last, park0, 'level exit') or best_box(S['triggers'].get('BOARDS', []), last, park0, 'BOARDS')
        after = (l_items[pos - 1] if pos else head[-1])[2]
        to = l_items[pos][2] if pos < len(l_items) else (lev[2] if lev else park0)
        out_ = best_box(S['triggers'].get('EXITS', []), after, to, 'EXITS_BANK')
        said = notes[mute:]
        del notes[mute:]
        x = out_ and ('exit', 'EXITS_BANK %s (stage 2)' % name(out_[0]), out_[2], out_[0], out_[1])
        v = lev and ('level', '%s %s (stage 3%s)' % ('level exit' if lev[0] in S['exits'] else 'BOARDS', name(lev[0]),
                                                      '; it calls the vehicle as a player enters it - ASSUMPTION' if lev[0] in S['exits'] else ''),
                     lev[2], lev[0], lev[1])
        return x, v, said

    def length(seq):
        n = 0.0
        for a, b in zip(seq, seq[1:]):
            got = nav.path(a[2], b[2])
            if got is None:
                return 1e30
            n += got[1]
        return n

    park = ('park', '', park0, None, None)

    def pre_ok(q):
        """Do the stations of q up to and including the LAST loot stop lie outside the level exit boxes, with a way
        between them that stays outside? (No loot station: there is nothing to wait for, any order is as good.)"""
        idx = max([i for i, it in enumerate(q) if it[0] == 'loot'], default=None)
        if not ban or idx is None:
            return True
        return all(okp(b[2]) and nav.path(a[2], b[2], ban) is not None for a, b in zip(q[:idx], q[1:idx + 1]))

    if opt['no_stage']:
        seq = head + l_items
    else:
        seqs = []
        for pos in range(len(l_items), -1, -1):         # the way out after the last stop first: it wins a tie
            x, v, said = tail(pos)
            if x or pos == len(l_items):
                seqs.append((head + l_items[:pos] + ([x] if x else []) + l_items[pos:] + ([v] if v else []), said))
        lens = [length(q + [park]) for q, _s in seqs]
        good = [i for i, (q, _s) in enumerate(seqs) if pre_ok(q)]
        if not good:
            notes.append('CALLS EARLY: no order of the stations keeps the way to the loot out of the level exit boxes; the shortest is taken '
                         'and a bot calls the escape vehicle on its way IN')
            ban = set()
        pick = min(good or range(len(seqs)), key=lambda i: lens[i])
        seq, said = seqs[pick]
        if len(seqs) > 1 and one:
            log('route order: loot before the way out = %d of path, the way out before the loot = %d: %s' % (
                *(round(x) for x in lens), 'the shorter is taken' if lens[pick] == min(lens) else
                'the LONGER is taken - on the shorter one the bots walk into a level exit box before the loot'))
        elif len(seqs) > 1:
            log('route order: the way out (EXITS_BANK) after stop %s = %s of path: %s' % (
                ' / '.join(str(sum(1 for it in q[:[i[0] for i in q].index('exit')] if it[0] == 'loot') if any(i[0] == 'exit' for i in q) else '-')
                           for q, _s in seqs), ' / '.join('%d' % round(x) for x in lens),
                'the shortest is taken' if lens[pick] == min(lens) else
                'a LONGER one is taken - on the shortest the bots walk into a level exit box before their last loot stop'))
        notes += list(dict.fromkeys(said))
        if not any(i[0] == 'exit' for i in seq):
            notes.append('no EXITS_BANK trigger on the route (stage 2 is skipped; stage 3 does not need it: 0x5dd890 only raises)')
        if not any(i[0] == 'level' for i in seq):
            notes.append('NO level exit or BOARDS trigger on the START row\'s mesh part: the bots never reach stage 3, so they do not board '
                         'through the tactic (0x4faf60) and the stage term of the traitor rule stays at 2%s' % ('' if ally else ' - AND THERE IS NO AllyEscapeBox: THEY DO NOT BOARD'))
            ally = ally or opt['ally_box'] == 'auto'
    P['ally_box'] = bool(ally)
    seq.append(('park', 'the boarding place%s' % (' (inside the AllyEscapeBox)' if ally else ' (%d..%d from the boarding action)' % PARK), park0, None, None))

    # ---- the anchors' path, the stations between them, seven places per station
    route, total, gates = [], 0.0, []
    # option lane: on the way out (after the last loot wait) nobody is sent to stand in the escape car's road
    # (a key-framed van: always. It drives through whatever stands on its line; a spline car at least was a physics body)
    lane = lanes(B) if opt['lane'] or van else []
    off = lambda c: lane_dist(lane, c) >= LANE_CLEAR
    if lane:
        log('escape %s: %d route(s), %d points; the places of the way out keep %d from them where the mesh allows' % (
            'van' if van else 'car', len(lane), sum(len(x) for x in lane), LANE_CLEAR))
    hops = {(tuple(pa), tuple(pb)) for ds in nav.drops.values() for _j, pa, pb, _k in ds}
    i_loot = max([i for i, it in enumerate(seq) if it[0] == 'loot'], default=None)
    for leg, ((ka, _wa, a, _na, _ca), (kb, wb, b, nb_, cb)) in enumerate(zip(seq, seq[1:])):
        pre = bool(ban) and i_loot is not None and leg < i_loot          # this leg ends at or before the last loot stop
        got = nav.path(a, b, ban if pre else ())
        if got is None:
            raise ValueError('no path on the mesh from %s to %s' % (ka, kb))
        pts, length = got
        total += length
        run, nxt = 0.0, SPACING
        for p, q in zip(pts, pts[1:]):
            d = math.dist(p, q)
            if (tuple(p), tuple(q)) in hops:
                # the way goes over a link here: the seven gather in front of it first (a step ends there, see
                # chunks), GATE_BACK inside their side of the mesh - inside an AllyEscapeBox, so that a bot the
                # link does not carry is still taken aboard from there, as on every build before the link
                u = math.dist(p, q) or 1.0
                g = snap(tuple(p[i] + (p[i] - q[i]) / u * GATE_BACK for i in range(3)), 260.0)
                if g:
                    route.append(('gate', 'in front of the drop at (%d, %d, %d): %d across, %d down' % (
                        *p, math.hypot(p[0] - q[0], p[2] - q[2]), p[1] - q[1]), g, None, None, length, pre))
                    gates.append(g)
                run += d
                nxt = max(nxt, run + 300.0)             # the next way place not nearer than 3 m beyond the landing
                continue
            while d > 0 and run + d >= nxt and length - nxt > SPACING * 0.5:
                t = (nxt - run) / d
                m = tuple(p[i] + (q[i] - p[i]) * t for i in range(3))
                s = None
                if pre:                             # a place beside the path, but not one in a level exit box
                    c = [x for x in nav.around(m, 260.0, home, dy=260.0) if okp(x)]
                    s = (nav.spots(c, 1, 0.0, ref=m) or [None])[0]
                elif lane and i_loot is not None and leg >= i_loot and not off(m):
                    # beside the road, and on the side they come from: a place across the road costs the way back
                    c = [x for x in nav.around(m, LANE_REACH, home, dy=260.0) if off(x)]
                    back = route[-1][2] if route else a
                    c = [x for x in c if not _crosses(lane, back, x)] or c     # not across the road when a place this side will do
                    c.sort(key=lambda x: math.dist(x[:3], m) + 0.5 * math.dist(x[:3], back[:3]))
                    s = (nav.spots(c[:60], 1, 0.0, ref=c[0]) or [None])[0] if c else None
                s = s or snap(m, 260.0)
                if s:
                    route.append(('way', 'on the way to %s' % kb, s, None, None, length, pre))
                nxt += SPACING
            run += d
        route.append((kb, wb, b, nb_, cb, length, pre))
    P['path_length'] = round(total)
    places, stop_no = [], 0                         # per station: (kind, what, [7 places])
    after_loot = not stops                          # the stations behind the last loot stop
    came = a0
    def near(c, anchor):
        """The place of c to gather round: the anchor - or, beside the car's road, the one of c that is nearest
        to the anchor without crossing over from where the bots come (`came`)."""
        if not (lane and after_loot) or not c:
            return anchor
        return min(c, key=lambda x: math.dist(x[:3], anchor[:3]) + 0.5 * math.dist(x[:3], came[:3]))
    for kind, what, anchor, node, cands, _len, pre in route:
        keep = (lambda c: [x for x in c if okp(x)] or c) if pre else (lambda c: c)
        if lane and after_loot and not pre:             # the way out: beside the car's road, and on the side they are on
            keep = lambda c, came=came: [x for x in c if off(x) and not _crosses(lane, came, x)] or [x for x in c if off(x)] or c
            if kind == 'level' and node is not None:
                # the whole box counts here, not its middle INSIDE share: the three size values ARE half extents
                # (run BOT1 / BOT2: M01's bots called the car at a door 7 inside the box's edge, re/bots.md 11),
                # and the middle of a level exit box is the car's road
                cands = box_places(B, nav, node, home, share=0.9) or cands
        if cands:
            cands = keep(cands)
        if kind == 'loot':
            got, used = [], []
            area = stops[stop_no]; stop_no += 1
            after_loot = stop_no >= len(stops)
            for b in range(7):                      # each bot beside 'its' loot object, the richest first
                k, p, _amount, s = area[b % len(area)]
                c = nav.spots(keep(nav.around(p, LOOT_SNAP, home, dy=260.0)), 1 + len(used), SEP, ref=s)
                c = [x for x in c if all(math.hypot(x[0] - u[0], x[2] - u[2]) >= SEP for u in used)] or c
                used.append(c[0]); got.append(c[0])
        elif kind == 'gate':
            c = box_places(B, nav, None, home, size=ALLY_SIZE, centre=(anchor[0], anchor[1] + ALLY_UP, anchor[2]))
            c = [x for x in c if abs(x[1] - anchor[1]) <= 30.0]             # their side of the drop only
            got = nav.spots(c, 7, 90.0, ref=anchor) or [anchor]
            if len(got) < 7:
                got = nav.spots(c, 7, 60.0, ref=anchor) or got
        elif kind == 'park':
            if ally:
                c = box_places(B, nav, None, home, size=ALLY_SIZE, centre=(anchor[0], anchor[1] + ALLY_UP, anchor[2]))
                if lane:                                # D3 b: the box may reach into the road, the seven places do not
                    if len([x for x in c if off(x)]) >= 7:
                        c = [x for x in c if off(x)]
                    else:
                        notes.append('the AllyEscapeBox: fewer than 7 places %d from the escape vehicle\'s line inside it; check() says which stand nearer' % LANE_CLEAR)
                got = nav.spots(c, 7, 90.0, ref=anchor) or [anchor]
                if len(got) < 7:
                    got = nav.spots(c, 7, 60.0, ref=anchor) or got
            else:
                c = [x for x in nav.around(anchor, PARK[1], home, dy=260.0) if PARK[0] <= math.hypot(x[0] - ap[0], x[2] - ap[2]) <= PARK[1]]
                if lane and len([x for x in c if off(x)]) >= 7:
                    c = [x for x in c if off(x)]        # beside the road, not in it: the car comes through here
                elif lane:
                    notes.append('the boarding place: fewer than 7 places %d from the car\'s route within %d..%d of the boarding action; the bots wait in the road' % ((LANE_CLEAR,) + PARK))
                got = nav.spots(c, 7, SEP, ref=near(c, anchor))
                if not got:
                    raise ValueError('no place %d..%d from the boarding action on the mesh' % PARK)
        elif cands:
            got = nav.spots(cands, 7, SEP, ref=near(cands, anchor)) or [anchor]
            if len(got) < 7:                        # a doorway: closer together rather than all on one spot
                got = nav.spots(cands, 7, 50.0, ref=near(cands, anchor)) or got
        else:
            got = nav.spots(keep(nav.around(anchor, 260.0, home)), 7, SEP, ref=anchor) or [anchor]
        came = got[0]
        places.append((kind, what, node, [got[b % len(got)] for b in range(7)], len(got)))
        log('  %-5s %-78s round (%6d %5d %6d): %d distinct places, clearance %d..%d' % (
            kind, what[:78], *anchor[:3], len(got), min(nav.clearance(*g[:3]) for g in got), max(nav.clearance(*g[:3]) for g in got)))
    P['stations'] = [{'kind': kind, 'what': what, 'node': name(node) if node else None, 'distinct_places': n,
                      'places': [[round(v, 1) for v in g[:3]] for g in got]} for kind, what, node, got, n in places]
    ally_at = None
    if ally:
        ally_at = (park0[0], park0[1] + ALLY_UP, park0[2])
        if split:
            notes.append('the AllyEscapeBox stands at (%d, %d, %d), %d from the boarding action: bots inside it board (kl2 0x907a50: no stage and no '
                         'path test) when the vehicle is in state 3 / 4 - they vanish there, they do not walk to the vehicle'
                         % (*ally_at, math.hypot(ally_at[0] - ap[0], ally_at[2] - ap[2])))
    if gates and not ally and opt['ally_box'] != 'off':
        ally_at = (gates[0][0], gates[0][1] + ALLY_UP, gates[0][2])
        notes.append('an AllyEscapeBox stands at the drop, round (%d, %d, %d): the fall-back if the AI does not take the link (kl2 0x907a50 boards a '
                     'bot inside it when the vehicle is in state 3 / 4); a bot that takes the link boards at the vehicle through the tactic' % ally_at)
    # D4 (re/play_fixes_review.md): the bots end in a box beyond a one-way drop (M03 with the van: the box beside
    # the van, on the street). If the AI does not take the hand-written link - never seen - seven bots would stand
    # in the yard for the rest of the round with nothing to take them aboard. So the gather place in front of EVERY
    # drop gets a box of its own as well (stock F02 / F06 have eight boxes each): both sides work.
    ally_more = []
    if ally and opt['ally_box'] != 'off':
        for g in gates:
            at = (g[0], g[1] + ALLY_UP, g[2])
            if ally_at and all(abs(at[i] - ally_at[i]) <= ALLY_SIZE[i] * INSIDE for i in range(3)):
                continue                                # the main box already holds the gather place
            ally_more.append(at)
            notes.append('a second AllyEscapeBox stands at the drop, round (%d, %d, %d): the drop is one way, and a bot the link does not carry '
                         'is taken aboard from the gather place there when the vehicle stands (kl2 0x907a50)' % at)
    P['gates'] = [[round(v, 1) for v in g[:3]] for g in gates]
    P['ally_at'] = ally_at and [round(v, 1) for v in ally_at]
    P['ally_more'] = [[round(v, 1) for v in a] for a in ally_more]
    # ---- the cases (option cases). A loot object of type CONTAINER cannot be taken before its OnlineMoneyContainer
    # was opened (kl2 0x766e50 -> after the container's own delay 0x868fb0 makes each object of its field 0 active;
    # an object that is not active ignores the take message, 0x6cdb8f). Stock containers are opened by their own
    # TriggerBox2 'Open' when somebody stands within 125..150 (117 of 117, F01 F03 F08); Dead Men's jewel and watch
    # cases have no such trigger: their glass (HavokShatterGlass + RelayMessage HavokShattered -> 'Open') has to be
    # SHOT, and no AI code shoots at an object. So a route step tells the case: 'Activate' to the glass (kl2
    # 0x471443 -> 0x8d1b60: the same two routines a bullet ends in, 0x67e6a0 + 0x79bd10) and 'Open' to the container
    # (0x41a01d: no activator needed; a second 'Open' is ignored, byte +0x4c).
    box_of, glass_of = collections.defaultdict(list), collections.defaultdict(list)
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyContainer'):
        for s in (v[0] if v and isinstance(v[0], list) else []):
            for j in sc.resolve(s):
                box_of[j].append(k)
    for k, _i, v in kl_fa.controllers(sc, 'RelayMessage'):
        if len(v) > 2 and v[0] == 'HavokShattered' and v[1] == 'Open' and kl_fa.has(sc, k, 'HavokShatterGlass'):
            for j in sc.resolve(v[2]):
                if kl_fa.has(sc, j, 'OnlineMoneyContainer'):
                    glass_of[j].append(k)
    loot_at = [i for i, x in enumerate(places) if x[0] == 'loot']
    waits = []
    for n, a in enumerate(stops):
        base = 10 + 20 * n
        w = collections.OrderedDict(name='%03d_Timer_done_looting' % (base + 10), stop=n, seconds=int(opt['loot_seconds']),
                                    loot=[R_ + name(x[0]) for x in a[:LOOT_MAX]], worth=worth(a), timer='%03d_Timer_at_cases' % (base + 8),
                                    relays=['%03d_Relay_break_glass' % (base + 8), '%03d_Relay_open_cases' % (base + 8)],
                                    cases=collections.OrderedDict())
        cs = list(dict.fromkeys(c for x in a[:LOOT_MAX] for c in box_of.get(x[0], [])))
        if opt['cases'] == 'glass':
            cs = [c for c in cs if glass_of.get(c)]
        elif opt['cases'] != 'all':
            cs = []
        if cs:
            spot = places[loot_at[n]][3]
            for c in cs:
                p = B.at(c)
                for b in sorted(range(7), key=lambda b: math.hypot(spot[b][0] - p[0], spot[b][2] - p[2]))[:CASE_BOTS]:
                    d = w['cases'].setdefault(BOTS[b], {'glass': [], 'open': []})
                    d['open'].append(R_ + name(c))
                    d['glass'] += [R_ + name(g) for g in glass_of.get(c, [])]
            w['containers'] = len(cs)
            w['glass'] = sum(len(glass_of.get(c, [])) for c in cs)
            log('  cases of stop %d: %d containers (%d behind glass, %d panes); each is opened by %d bots, %d .. %d containers a bot'
                % (n + 1, len(cs), sum(1 for c in cs if glass_of.get(c)), w['glass'], CASE_BOTS,
                   min([len(d['open']) for d in w['cases'].values()] + [0] * (7 - len(w['cases']))), max(len(d['open']) for d in w['cases'].values())))
        waits.append(w)
    if not waits:                                       # no loot in reach: one plain timer, as before
        waits.append(collections.OrderedDict(name='020_Timer_done_looting', stop=0, seconds=int(opt['loot_seconds']), loot=[], worth=0,
                                             timer='018_Timer_at_cases', relays=[], cases={}))
    P['waits'] = waits
    # ---- per bot
    # ---- steps: up to STEP_MAX places each; a step does not END in a doorway all seven share (they would hold there)
    def chunks(idx):
        out, chunk = [], []
        for i in idx:
            chunk.append(i)
            keep = []
            if len(chunk) == STEP_MAX and places[i][4] < 7 and i != idx[-1]:
                keep = [chunk.pop()]                    # the doorway opens the next step instead
            if i == idx[-1] or len(chunk) >= STEP_MAX or keep or places[i][0] == 'gate':
                out.append(chunk)
                chunk = keep
        return out
    bounds = loot_at or [next((i for i, x in enumerate(places) if x[0] == 'enter'), 0)]
    steps, start = [], 0
    for n, i in enumerate(bounds + [len(places) - 1]):
        out_leg = n == len(bounds)
        idx = list(range(start, i + 1))
        start = i + 1
        if not idx:
            continue
        if not out_leg and n < len(waits) and waits[n]['cases'] and len(idx) > 1:
            parts = chunks(idx[:-1]) + [[idx[-1]]]      # the loot place is a step of its own: the cases go before it
        else:
            parts = chunks(idx)
        for m, chunk in enumerate(parts):
            steps.append({'name': '%03d_DefendBehaviour_%s' % (10 + 20 * n + m, 'out' if out_leg else 'to_loot'),
                          'leg': 'out' if out_leg else 'in', 'stop': None if out_leg else n, 'stations': chunk})
    P['steps'] = steps
    P['bots'] = collections.OrderedDict()
    for b, N in enumerate(BOTS):
        if N not in S['heroes']:
            raise ValueError('no Heroes!Hero_0%d\\Ground in the build' % N)
        P['bots'][N] = {'start': [round(v, 1) for v in stand[b][:3]], 'face': [round(v, 3) for v in fwd],
                        'places': [[round(v, 1) for v in x[3][b][:3]] for x in places],
                        'model': S['heroes'][N][0], 'snd': list(S['heroes'][N][1:])}
    # ---- where each bot first is inside a level exit box (= where it calls the vehicle), walked as the check walks it
    i_wait = max([i for i, x in enumerate(places) if x[0] == 'loot'], default=None)
    P['vehicle_call'] = collections.OrderedDict()
    early = []
    for b, N in enumerate(BOTS):
        pts = [stand[b]] + [x[3][b] for x in places]
        hit = first_exit_entry(B, nav, exits, pts) if exits else None
        if hit:
            before = i_wait is not None and hit[1] - 1 <= i_wait
            P['vehicle_call'][N] = {'path': round(hit[0]), 'on_the_way_to_station': hit[1], 'box': name(hit[2]), 'before_the_loot_wait': before}
            if before:
                early.append(N)
    if P['vehicle_call']:
        v = list(P['vehicle_call'].values())
        log('level exit boxes (%s): a bot is first inside one after %d..%d of path, %s' % (
            ', '.join(P['exit_boxes']['nodes']), min(x['path'] for x in v), max(x['path'] for x in v),
            'BEFORE its loot wait (bots %s): THE VEHICLE IS CALLED ON THE WAY IN' % early if early else 'after its loot wait'))
    if early and not opt['early_call'] and not any(n.startswith('CALLS EARLY') for n in notes):
        notes.append('CALLS EARLY: bots %s cross a level exit box before the loot wait although the stations avoid it' % early)
    P['start_above_feet'] = [round(p[1] - fy) for p, _f in S['starts']]
    P['loot'] = list(waits[0]['loot'])                  # (the first stop's; every stop's list is in P['waits'])
    P['guards'] = []
    if opt['wait_guards'] and area:
        P['guards'] = sorted({R_ + name(k) for k, p in S['guards'] if math.dist(p, la[:3]) <= GUARD_NEAR})
        if not P['guards']:
            notes.append('--wait-guards: no Enemy actor group within %d of the loot; no TriggerActorsDead is made' % GUARD_NEAR)
    P['monitor'] = S['monitor'] and R_ + name(S['monitor'])
    if S['monitor'] is None:
        raise ValueError('no AIMonitor in the build: nothing would start the squad (kl_fa.host_keep keeps Gameplay!AIMonitor)')
    P['vehicle'] = S['vehicle'] and {'controller': S['vehicle'][0], 'node': name(S['vehicle'][1]), 'class': S['vehicle'][2]}
    P['action'] = {'node': name(act), 'at': [round(v) for v in ap], 'on_home_part': not split}
    P['notes'] = notes
    for n in notes:
        log('  NOTE ' + n)
    return P


DEFAULTS = {'ally_box': 'auto', 'wait_guards': False, 'loot_seconds': 20, 'start_delay': 10.0, 'heal': False, 'no_stage': False,
            'tree': True, 'park': None, 'early_call': False,
            'stops': 1, 'cases': 'off', 'exit_boxes': 'keep', 'drop': False, 'lane': False}    # 2026-10-10 evening; RECIPE turns them on per map


# ------------------------------------------------------------------ node forms from the stock levels
class _Keys:
    """The key table of the nodes being made (kl_prpjoin.join re-interns them into the level's)."""
    def __init__(self):
        self.keys, self.ix = [], {}

    def key_index(self, s):
        if s not in self.ix:
            self.ix[s] = len(self.keys); self.keys.append(s)
        return self.ix[s]

    def key(self, tok):
        return self.keys[u32(tok)]


class Node:
    """One new entity: its .prp side (props, ctrls: tokens in the maker's key table) and its .gms side."""
    def __init__(self, name, tid, props, ctrls, ent):
        self.name, self.tid, self.props, self.ctrls, self.kids = name, tid, props, ctrls, []
        self.flags, self.group, self.aux, self.rot, self.trans = ent.flags, ent.group, ent.aux, ent.rot, ent.trans
        self.links, self.model, self.pos = (None if ent.links is None else []), 0, None

    def add(self, kid):
        self.kids.append(kid)
        return kid

    def walk(self):
        yield self
        for k in self.kids:
            yield from k.walk()


class Maker:
    """Clones node forms out of stock levels and edits their fields."""
    _stock = {}

    def __init__(self):
        self.p = _Keys()

    @classmethod
    def level(cls, name):
        if name not in cls._stock:
            sc = J.Scene.load(name)
            with zipfile.ZipFile(J.level_zip(name)) as z:
                m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
                scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
            cls._stock[name] = (sc, list(scene.entities()))
        return cls._stock[name]

    def adopt(self, toks, keys):
        return J._intern(toks, keys, self.p.ix, self.p.keys)

    def clone(self, level, path, name=None):
        sc, ents = self.level(level)
        hit = sc.resolve(path) if isinstance(path, str) else [path]
        if len(hit) != 1:
            raise ValueError('%s: %d nodes at %s' % (level, len(hit), path))
        k = hit[0]
        n = sc.nodes[k]
        return Node(name or sc.names[k], sc.tids[k], self.adopt(n['props'], sc.p.keys),
                    [(self.adopt([nm], sc.p.keys)[0], self.adopt(body, sc.p.keys)) for nm, body in n['ctrls']], ents[k - 1])

    # -- field editing: a value replaces a unit keeping the unit's own token kinds
    def unit(self, old, v):
        op = old[0][0]
        if op == 0x0c:
            return [(0x0c, struct.pack('<I', self.p.key_index(v)))]
        if op == 0x0e:
            return [(0x0e, struct.pack('<I', self.p.key_index(v)))]
        if op == 0x0a:
            return [(0x0a, struct.pack('<f', v))]
        if op == 0x09:
            return [(0x09, struct.pack('<I', v))]
        if op in (0x05, 0x06, 0x07):
            return [(op, bytes([v]))]
        if op == 0x04:                                   # a reference list: count + strings
            return [(0x04, struct.pack('<I', len(v)))] + [(0x0c, struct.pack('<I', self.p.key_index(s))) for s in v]
        if op == 0x01:                                   # an array of floats
            if len(v) != u32(old[0]) or any(t[0] != 0x0a for t in old[1:-1]):
                raise ValueError('array of another shape')
            return [old[0]] + [(0x0a, struct.pack('<f', x)) for x in v] + [old[-1]]
        raise ValueError('field of token kind %#x' % op)

    def set(self, node, ctrl, fields):
        """fields {index or label: value} on the node itself (ctrl None; labels as kl_prpjoin.labels) or on its
        controller named `ctrl`."""
        if ctrl is None:
            obj, lab = node.props, J.labels('dd', J.schema('dd').geoms.get(node.tid))
        else:
            i = next(i for i, (nm, _b) in enumerate(node.ctrls) if self.p.key(nm) == ctrl)
            obj, lab = node.ctrls[i][1], None
        us = [list(u) for u in units(obj[1:-1])]
        for f, v in fields.items():
            j = lab.index(f) if isinstance(f, str) else f
            us[j] = self.unit(us[j], v)
        new = [obj[0]] + [t for u in us for t in u] + [obj[-1]]
        if ctrl is None:
            node.props = new
        else:
            node.ctrls[i] = (node.ctrls[i][0], new)

    def place(self, node, pos, rot=None):
        """World place of a node whose parents all stand at the origin unturned (every group made here does)."""
        ident = rot9(0.0, 1.0)
        node.pos = tuple(float(v) for v in pos)
        self.set(node, None, {'ZGEOM[2]': list(node.pos), 'ZGEOM[1]': rot or ident})
        node.trans = struct.pack('<3f', *node.pos) + node.trans[12:]
        node.rot = struct.pack('<9f', *(rot or ident)) + node.rot[36:]

    def scene(self, tops):
        """The made subtrees as a kl_prpjoin.Scene (for join) and the nodes in its order."""
        order, names, tids = [], ['ROOT'], [kl_rtp.ROOT_TYPE]
        def conv(n):
            order.append(n); names.append(n.name); tids.append(n.tid)
            return {'props': n.props, 'ctrls': n.ctrls, 'children': [conv(k) for k in n.kids]}
        prp = type('P', (), {})()
        prp.keys = self.p.keys
        prp.root = {'props': [], 'ctrls': [], 'children': [conv(t) for t in tops]}
        return J.Scene(prp, names, tids, 'dd', 'bots'), order


def make(B, P, log=print):
    """The plan as nodes -> (maker, [top-level Node]). Every form is a clone of a stock node; the fields set here are
    the ones the docstring names."""
    opt = P['options']
    S = P.get('systems') or 'F07'
    if S not in SYSTEM_LEVELS:
        S = 'F07'
    Sx = 'F07'                                          # the forms are F07's (the level re/bots_squad.md read in full)
    M = Maker()
    sq = lambda N, tail='': '%s%sSquad#0%d%s' % (R_, SQUAD, N, tail)
    tops, first = [], []
    for N in BOTS:
        b = P['bots'][N]
        top = M.clone(Sx, sq(N))
        M.place(top, (0.0, 0.0, 0.0))
        # ---- the actor
        grp = top.add(M.clone(Sx, sq(N, '\\' + GROUP_NAME % N)))
        M.place(grp, b['start'], rot9(*b['face']))
        act = grp.add(M.clone(Sx, sq(N, '\\' + GROUP_NAME % N + '\\Ground')))
        M.place(act, (0.0, 0.0, 0.0))
        act.model = b['model']
        M.set(act, None, {'ZGEOM[4]': b['model'], 'ZLNKOBJ[1]': b['snd'][0], 'ZLNKWHANDS[5]': b['snd'][1]})
        if opt['heal']:
            # ASSUMPTION (re/bots_behaviour.md 4.3 A): field 2 not eNever makes kl2 0x6ab6a2 build the bot's ZHealTactic
            M.set(act, 'ZSoldier', {2: 'eSometimes'})
        # ---- the route
        steps = [(st['name'], [b['places'][i] for i in st['stations']], st['leg'] == 'out', st['leg']) for st in P['steps']]
        # the chain: per loot stop its steps, [the cases timer before the stop's last step], [the guards' wait], the
        # loot wait; then the way out and the last modifier. One stop without cases = the chain as it always was
        # (010.. -> 020_Timer_done_looting -> 030.. -> 040_SquadModifier_tight_defense_van).
        plan_waits = P.get('waits') or [{'name': '020_Timer_done_looting', 'stop': 0, 'seconds': int(opt['loot_seconds']), 'loot': P['loot'], 'cases': {}}]
        waits, chain, fan = [], [], {}
        for w in plan_waits:
            names = [st['name'] for st in P['steps'] if st['leg'] == 'in' and st.get('stop', 0) == w['stop']]
            cs = w['cases'].get(N) or w['cases'].get(str(N))
            if cs and (cs['glass'] or cs['open']):
                # DefendBehaviourRout -> TriggerDelay2 -> DefendBehaviourRout are stock transitions (329 and 119 in
                # the nine stock squads); TriggerDelay2 -> a RelayMessageList is stock F02's (2). The timer stands
                # BEFORE the step that walks to the loot place, so that step ends in the loot wait as it always did.
                names.insert(max(0, len(names) - 1), w['timer'])
                relays = [(w['relays'][0], 'Activate', list(dict.fromkeys(cs['glass']))), (w['relays'][1], 'Open', list(dict.fromkeys(cs['open'])))]
                fan[w['timer']] = [r for r in relays if r[2]]
                waits.append((w['timer'], 'TriggerDelay2', {0: float(CASE_DELAY), 1: 0.0, 2: -1.0, 3: 0}, 4))
            if P['guards'] and w['stop'] == 0:
                names.append('015_TriggerActorsDead_Lootarea')
                waits.append(('015_TriggerActorsDead_Lootarea', 'TriggerActorsDead', {0: P['guards'], 1: 0}, 2))
            names.append(w['name'])
            if w['loot']:
                waits.append((w['name'], 'TriggerLootDepleted', {0: w['loot'], 1: int(w['seconds']), 2: 0, 3: 0}, 4))
            else:
                waits.append((w['name'], 'TriggerDelay2', {0: float(w['seconds']), 1: 0.0, 2: -1.0, 3: 0}, 4))
            chain += names
        last = '%03d_SquadModifier_tight_defense_van' % (20 + 20 * len(plan_waits))
        chain += [s[0] for s in steps if s[3] == 'out'] + [last]
        nxt = {a: [sq(N, '\\' + c)] for a, c in zip(chain, chain[1:])}
        for timer, relays in fan.items():               # the next link of the chain first (check() follows the first)
            nxt[timer] = nxt[timer] + [sq(N, '\\' + r[0]) for r in relays]
            for rname, msg, targets in relays:
                # stock F01's form: Gameplay!merc_bot_squad!KickdoorMonitor!KickDoor_RelayList_Door0n = ZBoxPrimitive +
                # RelayMessageList {'AITrigger' -> 'DoorOpened', 8 / 10 money cases, 0.0}; here the message is the
                # glass's 'Activate' or the container's 'Open'
                r = top.add(M.clone('F01', R_ + SQUAD + 'KickdoorMonitor!KickDoor_RelayList_Door08', rname))
                M.place(r, (0.0, 0.0, 0.0))
                M.set(r, 'RelayMessageList', {0: 'AITrigger', 1: msg, 2: targets, 3: 0.0})
        for nm, pl, sprint, _leg in steps:
            g = top.add(M.clone(Sx, sq(2, '\\020_DefendBehaviour_rout_merc_fight_left'), nm))
            M.place(g, (0.0, 0.0, 0.0))
            refs = []
            for j, p in enumerate(pl):
                box = g.add(M.clone(Sx, sq(2, '\\020_DefendBehaviour_rout_merc_fight_left\\Pos#01'), 'Pos#%02d' % (j + 1)))
                M.place(box, p)
                refs.append(sq(N, '\\%s\\Pos#%02d' % (nm, j + 1)))
            M.set(g, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_Sprint' if sprint else 'eDMS_NotSet', 5: 'eDF_NotSet',
                                             6: '', 7: nxt[nm], 8: 1, 9: 0})
        g = top.add(M.clone(Sx, sq(2, '\\100_SquadModifier_tight_defense_van'), chain[-1]))
        M.place(g, (0.0, 0.0, 0.0))
        M.set(g, 'SquadModifierBehaviour', {0: 'eLM_Leash', 9: 'eDM_Tight', 26: []})    # F01 F03 F04 F07's last step: leashed, tight
        src = {'TriggerActorsDead': '\\020_TriggerActorsDead_Lootarea', 'TriggerLootDepleted': '\\030_Timer_done_looting',
               'TriggerDelay2': None}
        for nm, ctrl, fields, f_next in waits:
            w = top.add(M.clone(Sx, sq(2, src[ctrl]), nm) if src[ctrl] else M.clone(Sx, R_ + SQUAD + 'Timer_start_bots', nm))
            M.place(w, (0.0, 0.0, 0.0))
            fields = dict(fields); fields[f_next] = nxt[nm]
            M.set(w, ctrl, fields)
        first.append(sq(N, '\\' + chain[0]))
        tops.append(top)
    t = M.clone(Sx, R_ + SQUAD + 'Timer_start_bots')
    M.place(t, (0.0, 0.0, 0.0))
    M.set(t, 'TriggerDelay2', {0: float(opt['start_delay']), 1: 0.0, 2: -1.0, 3: 0, 4: first})
    tops.append(t)
    # the boxes: the one the bots end in, then (D4) one at the gather place in front of each one-way drop
    for n, at in enumerate(([P['ally_at']] if P['ally_at'] else []) + list(P.get('ally_more') or [])):
        sc, _e = Maker.level('F02')
        k = kl_fa.controllers(sc, 'AllyEscapeBox')[0][0]
        a = M.clone('F02', k, SQUAD + 'AllyEscapeBox' + ('_%02d' % (n + 1) if n else ''))
        a.ctrls = [c for c in a.ctrls if M.p.key(c[0]) == 'AllyEscapeBox']     # F02's box is also the players' boarding action
        a.flags &= ~0x400                               # F02's is created hidden (flag 0x400, ZGEOM[3] = 1) and switched on by
        M.place(a, at)                                  # ActivateGeom when its helicopter comes. ASSUMPTION: a box that is
        M.set(a, None, {'ZGEOM[3]': 0, 'ZBoxPrimitive[0]': ALLY_SIZE[0], 'ZBoxPrimitive[1]': ALLY_SIZE[1], 'ZBoxPrimitive[2]': ALLY_SIZE[2]})
        tops.append(a)                                  # never hidden ticks from the start (0x907a50 has no flag of its own
    return M, tops                                      # and boards only in vehicle state 3 / 4: slot 45, 0x6840a0)


# ------------------------------------------------------------------ writing
def room_sets_check(scene, octx, rmi, rmc):
    """Every SLOT id of the room trees and of the room index against the scene -> list of faults.
    Tree 0 lists pool category 1, 1 lights, 3 groups, 4 rooms; a room index box names a room (kl_octree)."""
    slot = scene.slots()
    by = {s + 2: e for e, s in slot.items()}
    want = {0: (1,), 1: (2,), 2: (3,), 3: (0,), 4: (0,)}
    bad = collections.Counter()
    for room in octx.rooms:
        for ti, t in enumerate(room):
            for it in (t.items if t else ()):
                e = by.get(it[0])
                if e is None:
                    bad['tree %d: an id that is no entity' % ti] += 1
                elif kl_gms.category(e.tid) not in want[ti]:
                    bad['tree %d lists an entity of category %d' % (ti, kl_gms.category(e.tid))] += 1
    for nm, ix in (('.rmi', rmi), ('.rmc', rmc)):
        for b in ix.boxes:
            e = by.get(b.room)
            if e is None or kl_gms.category(e.tid) != 0:
                bad['%s: a box names an id that is no group-class entity' % nm] += 1
    return ['%s (x%d)' % kv for kv in bad.items()]


def apply(B, P, dst, log=print, more=None):
    """Write the plan into a copy of build B in folder dst -> report dict.
    more (kl_fa_bots_rt, a map of two navigation parts): an object with nodes(M, tops), called on the made squads
    before they are joined (it may add step nodes to them), and edit(Jn), called on the joined property tree after
    the AIMonitor edit (it may edit ONE existing node; diff(also=...) then has to be told its name)."""
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    sc = B.sc
    if any(sc.names[t].startswith(SQUAD) and 'Squad#' in sc.names[t] for t in sc.tops()):
        raise ValueError('the build already has a %sSquad' % SQUAD)
    before = sizes(B.folder)
    # the base must come back byte for byte before anything is appended to it
    # (not byte for byte: a built .prp holds keys in the order its steps added them, join() writes them in order of
    # first use - so every node with its strings spelled out is compared, and the scene property block)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    if not getattr(B, 'verified', False):               # (prepare() has done it when it edited the build in memory)
        _roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = room_sets_check(B.scene, octx, rmi, rmc)

    M, tops = make(B, P, log)
    if more is not None:
        more.nodes(M, tops)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'bots')
    # ---- the round-start event starts the squad
    timer = R_ + SQUAD + 'Timer_start_bots'
    mon = Jn.resolve(P['monitor'])[0]
    mi = next(i for i, (nm, _b) in enumerate(Jn.nodes[mon]['ctrls']) if Jn.p.key(nm) == 'AIMonitor')
    def fn(us):
        have = [Jn.p.key(t) for t in us[2][1:]]
        if timer.lower() not in [h.lower() for h in have]:
            us[2] = kl_fa._refs(Jn, have + [timer])
    kl_fa.edit(Jn, mon, mi, fn)
    if more is not None:
        more.edit(Jn)
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    # ---- .gms / .buf
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
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
    for t in tops:
        ent(t, None)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    # ---- .oct / .rmi / .rmc: every slot id moved
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    # the squad and step groups in the root's group tree, as F07 has them: the box of the places below them, +- 10
    items = []
    for n in order:
        if not n.tid & kl_scene.GROUP or n.name.startswith('Glazer_'):     # F07 lists neither the actor groups nor the boxes
            continue
        ps = [k.pos for k in n.walk() if k.name.startswith('Pos#')]
        if n.name.startswith(SQUAD + 'Squad#'):
            ps = ps + [k.pos for k in n.kids if k.name.startswith('Glazer_')]
        if ps:
            lo = tuple(min(p[a] for p in ps) - 10.0 for a in range(3))
            hi = tuple(max(p[a] for p in ps) + (10.0 if a != 1 or not n.name.startswith(SQUAD) else 190.0) for a in range(3))
            items.append((slot1[made[id(n)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    listed, repointed, new_prm = 0, 0, None
    if root3 is not None and items and P['options']['tree']:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        listed = len(items)
        octn.rooms[0][3].check()                        # raises unless the engine walks it correctly
        # the tree grew, so every collision record behind the room trees moved: the .prm's model roots name them by
        # file offset ((offset + 4) | 1 at +0x1c of a 64-byte type-7 chunk, kl_octree) - re-pointed in place, as
        # kl_graft.build does for S's records. Nothing else of the .prm changes, its size stays.
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(B['.prm'])
            t, n = struct.unpack_from('<II', prm, 0)
            old = set(octx.record_refs())
            for i in range(1, n):
                o, size = struct.unpack_from('<II', prm, t + 16 * i)
                if size == 64 and prm[o:o + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, o + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, o + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            # (fewer roots than records is the rule on a lightened + wardrobe build: the wardrobe took the chunk indices
            # of dead model roots, whose records stay in the .oct unnamed. M01: 2130 records, 1107 named.)
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(prm)
    post = room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'bots.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = sizes(dst)
    rep = collections.OrderedDict(
        source=B.folder, out=dst, members_changed=changed, entities_added=len(order), entities=len(ents),
        classes_added=dict(collections.Counter(J.schema('dd').geoms.get(n.tid) for n in order)),
        controllers_added=dict(collections.Counter(M.p.key(nm) for n in order for nm, _b in n.ctrls)),
        ref_ids='%d..%d' % (nxt - len(order), nxt - 1), slot_ids_moved=moved, groups_listed_in_root_tree_3=listed,
        prm_model_roots_repointed=repointed,
        slot_id_faults_before=pre, slot_id_faults_after=post, big_before=before, big_after=after)
    # steps.json (kl_maps.audit compares the folder with what was measured): the squad is one more step after the verify
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['bots'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_bots: AI heister squad (7 bots, %d entities) from %s; options %s\n' % (len(order), B.folder, json.dumps(P['options'], sort_keys=True)))
    log('written %s: %d entities added (%s); members changed: %s; %d slot ids renumbered, %d groups listed in the root\'s group tree, '
        '%d model roots of the .prm re-pointed at their moved .oct records'
        % (zp, len(order), ', '.join('%s %d' % kv for kv in rep['classes_added'].items()), ' '.join(changed), moved, listed, repointed))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    return rep


# ------------------------------------------------------------------ the check
def check(folder, log=print, slot=SLOT, early_ok=None, links=None):
    """Every check on a finished folder -> (list of (severity, text), facts). Severities: FAIL (must be none before
    an install), NOTE (differs from stock, said aloud). early_ok: a bot that enters a level exit box before its
    loot wait is a NOTE, not a FAIL (None: what the folder's bots.json says the build was made with). links: walk the
    mesh's links too (None: when bots.json says the build has a drop link of this module)."""
    B = Built(folder, slot)
    bj = os.path.join(B.folder, 'bots.json')
    popt = json.load(open(bj)).get('plan', {}).get('options', {}) if os.path.isfile(bj) else {}
    if early_ok is None:
        early_ok = bool(popt.get('early_call'))
    if links is None:                                   # a build with a drop link written by this module (option drop)
        links = bool(popt.get('drop'))
    sc, nav, out = B.sc, Nav(B.scene.nav, links=links), []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    S = stations(B, nav)
    home = S['home']
    name = lambda k: sc.path[k][5:]
    res = lambda s: sc.resolve(s)
    facts = collections.OrderedDict()
    # 1. the actors
    allies = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and B.values(k)['ZFFActor[0]'] == 'Ally']
    facts['bots'] = len(allies)
    if len(allies) != 7:
        fail('%d ZFFActor of team Ally (stock: 7, Squad#02..#08)' % len(allies))
    digits, squads = [], {}
    cols = None
    try:
        import kl_anm
        cols = {c.name.lower() for c in kl_anm.Anm(B['.ANM'], 'dd').cols}
    except Exception as x:                              # the animation test is one of many: say it, go on
        note('the .ANM could not be read for the animation-set test: %s' % x)
    for k in allies:
        g = sc.parent[k]
        gn = sc.names[g]
        top = sc.top[k]
        squads[top] = k
        if len(gn) < 19 or gn[18] not in '12345678':
            fail('%s: group name %r has no digit 1..8 at index 18 (int3 at kl2 0x51ab2d when the bot speaks a per-character line)' % (name(k), gn))
            continue
        N = int(gn[18]); digits.append(N)
        v = B.values(k)
        hero = S['heroes'].get(N)
        if hero is None:
            fail('%s: no Heroes!Hero_0%d\\Ground' % (name(k), N)); continue
        if v['ZGEOM[4]'] != hero[0] or B.ents[k - 1].model != hero[0]:
            fail('%s: model %d (.prp) / %d (.gms), Hero_0%d has %d - the game\'s body swap (0x8f5e90) finds a bot by that number'
                 % (name(k), v['ZGEOM[4]'], B.ents[k - 1].model, N, hero[0]))
        if (v['ZLNKOBJ[1]'], v['ZLNKWHANDS[5]']) != hero[1:]:
            fail('%s: .SND offsets %s, the heroes have %s' % (name(k), (v['ZLNKOBJ[1]'], v['ZLNKWHANDS[5]']), hero[1:]))
        anim = v['ZLNKOBJ[2]']
        if cols is not None and anim.lower() not in cols:
            fail('%s: animation set %s is not in the .ANM' % (name(k), anim))
        if not res(v['ZFFActor[1]']):
            fail('%s: weapon %s does not resolve' % (name(k), v['ZFFActor[1]']))
        if not kl_fa.has(sc, k, 'ZSoldier'):
            fail('%s: no ZSoldier controller' % name(k))
        ss = [vv for kk, _i, vv in kl_fa.controllers(sc, 'ZSquadScript') if kk == top]
        if not ss or ss[0][1] != 'eHeistOnly':
            fail('%s: its squad group %s has no ZSquadScript with field 1 = eHeistOnly' % (name(k), sc.names[top]))
    if sorted(digits) != list(BOTS):
        (fail if len(set(digits)) != len(digits) else note)('bot digits %s (stock: 2..8, one voice each)' % sorted(digits))
    # 2. the start: AIMonitor -> timer -> the first step of every squad; every chain to its end
    timer = res(R_ + SQUAD + 'Timer_start_bots')
    mon = [v for _k, _i, v in kl_fa.controllers(sc, 'AIMonitor')]
    if not timer or not any(R_ + SQUAD + 'Timer_start_bots' in v[2] for v in mon):
        fail('no AIMonitor list 2 names %sTimer_start_bots' % SQUAD)
    firsts = []
    if timer:
        tv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if k == timer[0]]
        firsts = tv[0][4] if tv else []
        if len(firsts) != len(squads) or {sc.top[j] for s in firsts for j in res(s)} != set(squads):
            fail('Timer_start_bots names %d first steps of %d squads (%d squads have a bot)' % (len(firsts), len({sc.top[j] for s in firsts for j in res(s)}), len(squads)))
    mine = {k for t in sc.tops() if sc.names[t].startswith(SQUAD) for k in range(t, sc.end[t])}
    facts['squad_nodes'] = len(mine)
    dang = [(sc.path[k], f, s) for k, _h, f, s, hit in J.references(sc) if k in mine and not hit]
    for p, f, s in dang[:8]:
        fail('%s %s -> %s does not resolve' % (p, f, s))
    out_refs = collections.Counter()
    for k, _h, f, _s, hit in J.references(sc):
        if k in mine and hit and not all(h in mine for h in hit):
            out_refs['%s -> %s' % (f, sc.names[sc.top[hit[0]]].split('!')[0].split('/')[0])] += 1
    facts['references_out_of_the_squad'] = dict(out_refs)
    NEXT = {'DefendBehaviourRout': 7, 'SquadModifierBehaviour': 26, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerActorsDead': 2,
            'KickDoorBehaviourRout': 0, 'RunToCoverBehaviourRout': 0}
    ctrl_of = {}
    for cn in NEXT:
        for k, _i, v in kl_fa.controllers(sc, cn):
            if k in mine:
                ctrl_of[k] = (cn, v)
    ally_boxes = [k for k, _i, _v in kl_fa.controllers(sc, 'AllyEscapeBox')]
    facts['ally_boxes'] = [name(k) for k in ally_boxes]
    # the cases: which container holds which loot object, which glass opens which container, which opens by itself
    box_of, glass_of, self_open = collections.defaultdict(list), collections.defaultdict(list), set()
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyContainer'):
        for s in (v[0] if v and isinstance(v[0], list) else []):
            for j in res(s):
                box_of[j].append(k)
    for k, _i, v in kl_fa.controllers(sc, 'TriggerBox2'):
        if 'Open' in v:                                 # the stock form: somebody within reach opens the container
            self_open.update(j for s in (v[0] if v and isinstance(v[0], list) else []) for j in res(s) if kl_fa.has(sc, j, 'OnlineMoneyContainer'))
    for k, _i, v in kl_fa.controllers(sc, 'RelayMessage'):
        if len(v) > 2 and v[0] == 'HavokShattered' and v[1] == 'Open' and kl_fa.has(sc, k, 'HavokShatterGlass'):
            for j in res(v[2]):
                glass_of[j].append(k)
    relay_of = {k: v for k, _i, v in kl_fa.controllers(sc, 'RelayMessageList') if k in mine}
    # a case is opened for everybody by whichever squad's relay names it (each case is named by CASE_BOTS squads)
    opened_all = {t for rv in relay_of.values() if rv[1] == 'Open' for s in rv[2] for t in res(s)}
    broken_all = {t for rv in relay_of.values() if rv[1] == 'Activate' for s in rv[2] for t in res(s)}
    used_relays = set()
    # 3. per squad: the walk of its chain
    enters, lev = S['triggers'].get('ENTERS', []), S['exits'] + S['triggers'].get('BOARDS', [])
    act = S['action']
    ap = act and B.at(act)
    routes = collections.OrderedDict()
    feet = []
    lane, lane_least, lane_cross, lane_path = lanes(B), collections.OrderedDict(), collections.OrderedDict(), collections.OrderedDict()
    hops = {(tuple(pa), tuple(pb)) for ds in nav.drops.values() for _j, pa, pb, _k in ds}
    for top, actor in sorted(squads.items(), key=lambda kv: sc.names[kv[0]]):
        first = [j for s in firsts for j in res(s) if sc.top[j] == top]
        places, seen, k, tight, waits, n_in = [], set(), first[0] if first else None, False, [], None
        opened, broken, relays = set(), set(), 0
        while k is not None and k not in seen:
            seen.add(k)
            cn, v = ctrl_of.get(k, (None, None))
            if cn is None:
                fail('%s: the chain reaches %s, which has no behaviour or wait controller' % (sc.names[top], name(k))); break
            if cn == 'DefendBehaviourRout':
                tg = ([v[0]] if v[0] else []) + list(v[1])
                if not tg:
                    fail('%s: DefendBehaviourRout without a place' % name(k))
                places += [j for s in tg for j in res(s)]
            elif cn == 'SquadModifierBehaviour':
                tight = v[9] == 'eDM_Tight'
            else:
                # the places walked before the LAST loot wait: up to there a bot must stay out of the level exit
                # boxes. (A timer that only fans out to the cases' relays is no loot wait.)
                if cn != 'TriggerDelay2' or 'done_looting' in sc.names[k]:
                    n_in = len(places)
                waits.append((cn, v))
            nx = [j for s in v[NEXT[cn]] for j in res(s)]
            # a timer may name the cases' relays beside the next link of the chain (this module's 0n8_Timer_at_cases)
            for j in nx:
                if j in relay_of:
                    rv = relay_of[j]
                    relays += 1
                    used_relays.add(j)
                    tg = [t for s in rv[2] for t in res(s)]
                    if rv[0] != 'AITrigger' or len(tg) != len(rv[2]) or not tg:
                        fail('%s: RelayMessageList %s: in-message %r, %d of %d targets resolve' % (sc.names[top], name(j), rv[0], len(tg), len(rv[2])))
                    if rv[1] == 'Activate' and all(kl_fa.has(sc, t, 'HavokShatterGlass') for t in tg):
                        broken.update(tg)
                    elif rv[1] == 'Open' and all(kl_fa.has(sc, t, 'OnlineMoneyContainer') for t in tg):
                        opened.update(tg)
                    else:
                        fail('%s: RelayMessageList %s sends %r to something that is no glass / no money container' % (sc.names[top], name(j), rv[1]))
            nx = [j for j in nx if j in ctrl_of] or [j for j in nx if j not in relay_of]
            k = nx[0] if nx else None
        if not places:
            fail('%s: no route place' % sc.names[top]); continue
        pts = [B.at(j) for j in places]
        sp = B.at(actor)
        feet.append(sp)
        # every place and the bot on a walkable polygon of the START row's part, clear of the walls
        low = 1e9
        for what_, p in [('the bot', sp)] + [(name(j), q) for j, q in zip(places, pts)]:
            hit = nav.at(p[0], p[1], p[2], dy=15.0)
            if hit is None:
                fail('%s at (%d, %d, %d) is not on a walkable polygon (within 15 of the mesh\'s height)' % (what_, *p)); continue
            if nav.part[hit[0]] != home:
                fail('%s at (%d, %d, %d) is on a mesh part of %d polygons, not the START row\'s' % (what_, *p, nav.part_size[nav.part[hit[0]]]))
            c = nav.clearance(*p)
            low = min(low, c)
            if c < CLEAR_MIN:
                fail('%s at (%d, %d, %d): %d from a mesh edge without a neighbour (least %d)' % (what_, *p, c, CLEAR_MIN))
        # connected, in order: a path on the mesh from the bot through every place
        length, prev, ok, walked = 0.0, sp, True, []
        for n_p, p in enumerate(pts):
            a, b = nav.at(prev[0], prev[1], prev[2], dy=15.0), nav.at(p[0], p[1], p[2], dy=15.0)
            got = a and b and nav.path(tuple(prev) + (a[0],), tuple(p) + (b[0],))
            if not got:
                ok = False; break
            walked.append(got[0])
            # D4: beyond a one-way link nothing brings a bot back. The place it stands at before the link must be
            # inside an AllyEscapeBox, or a bot the link does not carry (the AI taking a hand-written link was
            # never seen) waits there for the rest of the round
            if any((tuple(u), tuple(w)) in hops for u, w in zip(got[0], got[0][1:])) and ally_boxes \
                    and not any(B.in_box(x, prev) for x in ally_boxes):
                fail('%s: place %d lies beyond a one-way drop link and the place before it, (%d, %d, %d), is in no AllyEscapeBox: a bot the '
                     'link does not carry is never taken aboard' % (sc.names[top], n_p + 1, *prev))
            length += got[1]; prev = p
        if not ok:
            fail('%s: no path on the mesh along its places' % sc.names[top])
        # D3: the escape vehicle's road. A place of the way out (after the last loot wait) or the last place nearer
        # than the body's half width + a man to the vehicle's line is IN its lane: a key-framed van drives through
        # whatever stands there (and carries a KillBox at its nose)
        if lane:
            first_out = n_in if n_in is not None else len(pts) - 1
            near_l = [(lane_dist(lane, p), n_p) for n_p, p in enumerate(pts) if n_p >= first_out]
            for d, n_p in near_l:
                if d < LANE_HALF + LANE_MAN:
                    fail('%s: place %d of %d, %s at (%d, %d, %d), is %d from the escape vehicle\'s line: IN ITS LANE (half width %d + %d)'
                         % (sc.names[top], n_p + 1, len(pts), 'the last place' if n_p == len(pts) - 1 else 'on the way out', *pts[n_p], d, LANE_HALF, LANE_MAN))
            lane_least[sc.names[top]] = round(min(d for d, _n in near_l)) if near_l else None
            # where the way out crosses the line: said, not failed - the bots walk on, they do not stand there.
            # 'sides' = two places that follow one another lie on different sides of it (the bot HAS to cross);
            # 'path' = only this module's stand-in path does (through the middles of the polygons' shared edges,
            # which on a street polygon is the middle of the road; the game's own pathfinder was not read)
            seq = ([sp] + pts)[first_out:]
            for u, w in zip(seq, seq[1:]):
                if _crosses(lane, u, w):
                    lane_cross[sc.names[top]] = [round(v) for v in w]
            for poly in walked[first_out:] if ok else []:
                for u, w in zip(poly, poly[1:]):
                    if _crosses(lane, u, w):
                        lane_path[sc.names[top]] = [round(v) for v in u]
        # the level exit boxes: an actor with a crew record inside one CALLS THE ESCAPE VEHICLE (kl2 0x6c3d50 ->
        # ZGameRulesHeist slot 44, 0x6cd8e0); the round then ends one vehicle cycle + 60 s later (runs BOT1 / BOT2)
        call = first_exit_entry(B, nav, S['exits'], [sp] + pts) if S['exits'] else None
        if call and n_in is not None and call[1] <= n_in:
            (note if early_ok else fail)('%s: is inside level exit box %s after %d of path, on the way to place %d of the %d BEFORE its loot wait: '
                                         'it calls the escape vehicle on the way in%s' % (sc.names[top], name(call[2]), call[0], call[1], n_in,
                                                                                         ' (--early-call build)' if early_ok else ''))
        # the stage
        st1 = any(B.in_box(t, p) for t in enters for p in pts)
        st3 = any(B.in_box(t, p) for t in lev for p in pts)
        inbox = any(B.in_box(a, pts[-1]) for a in ally_boxes)
        if not st1:
            fail('%s: no route place inside an ENTERS_BANK trigger: no stage 1, the bot never loots (kl2 0x451920)' % sc.names[top])
        if not st3 and not inbox:
            fail('%s: no route place inside the level exit / a BOARDS trigger and the last place is in no AllyEscapeBox: the bot never boards' % sc.names[top])
        elif not st3:
            note('%s: stage 3 is never reached (no level exit / BOARDS trigger on its mesh part); it boards through the AllyEscapeBox only' % sc.names[top])
        if not inbox and ap:
            hit = nav.at(ap[0], ap[1], ap[2], part=home, lo=ap[1] - B.box(act)[1] - 200.0, hi=ap[1] + B.box(act)[1])
            if hit is None:
                fail('%s: the boarding action %s is not on the mesh part of the last route place and there is no AllyEscapeBox' % (sc.names[top], name(act)))
            d = math.hypot(pts[-1][0] - ap[0], pts[-1][2] - ap[2])
            if d > 1500.0:
                note('%s: the last place is %d from the boarding action' % (sc.names[top], d))
        if not tight:
            note('%s: the chain does not end in a tight-defense SquadModifierBehaviour (F01 F03 F04 F07 do)' % sc.names[top])
        shut = set()
        for cn, v in waits:
            if cn == 'TriggerLootDepleted':
                bad = [s for s in v[0] if not any(kl_fa.has(sc, j, 'OnlineMoneyCtrl') or kl_fa.has(sc, j, 'OnlineMoneyContainer') or
                                                  any(kl_fa.has(sc, c, 'OnlineMoneyCtrl') for c in range(j, sc.end[j])) for j in res(s))]
                if bad or not v[0]:
                    fail('%s: TriggerLootDepleted names %d objects, %d of them no money object (an empty list fires at once: 0x811fb0)' % (sc.names[top], len(v[0]), len(bad)))
                # a loot object in a container that only its glass opens: somebody has to open it for the bot
                for s in v[0]:
                    for j in res(s):
                        for c in box_of.get(j, []):
                            if c not in self_open and c not in opened_all and not (set(glass_of.get(c, [])) & broken_all):
                                shut.add(c)
        if shut:
            fail('%s: its loot wait names loot in %d case(s) that open only when their glass is SHOT, and no step of any squad opens them '
                 '(an object in a shut container cannot be taken, kl2 0x6cdb8f; no AI shoots at glass): e.g. %s'
                 % (sc.names[top], len(shut), name(sorted(shut)[0]).split(chr(92))[-1]))
            if cn == 'TriggerActorsDead':
                bad = [s for s in v[0] if not any(sc.cls(c) == 'ZFFActor' for j in res(s) for c in range(j, sc.end[j]))]
                if bad or not v[0]:
                    fail('%s: TriggerActorsDead names %d groups, %d without an actor (it has no time limit)' % (sc.names[top], len(v[0]), len(bad)))
        routes[sc.names[top]] = {'bot': [round(v) for v in sp], 'places': [[round(v) for v in p] for p in pts], 'path_length': round(length),
                                 'least_clearance': round(low), 'stage_1': st1, 'stage_3': st3, 'ends_in_ally_box': inbox,
                                 'places_before_the_loot_wait': n_in,
                                 'first_inside_a_level_exit_box': call and {'path': round(call[0]), 'place': call[1], 'box': name(call[2])},
                                 'waits': [(cn, len(v[0]) if isinstance(v[0], list) else v[0], v[1]) for cn, v in waits],
                                 'cases': {'relays': relays, 'glass_broken': len(broken), 'containers_opened': len(opened)}}
    facts['routes'] = routes
    if lane:
        vd = van_drives(B)
        facts['lane'] = {'vehicle': 'key-framed van' if vd else 'spline car', 'lines': len(lane), 'points': sum(len(x) for x in lane),
                         'least_distance_of_a_way_out_place': lane_least, 'fail_below': LANE_HALF + LANE_MAN,
                         'places_on_different_sides_before': lane_cross, 'stand_in_path_crosses_the_line_at': lane_path}
        got = [v for v in lane_least.values() if v is not None]
        if got and min(got) >= 1e8:
            log('escape %s: no place of the way out is within 400 in height of its line (the bots end on another floor)' % facts['lane']['vehicle'])
        elif got:
            log('escape %s: the places of the way out and the last places are %d .. %d from its line (FAIL below %d, planned at %d)'
                % (facts['lane']['vehicle'], min(got), max(got), LANE_HALF + LANE_MAN, LANE_CLEAR))
        if lane_cross:
            note('%d squad(s) HAVE TO CROSS the escape vehicle\'s line on the way out (e.g. %s on the way to %s): two places that follow one '
                 'another lie on different sides of its road. They do not stand there; a van that is driving at that moment drives through them'
                 % (len(lane_cross), next(iter(lane_cross)), tuple(next(iter(lane_cross.values())))))
        if lane_path:
            log('  (the stand-in path of %d squad(s) touches the vehicle\'s line between two places of the same side, e.g. near %s: the middle of '
                'a street polygon\'s edge. Not a finding: where the game\'s pathfinder walks between two places was not read)'
                % (len(lane_path), tuple(next(iter(lane_path.values())))))
        if vd:
            facts['van'] = [{k: ([round(x) for x in d[k]] if k != 'seconds' else list(d[k])) for k in ('wait', 'stop', 'end', 'board', 'seconds')} for d in vd]
            for d in vd:
                for a in ally_boxes:
                    q = B.at(a)
                    facts.setdefault('ally_box_from_the_van_line', {})[name(a)] = round(lane_dist([d['line']], q))
    for j in sorted(set(relay_of) - used_relays):
        fail('%s: a RelayMessageList no walked chain names' % name(j))
    facts['cases'] = {'glass_broken_by_a_step': len(broken_all), 'containers_opened_by_a_step': len(opened_all),
                      'containers_that_need_a_shot': sum(1 for k, _i, _v in kl_fa.controllers(sc, 'OnlineMoneyContainer') if k not in self_open)}
    # 4. where the seven stand
    if feet:
        near = [min(math.hypot(f[0] - p[0], f[2] - p[2]) for p, _f in S['starts']) for f in feet]
        apart = min([math.hypot(a[0] - b[0], a[2] - b[2]) for i, a in enumerate(feet) for b in feet[i + 1:]] or [0])
        above = [round(p[1] - sum(f[1] for f in feet) / len(feet)) for p, _f in S['starts']]
        facts['start'] = {'bot_to_nearest_START_point': [round(min(near)), round(max(near))], 'bots_apart_at_least': round(apart),
                          'START_points_above_the_bots_feet': [min(above), max(above)]}
        if min(near) < 60 or max(near) > 600:
            fail('bots stand %d..%d from the nearest START point (stock 80..440)' % (min(near), max(near)))
        if apart < 80:
            fail('two bots stand %d apart' % apart)
        if not 40 <= sum(above) / len(above) <= 180:
            note('the START points are %d..%d above the bots\' feet (stock 92..137)' % (min(above), max(above)))
    # 5. classes and controllers: nothing the levels do not already run
    sys_level = B.result.get('S') or 'F07'
    stock, _e = Maker.level(sys_level if sys_level in SYSTEM_LEVELS else 'F07')
    s_tids = set(stock.tids)
    s_ctrl = {stock.p.key(nm) for n in stock.nodes for nm, _b in n['ctrls']}
    here = {sc.tids[k] for k in range(1, len(sc.nodes)) if k not in mine}
    for t in sorted({sc.tids[k] for k in mine}):
        if t not in s_tids:
            fail('class %s (%#x) of the squad is in no object of stock %s' % (J.schema('dd').geoms.get(t), t, sys_level))
        if t not in here:
            note('class %s is used by the squad only (stock %s has it)' % (J.schema('dd').geoms.get(t), sys_level))
    for cn in sorted({sc.p.key(nm) for k in mine for nm, _b in sc.nodes[k]['ctrls']}):
        if not any(J.schema('dd').controller(cn, sc.cls(k)) for k in mine if any(sc.p.key(nm) == cn for nm, _b in sc.nodes[k]['ctrls'])):
            fail('controller %s is not registered in kl2.exe' % cn)
        elif cn not in s_ctrl:
            users = [L for L in SYSTEM_LEVELS if any(Maker.level(L)[0].p.key(nm) == cn for n in Maker.level(L)[0].nodes for nm, _b in n['ctrls'])]
            (note if users else fail)('controller %s is not used by stock %s; stock levels that run it in Arcade: %s' % (cn, sys_level, ' '.join(users) or 'NONE'))
    bad = [(k, what_, why) for k, what_, why in J.misfits(sc) if k in mine]
    for k, what_, why in bad[:5]:
        fail('%s: %s does not fit its class: %s' % (name(k), what_, why))
    # 6. the files: entity table, slot ids
    for x in B.scene.check()[:5]:
        fail('kl_scene.check: ' + x)
    for x in room_sets_check(B.scene, O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])):
        note('slot ids: %s - the same counts are in the build the squad was added to (apply() refuses any change)' % x)
    for k in mine:
        e, v = B.ents[k - 1], kl_fa.node_values(sc, k)
        if tuple(struct.unpack('<3f', e.trans[:12])) != tuple(struct.unpack('<3f', struct.pack('<3f', *v[2]))) or e.model != v[4]:
            fail('%s: .gms record and .prp disagree on place or model' % name(k)); break
    # 7. the voices
    try:
        import kl_voice
        hv = kl_voice.heisters(B.zp, stream=None)
        crash = [t for s, t in hv['findings'] if s == 'CRASH']
        facts['voice'] = {k: v for k, v in hv.items() if k != 'findings' and ('heister' in k.lower() or 'per-character' in k or 'pairs' in k)}
        for t in crash:
            fail('kl_voice.heisters: ' + t)
    except Exception as x:
        note('kl_voice.heisters did not run: %s: %s' % (type(x).__name__, x))
    # 8. kl_fa's own view
    fa = kl_fa.check(sc, B.files.get(B.ext.get('.SND')), B.files.get(B.ext.get('English.LOC')), B['.ANM'])
    facts['kl_fa'] = dict(collections.Counter(kl_fa.SEV[f.sev] for f in fa))
    for f in fa:
        if f.sev <= kl_fa.BROKEN:
            fail('kl_fa.check: ' + str(f))
        elif f.code == 'bots':
            fail('kl_fa.check still says: ' + str(f))
    facts['big'] = sizes(folder, slot)
    out.sort(key=lambda x: x[0] != 'FAIL')
    for sev, text in out:
        log('%-4s %s' % (sev, text))
    for nm, r in routes.items():
        log('  %s: bot at %s, %d places, %d of path, least clearance %d, stage 1 %s, stage 3 %s, ends in an AllyEscapeBox %s; waits %s'
            % (nm, tuple(r['bot']), len(r['places']), r['path_length'], r['least_clearance'], r['stage_1'], r['stage_3'], r['ends_in_ally_box'], r['waits']))
    log('RESULT: %s (%d FAIL, %d NOTE); %d bots, %d squad nodes; large blocks %s' % (
        'PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out),
        len(allies), len(mine), ', '.join('%s %d' % kv for kv in facts['big'].items())))
    return out, facts


def guns_entries(folder, log=print, slot=SLOT):
    """KLGuns.ini of a build made before 2026-10-10 evening has no 'Entries=' (the chunk count of the .prm beside
    it); klgun.c refuses such a file since then and kl_map_guns.py check says so, with the line to add. The squad
    step does not change the chunk count, so the line is added to the COPY in the output folder - nothing else of
    the file changes. -> the count written, or None when there was nothing to do."""
    ini = os.path.join(folder, 'KLGuns.ini')
    if not os.path.isfile(ini):
        return None
    raw = open(ini, 'rb').read()
    text = raw.decode('latin1')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    try:
        a = next(i for i, l in enumerate(lines) if l.strip() == '[Guns]')
    except StopIteration:
        return None
    b = next((i for i in range(a + 1, len(lines)) if lines[i].strip().startswith('[')), len(lines))
    if any(l.split('=')[0].strip() == 'Entries' for l in lines[a + 1:b]):
        return None
    with zipfile.ZipFile(os.path.join(folder, slot + '_Main.zip')) as z:
        prm = z.read(next(n for n in z.namelist() if n.endswith('_Main.prm')))
    n = struct.unpack_from('<I', prm, 4)[0]
    while b > a + 1 and not lines[b - 1].strip():
        b -= 1
    lines.insert(b, 'Entries=%d' % n)
    with open(ini, 'wb') as f:
        f.write(nl.join(lines).encode('latin1'))
    log('KLGuns.ini: the line Entries=%d added under [Guns] (the .prm\'s chunk count; klgun.c and kl_map_guns.py check want it since 2026-10-10)' % n)
    return n


def build(src, dst, opt=None, log=print):
    """plan + apply + check on the written folder; bots.txt / bots.json in it -> (findings, report)."""
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    B = Built(src)
    say('kl_fa_bots build %s -> %s' % (src, dst))
    edits = prepare(B, opt, say)
    P = plan(B, opt, say)
    P['edits'] = edits
    rep = apply(B, P, dst, say)
    rep['guns_ini_entries'] = guns_entries(dst, say)
    out, facts = check(dst, say, early_ok=bool(P['options'].get('early_call')), links=bool(P['options'].get('drop')))
    rep.update(plan=P, check=[list(x) for x in out], facts=facts)
    with open(os.path.join(dst, 'bots.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'bots.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def diff(src, dst, log=print, also=()):
    """What differs between the build the squad was added to and the result, file by file - the proof that the step
    changed nothing else. -> list of UNEXPECTED differences (must be empty). Expected: the new top-level subtrees at
    the end of the scene, one more entry in AIMonitor list 2, the new groups in the root's group tree, the .oct record
    offsets in the .prm's model roots, and slot ids that name the same entities as before.
    also: names of top-level subtrees that may differ too (kl_fa_bots_rt: the JumpPoint whose list starts the
    squads' second leg)."""
    A, B = Built(src), Built(dst)
    bad = []
    n = len(A.ents)
    bj = os.path.join(B.folder, 'bots.json')
    edits = (json.load(open(bj)).get('plan', {}).get('edits') or {}) if os.path.isfile(bj) else {}
    cut, drops = set(edits.get('boxes') or {}), edits.get('drops') or []
    also = tuple(also) + tuple(cut)
    new = B.ents[n:]
    if any(e.parent is not None and e.parent not in set(new) for e in new) or len(B.ents) < n:
        bad.append('the new entities are not whole top-level subtrees at the end of the scene')
    ia, ib = {e: i for i, e in enumerate(A.ents)}, {e: i for i, e in enumerate(B.ents)}
    key = lambda e, ix: (e.name, e.tid, e.flags, e.group, e.model, e.rot, e.trans, e.raw, e.aux, e.ref,
                         None if e.parent is None else ix[e.parent], None if e.links is None else [(None if t is None else ix[t], b) for t, b in e.links])
    same = sum(key(a, ia) == key(b, ib) for a, b in zip(A.ents, B.ents))
    moved = [a for a, b in zip(A.ents, B.ents) if key(a, ia) != key(b, ib) and a.parent is None and a.name.decode('latin1') in cut
             and key(a, ia)[:6] + key(a, ia)[7:] == key(b, ib)[:6] + key(b, ib)[7:]]         # only the place differs
    if same + len(moved) != n or len(moved) != len(cut):
        bad.append('%d of %d entities of the build differ in the .gms (%d of them the %d cut level exit boxes)' % (n - same, n, len(moved), len(cut)))
    same += len(moved)
    if [(None if a is None else ia[a], ia[b]) for a, b in A.scene.pairs] != [(None if a is None else ib[a], ib[b]) for a, b in B.scene.pairs]:
        bad.append('room pairs differ')
    if (A.scene.head, A.scene.tail, A.scene.dyn, A.scene.tags, A.scene.budget, A.scene.fdx) != \
            (B.scene.head, B.scene.tail, B.scene.dyn, B.scene.tags, B.scene.budget, B.scene.fdx):
        bad.append('.buf head / tail, dynamic list, tags, heap budget or FDX differ')
    if A.scene.nav != B.scene.nav:
        # a drop link: two more waypoints, one more link; trees, polygons' shape, vertices and edges as they were
        na, Aa = kl_pf4.split(A.scene.nav, True)
        nb, Ab = kl_pf4.split(B.scene.nav, True)
        shape = lambda X: [r[:16] + r[20:] for r in X[3]]            # a polygon without its 'waypoints before'
        ok = (len(drops) > 0 and all(Aa[k] == Ab[k] for k in (0, 1, 2, 6, 8, 9, 11, 12)) and shape(Aa) == shape(Ab)
              and nb[5] == na[5] + 2 * len(drops) and nb[7] == na[7] + len(drops) and nb[4] == na[4]
              and [r[48:] for r in Aa[4]] == [r[48:] for r in Ab[4]])
        if not ok:
            bad.append('the navigation mesh differs in more than the %d drop link(s) of the plan' % len(drops))
        else:
            log('navigation mesh: %d waypoints -> %d, %d links -> %d (the plan\'s drop); trees, polygons, vertices, edges, area boxes equal'
                % (na[5], nb[5], na[7], nb[7]))
    log('.gms / .buf: %d entities as they were (record, parent, light lists by entity), %d new (REF %d..%d; REF slots %d -> %d); head, surface '
        'table, dynamic list, heap budget equal' % (same, len(new), min(e.ref for e in new) if new else 0, max(e.ref for e in new) if new else 0,
                                                                   A.scene.ref_slots, B.scene.ref_slots))
    # .prp: every old node with its strings spelled out; the one edit
    ta, tb = J.fingerprints(A.sc), J.fingerprints(B.sc)
    differ = [t for t, u in zip(A.sc.tops(), B.sc.tops()) if ta[t] != tb[u]]
    mon = [A.sc.names[t] for t in differ]
    differ = [t for t in differ if A.sc.names[t] not in also]
    if len(B.sc.tops()) < len(A.sc.tops()) or any(not any(A.sc.p.key(nm) == 'AIMonitor' for nm, _b in A.sc.nodes[t]['ctrls']) for t in differ) or len(differ) > 1:
        bad.append('.prp: top-level subtrees other than the AIMonitor differ: %s' % mon[:5])
    for nm in cut:                                      # a cut box: its x and its first size, nothing else
        ka, kb = A.sc.resolve(R_ + nm), B.sc.resolve(R_ + nm)
        va, vb = A.values(ka[0]), B.values(kb[0])
        cv = lambda X, k: [(X.sc.p.key(nm), [kl_fa.value(X.sc, u) for u in units(b[1:-1])]) for nm, b in X.sc.nodes[k[0]]['ctrls']]
        d = [f for f in va if va[f] != vb[f]]
        if sorted(d) != ['ZBoxPrimitive[0]', 'ZGEOM[2]'] or va['ZGEOM[2]'][1:] != vb['ZGEOM[2]'][1:] or \
                cv(A, ka) != cv(B, kb):
            bad.append('.prp: %s differs in more than its x and its first size: %s' % (nm, d))
    if J.text(A.sc, A.sc.p.settings) != J.text(B.sc, B.sc.p.settings):
        bad.append('.prp: the scene property block differs')
    log('.prp: %d of %d top-level subtrees equal, changed: %s; %d new subtrees; scene property block equal' % (
        len(A.sc.tops()) - len(differ), len(A.sc.tops()), mon, len(B.sc.tops()) - len(A.sc.tops())))
    # .oct / .rmi / .rmc by entity
    def trees(L, ix):
        by = {s + 2: ix[e] for e, s in L.scene.slots().items()}
        by[1] = -1
        o = O.Oct.parse(L['.oct'])
        sets = [[None if t is None else (t.origin, t.scale, sorted((by.get(it[0], 'gone'), t.world(it[1:4]), t.world(it[4:7])) for it in t.items)) for t in room] for room in o.rooms]
        idx = [[(b.raw[:0x4c], by.get(b.room, 'gone'), by.get(b.second, 'gone') if b.second else 0) for b in O.RoomIndex.parse(L[e]).boxes] for e in ('.rmi', '.rmc')]
        return o, sets, idx
    oa, sa, xa = trees(A, ia)
    ob, sb, xb = trees(B, ib)
    more = 0
    for r, (ra, rb) in enumerate(zip(sa, sb)):
        for t, (x, y) in enumerate(zip(ra, rb)):
            if x == y:
                continue
            if (r, t) == (0, 3) and x and y:
                ids_a = collections.Counter(i[0] for i in x[2]); ids_b = collections.Counter(i[0] for i in y[2])
                extra = ids_b - ids_a
                if ids_a - ids_b or any(i < n for i in extra):
                    bad.append('.oct: the root\'s group tree lost or gained an old entity')
                more = sum(extra.values())
            else:
                bad.append('.oct: room set %d tree %d differs' % (r, t))
    if len(sa) != len(sb) or xa != xb:
        bad.append('.oct room sets or .rmi / .rmc boxes differ by entity')
    if [r.pack() for r in oa.records] != [r.pack() for r in ob.records] or oa.tail != ob.tail:
        bad.append('.oct collision records or tail differ')
    log('.oct: %d room sets, every item names the entity it named; the root\'s group tree has %d more (the new groups); %d collision records '
        'and the tail equal; .rmi / .rmc: %d + %d boxes name the rooms they named' % (len(sa), more, len(oa.records), len(xa[0]), len(xa[1])))
    # .prm: only record offsets in model roots
    pa, pb = A['.prm'], B['.prm']
    cells = 0
    if pa != pb:
        if len(pa) != len(pb):
            bad.append('.prm: size differs')
        else:
            move = dict(zip(oa.record_refs(), ob.record_refs()))
            t, cnt = struct.unpack_from('<II', pa, 0)
            spans = {}
            for i in range(1, cnt):
                o, size = struct.unpack_from('<II', pa, t + 16 * i)
                if pa[o:o + size] != pb[o:o + size]:
                    va, vb = struct.unpack_from('<I', pa, o + 0x1c)[0], struct.unpack_from('<I', pb, o + 0x1c)[0]
                    if size != 64 or pa[o:o + 0x1c] != pb[o:o + 0x1c] or pa[o + 0x20:o + 64] != pb[o + 0x20:o + 64] or move.get(va) != vb:
                        spans[i] = 1
                    cells += 1
            if spans or pa[t:] != pb[t:] or pa[:16] != pb[:16]:
                bad.append('.prm: %d chunks differ in more than their .oct record offset, or the table differs' % len(spans))
    log('.prm: %s' % ('byte for byte' if pa == pb else '%d model roots differ, each only in its .oct record offset (+0x1c), old record -> the same record' % cells))
    rest = [e for e in A.ext if e not in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm') and A[e] != B[e]]
    if rest or A.order != B.order:
        bad.append('other members differ: %s' % rest)
    side = [f for f in os.listdir(A.folder) if f.startswith(SLOT + '_Main') and f != SLOT + '_Main.zip' or f == 'KLWardrobe.ini']
    sdiff = [f for f in side if not os.path.isfile(os.path.join(B.folder, f)) or open(os.path.join(A.folder, f), 'rb').read() != open(os.path.join(B.folder, f), 'rb').read()]
    if sdiff:
        bad.append('files beside the archive differ: %s' % sdiff)
    log('the other %d members and the %d files beside the archive (KLWardrobe.ini too): byte for byte' % (len(A.ext) - 7, len(side)))
    for x in bad:
        log('UNEXPECTED: ' + x)
    extra = ''.join([', %d level exit boxes cut (x and first size)' % len(cut) if cut else '', ', %d drop link(s) in the navigation mesh' % len(drops) if drops else ''])
    log('RESULT: %s' % ('only the squad was added' + extra if not bad else '%d unexpected differences' % len(bad)))
    return bad


def stock(levels=SYSTEM_LEVELS, log=print):
    """The stock levels' own squads through this module's reading of the mesh and of the trigger boxes: the control
    of Nav (neighbours, heights) and of Built.in_box (frames, half extents), and what 'as stock' means for a place."""
    q = lambda a, f: round(a[int(f * (len(a) - 1))]) if a else None
    for L in levels:
        B = Built(J.level_zip(L))
        sc, nav = B.sc, Nav(B.scene.nav)
        S = stations(B, nav)
        mine = {k for t in sc.tops() if 'merc_bot_squad' in sc.names[t] for k in range(t, sc.end[t])}
        pos = [k for k in mine if sc.cls(k) == 'ZBoxPrimitive' and not sc.nodes[k]['ctrls']]
        where, dys, cl = collections.Counter(), [], []
        for k in pos:
            p = B.at(k)
            hit = nav.at(p[0], p[1], p[2], dy=400)
            if not hit:
                where['off the mesh'] += 1; continue
            dys.append(p[1] - hit[1]); cl.append(nav.clearance(p[0], hit[1], p[2]))
            where['START row\'s part' if nav.part[hit[0]] == S['home'] else 'another part'] += 1
        dys.sort(); cl.sort()
        feet = []
        for k in (k for k in mine if sc.cls(k) == 'ZFFActor'):
            p = B.at(k); hit = nav.at(p[0], p[1], p[2], dy=400)
            feet.append(round(p[1] - hit[1]) if hit else None)
        ins = {}
        for kind, nodes in list(S['triggers'].items()) + [('level exit', S['exits'])]:
            for t in nodes:
                ins['%s %s' % (kind, sc.names[t].split('!')[-1])] = sum(B.in_box(t, B.at(k)) for k in pos)
        n_e, good = nav.selftest()
        log('%s: %d polygons in %d parts, neighbour edges shared %d of %d; %d route boxes: %s; box above the mesh %s / %s / %s (least, middle, most); '
            'clearance %s / %s / %s (least, 10 %%, middle); bots\' feet above the mesh %s; boxes inside: %s'
            % (L, len(nav.pv), len(nav.part_size), good, n_e, len(pos), dict(where), q(dys, 0), q(dys, .5), q(dys, 1), q(cl, 0), q(cl, .1), q(cl, .5), feet, ins))


def options(a):
    opt = {}
    def take(name, conv=str):
        if name in a:
            i = a.index(name)
            v = conv(a[i + 1]); del a[i:i + 2]
            return v
    for flag, key in (('--wait-guards', 'wait_guards'), ('--heal', 'heal'), ('--no-stage', 'no_stage'), ('--early-call', 'early_call')):
        if flag in a:
            a.remove(flag); opt[key] = True
    if '--no-tree' in a:
        a.remove('--no-tree'); opt['tree'] = False
    for flag in ('--drop', '--lane'):
        if flag in a:
            a.remove(flag); opt[flag[2:]] = True
    for name, key, conv in (('--ally-box', 'ally_box', str), ('--loot-seconds', 'loot_seconds', int), ('--start-delay', 'start_delay', float),
                            ('--stops', 'stops', int), ('--cases', 'cases', str), ('--exit-boxes', 'exit_boxes', str)):
        v = take(name, conv)
        if v is not None:
            opt[key] = v
    v = take('--park')
    if v is not None:
        opt['park'] = [float(x) for x in v.split(',')]
        if len(opt['park']) != 3:
            raise SystemExit('--park x,y,z')
    if opt.get('ally_box', 'auto') not in ('auto', 'on', 'off'):
        raise SystemExit('--ally-box auto|on|off')
    if opt.get('cases', 'off') not in ('off', 'glass', 'all') or opt.get('exit_boxes', 'keep') not in ('keep', 'cut') or not 1 <= opt.get('stops', 1) <= 8:
        raise SystemExit('--cases off|glass|all   --exit-boxes keep|cut   --stops 1..8')
    return opt


def owner(src_root, dst_root, maps=None, more=None, log=print):
    """The four maps as the owner asked for them on 2026-10-10 (RECIPE; re/bots.md 12): build <src_root>/<Mxx> into
    <dst_root>/<Mxx> for every map folder that has a recipe -> {map folder: (findings, report)}."""
    out = {}
    for d in sorted(os.listdir(src_root)):
        src = os.path.join(src_root, d)
        if not os.path.isfile(os.path.join(src, SLOT + '_Main.zip')) or (maps and d not in maps):
            continue
        rj = os.path.join(src, 'result.json')
        level = json.load(open(rj)).get('M') if os.path.isfile(rj) else None
        if level not in RECIPE:
            log('%s: no recipe for %s' % (d, level)); continue
        opt = dict(RECIPE[level], **(more or {}))
        log('==== %s (%s): %s' % (d, level, json.dumps(opt, sort_keys=True)))
        out[d] = build(src, os.path.join(dst_root, d), opt, log)
    return out


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'check':
        out, _f = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) >= 3 and a[0] == 'owner':
        res = owner(a[1], a[2], a[3:] or None, opt)
        for d, (out, _rep) in res.items():
            print('%s: %s' % (d, 'PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL'))
        sys.exit(1 if not res or any(s == 'FAIL' for out, _r in res.values() for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'plan':
        B = Built(a[1])
        prepare(B, opt)
        P = plan(B, opt)
        for N, b in P['bots'].items():
            print('Squad#0%d: stands at %s; places %s' % (N, tuple(b['start']), b['places']))
        print('steps: %s' % [(st['name'], st['stations']) for st in P['steps']])
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2]) else 0)
    elif a and a[0] == 'stock':
        stock(a[1:] or SYSTEM_LEVELS)
    elif len(a) >= 2 and a[0] == 'sizes':
        for d in a[1:]:
            print('%s: %s' % (d, ', '.join('%s %d' % kv for kv in sizes(d).items())))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
