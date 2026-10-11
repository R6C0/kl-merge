# Review of track P - AI heisters and the civilians who carry money

2026-10-11, adversarial reviewer. Reviewed: `tools/kl_fa_bots_civ.py` (934 lines, read whole), `re/bots_civs.md`, the
builds `<work>\build\z_civ\M01 M02 M03 M06 _money_only\M02`. OFFLINE: nothing was run in the game, nothing committed,
no file of the worker changed (the audit was re-run on copies in `G:\kl_scratch\revP`, deleted afterwards).
Reviewer's scratch scripts: session scratchpad `revP\` (`order.py`, `win.py`, `props.py`, `scan*.py`, `rerun.sh`).

## Verdict: ACCEPT WITH FIXES

The reading of kl2.exe holds where it matters (one statement is wrong, several are better founded than the note
says), the tool does what it says, every check and build reproduces. A z_civ build may be LOADED on a test tree as
it is. Two things must change before any z_civ build is called a candidate for the owner's tab: the step swaps
track A's proven fix on Late Night Opening for the alternative track A rejected by name, and its check reports that
as a pass (MUST 1); and the 'take' step walks to the wrong node for what the note itself says about the trigger
(MUST 2).

## What was re-read in kl2.exe (debug\dasm.py) and what came of it

| claim of the note | re-read | result |
|---|---|---|
| the take trigger serves every player / Ally actor, loop goes on | 0x626f43 .. 0x626fee | CONFIRMED: class mask 0x1548c7c, or Arcade + mask 0x1547b24 + `[[actor+0x54]+4] == 2`; `inc` + `jmp 0x626f43` after every object |
| the money object knows no person; field 11 not in the take | 0x6cdb40 .. 0x6cdc34 | CONFIRMED. The hidden test (0x6cdb65) and everything else is on the CONTROLLER'S node = the money GROUP; `+0x5c` is only written (0x6cdc0e) |
| field 11 passes the object over in the loot test | 0x451a88 | CONFIRMED (`cmp byte [edx+0x5c]` -> the KickDoor branch) |
| KillCivilians: vtable 0xbcde3c, fields s / refs / b / b, same shape as FollowBehaviourRout | `kl_rtp.Schema('dd')` | CONFIRMED: both {s type 1, refs 39, b 51, b 51}; controller on ZGROUP |
| its init, slot 14 0x4af120 | whole | CONFIRMED, with two things the note does not say: the node `0x8ccde0` returns is dereferenced with NO null test (0x4af12c), and the squad pointer `[ZSquadScript+0x3c]` goes into the goal untested (0x4af15c). That pointer is made in `ZSquadScript` slot 13 (0x6316b0). See SHOULD 4 |
| its goal 0x49a5c0 | whole | CONFIRMED: members `[squad+0xc0]`, `+0xc4..`; dead test virtual +0x3d0; point (0, 50.0, 0) of `[[member+0x40]+4]` through 0x7b3020; own squad's soldiers virtual +0x14c with (0, point, 3.0); wait 2.0; done -> 0x5c6e70(1) -> the rout's NEXT (0x8df0d0). Constants 0xbaf9e0 = 50.0, 0xb4a174 = 3.0, 0xb5c828 = 2.0 |
| a civilian IS a member of her squad's list | (not shown in the note) | CONFIRMED by the reviewer: `ZSquadScript` slot 14 (0x7b3790): an actor without a soldier (`[actor+0x77c] == 0`) is looked up in the registry gamedata+0x15ac (0x664850); an object whose type name is "Civilian" is added by 0x48c480 to the SAME list `+0xc0 / +0xc4` (12 at most). `CPPScript::ZCivilian` (0xbcfe54) and `ZSoldier` (0xbd0954) share base slots 13 / 14, so `+0x40` = the actor for both (by likeness, ctor not read). A squad with soldiers AND civilians is an int3 (0x7b3a24) |
| soldier virtual +0x14c = 0x831850 -> ZCoverFire | 0x831850 .. 0x8319d6 | CONFIRMED for the plain case (`soldier+0x654`, 0x717f90, 0x637800 weight 0xa0). NOT in the note: when the soldier's task at `+0x5ac` is running (state not 0 / 4) and 0x4c53b0(point) answers 1, the point goes to THAT task (0x809830) and no cover-fire task is queued. What that task is was not read by either of us |
| DefendNPCPos goal 0x5ed640 'never ends by itself and never fires its NEXT' | whole | **WRONG in one case**: `ebx` counts the members with `[actor+0x576] == 1` it ordered in a pass; with none (0x5ed6e3) or with the target unresolved (0x5ed692) it ends through 0x5c6e70(1) = fires NEXT. Harmless here (NEXT is empty on both routs of this step), but the sentence must go |
| the last bool (0x3f) shuts the squad | 0x79110d, 0x79112f .. 0x791138 | CONFIRMED |
| 'a new rout replaces a running goal (0x7f6750 read in outline)' | 0x791090, 0x7f6750, 0x4f3350 whole | CONFIRMED and class-independent: 0x791090 starts a goal only in state 0 or 4 and with `[squad+0xbc] == 0`; 0x7f6750 takes the running goal `[squad+0x154]` off the squad (0x4f3350: 0x5a0300 or 0x4052d0 / 0x8883d0) before it queues the new one with weight 0xc8 (0x6cabf0) - unless the squad has no member left. The two goal virtuals it asks (slots 9 and 13) are the same stub 0x429f30 for the Defend, DefendNPCPos and KillCivilians goals, so the new classes take the path every Defend step takes |
| 'field 2 of the kill rout (0x3e) = 1: GUESS by likeness' | rout slot 26, 0x4ebed0 | **NO LONGER A GUESS**: on the start message (0x168d804) a rout with `[+0x42]` (property 0x3e) set and `[+0x40]` set (it has started once) is skipped (0x4ebf01 .. 0x4ebf0b); `[+0x41]` (message 0x168d800) switches it off altogether. 0x3e = 'start once'. 1 is the right value for all three routs of the step |

