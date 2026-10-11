# The park, the campaign way: M06_A 'Exchange' as a Fragile Alliance map (study)

2026-10-11, agent `park` of the campaign-FA study. OFFLINE: nothing was installed, the game was not
started, no existing tool was edited, nothing was committed. `<work>` = `G:/SteamLibrary/steamapps/common/
Kane and Lynch Dead Men/KL_PortTools`.

- Scratch scripts (all new, read-only on the game files): `G:/kl_scratch/cfa_park/*.py`; their outputs are the
  `.txt` files beside them. Each MEASURED statement below names the script or command.
- Trial builds: `<work>/build/cfa/park/` (archives deleted after measuring; `result.json`, `log.txt`,
  `graft.txt`, `preflight_run.txt`, `lighten_log.txt` kept).
- Pictures: `<work>/build/cfa/park/pics/` (five PNG, made by `pic.py` from the levels' own collision and
  navigation mesh; north = +z is up, +x right, 16 world units a pixel, 100 units = 1 m).

Evidence labels: **MEASURED** (output I produced), **READ** (code or an existing note), **ASSUMED** (with the
reason), **GUESS** (a coordinate or number proposed, not measured). Compass words are read off the
coordinates (+z called north), not off the game.

---------------------------------------------------------------------------------------------------

## 0. Short answers

1. **M06_A is the same place as the Fragile Alliance map 'A Walk in the Park' (M06_FA_A): the same
   Japanese garden at the same world coordinates, at night.** 91 % of the campaign level's floor (1 m
   cells of the static collision, compared at the same height) is in the FA level, 87 % the other way;
   358 of its 456 textures are in the FA level; same far plane and background colour. MEASURED
   (`mapcmp.py`, `compare.py`).
2. **What the campaign level has and the FA level does not use:** the spiral STAIR TOWER at the south end
   and the HIGHWAY RING 23 - 25 m above the garden as playable ground (on the navigation mesh, with cover
   boxes and level bounds), the pagoda as a place where the round begins, Retomoto's men spread over the
   south garden, police cars / a SWAT van / snipers on the ring, a getaway van, and the chapter's action
   music. **The FA level has no stair tower at all** (none of its objects, 52 collision triangles in its
   footprint against 7,180) and its navigation mesh has no polygon above y 719: from its south garden there
   is no way up to the part of the ring where the campaign ends (its own two stairs stand in the north-west
   and in the east, at its START). MEASURED (`stairs_objs.py`, `stairs_fa.py`, `mapcmp.py`, `flow.py`,
   `music.py`).
   *Corrected by the second agent:* 'no way up' is wrong as a statement about the FA level's ground. Its
   collision holds stairs from the garden to the ring's deck in the north-west (`SO0201_M06_FreeW_Spiral_WithStairs_A_01`,
   climbing at about (-3060, 533, 6540) .. (-3380, 2003, 7100)) and the deck is continuous from there to the
   campaign van's place: a flood fill over the collision floors of M06_FA_A from the helicopter's boarding
   place reaches (-2572, 2498, -7933) after 435 m. IO closed those stairs with a level bound of its own,
   `Level_Bounds!LevelBound_Stairs_01` at (-3026, 1010, 7277). MEASURED `sk_flood.py M06_FA_A ... --trace`,
   `sk_names.py M06_FA_A stairs levelbound` (optimistic fill: floors only, no walls). What stands: no stair
   tower in the south (0 of its objects, 52 triangles against 7,180: re-measured), and no mesh polygon above
   y 720 (re-measured) - so the AI cannot go up there, and for a player the way is half round the ring.
3. **It grafts.** `kl_maps.py one ... F07 M06_A --campaign`: 10 problems, every one the missing Fragile
   Alliance layer; 0 dangling paths; everything inside the limits and below the sizes that already ran
   (section 3). Two faults of the pre-pass on this level, both with a one-line cure that was tried without
   editing a tool (`trial2.py`): it drops the level's only cover list, and it keeps a level bound on the
   stairs whose off-switch it drops.
4. **The AI heisters can walk the whole campaign route**: pagoda, bridge, garden, stair tower, highway and
   the van's place lie on ONE connected part of the converted mesh (584 polygons, joined by polygon edges
   alone, no link needed). MEASURED (`nav2.py`).
5. **Verdict: feasible as a variant** - a second round on the garden the owner already has, not a new
   place. It has to be BUILT from M06_A (a graft of its own, the Retomoto way, about 0.4 of Retomoto's
   work), because the existing FA level has neither the stair tower nor a mesh on the highway. Of the campaign
   places in this study it adds the least that is new; it is the cheapest to make.

---------------------------------------------------------------------------------------------------

## 1. What the place is

### 1.1 Rooms, extents, counts

MEASURED: `python tools/kl_maps.py what M06_A` / `what M06_FA_A` (extent = entity positions of everything
under the room, far scenery included).

| level | entities | rooms (entities; x / y / z of what is under them) |
|---|---:|---|
| M06_A 'Exchange' | 17,542 | `M06_A_Out_Part_01a` 1,817 (x -52169..62199, y -8908..31828, z -75990..10493); `_Part_02a` 980; `_Part_04a` 207; `Out_Visible_01a` 3; backdrop `M09_Backdrop_A_00` 2; `M06_Exit_Cutsequence_01a` 202 (x -2990..75694, z -49115..2836: the set of the exit cut scene, a road 700 m away) |
| M06_FA_A 'A Walk in the Park' | 13,746 | `M06_FAA_Out_Part_01a` 1,457; `_02a` 1,243; `_03a` 116; `_04a` 226; `Out_Visible_01a` 3; backdrop `M06_Backdrop_A_00` 2 |

All outdoors, one level of rooms: no interior, and no door or gate on the way that a script opens. MEASURED
(`scripted.py`, and every `ActivateGeom` / `DeactivateGeom` / `AIDWrapper` of `dump_campaign.txt`): of the kept
geometry's own scripted objects only the pagoda's window relay and three 'shoot at' helper boxes are named by
a campaign object; beyond that the campaign switches, by list, the three boxes of the stairs' level bound
(3.3), the lights under the highway, three invisible `VisionBlocker_snipers_*` at the snipers' perches, a
phone and two ambience sounds. Nothing of that is a wall on the route.

The ground in numbers (MEASURED, `mapcmp.py`, `lootspots.py`, `ring.py`, `stairs.py`; static collision of
`Locations/*` and the converted navigation mesh):

| part | where (world units) | note |
|---|---|---|
| the pagoda (pavilion on the lake) | floor y 635, platform x 273..1328, z 1905..2798 (10.5 x 9 m); inner floor x 495..1104, z 2059..2640 (corrected by the second agent: that is the BOX of three polygons that form a cross - corridor 54 x 725..875, z 2060..2640 = 8.6 m2; wings 55 / 56 x 495..725 and 875..1105, z 2225..2475 = 5.7 m2 each; 20.0 m2 of floor on the mesh, MEASURED `sk_polys.py M06_A 200 1400 1800 2900 600 700`) | twelve breakable windows `PC0200_M06_Window_Pavilion_*` at y 728; paper lanterns over it |
| bridge, pagoda -> south | x 613..987 wide (3.7 m), z 1839 down to the landing at about (814, 392, -651) | 25 m long, open to both sides: the campaign's 'Hellfire' stretch |
| bridge, pagoda -> north | to z 4173; `LevelBound_PagodaBridge` at (803, 545, 4454) half (300, 200, 250) closes it | the FA map comes IN over this bridge |
| the south garden | mesh x -6017..5842, z -13464..4236, floor y about 180..450, 6,801 m2 on the largest mesh part | tea house (802, 173, -2477); torii gate (-776, 165, -4033); 2 `Shrine_B`, 2 `Shrine_A`, 4 `Statue_A`; 228 park lamp pieces; 214 cover boxes |
| the stair tower | square spiral round a shaft, x -265..265, z -11525..-10875, mesh flights 1.3 m wide, y 320 -> 2569 (22.5 m) in 3.5 turns (corrected by the second agent: the mesh enters at the garden's own level, y 220, through polygon 804 on the tower's EAST side at about (80, 220, -11465), portals 113..117 wide, then 37 polygons of flights 129 wide and landings, slopes 28..31 degrees; 220 -> 2570 = 23.5 m up and 74.5 m of walking from the entry to the top; closed on all four sides between the first landing and the top - no way off half-way. MEASURED `sk_nav.py`, `sk_misc.py`, `sk_tower.py`) | 29 mesh polygons of the largest part between y 900 and y 2300, 48 in all; 7 cover boxes |
| the highway ring | a ring road round the garden, centre about (0, -100), deck at radius about 7,900..10,500 (two carriageways, median near 9,200), deck y 2,260 (west) .. 2,640 (south) .. 2,950 (north) | 3,583 m2 of it are on the largest mesh part: the south-west arc, x -9845..4051; 6 cover boxes; the campaign's two bounds leave 91 m of it (33 m west and 58 m east of the van) (added by the second agent: 33 / 58 m are to the bounds' CENTRES; on the van's lane their kill boxes begin 30.6 m west and 55.4 m east of the stop, their warn boxes 15.5 m west and 42.8 m east, MEASURED `sk_bounds.py`. And the two carriageways are separate decks: the median `SO0201_M06_MiddleConcrete_01` (radius 9,250..9,350) has ONE gap on this arc, x 80..320 at z about -9300..-9450, 2.4 m wide in the collision in both of the median's states and 186 on the mesh, 15 m north of the stairs' top - everything between the stairs and the van passes through it. MEASURED `sk_ring.py`, `sk_median.py`) |

Pictures:
- `pics/park_campaign_garden.png` - M06_A, floors below y 1300, colour = height, white = the largest part
  of the navigation mesh, marks 1 PAGODA, 2 BRIDGE (objective 020), 3 GATE (checkpoint 2), 4 MERCS, 5 GARDEN,
  6 STAIRS.
- `pics/park_campaign_upper.png` - M06_A, floors from y 1300: the ring, the ramps, the stair tower; marks
  6 STAIRS, 7 TOP, 8 LYNCH, 9 VAN, SN-W / SN-E (the two highway snipers).
- `pics/park_fa_garden.png` - M06_FA_A, garden level with its mesh and the FA round's places.
- `pics/park_navmesh.png` - both meshes in one picture: yellow = M06_A's largest part at garden level,
  red = the same part on the stairs and the ring, blue = M06_FA_A's mesh (it shows through as khaki where
  both lie), grey = M06_A's other parts.
- `pics/park_shared_floor.png` - grey = floor both levels have, orange = campaign only, blue = FA only.

### 1.2 Top-level subtrees and the graft's two sides

MEASURED: `python tools/kl_maps.py sides M06_A`; per subtree with places: `tops.py M06_A`.

