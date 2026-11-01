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

## Gap 4 diagnosis (11-01)

Offline read of `klhook/klbotfill.c` (line numbers of HEAD 7b5ac0b4e) and the finished Q31 host/joiner logs (`...\KL_PortTools\build\klhook\solo\Q31_DD09`, `Q31_DD05`, also `Q31_DD07`, `Q31_DM06`, `Q31_DD03` for comparison). No Q32_DD09 / Q32_DD05 folder existed when this was written.

### Code path
- Scan `klbotfill.c:1435-1449`: every `ZOnlineMoneyCtrl` in the registry (0xe09e38, count 0xe0e63c); skips type `+0x38 == 1` (drop pool), amount `+0x34 <= 0`, `+0x6c` (armed) == 0, `+0x5c` shut door.
- Order: bot gets `target` and phase 1. "Gone" test `klbotfill.c:1530`: vtable != money vt, or `+0x34 <= 0`, or `+0x6c == 0`, or no node -> log at `:1531`. The phase-4 twin is `:1569` ("stack gone or hidden").
- Take: `:1547-1549` (lump) and `:1591` (timed parts) call the game's 0x4e3f40 only AFTER the bot is within `OnlineTacticsNear` (150 cm) of the stack. Nothing else in the hook touches `+0x34`.

