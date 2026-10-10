# Review of the bot builds on the tuned maps (`<work>\build\u_maps\M01 M02 M03 M06`)

2026-10-10, agent u-verify (adversarial review; claim: gun looks + repaired escape camera + tougher enemies with
the defects F1..F3 of re/map_tune_review.md fixed + a seven-bot AI heister squad, made by
`kl_fa_bots.py build <work>\build\t_maps2\Mxx`). OFFLINE: the game was not started by me, nothing was installed,
nothing was written into the Dog Days folder. The four build folders were not changed (archive sha1 before and
after: `4ea0322d59cf`, `0ef2e7e2d091`, `284b1f8a116d`, `d3a2e83a68b5`); every checker that writes into its folder
ran on copies (`<scratch>\uv\Mxx`, member for member equal to the builds). NOTHING HERE RAN IN THE GAME.
Status words: **seen** = read in the files by me, **not established**, **ASSUMPTION**.
`u_maps\M01_wait90` (the same build with a 90 s loot wait) was NOT reviewed.

## 0. Verdict

| map | load it? | fix first (files) | watch first (live) |
|---|---|---|---|
| M01 diner | yes - every checker and every test of mine passes | nothing | when the bots call the vehicle (they enter `Triggers!CallExitVehicle_02` after their loot wait: start 10 s + walk + at most 20 s); two loot people (FBI agents, the Senator) stand INSIDE an exit box - the route avoids them, the bots' own loot tactic may not |
| M02 Late Night Opening | yes | nothing; R1 below (the police car's drive is named from three places) is the one order left that I would not sign | same call as M01 (`Triggers!ExitTrigger_01`); the four police in the car park (F4 of the first review, unchanged) |
| M03 the bank | yes | nothing | the bots never enter the level exit box and never board through the tactic: they end in the `AllyEscapeBox` in the yard, 1,661 from the vehicle (the tool's own 8 NOTEs). Only the human calls the car |
| M06 A Walk in the Park | yes | nothing | stage 2 is skipped (no EXITS_BANK place on the mesh part); boarding through the `AllyEscapeBox` |

Nothing I tried refuted a claim about the FILES. What is left is behaviour nobody has seen (section 7) and one
tool gap the lead will trip over: **`kl_map_tune.py check` on a `u_maps` folder exits 1** (section 1).

The points asked for:

| asked | result |
|---|---|
| every checker | all pass (section 1); `kl_map_tune.py check` FAILS two of its eleven lines, both because it does not know the bot step |
| reference lists without `ROOT\` or that do not resolve | **0 / 0 / 0 / 0** in every list of every node and controller, and in the raw key table (section 2). Control: the same census finds the 7 entries of F1 in `t_maps\M02` |
| F2 really gone | yes: `Triggers!ArrivingCops_Timer` is named by exactly the five objects that name it in `z_maps` and in Dead Men (section 3) |
| F3 really gone | yes for every case the first review named; the by-pass entries that are left sit where Dead Men had the exit rout (section 3). One residue, R1 |
| the squad's references after the other steps | 0 of the squad's 154 / 336 / 217 / 147 list entries and 7 weapon references name anything but exactly one node; the only field of an old node that changed is `Gameplay!AIMonitor` `AIMonitor[2]` (+ the start timer) |
| the other steps' references after the renumbering | .oct / .rmi / .rmc ids, list pool, room pairs, .prm -> .oct offsets, KLGuns.ini, KLWardrobe.ini: all name what they named (sections 4, 5) |
| no large member grew beyond the gun step | .prm, .TEX, .MAT, .ANM, .fxc, .WAV are byte-equal in size to `t_maps2`; the bot step changes 4 bytes in each model root that has an .oct record and nothing else of the .prm (section 6) |
| side files | 20 beside the archive, none missing, 19 equal by sha1 to `z_maps`, new: `KLGuns.ini`; all 20 equal to `t_maps2` |

## 1. The checkers, run by me on the copies

| | M01 | M02 | M03 | M06 |
|---|---|---|---|---|
| `kl_fa_bots.py check` | PASS (0 FAIL, 0 NOTE), exit 0 | PASS (0, 0), exit 0 | PASS (0 FAIL, 8 NOTE), exit 0 | PASS (0 FAIL, 1 NOTE), exit 0 |
| `kl_fa_bots.py diff t_maps2 -> copy` | only the squad was added, exit 0 | same | same | same |
| `kl_map_guns.py check` | problems: 0 | problems: 0 | problems: 0 | problems: 0 |
| `kl_maps.py audit` | PASS (0; 1 known) | PASS (0; 6 known) | PASS (0; 0 known) | PASS (0; 6 known) |
| `kl_impact.py` (bone ids, chunk limit, surface table) | problems: 0 | problems: 0 | problems: 0 | problems: 0 |
| `kl_map_escape.py check` | 0 faults | 0 faults | 0 faults | 0 faults |
| `kl_maps.py preflight` | CRASH 0, RISK 0 | CRASH 0, RISK 3 | CRASH 0, RISK 0 | CRASH 0, RISK 2 |
| `debug\check.py` | 0 layouts Dog Days never stores | 0 | 0 | 0 |
| `kl_map_tune.py check` | **FAIL: kl_map_ai, members**, exit 1 | **FAIL**, same two | **FAIL**, same two | **FAIL**, same two |

The RISK lines are the ones `z_maps` already has (ZEnvSampler / SoundSpline on M02, SoundSpline /
SoundVolumetricRandom on M06); M02 was played with them.

**G1, tool gap, not a defect of the builds.** `kl_map_tune.py check <u_maps\Mxx>` reports
`members ... NOT EXPECTED: .buf .rmc .rmi` and `kl_map_ai ... totals DIFFER from the ai step alone`. Both are the
bot step: I compared `kl_map_ai.measure` of `t_maps2` and of the copy, and the only totals that differ are
`AI heisters` 0 -> 7, `named at the round start` +1 and one more timer of 10.0 s (the same three lines on all four
maps); soldiers, hit points and accuracy are equal. A loop that trusts this exit code will refuse four good
builds. `kl_map_tune.checks()` should read the `bots` step of `steps.json` (expected members + .buf .rmc .rmi,
and the totals compared without the three squad lines).

**G2, for information.** The audit's member test passes because `kl_fa_bots.apply()` rewrites `steps.json`
(`final` = the members it has just written). That is the step certifying itself; sections 4 to 6 are the
independent test of those members.

## 2. Census of every reference in the .prp

`uv_refs.py` (my own walk of the tokens: every `04 n` + `0c` list, every single `0c`, every `0f` list, of every
node's properties and every controller; no function of `kl_fa_bots`, `kl_map_ai` or `kl_map_guns`). A list entry
counts as a fault when it is not empty and does not begin `ROOT\` (whether or not it would resolve with the
prefix added), or when it names no node, or more than one.

| u_maps | M01 | M02 | M03 | M06 |
|---|---:|---:|---:|---:|
| nodes (`z_maps` -> `u_maps`) | 15,000 -> 15,148 | 21,935 -> 22,146 | 19,828 -> 19,991 | 15,600 -> 15,763 |
| list entries with `ROOT\` that name exactly one node | 1,900 | 4,454 | 3,995 | 1,377 |
| list entries that are empty strings (as in `z_maps`) | 1 | 129 | 7 | 0 |
| list entries WITHOUT `ROOT\` | **0** | **0** | **0** | **0** |
| list entries that name no node / several | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| single references with `ROOT\`, one node each | 1,717 | 2,209 | 2,417 | 1,861 |
| single strings that are a scene path from the root without the prefix | 0 | 0 | 0 | 0 |
| key table: strings that begin `ROOT\` / name no node / name several | 1,581 / 0 / 0 | 4,121 / 0 / 0 | 3,310 / 0 / 0 | 1,242 / 0 / 0 |

The list counts of `t_maps2` agree with re/map_ai.md's own census (1,745 / 4,117 / 3,777 / 1,229 + the squad's
entries). Control (`uv_f23.py`): on `t_maps\M02`, the build of the first review, the same walk finds the 7
entries without `ROOT\`. **F1 is gone.**

Old nodes, `t_maps2` against `u_maps`, token for token with the strings spelled out: the first 15,000 / 21,935 /
19,828 / 15,600 paths and classes are equal, the scene property block is equal, and **one** field differs:
`Gameplay!AIMonitor` `AIMonitor[2]` gained `ROOT\Gameplay!merc_bot_squad!Timer_start_bots`. No path of a new
node is also the path of another node.

## 3. F2 and F3

`uv_f23.py`, `uv_who.py`: every list entry `u_maps` has and `z_maps` has not (24 on M02, 30 on M03, without the
squad's own), what it reaches through timers and counters, and who names every rout of every squad that has a
vehicle rout - in `u_maps`, in `z_maps` and in Dead Men's own level.

**F2 (M03), gone.** `Triggers!ArrivingCops_Timer` is named by `Triggers!Respawn_Trigger`,
`Triggers!CivilWar_Counter`, `Triggers!DeliveryCar_01 / _02 / _03_Trigger` - the same five in `u_maps`, `z_maps`
and Dead Men. No `ZSquadScript[8]` and no monitor list names it. No new entry of any of the four maps reaches a
`VehicleEnterBehaviourRout`, directly or through a timer / counter.

**F3, gone as described.**
- M02 `AIEnemies!PoliceSwats\HuntBehaviour`: named only by `PoliceSwats\HuntTimer`, and that only by the squad's
  own `VehicleMoveBehaviourRout[4]` (the drive's end list). `TransporterGuards` `ZSquadScript[8]` names
  `Triggers!ReinforcementsCounter` instead; the monitor's field 4 names the drive (`Gate\Way#01`) and five routs
  of squads on foot.
- M03 `AI_Enemies!EscSquad\HuntBehaviour`: only from `EscSquad\VehicleMoveBehaviour[4]`.
  `ArrivingCops_Squad_01\HuntBehaviour` and `ParkingLotSWAT_01\FlankingBehaviour`: new, from
  `Triggers!Parkinglot_SWAT_Timer` - the timer that names the two squads' (lost) `VehicleExitBehaviour` in Dead
  Men, and which only Dead Men's own four boxes name (`Respawn_Trigger`, `Balcony_SWAT_Trigger`,
  `Parkinglot_SWAT_Trigger_01 / _02`), no list of the plan. `ArrivingCops_Squad_02\FlankingBehaviour` and
  `Triggers!ArrivingCopsHunt_Timer`: new, in that squad's `VehicleEnterBehaviourRout[0]`, beside its lost
  `VehicleExitBehaviour` - again where Dead Men had the exit. So each order to a car squad is given at the moment
  Dead Men told it to get out. The monitor's field 4 on M03 names four routs of squads on foot only.
- M01: `FrontMall_01 / _02` have no enter or move rout (men of parked cars); the many new entries that name their
  hunt / flank routs are not F3 by the first review's definition. Whether these men act is F4 of that review,
  unchanged.

**R1, residue (M02), not established.** `AIEnemies!PoliceSwats\Gate\Way#01` (-> the squad's
`VehicleMoveBehaviour`) is named from three places: `Triggers!ReinforcementsTimer` (45 s after GO),
`Triggers!ReinforcementsCounter`, and NEW the monitor's field 4 (the vehicle is called). A squad that has driven
and is fighting gets its DRIVE rout again when the escape car is called. `kl_map_ai.order_faults` does not follow
a `GatePath`, so its check does not see this. Whether a second drive order does anything to men on foot was not
read; the cautious form is to take `Gate\Way#01` out of the 'vehicle called' list of `PLANS['M02_FA_A']`.

## 4. The two id spaces after the squad was appended

`uv_ids.py`: my own reading of both .gms files (entity table, records, the STORED cluster table - not a
regenerated one -, list pool, room pairs); `kl_octree` only to split .oct / .rmi / .rmc into trees and boxes.
`t_maps2` = before, `u_maps` = after.

| | M01 | M02 | M03 | M06 |
|---|---:|---:|---:|---:|
| entities | 14,999 -> 15,147 | 21,934 -> 22,145 | 19,827 -> 19,990 | 15,599 -> 15,762 |
| cluster blocks (stored table fits the entities: yes) | 2,983 -> 3,039 | 3,574 -> 3,644 | 3,337 -> 3,393 | 3,115 -> 3,171 |
| old entities whose slot moved | 14,827 | 21,712 | 19,612 | 15,383 |
| REF count in the header | 25,880 -> 26,028 | 32,815 -> 33,026 | 30,708 -> 30,871 | 26,480 -> 26,643 |
| .rmi boxes / ids that changed value / ids that name another entity or no room | 21 / 20 / 0 | 45 / 44 / 0 | 61 / 60 / 0 | 11 / 10 / 0 |
| .rmc boxes / changed / wrong | 12 / 11 / 0 | 31 / 30 / 0 | 19 / 18 / 0 | 7 / 6 / 0 |
| .oct room-tree items / name no entity / in a tree of the wrong kind | 3,995 / 0 / 0 | 8,054 / 0 / 0 | 6,664 / 0 / 0 | 4,721 / 0 / 0 |
| room trees whose items (as entities, with bounds) differ, the root's group tree apart | 0 | 0 | 0 | 0 |
| new items of the root's group tree (all new group entities; tree passes `Tree.check`) | 42 | 56 | 42 | 42 |
| .oct collision records (equal one by one) / moved by | 2,142 / +768 | 3,328 / +896 | 3,522 / +720 | 2,018 / +704 |
| .prm model roots / with an .oct record / re-pointed / wrong | 1,389 / 1,111 / 1,111 / 0 | 2,686 / 2,297 / 2,297 / 0 | 2,848 / 2,491 / 2,491 / 0 | 1,375 / 987 / 987 / 0 |
| .prm bytes that differ outside the 4 bytes at +0x1c of a model root | 0 | 0 | 0 | 0 |

Seen in addition, on all four:
- SLOT ids. Every .rmi / .rmc id resolves, through the slots of the STORED cluster table, to the same entity as
  before and that entity is a ZROOM-derived one. Every item of every room tree resolves to the entity it named in
  `t_maps2`, with the same bounds, in a tree of its kind (tree 0 category 1, 1 lights, 3 groups, 4 rooms). The
  list pool (3,542 / 7,628 / 5,981 / 3,679 lists) names the same entities with the same bits as before, every
  element joins a light to a non-light, none names nothing; the room pairs (10 / 32 / 18 / 5) are the same
  entities, the first of each a room.
- REF labels. All distinct, none 0, the highest one below the header count; the old entities keep theirs (class,
  pool group, label, model, name, parent, flags, place equal for every old entity); the new ones take the labels
  above the old header count, none an old entity had. .HVK, .sgd, .hrd (REF labels) and .sgp (room paths) are
  byte-equal to `z_maps`; the surface table (the .buf tail, 30,576 bytes) and the .buf head (up to the first
  name) are byte-equal to `t_maps2`; no raw data block of an old entity changed.
- .prm against .oct, raw: for every model root with a record, `(value & ~1) - 4` in the NEW .oct is the start of
  a record (stale vtable dword 0x01e15844 or Dead Men's 0x017136f8, zero at +0x1c, the copy of origin and scale
  equal to the tree's own), and it is the record the root named before. No record is named by two roots. Every
  tail pair of the .oct names a 64-byte type-8 object of the final .prm.
- Type table: count = entities + dynamic list for every class; the new entities are of classes the level already
  had (ZGROUP, ZFFActor, ZBoxPrimitive). Dynamic list, tag block and navigation mesh are byte-equal.
- Stock comparison: most entities 42,915 and highest REF count 77,599 (L10), most cluster blocks 5,353 (L02),
  heap budgets 96,868 .. 1,338,752. The four builds are inside all of it (budget 584,836 .. 749,524, unchanged by
  the bot step: ASSUMPTION of kl_scene that it need not grow; F07's own figure, with its seven bots, is 403,200).

Not listed in the root's group tree: the 7 `Glazer_Bodyguard_0N` groups and the 7
`040_SquadModifier_tight_defense_van` groups per map (the tool says F07 lists neither; not checked against F07
here).

## 5. KLGuns.ini and KLWardrobe.ini against the final .prm

`uv_guns.py` (the first review's `rv_guns.py`, `z_maps` -> the copy, with the re-pointed model roots set apart):
- `KLGuns.ini` (sha1 equal to `t_maps2`'s): Version 2, 6 guns, HideWord 28, HideBit 8388608. Each `Root`
  (50057.. / 58386.. / 62695.. / 46917..) is a 64-byte model root of the FINAL .prm; its object table has exactly
  Stock + Look parts entries; the stock parts and the Zastava's look 2 are all hidden, look 1 all shown; every
  part is a 64-byte one-bone object with descriptor, vertices and indices, in no other model's table; the
  template's `Ground` entity names the root and no entity is left on the old model. Hide bit: 36 more objects
  than `z_maps` on every map = the hidden parts of the six guns. PROBLEMS 0 on all four.
  (The pairings differ from the first review's builds: the P90 now sits on `SMG_Type05`, not `SMG_UMP`.)
- `KLWardrobe.ini` (sha1 equal on all four maps and to `z_maps`): the 16 `Root` numbers are model roots of the
  final .prm. Of the chunks the `z_maps` level reaches (entities, .prp fields, the 16 wardrobe roots: 34,543 /
  42,868 / 47,162 / 31,394) **0** changed, the .oct offset of model roots apart; the final level reaches no empty
  chunk.
- The bots: `Glazer_Bodyguard_0N\Ground` has model 9341, 9451, 9552, 9655, 9760, 9871, 9982 = the model of
  `Heroes!Hero_02 .. _08\Ground` of the same build (wardrobe characters 2..8), each a model root. Against stock
  F07's own bot the actor differs in that one field (`ZGEOM[4]`); `ZSoldier` and `ZSquadScript` are equal to
  stock field for field. Its weapon reference resolves to one `ZFFItemTemplateWeapon` (`Rifle_zastavam85`), so
  all seven bots carry the gun that is built to show the MP5.

## 6. Members and side files

Bytes, `z_maps` -> `t_maps2` -> `u_maps` (archive directories read by me; 31 members, names and order equal):

| | .prm | chunk table (limit 69,632) | .TEX | .prp | .gms | .buf | .oct |
|---|---|---|---|---|---|---|---|
| M01 | 55,088,000 -> 55,917,968 = | 50,042 -> 50,254 = | 234,505,616 -> 242,724,752 = | 3,110,322 -> 3,141,803 | 216,810 -> 218,908 | 606,480 -> 607,328 | 882,820 -> 883,588 |
| M02 | 54,619,216 -> 55,449,184 = | 58,371 -> 58,583 = | 216,130,816 -> 224,349,952 = | 4,642,396 -> 4,687,257 | 379,535 -> 382,675 | 684,672 -> 685,584 | 1,155,652 -> 1,156,548 |
| M03 | 60,469,040 -> 61,299,008 = | 62,680 -> 62,892 = | 217,786,368 -> 225,939,136 = | 4,260,134 -> 4,294,948 | 330,207 -> 332,418 | 742,224 -> 743,168 | 1,223,388 -> 1,224,108 |
| M06 | 49,585,744 -> 50,415,712 = | 46,902 -> 47,114 = | 204,607,072 -> 212,826,208 = | 3,123,245 -> 3,157,203 | 341,940 -> 344,055 | 585,456 -> 586,352 | 880,428 -> 881,132 |

(`=`: `u_maps` equal to `t_maps2`. For .prp .gms .buf .oct the figures are `t_maps2` -> `u_maps`.)

- 22 members are equal to `z_maps` by size and CRC: .ANM .HVK .SND .fxc .sgd .sgp .hrd .sup .zgf, the nine .LOC,
  the four .xml. .TEX and .MAT are equal to `t_maps2` (and to `t_maps`, the build of the first review). .rmi and
  .rmc keep their size (6,616 / 2,088 on M03).
- The .prm's +829,968 over `z_maps` is the gun step's, to the byte: 442,800 in 212 appended chunks + 16 x 212
  table entries + 383,776 in 2,551 old chunk indices that now hold more bytes (dead indices the gun step reuses;
  none of them is reached by the `z_maps` level, section 5). All 212 appended chunks are reached from the six
  gun roots of `KLGuns.ini`. Unaccounted: 0. It is 438,704 more than the first review's `t_maps` (+391,264, 94
  chunks): the gun step was rebuilt since (fitted geometry of the looks).
- The four blocks read in one piece: .prm 50.4 .. 61.3 MB, .ANM 21.6 .. 22.2 MB, .fxc 17,760,648, F01_Main.WAV
  21.7 .. 22.7 MB - the bot step changes none of them in size. Archives 201.0 / 181.9 / 192.6 / 181.7 MB.
- Beside the archive: 20 files (`F01_Main.WAV .WHD .hti`, `_LS.SND`, seven `_LS_<language>.WAV` + `.WHD`,
  `KLGuns.ini`, `KLWardrobe.ini`); every .WAV has its .WHD; against `z_maps` none missing, none changed, new:
  `KLGuns.ini`. `debug\slot.py` `SIDE` now holds `KLGuns.ini` (F6 a of the first review is done).

## 7. What the files cannot show

- **The call of the vehicle.** `uv_exit.py` (my own frames from the .gms records): no place of any bot before its
  loot wait lies in a level exit box, and no straight line between those places crosses one (nearest over the seven bots: 403 on
  M01 - four metres, the thinnest margin -, 1,474 on M02, 2,984 on M06, 5,139 on M03; the game walks the mesh,
  not my straight lines, and `kl_fa_bots.check` tests the mesh path). After the wait the route of every bot enters
  `Triggers!CallExitVehicle_02` (M01), `Triggers!ExitTrigger_01` (M02), `Triggers!Call_ExitChpooer_Trigger`
  (M06); on M03 no bot enters the exit box at all. So on three maps a bot calls the vehicle some seconds after
  the loot wait ends (10 s start + the walk + at most 20 s), whatever the human is doing. That is the plan, not a
  fault; `M01_wait90` exists for it.
- **The loot wait** names objects with an `OnlineMoneyCtrl` as stock does, but of other classes: stock F07 names
  35 `ZGROUP` (people), the builds name `ZSTDOBJ` money objects too (M02: 19 per bot, M03: 10) and on M01 three
  people (`GangMember_01 / _02`, `Fat_Waitress_01`). Whether the trigger counts a `ZSTDOBJ` was not read; the
  20 s limit ends the wait either way.
- F4 and F5 of the first review are as they were (car squads without an exit rout; the two model queries that
  ignore the hide bit). F5 now concerns seven more gun instances: if it bites, the bots' rifles are invisible too.
- `AllyEscapeBox` (M03, M06) is not a controller of the host level F07's own squad (stock F02 / F06 / F08 run it;
  its six fields here equal F02's).

## 8. What was run

Scripts (scratchpad, not in the repository): `uv_refs.py` (census, old nodes, the squad's references),
`uv_f23.py` / `uv_who.py` (F1 control, F2, F3, who names what in three versions of each level), `uv_ids.py` (both
id spaces, .gms tables, .oct / .rmi / .rmc, .prm offsets), `uv_size.py` (members, side files, what the .prm
gained), `uv_guns.py` (the two ini files against the final .prm), `uv_bots.py` (the squad against stock F07 field
by field), `uv_exit.py` (places against the exit boxes), `uv_tot.py` (the ai totals), `uv_stock.py` (stock
extremes). Logs: `<scratch>\uv\logs\Mxx.*.log`.

## 9. Findings, in order

| # | map | what | kind |
|---|---|---|---|
| G1 | all | `kl_map_tune.py check <u_maps\Mxx>` exits 1 (`members`, `kl_map_ai` totals): it does not know the bot step | tool gap; the builds are sound |
| R1 | M02 | `PoliceSwats\Gate\Way#01` (the drive) is in the 'vehicle called' list as well as on the timer and the counter: a second drive order to a squad that is out | not established; outside `order_faults` (it stops at a `GatePath`) |
| G2 | all | the audit's member comparison rests on `steps.json` as rewritten by the bot step | information |
| - | M01 M02 M06 | a bot calls the escape vehicle shortly after its loot wait | by design; first thing to time in a live round |
| - | M03 | bots end in the yard, never call, never board by the tactic | the tool's own NOTEs |

Claimed and not refuted: no reference-list entry without `ROOT\` and none that names nothing; F1, F2, F3 gone;
every slot id, REF label, .oct record offset, KLGuns.ini root and KLWardrobe.ini root names what it named; no
block grew beyond the gun step; all side files present.
