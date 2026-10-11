# The crew that is left behind: what kills it, and 'the crew follows you out' (`[Bots] FollowOut`)

2026-10-11, track J. **OFFLINE: the game was not started, nothing was written into a game folder, nothing committed.**
Files changed: `klhook/klescort.c` (section 3 of its top comment + the code), `klhook/KLHook.ini` (the sample's
`[Bots]` lines), this file. Scratch: `G:\kl_scratch\j\` (the source snapshot, builds, the rig).

**Reviewed** (`re\bots_follow_out_review.md`: ACCEPT WITH FIXES - one MUST, seven SHOULD, nine notes). Every one of
them was read again in the exe and is applied; none was refuted, one was applied in a stricter form than proposed.
Section 10 lists them with what changed. This file, the sample ini and the comment of `klescort.c` describe the code
as it is AFTER those fixes.

Words: **EXE** = read in kl2.exe build 0490 for this file (`debug\dasm.py`; addresses are given so that anybody can
read it again); **LIVE** = seen in a log of a run in the game (the lead's); **RIG** = this file's code run against a
made-up round off the game (section 6); **ASSUMED / GUESS**; **not run**.

## 0. Short answers

1. **The game shoots them itself, on purpose.** `ZGameRulesHeist` - the Arcade rules class, and only it - has a
   schedule for it: when the escape vehicle starts to drive out (state 5) **with the human aboard**, every crew
   record slot gets a time, about one a second over the next 8 s, in a shuffled order; and the rules' own update
   then, slot by slot, deals **1,000,000 damage** to the AI heister in that slot if he is neither aboard nor dead
   nor escaped, and books him as dead. No distance, no heist stage, no traitor test. Slot 194 = 0x8fa6d0 at
   0x8fab77..0x8fac9a makes the schedule, slot 7 = 0x74b6d0 at 0x74b8a2..0x74b99a carries it out. Section 1.
2. **It is stock, and it is Arcade's own.** No level field feeds it, the hook patches no code, and the multiplayer
   classes have no such loop. With the human NOT aboard nothing of it runs - which is why no idle-human run ever
   showed it.
3. **The KILL costs the human nothing but the sight.** His round is over anyway (he escapes when state 5 ends, the
   round ends 3 s later); no life depends on it, and for the payout a bot that was shot and a bot left in play are
   the same - both are outside the pool the escaped share (1.4). What it does is put up to seven 'killed' lines and
   bodies into the last 8 s of every round the human wins while crew is still out. That is very likely a good part
   of the owner's 'dropping like flies'. (Getting more bots ABOARD does touch his cut: 2.5.)
4. **Built: `[Bots] FollowOut=1`** (default 0). Signal = the human's own crew record has heist stage 3 (he stood in the
   exit trigger, which calls the vehicle). Then every AI heister in play that is no traitor gets heist stage 3 (one
   byte - the game's loot tactic lets go while the vehicle waits, its board tactic runs to the vehicle) and, while
   the vehicle drives in and is 2 s or more away, one order to the boarding place (the call the escort's release
   makes). Section 2.
5. **That alone will not save the bank's crew, and the numbers say so now:** from the human's stage 3 to the
   departure there are 7.2 s (drive in) + 8 s (wait) = 15 s; the four killed in the control stood 55 .. 75 m from the
   van as the crow flies (about 100 m by the way the human walked), and a bot walks about 3 m/s (GUESS from run E3).
   Two more keys, each a data write and each off by default: **`FollowOutHold=N`** - the driver waits up to N s more
   while the human sits aboard and called crew still comes nearer (the float and the 5 s of the game's own 'hold the
   driver' rule, slot 152); **`FollowOutSpare=1`** - whoever is still out when the vehicle drives out is not shot (the
   schedule's times are put off). Sections 3 and 4.
6. **Two prices the owner must know** (2.5): every bot `FollowOut` / `FollowOutHold` gets aboard joins the split of
   the escaped crew's money, and a called bot can turn traitor where a bot inside could not.
7. **Tried off the game only**: SHIP and TEST compile without a warning from this file; the scratch rig runs the
   code against a made-up round, 58 checks, 0 failed, and the reviewer's own five cases pass unchanged (section 6).
   **Nothing of it has run in the game.** The live checks, in order, with the lines that mean PASS and FAIL: section 8.

## 1. What kills them (EXE)

### 1.1 The control (LIVE, run `PB_DM03_board_hp`, `<work>\build\klhook\live\PB_DM03_board_hp.log`)

| time | what |
|---|---|
| 10:15:17.5 | human: heist stage 2 -> 3 (the exit box); vehicle state 1 (7.2 s to drive in) |
| 10:15:24.7 | vehicle state 3, timer 8.0 s |
| 10:15:27.8 | `record 0 (you): aboard` |
| 10:15:30.7 | record 1 (the escort, stage 3) aboard |
| ~10:15:32.7 | vehicle state 5, timer 8.4 s (`van 3 0.3s` at :32.385, `van 5 7.6s` at :33.481) |
| 10:15:33.8 | record 4 aboard, **1.1 s into state 5**, at stage 2 (the boarding rule's window, 1.6) |
| 10:15:35.6 / 36.6 / 38.2 / 40.7 | records 3, 6, 2, 5: `lost 252.0 (0.0 of 252.0) ... ONE STEP - DOWN`, all at stage 1 inside the bank |
| 10:15:41.1 | records 0, 1, 4: `status6` (escaped); vehicle state 8 |
| 10:15:44.1 | session state 0x19 -> 0x1f |

The four deaths are 2.9, 4.0, 5.5 and 8.0 s after the change to state 5. Section 1.3 says where those numbers come
from. (The first version of this file put the change at :32.9 and the drive-out at 8.0 s; the review's replay is
right: the wait's timer reads 0.3 s at :32.385, and state 5 lasts 8.4 s.)

A second run with a boarding human, which the first version did not use (LIVE, `PB_DM01_board_hp`, Hot Coffee, 10:58):
human aboard 10:58:07.8, `van 5 8.4s` at :15.103, five of the six bots in play lose 252.0 in one step at :16.6, :18.6,
:20.5, :21.9, :22.4, **record 2 is never shot**, the human's `status6` at :23.525, then klbot's line reads `van 7`
with record 2 still `in-play`, and `session: state 0x19 -> 0x1f` at :26.523 = 3.0 s after the escape. That is 1.3's last point seen live: stock ends a
round with one AI heister still in play.

### 1.2 The schedule: `ZGameRulesHeist` slot 194 = 0x8fa6d0 (the vehicle's state is set), case 5

The jump table at 0x8fb078 sends state 5 to 0x8faac5. After the vehicle's message and the timer (`[rules+0x1f8]` once
if it is not 0; else the vehicle's own field 16, `[controller+0x74]`, 0x8fab3e; else `[tuning+0x630]` without an
`OnlineEscAnimatedVehicle` - on the F07 van these maps use the timer starts at 8.4 s):

```
8fab6a  mov ecx, [esi+0x5f8]            ; the score object
8fab77  test byte [ecx+0x1d4], 0x20     ; client 0's flags: 0x20 = ABOARD (set by the boarding rule, 0x684157)
8fab7e  je  0x8faca2                    ; the human is not aboard: no schedule
        base = [sysif+0x48] + 0x400 + 1024 * 0.3 * rand01         ; now + 1.0 .. 1.3 s (the clock counts 1/1024 s)
        step = 8.0 / [rules+0x354]                                ; 8 record slots in Arcade: 1.0 s
8fabfd  for k in 0 .. slots-1:
            [rules+0xf1c + k]   = k                               ; a byte per slot
            [rules+0xeec + 4*k] = base + 1024 * step * (k + 0.7 * (2 * rand01 - 1))
8fac9a  call 0x7f87c0 (&[rules+0xf1c], &[rules+0xf1c + slots])    ; shuffle: byte swaps by MSVCR rand
```

Constants: 0xb172d8 = 0.3, 0xb39f70 = -1024.0, 0xb19588 = 8.0, 0xb62258 = 2.0, 0xb18cc0 = 0.7, 0xb59200 = 1/32768;
the random numbers are the game's own generator at `[sysif+0xb30]` (0x41aa70). So slot k is due between
`k + 0.3` and `k + 2.0` seconds after the change, and which crew record a slot names is a fresh shuffle each time.
The step is 8 s over the number of slots whatever the vehicle's own drive-out time is.

The table's shapes, which `FollowOutSpare`'s test goes by (section 4): the constructor 0x835480 zeroes the twelve
times (0x8355db..0x83561d) and **writes nothing at +0xf1c** - until the first schedule the slot bytes are whatever
the heap held (every instruction of .text with the displacement 0xf1c: 0x74b910, 0x8fabfd, 0x8fac8b, 0x8fac93, none
in the constructor). After a schedule the bytes are a shuffle of 0..slots-1.

### 1.3 The loop: `ZGameRulesHeist` slot 7 = 0x74b6d0 (the rules' update), every frame of a round

```
74b8a2  mov ecx, [esi+0x5f8]
74b8a8  test byte [ecx+0x1d4], 0x20     ; the human is aboard
74b8ae  je  out
74b8b4  cmp byte [esi+0x1dc], 5         ; the vehicle drives out
74b8bb  jne out
        a damage record on the stack: attacker 0, ..., amount = float [0xb631b0] = 1000000.0
74b910  for k in 0 .. slots-1:
            i = byte [rules+0xf1c + k]                     ; the record this slot names
74b91e      i >= [rules+0x354]                             ; a byte out of range: next (no fault)
            record i in use ([rules+0x34c][i] == 0)        else next
            test byte [record+0x79], 1                     ; an AI member                    else next
