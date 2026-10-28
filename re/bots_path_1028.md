# AI heister paths and van boarding online (wk-botpath, 2026-10-28)

Static + log analysis only; the game was not run. CERTAIN = read in a log or the code. GUESS = inferred.
Logs: `<DM>\KL_PortTools\build\klhook\solo\<TAG>\inst1\KLHook.log` for Q27_DD04, Q27_DD04R, Q27_DD05, Q27_DD08, BOS_DD08r (+ Q27_DD06/DD02 legs).
No Arcade bot-walk log with leg/box probe lines exists (Arcade bots use the game's own ZBoardEscapeVehicleTactic and write no such lines), so the Arcade
comparison is by design only: Arcade bots board by walking into the escape box and standing there, without a hook clock, a 15 s hold cap or a crowd on one point.

## Findings per map

| Map | Bot / leg | Failure | Cause | Certainty |
|---|---|---|---|---|
| DD08 (Q27_DD08, 4/7) | all, legs 2-5 | legs time out at the flat 15 s with 28-79 m left (46 m leg 1-2 = ~3 m/s) | the 15 s limit is shorter than the walk; the skipped leg's order moves on, so bots still arrive (BOS_DD08r 7/7) | CERTAIN timeouts, GUESS harmless |
| DD08 | bots 1,2,4,5 | stood inside the box at +2 s and +7 s of the van call, then 12-18 m out and back; never inside on a 1 s tick during the 15 s state-3 hold; bots 3,6,0,5 boarded | 7 bots ordered to ONE point (box centre), every re-order (6 s, BoxForce 4 s) to the same point; the oscillation 0 m -> 12 m -> 0 m looks like crowd push (not seen in Arcade) | CERTAIN pattern, GUESS crowd push |
| DD08 | bots 4,5 | `did not reach the exit trigger after 90 s (0 m / 17 m)` printed while the bots were AT the box | the 90 s cap counts from phase 2 and keeps running during the gather wait | CERTAIN |
| DD08 | all | state 3 lasts ~15 s because OnlineVanHold HoldMaxS = 15, then the van goes (state 5) | the hold cap, with walkers 4 m away | CERTAIN |
| DD04 (Q27_DD04R, 6/7; Q27_DD04 3/7 older build) | bot 4 | arrived 4 m from the trigger at +61 s, after the van had gone (state 5 at 20:05:33); then idle, back to loot | far start (124 m from the exit, left phase 0 late at 20:04:39), gather waited the full 25 s with the farthest bot 35 m out; no [BotFillWay_F04] section; no escape box found, so only the exit trigger / crowd rule counts | CERTAIN timeline, cause of the slow walk unknown (door / nav stall) |
| DD04 | bots 1,3,4,5 | 5 "did not reach stack" give-ups at 2-9 m, 12 s no progress | stack walk stall near cops (loot side, not the van) | CERTAIN |
| DD05 (Q27_DD05) | all 7 | 7/7 counted aboard (3 by state, 4 by OnlineExitCrowd); the old 6/7 is not reproduced in this log | no waypoint section F05, short walk (farthest 8 m at the call); counted by the hook tally (OnlineBoard off) | CERTAIN |
| DD06 / DD02 | legs | 8 timeouts of 35 (DD06 leg 2: 20-36 m left), DD02 legs 2-4 at 5-54 m | same flat 15 s | CERTAIN |

Route data: DD08 P1..P7 and DD06/DD02 points checked against the logs: bots reach P4-P7 within 1-3 m (y matches the bot's y, e.g. P7 y 2145). No wrong waypoint found; no data
change made. F04 and F05 have no section; the logs show no stall long enough to place points from (no position trace), so none were invented.

## What changed (klhook/klbotfill.c, all default 0 = as before; ini lines are commented in klhook/KLHook.ini)
- `OnlineLegScale` (0/1), `OnlineLegSpeed` (cm/s, 300 GUESS), `OnlineLegMaxS` (60): leg timeout = clamp(5 s + horizontal distance / speed, 15 s, MaxS). Site: `klbf_leg_begin`, the OnlineWaypoints leg block in the phase-2 tick.
- `OnlineLegStallS`: no 3 m progress for N s: the order is repeated at N/2 (re-path), skip to the next leg at N ("stalled (skipped)"); a live cop within OnlineTacticsGuard pauses the clock.
- `OnlineLegNear` (cm, 0 = 300), `OnlineLegDy` (cm, 0 = height ignored): arrival radius and height window of a leg point.
- `OnlineBoxSpread`: `klbf_ot_slot_target`, per-bot place inside the box frame (8-slot pattern, 1.5 m), used by the box order and by OnlineBoxForce.
- `OnlineBoxLatch` + `OnlineBoxLatchM` (1500): in the OnlineBoxWalk block: once inside since the call, within M while state 3/4 counts as inside (hook tally, then OnlineBoard if on). Needs OnlineBoxProbe=1 (default) so `in` is evaluated before state 3.
- `OnlineBoardTeleport` (0 off, 1 on, 2 dry) + `OnlineBoardTeleportS` (10), `OnlineBoardTeleportM` (4000): NOT ARCADE. State 3, still outside after S s, within M: the game's actor teleport 0x62a900 (klcrew_rt.c klt_refuse / klt_tele_known / klt_teleport), once per bot per round, to its slot place at the bot's own height. Refusals are logged.
- Existing keys worth raising in the same bench (no code): `OnlineHoldMaxS` 15 -> 30 (DD08 cap hit with walkers 4 m away), `OnlineGatherMaxS` 25 -> 40 (DD04 bot 4).
- Leg log line now also prints `dy` and the leg's limit in s; the verdict word is `reached`, `timed out` or `stalled (skipped)`.

## GUESS list
1. 3 m/s walking speed for the leg limit (DD08 leg 1-2 average).  2. The 1.5 m ring pattern and that world x/z offsets stay inside the box (checked with the frame, centre fallback).
3. Crowd push as the reason bots leave the box (alternative: another module's order; RestlessHop is Arcade-only).  4. 15 m latch radius.  5. Repeating the order re-plans the route (re-path).
6. Teleport keeps the bot's own y (the box centre is 3 m above a bot's feet on DD08); 10 s / 40 m limits.  7. Different points per bot are no worse for nav than one point (the snap of the centre may be what held bots out).

## Bench recipe (2 seats; run only when the game is free)
Base: `C:\kl_build_1024\week_1028\WK2_host.ini` / `WK2_join.ini` (the [Script] picks the map: change its map step to DD04, DD05, DD08; one tag per map). Add under `[BotFill]` of BOTH inis:
```
OnlineLegScale=1
OnlineLegStallS=10
OnlineLegDy=300
OnlineBoxSpread=1
OnlineBoxLatch=1
OnlineHoldMaxS=30
OnlineGatherMaxS=40
OnlineBoardTeleport=2      ; dry first; set 1 only for the last run (NOT Arcade)
```
```
python C:/kl-merge/wt/wk-merge/tools/kl_solo_test.py --hook C:/kl-merge/wt/wk-botpath/klhook/out_botpath_1028_test --n 2 --secs 700 --gap 45 --relaunch 2 --tag BP_DD08 --owner-away --ini1 <host ini> --ini2 <join ini>
```
(ship dll for the final run: out_botpath_1028). Proving lines in solo/BP_*/inst1/KLHook.log: `botfill: wk-botpath: OnlineLegScale=1 ...` at init;
`waypoint leg N of M reached|timed out|stalled (skipped) (... limit S s)` with limits above 15 s and fewer `timed out` than the Q27_DD08 baseline (18 of 33 leg lines); `OnlineLegStallS re-path` lines;
`was inside the escape box since the call ... counts as inside (OnlineBoxLatch`; `BOARDED in the escape box` count 7 of 7 (baseline DD08 4, DD04 6, DD05 7 by tally); `round summary: 7 bot(s) ..., 7 boarded`;
dry run: `OnlineBoardTeleport DRY would move` only for bots still outside. FAIL: any fault / dump, `OnlineBoardTeleport ... moved` followed by a bot standing outside or falling, a skipped leg that sends a bot back,
a round that does not reach the end normally. Compare against the same map with the keys off (baseline tags Q27_DD08 / Q27_DD04R / Q27_DD05).
