"""kl_fa_v2_hotcoffee.py - VERSION 2 of 'Hot Coffee' (map id DM01B): Dog Days' F07 Fragile Alliance systems + the CAMPAIGN level
M01_A ('Hot Coffee' of Dead Men) with the campaign's own enemies, a CAMPAIGN-style round. OFFLINE ONLY: built and checked, NEVER RUN IN THE GAME.
V1 is the installed M01_FA_A (slot F01 page 2, id DM01, tools/kl_maps.py). This is a NEW map beside it (kl_expansion.EXTRA: slot F03, page 3).
Cut from tools/kl_fa_v2_park.py (DM06B); the park module is NOT edited.

THE ROUND (owner, 2026-10-17: 'the campaign version'; raw, bodycam-like, Heat-style gunfire):
  1. The crew starts at the GARAGE / back-street end of the campaign level (x -650 .. -220, z 4150 .. 4280) and fights toward +z.
  2. The campaign's own police squads fight them on the way (50 men in 23 squads, in four stages):
       start (timer)      the garage and its back street (z 4000 .. 10000)
       walk  (box)        the alley's mouth (z 11800): the warehouse's squads (z 20000)
       floor (box)        the warehouse's exit (z 22500): the diner's squads (z 25000 .. 27500)
       donut (speak box)  the diner's north edge (z 24250): the donut shop's squads, THE ALARM (van timer + gate = F07's police squads)
  3. Loot: 12 briefcases, six in the warehouse and six in the diner.
  4. Out: north past the donut shop to the street at z 30800: the van waits there (kl_map_escape plan, stop (2000, 30800)).
The garage's back wall is blown by the campaign's own blast objects at the round-start event (GARAGE_BLAST, measured with kl_walk2d.py: the crew was
locked in without it). No other doors, no seal, no light show, no room gates (bots: bots_step, OFF - the mesh is in islands, see its docstring): the campaign level needs none of them.

Holds the nine names of kl_graft.AUTHOR_NAMES. Every number marked GUESS is a guess; MEASURED ones come from the real files (the bare graft
F07+M01_A: navigation mesh = kl_route.load('M01_A').mesh(), collision floors = kl_map_escape.Ground; re/campaign_v2_plan.md).
Usage (from tools/):
  python kl_fa_v2_hotcoffee.py test <out> [--keep] [--plan plan.json] [--squads-awake] [--no-ai] [--no-police] [--no-blast] [--no-civilians] [--str PC_Def.str]
  python kl_fa_v2_hotcoffee.py civilians <finished folder> <new folder> [n]   the post-step (after the gun-sound step)
  python kl_fa_v2_hotcoffee.py plan <bare-folder> <plan.json>      the van's plan from a built bare graft
  python kl_fa_v2_hotcoffee.py check <folder> | van-check <folder> | finish <folder>
"""
import collections, contextlib, math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms
import kl_prpjoin as J
import kl_fa_author as A
import kl_fa_bank as BK
import kl_map_escape as ESC

HOST, LEVEL = 'F07', 'M01_A'
TITLE = 'Hot Coffee (campaign)'
R = 'ROOT\\'
HIDDEN = 0x400
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
KNOWN = (('stream clips are not in the merged stream file', 'the campaign level\'s music and ambience beds have no record in the installed PC_Def.str '
          '(a later stream-file step): those sounds are silent, nothing else'),)
NO_AI = False                           # True ('--no-ai'): no squad of the campaign stays
SQUADS_AWAKE = False                    # True ('--squads-awake'): ZSquadScript field 3 = 1 on all (fall-back if naming the start child does not wake a squad)
POLICE_ARRIVE = True                    # False ('--no-police')
VOICE = True
STREAM = None

# what the campaign pre-pass drops from M01_A on top of its own rule. GUESS: nothing (build() reports the bound objects that stayed)
M_DROP = ()

# ------------------------------------------------------------------ the campaign level, measured on M01_A (bare graft; navigation mesh; collision floors)
# MEASURED: the mesh is flat (every polygon is at height about 0), so the heights below are COLLISION floors (kl_map_escape.Ground):
# garage 0, alley 0 .. 60, warehouse 0, diner / donut street / van street -15. The mesh has islands: garage (part 0), alley (24), the rest (15).
FLOOR_Y = 0.0
STREET_Y = -15.0
NORTH = (0.0, 1.0)                      # the way of the round: +z
# START: two rows of four on the mesh's block x -700 .. -100, z 3900 .. 4600 of the garage. MEASURED (every point inside the mesh), GUESS: the rows
START = [(float(x), FLOOR_Y, z) for z in (4150.0, 4280.0) for x in (-650, -520, -390, -260)]
# TRAITOR: four behind the START rows (z 4650, mesh rows 4600 / 4700 are whole from x -900 to 0). GUESS
TRAITOR = [(float(x), FLOOR_Y, 4650.0) for x in (-700, -550, -400, -250)]
# TEAM_MERC: eight on the strip x 800 .. 900, z 4000 .. 4600 (whole in the mesh). GUESS
TEAM_MERC = [(float(x), FLOOR_Y, float(z)) for z in (4000, 4200, 4400, 4600) for x in (800, 900)]
WALK_AT = (2800.0, 0.0, 12000.0)        # the alley (mesh x 2700 .. 2900, z 10800 .. 12800 is a strip 200 wide)
WAREHOUSE = (3100.0, FLOOR_Y, 20250.0)  # the warehouse's floor (collision 0; upper floors at 345 and over)
FLOOR_AT = (5250.0, FLOOR_Y, 22500.0)   # between the warehouse and the diner: the mesh holds x 1000 / 1500 and x 5000 .. 7000 here
DINER = (4500.0, STREET_Y, 25400.0)
DONUT_AT = (4000.0, STREET_Y, 24250.0)  # the diner's north edge (mesh x 3000 .. 4500, z 24000 .. 24500)
STAGE_B = [(x, FLOOR_Y, z) for x, z in ((2700.0, 12000.0), (2700.0, 12200.0), (2900.0, 12000.0), (2900.0, 12200.0))]
STAGE_C = [(x, FLOOR_Y, z) for x, z in ((5000.0, 22400.0), (5500.0, 22400.0), (5000.0, 22600.0), (5500.0, 22600.0))]
STAGE_D = [(x, STREET_Y, z) for x, z in ((3500.0, 24500.0), (4000.0, 24500.0), (3500.0, 24000.0), (4000.0, 24000.0))]
# the police who come back after a death: the street west of the van's stop (x -900 .. -300, z 28900: mesh, 2900 from the boarding place). GUESS
AFTER_DEATH = [(-900.0 + 100.0 * i, STREET_Y, 28900.0) for i in range(7)]
BODIES = [(-900.0 + 100.0 * i, STREET_Y, 28600.0) for i in range(8)]


def snap_mesh(mesh, p):
    """p with the navigation mesh's height under it (p itself when the mesh has nothing there). NOT used on M01_A: its mesh is flat (0)."""
    return (float(p[0]), float(p[1]), float(p[2]))


