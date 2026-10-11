# BoardAll after the rework (klescort.c, commit 999c304) - adversarial review

2026-10-11. OFFLINE: the sources at HEAD (999c304; the working tree has no change under `klhook/`), kl2.exe build
0490 read with `debug/dasm.py` / capstone, the saved live logs `<work>\build\klhook\live\L8_DM02 / L10_DM02 /
L11_DM02 / L12_DM02` and the game folder's `KLHook.ini` / `KLHook.log` (read only). **Nothing was built, started,
installed, changed or committed.** Status words: **read** = seen in the code or the disassembly at the place named;
**measured** = from the log named; **not read** = a gap, said as one.

Scratch scripts (session scratchpad, folder `rw\`): `held.py <log> [seconds]` replays `kle_all_track` and the HELD test
on a saved log, `money.py <log>` lists every bot's earnings and the gaps between them. They sample at the log's rate
(places every 5 s, money once a second); the hook samples every 0.5 s. So a 'stood' time here is an estimate.

## Verdict

**SAFE_TO_RUN_LIVE** - for L12 as a scripted TEST-hook run with the owner away and the game window in front.
No 'must'. The rework is narrower than the form both first reviews already passed for L12: by default it makes NO
game call, it writes one heap byte with the value the game's own 0x5dd890 writes, for fewer records, after the record
is checked again. No path was found that writes with BoardAll=0, in a dry run, with BoardAllStage=0, off the game's
thread, outside session state 0x19, on a stock level, into a human's record, or past the tables.

**Not for the owner's own KLHook.ini yet.** Four 'should' items (section 5): the stillness clock is wall time (a
pause or Alt+Tab makes standing bots 'held'), the new test in `kle_bot` DROPS a held escort for good instead of
waiting, the Van / VanLeftBehind clash is a comment and not an interlock, and the key's text names L8 / L10 as its
reason although BoardAll would not have acted in either (the vehicle never came). And one thing to know before
reading L12: **'held' as coded is 'stands and earns nothing', not 'held by loot'** - in L10 / L11 most such spells
ended by themselves (section 4).

## 1. The six claims of the rework

| # | claim | finding |
|---|---|---|
| 1 | only a HELD bot is raised | **holds** as coded: `kle_board_all` :450 (in use, AI, no traitor, status 0, never `kle_r.used`), :453 (stage 1 or 2), :454 (place read this pass), :455-456 (`now - all_since >= BoardAllStill`); `kle_all_track` :421-432 restarts the clock on a move of more than 100 or any change of money, every pass that reaches it. What 'held' catches: section 4. What the clock counts: defect S-A |
| 2 | the stage byte alone, through `klb_put8` after `klb_still` and a second read | **holds**: :457-463. `klb_still` (klbot.c:494-501): free byte, record address, same actor, mask 1; then status 0, no traitor flag, the byte read again, written only when under 3. No order unless `BoardAllOrder` (:469) |
| 3 | the order only with BoardAllOrder=1, once per visit, retried | **holds**: :469-479. Reached only for a record this file judged held (`all_raised` 1 or 2). See note N-B for the dry / Stage=0 case |
| 4 | `kle_bot` refuses a running defend goal with an empty goal stack | **holds, and the test is the right one** (read: 0x760f13..0x760f2b take the 0x7bbf70 branch only for goal state not 0 / 4 and not soft; 0x7bbf9f `mov ecx,[ebx+4]` / 0x7bbfa7 `mov edi,[ecx]` / 0x7bbfaf `mov byte [edi+0x11],1` with no test; 0x7bbfc6 `add dword [esi+4],4` shows +8 is the end pointer and the element is 4 bytes; 0x5ca0b7..0x5ca0bf int3 on begin == end). **Side effect not intended: defect S-B** |
| 5 | comments say what the exe says | **mostly**: :29-34, :40-48, :93-94, :135-158, klhop.c:58-60, klhook.c:31-33. Read again here: jump table 0x8fb098 = {0x8fafa0, 0x8fb06b}, byte table 0x8fb0a0 = 00 00 01 01 00 00 -> the pass for states 1, 2, 5, 6; 0x4fb064 `cmp byte [eax+0x78],3 / jb`; 0x4519d4 `cmp al,1 / jb`, 0x4519dc `cmp al,3 / jne`. Left over: note N-G |
| 6 | R+0x1c scales the fire of an Ally SHOOTER not at the player's stage | **confirmed in the exe**: the caller pushes `esi` then `ebx` at 0x61ad14 / 0x61ad15, so the first argument is `ebx` - the actor whose soldier's float `[[ebx+0x77c]+0x704]` multiplies the damage just before (0x61acd3..0x61ace9), i.e. the attacker; `esi` is the hit routine's own object. 0x591bb3 `mov ecx,[esp+0x14]` is that first argument; its team picks R+0 / R+4 (0x591bc0..0x591bd9) and its crew record's stage (0x78f470, 0x591c00) is compared with the local player's (0x6c7700, 0x591c17); unequal -> times `[R+0x1c]` (0x591c1d). klbalance.c:31-35 and re/balance.md are right now |

## 2. Every defect of the two reviews

Line numbers are klescort.c at 999c304 unless another file is named.

### re/boardall_review_exe.md

| id | where | status | evidence |
|---|---|---|---|
| S1 | `kle_bot`: empty goal stack under 0x7bbf70 | **FIXED** | :261-264; only when the goal runs (the review's form refused in the idle case too - the rework's is the exact branch). Brings S-B |
| S2 | `kle_board_all`: write from the snapshot without `klb_still` | **FIXED** | :458 `if (!klb_still(s, i, &fl, &st) \|\| st \|\| (fl & 2) \|\| !klh_rd(r->at + 0x78, &cur, 1)) continue;` :459 `cur < 3 &&` |
| S3 | `kle_board_all`: silent return without a boarding place | **FIXED** | :443-447 no return; one line per visit when the order is wanted; the stage part no longer needs the place; :469 `!have_bd` |
| S4 | comments state what the exe does not do | **PARTLY** | fixed: :29-34 (0x6e49b0, 0x7bbf70), :40-48, :93-94, :135-158, klhop.c:58-60. Left: :402 log text 'the game's rules send it aboard themselves', :526 comment 'the rules have sent it themselves' (it is the bot's own board tactic while the vehicle waits) |
| S5 | klbot.c Van / VanLeftBehind reads stage 3 as 'at the vehicle' | **PARTLY** | text only: :153-154 and KLHook.ini:254 'DO NOT combine'. klbot.c:603-609 unchanged, no skip of raised records, no interlock; klbot.c's own Van text (:134-135, :192) and KLHook.ini:226-232 say nothing. Defect S-C |
| N1 | a raised bot shoots police at R+0x1c | **NOT FIXED** (documented :151-152; klbalance.c:71-72 'a key for it is owed') | by design |
| N2 | traitor stage points, Backstab's stage test | **NOT FIXED** (documented :152-153) | klbot.c:560 unchanged |
| N3 | kltalk 'Stage2' line for a bot that never left | **NOT FIXED** (documented :154) | kltalk.c not in the commit |
| N4 | escort ordered twice; EscortBoard=0 overridden | **FIXED** | :450 `kle_r.used[i]` -> the record is never BoardAll's |
| N5 | `all_told` a counter that wraps | **FIXED** | :460 bit 1, :471 bit 2, each set once |
| N6 | 'escort' wording with Escort=0 | **PARTLY** | :497 gate line says 'board' when no escort, :507 `kle.n &&`. :500 still 'escort: the tick is not on the game's thread ... nothing is ordered' whatever is on |
| N7 | balance.md / klbalance.c: shooter and victim swapped | **FIXED** | claim 6 above |
| N8 | maps with no path to the boarding object | **NOT FIXED** (documented in LIMITS :149-150) | stays a reason not to make BoardAll a default for all five maps |

### re/boardall_review_code.md

| id | where | status | evidence |
|---|---|---|---|
| D1 | old :406: a record at stage 0 is raised | **FIXED** | :453 `if (r->stage < 1 \|\| r->stage >= 3) continue;` and :450 for the ex-escort. Its second half (a second value of `all_raised` so that 'looked at, not written' is told apart) is **PARTLY**: :464 stores 2, nothing reads it (note N-B) |
| D2 | old :399: no boarding place = silent return, no stage write | **FIXED** | as S3 |
| D3 | source contradicts the exe; stale 'no data write' | **PARTLY** | as S4; :5-7 and klhook.c:31-33 fixed; :567 'no write' is the escort's own line and true of it |
| D4 | escort handled twice, EscortBoard=0 overruled | **FIXED** | :450 |
| D5 | the order's place is on the van's approach | **FIXED by default** (:469, BoardAllOrder=0; said at :157-158); unchanged with BoardAllOrder=1 |
| D6 | `all_told` char, two messages share it | **FIXED** | as N5 |
| D7 | a guessed new round forgets `all_raised` | **NOT FIXED** | :491-492 unchanged. With the order off the named harm is gone; new: the same memset forgets `used[]`, so an ex-escort becomes BoardAll's, and every clock restarts. Not seen live (every fall of the stage sum in the logs is between rounds) |
| D8 | with Escort=0 the tick talks about an escort | **PARTLY** | :497, :507, :540-543 fixed; `t.told_soft = 1` gone (:475), so with BoardAllOrder=1 the 'taken as soft' line can come - worded 'escort: record N ... (said once per escort)' and said at every such order (note N-G) |
| D9 | other parts read stage 3 as 'at the vehicle' | **PARTLY** | listed at :151-154 and KLHook.ini:254; no code excludes a raised record |
| D10 | vehicle state 8 exists | **REFUTED as a defect of BoardAll** | it acts on 3 / 4 only (:503); klbot.c's comment (0..7) was not touched |

## 3. The code, path by path

Read line by line: `kle_all_track` :421-432, `kle_board_all` :440-481, `kle_tick` :483-534, `kle_init` :536-569,
`kle_bot` :245-268, and what they stand on: klbot.c `klb_read` :265-287, `klb_still` :494-501, `klb_put8` :485,
`klb_pos` :673, klhook.c `klh_may_write` :305-322, `klh_data` :340-348, `klh_tick` :592-622, the wrapper :628-634.

Gates before anything of BoardAll runs (`kle_tick`): :487 a key is on, klbot.c on, the exe is build 0490, 500 ms
since the last pass; :489 `klb_read` (Arcade, ZGameRulesHeist, 1..32 records); :495 session state 0x19; :496
`klb_level` (the Steam guard is on and the archive is NOT stock); :500 the game's thread (a return address inside
the main loop 0x87a930..0x87ab40 on the main thread, klhook.c:630-633). Only then :506
`if (kle.all) { kle_all_track(&s, now); if (waiting) kle_board_all(&s, now); }`.

| setting | what happens (all read) |
|---|---|
| BoardAll=0 | neither function is reached (:506); no other caller of `klb_put8` in the file |
| [Bots] Enable=0 | `kle_init` :540-544 returns with `kle` zero; one line if BoardAll or Escort was asked for |
| Escort=0 | `kle.n` 0: the escort loop (:512) and `kle_pick` (:533) do not run, `used[]` stays 0, every AI record is BoardAll's. `kle.dry` is read before the `!kle.n` return (:551), so EscortDry works alone. `kle_human` is still called each pass (reads only) |
| Escort=1 / 2 | the picked records get `used[rec] = 1` (:334) for the round: never judged by BoardAll, held or released (:450). `kle_release` / the mode-2 branch send a released escort under stage 3 by the order alone, as before. BoardAll runs before the escort loop in the pass; no record is handled by both |
| EscortDry=1 | :457 false -> `all_raised = 2`, the line ends '... heist stage WOULD be set to 3 (dry run)'; with the order on `kle_order` returns 2 before the call (:295). No write, no call. The escort is dry too (one key for both) |
| BoardAllStage=0 | no write; `all_raised = 2`; the line ends 'BoardAllStage=0, the stage is left'. The measuring mode. With BoardAllOrder=1 it is 'the order alone' - and then the order goes at EVERY later visit to a record once judged held, held or not (note N-B) |
| BoardAllStage=1 | the write, once per record and round (:463) |
| BoardAllOrder=0 | :469 `continue`: no call of the game from BoardAll at all; `kle_boarding` is still read (unused) |
| BoardAllOrder=1 | in the pass of the raise and then once per visit: `kle_bot` (retried every pass, one 'no order yet' line per record and round), `all_visit` set, `kle_order` (place, 0, 1, 0). No boarding place: one line per visit, the stage is still written |
| BoardAllStill=15 | `all_still` 15000 ms (:550; `klb_pos` clamps 0..600) |
| BoardAllStill=0 | :456 skipped: every AI record in play at stage 1 or 2 whose place was read is raised in the first pass of a wait (the line says 'held for 0 s'). A NEGATIVE, empty or non-numeric value also gives 0 = everybody (note N-F) |

Events:

- **A new round** (:491-493, rules object new, state becomes 0x19, or the stage sum fell): `memset(&kle_r)` - visit,
  was_waiting, every mark, every anchor. The first tracked pass sets each anchor with `since = now`; nobody can be
  held for BoardAllStill seconds. The game's own reset has put every stage to 0 by then (0x817d20). Holds.
- **The hook's first look falls into a wait** (the gate opens late): :504 visit becomes 1; anchors are new, stood 0;
  nobody is raised before 15 s have been WATCHED - with an 8 s wait, nobody at that visit. With BoardAllStill=0
  everybody at once. Holds.
- **A record freed**: `r->used` 0 -> `all_seen[i] = 0` (:427). **Re-used**: the anchor is taken new only if the place or
  the money differs; `all_raised / all_told / all_visit / used` are kept by INDEX, not by actor (note N-D). No AI
  record is known to be re-used inside an Arcade round, and a freed record with a stage drops the stage sum, which
  clears everything.
- **GetTickCount wrap**: every use is an unsigned difference (`now - last`, `now - all_since[i]`, `now - round_at`);
  `all_seen` is the validity flag, so a stamp of 0 means nothing. Holds.
- **A bot whose place cannot be read** (actor null, not ZFFActor's vtable, node chain unreadable or not finite):
  `all_seen = 0` -> :454 'not judged', also with BoardAllStill=0; its clock starts again when the place is back.
  Conservative - and silent (note N-C).
- **A failed read of the money** (klbot.c:283 does not test `klh_rd`): money reads 0, differs, the clock restarts.
  Conservative.
- **The record changed since the snapshot**: :458 skips, silently, and tries again next pass.
- **The write refused**: one line (:460), tried again every pass of every wait (each refusal by the guard also logs
  'patch REFUSED', 64 at most in a process).
- **Log volume**: tracking says nothing; one 'held for' line per record and round; one 'not written' and one 'no
  order yet' per record and round; one 'cannot be read' per visit. Nothing can repeat every 500 ms.

## 4. What `klb_rec.money` is, and the HELD test against the live logs

**What it is (read)**: klbot.c:283 `klh_rd(s->score + 0x150 + 4 * i, &r->money, 4)`, score = `[rules+0x5f8]`: the
score object's money of crew member i - the number the `bots:` line prints as `$`, the one the bribe halves
(klbot.c:577-580, the game's own 0x757541).

**Does it move while a bot loots and stand while it is held? Yes (measured).** Earnings come as steps about every
1.1 s (the log's own rate; median gap 1.1 s for 13 of the 18 bots that earned in L8 / L10 / L11), $5,000..$100,000
each. Held bots: L11 record 1 $0 for 224 s and record 3 $150,000 for 183 s at (-1278, 500, 1884); L10 six records
unchanged for 106..141 s at (-1770..-1772, 500, 2792..2793), the clerk; L8 (no places in that log) no earning by
anybody for the last 190..262 s of the round.

**But 'no move of 1 m and no earning for 15 s' is not 'held by loot' (measured, `held.py`).** Spells of 15 s or
more at stage 1 or 2:

| log | spells | the trap (to the end of the log) | ended by themselves | of those, by an earning | longest that ended by itself |
|---|---|---|---|---|---|
| L10 | 16 | 6 | 10 | 2 | 60 s |
| L11 | 8 | 2 | 6 | 1 | 60 s |

A bot that goes on to earn DOES stand 15 s and more without moving or earning: L10 record 5, 33 s at
(1076, 500, 2815) with $0, then +$50,000 (03:01:41 .. 03:02:14); L10 record 1, 25 s at (-1151, 500, 2264), then
+$20,000 and $150,000 more in the next 19 s; L11 record 7, 16 s at (1269, 500, 1920) before its first $50,000. The
same places come back in both runs, each time ended by the bot walking on: (1879..1883, 510, 2550..2553) 60 s in
both, (1637, 510, 3055) 35..60 s, (1446..1455, 500, 2668..2671) 45 s in both, (1874..1879, 510, 2253..2257) 15 s
in both. Gaps between two earnings reach 93 s (L11 record 5, with 27 m walked in between).

| BoardAllStill | L10: spells not the trap | L11: spells not the trap | L11: record 1 / record 3 held at the START of visit |
|---|---|---|---|
| 10 | 13 | 12 | 1 / 1 |
| 15 | 10 | 6 | 1 / 1 |
| 30 | 7 | 4 | 2 / 1 |
| 45 | 4 | 3 | 2 / 4 |
| 60 | 2 | 2 | 3 / 4 |
| 75 | 0 | 0 | 3 / 5 |

So 15 s frees the trapped bots at the first visit and also raises whoever stands at a route wait or in a long
grab when the vehicle waits; 75 s would raise only the trap in these two runs, but two or more visits later, of
five. A wrong raise costs little (the bot stops what it does and goes to the vehicle that waits; side effects N1 -
N3 of the first review), so 15 is a fair default for L12 - **but a 'held for 35 s with $650000' line at a route
place is the test working as coded, not a fault.**

**Would the held bots have met the test, and when (measured)?**

- **L8 and L10: the test is met, and BoardAll would have done NOTHING.** The vehicle's state is 0 in every `bots:`
  line of both rounds (L8: 67 lines in state 0x19; L10: no 'van 1..7' line at all). In L10 the six at the clerk
  arrive 03:03:21.9 .. 03:03:57.1 and are 'held' from 03:03:37 .. 03:04:12 on; the seventh died at 03:01:20 at stage
  0. Nobody reaches the exit trigger, nobody calls the vehicle, it never waits, `kle_board_all` is never called -
  and without a waiting vehicle stage 3 does not stop the loot tactic anyway (0x4519dc..0x4519ef). Defect S-D.
- **L11: both, at visit 1.** Visits start 03:14:43.9, 03:15:14.2, 03:15:43.2, 03:16:12.9, 03:16:42.6 (GO was
  03:12:36.3), each wait 8 s. Record 1 stands at (-1278, 500, 1884) from the sample of 03:14:21.98 (it was at
  (-532, 500, 1934) 5 s before): held from about 03:14:37, raised in the first pass of visit 1 with about 22 s.
  Record 3 stands at (1446, 500, 2671) from 03:14:06.9 - its EARLIER stop: held from about 03:14:22, raised at visit
  1 with about 37 s and $150,000. In the unchanged run it walked off between 03:14:47 and 03:14:52, by itself, and
  was at (-1278, 500, 1884) by 03:15:02. **So L12 should not expect two raises at (-1278, 500, 1884): if the timing
  repeats, one is there and the other at about (1446, 500, 2671)** - a place where the bot stood 45 s and then left in L10 as well. Records 2 and 5 left their
  60 s places 2 to 7 s before visit 1 began; a few seconds' difference in L12 and they are raised too. No other spell
  overlaps a wait.

Limits of the 1 m circle: the three logs show the trapped bots dead still (the same whole coordinates for
100..224 s). A bot the tactic sends back and forth between two closed cases more than 1 m apart would never be
'held'. Not seen; not excluded on the other maps (only L10 and L11 have place lines).

## 5. New defects

### S-A (should) - the stillness clock is wall time; the round is not
`kle_all_track` :429 and `kle_board_all` :455 count `GetTickCount`. Tracking runs only on the game's thread (:500
returns first). With the window not in front the main loop only pumps messages (CLAUDE.md, re/freeze_1009.md): the
round stands still in state 0x19, the fallback thread ticks with `game_thread` 0, no pass reaches `kle_all_track` -
and `all_since` keeps its old value. At the first pass after the return every bot that has not yet gone 1 m has
'stood' the whole absence; if the vehicle waits then (its state is frozen with the round), each one at stage 1 or 2
is raised and the line states a time it did not stand ('held for 73 s'). The same if the pause menu keeps the main
loop running with the round frozen (not read: whether it does, and whether the state stays 0x19). The game folder's
log shows the mechanism inside state 0x19, in short form ('tick: driven by the fallback thread' at 18:45:15,
14:54:04, 18:57:18, back after 0.1 .. 2.7 s); no absence of 15 s inside a round was looked for further. For the
owner: an Alt+Tab of 15 s across a wait raises every standing bot. For L12: a wrong 'held for'.
Fix, in `kle_tick` in place of :506 (a pass missing for 1.5 s = the round may have stood still: every clock starts
again):

    if (kle.all) {
        static DWORD tracked;
        if (tracked && now - tracked > 1500) memset(kle_r.all_seen, 0, sizeof kle_r.all_seen);
        tracked = KLB_T(now);
        kle_all_track(&s, now); if (waiting) kle_board_all(&s, now);
    }

Better, and it covers a pause that keeps the loop running: count on the game's own clock `[[0xdd2640]+0x48]` (1024
a second; the clock ZLootTactic's and the board tactic's own tests count by, 0x45193a / 0x4faf7a; 're/crash_gamedata.md'
calls it game time). ASSUMPTION until seen: that it stops in a pause.

### S-B (should) - the new refusal in `kle_bot` drops a held escort for good
:261-264 is right for the call. But the escort loop treats EVERY refusal of `kle_bot` as 'this escort is gone'
(:515-519: line 'escort: record N dropped: ...', slot wiped, mode 3). The first review meant 'BoardAll tries again
every pass, the escort at its next order'; the code does the second differently. How often a soldier's defend goal
is 'running' with an empty stack between two frames is not known (expected: never). If it happens once, the owner's
escort leaves him for the rest of the round - with Escort=1 live in the owner's ini today. Fix: a refusal that
means 'not now' must not drop.

    static int kle_later;                                /* kle_bot refused for a reason that passes */
    ... in kle_bot, first line:            kle_later = 0;
    ... at the empty-stack return:         kle_later = 1; strcpy(why, "..."); return 0;
    ... in kle_tick's escort loop:
        k = kle_bot(&s, e->rec, &actor, &soldier, bp, w);
        if (!k && kle_later) continue;                   /* asked again next pass; no order meanwhile */
        if (!k || actor != e->actor || soldier != e->soldier) { ...drop as now... }

L12 runs with Escort=1 and measures this: no 'escort: record N dropped: its defend goal runs ...' line in the round.

### S-C (should) - BoardAll with Van / VanLeftBehind is forbidden by a comment only
S5 of the first review, half done. klbot.c:608 takes any AI record in play at stage 3 as 'stands at the vehicle';
with VanLeftBehind=1 and the vehicle driving out (:603, :609) a bot BoardAll raised 100 m away qualifies, and
after VanDelay the game's damage rule is called (Van=2: everybody aboard dead) - at nearly every visit. Neither key
is in the owner's ini or in L12's. Fix, in `kle_init` after :551 (klb_init has run: klhook.c:782-783):

    if (kle.all && klb.van && klb.van_left) {
        klog("board: BoardAll is OFF: [Bots] VanLeftBehind=1 takes every bot at stage 3 as standing at the vehicle, and BoardAll gives stage 3 to bots far from it");
        kle.all = 0;
    }

and one sentence in klbot.c's Van text and KLHook.ini:226-228.

### S-D (should) - the key's text gives L8 / L10 as its reason; BoardAll does not act there
:139-143 'WHY (live runs L8 / L10 / L11 ...) ... six of seven stood on the clerk for minutes'. Section 4: in both
runs the vehicle's state was 0 from GO to the end. BoardAll needs a wait; a wait needs somebody in the exit
trigger (a free bot, or the human); and the loot tactic lets a stage-3 bot go only while the vehicle waits. With
the whole crew held and the human elsewhere nothing happens. What got five bots out in L11 was the one-stop build,
not the hook. Fix: say so in LIMITS ('acts only once somebody has called the vehicle; the L8 / L10 case - everybody
held, no vehicle - is not touched') and do not report BoardAll to the owner as the cure for Late Night Opening.
The lever for that case is the map (take the clerk and the closed cases out of the money list) or, as the first
review said, the loot test's own gate `[tuning+0xc34]`.

### Notes

- **N-A 'held' is 'stands and earns nothing'** - section 4. A route wait, a long grab, a bot in cover at stage 2 all
  qualify when the vehicle waits. Wanted or not, the key's text ('HELD ... by loot') promises more than the test knows.
- **N-B `all_raised` 2 is written and never read.** With BoardAllStage=0 or a dry run, and BoardAllOrder=1, a
  record once judged held is ordered at every later visit, also after it walked off or reached stage 3 by itself
  (:451 is skipped, :469 has no stage or stillness test). Fix: `if (kle_r.all_raised[i] == 2) { judge again each visit }`
  or order only while `r->stage < 3`.
- **N-C three silent paths** in `kle_board_all`: place not read (:454), record changed (:458), and - by design - not
  yet still (:456). 'A bot stands at g1 while the vehicle waits and no board: line comes' cannot be told apart in
  the log. One line per record and round for :454 and :458 would do.
- **N-D marks by index**: `all_raised / all_told / all_visit / used` and the anchor are not tied to the actor
  (klhop.c:282 does tie its marks). A re-used record would inherit them; with BoardAllOrder=1 it would be ordered
  at stage 0 (the stage test sits inside `!all_raised`).
- **N-E an ex-escort held by loot is nobody's**: `used[]` keeps BoardAll off it for the round (the first reviews
  asked for that), and the escort part gives it one order, which a held bot does not follow.
- **N-F BoardAllStill**: -1, an empty value or text read as 0 = 'every bot'; the widest setting is the one a typo
  gives. And the line then says 'held for 0 s'.
- **N-G texts**: :9 'NOTHING HERE HAS RUN IN THE GAME. Off unless ... Escort=1 or 2' and :117 'TESTED OFF-GAME ONLY'
  (the escort ran in E1, E3, L11; BoardAll works without Escort); :402 and :526 (S4); :500 'escort:' for both
  parts; :196 'bit 1 / 2 / 4' (4 is not used); the `board: on` line says 'gets heist stage 3' with Stage=0 too;
  `kle_order`'s soft line (:299-300) says 'escort: ... (said once per escort)' for a BoardAll order and comes at
  every such order.
- **N-H the printed place is the anchor**, up to 1 m from where the bot stands; 'held for T s' starts at the last
  restart of the clock, up to 0.5 s after it stopped.
- **N-I the board tactic has the loot tactic's kind of gate** (read, 0x4faf6c..0x4faf9d): 0.0 until 2.0 s
  (float 0xb5c828; ticks x 1/1024, double 0xb5c498) have passed since `[[actor+0x54]+0x30]`. What sets that stamp
  is still **not read** (three scans for a store of the clock at +0x30 found only stack slots). If a raised bot does
  not leave in L12, this is the first thing to read in a dump.
- **N-J with every bot out the round may end sooner for the human** (the diner and park runs ended 152..189 s after
  GO once the crew had left). L12 will show what the session does after the last 'status6'.
- **N-K klbot.c Leave / Bribe** act on bots ABOARD: more bots aboard, more chances. Neither key is set today.

## 6. SHIP and TEST

klescort.c, klbot.c, klhop.c and klbalance.c hold no `#if`. `KLHOOK_TEST` appears in klhook.c (:255 policy session
/ ship, :576 klauto.c, :727, :750 SessionSafe, :760 the build line, :791 the fault filter) and klsteam.c (:157, :327,
:539, :559: a TEST build passes no Steam write at all). None is on BoardAll's path: the crew record is heap,
`klh_kind` answers 0 and `klh_may_write` returns 1 before any policy is looked at (klhook.c:308); `klh_data` wants
a committed writable page and changes no protection; `klb_level` asks for verdict 2 in both. Both DLLs the lead
built carry the new texts (string search: 'board: on; BoardAll=1 Still=%lu s Stage=%d Order=%d', 'held for %lu s
with $%lu', 'its defend goal runs but its goal stack is empty'): `<work>\build\klhook\ship_board3` sha1 47b609e8..,
`test_board3` sha1 079873ba.., written 04:37:26 / 04:37:29, after the last source change (04:37:04). The SHIP
folder's sample ini has [Bots] Enable=0 and the four BoardAll keys commented out. The game folder holds neither
build now (dinput8.dll 212f2641.., 03:32) and its KLHook.ini has Escort=1 and no BoardAll, Van, Backstab or Tune.

## 7. Run L12

Safe as a scripted TEST-hook run (test_board3), owner away, **the game window in front for the whole round** (S-A).
Keys in the FIRST `[Bots]` section of the ini (it has two; Windows reads the first): `Enable=1 Log=1 BoardAll=1
Escort=1`; the defaults give Still=15, Stage=1, Order=0. Keep `[CrewHop] Enable=1 Dry=1 Log=2` - it writes the place
lines. No Van, Backstab, Tune.

Worth one run first (six minutes): **L12a with `BoardAllStage=0`** - no write, the escort real. It shows whom the
test picks and when, against the unchanged run. Then L12b with the write.

**At the start**

    build: TEST (klauto), Oct 11 2026 04:3x ...
    board: on; BoardAll=1 Still=15 s Stage=1 Order=0: while the escape vehicle waits, an AI heister at heist stage 1 or 2 that has neither moved 1 m nor earned for that long gets heist stage 3 (one byte of its crew record: the game's loot tactic lets go, its board tactic starts); Arcade only, on a level that is not the stock one of its slot
    escort: on; Escort=1 ...

No ' DRY RUN', no ' and one order to the boarding place a visit'. Until the first 'van 3' there is NO `board:` line.

**Success, in this order** (L11's times: van 1 at GO + 120 s, van 3 at GO + 128 s)

1. Within 0.5 s of the vehicle's state 3 (the `bots: ... van 3` line may come up to a second later):
   `board: record A (stage 1) at (x, y, z): held for T s with $M: the vehicle waits (state 3): heist stage set to 3`
   - one with (x, y, z) within 100 of (-1278, 500, 1884), T about 22, $0; the other most likely within 100 of
   (1446, 500, 2671), T about 37, $150000 (section 4). T is 15 or more, and no more than the place lines show the
   bot standing.
2. klbot.c: `bots: record A (bot): heist stage 1 -> 3` - a jump past 2 is the hook's signature.
3. The escort: `escort: record E released (the vehicle waits, state 3): sent to the boarding place (-352, 122, -8268), the game set (-352, 0, -8268); it is at stage 0`
   and NO `board:` line for record E, ever.
4. NO `board: record N at (...): sent to the boarding place` (the order is off), no `board: visit N: ... cannot be read`.
5. Places: the next `hop: bot A stage 3: node (...)` lines move away while the line still says van 3 - 300 or more
   between two samples (3.3 m/s; the wait gives about 26 m).
6. Later visits: no second `board:` line for A or B (once a round). They gain ground each wait; then
   `bots: record A (bot): aboard`, `status6`; the last crew line has no `bot in-play`.
7. Regression: the bots that left by themselves in L11 still do; no `escort: record E dropped: its defend goal runs ...`.

In L12a the same lines end 'BoardAllStage=0, the stage is left', there is no 'heist stage 1 -> 3', and the two
bots stay where L11 left them.

**Not a fault**: more `board:` lines than two, at the route's waiting places, 'held for 35..60 s' with money (N-A).
A and B standing again after 'van 5' (the loot tactic is back, the bot now at stage 3) and moving on at the next
'van 3' with no `board:` line (the game's own test). The vehicle staying at 0 after the last free bot boarded, with A
or B still on their way: 119 m is more than five waits of 26 m unless they keep walking between the waits.

**The feature failed (no danger)**

- `hop: bot A stage 3: node` unchanged through a whole wait after its 'set to 3' line: the loot tactic did not let
  go, or the board tactic's test is 0.0 (no path, or its 2 s gate, N-I).
- a bot at g1 / g2 on one place for 20 s and more in the place lines, 'van 3', and no `board:` line for it: the
  gate (`escort: <why>: nothing is done here` - it says 'escort' because Escort is on), the thread (`escort: the tick
  is not on the game's thread`), or a silent path (N-C).
- `board: record N (stage S): the stage byte was not written: it is left alone`, or `patch REFUSED ... crew record`.
- T larger than the place lines allow, or `tick: driven by the fallback thread` / `stall watch:` inside the round:
  the window was not in front; the run measures nothing (S-A).
- `bots: record N: traitor flag SET` for a raised record (not possible on Arcade level 1 without Tune).

**A fault**: `CRASH` / `FATAL` / `ASSERT at kl2.exe+`. With the order off BoardAll calls nothing, so dinput8 frames
over 0x760e50..0x760f69, 0x412910, 0x7bbf70 or 0x5ca0bf can only be the ESCORT's order. A fault after a 'set to 3'
line with EIP in 0x4faf60 / 0x82f970 (board test / action), 0x451920 / 0x7bc7d0 (loot), 0x727cb0 (the grab's
clean-up), 0x6840a0 (boarding) or 0x8fb031..0x8fb05f (the rules' pass at 'van 5') is the game acting on the byte:
read rules = `[[0x168e9e4]+0x54]`, record i = `[rules+0x348] + i * 0x7c` (+0x78, +0x10, +0x15, +0x1c, +0x79),
`[[rules+0x5f8] + 0x1d4 + 4 * i] & 0x2000`, `[rules+0x1dc]`; soldier = `[actor+0x77c]`: goal stack +4..+8, defend goal
+0x648 (+8), block +0x64c, +0x4fc; and `[[actor+0x54]+0x30]` against `[[0xdd2640]+0x48]`. 0x686a66 is NOT expected on
this map (re/crash_686a66.md: a FakeTarget outside the vision grid, Retomoto builds only).

## 8. Not read

What sets `[[actor+0x54]+0x30]`; whether the pause menu stops the main loop's SteamAPI_RunCallbacks calls or the
clock `[sysif+0x48]`; whether 'defend goal running, goal stack empty' ever holds between two frames; what the
board tactic does for a bot with a path of one node; what ends an Arcade round once every bot has escaped; any map
but Late Night Opening (no other saved log has place lines).
