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

2026-10-26 ~01:40 - COVER on 10 maps + ARCADE DM01/03/06 + DM02 CO-OP solo Lift Door (untested in game) installed, stale 0.
C: filled mid-install (DM06/07/06B zips broken, restored + reinstalled); templates now guard free space (1e43fa9ad); bulk moved to D:.
Smoke rotation live_1026/rotate.py needs --hook out_all_1026a_test (SHIP hook ignores [Script]); DM01 PASS 01:19.

2026-10-26 ~00:10 - 9-INSTANCE LAN: L9b put 7 humans in one FA round (0 faults); player 9 froze 30 s across the host's start and stayed in the lobby.
Bench host now waits for all to connect (script op waitpeers, bbcf618da); L9c running. Lobby shows only 8 rows: agent building a 12-row FALobby ([Lobby] Rows12).

2026-10-25 ~23:55 - HOSTOPTS 1025b (out_hostopts_1025b SHIP 2f771cba / _test 004e2409, not run): host's F7/row now sets kls_online_set (LOAD follows); TEST logs the round clock ([rules+0x4c] etc.) at state 25/31 to find why a 10 min round lasts 83 s; [Lobby] RoundClockFix=1 optional GUESS write.

2026-10-25 ~23:30 - HOST OPTIONS (re/host_options.md; out_hostopts_1025a SHIP c3f32a80 / _test fc18e73a; overlay C:/kl_build_1024/hostopts_1025, none installed, none run):
klhostopt.c [HostOpts] Enable=0: F7 map set, F8 AI heisters, rows KLSHMap/KLSHOpt (Menu=1 overlay, +4 tags), host map set -> clients via Steam klx_opts + UDP 27413 (in memory only).
kllobbyopt.c: max/min edge fixed (SL7 time stuck at 5), NaN float read dropped, TEST logs the 25->31 round length.

2026-10-25 ~22:10 - HUD ONLINE / OLD HUD (out_hudonline_1025a, not installed, not run): [HUD] HideSrc=1 wraps ZFAPlayerListDisplay Render (slot 2 0x5e60f0, private heap vtable) and skips it while our HUD stands, so Tab/Alt+Tab cannot restore the old list; HideOnline=1 skips it online too (no online crew list exists: Sv/Cl rules records not decoded, re/hud_online.md). Rows hidestock/hidestockonl.

2026-10-25 ~22:10 - SOLO ONLINE HOST WORKS + INSTALLED: SOLO2 live (System Link, host alone, out_solo_1025b_test, SL5.ini) round 1 -> FAStatus/StatusMoney -> round 2, 0 faults.
Cause: slot 3 of the session manager vtable (0x61a410) is a session END request; 0x80ad60's tail asks for it (word 8) when < 2 humans; Solo=1 drops it for a lone FA host (kllobby.c, 70dbb3197).
Installed SHIP 2a88a86b + [Lobby] Solo=1, MinPlayers=1 (C:/kl_build_1024/solo_1025/install.py --undo; .before-1025solo). Lobby names set2 installed (rand collage live-checked, not left in).
Agents: Quick/Ranked BuildKey + host-server mode (out_server_1025a), Arcade HUD online + old HUD on Alt+Tab (out_hudonline_1025a), heist time to 10 min / more rounds (out_lobbyopts_1025a).

2026-10-25 ~21:26 - SYSTEM LINK + DEAD MEN MAPS: PASS (SL2, TEST out_escfar_1025a_test, script C:/kl_build_1024/online_1025/live/SL2.ini, [Lobby] MinPlayers=1 test-only).
Installed online_1025 (SHIP 05a47b0e, ini 4b2bcf1a: [Expansion] OnlineSet=2, [HUD] TrackerEscapeFar=1; .before-1025online, undo C:/kl_build_1024/online_1025/install.py --undo).
Route MainMenu DOWN DOWN RETURN > OnlineMenu DOWN RETURN > SystemLink DOWN DOWN RETURN (Create; SL1 pressed Join = SysUIErrorScreen) > SystemLinkCreate RETURN > FALobby;
host Ready alone -> 'LOAD F01: online=1 OnlineSet=2 -> page 2, rule DM01', level loaded, 0 asserts 0 faults. Grenade GSP1: PASS but no grenade carried (needs a pickup). QoL2 WatchDry sane.
Destruction-sound loudness (vehicle explosions, extinguishers, glass) as MP45: agent building C:/kl_build_1024/fxraw_1025 (not installed).

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
