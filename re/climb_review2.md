# Second review of track F - the wall climb after the fixes (klhook/klclimb.c, re/climb.md)

2026-10-11, adversarial reviewer of the fix round. OFFLINE: no game was started, no game folder written, nothing
committed, no tool or source file changed; this file is the only thing written in the repo. Scratch (not in the
repo): `<scratchpad>\rv2_climb\` (my disassembly helper `d.py` over `debug\kl.py`, `ident.py`, `clipm.py`,
`p1only.py`, `cls.py`, a wired copy of `klhook\` in `hk\`, the off-game test rebuilt in `sim\` with my own
scenarios `sim2.c`). Status words: **read** = seen by me at the address given; **measured** = counted by a script
of mine; **reasoned**.

## Verdict: ACCEPT WITH FIXES

- **The main finding of the fix round holds.** The first review's fix for its own MUST (proxy sync 'immediately
  before `0x686600` in the end paths') would indeed have come one frame late; I re-derived it from the exe
  (section 1). The hand-over before the clip's end is the right shape of fix, and the file does it as described.
- **M1, S1, S2, S3, S4 of `re/climb_review.md` are met in the code** (section 3). No MUST was found.
- **K0, K1, K2 can run once the file is wired** (the three lines are right: section 2). K2 can now tell a climb
  that held from one that did not. Two of its expected numbers are wrong on paper (D3) - read the corrected ones
  below before the run.
- **`Mode=vault` / K6 needs two small fixes before it is run** (D1, D2): its failure branch can leave the
  collision count held without saying so, and its 'REFUSED' verdict can be a passing state.
- What still rests on reading alone is what the worker says rests on it: nothing ran.

## 1. The claims everything rests on, re-derived

### 1.1 'The game ends the action and steps the ordinary movement from the proxy inside one frame' - CONFIRMED (read)

- ZPlayer's frame `0x74efc0`: `[player+0x7a4]` set -> `0x710da0`, return (`0x74efc6`); `[player+0x430]` clear ->
  nothing (`0x74efd9`); **a third gate the account does not name**: `0x598460([player+4])` = `[[node+0x50]+0x60]`,
  bit 0x800 of `[[that+4]+0x3c]` -> nothing (`0x74efe6 .. 0x74eff8`). Then: the animation update, vtable +0x2e8 =
  `0x50ac80` (`0x74f041`); **vtable +0x578 = `0x5aa510` (`0x74f057`): the node's world transform is read
  (`0x857110`) - this is Move's 'from'**; Move, vtable +0x63c = `0x6e6730` (`0x74f077`); vtable +0x620 =
  `0x6b9d50` (`0x74f097`; when 'moved by animation' it only calls vtable +0x378 and returns, `0x6b9d66` ->
  `0x6ba0d9`); and at the end **the node is WRITTEN
  from Move's result by vtable +0x60c = `0x693400` -> `0x8caf30` (`0x74f2df`) unless vtable +0x678 = `0x5380d0`
  (`[player+0xd50] != 0`) says so** (`0x74f2c5`). `0x8caf30` tells the pathfinder object and sets the node
  (`0x8caf96`); it does not touch the character proxy.
- The update ends a channel that reaches its end (state := 4 at `0x50afca .. 0x50afd1`) and reports it:
  `0x50b5e8 .. 0x50b645` -> vtable +0x2e4 = `0x7cc140` -> `0x8f0df0` -> dispatcher slot 7 `0x5d0260` -> the current
  action's slot 10 -> slot 6 `0x595b70` (`[disp+4] = 0`, End = action slot 5, delete when slot 9 agrees).
  `ZFFActionMiniAnim` (vtable `0xbb4f0c`): slot 10 = `0x42b7f0` (with endWithClip it answers byte +0x24), End =
  `0x6fb600` (stops its channel through vtable +0x1f8, nothing else).
- Move `0x6e6730`: vtable +0x668 = `0x6d4570` (vtable +0x214 = `0x41a6b0`: the channel `0x760120` finds - state 1
  or 3, flag 0x8000, clip record byte +8 bit 0x40 - has flag 0x200, or its clip has bit 8 clear and moves bone
  0x39; and `0x7bae10`: that channel has no flag 0x1000). Yes -> movement number 1 (vtable +0x664 = `0x8b61b0`, a
  jump to `0x462420`). No -> the chooser vtable +0x638 = `0x5bf250`, then `[player+0x6b4]`.
- After the mini animation's End no playing full-body channel is left (its own Play stopped them: 1.3), so in
  that very frame Move goes to the current movement. **Both candidates step from the proxy whatever the collision
  flag says**: `ZFFPlayerMovementStand` (vtable `0xbb5614`, update `0x74f880` = slot 30, then slot 33,
  unconditionally) and `ZFFPlayerMovementBaseMove` (`0x7a43e0`: the only test before slot 33 at `0x7a4ae3` is the
  cover test `0x7a4a4d .. 0x7a4a6c`; the routine has no early return and no read of `[player+0x7a5]`).
- The physics step `0x6d1ad0` (slot 33 of every movement class - measured on the 19 RTTI vtables): velocity
  `[player+0x808]` = the move x 60.0 (`0xb35dd4`), vtable +0x680 = `0x4d1310` (proxy integrate, then the body is
  put at the proxy's place, `0x9fe840`), **result = the proxy's place x 100 + ('from' - node)** (`0xa768a0` at
  `0x6d1b73`, `0x408060`, `0x42a4d0`, stored at `0x6d1b97 .. 0x6d1ba7`).
- So: with the collision still off when the clip ends, the frame writes the node where the proxy stayed, before
  any hook tick. The review's fix would have synced a proxy to a node that is already back at the foot.

### 1.2 'With the collision off the node follows the clip and the proxy stays behind' - CONFIRMED (read), by a path the account marks 'not read'

- `ZMovementAnimation` (vtable `0xba6e94`) update `0x5397e0`: slot 35 `0x536a20`, then the physics step **only
  when vtable +0x630 says the collision is on** (`0x53986f .. 0x539879`, slot 33 at `0x539892`).
- Slot 35 `0x536a20` (the account: 'not read'): `player->vtable[0x5f8]` = `0x72d010` hands out the frame's root
  delta (`[player+0x20]` rotation, `[player+0x44 .. 0x4c]` translation - what `0x50ac80` leaves there, `0x50b5c0
  ..`) when 'moved by animation'; with it **out = 'from' moved by the delta** (`0x536a8f .. 0x536b59`), without it
  out = 'from'. The frame then writes out to the node (1.1). That is how the node follows the clip.
- Nothing on that path moves the proxy: Move's own proxy work (`0x6e699e ..`) asks for `[player+0x7a5] != 0`
  (`0x6e69c9`), `0x8caf30` does not touch it. `0x4af5b0` (read whole: node place `0x7b3020` x 0.01 ->
  `0xa768b0` -> `0x9fc110` writes the phantom's +0xa0 .. +0xac, asks `[[ph+8]+0x6c]`, calls the shape's vtable
  +0x18, updates the broad phase) has 30 direct calls and one tail jump (`0x90183c`) = the 31 sites named.
- The enders' order (read): vault End `0x82f780`: `0x4af5b0` at `0x82f796`, vtable +0x564 at `0x82f7a6`.
  Collision switch: `0x8c5270` / `0x8b41c0` and layer 0xc / 5 through `0x40ed30` (the body's word +0x2c, then
  Havok when the world's byte +0x14fc is set) - as the file says; `0x4adce0`: 0x1388 entries, count at +0x1183c.

### 1.3 'Play itself reports a replaced channel to the action that is already current' - CONFIRMED (read)

- Play `0x4da1d0`: body class of the new clip = clip `+0x28` bit 0x10 clear (`0x4da278 .. 0x4da281`); with flag
  bit 0 every playing channel (state 1 or 3) of that class is stopped and its id kept (`0x4da294 .. 0x4da306`),
  and each is reported through vtable +0x2e4 before the return (`0x4da711 .. 0x4da751`).
- The dispatcher's slot 1 `0x672d00` stores the action at +4 (`0x672d07`) BEFORE it calls the action's start
  (`0x672d0f`); `ZFFPlayer`'s StartAction `0x542c00` -> `0x869e10` -> that slot.
- The vault's slot 10 is `0x553070` = `mov al, 1`; the mini animation's start `0x76d1d0` clears byte +0x24 at
  `0x76d212`, plays at `0x76d221`, sets it at `0x76d22a`. (Its first instruction sets the byte to 1 and
  `0x74c040` runs before it is cleared: a report from inside `0x74c040` would end it too - the game's own
  exposure, `0x74c040` only posts an event.)
- `StartMiniAnim 0x5ea340` has exactly two callers (measured: `0x5022ed`, `0x607a1c`), `ret 0x10`; the game's
  own call is `(slot, 0, 0, 1)` behind 'no action' and down state `== 0` (`0x5022c0 .. 0x5022ed`) - the file's
  call and guard.

### 1.4 The numbers of the clips - CONFIRMED (measured, my own key reader on `z_climb\M03`)

| class (clip) | frames | events | at 3 frames before the end | 0 beyond the face from | 10 beyond from | at the end |
|---|---|---|---|---|---|---|
| High `Climb#Up_High` | 52 | 5 at 6, 6 at 20 | frame 48: 27.2 beyond, +24.5 | 43.4 | 45.1 | 44.4 beyond, +24.5 |
| Medium `Climb#Up_Medium` | 37 | 5 at 6, 6 at 16 | frame 33: 4.8 beyond, +0 | 31.6 | 34.6 | 14.9 beyond, +0 |
| Low `Climb#Sprint_Low` | 27 | 5 at 6, 6 at 16 | frame 23: 22.1 before, +2.3 | 25.7 | never | 3.2 beyond, +3.3 |

