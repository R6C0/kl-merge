# A Newer Perspective (ANP): briefing for Claude

Read this first. It is the hand-over from the previous Claude session, written 10 Oct 2026. The detailed notes are in `docs/progress_and_format_notes.md` and `docs/ANM_FORMAT.md`.

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
- ASI loader: `dinput8.dll` in the DD folder. The DD folder also has `KL2Fix.asi` (DebugMenu, BorderlessWindowed, TrueAltF4) and `main.ini` (FreeCam, cheats).
- The previous session worked in a Linux VM with paths `~/mnt/<game>` and `~/work`. The code now takes env vars instead:
  - `ANP_DD_GAME`, `ANP_DM_GAME`
  - `ANP_WORK` (the work folder)
  - `ANP_DD_EXE`, `ANP_DM_EXE` (for `re/`)

## Getting set up (not yet run on Windows; fix what breaks)
1. Install Python 3.10+, then `pip install capstone pefile`.
2. Clone kl-merge into `work/ext/kl-merge`. Only `re/schemas_dd.json`, `re/schemas_dm.json` and `tools/dd_enums.json` are used.
3. Run `python tools/setup_workspace.py --dd "<DD>" --dm "<DM>" --work work`. This extracts `scn/dd`, `scn/dm` and `cache/L01_Main.TEX`, and builds `dd_types.txt`, `dd_db.pkl`, `dd_arrlen.pkl`, `dd_enums.pkl` and `fxc/union.pkl`.
   - Prebuilt copies of the small stats files are already in `work/`.
   - The script is new and untested.
4. Convert level 1: `python tools/port_level.py M01_A M01A M01`. This writes `<DD>\Scenes\Locations\M01\M01_Main.zip` and takes about 60 s.
   - Use `ANP_SET="CameraFogBegin=0.25"` (the previous session always did).
   - All 16 story levels convert: M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14.
5. Loader: `loader\build.bat` (MinGW-w64 i686, needs `-lgdi32`). Copy the result to `<DD>\ANP_Loader.asi`.
   - The game locks the file while it runs, so copy it only when the game is closed.
   - `loader/ANP_Loader_b38.asi` is the current build.
6. Test:
   - `ANP_autoload.txt` (`M01 1 12`) loads M01 about 12 s after launch; press Enter at "Buffering 100%".
   - The log is `<DD>\ANP_log.txt`.
   - Hook files (create in the DD folder): `ANP_quit.txt`, `ANP_shot.txt`, `ANP_nodes.txt`, `ANP_gui.txt`, `ANP_where.txt` (node indices; also logs Player objects and every registered use prompt).
   - Loads now take about 3 s.

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
- DD has no player climb class (DM `ZFFPlayerMovementClimb`: Low 120, Medium 170, High 220 cm).
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

### JC's notes still worth checking
- Bullet-hit crash at 0x4c34b3 (bone id byte +0x3e must match the skeleton table).
- First-execution crash at 0x4098a1 (ExecutionBloodSpatter define order).
- Weapon-handling anim folders come from the item-enum table at 0x154a650.
- Discord's overlay hook has crashed the game.

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
- **Sound broken since the animation merge:** only the first dialogue stream (about 1 s) plays, then nothing; W reported no gunshots or ambience. The anim library is now filtered (+2.6 MB instead of +13 MB) and ZSoldier speaker names are restored. Isolate the cause:
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

## Next steps, in order
1. **Climb:** position check, fix placement and orientation, confirm the prompt and the climb. Then add the other DM climbs: the M01 warehouse wall `ColiObj_HeroClimb_01` / `099_TB_ClimbWall`, M03A `TriggerBox_ClimbWall`, M03B `ColiObj_CornerClimb*`, and M13A `ColiObj_HeroClimb_A_*`. Lynch should use the `/Movement/Climb/*_NPC` clips.
2. **Sound and intro:** isolate as above, then restore them.
3. **Pause menu** rendering.
4. **Gun hold.**
5. **Lighting:** brightness tuning, then DM lightmaps (0x200110) and AO volumes (0x800011e).
6. **Load-test M02 onward** and triage.
7. **Later:** Fragile Alliance maps and characters, upscaling, first person, free camera.
