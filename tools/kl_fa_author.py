#!/usr/bin/env python3
"""
The Fragile Alliance layer of Retomoto Tower (Dead Men M09_A + M09_B under Dog Days F07):
authored from stock objects, offline. Spec, evidence and the list of what only a live run can
settle: re/retomoto_fa.md. Nothing here installs anything or starts the game.

    python kl_fa_author.py test <out> [--keep]   build F07 + M09_B + M09_A with the layer into
                                                 <out> (kl_maps.chain), verify, kl_fa.check, print
                                                 the inventory with world coordinates; exit 1 if a
                                                 problem is left that is not in KNOWN
    python kl_fa_author.py plan                  the campaign squads that stay, per part, and why
    python kl_fa_author.py vans                  the three baked van paths fitted to the road
    python kl_fa_author.py inventory <archive>   the inventory of a built level

HOW (no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  Host F07 has its whole Fragile Alliance layer as top-level subtrees: 234 FASpecials!, 32
  Specials!, the escape set-up and three animated vans. kl_graft keeps them when their names are
  in Select(s_keep) (KEEP), exactly as it keeps kl_fa.host_keep's seven. Then
  1. prepare_host(S) - on the stock Level before the graft: positions (.prp ZGEOM[1] / [2] and
     the .gms record, as kl_graft does for Heroes!), box half extents, values. Tables below.
  2. the campaign levels keep, besides what kl_maps.campaign_drop keeps, the squads squad_plan()
     calls self-contained and a few single-node helpers of the campaign itself (CAMPAIGN_KEEP):
     the window bomb, the chair / door swaps, the two elevator door proxies.
  3. wire(Jn) - on the final joined scene, where both parts exist: every reference list that
     names a map node. It only edits values of existing controllers (kl_fa.repair's rule).
  For kl_graft: authoring(log) patches the four entry points from outside (kl_maps does the
  same); the three lines that would make it native are in re/retomoto_fa.md.

GUESS = a value that is not copied from a stock object or measured in the levels. Every table
entry carries its source; what is marked GUESS has to be looked at in the game.
Facts the tables rest on (all read from the files, scripts in re/retomoto_fa.md):
  rotation  ZGEOM[1] = [third column, second column, first column] of the local matrix; a node
            that faces (dx, dz) holds [dx 0 dz, 0 1 0, dz 0 -dx]. Facing = local +Z: ASSUMPTION
            (F07's START points are identity = +z, the way to its loot; M09_A's Jump_02 outside
            the window holds (-1, 0), into the room).
  boxes     ZBoxPrimitive[0..2] are HALF extents (F07 AlleyTop: bound centre + half and warn
            centre + half end on the same plane, 26154.06 / 26153.9).
  hidden    ZGEOM[3] = 1 together with .gms flag 0x400 (F02's eight late money bags, M09_A's
            blown window, broken door and thrown chairs).
"""
import collections, contextlib, glob, math, os, struct, sys, zipfile
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
# 8 heisters in a row 2 m inside the main window (z -990..790). GUESS: the row; the campaign
# proves the floor there (a guard at (5770, 21012, -347), its 'InvisiBomb' at (5685, 20997, -394))
START = [(5650.0, FLOOR3, z) for z in (-700, -500, -300, -100, 100, 300, 500, 700)]
TRAITOR = [(5700.0, FLOOR3, z) for z in (-600, -200, 200, 600)]                      # GUESS
# police who come back: the elevator lobby (campaign 'SquadArrivingElevator', which is not
# kept), the atrium lift, and the square in front of the lobby (campaign 'Squad_InFront')
POLICE = [(1904.0, 19601.0, 818.0), (1800.0, 19601.0, 812.0), (1987.0, 19601.0, 973.0),
          (-1764.0, 19613.0, -61.0), (-1508.0, 19613.0, -147.0), (447.0, 26.0, -7956.0), (-367.0, 26.0, -7594.0)]
