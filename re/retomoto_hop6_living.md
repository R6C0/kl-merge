# Retomoto (DM09): what hop 6 does while the human is alive (queue item (q))

2026-10-19, offline, read-only; second pass (every claim re-tested against code and logs, changes listed in section 5). Static reading of klhop.c, klcrew_rt.c, klescort.c, klmove.c, KLJoin 0b557e40 (staged at C:\kl_build_1018\rt_leaderless\DM09; NOT installed: the Dog Days KLExpansion\Maps\DM09\KLJoin.ini is the live b2bb6a2f and has no [CrewHop.6]), 3f's logs L94 / L95b / L96 and PT_DM09_*.ini.
Nothing was launched or edited. Tags: [code] file:line, [log] log + line, GUESS = not shown by code or log.
r = seconds after session state 0x19 (round clock start; [log] L95b 00:36:03.337).

## 1. When hop 6 fires (exactly)

The hop is [CrewHop.6]: From (2000, 20000, -500), Radius 6000, Height 1500, Wait 150, Stage 0, Player 0, Again 0, 7 To places = the [CrewJoin] Place list.

Per bot, in the order klhop.c tests them (klv_tick, klhop.c:385-488):
1. Level gate: hop on, a KLJoin.ini for this level, `s.state == KLB_ROUND`, `klb_level` (not a stock level), game thread, teleport routine known [code klhop.c:399-405].
2. Bot gate: record used, AI member (`flags & 1`), actor present, `status == 0` (in play; dead/aboard excluded), not yet done for this hop [code klhop.c:421-422].
3. Place: node OR +0x460 inside the circle (plan distance <= 6000 from (2000, -500) and |y - 20000| <= 1500) [code klhop.c:140, 425-426].
4. Timer: `since` is set on the first tick the bot is inside and is zeroed on any tick it is outside [code klhop.c:432-441]. Fires when `now - since >= 150 s` [code klhop.c:442].
5. Stage: `r->stage < h->stage` with Stage=0 is never true, so no stage is asked for [code klhop.c:442].
6. Human: `h->player` is 0, so `(h->player && !passed)` is false: the human is not consulted at all, alive, dead or fed [code klhop.c:442]. `kle_human()` is read at klhop.c:408 but only used for Player=1 hops.
7. Crew join: klhop.c never reads `klt_r.done`. A finished or pending crewjoin matters only through where the bots stand (step 3).
8. Rate and refusals: one bot per 0.5 s [code klhop.c:443]; `klt_refuse()` and "held as a human shield" (`actor+0x770`) skip a bot and retry [code klhop.c:444-449]; a landing place nobody stands on in the last 2 s is needed (`klv_free`) [code klhop.c:221-243, 460].
9. Action: ordinary hop: `klt_teleport` to To.n, then OrderTo (the soldier is ordered to the landing place), then the fast landing watch / Recheck [code klhop.c:468-486].

Real clock: `since` is not set at r0. In every log the first "is at From of hop 6" line (r0.2) is repeated 5.4-5.7 s later with a different node height (21404..21488) and +0x460 22776: during the blast / rappel the bots leave the height window, `since` is zeroed, and it restarts at about r5.7 [log L94 1462 and 1649; L95b 1474 and 1643; L96 1462 and 1645]. So **hop 6 fires at r = 155.7 s, seven bots over 3.5 s** (r155.7-159.2) [log L94 5639-5757: 29:39.7-29:43.0 against a 27:04.1 round start; L96 5785-5897].

Conditions on the human, summarised: none. Alive, dead, fed, in the tower, in the street: the same. Conditions on crewjoin: none, directly. Time: r ~156 s. Stage: any.

What makes it NOT fire for a bot: it left the circle for one tick (reset); it is dead or aboard; it was carried by the lift hops 2 (and 1/3 walk/GIVE UP) or by the crew join earlier (it stands at y 570, 19,430 below the circle).

## 2. Predictions with a living human

