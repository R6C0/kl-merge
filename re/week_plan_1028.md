# Week plan 2026-10-28 .. ~11-04 (owner away, full access, never ask)

Owner's words (10-28 ~11:30): "implement those features of the gamemodes into reasonable keybinds and also shops / UIs so people
can see what they can do so it isnt just a secret feature, make sure the maps all work on both sides and the ai heisters work on
the respected maps and also make them the same as they are in arcade with behaviour and looting since they dont do much in online
and also trigger the cops or enemies to also get spawned or whatever from the ai heisters as well instead of just the player and
sort the maps gun ui, sounds to match mp45 from arcade to multiplayer overhaul everything i better see big progress".
The owner reads the VS Code chat and their Claude app chats only. Every feature stays an ini toggle "(recommended on/off)".

This file is the shared queue for every session: the live chats (kl-merge-ce, kl-merge-c9, henri-3f) and the scheduled
headless resumes (`tools/kl_week_resume.ps1`, Windows task "KLMerge Resume"). Claim a track by writing your name and the time
next to it; write the result (commit, bench tag, PASS/FAIL) under it. Newest status first inside each track.

## Tracks

### T1 Discoverability: keybinds + shop/UI pages (owner: "not a secret feature")
- 10-28 12:00 ce: research re/keybinds_ui_1028.md (F7/F8/F10 clash with ReShade, CopSquad F/G vs melee/grenade); build wf_ce299754 in wt/wk-keys.
Owner wants every mod feature reachable on a sensible key and shown on screen (shop pages, hint lines, a controls page).
- [x] Inventory of every mod key and feature -> re/keybinds_ui_1028.md, with clashes.
- [x] One coherent key map, [Keys] Map=1 (WK2 live 10-28: 9 keyed features, 0 clashes incl. ReShade.ini).
- [x] In-game "MOD CONTROLS" page in the shop + hint (WK2 live: "MOD CONTROLS page on"; F2 cycles stock -> page II -> hire -> controls). Owner still to look at it.
- [x] Toggles visible in Mod Options (tools/kl_mod_options.py, 10-28 13:55 ce 6bc15209f: 14 week rows added, OnlineTriggers/Keys Map/Hints "(recommended on)", rest off).
Owner: ce.

