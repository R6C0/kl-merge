"""kl_dig_layer.py - the FRAGILE ALLIANCE ROUND of 'The Dig' (map id DM07): Dog Days' F07 Fragile Alliance systems + Dead Men's M07_A
(Gravel Pit, 'Dig': the campaign mission in which Kane's daughter is killed). OFFLINE ONLY: built and checked, NEVER RUN IN THE GAME.
Design: re/dig_fa_design_1025.md (+ its section 12 critic corrections). Cut from tools/kl_fa_v2_park.py (the same author-layer
interface, the nine names of kl_graft.AUTHOR_NAMES) and from tools/kl_fa_blast.py (the round-start blast).

THE ROUND
  1. The crew starts in the PIT at the campaign's start (-2300, -454, 3000), rain, dusk, the 'Construction_Site' bed, calm start music.
  2. Round start + 9 s: a blast at the barricade in the trench north of the pit (z 1440): sound, fire, dust, camera shake (kl_fa_blast's
     six boxes re-placed, the pattern proven live on Retomoto), the barricade's intact model is hidden (GUESS: DeactivateGeom).
  3. FOUR police waves (F07's own four arrival squads, re-placed on M07's main navigation mesh; RunToCover / Defend / RandomTrigger / Flank
     as the squads' own children run them):
       wave 1  at the blast      from the north trench, through the broken barricade
       wave 2  crew in mid pit   from the west lane
       wave 3  crew on the south plateau (+ the alarm: the van, the action music)   from the east plateau
       wave 4  the van's alarm + 8 s     on the plateau, north of the van's lane (1025dig2; was the east terrace)
     The campaign's own squads, vans and roads are dropped by the campaign pre-pass; no vehicle delivers a wave (DEVIATION from the design).
  4. Loot: 11 briefcases at pipes, containers, the excavator on the pit floor, the mid pit and the south plateau (4,000,000 in all since 1025dig2).
  5. Escape (1025dig2): ONE way down, ONE way out. A van on the plateau's west end, one straight road along z 10400 (x -6000 .. 2400, y from the
     collision floor), stop (-2600, 401, 10400), boarding place 337 west of it; kl_map_escape plan with no fault (lin 3400, lout 4400). The two
     colonnade pillars are sunk 120 (kl_escape.OPEN M07_A): MEASURED on the built level, Pillar_F_08 is a collision slab x -4641..-4544, y 392..486 across the lane (lane() faults without the sink). Was: the east terrace road (x 2450), whose y 50 lay 350 under the ground.
  6. Music: the level's own PlayMusic groups (start, then V2 with its fades at the alarm) via campaign_names; ambience bed of the level.
Every number marked GUESS is a guess; MEASURED ones come from the real files (survey scripts, see re/open_work_log.md 2026-10-25).
Usage (from tools/):
  python kl_dig_layer.py test <out> [--keep] [--plan plan.json] [--no-ai] [--no-police] [--no-music] [--no-blast] [--str PC_Def.str]
  python kl_dig_layer.py plan <bare-folder> <plan.json>      the van's plan from a built bare graft
  python kl_dig_layer.py check <folder> | van-check <folder> | finish <folder>
"""
import collections, contextlib, math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms
import kl_prpjoin as J
import kl_fa_author as A
import kl_fa_bank as BK
import kl_map_escape as ESC

HOST, LEVEL = 'F07', 'M07_A'
TITLE = 'The Dig (Gravel Pit)'
R = 'ROOT\\'
HIDDEN = 0x400
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
KNOWN = ()
NO_AI = False                           # True ('--no-ai'): no police squad is placed or woken
POLICE_ARRIVE = True                    # False ('--no-police')
BLAST = True                            # False ('--no-blast'): the round starts without the barricade blast
VOICE = True
STREAM = None
MUSIC = True                            # False ('--no-music')
VAN_HIDE = True                         # the van's group hidden until the alarm (as Park II)
KEEP_FAKETARGET = False
VAN_SHOW = True
SQUADS = collections.OrderedDict()      # the campaign's squads: none (the pre-pass drops them; the cops are F07's)
SQUADS_AWAKE = False

# the campaign pre-pass keeps M07_A's Truckland bound (the only thing that closes the pit's far end); nothing else of the level is dropped here
# 1025dig2: nothing is dropped for the van's lane (z 10400): MEASURED round 2, lane() is clear once kl_escape.OPEN sinks Pillar_F_08/_05 by 120 (without: a slab at x -4600, y to 486, lin 660)
M_DROP = ()

FLAT = (0.0, -1.0)                      # facing: towards the blast (z falls to the north of the pit)
FACE_NORTH = FLAT
WEST, SOUTH = (-1.0, 0.0), (0.0, 1.0)


MAIN_POLY = 102                         # a polygon of the main navigation part (the START rows' polygon; part 1, 520 polygons; the Hero island is 2 polygons)


def snap_in(mesh, x, z, margin=30.0, far=300.0, part=None, y=None):
    """(x, y, z) ON the navigation mesh nearest to (x, z): the point itself when inside a polygon, else moved towards the nearest polygon's middle
    until it is inside by `margin`. y (round 2): only polygons whose middle is within 120 of y count (the pit is a bowl under the rim: without it a rim point
    snaps down to the pit floor). -> (point, how far it was moved). A move over `far` is an error (a table that missed the map).
    fix 1025b: ONLY polygons of the main part (`part`, default the part of MAIN_POLY) count: before, a point near the 2-polygon Hero island
    (TEAM_MERC) was snapped onto the island, which no way leads to."""
    part = mesh.part[MAIN_POLY] if part is None else part
    d, i = mesh.nearest(float(x), 0.0 if y is None else float(y), float(z), dy=1e9 if y is None else 120.0, part=part)
    if i is None:
        raise ValueError('kl_dig_layer: no navigation polygon near (%d, %d)' % (x, z))
    if mesh.inside(i, float(x), float(z)):
        return (float(x), float(mesh.height(i, x, z)), float(z)), 0.0
    mid = mesh.mid[i]
    for s in range(1, 101):
        px, pz = x + (mid[0] - x) * s / 100.0, z + (mid[2] - z) * s / 100.0
        if mesh.inside(i, px, pz) and math.hypot(px - x, pz - z) >= d + margin:
            if math.hypot(px - x, pz - z) > far:
                break
            return (px, float(mesh.height(i, px, pz)), pz), math.hypot(px - x, pz - z)
    raise ValueError('kl_dig_layer: (%d, %d) is %d from the navigation mesh (%d allowed)' % (x, z, d, far))


def snap_mesh(mesh, p):
    """p with the navigation mesh's height under it (p itself when the mesh has nothing there)."""
    hit = mesh.on(*[float(v) for v in p]) if mesh is not None else None
    return (float(p[0]), float(hit[1]), float(p[2])) if hit else (float(p[0]), float(p[1]), float(p[2]))


