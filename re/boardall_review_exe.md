# Review of `[Bots] BoardAll` (klescort.c, commits 6186767 + ad3070d) - the game's side

Written 2026-10-11 (reviewer, lens: kl2.exe). OFFLINE: static reading of `kl2.exe` build 0490 (base 0x400000) and of the
hook's sources, plus the logs of the earlier live runs (read only). **Nothing was run, built, installed or committed; no
source file was changed.** Status words: **read** = disassembled at the address given; **measured** = from a live log
named; **not read** = honest gap.

Verdict: **SAFE TO RUN LIVE as run L12** (the scripted test on Late Night Opening). No path to a fault was found in
what the byte's five readers do with it, and the order is the call the game's own route chain makes on looting bots
all the time. Before `BoardAll=1` goes into the owner's own KLHook.ini the 'should' items of section 7 want doing;
none of them is needed for L12.

What the live record does and does not cover (measured, the logs in `<work>\build\klhook\live\`): the hook has made
the order call **63 times** for real (L11_DM02 12, E1_DM03 38, E3_DM01 13; L9's 288 and E0's 12 'WOULD be
re-pointed' lines are dry runs), no fault - **every one of them to an escort at heist stage 0**, where the Loot
tactic cannot run (0x4519d4). So 'the order given to a bot whose Loot pass is running' has not run from the hook.
The game does exactly that itself: every Defend step of the route chain that fires while a bot loots calls
0x760e50 with (place, 0, 1, 0) (0x686bac / 0x686df2) - which is what 'the tactic beats the Defend orders' was
measured on.

Three things in the brief turned out different from what the code says, and they change what L12 should expect:

1. **The rules do NOT order stage-3 bots when the vehicle starts to wait.** Slot 194's order pass (0x8fafa0..0x8fb069)
   runs when the state becomes **1, 2, 5 or 6**, not 3 or 4 (section 1, reader R5). What takes a stage-3 bot aboard
   while the vehicle waits is the soldier's own `ZBoardEscapeVehicleTactic`.
2. **The stage byte flips TWO tactics, not one**: Loot off (0x4519dc) and Board ON (0x4fb064, `stage >= 3`). Board is
   second in the soldier's tactic lists, Loot is last (section 2). So the stage write alone sends the bot to the
   vehicle; the hook's order is the fallback for a bot that has no path.
3. **The vehicle waits 8 s** (measured, L11) and the Loot tactic comes back the moment it leaves. A bot 100 m away
   cannot make the first visit; section 6 says what L12 will most likely show.

---

## 1. Every reader and writer of crew record +0x78 (question 1)

How found (scripts in the scratchpad, `rv\`): `sweep.py` disassembles all of `.text` (2,541,993 instructions, resumed
after every undecodable byte) and keeps every operand `+ 0x78]`; `raw78.py` cross-checks with a raw byte search for
every byte-sized instruction with a disp8 of 0x78 (220 candidates; the 158 the sweep had not seen start inside another
instruction - nearly all are `00 68 78`, the tail of one instruction and a push; the three that read like a real move
or neg were looked at by hand, none is one); `bytes.py` / `wide.py` / `bias.py` look, in the 84 functions that reach
the record table (`[rules+0x348]` with the 0x7c stride, or a call of 0x7fd930 / 0x78f470 / 0x5dd890 / 0x817d20), for a
record pointer used under another displacement, a word / dword access that covers +0x78, and a whole-record copy.

Result: 62 functions in the exe touch a byte at `[reg+0x78]`. 54 are stack slots or other classes (the same base
register is used with displacements of 0x7c and more, the object has a vtable, or the stride is another; each looked
at). **Eight are the crew record:**

| | address | function | what |
|---|---|---|---|
| W1 | 0x5490d1 | record constructor 0x549030 (called from slots 197 / 198 and the update 0x74ba10) | `= 0` |
| W2 | 0x817e98 | round reset 0x817d20 (from 0x8c7ab3) | `= 0` for every record in use (bl is 0) |
| W3 | 0x5dd906 / 0x5dd90f | **0x5dd890**(activator, n) | `= max(old, n)`; nothing else (whole function, below) |
| R1 | 0x4519d1 | `ZLootTactic` test 0x451920 | section 2 |
| R2 | 0x4fb064 | `ZBoardEscapeVehicleTactic` test 0x4faf60 | `cmp [rec+0x78], 3 / jb` -> needs stage >= 3 |
| R3 | 0x591c00, 0x591c17 | 0x591b60 (from the NPC hit routine at 0x61ad18) | compares the SHOOTER's stage with the local player's |
| R4 | 0x79b883 | `ZBecomeTraitorTactic` test 0x79b7c0 | stage term `[R + 0x24 + 4 * stage]` (jump table 0x79b970) |
| R5 | 0x8fb02b | `ZGameRulesHeist` slot 194 = 0x8fa6d0 | `cmp [rec+0x78], 3 / jb` in the order pass |

No word / dword access covers +0x78. The only whole-record copies (`mov ecx, 0x1f / rep movsd`) are the two that put a
freshly built record into the table (0x42bcd3 slot 197, 0x588a29 slot 198). No biased pointer was found. So:
**the byte is not replicated** - nothing reads it but R1..R5, and its only writers are the constructor, the round reset
and 0x5dd890, whose four call sites are the trigger boxes (0x6c3d9e exit trigger: 3; 0x8d2781 / 0x8d27dd / 0x8d2835
gameplay trigger kinds 2 / 1 / 0: 3 / 2 / 1). Every machine raises it from its own triggers.

**0x5dd890, whole** (0x5dd890..0x5dd914, `__thiscall(rules, activator, char n)`, `ret 8`): activator's class id
(vtable +0x30) is ZFFPlayer -> index = 0x6c7700(player); is ZFFActor -> index = 0x78f470(rules, actor); else return.
Index 0xff, out of range, or record not in use -> return. `rec+0x78 = max(rec+0x78, n)`. No call, no flag, no
announcement. **The hook's byte write is exactly this function's whole effect.**

### What each reader does with stage 3 on an AI record that never walked through the boxes

- **R1 Loot**: stops while the vehicle's state is 3 or 4 (section 2). Wanted.
- **R2 Board**: becomes eligible. Wanted, and it is the half that does the work (section 2).
- **R5 slot 194** (read, 0x8faf81..0x8fb069): `state - 1` indexes the byte table **0x8fb0a0 = 0, 0, 1, 1, 0, 0** into
  {0x8fafa0 the pass, 0x8fb06b return}. So the pass runs for **state 1, 2, 5, 6** and NOT for 3, 4 (0, 7: range test).
  For every record in use with mask 1, stage >= 3 and `[actor+0x77c]` not null: `soldier->vt[0x1b4]()`, then
  `soldier->vt[0x13c](&place, 1, 1, 0)`, place = boarding object + 500.0 (0xb3d5e4) along its x axis.
  `re/bots_squad.md` 5.1 has this right; **klescort.c's header (section 1, 'WHO CALLS IT'), its RELEASE text, the
  BoardAll key text, klhop.c lines 58-59 and the review brief have it wrong** ('when the vehicle starts to wait').
  For a raised bot this means: nothing from the rules at the wait itself; a SOFT order to the boarding place when the
  vehicle drives off (5) and when the next one is called (1). Soft sets `[soldier+0x4fc] = 1`, which ends a waiting
  Defend step of its route chain (0x686c77): the chain then goes on to its next step - for the kl_fa_bots routes that
  is the way out. Not harmful as far as read.
- **R3 damage** (read, 0x591b60 whole; caller 0x61a980: `[hit+0xc]` is the attacker, kept at `[esp+0x14]` when it is
  a ZFFActor, pushed as the first argument at 0x61ad15): R = tuning + 0x6ac + level * 0x70. Shooter team Ally and the
  local player not police -> `[R+4]`; shooter not Ally -> `[R+0]`. Then, **only for an Ally shooter**: if the
  shooter's stage != the local player's stage, times `[R+0x1c]` (0.5 at Arcade level 1-3 ... 0.1 at 10-11).
  So it is the **bot's own fire on the police** that is scaled, not the fire it takes. (`re/balance.md` 1c and
  klbalance.c line 31 / 67 describe the row the other way round - attacker and victim are swapped there.)
  Effect of the write: a bot raised to 3 while the human is at stage 0-2 shoots the police at half strength from then
  on; if the human already stands at stage 3, a raised bot LOSES that penalty. A balance side effect, no more.
- **R4 traitor** (read): stage terms `[R+0x24], [R+0x28], [R+0x2c], [R+0x30]` = 0 / 0 / 2 / 3 (klbot.c's stock table).
  A bot raised from 1 to 3 gains 3 of the 7 points (6 with klbot's Tune). With the stock table nothing can turn on
  Arcade levels 1-3 (`[R+0x6c]` = 0); from level 4 on, or with `Tune=1`, every bot BoardAll raises is a traitor
  candidate as a bot at the vehicle is - while it still stands in the shop. `BecomeTraitor` is FIRST of the three
  Arcade tactics in the lists. kle_board_all skips a traitor, so such a bot is then left where it is.

### The other things the question named

- **The vehicle call**: the exit trigger 0x6c3d50 raises the stage and then, while the vehicle's state is 0
  (0x6c3e3e), calls slot 44 = 0x6cd8e0 for whoever stands in it, which sets bit 4 of the member's client-block byte
  `[[rec]+2]` and calls the vehicle (0x8154f0). **Neither reads the stage.** For a player the trigger also raises
  `rec+0x12` to 4; for an AI record it does nothing but the stage and that call. Nothing counts 'heisters at stage
  3' or 'everybody is out': 'criminals left' (0x4906b0) counts status 0. BoardAll acts only while the vehicle is
  already there, so no call is missed.
- **Round end / escape / score**: no reader of +0x78 among them (the list above is complete). Status 4 is set by the
  boarding rule 0x6840a0, which asks for no stage.
- **Set-once bits** `[[rec]+2]`: 1 entered (slot 47 = 0x689330), 2 exited (slot 48 = 0x5a1bf0), 4 at the exit
  (slot 44), 8 took loot (0x7280cf), 0x10, 0x20. A raised bot has stage 3 without bits 1 / 2 / 4 unless it crosses
  the boxes on its way. None of R1..R5 looks at them. **Who reads those bits: not read.**
- **klbot.c**: the new-round test ('the sum of the stages went down', also in klescort.c and klhop.c) cannot be
  tripped by a raise. **Backstab**: `r->stage >= BackstabStage` (default 2) is true at once for a raised bot - the
  picked bot may turn while still inside. **Van**: 'at the vehicle' IS `stage >= 3` there (klbot.c says so); with
  `VanLeftBehind=1` every raised bot that misses the 8 s is 'left behind at stage 3 while the vehicle drives out with
  somebody aboard' -> the damage rule is called (grade 2 kills everybody aboard). See defect S5. **Leave / Bribe**:
  not touched (status, and the HUMAN's stage).
- **kltalk.c** line 643: `st >= 2 && old < 2` -> a raised bot fires the 'Stage2' chatter event (it 'left the bank'
  while standing in it). **klhop.c**: a raised bot satisfies every hop's `Stage`; harmless (it must still stand at
  From). **klfed.c, klcrew.c, klcrew_rt.c**: do not read the stage.

---

## 2. The loot tactic's exit, exactly (question 2)

**The test 0x451920** (read whole):

1. seconds since `[[actor+0x54]+0x30]` (ticks x 1/1024) must be >= `[tuning+0xc34]` (default 4.0); what that time
   stamp is: **not read**.
2. Arcade rules object (0x508ef0), the actor is a ZFFActor.
3. `idx = 0x78f470(rules, actor)`, `rec = 0x7fd930(rules, idx)` - **the bot's OWN record**, not the player's.
4. 0x4519d4 `cmp al, 1 / jb` -> stage 0: return 0.0.
5. 0x4519dc `cmp al, 3 / jne` -> **exactly 3** (there is no stage above 3): `rules->vt[0x12c]()` (= slot 75 =
   0x5d52f0 = byte `[rules+0x1dc]`) `== 3` -> 0.0; `== 4` -> 0.0. In every other state a stage-3 bot loots on.
6. five candidates from slot 202 (0x8b94d0); none -> 0.0. Only THEN `rules->vt[0x1c8](idx) & 0x2000` ('busy
   looting') -> 1.0. So the stage test comes BEFORE the 'busy' test: a bot in a grab also gets 0.0.

So yes: 0.0 on every call for as long as the state is 3 or 4 - and **1.0 again the moment it is 5** (and 7, 0, 1, 2).

Slot 202's window (read; tuning defaults from the constructor at 0x530aa8..0x530b4a): an object of the first list
must be within **800** (`+0xc1c`) with |height| <= 400 (`+0xc20`), of the second within 400 / 200 (`+0xc24`,
`+0xc28`), not taken (0x4536e0), `[obj+0x6c]` set. **A bot is only ever held by loot within 8 m.**

**Who calls the test, and when**: the running goal's loop, not a timer. `ZDefendPosition` run 0x85f6c0 (also
`ZSoldierIdle` 0x77bbd0, `ZAttackTarget` 0x4f4460, `ZSoldierAttack`, `ZFollow`, `ZProtectGoal`, `ZPsychoticGoal`):
at 0x85f8e2..0x85f933 it walks ONE of the soldier's lists (`+0x610`, or `+0x604` when `[soldier+0x4fc]` and
`[soldier+0x6fc]`) in order, calls `vt[0x2c]`, and runs the **FIRST** tactic whose test is > 0.0 as a child, to the
end of that tactic's pass; then loops (0x8602bc). Only when no tactic wants to run does the goal move to its own
defend place. That is the mechanism behind 'the tactic beats the Defend orders'.
List order (slot 17 = 0x6ab250, the push_backs at 0x6abc9e.. for `+0x604`, 0x6ac04e.. for `+0x610`):
`... BecomeTraitor (+0x5f8), BoardEscapeVehicle (+0x5f4), eight or nine other tactics (not named here), Loot (+0x5f0) LAST`.
So Board, once its test is true, also goes before whatever those others are - a raised bot heads for the vehicle
first, as a stock stage-3 bot does.

**The Board tactic** (test 0x4faf60, read whole): state 3 / 4 -> boarding position (0x5aeb00: the boarding OBJECT's
own place, not +500), `stage >= 3` (0x4fb064), a path of more than one node -> 1.0. State 1 / 2: the same, but only
when the rules' countdown (`vt[0x130]`) is under 2.0. Other states: 0.0. Its action 0x82f970 runs there and, within
300 units (squared 90000.0 at 0xd19a28), calls 0x74d7f0 -> the boarding rule. Neither test nor action reads the grab.

**The grab is the rules' business, not the tactic's** (read whole: 0x8e8750, 0x727cb0, 0x522090):

- `ZLootTactic` has NO exit code: its slot 3 is `ret` (0x66b570); slot 12 (0x640910 -> 0x474450 -> 0x7bea40) only
  pops goals. Nothing of the tactic knows `rec+0x15`.
- start 0x8e8750 (from slot 201 = 0x56f6e0, called by the money object's trigger): `rec+0x15` 0 -> 1, `+0x1c` = the
  object, `+0x18` = the time, status flag 0x2000 at `[score + 0x1d4 + 4 * idx]`; and `+0x15` **2 -> 1 for the same
  object** - the re-arm.
- 0x727cb0(idx, dt), called every rules update for every record with status 0 (0x58b2c0 <- 0x74bc48), jump table
  0x728204: state 1 -> object taken, `[obj+0x64] != 1`, or for an AI `[actor+0x576] != 1` -> clean up; else
  `+0x15 = 2`, timer down, money when it runs out. **State 2 (nobody re-armed since the last update) -> 0x7281ba:
  0x522090 (the object's looter bit, `+0x15`, `+0x18`, `+0x1c` all cleared), `vt[0x198](idx, 0)`, flag 0x2000
  cleared (0x7281f0).**

So a grab lives only while the bot stands in the money object's box. When the test turns false the bot is taken
elsewhere by the next tactic or the goal, steps out of the box, and one rules update later the grab is cleaned up by
the rules. If nothing moves him, the grab simply finishes. **He cannot be left 'busy looting' for good.**
The boarding rule 0x6840a0 (read whole) tests: session state 0x19; vehicle state 3 / 4 (or 5 within a grace time);
for an actor, its record's status 0. No stage, no grab, no flag 0x2000.

---

## 3. The order for a bot that is looting (question 3)

**0x760e50** (read whole) with (place, soft 0, reset 1, 0), actor not held as a shield:
`[soldier+0x4fc] = soft2` (1 only when `[soldier+0xec]` and the place is within 250), `[soldier+0x720] = 0`,
0x412910 snaps the place into the defend block, `block+0x11 = 1`, then by the defend goal's state `[[soldier+0x648]+8]`:

- **running (not 0, not 4) and not soft -> 0x7bbf70(soldier)** (read): takes the FIRST element of the goal stack
  (`[soldier+4]`..`[soldier+8]`), sets its `+0x11`, pops everything down to and including it (0x7bea40 -> 0x5ca0b0)
  and pushes it back with `+0x12 = 1`. A Loot pass that was running as a child is popped: **interrupted**, at its
  current yield.
- **idle (0 or 4)**: `vt[0x1b4]()`, 0x6cabf0(defend goal, 150), `vt[0x50](1)` = 0x6353a0 -> 0x81eb90: the soldier
  re-selects its root from the queue `[soldier+0x48]`..`[+0x4c]` (16-byte entries {goal, priority}); if the best is
  not the root, the whole stack is popped (with an empty-stack test, 0x81ec3a) and the new root pushed. So here the
  order is **queued and wins unless a goal of higher priority runs**; then it waits behind it.
- running and soft: nothing more.

It is never dropped. What happens next decides everything: the restarted `ZDefendPosition` walks the tactic list
again BEFORE it moves - with stage < 3 Loot's test is still 1.0 and the bot is back at the case (what L8..L11
measured); with stage 3 and the vehicle waiting Loot is 0.0 and Board 1.0.
An order costs the bot 0.1-0.3 s (the random wait at 0x85f709..0x85f752 after `block+0x11`) and a stance change.

**`vt[0x1b4]` = 0x6e49b0 is not an interrupt** (klescort.c's header says 'every running goal is interrupted'): it
reads eleven goal pointers (`soldier+0x638`..`+0x664`, the defend goal `+0x648` among them) and for each calls
0x8883d0(goal, 150), which finds and ERASES the pair {goal, 150} in the queue vector (0x4d87b0 / 0x7ce220 /
0x4d0b20 taken as find / remove / erase from their call shape - not read inside). It pops nothing and calls no
virtual function.

**Should BoardAll call it first, as the rules do? No.**
- Not needed: the not-soft order already cuts the running tactic (0x7bbf70) or calls 0x1b4 itself (idle case).
- The rules pair it with a SOFT order, which BoardAll must not use (it ends the chain's waiting Defend step at once;
  klescort.c's own reasoning holds).
- With a running defend goal and a not-soft order, a 0x1b4 call beforehand would erase the defend goal's own queue
  entry and nothing would put it back (0x760f25..0x760f2b only calls 0x7bbf70). What the next root selection then
  does to the bot: **not read to the end** - one more reason not to add it.
- As a call it would be about as safe as the order (it only touches the soldier's own vector), with its own code
  compare.

**One precondition the hook does not test** (defect S1): 0x7bbf70 reads `[[soldier+4]]` with no empty-stack test (the
only one, 0x7bbf97, is on the network-client branch) and 0x5ca0b0 answers an empty stack with `int3` (0x5ca0bf).
'Defend goal running' should imply 'stack not empty', and the hook's 63 live calls (L11, E1, E3) did not fault - but
BoardAll widens the callers from one or two escorts picked at a calm moment to every bot at whatever it is doing
when the vehicle arrives.

---

## 4. The code (question 4, brief)

Read line by line: `kle_board_all`, `kle_tick`, `kle_init`, `kle_bot`, `kle_callable`, `kle_order`, `kle_boarding`,
klbot.c's `klb_read` / `klb_put8` / `klb_still` / `klb_level`, klhook.c's `klh_may_write` / `klh_data` / `klh_tick`.

Holds:
- No write with `BoardAll=0` (`kle_tick`: `if (kle.all && waiting)`), none in a dry run (`!kle.dry` guards
  `klb_put8`; `kle_order` returns 2 before the call), none with `BoardAllStage=0`.
- Not off the game thread (`kle_tick` returns at `!game_thread` before anything acts), not on a stock or unknown
  level, not without the Steam guard (`klb_level`), not outside session state 0x19.
- Index: `i < s->n && i < KLB_NREC`, and `klb_read` refuses `n > KLB_NREC`.
- `klh_data` in both builds: a crew record is heap, `klh_kind` returns 0, `klh_may_write` returns 1 under SHIP and
  SESSION alike; the page must be committed and writable. SHIP and TEST differ in nothing BoardAll uses.
- A bot at stage 3 by itself is not touched (`r->stage >= 3 && !all_raised`). The reason given in the comment ('the
  rules have sent it') is wrong (section 1), the outcome is right: the Board tactic takes it.
- Visits: a hook that starts mid-wait, or a round change (`memset(&kle_r)`), begins at visit 1 and acts once. Log:
  one 'stage' line per record and round, one 'sent' line per record and visit, one 'no order yet' line per record.
- `kle_bot` does not refuse a bot because it is looting: the grab machine itself requires `[actor+0x576] == 1`
  (0x727fa9). And if the order cannot be given, the stage byte alone is enough (section 2).

Found (all in section 7): the record is not re-checked before the write although game code ran since the snapshot
(S2); `kle_boarding` failing returns without a word (S3); an escort released in the same pass is ordered twice, and
`EscortBoard=0` no longer keeps a released escort where it is (N4); `all_told` is a char that wraps after 256
failing passes (N5); the gate's line says 'escort' when only BoardAll is on (N6).

---

## 5. A safer form (question 5)

- **Making the object 'taken'**: no. 0x4536e0 is read by the human's own looting, by the candidate list, by the
  route chain's `TriggerLootDepleted` (0x79f390) and by the grab machine; there are 363 money objects on this map.
  It changes the level's loot, not one bot.
- **Calling 0x5dd890(rules, actor, 3)**: possible and clean - but it IS the byte write and nothing else (section 1),
  with the same consequences at R2..R5. It would add a second game call with its own preconditions (the actor's
  vtable slot +0x30 is called twice) to save one guarded heap byte. No gain in safety.
- **Slot 194**: no. It is the vehicle's state change itself (it stores `[rules+0x1dc]`, timers, announcements, the
  boarding object), and its order pass does not even run for states 3 / 4.
- **`vt[0x1b4]` + soft order, as the rules do**: no (section 3).

**Recommended: the form as written - the stage byte through the hook's guarded write, then ONE not-soft order - with
the record re-checked by `klb_still` just before the write (S2) and the empty-stack test in `kle_bot` (S1).** Reasons:
it is the smallest change that flips both of the game's own tests (Loot off at 0x4519dc, Board on at 0x4fb064); it
leaves exactly what the exit trigger leaves on an AI record; the order half is the call that has run live; and the
byte half needs no assumption about calling conventions.

What this form cannot do, whichever way the byte is written: it acts only in the 8 s the vehicle waits, and Loot
returns when it leaves. If L12 shows bots caught again between visits, the lever to look at next is the Loot test's
own gate, the float `[tuning+0xc34]` (default 4.0, read at 0x45195b): above any possible time it switches the tactic
off for everybody and the route chain's orders win again. NOT read: what the time it is compared with measures. NOT
proposed for now.

---

## 6. The live check L12 (question 6)

**What the numbers say to expect** (measured, L11_DM02.log, same build): the vehicle waits 8.0 s, drives off 8.4 s,
is away 6 s, comes 7.1 s: one visit every ~29.5 s, five visits (03:14:44 .. 03:16:50), then state 0 for good - it
is only called by somebody standing in the exit trigger, and the last such bot had boarded. Bots walk about 3.3 m/s
(bot 7: 1815 units in 5 s). From (-1278, 500, 1884) to the boarding place (-352, 0, -8268) is about 119 m by the
stairs = ~36 s. So **the two held bots cannot board at the visit that frees them**; each wait gives them ~26 m, and
between waits they walk on only while no untaken money object is within 8 m. Boarding at visit 2-5 is the realistic
success; 'held again at another case after the last vehicle left' is the realistic failure, and is no fault of the
hook's safety.

Also check the first lines: L12_DM02.ini has **two `[Bots]` sections**; Windows reads the first (BoardAll=1,
Escort=1). The `board: on` line of the aborted 03:22 run confirms it took.

**Success, in this order:**
1. `board: on; BoardAll=1 BoardAllStage=1: ...` without `DRY RUN`; no `escort: ...: no escort here` line; no
   `escort: the tick is not on the game's thread`.
