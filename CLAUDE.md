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
2026-11-11 ~01:30 - [d0, offline] DD10 VAN FIX STAGED, NOT installed/benched (owner: 'van spawns in and blows up, supposed to be a cutscene drive'): tools/kl_dd10_vanfix_1111.py (2a86e8c6), kit C:/kl_build_1024/dd10vanfix_1111 (pins live e822d75d/f16b4bc1/0a1c00d0 -> zip 0dc61bdf, bots 67753c78, base 4da0052a).
KillBox 21957 (only FA_DieFromSelf source in F07) shrunk + sunk 4 m, 3 RelayAnimatedVehicleHit (21943/21960/21961) cut = no crash legs/explosion. First-spawn death cause (approach box east edge x 9100) still a GUESS. CHECK PASS, undo byte-exact. Waits for owner 'install van' or 'go' (bench: first spawn x3, later spawn, round 2, call+board). After install: 81 re-packs.
2026-11-11 ~00:15 - [d0] MERGED 1110h INSTALLED on owner "yes all good install all" (not benched): dll 6dcae9e6 -> 4485802e, ini 50fb6eac -> 13ff7f94 (CopToCrew 0.70, CrewHealth 1.00, TraitorReveal=1, Defend=0, [Difficulty] Ai=2 You=2 = Ctrl+Home / Ctrl+PgDn, ListUserGuard=2 for DM03 0x4f8a8e).
Undo: C:/kl_build_1024/merged_1110h/kit/UNDO.bat FIRST, then merged_1110g. 81 told to re-pack. Open: bench m1110h_dm03 + DD10 first-spawn trace (dd10trace3a/3b) when the PC is free.
2026-11-10 ~23:50 - [d0] MERGED 1110h STAGED, NOT installed (pack frozen; 81 re-packs after any install): branch d0-merged-1110h cb0a9885 = 1110g + difficulty + traitor + dm03skip0. SHIP 4485802e / TEST b43a109d, kit C:/kl_build_1024/merged_1110h/kit (pins live dll 6dcae9e6; ini 50fb6eac -> 13ff7f94; undo byte-exact in scratch; review PASS; kl_tests 173/0/5).
Sponge cause: CopToCrew 0.01 = stock Arcade L1 + CrewHealth 1.25 -> 0.70 / 1.00, Ctrl+Home / Ctrl+PgDn steps. Early traitor = our TraitorFoe score-bit write (a7636fb0) -> [Bots] TraitorReveal=1 hides until first hostile act; Defend=0 until benched. DM03 0x4f8a8e: ListUserGuard=2 = C port of 0x630700 skipping key 0.
Bench: kl_bench_1106.py run m1110h_dm03 solo. DD10 first-spawn death (FA_DieFromSelf at x ~9300 z ~936, 3/3) UNPROVEN: trace kits dd10trace3a..d (branch d0-dd10tracekit-1110), needs the owner's PC. Incident: a reviewer ran difficulty kit install.py --help = real install; undone byte-exact at once, kits now refuse unknown args.
2026-11-10 ~21:40 - [d0] INSTALLED merged_1110g (owner "install all", NOT benched): dll b330ffb6 -> 6dcae9e6 (branch d0-merged-1110g f9f873cc = shop-cycle + [CampEquip] Kane's DM gun Mode=dm + [CampRappel] Cam=ours + [Campaign] CutsceneLog=0), ini 1d0688aa -> 6d0b69b5.
GUESSES: campequip gun per level (M04-08 UMP/MP5, M09+ Zastava/SG552) and pistol may be replaced by M-77B; Cam=ours = cam+0x7fc cleared from rappel state 3 to landing+1.5 s. DM01B doorfix + DM03 vault stage_m were already live (17:08/17:09). Undo: merged_1110g/kit/UNDO.bat FIRST, then shopcycle_1110/kit/UNDO.bat.
2026-11-10 ~21:10 - [d0] INSTALLED campreflect_1110 (owner: Retomoto "so reflective" in the campaign): M09 18bfd459 -> 8007da0b, M09B 84ba3585 -> cae54aac (.fxc only: 3 + 5 alias records moved off REFLECTIONENABLED donors). Not run in game. Undo: C:/kl_build_1024/campreflect_1110/{M09,M09B}/UNDO.bat.
Building ONE dll merged_1110g = shop-cycle (live b330ffb6) + [CampEquip] (Kane's DM gun, Mode=dm) + [CampRappel] Cam=ours (owner's camera during the descent) + [Campaign] CutsceneLog (off). Workflow witt48ks0, not installed yet.
2026-11-10 ~20:40 - [d0] OWNER "PAGE 1/4 goes to 2/4, F2 mod menu": shop F2 pressed with the weapon list closed (round-over / category) started from the page the last shop left (stale kspg.hire/ctl), not the caption's stock page -> opened CONTROLS / BOTS AND MODES. Fix branch shop-cycle-1110 947ccb8a (kpq_press_page, test 123/0, kl_tests 169/0), reviewed. INSTALLED dll 6711bc5f -> b330ffb6 (TEST 4f827cb9), kit C:/kl_build_1024/shopcycle_1110/kit; undo it FIRST, then merged_1110f. NEXT dll merges must base on shop-cycle-1110. Disk: pruned dd10_slim_1105, vans_1107, 5 uninstalled lcchain variants (C: 0.2 -> 5.5 GB). Cutscene gun waving: give code + script holster refuted, likely DM gesture clips with a gun in hand, unproven; read-only [Campaign] CutsceneLog being built.
2026-11-10 ~20:30 - [d0] Story Mode crash (menus_combined campui page, graphic used twice) -> 6b storyfix_1110 INSTALLED ([CampaignUI] Menu=0, row "Dead Men Rising"). Menu sounds uncut
(Menu/Window had a 1.5 s cap): C:/kl_build_1024/menusounds_full_1110 INSTALLED (WAV 6f799fa3, klms 2752cbc3; undo its bat). Neither run in game yet.
2026-11-10 ~19:55 - [6b] STORY MODE CRASH (owner, since menus_combined_1110): main menu -> Story Mode -> campguard "ZGraphic template int3 0x51f1a9 ... no campaign level" -> ASSERT -> c0000005 0x4be312 (read 0x40).
Cause: the *_campui twins (served while [CampaignUI] Menu=1) put the pick row (Y288) AND the campui row (Y322) on CampaignMenu, both on FocusBar_short#04 + Line_Short_01#04 (used 2-3 x; stock uses each once). GUESS (strong, files only): a scene graphic binds once.
FIX INSTALLED C:/kl_build_1024/storyfix_1110: ini 3df8a23b -> 7c8cec3d ([CampaignUI] Menu=0; the campui row needed the uninstalled levels half anyway) + owner rename: pick row + KLCampPick headline -> "Dead Men Rising" in the 4 overlay Patch01*.zip
(055b5f37 / e11c4844 / e8cf0a8a / 1494c669). Rehearsed (install, 2nd refused, undo byte-exact); NOT run in game. Undo: storyfix_1110/UNDO.bat FIRST, then menus_combined_1110. menulayout_1110 pins are now stale (re-pin before use).
2026-11-10 ~18:30 - [6b, offline] MENU LAYOUT (cloud tools/kl_menu_layout_1110.py) STAGED + REHEARSED, NOT installed (tests stopped, testers download today, a broken main menu = no game). No crash involved.
Kit C:/kl_build_1024/menulayout_1110/kit: plan 0 problems + check PASS on the live set, Dead Men art filled into the 6 scene stubs (entity delta 0), AND the same layout on the _campui twins (they shadow _deadmen while [CampaignUI] Menu=1;
without them the XML part would not show). Pins live 57f2cb22 / 0bd4379a / 1fb7d82e / f0d82c48 / scene b2b494ab; scratch rehearsal install / 2nd refused / undo byte-exact. Undo it BEFORE menus_combined_1110.
Contact sheet (kit/contact_layout*.png): main-menu focus bars MMfb (1024 wide) run across the Kane/Lynch portraits, Heister splat overlaps KLH_CharPic: design call for the cloud before an install + screenshot bench.
2026-11-10 ~17:45 - [6b] INSTALLED on owner "install all" (no game run: owner stopped tests), no crash involved. OUTFITS maps on all 21 maps (C:/kl_build_1024/outfits_1110, 75 files md5-verified, backups = hard links, map zips e.g. DM01 b3b5bee8, DM07 f774dc97 -> 06's dm07plane da0e0431 on top).
MENUS COMBINED (C:/kl_build_1024/menus_combined_1110/kit, --keyboard-only): campaign pick + 33-entry Heister row + campui row (Y322) on 06's plates; 4 overlay zips + 5 *_campui.zip, ini 0da79eb8 -> 3df8a23b ([CampaignPick] Enable=1, [CampaignUI] Menu=1), dll 6711bc5f untouched.
RISK: static menu count (kl_menu_count) keyboard 4938 / GAMEPAD 5129 of 5000 -> gamepad can fault 0x8618b9 (DefaultFocus); live count UNMEASURED: next game start add [Menu] TableLog=1 and read 'menu: table N'. campui LEVELS half not installed (needs 3.2 GB, C: 2.5 GB).
Undo: menus_combined_1110/kit/UNDO.bat; maps: dm07plane_1110 install.py --undo FIRST, then outfits_1110 install.py --undo --skip-run-check --ignore-dll.
2026-11-10 ~17:45 - [06] INSTALLED on owner "install all" (NOT benched, tests stopped): menuplates_1110 RE-STAGED on the live overlay (scene zip had moved caf16a44 -> 9de0f526):
Overlay Patch01_deadmen ba1154de -> 76499363, Patch01_rows12_deadmen 3a452a28 -> 355a4b30, Scenes/kaneandlynch_deadmen 9de0f526 -> b2b494ab (only the OnFocus colour set = ink; 6b re-bases its menu kit on these).
dm07plane_1110 (sub 0x108; re-staged on d0 exitstrip then 6b outfits): KLExpansion DM07 F06 f774dc97 -> da0e0431, bots ea470c0f -> 0fd216da, base a3ff31ad -> 54dec058. Both rehearsed byte-exact.
Undo: dm07plane_1110\install.py --undo BEFORE outfits_1110; menuplates_1110\install.py --undo. Bench later: DM07 gate (planes block heisters, van passes), ML1 plate text dark.
2026-11-10 ~19:00 - [d0] OWNER "install all": d0 map kits (DM01B door fix + strip, DM06B/DM07 strips, DD10 south box, DM03 vault, DM09 cover), 6b outfits (21 maps), 06 plates + DM07 plane
INSTALLED; only DM01B load-benched (before outfits), owner said "stop tests". Live dll SHIP 6711bc5f / ini 0da79eb8. Undo: dm07plane -> outfits -> d0 kits. dm09terminal HELD.
NEXT when the PC is free: re-pin LOADSWEEP to the outfits md5s, 13-map load sweep + online smoke; undo any map that fails.
2026-11-10 ~11:40 - [d0, offline] HELD STAGES re-checked (dry-run on live): all pin live except exitstrip DM01B (stale 5eab5ecc). Re-staged on the door fix output:
C:/kl_build_1024/exitstrip_ondoorfix/exitstrip_1110/DM01B (check PASS, lane unchanged, prm roots 0 stale). DM01B order after "upload done": dm01bdoorfix_1110 FIRST, then the strip.
2026-11-10 ~11:15 - [d0] LAUNCHER E2E PASS (for 81, C:\kl_release\e2e_1110 + pkg_1110, no INSTALL/UNINSTALL): verify 823/0 before + after, dll 6711bc5f / ini 0da79eb8 unchanged, dinput8* list identical, no strays.
PLAY DEAD MEN RISING -> hook loaded, clean close logged; PLAY DOG DAYS -> hook renamed .klmerge-off, no hook; PLAY DEAD MEN RISING put it back byte-exact. No new crash files.
Steam options on the PC are "-dx10" only (no F01/AutoExit; 81 tells the owner). Oddities to 81: MOD "not installed" without a journal, letter-spaced button names for UIA, "..." buttons = dashes, hook stays off after a stock run (README hint 1e9be368).
2026-11-10 ~11:00 - [scheduled, cloud] PALE PLATE TEXT FIXED (T9 "theme bug for the cloud"): the OnFocus colour set (text ON a light plate: lobby header, selected row, Heister values, Bonus/Penalty) was mapped to chalk; stock is ink.
Table fixed in kl_menu_look_1109.py; repair kit for the live _deadmen files: tools/kl_menu_plates_1110.py -> C:/kl_build_1024/menuplates_1110 (install.py pins ba1154de/3a452a28/caf16a44, README). NOT installed (PC busy). Next: install (game closed) + ML1 lobby shot.
2026-11-10 ~10:25 - [d0] RELEASE ONLINE SMOKE 13/13 PASS (TEST 03840ed0, nothing installed): Q32 host+join pair, round 1 -> shop -> round 2 on DM01 DM01B DM02 DM03 DM03A DM05A DM06 DM06B
DM07 DM09 DM11B DD10 DD06(stock); every seat asserts 0 / faults 0 / dumps 0, no d3d9+0x5feeb device reset (fc's 08:33 reset = one-off system display event). DM06B client: 1 first-chance
c0000005 at DINPUT8+0x10953e = kllistguard's __try scan reading a page freed meanwhile (caught); kl_bench_1106 faults() now skips first-chance DINPUT8 lines when the log's RESULT says faults 0.
Run: python tools/kl_bench_1106.py run load_<MAP> online. Held stages still wait for 81's upload-done.
2026-11-10 ~10:40 - [vault] DM03 blow-up vault NOT installed (out of the release pack). DM03VAULTK on stage_k (--no-arm) PASS: all 6 lanes blocked BOTH ways, the per-leaf slabs hold
(side rule refuted). The stage_slab "leak" = the host pressed on the DOCK side fired the Arm box (edge 44 cm off the hinge plane) THROUGH the shut leaf, fuse 3 s, swing.
Fix: Arm box moved to z -7250 (edge 2.9 m off; kl_dm03vault_1110 --arm-z, refuses < 1.5 m). stage_m on live 33361cd1: zip c71dbd01 / bots fce3ac2a / base e23f6545.
10:34 RERUN DM03VAULT_1110 PASS (both seats 0 faults/asserts, round 2, 15/15 vault checks incl. the late Backstop walk; the dump FAIL = stale 08:33 .dmp files).
READY TO INSTALL on the owner's OK: C:/kl_build_1024/dm03vault_1110/stage_m/install.py (pins live 33361cd1).
~08:35 on stage_m: shut door blocked the dock walk, Arm at -7226 armed, blast, walked through = door logic PASS; run cut at 08:33:55 by a display
reset (both seats d3d9+0x5feeb, Display 4107 SetDisplayConfig; cause unknown, the "input" may be the bench's own keys) before the Backstop walk + round 2. Undo byte-exact. Rerun when the owner is away; not installed.
2026-11-10 ~09:00 - [d0] RELEASE LOAD SWEEP 13/13 PASS on the live frozen-pack files (TEST 03840ed0, nothing installed): DM01 DM01B DM02 DM03 DM03A DM05A DM06 DM06B DM07 DM09 DM11B DD10 + stock control
each loaded under its own rule, reached 0x19, stood 60 s, 0 asserts/faults/dumps. Control = DD06 (page 0 entry 4; kit re-pinned f609e1d9). Offline: every type-7 .prm root of all 26 live zips hits a .oct record start.
Run: python tools/kl_bench_1106.py run load_<MAP> solo. DM01B door fix (C:/kl_build_1024/dm01bdoorfix_1110) still held until 81 says upload done.
2026-11-10 ~07:20 - [d0] DM01B LOAD CRASH ROOT CAUSE PROVEN + FIXED (ec59d918): kl_dm01b_undoor_1109 model_leg re-referenced the .prm roots against the EDITED .oct (room part -16 bytes), so 3640 type-7 roots
pointed 16 bytes into the next record -> junk vtable at 0x6ad1d9 (ZCollisionBase slot 34). Now keyed on the live .oct; check() fails any root off a record start (flags the old 5eab5ecc: 3640). Siblings (kl_interact_graft, dm02doorglass) OK.
Rebuilt C:/kl_build_1024/dm01bdoorfix_1110 (476aec5f / a056edbd / 4272c0eb, check + self-test PASS), bench kit dm01bdoorfix1110, NOT installed (freeze). Also: exitstrip DM06B + DM07 benches PASS (held).
Release load sweep kits load_<MAP> (13 maps incl. DM01, DM06, DD05 control; af75c29c) run after fc's vault benches; verdicts go to 81.
2026-11-10 ~06:35 - [f0, T0] PACKAGE RE-FROZEN, supersedes 9a60c535 (do NOT upload that): d0 found the live DM01B 5eab5ecc (dm01bdoorfix_1109, unbenched) crashes at round load 3/3
(c0000005 junk address, caller 0x6ad1d9); A/B on 778b075c PASS -> d0 put 778b075c / bots dccc9250 back live. map:DM01B re-made: C:/kl_release/KLMerge_package.zip 2,026,178,709 bytes,
sha1 504a398f1998f0f5987faa4b9f8cc8deab32fe3e. DM01B rehearsal from the unzipped package PASS (install 0, uninstall 0 differences). DM01B keeps its 2 dead kick doors (as 11-09).
2026-11-10 ~06:20 - [d0] DD10 EXIT-SOUTH BENCH PASS, HELD for the next release (81's freeze, package 9a60c535 has DD10 6aeb8208): stage C:/kl_build_1024/dd10exitsouth_1110
(zip e152950e / bots 604a9d9e / base 88f4be29). dd10south1110 + dd10southledge1110 (TEST 03840ed0): van called from z 750, HealFloor 3600->9600, shielded 53 s wait + drive-out,
seat alive at (8300,750) wait 15/30/45 s, 0 faults/deaths; only the known round-end check FAILs. Undo byte-exact. Install when 81 says the owner uploaded.
2026-11-10 ~06:00 - [d0] DM02C INSTALLED after bench run 4 ALL PASS (online 7/0, items 37/0): DM02 43c088c2 -> b24fb05d / bots dde7720a / base 816ce4ad (combined_closed, variant_full).
Doors 3+4 walkable, both vault panes (closed pose) block then break at the 60 s fallback, both shutters prompt (6/8) + rise +300. Undo: C:/kl_build_1024/dm02shop_1110/combined_closed/install.py --undo.
DD10 street death = the keyframed van runs over heisters in the north half of otrExitLevel (z 650..1550 covers the lane z ~920..1140; seat at z 1100 died, z 750 lived): exit-south stage (box z 650..900) being built.
2026-11-10 ~05:55 - [f0, T0] RELEASE PACKAGE FROZEN 05:47, ready for the owner's upload: C:/kl_release/KLMerge_package.zip 2,026,193,651 bytes (< 2 GiB), sha1 9a60c535
(core 1110f 6711bc5f / ini 0da79eb8, DM02 combo b24fb05d in; two rehearsals from the unzipped package PASS). Later landings = next release. Owner: upload per OWNER_RELEASE_STEPS section 4.
2026-11-10 ~05:00 - [d0] INSTALLED after bench PASS: SMART COPS DM01 (e091f0d8 / bots 957f20aa / base 6b7255e6) + DM03 (33361cd1 / 0bc8d138 / a4ad617a, on fc's back SWAT),
DM05A LCDOORS timer (791eb9c3 / 912e08a5 / 501e1b79). Undo: C:/kl_build_1024/{smartcops_1110/DM01,smartcops_1110/DM03,lcdoors_1110}/UNDO.bat. DM02C (doors/glass/shutter/shop) NOT installed:
host killed at the door 2 stand (AI posts; stands moved, 65d3543e), door 3 stand on a merc post, and both vault glass panes are SWUNG out of their doorways (block nothing): closed-pose stage being built.
2026-11-10 ~03:45 - [f0] DM03 BACK-SWAT INSTALLED (owner 11-09 ask) after bench DM03BS_1110 PASS (tools/kl_bench_1110.py, TEST f4c8c3fd, 2 seats, items 16/0, online 7/0, census 48, 427 cop hits, kick 176 ok, no screenshots so the SWAT look is unseen):
DM03 8e23cbd3 -> a81ede87, bots e8c06e13, base afc6ca40, KLJoin 5c02ca99 untouched. Undo: python C:/kl_build_1024/dm03backswat_1110/install.py --undo --skip-run-check (backups *.before-dm03backswat_1109).
DM03 chain agreed with d0: back-SWAT -> d0 smartcops re-staged on a81ede87 -> vault (tools/kl_dm03vault_1110.py cc3702a5, stage on a81ede87, NOT benched) re-staged on smartcops. Vault review: a detour via the security hall stays open (shortcut, not a gate: owner call); 240 s Backstop may replay the opening after an early blast (bench must check).
2026-11-10 ~03:15 - [f0, T0] PACKAGE MADE + REHEARSED, NOT uploaded: C:/kl_release/pkg_1110 (823 files, 635 patches, installs 13.13 GB; core = SHIP 38104558 + ini a08b6110), packed
KLMerge_package_v1.0.0.zip 3.68 GB sha1 dd8cc7df (+ KLMerge_package.zip link). Scratch-DD rehearsal (core,audio,overlay,pcdef,stockwav,DD01,DM07,DM09 = 387 files): install exit 0 in 409 s, verify 0 problems, uninstall byte-exact (4 empty KL_PortBackup dirs remain).
BLOCKER: GitHub caps an asset at 2 GiB. 06 is writing bots.zip-vs-main-zip patches ('out:' refs, ~1.89 GiB total) -> re-make map groups + repack. d0 map stages (lcdoors, DM02 combo, smart cops, dll 1110f) ride it if installed by ~10:00.
make now prints kl_ini_shipcheck ERROR/WARN (never stops). Owner: 7 WARN ini keys, menu look in/out, literal stock bytes in a PUBLIC release (06).
2026-11-10 ~03:35 - [scheduled check-in, offline] SHIPPED-INI REVIEW TOOL: tools/kl_ini_shipcheck.py (+_test) grades a KLHook.ini by the sample's own (recommended ...) / TEST-only / diagnostic comments;
live ini 02:19: 0 ERROR (no owner path in a value), 7 WARN (CarDown Dry=1; [Brain] RayAim/HolderSet/CombatFlag TEST-only; FireLine/DefendPull/OnlineBrainBoard log modes), 73 FEAT, 47 Log=/probe keys,
[Campaign]+Camp*/[Redirect.N]/[Page.N]/[Wardrobe] undocumented in the sample: debug/notes/2026-11-10-scheduled-shipcheck.md. kl_release_test PASS on Linux, kl_tests 150/0/18. Owner: Dry=1 + the 3 TEST-only keys for the tester ini.
2026-11-10 ~02:55 - [T9 local] MATCH PAGES SHOT (no crash involved): bench MENULOOK_MATCH PASS (TEST f4c8c3fd, deadmen + stock, live dll 38104558 / ini a08b6110 restored).
All 16 pages per look now in C:/kl_build_1024/menulook_1109/shots/{deadmen,stock} (lobby, lobby_map, pause, roundover, shop_page1/2, shop_hire, shop_controls + the 8 menus).
THEME BUG for the cloud (colour, not width): text ON the light plates (selected row, lobby column header) is dark in stock but PALE in deadmen = unreadable (lobby 'LOCATION: HOT COFFEE', 'NAME: / CRIMINAL ...').
Shop pages identical in both looks (not themed): 'ASSAULT RIFLES' spills below the category box, the left arrow overlaps 'SW MP45' = stock/hook layout, for kl_menu_layout_1110. Pause + roundover fine.
2026-11-10 ~03:00 - [T9 local] MENU SHOTS + PICKER LIVE (no crash involved): menu sound picker INSTALLED (install_1110c.py, ini f67f94bc -> a08b6110, sounds _deadmen.WHD 5ba73f5e/.WAV fffb4841/.klms 5ae473c1; undo C:/kl_build_1024/menupick_1110/install_1110c.py --undo; dll is d0's 1110d, accepted). Bench MENULOOK_MENUS2 PASS:
8 pages per look shot (C:/kl_build_1024/menulook_1109/shots/{deadmen,stock}), ML5 PASS, ML1 = wider rows only, no real clipping by eye; Heister Outfit row hits its arrows in STOCK too.
Shots fix 6428ca18 (kit ini D3dShotPost=1 + Bridge=1). Next: match pages, then the cloud's kl_menu_layout_1110.py on overlay 9de0f526.
2026-11-10 ~01:30 - [6b] MENU SOUND PICKER on the campaign build: klslot.c kls_menusounds + klmenusounds_logic.h (45 checks), [MenuSounds] Enable/Navigate/Confirm/Back/Toggle/Slider/Menu/Window = dd|dm|off|<clip>, Mod Options rows, tools/kl_menu_sounds_1110.py (+_test). Checked against the REAL banks (dd/dm/off/clip/bogus; installed 1109 bank refused by hash). Fix found: the table must not carry a 'dm' C line (parser reserves it). SHIP 68c6ee55 / TEST fc00acb8 (klhook/out_menupick1110*), kit C:/kl_build_1024/menupick_1110 (pins 258daf8e, NOT installed, NOT benched: queued after 81's T0).
2026-11-10 ~00:55 - [06, offline] RELEASE ASSET NAME: Setup.bat downloads .../releases/latest/download/KLMerge_package.zip but pack_release.ps1 wrote only
KLMerge_package_v<ver>.zip (+ a .sha1 naming that file); OWNER_RELEASE_STEPS had a manual copy step. pack_release now also writes KLMerge_package.zip (hard link) + its .sha1;
steps say C:\kl_release (D: 1.2 GB free); launcher_test checks the name (fails on the old pack). Scratch pack x2 OK (11 files, 0 game files). Owner on the PC: no live run.
01:10: launcher PROVEN LIVE by the owner's own use 23:53-00:35 (riff plays, PLAY x4, hide/reappear each time, 0 errors in launcher_1109\KLMergeLauncher.log).
Setup.bat e2e after the rename (file:// URL, folder "setup e2e & (x) o'k"): download/unpack/py -3/copy-up OK, launcher opened, riff made from the DM install in 10 s = md5 c9a762a1 = owner's repaired file.
GitHub R6C0/dead-men-rising: public, NO release yet (latest/download 404) -> waits for make + upload.
2026-11-10 ~01:00 - [campaign] INSTALLED on owner "install all" (NOT benched): campaign_1110 voices + rappel camera, dll 4722b12a -> 258daf8e, ini ba4441c1 -> c62045c9 (Adpcm=1, StreamRedirect=1: converted SND name ..\Kane and Lynch Dead Men\PC_Def.str, DM is on G:, so .str opens are redirected; empty PC_Eng.str now recognised;
SndDiv=1, [CampRappel] Land=auto = luvsic landing re-aim, CamFix=0, [Camera] CampaignOff=0 = owner keeps OUR camera on campaign). Undo: C:\kl_build_1024\campaign_1110\UNDO.bat BEFORE campaign_1109. Bench: M07F voices, M09 roof rappel ("camprappel: land=").
Menu: sounds stage2 (all 7 OSD records, RMS-matched, appended) + redesign stage A (DM backgrounds, overlay kaneandlynch_deadmen.zip caf16a44; undo redesign\UNDO menu redesign A 1110.bat) installed. Picker / campaign UI / lighting / outfits / arcade-style campaign pages still staging.
2026-11-10 ~00:10 - [campaign] MENU LOOK INSTALLED on owner "install this too" (NOT benched): toggle [MenuLook] DeadMen (DLL default 1, already in campaign SHIP 4722b12a, no ini line added).
Stage 1 fonts+colours: KLExpansion\Overlay\Patch01_deadmen.zip ba1154de, Patch01_rows12_deadmen.zip 3a452a28, Scenes\kaneandlynch_deadmen.zip 31623dcc (worst row +16.3% wide).
Stage 4 clicks: <DD>\Scenes\kaneandlynch_deadmen.WHD 52e4c167 / .WAV dc8effa7 (5 OSD records -> DM UserInterface Up_Down/Toggle/Slide/Back/Select; ambience + OpenWindow kept). Stage 2 (plates/bars) not written.
Undo: C:\kl_build_1024\menulook_1109\stage1\UNDO menu look 1109.bat + sounds\stage\UNDO menu sounds 1109 (variant).bat; or DeadMen=0. Check "menulook:" lines in KLHook.log.
2026-11-09 ~23:55 - [campaign] INSTALLED on owner "install all" (NOT benched): luvsics Dead Men campaign, all 16 levels + M07F funeral cutscene (Scenes\Locations\Mxx, own folders, 2.9 GB),
dll 50d20cd1 -> campaign SHIP 4722b12a (out_campaign_1109), ini 4cb8faa0 -> ba4441c1 ([Campaign] Enable/Routing/Trigger + CampGuard/Squad/Give/Rappel/Revive, Grenade Release=1).
Start: game at main menu -> <DD>\Dead Men Campaign.bat -> pick a level (writes KLCampaign_load.txt). Undo: C:\kl_build_1024\campaign_1109\UNDO.bat FIRST, then levelmusic_1109.
2026-11-10 ~01:05 - [scheduled check-in, offline] kl_tests GREEN on Linux 137/0/17: klmenulook_test 0xC0000409 = the test's own out[260] vs cap 300 (fixed, 109 checks); 11 unlisted C tests
listed (all PASS, ASan/UBSan clean); kl_campaign KL_PortBackup guard now case-folds on every host; kl_release_test SKIPs without zstandard. Owner: run `python tools\kl_tests.py --c` on Windows once;
the DD / DM folders are not connected to the scheduled task (KLHook.log / dumps unread).
2026-11-09 ~21:30 - [main, offline] LUVSIC CAMPAIGN MERGE (owner: "his campaign stuff ... maybe not the whole ui thing"): third_party/anp refreshed to his 32aa649 minus UI (dmhud/dmfont/anp_menu/anp_movie);
tools/kl_campaign.py (setup/convert/status/install/undo, additive M01..M14 folders, md5 manifest; _test 50/0); klhook ports, ALL default 0 behind [Campaign] Enable: klcampaign.c (scene routing, load trigger, save redirect,
ADPCM), klcampguard.c ([CampGuard] incl. ListUserFA = the DM03 0x4f8a8e respawn crash), [Grenade] Release, [CopSquad] HeldGuard, klcampsquad/klcampgive/klcamprappel, klcamprevive (observe only). FA down modules skip campaign levels.
Ini keys: klhook/ini_campaign_*.txt (not in KLHook.ini yet); 9 new C tests UNLISTED in kl_tests C_TESTS. Builds SHIP fda53367 / TEST 43060e47, NOT installed, NOTHING run in the game. Missing: [CampEquip] (M02). re/campaign_merge.md.
klmenulook_test (peer 2b64ea7b) crashes 0xC0000409 under cl.
2026-11-09 ~23:00 - [coop] DM02 CO-OP SHUTTERS staged, NOT installed: tools/kl_dm02coop_1109.py (+_test PASS, rehearsal PASS), stage C:\kl_build_1024\dm02coop_1109 (--variant timer DEFAULT 90 s | coop). The 3 Atrium_201a shutters (REF 24710/24711/24712) get F07-style KEYS (rise 300 cm, frames 0..82) + MatPosAnim, a type-4 HVK slab each, Open nodes -> MatPosAnimProxy; OpenNow keeps only the 2 frontages. Pins live zip bd119e9c, bots a5068fa0. timer zip 43c088c2 / bots bb8f04cb, coop zip 698fc59b / bots bd22461d. Proven offline: only prp/gms/buf/HVK members change, slots identical, static list + MOPP + order untouched, check.py 0 bad, check_passes PASS. GUESS: the keyed ZSTDOBJ still draws and its type-4 body follows it; needs the bench in the stage README.
2026-11-09 ~18:30 - [main] KICK DOOR AUDIT (workflow, offline, adversarially verified) of every added door: DEAD (no room / sealed / bypassable) = DD10 19 of 21 (only 9 + 13 gate),
DM01 957 + 2569, DM03A 6516 (+ older doors 1, 5), DM01B !1 D4 + !2 D2 (!1 D3 unclear). Real: DM01 1,2,4-7, DM02 all 6, DM05A both, DM01B !1 D2. DM06/06B/07/09/11B have none.
Kits being staged (workflow wmwfodbbu): revert the dead ones to plain doors, DD10 + 14 two-sided candidates checked for replacements. Nothing installed. Details: scratchpad doors_audit + the workflow output.
2026-11-09 ~17:50 - [main] MUSIC KIT for the owner: C:/kl_build_1024/levelmusic_1109 (SHIP 50d20cd1, TEST 0830d057; from 935b6222, live dll f016c36d pinned)
+ [LevelMusic] Restart=1 line. Rehearsed in a scratch copy (install, 2nd refused, undo byte-exact); NOT benched. kl_doors_clear_1108_test expected the old DM03 hosts
(546/1255) -> updated to [176, 64]; kl_tests 134/0/5. The repo KLHook.ini sample still lacks the [LevelMusic] block (peer-dirty file).
2026-11-09 ~17:30 - [music] DM LEVEL MUSIC ROUND 2+ (owner: 'music not coming in for the round after'): CAUSE proven from the exe: the music of DM01/DM02/DM03/DM06 is settings field 157, played ONCE by the settings Init (0x88d780 -> 0x8736d0 stores it at [[0x168e958]+0x944], 0x8ce720 plays it); later rounds reuse the level and nothing calls it again (only Backstab plays field 158). DM05A/DD01-09 have none; PlayMusic maps (DM03A/DM06B/DM07/DM09) are trigger-driven.
FIX built, NOT installed: klhook/kllevelmusic.c ([LevelMusic] Restart=0, Delay=2000, Online=0, Log=1; calls 0x8ce720 once per round 2+), logic + test kllevelmusic_test.c PASS. SHIP out_levelmusic1109 e80d80df, TEST out_levelmusic1109_test 38ecc430. No ini/feat row yet (KLHook.ini peer-dirty). GUESS: Init-time call context still valid in round 2. Bench: DM03 round 1 then 2, log 'levelmusic: round 2 ... restarted'.
2026-11-09 ~17:05 - [d0, offline] OWNER live: DM03 crash 0x4f8a8e at the police respawn (list record id 0; debug/notes/2026-11-09-dm03-fedrespawn-crash.md), DM03 kick doors 546/1255 one-sided (agent restaging on live c586d445),
no music in round 2 (agent). DM09 terminal bounds + OnlineVanRest pushed 0a8edd21 (stage 7ac5c209, dll SHIP d9239eef, NOT installed).
2026-11-09 ~19:40 - [06, offline] LAUNCHER RIFF POPS FIXED, pushed e07101e5: kl_pybink now decodes FIRST with burst_limit 4.0 (9 overloaded Bink blocks = the trailer's own
40-43 ms full-scale pops at 33.68..37.52 s, in ffmpeg's decode too); ffmpeg = fallback as decoded (no sample rule possible: the trailer clips for real in 42k frames). --keep-pops = old way.
Checked: pybink = ffmpeg 0-2 LSB outside those blocks; pop windows now at/below the music. 5.4 s to make. launcher_1109\music\deadmen_riff.wav regenerated (old in _before_1625), preview 14. Self-test 93, kl_tests --py 58/0/1.
2026-11-09 ~19:40 - [d0, offline] DM09 TERMINAL VARIANT staged, NOT installed (optional, recommended off until benched): tools/kl_dm09_terminal_1110.py (+_test PASS), stage C:\kl_build_1024\dm09terminal_1110 on top of dm09cover
(pins 3a981a70/2ede91ed/0126d412 -> zip 17f981ed, bots 2293dec7): van group + otrExitLevel + run boxes moved to the terminal lane x -25500 (stop z 8100), west slab opened z 7088..11114, pen bounds parked,
InvisibleBarricade REF 23098 cut from the .HVK (it sealed the pen; collision flood now reaches the lane). Open before a bench: NO bounds around the terminal (walkable 50 m+ west); online bots read the van node at the
moved group (-23647,-2700) (klbotfill.c:2296/2392, needs a rest-position guard); KLBF_WAY_MAX 8 -> 16 for the full route (ini_fragment.txt); clock proposal 8 min / TimeMax 10.
2026-11-09 ~19:10 - [06, offline] LAUNCHER MUSIC = OWNER'S FINAL PICK pushed 941ef598: Trailer.bik guitar riff 24.43-41.05 s (measured: starts on the first attack, seam cosine 0.92) x2,
4 s equal-power xfade into MenuLoop_01, fade to 0, loops -> music\deadmen_riff.wav (106 s 48 kHz, riff x0.34, menu x2.0, no clip; 3.4 s to make). Supersedes the 18:40 main-theme ask.
Trailer decoded by ffmpeg, else tools/kl_pybink.py (6b writing it; packed + copied when present). Without both: MenuLoop_01 alone. Self-test 87, kl_tests --py 57/0/1.
Owner preview: C:\kl_build_1024\launcher_1109\music\previews\13 deadmen_riff (tool output).wav. Open: kl_pybink check vs ffmpeg, then the launcher run live.
2026-11-09 ~16:05 - [f0, offline] LAUNCHER REVIEW FIXES PUSHED 107f86ea (Setup.bat: quoted python path, .part download, PowerShell Stop, no del;
launcher: Guard/trap, safe hook rename, log copy). Scratch e2e 7/7, launcher_test PASS. T0 next: kl_release make/verify/pack once the PC is free + dinput8.dll back.
2026-11-09 ~18:30 - [d0, offline] DM09 COVER STAGE built, NOT installed: tools/kl_cover_dm09_1110.py (+_test 24/0), stage C:\kl_build_1024\dm09cover_1110: +11 boxes (KL_CoverStreet!: 8 wall tiles, 2 static wreck copies
on V_JPN_Civilian_B2_A_Group_00#08; 1 unreachable prop box pruned by a floornav re-check). Pins live afee8967/90e9046d/bdd4dc08 -> zip 3a981a70, bots 2ede91ed, base 0126d412; undo rehearsed byte-exact, 2-lens review.
Finding: KL_CoverMore! already gave all 68 street vehicles static (explosion-proof) cover copies; only these 2 were missing. GUESS: the blast leaves static copies alone, NoCoverBox edge test. Needs a bench.
2026-11-09 ~15:35 - [06, offline] LAUNCHER MUSIC = Dead Men MAIN MENU theme, pushed c012079b: SFX/UserInterface/MenuLoop_01 (Ogg Vorbis, 77.0 s 32 kHz stereo) is CANDIDATES[0];
decoders bin\kl_oggdec.exe (stb_vorbis, pinned) -> ffmpeg on PATH -> tools/kl_pyvorbis.py (6b, 7 s). Real extract identical on both paths (max diff 1 LSB). File renamed music\deadmen_menu.wav
(old deadmen_launcher.wav = FA theme was reused); .Handle fix so ExitCode is read. kl_tests --py 55/0/1. 81 owns the remaining Setup.bat/ps1 review fixes. Launcher not run live.
DM07PLANE stages (0x108 + 0x72) exist (no longer blocked by disk); benches wait for test runs + the mod dll back on.
2026-11-09 ~17:45 - [d0, offline] DM09 TERMINAL ROUTE FEASIBLE: tools/kl_dm09_flood_1109.py on the LIVE DM09 mesh: road mouth (-5700, 9000) -> stairs -> campaign terminal van (-24630, 8958)
is ONE mesh component, path 279 m, y -40 -> -1040, 0 broken steps. Blockers are authored only (west slab x -7500..-6500, exit boxes/van at z 10800). Plan for a toggle-able
"terminal" variant + hook consumers: re/dm09_terminal_1109.md. Also from the research workflow: more cover + wreck cover boxes (kl_cover_1026) = safest first stage; SWAT drop-offs = parked vehicle + trigger only.
2026-11-09 ~14:20 - OWNER (live) asks, details in re/week_plan_1028.md "Owner's words 11-09": DM03 Withdrawal = more SWAT at the BACK incl. the van spawn (front stays normal police),
the double door before the garage as a BLOW-UP vault door with loot, more loot rooms + kick doors. DM09 Retomoto = escape down the steps to the van as in the campaign,
SWAT dropped off by vans/cars down there, more cover, wrecks as cover after the explosion (owner CONFIRMED ~15:00), AI not colliding into vehicles, player-player collision. "Interactive, immersed."
Disk: sessions prune superseded 1105/1107 stages + dead pq_*/c9_* kits (C:\kl_build_1024 = 35 GB, C: 241 MB free).
2026-11-09 ~21:00 - [cloud] TESTERS download Tue 11-10, PLAY Wed 11-11 (owner, live): ship-readiness first. tools/launcher/ (Setup.bat, WPF launcher in the brush-kit look,
kl_release install/verify/uninstall, READMEs) written offline, UNTESTED on Windows; copy for the owner in C:\kl_build_1024\launcher_1109. T9 MENU LOOK (owner "huge ask", default ON):
re/menu_look_1109.md; stage 1 kl_menu_look_1109.py (fonts + colours), stage 4 kl_menu_sounds_1109.py (OSD clicks -> Dead Men), toggle [MenuLook] DeadMen in klslot.c
(+logic/test, NOT BUILT) + Mod Options row. Hook owner builds/benches; local session runs probe/inventory on the live files first. Stage 2 (bars/plates) open.
DM03: re/dm03_vault_swat_1109.md + kl_dm03cops_1108 part backswat (default off) + kl_dm03_scan_1109.py (run on the live zip first).
2026-11-09 ~11:20 - [sched] MOPP BYTE CODE READ (tools/kl_mopp.py + _test, 115 checks on the live DM07/DD10 .HVK): list terminal = child index PROVEN (re/havok.md), fillers never returned.
DM07PLANE: slots 256 / 248 are reached for x -4622..-4526, y 464..817, z 9989..10395 / 10384..10843 -> the plane clones block any query box touching y 464..817 over the whole gap;
only a body wholly under y 464 slips (4 cm over the mud): no crawl bench steps needed, bench the sub flags + the van. kl_tests cloud 48/0/79 (fallback_guns KL_PortBackup refusal on Linux fixed, gunpunch SKIP as root).
PC idle since 09:23; the 11-08 14:22 dump = the FedKeep crash, nothing new. Owner: free C: (dm07unhide_1109 385 MB + dm07curtain_1109 325 MB stale) for the DM07PLANE stage.
2026-11-09 ~09:25 - [d0] DD10 LEDGE ROUTE FIXED + LANDING LIVE: the vancall Target change (KLJoin ebdf1472) broke the balcony ride; ledgefix_1109 put Target back (600409d7), but the ride lands ON 06_Exit
(8300,0,1100) = van lane, seat KILLED 3.6 s later (dd10ledgefix1109). New [Join] Land= (16e82f2b, kljoinland.c, [KLHook] JoinLand=1 recommended on, off online): moves the local player to Land after the jump.
KLJoin 600409d7 -> 8f3034c0 (Land=8300 0 750, ledgeland_1109). Bench dd10land1109 PASS (TEST a7f87dc2): landed 313 ms after, van called/healed 9600, 0 deaths/faults. INSTALLED merged_1109land SHIP f016c36d, ini 4a740f92 -> 1ec9bea0.
Undo: merged_1109land\UNDO.bat FIRST, then merged_1108h...; KLJoin: ledgeland_1109\UNDO.bat, then ledgefix_1109\UNDO.bat.
2026-11-09 ~09:45 - [06] DM07PLANE tool 1da31ede (tools/kl_dm07plane_1109.py, self-test OK, reviewed): HVK slots 248/256 (hidden gate panels) -> 2 clones of DD10's HERO plane at x -4578, y 381..979, z 9852..10948; static count 2777 kept,
REF 21320 reused (no new entities), --sub 0x108 or 0x72, panels stay hidden. GUESS: the list MOPP only reaches the old slot volumes (y 471..801), so the mud hole may stay. Bench kit DM07PLANE_1109 being written.
BLOCKED BY DISK: C: 131 MB, D: 111 MB free (stage needs 426 MB); kl_tests fails 3 on ENOSPC. Owner: delete C:/kl_build_1024/dm07curtain_1109 + dm07unhide_1109 (~740 MB, stale) and the D: scratch dirs.
2026-11-09 ~08:50 - [06] KICK DOORS proven on DM01 x2, DM03, DM03A, DM02 x2 (DM02_1109 run d ALL PASS; stands = KickDoor_Arrow entities). DD10GATE_1109 ALL PASS: hidden gate
does not leak (stock ColiObj_HERO_Plane01 blocks at x 8017). DM07: KillBox curtain inert (no KillBox ever proven) -> options un-hide panels (van clips, owner taste) /
DM07BURY_1109 staged on D: (not benched: C: 336 MB) / clone a HERO plane (workflow). Owner: delete D:/scratch_bury_game + D:/kl_scratch_dm07sink_{rehearse,review2}.
2026-11-09 ~04:35 - [d0] [VanBlow] ShieldCalled (8c4292b9, default 0, shields state 1 = DD10's heister-call drive-in) in f0's merged_1108h (SHIP 52b37716 / TEST fceb3c6d), STAGED NOT installed.
Bench dd10called1109 (install.py --test, undone): 0 faults, shield ON at state 1 both calls, 2nd van 9600/9600, but the 1st van was already 3600/9600 AT the call (hit in state 0, GUESS: shown by the approach box).
~04:45 dd10healed1109 (+ HealFloor=95) PASS 0 faults: 'restored 3600 -> 9600' at the wait (state 3; it still drives in damaged ~7 s), 9600 through wait + drive-out. Fire clearing unproven (black shots).
Effect: with HealFloor + ShieldWhileWaiting no EMPTY vehicle on any non-stock map can be destroyed before boarding (VanBlow's blow-up only after drive-out). f0 installs 1108h SHIP + ShieldCalled=1 + HealFloor=95.
2026-11-09 ~04:05 - [d0] DD10 dd10side1109 (live map, TEST 40d00164): a heister waiting in the exit box's SOUTH strip (8300, 750) lives through the van's drive-in + 53 s wait;
the box centre (8300, 1100) is on the drive-in lane (gate -> stop 8642, z 1030) and died there 4 s in (no kill box; KILLED BY RED = own Char 13). Not changed: stock layout.
Option for the owner: shrink otrExitLevel to the south strip. Open: the van reached its first wait at 3600/9600 (hit before state 3, no state 2 seen by ShieldDriveIn).
2026-11-09 ~05:30 - [shop] SHOP LOOK BENCH (live tidy, merged_1108f): C:\kl_build_1024\shoplook_1109 ON + OFF both PASS (TEST 40d00164, DD05, 2 seats, 0 asserts/faults), 130 shots each.
ON vs OFF: hire rows 'JEAN  $90K' vs '$90,000'; hire desc 3 lines vs 6 (OFF ran into the stars); page II caption 'PD2 GUNS', rows 'PD2 PAR'. Still stock: tab names (no redraw, as guessed), dim star outlines (idx 99 = dim, not hidden), selected-row text under the bar (page I too).
Fix b5465f50 (not in a dll yet, given to 81): TidyPage hire desc drops 'Price $X, rank N needed (no rank gate)'; with a gate 'Needs rank N (your rank R)'. Shots: <work>\build\klhook\solo\SHOPLOOK_{ON,OFF}_DD05 (inst1_44, inst1_263).
2026-11-09 ~03:10 - [d0] BENCHES on the INSTALLED DD10 + DM05A (TEST 09a02a2c, nothing installed, undo byte-exact each): dd10live1109 PASS: 'last:' called the van (59.8 s left), ShieldDriveIn+ShieldWhileWaiting
kept it 9600/9600 in, waiting and out (no fire). dd10call1109 ALL PASS: a heister in otrExitLevel with $0 calls it (state 3 after 4.4 s), but the seat at the box centre (8300,1100) died ~4 s in while the van
parked on it (GUESS run over, KILLED BY RED); the box overlaps the van stop (8640,1030). lcmusicblive1109 (DM05A music B 0ff298a6): 290 s, 0 faults, round end unseen (kit 480 s too short -> 600). tools/kl_bench_1106.py.
2026-11-09 ~03:00 - [06] INSTALLED on owner OK (not benched): Hasta look/vault/blast (DM11B), dm03cops -> doors DM03 -> DM03_van (DM03 c586d445), doors DM01 + DM03A, DM01B street2 van (778b075c), DM07 van (f35e4133), dm02fix (vault glass now HVK-cut, coop OFF: static planes never open) -> dm02door (DM02 bd119e9c).
Undo: UNDO ALL 1105.bat steps 0z1..0z9, 0za (top). C: freed by hard-linking stage copies equal to game files (tool in scratch linkdupes.py). Bench queue: after d0, f0, fc. Bench kits + DM01B wider corners being prepped (wewgiykat).
2026-11-08 ~21:00 - [d0] INSTALLED for owner testing, NOT benched: DM05A club music level B (Ambient group 0.5, 2D pair b1 12, 3D 48/30; zip 0ff298a6, bots 72259e27, base 6cd71dd7);
DD10 flatledge (KLJoin 481520e7) + dd10flats (3 loot stacks to y1600, 2 cans re-seated + 6 new, 21 kick doors; F07 13bc6388, bots 488872aa, base 2d73022b, KLJoin 30482fec).
DD10 van: called ONLY by entering otrExitLevel (8300,200,1100); backstop only un-hides it, parked van unshielded. ~22:00 dd10vancall INSTALLED (approach box shows van, marker from alarm, Join.3 -> 8500 0 1180; no fallback call): F07 1a0d94b0, bots 27c9fae8, base 11a071b3, KLJoin ebdf1472. Undo: UNDO ALL 1105.bat steps 0y, 0x, 0l, 0w (top).
2026-11-08 ~17:40 - [shop] SHOP UI TIDY built, NOT installed (owner: page II + hire page 'still look somewhat bad to navigate'): [ShopPage] TidyPage2 + [Hire] TidyPage, both default 0, '(recommended on)'.
Page II: rows 'PD2 PAR', desc line 1 'PD2 GUN: price + rank of the stock gun' (Police reg. last), caption 'PD2 GUNS (13 NEW)', PD2 tabs PISTOLS+SHIELD.. (GUESS: may not redraw). Hire: line 1 '$45,000 - BUY twice to hire' / HIRED / RANK TOO LOW / NOT ON THIS MAP,
rows 'Pierre  $45K' / HIRED / n/a, no stars without a rank gate, no gun lock. klshopui_logic.h + klshopui_test.c, kl_tests 112/0. SHIP 027cd72d / TEST 9eeedf81 in C:\kl_build_1024\shopui_1108. Needs a look bench (widths are GUESSes) when testing is allowed.
2026-11-08 ~17:20 - [veh] DM01B street2 van from/to unseen pockets, staged NOT installed (zip 778b075c, bots dccc9250, base 6616525a; pinned live 74d37233 / 73583df1 / c3535e34): waits west (-8000,30500), leaves east (17400,30400).
Seen by 0 of 385 reachable-floor viewers at both, 0 pierces, planter ground ok. Kit needs ~940 MB (--min-free-mb 300). re/vehicle_routes_1108.md. Not benched.
2026-11-09 ~04:56 - [f0] MERGED 1108h LIVE (for d0): dll d1145cbe -> 52b37716 (from 8c4292b9 = 1108g + d0 [VanBlow] ShieldCalled), ini f7f11dcc -> 4a740f92
(+ [VanBlow] ShieldCalled=1 + HealFloor=95, both "(recommended on)"). Benched by d0 on the TEST twin fceb3c6d (dd10called1109, dd10healed1109 PASS), not as SHIP.
Scratch round trip ok (SHIP+TEST, 2nd install refused, undo byte-exact, dry, strip drops exactly 2 lines, wrong dll refused). 1108g LIVE before it: bench M1108G_DD05 PASS.
Undo: merged_1108h\UNDO.bat FIRST, then 1108g, 1108f, 1108c, 1108b, 1108, vanwait_1108, 1107.
2026-11-08 ~18:00 - [veh] DM07 VAN RE-STAGED, NOT installed: C:/kl_build_1024/vehroutes_1108/DM07 (zip f35e4133, bots 1f514d51, base 08478b6e; pinned live e0a9e326 / 7e897565 / f6259849).
Far start/end in the unreachable mud pocket (x -9300), gate = hidden fence panels (0x400 hides render only, static collision stays), reverse out, crash keys on the floor. Seen by 29 of 639 reachable-floor viewers (gate corridor only). Undo byte-exact in scratch; install needs ~1.4 GB free on C:.
2026-11-08 ~18:30 - [d0] INSTALLED for owner testing ("install and tell me"), NOT benched: DM05A heli departure (lcdepart) + club music A rebased on it (stage C:/kl_build_1024/ondepart_1108/lcmusic_a_1108): zip 0c0980c4, bots 2f719e08, base 0344d4c9.
DD10 van lane z 1030 + gate fence render hidden (collision kept): F07 5d76d91a, bots 069f4402, base 3dcfc1d3; thin margins (pillar 7 cm, dustbin ~1 cm), crash legs still clip. Undo: UNDO ALL 1105.bat steps 0v, 0m, 0e (top). Re-stage DM05A on 0c0980c4, DD10 on 5d76d91a.
2026-11-08 ~18:00 - [doors] KICK DOORS (own leaf models) REVIEWED + restaged, NOT installed: tools/kl_doors_1108.py + tools/kl_doors_clear_1108.py, stage C:/kl_build_1024/doors_1108/{DM01,DM03A,DM03} (2/1/4 doors).
Review fixes: clearance walk from every real ZSpawnPoint + escape boxes (leaf shut and swung 90/120 both ways) dropped DM03 host 1076 and DM03A host 6770 (they cut a corridor / room off); .HVK proven shape by shape (only the door slabs change, static order kept); report top name fixed (DM03A KL_Interact!3).
Pins: DM01 444a3ed6 / f3ed6155 / 8b34977b (unchanged), DM03A aa79d66d / d1a8dd0c / d700472e, DM03 33d1fa5f / 2971ec6d / a14e0134 (input = dm03cops stage, install it first). Undo byte-exact in scratch x3. GUESS: own model draws + DD kick sound plays; MIN_CUT 8 cells. Not benched (owner playing).
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