# ------------------------------------------------------------------ the pit, MEASURED on M07_A (gate-1 bare graft; mesh part 1 = main)
PIT_Y = -463.0                          # the mesh's height at the campaign's start (collision floor about -482)
# START: two rows of four, 80 apart, round the campaign's start, on mesh polygon 102 (MEASURED). GUESS: the rows
START = [(float(x), PIT_Y, float(z)) for z in (2940.0, 3060.0) for x in (-2420, -2340, -2260, -2180)]
# TRAITOR: four beside, 3 m north-west (polygon 103)
TRAITOR = [(float(x), -435.0, 3300.0) for x in (-2900, -2820, -2740, -2660)]
# fix 1025b: the old x -2600 / -2520 .. were two columns west of the START rows; (-2600, 3000) and (-2600, 3080) lay on the 2-polygon Hero island
# (part 5, x -2694 .. -2629) and snapped onto it. Now four columns on polygon 102, 80 apart, all 55 or more inside its west edge (x -2555)
TEAM_MERC = [(float(x), PIT_Y, float(z)) for z in (3000.0, 3080.0) for x in (-2500, -2420, -2340, -2260)]
STAGE_B = [(-2650.0 + dx, -564.0, 1100.0 + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]       # the trench, past the pit
STAGE_C = [(-1000.0 + dx, -182.0, 5600.0 + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]       # the mid pit
STAGE_D = [(-2300.0 + dx, 405.0, 9800.0 + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]          # 1025dig2: the plateau's west end, 600 south of the van's lane (was the east terrace). GUESS: the place
# the police who come back after a death. fix 1025b: they stood at z -3300 / -3420, NORTH of LevelBound_Truckland's Bound box (world z -3291 .. -2791),
# so the only way to the crew crossed the kill box. Now the car park's south part, polygon 546 (z -1270 .. 69, y about -700), 4000 .. 4400 from the START
# rows, south of every Truckland box (Warn01 ends at z -1911) and EAST of x -2165 (so also clear of the transposed reading of the boxes' half extents,
# which would put a wall at x -2665 .. -2165). Two rows, 125 apart. GUESS: the place; MEASURED (check()): on part 1, a mesh way to polygon 102 that never
# enters a Bound / Warn box, and a free walk.
AFTER_DEATH = [(float(x), -700.0, -900.0) for x in (-2000, -1875, -1750, -1625, -1500, -1375, -1250)]
BODIES = [(float(x), -700.0, -1100.0) for x in (-2000, -1872, -1744, -1616, -1488, -1360, -1232, -1104)]


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


# ------------------------------------------------------------------ the loot: 11 briefcases (where the case's underside lies, degrees, value, what)
# MEASURED: places beside the props (survey1.txt) moved onto the mesh, y = the collision floor there (kl_map_escape.Ground.under).
# 1025dig2: THE TOTAL IS 4,000,000 (was 1.85 million: pit 4 x 250,000 = 1,000,000; mid pit 3 x 300,000 = 900,000; plateau 500,000 + 500,000 + 550,000 + 550,000
# = 2,100,000). GUESS: every turn and value. The 2 plateau cases that lay over bare mud, far from any prop ((-1000, 10500): ON the van's lane; (300, 11000)), moved
# to the concrete pipes on the plateau's north side: (-1500, 11450) 100 from ConcretePipe_21 and (-3500, 11100) 100 from ConcretePipe_19 (MEASURED with
# kl_fa_loot.Floors.stand: reach 165, >= 100 to spare on the plateau flood from STAGE_D). Cases are the Dead Men briefcase (no yuan boxes in a gravel pit).
LOOT = [((x, y, z), yaw, value, what) for (x, y, z), yaw, value, what in [
    ((-697.0, -482.3, 2692.0), 20.0, 250000, 'pit: red pipes'),
    ((-1430.0, -543.4, 1702.0), -35.0, 250000, 'pit: red pipe, the trench mouth'),
    ((-3946.0, -482.3, 2643.0), 80.0, 250000, 'pit: pipe holders'),
    ((-1503.0, -496.2, 2471.0), 5.0, 250000, 'pit: the open container'),
    ((-1025.0, -276.3, 5984.0), 60.0, 300000, 'mid pit: red pipes'),
    ((-1025.0, -327.9, 5079.0), -20.0, 300000, 'mid pit: red pipes south'),
    ((-911.0, -189.6, 7355.0), 100.0, 300000, 'mid pit: the open container'),
    ((596.0, 421.3, 8696.0), 0.0, 500000, 'plateau: the open container'),
    ((-647.0, 404.0, 8903.0), 40.0, 500000, 'plateau: the excavator'),
    ((-1500.0, 397.5, 11450.0), -70.0, 550000, 'plateau: the concrete pipes east'),
    ((-3500.0, 410.0, 11100.0), 15.0, 550000, 'plateau: the concrete pipes west')]]
LOOT_TOTAL = 4000000                    # checked in prepare_host
LOOT_CLEAR = 400.0                      # every case at least this far from every START point (pickup reach is LOOT_REACH + 40; e5's number)
LOOT_REACH = 125.0                      # TriggerBox2 radius (kl_escape.REACH)
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, as the club's

# ------------------------------------------------------------------ the host's layer (F07)
PARK = (0.0, -60000.0, 0.0)
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyTop', '040_LevelBound_AlleyRight',
                                                         '040_LevelBound_AlleyLeft', '030_LevelBound_StreetRight', '030_LevelBound_StreetLeft')
          for b in ('Bound', 'Warn01', 'Warn02')]       # all 18: F07's alley bounds do not fit a pit (M07's own Truckland bound stays)
ENTER_AT, ENTER_HALF = (-2000.0, -350.0, 2400.0), (2100.0, 300.0, 900.0)          # the pit: the bots' first stage (START, 4 loot places inside)
EXIT_AT, EXIT_HALF = (-1000.0, 405.0, 10400.0), (1800.0, 200.0, 700.0)            # 1025dig2: the plateau's west half, round the van's stop (was a plane at the terrace). GUESS
WALK_BOX = ((-1020.0, -130.0, 5600.0), (700.0, 300.0, 700.0))                      # the mid pit (wave 2)
FLOOR_BOX = ((-1000.0, 150.0, 8000.0), (1300.0, 400.0, 500.0))                     # the south plateau's foot (wave 3, the alarm); 1025dig2: wider and 300 further south, so the alarm comes earlier. GUESS
BLAST_AT = (-2660.0, -560.0, 1440.0)                                              # MEASURED: SO0700_M07_Barikade_PRE_03 (the trench plug)
PLACE_FIXED = {
    'FASpecials!POI!Trigger_POI_TheLootArea': (ENTER_AT, None, ENTER_HALF, 'GUESS: the pit (it starts the loot marker\'s timer)'),
    'FASpecials!POI!POI_TheLootArea': ((ENTER_AT[0], ENTER_AT[1] + 80, ENTER_AT[2]), None, None, 'over the pit'),
    'FASpecials!PIP!EnterLootArea': (ENTER_AT, None, ENTER_HALF, 'the pit: AI heisters\' first stage is inside this box'),
    'FASpecials!PIP!ExitLootArea': (EXIT_AT, None, EXIT_HALF, 'GUESS: a plane at the terrace\'s south end, after the last loot'),
    'Specials!LevelSpeak!TriggerBox': ((-2400.0, 405.0, 10600.0), None, (900.0, 200.0, 500.0), 'GUESS (1025dig2): the plateau west end, by the van (the crew comes onto it)'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((-2400.0, 405.0, 10600.0), None, None, 'with its trigger box'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((-1500.0, -100.0, 3800.0), None, None, 'GUESS: over the pit'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((-2300.0, -450.0, 3000.0), None, None, 'the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((-2000.0, -300.0, 700.0), None, None, 'GUESS: the trench'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((-2650.0, -560.0, 1100.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((-2400.0, 100.0, 6200.0), None, None, 'GUESS: the mid pit'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((-1000.0, -180.0, 5600.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((-1200.0, 520.0, 9300.0), None, None, 'GUESS (1025dig2): over the plateau, looking west at the van stop'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((-2600.0, 401.0, 10400.0), None, None, 'the van stop (STOP)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((-900.0, -350.0, -1500.0), None, None, 'GUESS: over the car park, looking at the police rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((-1625.0, -690.0, -1000.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((-900.0, -350.0, -1500.0), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((-1625.0, -690.0, -1000.0), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these (GUESS: the trench, the mid pit, the terrace)
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': (STAGE_B[0], None, (250, 150, 250), 'GUESS: the trench'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': (STAGE_C[0], None, (300, 150, 250), 'GUESS: the mid pit'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': (STAGE_D[0], None, (300, 150, 250), 'GUESS: the plateau west end'),
    # jump points (developer aids): the round's stations
    'Specials!JumpPoints!01_Start': (START[1], FLAT, None, 'the pit'),
    'Specials!JumpPoints!02_MarketMain': (STAGE_B[0], FLAT, None, 'the trench'),
    'Specials!JumpPoints!03_MarketOrange': (STAGE_C[0], FLAT, None, 'the mid pit'),
    'Specials!JumpPoints!04_LootWarehouse': ((-1000.0, 400.0, 10500.0), FLAT, None, 'the plateau'),
    'Specials!JumpPoints!05_MarketGreen': (STAGE_D[0], FLAT, None, 'the plateau west end'),
}
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'start timer': FF + 'RivalMercs!Timer',                          # TriggerDelay2 START_AT -> the blast, wave 1, the ambient music
        'backstop': FF + 'RivalMercVan!Timer',                           # TriggerDelay2 BACKSTOP_AT -> wave 2, the gate, the van, whatever the crew did
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # TriggerBox in the mid pit -> wave 2
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # TriggerBox at the plateau's foot -> wave 3 (the gate), the alarm
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate',                  # GateGroup + two GatePath
        'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',            # ActivateGeom -> the van's group (the van is hidden until then)
        'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',       # TriggerDelay2 VAN_DELAY -> van on, wave 4, the alarm music
        'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator',   # DeactivateGeom -> the van's group again (round 2)
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
GATE_WAYS = ('Way#01', 'Way#02')
# THE LEVEL'S OWN MUSIC: the PlayMusic groups of M07_A's 'Special!Music' stay (campaign_names) and the layer's lists start them.
#   round start (start timer)  'PlayMusic_start' (Gravel_Pit_START, calm; its Layer1 fade-out box is the campaign's own '2 s to -100 dB')
#   the alarm (van timer)      'PlayMusicV2' (Layer_A_V2) + its '02_Layer2' fade (to -6 dB in 3 s) + the start music's Layer1 fade-out
# GUESS: a second PlayMusic does not stop the first, so the start music is faded out by hand (the campaign does the same).
# The clips need the stream file (kl_v2_str.SETS['M07_A']).
MUSIC_AMBIENT, MUSIC_ACTION = 'Special!Music!PlayMusic_start', 'Special!Music!PlayMusicV2'
MUSIC_NAMES = (MUSIC_AMBIENT, MUSIC_ACTION)
MUSIC_ALARM = (MUSIC_ACTION + '\\02_Layer2', MUSIC_AMBIENT + '\\Layer1')
START_AT = 9.0                          # s from the round-start event: the blast, wave 1, the music. GUESS (Retomoto: 9 s)
BACKSTOP_AT = 210.0                     # s from the round-start event: waves 2 and 3, the van, whatever the crew did. GUESS
VAN_DELAY = 8.0                         # s from the alarm to the van's show and wave 4. GUESS
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R', 18: 'Multiplayer/F09/MissionReminder_02_R', 19: 'Multiplayer/F06/MissionReminder_01_R',
         20: 'Multiplayer/F06/ReachlootArea_01_R', 127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
         136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
START_KEY = 'AllLevels/Interface/Online/GameStart/M07A_%s_Start'
TEXTS = {START_KEY % 'FA': 'The barricade blows. Grab the cases in the pit, the mid pit and on the plateau; the police come in waves. When the alarm sounds the van drives to the west end of the plateau: get in.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'The barricade blows. Grab the cases in the pit, the mid pit and on the plateau; the police come in waves. When the alarm sounds the van drives to the west end of the plateau: get in.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}

# ------------------------------------------------------------------ the van on the east terrace (MEASURED plan, zero faults: kl_map_escape.van_plan_points)
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'
# 1025dig2: the van waits at the plateau's WEST end and the road is one straight line along z 10400 (x -6000 .. 2400), the y of each way point the collision floor
# there (MEASURED, Ground.hits; the old y 50 was 350 under the ground: ~1900 boarding refusals). at='origin': STOP is the van's origin, the rear box (boarding
# place) 337 west of it. The plan has zero faults as the bare graft stands (round 2 MEASURED: z 10800 has 2 faults, lin 640 / lout 2150); lin 3400, lout 4400.
STOP = (-2600.0, 401.0, 10400.0)
ROAD = dict(arrive=[(-6000.0, 393.0, 10400.0), (-5700.0, 401.0, 10400.0), (-5400.0, 406.0, 10400.0), (-5100.0, 403.0, 10400.0), (-4800.0, 401.0, 10400.0),
                    (-4500.0, 400.0, 10400.0), (-4200.0, 399.0, 10400.0), (-3900.0, 392.0, 10400.0), (-3600.0, 393.0, 10400.0), (-3300.0, 401.0, 10400.0),
                    (-3000.0, 406.0, 10400.0)], stop=STOP,
            leave=[(-2400.0, 401.0, 10400.0), (-2100.0, 400.0, 10400.0), (-1800.0, 399.0, 10400.0), (-1500.0, 392.0, 10400.0), (-1200.0, 393.0, 10400.0),
                   (-900.0, 401.0, 10400.0), (-600.0, 406.0, 10400.0), (-300.0, 403.0, 10400.0), (0.0, 401.0, 10400.0), (300.0, 400.0, 10400.0),
                   (600.0, 399.0, 10400.0), (900.0, 392.0, 10400.0), (1200.0, 393.0, 10400.0), (1500.0, 401.0, 10400.0), (1800.0, 406.0, 10400.0),
                   (2100.0, 403.0, 10400.0), (2400.0, 401.0, 10400.0)], at='origin', heading=None,
            cam=(-2200.0, 560.0, 9600.0))                           # GUESS: the escape camera's eye, over the lane's south side, looking at the stop and the way out
PLAN = None
NO_PLAN = 'kl_dig_layer: the van has no plan: build with \'kl_dig_layer.py test <out>\' or kl_dig_layer.build()'
BOARD_AT = (-2937.0, 402.0, 10400.0)    # the rear doors of the standing van (MEASURED by the plan: 337 west of STOP; prepare_host takes PLAN['board'] once there is a plan)
LANE_CLEAR = 250.0                      # no spawn point, man, cover point or the marker nearer than this to the van's drive. GUESS
BOARD_CLEAR = 500.0                     # no cover point of the police nearer than this to the boarding place
FED_CLEAR = 1000.0                      # no AFTER_DEATH point or police body nearer than this to the boarding place
POLICE_CLEAR = BK.POLICE_CLEAR
BOUND_AFTER = 1000.0
BOARD_NEAR = 30.0
CIVILIANS = 0                            # none (the stock FA civilians are a post-step: civilians_step)

# F07's police squads, four waves. name -> [anchor, men, cover, defend] as (x, z); y from the mesh at prepare time (snap_in). GUESS: every place.
#   men: where they appear; cover: the points of RunToCover; defend: the Defend post; anchor: the squad group's own place (RunToEscape)
# All 460 or more outside the van's line (x 2450); wave 1 behind the barricade, wave 2 in the west lane, wave 3 on the plateau, wave 4 on the terrace.
G30 = 'Gameplay!030_AfterLoot!'
WAVES = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-2700, 300), [(-2900, 439), (-2863, 18), (-2900, 260)], [(-2700, 1750), (-2600, 1800), (-2800, 1800)], (-2650, 1750))),
    # fix 1025b: the men were at (-5000, 4000) / (-5000, 4300), (-5000, 4000) in sight of the START rows (28 m); now 450 / 500 further east and
    # south in the west lane, out of sight of every START / TEAM_MERC / TRAITOR row (kl_dig_layer.sight_report: exact rays, eye 160, target 120 and 175)
    (G30 + '030_FinancialAlleyExitStreet_Left', ((-4450, 4500), [(-4450, 4350), (-4450, 4650)], [(-3957, 4157), (-3996, 4511)], (-3982, 4139))),
    # 1025dig2: the van's lane runs along z 10400 now, so wave 3 stood on it: moved 800 south (men 600+ off the lane). GUESS
    (G30 + '030_FinancialAlleyExit_Right', ((1500, 9700), [(1500, 9700), (1600, 9600), (1700, 9500)], [(200, 9800), (300, 9700), (400, 9600)], (300, 9800))),
    # 1025dig2: wave 4 (the van's) came to the east terrace; now it comes onto the plateau, NORTH of the van's lane (men 800 off, cover 450 .. 550 off). GUESS
    (G30 + '030_FinancialAlleyExitStreet_Right', ((-1800, 11200), [(-1800, 11200), (-1700, 11250)], [(-2200, 10900), (-2000, 10850)], (-2000, 10900)))])
WAVE_NAMES = tuple(WAVES)
# FIVE MORE of F07's police squads (the loot-phase ones: 2 + 2 + 2 + 3 + 1 men, each with a 10_ and a 20_RunToCover and a 40_RunToEscape post), re-placed
# round a centre with the same rules and woken with the wave named. Their places are generated: men within RADIUS/2 of the centre, cover points on a ring of
# RADIUS round it, every point snapped onto the main mesh. GUESS: centres, radii, the wave each joins (10_RunToCover is the rout that wakes the squad).
G20 = 'Gameplay!020_Loot!'
EXTRA = collections.OrderedDict([
    (G20 + '020_FinancialAlley_LeftFurther', (1, (-2950, 800), 260)),         # wave 1: the trench behind the barricade, west of the dog
    # fix 1025b: RunForDumpster's men stood at (-1500, 4750 / 5050) and LeftParking's first at (-3561, 4240), 17 .. 21 m from the START rows and in their
    # line of sight while asleep. Now the nearest centres whose men are out of sight of every START / TEAM_MERC / TRAITOR row (kl_dig_layer.sight_report)
    (G20 + '020_FinancialAlley_RunForDumpster', (2, (-300, 5050), 300)),      # wave 2: the mid pit's east rim (behind the rim from the pit)
    (G20 + '020_FinancialAlley_LeftParking', (2, (-3400, 4450), 300)),        # wave 2: the west lane
    (G20 + '020_FinancialAlley_RightPlatform', (3, (250, 9750), 350)),        # wave 3: the east plateau
    (G20 + '020_FinancialAlley_RightGround', (4, (1500, 11000), 250)),
    # 1025dig2 round 2: the three police squads F07 has left (each with a 10_RunToCover). The design's rim posts (RIM_A (-3300, 3500), RIM_B (-700, 3900)) are
    # MEASURED impossible: the mesh has no polygon on the west rim above the pit floor and the terrace (y 50) starts at x -400; the two terrace places below are
    # the nearest that are out of sight of every START / TEAM_MERC / TRAITOR row (rim1.py, exact casts; every terrace place nearer the pit is in sight). They
    # cover the mid pit's east rim (wave 2) and the climb to the plateau (wave 3). y = the terrace's mesh height (snap_in y). GUESS: every place
    (G30 + '030_FinancialAlleyExitSkywalk', (2, (-250, 5600), 110, 50.0)),         # RIM_A: 2 men, the terrace over the mid pit
    # EntranceLeft (1 man, plateau SW corner (-3300, 400, 8900)) was tried and FAILED the sight check: in sight of the spawn row across the pit, 60.9 m. Dropped.
    ('Gameplay!040_Escape!040_EscapeEntranceRight', (3, (290, 6680), 110, 50.0))])                                         # RIM_B: 2 men, the terrace over the climb
EXTRA_PLACED = {}                       # name -> [(kind, [points])], filled by place_extra for the check
# ONE POLICE DOG: F07's own squad 'Gameplay!020_Loot!021_FinancialAlley_Dog' (ZSquadScript parked, DefendBehaviour + Pos#01, Dog group with the
# ZFFActor 'eDog'; nodes 123..128, every child stands at a world place). Re-placed: it waits in the trench behind the barricade and runs to the crew's start
# when the round-start timer releases it (the stock release, the box 'tbReleaseDog', is parked away). GUESS: place, release time; UNPROVEN in the game.
DOG = 'Gameplay!020_Loot!021_FinancialAlley_Dog'
DOG_PARK = (-2700.0, 900.0)             # the trench, 540 behind the barricade (z 1440). Snapped onto the mesh
DOG_POST = (-2300.0, 2950.0)            # the START rows (the Defend post: the dog runs here and attacks what it meets)
DOG_ON = True                           # False ('--no-dog')
EXTRA_ON = True                         # False ('--no-extra'): the five loot-phase squads
ARRIVE_START = '10_RunToCover'
ARRIVE = collections.OrderedDict()      # filled by lay_police(mesh): the same shape as the park's ARRIVE: name -> (anchor, men, cover, defend), (x, y, z)


def lay_police(mesh, log=print):
    """ARRIVE from WAVES, every place moved onto the navigation mesh (snap_in); the shifts are logged."""
    ARRIVE.clear()
    moved = []
    for name, (anchor, men, cover, defend) in WAVES.items():
        def s(xz):
            p, sh = snap_in(mesh, xz[0], xz[1])
            if sh > 1.0:
                moved.append(int(sh))
            return p
        ARRIVE[name] = (s(anchor), [s(q) for q in men], [s(q) for q in cover], s(defend))
    log('  kl_dig_layer: %d police places laid on the mesh, %d moved (largest %d)' % (sum(2 + len(v[1]) + len(v[2]) for v in ARRIVE.values()), len(moved), max(moved or [0])))
    return ARRIVE


def _lay_const():
    """ARRIVE with the table's own (x, z) and y 0 until prepare_host lays it on the mesh: names (KEEP) are what is needed before that."""
    if not ARRIVE:
        for name, (anchor, men, cover, defend) in WAVES.items():
            f = lambda q: (float(q[0]), 0.0, float(q[1]))
            ARRIVE[name] = (f(anchor), [f(q) for q in men], [f(q) for q in cover], f(defend))
_lay_const()

ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
import kl_fa_blast as KB
BLAST_KEEP = tuple(v[0] for v in KB.PLAN.values()) if BLAST else ()
_KEEP = ('FASpecials!', 'Specials!', VAN, DOG) + ESCAPE + BLAST_KEEP + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))


