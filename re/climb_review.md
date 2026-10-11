# Review of track F - the wall climb (re/climb.md, tools/kl_fa_climb.py, klhook/klclimb.c, build z_climb\M03)

2026-10-11, adversarial reviewer. OFFLINE: no game was started, no game folder written, nothing committed, no source
file changed; this file is the only thing written in the repo. The build folder `<work>\build\z_climb\M03` was read
only (`kl_maps.py audit` writes two files into the folder it audits, so it ran on a scratch copy, deleted afterwards).
Everything below was re-read in the two exes with my own disassembly (scratchpad `rv_climb\d.py`, `x.py`: capstone
through `debug\kl.py`, both exes) or re-measured with my own scripts; where I only took over a number I say so.
Status words: **read** = seen at the address given; **measured** = counted by a script of mine; **reasoned**.

## Verdict: ACCEPT WITH FIXES

- The account's three verdicts hold (vault rule, Dead Men's climb, no player half and no clips in Dog Days). I
  found no stock counterexample.
- The level's half is sound: only the `.ANM` member differs, the old `KLJoin.ini` is a byte prefix of the new one, the
  AI heisters' drop link is in the mesh, every check's last line reproduces. **K0 can run as it is.**
- **`klhook/klclimb.c` must not go to K2 as written**: it ends the climb without the step every animated move of the
  player in kl2.exe ends with (the character proxy is put at the node, `0x4af5b0`). By the code read, the first
  ordinary movement step after the climb then takes the player back to where the proxy stayed - the foot of the
  wall. The account describes the vault's end as 'collision on' only; that is where the gap comes from. Four
  further weaknesses of the file are listed as *should*.
- K2 as proposed cannot tell that failure from success by its log line; it needs a later line and a later picture.

## 1. The three claims, re-derived

### 1.1 What makes an obstacle vaultable in Dog Days, and the limits (kl2.exe) - CONFIRMED

- Vault test `0x7a8480` (read whole): `[player+0x2954]` or not in cover (`0x40f840`) -> no; side `0x7a26d0`;
  `[side+0x3c] & 0x1000` -> no (`0x7a84ba`); **`& 0x800` -> yes at `0x7a84c5..0x7a84cd`, nothing else looked at**.
  Otherwise: box type `[box+0x4c] == 1` no, car byte `[box+8]` no, BaseMove byte `+0x1e70` no, ability `0x80ac10(0x10)`
  no, distance `0x639bd0` over 100.0 (`0xb3dde8`) no; then two overlap queries `0x475dc0`: at feet + 150.0
  (`0xb31878`) between him (+-50 along the face) and the landing = depth + d + 50.0 (`0xb71b60`), and a fan to depth +
  d + 110.0 (`0xb464c0`), +-40, at + 30.0 (`0xb45350`). No floor is looked for.
- Where the 0x800 comes from, `0x440de0` (read): only for a box with a modifier (`[box+9]`); top state 1 / 3 / 4 ->
  0x40; and **only when `[box+0x4c] != 1`** (`0x440ff9`, `0x441018`, `0x441037`, `0x441056`): 2 -> 0x80, 3
  (`ON_VAULT_ON`) -> 0x800, 4 and 5 -> 0x1000. A high box never gets 0x800.
- A box is a cover candidate only with `|player y - (centre y - half y)| <= 50` (`0x797634..0x797654`); the prompt
  bit 0x10 is set at `0x58fc01..0x58fc12` after `0x7a8480`.
