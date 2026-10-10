#!/usr/bin/env python3
"""
Retomoto Tower, part B: the street. Out of the front entrance, down the road to a van - 'like
the movie Heat': police waves along the road, the escape, the street's bounds. Offline; nothing
here installs anything or starts the game. Spec, evidence, live test order: re/retomoto_street.md.
Part A and the layer as a whole are tools/kl_fa_author.py (re/retomoto_fa.md); this file hooks
into it and edits nothing of it.

    python kl_fa_street.py test <out> [--keep] [--no-ai] [options]
                                       build F07 + M09_B + M09_A with kl_fa_author's layer AND
                                       this one into <out> (a scratch folder; kl_maps.chain),
                                       verify, kl_fa.check, read the street back from the built
                                       archive: wave table, escape, bounds, sketch. Exit 1 if a
                                       problem is left that is not known, or a check here fails.
                                       Options, one variable each (re/retomoto_street.md 8):
                                       --merc-only    wave boxes ECPS_FA_MERCONLY (default: stock ECPS_BOTH)
                                       --three-vans   the exit box picks among F07's three vans (stock)
                                       --vans-stay    the two vans that are not called stay on the road
                                       --rigid        actors keep F07's distance to their cover points
                                       --no-waves     F07's squads are kept but nothing starts them
                                       --street-classic  the street as before 2026-10-10: police start at the front
                                                      door, no fall-back chains, stock run-to-escape clock
                                       --no-chains    dynamic street without the 'wiped out -> neighbours fall
                                                      back' lists (ZSquadScript field 8: an ASSUMPTION)
                                       --van-bent     F07's drive as kl_fa_author fits it (kl_fa_van off)
                                       --no-police    F07's squads and their boxes are not kept at all
                                                      (with --no-ai: an empty street, for the escape)
    python kl_fa_street.py report <archive>   the same read-back of a built level
    python kl_fa_street.py squads              F07's 14 police squads as stock has them
    python kl_fa_street.py plan                the tables below with every point put on M09_B's
                                               navigation mesh (no build; 10 s)

HOW (no new entity, no new controller: stock F07 objects re-placed, values and lists edited)
  F07 has 14 police squads as top-level groups (6 Gameplay!020_Loot!, 6 Gameplay!030_AfterLoot!,
  2 Gameplay!040_Escape!). Each is a ZGROUP + ZSquadScript at a translation of its own with
  identity rotation; its actor groups, the RunToPosInfo / Pos boxes of its routs and (the dog) a
  trigger box are children with local positions. They name nothing of F07's map: 26 weapon
  templates in the systems side and each other (kl_fa_street.py squads). So a squad moves by
  moving the group and re-laying its children:
    1. the squad's layout is mapped RIGIDLY in the ground plane (one turn about Y, one shift) so
       that the centre of its cover points lands on an anchor of the table and the direction
       'actors -> cover' points at the criminals;
    2. every point is then put on M09_B's own navigation mesh at the mesh's height (F07's alleys
       have platforms at y 100..500, the road is flat at y -47..-40): a point that falls off the
       mesh is pulled towards the anchor until it stands on it;
    3. the actors' start group is pulled in to MAX_BACK behind the cover points (F07 has them
       3 - 58 m away round the corners of its alleys; the road has no corners). --rigid: not.
  The group itself gets the anchor as its translation and keeps the identity rotation every
  stock squad group has (no stock level has a ZFFActor under a rotated parent: 0 of 43 in F07,
  0 of 49 in F01; all 43 of F07's are under a translated one).
  Waves are started by F07's own trigger boxes, re-placed across the road (BOXES), each still
  holding the reference list stock gave it wherever that list fits.

FOR kl_fa_author (the exact lines; until they are in, hook() patches the same three places from
outside for the length of a process, and 'test' here does that):
    KEEP = (...) + kl_fa_street.KEEP                              # kl_fa_author.KEEP
    kl_fa_street.prepare_host(S, log)                             # last line of prepare_host(S, log)
    kl_fa_street.wire(sc, log)                                    # last line of wire(sc, log)

GUESS = a value not copied from a stock object and not measured in the levels; each table entry
says which it is. ASSUMPTION = fits the evidence, not proven. Sources of the measured values:
re/retomoto.md 3.4 (road, static cars), re/retomoto_fa.md 9 - 10 (heights and van stops seen
live), the level files (kl_fa_street.py squads / plan).
"""
import collections, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms, kl_scene, kl_pf4
import kl_prpjoin as J
import kl_fa_author as au
import kl_fa_van

R = 'ROOT\\'
IDENT = (0.0, 1.0)                      # au.rot9(IDENT) = the identity (third, second, first column)

# ------------------------------------------------------------------ the street (M09_B), measured
ROAD = (-5700.0, -300.0)                # carriageway in x (re/retomoto.md 3.4); kerbs to x -6000 / 0
LANE = (-5400.0, -600.0)                # where a squad's point may stand: 3 m inside the carriageway
DOOR = (2600.0, -6490.0)                # front entrance, centre of the doorway (x, z)
PLAY = ((-6200.0, 3000.0), (-12500.0, 13800.0), (-150.0, 110.0))   # road + forecourt, at road level: the
                                        # polygons of the navigation mesh a point may stand on
START = (-3000.0, -6000.0)             # a point of the road in front of the entrance (the scripted walks pass it)
MAX_BACK = 1500.0                       # GUESS: actors start at most this far behind their cover points
RIGID = False                           # True ('--rigid'): actors keep F07's distance (3 - 58 m)
WAVES = True                            # False ('--no-waves'): the squads are kept and placed, nothing starts them
POLICE = True                           # False ('--no-police'): none of F07's squads or wave boxes is kept (test builds)
WHO = 'ECPS_BOTH'                       # field 14 of the wave boxes. Stock F07: ECPS_BOTH on all three of its
                                        # squad boxes - a criminal OR a returned policeman starts the wave, which is
                                        # what F01's pair tbPlatform#0n_MercOnly / tbStreet_RespawnOnly does with two
                                        # boxes (re/fa_gamemode.md 2). '--merc-only': ECPS_FA_MERCONLY
SOUTH, NORTH = (0.0, -1.0), (0.0, 1.0)

# F07's police squads: name -> (wave, anchor x, anchor z, the way the squad faces = where the
# criminals come from, what stands there). The anchors are GUESSES beside objects of the
# campaign's own street (their positions measured: re/retomoto.md 3.4 and 'plan' below).
G2, G3, G4 = 'Gameplay!020_Loot!', 'Gameplay!030_AfterLoot!', 'Gameplay!040_Escape!'
SQUADS = collections.OrderedDict([
    # wave 1: mid road, 35 - 55 m north of the door line, in the standing traffic
    (G2 + '020_FinancialAlley_LeftParking',        (1, -4100, -2700, SOUTH, 'west lane: Civilian_E (-4078, -3574), Taxi_Green_06 (-4165, -2192)')),
    (G2 + '020_FinancialAlley_LeftFurther',        (1, -1800, -2500, SOUTH, 'east lane: Taxi_Red_01 (-1775, -2206), Taxi_Green_02 (-1790, -3009)')),
    (G2 + '020_FinancialAlley_RightGround',        (1, -2900, -1900, SOUTH, 'middle: Civilian_B_00#16 (-2154, -1500)')),
    (G2 + '020_FinancialAlley_RunForDumpster',     (1, -4100, -1250, SOUTH, 'west lane: Civilian_A_00#14 (-4124, -1021), Taxi_Red_07 (-4165, -1593)')),
    (G2 + '020_FinancialAlley_RightPlatform',      (1, -1800, -1250, SOUTH, 'east lane: Civilian_A_00#06 (-1792, -1598)')),
    # wave 2: the campaign's first road block, three police cars at (-4090, 3602) (-3493, 3805)
    # (-1901, 3911); the police side of it is north
    (G3 + '030_FinancialAlleyExit_Left',           (2, -4090, 4050, SOUTH, 'behind block car #04 (-4090, 3602)')),
    (G3 + '030_FinancialAlleyExitStreet_Left',     (2, -3493, 4200, SOUTH, 'behind block car #03 (-3493, 3805)')),
    (G3 + '030_FinancialAlleyExitStreet_Right',    (2, -2700, 4150, SOUTH, 'the gap between cars #03 and #01')),
    (G3 + '030_FinancialAlleyExit_Right',          (2, -1901, 4300, SOUTH, 'behind block car #01 (-1901, 3911)')),
    (G3 + '030_FinancialAlleyExitSkywalk',         (2, -3340, 2900, SOUTH, 'in front of the block: Taxi_Red_03 (-3339, 3174), Taxi_Green_01 (-3813, 2832)')),
    (G3 + '030_FinancialAlleyExitSkywalkNoCover',  (2, -2300, 3300, SOUTH, 'in front of the block, open road')),
    (G2 + '021_FinancialAlley_Dog',                (2, -3000, 4500, SOUTH, 'behind the block; the dog runs at the criminals')),
    # wave 3: the far end, at the campaign's SWAT truck V_JPN_SWAT_North (-3588, 10886), north of the van's stop
    (G4 + '040_EscapeEntranceLeft',                (3, -3588, 10450, SOUTH, 'in front of the SWAT truck (-3588, 10886)')),
    (G4 + '040_EscapeEntranceRight',               (3, -2613, 11000, SOUTH, 'Taxi_Red_04 (-2613, 11468)')),
])
# stock F07 sends every squad but the dog to a 'run to the escape' position a minute after the
# criminals pass the alley's end (Gameplay!RunToEscape!*: box -> 44 s -> gate -> 18 s -> the 13
# '40_RunToEscape' routs; three criminals: 32 s). Kept as it is; the 13 positions, one per squad
# in SQUADS order, close a ring round the van's stop. GUESS: every point (offsets from the stop)
RING = [(-830, -1700), (-200, -1800), (-1430, -2000), (-2330, -1000), (-1730, 0),          # wave 1: from the south
        (-2930, 100), (-2330, -400), (-1730, 1000), (470, 1000), (-1130, 1200), (-530, 1000),   # wave 2: west and north
        (-2530, 1200), (-1930, 1000)]                                                      # wave 3: north

