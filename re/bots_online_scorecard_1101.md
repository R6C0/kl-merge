# Online bots scorecard, Q31 (ship1102 candidate ini), 2026-11-01

Offline analysis of the 21 host logs of c9's Q31 run (week-plan T3 "Online bots loot, carry, bank and escape like Arcade"). Game not launched, no code edited.

Sources: `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo\Q31_<MAP>\inst1\KLHook.log` (host), kit `C:\kl_build_1024\c9_1028\q31` (maps.txt, `Q31_<MAP>_run.txt`). Log texts: `klhook/klbotfill.c`.

## Read this first (limits)

- Arcade baseline: NONE exists per map. The BO*/COVER*/ALL2* benches are online bot benches, not Arcade runs. Arcade bots use the game's own brain (ZLootTactic / ZBoardEscapeVehicleTactic, `re/bots_online_arcade_1028.md` sec. 1), which writes no `botfill:` lines. So no number below is an Arcade number. The "gap" is judged against the Arcade design (bots fight for loot, call the van, board with the loot), not measured against an Arcade run. An Arcade per-map baseline needs an Arcade bench with a stack/board counter (nothing logs one today).
- Only round 1 is a full round. The bench stops about 33 s into round 2 (`Q31_<MAP>_run.txt`: "ROUND 2 running"), so round 2 has no summary lines. Per-round columns below are round 1. Round 2 only shows spawn (7 bots every map) and trigger fires.
- Bank: `OnlineBank=0` in the candidate ini (log: `botfill: bank: OnlineBank=0, OnlineBoardAll=1, ...`), so there is no ledger line anywhere. "Carried" is the hook tally from the round summary. Commit 39697dae7 already says ship1102 needs `OnlineBank=1` + `OnlineBankCredit=1` next to `Take=2`. Until then "$ banked" cannot be scored.
- "Aboard" is the hook's count (`BOARDED ... hook tally only`), not a physical boarding. "Far-counted" = bots credited by `OnlineBoardAll` (`boardall: bot N ... M m from the escape point ... counted aboard`, `klbotfill.c:992`) from far away, i.e. left behind in fact.
- Van call time = seconds after `tactics: round 1 starts`. Round clock is 250 s (DM09 1100 s bench cap, same clock).

## Scorecard (round 1, host seat)

