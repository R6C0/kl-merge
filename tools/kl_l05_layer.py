"""kl_l05_layer.py - the FRAGILE ALLIANCE ROUND of 'The Flat Raid' (map id DD10): Dog Days' F07 Fragile Alliance systems + Dog Days' OWN campaign
level L05 (the tower block: street, stairwell, flats). OFFLINE ONLY: built and checked, NEVER RUN IN THE GAME.
Design source: re/l05_flat_raid_1025.md. Cut from tools/kl_dig_layer.py (the same author-layer interface, the nine names of kl_graft.AUTHOR_NAMES).

THE ROUND
  1. The crew starts on the STREET at the tower's entrance (8 ground polygons round (12736, 0, -204)); the campaign's squads that stay sleep upstairs.
  2. Round start + 9 s: wave 1 (F07's first police squad) arrives on the 3rd floor, the calm level music (Special!Music!02_APP) starts.
  3. FOUR police waves (F07's own arrival squads, re-placed on L05's navigation mesh; RunToCover / Defend / Flank as the squads' children run them):
       wave 1  round start          3rd floor (y 1200)        wave 2  crew on the 1st floor (y 400)
       wave 3  crew in the flats (y 1600; + the alarm: the van, the action music)         wave 4  the van's alarm + 8 s, 2nd floor (y 800)
     ONE police dog waits on the 1st floor and runs to the street. No extra squads (the actor wall: Dog Days is 32-bit).
  4. Loot: 8 briefcases (the flat, the shop, the TV drawers, the cabinet, the corridor TV, the tower's old TV, the monitor), 1.0 million.
  5. Escape: a van on the street (x 5300 .. 12400, z 1100), the plan of kl_map_escape.van_plan_points without a fault; the layer takes 8 street
     props out of its way (collision cut + hidden: CLEAR_REFS).
  6. The campaign's own Dead Men music groups of L05 stay (Special!Music!*): the start fires the calm one, the alarm the combat one.
  7. Navigation: L05's mesh is in 8 parts; six bridges (NAV_PAIRS, proven by kl_route.Mesh.way) join the floors into one main part.
The campaign's end-of-level scripts, the story triggers that would end the round (C2 / C3 / B2 / B4 / B6) and the roof, vans and extra squads are dropped
(M_DROP). Every number marked GUESS is a guess; MEASURED ones come from the real files (scratch scripts of 2026-10-25, re/open_work_log.md).
Usage (from tools/):
  python kl_l05_layer.py test <out> [--keep] [--plan plan.json] [--no-ai] [--no-police] [--no-music] [--no-dog] [--str PC_Def.str]
  python kl_l05_layer.py check <folder> | finish <folder> | plan <bare-folder> <plan.json> | cover <zip> <out>
"""
import collections, contextlib, math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms
import kl_fa_author as A
import kl_fa_bank as BK
import kl_map_escape as ESC

HOST, LEVEL = 'F07', 'L05'
TITLE = 'The Flat Raid (Tower Block)'
R = 'ROOT\\'
HIDDEN = 0x400
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
KNOWN = ()
NO_AI = False                           # True ('--no-ai'): no police squad is placed or woken
POLICE_ARRIVE = True                    # False ('--no-police')
VOICE = True
STREAM = None
MUSIC = True                            # False ('--no-music')
VAN_HIDE = True
KEEP_FAKETARGET = False
VAN_SHOW = True
DOG_ON = True                           # False ('--no-dog')
SQUADS = collections.OrderedDict()      # the campaign's squads are L05's own (they stay as the level has them, asleep until its triggers): no table here
SQUADS_AWAKE = False
ACTOR_CAP = 55                          # the memory wall (Dog Days is 32-bit; DM05A already exhausts the address space): check() fails over this

# ------------------------------------------------------------------ what of L05 is dropped (kl_graft --m-drop patterns on top-level names)
# BASE (the proven build 'base', 0 dangling): the campaign systems zip, the menu, checkpoints, cutscenes, dialogue, friendly AI, co-op, mission scripts.
D = ('AllLevels/mainsceneincludes.zip', 'MenuResources', 'Checkpoints!*', 'Special!Cutscenes!*', 'Animation/L05/Cutscenes/*', 'AI!Dialogue!*', 'AI!Friendly!*',
     'Coop!*', 'Special!Co-Op!*', 'Extras!MissionRelated!*', 'POI!*')
# T: civilians and the squads outside the raid path (the actor wall), exact names as in the base build
T = ('AI!Civilian!*', 'AI!Enemies!A-Stairways!A1!SQ_Piss', 'AI!Enemies!A-Stairways!A1!SQ_Goons_idle#01', 'AI!Enemies!A-Stairways!A1!SQ_Goons_idel#02',
     'AI!Enemies!A-Stairways!A7!SQ_Airlock_Mobsters_0?', 'AI!Enemies!C-Roof!C2!SQ_sniper_*', 'AI!Enemies!C-Roof!C2!SQ_1Singleguy#0?', 'AI!Enemies!C-Roof!C3!Squad_Henchmen')
# X (GUESS, this layer): the arrival car squad, the roof, the big B6 groups and the story triggers that end or fail the mission
X = ('AI!Enemies!A-Stairways!A1!SQ_Goons_car', 'AI!Enemies!A-Stairways!A9!SQ_Mob_5thFloor_*', 'AI!Enemies!B-Appartments!B2!*',
     'AI!Enemies!B-Appartments!B6!*', 'AI!Enemies!B-Appartments!B6_part2!*', 'AI!Enemies!C-Roof!*', 'AI!Triggers!C2!*', 'AI!Triggers!C3!*', 'AI!Triggers!B2!*', 'AI!Triggers!B6!*',
     'AI!Triggers!B4!*', 'AI!Triggers!B1!*', 'Special!EndOfLevel!*', 'Extras!AlteredVision!*', 'Extras!Xiu_tracker', 'Extras!GeomDeactivator_facetracker')
M_DROP = D + T + X

# ------------------------------------------------------------------ navigation: six bridges between the mesh's parts (MEASURED: kl_route.Mesh.way finds them, 2026-10-25)
# (polygon a, its border edge, polygon b, its border edge); the corners are the edges' own end points, so the bridge is a quad between two borders
NAV_PAIRS = ((927, 0, 993, 2), (436, 2, 452, 2), (449, 1, 447, 3), (332, 2, 314, 1), (340, 0, 322, 1), (1204, 1, 1173, 3))
MAIN_POLY = 927                         # a polygon of the main part (the street's; after the bridges it holds all 896 polygons of 5 floors)
WAY_LEAST = (100.0, 50.0, 0.0)          # Mesh.way's narrowest shared edge, tried in turn (kl_route's own chain; the stairs' doors are 24 wide: MEASURED)


def bridges_of(block, log=lambda *a: None):
    """kl_nav_bridge's list from NAV_PAIRS against a navigation block (kl_fa_bots.Nav's polygons: pv, en)."""
    import kl_fa_bots as F
    nav = F.Nav(block)
    out = []
    for pa, ea, pb, eb in NAV_PAIRS:
        for p, e in ((pa, ea), (pb, eb)):
            if nav.en[p][e] != -1:
                raise ValueError('kl_l05_layer: NAV_PAIRS: polygon %d edge %d is not a border (neighbour %s)' % (p, e, nav.en[p][e]))
        a0, a1 = nav.pv[pa][ea], nav.pv[pa][(ea + 1) % len(nav.pv[pa])]
        b0, b1 = nav.pv[pb][eb], nav.pv[pb][(eb + 1) % len(nav.pv[pb])]
        out.append(dict(corners=[a1, a0, b1, b0], joins={0: ('old', pa, ea), 2: ('old', pb, eb)}))
    return out


def bridged_block(block, log=lambda *a: None):
    import kl_nav_bridge as NB
    new, rep = NB.add_bridges(block, bridges_of(block), log=log)
    return new, rep


_MESH = {}


def bridged_mesh(log=lambda *a: None):
    """The mesh of L05 WITH the six bridges, from the level itself (the same polygons as the built folder's after nav_bridge_step)."""
    import kl_route
    if 'm' not in _MESH:
        lv = kl_route.load(LEVEL)
        new, _rep = bridged_block(lv.scene.nav, log)
        _MESH['m'] = kl_route.Mesh(new)
    return _MESH['m']


def snap_in(mesh, x, z, y=None, margin=30.0, far=300.0, part=None):
    """(x, y, z) ON the navigation mesh nearest to (x, z) (and, when y is given, to the floor y: polygons within 130 of it): the point itself when inside
    a polygon, else moved towards the nearest polygon's middle until it is inside by `margin`. -> (point, how far it was moved). A move over `far` is an
    error (a table that missed the map). Only polygons of the main part count (before 1025b the dig's TEAM_MERC snapped onto an unreachable island)."""
    part = mesh.part[MAIN_POLY] if part is None else part
    d, i = mesh.nearest(float(x), 0.0 if y is None else float(y), float(z), dy=1e9 if y is None else 130.0, part=part)
    if i is None:
        raise ValueError('kl_l05_layer: no navigation polygon near (%d, %s, %d)' % (x, y, z))
    if mesh.inside(i, float(x), float(z)):
        return (float(x), float(mesh.height(i, x, z)), float(z)), 0.0
    mid = mesh.mid[i]
    for s in range(1, 101):
        px, pz = x + (mid[0] - x) * s / 100.0, z + (mid[2] - z) * s / 100.0
        if mesh.inside(i, px, pz) and math.hypot(px - x, pz - z) >= d + margin:
            if math.hypot(px - x, pz - z) > far:
                break
            return (px, float(mesh.height(i, px, pz)), pz), math.hypot(px - x, pz - z)
    raise ValueError('kl_l05_layer: (%d, %d) is %d from the navigation mesh (%d allowed)' % (x, z, d, far))


# ------------------------------------------------------------------ the places. MEASURED = on the (bridged) mesh, main part; GUESS = my choice of area.
# START: 8 ground polygons in front of the tower (the doc's list). MEASURED on the mesh: all on the main part at y 0.
START = [(12321.0, 0.0, -334.0), (12409.0, 0.0, -242.0), (12569.0, 0.0, -321.0), (12750.0, 0.0, -226.0), (12879.0, 0.0, -191.0), (12976.0, 0.0, -274.0),
         (12964.0, 0.0, 3.0), (13021.0, 0.0, -45.0)]