2. Where the `bots:` line first shows `van 3` (the hook acts within 0.5 s of the state change; the bots line is
   written at most once a second, so the order of the lines may vary): for every bot in play under stage 3
   `board: record N (stage S): the vehicle waits (state 3): heist stage set to 3`,
   klbot's `bots: record N (bot): heist stage S -> 3` (a jump past 2 is the hook's signature), and
   `board: record N at (x, y, z): sent to the boarding place (-352, 122, -8268), the game set (-352, 0, -8268); visit 1 of the vehicle`.
3. In the 5 s position lines (`hop: bot N stage 3: node (...)`) the two held records leave their place within the
   wait: 15 m or more between two samples, towards the stairs.
4. At later visits `board: record N at (...): sent ...; visit K of the vehicle` from a place nearer the vehicle each
   time, then `bots: record N (bot): aboard` and `status6`.
5. The last `bots:` line has no `bot in-play g1` / `g2` left.

**Faults:**
- `board: record N (stage S): the stage byte was not written: it is left alone`.
- `board: record N: no order to the boarding place yet: <why>` with no `sent` line for N in that visit - `<why>` is
  kle_bot's reason; `board: record N: NOT sent to the boarding place: <why>` - kle_callable's.
- `van 3` in the bots line and no `board:` line at all: the gate, the thread, or `kle_boarding` (silent, S3).
- a raised record whose place does not change during the whole wait while its money keeps rising: the Loot tactic did
  not let go - that would contradict section 2 and wants a dump.
