# BoardReach order-to-the-doors census (2026-10-18, offline, read-only)

Question: how often does the BoardReach order (klmove.c ~962) aim at a point on the BOT'S OWN floor
when the bot is on another floor than the boarding object, per map, and would
`[Bots] BoardReachAimHeight=3` (commit 7ebc5c79) change anything?

## Method
- Source: `<DD>\KLHook.log` (1,260,890 lines, 205 sessions, Oct 14 17:00 .. Oct 18 23:35 when drafted; the log is LIVE: at 23:42 it had 1,274,490 lines and a 206th session, started 23:41:42 by 3f's run, with no new order line), streamed with
  Python, read-only. Scratch scripts: the session scratchpad (`census.py`, `census2.py`), not in the repo.
- Orders: 324 lines (the first draft said 323; its own table sums to 324) `reach: visit N: record R (stage S) stood D m from the boarding box at (..): sent to the doors (aim), the game set (got)`.
  Units are cm, D is the 3-D distance. 50 rounds, 9 maps, 0 on a stock Dog Days map (the feature runs only on a
  level that is not the stock one of its slot).
- Map per order (checked by an independent recount, see Review): the last `steam: level archive fNN\fNN_main.zip opened from ...\KLExpansion\Maps\<DMxx>\...` line
  (that line is once per level load and names the map folder; the `LOAD end scene` line only gives the slot).
- Session class: the `build:` line. SHIP = the owner's build, TEST (klauto) = autotests. Of 324 orders only 13 are SHIP
  (DM03 2, DM03A 5, DM05A 2, DM09 4), all on the boarding floor. Everything off-floor below is from TEST runs.
- Boarding y: (1) the `visit N: the vehicle's boarding box ... round (x, y, z)` line when logged (41 orders);
  (2) else the aim point of an order in the same visit whose aim y differs from the bot's y (= the object's place, 89);
  (3) else the map's most common such y (194, GUESS; DM03A 822 and DM02 122 are the same doors as in every other round
  of that map, and 822 matches "doors y 822" in the L85/L86 notes).
- Off-floor = |bot y - boarding y| > 300 cm (3 m, the BoardReachAimHeight value). The boarding y is the box CENTRE, the
  floor is about 1.2-1.3 m below it (game set y = box y - 120..130 on the same floor), so a bot standing on the doors'
  floor shows dy of about 1.2 m.
- "Aimed on the bot's floor" = the aim point differs from the map's doors point T (BoardReachAim fired: aim y = bot y).
  The log never prints BoardReachAim, so this is inferred per order.
- Boarded = a `bots: record R (bot): aboard` line for that record after the order and before that visit's
  `reach: visit N is over` (+5 s; 120 s if no such line).

## Table (all sessions; "floor-aim" = off-floor and sent to the bot's own floor, "object-aim" = off-floor and sent to the doors themselves)

| map (slot) | orders | rounds | max dy (m) | off-floor orders | floor-aim | boarded, same-floor | boarded, off-floor | median s to board, same / off | game set landed |
|---|---|---|---|---|---|---|---|---|---|
| DM03A Vault (F07) | 198 | 15 | 17.8 | 25 (12.6 %), in 3 rounds, 8 bot-visits | 25 | 148/173 orders (37/53 bot-visits) | 22/25 orders (7/8 bot-visits) | 7.8 / 33.8 | bot's floor 25/25 (game set = aim point exactly) |
| DM05A (F01) | 19 | 7 | 9.7 | 7 (37 %), in 4 rounds, 7 bot-visits | 0 (the logs predate / lack BoardReachAim: aim = the doors in 19/19) | 12/12 | 3/7 (corrected from 4/7; the van left 1 s after one order, and the visit ended 43-52 s after four others) | 1.7 / 42.4 (corrected from 32.9) | doors' floor 7/7 (game set y = box y - 132) |
| DM02 (F02) | 65 | 6 | 1.2 | 0 | 0 | 34/65 | - | 6.3 / - | same floor |
| DM06B (F02) | 10 | 6 | 1.4 | 0 | 0 | 9/10 | - | 1.3 / - | same floor |
| DM11B (F04) | 13 | 6 | 1.3 | 0 | 0 | 13/13 | - | 2.0 / - | same floor |
| DM09 Retomoto (F06) | 6 | 3 | 1.2 | 0 | 0 | 6/6 | - | 4.0 / - | same floor |
| DM01B (F03) | 7 | 3 | 1.2 | 0 | 0 | 3/7 | - | 11.6 / - | same floor |
| DM03 (F03) | 3 | 2 | 0.5 | 0 | 0 | 3/3 | - | 6.5 / - | same floor |
| DM01 (F01) | 3 | 2 | 1.2 | 0 | 0 | 3/3 | - | 1.9 / - | same floor |
| stock Dog Days maps | 0 | 0 | | | | | | | feature not active there |

