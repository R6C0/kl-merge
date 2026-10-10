# An AI heister that stays near the human: the mechanism, the hook part, the live checks

2026-10-10. Static reading of kl2.exe build 0490 (`debug\dasm.py`, scratch `esc\fn.py`) and a hook part,
`klhook\klescort.c`. **Nothing here ran in the game.** Builds: `<work>\build\klhook\ship_esc1`
(sha1 f5fe0bbbf3443b998488747c5366713f9138f4bd) and `test_esc1` (ee711e29316574d0056d6b5a34a8fa673e446302),
not installed. Off unless `[Bots] Enable=1` and `Escort=1` or `2`.

## 0. Short answers

- There IS a safe way. A soldier's "defend this place" order is one virtual routine,
  `ZSoldier` vtable +0x13c = **0x760e50**, and the heist rules themselves call it for the AI crew from
  outside the soldiers' scripts (0x8fb04c). The hook calls the same routine with the arguments a Defend
  step uses. No data write, no code byte, no teleport.
- The order snaps its point to the navigation mesh itself (0x412910).
- `DefendPlayerPosBehaviourRout` is NOT "one order per trigger" (correction to `re/bots_dynamic.md` 1.1
  and 5): its run 0x622c40 is a loop that orders every member to the nearest player again and again,
  with a random wait between members. It would work as map data too, but it cannot pick one bot of a
  one-man squad's chain without replacing that chain; the hook can.
- A bot that is called away does not break its chain: the running Defend step WAITS for him.

## 1. What was read

### 1.1 Objects