Record flags 0x10c0, `+0x28` = 0 on all three; last key - first key = the record's vector +0x18. Slot ids in the
build's `climb.json`: High 2505, Low 2506, Medium 2507. `F01_Main.zip` sha1 2c93ab68.. - the build is unchanged.

### 1.5 The smaller ones (read)

- The clock: `0x70da30` - `+0x4c` := `+0x48`; with the pause byte `[[sys+0xac]+0xbc]` the offset `+0x54` is
  re-based and `+0x48` stands; else `+0x48` = offset + raw; `+0x50` = the difference x 1/1024 (`0xb5c498`). Move
  skips the movement's update when the step is 0 (`0x6e692e .. 0x6e697b`).
- Cover: `0x40f840` = `[+0x2954]` or `0x6e2740` or `0x780b80`, which together come to `[+0x2954]` or bit 0x80 of
  `[+0x818]` whatever `0x651000` answers. The file's test is the game's.
- The 8 x 14 identity bytes and the 4 vtable entries of `klq_code`: compared with kl2.exe by my script, ALL SAME.

## 2. The checks, re-run

| check | my last line | the worker's |
|---|---|---|
| my own wired copy (repo `klhook\` at aa48c72 + the three lines; its `klhook.c` is byte-equal to the worker's scratch one) `build.bat` | `built ...\out\dinput8.dll (SHIP)`, exit 0, 0 warning lines, **406,016 bytes** | the same size |
| `build_auto.bat` | `built ...\out_auto\dinput8.dll (TEST)`, exit 0, 0 warning lines, **454,144 bytes** | the same size |
| `cl /Zs /W4`, SHIP and TEST | exit 0 both, 0 lines naming `klclimb.c` | the same |
| worker's scratch: `klclimb.c` there = the repo's (sha1 ae3b1637..); its `klhook.c` differs from the repo's by exactly the three lines; DLL sha1 1a0e2592.. / 079d0d34.. | as reported | |
| the off-game test, `sim.c` rebuilt by me against the REPO's `klclimb.c` | `SIM: PASS (0 failed)`, 32 of 32 | the same |
| `kl_fa_climb.py check z_climb\M03` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)` | the same |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 3 NOTE)` (the loot-window FAILs of the source build) | the same |
| `kl_impact.py` | `problems: 0 in 1 levels` | the same |
| `kl_maps.py audit` (on a scratch copy, removed afterwards) | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` | the same |
| `kl_map_escape.py van-check` | `0 fault(s)` | the same |
| `kl_anm.py check` | `byte-identical: 41 of 41` | the same |
| `git status` | of track F only ` M klhook/klclimb.c`, ` M re/climb.md`; `klhook.c` has no `klq_` / `klclimb` line; HEAD aa48c72 | the same |

