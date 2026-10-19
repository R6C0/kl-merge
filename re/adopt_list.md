# Adopt list (2026-10-18, offline; e5 compiled from the logs and a read-only look at <DD> and C:\kl_build_1018)

Claims carry "per log note <date time>" (re/open_work_log.md) or "checked" (read in the files today). UNKNOWN = not in any note or file.
Nothing here was run in the game by this page. Zip ids are the first 8 hex of md5 of the zip. Hook/ini ids written by 3f in the log
(a57d9ce7, ccec94fb) are SHA1 prefixes (kl_autotest prints sha1; 3f confirmed 10-18 16:40): hook sha1 a57d9ce7 = md5 249ab16a, ini sha1 ccec94fb =
md5 231cde94, i.e. the same files as live. Checked: live dinput8.dll md5 249ab16a =
C:\kl_build_1018\owner_1018\hook_apply1018\dinput8.dll; live KLHook.ini md5 231cde94 = KLHook.ini.before-apply1018 + exactly the keys of
log note 10-18 11:50 (CopToCrew 0.01, DownsMax 3, EscVisitFix, CrewRoute*, BoardReachFlat, LastVehicleFlagged, FollowOutHoldAlone*, ComeMoved).
Both files were last written 15:07 (end of L79); log note 14:40 says all was restored after each run.

## 1. Already live (nothing to decide; one undo: "UNDO everything applied 1018.bat" in owner_1018)
Per log note 10-18 11:50: hook SHIP build, CopToCrew=0.01, DownsMax=3, the escape-visit stack (EscVisitFix=1, CrewRouteHold=45,
CrewRouteRange=100, CrewRouteAlone=1, BoardReachFlat=1, LastVehicleFlagged=1, FollowOutHoldAlone=1, Range=60, ComeMoved=1).
Per log note 10-18 12:00: Hot Coffee II walk-through doors (DM01B ea8cbc82). Ini also has PointBlankToCrew=5, YouToCop=2.0, CopToYou=1.3 (checked).

## 2. Maps (redirect slot in brackets; live md5 checked today)

### Vault, DM03A [page 2 F07]
- LIVE: 7cd07d15 (= vault_e9late110, plaza squads wake 110 s after the exit box; KLJoin 8a8c4fdd).
- BEST PROVEN: the live zip itself. L65 (7cd07d15 + hook q + CopToCrew 0.01 + hold keys): you + all 7 out on visit 1, 0 asserts (per 10:20).
  Those keys are live now. L60: you + 6 of 7 (per 09:40). Plaza-cut alternative vault_e9 (L26: 3 out, 1 dead) was NOT better than late110
  (L33: you + 3 loyal, 3 traitors dead, per 06:00).
- STAGED, NOT RUN (all KLJoin 8a8c4fdd, .HVK/.prp only; rollback = 7cd07d15): B door-nocol 54c2b946, C noblocker 1c4b1667,
  D both e6be64a7 (vault_both), hide-parts e69d7a61 / 3574538f (hideparts, bank-stage). Cause hint: door body 27109 or PathBlocker_Vault
  seals the inside-vault places (per 16:25). Queued as 3f (g).
- RUN L80 (3f, 18:10): hide-parts 3574538f + hook 1018u, EscVisitFix=0. PASS, 0 asserts. Visit 1 worked (escprobe: 1e4 set at state 1 without the fix);
  you + 5 aboard, 1 dead, 1 left 13.4 m out. So the van show/hide was the visit-1 cause; the result is below L65 (you + all 7), no reason to switch yet.
- RUN L85 (3f (d), ~23:25, live map + hook zc + WalkAwayReorder=3, CrewRouteHopHold=15): PASS, ALL 7 AI escaped, 0 dead (2 traitors aboard),
  the hold used 45 of 45 s. WalkAwayReorder: 10 orders, all redundant (bots on the stair route out of the vault, already targeting the doors);
  harmless here. CrewRouteHopHold not needed. Fix for the false orders staged as (m): hook out_e5_1018zk WalkAwayGoal=8 (71865807).
- DECISION: keep late110 and let 3f's queue (g) pick B/C/D; or say "cut" to switch to vault_e9 (UNKNOWN md5 in the folders; ask 3f).
  L85's all-7 result came with CrewRouteHold=45 at work; WalkAwayReorder added nothing, so do not adopt it.
- RUN L86 (3f (e), ~23:31, + BoardReachRepeat=3 / Chase=1 / Sent=6000): PASS, ALL 7 AI escaped, 0 dead. CrewRouteHopHold fired for the first
  time (+15 s) and got the last 2 bots aboard: CrewRouteHopHold=15 is a CANDIDATE for the Vault. The chase took 12 s longer and its orders kept
  the bot's own height (BoardReachAim, live 80): sent to floors below the van. Fix staged as (n): hook out_e5_1018zl BoardReachAimHeight=3
  (7ebc5c79), ini vault_wag\PT_DM03A_wrh.ini 458a5c99. Do not adopt the chase keys before (n).
