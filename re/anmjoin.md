# Animation join (.ANM) for the graft

2026-10-09, offline work only: **nothing here has run in the game.** Tool: `tools/kl_anmjoin.py`
(its docstring is the short form of this file); reader / converter: `tools/kl_anm.py`.
Marks: (exe) read in kl2.exe, (data) counted over stock files, GUESS / ASSUMPTION = not established.

## 1. What was wrong before

A graft ships ONE .ANM: the systems level's (S). An animation set the map names and S lacks was
renamed in the .prp to a guess (`kl_graft.dm_rename`, `ANIM_FALLBACK`, `kl_package.ANIM_SETS`:
Police -> Swat_02, Army -> Swat_02, Police_USA -> Police, Generic -> Civilian, Van -> ''). Two of
those were wrong in kind, not only in taste: `Police_USA` and `Generic` are CAR sets (door clips on
door bones), not characters. And the map's own slot names (passenger clips, mini-cutscene clips)
were in no shipped file at all.

## 2. How a level names animations (data: 9 F levels + 6 Dead Men maps, every stored field)

| what | where in the .prp | example |
|---|---|---|
| set | `ZLNKOBJ[2]` of ZFFActor, ZFFPlayer, ZLNKOBJ (weapon), ZHavokCar | `anmcol:animationdatabase#Police_USA` |
| slot name, whole string | `ZPassengerAnimPos[0]` / `[5]` (Dead Men), `ZThrowable[6..23]`, `ZCOOPAirlockController[12..15]` (Dog Days) | `/Vehicles/Police_USA/Back_Left` |
| slot name inside a script | `ZMiniCutsceneRout[0]`: `(anim| /Level_Specific/F06/Situations/Police_01)`, also `startanim`, `msanim` | F06: 4, M09_A: 49, M09_B: 12 `/Level_Specific` names |
| clip name (`anim:...`) | never: 0 keys in 15 key tables | |

A slot name is resolved in the set of the character that plays it: file-wide name -> id (type 7
chunk, binary search kl2 0x68a730), then the set's id -> clip list. So a passenger clip needs
(a) the name in the file's slot table and (b) a list for it in the PASSENGER's set.
kl2.exe holds no set name; of the slot names it holds 405 whole (the rest are composed, e.g. per
weapon). Among them `/Doors/Open_Back_Left` ... and `/Vehicles/Jeep|Police_Japan/..._Dead`, which
no Dog Days .ANM has: the Dead Men car code is still in the exe.

## 3. Facts about the file the join relies on (data, all 41 stock files unless said)

- **Type 5 lists partition the clips**: a set lists exactly the clips of its pool that no earlier
  set of the file lists (909 sets, no exception). `kl_anm.relist` writes it, `kl_anm.audit` checks
  it. `kl_anm.merge` broke the rule when it reused a stock clip (listed twice): fixed.
- One clip name = one data block in every file. A record with size 0 is an alias of the record of
  the same name on the same data (27,610 records); it has the same event count as the owner (0
  exceptions) and differs from it only at +0x24 (size) and +0x2C.
- Same-named sets of two Dog Days F levels never disagree on a slot both have (0 differing of
  about 2,340 common slots per pair, 462 ordered pairs of the nine character sets); a level adds 2 - 5 slots of its own
  (`/Level_Specific/<level>/...`). The 24 weapon sets are identical in all nine F levels.
- Bone index 57 = `GROUND` in all 41 files (hard-coded, kl_anm). S is the base, so it stays.
- Slot names: Dog Days 3,630, Dead Men 1,501, **common 356**. A Dead Men character set therefore
  has almost none of the names Dog Days' AI and weapon code ask for (`/Weapon_Handling/<Dog Days
  weapon>/...` alone are 1,598 names).
- (exe) Events are pulled: kl2 0x4a75d0 (clip record, event id, cursor*) scans the table at
  data + record[+0x10] (record[+6] entries of {u32 id, u16 frame, u16}) for one id and returns the
  frame or -1. An id nobody asks for is inert; record +0x10 is never read when the count is 0.
- (exe + data) Dead Men's passenger clips fire ids 15, 16, 17, 18, 19, 37, 38. No stock Dog Days
  clip fires any of them (21 files), yet kl2.exe asks for 15 (2 call sites), 16 (8), 17 (10),
  18 (2), 19 (2), 38 (1). The car-passenger code is alive and the ids are numbered alike.
- (exe) The loader 0x7079f0 computes the clip table as count * 0x68 (`imul esi, esi, 0x68` at
  0x707a5f): the record size is now read in the exe, not only inferred from file geometry. It
  stores manager dwords 9 / 10 / 11 / 12 at manager +0x58 / +0x5c / +0x20 / +0x24 and zeroes +0x1c.
  The manager is the global [0x1546f6c]; clip accessors 0x48bc90 (index) and 0x4ae780 (index + 1).

## 4. The join

`kl_anmjoin.join(S .ANM, M .ANM, strings, donors=[...]) -> (Anm, report)`; `verify(anm, report)`.
S is the base: none of its clips, data offsets, bone / pose indices or slot ids moves. For every
set X the strings name (`anmcol:animationdatabase#X`):

