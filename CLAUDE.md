# KL Merge — agent brief

Goal: Kane & Lynch: Dead Men (DM, 2007) content, above all Fragile Alliance (FA): maps, weapons,
suits/masks, sounds, voice lines, playable inside Kane & Lynch 2: Dog Days (DD, 2010), PC Steam.
Must run easily. Long-term option: a clean-room reimplementation (hl2-rs style).

DEEP REFERENCE IS NOT LOADED. Before touching a format or crash site, read the matching file:
- `re/engine_facts.md`: engine facts, known kl2.exe sites, exact schemas (kl_rtp), research results
  (crash risks first), roadmap for a rewrite.
- `re/graft_formats.md`: graft direction details, format modules (kl_scene, kl_prmgraph, kl_texmat,
  kl_octree), SLOT id vs REF label (do not mix them).
- `re/open_work_log.md`: dated log, newest first (big: grep it).
- `re/retomoto_owner_log.md`: the owner's dated play feedback on the Retomoto build.
- `re/payday2_state.md`, `re/pd2_*.md`: Payday 2 crate format and readers.
- Others: `re/havok.md`, `re/pairings.md`, `re/characters.md`, `re/menus.md`, `re/netcode.md`,
  `re/wardrobe.md`, `re/shop_more_guns.md`, `re/netsmooth_solo.md`.

