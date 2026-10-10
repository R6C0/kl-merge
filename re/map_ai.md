# The enemies of the four Dead Men Fragile Alliance maps: measured, compared, made harder

Agent t-ai, 2026-10-10. OFFLINE: nothing launched, nothing installed, nothing written into the Dog Days
folder. Tool: `tools/kl_map_ai.py` (its docstring is the short form of this file). Builds:
`<work>\build\t_ai\M01 M02 M03 M06` (default) and `<work>\build\t_ai\car_exit\M01 M02 M03` (section 4).
Source builds, unchanged: `<work>\build\z_maps\<map>`. NOTHING HERE HAS RUN IN THE GAME.

The owner, after Late Night Opening: "the ai a bit too easy so just probably take some logic from retomoto
and put it in there and do the same fixes for the other maps, i think the walk in the park is a heli so it
shouldnt be as bad".

## 0. Short answers

1. **Why they are easy, measured.** A stock Dog Days Fragile Alliance level has 21..45 armed enemies with
   2,575..6,120 hit points between them, 17..35 of them NOT in the world at the load (they arrive as waves),
   and seven AI heisters beside the player. A Dead Men map has 12..15 enemies with 1,220..1,500 hit points,
   all standing in the level from the load, and no AI heister. Per man they are not weak: their accuracy is
   98..100 (stock SWAT: 55). Dead Men made few men deadly; Dog Days makes many men tough.
2. **A fault found on the way, bigger than any tuning: the police that come BY CAR lose the behaviour that
   ends their drive.** `kl_convert` removes every `VehicleExitBehaviourRout` (M01 2, M02 1, M03 4 - the squads
   of 4, 4 and 9 of the 13 / 12 / 15 soldiers). With it go the orders that rout gave: M02's four police -
   the map's only reinforcement - never get their flank rout or their hunt timer. Cause and two repairs:
   section 4. What a squad does that sits in a car without that rout was not established, so this is a
   CANDIDATE for "too easy" on M02, not a proven cause; it is on M01 and M03 too.
3. **Retomoto's soldier table must NOT be copied to these maps.** Its first form wrote skill names by weapon
   class (`eAmateur` / `eRegular` / `eVeteran`); since 2026-10-10 `kl_arms.ROWS` writes whole stock rows
   (accuracy 50) on Retomoto. Read in kl2.exe (section 1): a skill name other than `eCustom` OVERWRITES accuracy
   and aim with a preset (35 / 50 / 60). Retomoto's campaign guards came out of the conversion at 50; every
   soldier of M01 / M02 / M03 is `eCustom` with accuracy 98..100, so either table would cut them to 38..66.
   `kl_map_ai` uses the same ladder as FLOORS instead (nobody gets worse); `--presets` writes the names, for a
   comparison run.
4. **What the step changes** (values and reference lists of existing objects; only the `.prp` member of the
   archive differs, proved by CRC of every member): health by weapon class up to stock's numbers (hit points
   +41..52 %), rifles for the squads that arrive, the map's own reinforcement timers shorter and (M02) started
   with the round, 2 squads a map unleashed, 31 squads with a "wiped out" list, 33 routs named when the escape
   vehicle is called, and the lost car orders by-passed.
5. **What it cannot change: the head-count.** No entity is added. 12..15 men stay 12..15 men; section 7 says
   what each map lacks against stock.

## 1. What a soldier's numbers are (kl2.exe, read 2026-10-10)

