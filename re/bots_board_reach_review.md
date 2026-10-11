# Review of track N4: `[Bots] BoardReach` (klhook/klmove.c section 4, re/bots_move.md 9)

Adversarial review, 2026-10-11 evening. Offline: kl2.exe read again, the diff read line by line, the compile re-run.
NOTHING RUN IN THE GAME (neither by the worker nor here). The worker's files were not changed.

## Verdict: ACCEPT WITH FIXES - one MUST before the first live run that is meant to show anything (R1)

The reading of the exe is right and the re-implemented update is faithful. The filter has one hole in time (M1) through
which exactly the bots the owner complained about still go aboard from afar. R0 (dry run) may run as it is.

## What was checked and holds

- **0x907a50 (164 bytes), read whole again.** Arcade test 0x7f6850, rules by 0x508ef0, the place cache at box +0x4c
  when node flag 0x20000000, then one loop: count = rules vtable +0x50 asked every time round (signed char), record =
  `[rules+0x348] + 0x7c * (byte)i` (0x7fd930 is `movzx / imul 0x7c / add [ecx+0x348] / ret 4`), `+0x79 & 1`, actor `+4`,
  status `+0x10 == 0`, 0x758cb0(box, actor), 0x74d7f0(rules, i). `klmv_ally_reach` makes the same calls with the same
  arguments in the same order; `continue` re-asks the count as the stock loop does; index, signedness and the
  `__fastcall`-for-`__thiscall` forms match the callees' `ret N` (0x758cb0 ret 4, 0x74d7f0 ret 4, 0x7b3020 one stack
  argument, 0x7f6850 / 0x508ef0 / vtable +0x50 none).
- **0x74d7f0, whole:** `[rules vtable +0xb4](record's actor, 0)` = 0x6840a0. **0x6840a0, whole:** session state 0x19;
  vehicle state 3 / 4, or 5 in its first second; the NPC branch (0x6841fd) finds the record by 0x78f470 and does
  nothing unless its status is 0, then sets status 4 AT ONCE. So: no record can be boarded twice (the second caller
  finds status 4, and the wrapper's own `rec[0x10]` test skips it before that); a dead / aboard / escaped record is
  skipped as in stock; no stage, traitor or distance test exists in the game's rule, so the wrapper refuses nobody
  the game would take except the far ones, and takes nobody the rule itself would refuse (wrong vehicle state, wrong
  session state: the rule returns).
- **The human's own boarding is untouched:** both the stock loop and the wrapper act only on records with the AI bit;
  the human goes through the action and 0x6840a0's player branch (0x684115), which this file never calls.
- **Guard bytes:** the 164 bytes of `whole[]` and the six 16-byte heads compared with the exe by script: all equal.
- **Frame maths:** `klmv_frame` uses the same row order as the game's 0x6be1c0 (x' = x*m6 + y*m3 + z*m0), so
  `half[k]` pairs with the right world axis; the box test 0x4aca80 is `|local| <= [ent+0x14+4k] (+ margin)` = half
  extents, as said.
- **Off by default / stock level / multiplayer:** with `BoardReach=0` `klmv_rc.on` is never set, `klmv_boxes` is
  entered only for `BoardNear` as before, and the changed lines in it are no-ops when `near_ > 0` (the two added
  `klmv.near_ > 0 &&` tests were implied by the old call site). Boxes are scanned and wrapped only behind the
  existing `klb_level` gate; the stand-down path clears `on`. 0x508ef0 gives a rules object only in Arcade.
- **`klmv_stage3`** is the old block (g) moved into a function, condition for condition; only the texts differ.
- **Round / visit state:** `klmv_r` (with `rc_visit`, `rc_told`, `rc_wait_at`) is zeroed at a new round together with
  `klmv_rc.on` and `klmv_rc.rules`; bits 16 / 32 of `told` are cleared at each new visit.
- **Second visit, helicopter, traitor, escort, dead record:** second visit re-reads the box (same code path, new
  `rc_visit`); the park's pad is a ZBoxPrimitive, handled as a box, turned 20 degrees = the oriented distance is
  needed and is what is computed; a traitor in a box within reach boards as in stock, beyond reach he is refused and
  gets NO order (S5); an escort still held gets no order and no stage write, as for BoardNear.
- **Can the round fail to end?** No. A refused bot only stays 'in play'; with the human aboard the wait timer runs out
  and state 5's rule (shoot, or FollowOutSpare) ends it; without him the round clock does. FollowOutHold is capped
  per visit. What CAN happen is a bot that never boards on any visit (S2).