# The one van. F07 has three; the exit box picks one at random (kl2 0x6c3f90) and each stops
# somewhere else (kl_fa_author: 16 - 27 m apart on this road). VAN = index into kl_fa_author.VANS.
# Van 01's stop is the northernmost (longest run), nothing static stands within 14 m of it, and
# kl_fa_author already puts the 'Escape area' marker on it. '--three-vans': stock behaviour.
VAN = 0
ONE_VAN = True
PARK_OTHERS = True                      # the two vans that are not called go 600 m under the road ('--vans-stay':
                                        # they stand at their waiting places as scenery, as in the live runs so far)
EXIT_BEFORE = 2500.0                    # the exit box begins this far before the stop. Stock F07: its box's south
                                        # face is 23.9 - 26.0 m before its three stops
EXIT_AFTER = 2000.0                     # ... and ends this far beyond it (GUESS; stock: 45 m)
BOARD_BACK = 337.0                      # the boarding box is this far behind the van's origin (its local -Z; read)

# trigger boxes: role -> (host object, centre, half extents, source). All are stock F07
# TriggerBox objects (fields 0..2 = 1, 1, 1; 13 eTGS_AllInside; 16 EFAMPS_ALL_MODES unless noted).
# Rotation: set to identity - tbEscapeAI is turned by 90 degrees in stock, and half extents are local.
DOG_BOX = G2 + '021_FinancialAlley_Dog\\tbReleaseDog'
BOXES = collections.OrderedDict([
    ('wave 1', (G2 + 'tbExitLoot', (-800, 300, -6500), (300, 400, 5400),
                'GUESS: the first 2 - 8 m of carriageway along the whole forecourt (z -11800..-1100), x -1100..-500; clear of '
                'the police point at (-367, -7594), where a player body stands from the load on')),
    ('wave 2', (DOG_BOX, (-3000, 300, -3300), (2700, 400, 300),
                'GUESS: across the road 6 m before the first squad of wave 1 (z -2700)')),
    ('wave 3', (G4 + 'tbEscapeAI', (-3000, 300, 2000), (2700, 400, 300),
                'GUESS: across the road 16 m before the first road block (z 3602)')),
    ('run', ('Gameplay!RunToEscape!tbRunToEscape1Player', (-3000, 300, 6500), (2700, 400, 300),
             'stock: 25 m before the van stops (F07: 25.2 - 27.3 m); here 28 m before the stop')),
    ('run 3', ('Gameplay!RunToEscape!tbRunToEscape', (-3000, 300, 6500), (2700, 400, 300),
               'with the box above, as in stock (F07: 3 m apart); EFAMPS_FA_UCC, counts three criminals')),
])
# what else of F07 has to stay for the chains above (single nodes, and the gate's group)
CHAIN = (G2 + 'Timer', 'Gameplay!RunToEscape!Timer', 'Gameplay!RunToEscape!Timer1Player', 'Gameplay!RunToEscape!Timer3Player',
         'Gameplay!RunToEscape!tcRunToEscape', 'Gameplay!RunToEscape!RunToEscapeGate')
KEEP = tuple(SQUADS) + tuple(v[0] for v in BOXES.values() if '\\' not in v[0]) + CHAIN + ('Gameplay!020_Loot!FollowPlayers!tbCountPlayers',)

# ------------------------------------------------------------------ THE DYNAMIC STREET (owner, 2026-10-09 late)
# 'they spawn in once you go down the elevator ... they are all like outside ish but they retreat to some
# of their spots to hold you off and the more you shoot the more they run away but the closer you get to
# the vehicle the more they try to shoot it'. Design, evidence and every GUESS: re/retomoto_ai.md 4 - 6.
# All of it is values, lists and places of objects the level already has.
DYNAMIC = True                          # False ('--street-classic'): the layer as the owner played it on 2026-10-09
CHAINS = True                           # False ('--no-chains'): no fall-back lists in ZSquadScript field 8
SQUAD_DEAD = au.SQUAD_DEAD              # field 8: the list sent when a squad is wiped out (ASSUMPTION, as kl_fa_author's)
E1, E2 = 'Enemies!010_RetoBldFront!', 'Enemies!020_Street!'
ELEVATOR = 'Mercenaries!TriggerBox_1_LeaveElevator'     # campaign box (5902, 709, -6488) half (100, 150, 1400): across
                                        # the lobby car's doors, where the hook's join puts the crew (read: M09_B)
ELEV_TIMER = E2 + 'Timer'               # campaign TriggerDelay, top-level, its own value 5 s
ELEV_DELAY = 5                          # s after the elevator box: the second pair runs in from out of sight (GUESS)
CAMPAIGN_KEEP_B = (ELEVATOR, ELEV_TIMER)
# campaign squad -> (what starts it, its rout that is named). Not listed: as kl_fa_author / CAMPAIGN_WAVE.
# The lobby's front is glass: what stands on the forecourt between z -8900 and -4000 is seen from the
# elevator landing. Squad_InFront is there from the load (ZSquadScript field 3 = 1): the picture the
# campaign had. Everybody else comes from where the lobby cannot see.
DYN_START = {
    E1 + 'Squad_InFront': ('elevator', 'Regroup'),              # 3 on the forecourt: run to the police car, hold
    E1 + 'Squad_Teargasguys': ('timer', 'FlankingBehaviour'),   # 2 from the south end of the forecourt, 5 s later
    E2 + 'Squad_RoadBlock_South': ('wave 1', '01_DefendBehaviour'),     # 3 at the rear of the static SWAT van (south)
    E2 + 'Squad_RoadBlock_South#02': ('wave 1', '01_SquadModifier'),    # 2: unleashed (kl_fa_author's pick was
                                        # '04_Retreat' -> Deactivate: they ran off and vanished at the door)
    E2 + 'Squad_SWAT_From_Behind_South': ('wave 1', 'FlankingBehaviour')}   # 3 at the static police car (south)
# campaign nodes re-placed, WORLD positions (x, y, z). y: 25 on the forecourt's paving, 22 on the raised
# strip east of the carriageway (x > -1500), 5 on the carriageway - the heights the campaign's own actors
# have there. Every (x, z) was put against M09_B's navigation mesh (Nav.floor) by the design pass. GUESSES.
DYN_PLACE = {
    E1 + 'Squad_InFront\\Regroup\\Pos#01': (-200, 25, -6600),                   # behind police car RetoFront02 (147, -6408)
    E1 + 'Squad_InFront\\FlankingBehaviour\\LeftFlank#1': (-2800, 5, -7800),    # their fall-back: across the road
    E1 + 'Squad_InFront\\FlankingBehaviour\\RightFlank#1': (-2800, 5, -5200),
    E1 + 'Squad_Teargasguys\\JPN_Teargas_Police_01#02': (-800, 22, -10800),    # start: south of the facade's end (z -8837)
    E1 + 'Squad_Teargasguys\\JPN_Teargas_Police_01#01': (-1300, 22, -10600),
    E1 + 'Squad_Teargasguys\\FlankingBehaviour\\LeftFlank#1': (-400, 25, -7700),    # behind police car RetoFront01 (38, -7382)
    E1 + 'Squad_Teargasguys\\FlankingBehaviour\\RightFlank#1': (-200, 25, -7200),
    E2 + 'Squad_RoadBlock_South\\01_DefendBehaviour\\Pos#01': (-1000, 22, -7000),   # the road at the forecourt, behind the crew
    E2 + 'Squad_RoadBlock_South\\03_Retreat\\Pos#01': (-4500, 5, -7000),            # west kerb, then 'Deactivate' (campaign's own)
    E2 + 'Squad_RoadBlock_South#02\\04_Retreat\\Pos#01': (-4500, 5, -7000),
    E2 + 'Squad_SWAT_From_Behind_South\\SWAT_Beam01': (-900, 22, -12800),      # start: the static police car south (-1189, -12382)
    E2 + 'Squad_SWAT_From_Behind_South\\SWAT_Beam02': (-1300, 22, -12800),
    E2 + 'Squad_SWAT_From_Behind_South\\SWAT_Beam03': (-1100, 22, -13000),
    E2 + 'Squad_SWAT_From_Behind_South\\FlankingBehaviour\\LeftFlank#1': (-1500, 22, -8500),
    E2 + 'Squad_SWAT_From_Behind_South\\FlankingBehaviour\\RightFlank#1': (-1500, 22, -4500)}
