# The AI heisters: leaving early, standing still, the loot square

2026-10-11, track N. **OFFLINE: the game was not started, nothing was written into the Dog Days folder, nothing was
committed.** New: `klhook/klmove.c` (keys `[Bots] Restless..`, `WaitForYou..`, `BoardNear..`, `MoveDry`, `MoveLog`),
sample lines in `klhook/KLHook.ini`. `klescort.c` is unchanged. **NOTHING OF IT HAS RUN IN THE GAME.**

**Second version, after the adversarial review (`re/bots_move_review.md`, ACCEPT WITH FIXES; section 8 says what
changed per point).** The part's names now begin with `klmv_` (the first version's `kly_` is `klgrudge.c`'s).

Words: **read** = disassembled at the address given (kl2.exe build 0490); **log** = the owner's own `KLHook.log` of
12:33 - 12:45 or a run log in `<work>\build\klhook\live\`; **measured** = counted by a script on those logs;
**ASSUMPTION / GUESS** = fits, not proven.

The owner (2026-10-11): 'the ai seems to leave early, they should have to get to the car physically and make it so
they're normally moving majority of the time somewhat ... sometimes they just be standing still a bit ... they should go
onto like a money square thing and if nothing happens for like 5ish seconds they get fed up n move but if they do end
up getting the money they might go back for it'.

## 0. Short answers

1. **Both readings of 'leave early / get to the car physically' are true.**
   - (b) **A bot counts as aboard from afar: yes, through a `ZAllyEscapeBox`.** Log, the bank, 12:35:42 - 12:35:45:
     record 4 at (-1197, 200, -2651), 45.6 m from the van, 'aboard' 2.9 s later; second round: record 5 at 48.6 m,
     aboard 1.5 s later. Read: the box's update (vtable 0xbc7f6c slot 25 = 0x907a50) boards every AI record in play
     whose actor is inside it through 0x74d7f0 -> rules vtable +0xb4 = the boarding rule 0x6840a0 - **no stage, no
     path, no distance**; the rule itself only asks 'the vehicle waits'. The stage byte that BoardAll / FollowOut
     write does NOT board anybody by itself: it switches the board tactic on (0x4faf60), whose action (0x82f970) runs
     to the boarding object and calls the rule within 3 m (0x82fa35, squared 90000.0). So the far boardings are the
     boxes' work, not the hook's.
   - (a) **The car goes 8 s after it arrives, whoever called it.** Log, the park: he took stage 3 himself at 12:43:01
     (FollowOut called the crew), the helicopter waited from 12:43:09, 'leaves without you: 2 of the crew aboard' at
     12:43:17, he died at 12:43:20. Log, the bank's first round: **a bot called the van** - record 1 had stage 3 at
     12:35:34, he at 12:35:42; the van left at 12:35:49 without him, came again at 12:36:11, he boarded on its third
     visit (12:36:45). Read: the exit trigger (0x6c3d50) gives stage 3 and calls the vehicle for whoever stands in it,
     human or AI, with no stage / money test.
2. **Standing, measured** (section 1): 22 .. 52 % of the sampled bot-seconds; most of it at the chain's own places
   (cover holds, loot waits, Retomoto's gates) - meant waits that are long -, the rest at money that does not pay and
   at the exit / the van's stop.
3. **Built** (section 3): `Restless` (the loot square's 'fed up', a stuck bot's order given again, optional shifting
   at a hold), `WaitForYou` (nobody calls the vehicle before you; the driver waits while you come), `BoardNear` (a
   far escape box takes nobody; the bot gets stage 3 and walks). All off by default.
4. **A per-bot 'this money is not for you' mark does not exist** in the loot tactic (section 2.3). The mark the hook
   uses is per OBJECT: byte `+0x6c`, the candidate filter's own.

## 1. The standing, measured

Script: scratchpad `n/stand.py <log> <build folder>`. Input: the place log (`[CrewHop] Dry=1 Log=2`: every bot's node
every 5 s - **only from heist stage 1 on, so the approach before the building is not in it**), the crew log's money,
the build's own notes (`bots.txt` stations, `dyn.txt` cover holds) for the labels. A pair of samples that moved under
1 m = 5 s of standing. Labels are by PLACE (within 3 m of a hold, 6 m of a station), not by the squad's node: which
chain node was running is NOT read.

| run | map / build | human | stood | where (bot-seconds) |
|---|---|---|---|---|
| B1_DM01 | Hot Coffee `z_route3\M01` | idle | 322 of 624 = **52 %** | cover holds 101, nowhere named 70 (two bots 25 - 40 s at (7057..7141, 0, 22569..22660)), at loot while the van waits 90 (50 of it earning), loot that pays nothing 40, exit 15 |
| W1_DM02 | Late Night Opening `z_loot3\M02` | idle | 297 of 896 = **33 %** | cover holds 161 (three spells of 45 - 50 s), loot earning 60, the ENTERS box 45, loot no pay 10 |
| L12b_DM02 | the one-stop build `z_m02s1\M02` | idle | 528 of 1152 = 46 % | the escort beside the idle human 196, cover holds 201, nowhere named 60, loot no pay 55 (one bot 45 s at (1877, 510, 2544)) |
| H0_DM03 | Withdrawal `z_hop\M03` (old) | idle | 10 of 70 | only 17 place lines: **the bank is not measured** (no run of the tab's `z_cover3\M03` has the place log) |
| B6_DM06 | the park `z_route\M06` | idle | 151 of 634 = **24 %** | cover holds 106 (35 s and 40 s at two holds on the second floor), way 15, park 10, loot no pay 10 |
| J1_DM09_join | Retomoto gates `z_rooms\retomoto_full` | scripted, walks | 433 of 1117 = **39 %** | nowhere named 186 (= the gates' holds: the tool's notes do not list them by place), loot no pay 101, way 70, loot earning 55, enter 20 |
| B1_DM09_board_gates | the same | scripted | 367 of 911 = 40 % | nowhere named 176, way 81, exit 40 (40 s at the lobby's exit), enter 35, loot no pay 20 |
| J0_DM09_join_oldchain | Retomoto old chain | scripted | 161 of 724 = 22 % | nowhere named 121 |

Per bot the share is 10 .. 63 %; the per-bot lines with every spell of 10 s and more are in scratchpad
`n/stand_out.txt` (run the script again for them).

What the spells are:

- **Cover holds (the largest block on every map but Retomoto).** A hold's own timer is 5 - 12 s (`dyn.txt`), yet the
  spells are 30 - 50 s. Where they lie they are the holds beside a loot stop: the chain waits there on
  `TriggerLootDepleted` with a deadline of 15 - 45 s (M02: 45 s, M06: 15 - 35 s, M01: 30 s, M03: 20 s) while ONE or
  two of the seven empty the place. So the long standing is a meant wait on the looters. (By place; the node was not
  read.)
- **Retomoto's gates**: `TriggerActorsDead` with a 30 s fall-back each (re/retomoto_bots_rooms.md) - meant, and what
  keeps the crew alive there.
- **Loot that pays nothing**: 10 - 101 s a run; the form runs L8 / L10 / L11 showed as a hold for good.
- **The exit / the van's stop**: bots at stage 3 standing in the escape box, or at the lobby's exit, until a vehicle
  comes.
- **Nowhere named** on Hot Coffee: two bots 25 - 40 s at the same spot 3 m from a hold's place: GUESS a hold of
  another way of the fork.

So 'training' is three things: shorter loot deadlines for the bots that do not loot (level data, section 5), a bot
on a hold that shifts instead of standing (`RestlessHold`), and no bot left on money that does not pay (`Restless`).

## 2. The mechanisms (read)

### 2.1 Who takes a bot aboard

| path | code | asks |
|---|---|---|
| the board tactic | `ZBoardEscapeVehicleTactic` test 0x4faf60, action 0x82f970 | stage >= 3 (0x4fb064), the vehicle waits (or arrives within 2 s), a path; runs to the boarding object, boards **within 300 units** |
| the escape box | `ZAllyEscapeBox` slot 25 = 0x907a50 | Arcade; an AI record (+0x79 mask 1) in play whose actor is inside the box (0x758cb0: the box entity's own 'point inside', vtable +0x170). **Nothing else** |
| a BOARDS trigger | `ZOnlineGamePlayTrigger` 0x8d2740, kind 2 | whoever stands in it (not measured per map here) |
| all three end in | rules vtable +0xb4 = 0x6840a0 | session state 0x19; vehicle state 3 / 4 (or 5 in its first second); actor branch 0x6841fd: the record's status 0 -> 4, 0x89c890, `[actor+0x8f0] = 1`; nobody left in play -> the wait timer = 0 (0x684281) |

The boxes of the tab's builds (`bots.txt` of each): every map has one beside the van's stop with the seven's last
places in it - Hot Coffee 5.1 m from the boarding action, Late Night Opening 3.8 m, Withdrawal 8.4 m, the park's
beside the helicopter - and **Withdrawal has a second one at the one-way drop in the yard, round (-1706, 419, -899):
42.6 m from the van's stop (2438, 122, 102)**. Retomoto has one beside the tower car (the fall-back when the join is
off).

Distances at which bots went 'aboard' in the owner's log (place = the `follow:` line before it):

| round | record | place, distance to the boarding place | aboard after | by |
|---|---|---|---|---|
| bank 1 | 1 | (874, 68, -151), 15.8 m | 2.4 s | the box beside the van (it ran the last metres) |
| bank 1 | 4 (escort) | (-1197, 200, -2651), 45.6 m; 18 m from the drop's box | 2.9 s | **the drop's box** |
| bank 2 | 4 (escort) | (-1952, 200, -3465), 43.1 m | the tick the van stood | **the drop's box** |
| bank 2 | 5 | (-1977, 200, -1937), 48.6 m; 11 m from the drop's box | 1.5 s | **the drop's box** |
| bank 2 | 3 | (-871, 240, -5227), 62.7 m; 44 m from the drop's box | 7.9 s | the drop's box (GUESS: no place line between) |
| park | 3 | 18.7 m when called | the tick the helicopter stood | the box beside it |
| park | 4 | 12.5 m | 2.0 s | the box beside it |

Those who walked the whole way and died or were left: bank 2 record 1 (dead 8.0 m from the van as it left).

### 2.2 Who calls the vehicle, and the byte that stops it

`ZOnlineExitLevelTrigger` slot 34 = 0x6c3d50, in a round, for whoever activates it: stage 3 (0x5dd890); then, if
the vehicle's state is 0 (0x6c3e3e) **and rules vtable +0x290 = 0x8ad6c0 (`mov al, [ecx+0x1ee]`) is 0** (0x6c3e4e),
vtable +0xb0 = slot 44 = 0x6cd8e0 -> 0x8154f0 calls a vehicle.

`[rules+0x1ee]` = 'the round's LAST vehicle has been called': slot 194 (0x8fa6d0) sets it in its case for state 2
(jump table 0x8fb078: state 2 -> 0x8fa758 `mov byte [esi+0x1ee], 1`, then the case of state 1); 0x8154f0 asks for
state 2 instead of 1 when `[rules+0xe8a]` is set (the round's time is too short for another trip, or its caller
forced it). Cleared by the callers of slot 194 with state 0 (0x4fb647 = slot 3, and four more). Other readers:
slot 153 = 0x87d000 (0x6ba930 is the same slot of the multiplayer rules classes, not of `ZGameRulesHeist`), behind
the human's client flag 0x20 'aboard' - never true in state 0; **and the HUD's round clock** (found by the review;
the first version of this note said 'nothing else'): `ZFATimeDisplay` slot 5 = 0x62a0c0 asks rules vtable +0x290
every frame (0x62a262, 0x62a381), in every vehicle state, and colours the clock's two text objects `[0xbbe498]` =
0xffcc0000 (red) when the byte is set, else `[0xbbe494]` = 0xffcccccc. 0x8154f0 does not read the byte. **So in
state 0 the byte switches the exit trigger's call off and turns the round clock RED; no rule reads it otherwise.**
With `WaitForYou=1` the clock is red from GO until the human has his stage. No other handle for the call was found
that is data only (the trigger's two tests are the vehicle state and this byte). (`[rules+0xe8a]` itself is NOT one:
the round's end reads it at 0x80543c, 0x8facce, 0x894456.)

The exit trigger is level-triggered (read by the review: its update 0x65dd10 walks everybody inside every tick and
calls 0x6c3d50 for each), so when the byte goes back to 0 the vehicle is called for whoever still stands in it.

### 2.3 The loot tactic and what can take a bot off it

`ZLootTactic` test 0x451920, per-bot terms: the stamp `[[actor+0x54]+0x30]` must be 4.0 s old (tuning +0xc34);
stage >= 1; not (stage 3 while the vehicle waits). Then the five candidates of rules slot 202 = 0x8b94d0: list one
`[rules+0xdcc]` (count `+0xdc0`) of `ZOnlineMoneyCtrl` (vtable 0xbc874c), an entry passed over when null, taken
(`[obj+0x34] <= 0`) or with byte `[obj+0x6c]` clear; within 800 / 400 of the bot's node.

- **No per-bot filter.** The stamp is shared with thirteen other readers (0x40f714 in the NPC health code, 0x4faf7d
  the board tactic's '2 s', 0x449d0d, 0x580456, 0x6160c8, 0x616124, 0x6225f6, 0x6901d3, 0x690263, 0x6f5b37,
  0x7abc34); no writer was found, so what it stamps is NOT established ('time since it was last hit' fits the health
  reader; a guess). **Not used.**
- **The stage** switches the tactic per bot (0 = off) but klbot.c and klescort.c take a falling stage sum as a new
  round (the Backstab pick is rolled again, the escort is chosen again): not used.
- **`[obj+0x6c]`** - readers, from a search of every function of the class's vtable and of the grab path: the
  candidate filter (0x8b95f2); the object's update slot 25 (0x5f1b2b), only 'the round is over and `+0x6c != 0` ->
  Deactivate'; slots 21 / 22 (the network copy; Arcade has none). Writers: init, taken (0x4e3f76), Deactivate
  (0x4c95e6), and `'Activate'` (0x4fb5d3 / 0x4fb5e4 set it - **an opened case re-arms it by itself**). The grab never
  reads it. So clearing it on an untaken object = 'no AI heister goes for it', for all of them, nothing else - as
  long as it is set again before the round is over (the hook does, in the pass that sees the state leave 0x19).

### 2.4 A meant wait and a stuck bot

The soldier's defend block `[soldier+0x64c]` holds the place its route chain last ordered (klescort.c 1). A Defend
step is over when its man has arrived; what waits after it is a timer or a `TriggerActorsDead`, which do not look
where he stands. So: **within 3 m of the block's place = where the chain put him = a meant wait** (gate, cover hold,
loot wait, the place beside the van); farther and not moving = stuck (a tactic that goes nowhere, no path). That is
the test the hook uses. It cannot tell a 5 s cover hold from a 45 s loot deadline: both are 'at its place'.

## 3. What was built: `klhook/klmove.c`

Its top comment is the spec. Everything is off unless its key is set, runs only in an Arcade round (state 0x19) on a
level that is not the stock one of its slot (klbot.c's gate), from the game's thread. `MoveDry=1` logs every
decision and writes / calls / wraps nothing.

| key | what | game data touched |
|---|---|---|
| `Restless=N` + `RestlessLoot` (default N), `RestlessLootBack=30`, `RestlessLootNear=200` | a bot **at heist stage 1 or more, not hit in the last 4 s, with no grab running (crew record `+0x15` = 0)** that stood N s within 2 m of a candidate money object whose amount did not fall: the object's `+0x6c` = 0 for 30 s (doubling, 240 s at most); back at once when its amount or `+0x74` changes, when the game re-arms it, and when the round is over; **not put back when its state `+0x64` changed meanwhile (the level deactivated it)**; a pass that cannot read the session loses no mark | one byte of a `ZOnlineMoneyCtrl` |
| `Restless=N` | a bot that stood N s more than 3 m from its defend place **and was not hit in the last 4 s**: that order again (0x760e50 with (place, 0, 1, 0), klescort.c's call and tests); the third time on a spot: beside the human, where it stays; after four on one spot **or six for one place of its chain**: left until the chain orders a place more than 6 m away. The chain's place stays the anchor while the defend block holds what the hook put there | one game call |
| `RestlessHold=N` (default 0), `RestlessPace=350` | a bot N s at its own place (or at the place the last shift sent it): an order to a place 3.5 m from the chain's place, another side each time; not within 4 s of a loss of health, not while a vehicle is called, not at an escape box | one game call |
| `WaitForYou=1`, `WaitForYouStage=3`, `WaitForYouFloor=0`, `WaitForYouMax=150` | while the human is a heister in play under that stage and the vehicle's state is 0: `[rules+0x1ee]` = 1; back to 0 when he reaches the stage, is dead / a fed / aboard, 150 s after the first bot stood ready at stage 3, and when the round ends | one byte of the rules object |
| `WaitForYouHold=15` | while the vehicle waits and the human comes (2 m nearer in 2 s, or within 15 m): timer `[rules+0x1d8]` + up to 5 s under 2 s, 15 s a visit | one float (FollowOutHold's) |
| `BoardNear=N`, `BoardNearVisits=3`, `BoardScanEveryRound=0` | every `ZAllyEscapeBox` (looked for at the scene's first round's start - 125 - 140 ms standstill, measured 2026-10-23 - and kept for its later rounds while the scene name stays, no level archive is opened and every kept object still carries the private vtable; `BoardScanEveryRound=1` = at every round's start, as before) gets a private copy of the class's vtable (34 slots, RTTI locator kept) with slot 25 wrapped: the stock update is not called while the box is farther than N from the boarding place, **the vehicle stands (state 3 / 4; the decision is kept through state 5, so a near box keeps the stock boarding of that state's first second)**, it is not the last vehicle and fewer than 3 waits have begun | the first dword of each box object (1 - 3 a level) |
| `BoardNearStage=1` | a bot at stage 1 / 2 within 5 m of a denied box while the vehicle waits: stage 3 (BoardAll's byte and tests: no traitor, in play, **not this round's escort**, the record read again) | one byte of its crew record |

**What BoardNear costs the crew.** A bot a far box used to take aboard now has the vehicle's 8 s a visit to walk
(the bank's drop box is 43 m from the van: about 14 s at 3 m/s). When the vehicle leaves WITHOUT the human it comes
again (about every 29.5 s) and from visit `BoardNearVisits` on every box works. When it leaves WITH THE HUMAN ABOARD
stock Arcade shoots every AI heister still in play (rules slot 7 = 0x74b6d0, re/bots_follow_out.md): in the owner's
bank rounds records 4, 5 and 3 lived only BECAUSE the drop's box took them. So with `BoardNear` alone 'physically'
means more of the crew shot at the departure, and the owner already says the crew dies too fast. It belongs
together with `FollowOutHold=<seconds>` (the driver waits while called crew comes nearer) or `FollowOutSpare=1`
(nobody left behind is shot); the start line names both keys' values and says so when neither is on. The part counts
the cost itself: at every departure `near: visit N: the vehicle leaves WITH YOU ABOARD / without you: K AI
heister(s) still in play (record, metres from the boarding place: ...), M of them (*) stood at a denied box on this
visit`.

**MEASURED 2026-10-11 (runs N1c / N1 / N1b on the bank, BoardNear=1500; re/bots_follow_out.md 11) - the advice
changes:** BoardNear itself works (the drop's box, 42.7 m off, 'takes nobody aboard', asked ~6,000 times a visit).
- **With BoardNear and a plain 8 s visit nobody of the crew arrives**: the vehicle leaves 15 s after the call, the
  crew is 46 .. 56 m off (N1c) and five are shot. The 14 s above was the walk from the drop only; from inside the
  bank the first bot is aboard 24.0 / 25.5 s after the call, the last would need about 36 s.
- **`FollowOutHold=15` as it was KILLED THE HUMAN ABOARD** (N1, N1b): a van that stands 21 s is destroyed by the
  police, and the rules then kill everybody with status 4 (slot 94 = 0x6a1100, grade 2). The hold is only safe with
  `FollowOutShield` (new, default 2: the held vehicle takes no hit; klescort.c 3 c2) - `WaitForYouHold` asks the
  same guard now. After the review (`re\bots_hold_review.md`): the guard fails closed (a key-framed van whose health
  object is not found is not held), the shield only starts at the first timer write (~6 s into a wait), 2 against 1
  is the owner's choice, and 25 s is the bank's measured value only (`re\bots_follow_out.md` 11.3, 11.4).
- **So BoardNear=1500 wants `FollowOutHold=25` (shielded) AND `FollowOutSpare=1`** for whoever still does not make
  it; `FollowOutSpare` alone is the cheap form ('they are simply left, not shot'), `FollowOutHold` alone under 20 s
  gets one or two of the bank's seven aboard. A larger BoardNear for the bank would only bring the far box back.
  NOT RUN IN THE GAME in this form: checks N3a .. N3g there.

**What WaitForYou costs** (the owner did not ask for the key): the round clock is red while the crew waits
(section 2.2), and the crew that is through the exit trigger stands at its last place - the escape box beside the
vehicle's stop, in the open - for up to `WaitForYouMax` = 150 s. W1 counts the deaths against run I3.

**WaitForYouStage - the guess and the alternatives.** The task's guess was 2 ('until he has left the building'). The
log says 2 would have changed neither of his rounds: on the bank he had stage 2 at 12:35:21, the bot called at
12:35:34; in the park nobody called before him. What his rounds show is a bot calling 8 s before he was there. So the
default is **3 = only his own step into the exit trigger calls the vehicle**; 2 and 1 are the same key; a time floor
is `WaitForYouFloor`; 'until he has looted' would be a money test (not built: FollowOutMoney is that idea on the
other key). The crew cannot deadlock a round: 150 s after the first bot stood ready the byte goes back, and the rules'
own forced last vehicle does not ask the byte.

**BoardNear - two values.** 1500: the boxes beside the vans work as today, the bank's drop box does not (its bots
get stage 3 and must take the drop and run). 300: no box works at all - every bot has to reach the vehicle's doors;
a bot whose board tactic finds no path stands until the third visit.

**Policy note for the lead.** BoardNear's vtable copy sits on every `ZAllyEscapeBox` of the level (up to three
objects of one class), not on one object; finding them is a scan of the committed private memory (klhud.c's way,
through `ReadProcessMemory` in 64 KB pieces, klmem's reserve with the .prm included) **at the first pass of EVERY
round** - once per rules address was not enough: a level loaded again can put its rules object where the last one
was. The game stands still for it; **how long is NOT measured** (my estimate 0.1 - 0.5 s is only that), the `near: N
ZAllyEscapeBox object(s) found in .. ms` line says it each time and M0 has the number in its PASS. If it is too long
at GO: scan in the countdown before GO instead (reads only; not built). The rules object's own vtable (slot 45, where all
three boarding paths meet) was NOT wrapped: klbot.c, klfed.c and others identify the rules object by its vtable.

## 4. Wiring, builds

`klhook/klhook.c` (not edited; three lines):

```c
#include "klmove.c"                 /* directly after  #include "klhop.c"  */
    klmv_init();                    /* directly after  kle_init();         */
    klmv_tick(game_thread);         /* directly after  kle_tick(game_thread);  (it reads who is an escort) */
