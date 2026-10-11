#!/usr/bin/env python3
"""
The Fragile Alliance layer of THE VAULT: the bank the campaign way (Dead Men M03_A, chapter 3 'Withdrawal',
alone, under Dog Days F07) - a second bank map beside the Fragile Alliance bank M03_FA_A. Authored from stock
objects, offline, on the pattern of kl_fa_author.py (Retomoto Tower). The study: re/campaign_fa.md 4.1,
re/campaign_fa_bank.md 4.3 / 8.3 / 8.4; the build stage by stage, every check with its output and the list of
what only a live run can settle: re/bank_campaign.md. Nothing here installs anything or starts the game.

    python kl_fa_bank.py test <out> [--keep] [options]    build F07 + M03_A with the layer into <out> (build(): the
                                                          van's plan on a bare graft, then kl_maps.one inside
                                                          kl_map_escape.van_layer), finish() on the written level,
                                                          check(); exit 1 if a problem is left that is not in KNOWN
    python kl_fa_bank.py finish <built folder>            what needs the WRITTEN level, on a folder build() made: the
                                                          vault loot's briefcases, the level's own texts
    python kl_fa_bank.py check <built folder>             every check of this layer on a built folder
    python kl_fa_bank.py inventory <built folder>         the layer with world places read back from the level
    python kl_fa_bank.py bots <finished folder> <out>     the seven AI heisters into a copy (kl_fa_bots.build with
                                                          BOT_OPT and the vault gate: bots_gate), then bots-check
    python kl_fa_bank.py bots-check <folder>              the gate and the vault's loot window on a folder with the
                                                          squad, before or after kl_fa_bots_dyn's step
    python kl_fa_bank.py seal <folder>                    in place, the LAST step of the finishing chain: room list
                                                          entries that name an entity outside the map (the bots'
                                                          squad group took the id the graft parked them on) go to
                                                          the scene's free REF id
    python kl_fa_bank.py reverify <folder>                kl_graft.verify's cross-reference tests on the level as
                                                          WRITTEN (check does it too): exit 1 on a problem
    options of 'test' (one flag each for the live runs):
      --doors-animate   the eleven door leaves of the route stay where the level has them and get 'Activate' at
                        the round start (default: they are OPEN AT BUILD TIME - sunk, their collision cut)
      --vault-open      the vault door is sunk at build time too (a first load in which no door can stop anybody)
      --vault-stays     the vault door is not switched off after its swing (default: it goes away DOOR_GONE s later)
      --loot-shown      the vault's loot lies there from the start (default: hidden until the beat's timer ends)
      --loot-bags       the vault's loot keeps F07's money bags (finish() leaves the models alone)
      --beat S          seconds from the ante-room box to the vault door (default BEAT)
      --no-ai           no squad of the campaign stays and none of F07's police: a round without enemies, for a first
                        live run (the beat, the loot and the music are as with them)
      --alarm-lights    the 22 lights of the alarm lamps keep their LightToggle and light at the alarm (default: the
                        controller is taken off and the lights hidden - a kind no stock Dog Days level runs)
      --music-layer4    the nine fades of the break-in set's fourth layer keep their controller and are named
                        (default: taken off - a value no stock Dog Days level has; needed once the clips play)
      --blast-real      the vault's blast with the campaign's own reach and damage (default: a harmless show)
      --no-blast        the vault stays intact: no blast, no swap to the blown vault
      --dead-men-rows   the campaign's soldiers keep Dead Men's rows (default: stock rows by weapon class)
      --plan FILE       the van's plan from a file (the van.json beside an earlier build, or 'kl_map_escape.py
                        van-plan <bare graft> --points ... --json'): no bare graft is built for it (60 s less)

THE ROUND
  START   roped down in the secure yard, two stacks of four beside the loading dock's roller door.
  IN      dock -> vault lobby -> two flights down -> the vault's ante-room. Six door sets stand in series on the
          way in and out (re/campaign_fa_bank.md 8.3): five of them are open from the load, the vault door is the beat.
          13 guards hold the dock and the vault lobby, three pairs the way down (STAGE 'start' / 'down': they come
          into the world SQUADS_AT seconds after the round-start event, just after GO).
  BEAT    a box in the ante-room starts, all at once: six timers that pull the vault door's six locking rods one
          by one, 14 police who come down behind the crew (they come into the world behind the airlock, off the
          way in: BEAT_MEN), the music's rise, and the beat's timer. The box fires ONCE. When the timer ends
          the vault door gets 'Activate', the loot appears, the alarm goes (sound, lamps), the music changes to
          the way-out set, five squads hunt into the vault and three of F07's own police squads take the banking
          hall. DOOR_GONE seconds later the door's body is switched off - the vault can be entered whatever the
          swing did - and the vault blows (VAULT_BLAST: a harmless show; the intact vault is swapped for the blown one).
  LOOT    seven briefcases in the vault (six at the deposit-box walls, one in the middle of the room), four
          stacks on the teller counters of the banking hall.
  OUT     up the airlock stairs into the hall; the foyer box brings the plaza's seven squads (20 men, two SWAT
          fours with rifles); out of the front entrance, onto the plaza: the exit box calls the van.
  ESCAPE  F07's first key-framed van on ROAD (kl_map_escape's way-point front end): it waits at the west end of
          the front square on the designers' own in-road, drives 48 m in 7.2 s to its stop in front of the plaza
          (nose east-north-east; its rear doors are 18 - 20 m from the front entrance), and leaves east along their away
          road, 71 m in 8.48 s, passing the campaign's east level bound 26 m after the stop as every stock van
          passes one. Boarding box, kill box, path blocker, in-van and fixed camera are the van's own, moved with
          it; F07's second and third van are not in the level (VAN). The escape marker stands beside the lane,
          4 m from the drive (ESC_AT), not on the van's stop.

HOW (as kl_fa_author: no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  The nine names of kl_graft.AUTHOR_NAMES: HOST, prepare_host(S), strip(M), KEEP, DROP, layer_names(Jn),
  complete(Jn), wire(Jn), campaign_names(level). On top of them, because the interface has no place for it:
  1. THE DOORS AT BUILD TIME (Doors): three functions of kl_escape that kl_graft.build calls for every Dead Men
     map are wrapped for the length of ONE build - the recipe of the study's G:/kl_scratch/cfa_fill1/build_open.py
     (re/campaign_fa.md G1.1, with its two traps). prepare_host() puts the wrappers in, the last of them takes
     them out again; 'with doors(): ...' does the same from a script.
  2. finish(folder), on the written level (chunk numbers and the .LOC exist only then): the briefcase model
     (kl_fa_loot.case_model, into dead chunk indices), and the level's own texts (.LOC keys, settings fields).
  3. THE VAN (build()): its plan needs the collision of a BUILT level without the layer, and its collision
     placements are set in kl_hvk.join, which no name of the interface reaches - so build() makes a bare graft
     for the plan, hands it to prepare_host() / wire() (lay_van) and wraps the build in kl_map_escape.van_layer.
     'kl_maps.py one ... --author kl_fa_bank' alone therefore stops in prepare_host with a line that says so.

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
import kl_map_escape as ESC             # the van: plan from way points, F07's keys laid on it, its check
from kl_prp import units

HOST, LEVEL = 'F07', 'M03_A'
TITLE = 'The Vault'                     # the map's name (for the menu page: kl_expansion's table, a later stage)
R = 'ROOT\\'
IN = 'Locations/M03_A/M03A_Locations.zip\\Locations/M03_A/M03A_LOC_Inside.zip\\'
VA = IN + 'Locations/M03_A/M03A_LOC_Ins_Vault.zip\\'
HIDDEN = 0x400
# problems kl_graft.verify reports that this layer cannot remove: (text looked for, why it stands)
KNOWN = (('stream clips are not in the merged stream file', 'the level\'s music (MUSIC_CLIPS), its vault ambience and nine guard lines have no record in '
          'the built .WHD - they are not in the installed PC_Def.str; a larger stream file is the owner\'s go-ahead (re/campaign_fa.md 3.1 K): those sounds '
          'are silent, nothing else. (The kept guards\' other one-liners DO stream from the merged file; result.json\'s list of names is longer than what '
          'is lost - check() reads the built .WHD: lost_clips)'),)
# ... and in a build without enemies ('--no-ai'), which check() knows by the level having no squad at all
KNOWN_NO_AI = ('no ZSquadScript', 'a round without enemies (NO_AI): the build for a first live run')

# ------------------------------------------------------------------ the bank (M03_A), measured
# Floors (collision, tools/kl_route.py stations on a built level): yard and loading dock y 200, vault lobby 240,
# vault and ante-room -960, banking hall and plaza 800, front street 700. Everything below is on ONE part of the
# navigation mesh (566 polygons; re/bank_campaign.md T3).
YARD = 200.0                            # (the dock's roller door M03_A_Garage_01a\SI0201_M03_BackDorAnim_01: doorway x 385..735, z -4706)
FRONT = (300.0, 800.0, -9350.0)         # the front entrance: no door, a 2.0 m gap between two glass wings (x 200..400, z -9410)
TO_DOOR = (0.0, -1.0)                   # from the yard at the dock door
# THE ESCAPE MARKER (the HUD's 'go here') stands BESIDE the van's lane, between the plaza and the place where the
# van's rear doors will be: MEASURED 425 from the drive's line and 357 from the boarding place, on the START's
# mesh part and on free floor (C:/kl_scratch/bank/fix_1/s/lane.py). The first three stages had it over the van's
# STOP: the van is called when the plaza is entered, 18 m away, and takes 7.2 s - a running player stood on the
# marker before the van's nose came, and the van's KillBox (180 wide, at its nose) 'kills what it runs over'
# (re/map_escape.md). Stock F07's marker stands 3 m off the nearest of its three stops, on none of them
# (review round 1). GUESS: the place itself (the bots' own waiting place beside the stop, kl_fa_bots' AllyEscapeBox)
ESC_AT = (316.0, 702.0, -11070.0)       # on the street's floor (y 700): the round's last station (ROUTE_OUT)
ESC_POI_UP = 188.0                      # the marker over the floor (F07: 190 over its road; Retomoto's)
ESC_POI = (ESC_AT[0], ESC_AT[1] + ESC_POI_UP, ESC_AT[2])
# START (re/campaign_fa.md 4.1 item 1): two stacks of four beside the dock door, under the back wall where the
# campaign's ropes end ((-35 / -151, 200, -4525)). GUESS: the stacks; MEASURED: each point on the mesh and on free
# floor (check()). A parked armoured transport (x -30..190, z -4130..-3590) stops the rows moving west.
START = [(float(x), YARD, -4350.0) for x in (150, 250, 350, 450, 700, 800, 900, 1000)]
TRAITOR = [(float(x), YARD, -4000.0) for x in (300, 530, 770, 1000)]            # GUESS: behind the stacks
# police who come back: the front street, at the places of the campaign's own plaza police (re/campaign_fa.md
# 4.1 item 7: 'Police_OutSide_01' west (x -1842..-1437), 'Police_Outside_Teargas_01' east). GUESS: the points inside
# those spans; the west row begins at x -1750: the campaign's own warn box of its west level bound reaches x -1805.
# Those squads STAY (STAGE 'plaza': their men stand at z -9686..-9397), so the rows are 2 m beyond them, towards
# the street (z -9900): no point or police body within POLICE_CLEAR of a squad's man (check())
POLICE = [(-1750.0, 705.0, -9900.0), (-1650.0, 705.0, -9900.0), (-1545.0, 705.0, -9900.0), (-1437.0, 705.0, -9900.0),
          (2016.0, 706.0, -9900.0), (2100.0, 706.0, -9900.0), (2178.0, 706.0, -9900.0)]
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
# (place on the floor, degrees the case is turned, value). GUESS: every place, turn and value
# (the study: 'about 2.6 million'; F07's own loot: 5 x 800,000). The places are 100 in front of their wall:
# the blown vault 'Vault_POST', which the beat's blast shows in place of the intact one, has its rubble at the
# walls' feet (floors y -879 at z -13350 and x 70) and a heap of it at x 400..500, z -13310..-13200 (top y -891):
# a case must lie where BOTH vaults have bare floor (check(): 'buried'). So the south wall's cases lie at x 200,
# 300 and 600, and the big one in the middle of the room - not on the trolley's cartons, which go with the
# intact vault (the first half had it there).
VAULT_LOOT = [((200.0, -960.0, -13310.0), 8.0, 300000), ((300.0, -960.0, -13310.0), -6.0, 300000), ((600.0, -960.0, -13310.0), 11.0, 300000),
              ((110.0, -960.0, -13230.0), 96.0, 300000), ((110.0, -960.0, -13030.0), 84.0, 300000), ((110.0, -960.0, -12830.0), 101.0, 300000),
              ((430.0, -960.0, -12950.0), 20.0, 500000)]            # the last: the middle of the room, before the door
VAULT_BOX = ((-50.0, 1150.0), (-1000.0, -400.0), (-13560.0, -12650.0))      # the room, for finish() / check(): what lies in the vault. GUESS: the
                                                                            # box, drawn round the walls' places above with room to spare
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
BOX_PER_MAN = 15                        # TriggerBox field: 1 = fires for every criminal that enters, 0 = once (wire(): the census)
DOOR_GONE = 6.0                         # s after the door's 'Activate'. GUESS: the swing is at its 100 degrees after 2.4 s

# ------------------------------------------------------------------ the host's layer
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put (kl_fa_author.PARK)
BOX = (0.0, 1.0)                        # a box is laid in the world's axes (the turn that leaves local +Z where it is)
# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # the round's markers and planes
    'FASpecials!POI!Trigger_POI_TheLootArea': ((575, 350, -4150), None, (700, 200, 450), 'GUESS: box round the START stacks in the yard (F07: round its start); it starts the loot marker\'s 11 s timer'),
    'FASpecials!POI!POI_TheLootArea': ((400, -800, -13000), None, None, 'the vault\'s middle; GUESS: 160 over its floor'),
    'FASpecials!PIP!EnterLootArea': ((560, 380, -4800), None, (250, 230, 50), 'GUESS: a plane 1 m inside the dock\'s roller door (doorway x 385..735, z -4706)'),
    'FASpecials!PIP!ExitLootArea': ((303, 974, -9407), None, (300, 200, 100), 'the front entrance: M03_FA_A\'s own ENTERS box there (Triggers!EnterBankTrigger_01), same world'),
    'FASpecials!POI!POI_TheEscapeArea': (ESC_POI, None, None, 'BESIDE the van\'s lane, not over its stop (ESC_POI); prepare_host() holds it against the PLAN\'s drive'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((300, 1075, -10550), None, (1500, 425, 1150), 'GUESS: plaza and street as the exit box (z -11700..-9400), y 650..1500. NOT the banking hall: '
                                                 'the box takes the loot marker away (GeomDeactivator_TheLootArea), and the hall is reached from the vault lobby without the vault (review round 1)'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((300, 1075, -10550), None, (1500, 425, 1150), 'as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((300, 1075, -10550), None, (1500, 425, 1150), 'as above'),
    # the beat's box and the exit
    'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou': ((460.4, -714.0, -12151.8), None, (550.2, 254.0, 556.1), 'the campaign\'s own box GamePlay!4_Vault_Part!...\\TB_VbByVault: place and half extents'),
    'Gameplay!EscapeSetup!otrExitLevel': ((300, 800, -10550), None, (1500, 300, 1150), 'GUESS (the study): plaza and street in front of the entrance, from 50 beyond its gap: z -11700..-9400 - carried '
                                          '500 farther south than the study\'s, so that it holds the van\'s stop AND its boarding place as the box of every stock level does (12 vans of F01 F04 F05 F07)'),
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
        'beat timer': 'Gameplay!010_FirstFight!RivalMercVan!Timer',                  # TriggerDelay2 BEAT: the gate of the round
        'door': 'Gameplay!010_FirstFight!RivalMercVan!Activator_VanSound',           # AIDWrapper 'Activate' -> the vault door
        'door timer': 'Gameplay!010_FirstFight!RivalMercVan!TimerVanGo',             # TriggerDelay2 DOOR_GONE
        'door off': 'Gameplay!010_FirstFight!RivalMercVan!GeomDeactivator_DriveInVan',   # DeactivateGeom -> the door's body
        'loot on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT',    # ActivateGeom -> the vault's hidden loot
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel',
        # the second half: the squads' start, the music, the six rods, the vault's blast
        'start timer': 'Gameplay!010_FirstFight!RivalMercs!Timer',                   # TriggerDelay2 SQUADS_AT -> the first squads
        'music timer': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!Timer',  # TriggerDelay2 MUSIC_AT -> the break-in set
        'post on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_RIGHT',   # ActivateGeom -> the blown vault, fire, smoke
        'pre off': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!GeomDeactivator'}    # DeactivateGeom -> the intact vault
FF = 'Gameplay!010_FirstFight!'
ROLE.update(('rod timer %d' % (i + 1), FF + n) for i, n in enumerate((               # six TriggerDelay2, one a rod
    'RivalMercs!RandomizeFight!Timer_LEFT', 'RivalMercs!RandomizeFight!Timer_RIGHT', 'RivalMercs!DisableVisionBlocker!TimerInputAI',
    'RivalMercVan!Timer_PFBlocker', 'RivalMercVan!CoverStateChangerHero!Timer', 'RivalMercVan!TimerMercsVanExit')))
ROLE.update(('rod %d' % (i + 1), FF + n) for i, n in enumerate((                     # six AIDWrapper 'Activate' -> a rod
    'RivalMercVan!CoverStateChangerHero!ActivateCovers', 'RivalMercVan!CoverStateChangerHero!DeactivateCovers',
    'Shutters!Activator_Shutter_Close_RIGHT', 'Shutters!Activator_Shutter_Close_LEFT', 'Shutters!Activator_Shutter_LEFT',
    'Shutters!Activator_Shutters_RIGHT')))
# FOR THE NEXT STAGES. Free single top-level objects of F07 this file does not touch (add the name to KEEP_MORE, give
# it a ROLE): trigger boxes Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou, Gameplay!030_AfterLoot!tbExitFinancialAlley,
# Gameplay!020_Loot!tbExitLoot, Gameplay!020_Loot!FollowPlayers!tbCountPlayers, Gameplay!040_Escape!tbEscapeAI,
# Gameplay!RunToEscape!tbRunToEscape, ...!tbRunToEscape1Player; counters Gameplay!020_Loot!FollowPlayers!TriggerCounter,
# Gameplay!RunToEscape!tcRunToEscape; six more TriggerDelay2 (Gameplay!010_FirstFight!Shutters!TimerShuttersClose_RIGHT,
# ...TimerShuttersClose, ...TimerShuttersOpenDif, ...TimerShuttersOpen, ...PF_Blocker!Timer_PF_LEFT / _RIGHT) and the
# three of Gameplay!RunToEscape!. NO AIDWrapper, ActivateGeom or DeactivateGeom of F07 is free any more; the campaign has
# single ones (GamePlay!5_Lobby!LobbySlidedoors!LockLobbyDoor ...) that stay when campaign_names() names them.
# Five of the timers are named by F07's AIMonitor at the round start (RivalMercVan!Timer and TimerVanGo among them):
# wire() writes the monitor's list, so that a ROLE object is started only by what this file names.
KEEP_MORE = ()
# the escape: F07's first van, its relay, the exit trigger and the two 'last van' objects (the monitor is kept by
# kl_fa.host_keep) = kl_map_escape.VAN_KEEP + three. F07's SECOND AND THIRD VAN ARE NOT KEPT: a van without a use
# cannot be parked under the map as Retomoto's street layer did (its ZFakeTarget outside the rooms' bounds is the
# 0x686a66 crash, re/crash_686a66.md), and a level with ONE van is the form the three car maps on the owner's tab
# run (re/map_escape.md 10). The exit trigger names the one van in field 2 and nothing in 3..5.
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'       # everything of the van with a place is below it (kl_fa_author.place_vans)
# THE VAN'S ROAD (re/bank_campaign.md T2.4: 'the passing plan'; kl_map_escape.van_plan_points makes the plan of it
# against the map's collision - keys, boarding box, camera, bounds - and van_prepare lays F07's keys on it):
#   arrive  the first three points of the designers' own in-road on the front square: the van waits at the first,
#           43 m west of the stop (48 m of drive), beyond the campaign's west bound - and IN SIGHT of the plaza: the
#           square is open (re/bank_campaign.md L3.4)
#   stop    in front of the plaza, the origin of the standing van. MEASURED: the lane is clear 220, 260 and 320 wide;
#           the first agent's stop (250, 707, -10700) has 4 m of lane (T2.4). The heading is the curve's (67: nose
#           east-north-east, the rear doors west-south-west); heading 90 passes too - taste, not chosen
#   leave   the designers' away road, and from its end (3958, 713, -11173) the same line carried on east to x 8600.
#           GUESS that it looks like a road out there: MEASURED are the collision floor (y 700.0, unbroken) and the
#           furniture beside it (out to x 8000); without the extension the drive away is 24 m, under MIN_OUT
#   cam     None = kl_map_escape.cam_spot's eye (GUESS: 18 m behind the stop, 330 over the square)
ROAD = dict(arrive=[(-3248, 710, -11859), (-1917, 712, -12126), (-231, 707, -12332)], stop=(949, 704, -11105),
            leave=[(2473, 705, -11177), (3958, 713, -11173), (8600, 705, -11173)], at='origin', heading=None, cam=None)
PLAN = None                             # the plan of ROAD (lay_van): prepare_host() and wire() lay the van on it
NO_PLAN = ('kl_fa_bank: the van has no plan: build with \'kl_fa_bank.py test <out>\' or kl_fa_bank.build() (the plan is made on a bare graft and '
           'kl_map_escape.van_layer has to stand round the build; \'kl_maps.py one ... --author kl_fa_bank\' can do neither)')
BOARD_NEAR = 30.0                       # the boarding place is a station of the round: on the START's mesh part and on free
                                        # floor within this (the measure of the spawn points)
LANE_CLEAR = 250.0                      # no spawn point, player body, squad's man, escape marker or station of the way out
                                        # nearer than this to the van's drive (the lane that is tested is 110 either side;
                                        # the van's kill box is 90). GUESS. The boarding place is the one exception: the box
                                        # rides on the van, a player goes there when the van STANDS
BOUND_AFTER = 1000.0                    # a level bound on the drive away at least this far after the stop: every stock
                                        # Dog Days van passes one with its passengers, the nearest 10.9 m after the stop
                                        # (F01; F07's own 18.6 .. 39.8 m; MEASURED C:/kl_scratch/bank/l3/s/stockbound.py)
ESCAPE =('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith('Gameplay!0'))


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_bank.KEEP at the moment of use
        more = tuple(KEEP_MORE) + (() if NO_AI else tuple(HALL))        # F07's three police squads of the banking hall
        return _KEEP + tuple(x for x in more if x not in _KEEP)
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

NO_AI = False                           # True ('--no-ai'): no squad stays, no F07 police - the round without enemies of
                                        # the first live run (the beat, the loot, the van and the music are as with them)

# ------------------------------------------------------------------ the enemies
# THE CAMPAIGN'S SQUADS THAT STAY: kl_fa_author.squad_plan's rule (a subtree of plain squad objects with an actor
# and a behaviour rout; mini-cutscene controllers come off), asked of the real function with these name roots.
# 22 squads / 53 men (re/campaign_fa_bank.md 4.1, 8.2). What does NOT stay under the rule: the six police-car
# squads, the shield SWAT, both helicopters, the snipers, the eight hall guards (no rout), the story's own crew
# (every ZMercSquad / ZFusionSquad: the vault breaker's vault sequence among them) and 22 civilians.
SQUAD_ROOTS = ('GamePlay!', 'COOP!')
G3, G4, G5, CO = 'GamePlay!3_Garage_Part!', 'GamePlay!4_Vault_Part!', 'GamePlay!5_Lobby!', 'COOP!Squads_Lobby!'
# squad -> stage. A squad whose ZSquadScript field 3 is 0 is NOT IN THE WORLD until one of its routs is named
# (re/map_ai.md 2: seen live on Retomoto, 'they spawn in'); wire() names the start rout squad_plan found, by stage:
#   'start'  dock and vault lobby, 13 guards: the round's start timer (SQUADS_AT)
#   'down'   the three guard pairs of the way down (upper flight, cross corridor, ante-room): with them
#   'beat'   14 police: the ante-room box. Their defend places run down the stairs towards the ante-room (the last of
#            'Vault_Reinforcement_Police_03' is (396, -956, -12332)): they come down behind the crew. Three of these
#            squads and two of 'start' have the campaign's hunt (HUNT), named when the beat ends
#   'plaza'  the front street's seven squads / 20 men (two SWAT fours with rifles): the foyer box
# GUESS: the split (the study's: re/campaign_fa.md 4.1 items 3 - 7); MEASURED: where each stands (check())
STAGE = collections.OrderedDict([
    (G3 + 'PatrolGuards_01a', 'start'), (G4 + 'Guards_Reinforcement_StayUpstairs', 'start'), (G4 + 'Guards_Reinforcement_StayUpstairs#01', 'start'),
    (G4 + 'Guards_Reinforcement_01a', 'start'), (G4 + 'Guards_Reinforcement_01b', 'start'),
    (G4 + 'Guards_01', 'down'), (G4 + 'Guards_02', 'down'), (G4 + 'Guards_03', 'down'),
    (G4 + 'Police_Reinforcement_02', 'beat'), (G4 + 'Police_Reinforcement_03', 'beat'), (G4 + 'Police_Reinforcement_Teargas_01', 'beat'),
    (G4 + 'Police_Reinforcement_Teargas_01#01', 'beat'), (G4 + 'Vault_Reinforcement_Police_01', 'beat'),
    (G4 + 'Vault_Reinforcement_Police_02', 'beat'), (G4 + 'Vault_Reinforcement_Police_03', 'beat'),
    (G5 + 'Police_OutSide_01', 'plaza'), (G5 + 'Police_Outside_Teargas_01', 'plaza'), (CO + 'Police_OutSide_SWAT_02', 'plaza'),
    (CO + 'Police_OutSide_SWAT_03', 'plaza'), (CO + 'Police_OutSide_SWAT_02_ShieldSupport', 'plaza'),
    (CO + 'Police_OutSide_SWAT_03_ShieldSupport', 'plaza'), (CO + 'Police_Reinforce_Wave1_COOP_03', 'plaza')])
# the rout a stage names, where it is not the one squad_plan finds (the lowest-named rout a campaign trigger names).
# The two single SWAT men's is '080_Cutscene_MoveOutside' - a place ON the van's stop ((894, 709, -11061), the stop is
# (949, 702, -11105)); their '050_Move_In_01' takes them into the banking hall instead, as the campaign's own
# modifier '040_' does: the police follow in while the crew comes out
START_ROUT = {CO + 'Police_OutSide_SWAT_02_ShieldSupport': '050_Move_In_01', CO + 'Police_OutSide_SWAT_03_ShieldSupport': '050_Move_In_01'}
# five squads have the campaign's hunt: a modifier '49_SquadMod' (unleash, fire at will) that names '50_HuntBehaviour',
# whose search box is IN THE VAULT (427, -733, -12986). Named when the beat ends: they come for the crew at the loot
HUNT = '49_SquadMod'
SQUADS_AT = 10.0                        # s from the round-start event to the first squads. That event comes when the 8 s
                                        # countdown BEGINS, 8.4 - 8.8 s before GO (kl_fa_author.BLAST_DELAY's note, two clock
                                        # readings); a squad that waits is not in the world, so nobody is shot in the countdown
                                        # through the open dock door (Retomoto's run S2). GUESS: 10
MAN_OFF, MAN_IN = 60.0, 15.0            # snap_men: a man this far beside the mesh at most is put this far inside it. GUESS
# WHERE THE 14 POLICE OF THE BEAT COME INTO THE WORLD. The campaign has them in the dock and the vault lobby (seven
# within 4.5 m of the route's own station there, the nearest 165 from it): right for a story in which everybody is
# down at the vault when they come, wrong here - the box fires for the FIRST criminal in the ante-room (an AI heister,
# some 35 - 40 s after GO), and a human still fighting the 13 guards upstairs would get 14 police out of the air at
# arm's length (review round 1). So their men are re-placed (strip: beat_men) BEHIND THE AIRLOCK, off the way in:
# eight in the corridor that leads from the airlock to the hall's stairs (x 1467..1625, flat floor y 240 from
# z -7125 to -6050; round the corner from the airlock's doorway) and six on the landing above its stairs (floor
# y 420). From there their own defend routs bring them through the airlock and the lobby and down: they still come
# down behind the crew, on foot. MEASURED (C:/kl_scratch/bank/fix_1/s/beat_floor.py): each place on the START's mesh
# part and on free collision floor, the nearest 1195 from a station of the way in. GUESS: the places themselves, and
# 100 - 125 between two men. ASSUMPTION: a defend rout walks its men from wherever they stand on the mesh.
# None: the campaign's places stay (check() then fails on BEAT_CLEAR)
BEAT_MEN = [(1510, 240, -6700), (1585, 240, -6610), (1510, 240, -6520), (1585, 240, -6430), (1510, 240, -6340), (1585, 240, -6250),
            (1510, 240, -6160), (1585, 240, -6070),
            (1510, 420, -5620), (1585, 420, -5540), (1510, 420, -5460), (1585, 420, -5380), (1415, 420, -5510), (1415, 420, -5400)]
BEAT_CLEAR = 1000.0                     # no man of a squad that comes later than the round's start nearer than this to a
                                        # station of the round that lies BEFORE the squad's trigger (check()). GUESS
SQUAD_ACTIVE = A.SQUAD_ACTIVE           # ZSquadScript field 3, 'in the world from the load': 1 on the dock patrol only; 0 is
                                        # written, so that it waits for the start timer like the rest (kl_fa_author.ROOM_WAITS:
                                        # SEEN LIVE on Retomoto, run GW2)
# THE SOLDIER ROWS. As converted the 53 are eGuard / eArmy with a skill NAME (eN00b 1, eAmateur 24, eRegular 16,
# eVeteran 12: the name overwrites accuracy with 20 / 35 / 50 / 60, re/map_ai.md 1) and health 50 (13 of them 120) -
# against stock Fragile Alliance police at 100 / 175. Retomoto's cure is kl_arms' stock rows by the class of the
# weapon handed out (the owner, after it: 'guards good'); that pass is tied to kl_arms.SKILL_LEVELS and skips a man
# whose first three floats are not 50 / 50 / 50 - ten of the bank's police have 2 / 50 / 50. So the same rows
# (kl_arms.ROWS by kl_arms.SKILL: pistol 'cop' 50 / 100, SMG and shotgun 'swat' 50 / 175, rifle 'sharp' 75 / 175)
# are written here, in wire(), for every man of a kept squad. False: Dead Men's rows stay
STOCK_ROWS = True
# THE BANKING HALL. The campaign's eight hall guards have no rout ('GuardSquadForCutSeq'); the hall is held by
# three of stock F07's own police squads, re-placed (eight men: 3 + 3 + 2, each 'eArmy eCustom'). A squad is a
# ZGROUP + ZSquadScript with identity rotation whose children's places are offsets (kl_fa_street's docstring);
# it moves by moving the group and re-laying the children. squad -> (anchor, actors' places, the points of
# '10_RunToCover', the point of '10_Defend'); the point of '40_RunToEscape' (which nothing names here) goes to
# the anchor. Stock starts each from a box by naming '10_RunToCover'; here the beat's timer does (the alarm):
# they are in the hall when the crew comes up from the vault. GUESS: every point - MEASURED only that each is on
# the START's mesh part and on free floor (check()). The hall's floor is y 800; its middle (x 100..500,
# z -8200..-7000) and five rows of furniture (z -8800, -8200, -7600, -7000, -6400) are no mesh.
HALL_Y = 801.0
G30 = 'Gameplay!030_AfterLoot!'
HALL = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-300, HALL_Y, -8600), [(-500, -9000), (-300, -9000), (-100, -9000)],       # the west side
                                           [(-500, -8400), (-300, -7800), (-500, -7200)], (-100, -8000))),
    (G30 + '030_FinancialAlleyExit_Right', ((900, HALL_Y, -8600), [(700, -9000), (900, -9000), (1100, -9000)],         # the east side
                                            [(1100, -8400), (900, -7800), (1100, -7200)], (700, -8000))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((300, HALL_Y, -8900), [(100, -9000), (500, -9000)],                   # before the entrance
                                                 [(100, -8600), (500, -8600)], (300, -8600)))])
HALL_START = '10_RunToCover'

# ------------------------------------------------------------------ the beat
# the six locking rods of the vault door, in the campaign's order (its 'MatPosAnimProxy_Rod#01..#06' play frames
# 1..60 on each; the proxies sit inside the vault breaker's ZMercSquad, which cannot stay). Each rod has a
# MatPosAnim of its own with the in-message 'Activate' and stores -1 / -1 = its whole clip, one way
# (re/campaign_fa.md G1.8): a host AIDWrapper sends it. THE RODS ARE SHOW: the gate is the beat's timer
VE = VA + 'M03_A_VaultEntrance_01a\\'
RODS = [VE + 'Rod_%s01' % c for c in 'ABCDEF']
ROD_FIRST, ROD_STEP = 2.0, 8.0          # s from the ante-room box to the first rod, and between rods. GUESS (the study: 8 s)
# the campaign's single nodes that stay (campaign_names), by the job they have in wire(). Each keeps the list the
# campaign gave it unless wire() says otherwise
AUDIO = 'Special!Audio!'
CAMP = collections.OrderedDict(
    [('rod sound %d' % (i + 1), AUDIO + n) for i, n in enumerate(['GeomActivator_PlaysoundVaultRod0%d' % j for j in range(1, 6)] + ['GeomActivator_PlaysoundFinalRod'])] + [
     ('door sound', AUDIO + 'GeomActivator_PlaysoundVaultOpen'),                # ActivateGeom -> Audio!3D!Doors!Vault_Door_Open
     ('alarm sound', AUDIO + 'GeomActivator_PlaysoundAlarm'),                   # ActivateGeom -> Audio!3D!Alarm_01 / _02
     ('alarm lamps', G3 + 'Activator_AlarmRedLights'),                          # AIDWrapper 'Activate' -> the 11 lamps
     ('lights off', G3 + 'GeomDeactivator_Lights'),                             # DeactivateGeom -> the vault lobby's white light
     ('boom 1', G4 + 'BoomBox_BlowVault#01'), ('boom 2', G4 + 'BoomBox_BlowVault#02'), ('boom 3', G4 + 'BoomBox_BlowVault#03'),
     ('blast sound', G4 + 'Activator_SetOffAlarm'),                             # AIDWrapper 'Activate', empty in the campaign
     ('music', AUDIO + 'PlayMusic_Outside'),                                    # 4 layers 'BO_Sus_LOOP' + 41 layer fades
     ('music out', AUDIO + 'PlayMusic_Inside_Part2')])                          # 'M03A_Bustout_A_I' + 3 layer fades
# THE ALARM LAMPS: eleven 'Pc0100_M03_LampAlarm_Wall_*' in the vault lobby, both stair rooms and the ante-room. Each
# is a group with a RelayMessageList 'Activate' -> its glow (VertAnim) and its two lights, an omni and a spinning
# spot, which hold a LightToggle (state OFF, on at 'Activate'). LightToggle is registered in kl2.exe and used by NO
# stock Dog Days level: 'kl_maps.py preflight' calls the 22 a RISK (re/campaign_fa_bank.md 3.4). So, the lead's rule:
#   False (default)        the 22 LightToggle are TAKEN OFF before the join and the 22 lights - and the 8 slave spots
#                          the spinning ones have in the rooms next door - hidden (ZGEOM[3] = 1 and
#                          the .gms flag, the form the level's own fire lights have): the first live load runs no
#                          LightToggle code. The lamps still get 'Activate' at the alarm - their glow plays, no light.
#                          ASSUMPTION that a hidden light does not shine; if it does, eleven red lamps are lit all round
#   True ('--alarm-lights') the controllers stay; at the alarm the lamps light and the vault lobby's white halogen
#                          rows go off, as the campaign has it (its 'Timer_Alarm' names the same three objects)
ALARM_LIGHTS = False
LAMP = 'Pc0100_M03_LampAlarm_Wall_'
SLAVES = 'ZGateLightSpot[3]'            # a gate light's list of slave spots (8 of the 11 spinning spots reach into the room next door)
# THE VAULT'S OWN BLAST. The campaign blows the deposit boxes 15 s after the charges are set: three 'BoomBox'
# (Explode + its own AIDWrapper, #01 also a ShakeCamera), the explosion sound, the intact vault 'Vault_PRE' off and
# the blown one 'Vault_POST' on (26 objects each way: walls, overlays, burnt ceiling, the ante-room's carpet), the
# fire and smoke groups on. Here it goes off DOOR_GONE seconds after the door's 'Activate' - at the moment the
# door's body is switched off, so a door that did not swing is 'blown away'. The lists are the campaign's own, read
# from the stock level (blast_lists) less what is not in the build.
#   'show' (default, the lead's)  harmless: the Explode's two radii are set to 1 (kl_fa_author.BLAST_HARMLESS; GUESS
#                                 that fields 0 / 1 are its reach - a rocket 500 / 150, a gas tank 600 / 400)
#   'real' ('--blast-real')       the campaign's values: 1300 / 1000 and 800 / 800, field 4 = 30 (a stock grenade has
#                                 350 there, a gas tank 1000: GUESS that it is the damage, so even 'real' is a light hit)
#   None ('--no-blast')           the vault stays intact; nothing of the blast is named
# The fire is a picture in both: the campaign's two 'FireDamageBox' (EffectDmgBox, a kind no stock Dog Days level
# runs) are not kept.
VAULT_BLAST = 'show'
EXPLODE_REACH = (0, 1)                  # Dog Days Explode fields (18 in all), as kl_fa_author's wire() writes them
BLAST_FROM = 'GamePlay!4_Vault_Part!MercSqd_Valutbreaker_BlowingBoxes\\50_BlowingVault_RigC_DONOTDELETE\\'
BLAST_LISTS = {'post on': ('GeomActivator_POST_Vault', 'GeomActivator_Efx_Geoms'), 'pre off': ('GeomDeactivator_PRE_Vault',)}
BLAST_SOUND = 'Locations/M03_A/M03A_Audio.zip!Audio!3D!Sound_VaultExplosion'
VAULT_PRE, VAULT_POST = VA + 'M03_A_Vault_01a\\Vault_PRE', VA + 'M03_A_Vault_01a\\Vault_POST'
# THE MUSIC, wired through the campaign's own PlayMusic objects (they are silent until the stream file holds the
# clips: MUSIC_CLIPS, for the owner's go-ahead - kl_str.py builds no file here). The break-in set from the start;
# at the ante-room box the campaign's 'guards under fire' fades; when the beat ends its four 'vault explosion' fades
# (every layer to silence in 1 s) and the way-out set, which the campaign starts at the same place
# THE FOURTH LAYER. The break-in set has four layers and nine of its fades work on 'eLayer4' ('basic', the one that
# sounds from the start: -14 dB, the others silent). Dog Days' enum has the value, but no stock level fades a fourth
# layer: 'kl_maps.py preflight' calls the nine a RISK ('value'). The lead's rule for the alarm lamps, here too:
#   False (default)         the nine lose their PlayMusicLayerFade before the join and nothing names them. With the
#                           clips in the stream file the 'basic' layer then plays on under the way-out set
#                           (ASSUMPTION: a second PlayMusic does not stop the first - the campaign fades all four out
#                           before it starts the next): the stage that brings the music sets the flag
#   True ('--music-layer4') they stay and '03_Basic' / '23_Basic' are named with the rest
MUSIC_LAYER4 = False
LAYER4 = 'eLayer4'
MUSIC_AT = 1.0                          # s from the round-start event. GUESS
MUSIC_RISE = ('03_Ambient', '03_Basic', '03_Intense')
MUSIC_FADE = ('23_Ambient', '23_Basic', '23_Bass', '23_Intense')
MUSIC_CLIPS = ('Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer2_Bass_LOOP.wav',
               'Music/InHouse/M03A/BO_Sus_Layer3_Intense_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer4_Basic_LOOP.wav',
               'Music/InHouse/M03A/M03_Bustout_ActionV34.wav', 'Music/InHouse/M03A/M03_Bustout_IntenseClimax_Loop.wav')
_plan = {}


def rod_times():
    """Seconds from the ante-room box to each rod: ROD_STEP apart, nearer when BEAT is short ('--beat'): the last rod
    goes at least 4 s before the door."""
    step = min(ROD_STEP, max(0.5, (BEAT - ROD_FIRST - 4.0) / (len(RODS) - 1)))
    return [ROD_FIRST + i * step for i in range(len(RODS))]


def squad_plan():
    """kl_fa_author.squad_plan(M03_A) -> ({squad: (path of its start rout, actors, stripped kinds)}, {left: why}).
    That function reads its name roots from its own table SQUADS, which has Retomoto's two levels: the bank's
    entry is lent to it for the length of the call (no file of that module is edited)."""
    if NO_AI:
        return {}, {'*': 'a build without enemies (NO_AI)'}
    if 'plan' not in _plan:
        had = A.SQUADS.get(LEVEL)
        A.SQUADS[LEVEL] = SQUAD_ROOTS
        try:
            keep, left = A.squad_plan(LEVEL)
        finally:
            if had is None:
                del A.SQUADS[LEVEL]
            else:
                A.SQUADS[LEVEL] = had
        if set(keep) != set(STAGE):
            raise ValueError('kl_fa_bank: the squads that can stay are not the %d of STAGE: only in the plan %s, only in STAGE %s' % (
                len(STAGE), sorted(set(keep) - set(STAGE)), sorted(set(STAGE) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


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
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT F07 + M03_A folder WITHOUT
    the layer (a bare 'kl_maps.py one <out> F07 M03_A --campaign --keep': on a build that has the van, the planner
    takes the van's own camera for a designer's and lists it to be left out). A fault of the plan is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_bank: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
    """A plan from a file: the JSON 'kl_map_escape.py van-plan ... --json' prints, or the van.json test() writes
    beside a build (the plan is its 'plan')."""
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


def place_hall(S, log=print):
    """F07's three police squads of HALL into the banking hall: the group to its anchor, every child that has a
    place of its own (a non-zero local translation under parents that have none: actor groups, the points of the
    routs) to its place of the table, as an offset from the anchor. -> [(squad, actors)]"""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    for name, (anchor, actors, cover, defend) in HALL.items():
        top = A.node_of(sc, name)
        turned = max(abs(a - b) for a, b in zip(struct.unpack('<9f', S.ents[top - 1].rot[:36]), A.rot9(BOX)))
        if not kl_fa.has(sc, top, 'ZSquadScript') or turned > 1e-3 or not sc.resolve(R + name + '\\' + HALL_START):
            raise ValueError('%s: not a squad group without a turn that has a %s' % (name, HALL_START))
        own = []
        def go(k):
            for c in range(k + 1, sc.end[k]):
                if sc.parent[c] == k:
                    own.append(c) if any(abs(v) > 0.5 for v in tr(c)) else go(c)
        go(top)
        by = collections.defaultdict(list)
        for k in own:
            by['actors' if any(sc.cls(c) == 'ZFFActor' for c in range(k, sc.end[k])) else sc.names[sc.parent[k]]].append(k)
        want = {'actors': [(x, HALL_Y, z) for x, z in actors], '10_RunToCover': [(x, HALL_Y, z) for x, z in cover],
                '10_Defend': [(defend[0], HALL_Y, defend[1])], '40_RunToEscape': [anchor]}
        if {k: len(v) for k, v in by.items()} != {k: len(v) for k, v in want.items()}:
            raise ValueError('%s: placed children %s, the table has %s' % (name, {k: len(v) for k, v in by.items()}, {k: len(v) for k, v in want.items()}))
        A.place(S, top, anchor)
        for kind, ks in by.items():
            for k, p in zip(ks, want[kind]):
                A.place(S, k, tuple(p[a] - anchor[a] for a in range(3)))
        out.append((name, len(by['actors'])))
    log('  kl_fa_bank: the banking hall: %d of F07\'s police squads re-placed (%d men); the beat\'s timer names their %s' % (
        len(out), sum(n for _s, n in out), HALL_START))
    return out


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the bank. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    if PLAN is None:                                    # before anything is armed: a caller that goes on in this process must
        raise ValueError(NO_PLAN)                       # not find kl_escape wrapped (review round 1)
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
    # escape: the one van laid on the plan of ROAD - F07's own keys re-written in place, the boxes beside its drive
    # and its camera moved with it (kl_map_escape.van_prepare; the van's nodes must still stand where F07 has them);
    # the exit trigger names it alone (kl2 0x6c3f90 loops until one field is set). The escape marker stays where
    # PLACE has it, beside the lane: held against this plan's drive here (check() does it again on the written level)
    S.van = ESC.van_prepare(S, PLAN, log)
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(ESC_AT)[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_fa_bank: the escape marker\'s place %s is %d from the van\'s drive (%d wanted)' % (ESC_AT, off, LANE_CLEAR))
    log('  kl_fa_bank: the escape marker stands %d from the van\'s drive, %d from the boarding place at the stop' % (off, math.dist(ESC_AT, PLAN['board'])))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van, 'hall': [] if NO_AI else place_hall(S, log)}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M03_A the campaign pre-pass must leave in: the squads that stay and the campaign's
    single nodes of the beat. No door proxy is among them - every door takes 'Activate' itself
    (re/campaign_fa_bank.md 5, the second agent's note)."""
    if level != LEVEL:
        return ()
    return tuple(squad_plan()[0]) + tuple(CAMP.values())