`ZSoldier` = class `ZSoldierRout` (vtable 0xbd08c4), 23 fields. Property offsets from its reflection records
(a record's offset is relative to `this - 4`): field 3 at +0xa0, the fourteen floats 4..17 at +0xa4..+0xd8.

- Slot 4 (0x846340) copies the fields into a block D at rout+0x34 (style +0, the two special features +4 /
  +8, skill +0xc, floats 4..17 at +0x10..+0x44, the bool 20 at +0x48, the string 18 at +0x49) and calls
  **0x46e410**: a switch on the skill name. `eN00b` .. `eElite` write five numbers over what the level stores:

  | skill name | field 4 | 5 | 6 | 13 | 14 |
  |---|---:|---:|---:|---:|---:|
  | eN00b | 20 | 0 | 20 | 100 | 40 |
  | eAmateur | 35 | 20 | 10 | 70 | 45 |
  | eRegular | 50 | 50 | 10 | 50 | 50 |
  | eVeteran | 60 | 60 | 5 | 20 | 55 |
  | eElite | 90 | 90 | 10 | 0 | 60 |
  | eCustom | the level's own numbers | | | | |

  Then field 4 is multiplied by 1.1 (table at 0xd19328: 1.1 / 1.0 for `No_Mercenary`, 1.0 / 1.0 otherwise) and
  fields 4 and 6 are clamped to 0..100 (0x6143f0).
- **Dead Men's exe has the same function (0x724060, called from its slot 4 at 0x724a60) with the same
  numbers on ITS fields 4, 5, 6, 9, 10** (and 300 / 500 on its field 12 for eVeteran / eElite). That proves
  the converter's pairing Dog Days 13 / 14 <- Dead Men 9 / 10, which re/pairings.md had "by values only,
  medium".
- Slot 13 (0x622ae0) creates the soldier (0x750 bytes, ctor 0x761900) with a pointer to D kept at
  **soldier+0x6d8**. Every reader of D was found through that pointer (a scan of the code for
  `mov r, [x+0x6d8]` followed by `[r+off]`):

  | field | read at | what it is |
  |---|---|---|
  | 0 style | 60 places | comparisons with 2, 4, 5, 6, 7 (heavy thug, sneaky SWAT, shield, dog, street cop) |
  | 3 skill | 0x60fd40 | one test `== eVeteran` (what it switches was not read) |
  | **4** | 0x557ae0, 0x719b00, 0x8b84b0 | **accuracy, per cent**: `1 - field4 / 100` is the miss share (0x557b17, 0x719ce1); also two ranges of the tuning table |
  | 5 | 0x5a85a0, 0x622b57 | two ranges of globals 0xd18fa4.. and one of the tuning table, read at field 5 per cent. ASSUMPTION: how fast the aim settles |
  | 6 | 0x6c81a0 | not read |
  | **7** | 0x8fbac0 | **health**: the function starts with the option `GodActors` and with `field7 <= 0` (both: invulnerable, 0x6f4890); else a range of the tuning table at field 7 per cent, times a team factor (0x831f00), times field 9 / 10 / 11 / 12 chosen by `[0x156b5f0]` = 0..3 (ASSUMPTION: the difficulty), handed to the actor's virtuals +0x674 and +0x670 |
  | 8 | 0x8fbac0 | a second pair for the actor (virtual +0x67c); -1 = none. Not read further |
  | 9..12 | 0x8fbac0 | the health factor per difficulty. New in Dog Days, 1.0 in every level |
  | 13, 14 | 0x784330 | two more ranges of the tuning table (field 13: scaled by a global when the squad pointer is set) |
  | 15 | 0x7842f0 | returned times a factor of an object of the squad (`+0x5c8`). ASSUMPTION: the sight range (stock 5000, these maps 6000..10000; the squad modifier has `eVIM_Factor_2_0`) - but the AI heisters have 1.0 there |
  | 16, 17 | 0x451f30, 0x4c12e0, 0x590320 | used only while `[soldier+0x6ac]` is set, else a global. Not read further |
  | 21 game type | 0x622ba6.. | the actor is removed when the session's mode is not in the set (bit 1 FA, 2 team, 8 UCC) |

  "A range of the tuning table" = `0x884a70(a, b, t)` = a + (b - a) * t / 100 with a, b from the object at
  `[0x168d7c0]`. Its numbers were not read (it is built at run time), so health 175 is "1.75 times the health
  100 buys", not a number of bullets.

## 2. Stock Dog Days: what makes its police hard

`python tools\kl_map_ai.py stock` (the nine levels, AI heisters not counted as soldiers):

| | soldiers | squads | hit points | health mean | accuracy as used | squads / men NOT in the world at the load | "wiped out" lists | named at the round start | AI heisters |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| F01 | 29 | 14 | 4,060 | 140 | 55 | 14 / 29 | 0 | 8 | 7 |
| F02 | 21 | 6 | 2,575 | 123 | 55 | 5 / 17 | 0 | 13 | 7 |
| F03 | 40 | 17 | 5,095 | 127 | 64 | 7 / 18 | 8 | 10 | 7 |
| F04 | 45 | 24 | 6,080 | 135 | 68 | 18 / 33 | 0 | 11 | 7 |
| F05 | 28 | 13 | 4,330 | 155 | 62 | 11 / 25 | 0 | 4 | 7 |
| F06 | 36 | 11 | 4,320 | 120 | 55 | 10 / 32 | 0 | 11 | 7 |
| F07 | 34 | 20 | 4,640 | 137 | 62 | 16 / 29 | 0 | 8 | 7 |
| F08 | 40 | 13 | 6,120 | 153 | 55 | 11 / 35 | 0 | 3 | 7 |
| F09 | 43 | 19 | 3,746 | 87 | 81 | 6 / 19 | 1 | 7 | 7 |

- **Numbers and health, not aim.** 138 of the 316 soldiers are one row: `eArmy eCustom`, accuracy 50 (55 as
  used), health 175, a rifle (kl_arms' census: 137 x `Rifle_AK74` as a primary in the nine levels). Street cops: 55 / 100, SMG. Guards: `eGuard eRegular`,
  55 / 65. The rival gangs of F03 / F04 / F05 / F07 / F09 are the accurate ones (75..80 -> 82..88) and are
  given health 10..30 where they are meant to fall at once.
- **Waves.** 5..18 squads a level have `ZSquadScript` field 3 = 0: their men are not in the world until one
  of their routs is named (seen live on Retomoto: "they spawn in"). They are named by boxes on the crew's way,
  by `TriggerDelay2` timers (F01: 44 timers; 20 s in 15 of them, 10 s in 5) and by the round's start: the
  `AIMonitor`'s field 2 names 3..13 objects, mostly timers.
- **Reinforcement chains.** F03: each of its three first SWAT squads names `Gate_RandomRespawnSWAT` in its
  field 8, which picks one of four reinforcement squads by a `RandomTrigger`; each reinforcement squad names
  the next in ITS field 8, the fourth names the first (a ring). Whether a squad that is named again after its
  men are dead comes back was NOT established (the node's name says "respawn"; the level has 12 men in those
  four squads and nothing else that would make more).
- **The escape.** Boxes before the van send every squad to places round it (F07: 44 s + 18 s after the "run"
  boxes) and the van carries a `FakeTarget` of team `Mercenary`, so police who see it shoot it (re/retomoto_ai.md
  1.3). The monitor's lists for "vehicle n was called" (section 5, part 4) are empty in all nine levels.
- 0 of the nine levels has a `VehicleExitBehaviourRout`: stock police arrive in animated cars, by cut scenes.

## 3. The four maps today (`python tools\kl_map_ai.py table <work>\build\z_maps\M02`)

| | M01 Hot Coffee | M02 Late Night Opening | M03 Withdrawal | M06 A Walk in the Park |
|---|---|---|---|---|
| soldiers / squads | 13 / 10 | 12 / 6 | 15 / 8 | 14 / 9 |
| civilians | 3 | 3 | 5 | 0 |
| hit points (health mean) | 1,325 (102) | 1,220 (102) | 1,500 (100) | 1,400 (100) |
| accuracy as used | 100 | 100 | 100 | 76 (55..96) |
| skill names | 13 eCustom | 12 eCustom | 15 eCustom | 8 eCustom, 5 eVeteran, 1 eRegular |
| weapons (kl_arms, seed 2026) | SMG 6, pistol 3, rifle 2, shotgun 2 | rifle 5, SMG 4, pistol 2, shotgun 1 | rifle 9, pistol 3, SMG 2, shotgun 1 | SMG 9, rifle 4, shotgun 1 |
| in the world at the load | all | all | all | all |
| unleashed squads | 3 | 4 | 6 | 2 |
| who arrives later | 4 sit in two parked cars and get out when the diner is alarmed | 4 police in one car: 80 s after the first step into the mall, or when 2 guard squads are alarmed, or at a box | 9 police in four cars, by boxes and 2..8 s timers | nobody; after the first shot the two gangs hunt after 45 / 50 s |
| at the escape | three exit boxes send seven squads hunting | a box sends the car and the transporter guards | a box sends the escape squad's car | nothing |
| "wiped out" lists / round-start names / vehicle-called names | 0 / 1 (the briefing timer) / 0 | 0 / 1 / 0 | 0 / 1 / 0 | 0 / 1 / 0 |
| distance of the squads from the START row | 81..109 m | 20..55 m | 57..106 m | 46..86 m |

Dead Men's own rows, from its levels (17 fields; the converter carries fields 0..8 as they are and Dead
Men 9 / 10 / 11 to Dog Days 13 / 14 / 15): guards and police `eCustom` (100, 100, 10, **health 100**, 50, 25,
65, sight 8,000..10,000); M06's thugs (75..87, 90, 10, 100, ...). Against the preset table these are above
`eElite` in accuracy and aim and about `eVeteran` in fields 13 / 14. Dead Men's weapons: USP, P90, M4A1,
MP5 (re/maps.md 14.3).

What starts each rout of each squad, and what each squad's event lists name, is in the tool's output
(`rout <name> <- ...`). Dead Men's maps use `ZSquadScript` lists 4, 11 and 12 (alarm events: own hunt, the
neighbours' flank routs, a reinforcement counter) and never list 8.

## 4. FOUND: the police that come by car lose their exit rout

- Dead Men ends a squad's drive with `VehicleExitBehaviourRout` on a node `VehicleExitBehaviour`, named by the
  drive (`VehicleMoveBehaviourRout` field 4) or by alarm lists. Its field 0 is what the squad does next.

  | map | squad (men) | the rout started |
  |---|---|---|
  | M01 | `AI_Enemies!FrontMall_01` (2), `FrontMall_02` (2) | their `FlankingBehaviour` (which nothing else names) |
  | M02 | `AIEnemies!PoliceSwats` (4) | `FlankingBehaviour` + `HuntTimer` (30 s -> `HuntBehaviour`); neither is named by anything else |
  | M03 | `EscSquad` (2), `ArrivingCops_Squad_01` (2), `ArrivingCops_Squad_02` (2), `ParkingLotSWAT_01` (3) | `HuntBehaviour` / `HuntBehaviour` / `FlankingBehaviour` + `Triggers!ArrivingCopsHunt_Timer` / `FlankingBehaviour` |
  | M06 | none (helicopters) | |

- `kl_convert.convert_level` removes the controller on every map (seen: Dead Men's level has it, the built
  level's node of the same path has no controller; M02's log counts 36 `ctrl_removed`): the class is registered by Dog Days (`ZVehicleExitBehaviourRout`, fields refs, bool, ?, bool), but its
  field 2 has type handler 54 (loader 0x43e060), which no stock level stores, so `kl_rtp` has no shape for it
  (`kind` None) and `conv.object` gives up. The node stays, without a controller; what names it names nothing.
- Read: 0x43e060 is byte for byte the code of the known flag-set loaders 0x44e940 and 0x7f30b0 (the same
  call of the reader 0x7cc520), with the enum info 0xcfdedc pushed = `EBoneType`, the same enum with the same
  26 options as Dead Men's field (0xa58a18). So the field is a `k` token in both games; all seven objects
  store it with 0 names.
- What a squad that sits in a car does when the rout that should get it out does not exist: NOT KNOWN. The
  owner did not report police sitting in a car; M02's police are `eUnleashed` and may act by themselves.

Two repairs in `kl_map_ai` (part 0, with the waves):

| | what | risk |
|---|---|---|
| **by-pass** (default) | every list that names the empty node also names what its rout started (M01 5 + 9 lists, M02 1, M03 1 each). Values only | the orders arrive; whether the men leave the car without the rout is not known |
| `--car-exit` | the controller is put back, token for token from Dead Men's level (`<work>\build\t_ai\car_exit\`) | code no stock Dog Days level runs. `kl_fa.check` calls the object a CRASH ("does not fit its class") because of the unknown field type: that verdict is what the reading above contradicts, and a live load decides |

The right place for the fix is the converter: section 10.

## 5. What `kl_map_ai apply` does

    python tools\kl_map_ai.py apply <finished build folder> <out folder> [--no-strength] [--no-waves] [--no-chains]
                                    [--no-escape] [--presets] [--health=1.5] [--car-exit]
    python tools\kl_map_ai.py all <z_maps> <out> [M02 ...]      apply + check + kl_maps.audit
    python tools\kl_map_ai.py check <before> <after>            the before / after table

It opens the finished archive (`kl_graft.open_built`), requires the `.prp` to re-serialise byte for byte,
edits, fits every object to its class again, refuses a list entry that names nothing, runs `kl_arms.check`,
writes the archive with the new `.prp` and copies every other file. `steps.json` gets the step ("map_ai":
[".prp"]) after the member CRCs proved that nothing else differs. A map's plan is a table in the tool
(`PLANS`); a name the build does not have stops the run.

**Part 1, strength.** The class of the weapon an actor carries sets floors:

| class | accuracy / aim floor = the preset of | health floor | Retomoto's name for the class (not used here) |
|---|---|---:|---|
| pistol, revolver | eRegular (55 used / 50) | 100 | eAmateur |
| SMG | eVeteran (66 / 60) | 125 | eRegular |
| shotgun | eVeteran | 150 | eRegular |
| rifle | eElite (99 / 90) | 175 | eVeteran |
| MG | eElite | 200 | eVeteran |
| sniper | eElite | 100 | eElite |

Health 100 and 175 are stock's street cop and SWAT; 125 / 150 / 200 are GUESSES. A row below its accuracy
floor that has a skill name becomes `eCustom` with that name's preset numbers kept (M06: one `eRegular`).
`arms` re-arms whole squads from `kl_arms.POOLS` (template by seed and path, the animation set must have the
weapon's folder): the squads that ARRIVE get rifles, as stock's police have.

**Part 2, waves.** Timers, counters, attitudes and the round-start list, per map (section 6).

**Part 3, chains.** `ZSquadScript` field 8 of a squad names routs of its neighbours and, where the map has
one, its reinforcement trigger. ASSUMPTION, as on Retomoto and still not seen live: the list is sent when the
squad is wiped out (stock: 653 entries of the twelve story levels' field 8 name a `TriggerCounter`;
re/retomoto_ai.md 1.3 has their names, `TC_AllDead`).
Retomoto's chains send neighbours a line BACK; these maps' squads are one or two men with a hunt or a flank
rout and no second line, so here the neighbours come TO the fight and the police are called.

**Part 4, the escape.** `OnlineEscVehicleMonitor` field 4. Read: `ZOnlineExitLevelTrigger` slot 34 (0x6c3d50)
picks a vehicle (its fields 2..5) and calls 0x6276e0 with 1..4; that function sends the monitor's list at
this+0x48 / +0x4c / +0x50 / +0x54, and the monitor's reflection records put fields 4..7 at those offsets. A
Dead Men map has one vehicle, in field 2 (`kl_fa.exit_trigger`) -> field 4 is sent when the car, van or
helicopter is CALLED. The list names every squad's hunt (or flank) rout and the map's reinforcement trigger.
No stock level fills fields 4..7: the send loop is the same as for the lists stock fills, but it has never
run with entries. `--no-escape` leaves it empty.

## 6. Per map: what changed (`<work>\build\t_ai\<map>\map_ai.txt` has every line, `map_ai_check.txt` the table)

| | M01 | M02 | M03 | M06 |
|---|---|---|---|---|
| hit points | 1,325 -> 1,875 | 1,220 -> 1,775 | 1,500 -> 2,275 | 1,400 -> 1,975 |
| health mean | 102 -> 144 | 102 -> 148 | 100 -> 152 | 100 -> 141 |
| accuracy as used | 100 | 100 | 100 | 76.4 -> 80.1 (four riflemen 82..96 -> 99, one eRegular 55 -> 66) |
| weapons | `FrontMall_01 / _02`: 3 SMGs -> rifles (rifle 2 -> 5) | `TransporterGuards`: SMG -> rifle (rifle 5 -> 6) | - | - |
| unleashed | + `BossFlank_01`, `BossFlank_02` (the two pistol men of the back room: "guys with pistols will rush you") | + `3rdFloor_Guard_02`, `JewelShop_Guards` | + `BankMainSquad_01`, `BankMainSquad_03` | - |
| timers / counters | - | `ReinforcementsTimer` 80 -> 45 s, `ReinforcementsCounter` 2 -> 1, `PoliceSwats\HuntTimer` 30 -> 8 s | `CivilWar_Counter` 4 -> 2 | `US_Boss_Timer` 45 -> 20 s |
| round start | - | + `ReinforcementsTimer`: the police car comes 45 s after GO whatever the crew does | - | - |
| "wiped out" lists | 9 squads | 6 (each guard squad also calls the police: the counter) | 8 (the hall squads call `Parkinglot_SWAT_Timer` / `ArrivingCops_Timer`) | 8 |
| vehicle called -> | 10 routs | the police car's gate + 6 routs | `ArrivingCops_Timer` + 8 routs | 7 routs |
| car orders by-passed | 2 squads (14 lists) | 1 (1 list) | 4 (4 lists) | - |
| unleash times after | parked-car men get their flank rout with the alarm (was: never) | police: GO + 45 s, or the first guard squad wiped out, or one squad alarmed; out of the car flank at once and hunt 8 s later (was: no order at all) | as before + a hall squad down calls the next car | the American side hunts 20 s after the first shot |

M06 gets the least, as the owner expected: no squad re-armed, nobody unleashed, the Japanese timer (50 s)
untouched because its list also flies the boss out.

The `--presets` run, computed from the preset table (not built): every armed soldier's accuracy as used
becomes 38.5 (pistol), 55 (SMG, shotgun) or 66 (rifle) - from 100 on M01 / M02 / M03 and from 55..96 on M06.

## 7. What is missing where a map has too few people

No entity was added, so against stock:

| | has | stock has | what would close it |
|---|---|---|---|
| soldiers | 12..15 | 21..45 | more squads = new entities (copies of the map's own squads with their boxes: `kl_scene.graft` can do it; places on the map's mesh must be chosen per map) |
| hit points | 1,775..2,275 after | 2,575..6,120 | `--health=1.5` would give 2,660..3,410 (computed from the floors, not built) without an entity: every man soaks more. GUESS that this is less fun than more men, so it is off |
| squads that arrive | 0 with field 3 = 0; 1 car (M02), 4 cars (M03), 2 parked cars (M01) | 5..18 squads | field 3 = 0 on squads that a box or chain starts would make them "spawn in" - not done: nobody has seen it on a Dead Men squad, and a squad that nothing names would never appear |
| timers to stage waves | M02 1, M06 2, M03 only 2..8 s ones, M01 none | 4..13 named at the round start | a spare timer per map = a new entity |
| the escape | routs named at the call (this tool) | squads walk to places round the van; the van is a target | no `FakeTarget` on a Dead Men car or helicopter (a controller, not a value); no positions round the vehicle |
| AI heisters | 0 | 7 | the bots workflow (tools/kl_fa_bots.py, another session) |
| respawn | none | not established for stock either (section 2) | - |

## 8. Budget

Nothing was added to any block. Bytes of the members that are read into one block each, before = after:

| | .prm | .ANM | .fxc | .TEX | F01_Main.WAV |
|---|---:|---:|---:|---:|---:|
| M01 | 55,088,000 | 22,061,764 | 17,760,648 | 234,505,616 | 21,722,704 |
| M02 | 54,619,216 | 22,202,472 | 17,760,648 | 216,130,816 | 22,527,568 |
| M03 | 60,469,040 | 22,202,616 | 17,760,648 | 217,786,368 | 22,716,752 |
| M06 | 49,585,744 | 21,642,576 | 17,760,648 | 204,607,072 | 21,775,744 |

The `.prp` grows by 815 / 584 / 728 / 466 bytes (strings of the new list entries); no chunk, no texture, no
sound, no entity. The `.fxc` is the 17.8 MB one of the source builds (the fxc cut is another agent's step).

## 9. Tests run

    python tools\kl_map_ai.py all <work>\build\z_maps <work>\build\t_ai
        M01 M02 M03 M06: apply ok; steps.json: only .prp differs; kl_maps.audit PASS
        (bad 0; known 1 / 6 / 0 / 6 = the materials without a shader of re/maps.md 14.2)
    python tools\kl_maps.py audit <work>\build\t_ai\M02            RESULT: PASS (0 findings that must be 0, 6 known)
    python tools\kl_map_ai.py all <work>\build\z_maps <work>\build\t_ai\car_exit M01 M02 M03 --car-exit
        7 controllers put back; kl_maps.audit PASS with the field type taught in memory (kl_map_ai.teach_schema)
    python tools\kl_maps.py audit <work>\build\t_ai\car_exit\M02   RESULT: FAIL (1): kl_fa.check CRASH 'layout' on the
        restored controller - expected, the stock schema has no shape for its field 2 (section 4)
    python tools\kl_map_ai.py stock                                the table of section 2
    python tools\kl_map_ai.py table <build>                        sections 3 and 6

## 10. Changes outside my files, for the lead

1. **`tools/kl_rtp.py` / `re/kl2.json`: type handler 54 (loader 0x43e060) is kind `k`.** Generally: a type
   handler never seen in a stock level whose loader is the flag-set stub (`push <enum info>; ... call
   0x7cc520`, as 0x44e940 / 0x7f30b0) can be given kind `k` from the code. With that, `kl_convert` carries
   `VehicleExitBehaviourRout` (same four fields in both games) and M01 / M02 / M03 keep their seven exit routs
   without any by-pass. Until a live run has shown a Dead Men car squad getting out, keep it behind a switch.
2. `tools/kl_arms.py` (session kl-merge-b6, changed while this was written): (a) `SKILL_LEVELS` must stay
   ('M09_A', 'M09_B'): on the Fragile Alliance maps its rows would cut accuracy 100 to 55 (section 0.3).
   (b) Its row 'sharp' (`eRegular` 85 82 82 150, "higher calibre = more technical") is NOT sharper than 'swat':
   the name `eRegular` writes 50, 50, 10 over the first three numbers (0x46e410), so a 'sharp' man shoots like
   SWAT (55 as used) and has LESS health (150 against 175). To be sharp the row must be `eCustom` (e.g. 85 82
   10 175 ...). The same holds for stock's own 28 `eArmy eRegular` soldiers: their 85 / 82 / 82 are never used.
   (c) Its comment "what each float does was NOT read in the exe" is answered by section 1: the fourth IS
   health, the first accuracy; field 15 (Dead Men's 1000 on the tower guards, stock 5000) is ASSUMED to be the
   sight range (section 1).
3. `re/pairings.md`: `ZSoldierRout` DD13 / DD14 <- DM9 / DM10 is now proved by code (section 1), no longer
   "medium (values only)".
4. `tools/kl_fa_street.py` / `kl_fa_author.py` (Retomoto): the same monitor list (field 4, "vehicle called") is
   free there too; and health 175 on the campaign police it keeps would match F07's own.
5. Order with the other steps on a finished build: run this AFTER a step that changes what actors carry (the
   floors follow the weapon in `ZFFActor[1]`; a template that is in no `kl_arms` pool gets no floor).

## 11. Not known, and the live test order (one variable a run; ask the session that holds the game)

Not known: whether list 8 is "wiped out"; whether the monitor's field 4 fires as read; what a seated squad
does with a flank rout (by-pass) and whether Dog Days' exit rout works (`--car-exit`); whether naming a
timer or a gate twice sends a car twice (Dead Men itself names M02's car from a box AND through the gate, and
M03's `ArrivingCops_Timer` from five boxes); what `eUnleashed` does to a guard who has no hunt rout; the
real size of health 175 against 100; what field 8 of the row and the `eVeteran` test do.

| run | build | look at | if not |
|---|---|---|---|
| A1 | `t_ai\M02` | the police car: does it come about 45 s after GO, do the four get out, flank, hunt | they stay seated -> A2 |
| A2 | `t_ai\car_exit\M02` | the same. A fault at the load = the field type is not what was read -> drop `--car-exit` and section 10.1 | - |
| A3 | `t_ai\M02` | kill the two 2nd-floor guards: do the others come, does the car come at once | nothing -> list 8 is not "wiped out": `--no-chains` |
| A4 | `t_ai\M02` | step into the exit box: does everybody alive come | nothing -> the monitor list does not fire; a fault there -> `--no-escape` |
| A5 | `t_ai\M02` | do riflemen take visibly more hits than pistol guards | too spongy -> lower `STRENGTH`; too soft -> `--health=1.5` |
| A6 | `t_ai\M03`, `t_ai\M01`, `t_ai\M06` | one round each, the same four things | per-map tables in `PLANS` |

## 12. After the review (2026-10-10, `re/map_tune_review.md`): what was wrong, what is changed

OFFLINE as everything above. The builds of sections 6 and 9 (`t_ai\<map>`, `t_maps\<map>`) are the OLD ones and
carry the three defects; the corrected ones are `<work>\build\t_ai2\<map>` (this step alone) and
`<work>\build\t_maps2\<map>` (guns -> escape -> ai). Sections 5 and 6 above describe the old plans where they
differ from this table.

| | defect | cause | now |
|---|---|---|---|
| F1 | all four maps: the 33 entries of the 'vehicle called' list were written without `ROOT\` | `rooted()` took the form 'the controller's lists have in this level' by majority and counted an all-empty controller (the monitor) as 0 > 0 = 'without' | `refs()` writes `ROOT\` always; `rooted()` is gone. Census (every reference list of every node and controller): `t_maps2` M01 1,745 / M02 4,117 / M03 3,777 / M06 1,229 entries with `ROOT\`, 1 / 129 / 7 / 0 empty, **0 without** |
| F2 | M03: three 'wiped out' lists and the van call named `Triggers!ArrivingCops_Timer` -> `ArrivingCops_Squad_02\VehicleEnterBehaviour` (a fighting squad sent back into its car) | the plan | the timer is in no list of the plan |
| F3 | M02 `PoliceSwats\HuntBehaviour` (from `TransporterGuards[8]` and the car call), M03 the hunt routs of `EscSquad`, `ArrivingCops_Squad_01 / _02`, `ParkingLotSWAT_01`: orders to a squad that has not driven yet | the plan | no list of the plan orders a car squad; M02's `TransporterGuards[8]` names `Triggers!ReinforcementsCounter` (calls the car through its gate), M03's chains and van call order the six men on foot only |
| new | M03 `Triggers!Parkinglot_SWAT_Timer` (the review took it for harmless) names the EXIT nodes of `ArrivingCops_Squad_01` and `ParkingLotSWAT_01` - with the by-pass their hunt / flank routs | found by the new check | not named; `LoadingDockSquad_01\FlankingBehaviour` is named directly |

The check that keeps it so: `kl_map_ai.faults(sc)` = (a) an entry of the lists this tool writes that names
nothing, resolved AS WRITTEN (the old test added the prefix first, which is why F1 passed); (b) `bare()`: any
non-empty reference-list entry of the WHOLE level without `ROOT\`; (c) `order_faults()`: every squad's list 8
and the monitor's lists 4..7 are followed through timers, counters and random triggers (not through a
`GatePath`) and must reach neither a `VehicleEnter` / `VehicleMove` rout (F2) nor anything inside another squad
that has one (F3). `apply()` refuses to write a level with a finding; `kl_map_tune`'s checker `kl_map_ai` runs
it on the written folder. On the old builds it finds 20 / 16 / 42 / 14 faults (`t_maps\M01 M02 M03 M06`), on
`z_maps` and the new builds 0.

What the plans give now (the rest of section 6 is unchanged: health, rifles, timers, unleashed squads):

| | M01 | M02 | M03 | M06 |
|---|---|---|---|---|
| 'wiped out' lists | 9, as before | 6; `TransporterGuards` -> the police are called | 8; each names the loading dock's flank and / or the hall squads' hunt | 8, as before |
| vehicle called -> | 10 routs, as before (the parked-car squads of M01 have no drive) | the police car's gate + 5 routs (not the police's hunt) | 4 routs: `LoadingDockSquad_01` flank, `BankMainSquad_01 / _02 / _03` hunt | 7 routs, as before |

The price on M03: the nine police in four cars get no extra order at all; what moves them is what Dead Men
gave them (boxes, their drives' end lists with the by-pass). 'Harder' on M03 is health 175 + two unleashed
hall guards + the six on foot coming to the fight.

`map_ai.json` now has `plan` = an id of the map's plan (`kl_map_ai.plan_id`); `kl_map_tune` compares a tuned
map with the ai step alone only when both were made with the same plan.

## 13. What a hit costs (2026-10-10, agent p-balance; the whole of it is `re/balance.md`)

OFFLINE as everything above. The owner after playing the four maps with AI heisters: "they dont have much health
when i shoot them but when they shoot me i have a llot of health not proportional and the coppers dont seem too
intimidating it should be all the same kinda risk". Read in kl2.exe for that; three lines of section 1 are
answered and one is corrected:

| section 1 said | now |
|---|---|
| field 7: 'a range of the tuning table ... its numbers were not read ... health 175 is 1.75 times the health 100 buys, not a number of bullets' | the range is 0..100 (tuning +0x364 / +0x368, from the constructor 0x524050): **field 7 IS hit points**, times the difficulty row's factor |
| 'a team factor (0x831f00)' and '`[0x156b5f0]` = 0..3 (ASSUMPTION: the difficulty)' | it is the option 'Difficulty' (0x472d50). 0x831f00 picks a row of nine floats: Arcade is not 'online', so it takes the STORY rows: NPC health x **0.5 / 0.9 / 1.15 / 1.3**; the 9 / 6 / 3 / 1.5 of the other column are for the campaign's buddy (`[gamedata+0x4cf0]`) only |
| field 8: 'a second pair for the actor; not read further' | **regeneration**: seconds before health comes back and seconds until it is whole, both 15 .. 1 at field 8 per cent (tuning +0x3c8..+0x3d4, 0x8fbbff -> 0x8f9bf0); -1 = none. SWAT and the AI heisters have 50 = 8 s / 8 s |
| the soldier rows decide how hard a map is | in Arcade they are the smaller half. Every hit is also multiplied by one of six numbers by who shoots whom, per ARCADE LEVEL (= 1 + the rounds escaped in this session): on level 1 police -> you 0.1, you -> police 2.0, police -> AI heister 0.01, AI heister -> police 3.0 |

So on level 1 - every test round so far - a policeman of these maps needs about 90 body hits to kill the player
(550 health that comes back within 8 s) and the player 2 for him; stock Subway is the same 91 / 2. Accuracy 100
did not make the Dead Men guards dangerous because their bullets are worth a tenth.

`python tools\kl_map_ai.py balance <build folder | stock level> [--dist=10] [--diff=1]` prints the hits to kill
between the player, the police and the AI heisters on five stock Arcade levels and under the three rows of
`klhook/klbalance.c`'s dial (`[Balance] Risk=1..3`, a hook part, OFF by default, not wired). The tool's tables
`ARCADE` / `RISK` mirror that file's `klr_code` / `klr_dial`.

**No change to the level step.** `apply()`, the plans and the builds (`t_ai2`, `t_maps2`, `u_maps`) are as they
were: the lopsidedness is run-time data, and health 100..175 by weapon class is right for a table of 1.0 (2..3
rifle hits a man). The one level-side number the dial may make too hard is accuracy 100 on M01 / M02 / M03's
PISTOL carriers (an NPC pistol bullet is 125..295 at 10 m, a rifle's 47..80): if live check B6 of re/balance.md
says so, `strength()` needs a cap for the pistol class (stock's guard row is 55), not a floor.
