# Retomoto Tower, part B: the street ("like the movie Heat")

2026-10-09, agent k-street. **Offline only**: nothing was installed, the game was not started (the
owner was playing). Tool: `tools/kl_fa_street.py`. It sits on top of `tools/kl_fa_author.py` (part A
and the layer as a whole, re/retomoto_fa.md) and edits nothing of it. Builds on re/retomoto.md (the
survey), re/retomoto_fa.md 9 - 10 (what the live runs saw of the street), re/fa_gamemode.md 2 (how
stock paces waves), re/fa_round.md 7 (the bank's escape), re/retomoto_design_plan.md 2a (the sketch).

Words: **read** = read off the level files or kl2.exe (address given); **seen** = in a live run of
an earlier agent (run named); **GUESS** = a value of mine; **ASSUMPTION** = fits the evidence, not
proven; **LIVE** = only a run can settle it (section 8 orders them).

    python tools/kl_fa_street.py test <out> [--keep] [--no-ai] [options]   build + verify + read back (4 min)
    python tools/kl_fa_street.py report <archive>                          wave table, escape, bounds, sketch
    python tools/kl_fa_street.py plan                                      the tables on M09_B's mesh, no build
    python tools/kl_fa_street.py squads                                    F07's 14 police squads as stock has them

## 0. Result

`test G:\kl_scratch\k_street --keep` (2026-10-09; the last two builds PASS, the last with the tables
below; one before them FAILED on this tool's own check - the dog's point on a mesh island, 3.2):
F07 + M09_B + M09_A with kl_fa_author's layer and this one, **25,725 entities, 22 rooms, 313 MB**.
- `kl_graft.verify`: **1 problem, known** ("39 particle template names do not resolve (stock
  M09_A: 36)", re/maps.md patch 2). The stream-clip problem of earlier builds no longer shows.
- `kl_fa.check`: **0 CRASH, 0 BROKEN**, the one DEGRADED as before (no bot squads).
- this tool's own read-back of the written archive: **0 faults** - all 14 squads are in the level,
  each is started by a box, every actor / cover point / ring point stands on a polygon of the
  joined navigation mesh that can be walked to from the road, every list entry of the boxes names
  a node, the van's stop is inside the exit box and on the mesh. `RESULT: PASS`.
- A second build, `--no-ai --no-police` (an empty street, for the escape runs), is in
  `G:\kl_scratch\k_street_np` (section 8, run S1): 25,158 entities, 296 MB, the same known verify
  problem, this tool's read-back 0 faults; `kl_fa.check` has one BROKEN there, 'no ZSquadScript: no
  police' - the point of that build (kl_fa_author's own `--no-ai` builds, which ran live, have
  the same), and the only finding `test` accepts in that combination.

What it adds to the level kl_fa_author builds (no new entity, no new controller):

