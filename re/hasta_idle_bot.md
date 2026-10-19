# Hasta L105: why crew rec 1 stayed at stage 0 / $0 and died

Run: 3f's L105, map DM11B in slot F04, zip a9ee0ebe (police4 S90), hook "zi", script PT_DM11B_p. Time 0 (round clock) = 02:02:51.3 as given; the hook's own `r=` in the otrace lines is 25.7 s ahead of that (r 237.2 = 02:06:22.77; r 31.2 = 02:02:56.77), and adopt_list's r values use the hook's scale. Below, `r` is the hook's scale only where it says `otrace r`; other `r` values (r 3.0, r 27..r 201, r 310.9) are on the 02:02:51.3 scale.
Log: `C:\Steam\...\Kane & Lynch 2 - Dog Days\KLHook.log` (read only), the L105 session starts at line 1535205 (`==== KLHook loaded` 02:01:41).
Earlier sessions of the same file were read for comparison (list below). `r` = seconds since 02:02:51.3.
Words: the human is "they"; bots are "it".

## Summary
- Rec 1 did not idle at its spawn and it was not blocked, refused, or out of loot. It was the ESCORT bot (klescort.c, `Escort=1`): the one AI heister that is
  chosen at the round start to stay beside the human and fight with them. By design an escort never loots (stage 0, $0) until the vehicle waits.
- The human script kept the human almost still in the plaza for about 170 s (r 27 .. r 201, at (37982, 830, 30401)), so rec 1 shadowed them there
  (`escort: record 1 re-pointed` every 5..10 s, all accepted). That is "stage 0, $0, never left the start" in the status line: it left the spawn, but only to the human's plaza.
- It was released only when the van waited (02:06:22.8, otrace r 237, state 3). It then had about 100 m of path to the boarding place while the van left 52 s later.
  It was 50 m short when the 8 late police (police4, first move at otrace r 229 = about 02:06:15, i.e. 8 s before the release) woke up on that very path. It fought, lost health 378 -> 214 over about 70 s (02:06:50 .. 02:08:00),
  and died at 02:08:02.2 (r 310.9), 13 s before the van came back for visit 2.
- Same role, same $0, same stage-0 start in every earlier Hasta run in this log. In all of them the escort boarded. L105 is the first with police on the escort's path
  (police4), so this is a one-off outcome of a recurring role, not an idle-bot bug.

## Evidence
### 1. Rec 1 is the escort (02:02:54.273, r 3.0)
`escort: record 1 (actor 625686c0, soldier 662d3c10) chosen: 4.5 m from you, 7 bot(s) could be; its place now (33950, 830, 30400); it is called when you are more than 8 m from it`

### 2. It follows the human, not the loot route
- `02:02:56.774 otrace: ... rec=1 by=escort ORDER (33924, 830, 30560) ... why=follow: keep beside the human`
- 76 `otrace` lines for rec=1; the escort orders run r 31 .. r 237. Typical: `02:04:07.772 escort: record 1 re-pointed: you are 8.1 m away at (37982, 830, 30401); place asked (38282, 830, 30403), the game set (38282, 830, 30403)`.
- Every order was accepted ("the game set" = place asked). No klmove "stood ... order is given again" line exists for rec 1 (all `move:` lines are records 2..7). No `reach:`, `hop:` or `near:` line names it before the release.
- The game's own chain keeps writing its route place into the same block (`by=GAME? BLOCK-CHANGED`, r 66 .. r 225, route moving (35554,830,30906) -> (26106,20,26232)). The hook wins again at the next order, as klescort.c section 2 says.
- Census, actor 625686c0 (the position only): 02:03:08 (33862,800,30039); 02:03:48 (39116,800,30413); 02:05:28 (37688,800,30341); 02:06:08 (37424,808,30236). Health 378 (one 8 hp nick at 02:03:08).
- The human stood still: `pos tick: me #8 (37982, 830, 30401)` from 02:03:18 to about 02:06:12.

### 3. Crew state over the round (`bots: L1 ...` lines)
- 02:02:51 all seven bots g0 $0. Bots 7, 3, 2, 5, 6, 4 went g1 at 02:03:14, :17, :18, :22, :28, :29 and started to earn from 02:03:19.
- 02:03:56 .. 02:06:09 recs 2..7 had $506k..$825k (rec 6 $75k). Rec 1 stayed `in-play g0 $0` in every line.
- 02:06:11.429 rec 4 g1 -> 3 (the van is called); `escprobe: state 1`, 02:06:22.632 state 3.
- 02:06:23 .. 02:06:41 recs 7, 4, 5, 3, 2, 6 aboard (rec 3 a TRAITOR, FOE line 02:06:28.492).
- 02:07:15.425 the van drives out (state 5): `near: visit 1: the vehicle leaves without you: 1 AI heister(s) still in play (record, metres from the boarding place: 1 42 m)`.
- 02:08:02.227 `bots: record 1 (bot): dead`. 02:08:16 the van is back (visit 2); the human boards 02:08:20.273.
- No grudge/FOE/botdown line for rec 1 (botdown lines are records 7 and 2 only).