- places that go BACK to the same case after `van 5`, with no net gain over two visits (section 5's limit).
- `bots: record N: traitor flag SET` for a raised record (cannot happen on Arcade level 1 without Tune).
- any fault / assert line. Addresses that would point here: **0x5ca0bf** (int3: a pop from an empty goal stack,
  under 0x7bea40 <- 0x7bbf70 <- 0x760f2b), anything in 0x760e50..0x760f69 or 0x412910 (the order, the mesh snap),
  0x4faf60 / 0x82f970 (Board test / action, pathfinder calls), 0x727cb0 (the grab), 0x6840a0 (boarding).
- after the seventh bot has escaped: what the session does with the idle human (`s19` changing, a round-over
  count). With BoardAll nobody is left behind in play, which is new for this map.

**In a dump:** rules = `[[0x168e9e4]+0x54]`; record i = `[rules+0x348] + i * 0x7c`: +0x78 stage, +0x10 status, +0x15
grab state (0 / 1 / 2 / 3), +0x1c the object, +0x18 the timer, +0x79 flags; `[[rules+0x5f8] + 0x1d4 + 4 * i]` flag
0x2000; `[rules+0x1dc]` state, `[rules+0x1d8]` timer, `[rules+0x1e0]` boarding object. Soldier = `[actor+0x77c]`:
goal stack `+4`..`+8` (empty?), root `+0x74` / priority `+0x78`, queue `+0x48`..`+0x4c`, `+0x4fc`, defend goal
`+0x648` (its `+8` state, `+0x11`, `+0x12`), defend block `+0x64c` (place, `+0x11`), Loot `+0x5f0` (candidates
`+0x14`..`+0x24`, `+0x28`, `+0x2c`), Board `+0x5f4`, lists `+0x604` / `+0x610`. `[actor+0x576]`, `[actor+0x770]`,
`[actor+0x8f0]` (1 = taken out of play by boarding).

---

## 7. Defects

No 'must'.

**S1 (should) - klescort.c `kle_bot`: the order's not-soft path needs a goal stack that is not empty, and nothing
tests it.** Evidence: 0x7bbf9f `mov ecx, [ebx+4]` / 0x7bbfa7 `mov edi, [ecx]` with no test; 0x5ca0b7..0x5ca0bf
`cmp [esi+4], [esi+8] / jne / int3`. Fix, after the soldier's vtable test:

    { DWORD sb = klh_rd32(soldier + 4), se = klh_rd32(soldier + 8), g0 = 0;
      if (!sb || se <= sb || ((se - sb) & 3) || !klh_rd(sb, &g0, 4) || !g0) { strcpy(why, "its soldier runs no goal now (empty goal stack; 0x7bbf70 has no test for that)"); return 0; } }

(It also refuses in the idle case, where the game would cope (0x81ec3a); BoardAll tries again every pass, the escort
at its next order.)

**S2 (should) - klescort.c `kle_board_all`: the stage is written from the snapshot without klbot.c's own re-check.**
`kle_order` for record i-1 ran game code (pathfinder, goal pops) between `klb_read` and the write for record i;
klbot.c's rule is 'the record as it is NOW, checked again just before a write' (`klb_still`). Fix:

    if (r->stage < 3 && !kle_r.all_raised[i]) {
        BYTE fl = 0, st = 0, cur = 3;
        if (kle.all_stage && !kle.dry) {
            if (!klb_still(s, i, &fl, &st) || st || (fl & 2) || !klh_rd(r->at + 0x78, &cur, 1)) continue;   /* gone, aboard, dead or turned since the snapshot */
            if (cur < 3 && !klb_put8(r->at + 0x78, 3, "crew record: heist stage 3 (the vehicle waits; ZLootTactic lets go at stage 3)")) { ...as now...; continue; }
        }

**S3 (should) - `kle_board_all` returns without a line when the boarding place cannot be read**, so 'no board: line'
in the live check has three possible causes. Fix: a `told_noboard` counter in `kle_r` and one line
`board: the vehicle waits (state %u) but the rules have no boarding object ([rules+0x1e0]): nothing is written or ordered`.

**S4 (should) - the comments state as read in the exe something the exe does not do.** klescort.c header ('when the
vehicle starts to WAIT (state 3 / 4) it walks the crew records ...'), RELEASE ('the rules' slot 194 has just ordered
it'), the BoardAll key ('the rules send only stage-3 AI aboard (0x8fb04c)'), `kle_release` / `kle_board_all` ('the
rules have sent it'), klhop.c 58-59; and '0x6e49b0: every running goal is interrupted'. Text: 'slot 194's pass runs
when the state becomes 1, 2, 5 or 6 (byte table 0x8fb0a0), never 3 or 4; while the vehicle waits a stage-3 bot is
taken aboard by ZBoardEscapeVehicleTactic (test 0x4faf60), second in the soldier's tactic lists; 0x6e49b0 erases the
eleven behaviour goals' {goal, 150} entries from the soldier's queue'. The BoardAll ASSUMPTION line can become a
statement: stage 3 is read in five places (section 1), two of them beyond loot and boarding.

**S5 (should) - klbot.c Van with `VanLeftBehind=1` takes 'stage >= 3 in play while the vehicle drives out' as 'stands
at the vehicle'; BoardAll makes that true for bots 100 m away.** With `Van=2` everybody aboard would be killed at
nearly every visit. Not set in the owner's ini today. Fix: skip records BoardAll raised (a forward-declared
`static int kle_raised(int rec)` returning `kle_r.all_raised[rec]`, tested in the `who` loop), or say in both key
texts that the two must not be combined.

Notes:
- **N1** a raised bot shoots the police at `[R+0x1c]` (0.5 at level 1-3) while the human is at another stage; R3.
- **N2** a raised bot gains the traitor tactic's 3 stage points (levels 4+, or Tune) and passes Backstab's stage test.
- **N3** kltalk says a 'Stage2' line for a bot that never left.
- **N4** an escort released in the same pass is ordered by `kle_release` (or the mode-2 branch of `kle_tick`) and
  again by `kle_board_all` within 500 ms; harmless. `EscortBoard=0` is overridden by `BoardAll=1`.
- **N5** `all_told` is a `char` incremented on every failing pass: the line comes again after 256 passes (128 s).
- **N6** with `Escort=0` the gate's line still says 'escort: ...: no escort here', and 'escort: you: ...' is logged.
- **N7** `re/balance.md` 1c and klbalance.c (lines 31, 67) have the `+0x1c` row's attacker and victim swapped.
- **N8** on a map where the bot has no path to the boarding object (the bank's two mesh parts, Retomoto's tower)
  Board's test stays 0.0: the bot stops looting for 8 s and is left with a defend place it cannot reach. What
  `ZDefendPosition` does then: not read. Try L12's map first; do not make BoardAll a default for all five maps on
  the strength of L12 alone.

## 8. Not read

What `[[actor+0x54]+0x30]` is (the time both tactics' tests start with); the priorities of root goals other than
150 and who else calls soldier slot 20; what the rules' own `0x1b4` + soft pair leaves behind when the defend goal
runs; who reads the client-block bits; rules slots 47 / 48 beyond those bits; `ZDefendPosition` with an unreachable
place; the insides of 0x4d87b0 / 0x7ce220 / 0x4d0b20; what ends an Arcade round once every bot has escaped.
