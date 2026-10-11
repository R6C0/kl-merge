# Retomoto Tower: the fed comes back at the elevator, nobody plops out, the street's police stand in position

Track X1, 2026-10-11 evening. The owner, 20:15, after playing Retomoto on the set of that day (DM09 =
`<work>\build\p_tab\DM09` = `z_fedpts\retomoto_lanes` + HUD look + fed line; hook ship_w8):

1. fed, died in the tower: 'yes but it spawns at the very top, should be at the elevator at the bottom, btw with the lmg
   guy and the two pistol guy at the elevator they always spawn in too late, make them spawn a bit early so its not like
   they just plop out try and do that with other parts if you can'
2. fed, died on the street: 'yes but then when u spawn the npc swat are like all bunched together, they should be in
   position waiting'
3. the crew's lanes: 'ehhh idk' - no verdict; the lanes are not touched.

OFFLINE. Read in `kl2.exe` build 0490 (`debug\dasm.py`), measured on the builds, built into
`<work>\build\x_spawn\retomoto`. **NOTHING HERE HAS RUN IN THE GAME.**
Status words: **READ** = disassembled, address given. **MEASURED** = computed from the build's files. **SEEN** = the
owner's log or pictures. **ASSUMED** = fits what was read, not seen. **GUESS** = a number of mine.

## 0. Short answers

- **Why men 'spawn in' (READ).** A squad whose `ZSquadScript` field 3 is 0 has its men HIDDEN and taken out of the
  actor tables when the level starts, and they are shown the moment the squad is handed its first goal - when a
  trigger box, a timer or another squad's 'wiped out' list first names a rout of theirs. On Retomoto that was 46 of
  the 48 enemy squads. Field 3 = 1: the men stand in the world from the load. (The notes called field 3 'active from
  the start' as an ASSUMPTION since 2026-10-09; it is read now, section 1.)
- **The fed's tower places** are now all three in the lift hall, 11 .. 15 m on foot from the box before the tower
  car, on the floor, outside every lift car: (2610, 19650, -190), (2330, 19650, -230), (2490, 19650, -630).
  `kl_fa_fedpoints.py` default `--low 3` and a new rule 'nearest the join box on foot' (`LIFT_NEAR`, `POST_FAR`).
- **The lift hall's guards** - the machine gunner and the three squads round the lifts, 7 men - are in the world from
  the load (`kl_fa_author.HALL_ACTIVE`). Their boxes still start their routs.
- **The street**: the men of the three waves (26 of F07's police + 7 of the campaign's who stand among them) are in
  the world from the load, and each of the 29 who stood in a clump has a post of his own 3 m behind HIS cover point.
  Before: 15 pairs of street police stood within 1.5 m of each other; after: 2 pairs (the squads that come from behind
  the crew, left asleep on purpose).
- **The other four maps**: every enemy squad is in the world from the load already (table, section 4). Nothing to fix.
- **What the owner most likely saw 'bunched'** (SEEN, his picture `<work>\research\watch\20261011_171409\0233_11534s.jpg`,
  7 s after `fed: YOU STAND at (-5484, -40, 9142)`): five or six men in black standing shoulder to shoulder in the
  open carriageway south-east of him. Which squads they were the picture does not say. Two causes are in the data and
  the first is fixed: (a) the start places (section 3.1); (b) the fall-back and 'walk to the van' routs are Defend
  routs with ONE place for a squad of two or three (section 3.3) - NOT changed, it needs new entities.
- **One build**: `<work>\build\x_spawn\retomoto` (archive `307b27162f37ab000b184474616a4a15652edd8e`, 218,953,782
  bytes) = `z_lanes\retomoto_full` -> `kl_map_ai.py spawnfix` -> `kl_fa_fedpoints.py apply`. Against
  `z_fedpts\retomoto_lanes` only `.prp` and `.gms` differ, and in them 22 squads' field 3, 29 actor groups' place and
  the three tower spawn points. Every check passes (section 5).

## 1. How a squad's men come into the world (READ)

`ZSquadScript` (vtable `0xbcce3c`, property list `0xd0c824`): field 3 is a bool stored at `this + 0x58` (record
offset 0x54; a record's offset is relative to `this - 4`, as `re\map_ai.md` 1 found for ZSoldier).

| | routine | what was read |
|---|---|---|
| load | slot 4, `0x8b2120` | calls the base loader `0x553070`, then **inverts the byte**: `[this+0x58] = ([this+0x58] == 0)`. So in memory +0x58 means 'start hidden' |
| the controller's phases | slot 30, `0x8da110` | the phase byte `+0x21` walks 1..7 and calls slots 13, 14, 15, 16, 28 in turn (jump table `0x8da1ac`) |
| phase 1 | slot 13, `0x6316b0` | makes the `CPPScript::ZSquad` (`0x7696f0`) with the 15 lists, field 2 and field 19; keeps it at `+0x3c` |
| phase 2 | slot 14, `0x7b3790` | gathers the members: every child actor whose node is NOT hidden and whose game type fits (`[this+0x34]` bits); a soldier is counted in `[squad+0x8c]` and listed at `[squad+0xc0]`. Field 0 == 1 (eUnleashed) sets `[soldier+0x6fc]`. At the end: field 20 >= 0 -> `0x8d2e20(squad, 0)` (it is -1 on every squad of these builds) |
| **phase 5** | slot 16, `0x787a10` | **`if [this+0x58]: 0x8d2e20(squad, 0); [this+0x58] = 0`** |
| hide | `0x8d2e20` | for every soldier of `[squad+0xc0]`: health object whole (`0x716660`), out of the two actor tables of `[0x1535c70]` (`0x4c5510` -> `0x4b33a0`, `0x739fc0`), **the node's Hide** (`[actor+4]` -> `0x598460` -> vtable +0x54 = ZGEOM slot 21), actor slot +0x598, `0x7247a0`; the same for the lists at `+0xf4` and `+0x128` |
| a rout is named | e.g. `ZSquadModifierBehaviour` slot 26 `0x4ebed0` ('AITrigger' -> slot 34 `0x833830` -> `0x791090`) | the rout hands its goal to the squad: `0x7f6750(squad, goal)` |
| show | `0x7f6750` | with soldiers in the squad (`[squad+0x8c] != 0`) and unless `[[squad+0x19c]+0x20d]` is set: **`0x7c0d50(squad, 0)`** - every member whose node has the hidden bit (`[node+0x3c] >> 10 & 1`) is shown and entered again; then the goal is queued (`0x6cabf0`) |

So: field 3 = 0 -> the men are not drawn, not in the actor tables, until the squad's FIRST goal of any kind (a
Defend, a RunToCover, a Flanking rout - and a SquadModifier too: `0x4ebed0` / `0x791090` are shared). Field 3 = 1 ->
nothing hides them. This is the mechanism behind every 'they spawn in' the owner has reported on this map since
2026-10-09.

Not read: what `'AITrigger'` sent to the squad's own group node does (the tower's `TriggerBox_PreLastTrigger` names
`Squad_MG-Guy` itself, not a rout of his: `ZSquadScript` slot 26 `0x8a9a60` knows four other messages and passes the
rest on to the squad object, `0x641960`). The machine gunner does appear in the owner's rounds, so something shows him.

