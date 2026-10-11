#!/usr/bin/env python3
"""
The Fragile Alliance layer of THE VAULT: the bank the campaign way (Dead Men M03_A, chapter 3 'Withdrawal',
alone, under Dog Days F07) - a second bank map beside the Fragile Alliance bank M03_FA_A. Authored from stock
objects, offline, on the pattern of kl_fa_author.py (Retomoto Tower). The study: re/campaign_fa.md 4.1,
re/campaign_fa_bank.md 4.3 / 8.3 / 8.4; the build stage by stage, every check with its output and the list of
what only a live run can settle: re/bank_campaign.md. Nothing here installs anything or starts the game.

    python kl_fa_bank.py test <out> [--keep] [options]    build F07 + M03_A with the layer into <out> (kl_maps.one),
                                                          finish() on the written level, check(); exit 1 if a problem
                                                          is left that is not in KNOWN
    python kl_fa_bank.py finish <built folder>            what needs the WRITTEN level, on a folder built by
                                                          'kl_maps.py one <out> F07 M03_A --campaign --author kl_fa_bank
                                                          --keep': the vault loot's briefcases, the level's own texts
    python kl_fa_bank.py check <built folder>             every check of this layer on a built folder
    python kl_fa_bank.py inventory <built folder>         the layer with world places read back from the level
    options of 'test' (one flag each for the live runs):
      --doors-animate   the eleven door leaves of the route stay where the level has them and get 'Activate' at
                        the round start (default: they are OPEN AT BUILD TIME - sunk, their collision cut)
      --vault-open      the vault door is sunk at build time too (a first load in which no door can stop anybody)
      --vault-stays     the vault door is not switched off after its swing (default: it goes away DOOR_GONE s later)
      --loot-shown      the vault's loot lies there from the start (default: hidden until the beat's timer ends)
      --loot-bags       the vault's loot keeps F07's money bags (finish() leaves the models alone)
      --beat S          seconds from the ante-room box to the vault door (default BEAT)

THE ROUND (this file is the FIRST HALF: a round without enemies and without the van's drive)
  START   roped down in the secure yard, two stacks of four beside the loading dock's roller door.
  IN      dock -> vault lobby -> two flights down -> the vault's ante-room. Six door sets stand in series on the
          way in and out (re/campaign_fa_bank.md 8.3): five of them are open from the load, the vault door is the beat.
  BEAT    a box in the ante-room starts a timer (the next stage hangs the six locking rods, the reinforcements,
          the alarm and the music on it); when it ends the vault door gets 'Activate', the loot appears, and
          DOOR_GONE seconds later the door is switched off, so that the vault can be entered whatever the swing did.
  LOOT    seven briefcases in the vault (six at the deposit-box walls, one on the trolley), four stacks on the
          teller counters of the banking hall.
  OUT     up the airlock stairs into the hall, out of the front entrance, to the street: the exit box calls the van.
          The van itself (kl_map_escape.van_plan_points / van_prepare) is the next stage's: here F07's first van
          only stands where it will wait, so that the exit trigger has a vehicle to name.

HOW (as kl_fa_author: no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  The nine names of kl_graft.AUTHOR_NAMES: HOST, prepare_host(S), strip(M), KEEP, DROP, layer_names(Jn),
  complete(Jn), wire(Jn), campaign_names(level). On top of them, because the interface has no place for it:
  1. THE DOORS AT BUILD TIME (Doors): three functions of kl_escape that kl_graft.build calls for every Dead Men
     map are wrapped for the length of ONE build - the recipe of the study's G:/kl_scratch/cfa_fill1/build_open.py
     (re/campaign_fa.md G1.1, with its two traps). prepare_host() puts the wrappers in, the last of them takes
     them out again; 'with doors(): ...' does the same from a script.
  2. finish(folder), on the written level (chunk numbers and the .LOC exist only then): the briefcase model
     (kl_fa_loot.case_model, into dead chunk indices), and the level's own texts (.LOC keys, settings fields).

GUESS = a value that is not copied from a stock object or measured in the levels; ASSUMPTION = fits the
evidence, not proven. Every table entry carries its source. Rotation, box and 'hidden' facts: kl_fa_author's
docstring (the helpers are imported from there: rot9 / look9 / place / setv / ctrl_of / node_of).
"""
import collections, contextlib, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms, kl_scene, kl_escape, kl_hvk
import kl_prpjoin as J
import kl_fa_author as A                # the small tools only (place, setv ...); none of Retomoto's tables
from kl_prp import units

HOST, LEVEL = 'F07', 'M03_A'
TITLE = 'The Vault'                     # the map's name (for the menu page: kl_expansion's table, a later stage)
R = 'ROOT\\'
IN = 'Locations/M03_A/M03A_Locations.zip\\Locations/M03_A/M03A_LOC_Inside.zip\\'
VA = IN + 'Locations/M03_A/M03A_LOC_Ins_Vault.zip\\'
HIDDEN = 0x400
# problems kl_graft.verify reports that this layer cannot remove: (text looked for, why it stands)
KNOWN = (('stream clips are not in the merged stream file', 'the level\'s ambience clip is not in the installed PC_Def.str; '
          'a larger stream file is the owner\'s go-ahead (re/campaign_fa.md 3.1 K): the sound is silent, nothing else'),
         ('no ZSquadScript', 'THIS HALF: a round without enemies (NO_AI); the next stage keeps the campaign\'s squads'))

# ------------------------------------------------------------------ the bank (M03_A), measured
# Floors (collision, tools/kl_route.py stations on a built level): yard and loading dock y 200, vault lobby 240,
# vault and ante-room -960, banking hall and plaza 800, front street 700. Everything below is on ONE part of the
# navigation mesh (566 polygons; re/bank_campaign.md T3).
YARD, STREET = 200.0, 700.0
DOCK_DOOR = (560.0, -4706.0)            # the roller door M03_A_Garage_01a\SI0201_M03_BackDorAnim_01: doorway x 385..735
FRONT = (300.0, 800.0, -9350.0)         # the front entrance: no door, a 2.0 m gap between two glass wings (x 200..400, z -9410)
TO_DOOR = (0.0, -1.0)                   # from the yard at the dock door
# START (re/campaign_fa.md 4.1 item 1): two stacks of four beside the dock door, under the back wall where the
# campaign's ropes end ((-35 / -151, 200, -4525)). GUESS: the stacks; MEASURED: each point on the mesh and on free
# floor (check()). A parked armoured transport (x -30..190, z -4130..-3590) stops the rows moving west.
START = [(float(x), YARD, -4350.0) for x in (150, 250, 350, 450, 700, 800, 900, 1000)]
TRAITOR = [(float(x), YARD, -4000.0) for x in (300, 530, 770, 1000)]            # GUESS: behind the stacks
# police who come back: the front street, at the places of the campaign's own plaza police (re/campaign_fa.md
# 4.1 item 7: 'Police_OutSide_01' west (x -1842..-1437), 'Police_Outside_Teargas_01' east). GUESS: the points inside
# those spans; the west row begins at x -1750: the campaign's own warn box of its west level bound reaches x -1805
POLICE = [(-1750.0, 705.0, -9600.0), (-1650.0, 705.0, -9580.0), (-1545.0, 705.0, -9560.0), (-1437.0, 705.0, -9542.0),
          (2016.0, 706.0, -9598.0), (2100.0, 706.0, -9500.0), (2178.0, 706.0, -9418.0)]