74b951      test byte [score+0x1d4 + 4*i], 0x64            ; 4 dead, 0x20 aboard, 0x40 escaped: next
74b95b      [rules+0xeec + 4*k] > [sysif+0x48]             ; signed (jg): its time has not come: next
74b96d      actor->vtable[0x694](&damage)                  ; ZFFActor 0x69f900: the actor's damage entry
74b98e      rules->vtable[0x40](actor, 0)                  ; slot 16 = 0x485740, the bot kill rule, killer 0
```

- **Whom**: every AI record that is in use and not dead / aboard / escaped. Not the human (mask 1), nobody by
  distance, nobody by stage; a traitor too.
- **How**: the actor's own damage entry with an amount of 1,000,000 - the 'ONE STEP' of the health log, 252.0 of
  252.0 - and then the rules' kill rule for an AI member, slot 16 (0x485740): the record is found by the actor
  (0x78f470), slot 71 (0x4b4850) with amount 0 takes the money it carried out of its record (the log: `$465000` ->
  `$0`; whether it is dropped as a pickup was not read), the kill text (0x704a10), client flag 4 (dead), record
  `+0x70` = 5.0, **status 7**. With killer 0 the routine credits nobody (0x485821 `test ebp, ebp / je end`).
- **When**: a slot whose time has come is taken in the next frame, and stays 'due' for as long as the state is 5:
  a bot that is still in play when its slot comes dies then, wherever it is. The only way out is to be aboard.
- **The timing of the control**: slots are due at `k + 0.3 .. k + 2.0` s; the four deaths at 2.9 / 4.0 / 5.5 / 8.0
  s fit slots 1 or 2, 2 or 3, 4 or 5, and 6 or 7 - four different slots; the other four held the human, the two
  aboard and the bot that had died earlier. It is one countdown table for the round object, not a countdown per record.
- A slot due after the end of state 5 is never taken: with a drive-out of 8.4 .. 8.5 s slot 7 (7.3 .. 9.0 s)
  misses in about three rounds of ten (worked out: its time is past 8.45 s with probability 0.29), when it names an
  AI heister in play. **So stock, too, sometimes ends a round with one AI heister still in play** - seen live in
  `PB_DM01_board_hp` (1.1).

### 1.4 After it

State 5 ends when its timer is 0 (slot 195 = 0x55ec70, jump table 0x55ee78, case 5 at 0x55eda0): `call 0x805120` -
every record with status 4 becomes 5 and then 6 (escaped), client flag 0x40 on and 0x20 off, a per-record word
at `[score+0x270+2*i]` grows by the word at 0xd1b3e0 or, for a traitor, 0xd1b3e4 (7 and 15 in the file; what it
counts was not read); 0x67f480 ('is the round over?': yes once client 0 has escaped) -> slot 193 with 3.0 s
(0xb4a174) and the round ends (`re\fed_respawn.md` 2.1). Then 0x4906b0 counts records in play: more than 0 ->
vehicle state 7, else 8. (The review adds: 0x805120 also works out 'client 0 aboard and everybody else dead or
escaped' and hands it to 0x6f8520, which needs session kind 3 - nothing in Arcade hangs on it.)

**No life of the human depends on the crew's deaths** (`dec [score+0x6c]` only when the human has not escaped,
0x5dfffd; `re\leaderboard.md`), and the crew records are cleared at the next round start (0x817d20). The Steam side
(stats, the 'single escape' achievement that the log shows blocked at 10:15:41) is blocked on these levels anyway.

**The payout** (EXE; corrected after the review - the first version said 'his money is his own record's', which is
wrong). The round's end (slot 192 = 0x5dff40 -> 0x70b920) does two things to the money:

```
70b920  for every record in use:  status 6 (escaped): [record+0x38] += its money
                                  else:               its money = 0                 ; dead OR still in play
796410  pool = 0, count = 0
        for every record in use whose client flags have 0x40 (escaped) and none of 0x0d (1 traitor, 4 dead, 8 ?):
            pool += its money;  count++
        share = pool * f / count                    ; f = 0x7360a0 = `fld1 / ret` = 1.0
        for every record in use:  [record+0x28] = 0;  [record+0x2c] = [score+0x184 + 4*i]
            escaped and a traitor:      [record+0x2c] += its own money
            escaped and no traitor:     [record+0x28] += share;  [record+0x2c] += (1 - f) * its own money + share
            client flags 8 or 0x80:     [record+0x28] = its own money;  [record+0x2c] += its own money