## Machine / paths (owner's Windows PC)
- DM: `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men` (exe `kaneandlynch.exe`)
- DD: `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days` (exe `kl2.exe`, 32-bit, no ASLR, base 0x400000)
- Work folder: `kl_port_check.workdir()` = `<DM>\KL_PortTools` (this repo's `tools/` is the source of truth).
  Live builds under `C:\kl_build_1019`. Outputs and build inputs live in the work folder.
- Originals replaced in DD are MOVED to `<DD>\KL_PortBackup\`, never deleted or overwritten.
  `tools/RESTORE Dog Days originals.bat` puts everything back.
- Never commit game files (see .gitignore). Keep the repo private. Assets stay on the owner's machine.

## Engine in five lines (details in re/engine_facts.md)
- Glacier 1 (same family as Hitman: Blood Money). Class type IDs are identical in both exes; 0x100000 = group.
- Level = `Scenes/Locations/<L>/<L>_Main.zip` (.gms .prp .TEX .prm .MAT .fxc .buf .oct .HVK .ANM .sgd
  .rmi .rmc .sgp .hrd .zgf .sup .LOC .SND). The exe hardcodes `Locations/Fxx/Fxx_Main.zip`, so a
  converted map replaces a slot (F01 = Subway) for testing.
- `tools/kl_rtp.py` gives every class's exact serialized field list from the exes; `kl_convert.py` is schema-driven.
- Two id spaces: SLOT id (.oct, .rmi, .rmc, list pool) changes when entities move; REF label (+0x30, gates, surface table) is stable.
- Never copy .ANM (header size differs). Use the slot's own .LOC. Patch01.zip overrides same-named archive members.

## Direction (owner, 2026-10-08): graft, not whole-level conversion
A compiled level holds the map AND the game systems (HUD, menus, cameras, weapons, players,
effects). Converting all of Dead Men's makes Dog Days' code run Dead Men's HUD and weapons, which
crashes. The owner wants Dead Men MAPS, voice lines and player models; Dog Days guns and sounds
reused; delivered like DLC (own folder, not overwriting a stock map). Keep Dog Days' systems
(`mainsceneincludes_multiplayer.zip`, CloneGroup_Effects, Heroes!), drop Dead Men's (`gamemenu.zip`,
`mainsceneincludes.zip`, CloneGroup_Effects). Subtree lists and cross-reference renumbering rules:
`re/graft_formats.md`.

## Unattended loop (owner's standing instruction)
Dog Days' Steam launch options are `-dx10 -o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120`:
a launch goes straight into the F01 slot and quits after 120 s.
- Test without a human: `python tools/kl_autotest.py` -> one `RESULT:` line (crash address, assert,
  clean exit, or hung). Triage a crash with `python debug/triage.py --keep`; pre-flight a build with `python debug/check.py`.
- Every off-game self-test in one go (tools/*_test.py + klhook/*_test.c, cl on Windows, gcc -m32 + klhook/test_shim elsewhere):
  `python tools/kl_tests.py` -> one `RESULT:` line, exit 1 on a FAIL. Run it before a build and before a push of klhook/ or tools/.
- Loop: integrate finished agent work (check it yourself first) -> build -> verify -> install into
  F01 -> autotest -> triage -> fix -> commit with what crashed and why -> push `rtp-schemas`.
- Keep background agents supplied with the next useful job; do not end a turn with nothing running
  while there is work that does not need the owner.
- NEVER: touch `KL_PortBackup` or stock files outside the F01 test slot, change the launch options,
  force-push, push to `main`, start later stages' game changes (research is fine).
- Pause live runs when the owner is playing (they block keyboard and mouse); work offline then.
- Leave a short dated note at the top of "Open work" AND of `re/open_work_log.md`; keep "Open work"
  here to about three notes, each 3 to 5 lines (older ones live only in the log).

## Pipeline
1. `tools/verify_levels.py` (from KL_PortTools): converts M01/M02/M03/M06 FA prp and checks every object vs DD. Must report `problems: 0`.
2. `kl_package.build('M01_FA_A','F01')` -> `build/install/...F01_Main.zip`; copy into DD (backup exists).
3. Test: DD -> Arcade Mode -> Subway -> Accept (keyboard only), or the autotest above.
4. Crash -> `<DD>\KLHook.log` + `KLHook_N.dmp` (KLHook from `klhook/`, installed as `<DD>\dinput8.dll`) and the game's own `kl2_490_crash_*.mdmp` -> `debug/triage.sh`, `debug/dump.py`, `debug/locate.py`.

## Open work
Full dated log: `re/open_work_log.md` (newest first). Shared week queue: `re/week_plan_1028.md`.
2026-11-08 ~09:00 - [dm03] DM03 COPS PASS staged, NOT installed: tools/kl_dm03cops_1108.py, stage C:/kl_build_1024/dm03cops_1108 (zip 2806a075, bots 1759a5fa, base 72f4c704; pinned live 802fd1f7 / 19adc63d). --parts carexit,garage,ramp,frontcops.
Cause of cops staying in cars PROVEN: 4 VehicleExitBehaviour nodes had no controller (restored from M03_FA_A; that DD then runs it is a GUESS). garage = 6 police, ramp = 5 police + 45 s Hunt into the garage (GUESS ramp = Ramp_01 beside the lot), frontcops = lot SWAT x3 + ArrivingCops_Squad_02 x2 -> police form. Census 33/27 -> 44/29.
Undo rehearsed byte-exact in scratch; bench needs ClientBuild*/ClientRewrite/ClientRingSync/AssertSoft lines (bench_cover_lines.txt). Not benched (owner playing).
2026-11-08 ~09:00 - [guns] GUNPUNCH staged, NOT installed: gunraw gave every gun the MP45's level/flat-top but not its shape (MP45 tail -20.5 dB, front +3 dB, 4% under 120 Hz; others tail -5..-15, front 0-2, 30-80% sub).
Stage C:\kl_build_1024\gunpunch_1108 (42 banks, install.py pins gunraw md5s, UNDO.bat, scratch round trip byte-exact; undo BEFORE gunraw_1107). Numbers + GUESS list: re/gunfeel_1108.md. Needs an owner A/B (preview pairs). Recoil/shake: none found, deferred.
2026-11-08 ~07:13 - [f0] MERGED 1108c LIVE: dll 246c643d (from 96ddcf7d = merged_1108b 3f8bc902 [d0 ShieldDriveIn] + db [Echo] RoomBoxes ear height, dormant), ini unchanged 6ddd03de.
Bench M1108C_DD05 PASS (TEST 09a02a2c, 2 seats, round 2, 0 asserts/faults/dumps, SHPH match). Kit C:\kl_build_1024\merged_1108c: dll only, 20 scratch checks, kl_tests 107/0.
Undo order: merged_1108c -> merged_1108b -> merged_1108 -> vanwait_1108 -> merged_1107 (each UNDO.bat in C:\kl_build_1024\<kit>; out of order refuses).
2026-11-08 ~07:05 - [d0] DM05A FOG WALL east of the roof pad hides the skyline: scene fog floats ruled out (skyfog1108: Far 80000 / FogFull 1.5, wall unchanged).
postneutral1108 (07:14, all 20 PostFilterBoxes -> DD neutral 33189) PASS 0 faults: wall unchanged, so the colour grade is ruled out too.
FOUND: the StreetGLOW curtain (REF 25478, vertex chunk 38553, MAT 891 SCREEN). streetglow1108 (vertex colours 0) PASS: wall gone, dark sky, black below the horizon.
glowfar1108 (alpha x 0.25 + Far 80000, stage C:\kl_build_1024\glowfar_1108) PASS: soft haze, towers clear. Staged, NOT installed (owner's taste call).
Skyline model can't be used: it sits behind the Distance shell, and moving it inside clips the map. citylights1108 (08:00, 9 dark 01d tower objects -> lit 01i, stage C:\kl_build_1024\citylights_1108) PASS 0 faults: right tower now a pale facade with a window grid. 08:20 INSTALLED (owner "install all"): DM05A zip 80b5547c, bots 1e02dbe5, base c009e5af, KLGuns 33432bb9; undo UNDO ALL 1105.bat step 0k; re-stage --base 80b5547c.
2026-11-08 ~05:46 - [f0] MERGED 1108 LIVE (SHIP 319aefc4, ini cd431998 -> 2f67d4bc = + [ShopPage] SetCheck=1) on top of d0s vanwait 19611c16: one dll from 9b74caf9 = fc SHPH set check + db [Echo] (dormant).
Bench M1108_DD05 PASS (TEST 337ecc4d, 2 seats, round 2, 0 asserts/faults/dumps, both seats "SHPH match" hash 4555f77f, no m10). Kit C:\kl_build_1024\merged_1108 (21 scratch checks, kl_tests 107/0, 3-lens review).
Undo order: merged_1108\UNDO.bat, then vanwait_1108\UNDO.bat, then merged_1107\UNDO.bat (out of order refuses, restores nothing).
2026-11-08 ~05:58 - [shop] SHPH set check LIVE via merged_1108 (dll 319aefc4, ini 2f67d4bc: SetCheck=1 warn only, SetCheckStrict absent = 0). Benches A-E all PASS, 0 faults (C:\kl_build_1024\shopset_1108, TEST ee6da004):
A warn mismatch, B strict client m10, C same set match, D off silent, E strict host vs a client with SetCheck=0 (old-build stand-in): host "unknown" -> host judge refuses page II buy with m10.
Untested: rejoin. Strict stays "(recommended off)" (it would refuse buys from every older-build player).
2026-11-08 ~04:15 - [d0] DM06B TRAFFIC LIVE: zip a6c0aef1 -> 7cee043d, bots ec42c5e4, base 171f7443, KLGuns 483f7450 (stage C:\kl_build_1024\dm06b_traffic_1108).
Bench dm06btraffic1108 run 3 PASS (0 faults, undo byte-exact): all 7 cars drawn, glow headlights fine (shots 08/12/20/28). Undo: UNDO ALL 1105.bat step 0d (top). Any DM06B re-stage: --base live 7cee043d.
skyline1108 (DM05A) bench PASS + undo byte-exact but no shot faces east: draw still unproven, stays staged NOT installed. Next: a look-east step in the kit.
2026-11-08 ~05:00 - [d0] VAN SHIELD LIVE: dll 502677ee -> 19611c16 (SHIP c7b7f1db = merged_1107 + db Echo fix (off) + [VanBlow] ShieldWhileWaiting), ini 6a17a145 -> cd431998 (+ [VanBlow] ShieldWhileWaiting=1 "(recommended on)").
Bench vanwait1108 (DD10 Flat Raid, TEST 76bd4a9c, nobody boards): PASS, 0 faults; shield on at state 4 for 54.5 s, health 9600/9600 (the game's scripted hits would have taken it to a tenth = the "always on fire" van), drove out at state 7 undamaged. No screenshots (ReShade bridge wrote none).
Kit C:\kl_build_1024\vanwait_1108 (install.py pins live dll+ini, scratch round trip byte-exact). Undo: its UNDO.bat, BEFORE merged_1107\UNDO.bat. Peers told (db oss_1106 ACCEPT list, 6b pd2r run.py).
2026-11-08 ~06:10 - [d0] RETOMOTO VAN: cause = cops hit it in the DRIVE-IN (state 2). [VanBlow] ShieldDriveIn (6f3df179) bench vanwait09h_1108 PASS: bus 3000/3000, no fire.
06:37 LIVE: merged_1108b SHIP dll 319aefc4 -> 3f8bc902, ini 2f67d4bc -> 6ddd03de (+ShieldDriveIn=1) after bench vanwait09m_1108 PASS (TEST 64701f02, installed line only, 3000/3000).
Undo: C:\kl_build_1024\merged_1108b\UNDO.bat FIRST, then merged_1108, vanwait_1108, merged_1107. HealFloor unproven, not shipped. Untested: boarding a drive-in-shielded van.

2026-11-08 ~04:30 - [sky] DM05A SKYLINE staged, NOT installed: Dead Men M05_A Buildings_MidRange (1 model, 156 tris, 5 mats, 6 tex) at (60000,1884,-4000) rot 0 east of the pad,
held by Backdrop .rmi box 59 only (GUESS: may not draw). Stage C:\kl_build_1024\skyline_1108 (zip cdd98872, bots 464adc61, base fdb74c80, KLGuns 33432bb9), pinned to live 651a7492; CHECK PASS,
route clearance 195 m (>= 98), outro-eye LOS 0 hits. tools/kl_skyline_1108.py; bench kit skyline1108 (validate OK, not run). Undo rehearsed byte-exact.
2026-11-08 ~03:30 - [shop] PD2 REBASE 1107r LIVE on all 20 maps + KLShopPage.ini 4bc8845a (13 pairs, HeliGuns=0, every PD2 gun on its own type). Benches PD2R_DM02 + PD2R_DD05 PASS
(C:\kl_build_1024\pd2r_1107, TEST 39e79011, 2 seats round 2, 0 asserts/faults/dumps). DM05A d65e8437 / bots 72e4c5b5 / base 388b40ec. Backups C:\kl_build_1024\pd2rebase_1107_backup.
Undo: UNDO ALL 1105.bat step 0r (a later layer adds its step above). Next: no-PD2 fallback set from Dead Men guns (tools/kl_fallback_guns.py, offline).

2026-11-08 ~03:00 - [f0] MERGED 1107 LIVE (SHIP 502677ee, ini 6a17a145, ovl df16480f, fx bc25a53f) after bench M1107_DD05 PASS (TEST 39e79011, 2 seats, round 2, 0 asserts/faults/dumps, shop rows ok). Undo: C:\kl_build_1024\merged_1107\UNDO.bat.
2026-11-07 - [f0] MERGED 1107 KIT (for c9): C:\kl_build_1024\merged_1107 = ONE dll from b628e16f (clean worktree):
lens + PickDefault + 6b ui_1107 + db [Echo] (0) + c9 [VanBlow] ShieldUntilBoarded (0). SHIP 502677ee, TEST 39e79011, overlay df16480f (= ui_1107's), fx bc25a53f.
install.py: refuses unless live dll e88a6093 / ovl d00527ff / fx 57663e0c; 15 ini lines (ini 97f8e972 -> 6a17a145); backups *.before-merged1107; undo byte-exact,
keeps in-game ini edits. 17 scratch checks + kl_tests 100/0 + 3-lens review. Supersedes ui_1107, lens_pick_1107_install, pick_1107_install.

2026-11-08 ~04:00 - [d0] DM05A LCARR 2h + CLUB MUSIC LIVE (zip 651a7492, bots ba98c0a6, base 1d89ea85) on top of 1107r: heli ROUTE_2H from the east, no building clip, club .SND boost.
Bench lcarr2h1108 PASS (TEST 39e79011, 0 faults/dumps, heli closest 1093, boarded at state 3, vehicle state 5 with player aboard, heli drawn in outro). Stage C:\kl_build_1024\arrival_1107\lcarr_2h_music_r.
Undo: UNDO ALL 1105.bat step 0h (above 0r). Any DM05A re-stage: --base live 651a7492. Next: vanwait1108 bench (DD10, [VanBlow] ShieldWhileWaiting, TEST 76bd4a9c) after db's [Echo] bench.

2026-11-06 ~14:30 - [db] PERF: [Perf] OsdScanSlice, ScanMinFrames, ShopPoolBlock, BotScanSlice, CensusSlice, FillCensusSlice (85fdae39) all "(recommended on)", NOT installed (live 727a73bb).
Bench OSS_DD09_FCS_S3 (TEST a77e0546): SMOOTH on every seat, 0 hitches/stalls, host 29.9 fps, max frame 128 ms (CEN_S3 486), p95 87. Host klbf 13 ms windows 24/30 -> 0/18.
klsy spikes are the kit's [Sync] Probe=1, not players. Left: ~5 ms whole-table walks (no hitch). 9-seat hitches are the one PC (9 games), not the hook.
Ready to offer: SHIP out_fcs1106 e88a6093 + the 6 ini keys.

2026-11-06 ~18:30 - [shop] 1106t LIVE on the 9 stock DD maps: MG42 (item 42) + PAR (item 40) with their cards, like the DM maps. Bench PD2S_DD05 PASS (rows 18/22 = items 42/40 host+client). Entries = 1106s + 59 each. Backups hard-linked to the 1106s stage (install.py --link-from), stage dropped (--cleanup). UNDO ALL: new step 0t first.
DD09 1.8 fps host (db OSS_DD09_FCS_S3_PD2T, Havok MOPP sphere-tri 0xa4dec0/0x9e5590) A/B'd: _PD2S2 (1106s) and _PD2T2 (1106t, rebuilt stage zip bc5da13a, same CRCs) both 29.8+ fps -> one-off, NOT 1106t; 1106t stays live. db tracks it as an intermittent (NanDump=1).
2026-11-06 ~17:40 - [shop] PD2 guns on ALL 11 DM maps: DM05A got 1106c+d+e+f on c9's chain 2c (bench pd2a_1106 PASS, zip 14c8d9dd, Entries=54659); 1106f (MG42 item 42, PAR item 40 + cards) also on DM01B/DM03A/DM06B/DM11B. No free item id left. Backups on D: hard-linked (dedupe_backups). UNDO ALL order: 0s 0f 0a 0b 0 0c(c9 chain) 1..7.
Undo: <work>/build/UNDO ALL 1105.bat (0: pd2guns_1106c, then 7 steps: pd2guns_1106b -> c9 glass_all_1106 -> entries -> pics -> buttons -> pd2guns -> DM05A lastcall_glass_1106) -> restore dll/ini. Zombie kl2.exe (0 threads) block tasklist checks: --skip-run-check (+ --root "<DD>" for buttons/pics).

## Owner's end goal (2026-10-09)
An EXPANSION: Dog Days keeps everything it has and gains all of Dead Men's content. Additive, never
replacement (testing in the F01 slot is temporary). In order:
1. Dead Men maps playable in Fragile Alliance / Arcade (graft), each in its own folder.
2. Dead Men voice lines and player models; Dog Days guns and sounds are reused.
3. Character / heister select, each character usable once per match.
4. Online, once the above is solid. Then: choose your police character for after you die.
5. Much later: assets from Payday 2.
Do not start a later stage before the owner says the earlier one works.
Every feature must also work on Dog Days' 9 stock FA maps and in private match.

Stage 1 wish: Retomoto Tower as a Fragile Alliance map, with its music. Dead Men never shipped an FA
version, so it is made from the campaign levels: M09_A (11,926 entities: offices, roof) and M09_B
(16,646: lobby, elevators). Music: 15 clips under Music/InHouse/Japan plus LevelSetup/Level/M09_A in
PC_Def.str. The FA layer (spawns, loot, escape, AI squads, bounds) is authored. BOTH parts in ONE
map (three-source graft: Dog Days systems + M09_A + M09_B). Owner's design, to be followed as given:
- Start: the heisters are OUTSIDE on the ledge just before the main window's glass (supersedes the
  earlier boardroom start); the explosion sound plays, the window blows (volatile blast like the
  Subway start: smoke, dust, debris, camera shake), then they go in. No rappel sequence. Guards
  unaware until the blast. Needs a standing ledge (invisible if no geometry), intact glass until the
  blast, a kill/bounds answer for stepping off.
- Part 1 (tower): fight through; loot comes from the STATUES (fitting prop, not a bag) and from the
  MAIN ROOM once everyone in it is dead. Loot props are briefcases; stacks must be reachable (move
  them nearer the outer ring).
- Part 2 (lobby/street): out the front entrance, down the road to a VAN, escape. Mood: the street
  shoot-out in Heat. I design how the two parts join. Its level music plays.
Owner's play feedback and open points: `re/retomoto_owner_log.md`.

## Payday 2 (owner, 2026-10-09)
Later wishes: Cloaker, Payday 2 maps and characters, first person. DECIDED for now: only the Payday 2
MASKS (WOLF FIRST), as further entries of the wardrobe's Mask row (`tools/kl_chars.py`,
`klhook/klchar.c`, `re/wardrobe.md`). Payday 2 is at `C:\Steam\steamapps\common\PAYDAY 2` (new
`.crate` format; readers `tools/pd2_crate.py`, `tools/pd2_model.py`; notes `re/payday2_state.md`).
Extracted data lives in `<work>\pd2\` only, never committed or shared.

## Working rules
- Verify before every install; commit each fix with a message saying what crashed and why.
- Don't guess silently: a guessed field mapping gets a code comment saying so.
- Patch C code and Windows paths with Edit/Write, not heredoc Python (it eats backslashes).
- A write into the game folder can be refused: give the owner a ready script instead.
- Do not name a PowerShell function rm/del/cp (aliases win).
- Scripted live runs need the game window in the foreground; monitor-off runs are 640x480 (leave settings alone).
- Owner dislikes the v82f HUD/shop; do not reinstall v82e/f without OK.