# TRAITOR / TEAM_MERC: grid points inside the street polygons round the START centroid (12736, -204), 400+ from the van's lane. MEASURED (gen1.py, 2026-10-25)
TRAITOR = [(12736.0, 0.0, 97.0), (12511.0, 0.0, -3.0), (12861.0, 0.0, 72.0), (12611.0, 0.0, 72.0)]
TEAM_MERC = [(12611.0, 0.0, -203.0), (12811.0, 0.0, -103.0), (12661.0, 0.0, -103.0), (12736.0, 0.0, -53.0)]
# the respawn stages of team mode: GUESS the areas (street east, 2nd floor corridor, 1st floor east); MEASURED: 2 x 2 squares of the mesh, lane >= 400 (gen4.py)
STAGE_B = [(10860.0, 0.0, 600.0), (10940.0, 0.0, 600.0), (10860.0, 0.0, 680.0), (10940.0, 0.0, 680.0)]
STAGE_C = [(11400.0, 800.0, 1500.0), (11480.0, 800.0, 1500.0), (11400.0, 800.0, 1580.0), (11480.0, 800.0, 1580.0)]
STAGE_D = [(12100.0, 400.0, 440.0), (12180.0, 400.0, 440.0), (12100.0, 400.0, 520.0), (12180.0, 400.0, 520.0)]
# the police who come back after a death: the 3rd floor's west rooms (hidden from every START row, MEASURED by exact casts: gen1.py marks 737 of 737
# upper-floor polygons unseen), 2 .. 3 km of mesh way away. GUESS the area; MEASURED (gen2.py): all on the main part, 125 apart, a mesh way to START.
AFTER_DEATH = [(9450.0, 1200.0, 1172.0), (9745.0, 1200.0, 1444.0), (9518.0, 1200.0, 1045.0), (9900.0, 1200.0, 1375.0), (9896.0, 1200.0, 1770.0),
               (9450.0, 1200.0, 902.0), (9776.0, 1200.0, 1990.0)]
BODIES = [(10050.0, 1600.0, 2564.0), (9488.0, 1600.0, 2143.0), (10084.0, 1600.0, 2755.0), (9639.0, 1600.0, 2086.0), (9796.0, 1600.0, 2035.0),
          (9450.0, 1600.0, 2000.0), (10178.0, 1600.0, 2855.0), (10153.0, 1600.0, 3080.0)]
FACE_NORTH = (0.0, -1.0)                # facing: into the tower (z falls towards the entrance; GUESS)
SOUTH = (0.0, 1.0)
BOARD_AT = (8300.0, 0.0, 1100.0)        # the van's boarding place (MEASURED in the plan; prepare_host takes PLAN['board'] once there is a plan)


def _spawn():
    """ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz) or a place looked at)."""
    board = BOARD_AT
    return {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (30, 0, 20), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (30, 0, 20), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 40), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (TEAM_MERC, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (40, 0, 40), FACE_NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (AFTER_DEATH, (0, 0, 0), board)}


# ------------------------------------------------------------------ the loot: 8 briefcases (where the case's underside lies, degrees, value, what)
# MEASURED: the doc's places (props of the flats) lie on the main part (moved 0), y = the collision floor there (kl_map_escape.Ground.under, gen3.py).
# GUESS: every turn and value (the tower 100,000 x 2, the 3rd floor 100,000, the flats 150,000 x 5 = 1.05 million).
LOOT = [((x, y, z), yaw, value, what) for (x, y, z), yaw, value, what in [
    ((11394.0, 402.6, 150.0), 20.0, 100000, 'tower: the old TV'),
    ((10964.0, 1202.6, 223.0), -35.0, 100000, 'tower: the monitor'),
    ((12295.0, 1602.6, 1566.0), 80.0, 100000, 'flats: the corridor TV'),
    ((10938.0, 1600.8, 2410.0), 5.0, 150000, 'flats: the vase'),
    ((10652.0, 1600.0, 2393.0), 60.0, 150000, 'flats: the shop bag'),
    ((10863.0, 1600.0, 2322.0), -20.0, 150000, 'flats: the shelf'),
    ((12547.0, 1600.0, 3108.0), 100.0, 150000, 'flats: the TV drawers'),
    ((13059.0, 1600.0, 3287.0), 0.0, 150000, 'flats: the cabinet')]]
LOOT_CLEAR = 400.0                      # every case at least this far from every START point (pickup reach is LOOT_REACH + 40)
LOOT_REACH = 125.0                      # TriggerBox2 radius
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, as the dig's

