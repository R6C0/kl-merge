"""kl_fa_v2_park.py - VERSION 2 of 'A Walk in the Park' (map id DM06B): Dog Days' F07 Fragile Alliance systems + the CAMPAIGN level
M06_A ('Exchange') with the campaign's own enemies, a CAMPAIGN-style round. OFFLINE ONLY: built and checked, NEVER RUN IN THE GAME.
V1 is the installed M06_FA_A (slot F04, id DM06, tools/kl_maps.py). This is a NEW map beside it (kl_expansion.EXTRA: slot F02, page 3).

THE ROUND (owner, 2026-10-17: 'the walk in the park to be like the campaign version'; raw, bodycam-like, Heat-style gunfire):
  1. The crew starts in the PAGODA at the top of the park (the campaign's start), the pavilion windows shatter at the round start.
  2. The campaign's own squads fight them on the way down: the bridge, the Japanese garden (RetoMoto squads, a sniper).
     Dead Men's campaign enemies (7 squads, 21 men) replace F07's mercenaries.
  3. Loot: briefcases in the pagoda (6) and in the garden - the tea house, the shrines and the four statues (9). 15 in all.
  4. Out: down the garden and up the STAIRS to the ring road; the van waits on the ring (kl_map_escape plan on the ring), F07's police
     come in on the ring when the crew reaches the stairs' foot (or by the clock).
No doors, no seal, no light show, seven bots (bots_step: kl_fa_bots + kl_fa_bots_dyn), no room gates: the campaign level needs none of them (kl_fa_club's machinery, left out).

This module is the club's author layer (kl_fa_club.py) cut down to what a park needs, with the park's own tables. It holds the nine names
of kl_graft.AUTHOR_NAMES. Every number marked GUESS is a guess; MEASURED ones come from the real files (re/campaign_v2_plan.md).
Usage (from tools/):
  python kl_fa_v2_park.py test <out> [--keep] [--plan plan.json] [--squads-awake] [--no-ai] [--no-police] [--no-music] [--str PC_Def.str]
  python kl_fa_v2_park.py plan <bare-folder> <plan.json>      the van's plan from a built bare graft
  python kl_fa_v2_park.py check <folder> | van-check <folder> | finish <folder>
"""
import collections, contextlib, math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms
import kl_prpjoin as J
import kl_fa_author as A
import kl_fa_bank as BK
import kl_map_escape as ESC

HOST, LEVEL = 'F07', 'M06_A'
TITLE = 'A Walk in the Park (campaign)'
R = 'ROOT\\'
HIDDEN = 0x400
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
KNOWN = (('stream clips are not in the merged stream file', 'the campaign level\'s music and ambience beds have no record in the installed PC_Def.str '
          '(a later stream-file step): those sounds are silent, nothing else'),)
NO_AI = False                           # True ('--no-ai'): no squad of the campaign stays
SQUADS_AWAKE = False                    # True ('--squads-awake'): ZSquadScript field 3 = 1 on all seven (fall-back if naming the start child does not wake a squad)
POLICE_ARRIVE = True                    # False ('--no-police')
VOICE = True
STREAM = None

# what the campaign pre-pass drops from M06_A: the level bound at the stairs' bottom (it would punish the way up), the exit cutscene
M_DROP = ('Specials!LevelBound!LevelBound_StairsBottom!*', 'Locations/M06_A/M06A_Exit_Cutsequence_01a.zip')

# ------------------------------------------------------------------ the park, measured on M06_A (bare graft, collision floors; re/campaign_v2_plan.md)
# the ring road round the park: centre (0, -100), the van's radius 8244, y about 2497 (the deck climbs from 2490 at -160 deg to 2630 at 160 deg)
C0, C1, RING_R, RING_Y = 0.0, -100.0, 8244.0, 2497.0
DECK = [(160, 2630.0), (166, 2610.0), (172, 2588.0), (176, 2574.0), (179, 2563.0), (184, 2546.0), (190, 2524.0), (195, 2507.0), (200, 2490.0)]    # (deg mod 360, y)