_dm = {}

def blast_lists():
    """{'post on': [...], 'pre off': [...]}: what the campaign's own blast shows and takes away, read from the stock
    Dead Men level (its three objects sit in the vault breaker's subtree, which is dropped: BLAST_LISTS)."""
    if 'blast' not in _dm:
        sc = J.Scene.load(LEVEL, 'dm')
        out = {}
        for role, names in BLAST_LISTS.items():
            out[role] = []
            for n in names:
                k = A.node_of(sc, BLAST_FROM + n)
                lists = [s for s in A.named(sc, k)]
                if not lists:
                    raise ValueError('%s names nothing in stock %s' % (n, LEVEL))
                out[role] += [s for s in lists if s not in out[role]]
        _dm['blast'] = out
    return _dm['blast']


def snap_men(M, keep, log=print):
    """Every man of a kept squad ON the navigation mesh: the campaign has three standing 10 - 32 beside it (at a
    wall's foot; Dead Men's own places). The man's group goes to the first point of the mesh on the way to the
    middle of the nearest polygon, at the mesh's height. More than MAN_OFF off the mesh is no such case: an error."""
    import kl_route
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
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
                raise ValueError('%s stands %s off the navigation mesh at (%d, %d, %d)' % (sc.path[k], d, *w))
            mid = mesh.mid[i]
            for step in range(1, 201):
                x, z = w[0] + (mid[0] - w[0]) * step / 200.0, w[2] + (mid[2] - w[2]) * step / 200.0
                if mesh.inside(i, x, z) and math.hypot(x - w[0], z - w[2]) >= d + MAN_IN:
                    break
            new = (x, mesh.height(i, x, z), z)
            man_to(M, g, new, mesh)
            moved.append((sc.path[g][5:], round(d), math.dist(w, new)))
    log('  kl_fa_bank: %d men of the kept squads stood beside the navigation mesh and were put on it: %s' % (
        len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    return moved


def man_to(M, g, new, mesh):
    """A man's group g of the converted level M to the world place `new` (his turn stays): the place in his parent's
    frame, read back; the place must be on the navigation mesh."""
    par = M.ents[g - 1].parent
    T, Rm = world_of(par) if par is not None else ((0.0, 0.0, 0.0), [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]])
    dv = [new[a] - T[a] for a in range(3)]
    A.place(M, g, tuple(sum(Rm[b][a] * dv[b] for b in range(3)) for a in range(3)))   # the parent's turn undone (transpose)
    got = world_of(M.ents[g - 1])[0]
    if math.dist(got, new) > 1.0 or mesh.on(*got) is None:
        raise ValueError('%s: placed at %s, stands at %s%s' % (M.prp.path[g], new, got, '' if mesh.on(*got) else ', which is not on the mesh'))


def beat_men(M, keep, log=print):
    """The men of the squads the ante-room box starts (STAGE 'beat') to the places of BEAT_MEN, behind the airlock:
    in STAGE's order, a squad's men side by side. -> [(squad, man's group, from, to)]"""
    import kl_route
    if not BEAT_MEN or not keep:
        return []
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    men = [(n, sc.parent[k]) for n, s in STAGE.items() if s == 'beat' for t in sc.tops() if sc.names[t] == n
           for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
    if len(men) != len(BEAT_MEN):
        raise ValueError('kl_fa_bank: %d men in the squads of the beat, BEAT_MEN has %d places' % (len(men), len(BEAT_MEN)))
    moved = []
    for (n, g), new in zip(men, BEAT_MEN):
        was = world_of(M.ents[g - 1])[0]
        man_to(M, g, tuple(float(v) for v in new), mesh)
        moved.append((n, sc.path[g][5:], was, new))
    log('  kl_fa_bank: the %d police of the beat (%d squads) re-placed behind the airlock, off the way in: from x %d..%d, z %d..%d to x %d..%d, z %d..%d' % (
        len(moved), len({n for n, _g, _w, _t in moved}), min(w[0] for _n, _g, w, _t in moved), max(w[0] for _n, _g, w, _t in moved),
        min(w[2] for _n, _g, w, _t in moved), max(w[2] for _n, _g, w, _t in moved), min(t[0] for t in BEAT_MEN), max(t[0] for t in BEAT_MEN),
        min(t[2] for t in BEAT_MEN), max(t[2] for t in BEAT_MEN)))
    return moved


def strip(M, log=print):
    """On the converted Dead Men level, before the join (nothing goes by controller index yet): the campaign's
    mini-cutscene controllers come off the squads that stay (kl_fa_author.STRIP). The door leaves are map nodes
    that stay as they are (they are sunk on the JOINED scene: Doors)."""
    if M.name != LEVEL:
        return 0
    sc, n = M.prp, 0
    keep = squad_plan()[0]
    for t in sc.tops():
        if sc.names[t] in keep:
            for k in range(t, sc.end[t]):
                nd = sc.nodes[k]
                left = [c for c in nd['ctrls'] if sc.p.key(c[0]) not in A.STRIP]
                n += len(nd['ctrls']) - len(left)
                nd['ctrls'] = left
    have = sum(1 for p, _at, _set in LEAVES if sc.resolve(R + p)) + bool(sc.resolve(R + VAULT_DOOR))
    log('  kl_fa_bank: %s: %d of %d door nodes of the route found; %d squads stay, %d mini-cutscene controllers taken off them' % (
        M.name, have, len(LEAVES) + 1, len(keep), n))
    snap_men(M, keep, log)
    beat_men(M, keep, log)
    # the music's fourth layer (MUSIC_LAYER4): without the flag its nine fades lose their controller
    four = [(k, i) for k, i, v in kl_fa.controllers(sc, 'PlayMusicLayerFade') if v[0] == LAYER4 and sc.names[sc.top[k]] in (CAMP['music'], CAMP['music out'])]
    if len(four) != 9:
        raise ValueError('kl_fa_bank: %d fades of %s under the two music objects, 9 expected' % (len(four), LAYER4))
    if not MUSIC_LAYER4:
        for k in {k for k, _i in four}:
            sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'PlayMusicLayerFade']
    log('  kl_fa_bank: the music: %d fades of the fourth layer %s' % (len(four), 'stay (MUSIC_LAYER4)' if MUSIC_LAYER4 else
                                                                  'lose their controller (a value no stock Dog Days level has)'))
    # the alarm lamps' lights (ALARM_LIGHTS): without the flag the LightToggle comes off and the light is hidden
    lights = [k for k in range(1, len(sc.nodes)) if ('\\' + LAMP) in sc.path[k] and any(sc.p.key(c[0]) == 'LightToggle' for c in sc.nodes[k]['ctrls'])]
    if len(lights) != 22:
        raise ValueError('kl_fa_bank: %d lights with a LightToggle under the alarm lamps, 22 expected' % len(lights))
    # ... and with it every SLAVE of a spinning spot (ZGateLightSpot's last field: a ZSPOTLIGHT '<room>@<lamp>@Alarm_Spot
    # __slave' in the room next door, 8 in all). The engine carries a gate light's state to its slaves only at RUN time
    # (show / hide 0x8e4600 and light off 0x743240 walk the slave list; the LightToggle's init switches the master off
    # so): with the controller gone and the master hidden in the file neither call ever runs, and a slave left shown
    # could shine from the load with nothing to turn it off (review round 1; whether it would was not seen)
    slaves = sorted({j for k in lights if sc.cls(k) == 'ZGateLightSpot'
                     for s in kl_fa.node_values(sc, k)[J.labels('dd', 'ZGateLightSpot').index(SLAVES)] for j in sc.resolve(s)})
    if len(slaves) != 8 or any(not sc.names[j].endswith('__slave') for j in slaves):
        raise ValueError('kl_fa_bank: %d slave spots under the alarm lamps\' gate lights, 8 expected' % len(slaves))
    if not ALARM_LIGHTS:
        for k in lights + slaves:
            sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'LightToggle']
            A.place(M, k, hidden=True)
    log('  kl_fa_bank: the alarm lamps: %d lights and %d slave spots of theirs in the rooms next door; %s' % (
        len(lights), len(slaves), 'their LightToggle stays (ALARM_LIGHTS)' if ALARM_LIGHTS else
        'the LightToggle taken off and all of them hidden (a kind no stock Dog Days level runs)'))
    return n