### 4. The release came late and the walk was long
- 02:06:22.772 `escort: record 1 released (the vehicle waits, state 3): sent to the boarding place (28017, 133, 22643), the game set (28017, 20, 22643); it is at stage 0`
- 02:06:28.632 `crewhold: the vehicle would leave in 1.8 s and 2 of the crew walk (the nearest 46.0 m out): timer 1.8 -> 46.8 s (45.0 of 45.0 s used this visit)`
- 02:07:13.632 `crewhold: the vehicle leaves in 1.8 s: the 45.0 s of CrewRouteHold are used` -> van out 02:07:15.4.
- Rec 1 path (census): 02:06:28 (33253,800,28767); 02:06:48 (27185,20,28161); 02:06:56 (27214,20,27435) health 357; 02:07:08 (26170,24,26504) health 332; 02:07:28 (26355,20,26243) 284; 02:07:48 (27454,24,24653) 237; 02:08:00 (26387,24,24062) 214; 02:08:02.389 (26410,96,24368) 0.
  The boarding place is (28017, 20, 22643); the other six were already standing at (27400..27620, 0, 22900) at 02:06:56.

### 5. The 8 late police were on that path
- 02:06:56 / 02:07:08 census, living police of the late group (slots 20254, 20255, 20272, 20285, 20287, 20289) at (28904,26047), (29248,26693), (28453,25765), (26339,24074), (26102,24042), (26575,25755), i.e. 20..40 m from rec 1's line to the van.
- Police first move r 229 (adopt_list L105: stair top + 90.0 s; hook scale, about 02:06:15 clock, GUESS for the exact clock time). Rec 1's health starts to fall at the 02:06:50 census (376 -> 357 at 06:56 -> 332 at 07:06 -> 284 at 07:28 -> 237 at 07:48 -> 214 at 07:58), about 2.3 hp/s, while the six other bots at the van lose almost nothing.
- Police 20285 and 20287 go from alive (02:07:28) to 0 (02:07:48): rec 1 or the van group killed them. Survivors at 02:08:00: 20254, 20255, 20272 at (28904,26047), (29337,26608), (28453,25765).
- Last 2 s: 214 -> 0 between the 02:08:00.389 and 02:08:02.389 census, with y 24 -> 96. That is not the slow loss before it. GUESS: one large hit (the same instant-kill pattern as the Hot Coffee II L70/L71 one-shots, re/hotcoffee2_oneshot.md), or the three living police in close fire. No hit-kind line exists for crew, so this is not proven.

### 6. Comparison: other Hasta (F04 / DM11B) sessions in the same log
Escort and its fate, from `escort: ... chosen`, `... released`, `bots: record N (bot): aboard`:

| session start | escort | release -> aboard | final line for the escort |
|---|---|---|---|
| 07:37 | rec 3 | released 07:43:26 (stage 3 already) | all dead earlier, human dead (a bad run) |
| 08:29 | rec 5 | 08:34:26 -> rec 1 aboard 08:35:09 | rec 5 $0 TRAITOR status6 (aboard) |
| 08:36 | rec 1 | 08:41:45 -> 08:42:32 (47 s) | rec 1 $0 g3 status6 |
| 08:46 | rec 5 | 08:51:27 -> boarded | rec 5 $0 g3 |
| 13:57 | rec 1 | 14:01:42 -> 14:02:21 (39 s) | rec 1 $0 g3 status6 |
| 23:53 (L90) | rec 4 | 23:58:23 -> boarded | rec 4 $0 g3 |
| 01:15 (L100, police3) | rec 1 | 01:20:18 -> 01:20:56 (38 s) | rec 1 $0 g3 status6 |
| 02:01 (L105, police4 S90) | rec 1 | 02:06:22 -> never | rec 1 DEAD g0 $0 |