Off-floor distances (dy): DM03A 4.0, 4.0, 4.8, 5.8 x 9 ... up to 17.8 m (L86: bot floors -960, -560, -160, 191, 240, 344, 420
against doors 822); DM05A 5.3 x 4, 9.5 x 2, 9.7 m. Smallest off-floor dy anywhere is 4.0 m, largest same-floor dy is 1.44 m,
so a 3 m threshold separates the two cleanly in everything logged.

## Findings
1. Off-floor orders exist on only two maps: DM03A (Vault) and DM05A. On the other seven the bots were always on the doors'
   floor (dy <= 1.44 m).
2. DM03A: all 25 off-floor orders were sent to the bot's own floor (aim y = bot y) and the game set landed exactly on that
   point, so none was sent to the doors' floor. 20 of them are one round (L86, rnd 836: 20 of 62 orders), 4 in round
   806, 1 in round 739. Rounds are named here by the build-line session index and wall clock, because the first draft's "rnd 836 / 806 / 739" cannot be reproduced from the log: L86 = session 204 (23:30:51 .. 23:31:22), L85 = session 196 (18:11:05 .. 18:11:31), the single order = session 180 (09:41:34) (GUESS that 204 / 196 are the L86 / L85 of the notes; the times fit). Real cost seen: the off-floor bots still boarded (7/8 bot-visits) but took a median 33.8 s from the
   order (per bot-visit, from its FIRST order: 34.1 s, range 26.8 .. 46.5, 7 bots; the order-weighted 33.8 repeats rec 1, which got 11 of the 25 orders) against 12.4 s for same-floor orders from 15 m or more (66 boarded orders; per bot-visit 11.4 s, n=19) and 4.4 s for under 15 m (corrected from 3.0; per bot-visit 5.3 s, n=11). The off-floor bots stood 17-36 m away in 3-D, so the far same-floor group is the fair comparison. GUESS: the extra time is
   the stair route plus the order not helping; this is confounded with distance (34 m vs 28 m median) and the route, so
   it does not prove the aim point is the cause. The one bot-visit that never boarded (rec 1, session 196) was ordered 3 times
   to the same floor-aim point (-160). In session 204 rec 1 was ordered 11 times, each time to a point one floor higher as it climbed (-960, -560, -160, 240, 420), and boarded 0.2 s before the van left: the floor-aim point acts as a carrot up the stairs and worked, which is a point AGAINST calling it the wrong floor. There is no Aim-off DM03A baseline with an off-floor bot, so nothing in the log shows the doors form doing better.
3. DM05A: all 19 orders aimed at the doors themselves (aim = (-2839, 992, 3601)) and the game set landed on the doors' floor
   (y 860) every time, because those runs had no BoardReachAim (xz of the aim never shifted). So the 7 off-floor bots (5.3-9.7 m
   below) got the "object" form that BoardReachAimHeight would give. Boarded 3/7 (corrected from 4/7; median 42.4 s of the three) against 12/12 same-floor
   (1.7 s). The four that did not board are not clean failures: in one round the van left 1 s after the order (visit 1 lasted 8 s); in the others the visit ended 43-52 s after it. GUESS: with BoardReachAim=80 and no Height key the same 7 bots would be sent to their own floors, as in the Vault.
4. DM02: 22 of 65 orders were aimed on the bot's floor (BoardReachAim=80 worked there, see adopt_list); every one is on the
   doors' floor, so Height=3 changes nothing there.
5. Caveat on "owner's real play": the log holds 13 SHIP orders, none off-floor; the evidence is autotest rounds with the test
   inis (`PT_*.ini`, BoardReachAim=80). The live `KLHook.ini` had no `BoardReachAim` line at 23:33, as drafted. Re-read at 23:42 (mtime 23:41:35) it HAS `BoardReachAim=80` in `[Bots]` (file line 225, no `[Bots.<F>]` section), because 3f's next live run (kl2.exe started 23:41:42) installed its test ini over it; none of the `KLHook.ini.before-*` backups has the key. So the 80 is a test setting, not an adopted owner setting, and the live ini is rewritten per run: do not read it as the owner's config.