### T2 Maps work on both sides (host and client), all maps
- 10-28 14:55 c9: A1HIRE3 PASS (ce ran it): stock-map hire body via rules+0x208 CONFIRMED online, money 100000 -> 90000 read back on host and client. A1SHIFT4 running 14:52, A1NET2 next.
- 10-28 14:35 c9: A1NET2 staged (ini-only: both seats walk W/A/D + yaw ~170 s; A1NET1 had no client movement). c9 game queue after ce's 5 benches + A1HIRE3 (ce runs it): A1SHIFT4, A1NET2 (queue.txt sections 4, 5).
- 10-28 14:20 c9: A1SHIFT3 div0 root cause = the shift used the STOCK F04 zip, not DM11B (sound records mismatched). Fixed + rebuilt from the real DM11B (984463891, Heroes moved too). A1SHIFT4 staged after ce's queue + A1HIRE3.
- 10-28 14:00 c9: A1TALK_DM01 + A1TALK_DD04 PASS (crew banter plays online on both seats, host 4 lines / client 3, 0 faults; TEST out_c9talk_1028_test 89117d7e). A1SHIFT run 1 invalid (botgate loaded the unshifted bots.zip -> DM11S bots companion 6c3f59315). A1SHIFT2 FAIL load crash kl2+0x1c6901 = stale .prm type-7 octree refs after the .oct shrank (fixed 723e78443). A1SHIFT3 FAIL: both seats in round, then c0000094 divide by zero at kl2+0x4668b (host 143 s, client 99 s); triage workflow wkthgj0ax (worktree C:\kl_wt\div0). DM11B + ship dll f520f5d1 restored; game handed to ce.
- 10-28 13:35 c9 benches (--owner-away, 0 faults each): A1NET PARTIAL (A1NET1/A1NET0 both seats in round, clean; netsmooth/tune criteria not met: only the host walks, needs a client input script). A1HIRE2 PARTIAL (out_week_1028f_test, DD06: paid hire works online, price on the name line, round-2 bodies J.C./Tommy worn; NOT proven: money after the hire read back, and no "charonline: stock hero" line, so StockHero=1 unconfirmed). A1SHIFT running 13:36 (ce paused its queue), A1TALK next.
- 10-28 12:45 c9 A1SND PARTIAL PASS: music/ambience/stinger Loud/voice lines run online on DM01 + DD04 (0 faults); crew banter (kltalk) still silent online. See open_work_log.
- [ ] 2-seat bench per map (DD 9 stock FA + every DM/graft map), host and client both reach round 2, 0 faults.
- [ ] Fix per-map failures (DM11B int16, Retomoto lift, missing wardrobe models -> hired body stays stock).
Owner: c9 (benches A1I16/A1LIFT/A1SND/A1NET queued 10-28).
- 10-28 12:45 c9 bench results (TEST arcade1to1_1027 f8ae48a1, --owner-away): A1I16 PASS (DM11B online falls back via int16guard, both seats in round; DD01 control ok), Q28_DM06R PASS, Q28_DD09R PASS (both seats to +302 s), A1LIFT PASS (Retomoto Arcade, 7 bots, 0 faults; lift box re-arm not visually checked), A1SND PARTIAL (DM01 + DD04 both seats in round, 0 faults). A1NET held (game handed to ce WK1/WK2 at 12:42). After ce: A1NET, A1HIRE2, A1SHIFT.
- 10-28 13:10 c9: online crew banter silent (A1SND) = kltalk klk_who_any refused online rounds without OnlineTraits/OnlineCrew, before any log line. Fix [Voice] OnlineTalk=1 (wide who incl. other humans, dead/escaped skipped, gate logs 'talk: gate N held'), reviewed, merged (a27db09ca), NOT RUN. TEST C:\kl_wt\talk\klhook\out_c9talk_1028_test (89117d7e). Bench A1TALK after A1SHIFT: A1SND inis + OnlineTalk=1, KLTalk.ini beside the archive, DD04 also [Talk] StockLevels=1.
- 10-28 12:50 c9: hire gaps coded (814c17c60, NOT RUN): [CharOnline] StockHero=1 (hired DD heister body on stock maps from rules+0x208, GUESS online), [Hire] PagePrice=1 (price on name line). TEST dll C:\kl-merge\wt\wk-merge\klhook\out_week_1028c_test (08c00611, ce; holds e54ef0b47). Bench A1HIRE2 after the A1 queue: recipe re/shop_hire.md section 10.
- 10-28 13:30 c9: DM11B int16 shift merged (9ad0aa579, test ALL OK, NOT RUN): <work>\shift_1028\F04_Main_DM11S.zip (T=-12288,0,-16384; gameplay z min -32725). Bench A1SHIFT after A1HIRE2: install into F04 test slot with the int16 guard off for it; watch vans, spawn doors, shatter, bots, no falls online.
- Q28_DM06R done 10-28 ~12:00 (c9): PASS, DM06 online both seats IN ROUND on F04, 0 faults (Q27_DM06 failure did not repeat).
- Q28_DD09R done 10-28 ~12:05 (c9): PASS, DD09 (F09) online both seats IN ROUND, 0 faults, alive +302 s.
- A1LIFT done 10-28 12:20 (c9): PASS, FedRide=2 proven live (fed no ride while 7 bots above y 10000, rides once crew is down), 0 faults; door box re-arm not verified. Inis C:\kl_build_10241lift_1028.
- A1I16 done 10-28 11:45 (c9): PASS, DM11B online falls back to stock F04, DD01 control untouched, 0 faults.

### T3 AI heisters online = Arcade (behaviour + looting)
- 10-28 14:40 ce benches (out_week_1028i_test, 0 faults every seat): WKBC F06 7/7 aboard (6 BOARDED + 1 boardall), ledger $1.9M, but the host's box tele came 2 s before the van left -> no human escape -> OnlineBankCredit NOT exercised; rerun WKBC2 (tele every 3 s from +50 s, C:\kl_build_1024\week_1028\WKBC2_*.ini). BP_DD08 6/7 boarded (baseline 4/7). BP_DD04 4/7 (baseline 6/7; 1 died): bot 4 logged "stopped 5 m from the exit" while ~60 m away, van called late -> agent fixing in wt/wk-dd04. AM_DM09 PASS both seats: hop + cardown online host-round paths entered (no carry seen; cardown Dry). BP joins FAIL = script only (host quits before 0x20).
- 10-28 12:00 ce: research re/bots_online_arcade_1028.md (0x7f6850 'Arcade?' false online -> no tactics/records, trigger boxes ignore bots, Take is a raw +0x34 write); build OnlineTriggers + OnlineTacticsTake=2 in wt/wk-bots.
- [x] Diff Arcade vs online bot code paths -> re/arcade_mods_online_1028.md (10-28 ce): klhop + klcardown got host-only online paths (review-fixed, merged 88706e681, NOT RUN; bench AM_DM09); klcrew/klgrudge/klshield/klescort/klcopsquad/klfedkit need crew records or a client carrier (open).
- [ ] Online bots loot, carry, bank and escape like Arcade. WK2 live 10-28 F06: 7 bots GRABBED via the game's 0x4e3f40, van called, 5/7 BOARDED, $1.35M on the bank ledger; paying the ledger to the score (OnlineBankCredit, data-only) = bench WKBC; 2 bots strayed (BP benches).
Owner: ce (10-28 11:40; 3f is another project).