### Evidence
1. It is not the hook's take and not a bot. DD09 round 1 has `round summary: 7 bot(s) given orders, 0 stack(s) taken, 40000 total`; the only take is bot 3's 2 parts (`11:39:57.341 bot 3 starts stack 28b1b5d0`, `left ... after 2 of 45 parts (partial tally 40000`). Bots 4 and 5 were still 27-30 m away when their stacks went (`11:39:51.351 ... bot 4 ... -> stack 28b1b760 (1200000) ..., 27 m away`; `11:40:04.427 bot 4 ... is gone before it got there`). No `GRABBED` line for those stacks. Take=2 cannot remove a stack early: it only runs at arrival.
2. It is real depletion of `+0x34`, not a hidden flag. The loot bar (`klonline_read.c:134-148`) sums `+0x34` only, ignores `+0x6c`, and falls with it: DD09 `11:40:01.364 on the map 5960000` -> `11:40:04.654 left 3000000` -> `11:40:05.194 left 900000` -> `11:40:05.741 (read not yet, init 0, left 0)`; `11:40:11.399 on the map 0 (NO controller read)`. The 139 money objects stay in the registry (`scan: ... 0 armed stack(s) ... of 139 money object(s)`), so they are not freed; amounts are 0.
3. It is not a human: the host seat stands still (`pos host-c/-d: me #0 (-14102, 102, 24903)` both reads); the first trigger FIRE is at +32 s.
4. It is replicated game state, not a host-only hook effect: the JOINER's log shows the same drain at the same moment (`Q31_DD09\inst2`): `11:40:04.320 left 3860000`, `04.866 left 1800000`, `05.428 left 900000`. The joiner has no BotFill take.
5. It starts at the same round-clock second on both maps and runs ~2 s: DD09 `played[+50]=11.6` at 11:40:02.9, drain 11:40:04-05 (about +13 s); DD05 `played=11.5` at 11:06:44.4, first stack gone at `11:06:41.6 (17%)`, bar `3710000 -> 3150000 -> 2360000` over 11:06:41-46 (about +8-13 s). Round 2 of DD09 repeats it at +13 s: `11:45:05.982 left 6000000` -> `11:45:18.603 left 4800000` -> `19.692 left 900000` -> `20.786 left 0`.
6. Each loss lines up with a stock script event, 1 to 1 on the maps where it happens. `mfprobe: SCRIPT 0x6d2500` (CPPScript slot 56, ZGeneric/ZCivilian; the owner is a team-1 `ZFFActor` named 'Ground' standing 15-20 m south of the stacks):
   - DD05: `#1 11:06:41.409` -> bar 17% at 41.631 and bot 1's stack 28ae50c0 (790000) gone at 42.106; `#2 11:06:44.012` -> bar 3150000 at 44.354 and bot 0's stack 28ae4da0 (560000) gone at 44.189.
   - DD09: `#2 04.107, #3 04.262` -> two stacks gone at 04.427; `#4 04.606, #5 04.769, #6 04.842` -> bar 3.0M at 04.654, 0.9M at 05.194, last stack gone at 06.437.
   - DD07 `#1 11:23:19.174` -> bar 20% at 19.415, then 40% and 60% as `#2`, `#3` fire (11:23:20.9 / 22.5). DM06 `#1 12:13:18.5` -> bar 23% at 12:13:23.6.
   - On maps without the drain (DD03, DD02, DM02...) the same script also fires (`Q31_DD03 10:49:42.230 #1`) but the bar moves only 1-2% a second (the bots' timed parts), so the script is a marker for "an actor died / was removed", not the take itself.
7. Maps where it happens (DD05, DD07, DD09, DM06) are the ones with the guarded-stack pattern of G2: `DD05 guardmode: round scan: 3 cop(s) read live, 6 money stack(s), 6 free stack(s) of which 3 guarded`. re/bots_loot.md section 5 already records "money on armed people (where the person is)" as takeable-from-the-start, and `Deactivate` / the take as the two things that end a stack.

### Answers to the questions
- Taken by a human? No (evidence 3). By another bot through the hook? No (1). By a stock bot/trigger path (ZTriggerBox2 serving team-2 actors in Arcade rules)? Possible but unproven: bots were 27-50 m from the stacks.
- Dropped pool (type 1)? Skipped by both the scan and the bar, so it cannot explain a falling bar.
- Container that empties itself? Best fit (GUESS): the stack is money tied to an armed person or scripted group (a team-1 'Ground' actor), and the stock level script depletes it when its carrier event fires (the 0x6d2500 hits). The loot is then paid out in the game's own accounting, not to the bots.
- Wrong field / online tally 0? No: `+0x34` is read the same way by the scan, the take, and the HUD bar, and the joiner agrees. Take=2 early? No (code and evidence 1).
- Type `+0x38`, registry: not logged for the vanished stacks. The scan only counts 139 objects; no per-stack type or state is in any line. This is the missing datum.

### Smallest fix (default off, diagnostic first)
1. New key `[BotFill] OnlineStackProbe` (default 0, recommended on for benches only). In the gone branch (`klbotfill.c:1531`) and the phase-4 stop (`:1569` log line) append `+0x34`, `+0x38`, `+0x64`, `+0x6c`, `+0x5c`, the node-hidden bit (ent flags 0x400) and the `[+0x80]` looter. Extend the scan summary line (`:1499`) with the per-type counts of the 139 (type 0 / 1 / 2) and, once per round, a one-line dump of each armed stack at the round start: address, type, amount, state, and the nearest team-1 actor within 30 m with its distance.
2. If stock depletion by an actor event is confirmed, the fix is a re-pick, not a prevention: when a stack goes "gone" while its bot is walking, the next scan already hands the bot another stack, but with 0 armed left the bot idles (DD09: `bot 6 ... no stack to take (0 guarded, 20 s idle ...)`). Nothing to add in the hook for that case; the money is simply gone on the stock rules. To keep it for the bots, the lever is the stock cause (the actor event), to be found with the probe below.
3. Optional log-only detour of 0x4e3f40 (`OnlineStackProbe=2`, in `klbotfill.c` next to the call at `:1548`): log `caller return address`, `this`, the amount and `+0x38`/`+0x64`, for calls whose `this` is not the one the hook is calling right now (a static flag around the hook's own two call sites at `:1548`/`:1591`). That names the stock caller of the depletion.

### What a bench must show
- A line such as `botfill: stackprobe: 0x4e3f40 by stock caller=XXXXXXXX this=28b1b760 amt=1200000 type=2 state=1 (hook call 0)` at 11:40:04 in the DD09 host log, with the caller RVA resolving to a script/trigger update (0x626ec0 = ZTriggerBox2, 0x727cb0 = the record state machine, 0x4c95d0 = Deactivate) or to the 0x6d2500 family.
- And the per-stack round-start dump showing a team-1 actor within 30 m of each stack that vanishes. If the caller is 0x626ec0 with a team-2 actor, the Ally bots' proximity (or `OnlineTriggers` FIRE) is taking it; if it is a script, the stacks are scripted prizes and DD09 / DD05 need a different loot rule (bots should wait for the carrier event, or the stock script gate be left untouched).
- Run: DD09 and DD05 online, `--n 2`, `OnlineStackProbe=2`, compare against DD03 (no drain) as control.

## Q33 DD05 A/B vs Q32 DD05 (11-01 ~16:35, ce)
Q33 = ship1103 + OnlineGuardBypassMin=3 + OnlineBoardAllM=1600 (c9 kit q33). PASS, 0 faults, both seats into round 2.
- Gap 2 key works: at round start (6 stacks, 3 guarded, 3 live cops) bot 3 "all 3 free stacks guarded: takes stack 28f07780
  with the fewest cops" (Q32: all four bots HOLD). Others still hold (only one release per 15 s).
- But it gains nothing yet: the stacks drain 6 -> 0 in 22 s (Q32: 24 s) before bot 3 covers the 42 m, and every bot walks
  to the exit with tally 0 in BOTH runs. Gap 4 (stack drain) masks gaps 2 and 5 on DD05; grade those again after gap 4.
- DD05 exit trigger is found ~1 s after the first "no exit trigger" line (lazy scan), same in both runs; harmless.

## SP1 stack probe (11-01 16:49-17:14, ce): OnlineStackProbe=2 on DD09 DD05 + DD03 control
Kit C:\kl_build_1024\week_1028\sp1 (ship1103 + the key, TEST hook stackprobe_test bdd1fa08). 3/3 PASS, 0 faults, both seats into round 2.
- Level 2 never ran: `patch REFUSED 004e3f40 +6 ... inside a range kl2.exe's integrity checks hash`. A session run cannot patch there,
  so level 3 (commit 0fe34f0e2) uses a hardware write watch (DR0, no code patch) on the first armed stack's +0x34 for 40 s instead.
- NEW: the type splits the maps. Draining maps DD09 / DD05: stacks are type 0 (t0 6/6). Control DD03 (no drain, the bar moves 1% per
  second with the bots' timed parts): stacks are type 2 (t2 12/12). Type 1 = 133 / 125 drop-pool objects, all armed in round 1 and
  none armed in round 2 on every map.
- DD09 round 2: 6 stacks in state 2 (round 1: state 1). At +13 s all 6 go amt 0, state 3, armed 0. The bar goes 6.0M -> 3.9 -> 1.8 ->
  0.9 -> 0 in 1.6 s and the type-1 armed count rises 0 -> 2 -> 5 -> 6, one per stack: each drained stack arms a drop-pool
  object, as if the money were DROPPED, not taken. No team-1 actor within 30 m of any DD09 stack.
- DD05: 9 of the 12 dump lines (2 rounds) have a team-1 actor 0.0 m from the stack, so on DD05 the money sits ON actors (money
  carried by armed people). It drains 4.5M -> 0 between +19 and +29 s of round 2.
- Reading (GUESS, SP2 checks it): a type-0 stack is "loot on a person / dropped on an event". The stock rules empty it into a
  type-1 drop pool when its event fires, so the bots' scan (which skips type 1) loses it. If SP2 confirms this, the fix is to let bots
  follow the stack's money into the newly armed type-1 objects (key OnlineDropFollow, default off), not to block the drain.
- Next: SP2 = OnlineStackProbe=3 on DD09 + DD05 (TEST hook stackprobe3_test 1cc357df, kit C:\kl_build_1024\week_1028\sp2), after
  c9's SHOTS2 / Q33 / Q34. Look for `WATCH 'stack` lines: the writer, and whether a type-1 object is armed in the same frame.

## Gap 4 RE + OnlineDropFollow (11-01 ~17:40, ce; static read, not run live)
- Chain (disassembly): actor death/removal -> CPPScript slot 56 0x6d2500 -> 0x4988f0 on [actor+0x8ec] (the carried money ctrl):
  0x6f9410(C, 0) empties the type-0 stack (amt 0, state 3, armed 0), then the rules' drop spawn (+0x324 online, 0x8f2f60) arms a free
  type-1 pool object via 0x4ef9a0 with the SAME amount at the CARRIER's position, Activate(1) = state 2 for ~3 s (GUESS: the constant).
- The game's online take pays a type-1 drop whole in one 0x4e3f40 call (0x6138a4/0x613951); 0x4e3f40 has no type check.
- Commits d906a4ddb + 32f0c75fb: OnlineStackProbe>=1 logs every armed drop and the stack that drained within 3 s (equal amount yes/NO);
  new [BotFill] OnlineDropFollow (recommended off until benched) + OnlineDropFollowM (1500): a bot whose stack went gone walks to the drop
  (equal amount within +-3 s of the drain: up to 80 m), waits out state 2, takes it whole (Take=2). Workflow review: SAFE_TO_MERGE.
- Bench: SP2 = OnlineStackProbe=3 + OnlineDropFollow=1, DD09 + DD05, TEST hook week_1028\dropfollow_test a40d6834 (SHIP twin
  dropfollow_ship d1c03cd5), kit week_1028\sp2. PASS = 'drop armed ... equal amount yes' lines and 'dropfollow: ... GRABBED' with a tally > 0.

## G3 DD01 research (11-01)

Cause: the live `KLExpansion\Maps\DD01` folder has no `F01_Main.bots.zip` (DD02..DD09 have one). The stock `merc_bot_squad` scripts are eHeistOnly in the plain archive, so online they never run and nothing places the 7 Ally actors: they are spawned, alive (health 280) and read (0,0,0) all round. The hook reads the right node (`+0x460` gives real positions on DD04).
- `botgate: WARNING slot F01: Ally bots ON but no .bots.zip next to ...\DD01\F01_Main.zip` in `Q31_DD01` (10:32:42) and `Q32_DD01` (13:27:38); DD04/DD02 log `botgate: slot F04 role 2: Ally bots ON -> ...\F04_Main.bots.zip`.
- Staged copy exists: `C:\kl_build_1024\botsstock_1026\DD01\F01_Main.bots.zip`; live `F01_Main.zip` md5 27680110... equals `SRC_MD5.txt`, so it still fits. install_any.py placed one on 10-26 ~19:20; a later bench undo probably removed it (GUESS).
- Explains: `exit walk from (0, 0, 0)` for all 7 at +156 s; `did not reach the exit trigger ... bot at (0, 0, 0)`; the spurious `trig: FIRE` (7 bots stacked at the origin); the 58 `+0x5c` "behind a door" cases (Alu cases in DL10_CtrlRoom behind kick doors 03/04; the squads' KickDoorBehaviourRout -> KickdoorMonitor -> DoorOpened clears them; humans are not gated by `+0x5c`).
- Not the scripted humans (DD04 has the same fixed host and its bots move at once). A real gap for any online DD01 round without the zip.
- Not to build: clearing `+0x5c` by a data write (reproduces BOS1's stall, kick-door pathblockers stay shut).

Code (default off): `[BotFill] OnlineUnplacedGuard` (`kvp_all_unplaced`, `klbotfill.c` before the trigger tick): all bots at the origin more than 10 s into a round -> log once per round and give the order loop no bots. It only makes the failure visible and stops useless orders; the fix is the data file. `OnlineTriggerOriginSkip` (G3 a) stays the trigger answer.

Bench recipe change: install the zip first (owner): `python C:\kl_build_1024\botsstock_1026\install_any.py DD01`, then run DD01 with `OnlineTactics=1 OnlineHost=1 OnlineTriggers=1 OnlineTriggerOriginSkip=1`. Control run without the zip adds `OnlineUnplacedGuard=1`.
PASS (with zip): `botgate: slot F01 ... -> ...\DD01\F01_Main.bots.zip` instead of the WARNING; `tactics: scan:` shows N armed stack(s) with the +M shut-door count falling, or bots take the exit and call the van by +155 s; `exit walk from (x,y,z)` non-zero; no `bot at (0, 0, 0)`; round summary shows a van call and boarded bots. PASS (control, no zip): one `OnlineUnplacedGuard` line per round, no `exit walk from (0, 0, 0)`, no `did not reach`.

## T3 online vs Arcade: table tool, stack give-up reasons, fixes, ARC2 kit (11-01 night, wk-botscore-1101)

### Table tool
`python tools/kl_online_vs_arcade.py --prefix Q31 --maps <list>` prints one table per map: Arcade (ARC1 note) | online host hook tally (round 1 summary, GRABBED
lines as fallback), loot ratio and PASS / BELOW / NO-BASELINE / NO-LOG / NO-ROUND. `--arcade` repeats (ARC1 + ARC2 notes merge). PASS = online loot >= 60 pct of Arcade
loot. The 60 pct is a JUDGEMENT CALL, not measured (Arcade itself swings a lot between rounds). Test: `tools/kl_online_vs_arcade_test.py` (25 checks).

### Why stacks were given up (Q31 host logs, read only)
- DD05 (Arcade 6 stacks, online 0 to few): `guardmode: round scan: 3 cop(s) read live, 6 money stack(s), 6 free stack(s) of which 3 guarded` (11:06:33), then
  `stack ... is gone before it got there (taken by someone else?)` x2 (11:06:42/44), then `no stack to take (0 guarded, 24 s idle, clock left 214 s) ... OnlineIdleVan` (11:07:08).
  Two causes: the guard test, and stacks that vanish (see DD09).
- DD07: `5 cop(s) read live, 5 money stack(s), 5 free stack(s) of which 5 guarded` (11:23:04); 57 s later `no stack to take (0 guarded, 57 s idle, clock left 192 s)` for
  bots 0..3 (11:24:02). All five stacks were "guarded", so the bots held, then went idle to the van. ARC1 DD07 shows the cops standing at the stacks are CARRIERS
  (the stock drop rule), and Arcade bots simply shoot them (6 dead in ARC1).
- DM06: `14 cop(s) read live, 4 money stack(s), 4 free stack(s) of which 4 guarded` (12:13:05), `no stack to take (0 guarded, 110 s idle, clock left 139 s)` (12:14:56). Same pattern.
- DD09: `17 cop(s) read live, 6 money stack(s), 6 free stack(s) of which 0 guarded` (11:39:51), so NOT the guard test; then four `stack ... is gone before it got there`
  within 1 s of each other at 11:40:04-05 (about +13 s). Stacks drained by the stock script (0x6d2500 chain, see "Gap 4 RE"): cause unproven, SP2 (OnlineStackProbe=3 + OnlineDropFollow=1) is
  the bench that decides it. No new probe key was added (the existing OnlineStackProbe covers it).
- DD06 (behind, not zero): `lootparts: bot 1 left stack 1f6ce8f0 after 25 of 34 parts (partial tally 500000; bot moved away: 8.3 m from the stack ... limit 2.5 m)` (11:15:23),
  the same for bots 4, 5, 6 within 1 s. Bots drift off the stack (crowding) mid-loot and the partial stop then blacklists the stack; with the exit commit that follows, the
  rest of the stack is never finished. Arcade (5.55M) finishes the stacks.

### Fixes in code (both default 0, SHIP-safe: tick/data only, no .text patch, no debug register)
- `[BotFill] OnlineGuardCarrierCm` (recommended off until benched; try 150; needs OnlineGuardMode=1): a live cop within that many cm of the stack is its CARRIER
  (it is the money's owner, not a guard), so it does not count as a guard. Pure rule `kgg_carrier` in klguard_logic.h (klguard_test.c). Risk: the bots walk into a
  cop and may die, as in Arcade (ARC1 DD07: 6 dead). GUESS: 150 cm is the carry offset; unmeasured.
- `[BotFill] OnlinePartialRetry` + `OnlinePartialRetryS` (60) (recommended off until benched): after a partial stop with a tally > 0 the bot does not commit to the exit
  for up to S seconds while a free stack remains and enough clock is left (`kgg_partial_hold`); the blacklist retry then picks the stack again. GUESS: 60 s.
- Rows in tools/kl_mod_options.py, commented doc lines in klhook/KLHook.ini. Not fixed: DD09 vanishing stacks (needs SP2), DD05 second half (same).

### ARC2 kit (staged, NOT run)
`python tools/kl_arc2_kit.py` writes `C:\kl_build_1024\week_1028\arc2`: KLHook_ARC2.ini, ARC2_<MAP>.ini x10, maps_ARC2.txt, run_arc2.sh, loadcheck.py, README.txt. Maps: DM01B DM02 DM03
DM03A DM05A DM06B DM07 DM09 DM11B DD10 (slot/page/entry from the live_1026 smoke inis; page 2 = 6 DOWN, page 3 = 7 DOWN). DM09 has a 1000 s cap. Needs the expansion maps installed,
the TEST dll week_1028 arcbase (ArcadeProbe), the game closed, the owner away. Test: tools/kl_arc2_kit_test.py (58 checks).

### Bench / ship proposal (nothing goes into NEXT_SHIP.txt)
- Bench: OnlineGuardCarrierCm=150 on DD05 DD07 DM06 DM01 (PASS: stacks taken > 0, ratio column >= 60 pct, deaths not worse than ARC1); OnlinePartialRetry=1 on DD06 DD08 (PASS: no
  `left stack` followed by an exit commit with a free stack left). Then ARC2, then re-run the table with both ARC notes.
- Ship only after a bench passes; keys stay at 0 until then.
