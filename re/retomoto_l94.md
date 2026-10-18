# Retomoto L94 (leaderless KLJoin 0b557e40, hook zi, PT_DM09_die)

Offline reading of L94.log and klhook/*.c, checked a second time against the log (2026-10-19). Nothing was run or edited.
Tags: [log] log line, [code] file:line, [doc] re/ file, GUESS = unverified.
Clock: r = wall seconds after 'fed: round 2' (00:27:04.3). The otrace lines use another clock (r_otrace = r + 25.8 s); the first
version mixed the two (see "Corrections").

## 0. Timeline in one clock (r = wall)
- r23 human is a fed [log 00:27:27.8]; r83 the fed jumps to the street join, the crew is NOT moved (FedSkip) [log 00:28:27.3]; the fed then stands still at (6208, 570, -6221) for 160 s.
- r155..159 hop 6 carries all 7 bots (otrace prints r181..185) [log 00:29:39.7..43.0]. 0 'GIVE UP' lines in the whole log (grep: 0).
- r157..168 all 7 reach stage 2 (last: rec 6 at 00:29:52.2).
- r264 bot 4 reaches stage 3 [log 00:31:28.4], r268 BotVan calls the van (102 s on the HUD clock, END timer about 34 s: HUD minus offset 68.3) [log 00:31:32.5].
- Van waits 31:39.6..31:47.6 (8.0 s), leaves; round ends 32:06.0 [log].
- The 6 others stayed at stage 2 to the end: 96 s after the last promotion until bot 4's stage 3, 107 s until the van waited, and still g2 at 32:14.

## 1. Why 6 bots sat in stage 2
- FollowOut can never fire for a fed. Two gates: `h->stage < 3 || !kle_criminal()` [code klescort.c:1113]; the fed's own record stays at stage 0 [log 'g0' on record 0 all round], and kle_criminal is type==2 only [code klescort.c:852-856] while the fed is type 3 [log 'type 3, police byte 1'].
- Stage 3 for a fed's crew has exactly one stock source: standing in the exit box (otrExitLevel). Only bot 4 did, at r264, and then BotVan called the van with the other six far away. (Changed: the first version said "no mod key gives stage 3 without the human". That is wrong: BotVan, BoardAll, BoardNear and VanCallNear exist. What is true: none of them promoted the crew in time. BoardAll needs 15 s still, VanCallNear is 0 in PT_DM09_die, VanCallLast is off.)
- The crew was not parked in stage 2: its chain orders walk it to the van area. Rec 5 was 135 m from its place at 31:20 and 51 m from the boarding place at 31:47 [log 'move' and 'near' lines]: about 3.5 m/s, matching the 3.3-4.1 m/s of re/bots_follow_out.md.
- fedkit Hunted fought this walk, but not only "back toward the fed". Orders of the whole round: 158 [log]; 45 TOWARDS YOU, 55 step aside, 58 to a [Hops] cover place (the last one at 31:22.1). Cover places are mostly far from the fed and a few lie away from the van too. First version's "ordered back toward the fed for about 70 s" is too narrow: they were scattered for about 100 s (r155..r258). Hunted skips only `stage >= 3 && veh 1..5` [code klfedkit.c:834].

## 2. Why bot 4 did not board
- Last vehicle: `if (last) relax = 1;` leaves `have` at 0, so klmv_reach_pass skips its doors order [code klmove.c:893-898; log 00:31:39.6 'the round's last vehicle: every escape box works as in stock'].
- The doors order only goes to a called bot within 30 m of the doors (once a visit) [code klmove.c header]. Bot 4 was 8 m away [log 'near' line], so BoardReach would have ordered it. That part holds.
- CORRECTION: the first version said the stock board tactic "reaches only about 300 units and needs a path". The tactic (0x82f970) RUNS to the boarding object and boards within 300 units on arrival [doc bots_move.md:91]. So bot 4 should have been walking in. Bot 4's block target moved at 31:32.6 and 31:36.1 to (-1087, -40, 10511) and (-1335, -40, 10468) [log otrace BLOCK-CHANGED]: it was moving near the van, then stood 8 m from the 'boarding place' at departure. Why the tactic did not close the last 8 m is NOT explained by the log. GUESS: the boarding place rides the van (bots_move.md:372: 10 m from the place, 39 m from the doors), or the tactic's path end is not the doors. The log has no per-bot position for rec 4 after 31:36.
- There is no street escape box: the only ZAllyEscapeBox is in the tower at (2430, 19801, 510) [log 00:27:04.3]. So a stage-2 bot cannot be taken by a box in the street at all.
- CrewRouteHold is gated to a criminal human unless CrewRouteFed [code klmove.c:1141], so no hold ran. LastVehicleLead did not act because BotVan had called the van first (the lead is a no-vehicle fallback [code klmove.c:800-812]).

## 3. Does (l) fix it?
(l): CrewRouteFed=1, VanCallLast=1, CrewRouteRange=300 (and LastVehicleLead=600 in the staged ini).
- Distances, CORRECTED: at departure the crew stood 83, 53, 92, 8, 51, 53, 73 m from the boarding place [log 'near' line 31:47.6]. The first version quoted "146-230 m" and called the near-line numbers "to the fed". Both are wrong: the log line says metres from the boarding place, and 151-237 m is L83's figure [doc retomoto_fedvan.md], not L94's. Fed positions are 45-97 m from the crew in the Hunted lines, a different distance.
- VanCallLast [code klmove.c:1641-1667] promotes the stage-1/2 bots at wait+3 s (VanCallDelay default 3, [code klmove.c:1862]), no distance limit. It fits an 8 s wait, 5 s left. It also matters more than the first version said: with no street box, stage 3 is the only way a bot boards.
- Walking time: 51-92 m at 3.3-4.1 m/s is 12-28 s. The 5 s left after the call is not enough, so no bot but bot 4 boards without a hold. The first version's "about 25 s for 150 m" was wrong in the other direction (150 m is 37-45 s).
- CrewRouteFed hold [code klmove.c:1136-1200]: when the timer is under 2.0 s, +5 s steps, 45 s budget a visit, only while some loyal in-play bot (any stage; the code has no stage test, the comment says "called") moves 2 m in 2 s within CrewRouteRange of the boarding place. All 7 stood 8-92 m out, inside even the default 100 m, so Range 300 is a margin. Stage-2 chain walkers also stand 5-6 s at times [log 'stood 6.0 s' lines], but seven bots rarely all stand at once. So, from the code: the van is likely held long enough for the crew to arrive (92 m is 28 s, under the 45 s budget). GUESS: not tried live; END timer 'does not cut a held van' is code reading only [doc bots_follow_out.md:206, retomoto_fedvan.md].
- Risks that remain: the hold's guard (damaged vehicle, 'somebody paid', timer changed) can refuse it; and the unexplained 8 m stop of bot 4 may repeat for the other bots at the doors (then they would stand beside the van, held, but not aboard). If so, the next step is the BoardReachLast key below.
- LastVehicleLead=600: BotVan called at END about 34 s; 600 tenths moves the fallback call to 60 s left, about 26 s earlier (31:06, Hunted still active, crew 77-100+ m from the van). GUESS: not useful, because the hold already gives up to 45 s. Drop it from (l) so one thing changes at a time. It is not proven harmful.
- Verdict, changed: (l) has a real chance to get the crew aboard, not only "bots within about 100 m". Expect: `vancall:` lines at wait+3 s, then `crewhold: ... timer x -> y` lines.

Smallest opt-in addition if the doors stay unreached (not implemented): `[Bots] BoardReachLast`, default 0; when 1 klmv_reach_pass does not set `relax=1` at the last vehicle, so the doors order runs for stage-3 bots within 30 m (klmove.c:893). GUESS: this fixes only the last metres, not distance.

## 4. Hop-6 N
- 150 s carried all 7 with no GIVE UP. Below ~107 s it pre-empts normal joins [doc retomoto_leaderless.md:96].
- Time matters more than the first version said: the carry at r155 left 147 s until the round end (r302). The walk from the landings to the van area took the crew until about r260-280, partly because Hunted scattered them (section 1). So lowering N (GUESS 120 s) buys 30 s directly, but change it only after (l), not in the same run.

## 5. Order
Run the living-human check (leaderless retomoto doc, step 5: does hop 6 pre-empt a living human?) before (l). Reason: if hop 6 carries a human's crew down before him, (l)'s result is not about the leaderless case. Unchanged.

## Corrections to the first version
1. Clock: hop times were given in the otrace clock (r181..185), the rest in wall clock. Now one clock (section 0).
2. "No key gives stage 3 without the human" replaced by "none in time" (BotVan, BoardAll, BoardNear, VanCallNear exist).
3. Hunted: not "back toward the fed"; 45 toward you, 55 aside, 58 cover places; about 100 s, not 70.
4. Board tactic: it walks to the boarding object; the 300 units is the arrival range, not the reach. Bot 4's missing last 8 m is unexplained (GUESS only).
5. Distances: 51-92 m (and 8 m), from the boarding place, not "146-230 m" and not "to the fed". The 146-230 m came from L83.
6. Walk speed: 3.3-4.1 m/s, so 150 m would be 37-45 s, not 25 s.
7. Verdict on (l): from "rescues bots within about 100 m" to "likely holds the van long enough for the whole crew, if the guard allows it".
8. Added: no street escape box (tower box only); stage 3 is therefore the only way aboard; hold counts any stage.
9. Added: durations 96 s / 107 s in stage 2 (the first version said 80 s or more).