```

Compile check of the second version (2026-10-11): a fresh `git archive HEAD klhook` + `klmove.c` + the three lines,
in `G:\kl_scratch\N\src`: TEST `G:\kl_scratch\N\test\dinput8.dll` sha1 0a63cfe6b05ddc255feccdde04b15cfa8fb496fc
('built ... (TEST)'), SHIP `G:\kl_scratch\N\ship\dinput8.dll` sha1 1fe62b519b8d32683828930612a0dc425bb91e4c ('built
... (SHIP)'); no warning from klmove.c. The sha1s name those two files only: a rebuild gives others (time stamps).
(HEAD's sources: the working tree's klbot.c / klbalance.c / klnet.c of the other tracks are not in these two.)
THE PREFIX CLASH IS GONE: a second scratch copy of the WORKING TREE's sources with klmove.c (`klmv_`) AND track O's
klgrudge.c (`kly_`) both included and wired built TEST and SHIP without an error (that copy is deleted).
**No off-game rig was written: the logic is unproven beyond compiling.**

## 5. Level data - a proposal only (the bots tools are other tracks')

1. **Loot deadlines by role** (`kl_fa_bots_dyn`): the point man, the flankers and the rear guard wait the whole
   `TriggerLootDepleted` deadline at a cover hold while the two looters work - 30 - 50 s of standing each, the
   largest block of section 1. Proposal: the non-looting roles get 10 - 12 s there and go on to the NEXT hold on the
   way (covering the looters' way out), Late Night Opening's 45 s first.
2. **The escape boxes**: the box at the bank's drop was a fall-back for 'the AI does not take the link'; run H0
   showed the link is taken ('left From of hop 1 after 2.4 s by itself'). Proposal: build Withdrawal without
   `--drop`'s second box. The boxes beside the vans could become the board tactic's job (no box, the last place 3 m
   from the boarding object on the side away from the van's line) once `BoardNear=300` has shown the tactic takes all
   seven.
3. **Hot Coffee**: two bots stand 25 - 40 s 3 m from a hold at (7057..7141, 0, 22569..22660): look at that fork.

## 6. Live checks (the lead; scripted human + `[CrewHop] Dry=1 Log=2` place log; `[Bots] Enable=1 Log=1`)

| # | keys | map | PASS = these lines |
|---|---|---|---|
| M0 | `Restless=5 RestlessHold=15 WaitForYou=1 BoardNear=1500 MoveDry=1` | the bank (F03), idle human | `move: on; ...DRY RUN`, `wait: on`, `near: on`; `near: N ZAllyEscapeBox object(s) found in .. ms: ...; DRY RUN` with two boxes about (2210, 215, -320) and (-1706, 419, -899) (the build's notes) - **two boxes at those places = the scan and the class are right**; `wait: no vehicle WOULD be called before you`; any `move: ... WOULD ...`; no `is no ZOnlineMoneyCtrl` line (= the money list is where it was read); the round as without the keys. **The `.. ms` of the `near:` line is part of PASS: write the number down; over about 300 ms at GO is a hitch the owner will see - then BoardNear waits for a scan in the countdown.** Let the run go into a SECOND round: the `near: N ZAllyEscapeBox object(s) found` line must come again at its start with the same boxes |
| M1 | `Restless=5` | Late Night Opening one-stop `z_m02s1\M02` (the build with the shut watch cases, runs L11 / L12), idle | `move: record N ... stood 5.x s at (-1278, 500, 1884) ... from money object ... active 0 ...: FED UP`; the place log: that bot leaves the spot within 10 s; later `is a loot candidate again (its time is over)`; score page reached (the round-over restore: no fault at the state change). **And the crew's total loot at the end against L11 / L12b of the same build: not lower** (a soured object is sour for all) |
| M2 | `Restless=5` | each tab map, idle, 4 min | stood share by `stand.py` against section 1; count of `its order is given again`; nobody 'left until its chain orders another place' at a spot that is not a wall; **deaths and the crew's total loot against the I-series run of the same map (I1 .. I5): no more dead, no less loot** - an order cuts a running tactic, and a soured object is off for everybody; every `FED UP` line's object should read `active 0` or be one the place log shows nobody emptied |
| M3 | `Restless=5 RestlessHold=15` | the park, then Retomoto gates (G1's run), idle | `move: record N shifts round its hold`; deaths against I4 (seven of seven escaped) and G1 (nobody dead before GO+175 s): **if more die, RestlessHold stays 0** |
| W1 | `WaitForYou=1 WaitForYouHold=0` | the bank, idle human | `wait: no vehicle is called before you ... (rules +0x1ee = 1)`, `wait: record(s) .. stand ready at heist stage 3`, **no `van 1` in the crew log for 150 s**, then `wait: released (WaitForYouMax ...)` and a vehicle within a few seconds (= the trigger fires again for a bot standing in it). **LOOK AT THE CLOCK in the pictures: it is red from GO to the release (expected, section 2.2) and grey after - the owner must accept that or the key is dropped. DEATHS against I3 (the same map and human without the key: nobody died): the crew waits in the open at the van's stop; more dead = the key stays off** |
| W2 | `WaitForYou=1` | the bank, `PB_DM03_board_hp`'s script | `wait: released (you have reached heist stage 3)` and `van 1` in the same second **without the script stepping out of the box** - if the van does not come, the exit trigger fires on entry only: say so, the key then needs a call of its own |
| W3 | `WaitForYou=1 WaitForYouHold=15` | the park, the script stops 20 m short of the helicopter for 12 s | `wait: hold: ... timer 1.x -> 6.x s`, twice or three times, then `... the 15.0 s of WaitForYouHold are used`; he boards on that visit |
| N1 | `BoardNear=1500` | the bank, the script | `near: 2 ZAllyEscapeBox ... slot 25 wrapped`; `near: visit 1: the box at (-1706, 419, -899) is 42.x m ...: it takes nobody aboard`, `... the box at (2210, 215, -320) ... works as in stock`; `near: record N (stage 2) ... heist stage set to 3`; `follow:` / place lines: **no 'aboard' of a record farther than 15 m from the boarding place**; `near: visit 1 is over: the denied box ... was asked N time(s)` with N > 0. **THE COST, as three runs of the same script: N1a without BoardNear (the control: PB_DM03_board_hp had 2 aboard, 4 shot), N1b `BoardNear=1500`, N1c `BoardNear=1500 FollowOut=1 FollowOutHold=15` (and N1d with `FollowOutSpare=1` if N1c still loses them). The number to compare is in the line `near: visit N: the vehicle leaves WITH YOU ABOARD: K AI heister(s) still in play ..., M of them (*) stood at a denied box` and the `follow: ... LEFT BEHIND` / 'ONE STEP' deaths after it: PASS for the owner's tab = N1c shoots no more of the crew than N1a** |
| N2 | `BoardNear=300` | Hot Coffee, the script; the same three forms as N1 (control PB_DM01_board_hp: five shot as the van left) | every 'aboard' of a bot within 3 - 4 m of the boarding place; how many of seven board on visits 1 - 2; visit 3: `every box works again`; the departure line's K against the control |
| N3 | N1's keys | leave the level, load another (and the same one again), play | no fault at the unload (the box objects die with our vtable on them: same slots, same destructor); **the `near: N ZAllyEscapeBox object(s) found` line again at the first round of each load, with that level's boxes** |

Order: M0 first (it proves the three addresses the part rests on without writing anything), then M1, N1a-c, N2, then W1, W2.

## 7. Assumed, and not done

No longer an assumption: the exit trigger fires again for somebody still standing in it (read by the review, 2.2).

ASSUMED: a bot at stage 1 or more, not under fire, within 2 m of a candidate would be taking it if it could (the loot
tactic's rank over the chain's orders, re/bots_squad.md 4) - so a cover hold beside good money is not soured by a bot
that merely waits; M2's loot totals test it; a controller's update runs on the
game's main thread (the wrapper only reads a small table); 2 m is the right 'on the money square' (a counter can keep
a bot farther from a case's node); 3 m separates 'at its place' from 'stuck'; a shift of 3.5 m stays inside the room a
hold was chosen for; list one's pointers are the objects' bases (checked at run time by the vtable: a wrong guess
logs one line and the loot rule does nothing); `kle_bot`'s tests are enough for an order to a bot nobody chose
(they are what Escort and FollowOut use).

NOT DONE: a per-level side list of 'next places' (the chain's own place and the human were enough for the rule as
built); reading the squad's current node; the BOARDS triggers' sizes per map; an off-game rig; `WaitForYou` for a
multiplayer session; a money condition for the wait; anything in `klescort.c`.

KNOWN INTERPLAY: `Restless` skips this round's escort and every stage-3 bot while a vehicle is called (FollowOut /
BoardAll own those); with `WaitForYou` a bot at stage 3 waits at its last place - inside the escape box - and is
left alone there; `WaitForYou` + `FollowOut`: his stage 3 releases the call and calls the crew in the same pass.
A soured object is sour for every AI heister: with `Restless=5` a bot waiting on a case its squad's relay has not
opened yet sours it, and the opening itself re-arms it.

## 8. The review's points (`re/bots_move_review.md`) and what was done

| point | done |
|---|---|
| M1 prefix clash with klgrudge.c | every name of klmove.c is `klmv_` / `KLMV_` now; the working tree's sources with both parts wired build TEST and SHIP |
| M2 `[rules+0x1ee]` is also the HUD clock's colour | text corrected in klmove.c 2 and here 2.2, in the `wait: on` line and the ini; W1 looks at the clock. No other data-only handle was found: the red clock is the key's price |
| M3 BoardNear's cost | written in klmove.c 3 h, here 3, the ini and the `near: on` line (it names FollowOutHold / FollowOutSpare and says when neither is on); a line at every departure counts who is left in play and who stood at a denied box; N1 / N2 are pairs against a control |
| S1 no under-fire test in (b) | a bot hit in the last 4 s gets no order of (b) or (c) |
| S2 the anchor is lost, endless orders | the anchor stays while the defend block holds what the hook put there; a plain order-again hands the block back after 10 s WITHOUT a new count; six orders at most for one place of the chain; a bot sent beside the human stays there |
| S3 the loot rule judges bots that are not looting | stage 1 or more, not hit in 4 s, no grab running (record `+0x15`). The 'busy looting' bit 0x2000 cannot be asked as a requirement: in the trap it is never set (the trigger does not fire). NOT changed: no test 'not at its own place' - the trapped bots of L11 stand at their loot station; M1 / M2 compare loot totals instead |
| S4 a deactivated object re-armed | the state byte `+0x64` is remembered at souring; changed = nothing written, one line |
| S5 the escort | `kle_r.used[i]` is skipped in the stage write |
| S6 scan once per rules address | the scan runs at every round's start |
| S7 the hitch | not measured (offline); the line prints the ms at every scan and M0's PASS holds the number |
| S8 state 5 | the denial is decided while the vehicle stands and kept through state 5; nothing is denied in states 0 - 2 |
| S9 WaitForYou parks the crew in the open | written into the key's text; W1 counts deaths against I3 |
| S10 sours forgotten on one failed read | the marks are kept; the round's book and the gate survive 3 s without a session; marks still on at a new round are put back if the object is still listed with its state, else dropped |

## 9. BoardReach: a bot goes aboard only where a human can (track N4, 2026-10-11 evening; NOT RUN IN THE GAME)

Owner, after rounds with `BoardNear=1500 FollowOutHold=25 FollowOutSpare=1` (hook ship_w8): 'saw a bot get in the car
and he was like 30 metres away like even i couldnt get in that point they need to be just as close but some do and
they sprint for the van'.

### 9.1 Read in kl2.exe

| what | where | says |
|---|---|---|
| the box's update | 0x907a50, whole (164 bytes) | Arcade (0x7f6850), rules = 0x508ef0 (`[[0x168e9e4]+0x54]`); a box whose node has flag 0x20000000 refreshes its place at `+0x4c` (0x7b3020); then ONE LOOP over all crew records (count = rules vtable +0x50, asked every time round; record = `[rules+0x348] + 0x7c * i`, 0x7fd930): AI bit `+0x79 & 1`, actor `+4`, status `+0x10 == 0`, inside (0x758cb0) -> 0x74d7f0(i). **Everybody inside goes aboard in the one call: there is no per-record hook point** |
| inside | 0x758cb0, whole | the actor's node origin through the box node's world-to-local (0x873dd0), then the box ENTITY's vtable +0x170 with margin 0.0; if not, a second point (the actor node's floats +0x30 / +0x34 / +0x38) the same way |
| the box test | ZBoxPrimitive vtable 0xb9f424 slot 92 = 0x4aca80, whole | `abs(local[k]) <= [entity + 0x14 + 4k] (+ margin)`: the three size values are **HALF extents** |
| aboard | 0x74d7f0, whole | rules vtable +0xb4 (0x6840a0) with the record's actor and 0 |
| the boarding rule | 0x6840a0, whole (again) | session state 0x19; vehicle state 3 / 4, or 5 while `[tuning+0x630] - timer < 1.0`; actor branch 0x6841fd: record by 0x78f470, status 0 -> 4, score flag 0x20 (0x47cf50), 0x89c890(actor), `[actor+0x8f0] = 1`, the announcement 0x69d4d0, and the wait timer 0 when nobody is left in play. No distance, no stage |
| where a HUMAN boards | `PlayerAction` 'EnterVehicle' (UA_FA_ESCAPE) on the box node the vehicle controller names = `[rules+0x1e0]`; registration 0x4c4de0 | the action's entry is made by 0x7be580 with radius **-1.0** (0xb3e980): no radius, the zone is the box entity itself (live run ESC3 / re/playtest.md: 'E inside the boarding box'). NOT READ: what the 50.0 (0xbaf9e0) and the two tuning floats `+0x320 / +0x324` of the entry do, and the player-side test itself |

### 9.2 The boxes of the six maps (builds `p_tab\DM01..DM09`, `q_vault\DM03A`; scratch scripts `n4\boxes.py`, `reach.py`, `poly.py`)

Every `AllyEscapeBox` is a `ZBoxPrimitive` with half extents **350 x 416 x 350**, not turned (local x = world x): it
reaches 4.95 m from its middle in the plan. Distances are in the plan, to the middle of the human's boarding box at
the vehicle's stop (`bots.json` plan `van.board`; the park: the node).

| map | escape box, middle | human's boarding box (half extents) at | box middle / nearest / FARTHEST corner from it | mesh under the boarding box | crew's box on the boarding box's own polygon |
|---|---|---|---|---|---|
| Hot Coffee (F01) | (6004, 200, 20211) | van doors 95 x 135 x 80 at (6164, 0, 20691) | 5.1 / 2.3 / **9.7 m** | yes, the crew's part | 149 of 324 grid points |
| Late Night Opening (F02) | (-821, 200, -8400) | van doors at (-621, 0, -8719) | 3.8 / 1.5 / **8.7 m** | yes | 262 of 324 |
| Withdrawal (F03) | (2210, 216, -320) | van doors at (2970, 0, 39) | 8.4 / 4.1 / **13.2 m** | yes, part 3 (the street) | 6 of 229 |
| Withdrawal, the drop | (-1707, 420, -900) | the same | 47.7 / 43.7 / **51.9 m** | another mesh part (the yard): only the drop link joins them | 0 |
| A Walk in the Park (F04) | (-1687, 420, -6542) | helicopter pad **400 x 200 x 300**, turned 20 degrees, at (-1687, 133, -6542) | 0 / - / 4.95 m = inside or within 1 m of the human's own box | yes | 83 of 251 |
| Retomoto Tower (F06) | (2430, 19801, 510) = **in the tower**, beside the tower car (kl_fa_bots_rt's fall-back when the join is off) | van 01's doors at the street stop | 198 m below it and about 90 m off in the plan: nobody in it is ever near the van | yes (the street part); the box is on the tower's part | - |
| The Vault (F07) | (316, 900, -11071) | van doors at (636, 700, -11230) | 3.6 / 1.9 / **8.4 m** | yes | 324 of 324 |

The human: on the five van maps he must be INSIDE the 1.9 x 1.6 m box at the rear doors (`V_Van_00\BoardingTrigger`,
3.37 m behind the van's middle) = at most 1.24 m from its middle. The BOARDS trigger `BoardingCar` of the van is a
10 x 10 x 10 box at the origin there: it is fired by the action, nobody stands in it. On the park the action box is the
pad itself and a second box (`Triggers!BoardingGameplayTrigger`, 343 x 400 x 297) is the BOARDS trigger.

So with `BoardNear=1500` (the test is on the box's CENTRE: 4.9 m on the bank) a bot is 'aboard' as soon as it crosses
the near box's edge: up to **13.2 m from the doors on the bank**, 8.4 - 9.7 m on the other van maps - six to ten times
the human's distance.

### 9.3 The owner's bank round, 20:33 - 20:38 (KLHook.log)

| time | line | reading |
|---|---|---|
| 20:36:17.3 | `follow: record 7 (stage 3, $370000) at (-924, 143, -347), 10.4 m from the boarding place` | the 'boarding place' of that line rides on the van, still driving in; from the doors at the stop he is **39 m** away |
| 20:36:21.8 | `the vehicle waits: ... nearest 18.4 m` | record 7, about 23 m from the doors |
| 20:36:25.4 | `bots: record 7 (bot): aboard` | 3.6 s later. The near box's west edge is x 1860 = 11.1 .. 11.8 m from the doors, 12 - 13 m of running from where he was: **he vanished at the box's edge, 11 - 13 m from the doors** (the far box was denied: 'asked 2752 time(s)'). No place line exists for the moment itself |
| 20:37:28.2 -> 29.6 / 31.5 / 32.7 | `nearest 10.7 m`, then records 3, 4, 5 aboard | the same box, the same edge, in a row |

No line of that round puts a bot 30 m off at the moment it boards; what the game allowed was 13.2 m at most (the box)
- and the owner had seen record 7 some 39 m off eight seconds before. 'Some do sprint for the van' = the stage-3 bots
on their board tactic / FollowOut's order; they too vanish at the box's edge on the way.

### 9.4 The key (`klhook/klmove.c` section 4)

`[Bots] BoardReach=<units>` (100 = 1 m; 0 = off; least 50): while the vehicle stands (states 3 / 4, kept through 5)
the private slot 25 **does the box's update itself** - the calls of 9.1 with the same arguments in the same order, in
the place of the stock call - and leaves out `0x74d7f0` for a record whose actor's node is farther than BoardReach
from the human's BOARDING BOX (distance to the box's SURFACE, 0 inside it; `[rules+0x1e0]`'s node frame and its half
extents; an object that is no ZBoxPrimitive counts as a point, one line says so). Nothing is written to hide a bot.
Why not 'call the stock update and hide the far ones': that needs a write into each far record (the AI bit or the
status) for the length of the call, and 0x6840a0's 'nobody left in play' count walks the same records.
Guards: the 164 bytes of 0x907a50 and the first 16 of 0x758cb0, 0x74d7f0, 0x7b3020, 0x7f6850, 0x508ef0, 0x4aca80
and of the rule 0x6840a0 (which must also be what the rules vtable holds at +0xb4) are compared first ('reach: ...
is not the one this build knows: BoardReach does nothing' - then no line of the part follows, in a dry run
neither); a record of another rules object than the tick's, or a bot whose place cannot be read, is handled as stock.

**WHEN the private update acts (fix round, review M1).** The first form was switched on by the tick (every 250 ms)
once it saw state 3: until then the stock update ran and took everybody who ALREADY stood in the escape box - the
usual case on Hot Coffee, Late Night Opening and The Vault, at every visit. Now the update is armed through the
whole round (on a level that is not stock, from the round's first tick) and reads in ITS OWN frame: the vehicle's
state `[rules+0x1dc]` (0 / 1 / 2 / 6 / 7: the stock update, the rule takes nobody), in 3 / 4 the boarding box
(`klmv_frame`, reads only; unreadable = the stock update, one line by the tick), in 5 the box it kept from the wait.
The tick hands it single words only (the rules object, the reach, 'as stock from this visit on'); the kept box is
the update's own, under a sequence count (S7). What is left of the hole: a tick pass that cannot read the session
disarms the update until the next pass that can (as BoardNear).

- `BoardReachDoors=1` (default): the same update also takes a CALLED bot (heist stage 3) that is within BoardReach
  - **and never more than 3 m, whatever the key (S3)** - of the boarding box and outside the escape box being
  updated; every wrapped box does it (S4; the rule sets status 4 at once, nobody is taken twice). Reason: the escape
  boxes stand beside the doors, not on them (nearest corner 1.5 - 4.1 m off), and the board tactic's test 0x4faf60
  asks 'a path of more than one node' - four maps park the crew on the boarding object's own mesh polygon (table
  above; that a node is a polygon is a GUESS). A level with NO escape box has no doors path (one line says so).
- `BoardReachOrder=1` (default): a called bot that stands a second, more than BoardReach and less than 30 m from the
  boarding box, gets ONE order a visit to the boarding object's place (the tactic's own goal; `kle_order2`, the
  soldier's own routine 0x760e50). Not a traitor (`kle_bot`), not an escort klescort.c still holds.
- a bot under stage 3 in a box beyond the reach gets stage 3 (`BoardNearStage=1`, the same code as for a denied box).
- `BoardReachVisits=N`: from visit N on the boxes work as in stock (**default 3**, as `BoardNearVisits`; 0 = never),
  and **the round's last vehicle (`[rules+0xe8a]`) always works as in stock** (S2): nobody is stranded for the
  whole round. What the owner sees with the default: a bot nothing can walk to the doors stands in the box for two
  visits and vanishes from 4 - 13 m at the third.
- `MoveDry=1`: nothing wrapped; the `reach:` lines say who would not be taken (this file's own inside test).
- **Refused and moved by nothing of this file (S5)** - stock's box took all three: a TRAITOR (no order by design,
  no stage write), a bot at heist STAGE 0 (`klmv_stage3` asks stage >= 1, BoardAll's rule), a bot MORE THAN 30 m
  from the boarding box (no order). The refused line says which; they board by their own tactics, or from visit
  `BoardReachVisits` on / at the last vehicle.
- **A police human (S8 c):** the key acts then too (FollowOut and its hold do not): the crew has to reach the doors
  in the vehicle's own 8 s a visit, with nobody holding it; from visit 3 the boxes work again.

**`BoardNear` is not needed with it** (leave it 0): the bank's box at the drop and Retomoto's in the tower take nobody
within any reach, the near boxes only who stands at the doors. Both set: a box BoardNear denies takes nobody.

**Proposed for the owner: `BoardReach=100 BoardNear=0`**, with his `FollowOutHold=25 FollowOutSpare=1` (S1). The
human must stand INSIDE the 1.9 x 1.6 m box (at most 1.65 m from its middle, at a corner); BoardReach is measured
from the box's SURFACE and from any side, so 100 lets a bot go aboard up to 1 m outside it (about 2.65 m from the
middle at a corner, also beside the van's flank), 200 up to 3.65 m. Neither is literally 'just as close'; 50 is the
least the code takes. BUT the game's own board tactic takes a WALKING stage-3 bot within 3 m of the box's node
(0x82fa35) whatever the key says - the key cannot make that shorter; it only decides for a bot that stands in an
escape box or at the doors without a running tactic. If seven do not get aboard at 100 (R1), try 200. On the park
the crew's box lies on the pad itself: nothing changes there.

**The lead's question on `BoardNear=300`** (in the owner's ini for his next start: no box works). Can the board
tactic alone take the crew? The mesh is under the boarding box on all six maps, on the part the crew's last places
are on - EXCEPT a bot in the bank's yard (the drop link must carry it; live run H0 saw it taken) and one left in
Retomoto's tower (the join carries it). THE RISK is the tactic's 'more than one node': on Hot Coffee, Late Night
Opening, The Vault and the park the crew waits on the boarding object's own polygon, 3.6 - 5.1 m from the doors, and
may stand there until visit 3 (`BoardNearVisits=3`: every box works again, so nobody is stranded for good - but the
owner would see them wait two visits and then vanish from 4 - 10 m). NOT KNOWN from a run: no round with no box has
been played. `BoardReach` is the answer to both; until it has run, `BoardNear=1500` is the safer of the two.

### 9.5 Builds, wiring

No new file, no new wiring line (klmove.c is wired at HEAD: `#include "klmove.c"`, `klmv_init();`,
`klmv_tick(game_thread);`). Compile check from `git archive HEAD klhook` + this klmove.c in `G:\kl_scratch\N4\src2`
(fix round): TEST and SHIP build. A build carries its build time: the sha1 of a rebuild differs, the sha1s in the
track's report are of those two files only (`G:\kl_scratch\N4\test2`, `ship2`).