| Map (slot) | Bots | Armed stacks | Stacks taken | $ carried | Van call s (why) | Aboard / given orders | Far-counted | Dead | Stack give-ups / gone | Get-up down / sent / up s | Trigger FIREs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DD01 (F01) | 7 | 0 (+58 behind shut door) | 0 | 0 | none | 0 / 7 | 0 | 0 | 0 / 0 | 0 / 0 / - | 1 (spurious, see G3) |
| DD02 (F02) | 7 | 24 | 14 | 3.54M | 271, after clock end | 6 / 6 | 6 (to 60 m) | 1 | 7 / 0 | 0 / 0 / - | 16 |
| DD03 (F03) | 7 | 12 | 7 | 4.20M | 188 (all in range) | 7 / 7 | 0 | 0 | 6 / 0 | 0 / 0 / - | 8 |
| DD04 (F04) | 7 | 10 | 8 | 3.50M | 187 (wait ran out) | 7 / 7 | 2 (to 26 m) | 0 | 6 / 0 | 0 / 0 / - | 11 |
| DD05 (F05) | 7 | 6 | 0 | 0 | 165 (wait ran out) | 7 / 7 (all tally 0) | 0 | 0 | 0 / 2 | 0 / 0 / - | 7 |
| DD06 (F06) | 7 | 8 | 2 | 3.13M | 185 (all in range) | 6 / 6 | 0 | 1 | 0 / 0 | 0 / 0 / - | 12 |
| DD07 (F07) | 7 | 5 | 0 | 0 | 200 (all in range, 2 bots) | 2 / 2 | 0 | 5 | 0 / 0 | 0 / 0 / - | 8 |
| DD08 (F08) | 7 | 47 | 14 | 0.71M | 209 (clock low) | 2 / 2 | 0 | 5 | 2 / 0 | 0 / 0 / - | 9 |
| DD09 (F09) | 7 | 6 | 0 | 0.04M | 131 (all in range) | 7 / 7 (6 tally 0) | 0 | 0 | 0 / 5 | 0 / 0 / - | 7 |
| DD10 (F07 p3) | 7 | 8 | 2 | 1.15M | 186 (wait ran out) | 4 / 4 | 3 (to 33 m) | 3 | 4 / 0 | 0 / 0 / - | 39 |
| DM01 (F01) | 7 | 5 (+1) | 0 | 0.56M (no GRABBED line) | 175 (all in range) | 5 / 5 | 0 | 2 | 1 / 0 | 0 / 0 / - | 6 |
| DM01B (F03) | 7 | 12 | 5 | 0.99M | 220 (clock low) | 4 / 4 | 1 | 3 | 9 / 0 | 0 / 0 / - | 17 |
| DM02 (F02) | 7 | 41 (+8) | 12 | 1.42M | 198 (wait ran out) | 5 / 6 | 4 (to 34 m) | 1 | 18 / 0 | 0 / 0 / - | 0 |
| DM03 (F03) | 7 | 14 | 9 | 4.70M | 126 (wait ran out) | 7 / 7 | 0 | 0 | 2 / 0 | 0 / 0 / - | 11 |
| DM03A (F07) | 7 | 13 | 6 | 1.20M | 171 (wait ran out) | 6 / 7 | 3 (to 47 m) | 0 | 17 / 0 | 4 / 7 / 12.0, 19.0, 20.0, 11.0 | 6 |
| DM05A (F01 p3) | 7 | 11 | 5 | 1.65M | 205 (clock low) | 5 / 6 | 3 (to 54 m) | 1 | 9 / 0 | 3 / 0 / 20.4, 18.6, 21.1 | 44 |
| DM06 (F04) | 7 | 4 | 0 | 0 | 138 (all in range) | 7 / 7 (all tally 0) | 0 | 0 | 0 / 0 | 0 / 0 / - | 2 |
| DM06B (F02 p3) | 7 | 15 | 12 | 2.98M | 180 (wait ran out) | 6 / 6 | 1 | 1 | 7 / 0 | 0 / 0 / - | 11 |
| DM07 (F06 p3) | 7 | 11 | 8 | 2.38M | 70 (wait ran out) | 6 / 6 | 0 | 1 | 0 / 0 | 1 / 0 / 18.3 | 3 |
| DM09 (F06) | 7 | 21 | 14 | 5.08M | none | 0 / 7 | 0 | 0 | 13 / 0 | 0 / 0 / - | 10 |
| DM11B (F04 p3) | 7 | 16 | 8 | 3.00M | 190 (wait ran out) | 7 / 7 | 1 (60 m) | 0 | 3 / 0 | 0 / 0 / - | 4 |

Totals over 21 maps: 147 bots spawned; 2 maps with no van call; 1 call after the clock ended; 5 maps with 0 stacks taken (DD01, DD05, DD07, DD09, DM06) plus DM01 (tally from a source with no GRABBED line); about 30 bots counted aboard from 13-60 m away; 24 bots dead (DD07 5, DD08 5).

Other findings (no gap by themselves):
- Trigger FIREs (OnlineTriggers=1) fire on all 20 maps with boxes (DM02 has 0 in R1). The FIRE count does not map to cops spawned; no cop census was compared.
- Get-up: 11 downs seen on the host in R1 across DM03A, DM05A, DM07 (R2 DM11B 1). DM03A: 7 orders, 4 rescues, rose after 11-20 s. DM05A and DM07: "no free bot within OnlineGetUpRange 2500 cm (nearest on this floor 5867 / 3380 cm)", seat rose alone after 18-21 s. That is Arcade-range behaviour on purpose (`re/getup_arcade_range_1101.md`: Arcade RushRange 25 m), not a strayed-bot defect.
- Round-2 evidence is only the start (bots re-spawn: 7 each map).

