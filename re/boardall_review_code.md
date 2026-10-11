# BoardAll ([Bots] BoardAll=1, klhook/klescort.c) - adversarial review, lens: the hook's code

2026-10-11. Reviewed: `klescort.c` at HEAD (commits 6186767 + ad3070d; the working tree has no change under
`klhook/`), `klbot.c`, `klhook.c` (guard, tick), `klhop.c`, `kltalk.c`, `klfed.c`, `klcrew.c`, `klcrew_rt.c`,
`klsteam.c` (the level verdict). Exe facts were read again in kl2.exe build 0490 with `debug/dasm.py` and three
scratch scans (every byte access at displacement 0x78; every function that walks the crew records; callers of the
record accessors). Live evidence: the saved logs `<work>\build\klhook\live\E1_DM03 / E3_DM01 / L11_DM02 / L12_DM02`
and the game folder's `KLHook.log` (read only). Nothing was built, started or changed.

## Verdict

**SAFE_TO_RUN_LIVE** - for run L12 as a scripted TEST-hook measurement with the owner away. No path writes or calls
with BoardAll=0, in a dry run, off the game's thread, outside an Arcade round or on a stock level; the write is one
heap byte with a value the game itself writes; no index can leave the tables.

**Not ready for the owner's own KLHook.ini** on the strength of L12 alone. Five things should change first (D1 - D5),
and one claim the design rests on is wrong in the source (D3): the rules do NOT send stage-3 bots to the boarding
place when the vehicle starts to wait.

## The six questions

### 1. Readers and writers of crew record +0x78 (as far as the code review needs it)

Found by scanning all of .text for byte accesses at +0x78 and classifying each by the object it belongs to (a base
register that also carries displacements >= 0x7c is no crew record; the rest were read).

| site | routine | what it does with the stage |
|---|---|---|
| 0x5490d1 | record constructor 0x549030 | writes 0 |
| 0x817e98 | round reset 0x817d20 | writes 0 (also `and [rec+0x79], 0xfd`) |
| 0x5dd906 / 0x5dd90f | 0x5dd890 (activator, n) | `stage = max(stage, n)` - the WHOLE routine: a class test, 0x78f470, the in-use byte, the byte. No other effect |
| 0x4519d1 | ZLootTactic test 0x451920 | `< 1` -> 0.0; `== 3` and vehicle state 3 or 4 -> 0.0 |
| 0x4fb064 | ZBoardEscapeVehicleTactic test 0x4faf60 | `< 3` -> 0.0; else needs the boarding place (0x5aeb00) and a path of more than one node |
| 0x591c00 / 0x591c17 | damage factor 0x591b60 | an NPC hits an Ally NPC: times R+0x1c when the victim's stage != the LOCAL PLAYER's |
| 0x79b883 | ZBecomeTraitorTactic test 0x79b7c0 | stage term `[R+0x24 + 4*stage]` (stage 3 -> R+0x30) |
| 0x8fb02b | rules slot 194 (0x8fa6d0), crew loop | `>= 3` and AI and soldier: `vtable[0x1b4]()`, then order (place, soft 1, reset 1, 0) |

No other reader exists in the image as far as these scans go. Consequences for an AI record that gets 3 without the
exit box:
- **Vehicle call / 'everybody is out'**: the exit trigger 0x6c3d50 calls the vehicle (rules vtable +0xb0) when its
  state is 0, for a player or an actor, without reading the stage. Nothing counts 'heisters at stage 3'. 'Criminals
  left' is 0x4906b0 = records with status 0 (0x4906e2); it decides 'leave at once' (0x6841b1), 'next vehicle' (state 7)
  or 'none left' (state 8, 0x55edd3). The player-only byte the exit trigger also raises is record +0x12 (0x6c3e07),
  not written for actors.
- **Round end, escape, score**: not computed from the stage. The boarding rule 0x6840a0 tests the session state, the
  vehicle state and status == 0 only (0x68422b), then status = 4. (Who writes status 6: not read.)
- **Damage**: 0x591c1b. A raised bot whose stage now EQUALS the player's loses the R+0x1c reduction (0.5 on Arcade
  levels 1-3 down to 0.1 on 10-11, re/balance.md): police hurt it 2x .. 10x more than before the write. One that now
  differs from the player's gains it. klbalance.c does not write +0x1c.
