# The bank, the campaign way: M03_A 'Withdrawal' (+ M03_B 'Cracking Up') as a Fragile Alliance map

2026-10-11, agent cfa-bank. STUDY ONLY, written offline: nothing was installed, the game was not started,
no existing tool was edited, nothing was committed. Scratch scripts: `G:/kl_scratch/cfa_bank/` (named below
as `<s>/`). Trial builds: `<work>/build/cfa/bank/` (result.json, log.txt, graft.txt kept; archives deleted).
Pictures: `<work>/build/cfa/bank/pics/`.

Evidence labels: **MEASURED** (output I produced; the command is named), **READ** (code or an existing note;
file and place named), **ASSUMED** (reason given), **GUESS** (a coordinate or value I propose and did not measure).
Coordinates are world units (100 = 1 m), x y z with y up, as `kl_maps.world()` composes them.

STATE OF THIS FILE: complete (sections 0 - 7).

## 0. Short answers

- M03_A grafts under F07 as it stands: MEASURED `python tools/kl_maps.py one <work>/build/cfa/bank F07 M03_A
  --campaign` -> ok, 0 dangling scene paths, the only problems are the missing Fragile Alliance layer and one
  ambience clip. Lightened and with the wardrobe on top it is LIGHTER than the Retomoto build the owner plays.
  (corrected by the second agent: true, but the 59.5 MB below is the map WITHOUT one enemy in it. With the 22
  campaign squads of 4.1 kept it is .prm 67.8 MB, chunk table 65,640, archive 191 MB - MEASURED, section 8.2 -
  still under Retomoto's 74.2 MB, but over stock F07's 63.6 MB.)
- The whole campaign route lobby -> vault -> front street lies in ONE connected part of the level's own
  navigation mesh (566 of 902 polygons): the seven AI heisters need no link, no hop, no hook teleport.
- M03_A is the SAME building at the SAME world coordinates as M03_FA_A, with 84 % of its texture pictures
  byte-identical; what it adds is the vault complex (seven rooms, about 700 placed objects, floors down to
  y -960) that the Fragile Alliance map does not have at all. It is a second map, not a rebuild of the first.
- M03_B does not belong in it: its walkable ground starts 1.3 km from the bank, the chapter is a van ride,
  the chain build breaks the .prm chunk table (79,408 of 73,728) and its city block overlaps the bank's.

## 1. What the place is

### 1.1 Rooms and floors