# ------------------------------------------------------------------ the host's layer (F07)
PARK = (0.0, -60000.0, 0.0)
# THE BOUNDS. F07's alley bounds mean nothing here. The inside of Bound / Warn01 / Warn02 (ZBoxPrimitive) is the danger zone. Four groups are re-placed as thin
# slabs round the map, in the world's axes, OUTSIDE the mesh (mesh x 6842 .. 13460, z -355 .. 3962, y 0 .. 1600); two stay parked. GUESS: that the tower's
# own walls hold the crew in the middle; the slabs catch anybody who gets out through a window or the street's ends. check() proves no way/spawn/man is inside.
BOUND_GROUPS = collections.OrderedDict([
    ('030_LevelBound_StreetLeft', dict(c=(4700.0, 700.0, 1800.0), h=(116.0, 1300.0, 2717.0), w=(4823.0, 240.0, 'x'))),     # west: Warn x 4583 .. 5063 (the van starts at 6280)
    ('020_LevelBound_AlleyRight', dict(c=(13900.0, 700.0, 1800.0), h=(116.0, 1300.0, 2717.0), w=(13777.0, 240.0, 'x'))),   # east: Warn x 13537 .. 14017
    ('040_LevelBound_AlleyTop', dict(c=(9300.0, 700.0, -800.0), h=(4800.0, 1300.0, 116.0), w=(-677.0, 240.0, 'z'))),       # north: Warn z -917 .. -437
    ('040_LevelBound_AlleyLeft', dict(c=(9300.0, 700.0, 4400.0), h=(4800.0, 1300.0, 116.0), w=(4277.0, 240.0, 'z')))])     # south: Warn z 4037 .. 4517
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('040_LevelBound_AlleyRight', '030_LevelBound_StreetRight') for b in ('Bound', 'Warn01', 'Warn02')]
ENTER_AT, ENTER_HALF = (11000.0, 800.0, 1500.0), (2700.0, 950.0, 2200.0)          # the whole tower volume: the bots' first stage (START and every loot place inside). GUESS
EXIT_AT, EXIT_HALF = (9300.0, 100.0, 1100.0), (150.0, 200.0, 500.0)               # a plane on the street between the tower and the van, after the last loot. GUESS
WALK_BOX = ((11394.0, 400.0, 150.0), (700.0, 100.0, 500.0))                        # the 1st floor, the tower's room (wave 2). GUESS
FLOOR_BOX = ((12295.0, 1600.0, 1566.0), (500.0, 100.0, 400.0))                     # the flats' corridor (wave 3, the alarm). GUESS
SPAWN_EYE = START[3]
PLACE_FIXED = {
    'FASpecials!POI!Trigger_POI_TheLootArea': (ENTER_AT, None, ENTER_HALF, 'GUESS: the tower (it starts the loot marker\'s timer)'),
    'FASpecials!POI!POI_TheLootArea': ((ENTER_AT[0], ENTER_AT[1] + 80, ENTER_AT[2]), None, None, 'over the tower'),
    'FASpecials!PIP!EnterLootArea': (ENTER_AT, None, ENTER_HALF, 'the tower: AI heisters\' first stage is inside this box'),
    'FASpecials!PIP!ExitLootArea': (EXIT_AT, None, EXIT_HALF, 'GUESS: a plane on the street, after the last loot'),
    'Specials!LevelSpeak!TriggerBox': ((12700.0, 100.0, -150.0), None, (900.0, 200.0, 400.0), 'GUESS: the street at the entrance'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((12700.0, 100.0, -150.0), None, None, 'with its trigger box'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((12000.0, 500.0, -900.0), None, None, 'GUESS: over the street'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((12736.0, 50.0, -204.0), None, None, 'the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((10200.0, 400.0, 100.0), None, None, 'GUESS: the street'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((10900.0, 50.0, 640.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((11000.0, 1100.0, 1000.0), None, None, 'GUESS: the 2nd floor'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((11440.0, 850.0, 1540.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((11600.0, 700.0, 100.0), None, None, 'GUESS: the 1st floor'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((12140.0, 450.0, 480.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((9200.0, 1500.0, 800.0), None, None, 'GUESS: over the 3rd floor, looking at the police rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((9600.0, 1200.0, 1400.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((9200.0, 1500.0, 800.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((9600.0, 1200.0, 1400.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': (STAGE_B[0], None, (250, 150, 250), 'GUESS: the street'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': (STAGE_C[0], None, (300, 150, 250), 'GUESS: the 2nd floor'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': (STAGE_D[0], None, (300, 150, 250), 'GUESS: the 1st floor'),
    'Specials!JumpPoints!01_Start': (START[1], FACE_NORTH, None, 'the street'),
    'Specials!JumpPoints!02_MarketMain': (STAGE_B[0], FACE_NORTH, None, 'the street, east'),
    'Specials!JumpPoints!03_MarketOrange': (STAGE_C[0], FACE_NORTH, None, 'the 2nd floor'),
    'Specials!JumpPoints!04_LootWarehouse': ((10938.0, 1600.0, 2410.0), FACE_NORTH, None, 'the flats'),
    'Specials!JumpPoints!05_MarketGreen': (STAGE_D[0], FACE_NORTH, None, 'the 1st floor'),
}
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'start timer': FF + 'RivalMercs!Timer',                          # TriggerDelay2 START_AT -> wave 1, the dog, the calm music
        'backstop': FF + 'RivalMercVan!Timer',                           # TriggerDelay2 BACKSTOP_AT -> wave 2, the gate, the van, whatever the crew did
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # TriggerBox on the 1st floor -> wave 2
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # TriggerBox in the flats' corridor -> wave 3 (the gate), the alarm
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate',                  # GateGroup + two GatePath
        'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',            # ActivateGeom -> the van's group (the van is hidden until then)
        'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',       # TriggerDelay2 VAN_DELAY -> van on, wave 4, the alarm music
        'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator',   # DeactivateGeom -> the van's group again (round 2)
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
GATE_WAYS = ('Way#01', 'Way#02')
# THE LEVEL'S OWN MUSIC (MEASURED names in the built base): L05's PlayMusic groups stay (they are not in M_DROP); this layer's lists start them.
#   round start  'PlayMusic_APP' (the apartment's calm bed)   the alarm  '03_PlayMusic_Combo' (the final fight's). GUESS: a second PlayMusic does not stop
#   the first; the campaign's own trigger boxes under Special!Music! fade layers by themselves.
MUSIC_AMBIENT, MUSIC_ACTION = 'Special!Music!02_APP!PlayMusic_APP', 'Special!Music!03_FignalFight!03_PlayMusic_Combo'
MUSIC_NAMES = (MUSIC_AMBIENT, MUSIC_ACTION)
START_AT = 9.0                          # s from the round-start event: wave 1, the dog, the music. GUESS (Retomoto: 9 s)
BACKSTOP_AT = 300.0                     # s from the round-start event: waves 2 and 3, the van, whatever the crew did. GUESS
VAN_DELAY = 8.0                         # s from the alarm to the van's show and wave 4. GUESS
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R', 18: 'Multiplayer/F09/MissionReminder_02_R', 19: 'Multiplayer/F06/MissionReminder_01_R',
         20: 'Multiplayer/F06/ReachlootArea_01_R', 127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
         136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
START_KEY = 'AllLevels/Interface/Online/GameStart/L05_%s_Start'
TEXTS = {START_KEY % 'FA': 'Fight up through the tower block. Grab the cases in the flats; the police come in waves. The van waits in the street.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'Fight up through the tower block. Grab the cases in the flats; the police come in waves. The van waits in the street.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}

# ------------------------------------------------------------------ the van in the street (MEASURED plan, zero faults: kl_map_escape.van_plan_points)
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'
STOP = (8300.0, 0.0, 1100.0)
CLEAR_NAMES = ['PC1201_L05_Dustbinbasket_03', 'PC1201_L05_Dustbinbasket_02', 'PC1201_L05_Dustbinbasket_A_01', 'PC1201_L05_Dustbinbasket_01',
               'PC0302_L05_BlackGarbageBag_A_02', 'SO0700_ALL_FenceBlock_A_10', 'SO0700_ALL_FenceBlock_A_11', 'PC0900_ALL_Scaffold_A_01']
# REF ids of those objects' entities (MEASURED on the base build; one name can have several entities). The layer takes them out of the van's way:
# collision cut (kl_escape.cut_collision) and hidden (.gms flag 0x400 + ZGEOM[3]); check() proves both.
# CLEAR_WHAT: REF -> (the last part of the object's scene path, its world position). Hidden (.gms flag 0x400 + ZGEOM[3]) and collision cut (kl_escape.cut_collision).
# WHY a table with names: the first 15 REFs of 1025a / 1025b were stale ids of an older graft (they hid L05's windows, a building, glass emitters and shards, and left the
# van's dustbins standing: check() passed because it only looked at the flags of whatever had those REFs). Now clear_proof() demands name AND place of every REF, in
# finish() and in check(). MEASURED on 1025b (round 2, verifier scripts of 2026-10-25); a REF that no longer fits is a PROBLEM, not a silent miss.
CLEAR_WHAT = collections.OrderedDict([
    # the van's way (CLEAR_NAMES that stand inside the plan's drive x 6280 .. 11800, z 1100; the same-named props of the roofs and flats stay)
    (31224, ('PC1201_L05_Dustbinbasket_03', (8061, 0, 1161))), (31233, ('PC1201_L05_Dustbinbasket_02', (8306, 0, 1161))),
    (31249, ('PC1201_L05_Dustbinbasket_A_01', (8856, 0, 1160))), (31250, ('PC1201_L05_Dustbinbasket_01', (8940, 0, 1160))),
    (26747, ('PC0302_L05_BlackGarbageBag_A_02', (10019, 0, 1115))),
    # the four doors of the two CoopAirlock pairs (TWO-PLAYER ONLY and shut: they gate the only routes to the tower and the flats; a lone FA player and every bot
    # would be walled in). The airlock controllers stay (their clips move nothing once the doors are gone). GUESS: that the controller tolerates it.
    (26690, ('PC0100_L05_Coop_DoubleDoor_Slide_A_Geom_00', (13180, -8, 880))), (26689, ('Coop_DoubleDoor_Slide_A_frame_00', (13175, 124, 880))),
    (22442, ('AirLock_HugeDoor_A_00', (9620, 1192, 1120))), (22441, ('ColiObj_Hero_Block', (9623, 1192, 998))),
    # round 2: the street entrance. The dumpster is exact STATIC collision (a 129 x 138 x 205 box, x 13027 .. 13156) on the mesh way to the entrance; it is a prop
    # (name, no structural role), so it goes. The pillar 26719 / doorway 26718 / hall 27151 pieces are the building's own walls (bbox 600 x 420 x 2800 and so on:
    # LOAD-BEARING, they stay: the doorway between them is open once the airlock doors are gone, MEASURED with a 25 radius body on a 5 grid).
    (26889, ('PC0300_ALL_Dumpster_B_03!_01_BoxMedium_00', (13091, 0, 727))),
    # round 2: invisible CorridorBlockers (campaign script toggles: collision-only boxes the story switches on/off). All three lie ON a route of this round.
    (27152, ('CorridorBlocker', (13350, 139, 996))),                                     # box x 13220 .. 13480, z 845 .. 1155: the whole ground-floor hall behind the entrance
    (27014, ('SO0010_L05_CorridorBlocker_A_01', (9450, 1200, 800))),                    # a wall across the 3rd floor corridor, next to the police spawns (9450, 1200, 902)
    (23991, ('SO0700_ALL_CorridorBlocker_4m_01', (7028, -11, 1076))),                   # x 7022 .. 7035, z 876 .. 1276: right across the street, inside the van's drive (x 6280 ..)
])
CLEAR_REFS = set(CLEAR_WHAT)
COOP_BLOCKERS = 3                       # the CoopAirLock_Pathblocker_00 nodes of the campaign map (MEASURED on 1025a: eBlocking, empty list, named by no controller)
ROAD = dict(arrive=[(5300.0, 0.0, 1100.0), (6300.0, 0.0, 1100.0), (7300.0, 0.0, 1100.0)], stop=STOP,
            leave=[(9300.0, 0.0, 1100.0), (10300.0, 0.0, 1100.0), (12400.0, 0.0, 1100.0)], at='box', heading=90.0, cam=[10450.0, 350.0, 1100.0], clear=list(CLEAR_NAMES))
PLAN = None
NO_PLAN = 'kl_l05_layer: the van has no plan: build with \'kl_l05_layer.py test <out>\' or kl_l05_layer.build()'
LANE_CLEAR = 250.0                      # no spawn point, man, cover point or the marker nearer than this to the van's drive (street floor only). GUESS
BOARD_CLEAR = 500.0                     # no cover point of the police nearer than this to the boarding place
FED_CLEAR = 1000.0                      # no AFTER_DEATH point or police body nearer than this to the boarding place
POLICE_CLEAR = BK.POLICE_CLEAR
CIVILIANS = 0                           # none (the stock FA civilians are a post-step)

# F07's police squads, four waves. name -> (anchor, men, cover, defend) as (x, y, z). MEASURED (gen2.py): every point is the middle of a polygon of the main part
# on the floor named, out of sight of every START / TRAITOR / TEAM_MERC row, a mesh way to START, 110 / 160 apart, 1000+ from the boarding place.
# GUESS: the choice of floor and room per wave.
G30 = 'Gameplay!030_AfterLoot!'
WAVES = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((9756, 1200, 962), [(9756, 1200, 962), (9878, 1200, 874), (9761, 1200, 802)],
                                             [(9784, 1200, 1150), (9518, 1200, 956), (9894, 1200, 605)], (9879, 1200, 1099))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((10532, 400, 188), [(10532, 400, 188), (10405, 400, 286)], [(10749, 400, 156), (10277, 400, 333)], (10450, 400, 75))),
    (G30 + '030_FinancialAlleyExit_Right', ((10938, 1600, 2410), [(10938, 1600, 2410), (11169, 1600, 1920), (10954, 1600, 2606)],
                                              [(10940, 1600, 2488), (11379, 1600, 2987), (10941, 1600, 2658)], (10888, 1600, 2412))),
    (G30 + '030_FinancialAlleyExitStreet_Right', ((12200, 800, 1502), [(12200, 800, 1502), (11801, 800, 1670)], [(12201, 800, 1567), (12111, 800, 1780)], (12187, 800, 1697)))])
WAVE_NAMES = tuple(WAVES)
# ONE POLICE DOG: F07's own squad (ZSquadScript parked, DefendBehaviour + Pos#01, Dog group with the ZFFActor 'eDog'). It waits on the 1st floor (MEASURED: a polygon
# of the main part, hidden from every START row) and runs to the street when the start timer releases it. GUESS: place, release time; UNPROVEN in the game.
DOG = 'Gameplay!020_Loot!021_FinancialAlley_Dog'
DOG_PARK = (10204.0, 400.0, 201.0)
DOG_POST = (12700.0, 0.0, 40.0)         # in front of the START rows (the Defend post: the dog runs here and attacks what it meets). GUESS; snapped onto the mesh
ARRIVE_START = '10_RunToCover'
ARRIVE = collections.OrderedDict()      # filled by lay_police(mesh): name -> (anchor, men, cover, defend), (x, y, z)


def lay_police(mesh, log=print):
    """ARRIVE from WAVES, every place moved onto the navigation mesh (snap_in); the shifts are logged."""
    ARRIVE.clear()
    moved = []
    for name, (anchor, men, cover, defend) in WAVES.items():
        def s(q):
            p, sh = snap_in(mesh, q[0], q[2], q[1])
            if sh > 1.0:
                moved.append(int(sh))
            return p
        ARRIVE[name] = (s(anchor), [s(q) for q in men], [s(q) for q in cover], s(defend))
    log('  kl_l05_layer: %d police places laid on the mesh, %d moved (largest %d)' % (sum(2 + len(v[1]) + len(v[2]) for v in ARRIVE.values()), len(moved), max(moved or [0])))
    return ARRIVE


def _lay_const():
    """ARRIVE with the table's own values until prepare_host lays it on the mesh: names (KEEP) are what is needed before that."""
    if not ARRIVE:
        for name, (anchor, men, cover, defend) in WAVES.items():
            f = lambda q: (float(q[0]), float(q[1]), float(q[2]))
            ARRIVE[name] = (f(anchor), [f(q) for q in men], [f(q) for q in cover], f(defend))
_lay_const()

ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN, DOG) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))


def police():
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def extra():
    return {}                           # none: the actor wall (see ACTOR_CAP)


def __getattr__(name):
    if name == 'KEEP':
        return _KEEP + tuple(x for x in list(police()) if x not in _KEEP)
    raise AttributeError(name)


DROP = ('Specials!CoverPoints!*',)      # L05 brings its own FFCoverList ('CoverList'); a second one is an assert in its init (MEASURED: the base has exactly one)
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout', 'GateGroup', 'GatePath', 'DeactivateGeom', 'Filter'}
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
SQUAD_ACTIVE = A.SQUAD_ACTIVE
MAN_OFF, MAN_IN = 60.0, 15.0
MEN = collections.OrderedDict()


# ------------------------------------------------------------------ 1. the host level before the graft
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT bare F07 + L05 folder. A fault is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_l05_layer: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
    import json
    with open(path, encoding='utf-8') as f:
        P = json.load(f, object_pairs_hook=collections.OrderedDict)
    P = P.get('plan', P)
    lack = [k for k in ('path', 'lin', 'lout', 'wait', 'stop', 'end', 'board', 'cam', 'points') if k not in P]
    if lack or P.get('faults'):
        raise ValueError('%s is no plan of the van without a fault (lacks %s; faults %s)' % (path, lack, P.get('faults')))
    road = {k: [list(map(float, p)) for p in v] if k in ('arrive', 'leave') else list(map(float, v)) if k in ('stop', 'cam') else v for k, v in ROAD.items()}
    if any(P['points'].get(k) != v for k, v in road.items()):
        raise ValueError('%s is a plan of other way points than ROAD: %s' % (path, {k: P['points'].get(k) for k in road if P['points'].get(k) != road[k]}))
    return P


def lay_van(P):
    global PLAN
    PLAN = P
    return P


def van_path():
    return R + VAN + '\\' + VAN_GROUP


def place_now():
    """PLACE_FIXED + the objects that hang on the van's boarding place (the exit box, the escape-area triggers, the marker)."""
    t = collections.OrderedDict(PLACE_FIXED)
    b = PLAN['board'] if PLAN else BOARD_AT
    mark = (b[0], b[1] + 188.0, b[2] + 350.0)                                          # beside the drive, 350 off (the footway). GUESS
    box = ((b[0], b[1] + 200.0, b[2]), None, (450.0, 300.0, 450.0), 'GUESS: round the van\'s boarding place in the street')
    t['Gameplay!EscapeSetup!otrExitLevel'] = box
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    t['FASpecials!POI!POI_TheEscapeArea'] = (mark, None, None, 'beside the boarding place')
    t['Specials!JumpPoints!06_Exit'] = ((b[0], b[1], b[2]), SOUTH, None, 'the boarding place')
    t[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the 1st floor room')
    t[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the flats\' corridor')
    return t


def place_police(S, log=print):
    """F07's police squads of ARRIVE onto the main navigation mesh (kl_fa_club.place_police's way, this file's table). -> [(squad, men)]"""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    up = lambda p: (p[0], p[1] + 1.0, p[2])
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
        at = up(anchor)
        want = {'men': [up(p) for p in men], ARRIVE_START: [up(p) for p in cover], '10_Defend': [up(defend)], '40_RunToEscape': [at]}
        if {k: len(v) for k, v in by.items()} != {k: len(v) for k, v in want.items()}:
            raise ValueError('%s: placed children %s, the table has %s' % (name, {k: len(v) for k, v in by.items()}, {k: len(v) for k, v in want.items()}))
        A.place(S, top, at)
        for kind, ks in by.items():
            for k, p in zip(ks, want[kind]):
                A.place(S, k, tuple(p[a] - at[a] for a in range(3)))
        out.append((name, len(by['men'])))
    if out:
        log('  kl_l05_layer: the police that arrive: %d of F07\'s squads re-placed (%d men) on the navigation mesh' % (len(out), sum(n for _s, n in out)))
    return out


def squad_plan():
    return {}, {'*': 'L05\'s own squads stay as the level has them (M_DROP removes the story ones); the police are F07\'s, re-placed'}


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the tower. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    if PLAN is None:
        raise ValueError(NO_PLAN)
    mesh = bridged_mesh()
    moved = []
    for tbl in (START, TRAITOR, TEAM_MERC, STAGE_B, STAGE_C, STAGE_D, AFTER_DEATH, BODIES):   # on the mesh (the tables hold measured middles; ground rows hold guesses)
        new = []
        for p in tbl:
            q, sh = snap_in(mesh, p[0], p[2], p[1])
            new.append(q)
            if sh > 1.0:
                moved.append(int(sh))
        tbl[:] = new
    log('  kl_l05_layer: spawn tables laid on the mesh: %d points moved (largest %d)' % (len(moved), max(moved or [0])))
    lay_police(mesh, log)
    spawn = _spawn()
    for name, (pos, face, half, _why) in place_now().items():
        put(S, name, pos, face, half)
    # the bounds: four groups as slabs, two parked
    for g, d in BOUND_GROUPS.items():
        base = 'Specials!LevelBound!%s!' % g
        put(S, base + 'Bound', d['c'], None, d['h'])
        wc, wh, ax = d['w']
        wcen = (wc, d['c'][1], d['c'][2]) if ax == 'x' else (d['c'][0], d['c'][1], wc)
        whalf = (wh, d['h'][1], d['h'][2]) if ax == 'x' else (d['h'][0], d['h'][1], wh)
        for w in ('Warn01', 'Warn02'):
            put(S, base + w, wcen, None, whalf)
    for name in PARKED:
        put(S, name, PARK)
    seen = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kind = kl_fa.node_values(sc, t)[8]
            if kind not in spawn:
                raise KeyError('%s: no place for spawn points of kind %s' % (sc.names[t], kind))
            pts, d, face = spawn[kind]
            p = pts[seen[kind] % len(pts)]
            p = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            A.place(S, t, p, turn=facing(p, face))
            seen[kind] += 1
        elif sc.names[t].startswith('Heroes!'):
            crook = sc.names[t].startswith('Heroes!Hero_0')
            pts, face = (START, SOUTH) if crook else (BODIES, BOARD_AT)
            p = pts[seen[crook, 'hero'] % len(pts)]
            A.place(S, t, p, facing(p, face))
            seen[crook, 'hero'] += 1
    log('  kl_l05_layer: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: stacks of F07's drop pools become loot that lies in the map (the club's way); finish() gives them the briefcase
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    take = (sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-8:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[8 - len(LOOT):])[:len(LOOT)]
    if len(take) != len(LOOT):
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
    by = collections.Counter(what.split(':')[0] for _p, _y, _v, what in LOOT)
    log('  kl_l05_layer: loot: %d objects, %d in all: %s' % (len(LOOT), sum(v for _p, _y, v, _w in LOOT), dict(by)))
    place_police(S, log)
    if DOG_ON and not NO_AI:
        dog_host(S, mesh, log)
    S.van = ESC.van_prepare(S, PLAN, log)
    vg = A.node_of(sc, van_path()[len(R):])
    gone = [] if KEEP_FAKETARGET else [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
    for k in gone:
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
    if VAN_HIDE:
        A.place(S, vg, hidden=True)
        log('  kl_l05_layer: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; the alarm shows it' % len(gone))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(place_now()['FASpecials!POI!POI_TheEscapeArea'][0])[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_l05_layer: the escape marker is %d from the van\'s drive (%d wanted)' % (off, LANE_CLEAR))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of the campaign level the campaign pre-pass must leave in (this map is not built with campaign=True: nothing)."""
    return ()


def strip(M, log=print):
    return 0


def dog_host(S, mesh, log=print):
    """F07's stock dog squad re-placed: the Dog group at DOG_PARK, the Defend post at DOG_POST, the release box parked away. Heights from the mesh."""
    sc = S.prp
    bs = chr(92)
    park, _ = snap_in(mesh, DOG_PARK[0], DOG_PARK[2], DOG_PARK[1])
    post, _ = snap_in(mesh, DOG_POST[0], DOG_POST[2], DOG_POST[1])
    for rel, at in ((bs + 'Dog', park), (bs + 'DefendBehaviour' + bs + 'Pos#01', post), ('', (0.0, 0.0, 0.0))):      # the top at the origin: the children hold world places
        A.place(S, A.node_of(sc, DOG + rel), at)
    A.place(S, A.node_of(sc, DOG + bs + 'tbReleaseDog'), PARK)
    log('  kl_l05_layer: the police dog waits at (%d, %d, %d), its Defend post (%d, %d, %d); release box parked' % (*park, *post))


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_l05_layer: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    left = [sc.names[t] for t in sc.tops() if sc.names[t].startswith(('Boundaries!', 'Special!EndOfLevel'))]
    if left:
        raise ValueError('kl_l05_layer: the campaign\'s own bounds / end-of-level are in the build: %s' % left)
    names = list(police())
    arrive = must([R + n + '\\' + ARRIVE_START for n in names])
    wave = {i + 1: arrive[i] for i in range(len(arrive))} if len(arrive) == 4 else {}
    wavex = lambda w: ([wave[w]] if wave else [])
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    put_(sc.resolve(ways[0])[0], 'GatePath', f0=wavex(3))       # wave 3 through the gate, wave 4 through the second path
    put_(sc.resolve(ways[1])[0], 'GatePath', f0=wavex(4))
    tune = [R + MUSIC_AMBIENT] if MUSIC else []
    alarm = must([R + MUSIC_ACTION]) if MUSIC else []
    if MUSIC:
        must(tune)
        for n in MUSIC_NAMES:
            if not kl_fa.has(sc, node(n), 'PlayMusic'):
                raise ValueError('%s is not a PlayMusic' % n)
    dog = [R + DOG + chr(92) + 'DefendBehaviour'] if DOG_ON and not NO_AI else []
    if dog:
        must(dog)
    lists('start timer', 'TriggerDelay2', f0=START_AT, f4=wavex(1) + dog + tune)
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=wavex(2))
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=[R + ROLE['van timer'], ways[0]])
    lists('backstop', 'TriggerDelay2', f0=BACKSTOP_AT, f4=wavex(2) + [ways[0], R + ROLE['van timer']])
    lists('van on', 'ActivateGeom', f0='AITrigger', f1=[van_path()] if VAN_SHOW else [])
    lists('van timer', 'TriggerDelay2', f0=VAN_DELAY, f4=[R + ROLE['van on'], R + ROLE['speak'], ways[1]] + alarm)
    lists('reset hide', 'DeactivateGeom', f0='AITrigger', f1=[van_path()])
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    lists('monitor', 'AIMonitor', f2=[R + ROLE['reset hide']] + have + [R + ROLE['start timer'], R + ROLE['backstop']])
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    if PLAN is None:
        raise ValueError('kl_l05_layer: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_l05_layer: wired: %d police waves; start +%.0f s -> wave 1 + dog + music; 1st floor box -> wave 2; flats box -> wave 3 + the alarm (+%.0f s: '
        'van, exit line, wave 4, action music); backstop %.0f s' % (len(wave), START_AT, VAN_DELAY, BACKSTOP_AT))
    return {'arrive': arrive, 'ways': ways}


def layer_names(sc):
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep))


def complete(sc):
    return True


# ------------------------------------------------------------------ on the written level
def clear_proof(sc, ents, where):
    """Does every REF of CLEAR_WHAT name the object it was measured for (the last part of its scene path, its place within 5 units)? -> [problems]. where(i, e) = the
    world position of entity e (index i)."""
    bad, byref = [], {}
    for i, e in enumerate(ents):
        byref.setdefault(e.ref, []).append(i)
    for ref, (name, at) in CLEAR_WHAT.items():
        ix = byref.get(ref, [])
        if len(ix) != 1:
            bad.append('CLEAR_WHAT REF %d (%s): %d entities carry it, wanted 1' % (ref, name, len(ix)))
            continue
        i = ix[0]
        p = tuple(where(i, ents[i]))
        if not sc.path[i + 1].endswith(name) or math.dist(p, at) > 5.0:
            bad.append('CLEAR_WHAT REF %d is %s at (%d, %d, %d), not %s at %s: the ids moved, re-measure the table' % (ref, sc.path[i + 1][-60:], *p, name, at))
    return bad


def finish(folder, log=print):
    """The written level, in place: the street props out of the van's way, the lightened level, the briefcases on the loot, the texts. -> [problems]"""
    import kl_fa_loot as L, kl_chars as C, kl_light, kl_loc, kl_texmat as T, kl_prmgraph  # noqa
    from kl_port_check import workdir
    E = L.Edit(folder)
    sc, bad = E.sc, []
    # the van's way: the props named in CLEAR_NAMES hidden (their collision was cut in the join: build())
    hid = []
    bad += clear_proof(sc, E.ents, lambda i, e: E.at(i + 1))
    if bad:
        for b in bad:
            log('  PROBLEM: ' + b)
        return bad                       # nothing is hidden on the strength of ids that moved
    for i, e in enumerate(E.ents):
        if e.ref in CLEAR_REFS:
            k = i + 1
            lab = kl_graft.J.labels('dd', sc.cls(k)) if hasattr(kl_graft, 'J') else None
            import kl_prpjoin as J
            lab = J.labels('dd', sc.cls(k))
            kl_graft.edit(sc.nodes[k], 'props', lambda us, lab=lab: A.setv(sc, us, lab.index('ZGEOM[3]'), 1))
            e.flags = e.flags | HIDDEN
            hid.append(k)
    if len(hid) != len(CLEAR_REFS):
        bad.append('the van\'s way: %d of the %d props to clear are in the level' % (len(hid), len(CLEAR_REFS)))
    log('  kl_l05_layer: %d street props hidden (the van\'s way)' % len(hid))
    loot = [k for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    dressed = not {E.ents[k - 1].model for k in loot} <= pool
    if len(loot) != len(LOOT):
        bad.append('%d loot objects in the level, LOOT has %d' % (len(loot), len(LOOT)))
    n0 = len(E.p.chunks)
    L.lighten_first(E, log)
    if CASE and loot and not dressed:
        C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
        root, _box, slots = L.case_model(E, CASE, CASE_SCALE, log)
        lo, _hi = L._assets(E).bounds(root)
        for k in loot:
            at = E.at(k)
            p, yaw, _value, _what = min(LOOT, key=lambda r: math.dist(r[0], at))
            if math.dist(p, at) > 1.0:
                bad.append('%s lies at (%d, %d, %d), which is no place of LOOT' % (sc.names[k], *at))
                continue
            E.put(k, (p[0], p[1] - lo[1], p[2]), L.yaw9(yaw), root)
        if len(E.p.chunks) != n0:
            raise ValueError('the chunk table grew from %d to %d: not enough dead indices' % (n0, len(E.p.chunks)))
        if slots:
            fxc = E.lv['.fxc']
            upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
            if os.path.isfile(upath):
                fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
            fit = kl_light.fit_shaders(E.mat, fxc, slots=slots, log=log)
            E.lv['.fxc'] = fxc
            bad += ['no compiled shader for %s' % v[0] for v in fit['unresolved'].values()]
        log('  kl_l05_layer: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_l05_layer: %s: the loot already shows models of its own: left as it is' % folder)
    langs = 0
    for ext in sorted(E.lv.ext):
        if not ext.lower().endswith('.loc'):
            continue
        kids = kl_loc.parse(E.lv[ext])
        if kids is None:
            continue
        for key, text in TEXTS.items():
            BK.set_text(kids, key, text)
        E.lv[ext] = kl_loc.build(kids)
        langs += 1
    for k, i, _v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, START_KEY % w)]) for f, w in START_FIELDS.items()])
    log('  kl_l05_layer: %d text keys in %d languages; settings fields %s name the start windows' % (len(TEXTS), langs, sorted(START_FIELDS)))
    # the CoopAirLock path blockers, BY NAME (a global strip would also take PathBlockerVan, which must stay): the airlock doors are cleared (CLEAR_REFS), so the
    # blockers that wall the AI off the same passages go inert (eNotBlocking, the vault_noblocker precedent). Nothing names them (checked on 1025a: no controller
    # lists one), so no reference dangles. The kick doors' blockers stay (eUnblock: opened by a kick); check() proves no proven way passes one.
    nb = 0
    for k, i, v in kl_fa.controllers(sc, 'PathBlocker'):
        if 'CoopAirLock_Pathblocker' in sc.path[k] and v[1] != 'eNotBlocking':
            kl_fa.edit(sc, k, i, lambda us: A.setv(sc, us, 1, 'eNotBlocking'))
            nb += 1
    if nb != COOP_BLOCKERS:
        bad.append('%d CoopAirLock path blockers made inert, wanted %d' % (nb, COOP_BLOCKERS))
    log('  kl_l05_layer: %d CoopAirLock path blockers eNotBlocking (PathBlockerVan untouched)' % nb)
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


def nav_bridge_step(folder, log=print):
    """Add the NAV_PAIRS bridges to the navigation mesh of the finished folder (its .gms / .buf only; every other member as it was). -> list of problems.
    After finish, BEFORE bots_step (kl_fa_bots.diff compares the mesh of its source with its result). The model is kl_fa_v2_hotcoffee.nav_bridge_step."""
    import json
    import kl_fa_bots as F
    B = F.Built(folder)
    nav = F.Nav(B.scene.nav)
    if len(nav.pv) < 1000 or nav.part[MAIN_POLY] == nav.part[993]:
        return ['nav bridges: polygon numbering differs from the proven one (%d polygons; 927 and 993 in part %d / %d)' % (len(nav.pv), nav.part[MAIN_POLY], nav.part[993])]
    new, rep = bridged_block(B.scene.nav)
    n2 = F.Nav(new)
    ends = [p for pr in NAV_PAIRS for p in (pr[0], pr[2])]
    if len({n2.part[p] for p in ends}) != 1:
        return ['nav bridges: the mesh is still in islands after the bridges (parts %s)' % [n2.part[p] for p in ends]]
    sizes = sorted(collections.Counter(n2.part).values(), reverse=True)
    B.scene.nav = new
    gms, buf = B.scene.write()
    files = dict(B.files)
    files[B.ext['.gms']], files[B.ext['.buf']] = kl_gms.pack(gms), buf
    kl_graft.write_zip(B.zp, [(n, files[n]) for n in B.order])
    sj = os.path.join(folder, 'steps.json')
    if os.path.isfile(sj):
        st = json.load(open(sj))
        st['navbridge'] = ['.gms', '.buf']
        st['same'] = [e for e in st.get('same', []) if e not in ('.gms', '.buf')]
        st['final'] = kl_maps.member_ids(folder)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(folder, 'graft.txt'), 'a') as f:
        f.write('kl_l05_layer: nav bridges %s (areas %s); mesh parts now %s\n' % (rep['polygons'], rep['areas'], sizes[:4]))
    log('  nav bridges: polygons %s in areas %s; mesh parts by size now %s (was %s)' % (
        rep['polygons'], rep['areas'], sizes[:4], sorted(collections.Counter(nav.part).values(), reverse=True)[:4]))
    return []