1. S has X: kept. If M has X too, X gains the slots S's X lacks - same game: all; Dead Men: the
   slot names the strings mention and their directory neighbours (`/Vehicles/Police_USA/*`, which
   brings the `_Dead` variants the exe asks for by itself; it also brings 17 `HG_USB` aim slots
   for M02 / M03 because `/Weapon_Handling/HG_USB/Aim/Shooting_From_Car` is mentioned - unneeded
   but harmless: Dead Men-only names).
2. M (Dog Days) has X: the whole set from M.
3. M (Dead Men) has X and X is not a character set: the whole set, converted. These are the sets
   with **no Dog Days equivalent**: the cars (and weapons, if a graft ever brings Dead Men guns).
4. X is a Dead Men character set (`STAND_IN`): a copy of a Dog Days set under the name X (from S,
   else from a donor file), then widened as in 1 with the Dead Men slots the map mentions.
   WHICH Dog Days set is a GUESS by role. This replaces the .prp rename and keeps the choice in one
   table; the copy costs about 30 KB (it shares every clip).
5. Nobody has X: `report['missing']`.

Clips are found again by name + whole event/data block (bone and pose indices compared by name);
same game: the record must agree as well, else an alias record is added; Dead Men: Dog Days' own
record of the clip is taken. A clip of the same name with other data becomes a second clip of that
name (1 or 2 per Dead Men map, e.g. `anim:_Test/Place_Holder_Ani#Place_Holder_Ani`).

### Header fields recomputed

All by `Anm.save()`; the list is complete because the file holds no other size or offset.
- root: flags | extent, extent, child count (2 per set + 2)
- type 5: extent, name offset, clip count, child extent, the clip list
- type 6: extent, K (slots in use), S (table length), the pair offsets of the table
- type 7: extent, N, string offsets, the name-sorted index
- type 4: dword 0 and 7 (clip count), 1 (data size), 2 / 3 / 4 (name table sizes), 6 (bones), 8 (poses)
- record of an added clip: +0x0C data offset, +0x10 event offset, +0x24 size (0 for an alias)
- data of an added block: the bone index of each track, the pose index of each pose track

### Kept without understanding (ASSUMPTIONS)

- Manager dwords 9..12: S's values. 10 and 11 vary per level and are 0 in six Dog Days levels; none
  of the 68 functions that use [0x1546f6c] was seen reading manager +0x5c / +0x20 / +0x24.
