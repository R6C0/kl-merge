# DM09 van timing (wk-vantime-1101)

Task: why the RT2L bots (DM09, 7 bots, 8 legs, 0 boarded) were not at the box when the van came, and the smallest fix.
Source: RT2L log (`week_1028\rt2`, `KLHook_RT2L.ini`: OnlineLegsWithVan=1, OnlineLegHopDy=1500, `[BotFillWay_DM09]` P1..P8; `OnlineVanPosSane` absent) and `klhook/klbotfill.c`.
NOT run live. Marks: GUESS = not proven by code or log.

## 1. Life cycle of the DM09 van

Fields (klbotfill.c, klescort.c): `[rules+0x1dc]` van state, `+0x1d8` state timer, `+0x1e0` boarding object (node at `[obj+4]`), `+0x4c` round clock.

| step | what happens | evidence |
|---|---|---|
| called / arrives | The game's `LastVehicle` trigger (round clock about 1.2 s) calls the van. Nothing the hook does calls it: `klbf_ot_call_van` (0x71e180) needs `klbf_ot_vh`, the exit-trigger vehicle handle, and that was never looked up (cause 2 below). | RT2L: state 0 -> 2 at clock 1.2 s |
| state 0 | no escape vehicle active; boarding object not set | log |
| state 2 | van drives in, about 7 s; boarding object reads (-1852, 121, 8675) | log; DD maps use 1 for "coming" (kvt_bo_ok accepts 1..4; GUESS that 2 on DM09 is the same phase) |
| state 4 | van waits, about 8 s; boarding object (-1851, 113, 10462) | log; DD maps use 3 for "waiting" (GUESS: 4 is DM09's flavour of the same wait) |
| state 6 | leaving (DD: 5), then gone (7) | log |

Wait time: about 7 s in + 8 s waiting. The bots were 64-76 m short of leg 8 when the boarding object showed (RT2 note, flat 15 s leg timeouts), the round ended 19 s after.

Why `OnlineVanHold` never held (`klbf_vh_pass`): it ran only for state 3 (DM09 showed 0/2/4/6), needed the clock at 20 s or more, and needed a walking bot with a goal (`klbf_ot_goal`: box or exit trigger, both unknown on DM09) to measure `dmin` against HoldM. Three independent reasons; any one is enough.

Where the "exit trigger" target pointed vs the boarding object:
- The scan accepted the vehicle object's STALE node (24235, -59842, 13883) as the van (`OnlineVanPosSane` was 0 in the kit). With `van != 0` the exit-trigger lookup (`!van && klbf_ot_van ...`) was skipped, so `klbf_ot_vh` stayed 0.
- After leg 8 the order target was `vpos` = that stale place (60 km away), not the trigger (-3000, 500, 10550).
- The boarding object is where the van actually stood: (-1852, 121, 8675) -> (-1851, 113, 10462), 18 m from the trigger at state 2.
- Arcade DM09 comparison: no Arcade DM09 round log exists in `re/arcade_baseline_1101.md` (ARC1 is the DD maps); not compared.

Also: bot arrival at the box is staggered by about 55 s while `OnlineGatherMaxS` caps the gather at 25 s.

## 2. The fix (four keys, default 0 = today, DD maps unchanged)

Pure decisions in `klhook/klvantime_logic.h` (31 checks in `klvantime_test.c`), wired in `klbotfill.c`:

- `[BotFill] OnlineVanAfterLegs=1`: the trigger lookup also runs with a van object known; once the trigger is known the phase-2 loop treats `van` as 0 (`kvt_van_for_walk`), so the legs, `klbf_ot_arrive`, `klbf_ot_call_van` and the stall test run as on a stock map.
- `[BotFill] OnlineVanBoPos=1` (review fix 11-02): `klbf_vbo_tick` takes the BOARDING PLACE from `kle_boarding` (klescort.c, shared, 0x8faf72..0x8fafe6): `[rules+0x1e0]` is the VEHICLE ITSELF, the place is its node + 500 along the node's x axis. Only while PARKED (state 3 or 4; `kvt_bo_ok`), never in state 1/2 where the vehicle moves along its road (klescort.c FollowOutStopPlace, Vault N1018_L22: 25-47 m). Not the origin, within 400 m, within 500 m of a trigger / box. A bot past its legs or after the call, with no escape box, walks to it (`kvt_use_bo`). `klbf_ot_goal()` (so dmin of OnlineVanHold / OnlineVanGather) therefore only ever sees a parked, fixed place. FollowOutStopPlace is the follow-out crew's own latch of the parked place for later drive-ins; independent, not reused (no second visit on DM09).
- `[BotFill] OnlineVanFarHold=1` (+ `OnlineVanFarHoldS`, default 40, GUESS): `OnlineVanHold` also runs in state 4; a walker with loot beyond HoldM counts as in range and lifts the visit's cap from `OnlineHoldMaxS` to FarHoldS. Needs `OnlineVanHold=1`. Review fix: in state 4 only the Invulnerable byte and VanBlow's paused clock are used; the state timer `[rules+0x1d8]` is written in state 3 only (its meaning in DM09's state 4 is unverified), so no timer GUESS is left.

Recommended together; independent otherwise. SHIP-safe: data, tick and order target only, no new patch.
- `[BotFill] OnlineLegWaitVan=1` (+ `OnlineLegWaitIdx`, default 1; `OnlineLegWaitMaxS`, default 0 = no cap), needs the legs (`OnlineWayPerMap`). Added after RT3 (below). Pure decision `klhook/klwaitvan_logic.h`, 24 checks in `klwaitvan_test.c`.

## 2b. RT3 result and OnlineLegWaitVan

RT3L (DM09, `KLHook_RT3L.ini`: OnlineLegScale=1 Speed=150 MaxS=60 OnlineLegStallS=20, log `...\solo\RT3L_DM09\inst1\KLHook.log`): the legs complete (12 reached), but all 7 bots die on street legs 2..6 between 23:42:31 and 23:43:16. The van probe first leaves state 0 at 23:43:06.270 (clock left 1.1 s, about 249 s into the round, "state 0 -> 2", boarding object (-1852, 121, 8742)), goes 2 -> 6 at 23:43:13, the round is over at 23:43:23. The bots walked into the street minutes before the van existed.

Rule: a bot in phase 2 (heading for the escape, it has the legs) that is at leg `OnlineLegWaitIdx` (0-based; default 1 = P2 = (2600, 114, -5920) of `[BotFillWay_DM09]`; GUESS: P1 is the tower floor y 19601, P2 the first street-height point still on the lobby side, P3..P8 the street where the bots died) and would advance (reached, timed out or stalled) STOPS there instead when the van is not there: probe state < 2 or unreadable, and the hook has not called it. While it waits the leg timeout, the stall clock and the re-path do not run (the order to the point is still repeated by the normal timer). Released when state >= 2 (or called), or when `OnlineLegWaitMaxS` > 0 seconds passed; then the leg gets a fresh timer and the rest run with the OnlineLegScale timeouts and no stall cut (`kwv_nostall`: once the van is there the stall cut is off for all legs). A bot that never reaches the hold leg is not held earlier. Where the bots call the van themselves (DD maps) the wait would last to the cap: use it on DM09 only.
Log lines (one per bot each): `waiting for the van at leg N of M ... van state S, clock left T s, tally X (OnlineLegWaitVan)` and `released from the van wait at leg N of M after K s: the van is there | cap OnlineLegWaitMaxS ran out, no van, van state S, clock left T s`.
GUESS left: the default hold leg; that the lobby side of P2 is safe enough (the bots may still be shot there); that state >= 2 leaves enough time for the street run (RT3: state 2 for 7 s and the van gone 17 s later: bots must be near P2 = about 110 m of road from the exit trigger).

### OnlineLegWaitCall (added 11-02)

Problem: the hook calls the van (`klbf_ot_call_van`, 0x71e180) only when a bot ARRIVES at the exit trigger, which is past the hold, so with OnlineLegWaitVan nobody calls it and the bots wait for the game's own LastVehicle van (249 s in; it leaves 2 -> 6 in about 15 s; the street run took about 45 s in RT3).
Call-site check (klbotfill.c `klbf_ot_call_van`, comment above `KLBF_SV_VT`): 0x71e180(rules, 0, vehicleHandle, 0) needs NO caller position. Preconditions: Sv rules vtable (or the private copy), the 16 head bytes of 0x71e180, the trigger still valid with its vehicle handle `klbf_ot_vh`, `[rules+0x1dc]` 0, `[rules+0x372]` 0, `[rules+0x1ee]` 0, `[rules+0x2c]` non-zero, and the clock `[rules+0x4c]` >= 20 s (below that it is marked called and refused, so the round end stays the humans'). A refusal is retried every 5 s. So calling from the hold is the same call, only earlier; nothing safer is needed. Not done: the player-only side effects of 0x4d85e0.
`[BotFill] OnlineLegWaitCall=1` (+ `OnlineLegWaitCallN`, default 1): needs OnlineLegWaitVan and OnlineVanAfterLegs (the trigger lookup/handle). When N carriers (phase 2, tally > 0) wait at the hold, the handle is known, nothing is called and the state is 0 (`kwv_call_ok`), the hook calls the van through `klbf_ot_call_van` (one `wait call` log line per round, then its own `CALLED ... clock` line). `called` counts as van ready, so the waiting bots are released in the same tick and run the street legs while the van drives in.
Timeline after the call (GUESS from RT2/RT3: about 7 s drive-in, then parked 3/4, 8 s unheld): t = 0 release at P2; t about 7 s parked; the street run takes about 45 s; carriers are staggered (RT2: about 55 s between first and last). OnlineVanHold/FarHold only start when the state is 3 (4 with FarHold), the clock left is >= 20 s and a walker is in range, and its cap runs from the first held tick: FarHoldS=40 ends at about t = 47 s, which is about the same as the first carrier's arrival and BEFORE the staggered ones. For RT4 use `OnlineVanFarHoldS=70` (7 s drive-in not counted + 45 s run + about 18 s stagger/margin; the cap is a ceiling, the hold ends earlier when the walkers are in range of HoldM and boarded). The hold also needs the round clock >= 20 s throughout: a call after about 249 s of a 300 s round (as the game's) cannot work; the hook's call at the first carrier's wait should come far earlier. GUESS: all of it, no live run.

## 3. Bench RT4 (not run)

DM09 live (kit as RT3: `week_1028t3`, ini `KLHook_RT3L.ini`): RT3L ini deltas
- `OnlineVanPosSane=1`, `OnlineLegsWithVan=1`, `OnlineVanHold=1`, `OnlineGatherMaxS=60` (as in the RT2/RT3 plan)
- Base (all variants): `OnlineVanAfterLegs=1`, `OnlineVanBoPos=1`, `OnlineLegWaitVan=1`, `OnlineLegWaitIdx=1`, `OnlineLegWaitMaxS=0`, `OnlineLegWaitCall=1`, `OnlineLegWaitCallN=1` (try 3 if a lone early carrier should not bring the van)
- RT4a: base plus `OnlineVanFarHold=1`, `OnlineVanFarHoldS=70`.
- RT4b: base without FarHold (shows whether the stock 15 s hold is enough).
- keep OnlineLegScale=1 OnlineLegSpeed=150 OnlineLegMaxS=60 OnlineLegStallS=20 OnlineWayPerMap OnlineLegHopDy=1500 and the `[BotFillWay_DM09]` P1..P8.
DD06 regression: same hook and ini (the DD06 RT2D ini), the new keys 0, then OnlineVanAfterLegs=1 OnlineVanBoPos=1 OnlineLegWaitVan=1 (and FarHold) on; expect the same BOARDED count (7 boarded in RT2D/RT2R/RT3) and no wait lines unless DD06 has legs (it has none: `OnlineLegWaitVan` is then inert).

Grep lines (KLHook.log):
- `wk-vantime` (ini state: AfterLegs/BoPos/FarHold and OnlineLegWaitVan), `exit trigger` (lookup now runs with a van known), `CALLED` (van call), `van state` / `van probe` (state 0 -> 2 clock), `waiting for the van`, `released from the van wait` (OnlineLegWaitVan), `wait call` (OnlineLegWaitCall), `parked in state` (BoPos goal), `far hold` (FarHold), `hold: cap of`, `BOARDED`, `waypoint leg`, `is dead or gone`.
- Pass: every bot prints `waiting for the van` at leg 2 of 8 before 23:4x of the van, none dies there; at the `van state 0 -> 2` line all waiting bots print `released ... the van is there` within one tick; `parked in state 4 (or 3)` appears; a `CALLED` line from the hook; at least one `BOARDED`; DD06 unchanged.
- Fail modes: bots still `is dead or gone` before `van state 0 -> 2` (the hold leg is not safe: try OnlineLegWaitIdx=0); `released` but legs end short (state 2 too late: lower to idx 0 or raise OnlineLegSpeed); no `parked in state` (the vehicle never parks in 3/4: DM09 went 2 -> 6 in RT3, so BoPos may stay silent there and the trigger remains the goal); `waiting` lines without a `released` (the van never came in the round).
