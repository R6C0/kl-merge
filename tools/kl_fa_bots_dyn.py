#!/usr/bin/env python3
"""
DYNAMIC AI HEISTERS: a step on a FINISHED bots build (the squad of tools/kl_fa_bots.py / kl_fa_bots_rt.py is in
it). The seven keep their actors, crew records, loot waits, cases, stage triggers and last places; what is made new
is how they get from one to the next: no sprint, a hold at a cover box every few places with a timer, a random
choice between two or three covers at a hold, a start a few seconds apart, and seven sets of numbers
('personalities'). Research it is built on: re/bots_dynamic.md (kl2.exe read + the 21 stock levels measured).
Build notes, per map what each of the seven does, live things to look for: re/bots_dyn_build.md.
RANDOM ROUTES (2026-10-10 night, re/bots_dyn_build.md 11): between the places of a chain that must stay, the WAY
FORKS - a RandomTrigger draws, per bot and per round, one of two or three ways (another corridor of the mesh where
it has one, else the build's way moved to a side), and all of them meet again at the next fixed place.
OFFLINE: nothing here installs anything or starts the game. kl_fa_bots.py is called; its check() (and
kl_fa_bots_rt's) got one addition: a chain that forks is walked once per branch set, so every way is checked.

    python kl_fa_bots_dyn.py build <bots build folder> <out folder> [options]   plan + write + every check; exit 1 on a FAIL
    python kl_fa_bots_dyn.py plan  <bots build folder> [options]                the plan only (nothing written)
    python kl_fa_bots_dyn.py check <folder>                                     kl_fa_bots.check (+ kl_fa_bots_rt.check on a
                                                                                two-part map) + the checks of this module
    python kl_fa_bots_dyn.py diff  <bots build folder> <out folder>             what the step changed; exit 1 if anything
                                                                                but the squads' steps differs
    python kl_fa_bots_dyn.py covers <folder>                                    the cover boxes of a build and how the
                                                                                squad's places lie to them
    python kl_fa_bots_dyn.py summary <dynamic folder>                           the plan of a built folder (its dyn.json),
                                                                                one line a bot
    python kl_fa_bots_dyn.py map <folder> <out.png>                             a top view: mesh edges, cover boxes, each
                                                                                bot's places and holds (to LOOK at offline)
    python kl_fa_bots_dyn.py owner <work>\\build [M01 ...]                       y_loot2\\M01 M02 M03 M06 and
                                                                                rt_full4\\retomoto_full into z_dyn\\<map>
    python kl_fa_bots_dyn.py routes <work>\\build [M01 ...]                      z_gate\\M01, z_final\\M02 M03 M06 and
                                                                                rt_full6\\retomoto_full into z_route\\<map>
    options
      --no-random       every hold is ONE cover and is walked by the chain (Defend 'rout' -> Defend 'pos' -> timer);
                        default: where a bot has two or three covers at a hold, a RandomTrigger picks one per round
      --no-vision       no vision factor on the opening modifier (default eVIM_Factor_2_0, the Fragile Alliance police's)
      --sixth N         ASSUMPTION, off by default: ZSoldier 16 / 17 = N (the police rows have 800) and eCSS_Enabled on
                        the opening modifier: 'notices anybody within N without seeing him' (re/bots_dynamic.md 4)
      --no-rusher       the point man keeps attitude eStayBack (default: eUnleashed, stock F08's bots)
      --no-stagger      all seven start with Timer_start_bots, as before
      --no-detour       no bot is sent the other way round (default: Squad#04 where the mesh has a second way);
                        only with --no-routes: with the random routes the other way round is one of a fork's ways
      --ways N          most ways a fork chooses between (default 3; 2 = about a third fewer new entities)
      --no-routes       no fork of the way: every bot walks the build's places every round (the step as it was
                        before the random routes)
      --gap N           least path between two holds of a bot on the way in (default GAP_IN)
      --no-tree         as kl_fa_bots: the new groups are not listed in the root's group tree
      --keep-fake-targets   a FakeTarget that stands outside the vision space keeps its controller (default: taken
                        off - it is what wrote over the heap in the 0x686a66 crash; check FAILS a build that has one)
      --fork-gap S      a TriggerDelay2 of S seconds before every RandomTrigger (default 0 = none; commit 76bfdcd
                        had 0.1 as the default: say '--fork-gap 0.1', or opt {'fork_gap': 0.1} to build(), for
                        that form - the build log says which it made. Both forms have run in the game.)
    python kl_fa_bots_dyn.py fake-test <M01 build> <a Retomoto build with the parked vans> [...]
                                                                                the FakeTarget rule against the two facts
                                                                                known from the running game (the grid of
                                                                                the M01 dump, 'no record' for the parked
                                                                                van) + a lattice; exit 1 if one fails or
                                                                                a control did not run
    python kl_fa_bots_dyn.py fake-fix <build folder> <out folder>               ONLY the FakeTargets outside the vision
                                                                                space taken off (the .prp member alone;
                                                                                the squads stay): for a build that is not
                                                                                to get the dynamic step; exit 1 on a FAIL
    python kl_fa_bots_dyn.py grid <folder> <96 hex digits | 12 floats | 6 floats>
                                                                                a grid read in the running game (the twelve
                                                                                floats at [0x1535c70] + 0x50) against the
                                                                                level's boxes: the one-load proof per map

WHAT A SQUAD'S CHAIN IS AFTERWARDS (each form's stock precedent: re/bots_dyn_build.md 2)
  Timer_start_bots -> 000_Timer_stagger (0 / 3 / 5 / 8 s) -> 001_SquadModifier_awake (eDM_Loose, vision x 2)
  -> NNN_DefendBehaviour_<leg> ('rout': 1..3 way places of the build, eDMS_NotSet)
     -> NNN_DefendBehaviour_pos_cover (ONE place 70..230 from a cover box, behind it as the bot walks) -> NNN_Timer_hold
     or -> [NNN_Timer_hold, NNN_RandomTrigger_cover -> one of NNN_DefendBehaviour_pos_cover_a / _b / _c (no NEXT)]
  -> NNN_RandomTrigger_way {0: 1, 1..3: weights by role, 5..7: the first step of each way} -> one of
       NNN_DefendBehaviour_way_a ...  (the build's own way places of this stretch, with its holds)
       NNN_DefendBehaviour_way_b ...  (another corridor of the mesh, or the build's way moved to the left / right)
       NNN_DefendBehaviour_way_c ...
     the last step of every way -> the step of the next fixed place (stock form: F07 Squad#02
     040_RandomTrigger_out_of_loot_area; a way without a step of its own names that step directly)
  -> ... -> NNN_SquadModifier_tight_defense_loot -> the loot place -> the build's own loot wait (seconds per bot)
  -> NNN_SquadModifier_Loose_defense -> ... the way out the same way, shorter holds -> the last 'rout' (eDMS_Sprint:
  the dash to the vehicle) -> the build's own last modifier (leashed, tight).
  KEPT as they are: the actors, the squad groups, every wait of the build (TriggerLootDepleted, the cases' timers and
  relays, a rally timer, TriggerActorsDead), the last modifier, the AllyEscapeBoxes, every place the old steps named
  (so every stage trigger, gate and park place is still walked, in the old order). REMOVED: the old Defend steps.
  A second chain (Retomoto's street route, started by the JumpPoint) is treated the same; its first step keeps its
  name, so the JumpPoint is not touched.
  ON A CHAIN THE JUMP CUTS OFF (Retomoto's tower) nothing of this module waits behind the table's loot wait: no hold,
  no timer - a timer that still runs when the human takes the join would start a tower step for a bot the hook has
  moved to the street. On a GATES build of kl_fa_bots_rt (2026-10-11, re/retomoto_bots_rooms.md) that is the whole
  way down: what this step adds there is the forks between two gates' holds (another way goes through no trigger
  box the build's way keeps out of, Routes.wakes_more, and past no post of an enemy the build's way keeps clear
  of, Routes.passes_more), the staggered starts and the opening modifier; the holds and the waits are the build's
  own. The build's own gate waits are the same hazard and are not this module's to
  remove: check() counts them and says so (the NOTE 'THE JOIN').

WHAT IS WRITTEN: .prp, .gms + .buf (entities added / removed inside the squad groups; REF ids of removed entities
  are reused), .oct / .rmi / .rmc (slot ids renumbered; the squad's groups re-listed in the root's group tree with
  the box of their places), .prm (only the 4-byte .oct record offsets in model roots, same size). No model, no
  animation, no sound, no shader: the four large blocks keep their size.
  ONE THING OUTSIDE THE SQUADS (2026-10-11, re/crash_686a66.md): a FakeTarget controller on an object that stands
  outside the vision space is taken off its node (.prp only). That object is what crashed the routes build of
  Retomoto at kl2 0x686a66 - not the forks: its update writes 16 bytes behind ZCheckVisible's table every frame.
  The vision space is read from the .rmi records of the rooms' bounds (FAKE TARGETS below; proven on one level).

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene
import kl_fa_bots as F
import kl_octree as O
import kl_prpjoin as J

R_ = F.R_
SX = 'F07'                      # the level the node forms are cloned from (kl_fa_bots.make uses the same)
FORM_SQ = R_ + F.SQUAD + 'Squad#02'
FORM = {'defend': FORM_SQ + '\\020_DefendBehaviour_rout_merc_fight_left',
        'pos': FORM_SQ + '\\020_DefendBehaviour_rout_merc_fight_left\\Pos#01',
        'mod': FORM_SQ + '\\040_SquadModifier_Loose_defense',
        'random': FORM_SQ + '\\060_RandomTrigger_BeforeStreet',
        'timer': R_ + F.SQUAD + 'Timer_start_bots'}

# ---- cover boxes (re/bots_dynamic.md 3.1: CFFCoverList, kl2 0x6d6a80, makes a cover of every ZSTDOBJ whose name
# matches *coverbox*, case ignored, unless its flag word has bit 0x400)
RING = (70.0, 230.0)    # a hold place lies this far from the middle of its cover box. Stock bots' hold places: median
                        # 165..291 from the nearest box, 54..94 % within 250 (re/bots_dynamic.md 2.1); DefendCover
                        # takes a cover within 500 of the defend position (kl2 0x84dc90). The lower bound is a GUESS
                        # (a box is a solid thing; the mesh is cut out round most of them anyway)
RING_BEST = 130.0       # GUESS: of the places of one box the one nearest to this distance (behind it) is taken
REACH = 900.0           # GUESS: a hold's cover box is at most this far from the route place the hold follows (650: 20 of 57 asks on M01 found one, 900: 33, 1200: 37)
REACH_Y = 260.0         # ... and within this height of it
HOLD_CLEAR = 35.0       # least distance of a hold place from a mesh edge without a neighbour (kl_fa_bots.check
                        # fails below 10; its planner wants 60, which beside a box is often not to be had)
HOLD_SEP = 100.0        # two hold places of one station are at least this far apart (stock bots: ~100, re/bots_squad.md 6)
HOLD_PATH = 1500.0      # GUESS: a hold place is at most this far to WALK from the route place before it
WARP = 15.0             # as kl_fa_bots_rt.WARP: no hold on a polygon whose fitted height is off by more
GAP_IN = 1300.0         # GUESS: least path between two holds of a bot on the way in (stock F07: a step every ~9 m,
                        # a 'pos' step every third; ours had none)
GAP_OUT = 1700.0        # GUESS: ... on the way out (the owner: 'move a bit more like the bots to the van')
BUDGET = (16.0, 85.0)   # sum of a bot's TriggerDelay2 seconds: what stock bots have (re/bots_dynamic.md 2.1)
# THE GAP BEFORE A FORK ('--fork-gap S'; OFF since 2026-10-11, re/crash_686a66.md): a TriggerDelay2 of S seconds between
# a Defend rout's arrival list and every RandomTrigger. It was written as an untested answer to the kl2 0x686a66 crash
# of the routes build (a ZDefendBehaviourGoal with a broken place list) on the thought that a fork starts the next
# Defend step from inside the old goal. The crash was NOT that: the list was never freed, 16 bytes of it were written
# over from outside (see FAKE TARGETS below). What is true of the thought: a RandomTrigger passes its message on at
# once, in the sender's stack (kl2 0x4d86e0), a TriggerDelay2 only arms and fires from its own update (0x71e250 /
# 0x744c30) - but the engine starts every next step from the old goal's last call anyway (0x5c6e70 -> 0x8df0d0), a
# Defend naming a Defend is stock's commonest link, and a goal is one object per rout that is never freed. So the
# form of the builds on the owner's tab stays the default (no gap). The timer form has run in the game since
# (2026-10-11 05:38-06:08, the lead's runs R7a / R7b / R7c_DM09 on z_route7\retomoto_full and C3_DM03 on
# z_cover3\M03: four clean rounds) - it does no harm that was seen and mends nothing: z_route7 still had the two
# parked FakeTargets, so the write was there in all three of its rounds. build() says in its log which form it made
# (another module, kl_fa_cover, builds through here with this default).
FORK_GAP = 0.0
# FAKE TARGETS OUTSIDE THE VISION SPACE (the cause of the 0x686a66 crash; re/crash_686a66.md). ZFakeTarget's update
# (kl2 0x560630, every frame) registers with ZCheckVisible (0x55cc40 -> 0x59c790) and then ALWAYS writes its cell and
# place into its record (0x7143f0). 0x59c790 answers 0xff for a place outside the grid of 16 x 1 x 16 cells that
# 0x541e40 lays over the rooms - and record 0xff of a table of 200 lies 0x5a8 bytes BEHIND the ZCheckVisible
# object: 16 bytes of whatever the heap has there are overwritten every frame. kl_fa_street parks Retomoto's two
# spare vans 600 m under the road with the FakeTarget 'Mercenary' on their bodies.
# WHAT THE GRID LIES OVER (kl2 0x541e40, read 2026-10-11; the first form of this rule took the items of the root's
# room tree instead - those are the rooms' CONTENTS, 7,300 to 12,400 wider than the engine's box on M01, and under
# the engine's own arithmetic that box would have let the parked vans register: re/crash_686a66_review.md D1):
#   a pre-order walk of the WHOLE scene (0x883840) takes every object of a ZROOM-derived class but the root, a
#   hidden one (slot flags & 0x400), one named *backdrop* (0x7472b0: a search without case) and one whose vtable
#   +0x2fc answers true (bit 2 of the dword at +0x118: 0 from the constructor 0x545150, and the only other writer,
#   the setter 0x6b81e0, is called for rooms with bit 0 alone - no code was found that sets it); a room named
#   *VisionSpaceBox* is the box alone and ends the walk (no stock level and no build has one). A room with a list at
#   +0x38 gives the box of every object of that list, a room without gives its own slot's (0x44a010 -> 0x8849b0:
#   centre -/+ the half extents turned into world axes, 0x7d8460).
#   OFFLINE that list is the room's ZBOUND children and the boxes are the records of the .rmi ('InsideBound_NN'; one
#   record per bound, +0x28 centre, +0x34 the bound's own place, +0x40 half extents; a room without bounds has one
#   record of its own with +0x34 = 0; some rooms of either kind have no record at all; no room of 14 levels has
#   bounds and another number of records).
#   PROOF, one level: the dump of 2026-10-08 20:05 (M01_FA_A) holds ZCheckVisible's grid, and its lo and hi are the
#   union of M01's bound records bit for bit on all six floats (GRID_M01; 'fake-test').
# TWO BOXES are therefore read (vision_space): 'sure' = the records of rooms whose records are their ZBOUND children
# (the kind the dump proves), 'all' = those and the one-record rooms without bounds (ASSUMPTION that such a record is
# the room's own slot box: Retomoto's 'all' is twice as wide as its 'sure'). NOT KNOWN offline: the box of a room
# that the walk takes and the .rmi has no record for (Retomoto 2, Late Night Opening 1, the bank 1, stock F02 F03
# F05 F06 F07 F08 F09) - so the engine's box is 'sure' or larger, never smaller.
# THE RULE (check): the place a FakeTarget registers at (its node's, 140 higher: 0x55cc40) must lie inside 'sure',
# EDGE clear of its faces. Inside 'sure' it registers under every reading (a larger box only makes the cells
# larger); the engine's own arithmetic is looser (it truncates toward zero and keeps the low byte, so a place up to
# one cell under lo, or 256 cells away, also gets a cell) and is printed beside it, not relied on. The build step
# takes the controller of a FakeTarget that fails off (nothing in kl2.exe asks an object for its FakeTarget: the
# class info 0x168e3d4 is named by its own registration only) - '--keep-fake-targets' leaves it.
VISION_SKIP = 'backdrop'        # kl2 0x541f0e: a room named *backdrop* is not joined
VISION_ALONE = 'visionspacebox'  # kl2 0x541eeb: a room of that name is the box alone
PROBE_UP = 140.0                # kl2 0x55cc40 adds 140.0 (the double at 0xb45358) to y before it asks for a record
EDGE = 1.0                      # GUESS: a place this near a face of the box is not called inside (the cell is float32)
NO_CELL = 0xff                  # what 0x59c790 answers, and the index 0x560630 then writes with
# The two facts from the running game the reading is held against ('fake-test'):
# 1. ZCheckVisible's grid ([0x1535c70] + 0x50: cell size, 1 / cell size, lo, hi - twelve floats) in the dump
#    %TEMP%\kl_triage\20261008_200513\KLHook_2.dmp, the whole-level conversion of M01_FA_A (no DebugRoom in it).
GRID_M01 = ('3bc2614502c08f4629764a45' '6825913986f3633817d9a139' 'f4009ec6400048c3cacef745' 'c1c1124701308e4602706947')
GRID_M01_ROOM = 'M01FAA_Out_Street_02a'     # a level with this room is held against GRID_M01
# 2. record 0xff in the dump of the crash (%TEMP%\kl_triage\20261011_013427\KLHook_2.dmp, 0x7d73f738): 'no cell' and
#    the place of the FakeTarget on Retomoto's parked van 02 - that target could NOT register in the game.
PARKED_RT = (-3216.61, -60040.02, 3419.27)
ALTS = 3                # most covers a RandomTrigger chooses between (stock bots: 2 lists 147 x, 3 lists 42 x, 4 14 x)

# ---- the seven. Every number is a value stock gives a bot (timers: 3 4 5 6 8 10 12 15; loot seconds 15 20 60;
# modifiers Loose / Tight / Leash+Tight; attitude eUnleashed: F08's seven; accuracy 90: F05's seven) - which bot
# gets which is OURS (re/bots_dyn_build.md 3). prefer: which cover of the ones in reach (ahead / behind along the
# way, to one side or the other, the nearest).
Pers = collections.namedtuple('Pers', 'role stagger hold_in hold_out prefer phase loot attitude accuracy after sprint out_holds')
PERS = {2: Pers('point man', 0.0, 5.0, 4.0, 'ahead', 0.5, 'short', 'eUnleashed', None, 'loose', 1, True),
        3: Pers('looter', 3.0, 8.0, 6.0, 'near', 1.0, 'long', None, None, 'loose', 1, True),
        4: Pers('flanker (one side)', 3.0, 8.0, 6.0, 'side+', 0.75, 'map', None, None, 'loose', 1, True),
        5: Pers('flanker (other side)', 5.0, 8.0, 6.0, 'side-', 1.25, 'map', None, None, 'loose', 1, True),
        6: Pers('second looter', 5.0, 10.0, 8.0, 'near', 0.5, 'long', None, None, 'loose', 1, True),
        7: Pers('rear guard', 8.0, 12.0, 8.0, 'behind', 1.0, 'map', None, 90.0, 'leash', 1, True),
        8: Pers('runner', 0.0, 4.0, 0.0, 'near', 1.5, 'short', None, None, 'loose', 2, False)}
ORDER = (2, 7, 4, 5, 3, 6, 8)   # who chooses his cover first at a station
LOOT_SHORT = 15         # TriggerLootDepleted field 1 of the point man and the runner (stock: 15, 20, 60)
LOOT_LONG = (15, 60)    # the looters: the build's own seconds + 15, at most 60
DETOUR = 'side+'        # the bot (by its cover preference) that takes the other way round where the mesh has one
DEFAULTS = {'random': True, 'vision': True, 'sixth': 0.0, 'rusher': True, 'stagger': True, 'gap': GAP_IN, 'tree': True, 'detour': True,
            'routes': True, 'ways': None, 'fork_gap': FORK_GAP, 'fake': True}

NEXT = {'DefendBehaviourRout': 7, 'SquadModifierBehaviour': 26, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerActorsDead': 2}
BS = '\\'


def hdist(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def unit2(dx, dz):
    n = math.hypot(dx, dz)
    return (dx / n, dz / n) if n > 1e-6 else (0.0, 0.0)


# ------------------------------------------------------------------ the mesh, with a grid over it
class Grid:
    """kl_fa_bots.Nav's at() and clearance() through a grid of cells (the same answers; Nav's own walk every
    polygon and every wall for each question)."""
    CELL = 400.0

    def __init__(self, nav):
        self.nav = nav
        c = self.CELL
        self.polys, self.walls = collections.defaultdict(list), collections.defaultdict(list)
        for i, b in enumerate(nav.box):
            if nav.ok[i]:
                for cx in range(int(b[0] // c), int(b[1] // c) + 1):
                    for cz in range(int(b[2] // c), int(b[3] // c) + 1):
                        self.polys[(cx, cz)].append(i)
        for w in nav.walls:
            for cx in range(int(min(w[0], w[2]) // c), int(max(w[0], w[2]) // c) + 1):
                for cz in range(int(min(w[1], w[3]) // c), int(max(w[1], w[3]) // c) + 1):
                    self.walls[(cx, cz)].append(w)
        self._warp = {}

    def at(self, x, y, z, dy=F.DY, part=None):
        nav, best = self.nav, None
        for i in self.polys.get((int(x // self.CELL), int(z // self.CELL)), ()):
            b = nav.box[i]
            if b[0] <= x <= b[1] and b[2] <= z <= b[3] and (part is None or nav.part[i] == part) and nav.inside(i, x, z):
                h = nav.height(i, x, z)
                if abs(h - y) <= dy and (best is None or abs(h - y) < abs(best[1] - y)):
                    best = (i, h)
        return best

    def clearance(self, x, y, z, limit=400.0):
        c, best, seen = self.CELL, limit, set()
        for cx in range(int((x - limit) // c), int((x + limit) // c) + 1):
            for cz in range(int((z - limit) // c), int((z + limit) // c) + 1):
                for w in self.walls.get((cx, cz), ()):
                    if id(w) in seen:
                        continue
                    seen.add(id(w))
                    x0, z0, x1, z1, wy = w
                    if abs(wy - y) > 150.0:
                        continue
                    dx, dz = x1 - x0, z1 - z0
                    L = dx * dx + dz * dz
                    t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((x - x0) * dx + (z - z0) * dz) / L))
                    best = min(best, math.hypot(x - x0 - t * dx, z - z0 - t * dz))
        return best

    def warp(self, i):
        if i not in self._warp:
            nav = self.nav
            self._warp[i] = max(abs(nav.height(i, v[0], v[2]) - v[1]) for v in nav.pv[i])
        return self._warp[i]


# ------------------------------------------------------------------ a bots build, read
class Ctx:
    """A bots build with everything the plan and the checks ask of it."""

    def __init__(self, folder, log=print):
        self.B = B = F.Built(folder)
        self.folder = B.folder
        bj = os.path.join(B.folder, 'bots.json')
        self.bots_json = json.load(open(bj)) if os.path.isfile(bj) else {}
        popt = self.bots_json.get('plan', {}).get('options', {})
        self.links = bool(popt.get('drop'))             # as kl_fa_bots.check: walk the mesh's links when the build has a drop
        self.nav = F.Nav(B.scene.nav, links=self.links)
        self.grid = Grid(self.nav)
        self.S = F.stations(B, self.nav)
        self.home = self.S['home']
        self.exits = self.S['exits']
        self.lane = F.lanes(B)
        self.hops = {(tuple(pa), tuple(pb)) for ds in self.nav.drops.values() for _j, pa, pb, _k in ds}
        self.ally = [k for k, _i, _v in kl_fa.controllers(B.sc, 'AllyEscapeBox')]
        self.covers = cover_boxes(B)
        self._spots, self._dm = {}, {}
        self.rt = None
        self.squads, self.timer, self.outside = parse(self)
        if any(len(q['chains']) > 1 for q in self.squads.values()):
            import kl_fa_bots_rt as RT                  # a map of two navigation parts (Retomoto): its lane, its checks
            self.rt = RT

    # -- places
    def p4(self, p, dy=15.0):
        """(x, mesh height, z, polygon) of a place on the mesh, or None."""
        hit = self.grid.at(p[0], p[1], p[2], dy)
        return hit and (p[0], hit[1], p[2], hit[0])

    def dist_from(self, a):
        key = (round(a[0], 1), round(a[2], 1), a[3])
        if key not in self._dm:
            if len(self._dm) > 400:
                self._dm.clear()
            self._dm[key] = self.nav.dist_map(a[3], a[:3])
        return self._dm[key]

    def walk(self, a, b):
        """(points, length, goes over a link) of the mesh path a -> b (both 4-tuples), or None."""
        got = self.nav.path(a, b)
        if got is None:
            return None
        hop = any((tuple(u), tuple(w)) in self.hops for u, w in zip(got[0], got[0][1:]))
        return got[0], got[1], hop

    def spots(self, ci):
        """The places round cover box ci a bot can be told to hold: [(x, y, z, polygon, clearance)]."""
        if ci not in self._spots:
            c, out, g = self.covers[ci]['at'], [], self.grid
            k = int(RING[1] // 40) + 1
            for ix in range(-k, k + 1):
                for iz in range(-k, k + 1):
                    x, z = c[0] + ix * 40.0, c[2] + iz * 40.0
                    if not RING[0] <= math.hypot(x - c[0], z - c[2]) <= RING[1]:
                        continue
                    hit = g.at(x, c[1], z, REACH_Y)
                    if hit and g.warp(hit[0]) <= WARP:
                        cl = g.clearance(x, hit[1], z)
                        if cl >= HOLD_CLEAR:
                            out.append((x, hit[1], z, hit[0], cl))
            self._spots[ci] = out
        return self._spots[ci]


def cover_boxes(B):
    """The objects kl2 0x6d6a80 makes covers of: ZSTDOBJ, name *coverbox*, flag bit 0x400 clear -> [dict]."""
    sc, out = B.sc, []
    for k in range(1, len(sc.nodes)):
        low = sc.names[k].lower()
        if 'coverbox' not in low or sc.cls(k) != 'ZSTDOBJ':
            continue
        kind = 'car' if 'coverboxcar' in low else 'low' if ('coverboxm' in low or 'coverboxl' in low) else 'high' if 'coverboxh' in low else None
        if kind is None:
            continue
        out.append({'node': k, 'at': B.at(k), 'kind': kind, 'hidden': bool(B.ents[k - 1].flags & 0x400)})
    return out


def _f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def _record_box(raw):
    """One .rmi record -> (centre, half extents in world axes at their largest, at their smallest). An axis-aligned
    record (+0 = 1) is centre -/+ half as it stands. A turned one (+0 = 0, matrix at +4; stock F09, the park) has
    the half extents |matrix| x half, as kl2 0x7d8460 forms a slot's; whether the record's matrix is that one or
    its transpose is NOT established, so both are formed and the 'sure' box takes the smaller per axis."""
    c, h = struct.unpack_from('<3f', raw, 0x28), struct.unpack_from('<3f', raw, 0x40)
    if struct.unpack_from('<I', raw, 0)[0]:
        return c, h, h
    m = struct.unpack_from('<9f', raw, 4)
    r1 = [sum(abs(m[3 * r + a]) * h[r] for r in range(3)) for a in range(3)]
    r2 = [sum(abs(m[3 * a + r]) * h[r] for r in range(3)) for a in range(3)]
    return c, [max(x, y) for x, y in zip(r1, r2)], [min(x, y) for x, y in zip(r1, r2)]


def vision_space(B):
    """The box ZCheckVisible lays its grid over (kl2 0x541e40; FAKE TARGETS at the top), as far as the level files
    give it -> dict, or None when no room has a record that can be relied on:
      'sure'   (lo, hi, records): the .rmi records that name a ZBOUND child of their room (+0x34 = its place) -
               the kind the dump of M01 proves bit for bit. The engine's box is this or larger.
      'all'    (lo, hi, records): 'sure' and the single records of rooms without bounds (ASSUMPTION: such a
               record is the room's own slot box, which is what the engine joins for a room without a list).
      'own'    names of the rooms counted in 'all' only;  'unknown' names of rooms the walk takes that have no
               record (the engine joins a box for them that is not read here);
      'skipped' {'backdrop': names, 'hidden': names};  'alone' the name of a *VisionSpaceBox* room, if any (its box
               is the room's own slot box and it ends the walk: then nothing is 'sure' and None is returned).
    lo and hi are float32, centre - half and centre + half as kl2 0x44a010 forms them."""
    sc, sch = B.sc, J.schema('dd')
    slots = B.scene.slots()
    by_id = {slots[e] + 2: k + 1 for k, e in enumerate(B.ents) if e in slots}
    per = collections.defaultdict(list)
    for b in O.RoomIndex.parse(B['.rmi']).boxes:
        per[by_id.get(b.room)].append(b)
    roomish = lambda k: 'ZROOM' in sch.bases(sc.cls(k) or '')
    box = {'sure': None, 'all': None}
    out = {'own': [], 'unknown': [], 'skipped': {'backdrop': [], 'hidden': []}, 'alone': None, 'rooms': 0}

    def join(key, c, h):
        lo, hi, n = box[key] or ([1e38] * 3, [-1e38] * 3, 0)
        box[key] = ([min(lo[a], _f32(c[a] - h[a])) for a in range(3)], [max(hi[a], _f32(c[a] + h[a])) for a in range(3)], n + 1)

    for k in range(1, len(sc.nodes)):                   # scene order = the engine's pre-order walk
        if not roomish(k):
            continue
        name, low = sc.names[k], sc.names[k].lower()
        if B.ents[k - 1].flags & 0x400:
            out['skipped']['hidden'].append(name); continue
        if VISION_ALONE in low:
            out['alone'] = name
            return None
        if VISION_SKIP in low:
            out['skipped']['backdrop'].append(name); continue
        out['rooms'] += 1
        bounds = [B.at(b) for b in range(k + 1, sc.end[k]) if sc.parent[b] == k and sc.cls(b) == 'ZBOUND']
        recs = per.get(k, [])
        if not recs:
            out['unknown'].append(name); continue
        for b in recs:
            c, big, small = _record_box(b.raw)
            join('all', c, big)
            # a bound's record names its bound: +0x34 is the ZBOUND child's place (582 of 582 records of rooms with
            # bounds on 14 levels, and where +0x50 holds a second slot id it is that child's, 59 of 59; a room's
            # own record has 0, 0, 0 there: 53 of 53). Only such a record is 'sure'.
            at = struct.unpack_from('<3f', b.raw, 0x34)
            if len(bounds) == len(recs) and any(math.dist(at, q) <= 1.0 for q in bounds):
                join('sure', c, small)
            elif name not in out['own']:
                out['own'].append(name)
    if box['sure'] is None:
        return None
    out.update(sure=tuple(tuple(x) if isinstance(x, list) else x for x in box['sure']),
               all=tuple(tuple(x) if isinstance(x, list) else x for x in box['all']))
    return out


def grid_cell(lo, hi, p):
    """kl2's own arithmetic for the cell of place p in a grid over lo..hi -> ((x, y, z) as the three bytes it
    forms, True when 0x59c790 would give a record). The grid (tail of 0x541e40): 16 cells in x and z, ONE in y,
    cell size and 1 / cell size kept as float32. The cell (0x59c790, 0x79bae0): (BYTE) ftol((p - lo) / size) with
    ftol = 0xa8d330 = cvttsd2si, a truncation TOWARD ZERO - so a place up to one cell under lo gets cell 0, and only
    the low byte is tested (x <= 15, y == 0, z <= 15)."""
    size = (_f32((hi[0] - lo[0]) * 0.0625), _f32(hi[1] - lo[1]), _f32((hi[2] - lo[2]) * 0.0625))
    c = []
    for a in range(3):
        v = (_f32(p[a]) - lo[a]) * _f32(1.0 / size[a]) if size[a] else 1e30
        c.append(int(v) & 0xff if abs(v) < 2.0 ** 31 else 0)       # cvttsd2si out of range: 0x80000000, low byte 0
    return tuple(c), c[0] <= 15 and c[1] == 0 and c[2] <= 15


def grid_floats(lo, hi):
    """The twelve floats ZCheckVisible keeps at +0x50 for a box lo..hi (cell size, 1 / cell size, lo, hi), as bytes."""
    size = (_f32((hi[0] - lo[0]) * 0.0625), _f32(hi[1] - lo[1]), _f32((hi[2] - lo[2]) * 0.0625))
    return struct.pack('<12f', *size, *[1.0 / s for s in size], *lo, *hi)


def outside(space, p):
    """How far the place a FakeTarget at p registers at (PROBE_UP higher) lies outside the 'sure' box per axis,
    EDGE counted; None when it is inside (or there is no space)."""
    if not space:
        return None
    lo, hi = space['sure'][0], space['sure'][1]
    q = (p[0], p[1] + PROBE_UP, p[2])
    ex = tuple(max(lo[a] + EDGE - q[a], q[a] - (hi[a] - EDGE), 0.0) for a in range(3))
    return ex if any(ex) else None


def fake_targets(B, space=None):
    """Every FakeTarget of the level -> [dict]: node, index of the controller in the node's list, path (without
    ROOT), place, 'out' = how far the place it registers at lies outside the 'sure' box per axis (None: inside, or
    no space could be read), 'cell' / 'cell_sure' = what kl2's own arithmetic makes of that place on the 'all' and
    the 'sure' box ((bytes), registers). The place is the node's own, as the level starts: a FakeTarget that cannot
    register THEN writes behind ZCheckVisible's table every frame until it has moved into the grid."""
    space = space if space is not None else vision_space(B)
    out = []
    for k, i, v in kl_fa.controllers(B.sc, 'FakeTarget'):
        p = B.at(k)
        q = (p[0], p[1] + PROBE_UP, p[2])
        out.append({'node': k, 'ctrl': i, 'path': B.sc.path[k][5:], 'at': tuple(p), 'team': v[0] if v else None, 'out': outside(space, p),
                    'cell': grid_cell(space['all'][0], space['all'][1], q) if space else None,
                    'cell_sure': grid_cell(space['sure'][0], space['sure'][1], q) if space else None})
    return out