- **Traitor**: the stage term rises from 0 (stage 0 / 1) or 2 to 3. On levels where R+0x6c > 0 (stock 4+, or
  [Bots] Tune=1) a rich raised bot can turn earlier than it would have at the exit box.
- **The hook's own readers**: klbot.c - the 'sum of the stages went down' test cannot trip (a raise only adds; in the
  game folder's log 88 falls, all in session states 0x16 / 0x23 / 0x24 / 0x25, 739 rises, all in 0x19);
  `BackstabStage` is met earlier; **Van / VanLeftBehind read stage 3 as 'at the vehicle'** (klbot.c:608) - a raised
  bot 100 m away qualifies. klhop.c - the `Stage=` gate of a hop is met earlier. kltalk.c - a member going from
  under 2 to 3 fires the Stage2 chatter event (kltalk.c:643), a line about being out said by a bot that is inside.
  klfed.c, klcrew.c, klcrew_rt.c do not read +0x78.
- **Replication**: no serializer reads the byte; the only block copies in functions that address the record array
  write a fresh record INTO it (0x42bcd3, 0x588a29). Network code was not read beyond that.

### 2. The loot tactic's exit

Exactly `stage == 3` (0x4519dc `cmp al, 3 / jne`) of the BOT's own record (0x78f470 on the tactic's actor) AND rules
vtable +0x12c (0x5d52f0 = byte rules+0x1dc) == 3 or 4. It returns 0.0 on every evaluation while both hold - and
**only then**: the moment the vehicle leaves (5, 7, 8, 0, 1, 2) a stage-3 bot is a looter again.
This test comes BEFORE the 'busy looting' test (0x451a59 `test eax, 0x2000`), so a bot in a grab is dropped too.
The grab is not left behind: it lives in the rules' per-record update 0x727cb0 (state byte +0x15), which needs a
re-trigger every tick - the object's box calls 0x8e8750, which turns state 2 back into 1 for the same object. Case 2
(0x7281ba) = no re-trigger since the last pass: 0x522090(record), +0x15 = 0, vtable +0x198 (index, 0), flag 0x2000
cleared (0x7281f0). Case 1 aborts the same way (0x728187; the flag through 0x467f20 at 0x7281a7) when the object is
taken, `[object+0x64] != 1`, or - for an AI record - `[actor+0x576] != 1` (0x727fa9). So a bot called away in a grab
is cleaned up by the rules one pass after it leaves the object's box, and the boarding rule tests none of +0x15 /
+0x1c / 0x2000 anyway.
Reach of the tactic (0x8b94d0, tuning defaults from the constructor 0x52ad20; the live values were not read):
list 1 = 800 in the plan and 400 in height, list 2 = 400 and 200.
Not read: what the tactic framework does with the tactic's own state when its test turns false mid-run.

### 3. The order for a bot the loot tactic holds

0x760e50 does not look at tactics. Defend goal idle (`[goal+8]` 0 or 4): vtable +0x1b4, the goal is queued at 150,
vtable +0x50 (1). Running and not soft: 0x7bbf70 (new plan). Either way the defend block holds the new place; it is
neither dropped nor queued behind anything. But L10 / L11 showed that Defend orders from the route chain - the same
routine with the same (place, 0, 1, 0) - do not move a bot the tactic holds, so the hook's order alone will not
either: it takes effect when the tactic lets go.
vtable +0x1b4 = 0x6e49b0: it removes the soldier's eleven behaviour goals (+0x638 .. +0x664) at priority 150
(0x8883d0 each). It needs nothing but the soldier object, and the order routine calls it by itself at 0x760f39: as
safe as the order call. **It should not be added**: it does not touch tactics, so it frees nobody from loot; and the
rules' form pairs it with a SOFT order, which ends the waiting step of the bot's route chain (0x686c77), the very
thing klescort.c's order avoids.

### 4. The code - see the defects below. What was checked and holds

- BoardAll=0: `kle_board_all` is not reached (klescort.c:451); `klb_put8` has no other caller in the file.
- Dry run: `kle.all_stage && !kle.dry && !klb_put8(...)` short-circuits before the write (:407); `kle_order` returns 2
  before the call (:266). BoardAllStage=0: no write.
