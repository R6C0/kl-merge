# Review of track J: what kills the crew left behind, and `[Bots] FollowOut` (klhook/klescort.c)

2026-10-11, adversarial review. **OFFLINE: the game was not started, nothing written into a game folder, no source or
tool file changed, nothing committed.** Reviewed: the working-tree diff of `klhook/klescort.c` against HEAD 2214b49
(388 lines added; file sha1 66740e58), `klhook/KLHook.ini`, `re/bots_follow_out.md`, the worker's report.

## VERDICT: ACCEPT WITH FIXES

- **The kill rule is right.** Re-derived from the exe with my own commands and replayed against the control log AND
  against a second human-boards run the worker did not use (`PB_DM01_board_hp`, 10:58): every death fits, and that run
  shows the predicted rare case live (one bot outlives state 5, vehicle state 7, round over 3 s later).
- **The code does what the document says**, compiles as claimed, and the scratch rig reproduces (41 / 0).
  No write or call was found that can act on a stock level, off the game's thread, after the round, or for a traitor /
  police human. The timer write has no reader that was missed, and it cannot cost the round by the clock (N3).
- **One MUST before the first run that writes (J1)**, seven SHOULD (three of them about live checks that cannot tell
  success from failure as written), notes. **J0 (dry) may run as the file stands** - from a fresh build (S7).
- Nothing of it has run in the game; this review does not change that.

Words: **READ** = I disassembled it (`debug\dasm.py`, own scripts in scratch `jrev\refs.py`, `callers.py`, `getter.py`);
**MEASURED** = from a live log, a compile, or a run of the rig; **REASONED** = follows from the two, not seen directly.

## 1. The kill rule, re-derived (confirmed)

| claim | result | rests on |
|---|---|---|
| slot 7 = 0x74b6d0, slot 194 = 0x8fa6d0, slot 16 = 0x485740, slot 195 = 0x55ec70 of vtable 0xbd3514 (`ZGameRulesHeist`) | holds | READ the vtable |
| schedule only when client 0 has flag 0x20: `0x8fab77 test byte [ecx+0x1d4], 0x20 / je 0x8faca2` | holds | READ |
| base = now + 0x400 + 1024 * 0.3 * rand; step = 8.0 / [rules+0x354]; time[k] = base + 1024 * step * (k + 0.7 * (2 r - 1)); slot bytes k, then `0x7f87c0` = a shuffle with MSVCR `rand` | holds | READ 0x8fab84..0x8fac9a, the x87 stack followed by hand; constants 0xb172d8 0.3, 0xb39f70 -1024, 0xb19588 8.0, 0xb18cc0 0.7, 0xb59200 1/32768 |
| loop every frame while session state 0x19, client 0 flag 0x20, vehicle state 5: record in use, mask 1, client flags & 0x64 clear, `time <= clock` (signed `jg`): `actor->vt[0x694]` (0x69f900) with amount 0xb631b0 = 1000000.0, then `rules->vt[0x40](actor, 0)` | holds | READ 0x74b7ba, 0x74b8a2..0x74b99a |
| no distance, stage or traitor test; only being aboard saves | holds | READ (the loop reads nothing else) |
| slot 16: record by actor, slot 71 (index, 0), kill text, flag 4, status 7; killer 0 credits nobody | holds | READ 0x485740..0x485823 |
| the tables at rules +0xeec / +0xf1c have no other reader | holds | MEASURED: every instruction of .text holding disp 0xeec / 0xf1c listed; only 0x74b907 / 0x74b910, 0x8fabe3 / 0x8fabfd / 0x8fac8b / 0x8fac93 and the constructor 0x8355db are on this class |
| not in the multiplayer classes | holds | MEASURED: `test byte [..+0x1d4], 0x64` once in .text (0x74b951); 0xb631b0 has ten references, one in a rules routine. The doc names slot 194 = 0x5b1410 for them; the SERVER class's own is **0x51e390** (slot 7 = 0x827f00) - neither refers to +0xeec, +0xf1c or 0xb631b0 |
| after state 5: 0x805120 (status 4 -> 5 -> 6, flag 0x40), round over 3.0 s later through slot 193; 0x4906b0 > 0 -> state 7 else 8 | holds | READ 0x55eda0..0x55edd9, 0x805120, 0x67f480 (client 0 at status 5: 'over' whatever the crew is) |