# 'the more you shoot the more they run away': a squad wiped out sends its neighbours one line back; a
# second loss on that side sends them to the van, or (forecourt) off the map. squad -> routs its field 8 names
FALL = collections.OrderedDict([
    (E1 + 'Squad_Teargasguys', (E1 + 'Squad_InFront\\FlankingBehaviour',)),
    (E1 + 'Squad_InFront', (E2 + 'Squad_RoadBlock_South\\03_Retreat', E2 + 'Squad_RoadBlock_South#02\\04_Retreat')),
    (G2 + '020_FinancialAlley_LeftParking', (G2 + '020_FinancialAlley_RunForDumpster\\20_RunToCover', G2 + '020_FinancialAlley_RightGround\\20_RunToCover')),
    (G2 + '020_FinancialAlley_LeftFurther', (G2 + '020_FinancialAlley_RightPlatform\\20_RunToCover', G2 + '020_FinancialAlley_RightGround\\20_RunToCover')),
    (G2 + '020_FinancialAlley_RightGround', (G2 + '020_FinancialAlley_RunForDumpster\\20_RunToCover', G2 + '020_FinancialAlley_RightPlatform\\20_RunToCover')),
    (G2 + '020_FinancialAlley_RunForDumpster', (G2 + '020_FinancialAlley_RightPlatform\\40_RunToEscape',)),
    (G2 + '020_FinancialAlley_RightPlatform', (G2 + '020_FinancialAlley_RunForDumpster\\40_RunToEscape',)),
    (G3 + '030_FinancialAlleyExitSkywalk', (G3 + '030_FinancialAlleyExitStreet_Left\\10_Defend', G3 + '030_FinancialAlleyExit_Left\\10_Defend')),
    (G3 + '030_FinancialAlleyExitSkywalkNoCover', (G3 + '030_FinancialAlleyExitStreet_Right\\10_Defend', G3 + '030_FinancialAlleyExit_Right\\10_Defend')),
    (G3 + '030_FinancialAlleyExit_Left', (G3 + '030_FinancialAlleyExitStreet_Left\\40_RunToEscape',)),
    (G3 + '030_FinancialAlleyExitStreet_Left', (G3 + '030_FinancialAlleyExit_Left\\40_RunToEscape',)),
    (G3 + '030_FinancialAlleyExit_Right', (G3 + '030_FinancialAlleyExitStreet_Right\\40_RunToEscape',)),
    (G3 + '030_FinancialAlleyExitStreet_Right', (G3 + '030_FinancialAlleyExit_Right\\40_RunToEscape',))])
BACK_1 = 2400.0                         # GUESS: wave 1's second line ('20_RunToCover') lies this far north of its first
# the road block's fall-back ('10_Defend', which nothing names in this layer): offsets from the van's stop.
# 20 m south of it, with the stop in view; the van carries a FakeTarget 'Mercenary' on its body (stock, all
# 15 vans), so police who see it shoot it - 'the closer you get to the vehicle the more they try to shoot it'
BACK_2 = {G3 + '030_FinancialAlleyExit_Left': (-2650, -2200), G3 + '030_FinancialAlleyExitStreet_Left': (-1850, -2000),
          G3 + '030_FinancialAlleyExitStreet_Right': (-750, -2200), G3 + '030_FinancialAlleyExit_Right': (-550, -1800)}
# wave 3 comes out of the static SWAT truck V_JPN_SWAT_North (-3588, 10886; its rear doors at z 10519 face
# south): squad -> where its actors start (owner: 'maybe use swat vans for some of the police spawning')
TRUCK = {G4 + '040_EscapeEntranceLeft': [(-3600, 10300)], G4 + '040_EscapeEntranceRight': [(-3800, 10300), (-3400, 10300)]}
# ... and is unleashed when the crew is this far before the stop: F07's spare box, across the road
GUARD_BOX = 'Gameplay!020_Loot!FollowPlayers!tbCountPlayers'
GUARD_BEFORE = 1300.0                   # GUESS
GUARD = (G4 + '040_EscapeEntranceLeft\\30_smUnleash', G4 + '040_EscapeEntranceRight\\30_smUnleash')
# stock sends every squad to the van 44 s + 18 s after the 'run' boxes (32 + 18 with three criminals). Shorter:
RUN_CLOCK = {'Gameplay!RunToEscape!Timer1Player': 20.0, 'Gameplay!RunToEscape!Timer3Player': 14.0, 'Gameplay!RunToEscape!Timer': 8.0}   # GUESS
VAN_CLEAR = 350.0                       # nobody is given a place this near the van's lane (its nose carries a KillBox)

# the campaign's own squads of the street (kl_fa_author keeps 10 and starts them all at the front
# entrance): which wave starts which. A name that is in no line stays at the entrance.
CAMPAIGN_WAVE = (('Enemies!020_Street!Squad_SWAT_From_Behind\\', 'wave 1'),         # 3 at (-3838, -2160): where wave 1 stands
                 ('Enemies!020_Street!Squad_RoadBlock_R2\\', 'wave 2'),             # (-1455, 3617): the block
                 ('Enemies!020_Street!Squad_RoadBlock_L\\', 'wave 2'),              # (-4318, 3839)
                 ('Enemies!020_Street!Squad_SniperResponse\\', 'wave 2'),           # (-4808, 2650)
                 ('Enemies!020_Street!Squad_Launcher_Dude_North\\', 'wave 2'))      # (-3468, 2804)
# stay at the entrance: 010_RetoBldFront (5 on the forecourt) and the three squads south of the south
# bound (z -12984 .. -14188), who come up the road BEHIND the crew as it turns north

# bounds. The play space is closed north and south by the campaign's own LevelBound boxes
# (kl_maps.campaign_drop keeps them) and open to the WEST: the navigation mesh joins the road to the
# overpass at z 7000..10500 (x -6000 and west, road level) and from there to the bus terminal
# (y -980) and the hotel street - 'kl_fa_street.py plan' draws it. One slab closes the whole west
# kerb. Rotation set to identity: F07's StreetLeft boxes are turned by 90 degrees in stock, and
# kl_fa_author's entry (half 400 / 1500 / 5000, no turn) came out as a wall ACROSS the road at
# z 2600..3400, x -12400..-2400 (re/retomoto_street.md 5).
WEST = 'Specials!LevelBound!030_LevelBound_StreetLeft!'
BOUNDS = collections.OrderedDict([
    (WEST + 'Bound',  ((-7000, 500, 5750), (500, 1500, 8250), 'GUESS: x -7500..-6500, z -2500..14000: 5 m west of the kerb (x -6000)')),
    (WEST + 'Warn01', ((-6850, 500, 5750), (650, 1500, 8250), 'GUESS: from x -6200 (stock warns 1.2 - 2.5 m before the bound)')),
    (WEST + 'Warn02', ((-6850, 500, 5750), (650, 1500, 8250), 'as Warn01')),
])