def space_words(space):
    """The two boxes in one line."""
    if not space:
        return 'the vision space cannot be read (no room has a record for each of its bounds, or a VisionSpaceBox room)'
    s, a = space['sure'], space['all']
    return ('vision space: the %d bound records of %d rooms x %d..%d y %d..%d z %d..%d (the kind the M01 dump proves; the rule\'s box); with %d '
            'room(s) counted by a record of their own x %d..%d y %d..%d z %d..%d (ASSUMPTION); %d room(s) without a record, their box not read (%s)'
            % (s[2], space['rooms'] - len(space['own']) - len(space['unknown']), s[0][0], s[1][0], s[0][1], s[1][1], s[0][2], s[1][2],
               len(space['own']), a[0][0], a[1][0], a[0][1], a[1][1], a[0][2], a[1][2], len(space['unknown']), ', '.join(space['unknown']) or '-'))


def fake_test(folders, log=print):
    """The tests of the FakeTarget rule against what is KNOWN from the running game -> True when every one that
    applies to the folders holds and both controls ran at least once:
      1. GRID: a level with the room GRID_M01_ROOM - the 'sure' box and the grid floats formed from it must be the
         twelve floats of GRID_M01 bit for bit.
      2. PARKED: a level with a FakeTarget at PARKED_RT - kl2's own arithmetic must give 'no record' for it on the
         'sure' AND on the 'all' box (the game did), and the rule must fail it.
      3. LATTICE, on every folder: of 31 x 31 x 31 places over three times the 'all' box, none may pass the rule
         that kl2's arithmetic gives no record on either box (the first form of the rule passed a van 400 m above
         the road, 200 m east of the tower and 600 m up the road: re/crash_686a66_review.md D1). This one only
         holds outside() against grid_cell() on the boxes as read; a WRONG box is what 1 and 2 are for."""
    good, ran = True, collections.Counter()
    want = struct.unpack('<12f', bytes.fromhex(GRID_M01))
    for folder in folders:
        B = F.Built(folder)
        space = vision_space(B)
        log('%s' % folder)
        if space is None:
            log('  FAIL %s' % space_words(space))
            good = False
            continue
        log('  ' + space_words(space))
        s, a = space['sure'], space['all']
        if any(B.sc.names[k] == GRID_M01_ROOM for k in range(1, len(B.sc.nodes))):
            got = grid_floats(s[0], s[1])
            ok = got == bytes.fromhex(GRID_M01)
            good, ran['grid'] = good and ok, ran['grid'] + 1
            log('  %s GRID: the \'sure\' box lo (%r, %r, %r) hi (%r, %r, %r)' % ('ok  ' if ok else 'FAIL', *s[0], *s[1]))
            log('       the game\'s (dump 2026-10-08)  lo (%r, %r, %r) hi (%r, %r, %r); the twelve floats %s'
                % (*want[6:9], *want[9:12], 'bit for bit' if ok else 'DIFFER: %s against %s' % (got.hex(), GRID_M01)))
        fts = fake_targets(B, space)
        for f in fts:
            if math.dist(f['at'], PARKED_RT) > 1.0:
                continue
            ok = not f['cell'][1] and not f['cell_sure'][1] and f['out'] is not None
            good, ran['parked'] = good and ok, ran['parked'] + 1
            log('  %s PARKED: %s at (%.1f, %.1f, %.1f): kl2\'s arithmetic gives cell %s on the \'all\' box (%s), %s on the \'sure\' box (%s); '
                'the game: no record (0xff); the rule: %s' % ('ok  ' if ok else 'FAIL', f['path'].split(BS)[0], *f['at'], f['cell'][0],
                'a record' if f['cell'][1] else 'no record', f['cell_sure'][0], 'a record' if f['cell_sure'][1] else 'no record',
                'outside by (%d, %d, %d)' % f['out'] if f['out'] else 'INSIDE'))
        n = bad = 0
        steps = [i / 10.0 for i in range(-10, 21)]          # -1 .. 2 box widths: 31 x 31 x 31 places
        for fx in steps:
            for fy in steps:
                for fz in steps:
                    q = tuple(a[0][i] + fr * (a[1][i] - a[0][i]) for i, fr in enumerate((fx, fy, fz)))
                    p = (q[0], q[1] - PROBE_UP, q[2])
                    r_all, r_sure, rule_in = grid_cell(a[0], a[1], q)[1], grid_cell(s[0], s[1], q)[1], outside(space, p) is None
                    n += 1
                    if rule_in and not (r_all and r_sure):
                        bad += 1
        ok = not bad
        good, ran['lattice'] = good and ok, ran['lattice'] + 1
        log('  %s LATTICE: %d places over three times the box: %d the rule passes although kl2\'s arithmetic gives no record on one of the boxes'
            % ('ok  ' if ok else 'FAIL', n, bad))
        for f in fts:
            log('       FakeTarget %s at (%.1f, %.1f, %.1f): %s; kl2\'s arithmetic: cell %s (%s)' % (f['path'].split(BS)[0], *f['at'],
                'outside by (%d, %d, %d) - the rule FAILS it' % f['out'] if f['out'] else 'inside', f['cell'][0], 'a record' if f['cell'][1] else 'no record'))
    whole = True
    for key, what in (('grid', 'a level with the room %s (the grid of the 2026-10-08 dump)' % GRID_M01_ROOM),
                      ('parked', 'a level with the FakeTarget of the 0x686a66 dump at (%.1f, %.1f, %.1f)' % PARKED_RT)):
        if not ran[key]:
            log('NOT RUN: %s is not among the folders' % what)
            whole = False
    log('RESULT (fake-test): %s (grid control %d, parked control %d, lattice %d)'
        % ('FAIL' if not good else 'PASS' if whole else 'INCOMPLETE - nothing failed, but a control did not run', ran['grid'], ran['parked'], ran['lattice']))
    return good and whole


def grid_compare(folder, text, log=print):
    """A grid read in the running game (the twelve floats at [0x1535c70] + 0x50: 96 hex digits, or twelve numbers,
    or six = lo and hi) against the boxes read from the level -> True when 'sure' or 'all' is that grid's box."""
    words = text.replace(',', ' ').split()
    if len(words) == 1 and len(words[0]) == 96:
        fl = struct.unpack('<12f', bytes.fromhex(words[0]))
    else:
        fl = tuple(_f32(float(w)) for w in words)
    if len(fl) not in (6, 12):
        raise ValueError('twelve floats (cell, 1 / cell, lo, hi), their 96 hex digits, or six (lo, hi)')
    lo, hi = fl[-6:-3], fl[-3:]
    space = vision_space(F.Built(folder))
    log(space_words(space))
    log('the game\'s grid: lo (%r, %r, %r) hi (%r, %r, %r)' % (*lo, *hi))
    hit = False
    for key in ('sure', 'all') if space else ():
        b = space[key]
        d = [b[0][i] - lo[i] for i in range(3)] + [b[1][i] - hi[i] for i in range(3)]
        same = tuple(b[0]) == tuple(lo) and tuple(b[1]) == tuple(hi)
        hit = hit or same
        log('  \'%s\': %s' % (key, 'the same six floats, bit for bit' if same else 'differs by lo (%+.4f, %+.4f, %+.4f) hi (%+.4f, %+.4f, %+.4f)' % tuple(d)))
    log('RESULT (grid): %s' % ('the level\'s box is the game\'s' if hit else 'NEITHER box is the game\'s - the reading is wrong for this level (say so in re/crash_686a66.md)'))
    return hit


def parse(ctx):
    """The squads of the build -> ({N: squad}, node of Timer_start_bots, [(holder path, field, target path)] of the
    references into a squad from outside it). A squad: top, group (the actor's), actor, name, chains [chain];
    a chain: entry ('timer' or the path that names it from outside), elems [dict] in the order the chain runs."""
    B, sc = ctx.B, ctx.B.sc
    tops = [t for t in sc.tops() if sc.names[t].startswith(F.SQUAD)]
    mine = {k for t in tops for k in range(t, sc.end[t])}
    timer = sc.resolve(R_ + F.SQUAD + 'Timer_start_bots')
    if len(timer) != 1:
        raise ValueError('%s: no %sTimer_start_bots: not a bots build' % (ctx.folder, F.SQUAD))
    timer = timer[0]
    ctrl_of = {}
    for cn in NEXT:
        for k, i, v in kl_fa.controllers(sc, cn):
            if k in mine and k != timer:
                ctrl_of[k] = (cn, v, i)
    relay_of = {k for k, _i, _v in kl_fa.controllers(sc, 'RelayMessageList') if k in mine}
    if any(k in mine for k, _i, _v in kl_fa.controllers(sc, 'RandomTrigger')) or sc.resolve(R_ + F.SQUAD + 'Squad#02\\001_SquadModifier_awake'):
        raise ValueError('%s: the squad already has the steps of this module (build from the bots build, not from its result)' % ctx.folder)
    firsts = [j for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if k == timer for s in v[4] for j in sc.resolve(s)]
    # kl_fa_bots_rt's room-first build (2026-10-11): Timer_start_bots names one TriggerCounter gate (also fed by the
    # boardroom's counter) and the gate names the seven first steps - look through it.
    gates = {k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if k in mine}
    if firsts and all(j in gates for j in firsts):
        firsts = [j for g in firsts for s in gates[g][4] for j in sc.resolve(s)]
    squads = collections.OrderedDict()
    for t in tops:
        actors = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        if not actors:
            continue
        g = sc.parent[actors[0]]
        N = int(sc.names[g][18])
        squads[N] = {'N': N, 'top': t, 'group': g, 'actor': actors[0], 'name': sc.names[t], 'chains': [], 'at': B.at(actors[0])}
    by_top = {q['top']: q for q in squads.values()}
    outside = []
    entries = collections.defaultdict(list)
    for k in firsts:
        entries[sc.top[k]].append(('timer', k))
    for k, holder, field, s, hit in J.references(sc):
        if k < 0 or k in mine or not hit:
            continue
        for j in hit:
            if sc.top[j] in by_top and j in ctrl_of:
                outside.append((sc.path[k], '%s %s' % (holder, field), sc.path[j]))
                entries[sc.top[j]].append((sc.path[k], j))
    for t, q in by_top.items():
        seen = set()
        for entry, k in entries.get(t, []):
            if k in seen:
                continue
            elems = []
            while k is not None and k not in seen:
                seen.add(k)
                if k not in ctrl_of:
                    raise ValueError('%s: the chain reaches %s, which is no step' % (q['name'], sc.names[k]))
                cn, v, ci = ctrl_of[k]
                nx = [j for s in v[NEXT[cn]] for j in sc.resolve(s)]
                also = [sc.path[j] for j in nx if j in relay_of]
                nx = [j for j in nx if j in ctrl_of]
                e = {'k': k, 'name': sc.names[k], 'ctrl': cn}
                if cn == 'DefendBehaviourRout':
                    pl = [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in sc.resolve(s)]
                    e.update(kind='defend', places=pl, pts=[B.at(j) for j in pl], sprint=v[4] == 'eDMS_Sprint')
                elif cn == 'TriggerDelay2':
                    e.update(kind='timer', seconds=v[0], also=also, cases=bool(also), loot='done_looting' in sc.names[k])
                elif cn == 'TriggerLootDepleted':
                    e.update(kind='loot', seconds=v[1], objects=len(v[0]))
                elif cn == 'TriggerActorsDead':
                    e.update(kind='dead')
                else:
                    e.update(kind='mod', leash=v[0], defend=v[9])
                elems.append(e)
                if len(nx) > 1:
                    raise ValueError('%s: %s names %d steps: not a chain kl_fa_bots made' % (q['name'], sc.names[k], len(nx)))
                k = nx[0] if nx else None
            if not any(e['kind'] == 'defend' for e in elems):
                raise ValueError('%s: the chain from %s has no route step' % (q['name'], entry))
            q['chains'].append({'entry': entry, 'elems': elems})
        if not q['chains'] or q['chains'][0]['entry'] != 'timer':
            raise ValueError('%s: Timer_start_bots does not start it' % q['name'])
        old = {e['k'] for c in q['chains'] for e in c['elems']}
        loose = [sc.names[k] for k in ctrl_of if sc.top[k] == t and k not in old]
        if loose:
            raise ValueError('%s: steps no chain reaches: %s' % (q['name'], loose[:4]))
    if sorted(squads) != list(F.BOTS):
        raise ValueError('%s: squads %s (wanted 2..8)' % (ctx.folder, sorted(squads)))
    return squads, timer, outside


# ------------------------------------------------------------------ the plan
def in_any_exit(ctx, p):
    return bool(F.in_exit(ctx.B, ctx.exits, p))


def hold_ok(ctx, part, e, q, nxt, post, why=None):
    """May a bot that has reached route place e (4-tuple) be told to hold at q before it walks on to nxt?
    The rules kl_fa_bots.check (and kl_fa_bots_rt.check) put on a route place, on the hold place and on the way
    to and from it; `post` = e lies behind the last loot wait."""
    nav, B = ctx.nav, ctx.B
    say = (lambda s: why.append(s)) if why is not None else (lambda s: None)
    hit = nav.at(q[0], q[1], q[2], dy=15.0)
    if hit is None or nav.part[hit[0]] != part:
        say('not on the route\'s mesh part'); return False
    if nav.clearance(q[0], q[1], q[2]) < HOLD_CLEAR - 0.5 or ctx.grid.warp(hit[0]) > WARP:
        say('edge or warped polygon'); return False
    q4 = (q[0], q[1], q[2], hit[0])
    a = ctx.walk(e, q4)
    if a is None or a[2] or a[1] > min(HOLD_PATH, 2.2 * hdist(e, q) + 300.0):
        say('no short way to it'); return False
    if nxt is not None:
        b = ctx.walk(q4, nxt)
        if b is None or b[2]:
            say('no way on from it'); return False
        d = ctx.walk(e, nxt)
        if d is not None and b[1] > d[1] + HOLD_PATH:
            say('a long way on from it'); return False
    if ctx.exits:
        # never inside a level exit box earlier than the route itself is (a bot in one calls the vehicle: kl2 0x6cd8e0)
        if not in_any_exit(ctx, e[:3]):
            pts = [e, q4] + ([nxt] if nxt is not None and not in_any_exit(ctx, nxt[:3]) else [])
            if in_any_exit(ctx, q[:3]) or F.first_exit_entry(B, nav, ctx.exits, pts):
                say('in or through a level exit box'); return False
    if ctx.lane:
        if F.lane_dist(ctx.lane, q) < F.LANE_CLEAR:
            say('in the escape vehicle\'s road'); return False
        if post and (F._crosses(ctx.lane, e, q) or (nxt is not None and not F._crosses(ctx.lane, e, nxt) and F._crosses(ctx.lane, q, nxt))):
            say('across the escape vehicle\'s road'); return False
    if ctx.rt is not None and part != ctx.home:
        RT = ctx.rt
        zone = RT.van.WAIT_Z - RT.LANE_SOUTH
        if RT.lane(q) or (q[2] >= zone and e[2] >= zone and (q[0] > RT.van.LANE_X) != (e[0] > RT.van.LANE_X)):
            say('in or across the van\'s lane'); return False
        if q[2] >= zone > e[2] and nxt is not None and (q[0] > RT.van.LANE_X) != (nxt[0] > RT.van.LANE_X):
            say('across the van\'s lane'); return False
    return True