```

So every escaped non-traitor gets **the same share: what the escaped non-traitors carried together, over their
number.** For the control, if the human has neither of the two exception flags: (550,000 + 40,000 + 415,000) / 3 =
335,000 each. A bot that was shot and a bot left in play are both outside the pool: **the kill costs the human
nothing, and `FollowOutSpare` changes no payout.** Not read: what client flags 8 and 0x80 are (flag 8 is the one the
heist triggers skip a member for, 0x6893a4 / 0x5a1c57), and what the score page prints of this (0x783010).

### 1.5 Is it stock? Is it the multiplayer rule?

- **Stock**: 0x74b6d0 and 0x8fa6d0 are entries 7 and 194 of vtable 0xbd3514 (`debug\rtti.py`: `ZGameRulesHeist`
  only). The hook has no code patch (SHIP policy: import slots and data), no level field is read by the loop or
  by the schedule (the only level number near it is the drive-out time itself), and the time tables are set by
  the class's own constructor (0x835480, which stamps 0xbd3514: 0x83559d.., 0x8355db..). Stock Subway with its
  own AI crew does the same whenever the human boards with crew still out.
- **Multiplayer**: no. The flags test `test byte [score+0x1d4+4*i], 0x64` occurs once in the whole of .text - at
  0x74b951 - and of the ten references to the float 1,000,000 at 0xb631b0 this is the only one in a rules routine
  (the others: a kill box's damage, `killbox.cpp` at 0x85268e; `ZLoader_Sequence_Script_Reader`, `ZSleepGoal`,
  `ZMoviePlayer`; and 0x812b70, 0x81d060, 0x9fdce0, 0xa6c9b0, none of which touches the crew records up to its
  first return).
  The multiplayer classes have their own state and timer routines without it: `ZGameRulesFragileAlliance` and its
  client class slot 194 = 0x5b1410, the SERVER class `ZGameRulesFragileAllianceSv` slot 194 = 0x51e390 and slot 7 =
  0x827f00 (the first version left that one out; it refers to neither table nor to the float), slot 195 = 0x727610 /
  0x7a30c0. It is Arcade's way to end a one-human round tidily: when he is gone, everybody else is either with him
  or dead - by the amount a kill box deals.
- **It is not the other 'one-step kill'** of the notes (Retomoto, `record 4 lost 236.0 ... ONE STEP` with an idle
  human): that one needs neither state 5 nor a human aboard and is still unexplained.

### 1.6 What else was read for the design (EXE)

| what | where | what it does |
|---|---|---|
| the exit trigger | `ZOnlineExitLevelTrigger` 0x6c3d50 | in a round, for whoever activates it: 0x5dd890 (activator, 3) = heist stage 3, **no earlier stage asked for**; then, when the vehicle's state is 0, a vehicle is drawn and slot 44 calls it. The human's stage 3 and the call are one step |
| the boarding place | slot 89 = 0x49d170, called from slot 194 for any state but 0 while `[rules+0x1e0]` is 0 | `[rules+0x1e4]` = the vehicle from `[score+0x5c]`, `[rules+0x1e0]` = its boarding object. **Before the call there is none** (state 0 and state 7 clear it, 0x8fa74d / 0x8fad58) |
| the boarding rule | slot 45 = 0x6840a0 | state 3 / 4; **state 5 while float `[tuning+0x630]` minus the timer is under 1.0** (0x6840d1..0x6840ed, double 0xb393d8) - the control's record 4 boarded 1.1 s into a state 5 whose timer began at 8.4, so that float is under 8.3; if it is 8, the window is the first 1.4 s (the hook logs the four tuning times when the crew is called). Status 4, client flag 0x20; if nobody is left in play: timer = 0 (0x6841b1) |
| 'hold the driver' | slot 152 = 0x8b3930 | `if [rules+0xd95]: [rules+0xd95] = 0; announce; [rules+0x1d8] += 5.0` (double 0xb5a068). `+0xd95` is 1 from the call on, 0 at state 5: **once a vehicle**. The player's HoldEscape; no AI caller |
| the timer `[rules+0x1d8]` | counted down by slot 195 = 0x55ec70 (`timer -= dt`, not under 0; in state 3 / 4 at 0: slot 194 (5)) | other readers in the class: slot 76 (0x63b300, the getter - the board tactic's test and run ask it in state 1 / 2; `ZFATimeDisplay` 0x62a1b3 and `ZGameplayTrackerDisplay` 0x8e2740 show it), slot 191 (0x702990: the HUD's `FA_Exit / FA_Boarding` seconds, stored as a **signed byte** in `[score+0x58]`), slot 45 (above). Writers: slot 194 (the phase times), slot 45 and slot 94 grade 1 and slot 149 (0.0 = leave now), slot 152 (+5.0), slot 87 |
| the round's end timer | slot 192 = 0x5dff40 | does nothing while the vehicle's state is 1 .. 6 (0x5dffc6 `mov al, [esi+0x1dc] / test al, al / je / cmp al, 7 / jb out`): **a held vehicle postpones the round's end, it cannot lose the round by the clock** |
| a damaged vehicle | slot 195, state 1 / 2 at 0 (0x55ed44) | `[score+0x60] == 1` (heavily damaged): timer = 0 on arrival |
| scripted hits | slot 194 case 3 / 4 (0x8fa913..) + slot 7 (0x74b827..) + 0x6db660 | while the human sits aboard (state 3 .. 5): ten times, spread over the wait + 3 s, `[vehicle+0x864] = max([+0x864] - [+0x868] / 30, [+0x868] / 10)` - read as: a thirtieth of its health a time, never under a tenth (0xb45350, 0xb4e7e8) - and a hit effect on the player. Counter `[rules+0xec0]`, times `[rules+0xec4..]`, made once per wait: a longer wait adds none |
| the board tactic | `ZBoardEscapeVehicleTactic` test 0x4faf60, run 0x82f970 | state 3 / 4, **or 1 / 2 with the timer under 2.0** (jump table 0x4fb128; `fcomp [0xb5c828]` at 0x4faff7, the same gate in the run at 0x82f9be): a boarding place, **stage >= 3** (0x4fb064), a path |
| the loot tactic | test 0x451920 | off under stage 1 (0x4519d4); off at stage 3 **only** while the vehicle's state is 3 or 4 (0x4519dc..0x451a04) - **on in every other state, the drive-in too** |
| the rules' own order | slot 194's tail, 0x8fafa0..0x8fb061, states 1, 2, 5, 6 (table 0x8fb0a0) | every AI record with stage >= 3: `soldier->vtable[0x1b4]()`, `soldier->vtable[0x13c](&place, 1, 1, 0)`, place = boarding object + 500 along its x axis. **The record's actor is not tested**: 0x8fb031 `mov ecx, [eax+4]` / 0x8fb034 `mov edi, [ecx+0x77c]` (only the soldier is, 0x8fb03a). A stage 3 in a record without an actor is a fault here |
| the traitor tactic | `ZBecomeTraitorTactic` 0x79b7c0 | reads the BOT's stage (0x79b883 `mov dl, [record+0x78]`) for its stage term (klbot.c 3: 0 / 0 / 2 / 3 against a limit of 7.0) |

## 2. The design: `[Bots] FollowOut`

### 2.1 The signal: the human's heist stage 3

- It is the game's own 'he is at the exit': the exit trigger writes it, and calls the vehicle in the same step.
- **Why not 'near the boarding place'**: before the call the rules have no boarding place at all (1.6), so a
  distance can only be measured once the stage is already there; and the exit boxes are large (the bank's: the
  human took stage 3 about 50 m from where he boarded). A distance would only be the same signal, later - and time
  is exactly what the crew lacks.
- **Why not earlier (his stage 2, 'left the bank')**: on the bank it would give 16 s more (LIVE: stage 2 at
  10:15:01, stage 3 at 10:15:17). But nothing says where to send the crew then - no vehicle, no boarding place -
  so it would have to be 'to where the human is', a moving point for seven bots, renewed every two seconds: the
  escort's mechanism for all, new behaviour on every map, and 'left the bank' boxes are not exits on a map with
  two shops. **Not built.** If the hold of section 3 turns out not to be enough, this is the next step.
- **Guards**: he must be a heister (the player object's type byte `[player+0x273c] == 2`; a policeman after his
  death is 3 - the fed case does nothing) in play or aboard, and carry `FollowOutMoney` (default 1): the exit trigger
  asks for no earlier stage, so a walk through an exit box before any loot would otherwise call the whole crew out
  at the start of the round. `FollowOutAfter=N`: the crew is called N seconds after the signal (default 0 - every
  second of grace is one the crew does not have).

### 2.2 What happens then

For every AI record in play that is no traitor (mask 2 clear), once:

a. **Heist stage 3 into its record** (`record+0x78`; `max`, as the trigger's own routine 0x5dd890 writes; the byte
   `BoardAll` writes, which ran in the game in runs L12b, C3, B1, B6). **Only when the record's actor is a `ZFFActor`
   whose place can be read** (review M1): from stage 3 on the rules walk the record themselves at every call and
   departure without a test of the actor (1.6), so a record with a null or stale actor gets no stage - one line
   (`its actor is no ZFFActor with a readable place ...: the stage byte is NOT written`), looked at again every pass.
   Checked again just before the write: the record is still in use, the same actor, in play, no traitor, and under
   3. From here the game does the work:
   - while the vehicle waits, its loot tactic is off and its board tactic takes it to the vehicle and aboard
     (LIVE, L12b: a bot 7.6 m on 2.3 s after the byte, aboard at the next visit). **While the vehicle still drives
     in, the loot tactic is ON** (1.6): a called bot in reach of loot goes on looting for those 7 s and beats the
     order of (b), as it beats every defend order (the Late Night finding);
   - at every later call and departure the rules themselves order it to the boarding place (1.6).
   A bot at stage 0 gets it too (unlike `BoardAll`, which frees bots held by loot): a rear guard that never
   entered must come as well. The price: its loot tactic, off at stage 0, is on from then on whenever the vehicle
   does not wait - if the human does not leave after all, such a bot may start to loot.
b. **One order to the boarding place, only while the vehicle drives in and its timer is 2 s or more**
   (`FollowOutOrder=1`, the default): `soldier->vtable[0x13c](&place, 0, 1, 0)` through `kle_order2` - the escort's
   release call, with all of `kle_bot`'s tests before it. It is the order the rules gave the stage-3 AI at the
   call, which these bots missed by a moment. **Not while the board tactic can have the bot**: that is while the
   vehicle waits, and in state 1 / 2 once the timer is under 2.0 (review S2; 1.6) - a not-soft order to a running
   defend goal pops its goal stack (0x7bbf70) and would cut the very tactic that takes him aboard. One line a
   call says when that window begins (`the vehicle arrives in 1.9 s (call 1): no order from here on ...`).
   Not within 4 m of the place (within 2.5 m the game takes an order as 'soft', which ends a waiting step of the
   route chain). Only to bots this part gave their stage; never to an escort (the escort part sends its own).

### 2.3 The route chain against the order

Corrected first: the escort is not re-pointed every 2 s 'because its chain pulls it away' - it is re-pointed when
the HUMAN has moved away from the place it holds, 2 s apart at least; the chain pulled 13 times in 125 s in run E3.

- The chain does not read the stage byte: **a stage-3 bot's chain pulls exactly as before.**
- A Defend step that was running when the order came keeps waiting for its man (the order is not soft): the chain
  stands still behind him. A step started by something else (a delay timer, a 'guards dead' trigger, the loot wait)
  orders him to its own place: the last caller wins.
- **Renewal**: while the vehicle still drives in (timer 2 s or more), at most every `FollowOutEvery` (2 s), a bot
  whose defend place is **more than 6 m** from what our order left there is ordered again. 6 m is `KLE_ROUTE`, the
  escort part's own measure for 'the route chain moved it, not one of the soldier's own tactics' (a GUESS there
  and here; the first version renewed from 1 m, and every renewal pops a fighting bot's goal stack - review S2).
  At a later call of the vehicle the game's own order has put the place there; the hook orders only a bot whose
  place is not within 3 m of it.
- In the wait nothing needs renewing: the board tactic does not go by the defend place.
- When the vehicle leaves, the rules' own order to every stage-3 AI is SOFT (0x8fb054 `push 1`): it ends the
  waiting step, and the chain's next step takes the bot on along its route. For a bot left behind with the human
  aboard that no longer matters. With the human still out, the bot is back on its route (which ends at the
  vehicle's stop), now at stage 3: it boards at the next visit as any stage-3 bot of the game does.

### 2.4 Stops, and the cases asked about

| case | what the part does |
|---|---|
| a bot aboard, dead, escaped | one line, then nothing. A bot found dead in the pass in which the human's own status ends the round still gets its line (`..., seen as the round ended for you`; review S4) |
| a bot turns traitor, or its record gets another actor | never written or ordered again (asked before every write and call) |
| a record whose actor is no `ZFFActor` | no stage byte, one line, looked at again every pass (M1) |
| the vehicle is under 2 s from arriving, or waits | no orders; stage bytes still (a bot that came into play late) |
| the vehicle has left, the human still out | no orders until it is called again; the stage stays |
| the human dead or escaped | `follow: over (...)` with the count; nothing more this round |
| the human is police (`[Fed] Player=1`) | nothing: type byte 3 |
| a stock level, or the Steam guard off | nothing: `klb_level`, the gate of the escort and of `BoardAll` |
| an escort (`Escort=1 / 2`) | gets the stage byte; no order from here - it is beside the human, and its own release sends it |
| `BoardAll=1` | runs before this part in the same pass; a byte it has just written is reported as 'stage 3 since this pass'. Both write the same value with the same test: no fight |
| `VanLeftBehind=1` | `FollowOut` switches itself off (every stage-3 bot counts as 'at the vehicle' there). With `Van` alone it says a note: a bot that turns traitor after it was called counts as at the vehicle |
| `Bribe` / `Leave` (klbot.c) | both act only while the human is NOT aboard and write the timer to 0; the hold acts only while he IS aboard and never raises a timer of 0: they cannot meet |
| `[Fed] Bots=1` (klfed.c) | a heister's death releases its parked policeman: with `FollowOutSpare` fewer die in the last 8 s, so fewer are released there - nothing else changes |
| **the human goes BACK inside** | **nothing is taken back.** The stage is the game's maximum; the game never lowers one in a round and neither does the hook. His crew is at stage 3: it goes to the vehicle at the next call, boards when it waits, and whoever of it stands in the exit box calls it - the crew leaves without him, as the game's own stage-3 bots do. His escort stays until the vehicle waits. `FollowOutMoney` covers the commonest accident (crossing the box before any loot); it is a thin guard on a map whose exit box lies on the way to more loot |

### 2.5 Two consequences for the owner (review S6; EXE)

- **His cut.** The rules pay every escaped non-traitor the same share of what they carried together (1.4). A bot
  these keys get aboard joins that split: the human's cut - in stock already the average of those who escaped -
  becomes the average of a larger crew, more if the bot carried more than the rest, less if less. In the control
  the four who were shot carried 465,000 / 0 / 20,000 / 630,000: with all of them aboard the share would have been
  2,120,000 / 7 = 302,857 instead of 335,000. `FollowOutSpare` alone changes nothing here. What the score page
  shows was not followed: **take a picture of it in J1 / J2 / J3 and compare with the control's.**
- **Traitors.** The traitor tactic's stage term is 0 / 0 / 2 / 3 by the bot's own stage, against a limit of 7.0
  with money terms of 0 .. 3 each for the bot and the player (klbot.c 3; the values are that file's, not read again
  here - the term's source is, 0x79b883). A bot inside at stage 1 can reach 6; raised to 3 it can reach 7 and more.
  Stock allows traitors from Arcade level 4 on - where an owner who wins rounds is after three. So `FollowOut` makes
  a betrayal possible for a called bot that could not have turned where it stood. With `[Bots] Tune=1` (every
  level, limit 6.0) a stage-1 bot can just reach the limit already; a called one needs 3 points less of the two
  money terms. REASONED from the table; not seen.
- The five readers of stage 3 (`re\boardall_review_exe.md` 1) besides: `Backstab`'s `BackstabStage`, `Van`, the
  off-stage damage factor (a called bot is on the human's stage: it hits police at the full factor), kltalk's stage
  line.

## 3. `FollowOutHold=N` - the driver waits for the crew (one float)

- **Who counts the timer down**: slot 195 only; the table in 1.6 has every reader (the review scanned the getter's
  callers too: nothing that decides was missing). The HUD shows the new seconds (the byte in `[score+0x58]`: the
  timer stays under 8 s here).
- **'The game's own write' - of the address and the amount, not of the count** (review N2): slot 152 adds 5.0 once
  a vehicle, behind `[rules+0xd95]`. The hook writes the same float by the same amount up to N / 5 times a visit and
  leaves that byte alone - so the human's own HoldEscape still gives its 5 s on top.
- **The write**: while the vehicle waits (state 3 / 4) and **the human is aboard**, when the timer is under 2 s
  and above 0: `timer += min(5, what is left of N)`, read again and written in the same pass, on the game's
  thread. 2 s = four passes of this file's 0.5 s tick; N at most 60, per visit.
- **Only while called crew COMES** (review S1): at least one called bot in play is **2 m or more nearer to the
  boarding place than 2 s before** (`KLE_COME`; the straight distance the pass computes anyway, sampled per bot
  every 2 s; no whole sample yet = no). The first version asked 'moves 3 m in 2 s in any direction': a bot that
  its route chain walked deeper into the map held the driver for the whole N seconds with the human sitting in a
  vehicle the police shoot at. Now a bot that stands, fights, loots or walks the other way does not count. The
  price: a bot whose way to the vehicle leads away from it for more than 2 s is not counted for that sample.
- **Not** when: the timer is exactly 0 (something set it to leave: the last criminal boarded, the driver was paid,
  a bribe / leave of klbot.c); `[rules+0x1b3] != 0xff` (somebody paid the driver); `[score+0x60] != 0` (a damaged
  vehicle must go).
- Not when the human is not aboard: then the vehicle's leaving kills nobody, and it comes again.
- **It cannot lose the round by the clock** (review N3): the round's end timer does nothing while the vehicle's
  state is 1 .. 6 (1.6). A held vehicle postpones the end.
- **Risks**: real police fire on a vehicle that waits longer (the F07 van has health and a FakeTarget: 'heavily
  damaged' makes it leave at once, 'destroyed' kills everybody aboard - the game's own price for holding); the
  human sits up to N s longer. The scripted hits of 1.6 do not grow and cannot destroy it (floor: a tenth).
- **Clocks** (review N6): the 2 s samples, `FollowOutAfter` and `FollowOutEvery` are wall time (`GetTickCount`); a
  game that stood still in the last 2 s of a wait (the window not in front) reads as 'nobody comes'. The N seconds
  are per visit as this file counts visits; if its round state is made new in mid-round (the rules object could
  not be read for a pass), a visit can get its N seconds again - bounded per visit, not per round, in that corner.
- **What N**: stage 3 to departure is 15 s without it. The bank's four were 55 .. 75 m off in a straight line.
  At about 3 m/s (GUESS: run E3's escort did ~100 m within one 29.5 s cycle and a bit) the nearest needs ~20 s
  more than he has, the farthest ~25. **15 first, then 25.** J1's wait / leave lines give the real speed.

## 4. `FollowOutSpare=1` - those left behind are not shot (one block)

- **The write**: when the state is 5, the `slots` dwords at `rules+0xeec` are set to 0x7fffffff - the loop's test
  is `cmp / jg`, signed, against a clock that counts 1/1024 s. One `klh_data` call on the rules object (heap).
  Nothing else: the shuffle bytes, the flags, the state stay.
- **Why it is in time**: the earliest time is 0.3 s after the change to 5 (8 slots; 1.2), and the loop of the
  frame that made the schedule has already run (slot 195 is called at 0x74b7cc, the loop is at 0x74b8a2). The
  0.5 s pass could be late, so while the vehicle waits the state byte is read on EVERY pass of the tick (one read)
  and the write follows the change within a frame. (The tick is skipped only while the hook's fallback thread holds
  it, after a 500 ms stall: one skipped tick does not lose a bot - review N7, REASONED.)
- **Tested before the write** (review S3): the rules object is the round's `ZGameRulesHeist`, the state is 5,
  1 .. 12 slots, every time either ours or a value of the clock that is not negative and not more than 16 s ahead
  (the latest the game sets is 9.3 s) - and the table has one of its honest shapes (1.2):
  - *scheduled* - the slot bytes are a shuffle of 0..slots-1 (each record once);
  - *never used* - all twelve times are 0, as the constructor left them. The slot bytes are then whatever the heap
    held and are **not judged**: the game's loop skips one out of range (0x74b91e), and the constructor never wrote
    them. The first version asked 'every slot byte under the number of slots' always, and so refused exactly the
    first departure of a round object with the human not aboard - with the line J0 reads as 'the offsets are wrong';
  - *put off by this file* - every time ours: nothing to do.

  Times of the clock beside bytes that are no shuffle: one line (`do not hold the table this build knows`), nothing
  written. The review proposed 'judge only the times when client 0 is not aboard'; the shapes are stricter and also
  cover the human who boards AFTER the change (he is aboard, and no schedule was made): a dword that is a pointer
  into the exe would pass as 'a time in the past' once the clock is beyond 0x400000 (68 minutes, if it counts from
  the start of the process - not established), and the bytes or the twelve zeros are what tell the table from that.
- It is also done when the human is not aboard (no schedule was made: he can still board in the first 1.4 s of
  state 5, and the loop would then run on whatever the table held; said once a round, in one of two wordings:
  'the table of an earlier one' or 'the table as the round object was made (never used ...)' - **both are healthy**).
- **What it leaves**: the bots stay in play; the round ends 3 s after the human's escape as ever (1.4) - with
  crew 'in play' at the end, a state stock reaches too (1.1, the second run). The vehicle goes to state 7 instead
  of 8. The 'all dead' paths are not touched. No payout changes (1.4). Works without `FollowOut`.
- **Is it 'one clean data write'?** One block of one table that only that loop reads - yes. But it needs the
  every-pass read to land in time, and it changes what the end of a won round looks like for every map of the
  expansion. It is a key of its own, off, and can go without touching the rest.

## 5. The code (`klhook/klescort.c`)

| function | what |
|---|---|
| `kle_follow` | called from `kle_tick` after `BoardAll`, every 0.5 s pass of a round on a level that is not stock, game thread: the signal, the 'over' pass (with the deaths not said yet), the per-record walk (status lines, the 'comes' sample, the wait / leave lines, stage byte, order), the two summary lines at the vehicle's wait and departure, the hold |
| `kle_spare` / `kle_spare_fast` | the table test and write; the every-pass read of the state byte, armed by the 0.5 s pass while the vehicle waits |
| `kle_criminal` | the local player's type byte, without `kle_human`'s node test (a player aboard must count) |
| `kle_order2` | `kle_order` with the dry flag as an argument (`kle_order` now calls it with `EscortDry`) |

Constants new with the review: `KLE_COME` 200 (2 m in 2 s; GUESS), `KLE_BOARD_WIN` 2.0 (the board tactic's window,
float 0xb5c828); `KLE_ROUTE` 600 is the escort part's and now also the renewal's.

Keys (`[Bots]`, all need `Enable=1`): `FollowOut=0`, `FollowOutDry=0` (`EscortDry=1` does the same for this
part), `FollowOutMoney=1`, `FollowOutAfter=0`, `FollowOutOrder=1`, `FollowOutEvery=2`, `FollowOutHold=0`,
`FollowOutSpare=0`. Every pointer chain is read through `klh_rd`; every write goes through `klh_data` /
`klb_put8` (the guard); the one call is the routine the escort part already calls, after the same tests.
The escort's and `BoardAll`'s own code paths are unchanged except: `kle_order` is a wrapper now, the tick no
longer returns early when only the new keys are set, and three log texts name the new part.

## 6. Off the game

- **Compile**: `build_auto.bat` (TEST) and `build.bat` (SHIP), /W3: no warning from `klescort.c`; the build's one
  warning is `klhud.c(188)` (`'i': unreferenced local variable`), another session's committed file. At /W4 one in
  `klescort.c`, line 386, old code (`kle_node`'s parameter `dir` hides a global).
- **RIG** (`G:\kl_scratch\j\rig\klfollow_rig.c`, `build_rig.bat`; scratch, not in the repo): `klhook.c` of the
  source snapshot (section 7) included as it is (SHIP configuration), the hook's clock replaced by the rig's, and a
  made-up Arcade round in the program's own memory - session, rules object, eight crew records, score object,
  actors, nodes, soldiers, defend blocks, a boarding object, the clock, the two tables - with a stub at the order
  routine's address that starts with the sixteen bytes the hook compares and then records the call.
  **58 checks, 0 failed.** The first 41 are the first version's and pass unchanged: nothing before stage 3;
  `FollowOutMoney`; the four right records get stage 3, the traitor / the dead / the one already at 3 do not; three
  orders (not the bot 2 m from the place), their defend place is the boarding place; no second order while the
  place is ours, none within 2 s, one after the chain moved it; none while the vehicle waits; the timer untouched
  until the human is aboard, then 1.8 -> 6.8, three times, not a fourth (15 s used); not at 0, not damaged, not
  paid, not when nobody comes; the times put off by the fast pass 20 ms after the change; refused for a table that
  holds a float or a slot byte over the number of slots beside real times; dry: nothing written, nothing called;
  police human, unknown level, `VanLeftBehind`, `FollowOutAfter`, `FollowOutOrder=0`, every key off.
  The 17 new ones are the review's findings as checks (its section 6): a table never used with slot bytes 0xcd or
  0, human not aboard and aboard - put off, no refusal line; one record named twice beside real times - refused;
  both bots shot in state 5 have their `LEFT BEHIND` line, the second from the 'over' pass; a human who dies - the
  line without it; a death after the times were put off - 'not their shot'; no stage for a record without a
  `ZFFActor`, written once it has one; state 1 with 1.5 s to go - the stage, no order, one line, and the three
  orders at the next call; a defend place 4 m from ours - no renewal, 8 m - one; a bot walking away or 1.1 m
  nearer - not held, 4.7 m nearer - held.
- **The reviewer's own rig file**, `rig2.c`, copied unchanged to `G:\kl_scratch\j\rig_review` (only the include
  path points at the snapshot): the first version's 41 checks and its five cases R1 .. R5, which each showed a
  finding before: **all ok now.**
- **It proves this file's own logic and nothing about the game.**

## 7. Builds (2026-10-11, after the review's fixes; these supersede 996ee63c / 92d0aa37 and the review's own)

| build | file | sha1 |
|---|---|---|
| TEST (`build_auto.bat G:\kl_scratch\j\test`) | `G:\kl_scratch\j\test\dinput8.dll` | `506f96b934da39483ec847c1b8d7584462e94b55` |
| SHIP (`build.bat G:\kl_scratch\j\ship`) | `G:\kl_scratch\j\ship\dinput8.dll` | `9220d0218da652c79649af338a40ad5afe5444f1` |

**What they are built from**: NOT the shared working tree (CLAUDE.md's build note: another session's
`klhook/klclimb.c` is uncommitted and changing there) but a snapshot in `G:\kl_scratch\j\src\klhook` =
`git archive HEAD klhook` at 7896d0f **plus this track's `klescort.c`** (sha1
`282c1dace59cf80a4347deb090c6e43e68fe0450`) - and nothing else that is not committed (checked file by file: the
snapshot differs from HEAD in `klescort.c` only, and from the working tree in `klclimb.c` only). So they carry
every hook part committed up to that HEAD - among them `klhud.c` with `[HUD] Reuse=2` and its fix 1c817c8, off
unless `[HUD] Enable=1` - and do NOT carry the uncommitted `klclimb.c`. The two batch files were run from the
snapshot (they compile the `klhook.c` beside them). A copy of the sample ini with the new lines:
`G:\kl_scratch\j\KLHook.sample.ini`. If `klescort.c` is committed as it is, a build from a clean worktree of that
commit is the same source.

## 8. Live checks for the lead, in order

The human: the scripted bank walk `<work>\research\playtest\rig2\PT_DM03_board_r2.ini` (he boards at the first
visit), the build and the `[Bots]` / `[Balance]` lines of run **`PB_DM03_board_hp`** = the CONTROL (four bots shot
at the departure: 10:15:35.6 .. 40.7). `[Bots] Enable=1 Log=2 Escort=1` as there; add only the keys named. One
variable a run. A fault of any kind in a run = FAIL, stop. Order: J0, JS, J4, J1, J2, J3, J5, J6 - J0 (dry) may run
at once; JS and J4 need nothing from the others.

**J0 - dry** (`FollowOut=1 FollowOutDry=1 FollowOutHold=15 FollowOutSpare=1`). The measurement run; the round must
go exactly as the control.
- PASS lines, in this order: `follow: on; ... DRY RUN`, `follow: spare on DRY RUN`; at the human's stage 3
  `follow: you are at heist stage 3 (in play, $...); vehicle state 1, timer 7.. s: THE CREW IS CALLED - N AI
  heister(s) ... WOULD get (dry run) heist stage 3 ... the tuning's vehicle times a / b / c / d` (**c is the
  state-5 boarding window's number, expected about 8, under 8.3**); per bot `follow: record N (stage S, $M) at (x,
  y, z), D m from the boarding place: heist stage WOULD be set to 3 (dry run)` and `follow: record N WOULD be sent
  (dry run) to the boarding place (...)`; `follow: the vehicle arrives in 1.x s (call 1): no order from here on`;
  per bot `follow: the vehicle waits (state 3, ..., visit 1): record N (stage S, $M) in play at (...), D m from the
  boarding place, coming / not coming (x m nearer in the last 2 s)` and the summary; `follow: hold: ... WOULD get
  5.0 s more (dry run)` or `... is NOT held: none of the called crew in play comes nearer ...` (expected here: in a
  dry run the bots are still at stage 1 and do not come); per bot `follow: the vehicle leaves (state 5, ...): record
  N ... in play at (...), D m ...` and `follow: the vehicle leaves (state 5, timer 8.4 s) with you aboard: A of the
  crew aboard, P left in play (record(s) ...)`; **`follow: spare: the vehicle drives out with you aboard: the
  rules' times for those left behind (8 slot(s), the first due in X s) WOULD be put off (dry run: they are shot)`
  with X between 0.3 and 2.0** - that X is the proof that `rules+0xeec` is the table; then the control's deaths,
  each as `follow: record N dead ... - LEFT BEHIND: ...` (the last may read `..., seen as the round ended for you -
  LEFT BEHIND`: it died in the half second before your `status6`); `follow: over (you escaped): of the crew A
  escaped, D dead, P left in play`. **The number of `LEFT BEHIND` lines = klbot's `ONE STEP` lines between `van 5`
  and your `status6`.**