# ------------------------------------------------------------------ the navigation mesh (read only)
class Nav:
    """Polygons of a Dog Days-form mesh block (kl_pf4: array 3 polygons, 9 edges, 6 vertices as
    x, z, y; 5 waypoints). Height of a vertex = the feet's height (seen live: the player's feet on
    the road are at y -47..-40, the mesh has -48..-40 there)."""

    def __init__(self, block):
        _n, A = kl_pf4.split(block, True)
        polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        edges = [struct.unpack('<iII', r) for r in A[9]]
        verts = [struct.unpack('<5f', r) for r in A[6]]
        self.pv = [[(verts[edges[e][1]][0], verts[edges[e][1]][2], verts[edges[e][1]][1]) for e in range(p[5], p[5] + p[0])] for p in polys]
        self.nb = collections.defaultdict(set)
        for i, p in enumerate(polys):
            for e in range(p[5], p[5] + p[0]):
                j = edges[e][0]
                j = -2 - j if j < -1 else j
                if 0 <= j < len(polys) and j != i:
                    self.nb[i].add(j); self.nb[j].add(i)
        # two waypoints of different polygons at one place join their areas (ASSUMPTION of
        # re/fa_round.md 6.1, borne out by every scripted walk)
        grid = collections.defaultdict(list)
        wps = [struct.unpack('<3fIIIHH', r) for r in A[5]]
        for w in wps:
            grid[int(w[0] // 100), int(w[1] // 100)].append(w)
        for w in wps:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for v in grid.get((int(w[0] // 100) + dx, int(w[1] // 100) + dz), ()):
                        if v[5] != w[5] and math.dist(w[:3], v[:3]) < 60 and max(v[5], w[5]) < len(polys):
                            self.nb[w[5]].add(v[5]); self.nb[v[5]].add(w[5])
        self.box = [(min(v[0] for v in vs), max(v[0] for v in vs), min(v[2] for v in vs), max(v[2] for v in vs),
                     sum(v[1] for v in vs) / len(vs)) if len(vs) >= 3 else None for vs in self.pv]
        self.play = [i for i, b in enumerate(self.box) if b and b[1] >= PLAY[0][0] and b[0] <= PLAY[0][1] and
                     b[3] >= PLAY[1][0] and b[2] <= PLAY[1][1] and PLAY[2][0] <= b[4] <= PLAY[2][1]]
        # ... and that can be walked to from the road: the mesh has islands (a 1.5 x 1.3 m polygon at
        # (-3000, 4500) among the cars of the first road block has no neighbour at all)
        self.walk = self.reach(*START)
        self.play = [i for i in self.play if i in self.walk]

    @classmethod
    def of_level(cls, level):
        """The mesh of a stock Dead Men level, converted as the graft converts it."""
        with zipfile.ZipFile(J.level_zip(level, 'dm')) as z:
            n = [x for x in z.namelist() if x.lower().endswith('_main.gms')][0]
            raw = kl_gms.unpack(z.read(n))
        o = struct.unpack_from('<I', raw, 0x34)[0]
        return cls(kl_pf4.convert(raw[o + 4:o + 4 + struct.unpack_from('<I', raw, o)[0]]))

    @classmethod
    def of_archive(cls, archive):
        with zipfile.ZipFile(archive) as z:
            n = [x for x in z.namelist() if x.lower().endswith('_main.gms')][0]
            raw = kl_gms.unpack(z.read(n))
        o = struct.unpack_from('<I', raw, 0x34)[0]
        return cls(raw[o + 4:o + 4 + struct.unpack_from('<I', raw, o)[0]])

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

    def floor(self, x, z, among=None):
        """Height of the play-space polygon under (x, z), or None."""
        for i in (self.play if among is None else among):
            b = self.box[i]
            if b[0] <= x <= b[1] and b[2] <= z <= b[3] and self.inside(i, x, z):
                return b[4]
        return None

    def put(self, x, z, towards):
        """(x, y, z) on the mesh: the point itself, or the first point on the mesh on the way from
        it to `towards`; and how far it was moved. towards has to stand on the mesh."""
        for s in range(0, 21):
            px, pz = x + (towards[0] - x) * s / 20, z + (towards[1] - z) * s / 20
            y = self.floor(px, pz)
            if y is not None:
                return (px, y, pz), math.hypot(px - x, pz - z)
        raise ValueError('(%d, %d) is not on the navigation mesh and neither is (%d, %d)' % (x, z, *towards))

    def nearest(self, x, z):
        """(x, z) if it stands on the mesh, else the centre of the nearest play-space polygon."""
        if self.floor(x, z) is not None:
            return (x, z)
        i = min(self.play, key=lambda i: math.hypot((self.box[i][0] + self.box[i][1]) / 2 - x, (self.box[i][2] + self.box[i][3]) / 2 - z))
        vs = self.pv[i]
        return (sum(v[0] for v in vs) / len(vs), sum(v[2] for v in vs) / len(vs))

    def reach(self, x, z):
        """Polygons that can be walked to from (x, z)."""
        start = next(i for i in self.play if self.box[i][0] <= x <= self.box[i][1] and self.box[i][2] <= z <= self.box[i][3] and self.inside(i, x, z))
        seen, st = {start}, [start]
        while st:
            for j in self.nb[st.pop()]:
                if j not in seen:
                    seen.add(j); st.append(j)
        return seen


_nav = {}

def nav_b():
    if 'b' not in _nav:
        _nav['b'] = Nav.of_level(au.PART_B)
    return _nav['b']


# ------------------------------------------------------------------ a squad as stock has it
def trans(S, k):
    return struct.unpack('<3f', S.ents[k - 1].trans[:12])


def placed(S, top):
    """Nodes of a top-level group that have a place of their own: a non-zero local translation
    under parents (below the top) that have none. -> [(node, world position)]; what is below
    such a node rides on it. Every rotation up to the node has to be the identity."""
    sc, T, out = S.prp, trans(S, top), []
    r = struct.unpack('<9f', S.ents[top - 1].rot[:36])
    if max(abs(a - b) for a, b in zip(r, au.rot9(IDENT))) > 1e-3:
        raise ValueError('%s is rotated: the positions of its children are not world offsets' % sc.names[top])
    def go(k):
        for c in range(k + 1, sc.end[k]):
            if sc.parent[c] != k:
                continue
            t = trans(S, c)
            if any(abs(v) > 0.5 for v in t):
                out.append((c, tuple(T[i] + t[i] for i in range(3))))
            else:
                go(c)
    go(top)
    return out


def layout(S, top):
    """-> {'actors': [(node, world)], 'cover': [...], 'escape': [...], 'boxes': [...]} of a squad:
    actor groups (the parent of a ZFFActor), the points of its routs (RunToPosInfo, Pos#nn), the
    one point of '40_RunToEscape', trigger boxes."""
    sc, out = S.prp, collections.defaultdict(list)
    for k, w in placed(S, top):
        if any(sc.cls(c) == 'ZFFActor' for c in range(k + 1, sc.end[k])):
            out['actors'].append((k, w))
        elif kl_fa.has(sc, k, 'TriggerBox'):
            out['boxes'].append((k, w))
        elif sc.names[sc.parent[k]].startswith('40_'):
            out['escape'].append((k, w))
        else:
            out['cover'].append((k, w))
    return out


def starters(S):
    """What starts each squad in stock: {squad top: [paths of its nodes named from outside the
    squad or by a trigger box inside it]}, the 'run to escape' routs left out."""
    sc, out = S.prp, collections.defaultdict(list)
    tops = {au.node_of(sc, n) for n in SQUADS}
    for k, _h, _f, s, hit in J.references(sc):
        for j in hit:
            t = sc.top[j]
            if k > 0 and t in tops and (sc.top[k] != t or kl_fa.has(sc, k, 'TriggerBox')) and not sc.names[j].startswith('40_') \
                    and not kl_fa.has(sc, j, 'ZSquadScript') and sc.cls(j) != 'ZFFActor' and not any(sc.cls(c) == 'ZFFActor' for c in range(j + 1, sc.end[j])):
                if sc.path[j] not in out[t]:
                    out[t].append(sc.path[j])
    return out


def centre(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))


def relay(S, name, nav, ring=None, log=print, stop=None):
    """Move one squad (see the docstring). -> a row for the table."""
    sc = S.prp
    _wave, ax, az, face, _what = SQUADS[name]
    top = au.node_of(sc, name)
    lay = layout(S, top)
    anchor = nav.nearest(ax, az)
    cov = centre([w for _k, w in lay['cover']] or [w for _k, w in lay['actors']])
    act = centre([w for _k, w in lay['actors']])
    back = math.hypot(cov[0] - act[0], cov[1] - act[1])
    a = ((cov[0] - act[0]) / back, (cov[1] - act[1]) / back) if back > 100 else NORTH
    # the turn about Y that takes a to `face`:  (x, z) -> (c x - s z, s x + c z)
    c, s = a[0] * face[0] + a[1] * face[1], a[0] * face[1] - a[1] * face[0]
    def to(p, scale=1.0):
        dx, dz = (p[0] - cov[0]) * scale, (p[2] - cov[1]) * scale
        x, z = anchor[0] + c * dx - s * dz, anchor[1] + s * dx + c * dz
        return min(max(x, LANE[0]), LANE[1]), z
    pull = 1.0 if RIGID or back <= MAX_BACK else MAX_BACK / back
    new, moved = {}, 0.0
    truck = list(TRUCK.get(name, ())) if DYNAMIC else []
    for kind in ('cover', 'actors', 'boxes'):
        for k, w in lay[kind]:
            x, z = to(w, pull if kind == 'actors' else 1.0)
            aim, rout = anchor, sc.names[sc.parent[k]]
            if DYNAMIC and kind == 'cover' and _wave == 1 and rout.startswith('20_'):
                z += BACK_1                             # wave 1's second line: where FALL sends it
                aim = nav.nearest(anchor[0], anchor[1] + BACK_1)
            elif DYNAMIC and kind == 'cover' and rout == '10_Defend' and name in BACK_2 and stop is not None:
                x, z = stop[0] + BACK_2[name][0], stop[2] + BACK_2[name][1]     # the road block's fall-back, at the van
                aim = nav.nearest(x, z)
            elif kind == 'actors' and truck:
                x, z = truck.pop(0)                     # out of the static SWAT truck
                aim = nav.nearest(x, z)
            new[k], d = nav.put(x, z, aim)
            moved = max(moved, d) if aim is anchor else moved
    for k, _w in lay['escape']:
        new[k], d = nav.put(ring[0][0], ring[0][1], ring[1])
    origin = (anchor[0], au.ROAD_Y, anchor[1])
    au.place(S, top, origin)
    for k, p in new.items():
        if k in {b for b, _w in lay['boxes']} and sc.path[k][5:] in [v[0] for v in BOXES.values()]:
            continue                                    # a box with a job of its own: place_boxes()
        au.place(S, k, tuple(p[i] - origin[i] for i in range(3)))
    return {'name': name, 'top': top, 'anchor': anchor, 'back': back, 'pull': pull, 'moved': moved,
            'actors': len(lay['actors']), 'cover': len(lay['cover']), 'escape': len(lay['escape']),
            'at': {kind: [new[k] for k, _w in lay[kind]] for kind in ('actors', 'cover', 'escape')}}


# ------------------------------------------------------------------ the van
def van_pose(S, i):
    """Where van i stands when it waits for the crew, in the level as kl_fa_author laid it:
    -> (stop, heading, boarding box centre, waiting place). The stop is the PathBlockerVan box (the
    van's origin dwells within 4 units of it: keys 152..173 / 145..153 / 176..181 of the three
    drives step less than 3 units). The heading there is the drive's tangent; the van's nose is
    its local +Z (its KillBox is 1.6 m in front of the origin, its hatch 2.3 m behind), and the
    boarding box - a child of the van, 1.9 x 1.6 m - is BOARD_BACK behind the origin: at the rear
    doors, on the side the van came from."""
    sc = S.prp
    top = au.node_of(sc, au.VANS[i])
    main, _all, stop = au.van_path(S, top)
    grp = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'EscapeVehicle_Animation_F07')
    m = struct.unpack('<9f', S.ents[grp - 1].rot[:36])          # au.rot9(turn): [dx 0 dz, 0 1 0, dz 0 -dx]
    dx, dz = m[0], m[2]
    t = trans(S, grp)
    f = lambda p: (t[0] + dz * p[0] + dx * p[2], t[1] + p[1], t[2] - dx * p[0] + dz * p[2])
    near = min(range(len(main)), key=lambda j: math.hypot(main[j][0] - stop[0], main[j][2] - stop[2]))
    a = next(main[j] for j in range(near, -1, -1) if math.hypot(main[near][0] - main[j][0], main[near][2] - main[j][2]) > 100)
    h = (main[near][0] - a[0], main[near][2] - a[2])
    n = math.hypot(*h)
    p0, p1 = f(a), f(main[near])
    head = ((p1[0] - p0[0]) / n, (p1[2] - p0[2]) / n)
    at = f(stop)
    board = (at[0] - BOARD_BACK * head[0], at[1] + 119.0, at[2] - BOARD_BACK * head[1])
    return at, head, board, f(main[0])


def place_escape(S, log=print):
    """The exit box round the one stop, the exit trigger's list, the other vans out of the way."""
    sc = S.prp
    at, head, board, wait = van_pose(S, VAN)
    z0, z1 = at[2] - EXIT_BEFORE, at[2] + EXIT_AFTER
    au.place(S, au.ROLE['exit'], (au.ROAD_X, 500.0, (z0 + z1) / 2), None, (2700.0, 900.0, (z1 - z0) / 2), turn=IDENT)
    au.place(S, 'FASpecials!POI!POI_TheEscapeArea', (at[0], 150.0, at[2]))
    k = au.node_of(sc, au.ROLE['exit'])
    if ONE_VAN:
        pick = [R + au.VANS[VAN] + '\\EscapeVehicle_Animation_F07', '', '']
        kl_fa.edit(sc, k, au.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [au.setv(sc, us, 2 + j, s) for j, s in enumerate(pick)])
        for i, name in enumerate(au.VANS):
            if i != VAN and PARK_OTHERS:
                top = au.node_of(sc, name)
                grp = next(j for j in range(top, sc.end[top]) if sc.names[j] == 'EscapeVehicle_Animation_F07')
                t = trans(S, grp)
                au.place(S, grp, (t[0], t[1] + au.PARK[1], t[2]))
    log('  kl_fa_street: escape: van %d of %d is called; stop (%d, %d, %d), heading (%.2f, %.2f), boarding box at (%d, %d, %d); '
        'exit box z %d..%d; the others %s' % (VAN + 1, 1 if ONE_VAN else 3, *at, *head, *board, z0, z1,
                                              'listed too' if not ONE_VAN else 'parked under the road' if PARK_OTHERS else 'left standing'))
    return {'stop': at, 'head': head, 'board': board, 'wait': wait, 'exit': (z0, z1)}


# ------------------------------------------------------------------ 1. the host level before the graft
def prepare_host(S, log=print):
    """Re-place F07's 14 police squads, their trigger boxes, the exit box and the west bound for
    Retomoto's street. S: kl_graft.Level('F07') AFTER kl_fa_author.prepare_host(S). Values of
    existing objects only."""
    sc = S.prp
    if getattr(S, 'street', None):                      # hook() and the native lines together: once
        return S.street
    mine = set(KEEP) | {DOG_BOX}
    clash = sorted(mine & (set(au.ROLE.values()) | set(au.PLACE) | set(au.PARKED)))
    if clash:
        raise ValueError('kl_fa_author uses objects this layer needs: %s' % clash)
    if kl_fa_van.STRAIGHT:
        kl_fa_van.VAN = VAN
        kl_fa_van.straighten(S, log)                    # before anything here reads the van
    nav, start = nav_b(), starters(S)
    rows, n = [], 0
    stop0 = van_pose(S, VAN)[0]
    for name in SQUADS:
        ring = None
        if SQUADS[name][0] and name != G2 + '021_FinancialAlley_Dog':
            stop = stop0
            rx = stop[0] + RING[n][0]
            if DYNAMIC and abs(rx - stop[0]) < VAN_CLEAR:   # not in the van's lane
                rx = stop[0] - VAN_CLEAR - 50.0
            ring = ((rx, stop[2] + RING[n][1]), nav.nearest(stop[0] - VAN_CLEAR - 50.0 if DYNAMIC else stop[0], stop[2])); n += 1
        rows.append(relay(S, name, nav, ring, log, stop0))
    by = collections.defaultdict(list)
    for name, row in zip(SQUADS, rows):
        by[SQUADS[name][0]] += start[row['top']]
    # the boxes. Lists: wave 1 and wave 3 keep stock's (tbExitLoot -> two RandomTrigger and the timer
    # of the other three; tbEscapeAI -> the two squads); wave 2 = the dog's own box, which now also
    # names what stock's tbExitFinancialAlley named (that box is kl_fa_author's entrance box)
    for role, (name, pos, half, _why) in BOXES.items():
        k = au.node_of(sc, name)
        par = sc.parent[k]
        org = trans(S, par) if par else (0.0, 0.0, 0.0)
        au.place(S, k, tuple(pos[i] - org[i] for i in range(3)), None, half, turn=IDENT)
        i = au.ctrl_of(sc, k, 'TriggerBox')
        if role.startswith('wave'):
            w = int(role[-1])
            have = kl_fa.controllers(sc, 'TriggerBox')
            cur = next(v for kk, _i, v in have if kk == k)[17]
            want = cur if w != 2 else by[2]
            if DYNAMIC and w == 1:                      # each squad's first line by name: stock's RandomTriggers pick
                want = [R + n2 + '\\10_RunToCover' for n2, v2 in SQUADS.items() if v2[0] == 1]   # '10_' or '20_', and '20_' is the fall-back now
            if not WAVES:
                want = []
            kl_fa.edit(sc, k, i, lambda us: (au.setv(sc, us, 14, WHO), au.setv(sc, us, 17, want)))
        elif not WAVES:
            kl_fa.edit(sc, k, i, lambda us: au.setv(sc, us, 17, []))
    esc = place_escape(S, log)
    if DYNAMIC:
        # the box before the van: wave 3 is unleashed (F07's spare 'count the players' box; field 15 = 1 there
        # and on tbRunToEscape, the two boxes that feed counters - GUESS that 0 = fire once, as every plain box)
        g = au.place(S, GUARD_BOX, (au.ROAD_X, 300.0, esc['stop'][2] - GUARD_BEFORE), None, (2700.0, 400.0, 300.0), turn=IDENT)
        kl_fa.edit(sc, g, au.ctrl_of(sc, g, 'TriggerBox'), lambda us: (au.setv(sc, us, 14, 'ECPS_FA_MERCONLY'), au.setv(sc, us, 15, 0),
                                                                au.setv(sc, us, 17, [R + x for x in GUARD] if WAVES else [])))
        for name, sec in RUN_CLOCK.items():
            t = au.node_of(sc, name)
            kl_fa.edit(sc, t, au.ctrl_of(sc, t, 'TriggerDelay2'), lambda us, sec=sec: au.setv(sc, us, 0, sec))
    for name, (pos, half, _why) in BOUNDS.items():
        au.place(S, name, pos, None, half, turn=IDENT)
    S.street = {'rows': rows, 'escape': esc}
    log('  kl_fa_street: %d squads (%d actors) on the road in three waves; farthest pull onto the mesh %.0f; '
        'actors pulled in on %d squads; boxes %s; west bound x %d..%d, z %d..%d' % (
            len(rows), sum(r['actors'] for r in rows), max(r['moved'] for r in rows), sum(r['pull'] < 1 for r in rows),
            ', '.join('%s z %d' % (r, v[1][2]) for r, v in BOXES.items()),
            BOUNDS[WEST + 'Bound'][0][0] - BOUNDS[WEST + 'Bound'][1][0], BOUNDS[WEST + 'Bound'][0][0] + BOUNDS[WEST + 'Bound'][1][0],
            BOUNDS[WEST + 'Bound'][0][2] - BOUNDS[WEST + 'Bound'][1][2], BOUNDS[WEST + 'Bound'][0][2] + BOUNDS[WEST + 'Bound'][1][2]))
    return S.street


# ------------------------------------------------------------------ 2. the joined scene
def wire(sc, log=print):
    """After kl_fa_author.wire(sc): the campaign's street squads, which that function starts all
    at the front entrance, are shared out over the waves (CAMPAIGN_WAVE); money triggers answer
    to people only. Reference lists and values of existing controllers."""
    box = lambda name: (au.node_of(sc, name), au.ctrl_of(sc, au.node_of(sc, name), 'TriggerBox'))
    dyn = dyn_pre(sc, log) if DYNAMIC else None
    lists = {k: v[17] for k, _i, v in kl_fa.controllers(sc, 'TriggerBox')}
    door, di = box(au.ROLE['street'])
    stay, go = [], collections.defaultdict(list)
    for p in lists[door]:
        w = next((w for pat, w in CAMPAIGN_WAVE if (R + pat).lower() in (p + '\\').lower()), None) if WAVES else None
        (go[w] if w else stay).append(p)
    if go and POLICE:
        kl_fa.edit(sc, door, di, lambda us: au.setv(sc, us, 17, stay))
        for w, more in go.items():
            k, i = box(BOXES[w][0])
            kl_fa.edit(sc, k, i, lambda us: au.setv(sc, us, 17, lists[k] + [p for p in more if p not in lists[k]]))
    # the van's body is a tracked object like the bank's car: a money trigger that takes anything as
    # its activator hands it to the game rules as an actor (kl2 0x6a8902, run ESC1). kl_fa.repair does
    # this only when the level has a ZHavokCar; the escape here is an animated van whose body parts
    # are tracked the same way (ASSUMPTION), and loot is carried right up to it
    if DYNAMIC:
        dyn_post(sc, dyn, log)
    n = kl_fa.money_people(sc, log)
    log('  kl_fa_street: wired: entrance box starts %d campaign squads, %s; %d money triggers set to people only' % (
        len(stay), ', '.join('%s +%d' % (w, len(v)) for w, v in sorted(go.items())) or 'no campaign squad moved to a wave', n))
    return {'entrance': stay, 'waves': dict(go), 'money': n}


# ------------------------------------------------------------------ the dynamic street: campaign side
def put_world(M, places, log=print):
    """Give nodes of a converted Dead Men level M (kl_graft.DeadMen) WORLD positions: {path: (x, y, z)}.
    A campaign squad's group has a place and often a turn of its own (Squad_RoadBlock_South: 90 degrees) and
    its children are local to it: the local value is the world one in the parent's frame. Read back afterwards."""
    sc, n = M.prp, 0
    def frame(k):
        """World rotation and position of node k, composed down the tree exactly as kl_maps.world does."""
        chain = []
        while k > 0:
            chain.append(k); k = sc.parent[k]
        Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], (0.0, 0.0, 0.0)
        for k in reversed(chain):
            e = M.ents[k - 1]
            r, t = struct.unpack('<9f', e.rot[:36]), struct.unpack('<3f', e.trans[:12])
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[j][i] for j in range(3)] for i in range(3)]
            T = tuple(T[i] + sum(Rm[i][j] * t[j] for j in range(3)) for i in range(3))
            Rm = [[sum(Rm[i][x] * m[x][j] for x in range(3)) for j in range(3)] for i in range(3)]
        return Rm, T
    done = {}
    for path, w in places.items():
        hit = sc.resolve(R + path)
        if not hit:
            continue                                    # a squad that does not stay ('--no-ai')
        k = hit[0]
        Rm, T = frame(sc.parent[k])
        d = [float(w[i]) - T[i] for i in range(3)]
        au.place(M, k, tuple(sum(Rm[j][i] * d[j] for j in range(3)) for i in range(3)))    # the parent's turn undone (transpose)
        done[k] = w
        n += 1
    pos = kl_maps.world(M.scene)
    for k, w in done.items():
        if math.dist(pos[M.ents[k - 1]], w) > 1.0:
            raise ValueError('%s: placed at %s, stands at %s' % (sc.path[k], w, pos[M.ents[k - 1]]))
    log('  kl_fa_street: %s: %d campaign nodes re-placed for the dynamic street' % (M.name, n))
    return n


