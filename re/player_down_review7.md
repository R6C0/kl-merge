# Review 7 of the knock-down: track R7 (`[Down] Camera`, `CameraSide`, `Prompt`) - adversarial

2026-10-11 evening. Offline: nothing here ran in the game, nothing committed, the worker's files not changed.
Reviewed: `klhook/kldown.c` sha1 754c7dea306fc229f3ce3fcc7ff59e18fce17ad9 (diff against HEAD 7efe1a1, read line by
line), the `[Down]` lines of `klhook/KLHook.ini`, `re/player_down.md` section 13. kl2.exe 0490 re-read with
`debug/dasm.py` and the worker's scratch `xref.py` / `disp.py` / `who.py`.

## Verdict: ACCEPT WITH FIXES - the scripted runs C0 .. C8 may go ahead as the code lies

No fault found in the code that would stop a live test. One MUST, and it is in the TEXT (a wrong label that hides
the best news of the track): the prompt element is not 'assumed' to be the human-shield break-free - it IS, by the
code the worker filed under 'the rise after a ragdoll throw'. Seven SHOULD points.

## What was tried to refute, and held

| claim | how checked | result |
|---|---|---|
| the mask dword is the local player's | 0x484553 `mov eax,[esi+8]` then 0x484574 `movsx edi, byte [eax+0x91e]`: `[input+8]` is the player; `kld_mask` walks `[gamedata+0x1590]` by `[player+0x91e]` as 0x8ee23b .. 0x8ee253 does | HOLDS. `[player+0xed0]` is right |
| bit 0x10 gates the mouse look and nothing else | every `[reg+0xed0]` in .text listed (`disp.py ed0`): the byte tests are 0x417310 (5), 0x76fd40 (3), 0x4d9ec0 (0x30), 0x87d930 (0x50), plus 0x7dffe0 (bit 8) and 0x8818a0 / 0x6400ad / 0x846513 (bit 0x80) which the report does not name; 0x4d9ec0 and 0x87d930 have ONE caller each, 0x4845bc / 0x4845cf, and what they zero is `[H+0x3e0]` / `[H+0x3e4]` only. All other `+0xed0` hits are other classes (a pointer, a ring index) | HOLDS. Taking 0x10 off gives back neither move (bit 1 stays: 0x417310 / 0x76fd40) nor any button (bit 0x80, not set by the fall) nor fire / cover (not in this mask at all) |
| stock takes 0x10 off in the fall, both at its end | 0x8ee22e .. 0x8ee260 (`push 0x10`, 0x787600) under 0x843fa0; 0x8ee31e / 0x8ee327 | HOLDS |
| the fall sets 1 and 0x10 once | 0x76a827 / 0x76a830, in 0x76a450; 0x6feb90's other callers are 0x7cea44, 0x84af60, 0x860dc0, 0x8d64f0 (see M1) | HOLDS |
| the setter's writes | 0x74a120 read whole | HOLDS, one write left out (S5) |
| the OSD lookup | 0x588680 = `[gd+0x15dc]`; 0x4ddae0: index <= 1, byte `[mgr+8i+4]` != 0xff, `[mgr+8i]` | HOLDS, `kld_mash_elem` is that routine |
| the element's fields | Tick 0x8ac6ba (`[E+0x50]`), 0x8ac6e1 (`movsx byte [E+0x5c]`), 0x8ac7b8 (`[E+0x10]`), 0x8ac829 / 0x8ac85b (`[E+0x54]` / `[E+0x58]`), 0x869fd0 (cap `[0xcef0ec]`); Render 0x48f4b6 / 0x48f4c0 (`[E+0x24]`, `[E+0x50]`); 0x47e230 | HOLDS |
| button 0 = the Cover byte | 0x4425de .. 0x4425e8: `[E+0x5c]` = 0 with `al = [player+0xeb4]` | HOLDS |
| a game path that clears the element every frame (would fight the hook) | all 30 functions that load `[osd+0x10fc]` looked at: every write of `[E+0x50]` sits behind a state test (a shield hold, the mash entity, the buddy game) or in a reset (0x708500 = rules slot 4) | none found: HOLDS |
| Flop=0 / 1 / 2 / 3 unchanged | the diff of the old code is three added statements (`kld_v.rate = rate` twice, `kld_v.act / pl` once), the rename, a comment; `kld_camera` acts only with `kld_s.fnow` (never Flop=0, never Dry), after `kld_tick_main`, so the first-pass mask proof (line 1060) still reads 0x11; the end's AND of 0x11 and its put-back on a refused state write work on 0x01 as on 0x11 | HOLDS |
| nothing on a stock level / for a fed / off the game thread | `kld_v.act` is zeroed before `kld_tick_main` and set only after `klb_level` and the police test; the wrapper returns on `!game_thread` | HOLDS |
| klhud.c untouched by this track, no klhud helper called | no `klu_` / `klhud` symbol in the diff; `git status`: klhud.c is modified in the tree (track V), not part of this diff | HOLDS |
| the compile | `git archive HEAD klhook` + this kldown.c in `G:\kl_scratch\R7rev\src`: 'built ...\test\dinput8.dll (TEST)' b6609f6d, 'built ...\ship\dinput8.dll (SHIP)' 4f28ad40 (a hash is per build); the only warning klhud.c(285) C4101 | HOLDS |