def deck(deg):
    """The ring's collision height at an angle (degrees from +z towards +x), linear between MEASURED samples; clamped at the ends."""
    a = deg % 360.0
    if a <= DECK[0][0]:
        return DECK[0][1]
    for (a0, y0), (a1, y1) in zip(DECK, DECK[1:]):
        if a <= a1:
            return y0 + (y1 - y0) * (a - a0) / (a1 - a0)
    return DECK[-1][1]


def ring(deg, r=RING_R, y=None):
    t = math.radians(deg)
    return (C0 + r * math.sin(t), deck(deg) if y is None else y, C1 + r * math.cos(t))


def snap_mesh(mesh, p):
    """p with the navigation mesh's height under it (p itself when the mesh has nothing there)."""
    hit = mesh.on(*[float(v) for v in p]) if mesh is not None else None
    return (float(p[0]), float(hit[1]), float(p[2])) if hit else (float(p[0]), float(p[1]), float(p[2]))


PAGODA_Y = 636.0                        # the mesh height in the pagoda's inner room (mesh 635.1, collision floor about 625)
FLOOR_Y = 625.0                         # the pagoda's collision floor: loot lies on it
WEST, SOUTH = (-1.0, 0.0), (0.0, -1.0)
# START: two rows of four in the pagoda's inner room (x 500..1100, z 2260..2460), facing south into the park. GUESS: the rows
START = [(float(x), PAGODA_Y, z) for z in (2300.0, 2420.0) for x in (560, 630, 700, 770)]
# 2026-10-17: the rows moved to the inner room's west end so the pagoda's cases (east corridor, x 1240) are >= LOOT_CLEAR from every START
# (before: rows x 560..1040 around cases at x 760-840, inside the pickup reach: a crew at spawn drained them from the pre-round panel).
# TRAITOR: four on the terrace in front of the pagoda, z 2700. GUESS (y snapped to the mesh at build time; check() reads it back)
TRAITOR = [(float(x), PAGODA_Y, 2700.0) for x in (700, 780, 860, 940)]
TEAM_MERC = [(float(x), PAGODA_Y, z) for z in (2330.0, 2390.0) for x in (600, 670, 740, 810)]
BRIDGE = (814.0, 392.0, -651.0)         # the bridge's landing (MEASURED)
STAIRS_FOOT = (-1.0, 580.0, -10940.0)   # MEASURED, floor about 574
STAIRS_TOP = (106.0, 2564.0, -10934.0)  # MEASURED, about radius 10834 from the ring's centre
SNIPER = (18.0, 1526.0, -11418.0)       # MEASURED
STAGE_B = [(BRIDGE[0] + dx, BRIDGE[1], BRIDGE[2] + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]
STAGE_C = [(STAIRS_FOOT[0] + dx, STAIRS_FOOT[1], STAIRS_FOOT[2] + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]
STAGE_D = [(STAIRS_TOP[0] + dx, STAIRS_TOP[1], STAIRS_TOP[2] + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]
# the police who come back after a death: the ring west of the stop's far side (160..166 deg, r 8800). GUESS
AFTER_DEATH = [ring(a, 8800.0) for a in (160, 161, 162, 163, 164, 165, 166)]
BODIES = [ring(a, 8880.0) for a in (160, 161, 162, 163, 164, 165, 166, 167)]


def _spawn():
    """ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz) or a place looked at)."""
    board = BOARD_AT
    return {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (30, 0, 20), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (30, 0, 20), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 40), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (AFTER_DEATH, (0, 0, 0), board),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (TEAM_MERC, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (40, 0, 40), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (AFTER_DEATH, (0, 0, 0), board)}


# ------------------------------------------------------------------ the loot: 15 briefcases (where the case's underside lies, degrees, value, what)
# MEASURED: collision floors (the pagoda 625; the garden's per spot). GUESS: every place, turn and value (pagoda 300,000 each = 1.8 million;
# garden 150,000 each = 1.35 million). The pagoda's lie in the east corridor, far from the START rows (check() fails below LOOT_CLEAR).
LOOT = [((float(x), FLOOR_Y, float(z)), yaw, 300000, 'the pagoda') for (x, z), yaw in
        zip([(1240, z) for z in (2200, 2270, 2340, 2410, 2480, 2550)], (4.0, -8.0, 90.0, 85.0, -12.0, 10.0))]
# 2026-10-17: the pagoda's six cases were at x 760-840, z 2290-2410 (between the START rows); now a line down the east corridor (x 1240, on the
# mesh, inside the EnterLootArea box x 350..1250 z 2160..2560 that the bots' first stage needs). GUESS: the spacing (70) and the turns.
LOOT_CLEAR = 400.0                      # every case at least this far from every START point (pickup reach is LOOT_REACH + 40; e5's number)
LOOT += [((float(x), float(y), float(z)), yaw, 150000, what) for (x, z, y), yaw, what in [
    ((802, -2456, 175), 0.0, 'the tea house'), ((122, -1619, 184), 40.0, 'shrine B1'), ((-2020, -6024, 180), -30.0, 'shrine B2'),
    ((-3346, -6454, 188), 70.0, 'shrine A1'), ((1106, -11613, 199), 15.0, 'shrine A2'),
    ((-539, -4741, 184), 90.0, 'statue 1'), ((-1073, -4566, 198), -20.0, 'statue 2'), ((276, -8748, 182), 5.0, 'statue 3'), ((-354, -8962, 182), 50.0, 'statue 4')]]
LOOT_REACH = 125.0                      # TriggerBox2 radius (kl_escape.REACH)
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, as the club's

# ------------------------------------------------------------------ the host's layer (F07)
PARK = (0.0, -60000.0, 0.0)
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyTop', '040_LevelBound_AlleyRight',
                                                         '040_LevelBound_AlleyLeft', '030_LevelBound_StreetRight', '030_LevelBound_StreetLeft')
          for b in ('Bound', 'Warn01', 'Warn02')]       # all 18: F07's alley bounds do not fit a park (no bound of the park's own: the ring has a rail)
PLACE_FIXED = {
    'FASpecials!POI!Trigger_POI_TheLootArea': ((800, 700, 2360), None, (450, 150, 200), 'GUESS: the pagoda\'s inner room (it starts the loot marker\'s timer)'),
    'FASpecials!POI!POI_TheLootArea': ((800, 760, 2360), None, None, 'over the pagoda\'s cases'),
    'FASpecials!PIP!EnterLootArea': ((800, 700, 2360), None, (450, 150, 200), 'the pagoda: AI heisters\' first stage is inside this box'),
    'FASpecials!PIP!ExitLootArea': ((STAIRS_FOOT[0], STAIRS_FOOT[1] + 120, STAIRS_FOOT[2]), None, (300, 150, 50), 'GUESS: a plane at the stairs\' foot, after the last loot'),
    'Specials!LevelSpeak!TriggerBox': ((STAIRS_TOP[0], STAIRS_TOP[1] + 80, STAIRS_TOP[2]), None, (300, 150, 200), 'GUESS: the stairs\' top (the crew comes up onto the ring)'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((STAIRS_TOP[0], STAIRS_TOP[1] + 80, STAIRS_TOP[2]), None, None, 'with its trigger box'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((1000, 900, 2900), None, None, 'GUESS: over the terrace'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((700, 650, 2360), None, None, 'the START rows'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((900, 600, -300), None, None, 'GUESS: the bridge'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': (BRIDGE, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((200, 900, -10300), None, None, 'GUESS: the stairs\' foot'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': (STAIRS_FOOT, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((300, 2750, -10500), None, None, 'GUESS: the stairs\' top'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': (STAIRS_TOP, None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((0, 2900, -8000), None, None, 'GUESS: over the ring'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((0, 2640, 8700), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((0, 2900, -8000), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((0, 2640, 8700), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these (GUESS: bridge, stairs foot, stairs top)
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': (BRIDGE, None, (250, 150, 250), 'GUESS: the bridge\'s landing'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': (STAIRS_FOOT, None, (300, 150, 250), 'GUESS: the stairs\' foot'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': (STAIRS_TOP, None, (300, 150, 250), 'GUESS: the stairs\' top'),
    # jump points (developer aids): the round's stations
    'Specials!JumpPoints!01_Start': (START[1], SOUTH, None, 'the pagoda'),
    'Specials!JumpPoints!02_MarketMain': (BRIDGE, SOUTH, None, 'the bridge\'s landing'),
    'Specials!JumpPoints!03_MarketOrange': ((802, 180, -2456), SOUTH, None, 'the tea house'),
    'Specials!JumpPoints!04_LootWarehouse': ((-539, 190, -4741), SOUTH, None, 'statue 1'),
    'Specials!JumpPoints!05_MarketGreen': (STAIRS_FOOT, SOUTH, None, 'the stairs\' foot'),
}
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'start timer': FF + 'RivalMercs!Timer',                          # TriggerDelay2 START_AT -> the 'start' squads + the shattering windows
        'backstop': FF + 'RivalMercVan!Timer',                           # TriggerDelay2 BACKSTOP_AT -> the police and the van, whatever the crew did
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # TriggerBox at the bridge's landing -> the 'walk' squads
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # TriggerBox at the stairs' foot -> the 'floor' squads, the alarm
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate',                  # GateGroup + two GatePath: the first of the box / the clock lets the police in
        'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',            # ActivateGeom -> the van's group (the van is hidden until then)
        'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',       # TriggerDelay2 VAN_DELAY -> van on, the gate
        'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator',   # DeactivateGeom -> the van's group again (round 2)
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
GATE_WAYS = ('Way#01', 'Way#02')
# THE LEVEL'S OWN MUSIC (2026-10-17; Retomoto and The Bank kept theirs the same way): the two PlayMusic groups of M06_A's
# Specials!Audio (each with its PlayMusicLayerFade boxes) stay and the layer's lists start them; the campaign's trigger
# chain (00_From_Startup .. 15_From_CutExit) stays out, it hangs on the dropped scripting. Their sounds come along through the
# sound ids in the PlayMusic nodes; the clips need the stream file that holds them (kl_v2_str.py).
#   round start (start timer)  ambient set  = the campaign's 'RetoMoto_Ambient_V2' (the FA sibling plays the same loop), calm
#   the alarm (van timer)      action set    = 'RetoMotoAction' (layers 1 + 2 at -3 dB, layer 3 silent) plus the campaign's own '13_' fades
#                              (what 13_From_SWAT does when the police come: main -3, bass -6, intense -15 dB) and the ambient's
#                              '03_Ambient' fade (-100 dB over 20 s). GUESS: a second PlayMusic does not stop the first, so the
#                              ambient is faded out by hand (the campaign does the same 32 s after the cut scene starts).
MUSIC = True                            # False ('--no-music'): the build as before, silent
MUSIC_AMBIENT, MUSIC_ACTION = 'Specials!Audio!PlayMusic_RetoMoto_Ambient_V2', 'Specials!Audio!PlayMusic_RetoMotoAction'
MUSIC_NAMES = (MUSIC_AMBIENT, MUSIC_ACTION)
MUSIC_ALARM = (MUSIC_AMBIENT + '\\03_Ambient', MUSIC_ACTION + '\\13_Main', MUSIC_ACTION + '\\13_Bass', MUSIC_ACTION + '\\13_Intense')
START_AT = 2.0                          # s from the round-start event to the first squads + the windows. GUESS (the event comes 8.4 - 8.8 s before GO)
BACKSTOP_AT = 240.0                     # s from the round-start event: the police come whatever the crew did. GUESS
VAN_DELAY = 8.0                         # s from the alarm to the van's show and the police. GUESS
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R', 18: 'Multiplayer/F09/MissionReminder_02_R', 19: 'Multiplayer/F06/MissionReminder_01_R',
         20: 'Multiplayer/F06/ReachlootArea_01_R', 127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
         136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
START_KEY = 'AllLevels/Interface/Online/GameStart/M06A_%s_Start'
TEXTS = {START_KEY % 'FA': 'The windows blow. Grab the cases in the pagoda, fight your way down through the garden and up the stairs to the ring road: the van waits there.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'The windows blow. Grab the cases in the pagoda, fight your way down through the garden and up the stairs to the ring road: the van waits there.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}

# ------------------------------------------------------------------ the van on the ring
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'
STOP = (-2572.0, 2498.0, -7933.0)
TH0 = math.degrees(math.atan2(STOP[0] - C0, STOP[2] - C1))      # -161.82 deg
ARRIVE_LEN, LEAVE_LEN = 4500.0, 4000.0
_DA, _DL = math.degrees(ARRIVE_LEN / RING_R), math.degrees(LEAVE_LEN / RING_R)
# GUESS: the stop, the lengths. MEASURED (vanp.py on the bare graft): no fault of kl_map_escape's planner for these (the ring has collision all along)
ROAD = dict(arrive=[ring(TH0 + _DA * (1 - i / 4.0), RING_R, RING_Y) for i in range(4)], stop=STOP,
            leave=[ring(TH0 - _DL * (i + 1) / 3.0, RING_R, RING_Y) for i in range(3)], at='box', heading=None, cam=None)
PLAN = None
NO_PLAN = 'kl_fa_v2_park: the van has no plan: build with \'kl_fa_v2_park.py test <out>\' or kl_fa_v2_park.build()'
BOARD_AT = ring(-159.5, RING_R)        # the rear doors of the standing van (about; prepare_host takes PLAN['board'] once there is a plan)
LANE_CLEAR = 250.0                      # no spawn point, man, cover point or the marker nearer than this to the van's drive. GUESS
BOARD_CLEAR = 500.0                     # no cover point of the police nearer than this to the boarding place
FED_CLEAR = 1000.0                      # no AFTER_DEATH point or police body nearer than this to the boarding place
POLICE_CLEAR = BK.POLICE_CLEAR
BOUND_AFTER = 1000.0
BOARD_NEAR = 30.0

# F07's police squads that come in on the ring (the club's four, laid by angle). squad -> (anchor, men, cover, defend); GUESS: every place.
# Left squads stand past the van's stop (-167 .. -176 deg), Right squads at the far end of its drive (168 .. 175 deg), r 8700 .. 9100:
# 460 or more outside the van's line, on the ring's mesh band (part 5, radius 8050 .. 9400)
G30 = 'Gameplay!030_AfterLoot!'
ARRIVE_ANGLES = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ([-167, -168, -169], [-172.0, -173.0, -174.0], -170.0)),
    (G30 + '030_FinancialAlleyExitStreet_Left', ([-170.5, -171.5], [-175.0, -176.0], -173.0)),
    (G30 + '030_FinancialAlleyExit_Right', ([170, 171, 172], [174.5, 175.0, 175.5], 173.0)),
    (G30 + '030_FinancialAlleyExitStreet_Right', ([168.5, 169.5], [173.5, 174.2], 171.0))])
ARRIVE_START = '10_RunToCover'
ARRIVE = collections.OrderedDict()
for _n, (_m, _c, _d) in ARRIVE_ANGLES.items():
    ARRIVE[_n] = (ring(_d, 9000.0), [ring(a, 8700.0 + 100.0 * i) for i, a in enumerate(_m)], [ring(a, 8800.0 + 100.0 * i) for i, a in enumerate(_c)], ring(_d, 8900.0))

ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))


