# Review of track B (the 0x686a66 crash): `re/crash_686a66.md`, `tools/kl_fa_bots_dyn.py`, builds `z_route4`

2026-10-11, adversarial review, OFFLINE (nothing ran in the game, nothing written in the game folder or in a
build folder; the reviewer's scripts are in the session scratchpad `rev\`). Verdict: **ACCEPT WITH FIXES**.

The cause is right and proven. The data fix (the two parked FakeTargets lose their controller) is right. The five
builds pass. What is wrong is the RULE that is meant to guard against it: `vision_space()` does not read the box
the engine uses, and under the engine's own arithmetic the worker's box would have REGISTERED the parked vans.

## 1. What was re-derived and holds

| claim | what I saw |
|---|---|
| `ZFakeTarget` update writes with an unchecked index | kl2 0x560630 = `ZFakeTarget` vtable 0xbd143c slot 25 (`debug/rtti.py`). `cmp byte [esi+0xa0],0xff / jne / call 0x55cc40`, then both ways out (0x56072e, 0x56076d) do `movzx reg, byte [esi+0xa0]` and `call 0x7143f0` with no test. The four other functions that call 0x7143f0 test first: 0x42a096 (`ZHavokCar`), 0x502726 (`ZHavokLnkObj` / `ZHeli` ..), 0x5dfaa1, 0x6ed13f. (The note says 'five test': it is six call sites, four other functions.) |
| the write is 16 bytes at `this + 0x12ae4 + i * 0x1c` | 0x7143f0: `esi = i*7`, `[ecx+esi*4+0x12ae4] = cell` (from 0x79bae0), `+0x12ae8 / ec / f0 = x, y, z`. |
| registration answers 0xff outside the grid or with 200 records used | 0x59c790: three `(BYTE) ftol((p - lo) * inv)`, `cmp bl,0xf / ja`, `cmp byte,0 / ja`, `cmp cl,0xf / ja` -> `al = 0xff`; else the first record with +0 == 0 among 0xc8, none -> 0xff. 0x55cc40 adds 140.0 (double at 0xb45358) to y before it asks. |
| the 16 bytes in the dump are record 0xff | `KLHook_2.dmp` of 01:34: `[0x1535c70] = 0x7d72b070`; `0x7d72b070 + 0x12ae4 + 0xff*0x1c = 0x7d73f738`; at 0x7d73f738: `ff100110 c54909d0 c76a8804 4555b444` = 'no cell' (bytes 10 01 10 ff = the constant at 0xcdf6d4, written only by 0x79bae0's outside path 0x79bcd9) + (-3216.61, -60040.02, 3419.27). The fault is `mov eax,[edx+0x14]` with edx = 0xc76a8804 = that y. The array block at 0x7d73f970 is intact: `0 0 3 0 6942 6943 6944`. |
| the place and the victim | `z_route\retomoto_full`: FakeTarget on `...F07_Escape_Vehicle_02...\Body_Main` at (-3216.6, -60040.0, 3419.3); slot ids 0x6942..0x6944 = `Squad#08\030_DefendBehaviour_way_c_b\Pos#01..03`, listed in that order by that rout. |
| nothing asks a node for its FakeTarget | 0x168e3d4 is named at 0xb0269e / 0xb026e7 / 0xb02727 only (its registration); the message ids 0x168e3d0 / 0x168e3cc only by the constructor (0x4048cb, 0x4048ec) and the handler 0x692d10. |
| classes of the stack | 0x686920 `CPPScript::ZDefendBehaviourGoal` slot 2, 0x570e60 `CPPScript::ZSquad` slot 4, 0x4b4af0 `ZDefendBehaviourRout` 14, 0x457720 slot 34, 0x4ebed0 `ZBaseBehaviourRout` 26, 0x4d86e0 `ZRandomTrigger` 26, 0x71e250 / 0x744c30 `ZTriggerDelay2` 26 / 25. (0x63c74d lies in the function at 0x63c6c0, not 0x63c5c0.) |
| every Retomoto build since play2 has the two | counted: `play2` (514c4689), `y_loot\retomoto_loot`, `rt_ai2`, `rt_full6`, `rt_full7`, `z_cover2`, `z_route`, `z_route7`: 3 FakeTargets, vans 02 / 03 at y -60040. |

## 2. Defects

### D1 (MUST) `vision_space()` is not the engine's vision space; the rule's PASS is not evidence

Two independent proofs.

**(a) A dump holds a real grid.** `%TEMP%\kl_triage\20261008_200513\KLHook_2.dmp` (M01_FA_A converted whole, crash
at 73 %; the dump names `M01FAA_Out_Street_02a`) has the ZCheckVisible object (vtable 0xba7ae4) with its grid at
+0x50: cell (3612.139, 18400.004, 3239.385) = (dx/16, dy, dz/16),

    lo  -20224.4765625   -200.0009765625   7929.8486328125
    hi   37569.75390625  18200.001953125  59760.0078125

The union of M01's **.rmi room boxes** (record +0x28 centre, +0x40 half; `c - h`, `c + h` in float32; without the
backdrop and without F07's `DebugRoom`, which that level did not have) is **bit-identical on all six floats**
(`rev\exact.py` on `z_route4\M01`). `vision_space()` gives for the same map lo (-27549, -398, 0) hi (49140, 18203,
72141): the item bounds of the root's .oct room tree are the rooms' CONTENTS (they equal the .rmc boxes), 7,300 to
12,400 units wider on four sides. So the engine joins the boxes of each room's list at +0x38 (0x541f5c..0x541fb0)
and those are the .rmi boxes - exactly the part the worker marked 'counted by its own box here'.

**(b) kl2's arithmetic contradicts the worker's box on the crash build itself.** The cell is
`(BYTE) ftol((p - lo) * inv)`, ftol = 0xa8d330 = `cvttsd2si` (truncation TOWARD ZERO), and there is ONE cell in y
with `inv = 1 / (hi.y - lo.y)` (tail of 0x541e40; the dump above confirms it). 'Outside in y' therefore means
`y >= hi.y` or at least one whole box height below `lo.y`. With the worker's Retomoto box (y -19804..68707):
(-60040 + 19804) / 88511 = -0.45 -> cell 0 -> **the parked van registers and nothing is written**. With the .rmi
boxes (x -87017..8596, y -10000..28723, z -99949..52922): -50040 / 38723 = -1.29 -> 0xff -> what the dump shows.
The note's 'the parked targets are 40,236 below it ... the dump's "no cell" agrees' is false as arithmetic.

Consequences:
- The rule fails the two vans only because they are outside BOTH boxes by a plain box test. It passes places the
  engine cannot register (`rev\counter.py`, `z_route4\retomoto_full`): the same van parked 400 m ABOVE the road
  (y +40,000), a van at x +20,000, a van at z 60,000 - all 'inside' for `check`, all 0xff for kl2.
- `fake-test` cannot see this: it tests the three lines of `outside()` against a point 60,000 lower and the box's
  centre, which holds for any box.
- 're/crash_686a66.md' 2, 5, 8 and the comment block at `VISION_SKIP` state the wrong box, the wrong sizes
  ('76,000 to 114,000 units across': M01 is 57,794 x 51,830, M02 49,522 x 20,000 with the van 3,088 from the z
  edge, M03 64,048 x 93,528) and a control that does not control (27 of 27 stock targets are inside either box).
- The advice 'or do not park it outside the rooms' would be followed with this box.

The conclusion survives: with the .rmi boxes and kl2's arithmetic the remaining FakeTargets register - Retomoto
van 01 (-1850, 2, 8683) cell (14, 0, 11); M01 (7, 0, 4); M02 (8, 0, 2); M03 (5, 0, 12); M06 has none; all 27
stock ones (F01 F04 F05 F07 F09) too. A place inside the .rmi union registers under any larger box as well.

Fix: read the vision space from the .rmi boxes of the rooms that are not backdrops (the rooms come from the whole
tree: 0x883840 is a pre-order walk, M01's rooms sit three levels down - not 'children'); judge a place with kl2's
arithmetic or, stricter, a box test on that union; say what is NOT known: the box of a room WITHOUT an .rmi box
(the engine takes 0x8849b0 of the room's own slot; Retomoto has two such rooms, M02 one, M03 one, stock F07 one -
on Retomoto it cannot be the contents box of `M09_B_Skyscrabers_01a`, or the vans would have registered), the
hidden test (locator +0x3c & 0x400 against the .gms record flags: no room of the five builds has the bit),
whether `DebugRoom` counts, and the filter the note leaves out: vtable +0x2fc = bit 2 of `[room+0x118]` skips a
room (0x541f36..0x541f44). Replace `fake-test` by the two facts that are known: M01's six floats, and 'van 02 of
`z_route\retomoto_full` gets 0xff'.

### D2 (SHOULD) the owner's tab still has the fault, and the source is not fixed

`<DD>\KLExpansion\Maps\DM09\F06_Main.zip` (manifest: built 2026-10-11 03:37:50; no routes, 3 FakeTargets, read
only) has vans 02 and 03 at y -60040: record 0xff is written every frame of every Retomoto round the owner plays
now. `kl_fa_street.place_escape` still makes it, so every Retomoto build that does not pass through
`kl_fa_bots_dyn.py build` keeps it (`z_route7` of commit 76bfdcd too). The worker said so; it is the first thing
to act on. DM01 on the tab is 58491ae9 = `z_route4\M01`.

### D3 (SHOULD) `diff` believes the new build's own dyn.json

A subtree outside the squads may now differ when dyn.json of the NEW build lists a FakeTarget as taken off. It is
not checked against the SOURCE that the one taken off stood outside (a build that dropped van 01's target and
listed it would pass). The node-by-node compare that replaces the subtree fingerprint there also drops the
parent / child structure (pre-order and count only). Fix: `fake_targets(source)` must give the same paths.

### D4 (SHOULD) the default of a shared module was turned back under another session

`FORK_GAP` 0.1 (commit 76bfdcd) is 0 again. The ground is sound (the cause is not the forks; the timer form never
ran) and the brief allowed it, but `tools/kl_fa_cover.py` builds through `D.build(pre, fin, None)`: that session's
next cover / route build silently comes out without the gap its notes (CLAUDE.md b0498a3) describe. Tell it
before either side commits.

### Notes

- N1. The reported check lines for M01 M02 M03 cannot be reproduced on the tree as it stands:
  `kl_fa_bots_dyn.py check` exits 1 with 7 / 14 / 7 FAIL. All of them are `kl_fa_bots.check`'s new loot-window
  rule (track A, `tools/kl_fa_bots.py` saved 04:54, after the worker's runs). With `base=False`: 0 FAIL and
  2 / 4 / 3 NOTE as reported. Those archives are the ones on the tab, so it is track A's finding about the tab.
- N2. 'Exactly 16 bytes' is the steady state. On the first frame 0x79bae0 reads the four bytes at +0x146c8 as the
  OLD cell and, if they look like one (x <= 15, y 0, z <= 15, slot < 0x3f), takes a slot off that cell's list
  inside the grid (0x789d00). And `ZFakeTarget` slot 26 (0x692d10) calls the unregister 0x669620 with the same
  unchecked index when its health falls below 0: a zero dword at +0x146c4. Not reachable for the vans (health -1).
- N3. The full table (200 records) stays uncovered, as the worker says. Records are given back (0x669620, five
  callers), so it is a peak, not a total.
- N4. 'The dump has ... (ZCheckVisible, vtable 0xba7ae4, 0x14120 bytes)': the dump of 01:34 holds the pointer
  only; the object is not in it. The vtable is confirmed by the dump of 2026-10-08.
- N5. That a van loads without its FakeTarget is still unseen (15 of 15 stock animated vans have one).

## 3. Checks re-run on `z_route4`

| | M01 | M02 | M03 | M06 | retomoto_full |
|---|---|---|---|---|---|
| archive sha1 | 58491ae9 = `z_route3\M01` | a980fff9 = `z_m02s1\M02` | 94587886 = `z_hop\M03` | 1d799830 = `z_route\M06` | acf622dc |
| `kl_fa_bots_dyn.py check` (own rules) | 0 FAIL, 2 NOTE | 0 FAIL, 4 NOTE | 0 FAIL, 3 NOTE | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) |
| ... with track A's base check now | FAIL (7) | FAIL (14) | FAIL (7) | PASS | PASS |
| `diff` | only the squad's steps | same | same | same | ... and 2 FakeTarget controller(s) taken off |
| `kl_impact.py` | problems: 0 | 0 | 0 | 0 | 0 |
| `kl_map_guns.py check` | problems: 0 | 0 | 0 | 0 | 0 |
| `kl_maps.py audit` (writes redirected) | PASS, 1 known | PASS, 6 known | PASS, 0 known | PASS, 6 known | - |
| `kl_map_escape.py van-check` | 0 fault(s) | 0 fault(s) | 0 fault(s) | - | - |
| `kl_fa_bots_rt.py check` | - | - | - | - | PASS (0 FAIL, 6 NOTE); start delay 91.5 s |

A rebuild of Retomoto with the tool as it stands gives acf622dc again. The room-first gate is kept:
`Counter_room_clear` (named by `Timer_start_bots` and the boardroom counter, nothing else) names the seven first
steps `000_Timer_stagger` / `001_SquadModifier_awake`, which alone name `010_DefendBehaviour_to_loot`.
Negative: `check` exits 1 with exactly two FakeTarget FAILs on `z_route`, `rt_full7`, `rt_full6`, `z_cover2`,
`z_route7` `\retomoto_full`. Only `z_route4` was written during the worker's run (file times).

## 4. Live check

Runs alone cannot tell success from failure: the faulty build ran clean three times in four, and the builds
without routes (the write is in them too) ran clean for two days. The worker's fallback (old build twice, then
three or ten clean runs) only works if the old build crashes both times; otherwise ten clean runs prove nothing.

Only the memory line decides, and it should carry more than the worker asked for (read only, TEST hook):
- once per level load: the 12 floats at `[0x1535c70] + 0x50` (cell, inv, lo, hi) - the real vision space of every
  map, which settles D1's open points with one load per map and no play;
- once a second: the 16 bytes at `[0x1535c70] + 0x146c8`. Old Retomoto: `ff100110` + a parked van's place from the
  first seconds. `z_route4\retomoto_full`: never a first dword `ff100110`.
A run must also show: the level loads without the two controllers, the round reaches GO, van 01 comes and is
boarded.

## 5. What was done about each point (the track's finishing pass, 2026-10-11 05:20-06:30; appended by the finisher)

Offline, own files only (`tools/kl_fa_bots_dyn.py`, `re/crash_686a66.md`, `re/bots_dyn_build.md`); nothing
committed. Scripts and logs: scratchpad `fin\`. Every 'must' and 'should' is fixed or answered; none is refuted.

- **D1 (must) - FIXED.** Both proofs were re-derived first (`fin\grids.py`: the 2026-10-08 dump is the only one
  of 107 that holds the grid, twelve floats as quoted; `fin\oldbox.py`: the first box on M01 is 7,324 to 12,381
  wider on four faces, and kl2's arithmetic on the first Retomoto box gives the parked van cell (5, 0, 6), a
  record). `vision_space()` now reads the `.rmi` records. It goes one step further than the fix asked for: the
  records are split by what the dump proves - the list at a room's +0x38 is its ZBOUND children, and M01's six
  faces all come from bound records - so the rule's box (`sure`) is the bound records alone (a bound's record
  names its bound: +0x34 is the ZBOUND child's place in 582 of 582 such records on 14 levels, `fin\tie.py`);
  `all` adds the rooms that have one record of their own (the unproven kind; on Retomoto it doubles the width). The rule is a
  box test of the REGISTRATION place (the node's + 140 in y, 0x55cc40) against `sure`, which is stricter than
  kl2's arithmetic on either box; kl2's arithmetic is printed beside every target. Stated as not known: the box
  of a room without a record, the own-record rooms and DebugRoom, the hidden bit's source, turned records.
  The +0x2fc filter was read: bit 2 of +0x118 is 0 from the constructor and no code that could reach a room
  sets it (static reading). The counterexamples (y +40,000, x +20,000, z 60,000) fail now. 27 of 27 stock
  targets and the four remaining ones of the builds pass on `sure` alone.
- **`fake-test` (should) - REPLACED** by the two facts (GRID: M01's twelve floats bit for bit; PARKED: 'no record'
  for van 02 on both boxes) and a lattice that holds `outside()` against `grid_cell()`. A run without a level
  for a control says INCOMPLETE; a level without a FakeTarget is no failure. New `grid <folder> <floats>` takes a
  grid read in the game - for the hook line of section 4.
- **D2 (should) - PARTLY, and it stays the lead's first thing to act on.** Confirmed read-only: the tab's
  `DM09\F06_Main.zip` (03:38:10) is `rt_full7\retomoto_full` member for member, and DM01 DM02 DM03 DM06 are
  `z_route4\M01..M06` member for member. New `fake-fix <build> <out>` takes only the failing controllers off;
  `<work>\build\z_route4\retomoto_tab_fix` (eed07a72) is the tab's Retomoto with that and nothing else (the .prp
  member, 92 bytes shorter; every check passes; never loaded). `kl_fa_street.place_escape` is another session's
  file and the install needs the owner: not done here.
- **D3 (should) - FIXED.** `diff` works out from the source which FakeTargets fail the rule, compares each
  subtree outside the squads by fingerprint against the source's with exactly those controllers removed, and
  only then holds the new build's `dyn.json` against what it saw. Negative test `fin\d3test.py`: the build that
  also dropped van 01's target is refused with and without a `dyn.json` that names it. Every member of the
  archive is compared by name now (the four menu files were outside the old list).
- **D4 (should) - ANSWERED, not undone.** `FORK_GAP` stays 0: the brief asked for it if the gap proved unneeded
  (it is: the forks are not the cause), and the form without it is the one of the owner's tree. What was wrong
  was the silence: `build` now says which form it made (`fork gap: NONE ...`), the usage text names the old
  default and how to get it. Since then the timer form HAS run (the lead's R7a / R7b / R7c_DM09 on `z_route7`
  and C3_DM03 on `z_cover3\M03`, 05:38-06:08: four clean rounds), so both forms are run forms and the default
  is a choice, not a safety matter: the lead's, with the session that committed 76bfdcd and CLAUDE.md's line.
- **N1** confirmed and reported as it stands: M01 M02 M03's `check` exits 1 with 7 / 17 / 7 FAIL (14 for M02
  until track A's file changed again about 06:05), every line track A's loot-window rule; own rules 0 FAIL.
  Nothing was weakened or switched off.
- **N2, N4, the small inaccuracies**: corrected in `re/crash_686a66.md` 1, 2, 2.1 (N2's second path re-read:
  0x692d10 leaves at once for health -1). **N3, N5**: stand, section 8 there.
- **Live check**: section 9 there is rewritten on this review's section 4.
- Builds: nothing written into an existing folder. `retomoto_full_r2` is the first pass's Retomoto rebuilt with
  the tool as it stands: the same archive (acf622dc). The four maps were not rebuilt (nothing of the planner or
  the writer changed; their archives are the tab's).