| what | where | evidence |
|---|---|---|
| soldier of an actor | `[actor+0x77c]` | constructor 0x761900 `mov [edx+0x77c], esi`; the rules read it at 0x8fb034 |
| actor of a soldier | `[soldier+0x40]` | every goal (`mov ecx,[esi+0x40]`) |
| the soldier class | `CPPScript::ZSoldier`, vtable 0xbd0954, the only one; made by `ZSoldierRout` slot 13 (0x622ae0) | one constructor, one caller |
| DEFEND POSITION | `[soldier+0x64c]` -> 0x1c bytes: +0 x y z, +0xc move style, +0x10 "style given", +0x11 "changed", +0x12 "queued", +0x14 the soldier, +0x18 1.0 | made in soldier slot 17 (0x6ab250) by 0x40b540; written by 0x412910; the Defend goal writes +0xc / +0x10 (0x686b96) |
| defend goal | `[soldier+0x648]`, +8 = state (0 / 4 = idle) | 0x760f13 |
| "soft order" byte | `[soldier+0x4fc]` | written by the order; read by the Defend goal's wait (0x686c77, 0x686e86) |
| held as a human shield | `[actor+0x770]` (the holder; `[holder+0x76c]` = the held) | 0x7034a0, 0x74fad0; `ZFFActor` vtable +0x620 = 0x86dba0 tests it |
| "takes orders" | byte `[actor+0x576] == 1` | the test 0x622c8d makes before it orders a member. What else it means: not read |
| the human | `[gamedata+0x828+4*(char)[gamedata+0x898]]`, feet +0x460; type byte +0x273c == 2 | `kljoin.c` (seen live); 0x7263d0 walks the same slots and measures with the node `[player+4]` |
| a place in the world | node: 9 floats +0, position +0x24, parent +0x50; v = M v + p up the chain | 0x7b3020 -> 0x6be1c0 + 0x42a4d0 (re-read; `klbot.c`'s arithmetic is right) |

Which crew record is the human: the first record without mask 1 at +0x79 (`klbot.c`; record 0 in Arcade,
0x7af9d0). The record's +4 is not used for him: the player object comes from gamedata.

### 1.2 The order: 0x760e50

`void __thiscall (ZSoldier *, const float pos[3], char soft, char reset, char unused)`, `ret 0x10`.

1. Network session and this machine a client (0x863a60, 0x4b0a40): return. Arcade: neither.
2. `actor->vtable[0x620]()` true (held as a shield): `soldier->vtable[0x160](pos)` instead (another
   goal, `[soldier+0x68c]`), return. **The hook does not call in that case.**
3. `soft2 = soft`; but if `[soldier+0xec] != 0` and the squared distance soldier - pos is under 62500
   (0xb7eb28; 250 units), `soft2 = 1`. What +0xec is: not read.
4. `reset`: `[soldier+0x720] = 0`. `[soldier+0x4fc] = soft2`.
5. 0x412910 (block, pos): `pf = [[[0xdd2640]+0xac]+0xc]`; `pf->vtable[0x80](pos, &hit)`; if it hit,
   `pf->vtable[0x84](&hit, &point, 1)`; the block gets `point`, or `pos` when either fails.
   ASSUMPTION: these are "nearest polygon" and "point on it"; the hook reads the block back and logs
   what the game set, so the first live run shows it.
6. Block +0x11 = 1. Goal state 0 or 4: `vtable[0x1b4]()` (0x6e49b0: all eleven goal slots
   interrupted), 0x6cabf0 (goal queued, priority 150), `vtable[0x50](1)`. Goal running and not soft2:
   0x7bbf70 (block queued for a new plan). Running and soft2: nothing more.

It derefs without a test: the soldier's actor, `[soldier+0x64c]`, `[soldier+0x648]`, the pathfinder.
The hook tests all of them (section 3).

### 1.3 Who calls it

38 call sites through vtable +0x13c with a soldier. The ones that matter:

| caller | arguments | note |
|---|---|---|
| `ZDefendBehaviourGoal` run 0x686920 (0x686bac, 0x686df2) | (place, 0, 1, 0) | every Defend step of the bots' chains |
| `ZDefendPlayerPosBehaviour` run 0x622c40 (0x622d52) | (nearest player's place, 0 first pass / 1 later, 1, 0) | a loop, see 0 |
| `ZDefendNPCPos`, `ZDefendCurrentPos`, `ZMove`, `ZFlanking`, `ZLeapFrog`, `ZRunForHelp`, `ZGrenadeAttack` goals | (place, 0, 1, 0) | |
| `ZAttackTarget` 0x4f4460, `ZStayInCoverGoal` 0x8d43b0, `ZCloseInOnTargetTactic` 0x5c4360 | (place, x, 0, 0) | the soldier's own tactics move the defend block too; how far: not read |
| **`ZGameRulesHeist` slot 194, 0x8fa6d0 (0x8fb04c)** | (boarding place, 1, 1, 0) after `vtable[0x1b4]()` | **outside any soldier script**: when the vehicle's state becomes 3 or 4, for every crew record in use with mask 1 and stage >= 3 whose `[actor+0x77c]` is not null. No status test, no other test |

The last row is the precedent: the same walk over the crew records the hook makes, the same pointer
chain record +4 -> actor -> +0x77c -> soldier, the same routine, from the rules' own update.
Boarding place = world place of `[[rules+0x1e0]+4]` + 500 x its x axis (0x8faf72 .. 0x8fafe6).

### 1.4 How a Defend step waits, and what that means for an escort

0x686c42 .. 0x686ce1 and 0x686e80 .. 0x686ee1: after the orders, for every member the goal sleeps 0.1 s
at a time until `actor->vtable[0x3d0]()` is true, or `[soldier+0x4fc] != 0`, or the member is within
10.0 or 1000.0 (chosen by the goal's +0x40 == 1; which property that is was not read) of the step's
place (0x60b160). When all are through:
0x5c6e70(1), the step is over, its NEXT list fires.

- A bot ordered elsewhere by a NOT-soft order: the step waits. The chain stands still behind him.
- A soft order (the rules' boarding call), or an order to a place within 250 of him: +0x4fc = 1, the
  waiting step is over at once and the chain's next step orders him away.

So the hook orders with soft = 0 and only when the bot is at least 5 m from the place (it is called
only when the human is more than `EscortFar` = 8 m from it; the place is `EscortSide` = 3 m from the
human; the ini is clamped so the gap is never under 3 m).

### 1.5 Stages and boarding

`ZOnlineGamePlayTrigger` 0x8d2740: kind 0 / 1 / 2 raise the stage of whoever is in the box to 1 / 2 / 3
(0x5dd890, a maximum, never lowered) and call rules slots 47 / 48 / 45. Slot 45 = 0x6840a0 is the
boarding rule: for an actor it finds the record (0x78f470) and, if status is 0 and the vehicle waits
(or has just left), sets status 4. **It does not ask for a stage.** `ZOnlineExitLevelTrigger` 0x6c3d50
also gives stage 3. So an escort that walks into the BOARDS box boards, whatever its stage was.

## 2. Design

`[Bots] Escort=N` (0 off; 1 or 2). Gate as `klbot.c` section 0: Arcade (mode 4), round state 0x19, a
level that is NOT the stock one of its slot, Steam guard on, game thread only.

**Which bots.** 3 s after the round state became 0x19: of the AI records in play, not traitors, that
pass every test of section 3, the nearest to the human - drawn at random among the nearest N + 2, since
at the start the seven stand in one row and "nearest" would be the same man every round (the owner:
'random every time'). A fixed record would always take the same role of `kl_fa_bots_dyn` (point man,
runner ...); `EscortRecord=<i>` exists as a test aid only.

**Hold** (twice a second per escort):

1. Read the defend block. Not what the hook's last order left there (5 units)? Farther than 600 from
   ours: the route chain ordered him - remember it as his ROUTE PLACE, the hook's hold is over.
   Nearer: one of his own tactics moved it - still our hold. **GUESS: the 600.**
2. Human farther than `EscortFar` from the bot, and (no hold, or the human moved more than
   `EscortRetarget` = 5 m from the hold place), and `EscortEvery` = 2 s since the last order:
   `soldier->vtable[0x13c](&p, 0, 1, 0)`, p = `EscortSide` from the human towards the bot (second
   escort 70 degrees round), the human's height. The game snaps p.
3. Not 1 m nearer to the place 12 s after an order: once, the human's own place (it is on the mesh).

**Against the chain** - the last caller wins, and the routine only replaces the place and queues a
plan, so nothing is left half done:

- a. the step that was running waits for him (1.4): the chain stands still;
- b. a step started by a timer, an "actors dead" trigger or the jump list orders him to its place: he
  goes; the hook notes the place and calls him back when he is 8 m from the human again; that step
  then waits like a;
- c. stage boxes are places: he gets the stages when he walks through them beside the human.

**Release.**

| when | what |
|---|---|
| the vehicle waits (state 3 / 4; `EscortUntil=1`: from state 1) | stage 3: left alone, the rules' slot 194 has ordered him. Under 3: ONE order (boarding place, 0, 1, 0). Not soft, unlike the rules' call: soft would end the waiting step and the chain would send him back into the level. He crosses the BOARDS box on the way: stage 3 and aboard. ASSUMPTION: the box is at that place |
| the human is dead or aboard; `EscortStage=1..3` reached (off by default) | if the hook's hold is still his place and a route place is known: ONE order back to it; the waiting step ends when he arrives and the chain goes on. Later, when the vehicle waits and he is under stage 3: the boarding order (`EscortBoard=0`: not) |
| the escort is dead, aboard, a traitor, another actor | dropped, no call. `EscortRefill=1` picks another |

Why `EscortStage` is off by default, against the brief ("release when the human reaches stage 3"):
the chain stood still while he escorted, so "back to its own chain" at that moment sends him to a
place early on his route - often back into the bank - while the human stands at the escape. Holding
him beside the human until the vehicle waits, then the rules' own boarding place, is what gets him
aboard. The key is there to try the other way.

Once released, an escort is not taken up again in that round (a second vehicle: no escort).

## 3. Tests before every call

First 16 bytes of 0x760e50 and vtable 0xbd0954 +0x13c == 0x760e50; record in use, mask 1, not mask 2,
status 0, still the chosen actor and soldier; actor vtable 0xbb3bac, its +0x620 entry 0x86dba0; node
flag bit 10 clear; `[actor+0x576] == 1`; `[actor+0x770] == 0`; soldier vtable 0xbd0954;
`[soldier+0x40] == actor`; defend block readable and its +0x14 == soldier; defend goal readable;
`[[[0xdd2640]+0xac]+0xc]` an object whose vtable entries +0x80 / +0x84 lie in kl2.exe; the place finite.

## 4. Assumed / not established

- AI and rules run on the main thread, so a call from the hook's game-thread tick (between two frames)
  is as good as the rules' call from their update. `klchar.c`'s body swap from the same tick is live.
- What the pathfinder's two calls return for a point off the mesh (the 12 s fallback covers "unreachable").
- `[actor+0x576]`, `[soldier+0xec]`, `[soldier+0x720]`: only their use in these routines.
- A bot called away while looting / in cover / in a mini scene: the rules do the same to stage-3 bots
  (with the interrupt 0x1b4 on top), so the routine is built for it; what it looks like is unseen.
- That an Ally fights from a hold beside the player as it does at a route hold (leash and cover use
  the same block; the police's squads do it under `DefendPlayerPos`).
- The 600 that tells the chain's order from a tactic's; two escorts on one polygon.
- No off-game rig was written for this file (klbot.c had one): only "both builds compile, no warning".

## 5. Live checks, in order

All on a map that is not stock (the bank, `[Bots] Enable=1 Log=1`), TEST hook `test_esc1`, owner away.

| # | ini | expect in KLHook.log | settles |
|---|---|---|---|
| E0 | `Escort=1 EscortDry=1` | `escort: on; ... DRY RUN`; `escort: you: record 0, player ..., feet (...), node (...)` - the two within a body's height; `escort: record N (actor ..., soldier ...) chosen: ... its place now (...)`; walk 10 m away: `escort: record N WOULD be re-pointed (dry run): you are 1x.x m away ...` at most every 5 s; at the vehicle: `released (the vehicle waits, state 3): WOULD be sent ...` | offsets, node arithmetic, every pointer test, the bot's place; nothing called |
| E1 | `Escort=1 EscortLog=2` | `escort: record N re-pointed: ... place asked (...), the game set (...)` - set within a few metres of asked and on the floor; the bot comes and stops ~3 m from you; NO line `took an order as 'he is there already'`; in the `bots:` lines the other six go on as before | the call; the snap; the chain waits |
| E2 | same, stand still 30 s, then move through the bank | `its route chain ordered it to (...)` lines at the chain's timers, each followed by a `re-pointed` once he is 8 m away; `bots: record N (bot): heist stage 0 -> 1` when he follows you in | who wins; stages beside the human |
| E3 | same, go to the vehicle | `released (the vehicle waits, state 3): sent to the boarding place (...)` or `it is at stage 3, the game's rules send it aboard themselves`; then `bots: record N (bot): aboard` | boarding |
| E4 | same, die early | `released (you are out of play): back to its route place (...)`; later his stages rise in the `bots:` lines | the chain resumes |
| E5 | `Escort=2`, then Retomoto with `[CrewJoin]` | two `chosen` lines, two places 70 degrees apart; after the join both are re-pointed on the street | two escorts; the two mesh parts |

Stop and report at: any fault with 0x760e50, 0x412910 or 0x7bbf70 on the stack; `NOT re-pointed: ...`;
`dropped: actor +0x77c is not its ZSoldier`; a bot that stands still for good after E4.

## 6. Files

`klhook\klescort.c` (new; top comment = the spec), `klhook\klhook.c` (include after `klbot.c`,
`kle_tick` after `klb_tick`, `kle_init` after `klb_init`, a row in the file table), `klhook\KLHook.ini`
(the Escort keys, commented out, under `[Bots]`).