# ------------------------------------------------------------------ 3. the joined scene
def soldier_rows(sc, plan, log=print):
    """A stock Fragile Alliance soldier row (kl_arms.ROWS: skill eCustom and ZSoldier fields 4..17) for every man of
    the kept squads, by the class of the weapon kl_arms handed him (STOCK_ROWS). After kl_arms.arm, which runs
    before wire(). -> Counter of rows written."""
    import kl_arms
    cls_of = {t.lower(): c for c, pool in kl_arms.POOLS.items() for t, _w in pool}
    n = collections.Counter()
    for k, squad, w, _w2, _g1, _g2, _set in kl_arms.carriers(sc):
        if squad not in plan:
            continue
        kind = kl_arms.SKILL.get(cls_of.get(w.lower()))
        if kind is None:                                # unarmed, or a weapon of no pool: Dead Men's row stays
            n['none (%s)' % (w or 'unarmed')] += 1
            continue
        name, row = kl_arms.ROWS[kind]
        def fn(us, k=k, name=name, row=row):
            if len(us) != 23 or us[kl_arms.SKILL_FIELD][0][0] not in (0x0c, 0x0e) or any(us[j][0][0] != 0x0a for j in range(4, 18)):
                raise ValueError('%s: ZSoldier is not in the Dog Days layout' % sc.path[k])
            A.setv(sc, us, kl_arms.SKILL_FIELD, name)
            for j, x in enumerate(row):
                A.setv(sc, us, 4 + j, x)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'ZSoldier'), fn)
        n[kind] += 1
    return n


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

    # ---- the enemies: who is named by which stage, the rows, the hunt
    plan = squad_plan()[0]
    stage = collections.defaultdict(list)
    for n, (first, _actors, _strip) in plan.items():
        if n in START_ROUT:
            first = R + n + '\\' + START_ROUT[n]
        stage[STAGE[n]] += must([first])
        k = node(n)
        if values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] not in (0, 1):
            raise ValueError('%s: ZSquadScript field %d is %r' % (n, SQUAD_ACTIVE, values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE]))
        put_(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 0})
    hunt = [R + n + '\\' + HUNT for n in plan if sc.resolve(R + n + '\\' + HUNT)]
    hall = [] if NO_AI else must([R + n + '\\' + HALL_START for n in HALL])
    armed = soldier_rows(sc, plan, log) if STOCK_ROWS else {}

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it. Two timers of
    # this layer are: the squads' (SQUADS_AT) and the music's
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['start timer'], R + ROLE['music timer']] + ([R + ROLE['doors']] if DOORS_ANIMATE else [])
    lists('monitor', 'AIMonitor', f2=have + start)
    lists('start timer', 'TriggerDelay2', f0=SQUADS_AT, f4=stage['start'] + stage['down'])
    music, out = must([R + CAMP['music'], R + CAMP['music out']])
    lists('music timer', 'TriggerDelay2', f0=MUSIC_AT, f4=[music])
    lists('doors', 'AIDWrapper', f0=leaves if DOORS_ANIMATE else [], f1='Activate')
    if DOORS_ANIMATE:
        glass = [p for p in leaves if '\\GlassDoor_' in p]
        for p in glass:                                 # the clip goes there AND back: stop it at its open frame
            j = sc.resolve(p)[0]
            put_(j, 'MatPosAnim', **{'f%d' % MPA_LAST: GLASS_LAST})
        log('  kl_fa_bank: DOORS ANIMATE: %d leaves get \'Activate\' at the round start; %d glass leaves store LAST %d' % (len(leaves), len(glass), GLASS_LAST))

    # ---- the beat. The ante-room box starts, all at once: the six rod timers, the beat's timer, the 14 police of
    # stage 'beat', the music's rise. TriggerBox FIELD 15 = 0 (BOX_PER_MAN): by the stock data 0 is 'fires once', 1 'fires
    # for every criminal that enters' - of the 226 TriggerBox of F01..F09 the 125 with 0 start the squad routs and
    # the one-shot timers (this very object in F07 has 0), and not one of the 101 with 1 names a squad rout; F07's
    # 'tbRunToEscape' (1) feeds a TriggerCounter of three, its twin 'tbRunToEscape1Player' (0) a timer
    # (C:/kl_scratch/bank/review_round_1/tb.py). The first three stages wrote 1 on the opposite ASSUMPTION: the beat
    # would have begun again for each further criminal - seven AI heisters among them (review round 1).
    # ASSUMPTION still: the field's meaning is read off the census, not in kl2.exe
    rods = must([R + p for p in RODS])
    for p in rods:
        msg = [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == sc.resolve(p)[0]]
        if msg != ['Activate']:
            raise ValueError('%s: MatPosAnim in-message %s, not one \'Activate\'' % (p, msg))
    camp = {r: must([R + n])[0] for r, n in CAMP.items()}
    for i, p in enumerate(rods):
        lists('rod timer %d' % (i + 1), 'TriggerDelay2', f0=rod_times()[i], f4=[R + ROLE['rod %d' % (i + 1)], camp['rod sound %d' % (i + 1)]])
        lists('rod %d' % (i + 1), 'AIDWrapper', f0=[p], f1='Activate')
    fades = lambda names: [p for p in must([music + '\\' + n for n in names]) if kl_fa.has(sc, sc.resolve(p)[0], 'PlayMusicLayerFade')]
    rise = fades(MUSIC_RISE)                            # without MUSIC_LAYER4 the fourth layer's fades hold no controller: not named
    gone = VAULT_DOOR_GOES and not VAULT_OPEN
    late = gone or bool(VAULT_BLAST)                    # the door timer has something to do
    lists('beat box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BOX_PER_MAN: 0},
          f17=[R + ROLE['beat timer']] + [R + ROLE['rod timer %d' % (i + 1)] for i in range(len(rods))] + stage['beat'] + rise)
    # ... when it ends: the door's swing and its sound, the loot, the alarm (sound, lamps), the music's change, the
    # hall's police, the hunt; DOOR_GONE later the door's body goes and the vault blows
    alarm = [camp['alarm sound'], camp['alarm lamps']] + ([camp['lights off']] if ALARM_LIGHTS else [])
    fade = fades(MUSIC_FADE)
    lists('beat timer', 'TriggerDelay2', f0=BEAT, f4=[R + ROLE['door'], camp['door sound'], R + ROLE['loot on']] + alarm + fade + [out] + hall + hunt
          + ([R + ROLE['door timer']] if late else []))
    lists('door', 'AIDWrapper', f0=[] if VAULT_OPEN else [door], f1='Activate')
    lamps = values(sc, sc.resolve(camp['alarm lamps'])[0], 'AIDWrapper')
    if lamps[1] != 'Activate' or len(lamps[0]) != 11 or any(LAMP not in s or not sc.resolve(s) for s in lamps[0]):
        raise ValueError('%s does not send \'Activate\' to the eleven alarm lamps: %s' % (CAMP['alarm lamps'], lamps))
    hidden = [R + sc.names[t] for t in sc.tops() if sc.names[t].startswith('FASpecials!DropMoney!') and kl_fa.node_values(sc, t)[3]
              and any(v[2] == 'ZMONEYCTRL_TYPE_NORMAL' for kk, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if kk == t)]
    if GATE_VAULT and len(hidden) != len(VAULT_LOOT):
        raise ValueError('%d hidden loot objects, the vault has %d' % (len(hidden), len(VAULT_LOOT)))
    lists('loot on', 'ActivateGeom', f0='AITrigger', f1=hidden)

    # ---- the blast (VAULT_BLAST), on the door's timer with the door's body
    boom = [camp['boom %d' % i] for i in (1, 2, 3)]
    on, off = [], []
    if VAULT_BLAST:
        got = blast_lists()
        on, off = [s for s in got['post on'] if sc.resolve(s)], [s for s in got['pre off'] if sc.resolve(s)]
        if R + VAULT_POST not in on or R + VAULT_PRE not in off:
            raise ValueError('the campaign\'s blast lists do not name the vault\'s two states: %d on, %d off' % (len(on), len(off)))
        for p in boom:
            k = sc.resolve(p)[0]
            v = values(sc, k, 'Explode')
            if len(v) != 18 or not all(isinstance(v[j], float) for j in EXPLODE_REACH) or values(sc, k, 'AIDWrapper')[:2] != [[p], 'Activate']:
                raise ValueError('%s: not an Explode in the Dog Days layout with a wrapper of its own: %s' % (p, v))
            if VAULT_BLAST == 'show':
                put_(k, 'Explode', **{'f%d' % j: 1.0 for j in EXPLODE_REACH})
        log('  kl_fa_bank: the vault\'s blast (%s): %d Explode%s, %d objects on (the blown vault, fire, smoke), %d off; of the campaign\'s lists %d / %d '
            'entries are not in the build' % (VAULT_BLAST, len(boom), ' with reach 1' if VAULT_BLAST == 'show' else ' as the campaign has them', len(on), len(off),
                                              len(got['post on']) - len(on), len(got['pre off']) - len(off)))
    lists('door timer', 'TriggerDelay2', f0=DOOR_GONE, f4=([R + ROLE['door off']] if gone else []) + (
        boom + [camp['blast sound'], R + ROLE['post on'], R + ROLE['pre off']] if VAULT_BLAST else []))
    lists('door off', 'DeactivateGeom', f0='AITrigger', f1=[body] if gone else [])
    put_(sc.resolve(camp['blast sound'])[0], 'AIDWrapper', f0=must([R + BLAST_SOUND]) if VAULT_BLAST else [], f1='Activate')
    lists('post on', 'ActivateGeom', f0='AITrigger', f1=on)
    lists('pre off', 'DeactivateGeom', f0='AITrigger', f1=off)

    # ---- the way out: F07's 'exit heist' box in the foyer, with a line that fits a front door - and the plaza's
    # seven squads: the police are outside when a criminal comes up into the hall
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']] + stage['plaza'])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    # ---- the escape: every exit trigger of the level (there is F07's one) calls the van - field 0 false, field 2
    # the van's group, 1 and 3..5 empty, the form the three car maps on the tab have (kl_map_escape.van_wire). The
    # rest of the round's last stage is F07's own and stays as the graft left it: the vehicle monitor's lists
    # (2 the escape sounds, 3 the relay of this van, 8 the 'last van' message and its timer)
    if PLAN is None:
        raise ValueError('kl_fa_bank: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_fa_bank: enemies: %d campaign squads (%d men): round start + %.0f s -> %d routs (dock, vault lobby, the way down); ante-room box -> %d; '
        'the beat\'s end -> %d hunts + %d of F07\'s squads in the hall; foyer box -> %d; stock soldier rows: %s' % (
            len(plan), sum(a for _f, a, _s in plan.values()), SQUADS_AT, len(stage['start'] + stage['down']), len(stage['beat']), len(hunt), len(hall),
            len(stage['plaza']), dict(armed) or ('none (NO_AI)' if NO_AI else 'Dead Men\'s rows stay')))
    log('  kl_fa_bank: sequence: ante-room box -> rods at %s s -> %.0f s -> the vault door %s, %d hidden loot objects on, alarm (%s), music -> way-out set%s' % (
        ', '.join('%.0f' % t for t in rod_times()), BEAT, 'is sunk already (VAULT_OPEN)' if VAULT_OPEN else 'gets \'Activate\'',
        len(hidden), 'sound, lamps, white light off' if ALARM_LIGHTS else 'sound, the lamps\' glow', '; -> %.0f s -> %s' % (
            DOOR_GONE, ' and '.join(x for x in ('the door\'s body off' if gone else '', 'the vault\'s blast (%s)' % VAULT_BLAST if VAULT_BLAST else '') if x)) if late else ''))
    log('  kl_fa_bank: wired: round start %s; music at %.0f s; %d briefing / reminder lines; exit line %s' % (
        '-> %d door leaves' % len(leaves) if DOORS_ANIMATE else 'starts no door (the leaves are open at build time)', MUSIC_AT, len(LINES), EXIT_LINE))
    return {'hidden': hidden, 'leaves': leaves, 'monitor': have + start, 'stage': dict(stage), 'hunt': hunt, 'hall': hall, 'on': on, 'off': off}


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
        cls.state = {'sink': {}, 'old': {}, 'prp_w': {}}

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
    1. The vault's loot shows a briefcase and stands on the floor turned as VAULT_LOOT
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
             ('street', ESC_AT)]                        # beside the van's lane, under the escape marker - not ON the van's stop