## MUST

1. **Field 11 in place of track A's removal re-opens the hold of runs L8 / L10 on Late Night Opening (narrowed, as
   the worker says - but the check now says PASS for it, and the task asked for the opposite).**
   - `re/bots_loot.md` 6, 'Not chosen, and why': *'Field 11 on the clerk ... the action does not read the field:
     while any other candidate in the window passes the test, a bot whose NEAREST candidate is the clerk's post runs
     to it and stands - and in a small shop that can be every bot that is left, with a watch untaken behind them. It
     narrows the trap, it does not close it.'* `kl_fa_bots.cannot_take`'s docstring: *'which is why this module does
     not use the field'*. The owner's tab build `z_loot3\M02` (money stripped) is the one with the clean round
     W1_DM02 (seven of seven escape). `z_civ\M02` puts the 215,000 back and relies on the field alone.
   - `kl_fa_bots.check`'s loot-window rule passes only because `cannot_take` returns '' for a flagged object BEFORE
     it reaches the civilian rule (kl_fa_bots.py line 1093 before 1101): the build's own log says 'loot window: 0
     squad(s) with a place inside the window of something they cannot take; the closest any place comes: 02 1579 ..'.
     Measured by the reviewer (`win.py`, Defend places of every branch against each money civilian's group node,
     800 / 400): EVERY squad of every map has places inside a money civilian's window. Late Night Opening: watch
     clerk 2 .. 5 places a squad, nearest 37 .. 500; her money is the nearest money object of all at a place of
     squads 04, 05, 06, 08. Withdrawal: `Civ_in_03` (the clerk nobody is sent to) is the nearest money object at
     1 .. 3 places of ALL SEVEN squads. Hot Coffee: the waitress at places of five squads.
   - Task point 3: 'keep its check meaningful - the killer roles' places are allowed, the others' are not'. Not
     done: five squads that are never sent to her stand in her window on every map and nothing says so.
   - Whether it bites depends on the one thing nobody knows (does a bot standing in her ball get paid): if yes the
     object is soon 'taken' and there is no trap; if no, a round can end as L8 did, and BoardAll does not help
     before somebody has called the vehicle.
   - WANTED: (a) `kl_fa_bots_civ.py check` states it per squad that is no killer - at least a NOTE with the numbers
     above and the words 'narrowed, not closed (re/bots_loot.md 6)', better a FAIL that a named option waives;
     (b) `z_civ\M02` is not a candidate for the owner's tab before a run shows no bot within ~150 of a clerk's post
     for more than 20 s with untaken loot left; (c) the live order starts with `z_civ\_money_only\M02` (idle
     player, `--poslog`): it is the field alone and it answers the open question (a bot in her ball: paid or not)
     without the two new classes in the way. On Hot Coffee and Withdrawal the tab's builds already carry this money
     WITHOUT the field, so there the field is a gain - say that too.