The other modified files of the tree (`kl_fa_bots_dyn.py`, `kl_fa_bots_rt.py`, `kl_chars.py`, the workflow file,
`klhook\out_auto\`) are other tracks' (their dates and diffs say so). `tools\kl_fa_climb.py`, `tools\kl_anm.py`
and the build folder are unchanged. Nothing of this track is under `<work>\build\klhook\` or in the game folder.
The wiring lines are reachable where they are put: `klq_tick` after `klv_tick` in `klh_tick` (which runs with
`game_thread = 1` only from the main loop's two `SteamAPI_RunCallbacks` sites), `klq_init` in the init list.
The brief of the first round said 'do not build the hook' and 'build outputs only under `<work>\build\z_climb\`':
the proof build is a scratch copy in `G:\kl_scratch\climb_fix_1011` - outside the tree, the work folder and the
game folder; it found a link error a syntax check cannot. The two DLLs there are not for installing.

## 3. klclimb.c, the diff read whole

Unchanged from the reviewed first version (function by function): `klq_node`, `klq_slot`, `klq_clip`,
`klq_align`, `klq_registered`, `klq_num`; `klq_source` by a comment. New or rewritten: the rest.

| review | in the code | verdict |
|---|---|---|
| M1 | `klq_follow`: from `to - margin` on (margin = HandFrames, at least one and a half ticks' worth, never before `f_top + 1`), when the node is 10 beyond the face or in the last tick, `klq_give_back` = `0x4af5b0` then `0x686600`; every other end path makes the same two calls | met; the order and the timing are the game's (1.1, 1.2) |
| S1 | `klq_carry_refuse` before every `0x4af5b0` / `0x686600` and (through `klq_refuse`, same tick) before `0x5d6200`: registered, node chain, the phantom's +0xa0 writable, `[[ph+8]+0x6c]`, the shape's vtable +0x18, the world, `idx < count <= 0x1388`, the body's +0x2c writable, `[world+0x14dc]` when the byte asks - each is what the routine dereferences (read) | met |
| S2 | `klq_clock` = `[[0xdd2640]+0x48]`; limit in game ms; a gap rule only when the clock cannot be read | met |
| S3 | `[+0x2954]`, bit 0x80 of `[+0x818]`; down state `!= 0` refuses | met |
| S4 | `klq_replaced` counts what `0x4da294 ..` would stop, with the clip's own class; `klq_vault_refuse` | met for the path that was read; see D1, D2 |

Calling conventions of the new calls (read): `0x4af5b0` thiscall, no argument, plain `ret` (`0x4af606`);
`0x8aef30` -> dispatcher slot 5 `0x640430` (nothing when no action). `Dry=1` reaches no call (every path
followed); nothing is called with `game_thread = 0`; no write of the file's own. No path was found that leaves
the hook's own count held, except the two it names itself (the object gone with its level; 'GIVEN UP after 3 s').

### Defects

**D1 (should) - `Mode=vault`: the failure branch does not look at the collision count.** `klq_vault`, after the
call of `0x619790`: when the action is not the vault's it writes 'did not outlive its own start' and returns.
The vault's start `0x6a27e0` runs leave-cover first (`0x6a2817`) and switches the collision off only at
`0x6a2a44`. The action is current from `0x672d07` on and says yes to any report (`0x553070`). An End that runs
BEFORE `0x6a2a44` (a report from inside leave-cover: `0x5abbb0` / `0x834ef0`, the two routines the account lists
as not read) gives the collision back at count 0 (`0x8b41c0` does not go below 0), the object is deleted, the
start goes on and switches the collision OFF - with no action left to switch it on. `klq_replaced` only covers
the Play at `0x6a2a5d`. My model of exactly that (scratch `sim2.c`, X3): the file says 'did not outlive its own
start', `[player+0x7b4]` = 1, `[player+0x7a5]` = 0, no call of `0x686600`, `klq_r.player` = 0 - he is left
without his collision and the line does not say so. Whether the game does this is not known; the guard costs
four lines. Fix: in that branch (and when the start says no) read `[player+0x7b4]` - `klq_refuse` had it at 0 -
and if it is not 0, `klq_give_back` and say so; name the line in K6's FAIL list.

**D2 (should) - K6's 'REFUSED' can be a passing state, and the refusal is final for the stay.** Measured on this
build's `.ANM` (`cls.py`): the clips of the vault's body class (`+0x28` bit 0x10 clear) are not only actions -
`Movement/Soldier/Transitions` 174, `Walk` 124, `Run` 61, `Stand` 44, `Crouch` 58, the cover idles - all with the
root-motion flag; the other class is weapon handling and faces. So a stop transition half a second after he
stopped walking would be counted. But `klq_tick` sets `told = 2` before the try, so one refusal ends the stay
(only `klq_refuse`'s reasons are retried), and section 7 concludes from one line that '(ii) is then closed for a
standing player'. K1's 'N full-body channel(s)' is counted when he is first SEEN at the foot - still walking -
not when the vault would be tried. (That the stock vault survives its start from cover, where the idle is of the
same class, says locomotion does not sit in these 16 channels or is stopped unreported: reasoned, not read.)
Fix: retry that refusal like the others (`told = 1`), print the count again in the 'WOULD climb' / 'WOULD vault'
line, and let K6 call (ii) closed only when the refusal repeats over a second of standing.

**D3 (should) - two expected numbers of K2's decisive line are wrong on paper.** re/climb.md 7 (K2) and the
sample log of klclimb.c give the HAND-OVER line as `proxy (x, y, -672) -> (x, 404 .. 428, about -581)`. Measured
(1.4): at frame 48.2 he is 28 beyond the face = **z about -597, y 428**; -581 is the clip's END (44 beyond). And
the first place is **where he stood** (`pos foot`'s z, -688 .. -648 with the script), not P1's -672: the first
alignment moves the node, not the proxy. The off-game test prints it right (`proxy (-3000, 200, -665) -> (-3000,
428, -596)`), and so does the worker's own report. K2's PASS is 'all of' its lines: correct the two numbers
before somebody reads a good run as a wrong one.

**Notes**

- N1. Where the account is two steps short (1.1, 1.2): slot 35 `0x536a20` is 'not read' although the main claim
  passes through it; the frame's third gate (`0x74efe6`), its vtable +0x578 and the node write at `0x74f2df`
  with the gate `[player+0xd50]` are not named, and the top comment's 'THE NODE IS PUT WHERE THE PROXY IS' is the
  frame's doing, not the physics step's. `klq_refuse` tests neither gate; with either set the clip plays and he
  does not move - a clean failure (`RESULT ... BACK AT THE FOOT`), so a note.
- N2. `HandFrames=3` leaves about 125 ms: one game frame of that length that begins just before frame 48 ends
  the clip unseen (my X2c: first failing length 130 ms; with `HandFrames=5` 240 ms). The reason given for the cap
  ('more would hand a High climb over before he is beyond the face') is not what the code does - the '10 beyond
  the face' test stands in front of every hand-over but the last tick's. 5 as the default costs nothing for High
  (frame 46: 15 beyond, +24.5) and nothing for Medium (it waits for frame 34.6 either way).
- N3. `Align=1` (K5) hands the proxy over UNDER the wall's top: the one correction is blended in to the last
  frame, so he crosses the face 4.9 under the top and stands 1.8 under it at frame 48 (3.1 at frame 46; `p1only.py`,
  from any stand 15 .. 70). Say it in K5; aim the alignment a few units over the top, or in that mode hand over
  in the last tick only.
- N4. A call-off after one step from before frame 6 past frame 42 (1.45 s of game time in one step): with only
  the first alignment set the node is then beyond the face and 28 under the top (`p1only.py`) and
  `klq_give_back` puts the proxy there - inside the wall. By the file's own reading 'collision on' WITHOUT the
  sync would have him back at the foot in the next frame. The file has the numbers to tell (`klq_off`, the
  height against the top). Rare; the same holds for the time-out path in `Align=1`.
- N5. K7 (c) lists `collision on (count 2 -> 1) - somebody else holds it off as well` as a pass. `0x686600` sets
  the body's layer to 5 whatever the count is (`0x686608 .. 0x68662d`): after that line a dead man's body
  collides while the game's own count says off. The game's own quirk (its vault's End would do the same); say
  it beside the line.
- N6. What can end the climb early in K2 without anybody pressing anything: EVERY channel that ends is reported
  (`0x50b5e8 ..`, no class test) and the mini animation says yes to each. Candidates by the measured classes:
  weapon handling (872 clips of the other class) and faces. The game's own stagger has the same exposure. K2's
  FAIL line (`ended at frame N of 51 BEFORE the hand-over (his action now 0 ...)`) names it; it is the likeliest
  way K2 fails.

## 4. Counterexamples tried against the main claim

- 'Move steps from the proxy in the frame of the end' needs the current movement to do so with the collision
  off: Stand and BaseMove both do (1.1). Not refuted.
- 'The frame writes the node from Move's result' - the set-transform could have moved the proxy as well (then the
  first review's M1 would have been moot): `0x8caf30` does not. Not refuted.
- A stock clip class that would make the vault kill itself in stock play (then the reading of 1.3 would be
  wrong): cover idles ARE of the vault's class (D2) - which does not refute the reading, only says those idles
  are not playing in the 16 channels when the vault starts.
- The state machine, in the off-game model (mine, `sim2.c`): two hook ticks a frame - one hand-over, UP; one long
  frame - N2; the vault's start that leaves the count at 1 - D1.
- After the hand-over (collision on, the clip still aligned): the animation movement drives the proxy by the
  clip's delta as a velocity and the node is the proxy's place (1.1, 1.2) - the path the game itself runs for
  `ZMiniPlayerMoveTask` (`0x607950`: StartMiniAnim with an align object, no collision call in the routine).
  High stands 24.5 over the top there with nothing to hit. What Havok does with him was not readable; K2 is.

## 5. Can the live checks tell success from failure?

| check | verdict |
|---|---|
| K0 | Yes (load, GO, the hop and van lines). Runs on the hook as installed. |
| K1 | Yes, and safe (no call). The node / +0x460 / proxy side by side and the facing number show a wrong reading at once. Do not take its channel count as K6's answer (D2). |
| K2 | **Yes now**: `RESULT` 2 s after the end is judged on the node against the edge (UP / ACROSS / INSIDE / BACK AT THE FOOT / ELSEWHERE - the five ranges do not overlap: read), the +500 / +1000 ms lines print the proxy as well, and the runner's `pos after` z is an independent witness. Read the HAND-OVER line with D3's numbers: first place = where he stood, second about (x, 428, -597). The script's commands exist in klauto.c (`goto x z [radius] [timeout] [sprint] [keep]`, `pos`, `wait`, `tap`, `mdown` / `mup`). |
| K2b, K3, K4 | Yes. |
| K5 | Yes for the lines; expect the proxy 2 - 4 under the top at its hand-over (N3). |
| K6 | PASS and FAIL yes; **REFUSED not as written** (D2), and its FAIL cannot see a held collision count (D1). Fix both before it is run. |
| K7 | Yes. (c): see N5. |
| K8 | Yes - with a human at the keyboard: a scripted key is not seen by `GetAsyncKeyState`, as the account says. |

## 6. What I did not do

- Nothing ran in a game. Havok's side of the hand-over (gravity during the animation movement, how the proxy
  settles 24.5 over the top) is not in the code I read.
- I did not read `0x5abbb0` past its head, `0x834ef0`, `0x87fb30` / `0x907440`, the writers of the pause byte, or
  what the clock does when the window comes back to the front.
- The facing sign, the node's height and the condition bits were reviewed in the first round and not again.

## 7. Appended by the fix round after this review (2026-10-11): what was done about each point

Written by the worker who finished the track, not by the reviewer. OFFLINE as everything before: no game
started, no game folder written, nothing committed; files changed: `klhook/klclimb.c` (third version, still
NOT WIRED), `re/climb.md` (its section 6.3 is the full table, 7 the corrected live checks), this section.
Every 'should' is FIXED; none is refuted. Evidence is the worker's own: the addresses read again with
`debug\dasm.py`, the clips measured again (`meas.py`), and the off-game test extended and run again - 66
expectations of 66 on the new file (the 32 of the second version unchanged in what they ask), and the SAME test
source compiled against the second version as a control, which shows D1's and N4's defect.

| point | done |
|---|---|
| **D1** should (`klq_vault`'s failure branch, K6) | Fixed. After a start that kept no vault action the branch reads `[player+0x7b4]` and `[player+0x7a5]` (0 and 1 before the call); if the collision is off it says `the vault's start LEFT HIS COLLISION SWITCHED OFF (count N, flag F; ...): this file gives it back`, calls `klq_give_back` at once (or owes it for 3 s, as after a climb) and watches for the RESULT. K6's FAIL list names the line. Read for it: 0x6a2817 (leave-cover), 0x6a2a4a (the collision-off call), 0x6a2a5d (Play), 0x8b41c0, 0x619826 -> 0x6199c7 (an empty pool: 0, nothing done). Test L (5 cases); control: the second version leaves count 1, flag 0 |
| **D2** should (`told = 2` before the try; K1 / K6) | Fixed. The channel refusal no longer ends the stay: said once (`NOT vaulted yet`, with the count and the first channel's number, clip and frame), asked again every 250 ms while he stands, `the vault is REFUSED from this stand: T tries in M ms` only after a second; a later pass says how many refusals went before. The count is printed in the `WOULD climb` / `WOULD vault` lines and every second with `Log=2`; the `at the foot` line says `as he arrives`. K1 and K6 reworded as asked. Test M (9 expectations) |
| **D3** should (K2's HAND-OVER line; the sample log) | Fixed in both places, with the numbers of the new default `HandFrames=5` (N2): first place = where he stood (`pos foot`), second = (x, 428, about -608) at frame 46.x. Measured: frame 46.0 z -609.6, 46.2 z -608.4, 48.2 z -596.6 (the review's -597), the end z -580.6 |
| N1 | The four addresses are in `re/climb.md` 3 and the top comment (each read again); `klq_refuse` refuses behind `[player+0xd50]` and behind bit 0x800 of the node `[[[node+0x50]+0x60]+4]`. Test Q |
| N2 | `HandFrames` defaults to 5; the comment corrected. Test N reproduces 240 ms / 130 ms |
| N3 | The single alignment of `Align=1` aims 10 over the top (measured: 0.8 .. 6.6 over at the face for a High top 183.5 .. 220 over the feet; 3.4 for the bank's 203.5); K5 says it. Found while measuring: `Align=1` cannot carry class Low (the clip lunges 51.9 forward in 3 frames) - refused with a line. Test O |
| N4 | `klq_give_back` leaves the proxy where it is when his node is between the faces (15 clear) and more than 3 under the top, and says so; every path that gives back goes through it. Test P; control: the second version puts the proxy at (x, 372, -612), `RESULT ... INSIDE THE OBSTACLE` |
| N5 | Said beside the line in K7 (c) |
| N6 | Said in K2's FAIL list ('the likeliest way K2 fails'), the plan's risks and the top comment's section 3 |
| the proof build | The third version's SHIP and TEST hooks were again built in a scratch copy outside the tree (`G:\kl_scratch\climb_fix3_1011`): exit 0, no warning; not for installing |

What still rests on reading alone is unchanged: nothing ran; what Havok does with him after the hand-over is
not in the code that could be read; `0x5abbb0` and `0x834ef0` inside leave-cover were not read.
