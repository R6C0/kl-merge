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
- [ ] Inventory of every mod key and feature (klhook/*.c VK_/DIK reads, ini keys) -> re/keybinds.md, with clashes.
- [ ] One coherent key map (no clashes with stock DD binds), configurable in KLHook.ini [Keys].
- [ ] In-game "MOD CONTROLS" page in the shop (same carrier trick as the hire page) + a one-line hint in the buy menu caption.
- [ ] Toggles visible in Mod Options.
Owner: ce.

### T2 Maps work on both sides (host and client), all maps
- [ ] 2-seat bench per map (DD 9 stock FA + every DM/graft map), host and client both reach round 2, 0 faults.
- [ ] Fix per-map failures (DM11B int16, Retomoto lift, missing wardrobe models -> hired body stays stock).
Owner: c9 (benches A1I16/A1LIFT/A1SND/A1NET queued 10-28).
- 10-28 12:50 c9: hire gaps coded (814c17c60, NOT RUN): [CharOnline] StockHero=1 (hired DD heister body on stock maps from rules+0x208, GUESS online), [Hire] PagePrice=1 (price on name line). TEST dll C:\kl-merge\wt\wk-merge\klhook\out_week_1028b_test (fd63dd26, ce; holds e54ef0b47). Bench A1HIRE2 after the A1 queue: recipe re/shop_hire.md section 10.
- 10-28 13:30 c9: DM11B int16 shift merged (9ad0aa579, test ALL OK, NOT RUN): <work>\shift_1028\F04_Main_DM11S.zip (T=-12288,0,-16384; gameplay z min -32725). Bench A1SHIFT after A1HIRE2: install into F04 test slot with the int16 guard off for it; watch vans, spawn doors, shatter, bots, no falls online.
- Q28_DM06R done 10-28 ~12:00 (c9): PASS, DM06 online both seats IN ROUND on F04, 0 faults (Q27_DM06 failure did not repeat).
- Q28_DD09R done 10-28 ~12:05 (c9): PASS, DD09 (F09) online both seats IN ROUND, 0 faults, alive +302 s.
- A1LIFT done 10-28 12:20 (c9): PASS, FedRide=2 proven live (fed no ride while 7 bots above y 10000, rides once crew is down), 0 faults; door box re-arm not verified. Inis C:\kl_build_10241lift_1028.
- A1I16 done 10-28 11:45 (c9): PASS, DM11B online falls back to stock F04, DD01 control untouched, 0 faults.

### T3 AI heisters online = Arcade (behaviour + looting)
- 10-28 12:00 ce: research re/bots_online_arcade_1028.md (0x7f6850 'Arcade?' false online -> no tactics/records, trigger boxes ignore bots, Take is a raw +0x34 write); build OnlineTriggers + OnlineTacticsTake=2 in wt/wk-bots.
- [ ] Diff Arcade vs online bot code paths (BotFill, klcrew, klgrudge, klhop, klcardown, klcdying, klshield: 0 online refs).
- [ ] Online bots loot, carry, bank and escape like Arcade.
Owner: ce (10-28 11:40; 3f is another project).

### T4 AI heisters trigger cops / enemy spawns (not only the player)
- 10-28 12:00 ce: research re/bots_trigger_cops_1028.md (ZTriggerBox 0x42afd0/ZTriggerBox2 0x626f92 count team-2 only when 0x7f6850); same build as T3.
- [ ] Find what starts cop waves and spawn triggers (player-only checks), make bot actions count, Arcade and online.
Owner: ce (10-28 11:40).

### T5 Gun UI + sounds Arcade -> multiplayer (MP45 first)
- 10-28 12:00 ce: research re/gun_ui_sounds_1028.md (MP45 = item 1 row 7, banks/volumes same online; rows 13/16/32/35 baked names but Swap inert online; DM07/DD10 unbaked); build OnlineSwap + text fallback in wt/wk-gunui.
- [ ] Find why the MP45 (and other guns) show different icon/name/sound online vs Arcade; make online match Arcade on every map.
Owner: ce.

- 10-28 ~13:30 ce: WEEK MERGE built (wk-bots + wk-keys + wk-gunui on c9 e54ef0b47): SHIP klhook\out_week_1028 (4253cea2), TEST out_week_1028_test (d7aacdbd), mod options test PASS. All new keys default 0, NOT RUN live. Bench order: BOTS (OnlineTriggers=2 dry, then 1 + Take=2), KEYS, GUNUI.

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