def police():
    return ARRIVE if POLICE_ARRIVE and not NO_AI else {}


def __getattr__(name):
    if name == 'KEEP':
        return _KEEP + tuple(x for x in police() if x not in _KEEP)
    raise AttributeError(name)


DROP = ('Specials!CoverPoints!*',)      # M06_A's own cover list stays; a second FFCoverList is an assert in its init

# ------------------------------------------------------------------ the campaign's squads (M06_A), MEASURED with sq.py / sqt.py on the dead level
# 'Gameplay!Enemy!' + name -> (stage, the child that starts it). Left out: the #01 squads (LeapFrog), the highway squads, the ring's HavokCar police.
#   'start'  timer START_AT  (the bridge's three, the garden's first three)
#   'walk'   the box at the bridge's landing  (the flanking four, two defenders)
#   'floor'  the box at the stairs' foot      (the sniper, the last defenders)
# A squad is not in the world (field 3 = 0) until its child is named; the children are plain behaviour routs (the stock Dog Days way).
GE = 'Gameplay!Enemy!'
SQUADS = collections.OrderedDict([
    (GE + '01_Bridge!01_RetoMoto_Squad', ('start', '25_DefendBehaviour')),
    (GE + '02_JapaneseGarden!03_RetoMoto_Squad', ('start', '15_DefendBehaviour_Run')),
    (GE + '02_JapaneseGarden!02_RetoMoto_Squad', ('walk', '20_FlankingBehaviour')),
    (GE + '02_JapaneseGarden!05_RetoMoto_Squad', ('walk', '10_DefendBehaviour')),
    (GE + '02_JapaneseGarden!06_RetoMoto_Squad_Singleplayer', ('walk', '10_DefendBehaviour')),
    (GE + '02_JapaneseGarden!01_Squad_Sniper', ('floor', '03_DefendBehaviour')),
    (GE + '02_JapaneseGarden!04_RetoMoto_Squad', ('floor', '10_DefendBehaviour'))])