- Which of the 08:xx and 13:57 sessions is which of L57 / L73 / L9 was not checked (the log has clock times only). adopt_list puts L73 at "14:40", so the 13:57 session may be L73 (GUESS).
- L100 (same map, police3, same hook "zi"): rec 1 was also the escort at (37984, 830, 30400), also released at state 3 (01:20:18), walked the same route in 43 s with no police there
  (alive census 23 -> 17, no late police), boarded 01:20:56, and the van left at 01:21:11 (53 s after the release). So the margin was 15 s in L100 and negative in L105.
- The role makes the escort end with `$0` in every run's final `bots: L1` line (`$0` entries in the table above). Only the rec number changes.

## Cause
FACT (from the log lines above):
1. Rec 1 was the escort (klescort.c). Stage 0 / $0 until the van waits is the designed behaviour, not a missing order, a refused order, or a lost loot case.
2. Its orders were all accepted; no klmove gate (distance, height, restless, loot-skip) was involved; no botdown, no traitor line, no downed state.
3. It was released at otrace r 237 and walked about 100 m; the van left 52 s after the release, 13 s before it would have got there.
4. The late police group, started by police4 (first move r 229), stood on the escort's path to the van.
5. It died at 02:08:02.2, after the van had gone.

GUESS (not proven by any log line):
- That the police caused the slow health loss (the census shows no shooter). It matches in place and time but a hit log is missing.
- That the final 214 -> 0 was a single big hit (see section 5).
- That the escort would have boarded in time without the police: the same walk took 43 s in L100 and the van waited 53 s, so likely but unproven.
- That the escort's long stay with the scripted human (170 s still) is the same in a normal human run. Here the plaza hold of the script made the escort's start-of-walk 80 m away. A human who walks to the van reaches it at about the same time as the escort.

## Fix options
Nothing here was applied or run. Owners as stated in the task: klmove.c and builders = e5, other klhook files = 3f.
1. Ini only, hook klescort.c (3f): `EscortUntil=1` (key exists, klescort.c line 276) releases the escort when the van DRIVES IN (state 1 at 02:06:11.6) instead of when it waits (state 3 at 02:06:22.6).
   That is about 11 s more walking time for L105. Global for every map. Untested in the live game as far as this note found (GUESS: the code path for state 1 is described in the file header but I did not check a run).
2. klescort.c (3f): release the escort as soon as ANY crew record reaches stage 3 (the van is called), not at state 3; or release it when the van is called and the human is farther than N m from the van.
3. klescort.c / crewhold (3f): count the escort in the crewhold computation. The 02:06:28 line said "2 of the crew walk (the nearest 46.0 m out)" but the 45 s budget (CrewRouteHold) is a cap per visit, and it was used up while rec 1 was still 42 m out. A larger CrewRouteHold (e.g. 60) is ini-only but global (GUESS on a good value).
4. Builder, Hasta police (e5): move the S of police4 or the start position of the 3 late squads so they do not stand on the plaza-to-van line at otrace r 229..265. S=120 (police wake after the van leaves, 02:07:15) would spare the escort but also the other 7. Trade-off: the late police were added to pressure the human in the plaza hold (L100 showed none engaged). GUESS: S=60..70 would meet the main crew instead of the escort, but that was not tested.
5. klhop / KLJoin [CrewHop] (3f, ini of the map): a hop that teleports the escort from the plaza to near the van at the release. Existing mechanism (ADOPT 3 for Retomoto uses it); needs a list entry with coordinates for DM11B (the release point near (33346, 840, 28916) -> (27500, 20, 24000), GUESS values). Not a fix for the police though.
6. klmove.c (e5): no change needed for this case. A klmove rule would not help, because the escort is outside klmove's loot logic by design.
7. Test aid (3f): a hit-kind log for crew deaths (the Verify list in re/hotcoffee2_wholehit.md) to prove or kill the one-shot GUESS in section 5.