### 9.6 Live checks (the lead; `[Bots] Enable=1 Log=1 MoveLog=2 FollowOut=1 FollowOutHold=25 FollowOutSpare=1`)

| # | keys | map | PASS = these lines |
|---|---|---|---|
| R0 | `BoardReach=100 MoveDry=1` | the bank, the board script (`PB_DM03_board_hp`) | `reach: on; BoardReach=100 ... DRY RUN`; `near: 2 ZAllyEscapeBox object(s) found ...; DRY RUN: nothing is wrapped`; **no** `reach: ... is not the one this build knows`; at the first wait `reach: visit 1: the vehicle's boarding box (where YOU get in) is 95 x 135 x 80 (half extents) round (about 2970, 121, 40)` - **those three numbers and that place = the frame and the extents are read right** ('is not a box this file knows' = FAIL, say so); `reach: visit 1: record N ... stands in an escape box 4 .. 13 m from the boarding box ...: the box WOULD not take it`; the round as without the key |
| R1 | `BoardReach=100` | the bank, the same script | the scan line ends `(BoardReach: a box takes an AI heister aboard only when THAT BOT is within reach ...)`; the boarding-box line as R0; for every bot that comes: `reach: ... stands in an escape box N m ...: the box does not take it`, then EITHER nothing (its tactic walks it) OR `reach: ... sent to the doors`, then `reach: record N (stage 3) is taken aboard AT THE DOORS: it stood X m from the boarding box` with **X <= 1.0** (the place is up to 0.25 s old: a runner can read a little more), or a plain `bots: record N (bot): aboard` whose last `follow:` / place line is within 3 m of the doors; `reach: visit 1 is over: ... the doors K time(s); M time(s) a box was asked ...` with M > 0. **M1's check: in the FIRST SECOND of every wait (from klbot's vehicle-state 3 line) no `bots: record N (bot): aboard` of a bot whose `reach: ... stands in an escape box ... does not take it` line follows or whose last place was more than 3 m from the doors - a bot that stood in the box at the arrival must get the refused line, not 'aboard'.** **PASS for the owner = no 'aboard' of a bot more than 3 m from the doors, and of the seven as many aboard as in N3c (seven) within the 25 s hold.** Pictures every 2 s at the van: the bots run to the rear doors |
| R2 | `BoardReach=100 BoardReachOrder=0` | Late Night Opening or The Vault (the crew parks on the doors' polygon), the script | does the tactic alone move them? `stands in an escape box` lines and then 'aboard' WITHOUT a `sent to the doors` line = the 'one node' guess is wrong and the order is not needed; bots that stand the whole visit = it is right (then R2b with the default `BoardReachOrder=1` must bring them to `AT THE DOORS`) |
| R3 | `BoardReach=100` | the park, the script | the boarding-box line reads `400 x 200 x 300`; the crew boards as in I4 (seven of seven), mostly `an escape box took an AI heister within reach` > 0 |
| R4 | `BoardReach=100` | Retomoto (gates build), the script through the join | one box found at (2430, 19801, 510); nobody is taken by it; on the street every 'aboard' is `AT THE DOORS` or the tactic's. The doors path is run by that ONE box in the tower: if no `AT THE DOORS` line ever comes on Retomoto while bots stand at the doors, its controller is not updated with the crew in the street (not known) - then only the tactic boards there (S4) |
| R6 | none (stock boarding; the rig) | the bank, the scripted human walked toward the rear doors in 10-unit steps from 3 m out along the van's axis and from the side, `[Bots] Log=2` | where the 'get in' prompt first shows / E first boards against the box line of R0 (95 x 135 x 80 round its middle): inside the box only = the human's zone is the box; earlier = what the action's 50.0 / tuning +0x320 / +0x324 add (S6: NOT READ; this measurement settles it and BoardReach's proposed value with it) |
| R5 | R1's keys | leave the level in the middle of a wait, load another | no fault (the update of the next level's boxes runs as stock until its own first wait) |

