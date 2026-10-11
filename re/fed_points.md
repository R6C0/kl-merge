# Where a dead player comes back as a fed

Track L, 2026-10-11. Owner, after his Retomoto round of 12:28-12:33 (`fed: YOU ARE A FED ... at (1804, 19601, 812)` -
the tower, while the round was in the street): 'okay yeah spawn as a fed but in a lift'; an hour later, after the park:
'fed spawns definitely need a fix on all maps im guessing'.
OFFLINE: read in `kl2.exe` build 0490 (`debug\dasm.py`) and measured on the five builds of his tab. **Nothing here has
run in the game.** The tool: `tools\kl_fa_fedpoints.py` (its docstring = the commands).

SECOND FORM, after the adversarial review (`re\fed_points_review.md`: ACCEPT WITH FIXES) - section 9 says what was
done about each of its points. In short: the step is now ALSO applied to track K's street-lanes build
(`z_fedpts\retomoto_lanes` - the one meant for the tab; the lanes took two of the four street places, which moved),
one of the tower's three points stands on the lift floor 23 m from the join box, the stale audit is gone, the diff
compares what it says, and `klhook\klfed.c` prints the place a second time half a second later (a log line, nothing
written). **No build of this track goes on the owner's tab before live checks P0, P1, P2 of section 6.**

Status words: **READ** = disassembled, address given. **MEASURED** = computed from the build's files (collision `.HVK`,
navigation mesh, `.prp`, `.gms`). **ASSUMED** = fits what was read, not seen. **GUESS** = a value of mine.

## 0. Short answers

- **The game picks the place at random, with equal chance, among the level's AFTER_DEATH spawn points that are not
  hidden** (`0x5614f0`, called by rules slot 199 = `0x518e30` from the respawn `0x4b28d0`). Nothing else counts: not
  where he died, not where the crew or the police are, no line of sight, no 'used' mark.