MEASURED `python tools/kl_maps.py what M03_A` (18,703 entities, 26 rooms + a backdrop) and `python <s>/rooms.py
M03_A` (extent of the placed objects under each room, 2nd..98th percentile; objects at the origin left out,
because world-space baked meshes sit at 0 0 0 and stretch `what`'s boxes to the origin).

| floor (y) | room | entities | x | y | z |
|---|---|---:|---|---|---|
| vault, -960 | `M03_A_Vault_01a` | 155 | -5..1100 | -960..-403 | -13530..-12659 |
| vault, -960 | `M03_A_VaultEntrance_01a` (ante-room, the vault door at z -12625) | 183 | 0..800 | -964..-160 | -12600..-10800 |
| -560 | `M03_A_VaultStairs_02a` (cross corridor + lower flight) | 176 | -600..1400 | -588..-23 | -11400..-9800 |
| -160 | `M03_A_ViewBooth_01a`, `#01`, `#02` (three guard booths) | 10 each | -600..-400 / 1000..1200 | -160..242 | -10000..-8600 |
| -160..240 | `M03_A_VaultStairs_01a` (upper flight) | 258 | -400..1200 | -193..585 | -10000..-8000 |
| 240 | `M03_A_VaultLobby_01a` (under the banking hall) | 365 | -600..1709 | 218..840 | -7800..-5447 |
| 240 | `M03_A_Garage_AdoptRoomHack_01a` (loading dock) | 208 | -201..1100 | 200..600 | -6400..-4712 |
| 240 | `M03_A_SecurityHall_01a`, `ControlRm_01a`, `Armory_01a`, `BreakRm_01a` | 100, 166, 31, 63 | -1196..-200 | 227..673 | -6400..-4633 |
| 800 | `M03_A_VaultLobbyFoyer_01a` (behind the hall's sliding doors) | 38 | -200..600 | 792..1257 | -5870..-5271 |
| 800 | `M03_A_Bank_Main_01` (the banking hall / lobby, gallery at y 1220) | 2,597 | -1160..1800 | 800..2052 | -9402..-5800 |
| 700..800 | `M03_A_Outside_02A` (front plaza and street) | 1,146 | -12642..11933 | 0..3473 | -19396..-7100 |
| 0..800 | `M03_A_Outside_01A` (yard, back streets) | 1,938 | -6911..6100 | 0..2750 | -6600..5815 |
| 300..1900 | `M03_A_Parkade_*` (six rooms: the car park's stair tower and deck) | 339 | -4600..-3200 | 200..1900 | -7173..-200 |
| - | `M03_A_Garage_01a` (a holder room: the dock's roller door and a few shared pieces), `Outside_03A`, `Outside_04_Buildings`, `M03_Backdrop_A_00` (far scenery) | 11, 15, 19, 4 | | | |

The bank stands on a slope: front street y 705, plaza and banking hall y 800, loading dock and yard y 200,
alley behind y 150, vault y -960 (17.6 m under the hall, UNDER the front plaza: z -10800..-13530).

Pictures (MEASURED `python <s>/nav.py M03_A <png> ...`: the level's navigation mesh as kl_graft converts it,
top-down, +z up, +x right, grid 10 m, colour = height):
- `pics/M03_A_nav_height.png` whole level; `pics/M03_FA_A_nav_height.png` the Fragile Alliance sibling, same scale
- `pics/M03_A_floor_vault.png` y -1000..-100: stairs (top, z -8000) -> cross corridor with the booths ->
  ante-room -> the door's narrow neck (z -12640) -> the vault (bottom)
- `pics/M03_A_floor_garage.png` y -100..500: alley (top) / yard / loading dock / vault lobby / stairs
- `pics/M03_A_floor_lobby.png` y 500..1100: banking hall with its four corner stairs, plaza, 180 m of street
- `pics/M03_A_floor_upper.png` y 1100..1500: gallery, parkade top, bank roof
- `pics/M03_B_nav_height.png` chapter 4's walkable ground (x 36,756..62,799, z 123,654..191,803)

### 1.2 Top-level subtrees and the side the graft gives them

MEASURED `python tools/kl_maps.py sides M03_A` (and `M03_B`).

| M03_A | nodes | side | campaign pre-pass |
|---|---:|---|---|
| `Locations/*` | 8,134 | map | kept |
| `CloneGroup_Locations` | 1,602 | map | kept (1,594 without a template + clone groups of kept templates 541) |
| `Locations/M03_A/M03A_Audio.zip!` | 105 | map | kept (ambience) |
| `Special!` | 329 | map | 100 kept (47 `NoCoverBox`, 45 `PlayerCoverCollision`, 3 `LevelBound` + their warn boxes), 229 dropped |
| `Effects/*` (4 templates), `M03_Backdrop_A_00` | 53, 4 | map | kept |
| `GamePlay!` | 1,409 | map | dropped (all squads, triggers, door proxies, the vault script) |
| `COOP!` | 760 | map | dropped (police waves, choppers, co-op gates) |
| `CutScenes/*`, `AI_Players!`, `Ropes!` | 65, 8, 8 | map | dropped |
| `AllLevels/mainsceneincludes.zip`, `CloneGroup_Effects` (systems), 2 singles | 2,492, 3,199, 2 | systems | not taken (F07's are used) |

Result: 489 subtrees dropped (2,479 nodes), 10,531 nodes stay. M03_B: 633 subtrees dropped (7,161 nodes:
`Specials!` 3,945, `Enemies!` 2,635 ...), 3,619 stay.

### 1.3 The campaign's flow, rebuilt from its scripted objects

MEASURED `python <s>/dump.py M03_A` (every node with class, controllers, world place: `<s>/M03_A.tsv`) and
`python <s>/tree.py M03_A "GamePlay!" --vals` (`<s>/t_gameplay.txt`, `t_vault.txt`, `t_lobby.txt`, `t_coop.txt`,
`t_special.txt`). Places are the objects' own.

| # | beat | objects (place) |
|---|---|---|
| 1 | Start in the back streets, meet the vault breaker | `Special!Checkpointsave!CP_01_PosP1` (-2976, 154, -202); `AI_Players!Kane` (-535, 803, 861); `AI_Players!Vaultbreaker_Merc_01` (-3462, 901, -4876); objective `MissionObjective_005_GoToVan` |
| 2 | Climb the wall into the car park, up its stair tower | `GamePlay!1_Civilian_Parking!Pathblocker_ClimbWall` (-2710, 237, -424); navigation links of kind 1 (climb) at x -3210 / -2938: y 150 -> 274 (z -409 -> -480) and y 284 -> 404 (z -540 -> -575); `CP_02` (-1864, 1292, -5070) |
| 3 | Bank roof: sleeping gas into the ventilation | `MissionObjective_010_Valium` (428, 1407, -5562); `GamePlay!2_Secure_Parking!GasBox!30_PlayerAction_GasInVentilation#05` (431, 1484, -5557) |
| 4 | Rappel into the secure yard | `Special!RappelPoint!RappelPoint_01!RappelBox` (33, 1579, -4576); navigation link kind 6 (-35, 1435, -4560) -> (-35, 200, -4525); `Jump#060` (-313, 205, -4398) |
| 5 | Yard and loading dock: patrol guards, the armoured car, the garage door | `GamePlay!2_Secure_Parking!AnimProxy_Garage_Open` (`MatPosAnimProxy` frames 1..150 on `M03_A_Garage_01a\SI0201_M03_BackDorAnim_01`); `Jump#131` (266, 202, -5002) |
| 6 | Vault lobby (y 240): the vault breaker opens the glass slide doors | `CP_03_PosP1` (394, 241, -7129); `GamePlay!4_Vault_Part!SlideDoors_Open` (`MatPosAnimProxy` 1..30 on `M03_A_VaultLobby_01a\SI0103_M03_BankVault_DDorSlide_01..04`) |
| 7 | Down the two flights, three guard pairs | `Guards_01` (-122..-18, -158, -9265..-9145), `Guards_02` (-98..-52, -559, -10673..-10548), `Guards_03` (326..719, -959, -11889..-11725) |
| 8 | **The vault door**: the vault breaker hacks six locking rods one after the other, guards and police come down meanwhile, then the door swings | `TB_VbByVault` (460, -714, -12152) -> `MatPosAnimProxy_Rod#01..#06` (frames 1..60 on `M03_A_VaultEntrance_01a\Rod_A01..` + `RodLight_*`), sounds `Special!Audio!GeomActivator_PlaysoundVaultRod01..05`, `...FinalRod`, `...VaultOpen`; `GamePlay!4_Vault_Part!VaultDoors_Open` (`MatPosAnimProxy` 1..75 on `...VaultEntrance_01a\SI0102_M03_BankVault_Door_PRE_01`, then `PathBlocker_Vault` (401, -911, -12626)); `CP_03b` (634, -958, -12226) |
| 9 | **Inside the vault**: charges on the deposit boxes, 15 s, blast, fire; the room is swapped | `Timer_to15secs` (`TriggerDelay` 15) -> `BoomBox_BlowVault#01` (407, -839, -11680: `Explode` + `ShakeCamera`), `#02` (407, -841, -13035), `#03` (695, -841, -12498); `Activator_BlowVault` -> `Sound_VaultExplosion` (396, -746, -11894), `FireDamageBox#01/#02`; `GeomDeactivator_PRE_Vault` / `GeomActivator_POST_Vault` (`Vault_01a\Vault_PRE` -> `Vault_POST`), `GeomActivator_Efx_Geoms` (fire, smoke) |
| 10 | Take the briefcase | `MissionObjective_020_Suitcase` (144, -959, -13277); `CP_04_PosP1` (399, -960, -12818) |
| 11 | Back up; alarm; reinforcements in the vault lobby and the dock | `Guards_Reinforcement_*`, `Police_Reinforcement_*`, `Vault_Reinforcement_Police_01..03` (y 201..243, z -7490..-5656); stairs to the hall `Jump#110` (1538, 355, -5822) |
| 12 | The banking hall: Lynch has shot the hostages; hold it | `CP_05_PosP1` (295, 802, -6052); `MissionObjective_030_JoinLynch` (305, 802, -8319); sliding doors `GamePlay!5_Lobby!LobbySlidedoors!BankLobby_Slidingdoors_DoorCtrl` (299, 936, -5802) |
| 13 | Police on the plaza: tear gas through the windows, two waves by car, SWAT with shields, two helicopters, snipers | `Police_Outside_Teargas_01` (2016..2201, 706, -9599..-9418), `Police_OutSide_01` (-1842..-1437, 705, -9621..-9542), `COOP!Squads_Lobby!Police_Reinforce_Wave1_*` / `Wave2_*` (cars at (-2622..-3156, 710, -9793..-11623) and (4477..5181, 707..712, -9632..-11117)), `Chopper01/02`, `Sniper_OutSide_01` (2691, 1404, -11933), (-2058, 2305, -13189) |
| 14 | The getaway van comes down the street, everybody in, drive off: end | `Squad_GetAwayVan_ForEscape\GetawayVan_ChaseVersion` (`ZHavokCar` at (-4900, 702, -11750)); `GamePlay!5_Lobby!TriggerBox_GetAwayVan` (307, 880, -9695); `GetAwayVan_FusionSquad` (`VehicleMoveOnRoadBehaviourRout`, `PlayerEnterVehicleAction`, `Timer_Endlevel`); `Special!SceneChange!SceneChangerExitPoint`; objective `MissionObjective_050_GetIntoVan` (281, 811, -9267) |

The developers' own jump list gives the same order (`Special!JumpPoints!Jump#010` .. `#132`: (-619, 805, 1007),
(1361, 50, 291), (-1739, 150, 486), (-2654, 204, -3718), (-4156, 302, -4480), (-14, 1410, -5132),
(-313, 205, -4398), (422, 242, -6188), (902, 240, -6545), (527, -950, -11979), (463, -956, -13238),
(1538, 355, -5822), (309, 803, -5624), (377, 801, -8423), (266, 202, -5002), (291, 714, -11159)).

The campaign bounds: `Special!Levelbound!LevelBound_Outside_Front` (355, 943, -14140), `..._Left` (3763, 843,
-10211), `..._Right` (-2837, 928, -10916): they are kept by the pre-pass and fence in the plaza only.

Chapter 4 (M03_B), MEASURED the same way: the heroes start in the van (`Hero_Allies!Hero!Hero_01_Bank` (7582, 12,
8611)), ride it through the city onto the motorway (`Specials!RoadSplines!*`, 58 `ZHavokCar`), fight on foot at a
tunnel road block (`CP_03_PosP1` (46269, -2252, 135461)), ride on, crash at an underpass (`CP_06` (55215, -1116,
144662)), walk into a subway station (`Pos07_subway` (44604, -1956, 184543)) and leave by train
(`Specials!Triggers!Subway!SceneChangerExitPoint` (54580, -2673, 185092)).

### 1.4 What M03_A has that M03_FA_A lacks, and what they share

MEASURED `python <s>/share.py M03_A M03_FA_A` (model entities under `Locations` / `CloneGroup_Locations`, matched by
class + name + world place within 5 units) and `python <s>/texshare.py M03_A M03_FA_A M03_B`.

- **Same world coordinates.** 2,726 of M03_A's 6,391 placed map objects (43 %) have a twin of the same class and
  name at the same place in M03_FA_A; whole rooms are identical (`Parkade_Deck_01a` 94 of 94, `Outside_04_Buildings`
  18 of 18, `Parkade_StairwayCorridor_01b` 27 of 32, `ControlRm_01a` 78 of 123, `Bank_Main_01` 635 of 1,337). The
  other way: 2,726 of M03_FA_A's 5,469 (50 %).
- **Same textures.** 1,155 of M03_A's 1,371 distinct pictures are byte-identical in M03_FA_A (135.1 of 192.3 MB);
  1,155 of M03_FA_A's 1,206. The 216 pictures only M03_A has (57.2 MB) are mostly its people and vehicles (heroes,
  police, getaway van, SWAT truck, helicopter), which the campaign pre-pass drops.
- **Only in M03_A (0 % shared):** `Vault_01a` (134 placed), `VaultEntrance_01a` (150), `VaultStairs_01a` (210),
  `VaultStairs_02a` (149), `ViewBooth_01a` x3 (27), `Armory_01a` (28): the whole way down and the vault. 724 names
  hold 'BankVault' (183 in M03_FA_A). Its navigation mesh has 902 polygons down to y -960; M03_FA_A's has 697 and
  none below y 0 (`python <s>/nav.py M03_FA_A`).
- **Only in M03_FA_A:** the enlarged loading dock `M03_FAA_Garage_01a` (349 placed, 40 shared), `SecurityHall02_01a`
  (48), `Parkade_StairwayRoom_01a` (68); the eight money boxes `PC0500_M03_MoneyBox_*` and four cash drawers
  `PC0500_M03_FA_Cashdrawer_*` (its loot).
- Vehicles in M03_A: 11 `ZHavokCar` (the getaway van twice, the armoured car twice, six police cars, the SWAT
  van) and 2 `ZHeli` (`COOP!Squads_Lobby!Chopper01/02`), all inside campaign squads that the pre-pass drops.
- Where the Fragile Alliance map plays (MEASURED `python <s>/tree.py M03_FA_A "SpawnPoint!" --vals2` and
  `<s>/M03_FA_A.tsv`): START on the plaza (-2262..-1214, 791, -12275..-11224), in by the front
  (`Triggers!EnterBankTrigger_01` (303, 974, -9407)), loot in the loading dock (`GUIResources!MapIconMainLoot`
  (667, 242, -6334)), out by the back (`ExitBankTrigger_01` (291, 399, -4668)), over the yard wall, cars in the
  alley (`Triggers!ExitTrigger_01` (408, 396, 460), `BoardingTrigger_Car` (3252, 133, -20)).

So a campaign-way map shares the hall, the plaza and the vault-lobby level with the map the owner already plays;
it adds 95 m of stairs, corridors and the vault below them, and it leaves by the FRONT.

## 2. Leftovers of a planned Fragile Alliance version

MEASURED `python -I <s>/leftovers.py M03_A` (every printable string of every archive member and of the .WHD / .SND
beside it matching fragile | online | multiplayer | _FA_ | FA_A | DL0n | Scenarios | eSPAWN | SpawnPoint |
OnlineMoney | MoneyBox | PIP_ | Traitor | Greed; `<s>/leftovers_M03_A.txt`, `_M03_B.txt`) and the class /
controller census of `<s>/M03_A.tsv`.

- **No Fragile Alliance layer was ever in these two levels.** 0 `ZSpawnPoint`, 0 `Online*` controllers, 0
  `OnlineMoney*`, 0 PIP points in M03_A and in M03_B.
- .prp / .buf: the only hits are `IngameFragileAllianceKILLERCamera` (a camera of the systems, in every level),
  31 map objects `SO0304_M03_FA_*` / `SO0202_M03_FA_Fix_*` (`..._FA_Etage_V1..H4`, `_Stukstor`, `_Stuklille`,
  `_Pillars`, `_Store`, `_Sign47`: a building FACADE across the plaza - 'FA' is not Fragile Alliance there,
  ASSUMED from the Danish part names) and one `SO0301_USA_animFence_02_FA_01` (`MatPosAnim`).
- .TEX: `UserInterface/UI_FA_Respawn_pip_mask` (user interface, every level).
- .SND of M03_A: `audio:levelsetup/multiplayer/m03_fa_a/sfx/doors/garagedoor_open#sound` - the campaign level
  plays a sound that is filed under the Fragile Alliance level. That is the one real trace: the two bank levels
  were worked on together. The rest (`Dialog/Multiplayer/FA_Menu/Fragile_Alliance_01..08`, `Traitor_Death_*`)
  is the menu's and the flashbacks', in every level.
- .LOC (the same table in every level): the ten placeholder briefings named in the task. Nothing in M03_A or
  M03_B names 'Bank Vault' (BriefingDL01) beyond that text.
- M03_B: `ZVehicleSpawnGroup` / `ZCivilianVehicleSpawnGroup` (traffic for the chase) are the only 'spawn' hits.

## 3. Can it be grafted

### 3.1 The trial builds

All MEASURED; folders under `<work>/build/cfa/bank/`.

| | F07 + M03_A | F07 + M03_B | chain F07 + M03_B + M03_A | Retomoto (played) | stock F07 |
|---|---|---|---|---|---|
| command | `kl_maps.py one .. F07 M03_A --campaign` | `.. F07 M03_B --campaign` | `kl_maps.py chain .. F07 M03_B M03_A` | CLAUDE.md, re/retomoto_fa.md 0 | `<s>` one-liner on the stock archive |
| built | ok, 85 s | ok, 77 s | ok, but see chunk table | | |
| entities | 19,675 | 12,764 | 22,873 | 25,490 | |
| rooms | 28 | 17 | 44 | 22 | |
| textures of 4,096 | 1,866 | 1,621 | 2,177 | 2,195 | |
| materials of 2,048 | 1,221 | 881 | 1,356 | 1,429 | |
| .prm chunk-table entries (limit 73,728; tools keep 4,096 free = 69,632) | **64,870** | 49,644 | **79,408: OVER** | 65,119 | 35,102 |
| .prm | 85.7 MB | 51.4 MB (log: '92.9 MB is past 90 MB: 8650 vertex / index chunks that nothing reaches emptied') | 73.5 MB | 74.2 MB | 63.6 MB |
| .TEX | 373.9 MB | 363.0 MB | 442.6 MB | 234 MB after lighten | 281.0 MB |
| .fxc | 17.8 MB | 17.8 MB | 17.8 MB | 16.9 MB | 8.1 MB |
| .ANM | 21.6 MB | 21.6 MB | 21.6 MB | 20.6 MB | 21.6 MB |
| .WAV beside | 22.9 MB | 18.6 MB | - | 25.9 MB | 18.3 MB |
| navigation mesh | 232,480 bytes, converted | 203,412 bytes, converted | 435,836 bytes (`nav_join`) | 603,332 | |
| sounds / waves | 4,724 / 4,586 | 4,597 / 4,454 | 4,752 / 4,606 | 4,941 / 4,766 | |
| dangling scene paths | 0 | 0 | 0 | 0 | |
| stream clips not in the merged PC_Def.str | 1 | 6 (8 names) | 1 | | |
| `kl_fa.check` | 1 CRASH, 9 BROKEN, 4 DEGRADED, 1 NOTE = no layer yet | the same | the same | 0 / 0 / 1 | |
| notes | 'dynamic lists name different classes; kept F07's' | + '.hrd left out: the rigid bodies do not all come from one level' | + the same .hrd note | | |

The 11 'problems' of F07 + M03_A are: 1 x 'sound: 1 stream clips are not in the merged stream file'
(`SFX/Ambiences/M03_A/Inside/Ambience_Inside_Vault_Deeper.wav`) and the ten Fragile Alliance findings every story
level has before a layer exists (settings CRASH; define, exit trigger, START and AFTER_DEATH spawn points, the three
`OnlineGamePlayTrigger` kinds, loot, squads BROKEN). Nothing else: the log's last check line is 'verified: 19675
entities, 19676 nodes, 36483 reachable chunks, 29 room sets, 694 gate / list REF cells, 1866 textures, 1221
materials' (`F07+M03_A campaign/log.txt`).

### 3.2 The finished weight (lighten, then the wardrobe)

MEASURED on a kept build (`.../cfa/bank/keep/`; the archives were deleted afterwards - 0.3 GB each - and the logs
kept: `preflight.txt`, `light/lighten.txt`, `wardrobe/wardrobe.txt`; to have the archive again: `python
tools/kl_maps.py one <work>/build/cfa/bank/keep F07 M03_A --campaign --keep`, 85 s, then step 1):
1. `python tools/kl_graft.py lighten "<keep>/F07+M03_A campaign" "<keep>/light" --load trim,slim` ->
   '.prm 85.7 -> 43.4 MB (8650 dead vertex / index chunks, emptied); .TEX 373.9 -> 183.6 MB (464 of 1866 textures
   only dead materials name, 451 shrunk to 4 x 4)'; archive 310.2 -> 153.1 MB. `python tools/kl_impact.py
   <keep>/light`: problems: 0.
2. `python tools/kl_chars.py wardrobe <keep>/light <keep>/wardrobe` -> '.prm 64870 -> 64870 chunks, 43.4 ->
   59.5 MB'; 'chunk table: 64871 entries (15509 of the base's 24322 dead indices taken, 8813 still free; limit
   69632 of the game's 73728)'; 16 people, problems: 0; archive 178 MB. `kl_impact.py <keep>/wardrobe`: problems: 0.

The five large blocks of a level load (CLAUDE.md 'BUDGET for the builders'), finished map against the others:

| block | campaign bank (lighten + wardrobe) | Retomoto as played | stock F07 | stock F01 |
|---|---|---|---|---|
| .prm | **59.5 MB** | 74.2 MB | 63.6 MB | 66.6 MB (MEASURED; CLAUDE.md says 63.5) |
| .fxc | 17.8 MB (8.9 expected with `--load fxc`: Retomoto's went 16.9 -> 8.9, ASSUMED alike) | 16.9 MB | 8.1 MB | 6.2 MB |
| .ANM | 21.6 MB (F07's own; M03_A adds no clip: '.ANM joined ... clips +0') | 20.6 MB | 21.6 MB | 20.7 MB |
| .WAV | 22.9 MB | 25.9 MB | 18.3 MB | 15.4 MB |
| chunk table | 64,871 | 65,119 | 35,102 | 24,844 |

(corrected by the second agent: the column 'campaign bank (lighten + wardrobe)' is a build with NO enemy. MEASURED
with the 22 squads / 53 actors of 4.1, the three single-node door proxies, the three blast boxes and the two music
objects kept (`python <k>/build_squads.py`, then lighten and wardrobe; section 8.2): .prm 67.8 MB, chunk table
65,640 (8,828 dead indices still free), .ANM 21.9 MB, .TEX 197.3 MB, archive 191 MB, 69 people, problems 0,
`kl_impact` 0. So: under Retomoto on .prm, OVER stock F07's 63.6 MB; the sentence below holds against Retomoto only.)

So the map costs LESS address space than Retomoto on every block that differs. The authored layer adds little:
Retomoto's layer added no entity at all (re/retomoto_fa.md 0), the kept campaign squads add their actors' models
(M03_A's police and guards: part of the 216 pictures / the chunks the pre-pass now leaves dead).

### 3.3 The navigation mesh

MEASURED `python <s>/nav.py M03_A`, `python <s>/navlinks.py M03_A`, `python <s>/stations.py M03_A ...`; preflight line
'nav: kl_pf4.check passes: 79 areas, 902 polygons, 138 waypoints, 14 links; Dead Men links dropped by kind: {1: 14, 6: 2}'.

- kl_pf4 CONVERTS it (186,516 -> 232,480 bytes), nothing refused. Of 30 links 14 are kind 2 (a drop: kept), 14
  kind 1 (the climbs back up: dropped, Dog Days has no such kind) and 2 kind 6 (the rappel, roof (-35 / -152,
  1435, -4560) -> yard (y 200): dropped).
- 30 connected parts by polygon neighbours. By walkable area:

| part | polygons | area | x | y | z | what |
|---|---:|---:|---|---|---|---|
| 0 | 566 | 7,762 m2 | -9603..8575 | **-960..1220** | -14745..-735 | **vault, both stair flights, vault lobby, loading dock, yard, banking hall with gallery, plaza, the whole front street** |
| 5 | 149 | 1,718 m2 | -3465..5603 | 0..800 | -835..2665 | alley and back streets (the Fragile Alliance map's escape side) |
| 9 | 112 | 1,343 m2 | -4395..-555 | 220..1300 | -5745..-660 | car park and its stair tower |
| 2 | 19 | 184 m2 | -1240..1725 | 1430..1435 | -5682..-4560 | bank roof |
| 13 | 1 | 35 m2 | 155..447 | 947 | -8214..-7000 | the flower bed in the hall (6 drop links down to the floor) |
| others | 55 | < 5 m2 each | | | | ledges, window sills |

- **Every station of a lobby -> vault -> front-street round is on part 0** (stations.py: hall centre (377, 801,
  -8423), hall back (295, 802, -6052), foyer (309, 803, -5624), stairs (1538, 355, -5822), vault lobby (394, 241,
  -7129), the three guard posts on the way down, vault door (400, -960, -12640), vault (399, -960, -12818), the
  briefcase place (144, -959, -13277), front door (300, 800, -9350), street (291, 714, -11159), street west
  (-4900, 702, -11750), street east (4477, 712, -11117), also loading dock (266, 202, -5002) and yard (-313, 205,
  -4398)): all 'off the mesh by 0'. Walking distances over polygon centres (an upper estimate): hall centre ->
  briefcase about 190 m; briefcase -> front door about 165 m; front door -> street 23 m; along the street to its
  west end 112 m.
- Part 0 is joined to nothing else by a link that is kept. The kind-2 drops join the alley (5), the car park (9),
  the roof (2) and three ledges into a second group of 283 polygons (navlinks.py: 'kind 2 only ... polygons per
  group [567, 283, ...]'; 567 = part 0 + the flower bed); the only links from that group into part 0 were the two
  rappel links (kind 6, dropped). A round that stays on part 0 needs none of it. A round that ended in the alley
  would need an added drop over the yard wall, as the Fragile Alliance bank did (READ re/bots_bank.md 1).

### 3.4 What this level has that no proven map has

MEASURED `python tools/kl_maps.py first M03_A` (whole map side, `<s>/first_M03_A.txt`), `python <s>/firstkept.py
M03_A` (only what the campaign pre-pass KEEPS, against the four Fragile Alliance maps and the kept parts of M09_A
/ M09_B) and `python tools/kl_maps.py preflight "<keep>/F07+M03_A campaign"` (`preflight.txt` in that folder:
CRASH 2 = the missing layer, RISK 10, NOTE 81).

- After the pre-pass: **no class** that no proven map has. Two controllers: `LightToggle` x 22 (`CLightToggle`, on
  the 11 alarm lamps `Pc0100_M03_LampAlarm_Wall_02..10` of the vault lobby, both stair rooms and the ante-room,
  each an omni + a spot) - registered in kl2.exe, used by NO stock Dog Days level: preflight's one RISK of the
  'first' kind; and one `MatPosAnimProxy` on an air-conditioner lid on the roof (713 in stock Dog Days).
- `kl_maps first` lists 73 more names (ZRoad 20, ZRopeLnkObj 8, WoundedFilter, PsychoticController, RappellingBox,
  DoorCtrl, ...): every one sits in a subtree the pre-pass drops ('in the build: 0' in preflight). They come back
  only for what the authored layer keeps by name (section 5): `MatPosAnimProxy`, `Explode`, `ShakeCamera`,
  `ActivateGeom` / `DeactivateGeom`, `AIDWrapper`, `TriggerDelay`, `TriggerBox`, `ZSquadScript` + behaviour routs
  - all of them kinds Retomoto's layer kept and ran.
- Preflight 'ok' lines: self-delete (no OnlineSpeakTrigger / OnlineMoneyContainer / PhysicsLinkage left), 160 KEYS
  chunks all found by keys_tracks, no controller on a node outside its class, 0 torn stream records, lights
  nothing, **0 of 1,221 materials without a compiled shader** (the Fragile Alliance bank ran live with 35), post
  filter 14 sets inside F07's palette, 28 rooms / 76 gates / 47 neighbour lists followed, .sgd has the three
  sections, no FDX block, no ZEnvSampler.
- Preflight NOTE 'size': 'larger than any Dead Men build that ran live: rooms 28 (ran live: 20), nav_bytes 232480
  (ran live: 186672)' - the note's table predates Retomoto (22 rooms, 603,332 bytes), which loads.

### 3.5 Crash classes of CLAUDE.md this level is exposed to

| class | exposure | basis |
|---|---|---|
| .prm chunk table (0xeac7b0, 73,728) | no: 64,871 with the wardrobe | MEASURED 3.2 |
| .prm heap block (0x8e5bbd) | less than Retomoto: 59.5 MB | MEASURED 3.2 |
| 2 GB address space on later loads | as every map; the five blocks are smaller than Retomoto's | MEASURED 3.2; READ CLAUDE.md 2026-10-10 01:35 |
| settings singleton (0x500990 / 0x728ba3) | until the layer keeps F07's `GameSettings` | MEASURED `kl_fa.check` |
| `JumpPoint` fired by a level object (0x8f40c9) | only if the layer wires one: do not | READ re/retomoto_fa.md 9.4 |
| two cover lists (assert 0x6682c5) | M03_A's `Special!CoverList` (`FFCoverList`) is dropped by the pre-pass; the layer must drop F07's `Specials!CoverPoints!*` as Retomoto's `DROP` does, or keep exactly one | READ re/retomoto_fa.md 9.1; MEASURED `<s>/M03_A.tsv` node 18167 |
| relay naming its own node (stack overflow 0x796ff4) | only through authored wiring | READ CLAUDE.md 'HOT COFFEE GATE BUILD' |
| bone ids (bullet on a person, 0x4c34b3) | kept campaign actors: `kl_impact` must stay at 0 | MEASURED `kl_impact.py`: problems 0 on the trial builds (no actors in them yet) |
| execute crash (human shield, 0x4098a1) | handled by the build ('ZSetZDefine ExecutionBloodSpatter ... renamed') | MEASURED log.txt |
| `ZDefendBehaviourRout` member loop (0x686a66) | open on every map with squads (CLAUDE.md, live night 2026-10-11); not specific | READ |
| missing stream clips | silent, not a crash | MEASURED 1 clip |
| `LightToggle` | unknown: first time in Dog Days | MEASURED 3.4 |
| rooms 28 > 22 | unknown: one more than any map that loaded has (corrected by the second agent: 22 is the most a GRAFTED map has loaded; stock Dog Days levels hold more rooms than 28 - ZROOM nodes F08 35, F09 42, L01 32, L03 61, MEASURED `<k>/facts2.py` - so the engine is not at a limit here, only our own experience is) | MEASURED |

### 3.6 Why the chain (M03_B + M03_A) is out

- MEASURED chain result.json: 'problems' line 1 = '.prm: 79408 chunk-table entries, the game's table has 73728:
  the loader writes 5680 pointers over the globals behind it (kl2 0xeac7b0 + 0x48000; re/prm_limit.md)'. That is
  a LIMIT, not a bug: F07's 35,102 + B's + A's chunks are appended. It could be cured only by a tool change
  (grafting the map into S's dead indices, or `kl_chars.py compact`, which has never been loaded: READ
  re/prm_limit.md 'Not done / open').
- MEASURED `<s>/rooms.py M03_B`, `<s>/share.py M03_B M03_A`: M03_B's city block `M03_B_City_01` (street tiles
  `PC0800_M03B_City_Street_A_*` at y 1..25, e.g. (4300, 25, -4700), (-4798, 1, 0); buildings `City_Building_A_*`)
  stands at x -8600..30100, z -23261..23500 - on top of M03_A's bank (x -6911..6100, z -19396..5815), whose yard is
  at y 200 and whose front street is at y 705. Not one of M03_B's 2,211 placed room objects has a twin at the same
  place in M03_A (85 matches, all outside rooms: backdrop and effect clones). So the two levels are not two halves
  of one world: in one level the chase's street grid would cut through the bank, and a map cannot be moved
  (READ CLAUDE.md, re/havok.md: MOPP codes are world-space).
- MEASURED: all of M03_B's navigation mesh lies at x 36,756..62,799, z 123,654..191,803 - at least 1.3 km from the
  bank; 0 links; the largest part has 215 polygons (the subway). Between the bank and that there is no ground to
  walk: the chapter is a ride in the van.
- A 'street escape' needs no second level: M03_A's own front street is 180 m long and holds the campaign's whole
  police assault and the getaway van's arrival (1.3 rows 13, 14).

## 4. The round

### 4.1 What the level offers a round

- **Squads that can stay.** MEASURED `python <s>/squads.py M03_A` (`tools/kl_fa_author.squad_plan`'s rule copied into a
  scratch script so that it can be asked of this level: a squad stays when its subtree holds only plain squad
  objects, at least one actor and one behaviour rout; mini-cutscene controllers are stripped). 76 squad subtrees,
  113 actors; **22 squads with 53 actors stay** (Retomoto: 33 / 63):

  | area | squads (actors) | kinds and Dead Men weapons | where |
  |---|---|---|---|
  | the way down | `GamePlay!4_Vault_Part!Guards_01` (2), `Guards_02` (2), `Guards_03` (2) | eGuard, amateur / regular, `HG_HK_USP_01` | (-122..-18, -158, -9265..-9145); (-98..-52, -559, -10673..-10548); (326..719, -959, -11889..-11725) |
  | loading dock + vault lobby | `3_Garage_Part!PatrolGuards_01a` (2); `4_Vault_Part!Guards_Reinforcement_StayUpstairs` (4), `#01` (3), `Guards_Reinforcement_01a` (2), `01b` (2), `Police_Reinforcement_02` (2), `_03` (4), `Police_Reinforcement_Teargas_01` (1), `#01` (1), `Vault_Reinforcement_Police_01` (2), `_02` (2), `_03` (2) = 12 squads, 27 men | eGuard, amateur / regular; pistols and `Smg_MP5-A3_01`; Defend and Hunt routs | y 201..243, x -901..834, z -7490..-5008 |
  | plaza and street | `5_Lobby!Police_Outside_Teargas_01` (4 veterans), `Police_OutSide_01` (4); `COOP!Squads_Lobby!Police_OutSide_SWAT_02` (4), `_SWAT_03` (4) (eArmy, veteran, `Rifle_M4A1_01`), `_SWAT_02_ShieldSupport` (1), `_SWAT_03_ShieldSupport` (1), `Police_Reinforce_Wave1_COOP_03` (2) = 7 squads, 20 men | Flanking and Defend routs | (1968..2201, 704..706, -9620..-9418) east; (-2269..-1415, 704..711, -9686..-9397) west |

  Do not stay under that rule: the six police-car squads `Police_Reinforce_Wave1_COOP_01/02`, `Wave2_01..04` (16
  actors; `ZHavokCar` + `HavokCarScriptRout` + `VehicleMoveOnRoadBehaviourRout`), `Police_OutSide_SWAT_01_Shield` (4
  `eSwatWithShield`; a car and `AttachGeomToBone`), `Chopper01/02` (`ZHeli` + `HeliWeapon`), `Sniper_OutSide_01` (2,
  no rout), the eight hall guards `GuardSquadForCutSeq` / `_COOP` (`Smg_FN_P90_01`, no rout), the car-park patrols
  (`WarnBehaviourRout`), the armoured car, 22 civilians (`ZCivilian`), and every `ZMercSquad` / `ZFusionSquad` (the
  story's own crew: Lynch, the vault breaker, the driver).
- **Doors on the way** (MEASURED `python <s>/proxies.py M03_A`; all are `MatPosAnim` objects of the MAP, kept by the
  pre-pass; what opens them is campaign script, dropped):

  | door | object (place) | the campaign opens it by |
  |---|---|---|
  | loading dock roller door | `M03_A_Garage_01a\SI0201_M03_BackDorAnim_01` (560, 550, -4706) | `GamePlay!2_Secure_Parking!AnimProxy_Garage_Open`, frames 1..150 (top-level single node) |
  | glass door, dock side | `M03_A_VaultLobby_01a\SI0103_M03_BankVault_GlassDoor_01` (0, 240, -6820) | `...MercSquad_VB_OpenGlassdoor\FirstGlassDoors_Open`, 0..50 (inside a `ZMercSquad`) |
  | glass door to the vault stairs | `...\SI0103_M03_BankVault_GlassDoor_02` (399, 240, -7614) | `...MercSqd_VB_Lynch\SecondGlassDoors_Open`, 0..36 (inside a `ZMercSquad`) |
  | airlock to the hall's stairs | `...\SI0103_M03_BankVault_DDorSlide_01..04` (1000 / 1215, 240, -7105 / -6895) | `GamePlay!4_Vault_Part!SlideDoors_Open`, 1..30 (top-level single node) |
  | hall <-> foyer | `M03_A_VaultLobbyFoyer_01a\SI0103_M03_BankVault_DDorSlide_01/02` | `GamePlay!5_Lobby!LobbySlidedoors!BankLobby_Slidingdoors_DoorCtrl` (299, 936, -5802): `DoorCtrl`, a class no stock Dog Days level uses |
  | six locking rods | `M03_A_VaultEntrance_01a\Rod_A01..F01` + `RodLight_A01..F01` | `...MercSqd_Valutbreaker_OpenVault\MatPosAnimProxy_Rod#01..#06`, 1..60 (inside a `ZMercSquad`) |
  | **the vault door** | `M03_A_VaultEntrance_01a\SI0102_M03_BankVault_Door_PRE_01` (group origin (571, -760, -12510); the opening at (400, -960, -12640)) | `GamePlay!4_Vault_Part!VaultDoors_Open`, 1..75 (top-level single node) |

  Not on the way: the dock's second bay `M03_A_Outside_01A\SI0201_M03_BackDorAnim_01` (40, 550, -4706) (no proxy
  names it and the mesh does not pass it) and two more glass doors at the ends of the cross corridor,
  `M03_A_VaultStairs_02a\SI0103_M03_BankVault_GlassDoor_01` (-215, -565, -10600) and `..._02` (990, -565, -10600).
  Every one of these objects is in the BUILT level with its `MatPosAnim` (MEASURED `python <s>/built_doors.py
  <keep>/light/F01_Main.zip`: 160 `MatPosAnim`, 22 `LightToggle`, 45 `PlayerCoverCollision`, 47 `NoCoverBox`, 3
  `LevelBound`, 0 `DoorCtrl`, 0 `ZFFActor`, 0 `ZSpawnPoint`).

- **The vault at load**: `Vault_01a\Vault_PRE` is shown (ZGEOM[3] = 0), `Vault_01a\Vault_POST` and the fire groups
  `Bank_Vault_Fire01\Vault_Fire_Big00 / _Small00` are hidden (ZGEOM[3] = 1) - MEASURED `python <s>/node.py M03_A 9358
  9469 9340`. So without any script the level shows the intact vault.
- **Can the vault script run for a Fragile Alliance player?** The campaign's sequence itself cannot: every step is
  a `MiniCutsceneRout` of a `ZMercSquad` whose actor is the story's vault breaker ('Merc_01'), with
  `MiniCutItemProxy`, `WoundedFilter`, `ActorMonitor` (MEASURED `<s>/t_vault.txt`), and a Fragile Alliance player has
  no story crew (READ re/retomoto_fa.md 9.4: `ZFFPlayer` slot 82 creates the crew object only for player types 0
  and 1). But what the sequence FIRES is plain: `MatPosAnimProxy` (doors, rods), `Explode` + `ShakeCamera` (the
  three `BoomBox_BlowVault`), `AIDWrapper` 'Activate' (sound), `ActivateGeom` / `DeactivateGeom` (PRE -> POST, fire),
  `TriggerDelay` - the kinds Retomoto's layer fires from the round-start event and from trigger boxes, and the
  owner has seen that blast work (READ CLAUDE.md 2026-10-09 22:00 'blast and shake amazing', re/retomoto_fa.md 6).
  So the vault can be opened and blown by timers and boxes; nobody 'hacks' it. NOT established live: whether a
  Dead Men `MatPosAnim` door moves in Dog Days when its proxy is named (section 6).
  (corrected by the second agent: there IS a live hint, and the proxies are not the only way. MEASURED `python
  <k>/w2.py M03_A node 6114` against `M03_FA_A node 3448`: the dock's roller door is the SAME object in both levels -
  same name, same place (560, 550, -4706), the same `MatPosAnim` values ('Activate', frames 1..150) - and the
  Fragile Alliance bank opens it by a plain 'Activate' sent to the door itself (READ re/escape.md 1, row
  `Triggers!GarageDoors!TriggerBox`). The owner saw that door open in Dog Days (READ CLAUDE.md 2026-10-10 ~21:40
  'once the garage door comes open'; re/map_escape.md 19.6 calls it the one live hint); in a solo scripted run it
  stayed shut (READ re/escape.md 4.2, run RN10: 'the doors were shut'), and that a shut key-framed door holds a
  player is seen on Retomoto's tower car (READ re/retomoto_fa.md 10.1, run J1: stopped at x 2727 for 15 s of
  pushing). Every door of the route has such a `MatPosAnim` of its own with
  the in-message 'Activate' (vault door frames 0..200, the six `DDorSlide` leaves 0..30, the glass doors through
  their own group's `RelayMessageList` 'Activate' -> both leaves, the rods): section 8.3.)
  *(corrected after the critic: the glass doors' own 'Activate' plays their whole there-and-back clip - open, then shut
  again four seconds later; re/campaign_fa.md, 'Gap closed: the route without a run-time event', G1.8.)*
- **The designers' road for the getaway van** (MEASURED `python <s>/splines.py M03_A 11637 11641`):
  in (the campaign van REVERSES up it, 64 m): (-3248, 710, -11859) -> (-1917, 712, -12126) -> (-231, 707, -12332) ->
  (132, 707, -11726) -> (159, 703, -11102) -> (318, 709, -10516) -> (338, 802, -9078) = up the plaza steps and into
  the hall's front; away (49 m): (299, 803, -9493) -> (299, 706, -9990) -> (402, 704, -10584) -> (949, 704, -11105)
  -> (2473, 705, -11177) -> (3958, 713, -11173). Police cars use the same square: e.g. `Wave2_02` (4163, 717, -11152)
  -> (946, 707, -11725), `Wave1_COOP_01` (4528, 709, -9600) -> (858, 706, -10586).
- **Loot props that fit the place**, all in `Vault_01a\Vault_PRE` (MEASURED `<s>/M03_A.tsv`): six deposit-box walls
  `SI0102_M03_BankVault_Wall2mBOXES_PRE_01..06` at (600 / 400 / 200, -960, -13410) and (0, -960, -13230 / -13030 /
  -12830), box blocks `BoxA_PRE_06..11h`, `BoxB_PRE_01`, the trolley `PC0600_M03_VaultTrolley_01` (199, -960, -13171)
  with five cartons, `PC0600_M03_Boxes_PRE_01` (859, -960, -13299); behind bars (`Bar1m / 2m / 4m_PRE` at x 800):
  `PC0600_M03_Statue_01` (966, -960, -12933), `PC0600_M03_PaintingRack_01` (789, -960, -12802), six paintings. The
  campaign's own prize is a briefcase (`MissionObjective_020_Suitcase` (144, -959, -13277)). The hall has teller
  counters `Pc0100_M03_Bankcounter_A_*` at x -791 (z -7202, -7602, -8002) - the row the Fragile Alliance map puts its
  cash drawers behind ((-808, 875, -8320), (-808, 875, -7120), (1411, 875, -8138), (1411, 875, -7338)).
  Money props that exist (READ re/retomoto_loot.md 3): Dead Men's own Fragile Alliance briefcase
  (`M01_FA_A DropMoney!KillDrop!Suitcase`, brought into the Retomoto build by `tools/kl_fa_loot.py`), F07's pool bag
  (model 1802), M03_FA_A's money box `PC0500_M03_MoneyBox_*` (an animated container, not in M03_A).
- **Music** (MEASURED `python <s>/music.py M03_A`; `python tools/kl_str.py list "<DM>/PC_Def.str" Music/`):
  `Special!Audio!PlayMusic_Outside` = four layers `levelsetup/level/m03_a/music/bo_sus_layer1_ambient_loop`,
  `_layer2_bass_loop`, `_layer3_intense_loop`, `_layer4_basic_loop` (stream set `LevelSetup/Level/M03_A/Music/BO_Sus_LOOP`,
  144.0 s, clips `Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav` .. `Layer4_Basic_LOOP.wav`, 36.9 MB; a second
  set `BO_Sus_LOOP2`, 56.0 s, 14.3 MB) with 41 `PlayMusicLayerFade` steps - the break-in;
  `Special!Audio!PlayMusic_Inside_Part2` = `levelsetup/level/m03_a/music/m03a_bustout_actionv34` +
  `m03a_bustout_intenseclimax_loop` (set `LevelSetup/Level/M03_A/Music/M03A_Bustout_A_I`, 168.0 s, clips
  `Music/InHouse/M03A/M03_Bustout_ActionV34.wav`, `M03_Bustout_IntenseClimax_Loop.wav`, 21.5 MB) - the way out.
  M03_B: `LevelSetup/Level/M03_B/Music/M03B_Loop_layers` (`M03B_Prison_Amb_Loop`, `M03B_Subway_Fight_Combat_Loop`).
- **Voice lines** in the level's bank (MEASURED scratch one-off over `kl_snd.bank('M03_A')`: 330 objects under
  `audio:dialog/m03/`): the vault breaker's six 'rod' calls `Dialog/M03/Dialogue/Situation/M03_OpenVaultX6/
  M03_OpenVaultX6_010..060_Vaultbreaker` (one per rod: the bank's own countdown, as Kane's is on Retomoto),
  `M03_BlowVault_010 / 030 / 061 / 090_Vaultbreaker`, `_020 / 050 / 070_Hero` (Kane), `_060 / 080_Lynch`,
  `M03a_OneLiners/M03_Alarm/M03_Alarm_010_Hero`, `M03_VaultShot_010..030_Vaultbreaker`, guards'
  `M03_GuardAlarm_010 / 030 / 040_Guard02`; sounds `levelsetup/level/m03_a/sfx/alarms/alarm_003`, `alarm_buzzer`,
  `levelsetup/all/environment/beeps/bankalarm_beeps/bank_alarm_beep_01..04`.

### 4.2 Three candidate rounds

**A. 'Over the roof, out the front' - the campaign's own order from the rappel on.**
Start in the secure yard under the bank's back wall, where the campaign's ropes come down; in through the loading
dock; down to the vault; the rods, the door, the loot; alarm; up the other stairs into the banking hall; police on
the plaza; the van on the street in front. Yard -> briefcase 147 m, briefcase -> van stop about 200 m (MEASURED
`<s>/stations.py`, polygon-centre paths: upper estimates). Start and escape are at opposite ends of the building
and the vault is the turning point in the middle.

**B. 'Lobby first' - the briefing's order ('Pacify the lobby, get to the vaults').**
Start inside the banking hall, down behind the sliding doors to the vault lobby, the vault, back up the same
stairs, out by the front, the same van. Hall centre -> briefcase about 190 m, back out about 190 m. Shorter to
author (no yard, no dock, one stair), but the way out is the way in, the escape is 20 m from the start, and the
hall + plaza half is where the Fragile Alliance map also starts.

**C. 'Withdrawal with a vault' - a variant of the map the owner has.**
START, entry, exit, van and bounds at M03_FA_A's own coordinates (they are valid here: same world, 1.4), the loot
moved from the loading dock down into the vault. Cheapest in decisions - the alley van, its lane and the yard wall
are known from the played map - but two thirds of the round are the round the owner already has, M03_A lacks the
enlarged dock and the money boxes, and the AI heisters would again need the drop link over the yard wall that
`kl_fa_bots.add_drop` had to add (READ re/bots_bank.md 1).

### 4.3 Recommendation: A

| | the round | basis |
|---|---|---|
| **start** | 8 START points in two stacks left and right of the dock door, about (150..450, 200, -4350) and (700..1000, 200, -4350), facing -z at the door; 4 TRAITOR points behind them about (300..1000, 200, -4000). 'In the middle of the action': the ropes are down the wall behind them (the campaign's rappel ends at (-35, 200, -4525) and (-151, 200, -4525)), the round-start event rolls the dock door up and wakes the dock's guards | places GUESS, on MEASURED mesh (`python <s>/grid.py M03_A -2600 3600 -7000 -500 100 100 420`: the yard is part 0, x -400..2400, z -4500..-800, y 200; the door gap x 400..700, z -4700..-4600) |
| **first fight** | dock and vault lobby: `PatrolGuards_01a`, the two `Guards_Reinforcement_StayUpstairs` squads and `Guards_Reinforcement_01a/01b` (13 men) started at the round start; small loot on the way: 2 stacks in the vault lobby / control room | squads MEASURED 4.1; loot places GUESS |
| **the way down** | glass door 2 open; `Guards_01`, `Guards_02`, `Guards_03` (6) at their own posts on the two flights and in the ante-room | MEASURED 4.1 |
| **the beat** | a trigger box in the ante-room at the campaign's own `TB_VbByVault` (460, -714, -12152) starts the vault: rod 1 .. rod 6 at 8 s steps (GUESS) with the rod lamps going out and the rods' own sounds, the vault breaker's six calls if the talk hook carries them; meanwhile the three `Vault_Reinforcement_Police` squads and `Police_Reinforcement_02 / _03 / Teargas` (14 men) come down the stairs behind the crew - the crew holds a dead end; then the door swings (75 frames; 3 s if a Dead Men door plays at the 25 frames a second of F07's van keys, re/map_escape.md 9.3: ASSUMED), the alarm lamps and the alarm sound start, the music changes to the bust-out theme, the loot appears | objects MEASURED 4.1; timing and wiring GUESS; the loot is hidden until then (ZGEOM[3] = 1 + flag 0x400, `ActivateGeom`): the gate Retomoto's boardroom table has (READ re/retomoto_fa.md 2), so the round works even if the door's collision does not hold a player |
| **loot** | vault: 6 briefcases at the deposit-box walls, about (200 / 400 / 600, -960, -13330) and (90, -960, -13230 / -13030 / -12830), 300,000 each, + 1 on the trolley (199, -890, -13171); optional second helping 15 s after the first take: the campaign's own blast (`Timer_to15secs` -> the three `BoomBox_BlowVault`, `Vault_PRE` -> `Vault_POST`, fire) opens the barred art store, 2 stacks at the statue and the painting rack; hall: 4 stacks at the teller counters on the way out, 75,000 each. About 2.6 M (F07: 4.0 M; Retomoto 4.05 M) | props MEASURED 4.1; every place and value GUESS; reach to be tested with `kl_fa_loot.py survey` (the west teller place is 150 off the mesh: MEASURED stations.py) |
| **enemies after the beat** | hall: none of the campaign's can stay (4.1) - F07's own squads re-placed, or the eight hall guards given a rout (authoring); plaza: the seven front squads (20: two SWAT fours with M4s, the tear-gas four, the patrol four ...) started when a criminal comes up into the foyer; police who return (AFTER_DEATH) on the street at the campaign police's own places, 4 west (-1842..-1437, 705, -9621..-9542), 3 east (2016..2178, 706, -9598..-9418). Police arrive from both ends of the street; the campaign's car arrivals (6 squads) are an option, not the base | MEASURED 4.1; READ re/map_ai.md (Dead Men spline police cars run in the played maps but lose their exit rout in conversion) |
| **escape** | F07's key-framed van (the one on Hot Coffee, Late Night Opening, the bank and Retomoto) laid on the designers' road: waits at (-3248, 710, -11859) west of the campaign's right bound, drives in east along the street, stops in front of the plaza steps about (250, 707, -10700), boarding at its rear; drives away east along (949, 704, -11105) -> (2473, 705, -11177) -> (3958, 713, -11173) and on. Exit trigger: a box over the plaza and the street in front of the doors, about centre (300, 800, -10300) half (1500, 300, 900). **Corrected by the second agent: this stop does not work as written.** The designers' IN road is driven in REVERSE (MEASURED `<k>/spl2.py M03_A 11643`: `VehicleMoveOnRoadBehaviourRout` field 6 = 'REVERSE', speed 35; the AWAY road 'FORWARD', 60) right up to the hall's front at y 802, so that the campaign van leaves nose first. F07's van is laid nose first along ONE curve with its heading = the direction of travel (READ tools/kl_map_escape.py `van_plan`: `curve(pin + ahead)`, re/map_escape.md 10.2): at (250, 707, -10700) it would stand nose to the bank with its boarding box on the STREET side, and from there to the first away point (949, 704, -11105) the heading turns from 15 to 134 degrees within 8 m - a pivot on the spot. A lane without that exists (MEASURED `<k>/lane2.py M03_A`, five rays across 220 every 20 units, dropped campaign cars left out): IN road as far as (-231, 707, -12332), straight to (949, 704, -11105), then the AWAY road = 77 m, clear but for the edge of one planter (`S00701_M03_Square_DirtB_04`, 21 m along); the AWAY road from (402, 704, -10584) on is clear on all 935 ray places. So: stop where that leg meets the AWAY road, about (850..950, 704, -11200..-11105) (GUESS), nose north-east to east, about 8 m from the foot of the plaza steps at (402, 704, -10584) - or teach the tool a reversed in-leg (new code) | road MEASURED 4.1; stop, box and the lane beyond x 3958 GUESS - `kl_map_escape.van_plan`'s lane test (rays against the collision every 20 units) is what proves a lane; the van itself READ re/map_escape.md 8 - 10 |
| **level bounds** | front: the campaign's own three, kept by the pre-pass (`LevelBound_Outside_Front` (355, 943, -14140), `_Left` (3763, 843, -10211), `_Right` (-2837, 928, -10916)); back: F07's bound boxes re-placed along the yard's north wall (z about -700) and its east fence (x about 2400; `SO0301_USA_animFence_01_01/02` at (2386, 303..399, -4980 / -3590)) so that nobody leaves by the alley | front MEASURED; back GUESS |
| **music** | `BO_Sus_LOOP` from the round start (`Special!Audio!PlayMusic_Outside`), `M03A_Bustout_A_I` from the vault door on (`Special!Audio!PlayMusic_Inside_Part2`), both kept and sent 'AITrigger' the way Retomoto's `Music!PlayMusic_TokyoAction` is; the stream sets (36.9 + 21.5 MB, optionally 14.3) appended to PC_Def.str by `kl_str.py build --extend` after `kl_str.MUSIC` gets an 'M03_A' entry | names MEASURED 4.1; the method READ tools/kl_str.py (`MUSIC`, `music_roots`), re/retomoto_fa.md 6; that Retomoto's music plays: READ CLAUDE.md (owner, 2026-10-09 17:35) |
| **AI heisters** | stations, all on mesh part 0 (MEASURED stations.py, every one 'off the mesh by 0'): START (300, 200, -4350) -> dock door (550, 200, -4650) -> dock (266, 202, -5002) -> vault lobby (394, 241, -7129) -> glass door 2 (399, 240, -7614) -> upper flight (-70, -158, -9200) -> cross corridor (-75, -558, -10600) -> ante-room (400, -959, -11800) [hold until the door] -> vault door (400, -960, -12640) -> vault (399, -960, -12818) [loot] -> back to the vault lobby -> airlock (1100, 240, -7000) -> stairs (1538, 355, -5822) -> foyer (309, 803, -5624) -> hall back (295, 802, -6052) -> hall centre (377, 801, -8423) -> front door (300, 800, -9350) -> plaza (281, 812, -9700) -> van stop (250, 707, -10700). One mesh part, no link: the standard `kl_fa_bots.py build` + `kl_fa_bots_dyn.py` path, no hop and no hook part | MEASURED 3.3; READ re/bots.md 2.2 |

**What makes it worth having next to 'Withdrawal'.** The Fragile Alliance map runs front -> hall -> dock -> yard ->
alley and never goes below y 200. This one runs the other way through the building and 12 m deeper: yard -> dock ->
vault (y -960) -> hall -> plaza -> street. The two share the hall and the vault-lobby level but no start, no loot
place, no escape and no vehicle lane; the vault complex (0 % shared, 1.4), the rods-and-door hold-out in a dead
end, the alarm and the police assault on the plaza with the van in front exist only here; and it has the level's
music, which the Fragile Alliance map never plays (its settings field 157 is 0 like every stock level's: READ
tools/kl_str.py `set_fa_music`).
(corrected by the second agent: 'no start, no loot place, no escape' is too strong. MEASURED `python <k>/overlap.py`:
of the 284 m the route is long over the mesh, 137 m (48 %) lie on ground M03_FA_A's own mesh also has - yard, dock,
the lobby level, the airlock stairs, foyer, hall, plaza - and 147 m (the way down from glass door 2, the vault, and
back) exist only here. The START is the yard in which the Fragile Alliance round ENDS its bank part, the van stop is
15 - 25 m from the Fragile Alliance START row on the plaza, and the four hall stacks of 4.3 stand at the Fragile
Alliance map's own cash-drawer row. Fair wording: the same house walked the other way round, half of the walking in
rooms the owner knows, the other half - and the beat, the loot and the music - new.)

## 5. What has to be authored

Kinds from `tools/kl_fa_author.py` (PLACE, ROLE, KEEP, CAMPAIGN_KEEP, SPAWN) and re/fa_gamemode.md 3; 'host' = a stock
F07 object kept by name, re-placed and re-wired (MEASURED pool: `python <s>/hostparts.py F07`).

| needed | where it comes from | does the level hold it? |
|---|---|---|
| settings, `IsMultiplayerLevel`, speakers, briefing, `AIMonitor`, escape monitor | host (`kl_fa.host_keep`) | no (0 in M03_A) |
| 8 START, 4 TRAITOR, 7 AFTER_DEATH (+ UCC, team and team-police sets), 16 player groups, spawn cameras | host: F07 has 8 / 4 / 7 and the other modes' sets | no; places from this note (yard, street) |
| ENTERS_BANK / EXITS_BANK planes, the two `PointOfInterest`, their trigger boxes | host `FASpecials!PIP!*`, `FASpecials!POI!*` (2 + 2 single nodes) | no; ENTERS at the dock door, EXITS at the hall's front doors (303, 974, -9407) = M03_FA_A's own enter plane (MEASURED) |
| loot (about 13 objects) + the drop pool | host pool stacks (133 single `OnlineMoneyCtrl` nodes) | no money object; the props are there (4.1) |
| loot gate ('appears when the door is open'), counter | host `ActivateGeom` (2 single), `DeactivateGeom` (3), `TriggerCounter` (2) | - |
| round-start chain, the beat's timers, the trigger boxes (ante-room, foyer) | host `TriggerDelay2` (25 single), `TriggerBox` (13 single), `AIDWrapper` (10 single) | the campaign's own are inside dropped subtrees |
| door openers | campaign single nodes kept by name: `GamePlay!2_Secure_Parking!AnimProxy_Garage_Open`, `GamePlay!4_Vault_Part!SlideDoors_Open`, `GamePlay!4_Vault_Part!VaultDoors_Open`; the host has ONE single `MatPosAnimProxy` | yes for dock door, airlock and vault door. The two glass doors, the six rods and the hall's `DoorCtrl` doors have no single-node opener: either the proxies inside `MercSqd_Valutbreaker_OpenVault` (77 nodes), `MercSquad_VB_OpenGlassdoor`, `MercSqd_VB_Lynch` are kept as husks (every other controller of the subtree taken off before the join, as `kl_fa_author.strip` takes the mini-cutscene ones off squads), or those doors are hidden at load / by `DeactivateGeom`. (Corrected by the second agent: a third way needs neither. Every door object of the route is map geometry that stays, with a `MatPosAnim` of its own whose in-message is 'Activate' and, where the range is stored, its own frames - dock door 1..150, vault door 0..200, the four airlock leaves and the two hall / foyer leaves 0..30; the two glass doors are groups with a `RelayMessageList` 'Activate' -> 'Activate' to their two leaves; the rods and glass leaves store -1 / -1 (MEASURED `<k>/w2.py M03_A node 6114 9617 9506 10345 10204 9654`). A host relay or timer that sends 'Activate' to the door (or the glass door's group) is how the Fragile Alliance bank opens the same roller door. ASSUMED: -1 / -1 plays the whole clip; not read in code. So no husk keep is needed for a first build) |
| the vault blast | campaign single nodes `GamePlay!4_Vault_Part!BoomBox_BlowVault#01..#03` (`Explode`, `ShakeCamera`), `Locations/M03_A/M03A_Audio.zip!Audio!3D!Sound_VaultExplosion` (kept already); PRE / POST / fire lists written into a host `ActivateGeom` + `DeactivateGeom` | yes (the objects), wiring authored |
| enemies | the 22 campaign squads of 4.1 kept by name and stripped; starters = their lowest-named rout; weapons by `kl_arms` | yes |
| hall defenders, police waves | host squads re-placed (as `kl_fa_street` did; F07 has 29 `ZSquadScript` subtrees), or a rout for the eight hall guards | partly |
| exit trigger + van + boarding + escape cameras | host `Gameplay!EscapeSetup!otrExitLevel`, `Animation/F07/F07_Escape_Vehicle_01.zip`; the van's keys re-laid on the road of 4.1 (`kl_map_escape.van_prepare`'s method; it reads its road from an `OnlineEscHavokCar`, which M03_A has not: the road has to be handed to it as points) | the road yes (two `ZEditorSpline`), no escape object |
| level bounds at the back | host `Specials!LevelBound!*` (6 single bounds + warn boxes) | front: yes, 3 kept |
| cover | the map's 45 `PlayerCoverCollision` + 47 `NoCoverBox` are kept; F07's `Specials!CoverPoints!*` dropped | yes |
| music | `Special!Audio!PlayMusic_Outside` (a subtree of 42 with its `PlayMusicLayerFade` children), `PlayMusic_Inside_Part2` kept by name | yes |
| alarm | the 11 lamp pairs with `LightToggle` are in the map; `Special!Audio!GeomActivator_PlaysoundAlarm` (single node) | yes |
| AI heisters | `kl_fa_bots.py build`, then `kl_fa_bots_dyn.py` | - |
| loot dress (briefcases), talk lines, wardrobe, lighten | `kl_fa_loot.py`, `kl_fa_talk.py`, `kl_chars.py wardrobe`, `kl_graft.py lighten` | wardrobe and lighten MEASURED 3.2 |

**Size of the work: about 0.5 of Retomoto.** Less than Retomoto because: one level instead of a chain (no `nav_join`,
no third static Havok part, the .hrd is carried); no join and no hook part (kljoin.c / klcrew_rt.c have no
counterpart); the route is one mesh part; half of the coordinates are MEASURED (the campaign's own markers and
M03_FA_A's layer in the same world) where Retomoto's were guesses; lighten, wardrobe, van, bots, guns and loot
tools exist and have run on the sibling map; every block is under Retomoto's. Not less than half because: seven
door sets and a timed vault sequence have to be wired and SEEN (Retomoto had one blast and two doors); the husk
keep is a new use of `strip`; 22 squads have to be staged in three areas; the hall needs defenders that no
campaign squad supplies; the van's road has to be given to `kl_map_escape` in a new form; and kl_graft /
kl_maps import their authoring hooks from the module `kl_fa_author` by name (READ tools/kl_graft.py line 1076,
tools/kl_maps.py line 440), so a second authored map needs either the outside patches Retomoto's first builds
used (READ re/retomoto_fa.md 7) or a small generalisation of those two files (other sessions' files).

**Order of steps to a first load**
1. `kl_maps.py one <out> F07 M03_A --campaign --heroes --keep` with a `HERO_AT` entry for M03_A (the campaign's
   `Special!Checkpointsave!CP_03_PosP1` (394, 241, -7129) / `CP_03_PosP2` (297, 800, -6120); needs one line in
   kl_maps or the same patch from outside) -> lighten -> direct boot: the level without enemies, the player in the
   vault lobby. Shows the load, the doors' load-time state, `LightToggle`, the 28 rooms, the walk to the vault
   door and to the street.
2. A new module on kl_fa_author's pattern (say `kl_fa_bank.py`): KEEP = F07's `FASpecials!`, `Specials!`,
   `Gameplay!EscapeSetup!*`, van 1; PLACE / SPAWN tables from 4.3; CAMPAIGN_KEEP = the single nodes of the table
   above; DROP F07's cover points. Build, `kl_fa.check` to 0 CRASH / 0 BROKEN. Second direct boot + a first Arcade
   round with no squads (`--no-ai`): start in the yard, doors (opened at the round start), loot, exit box.
3. The van on the designers' road; `kl_map_escape.py van-check`.
4. The beat: ante-room box -> rods -> door -> loot gate -> alarm -> music; then the optional blast.
5. Squads in three stages; `kl_arms`; `kl_impact`.
6. lighten -> wardrobe -> `kl_fa_bots.py build` -> `kl_fa_bots_dyn.py` -> guns / tune -> audit; music clips into
   the stream file; the sixth slot of the tab.

## 6. Risks, and what only a live run can settle

1. **Do the doors move?** Whether a converted Dead Men `MatPosAnim` object plays its KEYS chunk when a kept
   `MatPosAnimProxy` names it has not been seen in Dog Days: READ CLAUDE.md 2026-10-10 21:28 ('ASSUMPTIONS: Dog
   Days plays the Dead Men KEYS chunk'), 2026-10-11 (run G_DM01: 'the fence was not in the picture'). Offline the
   build is sound (preflight: 160 KEYS chunks, every one found). If they do not move: the door leaves are hidden at
   load or switched off by `DeactivateGeom` (a static piece switched off this way lets the player through: the
   Retomoto window, seen by the owner) and the beat is lamps, sound and the loot gate only.
   (corrected by the second agent: 'has not been seen' is wrong for the first door of the round. The dock's roller
   door is the very object the Fragile Alliance bank has (same name, place and `MatPosAnim` values) and the owner
   saw it open in Dog Days - sources in 4.1. What stays unseen is a
   `MatPosAnimProxy` driving a Dead Men door; a direct 'Activate' avoids the question. And the consequence nobody
   wrote down: the round STARTS behind that door. MEASURED `python <k>/walk6.py M03_A` and `walk8.py` on the built
   level: with the doors where the file has them the collision lets the crew reach nothing but the yard. If the
   door does not open at the round start, and a shut key-framed leaf holds a player here as Retomoto's tower car
   doors do, eight heisters stand in a closed yard - so the door's opening is the first thing a live run must
   show, before any other beat is worth wiring.)
2. **Do the closed doors hold a player?** Mixed evidence for key-framed leaves: Retomoto's tower car doors stop the
   player, its boardroom door does not (READ re/retomoto_fa.md 9.2, 10.1). The round does not depend on it (the loot
   is gated), the look of it does.
3. `LightToggle` on the 22 alarm lights: code no stock Dog Days level runs (MEASURED 3.4). If it faults at load:
   take the controller off those lights before the join.
4. 28 rooms, 902 polygons in 30 parts, 19,675 entities: entities and polygons within what has loaded (Retomoto:
   25,490 entities, 2,241 polygons), the room count beyond it (22).
5. The vault's `Explode` boxes next to players: values 1300 / 1000 / 1800 on `#01`, 800 / 800 / 800 on the others
   (MEASURED `<s>/t_vault.txt`; which of them is the lethal radius: READ re/retomoto_fa.md 6, not established); in a
   11 x 9 m room that is the whole room. Either the blast is made harmless (Retomoto's `BLAST_HARMLESS`: the two
   first values set to 1) or it is the reason to leave the vault within 15 s - a decision for the owner, and its
   damage has to be seen.
6. The hidden `Vault_POST` / fire groups: that `ActivateGeom` on a list of 20-odd Dead Men nodes (two
   `ZENVIRONMENT` lights among them) behaves; Retomoto's swaps had four lists and worked.
7. The van: the lane on the square (police cars, planters, the steps), the bound at x 3763 with players aboard
   (READ re/map_escape.md 10.4: the played bank van passes a bound 16 m after its stop), the stop's height.
8. The AI heisters in a dead end behind a gated door (a hold step before the vault), and on stairs (Retomoto's
   stairs were narrow for them: READ re/bots_retomoto.md 1).
9. The death of all seven bots that the Retomoto boardroom shows (CLAUDE.md, live night 2026-10-11, cause open) may
   repeat in the vault ante-room, which is as much of a kill box.
10. Kept campaign actors: their models, the skeleton rebind and bone ids (`kl_impact` must stay at 0), weapons
    (`kl_arms`), voices (the guards' lines are English here, unlike Retomoto's Japanese ones).
11. The one free slot of the 'Dead Men maps' page: this map and the other campaign candidates compete for it.
12. Stream file: +58 MB of music; installing a new PC_Def.str is the owner's call each time.
13. Online: every machine needs the identical build (READ CLAUDE.md, re/netcode.md); nothing here adds a hook part.

Only the game can settle: 1, 2, 3, 5, 6, 7 (the lane test is offline, the drive is not), 8, 9, and by ear the
music and the alarm.

## 7. Verdict

**ready-to-author.** The bank's campaign level goes through the existing graft today with nothing wrong but the
missing game layer, it weighs less than Retomoto once lightened and dressed, and the whole heist the campaign
tells - in from the yard, down to the vault, a hold-out while the door opens, up into the banking hall and out to
a van in the street - lies on one connected piece of walkable ground, so the seven AI heisters can walk it without
any trick. It is the same building as the 'Withdrawal' map the owner already plays, but it adds the vault and its
two staircases, runs through the house in the opposite direction, ends on the front square instead of the back
alley, and brings the level's own music and alarm. What is left is authoring on the Retomoto pattern, about half
that job: placing start, loot, exit and van, wiring a timed vault opening out of the campaign's own door, lamp,
sound and blast objects, staging 53 guards and police, then the usual bots, wardrobe and guns steps. The second
campaign level of the bank (the van chase and the subway) should be left out: it is a ride, it lies more than a
kilometre away, and together the two do not fit the game's model table. The two things only a run in the game
can tell are whether the Dead Men doors really swing when told to, and whether the vault's blast is fun or
simply lethal; both have a fall-back that keeps the round playable.

## 8. Verification (second agent)

2026-10-11, agent cfa-bank-skeptic. OFFLINE; no existing tool edited, nothing installed, the game not started.
My own scripts (none of them imports the first agent's): `G:/kl_scratch/cfa_bank/skeptic/` (`<k>/` below); my own
trial builds: `<work>/build/cfa/bank/skeptic/` (result.json / log.txt kept, every archive and file beside it deleted).
STATE: complete. Statements corrected IN PLACE above are marked 'corrected by the second agent' (sections 0, 3.2, 3.5,
4.1, 4.3 twice, 5, 6.1). The three lists are 8.6.

### 8.1 The trial graft, its weight, the mesh (each by my own run)

- MEASURED `python tools/kl_maps.py one <work>/build/cfa/bank/skeptic F07 M03_A --campaign --keep` (38 s): ok, problems 11
  (1 stream clip + the 10 Fragile Alliance findings), dangling 0, entities 19,675, rooms 28, textures 1,866, materials
  1,221, prm_chunks 64,870, .prm 85.7 / .TEX 373.9 / .ANM 21.6 / .fxc 17.8 MB, nav 232,480 bytes: identical to the first
  agent's result.json field for field (only 'seconds' differs).
- MEASURED `kl_graft.py lighten ... --load trim,slim` on my build: .prm 85.7 -> 43.4 MB, .TEX 373.9 -> 183.6 MB, archive
  153.1 MB; `kl_impact.py`: problems 0. `kl_chars.py wardrobe`: 64,870 chunks, chunk table 64,871 (15,509 of 24,322 dead
  indices taken, 8,813 free), .prm 59.5 MB, archive 178 MB, problems 0; `kl_impact.py`: 0.
- MEASURED `python <k>/nav2.py M03_A ...` (the RAW Dead Men mesh read straight from the .gms, my own parser, my own
  point location with the polygon's plane height, Dijkstra through shared-edge midpoints): 902 polygons, 79 areas, 138
  waypoints, 30 links (kind 2: 14, kind 1: 14, kind 6: 2); 30 connected parts, the largest 566 polygons, y -960..1220,
  x -9603..8575, z -14745..-735. All 21 stations of the route lie on that part with the mesh's height within 60 of the
  station's height (worst: the vault door's neck, mesh -900 against -960; plaza 756 against 812).
  ONE QUALIFICATION the report does not make: the 30 parts come out only when the 106 edges coded '-2 - polygon' (an
  edge into another AREA of the mesh) count as walkable; over plain neighbour fields alone the mesh is 79 parts = its
  79 areas. That the game's path search crosses such edges is not read in kl2.exe by anybody; it is borne out by the
  Fragile Alliance bank, whose mesh splits the same way (my script: 49 areas, 9 parts, the largest 490 polygons = the
  'part A, 490 polygons' of re/fa_round.md 6.1) and whose AI heisters cross it from the plaza to the yard live
  (READ CLAUDE.md 2026-10-10 16:50). So: ASSUMED from that, not proven for this level.
- Route length by my measure (through edge midpoints): yard -> briefcase 120 m, briefcase -> van stop 164 m, 284 m
  in all - under the report's 147 m / 200 m, which it calls upper estimates.
- MEASURED `python tools/kl_maps.py chain <work>/build/cfa/bank/skeptic F07 M03_B M03_A`: builds; first problem '.prm:
  79408 chunk-table entries, the game's table has 73728: the loader writes 5680 pointers over the globals behind it';
  22,873 entities, 2,177 textures, 1,356 materials, 45 room sets.
- MEASURED `python tools/kl_maps.py preflight` on a kept build of mine (`<k>/preflight.out`): 'preflight: CRASH 2, RISK
  10, NOTE 81'; 'RISK first controller LightToggle x22 (in the build: 22) ... stock Dog Days: 0 in NO LEVEL'; 'ok
  shaders 0 of 1221'; 160 KEYS chunks found; 28 rooms / 76 gates / 47 neighbour lists.

### 8.2 The weight WITH the enemies (the report estimated it; nobody had built it)

`python <k>/build_squads.py <work>/build/cfa/bank/skeptic`: `kl_maps.one` with `kl_maps.campaign_drop` and
`kl_graft.DeadMen` wrapped in my process only, so that the 22 squads `kl_fa_author.squad_plan` lets stay (asked of the
real function with `SQUADS['M03_A'] = ('GamePlay!', 'COOP!')`: 22 squads, 53 actors; 27 squad subtrees with 60 actors
are left; `kl_fa_author.strip` takes 83 mini-cutscene controllers off), the three single-node door proxies, the three
`BoomBox_BlowVault` and the two `PlayMusic` objects are not dropped. MEASURED:

| | no enemy (the report's build) | 22 squads + the 9 single objects |
|---|---|---|
| built | ok, problems 11 | ok, problems 10 (the 'no ZSquadScript' finding is gone), 0 dangling scene paths |
| entities / chunk-table entries | 19,675 / 64,870 | 20,076 / 65,639 |
| .prm as built | 85.7 MB | 51.6 MB (92.8 MB is past kl_graft's 90 MB: 8,650 dead chunks emptied at once) |
| .ANM / textures / materials | 21.6 MB / 1,866 / 1,221 | 21.9 MB (+25 clips) / 1,903 / 1,239 |
| kl_arms | no actor | 53 actors armed (Dead Men gave: `HG_HK_USP_01` 30, `Smg_MP5-A3_01` 13, `Rifle_M4A1_01` 10) |
| stream clips not in the merged PC_Def.str | 1 | 10 (kl_snd's count: the six music clips, the vault ambience, guards' lines) |
| after lighten | .prm 43.4 MB, archive 153 MB | .prm 51.6 MB, .TEX 197.3 MB, archive 167 MB |
| after wardrobe | .prm 59.5 MB, table 64,871, archive 178 MB | **.prm 67.8 MB, table 65,640 (8,828 dead indices free), archive 191 MB, 69 people** |
| `kl_impact` (bone ids of the kept actors) | 0 | 0 at all three steps |

So the squads can stay as far as the offline checks go, and the finished map is under Retomoto (74.2 MB / 65,119)
on the .prm and level with it on the chunk table - not under stock F07 (63.6 MB) as section 0 and the returned
claim say. F07 squads re-placed for the hall, the van's archive kept alive and the gun looks come on top.
This also shows the 'outside patch' route works for a second authored map: no file of kl_graft / kl_maps had to be
edited to keep campaign objects by name.

### 8.3 The round against the COLLISION (the report tested the navigation mesh only)

`tools/kl_escape.Walk` samples the non-convex static and key-framed collision into 20-unit cells; its own flood keeps
one floor per cell and so cannot hold the vault lobby under the banking hall (my first run, `<k>/walk2.py`, 'failed'
at the foyer for that reason alone: shown by `<k>/walk5.py`). `<k>/walk6.py` / `walk7.py` use its grid with a flood
over (cell, floor height), Walk's own step rule (up 45, down 60, blocked by anything 55..165 over the floor), every
convex key-framed placement added as its bounding box (door leaves), and REF ids taken out at flood time.
LIMITS: no character radius, rigid props ignored, a door is where the file has it. MEASURED on stock M03_A's .HVK
and again (`walk8.py`) on the .HVK of my built level, with the same outcome:

- **As the file is:** from the START (300, 200, -4350) the flood reaches the yard and nothing else. The yard's floor
  is real (y 199 under all four proposed start places and the traitor row); it is a closed box: wall and hero-only
  collision (`ColiObj_Player_15 / _16 / _17`) on three sides, the roller doors on the fourth.
- **Every key-framed object out:** every station is reached from the yard - dock, vault lobby, both flights, ante-room,
  vault, all seven proposed loot places, airlock, stairs, foyer, hall, both Fragile Alliance cash-drawer places, front
  door, plaza, van stop, both ends of the street, both police places. Not reached: the statue behind the bars
  (966, -960, -12933), as the report says (it needs the PRE -> POST swap). No static object stands on the way, and
  **the bank's front door has no door**: after the hall the flood runs out to the street with nothing animated in
  its way. MEASURED `<k>/door2.py M03_A`: the entrance is a funnel of two static shatter-glass wings
  (`While_ShatterGlass_A`, with its `Shard_*` pieces) whose free gap is 2.0 m at its narrowest, x 200..400 at
  z -9410 - the same entrance the Fragile Alliance map sends its crew IN through, here the crew's only way OUT.
- **The doors in the order the crew meets them** (`walk7.py`: open whatever animated object bounds the reached region,
  flood again):

  | stage | newly reached | what had to open | in the report's table? |
  |---|---|---|---|
  | 0 | the yard | - | |
  | 1 | dock, security hall, control room | `M03_A_Garage_01a\SI0201_M03_BackDorAnim_01` (x 370..750, z -4690) | yes |
  | 2 | vault lobby, the airlock's west side | `M03_A_VaultLobby_01a\SI0103_M03_BankVault_GlassDoor_01` (x -150..150, z -6810) | yes |
  | 3 | the stairs down, cross corridor, ante-room; airlock middle | `...VaultLobby_01a\SI0103_M03_BankVault_GlassDoor_02` (x 250..550, z -7610); airlock leaves `DDorSlide_03 / _04` (x 990) | yes |
  | 4 | vault and loot; airlock east, stairs, foyer | `M03_A_VaultEntrance_01a\SI0102_M03_BankVault_Door_PRE_01` (x 250..610, z -12510..-12430); airlock leaves `DDorSlide_01 / _02` (x 1210) | yes |
  | 5 | hall, front door, plaza, van stop, the whole street | `M03_A_VaultLobbyFoyer_01a\SI0103_M03_BankVault_DDorSlide_01 / _02` (x 190..410, z -5790, y 804) | yes (`DoorCtrl`) |

  So the report's door table is COMPLETE for the route: six sets must open (dock, glass 1, glass 2, vault, airlock,
  hall / foyer), the rods are for the eye only.
  **Sufficient and each necessary** (MEASURED `<k>/walk9.py M03_A`: the campaign's own entities out, every other
  animated object of the map where the file has it): with those six sets open all 20 stations of the round are
  reached; shut any ONE again and this is lost - dock door: everything but the yard; glass door 1: the vault lobby
  and everything after it (the steel side doors are no way round); glass door 2: the way down and the vault; vault
  door: the vault and the loot; airlock: stairs, foyer, hall and the whole way out; hall / foyer leaves: the hall
  and the whole way out. **The round is six doors in series and there is no second way**: the way OUT hangs on
  two sets (six leaves) that the crew passes only after the loot. A door that fails behind the crew ends the round
  for everybody in the cellar. That is a property of this building, not of the wiring - a reason to open the
  airlock and the hall / foyer leaves at the round START and keep them open, and to gate only the vault. Animated objects my test met that the table does not name, none on
  the route: the second bay is TWO leaves (`Garage_01a\SI0201_M03_BackDorAnim_02` and `Outside_01A\SI0201_M03_BackDorAnim_01`,
  both at (40, 550, -4706)); steel side doors `VaultLobby_01a\SI0201_M03_DoorSteel_A_01 / _02` (x -150 / 150,
  z -6530..-6430) and `SecurityHall_01a\SI0201_M03_DoorSteel_A_01` (-1190, 242, -4750: the west door, which the
  Fragile Alliance map leaves open and this level has shut); the booths' doors `VaultStairs_01a\SI0103_M03_BankVault_Wall_Door_01 / _02`;
  the two yard fences `SO0301_USA_animFence_01_01 / _02` (behind them the east ramp climbs to the plaza's level at
  (2420, 700, -8800) and ends at a static fence: not on the navigation mesh, 66..871 off it, so no AI takes it).
- A fall-back for a door that will neither move nor let itself be switched off, which the report does not name and
  which has a live precedent: `tools/kl_escape.py` `open_wall` / `place_entities` / `cut_collision` sink one piece of
  the Fragile Alliance bank's yard wall and take its collision placement out of the joined .HVK (READ re/escape.md
  5.1); AI heisters cross there in the game (READ CLAUDE.md, live night 2026-10-11, run H0_DM03). That piece is
  STATIC; a door leaf is key-framed, and the join already drops key-framed placements of entities that leave
  (MEASURED: 482 key-framed REF ids in stock M03_A's .HVK, 308 in my built level - the campaign's cars are gone).
  ASSUMED that a sunk leaf's key-framed placement can be cut the same way: `cut_collision`'s text speaks of static
  placements only. With it the route cannot be closed by a door for good; what is lost is the door as a beat.
  *(corrected after the critic: no longer ASSUMED - built. `python G:/kl_scratch/cfa_fill1/build_open.py bank <out>`: twelve
  leaves sunk, 12 key-framed placements cut (308 -> 296), verify 11 as before; this section's own walk8.py on the built
  .HVK reaches 45 of its 46 stations with nothing removed at flood time. re/campaign_fa.md, section 'Gap closed: the route without a run-time event', G1.2.)*
- Two parked armoured transports are map geometry and STAY: `M03_A_Outside_01A\V_USA_ArmoredTransport_A_Static_00`
  at x -30..190, z -4130..-3590 and `#01` at x -350..-130, z -3310..-2770. The first stands 2.2 m from the west
  START stack and 1.1 m from the traitor row's west end: clear, but the row cannot move west.
- The dock door's doorway on the mesh is x 385..735: one opening 3.5 m wide for eight heisters, with 13 guards
  behind it - and the owner's own words on the Fragile Alliance bank are that the AI heisters 'get slimed out' at
  this door or its twin bay (READ CLAUDE.md 2026-10-10 ~21:40). The start is a funnel; ASSUMED from that remark:
  the likeliest place for the bots to die first.

### 8.4 The escape vehicle

- The van exists and does not need Dead Men's .ANM: it is stock F07's `Animation/F07/F07_Escape_Vehicle_01.zip`, moved
  by position / rotation keys in the .buf (READ re/map_escape.md 9.2, 9.3; four maps and Retomoto drive it live).
- READ tools/kl_map_escape.py `van_plan` (line 1074): it wants exactly one escape car with two spline routes; M03_A
  has none (MEASURED: 0 `Online*` controllers), so the road has to be given as points - the report's soft blocker
  stands. Retomoto's `kl_fa_van.py` takes points but lays a straight lane only.
- MEASURED `<k>/spl2.py M03_A 11639 11643`: the two splines hold exactly the points the report lists (49 m and 64 m).
  The stop and the hairpin: corrected in place in 4.3. Lanes MEASURED by `<k>/lane2.py` (same place).
- Straight east-bound lines along the street are NOT lanes (planters `S00701_M03_Square_Dirt*`, palms, a shop
  corner at x 2648): the designers' roads are the only proven ground for a van.

### 8.5 Other statements re-derived

- MEASURED `<k>/facts2.py`: textures - 1,155 of M03_A's 1,371 distinct pictures are in M03_FA_A byte for byte (135.1
  of 192.3 MB), 216 (57.2 MB) only here. Placed objects - 6,391 under Locations / CloneGroup_Locations, 2,838 (44 %)
  with a twin of the same class and name within 5 units (the report: 2,726 by rounding to a 5-unit grid);
  `Parkade_Deck_01a` 94 of 94; `Vault_01a` 134, `VaultEntrance_01a` 150, `VaultStairs_01a` 210, `VaultStairs_02a` 149,
  three `ViewBooth` 27, `Armory_01a` 28 = 698 placed, 0 twins. M03_B: 2,774 placed, 2,211 inside rooms, 0 of those
  with a twin in M03_A (85 outside rooms). Leftovers: 0 classes and 0 controllers matching spawn | online | money |
  pip in M03_A; in M03_B only `ZVehicleSpawnGroup` 4 + `ZCivilianVehicleSpawnGroup` 4.
- MEASURED `<k>/nav2.py M03_FA_A` / `M03_B`: M03_FA_A 697 polygons, lowest vertex y 0; M03_B 785 polygons, all at
  x 36,756.. and z 123,654..191,803, 0 links, largest part 215.
- MEASURED `<k>/w2.py M03_A node ...` (world places from the .prp chain; they agree with the .gms records the first
  agent used on all but 39 of 18,703 nodes, those 39 being squad groups): `VaultDoors_Open`, `AnimProxy_Garage_Open`,
  `SlideDoors_Open` are top-level single `MatPosAnimProxy` nodes with the frames and targets given; the six rod
  proxies sit in `MercSqd_Valutbreaker_OpenVault` (77 nodes), the glass door proxies in two other `ZMercSquad`
  subtrees; `BoomBox_BlowVault#01` Explode 1300 / 1000 / 1800 + ShakeCamera, `#02` / `#03` 800 / 800 / 800;
  `Vault_PRE` ZGEOM[3] = 0, `Vault_POST` and the fire group = 1; the three level bounds, `CP_03_PosP1 / P2`,
  `TB_VbByVault`, the six deposit-box walls, the trolley, the statue, the counters at x -791: all at the places given.
- MEASURED `<k>/kept2.py M03_A`: the pre-pass drops 489 subtrees (2,479 nodes), 10,531 stay; kept controllers no Dead
  Men Fragile Alliance level has: `LightToggle` 22, `MatPosAnimProxy` 1. One kept CLASS none of the four has,
  `ZGateLightSpotSquare` x 2 - but M09_A / M09_B have it (9, played live in Retomoto) and stock Dog Days has 17.
- MEASURED `python tools/kl_str.py list <DM>/PC_Def.str Music/`: `BO_Sus_LOOP` 144.0 s 4 layers, `BO_Sus_LOOP2` 56.0 s,
  `M03A_Bustout_A_I` 168.0 s; and my squads build names exactly `BO_Sus_Layer1..4_*_LOOP.wav` and the two Bustout
  clips as missing from the merged stream file once the two `PlayMusic` objects are kept.
- READ: tools/kl_graft.py line 1076 `import kl_fa_author as au`, tools/kl_maps.py line 440 `import glob, kl_fa_author`;
  tools/kl_str.py `MUSIC` has the one entry 'M09_A'; tools/kl_expansion.py lists DM01 F01, DM02 F02, DM03 F03, DM06
  F04, DM09 F06 (five of six); re/retomoto_fa.md 0 '33 squads / 63 actors', 'No entity and no controller is created'.
- MEASURED: 76 top-level subtrees hold a squad controller (49 `ZSquadScript`, 21 `ZMercSquad`, 6 `ZFusionSquad`), 113
  actors, all under the 49; 11 `ZHavokCar`, 2 `ZHeli`.
- Enemy numbers against what has run: 53 kept actors against Retomoto's 63 (played live) and stock Dog Days'
  21..45 armed enemies a level (READ re/map_ai.md 0): inside our experience, above stock.

### 8.6 The three lists

**Confirmed** (my own run or reading, as named above)
1. F07 + M03_A builds: ok, 0 dangling, 11 problems = 1 stream clip + 10 layer findings; every number of the claim.
2. Lightened: .prm 43.4 MB, .TEX 183.6 MB, archive 153 MB, `kl_impact` 0.
3. Wardrobe on top: table 64,871 (15,509 of 24,322 dead indices, 8,813 free), .prm 59.5 MB, problems 0 - for the
   build without enemies (see Corrected 1).
4. Mesh: 902 polygons, 30 parts, the largest 566 with the extent given (with the qualification of 8.1).
5. Every station on that part, by my own point location with the plane's height.
6. 30 links = 14 + 14 + 2 by kind; none kept joins the bank's part to alley / car park / roof; the two rappel
   links end at (-35 / -151, 200, -4525).
7. Same building, same coordinates as M03_FA_A; the vault rooms (698 placed objects) have no twin; M03_FA_A's mesh
   has nothing below y 0.
8. 1,155 of 1,371 pictures identical (135.1 of 192.3 MB).
9. No leftover of a Fragile Alliance layer in M03_A or M03_B.
10. The chain: 79,408 chunk-table entries, 5,680 over.
11. M03_B's mesh is 1.3 km away, no link, largest part 215; 0 of its 2,211 room objects has a twin in M03_A.
12. `squad_plan`'s rule (the real function): 22 squads, 53 of 113 actors; the hall guards, car squads, shield
    squad, helicopters and snipers do not stay.
13. The vault's plain objects, their places, values and load-time states.
14. After the pre-pass: `LightToggle` x 22 and one `MatPosAnimProxy` are the only new controllers; registered in
    kl2.exe, 0 objects in all 21 stock levels (also `DoorCtrl`); preflight CRASH 2, RISK 10, NOTE 81.
15. The two splines, point for point; the three bounds.
16. The music objects and the three stream sets with their lengths.
17. The route IS one connected walkable way in the collision too, once six door sets are open; the door table
    is complete; the front entrance is open (8.3). Not in the report: this is new evidence FOR it.
18. The imports by name, the single 'M09_A' music entry, the one free slot, the van tool's need of an escape car.

**Corrected** (in place above, marked)
1. 'Lighter than Retomoto and than stock F07 (.prm 59.5 MB)' -> 67.8 MB / table 65,640 with the round's own 53
   enemies: under Retomoto, over F07 (8.2).
2. 'Whether a Dead Men door moves in Dog Days has never been seen' -> the dock's roller door is the very object of
   the Fragile Alliance bank and the owner saw it open; and no proxy or husk keep is needed: every door takes
   'Activate' itself (4.1, 5, 6.1).
3. The van's stop: the designers' in-road is a REVERSE drive into the bank's front; a nose-first F07 van at
   (250, 707, -10700) faces the bank and pivots 120 degrees to leave. A measured through lane is given (4.3).
4. 'No start, no loot place, no escape shared with Withdrawal' -> 137 of 284 m of the walking is on ground both maps
   have; the hall stacks are at the Fragile Alliance drawers; start and van are at the other map's end and start (4.3).
5. '28 rooms: more than any map that loaded' -> more than any GRAFTED map; stock Dog Days levels have up to 61 (3.5).
6. The start depends on ONE door opening, in a closed yard, through a 3.5 m doorway where the bots already die on
   the Fragile Alliance bank (6.1, 8.3): a design risk the report did not name.
7. Not a wrong statement but a missing one: the route is six doors in SERIES, each necessary, no way round any
   of them, two of them on the way out only (8.3, `walk9.py`). 'A fall-back keeps the round playable' (section 7)
   holds for the vault door; for the airlock and the hall / foyer leaves a failure means nobody escapes.

**Could not be verified**
1. That the game's path search crosses the '-2 - polygon' edges between mesh areas (not read in kl2.exe; inferred
   from the sibling map's live rounds). The whole 'one part, no link needed' statement rests on it.
2. That 'Activate' on a `MatPosAnim` storing frames -1 / -1 (glass leaves, rods) plays the whole clip; that the
   vault door, the airlock and the hall / foyer leaves answer 'Activate' in Dog Days as the roller door does.
   *(corrected after the critic: the first half is READ in kl2.exe - -1 / -1 is the whole clip - and for the GLASS leaves
   the whole clip is open AND shut again (135 degrees at frame 50, 0 at frame 100): they need LAST 50. Rods, vault door,
   slide leaves and roller door are one-way clips. re/campaign_fa.md, 'Gap closed: the route without a run-time event', G1.7 and G1.8.)*
3. Whether a shut key-framed door of this level holds a player (the collision records are there; Retomoto: one
   door did, one did not).
4. Every place marked GUESS in 4.3 (start rows, loot, exit box, back bounds, timings), the 2.6 M loot sum, and
   reach of the loot by a player's use action (`kl_fa_loot.py survey` was not run: there is no loot object yet).
5. The 330 dialogue objects and the vault breaker's six lines in the level's sound bank (not re-derived).
6. `LightToggle` at load; the vault blast beside players; the two PRE / POST swaps; music by ear: live only.
7. The 0.5-of-Retomoto estimate: a judgement. My reading: fewer unknowns than the report feared at the doors,
   more at the start and the van; about the same total.

**Verdict after the checks: ready-to-author**, with the round changed in three places before anything is wired -
the van stops where the through lane meets the away road, nose north-east to east (4.3); the airlock and the
hall / foyer leaves open at the round start and stay open, so that only the vault is gated (8.3); and the first
live run is the bare level with the dock door sent 'Activate' at the round start. Nothing I measured blocks the map; the level, its weight with its enemies, its mesh
and its collision all carry the route. What it is NOT is a new place: it is the owner's bank walked backwards with
a vault under it, and it would take the last free slot of the page.
