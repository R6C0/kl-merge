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
- DECISION: keep late110 and let 3f's queue (g) pick B/C/D; or say "cut" to switch to vault_e9 (UNKNOWN md5 in the folders; ask 3f).

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
- DECISION: leave Retomoto as is until 3f runs queue (b) (lead + WalkExclusive) and (c) (+ PointBlankToYou); then adopt the winning ini keys.

### Hasta, DM11B [page 3 F04]
- LIVE: ce42dcc9 + KLJoin 437c96ee.
- BEST PROVEN: with the live balance, ce42dcc9 gave you + all 7 out in L55/L56/L57 (per 09:40). Police build 3a186c93 (hasta_next, only 2 of 10
  plaza police started, KLJoin 437c96ee): L73 PASS, heli survived, you + all 7 out on visit 1 (per 14:40). The mechanism is a GUESS (per 12:18).
- STAGED, NOT RUN: rtcops DM11B 568e1786 (section 3). police2 131c8c2b (C:\kl_build_1018\hasta_police2\DM11B, KLJoin 437c96ee = live; builder
  --rest-late=120, 13d72a3b): the 2 ExitStreet_Left police start at the stair top as in 3a186c93, the other 8 start 120 s later instead of never
  (re/hasta_police.md e255313c: they were never started by design; the heli kill by SMG fire is a GUESS). Queued with 3f as (i).
- DECISION: swap in 3a186c93 (the plaza police that were passive are the cost), yes or no. Alternative to avoid the cost: none proven.

### A Walk in the Park II, DM06B [page 3 F02]
- LIVE: 7fef2733 (no KLJoin.ini in the live folder, checked).
- BEST PROVEN: the live zip. L68 (hook r, CrewRouteAlone): all 7 out on visit 1; L64 (balance only): all 7 via visit 2 (per 10:07, 09:40).
- STAGED, NOT RUN: loot6 tea-house case 3386b972 (tools/kl_fa_park_loot6.py 2f7e4e5b; loot was 166 of 165 flat from the stop, queued 3f (f));
  no-van-show d345bc5b (C:/kl_scratch/stage_park_nvs, hide/show A/B for the visit-1 cause, now moot since EscVisitFix is live); park_next KLJoin c99c4e11
  (two crew hops, with 7fef2733); rtcops 7bf368a7.
- RUN L81 (3f, 18:17): no-van-show d345bc5b + hook 1018s. PASS, 0 asserts, 416 s. The van's 1e4 was already set at state 1 without EscVisitFix, state 1->3->5 on visit 1;
  6 bots aboard (one traitor); the escort stayed with the scripted human 6 m out, the human did not board. Diagnostic only (EscVisitFix live): nothing to adopt.
- DECISION: adopt loot6 (3386b972) after 3f's run (f), yes or no. Nothing to do before that run.

### Hot Coffee II, DM01B [page 3 F03]
- LIVE: ea8cbc82 (walk-through doors; rollback = DM01B.replaced-1018doors, 01749906).
- BEST PROVEN: L70 (hook s + BoardReachFlat): rec 6 and traitor 4 escaped on visit 1, 3 dead, 2 never called (per 11:05); L71 with VanCallNear=40: both called stage-1/2 bots boarded on visit 1 (per 14:40).
  L52 with the 0.05 balance lost 6 of 7 (per 08:30); the 0.01 balance is live.
- STAGED, NOT RUN: rtcops DM01B 073dd57f (also 4 garage cops get rifles, per 14:11).
- DECISION: turn on [Bots] VanCallNear=40 (hook key, section 4), yes or no.

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
3 Park II: adopt loot6 3386b972 after run (f). 4 Vault: keep late110 or pick B/C/D after (g). 5 Retomoto: wait for queue (b)/(c).
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