2. **`civ_.._5_Take` should name the money GROUP, not the actor.** The note's own section 1 has the trigger's ball
   round the GROUP node (0x783e60, controller's node) and the hidden test on the group (0x6cdb65). The kill goal
   takes HER place from the ACTOR's node (0x49a62e .. 0x49a634: `[[member+0x40]+4]` -> 0x7b3020), i.e. the actor
   node is what the game treats as where she is - which is the evidence for 'which node moves' the note says it
   lacks, and it points at the group staying at the post. Then 'stand at the body = inside the money's trigger'
   (docstring line 56, note 0.4) is true only if she dies within 115 of her post. The group is right in both
   worlds (if it moves with her it is where she is; if not it is where the trigger is); the actor is right in one.
   `_2_Follow` rightly keeps the actor. Until changed, a C2 without money proves nothing about 'dead against alive'.

3. **Correct the note / docstring where they are wrong or weaker than what was read** (the table above): the
   DefendNPCPos 'never ends' sentence; 0x3e as 'start once' (0x4ebed0) instead of a guess; 0x791090's state test;
   the membership of a civilian in `+0xc0` (0x7b39f1 -> 0x48c480), without which 'the goal has her shot' is not
   shown; the `+0x5ac` branch of 0x831850; and 'stock names the GROUP, which makes sense only if the group moves'
   (section 2) against the kill goal's own use of the actor node.

## SHOULD

4. **A check rule for the kill rout's init.** 0x4af120 has no null test on the resolved node and none on the squad
   pointer; a null squad is a read of `[0+0xc0]` at 0x49a5ce at the moment the rout starts (60 .. 90 s after GO).
   In the builds the named squads resolve and stand EARLIER in scene order than every kill rout (nodes 1 / 9, 186,
   7123 against 15,323 .. 22,760: `order.py`), so they are safe under either init order. That slot 13 of every
   controller runs before slot 14 of any is likely (`ZSquadScript` slot 14 needs its children's slot-13 objects)
   but not proven. Add to `check()`: the squad node of a kill rout comes before the rout in scene order.
5. **Cover fire is aimed at a point for 3 s, not at a person.** No line-of-sight test was read; the point is 50
   above her feet. In an 8 m shop with the human and five other bots in it, look in C1 (`[Balance] Log=2`) for
   'you lost' / bot losses inside the 7 s windows, and for what the grudge / traitor logic of the other tracks
   makes of a crew bullet on the human.
6. **Where the steps sit.** They come BEFORE the walk to the stop's loot place, 37 .. 500 from it: the bot is
   then inside the window of the store's own loot, and the loot tactic beat Defend orders in L10
   (re/bots_loot.md 4, 'sometimes'). If it does here, the 12.1 s (24.2 s on Late Night Opening) pass at the cases
   and the fire comes from across the room. After the stop's loot wait the shop is empty, the tactic answers 0 for
   her flagged money, and it is also what the owner said ('if they do end up getting the money they might go back
   for it'). Worth a second build, or at least a line in the live checks telling the two outcomes apart.
7. **Unread and owed before the owner's tab** (the note lists them; they are not optional there): the score /
   traitor rules for a civilian killed by a bot ('Civilian kills' is a penalty line of the score page); what
   happens to the squad list entry of a civilian that has fled and been taken out (the goal re-reads `[ebx]` and
   calls through `[member+0x40]` every 2 s).
8. Small: `squad_no` reads character 18 of the actor's parent name ('Glazer_Bodyguard_0N' - correct today,
   fragile); `--reach` has no height twin (`REACH[1]` fixed); `check()` knows the two 'not used by stock' lines by
   their exact text; the build's `kl_fa_bots_dyn.py` (f4caa9bbe402) has since been edited by track K
   (5a737a66dd51) - every check below was re-run with the new one and gives the same lines.
9. C1's PASS text: add 'no bot within 150 of (1446, 504, 2501) / (-1769, 503, 2801) for more than 20 s' and 'no
   crew bullet on the human in the kill windows'; C2's 'records 1 and 3' holds only if records follow squads.

## Rules, state, scope

- Files: `git status` shows only `tools/kl_fa_bots_civ.py` and `re/bots_civs.md` as this track's; the diffs of
  `klhook/KLHook.ini`, `tools/kl_fa_bots_dyn.py`, `tools/kl_chars.py` hold no line about civilians;
  `tools/kl_fa_bots.py` is unmodified. Builds only under `z_civ`. No hook part, so no key, no memory write, no
  game routine called: the hook policy does not come into it.
- The worker's two heredoc patches (self-reported breach of the rules file): the tool parses, neither file holds
  a tab or control character.
- Stock levels / multiplayer: level data of the grafted maps only; the take trigger answers to Ally actors in
  Arcade alone (0x7f6850). New round / second round: nothing kept outside the level; the 'start once' bytes and
  the goals are the level's and are made again with it, like every Defend step of the squads.
- A deadlock of a round by the STEP's own nodes: none found - the chain is the three timers, every rout is started
  beside a timer, and `<L>` takes the squad back by the path every Defend step uses. The deadlock risk is MUST 1.

## Checks re-run (all reproduce)

| | M01 | M02 | M03 | M06 | `_money_only\M02` |
|---|---|---|---|---|---|
| archive sha1 | 0b9e3ab9c73f | 4a9cfa0f4840 | ffd0f05cec27 | 1d799830eeee | 6467165d5bf8 |
| `kl_fa_bots_civ.py check` | PASS (0 FAIL, 2 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 1 NOTE) | PASS (0 FAIL, 3 NOTE) |
| `kl_fa_bots_civ.py diff` | only the killers' steps + the money | same | same | same (nothing) | same (money) |
| `kl_fa_bots_dyn.py check` as it stands | FAIL (6 FAIL, 2 NOTE) | FAIL (10 FAIL, 4 NOTE) | FAIL (6 FAIL, 1 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) |
| `kl_impact.py` | problems: 0 | problems: 0 | problems: 0 | problems: 0 | problems: 0 (new: the worker had not run it) |
| `kl_maps.py audit` (on a copy) | PASS (0, 1 known) | PASS (0, 6 known) | PASS (0, 0 known) | PASS (0, 6 known) | not run |
| `kl_map_guns.py check` | exit 0, 6 guns with looks | same | same | same | not run |
| `kl_map_escape.py van-check` | 0 fault(s) | 0 fault(s) | 0 fault(s) | exit 0 (helicopter) | not run |

The FAIL lines of `kl_fa_bots_dyn.py check` are exactly the two kinds the note names (the two classes no Arcade
level runs; '<timer> also starts <rout> (None)'), nothing else.