What a man does who is in the world with no goal: ASSUMED he stands where the level put him and fights whom he sees.
SEEN twice on this map: `Enemies!010_RetoBldFront!Squad_InFront` (field 3 = 1 in every build) stands on the forecourt
through the tower part; the boardroom's guards with field 3 = 1 shot the heisters at the glass during the countdown
(run S2, `re\retomoto_fa.md` 10.3).

## 2. The audit: who plops out (`python tools\kl_map_ai.py spawns <build>`)

For every enemy squad: in the world from the load or not; the trigger boxes that name it (directly or through timers
and counters: `kl_fa_bots_rt.wake_map`), the one nearest the crew's start first (ASSUMED the first one crossed); from
any place somebody can stand inside that box (its footprint on the navigation mesh, every 1 m) the nearest a man of
the squad appears, and the nearest he appears IN SIGHT. Sight = a straight line from 1.5 m over the floor to the
man's chest through the walk test's collision samples (`kl_fa_fedpoints.Ground.sight`). **PLOP** = in sight within
40 m (`PLOP_NEAR`, GUESS). LIMITS: convex shapes (cars, crates) do not stop the line; a pane of glass with collision
does; 'inside the box' is the worst place of the box, not where the way crosses it.

### 2.1 Retomoto, before (`z_lanes\retomoto_full` = what the owner played; log `x_spawn\checks\round1\..`, scratch `spawns_rt0.txt`)

`PLOP 8 squads / 19 men, in sight far 14 / 24, out of sight 22 / 37, by a timer 3 / 9, active 1 / 3`.