## Recommendation
- DM03A (Vault): YES, test it. This is where 25 of 25 off-floor orders went to the wrong floor (3 rounds, 8 bots, up to
  17.8 m). Use the staged `PT_DM03A_wrh.ini` (BoardReachAimHeight=3 + WalkAwayGoal=8) with hook 5c466e85 and compare per
  bot-visit the time from order to aboard for the off-floor bots (now 33.8 s median; success = clearly lower, still 7/8+ aboard; also log when the van leaves: in session 204 rec 1 boarded 0.2 s before it left, so the time to board is capped by the visit and more bots may simply miss the van).
  Put the cut of the change into the same round as L86 (stairs from the vault, floors -960..424).
- DM05A: YES as a guard, low test value. Its off-floor bots are 5-10 m below; with Height=3 they get exactly what the logs
  already show (object, game set on the doors' floor, boarded 3/7, median 42.4 s). This is the ONLY live sample of the doors form for an off-floor bot, and it is not better than the Vault's floor form (7/8, 34.1 s); both are confounded by distance and van timing. The claim that the floor form is 'wrong' is therefore a hypothesis; the test is a fair comparison, not a known fix. It needs to be set whenever
  BoardReachAim=80 is turned on for that map, otherwise GUESS: it repeats the Vault behaviour there. Test: one DM05A round
  with Aim=80 and Height=3, expect aim = (-2839, 992, 3601) for every off-floor order.
- DM02, DM06B, DM11B, DM09, DM01, DM01B, DM03: no test needed. Never off-floor (max 1.44 m), Height=3 is inert there.
- Global or PerMap: global `BoardReachAimHeight=3` is safe on every logged map (largest same-floor dy 1.44 m, smallest
  off-floor dy 4.0 m, so a 3 m threshold has a 1.5 m margin on the high side, 1.56 m on the low side). A PerMap section
  (`[Bots.DM03A]`, `[Bots.DM05A]`) is only needed if the owner wants the key limited to the two maps that have
  floors; no map logged needs it OFF. GUESS: maps not yet played with the van above/below the crew's start (e.g. DM06B at y 2626, only
  one floor seen so far) would also be covered by a global setting, which is a reason to prefer global.
- Threshold caveat: 3 m separates the logged bots (largest same-floor dy 1.44 m, smallest off-floor 3.98 m), but only 8 Vault bots and 7 DM05A bots are off-floor samples; a same-floor bot on a ramp or stair landing 1.5-3 m from the van is untested (GUESS). The code compares the bot's y with the boarding place's y (`fr.T[1]`, klmove.c:962), the same quantity used here.
- Not covered by this census: bots that never got an order (beyond the send limit (30 m default, KLMV_SENT)
  or not stage 3), BoardReachRepeat re-orders (counted as separate orders above; the per-bot-visit counts
  are in the table), and any round on a stock map.

## Review (independent recount, 2026-10-18 23:45, read-only)
Own script (scratchpad `recount2.py`) over the same `KLHook.log`; the code at klmove.c:962 was read, nothing run.
Confirmed: 324 order lines, 50 rounds (50 sessions), 9 maps; per-map order and round counts; DM03A 198 / 15 rounds / 25 off-floor
(sessions 204 x20, 196 x4, 180 x1), 8 bots, 25/25 aim y = bot y and game set = aim; DM05A 19 / 7 / 7 off-floor, aim = doors 19/19;
max dy 17.8 and 9.7 m; smallest off-floor 3.98 m, largest same-floor 1.44 m; DM02 22 of 65 aimed on the bot's floor; boarded
same-floor DM03A 148/173 and 7/8 off-floor bot-visits, median 33.8 s order-weighted.
Map attribution: for the 49 TEST sessions the last-opened-map rule equals the `LOAD end scene` slot map in every case. SHIP sessions
log no `LOAD end scene`, so only the last-opened rule applies there; it checks out because each SHIP order's doors point is the same
one the TEST orders of that map show (DM09 (-1852, 10459), DM03A (627, -11233), DM03 (2956, 44), DM05A (-2839, 3601), x/z).
Errors fixed above: (1) 323 -> 324 orders; (2) the live ini claim (now has BoardReachAim=80, test-installed); (3) DM05A boarded 4/7 and
32.9 s -> 3/7 and 42.4 s; (4) DM03A comparison medians 3.0 s -> 4.4 s for near, and n=81 -> 66 boarded orders (per bot-visit
numbers added); (5) round labels 836/806/739 replaced by session indexes and times; (6) the 'wrong floor' framing softened, since
rec 1 climbed to the van on floor-aim carrots and the doors form has no better sample.
Recommendation after the attempt to refute it: still worth the DM03A test, but as an A/B of two forms never compared in the log,
not a bug fix; call a global Height=3  'inert on every logged map', not proven safe.