- Thread: `kle_board_all` is only reached after `if (!game_thread) return` (:445); `game_thread` = a return address
  inside the main loop 0x87a930 .. 0x87ab40 on the main thread (klhook.c:629); the tick is serialised by
  `klh_tick_busy`. The record address comes from the snapshot taken microseconds earlier in the same tick.
- Index: `klb_read` refuses n > 32; all three BoardAll arrays have 32 entries.
- Visits: the first visit is 1 and the arrays start at 0, so a hook that first looks mid-wait acts once. A new round
  clears everything; every one of the 67 round starts in the log has vehicle state 0.
- Log: no line can repeat every 500 ms (see D6 for the one that returns every 128 s).
- Guard: a heap address makes `klh_kind` return 0 and `klh_may_write` return 1 before any policy is looked at
  (klhook.c:307); `klh_data` then needs a committed, writable page and never changes a protection. SHIP and TEST
  alike; klescort.c and klbot.c contain no `#ifdef`.
- `kle_bot` does not refuse a looting bot as such: the rules themselves need `[actor+0x576] == 1` for an AI's grab
  to go on (0x727fa9), and no order was refused for that byte in E1, E3 or L11.

### 5. A safer form

Calling 0x5dd890 (actor, 3) gains nothing: the routine is the byte write and nothing else, plus a virtual call on the
actor. Marking money objects 'taken' is a wider write into level objects that the player's loot and the score read.
Slot 194 cannot be called without changing the vehicle's state - and it runs by itself for every stage-3 bot at the
next state change.