- RUN L98 (3f (n): zl + PT_DM03A_wrh, live map): PASS 363 s, you + 6 of 7. Rec 1 was DOWNED (botdown) 19 m out until departure, so a down state, not routing.
  - BoardReachAimHeight=3 did aim the 17 off-floor orders at the van's object (y 822).
  - The path there runs round via the far ramp: bots first walked up to 30 m AWAY, then back.
  - The van waited 113 s (L85 50.5 s, L86 62 s); crewhold and then FollowOutHold extended it.
  - VERDICT: no gain on the Vault, so do NOT adopt BoardReachAimHeight. As the census said (re/reach_aim_census.md), the own-floor aim worked as a stair carrot.
    The chase keys stay a candidate only on L86's evidence.
- RUN L88 (3f (g), 23:42-23:46, door B 54c2b946 + hook zi + live keys): PASS 243 s, INCONCLUSIVE.
  - The human reached stage 3 at r ~80 with $0, so the round ended before r 150.
  - Nobody earned anything: the human and all 7 bots stayed at $0.
  - No bot reached the inner vault (z -12830..-13190). They stood at y -960, z -11.7..-12.0k.
  - Boarded: 1, 2 (traitor), 6 and 5; 3, 4 and 7 were left behind (Spare kept them from being shot).
  - The $0 may be a regression of B, or the human's pickup failed. Asked 3f for (g0), a control on 7cd07d15, and (g1) B again,
    both with the human held in the vault to r 200.
  - Do not adopt B.
- RUN L91 (3f g0, 00:02-00:09, CONTROL live 7cd07d15 + hook zi + hold script PT_DM03A_hold): PASS 399 s, 0 asserts.
  - The human stayed at $0: the script's goto stops 5-8 m short of the vault and never re-tries. That is the script, not the map.
  - First bot money: r 83 rec 5 (became a traitor at r 101, then died), r 133-136 recs 3/2/7/6; recs 1 and 4 got $0.
    Bots stood in the deep vault (z -12830..-13190) from about r 130.
  - So L88's all-$0 round was too short (it ended at r ~80). It is NOT evidence against door B. g1 (B with the same hold script) is the fair comparison.
- RUN L92 (3f g1, door B 54c2b946 + zi + the same hold script): PASS 347 s, 0 asserts.
  - The human got into the deep vault at r 33 and had $900 k by r 77. In the control, the door kept the human out.
  - Rec 5 took $1.40 M (it went traitor, then came back and boarded). No other bot went deep or earned anything; all boarded with $0.
  - Van: called r 174, left r 242, one visit.
- READING (e5, from the two runs; GUESS where marked):
  1. The vault's loot ran out. Control: 270 + 380 + 105 + 255 k + rec 5's 1.29 M = about 2.3 M. Door B: you 900 k + rec 5 1.40 M = about 2.3 M.
     So in L92, rec 5 and the human emptied the vault before the bots' usual r ~139 entry. GUESS: the bots stayed out because no money was left, not because of the door.
  2. On the live zip the bots DO get into the deep vault (all 4 together at r ~139). So "door body / PathBlocker seals the inside-vault places" (16:25) is answered:
     not sealed, only timed. GUESS: r ~139 is the vault opening.
  3. Door B lets the human in about 100 s before that opening, so it skips the heist's wait at the vault door. That is a change to the game, not a fix.
  - RECOMMENDATION: keep the live 7cd07d15. Do not adopt B. C (noblocker) and D (both) also aim at the "sealed" cause, which (2) rules out, so drop them unless the owner wants the vault open early.
- RUN L93 (3f j, Hot Coffee II ea8cbc82, hit-log hook out_3f_1018d 3f073ebb, PT_DM01B_hits): 401 crew hit lines.
  - Hits: almost all -1; no friendly fire. The +0xac target matches 97 %. Median nearest police: 9.7 m. Point-blank shots: once. botdown worked twice.
  - Rec 1 DIED at 00:22:17.092 from one 340.0 drop at full health. The nearest soldiers targeting it were 30.9 m or more away.
    Its block target had moved from (2408, 0, 27240) to (2275, 0, 27263) 14 ms earlier.
  - GUESS: this is the same instant kill as the 5 L70/L71 deaths (no down first). Candidates: a car, an explosive, a kill volume or a script.
    Workflow wlhwez0yl is looking offline; output goes to re/hotcoffee2_oneshot.md.

### Last Call, DM05A [page 3 F01]
- LIVE: df719d34 + KLJoin dfc29f60 (the "sa" build: EnterVehicle field 9 empty, per 07:10).
- BEST PROVEN: L78 "combined route": you + all 7 aboard, 0 dead (per 15:16). L51 full pass on the live zip (per 08:30); L75 you + 6 of 7 (per 14:40).
  L78 files (3f confirmed 10-18 16:40): zip 5b0a025b (escape msg, C:\kl_build_1018\lastcall_route_next\DM05A) + KLJoin ea0446c1 (hop
  Stage=1) + hook out_e5_1018y (md5 792a9daf, NOT the live hook) + test ini PT_DM05A_roofgap.ini = live keys + [Bots] VanCallNear=40,
  VanCallLast=1, CrewRouteHopHold=15, BoardReachSent=6000, BoardReachRepeat=5, BoardReachChase=1. Adopting L78 = all four, not the zip alone.
