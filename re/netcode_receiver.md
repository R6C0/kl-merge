# Net receiver side: spin and float (2026-10-19, kl-merge track net)

Static reading of kl2.exe 0490. Nothing ran in the game. READ = seen in the disassembly (address given). GUESS = not proved.
Code: `klhook/klnetfix.c` (experiment, all keys off). Short answer: the receiver's real correction numbers are in hashed
.rdata, so no data-only hook can change them. One writable number exists; what it does is a GUESS.

## 1. What was READ

- The remote player update is ZFFPlayer vtable slot 393 (vtable 0xbb45f4, slot 0xbb4c18) = 0x506350, which calls 0x600eb0
  (via 0x4a1890) when `[esi+0x2720]` bit 1 is clear. READ. (re/netcode.md "called from 0x73c830" is wrong.)
- Time: 0x519e80 calls 0x49d020, which calls the function pointer in .bss `[0x1690a1c]`, then 0x942bf0. 0x942bf0 finds the
  dataset's class object with 0x960ff0 (table `[0x16914f8]`, index `[dataset+0x3c]>>22`) and calls its vtable slot +0x38
  `(dataset, a, b)`. READ. What that slot does (refresh the dataset's int16 from its model at "now") is GUESS from use.
- Heading: after the refresh `movsx word [esi+0x60]` / 162.9746 (double at 0xb78bc8) = radians (0x60143c..0x60145d).
  READ. 162.97 = 1024 per turn. The int16 is used raw; nothing in 0x600eb0 wraps it.
- Position: three models (x, y, z) at player +0x388 / +0x3c0 / +0x3f8, read by 0x77ebe0 (0x6014de, 0x601504, 0x601528).
  The predicted point is compared with the body: a length against the double 1,000,000 at 0xb49b40 (0x601568); above it
  the player is teleported by 0x5f21c0 (re-seeds the three models, places the body through vtable +0x8c). Below it a
  second compare (0xb89690 or 0xb3dde8, by flag `[type+0x3c] & 0x1000`, 0x60161a) decides whether the correction runs,
  and the actor is then steered with the replicated stick bytes `[esi+0x2a0]`, `[esi+0x2a1]` / 127 (0x601893..0x6018ba).
  READ. So the body is STEERED toward the prediction with stick input plus a correction, not placed. That is the "floaty"
  look (H3 holds). Whether 1,000,000 is a squared length (1000 units) is GUESS (0x42e1f0 not read to the end).
- `DisableSyncChange2` (string 0xb75010, read through 0x793550 on `[0xdd2640]`, 0x601789): when set it skips a block at
  0x6017ba..0x601851 that changes the height component of the correction (a call through vtable +0x264). READ. Its
  effect on feel is GUESS; it is a game flag, not a number KLHook can set without finding where 0x793550 reads it.
- The model (esi in 0x992ab0): int16 samples at +0, +2, +4 (older..newest), 64-bit times at +8, +0x10, +0x18, floats
  c, v, a at +0x20 / +0x24 / +0x28. 0x991ef0 picks a state from the samples: newest == middle -> 1, middle == oldest -> 2,
  else 2 or 3 (3 only when the policy float +0 is not 4.0, 0x991f27). 0x992f10 interpolates inside the history, else calls
  0x992ab0, which uses c + v*dt + 0.5*a*dt^2 with dt in ms, and NO cap on dt. READ.
- The int16 deltas are plain sign-extended differences (`movsx / movsx / sub`, 0x993051..0x993059): no wrap-around.
  So if the sender stores a heading that wraps (e.g. -512..511) the receiver will interpolate the long way round: H2 is
  possible. Whether the sender wraps is NOT known (sender encoder not read). GUESS.
- Policies: nine objects 0x168f204, 264, 2c4, 3a0, 400, 460, 4d0, 530, 590 made by 0x990de0 from static initialisers
  (0xb047d0..0xb04fb0): +0 float 4.0, +4 float -1.0, +8 dword 1000, +0xc dword 250, +0x10 byte 1, +0x14 dword 3500. READ.
  Each sits 0x20 after a sender tolerance object of klnet.c (0x168f1e4 actor position, 244 actor angle, 440 player
  position, 4b0 player angle, 510 camera, 570 aim). 0x991510 (add a sample) gives a model with no end time the end time
  "sample time + policy +0x14" (0x99155f..0x991578); 0x8df1c0 (player position) pushes 0x168f460, 0x5c1710 pushes 0x168f204. READ.
  Their link to the other four (2c4, 3a0, 400) is not known.

## 2. What it means for the two symptoms

- SPIN: sender stops turning, the "stopped" packet is lost (unreliable), the receiver goes on with v from the last two
  samples until the next forced refresh (2 s) - nothing on the receiver bounds dt. READ for "nothing bounds dt" (above).
  The only receiver number that looks like a bound is policy +0x14 (3500 ms), which is longer than the 2 s refresh, so
  in stock play it never matters. Lowering it MAY end the run-on earlier. What a model does at that end time is GUESS:
  0x9914c0 returns true after it and 0x992ab0 then re-derives c, v, a through 0x991fd0 (state 1 gives v = a = 0, i.e. a
  hold; states 2 and 3 re-fit from the int16 samples, which may NOT stop a spin). Treat it as an experiment.
- FLOAT: the thresholds that decide snap versus steer are in .rdata (0xb49b40, 0xb89690, 0xb3dde8): hashed, not
  writable. The only data levers are the sender's tolerance (klnet.c Tune: PosTol) and the hold time. A position hold is
  dangerous: a steady runner sends nothing for up to 2 s, so a short position hold would freeze him mid-run (default off).
- A real cure needs code: a wrapper of slot 393 that runs before 0x600eb0 and snaps (0x5f21c0) when the error is
  large, or that bounds dt. Design only, NOT built: it needs the player's position at a known offset and the
  model addresses, and the clock at `[0x1690a1c]` is global. A heap-vtable wrapper is legal (private copy of the
  0xbb45f4 table, pointer swapped in the object) but other KLHook parts compare the vtable pointer to 0xbb45f4.

## 3. What is built

`klnetfix.c`, behind new `[Net]` keys, all 0 = off: `HoldHeadingMs`, `HoldPosMs`, `HoldActorHeadingMs`, `HoldActorPosMs`
(500..3500), `HoldLog=1` (read-only: says the nine policies once per session, "NOT as read" if a layout differs).
It writes the dword at policy +0x14 (.bss, 4 bytes, through klh_data so klranges.h is checked) only when: role 2 or 3,
game type 4, state 0x13..0x1f, the Steam service object has vtable 0xbd597c and its ranked byte is 0, and the policy is
shaped as read. The game's value goes back when the gate closes. A model created before the write keeps its old end time.
Inert in Arcade/offline.

Wiring (klhook.c): `#include "klnetfix.c"` below `#include "klnet.c"` (line 651), `klnetfix_tick(game_thread);` below
line 782, `klnetfix_init();` below line 1129. Scratch build with these: 0 warnings, dinput8.dll sha1
8115a4148ebaf5acd895fd6feaebbae849427ca7 (SHIP, 1,135,104 bytes).

## 4. Safe against unhooked peers?

Yes for every key: only this machine's display of others changes; nothing is sent, no packet field differs, and the
policies are not replicated. No peer sees a difference. (Same basis as klnet.c: no peer compares these numbers.)

## 5. What can be checked without two PCs

Only the layout: `HoldLog=1` in a private lobby with one machine logs the nine policies; every line must read
"hold 3500 ms" and none "NOT as read". That proves the addresses, not the effect.

## 6. Cheapest two-PC test

Both PCs in one private FA lobby on a stock map. PC B has `HoldHeadingMs=800` and `HoldLog=1`; PC A is plain.
A turns on the spot for 3 s then stops while B watches A's heading; repeat with the sender hook `RefreshMs=-1`.
Judge: does A's body keep spinning after A stopped (stock) or stop sooner? Then the reverse. Also watch for jitter in
B's view of a steadily turning A (the re-fit could make it worse). If no change: the end time is not a hold, drop it.

## 7. GUESS list

1. The slot +0x38 of the class object refreshes the dataset (name from use only).
2. What a model does at its end time (hold, or re-fit) - the whole point of the experiment.
3. Policy +0x14 is also what other users read; only 0x991510 was seen using it.
4. The actor policies (0x168f204 / 264) behave like the player ones (same code 0x992f10 assumed; not traced for AI).
5. 0x168f2c4, 3a0, 400 are untouched; their meaning is unknown.
6. Whether the sender wraps the heading (H2).
7. 1,000,000 at 0xb49b40 being a squared length.
8. Effect of DisableSyncChange2 on feel.
9. That the ranked byte at svc+0x36f is the right ranked test on a client (same assumption as klnet.c).
