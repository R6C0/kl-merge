# The 0x686a66 crash of the random-route bots (Retomoto, run C_DM09, 2026-10-11 01:34)

Offline work: kl2.exe read with `debug/dasm.py` + capstone, the dump `%TEMP%\kl_triage\20261011_013427\KLHook_2.dmp`
(module data, the stack and 0x400-byte windows round every register and stack pointer: NOT the whole heap), the
dump `%TEMP%\kl_triage\20261008_200513\KLHook_2.dmp` (the only one of the 107 dumps under `%TEMP%\kl_triage`,
`<work>\research`, `<work>\build\klhook` and the game folder that holds ZCheckVisible's grid; scratchpad
`fin\grids.py`), the run's log `<work>\build\klhook\live\C_DM09.log`, the level files. Nothing ran in the
game for this note. ASSUMPTION = fits the evidence, not proven; everything else below was read.
SECOND PASS, after the review (`re/crash_686a66_review.md`; what was done about each of its points: section 10).
The cause and the data fix stood; the RULE that guards against it read the wrong box and was rewritten
(section 2.1), and with it sections 5 to 9.

## 0. Short answers

- **The forks are not the cause.** The crash is a 16-byte write from OUTSIDE into a Defend step's place list. The
  list was never freed and nothing of the squad's goal handling is on the stack.
- **Who writes:** `ZFakeTarget`'s frame update, kl2 0x560630, for a FakeTarget that stands outside the vision grid
  of `ZCheckVisible`. Registration fails for such a place (0x59c790 returns index 0xff) and the update then writes
  its grid cell and its place into record 0xff of a table of 200 records: 0x5a8 bytes behind the end of the
  ZCheckVisible object, into whatever the heap has there.
- **Which FakeTarget:** the 'Mercenary' target on the body of F07's escape van 02, which `kl_fa_street.py` parks
  600 m under Retomoto's road (`PARK_OTHERS`; van 03 is parked the same way). The 16 bytes in the dump are its
  place to the float: (-3216.6, -60040.0, 3419.3).
- **Since when, where:** every Retomoto build since the street layer (2026-10-09 18:10, `play2`) has the two
  parked targets, the non-dynamic ones too. **The Retomoto on the owner's tab has them**: the owner's tree
  w_tabC had `<DD>\KLExpansion\Maps\DM09\F06_Main.zip` (03:38:10) = `rt_full7\retomoto_full` member for member
  (read 05:25); the lead's test tree w_tabN that is in the game folder since 05:37 has DM09 =
  `z_route7\retomoto_full` member for member (read 06:30), which has them as well. So record 0xff is written in
  every Retomoto round played from either tree. The four other maps do not have it (M01 M02 M03: one FakeTarget,
  on the van that is called, inside the vision space; M06: none).
- **Why one run in four:** the write happens in every run; it only shows when the 16 bytes it hits are used. Here
  they were the place list of `Squad#08\030_DefendBehaviour_way_c_b` (way c of the runner's fork behind the loot
  wait, drawn 7 times in 9), and the crash came when that step first ran. Whether the same object is hit in every
  run of one build is NOT established (section 3).
- **Fix (level data, `tools/kl_fa_bots_dyn.py`):** `check` FAILS a FakeTarget whose registration place is not
  inside the vision space; `build` takes that controller off its node (.prp only); `fake-fix` does only that, for
  a build that is not to get the dynamic step. The route form is unchanged - it is stock's, field for field.
  The 0.1 s timer before a fork is off by default (`--fork-gap` brings it back; the build log says which was
  made): it mends nothing - the build that has it has the two parked targets too.
- **The vision space** is read from the `.rmi` records of the rooms' bounds. That reading gives the grid of the
  one dump that holds one bit for bit, and 'no record' for the parked van as the crash dump shows (section 2.1).