**Replay 1 - the control** (`PB_DM03_board_hp.log`). The wait's timer reads 0.3 s at 10:15:32.385, so state 5 starts at
about :32.7 (not :32.9), and it ends at :41.13: **8.4 s, not 8.0** (N1). Deaths 2.9 / 4.0 / 5.5 / 8.0 s after the change;
windows `k + 0.3 .. k + 2.0`: slots {1|2}, {2|3}, {4|5}, {6|7} - four different slots exist. Records 0 (human), 1 and 4
(aboard) and 7 (dead before) take the other four. Fits. MEASURED.

**Replay 2 - a run the worker did not have** (`PB_DM01_board_hp.log`, Hot Coffee, 10:58): human aboard 10:58:07.8, state 5
from :15.0 (`van 5 8.4s` at :15.103) to :23.52. Six bots in play; FIVE die in one step each at 1.6 / 3.6 / 5.5 / 6.9 /
7.4 s (slots {0|1}, {2|3}, 4, 5, 6); **record 2 is never shot** - its slot is 7 with a time past the 8.5 s - and the log
then reads `van 7 5.7s`, `2 bot in-play`, `session: state 0x19 -> 0x1f` at :26.523 = 3.0 s after the escape. That is the
doc's 1.3 last point and 1.4, seen live. It is also what `FollowOutSpare` leaves behind, produced by the stock game.
MEASURED.

**Replay 3 - idle human**: `I1_DM01`, `I2_DM02`, `I3_DM03`, `I4_DM06`, `W1_DM02`, `C3_DM03` hold 140 `van 5` lines, none with
`0 you aboard`, and 0 `ONE STEP` lines. MEASURED.

## 2. MUST

**M1 - before J1 (the first run that writes): the stage byte is written for a record whose actor was never looked at.**
`klescort.c` 780-797: the write asks `klb_still` (in use, same actor value, mask 1, status 0, no traitor) but not that
the actor IS one; `havep` (line 755: ZFFActor vtable and a readable node) is computed and only used for the order.
`BoardAll` asks for it (`all_seen`), `kle_bot` asks for it, the task's own rule was 'every pointer chain checked as the
file checks them'. Why it matters: once a record has stage 3 the GAME walks it at every vehicle call and departure with no
test of its own - `0x8fb031 mov ecx, [eax+4] / 0x8fb034 mov edi, [ecx+0x77c]` (READ) - so a stage 3 written into an AI
record with a null or stale actor is a fault inside kl2.exe at the next state 1 / 2 / 5 / 6. MEASURED on the rig
(`rig2.c` R3: record 3 with actor 0 gets stage 3). Not shown that such a record occurs (every bot in the logs has its
ZFFActor), which is why J0 may run; the fix is one condition: no write unless `havep`, with the 'not written' line.

## 3. SHOULD

**S1 - the hold's 'moves' is not 'comes'.** Line 779: 3 m in 2 s in any direction; line 833 holds the vehicle while one
such bot exists. The chain still pulls a stage-3 bot (doc 2.3), so a bot walking deeper into the map holds the driver for
the whole N seconds with the human sitting in a vehicle the police shoot at. MEASURED on the rig (R5: the only bot in play
walks 6 m AWAY, timer 1.8 -> 6.8). `d` (distance to the boarding place) is already there every pass: count a bot when it
came nearer by some metres since its last sample. Until then J2 can show three holds and nobody more aboard.