# ------------------------------------------------------------------ build and check
@contextlib.contextmanager
def clear_layer(log=print):
    """For the length of the `with`: kl_hvk.join also takes the placements of CLEAR_REFS out (kl_escape.cut_collision). Enter it BEFORE ESC.van_layer, so the van's
    placements are added to the cut collision."""
    import kl_hvk, kl_escape
    saved = kl_hvk.join
    done = []
    def join(*a, **kw):
        h = saved(*a, **kw)
        kl_escape.cut_collision(h, CLEAR_REFS, log)
        done.append(1)
        return h
    kl_hvk.join = join
    try:
        yield done
    finally:
        kl_hvk.join = saved
    if not done:
        raise ValueError('kl_l05_layer: the collision was joined without the cut of CLEAR_REFS')


def build(out, log=print, plan=None):
    """F07 + L05 with the layer into <out>/F07+L05 -> (kl_maps.one's result, that folder, the van's plan, kl_map_escape's report).
    plan None = made here on a BARE graft (no layer; <out>/_bare, deleted again)."""
    import shutil, kl_snd
    name = '%s+%s' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=False, m_drop=M_DROP, prune_dangling=True)
        try:
            if not r.get('ok'):
                raise ValueError('kl_l05_layer: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    kl_snd.VOICE = True if VOICE else None
    try:
        with clear_layer(log):
            with ESC.van_layer(plan, log) as st:
                r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=False, author='kl_l05_layer', m_drop=M_DROP, prune_dangling=True)
    except ValueError:
        if r.get('ok') or not r:
            raise
    finally:
        kl_snd.VOICE = None
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


