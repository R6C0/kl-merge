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
Full dated log: `re/open_work_log.md` (newest first).

2026-10-23 10:20 - cloud session (claude.ai, owner's "full perms, mods open items asap"): three offline pieces, all pushed, none run in the game.
- tools/run_harness_linux.sh --check-hook parses the hook again: MSVC __try/__except and __asm are stubbed by tools/lint/klhook_gcc_prep.py (it had stopped at the first SEH guard). SHIP + TEST 0 errors; all 7 harnesses + the 2 new ones pass under Wine. The check caught one real include-order error in the same hour.
- Head tags: [HUD] HeadMaxDist=N (metres, default 0 = off) + HeadFade (5): option D of re/hud_tags_sight.md - a tag past N m is not drawn, fades before it (alpha-in-colour GUESS as the outline's). klhud_tags_dist.h + klht_test.c (448 checks). Option A's premise corrected: 0x6e0b20 is the camera's bone anchor, NOT a raycast; the cast is Havok's hkWorldRayCaster (RTTI 0xd490ab), wrapper not found yet (section 5).
- Wardrobe: Kane's / Lynch's own bark set follows the body (bots_voice.md 6.5 hook side): klc_voice_own in klchar.c, klchar_voice.h + klcv_test.c (67 checks); opt-in by KLWardrobe.ini VoiceKane / VoiceLynch / Material, which the DATA side (kl_voice / kl_snd, needs level banks) has still to write.
- gfx branch: KLGfx 0.4 traces the first bridged frames + a Present watchdog (the 10-09 stall left no step in the log); in KL_PortTools\KLGfx, not installed.
- 10:06 OWNER DONE: Windows Firewall rules for kl2.exe added (netsh: in + out, allow, private + public). NOT yet verified by the game: the proof is the System Link page no longer saying "blocked by a firewall" - run the solo bench (re/netsmooth_solo.md section 6: TEST 1022e, H_host.ini then J_join.ini 45 s later) and read the hook's firewall line. If it still says blocked, the rule's program path must match exactly C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe (the game asks Windows Firewall through COM for that path, kl2 0x8945d0).
Owner: try HeadMaxDist=25 under HeadTags; the two scheduled check-ins (6 h cloud, 4 h PC-side) run on their own.
2026-10-22 00:30 - solo online bench: two kl2.exe side by side on this PC WORK; System Link stops at a firewall check (3f; run A1, owner asleep).
- TEST [Solo] (klhook/klsolo.c) + tools/kl_solo_test.py: mutex renamed, windowed D3D9, unfocused window kept running, per-instance files (env KLHOOK_DIR). Both reach MainMenu. Online = DOWN x2 RETURN, SystemLink = DOWN RETURN (window names, re/netsmooth_solo.md section 6).
- SystemLink -> "This game is blocked by a firewall" (0x8945d0 asks Windows Firewall via COM; profile Public). A hook stand-in and a firewall-rule script were both REFUSED by the permission classifier. inst1 crashed at kl2+0x43c785 idle on Achievements (open). Commit 547708589 (local).
- 01:36-03:55 controls + fixes: C2 (one process parked on Achievements) and D2 (two parked in MainMenu 4 min) 0 faults; H0dry: the inactive instance stopped its input (script stall) and 0x43c785 hit again on SysUIErrorScreen; [Solo] InputFix (klsolo.c 20ad71d2a, TEST 1022b) clears [[0xddb958]+0x94] and I1 proved it (both instances scripted to the firewall page, 0 faults). Host/join scripts ready: C:\kl_build_1019\live\solo\H_host.ini, J_join.ini (re/netsmooth_solo.md). Crash A/B (FpsCap/Vsync/Multithreaded) waits for an idle PC.
- 04:30-05:30 two-process crashes SOLVED: kl2 names its 7 render hand-off events (0x7ebbe0: DrawEnd, UpdateRenderState, ...), so two processes shared them and woke each other's threads (0x3c1dcb zero command, 0x43c785 null sprite). [Solo] Events=1 (klsolo.c, TEST 1022e) gives them per-process names: F0a-F0d 8/8 PASS vs 4 crashes in 6 before (FpsCap=60 did not help). klnudge: NudgeMs up to 24 h + first call held (1022c/d). Each start's SetCursorPos still resets the idle check (a wrap was REFUSED; runs wait 310 s instead).
- 05:50-06:45 System Link ports on one PC need no fix if the host creates before the client finds (9100 first-come; J_join.ini starts 45 s later). G0a/G0b: both instances in stock Bridge offline at once, sweep input, 4/4 PASS, 0 faults; G1a/G1b the same on Dead Men DM01 (F01) and DM09 (F06), 4/4 PASS; G2 the other 16 FA maps, 32/32 PASS: all 19 maps run in two processes at once.
- 12:47 end of the day-access window: firewall still blocks kl2.exe (0 rules), so NetSmooth online is untried. Ready: TEST 1022e, H_host.ini / J_join.ini, run command in re/netsmooth_solo.md section 6. 44 local commits unpushed.
Owner: allow kl2.exe in Windows Firewall (Allow an app, Private + Public); then the bench can host + join and NetSmooth gets its first online test.
2026-10-21 06:50 - 19-map sweep: shop swap + Rigid + NetSmooth together PASS on every map (3f; scripted, owner asleep).
- TEST 1020l (1020g source), owner's ini + [Shop] Swap=32:49 ReserveClips=2 + [Rigid] + [NetSmooth]: 10 Dead Men FA maps (DM01-03, 06, 09, 03A, 05A, 06B, 01B, 11B) and all 9 stock FA maps, two rounds each: clean exit, 0 asserts, 0 faults; every log shows the swap at load, the re-park at the round reset, Rigid on. Table: re/shop_more_guns.md "Map sweep".
- Still unproven by script: a BUY on a stock map, the Rigid feel, NetSmooth online. Commits are local (push refused).
Owner: reboot, then C:\kl_build_1019\hook_1020g\INSTALL hook 1020g.bat, shopswap, noblow; [Rigid] Enable=1 and try the feel; push rtp-schemas.
2026-10-23 (voice) - Dead Men voices for the eight Dead Men bodies, in every map folder incl. DD01..DD09 (branch feat/1023-voice, offline,
UNTESTED live). tools/kl_dmvoice.py grafts campaign clips as KLVoice/<Name>/<Event> + new KLTalk.ini (Kane+Lynch 13 own exchanges,
Dead Men pairs, pairs with Dog Days heisters); klhook/klvoice.c ([Voice] Enable=1) swaps the speech manager's per-voice entries
(data writes); [Talk] StockLevels=1. Who is whom and which clip fits is a GUESS: re/voice_1023.md; staged G:\kl_build_1023\voice_1023.
2026-10-23 05:40 - .LOC cap is 612,634 for EVERY language (kl_loc.LOC_CAP, strict check_cap; stock Russian is the only
proven size, live globals at offset 616,344). Our Russian/Japanese .LOC were 616-698 KB: kl_loc_fit swapped subtitles to
English, all 27 map zips re-installed (undo `<work>\build\locfit_1023_backup\UNDO locfit 1023.bat`; LOCFIT1 clean). Also:
Last Call civilians proven (CIVS3: still until approached, then flee); traitors rarer (Backstab 20, TraitorsMax 1).
05:50: police long guns on DM03 (12) and T01 (43) capped to accuracy 75 / aim 70 (`kl_map_ai pistol-row --row-classes
--row`), installed (undo `<work>\build\acc75_1023_backup\UNDO acc75 1023.bat`; ACC1b on DM03 clean, T01 not run live).
06:05: Heister-page portraits proven (PIC1/PIC2: all characters + 12 masks draw). Liveliness audit: nothing missing; engine-music maps
(DM09/03A/05A/06B) get no Payday 2 music by design (Force=1 is the owner's call).
2026-10-23 07:10 - Shop focus rows readable on all 27 maps (`kl_hud_menu.py shopbar`: dark FocusBar_short tile + ColorSet
White on the 8 rows over it; SHOP3b PASS on DM01). Undo `<work>\build\shopbar_1023_backup\UNDO shopbar 1023.bat`.
C: hit 0 bytes free mid-build: stage big zips on G:, not C:\kl_build_1019.
2026-10-23 07:50 - Shop on all 27 maps: focus rows readable (`kl_hud_menu.py shopbar`, SHOP3b) and cleaner card cut-outs on 11
rows (`kl_shop_cards.py recut --rows=`, SHOP4 PASS; Hawk Sawn-off keeps 2 stray fragments). Undo
`<work>\build\shopbar_1023_backup\UNDO shopbar 1023.bat`, then `<work>\build\shopcut3_1023_backup\UNDO shopcut 1023.bat`
(run the shopcut undo first). C: hit 0 bytes free mid-build: stage big zips on G:, not C:\kl_build_1019.
2026-10-23 09:45 - CamYaw (remote camera-yaw smoothing, [NetSmooth] CamYaw=1, default off) proven live in System Link (H8:
writes = restores = 1265, 0 faults) and merged (29ca1c8ef). The old join failures were key presses lost in a ~22 s stall after
CampaignMenu; scripted menus should use klauto `settle` + `tapuntil` (see H8_host.ini). Notes: re/netsmooth_camyaw.md.

2026-10-23 09:20 - Retomoto lift doors: the engine chain works (probe klprobe.c, LIFT9-11: box fires once, also for bots,
both proxies accept, 5 controllers each). "Shut doors" was the test route hitting the doorway frame. kl_doorfix on DM09 only;
kl_doorfix2 is a TEST tool (opens at the blast). CarWait 6 + CarFallback carry a slow human. Notes: re/retomoto_lift.md.

2026-10-23 08:20 - Shop on all 27 maps: readable focus rows (SHOP3b) + v2 card cut-outs on 12 rows with the edge rule (SHOP5 PASS,
Sawn-off clean). Undo newest first: `<work>\build\shopcut4_1023_undo\UNDO shopcut4 1023.bat` (copies from shopcut3_1023: keep it),
`shopcut3_1023_backup\UNDO shopcut 1023.bat`, `shopbar_1023_backup\UNDO shopbar 1023.bat`. Ambience pass 2 installed (DOOR1: Japanese
police radio on DM09; undo `<work>\build\ambience2_1023_backup\UNDO ambience2 1023.bat`). C:/G: are tight: stage big zips on G:.


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
