# A Newer Perspective (ANP): briefing for Claude

Read this first. It is the hand-over from the previous Claude session, written 10 Oct 2026. Updated the same night after the move to Windows: setup, verification, the test loop and new facts. The original hand-over is in `docs/HANDOFF.md`. The detailed notes are in `docs/progress_and_format_notes.md`, `docs/ANM_FORMAT.md` and `docs/TESTING.md` (unattended tests).

## Who and how
- The project lead is **W** (he calls Claude **C**). Keep it informal and concise.
- W tests in game and reports back with screenshots. Give him specific things to check.
- W's standing rules:
  - Aim for a quality, seamless release.
  - Don't get sidetracked by tangents ("remember the bigger picture").
  - **Never modify the Dead Men install.**
  - Nothing from either game is redistributed. The converter runs on each player's own files. Never commit game data: `.gitignore` covers it, and `work/` is local only.
- JC (author of `R6C0/kl-merge`, Dead Men Fragile Alliance maps in Dog Days) shares notes. W has permission to use kl-merge. Credit JC.

## The goal
All of Kane & Lynch: Dead Men's (DM, 2007) story levels, playable inside Kane & Lynch 2: Dog Days (DD, 2010). Both use the same Glacier 1 engine; both exes are 32-bit with base 0x400000.

Later goals:
- DM multiplayer (Fragile Alliance) maps, guns and characters;
- AI upscaling;
- true first person and a free camera.

The old first-person mod is in `<DD>\_claude_removed\old_firstperson_mod`. Its overlay covered the screen.