## MUST

**M1. The label 'the rise after a ragdoll throw' is wrong: 0x860dc0, 0x8d64f0 and 0x4424f0 ARE the human-shield
struggle. Correct the head comment of the block, section 13.2 / 13.5 and the report before the owner is told
anything is 'assumed'.** Evidence:
- 0x860dc0 has one caller, 0x7fa515, inside 0x7f9eb0 - the human-shield part of the player's frame - behind
  `test eax, 0x100`. It works on `[player+0xad4]` (the carrier) and `[player+0xad0]` (the victim) and the two tap
  floats `[+0xae4]` / `[+0xae8]` - the very `fTaps` of section 3 (`RMCSetHumanShieldPvPTapsShield / ..TapsCarrier`:
  0x8288e0 and 0x4ac030 are the two senders called here).
- Carrier's branch (0x860ddb): 0x4424f0 draws one of the FOUR buttons at random (`[0x1548e08]`, drawn again on the
  timer `[player+0xaec]`), writes it into `[E+0x5c]` and returns that button's input byte; a press adds 1 to
  `[+0xae4]`, each frame takes `[0xce8a8c]` x the value off, the value goes to `[E+0x54]`.
- **Victim's branch (0x860ed3 .. 0x861075) = the break-free the owner means**: once the carrier's taps are over
  `[T+0x680]` x `[0xb794c0]`, 0x860f36 sets `[E+0x50]` = 1, `[E+0x58]` = `[T+0x680]` x `[0xb21fe0]`, **`[E+0x5c]` = 1
  = `{TapUse}`**; a press of Use (`[victim+0x818]` bit 0x20) adds 1 to `[+0xae8]`, each frame takes `[0xce8a90]` x
  the value off, the value goes to `[E+0x54]` (0x860ffa); at `[T+0x680]` x `[0xb6e5c0]` he is free and 0x861071
  clears `[E+0x50]`. The colour is never touched there: white.
- 0x8d64f0 (0x8d6628: shown, max `[T+0x680]`) is called from 0x4d7b00 and sets the same mask bits 1 / 0x200 / 0x400
  as 0x860f7b: the start of a hold, not a ragdoll.

So: (a) 'this element is what the human-shield break-free shows' is READ, not assumed - strike the assumption and
the 'where the victim's struggle switches it on was not found' lines; (b) the 'KNOWN: a ragdoll throw during our
knock-down has its own use overwritten' is not a ragdoll case: the only other users are a PvP shield hold and the
campaign's mash entity, neither of which exists in an Arcade round with one human - say that instead; (c) the true
look to compare with is: `{TapUse}` picture + 'Tap Quickly' + a WHITE bar that is the victim's own tap meter and
falls back when he stops (see S3).

## SHOULD