## The worst gaps vs Arcade

### G1. The van is never called, or called after the clock ended (DM09, DD02; DD01 see G3)

DM09: 14 stacks and $5.075M carried, 0 aboard, no call. The bots' escape target is the van object at a bogus place (y = -59842, i.e. 600 m below the map), so they walk toward nothing and never reach the exit trigger; the log is silent from +137 s to the clock end.
- `Q31_DM09\inst1\KLHook.log` 12:23:37.457: `botfill: tactics: bot 1 (actor 37151930) -> escape van 36e15060 at (24235, -59842, 13883) with tally 600000 (2 grab(s))`
- 12:25:50.450: `botfill: tactics: round summary: 7 bot(s) given orders, 14 stack(s) taken, 5075000 total (hook tally, not the game's), 0 boarded, 7 stack(s) given up`
- 12:25:28.986: `van probe: state 2, group [+0x1e4] 36e132d0 at (0, 0, 0), boarding object [+0x1e0] 3711c650 at (-1852, 121, 8420)`. The real boarding object is at y 121.

DD02: the bots spend the round in 4-leg waypoint walks (24 `waypoint leg N of 4 timed out` lines, leg 4 stops 29-110 m short), the van is called at +271, after state 5, by `OnlineGatherLateS`; the six "aboard" are all boardall credits 4-60 m away.
- `Q31_DD02` +271: `van: gather: calling the van (the clock is low (OnlineGatherLateS)): 6 bot(s) walking, the farthest 63 m from the box (limit 12 m)`
- `+98 bot 3: waypoint leg 4 of 4 timed out (98 m from (-24, 6010, 3262), 15 s on the leg, dy -0.0 m, limit 15 s): on to the exit trigger`

Next fix:
- DM09: `klhook/klbotfill.c:1657` (the `-> escape van` order, target `vpos`) and `klbotfill.c:1652-1655` (the condition that picks van over exit trigger). Reject a `van` whose `vpos` is more than a sane height from the bots (or a van that is not at its stop, see the "one at the origin = not here yet" scan text) and take the exit-trigger branch (line 1658). New ini key, gate: `[BotFill] OnlineVanPosSane=1` (recommended on, 0 = today). Proof line: a `tactics: van: target ... implausible` log plus a call before +200 s.
- DD02: existing keys, ini only: `OnlineLegStallS` (`klbotfill.c:220`, default 0 = off; a leg stalled N s re-paths) and `OnlineLegScale=1` (`klbotfill.c:217`, the leg limit scales with the distance; the comment there records DD08 legs timing out with 28-79 m left). The same change should cover DD08 (36 leg time-outs). Also raise `OnlineLateExit` above 75 for this map set only if the legs stay slow (`klbotfill.c:166`).

### G2. Loot-starved: bots hold behind guarded stacks all round (DD05, DD07, DM01, DM06; DD03 and DD10 partly)

