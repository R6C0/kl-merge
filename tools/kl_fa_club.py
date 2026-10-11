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

    python kl_fa_club.py test <out> [--keep] [options]    build F07 + M05_A with the layer into <out> (build():
                                                          a bare graft first, for the van's plan, then the level
                                                          inside kl_map_escape.van_layer), finish() on the written
                                                          level, check(); exit 1 if a problem is left that is not
                                                          in KNOWN. Beside the archive: van.json
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
      --police-slab     the arriving police come into the world ON the pavement's collision slab, at its two
                        ends and in sight, instead of out of sight on the mesh strip beside it, where there is
                        no collision floor (ARRIVE_SLAB: the fall-back if a man cannot stand there)
      --office S        seconds from the round-start event to the front office's guards (default OFFICE_AT)
      --dead-men-rows   the guards keep Dead Men's soldier rows (default: stock Fragile Alliance rows by weapon)
      --str FILE        Dead Men's streamed clips are resolved against FILE and FILE.map.json instead of the
                        work folder's merged PC_Def.str (kl_fa_bank.use_stream): for the build against a stream
                        file that holds the club's music (MUSIC_CLIPS; the extension is a later step)
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
POLICE = [(float(x), SLAB[2], -2760.0) for x in (900, 1000, 1100, 1200, 1300, 1400, 1500)]
# the eight police bodies (Heroes!Henchmen_0n) beside those points. GUESS
BODIES = [(p[0], p[1], p[2] - 70.0) for p in POLICE] + [(1600.0, SLAB[2], -2830.0)]
# team mode's respawn stages: the front office, the wardrobe, the entrance hall. GUESS: the points beside each
STAGE_B = [(1900.0, 354.0, 3300.0), (2000.0, 354.0, 3300.0), (2100.0, 354.0, 3300.0), (2000.0, 354.0, 3400.0)]
STAGE_C = [(-4.0, 180.0, -240.0), (96.0, 180.0, -240.0), (196.0, 180.0, -240.0), (-4.0, 180.0, -150.0)]
STAGE_D = [(-450.0, 100.0, -600.0), (-350.0, 100.0, -600.0), (-450.0, 100.0, -680.0), (-350.0, 100.0, -680.0)]
WEST, SOUTH = (-1.0, 0.0), (0.0, -1.0)
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz), or a place looked at)
SPAWN = {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), LANE_MOUTH),
         # the other modes' criminals stand in the office too, in rows of their own (it is 46 m2 of mesh: the rows are near)
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (-50, 0, -35), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (-50, 0, -35), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, -45), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (50, 0, -35), LANE_MOUTH),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': ([(float(x), OFFICE, float(z)) for z in (2750, 2850, 2950, 3050) for x in (2650, 2750)], (0, 0, 0), DOOR_IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), WEST),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), SOUTH),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), SOUTH),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (50, 0, 40), SOUTH),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (-50, 0, -35), LANE_MOUTH)}

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
SEAL_AT = 120.0                         # s from the round-start event (about 111 s after GO) to the seal's end: nobody is ever
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
#   he falls into a kill box and the wave does not come: POLICE_ON_SLAB ('--police-slab') puts the ten on the slab.
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
ARRIVE_START = '10_RunToCover'
ARRIVE_Y = SLAB[2] + 1.0                # a man's height on the pavement (F07's stand 1 over their floor)
POLICE_ARRIVE = True                    # False ('--no-police'): none of the four squads is kept
POLICE_ON_SLAB = False
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


def police():
    """The squads of F07 that arrive in this build."""
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_club.KEEP at the moment of use
        keep = _KEEP + tuple(police())
        return keep + tuple(x for x in KEEP_MORE if x not in keep)
    raise AttributeError(name)