**Recommended: the stage byte ALONE, for the bots the trap holds.** Write 3 once per round into an AI record that is
in play, not a traitor, never an escort this round, **at stage 1 or 2**, and that has not moved 1 m in the last 10 s
when the vehicle waits (the trap's signature: bot 3 stood 41 s on (1446, 500, 2671) in L11). No order from the hook
for these. Reasons:
- the byte is all the game needs: the loot test lets go (0x4519dc), ZBoardEscapeVehicleTactic becomes eligible
  (0x4fb064) and runs the bot to the boarding object itself, where it is taken aboard within 300 (0x82fa35, float
  90000.0 at 0xd19a28); the bot's standing route order applies again; the rules order it at the next state change;
- stage 0 never loots (0x4519d4), so a write there only switches the tactic ON for when the vehicle is away;
- in L11 five of seven escaped unaided - they were walking, not held; today's form raises them too and brings each
  the rules' soft order 8 s later, in the middle of its chain;
- the order's place is on the van's approach on the key-framed-van maps and outside their AllyEscapeBox (D5);
- no game call is added.
Keep today's order behind a key (`BoardAllOrder`, default 0) so that a run can compare the two.

### 6. The live check L12

Before: the game window in front (the 03:22 attempt never left the menu: Discord), the owner away, TEST hook
test_board2; `[Bots] Log=2` (health losses with places); the keys in the FIRST `[Bots]` section of the ini (it has
two; Windows reads the first - the 03:22 log's 'board: on' line shows it did).

Proof of success, in this order:
1. `board: on; BoardAll=1 BoardAllStage=1: ...` at start, and no `escort: ...: no escort here` line in the round.
2. Within 0.5 s of the first `bots: ... van 3` line, for every AI record in play under stage 3 except the held
   escort: `board: record N (stage S): the vehicle waits (state 3): heist stage set to 3`, then
   `board: record N at (x, y, z): sent to the boarding place (...), the game set (...); visit 1 of the vehicle`, and
   from klbot.c `bots: record N (bot): heist stage S -> 3`. Going by L11 that is records 1 - 5, NOT only the two at
   the cases; the escort follows 0.5 s later, after its own `escort: record N released ... sent` line.
3. Positions (`hop: bot N stage 3: node ...` every 5 s): records 1 and 3 leave (-1278, 500, 1884) - more than 300
   between two lines - while the line still says van 3.
4. `bots: record N (bot): aboard`, later `status6`, for both; the last crew line has no `bot in-play`.
5. Regression: the five that escaped in L11 (2, 4, 5, 6, 7) escape again.

Partial, not a fault: they leave during van 3 and stand again once the line says van 5 / 7 / 1 (within 800 of a
closed case) = the tactic took them back; then `board: record N at ...: sent ...; visit 2` (no second 'set to 3').
The wait is 8.0 s a visit and the boarding place is 102 m from the cases, so one visit cannot be enough; L11 had
five visits and then van 0 for good.

Faults:
- `CRASH` / `FATAL` / `ASSERT at kl2.exe+` after a `board:` line.
- `board: record N (stage S): the stage byte was not written`, or a `patch REFUSED ... crew record` line.
- `board: record N: no order to the boarding place yet: <why>` with no `sent` line later in that visit.
- `board: record N: NOT sent to the boarding place: ...`.
- van state 3 lines with bots at g1 / g2 in play and NO `board:` line: the gate (`no escort here`), the thread
  (`escort: the tick is not on the game's thread` together with `tick: driven by the fallback thread` = the window was
  not in front), or the silent return of D2.
- `bots: record N (bot): dead` for a raised record; with Log=2 `lost ... ONE STEP ... DOWN at x y z` near the line
  from (-352, 0, -8268) to the van's stop (-793, 2, -9010) while the van drives in = run over (D5).
- `stall watch:` / `STALL:` after a `board:` line.

In a dump: is the fault under the hook's call? EIP in 0x760e50 .. 0x760f69, 0x412910, 0x7bbf70, 0x6e49b0, 0x8883d0
or 0x6cabf0, with dinput8.dll frames and then 0x87aa82 or 0x87a9ec as the nearest kl2.exe return address = the
order call. Then esi / ecx = the soldier: `[s]` 0xbd0954, `[s+0x40]` the actor (0xbb3bac), `[s+0x648]` the goal and
`[goal+8]`, `[s+0x64c]` the block (+0x14 == s), `[s+0xec]`, `[s+0x4fc]`.
Not under the hook: EIP in 0x451920 / 0x7bc7d0 (loot tactic), 0x4faf60 / 0x82f970 (board tactic), 0x727cb0 (grab),
0x6840a0 (boarding), 0x8fb031 .. 0x8fb05f (the rules' crew loop: eax the record, edi the soldier). Read the record
of the actor involved: rules = `[[0x168e9e4]+0x54]`, records `[rules+0x348] + i * 0x7c`: +0x78 (3 written by us?),
+0x15 (grab state 0 - 3), +0x1c (the object), +0x10, and the flags `[[rules+0x5f8] + 0x1d4 + 4*i] & 0x2000`.
**0x686a66 is the known ZDefendBehaviourGoal crash** (CLAUDE.md 'CRASH 0x686a66'), not this write: but note whether
a van 3 -> 5 change came within a second before it - the rules' soft order to the bots we raised ends their waiting
Defend steps at that moment, and the tab's Late Night Opening build has the fork wiring without the FORK_GAP fix.

## Defects

### D1 (should) - a record at stage 0 is raised: that switches the loot tactic ON for it
klescort.c:406. The loot test returns 0 for stage 0 at any time (0x4519d4 `cmp al, 1 / jb`), so such a bot is never
held and the write frees nobody. With 3 it loots whenever the vehicle is not in state 3 / 4 - 8 s later on Late Night
Opening. The record this hits first is the released escort: L11 `escort: record 6 released ... it is at stage 0`.
Fix: `int raise = kle.all_stage && r->stage >= 1 && !kle_r.used[i];` and write only then; give `all_raised` a second
value for 'looked at, not written' so that `r->stage >= 3 && all_raised[i] != 1` still means 'there by itself'
(today BoardAllStage=0 and the dry run set the flag without a write, and such a bot is ordered at every later visit).

### D2 (should) - no boarding place: a silent return, and no stage write either
klescort.c:399 returns before the loop. The comment above the function says the stage byte must not wait for the
order's tests; it waits for this one, and the log says nothing. All five maps on the tab have a boarding object, so
this is not expected in L12.
Fix: keep `have_bd`, log once per visit, do the stage block regardless, `continue` before the order when it is 0.

### D3 (should) - the source states as read from the exe what the exe contradicts
klescort.c:36-40, :85-86, :134, :395, and klhop.c:58-59: 'when the vehicle starts to WAIT (state 3 / 4)' slot 194
orders the stage-3 AI records. The table at 0x8fb0a0 is `00 00 01 01 00 00` for states 1 .. 6 and entry 1 is the exit
0x8fb06b: the crew loop 0x8fafa0 runs for states **1, 2, 5 and 6** - called, leaving, destroyed - and not for 3 / 4
(re/bots_squad.md section 5 has it right). What boards a stage-3 bot while the vehicle waits is its own
ZBoardEscapeVehicleTactic. Consequences the design did not count on:
- every bot BoardAll raises gets, when the vehicle LEAVES 8 s later, `vtable[0x1b4]()` and a SOFT order from the
  rules (0x8fb052 `push 1`). `[soldier+0x4fc] = 1` ends the waiting Defend step of its chain (0x686c77) and the next
  step fires. For a released escort that is what klescort.c:89-91 set out to avoid: its chain stood at an early 'in'
  step, and the next one sends it into the level.
- 'a bot that reached stage 3 by itself: the rules have sent it' (:403, :373) is true only for one that had stage 3
  when the vehicle was CALLED.
Also stale since the write exists: 'NO data write' (klescort.c:5), 'no write' in the escort's start line (:505),
'no data, no code' in klhook.c:31-32.

### D4 (should) - an escort is handled twice, and BoardAll overrules EscortBoard=0
- Released in the pass the vehicle starts to wait: `kle_release` orders it (:376); 500 ms later BoardAll finds mode 3,
  writes the stage and orders it again.
- Released earlier (mode 2): BoardAll runs first (:451), then the escort loop tests `s.r[e->rec].stage >= 3` on the
  snapshot taken BEFORE the write (:471) and orders it a second time in the same tick.
- EscortBoard=0 ('it is left where it is', :374) is undone half a second later.
Two orders to one place are harmless in themselves; the stage write for an ex-escort is D1 and D3.
Fix: BoardAll skips every record in `kle_r.used[]`; or `kle_release` and the mode-2 branch set
`kle_r.all_visit[e->rec] = kle_r.visit` after their call and the mode-2 branch tests it first.

### D5 (should) - the order's place lies on the van's approach and outside the map's own boarding box
The place is the rules' own, boarding object + 500 along its x axis. On the key-framed-van maps the object rides on
the van, 337 behind its origin on its axis (tools/kl_fa_bots.py:1125-1128). z_m02s1 M02, the build on the tab
(bots.json, van.json): stop (-793, -9010), box
(-621, -8720), the place L11 logged (-352, -8268) - one line, the place about 860 behind the stop, on the side the
van comes from (heading at the stop -150.2 degrees). That is the lane the map builder moved the bots out of
(re/play_fixes_review.md D3): they end in an AllyEscapeBox 422 to the side, at (-821, 200, -8400), which boards any
AI inside it with no stage and no path test (0x907a50). The hook's place is 487 from that box's middle - outside it.
So the order pulls a bot that was on its way to the box that would have taken it, to a point where only the tactic
can board it, and where it stands on the van's line if it arrives after the van left. Whether the van hurts an actor
there is NOT established (re/bots.md:936); the rules send their own stage-3 bots to the same point.
Fix: no order for raised bots (section 5), or a place from the level's KLJoin.ini written by kl_fa_bots (the park).

### D6 (note) - `all_told` is a char counted up on every failing pass, and two messages share it
:408 / :416. After 128 s it wraps and the line comes again; and once 'the stage byte was not written' was said, 'no
order to the boarding place yet' never is. Fix: two bits, set once.

### D7 (note) - a guessed new round forgets `all_raised`
:436-437. If the stage sum ever fell inside a round (a record released), a bot this file raised but could not yet
order would count as 'there by itself' and never be ordered. Not seen: every fall in the log is between rounds.

### D8 (note) - with Escort=0 the tick still talks about an escort
`escort: you: record ...` once a round (:452), `escort: ...: no escort here` on a stock level (:442), and with
[Bots] Enable=0 a BoardAll=1 is dropped without a line (:485). `t.told_soft = 1` (:420) also hides the one line that
would say an order was taken as soft.

### D9 (note) - other parts read 'stage 3' as 'at the vehicle'
klbot.c Van / VanLeftBehind (:608), BackstabStage (:560), klhop.c's Stage gate (:299), kltalk.c's Stage2 event
(:643), the damage factor R+0x1c and the traitor's stage term (question 1). None is on in the owner's ini today
except Talk; say so in the key's comment, or exclude raised records by `kle_r.all_raised`.

### D10 (note) - vehicle state 8 exists
`s19 van 8` 78 times in the log (5 -> 8 seven times; 0x55edd3 `push 8` = nobody left in play). klbot.c's comment
knows 0 .. 7. BoardAll acts on 3 / 4 only and is not affected.