- FAIL: `follow: spare: rules +0xeec / +0xf1c do not hold the table this build knows` or `rules +0xeec does not
  hold the table of times` with you aboard at the change (the offsets are wrong: keep `FollowOutSpare` off, tell
  this track); any `heist stage set to 3`, `sent to`, `timer a -> b` (a write in a dry run); a klbot line `heist
  stage N -> 3` at the moment of the call for a bot far from the exit; fewer `LEFT BEHIND` lines than `ONE STEP`.
- READ from it: every bot's D at the call, at the wait and at the leave (here they do not come: it is dry) - the
  base J1 is compared with.

**JS - the gate on a STOCK level** (review S7; `FollowOut=1 FollowOutHold=15 FollowOutSpare=1`, not dry, stock
Subway through the Arcade page, an idle human, four minutes so that the AI crew's vehicle comes and leaves).
- PASS: the two `on` lines at the start; once, when the round runs, `escort: this level is the STOCK one of its
  slot (a round here can go to Steam): nothing is done here (this part acts only on a level that is not stock)`
  (the prefix is `escort` with `Escort=1`, `follow` when neither `Escort` nor `BoardAll` is set); **no other
  `follow:` line in the whole run** - none at klbot's `van 3` and `van 5` lines either; the round as stock plays it.
- FAIL: any `follow: spare:`, `follow: you are`, `follow: record`, `follow: hold` line; any `heist stage set to 3`.

**J4 - the spare alone** (`FollowOutSpare=1`, FollowOut off): as the control up to the departure. Independent of
everything else, and the cheapest thing to hand the owner if the rest disappoints.
- PASS: `follow: spare: the vehicle drives out with you aboard: ... (8 slot(s), the first due in X s) are put off:
  K AI heister(s) in play are not shot (record(s) ...)`; **no `lost 252.0 ... ONE STEP` line between `van 5` and
  your `status6`**; klbot's line after the escape reads `van 7` with K bots `in-play`; `session: state 0x19 ->
  0x1f` 3 s after the escape; the score page comes up (a picture). The stock precedent to compare with:
  `PB_DM01_board_hp` 10:58:23.855 (`van 7`, one bot in play, the same end). With FollowOut off there are no
  `follow: record` / `follow: over` lines: K is read from klbot's line.
- FAIL: a ONE STEP death in state 5 (the write came too late or missed: say which X the line gave); the round
  does not end; anything odd on the score page about the crew still in play.

**J1 - the byte and the order** (`FollowOut=1`). Two questions, judged apart (review S5).
- MECHANISM, PASS: per called bot `follow: record N (stage S, $M) at (...): heist stage set to 3` with klbot's own
  `record N (bot): heist stage S -> 3` in the same second; for each of them farther than 4 m `follow: record N
  sent to the boarding place (x, y, z), the game set (x, y, z); order 1` - the two places within a few metres of
  each other (the game's snap to the mesh); no `- the game took it as 'he is there already' (soft)`; no fault.
- MOVEMENT - **judged from the wait edge on, not during the drive-in**: per bot, its D in `follow: the vehicle
  waits (...): record N ... D m ...` against its D in `follow: the vehicle leaves (...): record N ... D m ...` (8 s
  later) or in its `follow: record N dead ..., D m ... - LEFT BEHIND` line, or its `follow: record N aboard T s
  after the crew was called`. PASS: for the bots that have a way, D at the leave is smaller than at the wait, and
  smaller than the same bot's in J0. (D at the wait minus D at the leave) / 8 s is the speed; D at the leave over
  that speed is what `FollowOutHold` must be.
- EXPECTED, not a fail: **a bot in reach of loot does not move during the 7.2 s of the drive-in** - its loot
  tactic is on until the vehicle waits (1.6), and it beats the order; in the control records 2 and 5 were earning
  when the human took stage 3 ($375,000 -> $465,000, $550,000 -> $630,000). Its D at the wait can equal its D at
  the call. On the bank most of the four are still shot (`LEFT BEHIND`), nearer to the exit than in the control
  (472 294 -4932 / 258 336 -7004 / 816 336 -6371 / 809 240 -6376). `order 2`, `order 3` for one bot = its route
  chain put its defend place more than 6 m from the boarding place again: note which bot (the step is in the
  build's route file), not a fail. `no order to the boarding place yet: <why>` says why (e.g. its actor takes no
  orders now); `its actor is no ZFFActor ...: the stage byte is NOT written` should not appear at all - if it does,
  note the record: that is the case M1 was written for.
- FAIL: a fault; a `heist stage set to 3` line without klbot's echo; `the game set` more than ~10 m from the place
  asked (the boarding place is off the mesh for the bots); **no called bot's D shrinks between the wait and the
  leave** (the byte does not flip the two tactics as read).
- Also take a picture of the score page: your cut against the control's (2.5).

**J2 - the hold** (`FollowOut=1 FollowOutHold=15`; then `25`). The run's total seconds and the board script's
waits after the boarding must allow up to N s more before `van 5` (review N9).
- MECHANISM, PASS: after `record 0 (you): aboard`, `follow: hold: the vehicle would leave in 1.x s with you aboard
  and K of the crew still coming (...): timer 1.x -> 6.x s (5.0 of 15.0 s used this visit)`, up to three times;
  klbot's line shows `van 3` for up to 23 s instead of 8; then `follow: hold: ... is NOT held: none of the called
  crew in play comes nearer to the boarding place (2 m in 2 s)` or `the 15.0 s of FollowOutHold are used`, and the
  vehicle leaves by itself; the HUD's boarding seconds jump back up (a picture).
- OUTCOME (read, not judged against J1 bot for bot - two rounds with random routes differ): how many `follow:
  record N aboard` lines; per bot D at the wait against D at the leave. `is NOT held` at the FIRST time the timer
  falls under 2 s, with bots far away in the wait lines, means: nobody was approaching (looting ended only at the
  wait, a fight, the chain pulling) - the answer 'a hold does not help this crew here', not a fault of the hold.
- FAIL: the vehicle never leaves (it must: the seconds are bounded); it leaves at once after a hold (`van 5` in
  the next line: something reads the timer in a way that was not found); the human dies aboard or the van's state
  goes 6 (shot to pieces: note the second, lower N).

**J3 - the spare with the rest** (`FollowOut=1 FollowOutHold=<what J2 settled> FollowOutSpare=1`).
- PASS: `follow: spare: the vehicle drives out with you aboard: ... (8 slot(s), the first due in X s) are put off:
  K AI heister(s) in play are not shot (record(s) ...)`; **no `lost 252.0 ... ONE STEP` line between `van 5` and
  the human's `status6`**; `follow: over (you escaped): of the crew A escaped, D dead, P left in play` with P = K;
  `session: state 0x19 -> 0x1f` 3 s after the escape as in the control; the score page comes up (a picture); the
  next round (if the script goes on) starts with seven bots.
- A bot that dies in state 5 by real fire reads `... - while the vehicle drives out with you, although the rules'
  times were put off (FollowOutSpare): not their shot`: not a fail (its health line is not ONE STEP).
- FAIL: a ONE STEP death in state 5; the round does not end; anything odd on the score page about the crew still
  in play.

**J5 - the neighbours**: (a) an idle-human run of any map with `FollowOut=1 FollowOutHold=15 FollowOutSpare=1`
(e.g. `W1_DM02`'s setup): only `follow: on` / `spare on` and, once a round, `follow: spare: the vehicle drives out
without you: no time was set for this departure; the table ... is put off in case you board in its first second` -
**in either wording** ('the table of an earlier one (8 slot(s))' or 'the table as the round object was made (never
used: ...)': both are a healthy build, review S3); the round as before, no ONE STEP that the map's idle runs do not
have. FAIL only: `do not hold the table this build knows`, `does not hold the table of times`, any `follow: record`
line. (b) `BoardAll=1` with `FollowOut=1` on Late Night Opening with a walking human: `board:` and `follow:` lines
for different bots, or `it has heist stage 3 since this pass` - never two `heist stage set to 3` for one record.

**J6 - the other maps**, the human's board script of each (`PT_DM01 / 02 / 06 / 09_board_r2`), `FollowOut=1` +
the hold that J2 settled: per map how many of seven board. Retomoto's tower crew has no way to the street van but
the join (`[CrewJoin]`): expect `not coming` / not held there.

**Not for a script - for the owner's eyes**: he walks into the exit box, then back inside (2.4, last row).

## 9. ASSUMED, not established, not done

- **ASSUMED / GUESS**: a bot's walking speed (about 3 m/s) and with it the hold a map needs; `KLE_COME` (2 m nearer
  in 2 s = 'it comes') and `KLE_ROUTE` (6 m = 'the route chain, not a tactic'); that `[score+0x150+4*i]` is what
  the human 'carries' in the sense that matters for `FollowOutMoney` (it is the `$` of klbot's line, 550000 when he
  left, and the number the payout pools); that slot 71 with amount 0 only empties the record; that the boarding
  object stands still while the vehicle drives in (the rules order bots to it at the call, so it should).
- **Not established**: what `[tuning+0x630]` is on these maps (the hook logs it; under 8.3 by the control's record
  4); whether real police fire destroys a held van within 15 - 25 s; what the score page shows for crew left in
  play and of the shared cut (0x783010); what client flags 8 and 0x80 are (they take a member out of the share);
  the traitor table's numbers (klbot.c's, logged by the hook at a session's start); whether the rules object's heap
  block is zero when made (the code no longer depends on it); from where the clock `[sysif+0x48]` counts; the
  unexplained one-step kills with an idle human (1.5).
- **Not done**: the earlier signal (2.1); taking the stage back when the human turns round; a hold while the human
  is not aboard; faster bots; a rig in the repo (the scratch one is described in 6); `CLAUDE.md` (the lead's).
  Nothing was run in the game.

## 10. What the review changed (`re\bots_follow_out_review.md`)

Each finding was read again in kl2.exe (or run again on the rig) before anything was changed. **None refuted.**

| | finding | checked again | what changed |
|---|---|---|---|
| M1 | the stage byte was written for a record whose actor was never looked at; the rules walk a stage-3 record's actor untested | EXE 0x8fb031 / 0x8fb034: only the soldier is tested (0x8fb03a). RIG: actor 0 got stage 3 | no write unless the actor is a `ZFFActor` with a readable place; its own line; asked again every pass. Dry runs say the same |
| S1 | the hold counted a bot that 'moves' in any direction | RIG (the reviewer's R5: 1.8 -> 6.8 for a bot walking away) | 'comes' = 2 m nearer to the boarding place than 2 s before (`KLE_COME`); not known = no; the wait / leave lines print the metres |
| S2 | an order could land in the board tactic's own window; a renewal from 1 m pops a fighting bot's goal stack | EXE 0x4fb128 (states 1, 2 -> 0x4fafe0), 0x4faff7 and 0x82f9be `fcomp [0xb5c828]` = 2.0 | orders only with the timer at 2 s or more, one line when the window begins; renewal only beyond `KLE_ROUTE` (6 m) |
| S3 | the spare refused a table the game accepts, with the line J0 calls 'the offsets are wrong' | EXE: the constructor writes the 12 times and nothing at +0xf1c (all five instructions with that displacement listed); 0x74b91e skips a byte out of range; 0x7f87c0 swaps bytes | the three shapes of section 4 - stricter than the proposal ('times only when the human is not aboard'), and it covers the human who boards after the change; J5 (a) and J0 reworded |
| S4 | the last `LEFT BEHIND` line could be missing (the pass returned on the human's status first) | LIVE: the control's last death is 0.43 s before `status6`. RIG (R2) | the 'over' pass walks the records once more; J0 counts the lines against klbot's ONE STEP lines |
| S5 | J1 listed expected behaviour under FAIL | EXE 0x4519dc..0x451a04: loot is off at stage 3 only in state 3 / 4 | J1 split into mechanism and movement, movement judged from the wait edge; a per-bot line at the leave edge was added for it |
| S6 | the payout and the traitor consequence were not told | EXE 0x70b920, 0x796410 (pool, count, share), 0x7360a0 = `fld1 / ret`, 0x79b883 | 1.4 corrected, 2.5 new, the ini's and the comment's 'two prices' |
| S7 | the builds predated HEAD and carried another session's file; no stock control | `git status` | built from a snapshot of HEAD's `klhook` + this file only (section 7); JS added; J4 moved up |
| N1 | the drive-out is 8.4 .. 8.5 s, not 8.0 | LIVE both logs (`van 5 8.4s`); EXE 0x8fab3e | 1.1, 1.2, 1.3 and 1.6 corrected (slot 7 misses in ~3 rounds of 10; record 4 boarded 1.1 s in) |
| N2, N3, N5 .. N7, N9 | the hold's count, the round clock, 0x805120's flag, wall-time clocks, the fast pass, J2's run length | EXE 0x8b3933, 0x5dffc6 (N5 is the review's reading, not read again) | said in 1.4, 1.6, 3, 4 and J2 |
| - | the multiplayer server class's slot 194 was missing from 1.5 | `debug\rtti.py`: 0x51e390 / 0x827f00 = `ZGameRulesFragileAllianceSv` | 1.5 |

## 11. The hold killed the human aboard: the vehicle was destroyed (track N3, 2026-10-11 afternoon)

**OFFLINE: read in kl2.exe and in the three live logs; the fix compiles; NOTHING OF IT HAS RUN IN THE GAME.**
Files changed: `klhook/klescort.c` (section 3 c2, `kle_veh_read`, `kle_hold_guard`, `kle_veh_pass`, `kle_shield_off`, key
`FollowOutShield`), `klhook/klmove.c` (WaitForYouHold asks the same guard), the sample ini, `re/bots_move.md`, this section.

### 11.1 What the logs say (LIVE, `<work>\build\klhook\live\N1_DM03_boardnear.log`, `N1b_...notune.log`, `N1c_...nohold.log`)

| | N1 (hold 15, Tune=1) | N1b (hold 15, Tune=0) | N1c (no hold) |
|---|---|---|---|
| vehicle state 3 begins (from klbot's `van 1 0.8s` / `0.4s` line) | 15:27:50.9 | 15:37:36.3 | 15:42:57.8 |
| `record 0 (you): aboard` | :54.12 | :39.49 | 15:43:01.07 |
| holds (`timer 1.9 -> 6.9 s`) | :57.0, :02.0, :07.0 | :42.4, :47.4, :52.4 | - |
| a bot aboard | record 5, 15:28:09.5 | record 1, :52.9 | - |
| **the end** | `record 0 (you): dead` **and `record 5: dead` in the same tick**, 15:28:11.73; next line `van 6 9.8s` | `record 0 (you): dead` **and `record 1 (bot): dead`**, :57.52; `van 6 9.8s` | `van 5` at 15:43:05.8, `status6` 15:43:14.3 |
| from the wait's begin | **20.9 s** | **21.3 s** | 8.0 s + 8.5 s of state 5: escaped |

It is not the timer and not a second clock of the boarding: the vehicle's state goes **3 -> 6** (in N1 with 3.1 s still
on the timer 0.9 s before; in N1b 0.17 s after the fourth hold pass read state 3). State 6 = destroyed, and both
records that had status 4 are dead in that tick - nobody else. `balance: you lost 4949.7 (550.0 of 550.0)` 30 ms later
is the dead human's health object made new, not a hit. The traitors have nothing to do with it (N1b has none).

No fixed clock fits (the review's table, `re\bots_hold_review.md` 2): the death is 28.00 / 28.43 s after the call,
20.83 / 21.26 s after the wait's begin, 17.61 / 18.03 s after `aboard`, 14.7 / 15.17 s after the first hold write -
0.4 s of scatter from every possible start - and the wait timer AT the death was 2.25 s (N1) and 1.73 s (N1b).

**A fourth log, without any hold: `U_M01.log`** (Hot Coffee, 2026-10-10, idle human, no FollowOut; found by the
review): `van 2 7.9s` 16:28:24.4, `van 4 8.0s` 16:28:32.3, **`van 6 9.9s` 16:28:33.7** - the van destroyed 1.3 s into
its SECOND visit of a stock-length round, nobody aboard. It is the only other state 6 in `<work>\build\klhook\live`.
So the mechanism is the game's own and is seen without a hold; and either the health is NOT made new between visits
(`Reset`, 0x87f396, is a level message: who sends it was not read) or one step takes all of it.

### 11.2 What kills (EXE)

- **`ZGameRulesHeist` slot 94 = 0x6a1100 (grade)**: `[score+0x60] = grade`; grade 1: announcement, and in state 3 / 4
  the timer = 0 (0x6a1285..0x6a12a0); **grade 2, in states 1..5 (jump table 0x6a12b0): slot 194 (6), then for every
  record in use with status 4 (0x6a11a1 `cmp byte [record+0x10], 4`): its money gone (0x544550) and the rules' kill
  rule - slot 11 (`[vt+0x2c]`, 0x6a1240) for a human, slot 16 (`[vt+0x40]`, 0x6a1227) for an AI member**, the attacker
  `[rules+0x1e8]`. That is the whole of 'he is dead while aboard with 5,500 health'.
- **Who calls it - THE DIRECT PATH (found by the review; this is what the death rests on)**: the hit routine
  0x5aebb0 itself. After `health -= amount`: if the rules' vehicle kind (rules slot 95 = 0x5822d0 = byte
  `[rules+0x1ec]`) is 3 and the health is at or under 0 (0x5aec7c..0x5aec89) -> rules slot 33 (0x4d8a30: the attacker
  into `[rules+0x1e8]`) and **rules slot 84 = 0x61e570, which in states 1..5 calls slot 94 with 2** (0x61e5e7). No
  level wiring is in the chain. It is also why the state went **3 -> 6 with no 'heavily damaged' departure**: grade 1
  exists only as a level message, grade 2 comes straight from the hit that takes the last health. Slot 84's only
  other caller is the vehicle's update at 0x8fa37f behind the dword `[0x168d620]` (no writer in .text: a debug
  switch). State 6 is set by nothing else: the state machine (slot 195 = 0x55ec70) never makes it, the only `push 6`
  are slot 94 and its multiplayer twin 0x839380.
- **The kind byte `[rules+0x1ec]`** (read in this fix round): written by 0x42cfb0 from the class of `[rules+0x1e4]` -
  1 if the cast 0x7d29f0 takes it, 2 if 0x7ae760 does, 3 if 0x409920 does, else 0 (0x42cfc6 / 0x42cfe2 / 0x42cffe /
  0x42d016; the same triple at 0x626840.. and 0x7437d0..). 3 is asked by the hit routine (0x5aec7c) and the state
  machine (0x55ecf4) = the key-framed van. Which of 1 / 2 is the helicopter and which the Havok car: NOT read.
- **The second way to the same routine (the level's)**: `ZOnlineEscVehicleController` slot 26 (0x6d7d20), message
  0x168c770 with the grade as its argument -> 0x594b10 -> slot 94. The van's health object, a `ZAnimatedVehicle`
  (vtable 0xbcc0b4, the class's only one), sends `Activate_DamageFX_01 / 02 / 03` from its update (slot 87 =
  0x8fa330) when its health `[+0x14]` is at or under twice `[+0x18]`, at or under `[+0x18]`, at or under 0
  (0x8fa4f5..0x8fa5a8; one byte each at +0x1c..+0x1e so that each is sent once). `[+0x18]` = a quarter of the maximum
  (slot 82, 0x65322a; double 0xb293f0 = 0.25). Which of the three the level wires to which grade was not read, and
  the death does not need it.
- **The maximum** (0x552e10): in Arcade (0x7aca80) one of four of the object's floats by the dword `[0x156b5f0]`
  (0..3; +0x34 / +0x38 / +0x3c / +0x40), or +0x30 when 0x87c980 says so; the stock van's seven numbers are 9600, 10000,
  8000, 3000, 5000, 7000, 10000 (`re\bots_behaviour.md` 3.1) - if they lie in field order from +0x28, an Arcade van has
  **3000 .. 10000**. `[0x156b5f0]` is the option 'Difficulty' (`re\map_ai.md`: 0x472d50; `klbalance.c` KLR_DIFF), and
  every balance log of the owner's game says `campaign difficulty option 1` (`re\balance.md`): the second of the
  four = **5000, IF the field order holds** (ASSUMED; N3a's first `health H of M` line says M).
- **What takes the health** (slot 89 = 0x87f340, the object's messages, names from the registrars at 0xafdb00..):
  - `ProjectileHit` (0x168d6a4) -> 0x6c4730: **nothing if `[+0x21]` is set** (0x6c4740); else the weapon's damage
    (`[weapon vt+0x2f0]`) **x the hit's scale `[hit+0x18]`** (0x6c476e) x the vehicle's own factor for the attacker's
    kind (`[+0x48]` / `[+0x4c]`) -> 0x5aebb0: `health -= amount`, not under 0.
  - `DamageInfo` (0x168d6b0): `[info+0x28]` through the same 0x5aebb0, **nothing if `[+0x21]` is set** (0x87f36e).
  - `Invulnerable` / `Vulnerable` (0x168d6e0 / 0x168d6ec): `[+0x21] = 1 / 0` (0x87f426..0x87f448). No level of ours
    sends either (the string is in none of the five builds' .prp).
  - `FakeDamage` (0x168d6f8; a `ZAnimatedVehicleFakeDamage` controller sends it): `health -= x`, does not ask the
    byte. None of the five builds has that controller (same string count).
  - the rules' ten scripted hits (1.6; 0x6db660, the third branch for a `ZAnimatedVehicle` child, 0x6db7bb..): a
    thirtieth of the maximum each, **never under a tenth** (0xb45350 = 30, 0xb4e7e8 = 0.1): a third of the health
    while the human sits aboard, made once per wait - the hold adds none. They cannot destroy it.
- **So: real hits took the van's health to 0 - READ, NOT SEEN** (no log has the vehicle's health; besides 0x5aebb0
  the exe leaves only `FakeDamage`, the scripted hits, which cannot, and the debug switch). Police shoot it because
  `Body_Main` carries a `FakeTarget` of team Mercenary. Stock exposes it for 8 s of wait + 8.4 s of drive-out =
  16.4 s a visit (N1c: 16.5 s, alive); the 15 s hold made it 31 s, and it lasted 21. **That is not a rule 'under
  16.4 s is safe'**: `U_M01.log` (11.1) lost the van 1.3 s into a stock-length second visit.
- **NOT ESTABLISHED - steady fire or one step**: the direct path gives 3 -> 6 whatever took the last health, so the
  missing grade 1 says nothing about it. `re\melee_damage.md`'s rule fits: a soldier within 1.6 m of
  his target sends `ProjectileHit` with scale 100.0 at every burst step, and this handler multiplies the scale in
  (0x6c476e) - one step of an SMG is then 7,200 x the vehicle's factor, more than a 3000 .. 7000 van has. A squad
  that needs about 20 s to walk up to the van would give the two equal times. GUESS; the new `follow: vehicle:` lines
  (health at the wait, at every fall of a twentieth, at the drive-out, at state 6) decide it in the first run.
- The four vans of the tab are this one (F07's key-framed van: Hot Coffee, Late Night Opening, the bank, Retomoto -
  `OnlineEscAnimatedVehicle` + `FakeTarget` in their .prp). **The park's helicopter is an `OnlineEscHavokCar` with no
  FakeTarget and no `ZAnimatedVehicle`**: nothing was found that shoots it.

### 11.3 The fix: `[Bots] FollowOutShield` (default 2)

The hold still writes ONE clock, the wait timer `[rules+0x1d8]` (the hold's own start line says so); no second clock
exists. What is new is that a hold is only made when the vehicle cannot be shot to pieces meanwhile:

- right before a timer write, `kle_hold_guard` finds the health object as the game's HUD bar does
  (`[rules+0x1e4]` -> `[+0x40]` the first child's entity slot -> `[slot+0x60]` the object, word `[slot+0x5e]` the
  next sibling; 0x793b7e..0x793c60; every slot pointer checked against the scene's slot table `[[[0xe0ff90]+0xc]+0xc]`)
  and sets its **`Invulnerable` byte `[+0x21]` = 1** - one byte of a heap object, the byte the object's own
  `Invulnerable` message writes; no game routine is called;
- `kle_veh_pass` (every 0.5 s) takes it back - only the 1 this file wrote, only on an object that is still a
  `ZAnimatedVehicle` - when the vehicle is gone (state 0, 1, 2, 6, 7, 8; `FollowOutShield=2`) or when it drives out
  (`=1`: the 8.4 s of the drive-out are the game's own risk again); `kle_tick` takes it back at a new round, when the
  round is over or can no longer be read. The bookkeeping is outside the per-round block for that. If the level set
  the byte itself, it is left alone and not taken back; if the level cleared ours, it is set again (said once);
- **no shield possible = no hold, FAIL CLOSED** (fix round, the review's point 2): `... is NOT held: the vehicle's
  health object cannot be read ...`; and when the walk finds no `ZAnimatedVehicle`, the game's own kind byte
  `[rules+0x1ec]` decides: **3 (the key-framed van, the only kind a hit can destroy) = NOT held** (`... the rules say
  it is the key-framed van (kind 3 ...) but no ZAnimatedVehicle was found under it ...`), unreadable = not held, any
  other kind (helicopter, car) = held without a shield, the hold line ending `... is of kind N, not 3 ...: nothing to
  shield`. This also covers a derived class the exact-vtable test would miss. The walk was checked against the level
  on the bank only (`F07_EscapeVan_01 [ZAnimatedVehicle]` is the sixth direct child of the group that carries
  `OnlineEscAnimatedVehicle`, `z_cover3\M03`); the other three van maps were not looked at - there the log decides;
- `FollowOutShield=0` = the hold as it was. Its start line says what that did.
- `klmove.c`'s **WaitForYouHold shared the fault** in another form (the crew sits aboard while the human comes: a
  destroyed vehicle kills them) and asks the same guard now.
- **the DESTROYED line can accuse the shield** (fix round, the review's MUST): `kle_veh_pass` takes what the shield
  was at the top of the pass (our object, its byte as read then, seconds since it was set) BEFORE the release branch
  runs, and the state-6 line ends `- ALTHOUGH THIS FILE'S SHIELD WAS ON (the 'Invulnerable' byte of ... read 1 at
  this pass, set N s ago): SOMETHING ELSE THAN A HIT TOOK ITS HEALTH ...`, or `- this file's shield was set N s ago
  but the 'Invulnerable' byte ... read 0 ...` (the level's `Vulnerable` inside the last 0.5 s), or `- ALTHOUGH ITS
  'Invulnerable' BYTE IS n (the level's, not this file's)`. It is printed also without FollowOut (WaitForYouHold
  alone), and also when the health object can no longer be read at state 6;
- a guard call that finds OUR object with the byte 0 again sets it again and says `SHIELD ON AGAIN: ... was 0 again
  (the level's 'Vulnerable'?)` - no longer `shield: off (another vehicle is held)` (the review's point 7).

