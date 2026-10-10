#!/usr/bin/env python3
"""
The Fragile Alliance layer of Retomoto Tower (Dead Men M09_A + M09_B under Dog Days F07):
authored from stock objects, offline. Spec, evidence and the list of what only a live run can
settle: re/retomoto_fa.md. Nothing here installs anything or starts the game.

    python kl_fa_author.py test <out> [--keep] [--no-ai] [options]
                                                 build F07 + M09_B + M09_A with the layer into
                                                 <out> (kl_maps.chain), verify, kl_fa.check, the
                                                 ledge test, print the inventory with world
                                                 coordinates; exit 1 if a problem is left that is
                                                 not in KNOWN. --no-ai: a test build without the
                                                 campaign's squads. Options (one variable each for
                                                 the live runs, re/retomoto_fa.md 11.8):
                                                 --blast-delay S  seconds from the round-start event
                                                                  to the bomb's warm-up (default 9)
                                                 --fuse S         the bomb's own fuse (default 4)
                                                 --blast-real     the bomb keeps its radii
                                                 --guards-awake   the room squads as the campaign
                                                                  has them (active from the start)
                                                 --one-wave       every tower squad at the blast
                                                 --room-classic   the boardroom's guards as the campaign has them
                                                                  (default: they run from the window at the blast,
                                                                  the pistol squad rushes back 6 s later)
                                                 --police-follow  tower police points off once a
                                                                  criminal is at the front entrance
                                                 --loot-bags      the loot keeps its money bags and its
                                                                  places (without it kl_fa_loot dresses the
                                                                  written level: briefcases on the boardroom
                                                                  table, in reach; the armour as the cases'
                                                                  loot - re/retomoto_loot.md)
    python kl_fa_author.py ledge <archive>       the ledge test alone on a built level: what
                                                 stands outside the main window, the glass before
                                                 and after the blast, the rail
    python kl_fa_author.py plan                  the campaign squads that stay, per part, and why
    python kl_fa_author.py vans                  the three baked van paths fitted to the road
    python kl_fa_author.py inventory <archive>   the inventory of a built level
    python kl_fa_author.py hero <kept build folder> <out folder> x y z [dx dz]
                                                 test aid: a copy of a kept build whose Heroes!Hero_01
                                                 (where a direct boot starts) stands at x y z

HOW (no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  Host F07 has its whole Fragile Alliance layer as top-level subtrees: 234 FASpecials!, 32
  Specials!, the escape set-up and three animated vans. kl_graft keeps them when their names are
  in Select(s_keep) (KEEP), exactly as it keeps kl_fa.host_keep's seven. Then
  1. prepare_host(S) - on the stock Level before the graft: positions (.prp ZGEOM[1] / [2] and
     the .gms record, as kl_graft does for Heroes!), box half extents, values. Tables below.
  2. the campaign levels keep, besides what kl_maps.campaign_drop keeps, the squads squad_plan()
     calls self-contained and single-node helpers of the campaign itself (CAMPAIGN_KEEP): the
     window bomb and its invisible second bomb, the chair / door swaps, the campaign's own trigger
     boxes of the tower (STEPS: the staged fight), the two elevator door proxies and their sounds.
  The start (owner, 2026-10-09 17:00): the heisters stand OUTSIDE, on the balcony M09_A has in front
  of the main window (LEDGE), and go in when the bomb has blown it (re/retomoto_fa.md 11).
  3. wire(Jn) - on the final joined scene, where both parts exist: every reference list that
     names a map node. It only edits values of existing controllers (kl_fa.repair's rule).
  kl_graft.build(author=True) calls 1 and 3 itself, strip() on each Dead Men part and keeps KEEP;
  kl_maps.one(author=True) leaves campaign_names() out of the campaign pre-pass (2).

GUESS = a value that is not copied from a stock object or measured in the levels. Every table
entry carries its source; what is marked GUESS has to be looked at in the game.
Facts the tables rest on (all read from the files, scripts in re/retomoto_fa.md):
  rotation  ZGEOM[1] = [third column, second column, first column] of the local matrix; a player
            group (Heroes!*) that faces (dx, dz) holds [-dx 0 -dz, 0 1 0, -dz 0 dx] (look9: local
            -Z; SEEN LIVE, runs RT2b / RT4). A ZSpawnPoint looks along local +Z (rot9; SEEN LIVE the
            other way round in run RT5). A JumpPoint's list entry holds -Z as its direction (read
            from memory in run RT4): look9. Cameras: not looked at.
  boxes     ZBoxPrimitive[0..2] are HALF extents (F07 AlleyTop: bound centre + half and warn
            centre + half end on the same plane, 26154.06 / 26153.9).
  hidden    ZGEOM[3] = 1 together with .gms flag 0x400 (F02's eight late money bags, M09_A's
            blown window, broken door and thrown chairs).
"""
import collections, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms, kl_scene
import kl_prpjoin as J
from kl_prp import units

HOST, PART_B, PART_A = 'F07', 'M09_B', 'M09_A'
R = 'ROOT\\'
A_MAP = 'Locations/M09_A/M09A_Locations.zip\\Locations/M09_A/M09A_LOC_Inside.zip\\'
B_MAP = 'Locations/M09_B/M09B_Locations.zip\\Locations/M09_B/M09B_LOC_Inside.zip\\'
HIDDEN = 0x400
# problems kl_graft.verify reports that this layer cannot remove (re/maps.md 4.2, patches 2 and 3)
KNOWN = ('stream clips are not in the merged stream file', 'particle template names do not resolve')

# ------------------------------------------------------------------ the tower (M09_A), measured
FLOOR3 = 20996.0                        # boardroom floor: campaign actors stand at y 20991..20997
IN = (-1.0, 0.0)                        # into the room from the main window (x 5850, faces +x)
# THE LEDGE (owner, 2026-10-09 17:00: the heisters start OUTSIDE, on the ledge before the glass).
# It exists - M09_A has a balcony outside the main window, where the campaign's Kane lands from the
# rope and plants the bomb. All read from the level's .HVK / .gms (re/retomoto_fa.md 11.1):
#   slab     SO0200_M09_FrontTopWindows_01, its top face y 21011, x 5826..6164, z -1087..898,
#            collision flags 0x72 (as every floor); a canopy of the same object at y 21695
#   glass    ..._Window_Glass_Geom_Pre_00: two walls x 5840 / 5860, y 21020..21660, z -990..790, 0x72
#   pillars  S00200_M09_Balkon_HalfPillar_A_01..04, x 5850..5895, z -1046..-953 / -558..-466 /
#            265..358 / 753..845
#   rail     ColiObj_Plane01, invisible, flags 0x108 (the flags of Dog Days' own hero blockers),
#            y 21004..21204: x 6151 for z -1070..872, the two ends z -1070 and z 872, and two inner
#            returns at x 5888 for z -1070..-547 and z 346..872 - the way in is z -547..346
#   nav      two areas of the level's own navigation mesh: x 5894..6102, z -975..780 (the balcony)
#            and x 5871..5896, z -432..232 (the way through the window)
LEDGE_Y = 21011.0
LEDGE = ((5894.0, 6102.0), (-975.0, 780.0))             # the nav area on the balcony: where a point may stand
LEDGE_RAIL = ((5891.0, 6151.0), (-1070.0, 872.0))       # inside ColiObj_Plane01
BOMB = (5867.0, 21094.0, -66.0)                         # WindowBlowup!BombWindow03
INVISIBOMB = (5685.0, 20997.0, -394.0)                  # WindowBlowup!InvisiBomb, radii 300 / 100
# 8 heisters in two stacks of four on the balcony, left and right of the bay that blows (the charge
# sits on the centre glass, z -66). GUESS: the stacks. Placement keeps them out of the bomb's own
# first radius (600) whether BLAST_HARMLESS holds or not: nearest points 624 and 611 from the bomb,
# 432 from the InvisiBomb (ledge_facts() tests both)
START = [(6000.0, LEDGE_Y, z) for z in (-930, -850, -770, -690, 530, 610, 690, 770)]
TRAITOR = [(6070.0, LEDGE_Y, z) for z in (-890, -730, 570, 730)]                     # GUESS: behind the stacks
# police who come back: the elevator lobby (campaign 'SquadArrivingElevator', which is not
# kept), the atrium lift, and the square in front of the lobby (campaign 'Squad_InFront')
POLICE = [(1904.0, 19601.0, 818.0), (1800.0, 19601.0, 812.0), (1987.0, 19601.0, 973.0),
          (-1764.0, 19613.0, -61.0), (-1508.0, 19613.0, -147.0), (447.0, -50.0, -7956.0), (-367.0, -50.0, -7594.0)]