def police():
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def extra():
    return EXTRA if POLICE_ARRIVE and not NO_AI and EXTRA_ON else {}


def __getattr__(name):
    if name == 'KEEP':
        return _KEEP + tuple(x for x in list(police()) + list(extra()) if x not in _KEEP)
    raise AttributeError(name)


DROP = ('Specials!CoverPoints!*',)      # M07_A's own cover list stays (Special!CoverPoints!CoverControl); a second FFCoverList is an assert in its init
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout', 'GateGroup', 'GatePath', 'DeactivateGeom', 'Filter'}
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
SQUAD_ACTIVE = A.SQUAD_ACTIVE
MAN_OFF, MAN_IN = 60.0, 15.0
MEN = collections.OrderedDict()
SHATTER = None


# ------------------------------------------------------------------ 1. the host level before the graft
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT bare F07 + M07_A folder. A fault is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_dig_layer: no van on ROAD: %s' % '; '.join(P['faults']))
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
    mark = (b[0], b[1] + 188.0, b[2] - 350.0)                                          # 1025dig2: the drive runs along x now; the marker 350 south of it (the loot side). GUESS
    box = ((b[0], b[1] + 200.0, b[2]), None, (450.0, 300.0, 450.0), 'GUESS: round the van\'s boarding place on the terrace')
    t['Gameplay!EscapeSetup!otrExitLevel'] = box
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    t['FASpecials!POI!POI_TheEscapeArea'] = (mark, None, None, 'beside the boarding place')
    t['Specials!JumpPoints!06_Exit'] = ((b[0], b[1], b[2]), SOUTH, None, 'the boarding place')
    t[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the mid pit')
    t[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the south plateau\'s foot')
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
        log('  kl_dig_layer: the police that arrive: %d of F07\'s squads re-placed (%d men) on the navigation mesh' % (len(out), sum(n for _s, n in out)))
    return out


def squad_plan():
    """The campaign's squads that stay: none (the Dig's police are F07's own squads, re-placed)."""
    return {}, {'*': 'the campaign pre-pass drops them; the round has F07 police'}


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the Dig. S: kl_graft.Level('F07'), unedited."""
    import kl_route
    sc = S.prp
    if PLAN is None:
        raise ValueError(NO_PLAN)
    mesh = kl_route.load(LEVEL).mesh()
    moved = []
    for tbl in (START, TRAITOR, TEAM_MERC, STAGE_B, STAGE_C, STAGE_D, AFTER_DEATH, BODIES):   # on the mesh (the tables hold guesses)
        new = []
        for p in tbl:
            q, sh = snap_in(mesh, p[0], p[2])
            new.append(q)
            if sh > 1.0:
                moved.append(int(sh))
        tbl[:] = new
    log('  kl_dig_layer: spawn tables laid on the mesh: %d points moved (largest %d)' % (len(moved), max(moved or [0])))
    lay_police(mesh, log)
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
            pts, face = (START, SOUTH) if crook else (BODIES, BOARD_AT)
            p = pts[seen[crook, 'hero'] % len(pts)]
            A.place(S, t, p, facing(p, face))
            seen[crook, 'hero'] += 1
    log('  kl_dig_layer: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
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
    if sum(v for _p, _y, v, _w in LOOT) != LOOT_TOTAL:
        raise ValueError('kl_dig_layer: the loot adds up to %d, not %d' % (sum(v for _p, _y, v, _w in LOOT), LOOT_TOTAL))
    by = collections.Counter(what.split(':')[0] for _p, _y, _v, what in LOOT)
    log('  kl_dig_layer: loot: %d objects, %d in all: %s' % (len(LOOT), sum(v for _p, _y, v, _w in LOOT), dict(by)))
    place_police(S, log)
    if extra():
        place_extra(S, mesh, log)
    if DOG_ON and not NO_AI:
        dog_host(S, mesh, log)
    if BLAST:
        blast_host(S, log)
    S.van = ESC.van_prepare(S, PLAN, log)
    # the van is NOT in the world until the alarm (the club's VAN_LATE: no FakeTarget, hidden from the load)
    vg = A.node_of(sc, van_path()[len(R):])
    gone = [] if KEEP_FAKETARGET else [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
    if KEEP_FAKETARGET:
        log('  kl_dig_layer: the van\'s FakeTarget is KEPT (--keep-faketarget)')
    for k in gone:
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
    if VAN_HIDE:
        A.place(S, vg, hidden=True)
        log('  kl_dig_layer: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; the alarm shows it' % len(gone))
    else:
        log('  kl_dig_layer: the van\'s FakeTarget (%d) is taken off; its group is NOT hidden (--no-van-hide)' % len(gone))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(place_now()['FASpecials!POI!POI_TheEscapeArea'][0])[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_dig_layer: the escape marker is %d from the van\'s drive (%d wanted)' % (off, LANE_CLEAR))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M07_A the campaign pre-pass must leave in: the two PlayMusic groups."""
    if level != LEVEL:
        return ()
    return MUSIC_NAMES if MUSIC else ()


def strip(M, log=print):
    """On the converted Dead Men level, before the join: nothing to do (no campaign squad stays)."""
    return 0


# ------------------------------------------------------------------ 3. the joined scene
# ------------------------------------------------------------------ the barricade blast (kl_fa_blast's six boxes, re-placed at the trench plug)
# GUESS: the pattern is Retomoto's (proven live there: sound, fire, dust, shake); here it sits on the barricade 'SO0700_M07_Barikade_PRE_03'
# (-2660, -575, 1440; the plug spans x -3250 .. -2126) and blows towards the pit (+z). The barricade's own Whole_01 object holds HavokShatter + SmashActivate
# (it shatters when a car rams it); whether an Explode of reach 600 breaks it is UNPROVEN, so the 'second' box is the real one (reach 600 / 400, f4 3000
# = the campaign's own BombWindow03 values) and fires 0.4 s after the fan. Nobody stands within 1100 of it at +9 s.
BZ = BLAST_AT[2]
TOWARD = [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0]        # ZGEOM[1] with local +Y -> world +z, +Z -> up (checked: X x Y = Z)
BLAST_PLAN = collections.OrderedDict([
    ('fan', (-2660.0, -480.0, BZ - 150.0, KB.UP, None)),
    ('cloud', (-2660.0, -560.0, BZ + 120.0, KB.UP, 'fire')),
    ('spray', (-2660.0, -540.0, BZ, TOWARD, 'spray')),
    ('glass s', (-2900.0, -500.0, BZ, TOWARD, 'dust')),
    ('glass n', (-2420.0, -500.0, BZ, TOWARD, 'dust')),
    ('second', (-2660.0, -520.0, BZ - 60.0, KB.UP, 'spray'))])
BARRICADE_REACH = (600.0, 400.0, 3000.0)


def place_extra(S, mesh, log=print):
    """EXTRA's squads onto the mesh: the squad group at the centre, its children (men, cover points, the escape post) at generated mesh places."""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    up = lambda q: (q[0], q[1] + 1.0, q[2])
    for name, (_wave, (cx, cz), rad, *yy) in extra().items():
        yh = yy[0] if yy else None
        top = A.node_of(sc, name)
        if not kl_fa.has(sc, top, 'ZSquadScript') or not sc.resolve(R + name + chr(92) + ARRIVE_START):
            raise ValueError('%s: not a squad group with a %s' % (name, ARRIVE_START))
        own = []
        def go(k):
            for c in range(k + 1, sc.end[k]):
                if sc.parent[c] == k:
                    own.append(c) if any(abs(v) > 0.5 for v in tr(c)) else go(c)
        go(top)
        by = collections.defaultdict(list)
        for k in own:
            by['men' if any(sc.cls(c) == 'ZFFActor' for c in range(k, sc.end[k])) else sc.names[sc.parent[k]]].append(k)
        at, _ = snap_in(mesh, cx, cz, y=yh)
        at = up(at)
        A.place(S, top, at)
        got = []
        for kind, ks in sorted(by.items()):
            for i, k in enumerate(ks):
                r, a = (rad * 0.5 if kind == 'men' else rad), 2.0 * math.pi * (i + (0.5 if kind == 'men' else 0.0)) / max(1, len(ks))
                q, _sh = snap_in(mesh, cx + r * math.cos(a), cz + r * math.sin(a), y=yh) if kind != '40_RunToEscape' else (at, 0.0)
                q = up(q)
                A.place(S, k, tuple(q[j] - at[j] for j in range(3)))
                got.append((kind, q))
        EXTRA_PLACED[name] = got
        out.append((name, len(by['men'])))
    if out:
        log('  kl_dig_layer: %d more of F07 police squads re-placed (%d men): %s' % (len(out), sum(n for _s, n in out), ', '.join('%s %d' % (s.split('_')[-1], n) for s, n in out)))
    return out


def dog_host(S, mesh, log=print):
    """F07's stock dog squad re-placed: the Dog group at DOG_PARK, the Defend post at DOG_POST, the release box parked away. Heights from the mesh."""
    sc = S.prp
    bs = chr(92)
    park, _ = snap_in(mesh, *DOG_PARK)
    post, _ = snap_in(mesh, *DOG_POST)
    for rel, at in ((bs + 'Dog', park), (bs + 'DefendBehaviour' + bs + 'Pos#01', post), ('', (0.0, 0.0, 0.0))):      # the top at the origin: the children hold world places (kl_dog_1025's convention)
        A.place(S, A.node_of(sc, DOG + rel), at)
    A.place(S, A.node_of(sc, DOG + bs + 'tbReleaseDog'), PARK)
    log('  kl_dig_layer: the police dog waits at (%d, %d, %d), its Defend post (%d, %d, %d); release box parked' % (*park, *post))


def blast_host(S, log=print):
    """Re-place kl_fa_blast's six spare F07 boxes at the barricade and dress them. S after the rest of prepare_host."""
    sc = S.prp
    if getattr(S, 'blast', None):
        return S.blast
    KB.SECOND = 0.4
    KB.BLAST = 1.0
    for role, (x, y, z, m9, cl) in BLAST_PLAN.items():       # kl_fa_blast.PLAN is module state: set the Dig's places and clusters
        name = KB.PLAN[role][0]
        KB.PLAN[role] = (name, (x, y, z), m9, cl, 'the Dig barricade')
    for role, v in KB.PLAN.items():
        k = A.node_of(sc, v[0])
        if sc.parent[k] != 0 or sc.end[k] - k != 1 or sc.cls(k) != 'ZBoxPrimitive':
            raise ValueError('%s is not a single top-level ZBoxPrimitive' % v[0])
        KB.place(S, k, v[1], v[2])
    done = KB.dress(sc)
    sec = done['second']
    def fn(us):
        A.setv(sc, us, KB.E_REACH, BARRICADE_REACH[0])
        A.setv(sc, us, KB.E_INNER, BARRICADE_REACH[1])
        A.setv(sc, us, KB.E_F4, BARRICADE_REACH[2])
    kl_fa.edit(sc, sec, 0, fn)
    gone = KB.scrub(sc, [R + n for n in KB.KEEP], but={done['fan']})
    S.blast = {'boxes': done, 'scrubbed': gone}
    log('  kl_dig_layer: blast: %d boxes at the barricade (%d, %d, %d); %d old references removed' % (len(done), BLAST_AT[0], BLAST_AT[1], BLAST_AT[2], sum(n for _k, n in gone)))
    return S.blast


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_dig_layer: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    left = [sc.names[t] for t in sc.tops() if sc.names[t].startswith(('Boundaries!',))]
    if left:
        raise ValueError('kl_dig_layer: the campaign\'s own bounds are in the build: %s' % left)
    # the four waves: the squad's RunToCover rout is what wakes the squad (the same list a GatePath f0 holds)
    names = list(police())
    arrive = must([R + n + '\\' + ARRIVE_START for n in names])
    more = collections.defaultdict(list)
    for n, (w, *_cr) in extra().items():
        more[w] += must([R + n + '\\' + ARRIVE_START])
    wave = {i + 1: arrive[i] for i in range(len(arrive))} if len(arrive) == 4 else {}
    wavex = lambda w: ([wave[w]] if wave else []) + more[w]
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    put_(sc.resolve(ways[0])[0], 'GatePath', f0=wavex(3))       # wave 3 through the gate, wave 4 through the second path
    put_(sc.resolve(ways[1])[0], 'GatePath', f0=wavex(4))
    tune = [R + MUSIC_AMBIENT] if MUSIC else []
    alarm = must([R + n for n in (MUSIC_ACTION,) + MUSIC_ALARM]) if MUSIC else []
    if MUSIC:
        must(tune)
        for n in MUSIC_NAMES:
            if not kl_fa.has(sc, node(n), 'PlayMusic'):
                raise ValueError('%s is not a PlayMusic' % n)
        for p in alarm[1:]:
            if not kl_fa.has(sc, sc.resolve(p)[0], 'PlayMusicLayerFade'):
                raise ValueError('%s is not a PlayMusicLayerFade' % p)
    fan = [R + KB.PLAN['fan'][0]] if BLAST else []
    dog = [R + DOG + chr(92) + 'DefendBehaviour'] if DOG_ON and not NO_AI else []
    if dog:
        must(dog)
    lists('start timer', 'TriggerDelay2', f0=START_AT, f4=fan + wavex(1) + dog + tune)
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=wavex(2))
    # the plateau's foot: wave 3 (through the gate) and the alarm (the van's timer: the van, wave 4 through the second path, the action music)
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
        raise ValueError('kl_dig_layer: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    if BLAST:
        stray = KB.scrub(sc, [R + n for n in KB.KEEP], but={node(ROLE['start timer']), node(KB.PLAN['fan'][0])})
        if stray:
            log('  kl_dig_layer: %d stray references to the blast boxes removed' % sum(n for _k, n in stray))
    log('  kl_dig_layer: wired: %d police waves; start +%.0f s -> blast %s + wave 1 + music; mid pit box -> wave 2; plateau foot -> wave 3 + the alarm (+%.0f s: '
        'van, exit line, wave 4, action music); backstop %.0f s' % (len(wave), START_AT, 'on' if BLAST else 'off', VAN_DELAY, BACKSTOP_AT))
    return {'arrive': arrive, 'ways': ways}


def layer_names(sc):
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    return True


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
        log('  kl_dig_layer: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_dig_layer: %s: the loot already shows models of its own: left as it is' % folder)
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
    log('  kl_dig_layer: %d text keys in %d languages; settings fields %s name the start windows' % (len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ build and check
def build(out, log=print, plan=None):
    """F07 + M07_A with the layer into <out>/F07+M07_A campaign -> (kl_maps.one's result, that folder, the van's plan, kl_map_escape's report).
    plan None = made here on a BARE graft (<out>/_bare, deleted again)."""
    import shutil, kl_snd
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', m_drop=M_DROP)
        try:
            if not r.get('ok'):
                raise ValueError('kl_dig_layer: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    kl_snd.VOICE = True if VOICE else None
    try:
        with ESC.van_layer(plan, log) as st:
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_dig_layer', m_drop=M_DROP)
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
    box's own x, y, z (rotated into the world by BK.world_of). Parked boxes (y under -50000, F07's alley bounds) are left out. (fix 1025b)"""
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


def way_proof(mesh, p, boxes, goal=None):
    """Mesh.way (the AI's line, no shared edge under PORTAL wide) from the polygon under p to `goal` (default MAIN_POLY), sampled every 25
    -> (ok, why, length): ok when it exists, p is on the main part, and no sample stands in a box (plan test, 120 slack in y)."""
    goal = MAIN_POLY if goal is None else goal
    d, i = mesh.nearest(p[0], p[1], p[2], dy=300.0, part=mesh.part[MAIN_POLY])
    if i is None or d > 60.0:
        return False, 'not on the main part (%s from it)' % d, 0.0
    w = mesh.way(i, goal)
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
    if any(sc.names[t].startswith('Boundaries!') or 'LevelBound_StairsBottom' in sc.names[t] for t in sc.tops()):
        fail('the campaign\'s own bound objects are in the level (M_DROP)')
    # ---- the loot: 15 objects, the values, each on the navigation mesh
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
    starts = [pos[ents[t - 1]] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and 'START' in kl_fa.node_values(sc, t)[8]]
    if starts and loot:
        near = min((math.dist(pos[ents[k - 1]], q), sc.names[k]) for k, _v in loot for q in starts)
        log('  loot to START: nearest pair %d apart (%s; %d wanted)' % (near[0], near[1], LOOT_CLEAR))
        for k, _v in loot:
            d = min(math.dist(pos[ents[k - 1]], q) for q in starts)
            if d < LOOT_CLEAR:
                fail('loot %s is %d from a START point (%d wanted: a crew at spawn would drain it)' % (sc.names[k], d, LOOT_CLEAR))
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
        len(men), len(squads), len(SQUADS) if not NO_AI else 0, len(police()) + len(extra()), off))
    if not NO_AI:
        for n in SQUADS:
            kk = sc.resolve(R + n)
            if not kk:
                fail('squad %s is not in the level' % n)
                continue
            if values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE] != (1 if SQUADS_AWAKE else 0):
                fail('squad %s: field %d is %r' % (n, SQUAD_ACTIVE, values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE]))
    # ---- fix 1025b: level bounds, the police's way, the Hero island, sight
    boxes = bound_boxes(sc, ents)
    log('  level bounds: %d boxes' % len(boxes))
    mainp = mesh.part[MAIN_POLY]
    def part_of(p):
        h = mesh.on(*p)
        if h is not None:
            return mesh.part[h[0]]
        d, i = mesh.nearest(*p)
        return mesh.part[i] if i is not None and d <= 60.0 else None
    nway, longest = 0, 0.0
    for t in sc.tops():
        if sc.cls(t) != 'ZSpawnPoint':
            continue
        kind = kl_fa.node_values(sc, t)[8]
        p = pos[ents[t - 1]]
        if part_of(p) != mainp:
            fail('spawn point %s (%s) at (%d, %d, %d) is not on the main mesh part (Hero island or off the mesh)' % (sc.names[t], kind[-12:], *p))
        for name, lo, hi in boxes:
            if in_plan_box((p[0], p[1] + 50.0, p[2]), lo, hi, 0.0):
                fail('spawn point %s (%s) at (%d, %d, %d) stands inside %s' % (sc.names[t], kind[-12:], *p, name))
        if 'AFTER_DEATH' in kind or 'POLICE' in kind or 'BODIES' in kind:
            ok, why, ln = way_proof(mesh, p, boxes)
            nway += 1
            longest = max(longest, ln)
            if not ok:
                fail('police spawn point %s (%s) at (%d, %d, %d): %s' % (sc.names[t], kind[-12:], *p, why))
    log('  police spawn points: %d mesh ways to polygon %d, none enters a bound or warn box (longest %d)' % (nway, MAIN_POLY, longest))
    rows = [pos[ents[t - 1]] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and kl_fa.node_values(sc, t)[8].endswith(('_START', 'TEAM_MERC', '_TRAITOR'))]      # the crew's first places (not stage B / C / D, whose men wake with their stage)
    C = None
    try:
        sp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'third_party', 'anp', 'scripts')
        if sp not in sys.path:
            sys.path.insert(0, sp)
        import hvk_ray
        C = hvk_ray.Collision(arch)
    except Exception as e:
        fail('sight test: cannot load hvk_ray / collision (%s)' % e)
    nseen = ntest = 0
    for k in men:
        if 'merc_bot_squad' in sc.path[k]:
            continue
        p = pos[ents[sc.parent[k] - 1]]
        ntest += 1
        for name, lo, hi in boxes:
            if in_plan_box((p[0], p[1] + 50.0, p[2]), lo, hi, 0.0):
                fail('man %s at (%d, %d, %d) stands inside %s' % (sc.path[k], *p, name))
        if part_of(p) != mainp:
            fail('man %s at (%d, %d, %d) is not on the main mesh part' % (sc.path[k], *p))
        sn = seen_from(C, rows, p) if C else None
        if sn:
            nseen += 1
            fail('man %s at (%d, %d, %d) is in sight of the spawn row (%d, %d, %d), mask %#x, %.1f m' % (sc.path[k][-40:], *p, *sn[0], sn[1], math.dist(sn[0], p) / 100))
    log('  sight: %d policemen / dogs from %d START / TEAM_MERC / TRAITOR places, exact casts masks %s: %d in sight' % (ntest, len(rows), '/'.join('%#x' % m for m in SIGHT_MASKS), nseen))
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
        # ---- round 2 (design C1 / C2, the checks the verifier found missing): the boarding place against the stop, the ground, the boxes, the cover
        stop, bx = PLAN['stop'], (b[0], b[1] + 200.0, b[2])
        if math.hypot(b[0] - BOARD_AT[0], b[2] - BOARD_AT[2]) > BOARD_NEAR or abs(b[1] - BOARD_AT[1]) > 40.0:
            fail('the plan boarding place (%d, %d, %d) is not within %d (x/z) / 40 (y) of BOARD_AT %s' % (*b, BOARD_NEAR, BOARD_AT))
        back = math.hypot(stop[0] - b[0], stop[2] - b[2])
        if abs(back - ESC.BOARD_BACK) > BOARD_NEAR:
            fail('the boarding place is %d from the van origin, the rear box should be %d behind it (%d allowed)' % (back, ESC.BOARD_BACK, BOARD_NEAR))
        try:
            LV = ESC.Level(folder)
            GR = ESC.Ground(LV)
            for what, q in (('stop', stop), ('board', b)):
                u = GR.under(q[0], q[1], q[2])
                if u is None or abs(u[0] - q[1]) > 5.0:
                    fail('the van %s y %.0f is %s from the collision floor (5 allowed)' % (what, q[1], 'no floor' if u is None else '%.0f' % abs(u[0] - q[1])))
                else:
                    log('  van: %s y %.1f, floor %.1f (%s)' % (what, q[1], u[0], LV.name(u[1])[-34:]))
        except Exception as e:
            fail('van floor test: cannot load the collision (%s)' % e)
        ex_at = pos[ents[ex[0][0] - 1]] if ex else None
        if ex_at is None or math.dist(ex_at, bx) > 100.0:
            fail('the exit box is not on the boarding place (%s against %s)' % (ex_at, bx))
        nb = mesh.nearest(bx[0], b[1], bx[2], dy=300.0, part=mainp)
        if nb[1] is None or nb[0] > 100.0:
            fail('the boarding box centre is %s from a main-part polygon (100 allowed)' % nb[0])
        near_cov = []
        for k in range(1, len(sc.names)):
            pa = sc.parent[k]
            if pa and sc.names[pa].endswith('RunToCover') and sc.path[k].startswith(R + 'Gameplay!0') and 'merc_bot' not in sc.path[k]:
                near_cov.append((math.hypot(pos[ents[k - 1]][0] - b[0], pos[ents[k - 1]][2] - b[2]), sc.path[k][-44:]))
        if near_cov:
            log('  cover: %d police cover points, nearest to the boarding place %d (%s; %d wanted)' % (len(near_cov), min(near_cov)[0], min(near_cov)[1], BOARD_CLEAR))
            for d, nm in near_cov:
                if d < BOARD_CLEAR:
                    fail('cover point %s is %d from the boarding place (%d wanted)' % (nm, d, BOARD_CLEAR))
    return bad


def flags_of():
    return collections.OrderedDict(SQUADS_AWAKE=SQUADS_AWAKE, NO_AI=NO_AI, POLICE_ARRIVE=POLICE_ARRIVE, START_AT=START_AT, BACKSTOP_AT=BACKSTOP_AT, VAN_DELAY=VAN_DELAY)


BOT_OPT = {'stops': 4, 'cases': 'off', 'lane': True, 'window': True, 'loot_seconds': 20}
# GUESS (this file's): briefcases only (no glass cases), up to 4 stops (pagoda + garden loot areas), a loot wait of 20 s. Run with
# kl_fa_bots.STOP_SHARE as it is (0.10); the plan puts the van's AllyEscapeBox PARK_SIDE from the key-framed van line.


def bots_step(folder, log=print):
    """kl_fa_bots.build with BOT_OPT, then kl_fa_bots_dyn.build, each into a copy, the result copied over the folder's own files.
    -> list of problems. Run it AFTER finish and before check. NOT LOADED LIVE."""
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
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1. Beside the archive: van.json."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    if not NO_AI:
        late += bots_step(folder, log)
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
    GUESS: places = the biggest part of the navigation mesh, 150 apart, never on a guard's spot."""
    n = CIVILIANS if n is None else n
    if not n:
        return None
    import kl_fa_civs as C
    civs = C.plan_places(C.F.Built(folder, 'F01'), n, seed=seed)
    log('  kl_dig_layer: civilians_step: %d of %d placed' % (len(civs), n))
    return C.add(folder, out, civs, 'F01', C.HOST, max_prm_growth=1 << 21, log=log)


COVER_Z = 8000.0                        # the south plateau: the only place with long open ground and little cover (survey 2026-10-25)
COVER_MAX = 12


def cover_step(zp, dst, max_new=COVER_MAX, log=print):
    """POST-STEP on the finished F01_Main.zip: about 12 more cover boxes (tools/kl_cover_add.py) on the south plateau only (z >= COVER_Z).
    The pit and the trench have the level's own cover; no car copies (a Dead Men car here is static scenery). -> kl_cover_add.build's result."""
    import kl_cover_add as CA
    zp, dst = os.path.normpath(zp), os.path.normpath(dst)       # (kl_fa_cover.apply skips the source zip by string compare: mixed slashes copy it over the result)
    real, real_sample = CA.Lite.__init__, CA.SAMPLE
    CA.SAMPLE = 300.0                   # one place per 300 x 300 (600 finds six boxes on the plateau; the cap and the 250 spread still hold)
    def lite(self, zp_):
        real(self, zp_)
        for i in range(len(self.nav.pv)):
            if self.nav.mid[i][2] < COVER_Z:
                self.nav.ok[i] = False
    CA.Lite.__init__ = lite
    # The Dig has no form-b box model (flags 0x200, no collision record): all 121 campaign cover boxes are form a (flags 0x302, a collision record,
    # listed in the root's tree), so the new boxes take form a (kl_fa_cover's own tier a: the .oct record moves with it).
    real_forms = CA.C.forms
    CA.C.forms = lambda B, boxes, tiers='b', borrow=True: real_forms(B, boxes, 'ab', borrow)
    try:
        return CA.build(zp, dst, {'max': max_new, 'sparse': True, 'cars': False, 'spread': CA.SPREAD}, log)
    finally:
        CA.Lite.__init__, CA.SAMPLE = real, real_sample
        CA.C.forms = real_forms


def load_plan(folder):
    pj = os.path.join(folder, 'van.json')
    lay_van(plan_of(pj))


def main():
    global EXTRA_ON, DOG_ON, BLAST, NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, STREAM, MUSIC, CIVILIANS, VAN_HIDE, KEEP_FAKETARGET, VAN_SHOW
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        DOG_ON = '--no-dog' not in a
        EXTRA_ON = '--no-extra' not in a
        BLAST = '--no-blast' not in a
        MUSIC = '--no-music' not in a
        CIVILIANS = CIVILIANS if '--no-civilians' not in a else 0
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
        print('kl_dig_layer.plan: %s (stop %s, board %s)' % (a[2], P['stop'], P['board']))
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']
        print('kl_dig_layer.van-check %s: %d fault(s)' % (a[1], len(rep['faults'])))
        for x in rep['faults']:
            print('  ' + str(x))
        sys.exit(1 if rep['faults'] else 0)
    elif len(a) in (3, 4) and a[0] == 'civilians':
        civilians_step(a[1], a[2], int(a[3]) if len(a) == 4 else None)
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
    import kl_dig_layer
    kl_dig_layer.main()
