# AI heisters that stand still and react slowly (track A / B, 2026-10-12)

NOT RUN IN THE GAME. Owner, 2026-10-12: 'the ai heisters still seem a bit stiff like they always stand still even on retomoto
tower ... and they kinda feel like bullet sponges when im a fed which isnt bad but they are slow meaning they just let it
happen, come on the ai needs to have faster reactions than that'. Earlier: 'normally moving majority of the time ... sometimes
they just be standing still a bit'; 'less standing still thats a big one'.

Files: `tools/kl_fa_bots_rt.py` (`--hops N`, commands `hops`, `standing`), `tools/kl_fa_bots_dyn.py` (`--react`),
`klhook/klmove.c` (`[Bots] RestlessHop`), `klhook/klfedkit.c` (section 8, `[Fed] Hunted`), `klhook/KLHook.ini` (comment lines).
Build: `<work>\build\y_active\DM09`.

## 1. Measured: how long an AI heister stands

### 1.1 The owner's own Retomoto round (KLHook.log 14:10:54 .. 14:17:20, hook ship_w12, `[Bots] Restless=5 MoveLog=1`)
`klmove` writes a 'move: record N stood X s at ...' line whenever a bot has not moved 1 m (and earned nothing) for Restless = 5 s,
so the log holds every stand of 5 s or more and NO shorter one: all numbers are LOWER BOUNDS. Sum of the logged stands / the bot's
life (stage 1 or round start to its death or the end), per bot:

| part | bots | stand >= 5 s as a share of life | longest single stand |
|---|---|---|---|
| tower (stage 1 .. the join, 150 s) | records 5, 7 (the others' stage-1 lines are not in this window) | 31 %, 34 % | 14.2 s |
| street (join .. the van, 114 .. 204 s) | records 1, 2, 4, 5, 7 | 21 .. 32 % | 28.0 s (record 7 at (-3643, 0, 1393)), 22.0 s |
| whole round | records 1, 2, 4, 5, 6, 7 | 25 .. 38 % (85 .. 106 s of 263 .. 354 s) | 28.0 s; at the window 22.5 s |

(`python stand.py` style script: not kept; the numbers are reproducible from lines 255410 .. 258500 of that log.)
Restless itself acts: 74 orders in the round (14:10 .. 14:18), 48 of them the first on a spot, 26 (35 %) a second to fourth order on the same
spot - the bot was ordered and did not move (a bot under fire, or at a hold the chain meant). 6 times 'it is left until its
chain orders another place'. So Restless catches the bots that are STUCK OFF their place (b), and by design leaves the bots
that stand AT their place (c: 'a meant wait') alone (`RestlessHold=0`, the owner's ini).

### 1.2 What the build plans (tool: `python tools/kl_fa_bots_rt.py standing <build>`; UPPER BOUNDS, a wait its men's deaths end is shorter)
`y_rappel\DM09r2` (= the tab's Retomoto) per bot:

| wait | seconds | what holds the bot |
|---|---|---|
| the room (window, until the 3 room squads are dead) | <= 76.0 | `Timer_start_bots` fall-back, blast 16.5 + 1.0 + room_wait 75 -> stands at the window |
| the loot wait at the table | <= 30 | `TriggerLootDepleted`, loot_seconds 30 |
| seven gates (door .. lobby) | <= 30 each = 210 | `TriggerActorsDead` + the game's own 30 s limit (kl2 0x4afbbd); the bot stands at a Defend hold in cover until the men are dead |
| the street: lane holds + timed way pauses + the rally | 26 .. 30 (mean 28.3) | LANE_STAND 1.5 .. 2 s a hold, CLOCK_PAUSE 1.2, `street_hold` 10 |
| **total** | **344 (tower 316 + street 28)** | longest single wait 76 s, then 30 s (gates, loot) |

Stock Dog Days FA bots (re/bots_dynamic.md 2.1, measured on 63 bots): the sum of `TriggerDelay2` seconds per bot is 16 .. 85 s
(F01 43/63, F02 42, F03 21, F04 20, F05 71/85, F06 16, F07 36, F08 50, F09 46), 0 .. 4 `TriggerActorsDead` a bot, and a loot wait of 15
.. 60 s. So the tower's planned standing is about four times the stock bot's timers; one 30 s `TriggerActorsDead` hold followed by
another seven times is what the owner sees as 'always stands still'. Both the room (76 s) and the gates are the design of
kl_fa_bots_rt (the rooms are fought first so that the crew does not run onto the next guard: runs G1/G2/J1 showed that it lives
longer), so the fix must not shorten them: the bot must MOVE inside them.

### 1.3 Why a bot at a hold stands (exe + data)
A `DefendBehaviourRout` step is 'over' when its man has arrived (klescort.c 1), then the chain waits behind a timer or
`TriggerActorsDead`, which do not look at where he stands. The soldier's own tactics (AttackFromCover / Defend) keep him where he
is; Restless (c) leaves a bot within 3 m of its chain's place alone; the combat reading `fire` (health lost in the last 4 s) leaves a
bot under fire alone on purpose (klmove.c review S1). So a hold in a fight is a stand. The game offers a cover-to-cover move only
through new Defend steps behind a timer (stock: 8 .. 12 s `Timer_small`), but a timer armed at a hold that a `TriggerActorsDead`
has since released fires LATER and orders the bot BACK (no cancel): so hops are NOT written into the chain's nodes (rejected,
see 6).

## 2. Built: cover to cover (A)

### 2.1 Level: `[Hops]` in the build's `KLJoin.ini` (tools/kl_fa_bots_rt.py)
For every gate: more places than the seven holds (`pick_hops`): the holds' own rules - HOLD_RING 70 .. 230 from a cover box, flat
polygon, HOLD_CLEAR from a wall, no box of a later fight, no standing ring of a cover that has a side in one, POST_KEEP from
the men still alive - but looked for in the gate's box GROWN by 600 (the gate's own box is the room for the holds and has no
second set of covers), >= 100 from every hold, >= 150 apart, on the holds' floor, and whose way from EVERY hold within 18 m of it goes
through no box of a later fight and past no post of the gate's men (the rule the holds are laid by). Written per gate:
`Gate.g.Holds=7`, `Gate.g.Hold.j=x y z`, `Gate.g.Hops=n`, `Gate.g.Hop.j=x y z`, `Max=1800`. NOTHING in the level's nodes names them (the
archive is byte-identical to y_rappel\DM09r2: zip sha1 dcb7f94c).
`python tools/kl_fa_bots_rt.py hops <rt source build> <finished build> [--hops 8]` plans the tower half of the SOURCE build
(rt_full6\1_guns, 75 s), compares its holds with the finished build's `bots.json` ('THE SAME in all 7 gates' for DM09r2: the plan is
deterministic), and writes the section. `build ... --hops N` writes it in a fresh build. Result for Retomoto (8 wanted a gate):
door 8, reception 2, atrium 4, gallery 8, floor2 1, floor1 5, lobby 6 = 34 places (reception/floor2 are cramped: floor2 has one,
and 3 of its 7 holds have none in reach - those bots get the old shift, or stand).