def van_check(folder, log=print, plan=None):
    L = ESC.Level(folder)
    rep = ESC.van_check(L, log, plan)
    return rep, L, rep['faults']


def bound_boxes(sc, ents):
    """[(name, lo, hi)] world boxes of every LevelBound controller and the boxes it names (Bound, Warn01, Warn02): half extents read as the
    box's own x, y, z (rotated into the world by BK.world_of). Parked boxes (y under -50000) are left out."""
    out = []
    for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
        for j in [k] + [j for lst in v[0:2] for s in lst for j in sc.resolve(s)]:
            T, Rm = BK.world_of(ents[j - 1])
            h = kl_fa.node_values(sc, j)[8:11]
            ext = [sum(abs(Rm[a][b]) * hh for b, hh in enumerate(h)) for a in range(3)]
            if T[1] < -50000.0:
                continue
            out.append((sc.names[j], [T[a] - ext[a] for a in range(3)], [T[a] + ext[a] for a in range(3)]))
    return out


def in_plan_box(p, lo, hi, slack_y=120.0):
    return lo[0] <= p[0] <= hi[0] and lo[2] <= p[2] <= hi[2] and lo[1] - slack_y <= p[1] <= hi[1] + slack_y


def mesh_way(mesh, ia, ib):
    """Mesh.way over WAY_LEAST in turn -> ([points], narrowest) or None."""
    for least in WAY_LEAST:
        w = mesh.way(ia, ib, least)
        if w is not None:
            return w
    return None


def way_proof(mesh, p, boxes, goal=None, mainp=None):
    """The AI's line from the polygon under p to `goal` (default MAIN_POLY), sampled every 25 -> (ok, why, length): ok when it exists, p is on the main part,
    and no sample stands in a box (plan test, 120 slack in y)."""
    goal = MAIN_POLY if goal is None else goal
    d, i = mesh.nearest(p[0], p[1], p[2], dy=130.0, part=mesh.part[goal])
    if i is None or d > 60.0:
        return False, 'not on the main part (%s from it)' % d, 0.0
    w = mesh_way(mesh, i, goal)
    if w is None:
        return False, 'no mesh way from polygon %d to %d' % (i, goal), 0.0
    pts = [tuple(q) for q in w[0]]
    length = 0.0
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / 25.0))
        length += math.dist(a, b)
        for t in range(n + 1):
            q = tuple(a[c] + (b[c] - a[c]) * t / n for c in range(3))
            for name, lo, hi in boxes:
                if in_plan_box(q, lo, hi):
                    return False, 'the way passes (%d, %d, %d) inside %s' % (q[0], q[1], q[2], name), length
    return True, '', length


