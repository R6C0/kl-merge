# Review of track G: Retomoto Tower, the AI heisters fight every room first

Adversarial review, 2026-10-11, of `re/retomoto_bots_rooms.md`, the working-tree changes of
`tools/kl_fa_bots_rt.py` (+656 lines) and `tools/kl_fa_bots_dyn.py` (+33), and the builds
`<work>\build\z_rooms\retomoto_full` / `retomoto_full_r`. OFFLINE: nothing started, no game or build folder
written (the folder listings of both builds are the same before and after my check runs), nothing committed.
Only this file was written. Scratch: session scratchpad `Grev\` (`rdis.py`, `xref.py`, `ctx.py`, `rev1..8.py`).

**Verdict: ACCEPT WITH FIXES.** The worker's reading of the exe holds, the builds are what the report says and
every reported check line reproduces. But the task's one hard condition - a gate must not break the join - is
not met and the tool's own guard against that has stopped working on a gates build (D1). Three weaknesses of
the holds themselves (D2..D4) are cheap to repair and should be, before a live run is read as a verdict on the
idea. Neither build should go on the owner's tab before D1 is answered by a JOINED run.

## 1. Re-derived by my own commands

| claim | result | evidence |
|---|---|---|
| `TriggerActorsDead` arms once and fires by itself after 30 s | **holds** | vtable 0xbcac84: slot 26 = 0x4afb80, slot 25 = 0x8def80. 0x4afb8d compares the message with word [0x168ccf0], which 0x6ffa16 registers as "AITrigger" (`ff2\levelsetup\online\TriggerActorsDead.cpp`); 0x4afb96 / 0x4afb9c: deaf while +0x41 (armed) or +0x42 (spent); 0x4afbbd: deadline = [[0xdd2640]+0x48] + 0x7800. A tick is 1/1024 s: `TriggerDelay2` multiplies its seconds by the double at 0xb39f70 = -1024.0 (0x744d29). 0x8def80: only in session state 0x19 (0x8defad); loops the list at +0x3c through 0x5f4470; 0x8df00b `cmp now, [esi+0x44]; jg` fires on the deadline whatever lives; then +0x41 = 0, the list at +0x38 gets the message, +0x42 = 1. An EMPTY list fires at once (0x8defcc `jle` with bl = 1) |
| 'dead' = no object, or an actor with state byte 0, or a group with ONE dead actor below | **holds** | 0x5f4478 null -> 1; 0x5f449c `cmp byte [esi+0x576], 0; sete`; 0x5f44d0..0x5f44da: the first child that returns 1 makes the group dead; a child that is neither actor nor group -> 0 |
| a `DefendBehaviourRout` with field 8 = 1 starts once | **holds for 'AITrigger'** | slot 26 = 0x4ebed0: [0x168d804] ("AITrigger", basebehaviourrout.cpp, 0x781563) starts it unless +0x41, or +0x42 and +0x40. Field 8 is 1 and field 5 `eDF_NotSet` on all 98 / 505 Defend steps of the two builds (read from the archives). NOT said by the worker: the message whose id is at [0x168d844] calls the start routine with no test at all (0x4ebf2b..0x4ebf3b); who sends it was not found (the dword is not written by any instruction that names its address) |
| the state byte: 0 dead, 1 in play, **2 'the rest', assumed 'not in the world'** | **the 2 is wrong, the conclusion probably right** | 0x7e72d0 is `ZActor` slot 354 (confirmed). Who passes 2: `ZBecomeRagdoll@CPPScript` slot 2 = 0x677200 at 0x6772ad, and the same script passes 0 later (0x677504, 0x677a12); `ZFFActionHealWounded` 0x4ea150 passes 1 (0x4ea1bf). So **2 = going down / a ragdoll that may still get up or die**, not 'asleep'. What a sleeping squad's actor holds: the constructors zero +0x574..+0x577 (0x7d2788, 0x434e12, 0x86fdcf) and the routine that enters an actor in the game data's table of 0x200 actors writes **1** (0x546eca, inside 0x546de0). Nothing I found sets a sleeping squad's actors to anything else: so 'not dead' most likely as 1, not 2. File evidence the same way: 140 of the 175 groups that stock F07's 28 waits name belong to squads with `ZSquadScript` field 3 = 0 |
| 24 squads / 45 men, all asleep, woken by trigger boxes only | **holds** | my own scan of every controller of the level for a reference into an enemy squad from outside it (`rev1.py wake`): 24 `TriggerBox` field 17 lists, 3 `TriggerDelay`, 4 `TriggerDelay2`, nothing else; no squad names another squad. All 24 have field 3 = 0. The box -> squad table of section 2.3 of the note is the one I get |
| the gates as built | **holds** | 49 `TriggerActorsDead`, 7 names x 7 squads, one list per name, field 1 = 0, every entry a ZGROUP with exactly one Enemy ZFFActor and no sub-group, no squad named in part; each chain is step (one place) -> wait, seven times, then the car; no sprint in the tower (`rev1.py gates` / `chains`). Node class and controller list are the stock model's (`ZBoxPrimitive`, `TriggerActorsDead`) |
| `--no-gates` = the old chain; the delivered step is the final code's | **holds** | rebuilt both into my scratch: `--no-gates` archive sha1 c8eb1e86.. = `rt_full7\2_bots`; default archive 91be4ea5.. = `z_rooms\steps\2_bots` |
| rt_full7 lost the two talk delays | **holds, and is already repaired** | `rt_full7` and `z_route7` have sha1 34a7c381 (9.29 / 0.60); every log up to I5_DM09 (08:19) says 'starts at 9.30 s'. At 08:34:08 the lead put rt_full6's file into `z_route4\retomoto_tab_fix`, `w_tabW` and the game folder (commit c99d16c; the old file kept as `KLTalk.ini.delays-9.29-0.60`). Both z_rooms builds have 6c78c079. The sentence 'on the owner's tab' in the note is stale since then |
| other maps have no such wait | **holds** | 0 `TriggerActorsDead` in the bots' squads of `z_route3\M01`, `z_loot3\M02`, `z_cover3\M03`, `z_route\M06` |

Not re-derived: `TriggerCounter` 0x541220 and `TriggerDelay2` 0x71e250 beyond the tick constant; the three planted
faults (logs read, not rebuilt); the pictures.

## 2. Checks re-run (both builds; every last line is the reported one)

| check | `retomoto_full` | `retomoto_full_r` |
|---|---|---|
| `kl_fa_bots_rt.py check` | PASS (0 FAIL, 2 NOTE), 7 gates, jump list 7, [CrewJoin] 7; kl_fa_bots part PASS (0 FAIL, 10 NOTE), 367 squad nodes | PASS (0 FAIL, 7 NOTE); 1468 squad nodes |
| `kl_fa_bots_dyn.py check` | PASS (0 FAIL, 7 NOTE); FakeTargets 1, outside 0; loot window clean | PASS (0 FAIL, 4 NOTE); the same |
| `kl_impact.py` | problems: 0 in 1 levels | the same |
| `kl_map_guns.py check` | 6 guns with looks, problems: 0 | the same |
| `kl_fa_talk.py check` | FAIL 1: 'the countdown's NOW! starts at [7.51], the blast is at 16.50' (the hand-set delays; as reported) | the same |
| `kl_bain.py check` (stream `rt_full7\PC_Def.str`) | 26 Bain sounds, 0 not in PC_Def.str | the same |
| sizes | .prm 79879056, .ANM 21642904, .fxc 17760648, .WAV 27802960 = rt_full7's | the same |
| `kl_fa_street.py report` | exit 0, 47 actors, 0 with a drawing fault | the same |
| side files | KLJoin / KLGuns / KLWardrobe = rt_full7's byte for byte; KLTalk = rt_full6's | the same |
| `kl_fa_bots_rt.py diff` (1_guns -> steps\2_bots) | only the squad was added | `kl_fa_bots_dyn.py diff`: only the squad's steps were made anew |

## 3. Defects

### D1 (must) - the join: a gate that is still waiting starts a TOWER step for a bot the hook has moved to the street, and the tool's guard against exactly that no longer sees it

The brief: 'when the player takes the join, klcrew_rt teleports every bot in play to the lobby - a gate must not
break that'. A `TriggerActorsDead` that is armed when the human steps into the tower car fires up to 30 s later
and sends 'AITrigger' to the next tower step, which has never run and so starts (section 1). The old chain had
no wait behind the loot table; each bot now has seven, and `retomoto_full_r` adds **36 timers of the dynamic
step's own** (4..12 s holds between the gates: `rev5.py`), 3..10 per bot.

`kl_fa_bots_dyn` already knows this hazard and forbids it: `program()` gives the first chain of a two-part map
'no timer behind the last loot wait' (`(last_chain or not post)`, line 1666), and `check()` FAILs 'timer .. runs
behind the last loot wait of a chain that the jump cuts off: it would start a step of this part for a bot the
hook has moved to the next' (line 2342). Both take a `TriggerActorsDead` for a loot wait (lines 842, 1540,
2337: `kind in ('loot', 'dead')`). On a gates build 'the last loot wait' is therefore `036_TriggerActorsDead_lobby`,
the bottom of the tower: the rule protects one leg, the 36 timers are allowed again and the check passes. In
`z_route7` (no gates) the same step leaves nothing but 0.1 s gap timers behind the loot wait.
`re/retomoto_bots_rooms.md` 5.2 says 'every other rule is as it was'; in effect this one is off, and section 4
describes `_r` as 'the holds and the waits are the gates build's own' without the 36 holds.

Who is exposed: a human who gets to the car while the seven still wait - which the gates make the normal
case, since they hold up to 30 s at seven places while he walks on. What the bot then does is not established
(the note says so); the worst reading is all seven standing in the street lobby. The note lists this under
'not done'; it is the condition of the task.

Fix, in order of cost: (a) a joined run with bots waiting at a gate BEFORE anything else is concluded - the
scripted walking player exists now (`tools/kl_playtest.py`); run with the position log; (b) in
`kl_fa_bots_dyn`, 'the last loot wait' = loot waits only when the chain has gates, so no hold of its own
behind the table and the check's rule back in force; and a line in the check that names the gate waits as the
exposure instead of passing silently; (c) if (a) shows stuck bots: the JumpPoint list form the note sketches,
or a re-order from the hook after the teleport (the lead's file).

### D2 (should) - `retomoto_full_r`: the dynamic step stops single bots for 4..12 s between the gates, most of them beside an enemy's post

36 such holds (`rev5.py`), 25 within 6 m of a rout place of an enemy squad, three inside a wake box:
- Squad#02 `032_DefendBehaviour_pos_cover` (1597, 21000, -298), 5 s, INSIDE `TriggerBox_EnterAtrium` - the very
  place the worker's own planted fault `inbox` uses to prove the check FAILs a hold there;
- Squad#07 `034_.._pos_cover` (-2326, 20300, -702), 12 s, 1.4 m from `2nd LeftCharge`'s flank place, and
  Squad#04 `034_.._pos_cover` (-2015, 20300, -1454), 8 s, inside `Trigger_2ndFloorStairEnd`, 2.2 m from
  `LCharge`'s post: the foot of the first flight, where the note counts 10 of the 34 deaths;
- Squad#07 `036_.._pos_cover_b` (-2445, 19600, -130), 12 s, 0.1 m from `InfrontElevator`'s last place.
This is what section 1.2 of the note blames for R7d ('its holds stop a bot for 5..12 s at a cover among squads
that have just woken'). Rule 1 of the worker's change keeps the dynamic step off the gate's own hold only.
The fix of D1 (b) removes all 36.

### D3 (should) - gate 2 (reception): the covers the seven are sent to straddle the box that wakes the next ten men

`kl_fa_bots_rt.check` tests the hold POINT against later fights' boxes. `DefendCover` takes a cover within 500
of it and chooses the side itself (the note's own words). `rev4.py`: every one of the seven reception holds has
a cover box within reach whose standing ring lies partly inside `TriggerBox_EnterAtrium` (x 1435..1635; wakes
six squads, ten men): `CoverBoxh_134` (1700, -970) and `CoverBoxh_135` (1700, 766) - the holds' OWN boxes for
Squad#06 and Squad#05, 26 % of the ring - and `Reception_Group_01!CoverBoxM_06` (1757, -179), 12 %. The side
that lies in the box is the WEST side, and that is the protected side against four of the seven men this gate
names: the reception's three squads stand EAST of the desk (x 2900..3330), and they are named here precisely
for the case that they outlived the door gate's 30 s. `GATES[1]['enemy']` is (-1, 0) for all seven.
Fix: test the cover's whole ring (or keep the gate's covers 230 + a margin away from a later box), and give
the reception gate covers east of x 1870 only. The atrium gate has the same shape against
`TriggerBox_EnterAtriumFurther` (holds 65..147 from it, 57 % of the ring inside), but that box wakes only the
two men no gate waits for.

### D4 (should) - gate 5 (floor2) is not a hold short of its fight: the way to it runs through the men it names

Stand-in path of the leg gallery hold -> floor2 hold (`rev7.py`, three bots): it passes **1.7 m from
`LCharge`'s post, 3.9 m from where `RCharge#01` is sent, 6.2 m from `2nd LeftCharge`'s flank place, 0.5 m from
`Sneakup_01`'s first place - 20..26 m BEFORE the hold**. These are the men gate 5 names (and gate 4 names
from one floor up across the well, with a line of fire that is ASSUMED and by the note's own L5 a candidate to
run out). If gate 4 runs out, the seven walk - no sprint any more - through five or six men at arm's length and
on for 20 m with their backs to them. That is the deadliest place of the note's own table. Also on a post:
Squad#05's floor2 hold (-624, 20300, -1762) is 0.28 m from `LeftBehindStairs`' second rout place, Squad#03's
reception hold (1917, 21000, -58) 0.33 m from `AtrTop_Reception`'s; section 1.3 guesses close combat for the
one-step kills.
Fix: say it in the note; a check line 'the way to a hold passes within N of a rout place of a squad that
gate names'; for the stairs either a hold at the head of the first flight that is tested against the
collision, or the sprint back on that one leg.