### 2.2 Hook: `[Bots] RestlessHop=<s>` (klmove.c, section 5)
Needs `Restless` (the bot-watch) and `Enable=1`. A bot that has stood RestlessHop seconds (5 minimum; proposed 6) AT its chain's place
(c), not under fire (4 s), not in an escape box, no vehicle called, is given the soldier's own order (the call `RestlessHold`/the
escort already make: kl2 0x760e50, 'a running tactic is cut at its yield') to a hop of ITS gate: the gate is the one whose hold (or hop)
lies within 1.5 m of the bot's chain place on its floor; hops within Max of it, >= 3 m from where it stands, not the one it used last.
Then it stands again, hops again (the chain's place stays the anchor; the chain's next order takes it on as ever). No [Hops] in the
level's file, or none near: nothing (or the old random shift when `RestlessHold` is set). `MoveDry=1` logs what it would do.
Model (hop pairs 3 .. 18 m: 4 .. 51 a gate, mean 7 .. 12 m; walk 300 u/s as kl_fa_bots_rt.V_PLAN): a 30 s hold becomes cycles of 6 s stand +
~3 s walk: the LONGEST UNBROKEN STAND 30 s -> 6 s (and 76 s -> 6 s at the window is NOT covered: the window has no gate), the share of a
full-length wait spent standing 100 % -> ~65 %, three hops a wait. By the owner's own measure (a stand of 5 s or more is logged) a 6 s stand
still counts: set `RestlessHop=5` to make every stand 5.0 s - the log then shows the same number of stands but never one over ~6 s.