**S1. A round end is not among the off conditions.** `kld_v.act` comes from `klr_arcade`, which does not look at the
session state (`[session+0x70]`: 0x19 in play, 0x1f the score page); `kld_dead` knows only health 0 and statuses
7 / 1. A round that ends while he is on the floor (the round clock, the last crew member's death) leaves `want` = 1
until the clip is through or the time bound stops the part - up to ~9 s of prompt over the round's end. The task
asked 'it must vanish at ... a round end'. Either gate `want` on the session state the part already has (`state`
of `klr_arcade`, the values klbot.c / klauto.c use for 'in play'), or at least add a live check C9 (the round
clock run out 2 s into a knock-down: `prompt: OFF` before the score page's picture).

**S2. `kld_prompt_off` after a level change writes through a remembered pointer whose only guard is 'the vtable
still reads 0xbbe8f0'.** Freed memory keeps its bytes on many heaps; then three writes go into a freed 0x12c block.
The paths that get there are narrow (the pause test and `act` switch it off first), but cheap to close: remember
the rules object (`klr_arcade`'s `rules`) or the OSD pointer at ON and write the OFF only when `kld_mash_elem`
of the still-valid player returns the same element; otherwise just drop `ours` (the element died with its level).

**S3. `PromptStyle` default and the red pulse against 'very similar'.** By M1 the game's break-free bar is a mash
METER: +1 a press, a share taken off every frame, white. That is `PromptStyle=2` without `PromptPulse`. The default
(1 = progress, red flash) is a design choice of the hook - defensible (a man who does not tap still sees when he is
up), but the owner's words were 'very similar': show him both in C1 / C3 and let him pick, and say in the ini text
which of the two is the game's own behaviour. The picture differs too: the break-free shows the Use key, ours the
Cover / GET UP key (right for what the mash reads - say so).

**S4. One more reason for 'ON in the log, nothing in the picture': the OSD's 'HUD off' byte.** In the element loop
0x8bf583 .. 0x8bf5cd, while `[osd+0x1225]` is set the mash element is drawn only when `[[player+0x2940]+0x24]` is
2 .. 0xd (the game's own mash states); otherwise it is skipped like the rest. Add `[osd+0x1225]`, `[E+0x24]` and
`[E+0x25]` to the ON line (three reads) so a silent C1 names its cause in one run.

**S5. The setter's data form leaves out `[player+0xb8c]` = 0 (0x74a1a8)** - and the notes' list of its writes does
too. After the down start's own call it is 0 already, so the form is complete in the case built; but a delayed side
change armed before the fall (`[+0xb88]` timer, `[+0xb8c]` = +-1: the branch 0x74a15f) would fire in the fall and
is not seen by the three-writes cap as 'the game forcing left'. Name the field; a read of it in the side line is
enough.

**S6. Two blend restarts in two frames.** The down start flips to left and restarts the camera's blend
(0x4719f0); the hook flips back one pass later and restarts it again. Probably invisible, possibly a twitch at the
moment he is hit: add 'no sideways jerk of the camera in the first picture of the fall' to C1's PASS column, and
`CameraSide=0` as the remedy.

**S7. The pause test.** It runs only while `want`, compares against a `gtick` / `t_gtick` that may be stale from
the last down (one pass of `want` = 0 when the tick value repeats - harmless), and a single frame over 250 ms (a
hitch, a streamed load) gives an OFF / ON pair in the log that C1 would read as a fault. Say so in C1's FAIL
column, or raise the bound to 500 ms. That the tick stands in the pause menu stays ASSUMED (C4 decides).

## Still open after this review (not faults of the track)

- Whether freeing the look from the first frame of the dive turns the body or the clip's direction: only C1's
  pictures can say. Stock is in that state from 0.72 s on in the same D state 2, which is a fair argument.
- Whether the scripted player's mouse reaches `[[gamedata+0x1590]+0x2c]`: if the rig cannot move the mouse, the
  camera half of C1 is the owner's hand.
- The pad's look stick was free already by the reading of 0x4844e0 (not gated by 0x4d9ec0 / 0x87d930): agreed, not
  followed further.
- The low camera's source instruction: not read, not needed for what was built.