# team mode's respawn stages: vault lobby (campaign 'CP_03_PosP1'), ante-room (the campaign's box 'TB_VbByVault'),
# foyer and hall (campaign 'CP_05_PosP1' / 'CP_04_PosP2'). GUESS: the three points beside each marker
STAGE_B = [(394.0, 241.0, -7129.0), (294.0, 241.0, -7129.0), (494.0, 241.0, -7129.0), (394.0, 241.0, -7029.0)]
STAGE_C = [(460.0, -958.0, -12152.0), (334.0, -958.0, -12226.0), (234.0, -958.0, -12226.0), (400.0, -958.0, -11979.0)]
STAGE_D = [(295.0, 802.0, -6052.0), (297.0, 802.0, -6238.0), (195.0, 802.0, -6052.0), (395.0, 802.0, -6052.0)]
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz), or a place looked at)
SPAWN = {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), FRONT),
         # the other modes' criminals stand in the yard too, in rows of their own
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (0, 0, 100), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (0, 0, 100), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 120), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (0, 0, -120), FRONT),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (START, (100, 0, 200), TO_DOOR),      # 100: clear of the armoured transport
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (0, 0, -120), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (0, 0, -240), FRONT)}
HENCH_SHIFT = (0.0, 0.0, -160.0)        # the eight police bodies (Heroes!Henchmen_0n) beside the AFTER_DEATH points

# ------------------------------------------------------------------ the loot
# THE VAULT (M03_A_Vault_01a, floor y -960): the six deposit-box walls SI0102_M03_BankVault_Wall2mBOXES_PRE_01..06
# stand at (600 / 400 / 200, -960, -13410) and (0, -960, -13230 / -13030 / -12830); the trolley
# PC0600_M03_VaultTrolley_01 at (199, -960, -13171) carries cartons whose top is y -844 (MEASURED in the collision).
# (place on the floor or the cartons, degrees the case is turned, value). GUESS: every place, turn and value
# (the study: 'about 2.6 million'; F07's own loot: 5 x 800,000). The places are 100 in front of their wall:
# the hidden blown vault 'Vault_POST' has its rubble at the walls' feet (floors y -879 at z -13350 and x 70).
VAULT_LOOT = [((200.0, -960.0, -13310.0), 8.0, 300000), ((400.0, -960.0, -13310.0), -6.0, 300000), ((600.0, -960.0, -13310.0), 11.0, 300000),
              ((110.0, -960.0, -13230.0), 96.0, 300000), ((110.0, -960.0, -13030.0), 84.0, 300000), ((110.0, -960.0, -12830.0), 101.0, 300000),
              ((175.0, -844.0, -13180.0), 20.0, 500000)]            # the last: on the trolley's cartons
VAULT_BOX = ((-50.0, 1150.0), (-1000.0, -400.0), (-13560.0, -12650.0))      # the room, for finish() / check(): what lies in the vault
# THE TELLERS (M03_A_Bank_Main_01): counters Pc0100_M03_Bankcounter_A_* at x -791 (z -7202, -7602, -8002) and x 1393
# (z -7206, -7606, -8006), their top y 899, a glass grille over it (MEASURED in the collision). The stack lies on the
# counter's public edge - the side the crew passes on its way out. GUESS: the edge distance (26) and the value
TELLER_LOOT = [((-765.0, 899.0, -7202.0), 75000), ((-765.0, 899.0, -8002.0), 75000), ((1367.0, 899.0, -7206.0), 75000), ((1367.0, 899.0, -8006.0), 75000)]
LOOT_REACH = 125.0                      # TriggerBox2 radius: the value of all 117 stock OnlineMoneyContainer triggers (kl_escape.REACH)
GATE_VAULT = True                       # False ('--loot-shown'): the vault's loot lies there from the start
CASE = 'dm'                             # the vault's prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, kl_fa_loot's for that model (36 wide x 1.25 = 45: a real attache case)

# ------------------------------------------------------------------ the doors
# Six door sets in series, each necessary, no way round any of them (re/campaign_fa_bank.md 8.3; tools/kl_route.py
# doors). (path below ROOT, stock world place, set). The glass leaves stand under a TURNED group, the others not.
LEAVES = [(IN + 'M03_A_Garage_01a\\SI0201_M03_BackDorAnim_01', (560, 550, -4706), 'dock roller door'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_01\\GlassDoor_LEFT', (125, 240, -6808), 'glass door 1'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_01\\GlassDoor_RIGHT', (-125, 240, -6808), 'glass door 1'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_02\\GlassDoor_LEFT', (525, 240, -7602), 'glass door 2'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_02\\GlassDoor_RIGHT', (274, 240, -7602), 'glass door 2'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_01', (1215, 240, -7105), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_02', (1215, 240, -6895), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_03', (1000, 240, -6895), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_04', (1000, 240, -7105), 'airlock'),
          (VA + 'M03_A_VaultLobbyFoyer_01a\\SI0103_M03_BankVault_DDorSlide_01', (195, 802, -5801), 'hall / foyer'),
          (VA + 'M03_A_VaultLobbyFoyer_01a\\SI0103_M03_BankVault_DDorSlide_02', (405, 802, -5801), 'hall / foyer')]
# the vault door: a ZGROUP with the MatPosAnim ('Activate', frames 0..200: 100 degrees at frame 60, rests at 95;
# one way - re/campaign_fa.md G1.8) and below it the body that owns the key-framed collision placement
VAULT_DOOR = VA + 'M03_A_VaultEntrance_01a\\SI0102_M03_BankVault_Door_PRE_01'
VAULT_BODY = VAULT_DOOR + '\\SI0102_M03_BankVault_Door_PRE'
VAULT_BODY_AT = (571, -760, -12510)
# DOORS, the lead's default (the owner has not answered): the eleven leaves are OPEN AT BUILD TIME - sunk DOOR_DY
# in world y, their collision placements cut - so that the first live load cannot be stopped by a Dead Men door
# animation that does not play. True ('--doors-animate'): the leaves stay; the round-start event sends each
# 'Activate', and the four glass leaves get their own LAST frame GLASS_LAST first: their clip goes to 135 degrees
# at frame 50 and BACK to 0 at frame 100, and a leaf that stores -1 / -1 plays the whole clip (G1.8).
DOORS_ANIMATE = False
DOOR_DY = -2500.0                       # the study's: under the map's lowest floor (the vault, y -960)
GLASS_LAST = 50                         # the campaign plays 0..50 on door 1 and 0..36 on door 2 (109 degrees)
MPA_MESSAGE, MPA_LAST = 0, 14           # MatPosAnim fields: the message that starts it, the last frame (13 = the first)
# THE VAULT DOOR is the beat and keeps its collision. Whatever its swing does in Dog Days, the vault must be
# enterable: DOOR_GONE seconds after its 'Activate' a DeactivateGeom switches the body off. ASSUMPTION that a
# body switched off at run time stops colliding (stock F07 takes its 'BlockVisionPlane' away so; Retomoto's blown
# window is walked through). If it does not, '--vault-open' sinks the door with the others.
VAULT_OPEN = False
VAULT_DOOR_GOES = True                  # False ('--vault-stays'): once the swing has been SEEN to play and to let people in
BEAT = 48.0                             # s from the ante-room box to the door. GUESS: six rods at 8 s steps (the study)
DOOR_GONE = 6.0                         # s after the door's 'Activate'. GUESS: the swing is at its 100 degrees after 2.4 s