### 2.3 Not done on purpose
- Gate waits are not shortened (the game's 30 s; the squads dying ends them); `--room-wait 45` and `--loot-seconds 15` exist in the tool for the
  window and the table (a rebuild of the whole chain, not done: DM09r2's .prp is untouched).
- The window (first stand, 22.5 s in the owner's log) and the table's loot wait have no gate, so no hops there.

## 3. Reactions when the human is a fed (B)

### 3.1 What is known
- Hostile already, by the exe (re/balance.md 11.2, held on a second reading): kl2 0x882470 makes a police player a target of every
  crew soldier of team Ally; nothing needs registering. The owner's 14:15 fed round on Retomoto: he killed 5 bots between 14:16:47 and
  14:17:20 (33 s), `fedkit: pay` lines for each, and the game's 'the one who had killed you' +200,000 traitor line shows a bot killed
  him before; the log has no 'you lost' line of a heister on the fed (Log=1), so whether they SHOOT him is still not seen (live check TH).
- Their numbers are stock's: `eThug eCustom` accuracy/aim/6 = 50 50 50, health 280, ZSoldier 15 = 1.0, 16/17 = 600000 (switched
  on by nothing) on 56 of stock's 63 bots; fields 13/14 = 50 (= eRegular: 50 50 10 50 50 in the exe's skill table, 0x46e410).
- What fields 13 / 14 do: kl2 0x784330 (soldier creation, 0x761bd2) turns them into two ranges of the tuning table
  ([0x168d7c0]+0x3c0/0x3c4 and +0x36c/0x370) and stores them at soldier+0x10c (+0xc) and soldier+0x500. The exe's skill table:
  eN00b 100 / 40, eAmateur 70 / 45, eRegular 50 / 50, eVeteran 20 / 55, eElite 0 / 60 (13 / 14): 13 FALLS with skill, so it reads as a
  delay (reaction), 14 rises. NOT established that either is 'reaction time'; the readers of soldier+0x500 were not followed.
  Field 5 (aim settles) is read at 0x5a85a0/0x622b57. Idle/alerted sense switches (0x4c12e0, 0x590320) run at STATE CHANGES only, so a
  byte write at run time (soldier+0x6ac) would not reach the sense manager.
- What makes them slow, by the logs: they stay at the hold the chain gave them (section 1) and Restless does not move a bot that is
  hit (its 4 s 'fire' rule). A fed who shoots a bot at a hold meets a man who stands.

### 3.2 `[Fed] Hunted=1` (klfedkit.c section 8)
Not 'make them hostile' (they are) but 'make them move when hit': while the fed is in play, a crew bot that LOSES HEALTH (health object
[actor+0x5fc], the same read klbot/klmove use) with the fed within HuntedRange (4500 = 45 m) is given the soldier's own order to a hop
of its gate HuntedDelay (250) ms later, the bots within HuntedAlert (1500) of it that were not hit after it, 150 ms apart, each to its own
place; at most one order per bot per HuntedGap (4) s; not an escort, a traitor, a stage-3 bot with a vehicle called, a bot in an escape
box. `HuntedAway=1`: the hop farthest from the fed. `HuntedDry=1`: log only. Log: 'fedkit: hunted: record N lost x (y of z left), d m from
you' for the first 20 hits (all at KitLog=2) and 'is ordered to cover place k of [Hops] ... order n of the round'.
It cannot tell who hit the bot (police AI near it count) and does not make it shoot sooner: it is a GUESS that a cut tactic + a new
walk lets the soldier's own combat tactics start over, and that a bot that changes cover under fire is 'reacting'. It may take a bot
out of a fight it was winning. Needs `[Hops]` in the level's KLJoin.ini (the same list RestlessHop uses).

### 3.3 Level option for the aim/reaction fields: `kl_fa_bots_dyn.py ... --react veteran|elite`
ZSoldier 5 / 13 / 14 of the seven = the exe's own row (veteran 60 / 20 / 55, elite 90 / 0 / 60); accuracy (4) stays the persona's. ASSUMPTION: that
this makes the crew react or aim faster (see 3.1). Off by default. Smoke test: `build z_lanes\retomoto_full --react elite` PASSED
(kl_fa_bots_dyn check 0 FAIL, kl_fa_bots_rt check 0 FAIL, impact 0) and `diff` 'only the squad's steps were made anew' (its allowed ZSoldier fields
now include 5 / 13 / 14); the build was deleted (disk). It needs the dyn step of the chain re-run - NOT applied to y_active\DM09.

