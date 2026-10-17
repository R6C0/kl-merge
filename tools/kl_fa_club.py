#!/usr/bin/env python3
"""
The Fragile Alliance layer of LAST CALL: the Tokyo night club (Dead Men M05_A, chapter 5 'The Mizuki', alone,
under Dog Days F07). Authored from stock objects, offline, on the pattern of kl_fa_bank.py (The Vault), whose
generic parts are IMPORTED from there (the doors' frame arithmetic, the text and reading helpers, reverify);
none of its tables. The study: re/campaign_fa_club.md (its section 8 weighs more than the first text),
re/campaign_fa.md 4.2 and G1.3 / G1.8; the build stage by stage, every check with its output and what only a
live run can settle: re/club_campaign.md. Nothing here installs anything or starts the game.

THE ENEMIES, THE BEAT (stage L2) AND THE ESCAPE (stage L3: F07's van on ROAD) ARE IN. '--no-ai' builds the round
without enemies of stage L1.

VERSION 2 (2026-10-12, 'Last Call v2', after the owner's round C10; NOT RUN IN THE GAME; the default, '--v1' is the round of c_club5 and gives its archives byte for byte): the crew
STARTS ON THE PAVEMENT in front of the entrance (START_V2: two rows of four east of the lane mouth, the TRAITOR row west of it), runs IN through the queue lane, the hall, the stairs, both dance floors
and the walkway to Yoko's office (the loot is where it was), and fights OUT again through the five gated rooms to F07's van on the slab. Nothing is sealed (SEAL_OPEN: the seal pieces are out at build
time). The first criminal through the inner office door is the ALARM: 25 s later (ALARM_DELAY; or 200 s after the round start whatever a bot counts as, ALARM_BACKSTOP) the hunters and F07's police
come in, the van is shown (the 'van bug' of C10: its show hung on the seal's clock, which a sprinting crew beat) and the exit line is spoken. The exit box is the slab's south-west corner round the
boarding place (EXIT_V2). THE WAY IN HAS NO GATE (10 men of 'load' squads are awake along it: inleg_table, 6 guns at worst; the squads with a start child sleep until their out-gate). NOT BUILT: the
crowd (campaign civilians and clones), the roof stage and the helicopter (re/club_campaign.md 'Version 2'). '--exit van-slab' is the only exit this file builds.

THE ROOM GATES (2026-10-12, after live runs C3 / C4; NOT RUN IN THE GAME): the seven AI heisters hold at distinct cover places in front of each
of five rooms of the way out (walkway, dance floor 2 east / west, dance floor 1 north-west, the stairs' foot) and go on through a
TriggerActorsDead that names the room's men (dead, or the game's own 30 s) - Retomoto's gates (kl_fa_bots_rt.gates_plan, imported) with this
level's table; six men moved off the way (CLEAR_MEN); the dynamic step adds no hold behind them (`dyn` command). `--no-gates` / `--legacy` /
`--no-ai` leave them out. See ROOMS, bots_gates, rooms_check and re/club_campaign.md 'Gates, after runs C3-C4' and 'Gates, second fix'
(no fork between the first gate and the seal hold; no hold within 300 of a man of an earlier room; a gate names only the men a hold can see).

THE PRESSURE FIX (2026-10-12, after live run C5; NOT RUN IN THE GAME): C5 lost the seven at the walkway gate where 5 .. 8 of the 40 awake men had a clear exact ray to them. The yardstick is Withdrawal's (at most 3 guns on a hold, 4 on
a walk, counted by the exact ray over the men of the squads that are in the world): nine squads sleep until the gate before their room opens (WAKE_AT, the gates' TriggerActorsDead name their squad modifiers; command `wake` puts the names
back after the dynamic step), the holds are picked for the fewest guns (rt_for_club.spots), 13 men stand elsewhere in their rooms (PRESSURE_MEN), and the check `hold-guns` (rooms_check) counts. Four rooms stay over the yardstick:
PRESSURE_KNOWN. `--no-pressure` / `--no-gates` / `--legacy` / `--no-ai` leave it out. re/club_campaign.md 'Pressure, after run C5'.

THE WAKE FIX (2026-10-12, after live run C8; NOT RUN IN THE GAME): the nine staged squads were woken by the bots' gates alone. READ in kl2.exe that a named SquadModifierBehaviour shows a parked squad (0x4ebed0 -> 0x833830 -> 0x791090 -> 0x7f6750 -> 0x7c0d50);
each squad is now ALSO named by a criminals-only TriggerBox on the hold area of the room whose gate names it and by a backstop TriggerDelay2 (six free F07 objects: WAKE_NEW; WAKE_BOX holds the numbers). check() / rooms_check prove per squad
a gate, a box and a backstop, and that no man a box wakes has an exact-ray line to a mesh point of it. `--no-wake-boxes` leaves the boxes out. re/club_campaign.md 'Wake, after run C8'.

    python kl_fa_club.py test <out> [--keep] [--v1] [--exit van-slab] [options]
                                                          (--v1: the round of c_club5; V2 is the default)
                                                          build F07 + M05_A with the layer into <out> (build():
                                                          a bare graft first, for the van's plan, then the level
                                                          inside kl_map_escape.van_layer), finish() on the written
                                                          level, check(); exit 1 if a problem is left that is not
                                                          in KNOWN. Beside the archive: van.json
    python kl_fa_club.py hold-guns <built folder> ...     the guns bearing on every gate's seven holds and on the walk to them, the wake table read off the scene
    python kl_fa_club.py wake <built folder>              (chain step after the dynamic step) the squads each gate wakes back into its TriggerActorsDead
    python kl_fa_club.py van-check <built folder>         kl_map_escape.van_check on a built folder WITH THE DRAWN
                                                          PAVEMENT AS THE ROAD (Pavement: the plain 'kl_map_escape.py
                                                          van-check' faults every key of the drive that has no
                                                          collision floor under it - by design of this map)
    python kl_fa_club.py finish <built folder>            what needs the WRITTEN level, on a folder build() made:
                                                          the load weight, the briefcases, the level's own texts
    python kl_fa_club.py check <built folder>             every check of this layer on a built folder
    python kl_fa_club.py inventory <built folder>         the layer with world places read back from the level
    python kl_fa_club.py reverify <folder>                kl_graft.verify's cross-reference tests on the level as
                                                          WRITTEN (kl_fa_bank.reverify; check does it too)
    options of 'test' (one flag each for the live runs):
      --doors-animate   the four leaves of the two office doors stay where the level has them, store LAST frame
                        DOOR_LAST and get 'Activate' DOORS_AT seconds after the round-start event (default: they
                        are OPEN AT BUILD TIME - sunk, their collision cut)
      --seal-open       the entrance seal is taken out at build time too (a first load in which nothing can stop
                        anybody; the beat's clock then switches nothing)
      --seal-plane      the seal's second piece 'Plane01' stays as well and is named by the beat's DeactivateGeom
                        beside 'HeroColi' (default: 'Plane01' is out at build time - SEAL)
      --seal S          seconds from the round-start event to the seal's end (default SEAL_AT)
      --light-show      the seven PositionLightControl of the club's light show keep their controller
      --beat-anim       the two 'Beat_M05' objects stay ZIKLNKOBJ with their StartAnim (the beat track the light
                        show reads; default: retyped to plain objects without a model, StartAnim off)
      --fan-damage      the five roof fans keep their ShotActivateDamage (default: taken off - FAN_DAMAGE)
      --loot-bags       the loot keeps F07's money bags (finish() leaves the models alone)
      --no-ai           no squad of the campaign stays and none of F07's police: a round without enemies, for a
                        first live run (the seal then opens by its clock alone)
      --squads-awake    every campaign squad is in the world from the load (ZSquadScript field 3 = 1) instead of
                        waiting for its stage: the fall-back if a squad that has no behaviour rout is not started
                        by naming its SquadModifierBehaviour (STAGED: stock story levels do it, no build of ours has)
      --no-police       none of F07's police arrive when the seal opens (the club's own guards only)
      --police-strip    the arriving police come into the world out of sight on the pavement's mesh strip beside
                        the slab, where there is NO collision floor (ARRIVE: only if an AI can stand on bare mesh,
                        which no live run has shown; a man who cannot falls into a kill box). Default: ON the slab
                        (ARRIVE_SLAB, at its two ends, two of the ten in sight of the lane when the seal opens)
      --police-slab     (the default; kept so that old command lines still run)
      --office S        seconds from the round-start event to the front office's guards (default OFFICE_AT)
      --dead-men-rows   the guards keep Dead Men's soldier rows (default: stock Fragile Alliance rows by weapon)
      --str FILE        Dead Men's streamed clips are resolved against FILE and FILE.map.json instead of the
                        work folder's merged PC_Def.str (kl_fa_bank.use_stream): for the build against a stream
                        file that holds the club's music (MUSIC_CLIPS; the extension is a later step)
      --legacy          the first delivery's build (the fix after runs C0 - C2 off: the control, sha1 a4d024f3 of the bare archive)
      --no-guards-off   the front office's four guards stay in the front office (GUARDS_OFF, see 'THE FIX AFTER RUNS C0 - C2')
      --no-police-east  the arriving police start at both ends of the slab (POLICE_EAST)
      --no-van-late     the van stands in the world from the load with its target (VAN_LATE)
      --no-reset        round 2 is not put back by the round-start event (RESET)
      --no-voice        the streamed single ADPCM lines stay streamed (VOICE)
      --plan FILE       the van's plan from a file (the van.json beside an earlier build) instead of a new one:
                        saves the bare graft (35 s). Refused when its way points are not ROAD's

THE ROUND (re/campaign_fa.md 4.2)
  START   shut in Yoko's office over dance floor 2 with the money: two rows of four, six briefcases on and
          beside her desk and the sofa table. The ENTERS box lies round the START rows, so the office loot counts.
  OUT     the inner and the outer office door (open from the load: DOORS) -> front office -> the walkway down
          to dance floor 2 -> dance floor 1 (three cases on the long bar) -> the stair landing -> the wardrobe
          (a case on the coat check's counter) -> the entrance hall -> the entrance door (open in the level)
          -> the ticket counter (a case on its shelf) -> the queue lane -> the pavement.
  BEAT    'exit blocked': the street end of the queue lane is sealed from the load by the campaign's own
          invisible collision (SEAL) and opens when both dance-floor squads are wiped out (BEAT_SQUADS: their
          'wiped out' lists -> a counter of two) or SEAL_AT seconds after the round-start event - a clock
          that takes the seal away whatever else happens. Whichever comes first also lets the enemies in,
          once (F07's own 'first of two' gate, GATE): three hunters come down from the lounge over the stairs,
          and ten of F07's police arrive on the pavement from both sides (ARRIVE).
  ENEMIES the club's own security, 40 guards in 17 squads of the campaign (SQUADS), staged: the front office's
          four OFFICE_AT seconds after the round-start event (just after GO), the walkway's when the first
          criminal steps through the inner office door, the dance floors' second run and the upstairs
          squads when he is on the walkway; fifteen bouncers stand where the campaign has them from the load.
  ESCAPE  the exit box and the escape marker lie on the pavement, on the only collision floor outside the
          building (the slab: x -1200..1800, z -3450..-2650, y 30). Bound trios stand outside its three open
          edges and kill boxes under them: beyond the slab the street is drawn and not there (BOUNDS, KILL).
          F07's first key-framed van (ROAD; kl_map_escape's way-point front end) waits 50 m up the pavement to
          the west, comes along the house fronts when a criminal steps onto the slab and stops WEST of the
          lane's mouth, its rear doors at (-637, 30, -3100) on the slab; it leaves east along the pavement.
          It drives ON THE DRAWN PAVEMENT (y 30.0 from x -7200 to 7600: check() measures the models): outside
          the slab there is no collision floor under it, and a key-framed van needs none (Pavement).

HOW (as kl_fa_bank: no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  The nine names of kl_graft.AUTHOR_NAMES: HOST, prepare_host(S), strip(M), KEEP, DROP, layer_names(Jn),
  complete(Jn), wire(Jn), campaign_names(level). On top of them, because the interface has no place for it:
  1. THE BUILD'S OWN ARGUMENTS (build()): the campaign's five level bounds must go (M_DROP: four of them stand
     shown on the route), and the two 'Beat_M05' objects are loaded as plain objects (kl_maps' '--flat', the
     class pair lent to its table for the call). 'kl_maps.py one ... --author kl_fa_club' alone therefore stops
     in prepare_host with a line that says so.
  2. THE DOORS AT BUILD TIME (Doors): kl_fa_bank.Doors with this level's nodes - three functions of kl_escape
     wrapped for the length of ONE build (re/campaign_fa.md G1.1, with its two traps: the club's outer office
     door is the group under which .prp and .gms hold different local places).
  3. finish(folder), on the written level (chunk numbers and the .LOC exist only then): the load weight, the
     briefcase model (kl_fa_loot.case_model, into dead chunk indices), the level's own texts.
  4. THE VAN (as kl_fa_bank): the plan of ROAD needs a BUILT level's collision and must not see the layer's own
     van, so build() makes a bare graft first (<out>/_bare, deleted again) or takes a plan from a file, hands it
     to prepare_host() / wire() (lay_van) and wraps the build in kl_map_escape.van_layer (the van's collision
     placements). NEW HERE: the plan and van_check run inside pavement() - kl_map_escape.Ground with the DRAWN
     pavement as a floor where the collision has none (Pavement; kl_map_escape itself is unchanged).

GUESS = a value that is not copied from a stock object or measured in the levels; ASSUMPTION = fits the
evidence, not proven. Every table entry carries its source. Rotation, box and 'hidden' facts: kl_fa_author's
docstring (the helpers are imported from there: rot9 / look9 / place / setv / ctrl_of / node_of).
"""
import collections, contextlib, math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms, kl_hvk
import kl_prpjoin as J
import kl_fa_author as A                # the small tools only (place, setv ...); none of Retomoto's tables
import kl_fa_bank as BK                 # the generic parts only (Doors' frames, put / values / facing, world_of, set_text,
                                        # read_built, lost_clips, reverify); none of the bank's tables
import kl_map_escape as ESC             # the van: the way-point front end, van_prepare / van_wire / van_layer / van_check

HOST, LEVEL = 'F07', 'M05_A'
HOST_BASE = 'F07'                       # the real systems level; HOST becomes 'R09' (the donor step's pseudo level) for the second step of a heli build
TITLE = 'Last Call'                     # the map's name (for the menu page: kl_expansion's table, a later stage)
R = 'ROOT\\'
IN = 'Locations/M05_A/M05A_Locations.zip\\Locations/M05_A/M05A_LOC_Inside.zip\\'
AUDIO = 'Locations/M05_A/M05A_Audio.zip!STREAMS!Inside!Music!'
HIDDEN = 0x400
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
# problems kl_graft.verify reports that this layer cannot remove: (text looked for, why it stands)
KNOWN = (('stream clips are not in the merged stream file', 'the club\'s two music tracks and five ambience beds (MUSIC_CLIPS, AMBIENCE_CLIPS) have no record in '
          'the built .WHD - they are not in the installed PC_Def.str; the stream file\'s extension for the club is a later step (re/club_campaign.md): those '
          'sounds are silent, nothing else'),)
# ... and in a build without enemies ('--no-ai'), which check() knows by the level having no squad at all
KNOWN_NO_AI = ('no ZSquadScript', 'a round without enemies (NO_AI): the build for a first live run')
NO_AI = False                           # True ('--no-ai'): no squad of the campaign stays (campaign_names), none of F07's police

# ------------------------------------------------------------------ the build's own arguments
# The campaign's five level bounds 'Boundaries!LevelBound*' survive the campaign pre-pass; four of them are shown
# at the load and stand ON the route (wardrobe (200, 175, -251), stairs (399, 165, 218), ...), and what switches
# them is dropped (re/campaign_fa_club.md 1.2, 8.1 item 11). They go with the build's own drop list
M_DROP = ('Boundaries!*',)
# 'Beat_M05' (BEAT): Dead Men ZIKLNKOBJ 0x200027 -> ZSTDOBJ 0x200002 for the build, kl_maps' '--flat' (kl_maps.FLAT
# has no entry for the class: build() lends it this one for the call). Same pool category (1: kl_gms.category)
IK = ('ZIKLNKOBJ', (0x200027, 0x200002))
NO_BUILD = ('kl_fa_club: build with \'kl_fa_club.py test <out>\' or kl_fa_club.build(): the build needs arguments of its own (M_DROP; the Beat_M05 '
            'objects loaded as plain ones) and \'kl_maps.py one ... --author kl_fa_club\' gives it neither')

# ------------------------------------------------------------------ the club (M05_A), measured
# Floors (collision; C:/kl_scratch/club/l1/s/floors.py on a bare graft): Yoko's office 340 and its front office 349,
# the walkway 379 sloping down to dance floor 2 (39), dance floor 1 19, the stair landing 159, the wardrobe 179, the
# entrance hall 100, entrance and queue lane 19..23, the pavement slab 29. All of it is on ONE part of the
# navigation mesh (401 of its 437 polygons; re/campaign_fa_club.md 3.4).
OFFICE = 342.0                          # the mesh's height in the office (the floor is 339..340)
DOOR_IN = (2550.0, 347.0, 3313.0)       # the inner office door's doorway (leaves D1 / D2 in the plane x 2500, z 3167..3488)
LANE_MOUTH = (118.0, 20.0, -2623.0)     # where the queue lane meets the pavement
SLAB = ((-1200.0, 1800.0), (-3450.0, -2650.0), 30.0)    # the pavement's collision floor: x, z, y. MEASURED: mesh AND free floor
                                        # on every point of a 50 grid in it but three lamp bases at z -3300 (scan.py)
# START (re/campaign_fa.md 4.2 item 1): two rows of four in the office, facing the way to the inner door. GUESS: the
# rows (the study's); MEASURED: each point on the mesh and on free floor (check()); all eight in one mesh polygon
START = [(float(x), OFFICE, z) for z in (2420.0, 2560.0) for x in (2700, 2817, 2933, 3050)]
# TRAITOR: east of the desk (its top is x 2600..2800, z 2200..2300: the study's first row stood on it). GUESS
TRAITOR = [(float(x), OFFICE, 2290.0) for x in (2940, 3020, 3100, 3180)]
# police who come back: the pavement EAST of the lane's mouth and clear of it (8 m and more). The lane is sealed
# until the beat: until then they are outside the round, as the campaign's own dead-end has it. Rows at z -2760
# and nearer the wall than z -2850: the van drives along the slab (ROAD: z -3100, a lane 220 wide) and wants 250
# either side of its line free of spawn points. Stage L3 moved the four that stood at x -900..-600 east: the van
# stops WEST of the mouth and its rear doors are at x -637 - a policeman must not come back beside them
# (FED_CLEAR; check()). GUESS: the points
# ---- VERSION 2 (2026-10-12, the owner's 'spawn at the entrance of the club ... you run in and take the money from the office'): the crew
# starts on the pavement slab in front of the entrance, runs IN to Yoko's office and OUT again to the van on the slab. V2 = True is the
# default; '--v1' is the round of c_club5 (the archive of that set is reproduced byte for byte). set_v2() puts the tables below into START,
# TRAITOR, SPAWN and PLACE IN PLACE. START_V1 / TRAITOR_V1 are the office rows (also the mesh-part reference of check()).
V2 = True
START_V1 = list(START)
TRAITOR_V1 = list(TRAITOR)
START_REF = START_V1[1]                 # a point of the START's mesh part (the slab is on the same part: 401 of 437 polygons): the reference of check()
# Both rows on the slab (z -3450..-2650, y 30), 90 and 190 from its house edge, EAST of the lane mouth (118, 20, -2623) and facing it; row 2 is 260 from
# the van's line z -3100 (LANE_CLEAR 250). WHY EAST: kl_fa_bots puts each bot 110..420 from the nearest START point and FAILS a bot that starts inside a level exit box
# (the box calls the van), and every way into the club passes the lane mouth, so the exit box (EXIT_V2) is the slab's south-west corner round the van's boarding place
# and no START point is within 420 of it (MEASURED by the bots step: 'is inside level exit box ... after 0 of path' was the first form's fault, rows at x -300..120).
# The TRAITOR row lies west of the lane mouth, z -2790, 110 .. 400 from the START rows, outside the box.
START_V2 = [(float(x), SLAB[2], z) for z, xs in ((-2740.0, (160, 280, 400, 520)), (-2840.0, (220, 340, 460, 580))) for x in xs]
TRAITOR_V2 = [(float(x), SLAB[2], -2790.0) for x in (-340, -240, -140, -40)]
TEAM_MERC_V2 = [(float(x), SLAB[2], z) for z in (-2700.0, -2780.0) for x in (-800, -740, -680, -620)]    # (team mode only; not Arcade)
POLICE = [(float(x), SLAB[2], -2760.0) for x in (900, 1000, 1100, 1200, 1300, 1400, 1500)]
# the eight police bodies (Heroes!Henchmen_0n) beside those points. GUESS
BODIES = [(p[0], p[1], p[2] - 70.0) for p in POLICE] + [(1600.0, SLAB[2], -2830.0)]
# team mode's respawn stages: the front office, the wardrobe, the entrance hall. GUESS: the points beside each
STAGE_B = [(1900.0, 354.0, 3300.0), (2000.0, 354.0, 3300.0), (2100.0, 354.0, 3300.0), (2000.0, 354.0, 3400.0)]
STAGE_C = [(-4.0, 180.0, -240.0), (96.0, 180.0, -240.0), (196.0, 180.0, -240.0), (-4.0, 180.0, -150.0)]
STAGE_D = [(-450.0, 100.0, -600.0), (-350.0, 100.0, -600.0), (-450.0, 100.0, -680.0), (-350.0, 100.0, -680.0)]
WEST, SOUTH = (-1.0, 0.0), (0.0, -1.0)
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz), or a place looked at)
def _spawn(v2):
    """ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing). v2: the criminals' kinds on the slab facing the lane mouth."""
    S_, T_, face = (START_V2, TRAITOR_V2, LANE_MOUTH) if v2 else (START_V1, TRAITOR_V1, DOOR_IN)
    tm = TEAM_MERC_V2 if v2 else [(float(x), OFFICE, float(z)) for z in (2750, 2850, 2950, 3050) for x in (2650, 2750)]
    u = (60, 0, 20) if v2 else (-50, 0, -35)          # (V2: row 2 + (0, 0, -35) would stand 225 from the van line)
    return {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (S_, (0, 0, 0), face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (T_, (0, 0, 0), face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), LANE_MOUTH),
            # the other modes' criminals stand in the office too, in rows of their own (it is 46 m2 of mesh: the rows are near)
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (S_, u, face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (S_, u, face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (T_, (0, 0, -45), face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (50, 0, -35), LANE_MOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (tm, (0, 0, 0), face),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), WEST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (50, 0, 40), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (-50, 0, -35), LANE_MOUTH)}


SPAWN = _spawn(False)           # (set_v2() makes it the round's: V2 or V1)

# ------------------------------------------------------------------ the loot
# Briefcases on the PUBLIC side of each counter (four of the study's nine prop ORIGINS lie over 1 m off the mesh:
# re/campaign_fa_club.md 8.4 item 3). (where the case's underside lies, degrees it is turned, value, what it lies on).
# MEASURED in the collision (floors.py): the desk PC0100_M05_OfficeTable_01 top y 414 over x 2600..2800, z 2200..2300
# (a laptop at x 2625..2650, papers at 2775); the sofa table top 377 over x 3100..3175, z 2530..2640; dance floor 1's
# bar counters SI0102_M05_BarCounter_4m_01 / _LeftCorner_01 top 158: the long one along z 950..995 from x -1800 to
# -1050 (the bartenders' side is the raised floor y 55 south of it, the public the dance floor north of it), the
# corner along x -1060..-1020 from z 560 to 960 (public: east); the ticket counter SI0101_CounterA_01's shelf 128
# over x 200..290, z -1360..-1140 (public: the corridor west of it); the coat check SI0105_M05_Wall_B_WardrobeBooth_01's
# counter 284 over x -600..-250, z -110..-70 (public: the wardrobe south of it, floor 179).
# GUESS: every place on those tops, every turn and value (the study: 300,000 / 100,000 / 50,000; 2.2 million without
# the upstairs bars, which wait for the stairs to be proven). The loot lies there from the load: the crew starts on it.
LOOT = [((2695.0, 414.0, 2250.0), 8.0, 300000, 'Yoko\'s desk'), ((2757.0, 414.0, 2262.0), -14.0, 300000, 'Yoko\'s desk'),
        ((2870.0, 340.0, 2245.0), 80.0, 300000, 'the floor beside the desk'),
        ((3135.0, 377.0, 2560.0), 96.0, 300000, 'the sofa table'), ((3140.0, 377.0, 2615.0), 84.0, 300000, 'the sofa table'),
        ((3010.0, 340.0, 2650.0), 20.0, 300000, 'the floor at the sofa'),
        ((-1600.0, 158.0, 978.0), 6.0, 100000, 'dance floor 1\'s bar'), ((-1420.0, 158.0, 978.0), -9.0, 100000, 'dance floor 1\'s bar'),
        ((-1038.0, 158.0, 730.0), 95.0, 100000, 'the bar\'s corner'),
        ((-400.0, 284.0, -93.0), 5.0, 50000, 'the coat check\'s counter'),
        ((228.0, 128.0, -1250.0), 88.0, 50000, 'the ticket counter\'s shelf')]
LOOT_REACH = 125.0                      # TriggerBox2 radius: the value of all 117 stock OnlineMoneyContainer triggers (kl_escape.REACH)
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None ('--loot-bags') = F07's bags
CASE_SCALE = 1.25                       # GUESS, kl_fa_loot's for that model (36 wide x 1.25 = 45: a real attache case)

# ------------------------------------------------------------------ the doors and the seal
# DOORS, the lead's default: the four leaves of the two office doors are OPEN AT BUILD TIME - sunk DOOR_DY in world
# y, their key-framed collision placements cut - the fall-back that walked offline (re/campaign_fa.md G1.3), so that
# the first live load cannot be stopped by a Dead Men door animation that does not play. (path below ROOT, stock
# world place, set). The outer door's group has flag 0x40000000: its leaves hold WORLD places in the .prp and
# local ones in the .gms (G1.1 trap 2; kl_fa_bank.Doors' arithmetic keeps the two apart).
DR = IN + 'M05_A_Inside_Daughter_Room_01a\\'
LEAVES = [(DR + 'SI0108_M05_DaughterRoomDoorA_02\\D1', (2500, 358, 3343), 'office, inner door'),
          (DR + 'SI0108_M05_DaughterRoomDoorA_02\\D2', (2500, 358, 3283), 'office, inner door'),
          (DR + 'SI0108_M05_DaughterRoomDoorB_01\\D04', (1500, 358, 3283), 'office, outer door'),
          (DR + 'SI0108_M05_DaughterRoomDoorB_01\\D05', (1500, 358, 3343), 'office, outer door')]
# True ('--doors-animate'): the leaves stay; DOORS_AT seconds after the round-start event each gets 'Activate', and
# each stores its own LAST frame DOOR_LAST first: the clip slides open at frame 30 and is SHUT again at frame 60,
# and a leaf that stores -1 / -1 plays the whole clip (G1.8: 30 is the campaign's own DoorCtrl number)
DOORS_ANIMATE = False
DOOR_DY = -1500.0                       # the study's: under everything of the level (its lowest floor is y 19)
DOOR_LAST = 30
DOORS_AT = 10.4                         # s from the round-start event: that event comes 8.4 - 8.8 s before GO
                                        # (kl_fa_author.BLAST_DELAY's note); the study's 'GO + 2 s'. GUESS
MPA_MESSAGE, MPA_LAST = 0, 14           # MatPosAnim fields: the message that starts it, the last frame (13 = the first)
# THE SEAL of the beat 'exit blocked': the campaign's own two invisible 'hero collision' objects at the street end
# of the queue lane, both STATIC meshes that stop heroes only (flags 0x108), each alone enough to shut the lane
# (MEASURED kl_route.py doors on a bare graft: four closures, four necessary - two office doors and these two):
#   HeroColi   a hollow box x -13..369, z -2612..-2335 (the campaign starts its hero INSIDE it). .gms flags 0x200308 -
#              the very form of 'M05_A_Inside_3rd_Storage_01a\HeroColi', which the campaign itself switches off with a
#              DeactivateGeom ('GeomDeactivator_Storage_Herocoli'). THE GATE: it stands from the load and the beat's
#              clock switches it off (ROLE 'seal off').
#   Plane01    a plane at z -2538. .gms flags 0x308 (not HeroColi's 0x200000 bit), and NOTHING in the campaign ever
#              switches it: whether a DeactivateGeom frees it is the study's open question (campaign_fa.md 4.2).
# So, by default, 'Plane01' is taken out at build time with the leaves and the gate is 'HeroColi' alone: the one
# piece whose switch has the campaign's own precedent - the seal is present from the start, and what takes it away
# does not hang on the unanswered question. (The stage asked for 'the seal present, the clock opens it'; that both
# pieces must be what stands is this file's reading, said here because it is a choice.)
#   SEAL_PLANE True ('--seal-plane')  both pieces stand, the DeactivateGeom names both
#   SEAL_OPEN True ('--seal-open')    both are sunk at build time: no gate at all
# ASSUMPTION (as the bank's vault door): a body switched off by a DeactivateGeom at run time stops colliding (stock
# F07 takes its 'BlockVisionPlane' away so; Retomoto's blown window is walked through). These two are STATIC
# placements where the bank's door is key-framed: the campaign's storage 'HeroColi' is the precedent for that.
# NOT KNOWN: whether an AI heister is stopped by 'heroes only' collision at all (the next stages' squads and bots).
EN = IN + 'M05_A_Inside_Entrance_01a\\'
SEAL = [(EN + 'HeroColi', (131, 0, -2478), 'the seal: hollow box'), (EN + 'Plane01', (94, 230, -2537), 'the seal: plane')]
SEAL_PLANE = False
SEAL_OPEN = False
SEAL_AT = 100.0                         # (was 120 until the fix after run C2: '--legacy') s from the round-start event (about 91 s after GO) to the seal's end: nobody is ever
                                        # locked in. '--seal S'. GUESS. The study's and stage L1's 75 s were set for a round
                                        # without enemies; with 40 guards on 80 m of way to dance floor 1 a clock of 66 s after
                                        # GO would nearly always come before the two squads are dead, and the beat be no beat
# the music's muffle switches. Each office door's dropped DoorCtrl also sent 'Doors_Opening' to an ActivateGeom of
# the club's audio subtree, which shows a 'suppress box' of the muffled track (re/campaign_fa_club.md 5, the second
# agent's note). With the doors open from the load the round-start event sends it once, through a host AIDWrapper;
# with '--doors-animate' the doors' own timer does. ASSUMPTION (from the names): without it the music stays as
# muffled as behind a shut door. (The boxes are not hidden in the file: the message may change nothing.)
MUFFLE = (AUDIO + 'GeomActivator_Door_01', AUDIO + 'GeomActivator_Door_02')
MUFFLE_MESSAGE = 'Doors_Opening'

# ------------------------------------------------------------------ what never ran in Dog Days
# Three controller kinds of the kept map are registered by kl2.exe and used by NO stock Dog Days level ('kl_maps.py
# first M05_A'; preflight calls each a RISK). Each is behind a flag. READ in kl2.exe for the defaults
# (C:/kl_scratch/club/l1/s/vt.py: the class's vtable against its base's, the routines that differ):
#   PositionLightControl x 7 (the light show; top-level 'Locations/M05_A/M05A_LightControll.zip')
#       own init (slot 13, 0x671cb0, 244 instructions) AND an own routine in slot 25 (0x72c400, 289 instructions:
#       ASSUMED its per-frame step), own save / load. Field 0 names the animated object 'Beat_M05\Ground_Beat05',
#       field 8 the music object 'Club_01_Clean_Music_01'. Code that runs at the load and every frame and has never
#       run in the retail game: IN DOUBT, so OFF - LIGHT_SHOW False: the controller comes off, its seven boxes and
#       the lists of lights they name stay; the lights are as the file has them (a static club).
#   ZIKLNKOBJ + StartAnim x 2 ('Beat_M05\Ground_Beat05', '..._SecondFloor', under the floor at y -160)
#       StartAnim has an own init (slot 13, 0x8f6b90, 92 instructions) and no step: it starts the clip at the load.
#       The clip is 'anmcol:animationdatabase#Beat_M05', Dead Men .ANM records converted by kl_anm's own GUESS, and
#       only the light show reads the object. IN DOUBT, so OFF - BEAT_ANIM False: the two are loaded as plain ZSTDOBJ
#       (build(): IK), lose the StartAnim, their model and their place in the picture (hidden): empty helper objects,
#       the stock form of 'Locations/M05_A/M05A_Audio.zip!STREAMS!Inside!Arrow'. No Dead Men clip is then in the .ANM.
#       '--light-show' without '--beat-anim' reads a still object: the two flags belong together.
#   ShotActivateDamage x 5 (the roof's chimney fans 'PC0300_M05_Chimney_A_0n!Fan_A', y 1206: not on this round)
#       differs from its base ZShotActivate (439 controllers in this very build, a stock kind) in ONE routine, slot 34
#       (0x4bb9b0, 132 instructions), besides its property list: its init (slot 13, 0x5aa380, 22 instructions) is the
#       base's and does not call slot 34 (C:/kl_scratch/club/l1/s/vt34.py). ASSUMED from that: slot 34 is what runs when
#       the fan is SHOT and nothing of its own runs at the load - but where slot 34 IS called from was not found, the
#       fans stand on the roof, which this round never reaches, and keeping them buys the round nothing. IN DOUBT, so
#       OFF - FAN_DAMAGE False: the five lose the controller (the fans turn and cannot be shot to pieces).
#       '--fan-damage' keeps them: for the roof stage.
LIGHT_SHOW = False
BEAT_ANIM = False
FAN_DAMAGE = False
BEAT = [IN + 'Beat_M05\\Ground_Beat05', IN + 'Beat_M05\\Ground_Beat05_SecondFloor']
NEVER_RAN = collections.OrderedDict([('PositionLightControl', 7), ('StartAnim', 2), ('ShotActivateDamage', 5)])

# ------------------------------------------------------------------ the host's layer
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put (kl_fa_author.PARK)
ESC_AT = (-640.0, SLAB[2], -2800.0)     # the escape marker's place on the slab: BESIDE the van's lane (300 north of its line),
                                        # level with the rear doors of the standing van, 7.8 m from the lane's mouth - not over
                                        # the stop and not in the arriving van's sweep (kl_fa_bank's review finding; prepare_host
                                        # and check() hold it against the drive: LANE_CLEAR). GUESS
ESC_POI_UP = 188.0                      # the marker over the floor (F07: 190 over its road; Retomoto's)
# THE BOUNDS at the slab's three open edges (re/campaign_fa.md 4.2 item 9): beyond the slab there is no collision
# floor - whoever walks 13 m west, 17 m east or 8 m towards the parked cars from the lane's mouth falls through a
# pavement that is drawn (club 8.4 item 6). Three of F07's bound trios: the Bound box 6 m deep from the edge
# outwards, its two warn boxes the same and 1.2 m onto the slab (stock F07: the warn boxes reach 2.5 m in front
# of their bound). They PUNISH, they do not STOP: GUESS - what a level bound does to a player at the rim was never
# seen, and static collision cannot be added (re/havok.md 141). The fourth side is the building.
BOUND_Y = (250.0, 400.0)                # centre and half height: y -150..650
BOUNDS = {'030_LevelBound_StreetLeft': ((-1520, -3050), (300, 600), (-1460, -3050), (360, 600), 'west of the slab: Bound x -1820..-1220, warn from x -1100'),
          '030_LevelBound_StreetRight': ((2120, -3050), (300, 600), (2060, -3050), (360, 600), 'east: Bound x 1820..2420, warn from x 1700'),
          '040_LevelBound_AlleyTop': ((300, -3750), (2120, 300), (300, -3690), (2120, 360), 'the kerb: Bound z -4050..-3450, warn from z -3330')}
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft')
          for b in ('Bound', 'Warn01', 'Warn02')]
# ... and under the three edges the campaign's own three single kill boxes (they stand in the car showroom under
# the glass roof; campaign_names() keeps them, strip() re-places them): whoever steps off the slab falls into one.
# Their tops are y -100: 1.3 m under the slab and under the mesh strip beside it (x -3765..5786), on which the next
# stage's police come. name -> (centre, half extents, what). GUESS: the boxes, and that a body falling through one is
# killed (the campaign's field values are kept: 'CheckInsideEnter')
KILL = collections.OrderedDict([
    ('Specials!KillBox', ((-2620, -250, -3050), (1400, 150, 650), 'under the west edge: x -4020..-1220, z -3700..-2400')),
    ('Specials!KillBox#01', ((3920, -250, -3050), (2100, 150, 650), 'under the east edge: x 1820..6020')),
    ('Specials!KillBox#02', ((1000, -250, -4400), (5020, 150, 950), 'under the kerb and the road: z -5350..-3450'))])
# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # the round's markers and planes
    'FASpecials!POI!Trigger_POI_TheLootArea': ((2800, 450, 2450), None, (450, 150, 320), 'GUESS: box round the START rows in the office (F07: round its start); it starts the loot marker\'s 11 s timer'),
    'FASpecials!POI!POI_TheLootArea': ((2700, 520, 2260), None, None, 'over Yoko\'s desk; GUESS: 106 over its top'),
    'FASpecials!PIP!EnterLootArea': ((2800, 450, 2450), None, (450, 150, 320), 'THE ENTERS BOX ROUND THE START ROWS (x 2350..3250, z 2130..2770), not a plane behind them: '
                                     'an AI heister\'s stage 1 is a place inside this box and its order is START -> ENTERS -> loot (re/campaign_fa_club.md 4.3 a)'),
    'FASpecials!PIP!ExitLootArea': ((125, 120, -1440), None, (300, 150, 50), 'GUESS: a plane behind the entrance door (its leaves stand open at z -1366, gap x -148..162), after the last loot'),
    'FASpecials!POI!POI_TheEscapeArea': ((ESC_AT[0], ESC_AT[1] + ESC_POI_UP, ESC_AT[2]), None, None, 'over ESC_AT on the slab'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((300, 250, -3050), None, (1500, 300, 450), 'GUESS: the slab (z -3500..-2600), beyond the seal. It takes the loot marker away'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((300, 250, -3050), None, (1500, 300, 450), 'as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((300, 250, -3050), None, (1500, 300, 450), 'as above'),
    # the exit box (calls the van) and the line on the way out
    'Gameplay!EscapeSetup!otrExitLevel': ((300, 200, -3050), None, (1450, 250, 400), 'GUESS (the study): the slab, x -1150..1750, z -3450..-2650 - it begins 0.3 m beyond the seal\'s box'),
    'Specials!LevelSpeak!TriggerBox': ((0, 280, -250), None, (300, 120, 150), 'GUESS: the wardrobe (floor y 179), where the crew comes down from the stair landing'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((0, 280, -250), None, None, 'with its trigger box'),
    # spawn cameras (camera, look-at): all GUESS, none looked through
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((2850, 560, 2780), None, None, 'GUESS: over the office'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((2800, 400, 2420), None, None, 'the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((2000, 600, 3100), None, None, 'GUESS: front office'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((2000, 410, 3320), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((200, 420, -80), None, None, 'GUESS: wardrobe'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((0, 240, -240), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((-300, 350, -420), None, None, 'GUESS: entrance hall'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((-400, 160, -640), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((300, 520, -3350), None, None, 'GUESS: over the kerb'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((118, 120, -2700), None, None, 'the lane\'s mouth'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((300, 520, -3350), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((118, 120, -2700), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': ((2500, 450, 3313), None, (80, 150, 200), 'GUESS: the inner office door (plane x 2500, z 3167..3488)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': ((-55, 260, 320), None, (250, 150, 150), 'GUESS: the stair landing (campaign checkpoint 4)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': ((-414, 200, -500), None, (200, 150, 100), 'GUESS: the entrance hall\'s top (floor y 100)'),
    # jump points (developer aids in stock levels; nothing names them): the campaign's stations
    'Specials!JumpPoints!01_Start': ((2800, OFFICE, 2490), (0.0, 1.0), None, 'the office, between the START rows'),
    'Specials!JumpPoints!02_MarketMain': ((2000, 354, 3300), WEST, None, 'the front office'),
    'Specials!JumpPoints!03_MarketOrange': ((-864, 40, 2491), SOUTH, None, 'campaign Obj#02_Dance02: dance floor 2'),
    'Specials!JumpPoints!04_LootWarehouse': ((-1100, 20, 1150), SOUTH, None, 'dance floor 1, at the bar'),
    'Specials!JumpPoints!05_MarketGreen': ((-4, 180, -240), SOUTH, None, 'campaign Jump_01_Wardrobe'),
    'Specials!JumpPoints!06_Exit': (ESC_AT, SOUTH, None, 'the pavement'),
}
for _g, (_b, _bh, _w, _wh, _why) in BOUNDS.items():
    PLACE['Specials!LevelBound!%s!Bound' % _g] = ((_b[0], BOUND_Y[0], _b[1]), None, (_bh[0], BOUND_Y[1], _bh[1]), 'GUESS: ' + _why)
    for _n in ('Warn01', 'Warn02'):
        PLACE['Specials!LevelBound!%s!%s' % (_g, _n)] = ((_w[0], BOUND_Y[0], _w[1]), None, (_wh[0], BOUND_Y[1], _wh[1]), 'GUESS: ' + _why)
# host objects that get a new job in wire(): role -> name (each a single top-level node)
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'seal timer': FF + 'RivalMercVan!Timer',                         # TriggerDelay2 SEAL_AT: the beat's guaranteed clock
        'seal off': FF + 'RivalMercVan!GeomDeactivator_DriveInVan',      # DeactivateGeom -> the seal
        'doors timer': FF + 'RivalMercVan!TimerVanGo',                   # TriggerDelay2 DOORS_AT (DOORS_ANIMATE)
        'doors': FF + 'RivalMercVan!Activator_OLD_VanGo',                # AIDWrapper 'Activate' -> the four leaves (DOORS_ANIMATE)
        'muffle': FF + 'RivalMercVan!Activator_VanSound',                # AIDWrapper 'Doors_Opening' -> the music's two switches
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel',
        # the enemies' stages and the beat's fast way (the tables at SQUADS)
        'office timer': FF + 'RivalMercs!Timer',                         # TriggerDelay2 OFFICE_AT -> the front office's two squads
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # TriggerBox at the inner office door -> the walkway's squads
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # TriggerBox on the walkway -> dance floor 1's and the upstairs squads
        'floors counter': 'Gameplay!020_Loot!FollowPlayers!TriggerCounter',  # TriggerCounter 2 <- the two dance-floor squads' 'wiped out' lists
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate'}                  # GateGroup + two GatePath: the first of counter / clock lets the enemies in
# the fix after runs C0 - C2 (VAN_LATE, RESET): five more free objects of F07, kept like the rest (a kind each, none was in use here).
# They are in ROLE (and so in KEEP) only while their flag is on: set_roles()
ROLE_NEW = {'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',            # ActivateGeom -> the van's group (VAN_LATE)
            'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',       # TriggerDelay2 VAN_AFTER, named by the seal's clock and counter
            'van timer b': FF + 'RivalMercs!DisableVisionBlocker!TimerInputAI',   # TriggerDelay2 VAN_EARLY, named by the wardrobe's box
            'reset show': FF + 'Shutters!GeomActivator_TearGas_RIGHT',       # ActivateGeom -> the seal again (RESET), first in the round-start list
            'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator'}   # DeactivateGeom -> the van's group again (RESET)
LATE_ROLES = ('van on', 'van timer', 'van timer b')
RESET_ROLES = ('reset show', 'reset hide')
# THE WAKE FIX (2026-10-12, after run C8; NOT RUN IN THE GAME): the nine staged squads were woken by the bots' gates ALONE (TriggerActorsDead lists), i.e. only when a bot has
# reached the hold of the room before theirs. Six more free objects of F07 (none is named by anything in F07: MEASURED C:/kl_scratch/club_wake/f07.py) carry the second and the
# third trigger of each wake group: three TriggerBox (criminals only, once) and three TriggerDelay2 (the backstops, started by the round-start list). In ROLE only while WAKE_MORE
# is on (set_roles); WAKE_BOX (below) holds the numbers. re/club_campaign.md 'Wake, after run C8'.
WAKE_MORE = True
WAKE_NEW = collections.OrderedDict([
    ('wake box 1', 'Gameplay!020_Loot!tbExitLoot'), ('wake box 2', 'Gameplay!030_AfterLoot!tbExitFinancialAlley'), ('wake box 3', 'Gameplay!040_Escape!tbEscapeAI'),
    ('wake timer 1', FF + 'RivalMercs!RandomizeFight!Timer_LEFT'), ('wake timer 2', FF + 'RivalMercs!RandomizeFight!Timer_RIGHT'), ('wake timer 3', FF + 'RivalMercVan!Timer_PFBlocker')])
# Free single top-level objects of F07 this file does not touch yet (add the name to KEEP_MORE, give it a ROLE):
# trigger boxes Gameplay!020_Loot!tbExitLoot, ...!FollowPlayers!tbCountPlayers, Gameplay!030_AfterLoot!
# tbExitFinancialAlley, Gameplay!040_Escape!tbEscapeAI, Gameplay!RunToEscape!tbRunToEscape / tbRunToEscape1Player;
# counter Gameplay!RunToEscape!tcRunToEscape; TriggerDelay2 Gameplay!010_FirstFight!RivalMercs!RandomizeFight!Timer_LEFT
# / _RIGHT, ...!DisableVisionBlocker!Timer / TimerInputAI, ...!RivalMercVan!Timer_PFBlocker, ...!CoverStateChangerHero!
# Timer, ...!TimerMercsVanExit, six of ...!Shutters!, Gameplay!RunToEscape!Timer / Timer1Player / Timer3Player;
# AIDWrapper ...!CoverStateChangerHero!ActivateCovers / DeactivateCovers and four ...!Shutters!Activator_*; ActivateGeom
# ...!Shutters!GeomActivator_TearGas_LEFT / _RIGHT; DeactivateGeom ...!RivalMercs!DisableVisionBlocker!GeomDeactivator.
# F07's AIMonitor names five timers of its opening at the round start: wire() writes that list, so that a ROLE object
# is started only by what this file names.
KEEP_MORE = ()

# ------------------------------------------------------------------ the enemies (stage L2)
# THE CAMPAIGN'S SQUADS THAT STAY: 40 guards in 17 squads (re/campaign_fa_club.md 1.5, 4.2, 8.2 item 5) - the nine
# the study calls usable as they stand (21 men) and the eight 'first run' squads on the round's way once their
# AttachGeomToBone (a flashlight or a wand pinned to a hand) and WarnBehaviourRout are off (19 men). What does not
# stay: the roof's three squads, the five 'first run' squads of the upper floors' far ends, the 'Obliterate'
# ZFusionSquads, the civilians, Yoko and Lynch.
# kl_fa_author.squad_plan's rule cannot say this: it wants a behaviour rout, and 16 of the 17 have NONE - a club squad
# is a ZSquadScript, its men and at most a SquadModifierBehaviour (MEASURED C:/kl_scratch/club/l2/s/sq.py on a bare
# graft with every squad kept; out/sq_keep.txt). So the rule is widened here (squad_plan()): the squad's subtree holds
# only plain squad kinds (kl_fa_author.PLAIN) and what STRIP takes off, a ZSoldier for every actor, and it starts by
# what its row says. squad -> (stage, the child that starts it):
#   'load'    IN THE WORLD FROM THE LOAD, as the campaign has it (ZSquadScript field 3 = 1; nothing starts it): the
#             fifteen bouncers of the walkway, the two dance floors, the stairs' balcony and the entrance. None of
#             them is seen from a place a criminal starts at (MEASURED s/los.py), and nothing is asked of Dog Days
#             that the campaign does not ask of Dead Men. ASSUMPTION: a squad without a rout that is in the world
#             fights whoever it sees ('eStayBack', normal alertness: Dog Days' own squads all have a rout).
#   'office'  Yoko's four bodyguards in the front office: the round's timer, OFFICE_AT
#   'walk'    the walkway's two and the second run's first squad: the box at the inner office door (WALK_BOX)
#   'floor'   the second run's dance-floor squad and the four squads of the upper floors: the box on the walkway
#   'open'    the three hunters: the beat's gate (GATE) - they HAVE a rout, the stock way to start a squad
# A staged squad gets field 3 = 0 and is NOT IN THE WORLD until its child is named (re/map_ai.md 2; seen live on
# Retomoto and the bank for squads started by a ROUT). STAGED - THE ONE FIRST-TIMER OF THIS STAGE FOR A BUILD OF OURS:
# 'office', 'walk' and 'floor' name a SquadModifierBehaviour whose field 4 is 'eAM_Activate'. That is the campaign's
# own way (its 'SecondRun!Rt\Way#01' names the six 'Alert' children so; the value is written here into the three
# children that lack it). Stock Dog Days does it in its STORY levels only: 19 modifiers with that value in L02, L06,
# L09 and L11, 16 of them on a squad with field 3 = 0, named by a TriggerBox, a GatePath, a TriggerCounter - one
# (L11) on a squad that has no rout at all, as here (MEASURED s/amact.py, out/amact.txt). No Fragile Alliance level
# has one: of the modifiers the triggers name in F01 / F05 / F07 / F08 none has the value and every waiting squad
# there is started by a rout (s/sqnamed.py), and none names one from a TriggerDelay2 (the 'office' stage: ASSUMPTION
# that who sends the message does not matter). If it does not work the 22 men of those stages never come - no fault,
# an emptier club, and the seal opens by its clock. The fall-back is SQUADS_AWAKE ('--squads-awake'): every campaign squad in the
# world from the load. GUESS: the split into stages. MEASURED: nobody of a staged squad is seen from where the
# crew can be before his stage (check(): Sight).
E1, E2 = 'AI_Players!Enemies!FirstRun!', 'AI_Players!Enemies!SecondRun!'
SQUADS = collections.OrderedDict([
    (E1 + 'Backroom!WaitingRoom', ('office', 'Alert')),             # 2, front office
    (E2 + 'YokoGuards', ('office', 'SquadModifier')),               # 2, at the inner door (the study: 'needs its flag set')
    (E1 + 'DanceFloor02!FatBounceronWalkway', ('load', None)),      # 1, the walkway's top
    (E1 + 'Surprise2', ('walk', 'Alert')),                          # 2, the walkway
    (E2 + 'Dance#01', ('walk', 'Alert')),                           # 3: walkway, dance floor 2, dance floor 1
    (E1 + 'DanceFloor02!Dancefloor02a#01', ('load', None)),         # 3, dance floor 2
    (E1 + 'DanceFloor02!Dancefloor02a#02', ('load', None)),         # 2, between the floors, at the bar
    (E1 + 'DanceFloor02!Dancefloor02a#03', ('load', None)),         # 1, dance floor 2 under the walkway
    (E1 + 'DanceFloor01!On_Dancefloor#02', ('load', None)),         # 3, dance floor 1
    (E2 + 'Dance#02', ('floor', 'Alert')),                          # 3, dance floor 1
    (E2 + 'Lounge#01', ('floor', 'Alert')),                         # 3, second floor: off the way, at the detours
    (E2 + 'Lounge#02', ('floor', 'Alert')),                         # 2, third floor
    (E2 + 'Rave#01', ('floor', 'Alert')),                           # 2, the rave bar (re-placed: MEN)
    (E2 + 'Rave#02', ('floor', 'Alert')),                           # 3, the rave gallery
    (E1 + 'SurpriseStairs', ('load', None)),                        # 2, the balcony over the stair landing
    (E1 + 'Bodyguards_First_Floor!Entrance', ('load', None)),       # 3: wardrobe, entrance, the lane's bouncer
    (E1 + 'Hunters!HunterKillers', ('open', 'HuntBehaviour'))])     # 3 (re-placed: MEN); their search box is the whole club
STAGED = 'eAM_Activate'                 # SquadModifierBehaviour field 4 of a child that starts a squad
MOD_ACTIVE = 4
SQUAD_ACTIVE, SQUAD_DEAD = A.SQUAD_ACTIVE, A.SQUAD_DEAD     # ZSquadScript fields 3 ('in the world from the load') and 8 (the 'wiped out' list)
SQUADS_AWAKE = False                    # True ('--squads-awake'): field 3 = 1 on all 17, whatever their stage
# what comes off a kept squad before the join. kl_fa_author.STRIP (the campaign's mini-cutscene kinds) and the two
# kinds kl2.exe registers and no stock Dog Days level uses (re/campaign_fa_club.md 8.1 item 13). ASSUMED harmless:
# AttachGeomToBone pins a prop to a hand bone; the props of the kept squads (18: flashlights, the door bouncer's wand) would lie at
# their guards' feet without it, so each is hidden with its group. WarnBehaviourRout is the campaign's 'warn the
# guest' rout of two squads, which nothing here would name
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout'}
# a message list of these kinds inside a kept squad may only name a node that still holds a controller: with the
# mini-cutscenes gone 'YokoGuards' would send its alert to a bare box, the walkway's two boxes to a bare group
# (kl_fa_author.QUIET does this for two Retomoto boxes by name)
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
# THE BEAT'S FAST WAY: both squads of the second run's dance floors wiped out (the six men stand on the walkway and
# on the two floors). ASSUMPTION: ZSquadScript field 8 is sent when the last man is dead (re/fa_gamemode.md 0.6;
# Retomoto's boardroom loot and this level's own office door hang on it - the campaign's 'WaitingRoom' squad names
# its door so). If it never comes the clock opens the seal (SEAL_AT)
BEAT_SQUADS = (E2 + 'Dance#01', E2 + 'Dance#02')
GATE_WAYS = ('Way#01', 'Way#02')        # the gate's two paths: the counter's, the clock's. Stock F07 lets its
                                        # 'Timer1Player' and 'Timer3Player' both name 'Gameplay!RunToEscape!Timer' through
                                        # these two: ASSUMPTION from that use (GateGroup was not read in kl2.exe) that only
                                        # the first path to come passes. The seal itself does NOT hang on the gate: counter
                                        # and clock each name its DeactivateGeom directly. What a GatePath is named by and
                                        # names in stock (MEASURED s/gates.py): by a TriggerCounter (F08) and TriggerDelay2
                                        # (F05 F07 F08); a DefendBehaviourRout once (F01), else modifiers, timers, geom
                                        # switches. If both paths pass, the routs are named twice (ASSUMED harmless)
OFFICE_AT = 10.0                        # s from the round-start event to the front office's four. That event comes 8.4 - 8.8 s
                                        # before GO (kl_fa_author.BLAST_DELAY's note), so this is GO + 1.2 .. 1.6 s: the study's
                                        # 'GO + 2 s', a little earlier - the nearest START point is 7.8 m from the inner doorway,
                                        # and nobody is to stand in it when four men come into the world behind it. GUESS
# the two boxes that start a stage: (centre, half extents). GUESS: the boxes. MEASURED (C:/kl_scratch/club/l2/s/plan.py,
# and check() on every build): from no point of the mesh inside a box is a man of the squads it starts in sight.
WALK_BOX = ((2380, 450, 3320), (120, 150, 200))     # the front office's east end: the first step through the inner door
FLOOR_BOX = ((1000, 450, 2900), (300, 150, 350))    # the walkway's upper half (floor y 380 down to 320)
# MEN RE-PLACED (strip()): man's group -> (x, a height near the mesh's there, z); he is put ON the mesh there.
#   YokoGuards   one of the two is seen through the inner doorway from seven places a criminal starts at
#                (MEASURED s/plan.py): both go 2 m into the front office's south half, where no start place sees them
#   Rave#01      both stand 105 / 154 beside the mesh, behind the rave bar where the campaign's bartenders stand
#                (re/campaign_fa_club.md 8.2 item 5): to the public side of the bar
#   the hunters  the campaign has them IN THE WARDROBE, 1.3 - 3 m from the round's own station there - right for a
#                story in which nobody is inside when they come, wrong here: they would come into the world among
#                the crew (the bank's review round 1). Up to the second floor's lounge, over the stairs: no place of
#                the way sees it (MEASURED s/hidden.py: 88 view points), 21 - 27 m of mesh down to the stair landing
#                (narrowest edge 2.9 m). So they 'come in' from behind and above, on foot; the wardrobe is where
#                they arrive. GUESS: every place. MEASURED: on the START's mesh part, on free floor, unseen
MEN = collections.OrderedDict([
    (E2 + 'YokoGuards\\Guard#01', (2300, 361, 3200)), (E2 + 'YokoGuards\\Guard#02', (2300, 361, 3300)),
    (E2 + 'Rave#01\\Guard#01', (-2500, 460, 900)), (E2 + 'Rave#01\\Guard#07', (-2500, 460, 650)),
    (E1 + 'Hunters!HunterKillers\\Guard#02', (400, 460, 600)), (E1 + 'Hunters!HunterKillers\\Guard#03', (600, 460, 600)),
    (E1 + 'Hunters!HunterKillers\\Guard#04', (600, 460, 400))])
MAN_OFF, MAN_IN = 60.0, 15.0            # a man this far beside the mesh at most is put this far inside it (kl_fa_bank's). GUESS
STOCK_ROWS = True                       # False ('--dead-men-rows'): Dead Men's soldier rows stay (kl_fa_bank.STOCK_ROWS' note:
                                        # as converted the guards have health 50 and a skill NAME; stock police 100 / 175)

# ------------------------------------------------------------------ THE FIX AFTER RUNS C0 - C2 (2026-10-12; NOT RUN IN THE GAME)
# The first live runs (C0 bare, C1 no enemies, C2 full) loaded and played without a fault; C1: all seven AI heisters escaped.
# C2 (40 guards, then police, an idle human): four heisters dead 21 .. 26 s after GO in the front office / on the walkway (two
# 'ONE STEP' = the point-blank rule of re/melee_damage.md: a soldier that fires within 160 units lands 100 bullets) and two dead
# in one tick while ABOARD (the van went from state 3 to 6 = destroyed). Every flag below is ON by default; '--legacy' puts
# the build of the first delivery back (the control: `test --legacy` gives the archive a4d024f3 again).
#   GUARDS_OFF    the four bodyguards of the front office (YokoGuards, WaitingRoom) stand on the dance floor's upper deck
#                 (FRONT_MEN), 4 - 6 m from the route, out of sight of the START rows, out of the 160-unit point-blank ring of
#                 every place of the way (FRONT_CLEAR 400 from the office doors and from the way). Nobody is removed: 40 guards.
#                 check(): no man of the 'office' stage nearer than FRONT_CLEAR to a door, the way or an AI heister's place.
#   POLICE_EAST   the ten arriving police start on the slab EAST of the van's stop (ARRIVE_EAST): the west six stood 3 - 5 m
#                 from the drive and 8 m from the stop, the van came through their places; every man has a post of his own
#                 (>= 150, mostly 200+, apart), 10 m or more from BOT_PARK, in two rows 250 / 300 from the van's line.
#   VAN_LATE      the van is NOT in the world until the crew is close: its group is hidden from the load, its FakeTarget (the
#                 thing the police aim at) is taken off, and an ActivateGeom of F07's own ('van on') shows it VAN_AFTER s after
#                 the seal opens (counter or clock - nobody can call the van before) and VAN_EARLY s after the wardrobe's box.
#   RESET         round 2 starts as round 1: the round-start event names, FIRST, two stock objects that show again what the round
#                 switched off (the seal) and hide again what it switched on (the late van). check(): every node of this layer that
#                 switches geometry is covered, or is in RESET_CANNOT.
#   VOICE         kl_snd.VOICE = True for the build: the 55 streamed single IMA ADPCM lines (police one-liners, guard lines) become
#                 records in the level's .WAV (Dog Days cannot read them from the stream file: re/luvsic_pass.md 1.1, re/voice.md 6.2)
#   LOOT_SECONDS  the bots' wait at the office loot 30 -> 18 s and SEAL_AT 120 -> 100 s: the owner, 'less standing still, that's a big
#                 one' (the gate hold: 83 s in the entrance hall, now about 55 s). GUESS: both numbers.
LEGACY = False
GUARDS_OFF, POLICE_EAST, VAN_LATE, RESET, VOICE = True, True, True, True, True
LOOT_SECONDS = 18
LEGACY_FLAGS = {'SEAL_AT': 120.0, 'GUARDS_OFF': False, 'POLICE_EAST': False, 'VAN_LATE': False, 'RESET': False, 'VOICE': False, 'LOOT_SECONDS': 30, 'ROOM_GATES': False, 'PRESSURE': False, 'WAKE_MORE': False, 'V2': False}
FRONT_SQUADS = (E1 + 'Backroom!WaitingRoom', E2 + 'YokoGuards')
# the four posts: x, y, z on the navigation mesh part of the START, the dance floor 2's upper deck west of the stairs. MEASURED
# (C:/kl_scratch/club_fix/explore.py on the built level): each >= 400 from the doors, from every place of the way in (ROUTE_IN every 100)
# and from every AI heister place after the front office (the best set of four: 422 from the nearest), and in sight of none of the eight START
# places. >= 250 apart (the deck is 550 x 250)
FRONT_MEN = collections.OrderedDict([
    (E2 + 'YokoGuards\\Guard#01', (0, 364, 2050)), (E2 + 'YokoGuards\\Guard#02', (350, 362, 2050)),
    (E1 + 'Backroom!WaitingRoom\\Guard#01', (475, 363, 2275)), (E1 + 'Backroom!WaitingRoom\\Guard#02', (200, 368, 2250))])
FRONT_CLEAR = 400.0                     # an office-stage man this far from the doors, the way in and the heisters' places (the Vault's CREW_CLEAR)
VAN_AFTER, VAN_EARLY = 2.0, 1.0         # s after the seal opens / after the wardrobe's box that the van is shown. GUESS
# F07'S POLICE THAT ARRIVE when the seal opens (the owner, of the bank's square: 'should be a big shootout'; the
# study's weakness 7: 'nothing ever arrives'). Four of F07's own squads, ten men, each a ZGROUP + ZSquadScript whose
# children's places are offsets (kl_fa_bank.place_hall's reading): squad -> (anchor, the men's places, the points of
# '10_RunToCover', the point of '10_Defend'), all (x, z) on the pavement. Stock F07 starts each by naming its
# '10_RunToCover' from a box 40 - 50 m from where its men stand; here the gate names it.
#   WHERE THEY COME INTO THE WORLD: on the pavement's mesh strip just beyond the slab's two ends, 20 - 26 m from the
#   lane's mouth to either side, at the foot of the building's front. MEASURED (s/seen_strip.py): no place the crew
#   can be before the seal opens - the way's stations, the queue lane up to the seal's inner edge - sees the strip's
#   north band from x -3700 to -500 or from x 1900 to 2400 (the lane's west side is a wall; further east the tool's
#   lines pass over the lane's rails). THERE IS NO COLLISION FLOOR THERE, only mesh (the slab is x -1200..1800).
#   ASSUMPTION (the study's): an AI character walks the mesh and needs no collision under it. If a man falls instead,
#   he falls into a kill box and the wave does not come. NO LIVE RUN HAS SHOWN IT (review round 1: a Havok character stands
#   on the collision world, the mesh only guides), so the DEFAULT is the safe form, POLICE_ON_SLAB: the ten start ON the
#   slab at its two ends (ARRIVE_SLAB), two of them in sight of the lane when the seal opens. '--police-strip' = this form.
#   WHERE THEY RUN TO: cover points at the slab's two ends, 10.5 - 16 m from the lane's mouth and none before it (the
#   bank's run V2: eight police set up in the mouth of the only exit killed the crew), each 2.5 m or more from the
#   line z -3100 the van drives (LANE_CLEAR) and - stage L3, the two southern points of the west squads moved for it
#   (they were (-950, -3400) and (-800, -3400): 4.3 and 3.4 m from the rear doors of the standing van) - 5 m or more
#   from the boarding place (BOARD_CLEAR). GUESS: every place. MEASURED (check()): each man and cover point on the
#   START's mesh part, each cover point on free floor, each man out of sight.
G30 = 'Gameplay!030_AfterLoot!'
ARRIVE = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-2000, -2750), [(-2300, -2750), (-2200, -2750), (-2100, -2750)],
                                           [(-1100, -2720), (-1100, -3380), (-1160, -3410)], (-1050, -2780))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((-2000, -2850), [(-2500, -2850), (-2400, -2850)], [(-1150, -2850), (-1000, -2680)], (-950, -2780))),
    (G30 + '030_FinancialAlleyExit_Right', ((2000, -2750), [(1950, -2750), (2050, -2750), (2150, -2750)],
                                            [(1750, -2700), (1700, -3380), (1550, -3400)], (1750, -2850))),
    (G30 + '030_FinancialAlleyExitStreet_Right', ((2000, -2850), [(2250, -2850), (2350, -2850)], [(1600, -2850), (1400, -3400)], (1750, -2950)))])
ARRIVE_SLAB = {G30 + '030_FinancialAlleyExit_Left': [(-1150, -2700), (-1050, -2700), (-1150, -2800)],      # POLICE_ON_SLAB: the men's
               G30 + '030_FinancialAlleyExitStreet_Left': [(-1150, -3400), (-1050, -3400)],               # places, at the slab's ends
               G30 + '030_FinancialAlleyExit_Right': [(1750, -2700), (1750, -2800), (1750, -3400)],
               G30 + '030_FinancialAlleyExitStreet_Right': [(1650, -3400), (1550, -3400)]}
# POLICE_EAST (the fix after run C2): all ten start EAST of the van's stop. The west six stood 3 - 5 m from the drive and 8 m from the stop (the
# van drove through their places). Two rows: the north one at the house fronts (z -2655: 105 from the AFTER_DEATH points at z -2760, which
# stay where they are - FED_CLEAR keeps them 10 m from the boarding place), the south one at the kerb (z -3400); 150 / 200 apart in a row,
# each >= 1000 from BOT_PARK. squad -> (men, cover points, the defend point), (x, z). MEASURED by check(): each man and cover point on
# the START's mesh part, 250 / 300 from the van's line, 100 from a returning policeman's place, 10 m from BOT_PARK
ARRIVE_EAST = {G30 + '030_FinancialAlleyExit_Left': ([(1030, -3400), (1180, -3400), (1150, -2655)], [(1250, -2720), (1300, -3380), (1200, -3400)], (1200, -2780)),
               G30 + '030_FinancialAlleyExitStreet_Left': ([(1330, -3400), (1350, -2655)], [(1450, -2850), (1100, -3400)], (1350, -2850)),
               G30 + '030_FinancialAlleyExit_Right': ([(1480, -3400), (1630, -3400), (1550, -2655)], None, None),
               G30 + '030_FinancialAlleyExitStreet_Right': ([(1780, -3400), (1750, -2655)], None, None)}      # None: the squad's own (ARRIVE)
ARRIVE_START = '10_RunToCover'
ARRIVE_Y = SLAB[2] + 1.0               # a man's height on the pavement (F07's stand 1 over their floor)
POLICE_ARRIVE = True                    # False ('--no-police'): none of the four squads is kept
POLICE_ON_SLAB = True                   # False ('--police-strip'): the mesh strip, see ARRIVE
LANE_CLEAR = 250.0                      # kl_fa_bank's: no spawn point, player body, man, cover point, escape marker or station of
                                        # the way out nearer than this to the van's drive (the lane that is tested is 110 either
                                        # side; the van's kill box is 90). GUESS. The boarding place is the one exception: the
                                        # box rides on the van, a player goes there when the van STANDS
POLICE_CLEAR = BK.POLICE_CLEAR          # a returning policeman's point or body this far from a squad's man
LATE_CLEAR = 300.0                      # a man who comes into the world after the load: at least this far from every place the
                                        # crew can be before his stage (and out of sight of each: check()). GUESS
# the escape: F07's first van, its relay, the exit trigger and the two 'last van' objects (the monitor is kept by
# kl_fa.host_keep). F07's SECOND AND THIRD VAN ARE NOT KEPT (kl_fa_bank: a van without a use cannot be parked under
# the map - its ZFakeTarget outside the rooms' bounds is the 0x686a66 crash).
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'       # everything of the van with a place is below it (kl_fa_author.place_vans)
# THE VAN'S ROAD (kl_map_escape.van_plan_points makes the plan of it - keys, boarding box, camera, bounds - and
# van_prepare lays F07's keys on it; the bank's ROAD is the worked example). One straight line along the pavement,
# z -3100, the study's (re/campaign_fa.md 4.2 item 8), FROM THE WEST:
#   arrive  the van waits at the first point, 50 m west of its stop and 41 m west of the slab's edge, where the
#           pavement is drawn between the house fronts (z -2600) and the kerb (z -3460) and NOTHING has collision:
#           west of x -3765 it stands off the navigation mesh too. 50 m in F07's 7.2 s is F07's own drive (51 m),
#           unscaled; the study's first road was 62 m, over kl_map_escape.LIMIT_IN
#   stop    the standing van's origin at x -300: its nose (250 ahead) is at x -50, 1.7 m WEST of the line straight
#           out of the lane's mouth (x 118) - the arriving van never passes before the door the crew comes out of
#           (MOUTH_SIDE; the study's stop at x 1000 swept 22 m of slab in front of it). Its rear doors (the
#           boarding box, 337 behind the origin) are at (-637, 30, -3100): on the slab, 5.6 m inside its west edge
#           and 4.6 m clear of the west bound's warn box, 8.9 m from the lane's mouth on foot
#   leave   east along the same line to x 6700 (70 m in 8.48 s: F07's own drive away, unscaled; 'leave' reaches
#           600 farther because the lane is tested that far beyond the last key). It crosses the rest of the slab
#           with its passengers and the east level bound 21 - 27 m after the stop (the stock form: BOUND_AFTER)
#   cam     None = kl_map_escape.cam_spot's eye (GUESS: behind the standing van, over the pavement)
# GUESS: the side it comes from, the stop, both lengths. MEASURED on a bare graft (C:/kl_scratch/club/l3/s/drawn.py:
# every drawn model of the map rastered from above): the pavement 'SO0100_M05_Street_Wide_A_03 / B_04 .. B_01 / B_05 /
# A_01' is drawn at y 30.0 under every 20-unit cell of z -3460..-2580 from x -7200 to 7600, and nothing is drawn
# 25..220 over it between z -3280 and -2880 (street lamps and two bins stand at z -3300..-3400, the house fronts at
# z -2620, four parked cars beyond the kerb). West of x -400 the fronts are modelled buildings; east of x 2100 the
# street's north side is a glow plane ('UNIQUE_StreetGLOW'): the van COMES along the real fronts and LEAVES into the
# faked distance. check() measures the same along the drive of the written level (drawn_lane).
ROAD = dict(arrive=[(-5300, 30, -3100), (-2800, 30, -3100)], stop=(-300, 30, -3100), leave=[(3000, 30, -3100), (7300, 30, -3100)],
            at='origin', heading=None, cam=None)
PLAN = None                             # the plan of ROAD (lay_van): prepare_host() and wire() lay the van on it
NO_PLAN = ('kl_fa_club: the van has no plan: build with \'kl_fa_club.py test <out>\' or kl_fa_club.build() (the plan is made on a bare graft and '
           'kl_map_escape.van_layer has to stand round the build; \'kl_maps.py one ... --author kl_fa_club\' can do neither)')
# THE ROAD WHERE THERE IS NO FLOOR. Outside the slab the level has no collision floor (re/campaign_fa_club.md 1.3,
# 8.1 item 8), and kl_map_escape's planner and van_check hold every key of a drive against 'the ground under it':
# as it stands the tool refuses any road that leaves the slab ('only -340 of clear lane before the stop',
# C:/kl_scratch/club/l3/out/plan0.txt), and the slab is 30 m long where the least drive is 20 + 30 m. A key-framed
# van needs no floor (Retomoto's first drove 40 UNDER its road: re/retomoto_fa.md 9.3); what it must do is LOOK
# right, and the pavement it is seen on is drawn at one height. So the road's height is DECLARED: PAVEMENT is the
# drawn pavement (x, z, y), and Pavement / pavement() give kl_map_escape's Ground that floor wherever the collision
# has none within the tool's own tolerance of it. Everything else of the tool's tests is the tool's: collision in
# the van's body, convex bodies, the lengths, the bounds, the boxes at the stop, the camera, the collision file.
PAVEMENT = ((-7200.0, 7600.0), (-3460.0, -2580.0), SLAB[2])
BOARD_NEAR = 30.0                       # the boarding place is a station of the round: on the START's mesh part and on free
                                        # floor within this (the measure of the spawn points)
BOUND_AFTER = 1000.0                    # kl_fa_bank's: a level bound on the drive away at least this far after the stop (every
                                        # stock Dog Days van passes one with its passengers, the nearest 10.9 m after its stop)
MOUTH_SIDE = 150.0                      # the ARRIVING van's nose stops at least this far short of the line straight out of the
                                        # lane's mouth (a criminal who runs out of the door is not in its way). GUESS
BOARD_CLEAR = 500.0                     # no cover point of the arriving police nearer than this to the boarding place (the
                                        # rule of the lane's mouth is 10 m; the slab is 30 x 8.8 m). GUESS
FED_CLEAR = 1000.0                      # no AFTER_DEATH point and no police body nearer than this to the boarding place. GUESS
STREET_ROOM = 'M05_A_Outside_Street_01a'        # the pavement's room: its box holds the whole drive and the camera (check())
ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))
PLACE[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the front office\'s east end, x 2260..2500 - the first criminal through the inner office door')
PLACE[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the walkway\'s upper half, x 700..1300, z 2550..3250')


def set_roles():
    """ROLE holds the fix's five objects (ROLE_NEW) while their flags are on: VAN_LATE -> LATE_ROLES, RESET -> RESET_ROLES. Called at
    the end of the module and by everything that sets a flag."""
    for k, v in ROLE_NEW.items():
        if (k in LATE_ROLES and VAN_LATE) or (k in RESET_ROLES and RESET):
            ROLE[k] = v
        else:
            ROLE.pop(k, None)
    for k, v in WAKE_NEW.items():                       # the wake fix: the objects of the second and third trigger of the staged squads
        if WAKE_MORE:
            ROLE[k] = v
        else:
            ROLE.pop(k, None)


def men_table():
    """MEN, with the four front-office guards on the upper deck (FRONT_MEN) while GUARDS_OFF."""
    if not GUARDS_OFF:
        t = collections.OrderedDict(MEN)
    else:
        t = collections.OrderedDict((k, v) for k, v in MEN.items() if k not in FRONT_MEN)
        t.update(FRONT_MEN)
    if ROOM_GATES:
        t.update(CLEAR_MEN)                     # the five men the room gates move off the crew's way (CLEAR_MEN)
    if ROOM_GATES and PRESSURE:
        t.update(PRESSURE_MEN)                  # ... and the men the pressure fix puts out of the holds' and legs' line of fire (PRESSURE_MEN)
    if HELI and ROOM_GATES:
        t.update(HELI_MEN)                      # ... and, on the way UP, the five men who stand in the corridor itself (HELI_MEN)
    return t


set_roles()

# ------------------------------------------------------------------ VERSION 2: what differs from the round of c_club5 (set_v2)
# The place names of the V2 camera / box objects are the host's (PLACE); V2_PLACE overrides PLACE while V2 is on.
ALARM_BACKSTOP = 200.0                  # s after the round-start event: the alarm whatever a bot counts as (the slowest crew is at the office about 100 s; GUESS)
VAN_SHOW_V2 = 30.0                      # s after EVERY round-start event: the van is shown (the monitor's list runs in round 2 too; the walk box fires once a level, so the alarm alone left round 2 to the
                                        # 200 s backstop - the skeptic's fault). The alarm still lets the police in. GUESS
ALARM_DELAY = 25.0                      # s after the first criminal passes the inner office door (WALK_BOX: the end of the way IN) to the alarm: the gate that lets the
                                        # hunters and F07's police in, the van's show and the exit line. (V1: SEAL_AT from the round start.) GUESS
EXIT_V2 = ((-725, 200, -3175), (425, 250, 275))       # the exit box and the escape-area triggers of V2: the slab's SOUTH-WEST corner (x -1150..-300, z -3450..-2900), so that nobody who starts on the
                                                      # slab starts inside them (START rows z -2740 / -2840, TRAITOR -2790). MEASURED: still on the van's boarding place (-637, -3100)
V2_PLACE = {
    'Gameplay!EscapeSetup!otrExitLevel': (EXIT_V2[0], None, EXIT_V2[1], 'V2: the slab\'s south-west corner round the boarding place (the crew starts on the slab: the box holds no START point and no way into the club)'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((EXIT_V2[0][0], 250, EXIT_V2[0][2]), None, (EXIT_V2[1][0], 300, EXIT_V2[1][2]), 'V2: as the exit box'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((EXIT_V2[0][0], 250, EXIT_V2[0][2]), None, (EXIT_V2[1][0], 300, EXIT_V2[1][2]), 'V2: as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((EXIT_V2[0][0], 250, EXIT_V2[0][2]), None, (EXIT_V2[1][0], 300, EXIT_V2[1][2]), 'V2: as above'),
    # spawn cameras of the criminals' first stage: over the kerb, looking at the START rows. GUESS (none looked through)
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((420, 230, -3330), None, None, 'V2 GUESS: over the kerb, behind the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((380, 90, -2790), None, None, 'V2: the START rows'),
    'Specials!JumpPoints!01_Start': ((380, SLAB[2], -2790), WEST, None, 'V2: the slab, between the START rows'),
}
_PLACE_V1 = {}


def set_v2():
    """Put the tables of the round into place for V2 / V1: START, TRAITOR (in place), SPAWN, the PLACE overrides, the seal (V2: out at build time).
    Called at every place that sets a flag; idempotent."""
    START[:] = START_V2 if V2 else START_V1
    TRAITOR[:] = TRAITOR_V2 if V2 else TRAITOR_V1
    SPAWN.clear()
    SPAWN.update(_spawn(V2))
    for k in V2_PLACE:
        _PLACE_V1.setdefault(k, PLACE[k])
        PLACE[k] = V2_PLACE[k] if V2 else _PLACE_V1[k]
    for k, v in TEXTS_V2.items() if 'TEXTS' in globals() else ():
        _TEXTS_V1.setdefault(k, TEXTS[k])
        TEXTS[k] = v if V2 else _TEXTS_V1[k]


set_v2()


def police():
    """The squads of F07 that arrive in this build."""
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_club.KEEP at the moment of use
        keep = tuple(x for x in _KEEP if not (HELI and x == VAN)) + tuple(v for k, v in ROLE_NEW.items() if k in ROLE) + tuple(v for k, v in WAKE_NEW.items() if k in ROLE) + tuple(police())
        return keep + tuple(x for x in KEEP_MORE if x not in keep)
    raise AttributeError(name)

# F07's cover list goes: M05_A's own top-level 'CoverList' stays through the campaign pre-pass (kl_maps.PASSIVE), and
# a second FFCoverList is an assert in its init (kl2 0x6682c5; kl_fa_author.DROP)
DROP = ('Specials!CoverPoints!*',)

# ------------------------------------------------------------------ the helicopter exit (--exit heli-roof; re/club_campaign.md AA)
# HELI stays False unless main() sets it: every heli change sits behind it, the default build (van-slab) is byte-identical.
# STEP 1 of the two-step chain = the donor: F07 + M06_FA_A's chopper as pseudo level R09 (kl_maps.PSEUDO). F07's own map is dropped
# exactly as in the real build (host_keep + KEEP/DROP, KEEP without the van), M06 gives ONLY the wanted tops. MEASURED (scratch
# prototype, club_heli/donor1.py): the chopper tops alone verify 0 problems; without the two effects zips 6 dangling refs, without the
# CarExplotion tops 8 unresolved clone paths. The four EscCameraSetup! tops are new here (the camera of the way out; GUESS that they are needed).
HELI = False
HELI_DONOR = 'M06_FA_A'
HELI_GROUP = 'EscapeSetup!EscapeChopper\\Escape_Chopper'   # MEASURED in R09: ZGROUP with OnlineEscHavokCar + OnlineEscVehicleController + VehicleEffects
HELI_WANT = ('EscapeSetup!EscapeChopper', 'EscapeSetup!ForceNoLoop', 'EscapeSetup!HeliNetSync',
             'CloneGroup_ROOT/EscapeSetup/EscapeChopper/Escape_Chopper/Shards_Group_A',
             'Triggers!BoardingTrigger_Heli', 'Triggers!BoardingGameplayTrigger', 'PIP_Points!Boarding',
             'EscCameraSetup!EscCameraLAST', 'EscCameraSetup!EscCamera01', 'EscCameraSetup!CameraTrigger01', 'EscCameraSetup!CamPos01',
             'Effects/Hind_Dammage_01.zip', 'Locations/M06_FA_A/M06FAA_Effects.zip',
             'CloneGroup_Effects/AllocMany/All_level/CarExplotion_AllocMany_01.zip/Car_Explotion_01',
             'CloneGroup_Effects/AllocMany/All_level/CarExplotion_AllocMany_01.zip/Car_Explotion_01/Particle_Group_ALL',
             'CloneGroup_ROOT/CloneGroup_Effects/AllocMany/All_level/CarExplotion_AllocMany_01.zip/Car_Explotion_01/Car_Explotion_01/Particle_Group_ALL')


# What a donor with no author layer cannot be free of (MEASURED 2026-10-17, 14 of them, d2.log): F07's kept RunToEscape gate path -> a Timer, the
# TriggerBox[17] of the host's squads (dropped with the map; wire() rewrites them in the real build), the exit trigger's three vans (VAN is not kept in
# heli mode; prepare_host's exit-trigger edit), and the loot check (the host's money is dropped; the club's author lays the loot).
HELI_DONOR_EXPECTED = (r'ROOT\Gameplay!RunToEscape!Timer', r'ROOT\Gameplay!010_FirstFight!RivalMercs!', 'FA: CRASH    exit-trigger', 'FA: BROKEN   money')


def heli_donor(out, log=print):
    """STEP 1 of the heli chain: F07 + the chopper of M06_FA_A -> <out>/chain/F07+M06_FA_A as level R09 (kept), PSEUDO['R09'] set.
    -> kl_maps.one's result dict (ok, problems ...). Offline; the step-2 build (HOST='R09') is not here."""
    global HELI
    import kl_graft, kl_maps, kl_hvk_donor
    want = {n.lower() for n in HELI_WANT}
    real_sel, real_heli = kl_graft.Select, HELI
    HELI = True                             # KEEP without the van
    try:
        keep, drop = tuple(sys.modules[__name__].KEEP), tuple(DROP)   # KEEP is a module __getattr__
        class Donor(real_sel):              # kl_graft.build rebuilds its Select by the name kl_graft.Select: it must be this one
            def __init__(self, geometry=False, m_add=(), m_drop=(), s_keep=(), s_drop=()):
                super().__init__(geometry, m_add, m_drop, tuple(s_keep) + tuple(x for x in keep if x not in s_keep), tuple(s_drop) + drop)
            def m(self, name):              # M06: the wanted tops only (exact names)
                return name.lower() in want
        kl_graft.Select = Donor
        mid = os.path.join(out, 'chain')
        with kl_hvk_donor.patched():
            r = kl_maps.one(mid, HOST_BASE, HELI_DONOR, keep=True, campaign=False, slot='R09')
    finally:
        kl_graft.Select, HELI = real_sel, real_heli
    if r.get('ok'):                         # F07's kept Gameplay objects still name what the real build's wire() / prepare_host replace (step 2)
        left = [x for x in r.get('problems', []) if not any(k in x for k in HELI_DONOR_EXPECTED)]
        r = dict(r, problems_expected=len(r.get('problems', [])) - len(left), problems=left)
        kl_maps.PSEUDO['R09'] = os.path.join(mid, '%s+%s' % (HOST_BASE, HELI_DONOR))
        log('heli donor: R09 = %s+%s, %s entities, %s MB, problems %s' % (HOST_BASE, HELI_DONOR, r.get('entities'), r.get('archive_mb'), r.get('problems')))
    else:
        log('heli donor FAILED: %s %s' % (r.get('error'), r.get('where')))
    return r


# STEP 3: the chopper on the roof pad (re/club_campaign.md AA, step 3). The chopper's nodes are laid on the club's low-roof pad by ONE rigid
# motion (a turn about y + a shift) of M06's world: the landing point (the last point of the 'Incomming' spline, which is the chopper's hub
# when it stands) goes to HELI_PAD, the final approach is turned to HELI_APPROACH, everything is lifted by HELI_PAD y - HELI_GROUND_OLD. The two
# splines are NOT rewritten: their points are local to their node, so moving and turning the node re-frames them exactly (MEASURED: the
# node's local landing point maps to (-1535, 368, -6276) in M06's world, 275 from the stock boarding box at (-1686, 133, -6541)).
HELI_PAD = (-2900.0, 859.0, 3900.0)         # centre of the low-roof pad (x -3600..-2200, z 3500..4300, y 859: re/club_campaign.md V.6, measured by an earlier round)
HELI_WALK = ((-3479.0, 3822.0), (-2378.0, 4229.0))   # the roof door and checkpoint 10 (x, z): the way the crew arrives (V.6)
HELI_APPROACH = (HELI_WALK[0][0] - HELI_WALK[1][0], HELI_WALK[0][1] - HELI_WALK[1][1])   # GUESS: the chopper flies in from the east, towards the roof door, over the pad's free air (not checked against the roof's geometry)
HELI_GROUND_OLD = 0.0                       # GUESS: M06's ground at the landing; the stock boarding box (centre y 133, half 200) says 0 +- 70
HELI_CH = 'EscapeSetup!EscapeChopper\\'
HELI_MOVE = (HELI_CH + 'Escape_Chopper', HELI_CH + 'Incomming\\Spline', HELI_CH + 'Escaping\\Spline', HELI_CH + 'CrashSite_Center_01',
             'Triggers!BoardingTrigger_Heli', 'Triggers!BoardingGameplayTrigger', 'PIP_Points!Boarding',
             'EscCameraSetup!CameraTrigger01', 'EscCameraSetup!CamPos01')     # moved with the one motion; EscCamera01 follows CamPos01 (as the van's), OnMap goes to the pad
HELI_ST = {}                                # the motion of the running build (heli_place): 'land', 'c', 's', 'dy', 'refs'
HELI_STORAGE = IN + 'M05_A_Inside_3rd_Storage_01a\\'
HELI_SUNK = [HELI_STORAGE + 'SI0108_M05_Firedoor_03\\D03', HELI_STORAGE + 'SI0108_M05_Firedoor_02\\D03', HELI_STORAGE + 'HeroColi']   # the way up (V.6: REF 21773 / 21775 / 21820 of the stock M05_A); sunk like the office doors
HELI_EXIT = ((HELI_PAD[0], HELI_PAD[1] + 200.0, HELI_PAD[2]), (700.0, 250.0, 500.0))   # the exit box over the whole pad (x -3600..-2200, z 3400..4400). GUESS
HELI_BOT_PARK = (-3250.0, HELI_PAD[1], 3770.0)   # GUESS: where the AI heisters wait: 400 from the landing towards the roof door, on the pad (kl_fa_bots wants it PARK_SIDE from the boarding action)
HELI_PLACE = {
    'Gameplay!EscapeSetup!otrExitLevel': (HELI_EXIT[0], None, HELI_EXIT[1], 'HELI: the pad (the chopper lands in its middle)'),
    'FASpecials!POI!POI_TheEscapeArea': ((HELI_PAD[0], HELI_PAD[1] + ESC_POI_UP, HELI_PAD[2]), None, None, 'HELI: over the pad'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': (HELI_EXIT[0], None, HELI_EXIT[1], 'HELI: the pad'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': (HELI_EXIT[0], None, HELI_EXIT[1], 'HELI: the pad'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': (HELI_EXIT[0], None, HELI_EXIT[1], 'HELI: the pad'),
    'FASpecials!PIP!ExitLootArea': ((-3450.0, 900.0, 3680.0), None, (150.0, 120.0, 150.0), 'HELI: GUESS: the box the crew crosses on the third floor before the roof door (path point (-3554, 860, 3621)); the van round has it behind the entrance door'),
    'Specials!JumpPoints!06_Exit': (HELI_BOT_PARK, SOUTH, None, 'HELI: the pad')}


def bot_opt():
    """kl_fa_bots' options: the van form's, with the AI heisters' waiting place on the pad in heli mode."""
    return dict(BOT_OPT, park=list(HELI_BOT_PARK)) if HELI else BOT_OPT


def _yaw_only(m, name):
    if abs(m[4] - 1.0) > 1e-3 or any(abs(m[i]) > 1e-3 for i in (1, 3, 5, 7)):
        raise ValueError('kl_fa_club: %s is not turned about y only: %s' % (name, m))


def heli_frame(S):
    """The motion (see HELI_PAD) read off the donor's 'Incomming' spline in S -> dict(land, c, s, dy, last): the world landing point, cos / sin of the turn
    in the (x, z) plane, the lift, and the world points of the whole approach (for the report)."""
    sc = S.prp
    k = A.node_of(sc, HELI_CH + 'Incomming\\Spline')
    lab = J.labels('dd', sc.cls(k))
    v = kl_fa.node_values(sc, k)
    m, p = [float(x) for x in v[lab.index('ZGEOM[1]')]], [float(x) for x in v[lab.index('ZGEOM[2]')]]
    _yaw_only(m, sc.path[k])
    blob = next(x for x in v if isinstance(x, (bytes, bytearray)) and bytes(x[:4]) == b'1TPW')
    n = struct.unpack_from('<I', blob, 4)[0]
    pts = [struct.unpack_from('<3f', blob, 12 + 24 * j) for j in range(n)]
    world = lambda q: tuple(p[a] + q[0] * m[6 + a] + q[1] * m[3 + a] + q[2] * m[a] for a in range(3))   # ZGEOM[1] = [Z', Y', X'] images of the local axes (A.rot9)
    w = [world(q) for q in pts]
    land, d = w[-1], (w[-1][0] - w[-2][0], w[-1][2] - w[-2][2])
    al = math.atan2(HELI_APPROACH[1], HELI_APPROACH[0]) - math.atan2(d[1], d[0])
    return dict(land=land, c=math.cos(al), s=math.sin(al), dy=HELI_PAD[1] - HELI_GROUND_OLD, deg=math.degrees(al), world=w)


def heli_to(F, pt):
    """A world point of M06 -> its place in the club."""
    x, z = pt[0] - F['land'][0], pt[2] - F['land'][2]
    return (HELI_PAD[0] + x * F['c'] - z * F['s'], pt[1] + F['dy'], HELI_PAD[2] + x * F['s'] + z * F['c'])


def heli_place(S, log=print):
    """prepare_host, heli mode: lay the chopper's nodes on the pad (HELI_MOVE + EscCamera01 + OnMap) and remember the motion for the .HVK (heli_hvk)."""
    sc = S.prp
    F = heli_frame(S)
    HELI_ST.clear()
    HELI_ST.update(F)
    def geom(name):
        k = A.node_of(sc, name)
        lab = J.labels('dd', sc.cls(k))
        v = kl_fa.node_values(sc, k)
        return k, [float(x) for x in v[lab.index('ZGEOM[1]')]], tuple(float(x) for x in v[lab.index('ZGEOM[2]')])
    c0, e0 = geom('EscCameraSetup!CamPos01')[2], geom('EscCameraSetup!EscCamera01')[2]
    for name in HELI_MOVE:
        k, m, p = geom(name)
        _yaw_only(m, name)
        tz = (m[0] * F['c'] - m[2] * F['s'], m[0] * F['s'] + m[2] * F['c'])      # local +Z of the node, turned
        A.place(S, k, pos=heli_to(F, p), turn=tz)
    cam = heli_to(F, c0)
    A.place(S, 'EscCameraSetup!EscCamera01', pos=tuple(cam[i] + e0[i] - c0[i] for i in range(3)))      # beside CamPos01 as it was (the van's form)
    A.place(S, HELI_CH + 'EscapeChopper_OnMap', pos=HELI_PAD)
    ch = A.node_of(sc, HELI_CH + 'Escape_Chopper')
    HELI_ST['refs'] = sorted({S.ents[j - 1].ref for j in range(ch, sc.end[ch])})
    st = geom(HELI_CH + 'Escape_Chopper')[2]
    log('  kl_fa_club: HELI: %d nodes moved to the pad (turn %.1f degrees about y, lift %g); the chopper\'s start pose is (%d, %d, %d), it lands at (%d, %d, %d); %d .HVK REFs follow' % (
        len(HELI_MOVE) + 2, F['deg'], F['dy'], *st, *heli_to(F, F['land']), len(HELI_ST['refs'])))
    return F


def heli_hvk(hvk, log=print):
    """On the joined kl_hvk.Hvk: the chopper's key-framed placements get the same motion as its node (kl_map_escape.van_hvk's way: a placement that
    stays at M06's place would put the body there). ASSUMPTION as there: the placement is the body's pose at load."""
    import kl_hvk
    F = HELI_ST
    if not F.get('refs'):
        raise ValueError('kl_fa_club: the collision is joined and heli_place has not run')
    mine, n = set(F['refs']), 0
    R = ((F['c'], 0.0, -F['s']), (0.0, 1.0, 0.0), (F['s'], 0.0, F['c']))
    for s in hvk.shapes:
        if s.type == kl_hvk.STATIC:
            continue
        for j, inst in enumerate(s.inst):
            if kl_hvk.ref(inst) not in mine:
                continue
            p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
            q = [x / 100.0 for x in heli_to(F, [100.0 * x for x in p])]
            m2 = [sum(R[i][k] * m[3 * k + b] for k in range(3)) for i in range(3) for b in range(3)]
            s.inst[j] = struct.pack('<3f9f', *q, *m2) + inst[48:]
            n += 1
    log('  kl_fa_club: HELI: .HVK: %d placement(s) of the chopper moved with its node' % n)
    return hvk


@contextlib.contextmanager
def heli_hvk_layer(log=print):
    """Around the step-2 build, INSIDE kl_hvk_donor.patched(): the joined .HVK gets heli_hvk. A build in which the join did not run it is an error."""
    import kl_hvk
    saved, ran = kl_hvk.join, []
    def join(*a, **kw):
        h = heli_hvk(saved(*a, **kw), log)
        ran.append(1)
        return h
    kl_hvk.join = join
    try:
        yield
    finally:
        kl_hvk.join = saved
    if not ran:
        raise ValueError('kl_fa_club: the .HVK join did not run heli_hvk')

# ------------------------------------------------------------------ texts, lines, sound
# The level's own .LOC keys (finish()). The start window is a text key of the level's .LOC (settings fields 12 / 13
# Fragile Alliance, 14 Cops & Robbers, 15 Undercover Cop). Dead Men's own menu has the slots 'TitleDL04' /
# 'BriefingDL04' (stock text: 'Briefing DL04 - Tokyo') for a Tokyo map that never shipped: the title and a briefing
# in the style of its four ('Senator Simmens is in town, delivering his laundered mob money. ...') are written under
# those keys. Nothing in Dog Days reads the two: they are there for the menu page (a later stage).
# GUESS: every wording. The other eight languages get the English text.
START_KEY = 'AllLevels/Interface/Online/GameStart/M05A_%s_Start'
TEXTS = {START_KEY % 'FA': 'Grab the cases and fight your way down through the club. When the front door opens, get out to the street: the van picks you up there.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'Grab the cases and fight your way down through the club. When the front door opens, get out to the street: the van picks you up there.',
         'AllLevels/Menu/Online/Scenarios/TitleDL04': TITLE,
         'AllLevels/Menu/Online/Scenarios/BriefingDL04': 'The Mizuki is the hottest night club in Tokyo, and the owner\'s daughter keeps the takings in her office '
         'above the dance floor. We are already in there with the safe open when her bodyguards catch on. We grab the cases, shoot our way down across '
         'both dance floors and leave through the front entrance, where our getaway van will pick us up on the street.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}
TEXTS_V2 = {START_KEY % 'FA': 'Run into the club and take the cases from the office at the back. Then fight your way out again: the van picks you up on the street.',
            START_KEY % 'UCC': 'Run into the club and take the cases from the office at the back. Then fight your way out again: the van picks you up on the street.',
            'AllLevels/Menu/Online/Scenarios/BriefingDL04': 'The Mizuki is the hottest night club in Tokyo, and the owner\'s daughter keeps the takings in her office '
            'above the dance floor. We hit it from the front: in past the queue, up across both dance floors while the bouncers are still looking at the door, '
            'the cases from her desk - and back out the way we came, to the van that waits on the street.'}
_TEXTS_V1 = {}
set_v2()                                # (again: TEXTS exists now)
# the briefing and reminder lines: stock F07's speak of a data theft. Lines of other stock levels that fit cash in
# the hand and a fight on the way out, all in F07's bank with their eight voices (kl_fa_bank.LINES; re/bots_voice.md
# 6.2). settings field -> line. GUESS: the choice
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R',       # 'Alright! Grab the cash.'
         18: 'Multiplayer/F09/MissionReminder_02_R',     # 'We can do this. Be quick 'cause this is gonna turn nasty!'
         19: 'Multiplayer/F06/MissionReminder_01_R',     # 'Just get the money.'
         20: 'Multiplayer/F06/ReachlootArea_01_R',
         127: 'Multiplayer/F06/ReachlootArea_01_R',
         130: 'Multiplayer/F04/ExitLootArea_01_R',       # 'We got it! Let's keep moving!'
         136: 'Multiplayer/F06/MissionReminder_01_R',
         137: 'Multiplayer/F09/MissionReminder_02_R'}
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'             # 'Get out on the street! straight ahead!' (F07's: '... to the back alley')
# THE MUSIC. The club's two tracks are positional layered streams of the kept audio subtree ('...!STREAMS!Inside!
# Music!Club_01_*' = 'M05_A_Club_Layers', 202.7 s; '...Club_02_*' = 'M05_A_Club_2_Layers', 309.7 s), with boxes that
# muffle them on the stairs and in the office. NOTHING in the level starts them and one dropped campaign object
# stops them ('Specials!KillMusic'): ASSUMPTION that they play from the load. What this file wires is the muffle
# switch of the office doors (MUFFLE). They are SILENT until the stream file holds their clips - for the stage that
# extends PC_Def.str (check() reads the built .WHD and says which of these have no record):
# the seven layers the level's objects NAME. Each track is one interleaved set of FOUR layers in Dead Men's stream
# file; the second set's fourth, 'M05_A_Club_2_Muffled_3D.wav', is named by no object - the extension must bring the
# two whole sets all the same ('LevelSetup/Level/M05_A/Music/M05_A_Club_Layers' 32.4 MB, '..._Club_2_Layers' 49.5 MB)
MUSIC_CLIPS = tuple('Music/InHouse/Japan/M05_A/M05_A_Club_%s.wav' % n for n in ('Clean', 'Clean_3D', 'Muffled', 'Muffled_3D',
                                                                               '2_Clean', '2_Clean_3D', '2_Muffled'))
AMBIENCE_CLIPS = ('SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav', 'SFX/Ambiences/M05_A/Inside/M05_Club_Ambience_01.wav',
                  'SFX/Ambiences/M05_A/Inside/Yoko_Office_Ambience.wav', 'SFX/Ambiences/M05_A/Outside/Roftop/Ambience_Rooftop_M05_A.wav',
                  'SFX/Ambiences/M05_A/Outside/Street/Street_01.wav')


# ------------------------------------------------------------------ 1. the host level before the graft
_Ground = ESC.Ground                    # kl_map_escape's own, whatever pavement() has put in its place


class Pavement(_Ground):
    """kl_map_escape.Ground of this level WITH THE DRAWN PAVEMENT AS A FLOOR where the collision has none (PAVEMENT's
    note): a vertical line inside PAVEMENT that meets no collision floor within the tool's tolerance of the
    pavement's height (VAN_BODY[0] = 25) meets one more 'floor' at that height, owned by the REF id DRAWN, which no
    entity has (kl_map_escape.Level.name says 'REF -5'). Nothing else changes: the slab's own floor answers where
    it is, collision over the road is collision, `between` (lines of sight) sees only what is really there."""
    DRAWN = -5

    def hits(self, x, z):
        out = _Ground.hits(self, x, z)
        (x0, x1), (z0, z1), y = PAVEMENT
        if x0 <= x <= x1 and z0 <= z <= z1 and not any(h[1] > ESC.FLOOR and abs(h[0] - y) <= ESC.VAN_BODY[0] for h in out):
            out = sorted(out + [(y, 1.0, self.DRAWN)])
        return out


@contextlib.contextmanager
def pavement():
    """For its length kl_map_escape makes its Ground as a Pavement (van_plan_points, van_check)."""
    ESC.Ground = Pavement
    try:
        yield
    finally:
        ESC.Ground = _Ground


def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points, on the drawn pavement) against the collision of a BUILT
    F07 + M05_A folder WITHOUT the layer (a bare 'kl_maps.py one <out> F07 M05_A --campaign --m-drop "Boundaries!*"
    --keep': on a build that has the van, the planner takes the van's own camera for a designer's and lists it to
    be left out). A fault of the plan is an error."""
    with pavement():
        P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_club: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
    """A plan from a file: the van.json test() writes beside a build (the plan is its 'plan'), or a plan as JSON."""
    import json
    with open(path, encoding='utf-8') as f:
        P = json.load(f, object_pairs_hook=collections.OrderedDict)
    P = P.get('plan', P)
    lack = [k for k in ('path', 'lin', 'lout', 'wait', 'stop', 'end', 'board', 'cam', 'points') if k not in P]
    if lack or P.get('faults'):
        raise ValueError('%s is no plan of the van without a fault (lacks %s; faults %s)' % (path, lack, P.get('faults')))
    road = {k: [list(map(float, p)) for p in v] if k in ('arrive', 'leave') else list(map(float, v)) if k == 'stop' else v for k, v in ROAD.items()}
    if any(P['points'].get(k) != v for k, v in road.items()):
        raise ValueError('%s is a plan of other way points than ROAD: %s' % (path, {k: P['points'].get(k) for k in road if P['points'].get(k) != road[k]}))
    return P


def lay_van(P):
    """The plan the next build lays the van on (prepare_host, wire). -> P."""
    global PLAN
    PLAN = P
    return P


def van_path():
    if HELI:                            # the group of the chopper that carries OnlineEscVehicleController (GUESS: what the exit trigger and the show/hide lists name)
        return R + HELI_GROUP
    return R + VAN + '\\' + VAN_GROUP


def place_police(S, log=print):
    """F07's police squads of ARRIVE onto the pavement (kl_fa_bank.place_hall's way, with this file's table): the
    group to its anchor, every child that has a place of its own (a non-zero local translation under parents that
    have none: the men's groups, the points of the routs) to its place, as an offset from the anchor.
    -> [(squad, men)]"""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    y3 = lambda p: (float(p[0]), ARRIVE_Y, float(p[1]))
    for name, (anchor, men, cover, defend) in police().items():
        top = A.node_of(sc, name)
        turned = max(abs(a - b) for a, b in zip(struct.unpack('<9f', S.ents[top - 1].rot[:36]), A.rot9((0.0, 1.0))))
        if not kl_fa.has(sc, top, 'ZSquadScript') or turned > 1e-3 or not sc.resolve(R + name + '\\' + ARRIVE_START):
            raise ValueError('%s: not a squad group without a turn that has a %s' % (name, ARRIVE_START))
        own = []
        def go(k):
            for c in range(k + 1, sc.end[k]):
                if sc.parent[c] == k:
                    own.append(c) if any(abs(v) > 0.5 for v in tr(c)) else go(c)
        go(top)
        by = collections.defaultdict(list)
        for k in own:
            by['men' if any(sc.cls(c) == 'ZFFActor' for c in range(k, sc.end[k])) else sc.names[sc.parent[k]]].append(k)
        at = y3(anchor)
        e_men, e_cover, e_defend = ARRIVE_EAST[name] if POLICE_EAST and POLICE_ON_SLAB else (None, None, None)
        want = {'men': [y3(p) for p in (e_men or (ARRIVE_SLAB[name] if POLICE_ON_SLAB else men))], ARRIVE_START: [y3(p) for p in (e_cover or cover)],
                '10_Defend': [y3(e_defend or defend)], '40_RunToEscape': [at]}      # (nothing names the last two: kl_fa_bank.HALL's note)
        if {k: len(v) for k, v in by.items()} != {k: len(v) for k, v in want.items()}:
            raise ValueError('%s: placed children %s, the table has %s' % (name, {k: len(v) for k, v in by.items()}, {k: len(v) for k, v in want.items()}))
        A.place(S, top, at)
        for kind, ks in by.items():
            for k, p in zip(ks, want[kind]):
                A.place(S, k, tuple(p[a] - at[a] for a in range(3)))
        out.append((name, len(by['men'])))
    if out:
        log('  kl_fa_club: the police that arrive: %d of F07\'s squads re-placed (%d men) %s; the gate names their %s' % (
            len(out), sum(n for _s, n in out), 'ON THE SLAB\'s two ends (POLICE_ON_SLAB)' if POLICE_ON_SLAB
            else 'on the pavement\'s mesh strip beyond the slab\'s two ends, out of sight', ARRIVE_START))
    return out


_plan = {}

def squad_plan():
    """The campaign's squads that stay -> ({squad: (path of the child that starts it or None, actors, kinds that are
    stripped, the kind that starts it)}, {squad that is left: why}). The rule (SQUADS' note), asked of the stock
    Dead Men level: only plain squad kinds and what STRIP takes off, a ZSoldier for every actor, and the start child
    holds a behaviour rout or a SquadModifierBehaviour."""
    if NO_AI:
        return {}, {'*': 'a build without enemies (NO_AI)'}
    if 'plan' not in _plan:
        sc = J.Scene.load(LEVEL, 'dm')
        keep, left = {}, {}
        for t in sc.tops():
            name = sc.names[t]
            ctrl = collections.Counter(sc.p.key(nm) for k in range(t, sc.end[t]) for nm, _b in sc.nodes[k]['ctrls'])
            if not ctrl['ZSquadScript']:
                continue
            if name not in SQUADS:
                left[name] = 'not a squad of this round'
                continue
            stage, child = squads_now()[name]
            actors = sum(sc.cls(k) == 'ZFFActor' for k in range(t, sc.end[t]))
            odd = sorted(set(ctrl) - A.PLAIN - STRIP)
            if odd or not actors or ctrl['ZSoldier'] != actors:
                raise ValueError('kl_fa_club: %s cannot stay: it holds %s, %d actors, %d ZSoldier' % (name, odd or 'plain kinds', actors, ctrl['ZSoldier']))
            start, kind = None, None
            if child:
                ks = sc.resolve(R + name + '\\' + child)
                kinds = {sc.p.key(nm) for k in ks for nm, _b in sc.nodes[k]['ctrls']}
                kind = next(iter(sorted(kinds & A.BEHAVE)), 'SquadModifierBehaviour' if 'SquadModifierBehaviour' in kinds else None)
                if len(ks) != 1 or kind is None:
                    raise ValueError('kl_fa_club: %s\\%s: %d nodes holding %s - neither a behaviour rout nor a squad modifier' % (name, child, len(ks), sorted(kinds)))
                start = R + name + '\\' + child
            keep[name] = (start, actors, sorted(set(ctrl) & STRIP), kind)
        if set(keep) != set(SQUADS):
            raise ValueError('kl_fa_club: squads of SQUADS that are not in %s: %s' % (LEVEL, sorted(set(SQUADS) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the club. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    if not BEAT_ANIM and kl_gms.RETYPE.get(IK[1][0]) != IK[1][1]:      # before anything is armed: a caller that goes on in
        raise ValueError(NO_BUILD)                                     # this process must not find kl_escape wrapped
    if PLAN is None and not HELI:
        raise ValueError(NO_PLAN)
    Doors.arm(log)                                      # the build that follows opens the doors (see Doors)
    for name, (pos, face, half, _why) in place_now().items():
        put(S, name, pos, face, half)
    for name in PARKED:
        put(S, name, PARK)
    # spawn points by kind, and the sixteen player groups (a direct boot starts at Heroes!Hero_01)
    seen = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kind = kl_fa.node_values(sc, t)[8]
            if kind not in SPAWN:
                raise KeyError('%s: no place for spawn points of kind %s' % (sc.names[t], kind))
            pts, d, face = SPAWN[kind]
            p = pts[seen[kind] % len(pts)]
            p = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            A.place(S, t, p, turn=facing(p, face))      # a spawn point looks along local +Z (kl_fa_author: SEEN LIVE)
            seen[kind] += 1
        elif sc.names[t].startswith('Heroes!'):
            crook = sc.names[t].startswith('Heroes!Hero_0')
            pts, face = (START, SPAWN['eSPAWN_TYPE_FRAGILE_ALLIANCE_START'][2]) if crook else (BODIES, LANE_MOUTH)
            p = pts[seen[crook, 'hero'] % len(pts)]
            A.place(S, t, p, facing(p, face))           # ... a player group along local -Z
            seen[crook, 'hero'] += 1
    log('  kl_fa_club: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: stacks of F07's drop pools become loot that lies in the map (kl_fa_author's way, the values of stock
    # F02's money bags). Taken: the last 8 of the 108 of every mode (leaves 100, as six stock levels have) and the
    # last of the team-mode 25. finish() gives them the briefcase model on the written level.
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    take = (sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-8:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[8 - len(LOOT):])[:len(LOOT)]
    if len(take) != len(LOOT) or len(LOOT) < 8:
        raise ValueError('%d pool stacks for %d loot places' % (len(take), len(LOOT)))
    loot = []
    for (name, k, i), (p, _yaw, value, _what) in zip(take, LOOT):
        def fn(us):
            for j, v in enumerate(('ZMONEYCTRL_GAMEMODE_ALL', value, 'ZMONEYCTRL_TYPE_NORMAL', 'ZMONEYCTRL_VARIANT_NORMAL', 15000, 0.2, 1, 30.0, 800.0, 1000.0, 0, 0)):
                A.setv(sc, us, j, v)
        kl_fa.edit(sc, k, i, fn)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'TriggerBox2'), lambda us: A.setv(sc, us, 2, LOOT_REACH))
        A.place(S, k, p, hidden=False)
        loot.append(name)
    by = collections.Counter(what for _p, _y, _v, what in LOOT)
    log('  kl_fa_club: loot: %d objects, %d in all, shown from the load: %s' % (len(LOOT), sum(v for _p, _y, v, _w in LOOT), ', '.join('%d on %s' % (n, w) for w, n in by.items())))
    place_police(S, log)
    # escape: the one van laid on the plan of ROAD - F07's own keys re-written in place, the boxes beside its drive
    # and its camera moved with it (kl_map_escape.van_prepare; the van's nodes must still stand where F07 has them);
    # the exit trigger names it alone (kl2 0x6c3f90 loops until one field is set). The escape marker stays where
    # PLACE has it, beside the lane: held against this plan's drive here (check() does it again on the written level)
    S.van = None if HELI else ESC.van_prepare(S, PLAN, log)     # HELI: no van; the chopper is laid on the pad by heli_place
    if HELI:
        heli_place(S, log)
    if VAN_LATE:
        # THE OWNER, about the Vault's police: 'they shoot the van straight away'; run C2: the van went from waiting to state 6 (destroyed)
        # with two heisters aboard. The van is NOT in the world until the crew is close (wire(): the seal opening / the wardrobe's box show
        # it) and carries nothing a policeman aims at (its FakeTarget, faction 'Mercenary', the level's only one). ASSUMPTIONS: police aim
        # at a van because of that target (kl_fa_bank's, unproven); a hidden keyed vehicle runs its keys unseen and boards normally once shown
        vg = A.node_of(sc, van_path()[len(R):])
        gone = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
        for k in gone:
            sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
        A.place(S, vg, hidden=True)
        log('  kl_fa_club: VAN_LATE: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; %s shows it' % (
            len(gone), 'the seal\'s opening (+%g s) and the wardrobe\'s box (+%g s)' % (VAN_AFTER, VAN_EARLY)))
    if not HELI:                                        # (HELI: no van, no drive to keep the marker clear of)
        off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(ESC_AT)[1])
        if off < LANE_CLEAR:
            raise ValueError('kl_fa_club: the escape marker\'s place %s is %d from the van\'s drive (%d wanted)' % (ESC_AT, off, LANE_CLEAR))
        log('  kl_fa_club: the escape marker stands %d from the van\'s drive, %d from the boarding place at the stop' % (off, math.dist(ESC_AT, PLAN['board'])))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M05_A the campaign pre-pass must leave in: the three kill boxes (KILL) and the squads
    that stay (squad_plan). No door object is among them - every leaf takes 'Activate' itself, and the campaign's
    DoorCtrl is a kind no stock Dog Days level runs."""
    if level != LEVEL:
        return ()
    return tuple(KILL) + tuple(squad_plan()[0])


def take_off(sc, kind, want, log):
    """The controllers of `kind` off every node of the converted level -> how many; `want` must be there."""
    hit = [k for k, _i, _v in kl_fa.controllers(sc, kind)]
    if len(hit) != want:
        raise ValueError('kl_fa_club: %d %s in %s, %d expected' % (len(hit), kind, LEVEL, want))
    for k in set(hit):
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != kind]
    return len(hit)


def strip_squads(M, log=print):
    """The kept squads on the converted level: STRIP's kinds off (a node that loses an AttachGeomToBone is a prop:
    hidden with its group), the men of MEN to their places, every other man who stands beside the navigation mesh
    onto it (kl_fa_bank.snap_men's way: the campaign has a few at a wall's or a counter's foot). -> controllers
    taken off"""
    import kl_route
    keep = squad_plan()[0]
    if not keep:
        log('  kl_fa_club: %s: no squad stays (NO_AI)' % M.name)
        return 0
    sc, n, props = M.prp, collections.Counter(), 0
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            nd = sc.nodes[k]
            gone = [sc.p.key(c[0]) for c in nd['ctrls'] if sc.p.key(c[0]) in STRIP]
            if gone:
                nd['ctrls'] = [c for c in nd['ctrls'] if sc.p.key(c[0]) not in STRIP]
                n.update(gone)
                if 'AttachGeomToBone' in gone:          # the prop and the group it hangs in
                    A.place(M, k, hidden=True)
                    A.place(M, sc.parent[k], hidden=True)
                    props += 1
    mesh = kl_route.load(LEVEL).mesh()
    placed = []
    for path, hint in men_table().items():
        g = A.node_of(sc, path)
        if sc.names[sc.top[g]] not in keep or not any(sc.cls(c) == 'ZFFActor' and sc.parent[c] == g for c in range(g, sc.end[g])):
            raise ValueError('kl_fa_club: MEN: %s is not a man\'s group of a kept squad' % path)
        hit = mesh.on(*[float(v) for v in hint])
        if hit is None:
            raise ValueError('kl_fa_club: MEN: %s: (%d, %d, %d) is not on the navigation mesh' % (path, *hint))
        was = world_of(M.ents[g - 1])[0]
        BK.man_to(M, g, (float(hint[0]), hit[1], float(hint[2])), mesh)
        placed.append((path, was))
    moved = []
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            if sc.cls(k) != 'ZFFActor':
                continue
            g = sc.parent[k]                            # the man's group holds his place; 'Ground' sits at its origin
            w = world_of(M.ents[g - 1])[0]
            if mesh.on(*w) is not None:
                continue
            d, i = mesh.nearest(*w)
            if i is None or d > MAN_OFF:
                raise ValueError('%s stands %s off the navigation mesh at (%d, %d, %d): give him a place in MEN' % (sc.path[k], d, *w))
            mid = mesh.mid[i]
            for step in range(1, 201):
                x, z = w[0] + (mid[0] - w[0]) * step / 200.0, w[2] + (mid[2] - w[2]) * step / 200.0
                if mesh.inside(i, x, z) and math.hypot(x - w[0], z - w[2]) >= d + MAN_IN:
                    break
            new = (x, mesh.height(i, x, z), z)
            BK.man_to(M, g, new, mesh)
            moved.append((sc.path[g][5:], round(d), math.dist(w, new)))
    log('  kl_fa_club: %s: %d squads stay (%d men); taken off them: %s; %d props hidden' % (
        M.name, len(keep), sum(a for _s, a, _k, _w in keep.values()), dict(n) or 'nothing', props))
    log('  kl_fa_club: %d men re-placed (MEN): %s' % (len(placed), ', '.join('%s from (%d, %d, %d)' % (p.split('!')[-1], *w) for p, w in placed)))
    log('  kl_fa_club: %d men stood beside the navigation mesh and were put on it: %s' % (
        len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    return sum(n.values())


def strip(M, log=print):
    """On the converted Dead Men level, before the join (nothing goes by controller index yet): the three kill boxes
    to their places under the slab's edges, and what never ran in Dog Days by this file's three flags (LIGHT_SHOW,
    BEAT_ANIM, FAN_DAMAGE). The door leaves and the seal are map nodes that stay as they are (they are sunk on the
    JOINED scene: Doors)."""
    if M.name != LEVEL:
        return 0
    sc, n = M.prp, 0
    for name, (pos, half, _why) in KILL.items():
        k = A.node_of(sc, name)
        if sc.cls(k) != 'ZBoxPrimitive' or not kl_fa.has(sc, k, 'KillBox') or sc.end[k] - k != 1:
            raise ValueError('%s is not a single box with a KillBox' % name)
        put(M, k, pos, None, half)                      # laid in the world's axes ('#02' is a turned box in the campaign)
    log('  kl_fa_club: %s: %d kill boxes of the campaign re-placed under the slab\'s three open edges (tops y %d)' % (
        M.name, len(KILL), max(p[1] + h[1] for p, h, _w in KILL.values())))
    have = sum(1 for p, _at, _set in LEAVES + SEAL if sc.resolve(R + p))
    log('  kl_fa_club: %s: %d of %d door and seal nodes of the route found' % (M.name, have, len(LEAVES) + len(SEAL)))
    n += strip_squads(M, log)
    # ---- the light show
    if LIGHT_SHOW:
        if len(kl_fa.controllers(sc, 'PositionLightControl')) != NEVER_RAN['PositionLightControl']:
            raise ValueError('kl_fa_club: the light show has not its %d PositionLightControl' % NEVER_RAN['PositionLightControl'])
    else:
        n += take_off(sc, 'PositionLightControl', NEVER_RAN['PositionLightControl'], log)
    # ---- the beat objects
    beat = [A.node_of(sc, p) for p in BEAT]
    plain = [sc.cls(k) for k in beat]
    if BEAT_ANIM:
        if plain != ['ZIKLNKOBJ'] * 2 or len(kl_fa.controllers(sc, 'StartAnim')) != NEVER_RAN['StartAnim']:
            raise ValueError('kl_fa_club: BEAT_ANIM, but the two beat objects are %s (built with the retype?)' % plain)
    else:
        if plain != ['ZSTDOBJ'] * 2:
            raise ValueError('kl_fa_club: the two beat objects are %s, not loaded as ZSTDOBJ: %s' % (plain, NO_BUILD))
        # (the converter has taken the StartAnim off already: on a ZSTDOBJ it is no controller Dog Days registers)
        n += take_off(sc, 'StartAnim', len(kl_fa.controllers(sc, 'StartAnim')) and NEVER_RAN['StartAnim'], log)
        for k in beat:                                  # an empty helper object: no model, not in the picture
            lab = J.labels('dd', sc.cls(k))
            kl_graft.edit(sc.nodes[k], 'props', lambda us, lab=lab: A.setv(sc, us, lab.index('ZGEOM[4]'), 0))
            M.ents[k - 1].model = 0
            A.place(M, k, hidden=True)
    # ---- the roof fans
    if FAN_DAMAGE:
        if len(kl_fa.controllers(sc, 'ShotActivateDamage')) != NEVER_RAN['ShotActivateDamage']:
            raise ValueError('kl_fa_club: the roof fans have not their %d ShotActivateDamage' % NEVER_RAN['ShotActivateDamage'])
    else:
        n += take_off(sc, 'ShotActivateDamage', NEVER_RAN['ShotActivateDamage'], log)
    log('  kl_fa_club: what never ran in Dog Days: the light show\'s %d PositionLightControl %s; the 2 beat objects %s; the roof fans\' %d ShotActivateDamage %s' % (
        NEVER_RAN['PositionLightControl'], 'STAY (LIGHT_SHOW)' if LIGHT_SHOW else 'taken off (the lights are static)',
        'stay ZIKLNKOBJ with their StartAnim (BEAT_ANIM)' if BEAT_ANIM else 'are plain ZSTDOBJ without StartAnim and model, hidden',
        NEVER_RAN['ShotActivateDamage'], 'STAY (FAN_DAMAGE)' if FAN_DAMAGE else 'taken off (the fans cannot be shot to pieces)'))
    return n


# ------------------------------------------------------------------ 3. the joined scene
def gate():
    """Paths (below ROOT) of the seal's pieces that STAND in this build and are switched off by the beat."""
    return [] if SEAL_OPEN else [p for p, _at, _set in SEAL if SEAL_PLANE or not p.endswith('\\Plane01')]


def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene
    (kl_prpjoin.Scene). Values and reference lists of existing controllers only."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_club: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    left = [sc.names[t] for t in sc.tops() if sc.names[t].startswith('Boundaries!')]
    if left:                                            # the campaign's own bounds stand on the route (M_DROP)
        raise ValueError('kl_fa_club: %d of the campaign\'s Boundaries! objects are in the build: %s' % (len(left), NO_BUILD))
    leaves = must([R + p for p, _at, _set in LEAVES])
    must([R + p for p, _at, _set in SEAL])
    seal = must([R + p for p in gate()])
    for p in leaves:                                    # each takes 'Activate' itself
        msg = [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == sc.resolve(p)[0]]
        if msg != ['Activate']:
            raise ValueError('%s: MatPosAnim in-message %s, not one \'Activate\'' % (p, msg))
    muffle = must([R + p for p in MUFFLE])
    for p in muffle:
        v = values(sc, sc.resolve(p)[0], 'ActivateGeom')
        if v[0] != MUFFLE_MESSAGE or len(v[1]) != 1 or not sc.resolve(v[1][0]):
            raise ValueError('%s: not an ActivateGeom on \'%s\' with one box: %s' % (p, MUFFLE_MESSAGE, v))

    # ---- the enemies: each squad's stage, what is in the world from the load, the rows
    plan = squad_plan()[0]
    stage, quiet = collections.defaultdict(list), 0
    for n, (first, _actors, _strip, kind) in plan.items():
        k = node(n)
        st = squads_now()[n][0]
        if values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] not in (0, 1):
            raise ValueError('%s: ZSquadScript field %d is %r' % (n, SQUAD_ACTIVE, values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE]))
        put_(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 1 if st == 'load' or SQUADS_AWAKE else 0})
        if first:
            j = sc.resolve(must([first])[0])[0]
            stage[st].append(first)
            if kind == 'SquadModifierBehaviour':        # the child that starts the squad says so (STAGED)
                if values(sc, j, kind)[MOD_ACTIVE] not in ('eAM_NotSet', STAGED):
                    raise ValueError('%s: SquadModifierBehaviour field %d is %r' % (first, MOD_ACTIVE, values(sc, j, kind)[MOD_ACTIVE]))
                put_(j, kind, **{'f%d' % MOD_ACTIVE: STAGED})
        # a message list inside the squad names only what still holds a controller (MESSAGE_KINDS)
        for j in range(k, sc.end[k]):
            for kind_ in [sc.p.key(nm) for nm, _b in sc.nodes[j]['ctrls'] if sc.p.key(nm) in MESSAGE_KINDS]:
                for f, x in enumerate(values(sc, j, kind_)):
                    if isinstance(x, list) and x and isinstance(x[0], str):
                        live = [s for s in x if not any(sc.top[h] == k and not sc.nodes[h]['ctrls'] for h in sc.resolve(s))]
                        if len(live) != len(x):
                            put_(j, kind_, **{'f%d' % f: live})
                            quiet += len(x) - len(live)
    beat = [n for n in BEAT_SQUADS if n in plan]
    for n in beat:                                      # the beat's fast way: 'wiped out' -> the counter of two
        put_(node(n), 'ZSquadScript', **{'f%d' % SQUAD_DEAD: [R + ROLE['floors counter']]})
    arrive = must([R + n + '\\' + ARRIVE_START for n in police()])
    armed = BK.soldier_rows(sc, plan, log) if STOCK_ROWS and plan else {}
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    enemies_in = stage['open'] + arrive                 # what the gate lets in, once
    for w in ways:
        put_(sc.resolve(w)[0], 'GatePath', f0=enemies_in)
    lists('office timer', 'TriggerDelay2', f0=OFFICE_AT, f4=stage['office'])
    # TriggerBox field 0 = 1 (in use from the load: F07 switches these two on by a timer), field 15 = 0 (fires once,
    # not for every criminal: kl_fa_bank.BOX_PER_MAN, the census of review round 1), criminals only
    # V2: the first criminal through the inner office door is the END of the way in: the alarm. The box also starts 'van timer b' (ALARM_DELAY: the gate that lets the hunters and the
    # police in, the van's show, the exit line), and the clock of the round start ('seal timer', ALARM_BACKSTOP) does the same whether or not a bot counts as a criminal for the box
    alarm = [R + ROLE['van timer b']] if V2 and VAN_LATE else []
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['walk'] + alarm)
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['floor'])
    wake_timers = []
    if WAKE_MORE:                                       # THE WAKE FIX: the second and third trigger of each wake group (a box on the room's hold area, a backstop timer)
        for room, mods_ in wake_groups(plan).items():
            i = list(WAKE_BOX).index(room)
            lists('wake box %d' % (i + 1), 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=must(mods_))
            lists('wake timer %d' % (i + 1), 'TriggerDelay2', f0=WAKE_BOX[room]['backstop'], f4=mods_)
            wake_timers.append(R + ROLE['wake timer %d' % (i + 1)])
        if len(wake_timers) != len(WAKE_BOX):
            raise ValueError('kl_fa_club: %d wake groups, WAKE_BOX has %d' % (len(wake_timers), len(WAKE_BOX)))
    van_t = [R + ROLE['van timer']] if VAN_LATE and not V2 else []           # VAN_LATE: whichever opens the seal also starts the van's timer
    lists('floors counter', 'TriggerCounter', f0=max(len(beat), 1), f4=([R + ROLE['seal off']] if seal and beat else []) + ([ways[0]] if beat else []) + (van_t if beat else []))

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it. This layer's:
    # the seal's clock, the front office's timer, and the doors' timer (DOORS_ANIMATE) or the music's muffle switch
    # (the doors are open)
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['seal timer']] + ([R + ROLE['office timer']] if stage['office'] else []) + ([R + ROLE['doors timer']] if DOORS_ANIMATE else [] if V2 else [R + ROLE['muffle']]) + wake_timers + ([R + ROLE['van timer']] if V2 and VAN_LATE else [])
    # RESET: two stock objects FIRST in the list put round 2 back as round 1 was at the load (the Vault's reset: re/bank_campaign.md W.5). Show
    # again what the round switched OFF (the seal's pieces), hide again what it switched ON (the late van). Both are no-ops in round 1
    reset = ([R + ROLE['reset show']] if seal else []) + ([R + ROLE['reset hide']] if VAN_LATE else []) if RESET else []
    if RESET:
        if seal:
            lists('reset show', 'ActivateGeom', f0='AITrigger', f1=seal)
        else:
            lists('reset show', 'ActivateGeom', f0='AITrigger', f1=[])
        lists('reset hide', 'DeactivateGeom', f0='AITrigger', f1=[van_path()] if VAN_LATE else [])
    lists('monitor', 'AIMonitor', f2=reset + have + start)
    # ---- the doors (DOORS_ANIMATE): the timer -> 'Activate' to the four leaves, the muffle switch with them
    lists('doors timer', 'TriggerDelay2', f0=DOORS_AT, f4=[R + ROLE['doors'], R + ROLE['muffle']] if DOORS_ANIMATE else [])
    lists('doors', 'AIDWrapper', f0=leaves if DOORS_ANIMATE else [], f1='Activate')
    lists('muffle', 'AIDWrapper', f0=muffle, f1=MUFFLE_MESSAGE)
    if DOORS_ANIMATE:
        for p in leaves:                                # the clip goes there AND back: stop it at its open frame
            put_(sc.resolve(p)[0], 'MatPosAnim', **{'f%d' % MPA_LAST: DOOR_LAST})
        log('  kl_fa_club: DOORS ANIMATE: %d leaves store LAST %d and get \'Activate\' %.1f s after the round-start event' % (len(leaves), DOOR_LAST, DOORS_AT))

    # ---- the beat's guaranteed clock: round start -> SEAL_AT -> the seal's pieces off. The next stage names the
    # same DeactivateGeom from its 'both dance-floor squads dead' counter: whichever comes first opens the lane
    # The fast way is the counter's (above): both name the DeactivateGeom themselves, and each its own path of the
    # gate, which lets the hunters and the police in for whichever comes first
    if V2:
        lists('seal timer', 'TriggerDelay2', f0=ALARM_BACKSTOP, f4=([ways[1]] if enemies_in else []) + van_t + [R + ROLE['speak']])
    else:
        lists('seal timer', 'TriggerDelay2', f0=SEAL_AT, f4=([R + ROLE['seal off']] if seal else []) + ([ways[1]] if enemies_in else []) + van_t)
    lists('seal off', 'DeactivateGeom', f0='AITrigger', f1=seal)

    # ---- the way out: F07's 'exit heist' box in the wardrobe, with a line that fits a front door
    if V2:                                              # the wardrobe's box is passed on the way IN too: it says nothing and shows nothing in V2 (the alarm does); it sends the music's muffle switch (the crew is inside the club's doors)
        lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['muffle']] if not DOORS_ANIMATE else [])
    else:
        lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']] + ([R + ROLE['van timer b']] if VAN_LATE else []))
    if VAN_LATE:                                        # the van is shown VAN_AFTER s after the seal opens / VAN_EARLY s after the wardrobe's box (idempotent)
        lists('van on', 'ActivateGeom', f0='AITrigger', f1=[van_path()])
        lists('van timer', 'TriggerDelay2', f0=VAN_SHOW_V2 if V2 else VAN_AFTER, f4=[R + ROLE['van on']])
        if V2:
            lists('van timer b', 'TriggerDelay2', f0=ALARM_DELAY, f4=[R + ROLE['van on']] + ([ways[1]] if enemies_in else []) + [R + ROLE['speak']])
        else:
            lists('van timer b', 'TriggerDelay2', f0=VAN_EARLY, f4=[R + ROLE['van on']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    # ---- the escape: every exit trigger of the level (there is F07's one) calls the van - field 0 false, field 2
    # the van's group, 1 and 3..5 empty, the form the three car maps on the tab have (kl_map_escape.van_wire). The
    # rest of the round's last stage is F07's own and stays as the graft left it (kl_fa_bank.wire's note)
    if HELI:                                            # no van_wire: the exit trigger names the chopper (GUESS: nothing else of the van's wiring has a chopper form yet)
        n_ex = 0
        for k, i, v in kl_fa.controllers(sc, kl_fa.EXIT):
            kl_fa.edit(sc, k, i, lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van_path(), '', ''))])
            n_ex += 1
        log('  kl_fa_club: HELI: %d exit trigger(s) name the chopper group %s; no van_wire' % (n_ex, HELI_GROUP))
    else:
        if PLAN is None:
            raise ValueError('kl_fa_club: wire() without a plan of the van (see prepare_host)')
        ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_fa_club: sequence: round start -> %.0f s -> %s' % (SEAL_AT, 'the seal off (%s)' % ', '.join(p.split('\\')[-1] for p in seal) if seal
                                                              else 'nothing: the seal is out at build time (SEAL_OPEN)'))
    log('  kl_fa_club: wired: round start %s; %d briefing / reminder lines; exit line %s' % (
        '-> %.1f s -> %d door leaves and the music\'s muffle switch' % (DOORS_AT, len(leaves)) if DOORS_ANIMATE
        else 'starts no door (the leaves are open at build time) and sends the music\'s muffle switch \'%s\'' % MUFFLE_MESSAGE, len(LINES), EXIT_LINE))
    men = sum(a for _f, a, _s, _k in plan.values())
    if plan:
        by = collections.Counter(squads_now()[n][0] for n in plan)
        log('  kl_fa_club: enemies: %d campaign squads (%d men): %d in the world from the load%s; round start + %.0f s -> %d (front office); the box at the inner '
            'office door -> %d; the box on the walkway -> %d; the gate -> %d hunt + %d of F07\'s police squads; %d dead entries cut from the squads\' message '
            'lists; soldier rows: %s' % (len(plan), men, len(plan) if SQUADS_AWAKE else by['load'], ' (SQUADS_AWAKE: all of them)' if SQUADS_AWAKE else '',
                                         OFFICE_AT, len(stage['office']), len(stage['walk']), len(stage['floor']), len(stage['open']), len(arrive), quiet,
                                         dict(armed) or 'Dead Men\'s rows stay'))
        log('  kl_fa_club: the beat: %s wiped out -> counter of %d -> the seal off and the gate; or the clock (%.0f s)' % (
            ' and '.join(n.split('!')[-1] for n in beat), len(beat), SEAL_AT))
    else:
        log('  kl_fa_club: enemies: none (NO_AI); the seal opens by its clock')
    return {'leaves': leaves, 'seal': seal, 'monitor': have + start, 'stage': dict(stage), 'arrive': arrive}


def layer_names(sc):
    """Top-level names of the layer in the joined scene: what kl_fa.repair's prune may cut dead references from."""
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    """One map: the layer is wired in the one build there is."""
    return True


# ------------------------------------------------------------------ the doors at build time
class Doors(BK.Doors):
    """kl_fa_bank.Doors (THE FALL-BACK THAT WALKS OFFLINE; its docstring says what the three wrappers do and why)
    for this level's nodes: sunk() and the three wrappers are this class's - the bank's read the bank's tables -
    the frame arithmetic (prp_frame, prp_world) and arm / disarm are inherited. Besides key-framed leaves it takes
    out STATIC pieces (the seal): kl_escape.cut_collision turns their placements into filler copies (G1.3)."""
    real, state = None, None

    @classmethod
    def sunk(cls):
        """Paths (below ROOT) of the nodes this build takes out."""
        standing = set(gate())
        return ([] if DOORS_ANIMATE else [p for p, _at, _set in LEAVES]) + [p for p, _at, _set in SEAL if p not in standing] + (HELI_SUNK if HELI else [])

    @classmethod
    def repair(cls, sc, log=print):
        done = cls.real[0](sc, log)
        st, tilted = cls.state, 0
        for path in cls.sunk() if sc.resolve(R + IN[:-1]) else ():      # only on a scene that holds the club
            k = A.node_of(sc, path)
            lab = J.labels('dd', sc.cls(k))
            Rm, _T = cls.prp_frame(sc, k)
            d = [Rm[1][a] * DOOR_DY for a in range(3)]   # R^T (0, dy, 0): the world's y move in the parent's frame
            tilted += abs(d[1] - DOOR_DY) > 0.01
            old = list(kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')])
            new = [old[a] + d[a] for a in range(3)]
            before = cls.prp_world(sc, k)
            kl_fa.edit(sc, k, None, lambda us, lab=lab, new=new: A.setv(sc, us, lab.index('ZGEOM[2]'), new))
            st['sink'][k], st['old'][k], st['prp_w'][k] = DOOR_DY, old, (before, cls.prp_world(sc, k))
        if st['sink']:
            log('  kl_fa_club: doors: %d nodes sunk by %g (world y) in the joined .prp; %d of them stand in a parent frame '
                'with another y axis than the world\'s' % (len(st['sink']), -DOOR_DY, tilted))
        return done

    @classmethod
    def place(cls, sc, ents, done, log=print):
        st = cls.state
        before = {k: world_of(ents[k - 1])[0] for k in st['sink']}
        other = 0
        for k in st['sink']:
            e = ents[k - 1]
            t = struct.unpack('<3f', e.trans[:12])
            other += max(abs(t[a] - st['old'][k][a]) for a in range(3)) > 0.05
            if max(abs(before[k][a] - st['prp_w'][k][0][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: world place by the .gms %s, by the .prp %s' % (sc.path[k], before[k], st['prp_w'][k][0]))
            Rm = world_of(e.parent)[1] if e.parent is not None else [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
            done['move'][k] = tuple(t[a] + Rm[1][a] * DOOR_DY for a in range(3))     # place_entities writes it into the record
        refs = set(cls.real[1](sc, ents, done, log))
        refs |= {ents[k - 1].ref for k in st['sink']}   # the sunk nodes' REF ids, for cut_collision
        for k in sorted(st['sink']):
            after = world_of(ents[k - 1])[0]
            if abs(after[0] - before[k][0]) > 0.5 or abs(after[2] - before[k][2]) > 0.5 or abs(after[1] - before[k][1] - DOOR_DY) > 0.5:
                raise ValueError('%s moved %s -> %s, not straight down by %g' % (sc.path[k], before[k], after, -DOOR_DY))
            if max(abs(after[a] - st['prp_w'][k][1][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: after the move the .gms says %s, the .prp %s' % (sc.path[k], after, st['prp_w'][k][1]))
        if st['sink']:
            log('  kl_fa_club: doors: %d entities moved in the .gms (%d of them hold another local place there than in the .prp; '
                'the world places agree); %d REF ids go to cut_collision' % (len(st['sink']), other, len(refs)))
        if not refs:                                    # kl_graft does not call cut_collision then: the build is through
            cls.disarm()
        return refs

    @classmethod
    def cut(cls, hvk, refs, log=print):
        try:
            mine = collections.Counter(s.type for s in hvk.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            h = cls.real[2](hvk, refs, log)
            left = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            if left:
                raise ValueError('%d placements are left in the .HVK under the %d REF ids taken out' % (left, len(refs)))
            log('  kl_fa_club: doors: %d placements (by shape type %s) were under the %d REF ids; none is left' % (sum(mine.values()), dict(mine), len(refs)))
            return h
        finally:
            cls.disarm()


@contextlib.contextmanager
def doors(log=print):
    """For a script that builds: the wrappers of Doors for the length of the block, taken out whatever happens."""
    Doors.arm(log)
    try:
        yield Doors
    finally:
        Doors.disarm()


# ------------------------------------------------------------------ on the written level
def finish(folder, log=print):
    """What needs the WRITTEN level, in place, on a folder with <slot>_Main.zip -> [problems]. A level finished
    before is left as it is.
    0. The level is lightened (kl_graft's trim + slim, kl_fa_loot.lighten_first): F07's dead map models and the
       textures only they show go. It has to come before the dead chunk indices are handed out.
    1. Every loot object shows a briefcase, lies on its top turned as LOOT says: kl_fa_loot's way - the model
       root comes from Dead Men's M01_FA_A into dead indices, its materials get compiled shaders.
    2. The level's own texts: TEXTS into every language's .LOC, the settings' start windows onto them."""
    import kl_fa_loot as L, kl_chars as C, kl_light, kl_loc, kl_texmat as T
    from kl_port_check import workdir
    E = L.Edit(folder)
    sc, bad = E.sc, []
    loot = [k for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    dressed = not {E.ents[k - 1].model for k in loot} <= pool
    if len(loot) != len(LOOT):
        bad.append('%d loot objects in the level, LOOT has %d' % (len(loot), len(LOOT)))
    n0 = len(E.p.chunks)
    L.lighten_first(E, log)                             # always: what is checked and handed on is the lightened level
    if CASE and loot and not dressed:
        C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
        root, _box, slots = L.case_model(E, CASE, CASE_SCALE, log)
        lo, _hi = L._assets(E).bounds(root)             # of what is drawn: the model's underside goes onto the top it lies on
        for k in loot:
            at = E.at(k)
            p, yaw, _value, _what = min(LOOT, key=lambda r: math.dist(r[0], at))
            if math.dist(p, at) > 1.0:
                bad.append('%s lies at (%d, %d, %d), which is no place of LOOT' % (sc.names[k], *at))
                continue
            E.put(k, (p[0], p[1] - lo[1], p[2]), L.yaw9(yaw), root)
        if len(E.p.chunks) != n0:
            raise ValueError('the chunk table grew from %d to %d: not enough dead indices' % (n0, len(E.p.chunks)))
        if slots:                                       # a material without a compiled shader is not drawn (kl_fa_loot.dress)
            fxc = E.lv['.fxc']
            upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
            if os.path.isfile(upath):
                fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
            fit = kl_light.fit_shaders(E.mat, fxc, slots=slots, log=log)
            E.lv['.fxc'] = fxc
            bad += ['no compiled shader for %s' % v[0] for v in fit['unresolved'].values()]
        log('  kl_fa_club: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_club: %s: the loot already shows models of its own: left as it is' % folder)
    # ---- texts
    langs = 0
    for ext in sorted(E.lv.ext):
        if not ext.lower().endswith('.loc'):
            continue
        kids = kl_loc.parse(E.lv[ext])
        if kids is None:                                # a stub (Dutch in every stock level)
            continue
        for key, text in TEXTS.items():
            BK.set_text(kids, key, text)
        E.lv[ext] = kl_loc.build(kids)
        langs += 1
    for k, i, _v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, START_KEY % w)]) for f, w in START_FIELDS.items()])
    log('  kl_fa_club: %d text keys in %d languages (the English text in each); settings fields %s name the start windows' % (
        len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ the checks
# the round's way, for tools/kl_route.py: the stations of re/campaign_fa_club.md 4.3 (the AI heisters' row), each
# MEASURED on the mesh. ROUTE_IN ends where the seal begins; ROUTE_OUT is what the seal gates
ROUTE_IN = [('START', START_REF), ('inner office door', (2600, 347, 3313)), ('front office', (2000, 354, 3300)), ('walkway', (780, 371, 2747)),
            ('dance floor 2', (-864, 40, 2491)), ('dance floor 1', (-1100, 20, 1150)), ('stair landing', (-55, 160, 320)),
            ('wardrobe', (-4, 180, -240)), ('entrance hall', (-414, 100, -604)), ('queue lane, club end', (105, 20, -1500))]
ROUTE_OUT = [('queue lane, street end', (105, 20, -2600)), ('pavement', ESC_AT)]
BOARD_AT = (-637.0, 30.0, -3100.0)     # the van's boarding place at its stop (ROAD): the rear doors; MEASURED by van-check
# the walk test of the loot's pick-up: (box x0, x1, z0, z1; places the route test reaches) for the office, dance floor 1
# and the wardrobe / entrance. GUESS: the three boxes (each room with a margin); the places are stations of ROUTE_IN
LOOT_WALKS = (((2300.0, 3400.0, 2000.0, 3600.0), [START_REF]), ((-2000.0, 100.0, 400.0, 1700.0), [(-1100.0, 20.0, 1150.0)]),
              ((-800.0, 700.0, -1700.0, 400.0), [(-4.0, 180.0, -240.0), (105.0, 20.0, -1500.0)]))
BLOCKS_LIVE = BK.BLOCKS_LIVE            # the five large load blocks of the build that loaded seven times in one process: 171 MB
# the chunk table: 69,632 entries is the tools' line (kl_impact.CHUNK_SAFE). The wardrobe and the gun looks come into
# DEAD indices: 'kl_chars.py wardrobe --plates=wolf,dallas,chains,hoxton' took 20,989 of the club's 24,318 in the study
# (re/campaign_fa_club.md 3.3) - the same number as on the bank (kl_fa_bank.WARDROBE_CHUNKS)
WARDROBE_CHUNKS = BK.WARDROBE_CHUNKS


ACTORS_LIVE = BK.ACTORS_LIVE            # ZFFActor and squads of the largest build that runs live (Retomoto on the tab: 99 / 55)
LANE_VIEWS = [(float(x), 20.0, float(z)) for x in (90, 118, 150, 250, 340) for z in (-1700, -1900, -2100, -2250, -2320)]
                                        # places in the queue lane up to the seal's inner edge (z -2335), for Sight. GUESS: the grid


class Sight:
    """A crude line of sight in a built level's collision, for ONE question: is a man who comes into the world later
    in view of a place the crew can be at that moment. kl_route's grid holds, per 20-unit cell, a height sample of
    everything solid there (walls every 10 units of height, floors at theirs); a line is walked in steps of 8 and is
    cut by a sample within 8 of its height. `glass`: REF ids that do not count (the seal: invisible collision).
    What it cannot know: a wall that is drawn and has no collision hides nobody here, a window's collision hides
    him; a rail or a table lower than the line is looked over. A man is SEEN when the line from eyes at 160 to his
    head (160) or to his chest (90) is free. GUESS: the three heights and the tolerance."""
    EYE, HEAD, CHEST, STEP, TOL = 160.0, 160.0, 90.0, 8.0, 8.0

    def __init__(self, lv, glass=()):
        import bisect
        self.g, self.glass, self.bisect = lv.grid(), frozenset(glass), bisect

    def solid(self, x, y, z):
        i, j = self.g.cell(x, z)
        self.g.floors(i, j)                             # makes the block
        s = self.g.so.get((i, j))
        if s:
            for k in range(self.bisect.bisect_left(s, (y - self.TOL, -1)), len(s)):
                if s[k][0] > y + self.TOL:
                    break
                if s[k][1] not in self.glass:
                    return True
        return False

    def free(self, a, b):
        n = int(math.dist(a, b) / self.STEP) + 1
        return not any(self.solid(*[a[c] + (b[c] - a[c]) * k / n for c in range(3)]) for k in range(1, n))

    def seen(self, view, man):
        a = (view[0], view[1] + self.EYE, view[2])
        return self.free(a, (man[0], man[1] + self.HEAD, man[2])) or self.free(a, (man[0], man[1] + self.CHEST, man[2]))


def way_views(mesh, stations, step=150.0):
    """The stations and points every `step` on the line an AI is given between each two (kl_route.Mesh.way), at the
    mesh's height: where the crew can be on that stretch of the round."""
    out = [tuple(p) for p in stations]
    for a, b in zip(stations, stations[1:]):
        ia, ib = mesh.on(*a), mesh.on(*b)
        w = mesh.way(ia[0], ib[0]) if ia and ib else None
        line = [a] + [tuple(q) for q in w[0]] + [b] if w else [a, b]
        for p, q in zip(line, line[1:]):
            n = int(math.dist(p, q) / step)
            for k in range(1, n + 1):
                x, y, z = (p[c] + (q[c] - p[c]) * k / (n + 1) for c in range(3))
                hit = mesh.on(x, y, z)
                out.append((x, hit[1] if hit else y, z))
    return out


def drawn_lane(folder, road, half=ESC.VAN_HALF):
    """What the MAP DRAWS in the lane of a drive - kl_map_escape's lane test sees collision only, and outside the
    slab this level has none (the study's open point: 'nothing DRAWN was tested in the lane'). road: an ESC.Poly
    whose y is the road. Every mesh of every entity below a 'Locations/' subtree that has a model and is not
    hidden (kl_fa_loot.Assets: static meshes, vertex stride 40; without collision hulls and blob shadows), in
    world space; the lane's samples are the tool's (five rays across `half`, every LANE_STEP, VAN_TAIL before
    and VAN_NOSE beyond). -> dict: samples, floor = how many have a drawn surface of upness > FLOOR within
    VAN_BODY[0] of the road under them, first_bare, y = that surface's range, pieces = Counter of the entities it
    belongs to, body = {entity: [first, last, count, material]} of what is drawn VAN_BODY over the road - under a
    ray, or with a corner inside the lane (a lamp post is thinner than the rays are apart) -, tris.
    What it cannot know: what the game does not draw (a model switched off by something), and a person."""
    import kl_fa_loot as L
    arch = BK.archive_of(folder)
    As, B = L.Assets(arch), L.Built(arch)
    fr = L.frames(B.scene)
    pts, s = [], -ESC.VAN_TAIL
    while s <= road.len + ESC.VAN_NOSE + 1e-6:
        p, t = road.at(s), road.tan(s)
        pts += [(s, p[0] + off * t[1], p[1], p[2] - off * t[0]) for off in (-half, -half / 2, 0.0, half / 2, half)]
        s += ESC.LANE_STEP
    x0, x1 = min(q[1] for q in pts) - 30.0, max(q[1] for q in pts) + 30.0
    z0, z1 = min(q[3] for q in pts) - 30.0, max(q[3] for q in pts) + 30.0
    y0, y1 = min(q[2] for q in pts) - 60.0, max(q[2] for q in pts) + ESC.VAN_BODY[1]
    box, tris, cell = {}, [], collections.defaultdict(list)
    for k, e in enumerate(B.ents):
        if e.model <= 0 or e.flags & HIDDEN or not B.sc.names[B.sc.top[k + 1]].startswith('Locations/'):
            continue
        if e.model not in box:
            try:
                box[e.model] = As.bounds(e.model)
            except (ValueError, IndexError, struct.error):  # no model root (a light, a sprite): nothing solid is drawn
                box[e.model] = None
        if box[e.model] is None:
            continue
        Rm, T = fr[e]
        w = lambda q: tuple(T[a] + sum(Rm[a][b] * q[b] for b in range(3)) for a in range(3))
        lo, hi = box[e.model]
        cs = [w((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        if max(c[0] for c in cs) < x0 or min(c[0] for c in cs) > x1 or max(c[2] for c in cs) < z0 or min(c[2] for c in cs) > z1 \
                or max(c[1] for c in cs) < y0 or min(c[1] for c in cs) > y1:
            continue
        name = B.sc.path[k + 1][5:]
        for o in As.meshes(e.model):
            pos, _uv, ii = As.geometry(o)
            ws, mat = [w(q) for q in pos], As.material(o).split('/')[-1]
            for ia, ib, ic in ii:
                a, b, c = ws[ia], ws[ib], ws[ic]
                if max(a[0], b[0], c[0]) < x0 or min(a[0], b[0], c[0]) > x1 or max(a[2], b[2], c[2]) < z0 or min(a[2], b[2], c[2]) > z1 \
                        or max(a[1], b[1], c[1]) < y0 or min(a[1], b[1], c[1]) > y1:
                    continue
                e1, e2 = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
                ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
                if ln < 1e-6:
                    continue
                tris.append((a, b, c, abs(n[1]) / ln, name, mat))
                for i in range(int(min(a[0], b[0], c[0]) // 200), int(max(a[0], b[0], c[0]) // 200) + 1):
                    for j in range(int(min(a[2], b[2], c[2]) // 200), int(max(a[2], b[2], c[2]) // 200) + 1):
                        cell[i, j].append(len(tris) - 1)
    out = dict(samples=len(pts), floor=0, first_bare=None, pieces=collections.Counter(), body=collections.OrderedDict(), tris=len(tris))
    ys = []
    def body(name, mat, s):
        e = out['body'].setdefault(name, [round(s), round(s), 0, mat])
        e[0], e[1], e[2] = min(e[0], round(s)), max(e[1], round(s)), e[2] + 1
    for s, x, y, z in pts:
        under = None
        for t in cell.get((int(x // 200), int(z // 200)), ()):
            a, b, c, up, name, mat = tris[t]
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-9:
                continue
            u = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            v = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            h = u * a[1] + v * b[1] + (1 - u - v) * c[1]
            if up > ESC.FLOOR and abs(h - y) <= ESC.VAN_BODY[0] and (under is None or h > under[0]):
                under = (h, name)
            if y + ESC.VAN_BODY[0] < h < y + ESC.VAN_BODY[1]:
                body(name, mat, s)
        if under:
            out['floor'] += 1
            out['pieces'][under[1]] += 1
            ys.append(under[0])
        elif out['first_bare'] is None:
            out['first_bare'] = round(s)
    # corners inside the lane, in the body's height (the line carried on VAN_TAIL before and VAN_NOSE beyond the drive)
    ext = ESC.Poly([road.at(-ESC.VAN_TAIL)] + list(road.p) + [road.at(road.len + ESC.VAN_NOSE)])
    lo_y, hi_y = min(p[1] for p in road.p) + ESC.VAN_BODY[0], max(p[1] for p in road.p) + ESC.VAN_BODY[1]
    for a, b, c, _up, name, mat in tris:
        for q in (a, b, c):
            if lo_y < q[1] < hi_y:
                s, d = ext.project(q)
                r = ext.at(s)[1]
                if abs(d) <= half and 1e-3 < s < ext.len - 1e-3 and r + ESC.VAN_BODY[0] < q[1] < r + ESC.VAN_BODY[1]:
                    body(name, mat, s - ESC.VAN_TAIL)
    out['y'] = (min(ys), max(ys)) if ys else (0.0, 0.0)
    return out


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (and finished) folder -> [what is wrong]. problems: kl_graft.verify's
    list of the build, when the caller has it (else result.json beside the archive is read). What the BUILD did
    (doors sunk or standing, which pieces of the seal stand, what of the never-run kinds stayed) is read off the
    level, not off this module's flags: 'check <folder>' is right for any variant."""
    import json, kl_route, kl_impact, kl_arms
    import kl_fa_loot as L
    arch = BK.archive_of(folder)
    sc, scene, ents, pos, hvk, snd, loc, size = BK.read_built(folder)
    bad = []
    def fail(s):
        bad.append(s); log('  FAIL: ' + s)
    named = lambda role: A.named(sc, A.node_of(sc, ROLE[role]))
    # ---- kl_graft.verify, against KNOWN
    res = json.load(open(os.path.join(folder, 'result.json'))) if os.path.isfile(os.path.join(folder, 'result.json')) else {}
    if problems is None:
        problems = res.get('problems')
    if res.get('dangling'):                             # scene paths the build found naming nothing
        fail('the build left %d dangling scene paths: %s' % (len(res['dangling']), res['dangling'][:3]))
    squads = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript') if not sc.path[k][len(R):].startswith(BK.BOT_SQUAD)]
    known = KNOWN + (() if squads else (KNOWN_NO_AI,))
    for p in problems or ():
        why = next((w for t, w in known if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    # ... and what of the sound is really lost: result.json's list is by NAME (kl_fa_bank.lost_clips), the built .WHD says more
    listed, lost, have = BK.lost_clips(folder, res)
    if listed:
        log('  sound: of the %d clip names result.json lists, %d have a streamed record in the built .WHD; %d have NO record = what the stream '
            'file\'s extension must bring:%s' % (len(listed), len(listed) - len(lost), len(lost), ''.join('\n          ' + n for n in lost)))
        odd = [n for n in lost if n not in MUSIC_CLIPS + AMBIENCE_CLIPS]
        if odd:
            fail('sound: %d clips without a record are neither in MUSIC_CLIPS nor in AMBIENCE_CLIPS: %s' % (len(odd), odd[:4]))
    in_whd = sum(n.lower() in have for n in MUSIC_CLIPS)
    log('  music: %d of the %d clips of the club\'s two tracks have a record in the built .WHD (%s); nothing starts the tracks, nothing stops them' % (
        in_whd, len(MUSIC_CLIPS), 'silent until the stream file holds them' if not in_whd else 'they play once that stream file is installed'))
    # ---- kl_fa.check on the written archive
    for f in kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch)):
        why = next((w for t, w in known if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
        log('  kl_fa: %s%s' % (str(f)[:230], '\n          = known: %s' % why if why else ''))
        if f.sev <= kl_fa.BROKEN and not why:
            fail('kl_fa.check: ' + str(f)[:200])
    ncov = len(kl_fa.controllers(sc, 'FFCoverList'))
    log('  cover lists (FFCoverList): %d' % ncov)
    if ncov != 1:
        fail('%d cover lists (a level needs exactly one)' % ncov)
    if any(sc.names[t].startswith('Boundaries!') for t in sc.tops()):
        fail('the campaign\'s own Boundaries! objects are in the level (M_DROP)')
    # ---- the doors and the seal, read back: each node DOOR_DY under its stock place and without a placement, or in
    # its place with one
    per = collections.Counter(kl_hvk.ref(i) for s in hvk.shapes for i in s.inst)
    state, ref_of = {}, {}
    for path, stock, name in LEAVES + SEAL:
        k = A.node_of(sc, path)
        e = ents[k - 1]
        low = abs(pos[e][1] - stock[1] - DOOR_DY) < 2.0
        state[path], ref_of[path] = low, e.ref
        ok = (low or abs(pos[e][1] - stock[1]) < 2.0) and abs(pos[e][0] - stock[0]) < 2.0 and abs(pos[e][2] - stock[2]) < 2.0 and bool(per[e.ref]) != low
        log('  %-20s %-10s REF %-6d at (%d, %d, %d), %d placement(s): %s' % (name, sc.names[k], e.ref, *pos[e], per[e.ref],
                                                                        'sunk, no collision' if low else 'in its place, collides'))
        if not ok:
            fail('%s %s: at (%d, %d, %d) with %d placements; its place in the level is (%d, %d, %d)' % (name, sc.names[k], *pos[e], per[e.ref], *stock))
    animate = not state[LEAVES[0][0]]
    if len({state[p] for p, _at, _set in LEAVES}) != 1:
        fail('the four leaves are not all in one state: sunk %s' % sorted(p.split('\\')[-1] for p, _a, _s in LEAVES if state[p]))
    standing = [p for p, _at, _set in SEAL if not state[p]]         # the seal's pieces that stand: the round's one gate
    gates = [ref_of[p] for p in standing] + ([ref_of[p] for p, _a, _s in LEAVES] if animate else [])
    seal_refs = [ref_of[p] for p in standing]
    lv = kl_route.load(folder)
    path_of = {e.ref: sc.path[k + 1] for k, e in enumerate(ents)}
    for ref, far in lv.moved():                         # a placement that stands off its entity (the van's five key-framed
        fail('REF %d (%s): its collision placement stands %d from its entity' % (ref, path_of.get(ref, '?')[-60:], far))     # bodies too: van_hvk)
    # ---- every spawn point and player group: on the START's mesh part, on free floor (the gates taken out: the
    # police who come back stand beyond the seal)
    pts, names = [START_REF], ['START']
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint' or sc.parent[k] == 0 and sc.names[k].startswith('Heroes!'):
            pts.append(pos[ents[k - 1]]); names.append(sc.names[k])
    rows = kl_route.stations(lv, pts, opened=gates, near=30)
    part = rows[0]['part']
    off = [(n, r) for n, r in zip(names, rows) if not (r['mesh'] and r['part'] == part and r['reached'])]
    log('  spawn points and player groups: %d places, %d on the mesh part of the START (%s polygons) and on free floor within 30' % (
        len(pts) - 1, len(pts) - 1 - len(off), rows[0].get('part_size')))
    for n, r in off:
        fail('%s at (%d, %d, %d): mesh %s, part %s, reached %s (gap %s)' % (n, *r['at'], r['mesh'], r['part'], r['reached'], r.get('gap')))
    kinds = collections.Counter(kl_fa.node_values(sc, k)[8] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint')
    bodies = [k for k in range(1, len(sc.nodes)) if sc.parent[k] == 0 and sc.names[k].startswith('Heroes!Henchmen_')]
    back = kinds['eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH']
    log('  spawn kinds: %s; police who come back: %d bodies, %d AFTER_DEATH points' % (
        {k.replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in sorted(kinds.items())}, len(bodies), back))
    if len(bodies) != 8 or back != len(POLICE) or kinds['eSPAWN_TYPE_FRAGILE_ALLIANCE_START'] != 8 or not set(kinds) <= set(SPAWN):
        fail('spawn points: %d police bodies (8 wanted), %d AFTER_DEATH points (%d), %d START (8), kinds %s' % (
            len(bodies), back, len(POLICE), kinds['eSPAWN_TYPE_FRAGILE_ALLIANCE_START'], sorted(set(kinds) - set(SPAWN))))
    # every one of them outside the pavement stands on the SLAB (the only collision floor there)
    out_ = [(n, p) for n, p in zip(names, pts) if p[2] < LANE_MOUTH[2] and not (SLAB[0][0] <= p[0] <= SLAB[0][1] and SLAB[1][0] <= p[2] <= SLAB[1][1])]
    for n, p in out_:
        fail('%s at (%d, %d, %d) is outside the building and not on the slab' % (n, *p))
    # ---- bounds and kill boxes: nobody starts inside one, no station of the round lies in one; three bound trios
    # stand at the slab's edges and three kill boxes under them, every other bound of the host is parked
    fr = L.frames(scene)
    def world_box(j):
        Rm, T = fr[ents[j - 1]]
        ext = [sum(abs(Rm[a][b]) * h for b, h in enumerate(kl_fa.node_values(sc, j)[8:11])) for a in range(3)]
        return [T[a] - ext[a] for a in range(3)], [T[a] + ext[a] for a in range(3)]
    boxes, live = [], 0
    for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
        far = pos[ents[k - 1]][1] < PARK[1] / 2
        live += not far
        for j in [k] + [j for lst in v[0:2] for s in lst for j in sc.resolve(s)]:
            boxes.append((sc.names[j], *world_box(j)))
            if (pos[ents[j - 1]][1] < PARK[1] / 2) != far:
                fail('%s: the bound and its warn boxes are not parked together' % sc.names[j])
    kills = [k for k in (sc.resolve(R + n) for n in KILL) if k]
    for (k,) in kills:
        lo, hi = world_box(k)
        boxes.append((sc.names[k], lo, hi))
        log('  kill box %-20s x %d..%d, y %d..%d, z %d..%d  %s' % (sc.names[k], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], values(sc, k, 'KillBox')))
        if hi[1] > SLAB[2] - 100.0 or not kl_fa.has(sc, k, 'KillBox'):
            fail('kill box %s: its top is y %d (the slab is %d: at least 100 under it), KillBox %s' % (sc.names[k], hi[1], SLAB[2], kl_fa.has(sc, k, 'KillBox')))
    way = ROUTE_IN + ROUTE_OUT
    held = [(n, p, b) for n, p in list(zip(names, pts)) + way + [('the lane\'s mouth', LANE_MOUTH)] for b, lo, hi in boxes
            if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
    log('  bounds: %d LevelBound in their place (%d bound and warn boxes with the parked ones), %d kill boxes; %d of the %d spawn points, player groups and stations inside one' % (
        live, len(boxes) - len(kills), len(kills), len(held), len(pts) + len(way) + 1))
    if live != len(BOUNDS) or len(kills) != len(KILL):
        fail('%d level bounds stand (%d wanted) and %d kill boxes (%d)' % (live, len(BOUNDS), len(kills), len(KILL)))
    for n, p, b in held:
        fail('%s at (%d, %d, %d) stands inside %s' % (n, *p, b))
    # the three edges of the slab: 100 beyond each a bound box holds a walker, 100 before it none does (a warn box may)
    bound = [(sc.names[k], *world_box(k)) for k, _i, _v in kl_fa.controllers(sc, 'LevelBound') if pos[ents[k - 1]][1] > PARK[1] / 2]
    inb = lambda p: [b for b, lo, hi in bound if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
    mid = ((SLAB[0][0] + SLAB[0][1]) / 2, (SLAB[1][0] + SLAB[1][1]) / 2)
    for what, on, over in (('west', (SLAB[0][0] + 100, SLAB[2], mid[1]), (SLAB[0][0] - 120, SLAB[2], mid[1])),
                           ('east', (SLAB[0][1] - 100, SLAB[2], mid[1]), (SLAB[0][1] + 120, SLAB[2], mid[1])),
                           ('kerb', (mid[0], SLAB[2], SLAB[1][0] + 100), (mid[0], SLAB[2], SLAB[1][0] - 120))):
        if inb(on) or not inb(over):
            fail('the slab\'s %s edge: a walker 1 m before it is in %s, 1.2 m beyond it in %s' % (what, inb(on) or 'no bound', inb(over) or 'no bound'))
    # ---- loot: the pick-up test as read in kl2.exe (kl_fa_loot.in_reach: horizontal distance <= radius + 40, a height
    # window) from a place a walk reaches (kl_fa_loot.Floors), with MARGIN to spare. The walks start where the route
    # test below proves the crew comes. Hidden things do not count here
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2]]
    built = L.Built(arch)
    skip = built.soft() | built.hidden
    walks = []
    for box, starts in LOOT_WALKS:
        f = L.Floors(hvk, box, skip=skip)
        walks.append((box, f, f.flood(starts)[0]))
    taken = 0
    for k, v in loot:
        at, tb = pos[ents[k - 1]], values(sc, k, 'TriggerBox2')
        row = min(LOOT, key=lambda r: math.hypot(r[0][0] - at[0], r[0][2] - at[2]))
        best = None
        for box, f, seen in walks:
            if box[0] <= at[0] <= box[1] and box[2] <= at[2] <= box[3]:
                place, h, n = f.stand(seen, at, tb[2])
                if place is not None and (best is None or h < best[1]):
                    best = (place, h, n)
        spare = tb[2] + L.REACH_PAD - best[1] if best else None
        good = best is not None and spare >= L.MARGIN
        log('  loot %-36s %7d at (%5d %5d %6d) %-26s %s' % (sc.names[k][-36:], v[1], *at, row[3], 'from (%d, %d, %d): %d away, %d up, %d to spare' % (
            *best[0], best[1], at[1] - best[0][1], spare) if best else 'OUT OF REACH'))
        if not good:
            fail('loot %s at (%d, %d, %d) on %s cannot be taken%s' % (sc.names[k], *at, row[3], ' with %d to spare (%d wanted)' % (spare, L.MARGIN) if best else ''))
        if math.hypot(row[0][0] - at[0], row[0][2] - at[2]) > 1.0 or v[1] != row[2]:
            fail('loot %s at (%d, %d, %d) worth %d is no row of LOOT' % (sc.names[k], *at, v[1]))
        hide = bool(kl_fa.node_values(sc, k)[3])
        if hide or ents[k - 1].flags & HIDDEN or tb[2] != LOOT_REACH or tb[3] != 1:
            fail('loot %s: hidden %s (flag %#x), TriggerBox2 radius %s, people-only %s' % (sc.names[k], hide, ents[k - 1].flags, tb[2], tb[3]))
        taken += good
    log('  loot: %d objects, %d; %d can be taken' % (len(loot), sum(v[1] for _k, v in loot), taken))
    if len(loot) != len(LOOT):
        fail('%d loot objects, LOOT has %d' % (len(loot), len(LOOT)))
    # the ENTERS box holds every START point and the office's loot (the bots' stage order: START -> ENTERS -> loot)
    lo, hi = world_box(A.node_of(sc, 'FASpecials!PIP!EnterLootArea'))
    inside = lambda p: all(lo[a] <= p[a] + (50 if a == 1 else 0) <= hi[a] for a in range(3))
    office = [pos[ents[k - 1]] for k, v in loot if v[1] == LOOT[0][2]]
    starts_ = START_V2 if V2 else START_V1
    n_in = sum(inside(p) for p in starts_)
    log('  ENTERS box x %d..%d, y %d..%d, z %d..%d: %d of the %d START points (%s) and %d of the office\'s %d cases inside' % (
        lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], n_in, len(starts_), 'V2: none may be - the crew ENTERS by walking in' if V2 else 'V1: all', sum(inside(p) for p in office), len(office)))
    if (n_in != 0 if V2 else n_in != len(starts_)) or not all(inside(p) for p in office) or len(office) != 6:
        fail('the ENTERS box %s and the six cases of the office' % ('holds a START point (V2: the crew starts outside it)' if V2 else 'does not hold every START point'))
    # ---- the route in the built collision, nothing removed at test time; what still stands is the round's gate
    crossing = lambda r: sorted({(o['ref'], o['name']) for leg in r['legs'] for c in leg.get('crossed') or () for o in c['objects']})
    say = lambda r: 'FREE, %d m' % r['length'] if r['free'] else 'NOT free; crossed: %s' % [n for _r, n in crossing(r)]
    all_pts = [p for _n, p in way]
    shut = kl_route.route(lv, all_pts)
    log('  route, %d stations (office -> pavement), the level as built: %s' % (len(all_pts), say(shut)))
    if shut['free'] != (not gates) or any(r not in gates for r, _n in crossing(shut)):
        fail('the route as built: free %s, crossed %s; what stands: %d' % (shut['free'], [n for _r, n in crossing(shut)], len(gates)))
    if not animate:                                     # the doors are open: everything up to the seal is free as built
        inside_ = kl_route.route(lv, [p for _n, p in ROUTE_IN])
        log('  route office -> queue lane, club end (%d stations), as built: %s' % (len(ROUTE_IN), say(inside_)))
        if not inside_['free']:
            fail('the way from the office to the queue lane is not free as built')
        if seal_refs and sorted(r for r, _n in crossing(shut)) != sorted(seal_refs)[:len(crossing(shut))]:
            fail('with the seal in its place the route should be shut by the seal alone: %s' % [n for _r, n in crossing(shut)])
    if gates:
        opened = kl_route.route(lv, all_pts, opened=gates)
        log('  route with the %d standing piece(s) out (%s): %s' % (len(gates), ', '.join(sc.path[A.node_of(sc, p)].split('\\')[-1] for p in standing), say(opened)))
        if not opened['free']:
            fail('the route is not free with the seal out')
        for p in standing:                              # each standing piece alone shuts the lane
            alone = kl_route.route(lv, all_pts, opened=[g for g in gates if g != ref_of[p]])
            if alone['free']:
                fail('%s alone does not shut the lane' % p.split('\\')[-1])
    # ---- the chain, read back
    mine = [(ROLE[r], A.node_of(sc, ROLE[r])) for r in ROLE]
    for n, k in mine:
        for s in A.named(sc, k):
            if not sc.resolve(s):
                fail('%s names %s, which is no node' % (n, s))
    mon = named('monitor')
    starters = {R + ROLE['seal timer']} | ({R + ROLE['doors timer']} if animate else set() if V2 else {R + ROLE['muffle']}) | ({R + ROLE['office timer']} if named('office timer') else set())
    starters |= {R + ROLE[r] for r in RESET_ROLES if r in ROLE and named(r)}      # RESET: the objects that put round 1's state back, first in the list
    starters |= {R + ROLE[r] for r in WAKE_NEW if r.startswith('wake timer') and r in ROLE}   # THE WAKE FIX: the three backstops
    if {s for s in mon if s[5:] in ROLE.values() and not any(s[5:] == ROLE[r] for r in LATE_ROLES if r in ROLE)} != starters:
        fail('the round start names %s of this layer\'s objects, wanted %s' % (sorted(s for s in mon if s[5:] in ROLE.values()), sorted(starters)))
    delay = lambda role: values(sc, A.node_of(sc, ROLE[role]), 'TriggerDelay2')[0]
    off_ = named('seal off')
    if sorted(off_) != sorted(R + p for p in standing) or (bool(standing) != (R + ROLE['seal off'] in named('seal timer'))) or not 5.0 <= delay('seal timer') <= 600.0:
        fail('the seal: %s stand, the DeactivateGeom names %s, the clock (%.0f s) names it: %s' % (
            [p.split('\\')[-1] for p in standing], [s.split('\\')[-1] for s in off_], delay('seal timer'), R + ROLE['seal off'] in named('seal timer')))
    last = {p: [v[MPA_LAST] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, p)] for p, _at, _set in LEAVES}
    if animate and (sorted(named('doors')) != sorted(R + p for p, _at, _set in LEAVES) or any(v != [DOOR_LAST] for v in last.values())
                    or R + ROLE['doors'] not in named('doors timer') or R + ROLE['muffle'] not in named('doors timer')):
        fail('the leaves stand, but their timer names %s and they store LAST %s' % ([s.split('!')[-1] for s in named('doors timer')], sorted(last.values())))
    if not animate and (named('doors') or named('doors timer')):
        fail('the leaves are sunk, but the layer still sends %d of them \'Activate\'' % len(named('doors')))
    muf = values(sc, A.node_of(sc, ROLE['muffle']), 'AIDWrapper')
    if sorted(muf[0]) != sorted(R + p for p in MUFFLE) or muf[1] != MUFFLE_MESSAGE:
        fail('the music\'s muffle switch: the wrapper sends %r to %s' % (muf[1], muf[0]))
    log('  chain: round start -> %s; -> %.0f s -> seal off %s; doors: %s; the music\'s muffle switch \'%s\' -> %d objects' % (
        [s.split('!')[-1] for s in mon], delay('seal timer'), [s.split('\\')[-1] for s in off_] or '(nothing: no piece stands)',
        'LAST %d, \'Activate\' after %.1f s' % (DOOR_LAST, delay('doors timer')) if animate else 'open at build time', muf[1], len(muf[0])))
    # ---- what never ran in Dog Days: all of a kind or none, and the beat objects in one of their two forms
    for kind, n in NEVER_RAN.items():
        got = len(kl_fa.controllers(sc, kind))
        log('  never ran in Dog Days: %-22s %d in the level (the campaign has %d)' % (kind, got, n))
        if got not in (0, n):
            fail('%d %s in the level: neither none nor the campaign\'s %d' % (got, kind, n))
    beat = [A.node_of(sc, p) for p in BEAT]
    form = [(sc.cls(k), ents[k - 1].model != 0, bool(ents[k - 1].flags & HIDDEN), kl_fa.has(sc, k, 'StartAnim')) for k in beat]
    log('  never ran in Dog Days: the beat objects: %s' % ', '.join('%s %s' % (sc.names[k], 'ZIKLNKOBJ with its StartAnim' if f[0] == 'ZIKLNKOBJ'
                                                                              else '%s, model %s, hidden %s' % (f[0], 'kept' if f[1] else 'none', f[2])) for k, f in zip(beat, form)))
    if any(f not in (('ZIKLNKOBJ', True, False, True), ('ZSTDOBJ', False, True, False)) for f in form) or len(set(form)) != 1:
        fail('the beat objects are in neither of their two forms: %s' % form)
    if len(kl_fa.controllers(sc, 'PositionLightControl')) and form[0][0] != 'ZIKLNKOBJ':
        log('  NOTE: the light show\'s controllers are in the level, the beat object they read is a still one (LIGHT_SHOW without BEAT_ANIM)')
    # ---- the enemies
    actors = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor']
    top_of = lambda k: sc.names[sc.top[k]]
    camp_sq, pol_sq = [k for k in squads if sc.names[k] in SQUADS], [k for k in squads if sc.names[k] in ARRIVE]
    more = sorted({top_of(k) for k in squads} - set(SQUADS) - set(ARRIVE))
    men = [k for k in actors if top_of(k) in SQUADS or top_of(k) in ARRIVE]
    at = lambda k: pos[ents[k - 1]]
    cover_at = []
    if squads:
        if len(camp_sq) != len(SQUADS) or len(pol_sq) not in (0, len(ARRIVE)):
            fail('%d of the %d campaign squads and %d of the %d police squads are in the level' % (len(camp_sq), len(SQUADS), len(pol_sq), len(ARRIVE)))
        f3 = {k: values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] for k in camp_sq + pol_sq}
        awake = all(f3[k] == 1 for k in camp_sq)        # a SQUADS_AWAKE build, read off the level
        on_slab = lambda p: SLAB[0][0] <= p[0] <= SLAB[0][1] and SLAB[1][0] <= p[2] <= SLAB[1][1]
        # every man on the START's mesh part and on free floor - but a policeman on the strip beside the slab stands on
        # mesh alone: there is no collision floor there (ARRIVE's ASSUMPTION; '--police-slab' has all ten on the slab)
        rows2 = kl_route.stations(lv, [START_REF] + [at(k) for k in men], opened=gates, near=30)
        strip_men = [k for k in men if top_of(k) in ARRIVE and at(k)[2] < LANE_MOUTH[2] and not on_slab(at(k))]
        off_mesh = [(k, r) for k, r in zip(men, rows2[1:]) if not (r['mesh'] and r['part'] == part and (r['reached'] or k in strip_men))]
        log('  enemies: %d campaign squads (%d men) + %d of F07\'s police squads (%d men); %d of the %d men on the mesh part of the START and on free floor '
            'within 30%s' % (len(camp_sq), sum(top_of(k) in SQUADS for k in men), len(pol_sq), sum(top_of(k) in ARRIVE for k in men), len(men) - len(off_mesh),
                             len(men), ' - %d of them police on the mesh strip beside the slab, where there is NO collision floor (ASSUMPTION: an AI walks the '
                             'mesh)' % len(strip_men) if strip_men else ''))
        for k, r in off_mesh:
            fail('%s at (%d, %d, %d): mesh %s, part %s, reached %s (gap %s)' % (sc.path[k][5:][-70:], *r['at'], r['mesh'], r['part'], r['reached'], r.get('gap')))
        # the places their routs go by (cover points, flank and defend places; a hunt's search box is a volume): the
        # police's are this file's - on that mesh part, a cover point on free floor, man and cover point clear of the van's line
        pts2, own = [], []
        for t in camp_sq + pol_sq:
            for j in range(t + 1, sc.end[t]):
                if any(sc.p.key(nm) in A.BEHAVE for nm, _b in sc.nodes[j]['ctrls']):
                    for h in sorted({h for s in A.named(sc, j) for h in sc.resolve(s)} | {c for c in range(j + 1, sc.end[j]) if sc.parent[c] == j}):
                        if sc.top[h] == t and sc.cls(h) in ('ZBoxPrimitive', 'ZSTDOBJ') and all(sc.p.key(nm) == 'RunToCoverPosInfoRout' for nm, _b in sc.nodes[h]['ctrls']):
                            pts2.append(at(h)); own.append((h, t in pol_sq, sc.names[j] == ARRIVE_START))
        rows3 = kl_route.stations(lv, [START_REF] + pts2, opened=gates, near=30) if pts2 else [None]
        away = [(h, r) for (h, _m, _c), r in zip(own, rows3[1:]) if not (r['mesh'] and r['part'] == part)]
        log('  enemies: %d places their behaviour routs go by; %d not on the START\'s mesh part%s' % (len(pts2), len(away), ''.join(
            '\n          %s (%d, %d, %d): %s off the mesh' % (sc.path[h][5:][-74:], *r['at'], r['off']) for h, r in away[:8])))
        for (h, mine_, cover), r in zip(own, rows3[1:]):
            if mine_ and not (r['mesh'] and r['part'] == part and (r['reached'] or not cover)):
                fail('the police\'s %s at (%d, %d, %d): mesh %s, part %s, on free floor %s' % (sc.path[h][5:][-60:], *r['at'], r['mesh'], r['part'], r['reached']))
        cover_at = [(sc.path[h][5:][-60:], at(h)) for h, m_, c in own if m_ and c]      # (held against the van's drive below)
        mouth = min([math.dist(p, LANE_MOUTH) for _n, p in cover_at] or [9e9])
        if pol_sq:
            log('  enemies: the police\'s %d cover points: the nearest %.1f m from the lane\'s mouth' % (len(cover_at), mouth / 100))
            if mouth < 1000.0:                          # the bank's run V2: nobody sets up before the only exit
                fail('a cover point of the police lies %.1f m from the lane\'s mouth (10 m wanted)' % (mouth / 100))
        # nothing of a squad names a node that is not there; the kinds are the ones that ran live
        kinds = collections.Counter(sc.p.key(nm) for t in camp_sq + pol_sq for j in range(t, sc.end[t]) for nm, _b in sc.nodes[j]['ctrls'])
        for t in camp_sq + pol_sq:
            for j in range(t, sc.end[t]):
                for s in A.named(sc, j):
                    if not sc.resolve(s):
                        fail('%s names %s, which is no node' % (sc.path[j][5:], s))
                    elif any(sc.top[h] == t and not sc.nodes[h]['ctrls'] for h in sc.resolve(s)) and any(sc.p.key(nm) in MESSAGE_KINDS for nm, _b in sc.nodes[j]['ctrls']):
                        fail('%s sends a message to %s, which holds no controller' % (sc.path[j][5:][-70:], s[-50:]))
        first = sorted(set(kinds) - A.PLAIN - A.BEHAVE)
        log('  enemies: controllers of the squads: %s' % dict(kinds))
        if first:
            fail('the squads hold controllers that are not kl_fa_author\'s plain squad kinds: %s' % first)
        # each squad starts as SQUADS says: in the world from the load, or waiting and named by its stage's object
        ways = [{h for s in A.named(sc, w) for h in sc.resolve(s)} for w in [j for wn in GATE_WAYS for j in sc.resolve(R + ROLE['gate'] + '\\' + wn)]]
        if len(ways) != 2 or ways[0] != ways[1]:
            fail('the gate\'s two paths do not name the same objects')
        named_by = {'office': {h for s in named('office timer') for h in sc.resolve(s)}, 'walk': {h for s in named('walk box') for h in sc.resolve(s)},
                    'floor': {h for s in named('floor box') for h in sc.resolve(s)}, 'open': ways[0] if ways else set()}
        by, mods = collections.Counter(), 0
        for t in camp_sq:
            st, child = squads_now()[sc.names[t]]
            by[st] += 1
            want = 1 if st == 'load' or awake else 0
            if f3[t] != want:
                fail('%s: ZSquadScript field %d is %s, stage \'%s\' wants %d' % (sc.names[t], SQUAD_ACTIVE, f3[t], st, want))
            if child:
                j = A.node_of(sc, sc.names[t] + '\\' + child)
                if st != 'gate' and j not in named_by[st]:          # (a gate-staged squad is named by a TriggerActorsDead of the bots step: rooms_check)
                    fail('%s\\%s is not named by the object of stage \'%s\'' % (sc.names[t], child, st))
                if kl_fa.has(sc, j, 'SquadModifierBehaviour'):
                    mods += 1
                    if values(sc, j, 'SquadModifierBehaviour')[MOD_ACTIVE] != STAGED:
                        fail('%s\\%s: SquadModifierBehaviour field %d is %s, not %s' % (sc.names[t], child, MOD_ACTIVE, values(sc, j, 'SquadModifierBehaviour')[MOD_ACTIVE], STAGED))
            elif any(sc.top[h] == t for hs in named_by.values() for h in hs):
                fail('%s is in the world from the load and named by a stage all the same' % sc.names[t])
        for t in pol_sq:
            if f3[t] or A.node_of(sc, sc.names[t] + '\\' + ARRIVE_START) not in named_by['open']:
                fail('%s: field %d is %s, its %s named by the gate: %s' % (sc.names[t], SQUAD_ACTIVE, f3[t], ARRIVE_START,
                                                                          A.node_of(sc, sc.names[t] + '\\' + ARRIVE_START) in named_by['open']))
        for role in ('walk box', 'floor box'):
            v = values(sc, A.node_of(sc, ROLE[role]), 'TriggerBox')
            if v[0] != 1 or v[BK.BOX_PER_MAN] != 0 or v[14] != 'ECPS_FA_MERCONLY':
                fail('%s: TriggerBox fields 0 / %d / 14 are %s / %s / %s (1, 0 = once, criminals only wanted)' % (ROLE[role], BK.BOX_PER_MAN, v[0], v[BK.BOX_PER_MAN], v[14]))
        wake_check(folder, sc, lv.mesh(), world_box, fail, log)          # THE WAKE FIX: each staged squad's box and backstop, none woken in sight of the box that wakes him
        # the beat's fast way: the two squads' 'wiped out' lists -> the counter of two -> the seal off and the gate's first path
        cnt = A.node_of(sc, ROLE['floors counter'])
        cv = values(sc, cnt, 'TriggerCounter')
        dead = [sc.names[t] for t in camp_sq if values(sc, t, 'ZSquadScript')[SQUAD_DEAD] == [R + ROLE['floors counter']]]
        way1, way2 = (R + ROLE['gate'] + '\\' + w for w in GATE_WAYS)
        if sorted(dead) != sorted(BEAT_SQUADS) or cv[0] != len(BEAT_SQUADS) or way1 not in cv[4] or way2 not in named('seal timer') \
                or (bool(standing) != (R + ROLE['seal off'] in cv[4])):
            fail('the beat\'s fast way: \'wiped out\' -> counter on %s; the counter counts %s and names %s; the clock names the gate: %s' % (
                [n.split('!')[-1] for n in dead], cv[0], [s.split('!')[-1] for s in cv[4]], way2 in named('seal timer')))
        log('  enemies: started: %s; %d of them by a SquadModifierBehaviour with %s (a first for a build of ours; stock Dog Days: story levels only, 19 in L02 L06 L09 L11)%s; '
            'the gate lets in %d objects by either path' % (dict(by), mods, STAGED, ' - SQUADS AWAKE: all 17 are in the world from the load' if awake else '',
                                                           len(ways[0]) if ways else 0))
        log('  the beat: %s wiped out -> counter of %d -> %s; the clock (%.0f s) -> the same' % (
            ' + '.join(n.split('!')[-1] for n in dead), cv[0], [s.split('\\')[-1].split('!')[-1] for s in cv[4]], delay('seal timer')))
        # ... and nobody who comes LATER comes into the world in view of the crew, or beside it (the bank's review round
        # 1): for each stage the places a criminal can be when it is started - Sight
        S, mesh = Sight(lv, seal_refs), lv.mesh()
        starts = [p for p in pts if p[0] > DOOR_IN[0] - 50.0 and p[2] > 2000.0]         # every start place: all of them are in the office
        def box_views(role):
            lo, hi = world_box(A.node_of(sc, ROLE[role]))
            out = []
            for x in range(int(lo[0]), int(hi[0]) + 1, 100):
                for z in range(int(lo[2]), int(hi[2]) + 1, 100):
                    hit = mesh.at(float(x), (lo[1] + hi[1]) / 2, float(z), dy=(hi[1] - lo[1]) / 2)
                    if hit:
                        out.append((float(x), hit[1], float(z)))
            return out
        way_in = [p for _n, p in ROUTE_IN]
        views = {'office': starts, 'walk': starts + way_views(mesh, way_in[:2]) + box_views('walk box'),
                 'floor': starts + way_views(mesh, way_in[:4]) + box_views('walk box') + box_views('floor box'),
                 'open': way_views(mesh, way_in) + LANE_VIEWS}
        late = [(k, SQUADS[top_of(k)][0]) for k in men if top_of(k) in SQUADS and squads_now()[top_of(k)][0] not in ('load', 'gate') and not awake] \
            + [(k, 'open') for k in men if top_of(k) in ARRIVE]
        worst, in_sight = collections.defaultdict(lambda: (9e9, 0)), []
        for k, st in late:
            p = at(k)
            eyes = [v for v in views[st] if S.seen(v, p)]
            near = min(math.dist(v, p) for v in views[st])
            worst[st] = (min(worst[st][0], near), worst[st][1] + 1)
            if eyes and top_of(k) in ARRIVE and on_slab(p) and near >= LATE_CLEAR:
                in_sight.append(k)                      # the default (ON the slab's ends), in sight - what that form costs
            elif eyes or near < LATE_CLEAR:
                fail('%s at (%d, %d, %d) comes into the world at stage \'%s\' %s' % (sc.path[k][5:][-60:], *p, st, 'in sight of %d of the %d places the crew can be '
                     'then, the first (%d, %d, %d)' % (len(eyes), len(views[st]), *eyes[0]) if eyes else '%d from such a place (%d wanted)' % (near, LATE_CLEAR)))
        log('  enemies: who comes into the world after the load, by stage (men, places the crew can be then, the nearest man to one): %s - %s' % (
            ', '.join('%s %d / %d / %d' % (st, worst[st][1], len(views[st]), worst[st][0]) for st in ('office', 'walk', 'floor', 'open') if st in worst) or 'nobody',
            'POLICE ON THE SLAB: %d of the police come into the world IN SIGHT of a place in the queue lane (the cost of the default form; --police-strip has none, and its own assumption)' % len(in_sight) if in_sight
            else 'in sight of one: see the FAIL lines' if any('comes into the world' in b for b in bad) else 'nobody in sight of one'))
        rows_ = collections.Counter((values(sc, k, 'ZSoldier')[3], values(sc, k, 'ZSoldier')[4], values(sc, k, 'ZSoldier')[7]) for k in men if top_of(k) in SQUADS)
        stock = sum(n for (skill, _a, _h), n in rows_.items() if skill == 'eCustom')
        log('  enemies: soldier rows of the campaign\'s men (skill, accuracy, health): %s' % ', '.join('%d x %s %g / %g' % (n, *r) for r, n in sorted(rows_.items(), key=lambda t: -t[1])))
        if 0 < stock < sum(rows_.values()):
            fail('%d of the campaign\'s %d men have a stock row, the others Dead Men\'s' % (stock, sum(rows_.values())))
    else:
        log('  enemies: none (a build without squads); the seal opens by its clock')
        for role, kind, f in (('office timer', 'TriggerDelay2', 4), ('walk box', 'TriggerBox', 17), ('floor box', 'TriggerBox', 17), ('floors counter', 'TriggerCounter', 4)):
            named_ = values(sc, A.node_of(sc, ROLE[role]), kind)[f]
            if V2 and role == 'walk box':               # V2: the box is the alarm too: it starts the van's timer (the show of the van, the gate, the exit line)
                named_ = [x for x in named_ if x != R + ROLE['van timer b']]
            if named_:
                fail('no squad is in the level, but %s names %s' % (ROLE[role], named_))
    if more:
        log('  enemies: squads that are not this file\'s: %s' % more[:8])
    # police who come back: the eight bodies (re/fed_respawn.md: 8 police bodies a level load) and their points, clear of the squads' men
    back_at = [pos[ents[k - 1]] for k in bodies] + [pos[ents[k - 1]] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint'
                                                    and kl_fa.node_values(sc, k)[8] == 'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH']
    near = min([math.dist(a, at(b)) for a in back_at for b in men] or [9e9])
    log('  police who come back: %d bodies, %d AFTER_DEATH points; the nearest of the squads\' men stands %s from one' % (len(bodies), back, '%d' % near if men else '-'))
    if near < POLICE_CLEAR:
        fail('police who come back: a squad\'s man stands %d from a point or body (%d wanted)' % (near, POLICE_CLEAR))
    log('  people: %d ZFFActor in %d squads + 16 player bodies (ran live: %d actors, %d squads)' % (len(actors), len(squads), ACTORS_LIVE[0], ACTORS_LIVE[1]))
    if len(actors) > ACTORS_LIVE[0] or len(squads) > ACTORS_LIVE[1]:
        fail('%d actors in %d squads: more than has run live (%d / %d)' % (len(actors), len(squads), *ACTORS_LIVE))
    # ---- the escape of this half: one van, standing; the exit box on the slab; the marker on the slab
    vans, fakes = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle'), kl_fa.controllers(sc, 'FakeTarget')
    ex = [k for k, _i, _v in kl_fa.controllers(sc, kl_fa.EXIT)]
    want_fakes = 0 if VAN_LATE else 1                   # VAN_LATE: the police have nothing to aim at (the 0x686a66 rule cannot bite with none)
    if HELI:                                            # the chopper form: no van, no FakeTarget; ONE exit trigger naming the chopper group; exactly ONE vehicle monitor
        mons = kl_fa.controllers(sc, kl_fa.MONITOR)
        hv = [k for k, _i, _v in kl_fa.controllers(sc, 'OnlineEscVehicleController')]
        if vans or len(mons) != 1 or len(ex) != 1 or len(hv) != 1 or fakes:
            fail('HELI: %d OnlineEscAnimatedVehicle, %d OnlineEscVehicleMonitor, %d exit triggers, %d OnlineEscVehicleController, %d FakeTarget (0, 1, 1, 1, 0 wanted)' % (
                len(vans), len(mons), len(ex), len(hv), len(fakes)))
        else:
            ev = values(sc, ex[0], kl_fa.EXIT)
            if [s for s in ev[2:6] if s] != [van_path()]:
                fail('HELI: the exit trigger names %s, not the chopper group' % [s for s in ev[2:6] if s])
            log('  heli: 1 chopper (%s), 1 OnlineEscVehicleMonitor, 1 exit trigger naming it; no van' % sc.names[hv[0]])
            # ---- step 3, read back from the written level: the way up is open, the boarding box and the exit box stand on the pad, the chopper's body follows its node
            per_h = collections.Counter(kl_hvk.ref(i) for s_ in hvk.shapes for i in s_.inst)
            for p_ in HELI_SUNK:
                e_ = ents[A.node_of(sc, p_) - 1]
                if pos[e_][1] > -300.0 or per_h[e_.ref]:
                    fail('HELI: %s is not sunk (y %d, %d placements)' % (p_.split(chr(92))[-1], pos[e_][1], per_h[e_.ref]))
            on_pad = lambda p_: abs(p_[0] - HELI_PAD[0]) <= HELI_EXIT[1][0] + 400.0 and abs(p_[2] - HELI_PAD[2]) <= HELI_EXIT[1][2] + 400.0 and -100.0 < p_[1] - HELI_PAD[1] < 1200.0   # M06's gameplay box stands 420 up, its PIP camera point 1050 up
            for n_ in ('Triggers!BoardingTrigger_Heli', 'Triggers!BoardingGameplayTrigger', 'PIP_Points!Boarding', HELI_CH + 'EscapeChopper_OnMap', ROLE['exit']):
                e_ = ents[A.node_of(sc, n_) - 1]
                if not on_pad(pos[e_]):
                    fail('HELI: %s stands at (%d, %d, %d), not on the pad (%s)' % (n_, *pos[e_], HELI_PAD))
            gh = A.node_of(sc, van_path()[len(R):])
            mine_ = {ents[j - 1].ref for j in range(gh, sc.end[gh])}
            n_pl = sum(1 for s_ in hvk.shapes if s_.type != kl_hvk.STATIC for i in s_.inst if kl_hvk.ref(i) in mine_)
            log('  heli: the boarding box, the PIP point, the on-map marker and the exit box are on the pad; %d sunk closures; the chopper has %d key-framed placement(s) (moved with it: see the generic placement check)' % (len(HELI_SUNK), n_pl))
            if not n_pl:
                fail('HELI: the chopper has no key-framed .HVK placement')
    elif len(vans) != 1 or len(fakes) != want_fakes or len(ex) != 1:
        fail('%d OnlineEscAnimatedVehicle, %d FakeTarget, %d exit triggers (1, %d, 1 wanted: an unused van\'s target is the 0x686a66 crash)' % (len(vans), len(fakes), len(ex), want_fakes))
    else:
        lo, hi = world_box(ex[0])
        ev = values(sc, ex[0], kl_fa.EXIT)
        in_exit = lambda p: all(lo[a] <= p[a] + (50 if a == 1 else 0) <= hi[a] for a in range(3))
        mark = pos[ents[A.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea') - 1]]
        on_slab = SLAB[0][0] <= lo[0] and hi[0] <= SLAB[0][1] and SLAB[1][0] <= lo[2] and hi[2] <= SLAB[1][1]
        log('  exit box x %d..%d, z %d..%d: on the slab %s; holds the pavement station %s, the lane\'s street end %s; it names %s; the escape marker at (%d, %d, %d)' % (
            lo[0], hi[0], lo[2], hi[2], on_slab, in_exit(ESC_AT), in_exit(ROUTE_OUT[0][1]), [s.split('\\')[-1] for s in ev[2:6] if s], *mark))
        # V2: the crew STARTS on the slab, so the box is its south part: it holds the boarding place, no START / TRAITOR point and not the lane's street end (the marker may lie beside it)
        marker_ok = in_exit(ESC_AT) if not V2 else (in_exit(BOARD_AT) and not any(in_exit(p) for p in START + TRAITOR))
        if not on_slab or not marker_ok or in_exit(ROUTE_OUT[0][1]) or [s for s in ev[2:6] if s] != [R + VAN + '\\' + VAN_GROUP] \
                or math.dist(mark, (ESC_AT[0], ESC_AT[1] + ESC_POI_UP, ESC_AT[2])) > 1.0:
            fail('the exit box / escape marker are not as this file places them (on the slab, beyond the seal, naming the one van)')
        # ---- the van on its road. kl_map_escape.van_check reads the WRITTEN files - who the exit trigger calls, the keys
        # against the road's height, the lane (five rays, every 20), the boxes at the stop, the camera's eye and sight,
        # the collision file - here on the drawn pavement (Pavement); held against the plan in van.json when test()
        # wrote one. What the PLAIN tool says is counted beside it: nothing but the missing collision floor may differ
        plan, pj = None, os.path.join(folder, 'van.json')
        if os.path.isfile(pj):
            try:
                plan = plan_of(pj)
            except ValueError as x:
                fail('the van\'s plan beside the build: %s' % x)
        else:
            log('  van: no van.json beside the build: the drive is tested as the level has it, not against a plan')
        rep, VL, plain = van_check(folder, lambda s: log('  ' + s), plan)
        for x in rep['faults']:
            fail('van: ' + x)
        floorless = ('no ground under it', 'no road within', 'the eye is outside the map')
        odd = [x for x in plain if x not in rep['faults'] and not any(w in x for w in floorless)]
        log('  van: the plain kl_map_escape.van_check (collision only) has %d fault(s): %s - each one the missing collision floor outside the slab, '
            'which the drawn pavement stands in for%s' % (len(plain), ', '.join('%d x \'%s\'' % (sum(w in x for x in plain), w) for w in floorless if any(w in x for x in plain)) or '-',
                                                       '' if not odd else '; AND %d OTHER' % len(odd)))
        for x in odd:
            fail('van (the plain tool): ' + x)
    if stop_at_all := (not HELI and len(vans) == 1 and len(fakes) == want_fakes and len(ex) == 1 and 'stop' in rep):
        if any('FAEscCameraLAST' in x for x in rep['notes']):   # MEASURED (kl_fa_bank): no such define in stock F07, F02, F05 either
            log('    (the stock form: no Dog Days Fragile Alliance level has that define - it is Dead Men\'s box, which the three car maps kept)')
        N = ESC._van_nodes(sc, sc.top[vans[0][0]])
        ends_ = sorted({o for e in VL.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(VL.scene.head)})
        K = ESC.VanKeys(VL.scene.head, VL.ents[N['V_Van_00'] - 1].raw, ends_, kl_graft.keys_tracks)
        drive = K.pos[:K.drive()]
        k_stop = K.f2p[ESC._leg_frames(sc, N['F07_Escape_Vehicle_01'])['Activate_Enter'][1]]
        wait, stop, end, board = drive[0], drive[k_stop], drive[-1], tuple(rep['board'])
        D2 = ESC.Poly([tuple(p) for p in drive])
        to_drive = lambda p: abs(D2.project(p)[1]) if 0.0 < D2.project(p)[0] < D2.len else min(math.dist(p, drive[0]), math.dist(p, drive[-1]))
        # what the van drives over: collision floor (the slab) or the drawn pavement alone; the stop on real floor
        def real_under(x, y, z):                        # kl_map_escape.Ground.under on the collision alone (no Pavement)
            fl = [h for h in _Ground.hits(VL.G, x, z) if h[1] > ESC.FLOOR and h[0] <= y + ESC.REACH]
            return (fl[-1][0], fl[-1][2]) if fl else None
        real = [real_under(p[0], p[1] + 20.0, p[2]) for p in drive]
        on = [i for i, g in enumerate(real) if g is not None]
        g = real[k_stop]
        log('  van: of the %d keys of the drive %d have a collision floor under them (x %d..%d: %s), %d the drawn pavement alone (PAVEMENT y %.0f); '
            'the stop: origin y %.1f, the floor under it y %s; keys at most %.1f off the road\'s height; drive in %.0f m, away %.0f m' % (
                len(drive), len(on), drive[on[0]][0] if on else 0, drive[on[-1]][0] if on else 0, ', '.join(sorted({VL.name(real[i][1]) for i in on})) or '-',
                len(drive) - len(on), PAVEMENT[2], stop[1], '%.1f' % g[0] if g else '-', rep['height_off'], rep['length_in'] / 100.0, rep['length_out'] / 100.0))
        if g is None or abs(stop[1] - ESC.VAN_UP - g[0]) > 3.0:
            fail('van: the standing van\'s origin (y %.1f) is not %.0f over a collision floor (%s): the crew boards on the slab' % (stop[1], ESC.VAN_UP, '%.1f' % g[0] if g else 'none'))
        # ... and what is DRAWN there (the tool's lane test sees collision only): the pavement under every wheel
        # sample of the lane, nothing of the map's models in the van's body
        try:
            dl = drawn_lane(folder, ESC.Poly([(p[0], p[1] - ESC.VAN_UP, p[2]) for p in drive]))
            log('  van: DRAWN in its lane (the map\'s models, %d triangles near it; 5 rays every %d, %d before and %d beyond): a surface within %d of the road under '
                '%d of %d samples, y %.1f..%.1f (%s); in the van\'s body (%d..%d over the road): %s' % (
                    dl['tris'], ESC.LANE_STEP, ESC.VAN_TAIL, ESC.VAN_NOSE, ESC.VAN_BODY[0], dl['floor'], dl['samples'], dl['y'][0], dl['y'][1],
                    ', '.join('%s x %d' % (n.split('\\')[-1], c) for n, c in dl['pieces'].most_common(8)), *ESC.VAN_BODY,
                    '; '.join('%s [%s] %d..%d along' % (n.split('\\')[-1], m, a, b) for n, (a, b, _c, m) in dl['body'].items()) or 'nothing'))
            if dl['floor'] != dl['samples']:
                fail('van: no drawn surface under %d of the %d wheel samples of its lane, the first %d along the drive: it would be seen driving on nothing' % (
                    dl['samples'] - dl['floor'], dl['samples'], dl['first_bare']))
            if abs(dl['y'][0] - PAVEMENT[2]) > 2.0 or abs(dl['y'][1] - PAVEMENT[2]) > 2.0:
                fail('van: the drawn surface under its lane is y %.1f..%.1f, PAVEMENT says %.1f' % (*dl['y'], PAVEMENT[2]))
            for n, (a, b, c, m) in dl['body'].items():
                fail('van: DRAWN in its lane, without collision: %s [%s] %d..%d along the drive' % (n[-60:], m, a, b))
        except (ImportError, AttributeError, KeyError, struct.error) as x:
            log('  van: what is drawn in its lane: NOT CHECKED (%s: %s)' % (type(x).__name__, x))
        # the boarding place (the box rides on the van: in the file it stands at the waiting place): a station of the
        # round - on the START's mesh part, on free floor - and reached in the collision from the queue lane
        rows4 = kl_route.stations(lv, [START_REF, board, tuple(stop)], opened=gates, near=BOARD_NEAR)
        b4 = rows4[1]
        walk = kl_route.route(lv, [ROUTE_OUT[0][1], board], opened=gates)
        on_slab_ = lambda p, pad=0.0: SLAB[0][0] + pad <= p[0] <= SLAB[0][1] - pad and SLAB[1][0] + pad <= p[2] <= SLAB[1][1] - pad
        log('  van: boarding place at the stop (%d, %d, %d): on the slab %s, mesh %s, part %s (the START\'s: %s), free floor within %d: %s; the van\'s stop: mesh %s, part %s; '
            'queue lane, street end -> boarding place in the collision (the seal out): %s; %.1f m from the lane\'s mouth' % (
                *board, on_slab_(board, 100.0), b4['mesh'], b4['part'], part, BOARD_NEAR, b4['reached'], rows4[2]['mesh'], rows4[2]['part'], say(walk), math.dist(board, LANE_MOUTH) / 100.0))
        if not (b4['mesh'] and b4['part'] == part and b4['reached'] and on_slab_(board, 100.0)):
            fail('van: the boarding place (%d, %d, %d) is no station of the round on the slab: mesh %s, part %s, reached %s (gap %s)' % (*board, b4['mesh'], b4['part'], b4['reached'], b4.get('gap')))
        if not walk['free']:
            fail('van: no free way from the queue lane to the boarding place: crossed %s' % [n for _r, n in crossing(walk)])
        # ... and the way an AI is GIVEN there stays on the slab. The pavement's mesh polygons run on beyond the slab
        # (x -3765..5786) where nothing has collision: kl_route's model of a mesh way (through the middles of the
        # polygons' shared edges) from the escape marker to the boarding place goes 17 m WEST of the slab and back
        # (MEASURED: kl_route.py walk ... --via marker --to boarding place). The straight leg from the lane does not
        off_slab = lambda leg: [p for p in way_views(lv.mesh(), leg, step=25.0) if p[2] < SLAB[1][1] and not on_slab_(p)]
        direct, by_mark = off_slab([ROUTE_OUT[0][1], board]), off_slab([ROUTE_OUT[0][1], ESC_AT, board])
        log('  van: the way an AI is given over the mesh (kl_route\'s model), lane\'s street end -> boarding place: %s; by way of the escape marker: %s' % (
            'on the slab all the way' if not direct else '%d samples OFF THE SLAB, the first (%d, %d, %d)' % (len(direct), *direct[0]),
            'on the slab all the way' if not by_mark else '%d samples off the slab (as far as x %d) - the marker is for the HUD, no station for a bot' % (
                len(by_mark), min(p[0] for p in by_mark))))
        if direct:
            fail('van: the mesh way from the lane to the boarding place leaves the slab at (%d, %d, %d): no collision floor there' % direct[0])
        # the van's own path blocker (eToggle: it blocks where the van STANDS): the boarding place must be outside it
        inside = lambda k, p, up=0.0: all(abs(sum(VL.frame(k)[0][a][b] * ((p[a] + (up if a == 1 else 0.0)) - VL.frame(k)[1][a]) for a in range(3)))
                                          <= VL.values(k)['ZBoxPrimitive[%d]' % b] for b in range(3))
        pb = N['PathBlockerVan']
        log('  van: PathBlockerVan at (%d, %d, %d) half %s: the boarding place is %s it' % (
            *VL.place(pb), tuple(round(VL.values(pb)['ZBoxPrimitive[%d]' % b]) for b in range(3)), 'INSIDE' if inside(pb, board, 50.0) else 'outside'))
        if inside(pb, board, 50.0):
            fail('van: the boarding place lies inside the van\'s path blocker: an AI heister cannot be sent there')
        # the exit box calls the van: the stock form - it holds the van's stop and its boarding place (12 of 12 stock
        # vans of F01 F04 F05 F07: kl_fa_bank L3.3); not entered from inside the lane (above)
        at_van = [in_exit(stop), in_exit(board)]
        log('  van: the exit box holds the van\'s stop %s, the boarding place %s; drive in %.1f s' % (*at_van, rep['seconds'][0]))
        if not all(at_van):
            fail('van: the exit box does not hold the van\'s stop and its boarding place (%s, %s)' % tuple(at_van))
        # the ARRIVING van and the door: its nose stops short of the line straight out of the lane's mouth
        ahead = D2.tan(D2.cum[k_stop], ESC.AXLES)
        nose = (stop[0] + ESC.GATE_NOSE * ahead[0], stop[1], stop[2] + ESC.GATE_NOSE * ahead[1])
        swept = [p for p in drive[:k_stop + 1] if on_slab_(p)] + [nose]     # (the lane runs out of the building along -z,
        x0, x1 = min(p[0] for p in swept), max(p[0] for p in swept)         # the drive along x: the rule is one of x)
        short = 0.0 if x0 <= LANE_MOUTH[0] <= x1 else min(abs(x0 - LANE_MOUTH[0]), abs(x1 - LANE_MOUTH[0]))
        log('  van: the arriving van, nose included, sweeps the slab from x %d to x %d (%.1f m of it) and stops %d short of the line straight out of the '
            'lane\'s mouth (x %d; %d wanted)' % (x0, x1, (x1 - x0) / 100.0, short, LANE_MOUTH[0], MOUTH_SIDE))
        if short < MOUTH_SIDE:
            fail('van: the arriving van passes before the lane\'s mouth or stops %d short of it (its sweep on the slab is x %d..%d, the mouth x %d; %d wanted)' % (
                short, x0, x1, LANE_MOUTH[0], MOUTH_SIDE))
        # level bounds: neither the stop nor the boarding place in a bound, warn or kill box; a bound on the drive AWAY
        # is the stock form (every stock van passes one with its passengers aboard: BOUND_AFTER), not at the stop itself
        for n, p in (('the van\'s stop', stop), ('the boarding place', board)):
            for b, lo_, hi_ in boxes:
                if all(lo_[a] <= (p[a] + (50 if a == 1 else 0)) <= hi_[a] for a in range(3)):
                    fail('van: %s lies inside %s' % (n, b))
        edge = min(board[0] - SLAB[0][0], SLAB[0][1] - board[0], board[2] - SLAB[1][0], SLAB[1][1] - board[2])
        warn = min([max(lo_[0] - board[0], board[0] - hi_[0], lo_[2] - board[2], board[2] - hi_[2]) for _b, lo_, hi_ in boxes if hi_[1] > SLAB[2]] or [9e9])
        log('  van: the boarding place is %.1f m inside the slab\'s nearest rim and %.1f m from the nearest bound or warn box' % (edge / 100.0, warn / 100.0))
        for nm, a, b in rep['bounds']:
            ok = b < 0 or a >= BOUND_AFTER
            log('  van: the drive passes the level bound %s %.1f .. %.1f m %s the stop: %s' % (
                nm.split('!')[-2] if '!' in nm else nm, abs(a) / 100.0, abs(b) / 100.0, 'before' if b < 0 else 'after',
                'the van is empty there' if b < 0 else 'players aboard - the stock form (stock vans: 10.9 .. 105 m after their stops)' if ok else 'TOO NEAR THE STOP'))
            if not ok:
                fail('van: the level bound %s lies on the drive %d .. %d from the stop (after it: at least %d)' % (nm, a, b, BOUND_AFTER))
        # nobody starts in the lane - spawn points, player bodies, the squads' men, the police's cover points - and
        # nobody is SENT into it: the escape marker and the stations of the way out (the van's kill box rides at its nose)
        sent = [('the escape marker', pos[ents[A.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea') - 1]])] + [('station \'%s\'' % n, p) for n, p in ROUTE_OUT]
        near_ = sorted((to_drive(p), n, p) for n, p in list(zip(names, pts))[1:] + [(sc.path[k][5:][-50:], at(k)) for k in men] + cover_at + sent
                       if abs(p[1] - stop[1]) < 400.0 and p[2] < LANE_MOUTH[2] + 100.0)
        mark = next(d for d, n, _p in near_ if n == sent[0][0])
        log('  van: the escape marker stands %d from the drive, %d from the boarding place at the stop' % (mark, math.dist(sent[0][1][::2], board[::2])))
        log('  van: of %d spawn points, player bodies, men, cover points, the marker and stations on the pavement the nearest to the drive is %s' % (
            len(near_), '%s, %d from it' % (near_[0][1], near_[0][0]) if near_ else '-'))
        for d, n, p in near_:
            if d < LANE_CLEAR:
                fail('van: %s at (%d, %d, %d) stands %d from the van\'s drive (%d wanted)' % (n, *p, d, LANE_CLEAR))
        # the boarding place against the police: no cover point of the arriving squads beside the rear doors, nobody
        # comes back as police beside them
        cov = min([(math.dist(p[::2], board[::2]), n) for n, p in cover_at] or [(9e9, '-')])
        back_pts = [(sc.names[k], at(k)) for k in bodies] + [(sc.names[k], at(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint'
                                                             and kl_fa.node_values(sc, k)[8].endswith(('AFTER_DEATH', 'POLICE'))]
        fed = min([(math.dist(p[::2], board[::2]), n) for n, p in back_pts] or [(9e9, '-')])
        log('  van: the boarding place and the police: the nearest cover point of the arriving squads %.1f m (%s; %.0f m wanted), the nearest point or body of '
            'police who come back %.1f m (%s; %.0f m wanted)' % (cov[0] / 100.0, cov[1][-40:], BOARD_CLEAR / 100.0, fed[0] / 100.0, fed[1][-40:], FED_CLEAR / 100.0))
        if cov[0] < BOARD_CLEAR:
            fail('van: the police\'s cover point %s lies %.1f m from the boarding place (%.0f m wanted)' % (cov[1], cov[0] / 100.0, BOARD_CLEAR / 100.0))
        if fed[0] < FED_CLEAR:
            fail('van: %s lies %.1f m from the boarding place (%.0f m wanted)' % (fed[1], fed[0] / 100.0, FED_CLEAR / 100.0))
        # is the waiting van seen from where the crew comes out? (said, not a rule: the street is straight and open)
        eyes = [('the queue lane before the seal', (118.0, 20.0 + 160.0, -2320.0)), ('the lane\'s mouth', (LANE_MOUTH[0], LANE_MOUTH[1] + 160.0, LANE_MOUTH[2])),
                ('the escape marker', (ESC_AT[0], ESC_AT[1] + 160.0, ESC_AT[2])), ('the boarding place', (board[0], board[1] + 160.0, board[2]))]
        solid = lambda e: [VL.name(r) for _d, r in VL.G.between(e, (wait[0], wait[1] + 100.0, wait[2])) if 'ColiObj' not in VL.name(r) and 'HeroColi' not in VL.name(r)]
        seen = ['%s: %s' % (n, 'hidden by %s' % solid(e)[0] if solid(e) else 'SEEN (%d m)' % (math.dist(e, wait) / 100.0)) for n, e in eyes]
        log('  van: waits at (%d, %d, %d), %.0f m from its stop, %s the navigation mesh; from %s' % (
            *wait, math.dist(wait, stop) / 100.0, 'ON' if kl_route.stations(lv, [START_REF, tuple(wait)], opened=gates, near=BOARD_NEAR)[1]['mesh'] else 'off', '; from '.join(seen)))
        # the camera: F07's own fixed escape camera, moved with the drive (cam_spot's eye)
        cam = rep.get('camera') or {}
        if cam.get('eye'):
            e = cam['eye']
            under = real_under(e[0], e[1], e[2])
            log('  van: the escape camera\'s eye (%d, %d, %d): %s over the road, %.0f m from the stop, %s; between it and the van at the stop: %s' % (
                *e, cam.get('over'), cam.get('far', 0) / 100.0, 'over the collision floor %s' % VL.name(under[1]) if under else 'over the drawn pavement (no collision under it)',
                cam.get('sight') or 'nothing'))
        else:
            fail('van: no escape camera with an eye of its own')
    # ---- the van's ZFakeTarget: inside the vision space, by kl_fa_bots_dyn's rule (the 0x686a66 crash: a target that
    # cannot register writes behind ZCheckVisible's table every frame; re/crash_686a66.md). The rule is for the place
    # at the LOAD; where the drive takes it is said beside it. And the street's ROOM: the van's three places and the
    # camera's eye inside the room box of the pavement's room (ASSUMPTION that a thing outside every room box may not
    # be drawn; MEASURED C:/kl_scratch/club/l3/s/rooms.py: M05_A_Outside_Street_01a x -6725..9275, y 20..3000, z -7075..-2490)
    try:
        import kl_fa_bots as FB, kl_fa_bots_dyn as D, kl_octree as O
        B = FB.Built(folder)
        space = D.vision_space(B)
        log('  ' + D.space_words(space)[:330])
        for f in D.fake_targets(B, space):
            good = space is not None and f['out'] is None and f['cell'][1] and f['cell_sure'][1]
            log('  FakeTarget %s at (%d, %d, %d): %s' % (f['path'].split('\\')[0], *f['at'], 'inside the vision space, kl2\'s arithmetic gives a record'
                                                      if good else 'OUTSIDE the vision space (%s)' % (f['out'],)))
            if not good:
                fail('FakeTarget %s at (%d, %d, %d) cannot register (outside by %s)' % (f['path'].split('\\')[0], *f['at'], f['out']))
            if stop_at_all and space is not None:
                later = [(n, D.outside(space, tuple(f['at'][a] + p[a] - wait[a] for a in range(3)))) for n, p in (('the stop', stop), ('the end of the drive', end))]
                log('    on the drive: %s' % '; '.join('at %s %s' % (n, 'inside' if o is None else 'outside by (%d, %d, %d)' % o) for n, o in later))
        if stop_at_all:
            slots = B.scene.slots()
            by_id = {slots[e] + 2: k + 1 for k, e in enumerate(B.ents) if e in slots}
            room = [D._record_box(b.raw)[:2] for b in O.RoomIndex.parse(B['.rmi']).boxes if by_id.get(b.room) and sc.names[by_id[b.room]].endswith(STREET_ROOM)]
            places = [('waits', wait), ('stops', stop), ('ends', end)] + ([('the camera\'s eye', tuple(cam['eye']))] if cam.get('eye') else [])
            out_ = [n for n, p in places if not any(all(abs(p[a] - c[a]) <= h[a] for a in range(3)) for c, h in room)]
            log('  van: the room box of %s (%d record(s)%s) holds: %s' % (STREET_ROOM, len(room), ': x %d..%d, y %d..%d, z %d..%d' % tuple(
                v for a in range(3) for v in (room[0][0][a] - room[0][1][a], room[0][0][a] + room[0][1][a])) if room else '',
                ', '.join('%s %s' % (n, 'NO' if n in out_ else 'yes') for n, _p in places)))
            for n in out_:
                fail('van: where it %s is outside the room box of %s' % (n, STREET_ROOM))
    except (ImportError, AttributeError) as x:
        log('  FakeTarget: NOT CHECKED (%s: %s)' % (type(x).__name__, x))
    # ---- texts
    keys = kl_fa.loc_keys(loc) or set()
    st = kl_fa.controllers(sc, kl_fa.SETTINGS)[0][2]
    for f, w in START_FIELDS.items():
        if st[f] != START_KEY % w or st[f].lower() not in keys:
            fail('settings field %d is %r%s' % (f, st[f], '' if st[f].lower() in keys else ', which is no key of the level\'s .LOC (finish() not run?)'))
    for key in TEXTS:
        if key.lower() not in keys:
            fail('text key %s is not in the level\'s .LOC (finish() not run?)' % key)
    for f, s in LINES.items():
        if st[f] != s or not kl_fa.spoken(keys, s):
            fail('settings field %d is %r, wanted %r in the .LOC' % (f, st[f], s))
    if values(sc, A.node_of(sc, ROLE['speak']), 'OnlineSpeakPlayer')[1] != EXIT_LINE or not kl_fa.spoken(keys, EXIT_LINE):
        fail('the exit line is not %s, or the .LOC does not have it' % EXIT_LINE)
    log('  texts: %d keys of the level\'s own, %d lines, the exit line' % (len(TEXTS), len(LINES)))
    # ---- weight
    for b in kl_impact.check(arch):
        fail('kl_impact: ' + b[:200])
    blocks = 32.0 + sum(size[e] + 0x60000 for e in ('.prm', '.fxc', '.anm')) / 1e6 + size['.wav'] / 1e6
    log('  chunk table: %d entries (the tools\' line: %d); .prm %.1f, .fxc %.1f, .ANM %.1f, .WAV %.1f MB; the five load blocks %.0f MB (the Retomoto build that loaded seven times in one process: %.0f)' % (
        size['entries'], kl_impact.CHUNK_SAFE, size['.prm'] / 1e6, size['.fxc'] / 1e6, size['.anm'] / 1e6, size['.wav'] / 1e6, blocks, BLOCKS_LIVE))
    if blocks > BLOCKS_LIVE:
        fail('the five load blocks are %.0f MB, more than has loaded live (%.0f)' % (blocks, BLOCKS_LIVE))
    import kl_chars as C
    E = L.Edit(folder)                                  # read only: nothing of it is saved
    dead, _saved = C.dead_indices(E.p, E.sc, E.raw, E.oct, E.extra, lambda *a: None)
    worn = os.path.isfile(os.path.join(folder, 'KLWardrobe.ini'))
    log('  chunk table: %d of its indices are dead (free for the wardrobe, which takes %d with the four plates, and the gun looks)%s' % (
        dead, WARDROBE_CHUNKS, '; KLWardrobe.ini is there - the wardrobe is in' if worn else ''))
    if size['entries'] > kl_impact.CHUNK_SAFE or (dead < WARDROBE_CHUNKS and not worn):
        fail('chunk table %d entries (line %d) with %d dead indices (the wardrobe wants %d)' % (size['entries'], kl_impact.CHUNK_SAFE, dead, WARDROBE_CHUNKS))
    # ---- THE FIX AFTER RUNS C0 - C2: guards off the doors, the late van, the reset, the voice lines, the police's posts
    fix_check(folder, sc, ents, pos, lv, squads, men, top_of, named, fail, log)
    # ---- kl_graft.verify's cross-references on the level AS WRITTEN (the build's own verify ran before finish())
    for b in BK.reverify(folder, log):
        fail('written level: ' + b[:200])
    log('kl_fa_club.check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ the checks of the fix after runs C0 - C2
FRONT_GAP = 250.0                       # the four front-office men are at least this far apart (their deck is 550 x 250). GUESS
POST_GAP_MIN = 150.0                    # two arriving policemen at least this far apart (kl_fa_bank.POST_GAP_MIN: a man is 0.5 m wide)
POINT_BLANK = 160.0                     # re/melee_damage.md: a firing soldier within this lands 100 bullets
RESET_CANNOT = ('the music\'s muffle switch (an AIDWrapper that sends \'%s\' at every round start: idempotent, nothing to put back); the squads\' '
                'own state (ZSquadScript field 3 / SquadModifierBehaviour: a hook would have to write the squads\' in-the-world flag, or the rules\' '
                'round start must re-arm them - ASSUMED, as the Vault); the floors counter and the two stage boxes (TriggerBox field 15 = 0 fires once: '
                'ASSUMED re-armed per round); the GatePath lists (one-shot, ASSUMED); the van\'s key-framed animation (re-runs at every visit: seen in C1 / C2); '
                'the loot (the rules\' money objects restart per round)' % MUFFLE_MESSAGE)


VOICE_KNOWN = ('Dialog/AllLevels/Oneliners/Japanese/Civilians/ChitChat/CellPhoneChitChat_001_JapaneseMale.wav',)
                                        # MEASURED: 5 of this clip's 648 blocks fail the ADPCM header test (step index 152 / 207 / 211 at blocks 160, 161, ...:
                                        # kl_voice.stream_clip refuses it, as it must - it would play noise). A civilians' cell-phone line; the club has no civilians.
                                        # It stays streamed (the same one club_noai had)


def streamed_singles(folder):
    """The streamed single IMA ADPCM records (0x11, one clip, not a language file's) of the folder's built .WHD -> sorted names."""
    import kl_whd, kl_snd
    f = [x for x in os.listdir(folder) if x.lower().endswith('_main.whd')]
    if not f:
        return []
    b = open(os.path.join(folder, f[0]), 'rb').read()
    return sorted(kl_snd.cs(b, r['name']).decode('latin1').replace('\\', '/') for r in kl_whd.records('dd', b).values()
                  if r['fmt'] & kl_whd.STREAMED and not r['fmt'] & kl_whd.LANGFILE and not r['fmt'] >> 24 and r['fmt'] & 0xffff == 0x11)


def fix_check(folder, sc, ents, pos, lv, squads, men, top_of, named, fail, log):
    """The rules that fail what the fix after runs C0 - C2 guards (each as the flag decides; a folder built with --legacy is judged as that):
    GUARDS_OFF the front office's four stand FRONT_CLEAR from the doors, the way in and the AI heisters' places; VAN_LATE the van is hidden at the
    load, carries no target, and is shown by the seal's timer and the wardrobe's box; RESET the round start names the reset objects first and
    they cover every geometry switch of this layer (or the switch is in RESET_CANNOT); VOICE no streamed single ADPCM line is left;
    POLICE_EAST the arriving men are east of the stop, POST_GAP_MIN apart."""
    import json
    at = lambda k: pos[ents[k - 1]]
    # ---- the guards
    if squads:
        mesh = lv.mesh()
        route = way_views(mesh, [p for _n, p in ROUTE_IN], 100.0)
        bst = []
        try:
            with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
                bst = [tuple(p) for i, s in enumerate(json.load(f)['plan']['stations']) if i >= 2 for p in s['places']]
        except (OSError, ValueError, KeyError):
            pass
        doors = [a for _p, a, _w in LEAVES]
        front = [k for k in men if top_of(k) in FRONT_SQUADS]
        dist = lambda p, pts: min(math.dist(p, q) for q in pts) if pts else 9e9
        rows = [(k, dist(at(k), doors), dist(at(k), route), dist(at(k), bst)) for k in front]
        log('  guards: the %d men of the front office\'s two squads: nearest door %s, nearest place of the way in %s, nearest place of an AI heister %s (%d wanted)%s' % (
            len(front), '%d' % min(r[1] for r in rows), '%d' % min(r[2] for r in rows), '%d' % min(r[3] for r in rows) if bst else '- (no bots.json)', FRONT_CLEAR,
            '' if GUARDS_OFF else ' - GUARDS_OFF is off in this build: reported, not judged'))
        if GUARDS_OFF:
            if len(front) != 4:
                fail('guards: %d men in the front office\'s two squads, 4 wanted' % len(front))
            for k, dd, dr, db in rows:
                for what, d in (('a door of the offices', dd), ('the way in', dr), ('a place of an AI heister', db)):
                    if d < FRONT_CLEAR:
                        fail('guards: %s at (%d, %d, %d) is %d from %s (%d wanted: the point-blank ring is %d)' % (sc.path[k][5:][-50:], *at(k), d, what, FRONT_CLEAR, POINT_BLANK))
            gap = min([math.dist(at(a), at(b)) for i, a in enumerate(front) for b in front[i + 1:]] or [9e9])
            log('  guards: the four stand %d apart at least (%d wanted)' % (gap, FRONT_GAP))
            if gap < FRONT_GAP:
                fail('guards: two of the front office\'s men stand %d apart (%d wanted)' % (gap, FRONT_GAP))
        rest = [k for k in men if top_of(k) in SQUADS and top_of(k) not in FRONT_SQUADS]
        ring = [k for k in rest if dist(at(k), route) < POINT_BLANK + 90.0]
        log('  guards: %d of the other %d campaign men stand within %d of a place of the way in (reported, not judged: the walkway\'s and the dance floors\' men '
            'stand on the way by the map\'s design)' % (len(ring), len(rest), POINT_BLANK + 90.0))
    # ---- the police's posts
    pol = [k for k in men if top_of(k) in ARRIVE]
    if pol:
        gap = min([math.dist(at(a), at(b)) for i, a in enumerate(pol) for b in pol[i + 1:]] or [9e9])
        west = [k for k in pol if at(k)[0] < 0.0]
        log('  police: %d arriving men, %d west of x 0, the nearest two %d apart (%d wanted)%s' % (len(pol), len(west), gap, POST_GAP_MIN,
                                                                                              '' if POLICE_EAST else ' - POLICE_EAST is off in this build: reported, not judged'))
        if POLICE_EAST and POLICE_ON_SLAB and (west or gap < POST_GAP_MIN):
            fail('police: %d men west of x 0 (the van\'s drive), the nearest two %d apart (%d wanted)' % (len(west), gap, POST_GAP_MIN))
    # ---- the late van
    named_by = collections.defaultdict(list)
    for kk in range(1, len(sc.nodes)):
        for s_ in A.named(sc, kk):
            named_by[s_].append(kk)
    van = van_path()
    vg = sc.resolve(van)[0] if sc.resolve(van) else None
    if VAN_LATE and vg is not None:
        hidden = bool(ents[vg - 1].flags & HIDDEN)
        if not hidden:
            fail('VAN_LATE: the van\'s group is not hidden at the load')
        von, t1, t2 = (A.node_of(sc, ROLE[r]) for r in LATE_ROLES)
        if values(sc, von, 'ActivateGeom')[1] != [van]:
            fail('VAN_LATE: \'van on\' names %s, not the van\'s group' % values(sc, von, 'ActivateGeom')[1])
        seal_named = [named_by.get(R + ROLE['van timer'], [])]
        starters = set(named_by.get(R + ROLE['van timer'], ()))
        want = {A.node_of(sc, ROLE['monitor'])} if V2 else {A.node_of(sc, ROLE['seal timer'])} | ({A.node_of(sc, ROLE['floors counter'])} if squads else set())
        if starters != want:
            fail('VAN_LATE: the van\'s timer is named by %s, wanted the seal\'s clock%s' % (sorted(sc.names[x] for x in starters), ' and the beat\'s counter' if squads else ''))
        early = {A.node_of(sc, ROLE['walk box'])} if V2 else {A.node_of(sc, ROLE['speak box'])}      # (V2: the alarm = the first criminal through the inner office door)
        if set(named_by.get(R + ROLE['van timer b'], ())) != early:
            fail('VAN_LATE: the early timer is not named by %s alone' % ('the box at the inner office door' if V2 else 'the wardrobe box'))
        if [R + ROLE['van on']] != values(sc, t1, 'TriggerDelay2')[4] or R + ROLE['van on'] not in values(sc, t2, 'TriggerDelay2')[4]:
            fail('VAN_LATE: a van timer does not name \'van on\'')
        if any(sc.names[sc.top[x]].startswith(tuple(SQUADS) + tuple(ARRIVE)) for x in named_by.get(van, ())):
            fail('VAN_LATE: a squad names the van')
        log('  van: hidden at the load (%s), no FakeTarget, shown %g s after the seal opens (clock%s) or %g s after the wardrobe\'s box (V2: the van timer also runs %g s after EVERY round start); nothing of a squad names it' % (
            hidden, VAN_AFTER, ' / counter' if squads else '', VAN_EARLY, VAN_SHOW_V2))
    elif not VAN_LATE:
        log('  van: VAN_LATE is off in this build: the van stands in the world from the load with its target')
    # ---- the reset
    if RESET:
        mon = values(sc, A.node_of(sc, ROLE['monitor']), 'AIMonitor')[2]
        first = [R + ROLE[r] for r in RESET_ROLES]
        shown = [x for x in first if x in mon]
        if mon[:len(shown)] != shown or len(shown) != (2 if (VAN_LATE and gate()) else 1 if (VAN_LATE or gate()) else 0):
            fail('RESET: the round start\'s list begins %s, wanted %s first' % ([s[5:].split('!')[-1] for s in mon[:3]], [s.split('!')[-1] for s in first]))
        mod = [A.node_of(sc, ROLE[r]) for r in ROLE if r not in RESET_ROLES]
        for t in sc.tops():
            if sc.names[t] in SQUADS or sc.names[t] in ARRIVE:
                mod += list(range(t, sc.end[t]))
        off, on = [], []
        for kind, into in (('DeactivateGeom', off), ('ActivateGeom', on)):
            for kk, _i, v in kl_fa.controllers(sc, kind):
                if kk in mod:
                    into += [s for s in v[1] if s not in into]
        got_show = values(sc, A.node_of(sc, ROLE['reset show']), 'ActivateGeom')[1]
        got_hide = values(sc, A.node_of(sc, ROLE['reset hide']), 'DeactivateGeom')[1]
        miss = [s for s in off if s not in got_show] + [s for s in on if s not in got_hide]
        extra = [s for s in got_show if s not in off] + [s for s in got_hide if s not in on]
        if miss or extra or [s for s in got_show if s in got_hide]:
            fail('RESET: the layer switches %d objects off and %d on; the reset shows %d and hides %d; not covered %s, not switched %s, both ways %s' % (
                len(off), len(on), len(got_show), len(got_hide), [s.split('\\')[-1] for s in miss], [s.split('\\')[-1] for s in extra], [s for s in got_show if s in got_hide]))
        log('  reset: the round start names %s first; it shows %d again (%s) and hides %d again (%s); every geometry switch of the layer is covered'
            % ([s.split('!')[-1] for s in shown], len(got_show), ', '.join(s.split('\\')[-1] for s in got_show) or '-', len(got_hide), ', '.join(s.split('\\')[-1] for s in got_hide) or '-'))
        log('  CANNOT BE RESET BY DATA: ' + RESET_CANNOT)
    else:
        log('  reset: RESET is off in this build: round 2 starts with the seal gone')
    # ---- the voice
    left = [n for n in streamed_singles(folder) if n not in VOICE_KNOWN]
    log('  voice: %d streamed single IMA ADPCM line(s) left in the built .WHD%s' % (len(left), '' if VOICE else ' - VOICE is off in this build: reported, not judged'))
    if VOICE and left:
        fail('voice: %d streamed single IMA ADPCM lines are left (Dog Days cannot read them from the stream file): %s' % (len(left), left[:3]))


def inventory(folder, log=print):
    """What the layer consists of in a built level, with world places read back from it."""
    sc, _scene, ents, pos, _hvk, _snd, _loc, _size = BK.read_built(folder)
    at = lambda k: '(%6d %6d %6d)' % tuple(round(x) for x in pos[ents[k - 1]])
    ctl = lambda k: ','.join(sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls'])
    half = lambda k: ' half %s' % (tuple(round(x) for x in kl_fa.node_values(sc, k)[8:11]),) if sc.cls(k) == 'ZBoxPrimitive' else ''
    def row(k, note=''):
        log('  %-74s %-22s %s%s %s %s' % (sc.path[k][5:][-74:], sc.cls(k), at(k), half(k), ctl(k), note))
    def targets(k):
        for s in A.named(sc, k)[:20]:
            log('        -> %s%s' % (s[5:][-110:], '' if sc.resolve(s) else '   NOT IN THE LEVEL'))
    log('SPAWN POINTS (ZSpawnPoint) and player groups')
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint':
            row(k, kl_fa.node_values(sc, k)[8].replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''))
        elif sc.parent[k] == 0 and sc.names[k].startswith('Heroes!'):
            row(k)
    log('PLACED HOST OBJECTS (PLACE; source of each number in the table)')
    for name, (_p, _f, _h, why) in place_now().items():
        row(A.node_of(sc, name), '<- ' + why)
    log('KILL BOXES (the campaign\'s, re-placed)')
    for name, (_p, _h, why) in KILL.items():
        row(A.node_of(sc, name), '<- ' + why)
    log('LOOT (OnlineMoneyCtrl that is no drop pool)')
    total = 0
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' not in v[2]:
            total += v[1]
            row(k, '%s %d model %d%s' % (v[2][16:], v[1], ents[k - 1].model, ' HIDDEN at start' if kl_fa.node_values(sc, k)[3] else ''))
    pools = collections.Counter(v[0][20:] for _k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2])
    log('  loot %d; drop pools left: %s' % (total, dict(pools)))
    log('THE CHAIN (ROLE) and what each object names')
    for role, name in ROLE.items():
        k = A.node_of(sc, name)
        row(k, '= ' + role)
        targets(k)
    log('ESCAPE (in the file the van and its boarding box stand at the waiting place; the boxes beside the drive at the stop)')
    for k in range(1, len(sc.nodes)):
        names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if any(n in names for n in (kl_fa.EXIT, kl_fa.MONITOR, 'OnlineEscAnimatedVehicle', 'FakeTarget')) or sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k]:
            row(k)
    log('LEVEL BOUNDS')
    for k, _i, _v in kl_fa.controllers(sc, 'LevelBound'):
        row(k)
    log('DOORS AND THE SEAL')
    for path, _stock, name in LEAVES + SEAL:
        k = A.node_of(sc, path)
        log('  %-20s %-48s %s' % (name, sc.path[k][-48:], at(k)))
    log('WHAT NEVER RAN IN DOG DAYS')
    for kind in NEVER_RAN:
        log('  %-22s %d' % (kind, len(kl_fa.controllers(sc, kind))))
    for p in BEAT:
        row(A.node_of(sc, p))


def build(out, log=print, plan=None):
    """F07 + M05_A with the layer into <out>/F07+M05_A campaign -> (kl_maps.one's result, that folder, the van's
    plan, kl_map_escape's report of what it did to the van). The build's own arguments: M_DROP, and - unless
    BEAT_ANIM - the two beat objects loaded as plain objects (kl_maps' 'flat', with the class pair IK lent to
    kl_maps.FLAT for the call, as kl_fa_bank lends kl_fa_author its squad roots). plan: a plan of ROAD (plan_of /
    van_plan); None = made here, on a BARE graft of the two levels built into <out>/_bare (35 s, 284 MB) and deleted
    again - the plan needs a built level's collision and must not see the layer's own van (van_plan)."""
    import shutil
    if HELI:
        return heli_build(out, log)
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', m_drop=M_DROP)
        try:
            if not r.get('ok'):
                raise ValueError('kl_fa_club: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    flat = () if BEAT_ANIM else (IK[0],)
    lent = [c for c in flat if c not in kl_maps.FLAT]
    for c in lent:
        kl_maps.FLAT[c] = IK[1]
    r, st = {}, {}
    import kl_snd
    kl_snd.VOICE = True if VOICE else None              # the speech repairs of re/voice.md (kl_maps.ready_one's way): streamed single ADPCM lines -> the .WAV
    try:
        with ESC.van_layer(plan, log) as st, doors(log):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_club', m_drop=M_DROP, flat=flat)
    except ValueError:                                  # van_layer: 'a step of the van did not run'. After a build that
        if r.get('ok') or not r:                        # failed (r says why) that is no news; after one that did not, it is
            raise
    finally:
        kl_snd.VOICE = None
        for c in lent:
            del kl_maps.FLAT[c]
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


def heli_build(out, log=print):
    """STEP 2 of the heli chain: R09 (the donor step's F07 + the chopper, built here when PSEUDO has no R09) + M05_A with the club's author, HOST = 'R09'
    (kl_graft runs prepare_host only when S is HOST). No plan of a road, no van_layer, no van-slab pre-pass; kl_hvk_donor.patched() for the .HVK join
    (the chopper has no static placement). -> (kl_maps.one's result, <out>/R09+M05_A heli, None, {'van': None, 'wired': None, 'hvk': 'donor'})."""
    global HOST
    import kl_hvk_donor, kl_snd
    if 'R09' not in kl_maps.PSEUDO or not os.path.isfile(os.path.join(kl_maps.PSEUDO['R09'], 'R09_Main.zip')):
        d = heli_donor(out, log)
        if not d.get('ok') or d.get('problems'):
            return dict(d, ok=False, error=d.get('error') or 'the donor step left problems: %s' % d.get('problems'), where=d.get('where')), '', None, {}
    flat = () if BEAT_ANIM else (IK[0],)
    lent = [c for c in flat if c not in kl_maps.FLAT]
    for c in lent:
        kl_maps.FLAT[c] = IK[1]
    real_host, r = HOST, {}
    HOST = 'R09'                                        # the author's HOST: the second step's S is the pseudo level
    kl_snd.VOICE = True if VOICE else None
    try:
        with kl_hvk_donor.patched(), heli_hvk_layer(log), doors(log):
            r = kl_maps.one(out, 'R09', LEVEL, keep=True, campaign=True, tag=' heli', author='kl_fa_club', m_drop=M_DROP, flat=flat,
                            nav_base=kl_maps.nav_of('R09'))
    finally:
        HOST = real_host
        kl_snd.VOICE = None
        for c in lent:
            del kl_maps.FLAT[c]
    return r, os.path.join(out, 'R09+%s heli' % LEVEL), None, {'van': None, 'wired': None, 'hvk': 'donor'}


def van_check(folder, log=print, plan=None):
    """kl_map_escape.van_check on a built folder with the drawn pavement as the road (Pavement) -> (its report, the
    Level it read, how many keys of the drive have NO collision floor under them: each of those is a fault of the
    plain 'kl_map_escape.py van-check', and the only kind it has here)."""
    L = ESC.Level(folder)
    with pavement():
        rep = ESC.van_check(L, log, plan)
    bare = [x for x in ESC.van_check(ESC.Level(folder), lambda *a: None, plan)['faults']]
    return rep, L, bare


# ------------------------------------------------------------------ the finishing chain's bots (re/club_campaign.md 'Stage F')
# kl_fa_bots.RECIPE has no M05_A row, so the options come from here (as kl_fa_bank.BOT_OPT does): ONE loot stop (the office, where
# the richest six cases are: the bots start beside them; the bar's, the ticket counter's and the coat check's cases are left to
# the loot tactic, which takes what lies within its window on the way) and a loot wait of 30 s.
# GUESS: the bots end beside the van's lane. kl_fa_bots wants the AllyEscapeBox PARK_SIDE (420) to the side of the van's line
# (z -3100) and the slab is only 800 wide, so the place is chosen by hand. REVIEW ROUND 2: the first form (-640, -2720) stood 3.6 m
# from the west police's cover point (-1000, -2680) and 5 m from their men - bots_check now holds BOT_PARK against every police place
# (PARK_POLICE_CLEAR). On the lane's own side of the van's road (the south side, tried first, made all seven squads CROSS the road the
# van drives, and stood 0.8 m from the rim): slab's middle, 2.5 m north of the van's line (= LANE_CLEAR), 10.1 m
# 10 m or more from every place the arriving police run to or start at (x 0 was 9.5 m from a man), 7.9 m from the nearest place police come back at.
BOT_PARK = (60.0, ESC_AT[1], -2850.0)
PARK_POLICE_CLEAR = 1000.0              # no cover point, defend place or start place of the ARRIVING police nearer than this to BOT_PARK (10 m). GUESS
PARK_FED_CLEAR = 700.0                  # ... nor a place police COME BACK at (a dead human's respawn: once, later in a round) nearer than this (7 m): the arriving police's
                                        # west places end at x -950 and the returning ones begin at x 850 (z -2795), so no spot north of the van's road is 10 m
                                        # from both. GUESS
BOT_OPT = {'stops': 1, 'cases': 'glass', 'lane': True, 'window': True, 'loot_seconds': 30,
           'park': list(BOT_PARK)}
GATE_AT = (400.0, 100.0, -150.0)        # GUESS: the entrance hall, 13 m before the queue lane (z -1500); the way station nearest to it is the hold
GATE_MORE = 0.0                         # s on top of SEAL_AT before which the QUICKEST bot must not leave the hold (review round 2: it was 5 s with
                                        # a hold made for a typical bot, so the quickest left at 115 s, 5 s before the clock). GUESS
GATE_SPEED = 400.0                      # units a second the FASTEST bot is taken to walk from the start to the hold (the step is a walk, not a sprint). GUESS:
                                        # an estimate that is too high only makes the hold longer for every bot
GATE_SLOW = 200.0                       # units a second the SLOWEST bot is taken to walk (a path that winds: the straight way is only its lower bound). GUESS
# (a GATE_LOOT_TYPICAL of 15 s, used by review round 1 for the hold, is gone: round 2 makes the hold for the QUICKEST bot, see bots_gate)
GATE_LOOT_MIN = 5.0                     # s the quickest bot spends there. GUESS
GATE_LATE = 50.0                        # s after SEAL_AT + GATE_MORE the SLOWEST bot may leave the hold at most (bots_check). GUESS
GATE_MIN = 10.0                         # s: no hold shorter than this
GATE_NAME = '040_Timer_seal_opens'      # no 'done_looting' in it: kl_fa_bots.check and kl_fa_bots_dyn take it for a wait that is no loot wait


def bots_gate(B, P, log=print):
    """kl_fa_bots' plan P of built level B with the SEAL GATE -> P (changed in place). The round's beat seals the entrance from the
    load; it opens when both dance-floor squads are dead or SEAL_AT seconds after the round-start event, whichever comes first.
    Nothing is known to stop an AI at the heroes-only seal, but the bots should come to the queue lane when it is open and not
    before: after the loot stop the way station nearest GATE_AT is a hold (stop 1) of plain-timer seconds = SEAL_AT + GATE_MORE minus
    the time the QUICKEST bot needs to be there (kl_fa_bots' start delay + GATE_LOOT_MIN at the loot + the straight way / GATE_SPEED;
    review round 2: made for a typical bot the first form let the quickest leave 5 s before the clock),
    then the way out. (Review round 1: the first form left out the loot wait. The hold's timer starts when a bot ARRIVES, so the
    bots leave spread out: the quickest not before SEAL_AT, the slowest GATE_LATE s after SEAL_AT + GATE_MORE at most - bots_check says
    so with the plan's own numbers, written to the report as plan['gate'].) With SEAL_OPEN there is no seal: the hold is GATE_MIN."""
    if ROOM_GATES:
        return bots_gate_rooms(B, P, log)
    loot = [i for i, s in enumerate(P['stations']) if s['kind'] == 'loot']
    if len(loot) != 1 or len(P['waits']) != 1 or P['waits'][0]['cases'] or not P['waits'][0]['loot']:
        raise ValueError('kl_fa_club.bots_gate: the plan has %d loot stations and %d waits (wanted: one stop with loot, no case)' % (len(loot), len(P['waits'])))
    out = [i for s in P['steps'] if s['leg'] == 'out' for i in s['stations']]
    ways = [i for i in out if P['stations'][i]['kind'] == 'way']
    if not ways:
        raise ValueError('kl_fa_club.bots_gate: the way out has no way station to hold at')

    def mid(i):
        pl = P['stations'][i]['places']
        return [sum(p[k] for p in pl) / len(pl) for k in range(3)]
    i_gate = min(ways, key=lambda i: math.dist(mid(i), GATE_AT))
    if math.dist(mid(i_gate), GATE_AT) > 600.0:
        raise ValueError('kl_fa_club.bots_gate: the nearest way station to %s is %d away' % (GATE_AT, math.dist(mid(i_gate), GATE_AT)))
    first = [s for s in P['steps'] if s['leg'] == 'in']
    before = [i for i in out if i <= i_gate]
    after = [i for i in out if i > i_gate]
    if not after:
        raise ValueError('kl_fa_club.bots_gate: nothing is left to walk after the hold')
    b0 = P['bots'][next(iter(P['bots']))]
    pts = [b0['start']] + [b0['places'][i] for s in first for i in s['stations']] + [b0['places'][i] for i in before]
    straight = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    start = float(P['options'].get('start_delay', 10.0))
    loot_cap = float(P['options'].get('loot_seconds', 20))
    seconds = GATE_MIN if SEAL_OPEN else max(GATE_MIN, math.ceil(SEAL_AT + GATE_MORE - start - min(GATE_LOOT_MIN, loot_cap) - straight / GATE_SPEED))
    steps = [dict(s) for s in first]
    for k in range(0, len(before), 3):
        steps.append({'name': '%03d_DefendBehaviour_to_loot' % (30 + k // 3), 'leg': 'in', 'stop': 1, 'stations': before[k:k + 3]})
    for m, k in enumerate(range(0, len(after), 3)):
        steps.append({'name': '%03d_DefendBehaviour_out' % (50 + m), 'leg': 'out', 'stop': None, 'stations': after[k:k + 3]})
    P['steps'] = steps
    P['waits'] = [P['waits'][0], collections.OrderedDict(name=GATE_NAME, stop=1, seconds=seconds, loot=[], worth=0, timer='038_Timer_at_cases',
                                                       relays=[], cases={})]
    P['stations'][i_gate]['what'] = 'the hold before the queue lane until the seal is open (%g s)' % seconds
    P['gate'] = {'station': i_gate, 'seconds': seconds, 'straight': round(straight), 'seal_at': SEAL_AT, 'seal_open': SEAL_OPEN, 'start': start, 'loot_cap': loot_cap, 'places': P['stations'][i_gate]['places']}
    note = ('THE SEAL GATE: station %d (round %s) is a hold of %g s, a plain timer (%s) that starts when the bot ARRIVES: SEAL_AT %g s + %g, minus the '
            'start delay %g s, the quickest bot\'s loot wait of %g s and the fastest bot\'s straight way of %d / %g%s'
            % (i_gate + 1, tuple(round(v) for v in mid(i_gate)), seconds, GATE_NAME, SEAL_AT, GATE_MORE, start, min(GATE_LOOT_MIN, loot_cap), straight,
               GATE_SPEED, ' (--seal-open: no seal, the shortest hold)' if SEAL_OPEN else ''))
    P['notes'].append(note)
    log('  NOTE ' + note)
    log('steps: %s' % [(s['name'], s['stations']) for s in steps])
    return P


def bots(src, dst, log=print):
    """The seven AI heisters into a COPY of a finished build of this level: kl_fa_bots.build with BOT_OPT and the seal gate
    (bots_gate) -> (kl_fa_bots' findings, its report). The dynamic step, guns and the rest are the other tools' own commands."""
    import kl_fa_bots as F
    plan0, apply0 = F.plan, F.apply
    F.plan = lambda B, opt=None, log=print: bots_gate(B, plan0(B, opt, log), log)
    if ROOM_GATES:                              # the rooms' TriggerActorsDead nodes: kl_fa_bots_rt.Street's gate_nodes, called by apply (its `more`)
        import kl_fa_bots_rt as RT
        F.apply = lambda B, P, dst_, log_=print, more=None: apply0(B, P, dst_, log_, more=club_street(RT, P['club_gates']))
    try:
        return F.build(src, dst, dict(bot_opt(), loot_seconds=LOOT_SECONDS), log)
    finally:
        F.plan, F.apply = plan0, apply0


def club_street(RT, gates):
    """kl_fa_bots_rt.Street for the club's gates; with PRESSURE a gate's TriggerActorsDead also names (next list, field 2) the squad modifiers of the squads
    that are awake at the NEXT room's hold (g['wake']): the gate before a room wakes its men. Idempotent for the seven bot squads' seven copies (ASSUMED)."""
    from kl_prp import units

    class ClubStreet(RT.Street):
        def gate_nodes(self, M, tops):
            super().gate_nodes(M, tops)
            if not PRESSURE:
                return
            n = 0
            for top in tops:
                for kid in top.kids:
                    g = next((g_ for g_ in self.gates if g_['wait'] == kid.name), None)
                    i = next((i for i, (nm, _b) in enumerate(kid.ctrls) if M.p.key(nm) == 'TriggerActorsDead'), None)
                    if g is None or i is None or not g.get('wake'):
                        continue
                    nxt = [M.p.key(tok) for tok in [list(u) for u in units(kid.ctrls[i][1][1:-1])][2][1:]]
                    M.set(kid, 'TriggerActorsDead', {2: nxt + [w for w in g['wake'] if w not in nxt]})
                    n += 1
            import kl_fa_bots as F
            want = len([g for g in self.gates if g.get('wake')]) * len(F.BOTS)
            if n != want:
                raise ValueError('kl_fa_club.club_street: %d TriggerActorsDead lists got the squads of their rooms, wanted %d' % (n, want))
    return ClubStreet(None, None, gates)


def dyn(src, dst, log=print):
    """kl_fa_bots_dyn.build (the chain's dynamic step) with ONE difference while ROOM_GATES: no bot gets a hold at cover or a hold timer behind the
    last loot wait (kl_fa_bots_dyn.PERS' out_holds False for the seven, for the call only). Behind the loot the chain is the rooms' gates, each a
    hold of the planner's choosing (against the trigger boxes and the men), and a hold of the dynamic step - a cover of ITS choosing and a timer of 4 .. 8 s - between two
    gates would be a second wait for a bot that has just been let go (kl_fa_bots_rt's review, D3; the Retomoto builds have none). What the step
    still adds behind the gates: the stagger at the start, the forks (RandomTrigger between the places of a leg: another corridor of the mesh).
    -> (findings, report) as kl_fa_bots_dyn.build."""
    import kl_fa_bots_dyn as D
    saved, llw = D.PERS, D.last_loot_wait
    if ROOM_GATES:
        # (kl_fa_bots_dyn takes the LAST TriggerActorsDead of a squad's last chain for 'the last loot wait' - its reading of --wait-guards - so with
        # the rooms' gates everything up to the last gate would be 'the way in' and get holds. For the call the chain is read as one that has a
        # table and is cut off behind it: only the table's loot wait counts, the rooms are the way out, and out_holds False gives it no hold.)
        D.PERS = {n: p._replace(out_holds=False) for n, p in saved.items()}
        D.last_loot_wait = lambda flat, cut_off, timers=True: llw(flat, True, timers)
    forks0 = D.Routes.forks
    if ROOM_GATES:
        def forks(self, q, flats, pers, opt, log=print):
            # second fix (skeptic's fault 1): no fork between the loot wait and the seal hold. A fork's other way is a corridor / a moved copy of the build's way that
            # the planner never looked at: 13 of its places lay under 160 from a living guard (point-blank reach), the deck's way_b ones 34 .. 90 from men not yet named.
            # The legs BEHIND the last gate (the exit, after the seal timer: the final leg of a chain) keep their forks. A `leg` of flat_chain is the run of Defend
            # steps between two kept elements (a TriggerActorsDead gate, a timer), so the legs after the loot wait but before the final one are the gated ways.
            rep = forks0(self, q, flats, pers, opt, log)
            for flat in flats:
                last = llw(flat, True)
                n_leg = [i for i, (kind, _x) in enumerate(flat) if kind == 'leg']
                for i, (kind, leg) in enumerate(flat):
                    if kind == 'leg' and i > last and i != n_leg[-1]:
                        for pl in leg:
                            pl.pop('fork', None)
            return rep
        D.Routes.forks = forks
    try:
        return D.build(src, dst, None, log)
    finally:
        D.PERS, D.last_loot_wait, D.Routes.forks = saved, llw, forks0


def wake_step(folder, log=print):
    """THE PRESSURE FIX, last step of the chain (`kl_fa_club.py wake <folder>` = wake_step, after the dynamic step): the dynamic step rewrites a gate's TriggerActorsDead
    next list to the one step that follows and drops the squad modifiers `bots` had put into it (kl_fa_bots_dyn keeps only what its chain walk reaches), so
    the plan's wake lists (bots.json, club_gates[*]['wake']) are put back into the next list of the gate's TriggerActorsDead of each of the seven bot squads.
    Only the .prp member of the archive changes. -> 0 (1 if a gate has no TriggerActorsDead in a bot squad)."""
    import json
    import kl_fa_bots as F
    import kl_graft
    from kl_prp import Prp
    load_flags(folder)
    if not (PRESSURE and ROOM_GATES):
        log('kl_fa_club.wake %s: no pressure fix in this build: nothing to do' % folder)
        return 0
    with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
        P = json.load(f).get('plan') or {}
    gates = {g['wait']: g for g in P.get('club_gates', ()) if g.get('wake')}
    B = F.Built(folder)
    sc = B.sc
    done = collections.Counter()
    for k, i, v in kl_fa.controllers(sc, 'TriggerActorsDead'):
        g = gates.get(sc.names[k])
        if g is None or not sc.path[k][len(R):].startswith(BK.BOT_SQUAD):
            continue
        have = list(v[2])
        add = [w for w in g['wake'] if w not in have]
        if add:
            kl_fa.edit(sc, k, i, lambda us, have=have, add=add: us.__setitem__(2, kl_fa._refs(sc, have + add)))
        done[g['name']] += 1
    bad = [n for n in gates.values() if done[n['name']] != len(F.BOTS)]
    if bad:
        log('kl_fa_club.wake: gate(s) %s have a TriggerActorsDead in %s of the %d bot squads' % ([g['name'] for g in bad], [done[g['name']] for g in bad], len(F.BOTS)))
        return 1
    prp = sc.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
        raise ValueError('kl_fa_club.wake: the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    tmp = B.zp + '.wake'
    kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
    os.replace(tmp, B.zp)
    log('kl_fa_club.wake %s: %d TriggerActorsDead lists of the seven bot squads name the squads of the next room (%s); the .prp changed, nothing else' % (
        folder, sum(done.values()), ', '.join('%s -> %d squad(s)' % (n, len(g['wake'])) for n, g in gates.items())))
    return 0


def bots_check(folder, log=print):
    """What kl_fa_bots.check / kl_fa_bots_dyn.check do not know of this level, on a folder with the squad (before or after the dynamic
    step) -> list of faults: seven squads, each with ONE timer GATE_NAME of at least GATE_MIN s, started by steps whose last place lies
    in the entrance hall (within 600 of GATE_AT), and not longer than the seal's clock and the margin."""
    import kl_fa_bots as F
    B = F.Built(folder)
    sc, bad = B.sc, []

    def fail(s):
        bad.append(s); log('  FAIL ' + s)
    delay = {sc.path[k]: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    tops = [t for t in sc.tops() if sc.names[t].startswith(BK.BOT_SQUAD + 'Squad#')]
    defend = {k: v for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    if len(tops) != len(F.BOTS):
        fail('%d squads of AI heisters in the level, %d wanted' % (len(tops), len(F.BOTS)))
    n_gate, longest = 0, 0.0
    for t in tops:
        mine = range(t, sc.end[t])
        gate = [k for k in mine if sc.names[k] == GATE_NAME]
        if len(gate) != 1 or delay[sc.path[gate[0]]] < GATE_MIN:
            fail('%s: %d timer(s) %s%s' % (sc.names[t], len(gate), GATE_NAME, ' of %g s' % delay[sc.path[gate[0]]] if gate else ''))
            continue
        secs = delay[sc.path[gate[0]]]
        longest = max(longest, secs)
        ends = [B.at(sc.resolve(v[1][-1])[0]) for k, v in defend.items() if k in mine and v[1] and any(j == gate[0] for s in v[7] for j in sc.resolve(s))]
        if not ends or not all(math.dist(p, GATE_AT) <= 600.0 for p in ends):
            fail('%s: %d step(s) start %s, their last places %s: not all within 600 of %s' % (sc.names[t], len(ends), GATE_NAME,
                                                                                            [tuple(round(x) for x in p) for p in ends], GATE_AT))
        if secs > SEAL_AT + GATE_MORE:
            fail('%s: the hold of %g s is longer than the seal\'s clock (%g s) and the margin' % (sc.names[t], secs, SEAL_AT))
        n_gate += 1
    # WHEN A BOT LEAVES THE HOLD (review round 1: the hold's timer starts on ARRIVAL, so the hold alone says nothing): start delay +
    # loot wait + the walk to the hold + the hold. The quickest bot (shortest wait, GATE_SPEED) must not leave long before the
    # seal's clock; the slowest (loot deadline, GATE_SLOW) not more than GATE_LATE s after the clock and its margin.
    g = None
    try:
        import json
        with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
            g = json.load(f).get('plan', {}).get('gate')
    except (OSError, ValueError):
        pass
    if not g or 'start' not in g:
        log('  NOTE bots.json holds no timing of the gate (a build before review round 1): when the bots leave the hold is NOT CHECKED')
        window = None
    elif g.get('rooms'):
        window = None                                   # the room gates' timetable is rooms_check's (below)
    else:
        quick = g['start'] + GATE_LOOT_MIN + g['straight'] / GATE_SPEED + longest
        slow = g['start'] + g['loot_cap'] + g['straight'] / GATE_SLOW + longest
        window = (round(quick), round(slow))
        if g.get('seal_open'):
            log('  the seal is open from the load (--seal-open): the hold only spaces the bots')
        else:
            if quick < SEAL_AT + GATE_MORE - 0.1:       # (g['straight'] is rounded)
                fail('the quickest bot leaves the hold %.0f s after the round-start event, the seal\'s clock is at %g s' % (quick, SEAL_AT))
            if slow > SEAL_AT + GATE_MORE + GATE_LATE:
                fail('the slowest bot leaves the hold %.0f s after the round-start event, %g s after the seal\'s clock and its margin at most' % (slow, GATE_LATE))
        log('  the bots leave the hold %d s (quickest: start %g + loot %g + walk %.0f) .. %d s (slowest: loot deadline %g, walk at %g) after the round-start event; '
            'the seal opens at %g s or when both dance-floor squads are dead' % (quick, g['start'], GATE_LOOT_MIN, g['straight'] / GATE_SPEED, slow, g['loot_cap'], GATE_SLOW, SEAL_AT))
    # ---- ONE CLOCK (review round 2): the seal's clock and the bots' start delay both count from the round-start event only if the
    # same AIMonitor list (field 2) names the seal timer and kl_fa_bots' Timer_start_bots; the arithmetic above relies on that.
    mon = [v[2] for _k, _i, v in kl_fa.controllers(sc, 'AIMonitor')]
    seal_t, start_t = R + ROLE['seal timer'], F.R_ + F.SQUAD + 'Timer_start_bots'
    if not any(seal_t in m and start_t in m for m in mon):
        fail('the seal timer and %s are not named by the same AIMonitor list (the round-start event): the gate clocks would differ' % start_t)
    else:
        log('  clocks: the seal timer and Timer_start_bots are named by the same AIMonitor list (the round-start event, which comes before GO)')
    # ---- THE PARK PLACE against the police (review round 2): nobody the bots end beside may be within PARK_POLICE_CLEAR of a
    # place the arriving police run to or start at, or of a place police come back at (the bank's run V2 lost its crew in the mouth of its only exit)
    _sc, _scene, ents, pos, *_rest = BK.read_built(folder)
    at = lambda k: pos[ents[k - 1]]
    park = None
    try:
        import json
        with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
            park = json.load(f).get('plan', {}).get('options', {}).get('park')
    except (OSError, ValueError):
        pass
    if not park:
        log('  NOTE bots.json holds no park place: the police check of it is NOT CHECKED')
    else:
        near, back = [], []
        for name in police():
            top = A.node_of(sc, name)
            for k in range(top, sc.end[top]):
                if sc.cls(k) in ('ZBoxPrimitive', 'ZSTDOBJ', 'ZFFActor') and k != top:
                    near.append(('%s/%s' %(name.split('!')[-1], sc.names[k][-24:]), at(k)))
        back += [(sc.names[k], at(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint'
                 and kl_fa.node_values(sc, k)[8].endswith(('AFTER_DEATH', 'POLICE'))]
        back += [(sc.names[k], at(k)) for k in range(1, len(sc.nodes)) if sc.parent[k] == 0 and sc.names[k].startswith('Heroes!Henchmen_')]
        for what, pts, want in (('arriving', near, PARK_POLICE_CLEAR), ('returning', back, PARK_FED_CLEAR)):
            if not pts:
                log('  park: no place of %s police in this level (--no-ai / --no-police)' % what)
                continue
            d, who = min((math.dist((park[0], park[2]), (p[0], p[2])), n) for n, p in pts)
            log('  park: the bots end at (%d, %d, %d); the nearest of %d place(s) of %s police is %.1f m away (%s; %.0f m wanted)' % (
                *park, len(pts), what, d / 100.0, who[-50:], want / 100.0))
            if d < want:
                fail('the park place of the bots lies %.1f m from the place %s of the %s police (%.0f m wanted)' % (d / 100.0, who, what, want / 100.0))
    bad += rooms_check(folder, log)
    log('kl_fa_club.bots_check %s: %d squads, %d with the seal gate (%s, longest %g s; seal clock %g s; leaving %s): %s' % (
        folder, len(tops), n_gate, GATE_NAME, longest, SEAL_AT, '%d..%d s' % window if window else 'not checked', 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ THE ROOM GATES (after runs C3 - C4; NOT RUN IN THE GAME)
# Run C4 (the full map, idle human): all seven AI heisters dead GO+27..73 s, every one at stage 1, 271 'lost' lines, no ONE STEP; they ran the
# route into the club's 40 men without stopping anywhere and fell along it from the walkway across both dance floors. What took Retomoto's
# crew from 'six dead by GO+79..122 s' to 'nobody dead before GO+175 s' (kl_fa_bots_rt GATES; re/retomoto_bots_rooms.md, its review) is built here:
# the way from the loot to the entrance hall is cut into ROOMS by the men that defend them; before each room the seven HOLD at distinct
# cover places at its mouth, and the chain goes on only through a TriggerActorsDead that names that room's men (stock F07's own form: kl2
# 0x4afb80 / 0x8def80 - it sends its list when every named group is dead OR 0x7800 ticks = 30 s after the hold step called its place
# reached, whichever comes first). THE PLANNER IS Retomoto's: kl_fa_bots_rt.gates_plan (holds, ways, posts, trigger boxes) is IMPORTED and
# called with this level's table, through a context manager that sets four of that module's names for the call and puts them back
# (rt_for_club); kl_fa_bots_rt.py is not edited. What is different from Retomoto:
#   - the men are named ONE BY ONE (a squad spans rooms: Dance#01 stands on the walkway, dance floor 2 and dance floor 1): the table gives
#     only the room's box, floor and direction, the men of a room are those whose post lies in it (room_of) and the TAD names their groups;
#   - the planner is told that no squad is 'known' (wake_map's second map is {}): the club's 'load' squads are awake from the load and ARE
#     the fight, in Retomoto only the boardroom was; its 'not woken by any box' notes are therefore meaningless here and not logged;
#   - the gate table has the seal hold as its LAST leg: the 'car' leg of gates_plan is the hold in the entrance hall, and the seal gate that
#     was already there (GATE_NAME, a plain timer) follows it unchanged; the exit, level-exit and park stations follow that;
#   - the floors' holds are picked by pick_holds_club (the planner's own picks seven from one cover box only when the mesh round it is 4 m
#     wide - the walkway's mouth has ONE cover box): 7 places >= 80 apart, as many different cover boxes as there are, best first;
#   - POST_KEEP 400 (Retomoto 300): no hold within 4 m of a post of a man who may be alive.
# THE TIMETABLE (every number a GUESS; bots_check prints it from the plan): the seal's clock counts from the round-start event; the quickest crew
# (every room won at once, ROOM_G_MIN s a room) reaches the entrance hall at start + GATE_LOOT_MIN + walk/400 + rooms * ROOM_G_MIN and waits
# the seal hold until SEAL_AT (the hold is made for that bot); a crew that wins NOTHING loses WAIT_S = 30 s a room: start 10 + loot 18 + the
# mesh path / 200 + rooms * 30 + the hold, then the walk out - ROOM_LATEST is where it must still be at the van call.
ROOM_GATES = True                       # False ('--no-gates', '--legacy'): the way as C3 / C4 had it, and the men where they stood
ROOM_TYPICAL = 20.0                     # V2: s a typical crew is taken to spend in a room (the men fall in 20 s; the quickest 12, the clock 30). GUESS
ROOM_G_MIN = 12.0                       # s the quickest crew is taken to spend in a room (arrive, shoot, the men fall). GUESS
ROOM_WAIT_S = 30.0                      # TriggerActorsDead's own limit (READ in kl2, 0x7800 ticks); kl_fa_bots_rt.WAIT_S
ROUND_CLOCK = 360.0                     # the round's six minutes, counted here from the round-start event (8.5 s before GO: 8.5 s of margin it does not need)
ROOM_VAN_MARGIN = 75.0                  # s the van call (the exit trigger) must still come before the round's end: the van drives in (7.2 s), waits 8 s, leaves
ROOM_POST_CLEAR = 400.0                 # no hold, no station up to the seal hold within this of a post of a man who may be alive (the task's crew-check rule)
ROOM_HOLD_RING = (60.0, 240.0)          # a hold lies this far from the middle of a cover box (kl_fa_bots_rt.HOLD_RING 70..230, with a tolerance for rounding)
ROOM_NAME_SEEN = True                   # the TriggerActorsDead names only the men a hold can see (--name-all: every man of the room)
ROOM_AFTER_CLEAR = 300.0                # no hold within this of a man of an EARLIER room (he may have outlived his gate's 30 s); the other men: ROOM_POST_CLEAR
ROOM_STEP_CLEAR = 200.0                 # every place of every step between the first gate and the seal hold at least this far from every man on its floor (the holds: ROOM_POST_CLEAR)
ROOM_HOLD_SEP = 80.0                    # two holds of one room at least this far apart (kl_fa_bots.check's own number)
# ---- THE PRESSURE FIX (2026-10-12, after run C5; NOT RUN IN THE GAME). Run C5 lost all seven AI heisters GO+26..112 s, four of them within a few metres
# of each other at the walkway's gate where five to eight of the 40 awake men had a clear line to them (re/club_campaign.md 'Pressure, after run C5').
# The yardstick is the tab's Withdrawal, on which the same crew at the same dial escapes: counted with the exact ray (hvk_ray: a part blocks when
# flags & 0x20), men of the squads that are in the world at that moment, within GUN_RANGE, never more than HOLD_GUNS at a station of the heist
# and LEG_GUNS on a stretch between two (its worst, with the police there: 5). So the club is held to the same numbers:
#  1. the rooms' squads are STAGED as stock stages its squads: WAKE_AT = the gate whose hold the squad is awake at; the TriggerActorsDead of the gate
#     BEFORE it names the squad's SquadModifierBehaviour (field 4 eAM_Activate, as the 'walk' / 'floor' stages) in its next list;
#  2. the men that bear on a hold or a leg beyond the numbers, and the men that would come into the world in sight of the previous hold, stand
#     elsewhere in their room (PRESSURE_MEN, found by C:/kl_scratch/club_pressure/reloc2.py, kept here as data; rooms_check proves them);
#  3. the holds are chosen BY FIRE (rt_for_club.spots): a place with more than HOLD_GUNS guns bearing is no hold while seven others exist; where
#     they do not, the seven take the least fire and rooms_check says so.
# `--no-pressure`, `--no-gates`, `--legacy` and `--no-ai` leave all three out.
PRESSURE = True
HOLD_GUNS = 3                           # guns that may bear on a hold of the seven (Withdrawal's heist stations: 0..2, 0..3 counting every place a rout goes by)
LEG_GUNS = 4                            # ... on any stretch of the walk between two holds (Withdrawal's heist legs: 4; its worst with the police: 5)
GUN_RANGE = 6000.0                      # a gun bears within 60 m with an exact ray free (kl_fa_bank.PRESSURE_RANGE; GUESS: the AI's fire is hardly aimed beyond)
GUN_FLOOR = 1200.0                      # ... and not from a floor 12 m or more away
LEG_STEP = 300.0                        # the walk between two holds is sampled every 3 m ... 3 m: WALK_SAMPLE
# squad (short name) -> (the gate at whose hold it is awake, its start child). The gate before it wakes it. GUESS: that a TriggerActorsDead's list
# starts a SquadModifierBehaviour as the TriggerDelay2 of the 'office' stage does; if it does not, these squads never come (an emptier club).
WAKE_AT = collections.OrderedDict([
    ('YokoGuards', (5, 'SquadModifier')), ('WaitingRoom', (5, 'Alert')),            # the four on the deck over dance floor 2's south wall: asleep until the crew has left the stairs' room (SECOND FIX, skeptic's fault 2: woken by floor1s's gate they see its walk through the deck's rail, 10 -> 12 guns while a laggard is still on it; from floor1n's holds 5 of 7 see them). W = len(ROOMS) = woken by the LAST gate, named by no gate
    ('Dance#02', (3, 'Alert')),                                                    # dance floor 1's second run: floor1s
    ('Lounge#01', (4, 'Alert')), ('Lounge#02', (4, 'Alert')), ('Rave#01', (4, 'Alert')), ('Rave#02', (4, 'Alert')),   # the upper floors, over the stairs' room
    ('SurpriseStairs', (4, 'Alert')), ('Entrance', (4, 'SquadModifier'))])
PRESSURE_KNOWN = {'floor2': (5, 7), 'floor1n': (5, 8), 'floor1s': (5, 10), 'stairs': (3, 5)}                                     # gate name -> (guns on a hold, guns on a walk) that the delivered build is KNOWN to exceed the yardstick by (rooms_check fails above them: a regression guard, not a pass)
# HELI (the way UP): gate name -> (guns on a hold, guns on a walk, laggard case) the heli build is KNOWN to exceed the yardstick by - MEASURED by hold-guns on the step-4 build, NOT fixed: the lounge walk starts at the
# stairs' head (-6, 460, 850) in sight of SurpriseStairs and Lounge#01 (6 guns, 8 with the men the gate wakes); the third floor's gallery holds Rave#01 / Rave#02 (5). A regression guard, like PRESSURE_KNOWN.
HELI_KNOWN = {'lounge': (3, 6, 8), 'third': (5, 5, 5)}
PRESSURE_MEN = collections.OrderedDict()               # man's group path -> (x, y, z): the men moved by the pressure fix (found by C:/kl_scratch/club_pressure/reloc4.py on the built c_club3 club: each in his own room (room_of),
                                                        # on the START's mesh part, 90 off his floor at most, 250 from every other man, 400 from every hold, not in the front office or the entrance; kept here as data, proved by rooms_check)
PRESSURE_MEN[E2 + 'Dance#01\\Guard#08'] = (1160, 40, 3008)
PRESSURE_MEN[E2 + 'Dance#01\\Guard#10'] = (1008, 40, 2148)
PRESSURE_MEN[E2 + 'Dance#02\\Guard#01'] = (-423, 48, 1355)
PRESSURE_MEN[E2 + 'Dance#02\\Guard#09'] = (-535, 43, 1429)
PRESSURE_MEN[E1 + 'DanceFloor01!On_Dancefloor#02\\Guard#01'] = (38, 204, 432)
PRESSURE_MEN[E1 + 'DanceFloor01!On_Dancefloor#02\\Guard#07'] = (1223, 5, 796)
PRESSURE_MEN[E1 + 'DanceFloor01!On_Dancefloor#02\\Guard#08'] = (1048, 40, 2226)
PRESSURE_MEN[E1 + 'DanceFloor02!Dancefloor02a#03\\Guard#02'] = (1256, 40, 3393)
PRESSURE_MEN[E1 + 'DanceFloor02!Dancefloor02a#01\\Guard#04'] = (-349, 40, 2569)
PRESSURE_MEN[E1 + 'DanceFloor02!Dancefloor02a#01\\Guard#03'] = (579, 40, 2554)
PRESSURE_MEN[E1 + 'DanceFloor02!Dancefloor02a#01\\Guard#02'] = (28, 40, 3768)
PRESSURE_MEN[E1 + 'DanceFloor02!Dancefloor02a#02\\Guard#03'] = (889, 40, 2172)
PRESSURE_MEN[E1 + 'DanceFloor02!FatBounceronWalkway\\Guard#02'] = (1138, 363, 3066)


# ---- THE WAKE FIX (2026-10-12, after run C8; NOT RUN IN THE GAME). READ in kl2.exe (re/club_campaign.md 'Wake, after run C8'): a TriggerActorsDead / TriggerBox / TriggerDelay2 that names a
# SquadModifierBehaviour sends it 'AITrigger'; the rout's slot 26 (0x4ebed0) runs its slot 34 (0x833830 -> 0x791090), which hands the modifier's goal (kind 0) to the squad (0x7f6750);
# for a squad that is not an online client that shows every hidden member (0x7c0d50). That is the path of a Defend rout too (0x457720 -> 0x791090), and the campaign's own
# 'Alert' children of these squads are the only thing that wakes them in Dead Men. Each staged squad is now started by THREE objects, any one of which is enough (the modifier is
# 'start once': +0x42 = field 8 = 1, so the others are no-ops):
#   1. the gate before its room (the bots' TriggerActorsDead of the plan, put there by the wake step: unchanged),
#   2. a criminals-only TriggerBox on the hold area of THAT room (the room whose gate names the squad: the human who runs ahead of the bots meets the guards when he reaches the
#      place where the bots would hold; a bot that arrives first fires it too: ASSUMED that a bot counts as a criminal for ECPS_FA_MERCONLY, which only moves the wake to the bot's
#      arrival, up to 30 s before the gate's list - the laggard rule of rooms_check already covers that),
#   3. a backstop TriggerDelay2 that the round-start list starts: later than the slowest crew's gate (rooms_check: wake_min), so nobody sleeps for good.
# room (the gate whose list names the group) -> the box (centre, half-sizes: the seven holds of c_club4's plan + 100 each side, y from 40 under the lowest hold to 170 over the highest;
# found by C:/kl_scratch/club_wake/boxes.py, proved by check(): none of the group's men has an exact-ray line to a mesh point of the box) and the backstop (s after the round-start
# event: the slowest crew's arrival at that room's hold + the gate's 30 s + 3 s; rooms_check computes the minimum from the plan and fails below it).
WAKE_BOX = collections.OrderedDict([
    ('floor1n', dict(centre=(-1050.0, 105.0, 2730.0), half=(260.0, 105.0, 280.0), backstop=166.0)),      # wakes Dance#02 (awake at floor1s)
    ('floor1s', dict(centre=(-1306.5, 96.0, 1883.5), half=(258.5, 116.0, 201.5), backstop=204.0)),       # wakes the upper floors, SurpriseStairs and Entrance (awake at the stairs)
    ('stairs', dict(centre=(-201.0, 123.0, 877.5), half=(749.0, 143.0, 292.5), backstop=246.0))])        # wakes the front office's deck: YokoGuards and WaitingRoom (awake at the last hold)
WAKE_DELAY = 3.0                        # the backstop is this many seconds after the slowest crew's gate could have fired (GUESS)


def place_now():
    """PLACE with the wake fix's three boxes (WAKE_BOX) while WAKE_MORE is on."""
    t = collections.OrderedDict(PLACE)
    if WAKE_MORE:
        for i, (room, w) in enumerate(WAKE_BOX.items()):
            t[ROLE['wake box %d' % (i + 1)]] = (w['centre'], None, w['half'], 'GUESS: the hold area of the %s room (the seven holds of c_club4 + 100): the criminal who reaches it wakes the squads that are awake at the room after it' % room)
    if HELI:                                            # the exit, its area triggers and the marker are on the pad
        t.update(HELI_PLACE)
    return t


def wake_groups(plan):
    """{room: [path of the child that starts each squad, ...]} of the squads WAKE_AT stages, by the room whose gate names them (plan: squad_plan()[0])."""
    out = collections.OrderedDict((r['name'], []) for r in ROOMS)
    for n, (first, _a, _s, _k) in plan.items():
        short = n.split('!')[-1]
        if short in WAKE_AT and first:
            out[ROOMS[WAKE_AT[short][0] - 1]['name']].append(first)
    return collections.OrderedDict((r, v) for r, v in out.items() if v)


def squads_now():
    """SQUADS as the build wants them: with PRESSURE the squads of WAKE_AT are stage 'gate' (waiting, named by the gate before their room) with their
    start child; without it the table of the gates fix. -> OrderedDict name -> (stage, child)."""
    if not (PRESSURE and ROOM_GATES):
        return SQUADS
    out = collections.OrderedDict(SQUADS)
    for n in SQUADS:
        short = n.split('!')[-1]
        if short in WAKE_AT:
            out[n] = ('gate', WAKE_AT[short][1])
    return out


def wake_gate(name):
    """The gate at whose hold the squad (full path without ROOT) is awake: 0 = from the start / its box, WAKE_AT's for a gate-staged squad, 99 never (the hunters)."""
    short = name.split('!')[-1]
    if PRESSURE and ROOM_GATES and short in WAKE_AT:
        return WAKE_AT[short][0]
    return 99 if SQUADS.get(name, ('',))[0] == 'open' else 0

# the rooms, in the order of the way: name, what, box (x0, x1, z0, z1) and y of the hold places, the direction the men are in (plan), the trigger boxes
# of a LATER fight the way to the hold cannot go round (bots_rt's 'cross'; the campaign's walkway box is the stair's end). GUESS: every box and
# direction; MEASURED: the holds they give (check prints them) are on the START's mesh part, at cover boxes, 4 m and more from every living post.
ROOMS = (
    dict(name='walkway', what='the front office\'s west end, before the walkway (the bouncers of the walkway top, Yoko\'s second door)',
         box=(1350.0, 2300.0, 3000.0, 3500.0), y=360.0, enemy=(-1.0, -0.6)),
    dict(name='floor2', what='the foot of the walkway, dance floor 2\'s east end (the floor\'s bouncers, the bar)',
         box=(250.0, 950.0, 2950.0, 3500.0), y=40.0, enemy=(-1.0, -0.3), cross=('Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou',)),
    dict(name='floor1n', what='dance floor 2\'s west end (the floor\'s west, the deck over the south wall)',
         box=(-1500.0, -500.0, 2350.0, 3000.0), y=40.0, enemy=(0.0, -1.0)),
    dict(name='floor1s', what='the north-west of dance floor 1 (the second run\'s dancers, the south bar)',
         box=(-1500.0, -600.0, 1500.0, 2000.0), y=20.0, enemy=(0.0, -1.0)),
    dict(name='stairs', what='the south of dance floor 1 at the stairs\' foot (the stair landing, the wardrobe)',
         box=(-900.0, 1000.0, 400.0, 1100.0), y=40.0, enemy=(0.0, -1.0), dy=60.0))
EN_CLUB = 'AI_Players!Enemies!'

# ---- THE WAY UP (HELI; AA step 4; NOT RUN IN THE GAME). MEASURED on the heli build (mesh path loot -> pad, scratch club_heli/s4/path.py): the 248 m walk from the
# office money (2855, 342, 2439) is the van round's own first five rooms (walkway .. floor1s, then the stairs' foot: the same direction), then UP the stairs
# (7, 160, 360) -> (-13, 460, 950), the y460 corridor west to the ramp (-3837, 460, -222) -> (-2539, 860, -198), the y860 floor south to z 1700, west and
# north-east to the roof door and the pad (-3125, 860, 3860). So HELI adds two rooms behind 'stairs' (a third, the stair landing y160, has hold places only on the 3 m stair: 21 places in a 6 m strip, never seven 80 apart: its men
# SurpriseStairs / Lounge#01's east men are the 'stairs' room's): 'lounge' (the stairs' head y460: Lounge#01's third man at (-102, 479, 1510), Rave#01) and 'third' (the ramp's head y860:
# Rave#02 at (-1536, 866, 495) .. (-1879, 862, 1256), Lounge#02). Which of the planner's holds those rooms get is GUESS until bots_check ran on a build.
# Nobody lives on the y860 floor beyond z 1300, in the storage, the L-hallway or on the roof (no squad there): no gate after 'third'.
HELI_UP_Y = 700.0                       # y at and above which a man stands on the third floor (the y860 floor; the y460 corridor is 'lounge' / 'landing')
HELI_ROOMS = (
    dict(name='lounge', what='the stairs\' head on the y460 floor: the third man of Lounge#01 and the rave bar (Rave#01)',
         box=(-2300.0, -300.0, -150.0, 1250.0), y=460.0, enemy=(1.0, 0.7), dy=70.0),
    dict(name='third', what='the head of the ramp on the third floor (y 860): the rave gallery (Rave#02) and the lounge (Lounge#02)',
         box=(-2900.0, -1900.0, -450.0, 50.0), y=860.0, enemy=(0.7, 1.0), dy=70.0))
# squad (short name) -> (woken by gate number, 1-based, i.e. awake at the hold after it; its start child) for HELI. GUESS: the same Alert children as the van round
HELI_WAKE = collections.OrderedDict([
    ('Lounge#01', (5, 'Alert')), ('Rave#01', (5, 'Alert')), ('SurpriseStairs', (5, 'Alert')),                      # woken by 'stairs', awake at the 'lounge' hold (SurpriseStairs: 4 in the van round, 5 here because HELI_MEN moves its guards into the lounge, z > 900)
    ('Rave#02', (6, 'Alert')), ('Lounge#02', (6, 'Alert')),                       # woken by 'lounge', awake at the 'third' hold
    ('YokoGuards', (6, 'SquadModifier')), ('WaitingRoom', (6, 'Alert'))])         # the office deck's four: later than the van round's 5: awake at the 'third' hold, because at the 'lounge' hold the planner's way past (-142, 460, 1638) is 403 from (0, 363, 2050) and is refused (MEASURED)
# THE MEN ON THE WAY UP (MEASURED, scratch club_heli/s4/mv.py: distance of each post to the mesh path loot -> pad): Lounge#01 Guard#08 51 from it (the corner at (-48, 460, 1443)),
# SurpriseStairs Guard#01 60 / Guard#02 87 (the stairs' head), Rave#02 Guard#02 138 / Guard#07 107 (the gallery by the y860 floor). The planner refuses every hold whose way walks past a living man
# (4 m clear of a post, 'walks past its own men'), so with them in the corridor the lounge has no hold at all. Each goes to the nearest mesh point (grid 40, clearance 60) of his floor that is 600+
# from the path, in the same floor / part (found by mv.py; the originals' y: 479 / 504 / 864 / 862 -> the floor's 460 / 860). GUESS: that the mesh point is a place a man can stand (it is on the mesh) and
# that the spot is in his squad's room; the walls and the cover round it are not looked at.
HELI_MEN = collections.OrderedDict([
    (E2 + 'Lounge#01\\Guard#08', (538, 460, 1670)),
    (E1 + 'SurpriseStairs\\Guard#01', (571, 460, 1323)),
    (E1 + 'SurpriseStairs\\Guard#02', (716, 460, 976)),
    (E2 + 'Rave#02\\Guard#02', (-1364, 860, 849)),
    (E2 + 'Rave#02\\Guard#07', (-1319, 860, 976))])
HELI_GATE_AT = (-3770.0, 860.0, 3500.0)  # GUESS: 130 before the relocated ExitLootArea box (HELI_PLACE), on the path (-3774, 860, 3549); the way station nearest to it is the last hold
ROOMS_BASE, WAKE_AT_BASE, GATE_AT_BASE = ROOMS, collections.OrderedDict(WAKE_AT), GATE_AT


def set_route():
    """Put ROOMS, WAKE_AT and GATE_AT in place for the van round or the heli round (the way down to the slab / the way up to the pad). Called wherever a flag is set
    after set_roles(); idempotent. The tables are module names that every function reads at call time."""
    global ROOMS, GATE_AT
    ROOMS = ROOMS_BASE + HELI_ROOMS if HELI else ROOMS_BASE
    GATE_AT = HELI_GATE_AT if HELI else GATE_AT_BASE
    WAKE_AT.clear()
    WAKE_AT.update(WAKE_AT_BASE)
    if HELI:
        WAKE_AT.update(HELI_WAKE)


def room_of(p):
    """The room (a ROOMS name) whose men stand at post p = (x, y, z), or None: the upper floors (y >= 420: the lounge, the rave gallery, the
    stairs' balcony; they overlook, nobody reaches them) and the lane (z < -1000: the two entrance men, beyond the seal) are waited for by nobody.
    The deck over dance floor 2's south wall (y 300..420, z < 2500: the four office bodyguards of FRONT_MEN) belongs to floor1n, which they overlook."""
    x, y, z = p
    if HELI and z >= -1000.0:                           # HELI: the crew climbs through the upper floors, their men are waited for (HELI_ROOMS)
        if y >= HELI_UP_Y:
            return 'third'
        if y >= 420.0:
            return 'stairs' if (z < 900.0 and x > -400.0) else 'lounge'
    if y >= 420.0 or z < -1000.0:
        return None
    if y >= 300.0:
        return 'floor1n' if z < 2500.0 else 'walkway'
    if z >= 2550.0:
        return 'floor2'
    if z >= 1500.0:
        return 'floor1n'
    if y >= 130.0 or z < 700.0:
        return 'stairs'
    return 'floor1s'


# MEN MOVED (ROOM_GATES; computed by C:/kl_scratch/club_gates/moves.py on the finished club: of the 15 men within 250 of a place the crew walks
# - the holds, the stations and the mesh path between them - the five that have a post in the SAME room at cover (70..230 from a cover box), 4 m and more from every hold and
# station, 2.6 m from the path, on the mesh part of the START). The other ten stay (ROOM_STAY below). GUESS: the posts; MEASURED: on the mesh.
CLEAR_MEN = collections.OrderedDict([
    (E1 + 'Surprise2\\Guard#02', (634, 375, 2546)),
    (E1 + 'DanceFloor02!Dancefloor02a#01\\Guard#04', (-1699, 40, 2569)),
    (E1 + 'DanceFloor02!Dancefloor02a#01\\Guard#03', (-21, 40, 2704)),
    (E1 + 'DanceFloor02!Dancefloor02a#02\\Guard#03', (-611, 40, 2172)),
    (E2 + 'Dance#02\\Guard#09', (-1585, 21, 1129)),                 # (second fix: was (-905, 20, 809), 266 from a stairs hold; found by a search on the nav mesh, 70..230 from a cover box, 400 from every hold)
    (E2 + 'Dance#01\\Guard#10', (-342, 40, 2148))])                  # (second fix: stood at (-1302, 26, 1868), 75 .. 175 from the seven floor1s holds)
# the ten that stay within 250 of the way, and why (printed by check; each is the design of the room the crew fights through):
ROOM_STAY = ('Dance#01 Guard#01 (623, 322, 2902) on the ramp: the walkway fight itself - the hold waits for him',
             'Surprise2 Guard#01 (947, 381, 2740) on the walkway: the walkway fight',
             'FatBounceronWalkway (988, 382, 2916): the walkway fight',
             'On_Dancefloor#02 Guard#01 (488, 161, 582) and Entrance Guard#02 (-106, 182, -386): the stairs\' fight (the landing is 3 m wide)',
             'Dance#01 Guard#08 (-340, 44, 2708): his only posts in floor2 at cover lie on the way',
             'Dance#02 Guard#10 (627, 63, 1148) and Dancefloor02a#02 Guard#04 (-1132, 25, 1176): the south bar, the way passes it (the stairs holds keep 300 from them: ROOM_AFTER_CLEAR)',
             'Entrance Guard#03 (-65, 21, -1307) and Guard#01 (134, 29, -2398): the queue lane, 3 m wide: no post is 4 m from its way; they are the seal\'s other side')


class Fire:
    """Guns bearing on a place: the exact ray of third_party/anp/scripts/hvk_ray.py (a part of the level's collision blocks when flags & 0x20: MEASURED against
    five live rays) from the eyes of each man of the campaign's squads (160 over his post) to a place's chest or head (120 / 175 over its floor), within
    GUN_RANGE and not from another floor (GUN_FLOOR). A man counts when his squad is awake at the gate asked for: wake_gate (the plan) or `wake` {squad: gate}."""

    def __init__(self, B, wake=None):
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'third_party', 'anp', 'scripts'))
        import hvk_ray
        import kl_fa_bots_rt as RT
        self.B, self.col, self.men, self.cache = B, hvk_ray.Collision(B.zp), [], {}
        sc = B.sc
        for t, groups in RT.enemy_squads(B).items():
            name = sc.path[t][len(R):]
            if name.startswith(('Gameplay!', BK.BOT_SQUAD)):
                continue                                # the police that arrive and the bots are not the club's men
            for k in range(t + 1, sc.end[t]):
                if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups:
                    self.men.append(dict(squad=name, group=sc.path[sc.parent[k]], man='%s %s' % (name.split('!')[-1], sc.path[sc.parent[k]].split(chr(92))[-1]), at=B.at(k),
                                         wake=(wake or {}).get(name, wake_gate(name))))

    def sees(self, o, p):
        k = (round(o[0]), round(o[1]), round(o[2]), round(p[0]), round(p[1]), round(p[2]))
        v = self.cache.get(k)
        if v is None:
            e = (o[0], o[1] + 160.0, o[2])
            v = self.cache[k] = any(self.col.ray(e, (p[0] - e[0], p[1] + dy - e[1], p[2] - e[2]), 0x20) is None for dy in (120.0, 175.0))
        return v

    def bearing(self, p, gate, dead=()):
        """-> [(distance, man)] of the men awake at `gate` (and not in `dead`, a set of group paths) who have a free line to place p within GUN_RANGE."""
        out = []
        for m in self.men:
            if m['wake'] <= gate and m['group'] not in dead:
                d = math.dist(m['at'], p[:3])
                if d <= GUN_RANGE and abs(m['at'][1] - p[1]) < GUN_FLOOR and self.sees(m['at'], p[:3]):
                    out.append((d, m))
        return out


def gun_table(B, P, fire, log=None):
    """The table of the pressure fix for plan P of built level B -> list of per-gate dicts: the guns bearing on each of the seven holds, on the walk to it
    (every LEG_STEP along the mesh path of each bot from the place before to its hold), and who they are. `fire`: a Fire."""
    import kl_fa_bots as F
    import kl_fa_bots_rt as RT
    nav = F.Nav(B.scene.nav)
    st = P['stations']
    i_loot = max(i for i, s_ in enumerate(st) if s_['kind'] == 'loot')
    bots_ = list(P['bots'])
    prev = [tuple(P['bots'][n]['places'][i_loot]) for n in bots_]
    rows = []
    for gi, g in enumerate(P['club_gates']):
        idx = i_loot + 1 + gi
        holds = [tuple(P['bots'][n]['places'][idx]) for n in bots_]
        hold_n = [fire.bearing(h, gi) for h in holds]
        worst_leg, seen_pts, leg_pts = (0, None, []), set(), []
        for b, h in enumerate(holds):
            got = RT.way_samples(nav, prev[b], h, LEG_STEP)
            for q in (got[0] if got else []):
                key = (round(q[0] / 100), round(q[1] / 100), round(q[2] / 100))
                if key in seen_pts:
                    continue
                seen_pts.add(key)
                leg_pts.append(q)
                n = fire.bearing(q, gi)
                if len(n) > worst_leg[0]:
                    worst_leg = (len(n), tuple(round(v) for v in q[:3]), n)
        lag_pts = leg_pts + holds                           # SECOND FIX (skeptic's fault 2): the men woken by THIS gate's TriggerActorsDead (wake gi + 1) are in the world while a bot that has not
        if gi == len(P['club_gates']) - 1:                  # yet arrived (any of the seven copies fires the wake) is still on the leg or at the hold; the last gate's also on the walk to the seal hold
            seal = [tuple(P['bots'][n]['places'][idx + 1]) for n in bots_]
            for b, h in enumerate(holds):
                got = RT.way_samples(nav, h, seal[b], LEG_STEP)
                lag_pts += list(got[0]) if got else []
            lag_pts += seal
        lag_n = [(len(fire.bearing(q, gi + 1)), q) for q in lag_pts]
        lag_w = max(lag_n, key=lambda x: x[0])
        dead = {x for g_ in P['club_gates'][:gi] for x in g_['groups']}            # the men the gates before this one name: dead (or their gate's 30 s have run)
        k_hold = max(len(fire.bearing(h, gi, dead)) for h in holds) if dead else max(len(x) for x in hold_n)
        rows.append(dict(name=g['name'], holds=[len(x) for x in hold_n], hold_worst=max(len(x) for x in hold_n), leg_worst=worst_leg[0], leg_at=worst_leg[1], hold_dead=k_hold,
                         leg_dead=max([len(fire.bearing(q, gi, dead)) for q in leg_pts] or [0]) if dead else worst_leg[0],
                         who_hold=sorted(set(m['man'] for x in hold_n for _d, m in x)), who_leg=sorted(m['man'] for _d, m in worst_leg[2]),
                         hold_at=[tuple(round(v) for v in h) for h in holds], samples=len(seen_pts), lag_worst=lag_w[0], lag_at=tuple(round(v) for v in lag_w[1][:3])))
        prev = holds
    return rows


@contextlib.contextmanager
def rt_for_club(gates, men=None):
    """kl_fa_bots_rt with this level's table for one call of gates_plan: GATES, EN_ (the squads are named in full), POST_KEEP, pick_holds,
    hold_spots (the floor filter ROOMS' dy), wake_map (no squad 'known') - put back afterwards."""
    import kl_fa_bots_rt as RT
    PICK.update(gate=None, room=None, picked={}, note={}, guns={})
    saved = {k: getattr(RT, k) for k in ('GATES', 'EN_', 'POST_KEEP', 'GATE_MAX', 'pick_holds', 'hold_spots', 'wake_map', 'near_post')}
    spots0, wake0, near0 = RT.hold_spots, RT.wake_map, RT.near_post

    order = [r['name'] for r in ROOMS]

    def spots(B, nav, home, covers, g, *rest):
        out = spots0(B, nav, home, covers, g, *rest)
        out = [s for s in out if abs(s[1] - g['y']) <= g.get('dy', 150.0)]
        # second fix (skeptic's fault 2): the planner counts a squad an earlier gate waited for as dead, but a squad spans rooms here and a gate may run out its
        # 30 s with its men alive. So no hold within ROOM_AFTER_CLEAR of a man of an EARLIER room, whatever gate named him (the other men: the planner's 400)
        prior = [p for r in order[:order.index(g['name'])] for _t, _g, p in (men or {}).get(r, ())]
        return [s for s in out if not any(abs(p[1] - s[1]) <= RT.FLOOR_DY and RT.hdist(s, p) < ROOM_AFTER_CLEAR for p in prior)]
    if PRESSURE:
        _spots_plain = spots
        fires = {}

        def spots(B, nav, home, covers, g, *rest):             # THE PRESSURE FIX 3: holds by fire
            out = _spots_plain(B, nav, home, covers, g, *rest)
            if not out:
                return out
            if B not in fires:
                fires[B] = Fire(B)
            gi = order.index(g['name'])
            cnt = [(len(fires[B].bearing(s, gi)), s) for s in out]
            PICK['gate'], PICK['room'] = g['name'], gi
            for n, s_ in cnt:                       # (a place the men woken when THIS gate opens can see counts 3 more each: they would plop out in view of the seven)
                PICK['guns'][gun_key(s_)] = n + 3 * sum(1 for _d, m in fires[B].bearing(s_, gi + 1) if m['wake'] == gi + 1)
            ok = [s_ for n, s_ in cnt if n <= HOLD_GUNS]
            back = [s_ for s_ in (PICK['picked'].get(order[gi - 1], ()) if gi else ()) if s_ not in out]
            for s_ in back:                         # the seven of the room before, as places of this one (one room back): their fire at THIS gate
                PICK['guns'][gun_key(s_)] = len(fires[B].bearing(s_, gi))
            back = [s_ for s_ in back if PICK['guns'][gun_key(s_)] <= HOLD_GUNS]
            low = min(n for n, _s in cnt)
            PICK['note'][g['name']] = ('fire: %d of %d places have %d guns or fewer bearing%s (the fewest: %d); the seven are picked for the least fire' % (
                len(ok), len(out), HOLD_GUNS, ', %d one room back' % len(back) if len(ok) < 7 and back else '', low)) if len(ok) >= 7 or back else (
                'FIRE: only %d places with %d guns or fewer bearing (the fewest: %d)' % (len(ok), HOLD_GUNS, low))
            return list(out) + (back if len(ok) < 7 else [])
    RT.GATES, RT.EN_, RT.POST_KEEP = tuple(gates), '', ROOM_POST_CLEAR
    RT.GATE_MAX = 99                            # the planner names whole squads; the TADs name the room's men (bots_gates), at most 9 of them (rooms_check)
    RT.pick_holds, RT.hold_spots = pick_holds_club, spots
    # THE WAKE FIX: the three wake boxes stand ON the holds' area by design (the first criminal there wakes the room after, at most the gate's 30 s before its own list would); the
    # planner keeps holds and ways out of every box that wakes a LATER room's men, which would leave floor1n two cover boxes, none of them free. So they are not boxes to it
    # (rooms_check proves instead that no man they wake has a line to the holds or the walk, and wake_check that none sees the box: NOTHING is hidden from the checks).
    wake_boxes = {R + v for k, v in WAKE_NEW.items() if k.startswith('wake box')}
    RT.wake_map = lambda B, squads=None: ({k: v for k, v in wake0(B, squads)[0].items() if B.sc.path[k] not in wake_boxes}, {})
    RT.near_post = lambda p, posts, among, keep=ROOM_POST_CLEAR: near0(p, posts, among, keep)      # (the default of the original is bound at import: 300)
    try:
        yield RT
    finally:
        for k, v in saved.items():
            setattr(RT, k, v)


PICK = {'gate': None, 'room': None, 'picked': {}, 'note': {}, 'guns': {}}      # what the fire filter of rt_for_club and pick_holds_club tell each other (one process, one build)


def gun_key(s):
    return (round(s[0]), round(s[1]), round(s[2]))


def pick_holds_club(spots, n=7, seps=(110.0, 100.0, 90.0, ROOM_HOLD_SEP), tries=400):
    """Seven of the places kl_fa_bots_rt.hold_spots found -> (places, the separation asked for); ([], 0) when there are not seven. The widest
    separation of `seps` for which a set exists; among the sets tried (a fixed order first, then shuffles of a fixed seed) the one with the
    most different cover boxes, then the most places behind their box, then the most clearance. The planner's own pick packs one box's places
    along a line and gives up where a box has 24 places in a 4 m strip (the walkway's mouth)."""
    import random
    if len(spots) < n:
        return [], 0.0
    hd = lambda a, b: math.hypot(a[0] - b[0], a[2] - b[2])
    gun = lambda s: PICK['guns'].get(gun_key(s), 0)         # THE PRESSURE FIX: fewest guns first (0 for all while PRESSURE is off: the old order)
    key = lambda s: (gun(s), not s[5], abs(s[7] - 130.0), -s[6])
    rng = random.Random(7)
    for sep in seps:
        best = None
        for t in range(tries):
            if t == 0:
                order = sorted(spots, key=key)
            elif not PICK['guns']:
                order = rng.sample(spots, len(spots))
            else:                               # mostly by fire, mixed within a band so that other sets of boxes are tried (the fire of a place is a few guns)
                order = sorted(spots, key=lambda s: gun(s) + rng.uniform(0.0, 1.5 if t % 2 else 0.6))
            got, used = [], collections.Counter()
            for rnd in (0, 1):
                for s in order:
                    if len(got) < n and not (rnd == 0 and used[s[4]]) and all(hd(s, o) >= sep for o in got):
                        got.append(s)
                        used[s[4]] += 1
            if len(got) >= n:
                score = (-max(gun(g) for g in got), -sum(gun(g) for g in got), len(used), sum(1 for g in got if g[5]), min(g[6] for g in got))
                if best is None or score > best[0]:
                    best = (score, got[:n])
        if best:
            if PICK['gate']:
                PICK['picked'][PICK['gate']] = best[1]
            return best[1], sep
    return [], 0.0


def room_men(B):
    """{room: [(squad node, group node, post)]} of the built level B: every man of the kept campaign squads by the room of his post."""
    import kl_fa_bots_rt as RT
    sc, out = B.sc, collections.OrderedDict((r['name'], []) for r in ROOMS)
    for t, groups in RT.enemy_squads(B).items():
        if sc.path[t][len(R):].startswith(('Gameplay!', BK.BOT_SQUAD)):
            continue                                # the police that arrive (ARRIVE) and the bots are not the club's men
        if HELI and SQUADS.get(sc.path[t][len(R):], ('',))[0] == 'open':
            continue                                # HELI: the hunters search the whole club on no gate's clock (their men stand on the y460 floor now a room)
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups:
                room = room_of(B.at(k))
                short = sc.path[t][len(R):].split('!')[-1]
                if room and PRESSURE and short in WAKE_AT:      # a man who sleeps until a later room's hold belongs to THAT room's gate (the deck over floor1n wakes at floor1s)
                    names = [r_['name'] for r_ in ROOMS]
                    room = names[max(names.index(room), WAKE_AT[short][0])] if WAKE_AT[short][0] < len(names) else None      # (woken by the last gate: no gate waits for him)
                if room:
                    out[room].append((t, sc.parent[k], B.at(k)))
    return out


def RT_enemy_squads(B):
    import kl_fa_bots_rt as RT
    return RT.enemy_squads(B)


def bots_gates(B, P, log=print):
    """The room gates into plan P (kl_fa_bots.plan of B, already through the first part of bots_gate): loot -> holds of the rooms ->
    the seal hold -> the exit stations. P's stations, steps and every bot's places are rewritten behind the loot station; the gate
    list goes to P['club_gates'] (kl_fa_bots_rt.Street's form: name, step, wait, groups, holds ...). -> the index of the seal hold."""
    import copy
    import kl_fa_bots as F
    sc = B.sc
    nav = F.Nav(B.scene.nav)
    S = F.stations(B, nav)
    st = P['stations']
    i_loot = max(i for i, s in enumerate(st) if s['kind'] == 'loot')
    ways = [i for i, s in enumerate(st) if s['kind'] == 'way' and i > i_loot]
    if not ways:
        raise ValueError('kl_fa_club.bots_gates: no way station behind the loot')
    mid = lambda i: [sum(p[k] for p in st[i]['places']) / 7.0 for k in range(3)]
    i_seal = min(ways, key=lambda i: math.dist(mid(i), GATE_AT))
    if HELI:                                    # the last hold is before the roof door: the exit-area and level-exit stations must still follow it
        if not any(x['kind'] == 'exit' for x in st[i_seal + 1:]) or math.dist(mid(i_seal), GATE_AT) > 600.0:
            raise ValueError('kl_fa_club.bots_gates: HELI: the way station nearest %s (%s, %d away) is not before the exit station' % (GATE_AT, [round(v) for v in mid(i_seal)], math.dist(mid(i_seal), GATE_AT)))
    men = room_men(B)
    table, named = [], {}
    for r in ROOMS:
        ms = men[r['name']]
        if not ms:
            log('  kl_fa_club: room %s: no man stands in it - no gate' % r['name'])
            continue
        squads = tuple(dict.fromkeys(sc.names[t] for t, _g, _p in ms))
        table.append(dict(r, squads=squads))
        named[r['name']] = [R + sc.path[g][len(R):] for _t, g, _p in ms]
    seal = dict(st[i_seal], kind='park')
    P2 = {'stations': copy.deepcopy(st[:i_loot + 1]) + [seal],
          'steps': [s for s in P['steps'] if s['leg'] == 'in' and s.get('stop', 0) == 0],
          'bots': {N: {'places': list(P['bots'][N]['places'][:i_loot + 1]) + [P['bots'][N]['places'][i_seal]]} for N in F.BOTS}}
    with rt_for_club(table, men) as RT:
        gates = RT.gates_plan(B, nav, S, P2, {'gate_names': None}, lambda s: log(s) if s.lstrip().startswith(('gate', 'to the car')) else None)
    sight = None
    if ROOM_NAME_SEEN:
        import kl_route
        sight = Sight(kl_route.load(B.folder))
    for g in gates:
        every = named[g['name']]
        g['groups'] = every
        g['room_men'] = len(every)
        if sight is not None:
            # second fix (skeptic's fault 3): a gate that waits for a man no hold can hit waits for the 30 s clock; name the men the seven can SEE from at least one hold
            # (Sight: the 0x20 line from eye to head or chest); where none is seen the room's men are all named (the clock is then the gate)
            ends = [tuple(h[:3]) for h in g['holds']] if g.get('holds') else []
            at = {R + sc.path[gp][len(R):]: p for _t, gp, p in men[g['name']]}
            seen = [x for x in every if any(sight.seen(h, at[x]) for h in ends)] if ends else []
            if seen:
                g['groups'] = seen
            g['unnamed'] = [x for x in every if x not in g['groups']]
        g['men'] = len(g['groups'])
        g['wait'] = '%03d_TriggerActorsDead_%s' % (30 + [x['name'] for x in gates].index(g['name']), g['name'])
        g['seconds'] = ROOM_WAIT_S
    if PRESSURE:                                                # THE PRESSURE FIX 1: the gate before a room's hold wakes the squads that are awake at it
        by_room = {g['name']: gi for gi, g in enumerate(gates)}
        order_ = [r['name'] for r in ROOMS]
        for g in gates:
            g['wake'] = []
        for t, _groups in RT_enemy_squads(B).items():
            name = sc.path[t][len(R):]
            short = name.split('!')[-1]
            if short not in WAKE_AT:
                continue
            w, child = WAKE_AT[short]
            room = order_[w - 1]                                # the gate whose opening wakes it: the room before the one it is awake at
            if room not in by_room:
                raise ValueError('kl_fa_club.bots_gates: %s wakes at gate %d (%s), which has no gate' % (short, w, room))
            gates[by_room[room]]['wake'].append(sc.path[t] + chr(92) + child)
        for g in gates:
            log('  gate %-8s opens -> wakes %s' % (g['name'], ', '.join(x.split('!')[-1].split(chr(92))[0] for x in g['wake']) or 'nobody'))
        for name, note in PICK['note'].items():
            log('  gate %-8s %s' % (name, note))
            for g in gates:
                if g['name'] == name:
                    g['fire'] = note
    n_new = len(P2['stations']) - 1 - (i_loot + 1)              # the holds (WAY_EVERY is 0: no way stations)
    # ---- the plan: stations
    seal_st = dict(st[i_seal])
    seal_st['what'] = 'the seal hold in the entrance hall until the seal is open'
    tail = st[i_seal + 1:]
    off = len(P2['stations']) - 1 - i_seal                       # tail station k -> k + off
    P['stations'] = P2['stations'][:-1] + [seal_st] + tail
    for N in F.BOTS:
        pl = P['bots'][N]['places']
        P['bots'][N]['places'] = P2['bots'][N]['places'][:-1] + [pl[i_seal]] + list(pl[i_seal + 1:])
    # ---- the plan: steps (the rooms' steps and the hold in front of the seal are the second stop's walk, 'in' leg, so the seal timer follows them)
    first = [s for s in P['steps'] if s['leg'] == 'in' and s.get('stop', 0) == 0]
    steps = [dict(s) for s in first]
    for s in P2['steps']:
        if s.get('gate'):
            steps.append({'name': s['name'], 'leg': 'in', 'stop': 1, 'stations': s['stations'], 'gate': s['gate']})
    out_idx = [i + off for s in P['steps'] if s['leg'] == 'out' for i in s['stations'] if i > i_seal]
    for m, k in enumerate(range(0, len(out_idx), 3)):
        steps.append({'name': '%03d_DefendBehaviour_out' % (50 + m), 'leg': 'out', 'stop': None, 'stations': out_idx[k:k + 3]})
    P['steps'] = steps
    for g in gates:
        g['step'] = next(s['name'] for s in steps if s.get('gate') == g['name'])
    P['club_gates'] = gates
    return i_loot + 1 + n_new


def gates_timetable(P):
    """Seconds after the round-start event, from the plan: the quickest crew's and the slowest crew's times at the seal hold and at the
    van call -> dict. quick = every room won at once (ROOM_G_MIN); slow = every room runs its WAIT_S out and every walk is the mesh path at GATE_SLOW."""
    gates = P.get('club_gates') or []
    n = len(gates)
    start = float(P['options'].get('start_delay', 10.0))
    cap = float(P['options'].get('loot_seconds', 20))
    st = P['stations']
    b0 = P['bots'][next(iter(P['bots']))]['places']
    i_loot = max(i for i, s in enumerate(st) if s['kind'] == 'loot')
    i_seal = i_loot + n + 1
    pts = [b0[i_loot]] + [b0[i_loot + 1 + k] for k in range(n)] + [b0[i_seal]]
    straight = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    path = sum(g['path'] for g in gates) + math.dist(pts[-2], pts[-1]) * 1.3
    to_van = [b0[i] for i in range(i_seal, len(st))]
    exit_walk = sum(math.dist(a, b) for a, b in zip(to_van, to_van[1:])) * 1.3
    # V2: the bots START on the slab, the way IN to the loot is walked first (no gate on it): the straight line through the stations at GATE_SPEED, the path 1.3 x that at GATE_SLOW
    in_straight = 0.0
    if V2:
        first = P['bots'][next(iter(P['bots']))]['start']
        walk_in = [first] + [b0[i] for i in range(i_loot + 1)]
        in_straight = sum(math.dist(a, b) for a, b in zip(walk_in, walk_in[1:]))
    return dict(rooms=n, start=start, loot_cap=cap, straight=straight, path=path, exit_walk=exit_walk, in_straight=in_straight,
                quick_arrive=start + in_straight / GATE_SPEED + GATE_LOOT_MIN + straight / GATE_SPEED + n * ROOM_G_MIN,
                slow_arrive=start + in_straight * 1.3 / GATE_SLOW + cap + path / GATE_SLOW + n * ROOM_WAIT_S)


def bots_gate_rooms(B, P, log=print):
    """bots_gate with ROOM_GATES: kl_fa_bots' plan P of built level B -> P with the rooms' gates (bots_gates) in front of the seal gate. The seal's
    hold is the last leg of the rooms and keeps its plain timer (GATE_NAME) of the seconds that make the QUICKEST crew leave it no sooner than SEAL_AT
    (a crew that has won every room in ROOM_G_MIN s each); slower crews arrive later and wait less long for the same clock, but a crew that is held
    in every room still waits this timer: its worst case is gates_timetable's 'slow_leave'."""
    import kl_fa_bots as F
    loot = [i for i, s in enumerate(P['stations']) if s['kind'] == 'loot']
    if len(loot) != 1 or len(P['waits']) != 1 or P['waits'][0]['cases'] or not P['waits'][0]['loot']:
        raise ValueError('kl_fa_club.bots_gate: the plan has %d loot stations and %d waits (wanted: one stop with loot, no case)' % (len(loot), len(P['waits'])))
    bots_gates(B, P, log)
    tt = gates_timetable(P)
    seconds = GATE_MIN if SEAL_OPEN else max(GATE_MIN, math.ceil(SEAL_AT + GATE_MORE - tt['quick_arrive']))
    i_seal = loot[0] + len(P['club_gates']) + 1
    P['waits'] = [P['waits'][0], collections.OrderedDict(name=GATE_NAME, stop=1, seconds=seconds, loot=[], worth=0, timer='038_Timer_at_cases',
                                                       relays=[], cases={})]
    P['stations'][i_seal]['what'] = 'the seal hold in the entrance hall until the seal is open (%g s)' % seconds
    P['gate'] = {'station': i_seal, 'seconds': seconds, 'straight': round(tt['straight']), 'seal_at': SEAL_AT, 'seal_open': SEAL_OPEN, 'start': tt['start'],
                 'loot_cap': tt['loot_cap'], 'places': P['stations'][i_seal]['places'], 'rooms': tt['rooms'], 'path': round(tt['path']), 'in_straight': round(tt['in_straight']),
                 'exit_walk': round(tt['exit_walk']), 'room_g_min': ROOM_G_MIN, 'room_wait': ROOM_WAIT_S}
    note = ('THE ROOM GATES: %d rooms (%s) between the loot and the seal hold; each is a hold of seven at cover and a TriggerActorsDead on the room\'s men '
            '(30 s at most); the seal hold (station %d, %g s) follows. Timetable after the round-start event: quickest crew at the hold %d s, slowest %d s '
            '(+ the hold, + the walk out %d s)' % (tt['rooms'], ', '.join(g['name'] for g in P['club_gates']), i_seal + 1, seconds, tt['quick_arrive'], tt['slow_arrive'],
                                                   tt['exit_walk'] / GATE_SLOW))
    P['notes'].append(note)
    log('  NOTE ' + note)
    log('steps: %s' % [(s['name'], s['stations']) for s in P['steps']])
    return P


def scene_wake(B, P, tad):
    """{campaign squad name: the gate at whose hold it is awake}, READ OFF THE BUILT SCENE: 0 for a squad in the world from the load (ZSquadScript field 3 = 1) or
    started by a box / the round's timer, k + 1 for a squad whose SquadModifierBehaviour the TriggerActorsDead of gate k names (any of the seven bot squads'
    copies), 99 for a waiting squad nothing of the gates names (the hunters: the beat's gate)."""
    import kl_fa_bots_rt as RT
    sc = B.sc
    gates = P.get('club_gates') or []
    f3 = {t: v[SQUAD_ACTIVE] for t, _i, v in kl_fa.controllers(sc, 'ZSquadScript')}
    named = {}                                          # squad node -> the lowest gate index that names a node of it
    for k, v in tad.items():
        for gi, g in enumerate(gates):
            if sc.names[k] == g['wait']:
                for ref in v[2]:
                    for h in sc.resolve(ref):
                        if sc.top[h] in f3:
                            named[sc.top[h]] = min(named.get(sc.top[h], 99), gi)
    out = {}
    boxes, other = RT.wake_map(B)
    for t in RT.enemy_squads(B):
        name = sc.path[t][len(R):]
        if name.startswith(('Gameplay!', BK.BOT_SQUAD)):
            continue
        if f3.get(t) == 1:
            out[name] = 0
        elif t in named:
            out[name] = named[t] + 1
        elif any(t in hit for hit in boxes.values()) or other.get(t) == 'timer':
            out[name] = 0
        else:
            out[name] = 99
    return out


INLEG_KNOWN = 6                        # V2: guns that bear on a stretch of the way IN (MEASURED on the first V2 build: 5 for bot 1, 6 for bot 2, on dance floor 2 and the ramp); a guard, not a yardstick
INLEG_STEP = 300.0


def inleg_table(B, P, fire):
    """V2: the guns on the way IN (the bots' places from their start to the loot station, sampled every 3 m on the straight lines between them; the exact ray; the men of the squads
    that are in the world from the load: stage 'load' of squads_now) -> (worst, [(metres along the way, place, [men])] of the samples with 2 or more, bot name, the way's length in units)."""
    sq = squads_now()
    men = [m for m in fire.men if sq.get(m['squad'], ('',))[0] == 'load']
    st = P['stations']
    i_loot = max(i for i, x in enumerate(st) if x['kind'] == 'loot')
    worst, rows, who, length = 0, [], None, 0.0
    for N in sorted(P['bots']):
        b = P['bots'][N]
        pts = [b['start']] + [b['places'][i] for i in range(i_loot + 1)]
        run, rr, w = 0.0, [], 0
        for a, c in zip(pts, pts[1:]):
            d = math.dist(a, c)
            n = max(1, int(d / INLEG_STEP))
            for k in range(n):
                p_ = tuple(a[j] + (c[j] - a[j]) * k / n for j in range(3))
                g = [m for m in men if math.dist(m['at'], p_) <= GUN_RANGE and abs(m['at'][1] - p_[1]) < GUN_FLOOR and fire.sees(m['at'], p_)]
                w = max(w, len(g))
                if len(g) >= 2:
                    rr.append((round((run + d * k / n) / 100), tuple(round(v) for v in p_), sorted({m['man'] for m in g})))
            run += d
        if w > worst or who is None:
            worst, rows, who, length = w, rr, N, run
    return worst, rows, who, length, len(men)


def pressure_check(folder, B, P, tad, fail, log):
    """THE PRESSURE FIX's proofs on a folder with room gates (called by rooms_check): (1) every squad of WAKE_AT is waiting and named by the TriggerActorsDead
    of the gate before its room, by no other (the wake table is READ OFF THE SCENE); (2) hold-guns: on the exact ray, at most HOLD_GUNS men awake at the gate bear
    on a hold place and at most LEG_GUNS on any stretch (every LEG_STEP) of a bot's way to it; (3) nobody is woken in sight of the previous room's holds (no
    'plopping out'). The table is logged; faults go to `fail`."""
    gates = P.get('club_gates') or []
    wake = scene_wake(B, P, tad)
    fire = Fire(B, wake)
    rows = gun_table(B, P, fire)
    log('  hold-guns (exact ray, within %d m, men of the squads awake at the gate; yardstick Withdrawal: holds 0..3, walks 1..4, with the police 4..7; caps HOLD_GUNS %d, LEG_GUNS %d):'
        % (GUN_RANGE / 100, HOLD_GUNS, LEG_GUNS))
    for gi, (g, r) in enumerate(zip(gates, rows)):
        log('    gate %-8s guns on the 7 holds %s (worst %d; %d if the men the gates before named are dead); the walk to them: worst %d at %s (%d; %d samples); awake men %d of %d%s' % (
            r['name'], r['holds'], r['hold_worst'], r['hold_dead'], r['leg_worst'], r['leg_at'], r['leg_dead'], r['samples'], sum(1 for m in fire.men if m['wake'] <= gi), len(fire.men),
            '; %s' % g['fire'] if g.get('fire') else ''))
        log('      laggard case (the men this gate wakes in the world while a bot is still on its leg / hold%s): worst %d at %s' % (', or on the walk to the seal hold' if gi == len(gates) - 1 else '', r['lag_worst'], r['lag_at']))
        if r['lag_worst'] > max(r['hold_worst'], r['leg_worst'], HELI_KNOWN.get(r['name'], (0, 0, 0))[2] if HELI else 0):
            fail('hold-guns: gate %s: the men its opening wakes add guns on a bot still arriving: %d at %s against %d without them' % (r['name'], r['lag_worst'], r['lag_at'], max(r['hold_worst'], r['leg_worst'])))
        known_h, known_l = (HELI_KNOWN if HELI else PRESSURE_KNOWN).get(r['name'], PRESSURE_KNOWN.get(r['name'], (HOLD_GUNS, LEG_GUNS)))[:2]
        if r['hold_worst'] > max(HOLD_GUNS, known_h):
            fail('hold-guns: gate %s: %d guns bear on a hold (%d wanted at most, %d known): %s' % (r['name'], r['hold_worst'], HOLD_GUNS, max(HOLD_GUNS, known_h), ', '.join(r['who_hold'][:8])))
        elif r['hold_worst'] > HOLD_GUNS:
            log('      NOTE KNOWN over the yardstick: %d guns on a hold (%d wanted; PRESSURE_KNOWN)' % (r['hold_worst'], HOLD_GUNS))
        if r['leg_worst'] > max(LEG_GUNS, known_l):
            fail('hold-guns: gate %s: %d guns bear on the walk to it at %s (%d wanted at most, %d known): %s' % (r['name'], r['leg_worst'], r['leg_at'], LEG_GUNS, max(LEG_GUNS, known_l), ', '.join(r['who_leg'][:8])))
        elif r['leg_worst'] > LEG_GUNS:
            log('      NOTE KNOWN over the yardstick: %d guns on the walk (%d wanted; PRESSURE_KNOWN)' % (r['leg_worst'], LEG_GUNS))
    if V2 and P.get('gate', {}).get('in_straight'):       # THE WAY IN has no gate: the guns of the squads that are in the world from the load bear on it
        worst, rows_in, who_in, length_in, n_men = inleg_table(B, P, fire)
        log('  way in (no gate; %d men awake from the load): %d m for bot %s, worst %d guns on a stretch (%d known) at %s' % (
            n_men, length_in / 100, who_in, worst, INLEG_KNOWN, ', '.join('%d m %s: %s' % (m, pl, '+'.join(x.split(' ')[0] + x.split('Guard')[-1] for x in g)) for m, pl, g in rows_in if len(g) == worst)[:300]))
        if worst > INLEG_KNOWN:
            fail('way in: %d guns bear on a stretch of the way in (%d known)' % (worst, INLEG_KNOWN))
    order_ = [r['name'] for r in ROOMS]
    for n, w in wake.items():
        short = n.split('!')[-1]
        if short in WAKE_AT and w != WAKE_AT[short][0]:
            fail('pressure: %s is awake at gate %s by the scene, WAKE_AT wants %s (named by the gate of %s)' % (short, w, WAKE_AT[short][0], order_[WAKE_AT[short][0] - 1]))
        if short not in WAKE_AT and SQUADS.get(n, ('',))[0] != 'open' and w == 99:
            fail('pressure: %s is waiting and nothing wakes it' % short)
    for gi in range(1, len(gates) + 1):                 # (3) the squads woken when gate gi-1 opens are not in sight of that gate's holds
        for m in fire.men:
            if m['wake'] == gi:
                seen = [h for h in rows[gi - 1]['hold_at'] if math.dist(m['at'], h) <= GUN_RANGE and abs(m['at'][1] - h[1]) < GUN_FLOOR and fire.sees(m['at'], h)]
                if seen:
                    fail('appear: %s (woken when gate %s opens) stands at (%d, %d, %d) in sight of %d of the seven holds of %s, the first (%d, %d, %d)' % (
                        m['man'], gates[gi - 1]['name'], *[round(v) for v in m['at']], len(seen), gates[gi - 1]['name'], *seen[0]))


def wake_nodes_of(sc):
    """{room: ([node of each staged squad's start child], [squad short names])} read off the scene: the squads of WAKE_AT by the room whose gate names them."""
    out = collections.OrderedDict()
    for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript'):
        name = sc.path[k][len(R):]
        short = name.split('!')[-1]
        if short not in WAKE_AT:
            continue
        child = WAKE_AT[short][1]
        j = sc.resolve(R + name + '\\' + child)
        room = ROOMS[WAKE_AT[short][0] - 1]['name']
        e = out.setdefault(room, ([], []))
        e[0].extend(j)
        e[1].append(short)
    return collections.OrderedDict((r['name'], out[r['name']]) for r in ROOMS if r['name'] in out)


def wake_check(folder, sc, mesh, box_of, fail, log):
    """THE WAKE FIX's proofs on a folder (called by check(); a folder without the fix is said and left): every staged squad (WAKE_AT) is parked (ZSquadScript field 3 = 0)
    and its start child (a SquadModifierBehaviour: the node the exe's 'AITrigger' path wakes) is named by (1) a TriggerBox that fires for criminals only, once, standing
    where WAKE_BOX says, (2) a TriggerDelay2 of the backstop's seconds that the round-start list starts, and - in a folder with the bots' gates - (3) the gate of the room
    before its own (rooms_check). NONE of a group's men has an exact-ray line (Fire: eyes 160, within GUN_RANGE, not from another floor) to a mesh point of the box that
    wakes him (a criminal standing in it must not see him appear). box_of(k) -> (lo, hi) of a ZBoxPrimitive. Faults go to `fail`."""
    import kl_fa_bots as F
    if not any(sc.resolve(R + v) for v in WAKE_NEW.values()):
        log('  wake: no wake boxes / backstops in this folder (a build of before 2026-10-12 or with --no-wake-boxes / --no-pressure / --legacy / --no-ai): the squads wake by the gates of the bots only')
        return
    groups = wake_nodes_of(sc)
    if list(groups) != list(WAKE_BOX):
        fail('wake: the staged squads form the groups %s, WAKE_BOX has %s' % (list(groups), list(WAKE_BOX)))
        return
    mon = {h for s in values(sc, A.node_of(sc, ROLE['monitor']), 'AIMonitor')[2] for h in sc.resolve(s)}
    B = F.Built(folder)
    fire = Fire(B, {})
    rows = []
    for i, (room, w) in enumerate(WAKE_BOX.items()):
        mods, shorts = groups[room]
        want = set(mods)
        bx, tm = A.node_of(sc, ROLE['wake box %d' % (i + 1)]), A.node_of(sc, ROLE['wake timer %d' % (i + 1)])
        v = values(sc, bx, 'TriggerBox')
        if v[0] != 1 or v[BK.BOX_PER_MAN] != 0 or v[14] != 'ECPS_FA_MERCONLY':
            fail('wake box %s: TriggerBox fields 0 / %d / 14 are %s / %s / %s (1, 0 = once, criminals only wanted)' % (room, BK.BOX_PER_MAN, v[0], v[BK.BOX_PER_MAN], v[14]))
        got = {h for s in v[17] for h in sc.resolve(s)}
        if got != want or len(v[17]) != len(want):
            fail('wake box %s names %d objects, the group is %d squads (%s): %s' % (room, len(v[17]), len(want), ', '.join(shorts), [s.split('!')[-1] for s in v[17]][:4]))
        lo, hi = box_of(bx)
        ctr = [(lo[a] + hi[a]) / 2 for a in range(3)]
        if any(abs(ctr[a] - w['centre'][a]) > 1.0 or abs((hi[a] - lo[a]) / 2 - w['half'][a]) > 1.0 for a in range(3)):
            fail('wake box %s stands at %s, half %s: WAKE_BOX wants %s, %s' % (room, [round(c) for c in ctr], [round((hi[a] - lo[a]) / 2) for a in range(3)], w['centre'], w['half']))
        tv = values(sc, tm, 'TriggerDelay2')
        if abs(tv[0] - w['backstop']) > 0.01 or {h for s in tv[4] for h in sc.resolve(s)} != want or len(tv[4]) != len(want) or tv[2] >= 0:
            fail('wake timer %s: TriggerDelay2 %s s (%s), names %d objects (%d wanted), re-arm field %s (a negative one wanted: once)' % (room, tv[0], w['backstop'], len(tv[4]), len(want), tv[2]))
        if tm not in mon:
            fail('wake timer %s is not in the round-start list of the AIMonitor: nothing starts it' % room)
        if not (100.0 <= tv[0] <= ROUND_CLOCK - ROOM_VAN_MARGIN):
            fail('wake timer %s: %g s after the round-start event is outside 100 .. %g' % (room, tv[0], ROUND_CLOCK - ROOM_VAN_MARGIN))
        rm = next(r for r in ROOMS if r['name'] == room)
        if not (rm['box'][0] - 150.0 <= lo[0] and hi[0] <= rm['box'][1] + 150.0 and rm['box'][2] - 150.0 <= lo[2] and hi[2] <= rm['box'][3] + 150.0):
            fail('wake box %s (x %d..%d, z %d..%d) is not in the %s room (x %d..%d, z %d..%d, 150 allowed)' % (room, lo[0], hi[0], lo[2], hi[2], room, *rm['box'][:2], *rm['box'][2:]))
        for h in want:                                  # every squad of the group: parked
            t = sc.top[h]
            if values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE] != 0:
                fail('wake: %s is not parked (ZSquadScript field %d = %s): nothing would be left to wake' % (sc.names[t].split('!')[-1], SQUAD_ACTIVE, values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE]))
            if not kl_fa.has(sc, h, 'SquadModifierBehaviour'):
                fail('wake: %s is not a SquadModifierBehaviour, the object the exe\'s AITrigger path wakes a squad by' % sc.path[h][-60:])
        pts = []
        for x in range(int(lo[0]), int(hi[0]) + 1, 100):
            for z in range(int(lo[2]), int(hi[2]) + 1, 100):
                hit = mesh.at(float(x), (lo[1] + hi[1]) / 2, float(z), dy=(hi[1] - lo[1]) / 2)
                if hit:
                    pts.append((float(x), hit[1], float(z)))
        men = [m for m in fire.men if m['squad'].split('!')[-1] in shorts]
        seen = [(m['man'], p) for m in men for p in pts if math.dist(m['at'], p) <= GUN_RANGE and abs(m['at'][1] - p[1]) < GUN_FLOOR and fire.sees(m['at'], p)]
        if not pts:
            fail('wake box %s: no mesh point inside it (nobody can stand in it)' % room)
        if seen:
            fail('wake box %s: %s (woken by it) has a free line to %d of its %d mesh points, the first (%d, %d, %d)' % (room, seen[0][0], len({s[1] for s in seen}), len(pts), *seen[0][1]))
        rows.append((room, len(mods), len(men), len(pts), len({s[1] for s in seen}), w['backstop'], [round(c) for c in ctr], [round(w['half'][a]) for a in range(3)]))
    for room, ns, nm, npts, nseen, back, ctr, half in rows:
        log('  wake %-8s: %d staged squads (%d men; the gate before the room names them in a folder with the bots: rooms_check), by a criminals-only box at %s half %s (%d mesh points inside, %d of them in the exact-ray '
            'sight of a man it wakes) and by the backstop %g s after the round-start event' % (room, ns, nm, ctr, half, npts, nseen, back))


def wake_plan_check(folder, B, P, gates, tad, fail, log):
    """THE WAKE FIX against the plan of a folder with the bots' gates (called by rooms_check): the box of a group holds at least 5 of the seven holds of the room whose gate names the
    group (a bot that holds there fires it; the human on the way meets it), and its backstop is later than the SLOWEST crew's gate (wake_min: the quickest-out arrival at that room
    after every room before it has run its 30 s + the room's own 30 s) by WAKE_DELAY and sooner than the van's margin. A squad of WAKE_AT is named by the gate of its room's TAD
    in all seven bot squads (already proved by pressure_check) AND by the box AND by the backstop: said as one line per group."""
    import kl_fa_bots as F
    sc = B.sc
    if not any(sc.resolve(R + v) for v in WAKE_NEW.values()):
        return
    start, cap = float(P['gate']['start']), float(P['gate']['loot_cap'])
    wait = float(P['gate'].get('room_wait', ROOM_WAIT_S))
    names = [g['name'] for g in gates]
    for i, (room, w) in enumerate(WAKE_BOX.items()):
        if room not in names:
            fail('wake: %s has no gate in the plan' % room)
            continue
        k = names.index(room)
        arrive = start + cap + sum(g['path'] for g in gates[:k + 1]) / GATE_SLOW + k * wait
        wake_min = arrive + wait
        g = gates[k]
        bx = A.node_of(sc, ROLE['wake box %d' % (i + 1)])
        c, hf = B.at(bx), kl_fa.node_values(sc, bx)[8:11]
        inside = [h for h in g['holds'] if all(abs(h[a] - c[a]) <= hf[a] for a in range(3))]
        if len(inside) < 5:
            fail('wake box %s holds %d of the 7 holds of its room (5 wanted): the first bot would not fire it' % (room, len(inside)))
        if w['backstop'] < wake_min + WAKE_DELAY - 0.01:
            fail('wake timer %s: %g s is before the slowest crew\'s gate (%.1f s + %g): it would wake the men on top of a crew that is still on its way' % (room, w['backstop'], wake_min, WAKE_DELAY))
        log('  wake %-8s plan: the box holds %d of the 7 holds; the slowest crew arrives at the room at %.0f s and its gate fires by %.0f s; the backstop is at %g s (round %g, van margin %g)' % (
            room, len(inside), arrive, wake_min, w['backstop'], ROUND_CLOCK, ROOM_VAN_MARGIN))
    # ---- every staged squad: its start child is named by the gate of the room before its own in each of the seven bot squads, by its group's box and by its group's backstop - and by nothing else
    refs = collections.defaultdict(lambda: collections.defaultdict(list))
    for cn, field in (('TriggerActorsDead', 2), ('TriggerBox', 17), ('TriggerDelay2', 4)):
        for k, _i, v in kl_fa.controllers(sc, cn):
            for s in v[field]:
                for h in sc.resolve(s):
                    refs[h][cn].append(k)
    boxes_ = {A.node_of(sc, ROLE['wake box %d' % (i + 1)]): room for i, room in enumerate(WAKE_BOX)}
    timers_ = {A.node_of(sc, ROLE['wake timer %d' % (i + 1)]): room for i, room in enumerate(WAKE_BOX)}
    order_ = [r['name'] for r in ROOMS]
    for room, (mods, shorts) in wake_nodes_of(sc).items():
        for h, short in zip(mods, shorts):
            gate = order_[WAKE_AT[short][0] - 1]
            tads = [sc.names[k] for k in refs[h]['TriggerActorsDead'] if sc.path[k][len(R):].startswith(BK.BOT_SQUAD)]
            want_ = [g['wait'] for g in gates if g['name'] == gate]
            got_b = [boxes_.get(k) for k in refs[h]['TriggerBox']]
            got_t = [timers_.get(k) for k in refs[h]['TriggerDelay2']]
            ok = len(tads) == len(F.BOTS) and set(tads) == set(want_) and got_b == [room] and got_t == [room]
            log('  wake %-15s: gate of %s %s x%d, box of %s %s, backstop of %s %s%s' % (short, gate, sorted(set(tads)), len(tads), room, got_b, room, got_t, '' if ok else '  <- NOT AS WANTED'))
            if not ok:
                fail('wake: %s (%s) is named by gates %s x%d, boxes %s, timers %s - wanted gate %s x%d, box %s, timer %s' % (short, sc.path[h][-40:], sorted(set(tads)), len(tads), got_b, got_t, gate, len(F.BOTS), [room], [room]))


def rooms_check(folder, log=print):
    """The room gates of a finished folder (before or after the dynamic step) -> list of faults. Reads bots.json's 'club_gates' (a folder of the
    first delivery has none: nothing to check, said). FAILS: a gate whose TriggerActorsDead is missing from a squad, names other groups than
    planned, names a group that does not exist, has a group without an actor (no 30 s clock then), names a man a gate before it named, or has
    field 1 other than 0; the seven holds of a room not at seven distinct places (80 apart) or a hold not 60..240 from a cover box; a hold or a
    station up to the seal hold within ROOM_POST_CLEAR of a post of a man who may be alive (not named by an earlier gate) on its floor; any
    timer or loot wait between the first gate and the seal hold (the dynamic step's rally, a TriggerDelay2); the timetable (quick / slow)."""
    import json
    import kl_fa_bots as F
    import kl_fa_bots_rt as RT
    bad = []

    def fail(s):
        bad.append(s)
        log('  FAIL ' + s)
    try:
        with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
            P = json.load(f).get('plan') or {}
    except (OSError, ValueError):
        P = {}
    gates = P.get('club_gates')
    if not gates:
        log('  rooms: bots.json has no room gates (a build made with --no-gates / --legacy, or before 2026-10-12): not checked')
        return bad
    B = F.Built(folder)
    sc = B.sc
    tops = [t for t in sc.tops() if sc.names[t].startswith(BK.BOT_SQUAD + 'Squad#')]
    tad = {k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerActorsDead')}
    defend = {k: v for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    NEXT = {'DefendBehaviourRout': 7, 'TriggerActorsDead': 2, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerCounter': 4}
    nxt = {k: [j for s in v[NEXT[cn]] for j in sc.resolve(s)] for cn in NEXT for k, _i, v in kl_fa.controllers(sc, cn)}
    kind = {k: cn for cn in NEXT for k, _i, v in kl_fa.controllers(sc, cn)}
    for k, _i, v in kl_fa.controllers(sc, 'RandomTrigger'):     # the dynamic step's fork (kl_fa_bots_dyn: fields 5..7 = the first step of each way): a way, not a wait
        kind[k] = 'RandomTrigger'
        nxt[k] = [j for x in v[5:8] for s in (x if isinstance(x, list) else [x]) if isinstance(s, str) and s for j in sc.resolve(s)]
    covers = RT.cover_boxes(B)
    named_before, posts_all = set(), {}
    sq = RT.enemy_squads(B)
    posts = RT.enemy_posts(B, sq)
    men = []                                           # (post, group path, squad name): the club's own men
    for t, groups in sq.items():
        if sc.path[t][len(R):].startswith('Gameplay!'):
            continue
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups:
                men.append((B.at(k), sc.path[sc.parent[k]], sc.names[t]))
    holds_seen, seal_hold = [], None
    rank = {r['name']: i for i, r in enumerate(ROOMS)}
    rows = []
    import kl_route
    sight = Sight(kl_route.load(folder))
    for gi, g in enumerate(gates):
        found, ends = [], []
        for t in tops:
            hit = [k for k in range(t, sc.end[t]) if sc.names[k] == g['wait'] and k in tad]
            if len(hit) != 1:
                fail('%s: %d TriggerActorsDead %s (wanted 1)' % (sc.names[t], len(hit), g['wait']))
                continue
            v = tad[hit[0]]
            found.append(v)
            want = [s.lower() for s in g['groups']]
            if sorted(s.lower() for s in v[0]) != sorted(want):
                fail('%s: %s names %d groups, the plan %d (%s)' % (sc.names[t], g['wait'], len(v[0]), len(want), [s.split('!')[-1] for s in v[0]][:4]))
            if v[1] != 0:
                fail('%s: %s field 1 is %s (stock: 0)' % (sc.names[t], g['wait'], v[1]))
            before = [k for k, d in defend.items() if t < k < sc.end[t] and any(hit[0] == j for s in d[7] for j in sc.resolve(s))]
            if not before:
                fail('%s: no step leads into %s' % (sc.names[t], g['wait']))
            for k in before:
                if defend[k][1]:
                    ends.append(B.at(sc.resolve(defend[k][1][-1])[0]))
        if len({tuple(v[0]) for v in found}) > 1:
            fail('gate %s: the seven squads name different groups' % g['name'])
        for s in (found[0][0] if found else []):
            hits = sc.resolve(s)
            if len(hits) != 1 or not any(sc.cls(c) == 'ZFFActor' and sc.parent[c] == hits[0] for c in range(hits[0], sc.end[hits[0]])):
                fail('gate %s names %s: %s' % (g['name'], s, 'no such group' if not hits else 'a group without an actor (a TriggerActorsDead then has no 30 s clock)'))
            if s.lower() in named_before:
                fail('gate %s names %s, which a gate before it already waited for (its man is dead or its clock has run)' % (g['name'], s.split('\\')[-1]))
            named_before.add(s.lower())
        if len(found[0][0] if found else []) > 9:
            fail('gate %s names more than 9 groups (stock: 9 at most)' % g['name'])
        # ---- the seven holds: distinct places, at cover
        if len(ends) != 7 or any(math.dist(a, b) < ROOM_HOLD_SEP for i, a in enumerate(ends) for b in ends[i + 1:]):
            fail('gate %s: %d hold places, %s apart at least (wanted 7, %g)' % (g['name'], len(ends), round(min([math.dist(a, b) for i, a in enumerate(ends) for b in ends[i + 1:]] or [0])), ROOM_HOLD_SEP))
        ring = []
        for h in ends:
            d, ck = min((RT.hdist(h, c), k) for k, c in covers if abs(c[1] - h[1]) <= 260.0) if covers else (1e9, None)
            ring.append(d)
            if not (ROOM_HOLD_RING[0] <= d <= ROOM_HOLD_RING[1]):
                fail('gate %s: a hold at (%d, %d, %d) is %d from the nearest cover box (wanted %d..%d)' % (g['name'], *h, d, *ROOM_HOLD_RING))
        for h in ends:
            if any(math.dist(h, o) < 1.0 for o in holds_seen) and 'one room back' not in (g.get('fire') or ''):       # (the pressure fix's fallback: some of the seven stay at the room before's holds)
                fail('gate %s: a hold at (%d, %d, %d) is the place of a hold of an earlier gate' % (g['name'], *h))
        holds_seen += ends
        # ---- no living man within 4 m of a hold (men not named by a gate before this one)
        # (second fix, skeptic's fault 2: EVERY man, also the ones an earlier gate names - a gate may run out its 30 s with them alive)
        alive = [(p, n_) for p, gp, n_ in men]
        lim = lambda p: ROOM_AFTER_CLEAR if (room_of(p) in rank and rank[room_of(p)] < rank.get(g['name'], 0)) else ROOM_POST_CLEAR
        close = [(round(RT.hdist(h, p)), n_.split('!')[-1], tuple(round(c) for c in p)) for h in ends for p, n_ in alive if abs(p[1] - h[1]) <= RT.FLOOR_DY and RT.hdist(h, p) < lim(p)]
        if close:
            fail('gate %s: %d hold(s) within %d (a man of an earlier room: %d) of a post of a man who may be alive, e.g. %s' % (g['name'], len(close), ROOM_POST_CLEAR, ROOM_AFTER_CLEAR, close[0]))
        dead_close = sum(1 for h in ends for p, gp, n_ in men if gp.lower() in {x for g_ in gates[:gi] for x in map(str.lower, g_['groups'])}
                         and abs(p[1] - h[1]) <= RT.FLOOR_DY and RT.hdist(h, p) < ROOM_POST_CLEAR)
        # ---- who of the room can be hit from the holds (the 0x20 line on the mesh, kl_fa_bots_rt.mesh_line) - said, not failed
        mine = {x.lower() for x in g['groups']}
        room = [p for p, gp, _n in men if gp.lower() in mine]
        seen = sum(1 for p in room if any(sight.seen(h, p) for h in ends))
        foreign = sum(1 for p, gp, _n in men if gp.lower() not in mine and abs(p[1] - ends[0][1]) <= RT.FLOOR_DY and any(RT.hdist(h, p) < 2500.0 and sight.seen(h, p) for h in ends))
        rows.append((g['name'], len(room), seen, round(min(ring)), round(max(ring)), dead_close, [tuple(round(c) for c in h) for h in ends][:2], foreign, g.get('room_men', len(room))))
    for name, n_, seen, lo, hi, dc, hs, foreign, all_ in rows:
        log('  room %-8s %d of its %d men named (the rest no hold can see), %d of the named in the 0x20 line of sight of a hold (eye 160 to head or chest, kl_fa_club.Sight), %d men of other rooms on the floor within 25 m see a hold; holds %d..%d from a cover box; %d hold/earlier-man pairs under %d (only if that gate ran out); e.g. %s'
            % (name, n_, all_, seen, foreign, lo, hi, dc, ROOM_POST_CLEAR, hs[0]))
    # ---- the stations up to the seal hold: the loot place against every man
    st = P['stations']
    i_loot = max(i for i, s in enumerate(st) if s['kind'] == 'loot')
    for p in st[i_loot]['places']:
        near = [(round(RT.hdist(p, q)), n_.split('!')[-1]) for q, _gp, n_ in men if abs(q[1] - p[1]) <= RT.FLOOR_DY and RT.hdist(p, q) < ROOM_POST_CLEAR]
        if near:
            fail('the loot place (%d, %d, %d) is within %d of a man of %s' % (*p, *near[0]))
    # ---- a timer or a loot wait between the first gate and the seal hold
    wake_nodes = {h for g in gates for ref in g.get('wake', ()) for h in sc.resolve(ref)} if PRESSURE else set()
    for t in tops:
        first = next((k for k in range(t, sc.end[t]) if sc.names[k] == gates[0]['wait']), None)
        if first is None:
            continue
        seen, todo, stop = set(), [first], 0
        while todo:
            k = todo.pop()
            if k in seen:
                continue
            seen.add(k)
            if sc.names[k] == GATE_NAME:
                stop += 1
                continue
            if kind.get(k) == 'RandomTrigger':
                fail('%s: %s - a fork between the first gate and the seal hold: its other ways are places nobody checked against the men (second fix)' % (sc.names[t], sc.names[k]))
            elif kind.get(k) == 'DefendBehaviourRout':
                for ps in defend[k][1]:
                    q = B.at(sc.resolve(ps)[0])
                    nr = [(round(RT.hdist(q, p_)), n_.split('!')[-1]) for p_, _gp, n_ in men if abs(p_[1] - q[1]) <= RT.FLOOR_DY and RT.hdist(q, p_) < ROOM_STEP_CLEAR]
                    if nr:
                        fail('%s: %s has a place (%d, %d, %d) %d from a living man (%s) - under %d' % (sc.names[t], sc.names[k], *q, *nr[0], ROOM_STEP_CLEAR))
            if k in wake_nodes:                         # a squad modifier a gate wakes (the pressure fix): a side of the gate, not a link of the chain
                continue
            if kind.get(k) not in ('DefendBehaviourRout', 'TriggerActorsDead', 'RandomTrigger'):
                fail('%s: %s (%s) stands between the first gate and the seal hold - a timer behind a gate: a bot that arrives early waits again' % (sc.names[t], sc.names[k], kind.get(k)))
                continue
            todo += nxt.get(k, [])
        if not stop:
            fail('%s: the chain behind the first gate never reaches %s' % (sc.names[t], GATE_NAME))
    # ---- THE PRESSURE FIX: who is awake when, and the guns bearing (hold-guns)
    if PRESSURE:
        pressure_check(folder, B, P, tad, fail, log)
    if WAKE_MORE:
        wake_plan_check(folder, B, P, gates, tad, fail, log)
    # ---- the timetable
    tt = {k: P['gate'].get(k) for k in ('start', 'loot_cap', 'straight', 'path', 'exit_walk', 'seconds', 'rooms')}
    longest = float(tt['seconds'])
    in_s = float(P['gate'].get('in_straight', 0.0) or 0.0)
    quick = tt['start'] + in_s / GATE_SPEED + GATE_LOOT_MIN + tt['straight'] / GATE_SPEED + tt['rooms'] * P['gate'].get('room_g_min', ROOM_G_MIN) + longest
    slow_arrive = tt['start'] + in_s * 1.3 / GATE_SLOW + tt['loot_cap'] + tt['path'] / GATE_SLOW + tt['rooms'] * P['gate'].get('room_wait', ROOM_WAIT_S)
    slow_leave = slow_arrive + longest
    at_van = slow_leave + tt['exit_walk'] / GATE_SLOW
    # V2: the TYPICAL crew (every room ROOM_TYPICAL s: the men fall in 20 s, the walks at GATE_SPEED), judged; the crew held in every room's 30 s is a NOTE (it cannot fit:
    # the way in takes ~100 s and the five gates are TriggerActorsDead's own 30 s) and the round's clock ends the round with it still in the club
    typical = tt['start'] + in_s / GATE_SPEED + tt['loot_cap'] + tt['straight'] / GATE_SPEED + tt['rooms'] * ROOM_TYPICAL + longest + tt['exit_walk'] / GATE_SPEED
    if not P['gate'].get('seal_open') and quick < SEAL_AT + GATE_MORE - 0.1:
        fail('the quickest crew leaves the seal hold %.0f s after the round-start event, the seal\'s clock is at %g s' % (quick, SEAL_AT))
    if V2:
        log('  timetable V2 (s after the round-start event): the TYPICAL crew (way in %d m at %d u/s, loot %g s, every room %g s, the hold %g s) is at the exit trigger at %d s of %g (the van needs %g)' % (
            in_s / 100, GATE_SPEED, tt['loot_cap'], ROOM_TYPICAL, longest, typical, ROUND_CLOCK, ROOM_VAN_MARGIN))
        if typical > ROUND_CLOCK - ROOM_VAN_MARGIN:
            fail('the typical crew is at the exit trigger %.0f s after the round-start event; the round ends at %g and the van needs %g' % (typical, ROUND_CLOCK, ROOM_VAN_MARGIN))
        if at_van > ROUND_CLOCK - ROOM_VAN_MARGIN:
            log('  NOTE KNOWN: a crew held in every room (30 s each) is at the exit trigger %.0f s after the round-start event, past %g: the round clock ends the round with it in the club (V2 cannot fit that case: '
                'the way in alone is %d m)' % (at_van, ROUND_CLOCK - ROOM_VAN_MARGIN, in_s / 100))
    elif at_van > ROUND_CLOCK - ROOM_VAN_MARGIN:
        fail('a crew held in every room is at the exit trigger %.0f s after the round-start event; the round ends at %g and the van needs %g' % (at_van, ROUND_CLOCK, ROOM_VAN_MARGIN))
    log('  timetable (s after the round-start event, GO is about 8.5 later): the quickest crew (every room %g s) leaves the seal hold at %d s (clock %g s); '
        'a crew that wins nothing (30 s a room) reaches the hold at %d s, leaves it at %d s and is at the exit trigger at %d s of the round\'s %g (the van is called there: %g s of margin)'
        % (P['gate'].get('room_g_min', ROOM_G_MIN), quick, SEAL_AT, slow_arrive, slow_leave, at_van, ROUND_CLOCK, ROUND_CLOCK - at_van))
    # ---- the men that moved are where CLEAR_MEN puts them
    for path, post in (dict(CLEAR_MEN, **PRESSURE_MEN) if PRESSURE else CLEAR_MEN).items():
        try:
            g_ = A.node_of(sc, path)
        except Exception:
            g_ = None
        if g_ is None:
            fail('CLEAR_MEN: %s is not in the level' % path)
            continue
        k = next((c for c in range(g_, sc.end[g_]) if sc.cls(c) == 'ZFFActor'), None)
        if k is None or math.dist(B.at(k)[::2], (post[0], post[2])) > 60.0:
            fail('CLEAR_MEN: %s stands at %s, not at %s' % (path, tuple(round(c) for c in B.at(k)) if k else None, post))
    log('  rooms: the men that stay within 250 of the way by the design of their room (%d lines, ROOM_STAY), %d were moved (CLEAR_MEN): %s' % (len(ROOM_STAY), len(CLEAR_MEN), '; '.join(s.split(':')[0] for s in ROOM_STAY)))
    log('kl_fa_club.rooms_check %s: %d rooms, %s' % (folder, len(gates), 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# THE BUILD'S FLAGS TRAVEL WITH THE FOLDER (review round 1): bots, bots-check, check and finish run in other processes than the build,
# so the flags a variant was built with are kept in van.json ('flags') and read back by load_flags. A folder without them is a build
# with the defaults.
FLAG_NAMES = ('HELI', 'DOORS_ANIMATE', 'SEAL_OPEN', 'SEAL_PLANE', 'SEAL_AT', 'LIGHT_SHOW', 'BEAT_ANIM', 'FAN_DAMAGE', 'CASE', 'NO_AI', 'SQUADS_AWAKE',
              'POLICE_ARRIVE', 'POLICE_ON_SLAB', 'STOCK_ROWS', 'OFFICE_AT', 'STREAM',
              'GUARDS_OFF', 'POLICE_EAST', 'VAN_LATE', 'RESET', 'VOICE', 'LOOT_SECONDS', 'ROOM_GATES', 'PRESSURE', 'WAKE_MORE', 'V2')
STREAM = None                           # '--str FILE': the merged stream file the clips are resolved against (review round 2: it travels in van.json)


def flags_of():
    """The module's build flags now -> dict (written to van.json)."""
    g = globals()
    return {k: g[k] for k in FLAG_NAMES}


def load_flags(folder, log=print):
    """Set the build flags from <folder>/van.json ('flags'), if it has them. -> True if it did."""
    import json
    try:
        with open(os.path.join(folder, 'van.json'), encoding='utf-8') as f:
            fl = json.load(f).get('flags')
    except (OSError, ValueError):
        fl = None
    if not fl:
        return False
    g = globals()
    fl = dict(fl)
    for k, v in LEGACY_FLAGS.items():                   # a folder of the first delivery has none of the fix's flags: it IS the legacy build
        fl.setdefault(k, v)
    changed = {k: v for k, v in fl.items() if k in FLAG_NAMES and g[k] != v}
    g.update({k: v for k, v in fl.items() if k in FLAG_NAMES})
    set_roles()
    set_route()
    set_v2()
    if g['STREAM']:
        BK.use_stream(g['STREAM'])
    if changed:
        log('  kl_fa_club: the build flags of %s (van.json): %s' % (folder, ', '.join('%s = %s' % kv for kv in sorted(changed.items()))))
    return True


def test(out, keep=False, log=print, plan=None):
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1. Beside the archive: van.json
    (the van's plan, what was done to F07's van, kl_map_escape.van_check's report: kl_map_escape.van_build's form)."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], flags=flags_of(),
                                          check=None if HELI else van_check(folder, lambda *a: None, plan)[0]), f, indent=1, default=str)
    bad = check(folder, log, r['problems']) + late
    log('level: %d entities, %d rooms, %.0f MB' % (r['entities'], r['rooms'], r['archive_mb']))
    if not keep:
        for f in os.listdir(folder):
            if '_Main' in f:
                os.remove(os.path.join(folder, f))
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        global DOORS_ANIMATE, SEAL_OPEN, SEAL_PLANE, SEAL_AT, LIGHT_SHOW, BEAT_ANIM, FAN_DAMAGE, CASE
        global NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, POLICE_ON_SLAB, STOCK_ROWS, OFFICE_AT, STREAM
        global GUARDS_OFF, POLICE_EAST, VAN_LATE, RESET, VOICE, LOOT_SECONDS, LEGACY, ROOM_GATES, PRESSURE, WAKE_MORE, V2
        LEGACY = '--legacy' in a                        # the first delivery's build: every flag of the fix after run C2 off, the old numbers
        V2 = not LEGACY and '--v1' not in a            # VERSION 2 (entrance start): the default; --v1 is the round of c_club5
        GUARDS_OFF = not LEGACY and '--no-guards-off' not in a
        POLICE_EAST = not LEGACY and '--no-police-east' not in a
        VAN_LATE = not LEGACY and '--no-van-late' not in a
        RESET = not LEGACY and '--no-reset' not in a
        VOICE = not LEGACY and '--no-voice' not in a
        ROOM_GATES = not LEGACY and '--no-gates' not in a and '--no-ai' not in a
        PRESSURE = ROOM_GATES and '--no-pressure' not in a
        WAKE_MORE = PRESSURE and not V2 and '--no-wake-boxes' not in a     # (V2: the boxes would wake the sleepers on the way IN)
        LOOT_SECONDS = 30 if LEGACY else LOOT_SECONDS
        if LEGACY:
            SEAL_AT = LEGACY_FLAGS['SEAL_AT']
        set_roles()
        set_v2()
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        POLICE_ON_SLAB = '--police-strip' not in a
        STOCK_ROWS = '--dead-men-rows' not in a
        def value(name, cast=str):                      # the argument after an OPTION; a message, not an IndexError, when it is missing
            i = a.index(name) + 1
            if i >= len(a) or a[i].startswith('--'):
                sys.exit('kl_fa_club: %s needs a value' % name)
            try:
                return cast(a[i])
            except ValueError:
                sys.exit('kl_fa_club: %s: "%s" is not a %s' % (name, a[i], cast.__name__))
        global HELI
        if '--exit' in a and value('--exit') == 'heli-roof':
            # OPTIONAL stage (AA, step 2): the two-step chain builds and check() runs; the chopper's flight, boxes, camera, roof way are NOT placed (re/club_campaign.md AA)
            if '--v1' in a or LEGACY:
                sys.exit('kl_fa_club: --exit heli-roof belongs to Version 2 (not --v1 / --legacy)')
            HELI = True
            set_roles()
            set_route()
        elif '--exit' in a and value('--exit') != 'van-slab':
            sys.exit("kl_fa_club: --exit %s: only 'van-slab' and (partial) 'heli-roof' are built" % value('--exit'))
        if '--v1' in a and '--exit' in a:
            sys.exit('kl_fa_club: --exit belongs to Version 2; --v1 is the round of c_club5')
        if '--seal-open' in a and ('--seal-plane' in a or '--seal' in a):
            sys.exit('kl_fa_club: --seal-open (no seal at all) contradicts --seal-plane and --seal S')
        if '--no-ai' in a and ('--squads-awake' in a or '--dead-men-rows' in a or '--office' in a):
            sys.exit('kl_fa_club: --no-ai (no enemies) contradicts --squads-awake, --dead-men-rows and --office S')
        if '--no-police' in a and '--police-strip' in a:
            sys.exit('kl_fa_club: --no-police contradicts --police-strip')
        if '--police-slab' in a and '--police-strip' in a:
            sys.exit('kl_fa_club: --police-slab contradicts --police-strip')
        if '--str' in a:                                # OPTION, the stream file the clips are resolved against
            STREAM = os.path.abspath(value('--str'))
            BK.use_stream(STREAM)
        if '--office' in a:                             # OPTION, seconds from the round-start event to the front office's guards
            OFFICE_AT = value('--office', float)
        DOORS_ANIMATE = '--doors-animate' in a
        SEAL_OPEN = '--seal-open' in a or V2             # V2: nothing is sealed (the crew starts outside)
        SEAL_PLANE = '--seal-plane' in a
        LIGHT_SHOW = '--light-show' in a
        BEAT_ANIM = '--beat-anim' in a
        FAN_DAMAGE = '--fan-damage' in a
        CASE = None if '--loot-bags' in a else CASE
        if '--seal' in a:                               # OPTION, seconds from the round-start event to the seal's end
            SEAL_AT = value('--seal', float)
        plan = plan_of(value('--plan')) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 2 and a[0] == 'donor':                # STEP 1 of the heli chain (AA): R09 = F07 + M06's chopper, offline, into <out>/chain
        r = heli_donor(a[1])
        sys.exit(0 if r.get('ok') and not r.get('problems') else 1)
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']        # the escape cameras' table (L_ keeps the Pavement it was read with)
        print('kl_fa_club.van-check %s: %d fault(s) on the drawn pavement; the plain kl_map_escape.van_check has %d, %d of them \'no ground under it\'' % (
            a[1], len(rep['faults']), len(bare), sum('no ground under it' in x for x in bare)))
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) == 3 and a[0] == 'bots':
        load_flags(a[1])
        res = bots(a[1], a[2])
        print('kl_fa_club.bots: %s' % (res[0] if isinstance(res, tuple) else res))
    elif len(a) == 3 and a[0] == 'dyn':
        load_flags(a[1])
        out, _rep = dyn(a[1], a[2])
        sys.exit(1 if any(x == 'FAIL' for x, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'wake':
        sys.exit(wake_step(a[1]))
    elif len(a) == 2 and a[0] == 'bots-check':
        load_flags(a[1])
        sys.exit(1 if bots_check(a[1]) else 0)
    elif len(a) >= 2 and a[0] == 'hold-guns':           # the pressure table of finished folders (the numbers, the wake table read off the scene; no checking)
        import json
        import kl_fa_bots as F
        for fo in a[1:]:
            load_flags(fo)
            with open(os.path.join(fo, 'bots.json'), encoding='utf-8') as f:
                P = json.load(f).get('plan') or {}
            if not P.get('club_gates'):
                print('hold-guns %s: no room gates in this folder (a build with --no-ai / --no-gates / --legacy): nothing to count' % fo)
                continue
            B = F.Built(fo)
            tad = {k: v for k, _i, v in kl_fa.controllers(B.sc, 'TriggerActorsDead')}
            wake = scene_wake(B, P, tad)
            fire = Fire(B, wake)
            print('hold-guns %s: wake table (the gate at whose hold a squad is awake): %s' % (fo, {n.split('!')[-1]: w for n, w in wake.items()}))
            for r in gun_table(B, P, fire):
                print('  gate %-8s guns on the 7 holds %s worst %d (%d with the men of earlier gates dead) | the walk: worst %d at %s (%d with them dead; %d samples) | holds: %s | walk: %s' % (
                    r['name'], r['holds'], r['hold_worst'], r['hold_dead'], r['leg_worst'], r['leg_at'], r['leg_dead'], r['samples'], ', '.join(r['who_hold'][:6]), ', '.join(r['who_leg'][:6])))
    elif len(a) == 2 and a[0] == 'strays':
        BK.seal(a[1])                   # kl_fa_bank.seal: stray room-list entries (not this level's entrance SEAL)
    elif len(a) == 2 and a[0] == 'finish':
        load_flags(a[1])
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        load_flags(a[1])
        sys.exit(1 if check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'inventory':
        load_flags(a[1])
        inventory(a[1])
    elif len(a) == 2 and a[0] == 'reverify':
        bad = BK.reverify(a[1])
        print('kl_fa_club.reverify %s: problems: %d' % (a[1], len(bad)))
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_club                   # kl_graft imports this file by name: one module, one set of flags
    kl_fa_club.main()