| squad | men | first named by | nearest / nearest in sight, m | verdict |
|---|---|---|---|---|
| `020_Office!Squad_Guards_Inside_01 / _02 / _03` | 2 + 4 + 3 | the blast timer | - | by a timer (the design: 'guards unaware until the blast'. By the reading of section 1 the boardroom is EMPTY through the countdown and the nine appear at the blast, 16.5 s after the round-start event, when the glass goes. Not changed: with field 3 = 1 they shot the heisters during the countdown) |
| `030_Reception!` three squads | 5 | `tb_LEFT_TheySpotYou` | 10 .. 12 / none | out of sight (the boardroom's wall) |
| `040_Atrium_3rd!` six squads | 10 | `tb_RIGHT_TheySpotYou`, `TriggerBox_EnterAtrium` | 26 .. 38 / none | out of sight |
| `050_Atrium_2nd!` four squads | 7 | `TriggerBox_EnterAtrium(Further)`, `Trigger_2ndFloorStairs` | 14 .. 39 / none | out of sight (a floor below) |
| `060_Atrium_1st!` four squads | 7 | `Trigger_2ndFloorStairEnd` | 40 .. 44 / none | out of sight (a floor below) |
| `070_Elevators!010_Squad_Elevators` | 3 | `Trigger_1stFloorStairEnd` | 39 / none | out of sight |
| `060_Atrium_1st!Squad_MG-Guy` | 1 | `TriggerBox_PreLastTrigger` | 25 / none | out of sight BY THE MODEL - the owner sees him appear ('the lmg guy'): he stands at the lift end of the one passage, (2908, 19601, -68), and the box lies across its other end. The model's line is stopped by something in that passage (a show case's glass?); the owner's eyes count |
| `070_Elevators!010_Squad_Elevators_GuardingElevator` | 1 | `TriggerBox_PreLastTrigger` | 21 / none | out of sight |
| **`070_Elevators!020_Squad_Elevators_Last_Stand_02`** | 2 | `TriggerBox_OpenExitElevator` | **5 / 5** | **PLOP**: the box is the passage's lift end, the two stand 5 and 12 m from it in the hall |
| `Squad_Teargasguys` | 2 | the lobby lift's box + 5 s | 73 / none | out of sight (the design) |
| `Squad_InFront` | 3 | - | - | active |
| **wave 1**: five F07 squads, `Squad_SWAT_From_Behind` | 10 + 3 | `tbExitLoot` (the first step on the road) | 7 .. 32 / 7 .. 55 | **PLOP** (5 of the 6; `RunForDumpster` 55 m: far) |
| from behind: `Squad_RoadBlock_South`, `..#02`, `Squad_SWAT_From_Behind_South` | 3 + 2 + 3 | `tbExitLoot` | 9 .. 47 / 9 .. 47 | **PLOP** for two - but from the box's SOUTH END (z -11900); the way meets the box at the forecourt, 41 m or more from them |
| **wave 2**: six F07 squads, the sniper, the launcher, `RoadBlock_R2 / _L` | 13 + 4 | `tbReleaseDog` (z -3600..-3000) | 56 .. 87 / 57 .. 87 | in sight, far |
| the dog | 1 | `tbReleaseDog` | 91 / none | out of sight |
| **wave 3**: `040_EscapeEntranceLeft / Right` | 3 | `tbEscapeAI` (z 1700..2300) | 80 / 80 | in sight, far - **but 10 m from two of the fed's street places**: a fed who comes back at the SWAT truck before the crew is at z 1700 sees nobody, and then three men appear |

### 2.2 Retomoto, after (`x_spawn\retomoto`; `x_spawn\checks\spawns_after.log`)

`PLOP 2 squads / 6 men (the two from behind, see above), in sight far 1 / 2 (RoadBlock_South#02), out of sight 19 /
32 (the tower above the first floor's lift hall, the dog, the tear-gas pair), by a timer 3 / 9 (the boardroom),
active 23 / 43`.

## 3. What was built

### 3.1 The fed's tower places (`tools\kl_fa_fedpoints.py`)