SIGHT_MASKS = (0x10, 0x20, 0x28)


def seen_from(C, rows, p):
    """(row, mask) of the first row (eye 160 over its feet) with a FREE exact cast (hvk_ray) to the man at p (target 120 / 175 over his feet) under any
    of SIGHT_MASKS, else None."""
    for s in rows:
        e = (s[0], s[1] + 160.0, s[2])
        for dy in (120.0, 175.0):
            seg = (p[0] - e[0], p[1] + dy - e[1], p[2] - e[2])
            for m in SIGHT_MASKS:
                if C.ray(e, seg, m) is None:
                    return s, m
    return None

CAST_MASK = 0x28                        # characters (0x20) or heroes only (0x8): what a player or a bot is stopped by (kl_route's reading of the sub-part flags)
CAST_HEIGHTS = (50.0, 110.0, 170.0)     # a knee, a chest and a HEAD line over the way's floor (round 2: 170 added, so lintels, door frames and ducts are met). GUESS: the same column
                                        # as kl_route (55 .. 165), a little lower to meet low rails; a Glacier character is about 180 tall, the 170 line leaves 10 for the skull
STEP_UP, STEP_DOWN = 35.0, 20.0         # round 2: the floor under a piece's two ends is looked for from STEP_UP over the mesh to STEP_DOWN under it (exact cast, mask CAST_MASK) and the three
                                        # lines are cast over THAT floor: a stair's treads or a kerb stand above or below the mesh's plane, and a line cast over the mesh plane would meet a step
                                        # edge that a body steps over. GUESS: 35 up is what a character climbs without a stair animation (Dog Days' own stairs are 18 per tread)
CAST_SIDE = 25.0                        # each of the three lines (centre, +side, -side) must be free: a body of 2 * CAST_SIDE = 50 fits along the way (the least width wanted)
CAST_STEP = 100.0                       # long segments are cut into pieces this long, so a corner cut is seen where it is
PB_BOX_DY = 100.0                       # kl_route.PB_DY: a path blocker's box counts this far above and below itself


SHIFTS = tuple(range(-120, 121, 20))    # the sideways offsets (units) a body may take from the AI's centre line inside the mesh. GUESS: 1.2 m each side
SCRIPTED_NAMES = ('WoodDoor', 'wooddoor', 'Wall_Break', 'Drawers')
WAY_RETRIES = 12                        # see walk_proof
SHIFT_EDGE = 60.0                       # see cast_way
SHIFT_STEP = 40.0                       # ... and how far the offset may change from one piece of the way to the next (a body turns; 2 steps)


def cast_way(C, mesh, pts):
    """Is there a BODY-WIDE way along the mesh way `pts`? The way is cut into pieces of at most CAST_STEP; a piece is FREE at sideways offset d when its three
    EXACT casts (hvk_ray: centre, +-CAST_SIDE of it, at each of CAST_HEIGHTS, mask CAST_MASK) hit nothing and its two ends and middle stand on the mesh. The
    offset starts at 0 (the place), may change by SHIFT_STEP per piece and must end at 0. A centre line that cuts a corner of a prop is thus not a failure while a
    50-wide way exists beside it; a door shut over the whole passage is.
    GUESS: the offsets are chosen per piece (the small step across a join is not cast); when the centre is free the search keeps only offset 0 (never a false
    pass, a rare false alarm). -> (n casts, [(piece, at, [(object name, REF)...])] of the pieces with no free offset)."""
    pieces = []
    for a, b in zip(pts, pts[1:]):
        dx, dz = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(dx, dz)
        if ln < 1.0:
            continue
        k = max(1, int(math.ceil(ln / CAST_STEP)))
        for j in range(k):
            t0, t1 = j / k, (j + 1) / k
            pieces.append((tuple(a[c] + (b[c] - a[c]) * t0 for c in range(3)), tuple(a[c] + (b[c] - a[c]) * t1 for c in range(3)), -dz / ln, dx / ln))
    n = [0]
    memo = {}
    def free(j, d):
        if (j, d) in memo:
            return memo[j, d]
        p0, p1, px, pz = pieces[j]
        ok, objs = True, []
        for t in (0.0, 0.5, 1.0):
            q = [p0[c] + (p1[c] - p0[c]) * t for c in range(3)]
            # GUESS: the mesh's doors are often narrower than a body (kl_route: down to 16), so a way beside the centre line need not lie ON the mesh,
            # only within SHIFT_EDGE of it (the AI steers by the mesh, the body is stopped by collision alone)
            if d == 0:
                if mesh.on(q[0], q[1], q[2]) is None:
                    ok = False
            else:
                dd, ii = mesh.nearest(q[0] + px * d, q[1], q[2] + pz * d, SHIFT_EDGE + 10.0)
                if ii is None or dd > SHIFT_EDGE:
                    ok = False
        if ok:
            # the floor under the two ends at this offset (STEP_UP / STEP_DOWN: see there); the lines run from floor to floor
            g0, g1 = [C.ray((q[0] + px * d, q[1] + STEP_UP, q[2] + pz * d), (0.0, -(STEP_UP + STEP_DOWN), 0.0), CAST_MASK) for q in (p0, p1)]
            n[0] += 2
            y0 = g0['hit'][1] if g0 else p0[1]
            y1 = g1['hit'][1] if g1 else p1[1]
            for lat in (0.0, CAST_SIDE, -CAST_SIDE):
                for h in CAST_HEIGHTS:
                    o = (p0[0] + px * (d + lat), y0 + h, p0[2] + pz * (d + lat))
                    n[0] += 1
                    r = C.ray(o, (p1[0] - p0[0], y1 - y0, p1[2] - p0[2]), CAST_MASK)
                    if r is not None:
                        ok = False
                        objs.append((r['name'], r['ref']))
                    if not ok and d != 0:
                        break
                if not ok and d != 0:
                    break
        memo[j, d] = (ok, objs)
        return memo[j, d]
    bad = []
    reach = {0}
    for j in range(len(pieces)):
        if 0 in reach and free(j, 0)[0]:
            reach = {0}
            continue
        new = {d for d in SHIFTS if any(abs(d - e) <= SHIFT_STEP for e in reach) and free(j, d)[0]}
        if not new:
            q = pieces[j][0]
            bad.append((j, tuple(round(v) for v in q), sorted(set(free(j, 0)[1]))))
            reach = {0}                         # go on from the centre: one report per blocked piece
        else:
            reach = new
    return n[0], bad