### (a) The human leads: EARLY join before ~r155 (L95b)

- Evidence: L95b, human alive, join at r123.3 (00:38:06.675). `grep -c "hop 6: at From for" L95b.log` = 0 [log]. Margin 32 s to r155.7.
- Mechanism: klt_move teleports all 7 to the street; they stand at y 570, so the circle test fails and `since` is zeroed [code klhop.c:432-435]. Hop 6 is inert for the rest of the round. It does not fight the early join and nothing else changes from the stock join.
- Race at r150-156: if the human's jump request arrives while hop 6 is already moving bots (3.5 s window), the landed bots are within 1500 of the entry [Near default, klcrew_rt.c:150; all seven To places are 320-1465 from Target (6272, 563, -6305): checked by hand] and `klt_move` skips them ("it is at the entry already", klcrew_rt.c:~190-200 in the loop). The rest are moved by the join. Harmless but not exact: the join's place counter n counts only the bots IT moves and starts at Place.1 [code klcrew_rt.c:233-243], while the hop's landing places are the same seven coordinates handed out by klv_free in its own order [code klhop.c:460]. So a bot the join moves can be put on a place a hop-landed bot already stands on (Place.n = To.n). klv_free keeps hop bots apart only from crew already standing there (klhop.c:221-243); the join does not ask. GUESS: two bots overlap for a moment and the game's body separation sorts it out; minor.
- So (a) is fine as long as the human gets to the join box before ~r150. Census join times are 107-261 s (re/retomoto_leaderless.md s3): the scripted human is at the fast end (123 s). A real player is likely past 156 s more often than not (GUESS: the census is rough).

### (b) The human is slow and still in the tower at r156