def find_holds(ctx, part, e, prev, nxt, pers, taken, spots_taken, want, post, tally=None):
    """Up to `want` hold places for a bot at route place e -> [(place 4-tuple, cover index, distance to the box)].
    A cover box within REACH of e that no other bot has at this station; of its places the one BEHIND the box as
    the bot walks (GUESS for the side: the engine picks the side of the box itself, the place only has to be
    within 500 of it, kl2 0x84dc90); the boxes ranked by the walk to them and the bot's preference."""
    ref = nxt if nxt is not None else None
    d = unit2(ref[0] - e[0], ref[2] - e[2]) if ref is not None else unit2(e[0] - prev[0], e[2] - prev[2])
    side = (-d[1], d[0])
    cands = []
    for ci, c in enumerate(ctx.covers):
        ca = c['at']
        if c['hidden'] or ci in taken or abs(ca[0] - e[0]) > REACH or abs(ca[2] - e[2]) > REACH or hdist(ca, e) > REACH or abs(ca[1] - e[1]) > REACH_Y:
            continue
        best = None
        for q in ctx.spots(ci):
            if ctx.nav.part[q[3]] != part or abs(q[1] - e[1]) > 200.0:
                continue
            behind = (ca[0] - q[0]) * d[0] + (ca[2] - q[2]) * d[1] > 0
            key = (not behind, q[4] < F.CLEAR, abs(hdist(q, ca) - RING_BEST))
            if best is None or key < best[0]:
                best = (key, q)
        if best is None:
            continue
        q = best[1]
        fwd = (q[0] - e[0]) * d[0] + (q[2] - e[2]) * d[1]
        sd = (q[0] - e[0]) * side[0] + (q[2] - e[2]) * side[1]
        score = hdist(e, q) + (300.0 if best[0][0] else 0.0)
        score += {'ahead': -0.6 * fwd, 'behind': 0.6 * fwd, 'side+': -0.6 * sd, 'side-': 0.6 * sd}.get(pers.prefer, 0.0)
        cands.append((score, ci, q))
    cands.sort(key=lambda x: x[0])
    out = []
    if tally is not None and not cands:
        tally['no free cover box in reach'] += 1
    for _score, ci, q in cands[:14]:
        if len(out) >= want:
            break
        if any(hdist(q, o) < HOLD_SEP for o in spots_taken) or any(hdist(q, o[0]) < HOLD_SEP for o in out):
            if tally is not None:
                tally['box: too near another hold'] += 1
            continue
        why = []
        if hold_ok(ctx, part, e, q, nxt, post, why):
            out.append((q[:4], ci, hdist(q, ctx.covers[ci]['at'])))
        elif tally is not None:
            tally['box: ' + why[0]] += 1
    if tally is not None and cands and not out:
        tally['every box in reach refused'] += 1
    miss = getattr(ctx, 'misses', None)                 # (kl_fa_cover.py sets ctx.misses = [] to learn WHERE no hold was found)
    if miss is not None and tally is not None and not out:
        miss.append({'at': [round(v, 1) for v in e[:3]], 'dir': [round(d[0], 3), round(d[1], 3)], 'part': part, 'post': bool(post),
                     'why': 'every box in reach refused' if cands else 'no free cover box in reach', 'role': pers.role})
    return out


def last_loot_wait(flat, cut_off, timers=True):
    """THE LAST LOOT WAIT of a chain in flat form -> its index in `flat` (-1: the chain has none). 'Behind the last
    loot wait' is the way OUT: other gaps, no hold of this module on a chain the jump cuts off (program()).
    A TriggerActorsDead counts as a loot wait where it is one - kl_fa_bots' '--wait-guards' puts it in front of the
    table's own wait - and that is all it was until 2026-10-11. kl_fa_bots_rt's GATES are TriggerActorsDead waits
    too, but they stand BEHIND the table, seven of them, down to the foot of the tower: counted as loot waits they
    moved 'the last loot wait' to the last gate, and the rule 'no timer behind the last loot wait of a chain that the
    jump cuts off' then covered the last leg alone (36 timers of this module between the gates of the first gates
    build, re/retomoto_bots_rooms_review.md D1 / D2). So: on a chain that the jump cuts off (cut_off: not the
    squad's last chain) that HAS a loot wait, only loot waits count. Everywhere else as before - the plan of every
    build without such a chain is the same byte for byte.
    timers=False: detours()' own older reading (TriggerLootDepleted and TriggerActorsDead only), kept as it was."""
    is_loot = lambda x: x['kind'] == 'loot' or (timers and x['kind'] == 'timer' and x.get('loot'))
    loot = [i for i, (kind, x) in enumerate(flat) if kind == 'keep' and is_loot(x)]
    if cut_off and loot:
        return loot[-1]
    return max([i for i, (kind, x) in enumerate(flat) if kind == 'keep' and (is_loot(x) or x['kind'] == 'dead')], default=-1)


def flat_chain(ctx, q, chain):
    """A chain's elements as legs -> [('leg', [place dict]) | ('keep', element)]; a place: pt (4-tuple), old (the
    old step's name), flags."""
    out, part = [], None
    for e in chain['elems']:
        if e['kind'] != 'defend':
            out.append(('keep', e))
            continue
        if not out or out[-1][0] != 'leg':
            out.append(('leg', []))
        for p in e['pts']:
            p4 = ctx.p4(p)
            if p4 is None:
                raise ValueError('%s: %s names a place off the mesh: (%d, %d, %d)' % (q['name'], e['name'], *p))
            out[-1][1].append({'pt': (p[0], p[1], p[2], p4[3]), 'old': e['name'], 'sprint': e['sprint']})
    return out


def poly_path(nav, a, b, ban=()):
    """The polygons of the mesh path a -> b (4-tuples), in order, or None."""
    _dist, prev, _at = nav.dist_map(a[3], a[:3], ban)
    if b[3] != a[3] and b[3] not in prev:
        return None
    out, i = [b[3]], b[3]
    while i != a[3]:
        i = prev[i][0]
        out.append(i)
    return out[::-1]


def seg_dist(p, a, b):
    dx, dz = b[0] - a[0], b[2] - a[2]
    L = dx * dx + dz * dz
    t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz)


def line_dist(p, pts):
    return min([seg_dist(p, a, b) for a, b in zip(pts, pts[1:])] or [hdist(p, pts[0])])


def detours(ctx, q, flats, log=print):
    """THE OTHER WAY ROUND for one bot: where a run of plain way places (no trigger box, no loot, no gate, not the
    last) lies between two places A and Z and the mesh has a second way from A to Z that does not use the
    polygons of the shortest one, the run's places are laid along that second way. The places that give the bot
    its heist stage, the loot places and the last places stay. -> number of places moved.
    GUESS all of it (stock makes its other ways by hand: re/bots_dynamic.md 2.1); every moved place then has to
    pass the same checks as the old ones."""
    nav, B, S = ctx.nav, ctx.B, ctx.S
    boxes = [k for ks in S['triggers'].values() for k in ks] + list(S['exits']) + list(ctx.ally)
    fixed = lambda p: any(B.in_box(k, p) or B.in_box(k, (p[0], p[1] + F.CHEST, p[2])) for k in boxes)
    moved, ways = 0, []
    prev = ctx.p4(q['at'], dy=260.0)
    for ci, flat in enumerate(flats):
        if ci:
            prev = None
        last_loot = last_loot_wait(flat, ci < len(flats) - 1, timers=False)
        legs = [i for i, (kind, _x) in enumerate(flat) if kind == 'leg']
        for i, (kind, leg) in enumerate(flat):
            if kind != 'leg':
                continue
            post = i > last_loot
            nxt_keep = flat[i + 1][1] if i + 1 < len(flat) else None
            n = len(leg)
            free = [not fixed(p['pt'][:3]) for p in leg]
            free[-1] = False                            # a leg ends at a loot place, a gate, a rally or the last place
            if ctx.hops:
                for j in range(n - 1):
                    w = ctx.walk(leg[j]['pt'], leg[j + 1]['pt'])
                    if w is None or w[2]:
                        free[j] = free[j + 1] = False
            j = 0
            while j < n:
                if not free[j]:
                    prev = leg[j]['pt']; j += 1
                    continue
                k = j
                while k < n and free[k]:
                    k += 1
                A, Z = prev, leg[k]['pt']               # (k < n: the last place of a leg is never free)
                got = A is not None and nav.part[A[3]] == ctx.home == nav.part[Z[3]] and other_way(ctx, A, Z, k - j, post)
                if got:
                    for m, w in enumerate(got):
                        leg[j + m]['pt'] = w
                        leg[j + m]['moved'] = True
                    moved += k - j
                    ways.append((ci, i, j, k - j))
                prev = leg[k]['pt']
                j = k + 1
    return moved, ways


LANE_DEV = 500.0        # GUESS: a second way counts only if it lies this far from the shortest one somewhere
LANE_LONG = (1.6, 600.0)    # GUESS: ... and is at most this much longer (factor, plus)


def other_way(ctx, A, Z, n, post):
    """n way places along a second mesh way from A to Z (4-tuples), or None."""
    nav, B = ctx.nav, ctx.B
    main = nav.path(A, Z)
    polys = poly_path(nav, A, Z)
    if main is None or polys is None or len(polys) < 4 or any((tuple(u), tuple(w)) in ctx.hops for u, w in zip(main[0], main[0][1:])):
        return None
    ban = {i for i in polys if math.dist(nav.mid[i], A[:3]) > 500.0 and math.dist(nav.mid[i], Z[:3]) > 500.0}
    if ctx.exits and not in_any_exit(ctx, A[:3]):       # as kl_fa_bots.plan: not through a polygon a level exit box touches
        ban |= {i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == ctx.home and any(in_any_exit(ctx, v) for v in nav.pv[i] + [nav.mid[i]])}
    if not ban:
        return None
    alt = nav.path(A, Z, ban)
    if alt is None or alt[1] > LANE_LONG[0] * main[1] + LANE_LONG[1]:
        return None
    pts, L = alt
    if max(line_dist(p, main[0]) for p in pts) < LANE_DEV or any((tuple(u), tuple(w)) in ctx.hops for u, w in zip(pts, pts[1:])):
        return None
    out = []
    for m in range(n):
        want, run = L * (m + 1) / (n + 1), 0.0
        at = pts[-1]
        for u, w in zip(pts, pts[1:]):
            d = math.dist(u, w)
            if d > 0 and run + d >= want:
                t = (want - run) / d
                at = tuple(u[i] + (w[i] - u[i]) * t for i in range(3))
                break
            run += d
        c = [x for x in nav.around(at, 260.0, ctx.home, dy=260.0) if ctx.grid.warp(x[3]) <= WARP and not in_any_exit(ctx, x[:3])
             and (not ctx.lane or not post or F.lane_dist(ctx.lane, x) >= F.LANE_CLEAR)]
        got = nav.spots(c, 1, 0.0, ref=at)
        if not got or nav.clearance(*got[0][:3]) < HOLD_CLEAR:
            return None
        out.append(got[0])
    seq = [A] + out + [Z]
    for u, w in zip(seq, seq[1:]):
        g = ctx.walk(u, w)
        if g is None or g[2]:
            return None
        if ctx.lane and post and F._crosses(ctx.lane, u, w) and not F._crosses(ctx.lane, A, Z):
            return None
    if ctx.exits and not in_any_exit(ctx, A[:3]) and F.first_exit_entry(B, nav, ctx.exits, seq[:-1] + ([] if in_any_exit(ctx, Z[:3]) else [Z])):
        return None
    return out


# ------------------------------------------------------------------ random routes (a RandomTrigger between two steps)
# THE STOCK FORM, copied field for field: F07 Gameplay!merc_bot_squad!Squad#02
#   040_SquadModifier_Loose_defense {26: [040_RandomTrigger_out_of_loot_area]}
#   040_RandomTrigger_out_of_loot_area (ZBoxPrimitive + RandomTrigger {0: 1, 1..4: 3 3 0 0, 5: [..._rout_out_of_loot_area_left],
#                                       6: [..._rout_out_of_loot_area_right], 7: [], 8: []})
#   each branch a DefendBehaviourRout chain of its own; the branches meet again by naming the same next step
#   (090_DefendBehaviour_rout_escape_* x 8 -> 100_SquadModifier_tight_defense_van).
# The node that is cloned is the same squad's 060_RandomTrigger_BeforeStreet (FORM['random']; the same class, the
# same controller, the same nine fields). What starts a RandomTrigger on a stock bot (measured, F01..F09, 440 uses):
# TriggerDelay2 181, DefendBehaviourRout 119, TriggerActorsDead 49, SquadModifierBehaviour 42, TriggerLootDepleted
# 14, another RandomTrigger 28; what it starts: a DefendBehaviourRout step 728 times of 805.
# Weights on stock bots: (3,3) 154 x, (33,33) 44, (3,3,3) 28, (3,3,3,3) 14 ... and UNEQUAL ones: F02 (4,2) (7,1)
# (2,4), F01 (32,13), (11,33), (8,24,34), (7,14,34) - so a weight is a share, and a bot may prefer a way.
BR_MAX = 3              # most ways a fork chooses between (stock bots: two lists 239 x, three 77 x, four 28 x)
ROUTE_LONG = (1.6, 600.0)   # GUESS (as LANE_LONG): another way is at most this much longer than the build's (factor, plus)
ROUTE_SHARE = 0.6       # GUESS: ... and shares at most this part of its length with the build's way or with another one
ROUTE_NEAR = 250.0      # ... 'shares' = lies within this of it in the plan (and within 200 in height)
ROUTE_DEV = 500.0       # GUESS (as LANE_DEV): ... and lies this far from the build's way somewhere
ROUTE_PEN = 4.0         # the polygons of the ways already found cost this many times their length in the next search
ROUTE_MIN = 900.0       # GUESS: no fork on a stretch shorter than this (two fixed places a few steps apart)
ROUTE_SPLIT = 5000.0    # GUESS: a stretch longer than this for which the mesh has no other corridor is cut in two at one
                        # of its way places, each half a fork of its own (stock F07: nine forks on about 250 m of route)
WAY_GAP = 1500.0        # GUESS: a way place about every 15 m of another way (kl_fa_bots.SPACING is 18 m)
WAY_MAX = 6             # ... and at most this many
SIDE_OFF = (320.0, 240.0, 170.0)    # GUESS: a 'side' way = the build's way places moved this far to the left / right
SIDE_MIN = 150.0        # ... (the first that the mesh has room for), at least this far in the end
SIDE_INSERT = 1200.0    # GUESS: a stretch without a way place gets one (in its middle, to the side) if it is this long
WARP_HOME = 100.0       # GUESS: on the START row's mesh part a new WAY place may stand on a polygon this uneven (holds:
                        # WARP). kl_fa_bots has no such rule there and its own way places on M06's lawns stand on
                        # polygons whose fitted height is off by 61..99; with WARP the park had no other way at all.
                        # On another part (Retomoto's street) WARP holds, as kl_fa_bots_rt.check demands.
# who prefers which way: the weights. Stock values where a fork has two ways: (4, 2) is F02 Squad#0n
# RandomTrigger_ramp_choice, (7, 1) F02 RandomTrigger_arch_combat_choice, (3, 3) the commonest. With three ways the
# same numbers are used ((4, 2, 2), (7, 1, 1)): GUESS for the triples (stock's unequal triples are (8, 24, 34) and
# (7, 14, 34)).
PREF = {'ahead': ('short', 4, 2), 'side+': ('left', 4, 2), 'side-': ('right', 4, 2), 'behind': (None, 3, 3), 'near': (None, 3, 3)}
PREF_RUNNER = ('short', 7, 1)


def way(nav, a, b, ban=(), pen=(), factor=1.0):
    """The mesh way a -> b (4-tuples) through the middles of the shared edges, as kl_fa_bots.Nav.path, but a
    stretch inside a polygon of `pen` costs `factor` times its length, and the links (drops) are not walked.
    -> (points, true length, polygons in order) or None."""
    import heapq
    dist, prev, at = {a[3]: 0.0}, {}, {a[3]: a[:3]}
    pq = [(0.0, a[3])]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist.get(i, 1e30):
            continue
        if i == b[3]:
            break
        f = factor if i in pen else 1.0
        for j in nav.nb[i]:
            if j in ban:
                continue
            q = nav.portal(i, j)
            nd = d + math.dist(at[i], q) * f
            if nd < dist.get(j, 1e30):
                dist[j], prev[j], at[j] = nd, (i, q), q
                heapq.heappush(pq, (nd, j))
    if b[3] not in dist:
        return None
    pts, polys, i = [b[:3]], [b[3]], b[3]
    while i != a[3]:
        i, q = prev[i]
        pts.append(q); polys.append(i)
    pts.append(a[:3]); pts.reverse(); polys.reverse()
    return pts, sum(math.dist(u, w) for u, w in zip(pts, pts[1:])), polys


def along(pts, want):
    """The point `want` along the line pts (3-tuples)."""
    run = 0.0
    for u, w in zip(pts, pts[1:]):
        d = math.dist(u, w)
        if d > 0 and run + d >= want:
            t = (want - run) / d
            return tuple(u[i] + (w[i] - u[i]) * t for i in range(3))
        run += d
    return tuple(pts[-1][:3])


def samples_of(pts, step=100.0):
    L = sum(math.dist(u, w) for u, w in zip(pts, pts[1:]))
    n = max(1, int(L // step))
    return [along(pts, L * i / n) for i in range(n + 1)]


def near_line(p, pts, dy=200.0):
    """Distance in the plan from p to the line pts, counting only stretches within dy of p's height."""
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        dx, dz = b[0] - a[0], b[2] - a[2]
        L = dx * dx + dz * dz
        t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / L))
        if abs(a[1] + (b[1] - a[1]) * t - p[1]) <= dy:
            best = min(best, math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz))
    return best


def shared(a, b):
    """(the part of line a that lies within ROUTE_NEAR of line b, the farthest a gets from b)."""
    ds = [near_line(p, b) for p in samples_of(a)]
    return sum(d <= ROUTE_NEAR for d in ds) / len(ds), max(ds)


def side_of(line, A, Z):
    """Mean offset of a line to the LEFT of the straight line A -> Z (negative: to the right)."""
    d = unit2(Z[0] - A[0], Z[2] - A[2])
    s = (-d[1], d[0])
    sm = samples_of(line)
    return sum((p[0] - A[0]) * s[0] + (p[2] - A[2]) * s[1] for p in sm) / len(sm)