## Machine (W's PC, Windows)
- DD: `C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days` (exe `kl2.exe`)
- DM: `C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men` (exe `kaneandlynch.exe`). **Read only.**
- ASI loader: `dinput8.dll` in the DD folder is Ultimate ASI Loader 9.7.0 (sha1 `828a620a…`; a copy is in `<DD>\KL_PortBackup\`). The DD folder also has `KL2Fix.asi` (DebugMenu, BorderlessWindowed, TrueAltF4; its LAA patcher is on) and `main.ini` (FreeCam, cheats).
- `kl2.exe` is a Steam CEG build. Its code is byte-identical to stock `KL2.exe.bak` and its timestamp and image size match JC's. The LAA flag is set, by KL2Fix's patcher. **Never change kl2.exe.**
- Tools on W's PC (installed 10 Oct):
  - Python 3.12 with pefile and capstone. Run it as `py`: `python` in a terminal opens the Microsoft Store stub.
  - Git.
  - MSYS2 32-bit GCC at `C:\msys64\mingw32\bin`.
  - VS 2022 Build Tools (C++).
  - ffmpeg.
- Paths are found automatically by `tools/anp_paths.py`, which looks in the Steam libraries and defaults the work folder to `<repo>\work`. To override:
  - `ANP_DD_GAME`, `ANP_DM_GAME`
  - `ANP_WORK` (the work folder)
  - `ANP_DD_EXE`, `ANP_DM_EXE` (for `re/`)

## Getting set up (done on W's PC, 10 Oct; verified)
1. Python 3.12 + `py -m pip install capstone pefile`.
2. `git clone https://github.com/R6C0/kl-merge.git work\ext\kl-merge` (private; W's GitHub login).
   - ANP uses only kl-merge's exact schemas, pinned to commit `8466319`: `re/schemas_dd.json`, `re/schemas_dm.json` and `tools/dd_enums.json`.
   - Later kl-merge commits replaced the two schema files with `re/kl2.json` and `re/kaneandlynch.json`, which use another format.
   - `setup_workspace.py` copies the pinned files into `work\ext\schemas` with `git show`.
   - The converter now **stops** when they are missing, unless `ANP_EXACT=0` / `ANP_ENUM_EXE=0`. It used to fall back silently to the old statistical conversion.
3. `py tools\setup_workspace.py --dd "<DD>" --dm "<DM>"` takes about 2.5 min.
   - It installs the schemas, extracts `scn/dd`, `scn/dm` and `cache/L01_Main.TEX`, and builds `dd_types.txt`, `dd_db.pkl`, `dd_arrlen.pkl`, `dd_enums.pkl` and `fxc/union.pkl`.
   - Its output is identical to the stats the tested builds used.
   - That required three fixes. It reads every stock scene: the F01–F09 and L00–L11 zips except Loader_Sequence (so `L00_Intro` too), plus the front end `Scenes\kaneandlynch.zip`. It reads them in name order, because ties keep the first scene. And `dd_types` comes from the class-stats and dynamic-pool tables (h4/h9), not just placed entities: every DM level has `0x100489` and `0x10048b` pools.
   - `X07` in the DD folder is a test clone of L07 (`clone_level.py`) and is not stock.
4. Convert level 1 (PowerShell): `$env:ANP_SET='CameraFogBegin=0.25'; py tools\port_level.py M01_A M01A M01`. This takes about 30 s.
   - It writes `<DD>\Scenes\Locations\M01\`. Set `$env:ANP_OUT='work\out_win'` to build somewhere else.
   - Verified 10 Oct: the Windows build of M01 is byte-identical to the 22:01 VM build in all 31 zip entries and every sound bank.
   - It refuses to write into the game folder while kl2.exe runs.
   - All 16 story levels convert: M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14 (on the VM; not yet re-run on Windows).
5. Loader: `loader\build.bat` finds the MSYS2 GCC and writes `build\ANP_Loader.asi`. To install it, copy it to `<DD>\ANP_Loader.asi`.
   - It builds cleanly on Windows (GCC 16.2, 171 KB) but has not been run in game yet.
   - `loader/ANP_Loader_b38.asi` (the VM build) is what is installed.
   - The game locks the file while it runs, so copy it only when the game is closed.
6. Test:
   - `ANP_autoload.txt` (`M01 1 12`) loads M01 about 12 s after launch; press Enter at "Buffering 100%".
   - The log is `<DD>\ANP_log.txt`.
   - Hook files (create in the DD folder): `ANP_quit.txt`, `ANP_shot.txt`, `ANP_nodes.txt`, `ANP_gui.txt`, `ANP_where.txt` (node indices; also logs Player objects and every registered use prompt).
   - Loads now take about 3 s.
7. Unattended tests (JC's KLHook TEST build + `kl_autotest.py`): see `docs/TESTING.md`.
   - Both stock tests pass on this PC: main menu, and Arcade Subway started from the menu.
   - They swap the ASI loader out for the run, so ANP_Loader and KL2Fix are not loaded during them.
   - Steam launch options stay **empty**. JC's documented options would make every launch boot into F01 and quit; scripts add their own options in memory (`CmdAdd`).

## Pipeline (tools/port_level.py)

| DM file | What happens to it |
|---|---|
| .gms | Entity tree: neutralise DM-only types; rebuild pools (h5), stats (h4) and dynamic pools (h9); overlap lists 0x70→0x80 stride; pathfinder int16→int32 |
| .prp | Properties. `prpconv.py`: exact relayout from exe schemas (kl-merge), statistical fallback from DD-level stats, `soldier()` manual mapping, enum fixes. `scriptconv.py` translates mini-cutscene scripts (`Player` becomes `Lynch`, the DD player section) |
| .prm | Geometry descriptors 32→48 bytes; baked vertex lighting dropped; environment lights scaled (`patch_environments`) |
| .MAT | Records 16→12 bytes; layers PostFilterZPass* → NormalAndLinearZ* |
| .TEX | Tables rebuilt; grafted menu textures |
| .fxc | Donor library plus aliases for DM permutation keys; the runtime alias is in the loader |
| SND/WHD/str | 6→10 languages; DM ADPCM dialogue is served as virtual PCM by the loader |
| .ANM | Dog Days F03 library plus the DM clips the level needs (`anm_merge.py`) |
| .oct .sgp .rmc .rmi .sgd .hrd .HVK | Copied as is; **they bake node indices** |

**Graft** (`graft.py`): DD L01's `AllLevels/Menu.zip` and `MenuResources` (DD menus), plus the climb MiniCutscenes. These hang under the nearest plain ZGROUP ancestor of the last group entity, so existing node indices don't move.

## Hard-won facts (don't re-learn these)

### Engine internals
- **Node table:** `*(*(0xe0ff90)+0xc)`, stride +4, base +0xc. Object at node+0x60, parent at +0x50. Static handle = `0x40000000|idx<<7`.
  - Order: ROOT; then blocks in preorder of group entities (type & 0x100000); within a block by slot = prio×8 + basetype; then entity order.
  - `clusters.node_order()` reproduces this exactly. Inserting entities anywhere but the tail shifts baked indices and crashes the game.
- **Stored 3x3 matrices:** identity is stored as `[0,0,1,0,1,0,1,0,0]`. An actor or PosObject faces the third row. For a yaw-only facing f, stored = `[-fz,0,fx, 0,1,0, fx,0,fz]`.
- **Prim bounding box:** PRM chunk 0x70100, floats 8..13.
- **Property schemas:** GetProperties is vtable slot 11. Record member offset = node+0x10, **plus 4** to get the real object offset.
- **Anti-tamper:** 0xa8e3cb is a benign fault (Steam probe). Hardware breakpoints kill the game.
- **Valve CEG code-integrity check** (JC: kl-merge `re/antitamper.md`; ranges in `klhook/klranges.h`):
  - kl2.exe hashes 85% of `.text` and 66% of `.rdata`.
  - In a REAL session (Arcade/FA started from the menu) with a hashed byte changed, the game ends itself with `ExitProcess(0x8000dead)` about 30 ms after the level loads.
  - Not hashed: import slots, `.data`, the heap.
  - **All seven of ANP_Loader's code patches lie in hashed ranges**: 0x6d100f, 0x4f8a60, 0x71166d, 0x51f1a5, 0x8a40fe, 0x927b44 and 0x446673. ANP's autoload and direct boots have not tripped it. Stock Arcade/FA with ANP_Loader installed probably will.
  - Before a release, move these patches to import-slot wrappers, data writes or unhashed pages. JC's SHIP hook works that way.
- **LAA:** JC says not to make kl2.exe large-address-aware, because the engine tags pointers with the top bit. W's exe *is* LAA (KL2Fix's patcher). That is an untested lead for the sound bug.
  - Test it without touching the exe: log or reserve addresses ≥ 0x80000000 from the loader.
  - JC's SHIP hook also reserves address space (`[Memory] ReserveMB`).
- **Memory:** kl2.exe is not large-address-aware. A load allocates scratch, .fxc, .prm and .ANM (each size + 0x60000), then the whole .WAV. Keep the ANM small (that is why the merge is filtered). Do NOT set the 4 GB flag. The PRM chunk table holds at most 73,728 entries.

### Soldiers (ZSoldier = ZSoldierRout)
- Layout: 4 enums, then 14 floats in DD (9 in DM).
- f[3] (field 7) = health; ≤ 0 means invulnerable.
- Fields 9..12 = health factor per difficulty (1.0). Wrong values here made enemies unkillable; that's fixed.
- Skill presets apply unless the skill is eCustom.

### Enums
- Any value in DD's exe enum tables is kept.
- Except `ZMercSquad` (Merc_04 → Kane makes Lynch the buddy squad) and ZROOM (0x100021) inside/outside classes, which keep the old observed-value mapping.

### Animations
- DM and DD .ANM differ only in clip record size (0x50 vs 0x68). Bones are remapped by name.
- DB lookup = first DB whose name *ends with* the requested name.

### Climbing
- **DM climb is a free move, not scripted** (static RE of kaneandlynch.exe, 11 Oct; W's DM playthrough: Kane climbs crate stacks anywhere with W+E):
  - `ZFFPlayerMovementClimb` = player movement id 11 (ctor 0x60a920, TryActivate slot 14 at 0x605b50). Not a level entity; all values are exe constants.
  - Trigger: use held (two consecutive calls) while pushing forward and blocked (proxy speed < 75% of 500 cm/s), not in cover or an action, ≥ 0.5 s since the last action.
  - Probe: 4 down-rays from feet+310 at 25/40/55/70 cm ahead (mask 0x20, layer 11); clearance ray at h+15 (mask 0x28; hero-only walls 0x108 block it); head room 180 cm; wall-face ray at h−1. Rigid bodies abort. Any collision with flag bit 0x20 is climbable (crates 0x72, van 0x60/0x172). Names like `HeroClimb` mean nothing to the engine.
  - Class by ledge height h: 25 < h ≤ 120 Low (start 81 cm back from the face; Sprint_Low when sprinting), ≤ 170 Medium (47), ≤ 220 High (47). `/Movement/Climb/Down/*` is never used by the player (dropping is a fall).
  - Motion: root motion of `/Movement/Climb/Up/<class>`, warped so the player is at the start at clip event 5 and at start + (0, h, 0) at event 6 (player vt +0x20c, 0x526620). Keeps yaw.
  - The prompt is level-scripted (IngameBriefing `100_ClimbVan`), not code.
  - DD raycast: collision world `*(0x138c868)`, ZCollisionWintel vt slot +0x2c = 0x7daa80, same 9 arguments as DM. DD's result layout is not verified.
  - Scripts: scratchpad `dmclimb\`. Van top ≈ 202–207 (High from the ground); shelter roof 346 = Medium from the van roof.
- DD has no player climb class.
- **The loader climb WORKS LIVE in game (11 Oct 08:47 and 08:50, unattended, `scripts\smoke_climb.py live`, evidence `work\smoke\climb_1011_084723\summary.json`, in-game D3D shots `work\smoke\d3d_climb_1011_0850\`).** Five of five spots passed in two separate runs:

  | Spot | Class | Height |
  |---|---|---|
  | Van rear to roof | High | 200 |
  | Van roof to shelter | Medium | 140 |
  | Crate_C | Low | 97 |
  | Crate_A | Medium | 128 |
  | Crate stack | High | 177 |

  Each ended within 2–4 cm of the computed Final, with no snap, the camera following and control back. `ANP_climb.txt` is now `live`.
  - Desktop capture is black while W's screen is off; use `scripts\d3d_shots.py` (loader back-buffer shots via `ANP_shot.txt`).
  - Test teleport: `ANP_tp.txt` = `x y z yawDeg`. Spots are in `scripts\climb_spots.json`, made offline by `scripts\hvk_ray.py`, a .HVK ray caster that matches the game to 0.2 cm.
- `climbs.py` rebuilds a climb as:
  - a **ZPlayerAction** use prompt on the DM hint box, moved to the climb start;
  - a grafted L01 MiniCutscene whose `Lynch` (player) section `act`s DM `/Movement/Climb/...` clips snapped to its PosObjects.
- ZPlayerAction members:
  - +0x50 text key; **+0x54 enabled**; +0x58 use-geom path; +0x60..+0x70 enums; +0x74/+0x75 bools.
  - Init is slot 13 (0x4c4de0). It registers only if `gameMgr(0xdd265c)+0x828 != 0`, appending to the list at gameMgr+0xa20 and registering a HUD slot via gameMgr+0x15e0.
  - The message handler is slot 26.
  - The box volume's last bool before its sizes is 1 on always-available prompts.

### Lighting
- DM Environment lights (0x80000d) are about 2x DD's values. They are scaled by `ANP_ENV_SUN` 0.45, `ANP_ENV_AMB` 0.55 and `ANP_ENV_CHAR` 0.9.
- Light and postfilter chunk formats are identical in both games.

### Loader
- Throttles `GetForegroundWindow`: kl2 0x6f4220 nudges the cursor every millisecond. That one change took loads from minutes to about 3 s.
- **Climb** (`loader/climb.inc`, added 11 Oct, built, **not yet run in game**): Dead Men's W+E climb as a loader move.
  - Mode file `<DD>\ANP_climb.txt`, re-read within 1 s of a save. First word `off`, `dry` or `live`; **no file = `dry`**. `dry` only probes and logs; `live` plays the clip.
  - Options after the mode: `warp=end|dm`, `vehicle=action|snap`, `needblock=0|1`, `fwd=1|-1`, `cam=0|1`, `snap=0|1`, `trace=0|1`. Example: `live trace=1`.
  - Frame hook: kl2's IAT slot for `steam_api!SteamAPI_RunCallbacks`, filtered to the gameplay call (return address 0x87aa82). No kl2 byte is changed, so it is CEG-safe.
  - Live climbs use a real `ZFFActionVaultOver` (type 0x2B) whose vptr points at a loader-owned vtable copy.
  - Every engine call runs inside a VEH fault guard. A `climb: FAULT` line disables climbing until the game restarts.
  - Log lines start with `climb:`. The test steps are in `docs/TESTING.md`.

### JC's notes still worth checking
- Bullet-hit crash at 0x4c34b3 (bone id byte +0x3e must match the skeleton table).
- First-execution crash at 0x4098a1 (ExecutionBloodSpatter define order).
- Weapon-handling anim folders come from the item-enum table at 0x154a650.
- Discord's overlay hook has crashed the game.

## All 16 story levels load (11 Oct 14:44)
- M01–M14 incl. B parts each survive 60 s in level (helper sweeps; `work\helper\REPORT.md`).
- **Crash fixes that got there** (converter, all default on; details in the workflow journals):
  - vehicle-only events on neutralised owners dropped (`VEHICLE_ONLY`, `ANP_CAR_CHILD_EVENTS`, `ANP_FAILSAFE13B`);
  - DM PIP cutscene sections dropped (`ANP_DROP_PIP`);
  - DM layered WHD groups relaid; SND type-1 relayout;
  - duplicate particle-pool names made unique (`ANP_ALLOC_POOLS`);
  - DM anim DBs back-filled with DD paths (`ANP_ANM_BACKFILL`);
  - checkpoint index 0 renumbered (`ANP_CP_INDEX`);
  - loader guard for a null light block in M09 (`boneslights_guard`).
- **Graft host (`ANP_GRAFT_HOST`, default new):** the last ZAllocMany pool is retired in place and rebuilt under a new tail group `ANP_Tail` with the grafted wrapper. No more heap overflow from slot 84, and every DM node is back on its own index (the old graft had shifted 1–36 nodes per level).
- **Player filters:** DM and DD number them the other way round.
  - `ANP_ECPS_SWAP` (TriggerBox/EndOfLevelTrigger) and `ANP_PFILTER_SWAP` (CCameraBox, SneakTrigger, PlayerAction, OnscreenMessage, weapon pickups) swap the names.
  - `ANP_PA_GENERIC` gives converted PlayerActions eNoFilter/UA_GENERIC.
  - CamOscillator and TriggerPsychoMode keep their names.
- **Player-filter fix confirmed in game (15:22, `work\smoke\trig_M01_1011_152039`):** leaving the start area fires `TB_PlayerLeftStartArea_01`, a KANEONLY box that never fired before. Its minicutscenes `010_RunToBackUp` and `008_MC_YellToPlayer` start at that moment.
- **Test god mode:** `<DD>\ANP_god.txt` (`loader\godmode.inc`) sets kl2's unused god switch `0x1535a2c` (.data; 1 = no damage, 2 = can't die). It doesn't stop fall deaths.
  - Teleport targets need the real floor height. `scratchpad\findpos.py`'s world positions are wrong (no collision under them); use `scripts\climb_spots.py`-style positions or `scripts\hvk_ray.py` to check.
  - An idle unattended player otherwise dies ~60 s after M01's intro. Without a reached checkpoint, the level restarts from the intro.

## CEG-clean loader (11 Oct 17:08, verified in game)
- **ANP_Loader now changes NO kl2 code byte by default.** `scripts\smoke_ceg.py` compared all 225 hashed ranges in memory against kl2.exe on disk: every difference is NOT ANP. 17 of them belong to **KL2Fix** (W's mod), including 0x7b04b6 and 0x7f5611, all redirecting into a module at ~0x65fa0000. W should know KL2Fix itself writes hashed bytes.
- **The 6 old patches are replaced** (`<DD>\ANP_guards.txt`; `legacy` brings any back):

  | Patch | Replacement |
  |---|---|
  | CListUser 0x4f8a60 | VEH (`cl=veh`). It fired in M01 because DM AO volumes (0x800011e, pool slot 3) were neutralised to ZSTDOBJ (slot 1), which moved static nodes in 14 of 16 levels. Fixed offline 11 Oct (`ANP_NEUTRAL_SLOT`: they become 0x800001a), and the build validator `tools\ovlcheck.py` (`ANP_VALIDATE`) now fails any build that moves a node. Not yet re-checked in game |
  | FX alias 0x71166d | Offline data: `scripts\fxmiss_harvest.py --apply` → `fxc\miss_<ID>.txt`, applied at build |
  | gfx 0x51f1a5 | VEH on the int3 |
  | wrap 0x8a40fe | Watchdog (`wrap=watch`) |
  | coll 0x927b44 | VEH |
  | snd 0x446673 | VEH |

- The start-up log prints `CEG: kl2.exe code bytes changed by ANP_Loader: none`.

## Crew orders (11 Oct 16:31, in game on M02)
- `loader\squad.inc`, configured by `<DD>\ANP_squad.txt` (`mode=off|probe|dry|on`; set to `on` for play).
- **Keys:** `1` Follow, `2` or middle mouse Fire at, `3` Defend, Tab / Shift+Tab next/prev merc. Tap = selected merc; hold (≥ 0.25 s) = all.
- **How it works:**
  - Follow uses DD's own `0x4c3900`, which includes the refusal, hand signal and voice.
  - Attack uses soldier slot 83 (`0x831850`, which takes a HANDLE). Defend uses slot 79 (`0x760e50`) with a per-merc LOS check.
  - Recruitment: DD skips recruiting the story buddy in no-session mode (kl2 `0x615f59`), so squad.inc calls DD's Recruit `0x908040(sc, body)` for every live merc, with a duplicate guard.
  - M01 refuses all orders, as in DM.
- **Proven:** recruit → recv=1; follow issued; attack-nearest sets Lynch's attack target. Defend correctly refused with no LOS.
- **Test driver:** `scripts\smoke_squad.py <L> on`, using the command file `ANP_squad_cmd.txt`.
- **Not yet done:** the CommandDisplay2 HUD, the map, and acknowledgement voice ids (DD speech ids differ from DM's).

## Hints and objectives (11 Oct 15:52, in game)
- **IngameBriefing → DD OnscreenMessage** (`ANP_BRIEFINGS`). Same AITrigger toggle logic and field reorder. Hints for features DD lacks are dropped: ObjectiveLocator/map, squad commands until crew orders land, give-weapon.
- **Ingamemap → DD Objective** (`ANP_OBJECTIVES`). ObjectiveReminder, MapControl and IngamemapLoot are not mappable.
- **Seen in game:** "FOLLOW LYNCH" objective popup after M01's intro (`work\smoke\level_M01_1011_155059`).

## Cutscenes (11 Oct 12:28: DM's M01 intro PLAYS in game)
- **Evidence:** in-game shots in `work\smoke\level_M01_1011_122739\` show Kane and Lynch in the transport, the crash, Kane climbing out and the police. `cutdiag` shows 0 of 187 MiniCutscenes dead; 010_CUT_Transport ran, then chained into 010_IntroCutScene_01.
- **Fixes, all converter, all on by default:**
  - `ANP_MERC_IDS`: Lynch = DD 'Kane' buddy; other mercs keep distinct values.
  - `ANP_BUDDY_KANE`: DM's buddy `(Actor| Merc_04|…)` section becomes DD `(Kane| Kane|…)`, id −5, with `_dep` renumbered. Needed because the buddy registers at gameMgr+0x4cf0 about 250 ms AFTER the cutscene squads initialise, so a squad-bound Actor never finds him. A Kane section binds to the buddy directly.
  - `ANP_SCRIPT_RESTORE`: keeps playermode, camprofile, camfade, setvariant, setfollow and throwgrenade.
  - `ANP_DROP_PIP`: drops DM PIP sections, which kl2 int3s on.
- **Diagnostic:** `<DD>\ANP_cutdiag.txt` (empty = M01's 4 camera cutscenes; else one name per line) turns on `cutdiag:` log lines from `loader\cutdiag.inc`. Its one-time heap scan stutters for a few seconds, so leave it off for play.
- **Testing:** Enter is kl2's cutscene-skip key. `scripts\smoke_level.py` stops pressing Enter once cutdiag sees the InGame state (or use `SMOKE_ENTERS=1`).

## Campaigns and menu (11 Oct; W: DM and DD must coexist)
- Main-menu rows 'Play Dead Men' / 'Play Dog Days' / 'Play Dead Dogs'. Dead Dogs is option A, 'The Full Story': DM's 16 scenes then DD's L00..L11, one saga with its own save.
  - Built by `tools\anp_menu.py`. Output: `work\out_menu\ANP\ANP_Patch01.zip` plus a loose `ANP\menu\frontend.xml`; install both to `<DD>\ANP\`.
  - It also adds the three rows as the FIRST rows of KL2Fix's CheatMenu, because W's KL2Fix has `DebugMenu=1`, which opens CheatMenu instead of MainMenu, and Back there closes every window.
- Loader code is in `loader\campaign.inc`, configured by `<DD>\ANP_campaign.txt` (sample: `loader\ANP_campaign.sample.txt`). All of it is import hooks or heap/.data writes; no kl2 code bytes are touched.
  - **Menu delivery:** the game loads the patch zip with MSVCR90 `fopen` (the CreateFileA open is only an existence probe), so `fopen` is hooked. `frontend.xml` is also served directly through a copy of the file system's vtable (`[0xdd263c]`, wrapping `+0x34` size and `+0x68` read).
  - **Scene routing:** MSVCR90 `strncpy` hook at `dst 0x156b6f5`, borrowing table entry 12. Pseudo-ids: `DMCN` = Dead Men continue, `DGNW`/`DGCN` = saga new/continue.
  - **The 0x6d100f code patch is gone** (`LegacyResolver=1` brings it back).
  - **Other pieces:**
    - save redirect in DM/Dead Dogs mode to `%LOCALAPPDATA%\A Newer Perspective\saves\...`;
    - profile reload on return to the front end;
    - achievement guard (vptr swap);
    - `ANP_progress.ini`;
    - Dead Dogs hand-over to L00;
    - ExitProcess CEG tripwire.
  - **SceneChanger chain:** `port_level.py` rewrites DM paths, so M01→M02→…→M14→front end. Untested in game.
- **Proven in game (10:09–10:12, `scripts\smoke_menu.py`):**
  - our menu XML is used and our rows show;
  - 'Play Dead Men' → Dead Men page → Continue loads M01 in DeadMen mode (`scene request 'M01' (asked 'DMCN') from 00869d1b (SetId)`);
  - the DD `0.kls` SHA-1 is unchanged (`2AA311B1…`) across 6 runs.
- **Open:**
  - the Dead Men page layout overlaps the DD logo;
  - arrow keys didn't move focus on our page;
  - one run crashed ~26 s into M01 off the main thread at 0x695e199b in an unnamed module, not reproduced; exception logs now print the module and thread.
- **Intro movie and funeral (11 Oct evening, built offline, NOT yet run in game; outputs in `work\out_fun\`):**
  - `tools\anp_movie.py` builds `<DD>\Movies\ANP\M00_Intro.bik` from DM's five `M00_Intro*.bik` (DD-style 7 audio tracks, ids 0,2,4,1,3,6,8; `--install` writes it into DD). Must be a loose file: a .bik only inside a zip crashes kl2 at 0x4df0b8.
  - `anp_menu.py --intro auto|on|off` (auto = on when that file is installed): New game / New saga open `ANP_DMIntro` / `ANP_DGIntro` (MoviePlayer, `OpenWindowOnFinish` → `*Go` window with a fallback LoadScene button after 1.5 s).
  - Loader `IntroMovie=1`: `_BinkOpen@8` / `_BinkClose@4` import hooks; ~200 ms after the intro closes, `do_load("M01")` or `do_load("DGNW")`. kl2 turns `\` into `/` in movie paths (0x5dfb50) but keeps case, so the pages use `Movies/ANP/M00_Intro` (Dead Men) vs `Movies/ANP/M00_INTRO` (Dead Dogs).
  - Funeral: `py tools\port_level.py M07F` (`SPECIAL_SCENES`) → `<Scenes>\CutScenes\M07\M07_A_Funeral.*` (path must keep 'Funeral': kl2 0x881350/0x696c40 skip bookkeeping for it, as DM does). `ANP_SKIP_FUNERAL` now defaults to `auto`: M07's SceneChanger → `CutScenes/M07/M07_A_Funeral.zip` only when the converted funeral exists in the build's output tree or in DD; else straight to M08.
  - campaign.inc: `CMP_ALIAS` id `M07F` → that path (ANP_load.txt, Continue, progress; `CMP_DM_ORDER` has M07F between M07 and M08).
- Mouse clicks via SetCursorPos/mouse_event don't reach the game (DirectInput mouse); drive menus with keys.
- **Test hygiene:** `ANP_guinames.txt` scans memory on the main thread and freezes the game for ~20 s; use it once at most.

## Where M01 stands (last tested build, 10 Oct ~22:00)
- **Works:**
  - loads in about 3 s and is stable;
  - enemies die (confirmed by W);
  - Lynch followed well in earlier builds;
  - police AI engages;
  - death and respawn work.
- **Climb at the getaway van: no prompt yet.** The fixes for the enabled flag are in. The next step was to have W stand at the van while Claude writes `ANP_where.txt` with `566 22095 10840 10456 19784`:
  - 566 is the prompt box (`Specials!IngameBriefing!ClimbBriefTriggerON`);
  - 22095 is the first climb PosObject;
  - 10840 is the van's HeroOnly collision;
  - 10456 is the van group;
  - 19784 is the climb MiniCutscene group.

  The log then shows the player's position, whether the prompt registered (`+828`, `playeractions`, `en`, `init`) and the box's real coordinates. The box and climb positions come from bounding-box maths, so they may be off.
  - Van (HeroOnly bbox): x -3316..-3055, y 0..202, z 2230..2829. Rear doors at z ≈ 2250.
  - Shelter roof: about 346 high, z 2638..2884. Fence at z 2860..2886.
  - Note: the van is upright in game.
  - Note: node indices change whenever entities change; recompute with `clusters.node_order`.
- **Installed M01 is the 22:01 VM build.** A Windows rebuild is identical, except that the Japanese/Russian `LS` WHDs in the game folder are stale copies from 05:37. That bug is fixed: they are now refreshed on every build.
- **SOUND FIXED (11 Oct 11:00, proven by WASAPI-loopback recordings, `work\backup\sndr2_1011_104551\results.json`).** M01 is audible 81/84 s, the same as stock L01.
  - **Cause:** DM SND type-1 sound records are 0x30 bytes; DD reads 0x40. kl2 0x7a1200 reads the volume % at +0x2d from DM padding (0xCD → −51 → clamped to 0%), so every level sound played at gain 0 (proof: `gainfloor=0.2` on the old build makes it audible). The anim merge was never the cause.
  - **Fix:** `tools\sndconv.py` relays each record to DD's layout (`ANP_SND_T1`), converts the reverb presets (`ANP_SND_REVERB`), and re-strides `*_LS.SND` (`ANP_SND_LS`). Earlier fixes are still in: LIP flags, layered groups in DD's 0x48 layout, loader LIP serving and `.str` zero-fill.
  - **Loader switches** (`<DD>\ANP_sound.txt`): `vpcm`, `strhook`, `al` (OpenAL import hooks plus an `al:` stats line), `gainfloor`, `nanfix`.
  - **Non-English dialogue (11 Oct ~18:15, offline only):** `ANP_SND_LANGS` (default 1; `=0` gives a byte-identical old build).
    - DM ships Eng (`PC_Def.str`) plus Ger/Fre/Spa/Ita (`PC_<Lang>.str`); every localized wave has 5 items.
    - `sndconv.snd_expand_langs` writes DD's 9-item layout: Dut/Rus/Pol/Jap get English. The old build read garbage for those four.
    - `whdconv` now gives language-file ADPCM records virtual PCM too; before, about 30% of non-English lines couldn't play.
    - kl2 takes the language from Steam (0x665300; 0 Eng, 1 Ger, 2 Fre, 3 Spa, 4 Ita, 5 Dut, 6 Rus, 7 Pol, 8 Jap). The Audio option `Audio_LanguageEnglish` forces English.
    - Each decoded language line matches its DM source (`work\out_lang\lang_check\`).
    - The M01 SND grows to 2.59 MB; DD's largest stock SND is 2.46 MB, so it needs a load check.
  - The old note follows (OBSOLETE: the cause was the SND record size above). Only the first dialogue stream (about 1 s) played, then nothing; W reported no gunshots or ambience. The anim library is now filtered (+2.6 MB instead of +13 MB) and ZSoldier speaker names are restored.
  - The loader logs only the first 5 virtual-PCM reads (by design), so `ANP_log.txt` can't show how long speech played.
  - The snd guard's counter (`g_sndZero`) is never logged.
  - Isolate the cause:
  1. build with `ANP_ANM_MERGE=0`;
  2. then with the merge but DM-only clip event ids stripped (DM uses 1, 13–19, 21, 24, 30, 37, 38, which DD never uses; the intro clip Sc4_INSERT_Lynch has event 21);
  3. then `ANP_SOLDIER=0`.
- **Intro cutscene** doesn't show (it may be skipped or aborted). It's tied to the sound issue above.
- **Lynch follow:** a TriggerBox mapping fix (`eTGS_AllInside` → `eTGS_AllDead`, "KaneIsDeadFollowHim") may change his behaviour.
- **Pause menu:** Escape pauses and the window opens, but nothing draws.
- **Other open issues:**
  - brightness: just scaled down, awaiting W's verdict;
  - gun hold: DD grip clips on DM weapons and attachers;
  - alt-tab crash;
  - missing shaders: ScatterNew, GlassSurface, rigid Glow.

## Next steps (rewritten 11 Oct ~18:00; the M01 section above is the 10 Oct history)
Done since 10 Oct: free climb (loader, live), sound, the M01 intro cutscene, all 16 levels load, gun fit (`tools\gunfit.py`), the DM HUD and fonts, crew orders, the coexisting campaigns menu, and the CEG-clean loader. The Esc/settings crash is fixed (0x900ff8); pause-menu drawing comes from the OSD graft and needs a recheck.
1. **Helper queue (`work\helper\TASKS.md`):**
   - finish the 5-minute long sweep of all 16 levels on `out_ovl`;
   - then install `work\out_fun` and test it in game (intro movie → M01, the Dead Dogs intro, M07 → funeral → M08).
**RESUMED 12 Oct (W: "continue").**
   - Loop cron 2849ee1d (renewed 13 Oct ~16:00; expires ~20 Oct; :07/:27/:47). The helper is now session `a-newer-perspective-01`.
   - Workflows relaunched: `anp-m03-chase` (wf_7ae1b77b-813) and `anp-dm-mechanics` (wf_b4b8b8a5-c72, builds per feature in `work\mech\<feature>`, integrated build in `work\out_mech_all`).
   - The helper is running the out_rel2 long sweep, then the funeral test.
   - `docs\HANDOFF_CODEX.md` is the best organised findings doc; use it as a briefing for any agent. W dropped the Codex plan (12 Oct): don't mention it again.
   - **Mechanics built (12 Oct, workflow `anp-dm-mechanics`; integration and rebuild into `work\out_rel3` by `anp-mech-integrate`):**
     - **`give.inc`:** key 4; `ANP_give.txt`; `ANP_give_cmd.txt`.
       - Gives the held gun to the selected/nearest merc within 300 cm (DM rules; refuses rocket launchers and gas/flare launchers); swaps if he already holds that type.
       - DD building blocks: ZActor::AddItem 0x4e3fa0 (`actor+0x5e0[slot]`), player current item 0x727b40, ZFFPlayer::RemoveItem 0x633250, AddItem 0x6020d0.
       - Slot for each item type: 0→3, 1→0, 2→1, 3→2.
       - The DD WeaponFilter (0x8fa1a0) with bool 0 checks `actor+0x5e0[slot]` against the template's registry id.
       - Raises monitor event 18.
       - `ANP_GIVE=1` (prpconv: DM list 19 → DD 18, repeating; WeaponFilter pass off) is the faithful mode, still to be proven in game.
     - **`grenade.inc`:** G; `ANP_grenade.txt`.
       - DD removed the player throw (input 0x4aa410 only clears the bit), so the module uses the NPC release path: 0x477650, item vt+0x2cc, 0x659be0.
       - It raises event 30.
       - Equip assist: DD `equip` (0x7cd310) refuses a grenade when two guns are held.
       - `ANP_PLAYERMON_THROW`: DM 12/13/20 → DD 30.
     - **`rappel.inc` + `tools\rappel.py`:**
       - **DD has DM's full rappel system:** ZRappellingBox vt 0xbc23bc; ZFFPlayerMovementRappel vt 0xbb5ebc at player+0xdf0.
       - It crashed because Kane/Lynch lacked `/Movement/Rappelling/*` clips (lookup 0x59d550 returns NULL) and because DD gives single player the SECOND callback half.
       - `ANP_RAPPEL` adds the clips and copies the callbacks into both halves. Loader modes dry|native|live|auto (default native after integration).
   - **out_rel3 BUILT (13 Oct ~16:15; integration reviewed; NOT yet run in game):**
     - All 16 levels + M07F, rc 0, 0 nodes moved, 0 bad clip sound ids.
     - Kane and Lynch have all 15 rappel paths in every level; the callback halves are fixed (M03/M08/M09/M12/M13).
     - Loader `work\out_rel3\ANP_Loader.asi` (sha1 90987205…). Review fixes applied by the lead:
       - climb refuses only while kl2's rappel prompt is up (+0x1f6c, not the stale +0x1f68);
       - RpTry clears +0x1f68 before each stock TryActivate;
       - give-back first clears the merc slot and never double-owns;
       - grenade refuses during a rappel (movement 0x10) or a MiniScene.
     - `work\out_rel3_give\M02` is the `ANP_GIVE=1` faithful variant.
     - The helper (`a-newer-perspective-01`) is installing and testing: give, rappel M02/M09, grenade, M03/M03B, M01 regression.
   - **out_rel3 IN GAME (13 Oct 16:19–16:56, helper; installed; 0 crashes in 5 launches; backup `work\backup\install_1013_161754`):**
     - **Give PASS (mechanics):** `give: done … merc=1 slot 0`. Event 18 had no monitors, because the installed M02 is ANP_GIVE=0. Next: the faithful `out_rel3_give\M02` test.
     - **Rappel PASS:**
       - M02: native descent in 6.4 s, states 0→1→3→4→5, landed by TriggerBox_PlayerDidRappel.
       - M09: no crash. A multi-stage wall-jump descent (S/W presses, about 820 cm each).
       - **The M09 level reset about 20 s after landing**; being investigated.
     - **Grenade FAIL:** `release done … no ammo used`, no gas cloud, item type=3. Workflow `anp-grenade-fix` is on it.
     - **M03:** can't be tested unattended (gunfire raises the alarm → mission fail loop; no crash).
     - **M03B:** the beam to the tunnel WORKS; MC_02 ran.
     - **M01 regression PASS.**
     - Funeral PASS again (out_rel2).
   - **Rappel crash ROOT CAUSE CONFIRMED (13 Oct, workflow `anp-rappel-crash`, verified):**
     - Activate (slot 15, 0x6db3b0) gets `/Movement/Rappelling/Start` through vt+0x90 0x7dda80 → 0x59d550 (player DB `[player+0x84]`, names `[player+0x80]`). It stores NULL at +0x1ff0, and 0x5a5030 then faults at 0x5a503a.
     - The player DB is `animationdatabase#Kane`. The clip ids are cached by slot 20 (0x77ac70): Start/Jump_Start/Wait_On_Wall/Jump_Loop/Jump_End at +0x1fe4..+0x1fec.
     - Update NULL-checks except Jump_End (0x8256b9). That clip is present in out_rel3.
     - out_rel3 is fixed in M02/M03/M08/M09/M11B/M12/M13 (11 boxes; every callback path resolves). No other NULL path was found.
     - **Expected log:** `native Activate done: clip=00000000` is normal (Activate clears it at 0x6db63d; slot 19 0x41e9b0 refetches it). If the state stays 0, the player is stuck at the edge (not a crash).
     - No stock DD level uses a RappellingBox.
   - **Faithful M02 in game (13 Oct ~18:13, out_rel4_give):**
     - **Steps 1–5 PASS:** 010 drops the Spas and adds the Remington; give Remington (event 18 registered); P90 020; 021 drops the USP and adds the Taurus; give Taurus (Lynch slots 0:16 1:2).
     - **Stalled at step 6:** the dropped guns get DD world-pickup prompts ('PickUpWeaponNoText') that beat the level's USP prompt at the trunk, so 022 never starts. Rolled back to out_rel4 M02.
     - **Fix (lead, 20:55):** equipassist `drop=remove` (default) uses ZFFPlayer::RemoveItem 0x633250 instead of the world drop. Loader `work\out_rel4b\ANP_Loader.asi` (sha1 3DC59566…); the helper is re-testing.
     - Also seen: the give range of 300 cm is tight; select after 021 didn't apply; "P900" label text.
     - **Rerun with drop=remove (20:50): steps 1–7 PASS** (the USP prompt shows, 022 runs). It stopped at 025 cover practice because the test never took cover.
       - The 025 gates are DM lists 3/4 (cover stand/crouch → DD 3/4), 5/6 (aim in cover → DD 9/10) and 9/10 (blind fire → DD 13/14), all live.
       - No M02 monitor uses the weapon-switch lists (14/15/17). The "Press Q" hint is not a gate.
   - **20:48:** `anp-appendage-fix` and `anp-revive-build` both died on the spend limit (session reset 20:40); relaunched (wf_c279b17d-f22, wf_80a93ab7-95f).
   - **Revive IMPLEMENTED (13 Oct ~22:00):**
     - `loader\revive.inc` (910 lines) + `loader\ANP_revive.sample.txt`, wired: climb refuses while the revive prompt is up; give refuses a DOWN merc; squad `sq_canrecv` skips DOWN mercs.
     - Build `work\out_rev\ANP_Loader.asi`; the build check matches kl2 (26 code + 12 table checks).
     - The census of all 16 levels passes (Kane has the Heal clips; every DB has the 40 Down_Not_Dead clips). Test commands: `down N`, `heal N`, `bleed N`.
     - The review found 8 defects: leftover mask (invulnerable), heal on a corpse, narrow resurrection guard, zombie from a raw life 0 write, M14 NotHealable, dry still advancing the anim RNG, PENDING flood, buddy=dm.
     - Fixed (workflow `anp-revive-fix`, 11 items):
       - gates are checked before the mask (refusal back-off 10–160 s, no mask);
       - undeath: 0x7e72d0(2) then (0);
       - default `exclude=M14:2` (Shelly, Merc_01);
       - the anim RNG [[0xdd2640]+0xb30] is saved around lookups;
       - `revive_is_down()` acts only when live;
       - buddy=dm sets +0x124=2 while DOWN.
     - Note: ZFFActor vt+0x654 (0x410a30) returns +0x64c; the real vehicle test is +0x774 in 0x70f330.
     - Re-review found 3 more, fixed in `anp-revive-fix2` (reviewed PASS):
       - **OnDeath swallow:** `saw0` → SetLifeState(0x6cee20)(0) once, else the raw path;
       - **DEAD hold while the dying task is current:** now held whenever the task is valid (lead fix: ZBecomeRagdoll Start clears +0x64c at 0x67727b);
       - **same-scene restart:** merc list empty → forget with no write, in off mode too (lead fix).
     - **Known, rare:** a one-frame race (DD SetLifeState(0) plus heal End in the same tick) could run OnDeath twice (double fail). It needs a heal on a merc killed by DoT or a script.
     - **revive.inc is ready for its staged in-game test** (no file = dry).
   - **Revive (13 Oct ~19:30): design `work\revive\DESIGN.md`, critiqued.** It is being implemented as `loader\revive.inc` (workflow `anp-revive-build` → `work\out_rev`), "Variant B + HP floor":
     - Each frame for listed mercs: `script+0x124=1` (DND force) and `body+0x5cb=0`. At HP ≤ 25%: mask 0x4000 plus `0x688190(s,NULL,1)` retries. Hold DOWN via DND task+0x14.
     - Bleed-out 60/45/30 s by difficulty, then native Die → MF_01.
     - Revive: prompt 0x1b shown via 0x4c06c0. The heal is OUR start: `P+0xd34`=body, then vt+0x384(0x12)/vt+0x370; the SP heal scan 0x7aaaf0 wipes `P+0xd34` every frame. The native heal sets HP to max.
     - Key facts:
       - DM fails every merc death with MF_01 (MF_05 is the M05 level controller only).
       - `0x70e0e0` refuses DND (= instant death) when in a vehicle/carried, or when a 16-direction 100 cm clearance probe fails, regardless of force.
       - Heal End (0x4ea150) SetLifeState(1)s unconditionally, so never Die during a heal.
       - `act+0x1c/+0x20` are float seconds.
     - No file = dry.
   - **13 Oct ~19:00: out_rel4 READY:**
     - all 16 + M07F, explode fix (218 events by meaning; 0 moved);
     - loader `work\out_rel4\ANP_Loader.asi` (sha1 2E2FD6CA…) with equipassist (review fixes: PRE/POST single drop, no calls on a failed build check, task +4 invalid check), failwatch, give swap-reserve fix, squad recruit option;
     - `work\out_rel4_give\M02` = faithful M02 (ANP_GIVE=1).
     - The helper is installing it and running the full faithful M02 chain.
   - **13 Oct ~18:30:**
     - **ANP_EXPLODE_FIX applied** to prpconv.py (`Conv.explode`; M01 10/10 by meaning; validator ok). Full rebuild running → `work\out_rel4`.
     - **M02 equip:** DD's player `equip` (0x7cd310) gives nothing when 2 guns are carried and has no replace flag; DM's (0x6fb920) drops the same-type gun (DropItem) then adds.
       - `loader\equipassist.inc` (`ANP_equip.txt`, no file = off, `levels=M02`) emulates DM.
       - The player start inventory comes from the engine/profile carry-over, not level data.
       - Workflow `anp-equip-fix`: review fixes + wiring + give.inc 999-reserve fix → `work\out_rel4\ANP_Loader.asi`.
     - Faithful M02 test plan: M02 built with `ANP_GIVE=1` (make `work\out_rel4_give\M02` after rel4), equip live, give live.
   - **out_rel3d loader IN GAME (13 Oct 17:29–17:50, helper): PASS, INSTALLED.**
     - **Heap guard 5/5 quits with no crash.**
     - **KEY: the player's and buddy's ZLNKOBJ+0x88 render-instance header is already BAD about 17 s after EVERY load** (M01 nodes 1028/1064, M02 8320/8314). At MM01 the walk shows 516 ZLNKOBJ: 514 ok, BAD 2. So something corrupts the heroes' render instances at or after load.
     - **ROOT CAUSE FOUND (13 Oct ~19:45, workflow `anp-hero-heap`, verified): DM `Appendage` events (handcuff chains M01/M02, ropes M09).**
       - DD's ZAppendage update (slot 25 0x8cbe30) looks up its render-instance attachment entry (0x5d1e50) by the TARGET's node, but Init registered it under the OWNER GROUP's node (0x7e06c0 → 0x5670d0). So it always gets −1, unchecked, and writes entry[−1] = inst−0x2c every frame: the 3x3 over the allocator header, the position over inst+0..+0xc.
       - DD regressed this: DM 0x5b8140 uses the right key and range-checks. No stock DD level uses Appendage.
       - **FIX BUILT and reviewed (13 Oct ~21:20, `work\out_app` M01/M02/M09 + `work\out_app_give\M02`):**
         - `ANP_APPENDAGE=drop` (default; `keep` is byte-identical to out_rel4).
         - `ANP_APPENDAGE_HIDE`: `.gms` +0x1c |= 0x400 and ZGEOM[3]=1 on the meshes under the dropped Appendage groups (the stock "hidden at load" pattern: 29,664/29,664 stock nodes with ZGEOM[3]=1 carry 0x400). The loader copies rec+0x1c into node+0x3c at 0x8adcab (proved).
         - Only the .prp/.gms differ (dropped events 4/4/12; hidden 12/12/36).
         - **IN GAME PASS (13 Oct ~21:30):** M01 ×2 and M09 give 0 header BAD; the MM01 walk shows ok 516 BAD 0; 0 heapguard hits; clean quits; no floating chains or ropes; the M09 rappel still works. **INSTALLED** (backups `install_1013_212757`/`_213419`).
     - **Faithful M02 chain run 4 (21:10): PASSES through cover practice (via test raises 4,3,13,14,9,10), grenades (023 equip tops up ammo; 060–110 cutscenes) and the rappel (010_MC_RappelPoint enables the box).** After landing, a firefight remains before EndOfLevel; to be tested.
       - Cover practice needs a WALK south from (-1070,1,-1490) to start 010_MC_InstructInCoverUse.
       - **M03B (13 Oct 22:05):** the beam works, but merc id=2 (max HP 38.7) dies within ~8 s at the roadblock → DD instant "You Lost A Crew Member" → checkpoint loop (14×/2 min). UNPLAYABLE.
         - Workflow `anp-merc-hp` is checking DM vs DD merc HP / difficulty / the NPC damage factor 1.5. Revive is the other half.
         - The helper is tallying crew deaths per level (M05–M14).
         - M03 needs a real walk route (or W).
       - **MILESTONE (13 Oct 21:57): faithful M02 plays END TO END → M03 loads.** INSTALLED (`out_app_give\M02`).
         - The cover practice passes with REAL keys: C at the vending machine's south face gives mov=8; RMB+LMB in cover advance 015 → 025 → 050.
         - The exit hint "Press [1] to make Lynch follow".
         - Oddity: Lynch bounces between roof and ground after the rappel, HP 72→1→72 (NPC rappel vs fall?).
         - Note: `tools\worldxf.py` prints (z,y,x).
       - **COVER (workflow `anp-cover`, verified): DD takes cover on a KEY, TapCover = C** (HoldCover = hold C).
         - DM snapped automatically; the M02 hints are DM's text.
         - DD's cover list (0x6d6a80) takes only ZSTDOBJ `*coverbox*` (low for car/m/l, high for h; up < 0.717 rejected; flag 0x400 skipped).
         - So **1,345 DM ZBoxPrimitive cover boxes are lost** (M13B keeps 2/476), plus tilted prefab boxes (M02 11).
         - Cover works at the kept boxes (one mov=8 seen in chain3). The test never pressed C at a valid spot.
         - Fix in progress (workflow `anp-cover-fix` → `work\out_cov`): `ANP_COVERS=box` adds ZSTDOBJ ANP_CoverBox* under ANP_Tail\ANP_Covers (tilted ones rebuilt upright); `ANP_COVER_HINTS` uses DD TapCover text; the climb trace logs cover/side/covers.
         - **W: press C next to cover.**
         - **ANP_COVERS built (13 Oct ~22:45, `tools\coverconv.py`, hook in `graft._graft_tail`; reviewed):** new ZSTDOBJ ANP_CoverBox* under ANP_Tail\ANP_Covers.
           - Covers: M02 38 → 110, M13B 2 → 476.
           - 0 moved; off = byte-identical except the LOC hint files.
           - Flags 0x302 with one mesh 0x80189/0x800000, like stock cover boxes (not drawn, no collision).
           - `ANP_COVER_HINTS`: M02 hints become L01's `{TapCover}` text in 5 languages.
           - The climb trace line adds `cover= side= covers=`.
           - Test spot: M02 column `ANP_CoverBoxH_19`, tp `-966.6 0 -1936 180`, then C.
           - **Review fixes done (`anp-cover-fix2`, reviewed):**
             - 1:1:1 mesh/meshlist/prim per box size, with refcounts summed down the chain via `prmconv ref_add`;
             - oblique boxes get an enclosing box;
             - `ANP_COVERS_MINHALF=15` skips degenerate boxes;
             - an old graft host logs a warning;
             - the lead added the prim-w4 zero-chunk refcount.
             - Covers: M02 108, M13B 476, M03B 347, M13 486.
     - **CREW HP FIX (13 Oct ~23:20, workflow `anp-merc-hp`, verified): `ANP_SOLDIER_HP=merc` (default).**
       - **DM gives crew mercs 8.5× HP** (kaneandlynch 0x722090: int field > 0 → int, else (50+1.25·h)·8.5 when merc id ≠ No_Mercenary).
       - DD's 0x8fbac0 multiplies by SP record +8 (0.5/0.9/1.15/1.3) · field(9+diff), so fields 9..12 = 1/record cancel it.
       - Values: M03B Ryu/Vaultbreaker 43 → 881.9 (was 38.7 effective); Lynch 1275; M13 Carlos 0 → 425. Enemies and player unchanged.
       - Stage 2 (opt-in, after a playtest): `ANP_SOLDIER_HP=all` + `ANP_WEAPON_ZONE=dm` (patch text in the workflow) for full DM damage parity. DD zone table 1/1.2/7.5/9/... vs DM 1/2/5/5/....
     - **out_rel5 M03B in game (13 Oct 23:11, helper; `rel3_b5_1013_231120`): the crew HP fix WORKS.**
       - Ryu has 881.9, Lynch 1275; police hits are about −54.
       - Only ONE crew death (at 17 s, roadblock), then the chain RAN THROUGH: MC_02_TunnelSnipersDead → AfterRoadblockGetIn → MC_04A_CrashUnderpass → 05_ArgueHill → 04D → 06_LostBag → 06B_PickupBag → 05_UnderpassVanReady → MC_09_SubwayCrash → MC_10_SubwayGetUp → 08_SubwayLeaveEm → subway (y −2065, z 184047; covers=422).
       - It didn't reach M05 within the run; the reason is pending.
     - **REVIVE LIVE: 5/5 PASS (14 Oct 00:33, M09, `rel3_rv_1014_003339`):**
       - `down 7` → `0x688190(...)=1` → DOWN.
       - Prompt + E → heal → GETUP → HP max (both dd and dm clips).
       - Bleed-out → DEAD → "You Lost A Crew Member" → reload with all writes given back and no stuck mask.
       - A wall refusal logs once with back-off; the buddy is refused (buddy=dd).
       - The prompt shows only at about 87 cm, though it is offered within 200.
       - Was enabled live, then **set back to DRY by the helper (00:41):** live revive soft-locked M03B.
         - DD's own DND regenerates the downed merc's HP; revive read that as RESTORED(external) and then re-downed him from the native DND state about 1×/s, so he ended pinned DOWN at full HP.
         - The first hit's down was refused by the room test, so he died outright.
         - **Fixed (14 Oct ~02:30, `anp-revive-fix3` + review; loader `work\out_rev2\ANP_Loader.asi` sha1 4690C922…; not yet in game):**
           - The HP rise was DD's general regen 0x419570 on `[body+0x5fc]` (+0x1c start, +0x20 last tick, +0x14 delay, +0x18 refill time), not DND. `rv_noregen` holds it off while DOWN/WSTAND.
           - RESTORED(external) is removed; there is a 10 s no-re-entry window.
           - New WSTAND for refused downs (mask, HP ≥ 1, heal, DND retry every 2 s, bleed). The vehicle gate stays a plain refusal.
           - Review fixes applied by the lead: regen +0x20 = +0x1c; an expired kept deadline stays kept; the dying task on top of DND → DEAD; PENDING from WSTAND has no regen.
           - Open: re-pin after a GETUP timeout (rare); no visible WSTAND cue.
           - With god 1, godpause=1 pauses bleed, so tests need `godpause=0` or a heal step.
         - The live config is saved at `work\helper\scratch\ANP_revive.live.txt`.
       - M01 regression on rel5 PASS (climb, refusals, 2 quits with BAD 0).
     - **`anp-m02-m03b-ends` results (14 Oct ~01:50):**
       - **M02:** after 006, Lynch never moves (his follow stalls), so KaneLynchBox `TriggerBoxCoverPoint` never fires and 010 never starts.
         - kl2's KaneLynchBox (0x7103e0) fires only when the player AND the buddy are inside, and it never moves the buddy.
         - The suspects are the 70 new cover boxes and Lynch's HP 80→1275. A/B builds `work\out_ab_m02_nocov` / `out_ab_m02_nohp` were sent to the helper.
         - **nocov A/B (14 Oct 02:00, not clean: W's input mixed in):** with ANP_COVERS=off, Lynch moved right after 006 and 010 fired. So the cover boxes are the likely blocker. The nohp run is not done.
         - Fallback patch `ANP_KLBOX_PLAYER` (that box becomes a player-only TriggerBox) is in the workflow journal, unverified.
         - Side note: the ANP_Covers group node shifts 2,356 graft nodes by +1. Harmless: no DM node moved.
       - **M03B: no conversion bug (verified).** EndOfLevel is a 65 cm strip at the platform edge (x 49653..54073, z 184783..184929), live only MC_09+9.9..+24.9 s.
         - In single player, ECPS is ignored, but every squad receiver (Lynch, via squad.inc) must be able and inside the CrewBox.
         - Test procedure sent to the helper. W: stand at the yellow edge by the train doors when "GET TO THE TRAIN" shows.
     - **Polish batch 1 (14 Oct ~03:00, `anp-polish-batch1`, reviewed; review fixes running in `anp-polish-batch1-fix` → `work\out_rel6_loader`):**
       - **Lynch's M02 "bounce":** NOT a bug in the rappel code. He walks the escalators and turns back each time the player changes floor (HVK-proven floors). The 72→1→72 swing is DD's buddy HP-1 rule plus regen on the old 72 HP Lynch: out_app_give predates ANP_SOLDIER_HP. A merc-HP M02 fixes it.
         - Test driver: change the tp `-1645 999 -750` → `-1720 1000 -660`; the old spot ends the cutscene 30 cm from the scaffold edge.
       - **Taurus not selected after 021:** DD's `unlockplayer weaponhdl UnholsterSec` (0x4d5c20) picks by inventory SLOT (0x566f20), DM's by type, so the P90 won.
         - Fix: equipassist `wpnhdl=1` mutes the unlock's +0x24 and selects by type.
       - **Loader `work\out_rel6_loader\ANP_Loader.asi` (sha1 55888FEE…, 14 Oct ~03:10).** It went through 3 fix/review rounds plus lead fixes and is NOT yet in game. It includes:
         - the revive fix3;
         - Taurus wpnhdl;
         - no-file defaults: climb live, squad on, give/grenade live, equip `live levels=M02`, rappel native, revive dry. All are M-level gated;
         - an unknown mode word means dry (an explicit off is kept);
         - an unreadable file keeps the previous config and is retried;
         - rappel tracks the scene every tick;
         - equip `levels=` is M levels only, and a restart with reallocated tasks triggers a rescan.
       - `work\out_m02hp\M02`: merc HP, covers off. It's the fallback M02.
       - **COVER PREMISE WAS WRONG (14 Oct ~03:40, workflow `anp-cover-follow`, verified):** DD already lists DM's ZBoxPrimitive cover boxes.
         - ZBoxPrimitive derives from ZSTDOBJ, and 0x6d6a80's class-mask test lets subclasses through. Stock DD has 291 of them; the runtime `covers=` counts match ZSTDOBJ + ZBoxPrimitive.
         - So rel5's ANP_COVERS mostly DUPLICATED covers (M13B 474, M12 252, M08 242). The only real additions are the tilted rebuilds.
         - **coverconv v2 APPLIED to tools:**
           - `ANP_COVERS_ZBOX=skip`: no copies of upright ZBoxPrimitives;
           - `ANP_COVERS_TILTED=auto`: drop a tilted box that duplicates a neighbour; a rebuilt H under 150 cm becomes low;
           - `ANP_COVERS_DUP=skip`;
           - `ANP_COVERS_FLOOR=keep` (`skip` needs `coverconv.HVK_SRC=get('.HVK')` in port_level).
           - All `keep` = rel5 byte-identical.
         - M02: 2 new low boxes (list 99 → 101).
         - Follow (0x6f4f50) never chooses a cover. ZPlayMiniScene slot 2 (0x6b74bd) CAN claim a cover within 100 cm for an actor.
         - The Lynch-freeze mechanism is still unproved (covers vs HP). The 9 dropped tilted H boxes include H_7 at Lynch's LynchCoverLoc.
         - **Candidate M02 = `work\out_m02v2\M02`** (merc HP + covers v2). Full rebuild `work\out_rel6` DONE (all rc 0, 0 moved; covers M01 382→395, M03B 339→347, M13 476→485, others unchanged). Queued for the helper (TASKS.md step 6).
       - **Release defaults:** with no file, give/grenade/equip are now live. Climb (with a new M-level gate) and squad become live/on in the fix run. Revive stays dry.
     - **Neutral-type audit (14 Oct ~04:00, `anp-neutral-audit`): `work\neutral\PLAN.md`** (+ INVENTORY.md, cat_0..4.md).
       - DD still has EVERY class the converter neutralises: same type id, same pool slot, schemas identical except ZCloth force, VehicleEffects and 5 vehicle routs. No stock DD level uses them, so each needs a smoke test (Appendage lesson).
       - Progression risks:
         - **M07 exit:** a ZWindowHitTrigger on the neutralised truck;
         - **M03:** DM's WarnBehaviourRout is dropped, so guards raise the alarm without warning.
       - **Decisions for W:** M03 stealth warnings, mounted-gun balance, crowds (performance), vehicles scope / BTR, PsychoticController, rain look, plant sway, PIP.
       - **Batch 1 DONE (14 Oct ~06:00): `work\out_nb1` = rel6 + batch 1.** All rc 0, 0 moved, reviewed as ready. Queued for the helper (TASKS step 7; it supersedes rel6).
         - Ropes default off.
         - HeliFly: `_ATTACK=gun` + FACE_TARGET. Fields 9–12 are left alone: converted runs have (0,1,0,0), stock always has 11 or 12 = 1. If choppers never fire, set (0,1,1,1).
         - Disk cleaned to 38 GB free (old loaders in `work\loaders_archive`).
         - **M07 exit is a GUARANTEED SOFT-LOCK in rel6** (proved). ZWindowHitTrigger 03 is only switched on by the dropped truck routs. Window hits come from ZVehicleEffects' window listener.
         - `ANP_M07_TRUCK=relay` (default):
           - the 10_ToGrave relay at T0+15 s enables the window trigger, objective, music and lights;
           - a TriggerDelay 62 s on the 60_ node, `_TIMEOUT=win` (safety net; `fail` = DM's crush, only once window hits are proven).
         - `ANP_KEEP_DM_TYPES` groups (mg, crowd, rope, plant, rain, ik, env, car; default empty = rel6). The exact relayout is DM bytes plus the ZGEOM bool.
         - `ANP_HINTS2`: hints show [O], [2] and [4].
         - `ANP_PLANT=static`: 973 leaves keep their prim.
         - `ANP_ROPES` (going to default off until tested).
         - `ANP_HELIFLY` mapping of fields by meaning (choppers attack: M01 12, M08 5, M11 8, M11B 6 runs). `_ATTACK` default becomes `gun` (LAUNCHER → none; stock DD never uses it).
         - Live-controller audit: no crash path found. BUT 0x701830 (shared with ZVehicleGetAwayEffects) can read NULL: audit it before any `car` work.
         - Leaves and ropes need an FXMISS harvest run (`fx=legacy` → `fxmiss_harvest.py --apply`).
     - **Open (workflow `anp-m02-m03b-ends`):**
       - **M02 rel5 regression:** 010_MC_InstructInCoverUse never starts and Lynch stays at the car. The helper put `out_app_give\M02` back as the safe M02.
       - **M03B end:** after MC_09_SubwayEscape, MF_12_MissTrain fires about 43 s later. TriggerBox_Platform is eTGS_AllInside + ECPS_BOTH.
     - **out_rel5 sweep (13 Oct 23:22–14 Oct 00:08):** M05/M06/M07/M08/M11/M11B/M12/M13 had 0 crew deaths and 0 exceptions; cutscenes started.
       - Covers per level: M05 179, M06 240, M07 128, M08 598, M11 625, M11B 261, M12 758, M13 560, M13B 950, M14 712. M13B and M14 also clean (0 deaths, 0 exceptions): the whole rel5 sweep passed.
       - Revive dry pre-flight ok: Kane has the heal clips; mercs at 956/1275 HP.
       - Next for the helper: revive LIVE test, then the M03B end.
     - **Crew-death sweep (old installs, 13 Oct 22:14–23:10):** M05/M06/M07/M08/M11/M11B/M12/M13 ran 300 s each: 0 merc deaths, 0 restarts, 0 exceptions, no silent exits. Crew death is NOT widespread; only M03B (and M03 when the crew is left behind) showed it. The helper is now on out_rel5.
     - **out_rel5 BUILT (23:40): all 17 rc 0, 0 moved; per-level covers/appendage/HP lines confirmed. Sent to the helper for install + sweep.** (M01: no hp lines because its only crew merc, Lynch, has DM health -1 = cannot die, which the rule leaves alone.)
     - (was:) out_rel5 building (all levels: appendage drop, covers, explode, give=1, merc HP) + loader `work\out_rel5_loader\ANP_Loader.asi` (sha1 AD390570…: give, rappel, grenade, equip drop=remove, heap/reset guards, failwatch, revive (dry), cover diag).**
     - **ANP_GIVE now defaults to 1** (faithful M02, 13 Oct ~23:00). The loader's give/equip still need `ANP_give.txt`=live and `ANP_equip.txt`='live levels=M02'. **For release, make those defaults live.**
       - The helper is installing `out_app_give\M02` as THE M02.
     - **A/B result (13 Oct ~17:55): NOT gunfit.** It is identical with `ANP_GUNFIT_BIND=0` and `ANP_GUNFIT=0`.
       - The headers go bad within about 1.5–2.4 s of level start (the intro), for both player and buddy.
       - **The bad "header" bytes are a unit quaternion that changes every frame,** so per-frame pose/bone rotation data is written over the start of the +0x88 block: an overrun from the preceding allocation, most likely a pose/matrix buffer.
       - Suspect: the DM hero rigs have more bones/tracks than DD sizes the buffer for. Workflow `anp-hero-heap` is on it.
     - (Earlier) suspect gunfit skeleton bone binding (a -1/0xffff bone index). A/B builds: `work\out_ab_bind\M01` (`ANP_GUNFIT_BIND=0`) and `work\out_ab_gunfit\M01` (`ANP_GUNFIT=0`); the helper is testing them.
     - **GRENADE WORKS:** the probe passes (pool 25); `throw fwd` and the G key both launch, use ammo, raise event 30, and the gas cloud is visible in shots. The 13 Oct "fail" was the camera looking away.
     - Give + rappel regressions pass.
   - **M09 follow-ups (workflow `anp-m09-followups`, reviewed):**
     - **EXPLODE BUG: every converted explosion does 1000 damage** (218 events). The positional aligner put [DM0,DM1,DM2,DM3,1000,1.0]; the correct mapping is DD = `[DM0, DM1, NEW_cam(200), DM2(tinnitus), DM3(damage), 1.0, DM4..DM14, 0]` (DD's own copies of DM templates insert 200 at index 2). Patch text (`Conv.explode`, `ANP_EXPLODE_FIX`) is in that workflow's work dir. TO APPLY to prpconv.py once `anp-m02-equip` finishes.
     - `loader\failwatch.inc` is WIRED (opt-in `ANP_failwatch.txt`):
       - the fail text at 0x156b5f4 (8-bit), flag 0x156b6f4, fail window +0x20+idx / name +0x22+32*idx;
       - per merc: able +0x576, HP block body+0x5fc (+4 cur, +8 max), position, +0x513/+0x512.
     - **squad.inc** has the new `recruit=start|always|off` (start = never pull from level squads, adopt owner only). **The default is `always`** (old, proven), because under `start` M02's Lynch stays in a level squad DD never releases, so orders would be refused. Use `start` per level only after testing.
     - The plant clip is present (M09 clip 3657, 2.2 s); the ~0 s act cause is unknown. The clip census (`work\clipcensus\missing.md`) found 23 missing script clip paths, all missing in DM too: harmless.
   - **M09 reset after the rappel (workflow `anp-m09-reset`, verified): a TEST ARTEFACT, not a rappel/callback bug.**
     - The test enabled the box directly, skipping checkpoint 1 and `Trigger_StartMercsRappel` (Defend-Boardroom). So the mercs followed the player down and landed under the guards' fire; a merc died → DD's instant MF_01 → restore to the level start (no CP1).
     - The callbacks can't double-fire: each handler has one call site; the end handler sends +0x44 or +0x54 by `0x660b00(1)`.
     - The fail text is at 0x156b5f4 (0x7864f0 writes it before 0x8edc40), with the flag at 0x156b6f4.
     - Leads (workflow `anp-m09-followups`): squad.inc re-recruits mercs out of level squads mid-script; DM Explode is 4 floats vs DD 6 (positional fill 1000/1.0); the Plant clip may be missing; a fail-reason logger.
     - **The faithful gap: DD fails the mission at once on a merc death; DM wounds and lets you revive.** A loader revive is the next big item.
   - **Faithful give in game (13 Oct 17:00, out_rel3_give M02):**
     - The give works and gates: Remington → Lynch is a swap; event 18 raised with monitors registered; the P90 prompt, 020_MC_KaneEquipsP90 and 021_MC_KaneEquipsTaurus all ran.
     - **But the P90 and the Taurus never reached the player.** DD's mini-cutscene equip (0x7cd310) refuses when one-handed + two-handed are full: the player held USP + the Spas, and the Spas came back from Lynch in the swap. 022_MC_KaneEquipsUsp never started, so the level soft-locked; M02 was rolled back to out_rel3.
     - Workflow `anp-m02-equip` is fixing it (start inventories / equip replace).
   - **Crash dump findings (13 Oct, workflow `anp-dumps`, verified; `work\dumps\inventory.md`):**
     - **The most common crash (7/19, incl. W's 05:12):** int3 at KL2+0x665dc (heap-unlink magic 0x12345678 check, caller 0x882c30 ZWin32Allocator free).
       - It happens on scene teardown (quit to menu), freeing the FIRST hero torn down: its render instance ZLNKOBJ+0x88 (0x3ac bytes, from 0x86f2f0/0x8b8c30).
       - That's Lynch in M01 (Lynch_Squad, torn down before Hero) and the player in M02.
       - What damages the header is NOT proved. It is hero-specific, not squad-recruit-only and not climb.
     - **Render-thread crash after a D3D device reset** (monitor reconnect): W's 11 Oct 10:10 "0x695e199b" crash and M12 13 Oct 15:56.
       - It's a kl2 bug: the reset (0x456bf0) recreates the render targets, but the command list built before it still holds the old surface pointers.
       - Doesn't always crash.
     - **12 Oct 01:42 0x222580:** a reset with a NULL device (state-4 path). Separate.
     - **Loader guards BUILT and reviewed (`loader\heapguard.inc`, `loader\resetguard.inc`; tokens in `ANP_guards.txt`: `heap=veh|off`, `herowatch=on|off`, `reset=on|all|off`; all default on):**
       - **heapguard:** a VEH on the int3 at 0x4665dc with `[esp]==0x882c85`. Resumes with `Esp+=8; Eip=0x882c9b` (Free's own epilogue; lock 0xe059c0 balanced); the block is leaked. It also logs the owner (`[esp+0x28]` when `[esp+0x2c]==0x6dd751`).
       - **herowatch:** buddy (gameMgr+0x4cf0) and player ZLNKOBJ+0x88 headers, plus a node walk at each scene request.
       - **resetguard:** kl2 SetEvent IAT 0xb100fc. At return 0x456d72 (reset) it empties both render lists like slot 14. With `reset=all` it also acts at 0x8bbc63 (state-4 recreate).
       - Note: ZFFPlayer does NOT derive from ZFFActor/ZActor (only ZLNKOBJ at offset 0).
       - Review defects fixed by the lead (reset=all now acts; herowatch_event is main-thread only).
       - **Integrated loader `work\out_rel3d\ANP_Loader.asi` (sha1 D70A4489…, 13 Oct ~18:00):** give + rappel + grenade (with fixes) + heapguard/herowatch/resetguard. The helper is testing it (heap quit ×5, grenade with flight watch, regressions).
     - **Grenade (workflow `anp-grenade-fix`):** the release path is probably fine. The 13 Oct test likely fired out of view (2000 cm, 2 s).
       - New: a pre-throw probe of the ammo template pool (+0xa8 array / +0xac count / +0xb0 cursor, filled by 0x7782b0 at load) and of launch gate +0x1a4.
       - Launch is detected by the release point being consumed plus the cursor moving; a flight watch logs the arc.
       - Ammo is used (clip/reserve XOR 0xbeebbeeb); release is 70 cm forward.
       - DD's own Gas/Smoke/FlashBang are item type 3 (SpecialEquipment); Frag/Incendiary are type 0.
   - **Dumps:** WER full dumps are in `%LOCALAPPDATA%\CrashDumps\kl2.exe.*.dmp`, plus game dumps `kl2_490_crash_*.mdmp` in the DD folder. Parser: `work\dumps\mdparse.py` (workflow `anp-dumps`). W crashed at 13 Oct 05:12 while playing; it's being analysed.
   - **out_rel2 sweep (13 Oct):** 9/16 survive 5 min.
     - M03 survived 30 checkpoint restores, so the Appendage fix is proven in game (the restores come from the test's gunfire triggering M03's alarm mission-fail).
     - M12 crashed in ntdll on a background thread.
     - M06/M08/M09B/M11 silent exits on 12 Oct ~01:10–01:30 have no WER dump: probably killed externally while the old helper session died. Re-run them.
   - **W, 12 Oct ~01:20: TOP PRIORITY = weapon swapping/giving** (Kane keeps the shotgun; in DM he gives it to Lynch and uses a P90). **Rappel CRASHES the game**: KL2+0x1a503a reads [0+8] with edi = player. Seen in W's M02 at 19:59 and in the helper's M09 run at 01:25. A background RE agent is on it (`work\rappelcrash\`).
   **M03/M03B (12 Oct, workflow `anp-m03-chase`, reviewed; offline only; builds in `work\out_m03`):**
   - **M03, `ANP_M03_GETAWAY=faithful`:**
     - The 10_ relay waits 9 s (`_DRIVE`).
     - The EnterGetAwayVehicle relay is driven by WoundedFilter_GetIntoVan's OnNoWounded container and waits 3.5 s (`_DOORS`).
     - kl2's WoundedFilter (0x7730a0/0x8d6030) sends container 1 if any actor has +0x576 == 1, else container 2.
     - DM has no walk-up box at the van.
   - **M03B, `ANP_M03B_FALLBACK=teleport`:**
     - All 17 SP van routs plus 2 get-in prompts become relays, and DM's beams chain the stages.
     - CP_04_PosP1 gets a ZBeamToPos for the player.
     - The driver (Merc_Driver_02 = actor Merc_03) is beamed to BeamPos_01_Underpass_Car: there's floor 6 cm below, and MC_04A/04D/05 need him.
     - Gate_Beam01 fires before MC_04A.
     - 5 van-only events are dropped.
   - `ANP_VEHICLE_RELAY=exit` now **fails the build** if an exit relay would be skipped as a loop.
   - **Untested in game:** whether ZBeamToPos moves the player (kl2 0x6030a0 has an actor branch) and whether MC_04A/MC_09/MC_10 bind. Track them with cutdiag.
   - **squad.inc `critical=clear` is finished** (own byte-checked build gate; log flood guard). It's in `work\out_m03\ANP_Loader.asi`, not installed.
     - Caveat: with `clear`, the death of a story-critical merc (M03 Vault Breaker, M03B driver) becomes a soft-lock instead of a mission fail. Keep the default `keep`.
(Older note) **PAUSED by W (11 Oct ~20:35), until he says continue.** The 20-minute loop was cancelled, and the helper was told to pause.
   - Workflows `anp-dm-mechanics` (wf_b4011d8d-076) and `anp-m03-chase` (wf_f203d5e2-53e) were stopped mid-run. Resume them with `Workflow({scriptPath, resumeFromRunId})`; finished agents replay from cache.
   - Their partial edits may be in `loader\squad.inc`, `loader\godmode.inc`, new `loader\*.inc` files, `tools\prpconv.py` and `tools\port_level.py`. Check those files before building.
   - The installed game is out_rel2 and is known good.
1b. **W's TOP PRIORITY (11 Oct ~20:30, after his playtest):** DM **rappelling**, **grenades** and **giving/swapping weapons with squad mates** are required to progress M02 and later levels.
   - Workflow `anp-dm-mechanics`: RE both exes, then new `loader\rappel.inc`, `grenade.inc`, `give.inc` and/or prpconv/new tools modules, integrated into `work\out_mech_all`.
   - The port_level hook lines get added by the lead after `anp-m03-chase` finishes, since that workflow owns `port_level.py`.
   - **out_rel2 is INSTALLED (20:23, helper):** all of the 11 Oct fixes. 90 s M01 clean; hits −17 to −37.
2. **PROGRESSION BLOCKERS (found 11 Oct ~19:30, `work\gap\entities\blockers.txt`):**
   - The converted M01, M03, M07 and M09B **cannot reach their exits**: the exit gates are only sent by dropped vehicle routs. M02 (PlayerMonitor targets lost), M11 (BTR) and M03B (van chase) probably can't either.
   - Fix in progress (workflow `anp-progression-fixes` → `work\out_prog_all`): `ANP_VEHICLE_RELAY` forwards the dropped routs' messages; `ANP_PLAYERMON` restores PlayerMonitor targets.
   - `scripts\install_build.py` installs a build together with the funeral, with backup and rollback.
   Also in work: the out_ovl crashes, M03 ~60 s (0x8c6bbe), M09B ~30 s (call to cccccccc), M12 ~250 s (0x5c8075 after `1_MiniCutScene_ThrowGrenade`), being analysed by workflow `anp-ovl-crashes`.
   **Queued for port_level.py once those workflows finish:** `ANP_PROXY_ITEMS`. The InventoryBinding dedupe drops `HG_HK_USP_01_Carry`, so 4 M05 cutscenes (Kidnap ×2, the two COOP pickups) are dead (+35 = a section track didn't bind, kl2 0x4b64e0). Fix: repoint those proxies to the kept `HG_HK_USP_01` (helper REPORT 11 Oct ~20:00, scan scripts in `work\helper\scratch\cut05\`).
   **out_ovl crash causes (workflow `anp-ovl-crashes`, each confirmed by an adversarial verifier; fixes not yet applied):**
   - **M03/M03B 0x8c6bbe:** DM door `Appendage` events link to the getaway van `Ground_01` (DM ZHavokCar, neutralised to ZSTDOBJ). ZAppendage Load (slot 22, 0x833660 → 0x8c6b70) needs a ZLNKOBJ and runs on EVERY checkpoint restore or mission fail, so it crashes every time (Init checks, Load doesn't).
     - Fix `ANP_APPENDAGE_LINK`: drop Appendage events whose target is neutralised. Build the neutral path set where `car_owners` is built, since `neutral` is complete there. No loader guard: there is a second fault at 0x8336d0.
   - **M09B call to cccccccc:** `prpconv.ITEM_MAP` maps GrenadeLauncherGas → GrenadeLauncher and GrenadeIncendiary → Grenade_Frag, so the bindings are dropped as duplicates. A `fireat … usesec 1` with an unbound weapon gets item type 4, and the 4-entry jump table at 0x49f288 overflows.
     - Fix `ANP_ITEM_EXACT`: map them to DD's own `eFF2ItemGrenadeLauncher_Gas` (53) and `eFF2ItemGrenade_Incendiary` (58).
     - **Also hit W on a weapon swap (11 Oct 20:05, 0xcccccccc).** Under the same switch, every DM variant now gets a spare DD id of the same class:

       | DM variant | DD id |
       |---|---|
       | USPCarry | HG_SigSauer226 |
       | USPLight | HG_SW_MP45 |
       | MP5Light | SMG_UMP_SBR |
       | M4Light | Rifle_AK47 |
       | Rem700Silenced | Rifle_Type88_Scoped |
       | RPGInaccurate | RocketLauncher_Hind |

       RPGInaccurate is still dropped where Hind is used. This also binds the M05 USP_Carry cutscene proxies.
     - **APPLIED 11 Oct ~20:15** together with `ANP_APPENDAGE_LINK` and `clip_sounds()` (`ANP_ANM_CLIPSND`), in `port_level.py` (build stage). Full rebuild: `work\out_rel1`.
   - **M12/M13/M13B/M14 0x5c8075:** ANM clip field 11 (+0x2c) is a **per-level .SND record offset**. `ANM_FORMAT.md`/`anm_lib.py` wrongly said it was equal across games.
     - The ~1,240 DD donor clips carry F03 offsets, which hit junk in our banks: 1,126–1,191 bad ids per level, 8–89 of them land on crash words.
     - Fix: `tools\clipsnd.py` (`ANP_ANM_CLIPSND=name`) re-points by record name or zeroes the offset. Needs wiring in port_level after the gunfit block and in the `ANP_ANM_MERGE=0` branch.
   **Progression fixes landed (workflow `anp-progression-fixes`):** all exits are reachable in the model (`work\gap\entities\prog\blockers.txt`) except M03B (the physical van chase).
   - `ANP_VEHICLE_RELAY=exit`: RelayMessageList 'AITrigger' on the dropped vehicle routs of M01/M03/M07/M09B/M11.
   - `ANP_PLAYERMON`: one DD PlayerMonitor per DM list. kl2 never raises 16–22, 25 or 26. DM 19 → 28 one-shot; DM 21 → 27 eON_HEALED.
   - Added by the lead, 11 Oct ~20:30:
     - `ANP_BUDDY_WEAPONFILTER=pass`: M02 020_GettingGuns waits for "Lynch holds the Taurus/Remington", which only DM's give wheel can satisfy, so the level soft-locked. Now the pass container is forwarded.
     - `ANP_PLAYERMON_P2=drop`: co-op P2 monitors are dropped. kl2's 20-slot monitor table (0x8ef000) doesn't catch overflow; M02 had 22, now 11. The build logs the count and warns above 20.
   - Open from the review:
     - The M03 relays skip the walk to the van and WoundedFilter_GetIntoVan.
     - DM 12/13/20 could map to DD 30 eTHROW_THROWABLE, and 18 to 23.
     - `port_level` writes the .TEX via the shared `work\_tex_out.bin`, so **never run two builds at once**.
   **Friendly mercs are mission-critical in DD (helper static RE, 11 Oct ~20:30):**
   - kl2 soldier init 0x615c90 makes every friendly soldier a merc (+0x6e8=0xd) and sets +0x512=1 and +0x513=1 through slot 57 (0x725b20).
   - On death: 0x8fd470 → 0x6d2500 → slot 58 reads +0x513 → MF_01_MercDead → 0x8edc40 → MissionFailedReload → the level restarts and the intro replays (the M09 "loop").
   - squad.inc does NOT set it.
   - Planned: squad.inc `critical=keep|clear` (walk the merc list at [0x1548fd8] and clear +0x513; data writes only). The faithful fix is DM's downed/adrenaline revive; the helper is reverse-engineering DM's rule.
   **DM revive vs DD (helper RE, REPORT.md ~20:50):**
   - DM mercs go WOUNDED (ZActor+0x536 = 2, ZWounded task) and the player heals them within 200 cm (ZFFActionHealWounded). The bleed-out time is 1024 × difficulty record +0xc; only after that does MF_01_MercDead fire.
   - DD has no merc heal: its heal scan 0x7aaaf0 accepts only ZFFPlayer co-op partners (170 cm, action 0x12).
   - DD's DownNotDead (SquadModifier enum 14: Force 1 / Prevent 2; L10 GalleryCampers is the only Force example, with DownNotDeadBehaviourRout) makes soldiers go down and get up by themselves.
   - Plan: first `ANP_MERC_DND`, then a loader-driven revive.
   - **`ANP_MERC_DND` is built (default 0, not tested in game):** `tools\dnd.py` plus a hook in `graft._graft_tail` (`dnd.graft_hook`).
     - ANP_DND becomes the FIRST child of ANP_Tail. It holds one modifier ZMercSquad per merc slot set, each with L10's SM_DND (eDND_ForceDownNotDead) plus a DownNotDeadBehaviour pair.
     - Every node is new: 0 moved, and it's byte-identical when off.
     - It runs only when the menu graft runs. port_level needs no change; don't also call `add_merc_dnd`.
   - **Also:** DD levels scale enemy damage per squad (`eDmgM_*`, L01 70%) and health (`eHealthMod_*`); DM ports have none. Check this against the one-bullet deaths.
   **Player one-bullet death: FIXED offline (11 Oct ~21:00, workflow `anp-oneshot-death`, confirmed by a verifier):**
   - `prpconv.exact()` left-aligned DM's 7 weapon floats onto DD fields 19..25, so DD field 25 (damage multiplier, gun +0xe4, applied unconditionally in kl2 0x46ef60) got DM field 23, the rate of fire (250–850). Every hit did 750–29,000 against 500 HP (Normal = 100×5); enemies died from one shot for the same reason.
   - Fix `ANP_WEAPON_DMG` (`Conv.weapon_damage`, default 1):
     - weapon fields 19←17, 20←18, 21,22←19, 23,24←20, 25←21, 26←22, 27←23;
     - ammo fields 17,18←15 and 19,20←16.
     - This reproduces DM's damage curve (DM 0x51d820).
   - Field 37 (NPC factor) is still 1.5 on every gun. DM has none (1.0 would be faithful); `ANP_WEAPON_NPCDMG` overrides it. This is a balance call for W.
   - godmode.inc `log` mode: `ANP_god.txt` = `log` keeps god mode off and logs every HP change plus difficulty (0x156b5f0).
   - Only M01 is built so far (`work\out_hp`); every level needs it.
   **Out_fun in game: 5/5 PASS, now INSTALLED (11 Oct ~20:40):**
   - The intro movie plays, then M01 loads; skipping the movie works too.
   - Dead Dogs: `M00_INTRO` → DGNW → M01.
   - Funeral: M07 → M07F → M08 automatically, with audio.
   - The endlevel chain and progress update work.
   **Disk:** C: filled up at about 19:40 (builds, backups, smoke WAVs). Superseded build folders were deleted. Keep work\ lean: delete parity/scratch builds after use. Builds made around 19:30–20:40 may have failed from the full disk, so check rc and the validator.
3. **Feature-gap plan `work\gap\PLAN.md`** (tiers A/B/C). Tier A (funeral in build_all, enum fixes, silent DD loading call, chapter/difficulty names, crew hints, HUD tweaks, static shadows behind a flag, progression-blocker audit) is being built into `work\out_gapA` by workflow `anp-gap-batch-a`. Then C1: the full chain run in game. Note that **0x200110 is ZSHADOWMESHOBJ (static shadow geometry), not lightmaps**; DM's "lightmaps" are AO in the `.prm` stream plus `.TEX` (plan B2).
3. **Crew orders:** CommandDisplay2 HUD and recruiting the other mercs in later levels.
4. **Non-English dialogue:** DM type-4 records hold 5 languages; DD reads 9.
5. **Lighting:** W's brightness verdict.
6. **Hook coexistence:** move the ASI loader to `winmm.dll` so JC's SHIP hook can stay in; not tried.
7. **Later:** Fragile Alliance maps and characters, upscaling, first person, free camera.

## 15 Oct overnight (W: camera off in places, give UI missing, audio inconsistencies, revive needed)
- **Camera:** `ANP_CAMPROFILE_SWAP` (scriptconv, default 1). camprofile coopfilter numbering is reversed in DD (ONLY_KANE = 1 = player two), so DM's single-player camera moves never applied: M02 10, M03 2, M06 6, M07 1. M02's co-op shots hit the player. Build `work\out_cam\M02`.
  - M09 rappel: ECP tables, the camera boxes and the rappel move are all identical to DM (proved). Still open; needs W's screenshot / which phase.
  - `ANP_DOCUCAM` (default 0): grafts DD's Cam_Handheld shake. DM had none; this is a look choice only (`work\out_cam2`).
- **Give UI:** give.inc on-screen prompt (id 6, raw text "[4] Give Lynch your X" / "Swap…") plus a result line. `ui=1`. Loader `work\out_giveui` sha1 84A92867…, untested.
- **Audio:**
  - `ANP_SND_SEQREF`: type-3 sequence steps now re-pointed to the relocated type-1 copies (they read garbage loop flags before).
  - `ANP_ANM_CLIPSND_BASE`: file-name fallback for donor clip sounds. Builds `work\out_snd`.
  - ~960 donor clips per level are still silent (crouch/sneak/cover); `ANP_SND_IMPORT_DD` agent running → `work\out_snd2`.
  - Open: SND byte +0x2c (DM dialogue 6, DD 0): A/B `ANP_SND_T1_B0=zero`.
- **Helper** (now session a-newer-perspective-5c) is running the TASKS queue on out_nb1 + the rel6 loader: revive first, then the give UI and the cam M02.
- **`ANP_SND_IMPORT_DD` (tools\sndimport.py, default 0 until tested):** imports F03's SND/WHD/WAV records for the cleared donor clips.
  - Donor clips: 881 restored, 35 still silent.
  - Size: .WAV +0.85 MB per level.
  - Skipped: localized and streamed waves.
  - Builds: `work\out_snd2` M01/M02 (0 bad clip ids, 0 moved). Queued for the helper.
- **REVIVE LIVE PASS (15 Oct ~06:20, helper): enabled live in W's install** (out_nb1 + rel6 loader 55888FEE).
  - M03B: no flap and no regen; MC_02 starts and the chain goes on; the E heal works.
  - M09 a–e pass; a room refusal gives WSTAND.
  - Open: a checkpoint resets the bleed to the full time; the WSTAND→DOWN retry was not seen.