- (18:2x: hopstage_next and roofgap_next folders deleted to free C:, superseded by lastcall_route_next / L78; rebuild from kl_route if needed.)
- STAGED, NOT RUN: hopstage_next (zip df719d34 + KLJoin ea0446c1, same as L75 ini); roofgap_next (6903219f + ea0446c1; roof gap, BoardReachSent
  442a014d, queued L77 rerun after the 14:27 VOID); rtcops 6903219f ran as L76 (see section 3).
- DECISION: adopt the L78 set (zip 5b0a025b + KLJoin ea0446c1 + hook 1018y + those six [Bots] keys) in place of df719d34 + dfc29f60, yes or no.
  The hook and the keys apply to every map, so 3f would check them on the others first (GUESS: one L78 run only).

### Retomoto Tower, DM09 [page 2 F06]
- LIVE: bf1dfdb3 + KLJoin b2bb6a2f (= rt_join_next2).
- BEST PROVEN: no clean win to adopt. L79 (KLJoin e8c41f20 = rt_join_next4 margins + hop 6, hook 1018za): PASS but NO van; the human died on the
  atrium stair (-2007, 20300, -1330) at 82 s; the margins did not matter; 5 hop-3 walks were teleported by GIVE UP (per 15:35 and re/retomoto_fa.md s14).
  Vans came in only 7 of 72 logged sessions; none in 21 where the human died first (s14(1)).
- STAGED, NOT RUN: rt_join_next5 KLJoin 237f60f0 (kl_rt_joinini --giveup c1a43afc); rt_join_next3 d4dddd6d (folder deleted 18:2x, superseded by next4/5); --rescue-wedge d1258797 (UNKNOWN
  folder); hook keys in section 4. Also dm09_ini_1018 (KLJoin 3f9ce520 for DM09, 1cf31914 for the DM09RB* variants): purpose UNKNOWN in the notes.
- RUN L83 (3f (b), ~23:10, Lead=450 + WalkExclusive=1, hook za): PASS, no van. Human fed at 70 s, FedSkip kept the crew in the tower, hop 2
  carried 3 bots, 0 GIVE UP; WalkExclusive works. LastVehicleFlagged called the last van at 45 s left; it waited the stock 8 s and left EMPTY,
  crew 151-237 m out, stage-2 bots never got stage 3 (FollowOut needs YOUR stage 3). -> fix staged as (l) below.
- RUN L84 (3f (c), = (b) + PointBlankToYou=20): PASS; the key fires (13 steps scaled 100 -> 20), human lived, crewjoin EARLY moved all 7 to the
  street. CAVEAT: the test ini also has the survive dials (police->you 0, health x10), so this does NOT show that 20 saves a normally armed
  human. A fair test needs live CopToYou / health. Still the owner's call.
- STAGED, NOT RUN: (k) --leaderless-hop KLJoin 0b557e40 (6c7066d1, re/retomoto_leaderless.md); (l) fed-van: TEST hook out_e5_1018zj 40fe1088
  ([Bots] CrewRouteFed=1, 57f0f13e) + PT_DM09_fedvan.ini e21001ed (VanCallLast=1, LastVehicleLead=600, CrewRouteRange=300), re/retomoto_fedvan.md.
- RUN L94 (3f (k), leaderless KLJoin 0b557e40 + zi + PT_DM09_die): PASS 392 s, 0 asserts; restored KLJoin b2bb6a2f. r is counted from 'fed: round 2'.
  - The human was fed at r24. In the join box FedSkip fired and nothing moved.
  - Hop 6 carried all 7 bots at r181..185, and they reached stage 2 by r188. GIVE UP lines: 0 (L79 had 5).
  - Only bot 4 reached stage 3 (r264). BotVan called the van at r268, the round's last vehicle. It waited the stock 8 s and left EMPTY.
    Bot 4 was 8 m off; the other bots were 51..92 m off. Nobody escaped.
  - READING: the leaderless hop works as designed. What remains is L83's gap: stage-2 bots get no stage 3 without the human, and the last van waits only 8 s.
    That is what (l) targets. Workflow wk18hv8ig is checking the (l) code paths against L94 (re/retomoto_l94.md).
- RUN L95b (3f (l) try 1: zj + PT_DM09_fedvan e21001ed + KLJoin 0b557e40): PASS 366 s. NOT a test of (l): the ini inherited god mode from PT_DM09_lead, so the human never turned fed.
  - EARLY join at r123: all 7 bots went to the street.
  - The human's goto stuck 13.8 m short, so there was no stage 3 for anyone and no van. Rec 1 turned traitor and died.
  - (l) is rerun as L96 with PT_DM09_fedvan_die 3185b898 (PlayerHealth 0.05).
- RUN L96 (3f (l): zj + PT_DM09_fedvan_die 3185b898 + KLJoin 0b557e40): PASS 463 s. FIRST RETOMOTO ESCAPE WITH A FED HUMAN: 3 bots aboard.
  - The human turned fed at r22. Hop 6 carried all 7. Deaths: recs 2, 1 and 3.
  - Stage 3: rec 5 (traitor); recs 6 and 7 via VanCallLast; rec 4.
  - The last van waited 53 s: the crewhold took the timer from 1.9 to 46.9 s.
  - Aboard: recs 6 and 7, and rec 5 (back to loyal). Rec 4 was left about 5 m off in stage 3, which is the BoardReachLast case. It is rerun as (s) with TEST hook out_e5_1019a 043419cb.
  - Hunted orders: 141, of which 38 went towards the fed.