SHATTER = GE + '01_Bridge!Activator_ShatterPavillionWindows'    # AIDWrapper 'DestroyWindows' (the pavilion's glass): named by the start timer
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout', 'GateGroup', 'GatePath', 'DeactivateGeom', 'Filter'}
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
SQUAD_ACTIVE = A.SQUAD_ACTIVE
MAN_OFF, MAN_IN = 60.0, 15.0
G2 = R + 'Gameplay!Enemy!02_JapaneseGarden!02_RetoMoto_Squad' + chr(92)
MEN = collections.OrderedDict([       # {path of a man's group: (x, y, z) hint}: the flanking squad's men start 146..203 off the mesh; GUESS: put them on polygon 759
    (G2 + 'JPN_Guard#01', (-2567.0, 220.0, -7691.0)), (G2 + 'JPN_Guard#03', (-2507.0, 220.0, -7691.0)),
    (G2 + 'JPN_Guard#04', (-2627.0, 220.0, -7691.0))])
WALK_BOX = (BRIDGE[0], BRIDGE[1] + 100.0, BRIDGE[2]), (300.0, 200.0, 300.0)         # GUESS
FLOOR_BOX = (STAIRS_FOOT[0], STAIRS_FOOT[1] + 100.0, STAIRS_FOOT[2]), (400.0, 150.0, 300.0)       # GUESS