def _spawn():
    """ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz) or a place looked at)."""
    board = BOARD_AT
    return {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (30, 0, 20), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (30, 0, 20), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 40), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (TEAM_MERC, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (40, 0, 40), NORTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (AFTER_DEATH, (0, 0, 0), board)}


# ------------------------------------------------------------------ the loot: 12 briefcases (where the case's underside lies, degrees, value, what)
# MEASURED: the collision floors (warehouse 0 with upper floors from 345; diner -15, one spot at 2). GUESS: every place, turn and value
# (warehouse 150,000 each = 0.9 million; diner 200,000 each = 1.2 million). The diner has no roof collision at these points: whether the
# cases lie INSIDE the diner is not known (a live look decides).
LOOT = [((float(x), FLOOR_Y, float(z)), yaw, 150000, 'the warehouse') for (x, z), yaw in
        zip([(2900, 20150), (3100, 20150), (3300, 20150), (2900, 20300), (3100, 20300), (3300, 20300)], (4.0, -8.0, 90.0, 85.0, -12.0, 10.0))]
LOOT += [((float(x), STREET_Y, float(z)), yaw, 200000, 'the diner') for (x, z), yaw in
         zip([(4150, 25350), (4350, 25350), (4550, 25350), (4750, 25350), (4300, 25800), (4650, 25800)], (0.0, 30.0, -20.0, 70.0, 15.0, -45.0))]
LOOT_REACH = 125.0                      # TriggerBox2 radius (kl_escape.REACH)
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, as the club's

# ------------------------------------------------------------------ the host's layer (F07)
PARK = (0.0, -60000.0, 0.0)
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyTop', '040_LevelBound_AlleyRight',
                                                         '040_LevelBound_AlleyLeft', '030_LevelBound_StreetRight', '030_LevelBound_StreetLeft')
          for b in ('Bound', 'Warn01', 'Warn02')]       # all 18: F07's alley bounds do not fit this map (no bound of the map's own)