- **Builds:** `<work>\build\z_route4\`: M01 M02 M03 M06 are byte-identical to the builds on the tab;
  `retomoto_full_r2` (= `retomoto_full`, same archive) is the room-first bots + routes + the two targets off;
  `retomoto_tab_fix` is the tab's Retomoto with ONLY the two targets off. None loaded in the game (section 7).

## 1. The stack as it was

`debug/dump.py` lists every word on the stack that follows a call; three of the hook's 'callers' are stale words
in the faulting function's own 0x240 bytes of locals (below ebp), three more in the scheduler's locals. By the
frame pointers ([ebp+4] at 0x01b4f514, 0x01b4f5ac, 0x01b4f5cc) the real chain is:

| return address | function | what |
|---|---|---|
| (fault 0x686a66) | 0x686920 | `CPPScript::ZDefendBehaviourGoal` vtable 0xbccf54 slot 2: the goal's body |
| 0x65bc6c | 0x65bbf0 | goal start: state 1, slot 1; state 2; slot 6 false -> ONE yield (0x55b9f0); then the body |
| 0x63c74d | 0x63c6c0 | the script object's goal scheduler (setjmp 0x168e4c8, a goal's stack saved in an arena); the first pass named 0x63c5c0, which is the function before it (`CPPScript::ZScriptInfo` slot 4) |
| 0x570e68 | 0x570e60 | `CPPScript::ZSquad` slot 4: the squad's update |
| 0x601f84 | 0x601e80 | walks the script objects |
| 0x4bd0e1 | 0x4bca90 | `ZFFGameData` slot 13 |
| 0x408022, 0x5c7168, 0x87aa7c | | engine frame, main loop |

Stale, not callers: 0x55ba07 (the yield's own setjmp return), 0x836d34, 0x63c8d7, 0x41fedb, 0x7579ea, 0x788c9d.

The goal (esi = 0x7e928880): +0x04 its squad 0x7df8f8b0 (one member; the squad holds the goal at +0x74 with
priority 0xc8 and at +0x154), +0x08 state 2, +0x0c its context (saved stack: arena offset 0x5a3c, 0x24 bytes =
the yield inside 0x65bbf0, and the scheduler's pending-free globals 0xd1a28c / 0x168e508 hold the same pair), +0x18
its rout, +0x2c the place list 0x7d73f740, +0x30 place index 0. So: the goal had been started in an earlier
update, yielded once as every goal does, and this was the FIRST run of its body. The fault is the body's first
look at the list (`mov ecx,[esi+0x2c]; mov edx,[ecx]; mov eax,[edx+0x14]`): the list's vtable word is 0xc76a8804.

## 2. What was overwritten, and by what

The list is not the goal's. `ZDefendBehaviourRout` slot 14 (0x4b4af0) makes ONE goal per rout (0x44 bytes, kept
at rout+0x60 for the life of the level) and gives it a plain pointer to the rout's own reference list:
`goal+0x2c = rout+0x4c` (field 1, the places) when that list has entries, else `goal+0x1c` = the one place of
field 0. Nothing frees or rebuilds that list after the load.

The heap round it (every block: 8 bytes heap header, then the engine allocator's 16 bytes {0x12345678, previous,
next, raw pointer}, then the object):

    0x7d73f728  1707947d 88001000                      heap header, busy
    0x7d73f730  12345678 7d73f970 [ff100110 c54909d0   allocator header: next and raw pointer OVERWRITTEN
    0x7d73f740  c76a8804 4555b444] 7d73f980 3 3 3 1    REFTAB: vtable (0xb8d77c) and first pointer OVERWRITTEN
    0x7d73f970  12345678 7d73f6a0 7d73f730 7d73f970    the list's array block: intact, and its 'next' still
    0x7d73f980  0 0 3 0  6942 6943 6944                names the list's block -> the list was NEVER FREED

16 bytes, 0x7d73f738..0x7d73f747, in the steady state (two more writes can go through the same index: below).
They are a record of another object:

- `ff100110` = bytes 10 01 10 ff = the constant at kl2 0xcdf6d4: 'no cell' of a grid of 16 x 1 x 16 cells
  (0x79bae0 / 0x53be20 return it for a place outside the grid);
- `c54909d0 c76a8804 4555b444` = the floats -3216.61, -60040.02, 3419.27.

The only code that stores {cell, x, y, z} is 0x7143f0: `record[i].cell = grid.move(...)`, `record[i].pos = pos`
at `this + 0x12ae4 + i * 0x1c`, `i` a byte. `this` is the `ZCheckVisible` singleton (pointer at 0x1535c70; built
by 0x5f9470 in 0x14120 bytes: grid at +0x50 with 256 cells of 0x40 from +0x80, 200 blocks of 0x12c from +0x4080,
200 records of 0x1c from +0x12ae0). The crash dump has the pointer, 0x1535c70 = 0x7d72b070 (the object itself is
not in that dump; its vtable 0xba7ae4 is seen in the dump of 2026-10-08), and

    0x7d72b070 + 0x12ae4 + 0xff * 0x1c = 0x7d73f738

So record index 0xff - 'not registered' - of a table of 200 was written: 0x5a8 bytes behind the object.

Who calls 0x7143f0 with an unchecked index: it has six call sites in five functions. Four functions test the
index for 0xff first (0x42a090 `ZHavokCar`, 0x502720 `ZHavokLnkObj` / `ZHeli` / ..., 0x5dfa90, 0x6ed130).
**0x560630 = `ZFakeTarget` vtable 0xbd143c slot 25, its frame update, does not** (both its sites, 0x56072e and
0x56076d): `cmp byte [esi+0xa0],0xff / jne / call 0x55cc40` (register), then it goes on to 0x7143f0 with
`movzx reg, byte [esi+0xa0]` whatever the registration gave. 0x55cc40 takes the node's world place, adds 140.0 to
y (the double at 0xb45358) and asks 0x59c790, which returns 0xff when that place is outside the grid or the 200
records are full.

Two more writes through the same unchecked index (the review's N2; the second re-read here): on the first frame
0x7143f0 hands the four bytes at +0x146c8 to 0x79bae0 as the OLD cell, and if they look like one (x <= 15, y 0,
z <= 15, slot < 0x3f) a slot is taken off that cell's list (0x789d00). And `ZFakeTarget` slot 26 (0x692d10)
calls the unregister 0x669620 with `[this+0xa0]` unchecked when its health falls below 0 - not reachable for the
vans (health -1: `cmp [ebx+0x50],0 / jl` leaves at once).

The level has that place: `Animation/F07/F07_Escape_Vehicle_02.zip\...\V_Van_00\Body\Body_Main`, FakeTarget
('Mercenary', -1, '', 20.0, [], 0, 1, 0.0, 0.0), at (-3216.6, -60040.0, 3419.3); van 03's at
(-1577.9, -60040.0, 1102.6). `kl_fa_street.place_escape` moves the two vans that are not called down by
`kl_fa_author.PARK[1]` = -60000. Both write the same record; the dump shows van 02's.

How often: slot 25 is the per-frame slot of these controller classes (a `TriggerDelay2` counts its time in it,
0x744c30). How often the engine calls it for a FakeTarget was not measured; one call does the damage, and the
bytes stay wrong because nothing else writes there.

### 2.1 The vision space (rewritten after the review)

**What the grid lies over** (0x4ee5b0 -> 0x541e40). lo starts at +1e38, hi at -1e38 (0xb6ed98 / 0xb5f1e0). A
pre-order walk of the WHOLE scene (vtable +0x78 of the root = 0x883840; M01's rooms sit three levels down)
takes every object whose class is ZROOM-derived (class id global 0x150c4dc, mask 0x150c4e0) and skips:

- a hidden one (`test dword [slot+0x3c], 0x400`),
- one named `*backdrop*` (0x7472b0: `_memicmp` at every offset, so anywhere in the name, any case),
- the scene root itself,
- one whose vtable +0x2fc answers true = bit 2 of the dword at +0x118 (0x8e4fc0 -> 0x4d43b0). That dword is 0
  from the constructor (0x545150: 0x54522c) and its only other writer is the setter 0x6b81e0 (set, mask), which
  is named by the two room vtables alone (ZROOM, ZBackdrop +0x2e4) and has no direct caller. Of the 23 call
  sites through a vtable's +0x2e4, the seven that pass two arguments to an object that is not the caller's own
  (0x4455d0, 0x4455ef, 0x4778c5, 0x59804d, 0x700805, 0x927c4c, 0x927ddb) pass the constants 0 and 1: bit 0;
  the others are GUI controls, link objects and actors on themselves, or take one argument. No code was found
  that sets bit 2, so this filter skips nothing - by static reading.

A room named `*VisionSpaceBox*` is the box alone and ends the walk (0x541fdd; no stock level and no build has
one). Each room that is taken joins boxes into lo / hi with 0x44a010 (`lo = min(lo, c - h)`, `hi = max(hi, c +
h)`, c and h from 0x8849b0: the slot's centre +0x30 and half extents +0x40 turned into world axes by 0x7d8460,
|matrix| x half): when the room has a list at +0x38 the box of every object of that list (resolved by 0x8ccde0),
else the room's own slot's. Tail: cell size = (dx / 16, dy, dz / 16) kept as float32, and 1 / cell size: **16
cells in x and z, ONE in y**.

**The cell of a place** (0x59c790 for a registration, 0x79bae0 for a move): `(BYTE) ftol((p - lo) * (1 / size))`
per axis with ftol = 0xa8d330 = `cvttsd2si`, a truncation TOWARD ZERO, and only the low byte is tested (`cmp bl,
0xf / ja`, `cmp byte, 0 / ja`, `cmp cl, 0xf / ja` -> 0xff). So 'no record' is not 'outside the box': a place up
to one whole cell under lo gets cell 0 (in y: up to one whole box height under the floor), and a place 256 cells
away wraps round. Only hi is a hard edge.

**What that is in the level files.** The list at +0x38 is the room's ZBOUND children ('InsideBound_NN'), and
their boxes are the records of the `.rmi` (room index: +0x00 1 = axis aligned, +0x04 matrix, +0x28 centre,
+0x34 a second point, +0x40 half extents, +0x4c the room's slot id, +0x50 an optional second slot id). Counted
on 14 levels (the nine stock Fragile Alliance levels and the five builds; scratchpad `fin\tie.py`):

- a room with bounds has one record per bound or none at all, never another number;
- such a record NAMES its bound: its +0x34 is the ZBOUND child's own world place (582 of 582 records), and where
  +0x50 holds a slot id it is that child's (59 of 59);
- a room without bounds has one record of its own, with +0x34 = (0, 0, 0) (53 of 53), or none.

So the tool calls a record a bound's only when its +0x34 is the place of one of the room's ZBOUND children.

**Proof, one level.** The dump of 2026-10-08 20:05 (M01_FA_A converted whole, crash at 73 %) holds the object,
and the twelve floats at +0x50 are

    cell  3612.139404296875   18400.00390625    3239.385009765625
    lo  -20224.4765625        -200.0009765625   7929.8486328125
    hi   37569.75390625      18200.001953125   59760.0078125

The union of M01's bound records (`c - h`, `c + h` in float32; 17 records of 8 rooms) is those six floats BIT
FOR BIT, and the cell sizes and their inverses formed from it are the other six
(`kl_fa_bots_dyn.py fake-test`, control GRID; all six faces of M01's box come from bound records).

**The first form of the rule was wrong** (the review's D1, re-derived with `fin\oldbox.py` in the scratchpad).
It joined the items of the root's room tree (.oct room 0, tree 4): those are the rooms' CONTENTS. On M01 that
box is (-27549, -398, 0)..(49140, 18203, 72141): 7,324 to 12,381 wider than the game's on four faces. On
Retomoto it is y -19804..68707, and under kl2's own arithmetic the parked van's place gets cell (5, 0, 6) there:
a record, no write - which the crash dump contradicts. It failed the two vans only because they are outside
both boxes by a plain box test, and it passed places kl2 cannot register (the same van 400 m ABOVE the road, a
van 200 m east of the tower, a van 600 m up the road: 'pass' then, 'no record' by kl2's arithmetic on the
records' box, FAIL now).

**Retomoto by the right reading.** Bound records: x -38470.1..8596.2, y -10000.0..28722.6, z -26550.0..49300.9
(38 records of 17 rooms). The place van 02's target registers at is y -60040.02 + 140: (-59900.02 + 10000) /
38722.6 = -1.29 -> -1 -> byte 0xff -> no record: what the dump shows. Van 01, the one that is called, at
(-1850, 2, 8683): cell (12, 0, 7), a record.

**Two boxes, and what is not known.** `vision_space()` returns both:

- `sure`: the records that name a ZBOUND child of their room - the kind the M01 dump proves. The engine's
  box is this or LARGER.
- `all`: `sure` and the single records of rooms without bounds (M01: WarehouseStaircase, WarehouseFoyer and
  F07's DebugRoom; Retomoto: `M09_A_Out_CityScapeBack` and DebugRoom). ASSUMPTION that such a record is the room's
  own slot box, which is what the engine joins for a room without a list. On M01 those rooms lie inside the
  bounds' box (the converted level had no DebugRoom), so the dump says nothing about them. On Retomoto `all` is
  x -87017.0.., z -99949.3..52922.5: twice as wide. The code has no exception for DebugRoom (a 1-unit room at
  (3, 0.5, 2)): by the reading it counts, and pulls the box to the origin on F01 F04 F06 F07 and the Dead Men
  maps (M01's z from 7930 to 1).
- NOT READ: the box of a room the walk takes that has no record. Retomoto `M09_B_Skyscrapers_01b`,
  `M09_B_Skyscrabers_01a`; Late Night Opening `M02_FA_A_Out_Skyline`; the bank `M03_FAA_Outside_04_Buildings`;
  stock F02 (2), F03, F05, F06 (3), F07, F08, F09 (2). The engine joins a box for each (its bounds' or its own
  slot's). On Retomoto that box cannot reach far down: the vans would have registered had lo.y been under
  about -15,600 (with hi.y as read).
- A turned record (+0x00 = 0; stock F09, the park): |matrix| x half; whether the record's matrix is the slot's
  or its transpose is not established, so `all` takes the larger and `sure` the smaller per axis.
- The hidden bit is read from the .gms record's flags (as `cover_boxes` does for kl2 0x6d6a80); no room of the
  14 levels has it.

**The rule** (`check`): the place a FakeTarget registers at (its node's, 140 higher) must lie inside `sure`, 1
unit clear of its faces. Inside `sure` it gets a record under EVERY reading above, because a larger box only
makes the cells larger. kl2's own looser arithmetic on `all` is printed beside each target and is not relied on.
Controls: 27 of 27 stock FakeTargets pass (F01 3, F04 3, F05 9, F07 3, F09 9); M01 M02 M03's one target and
Retomoto's van 01 pass on `sure` alone; the two parked ones fail under both boxes and both tests.

## 3. Why it showed in one run of four

The victim, by the ids in the list's array (0x6942..0x6944 = loader slot + 2 of three place boxes; the lists
beside it in the same heap run are the same squad's: 0x693f..41 `030_DefendBehaviour_way_c`, 0x6945..47
`..way_c_c`, one-entry lists naming `033_DefendBehaviour_out`, `050_RandomTrigger_way`, ...):

    Gameplay!merc_bot_squad!Squad#08 \ 030_DefendBehaviour_way_c_b     (the runner; way c of fork 030: weight 7 of 9)

a step BEHIND the loot wait, reached by `020_SquadModifier_Loose_defense -> 030_RandomTrigger_way` (weights
1, 1, 7: way c) `-> 030_DefendBehaviour_way_c -> ..way_c_b`. The four runs of `z_route\retomoto_full` (the bot
log's money per record; which record is Squad#08 is not in the logs - the crew is drawn at random):

| run | police -> crew | first money | the bots | crash |
|---|---|---|---|---|
| R12_DM09 | 0.15 | 28 s after GO | all dead by 96 s; each looted, some lived 20..50 s after their last gain | none |
| B_DM09_007 | 0.07 | 32 s | all dead by 105 s; several lived 20..40 s after their last gain | none |
| B_DM09_000 | 0.01 | 36 s | all dead by 151 s; one lived 70 s after his last gain | none |
| C_DM09 | 0.01 (dial 0.001) | 62 s | all alive; one full ($300,000) at 67 s | 69.5 s: 2.5 s after that |

So bots finished looting in the clean runs too, and steps behind the loot wait were most probably walked there.
Two readings, NOT decided: (a) a level loads in the same order every time, so the object 0x5a8 bytes behind
ZCheckVisible is the same in every run of one build, and the clean runs are the ones in which Squad#08 died
first or drew way a / b (2 in 9); (b) the heap behind ZCheckVisible differs from run to run and the write
usually hits something that does not mind. Absolute addresses do differ between the runs (the bots' actors:
0x7d3dcf50, 0x7d417be0, 0x7d3b3be0, 0x7d457670). Under either reading every other Retomoto build has its own
victim - a list nobody reads, or something that only misbehaves; nothing in the Retomoto notes was tied to that
here.

## 4. The forks: what the engine does, and stock

Read because the first reading blamed them (CLAUDE.md 'CRASH 0x686a66 READ FROM THE DUMP': 'freed', 'array
zeroed' - the array is [0, 0, count, 0, ids], not zeroed; the list is linked and its heap block busy).

- A step starts: `ZBaseBehaviourRout` slot 26 (0x4ebed0) on its message -> slot 34 (Defend: 0x457720) ->
  0x791090(rout, the rout's goal): ignored while the goal's state is 1..3; else owner and rout are set and
  0x7f6750(squad, goal) makes it the squad's goal. The scheduler starts it at the squad's next update, it yields
  once, its body runs the update after.
- A step ends: the body orders every member to each place in turn and yields while they walk (0x686a74..0x686ce1),
  waits for all of them, and as its LAST act calls 0x5c6e70 -> 0x8df0d0(rout): the arrival list (field 7) gets its
  message there, in the old goal's stack, after its loops. Then the body returns, state 3, 4, back to the
  scheduler.
- `RandomTrigger` (0xbc8a6c slot 26 = 0x4d86e0, no update slot): draws and passes the message on AT ONCE, in the
  sender's stack. `TriggerDelay2` (0xbc25fc slot 26 = 0x71e250): only arms; it fires from its own update
  (slot 25 = 0x744c30). So the other session's assumption about the timer is right as a mechanism - and beside
  the point: every stock chain starts its next step from the old goal's last call.

Stock, the nine Fragile Alliance levels' bot squads (1,100 Defend steps, 344 RandomTriggers):

| | stock | ours (z_route3 M01, z_m02s1 M02, z_hop M03, z_route M06, z_route Retomoto) |
|---|---|---|
| a Defend's arrival list names a RandomTrigger | 119 | 20 + 54 + 32 + 19 + 57 |
| ... whose draw is a Defend of the same squad | 77 (F03 14, F07 35, F08 28) | all of them |
| ... Defend 'rout' -> RandomTrigger -> Defend 'rout' | 21 (F07) | 5 + 25 + 17 + 0 + 31 |
| ... Defend 'rout' -> RandomTrigger -> Defend 'pos' | 14 (F08) | 15 + 29 + 15 + 19 + 26 |
| a RandomTrigger named by a SquadModifier / a timer | 42 / 181 | 18 + 14 + 11 + 28 + 7 / 9 + 13 + 6 + 1 + 4 |
| a Defend names a Defend | 56 | 87 + 161 + 116 + 93 + 198 |
| an arrival list that names TWO things | **0** | **15 + 29 + 15 + 19 + 28** |
| an arrival list that starts two Defend steps at once | 0 | 0 |

Three stock chains beside ours, field for field (DefendBehaviourRout: 0 one place, 1 places, 2, 3, 4 move
style, 5, 6, 7 arrival list, 8, 9; RandomTrigger: 0, 1..4 weights, 5..8 lists):

    F07 Squad#08  060_DefendBehaviour_rout_junction_garage   ['', [Pos#01, Pos#02], 1, 0, eDMS_NotSet, eDF_NotSet, '', [060_RandomTrigger_BeforeStreet], 1, 0]
                  060_RandomTrigger_BeforeStreet              [1, 3, 3, 0, 0, [065_..._BeforeStreet_Left], [065_..._BeforeStreet_Right], [], []]
                  065_DefendBehaviour_rout_..._Left           ['', [Pos#01, Pos#02], 1, 0, eDMS_NotSet, eDF_NotSet, '', [...], 1, 0]
    F08 Squad#08  040_DefendBehaviour_ExitOfficePart1         [Pos#01, [], 1, 0, eDMS_NotSet, eDF_NotSet, '', [030_RandomTrigger_OfficeCorridor_Choise], 1, 0]
                  030_RandomTrigger_OfficeCorridor_Choise     [1, 3, 3, 0, 0, [050_..._Left], [050_..._Right], [], []]
                  050_DefendBehaviour_OfficeCorridor_Left     ['', [Pos#01, Pos#02, Pos#03], 1, 0, eDMS_NotSet, eDF_NotSet, '', [...], 1, 0]
    F07 Squad#02  040_SquadModifier_Loose_defense             {eDM_Loose, 26: [040_RandomTrigger_out_of_loot_area]}
                  040_RandomTrigger_out_of_loot_area          [1, 3, 3, 0, 0, [050_..._left], [050_..._right], [], []]
    OURS Squad#08 020_SquadModifier_Loose_defense             {eDM_Loose, 26: [030_RandomTrigger_way]}
                  030_RandomTrigger_way                       [1, 1, 1, 7, 0, [030_..._way_a], [030_..._way_b], [030_..._way_c], []]
                  030_DefendBehaviour_way_c                   ['', [Pos#01, Pos#02, Pos#03], 1, 0, eDMS_NotSet, eDF_NotSet, '', [030_DefendBehaviour_way_c_b], 1, 0]
                  030_DefendBehaviour_way_c_b  (the victim)   ['', [Pos#01, Pos#02, Pos#03], 1, 0, eDMS_NotSet, eDF_NotSet, '', [030_DefendBehaviour_way_c_c], 1, 0]

The step that crashed was reached by a SquadModifier -> RandomTrigger (F07 Squad#02's form) and then a plain
Defend -> Defend: the 'Defend -> RandomTrigger -> Defend' link is not even on its way.

The one shape of ours stock does not have: a 'rout' step whose arrival list names TWO things, `[NNN_Timer_hold,
NNN_RandomTrigger_cover]` (a hold drawn at random beside the timer that goes on: 104 lists; with one hold only
the list names that 'pos' step itself: 2 lists). The engine walks the whole list (0x8df0d0), the timer only arms,
the RandomTrigger starts ONE 'pos' step: one Defend step is started, as from a list of one. It ran on all five
maps without a fault and is left as it is. Not proven beyond that.

## 5. Which builds are exposed

`python tools\kl_fa_bots_dyn.py check <folder>` says it. The rule's lines of the runs of this pass (logs:
scratchpad `fin\out\`):

| build | FakeTargets | fail the rule | check |
|---|---|---|---|
| `z_route\retomoto_full` (the crash) | 3 | 2 | FAIL (2 FAIL, 4 NOTE), exit 1; both FAILs are this rule |
| `rt_full7\retomoto_full` (= DM09 OF THE OWNER'S TREE w_tabC; ran clean as T7_DM09) | 3 | 2 | FAIL (2 FAIL, 7 NOTE), exit 1; both this rule |
| `rt_full6\retomoto_full` | 3 | 2 | FAIL (2 FAIL, 7 NOTE), exit 1; both this rule |
| `z_cover2\retomoto_full` | 3 | 2 | FAIL (2 FAIL, 4 NOTE), exit 1; both this rule |
| `z_route7\retomoto_full` (commit 76bfdcd: rt_full7 + routes + the 0.1 s fork timer; = DM09 of the lead's test tree w_tabN; ran clean three times as R7a / R7b / R7c_DM09) | 3 | 2 | FAIL (2 FAIL, 4 NOTE), exit 1; both this rule - the timer does not take the write away |
| `play2`, `play3s`, `x_chunks\retomoto_wardrobe`, `y_loot\retomoto_loot`, `rt_masks\retomoto_masks`, `rt_ai\retomoto_ai`, `rt_ai2\retomoto_ai2`, `rt_full`, `rt_full4`, `rt_full5` `\retomoto_full`, `z_dyn\retomoto`, `z_cover\retomoto_full` | 3 each | 2 each | (counted with `fake_targets`, scratchpad `fin\count.py`; the full check not run on them) |
| `z_route4\M01`, `M02`, `M03` (= the tab's DM01 DM02 DM03, member for member) | 1 | 0 | the rule passes; see section 7 for the whole check |
| `z_route4\M06` (= the tab's DM06) | 0 | 0 | PASS |
| stock F01 F04 F05 F07 F09 | 3 3 9 3 9 | 0 | 27 of 27 inside `sure` (F02 F03 F06 F08 have none) |

In every faulty build the two are vans 02 and 03 at y -60040: outside by (0, 49901, 0), kl2's arithmetic cell
(14, 255, 10) = no record.

The four maps: not exposed. Their one FakeTarget is on the van that is called, at the place where it waits:

| map | the target | the bounds' box (`sure`) | cell |
|---|---|---|---|
| M01 | (8408, 2, 16671) | x -20224..37570, y -200..18200, z 7930..59760 | (7, 0, 2); (7, 0, 4) with DebugRoom counted |
| M02 | (1123, 2, -12911) | x -25013..24509, y -19..4500, z -16000..4000 | (8, 0, 2); 3,088 from the z face |
| M03 | (-2568, 152, 569) | x -24197..39851, y -60..20251, z -74546..18981 | (5, 0, 12) |
| M06 | none | x -30100..28900, y -3000..7000, z -29300..21223 | - |

A registered target that later leaves the grid is harmless (0x79bae0 gives it 'no cell' in its OWN record). The
second way to the same write - 200 records in use at once - has no rule: records are given back (0x669620, five
callers), so it is a peak, not a total; Retomoto has 99 actors + 16 players + 3 targets, the maps 39..49 objects
of the classes seen to register (not counted exactly).

## 6. What was changed (`tools/kl_fa_bots_dyn.py` only)

- `vision_space(B)`: the two boxes of section 2.1 from the `.rmi` records, with the rooms counted by a record of
  their own, the rooms without a record and the skipped ones by name. `grid_cell(lo, hi, p)`: kl2's arithmetic.
  `outside(space, p)`: the rule (the registration place against `sure`). `fake_targets(B)`: every FakeTarget
  with both.
- `check`: FAIL for every FakeTarget that fails the rule, with what kl2's arithmetic makes of it; the summary
  says both boxes and the rooms without a record. Facts in `dyn.json`.
- `build` (`apply` -> `take_off`): such a FakeTarget's controller is taken off its node in the new .prp (the
  node, its entity, its other controllers and every other member stay). `dyn.json` `fake_targets_removed`, a line
  in `dyn.txt` and `graft.txt`. `--keep-fake-targets` leaves it (then `check` fails the result).
- `diff`: works out FROM THE SOURCE BUILD which FakeTargets fail the rule; a subtree outside the squads must be
  the source's as it is, or the source's with exactly those controllers gone (the subtree's fingerprint: names,
  classes, properties, controllers, tree). The new build's `dyn.json` is held against that, no longer believed
  (the review's D3). Every member is compared by name now (the four menu files of the archive were not).
- `fake-fix <build> <out>`: a copy with ONLY those controllers taken off - the .prp member alone, the squads as
  they are - and its own diff. For a build that is not to get the dynamic step, e.g. the tab's Retomoto.
- `fake-test <M01 build> <Retomoto with the parked vans> ...`: the rule against the two facts from the running
  game (GRID: M01's twelve floats; PARKED: 'no record' for van 02 on both boxes) and a lattice that holds the
  rule against kl2's arithmetic. It replaces the first pass's test, which could not tell a wrong box.
- `grid <folder> <96 hex digits | 12 floats | 6 floats>`: a grid read in the running game against the level's
  boxes - for the hook line of section 9.
- The fork: NOT changed from the form that ran live. `FORK_GAP` (commit 76bfdcd of another session, made while
  this was being read: a 0.1 s `TriggerDelay2` before every RandomTrigger, default on there) is 0 = off,
  `--fork-gap S` builds it, and `build` now SAYS in its log which form it made (`fork gap: NONE ...`), because
  `tools/kl_fa_cover.py` builds through `D.build(pre, fin, None)` and so gets this default (the review's D4:
  the other session and CLAUDE.md's line on FORK_GAP have to be told by the lead - not this track's files).
  The timer form has run since (the lead's R7a / R7b / R7c_DM09 on `z_route7\retomoto_full`, 68 gap timers,
  and C3_DM03 on `z_cover3\M03`, 59: four clean rounds, 05:38-06:08), so both forms are run forms and which
  is the default is a choice, not a safety matter.
  One fork, old and new, is the same text: section 4 'OURS' is `z_route` and `z_route4` alike.

One node, old and new:

    ...\F07_Escape_Vehicle_02\V_Van_00\Body\Body_Main   controllers  [FakeTarget, RelayAnimatedVehicleHit]  ->  [RelayAnimatedVehicleHit]
    ...\F07_Escape_Vehicle_03\V_Van_00\Body\Body_Main   controllers  [RelayAnimatedVehicleHit, FakeTarget]  ->  [RelayAnimatedVehicleHit]
    ...\F07_Escape_Vehicle_01\V_Van_00\Body\Body_Main   (the van that is called, at (-1850, 2, 8683))          unchanged

Why taking it off is safe: nothing asks an object for its FakeTarget - the class info global 0x168e3d4 is named
by its own registration only (0xb0269e..), the message ids 0x168e3d0 / 0x168e3cc by the constructor and the
handler 0x692d10; the police find a target through ZCheckVisible's records. The two vans are never called, so
nobody was to shoot them. ASSUMPTION that it loads: a node with one controller fewer is ordinary; no stock
animated van is without one (15 of 15 have it), and none of these builds has been loaded.

The right place for this is `kl_fa_street.place_escape` (not this job's file): take the FakeTarget off a van it
parks. (The first pass also offered 'or do not park it outside the rooms': not advised - with the first rule's
box that advice would have been followed wrongly, and a spare van inside the grid would be a registered
'Mercenary' target.) Until then every Retomoto build that does not go through `kl_fa_bots_dyn.py build` or
`fake-fix` keeps the fault, and `check` says so.

## 7. Builds

All under `<work>\build\z_route4\`. Nothing was written into a folder that was there before: the Retomoto of
the first pass was rebuilt with the tool as it stands into a NEW folder and gave the same archive.
'The tab' below is the OWNER'S tree w_tabC as it stood in the game folder at 05:25 (DM01 `z_route3\M01`, DM02
`z_m02s1\M02`, DM03 `z_hop\M03`, DM06 `z_route\M06`, DM09 `rt_full7\retomoto_full`; every archive compared
member for member, read only). At 06:30 the game folder holds the lead's TEST tree w_tabN instead (DM09 =
`z_route7\retomoto_full`, DM03 = `z_cover3\M03`, the other three unchanged), with w_tabC to go back.

| folder | made by | from | archive sha1 | what it is |
|---|---|---|---|---|
| `M01` | `build` (first pass) | `z_gate\M01` | 58491ae9 | = the tab's DM01 member for member (`z_route3\M01`) |
| `M02` | `build` (first pass) | `z_m02s1\_bots\M02` | a980fff9 | = the tab's DM02 (`z_m02s1\M02`) |
| `M03` | `build` (first pass) | `z_hop\_bots\M03` | 94587886 | = the tab's DM03 (`z_hop\M03`) |
| `M06` | `build` (first pass) | `z_final\M06` | 1d799830 | = the tab's DM06 (`z_route\M06`) |
| `retomoto_full` | `build` (first pass) | `rt_full7\retomoto_full` | acf622dc | superseded by the next line: same archive, but its dyn.txt / dyn.json word the first rule's box |
| `retomoto_full_r2` | `build` (this pass) | `rt_full7\retomoto_full` | acf622dc | room-first bots + routes (42 forks, no fork timer) + the FakeTargets of vans 02 / 03 off |
| `retomoto_tab_fix` | `fake-fix` (this pass) | `rt_full7\retomoto_full` | eed07a72 | THE TAB'S RETOMOTO with only those two controllers off: the .prp member 5,004,744 -> 5,004,652 bytes, the other 29 members and the 32 files beside byte for byte; no routes |

The four maps were not rebuilt: the rule takes nothing off them and no line of the planner or the writer was
touched in this pass (the Retomoto rebuild is the proof that the tool still writes what it wrote). After the
two builds of this pass one line of the rule was tightened (a record counts as a bound's only if its +0x34 is
the bound's place, section 2.1): the boxes are the same on all 14 levels, and `diff` - which works the expected
set out anew from the source - was run on both builds again after it.

Last line of every check, run again on all seven with the tools as they stood at the end (third and last pass
2026-10-11 06:21-06:28: `tools/kl_fa_bots_dyn.py` of 06:13:14, `tools/kl_fa_bots.py` - track A's, saved several
times while this pass ran - of 06:12:17, neither changed during the pass; logs in the scratchpad `fin\out\`;
`kl_maps.py audit` through a wrapper that does not write its two files into the folder; the folders' listings
before and after the checks are the same). The two earlier passes (05:39 and 05:52) gave the same lines but for
M02's count; `check`, `diff` and `fake-test` were run once more at 06:35 after the last (text-only) edit of the
tool and against `kl_fa_bots.py` of 06:31:34: the same lines.

| check | M01 | M02 | M03 | M06 | retomoto_full | retomoto_full_r2 | retomoto_tab_fix |
|---|---|---|---|---|---|---|---|
| `kl_fa_bots_dyn.py check` (the command) | exit 1: FAIL (7 FAIL, 2 NOTE) | exit 1: FAIL (17 FAIL, 4 NOTE) | exit 1: FAIL (7 FAIL, 3 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 7 NOTE) |
| ... of those FAILs, track A's loot-window rule in `kl_fa_bots.check` | 7 of 7 | 17 of 17 (14 of 14 with the file of 05:08) | 7 of 7 | - | - | - | - |
| ... this module's own rules (`check(base=False)`) | PASS (0 FAIL, 2 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 7 NOTE) |
| `kl_fa_bots_dyn.py diff` against the source | only the squad's steps were made anew | the same | the same | the same | ... and 2 FakeTarget controller(s) outside the vision space taken off | the same as `retomoto_full` | (`fake_diff`) only the FakeTarget controllers that fail the rule on the source were taken off |
| `kl_impact.py` | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 |
| `kl_map_guns.py check` | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 |
| `kl_maps.py audit` | PASS (0 must, 1 known) | PASS (0 must, 6 known) | PASS (0 must, 0 known) | PASS (0 must, 6 known) | - | - | - |
| `kl_map_escape.py van-check` | 0 fault(s) | 0 fault(s) | 0 fault(s) | - | - | - | - |
| `kl_fa_bots_rt.py check` | - | - | - | - | PASS (0 FAIL, 6 NOTE); start delay 91.5 s after a blast at 16.5 s; jump list 7; [CrewJoin] places 7 | the same | PASS (0 FAIL, 1 NOTE); start delay 91.5 s after a blast at 16.5 s; jump list 7; [CrewJoin] places 7 |
| members that differ from the source | .buf .gms .oct .prm .prp | the same | the same | the same | the same | the same | .prp |
| beside the archive: the .ini files, the 18 sound / .hti files | byte for byte | byte for byte (M03 with its KLJoin.ini / [CrewHop]) | byte for byte | byte for byte | byte for byte (KLGuns, KLJoin, KLTalk, KLWardrobe) | byte for byte | byte for byte |
| .prm / .ANM / .fxc / .TEX sizes against the source | the same | the same | the same | the same | the same | the same | the same |

Retomoto's room-first hold is kept in both Retomoto builds with routes: `Timer_start_bots` (91.5 s) and the
boardroom's counter both name `Counter_room_clear`, which names the seven first steps of the new chains
(`000_Timer_stagger` / `001_SquadModifier_awake`) instead of `010_DefendBehaviour_to_loot`; nothing else names
them. `retomoto_tab_fix` has the squads of `rt_full7` untouched.

M01 M02 M03 and `kl_fa_bots_dyn.py check`: this module's own rules give 0 FAIL; the command as a whole exits 1
with 7 / 17 / 7 FAIL, every one of them `kl_fa_bots.check`'s loot-window rule ('money object(s) inside the loot
window ... that a bot cannot take there'), which track A put into `tools/kl_fa_bots.py` after the first pass's
runs and was still changing (M02: 14 lines with the file of 05:08, 17 with the one of 06:12). It is a finding
about the bots builds these three were made from - the ones on the tab - not about this step, and it is left
standing: track A's builds (`z_loot3`) are the answer to it. Because that file was being edited, five runs of
`check` between 06:01 and 06:09 died INSIDE `kl_fa_bots.py` (tracebacks at `window_report` and `stage_boxes`,
a half-saved state) and were run again; no result above comes from such a run.

One read fault to know of: at about 05:55 one read of `z_route4\M03\F01_Main.zip` failed inside zlib ('Error -3
while decompressing data: invalid distance code'). The file had not changed (same time stamp, sha1 94587886
before and after, `testzip` clean) and it has read clean every time since (about ten times): a bad read from the
G: drive or from memory, once. Nothing was being written then.

Negative tests of this pass:

- `kl_fa_bots_dyn.py check` exits 1 with exactly two FAIL lines, both the FakeTarget rule, on `z_route`,
  `rt_full7`, `rt_full6`, `z_cover2` and `z_route7` `\retomoto_full` (section 5).
- `kl_fa_bots_dyn.py fake-test <z_route4\M01> <rt_full7\retomoto_full>`: `RESULT (fake-test): PASS (grid control
  1, parked control 1, lattice 2)`; with the six other folders too: PASS (grid 1, parked 2, lattice 8). Without a
  level for a control it says INCOMPLETE and exits 1 (it does not call a level without a FakeTarget a failure).
  The first form of the rule fails both controls: its M01 box is not the dump's, and kl2's arithmetic on its
  Retomoto box gives the parked van a record.
- `kl_fa_bots_dyn.py grid <z_route4\M01> <the dump's 96 hex digits>`: `'sure': the same six floats, bit for bit`,
  exit 0; with the first form's box as the six floats: `NEITHER box is the game's`, exit 1.
- `diff` (scratchpad `fin\d3test.py`: a copy of `retomoto_full_r2` in the scratchpad in which the FakeTarget of
  van 01 - inside the vision space - is gone as well): with a `dyn.json` that names it, the case the first
  `diff` passed, 2 unexpected differences; with one that does not, 1; the untouched build 0. `RESULT (d3test):
  PASS`.

## 8. Assumptions, not done

- PROVEN on one level only (M01): that the grid's box is the union of the bounds' records. For the four other
  builds it is the same reading of the same files; the one-load proof per map is the hook line of section 9.
- ASSUMPTION: a room without bounds is counted by its own record (`all`); DebugRoom is such a room. The rule
  does not lean on it (`sure` is the box).
- NOT READ: the box of a room without a record (section 2.1); the engine's box may be larger than `sure` by
  them. So a FAIL of the rule can be a false alarm for a place outside `sure` (never for the parked vans: the
  dump has their 'no cell'); a PASS cannot be wrong by them.
- By static reading only: nothing sets bit 2 of a room's +0x118; the hidden bit of a slot is the .gms record's.
- ASSUMPTION: the heap behind ZCheckVisible is the same object in every run of one build (section 3).
- Not measured: how often slot 25 runs for a FakeTarget.
- Not done: the fix at its source (`kl_fa_street.py`, another session's file); a rule for '200 records in use
  at once'; what the write hit in the builds without routes; any live run; telling the session that committed
  76bfdcd that the fork timer's default is 0 again (the lead's: section 6).
- Never loaded: a van without its FakeTarget (15 of 15 stock animated vans have one).
- Commit 76bfdcd (the other session's: the fork timer and the gate counter of the room-first build in `parse`,
  `make`, `graph`, `diff`) is kept but for the timer's default; the Retomoto build needs the gate lines. The
  changes of this note are in the working tree, not committed.

## 9. Live check (owner away; TEST hook)

Runs alone cannot tell success from failure (the review's last note, and it is right): the faulty routes build
ran clean three times in four, and the builds without routes carry the same write and have run clean since
2026-10-09. The night's own runs say the same: T7_DM09 (`rt_full7`, 05:12) and R7a / R7b / R7c_DM09
(`z_route7`, the fork-timer build, 05:38-06:08) were four clean rounds of 4.5 min - of builds that ALL have the
two parked targets, so the write was there in each; the timer did not fix anything, the fault just did not
show. The first pass's fallback (the old build twice, then three or ten clean runs) only works if the old
build crashes both times. What decides is memory, read only:

1. Two lines in the TEST hook (not written here - `klhook/` is not this track's):
   - once per level load, when `[0x1535c70]` is not 0: the 48 bytes at `[0x1535c70] + 0x50` as hex (cell size,
     1 / cell size, lo, hi). Then `python tools\kl_fa_bots_dyn.py grid <build folder> <the 96 hex digits>` says
     whether the level's box is the game's, bit for bit. One load per map, no play: this settles the open points
     of section 2.1 (the rooms without a record, DebugRoom, the own-record rooms) for all five maps.
   - once a second from the level's start: the 16 bytes at `[0x1535c70] + 0x146c8`.
     The tab's Retomoto as it is (`rt_full7`): the first dword `ff100110` and a parked van's place
     (-3216.6, -60040.0, 3419.3 or -1577.9, -60040.0, 1102.6) within seconds.
     `z_route4\retomoto_tab_fix` and `retomoto_full_r2`: never a first dword `ff100110`.
   One load of each decides.
2. Every run of a fixed Retomoto must also show what cannot be read offline: the level loads without the two
   controllers, the round reaches GO, van 01 comes and is boarded (`bots: ... aboard`), no `CRASH` line.
   `retomoto_tab_fix` first (it differs from what the owner has played only in the two controllers); then
   `retomoto_full_r2`, where a run counts for the routes only if bots get past the loot wait (with the room-first
   bots the seven start when the room is clear or 91.5 s after the round-start event: watch from about 3 min).
3. If a fixed build fails to LOAD, the only data difference is the missing FakeTarget on vans 02 / 03:
   `kl_fa_bots_dyn.py build ... --keep-fake-targets` (or the source build) tells.
4. The four maps need no new run for this track: their archives are the ones already on the tab.

## 10. The review's points and what was done (2026-10-11, second pass)

| point | what | done |
|---|---|---|
| D1 (must) | `vision_space()` was not the engine's box; a PASS was not evidence | FIXED: section 2.1; the rule, `check`, the comment block and this note rewritten; own re-derivation of both of the review's proofs (the M01 grid from the dump; kl2's arithmetic on the first box gives the parked van a record). Stricter than asked: a box test on the PROVEN part of the union |
| `fake-test` (should) | a tautology; FAIL on a level without a FakeTarget | REPLACED by the two known facts + a lattice; a level without a FakeTarget is only not counted |
| D2 (should) | the tab still has the fault; the source is unfixed | PARTLY, as far as this track's files go: confirmed the tab's DM09 is `rt_full7` member for member; built `retomoto_tab_fix` (only the two controllers off) so the lead has a least-change candidate; `kl_fa_street.py` and the install are not this track's |
| D3 (should) | `diff` believed the new build's `dyn.json`; node-by-node compare lost the tree | FIXED: the expected set comes from the source; fingerprint of the subtree with those controllers removed; negative test `fin\d3test.py` |
| D4 (should) | `FORK_GAP` back to 0 under another session | KEPT at 0 (the brief said to; the forks are not the cause; the form without the timer is the one on the tab; the timer form has run four clean rounds since, so the default is a choice now, not a safety matter) and made LOUD: the build log and `--help` say which form is made. Telling the other session and CLAUDE.md's line: the lead's |
| N1 | M01 M02 M03's check now fails by track A's rule | confirmed, reported as it is (section 7); nothing weakened |
| N2 | 16 bytes is the steady state | section 2 |
| N3, N5 | the full table; a van without its target never loaded | section 8 |
| N4 | the crash dump holds only the pointer | section 2 |
| small inaccuracies | six call sites / four other functions; the whole tree; 0x63c6c0 | sections 1, 2, 2.1 |
| live check | runs cannot decide | section 9 rewritten; the `grid` command for the hook's line |