| family | subtrees | nodes | kl_prpjoin side | campaign pre-pass |
|---|---:|---:|---|---|
| `CloneGroup_Locations` | 34 | 5,414 | map | kept (clone groups follow their template) |
| `Locations/*` (`M06A_Locations.zip` 3,175, `M06A_Exit_Cutsequence_01a.zip` 228, `M06A_Effects.zip` 5, `M06A_Postfilter.zip` 2) | 4 | 3,410 | map | kept |
| `CloneGroup_Effects` | 113 | 4,071 | 872 map / 3,199 systems | map part kept |
| `AllLevels/mainsceneincludes.zip` | 1 | 2,491 | systems | left out by kl_graft (Dog Days' own systems come) |
| `Gameplay!` (Enemy! 18 squads, Friendly!, Civilian!, timers, trigger boxes) | 72 | 868 | map | DROPPED |
| `CloneGroup_ROOT` | - | 780 | map | - |
| `Specials!` | 107 | 140 | map | 99 dropped; 41 kept: 4 level bounds with their warn boxes (12), 18 `NoCoverBox`, 17 `PlayerCoverCollision` |
| `CutScenes/*` (`M06_Intro`, `M06_Exchange`, `M06_Exit`, `M06_Exit_part2`) | 4 | 108 | map | DROPPED |
| `COOP!` | 58 | 94 | map | DROPPED |
| `Locations/M06_A/M06_A_Audio.zip!*` (ambience) | 42 | 42 | map | kept |
| `Effects/AllocMany/*` (car fire, tyre, SWAT explosion) | 4 | 76 | map | kept |
| `Traffic!` | 32 | 32 | map | DROPPED |
| `AI_Players!` | 6 | 12 | map | DROPPED |
| `M09_Backdrop_A_00` | 1 | 2 | map | kept |

Pre-pass total: 238 subtrees / 1,213 nodes dropped, 10,637 nodes stay (MEASURED, same command).

### 1.3 The campaign's flow, rebuilt from its scripted objects

MEASURED: `dump.py M06_A ... Gameplay! Specials! COOP! AI_Players! Traffic! CutScenes` (2,145 lines,
`dump_campaign.txt`) and `flow.py M06_A` (`flow_M06_A.txt`). Places are the objects' own world positions.

1. **Start (two players apart).** Kane: checkpoint 1 `Specials!Checkpointsave!CP_01_PosP1` (802, 623, 1702),
   on the bridge just south of the pagoda. Lynch (player 2, or the AI `Merc_04`): `CP_01_PosP2`
   (-1920, 2516, -8001), up on the highway ring, guarding the girl `Gameplay!Civilian!01_Highway!RetoMotoGirl`
   at (-1776, 2519, -8076). Two mercs wait in the garden (`MercSquad_waiting`, box (783, 360, -1981)). The
   intro cut scene `CutScenes/M06/M06_Intro.zip` plays on the highway and stairs.
2. **Objective 010 'Negotiator'** (795, 627, 2355): Kane walks into the pagoda and picks up the phone
   (`Gameplay!Friendly!PlayerAction_PickupPhone` (809, 723, 2341), prop `Specials!Items!MobilePhone_01`);
   cut scene `M06_Exchange.zip` (x 603..1103, y 658..770, z 2173..2464 = inside the pagoda).
   Lynch's objectives meanwhile: 040 'WatchGirl', 060 / 070 / 080 kill the two highway snipers
   (`03_Highway!01_Sniper` at (-8601, 3506, 732), `03_Sniper` at (6319, 3030, 5572); the two sniper-van
   squads stand at about (5827..6785, 3027..3238, 5182..6662)).
3. **It goes wrong.** `Gameplay!Enemy!01_Bridge!Timer_PaviilionShatter` (3 s) ->
   `Activator_ShatterPavillionWindows` -> the pavilion's own relay `SO0100_M06_Pavilion_01` (twelve windows
   break); `10_MiniCutScene_Hellfire` (the bridge squad `01_Bridge!01_RetoMoto_Squad`, 3 men at
   (786, 170, 6856) .. (1111, 182, 6364), fires at the pagoda). Leaving before that is caught by
   `TriggerBox_LeavingTooEarly` (817, 726, 928) / (817, 638, 4500).
4. **Objective 020 'Bridge'** (1391, 182, 1699): down under the bridge (`CamBox_UnderBridge_01`
   (805, 314, 2675)); `TriggerBox_LeavingPagoda` (780, 751, 2314) unleashes the bridge squad and moves the
   snipers; music cue `07_From_LeavingPagoda`.
5. **Into the garden.** `TriggerBox_KaneGoingIntoGarden` (799, 510, -657); checkpoint 2 at
   `TriggerBox_Checkpoint02` (799, 404, -1521) -> `CP_02_PosP1` (814, 392, -651). Seven squads of Retomoto's
   men (`02_JapaneseGarden!02..06_RetoMoto_Squad*`, 21 men with `Smg_MP5-A3_01_Light`) between z -3,600 and
   z -12,400, started by boxes on the way: `TriggerBox_Hunt` (-2392, 344, -1490), `04_RetoMoto_Squad\TriggerBox`
   (-3991, 328, -2213), `T_KillSnipers` (68, 341, -4056), `TriggerBox_WhatHappened_Dialog` (-1952, 342, -6905),
   `TriggerBox_GoToStairs` (-1894, 178, -7446), `TriggerBox_Lynch_Humming` (-156, 252, -9746).
6. **The stairs.** `TriggerBox_LynchCrazy` (-45, 352, -11409) (music `09_From_EnterStairs`);
   `TriggerBox_OnStairs` (9, 689, -10945) switches `Specials!LevelBound!LevelBound_StairsBottom` OFF
   (`GeomDeactivator_LevelBoundStairsBottom`); a sniper on the stairs (`01_Squad_Sniper`, (18, 1526, -11418));
   checkpoint 3 at `TriggerBox_KaneGoingUp` (-18, 1650, -11462) -> `CP_03_PosP1` (-180, 1605, -11425).
7. **The highway.** `TriggerBox_Disablelights` (106, 2633, -10943) at the top turns the lights under the
   highway off and starts the police: `06_PoliceCar_SinglePlayer` (car parked at (-95, 2575, -10309), 2 men);
   `04_`, `05_`, `07_PoliceCar` drive in on `ZRoad`s from (-8998, 2267, -968), (-8388, 2292, -1911) and
   (7956, 2821, -2525), their 8 men then hold (-3806, 2467, -7352), (-2076, 2518, -8634), (-2103, 2527, -9990);
   `TriggerCounter_CallTheSWATs` / `Timer_Swat` bring `08_PoliceSWATvan` (5 men, van from (-7982, 2149, 4142),
   men beamed to about (-6467, 2402, -6325)). Music cues `11_From_ExitStairs`, `13_From_SWAT`,
   `14_From_SWATKilled`.
8. **Objective 030 'Escape'** (-2584, 2716, -7929): the getaway van `Gameplay!Friendly!03_Highway!GetAwayCar\
   GetAwayVan\Ground_01` (a `ZHavokCar`) at (-2572, 2498, -7933) on the ring's inner carriageway;
   `EndOfLevelTrigger` (-2601, 2609, -7973) half (491, 142, 408) with crew box (-2915, 2608, -8101); cut scenes
   `M06_Exit.zip` and `M06_Exit_part2.zip` (the drive-off, into the far set at x 70,000); `SceneChanger` ->
   `Locations\M07_A\M07A_Main.zip`.

Level bounds of the campaign (`props.py`): `LevelBound_Highway_01` (-6132, 2594, -7113) and `_Highway_02`
(3400, 2780, -8732), each half (1500, 200, 400), turned across the ring; `LevelBound_PagodaBridge` (above);
`LevelBound_StairsBottom` (-197, 659, -10960) half (100, 200, 100).
Enemies in all (`flow.py`): 42 `ZSoldier` + 1 civilian: 24 'JPN' with MP5, 3 snipers (`Sn_Rem700_01`),
10 police (`HG_HK_USP_01`), 5 SWAT (`Smg_MP5-A3_01`); 7 `ZHavokCar`: one sniper van (the squad `03_SniperVan`
holds no car of that class), 4 police cars incl. the parked one, the SWAT van, the getaway van.

### 1.4 Is it the same place as 'A Walk in the Park'? Yes