| | before | now |
|---|---|---|
| police on the street | the campaign's 10 squads (20 actors), all started at the front entrance | + F07's 14 squads (26 police, 1 dog) in three waves along 180 m of road; the campaign's 10 shared out over entrance / wave 1 / wave 2 |
| the van | three vans, random pick, stops 16 - 27 m apart; exit box from z 4300 (50 m before the stops) | one van (01), one stop (-1567, -40, 9300); exit box from z 6800 (25 m before the stop, stock's distance); the other two under the road |
| west side | a 'bound' that came out as a wall across the road (section 5) | one slab along the whole west kerb, x -7500..-6500, z -2500..14000 |
| early round end | not explained | explained (section 6); the level's part of it is the exit box and the single stop |

## 1. The street, measured

All from the files (`plan`, `report`; re/retomoto.md 3.4). x runs west (-) to east (+), z south to
north; the crew comes out of the door at (2600, -6490) and turns north.
- Carriageway x -5700..-300, kerbs to x -6000 / 0. Height of the navigation mesh on it y -48..-40,
  which is the player's feet as seen live (run RT4: -47..-40). Forecourt x -50..2650.
- The mesh that can be walked to from the road (flood over polygon edges and paired waypoints):
  road z -19000..13500; forecourt and lobby; **west: the overpass, joined to the road at
  z 7000..10500 on road level, and through it the bus terminal (y -980) and the hotel street**.
  Nothing else leaves the road between z -2000 and 7000 except a sidewalk nook x -7000..-6000 at
  z 1000..3000. The mesh has islands: a 1.5 x 1.3 m polygon at (-3000, 4500) among the block's
  cars has no neighbour (the tool only uses polygons that can be reached).
- 67 static vehicles stand on the map, about 45 of them on this stretch of road: a traffic jam,
  cover every 5 - 15 m (the sketch's `c`). Police: `RetoFront01 / 02` on the forecourt, the first
  road block (three cars at (-4090, 3602) (-3493, 3805) (-1901, 3911)), the SWAT truck
  (-3588, 10886), the far block (four cars z 13131..14404), the SWAT van south (-2208, -12506).
- Bounds the campaign brings (kept by `kl_maps.campaign_drop`; world extents with their
  rotation applied): north x -5869..739, z 13036..13798; south four boxes z -13218..-10898 across
  x -7186..889; behind the lobby x 7213..7717; three at the bus terminal x -26212..-24212. All
  4 m high (y -20..384). Whether a converted Dead Men `LevelBound` works at all: LIVE.

## 2. F07's police squads (`kl_fa_street.py squads`)

14 top-level groups, each `ZGROUP` + `ZSquadScript` (eStayBack / eAllTypes / field 3 = 0; the dog
eUnleashed / eFragileAllianceUCC) at a translation of its own (7119, 114, 9334) or (5311, .., 9335),
**rotation identity**. Children: actor groups (`Police_SWAT_01__*` / `Police#0n` / `Dog`, each with
a `ZFFActor` 'Ground' + `ZSoldier` eArmy, half of them eSR_FragileAllianceOnly, half
eSR_FragileAllianceUCC), routs with their points, a `RandomTrigger` or the dog's `TriggerBox`.
They reference **nothing of F07's map**: 26 weapon templates in the systems side
(`AllLevels/equipment.zip\Weapon\Rifle_AK74` ...) and each other.

| squad (prefix `Gameplay!`) | actors | first routs (points) | started in stock by |
|---|---:|---|---|
| `020_Loot!020_FinancialAlley_LeftParking` | 2 | `RandomTrigger` -> `10_RunToCover` / `20_RunToCover` (2 + 2) -> `30_smUnleash` | `tbExitLoot` -> `020_Loot!Timer` (TriggerDelay) |
| `020_Loot!020_FinancialAlley_LeftFurther` | 2 | `RandomTrigger` -> 10 / 20 (2 + 2) | the same timer |
| `020_Loot!020_FinancialAlley_RightGround` | 1 | `RandomTrigger` -> 10 / 20 (1 + 1) -> `30_smUnleash` | the same timer |
| `020_Loot!020_FinancialAlley_RunForDumpster` | 2 | `RandomTrigger` -> 10 / 20 (2 + 2) | `tbExitLoot` |
| `020_Loot!020_FinancialAlley_RightPlatform` | 3 | `RandomTrigger` -> 10 / 20 (3 + 3) | `tbExitLoot` |
| `020_Loot!021_FinancialAlley_Dog` | 1 dog | `DefendBehaviour` (1) | its own child box `tbReleaseDog` |
| `030_AfterLoot!030_FinancialAlleyExit_Left` | 3 | `10_RunToCover` (3), `10_Defend` (1), `30_smUnleash` | `tbExitFinancialAlley` |
| `030_AfterLoot!030_FinancialAlleyExitStreet_Left` | 2 | `10_RunToCover` (2), `10_Defend` (1) | `tbExitFinancialAlley` |
| `030_AfterLoot!030_FinancialAlleyExitStreet_Right` | 2 | `10_RunToCover` (2), `10_Defend` (1) | `tbExitFinancialAlley` |
| `030_AfterLoot!030_FinancialAlleyExit_Right` | 3 | `10_RunToCover` (3), `10_Defend` (1) | `tbExitFinancialAlley` |
| `030_AfterLoot!030_FinancialAlleyExitSkywalk` | 2 | `10_RunToCover` (2), `10_Defend` (1) | `tbExitFinancialAlley` |
| `030_AfterLoot!030_FinancialAlleyExitSkywalkNoCover` | 1 | `10_Defend` (1) -> `30_smUnleash` | `tbExitFinancialAlley` |
| `040_Escape!040_EscapeEntranceLeft` | 1 | `10_RunToCover` (1), `30_smUnleash` | `tbEscapeAI` |
| `040_Escape!040_EscapeEntranceRight` | 2 | `10_RunToCover` (2), `30_smUnleash` | `tbEscapeAI` |

All but the dog also have `40_RunToEscape` (`DefendBehaviourRout`, one `Pos#01` near F07's van
stops), named by `Gameplay!RunToEscape!Timer`: `tbRunToEscape1Player` (MERCONLY) -> `Timer1Player`
44 s -> `RunToEscapeGate\Way#02` -> `Timer` 18 s -> the 13 routs; with three criminals
`tbRunToEscape` (MERCONLY, EFAMPS_FA_UCC, counts) -> `tcRunToEscape` (3) -> `Timer3Player` 32 s ->
`Way#01` -> the same timer. In stock the two boxes lie 25 - 27 m before the van stops, so the
police converge on the vans about a minute after the criminals get there.
F07's three squad boxes (`tbExitLoot`, `tbExitFinancialAlley`, `tbEscapeAI`) and the dog's are
**ECPS_BOTH** in stock, not MERCONLY: a criminal or a returned policeman starts the squads.
Stock actors stand 3 - 58 m from their cover points, round the corners of the alleys, some on
platforms (y 100..500 over a road at y -200).

## 3. The waves

### 3.1 How a squad is moved

"Rigid group" as far as the data allows: the squad's layout is mapped by ONE turn about Y and ONE
shift in the ground plane, so that the centre of its cover points lands on the table's anchor and
the direction 'actors -> cover' points at the criminals (south). Then
- every point is put on **M09_B's own navigation mesh** at the mesh's height (y -47..-40); a point
  that falls off the mesh (a car, the kerb, F07's lateral spread) is pulled towards the anchor
  until it stands on it - at most 5.0 m in the table below;
- the actors' start group is pulled in to 15 m behind the cover points (`MAX_BACK`, GUESS; 9 of
  the 14 squads). `--rigid` keeps F07's distance: wave 2's actors then start in the van's stop;
- x is kept 3 m inside the carriageway.
The group gets the anchor as its translation and keeps the identity rotation. No stock level has
a `ZFFActor` under a rotated parent (0 of 43 in F07, 0 of 49 in F01); all 43 of F07's are under a
translated one - so a moved group with re-laid children is stock form, a turned group would not be.
ASSUMPTION that a squad's points only have to stand on the mesh: F07's `RunToPosInfo` points do
not name cover objects (field 5 names the actor group that runs there), and what the AI does at
such a point without one of the level's `CoverBox` objects nearby was not read. LIVE.

### 3.2 The table (as read back from the built level; `report`)

| step | box (stock F07 object) | world box | who | starts |
|---|---|---|---|---|
| entrance | `030_AfterLoot!tbExitFinancialAlley` (kl_fa_author's) | x 2592..3207, z -7302..-5697 | MERCONLY | campaign: `010_RetoBldFront` `Squad_Teargasguys` (2), `Squad_InFront` (3) on the forecourt; and the three squads SOUTH of the south bound, `Squad_RoadBlock_South` (3), `..._South#02` (2), `Squad_SWAT_From_Behind_South` (3), who come up the road behind the crew. 13 actors |
| wave 1 | `020_Loot!tbExitLoot` | x -1100..-500, z -11900..-1100: the first metres of carriageway along the whole forecourt | BOTH | stock's own list (two `RandomTrigger` + the timer of the other three): **5 F07 squads, 10 police**, mid road, cover points z -3270..-210, 30 - 65 m north of the door line, in the traffic; + campaign `Squad_SWAT_From_Behind` (3), who stand there |
| wave 2 | `020_Loot!021_FinancialAlley_Dog\tbReleaseDog` | across the road, z -3600..-3000 | BOTH | the six `030_AfterLoot` squads (what stock's `tbExitFinancialAlley` named) + the dog: **13 police + dog at the first road block**, cover points z 2750..4870, 60 - 80 m ahead; + campaign `Squad_RoadBlock_R2`, `_L`, `Squad_SniperResponse`, `Squad_Launcher_Dude_North` (4) |
| wave 3 | `040_Escape!tbEscapeAI` | across the road, z 1700..2300 | BOTH | stock's list: the two `040_Escape` squads, **3 police at the SWAT truck**, z 10450..11190, north of the van's stop |
| run | `RunToEscape!tbRunToEscape1Player` (+ `tbRunToEscape`, UCC) | across the road, z 6200..6800 | MERCONLY | stock's chain, timers untouched: 62 s (50 s for three criminals) later all 13 squads go to a ring round the van's stop |
| exit | `EscapeSetup!otrExitLevel` | x -5700..-300, z 6800..11300 | - | calls the van (section 4) |

Per squad (anchor = where its cover points are centred; all GUESSES beside measured objects):

| wave | squad | anchor (x, z) | beside | actors start | ring place |
|---:|---|---|---|---|---|
| 1 | LeftParking | (-4100, -2700) | Civilian_E (-4078, -3574), Taxi_Green_06 (-4165, -2192) | (-4060, -1919) (-4138, -1898) | (-2397, 7600) |
| 1 | LeftFurther | (-1800, -2500) | Taxi_Red_01 (-1775, -2206), Taxi_Green_02 (-1790, -3009) | (-1777, -1319) (-1813, -1885) | (-1767, 7500) |
| 1 | RightGround | (-2900, -1900) | Civilian_B_00#16 (-2154, -1500) | (-2900, -1430) | (-2854, 7500) |
| 1 | RunForDumpster | (-4135, -1298) | Civilian_A_00#14 (-4124, -1021), Taxi_Red_07 (-4165, -1593) | (-4166, 94) (-4106, 82) | (-3897, 8300) |
| 1 | RightPlatform | (-1800, -1250) | Civilian_A_00#06 (-1792, -1598) | (-1708, 188) (-1761, 313) (-1931, 249) | (-3297, 9300) |
| 2 | Exit_Left | (-4090, 4050) | behind block car #04 (-4090, 3602) | (-4057, 5540) (-4124, 5558) (-4089, 5551) | (-4351, 9395) |
| 2 | ExitStreet_Left | (-3493, 4200) | behind block car #03 (-3493, 3805) | (-3468, 5545) (-3521, 5705) | (-3897, 8900) |
| 2 | ExitStreet_Right | (-2700, 4150) | the gap between cars #03 and #01 | (-2722, 5647) (-2678, 5653) | (-3297, 10300) |
| 2 | Exit_Right | (-1901, 4300) | behind block car #01 (-1901, 3911) | (-1896, 5799) (-1889, 5886) (-1918, 5714) | (-1097, 10300) |
| 2 | ExitSkywalk | (-3350, 2819) | in front of the block: Taxi_Red_03, Taxi_Green_01 | (-3397, 3658) (-3302, 3674) | (-2697, 10500) |
| 2 | ExitSkywalkNoCover | (-2300, 3300) | in front of the block, open road | (-2300, 4421) | (-2097, 10300) |
| 2 | Dog | (-2825, 4601) | behind the block | (-2825, 6102) | - |
| 3 | EscapeEntranceLeft | (-3588, 10450) | in front of the SWAT truck (-3588, 10886) | (-3588, 11950) | (-4097, 10499) |
| 3 | EscapeEntranceRight | (-2613, 11000) | Taxi_Red_04 (-2613, 11468) | (-2613, 12500) x 2 (stock has the two on one spot) | (-3497, 10299) |

Two anchors moved to the nearest reachable polygon ((-4100, -1250) and (-3340, 2900) stand in
cars; the dog's (-3000, 4500) is the island of section 1).

### 3.3 Pacing (the Heat picture, as designed; every distance from the table)

1. Door. 5 police on the forecourt behind the two police cars; 8 more start 60 - 75 m to the SOUTH
   and come up the road behind the crew for the rest of the round.
2. First step on the carriageway: 13 police rise in the traffic 30 - 65 m to the north, both lanes.
3. Six metres before that line: 17 police and a dog man the road block 60 - 80 m further up - a
   long sight line down the street, fire from behind three police cars while the first line is
   still being fought.
4. 16 m before the block: three more take the SWAT truck at the far end, beyond the van's stop.
5. Past the block (z 6200): the clock of stock's 'run to the escape' starts; 62 s later every
   policeman of F07's left alive walks to a ring round the van. 6 m on, the exit box calls the van.
46 police and a dog over 180 m (13 + 13 + 17 + 3), 33 of them in front of the crew, 8 behind.
What is NOT designed and for the eye: whether 13 + 17 at once is too much for eight players or
one; the squads' modes (eStayBack: they hold until `30_smUnleash`, as in stock).

### 3.4 MERCONLY boxes and RESPAWNONLY twins

Asked for: MERCONLY boxes with RESPAWNONLY twins (F01's `tbPlatform#0n_MercOnly` /
`tbStreet_RespawnOnly`). Built: the three wave boxes keep **ECPS_BOTH, the value these very boxes
have in stock F07** - one box that fires for a criminal or a returned policeman, i.e. the pair in
one object. Reason: F07 has five free trigger boxes for the street (kl_fa_author uses
`tbExitFinancialAlley`, `tb_LEFT / RIGHT_TheySpotYou`, `tbCountPlayers`' counter); three waves +
the stock pair of 'run' boxes use all five, so a separate twin has no object. Difference from a
real pair: a twin can stand somewhere else (F01's stands where the police come back). Here two
of the seven police points are on the square, (447, -7956) and (-367, -7594); the wave 1 box
(x -1100..-500) is 1.3 m west of the second, so a policeman who comes back there starts wave 1
with his first steps onto the road - the police side gets its AI company, which is what the twin
is for. `--merc-only` writes ECPS_FA_MERCONLY instead (one variable, run S7).
Not established: whether a box counts the player bodies that stand at the police points from
the load on (`Heroes!Henchmen_0n`, one at (-367, -50, -7434)); the wave 1 box keeps clear of them.

### 3.5 The street from above (`report` on the built level)

A label stands on the row that holds the south face of its box (a bound: its centre line, or its north
end for the west slab).

```
SKETCH  one cell = 300 (x) x 500 (z);  . walkable from the road   c static car   P static police car / SWAT vehicle
        1 2 3 actors of F07's squads by wave   + their cover points   o their places round the van   e a b c the campa
        (e entrance, a b c with wave 1 2 3)   w the van waits   V the van stops
      x -7500     -4500     -1500     1500
  14500
  14000           P  P  P                     <- bound 030_LevelBound_StreetLeft, x -7500..-6500, z -2500..14000
  13500
  13000         ......  P .....               <- bound LevelBound_North, x -5869..739
  12500         ......  3......
  12000         ......  .......
  11500         .....3  .......
  11000         .....  +c......
  10500 ............ P  o......
  10000 ...........o.oo...o..o....
   9500 ..........................
   9000 ..........o...o....V......
   8500 ............o.............
   8000 ............o......... ...
   7500 ...............o.o.o.. ...
   7000     ......................
   6500       ..w........c........            <- exit box (calls the van), to z 11300
   6000      ..........2...c .....            <- run box, x -5700..-300; <- run 3 box, x -5700..-300
   5500      ...c..2.2.22c2 ......
   5000      ... .c..... ......
   4500      .......+..++......
   4000       .....++.++.2++...
   3500      ....+bP 2  +.P.b..
   3000  .......  ...+  .+.....
   2500  .......b...cb  .........
   2000  ........ ...c  .... ..
   1500  ... .... ....  .... ..               <- wave 3 box, x -5700..-300
   1000  .......... c..........
    500        .. .c...........
      0        .. .1......11 ..
   -500        .. .c....+......
  -1000        ...++.....++. ..
  -1500        ....c...1. .1...
  -2000       .....1..+..c1c++..
  -2500       .....aa...+..c.....
  -3000       ...+..+.....+....+.
  -3500      ......+.......c.....
  -4000       .....c.............             <- wave 2 box, x -5700..-300
  -4500     .............c... ............
  -5000     ..............c..c...........
  -5500     .................c........ ..
  -6000     . ....c......................
  -6500       ..........c........Pe   ....
  -7000      .....................e   ....
  -7500     ..... c..........c..eP.......     <- entrance box, x 2592..3207
  -8000     . . .c........... .e..e.. ...
  -8500     . ....c......................
  -9000     ...............c..............
  -9500      ............c. .....
 -10000       ............c......
 -10500       ...................
 -11000       ...................             <- bound LevelBound_South, x 389..889, z -11898..-10898
 -11500     . ...................
 -12000     ...........        .              <- wave 1 box, x -1100..-500; <- bound LevelBound_South, x -3008..607; <
 -12500      ............. .P ..
 -13000          .......ee......              <- bound LevelBound_South, x -7186..-2758
```

## 4. The escape

### 4.1 Why the script did not board (runs N0, N0b, J2, J3; re/retomoto_fa.md 10.2)

Read from the built level `<work>\build\i_rt` and from N0b's log and pictures:
1. **The 'red van at stop 3' is van 01 at its WAITING place** (-4866, -40, 6688), 12 m from stop 3
   (-4164, 7700). The three vans stand on the road from the load on (in F07 they wait in side
   streets); that is why RT4 saw it on a direct boot, where no van is ever called.
2. **The boarding box is not at a stop: it rides on the van.** `BoardingTrigger`
   (`PlayerAction` 'EnterVehicle', eONLY_LYNCH, field 12 = 1, UA_FA_ESCAPE: stock form) is a child
   of `V_Van_00`, local (-2, 119, -337), half extents 95 x 135 x 80: a patch of 1.9 x 1.6 m,
   **3.4 m behind the van's origin, at its rear doors** (the van's nose is local +Z: its `KillBox`
   is 1.6 m in front of the origin, `Door_Hatchback` 2.3 m behind). The stop is `PathBlockerVan`
   (the origin dwells within 4 units of it: keys 152..173 / 145..153 / 176..181 of the three baked
   drives step less than 3 units). So at a stop the box lies on the side the van CAME FROM:

   | van | waits at | stop | heading at the stop | boarding box centre |
   |---|---|---|---|---|
   | 01 | (-4866, 6688) | (-1567, 9300) | (0.60, 0.80) | **(-1769, 79, 9030)** |
   | 02 | (-3227, 3432) | (-1562, 8500) | (0.05, 1.00) | (-1580, 79, 8163) |
   | 03 | (-1594, 1101) | (-4164, 7700) | (0.23, 0.97) | (-4240, 79, 7371) |

   The script stood on the stops themselves - (-1616, 9214) and (-4095, 7735) - 2.4 m and 3.9 m
   from the boxes of the vans that stop there.
3. **Which van comes is a random pick of three** (kl2 0x6c3f90), and the box exists at a stop only
   while that van stands there: 8 s. In N0b the first van was called at 15:54:23.7 (the walker
   crossed z 4300); its red countdown read 00:05 at 15:54:42.4, so it ended at :47.4 = the call +
   23.7 s, which is van 01's whole cycle (drive in 7.2 + wait 8 + drive out 8.48): the countdown
   runs until the van is gone, and the 8 s at the stop were over at :38.9. The walker reached stop
   1 at :39.9 and stop 3 at :49.5. The next van arrived at about 15:55:07.8 (yellow 00:02 in the
   picture of :05.8), and it cannot have been van 03: the walker stood 0.8 m from that van's stop
   and lived (each van carries a `KillBox` at its nose). ASSUMPTION that the first was van 01 (its
   cycle fits to 0.1 s; van 03's 23.12 s fits the clock's 60 s to 0.1 s as well).
   At no moment was the player inside the boarding box of a standing van. E never had a target.
4. `BoardingCar` (`OnlineGamePlayTrigger` eOGPT_PLAYER_BOARDS) is not a place: the boarding action
   names it in field 1. Its box is at the origin / below the map in stock F07 too.

### 4.2 What is built

- **One van, one stop**: the exit trigger lists van 01 only (fields 3, 4 = ''; the pick loop takes
  the one). Its stop (-1567, -40, 9300) is the northernmost (158 m from the door), nothing static
  stands within 14 m of it (stop 2's boarding box is 25 cm beside `V_JPN_Civilian_B_00#18`), and
  kl_fa_author's 'Escape area' marker is on it already. ASSUMPTION that a single listed van comes
  again after it left (Dead Men's did, run ESC2; here N0b saw a second arrival 20 s after the
  first van left, of three listed). LIVE, run S2. `--three-vans` gives stock's pick back.
- The two other vans' groups are moved 600 m down (`--vans-stay` leaves them as scenery at
  (-3227, 3432) - inside the road block's line - and (-1594, 1101)). GUESS that this is harmless.
- **Exit box** x -5700..-300, y -400..1400, z **6800**..11300: its south face is 25 m before the
  stop. Stock F07: 23.9 - 26.0 m before its three stops. (kl_fa_author's began 50 m before.)
  Van 01 waits 1 m south of that face in the west lane: the crew crosses the line beside it and
  it pulls out with them, 7.2 s to the stop.
- **Where to board**: from the south-west, at the rear doors: **(-1769, 9030)**, 3.4 m from the
  stop; the mesh is under it (y -40). The van stands turned 37 degrees towards the east kerb.
- Money: nothing to do for 'carried to the van' - the bag is the player's; ESC3 on the bank paid
  loot + escape with these systems. `wire()` runs `kl_fa.money_people` whatever the level holds
  (kl_fa.repair does it only when there is a `ZHavokCar`): the van's body parts are tracked
  objects, and a money trigger that takes anything as activator crashed the bank at kl2 0x6a8902
  (run ESC1). This build: 0 such triggers were left, so nothing changed.
- 'All surviving criminals escaped' is the game rules' own end (seen: ESC3); needs the boarding.
- The ring: 13 `40_RunToEscape` points round the stop (GUESS, offsets in `RING`): three squads cut
  the road south of the van at z 7500..7600, the rest stand west and north of it.

## 5. Bounds and kill planes

- **A fault in the layer as it ran live.** F07's `030_LevelBound_StreetLeft` boxes are turned by
  90 degrees about Y in stock (`ZGEOM[1]` = 1 0 0, 0 1 0, 0 0 -1), and half extents are local.
  kl_fa_author's entry (centre (-7400, 500, 3000), half 400 / 1500 / 5000, no turn) therefore came
  out as **x -12400..-2400, z 2600..3400: a level bound across the road at the first road
  block**, 30 m high, and the west side stayed open. Every scripted walk went through it at
  x -2167 without being turned back (N0b: z 2302 -> 3172 in 1.5 s); J2 lost two minutes exactly
  there (ten way points 'NOT reached', z 2400..3100). Whether that was the bound: not established.
  Other turned stock boxes that kl_fa_author places without a turn: `Specials!LevelSpeak!TriggerBox`
  (90 degrees: its 170 x 130 x 120 is 120 x 130 x 170 in the world - harmless, it only speaks),
  `040_LevelBound_AlleyTop` (180 degrees: no effect). `tbExitFinancialAlley` is turned by 0.6
  degrees. This tool sets identity on every box it places.
- **West**: one slab `030_LevelBound_StreetLeft!Bound` x -7500..-6500, z -2500..14000,
  y -1000..2000; warning boxes from x -6200. It closes the overpass mouth (z 7000..10500, right
  beside the exit box), with it the bus terminal and the hotel street, and the nook at
  z 1000..3000. GUESS: 5 m west of the kerb; the squads stay east of x -5400.
- North, south, behind the lobby: the campaign's own (section 1). LIVE whether they act.
- **Kill planes: none placed, none needed on the street.** The road is flat; the only drop is
  the bus terminal (y -980), behind the west slab. F07's one map `KillBox` (FA_DieFromSelf,
  under its streets) is part of its map subtree and cannot be kept as a single object; the three
  the vans carry at their noses stay. The window drop of the tower is part A's.

## 6. The round that ends early: 60 seconds after the first van has gone

**Seen** (N0b; file times of the pictures against the log):

| picture | wall clock | HUD clock | van icon |
|---|---|---|---|
| N0b_191s | 15:54:42.4 | **03:59** | red 00:05, the same over a van in the world |
| N0b_203s | 15:54:52.9 | **00:54** | - |
| N0b_215s | 15:55:05.8 | 00:41 | yellow 00:02 |
| N0b_248s | 15:55:39.8 | 00:07 (red) | - |

The clock ran normally (06:00 at GO, 10 s after the round state began) until the first van's red
countdown ended at 15:54:47, and stood at **60 s** from then: the three later pictures all put
its zero at 15:55:46.8, the round state ended at 15:55:47.4. The van had been called at
15:54:23.7, when the walker crossed z 4300, the south face of the exit box: 23.1 s before.

| run | exit box entered (s after the round state began) | round ended | difference |
|---|---:|---:|---:|
| N0b | 111.8 | 195.6 | 83.8 |
| J3 | 186.0 | 269.5 | 83.5 |
| J2 | about 227 | 312.1 | about 85 |
| N0 | 143.4 | 196.3 | 52.9 (not explained; its pictures were not read) |

83.5 .. 85 = one van cycle + 60: the cycles are 23.68 / 21.32 / 23.12 s for vans 01 / 02 / 03.
So it is not the round clock running out early and not kl_fa_author's van timer: **the round
gets 60 s once the first escape vehicle has left**, and the vehicle was called 50 m before the
stops by a player who then needed 16 s to the first stop. The bank showed the same (ESC1: 'the
round clock drops to about a minute').

**Read in kl2.exe** (what the times are made of):
- `ZOnlineExitLevelTrigger` (0x6c3d50): random pick 0x6c3f90, then the rules' slot 44 with the
  player and the vehicle - `ZGameRulesHeist` 0x6cd8e0 -> 0x8154f0 (Arcade runs the Heist rules:
  ESC1's dump), `ZGameRulesFragileAllianceSv` 0x4d85e0 -> 0x71e180.
- 0x8154f0: for an `OnlineEscAnimatedVehicle` the cycle is `[veh+0x6c] + [veh+0x70] + [veh+0x74]`
  -> `[rules+0xe7c]`; if the time left is not more than cycle + 2.0 (0xb62258) the vehicle is
  flagged the last one (`[rules+0xe8a]`, message 0x43ef40). Slot 194 (0x8fa6d0, escape state
  0..7 at `[rules+0x1dc]`) takes the state's timer `[rules+0x1d8]` from veh+0x6c (states 1, 2:
  coming), +0x70 (3, 4: waiting), +0x74 (5: leaving), or from `[0x168d7c0]+0x628 / 0x62c / 0x630`
  for a vehicle that is not animated. ASSUMPTION that +0x6c / +0x70 / +0x74 are fields 14 / 15 /
  16: three floats in a row, and 14 and 16 equal the lengths of the 'Activate_Enter' and
  'Activate_Exit' animations at 25 frames a second in all 15 stock vans ((230 - 50) / 25 = 7.2,
  (485 - 273) / 25 = 8.48 for F07's van 01); field 15 is 8.0 in all 15: **the van waits 8 s**.
- The settings' floats 324 / 325 / 326 (F07: 11, 8, 20) go to `[0x168e9e4]+0x44 / +0x48 / +0x4c`
  (0x88ee81..0x88eebb). 325 is added to the clock when the FA rules reset a round (0x40f8b5), 326
  by the Heist rules (0x51bd34): start-of-round values. None is the 60 s. 0x6d3130 is the time
  getter; it returns 360.0 (0xb2e7fc) outside a round.
- **Not found**: the instruction that writes the 60 s. No 60.0 is loaded in 0x8fa6d0, 0x5e8570 or
  0x74b6d0. It is the game's rule, not a level value: no field of the settings, the exit
  trigger, the monitor or the vans holds 60 in any of the nine stock levels.

**What the level can do about it, and does**: call the van late (exit box 25 m before the stop,
as stock), make the stop known (one van) and board on the right side. A crew that crosses z 6800
together has 7.2 + 8 s to cover 25 m. Whoever misses the first van has 60 s and - ASSUMPTION -
further visits of the same van (N0b: the next came 20 s after the first had left).
Not a fix: fields 15 of the van (the wait) could be raised (GUESS; every stock van has 8.0) -
left as it is; it is one number in `OnlineEscAnimatedVehicle` if the owner finds 8 s too short.

## 7. For kl_fa_author / the lead

Three lines put this layer in natively (until then `kl_fa_street.hook()` patches the same three
places from outside; `kl_fa_street.py test` does that, `kl_fa_author.py test` builds WITHOUT it):

    KEEP = (...) + kl_fa_street.KEEP                    # kl_fa_author.KEEP (import kl_fa_street lazily: it imports kl_fa_author)
    kl_fa_street.prepare_host(S, log)                   # last line of kl_fa_author.prepare_host
    kl_fa_street.wire(sc, log)                          # last line of kl_fa_author.wire

- `prepare_host` raises if kl_fa_author's `ROLE` / `PLACE` / `PARKED` name one of this layer's
  objects (`KEEP` + the dog's box). It re-places four things kl_fa_author also places, after it:
  `ROLE['exit']` (box and van list), `POI_TheEscapeArea` (same place), the three
  `030_LevelBound_StreetLeft` boxes, and the two unlisted vans' groups. The van transforms
  themselves (`place_vans`, `VAN_STOP_Z`) are read, not changed: `van_pose()` takes the stop from
  the placed `PathBlockerVan` and the turn from the group's rotation.
- `wire` reads the entrance box's list as kl_fa_author wrote it and moves five campaign squads to
  wave boxes by name (`CAMPAIGN_WAVE`); a squad it does not know stays at the entrance.
- F07 trigger boxes left after both layers: two, neither usable as it is.
  `Gameplay!020_Loot!FollowPlayers!tbCountPlayers` is NOT kept on purpose: it feeds the counter
  kl_fa_author uses for the main room. `000_Civilians!001_Civilian_01\tbCivRunToGate` is a child
  of a civilian squad.
- kl_fa_author's StreetLeft entry and the turned boxes: section 5 (give `place()` a `turn=(0, 1)`
  wherever a half extent is set).
- kl_graft.py, kl_snd.py and kl_fa_author.py were being edited by others while this was built;
  two builds failed on half-written files (`load_options`, a quote in kl_snd.py line 588) and
  passed on the next try. The PASS above is on the tree as it stood at the last build.

## 8. Live test order (nothing of this was run; one variable per run)

Builds: `python tools/kl_fa_street.py test <scratch> --keep [options]`, install with
`python tools/kl_graft.py install F01 --from "<scratch>\R09+M09_A (R09 = F07+M09_B)"` (the join
needs the hook and `KLJoin.ini` as in re/retomoto_fa.md 10.1). Route up to the road: N0b's script
(`<work>\build\klhook\live\N0b.ini`, steps to `pos road0`). Shots every 3 s from the entrance on.

| run | build | the one variable | do | expect | if not |
|---|---|---|---|---|---|
| S1 | `--no-ai --no-police` (`G:\kl_scratch\k_street_np`) | the escape as built | N0b's walk to (-2700, 6600); note the clock; `goto -2400 6900` (in the exit box); `goto -1769 9030 60`; hold E 3 s, tap E, for 12 s | no red van at (-3227, 3432) or (-1594, 1101); yellow icon about 7 s, van 01 drives from (-4866, 6688) to (-1567, 9300); red 8 s; 'You jumped into the getaway car'; 'All surviving criminals escaped' | no prompt: stand 1 m further from the van on its axis, (-1830, 8950); then each side of the van (four runs). No van: read the exit trigger's list in the build (`report`) |
| S2 | as S1 | not boarding | stand at (-2400, 7200) from the call on, shots every 2 s for 120 s | van leaves after 8 s; clock 60 s when it is gone; van 01 comes AGAIN (when?); 'last van' message? round ends 60 s after the first departure | van never returns: one van is one chance - go back to `--three-vans` |
| S3 | `--no-ai --no-police --three-vans` | three vans listed | as S2 | which vans come, in which order, where they stand (boarding boxes of 4.1) | - |
| S4 | `--no-ai --no-police --vans-stay` | the two unlisted vans left standing | walk past (-3227, 3432) and (-1594, 1101) | two red vans as scenery, nothing else differs from S1 | a fault that S1 did not have: parking is what was harmless, keep it |
| S5 | `--no-ai --no-waves` | F07's squads present, nothing starts them | walk the road to the van | 26 police and a dog stand at their start places (table 3.2); do they ignore the walker (ASSUMPTION: field 3 = 0 squads do nothing)? Dog Days police models, on the road, not in cars | they shoot: the squads are active without a rout - then waves only decide where they go |
| S6 | `--no-ai` | the waves | walk (the script dies; a person plays, or read positions with `[Auto] PosLogMs`) | wave 1 at the first step onto the road, wave 2 at z -3600, wave 3 at z 1700; squads run to their cover points; 62 s after z 6200 they walk to the ring | a squad stands still: its points are on the mesh but not at cover - read what a `RunToPosInfo` needs (3.1) |
| S7 | full build | + the campaign's squads, shared out | play | 13 at the door incl. the 8 from the south, 3 more with wave 1, 4 with wave 2 | - |
| S8 | full build `--merc-only` | field 14 of the wave boxes | two players; one dies and comes back on the square | BOTH: his first steps onto the road start wave 1. MERCONLY: only a criminal does | - |
| S9 | any | bounds | walk west at z 3000 and z 9000 to x -6200 and -6500; north to z 13000; south to z -11400 | warning at -6200, turned back at -6500; the campaign's bounds likewise | no reaction west: `LevelBound` needs something this layer did not read. No reaction north / south: the converted Dead Men bounds do not act - use F07's parked ones (`kl_fa_author.PARKED`) |
| S10 | `--rigid` | actors at F07's distance | S6 again | wave 2's police start at z 7400..8400, in the van's area | - |

## 9. Not established

- Everything of section 8. In particular that F07's squads fight on a road without their alleys'
  cover objects, and that a single listed van returns.
- The code that sets the clock to 60 s (section 6), and N0's 52.9 s.
- Whether a trigger box counts the idle player bodies at the police points (3.4).
- Whether Dead Men's converted `LevelBound` boxes act (section 1).
- What `ZSoldier` 'eSR_FragileAllianceOnly' / 'eSR_FragileAllianceUCC' do in Arcade: half of F07's
  police carry each; if Arcade spawns only one kind the waves are half as large.
- The vans' baked drives pass through static cars and the far road block (re/retomoto_fa.md 4):
  untouched here.

## 10. After the owner's first round on the street (2026-10-09): invisible police

"Some of the police outside are invisible": 12 of the street's 47 actors - the campaign's own
`JPN_Police` model, never one of F07's moved squads - lose their body beyond close range, because
their far-detail material `Characters/_JPN/JPN_Police_LOD3` asks for a Cloth / Skin shader
permutation Dog Days never compiled. Cause, every other reason tested and cleared, the fix
(`kl_light.plain_twin` inside `fit_shaders`), and the repaired copy of the played build
(`<work>\build\s_visible`, not installed): `re/invisible.md`.
`kl_fa_street.py report` now ends with PEOPLE OF THE STREET (`kl_chars.people`) and counts a
person who would not be drawn as a fault: 12 on the played build, 0 on the repaired one.