**S2 - an order can land in the board tactic's own window.** The doc's reason for 'no order while the vehicle waits' is
that a not-soft order cuts the board tactic. That tactic is also live in state 1 / 2 once the timer is under 2.0:
`0x4faff7 fcomp [0xb5c828] (2.0) / jnp 0x4fb015` in its test, the same gate in its run 0x82f9be (READ). Line 800 asks only
`coming`. MEASURED on the rig (R4: crew called with 1.5 s to arrival, three orders). Add `timer >= 2` to the condition.
Related, REASONED: the renewal fires when the defend place is more than 1 m from ours (line 804); the escort part takes up
to 6 m as 'one of the soldier's own tactics moved it' and only more as the route chain (`KLE_ROUTE`). With 1 m a fighting
bot gets a goal-stack pop every `FollowOutEvery` and J1 reads it as 'the chain fights the order'.

**S3 - the spare's table test refuses a table the game accepts, and J0 calls that line 'the offsets are wrong'.** The
constructor zeroes the twelve times (0x8355db..0x83561d) and writes nothing at +0xf1c (READ; the object is 0xf30 bytes
from 0x89e850 -> 0x4a2fd0, no fill seen), so until the first schedule the slot bytes are what the heap held. The game does
not mind (`0x74b91e cmp edi, [esi+0x354] / jge next`); line 650 does: `slot[i] >= n` -> 'do not hold the table this build
knows', nothing written, and `spare_at5` is already set. That is exactly the case the worker wrote the 'without you'
branch for (first departure of a round object with the human not aboard; he boards in the first second of state 5; the
loop then runs on times of 0). MEASURED on the rig (R1: slot bytes 0xcd -> refusal line; R1b: zeros -> put off).
Whether the heap block is zero there: not shown. Fix: when client 0 is not aboard, judge the times only (or take
out-of-range slot bytes as 'never scheduled'); and J5 (a) must not count that line as a fault.

**S4 - the last 'LEFT BEHIND' line can be missing.** Line 728 returns on the human's status before the record walk, so a
bot shot in the same 0.5 s in which state 5 ends is only in the 'over' count. The control's last death is 0.43 s before
`status6`; replay 2's is 1.1 s. MEASURED on the rig (R2: two shot, one line). J0 says 'each also as LEFT BEHIND' and
would read a healthy run as short. Walk the records once more before 'over', or word J0 / J3 by the 'over' line.