# the five large blocks a level load asks of the 2 GB process (CLAUDE.md, 2026-10-10 01:35): 32.0 MB scratch, .fxc, .prm and
# .ANM + 0x60000 each, the whole .WAV beside the archive. No limit is known; the yardstick is what has loaded live many
# times in one process: the Retomoto build of 2026-10-10 (the owner's session of seven level loads in one process),
# 16.9 + 74.2 + 20.6 + 25.9 MB = 171 MB with the scratch block. (The tab's Retomoto of today is heavier - 180.3 MB by
# <work>/build/c_bank/blocks.txt - and plays; 171 is the figure a counted run stands behind, the safe side)
BLOCKS_LIVE = 171.0
# the chunk table: 69,632 entries is the tools' line (kl_impact.CHUNK_SAFE). The wardrobe and the gun looks come into
# DEAD indices. MEASURED on this level by the finishing chain: 'kl_chars.py wardrobe --plates=wolf,dallas,chains,hoxton'
# took 20,989 of the bare map's 23,690 (re/bank_campaign.md F.4; the study's 15,509 was a wardrobe without the four plates)
WARDROBE_CHUNKS = 20989
ACTORS_LIVE = (99, 55)                  # ZFFActor and squads of the largest build that runs live: Retomoto on the tab
                                        # (re/campaign_fa_tooling.md 5.4; stock Fragile Alliance: 35..57 and 20..36)