# (the square's ground is y -50: the player's feet at (439, -50, -7861) in run RT4; the campaign actors' own y there is 26)
STAGE_B = [(3110.0, 21005.0, -1138.0), (2961.0, 21005.0, -990.0), (3033.0, 21004.0, -8.0), (2917.0, 21004.0, -190.0)]   # reception (campaign actors)
STAGE_C = [(2340.0, 19606.0, 1238.0), (2534.0, 19605.0, 883.0), (2604.0, 19605.0, -1063.0), (2485.0, 19605.0, -1555.0)]  # elevator lobby (campaign actors)
STAGE_D = [(3076.0, 162.0, -6354.0), (3100.0, 162.0, -6594.0), (3300.0, 162.0, -6354.0), (3300.0, 162.0, -6594.0)]       # lobby: CP_01 + GUESS
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing)
SPAWN = {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), (1.0, 0.0)),
         # the other modes' criminals stand on the balcony too, inside LEDGE (x 5894..6102)
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (70, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (70, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (-120, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (0, 0, 80), (1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (START, (-60, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), (1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (120, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (0, 0, -80), (1.0, 0.0))}
# the 15 samurai-armour cases (re/retomoto.md 3.2: the '_Whole' glass of each); the loot stands
# at the case's own origin, i.e. inside the glass. That a stack there can be reached is no longer a
# guess: the pick-up test was read (kl2 0x783e60: horizontal distance <= radius + 40, no wall or glass in
# it) and every case has a place to stand 91..98 away with reach 190 (kl_fa_loot.py survey).
# kl_fa_loot.dress() gives these 15 the armour itself as their model (STATUE = 'suit').
STATUES = [(-2163, 20400, 523), (-73, 20400, 1362), (-109, 20400, -1578), (724, 20400, -808), (-2173, 20400, -705),
           (726, 20400, 606), (726, 21100, 607), (724, 21100, -807), (-110, 21100, -1578), (-2162, 21100, 522),
           (-73, 21100, 1362), (-2172, 21100, -705), (725, 19700, 606), (723, 19700, -808), (-2293, 19700, -131)]
# main room = the boardroom M09_A_Ins_Office_301. Six stacks on the table (chairs stand round
# x 4600..5450, z -290..180). GUESS: the table top is 80 above the floor
# MEASURED since (kl_fa_loot.table()): the top is y 21070 (the table stands on y 20990, not on FLOOR3), z -257..29
# in the middle. The row at z -120 lies 134 in from the rim and CANNOT BE TAKEN (reach 120, nearest place to stand
# 190 away; the owner, 2026-10-09 22:00: 'the ones on the left side from spawn'). kl_fa_loot.dress() re-places all
# six along the rims on the written level, with radius 125 and a briefcase each; this table is where they start.
MAIN_ROOM = [(x, FLOOR3 + 80.0, z) for x in (4750.0, 5000.0, 5250.0) for z in (-120.0, 20.0)]
STATUE_VALUE, ROOM_VALUE = 150000, 300000   # GUESS: 15 x 150,000 + 6 x 300,000 = 4.05 M (F07's loot: 5 x 800,000)
GATE_MAIN_ROOM = True                   # False: the boardroom loot lies there from the start
BLAST_HARMLESS = True                   # the bomb's two radii set to 1 (GUESS that they are its reach; 'test --blast-real' leaves them)
# THE SEQUENCE. The round-start event (AIMonitor list 2) comes when the 8 s countdown BEGINS, not at
# 'GO!' (SEEN LIVE, runs GW1 / GW2). The campaign's bomb has a fuse: Explode field 9 (Dead Men 7) is
# 4.0 on BombWindow03 and 0.0 on both of the campaign's instant bombs and on all 14 Explode of stock
# F01 / F07, and the campaign fires everything else of the blast from a 4 s TriggerDelay started
# with the bomb ('Timer_ExplosionDelay_Kane'). ASSUMPTION that field 9 is that fuse and that the
# first sound (Bomb_WarmUp) plays through it. So: event -> BLAST_DELAY -> the bomb gets 'Activate'
# (warm-up) -> BOMB_FUSE -> the bomb goes off by itself, and a second timer set to BLAST_DELAY +
# BOMB_FUSE swaps the glass, the chairs and the door, fires the InvisiBomb and starts the room's guards.
BLAST_DELAY = 9.0                       # countdown 8 s + GUESS 1 s: the warm-up starts a beat after GO
BOMB_FUSE = 4.0                         # the bomb's own value; another value is written into its field 9
EXPLODE_FUSE = 9                        # Dog Days Explode field (Dead Men 7)
ONE_WAVE = False                        # True: every tower squad starts at the blast (the layer before 2026-10-09 17:00)
POLICE_FOLLOW = False                   # OPTION, see wire(): tower police points switched off from the street

# ------------------------------------------------------------------ the join and the street (M09_B)
CAR_A = (2972.0, 19730.0, 909.0)        # tower escape car SI0101_JPN_Elevator_Int_A_03: box (2756 19600 756)-(3189 19873 1062)
CAR_B = (6272.0, 563.0, -6305.0)        # lobby car ..._Int_A_00, same model and rotation (B - A = 3298, -19040, -7214)
ROAD_X, ROAD_HALF, ROAD_Y = -3000.0, 2400.0, -40.0   # carriageway x -5700..-300 (re/retomoto.md 3.4); y: the player's feet
                                        # on the road, z -1500..9300 (run RT4; the first guess, 5, was the static cars' origin)
# for the hook (data write, re/retomoto_fa.md 3.4): feet inside JOIN_BOX -> jump-list entry JOIN_ENTRY
# The box is IN FRONT of the car, not inside it: the car's doors are shut and stop the player at x 2727
# (run J1, 2026-10-09: 15 s of pushing at (2727, 19601, 807..932), the inside box x 2802..3142 was never
# reached). This box fired from outside in RT4 and from the hook in J1b, both at (2719, 19601, 1100).
# The level's own 'join box' below (the speak trigger) is still the car's inside and is never entered.
JOIN_BOX = ((2550.0, 2790.0), (19500.0, 19800.0), (800.0, 1100.0))
# THE JOIN AS A BEAT, for the hook's author (klhook\KLJoin.retomoto.ini; not used by this file): once
# a live run has SEEN the car's doors open (they are opened by the campaign's own box at the lobby's
# entrance now, wire()), the box that makes the wait real is the car's inside - the player has to
# walk in through doors that take 75 frames to open. Until then JOIN_BOX above stays the one in use.
JOIN_BOX_CAR = ((2802.0, 3142.0), (19560.0, 19860.0), (789.0, 1029.0))
JOIN_ENTRY = 5                          # Specials!JumpPoints!06_Exit: the sixth JumpPoint in scene order (entries 0..5 read in run RT4)
VAN_STOP_Z = (9300.0, 8500.0, 7700.0)   # GUESS: north of the first road block (z 3602..3911), south of the SWAT truck (z 10886)
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put

# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # round start
    'FASpecials!POI!Trigger_POI_TheLootArea': ((6020, 21110, -100), None, (140, 150, 1000), 'GUESS: box round the START stacks on the balcony (F07: round its start)'),
    'FASpecials!POI!POI_TheLootArea': ((4600, 21060, -100), None, None, 'GUESS: boardroom centre'),
    'FASpecials!PIP!EnterLootArea': ((5700, 21100, -100), None, (50, 200, 1250), 'GUESS: a plane 1.5 m inside the glass, the inner edge of the wooden deck (x 5704)'),
    'FASpecials!PIP!ExitLootArea': ((5600, 600, -6500), None, (100, 500, 1650), 'GUESS: across the lobby below the elevator landing'),
    # spawn cameras (camera, look-at)
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((6500, 21300, 500), None, None, 'GUESS: in the air off the balcony'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((5950, 21080, -100), None, None, 'GUESS: the centre bay'),
    # the staged tower fight: the two steps the campaign has no trigger box for (wire())
    'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou': ((4200, 21200, -100), None, (60, 250, 1200), 'GUESS: across the boardroom at M09_A Markup!Jump_03 (x 4202): past the table'),
    'Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou': ((3430, 21200, -100), None, (60, 250, 300), 'the boardroom door (SI0200_M09_Office_DDoor_01_01, x 3430)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((2700, 21300, 0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((3300, 21050, -100), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((2600, 19950, -1200), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((2500, 19650, 0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((4500, 700, -5200), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((3100, 200, -6500), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((1500, 19950, 300), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((1900, 19650, 850), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((1500, 19950, 300), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((1900, 19650, 850), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': ((3430, 21200, -100), None, (60, 250, 300), 'GUESS: the boardroom door (x 3430)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': ((2200, 19800, -100), None, (1000, 250, 1700), 'GUESS: the elevator lobby'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': ((4300, 600, -6500), None, (1700, 600, 1650), 'GUESS: the Retomoto lobby'),
    # the join: a box in the tower's escape car -> the jump point in the lobby car
    'Specials!LevelSpeak!TriggerBox': (CAR_A, None, (170, 130, 120), 'the car\'s own box, 45 smaller on each side'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': (CAR_A, None, None, 'with its trigger box'),
    'Specials!JumpPoints!06_Exit': (CAR_B, (-1.0, 0.0), None, 'the campaign\'s arrival car; faces its door (x 6112)'),
    # jump points (developer aids in stock levels): the campaign's own
    'Specials!JumpPoints!01_Start': ((6000, LEDGE_Y, -100), IN, None, 'the balcony, between the START stacks'),
    'Specials!JumpPoints!02_MarketMain': ((4202, 21006, -129), IN, None, 'M09_A Markup!Jump_03'),
    'Specials!JumpPoints!03_MarketOrange': ((3037, 21006, -1048), IN, None, 'M09_A Markup!Jump_04'),
    'Specials!JumpPoints!04_LootWarehouse': ((102, 19649, -369), (1.0, 0.0), None, 'M09_A Markup!Jump_05'),
    'Specials!JumpPoints!05_MarketGreen': ((2499, 19606, 1156), (1.0, 0.0), None, 'M09_A Markup!Jump_06'),
    # part 2
    'Gameplay!030_AfterLoot!tbExitFinancialAlley': ((2900, 400, -6500), None, (300, 400, 800), 'GUESS: inside the front entrance (x 2600, z -7300..-5700)'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((4300, 600, -6500), None, (1750, 600, 1650), 'the lobby\'s bound (2600 42 -8150)-(6109 1254 -4850)'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((4300, 600, -6500), None, (1750, 600, 1650), 'as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((4300, 600, -6500), None, (1750, 600, 1650), 'as above'),
    # level bounds. Tower: the only way out is the blown window. Street: the campaign's own
    # north / south / lobby-back bounds stay (kl_maps.campaign_drop); the west side is open
    # The balcony's own rail stands at x 6151 and z -1070 / 872. The bound is the answer for whoever
    # gets past it: a slab that begins outside the rail and reaches 110 m down (the tower hangs
    # 190 m over part B's square; nothing of B's play space lies at x > 6170, z -2500..2300). It
    # must NOT cover the balcony: the heisters start there (the layer before had the warning from x 5880)
    'Specials!LevelBound!040_LevelBound_AlleyTop!Bound': ((6790, 17600, -100), None, (560, 5700, 2400), 'GUESS: outside the rail, x 6230..7350, y 11900..23300'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn01': ((6765, 17600, -100), None, (585, 5700, 2400), 'GUESS: from x 6180 (rail 6151 + a body)'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn02': ((6765, 17600, -100), None, (585, 5700, 2400), 'as Warn01'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Bound': ((-7400, 500, 3000), None, (400, 1500, 5000), 'GUESS: west of the road towards the overpass / bus terminal'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn01': ((-7000, 500, 3000), None, (800, 1500, 5000), 'GUESS'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn02': ((-7000, 500, 3000), None, (800, 1500, 5000), 'GUESS'),
}
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft',
                                                         '030_LevelBound_StreetRight') for b in ('Bound', 'Warn01', 'Warn02')]
# host objects that get a new job in wire(): role -> name (each a single top-level node)
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'arm timer': 'Gameplay!010_FirstFight!RivalMercVan!TimerVanGo',              # TriggerDelay2: the bomb's warm-up
        'blast timer': 'Gameplay!010_FirstFight!RivalMercVan!Timer',                 # TriggerDelay2: the moment it goes off
        'bomb': 'Gameplay!010_FirstFight!RivalMercVan!Activator_VanSound',           # AIDWrapper 'Activate'
        'glass': 'Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo',         # AIDWrapper
        'step room': 'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou',                  # TriggerBox, tower step 1
        'step door': 'Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou',                 # TriggerBox, tower step 2
        'street': 'Gameplay!030_AfterLoot!tbExitFinancialAlley',                     # TriggerBox ECPS_FA_MERCONLY
        'counter': 'Gameplay!020_Loot!FollowPlayers!TriggerCounter',
        'loot on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT',    # ActivateGeom
        'police off': 'Gameplay!010_FirstFight!RivalMercVan!GeomDeactivator_DriveInVan',   # DeactivateGeom (POLICE_FOLLOW)
        'join box': 'Specials!LevelSpeak!TriggerBox', 'join': 'Specials!JumpPoints!06_Exit', 'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
VANS = ['Animation/F07/F07_Escape_Vehicle_0%d.zip' % i for i in (1, 2, 3)]
# FOR k-street (tools/kl_fa_street.py, part B: lobby, street, vans, street bounds). The F07 objects
# in ROLE are taken. Free top-level trigger boxes of F07 this file does not touch: Gameplay!020_Loot!
# tbExitLoot, Gameplay!020_Loot!FollowPlayers!tbCountPlayers, Gameplay!040_Escape!tbEscapeAI,
# Gameplay!RunToEscape!tbRunToEscape, ...!tbRunToEscape1Player; timers: every other TriggerDelay2
# under Gameplay!010_FirstFight!. The street module is found by name and asked for a dict HOOKS,
# every key optional (street() below):
#   'keep'           more top-level names / patterns of F07 that stay (Select(s_keep))
#   'campaign_keep'  {level: names} of single campaign nodes that stay, as CAMPAIGN_KEEP
#   'prepare_host'   fn(S, log), called at the end of prepare_host(): it may re-place anything of
#                    part B this file placed (ROLE 'street' / 'exit', the vans, the street bounds)
#   'wire'           fn(sc, log), called at the end of wire() on the joined scene
# Without that module, or without HOOKS in it, part B is what this file built before (section 2 - 4).
_KEEP = ('FASpecials!', 'Specials!', 'Gameplay!EscapeSetup!*') + tuple(VANS) + tuple(v for k, v in ROLE.items() if v.startswith('Gameplay!0'))


# What works on the WRITTEN level (models: chunk numbers exist only then): fn(folder, log) -> [problems], called
# by test() here and by kl_fa_blast.test() once the archive is in `folder`. kl_fa_loot.hook() adds its finish().
# FOR kl_graft / kl_maps (not my files): `for fn in kl_fa_author.FINISH: fn(<folder of the written level>, log)`
# after the last step of a chain is written gives 'kl_maps.py chain ... --author' the same level.
FINISH = []


def street():
    """HOOKS of k-street's module, {} without it. Imported late: that module may import this one."""
    try:
        import kl_fa_street
    except ImportError:
        return {}
    return getattr(kl_fa_street, 'HOOKS', None) or {}


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_author.KEEP
        return _KEEP + tuple(x for x in street().get('keep', ()) if x not in _KEEP)
    raise AttributeError(name)

# ... but not F07's cover list: a Dead Men map brings its own top-level 'CoverList', and a second
# FFCoverList is an assert in its init (kl2 0x6682c5 from CFFCoverList slot 13, 0x6d6a80: the game
# data's cover list at +0x15a0 is already set; run RT2, after which the load never finished)
DROP = ('Specials!CoverPoints!*',)

# ------------------------------------------------------------------ the campaign's own objects that stay
# what the blast timer fires besides the glass wrapper and the room's guards (all take 'AITrigger').
# The last three are the campaign's own beat at this moment (its 'Timer_ExplosionDelay_Kane' names
# them): the invisible second bomb that kills the guard standing at the glass, and the box that
# lets a pillar come down 5 s after somebody walks in through the window
BLAST = ('AI_Players!Enemies!020_Office!GeomActivator_ChairPost', 'AI_Players!Enemies!020_Office!GeomDeactivator_ChairsPre',
         'AI_Players!Enemies!020_Office!GeomActivator_BrokenDoors', 'AI_Players!Enemies!020_Office!GeomDeactivator_Doors',
         'Music!PlayMusic_TokyoAction',                                             # the level's action theme, two layers
         'WindowBlowup!Activator_KillGuyNearWindow',                                # AIDWrapper 'Activate' -> WindowBlowup!InvisiBomb
         'WindowBlowup!TriggerBox_FallingDebris')                                   # field 0 = 0 until named, -> Timer 5 s -> the pillar
# THE STAGED TOWER FIGHT: the campaign's OWN trigger boxes, where its designers put them, with their
# own lists (what they name of the dropped campaign is cut by kl_fa.repair). wire() makes them
# ECPS_FA_MERCONLY - the idiom of stock F01's tbPlatform#01_MercOnly (re/fa_gamemode.md 2).
STEPS = ('AI_Players!Enemies!040_Atrium_3rd!TriggerBox_EnterAtrium',                # (1535 21176 -94) half (100 250 1200): reception -> atrium, 3rd floor
         'AI_Players!Enemies!040_Atrium_3rd!Timer_CoverDefense',                    # TriggerDelay 3, named by the box above
         'AI_Players!Enemies!040_Atrium_3rd!TriggerBox_EnterAtriumFurther',         # (673 21236 -94) half (100 250 1600)
         'AI_Players!Enemies!040_Atrium_3rd!Trigger_RecepLeftGoRight',              # (265 21243 1174) half (450 250 50): gallery, north side
         'AI_Players!Enemies!040_Atrium_3rd!Trigger_RecepRightGoLeft',              # (304 21242 -1351) half (450 250 50): gallery, south side
         'AI_Players!Enemies!050_Atrium_2nd!Trigger_2ndFloorStairs',                # (-928 21218 -94) half (50 300 2000): towards the top stairs
         'AI_Players!Enemies!050_Atrium_2nd!Trigger_2ndLeftGoRight',                # (-1005 20454 1408) half (450 250 50): 2nd floor
         'AI_Players!Enemies!050_Atrium_2nd!Trigger_2ndRightGoLeft',                # (-981 20435 -1683) half (450 250 50)
         'AI_Players!Enemies!050_Atrium_2nd!Trigger_2ndFloorStairEnd',              # (-1899 20581 -121) half (200 300 2000): foot of stairs C / D
         'AI_Players!Enemies!050_Atrium_2nd!Trigger_1stFloorStairEnd',              # (-1730 19884 -121) half (200 300 2000): foot of stairs A / B
         'AI_Players!Enemies!070_Elevators!TriggerBox_PreLastTrigger',              # (164 19742 -169) half (200 150 2000): across the atrium floor
         'AI_Players!Enemies!070_Elevators!TriggerBox_OpenExitElevator')            # (2049 19741 -110) half (100 150 1400): into the elevator lobby
STEP_LOBBY = STEPS[-1]                  # THE JOIN AS A BEAT hangs on this one (wire())
CAMPAIGN_KEEP = {
    PART_A: ('WindowBlowup!BombWindow03',                                           # Explode: particles + the two sounds
             'WindowBlowup!InvisiBomb', 'WindowBlowup!Timer', 'WindowBlowup!Activator_FallingDebris',
             'AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator',       # MatPosAnimProxy 0..75 on Ext_A_03 / Int_A_03
             'Audiotriggers!GeomActivator_ElevatorDing', 'Audiotriggers!GeomActivator_ElevatorOpen',
             'AI_Players!Enemies!020_Office!SmokeTimer') + BLAST + STEPS,       # ROOM_TIMER: the pistol rush
    PART_B: ('Mercenaries!VideoProxy!MatPosAnimProxy',)}                            # the lobby car's doors, 0..75
AT_BLAST = [R + n for n in BLAST]
# a tower squad no campaign trigger box starts (the campaign started it from a cutscene or left
# it standing) gets the step whose area it belongs to; anything else is started at the blast
STEP_AREA = (('step room', ('AI_Players!Enemies!030_Reception!',)),
             ('step door', ('AI_Players!Enemies!040_Atrium_3rd!', 'AI_Players!Enemies!050_Atrium_2nd!')),
             ('lobby', ('AI_Players!Enemies!060_Atrium_1st!', 'AI_Players!Enemies!070_Elevators!')))
# campaign boxes inside a kept squad whose only targets are that squad's stripped mini-cutscene
# groups: their lists are emptied (the box on the balcony would send 'AITrigger' to a bare group)
QUIET = ('AI_Players!Enemies!020_Office!Squad_Guards_Inside_01\\TriggerBox_TurnaroundGuard',
         'AI_Players!Enemies!020_Office!Squad_Guards_Inside_01\\Timer_ExplosionDelay_Kane')
WINDOW_PRE = R + A_MAP + 'M09_A_Ins_Office_301\\SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00'
SQUADS = {PART_A: ('AI_Players!Enemies!020_Office!', 'AI_Players!Enemies!030_Reception!', 'AI_Players!Enemies!040_Atrium_3rd!',
                   'AI_Players!Enemies!050_Atrium_2nd!', 'AI_Players!Enemies!060_Atrium_1st!', 'AI_Players!Enemies!070_Elevators!'),
          PART_B: ('Enemies!010_RetoBldFront!', 'Enemies!020_Street!')}
ROOM_SQUADS = 'AI_Players!Enemies!020_Office!'      # 'everyone in the main room'
# OPTION for the start problem (the heisters stand in sight of the seven boardroom guards, who hit them
# during the countdown: run S2, red screen at 'HEIST STARTS IN 1 SEC'). ZSquadScript field 3 is 1 on
# exactly three squads of the level - the two boardroom squads and one street squad - and 0 on the
# other 28, which do nothing until a behaviour rout of theirs is named (the tower's: by the blast
# timer). The campaign needs the 1 for the guards' sitting mini-cutscene, which the layer strips.
# True = the two room squads get 0 and so wait for the blast like the rest of the tower: their
# flanking routs are in the blast timer's list already. ASSUMPTION that field 3 is 'active from the
# start' (no name in the exe; 14 of 30 squads of stock F01 have 0: the ones that arrive later).
# SEEN LIVE with it (run GW2): the guards sit through the countdown and react when their rout is named.
# Default True since the owner's 2026-10-09 17:00 design (guards unaware until the blast);
# 'test ... --guards-awake' builds the level as the campaign has the field.
ROOM_WAITS = True
SQUAD_ACTIVE = 3
# scripted arrivals (elevators, cars). 'Squad_Guards_Inside_01' is no longer here: with the heisters
# outside, the guard at the glass ((5770, 21012, -347)) is the campaign's own first casualty again
# (the InvisiBomb, 98 from him); his partner stands at the table
NOT_SQUADS = ('Arriving', 'TakingElevator', 'VSquad')
BEHAVE = {'DefendBehaviourRout', 'FlankingBehaviourRout', 'HuntBehaviourRout', 'PatrolBehaviourRout', 'RunToCoverBehaviourRout'}
PLAIN = BEHAVE | {'ZSquadScript', 'ZSoldier', 'RunToCoverPosInfoRout', 'SquadModifierBehaviour', 'TriggerDelay', 'TriggerCounter', 'TriggerBox'}
# in-game scripted animation of the campaign: removed from a squad that stays (before the join)
STRIP = {'MiniCutsceneRout', 'MiniCutSlot', 'MiniCutPosObject', 'MiniCutSignal', 'MiniCutItemProxy'}
# THE ROOM'S GUARDS RUN, THE PISTOLS RUSH (owner, 2026-10-09 late: 'when you spawn in you see them run away
# and they hide for cover, then guys with pistols will rush you'; re/retomoto_ai.md 3). Values and places of
# the campaign's own objects. The three room squads each have one FlankingBehaviourRout with two points and a
# SquadModifierBehaviour; the blast timer names the flank rout. The points are moved (WORLD positions, on the
# level's navigation mesh: boardroom floor 20995 / 20996, reception 20995; no mesh at x 3300..3600 beside the
# doorway) so that at the blast the guards run AWAY from the window, to the door end and out into the
# reception. RUSH_DELAY later the campaign's own 'SmokeTimer' fires the pistol squad's modifier, set to
# eLM_Unleash: they come back through the door. GUESSES: every point, the delay, and that an unleashed squad hunts.
RT_LINES = {17: 'Multiplayer/F05/MissionBriefing_03_R', 18: 'Multiplayer/F01/MissionBriefing_03_R',
            19: 'Multiplayer/F05/MissionBriefing_02_R', 20: 'Multiplayer/F05/MissionBriefing_01_R',
            127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
            136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}   # settings field -> line
ROOM_RUNS = True                        # False ('--room-classic'): the guards flank towards the table, as the campaign has it
RO = 'AI_Players!Enemies!020_Office!'
ROOM_PLACE = {
    RO + 'Squad_Guards_Inside_01\\04_FlankingBehaviour\\LeftFlank#1': (3700, 20996, 700),    # was (5146, 522): the table
    RO + 'Squad_Guards_Inside_01\\04_FlankingBehaviour\\RightFlank#1': (3700, 20996, -900),  # the door end's corners
    RO + 'Squad_Guards_Inside_02\\03_FlankingBehaviour\\LeftFlank#1': (3300, 20995, 500),    # reception, behind the door jambs
    RO + 'Squad_Guards_Inside_02\\03_FlankingBehaviour\\RightFlank#1': (3300, 20995, -700),  # (the door opens z -400..200)
    RO + 'Squad_Guards_Inside_03\\02_FlankingBehaviour\\LeftFlank#1': (3100, 20995, 900),    # reception's far corners
    RO + 'Squad_Guards_Inside_03\\02_FlankingBehaviour\\RightFlank#1': (3100, 20995, -1100)}
ROOM_RUSH = RO + 'Squad_Guards_Inside_03\\01_SquadModifier'    # 3 men; kl_arms.FORCE gives them pistols
ROOM_HOLD = RO + 'Squad_Guards_Inside_02\\02_SquadModifier'    # 4 men with SMGs hold the doorway (eDM_Tight, GUESS)
ROOM_HIDE = RO + 'Squad_Guards_Inside_01'                        # the survivor at the table: eStayBack (the campaign: eUnleashed)
ROOM_TIMER = RO + 'SmokeTimer'          # campaign TriggerDelay (single top-level node); its own list is cut by the prune
RUSH_DELAY = 6                          # s after the blast (GUESS)
SQUAD_DEAD = 8                          # ZSquadScript field 8: the list sent when the squad is wiped out


# ------------------------------------------------------------------ small tools
def rot9(turn):
    """ZGEOM[1] of the turn about Y that takes local +Z to (dx, dz): [third, second, first column]."""
    dx, dz = turn
    n = math.hypot(dx, dz)
    dx, dz = dx / n, dz / n
    return [dx, 0.0, dz, 0.0, 1.0, 0.0, dz, 0.0, -dx]


def look9(face):
    """ZGEOM[1] of a node that FACES (dx, dz): the turn that takes local -Z there. SEEN LIVE (run
    RT2b): Hero_01 holding rot9((-1, 0)) stood at the main window looking OUT at the skyline,
    heading +x - a player looks along local -Z."""
    return rot9((-face[0], -face[1]))


def node_of(sc, name):
    hit = sc.resolve(name if name.startswith(R) else R + name)
    if len(hit) != 1:
        raise KeyError('%s: %d nodes named %s' % (sc.label, len(hit), name))
    return hit[0]


def setv(sc, us, i, v):
    """Field unit i = v, in the token kind the field already has."""
    op = us[i][0][0]
    if op == 0x0a:
        us[i] = [(op, struct.pack('<f', v))]
    elif op == 0x09:
        us[i] = [(op, struct.pack('<I', v))]
    elif op in (0x05, 0x06, 0x07):
        us[i] = [(op, bytes([v]))]
    elif op in (0x0c, 0x0e):
        us[i] = [(op, struct.pack('<I', sc.p.key_index(v)))]
    elif op == 0x01:
        us[i] = [us[i][0]] + [(0x0a, struct.pack('<f', x)) for x in v] + [us[i][-1]]
    elif op == 0x04:
        us[i] = kl_fa._refs(sc, v)
    else:
        raise ValueError('field %d: token %#x' % (i, op))


def ctrl_of(sc, k, name):
    for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']):
        if sc.p.key(nm) == name:
            return i
    raise KeyError('%s has no %s' % (sc.path[k], name))


def place(S, name, pos=None, face=None, half=None, hidden=None, turn=None):
    """Put a node of the Level S somewhere: .prp ZGEOM[1] / [2] and the .gms record (the Dog Days
    loader reads the .prp's; both are kept equal as in stock). Top-level nodes and nodes whose
    parents are identity at the origin only: the values are world values. face: the way the
    node looks (look9); turn: a plain rotation instead (rot9: the vans' baked drives)."""
    sc = S.prp
    m9 = look9(face) if face is not None else rot9(turn) if turn is not None else None
    k = name if isinstance(name, int) else node_of(sc, name)
    lab, e = J.labels('dd', sc.cls(k)), S.ents[k - 1]
    def fn(us):
        if m9 is not None:
            setv(sc, us, lab.index('ZGEOM[1]'), m9)
        if pos is not None:
            setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
        for i, v in enumerate(half or ()):
            setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
        if hidden is not None:
            setv(sc, us, lab.index('ZGEOM[3]'), int(hidden))
    kl_graft.edit(sc.nodes[k], 'props', fn)
    if m9 is not None:
        e.rot = struct.pack('<9f', *m9) + bytes(12)
    if pos is not None:
        e.trans = struct.pack('<3f', *pos) + bytes(4)
    if hidden is not None:
        e.flags = e.flags | HIDDEN if hidden else e.flags & ~HIDDEN
    return k


# ------------------------------------------------------------------ the vans
def van_path(S, top):
    """(points of the main drive: wait -> stop -> away, every baked position, the stop) of one of
    F07's escape vans, in F07's world. The van is a ZGROUP 'V_Van_00' with MatPosAnim; its KEYS
    chunk (kl_graft.keys_tracks) names six .buf tracks, the last a table of positions in the order
    they are driven (564 / 469 / 534 x 3 floats; pieces: the drive in and away, then the crash
    variants). The positions are the node's LOCAL ones; every parent is identity at the origin,
    which is why they read as world positions. The four index tracks are not decoded."""
    sc, buf = S.prp, S['.buf']
    k = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    (_p, offs), = kl_graft.keys_tracks(S.ents[k - 1].raw)
    tab = offs[5]
    end = min([o for o in offs if o > tab] + [len(S.scene.head)])
    pts = []
    while tab + 12 * len(pts) + 12 <= end:
        x = struct.unpack_from('<3f', buf, tab + 12 * len(pts))
        if not all(abs(v) < 1e6 for v in x) or x == (0.0, 0.0, 0.0):
            break
        pts.append(x)
    cut = next((i for i in range(1, len(pts)) if math.dist(pts[i], pts[i - 1]) > 400), len(pts))
    blk = next(j for j in range(top, sc.end[top]) if sc.names[j] == 'PathBlockerVan')      # stands where the van stops
    stop = kl_fa.node_values(sc, blk)[2]
    return pts[:cut], pts, (stop[0], pts[0][1], stop[2])


def van_fit(main, stop):
    """The turn about Y (as a facing) that makes the drive narrowest across the road with the van
    coming from the south, and the x that centres it on ROAD_X -> (facing, x of the stop, width)."""
    best = None
    for deg in range(360):
        dx, dz = math.sin(math.radians(deg)), math.cos(math.radians(deg))
        q = [(dz * (p[0] - stop[0]) + dx * (p[2] - stop[2]), -dx * (p[0] - stop[0]) + dz * (p[2] - stop[2])) for p in main]
        if q[0][1] >= 0:
            continue
        lo, hi = min(x for x, _z in q), max(x for x, _z in q)
        if best is None or hi - lo < best[2]:
            best = ((dx, dz), ROAD_X - (lo + hi) / 2, hi - lo, min(z for _x, z in q), max(z for _x, z in q))
    return best


def place_vans(S, log=print):
    """Each van's 'EscapeVehicle_Animation_F07' group (identity at the origin in stock) gets the
    rigid transform that lays its baked drive along Retomoto's road: everything with a place - the
    van, its boarding box, cameras, path blocker, door trigger - is below that group. The
    'V_Van_Reflection' template beside it stays at the origin, where its nine static Havok
    placements are (re/retomoto_fa.md). -> [(top name, stop, fits)]"""
    sc, out = S.prp, []
    for i, name in enumerate(VANS):
        top = node_of(sc, name)
        main, _all, s = van_path(S, top)
        (dx, dz), x, width, z0, z1 = van_fit(main, s)
        t = (x - (dz * s[0] + dx * s[2]), ROAD_Y - s[1], VAN_STOP_Z[i] - (-dx * s[0] + dz * s[2]))
        grp = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'EscapeVehicle_Animation_F07')
        place(S, grp, t, turn=(dx, dz))
        fits = width <= 2 * ROAD_HALF
        out.append((name, (x, ROAD_Y, VAN_STOP_Z[i]), fits))
        log('  kl_fa_author: %s stops at (%d, %d, %d); drive %d wide (road %d), z %d..%d%s' % (
            name, x, ROAD_Y, VAN_STOP_Z[i], width, 2 * ROAD_HALF, VAN_STOP_Z[i] + z0, VAN_STOP_Z[i] + z1, '' if fits else ' - DOES NOT FIT'))
    return out


# ------------------------------------------------------------------ 1. the host level before the graft
def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for Retomoto. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    for name, (pos, face, half, _why) in PLACE.items():
        place(S, name, pos, face, half)
    for name in PARKED:
        place(S, name, PARK)
    # spawn points by kind, and the sixteen player groups (a direct boot starts at Heroes!Hero_01)
    seen = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kind = kl_fa.node_values(sc, t)[8]
            pts, d, face = SPAWN[kind]
            p = pts[seen[kind] % len(pts)]
            # a spawn point looks along local +Z (rot9), a player group along -Z (look9): SEEN LIVE both
            # ways - with look9 on the START points the round's player stood facing the window (run RT5)
            place(S, t, (p[0] + d[0], p[1] + d[1], p[2] + d[2]), turn=face)
            seen[kind] += 1
        elif sc.names[t].startswith('Heroes!'):
            crook = sc.names[t].startswith('Heroes!Hero_0')
            pts, face = (START, IN) if crook else (POLICE, (1.0, 0.0))
            p = pts[seen[crook, 'hero'] % len(pts)]
            place(S, t, (p[0], p[1], p[2] + (0 if crook else 160 * (seen[crook, 'hero'] // len(pts) + 1))), face)
            seen[crook, 'hero'] += 1
    log('  kl_fa_author: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: 21 stacks of the drop pools become loot that lies in the map. F07 has 108 + 25 pool
    # stacks; six stock levels have 100 + 25. Taken: the last 8 of the 108 and the last 13 of the
    # team-mode 25 (which leaves 100 + 12). The controller values are those of stock F02's money
    # bags (ALL / NORMAL, 15000, 0.2, 1, 30, 800, 1000, 0, 0 and TriggerBox2 radius 80).
    # GUESS: that a pool stack's model (chunk 1802, no Havok shape) serves as loot that lies still.
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    take = sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-8:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[-13:]
    spots = [(p, STATUE_VALUE, False, 150.0) for p in STATUES] + [(p, ROOM_VALUE, GATE_MAIN_ROOM, 80.0) for p in MAIN_ROOM]
    if len(take) != len(spots):
        raise ValueError('%d pool stacks for %d loot places' % (len(take), len(spots)))
    loot = []
    for (name, k, i), (p, value, hide, reach) in zip(take, spots):
        def fn(us):
            for j, v in enumerate(('ZMONEYCTRL_GAMEMODE_ALL', value, 'ZMONEYCTRL_TYPE_NORMAL', 'ZMONEYCTRL_VARIANT_NORMAL', 15000, 0.2, 1, 30.0, 800.0, 1000.0, 0, 0)):
                setv(sc, us, j, v)
        kl_fa.edit(sc, k, i, fn)
        kl_fa.edit(sc, k, ctrl_of(sc, k, 'TriggerBox2'), lambda us: setv(sc, us, 2, reach))   # GUESS 150 at a case (its glass is 150 wide)
        place(S, k, p, hidden=hide)
        loot.append((name, hide))
    log('  kl_fa_author: loot: %d stacks at the samurai cases, %d in the boardroom (%s), %d in all' % (
        len(STATUES), len(MAIN_ROOM), 'hidden until its squads are dead' if GATE_MAIN_ROOM else 'visible', STATUE_VALUE * len(STATUES) + ROOM_VALUE * len(MAIN_ROOM)))
    # escape: the vans along the road, the box that calls them round the first stop, the marker
    vans = place_vans(S, log)
    stop = vans[0][1]
    place(S, ROLE['exit'], (ROAD_X, 500.0, stop[2] - 1500.0), None, (2700.0, 900.0, 3500.0))    # F07: 3542 x 953 x 3567, 16 m from its stops
    place(S, 'FASpecials!POI!POI_TheEscapeArea', (stop[0], 150.0, stop[2]))
    k = node_of(sc, ROLE['exit'])
    fit = [R + n + '\\EscapeVehicle_Animation_F07' if ok else '' for n, _s, ok in vans]
    if not any(fit):
        fit[0] = R + vans[0][0] + '\\EscapeVehicle_Animation_F07'       # kl2 0x6c3f90 loops until one field is set
    kl_fa.edit(sc, k, ctrl_of(sc, k, kl_fa.EXIT), lambda us: [setv(sc, us, 2 + j, s) for j, s in enumerate(fit)])
    S.authored = {'loot': loot, 'vans': vans}
    if street().get('prepare_host'):                    # part B: k-street's module may re-place what stands there
        street()['prepare_host'](S, log)
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's squads
def squad_plan(level):
    """Squads of a campaign level that can stay as they are -> {top-level name: (path of the rout
    that starts it, actors, controllers that are stripped)}; and what was looked at and left:
    {name: reason}. A squad stays when its subtree holds only squad objects (PLAIN), plus campaign
    mini-cutscene objects that are taken off (STRIP), at least one actor and one behaviour rout.
    Its start rout: the lowest-named behaviour rout the campaign's own triggers name."""
    sc = J.Scene.load(level, 'dm')
    named = collections.defaultdict(set)
    for k, _h, _f, _s, hit in J.references(sc):
        for j in hit:
            if k > 0 and sc.top[j] != sc.top[k]:
                named[sc.top[j]].add(j)
    keep, left = {}, {}
    for t in sc.tops():
        name = sc.names[t]
        ctrl = collections.Counter(sc.p.key(nm) for k in range(t, sc.end[t]) for nm, _b in sc.nodes[k]['ctrls'])
        if not ctrl['ZSquadScript'] or not name.startswith(SQUADS.get(level, ())):
            continue
        actors = sum(sc.cls(k) == 'ZFFActor' for k in range(t, sc.end[t]))
        routs = [k for k in range(t + 1, sc.end[t]) if any(sc.p.key(nm) in BEHAVE for nm, _b in sc.nodes[k]['ctrls'])]
        odd = sorted(set(ctrl) - PLAIN - STRIP)
        if any(w in name for w in NOT_SQUADS):
            left[name] = 'scripted arrival or part of the blast'
        elif odd:
            left[name] = 'holds ' + ', '.join(odd)
        elif not actors or not routs or not ctrl['ZSoldier']:
            left[name] = 'no actor or no behaviour rout'
        else:
            first = min([k for k in routs if k in named[t]] or routs, key=lambda k: sc.names[k])
            keep[name] = (sc.path[first], actors, sorted(set(ctrl) & STRIP))
    return keep, left


_plans = {}
NO_AI = False                           # test builds ('test ... --no-ai'): no campaign squad stays. A scripted
                                        # walk on a direct boot is shot dead within 10 s otherwise (run RT2b)

def plan(level):
    if level not in _plans:
        _plans[level] = ({}, {'*': 'test build without AI'}) if NO_AI else squad_plan(level)
    return _plans[level]


def campaign_names(level):
    more = tuple(street().get('campaign_keep', {}).get(level, ()))
    return tuple(CAMPAIGN_KEEP.get(level, ())) + more + tuple(plan(level)[0]) if level in SQUADS else ()


# ------------------------------------------------------------------ 3. the joined scene
def named(sc, k):
    """Every path the controllers of node k hold in a reference list."""
    out = []
    for _nm, body in sc.nodes[k]['ctrls']:
        for u in units(body[1:-1]):
            v = kl_fa.value(sc, u)
            if isinstance(v, list) and v and isinstance(v[0], str):
                out += v
    return out


def wire(sc, log=print):
    """Every reference of the layer that names a node of the map. sc: the joined scene with both
    parts (kl_prpjoin.Scene). Values and reference lists only."""
    node = lambda n: node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            log('  kl_fa_author: NOT IN THE LEVEL: %s' % gone)
        return [p for p in paths if sc.resolve(p)]
    def put(k, name, **fields):
        kl_fa.edit(sc, k, ctrl_of(sc, k, name), lambda us: [setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put(node(ROLE[role]), name, **fields)
    def values(k, name):
        return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][ctrl_of(sc, k, name)][1][1:-1])]
    squads = {lv: plan(lv)[0] for lv in (PART_A, PART_B)}
    start = {lv: must([p for p, _n, _s in squads[lv].values()]) for lv in squads}
    first = {n: p for n, (p, _a, _s) in squads[PART_A].items() if sc.resolve(p)}
    room = [n for n in squads[PART_A] if n.startswith(ROOM_SQUADS) and sc.resolve(R + n)]

    # ---- the staged tower fight. The campaign's own trigger boxes (STEPS) stay where they are and
    # keep their lists; a squad one of them names (directly, or through the one kept timer) is
    # theirs. The room's guards start at the blast; what is left gets its area's step (STEP_AREA):
    # the two F07 boxes in the boardroom and the campaign's own box at the elevator lobby.
    boxes = [node(n) for n in STEPS if sc.resolve(R + n)]
    covered, todo, seen = {}, list(boxes), set()
    while todo:
        k = todo.pop()
        if k in seen:
            continue
        seen.add(k)
        for s in named(sc, k):
            for j in sc.resolve(s):
                top = sc.names[sc.top[j]]
                if top in squads[PART_A]:
                    covered.setdefault(top, sc.names[k])
                elif top in STEPS:
                    todo.append(sc.top[j])
    at_blast, step = [first[n] for n in room if n in first], {r: [] for r, _p in STEP_AREA}
    for n in sorted(first):
        if n in room:
            continue
        role = next((r for r, pre in STEP_AREA if n.startswith(pre)), None)
        if ONE_WAVE or (n not in covered and role is None):
            at_blast.append(first[n])
        elif n not in covered:
            step[role].append(first[n])
    for k in boxes:
        if any(sc.p.key(nm) == 'TriggerBox' for nm, _b in sc.nodes[k]['ctrls']):
            v = values(k, 'TriggerBox')
            if len(v) != 18 or not str(v[14]).startswith('ECPS_'):
                raise ValueError('%s: not the Dog Days TriggerBox layout (%d fields)' % (sc.names[k], len(v)))
            # MERCONLY: a criminal's advance starts the wave, a policeman walking back does not.
            # ONE_WAVE: the squads were started already, the boxes name nothing but the lobby's doors
            put(k, 'TriggerBox', f14='ECPS_FA_MERCONLY', **({'f17': []} if ONE_WAVE and sc.names[k] != STEP_LOBBY else {}))
    lists('step room', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', f17=step['step room'])      # field 0 is 0 in F07 (a box that
    lists('step door', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', f17=step['step door'])      # waits to be switched on): 1 as every plain box
    # THE JOIN AS A BEAT: the campaign's own box across the way into the elevator lobby (x 2049)
    # opens the escape car with its ding and door sound, as in the campaign. Added: the lobby
    # car's doors in part B (so the arrival finds them open) and the lobby's last squad. The
    # doors are no longer opened at the blast: the open car is what the heisters fight towards.
    if sc.resolve(R + STEP_LOBBY):
        k = node(STEP_LOBBY)
        have = [s for s in values(k, 'TriggerBox')[17] if sc.resolve(s)]
        put(k, 'TriggerBox', f17=have + [s for s in must([R + n for n in CAMPAIGN_KEEP[PART_B]]) + step['lobby'] if s not in have])
    else:
        at_blast += step['lobby']
    for path in QUIET:
        for k in sc.resolve(R + path):
            for i in range(len(sc.nodes[k]['ctrls'])):
                kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(j, kl_fa._refs(sc, [])) for j, u in enumerate(us)
                                                 if u[0][0] == 0x04 and not (len(u) > 1 and u[1][0] == 0x0d)])

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins)
    # -> arm timer -> the bomb's warm-up; -> blast timer (the same delay + the bomb's fuse) -> the rest
    k = node(ROLE['monitor'])                           # the host's; M09_B's map has an AIMonitor of its own
    timers = [R + ROLE['arm timer'], R + ROLE['blast timer']]
    have = [s for s in next(v for kk, _i, v in kl_fa.controllers(sc, 'AIMonitor') if kk == k)[2] if sc.resolve(s)]
    lists('monitor', 'AIMonitor', f2=have + [t for t in timers if t not in have])
    lists('arm timer', 'TriggerDelay2', f0=BLAST_DELAY, f4=must([R + ROLE['bomb']]))
    rush = []
    if ROOM_RUNS and not ONE_WAVE:
        if sc.resolve(R + ROOM_RUSH) and sc.resolve(R + ROOM_TIMER):
            put(node(ROOM_RUSH), 'SquadModifierBehaviour', f0='eLM_Unleash', f26=[])      # f26 named the flank rout: they would run back out
            put(node(ROOM_TIMER), 'TriggerDelay', f0=RUSH_DELAY, f4=[R + ROOM_RUSH])
            rush.append(R + ROOM_TIMER)
        if sc.resolve(R + ROOM_HOLD):
            put(node(ROOM_HOLD), 'SquadModifierBehaviour', f9='eDM_Tight', f26=[])
            rush.append(R + ROOM_HOLD)
        if sc.resolve(R + ROOM_HIDE):
            put(node(ROOM_HIDE), 'ZSquadScript', f0='eStayBack')
        log('  kl_fa_author: the room runs: guards to the door end / the reception at the blast; %s' % (
            'the pistol squad is unleashed %d s later' % RUSH_DELAY if R + ROOM_TIMER in rush else 'NO RUSH (timer or squad not in the level)'))
    lists('blast timer', 'TriggerDelay2', f0=BLAST_DELAY + BOMB_FUSE, f4=must([R + ROLE['glass']] + AT_BLAST) + at_blast + rush)
    lists('bomb', 'AIDWrapper', f0=must([R + 'WindowBlowup!BombWindow03']), f1='Activate')                 # the Explode's own message
    lists('glass', 'AIDWrapper', f0=must([WINDOW_PRE]), f1='ForceTriggerShotActivate')                     # the window's ShotActivate, field 10
    if sc.resolve(R + 'WindowBlowup!BombWindow03'):
        b = node('WindowBlowup!BombWindow03')
        v = values(b, 'Explode')
        if len(v) != 18 or not isinstance(v[EXPLODE_FUSE], float) or abs(v[EXPLODE_FUSE] - 4.0) > 1e-3:
            raise ValueError('BombWindow03: Explode field %d is not the 4.0 the sequence is timed by: %s' % (EXPLODE_FUSE, v))
        if BOMB_FUSE != v[EXPLODE_FUSE]:
            put(b, 'Explode', **{'f%d' % EXPLODE_FUSE: BOMB_FUSE})
        if BLAST_HARMLESS:
            # GUESS: Explode fields 0 / 1 (600, 400) are its reach (stock: a rocket 500 / 150, a gas
            # tank 600 / 400; the campaign's unused 'kill the player at the bomb' has 80 / 80).
            # The START stacks stand outside the 600 as well (ledge_facts)
            put(b, 'Explode', f0=1.0, f1=1.0)
    # the street: its police start when a criminal reaches the front entrance
    street_list = list(start[PART_B])
    # OPTION (POLICE_FOLLOW; nothing stock does this, default off): once a criminal is at the front
    # entrance the five police points of the tower are switched off by a DeactivateGeom, so that a
    # dead criminal comes back at the square. GUESS that the spawn choice skips a switched-off point.
    if POLICE_FOLLOW:
        up = [R + sc.names[t] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and kl_fa.node_values(sc, t)[2][1] > 10000
              and kl_fa.node_values(sc, t)[8] == 'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH']
        lists('police off', 'DeactivateGeom', f0='AITrigger', f1=up)
        street_list.append(R + ROLE['police off'])
        log('  kl_fa_author: OPTION police-follow: %d tower police points go off at the front entrance' % len(up))
    lists('street', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=street_list)
    # the join. NOT by a message to the JumpPoint: that path (kl2 0x491e20 -> 0x57e110 with flag 1)
    # also walks the player's crew, and a Fragile Alliance player has none - read of 0xa4 at kl2
    # 0x8f40c9 the moment the scripted player stepped into the tower car (run RT3). The box keeps
    # F07's 'exit heist' line only; the jump point stays in the lobby car as entry 5 of the game
    # data's jump list, for the game's own DEBUG request (gamedata + 0x8d4 = 5, [0x156b358] = 1:
    # flag 0, no crew). Written from outside in run RT4 it put the player into the lobby car in one
    # frame. The hook has to make that write (re/retomoto_fa.md 3.4): JOIN_BOX / JOIN_ENTRY.
    lists('join box', 'TriggerBox', f14='ECPS_BOTH', f17=[R + 'Specials!LevelSpeak!OnlineSpeakTrigger_01'])
    # the main room: its squads' 'wiped out' lists -> counter -> ActivateGeom -> the hidden loot
    for n in room:
        k = node(n)
        put(k, 'ZSquadScript', **{'f%d' % SQUAD_DEAD: [R + ROLE['counter']]})
        if ROOM_WAITS:
            put(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 0})
    hidden = [R + sc.names[t] for t in sc.tops() if sc.names[t].startswith('FASpecials!DropMoney!') and kl_fa.node_values(sc, t)[3]
              and any(v[2] == 'ZMONEYCTRL_TYPE_NORMAL' for kk, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if kk == t)]
    lists('counter', 'TriggerCounter', f0=max(len(room), 1), f4=[R + ROLE['loot on']])
    lists('loot on', 'ActivateGeom', f0='AITrigger', f1=hidden)
    by_box = collections.Counter(covered.values())
    log('  kl_fa_author: sequence: round-start event -> %.1f s -> bomb warm-up -> %.1f s -> blast (glass, chairs, door, InvisiBomb, %d room squads%s)' % (
        BLAST_DELAY, BOMB_FUSE, len(room), ', waiting until then' if ROOM_WAITS else ', ACTIVE FROM THE START'))
    log('  kl_fa_author: tower steps: at the blast %d squads; F07 boxes: room %d, door %d; campaign boxes %d of %d in the level: %s; lobby box + %d' % (
        len(at_blast), len(step['step room']), len(step['step door']), len(boxes), len(STEPS),
        ', '.join('%s %d' % (n.split('!')[-1], c) for n, c in sorted(by_box.items())) or '-', len(step['lobby'])))
    log('  kl_fa_author: wired: %d tower + %d street squads, %d room squads -> counter -> %d hidden stacks' % (
        len(first), len(start[PART_B]), len(room), len(hidden)))
    # the briefing and reminder lines: stock F07's speak of a data theft ('grab the files'). Lines of other stock
    # levels that fit a bomb, cash and a street, all eight voices in the bank (re/bots_voice.md 6.2; b-voice's choice)
    try:
        import kl_voice
        for k, i, _v in kl_voice.settings(sc):
            kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in RT_LINES.items()])
    except (ImportError, AttributeError) as e:
        log('  kl_fa_author: briefing lines left as F07 has them (%s)' % e)
    out = {'squads': squads, 'room': room, 'hidden': hidden, 'at_blast': at_blast, 'step': step, 'covered': covered}
    if street().get('wire'):                            # part B: k-street's module, after everything of this one
        street()['wire'](sc, log)
    return out


# ------------------------------------------------------------------ what kl_graft.build(author=True) calls
def strip(M, log=print):
    """Take the campaign's mini-cutscene controllers (STRIP) off the squads of a converted Dead Men
    level (kl_graft.DeadMen) that stay. Before the join: nothing goes by controller index yet."""
    n = 0
    for t in M.prp.tops():
        if M.prp.names[t] in plan(M.name)[0]:
            for k in range(t, M.prp.end[t]):
                nd = M.prp.nodes[k]
                keep = [c for c in nd['ctrls'] if M.prp.p.key(c[0]) not in STRIP]
                n += len(nd['ctrls']) - len(keep)
                nd['ctrls'] = keep
    log('  kl_fa_author: %s: %d squads stay, %d mini-cutscene controllers taken off them' % (M.name, len(plan(M.name)[0]), n))
    if M.name == PART_A and ROOM_RUNS:
        import kl_fa_street                             # put_world: a squad's children are local to its group
        kl_fa_street.put_world(M, ROOM_PLACE, log)
    return n


def layer_names(sc):
    """Top-level names of the layer in a joined scene: what kl_fa.repair's prune may cut dead
    references from (the host's map is gone; the second part is not there yet in the first step)."""
    camp = set(campaign_names(PART_A)) | set(campaign_names(PART_B))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    """True once both parts of the map are in the scene: wire() names nodes of both."""
    return bool(sc.resolve(R + A_MAP[:-1]) and sc.resolve(R + B_MAP[:-1]))


# ------------------------------------------------------------------ the ledge
HERO_BITS = 0x28        # collision flags that stop a player: 0x20 (in 0x72, every wall and floor) and 0x08 (in 0x108,
                        # the whole flag word of 76 static placements of stock F01 / F07 / L03, all named ColiObj_*,
                        # 73 of them hero / block / hack / fix). ASSUMPTION by those names. Not a player's: 0x40
                        # alone (camera blockers), 0x10 alone (F07's BlockVisionPlane: AI sight only)
SIGHT_BIT = 0x10        # blocks AI sight: the only bit of stock F07's 'BlockVisionPlane', which F07 itself removes
                        # with a DeactivateGeom 23 s into the round; glass has 0x66 / 0x62 (no 0x10), a wall 0x72


def ledge_facts():
    """The tables against the measured balcony -> [what is wrong]. No file is read."""
    bad = []
    crooks = [k for k in SPAWN if SPAWN[k][0] in (START, TRAITOR)]
    for kind in crooks:
        pts, d, _face = SPAWN[kind]
        for p in pts:
            q = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            if not (LEDGE[0][0] <= q[0] <= LEDGE[0][1] and LEDGE[1][0] <= q[2] <= LEDGE[1][1] and q[1] == LEDGE_Y):
                bad.append('%s point %s is not on the balcony\'s nav area' % (kind[28:], q))
            if math.dist(q, BOMB) <= 600.0:
                bad.append('%s point %s is %d from the bomb (its first radius is 600)' % (kind[28:], q, math.dist(q, BOMB)))
            if math.dist(q, INVISIBOMB) <= 300.0:
                bad.append('%s point %s is %d from the InvisiBomb (radius 300)' % (kind[28:], q, math.dist(q, INVISIBOMB)))
    for name in ('Bound', 'Warn01', 'Warn02'):
        (c, _f, h, _w) = PLACE['Specials!LevelBound!040_LevelBound_AlleyTop!' + name]
        if c[0] - h[0] <= LEDGE_RAIL[0][1]:
            bad.append('the tower\'s level bound %s begins at x %d, inside the rail (%d)' % (name, c[0] - h[0], LEDGE_RAIL[0][1]))
    return bad


def ledge(archive, log=print):
    """The ledge test on a built level, from its .HVK / .gms / .prp alone -> number of failures.
    1. what the level has outside the main window (the slab, the rail, the glass, by name);
    2. a walk test (kl_escape.Walk: floors within 45 degrees of level, steps of 45 up / 60 down,
       blocked by anything 55..165 above the floor; only shapes with a player's collision bits)
       from a START point, with the level as it loads (hidden entities have no collision:
       ASSUMPTION, the rule stock F07's BlockVisionPlane and Dead Men's own window rest on): the
       walk must stay on the balcony - the glass keeps the heisters out, the rail keeps them on;
    3. the same after the blast (the intact window off, the blown window and the first cracked
       pane on - what the forced ShotActivate of the window does): the boardroom must be reached;
    4. every criminal spawn point and player group of the level stands on a reached cell."""
    import kl_escape, kl_hvk
    with zipfile.ZipFile(archive) as z:
        m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
        hvk = kl_hvk.Hvk(z.read(m['.hvk']))
    sc, _snd, _loc = kl_fa.load(archive)
    ents = list(scene.entities())
    name = {e.ref: e.name.decode('latin1') for e in ents}
    hidden = {e.ref for e in ents if e.flags & HIDDEN}
    bad = 0
    def fail(s):
        nonlocal bad
        bad += 1
        log('  FAIL: ' + s)
    def box(s, inst):
        vs = [struct.unpack_from('<3f', s.verts, i * s.vstride) for i in range(len(s.verts) // s.vstride)]
        p, r = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
        w = [[100 * (p[a] + r[3 * a] * v[0] + r[3 * a + 1] * v[1] + r[3 * a + 2] * v[2]) for a in range(3)] for v in vs]
        return [min(v[a] for v in w) for a in range(3)], [max(v[a] for v in w) for a in range(3)]
    log('THE LEDGE: collision outside the main window (x 5860..6400, y 20900..21300, z -1200..1000)')
    soft, facts = set(), {}
    for s in hvk.shapes:
        fl = 0
        for _su, f, _n in s.sub:
            fl |= f
        for inst in s.inst:
            r = kl_hvk.ref(inst)
            if not fl & HERO_BITS:
                soft.add(r)
            if s.type != kl_hvk.STATIC or s.convex:
                continue
            lo, hi = box(s, inst)
            if hi[0] > 5860 and lo[0] < 6400 and hi[1] > 20900 and lo[1] < 21300 and hi[2] > -1200 and lo[2] < 1000:
                nm = name.get(r, '?')
                facts[nm.split('!')[-1]] = (lo, hi, fl)
                log('  %-58s (%d %d %d)-(%d %d %d) flags %#x%s%s%s' % (nm[-58:], *lo, *hi, fl, '' if fl & HERO_BITS else ' (no player collision)',
                                                                   ' blocks AI sight' if fl & SIGHT_BIT else '', ' HIDDEN at load' if r in hidden else ''))
    for want in ('SO0200_M09_FrontTopWindows_01', 'ColiObj_Plane01', 'SI0200_M09_Window_Glass_Geom_Pre_00'):
        if want not in facts:
            fail('%s has no static collision at the window' % want)
    pre = facts.get('SI0200_M09_Window_Glass_Geom_Pre_00')
    if pre and not pre[2] & SIGHT_BIT:
        fail('the intact window does not block AI sight (flags %#x)' % pre[2])
    for s in ledge_facts():
        fail(s)
    ref_of = lambda end: {r for r, nm in name.items() if nm.endswith(end)}
    on, off = ref_of('SI0200_M09_Window_Glass_Geom_Post_00') | ref_of('SI0200_M09_GlassWindow_00_A'), ref_of('SI0200_M09_Window_Glass_Geom_Pre_00')
    if not on <= hidden or off & hidden:
        fail('the window is not in its intact state at load (blown / cracked hidden: %s, intact hidden: %s)' % (on <= hidden, bool(off & hidden)))
    area = (3300.0, 6500.0, -1500.0, 1300.0)
    at = (START[0][0], LEDGE_Y, START[0][2])
    (x0, x1), (z0, z1) = LEDGE_RAIL
    for title, skip in (('as the level loads', soft | hidden), ('after the blast', (soft | hidden | off) - on)):
        w = kl_escape.Walk(hvk, area, skip=skip)
        seen, _par, block = w.flood(at)
        xs, zs = [w.centre(c)[0] for c in seen], [w.centre(c)[1] for c in seen]
        log('walk test from %s, %s: %d cells of 20 x 20, x %d..%d, z %d..%d, floor y %d..%d' % (
            tuple(int(v) for v in at), title, len(seen), min(xs), max(xs), min(zs), max(zs), min(seen.values()), max(seen.values())))
        out = [w.centre(c) for c in seen if w.centre(c)[0] > x0 and not (w.centre(c)[0] < x1 and z0 < w.centre(c)[1] < z1)]
        if out:
            fail('the walk leaves the balcony\'s rail (x %d, z %d..%d) at %d cells, e.g. (%d, %d)' % (x1, z0, z1, len(out), *out[0]))
        if title.startswith('as'):
            if min(xs) < 5860:
                fail('the intact glass does not keep the walk out (x %d reached)' % min(xs))
            stop = collections.Counter(name.get(r, '?').split('!')[-1] for r in block)
            log('  what bounds it: %s' % ', '.join(sorted(stop)))
            for k in range(1, len(sc.nodes)):
                if sc.cls(k) == 'ZSpawnPoint' and SPAWN.get(kl_fa.node_values(sc, k)[8], (None,))[0] in (START, TRAITOR) or \
                        sc.parent[k] == 0 and sc.names[k].startswith('Heroes!Hero_0'):
                    p = kl_fa.node_values(sc, k)[2]
                    c = w.cell(p[0], p[2])
                    if c not in seen or abs(seen[c] - p[1]) > 5:
                        fail('%s at (%d, %d, %d) does not stand on the balcony\'s floor' % (sc.names[k], *p))
        elif min(xs) > 5600:
            fail('the blown window is not passable on foot (the walk ends at x %d)' % min(xs))
    log('ledge test: %s' % ('ok' if not bad else '%d failures' % bad))
    return bad


# ------------------------------------------------------------------ the inventory
def inventory(archive, log=print):
    """What the layer consists of in a built level, with world coordinates read back from it."""
    sc, _snd, _loc = kl_fa.load(archive)
    with zipfile.ZipFile(archive) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    ents = list(scene.entities())
    pos = kl_maps.world(scene)
    at = lambda k: '(%6d %6d %6d)' % tuple(round(x) for x in pos[ents[k - 1]])
    ctl = lambda k: ','.join(sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls'])
    half = lambda k: ' half %s' % (tuple(round(x) for x in kl_fa.node_values(sc, k)[8:11]),) if sc.cls(k) == 'ZBoxPrimitive' else ''
    def row(k, note=''):
        log('  %-74s %-22s %s%s %s %s' % (sc.path[k][5:][-74:], sc.cls(k), at(k), half(k), ctl(k), note))
    log('SETTINGS, DEFINE, SPEAKERS, BRIEFING (F07\'s own, untouched)')
    for k in range(1, len(sc.nodes)):
        if sc.parent[k] == 0 and (sc.cls(k) in kl_fa.SPEAKERS or any(sc.p.key(nm) in ('OnlineFragileAllianceSettings', 'FAMissionBriefingTrigger', 'AIMonitor', kl_fa.MONITOR)
                                                                      for nm, _b in sc.nodes[k]['ctrls']) or sc.names[k].endswith('IsMultiplayerLevel')):
            row(k)
    log('SPAWN POINTS (ZSpawnPoint) and player groups')
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint':
            row(k, kl_fa.node_values(sc, k)[8].replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''))
        elif sc.parent[k] == 0 and sc.names[k].startswith('Heroes!'):
            row(k)
    log('PLACED HOST OBJECTS (PLACE; source of each number in the table)')
    for name, (_p, _f, _h, why) in PLACE.items():
        row(node_of(sc, name), '<- ' + why)
    log('LOOT (OnlineMoneyCtrl NORMAL / CONTAINER)')
    total = 0
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' not in v[2]:
            total += v[1]
            row(k, '%s %d%s' % (v[2][16:], v[1], ' HIDDEN at start' if kl_fa.node_values(sc, k)[3] else ''))
    pools = collections.Counter(v[0][20:] for _k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2])
    log('  loot %d; drop pools left: %s' % (total, dict(pools)))
    log('ESCAPE')
    for k in range(1, len(sc.nodes)):
        names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if any(n in names for n in (kl_fa.EXIT, 'OnlineEscAnimatedVehicle', 'PathBlocker', 'OnlineEscCamTrigger', 'KillBox')) or \
                (sc.names[k] in ('V_Van_00', 'BoardingTrigger', 'BoardingCar') and 'Reflection' not in sc.path[k]) or sc.names[k].endswith('POI_TheEscapeArea'):
            if sc.path[k].startswith((R + 'Animation/', R + 'Gameplay!EscapeSetup', R + 'FASpecials!POI')):
                row(k)
    log('ROUND START, JOIN, MAIN ROOM (ROLE) and the campaign objects kept for them')
    for role, name in ROLE.items():
        k = node_of(sc, name)
        row(k, '= ' + role)
        for nm, body in sc.nodes[k]['ctrls']:
            for u in units(body[1:-1]):
                v = kl_fa.value(sc, u)
                if isinstance(v, list) and v and isinstance(v[0], str):
                    for s in v[:40]:
                        log('        -> %s%s' % (s[5:][-110:], '' if sc.resolve(s) else '   NOT IN THE LEVEL'))
    for lv in (PART_A, PART_B):
        for name in CAMPAIGN_KEEP[lv]:
            if sc.resolve(R + name):
                k = node_of(sc, name)
                row(k, '(%s)%s' % (lv, ' = tower step' if name in STEPS else ''))
                for s in named(sc, k)[:16]:
                    log('        -> %s%s' % (s[5:][-110:], '' if sc.resolve(s) else '   NOT IN THE LEVEL'))
    log('LEVEL BOUNDS')
    for k, _i, _v in kl_fa.controllers(sc, 'LevelBound'):
        row(k)
    log('SQUADS (ZSquadScript)')
    n = collections.Counter()
    for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript'):
        actors = [j for j in range(k, sc.end[k]) if sc.cls(j) == 'ZFFActor']
        n['squads'] += 1; n['actors'] += len(actors)
        log('  %-70s %d actors, first %s%s' % (sc.path[k][5:][-70:], len(actors), at(actors[0]) if actors else '-',
                                             '   dead -> %s' % [s.split('!')[-1] for s in v[SQUAD_DEAD]] if v[SQUAD_DEAD] else ''))
    log('  %s' % dict(n))


def move_hero(folder, out, pos, face=None, name='Heroes!Hero_01', slot=kl_maps.SLOT, log=print):
    """TEST AID for direct boots: a copy of a kept build in <out> in which one player group stands
    somewhere else (a direct boot puts the player at Heroes!Hero_01; the tower's boardroom is closed
    until the round-start blast, so the escape car, the lobby and the street are reached this way).
    Only the group's ZGEOM[1] / [2] in the .prp and its .gms record change."""
    import shutil
    os.makedirs(out, exist_ok=True)
    src = os.path.join(folder, slot + '_Main.zip')
    sc, _snd, _loc = kl_fa.load(src)
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        files = {n: z.read(n) for n in names}
    m = {n.rsplit('_Main', 1)[1]: n for n in names if '_Main' in n}
    scene = kl_scene.Scene(kl_gms.unpack(files[m['.gms']]), files[m['.buf']])
    lv = type('Built', (), {'prp': sc, 'ents': list(scene.entities())})
    k = place(lv, name, pos, face)
    gms, buf = scene.write()
    files[m['.gms']], files[m['.buf']], files[m['.prp']] = kl_gms.pack(gms), buf, sc.p.serialize()
    with zipfile.ZipFile(os.path.join(out, slot + '_Main.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n in names:
            z.writestr(n, files[n])
    for f in os.listdir(folder):
        if f.startswith(slot + '_Main') and f != slot + '_Main.zip':
            shutil.copyfile(os.path.join(folder, f), os.path.join(out, f))
    log('%s: %s (node %d) stands at %s%s' % (out, name, k, tuple(pos), ' facing %s' % (tuple(face),) if face else ''))


def test(out, keep=False, log=print):
    """Build the two-part level with the layer into <out>, verify, check, print the inventory."""
    r = kl_maps.chain(out, HOST, PART_B, PART_A, campaign=True, heroes=False, keep=True, author=True)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    folder = os.path.join(out, 'R09+%s%s' % (PART_A, r['tag']))
    archive = os.path.join(folder, kl_maps.SLOT + '_Main.zip')
    late = [p for fn in FINISH for p in fn(folder, log)]            # kl_fa_loot: the loot's props, on the written level
    inventory(archive, log)
    off = ledge(archive, log) or late
    mine = [p for p in r['problems'] if not any(k in p for k in KNOWN)]
    fa = [f for f in r['fa_findings'] if f.startswith(('CRASH', 'BROKEN'))]
    log('\nkl_graft.verify: %d problems, %d of them not KNOWN' % (len(r['problems']), len(mine)))
    for p in r['problems']:
        log('  %s %s' % ('known ' if p not in mine else 'OPEN  ', p[:230]))
    log('kl_fa.check: %s' % r['fa'])
    for f in r['fa_findings']:
        log('  ' + f[:230])
    log('level: %d entities, %d rooms, %.0f MB; first step %s' % (r['entities'], r['rooms'], r['archive_mb'], r.get('first')))
    import kl_chars                                     # who would not be drawn, and why (re/invisible.md)
    unseen = kl_chars.undrawn(kl_chars.Lv(folder))
    log('kl_chars.undrawn: %d' % len(unseen))
    for u in unseen:
        log('  ' + u[:260])
    off = off or unseen
    if not keep:
        for d in (folder, os.path.join(out, 'chain', '%s+%s' % (HOST, PART_B))):
            for f in os.listdir(d):
                if '_Main' in f:
                    os.remove(os.path.join(d, f))
    log('RESULT: %s' % ('PASS' if not mine and not fa and not off else 'FAIL'))
    return 1 if mine or fa or off else 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        global NO_AI, ROOM_WAITS, BLAST_DELAY, BOMB_FUSE, BLAST_HARMLESS, ONE_WAVE, POLICE_FOLLOW
        NO_AI = '--no-ai' in a
        ROOM_WAITS = '--guards-awake' not in a          # ('--guards-wait' of the builds before is the default now)
        BLAST_HARMLESS = '--blast-real' not in a
        ONE_WAVE = '--one-wave' in a
        ROOM_RUNS = '--room-classic' not in a
        POLICE_FOLLOW = '--police-follow' in a
        if '--loot-bags' not in a:                      # the loot's props and places (kl_fa_loot, on the written level)
            import kl_fa_loot
            kl_fa_loot.hook()
        if '--blast-delay' in a:                        # OPTION, seconds from the round-start event to the warm-up
            BLAST_DELAY = float(a[a.index('--blast-delay') + 1])
        if '--fuse' in a:                               # OPTION, the bomb's fuse (its own value: 4)
            BOMB_FUSE = float(a[a.index('--fuse') + 1])
        sys.exit(test(a[1], '--keep' in a))
    elif len(a) == 2 and a[0] == 'ledge':
        sys.exit(1 if ledge(a[1]) else 0)
    elif a == ['plan']:
        for lv in (PART_A, PART_B):
            keep, left = plan(lv)
            print('%s: %d squads stay (%d actors), %d do not' % (lv, len(keep), sum(n for _p, n, _s in keep.values()), len(left)))
            for n, (p, k, s) in sorted(keep.items()):
                print('  stays  %-62s %d actors, starts at \\%s%s' % (n, k, p.split('\\')[-1], '; stripped: ' + ', '.join(s) if s else ''))
            for n, why in sorted(left.items()):
                print('  goes   %-62s %s' % (n, why))
    elif a == ['vans']:
        S = kl_graft.Level(HOST)
        for name in VANS:
            main_, every, s = van_path(S, node_of(S.prp, name))
            (dx, dz), x, width, z0, z1 = van_fit(main_, s)
            print('%s: %d positions (%d in the drive, %.0f m), stop (%d %d %d) in F07; best facing (%.2f, %.2f): %d wide, %d before and %d after the stop' % (
                name, len(every), len(main_), sum(math.dist(p, q) for p, q in zip(main_, main_[1:])) / 100, *s, dx, dz, width, -z0, z1))
    elif len(a) == 2 and a[0] == 'inventory':
        inventory(a[1])
    elif len(a) in (6, 8) and a[0] == 'hero':
        move_hero(a[1], a[2], [float(x) for x in a[3:6]], [float(x) for x in a[6:8]] or None)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_author                 # kl_graft imports this file by name: one module, one NO_AI
    kl_fa_author.main()
