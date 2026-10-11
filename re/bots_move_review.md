# Track N (klmove.c: Restless / WaitForYou / BoardNear) - adversarial review

2026-10-11. Reviewer of track N. OFFLINE: the game was not started, nothing written in the game folder, nothing
committed, none of the worker's files changed. Read: `klhook/klmove.c` (all 674 lines), `re/bots_move.md`, the `[Bots]`
sample lines in `klhook/KLHook.ini`, the helpers it calls in `klescort.c` / `klbot.c` / `klhook.c`; kl2.exe re-read with
`debug/dasm.py` and three scratch scanners (displacement, vtable membership, call sites).

## Verdict: ACCEPT WITH FIXES

The MUST of the task (reading (b): a bot is taken aboard from afar) is established and the fix for it (`BoardNear`) is
built on addresses that all re-read correctly. Three MUST points before the lead wires it; none of them is a crash
found in the code, two are false statements the lead would act on, one stops the build.

## What was re-read and holds

| claim | re-read | result |
|---|---|---|
| ZAllyEscapeBox vtable 0xbc7f6c, 34 slots, slot 25 = 0x907a50 | vtable dump + RTTI | holds (slot 34 is 0, then the next class's locator); the first 16 bytes in `kly_scan` match |
| 0x907a50 boards every AI record in play inside the box, no stage / path / distance | whole function | holds: Arcade only (0x7f6850: mode 4, sub 0 / 1), record `+0x79 & 1`, `+0x10 == 0`, 0x758cb0, then 0x74d7f0 |
| 0x74d7f0 -> rules vtable +0xb4 = 0x6840a0 (slot 45); actor branch 0x6841fd | both whole | holds: state 3 / 4 or 5 in its first second; status 4, 0x89c890, `[actor+0x8f0] = 1`, timer 0 when nobody is left |
| the board tactic boards within 300 units | 0x82fa16 .. 0x82fa58, float 0xd19a28 = 90000.0 | holds |
| nothing in the exe compares the box's vtable pointer | every use of the constant 0xbc7f6c | holds: only the constructor 0x541699 and the destructor 0x63f908 |
| exit trigger 0x6c3d50: stage 3, then state 0 and vtable +0x290 == 0, then +0xb0 | whole | holds |
| rules +0x290 = 0x8ad6c0 = `mov al, [ecx+0x1ee]`; set at 0x8fa758, cleared by slot 3 (0x4fb647) | both | holds |
| `[rules+0xe8a]` = no more calls; the rules force the last vehicle by time | 0x8154f0, 0x6cd8e0, 0x81e570 | holds: 0x81e570 calls 0x8154f0 with 1 and does not ask +0x1ee, so WaitForYou cannot hold the last vehicle back |
| loot filter 0x8b9593 .. 0x8b95f6: null, taken, `[obj+0x6c] == 0` | read | holds |
| `+0x6c`: round-over reader 0x5f1b2b, Deactivate 0x4c95e6, 'Activate' 0x4fb5d3 / 0x4fb5e4 | read | holds; Deactivate also writes `+0x64 = 3` and does NOT touch `+0x74` (see S4) |
| a legit grab is not soured | re/bots_loot.md: 0.5 - 0.7 s a part | holds: the bot's money changes well inside 5 s, which restarts its clock |
| the worker's ASSUMPTION 'the exit trigger fires again for somebody still standing in it' | 0x65dd10 (slot 25 of the trigger) | **CONFIRMED statically**: every update it walks everything inside (0x5891f0 loop) and calls vtable +0x88 = 0x6c3d50 for each. It is level-triggered, not on entry. W2 should pass |
| the owner's log lines quoted (bank 12:35:34 - 12:35:49, park 12:43:01 - 12:43:17) | KLHook.log | hold as quoted |
| standing percentages | `n/stand.py` re-run on B1_DM01, W1_DM02, B6_DM06, J1_DM09_join, B1_DM09_board_gates | 52 / 33 / 24 / 39 / 40 %, as reported |
| compile | scratch copy's `build_auto.bat` and `build.bat` re-run; also the WORKING TREE's sources (track O's klbot.c / klbalance.c) + klmove.c + the three lines | both build, no warning from klmove.c. The worker's two DLLs have the sha1s he reports; a rebuild gives other sha1s (time stamps), so they are not reproducible numbers |
| rules file | `git status` / `git diff` | klmove.c and bots_move.md new, KLHook.ini lines inside the [Bots] samples, klescort.c untouched, klhook.c untouched. Every other changed file belongs to another track |
| defaults | `kly_init` | every key 0 / off; `kly.any` 0 returns at the first line of the tick. Arcade only (`klb_read`: mode 4), never on a stock level (`klb_level` before any write or scan) |

The attribution 'the drop's box took records 4 and 5' is an inference, not a reading: it needs 4.1 - 5.1 m/s over
the 18 m / 11 m to the box (half sizes 350 x 416 x 350, re/bots.md), and record 5 ran 4.2 m/s in the same round. It
fits; live check N1 is what proves it.

## MUST

**M1. klmove.c cannot be wired together with track O's klgrudge.c: both use the prefix `kly_`.**
Evidence: `kly`, `kly_r`, `kly_init`, `kly_tick` are defined in both files (klgrudge.c lines 121 - 123 give the same
wiring lines). A scratch copy of the working tree with both includes fails: `klgrudge.c(149): error C2371: 'kly':
redefinition`, `(162): 'kly_r': redefinition`, then member errors. With klmove.c alone the working tree builds. One of
the two files has to be renamed before either set of wiring lines goes into klhook.c, and whichever is second in the
lead's hands silently calls the other's `kly_tick` if only one include is added.

**M2. '`[rules+0x1ee]` is read by nothing else in vehicle state 0' is false: the HUD clock reads it every frame.**
Evidence: `ZFATimeDisplay` slot 5 = 0x62a0c0 calls rules vtable +0x290 at 0x62a262 and 0x62a381, in Arcade, in every
vehicle state, and sets the colour of the clock's text objects (`[this+0x28]`, `[this+0x30]`, vtable +0x20c) to
`[0xbbe498]` = 0xffcc0000 when the byte is set, else `[0xbbe494]` = 0xffcccccc. So with `WaitForYou=1` the round clock
is RED (the 'last vehicle' colour) from GO until the human has his stage. No crash, no rule changes - but the
statement in klmove.c section 2 and bots_move.md 2.2 ('a clean switch ... and nothing else') must be corrected, W1 must
look at the clock, and the lead / owner must accept a red clock or the key needs another handle. (Also: 0x6ba930 is
slot 153 of the multiplayer classes `ZGameRulesFragileAlliance*`, not of `ZGameRulesHeist`; harmless in Arcade.)

**M3. BoardNear's cost to the crew is not written down and no live check measures it.**
Evidence: re/bots_follow_out.md - slot 7 (0x74b6d0) shoots every AI record still in play when the vehicle leaves
with the human aboard. In the owner's bank rounds records 4, 5 and 3 were alive only BECAUSE the drop's box took
them; with `BoardNear=1500` they are 43 m short with at most 8 s (two more visits only if the human is not aboard) and
are shot at the departure. The owner asked for 'physically', and already says the crew dies too fast. Before N1 / N2:
say it in the key's text, run them with `FollowOutHold` or `FollowOutSpare` named, and make 'how many of the crew were
shot at the departure against the same run without the key' part of PASS.

## SHOULD

**S1. Restless (b) has no under-fire test; (c) has one.** A bot fighting from a spot more than 3 m off its defend
place gets its order with reset = 1 ('a running tactic is cut') every 5 s, up to four times (`kly_restless`, branch b;
the `hit_at` test is only in branch c). Add the same 4 s test to (b), and make M2's PASS compare deaths with the I-series,
as M3 does for RestlessHold.

**S2. 'After four orders it is left' can be undone by the part itself, and the chain's place is lost.** After an
order `have_target` is dropped 10 s later and whatever the defend block then holds is taken as the new `anchor` with
`tries = 0` (lines 500 - 504). After a 'beside you' order the block holds THIS FILE's place: it becomes 'its chain's
place', a bot arriving there counts as on a meant wait for good, and one not arriving is ordered every 5 s without end.
The same happens after a plain re-order whenever the game snaps the place by more than 5 units (FO_J1: asked y 278, set
y 150). Keep the anchor while the block still holds what this file put there.

**S3. The loot rule sours money for all bots on the word of a bot that may not be looting.** Branch (a) asks only
'stood within 2 m of a candidate for N s, amount not falling'. It does not ask for stage >= 1 (the loot tactic is off
at stage 0), the bot's 'busy looting' flag (0x2000, re/bots_squad.md) or 'not under fire'. The measured standing is
mostly cover holds BESIDE loot stops: a bot on such a hold can sour a good object for 30 - 240 s. Add the stage test at
least; M1 / M2 should compare the crew's total loot with a run without the key.

**S4. A soured object the level deactivates is re-armed by the hook.** Deactivate (0x4c95d0) writes `+0x6c = 0`,
`+0x64 = 3` and leaves `+0x74`; `kly_sour_pass` / `kly_sweeten` look at amount, `+0x74` and time only, so at the
time-out `+0x6c = 1` goes onto an object in state 3. Remember `+0x64` at souring and do not write if it changed.

**S5. BoardNear's stage write does not have 'BoardAll's guards'.** `kle_board_all` skips `kle_r.used[i]` (this
round's escort); `kly_boxes` part g does not. Small effect (klescort releases the escort when the vehicle waits
anyway), but the comment and the report say otherwise.

**S6. The boxes are scanned once per rules ADDRESS.** `kly_scan` runs when `kly_box_rules != s->rules`. A level
loaded again whose rules object lands on the same address is not scanned: the old entries are dropped as 'gone' (safe,
nothing is written to them) and BoardNear does nothing from then on, with no line. Re-check the entries at each new
round and scan again when one is gone; add a live check 'second round / second load: the `near:` line appears again'.

**S7. The scan's hitch is unmeasured and falls on GO.** It reads all committed private read-write memory through
`ReadProcessMemory` in 64 KB pieces (klmem's reserve with the .prm included). '0.1 - 0.5 s' is an estimate. M0 prints
the milliseconds: make the number part of M0's PASS.

**S8. In vehicle state 5 every box is denied.** `called` is state 1 .. 5 and the boarding object leaves with the
vehicle, so with any BoardNear the stock 'first second of state 5' boarding from the near boxes is cut too. Decide the
denial while the vehicle stands and keep it through state 5.

**S9. WaitForYou parks the crew in the open.** A bot through the exit trigger stands at its last place - the
escape box beside the vehicle's stop - for up to `WaitForYouMax` = 150 s. The owner did not ask for this key (the
report says so); if it is tried, W1 needs the deaths against I3.

**S10. Sours are forgotten without being put back when `klb_read` fails once** (tick, lines 594 - 598: `on = 0` for
all). Right when the level is gone; if the read fails for one pass mid-round the objects stay off for the AI until
something opens them. Keep the entries and let `kly_listed` decide.

## Not found

No write to memory that is not checked first (money object: vtable + still in the rules' list; rules byte: vtable,
state, value; box: found by vtable with a plausible entity; stage byte: `klb_still`; timer: re-read). No game routine
called that was not read (0x760e50 through `kle_order2` with `kle_bot`'s tests, as Escort does; 0x907a50 is the
wrapped original). Nothing on a stock level, nothing outside an Arcade session. No way to deadlock a round: the exit
trigger is level-triggered, `WaitForYouMax` releases, the rules' forced last vehicle ignores the byte, BoardNear's
boxes work again from visit 3 and for the last vehicle. State is reset at a new round, for a reused record
(`actor` change), and for a fed / dead / aboard human (release). The wrapper thread question stays as the worker
marked it (NOT ESTABLISHED).