# ------------------------------------------------------------------ 1. the host level before the graft
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT bare F07 + M06_A folder. A fault is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_v2_park: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
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
    global PLAN
    PLAN = P
    return P


def van_path():
    return R + VAN + '\\' + VAN_GROUP


def place_now():
    """PLACE_FIXED + the objects that hang on the van's boarding place (the exit box, the escape-area triggers, the marker)."""
    t = collections.OrderedDict(PLACE_FIXED)
    b = PLAN['board'] if PLAN else BOARD_AT
    out = (b[0] - C0, b[2] - C1)
    n = math.hypot(*out)
    mark = (b[0] + 350.0 * out[0] / n, b[1] + 188.0, b[2] + 350.0 * out[1] / n)       # outside the drive, 350 off, on the mesh band
    box = ((b[0], b[1] + 200.0, b[2]), None, (450.0, 300.0, 450.0), 'GUESS: round the van\'s boarding place on the ring')
    t['Gameplay!EscapeSetup!otrExitLevel'] = box
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    t['FASpecials!POI!POI_TheEscapeArea'] = (mark, None, None, 'beside the boarding place')
    t['Specials!JumpPoints!06_Exit'] = ((b[0], b[1], b[2]), SOUTH, None, 'the boarding place')
    t[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the bridge\'s landing')
    t[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the stairs\' foot')
    return t