POLICE_CLEAR = 100.0                    # a returning policeman's point or body this far from a squad's man. GUESS
# the walk test of the loot's pick-up: (box x0, x1, z0, z1; a place the route test reaches) for the vault and the banking hall.
# GUESS: the two boxes (each room with a margin); the two places are stations of ROUTE_VAULT / ROUTE_OUT
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


def lost_clips(folder, res):
    """(the clip names result.json lists as missing from the stream file, those of them WITHOUT a record in the built
    .WHD beside the archive, every name that has a record - lower case). Only the second are silent: a name with a
    record streams from the installed file. Names with '/'; ([], [], set()) when the folder has no list or no .WHD."""
    import kl_whd, kl_snd
    whd = [f for f in os.listdir(folder) if f.lower().endswith('_main.whd')]
    listed = [n.replace('\\', '/') for n in res.get('stream_clips_missing') or ()]
    if not listed or not whd:
        return [], [], set()
    b = open(os.path.join(folder, whd[0]), 'rb').read()
    have = {kl_snd.cs(b, f['name']).decode('latin1').replace('\\', '/').lower() for f in kl_whd.records('dd', b).values()}
    return listed, [n for n in listed if n.lower() not in have], have


def inventory(folder, log=print):
    """What the layer consists of in a built level, with world places read back from it."""
    import kl_arms
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
    log('THE CAMPAIGN\'S KEPT OBJECTS (CAMP) and what each names')
    for role, name in CAMP.items():
        for k in sc.resolve(R + name):
            row(k, '= ' + role)
            targets(k)
    log('SQUADS (stage, men with weapon and soldier row: skill, accuracy, health)')
    arms = {k: w for k, _s, w, _w2, _g1, _g2, _set in kl_arms.carriers(sc)}
    for t in sc.tops():
        if not kl_fa.has(sc, t, 'ZSquadScript'):
            continue
        stage = STAGE.get(sc.names[t], 'hall' if sc.names[t] in HALL else '-')
        row(t, '= %s' % stage)
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor':
                v = values(sc, k, 'ZSoldier')
                log('        man %s %-24s %s %g / %g' % (at(k), arms.get(k) or 'unarmed', v[3], v[4], v[7]))
    log('ESCAPE (the van at its waiting place; its boarding box, kill box and target ride on it: check() says where it stops)')
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
    res = json.load(open(os.path.join(folder, 'result.json'))) if os.path.isfile(os.path.join(folder, 'result.json')) else {}
    if problems is None:
        problems = res.get('problems')
    if res.get('dangling'):                             # scene paths the build found naming nothing
        fail('the build left %d dangling scene paths: %s' % (len(res['dangling']), res['dangling'][:3]))
    every = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript')]
    squads = [k for k in every if not sc.path[k][len(R):].startswith(BOT_SQUAD)]      # the enemies': the finishing chain's seven AI heisters are squads too
    known = KNOWN + (() if squads else (KNOWN_NO_AI,))  # what the BUILD is is read off the level: no squad of enemies = a NO_AI build
    for p in problems or ():
        why = next((w for t, w in known if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    # ... and what of the sound is really lost: result.json's 'stream_clips_missing' is a list by NAME (kl_maps.one's
    # reconstruction: a name is listed when any record of that name is a language-file one), the built .WHD says more
    listed, lost, have = lost_clips(folder, res)
    if listed:
        log('  sound: of the %d clip names result.json lists, %d have a streamed record in the built .WHD (they play from the installed stream file); '
            '%d have NO record = what a larger PC_Def.str would bring:%s' % (len(listed), len(listed) - len(lost), len(lost), ''.join('\n          ' + n for n in lost)))
        if any(n.lower() in have for n in MUSIC_CLIPS):
            fail('sound: MUSIC_CLIPS names %d clips that have a record in the built .WHD: the list for the owner is not the level\'s' % sum(n.lower() in have for n in MUSIC_CLIPS))
    # ---- kl_fa.check on the written archive
    import kl_arms
    fa = kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch))
    for f in fa:
        why = next((w for t, w in known if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
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
    for ref, far in lv.moved():                         # the van's five key-framed bodies too: kl_map_escape.van_hvk puts them where it waits
        fail('REF %d (%s): its collision placement stands %d from its entity' % (ref, path_of.get(ref, '?')[-60:], far))
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
    def named(role):
        return A.named(sc, A.node_of(sc, ROLE[role]))
    # the vault has TWO states when the blast is wired: what its ActivateGeom / DeactivateGeom name comes and goes
    # (whole subtrees). The loot must be takable, and not lie under rubble, in both
    sub = lambda paths: {ents[j - 1].ref for s in paths for k in sc.resolve(s) for j in range(k, sc.end[k])}
    on, off = sub(named('post on')), sub(named('pre off'))
    blast = bool(on or off)
    states = [('the vault intact', built.soft() | built.hidden)] + ([('blown', built.soft() | (built.hidden - on) | off)] if blast else [])
    walks = {}
    for what, skip in states:
        walks[what] = []
        for box, start in LOOT_WALKS:
            f = L.Floors(hvk, box, skip=skip)
            walks[what].append((f, f.flood([start])[0]))
    taken = 0
    for k, v in loot:
        at, radius = pos[ents[k - 1]], values(sc, k, 'TriggerBox2')[2]
        told, good = [], True
        for what, _skip in states:
            best = None
            for f, seen in walks[what]:
                place, h, n = f.stand(seen, at, radius)
                if place is not None and (best is None or h < best[1]):
                    best = (place, h, n)
            spare = radius + L.REACH_PAD - best[1] if best else None
            # buried: collision of that state 8..120 over the place, in its cell (the case itself has no collision)
            over = [built.name.get(r, str(r)).split('\\')[-1] for y, _fl, r in walks[what][0][0].w.grid.get(walks[what][0][0].w.cell(at[0], at[2])) or ()
                    if at[1] + 8 < y < at[1] + 120] if in_vault(at) else []
            told.append('%s: %s%s' % (what, 'from (%d, %d, %d), %d away, %d to spare' % (*best[0], best[1], spare) if best else 'OUT OF REACH',
                                    ', UNDER %s' % sorted(set(over))[:2] if over else ''))
            if best is None or spare < L.MARGIN:
                good = False
                fail('loot %s at (%d, %d, %d) cannot be taken (%s)%s' % (sc.names[k], *at, what, ' with %d to spare (%d wanted)' % (spare, L.MARGIN) if best else ''))
            if over:
                good = False
                fail('loot %s at (%d, %d, %d) lies under %s (%s)' % (sc.names[k], *at, sorted(set(over))[:3], what))
        log('  loot %-40s %7d at (%5d %5d %6d) %s; %s' % (sc.names[k][-40:], v[1], *at, 'hidden' if kl_fa.node_values(sc, k)[3] else 'shown ', '; '.join(told)))
        taken += good
    log('  loot: %d objects, %d; %d can be taken%s' % (len(loot), sum(v[1] for _k, v in loot), taken, ' in the intact and in the blown vault' if blast else ''))
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
    if blast:                                           # kl_route counts hidden bodies: the runs above had BOTH vaults in the way
        after = kl_route.route(lv, way, opened=gates + sorted(off))
        log('  route after the blast (the standing door(s) and the %d bodies the blast takes away out, the blown vault in): %s' % (len(off), say(after)))
        if not after['free']:
            fail('the route is not free in the blown vault')
    # ---- the chain, read back
    camp = {r: (sc.resolve(R + n) or [None])[0] for r, n in CAMP.items()}
    for r, n in CAMP.items():
        if camp[r] is None:
            fail('the campaign\'s %s (%s) is not in the level' % (r, n))
    mine = [(ROLE[r], A.node_of(sc, ROLE[r])) for r in ROLE] + [(CAMP[r], k) for r, k in camp.items() if k is not None]
    for n, k in mine:
        for j in range(k, sc.end[k]):
            for s in A.named(sc, j):
                if not sc.resolve(s):
                    fail('%s names %s, which is no node' % (sc.path[j][5:], s))
    mon = named('monitor')
    starters = {R + ROLE['start timer'], R + ROLE['music timer']} | ({R + ROLE['doors']} if animate else set())
    if {s for s in mon if s[5:] in ROLE.values()} != starters:
        fail('the round start names %s of this layer\'s objects, wanted %s' % (sorted(s for s in mon if s[5:] in ROLE.values()), sorted(starters)))
    delay = lambda role: values(sc, A.node_of(sc, ROLE[role]), 'TriggerDelay2')[0]
    box, beat = named('beat box'), named('beat timer')
    if R + ROLE['beat timer'] not in box or R + ROLE['loot on'] not in beat:
        fail('the beat\'s chain is not box -> timer -> loot: %s / %s' % (box, beat))
    if values(sc, A.node_of(sc, ROLE['beat box']), 'TriggerBox')[BOX_PER_MAN]:      # 1 = again for every criminal that enters (wire())
        fail('the beat\'s box fires for every criminal that enters (TriggerBox field %d is not 0): the beat would begin again with each' % BOX_PER_MAN)
    rods = []
    for i in range(len(RODS)):
        t, w = 'rod timer %d' % (i + 1), 'rod %d' % (i + 1)
        got = [s for s in named(w)]
        ok = R + ROLE[t] in box and R + ROLE[w] in named(t) and got == [R + RODS[i]] and 0 < delay(t) < delay('beat timer') and (not rods or delay(t) > rods[-1])
        ok = ok and [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, RODS[i])] == [values(sc, A.node_of(sc, ROLE[w]), 'AIDWrapper')[1]]
        if not ok:
            fail('rod %d: the box names its timer %s, the timer (%.0f s) its wrapper %s, the wrapper %s' % (i + 1, R + ROLE[t] in box, delay(t), R + ROLE[w] in named(t), got))
        rods.append(delay(t))
    hid = [R + sc.names[k] for k, _v in loot if kl_fa.node_values(sc, k)[3]]
    if sorted(named('loot on')) != sorted(hid):
        fail('the loot\'s ActivateGeom names %d objects, %d are hidden' % (len(named('loot on')), len(hid)))
    last = {p: [v[MPA_LAST] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, p)] for p, _at, _set in LEAVES if '\\GlassDoor_' in p}
    if animate and (sorted(named('doors')) != sorted(R + p for p, _at, _set in LEAVES) or any(v != [GLASS_LAST] for v in last.values())):
        fail('the leaves stand, but the round start names %d of them and the glass leaves store LAST %s' % (len(named('doors')), sorted(last.values())))
    if not animate and named('doors'):
        fail('the leaves are sunk, but the round start still sends %d of them \'Activate\'' % len(named('doors')))
    late = named('door timer')
    if vault_open == bool(named('door')) or (bool(late) and R + ROLE['door timer'] not in beat):
        fail('the vault door is %s, but its wrapper names %s and its timer %s' % ('sunk' if vault_open else 'in its place', named('door'), late))
    if bool(named('door off')) != (R + ROLE['door off'] in late):
        fail('the door\'s DeactivateGeom names %s and the door\'s timer %s it' % (named('door off'), 'names' if R + ROLE['door off'] in late else 'does not name'))
    booms = [camp[r] for r in ('boom 1', 'boom 2', 'boom 3') if camp[r] is not None]
    reach = sorted({tuple(values(sc, k, 'Explode')[j] for j in EXPLODE_REACH) for k in booms})
    if blast:
        want = [R + CAMP[r] for r in ('boom 1', 'boom 2', 'boom 3', 'blast sound')] + [R + ROLE['post on'], R + ROLE['pre off']]
        if any(s not in late for s in want) or R + VAULT_POST not in named('post on') or R + VAULT_PRE not in named('pre off') or camp['blast sound'] is None or not A.named(sc, camp['blast sound']):
            fail('the blast is wired in part only: the door\'s timer names %s' % [s.split('!')[-1] for s in late])
    elif any(R + CAMP[r] in late for r in ('boom 1', 'boom 2', 'boom 3', 'blast sound')):
        fail('no vault state is swapped, but the door\'s timer names the blast: %s' % late)
    lamps = [s for s in A.named(sc, camp['alarm lamps'])] if camp['alarm lamps'] is not None else []
    toggles = [k for k, _i, _v in kl_fa.controllers(sc, 'LightToggle')]
    lights = [k for k in range(1, len(sc.nodes)) if ('\\' + LAMP) in sc.path[k] and sc.cls(k) in ('ZOMNILIGHT', 'ZGateLightSpot')]
    # ... and the spinning spots' slaves in the rooms next door (strip): what a gate light's list names. Hidden with their masters
    slaves = sorted({j for k in lights if sc.cls(k) == 'ZGateLightSpot'
                     for s in kl_fa.node_values(sc, k)[J.labels('dd', 'ZGateLightSpot').index(SLAVES)] for j in sc.resolve(s)})
    is_dark = lambda k: bool(kl_fa.node_values(sc, k)[3] and ents[k - 1].flags & HIDDEN)
    dark, dark_s = [k for k in lights if is_dark(k)], [k for k in slaves if is_dark(k)]
    if len(lamps) != 11 or len(lights) != 22 or len(slaves) != 8 or (toggles and (dark or dark_s)) or (not toggles and len(dark + dark_s) != 30) \
            or R + CAMP['alarm lamps'] not in beat or (R + CAMP['lights off'] in beat) != bool(toggles):
        fail('the alarm: %d lamps named, %d lights and %d slave spots, %d LightToggle, %d + %d of them hidden; the white light goes off: %s' % (
            len(lamps), len(lights), len(slaves), len(toggles), len(dark), len(dark_s), R + CAMP['lights off'] in beat))
    music = [s for s in named('music timer')]
    live = lambda names: [p for p in (R + CAMP['music'] + '\\' + n for n in names) if sc.resolve(p) and kl_fa.has(sc, sc.resolve(p)[0], 'PlayMusicLayerFade')]
    four = sum(1 for _k, _i, v in kl_fa.controllers(sc, 'PlayMusicLayerFade') if v[0] == LAYER4)
    if music != [R + CAMP['music']] or R + CAMP['music out'] not in beat or any(p not in beat for p in live(MUSIC_FADE)) or any(p not in box for p in live(MUSIC_RISE)) \
            or len(live(MUSIC_FADE)) < 3 or four not in (0, 9):
        fail('the music: the round start\'s timer names %s; the beat\'s end the way-out set: %s' % (music, R + CAMP['music out'] in beat))
    log('  chain: round start -> %s; ante-room box -> rods at %s s, %d more -> %.0f s -> %d objects%s' % (
        [s.split('!')[-1] for s in mon], ', '.join('%.0f' % x for x in rods), len(box) - 1 - len(rods), delay('beat timer'), len(beat),
        '; -> %.0f s -> %s' % (delay('door timer'), [s.split('!')[-1].split('\\')[-1] for s in late]) if late else ''))
    log('  the beat: vault door %s; blast %s; alarm lamps %d, %s; music: break-in set at %.0f s, way-out set at the beat\'s end (silent until the stream file has %d clips)' % (
        'sunk at build time' if vault_open else 'swings at the beat\'s end' + (', its body off %.0f s later' % delay('door timer') if named('door off') else ', stays'),
        'none (the vault stays intact)' if not blast else '%s: Explode reach %s, %d bodies come, %d go' % ('show' if reach == [(1.0, 1.0)] else 'REAL', reach, len(on), len(off)),
        len(lamps), '%d LightToggle' % len(toggles) if toggles else 'no LightToggle in the level, %d lights and %d slave spots hidden' % (len(dark), len(dark_s)),
        delay('music timer'), len(MUSIC_CLIPS))
        + '; %d fades of the fourth layer' % four)
    # ---- the enemies
    actors = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor']
    top_of = lambda k: sc.names[sc.top[k]]
    camp_sq, hall_sq = [k for k in squads if sc.names[k] in STAGE], [k for k in squads if sc.names[k] in HALL]
    more = sorted({top_of(k) for k in every} - set(STAGE) - set(HALL))
    men = [k for k in actors if top_of(k) in STAGE or top_of(k) in HALL]
    if squads:
        if len(camp_sq) != len(STAGE) or len(hall_sq) != len(HALL):
            fail('%d of the %d campaign squads and %d of the %d hall squads are in the level' % (len(camp_sq), len(STAGE), len(hall_sq), len(HALL)))
        # every man on the START's mesh part, on free floor (the doors that stand taken out: the plaza is beyond none)
        rows2 = kl_route.stations(lv, [START[1]] + [pos[ents[k - 1]] for k in men], opened=gates, near=30)
        off_mesh = [(k, r) for k, r in zip(men, rows2[1:]) if not (r['mesh'] and r['part'] == rows2[0]['part'] and r['reached'])]
        log('  enemies: %d campaign squads (%d men) + %d of F07\'s in the hall (%d men); %d of the %d men on the mesh part of the START and on free floor within 30' % (
            len(camp_sq), sum(top_of(k) in STAGE for k in men), len(hall_sq), sum(top_of(k) in HALL for k in men), len(men) - len(off_mesh), len(men)))
        for k, r in off_mesh:
            fail('%s at (%d, %d, %d): mesh %s, part %s, reached %s (gap %s)' % (sc.path[k][5:][-70:], *r['at'], r['mesh'], r['part'], r['reached'], r.get('gap')))
        # the places their routs name (cover, flank, defend, search): the hall's are this file's and must be on that part
        pts2, own = [], []
        for t in camp_sq + hall_sq:
            for j in range(t + 1, sc.end[t]):
                if any(sc.p.key(nm) in A.BEHAVE for nm, _b in sc.nodes[j]['ctrls']):      # what its lists name, and its own children
                    for h in sorted({h for s in A.named(sc, j) for h in sc.resolve(s)} | {c for c in range(j + 1, sc.end[j]) if sc.parent[c] == j}):
                        if sc.top[h] == t and sc.cls(h) in ('ZBoxPrimitive', 'ZSTDOBJ') and all(sc.p.key(nm) == 'RunToCoverPosInfoRout' for nm, _b in sc.nodes[h]['ctrls']):
                            pts2.append(pos[ents[h - 1]]); own.append((h, t in hall_sq))
        rows3 = kl_route.stations(lv, [START[1]] + pts2, opened=gates, near=86) if pts2 else [None]
        away = [(h, mine_, r) for (h, mine_), r in zip(own, rows3[1:]) if not (r['mesh'] and r['part'] == rows3[0]['part'])]
        log('  enemies: %d places their behaviour routs name; %d not on the START\'s mesh part (the campaign\'s own; a hunt\'s search box is a volume '
            'over the floor)%s' % (len(pts2), len(away), ''.join(
                '\n          %s (%d, %d, %d): %s off the mesh' % (sc.path[h][5:][-74:], *r['at'], r['off']) for h, _m, r in away[:12])))
        for h, mine_, r in away:
            if mine_:
                fail('the hall\'s %s at (%d, %d, %d) is not on the START\'s mesh part' % (sc.path[h][5:], *r['at']))
        # nothing of a squad names a node that is not there; the kinds are the ones that ran live
        kinds = collections.Counter(sc.p.key(nm) for t in camp_sq + hall_sq for j in range(t, sc.end[t]) for nm, _b in sc.nodes[j]['ctrls'])
        for t in camp_sq + hall_sq:
            for j in range(t, sc.end[t]):
                for s in A.named(sc, j):
                    if not sc.resolve(s):
                        fail('%s names %s, which is no node' % (sc.path[j][5:], s))
        first = sorted(set(kinds) - A.PLAIN - A.BEHAVE)
        log('  enemies: controllers of the squads: %s' % dict(kinds))
        if first:
            fail('the squads hold controllers that are not kl_fa_author\'s plain squad kinds: %s' % first)
        # each squad is started by its stage's object and waits for it
        role_of = {'start': 'start timer', 'down': 'start timer', 'beat': 'beat box', 'plaza': 'speak box'}
        lists_ = {r: {sc.top[h] for s in named(r) for h in sc.resolve(s)} for r in ('start timer', 'beat box', 'speak box', 'beat timer')}
        by = collections.Counter()
        for t in camp_sq + hall_sq:
            r = role_of[STAGE[sc.names[t]]] if sc.names[t] in STAGE else 'beat timer'
            by[r] += 1
            if t not in lists_[r]:
                fail('%s is not named by %s' % (sc.names[t], ROLE[r]))
            if values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE]:
                fail('%s is in the world from the load (ZSquadScript field %d)' % (sc.names[t], SQUAD_ACTIVE))
        # ... and nobody who comes LATER is put into the world where the crew may still be: no man of such a squad within
        # BEAT_CLEAR of a station of the round that lies before the squad's trigger, on that station's floor (a squad
        # that waits 'spawns in' when its rout is named: the 14 police of the beat stood in the vault lobby - BEAT_MEN)
        foyer = [n for n, _p in ROUTE_OUT].index('foyer')
        ahead = {'beat box': ROUTE_IN[:-1], 'beat timer': ROUTE_IN + ROUTE_VAULT, 'speak box': ROUTE_IN + ROUTE_VAULT + ROUTE_OUT[:foyer]}
        close = []
        for k in men:
            r = role_of[STAGE[top_of(k)]] if top_of(k) in STAGE else 'beat timer'
            p = pos[ents[k - 1]]
            close += [(math.dist(p, q), sc.path[k][5:][-60:], n, p) for n, q in ahead.get(r, ()) if abs(p[1] - q[1]) < 400.0]
        close.sort()
        log('  enemies: of the %d men who come after the round\'s start the nearest to a station that lies before his squad\'s trigger: %s' % (
            sum(top_of(k) not in STAGE or STAGE[top_of(k)] not in ('start', 'down') for k in men),
            '%s, %d from \'%s\'' % (close[0][1], close[0][0], close[0][2]) if close else '-'))
        for d, who, n, p in close:
            if d < BEAT_CLEAR:
                fail('%s at (%d, %d, %d) comes into the world %d from the station \'%s\', which the crew passes before his squad is started (%d wanted)' % (who, *p, d, n, BEAT_CLEAR))
        hunts = sum(1 for s in beat if s.endswith('\\' + HUNT))
        rows_ = collections.Counter((values(sc, k, 'ZSoldier')[3], values(sc, k, 'ZSoldier')[4], values(sc, k, 'ZSoldier')[7]) for k in men if top_of(k) in STAGE)
        stock = sum(n for (skill, _a, _h), n in rows_.items() if skill == 'eCustom')
        log('  enemies: started by: %s; %d hunts at the beat\'s end; soldier rows of the campaign\'s men (skill, accuracy, health): %s' % (
            dict(by), hunts, ', '.join('%d x %s %g / %g' % (n, *r) for r, n in sorted(rows_.items(), key=lambda t: -t[1]))))
        if 0 < stock < sum(rows_.values()):
            fail('%d of the campaign\'s %d men have a stock row, the others Dead Men\'s' % (stock, sum(rows_.values())))
    else:
        log('  enemies: none (a build without squads)')
    if more:
        log('  enemies: squads that are not this file\'s: %s' % more[:8])
    # police who come back: the eight bodies (re/fed_respawn.md: 8 police bodies a level load) and their points, clear of the squads' men
    bodies = [k for k in range(1, len(sc.nodes)) if sc.parent[k] == 0 and sc.names[k].startswith('Heroes!Henchmen_')]
    back = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and kl_fa.node_values(sc, k)[8] == 'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH']
    near = min([math.dist(pos[ents[a - 1]], pos[ents[b - 1]]) for a in bodies + back for b in men] or [9e9])
    log('  police who come back: %d bodies, %d AFTER_DEATH points; the nearest of the squads\' men stands %s from one' % (len(bodies), len(back), '%d' % near if men else '-'))
    if len(bodies) != 8 or len(back) != len(POLICE) or near < POLICE_CLEAR:
        fail('police who come back: %d bodies (8 wanted), %d points (%d), a squad\'s man %d from one (%d wanted)' % (len(bodies), len(back), len(POLICE), near, POLICE_CLEAR))
    # people: stock Fragile Alliance levels have 35..57 ZFFActor and 20..36 squads, Retomoto on the tab 99 / 55 (re/campaign_fa_tooling.md 5.4)
    log('  people: %d ZFFActor in %d squads + 16 player bodies (ran live: %d actors, %d squads)' % (len(actors), len(every), ACTORS_LIVE[0], ACTORS_LIVE[1]))
    if len(actors) > ACTORS_LIVE[0] or len(every) > ACTORS_LIVE[1]:
        fail('%d actors in %d squads: more than has run live (%d / %d)' % (len(actors), len(every), *ACTORS_LIVE))
    # ---- the escape: the one key-framed van on its road. kl_map_escape.van_check reads the WRITTEN files: who the
    # exit trigger calls, the keys against the road's height, the lane (five rays, every 20), the boxes at the stop,
    # the camera's eye and sight, the collision file; held against the plan in van.json when test() wrote one
    VL = ESC.Level(folder)
    plan, pj = None, os.path.join(folder, 'van.json')
    if os.path.isfile(pj):
        try:
            plan = plan_of(pj)
        except ValueError as x:
            fail('the van\'s plan beside the build: %s' % x)
    else:
        log('  van: no van.json beside the build: the drive is tested as the level has it, not against a plan')
    rep = ESC.van_check(VL, lambda s: log('  ' + s), plan)
    for x in rep['faults']:
        fail('van: ' + x)
    stop = wait = None
    if 'stop' not in rep:
        fail('van: %s' % '; '.join(rep['notes']))
    else:
        if any('FAEscCameraLAST' in x for x in rep['notes']):   # MEASURED: no such define in stock F07, F02, F05 either
            log('    (the stock form: no Dog Days Fragile Alliance level has that define - it is Dead Men\'s box, which the three car maps kept)')
        vans, fakes = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle'), kl_fa.controllers(sc, 'FakeTarget')
        N = ESC._van_nodes(sc, sc.top[vans[0][0]])
        ends_ = sorted({o for e in VL.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(VL.scene.head)})
        K = ESC.VanKeys(VL.scene.head, VL.ents[N['V_Van_00'] - 1].raw, ends_, kl_graft.keys_tracks)
        drive = K.pos[:K.drive()]
        wait, stop, end, board = drive[0], drive[K.f2p[ESC._leg_frames(sc, N['F07_Escape_Vehicle_01'])['Activate_Enter'][1]]], drive[-1], tuple(rep['board'])
        # the road under the standing van (its origin stands VAN_UP over it)
        g = VL.G.under(stop[0], stop[1] + 20.0, stop[2])
        log('  van: the stop: origin y %.1f, the road under it y %s (%s); keys at most %.1f off the road\'s height on the whole drive; drive in %.0f m, away %.0f m' % (
            stop[1], '%.1f' % g[0] if g else '-', VL.name(g[1]) if g else 'NO GROUND', rep['height_off'], rep['length_in'] / 100.0, rep['length_out'] / 100.0))
        if g is None or abs(stop[1] - ESC.VAN_UP - g[0]) > 3.0:
            fail('van: the standing van\'s origin (y %.1f) is not %.0f over the road (%s)' % (stop[1], ESC.VAN_UP, '%.1f' % g[0] if g else 'no ground'))
        # the boarding place (the box rides on the van: in the file it stands at the waiting place): a station of the
        # round - on the START's mesh part, on free floor - and reached in the collision from the banking hall
        rows4 = kl_route.stations(lv, [START[1], board, tuple(stop)], opened=gates, near=BOARD_NEAR)
        b4 = rows4[1]
        out_way = [p for n, p in ROUTE_OUT if n in ('hall', 'front entrance', 'plaza')] + [board]
        walk = kl_route.route(lv, out_way, opened=gates)
        log('  van: boarding place at the stop (%d, %d, %d): mesh %s, part %s (the START\'s: %s), free floor within %d: %s; the van\'s stop: mesh %s, part %s; '
            'hall -> front entrance -> plaza -> boarding place in the collision: %s' % (*board, b4['mesh'], b4['part'], part, BOARD_NEAR, b4['reached'],
                                                                                     rows4[2]['mesh'], rows4[2]['part'], say(walk)))
        if not (b4['mesh'] and b4['part'] == part and b4['reached']):
            fail('van: the boarding place (%d, %d, %d) is no station of the round: mesh %s, part %s, reached %s (gap %s)' % (*board, b4['mesh'], b4['part'], b4['reached'], b4.get('gap')))
        if not walk['free']:
            fail('van: no free way from the banking hall to the boarding place: crossed %s' % [n for _r, n in crossing(walk)])
        # the van's own path blocker (eToggle: it blocks where the van STANDS): the boarding place must be outside it
        inside = lambda k, p, up=0.0: all(abs(sum(VL.frame(k)[0][a][b] * ((p[a] + (up if a == 1 else 0.0)) - VL.frame(k)[1][a]) for a in range(3)))
                                          <= VL.values(k)['ZBoxPrimitive[%d]' % b] for b in range(3))
        pb = N['PathBlockerVan']
        log('  van: PathBlockerVan at (%d, %d, %d) half %s: the boarding place is %s it' % (
            *VL.place(pb), tuple(round(VL.values(pb)['ZBoxPrimitive[%d]' % b]) for b in range(3)), 'INSIDE' if inside(pb, board, 50.0) else 'outside'))
        if inside(pb, board, 50.0):
            fail('van: the boarding place lies inside the van\'s path blocker: an AI heister cannot be sent there')
        # the exit box calls the van: entered on the plaza, on the way to the boarding place - not from inside the bank
        ex = [k for k, _i, _v in kl_fa.controllers(sc, kl_fa.EXIT)]
        where = {n: [inside(k, p, 50.0) for k in ex] for n, p in ROUTE_OUT if n in ('hall', 'front entrance', 'plaza')}
        # (and, the stock form: the box holds the van's stop and its boarding place - 12 of 12 stock vans of F01 F04 F05 F07)
        at_van = [any(inside(k, p, 50.0) for k in ex) for p in (stop, board)]
        log('  van: exit trigger(s) %s: holds the hall %s, the front entrance %s, the plaza %s, the van\'s stop %s, the boarding place %s; drive in %.1f s' % (
            [sc.names[k].split('!')[-1] for k in ex], *[any(where[n]) for n in ('hall', 'front entrance', 'plaza')], *at_van, rep['seconds'][0]))
        if len(ex) != 1 or any(where['hall']) or not any(where['plaza']) or not all(at_van):
            fail('van: %d exit trigger(s); the hall inside one: %s, the plaza: %s, the van\'s stop: %s, the boarding place: %s (wanted: one, no, yes, yes, yes)' % (
                len(ex), any(where['hall']), any(where['plaza']), *at_van))
        # level bounds: neither the stop nor the boarding place in a bound or warn box; a bound on the drive AWAY is
        # the stock form (every stock van passes one with its passengers aboard: BOUND_AFTER), not at the stop itself
        hold = [(n, b) for n, p in (('the van\'s stop', stop), ('the boarding place', board)) for b, lo, hi in boxes
                if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
        for n, b in hold:
            fail('van: %s lies inside %s' % (n, b))
        for nm, a, b in rep['bounds']:
            ok = b < 0 or a >= BOUND_AFTER
            log('  van: the drive passes the level bound %s %.1f .. %.1f m %s the stop: %s' % (
                nm.split('!')[-2] if '!' in nm else nm, abs(a) / 100.0, abs(b) / 100.0, 'before' if b < 0 else 'after',
                'the van is empty there' if b < 0 else 'players aboard - the stock form (stock vans: 10.9 .. 105 m after their stops)' if ok else 'TOO NEAR THE STOP'))
            if not ok:
                fail('van: the level bound %s lies on the drive %d .. %d from the stop (after it: at least %d)' % (nm, a, b, BOUND_AFTER))
        # nobody starts in the lane: spawn points, player bodies, the squads' men (at the street's height: the
        # ante-room lies under the square) - and nobody is SENT into it: the escape marker and the stations of the way
        # out (the van is called from the plaza and its kill box rides at its nose: ESC_AT)
        P2 = ESC.Poly([tuple(p) for p in drive])
        sent = [('the escape marker', pos[ents[A.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea') - 1]])] + [('station \'%s\'' % n, p) for n, p in ROUTE_OUT]
        near_ = sorted((abs(P2.project(p)[1]) if 0.0 < P2.project(p)[0] < P2.len else min(math.dist(p, drive[0]), math.dist(p, drive[-1])), n, p)
                       for n, p in list(zip(names, pts))[1:] + [(sc.path[k][5:][-50:], pos[ents[k - 1]]) for k in men] + sent if abs(p[1] - stop[1]) < 400.0)
        mark = next(d for d, n, _p in near_ if n == sent[0][0])
        log('  van: the escape marker stands %d from the drive, %d from the boarding place at the stop' % (mark, math.dist(sent[0][1][::2], board[::2])))
        log('  van: of %d spawn points, player bodies, men, the marker and stations of the way out at the street\'s height the nearest to the drive is %s' % (
            len(near_), '%s, %d from it' % (near_[0][1], near_[0][0]) if near_ else '-'))
        for d, n, p in near_:
            if d < LANE_CLEAR:
                fail('van: %s at (%d, %d, %d) stands %d from the van\'s drive (%d wanted)' % (n, *p, d, LANE_CLEAR))
        # is the waiting van seen from where the crew comes out? (said, not a rule: 'out of sight' is the lead's wish)
        eyes = [(n, (p[0], p[1] + 160.0, p[2])) for n, p in ROUTE_OUT if n in ('front entrance', 'plaza')] + [('the boarding place', (board[0], board[1] + 160.0, board[2]))]
        solid = lambda e: [VL.name(r) for _d, r in VL.G.between(e, (wait[0], wait[1] + 100.0, wait[2])) if 'ColiObj' not in VL.name(r)]   # a ColiObj is not drawn
        seen = ['%s: %s' % (n, 'hidden by %s' % solid(e)[0] if solid(e) else 'SEEN (%d m)' % (math.dist(e, wait) / 100.0)) for n, e in eyes]
        log('  van: waits at (%d, %d, %d), %.0f m from its stop; from %s' % (*wait, math.dist(wait, stop) / 100.0, '; from '.join(seen)))
        if len(vans) != 1 or len(fakes) != 1:
            fail('van: %d OnlineEscAnimatedVehicle and %d FakeTarget in the level (one van, with its one target, is wanted: an unused van\'s target is the 0x686a66 crash)' % (len(vans), len(fakes)))
    # ---- the van's ZFakeTarget: inside the vision space, by kl_fa_bots_dyn's rule (the 0x686a66 crash: a target that
    # cannot register writes behind ZCheckVisible's table every frame; re/crash_686a66.md). The rule is for the place
    # at the LOAD; where the drive takes it is said beside it ('a registered target that later leaves the grid is
    # harmless': the note's section on 0x79bae0)
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
            if stop is not None and space is not None:
                later = [(n, D.outside(space, tuple(f['at'][a] + p[a] - wait[a] for a in range(3)))) for n, p in (('the stop', stop), ('the end of the drive', end))]
                log('    on the drive: %s' % '; '.join('at %s %s' % (n, 'inside' if o is None else 'outside by (%d, %d, %d)' % o) for n, o in later))
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
    log('  chunk table: %d entries (the tools\' line: %d); .prm %.1f, .fxc %.1f, .ANM %.1f, .WAV %.1f MB; the five load blocks %.0f MB (the Retomoto build that loaded seven times in one process: %.0f)' % (
        size['entries'], kl_impact.CHUNK_SAFE, size['.prm'] / 1e6, size['.fxc'] / 1e6, size['.anm'] / 1e6, size['.wav'] / 1e6, blocks, BLOCKS_LIVE))
    if blocks > BLOCKS_LIVE:
        fail('the five load blocks are %.0f MB, more than has loaded live (%.0f)' % (blocks, BLOCKS_LIVE))
    import kl_chars as C
    E = L.Edit(folder)                                  # read only: nothing of it is saved
    dead, _saved = C.dead_indices(E.p, E.sc, E.raw, E.oct, E.extra, lambda *a: None)
    log('  chunk table: %d of its indices are dead (free for the wardrobe, which takes %d with the four plates, and the gun looks)' % (dead, WARDROBE_CHUNKS))
    worn = os.path.isfile(os.path.join(folder, 'KLWardrobe.ini'))      # the finishing chain's folder: the wardrobe is in, the room it wanted is taken
    if worn:
        log('  chunk table: KLWardrobe.ini is there - the wardrobe is in the level, no room is asked for it')
    if size['entries'] > kl_impact.CHUNK_SAFE or (dead < WARDROBE_CHUNKS and not worn):
        fail('chunk table %d entries (line %d) with %d dead indices (the wardrobe wants %d)' % (size['entries'], kl_impact.CHUNK_SAFE, dead, WARDROBE_CHUNKS))
    # ---- kl_graft.verify's cross-references on the level AS WRITTEN (the build's own verify ran before finish() and
    # before every step of the finishing chain)
    for b in reverify(folder, log):
        fail('written level: ' + b[:200])
    log('kl_fa_bank.check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ the seven AI heisters (the finishing chain)
# tools/kl_fa_bots.py plans the squad of this level without a table entry of its own: START row -> the dock's
# ENTERS box -> vault lobby -> the two flights -> the vault's loot -> back up -> airlock stairs -> hall -> the front
# entrance's EXITS box -> the exit box -> beside the van's stop (re/bank_campaign.md F.3). What it cannot know is
# THE VAULT DOOR: the mesh runs through it, the door's body stands until DOOR_GONE after the beat's end and the
# loot is hidden until then (a take message to a hidden object is dropped, kl2 0x6cdb65: kl_fa_bots.cannot_take).
# So bots() changes the PLAN between kl_fa_bots.plan and its apply (kl_fa_bots.plan is wrapped for the length of
# one build, as Doors wraps kl_escape): the last way station before the loot becomes seven places IN THE ANTE-ROOM,
# inside the beat's box, and a TriggerDelay2 stands behind it in every squad's chain - kl_fa_bots' own two-stop form
# (make(): a wait without loot is a plain timer), which kl_fa_bots_dyn reads as 'a rally' and holds at cover during.
# THE GATE IS A CLOCK, NOT THE EVENT, on purpose: a bot stands in the box, so the beat began when it arrived at the
# latest (ASSUMPTION: an AI heister trips an ECPS_FA_MERCONLY box - re/retomoto_bots_rooms.md 8, 'measured in
# effect'), and beat + DOOR_GONE later the door's body is off whatever the swing did. Naming the squads' next step
# from the beat's timer instead would start it while a hold timer of the way in may still be armed; that timer then
# starts a step of the way in for a bot that is in the vault and the chain cannot come back (a step starts once:
# re/retomoto_bots_rooms.md 9.1, 'the join'). The price: a bot that arrives when the vault is open still waits.
# If the assumption is wrong and no human is in the ante-room, the bots walk on to a shut door after the wait and
# their loot wait runs out: they leave without the vault's money (nothing worse).
BOT_SQUAD = 'Gameplay!merc_bot_squad!'  # kl_fa_bots.SQUAD (that module is imported only where the squad is made or read)
# kl_fa_bots.RECIPE's M03_FA_A row ('cases', 'lane', 'window') without its drop link. GUESS, this file's own: ONE stop (that
# row has kl_fa_bots.STOP_MAX; the tellers' stacks are left to the loot tactic) and a loot wait of 30 s
BOT_OPT = {'stops': 1, 'cases': 'glass', 'lane': True, 'window': True, 'loot_seconds': 30}
GATE_AT = (400.0, -960.0, -11900.0)     # GUESS: the ante-room's middle, 6 m before the vault door (z -12509); the seven places are the mesh's round it
GATE_REACH = 400.0                      # ... within this of it
GATE_MORE = 2.0                         # s on top of the beat's and the door's delay, both read from the built level. GUESS
GATE_NAME = '020_Timer_vault_opens'     # no 'done_looting' in it: kl_fa_bots.check and kl_fa_bots_dyn take it for a wait that is no loot wait
GATE_CLEAR = 100.0                      # a place before the gate keeps kl_fa_bots.LOOT_WINDOW + this from the vault's hidden loot. GUESS


def bots_gate(B, P, log=print):
    """kl_fa_bots' plan P of built level B (a kl_fa_bots.Built) with the vault gate -> P (changed in place)."""
    import kl_fa_bots as F
    sc = B.sc
    loot = [i for i, s in enumerate(P['stations']) if s['kind'] == 'loot']
    if len(loot) != 1 or len(P['waits']) != 1 or P['waits'][0]['cases'] or not P['waits'][0]['loot']:
        raise ValueError('kl_fa_bank.bots_gate: the plan has %d loot stations and %d waits (wanted: one stop, the vault, no case)' % (len(loot), len(P['waits'])))
    i_loot, i_gate = loot[0], loot[0] - 1
    at_loot = [B.at(k) for s in P['waits'][0]['loot'] for k in sc.resolve(s)]
    if i_gate < 1 or P['stations'][i_gate]['kind'] != 'way' or not all(in_vault(p) for p in at_loot):
        raise ValueError('kl_fa_bank.bots_gate: the richest loot is not the vault\'s, or no way station stands before it')
    delay = {sc.path[k]: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    seconds = delay[R + ROLE['beat timer']] + delay[R + ROLE['door timer']] + GATE_MORE
    box = sc.resolve(R + ROLE['beat box'])[0]
    nav = F.Nav(B.scene.nav)
    home = nav.part[nav.at(*P['bots'][F.BOTS[0]]['start'])[0]]
    far = F.LOOT_WINDOW[0] + GATE_CLEAR
    cands = [c for c in nav.around(GATE_AT, GATE_REACH, home, dy=60.0)
             if B.in_box(box, c[:3]) and all(math.dist(c[:3], q) >= far for q in at_loot)]
    got = nav.spots(cands, 7, F.SEP, ref=GATE_AT)
    if len(got) < 7:
        raise ValueError('kl_fa_bank.bots_gate: only %d places for seven round %s inside the beat\'s box and %d from the vault\'s loot' % (len(got), GATE_AT, far))
    st = P['stations'][i_gate]
    st.update(what='the ante-room: the hold until the vault is open (%g s)' % seconds, distinct_places=7, places=[[round(v, 1) for v in g[:3]] for g in got])
    for b, N in enumerate(F.BOTS):
        P['bots'][N]['places'][i_gate] = [round(v, 1) for v in got[b][:3]]
    # the chain as kl_fa_bots' two-stop form: stop 0 = the ante-room with a plain timer, stop 1 = the vault
    steps = []
    for s in [s for s in P['steps'] if s['leg'] == 'in']:
        idx = [i for i in s['stations'] if i != i_loot]
        if idx:
            steps.append({'name': '%03d_DefendBehaviour_to_loot' % (10 + len(steps)), 'leg': 'in', 'stop': 0, 'stations': idx})
    if steps[-1]['stations'][-1] != i_gate:
        raise ValueError('kl_fa_bank.bots_gate: the way in does not end at the ante-room')
    steps.append({'name': '030_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 1, 'stations': [i_loot]})
    for m, s in enumerate(s for s in P['steps'] if s['leg'] == 'out'):
        steps.append(dict(s, name='%03d_DefendBehaviour_out' % (50 + m)))
    P['steps'] = steps
    w = P['waits'][0]
    w.update(name='040_Timer_done_looting', stop=1, timer='038_Timer_at_cases')
    P['waits'] = [collections.OrderedDict(name=GATE_NAME, stop=0, seconds=seconds, loot=[], worth=0, timer='018_Timer_at_cases', relays=[], cases={}), w]
    P['gate'] = {'station': i_gate, 'seconds': seconds, 'box': ROLE['beat box'], 'places': st['places'],
                 'nearest_hidden_loot': round(min(math.dist(g[:3], q) for g in got for q in at_loot))}
    note = ('THE VAULT GATE: station %d is seven places in the ante-room round (%d, %d, %d), inside %s and %d or more from the vault\'s loot; every squad '
            'waits %g s there (%s, a plain timer: the beat\'s %g s + the door\'s %g s + %g) before its step into the vault'
            % (i_gate + 1, *[sum(g[i] for g in got) / 7 for i in range(3)], ROLE['beat box'], P['gate']['nearest_hidden_loot'], seconds, GATE_NAME,
               delay[R + ROLE['beat timer']], delay[R + ROLE['door timer']], GATE_MORE))
    P['notes'].append(note)
    log('  NOTE ' + note)
    log('steps: %s' % [(s['name'], s['stations']) for s in steps])
    return P


def bots(src, dst, log=print):
    """The seven AI heisters into a COPY of a finished build of this level: kl_fa_bots.build with BOT_OPT and the
    vault gate (bots_gate) -> (kl_fa_bots' findings, its report). The dynamic step, cover, guns and talk are the
    other tools' own commands on the result (re/bank_campaign.md F)."""
    import kl_fa_bots as F
    plan0 = F.plan
    F.plan = lambda B, opt=None, log=print: bots_gate(B, plan0(B, opt, log), log)
    try:
        return F.build(src, dst, dict(BOT_OPT), log)
    finally:
        F.plan = plan0


def bots_check(folder, log=print):
    """What kl_fa_bots.check / kl_fa_bots_dyn.check do not know of this level, on a folder with the squad (with or
    without the dynamic step) -> list of faults: every squad's chain has the gate's timer, at least the beat's and
    the door's delay long, started by a step whose last place is inside the beat's box; and no place of any squad
    before the gate lies in the loot window of a vault object (hidden until the beat's end: a bot with a heist
    stage goes for it, kl2 0x8b94d0, and cannot take it)."""
    import kl_fa_bots as F
    B = F.Built(folder)
    sc, bad = B.sc, []
    def fail(s):
        bad.append(s); log('  FAIL ' + s)
    delay = {sc.path[k]: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    need = delay[R + ROLE['beat timer']] + delay[R + ROLE['door timer']]
    box = sc.resolve(R + ROLE['beat box'])[0]
    money = [o for o in F.money_objects(B) if in_vault(o['at'])]
    hidden = [o for o in money if B.ents[o['node'] - 1].flags & HIDDEN]
    tops = [t for t in sc.tops() if sc.names[t].startswith(F.SQUAD + 'Squad#')]
    defend = {k: v for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    if len(tops) != len(F.BOTS):                        # a folder without the squad must not pass (review round 1)
        fail('%d squads of AI heisters in the level, %d wanted' % (len(tops), len(F.BOTS)))
    near, n_place, n_gate = None, 0, 0
    for t in tops:
        mine = range(t, sc.end[t])
        gate = [k for k in mine if sc.names[k] == GATE_NAME]
        if len(gate) != 1 or delay[sc.path[gate[0]]] < need:
            fail('%s: %d timer(s) %s%s (the beat\'s and the door\'s delay: %g s)' % (sc.names[t], len(gate), GATE_NAME,
                 ' of %g s' % delay[sc.path[gate[0]]] if gate else '', need))
            continue
        # who starts the timer: Defend steps of this squad (after the dynamic step also a RandomTrigger's ways' last steps)
        ends = [B.at(sc.resolve(v[1][-1])[0]) for k, v in defend.items() if k in mine and v[1] and any(j == gate[0] for s in v[7] for j in sc.resolve(s))]
        if not ends or not all(B.in_box(box, p) for p in ends):
            fail('%s: %d step(s) start %s, their last places %s: not all inside %s' % (sc.names[t], len(ends), GATE_NAME, [tuple(round(x) for x in p) for p in ends], ROLE['beat box']))
        n_gate += 1
        # the places BEFORE the gate: both tools number a chain's steps in blocks, the gate's block is GATE_NAME's
        before = lambda k: sc.names[sc.parent[k]][:3].isdigit() and int(sc.names[sc.parent[k]][:3]) < int(GATE_NAME[:3])
        for k in mine:
            if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#') and before(k):
                n_place += 1
                for o in money:
                    d = math.dist(B.at(k), o['at'])
                    near = d if near is None else min(near, d)
                    if F.in_window(B.at(k), o['at']):
                        fail('%s: place %s at (%d, %d, %d) before the gate is %d from the vault\'s %s: inside the loot window' % (
                            sc.names[t], sc.path[k].split('\\', 2)[-1], *B.at(k), d, sc.names[o['node']]))
    log('kl_fa_bank.bots_check %s: %d squads, %d with the gate (%s >= %g s); %d places before the gate, the nearest %s from one of the vault\'s %d money '
        'objects (%d hidden at the load; the window is %d): %s' % (folder, len(tops), n_gate, GATE_NAME, need, n_place, '%d' % near if near is not None else '-',
                                                                 len(money), len(hidden), F.LOOT_WINDOW[0], 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ the delivered level (after the finishing chain)
# TWO THINGS NO TOOL OF THE CHAIN DOES (review round 1):
# seal()     THE ROOMS' NEIGHBOUR LISTS. The graft sends a list entry whose entity did not come along to the scene's
#            free REF id (kl_scene.remap_refs: 'an id no entity has', it resolves to nothing: 229 entries of two rooms
#            here, the form Late Night Opening loaded and played with). Every tool that ADDS entities afterwards hands
#            exactly that id to its first new entity: after the bots' step the 229 entries name the squad group
#            'Gameplay!merc_bot_squad!Squad#02', which kl2 0x83dca0 then counts among 'the objects of the room' (no
#            crash by live precedent - the tab's maps carry it - but not what was meant). seal() sends every list entry
#            that names an entity outside the map's own subtrees ('Locations/...') to the free id of the WRITTEN
#            scene. It must be the chain's LAST step: a tool that adds an entity after it takes the id again.
# reverify() kl_graft.verify's cross-reference tests, on the written archive. audit and preflight only quote the
#            BUILD's result.json, and the chain takes some 160 entities out and puts some 530 in afterwards (slot ids
#            of the .oct / .rmi / .rmc move with each). Lifted from kl_graft.verify with the build-time arguments
#            taken out (the reviewer's C:/kl_scratch/bank/review_crash_1/s/verify2.py), plus seal()'s rule.
MAP_SIDE = 'Locations/'                 # top-level names of the map's own subtrees: what a room's list may name


def room_cells(sc, buf):
    """[(room node, offset in the .buf, kind)] of every REF id cell of the rooms' gates and neighbour lists
    (kl_scene.room_refs); kind 'gate' / 'head' (a list's own room) / 'entry'. Rooms whose two offsets lie outside
    the .buf are left out (reverify says so)."""
    out = []
    for k in range(1, len(sc.nodes)):
        lab = kl_graft.labels(sc.cls(k))
        if 'ZROOM[9]' not in lab:
            continue
        us = units(sc.nodes[k]['props'][1:-1])
        ng, nl = kl_graft.u32(us[lab.index('ZROOM[0]')][0]), us[lab.index('ZROOM[1]')][0][1][0]
        g, l = kl_graft.u32(us[lab.index('ZROOM[9]')][0]), kl_graft.u32(us[lab.index('ZROOM[10]')][0])
        if (ng and not 16 <= g <= len(buf) - 0x74 * ng) or (nl and not 16 <= l < len(buf)):
            continue
        gate, heads = {g + 0x74 * i + 0x30 for i in range(ng)}, {l + 12 * i for i in range(nl)}
        out += [(k, o, 'gate' if o in gate else 'head' if o in heads else 'entry') for o in kl_scene.room_refs(buf, 'dd', g, ng, l, nl)]
    return out


def strays(sc, scene, buf):
    """-> ([offsets of list entries that name an entity outside the map's subtrees], Counter of who they name, the
    number of entries that name no entity at all = the parked ones, the scene's free REF id)."""
    ents = list(scene.entities())
    by_ref = {e.ref: k + 1 for k, e in enumerate(ents)}
    free = scene.ref_slots
    if free in by_ref:
        raise ValueError('kl_fa_bank: REF id %d (the header\'s slot count) is taken by %s' % (free, sc.path[by_ref[free]]))
    offs, who, parked = [], collections.Counter(), 0
    for _room, o, kind in room_cells(sc, buf):
        v = struct.unpack_from('<I', buf, o)[0]
        if kind != 'entry' or v in (0, 0xffffffff):
            continue
        if v not in by_ref:
            parked += 1
        elif not sc.names[sc.top[by_ref[v]]].startswith(MAP_SIDE):
            offs.append(o); who[sc.path[by_ref[v]][len(R):]] += 1
    return offs, who, parked, free


def seal(folder, log=print):
    """In place, on a folder the finishing chain is through with: the room list entries that name an entity outside
    the map (strays) go to the scene's free REF id. Only the .buf member changes. -> the number of entries moved."""
    import kl_chars as C
    lv = C.Lv(folder)
    sc, raw = lv.scene()
    buf = lv['.buf']
    offs, who, parked, free = strays(sc, kl_scene.Scene(raw, buf), buf)
    if offs:
        new = bytearray(buf)
        for o in offs:
            struct.pack_into('<I', new, o, free)
        lv['.buf'] = bytes(new)
        tmp = lv.src + '.tmp'
        kl_graft.write_zip(tmp, [(n, lv.files[n]) for n in lv.order])
        os.replace(tmp, lv.src)
    log('kl_fa_bank.seal %s: %d room list entries named an entity outside the map (%s) and now name the free REF id %d; %d named no entity before' % (
        folder, len(offs), ', '.join('%d x %s' % (n, p) for p, n in who.most_common(3)) or '-', free, parked))
    return len(offs)


def reverify(folder, log=print):
    """kl_graft.verify's cross-reference tests on the WRITTEN level of a folder (bare, finished or delivered) ->
    [problems]. What it follows: .gms / .buf round trip and Scene.check; the property tree against the schemas and
    its scene paths; model = ZGEOM[4]; the .prm's materials, textures and .oct records; the .oct room trees by slot
    id under their room; .rmi / .rmc boxes; gates and neighbour lists; KEYS offsets; .HVK / .sgd / surface-table
    REFs; the .sgp's rooms; FDX; sound references; animation sets; registered classes."""
    import kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_members as MB, kl_anm, kl_snd
    from kl_prp import Prp
    arch = archive_of(folder)
    with zipfile.ZipFile(arch) as z:
        low = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        get = lambda e: z.read(low[e.lower()])
        out = {e: get(e) for e in ('.gms', '.buf', '.prp', '.prm', '.TEX', '.MAT', '.oct', '.rmi', '.rmc', '.HVK', '.sgd', '.sgp', '.ANM')}
    Jn, snd, _loc = kl_fa.load(arch)
    sch, bad = J.schema('dd'), []
    sc = kl_scene.Scene(kl_gms.unpack(out['.gms']), out['.buf'])
    bad += sc.check()
    g2, b2 = sc.write()
    if kl_gms.pack(g2) != out['.gms'] or b2 != out['.buf']:
        bad.append('.gms / .buf do not round-trip')
    ents = list(sc.entities())
    by_slot, by_ref, head = {v + 2: e for e, v in sc.slots().items()}, {e.ref: e for e in ents}, len(sc.head)
    # .prp
    _data, misfits, paths, _names = J.check(Jn, log=lambda *_a: None)
    bad += ['%s: %s: %s' % (Jn.path[k], what, why) for k, what, why in misfits[:10]]
    bad += ['scene path does not resolve: %s %s -> %s' % (h, f, s) for _k, h, f, s in paths[:10]]
    twice = [n for n, c in collections.Counter(Jn.names[k] for k in Jn.tops()).items() if c > 1]
    if twice:
        bad.append('%d top-level names are used twice, e.g. %s' % (len(twice), twice[:3]))
    if len(Jn.nodes) != len(ents) + 1 or Jn.names[1:] != [e.name.decode('latin1') for e in ents] or Jn.tids[1:] != [e.tid for e in ents]:
        bad.append('.prp nodes and .gms entities differ')
    # .prm, .TEX, .MAT, .oct records
    p, prm = Prp(out['.prp']), G.read(out['.prm'], 'dd')
    proots = G.prp_roots(p, Jn.tids, sch, 'dd')
    geom = {w[0]: c for w, c, k in proots if w[0] != 'scene' and w[1] is None and k is None}
    wrong = sum(1 for k, e in enumerate(ents, 1) if e.model != geom.get(k, 0))
    if wrong:
        bad.append('%d entities: .gms model differs from ZGEOM[4]' % wrong)
    try:
        kinds, args = G.walk(prm, [(c, k) if k else c for _w, c, k in proots] + [e.model for e in ents if e.model])
    except ValueError as x:
        kinds, args = {}, {}
        bad.append('.prm: %s' % x)
    tex, mat = T.read_tex(out['.TEX']), T.read_mat(out['.MAT'])
    octj = O.Oct.parse(out['.oct'])
    if octj.pack() != out['.oct']:
        bad.append('.oct does not round-trip')
    recs, seen, miss = set(octj.record_refs()), collections.Counter(), collections.Counter()
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm, i, k, args.get(i, 0)):
            if typ == 'm' and prm.u16(i, off) not in mat.insts:
                miss['material'] += 1
            elif typ in 'tT' and prm.u32(i, off) and prm.u32(i, off) % G.SLOTS['dd'] not in tex.tex:
                miss['texture'] += 1
            elif typ == 'o':
                seen[prm.u32(i, off)] += 1
                miss['.oct record'] += prm.u32(i, off) not in recs
    bad += ['.prm names %d missing %ss' % (v, k) for k, v in miss.items() if v]
    if any(v > 1 for v in seen.values()):
        bad.append('.oct record named by two live model roots: %d' % sum(1 for v in seen.values() if v > 1))
    if mat.refs != T.material_refs(out['.prm']):
        bad.append('.MAT ref table is not the .prm\'s')
    lost = T.used_textures(mat) - set(tex.tex)
    if lost:
        bad.append('%d material textures are not in the .TEX' % len(lost))
    if any(not (0 < c < len(prm.chunks) and len(prm.chunks[c]) == 64 and prm.u16(c, 2) == 8) for _f, c in octj.tail):
        bad.append('.oct tail names a chunk that is not a 64-byte mesh')
    # rooms: the .oct trees by SLOT id, the room index, gates and lists by REF id
    is_room = kl_graft.is_room
    _e, ro = kl_graft.rooms_of(sc)
    if len(ro) != len(octj.rooms):
        bad.append('.oct has %d tree sets, the scene %d rooms' % (len(octj.rooms), len(ro)))
    def room_above(e):
        e = e.parent
        while e is not None and not is_room(e.tid):
            e = e.parent
        return e
    wr, nitems = collections.Counter(), 0
    for owner, five in zip(ro, octj.rooms):
        for ti, t in enumerate(five):
            for it in (t.items if t else ()):
                nitems += 1
                e = by_slot.get(it[0])
                if e is None:
                    wr['no entity'] += 1
                elif room_above(e) is not owner:
                    wr['other room'] += 1
                elif (ti == 4) != is_room(e.tid) or (ti < 4 and kl_gms.category(e.tid) != {0: 1, 1: 2, 2: 3, 3: 0}[ti]):
                    wr['wrong tree'] += 1
            if t:
                try:
                    t.check()
                except Exception as x:
                    wr['tree: %s' % x] += 1
    bad += ['.oct room trees: %d items: %s' % (v, k) for k, v in wr.items()]
    nbox = 0
    for ext in ('.rmi', '.rmc'):
        for b in O.RoomIndex.parse(out[ext]).boxes:
            nbox += 1
            if b.room not in by_slot or not is_room(by_slot[b.room].tid):
                bad.append('%s: box names slot id %d, not a room' % (ext, b.room))
            if b.second and b.second not in by_slot:
                bad.append('%s: second id %d is no entity' % (ext, b.second))
    buf = out['.buf']
    cells = room_cells(Jn, buf)
    rooms_in = {k for k, _o, _kind in cells}
    for k in range(1, len(Jn.nodes)):
        lab = kl_graft.labels(Jn.cls(k))
        if 'ZROOM[9]' in lab and k not in rooms_in:
            us = units(Jn.nodes[k]['props'][1:-1])
            if kl_graft.u32(us[lab.index('ZROOM[0]')][0]) or us[lab.index('ZROOM[1]')][0][1][0]:
                bad.append('%s: gates / lists outside the .buf' % Jn.path[k])
        for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
            if l in lab:
                v = kl_graft.u32(units(Jn.nodes[k]['props'][1:-1])[lab.index(l)][0])
                if v not in (0, 0xffffffff) and not 16 <= v < head:
                    bad.append('%s: %s outside the .buf head' % (Jn.path[k], l))
    for k, o, kind in cells:
        v = struct.unpack_from('<I', buf, o)[0]
        if o >= head:
            bad.append('%s: a gate / list cell lies outside the .buf head' % Jn.path[k])
        elif kind != 'entry' and (v not in by_ref or not is_room(by_ref[v].tid)) and not (kind == 'gate' and v in (0, 0xffffffff)):
            bad.append('%s: %s names REF %d, not a room' % (Jn.path[k], 'a gate' if kind == 'gate' else 'a list', v))
    stray, who, parked, free = strays(Jn, sc, buf)
    if stray:                                           # seal()'s rule
        bad.append('%d room list entries name an entity outside the map (%s): seal() not run after the last tool that adds entities?' % (
            len(stray), ', '.join('%d x %s' % (n, q) for q, n in who.most_common(3))))
    # KEYS, .HVK, .sgd, .sgp, the surface table, FDX
    nk = 0
    for e in ents:
        tr = kl_graft.keys_tracks(e.raw)
        nk += len(tr)
        if any(not 16 <= v < head for _p, ko in tr for v in ko):
            bad.append('%r: KEYS offset outside the .buf head' % e)
    h = kl_hvk.Hvk(out['.HVK'])
    if h.serialize() != out['.HVK']:
        bad.append('.HVK does not round-trip')
    n = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) not in by_ref)
    if n:
        bad.append('.HVK: %d placements name no entity' % n)
    for name, payload in MB.sgd_read(out['.sgd']):
        if name in ('HavokShatterOctree', 'ExplodableOctree'):
            n = sum(1 for leaf in MB.Octree(payload).leaves if leaf[0] not in by_ref)
            if n:
                bad.append('.sgd %s: %d leaves name no entity' % (name, n))
    if sorted(r[0] for r in MB.Sgp(out['.sgp']).rooms) != sorted(Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k])):
        bad.append('.sgp rooms are not the level\'s rooms')
    table = MB.SurfaceTable(sc.tail)
    if table.refs() - set(by_ref):
        bad.append('surface table names %d entities that are gone' % len(table.refs() - set(by_ref)))
    n = sum(1 for s in h.shapes for su, _f, _n in s.sub if su > len(table.materials))
    if n:
        bad.append('.HVK: %d sub-parts name a surface row past the %d of the table' % (n, len(table.materials)))
    if sc.fdx is not None:
        for r in MB.fdx_read(buf, sc.fdx)[1]:
            if kinds.get(r['model']) != 'root':
                bad.append('FDX record names chunk %d, not a model' % r['model'])
    # sound references, animation sets, registered classes
    objs = kl_snd.Snd('dd', snd).kind
    n = nsnd = 0
    for k in range(1, len(Jn.nodes)):
        for cls, holder, key in kl_graft.objects(Jn, k):
            for f, u in zip(sch.fields(cls), units(kl_graft.get_obj(holder, key)[1:-1])):
                if f.type in kl_graft.SOUND_TYPES and f.kind == 'I' and kl_graft.u32(u[0]):
                    nsnd += 1
                    n += kl_graft.u32(u[0]) not in objs and kl_graft.u32(u[0]) != kl_snd.LS_SOUND
    if n:
        bad.append('%d sound references name no object of the .SND' % n)
    lack = {s for s in p.keys if s.startswith(kl_anm.PREFIX)} - {c.name for c in kl_anm.Anm(out['.ANM'], 'dd').cols}
    if lack:
        bad.append('animation sets the .ANM lacks: %s' % sorted(lack))
    unreg = {hex(t): c for t, c in collections.Counter(e.tid for e in ents).items() if t not in sch.geoms}
    if unreg:
        bad.append('entity classes kl2.exe does not register: %s' % unreg)
    log('  the written level again (kl_graft.verify\'s cross-references): %d entities, %d reachable chunks of %d, %d room sets with %d tree items, %d room boxes, '
        '%d gate / list cells (%d list entries parked on the free REF id %d), %d KEYS tracks, %d sound references, %d .HVK placements, misfits %d: problems: %d' % (
            len(ents), len(kinds), len(prm.chunks), len(octj.rooms), nitems, nbox, len(cells), parked, free, nk, nsnd, sum(len(s.inst) for s in h.shapes), len(misfits), len(bad)))
    for b in bad[:40]:
        log('  PROBLEM (written level): ' + b[:300])
    return bad


def build(out, log=print, plan=None):
    """F07 + M03_A with the layer into <out>/F07+M03_A campaign -> (kl_maps.one's result, that folder, the van's
    plan, kl_map_escape's report of what it did to the van). plan: a plan of ROAD (plan_of / van_plan); None = made
    here, on a BARE graft of the two levels built into <out>/_bare (60 s, 310 MB) and deleted again - the plan
    needs a built level's collision and must not see the layer's own van (van_plan)."""
    import shutil
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign')
        try:
            if not r.get('ok'):
                raise ValueError('kl_fa_bank: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    try:
        with ESC.van_layer(plan, log) as st, doors(log):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_bank')
    except ValueError:                                  # van_layer: 'a step of the van did not run'. After a build that
        if r.get('ok') or not r:                        # failed (r says why) that is no news; after one that did not, it is
            raise
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


def test(out, keep=False, log=print, plan=None):
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1. Beside the archive: van.json
    (the van's plan, what was done to F07's van, kl_map_escape.van_check's report: kl_map_escape.van_build's form)."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    L = ESC.Level(folder)
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], check=ESC.van_check(L, lambda *a: None, plan)),
                  f, indent=1, default=str)
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
        global DOORS_ANIMATE, VAULT_OPEN, VAULT_DOOR_GOES, GATE_VAULT, CASE, BEAT, NO_AI, ALARM_LIGHTS, VAULT_BLAST, STOCK_ROWS, MUSIC_LAYER4
        MUSIC_LAYER4 = '--music-layer4' in a
        NO_AI = '--no-ai' in a
        ALARM_LIGHTS = '--alarm-lights' in a
        VAULT_BLAST = None if '--no-blast' in a else 'real' if '--blast-real' in a else VAULT_BLAST
        STOCK_ROWS = '--dead-men-rows' not in a
        DOORS_ANIMATE = '--doors-animate' in a
        VAULT_OPEN = '--vault-open' in a
        VAULT_DOOR_GOES = '--vault-stays' not in a
        GATE_VAULT = '--loot-shown' not in a
        CASE = None if '--loot-bags' in a else CASE
        if '--beat' in a:                               # OPTION, seconds from the ante-room box to the vault door
            BEAT = float(a[a.index('--beat') + 1])
        plan = plan_of(a[a.index('--plan') + 1]) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'inventory':
        inventory(a[1])
    elif len(a) == 3 and a[0] == 'bots':
        out, _rep = bots(a[1], a[2])
        sys.exit(1 if any(x[0] == 'FAIL' for x in out) or bots_check(a[2]) else 0)
    elif len(a) == 2 and a[0] == 'bots-check':
        sys.exit(1 if bots_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'seal':
        seal(a[1])
    elif len(a) == 2 and a[0] == 'reverify':
        bad = reverify(a[1])
        print('kl_fa_bank.reverify %s: problems: %d' % (a[1], len(bad)))
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_bank                   # kl_graft imports this file by name: one module, one set of flags
    kl_fa_bank.main()
