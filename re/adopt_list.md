# Adopt list (2026-10-18, offline; e5 compiled from the logs and a read-only look at <DD> and C:\kl_build_1018)

Claims carry "per log note <date time>" (re/open_work_log.md) or "checked" (read in the files today). UNKNOWN = not in any note or file.
Nothing here was run in the game by this page. Zip ids are the first 8 hex of md5 of the zip. Hook/ini ids written by 3f in the log
(a57d9ce7, ccec94fb) are NOT md5 of the files now in <DD>: UNKNOWN which hash they are. Checked: live dinput8.dll md5 249ab16a =
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
- DECISION: keep late110 and let 3f's queue (g) pick B/C/D; or say "cut" to switch to vault_e9 (UNKNOWN md5 in the folders; ask 3f).

### Last Call, DM05A [page 3 F01]
- LIVE: df719d34 + KLJoin dfc29f60 (the "sa" build: EnterVehicle field 9 empty, per 07:10).
- BEST PROVEN: L78 "combined route": you + all 7 aboard, 0 dead (per 15:16). L51 full pass on the live zip (per 08:30); L75 you + 6 of 7 (per 14:40).
  The files for L78 are not named in any note. INFERRED from the folder name only: C:\kl_build_1018\lastcall_route_next\DM05A =
  zip 5b0a025b (df719d34 + escape-area text with the roof marker; L72 showed the text, per 14:40) + KLJoin ea0446c1 (hop Stage=1, L75).
  Confirm with 3f before relying on it.
- STAGED, NOT RUN: hopstage_next (zip df719d34 + KLJoin ea0446c1, same as L75 ini); roofgap_next (6903219f + ea0446c1; roof gap, BoardReachSent
  442a014d, queued L77 rerun after the 14:27 VOID); rtcops 6903219f ran as L76 (see section 3).
- DECISION: install lastcall_route_next (zip 5b0a025b + KLJoin ea0446c1) in place of df719d34 + dfc29f60, yes or no.

### Retomoto Tower, DM09 [page 2 F06]
- LIVE: bf1dfdb3 + KLJoin b2bb6a2f (= rt_join_next2).
- BEST PROVEN: no clean win to adopt. L79 (KLJoin e8c41f20 = rt_join_next4 margins + hop 6, hook 1018za): PASS but NO van; the human died on the
  atrium stair (-2007, 20300, -1330) at 82 s; the margins did not matter; 5 hop-3 walks were teleported by GIVE UP (per 15:35 and re/retomoto_fa.md s14).
  Vans came in only 7 of 72 logged sessions; none in 21 where the human died first (s14(1)).
- STAGED, NOT RUN: rt_join_next5 KLJoin 237f60f0 (kl_rt_joinini --giveup c1a43afc); rt_join_next3 d4dddd6d; --rescue-wedge d1258797 (UNKNOWN
  folder); hook keys in section 4. Also dm09_ini_1018 (KLJoin 3f9ce520 for DM09, 1cf31914 for the DM09RB* variants): purpose UNKNOWN in the notes.
- DECISION: leave Retomoto as is until 3f runs queue (b) (lead + WalkExclusive) and (c) (+ PointBlankToYou); then adopt the winning ini keys.

### Hasta, DM11B [page 3 F04]
- LIVE: ce42dcc9 + KLJoin 437c96ee.
- BEST PROVEN: with the live balance, ce42dcc9 gave you + all 7 out in L55/L56/L57 (per 09:40). Police build 3a186c93 (hasta_next, only 2 of 10
  plaza police started, KLJoin 437c96ee): L73 PASS, heli survived, you + all 7 out on visit 1 (per 14:40). The mechanism is a GUESS (per 12:18).
- STAGED, NOT RUN: rtcops DM11B 568e1786 (section 3).
- DECISION: swap in 3a186c93 (the plaza police that were passive are the cost), yes or no. Alternative to avoid the cost: none proven.

### A Walk in the Park II, DM06B [page 3 F02]
- LIVE: 7fef2733 (no KLJoin.ini in the live folder, checked).
- BEST PROVEN: the live zip. L68 (hook r, CrewRouteAlone): all 7 out on visit 1; L64 (balance only): all 7 via visit 2 (per 10:07, 09:40).
- STAGED, NOT RUN: loot6 tea-house case 3386b972 (tools/kl_fa_park_loot6.py 2f7e4e5b; loot was 166 of 165 flat from the stop, queued 3f (f));
  no-van-show d345bc5b (C:/kl_scratch/stage_park_nvs, hide/show A/B for the visit-1 cause, now moot since EscVisitFix is live); park_next KLJoin c99c4e11
  (two crew hops, with 7fef2733); rtcops 7bf368a7.
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
1 Last Call: install route build 5b0a025b + KLJoin ea0446c1 (confirm files with 3f). 2 Hasta: swap in police build 3a186c93.
3 Park II: adopt loot6 3386b972 after run (f). 4 Vault: keep late110 or pick B/C/D after (g). 5 Retomoto: wait for queue (b)/(c).
6 Hook keys: PointBlankToYou=20.0, WalkExclusive=1, VanCallNear=40 each yes/no. 7 Cops rtcops on five maps yes/no. 8 Push, disk, find.exe, replaced-*.