- **Files:** klmove.c, re/bots_move.md and the `[Bots]` sample lines of KLHook.ini only (the `[Balance]` lines in the
  same ini diff are another track's). Guesses are marked in code and text (KLMV_SENT, the 'node = polygon' reading,
  the action's 50.0, the thread).
- **Compile re-run** (`git archive HEAD klhook` + this klmove.c, `G:\kl_scratch\N4_review`): TEST and SHIP both
  `built ... dinput8.dll`, no warning. sha1 dd0faad3 (TEST) / e3847180 (SHIP) - NOT the worker's 711e1da6 / 6699c2e3:
  the builds carry their build time, so the sha1 of a rebuild proves nothing; `klmove.c` in the worker's scratch
  source is byte-identical to the tree's.

## MUST

**M1. The filter is armed up to 250 ms late at every visit, and in that time the STOCK update boards everybody in
the box.** `klmv_rc.on` is set only by `klmv_reach_pass`, which runs from `klmv_tick` (`if (now - last < 250) return;`,
klmove.c line 946) and only once it sees vehicle state 3 / 4 (`have`); in states 0 / 1 / 2 it clears `on`. The box's
update runs every frame (the owner's log: a denied box 'asked 6001 time(s)' in one visit), and 0x6840a0 takes a
record from the first frame of state 3. So between the vehicle's change to state 3 and the next tick - 125 ms on
average, 30 frames at his frame rate - `klmv_ally_tick` falls through to the stock 0x907a50 and every AI heister
ALREADY STANDING in the escape box goes aboard at once, from up to 13.2 m. That is the usual case on Hot Coffee, Late
Night Opening and The Vault (9.2: the crew's last places are inside the box) and it happens again at every later
visit. Only bots that enter the box after the first tick are filtered. (BoardNear has the same hole for its `deny`
flag; it did not show in N1 because nobody stood in the far box at the arrival.)
Fix, either: (a) the wrapper itself reads `[rules+0x1dc]`; in state 3 / 4 / 5, on a level the tick has passed as
'not stock' in this round, and with no boarding box read for THIS wait yet, it reads the box itself (`klmv_frame`
is safe reads only) or leaves out 0x74d7f0 for every inside record until the tick has delivered the frame; or
(b) keep the wrapper armed through the whole round on such a level, with 'frame not valid for this wait' = nobody
is taken by a box (the rule takes nobody outside 3 / 4 / 5 anyway, so nothing else changes). Add a live-check line:
R1 PASS needs NO `bots: record N (bot): aboard` in the first second of a wait without a `reach:` line for it.

## SHOULD

**S1. The proposed value is not 'just as close' as the human.** The human must be INSIDE the 95 x 135 box (at most
1.65 m from its middle at a corner). `BoardReach=200` measures from the box's SURFACE: a bot boards up to about
3.65 m from the middle, from any side - also beside the van's flank. That equals the board tactic's own 3 m, which
is a fair argument, but the owner's words are 'even i couldnt get in that point'. Say so to him, or propose 100; the
minimum the code allows is 50.

**S2. `BoardReachVisits=0` (never) with no exception for the round's last vehicle.** BoardNear relaxes at visit 3 and
at the last vehicle (`[rules+0xe8a]`) so that nobody is stranded for good; BoardReach does neither by default. A bot
whose tactic finds no way (the 'one node' guess, the bank's yard without the drop link, a stage-0 bot or a traitor,
S5) then stands in the box at every visit until the round clock - and in the idle-player series (I1 - I5) that is
how six or seven of seven escaped. Default 3, or at least the last vehicle as with BoardNear; the text for the
owner must say what he will see otherwise.

**S3. The doors path grows with the key.** `BoardReachDoors` takes any stage-3 bot within BoardReach of the boarding
box that stands in NO escape box. With the 'try `BoardReach=300`' of 9.6 that is harmless, but a large value
(`BoardReach=1500`, somebody copying BoardNear's number) boards bots from 15 m where stock has no box at all - worse
than stock. Cap the doors path (for instance `min(BoardReach, 300)`) or clamp the key.

**S4. The doors path hangs on ONE box being updated.** Only the level's 'first' wrapped box does it. On Retomoto
that box stands in the tower, 198 m up; whether its controller is updated while everybody is in the street is not
known, and on a level without a box there is no doors path at all (logged). Boarding is idempotent (status 4 at
once), so every wrapped box may do the pass - or say in R4 that a missing `AT THE DOORS` line there means this.

**S5. Who is refused and then moved by nothing.** A traitor (no order by design, no stage write), a stage-0 bot
(`klmv_stage3` asks `stage >= 1`) and a bot more than 30 m off get neither order nor stage; in stock the box took
all three. Not a fault of the round, but it should be in 9.7 and in the `reach:` line at the departure.

**S6. The human's zone is still partly unread** (the worker says so): the player-side test and the entry's 50.0 /
tuning +0x320 / +0x324 were not read; 'at most 1.24 m' is the box alone. R0's box line checks the box, not what
the game asks of the human. One scripted measurement (walk at the doors until the 'get in' prompt shows, log the
place) would settle it.

**S7. Thread.** `klmv_rc.fr` (60 bytes) is rewritten by the tick with `on` cleared first; an update running on
another thread in the middle of its loop would read a half-written frame. Marked 'NOT ESTABLISHED' by the worker;
a sequence counter read before and after in the wrapper would make it safe either way. Low.

**S8. Small.** (a) In a dry run `klmv_reach_pass` goes on although the guard failed (`klmv_reach_ok <= 0 &&
!klmv.dry`): the 'WOULD' lines then describe an update that would never be used. (b) The doors line says 'in no
escape box' when the bot was only outside the FIRST box. (c) `BoardReach` acts for a police human too (FollowOut
does not): the crew then has to reach the doors with nobody holding the vehicle - say it. (d) The rule's entry
0x6840a0 behind 0x74d7f0 is not among the compared heads (the rules vtable is klbot's own check; cheap to add).
(e) Report the sha1s as 'of that build', not as something a rebuild reproduces.