WALK_BOX = (WALK_AT[0], WALK_AT[1] + 100.0, WALK_AT[2]), (900.0, 200.0, 400.0)                  # GUESS: covers the alley's strip
FLOOR_BOX = (3500.0, FLOOR_AT[1] + 100.0, FLOOR_AT[2]), (3000.0, 200.0, 500.0)                  # GUESS: x 500 .. 6500, both ways out of the warehouse
DONUT_BOX = (4500.0, DONUT_AT[1] + 115.0, DONUT_AT[2]), (3500.0, 200.0, 300.0)                  # GUESS: the speak box, moved here
PLACE_FIXED = {
    'FASpecials!POI!Trigger_POI_TheLootArea': ((WAREHOUSE[0], 60.0, WAREHOUSE[2]), None, (700, 150, 300), 'GUESS: the warehouse floor (it starts the loot marker\'s timer)'),
    'FASpecials!POI!POI_TheLootArea': ((WAREHOUSE[0], 160.0, WAREHOUSE[2]), None, None, 'over the warehouse\'s cases'),
    'FASpecials!PIP!EnterLootArea': ((WAREHOUSE[0], 60.0, WAREHOUSE[2]), None, (700, 150, 300), 'the warehouse: AI heisters\' first stage is inside this box'),
    'FASpecials!PIP!ExitLootArea': ((DONUT_AT[0], DONUT_AT[1] + 120, DONUT_AT[2]), None, (700, 150, 50), 'GUESS: a plane at the diner\'s north edge, after the last loot'),
    'Specials!LevelSpeak!TriggerBox': (DONUT_BOX[0], None, DONUT_BOX[1], 'GUESS: the diner\'s north edge (the crew leaves the loot; it starts the donut squads and the alarm)'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': (DONUT_BOX[0], None, None, 'with its trigger box'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((-400, 700, 3300), None, None, 'GUESS: over the garage'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((-400, 0, 4200), None, None, 'the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((2800, 700, 11000), None, None, 'GUESS: the alley\'s mouth'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': (WALK_AT, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((5250, 700, 21500), None, None, 'GUESS: the warehouse exit'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': (FLOOR_AT, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((4000, 700, 23400), None, None, 'GUESS: the diner\'s north edge'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': (DONUT_AT, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((800, 700, 28000), None, None, 'GUESS: over the street west of the van'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((800, -15, 30000), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((800, 700, 28000), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((800, -15, 30000), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these (GUESS: the alley, the warehouse exit, the diner's north edge)
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': (WALK_AT, None, (900, 150, 400), 'GUESS: the alley'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': (FLOOR_AT, None, (3000, 150, 500), 'GUESS: the warehouse exit'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': (DONUT_AT, None, (3500, 150, 300), 'GUESS: the diner\'s north edge'),
    # jump points (developer aids): the round's stations
    'Specials!JumpPoints!01_Start': (START[1], NORTH, None, 'the garage'),
    'Specials!JumpPoints!02_MarketMain': (WALK_AT, NORTH, None, 'the alley'),
    'Specials!JumpPoints!03_MarketOrange': (WAREHOUSE, NORTH, None, 'the warehouse'),
    'Specials!JumpPoints!04_LootWarehouse': (DINER, NORTH, None, 'the diner'),
    'Specials!JumpPoints!05_MarketGreen': (DONUT_AT, NORTH, None, 'the diner\'s north edge'),
}
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'start timer': FF + 'RivalMercs!Timer',                          # TriggerDelay2 START_AT -> the 'start' squads
        'backstop': FF + 'RivalMercVan!Timer',                           # TriggerDelay2 BACKSTOP_AT -> the police and the van, whatever the crew did
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # TriggerBox at the alley -> the 'walk' squads
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # TriggerBox at the warehouse exit -> the 'floor' squads
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate',                  # GateGroup + two GatePath: the first of the speak box / the clock lets the police in
        'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',            # ActivateGeom -> the van's group (the van is hidden until then)
        'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',       # TriggerDelay2 VAN_DELAY -> van on, the speak line
        'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator',   # DeactivateGeom -> the van's group again (round 2)
        'pre show': FF + 'Shutters!GeomActivator_TearGas_RIGHT',         # ActivateGeom -> the garage wall's intact pieces again (round 2; GARAGE_BLAST)
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
# THE GARAGE WALL (owner 2026-10-17: 'you cant even leave that garage building because its a scripted event'). In the campaign a scripted
# explosion blows the garage's back wall; the build drops the scripts, so the wall stayed shut and the crew was locked in. MEASURED
# (tools/kl_walk2d.py on the built level, collision only): with the 15 pieces of the campaign's own 'GeomDeactivator_OnExplosion' list AND the brick
# wall 'Interior_BrickWallShatter_01' gone, a person walks from the START rows out to the junkyard (22,676 plan cells, the junk piles then
# bound it); without the brick wall only 5,712 cells (the garage), without the list 4,000. The door GarageDor_A is NOT the exit.
# So the campaign's own blast objects stay in the level and the round-start event fires them START_AT s after the round starts:
#   out   DeactivateGeom (campaign list: intact wall, tanks, repair walls, fire box) + the brick wall (added here)
#   gfx   ActivateGeom   (the blown wall's collision and debris)        fire / dust   ActivateGeom (flames, smoke, flask)   boom   Explode
# Round 2: the monitor list (round-start event) first shows the intact pieces again (carrier 'pre show') and hides the blown ones ('startup').
GARAGE_BLAST = True                     # False ('--no-blast'): the wall stays shut as in the first v2 (the crew is locked in the garage)
# The blast rides on the start timer (START_AT after the round-start event, i.e. before GO): the wall is open when the round begins. GUESS
GW = 'Specials!GarageWallExplosion!'
BLAST = collections.OrderedDict([('out', GW + 'GeomDeactivator_OnExplosion'), ('gfx', GW + 'GeomActivator_GFXToTurnOnExplosion'),
                                 ('fire', GW + 'GeomActivator_StartExplosionPart_01'), ('dust', GW + 'GeomActivator_StartExplosionPart_03'),
                                 ('boom', GW + 'BigExplosion'), ('startup', GW + 'GeomDeactivator_OnStartup'), ('brick', GW + 'Activator_BrickWallShatter')])
EXPLODE_REACH = BK.EXPLODE_REACH
CIVILIANS = 24                          # civilians for the POST-STEP civilians_step() (tools/kl_fa_civs.py, kl-merge-e5's; 0 / '--no-civilians' = none)
GATE_WAYS = ('Way#01', 'Way#02')
START_AT = 2.0                          # s from the round-start event to the first squads. GUESS (the event comes 8.4 - 8.8 s before GO)
BACKSTOP_AT = 420.0                     # s from the round-start event: the police come whatever the crew did. GUESS (the way is long: 290 m)
VAN_DELAY = 8.0                         # s from the alarm to the van's show and the police. GUESS
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R', 18: 'Multiplayer/F09/MissionReminder_02_R', 19: 'Multiplayer/F06/MissionReminder_01_R',
         20: 'Multiplayer/F06/ReachlootArea_01_R', 127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
         136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
START_KEY = 'AllLevels/Interface/Online/GameStart/M01A_%s_Start'
_GO = 'Fight north through the back street, the warehouse and the diner. Take the cases, then reach the van waiting on the street past the donut shop.'
TEXTS = {START_KEY % 'FA': _GO, START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.', START_KEY % 'UCC': _GO}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}

# ------------------------------------------------------------------ the van on the street north of the donut shop
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'
STOP = (2000.0, -13.0, 30800.0)
ARRIVE_LEN, LEAVE_LEN = 4500.0, 4000.0
# MEASURED (m01van.py on the bare graft F07+M01_A): no fault of kl_map_escape's planner for this road with this camera; one note: the drive in
# starts 900 after the donut shop's plant 'SO1103_M01_DonutShop_Plant_01!DonutShop_Plant_00' (a plant in the lane 4947 before the stop: GUESS harmless)
ROAD = dict(arrive=[(STOP[0] + ARRIVE_LEN * (1 - i / 4.0), STOP[1], STOP[2]) for i in range(4)], stop=STOP,
            leave=[(STOP[0] - LEAVE_LEN * (i + 1) / 3.0, STOP[1], STOP[2]) for i in range(3)], at='box', heading=-90.0, cam=(800.0, 250.0, 29600.0))
PLAN = None
NO_PLAN = 'kl_fa_v2_hotcoffee: the van has no plan: build with \'kl_fa_v2_hotcoffee.py test <out>\' or kl_fa_v2_hotcoffee.build()'
BOARD_AT = (2000.0, -15.0, 30800.0)    # the rear doors of the standing van (about; prepare_host takes PLAN['board'] once there is a plan)
LANE_CLEAR = 250.0                      # no spawn point, man, cover point or the marker nearer than this to the van's drive. GUESS
BOARD_CLEAR = 500.0                     # no cover point of the police nearer than this to the boarding place
FED_CLEAR = 1000.0                      # no AFTER_DEATH point or police body nearer than this to the boarding place
POLICE_CLEAR = BK.POLICE_CLEAR
BOUND_AFTER = 1000.0
BOARD_NEAR = 30.0

# F07's police squads that come in on the van's street: squad -> (anchor, men, cover, defend). GUESS: every place. Left squads stand west of the
# van (x -900 .. 500, z 29200 .. 29700), Right squads east of it (x 4000 .. 6000, z 29300 .. 29700): 1100 or more off the lane z 30800
# (mesh rows z 29000 .. 30500 are whole from x -1000 to 2500 and from 3500 to 6000; the bounds below were read by eye: check() proves them).
G30 = 'Gameplay!030_AfterLoot!'
ARRIVE = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-500.0, STREET_Y, 29200.0), [(-800.0, STREET_Y, 29400.0), (-600.0, STREET_Y, 29500.0), (-400.0, STREET_Y, 29600.0)],
                                           [(-300.0, STREET_Y, 29700.0), (-100.0, STREET_Y, 29600.0), (100.0, STREET_Y, 29700.0)], (-500.0, STREET_Y, 29300.0))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((0.0, STREET_Y, 29200.0), [(-200.0, STREET_Y, 29300.0), (0.0, STREET_Y, 29400.0)],
                                                 [(300.0, STREET_Y, 29500.0), (500.0, STREET_Y, 29400.0)], (100.0, STREET_Y, 29300.0))),
    (G30 + '030_FinancialAlleyExit_Right', ((5000.0, STREET_Y, 29300.0), [(4200.0, STREET_Y, 29400.0), (4500.0, STREET_Y, 29500.0), (4800.0, STREET_Y, 29600.0)],
                                            [(5200.0, STREET_Y, 29700.0), (5500.0, STREET_Y, 29600.0), (5800.0, STREET_Y, 29700.0)], (5000.0, STREET_Y, 29400.0))),
    (G30 + '030_FinancialAlleyExitStreet_Right', ((5500.0, STREET_Y, 29300.0), [(4000.0, STREET_Y, 29300.0), (4300.0, STREET_Y, 29200.0)],
                                                  [(5700.0, STREET_Y, 29500.0), (5900.0, STREET_Y, 29400.0)], (5600.0, STREET_Y, 29400.0)))])
ARRIVE_START = '10_RunToCover'

ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))


def police():
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def __getattr__(name):
    if name == 'KEEP':
        return _KEEP + tuple(x for x in police() if x not in _KEEP)
    raise AttributeError(name)


DROP = ('Specials!CoverPoints!*',)      # M01_A's own cover list stays; a second FFCoverList is an assert in its init

