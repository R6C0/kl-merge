#!/usr/bin/env python3
"""
The Fragile Alliance layer of LAST CALL: the Tokyo night club (Dead Men M05_A, chapter 5 'The Mizuki', alone,
under Dog Days F07). Authored from stock objects, offline, on the pattern of kl_fa_bank.py (The Vault), whose
generic parts are IMPORTED from there (the doors' frame arithmetic, the text and reading helpers, reverify);
none of its tables. The study: re/campaign_fa_club.md (its section 8 weighs more than the first text),
re/campaign_fa.md 4.2 and G1.3 / G1.8; the build stage by stage, every check with its output and what only a
live run can settle: re/club_campaign.md. Nothing here installs anything or starts the game.

THIS FILE IS THE FIRST HALF (stage L1): a round WITHOUT ENEMIES and without the escape's drive. NO_AI is True
and nothing here can make it False yet; F07's van only stands where it may wait (VAN_WAIT). The squads, the
police that arrive and the beat's 'floor cleared' switch are stage L2, the van's drive stage L3.

    python kl_fa_club.py test <out> [--keep] [options]    build F07 + M05_A with the layer into <out> (build()),
                                                          finish() on the written level, check(); exit 1 if a
                                                          problem is left that is not in KNOWN
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
      --no-ai           accepted and true in any case: this half keeps no squad

THE ROUND (re/campaign_fa.md 4.2)
  START   shut in Yoko's office over dance floor 2 with the money: two rows of four, six briefcases on and
          beside her desk and the sofa table. The ENTERS box lies round the START rows, so the office loot counts.
  OUT     the inner and the outer office door (open from the load: DOORS) -> front office -> the walkway down
          to dance floor 2 -> dance floor 1 (three cases on the long bar) -> the stair landing -> the wardrobe
          (a case on the coat check's counter) -> the entrance hall -> the entrance door (open in the level)
          -> the ticket counter (a case on its shelf) -> the queue lane -> the pavement.
  BEAT    'exit blocked': the street end of the queue lane is sealed from the load by the campaign's own
          invisible collision (SEAL) and opens SEAL_AT seconds after the round-start event - a clock that
          takes the seal away whatever else happens. The next stage adds the faster way: both dance-floor
          squads dead.
  ESCAPE  the exit box and the escape marker lie on the pavement, on the only collision floor outside the
          building (the slab: x -1200..1800, z -3450..-2650, y 30). Bound trios stand outside its three open
          edges and kill boxes under them: beyond the slab the street is drawn and not there (BOUNDS, KILL).

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
# ... and in a build without enemies, which check() knows by the level having no squad at all (this half always)
KNOWN_NO_AI = ('no ZSquadScript', 'a round without enemies (NO_AI): this half of the layer, and the build for a first live run')
NO_AI = True                            # THIS HALF: no squad of the campaign stays (campaign_names), none of F07's police

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
# police who come back: the pavement, both sides of the lane's mouth and clear of it. The lane is sealed until
# the beat: until then they are outside the round, as the campaign's own dead-end has it. Rows at z -2760 and
# nearer the wall than z -2850: the next stage's van drives along the slab (the study: z -3100, a lane 220 wide)
# and wants 250 either side of its line free of spawn points. GUESS: the points
POLICE = [(float(x), SLAB[2], -2760.0) for x in (-900, -800, -700, -600, 1300, 1400, 1500)]
# the eight police bodies (Heroes!Henchmen_0n) beside those points. GUESS
BODIES = [(p[0], p[1], p[2] - 70.0) for p in POLICE] + [(-1000.0, SLAB[2], -2830.0)]
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
SEAL_AT = 75.0                          # s from the round-start event (about 66 s after GO) to the seal's end. GUESS (the
                                        # study's 75 s 'at the latest'): nobody is ever locked in. '--seal S'
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
ESC_AT = (300.0, SLAB[2], -2800.0)      # the escape marker's place on the slab, 1.8 m east of the lane's mouth. GUESS; the next
ESC_POI_UP = 188.0                      # stage holds it against its van's drive (kl_fa_bank.LANE_CLEAR). The marker over the floor
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
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
# FOR THE NEXT STAGE. Free single top-level objects of F07 this file does not touch yet (add the name to KEEP_MORE,
# give it a ROLE): trigger boxes Gameplay!010_FirstFight!tb_LEFT_TheySpotYou / tb_RIGHT_TheySpotYou,
# Gameplay!020_Loot!tbExitLoot, ...!FollowPlayers!tbCountPlayers, Gameplay!030_AfterLoot!tbExitFinancialAlley,
# Gameplay!040_Escape!tbEscapeAI, Gameplay!RunToEscape!tbRunToEscape / tbRunToEscape1Player; counters
# Gameplay!020_Loot!FollowPlayers!TriggerCounter (the 'both dance-floor squads dead' counter), Gameplay!RunToEscape!
# tcRunToEscape; TriggerDelay2 Gameplay!010_FirstFight!RivalMercs!Timer, ...!RandomizeFight!Timer_LEFT / _RIGHT,
# ...!DisableVisionBlocker!Timer / TimerInputAI, ...!RivalMercVan!Timer_PFBlocker, ...!CoverStateChangerHero!Timer,
# ...!TimerMercsVanExit, six of ...!Shutters! and three of Gameplay!RunToEscape!; AIDWrapper ...!CoverStateChangerHero!
# ActivateCovers / DeactivateCovers and four ...!Shutters!Activator_*; ActivateGeom ...!Shutters!GeomActivator_TearGas_LEFT
# / _RIGHT; DeactivateGeom ...!RivalMercs!DisableVisionBlocker!GeomDeactivator. F07's AIMonitor names five timers of
# its opening at the round start: wire() writes that list, so that a ROLE object is started only by what this file names.
KEEP_MORE = ()
# the escape: F07's first van, its relay, the exit trigger and the two 'last van' objects (the monitor is kept by
# kl_fa.host_keep). F07's SECOND AND THIRD VAN ARE NOT KEPT (kl_fa_bank: a van without a use cannot be parked under
# the map - its ZFakeTarget outside the rooms' bounds is the 0x686a66 crash).
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'       # everything of the van with a place is below it (kl_fa_author.place_vans)
VAN_WAIT = (-3000.0, 32.0, -3100.0)     # THIS HALF ONLY: where the van STANDS - on the study's pavement line (z -3100, free of
                                        # every collision from x -3700 to 5700), 18 m west of the slab, y = the slab + 2. Its
                                        # drive is still F07's baked one (an L of 121 m from there, through whatever stands in
                                        # the way) if the exit box calls it: the next stage's kl_map_escape.van_prepare replaces
                                        # park_van(). GUESS: the place. Not under the map: see VAN
ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith('Gameplay!0'))


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_club.KEEP at the moment of use
        return _KEEP + tuple(x for x in KEEP_MORE if x not in _KEEP)
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
def park_van(S, log=print):
    """F07's first van stands at VAN_WAIT: its group gets the move that puts the first position of its baked drive
    there (no turn). THIS HALF ONLY - the drive itself is still F07's; see VAN_WAIT."""
    sc = S.prp
    top = A.node_of(sc, VAN)
    main, _all, _stop = A.van_path(S, top)
    grp = next(k for k in range(top, sc.end[top]) if sc.names[k] == VAN_GROUP)
    t = tuple(VAN_WAIT[a] - main[0][a] for a in range(3))
    A.place(S, grp, t)
    log('  kl_fa_club: %s stands at (%d, %d, %d) (its group moved by (%d, %d, %d)); its drive is still F07\'s' % (VAN, *VAN_WAIT, *t))
    return R + VAN + '\\' + VAN_GROUP


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the club. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    if not BEAT_ANIM and kl_gms.RETYPE.get(IK[1][0]) != IK[1][1]:      # before anything is armed: a caller that goes on in
        raise ValueError(NO_BUILD)                                     # this process must not find kl_escape wrapped
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
    # escape: the one van where it may wait, the exit trigger names it alone (kl2 0x6c3f90 loops until one field is set)
    van = park_van(S, log)
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M05_A the campaign pre-pass must leave in. THIS HALF: the three kill boxes (KILL). No
    door object is among them - every leaf takes 'Activate' itself, and the campaign's DoorCtrl is a kind no stock
    Dog Days level runs. No squad stays (NO_AI): the next stage returns its squads here."""
    if level != LEVEL:
        return ()
    return tuple(KILL)


def take_off(sc, kind, want, log):
    """The controllers of `kind` off every node of the converted level -> how many; `want` must be there."""
    hit = [k for k, _i, _v in kl_fa.controllers(sc, kind)]
    if len(hit) != want:
        raise ValueError('kl_fa_club: %d %s in %s, %d expected' % (len(hit), kind, LEVEL, want))
    for k in set(hit):
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != kind]
    return len(hit)


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
    log('  kl_fa_club: %s: %d of %d door and seal nodes of the route found; no squad stays (NO_AI)' % (M.name, have, len(LEAVES) + len(SEAL)))
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

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it. This layer's:
    # the seal's clock, and the doors' timer (DOORS_ANIMATE) or the music's muffle switch (the doors are open)
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['seal timer']] + [R + ROLE['doors timer'] if DOORS_ANIMATE else R + ROLE['muffle']]
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
    lists('seal timer', 'TriggerDelay2', f0=SEAL_AT, f4=[R + ROLE['seal off']] if seal else [])
    lists('seal off', 'DeactivateGeom', f0='AITrigger', f1=seal)

    # ---- the way out: F07's 'exit heist' box in the wardrobe, with a line that fits a front door
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_fa_club: sequence: round start -> %.0f s -> %s' % (SEAL_AT, 'the seal off (%s)' % ', '.join(p.split('\\')[-1] for p in seal) if seal
                                                              else 'nothing: the seal is out at build time (SEAL_OPEN)'))
    log('  kl_fa_club: wired: round start %s; %d briefing / reminder lines; exit line %s' % (
        '-> %.1f s -> %d door leaves and the music\'s muffle switch' % (DOORS_AT, len(leaves)) if DOORS_ANIMATE
        else 'starts no door (the leaves are open at build time) and sends the music\'s muffle switch \'%s\'' % MUFFLE_MESSAGE, len(LINES), EXIT_LINE))
    return {'leaves': leaves, 'seal': seal, 'monitor': have + start}


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
    for ref, far in lv.moved():                         # a placement that stands off its entity
        if ('\\' + VAN_GROUP) in path_of.get(ref, ''):
            log('  note: REF %d (%s): its key-framed placement stands %d from its entity - the parked van\'s bodies are still where F07 has them '
                '(the next stage\'s kl_map_escape.van_hvk moves them)' % (ref, path_of[ref].split('\\')[-1], far))
        else:
            fail('REF %d (%s): its collision placement stands %d from its entity' % (ref, path_of.get(ref, '?')[-60:], far))
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
    starters = {R + ROLE['seal timer'], R + ROLE['doors timer'] if animate else R + ROLE['muffle']}
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
        log('  van: THIS HALF - it stands at its waiting place with F07\'s own drive; the next stage lays the drive (kl_map_escape)')
    # ... its ZFakeTarget inside the vision space, by kl_fa_bots_dyn's rule (the 0x686a66 crash; re/crash_686a66.md)
    try:
        import kl_fa_bots as FB, kl_fa_bots_dyn as D
        B = FB.Built(folder)
        space = D.vision_space(B)
        log('  ' + D.space_words(space)[:330])
        for f in D.fake_targets(B, space):
            good = space is not None and f['out'] is None and f['cell'][1] and f['cell_sure'][1]
            log('  FakeTarget %s at (%d, %d, %d): %s' % (f['path'].split('\\')[0], *f['at'], 'inside the vision space, kl2\'s arithmetic gives a record'
                                                      if good else 'OUTSIDE the vision space (%s)' % (f['out'],)))
            if not good:
                fail('FakeTarget %s at (%d, %d, %d) cannot register (outside by %s)' % (f['path'].split('\\')[0], *f['at'], f['out']))
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
    people = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor')
    log('  people: %d ZFFActor in %d squads + 16 player bodies' % (people, len(squads)))
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
    log('ESCAPE (the van stands at its waiting place)')
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


def build(out, log=print):
    """F07 + M05_A with the layer into <out>/F07+M05_A campaign -> (kl_maps.one's result, that folder). The build's
    own arguments: M_DROP, and - unless BEAT_ANIM - the two beat objects loaded as plain objects (kl_maps' 'flat',
    with the class pair IK lent to kl_maps.FLAT for the call, as kl_fa_bank lends kl_fa_author its squad roots)."""
    flat = () if BEAT_ANIM else (IK[0],)
    lent = [c for c in flat if c not in kl_maps.FLAT]
    for c in lent:
        kl_maps.FLAT[c] = IK[1]
    try:
        with doors(log):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_club', m_drop=M_DROP, flat=flat)
    finally:
        for c in lent:
            del kl_maps.FLAT[c]
    return r, os.path.join(out, '%s+%s campaign' % (HOST, LEVEL))


def test(out, keep=False, log=print):
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1."""
    r, folder = build(out, log)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
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
        DOORS_ANIMATE = '--doors-animate' in a
        SEAL_OPEN = '--seal-open' in a
        SEAL_PLANE = '--seal-plane' in a
        LIGHT_SHOW = '--light-show' in a
        BEAT_ANIM = '--beat-anim' in a
        FAN_DAMAGE = '--fan-damage' in a
        CASE = None if '--loot-bags' in a else CASE
        if '--seal' in a:                               # OPTION, seconds from the round-start event to the seal's end
            SEAL_AT = float(a[a.index('--seal') + 1])
        sys.exit(test(a[1], '--keep' in a))
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