def place_police(S, log=print):
    """F07's police squads of ARRIVE onto the ring (kl_fa_club.place_police's way, this file's table). -> [(squad, men)]"""
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
        log('  kl_fa_v2_park: the police that arrive: %d of F07\'s squads re-placed (%d men) on the ring road' % (len(out), sum(n for _s, n in out)))
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
                raise ValueError('kl_fa_v2_park: %s cannot stay: it holds %s, %d actors, %d ZSoldier' % (name, odd or 'plain kinds', actors, ctrl['ZSoldier']))
            ks = sc.resolve(R + name + '\\' + child)
            kinds = {sc.p.key(nm) for k in ks for nm, _b in sc.nodes[k]['ctrls']}
            kind = next(iter(sorted(kinds & A.BEHAVE)), 'SquadModifierBehaviour' if 'SquadModifierBehaviour' in kinds else None)
            if len(ks) != 1 or kind is None:
                raise ValueError('kl_fa_v2_park: %s\\%s: %d nodes holding %s - neither a behaviour rout nor a squad modifier' % (name, child, len(ks), sorted(kinds)))
            keep[name] = (R + name + '\\' + child, actors, sorted(set(ctrl) & STRIP), kind)
        if set(keep) != set(SQUADS):
            raise ValueError('kl_fa_v2_park: squads of SQUADS that are not in %s: %s' % (LEVEL, sorted(set(SQUADS) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the park. S: kl_graft.Level('F07'), unedited."""
    import kl_route
    sc = S.prp
    if PLAN is None:
        raise ValueError(NO_PLAN)
    mesh = kl_route.load(LEVEL).mesh()
    for tbl in (START, TRAITOR, TEAM_MERC, STAGE_B, STAGE_C, STAGE_D):      # heights from the navigation mesh (the tables hold guesses)
        tbl[:] = [snap_mesh(mesh, p) for p in tbl]
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
    log('  kl_fa_v2_park: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
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
    by = collections.Counter(what.split()[0] + ' ' + what.split()[-1] if what != 'the pagoda' else what for _p, _y, _v, what in LOOT)
    log('  kl_fa_v2_park: loot: %d objects, %d in all: %s' % (len(LOOT), sum(v for _p, _y, v, _w in LOOT), dict(by)))
    place_police(S, log)
    S.van = ESC.van_prepare(S, PLAN, log)
    # the van is NOT in the world until the alarm (the club's VAN_LATE: no FakeTarget, hidden from the load)
    vg = A.node_of(sc, van_path()[len(R):])
    gone = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
    for k in gone:
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
    A.place(S, vg, hidden=True)
    log('  kl_fa_v2_park: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; the alarm shows it' % len(gone))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(place_now()['FASpecials!POI!POI_TheEscapeArea'][0])[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_fa_v2_park: the escape marker is %d from the van\'s drive (%d wanted)' % (off, LANE_CLEAR))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M06_A the campaign pre-pass must leave in: the kept squads and the pavilion's shatter wrapper."""
    if level != LEVEL:
        return ()
    return tuple(squad_plan()[0]) + ((SHATTER,) if squad_plan()[0] else ()) + (MUSIC_NAMES if MUSIC else ())


def strip(M, log=print):
    """On the converted Dead Men level, before the join: the kept squads lose STRIP's kinds; every man who stands beside the mesh goes onto it."""
    import kl_route
    if M.name != LEVEL:
        return 0
    keep = squad_plan()[0]
    if not keep:
        log('  kl_fa_v2_park: %s: no squad stays (NO_AI)' % M.name)
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
            raise ValueError('kl_fa_v2_park: MEN: %s: (%d, %d, %d) is not on the navigation mesh' % (path, *hint))
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
    log('  kl_fa_v2_park: %s: %d squads stay (%d men); taken off them: %s; %d props hidden' % (
        M.name, len(keep), sum(a for _s, a, _k, _w in keep.values()), dict(n) or 'nothing', props))
    log('  kl_fa_v2_park: %d men re-placed (MEN); %d stood beside the navigation mesh and were put on it: %s' % (
        len(placed), len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    for o in off:
        log('  kl_fa_v2_park: MAN OFF THE MESH (give him a place in MEN): ' + o)
    if off:
        raise ValueError('kl_fa_v2_park: %d men stand more than %d off the navigation mesh: %s' % (len(off), MAN_OFF, off))
    return sum(n.values())


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_v2_park: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    left = [sc.names[t] for t in sc.tops() if sc.names[t].startswith(('Specials!LevelBound!LevelBound_StairsBottom', 'Boundaries!'))]
    if left:
        raise ValueError('kl_fa_v2_park: the campaign\'s own bounds are in the build: %s' % left)
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
    if plan:                                        # the pavilion's windows go with the round start
        w = values(sc, node(SHATTER), 'AIDWrapper')
        if w[1] != 'DestroyWindows' or not w[0] or not all(sc.resolve(s) for s in w[0]):
            raise ValueError('%s: not an AIDWrapper \'DestroyWindows\' on nodes that exist: %s' % (SHATTER, w[:2]))
        shatter = [R + SHATTER]
    arrive = must([R + n + '\\' + ARRIVE_START for n in police()])
    armed = BK.soldier_rows(sc, plan, log) if plan else {}
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    for w in ways:
        put_(sc.resolve(w)[0], 'GatePath', f0=arrive)
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
    lists('start timer', 'TriggerDelay2', f0=START_AT, f4=stage['start'] + shatter + tune)
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['walk'])
    # the stairs' foot: the last squads, the alarm (the van's timer) and the gate (the police on the ring)
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['floor'] + [R + ROLE['van timer'], ways[0]])
    lists('backstop', 'TriggerDelay2', f0=BACKSTOP_AT, f4=[ways[1], R + ROLE['van timer']])
    lists('van on', 'ActivateGeom', f0='AITrigger', f1=[van_path()])
    lists('van timer', 'TriggerDelay2', f0=VAN_DELAY, f4=[R + ROLE['van on'], R + ROLE['speak']] + alarm)
    lists('reset hide', 'DeactivateGeom', f0='AITrigger', f1=[van_path()])
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    lists('monitor', 'AIMonitor', f2=[R + ROLE['reset hide']] + have + [R + ROLE['start timer'], R + ROLE['backstop']])
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    if PLAN is None:
        raise ValueError('kl_fa_v2_park: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    men = sum(a for _f, a, _s, _k in plan.values())
    log('  kl_fa_v2_park: wired: %d campaign squads (%d men): round start + %.0f s -> %d (+ the pavilion\'s windows: %d); the box at the bridge -> %d; the box at the '
        'stairs\' foot -> %d + the alarm (+%.0f s: the van, the exit line) + the gate (%d police squads); backstop %.0f s; %d dead entries cut; soldier rows: %s' % (
            len(plan), men, START_AT, len(stage['start']), len(shatter), len(stage['walk']), len(stage['floor']), VAN_DELAY, len(arrive), BACKSTOP_AT, quiet,
            dict(armed) or 'Dead Men\'s rows stay'))
    return {'stage': dict(stage), 'arrive': arrive, 'ways': ways}


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
        log('  kl_fa_v2_park: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_v2_park: %s: the loot already shows models of its own: left as it is' % folder)
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
    log('  kl_fa_v2_park: %d text keys in %d languages; settings fields %s name the start windows' % (len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ build and check
def build(out, log=print, plan=None):
    """F07 + M06_A with the layer into <out>/F07+M06_A campaign -> (kl_maps.one's result, that folder, the van's plan, kl_map_escape's report).
    plan None = made here on a BARE graft (<out>/_bare, deleted again)."""
    import shutil, kl_snd
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', m_drop=M_DROP)
        try:
            if not r.get('ok'):
                raise ValueError('kl_fa_v2_park: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    kl_snd.VOICE = True if VOICE else None
    try:
        with ESC.van_layer(plan, log) as st:
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_v2_park', m_drop=M_DROP)
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


def load_plan(folder):
    pj = os.path.join(folder, 'van.json')
    lay_van(plan_of(pj))


def main():
    global NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, STREAM, MUSIC
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        MUSIC = '--no-music' not in a
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
        print('kl_fa_v2_park.plan: %s (stop %s, board %s)' % (a[2], P['stop'], P['board']))
    elif len(a) == 2 and a[0] == 'van-check':
        pj = os.path.join(a[1], 'van.json')
        rep, L_, bare = van_check(a[1], print, plan_of(pj) if os.path.isfile(pj) else None)
        rep['faults'] += ESC.check(L_)['faults']
        print('kl_fa_v2_park.van-check %s: %d fault(s)' % (a[1], len(rep['faults'])))
        for x in rep['faults']:
            print('  ' + str(x))
        sys.exit(1 if rep['faults'] else 0)
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
    import kl_fa_v2_park
    kl_fa_v2_park.main()