## Fix
Decision: no edit was made. The evidence (one run, L105, plus L100 as the control) puts the cause in klescort.c's release timing, which is 3f's file, and in the police squads' timing. It does not put it in klmove.c or the Hasta builders, so nothing was added there. Nothing was compiled; no out_e5_1019idle folder exists.
- klmove.c: no gate is justified. Its CrewRouteHold already ran (45 s) and the escort is outside its loot logic.
- tools/kl_fa_hasta*.py: moving the police S value is a design trade-off (see Fix options 4), not a defect with evidence. Not changed. GUESS: S=60..70 would help, untested.
- Proposal for 3f, ini-only first: run one Hasta test with `[Bots] EscortUntil=1` in the DM11B test ini (the key exists, default 3). That frees the escort about 11 s earlier (state 1 at 02:06:11.6 vs state 3 at 02:06:22.6). GUESS: 11 s is enough, since L100's walk took 43 s and L105's van left 52 s after release with the escort 42 m out.
- Proposal for 3f if that is not enough: a new opt-in key `EscortCalled` (default 0, so behaviour is unchanged), releasing the escort the moment any other crew record reaches stage 3. Exact patch for klhook/klescort.c, in kle_pass near line 1384:

      static int kle_called(const struct klb_snap *s, int skip) { int j; for (j = 0; j < KLB_NREC; j++) if (j != s->human && j != skip && s->r[j].stage >= 3) return 1; return 0; }   /* GUESS: the field names follow the surrounding code; check them before compiling */
      ...
      else if (s.veh >= (BYTE)kle.until && s.veh <= 5) rel = 2;
      else if (kle.stage && h->stage >= kle.stage) rel = 3;
      else if (kle.called && kle_called(&s, -1)) rel = 4;          /* new; kle.called = 0 leaves this branch dead */

  In init (near line 1482): `kle.called = GetPrivateProfileIntA("Bots", "EscortCalled", 0, klh_ini) == 1;` and add `int called;` to the kle struct. kle_release needs a `what` text for reason 4 ("a crew bot is called"). Caveat (GUESS): the escort would then leave the human's side early, so a human who is not heading to the van loses their guard. The record of the escort itself must be skipped (the `skip` argument; pass the rec of the first escort entry in a loop if kle.n > 1).
- Test aid for 3f: add the crew hit-kind log (re/hotcoffee2_wholehit.md Verify list) to the next Hasta run so the one-shot GUESS can be tested.
- Not proven: that the police killed the escort, and that an earlier release would have saved it. One run is not enough to adopt ADOPT 5 as harmful or harmless to the escort; the evidence says only that the margin was about 15 s in L100 and negative in L105.

## Verify
Skeptic pass, 2026-10-19 (e5), against the L105 session of KLHook.log (read only) and klhook/klescort.c.
Confirmed:
- Rec 1 = escort (chosen 02:02:54.273), 76 otrace lines for rec 1, escort orders from 02:02:56.774 to 02:06:22.772, released at state 3 (escprobe state 1 at 02:06:11.632, state 3 at 02:06:22.632), van out 02:07:15.4 (52.6 s after the release), death 02:08:02.227 (census health 214 -> 0 between 02:08:00.389 and 02:08:02.389), visit 2 state 1 at 02:08:05.6 and state 3 at 02:08:16.6.
- The human's `pos tick` is fixed at (37982, 830, 30401) until 02:06:10 and moves from 02:06:12 (about 172 s still).
- The 11 s gain of `EscortUntil=1` (state 1 at 06:11.632 vs release 06:22.772). Code: klescort.c line 1482 reads the key, default 3; line 1384 `s.veh >= kle.until && s.veh <= 5`.
- `EscortCalled` default 0: the new branch would be dead code. Git: no tracked file differs (`git diff` is empty); the only new file of this work is re/hasta_idle_bot.md (the other untracked entries, build/ and klhook/out_* folders, existed before). Field names `struct klb_snap` .human and .r[].stage, `KLB_NREC` match klbot.c lines 312..334. The existing `kle.stage` branch (line 1385) tests the HUMAN's stage, not other records, so the new branch is not a duplicate.
- Pronouns checked (human = they, bots = it). No control characters in the file.
Corrected:
- The hook-vs-clock offset was 5.7 s; it is 25.7 s (header fixed).
- Health loss began at the 02:06:50 census (376), not 02:07:08, and lasted about 70 s, not 50 s (summary and section 5 fixed). It began while the police census positions were static, 15..20 m (100 units = 1 m per klescort.c) from rec 1's line; the damage onset is therefore consistent with police fire but still not proven.
- Mixed `r` scales in the doc (see header note).
Unverified (GUESS):
- That police caused the damage; no hit log. That the 214 -> 0 step was one big hit.
- That police4's first move was at otrace r 229 (that is adopt_list's claim; the only r 229 line here is an escort follow order).
- That the van group, not rec 1, killed police 20285/20287.
- That EscortUntil=1 or EscortCalled would have saved rec 1: at 02:06:16 rec 1 was still near x 35976 at the plaza, so the earlier release adds walking but the path is longer than from the release point.
- The census mapping of the earlier sessions (07:37 .. 13:57) to L-numbers.
- The 08:xx escort-fate table rows were not re-read in this pass.
Verdict: cause statement stands (escort released late at the van-wait, long walk, police on the path), as a one-run inference; no code change and no default change.
