# The Mizuki (Dead Men chapter 5, M05_A) as a Fragile Alliance map - study

2026-10-11, agent cfa-club. OFFLINE study: nothing was installed, the game was not started, no existing tool
or note was edited. Scratch scripts: `G:/kl_scratch/cfa_club/*.py` (their outputs: `G:/kl_scratch/cfa_club/out/`).
Trial builds, logs and pictures: `<work>/build/cfa/club/` (`<work>` = `G:/SteamLibrary/steamapps/common/Kane and
Lynch Dead Men/KL_PortTools`); every archive made here is deleted again, result.json / log.txt stay.
Most scratch scripts read the kept trial archive `<work>/build/cfa/club/patched/F07+M05_A campaign/F01_Main.zip`.
It is deleted with the others; to run a script again, rebuild it first (53 s):
`python G:/kl_scratch/cfa_club/run_maps.py one "<work>/build/cfa/club/patched" F07 M05_A --campaign --keep`.
The output each script gave here is kept under `out/` (file names: the script's name, or as cited).

Evidence labels, on every statement of fact:
**MEASURED** = output produced in this job (the command is named; run from `c:/kl-merge/kl-merge`),
**READ** = code or an existing note (file and place named), **ASSUMED** = fits the evidence, reason given,
**GUESS** = a coordinate or value of mine that nothing in the files fixes.
World units: 100 = 1 m; (x y z), y up. Sizes in MiB (2^20 bytes) unless 'MB' (10^6, as kl_maps prints).

## 0. Short answers

- **It can be grafted** - after ONE converter case: the stock command fails on a material string
  (`TEXT/TILU = MIRRORED`), a guard in kl_mat.py, not a limit (3.1). With that one string read as `TILED` the
  build completes: 26,106 entities, chunk table 52,935 of 69,632, 0 dangling paths (3.2).
- **It is light** (the smallest .prm and .TEX of the seven scouted levels: the lead's table): lightened, the level's large load blocks are .prm 34.9 + .fxc 8.7 +
  .ANM 20.7 + .WAV 10.7 MiB, less than stock F07 (60.6 + 7.7 + 20.6 + 17.4); with the full wardrobe and the
  four Payday 2 plates the chunk table does not grow and the .prm is 51.7 MiB (3.3).
  *(corrected by the second agent: these numbers are for a build with EVERY actor dropped - the trial keeps none of
  the campaign's guards. With the 27 enemy squads the round wants kept, MEASURED `bash G:/kl_scratch/cfa_club/skeptic/keep_chain.sh`:
  lightened .prm 41.2 + .fxc 8.8 + .ANM 21.2 + .WAV 10.9 MiB, chunk table 53,898; with the full wardrobe and the four plates
  the .prm is 58.0 MiB - still under stock F07's 60.6, by 2.6 MiB and not by 8.9. Details in 8.2.)*
- **The whole club is one walkable piece for AI**: 401 of the mesh's 437 polygons are one connected part from
  the pavement (y 20) through three floors to the far roof (y 1904); a heister route office -> roof end is 489 m
  on it, office -> pavement 187 m (3.4, 4.1).
- **What the place does NOT have**: no vehicle of any kind, no Fragile Alliance leftover, and almost no street:
  outside the front door the only collision floor is a pavement slab of 30 x 8.5 m; the road is scenery
  without collision (1.3, 2).
- **Four doors stand closed and two invisible walls stand in the way** as the level loads: doors that open on a
  stock message, walls of the kind the campaign itself switches off (1.4).
- **The famous crowd cannot come along in a first version**: it is not actors but the engine's HFlow crowd
  system (six flow objects, 1,980 members at most). Dog Days' exe still registers every HFlow class, no stock
  Dog Days level uses one, and three converter gaps stand before it (1.5).
- **Recommended round: 'Last call'** - the crew starts shut in Yoko's office with the loot, breaks out through
  her bodyguards, across both dance floors with the club's own music and light show running, and leaves by
  F07's key-framed van at the front door. Every part of it is a technique another map already uses.
  The campaign's own way out - over the roofs, across the glass roof, to a helicopter - is the second stage:
  the roof is all there, the helicopter has to be brought and none of the three ways to bring it works yet (4).
- Verdict: **feasible-with-work** (7). Effort: about 0.5 of Retomoto for 'Last call', about 0.9 with the roof.

## 1. What the place is

### 1.1 Rooms and floors

MEASURED (`python tools/kl_maps.py what M05_A`; output `out/what.txt`): 23,839 entities; 19 map rooms, a
backdrop, six crowd rooms, and a second set `Rooftops_END` 2.7 km away (the outro cut scene's roof):

| room (`M05_A_...`) | entities | x | y | z | what it is |
|---|---:|---|---|---|---|
| `Outside_Street_01a` | 457 | -11470..32559 | -157..5854 | -16191..1907 | the street in front, facades, trees; scenery (1.3) |
| `Inside_Entrance_01a` | 43 | -1428..523 | -665..1274 | -3610..0 | queue lane, ticket counter, entrance door |
| `Inside_Wardrobe_01a` | 221 | -1100..608 | -665..820 | -1741..700 | coat check, y 100..180 |
| `Inside_Stairs_01a` | 140 | -210..600 | 20..565 | 93..912 | stair room between the floors |
| `Inside_Dance_Floor_01a` / `_01b` | 61 / 392 | -1800..1500 | 20..565 | -550..2130 | dance floor 1 with the long bar, y 20..60 |
| `Inside_Dance_Floor_02a` | 597 | -1800..3528 | 20..880 | 1996..4368 | dance floor 2 (y 40), stage, the walkway (y 362..382) above it |
| `Inside_Daughter_Room_01a` / `_01b` | 96 / 239 | 1500..3313 | 350..1544 | 2000..3461 | front office and Yoko's office, y 342..362 |
| `Inside_2nd_Lounge_01a` (+ `_Hallway`, `_Stairs`) | 151 + 17 + 30 | -800..1713 | 0..1271 | -1000..2000 | lounge, y 460 |
| `Inside_3rd_Lounge_01a` (+ `_Hallway`) | 312 + 43 | -800..2311 | 0..1298 | -360..2711 | VIP lounge with two bars, y 860 |
| `Inside_3rd_Rave_01a` | 1,284 | -4985..-789 | 345..1297 | -400..2290 | rave room: floor y 460 with the bar island, gallery y 860 |
| `Inside_3rd_Storage_01a` | 73 | -3890..2044 | 0..1544 | 0..3593 | storage / L-hallway behind two fire doors, y 860 |
| `Outside_Roof_01a` | 1,331 | -16229..10264 | -2290..10189 | -1550..11649 | the roofs: y 760..1300, the glass roof y 1481..1525, the end platform y 1880..1900 |
| `Inside_CarShop_01a` | 150 | 0..6357 | 0..1723 | 0..6897 | car showroom UNDER the glass roof (three display cars, y 21); never entered |

(Extents as kl_maps prints them, two rooms on one line where named; a bound of 0 is an object parked at the
room's origin.)
Walkable area by region on the navigation mesh of the trial build (MEASURED, `python G:/kl_scratch/cfa_club/places.py`,
main mesh part only): pavement 826 m2 (collision floor: 258 m2, 1.3), entrance corridor 12 m2 (0.96 m wide,
12.5 m long), entrance / wardrobe 91, dance floor 1 328, dance floor 2 478, walkway 43, office 113, 2nd lounge +
hallway 418, rave floor 711, 3rd lounge 385, rave gallery 275, storage / L-hallway 10, roof (low part) 659,
glass roof and beyond 479, roof end platform 36 m2.

Pictures (MEASURED; drawn by `G:/kl_scratch/cfa_club/nav.py` and `route_pic.py` from the trial build's mesh; x to
the right, z up, yellow ticks every 10 m; in `<work>/build/cfa/club/pics/`):
- `nav_all.png` - the whole mesh without the far set, coloured by height (blue low, orange high), campaign
  stations as crosses;
- `nav_club_low.png` (y < 300: pavement, corridor, entrance, both dance floors), `nav_club_mid.png` (y 342..660:
  walkway, offices, 2nd lounge, rave floor), `nav_club_high.png` (y >= 760: 3rd lounge, rave gallery, storage,
  roofs, end platform);
- `route.png` - the two rounds of section 4: yellow 1..14 office -> roof end, cyan A..E the way out of the front
  door, red crosses = the doors and invisible walls of 1.4, green box = the pavement's collision slab, blue box =
  the glass roof.
`tools/kl_view.py` draws characters only (READ: its docstring); a room rendering was not made.

### 1.2 Top-level subtrees and what the graft does with them

MEASURED (`python tools/kl_maps.py sides M05_A`):

| side (kl_prpjoin.sides) | nodes | subtree | campaign pre-pass |
|---|---:|---|---|
| map | 10,238 | `CloneGroup_Locations` | stays (10,186 + 718 clone groups of kept templates) |
| map | 5,930 | `Locations/*` (map 5,863, `M05A_LightControll.zip` 30, `M05A_Postfilter.zip` 29, `M05A_Effects.zip` 8) | stays |
| map | 666 | `CloneGroup_Effects` (templates in the map) | stays with its template |
| map | 553 | `AI_Players!` (27 enemy squads, 7 civilian squads, Yoko, flee points) | dropped |
| map | 205 | `Characters!` (hero, Lynch, mini-cut-scene squads) | dropped |
| map | 155 | `CutScenes/*` (intro camera, kidnap, 'Yoko escapes', the call to Retomoto incl. `Rooftops_END`) | dropped |
| map | 84 | `Locations/M05_A/M05A_Audio.zip!` (the club's music and ambience objects) | stays |
| map | 52 / 52 / 50 / 39 / 37 / 31 / 28 / 9 / 7 / 5 | `Specials!` / `COOP!` / `Doors!` / `Checkpoints!` / `Crowds!` / `Boundaries!` / `Objectives!` / `Traffic!` / `Jumppoints!` / `ReducedVisionSplines!` | dropped, except 26 `Specials!` (cover / no-cover boxes) and **15 `Boundaries!`** (see below) |
| systems | 3,199 + 2,491 + 3 | `CloneGroup_Effects`, `AllLevels/mainsceneincludes.zip`, CoverList / TrackLinkObjects / ZParticleController | left out (Dog Days' own are used) |

Pre-pass total: 341 subtrees / 1,185 nodes dropped, 16,961 stay.
MEASURED (inline script on the trial build's .gms, 2026-10-11): the 15 kept `Boundaries!` nodes are five campaign
level bounds with their warning boxes, four of them NOT hidden at load and standing ON the route:
`LevelBoundTrapped_COOP` (200, 175, -251) wardrobe, `LevelBoundStairs` (399, 165, 218), `LevelBoundRoof`
(3220, 1189, 4392), `LevelBoundEscape` (7311, 1887, 4584); `LevelBoundEntrance` (46, 120, -2513) is hidden. The
campaign switches them with `Boundaries!Deactivate_*` (`out/refs_M05_A.txt`), which the pre-pass drops. **A
Fragile Alliance build must drop them (`--m-drop "Boundaries!*"`).**
MEASURED (`python G:/kl_scratch/cfa_club/run_maps.py one "<work>/build/cfa/club/nobounds" F07 M05_A --campaign
--m-drop "Boundaries!*"`): that builds - 26,091 entities, 0 dangling paths, the same 11 problems; kl_fa.check
then adds 'no level bound' to its DEGRADED list (bounds have to be authored, section 5).

### 1.3 The street is scenery

MEASURED (`python G:/kl_scratch/cfa_club/street.py`, `street2.py`: kl_map_escape.Ground on the trial build's .HVK):
- Across the street at x = 100: floor `SI0101_FloorA_Front_01` / `ColiObj_01` at y 30 from the club to z -3450;
  from z -3500 outwards **no collision floor at all**. Along both traffic lanes of the campaign (z -4008 and
  z -5305, x -12000..12000): no floor under any sample.
- The pavement's collision floor is one slab: **x -1220..1820, z -3450..-2600, y 30** (30.4 x 8.5 m). The mesh
  strip the campaign's civilians use is far longer (x -3765..5786, z -3502..-2623).
- Four parked cars (key-framed bodies with breakable glass) stand along the kerb at z -3750..-3520:
  x -1366..-894, -198..290, 614..1060, 1119..1615. Street lamps and two trash cans stand at z -3300.
- A van-wide strip along the pavement at z -2900 and z -3100 is free of every collision from x -3700 to 5700;
  what `kl_map_escape.lane` reports there is only 'no road' outside the slab.
MEASURED (inline spline decode, `Traffic!Traffic_Left_Spline` / `_Right_Spline`): the campaign's traffic drives two
straight lanes, (-12151, 33, -4004) -> (7483, 35, -4012) and (11242, 65, -5315) -> (-11908, 23, -5295), with five
car models (`Traffic!Cars!Ground_JPN_Civilian_A/B/D`, `_Police_A`, `_Taxi_A`): ambient traffic, no physics car.
MEASURED (`python G:/kl_scratch/cfa_club/actors.py M05_A`): the level holds 0 `ZHavokCar`, 0 `ZHeli`, 0
`ZAnimatedVehicle`. **There is no escape vehicle to re-use.**

### 1.4 Doors and invisible walls as the level loads

MEASURED (`python G:/kl_scratch/cfa_club/doors.py firedoor daughterroomdoor entrancedoor`, `node.py M05_A 4822 6079
6842 --kids`): every door is a `ZGROUP` + `RelayMessageList` ('Activate' -> its leaves), each leaf a `ZSTDOBJ` +
`MatPosAnim` 'Activate' + `Audio_PlaySound`, with a KEY-FRAMED collision body (flags 0x108 + 0x72).

| door | group (under `Locations/...`) | leaves at load | state |
|---|---|---|---|
| office, inner | `Inside_Daughter_Room_01a\SI0108_M05_DaughterRoomDoorA_02` | `D1`, `D2`: x 2496..2504, z 3167..3488 | CLOSED |
| office, outer | `...\SI0108_M05_DaughterRoomDoorB_01` | `D04`, `D05`: x 1496..1504, z 3167..3488 | CLOSED |
| storage | `Inside_3rd_Storage_01a\SI0108_M05_Firedoor_03` | `D03`: x -3246..-3134, z 2302..2310 | CLOSED |
| roof | `...\SI0108_M05_Firedoor_02` | `D03`: x -3846..-3734, z 3283..3291 | CLOSED |
| entrance | `Inside_Entrance_01a\SI0101_M05_EntranceDoorA_01` | `Dor_A_01` x -627..-148, `Dor_B_01` x 162..641, z -1366 | OPEN (3.1 m gap) |

The campaign drives them from `Doors!*` (dropped by the pre-pass): four `DoorCtrl` boxes - a controller Dog Days
registers but no stock Dog Days level uses (MEASURED, `kl_maps.py first M05_A`) - and, for the entrance, a
`MatPosAnimProxy` (frames 0..50) that CLOSES it behind the players at checkpoint 3.
MEASURED (`python G:/kl_scratch/cfa_club/walk2.py`, `walk4.py`; `out/refs_M05_A.txt`): the campaign's invisible
'hero collision' that is present at load and matters:
- `Inside_3rd_Storage_01a\HeroColi` (-3427, 1060, 3206): closes the storage rooms; switched by
  `Characters!Friendly!EscapeSquad\HeroColi_Remove` / `GeomDeactivator_Storage_Herocoli` (`DeactivateGeom`).
- `Inside_Entrance_01a\HeroColi` (131, 0, -2478) and `Inside_Entrance_01a\Plane01` (95, 231, -2538): close the
  street end of the queue lane (the campaign never lets the player back onto the street).
- `Outside_Roof_01a\HeroColi` (2895, 620, 3430) at the office skylight: not on any route used here.
What the collision walk test shows (kl_escape.Walk; hidden entities left out; a 'yes' = the collision leaves a
way, a 'no' is not proof of a wall):
- As loaded, nothing but the office is reached from the office.
- Door leaves out: office -> front office -> walkway -> dance floor 2 -> dance floor 1 -> wardrobe -> entrance
  hall -> entrance corridor: reached (about 140 m). The pavement only when `Plane01` and the entrance `HeroColi`
  are out as well (`walk3.py`).
- Upstairs: from the 3rd floor the storage, the roof door, the roofs and the glass roof are reached only with
  the two fire doors AND the storage `HeroColi` out (`walk4.py`).
- The test does not get UP any staircase of this level (dance floor 2 -> walkway, stairs -> 2nd lounge, 2nd ->
  3rd floor, roof -> end platform), also not with its step limit raised from 45 to 60, while it gets DOWN all of
  them. The campaign climbs every one (checkpoints CP_01 .. CP_11 lie along them, 1.6) and the mesh joins
  them: ASSUMED a limit of the test, to be settled by one scripted walk (6).
  *(corrected by the second agent: 'does not get UP any staircase' is too wide. MEASURED
  `python G:/kl_scratch/cfa_club/skeptic/walk6.py` (step limit 45 and 60, hack collision in and out): the test DOES climb
  queue lane (y 20) -> entrance hall (y 100) -> wardrobe (y 180) and dance floor 1 (y 60) -> stair landing CP4 (y 160) -
  every UP stretch of round A's route - and from the landing it gets up to floors at y 449 and into the rave room (y 708).
  NOT climbed: dance floor 2 -> walkway, 2nd lounge hallway -> 3rd floor (`Si0109_M05_Stairs_2nd_A_01`), the long roof
  stair (`SO0005_M05_StairLong_A_02`); the probe at CP_05 is not reached from the landing. So the open stair question
  touches the upstairs detour loot and stage two, not the way out of the front door. Also present and named by NO
  campaign object (so they stay, as in the campaign): `ColiObj_HACK_Plane01` in the stairs room (x -170..600, y 153..462,
  z 135..849) and in the 2nd lounge (x -235..294, y 450..849, z 69..895), `ColiObj_HERO_Box01/02` in the stairs room, five
  `ColiObj_HERO_*` on the roofs (`python G:/kl_scratch/cfa_club/skeptic/hack.py`).)*

### 1.5 The crowd, the civilians, the enemies

MEASURED (`python G:/kl_scratch/cfa_club/node.py M05_A 9209 9210 9215 9223 9227 23790 23796`, inline summary):
the crowd is the engine's HFlow system, not actors.

| flow object (class) | at | grid | capacity field `ZHFlow[22]` | members | flow map |
|---|---|---|---:|---|---|
| `Crowds!Crowd_1st\Crowd!Crowd_FirstFloor` (ZHFlowFF2M05) | (601, 0, 1614) | 64 x 48 | 750 | 3 PartyGirl + 1 PartyMan | dance_hflow.tga |
| `...Crowd_Lounge` (ZHFlowFF2M05) | (703, 450, 1055) | 24 x 24 | 100 | same four | lounge_hflow.tga |
| `...Crowd_LoungeRave` (ZHFlowFF2M05) | (-1188, 781, 1100) | 80 x 48 | 300 | same four | loungeandrave |
| `...Crowd_Rave` (ZHFlowFF2M05) | (-3182, 450, 800) | 40 x 24 | 700 | same four | rave_hflow.tga |
| `...Crowd_Sidewalk` (ZHFlow) | (268, 41, -2969) | 64 x 8 | 80 | 4 female + 2 male pedestrians | sidewalk, sidewalk2 |
| `...Crowd_Sidewalk_Far` (ZHFlow) | (387, 41, -6189) | 64 x 8 | 50 | same six | - |

(That field 22 is the member count is ASSUMED from its values; sum 1,980.) Ten `ZHFlowLnkObj` member models name
animation sets `Animation/Crowd/M05_Crowd_Female.xanm`, `M05_Crowd_Male.xanm`, `Crowd_Female.xanm`, `Crowd_Male.xanm`;
the flows are told to panic by `AIDWrapper` 'CrowdStartPanic' / 'CrowdSwitchMap'.
Can Dog Days carry it?
- MEASURED (`python G:/kl_scratch/cfa_club/exe_str.py HFlow Crowd`): kl2.exe holds the same 32 'HFlow' strings as
  kaneandlynch.exe (ZHFlow, ZHFlowFF2M05 / M08 / M09 / M11, ZHFlowLnkObj, ZHFlowAccessory, ZHFlowObstacle,
  ZHFlowRout, HFlowBox) and the messages CrowdStartPanic, CrowdPause, CrowdSwitchMap, CrowdPurgeLiving ...;
  `re/kl2.json` gives ZHFlow 38 own fields and ZHFlowLnkObj 6, as in Dead Men (inline `kl_rtp.Schema` read).
- MEASURED (`kl_maps.py first M05_A`): stock Dog Days uses none of these classes in any level: the code never
  ran in the retail game.
- Three converter gaps (READ: the field values above): `ZHFlow[4]` and `[10..14]`, `ZHFlowLnkObj[1]` / `[2]` are
  integers that look like .buf offsets (1130400, 480048 ..), which a graft would have to re-point; the crowd
  animation sets are Dead Men .ANM clips (not carried: the trial's .ANM join took 2 clips, both `Beat_M05`); the
  six crowd ZROOMs sit outside the map tree.
So: not blocked by a limit, but dead code plus three unwritten converter cases. **First version: no HFlow crowd.**
What can stand in: the campaign's 17 civilian ACTORS (`ZCivilian`: 4 bartenders, 5 in the queue, 2 phoners, 2
kissers, wardrobe attendant + 1, ticket seller, 1 walker) and its 16 flee points
`AI_Players!Civilians!_EscapePoints!Pos#01..16`, 13 of which lie on the pavement slab (x -1380..1763, z -2686..-2890)
(MEASURED, actors.py / street2.py). Stock FA levels hold 2..13 ZCivilian (READ re/fa_gamemode.md 1.2).

Actors (MEASURED, actors.py, `python G:/kl_scratch/cfa_club/squads.py`): 77 `ZFFActor` = 58 guards in 27 squads,
17 civilians in 7 squads, Yoko, Lynch. Yardstick: stock FA levels 35..57 ZFFActor, Dead Men's FA maps 14..20
(READ re/fa_gamemode.md 1.1); Retomoto runs 63 campaign actors + 7 bots (READ re/retomoto_fa.md 0, CLAUDE.md).
The two generations of guards:
- **'SecondRun'** - 10 squads / 26 guards, model 7927, `Smg_MP5-A3_01` (two `_Light`), no prop attached: Dance#01
  (3) at (623, 322, 2902) .., Dance#02 (3) at (-1323, 22, 1355) .., YokoGuards (2, pistols) in the front office
  (2387, 354, 3319), Lounge#01 (3) (805, 505, 1265), Lounge#02 (2) (763, 865, 2068), Rave#01 (2) (-2775, 489, 927),
  Rave#02 (3) (-1536, 866, 495), Roof!RoofVents#01 (3) (1790, 762, 3372), Roof!RoofWindow#02 (4) (7458, 1885, 4155),
  Roof!Sniper (1) (4339, 1913, 6145). These are the campaign's enemies once the alarm is up: checkpoint 8 names
  `SecondRun!Rt2\Way#01` -> `Rt\Way#01`, which names the `Alert` child of the six floor squads and the four
  `AI_Players!Obliterate!Bouncers#0n` squads that take the first-run bouncers away (MEASURED `out/refs_M05_A.txt`).
- **'FirstRun'** - 17 squads / 32 guards, pistols (`HG_HK_USP_01`; one MP5): 14 of the squads (28 guards) carry
  `AttachGeomToBone` (27 uses; registered by Dog Days, used by no stock level), two also `WarnBehaviourRout`
  (the same); `Hunters!HunterKillers` (3, at the wardrobe (-97, 183, -146)) has a `HuntBehaviourRout` and a
  campaign timer `Hunters!3min`.
By kl_fa_author.squad_plan's rule (READ tools/kl_fa_author.py 608; applied by squads.py): 2 squads / 4 guards stay
as the tool is written (it wants a behaviour rout); 9 more squads / 21 guards hold only squad objects but no
rout (`ZSquadScript` + `SquadModifierBehaviour` + `ZSoldier`); 17 squads / 34 actors hold something else
(`AttachGeomToBone` 14, `WarnBehaviourRout`, `AIDWrapper`, `DeactivateGeom`, Yoko's own scripts).
MEASURED (`python G:/kl_scratch/cfa_club/squad8.py`: the level converted in memory by kl_graft.DeadMen, Dog Days
field numbers): `ZSquadScript` field 3 (active from the start: ASSUMED meaning, READ re/retomoto_fa.md 10.3) is 1
on the 'FirstRun' squads and 0 on eight of the ten 'SecondRun' squads, which the campaign switches on later.
Field 8, the 'wiped out' list (READ re/fa_gamemode.md 0.6), is set on five of the 36 squads, among them
**`FirstRun!Backroom!WaitingRoom` -> `Doors!Daughter#02!COOP_DoorDaughter` / `SP_DoorDaughter`: the campaign itself
opens Yoko's inner office door when her two waiting-room guards are dead**, and `SecondRun!Roof!RoofWindow#02` ->
`Count2`, which the end-of-level trigger also names. The dance-floor, lounge and rave squads have it empty.

### 1.6 The campaign's flow, from its scripted objects

MEASURED (positions: `G:/kl_scratch/cfa_club/tree.py` -> `out/tree_M05_A.txt`; references: `refs.py` ->
`out/refs_M05_A.txt`; `places.py`). The order between steps 6 and 9 is ASSUMED from checkpoint numbers and names.

1. Start in the queue: `Characters!Hero!Hero` (ZFFPlayer) at (129, 32, -2535), Lynch at (121, 31, -2605);
   intro mini cut scene `Characters!Friendly!Intro`, camera `CutScenes/M05/M05_Intro_CAM.zip`; the entrance
   `HeroColi` holds the hero in the lane. Objective 'M05/MissionObjectives/2' at the entrance (28, 167, -2089).
2. `T_EnterClub` (-414, 210, -604), wardrobe (`Jumppoints!Jump_01_Wardrobe` (-4, 178, -240)); objective '/1':
   `Obj#01_Dance01` (576, 63, 1380), `Obj#02_Dance02` (-864, 84, 2491), `Obj#03_Walkway` (1272, 382, 3206);
   checkpoint 1 (780, 381, 2747). Bodyguards watch but do not fight ('FirstRun', `WarnBehaviourRout`).
3. Yoko's office: checkpoint 2 (2595, 342, 2773), `Obj#04_Office` (2918, 341, 2324), Yoko at (2606, 345, 2075);
   `PlayerAction` 'KnockYoko' (2943, 497, 2288); cut scene `CutScenes/M05/M05_Kidnap_Yoko.zip` at the desk
   (2443..2701, 190..415, 2097..2652). Lynch carries her from here on.
4. Back to the front: checkpoint 3 (393, 122, -219) closes the entrance door (`Doors!Entrance!CloseEntranceDoor`,
   `KillEntrancePF`) and plays `LynchPostKidnap\MiniCut_ExitBlocked` (dialogue group 'M05_Doors_Closed').
   `AI_Players!Enemies!SecondRun!*` are the enemies from now on (`Specials!2ndRunTrigger`).
5. Up: checkpoint 4 (-55, 161, 320), 5 (821, 462, 143), [6 (-754, 462, 644)], 7 (-723, 863, 641); rave gallery
   (`Jump_23_Rave` (-3182, 862, 1773)); objective '/3' the storage door (-3191, 920, 2300) (`Doors!Storage!PlAct`
   'OpenDoor', eONLY_KANE).
6. Storage: `Jump_25_L-Hallway` (-3186, 861, 2520), checkpoint 8 (-3786, 861, 3211); cut scene
   `M05_YokoEscapes.zip` at the roof door (-3778..-3386, 860..995, 3178..3250).
7. Objective '/5' the roof door (-3479, 861, 3822) (`Doors!Roof!PlAct`); roof: checkpoint 10 (-2378, 867, 4229),
   `Jump_30_Roof` (2350, 762, 3686). The mesh has four links here: two drops from the skylight level (y 619)
   into the office (y 359) and two steps between y 619 and y 760 (MEASURED, `walk.py`, Dead Men mesh array 7).
8. Checkpoint 8 switches the 'SecondRun' guards on all over the club (1.5). Checkpoint 9 'Capture' stands in the
   office (2605, 342, 2617): ASSUMED Yoko runs back there and is caught again, the players coming over the roof
   and down through the skylight (the links of step 7) or back through the club.
9. Checkpoint 11 (2498, 1284, 4610), `Jump_35_Roof` (2955, 1464, 4990), the glass roof (x 3496..5903, z 4598..5602,
   panes at y 1525 / 1481; 60 panes, each with its own `ShotActivate` + `HavokShatterGlass` pane, `Triggerbox`,
   `TriggerCounter` 5, `Timer`, `PathBlocker` and `KillBox`: MEASURED node.py 8469..8477), the long stair up to
   the end platform (y 1880..1900, x 6800..7800, z 3500..4300: MEASURED `helifit.py`).
10. End: `Specials!EndOfLevel!EndOfLevel` (`EndOfLevelTrigger`) at (7302, 1917, 4618) with `CrewBox` (7286, 1829, 4193)
    -> `Characters!Friendly!Outro`, cut scene `M05_Call_Retomoto.zip` (played in `Rooftops_END`, x 273747..282728)
    -> `SceneChanger` 'Locations\M06_A\M06A_Main.zip'. **They leave on foot over the roofs; no vehicle.**
    The campaign silences the club music at `Specials!Trigger` (-617, 1063, 3484) (`Specials!KillMusic`).

## 2. Leftovers of a planned Fragile Alliance version

MEASURED (`python G:/kl_scratch/cfa_club/leftovers.py M05_A`, `out/leftovers.txt`; actors.py census): **none in
this level.**
- 0 `ZSpawnPoint`, 0 `OnlineMoneyCtrl` / `OnlineMoneyContainer`, 0 `ZOnlinePIPCameraPoint`, no class or
  controller with Online / Spawn / PIP / Money in its name outside `AllLevels/mainsceneincludes.zip`; the only
  `Ingamemap` controllers (14) are the campaign's objectives.
- No entity name, property string, .buf / .MAT / .sgp string with FA / Online / DL0n / Multiplayer / Tokyo that
  belongs to the level: every match is the campaign ('EscapeSquad', 'YokoEscapes', `C_Civilian_Male_Tokyo_02`)
  or the systems every level carries (`UI_FA_Respawn_pip_mask`, `Dialog/Multiplayer/FA_Menu/*`, the
  `AllLevels/Menu/Online/*` text keys).
- The level's English .LOC holds the placeholders the lead found, as every level does:
  `AllLevels/Menu/Online/Scenarios/BriefingDL04` = 'Briefing DL04 - Tokyo', `TitleDL04` = 'Title DL04'. Nothing
  says WHICH Tokyo place was meant (this club or the Retomoto tower): not established.
- Cover boxes on the street (12) and in the unreachable car showroom (9) are children of prop prefabs (bus
  shelter, vending machine, the cars), not a sign of planned play there (MEASURED, `out/props_M05_A.txt`).

## 3. Can it be grafted

### 3.1 The stock command fails, and why

MEASURED: `python tools/kl_maps.py one "<work>/build/cfa/club" F07 M05_A --campaign` ends after 26 s with

    ValueError: material 538 (Locations/M05/Concrete/Concrete_Walkway_01a_M05): TEXT/TILU value b'MIRRORED' never occurs in Dog Days
    (kl_graft.py:823 __init__ -> kl_mat.py:397 convert_mat_full)

result.json / log.txt: `<work>/build/cfa/club/F07+M05_A campaign/`. `python tools/kl_whoref.py M05_A "..."` dies
at the same line (it builds the same converted level).
MEASURED (`python G:/kl_scratch/cfa_club/mat_mirror.py`): stock Dog Days DOES use `MIRRORED` - on `TEXT/TILV`
(F04 material 443 `Levels/F04/Concrete/Concrete_F04_Wall_C_01_b`, 3 bindings); on `TEXT/TILU` it has only '',
'NONE', 'TILED'. Dead Men has MIRRORED on TILU in M05_A (material 538, 3 bindings) and in M01_A (material 615, 1).
Kind of fault: **a missing converter case** (the guard compares per key), not a limit and not a bug in the level.
Fix (not applied; kl_mat.py is not mine): in `convert_mat_full`'s string test accept for TILU / TILV / TILW the
union of the three keys' Dog Days values (ASSUMED one addressing-mode enum: same value names on both keys); or
write `TILED` for it (one walkway material tiles instead of mirroring).

### 3.2 The trial graft with that one string substituted

MEASURED: `python G:/kl_scratch/cfa_club/run_maps.py one "<work>/build/cfa/club/patched" F07 M05_A --campaign --keep`
(the wrapper reads MIRRORED as TILED in memory and then calls kl_maps.main(); nothing else differs). 53 s.
result.json / log.txt / graft.txt: `<work>/build/cfa/club/patched/F07+M05_A campaign/`.

| | trial F07 + M05_A | limit / yardstick |
|---|---|---|
| verify problems | 11 = 1 sound + 10 Fragile Alliance findings | the 10 are what every level without an FA layer has: 1 CRASH (no `OnlineFragileAllianceSettings`), 9 BROKEN (define, exit trigger, START / AFTER_DEATH points, three gameplay triggers, loot, squads) |
| scene paths that name nothing | 0 | |
| entities | 26,106 (F07 systems 9,144 nodes + map 16,962) | Retomoto 25,529 (READ re/retomoto_fa.md 11.0) |
| rooms / gates / neighbour lists | 20 (19 the map's) / 46 / 38, verify followed every one | |
| textures | 1,676 | 4,096 |
| materials | 1,135 slots (4 without a compiled shader: not drawn) | 2,048 |
| .prm chunk table | **52,935 entries** (header +4) | 69,632 enforced, 73,728 hard (READ re/prm_limit.md) |
| sounds / waves | 4,701 / 4,552 | largest stock bank 4,806 / 4,568 (READ kl_maps.py docstring) |
| archive | 284.4 MB, + 46.4 MB beside | |
| `python tools/kl_impact.py <folder>` | problems: 0 | |
| `python tools/kl_maps.py preflight <folder>` (`out/preflight.txt`) | CRASH 2 (both = no FA layer), RISK 16 (9 FA + 7 first-timers, 3.5), NOTE 64 | |

The sound problem: '5 stream clips are not in the merged stream file'; by name 12 (result.json
`stream_clips_missing`): the seven `Music/InHouse/Japan/M05_A/M05_A_Club*` layers and five ambience beds (4.6).
Conversion log (MEASURED, log.txt): 46 gates converted; .prm 275 lit meshes handled, 2 scatter objects (become
empty meshes); `entities_retyped` 1; 20 controllers removed; .ANM joined with +2 clips, both `Beat_M05`
('GUESS Dead Men clip records' - kl_anm.convert's own note); .hrd left out; 17,803 of M05_A's 25,122 chunks
appended; +435 material slots, +488 textures.
Same wrapper with the helicopter level as host - `... one "<work>/build/cfa/club/host_f08" F08 M05_A --campaign` -
MEASURED: builds too; 26,105 entities, 44,848 chunks, the same 11 problems.

### 3.3 The large load blocks, and what a wardrobe adds

MEASURED (inline script over the archives; `python tools/kl_graft.py lighten <patched> "<work>/build/cfa/club/light"
--load trim,slim,fxc,wav`; `bash G:/kl_scratch/cfa_club/ward.sh` = lighten, then `python tools/kl_chars.py wardrobe
<light> <ward> --plates=wolf,dallas,chains,hoxton`, then kl_impact; numbers in `<work>/build/cfa/club/ward_sizes.json`):

| MiB | .prm | .fxc | .ANM | .WAV | sum of the four | chunk table |
|---|---:|---:|---:|---:|---:|---:|
| stock F07 | 60.6 | 7.7 | 20.6 | 17.4 | 106.4 | - |
| stock F01 | 63.5 | 5.9 | 19.8 | 14.7 | 103.9 | - |
| Retomoto as on the tab (`<work>/build/rt_full6`) | 76.2 | 16.9 | 20.6 | 26.5 | 140.3 | 65,119 |
| the bank (`<work>/build/z_final/M03`) | 59.7 | 16.9 | 21.2 | 21.6 | 119.4 | |
| **club, trial as built** | 75.3 | 16.9 | 20.7 | 20.2 | 133.1 | 52,935 |
| **club, lightened** (trim, slim, fxc, wav) | **34.9** | 8.7 | 20.7 | 10.7 | **74.9** | 52,935 |
| **club, lightened + full wardrobe + 4 plates** | 51.7 | 16.9 | 20.7 | 10.7 | 100.0 | **52,935** |

- Lighten: 1,401 dead model roots, 8,650 dead vertex / index chunks emptied; .TEX 342.3 -> 151.9 MB; .WAV: 151 of
  918 in-memory clips dropped. kl_impact on the lightened build: problems 0.
- Wardrobe: 'chunk table: 52935 entries (20989 of the base's 24318 dead indices taken, 3329 still free)';
  KLWardrobe.ini Characters=16, Masks=12; `kl_chars` check problems 0, kl_impact problems 0. The wardrobe step
  writes the full shader cache back (16.9); `lighten --load fxc` belongs after it (READ kl_graft.py 492).
- So the 2 GB / chunk-table crashes of CLAUDE.md (0x8e5bbd, 0x607272) are farther away here than on any shipped
  map: this is the smallest .prm of all seven candidates (37.0 MB in the stock level: the lead's table).
- *(corrected by the second agent: every row of the table above is a build WITHOUT actors - the campaign pre-pass drops
  `AI_Players!` and nothing keeps the guards. MEASURED with `AI_Players!Enemies!*` (27 squads, 58 guards) kept back
  (`G:/kl_scratch/cfa_club/skeptic/run_keep.py`, `keep_chain.sh`): as built 26,384 entities, .prm 81.5 MiB (85.5 MB),
  chunk table 53,898, textures 1,725, materials 1,162, sounds / waves 4,774 / 4,625, .ANM +35 clips (the guards' sets
  `Army` and `Bouncer` are STAND-INS copied from F07's `Swat_02` and `Thug`: kl_graft's own guess by role), 0 dangling
  paths, verify problems 10. Lightened: .prm 41.2, .fxc 8.8, .ANM 21.2, .WAV 10.9 MiB (sum 82.1). Lightened + wardrobe +
  4 plates: .prm 58.0 MiB (60,814,592 B), chunk table 53,898, kl_chars check problems 0, kl_impact problems 0. The
  conclusion stands in sum - 82.1 MiB lightened and 98.9 with the wardrobe (ASSUMED the shader cache slims to 8.8
  again in a pass after it, which I did not run; 107.0 as the wardrobe step leaves it) against stock F07's 106.4 - but the .prm margin under F07 is 2.6 MiB, not 8.9, and .fxc (8.8 against
  7.7) and .ANM (21.2 against 20.6) are each a little ABOVE F07's.)*

### 3.4 The navigation mesh

MEASURED (`python G:/kl_scratch/cfa_club/nav.py`, `out/nav.txt`):
- Dead Men's mesh: 95,608 bytes, 437 polygons, 55 areas, 106 waypoints, 6 links (kind 1: 2, kind 2: 4).
  `kl_pf4.convert` does not refuse it: 119,236 bytes, the two kind-1 links dropped, `kl_pf4.check` clean; the
  built level carries exactly that block.
- Connected parts by the edges' neighbour fields: 11 - **one of 401 polygons** (5,042 m2; x -4950..7453,
  y 20..1904, z -3502..5741), the far cut-scene roof (13 polygons, x 279035..281514), the strip behind the VIP
  bar (13 polygons, 6 m2, y 860), and eight scraps of 1..2 polygons, one of them the skylight level above the
  office (joined to the main part only by the four one-way links).
- All 25 campaign stations from the pavement to the end platform lie on the main part (table in `out/nav.txt`);
  walking distances along it between consecutive stations: 18, 8, 3, 36, 20, 40, 23, 23, 7, 136 (office -> 2nd
  lounge), 34, 82, 35, 8, 13, 12, 89, 24, 7, 49, 8 m.
- The edge self-test of kl_fa_bots.Nav holds: 976 of 976 edges with a neighbour share both ends with it.

### 3.5 What this level has that no proven map has, and the crash classes it is exposed to

MEASURED (`python tools/kl_maps.py first M05_A`, `out/first.txt`; preflight). Most first-timers leave with the
campaign pre-pass (HFlow classes, DoorCtrl, AttachGeomToBone, cut-scene and mini-cut controllers, CoopGate,
PsychoticController, LevelCtrlM05, ZFFItemWeapon ...). What STAYS in the build:

| class / controller | n | where | stock Dog Days | status |
|---|---:|---|---|---|
| `ZEnvSampler` | 3 (slots 0, 0, 1) | rave, lounge, entrance | no level | ran live on M02_FA_A (7 of them; READ re/maps.md 11, line 832) |
| `SoundSpline` | 1 | `M05A_Audio.zip!RAM!Inside!StorageRoom_Pipe` | no level | ran live on M02 / M06 (same place); its node has a sound of the merged bank (preflight ok) |
| `PositionLightControl` | 7 | `Locations/M05_A/M05A_LightControll.zip` | **no level** | NEVER RUN in Dog Days. It is the light show: each reads the position of the animated object below and the club music object (`Club_01_Clean_Music_01` / `Club_02_Clean`) and switches lasers / strobes |
| `ZIKLNKOBJ` + `StartAnim` | 2 | `...LOC_Inside.zip\Beat_M05\Ground_Beat05`, `_SecondFloor` (under the floor, y -161) | **no level** | NEVER RUN. Plays `anmcol:animationdatabase#Beat_M05`, the beat track (the 2 clips the .ANM join converted by a guess) |
| `ShotActivateDamage` | 5 | the roof's chimney fans `PC0300_M05_Chimney_A_0n!Fan_A` | **no level** | NEVER RUN |
| `KillBox` | 60 | one per glass-roof pane | 60 in F01..F09 | stock controller; Dead Men data |

Fall-back for the three never-run ones, if a load faults in them: drop `Locations/M05_A/M05A_LightControll.zip`
(30 nodes, top-level: `--m-drop`), flatten or remove the two `Beat_M05` children and strip the five fan
controllers (needs a pre-pass like kl_maps' `--flat`; not written). The light show is then static.

Crash classes of CLAUDE.md, one by one (MEASURED where a check is named, else READ):
- room trees / .rmi / .rmc / gates: verify followed every gate, list, tree and box (preflight 'rooms: ok'); the
  seven ZROOMs outside the map tree (six crowd rooms, `Rooftops_END`) leave with the pre-pass.
- navigation mesh missing (0x5503da): not exposed, the mesh converts (3.4).
- .ANM: only `Beat_M05` comes from Dead Men, used only by the two `ZIKLNKOBJ` above.
- .prm baked lighting: 275 lit meshes found and handled; 2 scatter objects not drawn.
- .MAT: four materials without a compiled shader are not drawn: `Items_Dynamic/MobilePhone_Front_01a`,
  `Locations/M05/Plastic/StripeLight_01a_Blue_M05`, `Locations/M05/Effects/ObjectLight_01_White_M05`,
  `.../CeilingLight_01b_White_M05` - three of them are lamps of the club: a look fault (the bank ran with 35).
- .sgd: SecurityZones, HavokShatterOctree, ExplodableOctree present (preflight ok).
- bone ids at a bullet hit (0x4c34b3): kl_impact problems 0.
- the .prm allocation (0x8e5bbd) and the chunk table (0x607272): 3.3.
- execute crash (0x4098a1): kl_fa's repair ran ('ExecutionBloodSpatter' line in log.txt).
- a JumpPoint fired by a level object (0x8f40c9): none kept (`Jumppoints!` dropped).
- duplicate cover list (0x6682c5): one `CoverList` at top level in the build (S's is not kept without an authored layer).
- bots' dynamic step (0x686a66, open: re/crash_686a66.md): the same exposure as every map with that step.
- size: 26,106 entities is past preflight's old baseline (19,827) but below what Retomoto runs.

## 4. The round

### 4.1 Three candidates

| | A. 'Last call' (out of the front door) | B. 'Over the roofs' (the campaign's second half) | C. 'In and out' (classic smash and grab) |
|---|---|---|---|
| start | shut in Yoko's office, loot on the desk | the same | on the pavement / in the entrance hall |
| route | office -> front office -> walkway -> dance floor 2 -> dance floor 1 -> stairs -> wardrobe -> entrance -> pavement; **187 m** on the mesh, least clearance 11 | office -> ... -> dance floor 1 -> stairs -> 2nd lounge -> 3rd floor -> rave gallery -> storage -> roof -> glass roof -> end platform; **489 m**, least clearance 3 (stair head to the 3rd floor) and 8 (roof door) | A's route walked in and back: 374 m |
| loot | office, bar tills, optional detours upstairs | office, bars on every floor, storage lockers | the same props, office last |
| beat | the front door is shut until the dance floors are cleared (the campaign's own 'exit blocked') | the storage fire door (the campaign's own objective), then the glass roof | the office doors open when the bodyguards are dead |
| escape | F07's key-framed van on the pavement slab | a helicopter at the end platform - **has to be brought** (4.4) | as A |
| parts never run live | a van whose drive has no collision floor under it outside the slab; two hidden collision objects | + a helicopter in this combination, the glass roof under Dog Days, 60 kill boxes | as A |
| effort (Retomoto = 1) | 0.5 | 0.9 | 0.5 |

MEASURED: route lengths and clearances by `python G:/kl_scratch/cfa_club/routes.py` (kl_fa_bots.Nav.path on the
trial build's mesh, links not used). For scale: the bots' routes on the park map are 206..225 m, least clearance
34..73 (READ re/bots.md 'M06'); Retomoto's two halves 207..221 m + 248..275 m with clearance 11..49 on its
stairs (READ re/bots_retomoto.md 1).
C starts with a walk-in, which the owner's taste rules out, and is listed for completeness.

### 4.2 Recommendation: A, 'Last call' - with B as the second stage on the same layer

Why A first: every part of it is a technique another map already uses, and most have been seen live (READ
CLAUDE.md 'Open work': F07 as host; F07's van re-laid by key rewrite on Retomoto and three FA maps; campaign
squads kept and started; a collision object switched off so that players walk through - Retomoto's window; one
bot squad on one mesh part). The switch on a squad's death is Retomoto's too, built there; that it was seen
firing is not in the notes I read. B is the better map - it is the campaign's own way, with
the campaign's own enemies standing along it - but its escape does not exist yet (4.4). A and B share the start,
the office, the loot, the dance-floor fight, the squads and the bots' first 107 m; B replaces A's last 80 m by
380 m of upper floors and roofs.

**The round, concretely.** Coordinates marked GUESS are proposals; everything else is a measured object position.

- **Start - in the middle of it.** The eight heisters stand in Yoko's office with the doors shut, the safe
  already emptied onto her desk; the club music comes muffled through the wall (the level's own
  `Yoko_Office_Suppress_Box_*` do that). START row: GUESS two rows of four at x 2700..3050, z 2420 and 2560,
  y 342, facing the inner door (+z, then -x): inside the office's mesh (113 m2; the campaign's own places there
  are checkpoint 9 (2605, 342, 2617) / (2991, 342, 2348), clearance 30 / 98). TRAITOR points GUESS behind them at
  z 2300. *(corrected by the second agent, MEASURED `skeptic/street3.py` part 6 and `skeptic/nav2.py`: the eight START
  places are sound - collision floor y 340 under each, 150 free in eight directions at chest height, all in mesh
  polygon 227, which is only 5.3 x 2.8 m (14 m2; Yoko's room proper has 46 m2 of mesh, the 113 m2 include the front
  office). But the TRAITOR row at z 2300 is wrong for x 2700..2817: those two points lie ON the desk
  `PC0100_M05_OfficeTable_01` (its top at y 413) and 51 off the mesh. Move the row east of the desk (GUESS:
  x 2900..3150 - mesh polygon 233 spans x 2867..3201, z 2219..2401; (2933 / 3050, 342, 2300) tested free).)* At GO + 2 s (GUESS) a host timer sends 'Activate' to both office door groups
  (`SI0108_M05_DaughterRoomDoorA_02`, `..B_01`): the doors slide open and Yoko's four bodyguards are in the front
  office (`FirstRun!Backroom!WaitingRoom` (2085, 354, 3178), (1967, 353, 3486); `SecondRun!YokoGuards`
  (2387, 354, 3319), (2378, 354, 3442)). That is this map's 'window blows'.
- **Loot - props that fit.** (a) The office: six stacks on and beside the desk `PC0100_M05_OfficeTable_01`
  (2700, 340, 2260) and the sofa tables (2988..3138, 380, 2530..2641), shown as briefcases - the Dead Men
  Fragile Alliance case model that `tools/kl_fa_loot.py` already puts on Retomoto's table (READ
  re/retomoto_loot.md 0) - 300,000 each (GUESS). (b) Bar tills: three stacks on dance floor 1's bar
  (`SI0102_M05_BarCounter_4m_01` (-1500, 20, 1006), `..._LeftCorner_01` (-1142, 20, 906)), 100,000 each. (c) On
  the way out: the ticket counter `SI0101_CounterA_01` (300, 0, -1200) and the coat check
  `SI0105_M05_Wall_B_WardrobeBooth_01` (-400, 100, 0), 50,000 each. (d) Greedy detours upstairs: the VIP bar
  `Si0109_M05_Bar_A_01` (1700, 860, 0) and the rave bar `Si0109_M05_Bar_B_01` (-3185, 460, 696), two stacks each,
  150,000. 15 objects, 2.8 million (GUESS on every value; Retomoto: 21 objects, 4.05 million). Money objects are
  F07's pool stacks re-placed, as on Retomoto (READ re/retomoto_fa.md 2: no entity is created).
- **The beat - 'exit blocked'.** The campaign shuts the entrance door behind Kane and Lynch (step 4 of 1.6); here
  it is shut from the round start (keep the single node `Doors!Entrance!CloseEntranceDoor`, a stock
  `MatPosAnimProxy`, and fire it from the round-start timer) and the street end of the queue lane is sealed by
  the campaign's own two collision objects (1.4). When both dance-floor squads are dead - their 'wiped out'
  lists -> a counter, the mechanism Retomoto's boardroom loot is built on (READ re/retomoto_fa.md 5) and this
  level's own office door hangs on (1.5) - or after 75 s at the latest (GUESS; so nobody is ever locked in), the door leaves and the two seals are switched off (`DeactivateGeom`), the three 'hunter' bodyguards
  come in from the wardrobe, and the van may be called. ASSUMED: switching the leaves off instead of playing
  the door's animation backwards (whether the 0..50 clip has a way back is not established).
- **Enemies - the club's own security.** Without touching a never-run controller: `WaitingRoom` 2 +
  `YokoGuards` 2 (pistols, front office), `FatBounceronWalkway` 1, `SecondRun!Dance#01` 3 and `Dance#02` 3 (SMG)
  on the two floors = 11 on the route, plus `Lounge#01` 3, `Lounge#02` 2, `Rave#01` 2, `Rave#02` 3 at the detour
  loot = 21 guards in 9 squads; kl_fa_author's rule needs one extension for them: a squad without a behaviour
  rout stays and is started by naming its own `Alert` child, a `SquadModifierBehaviour` (eAM_Activate +
  eALM_Alert) - that is how the campaign starts them (`AI_Players!Enemies!SecondRun!Rt\Way#01` names
  `Dance#01\Alert`, `Rave#01\Alert`: MEASURED `out/refs_M05_A.txt`, node.py), and how Retomoto's layer starts its
  boardroom squads (READ tools/kl_fa_author.py 395). *(corrected by the second agent, MEASURED `skeptic/squad2.py`,
  `skeptic/guards.py`: a child named `Alert` (eAM_Activate + eALM_Alert) exists under seven of these nine squads -
  Dance#01 / #02, Lounge#01 / #02, Rave#01 / #02 (all named by `SecondRun!Rt\Way#01`) and `WaitingRoom`. `YokoGuards`
  has none: its modifier is `SquadModifier` (eAM_NotSet), its ZSquadScript 'active' field is 0 and two of its lists name
  mini-cut nodes of dropped subtrees - it needs its flag set in data. `FatBounceronWalkway` has none either but is active
  from the load. And `Rave#01`'s two guards stand 105 / 154 units OFF the mesh, behind the rave bar counter (y 489..494
  over mesh y 460), where the campaign's bartenders stand: not 'usable as they stand'. All 58 guards otherwise lie on
  or within 30 of the main mesh part.)* With `AttachGeomToBone` stripped (ASSUMED harmless: it pins a
  prop to a bone, e.g. the hunters' `Flashlight_01`) the 'FirstRun' squads on
  the route add 19: `Surprise2` 2, `Dancefloor02a#01..03` 6, `On_Dancefloor#02` 3 (also lose `WarnBehaviourRout`),
  `SurpriseStairs` 2, `Hunters!HunterKillers` 3 (keeps its `HuntBehaviourRout`), `Bodyguards_First_Floor!Entrance`
  3 = 40 guards, weapons by kl_arms (the campaign gives pistols and MP5s). 'Police' are the dead heisters:
  AFTER_DEATH points at seven campaign actor places that are not kept - the entrance hall and the pavement:
  (-65, 21, -1307), (-141, 21, -1012), (314, 21, -1251), (143, 21, -544), (134, 29, -2398), (155, 31, -2654),
  (130, 31, -2320) (the last three lie in or beyond the sealed lane and come alive when it opens; GUESS whether to
  move them in). The level has no police of its own and no room for a street battle (1.3): the threat is
  inside. Civilians: up to 17 campaign actors with their own flee points (1.5) - optional, second step.
- **Escape - F07's van at the front door.** The van (`Animation/F07/F07_Escape_Vehicle_01.zip`, kept and re-laid
  as `tools/kl_map_escape.py` does on M01 / M02 / M03: READ re/map_escape.md 9, 10) waits out of sight on the
  pavement line to the west, GUESS (-5200, 32, -3100), drives +x along z -3100 (the strip is free of collision,
  1.3), and stops with its origin at GUESS (1000, 32, -3100) so that the boarding box 337 behind it stands at
  (660, 32, -3100) on the slab, 9 m from the lane's mouth *(corrected by the second agent: 7.2 m in a straight line
  from the lane's mouth (118, 20, -2623), as the table in 4.3 says; and the drive in as proposed, x -5200 -> 1000, is 62 m,
  over the planner's own `LIMIT_IN` of 60 m (READ tools/kl_map_escape.py 693, itself a GUESS), and its last 22 m cross the
  slab on which the crew waits (lane z -3210..-2990 of a slab z -3460..-2580))*; it leaves +x. Road height = the slab's y 30 + 2,
  given as a constant: the planner's 'ground under the path' finds nothing west of x -1220 (the van is
  key-framed and needs no floor: READ re/retomoto_fa.md 9.3 - Retomoto's van first drove 40 under the road).
  Exit trigger box GUESS (300, 150, -2950) half (1400, 250, 450) = the slab. Level bounds: F07's bound trios put
  just outside the slab's three open edges (x -1220, x 1820, z -3450), and the campaign's three single
  `Specials!KillBox` nodes re-placed below those edges (GUESS), because beyond the slab there is no floor.
- **Music - the club's own, and it comes with the map.** The kept subtree `Locations/M05_A/M05A_Audio.zip!STREAMS!
  Inside!Music!*` plays two tracks as positional layered streams (clean / muffled / 3D, with boxes that muffle
  them on the stairs and in the office). They need their clips in the merged PC_Def.str (4.6). ASSUMED they play
  from the load: nothing in the level starts them, one campaign object stops them.
- **Bounds inside:** none needed - the building is closed; the two fire doors to the storage stay shut in A.

### 4.3 The AI heisters' route for A, as stations on the mesh

MEASURED (routes.py; every station on the main mesh part, one squad, no hook teleport needed):

| # | station | place | leg | least clearance |
|---|---|---|---:|---:|
| 1 | start, office | (2900, 342, 2450) | | 108 |
| 2 | inner office door (opens at GO + 2) | (2600, 347, 3313) | 11 m | 36 |
| 3 | front office: ENTERS_BANK plane, first fight | (2000, 354, 3300) | 6 m | 36 |
| 4 | walkway | (780, 371, 2747) | 15 m | 35 |
| 5 | dance floor 2, under the walkway: hold | (-864, 40, 2491) | 27 m | 33 |
| 6 | dance floor 1, the bar: loot wait (`TriggerLootDepleted`) | (-1100, 20, 1150) (mesh 116 off: the bar itself) | 21 m | 11 |
| 7 | stairs / checkpoint 4 | (-55, 160, 320) | 27 m | 11 |
| 8 | wardrobe: hold until the door goes; EXITS_BANK plane | (-4, 180, -240) | 38 m | 70 |
| 9 | entrance hall | (-414, 100, -604) | 8 m | 44 |
| 10 | queue lane, club end | (105, 20, -1500) | 14 m | 35 |
| 11 | queue lane, street end: level exit box (calls the van) | (105, 20, -2600) | 11 m | 35 |
| 12 | beside the van's rear, in an `AllyEscapeBox` | (660, 20, -3100) | 7 m | 35 |

Total 187 m. The office loot is at station 1 (the bots start on it). The queue lane is 0.96 m wide on the mesh
for 12.5 m: seven bots and a human pass it in single file (LIVE, 6).
*(corrected by the second agent - three points on this table.
(a) Station 3 puts the ENTERS_BANK plane at the front office, AFTER the office loot of station 1. A bot's stage 1 is
'a place inside an ENTERS_BANK box' and the planner's order is START row -> ENTERS_BANK -> the loot (READ re/bots.md
103, 297, 435: 'do they pass the ENTERS_BANK place and then pick money up'): as drawn, six of the fifteen stacks
(1.8 of 2.8 million) lie before stage 1. The box belongs INSIDE the office, round the START row (as Retomoto's
`Trigger_POI_TheLootArea`: READ re/retomoto_fa.md 68).
(b) Station 12 'in an `AllyEscapeBox`': stock F07 has no such controller (MEASURED `skeptic/f07.py`: 0; F08's helicopter
has the one the report saw). Under F07 the rule is the other one: the boarding action on the same mesh part (READ
re/bots.md 297) - which holds here.
(c) The mesh lane is 0.96 m (x 70..166), but the collision lane is wider: first collision at x 81 to the west and
x 348 to the east at heights 60 / 120 / 170 (MEASURED `skeptic/street3.py` part 4; below y 60 not tested - a low queue
rail would not show) - a human has up to 2.7 m, the bots 0.96.
Route length by my own path over polygon middles: 191 m (`skeptic/nav2.py`); roof route 498 m (`skeptic/nav4.py`).)*

### 4.4 Stage two: B, and the helicopter that has to be brought

The roof half is in the build as it is: the mesh carries it (routes.py: 135 m from the office to the 2nd lounge
by way of both dance floors, then 35, 78, 32, 7, 12, 8, 12, 71, 27, 11, 43, 17 m), the campaign's SecondRun
squads stand along it (1.5), its beat is the campaign's own objective (the storage fire door: open it when the
rave squads are dead; then the roof door; both are 'Activate' to a door group), and the set piece is the glass
roof: 27 m of panes over the car showroom, each pane cracked by a shot and given way after five steps on it,
with its own kill box (1.6 step 9). Needed besides A's layer: the storage `HeroColi` switched off, the three
campaign `Specials!KillBox` kept where they are (4954, 103, 4959), (4954, 500, 5572), (5747, 335, 5384) (the car
showroom floor), the level exit and the boarding on the end platform (36 m2 of mesh, platform 10 x 8 m).
The helicopter. MEASURED in this job:
- Stock F08 lands one on a ROOF: `Gameplay!99_EscapeHelicopter#01`, ONE top-level subtree of 64 nodes
  (`python G:/kl_scratch/cfa_club/heli.py F08`): `V_Police_Helicopter_00` (`OnlineEscHavokCar` +
  `OnlineEscVehicleController`), a rope ladder, four incoming flights and one leaving, each a `ZEditorSpline`
  blob of 5..6 world waypoints, a boarding box (`PlayerAction` 'EnterVehicle' + `AllyEscapeBox`) at
  (8481, 2463, 10327) with the hover point 645 above it, its own monitor and exit trigger. Outside itself it
  names only four flares of F08's roof, `Effects/Helicopter_Damage_01.zip` and one FASpecials trigger.
- (H1) F08 as the host: the plain graft builds (3.2). Keeping the subtree by name (as kl_fa_author keeps F07's
  vans) and re-drawing 26 waypoints is authoring, not format work. But no Dead Men map has ever run under F08,
  and every tool of the map pipeline (bots, guns, tune, author tables) names F07's objects.
- A rigid move of F08's five splines onto the end platform does not fit: for every turn in steps of 30 degrees
  at least two segments cross the club's collision (mostly `SO0004_M05_BuildingJ_01`, the building beside the
  platform) (`python G:/kl_scratch/cfa_club/helifit.py`). The flights have to be drawn for this roof; the test
  that checks them exists (kl_map_escape.Ground.between).
- (H2) Dead Men's own escape chopper from the park map (`M06_FA_A` `EscapeSetup!EscapeChopper`, 21 nodes, two
  splines of 11 and 17 points) is the one that HAS run live under F07 with a human and seven bots boarding it
  (READ CLAUDE.md 'LIVE NIGHT 2026-10-11': park, 7 of 7 escape; re/bots.md 'M06'). Bringing it is a three-source
  build, and both orders fail today in tools/kl_hvk.py, not in the game: F07 + chopper only ->
  `ValueError: 3 MOPP codes for 0 static placements` (`python tools/kl_maps.py one "<work>/build/cfa/club/heli_only"
  F07 M06_FA_A --m-drop "Locations/*,..."`); (F07 + M05_A) + chopper only -> `TypeError: 'NoneType' object is not
  subscriptable` at kl_hvk.py:165 `fill[0].clone` (`python G:/kl_scratch/cfa_club/chain3.py`). Cause: a map side
  without any static collision placement - no filler to pad with. Fix: take the filler from the systems side
  when the map has none, and let kl_maps.chain give each step its own drop list.
- (H3) F08's whole map side on F07's systems builds with one problem (two `OnlineEscVehicleMonitor`)
  (`python tools/kl_maps.py one "<work>/build/cfa/club/dd_pair" F07 F08`): a Dog Days helicopter CAN ride as map
  content under F07; cutting it down to the helicopter alone meets the same kl_hvk case as H2.
So B is blocked by nothing in the game that was found, but by one small tool case (H2 / H3) or by proving a
new host (H1). That is why it is stage two.

### 4.5 What makes the map worth having

There is no Fragile Alliance sibling of this place, in either game: it would be the only night club, the only
map whose loot room is where you start, and (stage two) the only one that goes up instead of out. Against
Retomoto, the other Tokyo map: Retomoto is offices and a street; this is three floors of bars under a light
show, at a third of the route length in stage one.

### 4.6 Music and voices in Dead Men's PC_Def.str

MEASURED (`python tools/kl_str.py list "<DM>/PC_Def.str" M05`, `out/str_m05.txt`: 310 entries):
- Music, two interleaved sets of four PCM layers each (32 kHz):
  `LevelSetup/Level/M05_A/Music/M05_A_Club_Layers` (202.7 s; 32,435,600 bytes) =
  `Music/InHouse/Japan/M05_A/M05_A_Club_Clean.wav`, `_Clean_3D`, `_Muffled`, `_Muffled_3D`;
  `LevelSetup/Level/M05_A/Music/M05_A_Club_2_Layers` (309.7 s; 49,547,800 bytes) =
  `M05_A_Club_2_Clean.wav`, `_Clean_3D`, `_Muffled`, `_Muffled_3D`.
- Ambience beds (Vorbis): `SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav` (116.6 s),
  `.../Inside/M05_Club_Ambience_01.wav` (293.4 s, the crowd's noise), `.../Inside/Yoko_Office_Ambience.wav`
  (174.8 s), `.../Outside/Roftop/Ambience_Rooftop_M05_A.wav` (120.0 s), `.../Outside/Street/Street_01.wav` (210.6 s).
- These twelve are exactly the 'stream clips missing' of the trial build, about 88 MB (the two sets 82.0 MB, the
  five beds 6.5 MB). `python tools/kl_str.py build M05_A --extend` is the step that adds a level's clips (READ
  kl_str.py docstring); MEASURED `python tools/kl_str.py need M05_A`: for the WHOLE level (it does not apply the
  campaign pre-pass, so the campaign's dialogue counts) 398 blocks, 130.1 MB. Installing PC_Def.str is the game
  holder's job. Until then the club is silent, not broken.
- Voices: 293 dialogue entries under `Dialog/M05/Dialogue/`. Worth carrying for a round (Kane / Lynch lines, so
  only when they are in the crew - klhook/kltalk.c's rule): `M05_OneLiners/M05_HeroOrdersM05Specific` (31:
  FollowMe, GoThere, ShootAtMyMark), `M05_LynchShotAt` / `LynchGo` / `LynchFollow` / `LynchOpenDoor` (6 each),
  `M05_MiscDialogueHeroLynch/M05_HeroKillingCivilians` (if civilians stay), and `Situations/M05_Doors_Closed`
  (12 lines) - the campaign's own lines for the beat of 4.2. Guards: `Situations/M05_Alcove/M05_Alcove_010_JapGuard`,
  `M05_Argue_In_150_Guard`, and the Japanese one-liners Retomoto already merged (READ re/retomoto_fa.md 6).

## 5. What has to be authored

Kinds from tools/kl_fa_author.py (READ: its PLACE / ROLE / SPAWN tables and re/retomoto_fa.md 2). 'Host' = a stock
F07 object kept by name and re-placed; nothing is created.

| object | the level holds | to do |
|---|---|---|
| settings, 'IsMultiplayerLevel' define, speakers, briefing trigger, AIMonitor, escape-vehicle monitor | no | host, unchanged (F07's briefing lines) |
| 8 START, 4 TRAITOR, 7 AFTER_DEATH, 19 UCC, 18 + 7 team-mode points; 16 player groups | no | host; office rows (GUESS), police points = seven campaign actor places (4.2) |
| spawn cameras, team-mode stage triggers | no | host; GUESS positions (three stages: walkway, wardrobe, pavement) |
| loot marker, ENTERS_BANK / EXITS_BANK planes, escape marker | no | host; front office door, wardrobe, the slab |
| loot: 15 money objects | no money object; the props to put them on: desk, sofa tables, three bars, ticket counter, coat check (4.2) | host pool stacks; briefcase model by kl_fa_loot |
| round-start timer chain | no | host `TriggerDelay2` + `AIDWrapper` (as Retomoto's blast): office doors 'Activate', entrance door shut, squads on |
| doors | **yes**: five door groups with `RelayMessageList` + `MatPosAnim` (1.4) | wire only; keep `Doors!Entrance!CloseEntranceDoor`. *(corrected by the second agent: not only - each dropped `DoorCtrl` also fired the music's muffle switch through its field 4: `...Audio.zip!STREAMS!Inside!Music!GeomActivator_Door_01 / _02 / _StorageRoom_01` ('Doors_Opening', on `Yoko_OfficeEntrance_Suppress_Box_01`, `Yoko_Office_Suppress_Box_01`, `Club_02_Clean_3D_Suppress_Box`) and the matching `GeomDeactivator_*` ('Doors_Closing'). The layer must send 'Doors_Opening' to those kept nodes with each door, or the music stays as muffled as behind a shut door: MEASURED `skeptic/squad2.py`, `skeptic/music.py`; the effect is ASSUMED from the names)* |
| 'floor cleared' counter and switch | no | host `TriggerCounter` + `DeactivateGeom`; squads' field 8 -> counter |
| invisible walls | **yes**: entrance `HeroColi`, `Plane01` (the seal of the beat), storage `HeroColi` (stage two) | targets of the switch |
| squads | **yes**: 9 squads / 21 guards usable as they stand, 19 more guards after stripping `AttachGeomToBone` (1.5) | `campaign_names`; rule extended to squads without a rout; kl_arms |
| civilians and flee points | **yes**: 17 actors, 16 points | optional; strip their mini-cut controllers |
| cover | **yes**: the map's props carry `CoverBoxH` (141 names) and `CoverBoxM` (36); the pre-pass keeps 26 cover / no-cover boxes (11 `PlayerCoverCollision`, 15 `NoCoverBox`) | nothing (kl_fa_cover later) |
| level exit trigger, van, boarding box, BOARDS trigger, escape cameras | no vehicle at all | host van archive; a two-point lane at fixed height (kl_map_escape.van_* with a road-height constant: small tool change) |
| level bounds / kill boxes | five campaign bounds in the wrong places (drop them); three single `KillBox` nodes (keep, re-place) | host bound trios at the slab's edges |
| music | **yes** (the audio subtree) | `kl_str.py build M05_A --extend`; optionally settings field 157 |
| bot squad | no | tools/kl_fa_bots.py on one mesh part (4.3) |
| stage two: helicopter, its flights, boarding on the roof | no | 4.4 |

Size of the work: **0.5 x Retomoto for stage one.** Less than Retomoto because: one source level, not a chain (no
nav_join, no name clashes, no second static Havok part); one connected mesh, so no join hook and one bot squad;
no blast sequence and no ledge to prove; the doors and the seal are already objects of the level; lighter than
any map so no size work. Not less than half because: a new author table for a new level (every place above), the
squad rule's extension and the `AttachGeomToBone` strip, the van on a strip without collision, bounds around a
slab with nothing beyond it, three never-run controller kinds that may each cost a live round to drop.
Stage two adds about 0.4: the kl_hvk case or the F08 host, the flights, the roof checks.

Order of steps to a first load:
1. kl_mat.py: the MIRRORED case (3.1). Until then nothing of the pipeline reads M05_A.
2. `kl_maps.py one <out> F07 M05_A --campaign --m-drop "Boundaries!*" --heroes`, which needs a `HERO_AT` entry
   for M05_A in kl_maps.py (checkpoint 9: `Checkpoints!CP_09_PosP1` / `P2`, in the office), then `kl_graft.py lighten`. Direct boot: does
   it load, do the light show and the beat object run, where does the player stand, are the doors shut.
3. `kl_str.py build M05_A --extend` and the merged stream file installed: the club has its music.
4. The author table (start, loot, doors, squads, seal, van, bounds) -> `kl_fa.check` 0 CRASH / 0 BROKEN,
   `kl_impact` 0 -> first Arcade round from the menu.
5. Bots (`kl_fa_bots.py`), then wardrobe, gun looks, map tune, cover as on the shipped maps.
6. Stage two.

## 6. Risks, and what only a live run can settle

In the order a first run meets them:
1. **Does it load?** Three controller kinds no Dog Days level has ever run stay in the map (3.5); each has a
   drop-it fall-back. One load decides.
2. **The light show and the music together** (`PositionLightControl` reading `Beat_M05`'s converted clip and the
   stream objects): works, is static, or faults. Whether the music objects play from the load (4.2).
3. **Lamps not drawn**: three of the four shader-less materials are club lights; how dark the club is without
   them and without the crowd is for the owner's eyes. An empty dance floor is the map's weakest point.
4. **The four closed doors**: that 'Activate' to a door group opens it in Dog Days (the bank's garage doors did:
   READ tools/kl_map_escape.py 835), and that a switched-off leaf / seal stops colliding (Retomoto's window did).
5. **Stairs**: the collision walk test does not climb any stair of this level (1.4). One scripted walk
   office -> walkway and stairs -> 2nd lounge -> 3rd floor settles it.
6. **The queue lane** (0.96 m of mesh, 12.5 m): bots in single file under fire; the human between them.
7. **The pavement**: a van driving where there is no floor; players, dropped money and bodies at the slab's
   edges; what a level bound does to someone on the slab's rim (not established: READ re/retomoto_fa.md 11.1).
8. **Squads without a behaviour rout** switched on by flag; guards after the `AttachGeomToBone` strip (where the
   attached prop ends up).
9. **The seal as a beat**: the dance-floor squads' 'wiped out' lists are empty in the campaign and get wired by
   the layer. The mechanism is this level's own (the campaign opens the office door on the waiting-room squad's
   list, 1.5) and Retomoto's table loot hangs on it; that it fires for squads switched on by flag is not seen.
10. Stage two only: the helicopter under whichever way it is brought; the glass roof's panes, trigger boxes
    (`ECPS_BOTH`) and kill boxes under Fragile Alliance players and bots; the end platform's 36 m2 for eight.
11. Later: the HFlow crowd (dead code in kl2.exe).
Not a risk here, measured: size, chunk table, textures, materials, sound bank, mesh conversion, dangling paths.

## 7. Verdict

**feasible-with-work.** The Tokyo night club can become a Fragile Alliance map, and a good one: the whole
building - two dance floors, the lounges, the rave room, Yoko's office, the roofs - comes across in one piece
that the game's AI can walk from the pavement to the last roof, its model and texture data are the smallest of
the seven candidates,
and its own music, light show, doors and bouncers come with it. Three things stand between it and 'ready': a
one-line fault in a converter that stops every tool from reading the level today; the place has no getaway
vehicle and almost no street, so the first version has to end with the borrowed van pulling up on the pavement
at the front door; and the dancing crowd, the thing everybody remembers, cannot be carried yet - the first
version is a club with music and lights and security, without the clubbers. The round I recommend starts with
the crew shut in Yoko's office with the money, breaking out through her bodyguards, across the dance floors,
out of the front door once the floor is cleared - about half the work Retomoto was, all of it with parts the
other maps already use. The campaign's own, grander way out - up through the building, across the glass
roof, to a helicopter - is all there except the helicopter, and is the natural second stage.

## 8. Verification (second agent)

2026-10-11, agent cfa-club-skeptic. OFFLINE; nothing installed, no tool edited. My scripts:
`G:/kl_scratch/cfa_club/skeptic/*.py` (outputs `G:/kl_scratch/cfa_club/skeptic/out/`); my own trial builds
`<work>/build/cfa/club/sk_stock`, `sk_patched`, `sk_light`, `sk_ward`, `sk_keep9`, `sk_keep27` (+ `_light`, `_ward`),
`sk_nobounds`, `sk_host_f08`, `sk_heli_only` (every archive deleted again, result.json / log.txt stay). I did not reuse
the first agent's outputs: every number below was produced again, most of them by a script of my own that reads the
STOCK Dead Men level or my own rebuilt archive. `street3.py`, `walk5.py`, `walk6.py`, `hack.py`, `bounds.py` read the kept
archive of `sk_patched`; to run them again rebuild it first:
`python G:/kl_scratch/cfa_club/run_maps.py one "<work>/build/cfa/club/sk_patched" F07 M05_A --campaign --keep` (47 s).
Verdict after the checks: **feasible-with-work stands.** No number of the report was refuted; nine statements were
corrected (8.2), two of them about what the trial build was measured WITHOUT (the guards) and about a test that was
read too widely (the stairs); the round as drawn has five faults of placement or order that an author table would
have hit (8.4), none of them a blocker. What I would tell the owner differently from section 7: the map's weak parts
are its ESCAPE (a van on a 30 x 9 m island of collision in a street that is drawn but not there) and its EMPTINESS
(no crowd, no enemy that arrives from anywhere) - not its size, its mesh or its doors.

### 8.1 Confirmed (re-derived)

1. Stock graft fails as stated. MEASURED `python tools/kl_maps.py one "<work>/build/cfa/club/sk_stock" F07 M05_A --campaign`:
   `ValueError: material 538 (Locations/M05/Concrete/Concrete_Walkway_01a_M05): TEXT/TILU value b'MIRRORED' never occurs in
   Dog Days` at kl_mat.py:397. READ kl_mat.py 394-397: the guard compares per (node, key).
2. MIRRORED: MEASURED `python G:/kl_scratch/cfa_club/skeptic/mat2.py` (own scan of every stock .MAT of both games):
   Dog Days TEXT/TILU = '' 27, NONE 2,460, TILED 27,965; TEXT/TILV = '' 27, MIRRORED 3 (F04 slot 443), NONE 2,507,
   TILED 27,915. Dead Men TILU MIRRORED 4 = M05_A slot 538 (3) + M01_A slot 615 (1); none on TILV.
3. Patched graft: MEASURED (the first agent's wrapper re-run into `sk_patched`, 47 s): ok, problems 11 (1 sound + 1 CRASH
   settings + 9 BROKEN), dangling [], entities 26,106, rooms 20, textures 1,676, materials 1,135, prm_chunks 52,934
   (table 52,935), sounds / waves 4,701 / 4,552, archive 284.4 MB. `python tools/kl_impact.py <folder>`: problems 0.
4. Navigation mesh: MEASURED `python G:/kl_scratch/cfa_club/skeptic/nav2.py`, `nav3.py` (own parse of the STOCK Dead Men
   block; connectivity twice: by the edges' neighbour fields and purely by shared edge end points): 437 polygons, 55
   areas, 106 waypoints, 6 links (kind 1: 2, kind 2: 4); 11 parts both ways, sizes 401, 13, 13, 2, 2, 1 x 6; the
   largest x -4950..7453, y 20..1904, z -3502..5741 (I get 5,034 m2, the report 5,042). All twelve route stations of
   4.3 and the end platform lie on it.
5. Census: MEASURED `python G:/kl_scratch/cfa_club/skeptic/census2.py` (own): 0 ZHavokCar / ZHeli / ZAnimatedVehicle /
   ZSpawnPoint / OnlineMoney*; 77 ZFFActor = 60 ZSoldier (58 guards + Yoko + Lynch) + 17 ZCivilian; guards 32 in 17
   FirstRun squads + 26 in 10 SecondRun squads; 14 squads / 27 controllers AttachGeomToBone; one name with
   'Tokyo' (a civilian). ZHFlow 2 + ZHFlowFF2M05 4 + ZHFlowLnkObj 10.
6. Doors and seals: MEASURED `python G:/kl_scratch/cfa_club/skeptic/street3.py` part 5: the four office door leaves
   stand in the planes x 2500 and x 1500 (z 3167..3488, y 348..610), the two fire doors closed, the entrance leaves
   at x -627..-148 and 162..641 (open 3.1 m); entrance `HeroColi` is a box x -13..369, z -2612..-2335, `Plane01` a
   plane at z -2538.
7. Walk test, the part round A rests on: MEASURED `python G:/kl_scratch/cfa_club/skeptic/walk5.py` (kl_escape.Walk on
   my archive): as loaded only the office is reached (137 m2); with the FOUR OFFICE DOOR LEAVES out everything to
   the middle of the queue lane; the pavement only with entrance `HeroColi` AND `Plane01` out (each alone is not
   enough).
8. Street: MEASURED street3.py parts 1-3 (20-unit grid): collision floor outside the building x -1200..1800,
   z -3460..-2580 at y 30 (one entity, `M05_A_Outside_Street_01a\ColiObj_01`); none under the van line outside it;
   no map collision 25..220 over y 30 and no convex / key-framed body in a 220-wide lane along z -3100 from
   x -5200 to 5700.
9. Load blocks, the report's own case (no actors): MEASURED `python tools/kl_graft.py lighten "<sk_patched>" "<work>/build/cfa/club/sk_light"
   --load trim,slim,fxc,wav` and `python tools/kl_chars.py wardrobe <sk_light> <sk_ward> --plates=wolf,dallas,chains,hoxton`
   (`skeptic/out/lighten.txt`, `ward.txt`): lightened .prm 36,626,064, .fxc 9,071,684, .ANM 21,662,164, .WAV 11,191,104 B,
   table 52,935; with wardrobe .prm 54,263,120 B, table 52,935 ('20989 of the base's 24318 dead indices taken'), kl_chars
   check problems 0, kl_impact problems 0 - byte for byte the report's numbers. Stock F07 60.6 / 7.7 / 20.6 / 17.4 MiB,
   F01 63.5 / 5.9 / 19.8 / 14.7 (`python G:/kl_scratch/cfa_club/skeptic/stock_sizes.py F07 F01 F08`).
10. Preflight: MEASURED `python tools/kl_maps.py preflight <sk_patched folder>` (`skeptic/out/preflight.txt`): CRASH 2, RISK 16,
    NOTE 64; first-timers that stay: ZEnvSampler x3, ZIKLNKOBJ x2 + StartAnim x2, PositionLightControl x7,
    ShotActivateDamage x5, SoundSpline x1; '124 KEYS chunks, every one found by keys_tracks' (the doors' key data is in the
    .buf); 12 stream clips named missing.
11. Level bounds: MEASURED `python G:/kl_scratch/cfa_club/skeptic/bounds.py`: 15 `Boundaries!` nodes kept = 5 bounds with two
    warning boxes each; `LevelBoundEntrance` hidden (flag 0x400), the four at the wardrobe (200, 175, -251), the stairs
    (399, 165, 218), the roof (3220, 1189, 4392) and the roof end (7311, 1887, 4584) not. The 26 kept `Specials!` are 15
    NoCoverBox + 11 PlayerCoverCollision (no kill box is kept). Without them (`--m-drop "Boundaries!*"` into `sk_nobounds`):
    ok, 26,091 entities, 0 dangling, 11 problems, kl_fa adds 'DEGRADED bounds: no LevelBound'.
12. Squad wiring: MEASURED `python G:/kl_scratch/cfa_club/skeptic/squad2.py` (stock level, Dead Men field order):
    `FirstRun!Backroom!WaitingRoom` ZSquadScript[6] = [`Doors!Daughter#02!COOP_DoorDaughter`, `...!SP_DoorDaughter`], which
    lead to `Door_Daughter#02` (DoorCtrl on `SI0108_M05_DaughterRoomDoorA_02`); the six SecondRun floor squads' `Alert`
    children are named by `SecondRun!Rt\Way#01` (GatePath); 14 squads / 28 guards carry AttachGeomToBone (census2).
13. Exe and stock use: MEASURED `python G:/kl_scratch/cfa_club/skeptic/exe2.py ...` (21 stock Dog Days levels read): the
    HFlow strings are the same set in both exes (30 by my rule for a string, the report counts 32) and no stock level
    has an HFlow class; DoorCtrl, AttachGeomToBone, PositionLightControl, ShotActivateDamage, StartAnim,
    WarnBehaviourRout, ZIKLNKOBJ: registered in kl2.exe, in NO stock level. What the round's door / seal / squad
    mechanics rest on IS stock Dog Days: MatPosAnim (21 of 21 levels), RelayMessageList (12 levels, F01 F02 F03 F05
    among them), DeactivateGeom (21), SquadModifierBehaviour (20), PathBlocker (19). `skeptic/hflow.py`: six flow
    objects, field 22 = 750 / 100 / 300 / 700 / 80 / 50 (sum 1,980).
14. Music: MEASURED `python tools/kl_str.py list "<DM>/PC_Def.str" M05` (310 entries): the two layer sets (0x1eeed90 =
    32,435,600 B, 202.7 s; 0x2f40a18 = 49,547,800 B, 309.7 s), five ambience beds, 293 `Dialog/M05` entries.
    `skeptic/music.py`: the 84-node audio subtree is named from outside only by `Specials!KillMusic` (stops it), three
    DoorCtrl (muffle switches, see the correction in section 5) and seven PositionLightControl (read it): nothing starts
    the music, so 'plays from the load' has no counter-evidence in the files.
15. Helicopter: MEASURED `bash G:/kl_scratch/cfa_club/skeptic/heli_builds.sh`: F08 as host builds (26,105 entities, 44,848
    chunks, 11 problems, 0 dangling); F07 + chopper-only map fails with `ValueError: 3 MOPP codes for 0 static placements`
    (kl_hvk.py:54); `python G:/kl_scratch/cfa_club/chain3.py` again: step 2 `TypeError: 'NoneType' object is not
    subscriptable` at kl_hvk.py:165. `skeptic/heli2.py`: F08 `Gameplay!99_EscapeHelicopter#01` 64 nodes, five
    ZEditorSpline, boarding box (8481, 2463, 10327) with PlayerAction + AllyEscapeBox; M06_FA_A `EscapeSetup!EscapeChopper`
    21 nodes, two splines.
16. `python tools/kl_whoref.py M05_A ...` dies at the same kl_mat.py:397 line (MEASURED).
17. What was NOT in the report and speaks FOR it: with all 27 enemy squads kept the graft still verifies (0 dangling
    paths, 10 problems = the same list minus 'no police'), and round A's whole way out passes the collision walk test
    once the four office door leaves and the two entrance seals are out (item 7 above).

### 8.2 Corrected (each is also marked in place, 'corrected by the second agent')

1. **Sizes are for a level without its enemies** (section 0, 3.3). With the 27 enemy squads kept: lightened .prm 41.2
   MiB (not 34.9), with wardrobe 58.0 MiB (not 51.7), chunk table 53,898 (not 52,935). Below stock F07 in sum all the
   same (82.1 / 98.9 against 106.4 MiB).
   How: `skeptic/run_keep.py`, `keep_chain.sh`, `out/keep_chain.txt`.
2. **'The walk test climbs no staircase'** (1.4, 'needs live' 5): it climbs every UP stretch of round A (lane ->
   entrance hall -> wardrobe; dance floor 1 -> stair landing). Three staircases remain unclimbed by the test (dance
   floor 2 -> walkway, 2nd -> 3rd floor, the long roof stair). How: `skeptic/walk5.py`, `walk6.py`.
3. **Hero collision list** (1.4): besides the three objects the campaign switches there are nine permanent invisible
   ones that nothing names (`ColiObj_HACK_Plane01` in the stairs room and in the 2nd lounge, `ColiObj_HERO_Box01 / 02`
   in the stairs room, five `ColiObj_HERO_*` on the roofs). They are part of the campaign's own walkable space; listed so that nobody takes them for a new wall.
   How: `skeptic/hack.py`.
4. **TRAITOR row** (4.2): two of the four GUESS points lie on the desk. How: `skeptic/street3.py` part 6.
5. **Squads 'started by their own Alert child'** (4.2): true for 7 of the 9 squads; `YokoGuards` has no such child
   and is inactive, `Rave#01` stands off the mesh. How: `skeptic/squad2.py`, `guards.py`.
6. **Van** (4.2): 7.2 m, not 9 m, from the lane's mouth; the drive in is 62 m against the planner's 60 m limit and
   crosses the waiting crew's slab. How: arithmetic on the report's own points; READ kl_map_escape.py 693.
7. **ENTERS_BANK after the loot** (4.3): the stage order puts the box before the loot. How: READ re/bots.md 103, 297.
8. **`AllyEscapeBox` at the van** (4.3): F07 has none. How: `skeptic/f07.py`.
9. **Doors are 'wire only'** (5): the dropped DoorCtrl also drove the music's muffle switches. How: `skeptic/squad2.py`,
   `music.py`.
Not corrected, but weaker than it reads: the fix proposed in 3.1 ('accept for TILU what Dog Days has for TILV') is
still ASSUMED. READ kl2 0x8e7c55..0x8e7d48 (`python debug/dasm.py 0x8e7c30 0x8e7cd0`): the material reader fetches
'TILU', 'TILV', 'TILW' by the same lookup (0x8823e0) and hands the three value strings together to one virtual
routine; the text 'MIRR' occurs nowhere in kl2.exe (`skeptic/mirrored_exe2.py`), so how a value name becomes a mode
was not found. Writing `TILED` for that one walkway material is the safe case.

### 8.3 Could not be verified (offline, or not re-derived)

- That NOTHING DRAWN stands in the van's lane: I tested collision and entity origins only (one entity with a model has
  its origin in the strip - the slab's own collision object). A drawn-only obstacle (queue rail, sign, canopy) would
  not show. The far traffic lane (z -5305) and x beyond +-6000 were not re-tested; the four parked cars were seen as
  entities at z -3525..-3715 but their bodies not re-measured.
- `helifit.py`'s result (F08's flights moved rigidly onto the end platform cross the club's collision at every turn):
  not re-run. It only matters for stage two.
- The report's per-region areas (`places.py`), the pictures, the 141 / 36 cover-box counts, the campaign flow of 1.6
  beyond the objects I resolved (doors, squads, checkpoints named by them): not re-derived.
- Everything the report itself lists under 'needs live' stays open; my offline checks moved none of it. Above all:
  whether the three never-run controller kinds load; whether the light show and the `Beat_M05` clip (converted by
  kl_anm's own GUESS) run; whether a door group's 'Activate' opens and STAYS open without its DoorCtrl (the DoorCtrl
  carries a time value, field 2 = 30 / 10); whether `DeactivateGeom` frees `Plane01` (flags 0x308; no campaign object
  ever switches it) as it frees `HeroColi`; what a key-framed van does to players standing in its lane.
- 'Effort 0.5 x Retomoto': a judgement. Nothing I measured contradicts it for stage one, but see 8.4 (6) and (7): if
  the owner wants a contested escape and a walled pavement, both are new work that Retomoto did not need.

### 8.4 The round attacked as a design (MEASURED where a script is named; else READ / judgement)

What holds:
- START on walkable ground, not in geometry (8.2 item 4 for the exception). One connected walkable way from the START
  to the van: on the mesh (one part) AND by collision (8.1 item 7), with exactly six objects to switch: D1, D2, D04, D05
  at GO + 2 s; `Inside_Entrance_01a\HeroColi` and `\Plane01` at the beat. No lift, no cut scene, no jump point on it.
- The escape vehicle exists and needs no Dead Men .ANM: stock F07 holds three key-framed vans
  (`Animation/F07/F07_Escape_Vehicle_01..03.zip`, 223 nodes each; `skeptic/f07.py`), re-laid by key rewrite on four maps.
- Loot objects: F07 has 138 OnlineMoneyCtrl to re-place; 15 are asked for.
- Enemy numbers: 40 guards + 7 bots + 1 is below what Retomoto runs (63 + 7). No sibling Fragile Alliance map exists.

Faults of the round as drawn (all fixable in the author table):
1. ENTERS_BANK plane after the office loot (8.2 item 7).
2. TRAITOR points on the desk (8.2 item 4).
3. Loot places are the props' ORIGINS, and four of the nine lie more than 1 m from the walkable mesh: bar corner
   `..._LeftCorner_01` 135, coat check booth 166 (its inside is a separate 13 m2 mesh part: the attendant's side),
   VIP bar 235 (its nearest mesh is the 6 m2 strip BEHIND the bar), rave bar 107 (`skeptic/nav3.py`). The stacks have
   to go onto the public side of each counter; pick-up reach for bots was not established.
4. `YokoGuards` not started, `Rave#01` off the mesh (8.2 item 5).
5. The van's 62 m drive in (8.2 item 6).

Weaknesses of the place that no table fixes:
6. **The escape is on an island.** Collision floor outside the door: x -1200..1800, z -3460..-2580 (273 m2 with the
   lamp bases; MEASURED `skeptic/street3.py` part 1). The AI mesh of the pavement goes on for 25 m to the west and 40 m
   to the east (x -3765..5786; MEASURED `skeptic/nav2.py`) - ASSUMED the drawn pavement does too - and the road lies in
   front: whoever walks 13 m west, 17 m east or 8 m towards the parked cars from the lane's mouth falls through
   ground that is drawn. Static collision cannot be added or moved without rebuilding its MOPP codes (READ re/havok.md
   141, 225: 'not tested'); what remains is level bounds and kill boxes, which punish but do not stop, or re-placing a
   key-framed piece of the map as a rail (types 2..5 carry no code: READ re/havok.md 138; never tried). ASSUMED:
   dropped money and bodies at the rim are lost. This is the part of the map the owner sees last in every round.
7. **Nothing ever arrives.** Every enemy stands in the building from the load; when the 21 (or 40) guards are dead
   the rest of the round - the whole escape - is unopposed. The owner's notes on the four shipped maps ('the ai a bit
   too easy', 'the coppers dont seem too intimidating') were about exactly that. F07's police squads could be put on
   the pavement's mesh strip (ASSUMED: AI walks the mesh, not the collision), as on Retomoto's street (READ CLAUDE.md,
   re/retomoto_ai.md): that is the 'Heat' beat this place lacks, and it is not in the report's effort figure.
8. **An empty night club.** No crowd (1,980 members at most in the campaign, 80 of them on this very pavement), 17
   optional civilian actors, three lamp materials not drawn, a light show that hangs on a never-run controller. The
   report says so itself (risk 3); I rank it first among the reasons the owner might not like the map, above any crash.
9. The first 11 s put eight armed heisters and six stacks of money in 46 m2 behind two shut doors: with traitors on,
   the round may be decided in the office. A matter of taste, to be seen live.