### D5 (note) - 'counted from each bot's own arrival' is 'from within 10 m', and six waits are armed before the bot has left the hold before

The Defend goal's wait (0x686c4c): radius 10.0 when goal +0x40 == 1, else **1000.0**; goal +0x40 is the rout's
member +0x58 (slot 14 = 0x4b4af0, 0x4b4b8d..0x4b4b97), the second of two enum members, i.e. field 5 `eDF`
(tools/dd_enums.json: 0 NotSet, 1 Line) - ASSUMED from the member order; the distance is 3D (0x60b160 ->
0x6499b0). Every step of ours has `eDF_NotSet`. Holds within 1000 of the place before (`rev8.py`): door of
Squad#02 / #03 (652, 655), gallery of #04 / #06 / #08 (320, 597, 322), floor2 of #06 (823: his floor2 clock
starts on the third floor, about 50 m of way before the hold). Not dangerous. It also says that no timer covers
a bot that never comes within 10 m of its hold: the 30 s start at the arrival, as in stock.

### D6 (note) - wrong words in code and note

- 'actor state 2' = 'not in the world' (GATES comment line 109, the check's FAIL text line 1272, note 3.1): see
  section 1. A man who is DOWN and not dead holds a gate until the ragdoll script sets 0.
- 'the fall-back could not be chosen': it cannot be made longer, but it can be made shorter by a
  `TriggerDelay2` beside the wait in the hold step's list (the next step starts once) - the dynamic step's own
  form of a list of two. Worth knowing because the worst case as built (363 s after GO) is longer than a round
  where one was seen to end (L8_DM02: state 0x19 -> 0x1f exactly 360.2 s after GO; no Retomoto run has gone
  past GO+270).
- `--gates floor1,lobby` is offered as the A / B run 'old chain + the last two gates'. It is not: the way from
  the table to the first hold becomes ONE order of 138 m without sprint (plan: '13834 of path, 0 way
  station(s)'), where the old chain had ten way stations and sprint.
- V1 as 'the control' and 'with that hook the end of the way is the deadly place': one run. I5_DM09 (08:19, the
  same build, the same hook line 'crew off your stage x 1.00') lost six of six by GO+99 on the THIRD floor.

### Checked and found sound

- No check was weakened in the worker's own edits: `check()` gained tests, and the repair of the silently
  skipped tower-end tests is real (the old code took the gate for the first step and `continue`d).
  `diff ... also=(.., ROOM_COUNTER)` is the allowance the room-gate commit owed.
- Nothing outside the three files: the writes of 08:34:08 in `z_route4\retomoto_tab_fix`, `w_tabW` and the game
  folder are the lead's (commit c99d16c); the worker's `talk_delays.py` wrote only `z_rooms\retomoto_full`.
- The two rules in `kl_fa_bots_dyn.py` act only where a chain has a `TriggerActorsDead` on Retomoto's tower
  part (`_wake` is empty otherwise); the scratch copy the worker compared against is HEAD's file (sha1 aa7f65f8).
- Guesses are marked as guesses, in the code and in the note.

## 4. Counterexamples to 'the seven hold in cover short of each fight until its men are dead, or 30 s'

1. Gate 5: the hold is 20 m past the men (D4).
2. Gate 2: with the reception's men alive behind them, the protecting side of the hold's own cover is inside
   the next fight's box (D3).
3. `_r`: a bot holds alone, 4..12 s, at 36 places between the gates (D2).
4. A played round: the human at the car while the seven wait (D1).
Gates 1, 3, 6 and 7 stand as described: the holds are beyond the gate's own box, 8..11 m short of the next
one, no cover within reach in a later fight's box, no named man's post within 3 m.

## 5. Can the proposed live checks tell success from failure?

- L1 (loads): yes.
- L2 (the escort's 'its route place' as the gates' clock, 'much longer than 30 s = the wait did not fire'): **no.**
  A wait is armed only when its bot is within 10 m of the hold (D5). The hook pulls the escort back whenever he
  is 8..15 m from the idle player; the door holds are 19..20 m from the balcony. An escort who never comes
  within 10 m of his hold shows a route place that stands for ever with every wait in order. Use the position
  log of all seven (`live.py --poslog`, a place every 5 s) as the clock: a bot at hold n that is on its way
  to hold n + 1 within 30 s of coming within 10 m.
- L3 ('lost' places bunch at the holds): only bots that are hit leave a line; the position log shows drift.
- L4 (alive at each gate against V1 and T7): **not in one run.** The old chain on the same hook gave 4 dead (V1)
  and 6 dead (I5) of the six that are not the escort. Three runs of the gates build against V1 + I5 + one more,
  and a number said beforehand (e.g. four or more of six at the tower car in two of three runs).
- Nothing in L1..L6 can tell 'the gate opened because its men are dead' from 'it opened at once because the
  entries read dead' (no line says an enemy's state): a gate passed in under a second with no 'lost' line near it
  is the sign to look for.
- No joined run is in the list (D1). The run length asked for (GO+370) may be past the round's end (D6).

## 6. What was done about each defect (the track's second round, 2026-10-11 ~10:30; appended by the worker, not by the reviewer)

OFFLINE as before: nothing started, installed or committed. Files: `tools/kl_fa_bots_rt.py`,
`tools/kl_fa_bots_dyn.py`, `re/retomoto_bots_rooms.md` (written anew; its section 10 is this table), this
section. The builds of the names the task gives are the SECOND form now; what this review read is kept in
`<work>\build\z_rooms\round1\` (so every path above that begins `z_rooms\steps`, `z_rooms\neg_tests`,
`z_rooms\retomoto_full..` reads `z_rooms\round1\..`). Between the review and this round the lead ran the first
gates build live (G1_DM09, 09:31, idle player): its reading is section 1.4 of the note and is used below.

| defect | fixed / refuted | what, and the evidence |
|---|---|---|
| **D1 (must)** the join; the dynamic step's guard off | **(b) fixed, (a) written and not run, (c) not built - the hard condition is NOT proven** | `kl_fa_bots_dyn.last_loot_wait`: on a chain the jump cuts off 'the last loot wait' is the table's, a gate is not one; `program` gives the tower's way out no hold and no timer; `check` reads it the same way and FAILs a timer there again. Evidence: `round1\retomoto_full_r` through the check as it is: FAIL, 14 lines 'timer .. runs behind the last loot wait ..'; the new `retomoto_full_r`: PASS, and `rev5.py` (the reviewer's, unchanged) says '0 holds of the dynamic step between the gates', `rev3.py` '7 TriggerActorsDead' and nothing else behind the loot wait. Both checks NOTE the gates' own waits as the exposure ('THE JOIN', with the count: 7 gate waits + 1 loot wait a bot). (a): this track cannot run the game; the joined run is written with track H's tool - `z_rooms\live\J1_DM09_join.ini` and the control `J0_DM09_join_oldchain.ini`, what to read and the verdict said beforehand in the note 7.2. (c): not built (note 9.1); READ for it: 0x72e0f0 sends 'AITrigger' to the jump list in the list's order. One thing done to make the exposure smaller: the last gate no longer names `GuardingElevator`, a man no hold can reach - that wait could only run out, beside the car |
| **D2 (should)** 36 holds of the dynamic step between the gates | **fixed** | by D1 (b). `retomoto_full_r` rebuilt; the dynamic step adds on the tower's way out 14 forks of the way (0..3 a bot), the staggered starts and the opening modifier, nothing that waits (note 4.3). Two more rules there, both only on a gates build: another way of a fork passes no enemy post the build's way keeps clear of (`Routes.passes_more`; `kl_fa_bots_rt.check` FAILed the first try: the runner's way 2.9 m from a place of PillarCover and 11 m on), and nobody's loot wait is cut to 15 s when gates follow it. The plan of the five builds without a gate is the committed module's byte for byte (`neg_tests\dyn_same_plan.log`) |
| **D3 (should)** the reception's covers straddle the atrium's box | **fixed** | `hold_spots` / `check` 2b: every cover box within 500 of a hold is tested with its whole standing ring (the middle + 16 places on each of four rings to 270) against the boxes of later fights; FAIL in the check. The reception's hold is its east half (x 2067..3090; 137 of 180 places fell to the rule). `rev4.py` (the reviewer's) on the new build: reception 0, was all seven. Its other 24 lines are three cases the check names with a reason: `EnterAtriumFurther` at the atrium (the reviewer's own 'same shape': men with no post on that floor; there is no other cover at the mouth) and at the gallery (no way round that box), the boxes the two flights of stairs END in, and `Trigger_2ndRightGoLeft` (men no gate waits for). Planted faults `ring` and `inbox` FAIL |
| **D4 (should)** floor2's hold beyond its men; holds on a post | **fixed - by a third way, not by one of the two the review offers** | check lines as asked: a hold within 300 of a post of a man who may be alive (FAIL), a way - every way of every fork - that comes within 6 m of a post of a squad the gate names and no earlier gate has dealt with and then goes on more than 10 m (FAIL), squads out of reach / without a straight line on the mesh (NOTE). `round1\retomoto_full` through it: 6 holds on a post, 8 ways that walk past (all seven to floor2; one to the lobby, past the man of InfrontElevator - not in the review). The stairs: NOT the head of the first flight (no straight line on the mesh from any of 127 places at its three cover boxes to any post at the foot; the collision is read by no tool here) and NOT the sprint (it leaves nine living men above the second flight and the atrium floor). The hold is AT the foot, at the first cover there. G1 measured the fear: the four who walked that leg lost 81, 143, 156 and 288 health on it - the worst half minute of the run - and none died. Whether stopping there is better is a GUESS; the note 7.3 says what a run shows and that the first form's place is one edit away. Also from G1: the gallery no longer names the four men across the well (it ran its 30 s and a bot was shot dead at his hold meanwhile); floor2 names `2nd RightCharge` (they killed the bot that came down another flight); the man who ends beside the floor1 hold is floor1's |
| **D5 (should)** the live checks | **fixed; one point of it partly refuted by G1** | note section 7 written anew: J1 / J0 first; three idle runs against G1 and the old chain's SPREAD (V1 four dead at the lifts, I5 six by GO+99 - the first form's 'control' is withdrawn); verdicts said beforehand; the sign of a gate that opens for no reason; the place log, and that this map has none unless its KLJoin.ini carries a `[CrewHop]` (`z_rooms\live\KLJoin_with_poslog.ini`). Refuted in part: 'an escort who never comes within 10 m of his hold shows a route place that stands for ever' - in G1 his route place went from hold to hold every 34..36.5 s (reception: 8.5 s). His lines are the gates' earliest clock; they say nothing of where the others are, which was the review's point and stands |
| D5 note ('arrival') | corrected | note 3.1; `ARRIVE_3D`; `assign` pairs bots and holds so that no hold on another floor is within 10 m of the place before (floor1: 4 of 7 -> 0), the check NOTEs one |
| D6 notes | corrected | state byte 2 = going down (code comment, FAIL text, note 3.1); 'a step starts once' is said of 'AITrigger', and the two unnamed messages are 'DebugTrigger' / 'DebugTriggerSignals' (objects of 0x6fb080 made at 0xafff20 / 0xafff40; no sender found); the fall-back can be made shorter and is not (note 3.3); `--gates a,b` is not the old chain with fewer gates (tool text, note 5.1); the talk delays are the lead's since 08:34 (note 6.3) |

Checks of the second form (last lines; whole logs `z_rooms\checks_full*\`, record `z_rooms\checks.txt`):
`retomoto_full` - kl_fa_bots_rt PASS (0 FAIL, 9 NOTE), kl_fa_bots PASS (0 FAIL, 10 NOTE; 367 squad nodes),
kl_fa_bots_dyn PASS (0 FAIL, 8 NOTE), kl_impact 0, kl_map_guns 0, kl_bain 0, kl_fa_talk FAIL 1 (the owner's
countdown delay, as rt_full6), street report exit 0; `retomoto_full_r` - PASS (0 FAIL, 14 NOTE), PASS (10 NOTE;
1165 squad nodes), PASS (0 FAIL, 5 NOTE), the rest the same. Three FAIL rules were added and one restored, and
the first form fails all four. **One rule of the first round is narrower now, on purpose:** 'a hold INSIDE the
trigger box of a later fight' no longer applies to a box the seven cannot go round (a stair ends in it, or it
lies across every way; measured on the mesh by the check itself, not taken from the plan). The holds at the foot
of the two flights stand in such boxes - that is what 'the hold AT the fight' means there - and would FAIL the
rule as it was. The planted fault `inbox` still FAILs. If that narrowing is not wanted, the stairs need one of
the review's two ways after all.