Four maps take 0 stacks while 4-6 stacks are armed, with no cop-fight: the guard test marks every free stack guarded, the bypass needs at least 8 free stacks and these maps have 3 to 5.
- `Q31_DD05` 11:06:33.109: `guardmode: round scan: 3 cop(s) read live, 6 money stack(s), 6 free stack(s) of which 3 guarded (radius 25 m, floor gate 400 cm; bot 0 sees nguard 3)`
- `Q31_DD05`: `tactics: bot 3 (actor 4f439520): 3 free stack(s), all with a live cop within 25 m: it holds (until a stack is clear, OnlineGuardTake=0) while they are cleared` (bots 3, 4, 5, 6 the same)
- `Q31_DD07` 11:24:02.078: `bot 0 (actor 57e722a0): no stack to take (0 guarded, 57 s idle, clock left 192 s) and nothing carried: goes to the exit to call the van (OnlineIdleVan)`; round summary: `2 bot(s) given orders, 0 stack(s) taken, 0 total ... 2 boarded` (5 of the 7 died).
- `Q31_DM06` 12:14:56.580: `no stack to take (0 guarded, 110 s idle, clock left 139 s)`; `Q31_DM01` 11:50:45.519 the same, 155 s idle.
Result: DD05, DD07, DM06 carry $0; DM01 $0.56M without any GRABBED line.
Arcade bots go for the loot and fight the cops on the way; the ship ini has `OnlineGuardTake=0` (they hold for ever), the 30 s fallback was turned off because it got all 7 bots killed in BO8c (`klbotfill.c:155`).

Next fix: ini only, existing key `[BotFill] OnlineGuardBypassMin` (`klbotfill.c:157`, default 8, used at `klbotfill.c:1610` via `kgg_bypass_ok`). Set 3 for a bench (DD05 has 3 free stacks, DM06 4, DD07 5, DM01 5), keep `OnlineGuardBypassGapS=15` (`klbotfill.c:158`) so one bot at a time goes in. Bench maps DD05, DD07, DM01, DM06 and watch `guardmode: ... all N free stacks guarded: takes stack` and the death count (DD07 already lost 5 of 7 without taking anything). If it kills the bots, the alternative gate is `OnlineGuardWalk` (`klbotfill.c:1624`, wk-move, not run live).

### G3. DD01 (Subway): bots inert for the whole round

58 stacks, all behind a shut door, 0 armed; the bots read (0, 0, 0) for 90 s; no exit trigger was known at +155 s; the van was never called; the one trigger FIRE counted all 7 bots "inside" a box at the origin.
- `Q31_DD01` 10:33:00.659: `tactics: scan: 18511 objects, 7 live Ally bot(s), 0 armed stack(s) (+58 behind a shut door) of 183 money object(s), van 00000000`
- 10:37:07.198: `bot 0 (actor 553068f0): did not reach the exit trigger after 90 s (269 m from the trigger, bot at (0, 0, 0)): back to idle`
- 10:33:08.152: `trig: FIRE box 557eb920 via 0x6ae730 (7 bot(s) inside, need 6, re-arm -1, ecps 4, efamps 7, fire #1)` with the bots at the origin.
- 10:35:35.715: `wants the van but it is not here and no exit trigger was found to call it from`

Next fix: (a) `klbotfill.c:584-639` (the trigger scan/inside test): skip a bot whose place is (0,0,0), as the guard scan already does (`guardmode: ... cop(s) at (0,0,0) skipped (OnlineGuardLiveOnly)`); gate: reuse `OnlineTriggers` (log first with `OnlineTriggers=2` dry). (b) the Subway door: the scan counts the shut-door stacks (`klbotfill.c:1478` scan) but nothing opens the door; a Subway scripted-start fix is a new key `[BotFill] OnlineOpenDoors` (not present). The bots at (0,0,0) means they are not placed until a stage event; confirm with the joiner log before coding. In Arcade the squads kick the door open ("Squad#02..08 ... KickDoorBehaviourRout_loot_room_01", `re/stock_map_bots.md:45`).

### G4. Stacks are gone before the bots arrive (DD09: 0 stacks, DD05: 2 of 3 orders)