| measure | result | how |
|---|---|---|
| floor, 1 m cells of up-facing static collision inside x -9000..9000, z -15000..10000, matched within 30 units of height | M06_A 135,789 cells, 123,298 (91 %) also in M06_FA_A; M06_FA_A 141,068 cells, 123,367 (87 %) also in M06_A | MEASURED `mapcmp.py` |
| shared floor by height | garden (y 100..900) 50,066; ramps and the lower ring (900..2300) 34,194; highway deck (2300..3400) 28,609 | the RING is in the FA level's collision too (539 half-metre cells round the campaign van's place in both: `stairs_fa.py`) |
| the stair tower (x -265..265, z -11525..-10875) | M06_A: `SO0201_M06_FreeW_StairsBOTTOM / MIDDLE x2 / MIDDLE_EXIT / TOP`, 40 `LampStairs`, 7,180 static collision triangles (1,236 up-facing), about 116 half-metre floor cells a turn. **M06_FA_A: none of those objects, 52 triangles, 10 floor cells** | MEASURED `stairs_objs.py`, `stairs_fa.py`. The FA level has other stairs instead: `SO0201_M06_FreeW_Spiral_WithStairs_A` in the north-west (x -4085..-2982, z 6917..9857) and `_B` in the east (x 5584..7543, z 5189..7546), beside its START row, and `FreeW_Junction_E_Stairs_FA` |
| what only the campaign has | 12,491 cells: the car park south of the stair tower and the ramp at the east (largest patch 4,761 m2, x -3500..9000, z -15000..100) | `mapcmp.py`, `pics/park_shared_floor.png` |
| what only the FA level has | 17,701 cells: the lake's north shore, the east entrance and the north bridge approach (largest patch 7,078 m2, x -7500..9000, z -800..10000) | same |
| textures | 456 / 405, 358 in both; campaign-only 98 of which 47 are `Locations/M07` (the exit cut scene's set) | MEASURED `compare.py` |
| time of day | both night: `CameraFar` 30,000 and `CameraBackgroundColor` 395784 in both scene blocks | MEASURED `compare.py` |
| lights under `Locations` | campaign 182 omni + 122 spot + 76 square spots; FA 62 + 81 + 1 | MEASURED `compare.py` |
| navigation mesh | M06_A: 913 polygons in 130 areas, 19,304 m2, largest part 584 polygons from y 182 to y 2623 (garden + stairs + ring). M06_FA_A: 954 polygons in 14 areas, 9,389 m2, largest part 936 polygons at y 114..635; **all 954 polygons lie below y 900** (the highest: three single polygons at y 684 / 719 beside the pagoda) | MEASURED `mapcmp.py` |
| cover boxes garden / stairs / highway | M06_A 214 / 7 / 6; M06_FA_A 263 / 1 / 2 | MEASURED `scripted.py` |

The two rounds overlap in the south garden only (corrected by the second agent: and on the pagoda and the south bridge. The FA round comes in over the north bridge, crosses the pagoda's floor - polygons 437 / 439 / 449 at y 635 on the largest part of ITS mesh - and leaves down the same south bridge; 160 of the campaign way's 306 m, 52 %, lie over polygons of the FA level's own mesh at the same height. MEASURED `sk_polys.py M06_FA_A ...`, `sk_misc.py`). The FA round (MEASURED `flow.py M06_FA_A`): START row at
(5485..5634, 288..474, 4176..5000) at the east entrance, `Enter_BridgeHouse_01` (ENTERS_BANK) (671, 453, 5852)
on the north bridge, loot = cocaine carried by two gangs (14 `ZSoldier` with `OnlineMoneyCtrl`, 299 pooled
`DopeBag`s, 4 kill-drop briefcases - no loot lies on the map), `Call_ExitHeist_Trigger` (-342, 384, -1098),
helicopter called at (-1593, 206, -8050), boarding (-1687, 133, -6542); dead criminals return at
(-1001..-1158, 1631..1656, -10246..-9474). The campaign's route starts where the FA route passes its middle,
runs south over the same lawns and then goes UP a stair tower the FA level does not have.

---------------------------------------------------------------------------------------------------

## 2. Leftovers of a planned Fragile Alliance version: none in this level

MEASURED (`leftovers.py`, `flow.py M06_A`, `compare.py`):
- M06_A has 0 `ZSpawnPoint`, 0 `ZOnlinePIPCameraPoint`, 0 `ZOnlineGameplaySettings`, no controller with
  'Online' in its name, no `OnlineMoney*`.
- Its `.SND` has 8 objects under `dialog/multiplayer/fa_menu` (menu lines every level carries) and its `.LOC`
  the 32 scenario titles / briefings every level carries, the ten placeholders among them
  (`BriefingDL04` = 'Briefing DL04 - Tokyo'). Nothing in the level names them.
- Texture `UserInterface/UI_FA_Respawn_PiP_Mask` and camera `IngameFragileAllianceKILLERCamera` are in its
  systems subtree (every level's).
- The one level-specific trace runs the OTHER way: two bridge pieces of the campaign level are named
  `SO0100_M06_Pavilion_BridgePart_B__FA_01 / _02` ((800, 200, -148) and (800, 200, 4852)) and one effect file
  `Effects/AllocMany/M02/Shatter_M02_LightTube_01.zip\M02_FA_LightTube_Shatter_01`: pieces made for the FA
  levels and taken back into the campaign level.
ASSUMED from that: 'A Walk in the Park' IS IO's Fragile Alliance version of this garden; the placeholder
'Tokyo' is another place (not looked for here: the club M05_A and the tower M09 are other agents' parts).

---------------------------------------------------------------------------------------------------

## 3. Can it be grafted: yes

### 3.1 The two trial grafts

| | trial 1: `python tools/kl_maps.py one <work>/build/cfa/park F07 M06_A --campaign --heroes` | trial 2: `python G:/kl_scratch/cfa_park/trial2.py` (the same call, see 3.3) |
|---|---|---|
| result folder | `<work>/build/cfa/park/F07+M06_A campaign/` | `.../F07+M06_A campaign trial2/` |
| `kl_graft.verify` problems | **10, all 'FA:'** (below) | 10, the same |
| `kl_fa.check` | 1 CRASH, 9 BROKEN, 4 DEGRADED, 1 NOTE | the same |
| scene paths that name nothing | 0 | 0 |
| particle template names without a template | 64, none new against stock M06_A | 63, none new |
| entities | 19,157 | 18,626 |
| rooms | 7 (6 the map's) | 6 (5 the map's) |
| textures of 4096 | 1,589 | 1,450 |
| materials of 2048 | 1,002 | 927 |
| `.prm` chunks; table entries (chunks + 1) of 69,632 enforced / 73,728 hard | 53,959; 53,960 | 52,432; 52,433 |
| sounds / waves | 4,692 / 4,556 | 4,669 / 4,533 |
| archive | 326.8 MB | 286.7 MB |
| `.prm` / `.TEX` / `.ANM` / `.fxc` as built (MB = 10^6 bytes) | 79.5 / 392.7 / 21.6 / 17.8 | 78.2 / 336.5 / 21.6 / 17.8 |
| `.WAV` beside the archive | 20.1 MB (20,135,248 bytes) | 19.9 MB |
| after `python tools/kl_graft.py lighten <build> <out> --load trim,slim,fxc` | `.prm` 37.2, `.TEX` 202.3 MB, shader cache 242 -> 119 entries (16.94 -> 8.31 MiB), archive 167.7 MB | `.prm` **35.9**, `.TEX` **146.1** MB, cache 242 -> 117 entries (8.13 MiB), archive **127.6** MB |
| `python tools/kl_impact.py <lightened>` | problems: 0 | problems: 0 |
| `python tools/kl_maps.py preflight <kept build>` | CRASH 2, RISK 14, NOTE 61 | CRASH 2, RISK 11, NOTE 64 |

All MEASURED (the commands in the header row and the left column; `result.json`, `lighten_log.txt`,
`preflight_run.txt` in the folders).

The 10 problems (MEASURED, `result.json` of both): no `OnlineFragileAllianceSettings` (CRASH in a round),
no `ZSetZDefine IsMultiplayerLevel`, no `OnlineExitLevelTrigger`, 0 START and no AFTER_DEATH spawn points, no
`OnlineGamePlayTrigger` ENTERS_BANK / EXITS_BANK / BOARDS, no loot, no `ZSquadScript`. That is the list a
story level must have after the pre-pass (READ re/maps.md 4.2, last item: 'exactly as it should be for a
level that has none'). The two preflight CRASH lines are 'verify reported 10 problems' and the missing
settings: the same thing.

Log lines of the build worth knowing (MEASURED, `log.txt`): `.prm: 18848 of 26239 chunks of M06_A appended
to 35101`; `materials 700 -> 1002 slots, textures 1188 -> 1589 ids`; `baked AO: 939 meshes` (the level's lit
descriptors); 80 scatter objects converted; `.rmi: 1 boxes of F07 + 13 of M06_A`; `.oct: 8 room sets`;
6 gates; 49 KEYS blocks moved; `.ANM joined: clips +0` (the map side names no animation set once the
campaign is gone); `.HVK surfaces` renumbered (12 kinds); 15 materials fitted to the shader cache, 1 left
without a compiled shader: `Locations/_JPN/Paper/Paper_Rice_Lantern_01a_JPN` (the paper lanterns are not
drawn - the same material and the same loss as on the played M06_FA_A, READ re/maps.md 9.1).

### 3.2 Against the limits and the builds that ran

| | this graft (trial 2, lightened) | + wardrobe | stock F07 | Retomoto as played | M06_FA_A ready build `z_maps/M06` (READ re/maps.md 14.1) |
|---|---|---|---|---|---|
| `.prm` | 35.9 MB | about 52 MB - ASSUMED: the wardrobe added 16.1 MB on M06_FA_A (33.5 -> 49.6, READ re/maps.md 14.1) | 63 MB (READ re/maps.md 14.0) | 74.2 .. 79 MB (READ CLAUDE.md 'BUDGET', re/bots_retomoto.md 0) | 49.6 MB |
| chunk table | 52,433 of 69,632 | the same: the wardrobe takes dead indices (READ re/prm_limit.md 'Staying under it'; 8,650 dead vertex / index chunks and 1,401 dead roots are there, MEASURED `lighten_log.txt`) | 35,102 (35,101 chunks, MEASURED `log.txt`) | 65,119 | 46,902 |
| `.TEX` | 146.1 MB | + 12..21 MB (READ re/maps.md 14.1) | 281 MB | 234 MB | 204.6 MB |
| `.ANM` | 21.6 MB (F07's own, nothing added) | - | 21.6 | 20.6 | F07's + 103 clips (READ re/maps.md 9.1) |
| `.fxc` | 8.5 MB with `--load fxc` (17.8 without) | - | - | 16.9 | 17.8 (8.8 with the cut) |
| `.WAV` | 19.9 MB | - | stock F01 14.7 | 25.9 .. 27.8 | 21.8 |
| entities | 18,626 (+ the layer: Retomoto's layer added about 1,300) | - | - | 25,490 | 15,600 |
| navigation mesh | 258,988 bytes | - | - | 603,332 | 258,640 |

The campaign squads, when they are kept, bring animation sets F07 lacks: `Thug` (27 uses), `Army` (15),
`Police_Japan` (4), `Swat_Van`, `Van` (MEASURED `anmsets.py`) - the sets Retomoto's guards and street police
use (READ re/retomoto_fa.md 5), so the `.ANM` grows as it did there (20.6 MB as played). (Corrected by the second agent: it did not grow there. Retomoto's `.ANM` as played is 21,642,904 bytes, READ re/bots_retomoto.md 0 - '20.6' is the same number in MiB - which is F07's own size and the size of this trial; Dead Men's sets are mapped or stood in by kl_anmjoin, READ re/retomoto_fa.md 5, re/maps.md line 630. The conclusion of the paragraph stands.) Nothing here is
larger than what has loaded and played.

### 3.3 Two faults of the pre-pass on this level (causes found, cures tried, no tool edited)

1. **The level's only cover list is dropped.** MEASURED (`coverlist.py`): M06_A keeps its `FFCoverList` on
   `Specials!CoverPoints!CoverControl` (the Dog Days way; M09_A, M09_B and the four FA levels have a top-level
   `CoverList`). `kl_maps.campaign_drop` keeps a `Specials!` subtree only when all its controllers are in
   `PASSIVE = {PlayerCoverCollision, NoCoverBox, LevelBound}` (READ tools/kl_maps.py `campaign_drop`), and F07's
   own `Specials!CoverPoints!CoverControl` leaves with F07's map: trial 1 has **0 `FFCoverList` and 242 cover
   boxes** (second agent: 0 lists confirmed on a build of my own; '242' counts every node with 'CoverBox' in
   its name, 17 of them `NoCoverBox`: 225 cover boxes, 220 in trial 2). What Dog Days does with cover boxes and no list is NOT ESTABLISHED (two lists assert at kl2
   0x6682c5, READ re/maps.md 12). Cause: a missing case in the pre-pass (a limit of its rule, not a bug of
   the graft). Cure: `'FFCoverList'` into `kl_maps.PASSIVE`. Tried from outside (`trial2.py` sets it for its
   own process): the pre-pass drops 237 subtrees instead of 238 and the build has exactly 1 `FFCoverList`
   (`Specials!CoverPoints!CoverControl`, the map's) and 237 cover boxes. `--m-add` cannot do it: `Select`
   lets `m_drop` win (READ tools/kl_graft.py line 860). CAUTION for the authored build: `kl_fa_author.KEEP`
   holds F07's `Specials!*` (READ re/retomoto_fa.md 2, re/maps.md 12) - then F07's list would stand beside the
   map's: keep ONE.
2. **A level bound sits on the stairs and nothing switches it off.** `LevelBound_StairsBottom!Bound`
   (-197, 659, -10960) half (100, 200, 100) covers mesh polygons 808 / 809 of the second flight and its warn
   boxes cover 807 and 810 (MEASURED `stairs.py`); the campaign turns the three off from
   `...05_RetoMoto_Squad\GeomDeactivator_LevelBoundStairsBottom` when Kane is on the stairs (MEASURED
   `dump_campaign.txt` line 267), and the pre-pass keeps the bound (it is 'passive') and drops the switch.
   In a round every heister would be warned and killed on the only way up. Cure: leave the three boxes out,
   `--m-drop "Specials!LevelBound!LevelBound_StairsBottom!*"` (in trial 2).
3. Not a fault, a choice (also in trial 2): `--m-drop "Locations/M06_A/M06A_Exit_Cutsequence_01a.zip"` leaves
   out the exit cut scene's set, 700 m from the garden. It takes with it the only classes and the one
   controller of this level that no stock Dog Days level and no played Dead Men map has: `ZCubeGridParticles`
   x1 and `ZParticleBox` x1 (rain boxes) and `LightToggle` x2 (MEASURED `firstkept.py`), one room, 139
   textures, 56 MB of `.TEX`. Side effect: the build then says `.hrd left out: the rigid bodies do not all
   come from one level` (5 of the level's 11 `ZHavokRigidBody` are in that set) - the state Retomoto plays in
   (READ re/maps.md 12: 'no .hrd load and play').

### 3.4 The navigation mesh

MEASURED (`mapcmp.py`, `nav2.py M06_A <stations>`, `kl_maps.py stations <kept build>`, preflight):
- `kl_pf4.convert` takes it: `kl_pf4.check` passes, 130 areas, 913 polygons, 338 waypoints. Dead Men's 67
  links become 31 (kind 2 kept; 27 of kind 1 and 9 of kind 3 dropped, as for every Dead Men mesh - READ
  tools/kl_pf4.py docstring 'KINDS'). The links are pairs about 1 m apart in height at the scaffold under the
  north bridge, at the two sniper perches and at the ring's median, plus a knot of 19 at one point
  (2715, 201, -13465).
- **25 connected parts; the largest (584 polygons, 10,733 m2) holds the whole campaign route by polygon
  edges alone**: pagoda floor (800, 635, 2350), both bridges, checkpoint 2, the garden to z -13,464, the tea
  house, all 48 polygons of the stair tower, the stairs' top (106, 2587, -10934), the four police stands, the SWAT place
  and the van's place (-2572, 2498, -7933). Reached from the pagoda with no link at all, and back from the
  van (`nav2.py`: 'edges only: reaches 584 polygons').
- NOT on that part: the water's edge under the bridge (part of 135 polygons, objective 020), the north
  bridge squad's ground (25 polygons), the two rings of the far highway (38 + 32 + 32 + 32 polygons: traffic),
  and the FA map's START row (the nearest polygon of M06_A's mesh is 6 m away and on another level).
- Size: 258,988 bytes; M06_FA_A's 258,640 and Retomoto's 603,332 ran (the preflight NOTE 'larger than any
  build that ran live' compares with an old table: READ tools/kl_maps.py `LIVE`).

### 3.5 What this level has that no map which ran has

`python tools/kl_maps.py first M06_A` lists 6 classes and 50 controllers against M01 / M03 - but before the
pre-pass, and without counting M02, M06 and Retomoto, which have run since. Restricted to what the pre-pass
keeps and compared with the four FA maps and the kept sides of M09_A / M09_B (MEASURED `firstkept.py`):

| class / controller | n | where | stock Dog Days | answer |
|---|---:|---|---|---|
| `ZCubeGridParticles`, `ZParticleBox` | 1 + 1 | the exit cut scene's weather boxes | 0 in no level | gone with 3.3 item 3 |
| `LightToggle` | 2 | the exit cut scene's work light | 0 | gone with 3.3 item 3 |
| `DiscoMove` | 76 | the moth swarms at the park lamps (`...ParkLamp_A_nn!Swarm_A_#nn`) | 478 in F01 F03 F04 F06 F07 F08 L01 .. | code every stock FA level runs |

Preflight RISK lines that stay in trial 2: `SoundSpline` x3 and `SoundVolumetricRandom` x4 on the ambience
objects - both loaded and ran for whole rounds on M06_FA_A (READ re/maps.md 11, 14.2).

### 3.6 The crash classes of CLAUDE.md, one by one

| class (CLAUDE.md) | this level | state |
|---|---|---|
| rooms / gates (`.buf` gate stride, kl2 0x48e910) | 6 rooms, 6 gates, 6 neighbour lists | preflight 'ok rooms': verify followed every gate, list, tree and box |
| `.oct` room trees, `.rmi` / `.rmc` | 8 (7) room sets, 13 (12) + 6 (5) boxes | verified by the build |
| navigation mesh missing / refused (0x5503da) | converted, check passes | 3.4 |
| `.ANM` copied | not copied; nothing taken from Dead Men without squads | with squads: Retomoto's sets |
| `.prm` lit descriptors, scatter | 939 lit meshes baked, 80 scatter objects converted (not drawn, as M06_FA_A's 145) | handled by kl_prm / kl_light |
| `.MAT` techniques | 15 fitted, 1 without shader (paper lantern) | look, not crash |
| `.sgd` | `HavokShatterOctree` 5,664 B and `ExplodableOctree` 3,376 B both present (M06_FA_A has no explodable octree; this level has one); no glass-connectivity section | preflight 'ok sgd' |
| `.buf` tail surface table / `.HVK` surface rows (0x4e5068) | 12 surface kinds renumbered | `kl_impact` 0 |
| bone ids (0x4c34b3) | 2 skeletons renumbered | `kl_impact` 0 |
| self-deleting inits (`OnlineSpeakTrigger`, `OnlineMoneyContainer`, `PhysicsLinkage`) | 8 `PhysicsLinkage`, all 8 name a ZLNKOBJ; none of the others | preflight 'ok self-delete' |
| KEYS chunks (0x81e714) | 85, all found | preflight 'ok KEYS' |
| `.prm` allocation (0x8e5bbd) and chunk table (0x607272) | 35.9 MB / 52,433 entries | below stock F07 / inside the limit |
| a second / no `FFCoverList` (0x6682c5) | 3.3 item 1 | cure known |
| unregistered controllers / type ids | none on the kept side (`IngameBriefing`, `ObjectiveReminder`, `MapControl` are in dropped subtrees) | - |
| `ZHavokCar` on a spline / road (never driven live) | 7 cars, all in dropped subtrees; `VehicleMoveOnRoadBehaviourRout` x5 and `ZRoad` x5 are in no stock Dog Days level | not carried; section 4 uses F07's key-framed van |
| `JumpPoint` fired by a level object for an FA player (0x8f40c9) | 7 campaign jump points, dropped | no jump is needed: one mesh part |

---------------------------------------------------------------------------------------------------

## 4. The round

### 4.1 Three candidates

**A. 'Exchange' - the campaign's own run: pagoda -> garden -> stairs -> highway -> van.** Below in full.

**B. 'Highway first' - Lynch's side.** Start on the ring at (-1920, 2516, -8001) with the police arriving,
down the stair tower into the garden for the loot, back up to the van. Uses the same ground twice: the
stair tower is 1.3 m wide and would be climbed down and up by eight heisters and by the AI, and the bots'
route doubles. No stronger than A in any point. Not recommended.

**C. 'A Walk in the Park' with the highway as the way out** - the FA round as it is (east start, cocaine
from the two gangs), but the escape is the van on the ring instead of the helicopter. It would be the true
'variant of the existing build'. BLOCKED as such by measurement: the FA level has no stair tower (1.4), so
from its south garden not even the player gets up to the van's place (corrected by the second agent: a
player could - see the correction under 0.2: stairs in the north-west and about 250 m of ring, behind IO's own
level bound on those stairs. What blocks C is the mesh and the distance, not missing ground); its mesh has no polygon above y 719;
and the other level, M06_A, does not hold the FA round's first third on its mesh (START row 6 m off it, the
north bridge approach a separate part of 25 polygons) and lacks the FA level's east stairs. Joining the
two meshes is not `kl_maps.nav_join` (that puts two meshes of DIFFERENT places behind one another; here both
cover the same lawns) but surgery on areas and edges that no tool does. So a highway finale means building from M06_A, which is candidate A.

### 4.2 The recommended round: A, 'Exchange'

Every place below is on the largest part of the navigation mesh unless marked (MEASURED `nav2.py`).
Distances are straight lines between the places named.

**Start - in the pagoda, the second the exchange goes wrong.** Eight START points on the pagoda's inner
floor, x 560..1040, z 2260..2440, y 635, in two rows of four, facing south (-z) down the bridge (GUESS: the
rows; the floor polygons 54 / 55 / 56 are MEASURED: x 495..1104, z 2059..2640). TRAITOR points on the north
half of the platform, about (700..900, 635, 2700) (GUESS). The inner room is 6.1 x 5.8 m and its way to the
south is one opening 1.5 m wide (mesh polygon 53: x 725..874; MEASURED `lootspots.py`) (corrected by the second
agent: 6.1 x 5.8 m is the box of a cross-shaped floor of 20.0 m2, see 1.1; between its walls the main room is about
6.8 x 3.2 m with four closed corner cells, and there is a second opening of the same width to the NORTH, polygon 40.
The two rows as proposed do lie on polygons 54 / 55 / 56, and 160 x 180 is the spacing of stock START rows: nearest
neighbours 129..160 in F07, 134..155 in M06_FA_A. MEASURED `sk_pagoda.py`, `sk_polys.py`, `sk_misc.py`): if eight do not fit,
four stand inside and four on the south veranda (x 273..1326, z 1905..2024). At the round-start event a timer (a) fires the
campaign's own `Gameplay!Enemy!01_Bridge!Activator_ShatterPavillionWindows` (one node to keep: an `AIDWrapper`
that sends 'DestroyWindows' to the pavilion's relay `SO0100_M06_Pavilion_01`), so the twelve windows burst
round the crew, (b) starts the garden squads and the bridge squad, whose
ground is north of the pagoda (they fire across the water), (c) starts the action music. Why it is 'in the
middle of the action': it is the campaign's own turning point, the crew stands on a platform in a lake
under fire with one way out, a 25 m bridge without a wall. No walk-in: the first cover is the pagoda's own
(6 `PlayerCoverCollision_pagoda` boxes, kept by the pre-pass).

**Loot - the exchange itself, then the garden's own shrines.**
- In the pagoda: 6 briefcases round the phone's place (802, 626, 2343) (GUESS: the spots; reach rules READ
  re/retomoto_loot.md via kl_fa_author's notes: horizontal distance <= radius + 40, no wall between). The
  briefcase prop exists: `kl_fa_loot.dress()` gives Retomoto's table stacks a briefcase, and M06_FA_A carries
  `Money!KillDrop!Briefcase_01..04` (texture `Items_Dynamic/Briefcase_Brass_01`, MEASURED `compare.py` /
  `tops.py M06_FA_A`).
- In the garden, one stack beside each of 9 props that are there (MEASURED `lootspots.py`): tea house
  `SO0100_M06_Tea_House_SP_02` (802, 173, -2477); shrines `PC0200_M06_Shrine_B_01` (13, 174, -1615), `_B_02`
  (-1972, 163, -6177), `_A_01` (-3479, 180, -6402), `_A_02` (1246, 180, -11631); statues `PC0200_M06_Statue_A_01`
  (-522, 177, -4807), `_02` (-1118, 202, -4657), `_03` (328, 192, -8833), `_04` (-292, 192, -9041). The props
  stand in holes of the mesh (0..254 from its edge), so each stack goes on the nearest polygon within reach
  (GUESS until placed by a tool that tests reach as `kl_fa_loot` does).
- Kill drops: the pooled stacks of F07 on the squad leaders, as M06_FA_A's gangs carry theirs.
- Values (GUESS, in the scale of Retomoto: 15 x 150,000 + 6 x 300,000): 6 x 300,000 in the pagoda,
  9 x 150,000 in the garden = 3.15 M. Stacks come from F07's pool (`FASpecials!DropMoney!MoneyStack_*`,
  `TeamModeDropMoney!TM_MoneyStack_*`: 108 + 25, READ re/retomoto_fa.md 2).
- Different from the sibling on purpose: there ALL loot is carried by people (no loot lies on the map, 1.4),
  here it lies at the place's own props.

**The beat in the middle - the stair tower.** The first heister into the campaign's own box at the foot
(`TriggerBox_OnStairs` (9, 689, -10945), or `TriggerBox_GoToStairs` (-1894, 178, -7446) for an earlier call)
does what the campaign does at the top: the lights under the highway go out (the list of
`Gameplay!Friendly!03_Highway!GeomDeactivator_LightsUnderHighway`), the police squads on the ring start, the
music's third layer comes in, and the stairs sniper `01_Squad_Sniper` (18, 1526, -11418) is unleashed above
the climbers. The EXITS_BANK trigger sits at the foot; the level-exit box that calls the van at the top
(106, 2587, -10934). The tower is a 1.3 m wide square spiral of 3.5 turns: the crew is strung out in single
file with a traitor's best chance of the round on the landings.

**Enemies.**

| where | who (the campaign's own objects) | n | state for a graft |
|---|---|---:|---|
| garden | `02_JapaneseGarden!02_`, `03_RetoMoto_Squad`, `01_Bridge!01_RetoMoto_Squad`, `02_JapaneseGarden!01_Squad_Sniper` | 4 + 3 + 3 + 1 = 11 | stay as they are by `kl_fa_author.squad_plan`'s rule (MEASURED `plan.py`); mini-cut-scene controllers stripped |
| garden | `04_RetoMoto_Squad`, `04_..#01`, `03_..#01`, `05_`, `06_RetoMoto_Squad_Singleplayer` | 3 + 2 + 2 + 3 + 4 = 14 | each holds one thing outside the rule's PLAIN set (`GateGroup` / `GatePath`, `LeapFrogBehaviourRout` x2, `DeactivateGeom`, `Filter`): need those nodes cut - an extension of the STRIP list, not new objects. `LeapFrogBehaviourRout` is in no stock Dog Days level: replace by the squad's `DefendBehaviourRout`s, which it also has (second agent: of `03_..#01` and `04_..#01` the defend box `40_DefendBehaviour\Pos#01` stands at (800, 626, 2353) and the leap-frog `Destination` at (782, 631, 2354): the pagoda's floor, the proposed START - as written this orders four men into the START room. And `02_RetoMoto_Squad`, one of the four that 'stay as they are', names objects of squads 03 and 04 in its own script lists, among them `04_RetoMoto_Squad\Gate\Way#01`, which the cut removes. MEASURED `sk_pagoda.py`, `sk_dump.py M06_A "02_JapaneseGarden!02_RetoMoto_Squad"`) |
| ring | `03_Highway!04_`, `05_`, `06_`, `07_PoliceCar` (police, USP), `08_PoliceSWATvan` (SWAT, MP5) | 10 + 5 | they arrive by `ZHavokCar` + `VehicleMoveOnRoadBehaviourRout` + `PassengerAnimPos` (never run in Dog Days; the Retomoto build left its `VSquad_*` out for the same reason, READ re/retomoto_fa.md 5). The police actors' own places are on the deck inside the bounds: (-3806, 2467, -7352), (-2076, 2518, -8634), (813, 2580, -9226), (-2103, 2527, -9990) (MEASURED; ASSUMED to be where they fight from: 80 m from where their cars start). The SWAT's own places (6987..7055, 3024..3031, 5373..5767) are on the far side of the ring; the campaign beams them to about (-6467, 2402, -6325), where they have to be put. Work: cut the car, the road rout and the seat helper, keep actors + `DefendBehaviourRout` + boxes. The cars can stand as scenery where the campaign parks them |
| ring, far | `03_Highway!01_Sniper` (-8601, 3506, 732), `03_Sniper` (6319, 3030, 5572) | 2 | 95 and 64 m from the pagoda, outside the level bounds, killed by script in the campaign: leave out (or keep ONE as the opening's threat - a live matter) |

25 yakuza + 15 police / SWAT = 40 against Retomoto's 63 (READ re/retomoto_fa.md 0) and the sibling's 14.
Weapons and skill through `kl_arms` (FORCE + skill by weapon class, as on Retomoto: READ CLAUDE.md 'kl_arms').
Models are Dead Men's own (24 'JPN', 10 'Police', 5 'SWAT': MEASURED `anmsets.py`) - the kinds that fought on
Retomoto's tower and street. Dead criminals return as police (7 AFTER_DEATH points) on the ring east of the
stairs' top, round (813, 2580, -9226) and (-95, 2575, -10309) (GUESS; both are on the mesh), and for the
first half of the round in the south garden round (566, 283, -12147) (GUESS). (Second agent: (813, 2580, -9226) is 6 m from the median's only gap, the crew's one way from the stairs to the van - police returning there stand in the choke point; and the three men of `01_Bridge!01_RetoMoto_Squad` stand beyond `LevelBound_PagodaBridge` on a mesh part of their own: they can be shot at from the pagoda, 40 m off, and never reached, so a kill drop on them is lost. MEASURED `sk_ring.py`, `sk_bounds.py`, `sk_squads.py`.)

**Escape - F07's key-framed van on the ring.** The campaign's van is a `ZHavokCar`; Dog Days has never driven
one of Dead Men's (READ re/map_escape.md 8). F07's `Animation/F07/F07_Escape_Vehicle_01.zip` can follow any
curve (every key has a place and a heading; `kl_map_escape.van_plan` / `van_prepare`, READ re/map_escape.md
8.2, 10.1, 10.2). Here: the ring's inner carriageway at radius about 8,250 (MEASURED `ring.py`: the campaign's
van at angle -161.8, radius 8,244; deck y 2,498 there).
- Waits out of play on the west arc, beyond `LevelBound_Highway_01` (33 m west of the stop).
- Drives in 60 m (7.2 s) along the arc, turning about 41 degrees, and stops at the campaign's own place
  (-2572, 2498, -7933) with its rear to the west: the boarding box rides 337 behind the origin (READ
  re/map_escape.md 9.2), i.e. on the side the crew comes from the stairs (GUESS: the direction; the other
  way round is the same work).
- Drives away east to south-east, at most 58 m to `LevelBound_Highway_02` (so 50 m, turning about 34
  degrees; F07's own away leg is 70 m). The planner needs a ROUTE: the three car maps took Dead Men's spline
  routes, which this level does not have - the route here is a list of points on the arc (a small new
  entry in `kl_map_escape`, section 5).
  *Corrected by the second agent (MEASURED `sk_bounds.py`, the boxes tested along the lane at radius 8,244):* the
  kill box of `LevelBound_Highway_02` begins 55.4 m east of the stop, but its two warn boxes begin 42.8 and 48.6 m
  east: a 50 m drive away ends inside both, with the crew aboard, and about 3 m short of the kill box with the
  van's nose. Out of every box: about 40 m at most (F07's own leg is 70 m, Hot Coffee's 52 m), or the two
  highway bounds are re-placed. To the west the warn boxes begin 15.5 and 23.0 m from the stop and the kill box
  30.6 m - the van's rear, where one boards, looks that way. The lane itself is clear: nothing of the kept
  geometry stands 25..220 over the inner carriageway between 60 m west and 50 m east of the stop (`sk_ring.py`).
- Boarding point = the van's rear at the stop; BOARDS trigger, the in-van camera and the outside camera
  ride with the archive. Outside camera place: the campaign's own `MissionObjective_030_Pip_Cam`
  (-1729, 3113, -8638), 6 m above the deck and 11 m from the stop (GUESS that it has clear sight).
- From the stairs' top to the van: 40 m along the deck, past the police stands - the Heat stretch.

**Level bounds.** The campaign's own, kept by the pre-pass: `LevelBound_Highway_01` / `_02` (the ring west
and east), `LevelBound_PagodaBridge` (north: the crew cannot leave the pagoda the FA map's way). Dropped:
`LevelBound_StairsBottom`. To author (F07's bound boxes, as Retomoto re-placed them): the car park south of
the stair tower (the mesh runs to z -13,464 there) and the ramp at the east (mesh to x 5,842), if a live look
shows they are open - the FA level closes its east side with `Level_Bounds!LevelBound_02` (3344, 304, -9775)
(MEASURED `flow.py M06_FA_A`). Whether the garden's walls (`M06_ParkWall_8m_*`) close the rest: NOT
ESTABLISHED offline.

**Music.** MEASURED (`python tools/kl_str.py list <Dead Men>/PC_Def.str M06`, `music.py`):
- `Music/InHouse/M06/RetoMotoAction_Layer1_Main_Loop.wav`, `..._Layer2_Bass_Loop.wav`,
  `..._Layer3_Intense_Loop.wav` - PCM, 171.4 s each, one interleaved set `LevelSetup/Level/M06_A/Music/
  RetoMotoAction` (32.9 MB). The campaign's `Specials!Audio!PlayMusic_RetoMotoAction` plays it and fades the
  layers by 20 `PlayMusicLayerFade` cues (bass at the first sniper's death, main at leaving the pagoda,
  intense when the SWAT come). NOT in the merged stream file (`<work>/build/PC_Def.str` and
  `<work>/build/v_bain/over_talk/PC_Def.str` hold only the next one): one more `kl_str.py build --extend`
  and one install by the live side.
- `Music/InHouse/M06/Retomoto_Ambient_V2_Loop.wav` - Vorbis, 196.1 s. Already in the merged file, because
  **the FA sibling plays it**: M06_FA_A's settings field 149 = `levelsetup/level/m06_a/music/
  retomotoaction_ambient_v2_loop`, field 150 (traitor) = `fa_all/music/fa_slashmixprison`. So the action
  track is what the owner has not heard on the garden.
- Wiring: keep the campaign's `PlayMusic_RetoMotoAction` node (and three of its fade boxes for the three
  beats) as Retomoto kept `Music!PlayMusic_TokyoAction` (READ re/retomoto_fa.md 6; the owner heard that one
  play: READ CLAUDE.md '17:35, BY EAR').

**Voice lines worth carrying** (MEASURED, the same `kl_str.py list`, 126 clips with 'M06'): Kane / Lynch
arguments `Dialog/M06/Dialogue/Situation/M06_Argue01` (9 clips), `M06_Argue02` (25), `M06_ArgueExit` (9) and
Lynch's `M06_OneLiners/M06_SmallTalk` (11) - material for the Kane - Lynch exchange the owner asked for
(kltalk); some are in the merged file already (`M06_SmallTalk_010/030/050_Lynch`, `M06_Argue02_002_Lynch`,
`M06_LynchShoot_010_Hero`). `M06_Negotiation` (20, Retomoto on the phone, several at 6.9 kHz) and
`M06_SniperAim` / `M06_Sniper` (18) are story lines that mean nothing in a heist: leave. The briefing and
announcer lines of the garden exist as FA lines (`Dialog/Multiplayer/Mission_Briefing/
FA_MissionBriefingJapGarden_01..03`, `Hitting_The_Score/FA_HittingTheScoreJapGarden_01`,
`Mission_Reminder/FA_MissionReminderJapGarden_01`, `FA_Menu/JapGarden_heist_01..06`): the settings of the
sibling name them and can be taken over.

**The AI heisters' route** (stations on the largest mesh part, MEASURED `nav2.py`; the order is the
proposal):

| # | station | place | leg |
|---|---|---|---|
| 1 | START, the pagoda floor | (800, 635, 2350) | - |
| 2 | the pagoda's loot (6 briefcases) | round (802, 635, 2343) | 0 m |
| 3 | south bridge | (800, 622, 1650) | 7 m |
| 4 | bridge landing = ENTERS / first garden box | (814, 392, -651) | 23 m |
| 5 | tea house | (802, 173, -2477) | 18 m |
| 6 | shrine B1, statues 1 / 2 (loot) | (13, 174, -1615), (-522, 177, -4807), (-1118, 202, -4657) | 12 - 32 m apart |
| 7 | shrine B2 (loot), middle of the garden | (-1972, 163, -6177) | 17 m |
| 8 | statues 3 / 4 under the highway (loot) | (328, 192, -8833), (-292, 192, -9041) | 35 m |
| 9 | stairs' foot = EXITS_BANK | (9, 689, -10945) | 19 m |
| 10 | landing half-way | (-18, 1650, -11462) | the spiral, y 320 -> 2569 |
| 11 | stairs' top = level exit (calls the van) | (106, 2587, -10934) | - |
| 12 | beside the van's stop, off its lane | round (-2400, 2500, -8300) (GUESS) | 40 m |
| 13 | boarding | the van's rear at (-2572, 2498, -7933) | - |

Pagoda to van: 30 m of bridge + 103 m of garden + the tower + 40 m of deck, about 175 m of ground and 22.5 m
up; the sibling's round is about 205 m and flat. (Corrected by the second agent: both figures are straight
lines, and the first leaves the spiral out. Over the mesh, portal to portal: 30 + 19 + 121 + 75 in the tower + 16 to
the median's gap + 36 = 296 m; the sibling's round measured the same way is 257 m. The new round is the longer
one, a quarter of it single file. MEASURED `sk_misc.py`.) One mesh part: no hook teleport as on Retomoto, no joined
parts as the bank needed (READ re/bots_retomoto.md 0, re/maps.md 14.5).

### 4.3 What makes it different enough to keep beside 'A Walk in the Park'

| | A Walk in the Park (M06_FA_A, on the tab) | Exchange (M06_A) |
|---|---|---|
| start | east entrance, walk in over the north bridge | in the pagoda, under fire |
| ground | lake, island, south garden: flat | bridge, south garden, 22.5 m of stair tower, the highway ring |
| loot | carried by two gangs and two bosses | briefcases in the pagoda, stacks at shrines and statues |
| enemies | 14 dealers, the boss helicopter | 25 of Retomoto's men, 15 police / SWAT on the ring |
| way out | helicopter in the garden | van on the highway |
| music | the ambient loop | the three-layer action theme |
| shared | the south garden between z -650 and z -8,000 (about 70 m of either route), the look, the night | |

It is a different ROUND. It is not a different PLACE: the owner will know every lawn. That is the whole
case for and against.

---------------------------------------------------------------------------------------------------

## 5. What has to be authored

### 5.1 The objects (kinds READ from tools/kl_fa_author.py and re/retomoto_fa.md 2: every one a stock F07 object, kept by name, re-placed and re-wired; none is created)

| kind | from | the level already holds |
|---|---|---|
| settings, `IsMultiplayerLevel`, speakers, briefing trigger, `AIMonitor`, escape monitor | F07, position-free (kept by `kl_fa.host_keep` anyway) | - ; the sibling's briefing / announcer line names can be copied in |
| 8 START, 4 TRAITOR, 7 AFTER_DEATH spawn points (+ the UCC / team kinds) and the 16 player groups | `FASpecials!SpawnPoint!*`, `Heroes!*` | nothing (0 spawn points); places: 4.2 |
| spawn cameras, loot and escape markers (`PointOfInterest`), ENTERS / EXITS triggers | `FASpecials!POI!*`, `FASpecials!PIP!*` | nothing; the campaign's `MissionObjective_*_Pip_Cam` places are usable camera spots |
| 15 loot stacks + kill-drop pools, `OnlineMoneyCtrl` values | `FASpecials!DropMoney!*`, `TeamModeDropMoney!*`, dressed by `kl_fa_loot` | the props to stand them at (9 + the pagoda) |
| round-start timer and its lists | `Gameplay!010_FirstFight!RivalMercVan!Timer` + wrappers | the pavilion's shatter relay (kept geometry); the squads' start routs |
| 'beat' trigger at the stairs | `Gameplay!030_AfterLoot!tbExitFinancialAlley` (`TriggerBox`) | the campaign's box places; the lights list (to re-keep one node: `GeomDeactivator_LightsUnderHighway`) |
| exit trigger + van + boarding + BOARDS + cameras | `Gameplay!EscapeSetup!otrExitLevel`, `Animation/F07/F07_Escape_Vehicle_01.zip` | the van's place and the road; no route |
| level bounds | the campaign's three (kept) + F07's `Specials!LevelBound!*` where a side is open | 3 of the 4 are right as they are |
| cover | - | 237 cover boxes, the cover list (3.3), 18 no-cover and 17 player-cover boxes: all kept |
| police / guards | the campaign's squads | 4 squads (11) as they are, 5 garden squads (14) and 5 ring squads (15) after cutting (4.2) |
| music | the campaign's `PlayMusic_RetoMotoAction` + 3 fade boxes | the nodes; the clip must be merged into the stream file |
| AI heisters | `kl_fa_bots` squad on the stations of 4.2 | the mesh, in one part |

### 5.2 Size of the work: about 0.4 of Retomoto (0.35 .. 0.5)

Retomoto = 1.0 was: two campaign levels chained (three Havok parts, `nav_join`, the `.prm` limit), a join
between two places with a hook part, a start on a ledge behind glass with a bomb sequence, a staged tower
fight, a street layer, the van, loot dressing, enemy tuning, and bots through two mesh parts with a second
hook part.

Less here: ONE level and one clean graft (no chain, no join, no hook part of any kind); one mesh part (bots
without teleport); no interior, no doors, no paired room states; the start needs one message to an existing
relay instead of a bomb sequence; the level bounds exist; 40 enemies against 63; every size below what ran.

Not less: `kl_fa_author.py` is written round Retomoto's tables and names (`SQUADS`, `PLACE`, `A_MAP` / `B_MAP`,
`wire()`), so the layer needs either that file opened up to a second map or a sibling module with its own
tables (READ tools/kl_fa_author.py lines 86 - 200, 542 - 830) - the largest single item; every place in 4.2
marked GUESS wants a look in the game; the ring police need the 'arrive by car' part cut out of their
squads; the van needs a route input `kl_map_escape` does not take yet (the curve itself is nothing new:
41 degrees in 60 m here, 90 degrees in the 60 m of the Hot Coffee build, READ re/map_escape.md 10.4); the
stream file must be rebuilt and installed for the music.

### 5.3 Steps to a first load, in order

1. Two changes to the build call, no authoring: `'FFCoverList'` in `kl_maps.PASSIVE`; `m_drop` of
   `Specials!LevelBound!LevelBound_StairsBottom!*` and `Locations/M06_A/M06A_Exit_Cutsequence_01a.zip`
   (= `trial2.py`; verify must still say exactly the ten FA problems).
2. First load WITHOUT a layer (the lead's live side): that build kept, `python tools/kl_fa_author.py hero
   <kept build> <out> 800 635 2350` (the test aid that puts `Heroes!Hero_01` somewhere; it is not tied to
   Retomoto: READ kl_fa_author.py `move_hero`), direct boot. Expected: the garden without enemies. It settles
   the look (lanterns, lights, grass), that a player can walk pagoda -> bridge -> garden -> stairs -> ring,
   and which sides are open.
3. The layer's tables for this level (spawn rows, loot, triggers, bounds) + the wiring; `kl_fa.check` to
   0 CRASH / 0 BROKEN; direct boot, then one Arcade round standing still.
4. Squads: the four that stay, then the STRIP extension for the other ten; `kl_arms`.
5. The van: a route on the ring's inner carriageway into `kl_map_escape` (`van_plan` lane test on the
   level's collision, `van_prepare`, `van-check`).
6. `kl_graft.py lighten`, `kl_chars.py wardrobe`, `kl_maps.py audit` (the order of re/maps.md 14.1).
7. Bots (`kl_fa_bots` on the stations), then the cover and route steps the tab's maps have.
8. Stream file with the action set; the music node and its three fades.
9. Menu: a slot. The 'Dead Men maps' page has one entry left (F07); a further page of nine is foreseen
   (`[Redirect.3]`, READ re/expansion.md lines 77 - 83) - where this map goes depends on what the other
   campaign places of this study get.

---------------------------------------------------------------------------------------------------

## 6. Risks, and what only a live run can settle

Risks found offline (each with its cure above): no cover list after the pre-pass (3.3.1); the bound on the
stairs (3.3.2); three first-time classes in the exit set (3.3.3); the ring police as the campaign has them
cannot come (4.2); the van's drive away passes `LevelBound_Highway_02` with players aboard if it is longer
than 58 m (whether a passenger of a key-framed van is ended at a bound is an open live check for M02 / M03
too: READ re/map_escape.md 10.4, V5).

Only the game can settle:
1. Whether a level WITHOUT an `FFCoverList` loads and what its cover boxes do (only if the cure is not taken).
2. The look at night: paper lanterns not drawn, 80 scatter objects (grass) not drawn, 380 Dead Men lights
   and 939 baked meshes under F07's post filter - as M06_FA_A looks on the tab (ASSUMED the same: same
   materials, same converter), but the pagoda and the ring were never looked at.
3. That a PLAYER can walk the route the mesh promises: the bridge's landing at (814, 392, -651), the stair
   tower's flights (1.3 m wide on the mesh), the step from the tower's top onto the deck, the median of the
   ring between the top and the van.
4. Which sides of the garden and of the deck are open (bounds to author): the car park south of the tower,
   the east ramp, the 26 m wide ring beyond the two campaign bounds.
5. The pavilion's windows: that the relay's message breaks them for an FA round (the form is Retomoto's
   window, which worked: READ re/retomoto_fa.md 6) and that eight players inside are not hurt by it.
6. START on a 6 x 6 m floor: eight players and their spawn cameras in the pagoda.
7. The cut squads: that a police squad whose car, road rout and seat helper were removed stands and fights
   from its own place; `kl_arms`' rows on the three sniper actors.
8. The van on the arc: a curved drive of this van has been played (Hot Coffee; the owner: 'the van is almost
   perfect', READ CLAUDE.md) - here: that it clears the median and the parked police cars, that the deck's
   slope (it falls about 35 units per 10 degrees of arc towards the west, 2.4 %: MEASURED `ring.py`; the van is
   not pitched to a slope, READ re/map_escape.md 10.2) does not show, the camera's sight.
9. AI heisters on the spiral (seven bots in single file on 1.3 m flights; Retomoto's bots took narrow
   stairs DOWN, READ re/bots_retomoto.md 1 - corrected by the second agent: that section is a plan, headed
   'none of it seen in the game') and their boarding at the van's rear on the deck.
10. Three-layer `PlayMusic` with fades in a Fragile Alliance round (Retomoto's two-layer one played).
11. Whether the round is good: forty enemies over 175 m for one human and seven bots, the length of the
    climb, the traitor's chances on the stairs. The owner's call.

---------------------------------------------------------------------------------------------------

## 7. Verdict: feasible as a variant

For the owner, in plain words. The campaign chapter 'Exchange' is not another park: it is the very garden
of 'A Walk in the Park' that already plays on your tab - nine tenths of its ground are the same, at the
same hour of the same night. What the campaign adds is everything ABOVE and at the EDGE of it: you start in
the pagoda in the middle of the lake as the deal goes wrong, you fight Retomoto's men south through the
garden, you climb the tall stair tower at the end, and the round finishes as a street fight with police on
the highway ring, where a van takes you away - with the chapter's action music instead of the quiet loop.
That is a real second round, and technically it is easy by our standards: the level converts cleanly on the
first try, it is no bigger than the maps that already run, the AI heisters can walk it from the first step
to the van without any trick, and it needs neither two levels nor a hook part, so it is well under half the
work Retomoto was. But it cannot be made by adjusting the park you have (that level has no stair tower: the
way up to the highway is simply not there, and its AI knows nothing above the lawns); it has to be built
from the campaign level with its own Fragile Alliance layer. So: worth having as a variant of the park, and
the cheapest of the campaign places to make - but the one that shows you the least you have not seen. If
the others (the bank the campaign way, the club, Havana, the prison) bring new places, do those first and
this one when a quick win is wanted.

---------------------------------------------------------------------------------------------------

## 8. The scripts, for whoever checks this

All in `G:/kl_scratch/cfa_park/`, run from the repo root with `python <script>`; they only read the stock
archives (through `kl_prpjoin.level_zip`) and write their own cache under `cache/`. `geo.py` is the shared
loader (property tree, entity places by `kl_maps.world`, static collision triangles from the `.HVK`, mesh
through `kl_pf4.convert` and `kl_maps.NavParts`) and the picture canvas.

| script | what it prints (output kept as) |
|---|---|
| `tops.py <level>` | every top-level subtree: nodes, class, extent, classes and controllers, pre-pass DROP / keep (`tops_M06_A.txt`, `tops_M06_FA_A.txt`) |
| `dump.py <level> <out> <prefix> ...` | every node of the named subtrees with its controllers' values (`dump_campaign.txt`, `dump_fa.txt`) |
| `flow.py <level>` | squads with actors, weapons and places; vehicles; trigger boxes with targets; spawn points; names with FA / Online / ... (`flow_M06_A.txt`, `flow_M06_FA_A.txt`) |
| `compare.py` | same-named objects, textures, member sizes, scene block, lights of both levels (`compare.txt`) |
| `mapcmp.py` | collision floors of both levels cell by cell; both navigation meshes with their parts (`mapcmp.txt`) |
| `nav2.py <level> "x,y,z:label" ...` | links by kind with their ends; each station's polygon and part; what is reached from the first station by edges / + kind-2 links / + every link (`nav2_M06_A.txt`) |
| `stairs.py`, `stairs_fa.py`, `stairs_objs.py` | the stair tower's polygons against the stairs' level bound; the tower in the FA level's collision and objects |
| `ring.py` | the ring's centre, radial profile and heights, the campaign's places as angle / radius, arc lengths (`ring.txt`) |
| `props.py <level>` | prop name stems with counts and extents; level-bound boxes with half extents (`props_M06_A.txt`) |
| `lootspots.py` | shrines, statues, tea house, pagoda against the mesh; pagoda / deck / garden polygon sets (`lootspots.txt`) |
| `scripted.py` | scripted objects in the kept geometry and who names them; hidden-at-load entities; cover boxes by height (`scripted.txt`) |
| `plan.py` | `kl_fa_author.squad_plan`'s rule on M06_A (`plan.txt`) |
| `firstkept.py` | first-time classes / controllers after the pre-pass against every map that ran (`firstkept.txt`) |
| `coverlist.py [archive ...]` | `FFCoverList` objects in stock levels and built archives |
| `anmsets.py` | animation sets, weapon templates, actor kinds the squads name (`anmsets.txt`) |
| `music.py`, `leftovers.py` | sound names behind `PlayMusic` / settings fields; FA traces in `.SND` / `.LOC` (`music.txt`, `leftovers.txt`) |
| `trial2.py [--keep]` | the second trial graft (3.3) |
| `pic.py` | the five pictures |

---------------------------------------------------------------------------------------------------

## Verification (second agent)

2026-10-11, second agent (skeptic). OFFLINE: the game was not started, nothing was installed, no existing tool
was edited, nothing was committed. Corrections are IN PLACE above, each marked 'corrected by the second agent' /
'second agent'; this section lists what was checked and how. Nothing that stands was rewritten.

- My scripts (all new; none of the first agent's was run for a result - `geo.py` and its cache were not used):
  `G:/kl_scratch/cfa_park/skeptic/sk*.py`, outputs `sk*.txt` beside them. `sk.py` is the loader: entity places by
  `kl_maps.world`, collision triangles of EVERY placement of the `.HVK` (the first agent took only placements
  below `Locations/*`), convex and rigid placements as boxes, the mesh through `kl_pf4.convert` and parsed there.
- My trial builds: `<work>/build/cfa/park/skeptic/` - `F07+M06_A sk1` (= trial 1), `F07+M06_A sk2` (= trial 2),
  `light_sk2`. Archives deleted; `result.json`, `log.txt`, `graft.txt`, `preflight_run.txt`, `lighten_log.txt` kept.
- Two kinds of test that the report did not have. (a) THE ROUTE IN THE COLLISION, not on the mesh: `sk_walk.py`
  walks the route's portal midpoints and looks every 25 units for a floor within 90 of the mesh and for anything
  that is not floor in a 40 x 40 column from floor + 45 to floor + 150; `sk_pagoda.py` draws a top-down slice of
  the collision's walls in that band (its picture of the pagoda shows the walls, so the test does see walls).
  (b) FLOOD FILL over collision floors (`sk_flood.py`: 40-unit cells, step 45, walls NOT tested - optimistic, so
  'not reached' is certain and 'reached' only says the floors are continuous).

### Verdict after the checks: feasible as a variant (unchanged)

The measurements the verdict rests on are right: every number I rebuilt came out the same. What changes is the
design, not the feasibility: the START room is smaller than stated, the walk is longer than stated and longer
than the sibling's, the way from the stairs to the van has one 2.4 m gap, the van's drive away as proposed ends
in the level bound's warn boxes, and the case 'the FA level has no way up' is wrong as stated (it has one, which
IO bounded off). None of it blocks. Effort: I would say 0.45 (0.4 .. 0.55) rather than 0.4 - the squad work is
larger than 'cut one object each' (ASSUMED from the cross-references found, below); that is a judgement, not a
measurement. Priority as the report has it: last among the campaign places, since half of the walk is ground
the owner already plays.

### Confirmed (25)

1. **The trial graft, re-built twice.** `python G:/kl_scratch/cfa_park/skeptic/sk_trial.py 1 --keep` (the plain
   pre-pass): verify problems 10, all 'FA:' (1 CRASH settings, 9 BROKEN); `fa` {CRASH 1, BROKEN 9, DEGRADED 4,
   NOTE 1}; dangling 0; 19,157 entities; 7 rooms; 1,589 textures; 1,002 materials; 53,959 chunks; archive
   326.8 MB; `.prm` 79.5, `.TEX` 392.7, `.ANM` 21.6, `.fxc` 17.8 MB; mesh 258,988 bytes. `sk_trial.py 2 --keep`
   (FFCoverList passive + the two m-drops): the same 10 problems; 18,626 entities; 6 rooms; 1,450 / 927; 52,432
   chunks; 286.7 MB; `.prm` 78.2, `.TEX` 336.5 MB; `.WAV` 19,890,512 bytes; note '.hrd left out'. Identical to the
   report in every figure. Log lines of 3.1 found in my `log.txt` (18848 of 26239 chunks appended to 35101,
   700 -> 1002 materials, 1188 -> 1589 textures, 939 baked meshes, 80 scatter, `.rmi` 1 + 13, 8 room sets,
   6 gates, 49 KEYS blocks, clips +0); one figure differs: 'shaders: 14 materials fitted' in my trial 1 (report: 15).
2. **Lightened sizes, re-run** on my trial 2: `python tools/kl_graft.py lighten ... --load trim,slim,fxc` ->
   `.prm` 78.2 -> 35.9 MB, `.TEX` 336.5 -> 146.1 MB, shader cache 242 -> 117 entries (8.13 MiB), archive
   127.6 MB; `python tools/kl_impact.py <lightened>`: problems 0.
3. **Preflight, re-run** on my trial 2: CRASH 2 (verify, settings), RISK 11 (9 FA layer + `SoundVolumetricRandom`
   x4 + `SoundSpline` x3), NOTE 64. `kl_maps.py stations`: 913 polygons, 31 links, 25 parts, largest 584.
4. **The pre-pass**: `kl_maps.campaign_drop('M06_A')` = 238 subtrees / 1,213 nodes dropped (Specials! 99,
   Gameplay! 868, CutScenes 108, COOP! 94, AI_Players! 12, Traffic! 32), 10,637 kept (`sk_facts.py`).
5. **The cover list**: M06_A's only `FFCoverList` is on `Specials!CoverPoints!CoverControl` and the pre-pass
   drops it; my trial 1 holds 0 `FFCoverList`, my trial 2 exactly 1 (`sk_facts.py`, `sk_build.py` on both kept
   archives). Added: stock F07's own cover list has the SAME top-level name `Specials!CoverPoints!CoverControl`
   (`sk.Lv('F07')`), so an authored build that keeps F07's `Specials!*` meets a name clash as well as a second
   list - the report's 'keep ONE' is the right warning.
6. **The stairs' level bound**: `LevelBound_StairsBottom!Bound` (-197, 659, -10960) half (100, 200, 100) holds the
   landing of polygons 808 / 809, `Warn01` the flight 807; both kept by the pre-pass; the only object that names
   them besides the bound itself is `...05_RetoMoto_Squad\GeomDeactivator_LevelBoundStairsBottom`, dropped
   (`sk_facts.py` reference index, `sk_bounds.py` point-in-box tests). Gone in my trial 2 (3 `LevelBound` left).
7. **The mesh numbers**, parsed with my own reader: M06_A 258,988 bytes, 913 polygons, 130 areas, 338 waypoints,
   31 of 67 links kept (27 of kind 1 and 9 of kind 3 dropped), 19,304 m2, 25 parts, largest 584 polygons =
   507 (garden, 6,801 m2) + 29 + 48 (deck, 3,583 m2), heights 183..2624. M06_FA_A 954 polygons, 14 areas, 9,389 m2,
   7 parts, largest 936 at y 114..635, no polygon with a vertex above y 900 (highest 720). `sk_nav.py`, and the
   one-off at the end of `sk_compare.txt`. The mesh inside my built archive is byte-identical to
   `kl_pf4.convert(M06_A)` (`sk_build.py`).
8. **'One part, by polygon edges alone' means what the engine does with it.** 258 of the mesh's neighbour fields
   are negative-coded and every one of them joins two AREAS (none of the 1,760 plain ones does); by plain fields
   alone the mesh falls into 130 parts = its areas. kl2 0x63eaed..0x63eafa decodes a negative field (-2 - x) and
   builds the same portal record for it as for a plain one (READ `python debug/dasm.py 63e9e0 240`), and the
   path search's polygon step walks those portals (0x5ce212..0x5ce2e1). Every stock Dog Days level and every
   Dead Men map that ran is built the same way (F07: 84 areas, 178 area-crossing edges; M09_B: 60 / 138;
   `sk_stock.py`). So the 584-polygon part is one piece for the game's search too. No neighbour field is one-way.
9. **The route on the mesh**: pagoda floor, south bridge, landing, tea house, stairs, top, van place, 'beside the
   van', both ring AFTER_DEATH places, the TRAITOR place and Lynch's checkpoint all lie over a polygon of the
   584-part (0..5 off in height; the tea house's origin 47 below the mesh and the stair boxes 23..103 above it:
   those are a prop's origin and trigger-box centres); a way exists
   in both directions; NOT on it: objective 020 under the bridge (part of 135), the FA START row (`sk_nav.py`).
10. **The route in the collision** (new test): 301 m of portal midpoints pagoda -> veranda -> landing -> tea house
    -> garden middle -> stairs -> top -> van, 1,271 samples: a floor within 90 of the mesh under every one, and
    NOTHING in the body column at any (`sk_walk.py`). The flood fill agrees (`sk_flood.py M06_A ...`: landing after
    30 m, stairs' top 188 m, van place 245 m of cells).
11. **No scripted wall on the route.** The campaign's `Blocker_LeavingTooEarly` and three `CoopInvisibleWall`
    boxes (`COOP!Lynch_Blocks!LynchBlock_Stairs` at the tower's top (209, 2765, -10924), `_Left`, `_Right`) are in
    dropped subtrees; my trial 2 holds 0 `Blocker`, 0 `CoopInvisibleWall`, 0 `GateGroup` / `GatePath`,
    0 `ActivateGeom` / `DeactivateGeom`, 0 `TriggerBox`. Every 'Door' of the level is a car door in a dropped
    squad; the 'Gate' names are the torii, two park-wall gates (south (800, 180, -13600), east (6000, 180, -3600))
    and the exit set. (`sk_names.py M06_A door gate fence barrier block`, `sk_build.py`.) The stair tower is
    closed on all four sides between its first landing and its top (`sk_tower.py`): `StairsMIDDLE_EXIT` is a
    piece's name, not an exit.
12. **Same place as the FA map**: floors of every placement, 1 m cells, floors of a column merged within 30:
    M06_A 95,686 cells, 85,758 (90 %) in M06_FA_A; M06_FA_A 100,190, 85,783 (86 %) in M06_A; the deck band
    2300..3400 shared to 99 %. (The report: 91 % / 87 % with unmerged floors of `Locations/*` only.) `sk_compare.py`.
13. **Textures**: 1,078 ids / 456 names in M06_A, 964 / 405 in M06_FA_A, 358 names in both; 98 only in M06_A, 47 of
    them with 'm07' in the name (`sk_compare.py`, `kl_texmat.read_tex`).
14. **No stair tower in the FA level**: 7,180 collision triangles with their centre in the footprint in M06_A
    (the same number), 52 in M06_FA_A; no object named `*FreeW_Stairs*` there; the flood fill of M06_FA_A finds no
    floor within 120 of the campaign's stair boxes (`sk_compare.py`, `sk_flood.py M06_FA_A`).
15. **The campaign's places**: `CP_01_PosP1` (802, 623, 1702), `CP_01_PosP2` (-1920, 2516, -8001), `CP_02_PosP1`
    (814, 392, -651), `CP_03_PosP1` (-180, 1605, -11425), objective 010 (795, 627, 2355), `TriggerBox_OnStairs`
    (9, 689, -10945), `TriggerBox_Disablelights` (106, 2633, -10943), the `EndOfLevelTrigger` box (-2601, 2610, -7974)
    half (492, 142, 408), `SceneChanger` -> `Locations\M07_A\M07A_Main.zip`, seven `ZHavokCar` at the places
    given, all in dropped subtrees (`sk_facts.py`, the one-off after it).
16. **Enemies**: 45 `ZSoldier` controllers, 42 of them in the 18 `ZSquadScript` squads under `Gameplay!Enemy!`
    (+ 1 `ZCivilian`, + 3 friendly); weapons read from the actor nodes: 24 `Smg_MP5-A3_01_Light`, 3 `Sn_Rem700_01`,
    10 `HG_HK_USP_01`, 5 `Smg_MP5-A3_01`; animation sets Thug 27, Army 15 (`sk_squads.py`, `sk_guns.py`).
17. **The squad rule**: my own listing of each squad's controllers gives the same four that hold nothing outside
    `kl_fa_author.PLAIN` + `STRIP` (02, 03, `01_Squad_Sniper`, `01_Bridge!01_RetoMoto_Squad`: 4 + 3 + 1 + 3 = 11)
    and the same reasons for the other 14 (`sk_squads.txt`; constants READ in tools/kl_fa_author.py).
    `python tools/kl_maps.py first M06_A`: `ZRoad` x5, `VehicleMoveOnRoadBehaviourRout` x5, `LeapFrogBehaviourRout`
    x2 'stock Dog Days: 0 in NO LEVEL' (all three ARE registered in kl2.exe: `J.schema('dd').controller`).
18. **First-time classes after the pre-pass**: the tool's own second block says it - `ZCubeGridParticles` x1,
    `ZParticleBox` x1, `LightToggle` x2, all under `M06A_Exit_Cutsequence_01a.zip`, and `DiscoMove` x76
    (`python tools/kl_maps.py first M06_A`, kept as `skeptic/first_M06_A.txt`). Lights kept: 182 omni, 122 spot,
    76 square spots (the same list).
19. **Music**: `python tools/kl_str.py list <Dead Men>/PC_Def.str M06` = 126 clips; the three PCM layers
    `RetoMotoAction_Layer1_Main / Layer2_Bass / Layer3_Intense_Loop`, 171.4 s, one set
    `LevelSetup/Level/M06_A/Music/RetoMotoAction` of 0x1f643a0 = 32.9 MB; the merged file
    `<work>/build/v_bain/over_talk/PC_Def.str` lists 19 M06 clips, the ambient loop among them, none of the three
    layers. `PlayMusic_RetoMotoAction` is in the dropped `Specials!Audio!`; the level holds 22 `PlayMusicLayerFade`
    (the report says 20 cues).
20. **No Fragile Alliance leftovers in the tree**: 0 `ZSpawnPoint`, 0 `ZOnlinePIPCameraPoint`, 0 settings
    classes, no controller with 'Online' or 'Spawn' in its name; names with FA: the two
    `SO0100_M06_Pavilion_BridgePart_B__FA_01 / _02`, `M02_FA_LightTube_Shatter_01`, and the systems'
    `IngameFragileAllianceKILLERCamera` (`sk_facts.py`).
21. **The ring**: from the collision, round (0, -100): inner carriageway radius 7,900..9,200, outer
    9,400..10,550, deck height on the van's lane 2,348 at 42 degrees west of the stop, 2,497 at the stop, 2,618 at
    35 degrees east (2.4 %); the van at radius 8,244; the campaign's bounds 33 m west and 57 m east of the stop to
    their centres; the stairs' top at radius 10,835, outside the outer deck's edge (`sk_ring.py`).
22. **The pavilion's windows break without an animation**: `SO0100_M06_Pavilion_01` @RelayMessageList
    ('DestroyWindows' -> the twelve window groups), each window group @RelayMessageList ('DestroyWindows' ->
    'Activate' -> its own `While_window_*`, which carries `HavokShatter`); `AIDWrapper`, `RelayMessageList`,
    `HavokShatter`, `LevelBound`, `PlayMusic`, `PlayMusicLayerFade` are all registered in kl2.exe
    (`sk_dump.py M06_A SO0100_M06_Pavilion_01`, `J.schema('dd').controller`). No Dead Men `.ANM` is involved.
23. **The escape vehicle exists and moves without Dead Men's `.ANM`**: F07's `Animation/F07/F07_Escape_Vehicle_01.zip`
    is key-framed by a KEYS chunk of F07's own `.buf`, re-keyed along a curve by `kl_map_escape.van_plan` /
    `van_prepare` on three maps (READ re/map_escape.md 8, 9.2, 9.3, 10.2; seen live on Hot Coffee and the bank,
    READ CLAUDE.md). It is NOT in a plain graft (my trial 2: 0 `OnlineEscVehicleController`, 0 `ZAnimatedVehicle`,
    only the monitor): the layer has to keep it, as the report's 5.1 says. `van_plan` takes Dead Men's two spline
    routes as its input (READ re/map_escape.md 10.1), which this level lacks - the report's point stands.
24. **The loot props** stand 0..99 units from an edge of the largest mesh part at garden level (tea house 0,
    statues 56..59, shrines 81..99; the report: 0..254), so a stack on the nearest polygon is within reach of each
    (`sk_misc.py`).
25. READ claims looked up: `kl_maps.PASSIVE` and `campaign_drop`'s rule (tools/kl_maps.py lines 98, 122..154);
    `Select`: `m_drop` wins over `m_add` (tools/kl_graft.py line 860); `kl_fa_author.move_hero` is a general
    test aid; `kl_fa_author` is tied to Retomoto by `A_MAP`, `B_MAP`, `PLACE`, `JOIN_BOX`, `SQUADS`, `CAMPAIGN_KEEP`
    (lines 81..349).

### Corrected (12; each also marked in place)

1. **'The FA level has no way up to the ring' (0.2, 4.1 C, the first blocker of the returned result).** Wrong
   as stated. M06_FA_A's collision has stairs from the garden to the ring in the north-west
   (`SO0201_M06_FreeW_Spiral_WithStairs_A_01`) and a continuous deck from there to the campaign van's place; IO
   closed the stairs with `Level_Bounds!LevelBound_Stairs_01` (bound at (-3026, 1010, 7277), warn boxes at y 691
   and 915). `sk_flood.py M06_FA_A "-1687,133,-6542:..." "-2572,2498,-7933:..." --trace`: REACHED after 435 m of
   cells, climbing at (-3060, 533, 6540) .. (-3380, 2003, 7100), then about 200 m of ring. True and re-measured:
   no stair tower in the south, no mesh above y 720. So candidate C is blocked by the MESH (the AI) and by the
   distance, not by missing ground; the recommendation (build from M06_A) is unchanged.
2. **The pagoda's inner floor (1.1, 4.2).** Not 6.1 x 5.8 m: a cross of three polygons, 20.0 m2 (corridor
   1.5 x 5.8 m + two wings 2.3 x 2.5 m); the main room is about 6.8 x 3.2 m between its walls, with four closed
   corner cells; openings of 1.5 m to the south AND to the north. The eight START points as proposed do fit, at
   the spacing of stock rows. `sk_polys.py`, `sk_pagoda.py`, `sk_misc.py`.
3. **Two squads are ordered onto the START floor (4.2).** `02_JapaneseGarden!03_RetoMoto_Squad#01` and
   `04_RetoMoto_Squad#01` (2 + 2 men): their `40_DefendBehaviour\Pos#01` is (800, 626, 2353), their leap-frog
   `Destination` (782, 631, 2354). 'Replace the leap frog by the squad's own defend rout' sends them into the
   pagoda. They need new boxes (or to stay out).
4. **'Four squads stay as they are' needs one more look (4.2, 5.1).** The rule's count is right, but
   `02_RetoMoto_Squad`'s script lists name objects of squads 03 and 04 (`03_..\10_DefendBehaviour_Sneak`,
   `03_..\TriggerBox_Hunt`, `04_RetoMoto_Squad\Gate\Way#01`); the last is one of the gate objects the report
   cuts from squad 04. `sk_dump.py M06_A "02_JapaneseGarden!02_RetoMoto_Squad"`.
5. **The bridge squad cannot be reached (4.2).** Its three men stand 40 m north of the pagoda, beyond
   `LevelBound_PagodaBridge` (its warn boxes begin on the north bridge at z about 3300) and on a mesh part of
   their own: targets, not part of the walk; a kill drop on them is lost. `sk_bounds.py`, `sk_nav.py`.
6. **One crossing of the ring's median (1.1; new).** Between the stairs' top (outer deck) and the van (inner
   carriageway) the median `SO0201_M06_MiddleConcrete_01` has one gap, x 80..320, 2.4 m in the collision in both
   of its states (`MiddleConcrete_Whole` shown at load, `_Remains` hidden: the gap does not depend on anything
   breaking), 186 on the mesh. Dead Men's mesh also let the AI vault the median at four places (one-polygon parts
   17..20 on its top, at x 1340, 610, -468, -1355: a kind-1 link up and a kind-2 link down each); kind 1 is
   dropped by the conversion, so for the AI heisters and the police the gap is the only crossing. Whether a
   PLAYER can vault a 1 m median in Dog Days: not known. `sk_ring.py`, `sk_median.py`, `sk_links.py`.
7. **The proposed police return points are in that choke point (4.2).** (813, 2580, -9226) is 6 m from the gap.
8. **The van's drive away (4.2).** The level bound's WARN boxes begin 42.8 and 48.6 m east of the stop, its kill
   box 55.4 m (not '58 m to the bound'): 50 m ends inside both warn boxes with the crew aboard. West: 15.5 /
   23.0 / 30.6 m. `sk_bounds.py`. The lane itself is clear of kept geometry (`sk_ring.py`).
9. **The walking length (4.2, 4.3).** 296 m over the mesh (75 m of it in the tower), not '175 m of ground'; the
   sibling's round measured the same way is 257 m, not shorter. `sk_misc.py`.
10. **What is shared with the sibling (1.4, 4.3).** Not 'the south garden only': the FA round crosses the pagoda
    and the south bridge too; 52 % of the campaign way's length lies over the FA level's own mesh. New to the
    owner are the start inside the pagoda, the last 30 m of garden, the tower and the ring.
11. **The stair tower's figures (1.1).** The mesh enters at y 220 (not 320) through a portal 113..117 wide on the
    east side; 23.5 m up; `TriggerBox_OnStairs` (9, 689, -10945), which 4.2 calls the foot, is on the third flight
    (polygon 810, y 520..640), above the landing the dropped bound stood on.
12. Small ones: `.ANM` 'grows as it did there' - it did not grow on Retomoto (3.2); '242 cover boxes' counts 17
    `NoCoverBox` (3.3); 're/bots_retomoto.md 1' is a plan, not a sight (6.9); `--heroes` does nothing on M06_A
    (`kl_maps.HERO_AT` has no entry for it; the kept `result.json` of trial 1 says `heroes: false`) - the hero
    place for a first load comes from `kl_fa_author.py hero`, as 5.3 step 2 says.

### Design holes of the proposed round (for whoever plans it)

- START: 20 m2 for eight, two 1.5 m openings, and two campaign squads whose defend box is that floor (2, 3 above).
- One 2.4 m gap between the stairs and the van, with the police return points beside it (6, 7).
- The drive away as proposed ends in the bound's warn boxes; the boarding side of the van faces a warn box
  15.5 m off (8).
- A quarter of a 296 m walk is single file on 1.29 m flights, entered through a 1.15 m portal (9, 11).
- A bot that leaves the bridge or the platform sideways lands on the 135-polygon part at the water's edge, which
  hangs on the route only through links of the dropped kinds (`nav2_M06_A.txt` of the first agent: 732 polygons
  with every link, 584 without; my `sk_links.py`: no kept link from it to the largest part): it cannot come back.
  A player can - the flood fill reaches objective 020 from the landing.
- Three enemies that can never be reached (5).
- Not holes, checked: the start is on a floor and not inside geometry (collision floor at y 624 under the mesh's
  635, nothing in the body column, no object on the inner floor but the dropped phone); every loot prop is beside
  the mesh; no door, lift, cut scene or dropped subtree stands in the way; 40 enemies are fewer than Retomoto's 63.

### Could not be verified (offline, or not re-derived)

- That Dog Days breaks the pavilion's windows on 'DestroyWindows' in an Arcade round, and what it does to eight
  players standing inside (registration and wiring confirmed, the effect not).
- That a kept Dead Men `LevelBound` box warns and ends a player in an Arcade round, and what it does to a
  passenger of the key-framed van (open for M02 / M03 too).
- What Dog Days does with cover boxes and no cover list (moot if the PASSIVE cure is taken).
- That a player gets through the tower's 1.15 m entry and up 1.29 m flights, and whether he can vault the median.
- That the cut ring squads stand and fight; that seven bots climb a spiral in single file.
- Not re-derived (taken from the report as it stands): the `.SND` / `.LOC` traces of section 2; the scene blocks'
  `CameraFar` / background colour; M06_FA_A's settings field 149; the FA sibling's and Retomoto's sizes READ from
  re/maps.md and CLAUDE.md; the +16.1 MB of the wardrobe (ASSUMED there); the 20 fade cues' wiring; the pictures.
- The effort figure: 0.4 (the report) or 0.45 (mine) of Retomoto is a judgement either way.