- Stock (measured on the reader's `covers.json`, analysed again by me): 81 boxes have a forced-vault top, 80 low
  ones **86.3 .. 107.0 high** (median 100.0), no scaled box among them; the one high box (L01 `CoverBoxH_110`, 200
  high) is the case the code ignores. No forced vault on anything taller than a low cover: no counterexample.
- So verdict 1 stands: by the rule yes (one flag), as a climb no (the vault's end place is at the player's own
  height, its clip's root does not rise).

### 1.2 How the player is moved (kl2.exe) - CONFIRMED, WITH ONE OMISSION THAT MATTERS

- Vault start `0x6a27e0` (read): leave cover `0x5fcb80`; a phantom; `[player+0x2d60] = 0`; the slot by name, 2M when
  the way is over 175.0 (`0xb5820c`, `0x6a29d4`); clip `0x59d550`; **collision off, vtable +0x560, at `0x6a2a44`**;
  `Play(clip, 1)` vtable +0x204 at `0x6a2a5d`; **`AlignTo(rot, pos, to - from - 1)` vtable +0x208 at `0x6a2a8a`**.
  (`0x6a2a65` reads through the CHANNEL Play returned, not through the clip.)
- `AlignTo 0x80fdc0` (read): channel by `0x760120` (one of 16 slots, state 1 or 3, flag 0x8000, clip record byte +8
  bit 0x40), none -> 0; start `[this+0xe8]` = the channel's frame, target `[this+0xec]` = frame + frames clamped to
  the channel's end; the clip's root at the target (`0x5a5030`), the wanted transform and the node's own
  (`0x857110`) give the correction at `[this+0xb0..]`; what is applied so far `[this+0x94..]` is reset; channel flag
  0x200. The update `0x50ac80` moves the node only for a channel with flag 0x600 (`0x50b09e`); fraction = (frame -
  start) / (target - start) (`0x50b304..0x50b331`); when the target has passed the fraction is 1, start := target,
  target := the channel's end (`0x50b11a..0x50b131`) and the correction is cleared (`0x50b4cb..0x50b506`): the clip's
  own root motion goes on. A second AlignTo on the same channel starts from the node as it then is: the two-step
  form is consistent with the code (no game routine does it; it stays an assumption until seen).
- Collision switch (read): `0x5d6200` = `0x8c5270` (`++[player+0x7b4]`, `[player+0x7a5] = 0`), **also `[player+0x968]
  = 0`** (not in the account), body `[[world+0x11840+4*[player+0x27cc]]]` to layer 0xc by `0x40ed30`; `0x686600` =
  `0x8b41c0` (count down, not below 0; `[player+0x7a5] = 1` at 0) and layer 5 - set whatever the count is.
- `StartMiniAnim 0x5ea340` (read): as the account says - `[player+0xbe0]` -> `0x8b7410`, StopAction, `[player+0x2758]
  = 0`, pool `0x15151c0`, constructor `0x6b2970` (slot -> +0x18, third argument -> +0x1c, fourth -> +0x25), StartAction
  with whatever the pool gave (null when empty), `[player+0xdbc]` -> `0x4c1a70`; `ret 0x10`. Start `0x76d1d0`: no clip ->
  `[player+0x2758] = 1`, return 0, and the dispatcher's start `0x672d00` cleans up (`0x595b70`: End, then delete).
  Its channel-ended slot `0x42b7f0` returns byte +0x24 when `endWithClip` is set: ANY channel end reported to the
  dispatcher (`0x8f0df0` -> slot 7 `0x5d0260`) ends it; the byte is 0 only around its own Play.
- The game's own caller: `0x5022c0` `(vtable +0x388 == 0 and [[player+0x2940]+0x24] == 0) -> StartMiniAnim([player
  +0x25b0], 0, 0, 1)`, called at `0x60b5c2` from `0x60b230`, the routine with the string `DisableTinitus`
  (`0x60b3e5`): players within twice a radius of a blast. So 'called from standing and walking players in ordinary
  play' is right in substance (it is the stagger at an explosion); its guard is **down state == 0**.
- **THE OMISSION.** The vault's End `0x82f780` is not 'collision on': it calls `0x594960`, **`0x4af5b0`** (`0x82f796`),
  then vtable +0x564 (`0x82f7a6`), `0x74a120`, removes the phantom, and `0x82cc40` when `0x6a88f0` holds.
  `0x4af5b0` (read): `if [player+0x7d0]: p = world place of [player+4] (0x7b3020) * 0.01 (0x408cf0, 0xb29010);
  0xa768b0([player+0x7d0], p)`, and `0xa768b0` is `[this+0x30]->0x9fc110(p, [this+0x5c] + [this+0x58])` - the shape
  of Havok's `hkpCharacterProxy::setPosition` (phantom, keep distance + contact tolerance). **Every routine of
  kl2.exe that ends an animation-carried move of the player calls it**: `ZFFActionVaultOver` End; `ZFFActionJumpOver`
  End `0x5c8f70` (`0x5c8fa3`, then vtable +0x564); the mini cutscene's player act end `0x447bd0` (`0x447bf2`, then
  +0x564); `ZFFPlayerMovementFall`'s clip-end callback `0x4815c0` (+0x564, then `0x481600`); `ZFFActionExitVehicle`,
  `ZFFActionLeaveMountedWeapon`, `ZFFPlayerMovementRappel`, `...Die`, `...StandCover`; leave cover `0x5fcb80`
  (`0x5fcc27`); the placement `0x82cc40` (`0x82ccb3`); the jump point `0x8f3fa0`. 31 call sites.
  `ZFFActionMiniAnim`'s End `0x6fb600` only stops the channel: the game never carries a player with it.
  Why it matters (read): the movement step `0x6d1ad0` (`ZMovementBase` slot 33; `ZFFPlayerMovementBaseMove` has the
  same entry, vtable 0xbb56bc + 0x84) takes the node's place, writes a velocity (`* 60`) into `[player+0x808]`, runs
  the physics step vtable +0x680 = `0x4d1310` (proxy integrate `0x87fb30` or `0x907440`, then the body is put at the
  PROXY's place: `0xa768a0` -> `0x9fe840`) and makes its result from the proxy's place (`0xa768a0` at `0x6d1b73`).
  A proxy left at the foot of the wall is what the next step moves from. Whether the proxy is carried along while
  the collision is off was not read; the game does not rely on it anywhere.

### 1.3 What Dead Men's climb reads (kaneandlynch.exe) - CONFIRMED

- Vtable `0x966c44`: slot 14 `0x605b50` (test), 15 `0x602f30` (enter), 19 `0x603160` (channel ended), 20 `0x603340`.
- Table `0x603340` (read; four slot handles on the stack, three 16-byte records at this+0x68): {Low, Low,
  Sprint_Low, Sprint_Low, 120.0, 81.0}, {Medium x4, 170.0, 47.0}, {High x4, 220.0, 47.0}.
- Test, the local player's part from `0x605dae` (read whole): `[player+0xc68]`, `0x7d5660`, `0x5e7850`, 0.5 s since
  `[player+0x1414]`, `[player+0x1420] < 0.75 * [player+0x141c]` (`0x5e8a90`, `0x93ead0`), `[player+0x132c] == 0`,
  movement 0 or 0xd, and bit 5 of `[player+0x7d0]` latched one frame earlier (`[this+0xe8]`). Rays through
  `[0xbc1d34]` vtable +0x2c with flag words 0x20 (probes, headroom, face) and 0x28 (the clear way): four straight
  down 310 (`0x96703c`) from feet + 310 (`0x967040`), the first hd in front, then 15 further each (`0x95e920`); per
  top, a lower one than the last skipped (`0x6060c8`); clear way from 15 behind at top + 15, **d + 30 long - it ends
  15 past the probe, not 30** (`0x606128..0x60615b`; the tool has it right, re/climb.md 2.1 says 30); headroom 180
  (`0x96020c`) from top + 1, a hit refuses all (`0x606200`); a face from 10 behind at top - 1, d + 20 long, must hit
  (`0x6062a6`); h > 25.0 (`0x93f720`, `0x60638d`); first record with height >= h (`0x6063af`).
  P1 = (the face hit's x, z; feet y) + back vector * distance (`0x6063f2..0x606409`), P2 = P1 + (0, h, 0)
  (`0x605d92`), the matrix from his own back vector (`0x42fba0`). No name, flag, controller or link is asked for.
  ('No level data' means no marker: the rays see collision classes, and the level's hero-only collider over piece
  `_03` is how the designers forbid it. The tool counts every triangle, as it says.)
- Enter (read): frames of events 5 and 6 (`0x5bfa00`), fall-backs half the clip / half the rest; `Play(clip, 1, 0,
  f5, 1.0)` - the clip is played only TO event 5 - and `AlignTo(matrix, P1, f5)` (vtable +0x20c). Channel ended
  (`0x603160`): `Play(clip, 1, elapsed * 25, frames - 1, 1.0)` and `AlignTo(matrix, P2, f6 - from)`; the second end
  leaves the movement. Two channels, two alignments; the hook's one channel with two alignments is the same
  result by the code of 1.2.
- Dog Days' NPC half `0x4a5160`: 40 / 20 start tolerance, 160.0, 170.0, the table words +4 / +8 / +0xc / +6 / +0xe,
  event 6 by `0x4a75d0`, `0x59d550` - as the account says.
- Measured, my scripts: link kinds Dead Men {1: 195, 2: 203, 3: 34, 6: 25}, Dog Days {2: 192} in 12 levels;
  `M03_FA_A` has one link (kind 6, a 1,215 drop far from the wall); `M03_A` has the twelve wall links of 2.2 exactly
  (yard -> top 184.5 by kind 1 at x -3210 and -2938, both inside `[Climb]`). 0 of 21 Dog Days `.ANM` have a clip or
  slot with 'Climb' / 'Ladder'; all 20 Dead Men files have them.

## 2. The tool and the build

Re-run (last lines; all equal the planner's):

| check | last line |
|---|---|
| `kl_fa_climb.py check z_climb\M03` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)` |
| `kl_fa_climb.py check z_hop\M03` (control) | `RESULT (kl_fa_climb): FAIL (3 FAIL, 8 NOTE)` |
| `kl_fa_bots_dyn.py check z_climb\M03` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 3 NOTE)` - the same seven loot-window FAILs as `z_hop\M03`; the two outputs differ in the `.ANM` size alone (diff of both) |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_maps.py audit` (on a scratch copy) | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` | `byte-identical: 41 of 41` |
| `cl /Zs /W4` of a scratch file including `klhook.c` (as of 06:46, with `klvis.c`) then `klclimb.c` | exit 0, no warning from `klclimb.c` |

Measured on the two folders (`rv_climb\cmpbuild.py`, `anmchk.py`, `links.py`):
- 31 members, same names, order, dates; **only `F01_Main.ANM` differs** (22,202,616 -> 22,343,864); zip sha1
  2c93ab68.. as reported. Beside the archive: `KLJoin.ini` (the old 776 bytes are a byte prefix of the new file),
  `steps.json`, `dyn.json` (see N4), `audit.*`, and the two new `climb.*`.
- The merged file: the base's clip records, data, names, slot names are prefixes; 12 new records with data offsets,
  event offsets (= data - 8 x events) and sizes inside the block; frames 25 a second; bones up to entry 64 of 156;
  the three lists of Kane / Lynch are Dead Men's `PlayerCharacter` lists pair for pair; slot ids **2505 High**, 2506
  Low, **2507 Medium** (the build's own `climb.json` says the same). re/climb.md 4.2 has High and Medium the other
  way round, and so do the expected lines of K1 / K2 and the sample log in klclimb.c ('High = id 2507'): the live
  line will read 2505. The hook looks the id up by name, so nothing but the expectation is wrong.
  A set without the slots is safe: `0x876940` tests the slot id against the set's table length.
- The condition bits: Dog Days' own `Fall_1m` / `Fall_2m` lists of Kane are `[(0x10, ..Unarmed), (8, ..Unarmed),
  (0, default)]`, identical to Dead Men's `PlayerCharacter` - the assumption 'bits 8 / 0x10 mean the same' has a
  stock example behind it.
- The mesh of the build still has its one link: kind 2, cost 242, (-1704, 220, -766) -> (-1700, 150, -534).
- Nothing near the yard side of the wall can be taken as cover (no `*CoverBox*` node in x -3700 .. -1000, z -1000
  .. -300); the exit box (z from -540, x -3592 .. 4408) covers the street beyond both stretches.
- `kl_fa_climb.rule` against 1.3: probes, clear way (15 behind, d + 30), headroom, face (10 behind, d + 20), 25, the
  table - line for line the code.

Nothing here can crash a load that the graft's own join could not: the code path is `kl_anmjoin`'s. Nothing here
touches the AI heisters.

## 3. klclimb.c against the exe

Calling conventions (read): `0x5ea340` thiscall + 4, `ret 0x10`; `0x80fdc0` + (rot, pos, float), `ret 0xc`, reads 9 +
3 floats; `0x5d6200` / `0x686600` / `0x8aef30` no stack argument; `0x55f8f0` ecx / edx only, writes 9 floats; `0x619790`
+ 6, `ret 0x18`, argument order (cover, left, pos, rot, given, writeBack); `0x59d550` + 1, `ret 4`. All as the file
calls them. The 7 x 14 identity bytes and the four vtable entries are the exe's (compared byte by byte). The slot
table read, the event table read and the clip record fields are the game's (`0x68a730`, `0x4a75d0`, `0x76d252`).
No call is made off the game's thread; `Dry=1` reaches no call (every path checked); with `Enable=0` the two
functions return at once. No write of its own.

### Defects

**M1 (must) - the climb ends without the proxy sync.** `klq_follow` calls `0x686600` alone when the action is gone
(and after its own stop). Section 1.2: the game puts the character proxy at the node (`0x4af5b0`) at the end of
every such move, and the movement step works from the proxy. As written the expected live picture is: the clip
plays, the `over after ~2080 ms: node (x, 404 .. 428, -581)` line is printed - and with the next movement step he
is where the proxy was. Fix: `0x4af5b0` (thiscall, no argument, plain `ret`; first bytes `55 8b ec 83 e4 f0 83 ec
1c 56 8b f1 83 be`; it tests `[player+0x7d0]` itself and reads `[player+4]`) on the player immediately before
`0x686600` in both end paths of `klq_follow`, added to `klq_code`; and re/climb.md 1.3 / 3 / 4.3 corrected (the
vault's End, the list of calls).

**S1 (should) - the end path does not re-test what the start path tested.** `klq_refuse` reads the physics world
and the body entry before the start; `klq_follow` calls `0x686600` (which dereferences `[[sys+0xac]+0x52cc]` and
`[[world+0x11840+4*idx]]` with no test) one or more ticks after the action went - after a death, a round end, a
level being taken down - on `vtable + registered` alone. The table is append-only (`0x4adce0`: count at +0x1183c,
5,000 entries) so the entry itself stays, but the world pointer and the node are not re-read. Re-run the reads of
the last lines of `klq_refuse` (and the node for M1's call); if they fail, call nothing and say so.

**S2 (should) - the time-out is wall clock.** `limit = frames * 40 + 1500` ms against `GetTickCount`. A pause
during the 2.08 s (the window not in front - CLAUDE.md: Arcade pauses, the main loop only pumps messages; the
pause menu) longer than the margin makes the first tick afterwards stop the action in mid clip. Count the
channel's frame not advancing over game ticks instead, or add the gaps between game ticks to `began`.

**S3 (should) - cover and the down state.** Movement kind 3 includes LOW cover (cover is not a movement of its
own), and StartMiniAnim does not leave cover as the vault's start does (`0x5fcb80`). Refuse when `[player+0x2954]`
or bit 0x80 of `[player+0x818]` (what `0x40f840` / `0x6e2740` / `0x780b80` test). The game's own caller asks for
down state `== 0`; `klq_refuse` lets 1, 10 and 14.. pass - take the game's test.

**S4 (should) - Mode=vault / Fallback.** By the account's own reading the vault may free itself inside its start
when begun outside cover (use after free in game code, not a refusal), and what its start takes for granted
(`0x5fcb80`: `[player+0x2810]`, `[player+0xccc]`, the phantom; `[player+0x2d60] = 0`) is not among the pointers the
file tests although the top comment says every one is. Settle 'who reports a replaced channel' by reading before
K6; until then K6 is not a check to run on the owner's PC unattended.

Notes on the file: the edge class is fixed from `Floor=` while the rise is measured from the feet (a foot 40 off
the floor near a class border plays the other class's clip); `idx > 0x400` is the file's bound, the game's is
0x1388; he is turned square to the wall where Dead Men keeps his heading; the hook's reach 15 .. 75 goes 5 past
Dead Men's last probe (70).

## 4. Refutation attempts (stock counterexamples)

- A forced vault on something tall: none (1.1).
- A Dog Days file with the clips or slots: none of 21 (1.3).
- A Dog Days mesh with a kind-1 link: none of 192 links (1.3).
- A stock Dog Days clip that RAISES a person by root motion (the plan assumes the engine does that for a player):
  there are some - `MiniCut_ToolBox/Run_Up_On_Car_And_Fire_Default#*_Enter_Part2` (+96; L01, L07, L09),
  `L04_In_The_Tube#Kane_01_Leave` (+90), `L01_Brady_Underground_Leaving#*` (+201) - all mini cutscene or
  situation clips, none in an FA level. They do not refute anything; they are the stock precedent for plan
  (i)(b), and their player form (the act, 1.2) is where the missing sync was found.