- Clip +0x2C of an added clip: the source file's value. It is per record, not per clip (two
  records of one clip differ), per file (`HG_Default#Reload_UB`: 0x2fc0 in F07, 0x59a0 in F06),
  rises with the clip index in steps of about 144, and is not an offset into the data block.
  Of the clips the six Dead Men joins add, 3 (all in M09_A) have a non-zero value, the car and
  passenger clips have 0; a Dog Days + Dog Days join copies non-zero values. No reader found (two searches: readers near the clip accessors, and +0x2c
  reads inside the manager's users).
- Condition bits of slot lists are taken as numbered alike in both games (kl_anm GUESS). Moot for
  what is taken from Dead Men today: every `/Vehicles`, `/Doors`, `/Body`, `/Level_Specific` list
  of M01 / M03_FA_A, M09_A, M09_B has only the default pair (1,695 pairs).

## 5. Dead Men -> Dog Days clip record (0x50 -> 0x68), `kl_anm.convert`

| Dog Days field | source | status |
|---|---|---|
| +0x00 .. +0x2F | same offsets | established for +0x02 frames, +0x04 fps, +0x06 events, +0x08 flags, +0x0C, +0x10, +0x24 (exe / data); +0x00, +0x14, +0x18, +0x28 copied, meaning not known |
| +0x08 bit 0x1000 | set when a vector is non-zero | established (data 66,261 / 66,261; tested at kl2 0x8b427d) |
| +0x30 vec A start, +0x48 vec B start | Dead Men +0x30, +0x3C | established as "the value at clip start" (kl2 0x8b4200) |
| +0x3C vec A end, +0x54 vec B end | a COPY of the start value | **GUESS / approximation**: exact for loops, wrong for one-shot clips that move. Added clips with vectors: M01 3 (`Vehicles/Jeep#FA_Stand_Leave*`), M02 / M03 17 (`HG_USB` aim poses), M09_A 29, M09_B 4; no door clip has any |
| +0x2C | copied | not understood (0 in every car and passenger clip, non-zero in 3 added clips of M09_A) |
| +0x60, +0x64 | Dead Men +0x48, +0x4C (name pointer, 0 in the file) | established |
| events, data | unchanged | same format (2,622 same-named clips byte-identical across the games); ids see section 3 |

## 6. What each Dead Men map names (map side; `python tools/kl_anmjoin.py needs`)

Every set a map names is in that map's own .ANM. "No Dog Days equivalent" = no Dog Days level has
a set of that kind; these are converted. Character sets get a stand-in (GUESS) plus their own slots.

| map | no Dog Days equivalent (converted) | character sets -> stand-in | slot names mentioned |
|---|---|---|---|
| M01_FA_A | Van (1 car: 8 doors + 4 body slots), Police_USA (2), Generic (2; door slots, lists 0 clips of its own) | Mercenary_04 x13 -> Lynch_NPC, Civilian x1, Female x2 -> Civilian | `/Vehicles/Police_USA` 4, `/Vehicles/Jeep` 2, `/Vehicles/Generic` 2 |
| M02_FA_A | Van (1), Police_USA (1) | Police x8 -> Police, Army x4 -> Swat_02, Civilian x1, Female x2 | `/Vehicles/Police_USA` 4, `/Vehicles/Generic` 2, `/Weapon_Handling/HG_USB/Aim/Shooting_From_Car` |
| M03_FA_A (bank) | Van (2), Police_USA (4) | Army x9 -> Swat_02, Police x6 -> Police, Civilian x2, Female x3 | as M02 |
| M06_FA_A | none | Female_Fighter x6 -> Thug, Mercenary_04 x8 -> Lynch_NPC | none |
| M09_A | none | Army x76, Bouncer x4, Civilian x10, Female x11, Thug x2, Mercenary_04 x1, PlayerCharacter, Lynch_Coop | 65: `/Level_Specific/M09_A` 49 (roof top, elevator, conference room, Retomoto), `/Ambient/Resting_*` 4, `/Gesture/Unarmed` 2, `/Briefing/Crouched`, `/Movement/*` 7, `/Damage/Death`, `/Weapon_Handling/Plant` |
| M09_B | Police_Japan (14 cars), Swat_Van (2; 2 door slots), Van (1) | Army x84, Swat x9 -> Swat_02, Civilian x21, Female x15, Thug x2, Mercenary_04, PlayerCharacter, Lynch_Coop | 26: `/Level_Specific/M09_B` 12 (exit elevator, escape), `/Vehicles/Police_Japan` 4, `/Vehicles/Generic` 3, `/Vehicles/Van` 2, `/Vehicles/Police_USA` 2, `/Ambient/Scared`, `/Movement/*` 2 |

Scripted animation of map OBJECTS (doors, lifts, the escape van as a prop) is not in the .ANM in
either game: it is MatPosAnim / VertAnim key data in the .buf (KEYS chunks, already shifted by
kl_graft). The .ANM only animates skeletons: characters, weapons, ZHavokCar.

### Bones

- Car sets move `DOOR_BACK_LEFT/RIGHT`, `DOOR_FRONT_LEFT/RIGHT`, `BODY`, `WHEEL_*` (4),
  `SEAT_*` (4), `GROUND`. These 13 names are added to S's bone table (F07: 143 -> 156; the largest
  stock table has 239). The Dead Men car models hold exactly these names (M01FAA .prm: 9 models
  with `DOOR_BACK_LEFT`, M09_B: 10), no Dog Days .prm has them. So the clips match the models the
  map brings, and only those. (Counted as occurrences of the name in the .prm, not per model.)
- Passenger and `/Level_Specific` clips are human clips; they add no bone name to F07's table.
- The other direction is the open one: a Dog Days stand-in set on a Dead Men character model.
  Swat_02 / Police / Civilian / Lynch_NPC / Thug move 91 bones, the Dead Men sets 94; the only
  Dog Days bone the Dead Men sets never move is `free_bone01` (about 150 clips per set), which no
  Dead Men model has (re/characters.md section 5). Milestone B (run B-4) already played Dog Days
  sets on Dead Men agents without a crash; whether they animated correctly was not looked at.

## 7. Tests (`python tools/kl_anmjoin.py test`, 2 minutes)

Strings = S's systems side + M's map side (`kl_prpjoin.sides`), donor F03 (the one F level with
Police, Thug, Civilian and Dog).

- 9 x 14 = **126 joins, 0 failed, 0 sets missing.** Every result passes `verify`: re-read to the
  same bytes; `kl_anm.audit` (layout, every clip listed once and played by a set, offsets inside
  the data, bone / pose indices inside the tables, flag 0x1000); S's clips, data, names, tables,
  dwords 9..12 and every slot list unchanged; every slot list taken plays the same clips as in its
  source (name, events + data, bones and poses by name); every named set present.
