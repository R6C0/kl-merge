# DM09 online timing (RT4A), 2026-11-02, offline research (not committed)

Log: `KL_PortTools/build/klhook/solo/RT4A_DM09/inst1/KLHook.log`.

## 1. Lobby heist time
- The bench never sets it. `KLHook_RT4A.ini:834` only lifts the ceiling (`[Lobby] TimeMax=10`). The lobby default (`sm=4`, log line 1612, 17001) is what the round used: clock 250.0 s at round start (log 2421 = 240 + 10 s, see klroundkeep.c:27), over at played=273 s.
- Values: stock row 3..5 min; with TimeMax=10 / TimeMin=2 the row runs 2..10 (kllobbyopt.c:11-34). No script step in `RT4A_DM09_run.txt` presses the row. `RoundClockFix` only raises the clock to the lobby value, it cannot set one.
- Arcade DM09: van called at 300 s with 70 s left (arcade_baseline_1101_arc2.md:15) = about 370 s = 6 min (+10 s). Online got the van at 248 s only because the hook calls it earlier.
- Yes, a 6 min lobby is the fairer Arcade-parity test (RT4A ran 4 min = 114 s short of Arcade). Leg 1 was reached ~99 s in (01:55:42 vs round start 01:54:03), leaving 147 s for a 207 m walk.

## 2. Legs
- Route is sane. Leg lengths (m, cumulative from P2): P2-P3 67, P3-P4 90 (23), P4-P5 28 (118)... totals: P2 to boarding place (-1852,9959) = 274 m (incl. last 12 m from P8). The 190 m dy on leg 1 is the tower-to-street carry (OnlineLegHopDy hold, 36-37 s, "reached 70 m from" the tower point is expected).
- Bots really walk ~1.1-1.5 m/s under fire (leg 4: 47 s limit, 15 m left). OnlineLegSpeed=150 gives limit = 5 + d/1.5 s; actual pace is slower, hence timeouts 5-71 m short (log 15452-16567). A timeout just moves to the next leg, so the order is not lost, but time is. Clock, not leg count, is the limit: 274 m at ~1.2 m/s = ~230 s after leg 2.
- Van cycle: called at 135 s left, parked state 3 at 127 s left, left state 6 at 54.6 s left (log 16127) although FarHold allows 70 s (3 walkers still 30+ m away; the van's own state timer ran out). Then 5 bots counted aboard at state 4 by distance (28-60 m from the escape point), nobody actually boarded.
- Proposals (all default-off keys already exist):
  a. Longer clock: lobby 6 min (best: parity, no code).
  b. `OnlineLegSpeed=100` (floor) so limits are 5 + d/1.0 s, clamp `OnlineLegMaxS=60`.
  c. `OnlineLegNear=600` (arrival 6 m instead of 3 m): timeouts 5-20 m short become hits.
  d. `OnlineLegWaitIdx`/call: call the van at leg 1 arrival instead of leg 2 (OnlineLegWaitIdx=0); saves ~20 s. Risk: P1 is the tower floor, walkers are not yet down.
  e. Fewer legs: drop P3/P4 (P2 -> P5, 118 m gap with 3 m corners cut); NOT tried, needs a nav check. Per-map table `[BotFillWay_DM09]` only.
  f. `OnlineLateExit` (75 s) is already the global rule; for DM09 a per-map value (e.g. 120) would send carriers to the van earlier, but that needs code (the key is global). Not proposed for RT5.

## 3. RT5 rows (DM09 x2): 6 min lobby + slower leg speed + wider arrival
Base: copy `KLHook_RT4A.ini` to `KLHook_RT5A.ini`, change only:
```
[Lobby]
TimeMax=10
TimeMin=2
[BotFill]
-OnlineLegSpeed=150
+OnlineLegSpeed=100
+OnlineLegNear=600
```
(`OnlineLegSpeed` and `OnlineLegMaxS=60` lines already sit near ini:1108; add `OnlineLegNear=600   ; RT5`.) RT5B = same plus `OnlineLegWaitIdx=0` (lever d), to isolate it.
Host script (the `[Script]` block of the host ini; klauto reads keys 1.. in order and STOPS at the first missing number, so renumber
everything after the insert): after step 43 (the 4th RIGHT that picks F06) and before the old 44 (`log MAPS9 ...`), add
`tap DOWN`, `wait 900`, `tap DOWN`, `wait 900`, `tap RIGHT`, `wait 900`, `tap RIGHT`, `wait 900`. CERTAIN (2026-11-02, re/lobby_options.md
"Row order"): the FA lobby opens on the level row (-4), DOWN = row + 1, so two DOWNs land on Heist time (-2); LEFT / RIGHT never move the
row; Ready (RETURN) works from any row, so no UP is needed. The first RIGHT is stock (4 -> 5), the second goes through kllobbyopt
(TimeMax=10 is already in the ini): expect `lobbyopt: Heist time 5 -> 6 (the stock clamp would have kept 5)` and
`lobbyopt-test: session state 13 -> 18: time sm=6 min`. `[Lobby] TimeMin=6` does NOT work (the floor only limits LEFT; the default stays 4).
Pass check in the log: `lobbyopt: round clock at state 25 ... left[+4c]=370`, then `van ... parked` with >70 s left and `boardall` counts at state 3.
