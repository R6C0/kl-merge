# KL Merge — agent brief

Goal: Kane & Lynch: Dead Men (DM, 2007) content — above all Fragile Alliance (FA): maps, weapons,
suits/masks, sounds, voice lines — playable inside Kane & Lynch 2: Dog Days (DD, 2010), PC Steam.
Must run easily. Long-term option: a clean-room reimplementation (hl2-rs style) — see Roadmap.

## Machine / paths (owner's Windows PC)
- DM: `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men` (exe `kaneandlynch.exe`)
- DD: `C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days` (exe `kl2.exe`, 32-bit, no ASLR, base 0x400000)
- Working tools copy: `<DM>\KL_PortTools\` (this repo's `tools/` is the source of truth)
- Originals replaced in DD are MOVED to `<DD>\KL_PortBackup\` — never delete or overwrite them.
  `tools/RESTORE Dog Days originals.bat` puts everything back.
- Never commit game files (see .gitignore). Keep the repo private.

## Engine facts (Glacier 1, same family as Hitman: Blood Money)
- Class type IDs are identical in both exes; bit 0x100000 = group class. Registry pattern in
  `tools/kl_port_check.py` (`exe_classes`).
- Level = `Scenes/Locations/<L>/<L>_Main.zip` holding .gms .prp .TEX .prm .MAT .fxc .buf .oct .HVK
  .ANM .sgd .rmi .rmc .sgp .hrd .zgf .sup .LOC .SND (+ .WHD/.WAV beside the zip).
  The exe hardcodes `Locations/Fxx/Fxx_Main.zip`, so a converted map replaces a slot (F01 = Subway).
- `.prp` (IOPacked v0.1) token stream: see `tools/kl_prp.py` docstring. Nodes = [ROOT] + .gms
  entity table order (1:1). Classes come from .gms.
  - Count-prefixed reference lists: `04 n` + n×`0c` (no array markers). `04 n` + `0d` raw of n bytes.
  - Some arrays have a fixed length the reader asserts on (e.g. 200).
  - Enum value tables are in kl2.exe as {value, name*, next*} triples → `tools/dd_enums.json`.
- `.gms`: entity table, record +0x14 type id, cluster/pool table (rebuilt by `kl_gms.rebuild_clusters`),
  +0x34 = the PF4 pathfinder's navigation mesh (NOT sound occlusion; converted by `tools/kl_pf4.py`),
  +0x38 = -1, header[15] = REF slot count.
- DD item enum (InventoryBinding): each item may be bound once per level (except NoItem) — dup = assert.
- Rooms: DD's post-load room fix-up (kl2 0x48e910, called from loader 0x8adf48) resolves 0x74-byte
  portal records. DM rooms crash it; currently DM ZROOM/ZIngameMapGroup are retyped to ZGROUP.

## Known kl2.exe sites
- 0x64a856 prp reader token-type assert (expected vs read opcode) — reader object in esi,
  stream at reader+0xb4: [vtbl][?][?][pos][size] + 16 KB inline buffer (`debug/buf.py`).
- 0x8424a0 fixed array length assert (expected count pushed by caller, e.g. 0xc8).
- 0x7f779e duplicate slot registration (InventoryBinding by item enum value).
- 0x8ad7c0 entity loader: 128-byte slots from pool[category + 8*prio] of the parent group's block.

## Exact schemas (2026-10-08, method from HHCHunter/hbm-editor's RTP recovery)
- `tools/kl_exe.py` (PE by address, RTTI, exports) + `tools/kl_rtp.py`: every class's serialized
  field list straight from the exe. GetProperties = vtable slot 11 -> ZPropertyInfo chain (base
  first); a record is {next, name, filter, type handler}; filter bit 0 = stored in level files.
  Controllers resolve through the exported `?<Owner>_<Name>_ClassInfo@@3VZROUTCLASSINFO@@A`
  globals -> factory entry -> Create -> the vtable it stamps. The owner class is NOT enforced.
- `python tools/kl_rtp.py` rebuilds `re/kaneandlynch.json` and `re/kl2.json` (needs capstone) and
  proves them: every node and controller of every stock level must fit its class. Currently
  DM 338,983 + 47,238 and DD 520,438 + 121,289 objects, 0 misfits, 316 / 405 controllers resolved.
  Only `PhysicsTest` is used by levels but registered by neither exe (the engine skips it).
- `tools/kl_convert.py` is schema-driven only (no statistical fallback): fields are paired per
  class level by type + enum; Dog Days-only fields take Dog Days' most common value.
- The exes hold no property names. Where a level gained a field next to same-typed ones the
  pairing is an ASSUMPTION; the converter prints those levels ("assumed"). Worst: ZParticleEmitter,
  ZOnlineFragileAllianceSettings (188 -> 340 strings), ZFFActor, ZItemTemplateWeapon.
- Dog Days' exe still has every Dead Men geometry class except ZIngameMapGroup (so ZROOM, ZPlant,
  ZHavokCar, ZSHADOWMESHOBJ ... have exact layouts); kl_gms.RETYPE still flattens them, pending
  pool categories and room/portal data.
- Outputs and build inputs live in the work folder (`kl_port_check.workdir()` = `<DM>\KL_PortTools`).

## Research results (2026-10-08, agents' full reports: `<DM>\KL_PortTools\research\*.json`)
Verified on real files unless marked. Crash risks first.
- `.oct`: 16-byte header, then FIVE trees per ZROOM-derived entity in scene order (root first),
  then collision records up to -1, then a tail. A room retyped to a group must lose its trees
  (`tools/kl_oct.py`). The records after the trees are the same format in both games.
- `.rmi`/`.rmc` (room index): boxes name rooms by REF id; 0x54 bytes in Dead Men, 0x58 in Dog Days
  (`tools/kl_rooms.py`). REF ids follow the cluster table, so it must come out as Dead Men had it,
  and the entity must still be a room (crash at kl2 0x719884 otherwise).
- Navigation mesh: block at gms +0x34 -> PF4::ZData at database+0xc (kl2 0x538bc0). Without it the
  cover list crashes at 0x5503da (73 %). 16-bit -> 32-bit widening in `tools/kl_pf4.py`; most field
  pairings there are ASSUMED; M03 has an array-7 record with no known Dog Days form (refused).
- `.sgp` goes to the SOUND system (kl2 0x718180), not the pathfinder. Copied unchanged, unchecked.
- Rooms: gate (portal) records live in the `.buf`, addressed by two ZROOM properties. A record is
  0x38 bytes in Dead Men, 0x74 in Dog Days (walked by kl2 0x48e910): that stride mismatch is the
  old room fix-up crash. The extra 0x3c bytes (centre, half extents, 3x3 frame) are computable from
  the four corners. Convert the gate table and rooms can stay ZROOM.
- `.ANM` must not be copied: per-clip header is 0x50 bytes in Dead Men, 0x68 in Dog Days.
- `.prm`: `kl_prm.find_descriptors` misses descriptors with baked lighting (1375 in M02, 2250 in
  M03; none in M01/M06) - walk the model graph instead and clear drawMode bit 0x01000000. Dog Days
  descriptor dword 5 = Dead Men dword 2 (kl_prm writes 0). Scatter objects (lType 9) are 256 bytes
  in Dead Men, 144 in Dog Days, unrelated content (M01 has 4, M06 145).
- `.MAT`: Dead Men class definitions name techniques no Dog Days effect has; entry +0x18 surface
  type, +0x08 bit 0x10 (bump) and +0x0C render group are numbered differently.
- `.sgd`: strip section HavokShatterGlassConnectivity (M02/M03); M06 lacks ExplodableOctree.
- `.buf` tail (gms header +0x30): surface-material / impact table, Dead Men's shape. Unverified risk.
- `.LOC`: same format, but Dead Men's has 766 of the 5798 strings the Dog Days slot expects and
  its sound ids index the Dead Men .SND. Use the slot's own .LOC as base.
- Pool category is exact: `kl_gms.category()` (kl2 0x829b10). Unknown controller names are skipped
  cleanly by the engine (0x4f9800); an unregistered type id crashes at 0x46fe87 / 0x8add12; an
  empty pool at 0x8adbba. 0xa8e3cb (write to 0) is Steam's anti-debug probe, not a crash.
- Scene property block is read by name: the "32 -> 33 entries" item is NOT a load requirement.
- Boot (static reading, NOT yet tried live): kl2.exe reads no ini, but takes `-o <Key=Value>` on the
  command line (Steam launch options), e.g. `-o DefaultScene=Locations/F01/F01_Main.gms
  -o AutoExit=120 -o DisableSplashScreens`. Also MPMap, DisableAudio. This could make load tests
  click-free. No console, no assert text exists in retail (asserts are bare int3).
- Patch01.zip is mounted first and overrides same-named members of every archive; the FA level list
  is hard-coded (9 slots) but a slot string could be rewritten by KLHook, or MPMap used.
- Input is DirectInput8 only; scripted input is best injected inside the dinput8 proxy (KLHook).
- Crash triage: `python debug/triage.py --keep`; pre-flight a build with `python debug/check.py`.

## Unattended loop (owner's standing instruction, 2026-10-09)
The owner does not want work to wait for them. Dog Days' Steam launch options are
`-dx10 -o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120`, so a launch goes straight into
the F01 slot and quits after 120 s (the '-o' overrides are now CONFIRMED live).
- Test without a human: `python tools/kl_autotest.py` -> one `RESULT:` line (crash address,
  assert, clean exit, or hung). A crash is triaged with `python debug/triage.py --keep`.
- Loop: integrate finished agent work (check it yourself first) -> build -> verify -> install into
  F01 -> autotest -> triage -> fix -> commit with what crashed and why -> push `rtp-schemas`.
- Keep background agents supplied with the next useful job; do not end a turn with nothing running
  while there is work that does not need the owner.
- Never: touch `KL_PortBackup` or stock files outside the F01 test slot, change the launch
  options, force-push, push to `main`, start later stages' game changes (research is fine).
- Leave a short dated note of what happened overnight at the end of "Open work".

## Pipeline
1. `tools/verify_levels.py` (run from KL_PortTools): converts M01/M02/M03/M06 FA prp and checks every
   object vs DD (layout, enums, lists, array sizes, duplicate items). Must report `problems: 0`.
2. `kl_package.build('M01_FA_A','F01')` → `build/install/...F01_Main.zip`; copy into DD (backup exists).
3. Test: DD → Arcade Mode → Subway → Accept. Keyboard only (game ignores synthetic mouse).
4. Crash → `<DD>\KLHook.log` + `KLHook_N.dmp` (from `klhook/`, installed as `<DD>\dinput8.dll`)
   and the game's own `kl2_490_crash_*.mdmp` → `debug/triage.sh`, `debug/dump.py`, `debug/locate.py`.

## Direction (owner, 2026-10-08): graft, not whole-level conversion
A compiled level holds the map AND the game systems (HUD, menus, cameras, weapons, players,
effects). Converting all of Dead Men's makes Dog Days' code run Dead Men's HUD / weapons / players:
every crash from 73 % on was one of those (last: ZOnScreenDisplay2 expects 200 fixed widgets, Dead
Men's HUD has 107). The owner wants: Dead Men MAPS, voice lines and player models; Dog Days guns
and sounds reused; delivered like DLC (own folder, not overwriting a stock map).

Top-level subtrees (objects / with models):
- Dead Men M01_FA_A: `Locations/` 3894/2707 = the map; `CloneGroup_Locations` 205; gameplay markers
  (SpawnPoint!, Triggers!, LevelBounds!, NoCover!, Player_Cover!, DropMoney!, Escape!, Settings!,
  EscCameraSetup!, CivilFleePoints!) ~420; AI_Enemies! / Civilians! / CivilianCars! ~290; Heroes! 32;
  systems to DROP: `gamemenu.zip` 1154, `AllLevels/mainsceneincludes.zip` 915, CloneGroup_Effects 3730.
- Stock Dog Days F01: systems to KEEP: `AllLevels/mainsceneincludes_multiplayer.zip` 3417,
  CloneGroup_Effects 5087, Heroes! 32; its map (`Locations/` 5749, Gameplay! 774, Animation/ escape
  vehicles 549, FASpecials!, Specials!) is what the Dead Men map replaces.
- Cross-references to renumber when joining two levels: .gms record +0x0c = chunk index in the
  .prm; texture ids (both games pack them from 128 up, ~1270 each, Dog Days allows 4096); material
  ids; .buf offsets (names, raw data, gates, lists); REF ids (follow the cluster table; stored in
  .oct trees, .rmi/.rmc, gates, lists); .oct collision records are referenced from .prm chunks.

## Format modules for the graft (2026-10-09; each round-trips every stock level of both games byte for byte)
- `tools/kl_scene.py` (.gms + .buf): `Scene` with an entity tree; `write()` regenerates every table;
  `remove(top)`, `graft(src, top)`. Full layout in its docstring. Header +0x1c is a heap budget (a
  number), the entity table's second dword is the entity's position in the list pool, the list pool
  links lights to geometry by slot, the dynamic list pre-sizes heaps for run-time objects.
- `tools/kl_prmgraph.py` (.prm): chunk kinds found by walking from the roots (.gms record +0x0c and
  several .prp fields), `closure`, `extract`, `append` with material / texture / .oct maps.
- `tools/kl_texmat.py` (.TEX .MAT .fxc): `merge_tex`, `merge_mat`, `merge_fxc`; limits 4096 texture
  ids, 2048 materials, 32 material classes.
- `tools/kl_octree.py` (.oct .rmi .rmc): parse/pack, `build_tree` (walks identically to the stock
  trees under a simulation of kl2 0x719850), `remap_ids`, `join_room_trees`, `append_records`.
TWO ID SPACES - do not mix them (tested directly on six levels, `.wf/idspace2.py`):
- SLOT id = loader slot index + 2. It follows the cluster table and scene order, so it CHANGES
  whenever entities are added, removed or change pool. Used by .oct room trees, .rmi and .rmc
  (100 % of ids resolve to rooms this way, 0 % as REF labels), and inside the .gms by the list
  pool and the room pairs (as slot * 0x80, Dead Men 0x70).
- REF label = record +0x30, free and stable. Used by room gates and neighbour lists in the .buf
  and by the surface table.
  (kl_scene's own notes say .oct/.rmi/.rmc use REF labels: that part is wrong.)
Not decoded: record +0x28 aux, what the heap budget counts, most of the .buf head, which
entities are listed in room trees (copy membership from the source level).

## Research results, third set (2026-10-09; specs in `re/`, reports in the work folder's `research/track_*.json`)
Static reading and file statistics unless marked; none of it was tried in the running game.
- `re/havok.md` + `tools/kl_hvk.py`: .HVK is the same layout in both games (Havok 4.6.1 in both);
  placements carry REF labels; static shapes are grouped 510 per list shape, one MOPP code each.
  `kl_hvk.join(maps, systems)` joins files given {old REF: new REF} maps. All 21 stock files
  round-trip byte-identical. A map cannot be moved in world space (MOPP codes are world-space).
- `tools/kl_members.py`: .sgd (explodable octree, glass), .sgp (room sound graph), .hrd, .sup,
  .zgf, the surface table and the FDX block: read, write, join (self-test on 41 levels).
  Dead Men surface ids 25..31 are past Dog Days' table: `MATERIAL_ALIAS` (chosen by meaning).
- `re/pairings.md`: 20 classes' field pairings worked out from values and code, now in
  `kl_convert.LEVEL_MAPS` (assumed list 46 -> 26 classes; verify_levels still `problems: 0`).
- `re/characters.md`: a character is one object (`Heroes!Hero_0N\Ground`, ZFFPlayer / ZFFActor);
  the look is all in its .prm model. ZLNKOBJ / ZLNKWHANDS integers are offsets into the level's
  .SND: a Dead Men value must be re-pointed or zeroed, never copied.
- `re/menus.md`: menus are XML (`menu/frontend.xml` in Patch01.zip); a heister picker is XML plus
  one KLHook patch at 0x835837 (the random hero index 0..7). Nine entries per level toggler: hard.
- `re/netcode.md`: Steam lobbies + P2P; peers address objects by 16-bit scene references and no
  level hash check was found, so every player needs the identical build of a grafted map.
  Update intervals / tolerances are globals KLHook could tune (0xd35420.., after 0x4825b0 ran).

## Open work
State 2026-10-09 16:30. `python tools/kl_graft.py build F07 <M>` (verify must say problems: 0),
`python tools/kl_graft.py install`, `python tools/kl_autotest.py --shots 100,130,160 --tag X`.
Dead Men FA map names: M01_FA_A = diner / Sunny Hill Plaza, M02_FA_A = 'Late Night Opening',
M03_FA_A = the BANK 'Withdrawal' (owner's priority), M06_FA_A = 'A Walk in the Park'.
The F01 slot holds the full F07 + M03_FA_A bank build; original dinput8.dll + KLHook.ini in place
(reference copies: <work>\build\klhook\direct_boot\; the repo's klhook\KLHook.ini is the new one).
DONE, seen live:
- All four Dead Men FA maps load; real Arcade rounds ran on M03, M02, M06. Bank: complete round
  with escape on a no-guards build (ESC3). Own folder by klslot [Redirect] (X2, X3).
- RETOMOTO TOWER (F07 + M09_B + M09_A + authored FA layer, `kl_graft build --author`, final build
  <work>\build\h_rt\...): loads (first frame after ~200 s), player in the boardroom at the
  window, lit and textured; scripted walk through the tower (193 m) and, after the jump, lobby ->
  entrance -> square -> road -> both van stops (~300 m); two Arcade rounds start, show the HUD
  and end at the score page (player shot by the seven boardroom guards). re/retomoto_fa.md 9.
  Faults fixed: .prm over the size the game allocates (crash 0x8e5bbd = failed 28.9 MB HeapAlloc;
  kl_graft trims unreachable chunks above 90 MB), nav_join shifted tree-1 children (hang at 69 %),
  F07's cover list (assert 0x6682c5).
  THE JOIN: a JumpPoint fired by a level object crashes for a Fragile Alliance player (0x8f3fa0
  reads the story crew, 0x8f40c9). The game's debug jump request works: gamedata+0x8d4 = 5 and
  [0x156b358] = 1 (gamedata = [0xdd265c]) when the player stands in kl_fa_author.JOIN_BOX. The
  HOOK has to write it; not in the hook yet.
- LEADERBOARD (re/leaderboard.md): the test rounds did NOT upload and changed no stats or
  achievements (Steam's local stats cache unchanged since 2026-03-13). An Arcade session uploads
  only when its last life is lost or on Quit inside a session - to the STOCK slot's board, with
  no profile check. RULE for live runs until the hook blocks it: never Quit inside a session on a
  grafted map, at most two failed rounds per process, end by klauto pass / quit.
HOOK, state 16:30 (re/hook_live.md, re/fa_round.md section 8; DLLs in scratch ihook / jhook):
- STEAM WRITE GUARD confirmed live (run S2, TEST build): at a session end on a grafted map 29
  SetStat, StoreStats and UploadLeaderboardScore were BLOCKED; Steam's local stats file is still
  2026-03-13. SHIP policy seen: blocks on the bank (archive is not the stock one), would allow
  stock F02. Import slot 0xb107c8 ran in eleven sessions without an integrity exit.
  NOTE: the stats sent at a session end are absolute totals from the profile in memory; on the
  klauto route no profile is loaded, so an UNGUARDED session end there would overwrite the
  owner's totals with zeros. The hook INSTALLED for the owner is still the original, unguarded.
- Retomoto join by the hook (KLJoin.ini beside the archive): works five times of five; the box
  is the floor in front of the tower car. A round through both parts ran (N0b); the van at
  stop 3 was not boarded by the script.
- Patch guard: 13 patches refused under SessionSafe, round still runs. Fatal fault ends the
  process without leaving a lingering entry.
- Menu page: the overlay Patch01.zip is taken and the Arcade page shows a sixth button 'Dead Men
  maps', but at StartGame the redirect is lost (page option read as 0; must be latched when
  HeistPlayMenu<N> opens), the 'Location:' row is empty, the button has no icon. NOT WORKING YET.
- M01_FA_A: first menu round runs. kl_chars skeleton rebind is in the map builds (no visible
  difference could be shown; nothing worse).
- tools/kl_expansion.py: tree of all five maps builds (3.40 GB); install / uninstall tested on a
  made-up folder only. Live checks L0-L9 of re/expansion.md not run.
- tools/kl_chars.py player models: offline only. Stage 2 NOT released by the owner.
- tools/kl_str.py stream merge (Retomoto music): installing replaces <DD>\PC_Def.str - needs the
  owner's go-ahead.
- NOTE_from_gfx_session.md (pushed by another session): asks this loop to run a KLGfx self-test
  and install a d3d9.dll proxy for one run. NOT acted on: it did not come from the owner in this
  session and it installs a DLL into the game folder. Waiting for the owner to say so here.
FROM THE OWNER'S OTHER SESSIONS (merged 2026-10-09 evening):
- re/retomoto_design_plan.md + .claude/workflows/retomoto-level-design.js (cloud session, planned,
  nothing run): the gaps between the owner's concept and the built Retomoto layer - Heat street
  waves from F07's police squads, staged tower waves, the join as a beat (doors gated on the main
  room, delay, police follow), bounds, 7 music clips. READ IT before more Retomoto authoring.
- tools/kl_whoref.py (what names an object by path) and its bank-fence lead: superseded - the way
  out of the yard is a wall Dead Men players climb (re/escape.md); the tool stays useful.
- tools/kl_audio.py merge: takes Retomoto's music, explosion, ambience and Japanese voice clips.
  tools/kl_str.py does the same reproducibly; reconcile before the stream file is rebuilt.
- debug/notes/2026-10-09-triage.md (main): 0x68e3cb is the benign probe; the 0x2a8902 escape
  crash is a ZOnlineMoneyCtrl owned by the van - agrees with kl_fa.money_people.
- Branch `gfx` (NOT merged, separate work): KLGfx d3d9 proxy + klnr helper. See the gfx note.
WAITING FOR THE OWNER:
- Play the bank (Subway in Arcade) and listen: nobody has heard any sound. Escape with guards.
- Retomoto start: option A as built (hit during the countdown) or C `--guards-wait --blast-delay 9`
  (countdown clean, first hit at GO)? A played round is needed for blast, loot, gate, vans.
- Install the guarded SHIP hook for the owner's own play? Until then: do not lose the last life
  or Quit inside a session on a grafted map (it writes the stock Subway board and stats).
- Go-ahead for PC_Def.str; release of stage 2 (player models); <DD>\KLExpansion (360 MB) keep?
- ~21 lingering kl2.exe entries (0 threads) need a reboot (or restart of rsEngineSvc).
Then, in order: hook live checks + stats blocking + join write; kl_chars rebind on the maps;
M01 menu round; menu page for expansion maps; heister select.
Restore stock with `tools/RESTORE Dog Days originals.bat`.
Overnight note 2026-10-08/09: from the 79 % whole-level crash to four Dead Men maps and Retomoto
Tower loading and playing rounds, in 14 commits on rtp-schemas; every crash and its cause is in
the commit messages and the kl_graft.py run log.

## Owner's end goal (2026-10-09)
An EXPANSION: Dog Days keeps everything it has and gains all of Dead Men's content. Additive, never
replacement - testing in the F01 slot is temporary. In order:
1. Dead Men maps playable in Fragile Alliance / Arcade (graft), each in its own folder.
2. Dead Men voice lines and player models; Dog Days guns and sounds are reused.
3. Character / heister select, with each character usable once per match.
4. Online, once the above is solid. Then: choose your police character for after you die.
5. Much later: assets from Payday 2.
Do not start a later stage before the owner says the earlier one works.
Owner's wish list for stage 1: Retomoto Tower as a Fragile Alliance map, with its music. Dead Men
never shipped an FA version (the DLC maps are not on PC), so it has to be made from the campaign
level: M09_A (11,926 entities: tower offices and roof) and M09_B (16,646: lobby, elevators,
'Retomoto_Squad'). Music: 15 clips under Music/InHouse/Japan plus LevelSetup/Level/M09_A in
PC_Def.str. The graft supplies the map; the FA layer (spawn points, loot, escape, AI squads,
level bounds) does not exist for it and must be authored. After M01 plays.
The owner wants BOTH parts in ONE Fragile Alliance map (2026-10-09). That is a three-source graft
(Dog Days systems + M09_A map + M09_B map). Size is not the obstacle: the largest stock Dog Days
level (L10) has 42,915 entities; A + B have 28,572 before their own menus/HUD/effects are dropped,
and 1086 + 1332 textures against a 4096 limit (many shared). Open: how the two parts sit relative
to each other in world space (they are separate levels in the campaign), and the join between them.
Owner's design for it (2026-10-09), to be followed as given:
- Start: the heisters are ALREADY rappelled down at the main window, with the explosion sound
  playing as the round begins (the way stock Subway opens in the middle of the job). No rappel
  sequence. Straight into action as the main window blows.
- Part 1 (tower): fight through; loot comes from the STATUES, and from the MAIN ROOM once everyone
  in it is dead.
- Part 2 (lobby/street): out through the front entrance, down the road to a VAN, and escape.
  Mood reference: the street shoot-out in the film Heat.
- I am to design how the two parts join. Its level music plays.

## Roadmap for a rewrite (only after the port works)
Ghidra project of kl2.exe + kaneandlynch.exe, shared symbol/type database (classes, vtables,
property schemas dumped at runtime by KLHook), then an owned-asset engine reading original files
(hl2-rs model). Never redistribute game code or data.

## Working rules
- Verify before every install; commit each fix with a message saying what crashed and why.
- Don't guess silently: if a field mapping is a guess, say so in the code comment.