- RUN L97 (3f (s): TEST hook out_e5_1019a 043419cb + the L96 ini + [Bots] BoardReachLast=1, BoardReachLastRange=0 + KLJoin 0b557e40): PASS 463 s.
  ALL 6 LIVING BOTS ESCAPED on the last van with a fed human. L96, the same setup without the key, got 3.
  - Doors orders went out once per bot, 0 refused. All 6 boarded 'AT THE DOORS' within 23 s.
  - crewhold held the van 47 s, and the van left at 00:58:53. Rec 3 died earlier.
  - Retomoto best proven so far: leaderless KLJoin 0b557e40 + hook 1019a + [Bots] CrewRouteFed=1, VanCallLast=1, CrewRouteRange=300, LastVehicleLead=600, WalkExclusive=1, BoardReachLast=1.
    The DM09 set is one run only. These are global [Bots] keys; GUESS: put them under [Bots.DM09] (PerMap, L89) so other maps keep the live behaviour.
  - Still open: (q), the same set with a living human (workflow w8f1muo8a predicts it, re/retomoto_hop6_living.md).
- DECISION: WalkExclusive=1 + LastVehicleLead=450 are CANDIDATES (they acted as designed in L83/L84, no harm seen; two runs only); van boarding with a fed human
  waits for (k)/(l).
- ADOPT 3 (staged 2026-10-19, C:\kl_build_1019\adopt_1019, dry-run only): KLJoin b2bb6a2f -> 0b557e40 + PerMap=1 + [Bots.DM09] L97 keys (+ WalkExclusive, global GUESS; a no-WalkExclusive variant exists).
  - ADOPT 3h: SHIP hook b28dd444 (HEAD 3f5737c2; six klhook commits beyond 1018zh, all keys default 0) from 249ab16a or 916c3c57. Without 3h the DM09 keys are inert/partly inert.
  - Order with ADOPT 2: 2, then 3; undo 3 before 2 (UNDO 2 drops PerMap; re-running ADOPT 3 repairs it). Review w5k99giuv: md5 guards and byte-exact undo pass on scratch copies; one UNDO 3 PerMap bug fixed. DECISION: yes/no on 3 + 3h. Not run for real.
- RUN L101 (3f (q): hook 1019a, PT_DM09_live_brl_slow, KLJoin 0b557e40, human NOT god mode): PASS 433 s. The prediction in re/retomoto_hop6_living.md holds.
  - All 7 bots had sat 150 s at hop 6's From and were TELEPORTED to the street at r 155.6-158.9. The human was still alive and holding at the boardroom loot ($300k), carrying the crew's $1.8M share.
  - Waste: rec 2 then got 19 escort orders (every 2 s) aimed at tower height until the human died at r 193.
  - The van came once, as the last vehicle: 2 out with $405k, 5 bots died in the street. The human was fed at r ~198, dead at r ~261.
  - CAVEAT FOR ADOPT 3: with a LIVING human who is slow, 0b557e40 strips them of the whole crew at r ~156. A fix is the NoHuman gate in klhop.c, or counting From time only while the human is also down there. klhop.c is 3f's file; it is on 3f's owner list, not done. Until then ADOPT 3 suits a fast human only.

### Hasta, DM11B [page 3 F04]
- LIVE: ce42dcc9 + KLJoin 437c96ee.
- BEST PROVEN: with the live balance, ce42dcc9 gave you + all 7 out in L55/L56/L57 (per 09:40). Police build 3a186c93 (hasta_next, only 2 of 10
  plaza police started, KLJoin 437c96ee): L73 PASS, heli survived, you + all 7 out on visit 1 (per 14:40). The mechanism is a GUESS (per 12:18).
- STAGED, NOT RUN: rtcops DM11B 568e1786 (section 3). police2 131c8c2b (C:\kl_build_1018\hasta_police2\DM11B, KLJoin 437c96ee = live; builder
  --rest-late=120, 13d72a3b): the 2 ExitStreet_Left police start at the stair top as in 3a186c93, the other 8 start 120 s later instead of never
  (re/hasta_police.md e255313c: they were never started by design; the heli kill by SMG fire is a GUESS). Queued with 3f as (i).
- RUN L90 (3f (i), 23:56-00:00, police2 131c8c2b + hook zi): PASS 381 s, you + ALL 7 out on visit 1, 0 dead.
  - INCONCLUSIVE for the 8 late police: the heli lifted off about 38 s after the stair top, long before S=120. The census showed 0 ZFFActor.
  - Next: S=45 (lift-off + 5 s). STAGED, NOT RUN: C:\kl_build_1018\hasta_police3\DM11B F04_Main.zip 43a7c699, KLJoin 437c96ee (= live).
    - Same recipe as police2 (chain --blast --lock-wing --lock-show --corner-floor --heli-escape --heli-hvk-origin, then post.py and reslot.py), with --rest-late=45.
    - It differs from 131c8c2b in ONE .prp byte (float 120.0 -> 45.0); every other member and side file is identical.