DD09 has 6 armed stacks; 5 orders end within 13 s with "gone", the sixth is left at 2 of 45 parts; the bots then carry $40k and 6 board empty. Nothing fired yet (first FIRE at +32 s), no human played.
- `Q31_DD09` 11:40:04.427: `botfill: tactics: bot 4 (actor 4f253e10): stack 28b1b760 is gone before it got there (taken by someone else?)` (4 more lines at 11:40:04-06)
- 11:40:05.424: `lootparts: bot 3 left stack 28b1b5d0 after 2 of 45 parts (partial tally 40000; stack gone or hidden (taken by someone else?))`
- `Q31_DD05` 11:06:42.106 and 11:06:44.189: `stack 28ae50c0 / 28ae4da0 is gone before it got there`, then 11:07:07.540 `bot 2 starts stack 28ae5180 ...` and 11:07:08.516 `left stack 28ae5180 after 0 of 39 parts (... stack gone or hidden)`.
Cause unknown: a stack read as armed at the round start but empty/hidden seconds later. Possibly a stale scan (stacks the stock script hides at the start) or a second reader emptying it.

Next fix: diagnostic first. At `klbotfill.c:1510` (the "is gone" log) and `klbotfill.c:1565-1575` (the `left stack` log) add the stack's `[+0x34]`, state byte and node-hidden flag to the line, and in the scan at `klbotfill.c:1478` drop a stack whose state is not "armed" (the `+N behind a shut door` code already classifies). Gate: a new `[BotFill] OnlineStackRecheck=1` (recommended on once benched). Bench DD09 and DD05, compare the line before and after.

### G5. "Aboard" is counted for bots left far from the van (DD02, DM02, DM03A, DM05A, DD10, DM11B)

About 30 bots are credited by `OnlineBoardAll` at 13-60 m (`OnlineBoardAllM=6000`, `klbotfill.c:274`). They carry the loot in the tally but are not at the van. The score cannot pay them (OnlineBank is off); in Arcade only a bot that reaches the escape box boards.
- `Q31_DD02` +272: `boardall: bot 2 (actor 555dcfb0) tally 825000, 60 m from the escape point, van state 5: counted aboard`
- `Q31_DM05A`: three boardall lines at 44, 54 and 44 m; `Q31_DM11B` one at 60 m.
- DM02: 4 bots at 5-34 m, 5 of 6 aboard.
The cheap cut: shrink the credit radius. The costly truth: the bots do not arrive (see G1 for DD02; DM05A/DM03A are tower maps with long walks).

Next fix: ini only, `[BotFill] OnlineBoardAllM` (`klbotfill.c:274`): 1600 (= `OnlineExitCrowd`) makes the summary honest, and the bots that are further away count as left behind. Better for parity: `OnlineBoardTeleport=1` (`klbotfill.c:226-228`, `OnlineBoardTeleportS=10`, `OnlineBoardTeleportM=4000`) moves only a bot that nearly made it, but its own comment says "not Arcade behaviour". Combine with `OnlineBank=1` + `OnlineBankCredit=1` (39697dae7) so the scorecard has a "banked" column next time.

## Stray and stuck bots (the "2 strayed" note)

Nothing in Q31 shows a bot lost in the world on a map that otherwise works. Strays are of three kinds: (1) never called, G1; (2) far-counted, G5 (30 bots); (3) `did not reach the exit trigger after 90 s` lines on 14 maps. Kind 3 is the 90 s walk timeout, not a stuck bot: the same bots are in the van-call gather 40-90 s later (DD05, DD09, DM11B: 7 of 7 aboard). Only DD01 (bots at the origin) and DD07 (68-78 m short at +90 s, 2 of 7 left alive) are real.

## Suggested ship1102 ini additions, in order of value

1. `OnlineBank=1`, `OnlineBankCredit=1` (39697dae7).
2. `OnlineGuardBypassMin=3` (G2): ini only, bench DD05/DD07/DM01/DM06 first.
3. `OnlineLegStallS=<N>` and `OnlineLegScale=1` (G1 DD02, DD08): bench DD02 and DD08.
4. `OnlineBoardAllM=1600` (G5), after 1 so the bank is on.
5. Code, new keys: `OnlineVanPosSane` (G1 DM09), the (0,0,0) trigger skip (G3), `OnlineStackRecheck` (G4).