STAGE_B = [(3110.0, 21005.0, -1138.0), (2961.0, 21005.0, -990.0), (3033.0, 21004.0, -8.0), (2917.0, 21004.0, -190.0)]   # reception (campaign actors)
STAGE_C = [(2340.0, 19606.0, 1238.0), (2534.0, 19605.0, 883.0), (2604.0, 19605.0, -1063.0), (2485.0, 19605.0, -1555.0)]  # elevator lobby (campaign actors)
STAGE_D = [(3076.0, 162.0, -6354.0), (3100.0, 162.0, -6594.0), (3300.0, 162.0, -6354.0), (3300.0, 162.0, -6594.0)]       # lobby: CP_01 + GUESS
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing)
SPAWN = {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), (1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (-150, 0, 50), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (-150, 0, 50), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (-150, 0, 50), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (0, 0, 80), (1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (START, (-300, 0, 0), IN),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), (1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (120, 0, 0), (-1.0, 0.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (0, 0, -80), (1.0, 0.0))}
# the 15 samurai-armour cases (re/retomoto.md 3.2: the '_Whole' glass of each); the loot stands
# at the case's own origin, i.e. inside the glass. GUESS: that a stack there can be reached
STATUES = [(-2163, 20400, 523), (-73, 20400, 1362), (-109, 20400, -1578), (724, 20400, -808), (-2173, 20400, -705),
           (726, 20400, 606), (726, 21100, 607), (724, 21100, -807), (-110, 21100, -1578), (-2162, 21100, 522),
           (-73, 21100, 1362), (-2172, 21100, -705), (725, 19700, 606), (723, 19700, -808), (-2293, 19700, -131)]
# main room = the boardroom M09_A_Ins_Office_301. Six stacks on the table (chairs stand round
# x 4600..5450, z -290..180). GUESS: the table top is 80 above the floor
MAIN_ROOM = [(x, FLOOR3 + 80.0, z) for x in (4750.0, 5000.0, 5250.0) for z in (-120.0, 20.0)]
STATUE_VALUE, ROOM_VALUE = 150000, 300000   # GUESS: 15 x 150,000 + 6 x 300,000 = 4.05 M (F07's loot: 5 x 800,000)
GATE_MAIN_ROOM = True                   # False: the boardroom loot lies there from the start
BLAST_HARMLESS = True                   # the bomb's two radii set to 1 (the heisters stand at it)
BLAST_DELAY = 1.0                       # GUESS: seconds from the round-start event to the blast

# ------------------------------------------------------------------ the join and the street (M09_B)
CAR_A = (2972.0, 19730.0, 909.0)        # tower escape car SI0101_JPN_Elevator_Int_A_03: box (2756 19600 756)-(3189 19873 1062)
CAR_B = (6272.0, 563.0, -6305.0)        # lobby car ..._Int_A_00, same model and rotation (B - A = 3298, -19040, -7214)
ROAD_X, ROAD_HALF, ROAD_Y = -3000.0, 2400.0, 5.0   # carriageway x -5700..-300 (re/retomoto.md 3.4); y of the static cars
VAN_STOP_Z = (9300.0, 8500.0, 7700.0)   # GUESS: north of the first road block (z 3602..3911), south of the SWAT truck (z 10886)
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put

# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # round start
    'FASpecials!POI!Trigger_POI_TheLootArea': ((5600, 21100, -100), None, (300, 150, 1000), 'GUESS: box round the START row (F07: round its start)'),
    'FASpecials!POI!POI_TheLootArea': ((4600, 21060, -100), None, None, 'GUESS: boardroom centre'),
    'FASpecials!PIP!EnterLootArea': ((5350, 21100, -100), None, (50, 200, 1250), 'GUESS: a plane 3 m in front of the START row'),
    'FASpecials!PIP!ExitLootArea': ((5600, 600, -6500), None, (100, 500, 1650), 'GUESS: across the lobby below the elevator landing'),
    # spawn cameras (camera, look-at)
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((5000, 21500, 600), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((5650, 21050, -100), None, None, 'GUESS'),
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
    'Specials!JumpPoints!01_Start': ((5650, FLOOR3, 0), IN, None, 'the START row'),
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
    'Specials!LevelBound!040_LevelBound_AlleyTop!Bound': ((6650, 20500, -100), None, (650, 2600, 2200), 'GUESS: a slab outside the window, x 6000..7300, 26 m down'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn01': ((6590, 20500, -100), None, (710, 2600, 2200), 'GUESS: from x 5880 (window plane 5850)'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn02': ((6590, 20500, -100), None, (710, 2600, 2200), 'as Warn01'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Bound': ((-7400, 500, 3000), None, (400, 1500, 5000), 'GUESS: west of the road towards the overpass / bus terminal'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn01': ((-7000, 500, 3000), None, (800, 1500, 5000), 'GUESS'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn02': ((-7000, 500, 3000), None, (800, 1500, 5000), 'GUESS'),
}
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft',
                                                         '030_LevelBound_StreetRight') for b in ('Bound', 'Warn01', 'Warn02')]
# host objects that get a new job in wire(): role -> name (each a single top-level node)
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'blast timer': 'Gameplay!010_FirstFight!RivalMercVan!Timer',                 # TriggerDelay2
        'bomb': 'Gameplay!010_FirstFight!RivalMercVan!Activator_VanSound',           # AIDWrapper 'Activate'
        'glass': 'Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo',         # AIDWrapper
        'street': 'Gameplay!030_AfterLoot!tbExitFinancialAlley',                     # TriggerBox ECPS_FA_MERCONLY
        'counter': 'Gameplay!020_Loot!FollowPlayers!TriggerCounter',
        'loot on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT',    # ActivateGeom
        'join box': 'Specials!LevelSpeak!TriggerBox', 'join': 'Specials!JumpPoints!06_Exit', 'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
VANS = ['Animation/F07/F07_Escape_Vehicle_0%d.zip' % i for i in (1, 2, 3)]
KEEP = ('FASpecials!', 'Specials!', 'Gameplay!EscapeSetup!*') + tuple(VANS) + tuple(v for k, v in ROLE.items() if v.startswith('Gameplay!0'))

# ------------------------------------------------------------------ the campaign's own objects that stay
CAMPAIGN_KEEP = {
    PART_A: ('WindowBlowup!BombWindow03',                                           # Explode: particles + the two sounds
             'AI_Players!Enemies!020_Office!GeomActivator_ChairPost', 'AI_Players!Enemies!020_Office!GeomDeactivator_ChairsPre',
             'AI_Players!Enemies!020_Office!GeomActivator_BrokenDoors', 'AI_Players!Enemies!020_Office!GeomDeactivator_Doors',
             'AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator',       # MatPosAnimProxy 0..75 on Ext_A_03 / Int_A_03
             'Music!PlayMusic_TokyoAction'),                                        # the level's action theme, two layers
    PART_B: ('Mercenaries!VideoProxy!MatPosAnimProxy',)}                            # the lobby car's doors, 0..75
# what the blast timer fires besides the two wrappers (all take 'AITrigger')
AT_BLAST = [R + n for n in CAMPAIGN_KEEP[PART_A][1:] + CAMPAIGN_KEEP[PART_B]]
WINDOW_PRE = R + A_MAP + 'M09_A_Ins_Office_301\\SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00'
SQUADS = {PART_A: ('AI_Players!Enemies!020_Office!', 'AI_Players!Enemies!030_Reception!', 'AI_Players!Enemies!040_Atrium_3rd!',
                   'AI_Players!Enemies!050_Atrium_2nd!', 'AI_Players!Enemies!060_Atrium_1st!', 'AI_Players!Enemies!070_Elevators!'),
          PART_B: ('Enemies!010_RetoBldFront!', 'Enemies!020_Street!')}
ROOM_SQUADS = 'AI_Players!Enemies!020_Office!'      # 'everyone in the main room'
# scripted arrivals (elevators, cars) and the guard the campaign kills with the blast
NOT_SQUADS = ('Arriving', 'TakingElevator', 'VSquad', 'Guards_Inside_01')
BEHAVE = {'DefendBehaviourRout', 'FlankingBehaviourRout', 'HuntBehaviourRout', 'PatrolBehaviourRout', 'RunToCoverBehaviourRout'}
PLAIN = BEHAVE | {'ZSquadScript', 'ZSoldier', 'RunToCoverPosInfoRout', 'SquadModifierBehaviour', 'TriggerDelay', 'TriggerCounter', 'TriggerBox'}
# in-game scripted animation of the campaign: removed from a squad that stays (before the join)
STRIP = {'MiniCutsceneRout', 'MiniCutSlot', 'MiniCutPosObject', 'MiniCutSignal', 'MiniCutItemProxy'}
SQUAD_DEAD = 8                          # ZSquadScript field 8: the list sent when the squad is wiped out


# ------------------------------------------------------------------ small tools
def rot9(face):
    dx, dz = face
    n = math.hypot(dx, dz)
    dx, dz = dx / n, dz / n
    return [dx, 0.0, dz, 0.0, 1.0, 0.0, dz, 0.0, -dx]


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


def place(S, name, pos=None, face=None, half=None, hidden=None):
    """Put a node of the Level S somewhere: .prp ZGEOM[1] / [2] and the .gms record (the Dog Days
    loader reads the .prp's; both are kept equal as in stock). Top-level nodes and nodes whose
    parents are identity at the origin only: the values are world values."""
    sc = S.prp
    k = name if isinstance(name, int) else node_of(sc, name)
    lab, e = J.labels('dd', sc.cls(k)), S.ents[k - 1]
    def fn(us):
        if face is not None:
            setv(sc, us, lab.index('ZGEOM[1]'), rot9(face))
        if pos is not None:
            setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
        for i, v in enumerate(half or ()):
            setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
        if hidden is not None:
            setv(sc, us, lab.index('ZGEOM[3]'), int(hidden))
    kl_graft.edit(sc.nodes[k], 'props', fn)
    if face is not None:
        e.rot = struct.pack('<9f', *rot9(face)) + bytes(12)
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
        place(S, grp, t, (dx, dz))
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
            place(S, t, (p[0] + d[0], p[1] + d[1], p[2] + d[2]), face)
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

def plan(level):
    if level not in _plans:
        _plans[level] = squad_plan(level)
    return _plans[level]


def campaign_names(level):
    return tuple(CAMPAIGN_KEEP.get(level, ())) + tuple(plan(level)[0]) if level in SQUADS else ()


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map. sc: the joined scene with both
    parts (kl_prpjoin.Scene). Values and reference lists only."""
    node = lambda n: node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            log('  kl_fa_author: NOT IN THE LEVEL: %s' % gone)
        return [p for p in paths if sc.resolve(p)]
    def lists(role, name, **fields):
        k = node(ROLE[role])
        kl_fa.edit(sc, k, ctrl_of(sc, k, name), lambda us: [setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    squads = {lv: plan(lv)[0] for lv in (PART_A, PART_B)}
    start = {lv: must([p for p, _n, _s in squads[lv].values()]) for lv in squads}
    # round start: AIMonitor list 2 (event 2, kl2 0x8b5f60) -> the blast timer -> everything else
    k = node(ROLE['monitor'])                           # the host's; M09_B's map has an AIMonitor of its own
    have = [s for s in next(v for kk, _i, v in kl_fa.controllers(sc, 'AIMonitor') if kk == k)[2] if sc.resolve(s)]
    lists('monitor', 'AIMonitor', f2=have + [R + ROLE['blast timer']] * (R + ROLE['blast timer'] not in have))
    lists('blast timer', 'TriggerDelay2', f0=BLAST_DELAY, f4=must([R + ROLE['bomb'], R + ROLE['glass']] + AT_BLAST) + start[PART_A])
    lists('bomb', 'AIDWrapper', f0=must([R + 'WindowBlowup!BombWindow03']), f1='Activate')                 # the Explode's own message
    lists('glass', 'AIDWrapper', f0=must([WINDOW_PRE]), f1='ForceTriggerShotActivate')                     # the window's ShotActivate, field 10
    if BLAST_HARMLESS and sc.resolve(R + 'WindowBlowup!BombWindow03'):
        # GUESS: CExplode fields 0 / 1 (600, 400) are its damage radii (the campaign's 'kill the
        # player at the bomb' box has 80, 80). The heisters stand 2 m from this one.
        b = node('WindowBlowup!BombWindow03')
        kl_fa.edit(sc, b, ctrl_of(sc, b, 'Explode'), lambda us: [setv(sc, us, j, 1.0) for j in (0, 1)])
    # the street: its police start when a criminal reaches the front entrance
    lists('street', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=start[PART_B])
    # the join: anybody in the tower car -> JumpPoint in the lobby car ('AITrigger', kl2 0x491e20)
    lists('join box', 'TriggerBox', f14='ECPS_BOTH', f17=[R + ROLE['join'], R + 'Specials!LevelSpeak!OnlineSpeakTrigger_01'])
    # the main room: its squads' 'wiped out' lists -> counter -> ActivateGeom -> the hidden loot
    room = [n for n in squads[PART_A] if n.startswith(ROOM_SQUADS) and sc.resolve(R + n)]
    for n in room:
        k = node(n)
        kl_fa.edit(sc, k, ctrl_of(sc, k, 'ZSquadScript'), lambda us: setv(sc, us, SQUAD_DEAD, [R + ROLE['counter']]))
    hidden = [R + sc.names[t] for t in sc.tops() if sc.names[t].startswith('FASpecials!DropMoney!') and kl_fa.node_values(sc, t)[3]
              and any(v[2] == 'ZMONEYCTRL_TYPE_NORMAL' for kk, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if kk == t)]
    lists('counter', 'TriggerCounter', f0=max(len(room), 1), f4=[R + ROLE['loot on']])
    lists('loot on', 'ActivateGeom', f0='AITrigger', f1=hidden)
    log('  kl_fa_author: wired: %d + %d squads started (tower at the blast, street at the entrance), %d room squads -> counter -> %d hidden stacks' % (
        len(start[PART_A]), len(start[PART_B]), len(room), len(hidden)))
    return {'squads': squads, 'room': room, 'hidden': hidden}


# ------------------------------------------------------------------ from outside kl_graft
@contextlib.contextmanager
def authoring(log=print):
    """kl_graft.build with the layer, without editing kl_graft: Level('F07') comes prepared, the
    Dead Men parts with their kept squads stripped of mini-cutscene controllers, every Select
    keeps KEEP, kl_maps.campaign_drop leaves CAMPAIGN_KEEP and the squads, and kl_fa.repair also
    prunes the kept subtrees and, once both parts are in the scene, runs wire()."""
    real = kl_graft.Level, kl_graft.DeadMen, kl_graft.Select, kl_fa.repair, kl_maps.campaign_drop
    state = {}

    class Host(real[0]):
        def __init__(self, name):
            super().__init__(name)
            if name == HOST:
                state['host'] = prepare_host(self, log)

    class Part(real[1]):
        def __init__(self, name, log=print):
            super().__init__(name, log)
            n = 0
            for t in self.prp.tops():
                if self.prp.names[t] in plan(name)[0]:
                    for k in range(t, self.prp.end[t]):
                        nd = self.prp.nodes[k]
                        keep = [c for c in nd['ctrls'] if self.prp.p.key(c[0]) not in STRIP]
                        n += len(nd['ctrls']) - len(keep)
                        nd['ctrls'] = keep
            log('  kl_fa_author: %s: %d squads stay, %d mini-cutscene controllers taken off them' % (name, len(plan(name)[0]), n))

    class Select(real[2]):
        def __init__(self, geometry=False, m_add=(), m_drop=(), s_keep=(), s_drop=()):
            super().__init__(geometry, m_add, m_drop, tuple(s_keep) + tuple(x for x in KEEP if x not in s_keep), s_drop)

    def repair(sc, kept=(), log=log):
        mine = [n for n in sc.names if sc.resolve(R + n) and sc.parent[sc.resolve(R + n)[0]] == 0 and
                (kl_graft.Select.match(n, KEEP) or n in campaign_names(PART_A) or n in campaign_names(PART_B))]
        r = real[3](sc, tuple(kept) + tuple(mine), log)
        if sc.resolve(R + A_MAP[:-1]) and sc.resolve(R + B_MAP[:-1]):
            state['wired'] = wire(sc, log)
        return r

    def campaign_drop(level):
        names, gone, stay = real[4](level)
        keep = {glob.escape(n) for n in campaign_names(level)}
        return [n for n in names if n not in keep], gone, stay

    kl_graft.Level, kl_graft.DeadMen, kl_graft.Select, kl_fa.repair, kl_maps.campaign_drop = Host, Part, Select, repair, campaign_drop
    try:
        yield state
    finally:
        kl_graft.Level, kl_graft.DeadMen, kl_graft.Select, kl_fa.repair, kl_maps.campaign_drop = real


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
                row(node_of(sc, name), '(%s)' % lv)
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


def test(out, keep=False, log=print):
    """Build the two-part level with the layer into <out>, verify, check, print the inventory."""
    with authoring(log) as state:
        r = kl_maps.chain(out, HOST, PART_B, PART_A, campaign=True, heroes=False, keep=True)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    folder = os.path.join(out, 'R09+%s%s' % (PART_A, r['tag']))
    archive = os.path.join(folder, kl_maps.SLOT + '_Main.zip')
    inventory(archive, log)
    mine = [p for p in r['problems'] if not any(k in p for k in KNOWN)]
    fa = [f for f in r['fa_findings'] if f.startswith(('CRASH', 'BROKEN'))]
    log('\nkl_graft.verify: %d problems, %d of them not KNOWN' % (len(r['problems']), len(mine)))
    for p in r['problems']:
        log('  %s %s' % ('known ' if p not in mine else 'OPEN  ', p[:230]))
    log('kl_fa.check: %s' % r['fa'])
    for f in r['fa_findings']:
        log('  ' + f[:230])
    log('level: %d entities, %d rooms, %.0f MB; first step %s' % (r['entities'], r['rooms'], r['archive_mb'], r.get('first')))
    if not keep:
        for d in (folder, os.path.join(out, 'chain', '%s+%s' % (HOST, PART_B))):
            for f in os.listdir(d):
                if '_Main' in f:
                    os.remove(os.path.join(d, f))
    log('RESULT: %s' % ('PASS' if not mine and not fa else 'FAIL'))
    return 1 if mine or fa else 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        sys.exit(test(a[1], '--keep' in a))
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
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