def dyn_pre(sc, log=print):
    """Before the campaign squads are shared out over the waves: the squads of DYN_START leave the front
    door's list for the elevator box, its timer or the wave 1 box, each started by the rout named there."""
    has = lambda n: bool(sc.resolve(R + n))
    def put(name, ctrl, **f):
        k = au.node_of(sc, name)
        kl_fa.edit(sc, k, au.ctrl_of(sc, k, ctrl), lambda us: [au.setv(sc, us, int(a[1:]), v) for a, v in f.items()])
    tb = {k: v[17] for k, _i, v in kl_fa.controllers(sc, 'TriggerBox')}
    door = au.node_of(sc, au.ROLE['street'])
    squad_of = lambda p: sc.names[sc.top[sc.resolve(p)[0]]] if sc.resolve(p) else None
    stay = [p for p in tb[door] if squad_of(p) not in DYN_START]
    to = collections.defaultdict(list)
    for squad, (role, rout) in DYN_START.items():
        if has(squad + '\\' + rout):
            to[role].append(R + squad + '\\' + rout)
    wave1 = BOXES['wave 1'][0]
    if not (has(wave1) and POLICE and WAVES):           # no wave boxes in this build: with the second pair
        to['timer'] += to.pop('wave 1', [])
    if has(ELEVATOR) and has(ELEV_TIMER):
        v = next(v for k, _i, v in kl_fa.controllers(sc, 'TriggerBox') if k == au.node_of(sc, ELEVATOR))
        if len(v) != 18:
            raise ValueError('%s: not the Dog Days TriggerBox layout (%d fields)' % (ELEVATOR, len(v)))
        put(ELEVATOR, 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', f17=to['elevator'] + [R + ELEV_TIMER])
        put(ELEV_TIMER, 'TriggerDelay', f0=ELEV_DELAY, f4=to['timer'])
    else:                                               # the campaign's box is not in the level: the door, as before
        log('  kl_fa_street: NOT IN THE LEVEL: %s - the forecourt police start at the front door' % ELEVATOR)
        stay += to['elevator'] + to['timer']
    put(au.ROLE['street'], 'TriggerBox', f17=stay)
    if to.get('wave 1'):
        put(wave1, 'TriggerBox', f17=tb[au.node_of(sc, wave1)] + to['wave 1'])
    return to


def dyn_post(sc, to, log=print):
    """After the waves: what holds, what falls back, who fires on the van."""
    has = lambda n: bool(sc.resolve(R + n))
    def put(name, ctrl, **f):
        k = au.node_of(sc, name)
        kl_fa.edit(sc, k, au.ctrl_of(sc, k, ctrl), lambda us: [au.setv(sc, us, int(a[1:]), v) for a, v in f.items()])
    n = collections.Counter()
    front = E1 + 'Squad_InFront'
    if has(front + '\\SquadModifier'):
        # out of the front door: the forecourt police hold tight instead of flanking (their flank rout is
        # now their fall-back, FALL). GUESS: eDM_Tight
        put(front + '\\SquadModifier', 'SquadModifierBehaviour', f9='eDM_Tight', f26=[])
        put(front + '\\Regroup', 'DefendBehaviourRout', f4='eDMS_Run')         # GUESS: they RUN to the car
        door = au.node_of(sc, au.ROLE['street'])
        cur = next(v for k, _i, v in kl_fa.controllers(sc, 'TriggerBox') if k == door)[17]
        put(au.ROLE['street'], 'TriggerBox', f17=cur + [R + front + '\\SquadModifier'])
    south = E2 + 'Squad_SWAT_From_Behind_South'
    if has(south + '\\FlankingBehaviour') and has(south + '\\SquadModifier'):
        put(south + '\\FlankingBehaviour', 'FlankingBehaviourRout', f2=[R + south + '\\SquadModifier'])    # unleashed once in place (GUESS)
    if CHAINS:
        for squad, routs in FALL.items():
            if has(squad):
                put(squad, 'ZSquadScript', **{'f%d' % SQUAD_DEAD: [R + r for r in routs if has(r)]})
                n['chains'] += 1
    log('  kl_fa_street: dynamic street: elevator box starts %d routs, its %d s timer %d, wave 1 + %d campaign; '
        '%d squads send their neighbours back when wiped out%s' % (
            len(to.get('elevator', ())), ELEV_DELAY, len(to.get('timer', ())), len(to.get('wave 1', ())), n['chains'],
            '' if CHAINS else ' (chains off)'))


def hook():
    """Put this layer into kl_fa_author from outside (the three lines of the docstring), once."""
    if getattr(au, '_street', False):
        return
    au._street = True
    au.KEEP = tuple(au.KEEP) + tuple(k for k in (KEEP if POLICE else ()) if k not in au.KEEP)
    if DYNAMIC:                                         # the campaign's elevator box and its timer stay; its squads' points move
        au.CAMPAIGN_KEEP[au.PART_B] = tuple(au.CAMPAIGN_KEEP[au.PART_B]) + tuple(x for x in CAMPAIGN_KEEP_B if x not in au.CAMPAIGN_KEEP[au.PART_B])
        strip0 = au.strip
        def strip2(M, log=print):
            r = strip0(M, log)
            if M.name == au.PART_B:
                put_world(M, DYN_PLACE, log)
                kl_fa_van.clear_props(M, log)
            return r
        au.strip = strip2
    prep, wir = au.prepare_host, au.wire
    def prepare2(S, log=print):
        r = prep(S, log)
        prepare_host(S, log)
        return r
    def wire2(sc, log=print):
        r = wir(sc, log)
        wire(sc, log)
        return r
    au.prepare_host, au.wire = prepare2, wire2


# ------------------------------------------------------------------ reading a built level back
def read(archive):
    sc, _snd, _loc = kl_fa.load(archive)
    with zipfile.ZipFile(archive) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    ents = list(scene.entities())
    pos = kl_maps.world(scene)
    return sc, (lambda k: pos[ents[k - 1]]), Nav.of_archive(archive)


def report(archive, log=print):
    """The street of a built level: waves, escape, bounds, sketch; -> list of faults found."""
    sc, at, nav = read(archive)
    bad = []
    r3 = lambda p: '(%6d %5d %6d)' % tuple(round(v) for v in p)
    def half(k):
        """World half extents of a box: its own are local, and stock boxes are often turned about Y
        (au.rot9: local +Z -> (dx, dz), local +X -> (dz, -dx))."""
        v = kl_fa.node_values(sc, k)
        dx, dz = v[1][0], v[1][2]
        return (abs(dz) * v[8] + abs(dx) * v[10], v[9], abs(dx) * v[8] + abs(dz) * v[10])
    lists ={k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerBox')}
    marks = []                                          # (x, z, char) for the sketch
    reach = nav.walk
    def on(p):
        return nav.floor(p[0], p[2]) is not None
    log('WAVES (trigger boxes south to north; extents are world extents; field 14 = who fires the box)')
    order = [('entrance', au.ROLE['street'])] + [(r, v[0]) for r, v in BOXES.items()]
    if DYNAMIC:
        order = [('elevator', ELEVATOR)] + order + [('van', GUARD_BOX)]
    squad_of = {au.node_of(sc, n): n for n in SQUADS if sc.resolve(R + n)}
    if not squad_of:
        log('  no squad of F07 is in the level (a --no-police build): the entrance box only')
        order = order[:1]
    elif len(squad_of) != len(SQUADS):
        bad.append('%d of %d squads are in the level' % (len(squad_of), len(SQUADS)))
    started = collections.defaultdict(set)
    def follow(path, role, depth=0):
        for j in sc.resolve(path):
            if sc.top[j] in squad_of or any(kl_fa.has(sc, sc.top[j], c) for c in ('ZSquadScript',)):
                started[role].add(sc.top[j])
            elif depth < 4:                             # a timer, counter, gate or random trigger on the way
                for _h, _f, u in J.fields(sc, j):
                    for s in J.strings(sc, u):
                        if s[:5].upper() == R.upper():
                            follow(s, role, depth + 1)
                for c in range(j + 1, sc.end[j]):
                    for _h, _f, u in J.fields(sc, c):
                        for s in J.strings(sc, u):
                            if s[:5].upper() == R.upper():
                                follow(s, role, depth + 1)
    for role, name in order:
        hit = sc.resolve(R + name)
        if not hit:
            bad.append('%s: no %s' % (role, name)); continue
        k = hit[0]
        p, h, v = at(k), half(k), lists[k]
        gone = [s for s in v[17] if not sc.resolve(s)]
        if gone:
            bad.append('%s names %d nodes that are not in the level: %s' % (role, len(gone), gone[0]))
        for s in v[17]:
            follow(s, role)
        log('  %-8s %-46s %s half %s  x %d..%d  z %d..%d  %s %s' % (role, name[-46:], r3(p), tuple(round(x) for x in h), p[0] - h[0], p[0] + h[0],
                                                                      p[2] - h[2], p[2] + h[2], v[14], v[16] if v[16] != 'EFAMPS_ALL_MODES' else ''))
        marks.append((None, p[2] - h[2], '<- %s box, x %d..%d' % (role, p[0] - h[0], p[0] + h[0])))
        for s in v[17]:
            log('             -> %s' % s[5:][-100:])
    log('SQUADS (actors: where they start; cover: the points of their first routs; ring: their place round the van)')
    n = collections.Counter()
    seen_run = started.get('run', set()) | started.get('run 3', set())
    for t in sorted(k for k in range(1, len(sc.nodes)) if sc.parent[k] == 0 and kl_fa.has(sc, k, 'ZSquadScript')):
        name = sc.names[t]
        if not (name in SQUADS or name.startswith('Enemies!')):
            continue
        role = next((r for r, _n in order if t in started[r] and not r.startswith('run')), None)
        acts = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        pts = [k for k in range(t, sc.end[t]) if sc.names[k].startswith(('RunToPosInfo', 'Pos#')) and not sc.names[sc.parent[k]].startswith('40_')]
        esc = [k for k in range(t, sc.end[t]) if sc.names[k].startswith('Pos#') and sc.names[sc.parent[k]].startswith('40_')]
        mine = name in SQUADS
        n['squads', role] += 1; n['actors', role] += len(acts)
        log('  %-8s %-58s %d actors %s' % (role or 'NOBODY', name[-58:], len(acts), ' '.join(r3(at(k)) for k in acts[:4])))
        if mine:
            log('  %8s %-58s cover %s%s' % ('', SQUADS[name][4][:58], ' '.join('(%d %d)' % (at(k)[0], at(k)[2]) for k in pts[:6]),
                                             '   ring (%d %d)%s' % (at(esc[0])[0], at(esc[0])[2], '' if t in seen_run else ' NOT STARTED') if esc else ''))
            off = [sc.path[k][5:] for k in acts + pts + esc if not on(at(k))]
            if off:
                bad.append('%s: %d points are not on the navigation mesh the road is part of: %s at %s' % (name, len(off), off[0], r3(at(sc.resolve(R + off[0])[0]))))
            if role is None and WAVES:
                bad.append('%s is started by no box' % name)
        ch = {'entrance': 'e', 'wave 1': '1', 'wave 2': '2', 'wave 3': '3'}.get(role, '?')
        marks += [(at(k)[0], at(k)[2], ch if mine else ch if ch == 'e' else {'1': 'a', '2': 'b', '3': 'c'}.get(ch, '?')) for k in acts]
        marks += [(at(k)[0], at(k)[2], '+') for k in pts if mine] + [(at(k)[0], at(k)[2], 'o') for k in esc]
    for role, _n in order:
        if n['squads', role]:
            log('  %-8s %2d squads, %2d actors' % (role, n['squads', role], n['actors', role]))
    if DYNAMIC and CHAINS:
        log('FALL-BACK (ZSquadScript field %d of a squad: what is sent when it is wiped out - ASSUMPTION)' % SQUAD_DEAD)
        for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript'):
            if sc.names[k] in FALL:
                gone = [s for s in v[SQUAD_DEAD] if not sc.resolve(s)]
                log('  %-52s -> %s' % (sc.names[k][-52:], ', '.join(s[5:].split('!')[-1] for s in v[SQUAD_DEAD]) or 'NOTHING'))
                if gone or not v[SQUAD_DEAD]:
                    bad.append('%s: its fall-back list names %s' % (sc.names[k], gone[0] if gone else 'nothing'))
    log('  after \'run\': %d squads go to their place round the van (stock timers: 44 s + 18 s after the first criminal, 32 s + 18 s after the third)' % len(seen_run))
    # ---- escape
    log('ESCAPE')
    if kl_fa_van.STRAIGHT:
        bad += ['van: ' + b for b in kl_fa_van.check(archive, log)]
    ex = kl_fa.controllers(sc, kl_fa.EXIT)
    (k, _i, v), = ex
    p, h = at(k), half(k)
    vans = [x for x in v[2:6] if x]
    log('  exit box  %s half %s  z %d..%d  vans listed: %d' % (r3(p), tuple(round(x) for x in h), p[2] - h[2], p[2] + h[2], len(vans)))
    marks.append((None, p[2] - h[2], '<- exit box (calls the van), to z %d' % (p[2] + h[2])))
    for x in vans:
        g = sc.resolve(x)[0]
        t = sc.top[g]
        blk = next(j for j in range(t, sc.end[t]) if sc.names[j] == 'PathBlockerVan')
        van = next(j for j in range(t, sc.end[t]) if sc.names[j] == 'V_Van_00' and 'Reflection' not in sc.path[j])
        brd = next(j for j in range(van, sc.end[van]) if sc.names[j] == 'BoardingTrigger')
        act = next(vv for kk, _i, vv in kl_fa.controllers(sc, 'PlayerAction') if kk == brd)
        veh = next(vv for kk, _i, vv in kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle') if kk == g)
        s, w, b = at(blk), at(van), at(brd)
        d = math.hypot(b[0] - w[0], b[2] - w[2])
        head = ((w[0] - b[0]) / d, (w[2] - b[2]) / d)   # at the waiting place: from the boarding box to the origin
        log('  van       %s waits at %s, stops at %s; drive in %.2f s, waits %.1f s, drive out %.2f s (fields 14..16; the cycle kl2 0x8154f0 adds up: %.2f s)' % (
            sc.names[t][-26:], r3(w), r3(s), veh[14], veh[15], veh[16], veh[14] + veh[15] + veh[16]))
        log('            boarding box (PlayerAction %s, %s, field 12 = %d): half %s, %d behind the van\'s origin; at the waiting place %s' % (
            act[7], act[16], act[12], tuple(round(x) for x in half(brd)), d, r3(b)))
        marks += [(s[0], s[2], 'V'), (w[0], w[2], 'w')]
        if not (p[0] - h[0] <= s[0] <= p[0] + h[0] and p[2] - h[2] <= s[2] <= p[2] + h[2]):
            bad.append('the stop of %s is outside the exit box' % sc.names[t])
        if not on(s):
            bad.append('the stop of %s is not on the navigation mesh' % sc.names[t])
    for kk, _i, vv in kl_fa.controllers(sc, 'OnlineGamePlayTrigger'):
        if vv[0] == 'eOGPT_PLAYER_BOARDS' and sc.path[kk].startswith(R + 'Animation/'):
            named = any(kk in hit for _k, _h, _f, _s, hit in J.references(sc))
            n['boards'] += named
    log('  %d BOARDS triggers are named by a boarding action; money triggers that take anything as activator: %d' % (n['boards'], len(kl_fa.money_triggers(sc))))
    # ---- bounds
    log('BOUNDS (LevelBound; a box is the space a player may NOT be in)')
    for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
        p, h = at(k), half(k)
        if p[1] < -10000 or p[1] > 5000:
            continue
        log('  %-58s x %6d..%6d  z %6d..%6d  y %5d..%5d' % (sc.path[k][5:][-58:], p[0] - h[0], p[0] + h[0], p[2] - h[2], p[2] + h[2], p[1] - h[1], p[1] + h[1]))
        if p[0] + h[0] > -7500 and p[0] - h[0] < 3300:
            marks.append((None, p[2] if h[0] > h[2] else p[2] + h[2], '<- bound %s, x %d..%d%s' % (
                sc.names[k].split('!')[-2][-26:], p[0] - h[0], p[0] + h[0], '' if h[0] > h[2] else ', z %d..%d' % (p[2] - h[2], p[2] + h[2]))))
    sketch(sc, at, nav, reach, marks, log)
    # ---- who of the street would not be drawn (kl_chars.people; re/invisible.md). The owner's first round
    # here had 12 campaign policemen without a body beyond close range: one material without a compiled shader.
    import kl_chars
    rows = [r for r in kl_chars.people(kl_chars.Lv(os.path.dirname(os.path.abspath(archive))))
            if r['cls'] == 'ZFFActor' and r['pos'][1] < 5000]
    lost = [(r, sv, text) for r in rows for sv, text in r['faults'] if sv != 'NOTE']
    log('PEOPLE OF THE STREET: %d actors below y 5000 (%d of the host\'s squads, %d of the campaign\'s), %d with a drawing fault' % (
        len(rows), sum(r['path'].startswith(R + 'Gameplay!') for r in rows), sum(not r['path'].startswith(R + 'Gameplay!') for r in rows),
        len({r['path'] for r, _s, _t in lost})))
    for r, sv, text in lost:
        log('  %s %s (model %d, variant %d): %s' % (sv, r['path'][5:], r['model'], r['variant'], text))
        bad.append('%s %s: %s' % (sv, r['path'][5:], text))
    return bad


def sketch(sc, at, nav, reach, marks, log=print, cx=300, cz=500, xr=(-7500, 3300), zr=(-13000, 14500)):
    """Top-down: x to the right (west .. east), z up (north on top)."""
    grid = {}
    cell = lambda x, z: (int((x - xr[0]) // cx), int((z - zr[0]) // cz))
    for i in reach:
        b = nav.box[i]
        if b is None or not (PLAY[2][0] <= b[4] <= PLAY[2][1]):
            continue
        for gx in range(int((b[0] - xr[0]) // cx), int((b[1] - xr[0]) // cx) + 1):
            for gz in range(int((b[2] - zr[0]) // cz), int((b[3] - zr[0]) // cz) + 1):
                if nav.inside(i, xr[0] + gx * cx + cx / 2, zr[0] + gz * cz + cz / 2):
                    grid[gx, gz] = '.'
    for k in range(1, len(sc.nodes)):                   # a static vehicle's group (in the map tree) stands at the origin;
        if sc.names[k] == 'V_Coli_Hero_01' and sc.names[sc.parent[k]].startswith('Vehicles_static!'):   # its parts have the place
            p = at(k)
            if abs(p[1]) < 200:
                grid[cell(p[0], p[2])] = 'P' if 'Police' in sc.names[sc.parent[k]] else 'c'
    rank = '.cP+o123abce?wV'
    for x, z, ch in marks:
        if x is not None:
            g = cell(x, z)
            if rank.index(ch) >= rank.index(grid.get(g, '.')):
                grid[g] = ch
    lab = collections.defaultdict(list)
    for x, z, text in marks:
        if x is None:
            lab[int((z - zr[0]) // cz)].append(text)
    w = int((xr[1] - xr[0]) // cx)
    log('SKETCH  one cell = %d (x) x %d (z);  . walkable from the road   c static car   P static police car / SWAT vehicle' % (cx, cz))
    log('        1 2 3 actors of F07\'s squads by wave   + their cover points   o their places round the van   e a b c the campaign\'s squads')
    log('        (e entrance, a b c with wave 1 2 3)   w the van waits   V the van stops')
    log('      x %s' % ''.join('%-10d' % (xr[0] + g * cx) for g in range(0, w, 10)))
    for gz in range(int((zr[1] - zr[0]) // cz), -1, -1):
        log('%7d %s  %s' % (zr[0] + gz * cz, ''.join(grid.get((gx, gz), ' ') for gx in range(w)), '; '.join(lab.get(gz, ()))))


# ------------------------------------------------------------------ commands
def stock_squads(log=print):
    S = kl_graft.Level(au.HOST)
    sc, start = S.prp, starters(S)
    pos = kl_maps.world(S.scene)
    at = lambda k: tuple(round(v) for v in pos[S.ents[k - 1]])
    named = collections.defaultdict(list)
    for k, _h, _f, _s, hit in J.references(sc):
        for j in hit:
            if k > 0 and sc.top[k] != sc.top[j]:
                named[j].append(sc.names[sc.top[k]] if sc.parent[k] == 0 else sc.path[k][5:])
    for name in SQUADS:
        t = au.node_of(sc, name)
        v = next(v for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript') if k == t)
        lay = layout(S, t)
        log('%s  at %s  %s / %s / active %d' % (name, at(t), v[0], v[1], v[3]))
        for k, w in lay['actors']:
            a = next(c for c in range(k + 1, sc.end[k]) if sc.cls(c) == 'ZFFActor')
            sol = next(vv for kk, _i, vv in kl_fa.controllers(sc, 'ZSoldier') if kk == a)
            log('    actor  %-24s %s  %s %s %s' % (sc.names[k], tuple(round(x) for x in w), sol[0], sol[3], sol[21]))
        for k in range(t + 1, sc.end[t]):
            ctl = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
            if sc.parent[k] == t and ctl and sc.cls(k) != 'ZFFActor' and not any(sc.cls(c) == 'ZFFActor' for c in range(k + 1, sc.end[k])):
                pts = [at(c) for c in range(k + 1, sc.end[k]) if sc.parent[c] == k]
                log('    rout   %-24s %-26s %s%s' % (sc.names[k], ','.join(ctl), ' '.join('(%d %d %d)' % p for p in pts) if pts else '%s half %s' % (
                    at(k), tuple(round(x) for x in kl_fa.node_values(sc, k)[8:11])) if 'TriggerBox' in ctl else '',
                    '   <- ' + ', '.join(sorted(set(n for n in named[k] if 'merc_bot' not in n))) if named[k] else ''))
        log('    stock start: %s' % ', '.join(p.split('\\')[-1] for p in start[t]))


def plan(log=print):
    """The tables on M09_B's own mesh, without a build: stock F07 with kl_fa_author's and this
    layer's prepare_host, then every squad point and the van against the mesh."""
    S = kl_graft.Level(au.HOST)
    au.prepare_host(S, lambda *_a: None)
    st = prepare_host(S, log)
    nav = nav_b()
    for row in st['rows']:
        name = row['name']
        log('wave %d  %-52s anchor (%d %d)  actors were %.0f m behind their cover%s; farthest pull onto the mesh %.1f m' % (
            SQUADS[name][0], name[-52:], *row['anchor'], row['back'] / 100, ', pulled in to %.0f m' % (MAX_BACK / 100) if row['pull'] < 1 else '', row['moved'] / 100))
        for kind in ('actors', 'cover', 'escape'):
            log('        %-7s %s' % (kind, ' '.join('(%d %d %d)' % tuple(round(v) for v in w) for w in row['at'][kind])))
    e = st['escape']
    log('van: waits at (%d %d %d), stop (%d %d %d), heading there (%.2f %.2f); boarding box centre (%d %d %d): %s of the stop; exit box z %d..%d' % (
        *e['wait'], *e['stop'], *e['head'], *e['board'], 'south' if e['board'][2] < e['stop'][2] else 'north', *e['exit']))
    for i in range(3):
        at, head, board, wait = van_pose(S, i)
        log('  van %d: waits (%d %d), stop (%d %d), heading (%.2f %.2f), boarding (%d %d), floor under the boarding box: %s' % (
            i + 1, wait[0], wait[2], at[0], at[2], *head, board[0], board[2], nav.floor(board[0], board[2])))


def test(out, keep=False, log=print):
    work = os.path.normcase(os.path.abspath(kl_graft.out_dir('F01')))
    dd = os.path.normcase(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(J.level_zip('F02')))))))
    o = os.path.normcase(os.path.abspath(out))
    if o.startswith(dd) or o.startswith(work):
        log('refused: %s is the game\'s folder or the work folder\'s install' % out)
        return 1
    hook()
    r = kl_maps.chain(out, au.HOST, au.PART_B, au.PART_A, campaign=True, heroes=False, keep=True, author=True)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    folder = os.path.join(out, 'R09+%s%s' % (au.PART_A, r['tag']))
    archive = os.path.join(folder, kl_maps.SLOT + '_Main.zip')
    bad = report(archive, log)
    # an empty street on purpose ('--no-ai --no-police') has no squad at all: kl_fa.check's one finding for that is expected
    known = au.KNOWN + (('no ZSquadScript: no police',) if au.NO_AI and not POLICE else ())
    mine = [p for p in r['problems'] if not any(k in p for k in known)]
    fa = [f for f in r['fa_findings'] if f.startswith(('CRASH', 'BROKEN')) and not any(k in f for k in known)]
    log('\nkl_graft.verify: %d problems, %d of them not known' % (len(r['problems']), len(mine)))
    for p in r['problems']:
        log('  %s %s' % ('known ' if p not in mine else 'OPEN  ', p[:230]))
    log('kl_fa.check: %s' % r['fa'])
    for f in r['fa_findings']:
        log('  ' + f[:230])
    log('kl_fa_street: %d faults' % len(bad))
    for b in bad:
        log('  FAULT ' + b[:300])
    log('level: %d entities, %d rooms, %.0f MB; kept in %s' % (r['entities'], r['rooms'], r['archive_mb'], folder if keep else '(removed)'))
    if not keep:
        for d in (folder, os.path.join(out, 'chain', '%s+%s' % (au.HOST, au.PART_B))):
            for f in os.listdir(d):
                if '_Main' in f:
                    os.remove(os.path.join(d, f))
    ok = not mine and not fa and not bad
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


def main():
    global WHO, ONE_VAN, PARK_OTHERS, RIGID, WAVES, POLICE, DYNAMIC, CHAINS
    a = sys.argv[1:]
    if '--merc-only' in a: WHO = 'ECPS_FA_MERCONLY'
    if '--three-vans' in a: ONE_VAN = False
    if '--vans-stay' in a: PARK_OTHERS = False
    if '--rigid' in a: RIGID = True
    if '--no-waves' in a: WAVES = False
    if '--no-police' in a: POLICE = False
    if '--street-classic' in a: DYNAMIC = False
    if '--no-chains' in a: CHAINS = False
    if '--van-bent' in a: kl_fa_van.STRAIGHT = False
    au.NO_AI = '--no-ai' in a
    a = [x for x in a if not x.startswith('--') or x == '--keep']
    if len(a) >= 2 and a[0] == 'test':
        sys.exit(test(a[1], '--keep' in a))
    elif len(a) == 2 and a[0] == 'report':
        bad = report(a[1])
        for b in bad:
            print('FAULT ' + b)
        sys.exit(1 if bad else 0)
    elif a == ['squads']:
        stock_squads()
    elif a == ['plan']:
        plan()
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_street                 # one module: kl_fa_author is imported once, hook() patches that one
    kl_fa_street.main()