# ------------------------------------------------------------------ the campaign's squads (M01_A), MEASURED with m01sq.py / m01men.py on the dead level
# 'AI_Players!Enemies!' + name -> (stage, the child that starts it). All 23 are plain squads (ZSquadScript, ZSoldier, behaviour routs only).
# Left out: the 01_Crash and 02_Sidestreet squads (behind the start), the car squads (HavokCar: 03 ArriveByCar / ExitScene / Rear_OnStreet, 06 SWAT 01..04
# / BackupWave), LeftBarricade (LeapFrog), AssaultFromBehind (behind the START rows), the allies and Lynch's proxies.
#   'start'  timer START_AT            'walk'   the box in the alley            'floor'  the box at the warehouse exit
#   'donut'  the speak box (diner's north edge): also the alarm
# A squad is not in the world (field 3 = 0) until its child is named; the children are plain behaviour routs (the stock Dog Days way).
GE = 'AI_Players!Enemies!'
SQUADS = collections.OrderedDict([
    (GE + '03_Garage!03_Squad_01_CrawlUnder', ('start', '050_Defend_InsideGarage')),
    (GE + '03_Garage!03_Squad_StreetBehindGarage', ('start', '030_Defend')),
    (GE + '03_Garage!03_Squad_02_GarageAssaultOnFoot', ('start', 'DefendBehaviour')),
    (GE + '03_Garage!03_Squad_SneakAroundTheBack', ('start', '010_SneakAroundBack')),
    (GE + '03_Garage!03_Squad_02_OnStreet_Wave_03', ('start', '005_DefendBack')),
    (GE + '04_Warehouse!04_Squad_01_IntoWarehouseFRONT', ('start', '010_D_Outside')),
    (GE + '04_Warehouse!04_Squad_01_IntoWarehouse', ('walk', '010_D_GroundFloor_pos01')),
    (GE + '04_Warehouse!04_Squad_02_IntoWarehouse', ('walk', '010_DefendInside')),
    (GE + '04_Warehouse!04_Squad_03_IntoWarehouse', ('walk', '010_DefendInside')),
    (GE + '04_Warehouse!04_Squad_03_OutBack', ('walk', 'DefendBehaviour')),
    (GE + '05_Diner!05_Squad_07_StripmallBack', ('walk', '010_DefendInside')),
    (GE + '05_Diner!05_Squad_00', ('floor', '021_DefendBehaviour')),
    (GE + '05_Diner!05_Squad_02', ('floor', '020_FireAtWill')),
    (GE + '05_Diner!05_Squad_03', ('floor', '020_FireAtWill')),
    (GE + '05_Diner!05_Squad_04_SupportShootAtDiner', ('floor', '020_DefendBehaviour')),
    (GE + '05_Diner!05_Squad_05_SupportShootAtDiner', ('floor', '020_DefendBehaviour')),
    (GE + '05_Diner!05_Squad_06_SupportTearGasIntoDiner', ('floor', '020_DefendBehaviour')),
    (GE + '06_DonutShop!06_010_Wave_01_Middle', ('donut', '040_DefendBehaviour_02')),
    (GE + '06_DonutShop!06_010_Wave_01_Right', ('donut', '025_DefendBehaviour_02')),
    (GE + '06_DonutShop!06_000_RightBarricade', ('donut', '015_DefendVSDiner')),
    (GE + '06_DonutShop!06_030_Wave_02_SWAT_05', ('donut', 'DefendBehaviour')),
    (GE + '06_DonutShop!06_Squad_RightSniper', ('donut', '008_Defend')),
    (GE + '06_DonutShop!06_Squad_LeftSniper', ('donut', '008_Defend'))])
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout', 'GateGroup', 'GatePath', 'DeactivateGeom', 'Filter'}
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
SQUAD_ACTIVE = A.SQUAD_ACTIVE
MAN_OFF, MAN_IN = 60.0, 15.0
MEN = collections.OrderedDict()         # {path of a man's group: (x, y, z) hint}: men further than MAN_OFF off the mesh; filled by a first run (strip() lists them)