# F07's cover list goes: M05_A's own top-level 'CoverList' stays through the campaign pre-pass (kl_maps.PASSIVE), and
# a second FFCoverList is an assert in its init (kl2 0x6682c5; kl_fa_author.DROP)
DROP = ('Specials!CoverPoints!*',)

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
        want = {'men': [y3(p) for p in (ARRIVE_SLAB[name] if POLICE_ON_SLAB else men)], ARRIVE_START: [y3(p) for p in cover],
                '10_Defend': [y3(defend)], '40_RunToEscape': [at]}      # (nothing names the last two: kl_fa_bank.HALL's note)
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
            stage, child = SQUADS[name]
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
    if PLAN is None:
        raise ValueError(NO_PLAN)
    Doors.arm(log)                                      # the build that follows opens the doors (see Doors)
    for name, (pos, face, half, _why) in PLACE.items():
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
            pts, face = (START, DOOR_IN) if crook else (BODIES, LANE_MOUTH)
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
    S.van = ESC.van_prepare(S, PLAN, log)
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
    for path, hint in MEN.items():
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
        st = SQUADS[n][0]
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
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['walk'])
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['floor'])
    lists('floors counter', 'TriggerCounter', f0=max(len(beat), 1), f4=([R + ROLE['seal off']] if seal and beat else []) + ([ways[0]] if beat else []))

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it. This layer's:
    # the seal's clock, the front office's timer, and the doors' timer (DOORS_ANIMATE) or the music's muffle switch
    # (the doors are open)
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['seal timer']] + ([R + ROLE['office timer']] if stage['office'] else []) + [R + ROLE['doors timer'] if DOORS_ANIMATE else R + ROLE['muffle']]
    lists('monitor', 'AIMonitor', f2=have + start)
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
    lists('seal timer', 'TriggerDelay2', f0=SEAL_AT, f4=([R + ROLE['seal off']] if seal else []) + ([ways[1]] if enemies_in else []))
    lists('seal off', 'DeactivateGeom', f0='AITrigger', f1=seal)

    # ---- the way out: F07's 'exit heist' box in the wardrobe, with a line that fits a front door
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    # ---- the escape: every exit trigger of the level (there is F07's one) calls the van - field 0 false, field 2
    # the van's group, 1 and 3..5 empty, the form the three car maps on the tab have (kl_map_escape.van_wire). The
    # rest of the round's last stage is F07's own and stays as the graft left it (kl_fa_bank.wire's note)
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
        by = collections.Counter(SQUADS[n][0] for n in plan)
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
        return ([] if DOORS_ANIMATE else [p for p, _at, _set in LEAVES]) + [p for p, _at, _set in SEAL if p not in standing]

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
ROUTE_IN = [('START', START[1]), ('inner office door', (2600, 347, 3313)), ('front office', (2000, 354, 3300)), ('walkway', (780, 371, 2747)),
            ('dance floor 2', (-864, 40, 2491)), ('dance floor 1', (-1100, 20, 1150)), ('stair landing', (-55, 160, 320)),
            ('wardrobe', (-4, 180, -240)), ('entrance hall', (-414, 100, -604)), ('queue lane, club end', (105, 20, -1500))]