# ------------------------------------------------------------------ the host's layer
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put (kl_fa_author.PARK)
BOX = (0.0, 1.0)                        # a box is laid in the world's axes (the turn that leaves local +Z where it is)
# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # the round's markers and planes
    'FASpecials!POI!Trigger_POI_TheLootArea': ((575, 350, -4150), None, (700, 200, 450), 'GUESS: box round the START stacks in the yard (F07: round its start); it starts the loot marker\'s 11 s timer'),
    'FASpecials!POI!POI_TheLootArea': ((400, -800, -13000), None, None, 'the vault\'s middle, 160 over its floor'),
    'FASpecials!PIP!EnterLootArea': ((560, 380, -4800), None, (250, 230, 50), 'GUESS: a plane 1 m inside the dock\'s roller door (doorway x 385..735, z -4706)'),
    'FASpecials!PIP!ExitLootArea': ((303, 974, -9407), None, (300, 200, 100), 'the front entrance: M03_FA_A\'s own ENTERS box there (Triggers!EnterBankTrigger_01), same world'),
    'FASpecials!POI!POI_TheEscapeArea': ((949, 890, -11105), None, None, 'the van\'s stop (re/bank_campaign.md T2.5), 190 over the road as on Retomoto'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((300, 1075, -8600), None, (1500, 425, 2900), 'GUESS: hall, plaza and street, y 650..1500 (floors 800 / 700) - not the vault lobby under the hall (floor 240, ceiling 640)'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((300, 1075, -8600), None, (1500, 425, 2900), 'as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((300, 1075, -8600), None, (1500, 425, 2900), 'as above'),
    # the beat's box and the exit
    'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou': ((460.4, -714.0, -12151.8), None, (550.2, 254.0, 556.1), 'the campaign\'s own box GamePlay!4_Vault_Part!...\\TB_VbByVault: place and half extents'),
    'Gameplay!EscapeSetup!otrExitLevel': ((300, 800, -10300), None, (1500, 300, 900), 'GUESS (the study): plaza and street in front of the entrance, z -11200..-9400'),
    'Specials!LevelSpeak!TriggerBox': ((300, 930, -5650), None, (300, 180, 150), 'GUESS: the foyer, where the crew comes up into the hall (campaign Jump#120 (309, 803, -5624))'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((300, 930, -5650), None, None, 'with its trigger box'),
    # spawn cameras (camera, look-at): all GUESS
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((575, 650, -3550), None, None, 'GUESS: over the yard'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((560, 320, -4700), None, None, 'the dock\'s roller door'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((700, 470, -6600), None, None, 'GUESS: vault lobby'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((394, 300, -7129), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((600, -700, -11400), None, None, 'GUESS: ante-room'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((400, -880, -12400), None, None, 'GUESS: towards the vault door'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((300, 1250, -7000), None, None, 'GUESS: banking hall'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((295, 870, -6052), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((-1640, 1100, -10300), None, None, 'GUESS: over the street, west'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((-1640, 760, -9580), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((-1640, 1100, -10300), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((-1640, 760, -9580), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': ((0, 340, -6900), None, (200, 150, 80), 'GUESS: behind glass door 1 (x -150..150, z -6810)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': ((400, -800, -11200), None, (400, 200, 100), 'GUESS: the ante-room\'s near end (the room is z -12600..-10800)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': ((300, 930, -5650), None, (300, 180, 150), 'GUESS: the foyer (floor y 800)'),
    # jump points (developer aids in stock levels; nothing names them): the campaign's own jump list
    'Specials!JumpPoints!01_Start': ((575, YARD, -4250), TO_DOOR, None, 'the yard, between the START stacks'),
    'Specials!JumpPoints!02_MarketMain': ((266, 202, -5002), TO_DOOR, None, 'M03_A Special!JumpPoints!Jump#131: the dock'),
    'Specials!JumpPoints!03_MarketOrange': ((422, 242, -6188), TO_DOOR, None, 'Jump#070: towards the vault lobby'),
    'Specials!JumpPoints!04_LootWarehouse': ((463, -956, -13238), (0.0, 1.0), None, 'Jump#100: the vault'),
    'Specials!JumpPoints!05_MarketGreen': ((377, 801, -8423), TO_DOOR, None, 'Jump#130: the banking hall'),
    'Specials!JumpPoints!06_Exit': ((291, 714, -11159), (1.0, 0.0), None, 'Jump#132: the front street'),
    # level bounds. Front: the campaign's own three stay (kl_maps.campaign_drop: Special!Levelbound!LevelBound_Outside_
    # Front (355, 943, -14140), _Left (3763, 843, -10211), _Right (-2837, 928, -10916)). Back: the yard is a closed box
    # (walls and hero-only collision on three sides: re/campaign_fa_bank.md 8.3); these two are for whoever gets out
    'Specials!LevelBound!040_LevelBound_AlleyTop!Bound': ((1000, 400, -320), None, (1700, 600, 220), 'GUESS: behind the yard\'s north wall (z -600; a walker comes to z -680), z -540..-100'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn01': ((1000, 400, -345), None, (1700, 600, 245), 'GUESS: from z -590'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn02': ((1000, 400, -345), None, (1700, 600, 245), 'as Warn01'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Bound': ((2800, 400, -2700), None, (250, 600, 2100), 'GUESS: behind the yard\'s east fence (x 2386; a walker comes to x 2300), x 2550..3050'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn01': ((2750, 400, -2700), None, (300, 600, 2100), 'GUESS: from x 2450'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn02': ((2750, 400, -2700), None, (300, 600, 2100), 'as Warn01'),
}
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft',
                                                         '030_LevelBound_StreetRight') for b in ('Bound', 'Warn01', 'Warn02')]
# host objects that get a new job in wire(): role -> name (each a single top-level node)
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'doors': 'Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo',         # AIDWrapper 'Activate' -> the eleven leaves (DOORS_ANIMATE)
        'beat box': 'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou',                   # TriggerBox in the ante-room
        'beat timer': 'Gameplay!010_FirstFight!RivalMercVan!Timer',                  # TriggerDelay2 BEAT: what the next stage hangs the rods on
        'door': 'Gameplay!010_FirstFight!RivalMercVan!Activator_VanSound',           # AIDWrapper 'Activate' -> the vault door
        'door timer': 'Gameplay!010_FirstFight!RivalMercVan!TimerVanGo',             # TriggerDelay2 DOOR_GONE
        'door off': 'Gameplay!010_FirstFight!RivalMercVan!GeomDeactivator_DriveInVan',   # DeactivateGeom -> the door's body
        'loot on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT',    # ActivateGeom -> the vault's hidden loot
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
# FOR THE NEXT STAGES. Free single top-level objects of F07 this file does not touch (add the name to KEEP_MORE, give
# it a ROLE): trigger boxes Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou, Gameplay!030_AfterLoot!tbExitFinancialAlley,
# Gameplay!020_Loot!tbExitLoot, Gameplay!020_Loot!FollowPlayers!tbCountPlayers, Gameplay!040_Escape!tbEscapeAI,
# Gameplay!RunToEscape!tbRunToEscape, ...!tbRunToEscape1Player; counters Gameplay!020_Loot!FollowPlayers!TriggerCounter,
# Gameplay!RunToEscape!tcRunToEscape; 22 more TriggerDelay2 and 7 more AIDWrapper under Gameplay!010_FirstFight!;
# ActivateGeom ...Shutters!GeomActivator_TearGas_RIGHT; DeactivateGeom ...RivalMercs!DisableVisionBlocker!GeomDeactivator.
# Five of the timers are named by F07's AIMonitor at the round start (RivalMercVan!Timer and TimerVanGo among them):
# wire() writes the monitor's list, so that a ROLE object is started only by what this file names.
KEEP_MORE = ()
# the escape: F07's first van, its relay, the exit trigger and the two 'last van' objects (the monitor is kept by
# kl_fa.host_keep). The next stage: KEEP_MORE gets nothing new for it - this is kl_map_escape.VAN_KEEP already -
# and VAN_WAIT goes: prepare_host() calls kl_map_escape.van_prepare(S, plan, log) instead of park_van().
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'       # everything of the van with a place is below it (kl_fa_author.place_vans)
VAN_WAIT = (-3248.0, 702.0, -11859.0)   # where the van will wait (re/bank_campaign.md T2.5: the passing plan). Until the
                                        # next stage lays its drive, the van only STANDS there: F07's own baked drive starts
                                        # from that place if the exit trigger calls it. Not under the map: its ZFakeTarget
                                        # must stay inside the rooms' bounds (the 0x686a66 crash, re/campaign_fa.md 2.1 item 11)
ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith('Gameplay!0'))


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_bank.KEEP at the moment of use
        return _KEEP + tuple(x for x in KEEP_MORE if x not in _KEEP)
    raise AttributeError(name)

# F07's cover list goes: M03_A's own 'Special!CoverList' stays through the campaign pre-pass (kl_maps.PASSIVE), and
# a second FFCoverList is an assert in its init (kl2 0x6682c5; kl_fa_author.DROP)
DROP = ('Specials!CoverPoints!*',)

# ------------------------------------------------------------------ texts and lines
# The level's own .LOC keys (finish()). The start window is a text key of the level's .LOC (settings fields 12 / 13
# Fragile Alliance, 14 Cops & Robbers, 15 Undercover Cop; F07: 'Get the documents, then get to the back alley ...').
# Dead Men's own menu has the slots 'TitleDL01' / 'BriefingDL01 - Bank Vault' for a vault map that never shipped:
# the title and a briefing in the style of its four ('The money transport always arrives at The US Credit Bank ...')
# are written under those keys. Nothing in Dog Days reads the two: they are there for the menu page (a later stage).
# GUESS: every wording. The other eight languages get the English text.
START_KEY = 'AllLevels/Interface/Online/GameStart/M03A_%s_Start'
TEXTS = {START_KEY % 'FA': 'Get down to the vault, grab the cases and get out through the front. The van picks you up on the street.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'Get down to the vault, grab the cases and get out through the front. The van picks you up on the street.',
         'AllLevels/Menu/Online/Scenarios/TitleDL01': TITLE,
         'AllLevels/Menu/Online/Scenarios/BriefingDL01': 'The tellers at The US Credit Bank, Downtown district, only handle small change. The real money '
         'sits in the vault, three floors under the banking hall. We rope down into the secure yard, go in through the loading dock, '
         'crack the vault door and take the cases. Then up through the hall and out the front doors, where our getaway van will pick us up.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}
# the briefing and reminder lines: stock F07's speak of a data theft. Lines of other stock levels that fit cash, a
# quiet way in and a street, all in F07's bank with their eight voices (kl_fa_author.RT_LINES does the same for
# Retomoto; re/bots_voice.md 6.2). settings field -> line. GUESS: the choice
LINES = {17: 'Multiplayer/F05/MissionBriefing_03_R',     # 'Keep it down. Get in and get the cash at any price.'
         18: 'Multiplayer/F05/MissionBriefing_02_R',     # 'Move in quietly. The fuckers wont know what hit 'em.'
         19: 'Multiplayer/F05/MissionBriefing_01_R',     # 'Keep it down and take 'em by surprise.'
         20: 'Multiplayer/F05/MissionBriefing_03_R',
         127: 'Multiplayer/F06/ReachlootArea_01_R',      # 'Alright! Grab the cash.'
         130: 'Multiplayer/F04/ExitLootArea_01_R',       # 'We got it! Let's keep moving!'
         136: 'Multiplayer/F06/MissionReminder_01_R',    # 'Just get the money.'
         137: 'Multiplayer/F09/MissionReminder_02_R'}    # 'We can do this. Be quick 'cause this is gonna turn nasty!'
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'             # 'Get out on the street! straight ahead!' (F07's: '... to the back alley')

NO_AI = True                            # THIS HALF: no squad of the campaign stays (campaign_names). The next stage's flag


# ------------------------------------------------------------------ small tools
def facing(p, face):
    """(dx, dz) of a table's facing: a direction as it stands, or the way from p to a place (x, y, z)."""
    if len(face) == 2:
        return face
    return (face[0] - p[0], face[2] - p[2])


def put(S, name, pos=None, face=None, half=None, hidden=None):
    """kl_fa_author.place, with a box laid in the world's axes (F07's own turn of a re-placed box means nothing here)."""
    return A.place(S, name, pos, face, half, hidden, turn=BOX if face is None and half is not None else None)


def values(sc, k, name):
    return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][A.ctrl_of(sc, k, name)][1][1:-1])]


def world_of(e):
    """World place and rotation (rows) of an entity of a kl_scene.Scene, composed up its parents (kl_maps.world's rule)."""
    chain = []
    while e is not None:
        chain.append(e); e = e.parent
    Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], (0.0, 0.0, 0.0)
    for e in reversed(chain):
        r = struct.unpack('<9f', e.rot[:36]); t = struct.unpack('<3f', e.trans[:12])
        m = [r[6:9], r[3:6], r[0:3]]
        m = [[m[j][i] for j in range(3)] for i in range(3)]
        T = tuple(T[i] + sum(Rm[i][j] * t[j] for j in range(3)) for i in range(3))
        Rm = [[sum(Rm[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return T, Rm


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
    log('  kl_fa_bank: %s stands at (%d, %d, %d) (its group moved by (%d, %d, %d)); its drive is still F07\'s' % (VAN, *VAN_WAIT, *t))
    return R + VAN + '\\' + VAN_GROUP


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the bank. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
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
            pts, face = (START, TO_DOOR) if crook else (POLICE, FRONT)
            n = seen[crook, 'hero']
            p = pts[n % len(pts)]
            if not crook:
                p = tuple(p[a] + HENCH_SHIFT[a] * (n // len(pts) + 1) for a in range(3))
            A.place(S, t, p, facing(p, face))           # ... a player group along local -Z
            seen[crook, 'hero'] += 1
    log('  kl_fa_bank: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: stacks of F07's drop pools become loot that lies in the map (kl_fa_author's way, the values of stock
    # F02's money bags). Taken: the last 8 of the 108 of every mode (leaves 100, as six stock levels have) and the
    # last of the team-mode 25. finish() gives the vault's ones the briefcase model on the written level.
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    spots = [(p, value, GATE_VAULT) for p, _yaw, value in VAULT_LOOT] + [(p, value, False) for p, value in TELLER_LOOT]
    take = (sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-8:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[8 - len(spots):])[:len(spots)]
    if len(take) != len(spots) or len(spots) < 8:
        raise ValueError('%d pool stacks for %d loot places' % (len(take), len(spots)))
    loot = []
    for (name, k, i), (p, value, hide) in zip(take, spots):
        def fn(us):
            for j, v in enumerate(('ZMONEYCTRL_GAMEMODE_ALL', value, 'ZMONEYCTRL_TYPE_NORMAL', 'ZMONEYCTRL_VARIANT_NORMAL', 15000, 0.2, 1, 30.0, 800.0, 1000.0, 0, 0)):
                A.setv(sc, us, j, v)
        kl_fa.edit(sc, k, i, fn)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'TriggerBox2'), lambda us: A.setv(sc, us, 2, LOOT_REACH))
        A.place(S, k, p, hidden=hide)
        loot.append((name, hide))
    total = sum(v for _p, _y, v in VAULT_LOOT) + sum(v for _p, v in TELLER_LOOT)
    log('  kl_fa_bank: loot: %d in the vault (%s), %d at the tellers, %d in all' % (
        len(VAULT_LOOT), 'hidden until the beat\'s timer ends' if GATE_VAULT else 'shown', len(TELLER_LOOT), total))
    # escape: the one van where it will wait, the exit trigger names it alone (kl2 0x6c3f90 loops until one field is set)
    van = park_van(S, log)
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M03_A the campaign pre-pass must leave in. THIS HALF: none - every door takes 'Activate'
    itself (no proxy is kept: re/campaign_fa_bank.md 5, the second agent's note), and no squad stays (NO_AI).
    The next stage returns its squads (kl_fa_author.squad_plan's rule) and the campaign's single nodes here."""
    return ()


def strip(M, log=print):
    """On the converted Dead Men level, before the join. THIS HALF: nothing is taken off - the door leaves are map
    nodes that stay as they are (they are sunk on the JOINED scene: Doors). The next stage strips its squads here."""
    if M.name == LEVEL:
        have = sum(1 for p, _at, _set in LEAVES if M.prp.resolve(R + p)) + bool(M.prp.resolve(R + VAULT_DOOR))
        log('  kl_fa_bank: %s: %d of %d door nodes of the route found; no squad stays%s' % (
            M.name, have, len(LEAVES) + 1, '' if NO_AI else ' (NO_AI is off, but this file keeps none yet)'))
    return 0


# ------------------------------------------------------------------ 3. the joined scene
def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene
    (kl_prpjoin.Scene). Values and reference lists of existing controllers only."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_bank: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    leaves = must([R + p for p, _at, _set in LEAVES])
    door, body = must([R + VAULT_DOOR, R + VAULT_BODY])
    for p in leaves + [door]:                           # each takes 'Activate' itself
        msg = [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == sc.resolve(p)[0]]
        if msg != ['Activate']:
            raise ValueError('%s: MatPosAnim in-message %s, not one \'Activate\'' % (p, msg))

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['doors']] if DOORS_ANIMATE else []
    lists('monitor', 'AIMonitor', f2=have + start)
    lists('doors', 'AIDWrapper', f0=leaves if DOORS_ANIMATE else [], f1='Activate')
    if DOORS_ANIMATE:
        glass = [p for p in leaves if '\\GlassDoor_' in p]
        for p in glass:                                 # the clip goes there AND back: stop it at its open frame
            j = sc.resolve(p)[0]
            put_(j, 'MatPosAnim', **{'f%d' % MPA_LAST: GLASS_LAST})
        log('  kl_fa_bank: DOORS ANIMATE: %d leaves get \'Activate\' at the round start; %d glass leaves store LAST %d' % (len(leaves), len(glass), GLASS_LAST))

    # ---- the beat: ante-room box -> BEAT -> the vault door's swing, the loot; -> DOOR_GONE -> the door's body off.
    # The box is the form of stock F07's own box that starts a timer (FASpecials!POI!Trigger_POI_TheLootArea: field
    # 15 = 1; the squad boxes have 0). ASSUMPTION that 15 is 'once': the timer must not be started a second time
    gone = VAULT_DOOR_GOES and not VAULT_OPEN
    lists('beat box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', f15=1, f17=[R + ROLE['beat timer']])
    lists('beat timer', 'TriggerDelay2', f0=BEAT, f4=[R + ROLE['door'], R + ROLE['loot on']] + ([R + ROLE['door timer']] if gone else []))
    lists('door', 'AIDWrapper', f0=[] if VAULT_OPEN else [door], f1='Activate')
    lists('door timer', 'TriggerDelay2', f0=DOOR_GONE, f4=[R + ROLE['door off']] if gone else [])
    lists('door off', 'DeactivateGeom', f0='AITrigger', f1=[body] if gone else [])
    hidden = [R + sc.names[t] for t in sc.tops() if sc.names[t].startswith('FASpecials!DropMoney!') and kl_fa.node_values(sc, t)[3]
              and any(v[2] == 'ZMONEYCTRL_TYPE_NORMAL' for kk, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if kk == t)]
    if GATE_VAULT and len(hidden) != len(VAULT_LOOT):
        raise ValueError('%d hidden loot objects, the vault has %d' % (len(hidden), len(VAULT_LOOT)))
    lists('loot on', 'ActivateGeom', f0='AITrigger', f1=hidden)

    # ---- the way out: F07's 'exit heist' box in the foyer, with a line that fits a front door
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_fa_bank: sequence: ante-room box -> %.0f s -> the vault door %s, %d hidden loot objects on%s' % (
        BEAT, 'is sunk already (VAULT_OPEN)' if VAULT_OPEN else 'gets \'Activate\'', len(hidden),
        '; -> %.0f s -> the door\'s body off' % DOOR_GONE if gone else ''))
    log('  kl_fa_bank: wired: round start %s; %d briefing / reminder lines; exit line %s' % (
        '-> %d door leaves' % len(leaves) if DOORS_ANIMATE else 'starts no door (the leaves are open at build time)', len(LINES), EXIT_LINE))
    return {'hidden': hidden, 'leaves': leaves, 'monitor': have + start}


def layer_names(sc):
    """Top-level names of the layer in the joined scene: what kl_fa.repair's prune may cut dead references from."""
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    """One map: the layer is wired in the one build there is."""
    return True


# ------------------------------------------------------------------ the doors at build time
class Doors:
    """THE FALL-BACK THAT WALKS OFFLINE: the leaves of the route are taken out at build time. kl_graft.build calls
    three functions of kl_escape for every Dead Men map (the code path of the Fragile Alliance bank's yard wall,
    which bots cross live); for the length of one build they are wrapped - the study's build_open.py, unchanged in
    what it does (re/campaign_fa.md G1.1, G1.2: twelve leaves out, verify as before, the route free):
      repair          + each node of sunk() is moved DOOR_DY in WORLD y in the joined .prp (ZGEOM[2]). A leaf may
                        stand under a turned group (the four glass leaves do: after a world move of 2,500 down their
                        .prp y is 12), so the move is turned into the parent's frame; kl_escape.open_wall refuses such nodes
      place_entities  the real one, handed each node's new place in the .gms record's OWN parent frame ('move' entry;
                        the .prp and the .gms do not always hold the same local place: G1.1 trap 2), the two world
                        places held against each other before and after; + the moved entities' REF ids
      cut_collision   the real one, on those REF ids: their key-framed placements leave the joined .HVK
    arm() puts the wrappers in (prepare_host calls it: a plain 'kl_maps.py one ... --author kl_fa_bank' has no other
    place), the last wrapper that runs takes them out; doors() is the same as a context manager."""
    real, state = None, None

    @classmethod
    def sunk(cls):
        """Paths (below ROOT) of the nodes this build takes out."""
        return ([] if DOORS_ANIMATE else [p for p, _at, _set in LEAVES]) + ([VAULT_BODY] if VAULT_OPEN else [])

    @classmethod
    def arm(cls, log=print):
        if cls.real is None:
            cls.real = (kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision)
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.repair, cls.place, cls.cut
        cls.state = {'sink': {}, 'old': {}, 'prp_w': {}, 'rows': []}

    @classmethod
    def disarm(cls):
        if cls.real is not None:
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.real
            cls.real = None

    @staticmethod
    def prp_frame(sc, k):
        """World rotation (rows) of node k's PARENT frame from the .prp chain, and that parent's world place."""
        chain, j = [], sc.parent[k]
        while j > 0:
            chain.append(j); j = sc.parent[j]
        Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0]
        for j in reversed(chain):
            lab = J.labels('dd', sc.cls(j))
            v = kl_fa.node_values(sc, j)
            t, r = v[lab.index('ZGEOM[2]')], v[lab.index('ZGEOM[1]')]
            T = [T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3)]
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[b][a] for b in range(3)] for a in range(3)]
            Rm = [[sum(Rm[a][c] * m[c][b] for c in range(3)) for b in range(3)] for a in range(3)]
        return Rm, T

    @classmethod
    def prp_world(cls, sc, k):
        """World place of node k from the .prp chain alone."""
        Rm, T = cls.prp_frame(sc, k)
        t = kl_fa.node_values(sc, k)[J.labels('dd', sc.cls(k)).index('ZGEOM[2]')]
        return tuple(T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3))

    @classmethod
    def repair(cls, sc, log=print):
        done = cls.real[0](sc, log)
        st, tilted = cls.state, 0
        for path in cls.sunk() if sc.resolve(R + IN[:-1]) else ():      # only on a scene that holds the bank
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
            log('  kl_fa_bank: doors: %d nodes sunk by %g (world y) in the joined .prp; %d of them stand in a parent frame '
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
        refs |= {ents[k - 1].ref for k in st['sink']}   # the leaves' REF ids, for cut_collision
        for k in sorted(st['sink']):
            e = ents[k - 1]
            after = world_of(e)[0]
            if abs(after[0] - before[k][0]) > 0.5 or abs(after[2] - before[k][2]) > 0.5 or abs(after[1] - before[k][1] - DOOR_DY) > 0.5:
                raise ValueError('%s moved %s -> %s, not straight down by %g' % (sc.path[k], before[k], after, -DOOR_DY))
            if max(abs(after[a] - st['prp_w'][k][1][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: after the move the .gms says %s, the .prp %s' % (sc.path[k], after, st['prp_w'][k][1]))
            st['rows'].append((sc.path[k], e.ref, before[k], after))
        if st['sink']:
            log('  kl_fa_bank: doors: %d entities moved in the .gms (%d of them hold another local place there than in the .prp; '
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
            log('  kl_fa_bank: doors: %d placements (by shape type %s) were under the %d REF ids; none is left' % (sum(mine.values()), dict(mine), len(refs)))
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
def in_vault(p):
    return all(lo <= v <= hi for v, (lo, hi) in zip(p, VAULT_BOX))


def set_text(kids, key, text):
    """A text leaf at 'A/B/C' in a .LOC tree (kl_loc nodes), tables made on the way; an existing leaf gets the text."""
    import kl_loc
    tab = kids
    *path, name = [s.encode('latin1') for s in key.split('/')]
    for s in path:
        nxt = next((k for k in tab if k.name.lower() == s.lower()), None)
        if nxt is None:
            nxt = kl_loc.Node(s, kl_loc.TABLE, [])
            kl_loc._insert(tab, nxt)
        elif nxt.kids is None:
            raise ValueError('%s: %r is a leaf' % (key, s))
        tab = nxt.kids
    new = kl_loc.leaf(name, text.encode('latin1'), 0)
    old = next((k for k in tab if k.name.lower() == name.lower()), None)
    if old is None:
        kl_loc._insert(tab, new)
    else:
        old.flags, old.raw = new.flags, new.raw


def finish(folder, log=print):
    """What needs the WRITTEN level, in place, on a folder with <slot>_Main.zip -> [problems]. A level finished
    before is left as it is.
    0. The level is lightened (kl_graft's trim + slim, kl_fa_loot.lighten_first): F07's dead map models and the textures
       only they show go (.prm 85.7 -> 44 MB). It has to come before the dead chunk indices are handed out.
    1. The vault's loot shows a briefcase and stands on the floor (the trolley's: on its cartons) turned as VAULT_LOOT
       says: kl_fa_loot's way - the model root comes from Dead Men's M01_FA_A into dead indices, its materials get
       compiled shaders.
       The teller stacks keep F07's money bag: a bag on a bank counter needs no other prop (GUESS, the owner's eyes).
    2. The level's own texts: TEXTS into every language's .LOC, the settings' start windows onto them."""
    import kl_fa_loot as L, kl_chars as C, kl_light, kl_loc, kl_texmat as T
    from kl_port_check import workdir
    E = L.Edit(folder)
    sc, bad = E.sc, []
    loot = [k for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    vault = [k for k in loot if in_vault(E.at(k))]
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    dressed = not {E.ents[k - 1].model for k in vault} <= pool
    if len(vault) != len(VAULT_LOOT):
        bad.append('%d loot objects lie in the vault, VAULT_LOOT has %d' % (len(vault), len(VAULT_LOOT)))
    n0 = len(E.p.chunks)
    L.lighten_first(E, log)                             # always: what is checked and handed on is the lightened level
    if CASE and vault and not dressed:
        C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
        root, _box, slots = L.case_model(E, CASE, CASE_SCALE, log)
        lo, _hi = L._assets(E).bounds(root)             # of what is drawn: the model's underside goes onto the floor
        for k in vault:
            at = E.at(k)
            p, yaw, _value = min(VAULT_LOOT, key=lambda r: math.dist(r[0], at))
            if math.dist(p, at) > 1.0:
                bad.append('%s lies at (%d, %d, %d), which is no place of VAULT_LOOT' % (sc.names[k], *at))
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
        log('  kl_fa_bank: %d briefcases in the vault (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(vault), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_bank: %s: the vault\'s loot already shows models of its own: left as it is' % folder)
    # ---- texts
    langs = 0
    for ext in sorted(E.lv.ext):
        if not ext.lower().endswith('.loc'):
            continue
        kids = kl_loc.parse(E.lv[ext])
        if kids is None:                                # a stub (Dutch in every stock level)
            continue
        for key, text in TEXTS.items():
            set_text(kids, key, text)
        E.lv[ext] = kl_loc.build(kids)
        langs += 1
    for k, i, _v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, START_KEY % w)]) for f, w in START_FIELDS.items()])
    log('  kl_fa_bank: %d text keys in %d languages (the English text in each); settings fields %s name the start windows' % (
        len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ the checks
# the round's way, for tools/kl_route.py: the stations of re/campaign_fa_bank.md 4.3 (AI heisters' row), MEASURED on the mesh
ROUTE_IN = [('START', START[1]), ('dock door', (550, 200, -4650)), ('dock', (266, 202, -5002)), ('vault lobby', (394, 241, -7129)),
            ('glass door 2', (399, 240, -7614)), ('upper flight', (-70, -158, -9200)), ('cross corridor', (-75, -558, -10600)),
            ('ante-room', (400, -959, -11800))]
ROUTE_VAULT = [('vault', (399, -960, -12818))]
ROUTE_OUT = [('ante-room', (400, -959, -11800)), ('vault lobby', (394, 241, -7129)), ('airlock', (1100, 240, -7000)), ('stairs', (1538, 355, -5822)),
             ('foyer', (309, 803, -5624)), ('hall', (377, 801, -8423)), ('front entrance', FRONT), ('plaza', (281, 812, -9700)),
             ('street', (949, 702, -11105))]
# the five large blocks a level load asks of the 2 GB process (CLAUDE.md, 2026-10-10 01:35): 32.0 MB scratch, .fxc, .prm and
# .ANM + 0x60000 each, the whole .WAV beside the archive. No limit is known; the yardstick is what has loaded live many
# times in one process: Retomoto on the tab, 16.9 + 74.2 + 20.6 + 25.9 MB = 171 MB with the scratch block
BLOCKS_LIVE = 171.0
# the walk test of the loot's pick-up: (box x0, x1, z0, z1; a place the route test reaches) for the vault and the banking hall
LOOT_WALKS = (((-100.0, 1200.0, -13600.0, -12600.0), (399.0, -960.0, -12818.0)), ((-1300.0, 1900.0, -9500.0, -5700.0), (377.0, 801.0, -8423.0)))


def archive_of(folder):
    zips = [f for f in sorted(os.listdir(folder)) if f.lower().endswith('_main.zip')]
    if len(zips) != 1:
        raise ValueError('%s: expected one *_Main.zip' % folder)
    return os.path.join(folder, zips[0])


def read_built(folder):
    """-> (scene tree, kl_scene.Scene, its entities, {entity: world place}, kl_hvk.Hvk, .SND, English .LOC, sizes)."""
    arch = archive_of(folder)
    sc, snd, loc = kl_fa.load(arch)
    with zipfile.ZipFile(arch) as z:
        m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
        hvk = kl_hvk.Hvk(z.read(m['.hvk']))
        size = {e: z.getinfo(m[e]).file_size for e in ('.prm', '.fxc', '.anm', '.tex')}
        size['entries'] = struct.unpack_from('<I', z.read(m['.prm']), 4)[0]
    wav = [f for f in os.listdir(folder) if f.lower().endswith('_main.wav')]
    size['.wav'] = os.path.getsize(os.path.join(folder, wav[0])) if wav else 0
    return sc, scene, list(scene.entities()), kl_maps.world(scene), hvk, snd, loc, size


def inventory(folder, log=print):
    """What the layer consists of in a built level, with world places read back from it."""
    sc, _scene, ents, pos, _hvk, _snd, _loc, _size = read_built(folder)
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
    log('ESCAPE (the van only stands: the next stage lays its drive)')
    for k in range(1, len(sc.nodes)):
        names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if any(n in names for n in (kl_fa.EXIT, kl_fa.MONITOR, 'OnlineEscAnimatedVehicle', 'FakeTarget')) or sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k]:
            row(k)
    log('LEVEL BOUNDS')
    for k, _i, _v in kl_fa.controllers(sc, 'LevelBound'):
        row(k)
    log('DOORS')
    for path, _stock, name in LEAVES + [(VAULT_BODY, VAULT_BODY_AT, 'THE VAULT DOOR')]:
        k = A.node_of(sc, path)
        log('  %-16s %-48s %s' % (name, sc.path[k][-48:], at(k)))


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (and finished) folder -> [what is wrong]. problems: kl_graft.verify's
    list of the build, when the caller has it (else result.json beside the archive is read)."""
    import json, kl_route, kl_impact
    arch = archive_of(folder)
    import kl_fa_loot as L
    sc, scene, ents, pos, hvk, snd, loc, size = read_built(folder)
    bad = []
    def fail(s):
        bad.append(s); log('  FAIL: ' + s)
    # ---- kl_graft.verify, against KNOWN
    if problems is None and os.path.isfile(os.path.join(folder, 'result.json')):
        problems = json.load(open(os.path.join(folder, 'result.json'))).get('problems')
    for p in problems or ():
        why = next((w for t, w in KNOWN if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    # ---- kl_fa.check on the written archive
    import kl_arms
    fa = kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch))
    for f in fa:
        why = next((w for t, w in KNOWN if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
        log('  kl_fa: %s%s' % (str(f)[:230], '\n          = known: %s' % why if why else ''))
        if f.sev <= kl_fa.BROKEN and not why:
            fail('kl_fa.check: ' + str(f)[:200])
    ncov = len(kl_fa.controllers(sc, 'FFCoverList'))
    log('  cover lists (FFCoverList): %d' % ncov)
    if ncov != 1:
        fail('%d cover lists (a level needs exactly one)' % ncov)
    # ---- the doors, read back: each leaf DOOR_DY under its stock place and without a placement, or in its place with one
    # (what the BUILD did is read off the level, not off this module's flags: a leaf is 'sunk' when it stands DOOR_DY low)
    per = collections.Counter(kl_hvk.ref(i) for s in hvk.shapes for i in s.inst)
    gates, vault_ref, state = [], None, {}
    for path, stock, name in LEAVES + [(VAULT_BODY, VAULT_BODY_AT, 'the vault door')]:
        k = A.node_of(sc, path)
        e = ents[k - 1]
        low = abs(pos[e][1] - stock[1] - DOOR_DY) < 2.0
        state[path] = low
        ok = (low or abs(pos[e][1] - stock[1]) < 2.0) and abs(pos[e][0] - stock[0]) < 2.0 and abs(pos[e][2] - stock[2]) < 2.0 and bool(per[e.ref]) != low
        log('  door %-16s %-34s REF %-6d at (%d, %d, %d), %d placement(s): %s' % (name, sc.names[k][-34:], e.ref, *pos[e], per[e.ref],
                                                                              'sunk, no collision' if low else 'in its place, collides'))
        if not ok:
            fail('door %s: at (%d, %d, %d) with %d placements; its place in the level is (%d, %d, %d)' % (sc.names[k], *pos[e], per[e.ref], *stock))
        if path == VAULT_BODY:
            vault_ref = e.ref
        if not low:
            gates.append(e.ref)
    animate, vault_open = not state[LEAVES[0][0]], state[VAULT_BODY]
    if len({state[p] for p, _at, _set in LEAVES}) != 1:
        fail('the eleven leaves are not all in one state: %s' % sorted(n.split('\\')[-1] for n, low in state.items() if low))
    lv = kl_route.load(folder)
    path_of = {e.ref: sc.path[k + 1] for k, e in enumerate(ents)}
    van = [ref for ref, _far in lv.moved() if path_of.get(ref, '').startswith(R + VAN + '\\')]
    for ref, far in lv.moved():
        if ref not in van:
            fail('REF %d (%s): its collision placement stands %d from its entity' % (ref, path_of.get(ref, '?')[-60:], far))
    if van:                                             # THIS HALF: the van's group is moved, its key-framed bodies' placements are not
        log('  note: %d key-framed placements of the van still stand at F07\'s place (the van only stands at VAN_WAIT; Retomoto\'s vans '
            'drove so: ASSUMPTION that a key-framed body follows its entity). kl_map_escape.van_layer lays them in the next stage' % len(van))
    # ---- every spawn point, player group and loot place: on the START's mesh part, on free floor
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
    # ---- nobody starts inside a level bound or one of its warning boxes, and no station of the round lies in one
    # (the campaign's own three stand at the front with warn boxes up to 10 m into the street: world boxes of the turned ones)
    fr, boxes = L.frames(scene), []
    for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
        for j in [k] + [j for lst in v[0:2] for s in lst for j in sc.resolve(s)]:
            Rm, T = fr[ents[j - 1]]
            ext = [sum(abs(Rm[a][b]) * h for b, h in enumerate(kl_fa.node_values(sc, j)[8:11])) for a in range(3)]
            boxes.append((sc.names[j], [T[a] - ext[a] for a in range(3)], [T[a] + ext[a] for a in range(3)]))
    held = [(n, p, b) for n, p in list(zip(names, pts)) + ROUTE_IN + ROUTE_VAULT + ROUTE_OUT for b, lo, hi in boxes
            if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
    log('  level bounds: %d bound and warn boxes; %d of the %d spawn points, player groups and stations inside one' % (
        len(boxes), len(held), len(pts) + len(ROUTE_IN + ROUTE_VAULT + ROUTE_OUT)))
    for n, p, b in held:
        fail('%s at (%d, %d, %d) stands inside %s' % (n, *p, b))
    # loot: the pick-up test as read in kl2.exe (kl_fa_loot.in_reach: horizontal distance <= radius + 40, a height window)
    # from a place a walk reaches (kl_fa_loot.Floors), with MARGIN to spare. The walks start where the route test below
    # proves the crew comes: the vault's middle, the hall. Hidden things do not count here (the blown vault's rubble)
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2]]
    built = L.Built(arch)
    skip = built.soft() | built.hidden
    walks = [(L.Floors(hvk, box, skip=skip), start) for box, start in LOOT_WALKS]
    floods = [f.flood([start])[0] for f, start in walks]
    taken = 0
    for k, v in loot:
        at, radius = pos[ents[k - 1]], values(sc, k, 'TriggerBox2')[2]
        best = None
        for (f, _start), seen in zip(walks, floods):
            place, h, n = f.stand(seen, at, radius)
            if place is not None and (best is None or h < best[1]):
                best = (place, h, n)
        spare = radius + L.REACH_PAD - best[1] if best else None
        log('  loot %-46s %7d at (%5d %5d %6d) %s: %s' % (sc.names[k][-46:], v[1], *at, 'hidden' if kl_fa.node_values(sc, k)[3] else 'shown ',
            'taken from (%d, %d, %d), %d away, %d to spare, %d places' % (*best[0], best[1], spare, best[2]) if best else 'OUT OF REACH'))
        if best is None or spare < L.MARGIN:
            fail('loot %s at (%d, %d, %d) cannot be taken%s' % (sc.names[k], *at, ' with %d to spare (%d wanted)' % (spare, L.MARGIN) if best else ''))
        else:
            taken += 1
    log('  loot: %d objects, %d; %d can be taken' % (len(loot), sum(v[1] for _k, v in loot), taken))
    gated = {bool(kl_fa.node_values(sc, k)[3]) for k, _v in loot if in_vault(pos[ents[k - 1]])}
    for k, v in loot:
        tb = values(sc, k, 'TriggerBox2')
        hide = bool(kl_fa.node_values(sc, k)[3])
        if hide != bool(ents[k - 1].flags & HIDDEN) or (hide and not in_vault(pos[ents[k - 1]])) or len(gated) != 1:
            fail('loot %s: hidden %s in the .prp, flag %#x in the .gms, in the vault %s' % (sc.names[k], hide, ents[k - 1].flags, in_vault(pos[ents[k - 1]])))
        if tb[2] != LOOT_REACH or tb[3] != 1:
            fail('loot %s: TriggerBox2 radius %s, people-only %s' % (sc.names[k], tb[2], tb[3]))
    # ---- the route in the built collision, nothing removed at test time; what still stands is a gate of the round
    way = [p for _n, p in ROUTE_IN + ROUTE_VAULT + ROUTE_OUT]
    crossing = lambda r: sorted({(o['ref'], o['name']) for leg in r['legs'] for c in leg.get('crossed') or () for o in c['objects']})
    say = lambda r: 'FREE, %d m' % r['length'] if r['free'] else 'NOT free; crossed: %s' % [n for _r, n in crossing(r)]
    shut = kl_route.route(lv, way)
    log('  route, %d stations, the level as built: %s' % (len(way), say(shut)))
    if shut['free'] != (not gates) or any(r not in gates for r, _n in crossing(shut)):
        fail('the route as built: free %s, crossed %s; the doors that stand: %d' % (shut['free'], [n for _r, n in crossing(shut)], len(gates)))
    if not vault_open and not animate:                  # the default: five sets open from the load, the vault door the one gate
        if [r for r, _n in crossing(shut)] != [vault_ref]:
            fail('with the vault door in its place the route should be shut by that door alone: %s' % [n for _r, n in crossing(shut)])
        gate = kl_route.route(lv, [p for _n, p in ROUTE_IN + ROUTE_OUT[1:]])
        log('  route without the vault (yard -> ante-room -> hall -> street), as built: %s' % say(gate))
        if not gate['free']:
            fail('the way in and out is not free without the vault')
    if gates:
        opened = kl_route.route(lv, way, opened=gates)
        log('  route with the %d standing door(s) out: %s' % (len(gates), say(opened)))
        if not opened['free']:
            fail('the route is not free with the standing doors out')
    # ---- the chain, read back
    def named(role):
        return A.named(sc, A.node_of(sc, ROLE[role]))
    dead = [(r, s) for r in ROLE for s in named(r) if not sc.resolve(s)]
    for r, s in dead:
        fail('%s names %s, which is no node' % (ROLE[r], s))
    mon = named('monitor')
    if any(R + v in mon for r, v in ROLE.items() if r != 'doors') or (R + ROLE['doors'] in mon) != animate:
        fail('the round start names a ROLE object it must not: %s' % mon)
    if named('beat box') != [R + ROLE['beat timer']] or R + ROLE['loot on'] not in named('beat timer'):
        fail('the beat\'s chain is not box -> timer -> loot: %s / %s' % (named('beat box'), named('beat timer')))
    hid = [R + sc.names[k] for k, _v in loot if kl_fa.node_values(sc, k)[3]]
    if sorted(named('loot on')) != sorted(hid):
        fail('the loot\'s ActivateGeom names %d objects, %d are hidden' % (len(named('loot on')), len(hid)))
    last = {p: [v[MPA_LAST] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, p)] for p, _at, _set in LEAVES if '\\GlassDoor_' in p}
    if animate and (sorted(named('doors')) != sorted(R + p for p, _at, _set in LEAVES) or any(v != [GLASS_LAST] for v in last.values())):
        fail('the leaves stand, but the round start names %d of them and the glass leaves store LAST %s' % (len(named('doors')), sorted(last.values())))
    if not animate and named('doors'):
        fail('the leaves are sunk, but the round start still sends %d of them \'Activate\'' % len(named('doors')))
    if vault_open == bool(named('door')) or (bool(named('door off')) and R + ROLE['door timer'] not in named('beat timer')):
        fail('the vault door is %s, but its wrapper names %s and its DeactivateGeom %s' % ('sunk' if vault_open else 'in its place', named('door'), named('door off')))
    log('  chain: round start -> %s; ante-room box -> %s -> %s' % ([s.split('!')[-1] for s in mon], ROLE['beat timer'].split('!')[-1], [s.split('!')[-1] for s in named('beat timer')]))
    # ---- the van's ZFakeTarget: inside the vision space, by kl_fa_bots_dyn's rule (the 0x686a66 crash: a target that
    # cannot register writes behind ZCheckVisible's table every frame; re/crash_686a66.md)
    try:
        import kl_fa_bots as FB, kl_fa_bots_dyn as D
        B = FB.Built(folder)
        space = D.vision_space(B)
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
    log('  texts: %d keys of the level\'s own, %d lines' % (len(TEXTS), len(LINES)))
    # ---- weight
    for b in kl_impact.check(arch):
        fail('kl_impact: ' + b[:200])
    blocks = 32.0 + sum(size[e] + 0x60000 for e in ('.prm', '.fxc', '.anm')) / 1e6 + size['.wav'] / 1e6
    log('  chunk table: %d entries (the tools\' line: %d); .prm %.1f, .fxc %.1f, .ANM %.1f, .WAV %.1f MB; the five load blocks %.0f MB (Retomoto on the tab: %.0f)' % (
        size['entries'], kl_impact.CHUNK_SAFE, size['.prm'] / 1e6, size['.fxc'] / 1e6, size['.anm'] / 1e6, size['.wav'] / 1e6, blocks, BLOCKS_LIVE))
    if blocks > BLOCKS_LIVE:
        fail('the five load blocks are %.0f MB, more than has loaded live (%.0f)' % (blocks, BLOCKS_LIVE))
    log('kl_fa_bank.check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def test(out, keep=False, log=print):
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1."""
    with doors(log):
        r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_bank')
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    folder = os.path.join(out, '%s+%s campaign' % (HOST, LEVEL))
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
        global DOORS_ANIMATE, VAULT_OPEN, VAULT_DOOR_GOES, GATE_VAULT, CASE, BEAT
        DOORS_ANIMATE = '--doors-animate' in a
        VAULT_OPEN = '--vault-open' in a
        VAULT_DOOR_GOES = '--vault-stays' not in a
        GATE_VAULT = '--loot-shown' not in a
        CASE = None if '--loot-bags' in a else CASE
        if '--beat' in a:                               # OPTION, seconds from the ante-room box to the vault door
            BEAT = float(a[a.index('--beat') + 1])
        sys.exit(test(a[1], '--keep' in a))
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'inventory':
        inventory(a[1])
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_bank                   # kl_graft imports this file by name: one module, one set of flags
    kl_fa_bank.main()
