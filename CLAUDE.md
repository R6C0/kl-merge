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
2026-11-06 ~15:45 - [c9] LAST CALL CHAIN 2c LIVE on DM05A (zip e10ea488, bots bffb9736): doors B01+A02 only (4 doors held the bots; with 2 they call the heli
at ~293 s), 2nd-floor spawn, EscCamera01 fixed eye CamPos01 + 5-pt NE climb spline. Grey outro = eye/heli outside every Roof .rmi box (Backdrop-only start room).
Bench lcchain2c1106d PASS, undo byte-exact, player rides out, outro draws the city (heli not in view after lift-off). Undo: C:\kl_build_1024\lcchain_2c_safedoors_live_1a97e186\install.py --undo.
Handed to 6b: re-stage pd2guns c+d+e on DM05A on top of e10ea488 and add the undo step to UNDO ALL 1105.bat.

2026-11-06 ~14:30 - [db] PERF: [Perf] OsdScanSlice, ScanMinFrames, ShopPoolBlock, BotScanSlice, CensusSlice, FillCensusSlice (85fdae39) all "(recommended on)", NOT installed (live 727a73bb).
Bench OSS_DD09_FCS_S3 (TEST a77e0546): SMOOTH on every seat, 0 hitches/stalls, host 29.9 fps, max frame 128 ms (CEN_S3 486), p95 87. Host klbf 13 ms windows 24/30 -> 0/18.
klsy spikes are the kit's [Sync] Probe=1, not players. Left: ~5 ms whole-table walks (no hitch). 9-seat hitches are the one PC (9 games), not the hook.
Ready to offer: SHIP out_fcs1106 e88a6093 + the 6 ini keys.

2026-11-06 ~18:30 - [shop] 1106t LIVE on the 9 stock DD maps: MG42 (item 42) + PAR (item 40) with their cards, like the DM maps. Bench PD2S_DD05 PASS (rows 18/22 = items 42/40 host+client). Entries = 1106s + 59 each. Backups hard-linked to the 1106s stage (install.py --link-from), stage dropped (--cleanup). UNDO ALL: new step 0t first.
DD09 1.8 fps host (db OSS_DD09_FCS_S3_PD2T, Havok MOPP sphere-tri 0xa4dec0/0x9e5590) A/B'd: _PD2S2 (1106s) and _PD2T2 (1106t, rebuilt stage zip bc5da13a, same CRCs) both 29.8+ fps -> one-off, NOT 1106t; 1106t stays live. db tracks it as an intermittent (NanDump=1).
2026-11-06 ~17:40 - [shop] PD2 guns on ALL 11 DM maps: DM05A got 1106c+d+e+f on c9's chain 2c (bench pd2a_1106 PASS, zip 14c8d9dd, Entries=54659); 1106f (MG42 item 42, PAR item 40 + cards) also on DM01B/DM03A/DM06B/DM11B. No free item id left. Backups on D: hard-linked (dedupe_backups). UNDO ALL order: 0s 0f 0a 0b 0 0c(c9 chain) 1..7.
2026-11-06 ~16:30 - [shop] PD2 GUNS on the 9 STOCK DD maps too: layer 1106s (19 guns) LIVE DD01-09, bench PD2S_DD05 PASS (items 62/63/35 in page II pool host+client); UNDO ALL step 0s first.
2026-11-06 ~15:45 - [shop] PD2 GUNS 1106b+c+d+e LIVE on 10 DM maps (not DM05A, held for c9): C45 (62), HRL-7 (50/51), R700 (49), GL40 x3 (52-54, GUESS 190->191), RPK on Minimi 45-48 (GUESS 62->63), Deagle 63.
DM02 benches PASS for each layer (2 seats round 2, 0 faults; 1106e: item 63 in the page II pool host+client). Backups OFF C: (D:\kl_stage\pd2guns_1106c/d/e/s_backup). C: 2.2 GB, D: 7.4 GB free.
DM05A: after c9's chain, re-stage c+d+e on top. UNDO ALL steps 0a (1106e), 0b (1106d), 0 (1106c) come first.
Earlier: KLPic pictures on 28 maps; Entries regression (pics +72 chunks) fixed live 361a1d3e. C: at 976 MB after 1106b: 9 DD *.before-1026loot8m moved to D:\kl_old_backups\dd_1106c (3.3 GB free).
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
