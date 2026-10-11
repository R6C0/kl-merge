# AI heisters and the civilians who carry money

2026-10-11, track P; second form after the adversarial review (`re/bots_civs_review.md`: ACCEPT WITH FIXES; section
10 says what was done with each point). **OFFLINE: the game was not started, nothing was written into the Dog Days
folder, nothing was committed. NOTHING HERE HAS RUN IN THE GAME.** New: `tools/kl_fa_bots_civ.py` (a step on a
finished bots build), builds `<work>\build\z_civ\M01 M02 M03 M06`, `_money_only\M02`, `_before\M02` (logs:
`z_civ\logs\`; of the first round only the logs are kept, `z_civ\round1\logs` - its builds were deleted, their
`_5_Take` named the actor), this note. No file of another track was edited;
no hook part was written (section 8).

**EVERY z_civ BUILD IS A TEST BUILD. None is a candidate for the owner's tab** before the runs of section 6: on Late
Night Opening the step swaps track A's proven removal of the clerks' money (the clean round W1_DM02) for stored
field 11, which narrows the trap of runs L8 / L10 and does not close it (section 5, 'the window').

Words: **read** = disassembled at the address given (kl2.exe, base 0x400000); **measured** = counted on the build
files; **live** = from the hook's logs of earlier runs; **ASSUMPTION** / **GUESS** = fits the evidence, not proven;
**not read / not established** = said so. Background: `re/bots_loot.md` (track A: the grab, the loot window).

The owner, 2026-10-11: *'they need to know how to kill civs some of them otherwise they cant get money'*.

## 0. Short answers

1. **By the code a civilian does not have to die for her money.** Nothing on the take path looks at her: the trigger
   on her group fires for every player and every Ally actor inside its ball (0x626ec0, read whole: it walks ALL
   objects in reach, the civilian herself is simply passed over), the money object does not know her (0x6cdb40), the
   rules test the TAKER only (0x56f6e0: alive, has a crew record). There is no 'surrender', no squad event and no
   message in between. So the converter's mis-paired 'attacked' list of three Hot Coffee squads (track C) is **not**
   why a clerk never paid: no list of her squad is on the path.
2. **Why the watch shop's clerk never paid a bot is still not established** (section 2). What a death changes for
   certain is only that she lies still.
3. **No bot shoots a civilian by itself, and the game has a routine for it that no level of either game uses:**
   `KillCiviliansBehaviourRout` (section 3). Its goal has every soldier of the rout's squad lay cover fire on every
   living member of a NAMED squad until all of them are dead, then fires its NEXT. That is the mechanism built here.
4. **Built:** two killers a civilian, by role (point man, flankers, runner - never a looter or the rear guard).
   AFTER the loot wait of the stop nearest to her (the shop is empty then; the owner: 'they might go back for it') a
   killer walks to where she IS, is told to shoot her, stands on her money's GROUP node (where the take trigger is)
   and is sent on after 12 s whatever has happened. The chain itself runs through three timers, so no order of this
   step can hold a bot up. The other bots get nothing.
5. **The civilians' money is back in the level** (Late Night Opening: 215,000 that track A had taken out), for the
   human as before, with stored field 11 set: the AI's own loot TEST passes such an object over; the take never
   reads the field. **That narrows the hold of runs L8 / L10, it does not close it** (re/bots_loot.md 6: the loot
   ACTION never reads the field): every squad of every map has Defend places inside a money civilian's loot window,
   and the tool's check now says so per squad - a FAIL that only `--accept-window` turns into a NOTE.
   `z_civ\_money_only\M02` (the money and the field, no step) is the first thing to run: it also answers the one
   question nobody can answer offline - is a bot that stands in her ball PAID.
6. **A bot's civilian kill costs nobody anything** (read, section 3): the rules' death notice scores and penalises
   a PLAYER killer only; the traitor bookkeeping runs for a victim with a crew record only.
7. **The price:** two controller classes that have never run in an Arcade round - `KillCiviliansBehaviourRout`
   (in no level at all) and `DefendNPCPosBehaviourRout` (37 uses, story levels only). `kl_fa_bots.check` FAILs
   them by its rule 'nothing the levels do not already run', and `kl_fa_bots_dyn.check` FAILs the way they are
   started. Both are meant, both are said aloud by `kl_fa_bots_civ.py check` (section 7). **A z_civ build goes on a
   TEST tree first.**

## 1. How a civilian's money is taken (all read; the table of re/bots_loot.md 1 holds)

| step | code | what it tests |
|---|---|---|
| the trigger on her GROUP node | `ZTriggerBox2` update 0x626ec0 | asks the tracker (0x5891f0, gamedata+0x159c) for every object within the box's reach of the node's origin, **one after the other until the list is empty** (0x626fe6 `inc` .. `jmp 0x626f43`). For each: a player (class mask 0x1548c7c), or in Arcade (0x7f6850) an actor (class mask 0x1547b24) whose team `[[actor+0x54]+4]` is 2 = Ally; with field 3 set ('people only', every money trigger of our builds) everything else is skipped (0x626fbd). Then the inside test 0x68d030 -> 0x783e60 and the message. The civilian is an actor of team Neutral: skipped, nothing more |
| inside | 0x783e60 | a ball of field 2 + 40 (75 + 40) round the node's **centre point** (entity `+0x30..+0x38`, a point in the node's own frame, brought to the world through the parents by 0x7b3020) against the visitor's centre point: flat distance, then the height |
| the money object | `ZOnlineMoneyCtrl` slot 26, 0x6cdb40 | hidden node / state 2 or 3 / inactive: dropped. Nothing about a person |
| the rules | `ZGameRulesHeist` slot 201, 0x56f6e0 | Arcade; the TAKER: an actor that is not dead (virtual +0x3d0 = 0x87f870: byte `+0x576 == 0` means dead) and has a crew record (0x78f470), or a player (a police player goes another way: `[player+0x2723]`, 0x56f769) |

Before / after: byte `+0x6c` ('in play') is set from the controller's init for every type and cleared only when the
object is taken or gets `'Deactivate'`; `+0x74` (active) is set from the start for TYPE_NORMAL, which every civilian's
money is; the amount `+0x34` falls by parts of field 4 (20,000) every field 5 seconds (0.6 .. 1.0) while the taker
stays inside. The candidate filter of the AI's loot tactic (0x8b94d0) is 'not taken and `+0x6c` set'; its test
(0x451920) also passes over an object with stored field 11 (`+0x5c`) unless an enabled KickDoor is within 500 / 250.

**Can the human take it on the tab's builds today?** Hot Coffee (`z_route3\M01`) and Withdrawal (`z_cover3\M03`):
the money is in the level (40,000; 20,000 + 10,000), and by the code he takes it by standing in the ball - no run
shows it, and the owner's 'they dont loot the warehouse people on diner' (2026-10-10) was about the bots. Late
Night Opening (`z_loot3\M02`): no - track A took the three clerks' 215,000 out for everybody.

## 2. Why the clerk did not pay - what this track adds, and what stays open

- **Not the squad lists, not a missing death.** Section 1: none of it is on the path.
- **Not 'the trigger serves only the first object it finds'** (a guess of mine while reading: the civilian is the
  nearest object to her own trigger): the loop goes on after every object (0x626fe6).
- **The stock precedent for 'the place of an NPC'.** `DefendNPCPosBehaviourRout` (0x5ed640) and the loot tactic
  both take a node's ORIGIN through its parents (0x8d3150). Stock's four DefendNPCPos steps with a target name the
  actor's GROUP (`AI!Friendly!Glazer\Glazer_ALLY__`, the ZGROUP above the `Ground` actor), not the actor - which
  would make sense if the GROUP is what the engine moves. **Against that** (the review): the kill goal takes a
  member's place from the ACTOR's own node (0x49a62e .. 0x49a634: `[[member+0x40]+4]` -> 0x7b3020), so the actor
  node is what the game itself treats as 'where she is' - which points at the group staying at the post, and so at
  track A's explanation A ('the money is where she stood and she had left'). **Which of the two nodes moves was
  still not read**; the group's stored bounding kind is `BOUNDING_DynamicAutoAssign` on every one of these groups.
  The step no longer depends on it: the walk names the actor, the stand names the group (section 5).
- **Live, for comparison:** on the park ALL money is on armed people's groups (3,350,000, the same form: group +
  OnlineMoneyCtrl + TriggerBox2 75), and the bots do earn it (run I4_DM06: bot 1 750,000, bot 3 250,000, bot 5
  50,000). So a bot CAN be paid from a person's group. Whether those men were dead then is not in the log.
- **So:** what separates the paying bosses from the clerk who did not pay is not established: dead against alive is
  one candidate (the owner's own reading, 'kill civs ... otherwise they cant get money'), hidden is another. The
  build tries the first and loses nothing if it is the second: the one run of section 6 tells them apart.

## 3. Do bots shoot civilians? The game's own kill routine

- A bot is an actor of team Ally (2); a civilian is Neutral (3) (`ZFFActor` field 19; measured: every civilian of
  the four maps). No rout of any stock bot squad names a civilian, and no stock Fragile Alliance level has money on
  a civilian (re/bots_loot.md 3). That an Ally soldier never picks a Neutral as a target by itself was **not read**
  (the target choice, `ZAttackTarget`, is unread: re/bots_dynamic.md); it fits every run - six bots beside the clerk
  for 150 s and her money still whole.
- **`KillCiviliansBehaviourRout`** - registered for ZGROUP in both games (kl2 vtable 0xbcde3c, properties 0xd05594),
  used by **no level of either game** (searched: the .prp of all 59 Dead Men and 44 Dog Days archives). Stored
  fields: 0 s (member +0x48) = a squad's group; 1 refs = NEXT; 2 b (property offset 0x3e); 3 b (0x3f).
  - init (slot 14, 0x4af120): resolves field 0, asks that node for its `ZSquadScript` controller, takes the squad
    object `[+0x3c]` and makes a `CPPScript::ZKillCiviliansBehaviourGoal` (vtable 0xbcdecc, 0x24 bytes) with it at
    `+0x20`. No ZSquadScript on the named node = no goal, and the rout does nothing (slot 34, 0x8f6b80, tests it).
    **No null test** on the resolved node (0x4af12c) nor on the squad pointer (0x4af15c; it is made in
    `ZSquadScript` slot 13, 0x6316b0): a null squad would be a read of `[0+0xc0]` at 0x49a5ce when the rout starts.
    That every controller's slot 13 runs before any slot 14 is likely, not proven - so `check()` FAILs a kill rout
    whose squad does not stand EARLIER in scene order (in the builds: nodes 1 / 9, 186, 7123 against 15,323 and up).
  - **a civilian is a member of her squad's list** (the review read it): `ZSquadScript` slot 14 (0x7b3790) looks
    an actor without a soldier (`[actor+0x77c] == 0`) up in the registry gamedata+0x15ac (0x664850) and adds an
    object of type "Civilian" to the SAME list `+0xc0 / +0xc4` (0x7b39f1 -> 0x48c480; 12 at most; a squad with
    soldiers AND civilians is an int3, 0x7b3a24). `+0x40` of the member = the actor for both kinds (by likeness of
    the shared base slots; the ctor was not read).
  - the goal (slot 2, 0x49a5c0, read whole): for every member of the NAMED squad (`[squad+0xc0]` count, `+0xc4`..):
    while its actor is not dead (virtual +0x3d0): take the point (0, 50, 0) of the actor's node in the world
    (0x7b3020); for every soldier of the rout's OWN squad (0x8d0250) call virtual +0x14c = 0x831850 (no target
    object, that point, 3.0); wait 2.0 s (0x630b50 / 0x55b9f0); again. When every member is dead: done
    (0x5c6e70 -> the rout's NEXT, 0x8df0d0).
  - 0x831850 with a point and no object: the soldier's `CPPScript::ZCoverFire` object (`soldier+0x654`, made at
    0x6ab7ee = 0x5167d0, vtable 0xbd04dc) gets the point and the seconds (0x717f90) and is put on the soldier's
    list with weight 0xa0 (0x637800). **So: cover fire at where she is, 3 s at a time, renewed every 2 s, until she
    is dead.** What `ZCoverFire` does when the soldier has no line to the point was not read. One branch is unread
    too: when the soldier's task at `+0x5ac` is running (state not 0 / 4) and 0x4c53b0(point) answers 1, the point
    goes to THAT task (0x809830) and no cover-fire task is queued.
  - **It is fire at a POINT, not at a person:** 50 above her feet, for 3 s, no line-of-sight test read. Whoever
    stands between - the human, another bot - can be hit (live check C1 looks for it).
  - **a member that leaves the list** (read for the review's point 7): the two routines that take a member out,
    0x5230c0 (one member: finds its slot through 0x6fd800, writes 0, clears `[member+0x4f4]`) and 0x7bf950 (a
    sweep: every member whose actor's `+0x576` is not 1 ..), both ZERO THE SLOT and leave the count `+0xc0`; the
    kill goal tests the slot for 0 before every use (0x49a5f6) and again after every 2 s wait (0x49a6a9 ..
    0x49a6ad), so a civilian taken out that way is passed over and the goal ends when no slot holds a living
    member. NOT READ: who calls the two (is a civilian that has fled taken out at all), and whether a member can be
    freed WITHOUT its slot being zeroed - that case would be a call through a dead pointer every 2 s.
  - It has EVERY member of the named squad shot: each money civilian of the four maps is a squad of her own
    (measured), which is why the tool refuses a squad with more than one actor.
- **A bot's bullet on a civilian** goes through the NPC hit routine and the Arcade dial like any other
  (re/balance.md: row R+0x04, 'an Ally NPC hits an NPC', and R+0x1c when the bot's heist stage is not the human's).
  The owner's `Risk=2` writes 1.0 for both. A civilian's health was not read.
- **Penalty / traitor (read for the review's point 7):** the rules' death notice, `ZGameRulesHeist` slot 16 =
  0x485740 (victim actor, killer reference):
  - the crew bookkeeping 0x6706b0 (who becomes the traitor, re/bots_fight.md 2.4) is called only when the VICTIM
    has a crew record (0x485783 -> 0x78f470; `cmp ebx, -1; je 0x485821`). A civilian has none: **no traitor flag,
    no yellow card, no 'wanted' from her death, whoever killed her.**
  - everything after that - kill score, the on-screen line, the penalty - runs only when the KILLER is of the
    player class (0x485829 .. 0x48583f: class mask 0x1548c7c, else straight to the routine's end 0x485c18).
    **A civilian killed by a bot is not counted against anybody.**
  - a HUMAN who kills her: victim without a crew record and without a soldier (`[victim+0x77c] == 0`, 0x485884 ..
    0x485890) -> `[score+0x2c] += [tuning+0xc18]` (0x485892; the tuning object at [0x168d7c0]). That is the only
    score write for such a victim; that it is the score page's 'Civilian kills' line is by its place (ASSUMPTION;
    the number at +0xc18 was not read). A victim with a soldier counts as a kill (`+0x10`, `+0x14`).
  - NOT SEARCHED: other readers of a civilian's death (a police alert, a squad event). Nothing in the traitor
    tuning that klbot.c logs names civilians (stage terms and money only).
- **Civilians that flee:** `ZCivilian` {field 0 = 9000 / 8000 / 7000 on Late Night Opening, .., 5.0, 10.0, 1.0 x 5};
  field 0 goes to `civilian+0x54c` (0x5fa107) and is what the squad's wake-up asks for (slot 76, 0x56cbf0). Each map
  has a `CivilFleePoints!` list (ten on Late Night Opening, all on the ground floor; the clerks stand on the upper
  one). When and where a civilian runs was not read; the step does not depend on it (it walks to the ACTOR).

## 4. The other rout: `DefendNPCPosBehaviourRout`

37 uses in the story levels (enemy squads), none in a Fragile Alliance level. Fields: 0 refs NEXT, 1 b (0x3e), 2 b
(0x3f), 3 f (member +0x48), 4 s (member +0x4c) = an object. Goal `CPPScript::ZDefendNPCPosBehaviour` (vtable
0xbceb5c; slot 2 = 0x5ed640, read whole): for every member of its squad with `[actor+0x576] == 1`: resolve field 4,
take its origin (0x8d3150), order the member there (virtual +0x13c = 0x760e50 with (place, 0, 1, 0): the order the
heist rules use for 'go to the boarding box' and klescort.c for the escort - live in runs E1 / E3 / FO_J1), wait
field 3 seconds; and round again. **It ends, firing its NEXT (0x5c6e70(1)), in two cases** (the review; my first
note said 'never'): a pass that ordered NO member (0x5ed6e3) and a target that does not resolve (0x5ed692).
Harmless here: NEXT is empty on both DefendNPCPos routs of this step. Otherwise it ends when another rout becomes
the squad's goal.

**A new rout replaces the running goal, whatever its class** (0x791090, 0x7f6750, 0x4f3350 read whole by the
review): 0x791090 starts a goal only in rout state 0 or 4 and with `[squad object+0xbc] == 0`; 0x7f6750 takes the
running goal `[squad+0x154]` off the squad (0x4f3350: 0x5a0300 or 0x4052d0 / 0x8883d0) before it queues the new one
with weight 0xc8 (0x6cabf0) - unless the squad has no member left. The two goal virtuals it asks (slots 9 and 13)
are the same stub 0x429f30 for the Defend, DefendNPCPos and KillCivilians goals: the new classes take the path
every Defend step of the bots takes.

The bool at property offset 0x3e (member `+0x42`) of EVERY rout = **'start once'** (rout slot 26, 0x4ebed0: on the
start message 0x168d804 a rout with `[+0x42]` set and `[+0x40]` set - it has started before - is skipped, 0x4ebf01 ..
0x4ebf0b; `[+0x41]`, message 0x168d800, switches it off altogether). 1 on the three routs of this step, as on the
bots' Defend steps: no longer a guess.

The last bool of EVERY rout (property offset 0x3f, member `+0x43`): 0x791135 sets `[squad object+0xbc]`, and
0x79110d refuses every later rout while that byte is set. It is 0 on everything made here (stock's own steps: 0).

## 5. What is built (`tools/kl_fa_bots_civ.py`; its docstring has the node forms)

`python tools\kl_fa_bots_civ.py build <finished build> <out> [--donor <build with the civilians' money>]`

Per money civilian: the killers = the first two of the squads 2, 4, 5, 8 (point man, flanker, flanker, runner) that
have a loot place within 1,500 (`--reach`; 350 in height, `--reach-height`) of her post. Per killer the steps go
into the chain at `<X>`:

- `--when after` (the default since the review, point 6): `<X>` = the ONE node the stop's loot wait names as its
  next link (on these maps `0n0_SquadModifier_Loose_defense`). The killer loots the stop with the others, and when
  the wait is over (the stop is empty, or its deadline) he goes for her. Why: before the loot wait the bot stands
  inside the window of the store's own loot, and the loot tactic beat Defend orders there in run L10
  (re/bots_loot.md 4) - the 12 s could pass at the cases; afterwards the tactic has no candidate (her money is
  flagged), and it is what the owner said ('if they do end up getting the money they might go back for it').
- `--when before` (round 1; `z_civ\_before\M02`): `<X>` = the step that walks to the loot place of that stop.

    every reference to <X> inside the squad -> civ_<squad>_1_Timer_go
    civ_.._1_Timer_go      TriggerDelay2 0.1 s -> civ_.._3_Timer_shoot , civ_.._2_Follow
    civ_.._2_Follow        DefendNPCPosBehaviourRout {[], 1, 0, 1.0, her ACTOR node}      walk to where she is
    civ_.._3_Timer_shoot   TriggerDelay2 5 s   -> civ_.._6_Timer_fed_up , civ_.._4_Kill
    civ_.._4_Kill          KillCiviliansBehaviourRout {her squad, [civ_.._5_Take], 1, 0}  shoot until she is dead
    civ_.._5_Take          DefendNPCPosBehaviourRout {.., her money GROUP node}           stand where the money is paid
    civ_.._6_Timer_fed_up  TriggerDelay2 7 s   -> <X>                                     on, dead or not

- The chain is the three TIMERS. A rout of this step is only ever started BESIDE a timer's next link, and none of
  them is waited for: whatever a civilian does, the killer is back on the build's own chain 12.1 s later (the next
  Defend step replaces the goal: section 4). The owner's 'if nothing happens for like 5ish seconds they get fed up
  n move' is the 7 s (5 + the take: 75,000 = 4 parts of 0.7 s).
- The forms: the timers are the squads' own (`Timer_start_bots` of F07); the follow rout is stock L05's
  `...SQ_Mob_4thFloor_04\DefendNPCPosBehaviour` with its values and another object; **the kill rout has no stock
  form**: the node of a stock `FollowBehaviourRout` (L02; the same four stored fields with the same type handlers)
  with the controller's name replaced. Field 2 = 1 = 'start once' (section 4).
- **Which node each rout names** (the review's MUST 2): `_2_Follow` names the ACTOR node (`...\Ground`) - the node
  the kill goal itself reads her place from. `_5_Take` names her money GROUP - the node the take trigger's ball
  (0x783e60) and the money's hidden test (0x6cdb65) are on: if the group moves with her it is where she lies, if it
  stays at the post it is where the money is paid. Round 1 named the actor for both; then 'stand at the body' was
  inside the trigger only if she died within 115 of her post.
- **The civilians' money:** with `--donor` the `OnlineMoneyCtrl` and its take trigger are put back on the groups
  that `kl_fa_bots` option 'window' had stripped, byte for byte the donor's; then stored field 11 := 1 on every
  money civilian of the map, also on one nobody is sent to. bots.json: the entries move from `plan.edits.money_off`
  to `money_back`, so kl_fa_bots.check's NOTE 'money the build took out' stays true.

### The window: what field 11 leaves open, and what the check says (the review's MUST 1)

`re/bots_loot.md` 6 rejected field 11 by name: the loot TEST (0x451a88) passes a flagged object over, the loot
ACTION (0x7bc7d0) never reads the field - *'while any other candidate in the window passes the test, a bot whose
NEAREST candidate is the clerk's post runs to it and stands ... It narrows the trap, it does not close it.'*
`kl_fa_bots.check` cannot see this: its `cannot_take` answers '' for a flagged object before it reaches the civilian
rule, so its loot-window line reads '0 squad(s) ...' on every z_civ build. **`kl_fa_bots_civ.py check` now measures
it itself**: every Defend place of every branch of every squad against each money civilian's GROUP node, 800 / 400;
per squad the number of places inside, the nearest, and at how many of them her money is the nearest money object
of all (the action's worst case). The squads that are SENT to her are allowed (named in the line); **for every
other squad it is a FAIL**, which `--accept-window` (build or check; recorded in `civ.json`) turns into a NOTE that
begins 'WAIVED ... A TEST BUILD, NO CANDIDATE FOR THE OWNER'S TAB'. All six builds here are made with the waiver;
without it each of them FAILs (section 9 has the count).

Measured (`z_civ\<map>\civ.txt`; '#NN places / nearest / her money nearest of all at'):

| map | civilian | squads NOT sent to her (the FAIL) | sent to her (allowed) |
|---|---|---|---|
| Late Night Opening | watch shop's clerk 75,000 | #03 2 / 500 / 0; #05 2 / 126 / 1; #06 5 / 85 / 1; #07 3 / 251 / 0; #08 3 / 96 / 1 | #02 2 / 242 / 0; #04 5 / 37 / 1 |
| | jewel store's clerk 100,000 | #03 6 / 272 / 0; #05 18 / 229 / 0; #06 6 / 348 / 0; #07 3 / 464 / 0; #08 5 / 351 / 0 | #02 8 / 272 / 0; #04 5 / 263 / 0 |
| | cafe's clerk 40,000 | #05 1 / 672 / 0 | nobody |
| Hot Coffee | waitress 40,000 | #03 4 / 82 / 1; #05 4 / 362 / 1; #06 2 / 318 / 0; #07 10 / 140 / 2; #08 5 / 113 / 2 | #02 8 / 100 / 2; #04 7 / 374 / 2 |
| Withdrawal | hall's civilian 20,000 | #03 1 / 661 / 0; #06 1 / 600 / 0; #07 5 / 239 / 4; #08 1 / 771 / 0 | #02 3 / 184 / 1; #04 1 / 693 / 0 |
| | upper floor's clerk 10,000 | #02 6 / 637 / 4; #03 5 / 242 / 2; #04 8 / 91 / 6; #05 3 / 612 / 1; #06 2 / 90 / 2; #07 2 / 278 / 1; #08 3 / 621 / 2 | nobody |

(The review counted the watch clerk's money as the nearest of all at places of squads 04, 05, 06, 08 and
Withdrawal's `Civ_in_03` at places of all seven squads: the same picture.)

- Late Night Opening is where it matters: the tab's build (`z_loot3\M02`, the money taken out) is the one with the
  clean round W1_DM02, and z_civ puts 215,000 back on the field alone.
- On Hot Coffee and Withdrawal the tab's builds (`z_route3\M01`, `z_cover3\M03`) ALREADY carry this money WITHOUT
  the field - there every bot's own test takes it as loot (and both have run clean rounds: B1_DM01, C3_DM03, I1,
  I3). Against that the field is a gain; the check says so in its line.
- Whether the rest bites depends on what nobody knows: is a bot that stands in her ball PAID. If yes, her money is
  soon 'taken' and no candidate; if no, a round can end as L8 did (BoardAll does not help before somebody has
  called the vehicle). `_money_only\M02` answers it (section 6, C0).
- Written: `.prp`, `.gms`, `.buf`, `.oct` (slot ids; no tree changes its size, the `.prm` is not touched; `.rmi` /
  `.rmc` come out byte for byte on these maps). The four large blocks keep their size.

### Per map (measured; `z_civ\<map>\civ.txt`)

| map (source on the tab) | money civilians | killers | not sent |
|---|---|---|---|
| Late Night Opening `z_loot3\M02` + donor `z_route\M02` | `Civ_male_jewel\male_clerk` 100,000 (jewel store), `Civ_male_watch\female_clerk` 75,000 (watch shop), `Civ_girl_cafe\Clerk_Female` 40,000 (ground floor cafe) - all three put back | both clerks upstairs: Squad#02 (point man) and Squad#04 (flanker), after `020_Timer_done_looting` (jewel store) and `040_Timer_done_looting` (watch shop) | the cafe's clerk: no loot place of any squad within 350 in height of her - the human's alone |
| Hot Coffee `z_route3\M01` | `Waitress\Fat_Waitress_01` 40,000 | Squad#02 (point man, 100 from its loot place) and Squad#04 (flanker, 706), after `020_Timer_done_looting` | - |
| Withdrawal `z_cover3\M03` | `Civ_in_04\Civilian_in_Bank_01` 20,000 (hall), `Civ_in_03\Clerk_Female` 10,000 (upper floor) | the hall's: Squad#02 (887) and Squad#04 (838), after `020_Timer_done_looting` | the upper floor's clerk: no loot place within 350 in height |
| the park `z_route\M06` | none (its money is on armed people: the bots shoot and loot them already) | - | the archive is the source's byte for byte |

Each killer gets 12.1 s more in its chain per civilian (Late Night Opening: 12.1 s after each of the two stores).
Two more builds of Late Night Opening:
- `z_civ\_money_only\M02` (`--killers 0`): the three clerks' money back with field 11 and NO step - only the `.prp`
  member differs from the tab's build, and the existing `kl_fa_bots_dyn.py check` passes it as it stands (0 FAIL).
  **It is still a test build**: the window rule above FAILs it without the waiver like the others.
- `z_civ\_before\M02` (`--when before`): round 1's place in the chain with this round's `_5_Take` on the group -
  for telling the two places apart if C1 shows the killers standing at the cases instead of going for her.

## 6. Live checks for the lead (the owner away; TEST tree, TEST hook, `[Bots] Enable=1 Log=2`, `--poslog`)

No z_civ build goes on the owner's tab before C0 and C1 have run clean. The posts: jewel store's clerk
(1446, 504, 2501), watch shop's (-1769, 503, 2801), the cafe's (-1838, 1, -3855).

**C0 - FIRST: the field alone. `z_civ\_money_only\M02` in the Late Night Opening slot, idle player, `--poslog`,
Escort / BoardAll as the owner has them.** Nothing new for the engine in it (only the `.prp` differs from the tab's
build: the three clerks' money back, field 11). It answers two things without the two new classes in the way:
- **is anybody held:** PASS = the round of W1_DM02 again (stages 1 -> 2 -> 3, the van, `aboard` / `status6`, nobody
  `in-play g1` at the end) AND **no bot within 150 of a clerk's post for more than 20 s while loot is left** (the
  `hop:` position lines against the three posts). A bot that stands there = the trap of L8 / L10 through the field:
  the build is out, and `z_civ\M02` with it (the money stays stripped on Late Night Opening; the step would then
  need the take done by a hook part).
- **is a bot in her ball paid:** any bot passing within 115 of a post and gaining money in 20,000 parts that the
  store's own loot does not explain (the watch shop: nothing else there pays in 20,000 parts; her 75,000 = 20,000
  x 3 + 15,000). Paid = her money is soon 'taken' and the trap cannot hold; then killing is not needed for the
  money at all (section 1 says the code does not ask for it).

**C1 - does the step load and play: `z_civ\M02`, the same way, `[Bots] Enable=1 Log=2`, `[Balance] Log=2`.** PASS =
the level loads, GO, no fault, no assert for the whole round; every living bot `heist stage 0 -> 1`, `-> 2`, `-> 3`,
the van, `aboard` / `status6` as in run W1_DM02; **no living bot `in-play g1` at the end; no run of `hop:` lines
with one node for one bot over minutes; no bot within 150 of (1446, 504, 2501) / (-1769, 503, 2801) for more than
20 s outside the killers' own 12 s; and NO CREW BULLET ON THE HUMAN OR ON ANOTHER BOT IN THE KILL WINDOWS** - the
kill is 3 s of cover fire at a point, renewed for 7 s: `balance:` 'you lost' lines and bot losses ('record N
(bot): lost') in the 7 s after each killer's `_3_Timer_shoot` (about 5 s after his store's loot wait ended) mean
the fire crosses the room; and look what klgrudge / the traitor logic of the other tracks made of such a hit.
A fault at load = the two new classes at their Init: C0's build has loaded by then, so it is the routs. A fault at
the moment a store's loot wait ends (the first: when the jewel store is empty or its deadline is up) = the kill or
the follow goal at work: send the dump.
- **The two places in the chain:** with `z_civ\M02` the killers go for the clerk AFTER the store is looted. If
  instead they are seen standing at the cases through their 12 s (the loot tactic beating the order), that is no
  fault of the place. `z_civ\_before\M02` is the other place (before the walk to the loot place): there the same
  picture means the tactic beats the order as in L10, and the fire comes from across the room.

**C2 - who earned the clerk's money (the same run).** The log lines to read:
- The two killers are Squad#02 and Squad#04 = bots 2 and 4 (`Glazer_Bodyguard_02 / _04`). WHICH crew record that
  is must be read from the log (klbot's lines give the actor per record; 'records 1 and 3' holds only if records
  follow the squads - not established). After each store's loot wait they leave the group for about 12 s: with
  `--poslog` their `hop: bot n ... node (x, y, z)` lines move toward the clerk or toward wherever she ran, then to
  her post (the group node).
- **PASS for 'a bot can kill a civilian and take her money':** one of those two records gains money in 20,000
  parts (20,000 x 5 at the jewel store's clerk - mind the store's cash drawer pays 20,000 parts too: the clerk is
  proven only when the store's total goes past the 1,700,000 of runs L8 / L10 / L11, or at the watch shop past
  +460,000: there nothing else pays in 20,000 parts but her 75,000 = 20,000 x 3 + 15,000).
- Shots heard / the clerk seen dead in the pictures every 2 s = the kill routine works even if no money moves.
- No money and no dead clerk = cover fire without a line of sight, or she was out of reach in 5 s: raise `--go`.
- A dead clerk and no money while the killer stands at her POST (`hop:` node within 115 of the post for 5 s: the
  take step now names the group, so this is the case that proves something) = a bot is not paid from a civilian's
  group at all, dead or alive (section 2): then the money on a civilian is the human's only.
- The score page after the round: no 'Civilian kills' penalty for the human from a bot's kill (read, section 3;
  a line there = the reading is wrong: say so).

**C3 - the human, once (the owner, or the scripted player with a `goto` to (1446, 504, 2501)):** is the '$' on the
clerk again, does standing at her pay 20,000 parts while she is alive, does it after she is shot. That settles
section 2 for good.

**C4 - the others:** `z_civ\M01` (the waitress) and `z_civ\M03` (the hall's civilian) as C1 / C2; `z_civ\M06` is the
tab's build byte for byte, nothing to run.

## 7. The existing checks on a z_civ build - they FAIL as they stand, on purpose

`python tools\kl_fa_bots_dyn.py check <z_civ\M0x>` ends `RESULT (kl_fa_bots_dyn): FAIL` with exactly these lines and
no other (M02: 10):

- `kl_fa_bots.check: controller DefendNPCPosBehaviourRout is not used by stock F07; stock levels that run it in
  Arcade: NONE`, and the same for `KillCiviliansBehaviourRout` - rule 5 of `kl_fa_bots.check`, 'nothing the levels
  do not already run'. True, and the step itself: the reason for C1.
- `<squad>: civ_.._1_Timer_go also starts civ_.._2_Follow (None)` and `civ_.._3_Timer_shoot also starts
  civ_.._4_Kill (None)`, two a civilian a killer: `kl_fa_bots_dyn.graph()` knows a cover hold, a RandomTrigger and
  a relay beside a step's next link and no other class.

`python tools\kl_fa_bots_civ.py check <folder> [--accept-window]` runs that very check, takes exactly those lines
apart (by pattern: a `civ_` timer of this step 'also starts' a rout of this step; the two class names in the 'not
used by stock' line; the 'also starts' lines are counted against the routs this step starts beside a timer, a
mismatch is a FAIL), FAILs on every other line, and adds its own rules: the civilians' money (TYPE_NORMAL, its own
take trigger for people only, field 11, no KickDoor near), every rout a child of its squad's group, the last bool
0, `_2_Follow` names a money civilian's ACTOR and `_5_Take` her money GROUP, the kill rout her squad of ONE actor
**which stands earlier in scene order than the rout** (its init takes the squad object untested, section 3), the
three timers in every branch set of the chain in a row and in the order [next timer, rout], the last timer hands
on to a step of the same squad, no other squad node names a civilian, **the window rule of section 5** (FAIL per
civilian with a squad that is not sent to her inside her window; `--accept-window` = NOTE), every object fits its
class (`kl_prpjoin.misfits`), no dangling reference.

For track K, when it has `tools/kl_fa_bots_dyn.py` open - the two lines that would make its check know the step
(not made here; the file is not this track's): in `graph()`, in the loop `for j in nx[1:]`, before the final
`else`, `elif sc.names[j].startswith('civ_'): it['side'].append(('civ', j, []))`; and in `check()`'s loop over
`it['side']` a `continue` for kind `'civ'`.

`kl_impact.py`, `kl_maps.py audit`, `kl_map_guns.py check`, `kl_map_escape.py van-check`: pass unchanged (section
9 has each last line).

## 8. ASSUMED, guessed, not done

- That `KillCiviliansBehaviourRout` works at all: read, never run by any level. That a controller renamed on a
  stock FollowBehaviourRout node is a valid kill rout (same stored shape; the schema check passes).
- No longer assumed (read whole by the review, section 4): a new rout replaces the running goal whatever its class;
  property 0x3e = 'start once'; a civilian is in her squad's member list.
- **Field 11 against the trap of L8 / L10: narrowed, not closed** (section 5, the window) - the reason every build
  here is a test build.
- Which node the engine moves with a walking actor (the group or `Ground`; the step is right for both); what
  `ZCoverFire` does without a line of sight, and the `+0x5ac` branch of 0x831850; when and where a civilian flees
  and whether she is then taken out of her squad's list (if she is, the goal passes her over: section 3); a
  civilian's health; other readers of a civilian's death than the rules' notice: **not read**.
- That every controller's slot 13 runs before any slot 14 (the kill rout's init): likely, not proven; the builds do
  not depend on it (the check's scene-order rule).
- That an Ally soldier never targets a Neutral by itself: not read, fits the runs.
- 5 s to reach her, 7 s to kill and take, two killers, the four roles, the reach of 1,500, the place after the loot
  wait: OURS.
- NOT DONE: no hook part (`klhook/klciv.c`, `[Bots] Civs=1`) - the order is level data, and a hook part could only
  add what the live run asks for (e.g. a log line 'who shot the civilian', or the take when section 2 turns out to
  need a hand). `klhook/KLHook.ini` was not touched. Retomoto has no money civilian and was not built. The cafe's
  clerk on Late Night Opening and the upper floor's clerk on Withdrawal get no killer (no loot stop on their floor).
  `tools/kl_fa_bots.py`, `kl_fa_bots_dyn.py`, `kl_fa_bots_rt.py` were not edited.

## 9. The builds, second round (`<work>\build\z_civ\logs\summary_M01_M02_M03.txt` and `summary_M06_M02_money_only_M02_before.txt` have every line; `<name>_build.log` the build runs)

    python tools\kl_fa_bots_civ.py owner "<work>\build" --accept-window     (M01 M02 M03 M06 into z_civ\<map>; M02 with its donor)
    python tools\kl_fa_bots_civ.py build "<work>\build\z_loot3\M02" "<work>\build\z_civ\_money_only\M02" --donor "<work>\build\z_route\M02" --killers 0 --accept-window
    python tools\kl_fa_bots_civ.py build "<work>\build\z_loot3\M02" "<work>\build\z_civ\_before\M02" --donor "<work>\build\z_route\M02" --when before --accept-window

(Each was made by one `build` call of that form.) Tools: `kl_fa_bots_civ.py` c384d865e117 (M01 / M02 / M03 were
built before its docstring's last edit - the code was the same - and every check below was run again with this
file), `kl_fa_bots.py` 59183dc42505, `kl_fa_bots_dyn.py` 5a737a66dd51 (track K's file as it stands now; only its
`graph`, `Maker`, `from_build`, `check`, `NEXT`, `PERS` are used).

| | M01 | M02 | M03 | M06 | `_money_only\M02` | `_before\M02` |
|---|---|---|---|---|---|---|
| archive sha1 (source's) | 13921f508a53 (58491ae96cf4) | 0d392002b8ab (a004c014c5ce) | 7ebcde2d221c (6b1a780c0a73) | 1d799830eeee (the same) | 6467165d5bf8 (a004c014c5ce) | 7f951b27f114 (a004c014c5ce) |
| members that differ | .prp .gms .buf .oct | .prp .gms .buf .oct | .prp .gms .buf .oct | none | .prp | .prp .gms .buf .oct |
| entities added | 12 | 24 | 12 | 0 | 0 | 24 |
| `kl_fa_bots_civ.py check` (the build's waiver) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 6 NOTE) | PASS (0 FAIL, 5 NOTE) | PASS (0 FAIL, 1 NOTE) | PASS (0 FAIL, 6 NOTE) | PASS (0 FAIL, 6 NOTE) |
| the same WITHOUT `--accept-window` | 1 FAIL (the waitress) | 3 FAIL (the three clerks) | 2 FAIL (both civilians) | 0 FAIL | 3 FAIL | 3 FAIL |
| `kl_fa_bots_dyn.py check` as it stands | FAIL (6 FAIL, 2 NOTE): the lines of section 7, no other | FAIL (10 FAIL, 4 NOTE): the same kinds, no other | FAIL (6 FAIL, 1 NOTE): the same | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) | FAIL (10 FAIL, 4 NOTE): the same kinds |
| `kl_fa_bots_civ.py diff` | only the killers' steps were added and the civilians' money edited | same | same | nothing differs | the money of 3 civilians, `.prp` only | same as M02 |
| `kl_impact.py` | problems: 0 in 1 levels | same | same | same | same | same |
| `kl_maps.py audit` | PASS (0 must, 1 known) | PASS (0, 6 known) | PASS (0, 0 known) | PASS (0, 6 known) | PASS (0, 6 known) | PASS (0, 6 known) |
| `kl_map_guns.py check` | 6 guns with looks; problems: 0 | same | same | same | same | same |
| `kl_map_escape.py van-check` | 0 fault(s) | 0 fault(s) | 0 fault(s) | exit 0, no line (helicopter) | 0 fault(s) | 0 fault(s) |
| `.prm` / `.ANM` / `.fxc` / `.WAV` / `.TEX` / chunk entries | as the source | as the source | as the source | as the source | as the source | as the source |

`_money_only\M02` has the first round's sha1: the money edit did not change. M06 is the tab's build byte for byte.
The first round's builds (0b9e3ab9c73f, 4a9cfa0f4840, ffd0f05cec27) are deleted; their logs are in `round1\logs`.

Files beside the archive: byte for byte the source's (M03's `KLJoin.ini` with its `[CrewHop]` too), but `civ.json` /
`civ.txt` (new), `steps.json`, `graft.txt`, and on M02 `bots.json` (`money_off` -> `money_back`).

## 10. The review's points (`re/bots_civs_review.md`) and what was done

| point | done |
|---|---|
| MUST 1: field 11 re-opens the hold on Late Night Opening and the check says PASS | DONE. `check()` measures every squad's Defend places against each money civilian's window and FAILs per civilian for the squads not sent to her; `--accept-window` (recorded in `civ.json`) makes it a NOTE 'WAIVED ... NO CANDIDATE FOR THE OWNER'S TAB'; all builds are made with the waiver and FAIL without it (section 9). The live order starts with `_money_only\M02` (C0). The note says where the field is a gain (Hot Coffee, Withdrawal) and that no z_civ build is a tab candidate. The trap itself is NOT closed: it cannot be by level data short of taking the money out again |
| MUST 2: `_5_Take` names the GROUP | DONE (all builds rebuilt); the check wants the actor on `_2_Follow` and the money group on `_5_Take` |
| MUST 3: corrections | DONE: DefendNPCPos ends in two cases (section 4); 0x3e = 'start once' (0x4ebed0); 0x791090's state test; a civilian's membership in `+0xc0` (0x7b39f1 -> 0x48c480); the `+0x5ac` branch of 0x831850; 'stock names the group' against the kill goal's use of the actor node (section 2) - note and docstring |
| SHOULD 4: a check rule for the kill rout's init | DONE: FAIL when the named squad does not stand before the rout in scene order |
| SHOULD 5: cover fire at a point | DONE as a live check (C1: no crew bullet on the human or another bot in the kill windows) and said in section 3; nothing read further |
| SHOULD 6: where the steps sit | DONE: default `--when after` (after the stop's loot wait); `--when before` kept, `z_civ\_before\M02` for comparison; C1 says how to tell them apart |
| SHOULD 7: the unread rules | PARTLY. READ: the rules' death notice 0x485740 - a bot's civilian kill is counted against nobody, no traitor path for a civilian victim, a human's kill adds `[tuning+0xc18]` to score +0x2c; and the two routines that take a member out of a squad's list zero the slot, which the kill goal tests. NOT READ: whether a civilian that fled is taken out at all, and other readers of her death |
| SHOULD 8: small | DONE: `squad_no` matches the whole name `Glazer_Bodyguard_0N` and refuses another; `--reach-height`; the two kinds of known lines are matched by pattern on this step's own node and class names; every check re-run with track K's current file |
| SHOULD 9: C1's PASS text, C2's records | DONE (section 6) |