class Routes:
    """The search for other ways between the fixed places of the bots' chains (plan step of the random routes)."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.taken = []                                 # the way places made so far, all bots (kept F.SEP apart)
        self._exit_polys = None
        self._wake = None
        self._posts = None
        self.rt_side = {}                               # Retomoto's street: {bot: True = its places lie east of the van's lane}

    def wakes_more(self, part, main, line):
        """A GATES BUILD OF kl_fa_bots_rt (2026-10-11, re/retomoto_bots_rooms.md; nothing on any other build):
        does the way `line` go through a trigger box that wakes an enemy squad and that the build's own way
        `main` between the same two places keeps out of? Between two gates of Retomoto's tower the build's way
        goes through exactly the boxes of the fight it walks to. The first try of this step on such a build gave
        one bot, one round in three, the way from the south gallery to the second floor round the NORTH of the
        atrium (91 m for 56): alone through three boxes the gates keep for later - where runs R7a / R7d each
        lost a bot. Only the tower (the START row's mesh part): the street has no gates."""
        ctx = self.ctx
        if self._wake is None:
            self._wake = ()
            if ctx.rt is not None and any(e['kind'] == 'dead' for q in ctx.squads.values() for c in q['chains'] for e in c['elems']):
                self._wake = tuple(ctx.rt.wake_map(ctx.B)[0])
        if not self._wake or part != ctx.home:
            return False
        RT, B = ctx.rt, ctx.B
        on = lambda pts: {k for m in RT.samples([p[:3] for p in pts]) for k in self._wake if RT.in_trigger(B, k, m)}
        return bool(on(line) - on(main))

    def passes_more(self, part, main, line):
        """A GATES BUILD OF kl_fa_bots_rt, the tower part (as wakes_more; nothing anywhere else): does the way `line`
        come within reach (RT.PASS_NEAR, on the post's floor) of a POST of an enemy that the build's own way `main`
        keeps clear of - or walk on farther past one than the build's way does, beyond RT.PASS_ON? A gate's hold is
        laid so that no way to it walks PAST a man the gate waits for (kl_fa_bots_rt.passes; the first gates build
        had a hold 20 m beyond such men). Another way of a fork is held to the build's own: no new post, no longer
        walk with a post behind it. The first try of this step on the second gates build sent the runner to his last
        hold round a place of Atrium_1st_PillarCover, 2.9 m from it and 11 m on; kl_fa_bots_rt.check FAILS that."""
        ctx = self.ctx
        if self._posts is None:
            self._posts = ()
            if ctx.rt is not None and any(e['kind'] == 'dead' for q in ctx.squads.values() for c in q['chains'] for e in c['elems']):
                self._posts = tuple(q for ps in ctx.rt.enemy_posts(ctx.B).values() for _w, q, _r in ps)
        if not self._posts or part != ctx.home:
            return False
        RT = ctx.rt

        def left(pts):
            """{post: the way left when the line has come out of the post's reach for the last time}"""
            sm, out = list(RT.samples([p[:3] for p in pts])), {}
            for n, q in enumerate(self._posts):
                near = [i for i, m in enumerate(sm) if abs(m[1] - q[1]) <= RT.FLOOR_DY and hdist(m, q) < RT.PASS_NEAR]
                if near:
                    out[n] = sum(math.dist(u, w) for u, w in zip(sm[near[-1]:], sm[near[-1] + 1:]))
            return out
        a, b = left(main), left(line)
        return any(n not in a or (v > RT.PASS_ON and v > a[n] + 1.0) for n, v in b.items())

    def exit_polys(self):
        ctx, nav = self.ctx, self.ctx.nav
        if self._exit_polys is None:
            self._exit_polys = {i for i in range(len(nav.pv)) if nav.ok[i] and any(in_any_exit(ctx, v) for v in nav.pv[i] + [nav.mid[i]])} if ctx.exits else set()
        return self._exit_polys

    def place_ok(self, N, part, post, exit_free):
        """-> the test a new way place has to pass (the rules kl_fa_bots.check / kl_fa_bots_rt.check put on one)."""
        ctx = self.ctx
        RT = ctx.rt if (ctx.rt is not None and part != ctx.home) else None
        au = ctx.rt.au if (ctx.rt is not None and part == ctx.home) else None

        def ok(p):
            if exit_free and in_any_exit(ctx, p[:3]):
                return False
            if au is not None and (hdist(p, au.BOMB) < ctx.rt.BOMB_KEEP or hdist(p, au.INVISIBOMB) < ctx.rt.INVISI_KEEP):
                return False                            # (Retomoto's tower: kl_fa_bots_rt keeps its places clear of the charges)
            if ctx.lane and post and F.lane_dist(ctx.lane, p) < F.LANE_CLEAR:
                return False
            if RT is not None:
                if RT.lane(p):
                    return False
                if p[2] >= RT.van.WAIT_Z - RT.LANE_SOUTH and (p[0] > RT.van.LANE_X) != self.rt_side.get(N):
                    return False                        # (near the van every place of a bot lies on ONE side of its lane)
            return True
        return ok

    def pick(self, at, part, ok, others, radius=260.0, limit=None):
        """A way place near `at`: on the mesh part, flat, clear of the mesh's edge, F.SEP from every other bot's
        way place; the nearest with kl_fa_bots' own clearance first. limit = (place, most path from it)."""
        ctx, g = self.ctx, self.ctx.grid
        k, best = int(radius // 40), None
        uneven = WARP_HOME if part == ctx.home else WARP
        for ix in range(-k, k + 1):
            for iz in range(-k, k + 1):
                x, z = at[0] + ix * 40.0, at[2] + iz * 40.0
                r = math.hypot(ix, iz) * 40.0
                if r > radius:
                    continue
                hit = g.at(x, at[1], z, REACH_Y, part)
                if not hit or g.warp(hit[0]) > uneven:
                    continue
                p = (x, hit[1], z, hit[0])
                if not ok(p) or any(hdist(p, o) < F.SEP and abs(p[1] - o[1]) < 150.0 for o in others):
                    continue
                cl = g.clearance(x, hit[1], z)
                if cl < HOLD_CLEAR:
                    continue
                key = (cl < F.CLEAR, r)
                if best is None or key < best[0]:
                    best = (key, p)
        if best is None:
            return None
        if limit is not None:
            w = ctx.walk(limit[0], best[1])
            if w is None or w[2] or w[1] > limit[1]:
                return None
        return best[1]

    def line(self, seq):
        """The walked line through the places seq (4-tuples) -> (points, length) or None (no way, or over a link)."""
        pts, L = [seq[0][:3]], 0.0
        for u, w in zip(seq, seq[1:]):
            g = self.ctx.walk(u, w)
            if g is None or g[2]:
                return None
            pts += g[0][1:]; L += g[1]
        return pts, L

    def seq_ok(self, seq, post, exit_free):
        """The rules on a whole way A, places.., Z: the escape vehicle's road and the level exit boxes."""
        ctx = self.ctx
        A, Z = seq[0], seq[-1]
        if ctx.lane and post and not F._crosses(ctx.lane, A, Z) and any(F._crosses(ctx.lane, u, w) for u, w in zip(seq, seq[1:])):
            return False
        if exit_free and F.first_exit_entry(ctx.B, ctx.nav, ctx.exits, seq[:-1] + ([] if in_any_exit(ctx, Z[:3]) else [Z])):
            return False
        return True

    def real(self, N, part, seq, main, L0, post, found, pen):
        """Another way of the mesh from seq[0] to seq[-1] -> (branch or None, why not, its polygons)."""
        ctx, nav = self.ctx, self.ctx.nav
        A, Z = seq[0], seq[-1]
        exit_free = bool(ctx.exits) and not in_any_exit(ctx, A[:3])
        # (not through a polygon a level exit box touches, as kl_fa_bots.plan - unless the stretch itself ends in
        # the box: then its places and the walk up to its last place are tested instead, place_ok / seq_ok)
        got = way(nav, A, Z, self.exit_polys() if exit_free and not in_any_exit(ctx, Z[:3]) else (), pen, ROUTE_PEN)
        if got is None:
            return None, 'no way', set()
        pts, L, polys = got
        polys = set(polys)
        if L > ROUTE_LONG[0] * L0 + ROUTE_LONG[1]:
            return None, 'longer than %.1f x + %d m' % (ROUTE_LONG[0], ROUTE_LONG[1] / 100), polys
        for other in [main] + [b['line'] for b in found]:
            sh, dev = shared(pts, other)
            if sh > ROUTE_SHARE or dev < ROUTE_DEV:
                return None, 'the same way (shares %d %%, at most %d m off)' % (100 * sh, dev / 100), polys
        n = min(WAY_MAX, max(1, len(seq) - 2, int(round(L / WAY_GAP))))
        ok = self.place_ok(N, part, post, exit_free)
        places = []
        for m in range(n):
            p = self.pick(along(pts, L * (m + 1) / (n + 1)), part, ok, self.taken + places)
            if p is None:
                return None, 'no room for a way place on it', polys
            places.append(p)
        full = [A] + places + [Z]
        ln = self.line(full)
        if ln is None or ln[1] > ROUTE_LONG[0] * L0 + ROUTE_LONG[1] or not self.seq_ok(full, post, exit_free):
            return None, 'its way places do not pass the route\'s rules', polys
        worst = 0.0
        for other in [main] + [b['line'] for b in found]:
            sh, dev = shared(ln[0], other)
            worst = max(worst, sh)
            if sh > ROUTE_SHARE or dev < ROUTE_DEV:     # (the walk from place to place fell back into the other way)
                return None, 'the same way once its places are walked (shares %d %%)' % (100 * sh), polys
        if self.wakes_more(part, main, ln[0]):
            return None, 'through a trigger box of a fight the build\'s way keeps out of', polys
        if self.passes_more(part, main, ln[0]):
            return None, 'past a post of an enemy the build\'s way keeps clear of', polys
        return {'kind': 'real', 'pts': places, 'length': ln[1], 'share': worst, 'line': ln[0]}, None, polys

    def lateral(self, N, part, seq, main, L0, post, sign):
        """The build's way with its way places moved to one side (sign +1 = left of the way) -> branch or None."""
        ctx = self.ctx
        A, Z = seq[0], seq[-1]
        exit_free = bool(ctx.exits) and not in_any_exit(ctx, A[:3])
        ok = self.place_ok(N, part, post, exit_free)
        mids, made = list(seq[1:-1]), False
        if not mids:
            if L0 < SIDE_INSERT:
                return None
            m = along(main, L0 / 2)
            hit = ctx.grid.at(m[0], m[1], m[2], REACH_Y, part)
            if not hit:
                return None
            mids, made = [(m[0], hit[1], m[2], hit[0])], True
        out, moved = [], 0
        for m, p in enumerate(mids):
            u = out[-1] if out else A
            w = mids[m + 1] if m + 1 < len(mids) else Z
            d = unit2(w[0] - u[0], w[2] - u[2])
            s = (-d[1] * sign, d[0] * sign)
            got = None
            for off in SIDE_OFF:
                t = (p[0] + s[0] * off, p[1], p[2] + s[1] * off)
                got = self.pick(t, part, ok, self.taken + out, radius=90.0, limit=(p, 1.5 * off + 200.0))
                if got is not None and ((got[0] - p[0]) * s[0] + (got[2] - p[2]) * s[1]) >= SIDE_MIN:
                    break
                got = None
            if got is None:
                if made:
                    return None
                out.append(p)                           # (no room beside this one: it stays)
            else:
                out.append(got); moved += 1
        if moved < max(1, (len(mids) + 1) // 2):
            return None
        full = [A] + out + [Z]
        ln = self.line(full)
        if ln is None or ln[1] > ROUTE_LONG[0] * L0 + ROUTE_LONG[1] or not self.seq_ok(full, post, exit_free):
            return None
        if self.wakes_more(part, main, ln[0]) or self.passes_more(part, main, ln[0]):
            return None
        return {'kind': 'left' if sign > 0 else 'right', 'pts': out, 'length': ln[1], 'share': shared(ln[0], main)[0], 'line': ln[0], 'moved': moved}

    def forks(self, q, flats, pers, opt, log=print):
        """Mark the forks of one bot in its legs (leg place ['fork']) -> [report of every stretch between two fixed
        places]. A stretch = the run of plain way places between two places that must stay (a trigger box that
        gives the heist stage, a level exit box, an AllyEscapeBox, a loot place, a gate, a rally, the last place)."""
        ctx, nav, B, S, N = self.ctx, self.ctx.nav, self.ctx.B, self.ctx.S, q['N']
        boxes = [k for ks in S['triggers'].values() for k in ks] + list(S['exits']) + list(ctx.ally)
        fixed = lambda p: any(B.in_box(k, p) or B.in_box(k, (p[0], p[1] + F.CHEST, p[2])) for k in boxes)
        if ctx.rt is not None:                          # which side of the van's lane this bot's street places lie on
            RT = ctx.rt
            zs = [p['pt'] for flat in flats for kind, leg in flat if kind == 'leg' for p in leg
                  if nav.part[p['pt'][3]] != ctx.home and p['pt'][2] >= RT.van.WAIT_Z - RT.LANE_SOUTH]
            if zs:
                self.rt_side[N] = zs[-1][0] > RT.van.LANE_X
        report = []
        most = max(2, min(4, int(opt.get('ways') or BR_MAX)))
        prev = ctx.p4(q['at'], dy=260.0)
        for ci, flat in enumerate(flats):
            if ci:
                prev = None                             # (a chain started from outside: its first step is named, it stays)
            last_loot = last_loot_wait(flat, ci < len(flats) - 1)
            for i, (kind, leg) in enumerate(flat):
                if kind != 'leg':
                    continue
                post = i > last_loot
                n = len(leg)
                free = [not fixed(p['pt'][:3]) for p in leg]
                free[-1] = False
                def stretch(j0, k, A, depth=0):
                    """The stretch A -> leg[j0..k-1] -> leg[k]: a fork over all of it when the mesh has another
                    corridor for it; else, when it is long, two stretches that meet at one of its way places (the
                    ways of each meet there: more draws a round, stock F07 has a fork about every 28 m); else a
                    fork between the build's way and the same way moved to a side."""
                    Z = leg[k]['pt']
                    rep = {'chain': ci, 'leg': i, 'place': j0, 'way_places': k - j0, 'post': post, 'to': [round(v) for v in Z[:3]],
                           'from': [round(v) for v in A[:3]]}
                    part = nav.part[A[3]]
                    seq = [A] + [leg[m]['pt'] for m in range(j0, k)] + [Z]
                    ln = self.line(seq) if nav.part[Z[3]] == part else None
                    if ln is None:
                        rep['why'] = 'a link (the drop) or another mesh part: left as it is'
                        report.append(rep); return
                    main, L0 = ln
                    rep['length'] = round(L0)
                    if L0 < ROUTE_MIN:
                        rep['why'] = 'shorter than %d m' % (ROUTE_MIN / 100)
                        report.append(rep); return
                    if ctx.rt is not None and ci == 0 and A[:3] == tuple(ctx.p4(q['at'], dy=260.0)[:3]):
                        # Retomoto: from the balcony the only way in is the blown window (the other panes of the
                        # mesh's edge are glass that stays), past the charge: kl_fa_bots_rt planned that step
                        rep['why'] = 'the way in through the blown window: left as it is'
                        report.append(rep); return
                    found, pen, why = [], set(), []
                    for u, w in zip(seq, seq[1:]):
                        g = way(nav, u, w)
                        pen |= set(g[2]) if g else set()
                    for _round in range(most - 1):
                        br, w_, polys = self.real(N, part, seq, main, L0, post, found, pen)
                        pen |= polys
                        if br is None:
                            why.append(w_)
                            if not polys:
                                break
                            continue
                        found.append(br)
                    if not found and L0 > ROUTE_SPLIT and k > j0:
                        # no other corridor for the whole of it: cut it at the way place nearest to its middle
                        run, at, best = 0.0, A, None
                        for m in range(j0, k):
                            g = ctx.walk(at, leg[m]['pt'])
                            run += g[1] if g else 0.0
                            at = leg[m]['pt']
                            if best is None or abs(run - L0 / 2) < best[0]:
                                best = (abs(run - L0 / 2), m, run)
                        if min(best[2], L0 - best[2]) >= ROUTE_MIN:
                            stretch(j0, best[1], A, depth + 1)
                            stretch(best[1] + 1, k, leg[best[1]]['pt'], depth + 1)
                            return
                    rep['real'] = len(found)
                    rep['no_real'] = why
                    # the sides: the flankers their own side first
                    for sign in ((-1, 1) if pers.prefer == 'side-' else (1, -1)):
                        if 1 + len(found) >= most:
                            break
                        br = self.lateral(N, part, seq, main, L0, post, sign)
                        if br is not None:
                            found.append(br)
                    rep['branches'] = ['build'] + [b['kind'] for b in found]
                    rep['lengths'] = [round(L0)] + [round(b['length']) for b in found]
                    rep['shares'] = [round(100 * b['share']) for b in found]
                    if found:
                        base = side_of(main, A, Z)
                        brs = [{'kind': 'build', 'pts': seq[1:-1], 'length': L0, 'side': 0.0}] + \
                              [dict(b, side=side_of(b['line'], A, Z) - base) for b in found]
                        for b in brs:
                            b.pop('line', None)
                        self.taken += [p for b in found for p in b['pts']]
                        rep['weights'] = weights(pers, brs)
                        leg[j0 if k > j0 else k]['fork'] = {'n': k - j0, 'branches': brs, 'weights': rep['weights'], 'to': Z}
                    report.append(rep)

                j = 0
                while j < n:
                    k = j
                    while k < n and free[k]:
                        k += 1                          # (k < n: the last place of a leg is never free)
                    if prev is not None:
                        stretch(j, k, prev)
                    else:
                        report.append({'chain': ci, 'leg': i, 'place': j, 'way_places': k - j, 'post': post, 'to': [round(v) for v in leg[k]['pt'][:3]],
                                       'why': 'the first step of a chain that is started from outside: it stays'})
                    prev, j = leg[k]['pt'], k + 1
        return report


def weights(pers, brs):
    """The RandomTrigger's weights of a fork for this bot (PREF): which way it prefers; it still draws."""
    what, hi, lo = PREF_RUNNER if pers.role == 'runner' else PREF.get(pers.prefer, (None, 3, 3))
    if what == 'short':
        fav = min(range(len(brs)), key=lambda i: brs[i]['length'])
    elif what == 'left':
        fav = max(range(len(brs)), key=lambda i: brs[i]['side'])
    elif what == 'right':
        fav = min(range(len(brs)), key=lambda i: brs[i]['side'])
    else:
        return [3] * len(brs)
    return [hi if i == fav else lo for i in range(len(brs))]


def all_items(items):
    """Every item of a program, the ones inside a fork's branches too."""
    for it in items:
        yield it
        if it['kind'] == 'fork':
            for br in it['branches']:
                yield from all_items(br['items'])


def plan(ctx, opt=None, log=print):
    """-> the plan (dict, JSON-able): per bot its personality and, per chain, the program = the items of the new
    chain in order. plan['stations'] says what was found at each route place."""
    opt = dict(DEFAULTS, **(opt or {}))
    B, nav = ctx.B, ctx.nav
    P = collections.OrderedDict(folder=ctx.folder, map=B.result.get('M'), options=opt)
    cv = [c for c in ctx.covers if not c['hidden']]
    P['covers'] = {'all': len(ctx.covers), 'hidden': len(ctx.covers) - len(cv), 'high': sum(c['kind'] == 'high' for c in cv),
                   'low': sum(c['kind'] == 'low' for c in cv), 'car': sum(c['kind'] == 'car' for c in cv)}
    log('cover boxes (ZSTDOBJ named *coverbox*, as kl2 0x6d6a80 takes them): %d high, %d low, %d car%s'
        % (P['covers']['high'], P['covers']['low'], P['covers']['car'], '; %d more are created hidden (flag 0x400) and left out' % P['covers']['hidden'] if P['covers']['hidden'] else ''))
    if not cv:
        log('  NOTE the build has NO cover box: no hold can be planned (re/bots_dynamic.md 3.3 says how boxes could be made)')
    flats = {N: [flat_chain(ctx, q, c) for c in q['chains']] for N, q in ctx.squads.items()}
    sc = B.sc
    P['detours'] = collections.OrderedDict()
    P['routes'] = collections.OrderedDict()
    if opt['routes']:
        # RANDOM ROUTES: between the fixed places of every bot's chain the other ways the mesh has (and, where it
        # has one corridor only, the build's way moved to a side); a RandomTrigger draws one per bot per round
        R = Routes(ctx)
        for N in ORDER:
            P['routes'][N] = R.forks(ctx.squads[N], flats[N], PERS[N], opt, log)
        P['routes'] = collections.OrderedDict((N, P['routes'][N]) for N in sorted(P['routes']))
        log('random routes: a stretch = the way between two places that stay (stage trigger, loot place, gate, rally, last place)')
        for N, reps in P['routes'].items():
            f = [r for r in reps if r.get('weights')]
            none = [r for r in reps if 'branches' in r and not r.get('weights')]
            log('  Squad#0%d %-22s %d stretches: %d fork(s) (%d with 3 ways, %d with 2); ways of another corridor of the mesh: %d; of the build\'s way '
                'moved to a side: %d; stretches of %d m and more with no other way at all: %d; not looked at (short, a link, the first step): %d'
                % (N, PERS[N].role, len(reps), len(f), sum(len(r['branches']) == 3 for r in f), sum(len(r['branches']) == 2 for r in f),
                   sum(r['real'] for r in f), sum(b in ('left', 'right') for r in f for b in r['branches']), ROUTE_MIN / 100, len(none),
                   len(reps) - len(f) - len(none)))
            for r in f:
                log('      chain %d, (%d, %d, %d) -> (%d, %d, %d), %d m: %s; lengths %s m; weights %s%s'
                    % (r['chain'] + 1, *r['from'], *r['to'], r['length'] / 100, ' / '.join(r['branches']), [round(x / 100) for x in r['lengths']], r['weights'],
                       '; shares with the build\'s way %s %%' % r['shares'] if r['real'] else ''))
    if opt['detour'] and not opt['routes']:             # (with random routes the other way round is one of a fork's ways)
        for N in sorted(ctx.squads):
            if PERS[N].prefer == DETOUR:
                moved, ways = detours(ctx, ctx.squads[N], flats[N], log)
                P['detours'][N] = {'places_moved': moved, 'runs': ways}
                log('the other way round, Squad#0%d (%s): %d way place(s) in %d run(s) laid along a second way of the mesh%s'
                    % (N, PERS[N].role, moved, len(ways), '' if moved else ' - the mesh has none between the fixed places (or none short enough)'))
    names = {}
    for N, q in ctx.squads.items():
        old = {e['k'] for c in q['chains'] for e in c['elems'] if e['kind'] == 'defend'}
        names[N] = {sc.names[k].lower() for k in range(q['top'] + 1, sc.end[q['top']]) if sc.parent[k] == q['top'] and k not in old}
    # ---- first every bot ONE cover per hold (who chooses first: ORDER), then the covers that are left as the
    # alternatives of a RandomTrigger - so that the first bots do not take three boxes each and leave none
    taken, spots_taken = {}, []                         # {cover box: the bot that has it}, [(bot, station, hold place)]
    tally = collections.Counter()
    P['bots'] = collections.OrderedDict()
    for N in ORDER:
        q, pers = ctx.squads[N], PERS[N]
        gap_scale = 1.0
        while True:
            trial_taken, trial_spots = dict(taken), list(spots_taken)
            used, tl = set(names[N]), collections.Counter()
            progs, secs, holds = [], 0.0, 0
            for ci, flat in enumerate(flats[N]):
                items, s, h = program(ctx, q, ci, flat, pers, opt, trial_taken, trial_spots, gap_scale, used, tl)
                progs.append(items); secs += s; holds += h
            if secs <= BUDGET[1] or holds == 0 or gap_scale > 6.0:
                break
            gap_scale *= 1.25                           # too many seconds of timers: fewer holds
        taken, spots_taken, names[N] = trial_taken, trial_spots, used
        tally.update(tl)
        P['bots'][N] = collections.OrderedDict(squad=q['name'], role=pers.role, personality=pers._asdict(), holds=holds,
                                               timer_seconds=round(secs, 1), gap_scale=round(gap_scale, 2), chains=progs)
    for N in ORDER:
        finish(ctx, N, P['bots'][N]['chains'], PERS[N], opt, taken, spots_taken, names[N])
    P['hold_search'] = dict(tally)
    log('holds: %d route places asked for one; found %d; without: %s' % (tally['asked'], tally['found'], {k: v for k, v in tally.items() if k not in ('asked', 'found') and not k.startswith('box:')} or 'none'))
    log('  cover boxes refused on the way (a box may be refused for several bots): %s' % ({k[5:]: v for k, v in tally.items() if k.startswith('box:')} or 'none'))
    P['bots'] = collections.OrderedDict((N, P['bots'][N]) for N in sorted(P['bots']))
    for N, b in P['bots'].items():
        rnd = sum(1 for c in b['chains'] for it in all_items(c) if it['kind'] == 'rout' and it.get('fan') and it['fan']['kind'] == 'random')
        log('  Squad#0%d %-22s starts +%g s, %2d holds on the build\'s way (%d choices of cover on all ways), %d fork(s) of the way, %5.1f s of timers, '
            'loot seconds %s, sprint on %d step(s)'
            % (N, b['role'], PERS[N].stagger if opt['stagger'] else 0.0, b['holds'], rnd, sum(1 for c in b['chains'] for it in c if it['kind'] == 'fork'),
               b['timer_seconds'],
               [it['loot_seconds'] for c in b['chains'] for it in c if it['kind'] == 'keep' and it.get('loot_seconds') is not None] or '-',
               sum(1 for c in b['chains'] for it in c if it['kind'] == 'rout' and it['sprint'])))
    return P


def uniq_in(used, name):
    cand, n = name, 1
    while cand.lower() in used:
        n += 1
        cand = '%s_%s' % (name, 'abcdefghijklmnopqrstuvwxyz'[n - 1] if n <= 26 else str(n))
    used.add(cand.lower())
    return cand


def alt_of(ctx, g):
    return {'name': None, 'place': [round(v, 2) for v in g[0][:3]], 'cover': ctx.B.sc.path[ctx.covers[g[1]]['node']][5:],
            'cover_kind': ctx.covers[g[1]]['kind'], 'from_cover': round(g[2])}


def finish(ctx, N, progs, pers, opt, taken, spots_taken, used):
    """The second pass over a bot's chains: more covers for a hold where boxes are left (a RandomTrigger then picks
    one per round), the names, and the form: ONE cover = a walked 'pos' step before the timer (rout -> pos -> timer,
    stock F07's 070_DefendBehaviour_pos_to_street_middle -> 070_Timer_small_street_middle); several, or a hold
    during a timer of the build (a rally) = started beside the timer (rout -> [timer, RandomTrigger or pos]; a
    Defend step that starts a timer and another behaviour: stock F01 Gameplay!PolicePlatform#01 10_Defend)."""
    def fin(items):
        out = []
        for it in items:
            out.append(it)
            if it['kind'] == 'fork':                    # the ways of a fork: each its own holds
                for br in it['branches']:
                    br['items'] = fin(br['items'])
                continue
            h = it.pop('hold', None) if it['kind'] == 'rout' else None
            if h is None:
                continue
            key, part, e, prev, nx, post = h['search']
            alts = h['alts']
            if opt['random']:
                more = find_holds(ctx, part, e, prev, nx, pers, {c for c, n in taken.items() if n != N or c in h['boxes']},
                                  [x for n, k, x in spots_taken if n != N or k == key], ALTS - 1, post)
                for g in more:
                    taken[g[1]] = N; spots_taken.append((N, key, g[0]))
                    alts.append(alt_of(ctx, g))
            pre = h['pre']
            if len(alts) > 1:
                for a, ch in zip(alts, 'abc'):
                    a['name'] = uniq_in(used, '%s_DefendBehaviour_pos_cover_%s' % (pre, ch))
                it['fan'] = {'kind': 'random', 'name': uniq_in(used, '%s_RandomTrigger_cover' % pre), 'alts': alts}
            elif h['rally']:
                alts[0]['name'] = uniq_in(used, '%s_DefendBehaviour_pos_cover' % pre)
                it['fan'] = {'kind': 'one', 'alts': alts}
            else:
                a = alts[0]
                a['name'] = uniq_in(used, '%s_DefendBehaviour_pos_cover' % pre)
                out.append({'kind': 'hold', 'name': a['name'], 'place': a['place'], 'cover': a['cover'], 'cover_kind': a['cover_kind'], 'from_cover': a['from_cover']})
        return out

    for ci, items in enumerate(progs):
        progs[ci] = fin(items)


def program(ctx, q, chain_no, flat, pers, opt, taken, spots_taken, gap_scale, used, tally):
    """The new chain of one bot for one old chain -> (items, seconds of timers in it, number of holds).
    Items, in the order they run: stagger / mod / rout (places, sprint; 'hold' = the cover found for its end, which
    finish() turns into a hold item or a fan) / timer / keep."""
    nav, N = ctx.nav, q['N']
    uniq = lambda name: uniq_in(used, name)

    items, secs, holds = [], 0.0, 0
    main = chain_no == 0
    last_chain = chain_no == len(q['chains']) - 1
    if main:
        if opt['stagger'] and pers.stagger > 0:
            items.append({'kind': 'timer', 'name': uniq('000_Timer_stagger'), 'seconds': pers.stagger}); secs += pers.stagger
        fields = {'defend': 'eDM_Loose'}
        if opt['vision']:
            fields['vision'] = 'eVIM_Factor_2_0'
        if opt['sixth']:
            fields['sixth'] = 'eCSS_Enabled'
        items.append({'kind': 'mod', 'name': uniq('001_SquadModifier_awake'), 'fields': fields})
    # which elements follow each leg; where the last loot wait is
    kinds = [(kind, x) for kind, x in flat]
    is_lootwait = lambda e: e['kind'] == 'loot' or (e['kind'] == 'timer' and e['loot'])
    last_loot = last_loot_wait(kinds, not last_chain)   # (a gates build of kl_fa_bots_rt: the TABLE's wait, not the last gate)
    n_legs = [i for i, (kind, _x) in enumerate(kinds) if kind == 'leg']
    prev_pt = (ctx.p4(q['at'], dy=260.0) or None) if main else None
    since = 0.0
    routs = []                                          # the rout items of this chain, to set the sprint on the last ones
    for i, (kind, x) in enumerate(kinds):
        if kind == 'keep':
            it = {'kind': 'keep', 'name': x['name'], 'ctrl': x['ctrl'], 'also': x.get('also', []), 'what': x['kind']}
            if x['kind'] == 'loot':
                s = x['seconds']
                # (a map of two parts: nobody waits longer than the build says - see the hold rule below)
                long_ = pers.loot == 'long' and len(q['chains']) == 1
                it['loot_seconds'] = int(min(s, LOOT_SHORT) if pers.loot == 'short' else min(LOOT_LONG[1], s + LOOT_LONG[0]) if long_ else s)
                # A GATES BUILD OF kl_fa_bots_rt (a TriggerActorsDead behind this loot wait, 2026-10-11): nobody's wait at
                # the table is cut short. A gate holds the seven at one fight, each from his own arrival, 30 s at most;
                # the point man and the runner leaving the table 15 s before the others would be at every gate 15 s
                # early and, wherever a gate runs out (run G1_DM09: six of seven did, with an idle player), walk on
                # alone 15 s ahead - the string the gates are there to prevent.
                if any(k2 == 'keep' and x2['kind'] == 'dead' for k2, x2 in kinds[i + 1:]):
                    it['loot_seconds'] = int(s)
                it['was'] = x['seconds']
            if x['kind'] == 'timer':
                secs += x['seconds']
            items.append(it)
            if is_lootwait(x):
                since = 0.0
                if i == last_loot and pers.after == 'leash':
                    items.append({'kind': 'mod', 'name': uniq('%s_SquadModifier_tight_rear' % x['name'][:3]), 'fields': {'leash': 'eLM_Leash', 'defend': 'eDM_Tight'}})
                else:
                    items.append({'kind': 'mod', 'name': uniq('%s_SquadModifier_Loose_defense' % x['name'][:3]), 'fields': {'defend': 'eDM_Loose'}})
            continue
        leg = x
        post = i > last_loot
        nxt_kind = kinds[i + 1][1] if i + 1 < len(kinds) else None
        loot_leg = nxt_kind is not None and is_lootwait(nxt_kind)
        rally = nxt_kind is not None and nxt_kind['kind'] == 'timer' and not nxt_kind['cases'] and not nxt_kind['loot']
        final_leg = i == n_legs[-1]
        # the place after this leg (for the direction at its last place and the way on)
        after = None
        for kind2, x2 in kinds[i + 1:]:
            if kind2 == 'leg':
                after = x2[0]['pt']; break
        n = len(leg)
        gate = [False] * n
        for j in range(n):
            nx = leg[j + 1]['pt'] if j + 1 < n else after
            if nx is not None and ctx.hops:
                w = ctx.walk(leg[j]['pt'], nx)
                gate[j] = bool(w and w[2])
        part = nav.part[leg[0]['pt'][3]]
        gap = (opt['gap'] if not post else GAP_OUT) * gap_scale
        cur, cur_old = [], None
        skip = 0
        for j, p in enumerate(leg):
            if j < skip:                                # (a way place of the build that a fork's first way has taken)
                continue
            fk = p.get('fork') if opt['routes'] else None
            if fk:
                # A FORK OF THE WAY: what stands before it (a walk, a hold's timer, a modifier, a wait of the build)
                # starts a RandomTrigger; each of its ways is a chain of its own (walk, holds at ITS covers) and
                # every one of them ends by starting what follows the fork = the step of the next fixed place
                if cur:
                    routs.append({'kind': 'rout', 'name': uniq(cur_old), 'places': cur, 'sprint': False, 'way_out': post}); items.append(routs[-1])
                    cur = []
                pre = p['old'][:3]
                gap_f = gap * (pers.phase if holds == 0 else 1.0)
                want_f = (pers.out_holds or not post) and (pers.hold_out > 0 or not post) and (last_chain or not post)
                brs, ends = [], []
                for b, br in enumerate(fk['branches']):
                    its, s_b, h_b, since_b, at_b = [], 0.0, 0, since, prev_pt
                    cur_b = []
                    for m, e in enumerate(br['pts']):
                        since_b += math.dist(at_b[:3], e[:3])
                        nx = br['pts'][m + 1] if m + 1 < len(br['pts']) else fk['to']
                        cur_b.append([round(v, 2) for v in e[:3]])
                        hold = None
                        if want_f and since_b >= gap_f:
                            key = (chain_no, i, j, b, m)
                            tally['asked'] += 1
                            got = find_holds(ctx, part, e, at_b, nx, pers, {c for c, n in taken.items() if n != N},
                                             [x for n, k, x in spots_taken if n != N or k == key], 1, post, tally)
                            if got:
                                tally['found'] += 1
                                hold = got[0]
                                taken[hold[1]] = N; spots_taken.append((N, key, hold[0]))
                        if m == len(br['pts']) - 1 or hold is not None or len(cur_b) >= F.STEP_MAX:
                            r = {'kind': 'rout', 'name': uniq('%s_DefendBehaviour_way_%s' % (pre, 'abcd'[b])), 'places': cur_b, 'sprint': False, 'way_out': post}
                            its.append(r)
                            cur_b = []
                            if hold is not None:
                                h_b += 1; since_b = 0.0
                                sec = pers.hold_out if post else pers.hold_in
                                r['hold'] = {'pre': pre, 'rally': False, 'alts': [alt_of(ctx, hold)], 'boxes': {hold[1]}, 'search': (key, part, e, at_b, nx, post)}
                                its.append({'kind': 'timer', 'name': uniq('%s_Timer_hold' % pre), 'seconds': sec}); s_b += sec
                        at_b = e
                    brs.append({'kind': br['kind'], 'length': round(br['length']), 'weight': fk['weights'][b], 'items': its})
                    ends.append((s_b, h_b, since_b, at_b))
                items.append({'kind': 'fork', 'name': uniq('%s_RandomTrigger_way' % pre), 'branches': brs,
                              'to': [round(v, 2) for v in fk['to'][:3]]})
                secs += max(x[0] for x in ends)         # (the budget of timers: the way with the most)
                holds += ends[0][1]; since = ends[0][2]; prev_pt = ends[0][3]
                del routs[:]                            # (the dash is the steps BEHIND the last fork)
                skip = j + fk['n']
                if fk['n']:
                    continue
            e = p['pt']
            if prev_pt is not None:
                since += math.dist(prev_pt[:3], e[:3])
            nx = leg[j + 1]['pt'] if j + 1 < n else after
            is_loot_place = loot_leg and j == n - 1
            if is_loot_place:                           # the loot place is a step of its own, tight (stock F07: 030 -> 031)
                if cur:
                    routs.append({'kind': 'rout', 'name': uniq(cur_old), 'places': cur, 'sprint': False, 'way_out': post}); items.append(routs[-1])
                    cur = []
                items.append({'kind': 'mod', 'name': uniq('%s_SquadModifier_tight_defense_loot' % p['old'][:3]), 'fields': {'defend': 'eDM_Tight'}})
                cur_old = p['old']
            if not cur:
                cur_old = p['old']
            cur.append([round(v, 2) for v in e[:3]])
            last_place = final_leg and j == n - 1
            # A MAP OF TWO PARTS (Retomoto): the second chain is started by the jump, whenever the human takes it,
            # and the hook moves every bot to the street. A timer of the first chain that is still running then
            # would start the next TOWER step for a bot that stands in the street (what a Defend step does with a
            # place on another navigation part is not established: kl_fa_bots_rt). So behind the last loot wait
            # the first chain gets no timer: no hold on the tower's way out.
            # A GATE OF kl_fa_bots_rt (2026-10-11, re/retomoto_bots_rooms.md): the place a TriggerActorsDead follows is
            # itself a hold at a cover box, chosen there against the trigger boxes of the next fight (beyond the box
            # that wakes this fight's squads, out of the next one's). A cover of this module's choosing in its place
            # knows nothing of those boxes - on the first try it put a bot 6 m back from the reception's hold, and
            # within REACH of the gallery's hold lies the box that sends the second floor's men up. So: no hold of
            # ours there; the bot stands where the gate put it until the gate lets it go.
            # (Since the afternoon of 2026-10-11 the rule above it does the same for the whole of the tower's way
            # out: the gates stand behind the table's loot wait, last_loot_wait() no longer takes them for loot
            # waits, so `post` is true from the table on and the first chain gets no hold there at all. This rule
            # still acts where a TriggerActorsDead stands BEFORE the last loot wait - kl_fa_bots' --wait-guards.)
            gate_hold = j == n - 1 and nxt_kind is not None and nxt_kind['kind'] == 'dead'
            want_hold = (not is_loot_place and not last_place and not gate[j] and not gate_hold and (nx is not None or rally)
                         and (pers.out_holds or not post) and (pers.hold_out > 0 or not post) and (last_chain or not post))
            rally_here = rally and j == n - 1
            hold = None
            first_gap = gap * (pers.phase if holds == 0 else 1.0)
            if want_hold and (since >= first_gap or rally_here):
                key = (chain_no, i, j)
                tally['asked'] += 1
                got = find_holds(ctx, part, e, prev_pt or e, nx, pers, {c for c, n in taken.items() if n != N},
                                 [x for n, k, x in spots_taken if n != N or k == key], 1, post, tally)
                if got:
                    tally['found'] += 1
                    hold = got[0]
                    taken[hold[1]] = N; spots_taken.append((N, key, hold[0]))
            # (the last place of the squad's last chain is a step of its own: the dash to the vehicle, the only sprint)
            cut = (j == n - 1 or hold is not None or gate[j] or len(cur) >= F.STEP_MAX or (loot_leg and j == n - 2)
                   or (final_leg and last_chain and j == n - 2))
            if cut:
                r = {'kind': 'rout', 'name': uniq(cur_old), 'places': cur, 'sprint': False, 'way_out': post}
                routs.append(r); items.append(r)
                cur = []
                if hold is not None:
                    holds += 1
                    since = 0.0
                    pre = p['old'][:3]
                    r['hold'] = {'pre': pre, 'rally': rally_here, 'alts': [alt_of(ctx, hold)], 'boxes': {hold[1]}, 'search': (key, part, e, prev_pt or e, nx, post)}
                    if not rally_here:                  # (a rally: the build's own timer follows, the bot takes the cover while it runs)
                        sec = pers.hold_out if post else pers.hold_in
                        items.append({'kind': 'timer', 'name': uniq('%s_Timer_hold' % pre), 'seconds': sec}); secs += sec
            prev_pt = e
    # the dash: the last rout(s) of the LAST chain of the squad (the one that ends at the vehicle)
    if last_chain:
        for r in ([r for r in routs if r['way_out']] or routs[-1:])[-pers.sprint:]:
            r['sprint'] = True
    return items, secs, holds


# ------------------------------------------------------------------ nodes
def from_build(M, B, k):
    """Node k of the build (with its subtree) as a kl_fa_bots.Node that keeps its entity."""
    sc = B.sc
    nd = sc.nodes[k]
    n = F.Node(sc.names[k], sc.tids[k], M.adopt(nd['props'], sc.p.keys),
               [(M.adopt([nm], sc.p.keys)[0], M.adopt(body, sc.p.keys)) for nm, body in nd['ctrls']], B.ents[k - 1])
    n.keep, n.model, n.pos, n.src = B.ents[k - 1], B.ents[k - 1].model, B.at(k), k
    j = k + 1
    while j < sc.end[k]:
        n.add(from_build(M, B, j))
        j = sc.end[j]
    return n


MOD_FIELD = {'leash': 0, 'defend': 9, 'vision': 14, 'sixth': 16}


class Maker(F.Maker):
    """kl_fa_bots.Maker + the 16-bit fields (a RandomTrigger's weights)."""
    def unit(self, old, v):
        if old[0][0] == 0x08:
            return [(0x08, struct.pack('<H', v))]
        return F.Maker.unit(self, old, v)


def make(ctx, P, log=print):
    """The plan as nodes -> (maker, {top node of the build: Node}, [removed node indices])."""
    B, sc, opt = ctx.B, ctx.B.sc, P['options']
    M = Maker()
    out, removed = {}, []
    firsts = {}
    for N, q in ctx.squads.items():
        b, pers = P['bots'][N] if N in P['bots'] else P['bots'][str(N)], PERS[N]
        top = from_build(M, B, q['top'])
        old = {e['k'] for c in q['chains'] for e in c['elems'] if e['kind'] == 'defend'}
        removed += [j for k in old for j in range(k, sc.end[k])]
        top.kids = [n for n in top.kids if n.src not in old]
        by_name = {n.name: n for n in top.kids}
        path = lambda name: '%s%s%s%s' % (R_, q['name'], BS, name)
        if pers.attitude and opt['rusher']:
            M.set(top, 'ZSquadScript', {0: pers.attitude})
        actor = next(n for n in by_name[sc.names[q['group']]].walk() if n.src == q['actor'])
        zs = {}
        if pers.accuracy:
            zs[4] = float(pers.accuracy)
        if opt['sixth']:
            zs[16] = zs[17] = float(opt['sixth'])
        if zs:
            M.set(actor, 'ZSoldier', zs)

        def defend(name, places, single, nxt, sprint):
            g = top.add(M.clone(SX, FORM['defend'], name))
            g.keep = None
            M.place(g, (0.0, 0.0, 0.0))
            refs = []
            for j, p in enumerate(places):
                box = g.add(M.clone(SX, FORM['pos'], 'Pos#%02d' % (j + 1)))
                box.keep = None
                M.place(box, p)
                refs.append(path('%s%sPos#%02d' % (name, BS, j + 1)))
            # 'pos' form: field 0 = the one place, field 1 empty (540 of the stock bots' steps); 'rout': field 1 = 1..3
            M.set(g, 'DefendBehaviourRout', {0: refs[0] if single else '', 1: [] if single else refs, 2: 1, 3: 0,
                                             4: 'eDMS_Sprint' if sprint else 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: nxt, 8: 1, 9: 0})

        fork_gap = float(opt.get('fork_gap') or 0.0)        # '--fork-gap S': off by default (FORK_GAP above)
        entry = lambda it: it['name'] + '_gap' if (it['kind'] == 'fork' and fork_gap) else it['name']   # a fork is entered by its RandomTrigger (by its gap timer with '--fork-gap')
        def gap(name, target):
            """A TriggerDelay2 of fork_gap s named <name>_gap that starts the RandomTrigger <name>."""
            t = top.add(M.clone(SX, FORM['timer'], name + '_gap'))
            t.keep = None
            M.place(t, (0.0, 0.0, 0.0))
            M.set(t, 'TriggerDelay2', {0: fork_gap, 1: 0.0, 2: -1.0, 3: 0, 4: [path(target)]})

        def emit(items, after):
            """The nodes of a run of items; the last one starts `after` (a list of paths)."""
            for i, it in enumerate(items):
                nxt = [path(entry(items[i + 1]))] if i + 1 < len(items) else list(after)
                if it['kind'] == 'fork':
                    # stock F07 Squad#02 040_RandomTrigger_out_of_loot_area: {0: 1, 1..4: weights, 5..8: one target
                    # list each}; a way without a step of its own (the build's, where it has no way place) names
                    # what follows the fork
                    brs = it['branches']
                    if not nxt or not 2 <= len(brs) <= 4:
                        raise ValueError('%s: fork %s has %d ways and %d steps behind it' % (q['name'], it['name'], len(brs), len(nxt)))
                    r = top.add(M.clone(SX, FORM['random'], it['name']))
                    r.keep = None
                    M.place(r, (0.0, 0.0, 0.0))
                    w = [int(brs[j]['weight']) if j < len(brs) else 0 for j in range(4)]
                    lists = [([path(entry(brs[j]['items'][0]))] if brs[j]['items'] else nxt) if j < len(brs) else [] for j in range(4)]
                    M.set(r, 'RandomTrigger', {0: 1, 1: w[0], 2: w[1], 3: w[2], 4: w[3], 5: lists[0], 6: lists[1], 7: lists[2], 8: lists[3]})
                    if fork_gap:
                        gap(it['name'], it['name'])
                    for br in brs:
                        emit(br['items'], nxt)
                elif it['kind'] == 'rout':
                    fan = it.get('fan')
                    if fan and fan['kind'] == 'random':
                        nxt = nxt + [path(fan['name'] + '_gap' if fork_gap else fan['name'])]
                    elif fan:
                        nxt = nxt + [path(fan['alts'][0]['name'])]
                    defend(it['name'], it['places'], False, nxt, it['sprint'])
                    if fan:
                        for a in fan['alts']:
                            defend(a['name'], [a['place']], True, [], False)
                    if fan and fan['kind'] == 'random':
                        r = top.add(M.clone(SX, FORM['random'], fan['name']))
                        r.keep = None
                        M.place(r, (0.0, 0.0, 0.0))
                        w = [3 if j < len(fan['alts']) else 0 for j in range(4)]
                        lists = [[path(fan['alts'][j]['name'])] if j < len(fan['alts']) else [] for j in range(4)]
                        M.set(r, 'RandomTrigger', {0: 1, 1: w[0], 2: w[1], 3: w[2], 4: w[3], 5: lists[0], 6: lists[1], 7: lists[2], 8: lists[3]})
                        if fork_gap:
                            gap(fan['name'], fan['name'])
                elif it['kind'] == 'hold':
                    defend(it['name'], [it['place']], True, nxt, False)
                elif it['kind'] == 'timer':
                    t = top.add(M.clone(SX, FORM['timer'], it['name']))
                    t.keep = None
                    M.place(t, (0.0, 0.0, 0.0))
                    M.set(t, 'TriggerDelay2', {0: float(it['seconds']), 1: 0.0, 2: -1.0, 3: 0, 4: nxt})
                elif it['kind'] == 'mod':
                    g = top.add(M.clone(SX, FORM['mod'], it['name']))
                    g.keep = None
                    M.place(g, (0.0, 0.0, 0.0))
                    f = {9: 'eDM_NotSet', 26: nxt}
                    f.update({MOD_FIELD[k]: v for k, v in it['fields'].items()})
                    M.set(g, 'SquadModifierBehaviour', f)
                else:                                   # a wait or modifier of the build: only its NEXT (and a looter's seconds)
                    n = by_name[it['name']]
                    f = {NEXT[it['ctrl']]: nxt + list(it['also'])}
                    if it['ctrl'] == 'SquadModifierBehaviour' and not nxt:
                        f = {}
                    if it.get('loot_seconds') is not None:
                        f[1] = int(it['loot_seconds'])
                    if f:
                        M.set(n, it['ctrl'], f)

        for ci, items in enumerate(b['chains']):
            emit(items, [])
            if ci == 0:
                firsts[N] = path(entry(items[0]))
            else:
                old_first = q['chains'][ci]['elems'][0]['name']
                if items[0]['kind'] != 'rout' or items[0]['name'] != old_first:
                    raise ValueError('%s: the step %s is named from outside the squad and would change' % (q['name'], old_first))
        out[q['top']] = top
    by_top = {q['top']: N for N, q in ctx.squads.items()}
    was = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if k == ctx.timer][0][4]
    gates = {k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if k in [sc.resolve(s)[0] for s in was]}
    if gates:                                   # the room-first build: the gate counter names the first steps
        for g, gv in gates.items():
            gn = from_build(M, B, g)
            order = [sc.top[sc.resolve(s)[0]] for s in gv[4]]
            M.set(gn, 'TriggerCounter', {4: [firsts[by_top[x]] for x in order]})
            out[g] = gn
    else:
        t = from_build(M, B, ctx.timer)
        order = [sc.top[sc.resolve(s)[0]] for s in was]
        M.set(t, 'TriggerDelay2', {4: [firsts[by_top[x]] for x in order]})
        out[ctx.timer] = t
    return M, out, sorted(set(removed))


# ------------------------------------------------------------------ writing
def take_off(B, Jn, log=print):
    """Every FakeTarget of build B that fails the rule loses its controller in the joined scene Jn (same paths as
    B's) -> [dict], what dyn.json keeps as fake_targets_removed. Only a node's controller list changes."""
    gone = []
    for f in fake_targets(B):
        if not f['out']:
            continue
        hit = Jn.resolve(R_ + f['path'])
        if len(hit) != 1 or len(B.sc.resolve(R_ + f['path'])) != 1:
            raise ValueError('FakeTarget %s: its path names %d nodes of the new scene' % (f['path'], len(hit)))
        ctrls = Jn.nodes[hit[0]]['ctrls']
        idx = [i for i, (nm, _b) in enumerate(ctrls) if Jn.p.key(nm) == 'FakeTarget']
        if len(idx) != 1:
            raise ValueError('FakeTarget %s: the node has %d controllers of that name' % (f['path'], len(idx)))
        del ctrls[idx[0]]
        gone.append({'path': f['path'], 'at': [round(x, 1) for x in f['at']], 'outside': [round(x, 1) for x in f['out']], 'team': f['team'],
                     'cell': list(f['cell'][0]), 'registers': f['cell'][1]})
        log('FakeTarget taken off %s: at (%d, %d, %d) the place it registers at lies outside the vision space by (%d, %d, %d); kl2\'s own '
            'arithmetic: cell %s = %s - without a record its update writes 16 bytes behind ZCheckVisible\'s table every frame '
            '(re/crash_686a66.md)' % (f['path'], *f['at'], *f['out'], f['cell'][0],
                                      'a record, by the truncation alone' if f['cell'][1] else 'no record (0xff)'))
    return gone


def fake_fix(src, dst, log=print):
    """A copy of build src in folder dst in which the FakeTargets that fail the rule have lost their controller and
    NOTHING else differs: the .prp member alone (the squads' steps stay as they are - this is not the dynamic
    step). For a build that must not get the random routes, e.g. the Retomoto on the owner's tab.
    -> ([(severity, text)], report). Writes dyn_fake.json and a line in graft.txt; every other file is copied."""
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    say('kl_fa_bots_dyn fake-fix %s -> %s' % (src, dst))
    B = F.Built(src)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    before = F.sizes(B.folder)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'fake')
    if J.fingerprints(Jn)[0] != J.fingerprints(sc)[0] or J.text(Jn, Jn.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    say(space_words(vision_space(B)))
    gone = take_off(B, Jn, say)
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith('audit.'):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    rep = collections.OrderedDict(source=B.folder, out=dst, members_changed=['.prp'] if gone else [], fake_targets_removed=gone,
                                  big_before=before, big_after=after)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj) and gone:                     # kl_maps.audit compares the folder with what was measured
        import kl_maps
        st = json.load(open(sj))
        st['bots'] = sorted(set(st.get('bots') or []) | {'.prp'})
        st['same'] = [e for e in st.get('same', []) if e != '.prp']
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        for x in gone:
            f.write('kl_fa_bots_dyn fake-fix: FakeTarget controller taken off %s (outside the vision space: kl2 0x560630 wrote behind '
                    'ZCheckVisible\'s table, crash 0x686a66); nothing else of %s changed\n' % (x['path'], B.folder))
    say('written %s: %d FakeTarget controller(s) taken off; the .prp member %d -> %d bytes; every other member byte for byte'
        % (zp, len(gone), len(B['.prp']), len(prp)))
    out = []
    if before != after:
        out.append(('FAIL', 'a large block changed its size: %s -> %s' % (dict(before), dict(after))))
    bad = fake_diff(src, dst, say)
    out += [('FAIL', 'diff: ' + x) for x in bad]
    left = [f for f in fake_targets(F.Built(dst)) if f['out']]
    out += [('FAIL', 'FakeTarget on %s still fails the rule' % f['path']) for f in left]
    rep.update(check=[list(x) for x in out], diff=bad)
    say('RESULT (fake-fix): %s' % ('PASS: %d controller(s) off, nothing else changed' % len(gone) if not out else 'FAIL: %s' % [t for _s, t in out]))
    with open(os.path.join(dst, 'dyn_fake.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'dyn_fake.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def fake_expected(A):
    """What the step may take off build A outside the squads -> ([(path, node)] of the FakeTargets that fail the
    rule ON THE SOURCE, a scene like A's in which those nodes have no FakeTarget controller - for
    kl_prpjoin.fingerprints, which hashes names, classes, properties, controllers and the tree)."""
    sa = A.sc
    hits = [(f['path'], f['node']) for f in fake_targets(A) if f['out']]
    nodes = list(sa.nodes)
    for p, k in hits:
        n = dict(nodes[k])
        n['ctrls'] = [c for c in n['ctrls'] if sa.p.key(c[0]) != 'FakeTarget']
        if len(n['ctrls']) != len(nodes[k]['ctrls']) - 1:
            raise ValueError('FakeTarget %s: the node has not exactly one controller of that name' % p)
        nodes[k] = n
    import copy
    cut = copy.copy(sa)
    cut.nodes = nodes
    return hits, cut


def fake_diff(src, dst, log=print):
    """fake-fix's own diff -> list of UNEXPECTED differences: every member but the .prp byte for byte, the files
    beside the archive too, and the .prp = the source's with exactly the FakeTargets that fail the rule on the
    source taken off (whole-tree fingerprint, scene property block)."""
    A, Bn = F.Built(src), F.Built(dst)
    bad = []
    hits, cut = fake_expected(A)
    paths = [p for p, _k in hits]
    if A.sc.names != Bn.sc.names or A.sc.tids != Bn.sc.tids:
        bad.append('.prp / .gms: the entities are not the same list')
    elif J.fingerprints(cut)[0] != J.fingerprints(Bn.sc)[0]:
        bad.append('.prp: the tree is not the source\'s with %d FakeTarget controller(s) taken off (%s)' % (len(paths), ', '.join(p.split(BS)[0] for p in paths) or 'none'))
    if J.text(A.sc, A.sc.p.settings) != J.text(Bn.sc, Bn.sc.p.settings):
        bad.append('.prp: the scene property block differs')
    rest = [n for n in A.order if n != A.ext['.prp'] and A.files[n] != Bn.files.get(n)]     # every member by name, the menu XML too
    if rest or A.order != Bn.order:
        bad.append('other members differ: %s' % rest)
    skip = ('audit.', 'dyn_fake.', 'steps.json', 'graft.txt', os.path.basename(A.zp))
    side = [f for f in os.listdir(A.folder) if os.path.isfile(os.path.join(A.folder, f)) and not f.startswith(skip)]
    sdiff = [f for f in side if not os.path.isfile(os.path.join(Bn.folder, f)) or open(os.path.join(A.folder, f), 'rb').read() != open(os.path.join(Bn.folder, f), 'rb').read()]
    if sdiff:
        bad.append('files beside the archive differ: %s' % sdiff)
    log('.prp: the source\'s tree with %d FakeTarget controller(s) taken off (%s) and nothing else; the other %d members byte for byte; '
        '%d files beside the archive byte for byte' % (len(paths), ', '.join(p.split(BS)[0] for p in paths) or 'none', len(A.order) - 1, len(side)))
    for x in bad:
        log('UNEXPECTED: ' + x)
    return bad


def apply(ctx, P, dst, log=print):
    """Write the plan into a copy of the build in folder dst -> report dict."""
    B, sc = ctx.B, ctx.B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    before = F.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)

    M, made, removed = make(ctx, P, log)
    tops_new = [made[t] for t in sc.tops() if t in made]
    q, order = M.scene(tops_new)
    qtop = dict(zip([t for t in sc.tops() if t in made], q.tops()))
    Jn = J.join(sc, [(q, qtop[t]) if t in made else (sc, t) for t in sc.tops()], 'dyn')
    # ---- FakeTargets outside the vision space lose their controller (FAKE TARGETS at the top; the 0x686a66 crash).
    # Only the node's controller list in the .prp changes: no entity, no record, no other member.
    fake_gone = take_off(B, Jn, log) if P['options'].get('fake', True) else []
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    # ---- .gms / .buf: the squad groups' children anew; an entity that stays keeps its record
    A = B.scene
    slot0 = A.slots()
    gone = {B.ents[k - 1] for k in removed}
    for e in A.entities():
        if e not in gone and e.links and any(t in gone for t, _b in e.links):
            raise ValueError('%r is linked to a route step' % e)
    if any(a in gone or b in gone for a, b in A.pairs):
        raise ValueError('a room pair names a route step')
    free = sorted(e.ref for e in gone)
    ref_before = A.ref_slots
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    new_ents = {}

    def ent(n, parent):
        nonlocal nxt
        if getattr(n, 'keep', None) is not None:
            e = n.keep
        else:
            e = kl_scene.Entity()
            e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
            e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
            if free:
                e.ref = free.pop(0)
            else:
                e.ref = nxt; nxt += 1
            new_ents[id(n)] = e
        e.parent = parent
        e.kids = [ent(k, e) for k in n.kids]
        n.ent = e
        return e

    for t in tops_new:
        ent(t, None)
    A.ref_slots = max(A.ref_slots, nxt)
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    # ---- .oct / .rmi / .rmc: every slot id moved; the squad's groups are listed anew with the box of their places
    slot1 = A.slots()
    root3 = octx.rooms[0][3]
    squad_old = {slot0[B.ents[k - 1]] + 2 for N, sq in ctx.squads.items() for k in range(sq['top'], sc.end[sq['top']])}
    listed_before = {it[0] for it in root3.items} & squad_old if root3 is not None else set()
    tree = bool(P['options']['tree']) and bool(listed_before)
    elsewhere = sum(1 for r, room in enumerate(octx.rooms) for ti, t in enumerate(room) if t is not None and (r, ti) != (0, 3)
                    for it in t.items if it[0] in squad_old)
    if elsewhere:
        raise ValueError('%d room-tree items outside the root\'s group tree name a squad entity' % elsewhere)
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    drop = {slot0[e] + 2 for e in gone} | listed_before
    octn, rmin, rmcn = O.remap_ids(octx, ids, drop), O.remap_ids(rmi, ids, drop), O.remap_ids(rmc, ids, drop)
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in tops_new:
        for n in t.walk():
            if not n.tid & kl_scene.GROUP or n.name.startswith('Glazer_'):
                continue
            ps = [k.pos for k in n.walk() if k.name.startswith('Pos#')]
            if n.name.startswith(F.SQUAD + 'Squad#'):
                ps = ps + [k.pos for k in n.kids if k.name.startswith('Glazer_')]
            if ps:
                lo = tuple(min(p[a] for p in ps) - 10.0 for a in range(3))
                hi = tuple(max(p[a] for p in ps) + (10.0 if a != 1 or not n.name.startswith(F.SQUAD) else 190.0) for a in range(3))
                items.append((slot1[n.ent] + 2, lo, hi))
    listed, repointed, new_prm = 0, 0, None
    if tree and items:
        octn.rooms[0][3] = O.join_trees(octn.rooms[0][3], O.build_tree(items, root3.origin, root3.scale))
        listed = len(items)
        octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    if move:
        prm = bytearray(B['.prm'])
        t, n = struct.unpack_from('<II', prm, 0)
        oldrefs = set(octx.record_refs())
        for i in range(1, n):
            o, size = struct.unpack_from('<II', prm, t + 16 * i)
            if size == 64 and prm[o:o + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', prm, o + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', prm, o + 0x1c, move[v]); repointed += 1
                elif v and v not in oldrefs:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(prm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
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
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'dyn.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    added = [n for t in tops_new for n in t.walk() if getattr(n, 'keep', None) is None]
    rep = collections.OrderedDict(
        source=B.folder, out=dst, members_changed=changed, entities_before=len(B.ents), entities=len(ents), entities_removed=len(gone),
        entities_added=len(added), classes_added=dict(collections.Counter(J.schema('dd').geoms.get(n.tid) for n in added)),
        controllers_added=dict(collections.Counter(M.p.key(nm) for n in added for nm, _b in n.ctrls)),
        ref_slots=[ref_before, A.ref_slots], slot_ids_moved=moved, groups_listed_in_root_tree_3=listed,
        groups_unlisted=len(listed_before), prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post,
        fake_targets_removed=fake_gone, big_before=before, big_after=after)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):                              # kl_maps.audit compares the folder with what was measured
        import kl_maps
        st = json.load(open(sj))
        st['bots'] = sorted(set(st.get('bots') or []) | set(changed))
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_bots_dyn: the AI heisters\' steps made anew (%d entities out, %d in) from %s; options %s\n'
                % (len(gone), len(added), B.folder, json.dumps(P['options'], sort_keys=True)))
        for x in fake_gone:
            f.write('kl_fa_bots_dyn: FakeTarget controller taken off %s (outside the vision space: kl2 0x560630 wrote behind ZCheckVisible\'s '
                    'table, crash 0x686a66)\n' % x['path'])
    log('written %s: %d entities removed (the old route steps), %d added (%s); members changed: %s; %d slot ids renumbered, %d groups '
        'listed in the root\'s group tree (%d were), %d model roots of the .prm re-pointed at their moved .oct records'
        % (zp, len(gone), len(added), ', '.join('%s %d' % kv for kv in rep['classes_added'].items()), ' '.join(changed), moved, listed,
           len(listed_before), repointed))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    if before != after:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    return rep


# ------------------------------------------------------------------ the check of this module
def graph(ctx_or_B):
    """The squads of a (dynamic) build as they run -> {squad name: dict}: per chain the walked items, the holds
    (walked or behind a RandomTrigger), timers, modifiers."""
    B = ctx_or_B
    sc = B.sc
    tops = [t for t in sc.tops() if sc.names[t].startswith(F.SQUAD)]
    mine = {k for t in tops for k in range(t, sc.end[t])}
    timer = sc.resolve(R_ + F.SQUAD + 'Timer_start_bots')[0]
    ctrl = {}
    for cn in list(NEXT) + ['RandomTrigger', 'RelayMessageList']:
        for k, _i, v in kl_fa.controllers(sc, cn):
            if k in mine and k != timer:
                ctrl[k] = (cn, v)
    firsts = [j for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if k == timer for s in v[4] for j in sc.resolve(s)]
    gates = {k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if k in mine}
    if firsts and all(j in gates for j in firsts):        # the room-first build: through the gate counter
        firsts = [j for g in firsts for s in gates[g][4] for j in sc.resolve(s)]
    entries = collections.defaultdict(list)
    for k in firsts:
        entries[sc.top[k]].append(k)
    for k, _h, _f, _s, hit in J.references(sc):
        if k >= 0 and k not in mine:
            for j in hit or ():
                if j in ctrl and j not in entries[sc.top[j]]:
                    entries[sc.top[j]].append(j)
    out = collections.OrderedDict()
    for t in tops:
        actors = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        if not actors:
            continue
        g = {'top': t, 'actor': actors[0], 'chains': [], 'sets': [], 'forks': collections.OrderedDict(), 'reached': set(), 'faults': []}
        # A chain that FORKS (a RandomTrigger as the next link) is walked once per BRANCH SET v = 0, 1, ..: at every
        # fork branch v mod (its number of ways). g['chains'][c] is branch set 0 (every fork's first way = the
        # build's), g['sets'][c] all of them; every way of every fork is in at least one. An item that is the first
        # step of a way carries 'fork' = (the RandomTrigger, the way's index); g['forks'][node] says what it draws from.
        jobs = [(k, 0, c) for c, k in enumerate(entries.get(t, []))]
        for k, variant, c_no in jobs:
            chain, seen, widest, via = [], set(), 1, None
            while k is not None and k not in seen:
                seen.add(k); g['reached'].add(k)
                cn, v = ctrl.get(k, (None, None))
                if cn == 'RandomTrigger':
                    ws, lists = list(v[1:5]), [[x for s in lst for x in sc.resolve(s)] for lst in v[5:9]]
                    if variant == 0:
                        if v[0] != 1:
                            g['faults'].append('%s: field 0 is %s (stock: 1)' % (sc.names[k], v[0]))
                        for w, tg, lst in zip(ws, lists, v[5:9]):
                            if bool(w) != bool(lst) or len(tg) != len(lst) or len(tg) > 1:
                                g['faults'].append('%s: weight %s with %d targets, %d of them resolve (stock: one target for every weight that is not 0)' % (sc.names[k], w, len(lst), len(tg)))
                        if any(sc.top[x] != t for tg in lists for x in tg):
                            g['faults'].append('%s names a step of another squad' % sc.names[k])
                    br = [tg[0] for w, tg in zip(ws, lists) if w and tg]
                    g['forks'][k] = {'name': sc.names[k], 'ways': br, 'weights': [w for w, tg in zip(ws, lists) if w and tg]}
                    if len(br) < 2:
                        g['faults'].append('%s: a fork with %d way(s)' % (sc.names[k], len(br))); break
                    widest = max(widest, len(br))
                    via = (k, variant % len(br))
                    k = br[variant % len(br)]
                    continue
                if cn is None or cn in ('RandomTrigger', 'RelayMessageList'):
                    g['faults'].append('the chain reaches %s, which is no step of a chain' % sc.names[k]); break
                nx = [j for s in v[NEXT[cn]] for j in sc.resolve(s)]
                it = {'k': k, 'name': sc.names[k], 'ctrl': cn, 'v': v, 'side': [], 'fork': via}
                via = None
                if cn == 'DefendBehaviourRout':
                    it['places'] = [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in sc.resolve(s)]
                for j in nx[1:]:                        # what is started beside the next link
                    g['reached'].add(j)
                    cj, vj = ctrl.get(j, (None, None))
                    if cj == 'TriggerDelay2' and sc.names[j].endswith('_gap'):     # a '--fork-gap' timer: look through it
                        tg = [x for s in vj[4] for x in sc.resolve(s)]
                        if len(tg) == 1 and ctrl.get(tg[0], (None,))[0] == 'RandomTrigger':
                            j = tg[0]; cj, vj = ctrl[j]; g['reached'].add(j)
                        else:
                            g['faults'].append('%s does not name one RandomTrigger' % sc.names[j])
                    if cj == 'RandomTrigger':
                        alts = []
                        for w, lst in zip(vj[1:5], vj[5:9]):
                            tg = [x for s in lst for x in sc.resolve(s)]
                            if bool(w) != bool(tg) or len(tg) > 1:
                                g['faults'].append('%s: weight %s with %d targets' % (sc.names[j], w, len(tg)))
                            alts += tg
                        if vj[0] != 1:
                            g['faults'].append('%s: field 0 is %s (stock: 1)' % (sc.names[j], vj[0]))
                        it['side'].append(('random', j, alts))
                        g['reached'].update(alts)
                    elif cj == 'DefendBehaviourRout':
                        it['side'].append(('one', j, [j]))
                    elif cj == 'RelayMessageList':
                        it['side'].append(('relay', j, []))
                    else:
                        g['faults'].append('%s also starts %s (%s)' % (sc.names[k], sc.names[j], cj))
                chain.append(it)
                k = nx[0] if nx else None
            if variant == 0:
                g['chains'].append(chain); g['sets'].append([chain])
                jobs += [(jobs[c_no][0], n_v, c_no) for n_v in range(1, widest)]
            else:
                g['sets'][c_no].append(chain)
        g['faults'] = list(dict.fromkeys(g['faults']))
        g['ctrl'] = {k: v for k, v in ctrl.items() if sc.top[k] == t}
        out[sc.names[t]] = g
    return out


def check(folder, log=print, base=True):
    """kl_fa_bots.check (and kl_fa_bots_rt.check on a map of two parts) + what they do not look at: the holds
    behind a RandomTrigger, covers, sprint, timers, modifiers. -> ([(severity, text)], facts)."""
    out, facts = [], collections.OrderedDict()
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    quiet = lambda *a, **k: None
    ctx = None
    B = F.Built(folder)
    sc = B.sc
    G = graph(B)
    two_part = any(len(g['chains']) > 1 for g in G.values())
    if base:
        o1, f1 = F.check(folder, log)
        facts['kl_fa_bots'] = {'FAIL': sum(s == 'FAIL' for s, _t in o1), 'NOTE': sum(s == 'NOTE' for s, _t in o1)}
        out += [(s, 'kl_fa_bots.check: ' + t) for s, t in o1 if s == 'FAIL']
        if two_part:
            import kl_fa_bots_rt as RT
            o2, f2 = RT.check(folder, log)
            facts['kl_fa_bots_rt'] = {'FAIL': sum(s == 'FAIL' for s, _t in o2), 'NOTE': sum(s == 'NOTE' for s, _t in o2)}
            out += [(s, 'kl_fa_bots_rt.check: ' + t) for s, t in o2 if s == 'FAIL']
    bj = os.path.join(B.folder, 'bots.json')
    popt = json.load(open(bj)).get('plan', {}).get('options', {}) if os.path.isfile(bj) else {}
    nav = F.Nav(B.scene.nav, links=bool(popt.get('drop')))
    grid = Grid(nav)
    S = F.stations(B, nav)
    exits, lane = S['exits'], F.lanes(B)
    hops = {(tuple(pa), tuple(pb)) for ds in nav.drops.values() for _j, pa, pb, _k in ds}
    covers = [c for c in cover_boxes(B) if not c['hidden']]
    RT = None
    if two_part:
        import kl_fa_bots_rt as RT
    name = lambda k: sc.path[k][5:]
    near_cover = lambda p: min([math.dist(p, c['at']) for c in covers] or [1e9])
    stock_mod = {('eDM_Tight',), ('eDM_Loose',), ('eLM_Unleash', 'eDM_Tight'), ('eLM_Leash', 'eDM_Tight'), ('eLM_Leash', 'eDM_Loose')}
    rows, all_holds = collections.OrderedDict(), []
    d_all, d_hold = [], []
    join_waits = collections.OrderedDict()              # {squad: (gate waits behind the last loot wait, loot waits)} of a chain the jump cuts off
    for sq, g in G.items():
        for t in g['faults']:
            fail('%s: %s' % (sq, t))
        loose = [name(k) for k in g['ctrl'] if k not in g['reached']]
        if loose:
            fail('%s: %d step(s) nothing starts, e.g. %s' % (sq, len(loose), loose[0]))
        sp = B.at(g['actor'])
        new_row = lambda: collections.OrderedDict(defend_steps=0, sprint=0, holds=0, random=0, alternatives=0, timers=0.0, places=0, modifiers=[], loot_seconds=[], steps=[])
        row0 = new_row()
        row0['forks'], row0['fork_ways'] = len(g['forks']), [len(f['ways']) for f in g['forks'].values()]
        counted, ways_done = set(), {}
        # every BRANCH SET of every chain (graph()): set 0 is the build's own way at every fork and fills the row;
        # the further sets bring the other ways of the forks, which get the same rules (an item is counted once)
        for ci, vi, chain in [(ci, vi, ch) for ci, cset in enumerate(g['sets']) for vi, ch in enumerate(cset)]:
            row = row0 if vi == 0 else new_row()
            prev = None
            pts_chain = [B.at(j) for it in chain if it['ctrl'] == 'DefendBehaviourRout' for j in it['places']]
            if pts_chain:
                h = nav.at(*pts_chain[0], dy=15.0)
                part = h and nav.part[h[0]]
            # 'the last loot wait' as last_loot_wait() takes it: on a chain that the jump cuts off the table's own wait,
            # not a gate of kl_fa_bots_rt (a TriggerActorsDead behind it). Until 2026-10-11 afternoon a gate counted as
            # a loot wait here, the rule below looked at the last leg alone and the first gates build passed with 36
            # timers of this module between its gates (re/retomoto_bots_rooms_review.md D1).
            is_loot = lambda it: it['ctrl'] == 'TriggerLootDepleted' or (it['ctrl'] == 'TriggerDelay2' and 'done_looting' in it['name'])
            cut_off = ci < len(g['chains']) - 1
            loot_i = [i for i, it in enumerate(chain) if is_loot(it)]
            n_wait_last = loot_i[-1] if (cut_off and loot_i) else max([i for i, it in enumerate(chain) if is_loot(it) or it['ctrl'] == 'TriggerActorsDead'],
                                                                      default=-1)
            if cut_off:
                # (a '--fork-gap' timer is as good as the RandomTrigger it precedes: not a timer in this sense)
                late = [it['name'] for i, it in enumerate(chain) if i > n_wait_last and it['ctrl'] == 'TriggerDelay2' and not it['name'].endswith('_gap')]
                if late:
                    fail('%s: timer %s runs behind the last loot wait of a chain that the jump cuts off: it would start a step of this '
                         'part for a bot the hook has moved to the next (%d such timer(s) in this branch set)' % (sq, late[0], len(late)))
                # THE SAME HAZARD, NOT OF THIS MODULE'S MAKING: the waits of the build that stand there. A wait that is
                # armed when the human takes the join fires later (a TriggerActorsDead 30 s after it was armed at the
                # latest, kl2 0x4afbbd; a loot wait after its seconds) and sends 'AITrigger' to the next step of THIS
                # part, which has never run and so starts (0x4ebed0) - for a bot that stands on the next part. Counted
                # and said, once for the build; whether it strands a bot is not established (no joined run with bots).
                if vi == 0:
                    join_waits[sq] = ([it['name'] for i, it in enumerate(chain) if i > n_wait_last and it['ctrl'] == 'TriggerActorsDead'],
                                      [it['name'] for i, it in enumerate(chain) if i <= n_wait_last and is_loot(it)])
            walked = []                                 # (index in chain, place) of every walked place
            for i, it in enumerate(chain):
                if it['ctrl'] == 'DefendBehaviourRout':
                    walked += [(i, B.at(j)) for j in it['places']]
            for i, it in enumerate(chain):
                cn, v = it['ctrl'], it['v']
                fresh = it['k'] not in counted
                counted.add(it['k'])
                if cn == 'DefendBehaviourRout':
                    row['defend_steps'] += 1
                    row['sprint'] += v[4] == 'eDMS_Sprint'
                    if v[4] not in ('eDMS_NotSet', 'eDMS_Sprint'):
                        fail('%s: %s moves with %s (stock bots: eDMS_NotSet or eDMS_Sprint only - no other set is proven for their animation set)' % (sq, it['name'], v[4]))
                    if not it['places'] or len(it['places']) > F.STEP_MAX:
                        fail('%s: %s names %d places (stock: 1..3)' % (sq, it['name'], len(it['places'])))
                    single = bool(v[0]) and not v[1]
                    row['places'] += len(it['places'])
                    for j in it['places'] if fresh else ():
                        d_all.append(near_cover(B.at(j)))
                    row['steps'].append('%s %s %s' % (it['name'], 'pos' if single else 'rout', 'SPRINT' if v[4] == 'eDMS_Sprint' else ''))
                    if single and 'pos_cover' in it['name']:
                        row['holds'] += 1
                        if fresh:
                            all_holds.append((sq, ci, i, B.at(it['places'][0]), prev, it['name']))
                            d_hold.append(near_cover(B.at(it['places'][0])))
                    else:
                        prev = B.at(it['places'][-1])
                elif cn == 'TriggerDelay2':
                    row['timers'] += v[0]
                    row['steps'].append('%s %g s' % (it['name'], v[0]))
                    if v[1] != 0.0 or v[2] != -1.0 or v[3] != 0:
                        fail('%s: %s fields 1..3 are %s (every stock bot timer: 0.0, -1.0, 0)' % (sq, it['name'], v[1:4]))
                elif cn == 'TriggerLootDepleted':
                    row['loot_seconds'].append(v[1])
                    row['steps'].append('%s %d objects, %d s' % (it['name'], len(v[0]), v[1]))
                    if not 15 <= v[1] <= 60:
                        note('%s: %s waits %d s (stock bots: 15, 20, 60)' % (sq, it['name'], v[1]))
                elif cn == 'SquadModifierBehaviour':
                    setv = tuple(x for x in v[:24] if isinstance(x, str) and not x.endswith('NotSet') and x != 'eSC_Enabled')
                    row['modifiers'].append('%s: %s' % (it['name'], ' '.join(setv)))
                    row['steps'].append('%s %s' % (it['name'], ' '.join(setv)))
                    core = tuple(x for x in setv if not x.startswith(('eVIM_', 'eCSS_')))
                    if core and core not in stock_mod:
                        fail('%s: %s sets %s, which no stock bot squad has' % (sq, it['name'], core))
                    extra = [x for x in setv if x.startswith(('eVIM_', 'eCSS_'))]
                    if any(x not in ('eVIM_Factor_2_0', 'eVIM_Factor_4_0', 'eCSS_Enabled') for x in extra):
                        fail('%s: %s sets %s (Fragile Alliance police: vision x 2 or x 4)' % (sq, it['name'], extra))
                for kind, j, alts in it['side']:
                    if kind == 'relay':
                        continue
                    if cn not in ('DefendBehaviourRout',):
                        fail('%s: %s (%s) starts a hold beside its next link' % (sq, it['name'], cn))
                    if kind == 'random':
                        row['random'] += 1
                        row['alternatives'] += len(alts)
                        if len(alts) < 2:
                            fail('%s: %s chooses between %d places' % (sq, name(j), len(alts)))
                    nxt_i = i + 1
                    if nxt_i >= len(chain) or chain[nxt_i]['ctrl'] != 'TriggerDelay2':
                        fail('%s: %s starts a hold beside something that is no timer: the chain would not wait for it' % (sq, it['name']))
                    row['steps'].append('   + %s: %s' % ('RandomTrigger ' + sc.names[j] if kind == 'random' else 'hold', ', '.join(sc.names[a] for a in alts)))
                    for a in alts:
                        ca, va = g['ctrl'].get(a, (None, None))
                        if ca != 'DefendBehaviourRout' or not va[0] or va[1] or va[7]:
                            fail('%s: %s is no single-place hold without a NEXT' % (sq, name(a))); continue
                        pl = [x for x in sc.resolve(va[0])]
                        if len(pl) != 1:
                            fail('%s: %s: its place does not resolve' % (sq, name(a))); continue
                        row['holds'] += kind == 'one' or a == alts[0]
                        if fresh:
                            all_holds.append((sq, ci, i, B.at(pl[0]), B.at(it['places'][-1]), sc.names[a]))
                            d_hold.append(near_cover(B.at(pl[0])))
                            d_all.append(d_hold[-1])
                        # the rules a walked place has to obey, for a place the chain does not walk
                        p = B.at(pl[0])
                        e = B.at(it['places'][-1])
                        hit, he = nav.at(p[0], p[1], p[2], dy=15.0), nav.at(e[0], e[1], e[2], dy=15.0)
                        if hit is None or he is None or nav.part[hit[0]] != nav.part[he[0]]:
                            fail('%s: hold %s at (%d, %d, %d) is not on the mesh part of the place before it' % (sq, sc.names[a], *p)); continue
                        if nav.clearance(*p) < F.CLEAR_MIN:
                            fail('%s: hold %s is %d from a mesh edge without a neighbour' % (sq, sc.names[a], nav.clearance(*p)))
                        if grid.warp(hit[0]) > WARP:
                            fail('%s: hold %s stands on a polygon whose fitted height is off by %d' % (sq, sc.names[a], grid.warp(hit[0])))
                        e4, p4 = tuple(e) + (he[0],), tuple(p) + (hit[0],)
                        got = nav.path(e4, p4)
                        if got is None or got[1] > HOLD_PATH + 1.0:
                            fail('%s: hold %s: %s from the place before it' % (sq, sc.names[a], 'no path' if got is None else '%d of path' % got[1]))
                        after = next((pt for ii, pt in walked if ii > i), None)
                        if after is not None:
                            ha = nav.at(after[0], after[1], after[2], dy=15.0)
                            if ha is None or nav.path(p4, tuple(after) + (ha[0],)) is None:
                                fail('%s: hold %s: no path on to the next place' % (sq, sc.names[a]))
                        if exits and not F.in_exit(B, exits, e):
                            pts = [e, p] + ([after] if after is not None and not F.in_exit(B, exits, after) else [])
                            if F.in_exit(B, exits, p) or F.first_exit_entry(B, nav, exits, pts):
                                fail('%s: hold %s is in a level exit box, or the way to / from it is, before the route itself enters one' % (sq, sc.names[a]))
                        if lane and F.lane_dist(lane, p) < F.LANE_HALF + F.LANE_MAN:
                            fail('%s: hold %s is %d from the escape vehicle\'s line: IN ITS LANE' % (sq, sc.names[a], F.lane_dist(lane, p)))
                        if RT is not None and nav.part[hit[0]] != S['home'] and RT.lane(p):
                            fail('%s: hold %s is in the van\'s lane' % (sq, sc.names[a]))
            # THE WAYS OF THE FORKS met in this branch set. A way = its own steps from the RandomTrigger to the step
            # where all its ways meet again; A = the place walked before the fork, Z = the first place behind it.
            # Rules (each a FAIL): the ways meet, and share no step before they do; every place of the way on the
            # mesh part of A, clear of the mesh's edge, on no warped polygon; a path A -> its places -> Z without a
            # link; not in or through a level exit box unless A already is in one; not in the escape vehicle's lane
            # behind the last loot wait; not in the van's lane (Retomoto's street).
            is_place = lambda x: x['ctrl'] == 'DefendBehaviourRout' and not (x['v'][0] and not x['v'][1] and 'pos_cover' in x['name'])
            for i, it in enumerate(chain):
                if not it['fork'] or it['fork'] in ways_done:
                    continue
                rk, b = it['fork']
                fk = g['forks'][rk]
                if 'meet' not in fk:
                    lists = []
                    for w in fk['ways']:
                        lst, k = [], w
                        while k is not None and k not in lst:
                            lst.append(k)
                            cj, vj = g['ctrl'].get(k, (None, None))
                            nx = [j for s in vj[NEXT[cj]] for j in sc.resolve(s)] if cj in NEXT else []
                            k = nx[0] if nx else None
                        lists.append(lst)
                    common = set(lists[0]).intersection(*lists[1:])
                    fk['meet'] = next((x for x in lists[0] if x in common), None)
                    if fk['meet'] is None:
                        fail('%s: the ways of fork %s never meet again' % (sq, fk['name']))
                    else:
                        fk['own'] = [lst[:lst.index(fk['meet'])] for lst in lists]
                        flat_own = [x for o in fk['own'] for x in o]
                        if len(flat_own) != len(set(flat_own)):
                            fail('%s: two ways of fork %s share a step before they meet' % (sq, fk['name']))
                        if sum(1 for o in fk['own'] if not o) > 1:
                            fail('%s: two ways of fork %s have no step of their own' % (sq, fk['name']))
                if fk['meet'] is None:
                    continue
                own, i1 = set(fk['own'][b]), i
                while i1 < len(chain) and chain[i1]['k'] in own:
                    i1 += 1
                if i1 >= len(chain) or chain[i1]['k'] != fk['meet']:
                    fail('%s: way %d of fork %s does not run on to %s' % (sq, b + 1, fk['name'], sc.names[fk['meet']])); continue
                pts = [B.at(j) for x in chain[i:i1] if is_place(x) for j in x['places']]
                before = [B.at(j) for x in chain[:i] if is_place(x) for j in x['places']]
                behind = [B.at(j) for x in chain[i1:] if is_place(x) for j in x['places']]
                A, Z = before[-1] if before else (sp if ci == 0 else None), behind[0] if behind else None
                tag = '%s: way %d of fork %s' % (sq, b + 1, fk['name'])
                if A is None or Z is None:
                    fail('%s has no place before it or none behind it' % tag); continue
                if b == 0:
                    fk['base'] = {tuple(round(x) for x in p) for p in pts}
                seq = [A] + pts + [Z]
                hits = [nav.at(p[0], p[1], p[2], dy=15.0) for p in seq]
                if any(h is None for h in hits):
                    fail('%s: a place of it is not on the mesh, e.g. (%d, %d, %d)' % (tag, *seq[[h is None for h in hits].index(True)])); continue
                if len({nav.part[h[0]] for h in hits}) > 1:
                    fail('%s: its places are not on one mesh part' % tag); continue
                for p, h in list(zip(seq, hits))[1:-1]:
                    if nav.clearance(*p) < F.CLEAR_MIN:
                        fail('%s: (%d, %d, %d) is %d from a mesh edge without a neighbour' % (tag, *p, nav.clearance(*p)))
                    # (the warp rule is for the places THIS module made: way 1 is the build's own way, its places are
                    # kl_fa_bots' - M02 and M06 have some on large uneven polygons - and a side way keeps the ones it
                    # found no room beside. They are under kl_fa_bots.check's rules, in every branch set.)
                    if grid.warp(h[0]) > (WARP_HOME if nav.part[h[0]] == S['home'] else WARP) and b and tuple(round(x) for x in p) not in fk.get('base', ()):
                        fail('%s: (%d, %d, %d) stands on a polygon whose fitted height is off by %d' % (tag, *p, grid.warp(h[0])))
                    if lane and i > n_wait_last and F.lane_dist(lane, p) < F.LANE_HALF + F.LANE_MAN:
                        fail('%s: (%d, %d, %d) is %d from the escape vehicle\'s line: IN ITS LANE' % (tag, *p, F.lane_dist(lane, p)))
                    if RT is not None and nav.part[h[0]] != S['home'] and RT.lane(p):
                        fail('%s: (%d, %d, %d) is in the van\'s lane' % (tag, *p))
                length = 0.0
                for (u, hu), (w, hw) in zip(zip(seq, hits), list(zip(seq, hits))[1:]):
                    got = nav.path(tuple(u) + (hu[0],), tuple(w) + (hw[0],))
                    if got is None or any((tuple(x), tuple(y)) in hops for x, y in zip(got[0], got[0][1:])):
                        fail('%s: %s from (%d, %d, %d) to (%d, %d, %d)' % (tag, 'no path' if got is None else 'the path takes a one-way link', *u, *w)); length = None; break
                    length += got[1]
                if exits and not F.in_exit(B, exits, A):
                    if any(F.in_exit(B, exits, p) for p in pts) or F.first_exit_entry(B, nav, exits, [A] + pts + ([] if F.in_exit(B, exits, Z) else [Z])):
                        fail('%s is in or through a level exit box before the route itself enters one' % tag)
                ways_done[it['fork']] = length
        fork_list = []
        for rk, fk in g['forks'].items():
            ls = [ways_done.get((rk, b)) for b in range(len(fk['ways']))]
            if any((rk, b) not in ways_done for b in range(len(fk['ways']))):
                fail('%s: fork %s: a way of it was not walked and checked' % (sq, fk['name']))
            elif all(x is not None for x in ls) and max(ls) > ROUTE_LONG[0] * min(ls) + ROUTE_LONG[1]:
                note('%s: fork %s: its ways are %s long' % (sq, fk['name'], [round(x) for x in ls]))
            fork_list.append({'name': fk['name'], 'weights': fk['weights'], 'lengths': [x and round(x) for x in ls]})
        row = row0
        row['fork_list'] = fork_list
        if not BUDGET[0] <= row['timers'] <= BUDGET[1]:
            note('%s: %.0f s of timers (stock bots: %d..%d s)' % (sq, row['timers'], *BUDGET))
        rows[sq] = row
    n_gate = [len(a) for a, _b in join_waits.values()]
    n_loot = [len(b) for _a, b in join_waits.values()]
    facts['join_waits'] = {sq: {'gates': a, 'loot': b} for sq, (a, b) in join_waits.items()}
    if any(n_gate):
        first = next(a for a, _b in join_waits.values() if a)
        note('THE JOIN: every bot has %s TriggerActorsDead wait(s) behind the last loot wait of the chain that the jump cuts off (%s .. %s; '
             'kl_fa_bots_rt\'s gates) and %s loot wait(s) before them. One that is armed when the human takes the join fires up to 30 s later and '
             'starts the next step of THAT part for a bot the hook has moved on - the hazard this check FAILs a timer of this module for. Not '
             'established what such a bot then does: wanted before the build goes on the tab, ONE JOINED RUN with bots waiting at a gate '
             '(re/retomoto_bots_rooms.md 7, run J1)'
             % ('%d' % n_gate[0] if len(set(n_gate)) == 1 else '%d..%d' % (min(n_gate), max(n_gate)), first[0], first[-1],
                '%d' % n_loot[0] if len(set(n_loot)) == 1 else '%d..%d' % (min(n_loot), max(n_loot))))
    # the walked single holds: within reach of a cover box
    for sq, ci, i, p, e, nm in all_holds:
        d = near_cover(p)
        if d > 500.0:
            fail('%s: hold %s at (%d, %d, %d) is %d from the nearest cover box (DefendCover looks within 500: kl2 0x84dc90)' % (sq, nm, *p, d))
        elif d > 260.0:
            note('%s: hold %s is %d from the nearest cover box' % (sq, nm, d))
    # a cover box belongs to one bot: no two bots' hold places within 60 of one another, anywhere on the map
    clash = 0
    for a in range(len(all_holds)):
        for b in range(a + 1, len(all_holds)):
            x, y = all_holds[a], all_holds[b]
            if x[0] != y[0] and hdist(x[3], y[3]) < 60.0 and abs(x[3][1] - y[3][1]) < 150.0:
                clash += 1
                if clash <= 3:
                    fail('%s %s and %s %s hold %d apart' % (x[0], x[5], y[0], y[5], hdist(x[3], y[3])))
    med = lambda a: round(sorted(a)[len(a) // 2]) if a else None
    share = lambda a, r: round(100.0 * sum(x <= r for x in a) / len(a)) if a else None
    facts['covers'] = {'boxes': len(covers), 'high': sum(c['kind'] == 'high' for c in covers), 'low': sum(c['kind'] == 'low' for c in covers),
                       'car': sum(c['kind'] == 'car' for c in covers)}
    facts['places_to_cover'] = {'places': len(d_all), 'median': med(d_all), 'within_500_pct': share(d_all, 500.0), 'within_250_pct': share(d_all, 250.0)}
    facts['holds_to_cover'] = {'places': len(d_hold), 'median': med(d_hold), 'within_250_pct': share(d_hold, 250.0)}
    facts['squads'] = rows
    facts['big'] = F.sizes(folder)
    # no FakeTarget outside the vision space (FAKE TARGETS at the top; this rule is the one that fails the build of
    # the 0x686a66 crash, z_route\retomoto_full, and every Retomoto build since kl_fa_street parked the spare vans)
    space = vision_space(B)
    fts = fake_targets(B, space)
    facts['fake_targets'] = {'all': len(fts), 'outside': sum(1 for f in fts if f['out']),
                             'vision_space': space and {'sure': {'lo': [round(x, 1) for x in space['sure'][0]], 'hi': [round(x, 1) for x in space['sure'][1]], 'records': space['sure'][2]},
                                                        'all': {'lo': [round(x, 1) for x in space['all'][0]], 'hi': [round(x, 1) for x in space['all'][1]], 'records': space['all'][2]},
                                                        'own': space['own'], 'unknown': space['unknown'], 'skipped': space['skipped']},
                             'cells': [{'path': f['path'], 'at': [round(x, 1) for x in f['at']], 'cell': list(f['cell'][0]), 'registers': f['cell'][1]} for f in fts if f['cell']]}
    for f in fts:
        if f['out']:
            fail('FakeTarget on %s stands at (%d, %d, %d): the place it registers at (140 higher) lies outside the vision space by (%d, %d, %d); '
                 'kl2\'s own arithmetic (0x59c790) on the box: cell %s = %s. Without a record its update 0x560630 writes its cell and place into '
                 'record 0xff of a table of 200 - 16 bytes behind the ZCheckVisible object, every frame (the 0x686a66 crash, re/crash_686a66.md)'
                 % (f['path'], *f['at'], *f['out'], f['cell'][0], 'a record, but only by the truncation toward zero / the low byte - not relied on'
                    if f['cell'][1] else 'no record (0xff)'))
    if fts and space is None:
        fail('%d FakeTarget(s) and %s: it is not known that they can register' % (len(fts), space_words(space)))
    dj = os.path.join(B.folder, 'dyn.json')
    if os.path.isfile(dj):
        was = json.load(open(dj)).get('big_before')
        if was and dict(was) != dict(facts['big']):
            fail('a large block changed its size: %s -> %s' % (was, dict(facts['big'])))
    out[:] = list(dict.fromkeys(out))                   # (a finding on a step two branch sets share is said once)
    out.sort(key=lambda x: x[0] != 'FAIL')
    for sev, text in out:
        log('%-4s %s' % (sev, text))
    log('cover boxes in play: %d (%d high, %d low, %d car); every place a Defend step names: %s places, median %s from the nearest box, %s %% within '
        '500, %s %% within 250 (stock bots: 165..291, 61..100 %%, 31..94 %%); the hold places alone: %s, median %s, %s %% within 250'
        % (len(covers), facts['covers']['high'], facts['covers']['low'], facts['covers']['car'], len(d_all), med(d_all), share(d_all, 500.0),
           share(d_all, 250.0), len(d_hold), med(d_hold), share(d_hold, 250.0)))
    log('FakeTargets: %d, outside the vision space: %d; %s' % (len(fts), sum(1 for f in fts if f['out']), space_words(space)))
    for f in fts:
        if f['cell']:
            log('  FakeTarget %s at (%d, %d, %d): %s; kl2\'s arithmetic: cell %s (%s)' % (f['path'].split(BS)[0], *f['at'],
                'OUTSIDE by (%d, %d, %d)' % f['out'] if f['out'] else 'inside', f['cell'][0], 'a record' if f['cell'][1] else 'no record'))
    for sq, r in rows.items():
        log('  %s: on the build\'s way %d Defend steps (%d sprint), %d holds (%d by RandomTrigger, %d places to choose from), %g s of timers, loot waits %s s; '
            'forks of the way: %d (%d with 3 ways, %d with 2), every way checked'
            % (sq, r['defend_steps'], r['sprint'], r['holds'], r['random'], r['alternatives'], r['timers'], r['loot_seconds'],
               r['forks'], sum(n >= 3 for n in r['fork_ways']), sum(n == 2 for n in r['fork_ways'])))
    facts['forks'] = {'forks': sum(r['forks'] for r in rows.values()), 'ways': sum(sum(r['fork_ways']) for r in rows.values())}
    log('RESULT (kl_fa_bots_dyn): %s (%d FAIL, %d NOTE)' % ('PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL',
                                                         sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out)))
    return out, facts


# ------------------------------------------------------------------ what the step changed
def diff(src, dst, log=print):
    """What differs between the bots build and the result -> list of UNEXPECTED differences (must be empty).
    Expected: inside the squad groups the old route steps gone and new ones there; the first-step list of
    Timer_start_bots; field values of nodes that stay (a wait's NEXT and seconds, ZSquadScript 0, ZSoldier 4 / 16 /
    17); the squad's groups in the root's group tree; slot ids that name the same entities; .oct record offsets in
    the .prm's model roots."""
    A, Bn = F.Built(src), F.Built(dst)
    bad = []
    sa, sb = A.sc, Bn.sc
    squad = lambda sc: {t for t in sc.tops() if sc.names[t].startswith(F.SQUAD)}
    ta, tb = squad(sa), squad(sb)
    if [sa.names[t] for t in sa.tops()] != [sb.names[t] for t in sb.tops()]:
        bad.append('the top-level subtrees are not the same list')
    fa, fb = J.fingerprints(sa), J.fingerprints(sb)
    differ = [sa.names[t] for t, u in zip(sa.tops(), sb.tops()) if fa[t] != fb[u]]
    # a subtree outside the squad may differ in ONE way: the FakeTarget controllers that fail the rule ON THE SOURCE
    # are gone - all of that subtree's, and nothing else of it (the subtree's fingerprint: names, classes,
    # properties, controllers, tree). Which those are is worked out here from the source build; the new build's
    # dyn.json is only held against it (it was believed in the first form: re/crash_686a66_review.md D3).
    hits, cut = fake_expected(A)
    fc = J.fingerprints(cut)
    dj = os.path.join(Bn.folder, 'dyn.json')
    dyn = json.load(open(dj)) if os.path.isfile(dj) else {}
    said = [x['path'] for x in (dyn.get('fake_targets_removed') or [])]
    asked = (dyn.get('plan') or {}).get('options', {}).get('fake', True)
    out, fake_seen = [], []
    for t, u in zip(sa.tops(), sb.tops()):
        if fa[t] == fb[u] or sa.names[t].startswith(F.SQUAD):
            continue
        if fc[t] == fb[u]:
            fake_seen += [p for p, k in hits if sa.top[k] == t]
        else:
            out.append(sa.names[t])
    if out:
        bad.append('.prp: top-level subtrees outside the squad differ in more than the FakeTarget controllers that fail the rule on the source: %s' % out[:5])
    if sorted(fake_seen) != sorted(said):
        bad.append('.prp: dyn.json names %d FakeTarget(s) taken off (%s), the tree lost %d (%s)'
                   % (len(said), ', '.join(p.split(BS)[0] for p in said) or '-', len(fake_seen), ', '.join(p.split(BS)[0] for p in fake_seen) or '-'))
    if asked and sorted(fake_seen) != sorted(p for p, _k in hits):
        bad.append('.prp: %d FakeTarget(s) fail the rule on the source, %d were taken off' % (len(hits), len(fake_seen)))
    if not asked and fake_seen:
        bad.append('.prp: built with --keep-fake-targets and %d FakeTarget controller(s) are gone' % len(fake_seen))
    if J.text(sa, sa.p.settings) != J.text(sb, sb.p.settings):
        bad.append('.prp: the scene property block differs')
    n_sq = sum(1 for n in differ if n.startswith(F.SQUAD))
    log('.prp: %d of %d top-level subtrees equal; changed: %d of the squad (%s ...)%s; scene property block equal'
        % (len(sa.tops()) - len(differ), len(sa.tops()), n_sq, ', '.join(n[len(F.SQUAD):] for n in differ if n.startswith(F.SQUAD))[:60],
           '; %d other(s) differ ONLY in a FakeTarget controller taken off (%s)' % (len(differ) - n_sq - len(out), ', '.join(p.split(BS)[0] for p in fake_seen)) if fake_seen else ''))
    # entities: by path outside the squad everything equal; inside: kept ones equal records
    key = lambda e: (e.name, e.tid, e.flags, e.group, e.model, e.rot, e.trans, e.raw, e.aux, e.ref)
    pa = {sa.path[k]: A.ents[k - 1] for k in range(1, len(sa.nodes))}
    pb = {sb.path[k]: Bn.ents[k - 1] for k in range(1, len(sb.nodes))}
    in_squad = lambda p: BS in str(p) and str(p).split(BS)[1].startswith(F.SQUAD)
    if len(pa) != len(A.ents) or len(pb) != len(Bn.ents):
        log('  (%d + %d entities share a scene path with another: compared in order)' % (len(A.ents) - len(pa), len(Bn.ents) - len(pb)))
    oa = [(sa.path[k], key(A.ents[k - 1])) for k in range(1, len(sa.nodes)) if not in_squad(sa.path[k])]
    ob = [(sb.path[k], key(Bn.ents[k - 1])) for k in range(1, len(sb.nodes)) if not in_squad(sb.path[k])]
    if oa != ob:
        bad.append('.gms: an entity outside the squad differs (record, order or REF id)')
    kept = [p for p in pa if in_squad(p) and p in pb]
    gone = [p for p in pa if in_squad(p) and p not in pb]
    new = [p for p in pb if in_squad(p) and p not in pa]
    moved = [p for p in kept if key(pa[p]) != key(pb[p])]
    renewed = [p for p in moved if BS + 'Pos#' in p or 'DefendBehaviour' in p]
    if len(moved) != len(renewed):
        bad.append('.gms: %d entities of the squad that stay have another record, e.g. %s' % (len(moved) - len(renewed), [p for p in moved if p not in renewed][0]))
    refs_b = [e.ref for e in Bn.ents]
    if len(set(refs_b)) != len(refs_b):
        bad.append('.gms: two entities share a REF id')
    links = lambda X, ix: [(ix[e], [(None if t is None else ix[t], b) for t, b in e.links]) for e in X.ents if e.links]
    ia = {e: sa.path[i + 1] for i, e in enumerate(A.ents)}
    ib = {e: sb.path[i + 1] for i, e in enumerate(Bn.ents)}
    if links(A, ia) != links(Bn, ib):
        bad.append('.gms: the light lists differ')
    if [(a and ia[a], ia[b]) for a, b in A.scene.pairs] != [(a and ib[a], ib[b]) for a, b in Bn.scene.pairs]:
        bad.append('room pairs differ')
    if (A.scene.head, A.scene.tail, A.scene.dyn, A.scene.tags, A.scene.budget, A.scene.fdx, A.scene.nav) != \
            (Bn.scene.head, Bn.scene.tail, Bn.scene.dyn, Bn.scene.tags, Bn.scene.budget, Bn.scene.fdx, Bn.scene.nav):
        bad.append('.buf head / tail, dynamic list, tags, heap budget, FDX or the navigation mesh differ')
    log('.gms / .buf: %d entities outside the squad as they were (record, order, REF id); in the squad %d stay (%d of them steps that were made anew '
        'under an old name), %d gone, %d new; REF slots %d -> %d; head, surface table, dynamic list, heap budget, navigation mesh equal'
        % (len(oa), len(kept), len(renewed), len(gone), len(new), A.scene.ref_slots, Bn.scene.ref_slots))
    # .prp inside the squad: which kept nodes changed, and in what
    ka = {sa.path[k]: k for k in range(1, len(sa.nodes))}
    kb = {sb.path[k]: k for k in range(1, len(sb.nodes))}
    allowed = {'TriggerDelay2': {4}, 'TriggerLootDepleted': {1, 4}, 'TriggerActorsDead': {2}, 'SquadModifierBehaviour': {26},
               'ZSquadScript': {0}, 'ZSoldier': {4, 16, 17}, 'TriggerCounter': {4}}       # TriggerCounter: the room-first gate
    changed = collections.Counter()
    for p in kept:
        if p in renewed:
            continue
        a, b = ka[p], kb[p]
        if kl_fa.node_values(sa, a) != kl_fa.node_values(sb, b):
            bad.append('.prp: %s: its own properties differ' % p)
        ca = [(sa.p.key(nm), [kl_fa.value(sa, u) for u in F.units(body[1:-1])]) for nm, body in sa.nodes[a]['ctrls']]
        cb = [(sb.p.key(nm), [kl_fa.value(sb, u) for u in F.units(body[1:-1])]) for nm, body in sb.nodes[b]['ctrls']]
        if [c[0] for c in ca] != [c[0] for c in cb]:
            bad.append('.prp: %s: other controllers' % p); continue
        for (cn, va), (_cn, vb) in zip(ca, cb):
            d = {i for i, (x, y) in enumerate(zip(va, vb)) if x != y}
            if d - allowed.get(cn, set()):
                bad.append('.prp: %s: %s differs in field(s) %s' % (p, cn, sorted(d - allowed.get(cn, set()))))
            for i in d:
                changed['%s[%d]' % (cn, i)] += 1
    log('.prp inside the squad: fields changed on nodes that stay: %s' % (dict(changed) or 'none'))
    # .oct / .rmi / .rmc by entity path
    def trees(L, ix):
        by = {s + 2: ix[e] for e, s in L.scene.slots().items()}
        by[1] = '<root>'
        o = O.Oct.parse(L['.oct'])
        sets = [[None if t is None else (t.origin, t.scale, sorted((str(by.get(it[0], 'gone')), t.world(it[1:4]), t.world(it[4:7])) for it in t.items)) for t in room] for room in o.rooms]
        idx = [[(b.raw[:0x4c], by.get(b.room, 'gone'), by.get(b.second, 'gone') if b.second else 0) for b in O.RoomIndex.parse(L[e]).boxes] for e in ('.rmi', '.rmc')]
        return o, sets, idx
    oa_, sa_, xa = trees(A, ia)
    ob_, sb_, xb = trees(Bn, ib)
    lost = more = 0
    for r, (ra, rb) in enumerate(zip(sa_, sb_)):
        for t, (x, y) in enumerate(zip(ra, rb)):
            if x == y:
                continue
            if (r, t) == (0, 3) and x and y:
                na = collections.Counter(i[0] for i in x[2] if not in_squad(i[0]) if i[0] != '<root>')
                nb = collections.Counter(i[0] for i in y[2] if not in_squad(i[0]) if i[0] != '<root>')
                if na != nb:
                    bad.append('.oct: the root\'s group tree lost or gained an entity outside the squad')
                lost = sum(1 for i in x[2] if i[0] != '<root>' and in_squad(i[0]))
                more = sum(1 for i in y[2] if i[0] != '<root>' and in_squad(i[0]))
            else:
                bad.append('.oct: room set %d tree %d differs' % (r, t))
    if len(sa_) != len(sb_) or xa != xb:
        bad.append('.oct room sets or .rmi / .rmc boxes differ by entity')
    if [r.pack() for r in oa_.records] != [r.pack() for r in ob_.records] or oa_.tail != ob_.tail:
        bad.append('.oct collision records or tail differ')
    log('.oct: %d room sets, every item outside the squad names the entity it named; the root\'s group tree listed %d squad groups, now %d; %d '
        'collision records and the tail equal; .rmi / .rmc: %d + %d boxes name the rooms they named' % (len(sa_), lost, more, len(oa_.records), len(xa[0]), len(xa[1])))
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
    seven = {A.ext[e] for e in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm')}
    rest = [n for n in A.order if n not in seven and A.files[n] != Bn.files.get(n)]         # every member by name, the menu XML too
    if rest or A.order != Bn.order:
        bad.append('other members differ: %s' % rest)
    skip = ('audit.', 'dyn.', 'steps.json', 'graft.txt', F.SLOT + '_Main.zip')
    side = [f for f in os.listdir(A.folder) if os.path.isfile(os.path.join(A.folder, f)) and not f.startswith(skip)]
    sdiff = [f for f in side if not os.path.isfile(os.path.join(Bn.folder, f)) or open(os.path.join(A.folder, f), 'rb').read() != open(os.path.join(Bn.folder, f), 'rb').read()]
    if sdiff:
        bad.append('files beside the archive differ: %s' % sdiff)
    log('the other %d members byte for byte; %d files beside the archive byte for byte (%s; steps.json and graft.txt get a line of this step)'
        % (len(A.order) - 7, len(side), ', '.join(f for f in side if f.endswith('.ini')) or 'no .ini'))
    for x in bad:
        log('UNEXPECTED: ' + x)
    log('RESULT: %s' % (('only the squad\'s steps were made anew' + (' and %d FakeTarget controller(s) outside the vision space taken off' % len(fake_seen) if fake_seen else ''))
                        if not bad else '%d unexpected differences' % len(bad)))
    return bad


# ------------------------------------------------------------------ commands
def describe(P, log=print):
    """The plan in words: per bot, step by step."""
    for N, b in P['bots'].items():
        pers = b['personality']
        log('Squad#0%s  %s' % (N, b['role'].upper()))
        for ci, items in enumerate(b['chains']):
            if len(b['chains']) > 1:
                log('  chain %d (%s)' % (ci + 1, 'from Timer_start_bots' if ci == 0 else 'started from outside the squad: the jump'))

            def say(items, pad):
                for it in items:
                    if it['kind'] == 'fork':
                        log('%s%-44s THE WAY FORKS, drawn per round: %d ways to (%d, %d, %d)' % (pad, it['name'], len(it['branches']), *it['to']))
                        for n_b, br in enumerate(it['branches']):
                            log('%s  way %d of %d, weight %d: %s, %d m%s' % (pad, n_b + 1, len(it['branches']), br['weight'],
                                {'build': 'the build\'s way', 'real': 'ANOTHER CORRIDOR of the mesh', 'left': 'the build\'s way moved LEFT', 'right': 'the build\'s way moved RIGHT'}[br['kind']],
                                br['length'] / 100, '' if br['items'] else ' (no step of its own: straight on)'))
                            say(br['items'], pad + '      ')
                    elif it['kind'] == 'rout':
                        log('%s%-44s walk %s%s' % (pad, it['name'], ' -> '.join('(%d, %d, %d)' % tuple(p) for p in it['places']), '  SPRINT' if it['sprint'] else ''))
                        fan = it.get('fan')
                        if fan:
                            log('%s%-44s   + takes cover at %s' % (pad, fan.get('name', ''), ' OR '.join(
                                '(%d, %d, %d) %d from %s [%s]' % (*a['place'], a['from_cover'], a['cover'].split(BS)[-1], a['cover_kind']) for a in fan['alts'])))
                    elif it['kind'] == 'hold':
                        log('%s%-44s holds at (%d, %d, %d), %d from %s [%s]' % (pad, it['name'], *it['place'], it['from_cover'], it['cover'].split(BS)[-1], it['cover_kind']))
                    elif it['kind'] == 'timer':
                        log('%s%-44s %g s' % (pad, it['name'], it['seconds']))
                    elif it['kind'] == 'mod':
                        log('%s%-44s %s' % (pad, it['name'], ' '.join(it['fields'].values())))
                    else:
                        log('%s%-44s the build\'s own %s%s' % (pad, it['name'], it['what'], '' if it.get('loot_seconds') is None else
                                                               ': until the loot is gone or %d s (the build: %d)' % (it['loot_seconds'], it['was'])))
            say(items, '    ')


def summary(P, log=print):
    """The plan as one line a bot per chain (markdown): what it does, in order."""
    short = lambda c: c.split(BS)[-1].split('!')[-1]
    for N, b in P['bots'].items():
        pers = b['personality']
        def words(items):
            out, i = [], 0
            while i < len(items):
                it = items[i]
                k = it['kind']
                if k == 'fork':
                    kinds = {'build': 'the build\'s way', 'real': 'another corridor', 'left': 'to the left', 'right': 'to the right'}
                    out.append('FORK (weights %s): %s' % (' / '.join(str(br['weight']) for br in it['branches']), ' OR '.join(
                        '{%s: %s}' % (kinds[br['kind']], '; '.join(words(br['items'])) or 'straight on') for br in it['branches'])))
                elif k == 'timer':
                    out.append('wait %g s' % it['seconds'])
                elif k == 'mod':
                    out.append('[%s]' % ' '.join(v.replace('eDM_', '').replace('eLM_', '').replace('eVIM_Factor_2_0', 'vision x2').replace('eCSS_Enabled', 'sixth sense').lower() for v in it['fields'].values()))
                elif k == 'rout':
                    t = 'walk %d place%s' % (len(it['places']), '' if len(it['places']) == 1 else 's')
                    if it['sprint']:
                        t = 'SPRINT %d place%s' % (len(it['places']), '' if len(it['places']) == 1 else 's')
                    fan = it.get('fan')
                    if fan:
                        nx = items[i + 1] if i + 1 < len(items) else None
                        sec = nx['seconds'] if nx and nx['kind'] == 'timer' else None
                        t += ' -> cover %s%s' % (' / '.join('%s' % short(a['cover']) for a in fan['alts']) if len(fan['alts']) > 1 else short(fan['alts'][0]['cover']),
                                               ' %g s' % sec if sec is not None else ' during the rally')
                        if len(fan['alts']) > 1:
                            t = t.replace('-> cover', '-> cover, one of')
                        if sec is not None:
                            i += 1
                    out.append(t)
                elif k == 'hold':
                    nx = items[i + 1] if i + 1 < len(items) else None
                    out[-1] += ' -> cover %s %g s' % (short(it['cover']), nx['seconds'] if nx and nx['kind'] == 'timer' else 0)
                    if nx and nx['kind'] == 'timer':
                        i += 1
                elif it['what'] == 'loot':
                    out.append('LOOT until gone or %d s' % it['loot_seconds'])
                elif it['what'] == 'timer':
                    out.append('the build\'s %s' % ('cases timer (glass + open)' if it['also'] else 'rally timer'))
                elif it['what'] == 'mod':
                    out.append('[leashed tight: the end]')
                else:
                    out.append('the build\'s %s' % it['what'])
                i += 1
            return out

        for ci, items in enumerate(b['chains']):
            log('- **Squad#0%s, %s**%s: %s' % (N, b['role'], '' if len(b['chains']) == 1 else ' (%s)' % ('tower' if ci == 0 else 'street, from the jump'), '; '.join(words(items))))


def build(src, dst, opt=None, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    say('kl_fa_bots_dyn build %s -> %s' % (src, dst))
    ctx = Ctx(src, say)
    for h, f, t in ctx.outside:
        say('named from outside the squad: %s (%s) -> %s' % (h[5:], f, t[5:]))
    P = plan(ctx, opt, say)
    gap = float(P['options'].get('fork_gap') or 0.0)    # said aloud: another module (kl_fa_cover) builds through here with the default
    say('fork gap: %s' % ('a TriggerDelay2 of %g s before every RandomTrigger (the form of commit 76bfdcd)' % gap if gap else
                          'NONE - every fork is the form of the builds on the owner\'s tab. FORK_GAP is 0 since 2026-10-11 (the 0x686a66 crash was a '
                          'FakeTarget, re/crash_686a66.md); commit 76bfdcd built 0.1 s by default: \'--fork-gap 0.1\' / opt fork_gap makes that form'))
    rep = apply(ctx, P, dst, say)
    rep['plan'] = P
    with open(os.path.join(dst, 'dyn.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out, facts = check(dst, say)
    bad = diff(src, dst, say)
    out = out + [('FAIL', 'diff: ' + x) for x in bad]
    rep.update(check=[list(x) for x in out], facts=facts, diff=bad)
    say('')
    describe(P, say)
    with open(os.path.join(dst, 'dyn.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    try:
        draw(dst, os.path.join(dst, 'dyn_map.png'), log=say)
    except Exception as x:                              # the picture is a convenience: say it, go on
        say('no picture: %s: %s' % (type(x).__name__, x))
    with open(os.path.join(dst, 'dyn.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def covers_report(folder, log=print):
    ctx = Ctx(folder, lambda *a: None)
    cv = [c for c in ctx.covers if not c['hidden']]
    log('%s: %d cover boxes (%d high, %d low, %d car), %d hidden' % (folder, len(cv), sum(c['kind'] == 'high' for c in cv),
        sum(c['kind'] == 'low' for c in cv), sum(c['kind'] == 'car' for c in cv), len(ctx.covers) - len(cv)))
    ds = []
    for N, q in ctx.squads.items():
        for c in q['chains']:
            for e in c['elems']:
                if e['kind'] == 'defend':
                    ds += [min(math.dist(p, x['at']) for x in cv) for p in e['pts']] if cv else []
    if ds:
        ds.sort()
        log('  the squad\'s %d route places: median %d from the nearest box, %d %% within 500, %d %% within 250'
            % (len(ds), ds[len(ds) // 2], 100 * sum(d <= 500 for d in ds) / len(ds), 100 * sum(d <= 250 for d in ds) / len(ds)))
    with_spots = sum(1 for i in range(len(ctx.covers)) if not ctx.covers[i]['hidden'] and ctx.spots(i))
    log('  boxes with at least one place a bot can hold at (mesh %d..%d from the box, %d clear of the mesh\'s edge): %d' % (*RING, HOLD_CLEAR, with_spots))


# ------------------------------------------------------------------ a picture (to LOOK at the routes offline)
COLOURS = {2: (230, 60, 60), 3: (240, 150, 40), 4: (235, 215, 50), 5: (70, 200, 80), 6: (60, 190, 220), 7: (90, 110, 240), 8: (210, 90, 220)}


def _png(path, w, h, rgb):
    import zlib
    raw = b''.join(b'\0' + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def draw(folder, out, size=1800, log=print):
    """A top view of the squads of a build (dynamic or not) -> one PNG per navigation part the routes use:
    grey = the mesh's edges without a neighbour (walls, drops), white squares = cover boxes (hollow: created hidden),
    one colour a bot: thin line = its walked places in order (dim: the build's way; BRIGHT: the other ways of a
    fork, where a RandomTrigger draws per round), dot = a place, ring = a hold place (a line joins it to the route
    place it follows), big dot = where the bot stands at the start. Squad#02 red, 03 orange, 04 yellow,
    05 green, 06 cyan, 07 blue, 08 violet."""
    B = F.Built(folder)
    sc, nav = B.sc, F.Nav(B.scene.nav)
    G = graph(B)
    covers = cover_boxes(B)
    part_of = lambda p: (lambda h: h and nav.part[h[0]])(nav.at(p[0], p[1], p[2], dy=40.0))
    routes = collections.defaultdict(list)             # part -> [(N, [walked places], [(route place, hold place)], start)]
    for sq, g in G.items():
        N = int(sc.names[sc.parent[g['actor']]][18])
        for ci, vi, chain in [(ci, vi, ch) for ci, cset in enumerate(g['sets']) for vi, ch in enumerate(cset)]:
            walked, holds, last = [], [], None
            for it in chain:
                if it['ctrl'] != 'DefendBehaviourRout':
                    continue
                pts = [B.at(j) for j in it['places']]
                if it['v'][0] and not it['v'][1] and 'pos_cover' in it['name']:
                    holds.append((last, pts[0]))
                    continue                            # (a hold is drawn as a ring beside the way, not as part of it)
                walked += pts
                last = pts[-1]
                for kind, j, alts in it['side']:
                    if kind in ('random', 'one'):
                        for a in alts:
                            va = g['ctrl'][a][1]
                            holds += [(pts[-1], B.at(x)) for x in sc.resolve(va[0])]
            if walked:
                routes[part_of(walked[0])].append((N, walked, holds, B.at(g['actor']) if ci == 0 else None, vi))
    made = []
    for n_part, (part, rs) in enumerate(sorted(routes.items(), key=lambda kv: str(kv[0]))):
        xs = [p[0] for _n, w, h, st, _v in rs for p in w + [x[1] for x in h] + ([st] if st else [])]
        zs = [p[2] for _n, w, h, st, _v in rs for p in w + [x[1] for x in h] + ([st] if st else [])]
        ys = [p[1] for _n, w, h, st, _v in rs for p in w]
        x0, x1, z0, z1 = min(xs) - 900, max(xs) + 900, min(zs) - 900, max(zs) + 900
        k = size / max(x1 - x0, z1 - z0)
        w, h = int((x1 - x0) * k) + 1, int((z1 - z0) * k) + 1
        img = bytearray([18, 18, 22] * (w * h))

        def px(x, y, c):
            if 0 <= x < w and 0 <= y < h:
                o = (y * w + x) * 3
                img[o:o + 3] = bytes(c)

        def to(p):
            return int((p[0] - x0) * k), int((z1 - p[2]) * k)

        def line(a, b, c):
            (ax, ay), (bx, by) = to(a), to(b)
            n = max(abs(bx - ax), abs(by - ay), 1)
            if n > 4 * size:
                return
            for i in range(n + 1):
                px(ax + (bx - ax) * i // n, ay + (by - ay) * i // n, c)

        def dot(p, r, c, hollow=False):
            cx, cy = to(p)
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    d = dx * dx + dy * dy
                    if d <= r * r and (not hollow or d >= (r - 1) * (r - 1)):
                        px(cx + dx, cy + dy, c)

        lo, hi = min(ys) - 500, max(ys) + 500
        for i, vs in enumerate(nav.pv):
            if not nav.ok[i] or nav.part[i] != part:
                continue
            for e, j in enumerate(nav.en[i]):
                a, b = vs[e], vs[(e + 1) % len(vs)]
                if lo <= a[1] <= hi and x0 <= a[0] <= x1 and z0 <= a[2] <= z1:
                    line(a, b, (95, 95, 105) if j < 0 else (38, 38, 46))
        for c in covers:
            if lo <= c['at'][1] <= hi:
                cx, cy = to(c['at'])
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        if not c['hidden'] or abs(dx) == 3 or abs(dy) == 3:
                            px(cx + dx, cy + dy, (250, 250, 250) if c['kind'] != 'low' else (170, 170, 170))
                if '_kl_' in sc.names[c['node']].lower():       # a box kl_fa_cover.py added: a magenta frame round it
                    for dx in range(-7, 8):
                        for dy in range(-7, 8):
                            if max(abs(dx), abs(dy)) >= 6:
                                px(cx + dx, cy + dy, (255, 0, 220))
        # the further branch sets first, in the bot's full colour (the OTHER ways of its forks); then set 0 = the
        # build's way at every fork, dimmer, over them: where a bright line leaves the dim one the way forks
        for N, walked, holds, st, vi in sorted(rs, key=lambda r: -r[4]):
            c = COLOURS.get(N, (255, 255, 255))
            dim = tuple(v * 2 // 3 for v in c) if vi == 0 else tuple(min(255, v + 25) for v in c)
            seq = ([st] if st else []) + walked
            for a, b in zip(seq, seq[1:]):
                line(a, b, dim)
            for e, q in holds:
                if e is not None:
                    line(e, q, c)
                dot(q, 6, c, hollow=True)
            for p_ in walked:
                dot(p_, 2, c)
            if st:
                dot(st, 5, c)
        name = out if len(routes) == 1 else '%s_%d%s' % (os.path.splitext(out)[0], n_part + 1, os.path.splitext(out)[1] or '.png')
        _png(name, w, h, img)
        made.append(name)
        log('%s: %d x %d, mesh part of %d polygons, x %d..%d, z %d..%d (north = +z up), %d routes' % (name, w, h, nav.part_size[part], x0, x1, z0, z1, len(rs)))
    return made


OWNER = (('y_loot2', 'M01'), ('y_loot2', 'M02'), ('y_loot2', 'M03'), ('y_loot2', 'M06'), ('rt_full4', 'retomoto_full'))
# 2026-10-10 night, the random routes: the five bots builds that were on the owner's tab -> z_route\<map>
ROUTE = (('z_gate', 'M01'), ('z_final', 'M02'), ('z_final', 'M03'), ('z_final', 'M06'), ('rt_full6', 'retomoto_full'))


def options(a):
    opt = {}
    for flag, key, val in (('--no-random', 'random', False), ('--no-vision', 'vision', False), ('--no-rusher', 'rusher', False),
                           ('--no-stagger', 'stagger', False), ('--no-tree', 'tree', False), ('--no-detour', 'detour', False),
                           ('--no-routes', 'routes', False), ('--keep-fake-targets', 'fake', False)):
        if flag in a:
            a.remove(flag); opt[key] = val
    for flag, key in (('--sixth', 'sixth'), ('--gap', 'gap'), ('--ways', 'ways'), ('--fork-gap', 'fork_gap')):
        if flag in a:
            i = a.index(flag)
            opt[key] = float(a[i + 1]); del a[i:i + 2]
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'plan':
        ctx = Ctx(a[1])
        describe(plan(ctx, opt))
    elif len(a) == 2 and a[0] == 'check':
        out, _f = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2]) else 0)
    elif len(a) >= 2 and a[0] == 'fake-test':
        sys.exit(0 if fake_test(a[1:]) else 1)
    elif len(a) == 3 and a[0] == 'fake-fix':
        out, _rep = fake_fix(a[1], a[2])
        sys.exit(1 if out else 0)
    elif len(a) >= 3 and a[0] == 'grid':
        sys.exit(0 if grid_compare(a[1], ' '.join(a[2:])) else 1)
    elif len(a) == 2 and a[0] == 'covers':
        covers_report(a[1])
    elif len(a) == 3 and a[0] == 'map':
        draw(a[1], a[2])
    elif len(a) == 2 and a[0] == 'summary':
        summary(json.load(open(os.path.join(a[1], 'dyn.json')), object_pairs_hook=collections.OrderedDict)['plan'])
    elif len(a) >= 2 and a[0] in ('owner', 'routes'):
        res = {}
        for sub, d in (OWNER if a[0] == 'owner' else ROUTE):
            if a[2:] and d not in a[2:] and not (d == 'retomoto_full' and 'retomoto' in a[2:]):
                continue
            name = 'retomoto' if d == 'retomoto_full' and a[0] == 'owner' else d
            print('==== %s' % name)
            out, _rep = build(os.path.join(a[1], sub, d), os.path.join(a[1], 'z_dyn' if a[0] == 'owner' else 'z_route', name), opt)
            res[name] = not any(s == 'FAIL' for s, _t in out)
        for k, v in res.items():
            print('%s: %s' % (k, 'PASS' if v else 'FAIL'))
        sys.exit(0 if res and all(res.values()) else 1)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
