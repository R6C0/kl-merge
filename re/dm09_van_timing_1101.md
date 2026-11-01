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

## 2. The fix (three keys, default 0 = today, DD maps unchanged)

Pure decisions in `klhook/klvantime_logic.h` (31 checks in `klvantime_test.c`), wired in `klbotfill.c`:

- `[BotFill] OnlineVanAfterLegs=1`: the trigger lookup also runs with a van object known; once the trigger is known the phase-2 loop treats `van` as 0 (`kvt_van_for_walk`), so the legs, `klbf_ot_arrive`, `klbf_ot_call_van` and the stall test run as on a stock map.
- `[BotFill] OnlineVanBoPos=1`: `klbf_vbo_tick` reads the boarding object once per tick (state 1..4, not the origin, within 400 m, within 500 m of a trigger / box); a bot past its legs or after the call, with no escape box, walks to it (`kvt_use_bo`); it is also the goal for the hold's distance.
- `[BotFill] OnlineVanFarHold=1` (+ `OnlineVanFarHoldS`, default 40, GUESS): `OnlineVanHold` also runs in state 4; a walker with loot beyond HoldM counts as in range and lifts the visit's cap from `OnlineHoldMaxS` to FarHoldS. Needs `OnlineVanHold=1`.

Recommended together; independent otherwise. SHIP-safe: data, tick and order target only, no new patch.

## 3. Bench RT4 (not run)

DM09 live: RT2L ini plus `OnlineVanPosSane=1 OnlineLegsWithVan=1 OnlineVanAfterLegs=1 OnlineVanBoPos=1 OnlineVanFarHold=1 OnlineVanHold=1`, with the RT3 leg keys (`OnlineLegScale=1`, Speed=150, MaxS=60, `OnlineLegStallS=20`) and `OnlineGatherMaxS=60`.
DD06 regression: same hook, the three new keys 0, then 1; expect the same BOARDED count (7 boarded $4.8M in RT2D/RT2R) and no `wk-vantime` line besides the ini log.

Grep lines:
- `wk-vantime` (ini state), `exit trigger` (lookup now runs with a van known), `CALLED` (van call), `boarding object` (BoPos goal), `far hold` (FarHold), `van state`, `BOARDED`, `hold: cap of`.
- Pass: DM09 shows `exit trigger` found, a `CALLED` line from the hook, `boarding object ... is the walk goal`, at least one `BOARDED`; DD06 unchanged with the keys 0.
- Fail modes to read: no `exit trigger` line (lookup still blocked), `far hold` without `BOARDED` (cap too short), boarding object refused (nothing logged; the plausibility test rejected it: check the box/trigger refs).