Before (track L's second form): two on the top gallery (-1550, 21050, 1570) / (-670, 21050, 1770), one in the lift
hall's south wing (2650, 19650, -1390) - 2.1 .. 3.3 m from three posts of the hall's guards. SEEN in his log at
20:19:58 and 20:22:27: `fed: YOU STAND at (-1559, 21000, 1573)` and `(-647, 21000, 1733)` = 'the very top'.

Now `LOW = 3` (all three on the join box's floor, y 19600) and of that floor's cells that pass every old test
(crew's ground, a body's room, 0.5 m from a mesh edge, 3 m or more outside the join box `JOIN_FAR`, 6 m from every
place a step of the AI heisters names `BOT_FAR`, 2 m from an enemy's start place) those that are also

- within `LIFT_NEAR` = 2000 ON FOOT of the floor under the box's middle (cell by cell over the crew's ground along x
  and z: the passage that leads to the hall is near the box through a wall and far from it on foot - a first try by
  straight distance put the third point in the passage), and
- `POST_FAR` = 250 from every POST of an enemy squad on that floor (`kl_fa_bots_rt.enemy_posts`: start places and
  every place a rout names - the old rule knew the start places only),

the nearest to the box first, 2.5 m apart (`SEP`). 46 cells pass; taken:

| point | place | on foot from the box's middle | from the crew's hold before the car | from the nearest guard post |
|---|---|---|---|---|
| Dead_06 | (2610, 19650, -190) | 10.8 m | 6.2 m | 3.2 m (the machine gunner's place (2908, -68)) |
| Dead_05 | (2330, 19650, -230) | 12.8 m | 6.3 m | 2.9 m |
| Dead_07 | (2490, 19650, -630) | 15.2 m | 10.3 m | 2.8 m |

All in the lift hall `M09_A_Ins_Elevators_101` (x 2100..2800), its middle and south half; the join box is x
2550..2790, z 800..1100 at its north end, the escape car behind it. The six cars' floors are closed in (not the
crew's ground): no point can be put in one. `kl_fa_fedpoints.py check`: 7 good.
`--low 1` gives track L's form, `--lift-near 0` its rule (the farthest cells from the heisters). The four street
places are the ones `z_fedpts\retomoto_lanes` has.

**A police human and the join box** (READ again in `klhook\kljoin.c` / `klcrew_rt.c`, nothing changed):
`klj_tick` tests the feet of the local player object, whatever it is. A fed who walks the 11 m into the box is
jumped to the lobby, and in the same tick `klcrew_rt.c` moves EVERY AI heister still in play to the lobby with him -
from wherever they are in the tower - and the jump's list starts their street route. That has been so since track L
(it is how the round goes on when the human is police), but the box is 11 m from where he now appears instead of 23
or 129: **a fed who steps into it early ends the tower for the whole crew.** The owner should know; a `[Join]` key
'not for a police player while a heister is above floor 1' would be a hook change (not this track's).

### 3.2 The lift hall's guards are there from the load (`kl_fa_author.HALL_ACTIVE`)

`ZSquadScript` field 3: 0 -> 1 on `060_Atrium_1st!Squad_MG-Guy`, `070_Elevators!010_Squad_Elevators`,
`..!010_Squad_Elevators_GuardingElevator`, `..!020_Squad_Elevators_Last_Stand_02` (1 + 3 + 1 + 2 men), and - review M1 -
the four `060_Atrium_1st!Atrium_1st_{InfrontElevator,PillarCover}_Squad_01` / `_CoverMiddle_Squad_01,02` (1 + 2 + 2 + 2 = 7
men; they stand in the SAME hall as the fed's three places, 3.6 .. 9 m from them, and were woken only by
`Trigger_2ndFloorStairEnd`). 14 men in all. They stand at
their places: (2908, -68), (2340, 1238) (2534, 882) (2604, -1063), (2484, -1554), (2675, 959) (2461, -1239).
Their boxes are as they were: `Trigger_1stFloorStairEnd` sends the three to the passage's atrium end,
`TriggerBox_PreLastTrigger` the gunner (as far as it does anything, section 1) and the lift guard, `OpenExitElevator`
the last two to the passage's mouth.

Why 'from the load' and not 'one box earlier' ('a bit early' were his words): the fed's three places are in this
hall. With the guards asleep he stood in an empty hall and they appeared round him when the crew came down; one box
earlier would only move that moment. And 'in the world' is one bool a squad, the form `Squad_InFront` has in every
build, against a list edit on four boxes.

The rest of the tower is left: the audit measures sight from the WAKING BOX, never from where a fed stands, so it missed the
four Atrium_1st squads (review M1); `kl_map_ai.sleeping_near_fed` and a NOTE in `kl_fa_fedpoints check` now list every
hidden squad with a man within 15 m (FED_NEAR, a GUESS) of an AFTER_DEATH point, and a NOTE says when HALL_ACTIVE / ACTIVE
squads are still field 3 = 0 (review S4: a build without the `spawnfix` step). Otherwise the audit finds no other squad that appears in sight (2.1), and 38 more men awake
from the load would fight by sight instead of by their boxes - the staging of track G's gates.

### 3.3 The street: posts, and in the world from the load (`kl_fa_street.POSTED / ACTIVE / POST_*`)

**Why they stood in clumps (MEASURED).** `kl_fa_street.relay` pulls a squad's actors in to 15 m (`MAX_BACK`) behind
its cover points by SCALING their offsets from the cover's centre (`pull = MAX_BACK / back`). F07's men, who stand 3
.. 58 m from their cover round the corners of F07's alleys, come out 0.3 .. 0.9 m from one another:
`030_FinancialAlleyExit_Left` three men within 0.7 m at (-4090, 5550), `..ExitStreet_Right` two 0.44 m apart,
`020_..RunForDumpster` two 0.6 m apart, `Exit_Right` three within 1.7 m; and `TRUCK` lays wave 3 in a row 2 m apart
at the SWAT truck's doors. 15 pairs of street police within 1.5 m, 21 within 2.2 m.

**The posts.** Every actor of the 13 F07 squads (not the dog) and of `Squad_SWAT_From_Behind` gets a post of his own:
`POST_BACK` = 300 north (the police side: away from the tower's doors) of THE RunToCover POINT THAT NAMES HIM
(`RunToCoverPosInfoRout` field 5; the `10_RunToCover` one where a squad has two routs) - a man without one: where he
stood - on the nearest cell within 7 m (`POST_SNAP`) that is free floor on the street's mesh with a body's room,
outside every static vehicle (their collision is a convex box the walk test does not see: `_sp_vehicles`), 2.2 m
from every other man (`POST_APART`), 1.5 m from another man's cover point, 2.5 m from every leg and 4.2 m from every
place of the AI heisters' lanes (`POST_LEG`, `POST_HOLD`: `kl_fa_bots_rt.check` wants 2 m / 4 m), clear of the
bounds and 3 m off the van's road. The cover points were laid beside the street's cars by `SQUADS`' anchors, so a
post is the police side of that car. 29 men moved, 1.0 .. 21 m (median 10.6); the least distance of a post from a
leg is 2.55 m; `kl_fa_bots_rt.py check`: 'the nearest any leg comes to one of the 124 posts is 254' (rule 200).
The table: `<build>\spawnfix.txt`. Wave 3: one man at the SWAT truck's rear (-3510, 10650), two at the taxi 9 m
east of it (-2510, 11070) (-2770, 11150) - at their cover, no longer a row at the truck's doors.

NOT turned: an actor group keeps the matrix it has (no stock level has a ZFFActor under a rotated parent; whether
turning the group itself is safe was not looked at). They face as F07 faced them, not 'the tower's doors'.

**In the world from the load.** Field 3: 0 -> 1 on the squads of `kl_fa_street.ACTIVE`: wave 1 (five F07 squads +
`Squad_SWAT_From_Behind`: 13 men), wave 2 (six F07 squads + `Squad_SniperResponse`, `Squad_Launcher_Dude_North`,
`Squad_RoadBlock_R2`, `Squad_RoadBlock_L`: 17 men), wave 3 (3 men). The wave boxes name the same routs as before:
the wave runs to its cover (3 m), falls back when a neighbour is wiped out, wave 3 is unleashed 13 m before the van,
every squad walks to the van 28 s after the 'run' line. What changes for the crew: police who see them shoot from
their posts before the box sends them - wave 1 stands 35 .. 55 m north of the door line and has the forecourt's
mouth in view.

Left asleep on purpose: the dog; `Squad_Teargasguys` (run in from out of sight 5 s after the lift);
`Squad_RoadBlock_South`, `..#02`, `Squad_SWAT_From_Behind_South` (they come up the road from BEHIND the crew: the
design of 2026-10-10; their men still stand 0.6 .. 1.8 m apart).

**NOT fixed: one place for a whole squad.** `10_Defend` (the road block's fall-back, 20 m south of the van's stop) and
`40_RunToEscape` (every squad's place round the van) are `DefendBehaviourRout`s with ONE `Pos#01` for two or three
men; on F07's alleys that point has cover round it, on this road it is open carriageway. `Exit_Left`'s three are
sent to (-4498, 8594) and `ExitStreet_Left`'s two to (-3703, 8800): that is 11 and 18 m from where the owner stood
as a fed at 20:26. A second `Pos#` per man is a new entity (the SLOT ids of every later entity move: `.oct`, `.rmi`,
`.rmc`, the list pool) - `kl_fa_bots_rt` adds entities that way, a step on a finished build like this one does not.
PROPOSAL: in `kl_fa_street.relay` give each of those routs the squad's RunToCover form (stock F07 has
`20_RunToCover` with one point a man), or lay `BACK_2` / `RING` beside the parked buses.

### 3.4 The tools

| file | what |
|---|---|
| `tools\kl_map_ai.py` | NEW commands `spawns` (the audit, read only), `spawnplan`, `spawnfix <build> <out>` (field 3 + posts on a FINISHED build; options `--asleep=hall,wave1,wave2,wave3`, `--active=..`, `--auto` = every PLOP squad, for another map, `--no-posts`), `spawndiff <a> <b>` (entity by entity: only a squad's field 3, an enemy actor group's place and the AFTER_DEATH points may differ) |
| `tools\kl_fa_fedpoints.py` | `LOW` 1 -> 3, `LIFT_NEAR`, `POST_FAR`, option `--lift-near`, the low points' rule; `Ground.sight` |
| `tools\kl_fa_author.py` | `HALL_ACTIVE` (table + the reading) |
| `tools\kl_fa_street.py` | `POSTED`, `ACTIVE`, `POST_BACK / SNAP / APART / LEG / HOLD / COVER` (tables + why) |

`kl_fa_author.wire` and `kl_fa_street.relay` do NOT write these tables: a Retomoto built from scratch needs
`spawnfix` run on the finished folder (before `kl_fa_fedpoints.py apply`: the fed's places keep off the posts).

## 4. The other four maps (`<work>\build\p_tab\DM01 DM02 DM03 DM06`; logs `x_spawn\checks\spawns_DM0N.log`)

| map | enemy squads / men | in the world from the load | hidden until named |
|---|---|---|---|
| DM01 Hot Coffee | 10 / 13 | 10 / 13 | none |
| DM02 Late Night Opening | 6 / 12 | 6 / 12 | none |
| DM03 Withdrawal | 8 / 15 | 8 / 15 | none |
| DM06 A Walk in the Park | 9 / 14 | 9 / 14 | none |

Dead Men's Fragile Alliance maps have every guard and policeman in the level from the load (`re\map_ai.md` 7 said
so: '0 with field 3 = 0'); the ones that ARRIVE come by car, which is another mechanism (a car that drives in).
Nothing plops out by this cause, nothing was built. Should a later build give one of them a hidden wave (the fed
squads of `kl_fa_fed.py` are such: field 3 = 0, one man each, shown at a heister's death):
`python tools\kl_map_ai.py spawns <build>` lists it and `spawnfix <build> <out> --auto --no-posts` puts every PLOP
squad in the world from the load.

## 5. The build and its checks

```
python tools\kl_map_ai.py spawnfix "<work>\build\z_lanes\retomoto_full" "<work>\build\x_spawn\_posts"
python tools\kl_fa_fedpoints.py apply "<work>\build\x_spawn\_posts" "<work>\build\x_spawn\retomoto"
bash "<work>\build\x_spawn\checks\checks.sh"          (the intermediate _posts, archive 799427cf..., is deleted)
```

`z_lanes\retomoto_full` (archive `85c884eb...`) is track K's lanes build, the source of `z_fedpts\retomoto_lanes`
(`8a4042e0...`). The last line of every check (`x_spawn\checks\checks.txt`; the working tree's tools, which for
`kl_fa_bots_rt.py` / `kl_fa_bots_dyn.py` are the committed ones):

```
kl_map_ai spawndiff (z_lanes -> the spawn step)        RESULT (kl_map_ai spawndiff): only what the steps mean to change differs
kl_fa_fedpoints diff (the spawn step -> the output)    RESULT (kl_fa_fedpoints diff): only what the step means to change differs
kl_map_ai spawndiff (z_fedpts\retomoto_lanes -> out)   RESULT (kl_map_ai spawndiff): only what the steps mean to change differs
kl_fa_fedpoints check    RESULT (kl_fa_fedpoints): PASS (0 FAIL, 8 NOTE); 7 point(s): 7 good, 0 doubtful, 0 bad; START half 3, jump half 4
kl_map_ai spawns         RESULT (kl_map_ai spawns): PLOP 2 squad(s) / 6 men, in sight, far 1 squad(s) / 2 men, out of sight 19 squad(s) / 32 men, by a timer 3 squad(s) / 9 men, active 23 squad(s) / 43 men
kl_map_ai spawnfix       RESULT (kl_map_ai spawnfix): PASS      (read back: every squad's field, every man at his post)
kl_fa_bots_rt check      RESULT (kl_fa_bots_rt): PASS (0 FAIL, 12 NOTE); start delay 91.5 s after a blast at 16.5 s; 7 gate(s) on the tower's way out; 3 lane(s) on the street; jump list 7; [CrewJoin] places 7
kl_fa_bots_dyn check     RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 6 NOTE)
kl_impact                problems: 0 in 1 levels
kl_map_guns check        6 guns with looks ...; problems: 0
kl_fa_street report      PEOPLE OF THE STREET: 47 actors below y 5000 (27 of the host's squads, 20 of the campaign's), 0 with a drawing fault
kl_fa_author ledge       ledge test: ok
kl_fa_talk check         findings: FAIL 1, NOTE 0      (the source's own: the countdown's NOW! against the blast; 0 lines differ from z_fedpts\retomoto_lanes' log)
KLTalk.ini               6c78c079fdf893257cc3d61774e06f07028d8a31 = rt_full6's, the approved one
```

Against `z_fedpts\retomoto_lanes` (`checks\spawndiff_ref.log`): members `.prp` (5,139,536 bytes both) and `.gms`
changed, the other 28 the same CRC and size; beside the archive `fedpoints.*` changed, `spawnfix.*` new, 35 files
equal. In the `.prp`: 22 squads field 3 0 -> 1, 29 enemy actor groups another place (`ZGEOM[2]` only), 3 AFTER_DEATH
points (the tower's). In the `.gms`: 32 records' place; name, type, model, aux, REF, raw block, group, parent,
children, list key and list links of all 26,650 records equal. No entity added or removed, no pool change: `.buf`,
`.oct`, `.rmi`, `.rmc`, `.HVK` untouched. So the tower's gates and the lanes are byte for byte what they were.

Controls against track L's logs of `z_fedpts\retomoto_lanes`: `kl_fa_bots_rt` / `kl_fa_bots_dyn` 2 lines each (the
NOTE 'nearest leg to a police post': 262 -> 254), `kl_fa_street report` 56 lines (the actors' places, the sketch),
`kl_fa_talk` 0.

Applied to its own output the spawn step plans nothing (`checks\verify_self.log`: 22 squads 'in the world from the
load already', 0 men moved).

A FIRST ROUND FAILED and is kept in `x_spawn\checks\round1`: `kl_fa_bots_rt check` FAIL 4 - 'lane X: its hold ...
is 353 from a post of the police: wanted 400' - four posts lay 2.9 .. 3.7 m from a hold of a lane. `POST_HOLD` = 420
from every place of the heisters is what that added.

## 6. Live checks (for the lead; nothing has run)

The build has no HUD look and no `[FedBody]` line: add them as for `p_tab`. Hook: any of today's (`[Fed] Enable=1
Player=1 Log=1`). The checks P0 .. P4 of `re\fed_points.md` 6 hold for this build too (a spawn point hidden at the
load, the switch) with the new tower places.

| | how | PASS | means when it fails |
|---|---|---|---|
| **S0** | `x_spawn\retomoto`, a plain round, idle player | loads, GO, the round as `p_tab\DM09`'s: the gates' clock, the join, nobody of the crew dead before about GO + 120 s | a fault at the load: 40 more men in the world from the first frame - try `spawnfix --asleep=wave1,wave2,wave3` (hall only), then `--asleep=hall` (street only) to find which |
| **S1** | die in the TOWER before the lift, three times or more | `fed: YOU STAND at` one of (2610, 19602, -190), (2330, 19602, -230), (2490, 19602, -630) (+- 30); the picture: the lift hall, guards standing in it, the lift doors | y 21002: an old build is in the slot. A guard shoots the fed: police and the tower's guards are not one side - say so (not read) |
| **S2** | walk the tower (known remaining plops, review S2: `Squad_SWAT_From_Behind_South` 9 m and `Squad_RoadBlock_South` 17 m in sight - left asleep on purpose, they come from behind; not hidden by this track)  with the scripted player (`kl_playtest` B1) or the owner; pictures every 2 s from the first floor's stairs on | the machine gunner and the hall's men are THERE when the passage and the hall first come into view; nobody appears | a man appears: which, where - he is not one of `HALL_ACTIVE`'s seven, or field 3 is not what shows him |
| **S3** | the street: out of the lobby, pictures from the front door on | police stand in the traffic 35 .. 55 m up the road BEFORE the first step on the carriageway, one by one, none in a clump; at the road block a line of single men behind the three police cars | men stand shoulder to shoulder at a START place: say which squad. Men in the open ROAD in a clump later in the round = section 3.3's one-place routs (known, not fixed) |
| **S4** | die on the street (after the join) | `fed: YOU STAND at` one of the four street places (re\fed_points.md P2); from the SWAT truck's side: one man at the truck's rear, two at the taxi east of it, standing, before the crew is at z 1700 | nobody there until the crew comes: field 3 does not do what was read |
| **S5** | K1 of `re\retomoto_bots_street.md` on this build (the owner's balance, idle player): who of the crew lives to the van | not worse than the same run on `p_tab\DM09` | the crew is shot down on the forecourt by wave 1 from its posts: `spawnfix --asleep=wave1` (wave 1 rises at the first step on the road as before; its men still have posts of their own) |
| **S6** | frame time / the 'memory:' line of S0 against a run of `p_tab\DM09` | no difference that matters | 40 awake men cost frames: `--asleep` by set |

What the owner should see: as a fed in the tower he stands in the lift hall among the hall's guards; coming down
the tower the gunner is already at the end of the passage; outside, police are spread over the road at cars and
buses from the moment the doors are in view, and as a fed at the SWAT truck he finds three men at their places.

## 7. ASSUMED and GUESS, in one place

- ASSUMED: a man in the world with no goal stands at his place and fights whom he sees (seen for `Squad_InFront`
  and the boardroom's guards, not for F07's police or the hall's guards).
- ASSUMED: 40 more men awake from the load (7 hall, 33 street) are no load on the frame and do not change the tower
  part (the street's stand 200 m away and 210 m lower). Stock levels hold 17 .. 35 of their 40-odd men back; why
  was not read.
- ASSUMED: police awake from the load do not leave their posts for a fight they hear. Not read (`EIdleAlertness` is
  `eNormalAlertness` on all of them; squad attitude `eStayBack`).
- ASSUMED: a fed among the tower's guards is not their enemy (he stood 2 .. 3 m from three of them hidden; now they
  are awake).
- ASSUMED: the box nearest the crew's start is the one that first names a squad (the audit's verdict rests on it).
- GUESS: `PLOP_NEAR` 40 m; `LIFT_NEAR` 20 m on foot; `POST_FAR` 2.5 m; `POST_BACK` 3 m; `POST_APART` 2.2 m; the SWAT
  truck's and van's footprint (a bus's width, 8 m long).
- The sight model (2): collision samples only; it calls the machine gunner 'out of sight' where the owner sees him.
- 'The owner saw clumps at the start places' is ONE of two readings of his picture (0.); the other is not fixed.

## 8. Not done

- The one-place Defend routs (3.3) - the likeliest reason for a clump late in the round (review S1: the owner's 'bunched' picture is most likely THESE, not the start places; `10_Defend`, `40_RunToEscape` Pos#01 for 2-3 men, two such points 11 and 18 m from where he stood at 20:26; needs new entities = a kl_fa_street chain step before fedpoints, its own track). Check 2 of the owner is therefore only half answered.
- The men are not turned to face the tower's doors (3.3).
- The three squads from behind keep their places and stay asleep; the boardroom's nine still appear at the blast.
- `kl_fa_author.wire` / `kl_fa_street.relay` do not write the tables: the step is `spawnfix` on a finished folder.
- No top-view pictures of the posts (the table is `<build>\spawnfix.txt`; `kl_fa_street.py report`'s sketch shows them).
- The other maps: nothing to build. `kl_map_ai.py` got no per-map option beyond `spawnfix --auto`.
- What 'AITrigger' to a squad's own node does (the machine gunner's box), and why the model sees no line to him.
- The HUD look and the fed's body line on this build: the lead's.

## 9. Fix round (review of 2026-10-11)

- M1 done: the four Atrium_1st squads are in `HALL_ACTIVE` (14 men from the load in the hall); rebuilt (archive in `x_spawnetomoto`,
  the first round's build kept in `x_spawnetomoto_round1`, its checks in `checks_round1`).
- S1 stated plainly above (section 8); S2 listed in the live checks; S4 done as NOTEs; S5 stays a live check (S0 with `[Bots] Log=2`,
  then `--asleep=wave1,wave2`).
- S3 NOT changed offline: the three places are 11 .. 15 m on foot from the join box. A police human who walks into the box jumps himself
  and every AI heister still in play to the lobby (kljoin.c has no police test): a hook key is the lead's. Moving the places 5 m south
  was not done: they then leave the lift hall (LIFT_NEAR) which is the owner's request.