- A join that needs nothing (F07 + F09, or no M) returns stock F07 byte for byte.
- Sizes: S 19.8 .. 21.9 MB, result 20.3 .. 23.4 MB (a join adds 0 .. 3.6 MB; the most where S
  lacks Police, Thug and Civilian and the donor supplies them).

| S + M | result | added |
|---|---|---|
| F07 + F01 / F02 / F08 | 21.6 MB (S 21.6) | Police: 7 clips, 37,716 bytes (1,531+ clips found in S) |
| F07 + F06 | 21.8 MB | Police + 4 `/Level_Specific/F06` slots in 6 sets: 11 clips, 163,660 bytes |
| F07 + F03 | 21.9 MB | Police + 18 slots: 25 clips |
| F07 + M01_FA_A | 22.1 MB | 39 clips, 379,288 bytes, 13 bones, 42 slot names |
| F07 + M03_FA_A (bank) | 22.2 MB | 69 clips (25 of them the donor's Police), 487,828 bytes |
| F07 + M06_FA_A | 21.6 MB | 2 set copies, no clip |
| F07 + M09_A | 23.0 MB | 73 clips, 1,170,052 bytes, 85 slot names |
| F07 + M09_B | 22.6 MB | 54 clips, 723,672 bytes, 13 bones |
| F07 + M09_A + M09_B (two joins in a row) | 23.8 MB | 42 sets, 3,369 clips, 156 bones |

`compact()` (drop the sets nobody names and their clips) gives back 1 .. 2.4 MB only, because the
first set of a file owns the clips every set shares. Not worth renumbering S; left as an experiment.
`kl_anm.py check` still reads and writes all 41 stock files byte for byte with the new audit rules.

## 8. What kl_graft should change (I do not own that file)

In `build()`, after `Jn = J.join(...)`, replace the block "animations: one file that has every set
the joined .prp names" by:

    import kl_anmjoin
    anm, arep = kl_anmjoin.join(S['.ANM'], M['.ANM'], Jn.p.keys,
                                donors=[kl_anmjoin.stock_anm('F03')], log=log)
    for b in kl_anmjoin.verify(anm, arep): note('.ANM: ' + b)
    ...  '.ANM': anm.save()

`S['.ANM']` / `M['.ANM']` are the stock members (`DeadMen` leaves the .ANM untouched; the join
converts it). And stop renaming:
- `dm_rename`: delete the whole `elif s.startswith(kl_anm.PREFIX) and s not in have` branch and
  `ANIM_FALLBACK`; set names stay as Dead Men wrote them.
- `kl_package.ANIM_SETS` is then only used by the old whole-level build.
- `kl_retype.finish(have=...)` (emptying car sets): not needed, pass no `have`.
- `verify()`'s "animation sets the .ANM lacks" check stays as it is and should now find none.
- `pairs()`: the animation column no longer limits the choice of S and M.
For Retomoto (two maps): call `join` twice, the second time with the first result as S.

## 9. First live test (in this order; each step changes one thing)

1. **File acceptance, no new behaviour.** Build the known-good F07 + F09 graft, but ship
   `join(F07, F06)` as its .ANM (21.8 MB: one more set, 11 clips, 4 slot names nothing asks for).
   Expected: `RESULT: clean exit` as in run 3 / 7. A crash here means the engine depends on
   something the re-serialised file changes (dwords 9..12, +0x2C, table order) - the cheapest place
   to learn that.
2. **Dog Days + Dog Days, used.** F07 + F06 with the joined file: F06's police now have their own
   set and the mini cutscene `011_police_first_reinforcement_wave` its four clips. Look at a
   screenshot of the police.
3. **Dead Men map.** F07 + M01_FA_A with the joined file (22.1 MB), first with the cars still
   flattened (only the character sets and passenger slots matter), then with ZHavokCar kept
   (kl_retype): the police cars' doors (`/Doors/Open_*` on `DOOR_*` bones) and the passengers
   leaving (`/Vehicles/Police_USA/*`, events 15..19) are the things to watch.

## 10. Not established

- Reader of clip +0x2C and of manager dwords 10 / 11; who consumes chunk types 5 and 6 at all.
- Whether Dog Days' ZHavokCar / passenger code really runs the door and seat slots (strings and
  event ids say the code is there; no Dog Days level exercises it).
- Stand-in choice per Dead Men character set (`STAND_IN`), condition bits, `free_bone01`.
- End vectors of converted one-shot clips (`Jeep#FA_Stand_Leave*`).
- The strings used in the tests are an approximation of the joined .prp (systems side of S + map
  side of M); the real call passes `Jn.p.keys`.