Predicted, from code (no log: L95b never reached it):
1. At r155.7-159.2 every in-play AI bot still inside the tower circle is teleported to the street, one per 0.5 s, in the middle of whatever it is doing (firefight, loot, the escort next to the human). Bots in the lift lobby are normally already gone (hop 2: Wait 1 s, Again 10 s; owner 2026-10-14 wanted exactly that), so hop 6 adds the ones that are NOT at the lift. The human is left alone in the tower with the guards.
2. Street arrival: in L94/L96 they reached stage 2 within 2-12 s of the carry [log re/retomoto_l94.md s0; adopt_list L94]. In L79 bots 3, 4, 6, 7 reached stage 2 in the street BEFORE the fed's jump (lines 1135668-1135880 against 1136442 in re/retomoto_leaderless.md s3), and in L95b they got stage 2 0.3-4.4 s after the join: stage 2 comes from boxes, not from the human's AITrigger. What the bots do afterwards without the 'AITrigger' (the jump list sends it only when the human jumps, klcrew_rt.c header s1) is NOT shown: L94/L96 had the jump (fed, FedSkip) 70-100 s earlier. GUESS: they walk their stage-2 chain towards the van area, as L79 describes ("advance on their own").
3. The escort bot (Escort=1, one bot, record 3 in L95b) is teleported with the others. klescort keeps ordering it "keep beside the human" every 2 s while the human is farther than 8 m [code klescort.c:719-728, header s2], and it has no floor test (the 195 m of height difference simply makes the bot "far"). The tower and street navigation meshes share no polygon (klcrew_rt.c header). GUESS: that bot is ordered to a point it cannot reach and stalls or jitters in the street. Its first 8 s are protected by OrderGap=8 (the hop's own order). It is released only when the human is dead or aboard. GUESS: its chain stands still behind it (klescort.c s2 (a)).
4. When the human finally jumps, the EARLY form runs `klt_move`: every in-play bot farther than 1500 from the entry is teleported back to a ring place (bots that already walked on, 40-100 s at ~3.5 m/s, are at 100+ m), the jump sends 'AITrigger'. So they pop back to the ring around him. This is the stock gather, but now it can drag back bots that had progressed. Not harmful; visible.
5. Loot: statues and the main room need the room cleared [CLAUDE.md owner design]; with the crew gone the human clears alone. GUESS: slower; the owner may read it as the bots abandoning him.

This is what the owner would dislike: bots vanishing from a living player's fight at a fixed time, and the escort left stranded. No log shows it yet (the (q) run is that log).

### (c) The human dies after r150

- Dies after r156 (hop 6 already fired, human in the tower): identical to L94/L96 from then on. The crew is in the street, the escort is released ("you are out of play", [log L94 1989]), the fed comes back in the lobby (2500, 19601, -615), the join box fires with FedSkip, nobody is moved [log L94 3680, L96 3695]. Crew progress is the L94/L96 one, minus their lost time: the carry happened at r156 anyway.
- Dies in r150-156: hop 6 still fires at r156 (it ignores the human); the escort was released at the death; same as above.
- Dies in the street after an early join (case (a)): bots stand at y 570, hop 6 never fires; the fed spawns in the tower lobby; FedSkip. Same as L94 after r155 except the crew was already down.
- So (c) needs no gate: the human's death changes nothing for hop 6, and that is the point of the hop.

## 3. Smallest change if (b) is disliked

Not implemented. A hop cannot see "the human is a fed" (`Player=1` waits for a LIVING human beyond the hop and never passes for a fed: kle_human needs player type 2 [code klescort.c:491-503, klhop.c:408-418]), so the human gate cannot be expressed in KLJoin text alone.

1. KLJoin-only, no code: raise `Wait` of [CrewHop.6] (clamped to 600 s [code klhop.c:163]). Wait=240 means the hop fires at r~246, past most census join times (107-261), so only rounds that are already late or stuck are touched; cost: a fed crew sits 90 s longer (L94: the carry was r155 and the van call r268; GUESS: the later carry costs the van). Staging: `python tools/kl_rt_joinini.py SRC OUT --leaderless-hop 240`. It is a dial, not a gate: a slow living human is still pre-empted, only later.
2. klmove.c-only: none. The teleport is klhop.c's (kltr_tp "hop"), and klmove is an order giver that cannot stop it or call it back.
3. Smallest real gate (klhop.c, 3 lines, GUESS that it compiles as written): new hop key `[CrewHop.6] NoHuman=1`, default 0 = unchanged.
```
struct klv_hop: add   int nohuman;
klv_source (next to the Player= line, klhop.c:166):  h->nohuman = GetPrivateProfileIntA(sec, "NoHuman", 0, file) != 0;
klv_tick, right after "if (!h->on) continue;" (klhop.c:413):
    if (h->nohuman && human) { memset(klv_r.since[hi], 0, sizeof klv_r.since[hi]); continue; }
```
   `human` is already `kle_human()` of this tick (klhop.c:411). Effect: while a living criminal human exists the hop does nothing and its timers stay at 0; when he is dead or a fed the timers start, so `Wait` then means "seconds after the human stopped being a living criminal" (the same meaning as the `FedAfter` proposal in retomoto_leaderless.md s5.2 without touching klcrew_rt.c). With it Wait could be much shorter than 150, e.g. 25 (GUESS, from L79 where the first walk order came 71 s after the fed). Cases: (a) unchanged, (b) hop 6 never pre-empts him (the lift hops still do), (c) fires 25 s after he turns fed. Unknowns: whether `kle_human` is already 0 during the 4.9 s death countdown (GUESS: yes or the timer simply restarts, harmless); and a human who leaves via the exit box never matters. It touches klhop.c, which is outside the two files the task named, so it is a proposal for 3f, not part of this note's scope.
4. Escort stranding (point 3 of (b)) is separate: klescort.c has no floor test. GUESS minimal fix: skip the "keep beside the human" order when |human y - bot y| > 1000 (klescort.c:719, before the kle_order call at 728; kle_dist is 3D, klescort.c:460). Only needed if (q) shows the stranded-escort stall.

## 4. Checks for 3f in (q)

Run the living human so he is still in the tower at r156 and alive:

**Script.** Take PT_DM09_lead.ini (scratchpad; god mode: CopToYou 0.001, PlayerHealth 10; human alive for the whole round; it produced L95b's r123 join) and change the single line `81=wait 5000` (the wait after `80=pos money-2-TM_MoneyStack_021`, the human standing at the boardroom loot (4750, -8), y ~20996, inside the circle) to `81=wait 110000`. CORRECTED timing: in L95b that wait ran r49.2 (script 78, 00:36:52.6) to r55.2 (script 82, 00:36:58.6), NOT r70-90 as the first version said, and the walk from the loot to the join box took 68 s (r55 to r123). So `wait 95000` (the first version's value) would make him leave the loot at r~145, BEFORE hop 6, and be walking at x ~3000-4000 (still tower, y 20996) at r156: alive and in the circle, but not standing. With 110000 he stands at the loot until r~160 (hop 6 fires r155.7-159.2 around him), the join comes at about r123+105 = r228, ~70 s after the hop. Both are valid for (b); 110000 makes the picture clean. AutoExit=864 and MaxRunMs 764000 still hold (L95b ran 366 s, +105 s = ~470 s; L97 ran 463 s). Name it PT_DM09_hop6live.ini. The KLJoin 0b557e40 must be INSTALLED for this run (the live DM09 ini is b2bb6a2f and has no hop 6: a run on it shows 0 hits and proves nothing); hook 1018zj/e5_1019a as for (l)/(s). Do NOT use PT_DM09_die*/fedvan_die (those turn the human fed at r22 and are cases (c)/L94). AutoExit=864 and MaxRunMs 764000 hold (L95b ran 366 s, +90 s). Do not use PT_DM09_pb / hg for this (same route and god mode as lead, but kept for other jobs; GUESS they are equivalent).
Optional second run for (c-late): PT_DM09_fedvan_die with its long wait moved to r>160 (GUESS: its death leg is the line `--die: he stands here until he is dead`, PT_DM09_die.ini line 439; the wait before it needs raising by 140 s). Only if the owner wants (c) confirmed; the code reading says it equals L94/L96.

**Greps** (L.log = the run's KLHook.log copy):
1. Hop 6 fired during the human's life, and when:
   `grep -n "hop 6: at From for" L.log` expect 7 lines, `at From for 150.x-153.x s`, wall time ~ r155.7-159.2 (round start = `grep -n "state 0x18 -> 0x19" L.log`). 0 lines would mean the bots left the circle (reset) or were already down.
2. The human was alive and in the tower then:
   `grep -n -E "YOU ARE A FED|you are out of play" L.log` expect NONE before the hop; `grep -n "escort: record .* re-pointed" L.log`: the "you are X m away at (x, y, z)" lines just before the hop should read y ~ 20990 (tower).
3. Teleports: `grep -n "otrace.*by=hop TELEPORT" L.log` (7 lines, `rec=` ids) and `grep -n "hop: bot .* hop 6 NOT carried" L.log` (skipped bots: shield, refuse).
4. Bots after the carry: `grep -n -E "heist stage 1 -> 2" L.log` per rec within ~12 s of the hop; `grep -n "bots: L1" L.log` (the per-record g<stage> and any "dead" status) from the hop to the join: how many died alone in the street before the human came.
5. Escort stranding: `grep -n "by=escort ORDER" L.log` AFTER the hop time. Orders every ~2 s to the escort record with `why=follow: keep beside the human` and a place at y ~20990 (the tower) while the bot stands at y 570 confirm point 3 of (b). `grep -n "escort: record .* re-pointed: you are" L.log` after the hop: "you are N m away" with N in the hundreds. Also `grep -n "otrace.*BLOCK-CHANGED\|stood .* s" L.log` for that record to see if it stands.
6. The snap-back when he comes: `grep -n "crewjoin:" L.log`: the "(EARLY)" line, then per bot either `NOT moved: it is at the entry already` (bots that stayed at the landing places) or `-> place n` with a `at (x, y, z)` far down the street (a bot that was pulled back). Count each; the `-> place` ones with was-positions beyond 15 m of (6272, 563, -6305) are the progress that got lost. `grep -c "7 moved"` would be wrong here: expect fewer than 7 moved.
7. Time gap: join time minus hop time (`crewjoin: ... pending` against the hop line). Expect ~70 s with wait 110000 (~40 s with 95000).
8. Nothing else misfires: `grep -c "GIVE UP" L.log` = 0 expected; asserts 0; `grep -n "hop 6" L.log | grep -v "At From\|at From\|From (2000"` should show nothing odd.
9. Compare with L95b (case a): `grep -c "hop 6: at From for" L95b.log` = 0.

**Verdict rule for (q):**
- If check 1 shows 7 hits while check 2 shows the human alive in the tower, the pre-emption is real (b). Decide by 5 and 6: escort stalled or many pulled back = propose the NoHuman gate (3.3). If the street crew is calm and the snap-back is mild, the owner decides whether "bots leave a living player at 2:36" is acceptable; the cheap fallback is Wait=240 (3.1).
- If 0 hits (the bots left the circle or died), report why from check 3.
- Always restore the live KLJoin.ini after (q): live is b2bb6a2f (checked at this reading: the Dog Days DM09 folder holds b2bb6a2f with 0 lines of [CrewHop.6]; 0b557e40 exists only in C:\kl_build_1018\rt_leaderless\DM09).

## 5. Second pass: what was refuted, what changed (2026-10-19)

Tested and HELD (no change): hop 6 never reads the human (klhop.c:442, h->player 0); `since` restarts at r~5.7 and the carry is r155.7-159.2 (L94 27:03.97 to 29:39.7 = 155.75 s; L96 43:17.64 to 45:53.31 = 155.67 s; the first 'is at From' line at r0.1 and the second at r5.7 in all three logs); 7 hits in L94 and L96, 0 in L95b (join r123.3); klhop.c never reads the crewjoin done flag; one bot per 0.5 s (waited 150.1 to 153.3 s, a 3.2 s span); all To places within Near=1500 per axis of Target (largest dz 1465 for To.7, dx 320); kle_human = type 2 only, so a fed never counts (klescort.c:491-503, kle_criminal 853-856); kle_dist is 3D, so the escort's 'far' test is met by the 195 m height gap; the escort is picked by 3D distance among live bots, so at r156 it is a tower bot (L95b: record 3, chosen 2.0 m from the human, follow orders at y 20996 to r112).

Changed:
1. WRONG: 'the same md5 (0b557e40) is installed in the Dog Days DM09 folder right now'. The Dog Days DM09 KLJoin.ini is b2bb6a2f and has no [CrewHop.6]; 0b557e40 is only the staged copy. (q) needs it installed. Header, section 4 and the restore note fixed.
2. WRONG: the script timing. In L95b the human stands at the loot r49-55, not r70-90; `wait 95000` makes him leave at r~145. Recommended `wait 110000` (leave r~160, join ~r228, ~70 s after the hop).
3. Sharpened: the race in (a) is a real place overlap by construction (klt_move's counter starts at Place.1 for the bots it moves; the hop's landings use the same seven coordinates), no longer only a guess. Still harmless/minor.
4. Line numbers corrected (kle_human at klhop.c:408 not 411; the since block 432-441; the Wait clamp 163; the Player= line 166; escort follow test 719-728 not 718; klescort kle_human 491-503).
5. klmove.c was checked as asked: it does nothing before the van (CrewRouteHold / CrewRouteFed run only at a van visit, klmove.c:1143-1181; the live [Bots] ini has CrewRouteHold=45, CrewRouteAlone=1). It neither causes nor prevents the pre-emption, so it does not enter (b) and cannot be the fix (3.2 stands).
6. Prediction (b) is unchanged and is still a code-only prediction: no log covers a living human at r156. The new log L97 (00:51-00:59, PT_DM09_fedvan_die_brl, hook e5_1019a) is the BoardReachLast run, not (q); its human joined by box 9 at 00:54:25 as a fed.
7. Caveat added to 3.3: kle_human also returns 0 when the human's node is flagged off (bit 10; aboard, possibly mid-teleport or in the lift; GUESS). With NoHuman a flicker only zeroes the timers, so the failure mode is a hop that fires late, never early.


## 6. NoHuman gate, compiled (2026-10-19)

Written in a COPY (`C:\Users\Henri\AppData\Local\Temp\claude\nohuman\klhook`); klhook/ in the repo is untouched (klhop.c is 3f's). Nothing launched, installed or committed. Default `NoHuman=0` leaves every path as before: the new test sits before the existing `Player` block and is false.

Patch (also `...\nohuman\klhop_nohuman.patch`, apply with `patch -p1` from the repo root):
```diff
@@ -117,7 +117,7 @@
-struct klv_hop { int on, nto, stage, player, walk; DWORD wait, ...
+struct klv_hop { int on, nto, stage, player, nohuman, walk; DWORD wait, ...
@@ -164,6 +164,7 @@  (klv_source, after the Player= line)
+        h->nohuman = GetPrivateProfileIntA(sec, "NoHuman", 0, file) != 0;       /* 2026-10-19: 1 = idle (timers 0) while a LIVING human exists */
@@ -411,6 +412,11 @@  (klv_tick, after "if (!h->on) continue;")
+        if (h->nohuman && human) {
+            static DWORD held_at; memset(klv_r.since[hi], 0, sizeof klv_r.since[hi]);
+            if (klv.log && now - held_at >= 30000) { held_at = now; klog("hop: hop %d held (NoHuman=1): a living human is in play", hi + 1); }
+            continue;
+        }
```
(the first line is abbreviated here; the .patch file has the full context.)

Differences from the 3.3 sketch: the field sits between `player` and `walk`; the reset zeroes the whole `since` row of the hop (as 3.3); one log line `hop: hop N held (NoHuman=1): a living human is in play`, at most once per 30 s (one static shared by all hops; GUESS fine, only hop 6 uses the key); silent under `Log=0`. The gate sits before the `Player` block, so with NoHuman=1 and Player=1 the passed-flag is not updated while a living human exists.

Compile: `klhook\build_auto.bat <out>` (the TEST build with klauto.c; VS2022 x86 cl via vcvarsall, as the out_e5_* folders): no errors, dinput8.dll linked. md5 **604e4dd4ec898dee97e3949658963851** at `...\nohuman\out\dinput8.dll` (not copied anywhere). GUESS: the live a57d9ce7 is also a TEST build; no out_* folder matched that hash, so a build of the unmodified klhop.c would be the fair byte comparison. Not run in the game.

KLJoin: `python tools/kl_rt_joinini.py C:\kl_build_1019\rt_hop6_living\src_b2bb6a2f C:\kl_build_1019\rt_hop6_living\DM09_nohuman --leaderless-hop 150 --leaderless-nohuman`
- New flag `--leaderless-nohuman` (needs `--leaderless-hop`, refused alone). REFUSED with `--leaderless-player`: Player=1 never passes for a fed, so the combination would hold the hop for a fed crew too and defeat the gate.
- Default output unchanged (re-run today): `--leaderless-hop 150` = 0b557e406f311803518b2727a4083878; with `--leaderless-player` = fcfc2a7c1defde22427160538884dfbb.
- Staged: `C:\kl_build_1019\rt_hop6_living\DM09_nohuman\KLJoin.ini` = **79f3c66ead3bcd1934f817188fc9aa56**. Diff vs 0b557e40: one added line, `NoHuman=1` after `Player=0` (line 655); nothing else.

Old hook with this KLJoin: klv_source calls GetPrivateProfileIntA only for the keys it knows (klhop.c:159-172); the section test `GetPrivateProfileStringA(sec, 0, ...)` needs only the section to exist. An unknown key is ignored, so the old hook behaves exactly like 0b557e40 (hop 6 fires at r~156 whatever the human does).

Test plan for 3f (hook = the nohuman build, KLJoin = DM09_nohuman; restore the live b2bb6a2f and hook afterwards):
1. Living slow human (L101 script, alive in the tower past r156). Expect `grep -c "hop 6: at From for" L.log` = 0 while they live; `grep "hop 6 held (NoHuman=1)"` about every 30 s; no `by=hop TELEPORT` before they leave the tower; the crew stays near them. After an early join the bots stand at y 570 and the hop is inert as before.
2. Fed human (L97 script, human turns fed at r~22). Expect the held line to stop once kle_human returns 0, the timers to start then, and with Wait=150 the 7 `hop 6: at From for 150.x s` lines 150 s after the fed state (r~172+, LATER than L97's r156; GUESS: a shorter Wait such as 25-60 may be wanted, re-stage with `--leaderless-hop 60 --leaderless-nohuman` if the van is missed). Compare with L97: 6 of 6 out.
3. Optional: a human who dies in the tower after r156: the 150 s starts at death (GUESS: kle_human is 0 during the death countdown, harmless).
4. Hops 1-5 (no NoHuman key) must fire exactly as in L97, same wait times.

### 6.1 Review (2026-10-19, adversarial, static)

Confirmed
- Gate logic against the real klv_tick (klhop.c 387-445): `human = kle_human(...)` is taken once per tick before the hop loop; kle_human is non-zero only for a local player object with type byte +0x273c == 2, readable feet and a node not flagged off (klescort.c:491-500). A fed human is type 3 and a dead one is not type 2 (GUESS for the death countdown), so `NoHuman=1` holds only while a LIVING human exists and releases for a fed or dead one.
- Resetting `since[hi][*]` cannot starve the hop: while held the row stays 0, and on the first tick after release the existing code sets `since = now` for every bot at From, so Wait counts from the release (fed/death), never from a stale value. A bot that already waited 150 s must wait the full Wait again after release: by design, and the reason to consider a shorter Wait for the fed case.
- A flicker of kle_human (node bit 10, mid-teleport) can only zero the timers (human=1 tick) or leave them running (human=0 tick); it never makes the hop fire early.
- Other callers of the hop path: klv_follow / klv_walks / the `after` records act only on bots already carried or on hops with WalkTo; CrewHop.6 has no WalkTo, so nothing bypasses the gate. A future NoHuman hop WITH WalkTo would bypass it (klv_walks is not gated): OPEN, not needed for hop 6.
- Default 0: `h->nohuman` is 0 from GetPrivateProfileIntA, the added `if` is false, no other line changed (copy vs repo klhop.c differs in exactly the 8 patch lines; the repo diff of the whole file shown by git is only line endings).
- Builder re-run: `--leaderless-hop 150` = 0b557e406f311803518b2727a4083878, with `--leaderless-player` = fcfc2a7c1defde22427160538884dfbb, with `--leaderless-nohuman` = 79f3c66ead3bcd1934f817188fc9aa56 (equals the staged DM09_nohuman/KLJoin.ini; one added line `NoHuman=1`). `--leaderless-nohuman` alone and with `--leaderless-player` both refuse (exit 1).
- Repo: git status shows nothing modified under klhook/ (only the untracked out_* folders that were already there).
- dll md5 604e4dd4ec898dee97e3949658963851 re-checked.

Fixed
- This doc had mixed CRLF/LF line endings (107 CR); normalised to LF like HEAD. No control characters otherwise; the new text uses they/them (it names no pronoun).

Open
- `static DWORD held_at` is shared by all hops (log throttle only; harmless).
- Not run in the game; the live hook a57d9ce7 build type (TEST or not) is still unmatched.
- Whether kle_human is 0 during a human's death countdown (a held hop would then release at the start of it) is unverified: test plan item 3.