- RUN L100 (3f (p), 01:16-01:23, police3 43a7c699 + hook zi, PT_DM11B_p): PASS 441 s, you + all 7 out (rec 7 a traitor).
  - The heli left with the 7 bots at r~260 and came back; you boarded on visit 2 at r~326 after a plaza hold. No heli damage line.
  - STILL INCONCLUSIVE for the 8 late police: the alive census fell 43 -> 17 and never rose; there are no police -> crew/you lines, and no
    balance/hit/fire lines during the hold. The 300/360 s pictures show no police near you. GUESS: they never engaged, or never spawned.
  - DECISION: no reason yet to adopt police3 over 3a186c93 (ADOPT 1).
  - CAUSE FOUND (re/hasta_late_police.md, 30b5c425): police2/police3 can never start the 8. Way#01 and Way#02 share one GateGroup, which passes once (kl2 0x7fd5a0), so the stair top uses it up. L90/L100 tested nothing. Fix A (opt-in, police4) is being built by workflow w1ai9bl73.
- STAGED, NOT RUN: police4, built with the opt-in --rest-late-direct flag; the delay names the 3 late squads directly. Folder C:\kl_build_1019\hasta_police4: DM11B (S=45, d49627cf), DM11B_S90 (S=90, a9ee0ebe, RECOMMENDED: the 8 start ~13 s after the van call, GUESS). KLJoin 437c96ee (= live).
  - Only node 20000's list differs from police3. The checks pass. That a delay starts a 10_RunToCover rout is stock wiring (F01 Timer_SwatMoreForward). That the squads then show and move is a GUESS until a run. Queued with 3f as L105.