def walk_proof(folder, sc, ents, pos, mesh, C, boxes, log=print):
    """The proven ways (every START to every loot, every loot and START to the boarding place, every police spawn to the first and last START): the AI's mesh
    way, and on it the exact casts of cast_way (a body 2 * CAST_SIDE = 50 wide fits, nothing a character is stopped by lies in the way), and no eBlocking path
    blocker (but the van's) holds a sample. -> ([what is wrong], number of legs). A cut corner of the mesh way is a possible false alarm: each failure names its REF."""
    import kl_route
    bad = []
    def spot(p):
        h = mesh.on(*p)
        if h is not None:
            return h[0]
        d, i = mesh.nearest(p[0], p[1], p[2], 130.0)
        return i if i is not None and d <= 120.0 else None
    kinds = collections.defaultdict(list)
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kinds[kl_fa.node_values(sc, t)[8]].append(tuple(pos[ents[t - 1]]))
    starts = [p for k, v in kinds.items() if k.endswith('_START') for p in v]
    police = [p for k, v in kinds.items() if k.endswith(('_UCC_POLICE', '_TEAM_POLICE')) for p in v]
    loot = [tuple(pos[ents[k - 1]]) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    board = tuple(PLAN['board']) if PLAN else None
    legs = [('START%d -> loot%d' % (i, j), a, b) for i, a in enumerate(starts) for j, b in enumerate(loot)]
    if board:
        legs += [('loot%d -> van' % j, b, board) for j, b in enumerate(loot)] + [('START%d -> van' % i, a, board) for i, a in enumerate(starts)]
    if starts:
        legs += [('police%d -> START%d' % (i, j), a, starts[j]) for i, a in enumerate(police) for j in (0, len(starts) - 1)]
    pbs = [b for b in kl_route.load(folder).path_blockers() or () if b[5] == 'eBlocking' and 'PathBlockerVan' not in b[0]]
    cache, ncast, blocked, pbhit, narrow = {}, 0, collections.Counter(), collections.Counter(), 1e30
    first = {}
    for name, a, b in legs:
        ia, ib = spot(a), spot(b)
        if ia is None or ib is None:
            bad.append('%s: a place is off the mesh' % name)
            continue
        key = (ia, ib)
        if key not in cache:
            # A way is PROVEN when ANY mesh way is body-wide: where a cast says the cheapest one is blocked, the polygon under the blocked piece is banned
            # (its portals made negative) and the next way is cast, up to WAY_RETRIES times; the failure kept is that of the last way. GUESS: banning one
            # polygon per blocked piece finds a detour when there is one (not an exhaustive search: a rare false alarm, never a false pass).
            banned, orig_portal, w, n_all = set(), mesh.portal, None, 0
            def portal(i, j, _o=orig_portal, _b=banned):
                e = _o(i, j)
                return ((-1.0,) + tuple(e[1:])) if (i in _b or j in _b) and i != ia and j != ia and i != ib and j != ib else e
            mesh.portal = portal
            try:
                for _try in range(WAY_RETRIES + 1):
                    w2 = mesh_way(mesh, ia, ib)
                    if w2 is None:
                        break                   # the bans cut every way: the way kept is the last one found
                    w = w2
                    pts = [tuple(q) for q in w[0]]
                    n, hits = cast_way(C, mesh, pts)
                    n_all += n
                    if not hits:
                        break
                    new_ban = set()
                    for _j, at, _objs in hits:
                        hh = mesh.on(*at)
                        if hh is not None:
                            new_ban.add(hh[0])
                    if not (new_ban - banned):
                        break
                    banned |= new_ban
            finally:
                mesh.portal = orig_portal
                del mesh.portal
            if w is None:
                cache[key] = None
            else:
                n = n_all
                pb = set()
                for q0, q1 in zip(pts, pts[1:]):
                    ln = math.dist(q0, q1)
                    for s in range(int(ln // 25.0) + 1):
                        t = s * 25.0 / ln if ln else 0.0
                        x, y, z = (q0[c] + t * (q1[c] - q0[c]) for c in range(3))
                        for path, R, T, half, _m, _st in pbs:
                            d = (x - T[0], y - T[1], z - T[2])
                            loc = [sum(R[i][j] * d[i] for i in range(3)) for j in range(3)]
                            if all(abs(loc[j]) <= half[j] + PB_BOX_DY * abs(R[1][j]) for j in range(3)):
                                pb.add(path)
                cache[key] = (n, hits, pb, w[1])
        got = cache[key]
        if got is None:
            bad.append('%s: no mesh way' % name)
            continue
        ncast += got[0]
        narrow = min(narrow, got[3])
        for _j, at, objs in got[1]:
            for nm, ref in objs or [('(only beside the centre line: off the mesh)', -1)]:
                blocked[(ref, nm)] += 1
                first.setdefault((ref, nm), (name, at, 0, 0))
        for path in got[2]:
            pbhit[path] += 1
            first.setdefault(('pb', path), (name, None, None, None))
    for (ref, nm), c in blocked.most_common():
        nme, at, lat, h = first[(ref, nm)]
        bad.append('no body-wide way along %s: REF %s %s stands across it near %s: %d legs' % (nme, ref, nm[-40:], at, c))
    for path, c in pbhit.most_common():
        bad.append('the way %s passes the eBlocking path blocker %s: %d legs' % (first[('pb', path)][0], path[-60:], c))
    log('  casts: %d legs (%d distinct mesh ways), %d exact casts (%d heights x centre / +-%d), mask %#x: %d distinct blocking objects, %d path blockers in the way; narrowest mesh door %s' % (
        len(legs), len(cache), ncast, len(CAST_HEIGHTS), CAST_SIDE, CAST_MASK, len(blocked), len(pbhit), 'n/a' if narrow > 1e29 else round(narrow)))
    return bad, len(legs)


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (finished, bridged) folder -> [what is wrong]. PROVES: every spawn / loot / escape point stands on the main mesh part and
    is reachable (mesh ways), the police's ways stay out of every Bound / Warn box, no policeman is in sight of a START / TRAITOR / TEAM_MERC row, one
    OnlineEscVehicleMonitor, one cover list, at most ACTOR_CAP actors, the street props are out of the van's way."""
    import json, kl_route, kl_arms, kl_hvk
    arch = BK.archive_of(folder)
    sc, scene, ents, pos, hvk, snd, loc, size = BK.read_built(folder)
    bad = []
    def fail(s):
        bad.append(s); log('  FAIL: ' + s)
    res = json.load(open(os.path.join(folder, 'result.json'))) if os.path.isfile(os.path.join(folder, 'result.json')) else {}
    if problems is None:
        problems = res.get('problems')
    if res.get('dangling'):
        fail('the build left %d dangling scene paths: %s' % (len(res['dangling']), res['dangling'][:3]))
    for p in problems or ():
        why = next((w for t, w in KNOWN if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    listed, lost, have = BK.lost_clips(folder, res)
    if listed:
        log('  sound: of the %d clip names result.json lists, %d have a streamed record in the built .WHD; %d have NO record (music / ambience: silent):%s' % (
            len(listed), len(listed) - len(lost), len(lost), ''.join('\n          ' + n for n in lost)))
    for f in kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch)):
        why = next((w for t, w in KNOWN if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
        log('  kl_fa: %s%s' % (str(f)[:230], '\n          = known: %s' % why if why else ''))
        if f.sev <= kl_fa.BROKEN and not why:
            fail('kl_fa.check: ' + str(f)[:200])
    ncov = len(kl_fa.controllers(sc, 'FFCoverList'))
    log('  cover lists (FFCoverList): %d' % ncov)
    if ncov != 1:
        fail('%d cover lists (a level needs exactly one)' % ncov)
    nmon = len(kl_fa.controllers(sc, 'OnlineEscVehicleMonitor'))
    log('  OnlineEscVehicleMonitor: %d' % nmon)
    if nmon != 1:
        fail('%d OnlineEscVehicleMonitor (each Init deletes the one before: exactly one)' % nmon)
    if any(sc.names[t].startswith(('Boundaries!', 'Special!EndOfLevel')) or 'LevelBound_StairsBottom' in sc.names[t] for t in sc.tops()):
        fail('the campaign\'s own bound / end-of-level objects are in the level (M_DROP)')
    # ---- the mesh of the built folder (with the bridges): one main part
    mesh = kl_route.Mesh(scene.nav)
    mainp = mesh.part[MAIN_POLY]
    log('  mesh: %d polygons, main part %d polygons (part %d)' % (len(mesh.pv), mesh.size[mainp] if hasattr(mesh.size, '__getitem__') else -1, mainp))
    if any(mesh.part[p] != mainp for pr in NAV_PAIRS for p in (pr[0], pr[2])):
        fail('the bridges did not join the mesh into one main part (run nav_bridge_step)')
    def part_of(p):
        h = mesh.on(*p)
        if h is not None:
            return mesh.part[h[0]]
        d, i = mesh.nearest(p[0], p[1], p[2], 130.0)
        return mesh.part[i] if i is not None and d <= 60.0 else None
    # ---- the street props out of the van's way
    refs = {e.ref: e for e in ents}
    for x in clear_proof(sc, ents, lambda i, e: pos[e]):
        fail(x)
    miss = sorted(CLEAR_REFS - set(refs))
    if miss:
        fail('the street props to clear: REF %s are not in the level' % miss)
    shown = sorted(r for r in CLEAR_REFS if r in refs and not refs[r].flags & HIDDEN)
    if shown:
        fail('the street props to clear are not hidden: REF %s' % shown)
    cut = sorted({kl_hvk.ref(i) for s in hvk.shapes for i in s.inst} & CLEAR_REFS)
    if cut:
        fail('the street props to clear still have collision: REF %s' % cut)
    log('  van\'s way: %d props hidden, collision cut (%d REF still in the .HVK)' % (len(CLEAR_REFS) - len(shown) - len(miss), len(cut)))
    # ---- the loot: the values, each on the mesh and reachable from START
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    if len(loot) != len(LOOT) or sorted(v[1] for _k, v in loot) != sorted(w for _p, _y, w, _x in LOOT):
        fail('loot: %d objects with values %s, expected %d with %s' % (len(loot), sorted(v[1] for _k, v in loot)[:3], len(LOOT), sorted(w for _p, _y, w, _x in LOOT)[:3]))
    log('  loot: %d objects, %d in all' % (len(loot), sum(v[1] for _k, v in loot)))
    boxes = bound_boxes(sc, ents)
    log('  level bounds: %d boxes' % len(boxes))
    if len(boxes) != 3 * len(BOUND_GROUPS):
        fail('%d bound boxes, expected %d (the parked ones count 0)' % (len(boxes), 3 * len(BOUND_GROUPS)))
    for k, v in loot:
        p = pos[ents[k - 1]]
        near = mesh.nearest(p[0], p[1] - 0.0, p[2], 130.0)
        if near[1] is None or near[0] > 120.0:
            fail('loot %s at (%d, %d, %d) is %s from the navigation mesh' % (sc.names[k], *p, near[0]))
            continue
        if part_of(p) != mainp:
            fail('loot %s at (%d, %d, %d) is not on the main mesh part' % (sc.names[k], *p))
        ok, why, ln = way_proof(mesh, p, boxes)
        if not ok:
            fail('loot %s at (%d, %d, %d): %s' % (sc.names[k], *p, why))
        for name, lo, hi in boxes:
            if in_plan_box((p[0], p[1] + 50.0, p[2]), lo, hi, 0.0):
                fail('loot %s stands inside %s' % (sc.names[k], name))
    # ---- spawn points and men
    drive = ESC.Poly([tuple(p) for p in PLAN['path']]) if PLAN else None
    kinds = collections.Counter()
    nway, longest = 0, 0.0
    for t in sc.tops():
        if sc.cls(t) != 'ZSpawnPoint':
            continue
        kind = kl_fa.node_values(sc, t)[8]
        p = pos[ents[t - 1]]
        kinds[kind] += 1
        if part_of(p) != mainp:
            fail('spawn point %s (%s) at (%d, %d, %d) is not on the main mesh part' % (sc.names[t], kind[-12:], *p))
        for name, lo, hi in boxes:
            if in_plan_box((p[0], p[1] + 50.0, p[2]), lo, hi, 0.0):
                fail('spawn point %s (%s) at (%d, %d, %d) stands inside %s' % (sc.names[t], kind[-12:], *p, name))
        if 'AFTER_DEATH' in kind and PLAN and math.dist(p, PLAN['board']) < FED_CLEAR:
            fail('spawn point %s (AFTER_DEATH) is %d from the boarding place (%d wanted)' % (sc.names[t], math.dist(p, PLAN['board']), FED_CLEAR))
        if drive is not None and 'START' in kind and abs(p[1]) < 300.0 and abs(drive.project(p)[1]) < LANE_CLEAR:
            fail('spawn point %s is %d from the van\'s drive' % (sc.names[t], abs(drive.project(p)[1])))
        ok, why, ln = way_proof(mesh, p, boxes)          # every spawn point: a way to the main polygon that keeps out of the bounds
        nway += 1
        longest = max(longest, ln)
        if not ok:
            fail('spawn point %s (%s) at (%d, %d, %d): %s' % (sc.names[t], kind[-12:], *p, why))
    log('  spawn points by kind: %s' % {k.replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in kinds.items()})
    log('  spawn points: %d mesh ways to polygon %d, none enters a bound or warn box (longest %d)' % (nway, MAIN_POLY, longest))
    starts = [pos[ents[t - 1]] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and 'START' in kl_fa.node_values(sc, t)[8]]
    if starts and loot:
        near = min((math.dist(pos[ents[k - 1]], q), sc.names[k]) for k, _v in loot for q in starts)
        log('  loot to START: nearest pair %d apart (%s; %d wanted)' % (near[0], near[1], LOOT_CLEAR))
        for k, _v in loot:
            d = min(math.dist(pos[ents[k - 1]], q) for q in starts)
            if d < LOOT_CLEAR:
                fail('loot %s is %d from a START point (%d wanted: a crew at spawn would drain it)' % (sc.names[k], d, LOOT_CLEAR))
    men = [k for k in range(1, len(sc.names)) if sc.cls(k) == 'ZFFActor']
    squads = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript')]
    police_men = [k for k in men if sc.path[k][len(R):].startswith(('Gameplay!', 'merc_bot_squad'))]
    log('  actors: %d (police + dog %d, campaign %d), squads: %d (F07 police squads %d; cap %d actors)' % (
        len(men), len(police_men), len(men) - len(police_men), len(squads), len(police()), ACTOR_CAP))
    if len(men) > ACTOR_CAP:
        fail('%d actors, at most %d (the memory wall)' % (len(men), ACTOR_CAP))
    off = 0
    for k in men:
        g = sc.parent[k]
        p = pos[ents[g - 1]]
        if mesh.on(*p) is None and (mesh.nearest(p[0], p[1], p[2], 130.0)[0] or 1e9) > MAN_OFF:
            off += 1
            fail('man %s at (%d, %d, %d) is %s off the navigation mesh' % (sc.path[k], *p, mesh.nearest(p[0], p[1], p[2], 130.0)[0]))
        if drive is not None and sc.path[k][len(R):].startswith(G30) and abs(p[1]) < 300.0 and abs(drive.project(p)[1]) < LANE_CLEAR:
            fail('policeman %s is %d from the van\'s drive' % (sc.path[k], abs(drive.project(p)[1])))
    log('  men off the mesh: %d' % off)
    # ---- police cover points / posts: out of the bounds and the boarding place
    nplace = 0
    if PLAN:
        for name, (anchor, mn, cover, defend) in police().items():
            for q in cover:
                nplace += 1
                if math.dist(q, PLAN['board']) < BOARD_CLEAR:
                    fail('%s: a cover point %d from the boarding place (%d wanted)' % (name.split('!')[-1], math.dist(q, PLAN['board']), BOARD_CLEAR))
    # ---- sight: no policeman / dog in view of a START / TRAITOR / TEAM_MERC row (exact casts)
    rows = [pos[ents[t - 1]] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and kl_fa.node_values(sc, t)[8].endswith(('_START', 'TEAM_MERC', '_TRAITOR'))]
    C = None
    try:
        sp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'third_party', 'anp', 'scripts')
        if sp not in sys.path:
            sys.path.insert(0, sp)
        import hvk_ray
        C = hvk_ray.Collision(arch)
    except Exception as e:
        fail('sight test: cannot load hvk_ray / collision (%s)' % e)
    nseen = ntest = nasleep = 0
    for k in men:
        if 'merc_bot_squad' in sc.path[k]:
            continue
        p = pos[ents[sc.parent[k] - 1]]
        ntest += 1
        for name, lo, hi in boxes:
            if in_plan_box((p[0], p[1] + 50.0, p[2]), lo, hi, 0.0):
                fail('man %s at (%d, %d, %d) stands inside %s' % (sc.path[k], *p, name))
        sn = seen_from(C, rows, p) if C else None
        if sn:
            nseen += 1
            fail('man %s at (%d, %d, %d) is in sight of the spawn row (%d, %d, %d), mask %#x, %.1f m' % (sc.path[k][-40:], *p, *sn[0], sn[1], math.dist(sn[0], p) / 100))
    log('  sight: %d policemen / dogs / guards from %d START / TEAM_MERC / TRAITOR places, exact casts masks %s: %d in sight' % (ntest, len(rows), '/'.join('%#x' % m for m in SIGHT_MASKS), nseen))
    # ---- the exit and the van
    ex = [(k, v) for k, _i, v in kl_fa.controllers(sc, kl_fa.EXIT)]
    if len(ex) != 1 or ex[0][1][2] != van_path():
        fail('the exit trigger: %s, wanted one naming %s' % ([v[2:5] for _k, v in ex], van_path()))
    if PLAN:
        b = PLAN['board']
        bp = part_of(tuple(b))
        log('  van: boarding place (%d, %d, %d) on mesh part %s (main %s); stop %s; exit box %d from it' % (*b, bp, mainp, [round(x) for x in PLAN['stop']], math.dist(pos[ents[ex[0][0] - 1]], b) if ex else -1))
        if bp != mainp:
            fail('the boarding place is not on the main mesh part (%s)' % bp)
        s0 = mesh.nearest(starts[0][0], starts[0][1], starts[0][2], 130.0)[1] if starts else None
        bi = mesh.nearest(b[0], b[1], b[2], 130.0)[1]
        if s0 is not None and bi is not None:
            w = mesh_way(mesh, s0, bi)
            if w is None:
                fail('no mesh way from the START rows to the boarding place')
            else:
                log('  escape: mesh way START -> boarding place, %d long, narrowest door %d' % (sum(math.dist(a_, b_) for a_, b_ in zip(w[0], w[0][1:])), w[1]))
        for t in sc.tops():
            if sc.cls(t) == 'ZSpawnPoint' and 'START' in kl_fa.node_values(sc, t)[8] and math.dist(pos[ents[t - 1]], b) < 1500:
                fail('a START spawn point is %d from the boarding place' % math.dist(pos[ents[t - 1]], b))
    # ---- the proven ways, cast against the exact collision (a body 50 wide), and the path blockers
    if C is None:
        fail('walk proof: no collision (hvk_ray)')
    else:
        wbad, _nlegs = walk_proof(folder, sc, ents, pos, mesh, C, boxes, log)
        for x in wbad:
            if any(k in x for k in SCRIPTED_NAMES):
                # GUESS (by name only): a door a player opens, a wall the level breaks, a drawer chest that is keyframed (moves when pushed). The cast
                # meets the closed/intact form; whether the player passes it is NOT proven offline -> a NOTE, not a FAIL.
                log('  NOTE: walk proof (openable / breakable / movable by name, unproven): ' + x)
                continue
            fail('walk proof: ' + x)
    return bad


def flags_of():
    return collections.OrderedDict(SQUADS_AWAKE=SQUADS_AWAKE, NO_AI=NO_AI, POLICE_ARRIVE=POLICE_ARRIVE, START_AT=START_AT, BACKSTOP_AT=BACKSTOP_AT, VAN_DELAY=VAN_DELAY)


BOT_OPT = {'stops': 4, 'cases': 'off', 'lane': True, 'window': True, 'loot_seconds': 20, 'park': (8414.0, 0.0, 969.0)}   # GUESS: the street mesh near the van is a strip; 131 off its line is the widest place
# GUESS (the dig's): briefcases only, up to 4 stops, a loot wait of 20 s; the plan puts the van's AllyEscapeBox PARK_SIDE from the key-framed van line.


def bots_step(folder, log=print):
    """kl_fa_bots.build with BOT_OPT, then kl_fa_bots_dyn.build, each into a copy, the result copied over the folder's own files.
    -> list of problems. Run it AFTER finish + nav_bridge_step and before check. NOT LOADED LIVE."""
    import shutil
    import kl_fa_bots as F, kl_fa_bots_dyn as D
    probs = []
    cur = folder
    for name, run in (('bots', lambda s, d: F.build(s, d, dict(BOT_OPT), log)), ('dyn', lambda s, d: D.build(s, d, None, log))):
        tmp = folder.rstrip('/' + chr(92)) + '_' + name + '_tmp'
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        try:
            res = run(cur, tmp)
        except ValueError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            return probs + ['%s: %s' % (name, e)]
        out = res[0] if isinstance(res, tuple) else res
        probs += ['%s: %s' % (name, x[1] if isinstance(x, (list, tuple)) else x) for x in (out or ()) if (x[0] if isinstance(x, (list, tuple)) else 'FAIL') == 'FAIL']
        for f in os.listdir(tmp):
            shutil.copy2(os.path.join(tmp, f), os.path.join(folder, f))
        shutil.rmtree(tmp, ignore_errors=True)
    lane = [x for x in probs if 'IN ITS LANE' in x]
    if lane:
        # KNOWN: the street's mesh round the van is a strip about 150 either side of its line (MEASURED, 24 polygons beyond 250 in x 6800..10500), so
        # bots on the way out stand in the van's lane whatever the plan; the van's own KillBox/AllyEscapeBox is unchanged. Reported, not failed.
        log('  KNOWN (bots): %d places of the way out lie in the lane of the van: the street mesh there is a strip' % len(lane))
        probs = [x for x in probs if x not in lane]
    return probs


def test(out, keep=False, log=print, plan=None):
    """Build the level with the layer into <out>, finish it, bridge it, check it. -> 0 or 1. Beside the archive: van.json."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    late += nav_bridge_step(folder, log)
    if not NO_AI:
        late += bots_step(folder, log)
    vrep = van_check(folder, lambda *a: None, plan)[0]
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], flags=flags_of(), check=vrep), f, indent=1, default=str)
    for x in late:
        log('  LATE PROBLEM: %s' % x)
    bad = check(folder, log, r['problems']) + late
    log('level: %d entities, %d rooms, %.0f MB' % (r['entities'], r['rooms'], r['archive_mb']))
    if not keep:
        for f in os.listdir(folder):
            if '_Main' in f:
                os.remove(os.path.join(folder, f))
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


COVER_Y = 300.0                         # the street only (the tower and the flats have the level's own cover)
COVER_MAX = 12


def cover_step(zp, dst, max_new=COVER_MAX, log=print):
    """POST-STEP on the finished F01_Main.zip: up to 12 more cover boxes (tools/kl_cover_add.py) on the street (floor y under COVER_Y) only; no car copies."""
    import kl_cover_add as CA
    zp, dst = os.path.normpath(zp), os.path.normpath(dst)
    real = CA.Lite.__init__
    def lite(self, zp_):
        real(self, zp_)
        for i in range(len(self.nav.pv)):
            if self.nav.mid[i][1] > COVER_Y:
                self.nav.ok[i] = False
    CA.Lite.__init__ = lite
    try:
        return CA.build(zp, dst, {'max': max_new, 'sparse': True, 'cars': False, 'spread': CA.SPREAD}, log)
    finally:
        CA.Lite.__init__ = real


def load_plan(folder):
    pj = os.path.join(folder, 'van.json')
    lay_van(plan_of(pj))


def main():
    global DOG_ON, NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, STREAM, MUSIC, CIVILIANS, VAN_HIDE, KEEP_FAKETARGET, VAN_SHOW
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        DOG_ON = '--no-dog' not in a
        MUSIC = '--no-music' not in a
        VAN_HIDE = '--no-van-hide' not in a
        KEEP_FAKETARGET = '--keep-faketarget' in a
        VAN_SHOW = '--no-van-show' not in a
        if not VAN_SHOW and VAN_HIDE:
            sys.exit('--no-van-show needs --no-van-hide (a hidden van would never appear)')
        if '--str' in a:
            STREAM = os.path.abspath(a[a.index('--str') + 1])
            BK.use_stream(STREAM)
        plan = plan_of(a[a.index('--plan') + 1]) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 3 and a[0] == 'plan':
        import json
        P = van_plan(a[1])
        with open(a[2], 'w', encoding='utf-8') as f:
            json.dump(P, f, indent=1, default=str)
        print('kl_l05_layer.plan: %s (stop %s, board %s)' % (a[2], P['stop'], P['board']))
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']
        print('kl_l05_layer.van-check %s: %d fault(s)' % (a[1], len(rep['faults'])))
        for x in rep['faults']:
            print('  ' + str(x))
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) == 3 and a[0] == 'cover':
        _L, rep, out, bad = cover_step(a[1], a[2])
        sys.exit(1 if rep is None or any(s_ == 'FAIL' for s_, _t in out) or bad else 0)
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        load_plan(a[1])
        bad = check(a[1])
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
        sys.exit(1 if bad else 0)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    import kl_l05_layer
    kl_l05_layer.main()