- So the place is level data, and so is switching a point off and on: the pick skips a point whose node is HIDDEN, and
  the stock controllers `DeactivateGeom` / `ActivateGeom` hide and show whatever their lists name. No hook part is
  needed for it, and none was written (the hook's one change is a second log line of the place: section 5).
- **Retomoto: all seven of its points were bad.** Five stood inside two lift cars of the tower whose doors nothing
  opens (three in the lift opposite the escape car - that is where he came back -, two in the atrium's glass lift);
  the two on the square in front of the lobby stand 69 under the collision floor. And nothing tied the points to the
  half the round is in: after the join five of seven draws went to the tower.
- **The answer, built**: `<work>\build\z_fedpts\retomoto_lanes` (on track K's lanes build, the one for the tab) and
  `z_fedpts\retomoto_full` (on the tab's present build). Three points in the tower (shown at the load): two on the
  top gallery, one in the south wing of the lift hall; four on the street's police side (hidden at the load); a
  switch node turns the tower's off and the street's on when the crew steps out of the lobby lift; the level's own
  once-a-round pair (the blast) puts them back. Only `.prp` and `.gms` differ from the source build.
- **A police player can take the join**: `kljoin.c` looks at the local player object, whatever it is. A man who dies
  in the tower comes back on the top gallery (129 m of stairs from the box before the tower car) or in the lift hall
  (23 m from it), walks into the box, and the jump takes him and every AI heister still in play to the lobby
  (`klcrew_rt.c`) - the round goes on in the street. No hook part was changed for it.
- **The other four maps**: Withdrawal and Late Night Opening are good as Dead Men made them (he walks out; the bank's
  'double door' is shut, three other doorways of that room each have a leaf modelled open). Hot Coffee's seven stand on the warehouse's upper office floor, the
  park's five in a pen on the freeway junction - both Dead Men's 'the police drop in from above', 2.7 .. 4.0 m and
  4.3 m down with no way back. Built for both: the points on the ground below (`z_fedpts\M01`, `z_fedpts\M06`).

## 1. How the place is picked (READ)

The respawn `0x4b28d0` (klfed.c 1; re\fed_respawn.md 2.3): `0x4b29bf push 0 / push 2 / push player / call [vtable +
0x31c]` = `ZGameRulesHeist` slot 199 = **`0x518e30`(police player, type, 0)**. The round start places the hero the
same way with type 1 (`ZSessionHandlerSP` slot 11, `0x466bad`).

`0x518e30`:

1. `0x5614f0(type, 0)`; if that says -1 it is called once more; -1 again: return, nothing is placed - the police
   body stays where the level put its `Heroes!Henchmen_0N` object.
2. the point = entry of the spawn manager's list; its world matrix (`0x857110` of the node `[point+4]`);
3. ONE ray: from 10 above the point's place (`0xb5cde8` = 10.0) straight down over 200 (`0xb5ba0c` = -200.0), collision
   mask 0x20 (the collision world's vtable +0x264). Hit: the player's height = the hit + 2.0 (`0xb62258`). No hit:
   the point's own height;
4. the heading from the matrix (`0x589440`, `0x429ff0`), then `0x82cc40(player, place, heading, 1, 0, 1)`.

`0x5614f0` (the pick; 'this' = the rules object, unused):

```
L = [[0x168e9f8] + 4]            the spawn manager's list: [L] pointers, [L+4] one byte an entry (0 = in use), [L+0xc] count
for every entry in use:
    point = [L][i]
    [point + 0x14] == type ?                      else skip        (0x56154f; type 2 = AFTER_DEATH)
    node = [point + 4];  bit 0x400 of [node + 0x3c] clear ?   else skip        (0x561557: hidden)
    -> candidate                                                   (0x7b3020 reads the node's place: the result is not used)
none: the same loop once more without that read; none again: -1
seed = [[0xdd2640] + 0xb30] * 0x10dcd + 1          the engine's generator, stored back
return candidate[ int( ((seed >> 8) & 0x7fff) / 32768 * number of candidates ) ]         (0xb59200 = 1 / 32768)
```

Two callers and no other: slot 199 and slot 210 (`0x462440`, a twin of `0x518e30`). The multiplayer rules use the
picker `0x4d0b80` (callers: `...Sv` slot 197 `0x491900`; slot 22 `0x6a52a0`, which `ZGameRulesHeist`'s vtable shares;
`ZGameRulesFragileAlliance` slot 26 `0x6aa950`): the same two tests (type equal, `0x4d0bdb`; hidden bit, `0x4d0be3`),
the draw made from its second argument - so what is built here holds online too, as far as the pick goes. A third
picker, `0x4de590`, takes the type as a MASK and measures the distance to every player: its one caller is the co-op
rules (`ZGameRulesCoopSv` slot 19); Fragile Alliance does not go through it.

**What a point is.** `ZSpawnPoint` (vtable `0xbd2954`; ZSTDOBJ -> ZGEOM). Its constructor `0x8c06f0` sets
`[point+0x14] = -1`, `[point+0x18] = 0` and enters the point in the spawn manager (`0x5aa250`). Stored fields
(`tools\kl_rtp.py`): the eight of ZGEOM / ZSTDOBJ (bounding kind, matrix `ZGEOM[1]`, place `ZGEOM[2]`, hidden
`ZGEOM[3]`, ...), then 8 = `ESPAWN_TYPE` (-> `+0x14`; START 1, AFTER_DEATH 2, TRAITOR 4, TEAM 8..14, UCC 16..20, ANY -1)
and 9 = a string (-> `+0x18`; stock uses it for the team mode's stage letters 'A'..'D', empty on every AFTER_DEATH
point). The class has no message handler of its own (its vtable differs from ZSTDOBJ's in slots 0, 11..14, 82 only)
and no controller. `ZOnlineSpawnpointTrigger` (stock: 2..5 a level) only moves the TEAM mode's stage (`0x4b6470` ->
`0x64bf30(type - 8)`); it does nothing to the AFTER_DEATH pick.

**What decides, then.**

| | level data | live object |
|---|---|---|
| candidate at all | `ZSpawnPoint` field 8 = `eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH` | `[point+0x14] == 2` |
| on / off | hidden at the load: `ZGEOM[3] = 1` with `.gms` record flag 0x400 (the stock pair: 994 nodes of F07 have both, none has one without the other but the children of a hidden parent) | bit 0x400 of `[[point+4]+0x3c]` |
| where | `ZGEOM[2]` (and the `.gms` record's place) | the node's world matrix |
| which way he looks | `ZGEOM[1]`: the point looks along its local +Z | the same matrix |
| which of several | nothing | the engine's random number |

**Switching a point by level data (READ).** Hidden = node flag bit 0x400. ZGEOM's Hide and Show are vtable slots 21 /
22 (`0x46fe10` -> `0x6edd50`, `0x63f370` -> `0x8703e0`): `0x440290(node, set 0x400, clear 0)` and `(node, 0, 0x400)` -
a child of a hidden parent is not shown. The controllers:

- `ZDeactivateGeom` slot 26 (`0x824950`): on its message (field 0) **or on 'AITrigger'** (its init `0x538e40` always
  registers that word) it sends every object of its list (field 1) to the session manager's slot 9 (`0x668160`):
  already hidden -> nothing; else the object's slot 20 with 0, **Hide**, and a message to the object's own controllers.
- `ZActivateGeom` slot 26 (`0x55c9f0`; init `0x41a560`): the same with slot 8 (`0x4c4900`): not hidden -> nothing; else
  **Show**, `0x73b720` (returns at once for a node without a model, `0x73b762`), slot 20 with 1, a message.
- Both SAVE and RESTORE the shown state of every object they name: slot 21 (`0x899c50`) writes one bit an object,
  slot 22 (`0x6e8c70` / `0x8d6750`) reads it back and calls slot 8 or 9 where the object differs. Both register with
  the game data for that (slot 16 `0x7afa80`).

Stock (MEASURED, 9 FA + 11 campaign levels): 1,014 `ActivateGeom` and 583 `DeactivateGeom`, on `ZBoxPrimitive`
helper boxes and groups; 26 nodes carry BOTH on one message (L10's office windows on 'Activate', L03's minibus on
'BreakWindowsNow'); they switch groups, boxes, meshes, sounds, lights, emitters. **None names a spawn point, and no
stock spawn point is hidden** - the form is stock, its use on a `ZSpawnPoint` is new. ASSUMED: it behaves as on any
other node without a model (the routines above are the class-blind ones of ZGEOM).

## 2. The points of the five maps (MEASURED; `kl_fa_fedpoints.py report <build>`)

How a point is judged - the tool's docstring has the rules. In short: **floor** = a collision floor inside the game's
ray; **walk** = `kl_escape.Walk`'s rules made a body wide and with every floor of a cell kept apart, from the point to
THE CREW'S GROUND (what a man can walk to and back from the START row, from any place a step of the AI heisters
names, from the boarding action); **mesh** = the navigation polygon under it; **bounds** = LevelBound / warning /
kill boxes, the escape vehicle's road. The walk test sees the level as it loads, knows no door that opens, and leaves
convex shapes (crates, cars) out: 'good' means the collision leaves a body-wide way, nothing more.

### 2.1 Retomoto Tower - `z_rooms\retomoto_full` (the tab's build): 7 of 7 BAD

Placed by `kl_fa_author`'s POLICE table on F07's seven objects (`FASpecials!SpawnPoint!SpawnPoint_Dead_0N`).

| point | place | verdict | why |
|---|---|---|---|
| Dead_05 | (1800, 19601, 812) | **bad** | closed in: 8 m2 of floor, bounded by `SI0101_JPN_Elevator_Main_A_00` and its door leaves `DrInt_A_00` / `DrInt_B_00`; no mesh polygon. **This is where the owner came back** (1804, 19601, 812) |
| Dead_06 | (1904, 19601, 818) | **bad** | the same lift car |
| Dead_07 | (1987, 19601, 973) | **bad** | the same lift car |
| Dead_04 | (-1764, 19613, -61) | **bad** | closed in: 15 m2, bounded by `SI0103_M09_ElevatorCar_00` / `ElevatorDoor_01`; mesh part 53 (one polygon, joined to nothing) |
| Dead_03 | (-1508, 19613, -147) | **bad** | the same lift car |
| Dead_02 | (447, -50, -7956) | **bad** | no floor in the game's ray: the square's collision (`SO0102_JPN_Tiles_A_01`) is at y 20, 69 ABOVE the point; he is set down inside the slab |
| Dead_01 | (-367, -50, -7594) | **bad** | the same (`SO0100_JPN_Street_Wide_Parking_a_01`, y 20) |

- **Which lift.** The elevator lobby (`M09_A_Ins_Elevators_101`) has six shafts. The escape car is `Int_A_03` /
  `Ext_A_03` at (2973, 19600, 909): the only one a controller names (`AnimProxy_OpenEscapeElevator`, frames 0..75),
  and the join box lies before it. Points 05 / 06 / 07 stand in **`Int_A_04` / `Ext_A_04` at (1953, 19600, 890)**,
  the car opposite, on the lobby's west side. Its door groups have a `RelayMessageList` ('Activate' -> the two
  leaves); **nothing in the level names them**: in the campaign `SquadArrivingElevator` rode up in this car, and the
  Fragile Alliance layer does not keep that squad. The doors never open. `kl_fa_author`'s comment says where the
  places came from: 'the elevator lobby (campaign SquadArrivingElevator, which is not kept), the atrium lift'.
- Points 03 / 04: the atrium's glass lift `SI0103_M09_ElevatorCarGroup_02` (an `Elevator` controller with empty
  lists and a `MatPosAnim` on 'Activate', named by nothing).
- The street's navigation mesh lies 40..70 UNDER its collision (mesh -48, tiles +20 on the square; mesh -40, road 0
  at the van): a place taken from the mesh's height - as these two were - is under the ground for the game's ray.
  The AI heisters' places have the mesh's height too and work, so an actor is put on the collision by other means.
- And the halves: all seven were shown, nothing switched them. Before the join 2 of 7 draws went to the street,
  after it 5 of 7 to the tower.

`kl_fa_fedpoints.py check` on it: `RESULT (kl_fa_fedpoints): FAIL (13 FAIL, 6 NOTE); 7 point(s): 0 good, 0 doubtful,
7 bad; START half 5, jump half 2`.

### 2.2 Hot Coffee (M01) - `z_route3\M01`: 7 of 7 BAD

Dead Men's own Fragile Alliance data (`SpawnPoint!SpawnPoint_Dead_01..07`), x 2105..2790, y 950..953, z 16923..17129.

All seven stand on the UPPER OFFICE FLOOR at the south end of the warehouse (floor y 860, about 110 m2), on mesh
part 1 (16 polygons) that no polygon or link joins to the crew's part - **bad** by the rule 'a mesh part not joined
to the crew's' (an AI heister cannot path to him). The only way to the crew's ground is **a drop, one way: 2.7 m or
4.0 m** - the walk test finds a body-wide ledge 274 down with its grid on the world's own lattice and only one 399
down with the grid moved by 10 (three alignments of four tried): the answer hangs on a few centimetres, the kind
does not. What bounds the floor: `SI0103_M01_WareHouse_MainWallB_FA`, `SI0103_M01_Window_A_Whole_01`,
`SI0103_M01_Bridge_02`, `Si0105_M01_Staircase_FA_version_01`, `PlanksPacked_A`. Dead Men's police dropped in from
there; its players could also climb (re\escape.md), Dog Days' cannot. Whether a Dog Days player takes such a drop
unhurt is NOT known (stock gives its AI drop links of up to 5.2 m).

### 2.3 Late Night Opening (M02) - `z_loot3\M02`: 7 of 7 GOOD

Dead Men's own data, x 4228..4717, y 90, z -2617..-2042: a back room on the ground floor (floor y 0). On the crew's
ground: from it 503 of the crew's 504 places are reached by walking. No mesh polygon under any of them (the mesh
ends 20 m away): said, not judged - he walks out, the AI heisters cannot path in. The verdict holds with the walk
grid moved by (10, 10).

### 2.4 Withdrawal (M03, the bank) - `z_cover3\M03`: 7 of 7 GOOD

Dead Men's own data, x -4791..-4317, y 391..397, z -3593..-3369: the parkade's stairway room
(`M03_FAA_Parkade_StairwayRoom_01a`, floor y 300), on the crew's mesh part, 16..21 m from the nearest place of a
heister. **He can leave it.** From point 1 the walk test gives 382 of the crew's 383 places by walking, the nearest
47 m away; the way (`kl_fa_fedpoints.py way <build> 1`, 11 way points): (-4390, -3490) -> (-4550, -3310) ->
(-4550, -3070) -> (-4090, -3130) -> (-3650, -3010) -> (-3630, -2950) -> down to y 200 at (-3550, -1970) -> the
yard. The doors of the room are `SI0200_M03_DoorSteelWin_A_NN`: static collision (flags 0x17a), nothing in the
level moves them. MEASURED by the review, leaf by leaf in world space: the pair `_A_05` / `_A_06` (x -4911..-4883,
z -3620..-3380) is SHUT - that is the double door of the lead's picture, and the first form of this note was wrong
to call it open -; the other three doorways each have one leaf turned open, gaps of 110 (z -3102..-2992 at
x -4500), 109 (z -3208..-3099 at x -4100) and 211 (at x -3700), and the way above goes through those. A gap of 110
passes the walk test's body of 60; whether it passes Dog Days' player is live check P8. GUESS why the scripted player 'never moved far': it walked straight lines into the room's walls; the way
points above are for track H3's script. Holds with the grid moved by (10, 10).

### 2.5 A Walk in the Park (M06) - `z_route\M06`: 5 of 5 DOUBTFUL

Dead Men's own data (`SpawnPoints!Respawn!SpawnPoint_Respawn_01..05`), x -1158..-1001, y 1630..1656,
z -10246..-9474: **a pen of 141 m2 on the freeway junction** `_FreeW_Junction_E_01` (floor y 1539..1561), 13 m above
the park, bounded by the junction's rails, by Dead Men's own invisible `ColiObj_Police_spawn_BLOCK_01` and by the
barriers `PC0300_M06_RoadBlock_A_01..10`. No mesh under it. The only way to the crew's ground is **a drop of 428
(4.3 m), one way** (426 with the grid moved). The owner's two returns there (12:43, 12:44): the first round ended 6 s later, in the second he
was 'dead for good' after 82 s; his place is not in the log (the line read (0, 0, 0): it comes a tick early).

### 2.6 The five in one line each

| map | build | points | verdict |
|---|---|---|---|
| Retomoto Tower | `z_rooms\retomoto_full` | 7 | **7 bad**: 5 in two shut lift cars of the tower, 2 under the square's floor; no tie to the half the round is in |
| Hot Coffee | `z_route3\M01` | 7 | **7 bad**: upper office floor, own mesh part, a one-way drop of 2.7 .. 4.0 m |
| Late Night Opening | `z_loot3\M02` | 7 | 7 good (off the mesh) |
| Withdrawal | `z_cover3\M03` | 7 | 7 good; the stairway room has a way out |
| A Walk in the Park | `z_route\M06` | 5 | **5 doubtful**: a pen on the freeway junction, 4.3 m one-way drop |

## 3. Retomoto's two halves: the design, as built

`<work>\build\z_fedpts\retomoto_lanes` = `kl_fa_fedpoints.py apply <work>\build\z_lanes\retomoto_full <out>` (track K's
second form, archive `85c884eb...`); `z_fedpts\retomoto_full` = the same on `z_rooms\retomoto_full` (the tab's);
`z_fedpts\retomoto_lanes_r` = on `z_lanes\retomoto_full_r` (lanes + random routes in the tower).
Top views (collision, mesh, the heisters' places, the points): `<work>\build\z_fedpts\maps\`
(`retomoto_tower_lift_floor.png`, `retomoto_lanes_street_north.png` are the second form's).

**The tower (START half): three points, shown at the load** (the table: `retomoto_lanes` and `retomoto_full`, the same three; on `retomoto_lanes_r` the random routes move the heisters' places and the top two come out at (-790, 21050, 1770) and (-2270, 21050, 890), the low one the same). Two on the START
row's floor (the top one, y 21000), on the cells of the crew's ground FARTHEST from every place a step of the AI
heisters names, not within 30 m of the START row (the boardroom and its blast), a body's room round each, 0.5 m
from a mesh edge, 2 m from where an enemy stands. The third (`--low 1`, the default since the review's S3) by the
same rule on THE JOIN BOX'S FLOOR (y 19600), 3 m or more outside the box:

| point | place | from the nearest place of a heister | on foot to the join box | |
|---|---|---|---|---|
| Dead_06 | (-1550, 21050, 1570) | 22.7 m | 129 m | the top gallery's north-west arc, outside the north-west stair well |
| Dead_05 | (-670, 21050, 1770) | 18.1 m | not measured (9 m along the same gallery) | the north gallery |
| Dead_07 | (2650, 19650, -1390) | 14.6 m (the crew's hold before the tower car, in the hall's north end) | **23 m** | the SOUTH WING OF THE LIFT HALL (`M09_A_Ins_Elevators_101`), among the hall's own guards (`070_Elevators` squads: three stand 2.4 .. 3.3 m from it), 3.4 m from the shut door of lift `Ext_A_01` - outside it, on the crew's ground |

Why one low: the round goes on only when the human - police now - has walked into the join box (the AI heisters
never take the join without him), and from the top floor that is 129 m of stairs; a man who dies late, with the
crew at the lifts, was a long way from his own round (review S3). One draw in three now puts him in the same hall.
The cost: a man who dies in the first minute may come back three floors below a crew that is still in the
boardroom - with the join box 23 m away, which takes them all to the street if he walks into it. `--low 0` gives
the first form (all three on the top gallery, Dead_07 at (-2270, 21050, 890)); the owner's call.

The heisters take the south arc and the south-west stairs; the top two are on the other side of the atrium, by the
places the atrium's own squads charge from. 'Behind the crew' in the sense that the round's way leads down and away
from here; a man who dies in the first minute comes back AHEAD of a crew that is still in the boardroom, with the
reception between them. On foot from Dead_06 (`way <build> 1`): 87 m to the nearest place of a heister (the foot of
the stairs on the atrium floor), 129 m to the join box, by the east side of the gallery and the south-west stairs -
the north-west flight beside him is not a way in the walk test (a place on the atrium floor right under him is
about 115 m away by the other stairs).

**The street (jump half): four points, HIDDEN at the load**, at authored places (`PLACES` in the tool: six, taken in
order; the police side, north of where the crew comes from), each on the nearest cell that passes every test and is
15 m (`STREET_FAR`) from every place a step of the AI heisters names; a place with no such cell within 4 m is left
out for the next of the list.

On the tab's build (`z_fedpts\retomoto_full`: one street chain, east side) the first four are taken:

| point | place | from the nearest place of a heister | |
|---|---|---|---|
| Dead_04 | (-4250, 50, 5950) | 33 m | behind the road block, west lane - wave 2 starts 4 m south of it |
| Dead_03 | (-4550, 70, 10950) | 31 m | behind the SWAT truck (wave 3 stands in front of it); 2.2 m short of the north bound's first warning box |
| Dead_02 | (-3350, 50, 6350) | 24 m | behind the road block, at the median |
| Dead_01 | (-4810, 50, 10250) | 33 m | the west kerb beside the SWAT truck |

On the lanes build (`z_fedpts\retomoto_lanes`; `_r` has the same four) the heisters take BOTH sides: lane W runs
through the first place and 6 m past the third, so both road-block places are left out and the two of the west
pavement come in. (The first form of this step, tried on the lanes build, put one man 6 m from a hold of the crew
and one - 'no authored place left: the farthest cell of the half' - in a corner 180 m from the van: that is what
`STREET_FAR`, the two new places and the fall-back's `VAN_NEAR` are for.)

| point | place | from the nearest place of a heister | |
|---|---|---|---|
| Dead_04 | (-4550, 70, 10950) | 31 m | behind the SWAT truck |
| Dead_03 | (-4810, 50, 10250) | 33 m | the west kerb beside the SWAT truck |
| Dead_02 | (-5510, 70, 9190) | 32 m | the west pavement north of the exit line, across both carriageways from the van (37 m from the boarding action) |
| Dead_01 | (-5310, 70, 8290) | 25 m | the west pavement level with the place the van waits at (34 m from the boarding action); on the south edge of a box the top view draws there - by its place the level's exit box, a criminal's; `check` finds the point in no bound, warning or kill box |

So on the lanes build all four are in the north-west quarter, by the SWAT truck and the west pavement - the one
part of the street no lane enters; 370 of the street's 371 crew places are reached from each by walking.

All on the collision floor (the points float 50 above it: the game's ray finds it), on the jump entry's mesh part,
99 of the street's 100 crew places (370 of 371 on the lanes build) reached by walking, clear of the bound / warning boxes and 3 m off the van's
road. The van stops at (-1851, 10462); the truck and the median stand between it and the two by the SWAT truck.
'Beyond the SWAT truck' as the task put it has no room: the truck stands at (-3588, 10886) and the north bound's
first warning box begins at z 11174. The point 'behind the SWAT truck' is beside it on the far side from the van instead.

**The switch.** F07's helper box `Gameplay!010_FirstFight!RivalMercVan!GeomDeactivator_DriveInVan` (a
`DeactivateGeom` nobody names, its list empty - the node `kl_fa_author` keeps as ROLE 'police off' for exactly this,
behind its unused option POLICE_FOLLOW) now carries

    DeactivateGeom { 'AITrigger', [Dead_06, Dead_05, Dead_07], 0 }      the tower's three: OFF
    ActivateGeom   { 'AITrigger', [Dead_04, Dead_03, Dead_02, Dead_01], 0 }   the street's four: ON

and is one more entry in the list of **`Mercenaries!TriggerBox_1_LeaveElevator`** ((5902, 709, -6488), half
(100, 150, 1400), `ECPS_FA_MERCONLY`) - the campaign box across the lobby just outside the lift, which already
starts the street's police ('Squad_InFront\Regroup', the street's timer). All seven `[CrewJoin]` places of
`KLJoin.ini` lie inside it; the human walks through it two steps out of the car.

Why the box and not the JumpPoint's own list (which `0x72e0f0` sends 'AITrigger' at the jump itself):
`kl_fa_bots_rt.check` FAILs a build whose jump list holds anything but the seven squads' first street steps
('names something that is no DefendBehaviourRout step'), and that file is not this track's. `--at jump` builds that
form. The cost of the box: between the jump and the first step out of the lift (about 2.7 m) the tower's points are
still the shown ones - a man would have to die in the car.

**The way back for the next round.** The three tower points are also in the list of
`AI_Players!Enemies!020_Office!GeomActivator_ChairPost`, the four street points in
`...GeomDeactivator_ChairsPre`: the pair the blast timer (`Gameplay!010_FirstFight!RivalMercVan!Timer`, 16.5 s
after the round-start event, on the AIMonitor's round-start list) names every round to swap the boardroom's chairs.
In the first round both are no-ops (shown stays shown, hidden stays hidden: `0x4c4912`, `0x668172`). In a later
round on the same loaded level they put the points right whether or not the game restored them. (ASSUMED that it
does anyway: both controllers save and load what they name, section 1; whether an Arcade round start runs that
load was not read.)

**What a police player can and cannot do about the join** (READ in `kljoin.c`, `klcrew_rt.c`; decided, nothing
changed):

- He CAN take it. `klj_tick` reads the feet of local player 0 / 1 = `[gamedata + 0x828 + 4 * [gamedata + 0x898]]`,
  and the respawn has written the police object's index there (`0x537700`). A fed who walks into the box before the
  tower car is jumped like anybody; the game's `0x8f3fa0` moves the local player whatever he is.
- The crew comes along: in the tick the request is pending `klcrew_rt.c` moves every AI heister still in play to the
  arrival places, and the jump point's list starts their street route. That is the round going on: without it the
  crew stands at the tower car for good (re\bots_retomoto.md N2) and the round runs to its clock.
- He does NOT fire the points' switch: the box is for criminals. He needs no second return (a fed's second death is
  final, `0x4549f0`). Whether the seven AI heisters the hook puts into the box fire it - and with it the street's
  police - is not read (the review read the box itself: started at the load, it fires when ONE criminal is inside,
  and a message from the tower's `TriggerBox_OpenExitElevator`, which names it, can only start it, never fire it:
  kl2 `0x6e8b80`, `0x42afd0`, `0x42b20f`): if they do not, a fed who brings the crew down finds the street's waves asleep until a wave
  box of kind `ECPS_BOTH` is crossed.
- He cannot board or call the van (`0x68414e`); the crew does.
- A man who dies AFTER the join: the tower's points are off, he comes back at one of the four street points.
- Should a police player be kept from the join? No: it would leave a round nobody can end but the clock.

NOT done in the hook, on purpose: a switch by klfed.c (write the hidden bit, or the type, when the jump is seen).
It would be exact where the box is two steps late, and it would work on a build without this step - but it is a data
write into a node the engine keeps books on (`0x440290` does more than set the bit), it needs a new hook on the
owner's game, and the level data does the same with the game's own calls.

## 4. The other maps (built where a point is bad or doubtful)

`apply` on a map of one place moves every bad or doubtful point to the cell of the crew's ground NEAREST to where it
was in the plan - Dead Men's own choice of side is kept - that is on the crew's mesh part, has a body's room, is
clear of the bounds and the vehicle's road, 6 m from every place a step of the AI heisters names and 15 m from the
START row. Only the points' place and facing change.

- **Hot Coffee** `z_fedpts\M01` (from `z_route3\M01`): the seven go from the office floor to the warehouse's ground
  floor under it, x 1810..2970, y 110 (floor 60), z 17410..17810, 3.9 .. 8.7 m from where they were in the plan,
  8.4 m lower; 22 m or more from the nearest place of a heister.
- **A Walk in the Park** `z_fedpts\M06` (from `z_route\M06`): the five go from the junction to the park's ground
  under it, (-990, 290, -10230), (-910, 332, -9990), (-1750, 365, -9950), (-1150, 244, -9230), (-910, 326, -9150);
  0.2 .. 6.0 m in the plan, 12.8 .. 14.0 m lower; 15 m or more from the nearest place of a heister. They are inside
  the helicopter's call box (`Triggers!Call_ExitChpooer_Trigger`), as the junction is above it: Dead Men's police
  came down at the escape.
- Withdrawal and Late Night Opening: nothing to build.

Whether the two Dead Men drops (2.7 .. 4.0 m, 4.3 m) work in Dog Days is the one thing only a run can say; if a
scripted fed walks off both unhurt, the tab's builds can stay and these two are spare.

## 5. Builds and checks (second form, 2026-10-11 15:40-16:25)

All under `<work>\build\z_fedpts\`; the logs of every check in `checks\`, one line each in `checks\checks.txt`, the
step's self-checks in `checks\verify.txt`. The first form (the builds and logs the review read) is kept in
`z_fedpts\round1\`.

| build | from (its archive) | archive (bytes, sha1) |
|---|---|---|
| **`z_fedpts\retomoto_lanes`** | `z_lanes\retomoto_full` = track K's second form, `85c884eb4bb51607d81ce605cb20427a58a54c2d` | 218,953,973, `8a4042e0c9cb9b1cff4df266b57007192c8097c5` |
| `z_fedpts\retomoto_lanes_r` | `z_lanes\retomoto_full_r` (lanes + random routes in the tower), `3220509616a881ac5d030b69cee9a97079c9d0e7` | 218,957,526, `ce92895c2bb2a5b67b89420354e4cd80e20e6227` |
| `z_fedpts\retomoto_full` | `z_rooms\retomoto_full` (the tab's), `0bf668aa174b50eb01ce752ea9a1c9907ca84a6b` | 218,935,939, `9f7790598f3505a05b97460704bb97fe762e22b9` (the first form's was `518223a2...`: Dead_07 moved) |
| `z_fedpts\M01` | `z_route3\M01` (the tab's), `58491ae96cf4097c89823463f15bf90b080d74cc` | 205,906,147, `e28a4ab8d3b9bedc2594ce4710dfdb07aaa390a2` (the first form's archive, byte for byte) |
| `z_fedpts\M06` | `z_route\M06` (the tab's), `1d799830eeeed61335a4f59858e57eb1be678899` | 181,723,249, `710efed713a1bb549ee241cc5a9c43cce098123b` (the first form's archive, byte for byte) |

Every output's `fedpoints.txt` names its source's archive sha1 in its first line: **if track K builds `z_lanes`
again, `retomoto_lanes` is stale - run `apply` and `check` again** (the tower's three do not hang on the street;
the street's four are found anew from the list).

The last line of every check. The bots' checks and the others were run with the COMMITTED tools (a snapshot of
HEAD `370bc51`, `G:\kl_scratch\l\tools_head`: other tracks have `kl_fa_bots_rt.py` / `kl_fa_bots_dyn.py` open) -
except on the two lanes builds, whose lanes only the working tree's `kl_fa_bots_rt.py` / `kl_fa_bots_dyn.py` know:

```
z_fedpts\retomoto_lanes                                                              (bots checks: the working tree's tools)
  kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 8 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad; START half 3, jump half 4
  kl_fa_fedpoints diff     RESULT (kl_fa_fedpoints diff): only what the step means to change differs
  kl_fa_bots_rt check      RESULT (kl_fa_bots_rt): PASS (0 FAIL, 12 NOTE); start delay 91.5 s after a blast at 16.5 s; 7 gate(s) on the tower's way out; 3 lane(s) on the street; jump list 7; [CrewJoin] places 7
  kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 6 NOTE)
  kl_impact                problems: 0 in 1 levels
  kl_map_guns check        6 guns with looks ...; problems: 0
  kl_fa_street report      PEOPLE OF THE STREET: 47 actors below y 5000 (27 of the host's squads, 20 of the campaign's), 0 with a drawing fault
  kl_fa_author ledge       ledge test: ok
  kl_fa_talk check         findings: FAIL 1, NOTE 0      (the source's own: 'the countdown's NOW! starts at [7.51], the blast is at 16.50')
  KLTalk.ini               6c78c079fdf893257cc3d61774e06f07028d8a31 = the approved one
z_fedpts\retomoto_lanes_r                                                            (bots checks: the working tree's tools)
  kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 8 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad; START half 3, jump half 4
  kl_fa_fedpoints diff     RESULT (kl_fa_fedpoints diff): only what the step means to change differs
  kl_fa_bots_rt check      RESULT (kl_fa_bots_rt): PASS (0 FAIL, 12 NOTE); ... 3 lane(s) on the street; jump list 7; [CrewJoin] places 7
  kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 6 NOTE)
  kl_impact                problems: 0 in 1 levels
  (kl_map_guns, kl_fa_street, kl_fa_author ledge, kl_fa_talk: not run on this one)
z_fedpts\retomoto_full
  kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 8 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad; START half 3, jump half 4
  kl_fa_fedpoints diff     RESULT (kl_fa_fedpoints diff): only what the step means to change differs
  kl_fa_bots_rt check      RESULT (kl_fa_bots_rt): PASS (0 FAIL, 9 NOTE); start delay 91.5 s after a blast at 16.5 s; 7 gate(s) on the tower's way out; jump list 7; [CrewJoin] places 7
  kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 8 NOTE)
  kl_impact                problems: 0 in 1 levels
  kl_map_guns check        6 guns with looks ...; problems: 0
  kl_fa_street report      PEOPLE OF THE STREET: 47 actors below y 5000 (27 of the host's squads, 20 of the campaign's), 0 with a drawing fault
  kl_fa_author ledge       ledge test: ok
  kl_fa_talk check         findings: FAIL 1, NOTE 0      (z_rooms' own)
z_fedpts\M01
  kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 7 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad
  kl_fa_fedpoints diff     RESULT (kl_fa_fedpoints diff): only what the step means to change differs
  kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 2 NOTE)      (the tab's build fails the same seven: the civilian-money rule, on purpose)
  kl_impact                problems: 0 in 1 levels
  kl_map_guns check        problems: 0
z_fedpts\M06
  kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 5 NOTE); 5 point(s): 5 good, 0 doubtful, 0 bad
  kl_fa_fedpoints diff     RESULT (kl_fa_fedpoints diff): only what the step means to change differs
  kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 3 NOTE)
  kl_impact                problems: 0 in 1 levels
  kl_map_guns check        problems: 0
  kl_maps audit            RESULT: PASS (0 findings that must be 0, 6 known and accepted)      content id 9928e5a202b3e8b7f4c0022f9c79f152e3475cce
```

CONTROLS: every bots check was run with the same tool on the SOURCE build too, read only; each output's log is
its source's line for line, folder name aside (`checks.txt`: 'control ...: 0 line(s) differ', all five builds).
`kl_fa_street report` has one line more than the source's (the switch in the elevator box's list), on both
Retomoto builds it was run on; `kl_fa_talk check` is the source's log.
(In `checks.txt` the first `kl_fa_street` / `kl_fa_author ledge` lines read 'PermissionError': those two want the
archive's path, not the folder's; the lines under 'STREET / LEDGE again' are the runs.)

The tab's builds as they are (`kl_fa_fedpoints.py check`, read only; logs `checks\tab_*`), unchanged from the first
form:

```
z_rooms\retomoto_full   RESULT (kl_fa_fedpoints): FAIL (13 FAIL, 6 NOTE); 7 point(s): 0 good, 0 doubtful, 7 bad; START half 5, jump half 2
z_route3\M01            RESULT (kl_fa_fedpoints): FAIL (7 FAIL, 14 NOTE); 7 point(s): 0 good, 0 doubtful, 7 bad
z_route\M06             RESULT (kl_fa_fedpoints): PASS (0 FAIL, 15 NOTE); 5 point(s): 0 good, 5 doubtful, 0 bad
z_loot3\M02             RESULT (kl_fa_fedpoints): PASS (0 FAIL, 14 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad
z_cover3\M03            RESULT (kl_fa_fedpoints): PASS (0 FAIL, 7 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad
```

Self-checks of the step (`checks\verify.txt`):

- `z_fedpts\retomoto_full` was made three times (once as a trial, once as the build, once more with the tool as it
  is at the end): the same archive each time. M01 and M06 are the first form's archives byte for byte;
- **`--low 0` on `z_rooms\retomoto_full` gives the first form's archive `518223a2...`** - nothing but the new point
  changed in the tool's Retomoto answer for the tab's build;
- **applied to its own output it changes nothing** (`members changed: none`, the same archive), on
  `retomoto_full` and on `retomoto_lanes`;
- every verdict holds with the walk grid moved by (10, 10) (7 / 7 / 7 / 5 good: `retomoto_full`, `retomoto_lanes`,
  M01, M06);
- `--at jump` on the Retomoto output: this tool's check passes, and `kl_fa_bots_rt.py check` FAILs it as section 3
  says ('Specials!JumpPoints!06_Exit names 8 steps in 8 squads (wanted: one first street step in each of the 7)');
- **the diff sees what the review said it did not** (S2): with one entity's list links, list key or parent changed
  in memory it answers `UNEXPECTED: .gms record of ... differs: list links` / `list key` / `parent`.

Member by member (`kl_fa_fedpoints.py diff`): `.prp` and `.gms` differ, every other member has the source's CRC and
size (28 of 30 on Retomoto), the files beside the archive are the source's byte for byte, plus `fedpoints.json` /
`fedpoints.txt` (and `steps.json` continued where the build has one; `audit.*` not copied, see below). In the
`.prp`: the AFTER_DEATH points' `ZGEOM[1..3]` (7 nodes); on Retomoto also four nodes' controller values (the switch
with its new `ActivateGeom`, one more entry in the trigger box's list, the two lists of the once-a-round pair). In
the `.gms`: those points' records, and of them only place, matrix and flag 0x400 - the diff now also compares
name, type, model, aux, REF, raw block, group, parent, children, list key and list links of ALL records (26,650 on
the lanes build) and FAILs a changed `.buf` (it does not read one; `apply` refuses to write one that changed).
`.oct` / `.rmi` / `.rmc` / `.buf` / `.HVK` are untouched: no entity is added, removed or moves pool, so no SLOT id
changes. Not compared one by one: the `.gms` tables outside the records (clusters, list pool, matrix pool), which
`kl_scene` regenerates from the records.

`audit.json` / `audit.txt` (`kl_maps.audit`) name the content id of the build they were written for, so `apply` no
longer copies them (the first form's `z_fedpts\M06` carried `z_route\M06`'s); it says so and names the command.
`z_fedpts\M06` has its own now (`python tools\kl_maps.py audit <folder>`, the committed tool): PASS, content id
`9928e5a2...` - the review's own run gave the same. `z_route3\M01` has no audit, the Retomoto sources none.

THE HOOK (the review's S4): `klhook\klfed.c` + 14 lines, a log line only - 0.5 s after 'fed: YOU ARE A FED ...' it
prints `fed: YOU STAND at (x, y, z) NNN ms after you became police (object ...)`, the same three floats read again
(`[player + 0x460]`), nothing written, no game routine called, under `[Fed] Log` as the first line. Built from a
clean snapshot of HEAD `67003e1` + that one file (`G:\kl_scratch\l\src3`), one warning (`klhud.c(248)` C4101, the
tree's own): **TEST `G:\kl_scratch\l\test2\dinput8.dll` a28c60a9425803ba13cf4c1c11c3f088d736b913, SHIP
`G:\kl_scratch\l\ship2\dinput8.dll` f63d0339184d1088365900428dad5a97cd68a91d.** Compiled, NOT RUN. (An hour
earlier the same on HEAD `370bc51`: `...\test` f240c9a4..., `...\ship` 35049f3d....) It is the tree's hook at that
commit plus the line: the lead builds the hook he runs from the head of the branch once `klfed.c` is committed.
`klhook\KLHook.ini`'s `[Fed]` comment (which line to judge by) went into the tree with another track's commit of
that file (`5a50b42`).

## 6. For the lead: the live checks

**THE GATE (review M1, M2).**
- A build is one chain: the tab can hold the lanes OR a fed build of the tab's old Retomoto, not both side by side.
  The one for the tab is **`z_fedpts\retomoto_lanes`** (= K's `z_lanes\retomoto_full` + this step). If K's build
  changes, `apply` again (`fedpoints.txt` line 1 has the source's sha1 to compare).
- **Nothing of this track goes on the owner's tab before P0, P1 and P2 have run** on the build that is to go there.
  Four things have never happened in any level of either game: a `ZSpawnPoint` in a `DeactivateGeom` /
  `ActivateGeom` list, a spawn point hidden at the load, two geom controllers on this helper box, a third entry in
  the lobby box's list. The reading (section 1; the review's own, stronger: `ZSpawnPoint`, `ZSTDOBJ`, `ZGROUP` and
  `ZBoxPrimitive` share vtable slots 20-22, so hiding a spawn point runs the code stock levels run on helper boxes)
  makes a fault unlikely; a load fault would cost the owner his Retomoto. P0 doubles as K's first load if K0 has
  not run: then a fault there is K's or this step's - load `z_lanes\retomoto_full` alone to tell.

Hook: one that has klfed.c's second place line (section 5; any build of the branch's head after klfed.c is
committed), `[Fed] Enable=1 Player=1 Log=1`. **The line to judge by is `fed: YOU STAND at (x, y, z) ... ms after
you became police`**: the first line, `fed: YOU ARE A FED ... at (x, y, z)`, is printed in the tick the pointer
changes and read `(0, 0, 0)` in the owner's game at 12:43:29, 12:44:04, 15:06:59 and 15:14:34. With an older hook
take the test rig's next `pos tick: me` line, or the picture. The game sets him 2 above the floor, so y = the
table's floor + 2.

| | build / how | PASS | means when it fails |
|---|---|---|---|
| **P0** | `z_fedpts\retomoto_lanes`, a plain round | loads, GO, the round as its source build | the two controllers on one helper box / four hidden spawn points break the load: go back, tell |
| **P1** | the scripted player dies in the TOWER (before the join); three or more times (three places, one draw each) | `YOU STAND at` one of (-1550, 21002, 1570), (-670, 21002, 1770), (2650, 19602, -1390) (+- 30): the top gallery twice, the lift hall's south wing (on `retomoto_lanes_r` the gallery's two are (-790, 21002, 1770) and (-2270, 21002, 890)); never (1800..1990, 19601, 810..975) (the old lift car), never y about 2 / 22 (the street) | y 2 / 22: a point hidden by level data is still drawn - the pick's test is on another bit than the loader sets: the hook variant (section 3, last paragraph) is then the way |
| **P2** | walk him on (tower -> join), die in the STREET | one of (-4550, 22, 10950), (-4810, 2, 10250), (-5510, 22, 9190), (-5310, 22, 8290) on the lanes build; on `z_fedpts\retomoto_full`: (-4250, 2, 5950), (-4550, 22, 10950), (-3350, 2, 6350), (-4810, 2, 10250) | y 21002 / 19602: the box did not switch them - look for the street's police (the same box starts `Squad_InFront`): if they woke, `DeactivateGeom` did not hide a spawn point; if not, the box did not fire |
| **P3** | a second round in the same process after P2, die in the tower | a tower place again | the blast pair did not put them back: say so; the round after a join is then wrong until the level is loaded again. (If the game does not restore hidden states itself, the points are the wrong way round for the first 16.5 s after the round-start event of a later round - about 8 s after GO; a death that early is the case to look at) |
| **P4** | die in the tower, then walk the fed to the join box: `kl_fa_fedpoints.py way <build> 1` (20 way points, 129 m: `checks\way_retomoto_lanes_point1.txt`) or `way <build> 3` (5 way points, 23 m: `..._point3.txt`) | `join: player 0 entered box 9 ...`, `crewjoin: N moved`, the fed in the lobby; the heisters start their street route | no `join:` line: the box does not take a police player after all (it should: section 3) |
| **P5** | `z_fedpts\M06`, die | one of the five ground places of section 4 (y = the table's - 48) | |
| **P6** | `z_fedpts\M01`, die | y 62, x 1810..2970, z 17410..17810 | |
| **P7** | the tab's M01 and M06 as they are: walk the fed off the office floor / the junction (`checks\way_tab_M01_point1.txt`: 52 m, deepest drop 274; `way_tab_M06_point1.txt`: 50 m, deepest drop 428) | he lands and walks on | he dies or cannot step off: P5 / P6's builds are the answer |
| **P8** | the tab's M03: `checks\way_tab_M03_point1.txt` (11 way points, 47 m to the nearest place of a heister) | he leaves the stairway room | a doorway of 109 .. 115 is too narrow for Dog Days' player, or a door is shut after all: the walk test's body is 60 wide and it sees no door that opens or shuts |

What a fed finds on the lanes build's street (MEASURED, `checks\way_retomoto_lanes_point4..7.txt`): the four places
are 25 .. 33 m in a straight line from the nearest place of a heister and 34 .. 37 m from the boarding action, but
ON FOOT the median lies between - 107 m (behind the SWAT truck), 80 m (the west kerb), 73 m and 58 m (the west
pavement) to the boarding action, round by the road block's gap. He has the crew's run to the van in sight across
the carriageways; he does not stand in it.

## 7. ASSUMED and GUESS, in one place

- ASSUMED: `DeactivateGeom` / `ActivateGeom` hide and show a `ZSpawnPoint` as they do any node without a model
  (read: class-blind routines, and the review found the three slots to be the very functions of `ZSTDOBJ` /
  `ZGROUP` / `ZBoxPrimitive`; no stock level does it). P1 / P2.
- ASSUMED: a point stored hidden (`ZGEOM[3]` + `.gms` 0x400) has node bit 0x400 set after the load - the stock pair,
  and how `kl_fa_author` hides the main room's loot and a car in the van's way (those ran live).
- ASSUMED: the lobby's box fires for the human as it has (the street's police woke in his rounds). The review read
  the box: started at the load, fires at ONE criminal inside, and a message from the tower's box can only start it,
  not fire it. Whether the AI heisters the hook puts into it count was not read.
- ASSUMED: the level's hidden states are back at a new round; the blast pair makes it so 16.5 s after the
  round-start event in any case. P3.
- The walk test: no door that opens or shuts, no convex shape, a body = three cells of 20; the level as it loads
  (Retomoto's boardroom doors are shut in it, so the tower's points read '49 of 71 places by walking'). The review
  listed what the test leaves out round every point (nothing within 2 m; cars and the SWAT truck 3 m or more away).
- GUESS: 6 m from a heister's place (15 m for an authored street place), 15 m from the START row, 30 m from
  Retomoto's START row, 3 m outside the join box, the point 50 above its floor, a drop of up to 5.5 m as 'doubtful'
  and not 'bad', three points in the tower (one of them low) and four in the street, and the six street places
  themselves.
- NOT KNOWN: what a `LevelBound` box does to a police player (points are kept out of them and their warning boxes);
  whether the tower's guards and the street's police treat a police human as their own (the low tower point and
  all four street points stand among them: Dead_07 2.4 m from a guard of `070_Elevators`).

## 8. Not done

- Nothing was run in the game.
- The hook's second place line is compiled, not run; no other hook file was touched.
- The eight police BODIES (`Heroes!Henchmen_0N`) still stand where `kl_fa_author` put them, in the lifts and on the
  square: that place only matters when the pick finds no point, which no build here allows.
- `tools\kl_fa_fed.py` (the AI heisters' parked feds) places its men round the AFTER_DEATH points: a build of it made
  AFTER this step follows the new points; one made before keeps the old places (its check wants its men off the
  points, not near them).
- No audit on `z_fedpts\M01` (its source has none) or on the Retomoto builds (their sources have none; a Retomoto
  build has no `preflight.json` for `kl_maps.audit` to read).
- The team modes' and Undercover Cop's points of Retomoto (`TeamMode!SpawnPoint_TEAM_*`, `UCC!SpawnPoint_Dead_0N`)
  still stand in the lifts and under the square (the review measured it): Arcade does not draw from them.
- `kl_map_guns`, `kl_fa_street`, `kl_fa_author ledge`, `kl_fa_talk` on `retomoto_lanes_r`.

## 9. After the review (`re\fed_points_review.md`, ACCEPT WITH FIXES): each point, what was found, what was done

Every point was looked at again before anything was changed. None is refuted.

| | the review | checked again | done |
|---|---|---|---|
| **M1** | do not put `z_fedpts\retomoto_full` on the tab beside K's lanes build: apply the step to K's build | HOLDS. K's second form was there from 15:42 (`85c884eb...`). And it was more than a formality: the first form's street rule, run on it, put Dead_03 6.1 m from a hold of the crew's west lane and Dead_01 at (-6310, -8870), 'the farthest cell of the half', 180 m from the van | `z_fedpts\retomoto_lanes` (and `_r`), every check run. Tool: `STREET_FAR` 15 m for an authored street place, two more places (the west pavement), the fall-back bound to `VAN_NEAR` of the boarding action and said as a NOTE 'LOOK at it'. `fedpoints.txt` names the source's sha1 |
| **M2** | no fed build on the tab before P0, P1, P2 | HOLDS (nothing has run; nothing to refute offline) | written at the head of this note, of section 6, of the tool's docstring, and as the last line of every two-halves `fedpoints.txt`. Nothing was installed |
| **S1** | `z_fedpts\M06` carries the source's audit; the report's 'neither source has an audit' is wrong | HOLDS: `z_route\M06` has `audit.json` / `audit.txt`, the first form copied them (`round1\M06`) | `apply` no longer copies `audit.*` and says which command to run; `diff` FAILs an output that carries the source's audit byte for byte; `z_fedpts\M06` audited: PASS, content id `9928e5a2...`. The sentence is put right (section 8) |
| **S2** | `diff` does not compare `links` / `lkey` / the tree, and lets a changed `.buf` pass unread | HOLDS (read at the lines given) | `diff` compares name, type, model, aux, REF, raw, group, parent, children, list key and list links of every record and FAILs a changed `.buf`; `apply` refuses to write a changed `.buf`; three planted faults are caught (`verify.txt`). The docstring says what is compared and what is not |
| **S3** | all three tower points on the top floor: a man who dies late is 129 m of stairs from the crew; one lower point - 'the owner's call' | HOLDS, and weighs more than the review says: the round cannot go on until the police human has walked into the join box, wherever the crew is | `--low N` (default 1): Dead_07 in the lift hall's south wing, 23 m on foot from the join box, 14.6 m from the crew's nearest place. `--low 0` = the first form, proven byte for byte. THE OWNER HAS NOT BEEN ASKED: said in section 3 with the cost |
| **S4** | klfed.c's place line reads a tick early ('(0, 0, 0)' four times in the owner's log); a second line half a second later before P1 .. P6 | HOLDS: lines 119589, 119675, 124839, 125826 of his `KLHook.log`. The review calls klfed.c 'track M's file'; by the tracks' task files it is this track's (M and S are told not to edit it) | the `YOU STAND` line (section 5), `KLHook.ini`'s `[Fed]` comment says which line to judge by; section 6 is written for it |