**The largest safe hold**: with the shield the key's own limit (60 s a visit; the timer stays under 7 s, so the
HUD's signed byte and the boarding rule's window are as before). **Without the shield nothing is safe at all - stock
only makes it rare**: the van stood 20.9 / 21.3 s in N1 / N1b, and `U_M01.log` lost one 1.3 s into a second visit.

**What the shield does NOT cover** (said in the hold's start line too):
- **the first ~6 s of every wait**: the shield goes on at the first timer write, when the timer has fallen from 8.0
  to under 2 s, and only if the hold's other tests pass (the human aboard, a called bot coming). Before that, and at
  any visit that is not held, the risk is stock's. A shield from the wait's first second was NOT built: it would
  change rounds in which no hold is ever made;
- **a vehicle that comes back damaged**: if the health is not made new between visits (`U_M01.log` suggests so), a
  second visit starts low and can be destroyed before the first hold. N3a must be read at a SECOND visit too;
- the scripted hits (they go on under the shield, to a tenth at the lowest: `Activate_DamageFX_01 / 02` can come - if
  the level wires one of them to grade 1 the vehicle leaves at once, which only ends the hold). **With `=1` the
  vehicle then drives out UNSHIELDED at what is left - possibly a tenth - for 8.4 s, and with either value it stands
  at that health at the next visit**: the `shield: off` line says `it takes hits again at health H of M (P %)`;
- a `[Bots] Van` call of klbot.c (the damage rule itself); `FakeDamage` on a level that has the controller.

**The default is the owner's choice, not this track's.** `=2` (as built) keeps the drive-out invulnerable although
nothing holds the driver any more: after a hold he cannot lose the van at all - less than stock's risk, against his
'it should be all the same kinda risk'. `=1` gives the drive-out back to the game - with a van the scripted hits
may have taken to a tenth, so MORE than stock's risk for those 8.4 s, and a destroyed van there kills him aboard
again (the death this section is about, by the game's own rule). The default stays 2 until N3b / N3e have run.

Builds (HEAD 1fee632's `klhook` by `git archive` + this track's two files, fix round; HEAD wires both parts, no new
lines for `klhook.c`): TEST `G:\kl_scratch\n3\test\dinput8.dll` sha1 `be27b9bc17ce460007c1a2a82d098db28bf3af44`, SHIP
`G:\kl_scratch\n3\ship\dinput8.dll` sha1 `543f34e3890a59ab97939e316582e71d980a1c51`; /W3: the one warning is
`klhud.c(188)`, not this track's. THE BUILD IS NOT BYTE-REPRODUCIBLE (the review got other hashes from the same
sources; in this round a comment-only change gave new ones): whoever builds the hook for a run takes the hash of the DLL he built. No rig was run for the new code.

### 11.4 The crew must arrive: what the three logs say (the bank, BoardNear=1500)

- At the call the six or seven stand 64 .. 84 m from the boarding place in a straight line - inside the bank; the way
  is the yard at x -1500 (z -6000 -> -900), the drop at the denied box (-1707, 420, -900), then 43 m to the van:
  about 110 .. 130 m. For the first seconds the straight distance does not shrink (`not coming` at the wait edge for
  five of six in N1b): the way leads sideways first, and a bot in reach of loot still loots while the vehicle drives
  in (1.6).
- Once in the yard they RUN: 6.6 .. 8.2 m nearer per 2 s sample = 3.3 .. 4.1 m/s (N1c's and FO_J1's leave lines).
- **First bot aboard 24.0 s (N1b) / 25.5 s (N1) after the call**; when the 15 s were used, 28 s after the call, the
  other five stood 10 .. 35 m off (N1b) - the last of them needs about 36 s. Without a hold the vehicle leaves 15 s
  after the call (6.9 s drive-in + 8 s): in N1c the crew is 46 .. 56 m off then and five are shot.
- What stops them is time, not the route: nobody stood still in the yard, and the board tactic takes a stage-3 bot
  the last metres. (BoardNear's far box used to give them 43 m: FO_J1, three aboard 7 .. 15 s after the call.)
- So the bank needs the driver for **about 21 s more: `FollowOutHold=25`**.

**ONLY THE BANK IS MEASURED** (`record 1 (an escort) aboard 24.0 s after the crew was called`, N1b; 25.5 s, N1).
The other maps are ESTIMATES from the board runs without FollowOut (straight distances of the bots that were shot,
when the human boarded; an assumed 3.5 m/s; they were NOT called in those runs, so these are upper bounds for a
called crew - no run has a called crew on any of them):

| map | run | the crew when he boards | a called crew needs | hold |
|---|---|---|---|---|
| Hot Coffee | `PB_DM01_board_hp` | 17 .. 26 m from the stop (6153, 0, 20659) | 5 .. 8 s: inside the plain 8 s wait, the call comes 8 s before he boards | 0 .. 5 s |
| Late Night Opening | - (no board run with a human) | not known; idle run W1: the crew gets out by itself | - | not known |
| Withdrawal | `N1` / `N1b` (BoardNear) | 58 .. 72 m at the wait edge, ~110 m by the way | 24 .. 36 s after the call | **~21 s** |
| A Walk in the Park | `PB_DM06_board_hp` | 80 .. 124 m from the helicopter (-1217, 133, -6713) | 23 .. 35 s and more by the paths | 10 .. 20 s and more |
| Retomoto | `B1_DM09_board_gates` | three on the road 127 .. 145 m behind, two at the lobby's square ~190 m | 36 .. 41 s; the two: 55 s | 21 .. 26 s; the two not |

**Proposed for the owner** (the keys are global, not per map; **25 is the BANK's value** - Retomoto's estimate wants
as much or more, the park's is open; the hold only lasts while a called bot comes nearer,
and ends by itself when the last of the crew is aboard - 0x6841b1 - so a large N costs nothing on Hot Coffee):

| key | value | what it costs |
|---|---|---|
| `FollowOut=1` | as now | 2.5: the split, traitors |
| `FollowOutHold=25` | from 0 | he sits up to 25 s longer; every bot it gets aboard joins the split (2.5) - and a TRAITOR can board with him (N1: `record 5 (TRAITOR) aboard`) |
| `FollowOutShield=2` | default; **HIS CHOICE between 2 and 1** (11.3) | 2: once held, the vehicle cannot be destroyed, the drive-out included - less risk than stock. 1: the drive-out is the game's again, with a van the scripted hits may have worn to a tenth - more risk than stock for 8.4 s. Either way the first ~6 s of a wait are stock's |
| `FollowOutSpare=1` | from 0 | whoever still does not make it (Retomoto's two at the square, a bot cut off) is left, not shot: no payout change, a round that ends with crew in play (4) |
| `BoardNear=1500` | as in the runs | the bank's crew walks the last 43 m: that is the 21 s above. A larger radius per map is NOT proposed - it would put the far box back and with it 'they vanish at the wall' |

NOT proposed: the order at the human's stage 2 (2.1: nothing says where to send them before the vehicle is
called; it would win 10 s on the bank - N1b: stage 2 at 15:37:19, stage 3 at :29 - and is the next step if 25 s of
sitting is too long for the owner).

### 11.5 Live checks (the bank, the board script and ini of `N1b_DM03_boardnear_notune`; one variable a run)

- **N3a - the health, dry** (`FollowOutDry=1 FollowOutHold=25`): the round must go as N1c (he escapes, the rules
  shoot the crew). PASS: `follow: hold: FollowOutShield=2: ...` at the start; at the wait `follow: vehicle: it waits
  (state 3, timer 7.9 s, 0.0 s after it began to wait): health H of M (100 %), takes hits; you are in play` with M one
  of 3000 / 5000 / 7000 / 8000 / 10000; `follow: vehicle: hit (...): health ...` lines as it falls;
  `follow: vehicle: it drives out (state 5, ...)`; `follow: hold: ... its timer WOULD get 5.0 s more (dry run); the
  vehicle WOULD be shielded (dry run); health H of M` - or, as likely in a dry run where nobody was called,
  `... is NOT held: none of the called crew in play comes nearer ...` (the guard is then not asked: the `vehicle:`
  lines are what this run is for). FAIL: `follow: vehicle: its health object cannot be read`
  (the walk is wrong: tell the track; no hold will be made), an M that is none of those, any `SHIELD ON`.
  M is expected to be 5000 (Difficulty option 1, if the field order holds).
  READ from it: does the health fall in steps of tens (steady fire) or in one step of thousands (the point-blank
  rule)? How much is left when it drives out at 8 s? **And let the run go on to a SECOND visit** (the dry human
  escapes at the first: use the idle human of `U_M01` / an `--until exit` script for this): does the second
  `it waits` line say `health M of M (100 %)` again, or what the first visit left (then a damaged van comes back,
  and the ~6 s before a hold's shield are the weak place)?
- **N3b - the shielded hold** (`FollowOutHold=15`, as N1b). PASS: `follow: hold: ... timer 1.9 -> 6.9 s (5.0 of 15.0
  s used this visit); SHIELD ON: the vehicle's 'Invulnerable' byte [xxxxxxxx+0x21] 0 -> 1 until it is gone
  (FollowOutShield=2); health H of M`, the next two holds `...; shielded since N s; health ...`; `follow: vehicle:`
  lines after it say `SHIELDED by this file` and fall by at most M / 30 a hit (the scripted hits) to no less than a
  tenth; klbot's `van 3` for ~23 s, then `van 5`; **`record 0 (you): status6`**; `follow: shield: off (the vehicle is
  gone): ... 1 -> 0 after N s`; `follow: over (you escaped): ...`. FAIL: `record 0 (you): dead` while aboard;
  `follow: vehicle: DESTROYED ... - ALTHOUGH THIS FILE'S SHIELD WAS ON ...` (**the cause read in the exe is then
  wrong or not the whole: send the log**; the line is made from what the shield was BEFORE the pass released it);
  `DESTROYED ... - this file's shield was set N s ago but the 'Invulnerable' byte ... read 0` (the level cleared it:
  the 0.5 s upkeep is too slow); `DESTROYED` with no tail BEFORE the first `SHIELD ON` (the unshielded first ~6 s:
  not the hold's doing, but tell the track - it is the case for a shield from the wait's begin);
  `is NOT held: the vehicle's health object cannot be read`; **on any of the four van maps: `nothing to shield`,
  `has no ZAnimatedVehicle health object`, or `is NOT held: the rules say it is the key-framed van (kind 3 ...) but
  no ZAnimatedVehicle was found`** (the walk misses that level's van: no hold is made there until it is fixed);
  no `shield: off` line by the score page; `could NOT be written back`.
  READ from the `shield: off` line: `it takes hits again at health H of M (P %)` - how far the scripted hits wore
  it under the shield (expected: not under 10 %).
- **N3c - the crew arrives** (`FollowOutHold=25`): as N3b with up to five holds; count `follow: record N aboard T s
  after the crew was called` - expected 24 .. 36 s, most of the crew; the last hold line's `nearest / farthest`.
  Then with `FollowOutSpare=1`: nobody shot (J3's lines).
- **N3d - a second round in the same process** after N3b / N3c: `follow: vehicle: it waits ...: health M of M (100
  %), takes hits` - not `Invulnerable by the level` (that would be our byte left behind).
- **N3e - `FollowOutShield=1`**: `SHIELD ON ... until it drives out`, `follow: shield: off (it drives out, and
  FollowOutShield=1 leaves the drive-out to the game)` at `van 5`, then `vehicle: hit` lines again; he should escape
  (if the vehicle is destroyed in state 5: that is the answer 'use 2', not a fault). A STATED CHECK of this run:
  the `shield: off` line's `health H of M (P %)` = what the van drives out with unshielded, and the `vehicle: hit`
  lines of the 8.4 s after it = what the drive-out costs; with P near 10 one real hit of 500 ends it. The same
  health is what a NEXT visit starts with if nothing resets it (N3a's second visit says whether).
- **N3f - the park** (`PT_DM06_board_r2`, `FollowOutHold=25`): `follow: vehicle: it has no ZAnimatedVehicle health
  object (a helicopter or a car) ...` once, hold lines ending `...; the vehicle has no ZAnimatedVehicle health
  object and is of kind N, not 3 ...: nothing to shield` (N = 1 or 2: which is the helicopter was not read); he
  escapes. FAIL: he dies aboard (then helicopters are shot too: tell the track); `is NOT held: the rules say it is
  the key-framed van (kind 3 ...)` (the park's vehicle is of kind 3 after all: tell the track, the park gets no
  hold until then).
- **N3g - WaitForYouHold** (`WaitForYou=1 WaitForYouHold=15`, the human slow to the van): `wait: hold: ... timer 1.x
  -> 6.x s (...); SHIELD ON: ...` and the `follow: shield: off` line when the vehicle is gone (the prefix is
  `follow:` also there).

### 11.6 ASSUMED, not established, not done

- ASSUMED: that hits took the health (not a path that does not ask the byte - READ in the exe, seen in no log; the
  DESTROYED line's tail is the evidence against it if it ever prints); the park's vehicle is of kind 1 or 2 and is
  not shot; the field order of the van's seven numbers (so: 5000 at the owner's Difficulty option 1); bots run
  3.5 m/s on the other maps as in the bank's yard.
- Not established: steady fire or one point-blank step; whether the van's health is made new between visits and who
  sends `Reset` (`U_M01.log`); which `Activate_DamageFX` the level wires to which grade (not needed for the death);
  that the health walk finds the van on Hot Coffee, Late Night Opening and Retomoto (checked on the bank only);
  how long each other map's called crew really takes (no FollowOut board run exists for them); whether a traitor
  aboard does anything to the human there.
- Not done: no rig for the new code (compile only); a shield from the wait's first second; the earlier call at
  stage 2; per-map values (the keys are global); `CLAUDE.md` (the lead's). The J2 / J3 checks of section 8 are
  superseded by N3b / N3c.
- Review: `re\bots_hold_review.md` (ACCEPT WITH FIXES); its MUST and SHOULD 2 - 9 are in this section and the code
  (fix round, 2026-10-11): 1 the DESTROYED line, 2 fail closed by the kind byte, 3 the direct path, 4 `U_M01.log`
  and the uncovered seconds, 5 the default as the owner's choice, 6 the health at `shield: off`, 7 the guard's
  wrong reason, 8 only the bank is measured, 9 `[0x156b5f0]` = the option Difficulty, 1 in the owner's game.