### T4 AI heisters trigger cops / enemy spawns (not only the player)
- 10-28 12:00 ce: research re/bots_trigger_cops_1028.md (ZTriggerBox 0x42afd0/ZTriggerBox2 0x626f92 count team-2 only when 0x7f6850); same build as T3.
- [x] Find what starts cop waves and spawn triggers, make bot actions count online: [BotFill] OnlineTriggers=1 PROVEN live WK2 10-28 (F06: 3 ZTriggerBox FIREs via 0x6ae730 from bots, 0 faults). Arcade already counts team 2.
Owner: ce (10-28 11:40).

### T5 Gun UI + sounds Arcade -> multiplayer (MP45 first)
- 10-28 14:40 ce SHOT2D (F06, 2 seats, 0 faults, both IN ROUND): the RemoteShot2D vtable route installed live on both seats ("sound system now on the private vtable (slot 74)"); script FAIL = shop timer ran out after a lost Enter tap (not a game fault). Loudness by ear still open (owner).
- 10-28 13:10 ce: RemoteShot2D reworked as a SHIP-safe sound-system vtable route ([Sound] RemoteShot2D=1, RemoteShot2DRoute 0 auto/1 code/2 vtable; private copy of vtable 0xb9ae14, slot 74 wrapped), review fix 756fde98a (re-point a sound system rebuilt at the same address). In out_week_1028h(_test). Bench SHOT2D queued (F06, both seats, NOT RUN).
- 10-28 12:00 ce: research re/gun_ui_sounds_1028.md (MP45 = item 1 row 7, banks/volumes same online; rows 13/16/32/35 baked names but Swap inert online; DM07/DD10 unbaked); build OnlineSwap + text fallback in wt/wk-gunui.
- 10-28 12:45 ce CLAIMS remote shot loudness (section 3 of re/gun_ui_sounds_1028.md): static slot trace + [Sound] toggle in wt/wk-sound (branch wk-sound-1028).
- [ ] Find why the MP45 (and other guns) show different icon/name/sound online vs Arcade; make online match Arcade on every map.
Owner: ce.

- 10-28 ~13:10 ce: WK1 (dry) + WK2 (live, F06, 2 seats, out_week_1028c_test) PASS: in round, faults 0 both seats; proof lines shopPage, OnlineEarlyMake, keys (9 features, 0 clashes, MOD CONTROLS page), osw early make 4 pairs, trig, bank. The bankcredit code patch at 0x681103 was refused (integrity range), so it was REWRITTEN data-only: credit from the tick via 0x5a18c0 once a human seat has escaped. RULE: SHIP refuses every .text patch, so shipped features must be data/vtable/tick only. Botpath merged (c972d762c). New dlls out_week_1028g (SHIP 18adbf1b / TEST 44fb347f; 1028f + OnlineBoardTeleport under __try after the review workflow). Queued after c9 (~1.5 h): WKBC bankcredit bench, BP_DD08/DD04/DD05 botpath benches; shot2d agent reworking RemoteShot2D as a sound-dll vtable wrapper.

- 10-28 ~13:30 ce: WEEK MERGE built (wk-bots + wk-keys + wk-gunui on c9 e54ef0b47): SHIP klhook\out_week_1028 (4253cea2), TEST out_week_1028_test (d7aacdbd), mod options test PASS. All new keys default 0, NOT RUN live. Bench order: BOTS (OnlineTriggers=2 dry, then 1 + Take=2), KEYS, GUNUI.

- 10-28 ~12:40 ce: merged + pushed 05cf39e22: [Shop] OnlineSwap (full online swap, reviewed: ours parked until linked), [BotFill] OnlineBank/OnlineBoardAll/OnlineBankCredit (bot loot into the REAL online score via 0x5a18c0 at the round-end call 0x681103, reviewed), OnlineTriggersExtra (stock cop waves use ZTriggerBox = already covered). Bench dll out_week_1028c_test (08c00611); WK1 (all dry) + WK2 (live) staged in C:\kl_build_1024\week_1028 (RUN_week_1028.txt), after c9's queue. All default 0, NOT RUN.

### T6 Ops
- [x] Scheduled resume: Windows task "KLMerge Resume" every 2 h until 2026-11-04 runs tools/kl_week_resume.ps1 (skips while
  any session transcript is fresh; log in <work>\week_resume\).
- [x] AnyDesk + "leave Claude running" guide for the owner's Thursday setup: re/anydesk_setup.md (c9 10-28 11:50; sleep already Never, AnyDesk not installed: owner sets the password).
- [x] Owner status page (private): https://claude.ai/artifact/Pp48g1cQgREDE3AsHPqxTa - c9 republishes; send c9 a line per track.
- [x] Routines trig_01FKzQ (Desktop, 4 h) and trig_014C2 (cloud, 6 h) point at this file (c9).
- Headless check 10-28 11:35: `claude -p --permission-mode auto` answers on this PC (effort capped to medium).

## Rules for every session (short)
Never KL_PortBackup, never push main or force-push, commit + push rtp-schemas with what crashed and why, backups (keep 3),
live runs only when the owner is idle 5 min, a game-folder write that is refused -> leave a bat. Notes: CLAUDE.md Open work +
re/open_work_log.md (newest first).