ROUTE_OUT = [('queue lane, street end', (105, 20, -2600)), ('pavement', ESC_AT)]
# the walk test of the loot's pick-up: (box x0, x1, z0, z1; places the route test reaches) for the office, dance floor 1
# and the wardrobe / entrance. GUESS: the three boxes (each room with a margin); the places are stations of ROUTE_IN
LOOT_WALKS = (((2300.0, 3400.0, 2000.0, 3600.0), [START[1]]), ((-2000.0, 100.0, 400.0, 1700.0), [(-1100.0, 20.0, 1150.0)]),
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
    pts, names = [START[1]], ['START']
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
    log('  ENTERS box x %d..%d, y %d..%d, z %d..%d: %d of the 8 START points and %d of the office\'s %d cases inside' % (
        lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], sum(inside(p) for p in START), sum(inside(p) for p in office), len(office)))
    if not all(inside(p) for p in START) or not all(inside(p) for p in office) or len(office) != 6:
        fail('the ENTERS box does not hold every START point and the six cases of the office')
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
    starters = {R + ROLE['seal timer'], R + ROLE['doors timer'] if animate else R + ROLE['muffle']} | ({R + ROLE['office timer']} if named('office timer') else set())
    if {s for s in mon if s[5:] in ROLE.values()} != starters:
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
        rows2 = kl_route.stations(lv, [START[1]] + [at(k) for k in men], opened=gates, near=30)
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
        rows3 = kl_route.stations(lv, [START[1]] + pts2, opened=gates, near=30) if pts2 else [None]
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
            st, child = SQUADS[sc.names[t]]
            by[st] += 1
            want = 1 if st == 'load' or awake else 0
            if f3[t] != want:
                fail('%s: ZSquadScript field %d is %s, stage \'%s\' wants %d' % (sc.names[t], SQUAD_ACTIVE, f3[t], st, want))
            if child:
                j = A.node_of(sc, sc.names[t] + '\\' + child)
                if j not in named_by[st]:
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
        late = [(k, SQUADS[top_of(k)][0]) for k in men if top_of(k) in SQUADS and SQUADS[top_of(k)][0] != 'load' and not awake] \
            + [(k, 'open') for k in men if top_of(k) in ARRIVE]
        worst, in_sight = collections.defaultdict(lambda: (9e9, 0)), []
        for k, st in late:
            p = at(k)
            eyes = [v for v in views[st] if S.seen(v, p)]
            near = min(math.dist(v, p) for v in views[st])
            worst[st] = (min(worst[st][0], near), worst[st][1] + 1)
            if eyes and top_of(k) in ARRIVE and on_slab(p) and near >= LATE_CLEAR:
                in_sight.append(k)                      # a '--police-slab' build: on the slab's ends, in sight - what that fall-back costs
            elif eyes or near < LATE_CLEAR:
                fail('%s at (%d, %d, %d) comes into the world at stage \'%s\' %s' % (sc.path[k][5:][-60:], *p, st, 'in sight of %d of the %d places the crew can be '
                     'then, the first (%d, %d, %d)' % (len(eyes), len(views[st]), *eyes[0]) if eyes else '%d from such a place (%d wanted)' % (near, LATE_CLEAR)))
        log('  enemies: who comes into the world after the load, by stage (men, places the crew can be then, the nearest man to one): %s - %s' % (
            ', '.join('%s %d / %d / %d' % (st, worst[st][1], len(views[st]), worst[st][0]) for st in ('office', 'walk', 'floor', 'open') if st in worst) or 'nobody',
            'POLICE ON THE SLAB: %d of the police come into the world IN SIGHT of a place in the queue lane (the cost of that fall-back)' % len(in_sight) if in_sight
            else 'in sight of one: see the FAIL lines' if any('comes into the world' in b for b in bad) else 'nobody in sight of one'))
        rows_ = collections.Counter((values(sc, k, 'ZSoldier')[3], values(sc, k, 'ZSoldier')[4], values(sc, k, 'ZSoldier')[7]) for k in men if top_of(k) in SQUADS)
        stock = sum(n for (skill, _a, _h), n in rows_.items() if skill == 'eCustom')
        log('  enemies: soldier rows of the campaign\'s men (skill, accuracy, health): %s' % ', '.join('%d x %s %g / %g' % (n, *r) for r, n in sorted(rows_.items(), key=lambda t: -t[1])))
        if 0 < stock < sum(rows_.values()):
            fail('%d of the campaign\'s %d men have a stock row, the others Dead Men\'s' % (stock, sum(rows_.values())))
    else:
        log('  enemies: none (a build without squads); the seal opens by its clock')
        for role, kind, f in (('office timer', 'TriggerDelay2', 4), ('walk box', 'TriggerBox', 17), ('floor box', 'TriggerBox', 17), ('floors counter', 'TriggerCounter', 4)):
            if values(sc, A.node_of(sc, ROLE[role]), kind)[f]:
                fail('no squad is in the level, but %s names %s' % (ROLE[role], values(sc, A.node_of(sc, ROLE[role]), kind)[f]))
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
    if len(vans) != 1 or len(fakes) != 1 or len(ex) != 1:
        fail('%d OnlineEscAnimatedVehicle, %d FakeTarget, %d exit triggers (one each is wanted: an unused van\'s target is the 0x686a66 crash)' % (len(vans), len(fakes), len(ex)))
    else:
        lo, hi = world_box(ex[0])
        ev = values(sc, ex[0], kl_fa.EXIT)
        in_exit = lambda p: all(lo[a] <= p[a] + (50 if a == 1 else 0) <= hi[a] for a in range(3))
        mark = pos[ents[A.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea') - 1]]
        on_slab = SLAB[0][0] <= lo[0] and hi[0] <= SLAB[0][1] and SLAB[1][0] <= lo[2] and hi[2] <= SLAB[1][1]
        log('  exit box x %d..%d, z %d..%d: on the slab %s; holds the pavement station %s, the lane\'s street end %s; it names %s; the escape marker at (%d, %d, %d)' % (
            lo[0], hi[0], lo[2], hi[2], on_slab, in_exit(ESC_AT), in_exit(ROUTE_OUT[0][1]), [s.split('\\')[-1] for s in ev[2:6] if s], *mark))
        if not on_slab or not in_exit(ESC_AT) or in_exit(ROUTE_OUT[0][1]) or [s for s in ev[2:6] if s] != [R + VAN + '\\' + VAN_GROUP] \
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
    if stop_at_all := (len(vans) == 1 and len(fakes) == 1 and len(ex) == 1 and 'stop' in rep):
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
        rows4 = kl_route.stations(lv, [START[1], board, tuple(stop)], opened=gates, near=BOARD_NEAR)
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
            *wait, math.dist(wait, stop) / 100.0, 'ON' if kl_route.stations(lv, [START[1], tuple(wait)], opened=gates, near=BOARD_NEAR)[1]['mesh'] else 'off', '; from '.join(seen)))
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
    # ---- kl_graft.verify's cross-references on the level AS WRITTEN (the build's own verify ran before finish())
    for b in BK.reverify(folder, log):
        fail('written level: ' + b[:200])
    log('kl_fa_club.check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


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
    for name, (_p, _f, _h, why) in PLACE.items():
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
    try:
        with ESC.van_layer(plan, log) as st, doors(log):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_club', m_drop=M_DROP, flat=flat)
    except ValueError:                                  # van_layer: 'a step of the van did not run'. After a build that
        if r.get('ok') or not r:                        # failed (r says why) that is no news; after one that did not, it is
            raise
    finally:
        for c in lent:
            del kl_maps.FLAT[c]
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


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
BOT_OPT = {'stops': 1, 'cases': 'glass', 'lane': True, 'window': True, 'loot_seconds': 30,
           'park': [ESC_AT[0], ESC_AT[1], ESC_AT[2] + 80.0]}
# GUESS: the bots end beside the van's lane, 0.8 m south of the escape marker's place. kl_fa_bots wants the AllyEscapeBox PARK_SIDE
# (420) to the side of the van's line (z -3100) and the slab's north edge is z -2650; the van's body must not sweep it.
GATE_AT = (400.0, 100.0, -150.0)        # GUESS: the entrance hall, 13 m before the queue lane (z -1500); the way station nearest to it is the hold
GATE_MORE = 5.0                         # s on top of SEAL_AT. GUESS
GATE_SPEED = 400.0                      # units a second the FASTEST bot is taken to walk from the start to the hold (the step is a walk, not a sprint). GUESS:
                                        # an estimate that is too high only makes the hold longer for every bot
GATE_MIN = 10.0                         # s: no hold shorter than this
GATE_NAME = '040_Timer_seal_opens'      # no 'done_looting' in it: kl_fa_bots.check and kl_fa_bots_dyn take it for a wait that is no loot wait


def bots_gate(B, P, log=print):
    """kl_fa_bots' plan P of built level B with the SEAL GATE -> P (changed in place). The round's beat seals the entrance from the
    load; it opens when both dance-floor squads are dead or SEAL_AT seconds after the round-start event, whichever comes first.
    Nothing is known to stop an AI at the heroes-only seal, but the bots should come to the queue lane when it is open and not
    before: after the loot stop the way station nearest GATE_AT is a hold (stop 1) of plain-timer seconds = SEAL_AT + GATE_MORE minus
    the time the fastest bot needs to be there (kl_fa_bots' start delay + the straight way / GATE_SPEED), then the way out."""
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
    seconds = max(GATE_MIN, round(SEAL_AT + GATE_MORE - start - straight / GATE_SPEED))
    steps = [dict(s) for s in first]
    for k in range(0, len(before), 3):
        steps.append({'name': '%03d_DefendBehaviour_to_loot' % (30 + k // 3), 'leg': 'in', 'stop': 1, 'stations': before[k:k + 3]})
    for m, k in enumerate(range(0, len(after), 3)):
        steps.append({'name': '%03d_DefendBehaviour_out' % (50 + m), 'leg': 'out', 'stop': None, 'stations': after[k:k + 3]})
    P['steps'] = steps
    P['waits'] = [P['waits'][0], collections.OrderedDict(name=GATE_NAME, stop=1, seconds=seconds, loot=[], worth=0, timer='038_Timer_at_cases',
                                                       relays=[], cases={})]
    P['stations'][i_gate]['what'] = 'the hold before the queue lane until the seal is open (%g s)' % seconds
    P['gate'] = {'station': i_gate, 'seconds': seconds, 'straight': round(straight), 'seal_at': SEAL_AT, 'places': P['stations'][i_gate]['places']}
    note = ('THE SEAL GATE: station %d (round %s) is a hold of %g s, a plain timer (%s): SEAL_AT %g s + %g, minus the start delay %g s and the fastest '
            'bot\'s straight way of %d / %g'
            % (i_gate + 1, tuple(round(v) for v in mid(i_gate)), seconds, GATE_NAME, SEAL_AT, GATE_MORE, start, straight, GATE_SPEED))
    P['notes'].append(note)
    log('  NOTE ' + note)
    log('steps: %s' % [(s['name'], s['stations']) for s in steps])
    return P


def bots(src, dst, log=print):
    """The seven AI heisters into a COPY of a finished build of this level: kl_fa_bots.build with BOT_OPT and the seal gate
    (bots_gate) -> (kl_fa_bots' findings, its report). The dynamic step, guns and the rest are the other tools' own commands."""
    import kl_fa_bots as F
    plan0 = F.plan
    F.plan = lambda B, opt=None, log=print: bots_gate(B, plan0(B, opt, log), log)
    try:
        return F.build(src, dst, dict(BOT_OPT), log)
    finally:
        F.plan = plan0


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
    log('kl_fa_club.bots_check %s: %d squads, %d with the seal gate (%s, longest %g s; seal clock %g s): %s' % (
        folder, len(tops), n_gate, GATE_NAME, longest, SEAL_AT, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


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
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'],
                                          check=van_check(folder, lambda *a: None, plan)[0]), f, indent=1, default=str)
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
        global NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, POLICE_ON_SLAB, STOCK_ROWS, OFFICE_AT
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        POLICE_ON_SLAB = '--police-slab' in a
        STOCK_ROWS = '--dead-men-rows' not in a
        if '--str' in a:                                # OPTION, the stream file the clips are resolved against
            BK.use_stream(a[a.index('--str') + 1])
        if '--office' in a:                             # OPTION, seconds from the round-start event to the front office's guards
            OFFICE_AT = float(a[a.index('--office') + 1])
        DOORS_ANIMATE = '--doors-animate' in a
        SEAL_OPEN = '--seal-open' in a
        SEAL_PLANE = '--seal-plane' in a
        LIGHT_SHOW = '--light-show' in a
        BEAT_ANIM = '--beat-anim' in a
        FAN_DAMAGE = '--fan-damage' in a
        CASE = None if '--loot-bags' in a else CASE
        if '--seal' in a:                               # OPTION, seconds from the round-start event to the seal's end
            SEAL_AT = float(a[a.index('--seal') + 1])
        plan = plan_of(a[a.index('--plan') + 1]) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']        # the escape cameras' table (L_ keeps the Pavement it was read with)
        print('kl_fa_club.van-check %s: %d fault(s) on the drawn pavement; the plain kl_map_escape.van_check has %d, %d of them \'no ground under it\'' % (
            a[1], len(rep['faults']), len(bare), sum('no ground under it' in x for x in bare)))
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) == 3 and a[0] == 'bots':
        res = bots(a[1], a[2])
        print('kl_fa_club.bots: %s' % (res[0] if isinstance(res, tuple) else res))
    elif len(a) == 2 and a[0] == 'bots-check':
        sys.exit(1 if bots_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'strays':
        BK.seal(a[1])                   # kl_fa_bank.seal: stray room-list entries (not this level's entrance SEAL)
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'inventory':
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