# ------------------------------------------------------------------ 1. the host level before the graft
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT bare F07 + M01_A folder. A fault is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_v2_hotcoffee: no van on ROAD: %s' % '; '.join(P['faults']))
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
    mark = (b[0], b[1] + 188.0, b[2] - 350.0)       # south of the drive, 350 off (mesh rows z 30500 / 31000 are whole here)
    box = ((b[0], b[1] + 200.0, b[2]), None, (450.0, 300.0, 450.0), 'GUESS: round the van\'s boarding place on the street')
    t['Gameplay!EscapeSetup!otrExitLevel'] = box
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    t['FASpecials!POI!POI_TheEscapeArea'] = (mark, None, None, 'beside the boarding place')
    t['Specials!JumpPoints!06_Exit'] = ((b[0], b[1], b[2]), NORTH, None, 'the boarding place')
    t[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the alley')
    t[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the warehouse exit')
    return t


def place_police(S, log=print):
    """F07's police squads of ARRIVE onto the van street (kl_fa_club.place_police's way, this file's table). -> [(squad, men)]"""
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
        log('  kl_fa_v2_hotcoffee: the police that arrive: %d of F07\'s squads re-placed (%d men) on the street north of the donut shop' % (len(out), sum(n for _s, n in out)))
    return out


_plan = {}


def squad_plan():
    """The campaign's squads that stay -> ({squad: (path of the child that starts it, actors, kinds stripped, the kind that starts it)}, {left: why})."""
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
            _stage, child = SQUADS[name]
            actors = sum(sc.cls(k) == 'ZFFActor' for k in range(t, sc.end[t]))
            odd = sorted(set(ctrl) - A.PLAIN - STRIP)
            if odd or not actors or ctrl['ZSoldier'] != actors:
                raise ValueError('kl_fa_v2_hotcoffee: %s cannot stay: it holds %s, %d actors, %d ZSoldier' % (name, odd or 'plain kinds', actors, ctrl['ZSoldier']))
            ks = sc.resolve(R + name + '\\' + child)
            kinds = {sc.p.key(nm) for k in ks for nm, _b in sc.nodes[k]['ctrls']}
            kind = next(iter(sorted(kinds & A.BEHAVE)), 'SquadModifierBehaviour' if 'SquadModifierBehaviour' in kinds else None)
            if len(ks) != 1 or kind is None:
                raise ValueError('kl_fa_v2_hotcoffee: %s\\%s: %d nodes holding %s - neither a behaviour rout nor a squad modifier' % (name, child, len(ks), sorted(kinds)))
            keep[name] = (R + name + '\\' + child, actors, sorted(set(ctrl) & STRIP), kind)
        if set(keep) != set(SQUADS):
            raise ValueError('kl_fa_v2_hotcoffee: squads of SQUADS that are not in %s: %s' % (LEVEL, sorted(set(SQUADS) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for this map. S: kl_graft.Level('F07'), unedited."""
    import kl_route
    sc = S.prp
    if PLAN is None:
        raise ValueError(NO_PLAN)
    mesh = kl_route.load(LEVEL).mesh()
    spawn = _spawn()
    for name, (pos, face, half, _why) in place_now().items():
        put(S, name, pos, face, half)
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
            pts, face = (START, NORTH) if crook else (BODIES, BOARD_AT)
            p = pts[seen[crook, 'hero'] % len(pts)]
            A.place(S, t, p, facing(p, face))
            seen[crook, 'hero'] += 1
    log('  kl_fa_v2_hotcoffee: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
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
    by = collections.Counter(what for _p, _y, _v, what in LOOT)
    log('  kl_fa_v2_hotcoffee: loot: %d objects, %d in all: %s' % (len(LOOT), sum(v for _p, _y, v, _w in LOOT), dict(by)))
    place_police(S, log)
    S.van = ESC.van_prepare(S, PLAN, log)
    # the van is NOT in the world until the alarm (the club's VAN_LATE: no FakeTarget, hidden from the load)
    vg = A.node_of(sc, van_path()[len(R):])
    gone = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
    for k in gone:
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
    A.place(S, vg, hidden=True)
    log('  kl_fa_v2_hotcoffee: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; the alarm shows it' % len(gone))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(place_now()['FASpecials!POI!POI_TheEscapeArea'][0])[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_fa_v2_hotcoffee: the escape marker is %d from the van\'s drive (%d wanted)' % (off, LANE_CLEAR))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M01_A the campaign pre-pass must leave in: the kept squads and (GARAGE_BLAST) the garage wall's blast objects."""
    if level != LEVEL:
        return ()
    return tuple(squad_plan()[0]) + (tuple(BLAST.values()) if GARAGE_BLAST else ())


def strip(M, log=print):
    """On the converted Dead Men level, before the join: the kept squads lose STRIP's kinds; every man who stands beside the mesh goes onto it."""
    import kl_route
    if M.name != LEVEL:
        return 0
    keep = squad_plan()[0]
    if not keep:
        log('  kl_fa_v2_hotcoffee: %s: no squad stays (NO_AI)' % M.name)
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
                if 'AttachGeomToBone' in gone:
                    A.place(M, k, hidden=True)
                    A.place(M, sc.parent[k], hidden=True)
                    props += 1
    mesh = kl_route.load(LEVEL).mesh()
    placed = []
    for path, hint in MEN.items():
        g = A.node_of(sc, path)
        hit = mesh.on(*[float(v) for v in hint])
        if hit is None:
            raise ValueError('kl_fa_v2_hotcoffee: MEN: %s: (%d, %d, %d) is not on the navigation mesh' % (path, *hint))
        was = world_of(M.ents[g - 1])[0]
        BK.man_to(M, g, (float(hint[0]), hit[1], float(hint[2])), mesh)
        placed.append((path, was))
    moved, off = [], []
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            if sc.cls(k) != 'ZFFActor':
                continue
            g = sc.parent[k]
            w = world_of(M.ents[g - 1])[0]
            if mesh.on(*w) is not None:
                continue
            d, i = mesh.nearest(*w)
            if i is None or d > MAN_OFF:
                off.append('%s at (%d, %d, %d), %s off' % (sc.path[k], *w, d))
                continue
            mid = mesh.mid[i]
            for step in range(1, 201):
                x, z = w[0] + (mid[0] - w[0]) * step / 200.0, w[2] + (mid[2] - w[2]) * step / 200.0
                if mesh.inside(i, x, z) and math.hypot(x - w[0], z - w[2]) >= d + MAN_IN:
                    break
            new = (x, mesh.height(i, x, z), z)
            BK.man_to(M, g, new, mesh)
            moved.append((sc.path[g][5:], round(d), math.dist(w, new)))
    log('  kl_fa_v2_hotcoffee: %s: %d squads stay (%d men); taken off them: %s; %d props hidden' % (
        M.name, len(keep), sum(a for _s, a, _k, _w in keep.values()), dict(n) or 'nothing', props))
    log('  kl_fa_v2_hotcoffee: %d men re-placed (MEN); %d stood beside the navigation mesh and were put on it: %s' % (
        len(placed), len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    for o in off:
        log('  kl_fa_v2_hotcoffee: MAN OFF THE MESH (give him a place in MEN): ' + o)
    if off:
        raise ValueError('kl_fa_v2_hotcoffee: %d men stand more than %d off the navigation mesh: %s' % (len(off), MAN_OFF, off))
    return sum(n.values())


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_v2_hotcoffee: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    left = [sc.names[t] for t in sc.tops() if sc.names[t].startswith(('Boundaries!',))]
    if left:
        raise ValueError('kl_fa_v2_hotcoffee: the campaign\'s own bounds are in the build: %s' % left)
    plan = squad_plan()[0]
    stage, quiet = collections.defaultdict(list), 0
    for n, (first, _actors, _strip, kind) in plan.items():
        k = node(n)
        st = SQUADS[n][0]
        if values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] not in (0, 1):
            raise ValueError('%s: ZSquadScript field %d is %r' % (n, SQUAD_ACTIVE, values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE]))
        put_(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 1 if SQUADS_AWAKE else 0})
        j = sc.resolve(must([first])[0])[0]
        stage[st].append(first)
        if kind == 'SquadModifierBehaviour':
            put_(j, kind, **{'f4': 'eAM_Activate'})
        for j in range(k, sc.end[k]):               # a message list inside the squad names only what still holds a controller
            for kind_ in [sc.p.key(nm) for nm, _b in sc.nodes[j]['ctrls'] if sc.p.key(nm) in MESSAGE_KINDS]:
                for f, x in enumerate(values(sc, j, kind_)):
                    if isinstance(x, list) and x and isinstance(x[0], str):
                        live = [s for s in x if not any(sc.top[h] == k and not sc.nodes[h]['ctrls'] for h in sc.resolve(s))]
                        if len(live) != len(x):
                            put_(j, kind_, **{'f%d' % f: live})
                            quiet += len(x) - len(live)
    shatter = []
    arrive = must([R + n + '\\' + ARRIVE_START for n in police()])
    armed = BK.soldier_rows(sc, plan, log) if plan else {}
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    for w in ways:
        put_(sc.resolve(w)[0], 'GatePath', f0=arrive)
    blast_on, blast_reset = [], []
    if GARAGE_BLAST:
        b = {r: node(n) for r, n in BLAST.items()}
        live = lambda xs: [s for s in xs if sc.resolve(s)]
        brick = live(values(sc, b['brick'], 'AIDWrapper')[0])
        pre = live(values(sc, b['out'], 'DeactivateGeom')[1])
        post, fire = live(values(sc, b['gfx'], 'ActivateGeom')[1]), live(values(sc, b['fire'], 'ActivateGeom')[1])
        if len(brick) != 1 or len(pre) < 10 or not post or not fire:
            raise ValueError('kl_fa_v2_hotcoffee: the garage wall\'s blast lists are not whole: brick %s, %d pieces off, %d on, %d fire' % (brick, len(pre), len(post), len(fire)))
        v = values(sc, b['boom'], 'Explode')
        if len(v) != 18 or not all(isinstance(v[j], float) for j in EXPLODE_REACH) or values(sc, b['boom'], 'AIDWrapper')[:2] != [[R + BLAST['boom']], 'Activate']:
            raise ValueError('kl_fa_v2_hotcoffee: %s is not an Explode in the Dog Days layout with a wrapper of its own: %s' % (BLAST['boom'], v))
        put_(b['boom'], 'Explode', **{'f%d' % j: 1.0 for j in EXPLODE_REACH})      # no harm to the crew (as the vault's blast, kl_fa_bank)
        put_(b['out'], 'DeactivateGeom', f1=pre + brick)                            # GUESS: the brick wall's body leaves with the intact pieces
        lists('pre show', 'ActivateGeom', f0='AITrigger', f1=pre + brick)
        hid = live(values(sc, b['startup'], 'DeactivateGeom')[1])
        put_(b['startup'], 'DeactivateGeom', f1=hid + [s for s in post + fire if s not in hid])
        blast_on = [R + BLAST[x] for x in ('out', 'gfx', 'fire', 'dust', 'boom')]
        blast_reset = [R + BLAST['startup'], R + ROLE['pre show']]
        log('  kl_fa_v2_hotcoffee: GARAGE_BLAST: round start + %.0f s: %d pieces + the brick wall off, %d on, %d fire/smoke, 1 Explode (reach 1); round 2 shows them again first' % (
            START_AT, len(pre), len(post), len(fire)))
    lists('start timer', 'TriggerDelay2', f0=START_AT, f4=stage['start'] + blast_on)
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['walk'])
    # the warehouse exit: the diner's squads. The ALARM (the van's timer) and the gate (the police on the van's street) are the speak box's, at the diner's north edge
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['floor'])
    lists('backstop', 'TriggerDelay2', f0=BACKSTOP_AT, f4=[ways[1], R + ROLE['van timer']])
    lists('van on', 'ActivateGeom', f0='AITrigger', f1=[van_path()])
    lists('van timer', 'TriggerDelay2', f0=VAN_DELAY, f4=[R + ROLE['van on'], R + ROLE['speak']])
    lists('reset hide', 'DeactivateGeom', f0='AITrigger', f1=[van_path()])
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    lists('monitor', 'AIMonitor', f2=[R + ROLE['reset hide']] + blast_reset + have + [R + ROLE['start timer'], R + ROLE['backstop']])
    # the speak box (the diner's north edge): the donut shop's squads, the alarm and the gate; the exit line comes from the van's timer, once
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=stage['donut'] + [R + ROLE['van timer'], ways[0]])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    if PLAN is None:
        raise ValueError('kl_fa_v2_hotcoffee: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    men = sum(a for _f, a, _s, _k in plan.values())
    log('  kl_fa_v2_hotcoffee: wired: %d campaign squads (%d men): round start + %.0f s -> %d; the box in the alley -> %d; the box at the warehouse exit -> %d; '
        'the speak box -> %d + the alarm (+%.0f s: the van, the exit line) + the gate (%d police squads); backstop %.0f s; %d dead entries cut; soldier rows: %s' % (
            len(plan), men, START_AT, len(stage['start']), len(stage['walk']), len(stage['floor']), len(stage['donut']), VAN_DELAY, len(arrive), BACKSTOP_AT, quiet,
            dict(armed) or 'the campaign rows stay'))
    return {'stage': dict(stage), 'arrive': arrive, 'ways': ways}


def layer_names(sc):
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    return True


# ------------------------------------------------------------------ glass: the compiled permutation Dog Days has
def glass_fix(E, log=print):
    """Dead Men's glass material (class Standard/Glass: reflection + specular, NO refraction) asks for a glass.fx permutation no Dog Days
    level compiles: all 53 refraction-capable glass instances of Dog Days have Refraction2DEnabled = 1 and Dog Days' fxc caches hold only
    glass.fx permutations with REFRACTION2DENABLED (kl_light.fit_shaders can only switch features OFF, so it found no fit). Fix, measured
    2026-10-17: such an instance gets Refraction2DEnabled = 1 plus Dog Days' most common refraction nodes (mask texture 0, colour white,
    scale 0.2 0.2 1 1: 29 of 53 stock instances), and the stock permutation that matches (glass.fx MESH_STANDARD with BLEND + REFLECTION + SPECULAR + STDSAMPLERSTATE +
    USEDEFAULTREFLECTIONMAP + REFRACTION2D; F06's red beacon uses it) is copied into the level's .fxc from the stock level that holds it,
    when the .fxc does not have it already. GUESS: that a clear pane with a faint 2D refraction (scale 0.2) looks acceptable; NOT SEEN LIVE. An instance
    that still lacks a shader afterwards is put back as it was. -> [problems]"""
    import copy, zipfile, kl_light, kl_mat, kl_texmat as T
    from kl_port_check import find, level_zips, DD_GUESSES, DD_EXE
    from kl_light import _kid, _bools, shader_cache, shader_needs, missing_shaders
    bad = []
    have = shader_cache(E.lv['.fxc'])
    lack = missing_shaders(E.mat, have)
    todo = [s for s, l in sorted(lack.items()) if all(x[0] == 'glass.fx' for x in l) and kl_mat.class_key(E.mat, E.mat.insts[s]) == ('Standard', 'Glass')
            and 'REFRACTION2DENABLED' in _bools(E.mat.insts[s]) and not _bools(E.mat.insts[s])['REFRACTION2DENABLED'][1]]
    if not todo:
        log('  kl_fa_v2_hotcoffee: glass: no Standard/Glass instance lacks a shader (%d other lacking: %s)' % (
            len(lack), [E.mat.insts[s].name for s in lack]))
        return bad
    new = {'gm_mapRefraction2DMask': [['ENAB', 2, 1, 1], ['TXID', 2, 1, 0], ['TILU', 1, 6, b'TILED'], ['TILV', 1, 6, b'TILED']],
           'gm_vRefraction2DColor': [['ENAB', 2, 1, 1], ['VALU', 0, 4, struct.pack('<4f', 1, 1, 1, 1)]],
           'gm_vRefraction2DScale': [['ENAB', 2, 1, 1], ['VALU', 0, 4, struct.pack('<4f', 0.2, 0.2, 1, 1)]]}
    saved = {s: (copy.deepcopy(E.mat.insts[s].root), list(E.mat.insts[s].f)) for s in todo}
    for s in todo:
        e = E.mat.insts[s]
        _kid(_bools(e)['REFRACTION2DENABLED'][0], 'VALU')[3] = 1
        for n in _kid(e.root, 'BIND')[3]:
            nm = _kid(n, 'NAME')[3].decode('latin1')
            if nm in new and _kid(n, 'ENAB')[3] == 0 and len(n[3]) == 2:
                _kid(n, 'ENAB')[3] = 1
                n[3][1:] = copy.deepcopy(new[nm])
                n[2] = len(n[3])
        e.f[2] = kl_mat.feature_flags(e)
    need = set()
    for s in todo:
        need |= {x for x in shader_needs(E.mat, E.mat.insts[s]) if x not in have}
    dd = find(DD_GUESSES, DD_EXE)
    got, ver = [], None
    for z in sorted(level_zips(dd)):
        if not need:
            break
        with zipfile.ZipFile(z) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith('.fxc')]
            if not names:
                continue
            ver, ent = kl_mat.read_fxc(zf.read(names[0]))
        for head, blob in ent:
            d = [n for n, _v in T.fxc_defines(head)]
            k = (head[0x810:0x850].split(b'\0')[0].decode('latin1').lower(), d[0], frozenset(d[1:]))
            if k in need:
                got.append((head, blob)); need.discard(k)
                log('  kl_fa_v2_hotcoffee: glass: %s %s copied from %s' % (k[0], sorted(k[2]), os.path.basename(z)))
    if need:
        for s in todo:
            E.mat.insts[s].root, E.mat.insts[s].f = saved[s][0], saved[s][1]
        bad.append('glass: no stock level holds %s: the instances stay as they were' % sorted(need))
        return bad
    if got:
        E.lv['.fxc'] = T.merge_fxc(E.lv['.fxc'], kl_mat.write_fxc(got, ver))
    after = missing_shaders(E.mat, shader_cache(E.lv['.fxc']), todo)
    if after:
        bad.append('glass: still lacking after the fix: %s' % {E.mat.insts[s].name: v for s, v in after.items()})
    log('  kl_fa_v2_hotcoffee: glass: %d instance(s) got Refraction2DEnabled = 1 (%s); %d fxc entr%s added' % (
        len(todo), ', '.join(E.mat.insts[s].name for s in todo), len(got), 'y' if len(got) == 1 else 'ies'))
    return bad


# ------------------------------------------------------------------ on the written level
def finish(folder, log=print):
    """The written level, in place: the lightened level, the briefcases on the loot, the texts. -> [problems]"""
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
        log('  kl_fa_v2_hotcoffee: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_v2_hotcoffee: %s: the loot already shows models of its own: left as it is' % folder)
    bad += glass_fix(E, log)
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
    log('  kl_fa_v2_hotcoffee: %d text keys in %d languages; settings fields %s name the start windows' % (len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ build and check
def build(out, log=print, plan=None):
    """F07 + M01_A with the layer into <out>/F07+M01_A campaign -> (kl_maps.one's result, that folder, the van's plan, kl_map_escape's report).
    plan None = made here on a BARE graft (<out>/_bare, deleted again)."""
    import shutil, kl_snd
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', m_drop=M_DROP)
        try:
            if not r.get('ok'):
                raise ValueError('kl_fa_v2_hotcoffee: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    kl_snd.VOICE = True if VOICE else None
    try:
        with ESC.van_layer(plan, log) as st:
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_v2_hotcoffee', m_drop=M_DROP)
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


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (and finished) folder -> [what is wrong]."""
    import json, kl_route, kl_arms
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
    if any(sc.names[t].startswith('Boundaries!') for t in sc.tops()):
        fail('the campaign\'s own bound objects are in the level (M_DROP)')
    # ---- the loot: 12 objects, the values, each on the navigation mesh
    mesh = kl_route.load(LEVEL).mesh()
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    if len(loot) != len(LOOT) or sorted(v[1] for _k, v in loot) != sorted(w for _p, _y, w, _x in LOOT):
        fail('loot: %d objects with values %s, expected %d with %s' % (len(loot), sorted(v[1] for _k, v in loot)[:3], len(LOOT), sorted(w for _p, _y, w, _x in LOOT)[:3]))
    log('  loot: %d objects, %d in all' % (len(loot), sum(v[1] for _k, v in loot)))
    for k, v in loot:
        p = pos[ents[k - 1]]
        near = mesh.nearest(*p)
        if near[0] is None or near[0] > 120.0:
            fail('loot %s at (%d, %d, %d) is %s from the navigation mesh' % (sc.names[k], *p, near[0]))
    # ---- spawn points and men on the mesh
    drive = ESC.Poly([tuple(p) for p in PLAN['path']]) if PLAN else None
    kinds = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) != 'ZSpawnPoint':
            continue
        kind = kl_fa.node_values(sc, t)[8]
        p = pos[ents[t - 1]]
        kinds[kind] += 1
        if 'START' in kind or 'TRAITOR' in kind or 'AFTER_DEATH' in kind:
            if mesh.on(*p) is None and (mesh.nearest(*p)[0] or 1e9) > 60.0:
                fail('spawn point %s (%s) at (%d, %d, %d) is %s off the navigation mesh' % (sc.names[t], kind[-12:], *p, mesh.nearest(*p)[0]))
        if 'AFTER_DEATH' in kind and PLAN and math.dist(p, PLAN['board']) < FED_CLEAR:
            fail('spawn point %s (AFTER_DEATH) is %d from the boarding place (%d wanted)' % (sc.names[t], math.dist(p, PLAN['board']), FED_CLEAR))
        if drive is not None and 'AFTER_DEATH' not in kind and abs(drive.project(p)[1]) < LANE_CLEAR and 'START' in kind:
            fail('spawn point %s is %d from the van\'s drive' % (sc.names[t], abs(drive.project(p)[1])))
    log('  spawn points by kind: %s' % {k.replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in kinds.items()})
    men = [k for k in range(1, len(sc.names)) if sc.cls(k) == 'ZFFActor']
    squads = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript')]
    off = 0
    for k in men:
        g = sc.parent[k]
        p = pos[ents[g - 1]]
        if mesh.on(*p) is None and (mesh.nearest(*p)[0] or 1e9) > MAN_OFF:
            off += 1
            fail('man %s at (%d, %d, %d) is %s off the navigation mesh' % (sc.path[k], *p, mesh.nearest(*p)[0]))
        if drive is not None and sc.path[k][len(R):].startswith(G30) and abs(drive.project(p)[1]) < LANE_CLEAR:
            fail('policeman %s is %d from the van\'s drive' % (sc.path[k], abs(drive.project(p)[1])))
    log('  actors: %d, squads: %d (campaign squads %d, F07\'s police squads %d); men off the mesh: %d' % (
        len(men), len(squads), len(SQUADS) if not NO_AI else 0, len(police()), off))
    if not NO_AI:
        for n in SQUADS:
            kk = sc.resolve(R + n)
            if not kk:
                fail('squad %s is not in the level' % n)
                continue
            if values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE] != (1 if SQUADS_AWAKE else 0):
                fail('squad %s: field %d is %r' % (n, SQUAD_ACTIVE, values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE]))
    # ---- the exit and the van
    ex = [(k, v) for k, _i, v in kl_fa.controllers(sc, kl_fa.EXIT)]
    if len(ex) != 1 or ex[0][1][2] != van_path():
        fail('the exit trigger: %s, wanted one naming %s' % ([v[2:5] for _k, v in ex], van_path()))
    if PLAN:
        b = PLAN['board']
        log('  van: boarding place (%d, %d, %d); stop %s; exit box %d from it' % (*b, [round(x) for x in PLAN['stop']], math.dist(pos[ents[ex[0][0] - 1]], b) if ex else -1))
        for t in sc.tops():
            if sc.cls(t) == 'ZSpawnPoint' and 'START' in kl_fa.node_values(sc, t)[8] and math.dist(pos[ents[t - 1]], b) < 1500:
                fail('a START spawn point is %d from the boarding place' % math.dist(pos[ents[t - 1]], b))
    return bad


def flags_of():
    return collections.OrderedDict(SQUADS_AWAKE=SQUADS_AWAKE, NO_AI=NO_AI, POLICE_ARRIVE=POLICE_ARRIVE, START_AT=START_AT, GARAGE_BLAST=GARAGE_BLAST, BACKSTOP_AT=BACKSTOP_AT, VAN_DELAY=VAN_DELAY)


def compact_in_place(folder, log=print):
    """kl_chars.py compact (the .prm chunk table is over the game's 73,728 with the whole campaign level; dead chunks are dropped) -> the
    folder's own files replaced, result.json's problems rewritten from the compaction's own check. NOT LOADED LIVE (kl_chars.compact_level)."""
    import json, shutil, subprocess
    tmp = folder.rstrip('/' + chr(92)) + '_comp_tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kl_chars.py'), 'compact', folder, tmp],
                       capture_output=True, text=True)
    out = r.stdout.strip().splitlines()
    log('  compact: ' + next((x.strip() for x in out if 'chunk-table entries' in x), 'no report'))
    probs = [x.split('PROBLEM:', 1)[1].strip() for x in out if 'PROBLEM:' in x]
    if r.returncode not in (0, 1) or not os.path.isfile(os.path.join(tmp, 'F01_Main.zip')):
        return ['compaction failed: ' + (r.stderr or '')[-200:]]
    for f in os.listdir(tmp):
        if '_Main' in f or f.endswith('.hti'):
            shutil.copy2(os.path.join(tmp, f), os.path.join(folder, f))
    shutil.rmtree(tmp, ignore_errors=True)
    rp = os.path.join(folder, 'result.json')
    res = json.load(open(rp))
    old = [x for x in res.get('problems', ()) if 'chunk-table entries' not in x]
    res['problems'] = old + [x for x in probs if x not in old]
    json.dump(res, open(rp, 'w'), indent=1, default=str)
    return []


BOT_OPT = {'stops': 2, 'cases': 'off', 'lane': True, 'window': True, 'loot_seconds': 20}
# GUESS (this file's): briefcases only, two stops (warehouse, diner), a loot wait of 20 s.
WITH_BOTS = False       # '--bots': the bots step runs. OFF BY DEFAULT: kl_fa_bots.plan REFUSES this level today (below)


def bots_step(folder, log=print):
    """kl_fa_bots.build with BOT_OPT, then kl_fa_bots_dyn.build, each into a copy, the result copied over the folder's own files.
    -> list of problems. After finish + compact, before check. NOT LOADED LIVE.
    WHY IT IS OFF: the campaign level's navigation mesh (kl_route 'M01_A') is split into islands. The START row (garage) is on one part;
    the alley, the warehouse / diner and the van's street are on others. Same-height gaps between the parts: garage -> alley 332 flat
    (kl_fa_bots.DROP_MAX across is 240), alley -> main 91 (60 up). kl_fa_bots.plan raises 'no place on the mesh part of the START row
    within 900 of the van's boarding box ... give --park'. A bot would also have no path to the loot. NEEDED (not done: kl_fa_bots* and the
    mesh belong to another session): either a mesh repair that adds polygons / links over the two gaps (kl_pf4), or START moved onto the main part."""
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
    return probs


def test(out, keep=False, log=print, plan=None):
    """Build the level with the layer into <out>, finish it, compact it, check it. -> 0 or 1. Beside the archive: van.json.
    NOT DONE HERE: the installed gun sounds (build/v2_1017/DM06B/guns_step.py <out folder>): run it AFTER this, before staging."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    late += compact_in_place(folder, log)
    if WITH_BOTS and not NO_AI:
        late += bots_step(folder, log)
    r['problems'] = json.load(open(os.path.join(folder, 'result.json'))).get('problems', r['problems'])
    vrep = van_check(folder, lambda *a: None, plan)[0]
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], flags=flags_of(), check=vrep), f, indent=1, default=str)
    bad = check(folder, log, r['problems']) + late
    log('level: %d entities, %d rooms, %.0f MB' % (r['entities'], r['rooms'], r['archive_mb']))
    if not keep:
        for f in os.listdir(folder):
            if '_Main' in f:
                os.remove(os.path.join(folder, f))
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def civilians_step(folder, out, n=None, seed=7, log=print):
    """POST-STEP on a finished folder (after test() and the gun-sound step): n frightened civilians in Dog Days' own form, with F07's civilian model,
    into the NEW folder `out` (tools/kl_fa_civs.py add; this module never places a civilian itself). -> kl_fa_civs' report, or None for n == 0.
    GUESS: places = the navigation mesh's biggest part (the street, warehouse, diner), 150 apart; the 332-wide gap to the garage island is why the
    garage has none."""
    n = CIVILIANS if n is None else n
    if not n:
        return None
    import kl_fa_civs as C
    civs = C.plan_places(C.F.Built(folder, 'F01'), n, seed=seed)
    log('  kl_fa_v2_hotcoffee: civilians_step: %d of %d placed' % (len(civs), n))
    return C.add(folder, out, civs, 'F01', C.HOST, max_prm_growth=1 << 21, log=log)


def load_plan(folder):
    pj = os.path.join(folder, 'van.json')
    lay_van(plan_of(pj))


def main():
    global WITH_BOTS, NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, STREAM, GARAGE_BLAST, CIVILIANS
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        NO_AI = '--no-ai' in a
        WITH_BOTS = '--bots' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        GARAGE_BLAST = '--no-blast' not in a
        CIVILIANS = CIVILIANS if '--no-civilians' not in a else 0
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
        print('kl_fa_v2_hotcoffee.plan: %s (stop %s, board %s)' % (a[2], P['stop'], P['board']))
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']
        print('kl_fa_v2_hotcoffee.van-check %s: %d fault(s)' % (a[1], len(rep['faults'])))
        for x in rep['faults']:
            print('  ' + str(x))
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) in (3, 4) and a[0] == 'civilians':
        civilians_step(a[1], a[2], int(a[3]) if len(a) == 4 else None)
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
    import kl_fa_v2_hotcoffee
    kl_fa_v2_hotcoffee.main()