**S5 - J1 cannot tell success from failure as written.** A stage-3 bot's loot tactic is OFF only while the vehicle's state
is 3 or 4 (`0x4519dc cmp al, 3 / .. cmp eax, 3 / cmp eax, 4`, READ) and ON while it drives in, and the tactic beats a
defend order (the Late Night finding). In the control records 2 and 5 were earning when the human took stage 3
($375,000 -> $465,000, $550,000 -> $630,000). So for a bot in reach of loot the 7.2 s of drive-in are expected to pass
with no movement; the doc lists exactly that under FAIL ('a bot's D does not shrink') and under PASS ('every called
bot's D is SMALLER'), and 'known' in the same list. Also the speed it tells the lead to take ('D at the call minus D at
the wait, over 7.2 s') is 0 for those bots. Reword: mechanism PASS = the stage lines, the order lines with a snapped
place, no fault; movement is judged from the wait edge to the bot's `aboard` / `dead` line (both carry place and D), per
bot, and against J0's same bots.

**S6 - what the document does not tell the owner about consequences.**
- *The payout.* Doc 1.4: 'his money is his own record's'. Not shown, and the code says otherwise: the round end
  (0x70b920) zeroes the money of every record that did not escape and calls 0x796410, which pools the money of the
  escaped non-traitors (flag 0x40, none of 0x0d), divides by their number (factor 0x7360a0 = 1.0) and gives each of them
  that share (`record+0x28`, `+0x2c`; READ 0x79649f..0x7965f0) - unless the member's client flag 8 or 0x80 is set, then
  it is his own money (0x7965ff..0x796642; what those two flags are was not read - flag 8 is the one the heist triggers
  skip a member for, 0x6893a4 / 0x5a1c57). For the control, if the human has neither: (550,000 + 40,000 + 415,000) / 3
  = 335,000. So the KILL costs the human nothing (dead and left-in-play are both outside the pool - that claim stands,
  and `FollowOutSpare` changes no payout), but **every bot `FollowOut` / `FollowOutHold` gets aboard may move the human's
  cut to the crew's average**. Which number the score page prints was not followed (0x783010). Say it in the key's
  text; have J1 / J2 take a picture of the page and compare with the control's.
- *Traitors.* The traitor tactic's stage term is 0 / 0 / 2 / 3 (klbot.c 3). A bot inside at stage 1 cannot reach the
  stock limit 7.0; raised to 3 it can (3 + 3 + 1). The doc says 'only where the tuning allows traitors: not on Arcade
  levels 1-3' - an owner who wins rounds is on level 4 after three, and `[Bots] Tune=1` allows it everywhere. REASONED
  from klbot.c's table (not re-read). One line in the ini.
- *The stage is for the round*: said, and `FollowOutMoney=1` is a thin guard on a map whose exit box lies on the way.

**S7 - builds and controls.** The report's two DLLs predate commit 14b8654 (klhud.c) and carry the uncommitted
klclimb.c: they are not HEAD. Rebuilt here from the tree as it stands (HEAD 2214b49 + the two uncommitted files): TEST
`3a17e3f2c8ab4e66d3b37331f3579f2e93f1278e`, SHIP `b349d84b0d8934547de98796cc685a390a1e34b7`, in scratch `jrev\test`,
`jrev\ship` - for the record, not for install. Add a control the list lacks: the three keys on a STOCK level (expect the
gate line and nothing after 'on'); the fast pass is new code and its gate should be seen once before the key reaches
the owner's ini. J4 (the spare alone) is independent of everything else and could run straight after J0.

## 4. The live checks: can each tell success from failure

| check | verdict | why |
|---|---|---|
| J0 dry | yes, with S4 | X in 0.3 .. 2.0 is a real proof of rules+0xeec (REASONED from the schedule: the minimum over slots is base +- 0.7); 'no write' is visible in klbot's own stage / van lines. The 'each death as LEFT BEHIND' count is not reliable |
| J1 | **no** (S5) | expected behaviour is listed under FAIL; 'order 2, 3 ..' has two other causes (S2) |
| J2 | mechanism yes, outcome no (S1) | the timer lines, `van 3` for longer and 'it leaves' are sharp. 'More aboard than J1' compares two rounds with random routes |
| J3, J4 | yes | 'no ONE STEP between van 5 and status6', P = K, 0x19 -> 0x1f after 3 s. Add the stock precedent to compare with: `PB_DM01_board_hp` 10:58:23.855 (`van 7`, one bot in play) |
| J5 (a) | **no** (S3) | the line it treats as a fault can come from a healthy build |
| J5 (b), J6 | yes | - |

## 5. The diff, by write and call

| what | touches | thread | stock level | traitor | police human | round over | dead / freed actor | BoardAll / escort |
|---|---|---|---|---|---|---|---|---|
| stage byte (line 790) | record +0x78, max 3; 0x5dd890 writes nothing else (READ) | game thread only (`kle_tick` returns before `kle_follow` otherwise) | no: `klb_level` at 870 | skipped (snapshot and `klb_still`) | no signal: `kle_criminal` | `kle_tick` returns at state != 0x19 | **M1** | same byte, same test; an escort gets the byte, no order |
| order (line 810) | 0x760e50 through `kle_bot` + `kle_order2`, the escort's path unchanged | same | same | `kle_bot` refuses | same | same | `kle_bot`'s tests | not to an escort; not while it waits; S2 |
| timer (line 846) | rules +0x1d8, re-read in the pass; only after the crew was called (`FollowOut=1` needed), human status 4, state 3 / 4 | same | same | - | no | same | - | Bribe / Leave act only with the human NOT aboard: cannot meet |
| times (line 662) | n dwords at rules +0xeec, n <= 12 = the table's size | game thread (`kle_spare_fast` only with `game_thread`) | armed only behind the gate (694), dropped at 863 / 869 / 872 | spared too (stock shoots them) | written, no effect (no flag 0x20) | `kle_spare` asks state 0x19 itself | - | - |

Readers of the timer, my own list: slot 195 (countdown, state changes), slot 45 (state-5 window; writes 0), slots 94 /
149 / 87 / 152 / 194 (writers), slot 191 (HUD text), and through the getter slot 76 = 0x63b300: the board tactic's test
and run (state 1 / 2 only), `ZFATimeDisplay` 0x62a1b3, `ZGameplayTrackerDisplay` 0x8e2740 (MEASURED by a scan of the
getter's callers). The other functions that touch a float at +0x1d8 are other classes (their +0x1dc is a dword). The
worker's list is complete for what decides anything.

## 6. NOTES

- **N1 - the drive-out is 8.4 .. 8.5 s on these vans, not 8.0** (both replays; it comes from the vehicle's own field,
  `0x8fab3e fld [ebp+0x74]`, not from the tuning the hook logs). Consequences: slot 7 misses in about one round of three
  or four, not six of ten (REASONED); record 4 boarded 1.1 s into state 5, not 0.7, and the window is `T0 - (c - 1)` = about 1.4 s
  if c is 8. J0's 'c about 8' still holds (c < 8.3 by that boarding).
- **N2 - 'the game's own hold write'** is true of the address and the 5.0, not of the count: slot 152 adds once per vehicle
  behind `[rules+0xd95]` (READ 0x8b3933..0x8b395f); the hook adds up to twelve times and leaves that byte, so the human's
  own HoldEscape still gives 5 s on top.
- **N3 - the hold cannot lose the round by the clock.** The round-end timer (slot 192 = 0x5dff40) does nothing while the
  vehicle's state is 1 .. 6: `0x5dffc6 mov al, [esi+0x1dc] / test al, al / je / cmp al, 7 / jb out` (READ). A held vehicle
  postpones the end; it does not take the life.
- **N4 - the scripted hits** are as the doc reads them: floor a tenth, a thirtieth a time, ten per wait (READ 0x6db688..,
  0xb45350 = 30.0, 0xb4e7e8 = 0.1; the schedule's step is (timer + 3) / 10 at the change to state 3). They cannot destroy
  the vehicle; real fire can, and 'heavily damaged' sets the timer to 0, which the hold respects.
- **N5 - 0x805120** also works out 'client 0 aboard and everybody else dead or escaped' and hands it to 0x6f8520; that
  routine needs 0x8b9480 (session kind 3), so nothing in Arcade hangs on it (READ). The spare changes that flag and
  nothing reads it here.
- **N6 - clocks.** Movement samples, `FollowOutAfter` and `FollowOutEvery` are wall time (`GetTickCount`); a pause in the
  last 2 s of a wait reads as 'nobody moves'. The hold's seconds are per `kle_r.visit`, which starts again if `kle_r` is
  cleared (a failed `klb_read`, a stage sum that went down): bounded per visit, not per round, in that corner.
- **N7 - the fast pass** runs once per main-loop tick; the tick is skipped when the fallback thread holds `klh_tick_busy`
  (only after a 500 ms stall). The first time is 0.3 s away and the loop of the scheduling frame has already run
  (slot 195 is called at 0x74b7cc, the loop is at 0x74b8a2): one skipped tick does not lose a bot. REASONED.
- **N8 - compile and rig**: /W3 TEST and SHIP, one warning (klhud.c 187); /W4 one in klescort.c (line 332, old code).
  The rig copied to scratch and built against the current tree: 41 checks, 0 failed. MEASURED. My five extra cases
  (`jrev\rig\rig2.c`, R1 .. R5) are the findings above; they are scratch, not in the repo.
- **N9 - J2's run length**: a hold of 25 adds up to 25 s before `van 5`; the board script's waits allow it (15 s steps
  after the boarding), the run's total seconds must too.

## 7. Not checked

The order routine 0x760e50 and 0x7bbf70 themselves (taken from the file's earlier reviews and its live runs); the score
page (0x783010); the traitor tactic's numbers (taken from klbot.c); whether the heap block of the rules object is
zero; anything in the running game.