Order: R0, R1, R2, then R3 / R4. FAIL of R1 on 'as many aboard' = look at who stood where in the `near: visit N: the
vehicle leaves ...` line, then try `BoardReach=200` (the tactic's own 3 m) before giving the key up.
With the default `BoardReachVisits=3` every scripted check must look at visits 1 and 2: from visit 3 the line is
`reach: visit 3: BoardReachVisits: from this visit on: every escape box works as in stock`.

### 9.7 Assumed, and not done

ASSUMED: `[rules+0x1e0]` is the box entity with the `PlayerAction` (the vtable +0x170 test at run time says if not);
the human's zone is that box and no more (the action entry's 50.0 was not read: it may add 0.5 m; live check R6
measures it); a box controller's update runs on the thread the tick runs on (not needed any more for the boarding
box: the update keeps its own copy under a sequence count, the tick hands it single words, the bits are
interlocked); `[rules+0xe8a]` is set while the round's last vehicle stands (BoardNear relies on the same); the
board tactic's goal can be walked to as a defend order (the van's body stands beside it, 3.37 m off);
an order to a called bot whose board tactic IS running only restarts that walk (what Restless (b) relies on).
FIX ROUND (review `re/bots_board_reach_review.md`): M1 the update armed for the whole round and reading the state
itself; S1 proposal 100 and what it means; S2 default `BoardReachVisits=3` + the last vehicle; S3 the doors path
capped at 3 m; S4 every wrapped box does the doors pass; S5 the refused line says who is moved by nothing; S7 the
sequence count; S8 a / b / c / d. S6 is NOT done offline (R6).
NOT DONE: the player-side test of the action read to the end; a run; anything in klescort.c (its `follow:` lines still
measure to the rules' place 5 m beside the doors); the bots builds' own boxes moved onto the doors (level data, the
bots tools are other tracks'); online (the Arcade gate 0x7f6850 is the stock update's own).

## 8. v82f (2026-10-17): Restless gave the Hunted step back as if it were the chain's place (HELI3, record 4; built, NOT RUN)
- Log L1017_HELI3.log: record 4 (stage 1, $255000 from 17:28:33) is at 17:28:28.618 'fedkit: hunted: record 4 is ordered TOWARDS YOU (-1675, 460, -542)' (HuntedFire: a straight step at the human, who stood at (1400, 20, -2760) on another floor), then 17:28:39.931 and 17:28:47.929 'move: record 4 ... its order is given again ... (-1675, 460, -542)' (bot at (-1617, 460, 200), then (-1752, 460, 200): 8.3 m, 7.0 m away, same z, no progress). So the point is neither loot, route nor escape: it is klfedkit.c's step, adopted by klmove.c (b. 'stuck off its place') as the chain's anchor because the block held a place klmove had not put there.
- Only 2 re-issues are in the log (not 'the rest of the round'); the round ended at 17:28:51.9. Each new hunt step (66 in the round) started a fresh count (anchor0 moved), so the 4 / 6 caps never bit.
- Escape: the bot never reached it because that needs heist stage 3 (the exit trigger); van stayed 0 all round. Not a klmove fault.
- Change (klmove.c / klfedkit.c): klfk_hunted tells klmv_foreign(rec, got) what it ordered; klmove.c does not take a block value within 50 of that for the chain's place (anchor and counts stay, one log line per bot). New guard: KLMV_SAME = 3 orders in a row to the same target (within 50) with the bot not 200 nearer (KLMV_PROGRESS, GUESS) -> total = KLMV_TOTAL, log 'DROPPED' once per bot; the bot is left to its chain / the game as at 6 orders before.
- GUESS: that the game's chain then moves the bot on (the old cap behaved so, unproven); that 200 units is a fair progress step; that walking back to the chain's place after a hunt step is what the owner wants. Builds hud_v82f_test / hud_v82f_ship.