- L105 (3f, 2026-10-19, hook zi, only the zip swapped to S90 a9ee0ebe, all 25 side files identical to live; restored after to ce42dcc9 / KLJoin 437c96ee / 6755CC0C): PASS, 444 s.
  - Stair top (20240/20242 first move) at r 139. ALL 8 late police first change at r 229 = stair top + 90.0 s. 5 of the 8 killed; 20254, 20255, 20272 lived and moved.
  - They arrive ~18 s after the visit-1 heli waits (not ~13 s after the call as guessed). Visit 1: 5 aboard (2, 4, 5, 6, 7); rec 3 out as traitor; the human out on visit 2. Rec 1 never left the start (stage 0, $0) and died. Loot out $3.15M.
  - So the wiring is confirmed live. DECISION for the owner: ADOPT 5 = S90 a9ee0ebe, one click: C:\kl_build_1019\adopt_1019\ADOPT 5 Hasta police4.bat (UNDO 5 to go back). Zip swap only, KLJoin unchanged; an alternative to ADOPT 1 (Hasta police 3a186c93, same zip; it refuses while ADOPT 1 is in). Scratch-tested.
  - L105 rec 1 ($0, died) was the ESCORT bot, not idle (re/hasta_idle_bot.md): released at the van wait, 83 m to walk past the late police, the van left 52.6 s later. One run. Ini-only try for 3f: [Bots] EscortUntil=1 on DM11B (frees it ~11 s earlier; GUESS that it is enough). Proposed opt-in [Bots] EscortCalled (klescort.c, 3f's file) is text only.
    - Layer check, police check, check_passes and klt_audit all PASS.
    - Queued as 3f (p): script PT_DM11B_p.ini 8b693466 holds the human about 75 s in the plaza.
  - Do not adopt police2.
- DECISION: swap in 3a186c93 (the plaza police that were passive are the cost), yes or no. Alternative to avoid the cost: none proven.

### A Walk in the Park II, DM06B [page 3 F02]
- LIVE: 7fef2733 (no KLJoin.ini in the live folder, checked).
- BEST PROVEN: the live zip. L68 (hook r, CrewRouteAlone): all 7 out on visit 1; L64 (balance only): all 7 via visit 2 (per 10:07, 09:40).
- STAGED, NOT RUN: loot6 tea-house case 3386b972 (tools/kl_fa_park_loot6.py 2f7e4e5b; loot was 166 of 165 flat from the stop, queued 3f (f));
  no-van-show d345bc5b (C:/kl_scratch/stage_park_nvs, hide/show A/B for the visit-1 cause, now moot since EscVisitFix is live); park_next KLJoin c99c4e11
  (two crew hops, with 7fef2733); rtcops 7bf368a7.
- RUN L81 (3f, 18:17): no-van-show d345bc5b + hook 1018s. PASS, 0 asserts, 416 s. The van's 1e4 was already set at state 1 without EscVisitFix, state 1->3->5 on visit 1;
  6 bots aboard (one traitor); the escort stayed with the scripted human 6 m out, the human did not board. Diagnostic only (EscVisitFix live): nothing to adopt.
- RUN L82c (3f, 2026-10-18 ~23:00): park_next KLJoin c99c4e11 + TEST hook out_e5_1018zi. PASS, 402 s. ALL 7 AI aboard on visit 1 (one traitor), but
  the two hops carried NOBODY (From reached 5x, no bot stayed 8 s): every bot walked on its own, so the KLJoin is not what helped. L68 already
  had all 7 out on visit 1 without it. -> Do NOT adopt c99c4e11 (adds nothing proven); keep the live folder without KLJoin.ini.
- DECISION: adopt loot6 (3386b972) - still OPEN: run (f) did not answer it.
- RUN L87 (3f (f), 23:35-23:38, hook zi + PT_DM06B_hop): PASS 424 s, all 7 AI aboard visit 1 (CrewRouteHold 45 s), but INCONCLUSIVE for loot 6.
  - No bot came within reach of the tea-house case.
  - Rec 2 was routed there at 23:35:36; the escort re-pointed it to the human 2 s later.
  - Rerun queued: the same zip and ini with [Bots] Escort=0, sent to 3f as (o).
- RUN L99 (3f (o): loot6 3386b972 + hook zi + PT_DM06B_noesc, Escort=0): PASS 400 s. A BOT TOOK THE MOVED CASE.
  - Rec 1, on the game's own loot choice and with no klmove order, walked into the tea house and stood 72 flat from the case.
    It gained $150,000 there (= the case).
  - Rec 4 came later to the same spot and got nothing (the case was empty). All 7 bots got out.
  - loot6 3386b972 is now an ADOPT CANDIDATE (one run). The owner's call.

### Hot Coffee II, DM01B [page 3 F03]
- LIVE: ea8cbc82 (walk-through doors; rollback = DM01B.replaced-1018doors, 01749906).
- BEST PROVEN: L70 (hook s + BoardReachFlat): rec 6 and traitor 4 escaped on visit 1, 3 dead, 2 never called (per 11:05); L71 with VanCallNear=40: both called stage-1/2 bots boarded on visit 1 (per 14:40).
  L52 with the 0.05 balance lost 6 of 7 (per 08:30); the 0.01 balance is live.
- STAGED, NOT RUN: rtcops DM01B 073dd57f (also 4 garage cops get rifles, per 14:11).
- DECISION: turn on [Bots] VanCallNear=40 (hook key, section 4), yes or no.
- ONE-SHOTS (L93 and L70/L71): bots die from one unscaled 340 drop.
  - Refuted: gunfire, PointBlankToCrew, van, human, snipers, SM_ scripts (re/hotcoffee2_oneshot.md, re/hotcoffee2_campaign_leftovers.md).
  - Lead (GUESS): a campaign car with BlowupChanceDefinite stands 1.5..3.5 m from every site.
  - Staged cars-only 21c6ed49 (C:\kl_build_1019\hc2_nocampaign\DM01B_carsonly). The A/B is queued with 3f: (r) live + LogCrewHitsBig=100, then (t) cars-only.
  - RUN L102 (r, control: live ea8cbc82, hook f88586e9, PT_DM01B_hits + LogCrewHitsBig=100): PASS 517 s. ONE instant kill, rec 5 at r 54.6, (684, -15, 9215).
    - Health 167 -> 0 in one drop, after about 3 s of -2 chips from 2 soldiers at 3.3 m. At death an Enemy at 8.3 m was aiming at rec 5.
    - No explode, blast or car line in the whole log. No BIG line (the hit was under the rate limit). The 2 other deaths were chip deaths.
    - So this kill is "the rest of the health in one hit" with a soldier close and aiming, not 340 from nowhere. The car lead looks WEAKER (GUESS until L103).
  - RUN L103 (t, cars-only 21c6ed49, same hook and ini): PASS 519 s, NO instant kill. No drop of 10 or more at all; the BIG path was armed past the 400 limit and stayed silent.
    - One death (rec 5, r 336) was a chip death. 4 bots out with $1.085M (L102: 1 out with $0, 3 dead).
    - Score so far: cars live = one-shots in L70, L71, L93, L102; cars-only = 0 in 1 run. It fits the cars, but L102's victim had a soldier aiming at 8.3 m. A second cars-only run is asked of 3f (L104).
    - CANDIDATE (pending L104): 21c6ed49 in place of ea8cbc82. It only stops the 45 campaign cars blowing up (tools/kl_hc2_strip.py --no-snipers).
  - RUN L104 (cars-only repeat): PASS 465 s, no one-shot, 0 deaths. 5 bots + a traitor out with $1.62M. L103's "1 explode line" was the ShakeScale setting line, so 0.
    - SCORE: live ea8cbc82 = one-shots in 4 of 4 hit-logged/observed runs (L70, L71, L93, L102); cars-only 21c6ed49 = 0 in 2 (L103, L104).
    - ADOPT 4 / UNDO 4 Hot Coffee cars.bat in C:\kl_build_1019\adopt_1019. It swaps the zip with an md5 guard and a backup; tested on a scratch copy only.
    - DECISION: adopt 21c6ed49 for Hot Coffee II (zip only; every side file is identical to live). The mechanism (car blow-up with no log line?) is still being traced (workflow ww3881lpe, re/hotcoffee2_wholehit.md).

### Other installed maps (checked: KLExpansion\Maps; zips md5)
- Page 2: DM01 [F01] 94dc052b, DM02 [F02] c00d4d07, DM03 [F03] cf1dc436, DM06 [F04] 039dc886, DM09 [F06] (above), DM03A [F07] (above).
- DM02: boarding fixed by BoardReachAim=80, L23 7/7, L25 6, 0 dead (per 05:30). BoardReach=300 was left as the owner's call (per 05:30).
- Unreferenced by any [Redirect]: DM09RB, RB2, RB3, RB4, RD, RV, RV2, T01 (the T01 slot is listed in the folder; its use UNKNOWN).
- Stock overlays DD01..DD09 on page 0 (stockfa, installed per 10-17 23:40; md5 list is in the folder, nothing proven or pending since).
- No pending decision found in the notes for these.

## 3. Cops (rtcops, Retomoto-style rows): builds change only the .prp, cops get harder
Zips (C:\kl_build_1018\rtcops_next): DM01B 073dd57f, DM03A 985d7b97, DM05A 6903219f (5 rifles accuracy 55 -> 82.5), DM06B 7bf368a7, DM11B 568e1786.
Only Last Call ran: L76, 0 crew dead or down, 6 of 7, "no measurable difference" (per 14:40/14:34). The other four are NOT run.
- DECISION: harder cops on the Dead Men maps, yes or no (you must play them; the numbers do not say).

## 4. Hook-key decisions (all in [Balance]/[Bots] of <DD>\KLHook.ini; undo by deleting the line)
- [Balance] PointBlankToYou=20.0 (unset = 100; needs the decimal point): census of 87 Retomoto rounds, human dies to point-blank steps at the
  atrium stair and reception east end (per 15:35). NOT RUN. It makes YOU tougher. Decision: yes/no.
- [Bots] WalkExclusive=1 (off live): stops fedkit Hunted from re-ordering walking bots (the Retomoto GIVE UPs; per 15:35). A GUESS, NOT RUN (3f queue b). Decision: yes/no, or wait for the run.
- [Bots] VanCallNear=40: L71 PASS on Hot Coffee II. Per 16:25 it never fires on Last Call because FollowOut already gives stage 3. Decision: yes/no.
- [Bots] LastVehicleLead=450 (tenths of a second = 45 s; default 25): for Retomoto when the human dies early. Test ini only, NOT RUN.
- [Bots] BoardReachRepeat=3 / Chase=1 / Sent=6000 (queued 3f (e), PT_DM03A_wr.ini), HalfGuard (f75970fa), WalkAwayReorder (c0b2a6b6), --rescue-wedge:
  all opt-in, NOT RUN. Not decisions yet; wait for runs.
- [Bots] FollowOut=0: would let VanCall* act but ends the crew following you out; a trade (per 16:25). Default stays.
- CopToCrew=0.01 and DownsMax=3: already live and validated on 5 maps (per 09:40). Nothing to decide.
- klbuild.c (lobby build check): source only, in no build, stays out until you OK stage 4 (per 15:35). Build code for private matches: live = 6755CC0C (tools/kl_buildprint.py).

## 5. Open items that need you
- PUSH: `git push origin rtp-schemas:main`. Checked: HEAD is 50 commits ahead of origin/main (49 before this fact-check commit); every note since 10-18 asks for it.
- DISK: C: 2.7 GB free (checked; 931 G drive 100 %), G: 11 GB. C:\kl_build_1018 is 49 GB, owner_1018 9.4 GB. 3f's installer needs copy + 2 GB and refused at 2.1 GB (per 11:05).
- REPLACED-* CLEANUP: 15 folders `C:\kl_build_1018\owner_1018\Maps\*.replaced-*` (rollbacks: DM01B 1018doors/1018flatback/fedv2, DM03A e9late/e9late110,
  DM05A 1018roof/1018sa, DM06B 1018nvhback, DM09 1018dm09r, DM11B 1018back/back2, DM01/DM02/DM06 1018audit, DM03 1018audit3). 3f deleted 34 duplicates before
  with your OK (per 11:20); the auto-mode refused these two jobs and left them to you (per 10-18 05:30 note). Keep the ones you may roll back to.
- FIND.EXE: 4 find.exe processes are running now (PIDs 61912, 66584, 75080, 19676, checked with tasklist), the 05:30 note's five PIDs (75612 30944 25220 8256 51284) are gone.
  Kill them: `taskkill /F /IM find.exe`. Also the 0-thread zombie kl2.exe PID 48664 (since 10-14, 20 KB) is still present, left alone.
- Steam is running; no live game run is going (checked), the queue waits while you play.

## 6. Summary of single decisions
1 Last Call: adopt the L78 set (zip 5b0a025b + KLJoin ea0446c1 + hook 1018y + six [Bots] keys). 2 Hasta: swap in police build 3a186c93.
3 Park II: adopt loot6 3386b972 after rerun (o) (L87 was inconclusive). 4 Vault: keep late110 (L91/L92: bots do get in at r ~139; B only opens the vault early for the human). 5 Retomoto: wait for queue (b)/(c).
6 Hook keys: PointBlankToYou=20.0, WalkExclusive=1, VanCallNear=40 each yes/no. 7 Cops rtcops on five maps yes/no. 8 Push, disk, find.exe, replaced-*.

## 7. L78 keys on other maps (static reading of klhook/klmove.c; nothing here was run on those maps)
- Live hook a57d9ce7 (md5 249ab16a) was built at ed4322fb (11:50 note). `git diff ed4322fb 442a014d -- klhook` = klmove.c only, +77/-9: VanCallNear f3eb8d3d,
  VanCallLast + CrewRouteHopHold 51582eaf/ac127935, BoardReachSent 442a014d (= 1018y). Every key is default 0 = old behaviour, so the hook alone changes nothing; the ini keys do.
  BoardReachRepeat/Chase (1763efea, 604fc16e) are already in the live hook. The hook (klmove) acts only in Arcade, on a map that is not the stock one of its slot.
- Stock Dog Days FA maps DD01-DD09 (page 0): no effect of any key (klmove's own gate). Nothing to check there.
- VanCallNear=40 / VanCallLast=1: call heist stage 3 on stage-1/2 loyal bots (40 m, +-4 m height; Last: any distance) once per bot, after VanCallDelay.
  FollowOut=1 (live) already gives stage 3 at the van call, so they never fired in L74/L75/L78. Only L71 (Hot Coffee II, no FollowOut effect first): 2 bots called 17 m out, both boarded.
  Risk: GUESS a stage-1 bot near the van drops loot for the van; a van map where FollowOut does not call (Vault, Park II, Retomoto) is the case to watch. A heli (Hasta) is read the same (veh 3/4): GUESS, never run.
- CrewRouteHopHold=15: once per visit +15 s to CrewRouteHold (45 s live) if a stage-3 bot closed 1 m in within 15 s; needs CrewRouteHold, human aboard. Worst case van waits 60 s.
  Only matters where klhop hops exist (Last Call; Retomoto has [CrewHop]). Elsewhere it only adds time while a bot still closes in. Low risk; costs the human waiting.
- BoardReachSent=6000: a called bot up to 60 m from the boarding box (was 30) gets the order to the doors (klescort order, once per visit). Not for a held escort or a traitor.
  Risk: it overrides what a bot does mid-fight 60 m out, and a walk over a wall-split route may be longer than the van waits. No effect on the round's last vehicle or from visit 3 on (BoardReachVisits=3: boxes work as stock, `have` false, loop returns). GUESS: so Sent's gain in L78 came before the last vehicle or from the hop; L78 had the combined route too.
- BoardReachRepeat=5 / Chase=1: the order may go again 5 s after the last, and a bot in an escape box beyond BoardReach needs no 1 s stand-still; Chase re-sends a bot that walks off. Evidence: DM02 L18 (Repeat=3+Flat) 5 of the crew out vs 2 in L16, 1 in L14. Risk: fights the game's own chain (re-order every 5 s up to 60 m, bots may stutter); klescort's OrderGap debounce is the only brake. FollowOut-held escorts are skipped.
- HalfGuard (default 0, not in L78) and klescort do not interact with these keys; klhop-walked bots are skipped by WalkAwayReorder/Restless only when WalkExclusive=1 (off live), so Repeat/Chase can order a bot klhop is walking: GUESS, Last Call only has hops.
- Live check before global adoption: Vault DM03A (sealed ante-room, Sent+Repeat), Hot Coffee II DM01B (VanCallNear already L71 PASS; add Repeat/Sent), Park II DM06B, Retomoto DM09 (hops + WalkExclusive question), Hasta DM11B (heli: all keys GUESS). DM01/02/03/06 equal DM02's L18 case for Repeat only; Sent and VanCall untested there.
- Safe option: adopt the keys per map (maps.ini / test ini) for Last Call only, and leave them out of the global ini until each van map has one run.
- How (2026-10-18, 9347d05f + d3b6b6cc, NOT RUN IN THE GAME): hook out_e5_1018zh (SHIP, 916c3c57) reads `[Bots] PerMap=1`; each [Bots] key klmove reads is then looked up first in `[Bots.DM05A]` (folder of the map's KLJoin.ini, case-blind). Put the six L78 keys under `[Bots.DM05A]` and only Last Call gets them. PerMap=0 (default) = today's behaviour. Log: `move: per-map [Bots.DM05A]: 6 keys override [Bots]`. TEST build out_e5_1018zi da0e9d2c.
- RUN L89 (3f (h), 23:47-23:52, zip 5b0a025b + KLJoin ea0446c1 + TEST hook zi, the same source as zh): PASS 280 s, you + ALL 7 aboard, 0 dead.
  - 'per-map [Bots.DM05A]: 6 keys override [Bots]' was logged at the map load.
  - The van left 34 s into its wait with 7/7 aboard (2 traitors).
  - Hop 1 announced 7 carries but made none: every bot walked on within 10 s. HopHold was not needed.
  - PerMap WORKS on Last Call. Still open: that another map gets NO per-map line. 3f checks that at the start of (i) Hasta.

## 8. One-click scripts (2026-10-18 20:5x, C:\kl_build_1018\adopt_1018, README.txt; md5-guarded, refuse while kl2 runs; reviewed CLEAN, never run for real)
- ADOPT/UNDO 1 Hasta police (3a186c93). ADOPT/UNDO 2 Last Call L78 (zip 5b0a025b + KLJoin ea0446c1 + [Bots.DM05A] keys, inert on the live hook).
- ADOPT/UNDO 2b hook 1018zh (916c3c57): makes the Last Call keys act. (h) = L89 PASS, all 7 aboard (TEST zi, same source). L90 (i): DM11B logged 0 per-map lines, so the keys stay on Last Call. 2b is READY for the owner's yes or no.