## 4. Keys proposed for the owner's ini (all untested)
```
[Bots]
Restless=5
RestlessHop=6          ; needs the [Hops] of y_active\DM09
[Fed]
Hunted=1               ; HuntedRange=4500 HuntedAlert=1500 HuntedDelay=250 HuntedGap=4  (defaults)
```
Order of trust: RestlessHop (an existing, run order; new only in its choice of place) before Hunted (a new trigger for the same order).

## 5. Live checks, in order (the lead; owner away; hook test build from `G:\kl_scratch\active\test`)
1. **H0** `[Bots] Restless=5 RestlessHop=6 MoveDry=1 MoveLog=2` on y_active\DM09 (idle player): 'move: 34 hop place(s) at 49 hold(s) of 7 gate(s) ...'
   at the level load; 'move: record N WOULD hop (dry run) from its hold (x, y, z) after 6.x s ... a cover place of the level's [Hops]' - at a gate hold,
   never twice to the same place in a row. FAIL: no 'hop place(s)' line (the file is not found: kljoin.c did not stamp it), or a hop line for a bot at no gate.
2. **H1** the same with MoveDry=0: 'move: record N hops from its hold ... - a cover place of the level's [Hops]' ~6 s after the bot reaches a gate hold; the bot
   moves 3 .. 18 m (positions with `[CrewHop]`-style pos lines or watch pictures), stands, hops again; the gate's wait still ends (the chain goes on when the squads
   are dead/30 s: 'record N (stage 1)' lines of the next gate); nobody dies at the hop more than at the control run (S3_DM09 style); no 'NOT ordered'.
3. **H2** count the stands: owner-style script over the log (stands >= 5 s per bot life; expect the longest <= ~7 s in the tower).
4. **F0** `[Fed] Hunted=1 HuntedDry=1 KitLog=2` as a fed (die early): 'fedkit: Hunted=1 ...' at start; per hit 'hunted: record N lost ... m from you';
   'record N WOULD be ordered (dry run) to cover place k'. This also answers TH (are the hits coming from the fed: the distance is in the line).
5. **F1** HuntedDry=0: 'is ordered' lines ~0.25 s after a hit and the squad mates 0.4 .. 1 s later; the owner's eyes: do they change cover when shot.
6. Only then `--react elite` on a rebuilt dyn step.

## 6. Assumed / rejected / not done
- ASSUMED: the hop places are walkable from the holds (checked by the stand-in path on the mesh, not by the game's pathfinder); a bot ordered a
  hop leaves the 'meant wait' correctly (the same order Restless (c) shifts with); RestlessHop at 6 s does not make the gate's squads' men
  shoot a hopping bot more (cover places of the same rules, 1 .. 18 m apart).
- REJECTED: hop steps as chain nodes behind a `TriggerDelay2` at each hold: the timer cannot be cancelled when the `TriggerActorsDead` ends
  the gate first, and fires later and orders the bot back (stale order). A `RandomTrigger` loop has the same flaw.
- NOT DONE: shorter room/loot waits in y_active\DM09; the window and the table have no hops; the fed's reaction fields (3.3) not applied; no harness for
  klfedkit.c (klmove's hop picker was tested alone: `G:\kl_scratch\active\hoptest`, PASS: random never the last, never within 3 m, away picks the farthest,
  other floor / other gate / no hold near -> none).
- Interaction: after a Hunted/RestlessHop order the defend block holds the hop place; klmove's Restless takes it for a new place of the chain (re-anchors,
  'a new place' resets its counts) and a bot at a hop is again 'at its place': it can hop from there after RestlessHop seconds.

## 7. Second round (2026-10-12 15:30, after the owner's first round with it: ship_w15, 15:00-15:06)

### 7.1 What that round showed (KLHook.log from '14:59:18.905 ==== KLHook loaded')
- '34 hop place(s) at 49 hold(s) of 7 gate(s)' loaded; ONLY 8 'hops from its hold' against 53 'given again'; longest stand 14.0 s (28.0 s before). He was through the
  tower fast (stage 1 15:00:56, lobby exit 15:03:00), so the gates opened early and the standing that is left is ON THE STREET, which had no hop places.