- Fall height: stock F04 / F06 route players over 400 drops (the reader's census), so 253 from the wall is inside
  what stock does. A `Fall_Fatal_Enter` clip exists (`/Movement/Fall/Fall_High_Enter`); its threshold was not read.

## 5. Can the live checks tell success from failure?

| check | verdict |
|---|---|
| K0 | Yes for 'the file loads and the round plays' (crash or not, GO, the hop / van lines; `[CrewHop] Log=2` is needed for the 'left From' line). It does not play a climb clip: that the clips decode is K2's. |
| K1 | Yes: with `Log=2` the every-second line gives distance, height, speed and the facing number, so a wrong sign or a node that is not at the floor shows. Safe to run on the file as it is (no call is reached). The expected `slot ... High = id 2507` is wrong: 2505 is right (section 2). |
| K2 | **Not as written.** (a) The `over after` line is printed in the tick the action is gone, before any movement step: it reads 'on the wall' in the failure of M1 too. Add a line 1 - 2 s later with the node's place (klhop.c has that form) and take the picture 3 s after, not at the end. (b) The suggested route holds the stick into the wall through the whole clip (`goto ... keep` to a point beyond it), which is K4's question: if it fails, the cause is not known. Run K2 first from a stand - `goto -3000 -670`, then wait - and the run-through as a second run. (c) Read 'node y 150 or 281 right after' as success too: he ends 5 short of the far edge of a 50-thick wall and may slide off at once. |
| K3 | Yes (place, the van line). |
| K4, K5, K7, K8 | Yes. Add to K7: a pause of 5 s during a climb (S2), and a death during a climb (S1). |
| K6 | It can tell 'did not outlive its start' from 'ran' only when nothing worse happened; see S4. |

## 6. Notes

- N1. re/climb.md 2.1: 'to 30 past the probe' is 15 (1.3). 1.3: 'a null clip is a null read at 0x6a2a65' is the
  channel. 4.2 and section 7 (K1, K2): the slot id of High is 2505, not 2507 (section 2 here).
- N2. Clip record +0x2C: 8 of the 12 added clips carry Dead Men's non-zero value (9,008 .. 61,120). It is a
  per-file value (same-named clips: `Walk#Backwards_01` 5,824 in M03_FA_A, 134,704 in F07) with no reader found;
  the 67 Dead Men clips the graft had put into this build all have 0. The join's rule (copy) is the documented one
  (re/anmjoin.md), but these are the first such clips a PLAYER will play. Not among re/climb.md's assumptions.
- N3. `apply` rewrites `big_before` in the copied `dyn.json` / `fed.json` so that another tool's check does not see
  this step's growth. It is said in `climb.txt` and the old numbers are kept. I would rather have the other check
  learn of the step (its owner is another track); as long as it does not, say it in the check's own output too.
- N4. `Key=0` as the default means: 0.4 s at the foot, facing the wall within 60 degrees, and he climbs - Dead Men
  asks for the USE tap. Fine for scripted runs; for the owner's play it is his choice (an unwanted climb ends 253
  over the street in front of the police).
- N5. `0x59d550` advances the game's random generator; the vault mode's pre-test calls it twice per try.
- N6. The planner's 'not done' and 'assumed' lists are fair; the assumption 'moves the player as a vault's does'
  should now read 'with the proxy sync added'.

## 7. What I did not do

- I did not read what the movement class does DURING a clip with the collision off (whether BaseMove steps the
  proxy, whether a mini animation of kind 0x23 is treated as the vault's 0x2b is); K2 after M1 answers it.
- I did not decode who reports a replaced channel (S4), the fatal-fall threshold, or clip +0x2C.
- The cover census is the reader's file, analysed again, not rebuilt from the levels.