- Records 5 and 6 were sent to the SAME hop in one tick (15:01:52.766).
- Fed (back 15:05:23 on the street): 20 'hunted: ... lost' lines, 41 .. 77 m from him, all beyond HuntedRange 4500, none ordered; the street had no [Hops].
  The last four bots died within 65 s of his respawn.

### 7.2 Built
1. STREET HOPS (tools/kl_fa_bots_rt.py `street_hops`, run by `hops`, on by default): from the finished build's bots.json
   (plan.rt.street.lanes) the place each step of every bot's program ends at, every way of every fork, places under 60 apart kept once: 161 places (lobby, timed way,
   lane holds, rally, stop; x -5640 .. 5600, z -7162 .. 10583). ONE group 'street': its holds and its hops are the same list, so a bot standing at any of them may shift to another
   within 18 m on its floor. Every one of the 161 has at least one other within 3 .. 18 m (median 15, min 2). They were laid by the lanes' rules (clear of parked vehicles, off the
   police posts); the way BETWEEN two of them is not checked (ASSUMED walkable; the stations of a lane are 5 .. 24 m apart). [Hops] now: Gates=8, 49 tower holds + 161 street
   places, 34 + 161 = 195 hops (hook capacity raised to 320 / 320 / 24 gates).
2. RESERVATION (klmove.c): a hop one bot was sent to is no hop for another bot for 10 s (KLMV_HOP_KEEP); `klmv_hop_pick(anchor, bp, last, who, away, out)`, `klmv_hop_take(k, who)`;
   used by RestlessHop and Hunted alike. Harness (G:\kl_scratch\active\hoptest) PASS: bot 2 gets none right after bot 1's take, the hop after 10 s. (First version had a wrap bug
   in the time test; found by the harness, fixed.)
3. HUNTED at street distances (klfedkit.c section 8): HuntedRange default 9000 (90 m); with no hop near (or all taken) a FALLBACK: a step of HuntedPace (500) to a random side, a
   place 3 m or more away - needs no level data. New `HuntedFire=1` (default 0): the bot that was HIT is ordered TOWARDS the fed, HuntedStep (1500) along the line, until it is HuntedNear
   (2500) from him; the bots alerted with it take a cover place / the step aside. Log: 'is ordered TOWARDS YOU' / 'to a cover place of [Hops]' / 'a step aside to'.

### 7.3 What a stock soldier does when hit (read, not finished) and why HuntedFire does not hand over a target
The NPC's damage routine (0x61a980) takes soldier = [actor+0x77c], scales the hit by [soldier+0x704] (0x61acd9 ff.) and builds a message with 0x404ef0 (a 0x18c-byte frame, called at
0x61abb6 / 0x61b064) before it settles health - that message is how the soldier is told. I did NOT follow 0x404ef0 or the soldier's reaction slot, found no routine of the form 'add this
actor to the soldier's targets', and klgrudge.c does not call one either (it only writes the damage sums the target test 0x882470 reads: DATA, no call - the brief's 'sense-manager call'
is klbot's record mask 2 + 0x4322f0 for a traitor). So the hook cannot hand a bot its attacker; HuntedFire is the order call only: a bot that walks at the fed meets his line of sight
and fights by its own tactics. ASSUMED. Whether the bots 41 .. 77 m away did not turn because they did not SEE him (sight range [0x168d7c0]+0xc0 x vision factor; the dyn build gives the
crew x2) or because their tactics held them is not known. If HuntedFire fails, the next step is to follow 0x404ef0 and the soldier's slot for that message.

### 7.4 Ini lines for the owner
```
[Bots]
Restless=5
RestlessHop=6
[Fed]
Hunted=1                ; HuntedRange=9000 (default now)
HuntedFire=1            ; the hit bot walks at you (HuntedStep=1500, HuntedNear=2500); HuntedPace=500 for the step aside
```
### 7.5 Live checks (extra)
- H3 the street: 'move: ... 195 hop place(s) at 210 hold(s) of 8 gate(s)'; on the street 'hops from its hold ... a cover place of the level's [Hops]' for bots standing 6 s; two bots never to the
  same place within 10 s (compare the places in a tick).
- F2 as a fed on the street with HuntedFire=1: 'hunted: record N is ordered TOWARDS YOU' 0.25 s after a hit, then the bot's position closer to him (watch pictures) and, the real question,
  'you lost' lines (Balance Log=2) from heisters or the owner's eyes: do they shoot back. HuntedDry=1 first.
