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
READY TO SWAP IN (2026-10-10 ~13:00, offline, NEVER LOADED): <work>/build/rt_ai2/retomoto_ai2 = kl-merge-b6's Retomoto v2
(G:/kl_scratch/ai_dyn2, commit ca178fb, re/retomoto_ai.md 11) + wardrobe with the four plates + KLJoin.ini. Van: the parked car
PC0700_M09_Cars_Qeue_A_01 it drove into is hidden, drive-away to z 21000. Enemies: Dead Men soldiers had kept Dead Men ZSoldier
rows (field 15 = 1000, stock 5000) - now whole stock police rows by weapon class (which float is accuracy: NOT established).
Voice repairs ON (.WAV 27,158,864). Checks: wardrobe problems 0, chunk table 65,119, kl_impact 0, kl_chars check = the known glow
material, street report exit 0, kl_voice heisters: 1 SILENT (ExitHeist_01_R plain leaf, as in stock). Install on the owner's word:
`python debug/slot.py put "<work>/build/rt_ai2/retomoto_ai2" F01`, then a load check with scratchpad pd/RTM.ini.
OWNER PLAYED THE RETOMOTO AI + VAN BUILD (2026-10-10 ~12:30): 'i dont get why i survive from being shot so much maybe because im by
myself? the van is almost perfect its just when it finally leaves like before the end game result it goes into a car just make sure it
drives off down the road the whole time'. Passed to kl-merge-b6 (its files): the van's leave leg, enemy damage / accuracy against
the player (to be MEASURED against stock F07, not guessed), and the build was made with the voice repairs off (re/bots_voice.md 6).
The lead finishes the next build (lighten, wardrobe + plates, KLJoin.ini) and swaps it in. Same damage question for kl_map_ai.py.
SLOT 2026-10-10 12:10: Retomoto again on the owner's word = <work>/build/rt_ai/retomoto_ai (b8d430d0); hook ship_stall, the owner's ini. One thread-less kl2.exe entry (44 K) lingers.
OWNER PLAYED LATE NIGHT OPENING (2026-10-10 ~12:00, build z_maps/M02): 'dead men guns dont show up', 'the late night van sometimes is a
bit weird? camera goes under the map when ur in it', 'the ai a bit too easy so just probably take some logic from retomoto and put it
in there and do the same fixes for the other maps'; the park's helicopter 'shouldnt be as bad'. (The round and the escape evidently
work.) RUNNING: workflow map-tune (.wf/tune.js; run id in the session's workflows folder): tools/kl_map_escape.py (vehicle route
and camera against the ground), kl_map_ai.py (Retomoto's skill / waves / fall-back on the four maps), gun looks on the map builds
(kl_guns was never run on them), then kl_map_tune.py -> <work>/build/t_maps/<map>, then an adversarial review.
STATE 2026-10-10 11:51 - SLOT NOW = LATE NIGHT OPENING on the owner's word: <work>/build/z_maps/M02 (8 masks: no Payday 2 plates on
the four map builds yet; no KLJoin.ini). Load check LNO: PASS - the first live load of a lightened + wardrobe Dead Men map build:
level in 2 s, .prm 52.5 MB in the reserve, Kane's body taken, round reached GO, no fault. To see by playing: the 26 jewel
containers, three floors, the MOVED boarding action at the car park (-426, 136, -8627). Retomoto to put back on request:
`python debug/slot.py put "<work>/build/rt_ai/retomoto_ai" F01`.
STATE 2026-10-10 11:45 - SWAPPED on the owner's word: F01 slot = <work>/build/rt_ai/retomoto_ai (dynamic AI + straight van + wardrobe +
masks; sha1 b8d430d0), hook ship_stall + the owner's ini, overlay as before. Load check RTA: PASS (level in 2.3 s, Kane + Wolf,
round reached GO, no fault). The AI / street / van behaviour (D1..D6, re/retomoto_ai.md 9) is for the owner to see by playing; the
previous build is <work>/build/rt_masks/retomoto_masks. RUNNING (owner: 'continue the ai heisters', on Opus): workflow
wf_0bc8776f-9fb (.wf/bots2.js): research (squad mechanics; backstab / pay the driver and leave / blow the van / help up; heister
voice lines) -> tools/kl_fa_bots.py + builds <work>/build/b_bots -> adversarial review. Resume with that run id after a limit.
STATE 2026-10-10 11:40 - INSTALLED FOR THE OWNER AND SEEN LIVE (owner: 'continue', and through kl-merge-db 'yes retomoto mask'):
F01 slot = <work>/build/rt_masks/retomoto_masks (Retomoto + wardrobe + loot props + the four Payday 2 masks; sha1 a8e01b56) with its
KLJoin.ini and KLWardrobe.ini; hook = SHIP <work>/build/klhook/ship_stall (c120880a) + the owner's own KLHook.ini (Expansion on,
[Load] NudgeMs=1000, Char=10 Mask=1; pair kept in <work>/build/klhook/owner_now); overlay = BOTH files of
<work>/build/pd2/overlay/Overlay (Patch01.zip af59ca57 + Scenes/kaneandlynch.zip 30e0fd90). What was found in the game folder
before (the 09:40 mask-test state) is kept in <work>/build/klhook/found_1010_1115.
- Run PV1b (menu only, TEST hook test_stall): PASS. The Heister page shows the character and the mask picture above the rows,
  colours right, labels and pictures agree ('Tommy' / 'Black beard - Tommy'); Arcade page: ... Online Leaderboards, Heister, Guns.
  Pictures <work>/research/shots/PV1b_*.png.
- Run RTM (menu -> Arcade -> Subway slot, Char=9 Mask=10): PASS. 'wardrobe (version 2): 16 characters, 12 masks', 'body: slot 0,
  model 9482 -> 9256 ... the player now has 9256', 'look: variant 1 -> 11'; level in 2.3 s; the 76.0 MB .prm in the reserve; round
  reached GO. Picture <work>/research/shots/RTM_78s.png: Kane on the balcony with the WOLF plate on his face, drawn and textured.
- STALL WATCH, first live lines: 'the main thread is back after 21.9 s without a frame or a loader step' at every start - the
  intro movie (the main loop does not run while a movie plays; the script's 'wait 1500' took 22 s). So a movie is a healthy
  silence: StallEndMs MUST STAY OFF (a campaign cutscene can be minutes long); StallMs 30 s only writes a dump.
- READY TO SWAP IN (12:00, offline, NEVER LOADED): <work>/build/rt_ai/retomoto_ai = kl-merge-b6's dynamic AI + straight van
  build (entry below; loot props included) finished like the installed one: lighten trim,slim -> wardrobe with the four plates
  -> KLJoin.ini. Wardrobe problems 0, chunk table 65,119, kl_impact 0, kl_chars check = the known glow material,
  kl_fa_street report exit 0 (van x -1850, y 2, z 8700 -> stop 10800 -> 14900). Same sizes as the installed build, .WAV 22.0 MB.
  Install: `python debug/slot.py put "<work>/build/rt_ai/retomoto_ai" F01` (needs the owner's word; then one load check with
  scratchpad pd/RTM.ini, then D1..D6 of re/retomoto_ai.md 9 - most of them the owner will see by playing). Still unseen live: fxc_slim (F1), the four z_maps maps, the loot props (the owner's eyes),
  AI heisters for the Dead Men maps (job parked for usage).
RETOMOTO DYNAMIC AI + STRAIGHT VAN (owner asked 2026-10-09 late; BUILT OFFLINE 2026-10-10, NOT RUN IN THE GAME, NOT INSTALLED): re/retomoto_ai.md.
Tower: the boardroom guards run from the window at the blast, the pistol squad is unleashed 6 s later (kl_fa_author ROOM_*, --room-classic).
Street: police start when the crew leaves the lobby elevator (campaign box Mercenaries!TriggerBox_1_LeaveElevator), from out of sight; squads fall
back when a neighbour is wiped out (ZSquadScript field 8: ASSUMPTION, --no-chains), wave 3 comes out of the parked SWAT truck and is unleashed 13 m
before the van, run-to-van clock 62 -> 28 s (kl_fa_street DYNAMIC, --street-classic). Van: tools/kl_fa_van.py rewrites its baked position and
rotation keys in place: straight up the east carriageway x -1850 at y 2 (the road is y 0 there; it drove at y -40, under it), waits z 8700, stops
z 10800, leaves to z 14900; one barricade hidden (--van-bent). kl_arms: FORCE + skill by weapon class on Retomoto only. Build that PASSES every
offline check: G:/kl_scratch/ai_dyn1 (no wardrobe, no KLJoin.ini yet; no member grew). Live order D1..D6 in re/retomoto_ai.md 9.
STATE 2026-10-10 11:30 (kl-merge-01). THE SEVERAL-BLOCK RESERVE WORKS LIVE: the owner's own session 09:04-09:32 (hook ship_stall,
log + maps kept in <work>/research/owner_1010_0904): one process, SEVEN level loads (Retomoto x3, stock x4), no crash; four
requests the heap refused were served from the reserve - three 32 MB scratch blocks and, at 09:19:50, a 13.9 MB block with the
.prm already in it ('free 103 MB, largest piece 10.0 MB'), the case that crashed three times the night before. No stall line.
WHO HOLDS THE 2 GB (python debug/vmmap.py on those maps; second load, 204 MB free, largest piece 32 MB):
- modules 306 MB: nvgpucomp32 63, nvd3dum 61, nvwgf2um 53 (the D3D10/11 driver - the game is D3D9, so an overlay or recorder
  made that device: medal-hook32.dll, nvspcap.dll and gameoverlayrenderer.dll are loaded; d3d11.dll, dxgi.dll, dcomp.dll too);
- private RESERVED ONLY ~770 MB besides our reserve: 24 heap segments of 15.8 MB with 221 MB of them uncommitted; 56 thread
  stacks of 4 MB = 226 MB reserved, 10 MB used (deepest 3.5, 2.0, 1.3, 1.0 MB; the other 52 at most 204 KB); five 32 MB
  write-combined driver arenas (142 MB uncommitted); a second 128 MB reservation at 0x3b420000 with 0.4 MB committed, owner
  NOT found (kl2 0x64eac2 pushes a flag, not a size).
  => tell the owner: every overlay / recorder (Medal, NVIDIA overlay, Steam overlay, Discord) lives inside this 2 GB.
  => [Memory] StackMB as written is the WRONG set (it shrinks the game's own threads, among them the deep ones). Idea, not
  written: log start routine and peak stack use per thread, then shrink by routine.
GAME FOLDER NOW (11:15) = a mask test state left by ANOTHER session (not kl-merge-39, which never touched the game folder; most
likely kl-merge-db, which relayed the owner's words and also wrote tools/kl_add_plates.py), NOT the owner's Retomoto: slot <work>/build/pd2/pd2_F01 (stock Subway +
wardrobe + 4 Payday 2 masks; the owner: 'all work'), hook pd2_ship b4f1dc8b (no stall watch), KLHook.ini from the sample
([Expansion] Enable=0, [Load] NudgeMs=0 = slow loads), Overlay/Patch01.zip 91,646 bytes of 06:52. Asked kl-merge-db before
changing anything; the owner's own pair is kept in <work>/build/klhook/owner_now. kl-merge-db did not do it either: the
runs (kl_autotest tags pd2-wolf .. pd2-dallas-long) and tools/kl_add_plates.py (+ a 'plates' command in kl_chars.py, both
uncommitted) come from a tool outside the Claude sessions. ITS Retomoto + masks builds (<work>/build/plates_test, plates_cli ..
plates_cli3) FAIL kl_impact: the plates are appended, 69,743 chunk-table entries, 3,985 slots left of the 4,096 kept free.
READY INSTEAD (11:21, offline, NOT LOADED): <work>/build/rt_masks/retomoto_masks = `kl_chars.py wardrobe <work>/build/y_loot/light
<out> --plates=wolf,dallas,chains,hoxton`: chunk table still 65,119 entries (2,400 dead indices left), kl_chars check = the one
known glow material, kl_impact 0, kl_pd2mask selftest PASS; against the installed Retomoto only .prm (74.2 -> 75.6 MB), .TEX
(+2.7 MB) and .MAT differ; KLWardrobe.ini Masks=12 OutfitStep=14. HAND-OVER WAITS FOR THE OWNER'S WORD: slot = that build
(debug/slot.py put ... F01 --join klhook/KLJoin.retomoto.ini), hook ship_stall, the owner's KLHook.ini, overlay = BOTH files of
<work>/build/pd2/overlay/Overlay (the installed Patch01.zip IS that pictures build, but Scenes/kaneandlynch.zip is not beside
it - harmless only while [Expansion] is off); then PV1b (menu pictures) and one level load with Mask=10. The live queue below is partly overtaken: M8 is answered by the owner's session.
STATE 2026-10-10 07:15 (kl-merge-01; owner away since 01:00, STEAM STILL AT ITS SIGN-IN WINDOW: no live run since 00:55).
INSTALLED FOR THE OWNER: slot = <work>/build/y_loot/retomoto_loot (unchanged); hook = SHIP <work>/build/klhook/ship_stall (sha1
c120880a = ship_mem3's several-block reserve and map files + the STALL WATCH + klchar that accepts 1..12 masks); their KLHook.ini
untouched; overlay Patch01.zip (90,729 bytes) untouched. None of the hook's new parts has run in the game.
- STALL WATCH (klhook.c, [KLHook] StallMs / StallSayMs / StallEndMs): no frame and no loader step for 30 s -> a line with where the
  main thread stands + KLHook_freeze.dmp; silences over 3 s are logged when they end; StallEndMs (off) would end the process.
  Read the 'stall watch:' lines of the owner's next sessions before ever switching StallEndMs on.
- FOUR DEAD MEN MAPS REBUILT (agent z-maps, audits re-run: PASS x4), offline, NOT LOADED: <work>/build/z_maps/M01, M02, M03, M06
  (F07 systems, all fixes, lighten, wardrobe; .prm 50-61 MB, archives 178-197 MB). Install one: `python debug/slot.py put
  "<work>/build/z_maps/M03" F01`. Expansion tree of five maps: <work>/build/z_maps/expansion/KLExpansion (2.88 GB). re/maps.md 14.
  M02's boarding box had the bank's coordinates (kl_escape.board_box moves it; not run). No AI heisters on any (re/maps.md 14).
- DIAGNOSIS (agent z-freeze, re/freeze_1009.md) - CORRECTIONS to older entries below: the game is DIRECT3D 9 (imports d3d9.dll
  only; '-dx10' in the launch options changes nothing found); the 22:23 FREEZE had the reserve still held and no display driver
  fault (the 22:28 'watchdog' was the owner's Win+Ctrl+Shift+B): Quit from the score page, state 0x20 -> 0x2e, main thread never
  seen again, cause NOT established. DiscordHook.dll+0x1f7fd THREE times (17:08, 17:55, 00:25): the render thread inside Present,
  Discord's own pointer NULL, twice just after the window lost the foreground -> tell the owner to switch Discord's overlay off
  for this game. With the window not in front the main loop only pumps messages (Arcade pauses; scripted runs stand still).
- kl_watch.py took ONE picture of the Alt+Tab switcher over other windows (<work>/research/watch/20261009_174356/0081_661s.jpg;
  the owner has been told, the file is theirs to delete); grab() now also checks the window under the game's middle, twice.
- STOPPED by the lead at 11:25, nothing delivered (it died on the usage limit at 07:20, and the owner has asked another session
  to use less): workflow wf_b313b726-548 (.wf/bots.js, one agent b-bots): an AI heister squad for the Dead Men
  maps - the owner plays Arcade ALONE on every grafted map (0 bot squads). To come: tools/kl_fa_bots.py, re/bots.md, builds in
  <work>/build/b_bots/<map> made from the z_maps builds. Start it again only when the owner says usage allows (resume with
  that run id; the agent starts from the beginning, about 500k tokens).
- LIVE QUEUE, needs the owner's word once Steam is signed in (scratchpad now/QUEUE.txt; TEST hook <work>/build/klhook/test_stall):
  M8 six loads (klmem) -> M8b ReserveMB=176 RoomMB=128 -> PV1b Heister pictures with kl-merge-39's <work>/build/pd2/overlay/Overlay
  -> F1 <work>/build/fxc_slim/retomoto_loot -> PD2a/PD2b/PD3 Payday 2 masks (<work>/build/pd2/pd2_F01, scratchpad pd/PD2a.ini,
  PD2b.ini; rebuilt with the winding fix, cleared by kl-merge-39 at ~07:00) -> a z_maps map (M03 first) -> kl-merge-b6's Retomoto AI.
STATE 2026-10-10 01:35 - OWNER'S CRASHES 00:41, 00:44, 00:47 (all 0x8e5bbd, third / fourth level load of one process; dumps in
<work>/research/owner_crash_1010_0047) AND THE FIX, INSTALLED, NOT RUN IN THE GAME: the reserve held one block (the 74.6 MB .prm);
a level asks for five large blocks (32.0 scratch, 16.9 = .fxc, 74.6 = .prm, 20.6 = .ANM, 25.9 = no archive member) and the largest
free piece of address space shrinks from load to load (242 -> 32 -> 26 -> 14 MB; about 400 MB stay free in total), so the 20.6 or
25.9 MB block found no place while the reserve was 'in use'. klmem.c: the reserve is now an arena of several blocks; the .prm always,
plus any request of 1 MB or more the heap refuses (same as before in every case that worked). Proof so far: klhook/klmem_test.c
only (replays the requests in a cut-up 32-bit address space: PASS). Hook installed: SHIP <work>/build/klhook/ship_mem3 (sha1
bceda981); TEST sibling test_mem3; the previous one is ship_mem2. It also logs one 'memory: at the level's largest block: free
pieces ... in use ...' line per level load, writes the whole address space to <DD>/KLHook_map_0..7.txt at that moment (and
KLHook_map_refused_0/1.txt at a refused request), and its dumps carry the region list. THE ROOT CAUSE - what stays behind after a
level and cuts the space - is NOT known. What the old log shows: it follows PLAY TIME, not the number of loads (after 6-7 minutes
of play the largest piece before the next load is 26-32 MB; after 15 s sessions 96-207 MB). AFTER THE OWNER'S NEXT SESSIONS:
`python debug/vmmap.py <DD>/KLHook_map_0.txt <DD>/KLHook_map_1.txt` lists the allocations that came in between two loads by
size and kind and which free pieces they cut (copy the map files aside first: the next process overwrites them).
BUDGET for the builders: the five blocks are 32.0 scratch, .fxc + 0x60000, .prm + 0x60000, .ANM + 0x60000 and the WHOLE
<level>.WAV beside the archive. Stock F01: .fxc 5.9, .prm 63.5, .ANM 19.8, .WAV 14.7 MB; Retomoto: 16.9, 74.2, 20.6, 25.9 MB =
34 MB more than stock in large blocks. .fxc DONE OFFLINE, NOT LOADED LIVE: `kl_graft.py lighten <build> <out> --load fxc`
(kl_light.slim_cache) keeps what the materials ask for + sprite.fx, which is exactly what all 21 stock levels' caches hold:
Retomoto 242 -> 129 entries, 16.9 -> 8.9 MB; candidate <work>/build/fxc_slim/retomoto_loot (only the .fxc member differs from
the installed build; live check F1 = it looks the same). The .WAV (sounds nothing plays) is still open.
Known, older: material Weapons/BombWindow_02 (the bomb on the boardroom window) asks for glow30.fx MESH_RIGID, which no
cache has - it is not drawn. LIVE RUN OWED: scratchpad now/M8.ini (six loads in one process)
- it did not start because STEAM IS AT ITS SIGN-IN WINDOW (01:25; nobody signs in but the owner). Then try [Memory] ReserveMB=176
RoomMB=128 (all five blocks in the reserve from the second load on; klmem.c's comment). Also third DiscordHook.dll+0x1f7fd fault
at 00:25 (same callers as 17:55). Sessions now: kl-merge-01 = this one, holds the game; kl-merge-39 = Payday 2 masks + Heister
pictures (offline; rebuilt pair <work>/build/portraits/out2/Overlay waits for live run PV1b); kl-merge-b6 = Retomoto AI / street /
van (offline; re/retomoto_ai.md, builds in G:\kl_scratch\ai_*; owns kl_fa_street.py, kl_fa_author.py, kl_arms.py, kl_fa_van.py).
PAYDAY 2 MASKS - WORK IN THE GAME (2026-10-10 09:40-09:52, runs pd2-wolf / dallas / chains / hoxton / dallas-long; owner, relayed
by kl-merge-db: 'the payday 2 masks all work'). Log: 'wardrobe (version 2): 16 characters, 12 masks', 'body: ... the player now has
28509' (Kane), 'look: variant 1 -> 11' (wolf; 12 dallas); picture research/shots/pd2-wolf_60s.png: Kane at GO on Subway with the
plate on his face (drawn, not culled - the winding fix held). Build <work>/build/pd2/pd2_F01 (stock F01 + wardrobe + masks 9..12),
overlay <work>/build/pd2/overlay/Overlay (14 Mask entries + 31 pictures); the owner's SHIP hook already reads 1..12 masks.
Tools: tools/pd2_crate.py, pd2_model.py, kl_pd2mask.py, `kl_chars.py wardrobe <base> <out> --plates=wolf,dallas,chains,hoxton`;
notes re/pd2_crates.md, pd2_model.md, pd2_attach.md, pd2_klside.md. NOT DONE: the plates on the owner's Retomoto build (rebuild
the wardrobe step with --plates on the lightened base: the game holder's call); msk_backside (PD2's back shell) not carried; more
masks = kl_pd2mask.PD2_MASKS + mkoverlay PD2_MASKS + kl_chars.PD2_MASKS (room for 4 at step 14; more needs a larger step).
SIDE RESEARCH (offline, 2026-10-10): re/pd2_guns.md (39 single-piece wpn_npc_* guns, 254-441 triangles: the easy input for
kl_guns looks; unverified), re/pd2_audio.md + tools/pd2_audio.py (streams are Wwise PTADPCM, decoder verified; jukebox tracks
mapped; kl_str needs an external-clip entry point), re/firstperson_camera.md + re/firstperson_assets.md (camera-at-head +
hidden-body variant is feasible as a hook feature; animated PD2 first person is blocked by the undecoded .ANM key format).
STATE 2026-10-09 23:50 - INSTALLED FOR THE OWNER: F01 slot = <work>/build/y_loot/retomoto_loot (Retomoto + wardrobe + the loot
props: briefcases on the boardroom table, table stacks moved to the rims, armour as statue loot; NOT run in the game); hook = SHIP
<work>/build/klhook/ship_mem2 (sha1 6d0784ca: klnudge + klchar + the REWRITTEN klmem), KLHook.ini written fresh (copy of the pair:
<work>/build/klhook/owner_now), overlay Patch01.zip in <DD>/KLExpansion/Overlay (the Heister page WITHOUT pictures).
The owner's other session had left the TEST hook and a test script installed (input blocked): put right at 23:20.
klmem rewrite, live (TEST sibling test_mem2, runs M3-M5): the 74.5 MB .prm block is served from the reserve and 'was freed by the
game' on return to the menu, three times of three. SECOND LOAD SEEN (run M7, 23:53): after a quit to the menu the same process loaded the level again; largest free piece 46.6 MB,
74.6 MB asked, 'the block ... is in the reserve (use 2)', level loaded, PASS. Without the reserve that is the 0x8e5bbd crash.
(Runs M3-M6 ended on test-script faults: a stray ESCAPE, then a waitscene for a scene that was already loaded.)
Only ONE session may run the game or change the game folder; kl-merge-88 (Payday 2 masks, offline) has agreed to ask first.
GUN LOOKS (owner asked 2026-10-09 late: Dead Men gun models, Dog Days sounds, buyable, switchable; BUILT OFFLINE, NOT RUN IN THE GAME):
tools/kl_guns.py (docstring = the spec). New guns are NOT possible: 64 weapon items compiled in (eFF2ItemCount), the shop's 36 entries are a
table in hashed .rdata (0xbd1f70: price, rank, tier, DLC, item, ammo). Gun models are the same format in both games (rigid parts on
w_bone_* bones, same grip place), so a Dead Men gun is added as hidden PARTS of a Dog Days gun's model (variant 100 + n) and klhook/klgun.c
shows one group by writing variant bytes in the loaded .prm (KLGuns.ini beside the archive). Looks: MP5 and AK-74 on the starting Zastava,
SG 552 on the FN SCAR, M4A1 on the AK-47, P90 on the UMP, Steyr TMP on the MAC-10, USP on the M9 Beretta. Menu: button 'Guns' + window
KLGuns (mkoverlay.py; options KLGunStart / KLGunSet through klchar.c's private vtable). Kept build <work>/build/guns/guns_F01 (stock F01,
problems: 0; pictures: `kl_guns.py sheet`). LIVE CHECKS OWED: G1 the build with the old hook plays as stock; G2 Start=1 shows the MP5 in
the hands (is a part's variant read every frame, or cached per gun instance?); G3 reload / drop / pickup; G4 the Guns page. NOT DONE: the
shop's name and picture of a switched gun; Mini-14 and Taurus (in no Dead Men level's equipment tree); the wardrobe and the guns in ONE
build (run kl_guns on a wardrobe build folder: not tried).
HEISTER PAGE PICTURES (owner asked 2026-10-09 22:35; BUILT, NOT SEEN IN THE GAME): tools/kl_portraits.py renders the 16 characters and 8 masks
(kl_view; <work>/build/portraits/*.png, sheet.png) and adds them to a COPY of the menu scene as picture entities KLPic_* (texture -> sprite chunk ->
picture chunk -> ZWINGROUP + ZWINPIC; layout in its docstring; check: 0 problems) = <work>/build/portraits/out/Overlay/Scenes/kaneandlynch.zip;
klhook/mkoverlay.py --pictures puts two ToggleImages on the page. Both files must be installed TOGETHER under <DD>/KLExpansion/Overlay. Nothing of
it is installed. Live run PV1 (scratchpad pv/runpv.py, menu only) did not start: Steam was at its sign-in window after the owner's reboot.
Owner's plan: pictures first, then a preview of the model with mask and outfit together (not started).
OWNER'S FREEZE 22:23 (reboot 22:30): after an escaped round on Retomoto + wardrobe, second session of the process, the main loop stopped while
leaving the session (state 0x20 -> 0x2e, never 0x0); no dump; Windows logged display watchdog reports at 22:28. Free address space was 140 MB
(largest piece 35.8 MB) after that load. Cause not established.
LIVE RUNS: RESUMED IN PART (owner, 2026-10-09 18:45: 'crack on' with the wardrobe, re/wardrobe.md, and
the gfx note). One live agent (u-live) runs between the owner's sessions, never while kl2.exe is
already running, and puts the owner's Retomoto build + SHIP hook back after every run. The gfx test
run (install of KLGfx d3d9.dll) was REFUSED by the permission classifier: the owner can run the two
.bat files themselves; the GPU self-test ran (4 PASS, 2 FAIL: zero model changes the picture by 8,
limit 3; network 8.6 ms at 1080p, 13.7 ms at 1440p on the RTX 4070 Ti).
LOADING SOLVED (2026-10-09 22:10, experiment E1 of re/loading.md, klhook/klnudge.c from the owner's other
session): Retomoto + wardrobe, game window in front, TEST hook from f50df89, same slot, same script.
[Load] NudgeMs=1000: menu -> level in 2.7 s (22:03:57.6 -> 22:04:00.3), 'level loaded' 4.4 s after
the start. Control (NudgeMs=0, Count=1): 124 s to the same session state and 211 s to 'level loaded'.
The game's GetForegroundWindow / cursor nudge costs about 1 ms per call: the control never exceeds
~1,100 calls a second, also in play, the test reaches 22,456 a second in the level. So it is paid
per FRAME too. Installed for the owner: SHIP build with klnudge.c (<work>/build/klhook/ship_nudge)
and [Load] NudgeMs=1000 in KLHook.ini. Not yet watched for mouse side effects in real play.
INSTALLED FOR THE OWNER 2026-10-09 21:50 (supersedes the 21:25 entry below): F01 slot =
<work>/build/x_chunks/retomoto_wardrobe (play3s + the FULL wardrobe in dead chunk indices: 65,119
table entries, .prm 77.8 MB; KLJoin.ini + KLWardrobe.ini); hook = <work>/build/klhook/ship_mem
(SHIP + klchar.c + klmem.c, sha1 dfd3399f); overlay and KLHook.ini as before. Live before the
hand-over (TEST sibling test_mem, run RW): Kane (model 9236, a reused index) drawn on the balcony
at GO, round PASS. Owner's 21:39 crash = the .prm allocation failing on the SECOND level load of a
session; klmem.c is the answer, its release path not yet seen firing. Outfit 3 on Kane showed no
visible armour from behind in the one picture looked at: not checked further.
INSTALLED FOR THE OWNER 2026-10-09 21:25: F01 slot = <work>/build/play3s = Retomoto with every fix
since their last round (execute crash, kl_arms weapons, police far-detail shader, voice repairs
VOICE on, Subway-style blast layer, bone ids) and 'kl_graft.py lighten' (.TEX 405.6 -> 234 MB, zip
188 MB), KLJoin.ini; hook = <work>/build/klhook/ship_char (SHIP + klchar.c, sha1 ac7e1569) with
KLHook.ini [Expansion] Enable=1 and [Character] Enable=1; <DD>/KLExpansion/Overlay/Patch01.zip =
the Heister page. The previous hook pair is in <work>/build/klhook/owner_prev. Live before the
hand-over: play3s round PASS (run P3s: balcony, glass goes at the blast, the standing scripted
player is shot dead ~20 s after GO); Heister page labels now SHOW (run W2L: 'Tommy', 'Moustache -
J.C.', 'Plain clothes'); the SHIP_char build starts and loads all its parts (run SHIPC).
NO WARDROBE on Retomoto yet - HARD LIMIT FOUND: the .prm chunk table at 0xeac7b0 is fixed-size;
Retomoto + full wardrobe has 80,627 chunks and its entry for chunk 73,932 lands on the loading
progress object (crash kl2+0x207280, run P4). Retomoto alone has 65,119. Agent x-chunks is
establishing the exact limit and making the wardrobe reuse dead chunk indices (re/prm_limit.md).
LOADING: with the game out of the foreground (kl_loadfocus cover window) Retomoto still took
198 s to load: the foreground explanation of re/loading.md is NOT confirmed by this run.
WARDROBE LIVE (19:11, re/wardrobe.md 'Live outcome'): Dead Men player models WORK in the game. Kane and
Lynch are drawn and playable as the local heister on stock Subway and on the grafted bank (a model
no entity names is drawn; body swap through the game's own routine), a borrowed mask works on a
Dead Men body, the armoured outfit variant is set, the 96.5 MB bank .prm loads, the Heister page
opens and sets the three options. DEFECT: the page's value texts are blank. Not run: the SHIP
build of the hook with klchar.c, ragdoll / cover, a restart. Nothing of it is installed for the
owner; the slot is back on Retomoto play2.
GFX NOTE DONE (owner said 'you can do it', 18:50): KLGfx 0.3 nrtest ran once in the game (run GFX2,
installed by hand because the .bat counts the 21 lingering dead kl2.exe entries as a running game;
d3d9.dll moved to <DD>\KLGfx_removed afterwards). <DD>\KLGfx.log: 'KLGfx 0.3, mode 1 ... NR bridge
on', 'NR: started ...klnr.exe (model none), 2560x1440'; klnr.log: 'ready on RTX 4070 Ti in 1094 ms',
'the game has ended', exit 0. NO 'N frames through klnr' line (the run was ended by kl_autotest's
kill at 110 s, in the menu). NO PICTURE: neither kl_autotest's shots nor kl_watch got a frame with
the proxy in (both work without it, run GFX1), so whether the right half was grey - or whether
the game drew at all - was not seen. Self-test: 4 PASS, 2 FAIL (above). The note file is removed.
EARLIER NOTE - LIVE RUNS WERE PAUSED (owner, 2026-10-09 17:15): the owner is playing. Test runs take the game
(one kl2.exe, one F01 slot, a test hook that blocks the real keyboard and mouse), so NO agent
launches the game, swaps the hook or installs into the slot until the owner says to resume.
Offline work only. The scheduled wake-up prompt's "install / autotest" steps do not apply while
this note stands.
OWNER'S TWO CRASHES ON RETOMOTO, 17:37 and 17:41 (re/crash_owner_1009.md, tools/kl_impact.py):
- 0x4c34b3 (bullet mark on a person, 0x88c840): a shot hit a Dead Men GUARD in a bone whose id
  byte (bone definition +0x3e) still had Dead Men's number while kl_chars.reid had renumbered
  only the skeleton's id table [5]; table[old id] = 0xff was used as a matrix index. OUR
  regression, in every Dead Men map built since the skeleton rebind and in every kl_chars model.
  Fix: kl_impact.sync_bone_ids after reid / rebind in kl_graft.build (and in kl_chars.put),
  kl_impact.bone_faults in verify. NOT YET WIRED into kl_graft (m-load is editing it).
  Repaired copy of the played build: <work>uild
_crash\play_rt_boneids (kl_impact: 0
  problems; never run live) - install it when the owner has closed the game.
- 0x8e5bbd at load: the 60.7 MB .prm block failed to allocate in a 2 GB process (kl2.exe is not
  large-address-aware) with 1828 MB of address space in use (NVIDIA driver 190 MB, 104 threads'
  stacks, overlays: Medal, NVIDIA capture, Steam). Intermittent; stock levels can hit it too.
  Keep .TEX near the stock 290 MB and .prm small on every map (the four DM maps' .prm are
  75-87 MB: larger than any stock level). Hook idea (not written): reserve ~96 MB at start and
  release it when a large HeapAlloc fails.
OWNER PLAYED A WHOLE ARCADE ROUND ON RETOMOTO (17:44-17:55, build play_rt, SHIP hook; seen through
tools/kl_watch.py: 82 pictures in <work>/research/watch/20261009_174356): boardroom, loot
($1,285,000), stairs, the join by the hook (tower -> lobby in 0.5 s), lobby, street, 'You jumped
into the getaway car', ROUND OVER, Buy weapons. Then FATAL in DiscordHook.dll+0x1f7fd as round 2
started (second time in that DLL; dumps in research/owner_round_1009_1755; cause not looked at).
OWNER BY EAR: music plays; 'the yakuza / retomoto soldiers all replay the same thing too many
times - make it play once or make sure theyre unique each time' (agent q-repeat is on it).
LOADING (re/loading.md): slow loads (100-200 s) follow the game window being in FRONT, fast ones
(11-15 s) it being in the background; hook fix proposed (GetForegroundWindow slot 0xb10594), not
written. VOICE (re/voice.md): repairs built, kl_snd.VOICE = None (off) until heard.
kl_graft now syncs bone ids (the guard crash); builds made before 346c37e need kl_impact.py fix.
INSTALLED FOR THE OWNER 2026-10-09 18:10 (they said the game was closed): F01 slot =
<work>/build/play2 (zip sha1 514c4689): Retomoto with the start on the balcony outside the window,
the bomb fuse, staged tower fight, the Heat street layer (tools/kl_fa_street.py; positions are
GUESSES) and the bone-id fix (kl_impact: 0 problems). KLJoin.ini = klhook/KLJoin.retomoto.ini (the
front box). Hook SHIP 3f3f4f00, extended PC_Def.str as before. NEVER RUN IN THE GAME before this.
The previous build is <work>/build/play_rt (bone-fixed copy: build/n_crash/play_rt_boneids).
OWNER PLAYED play2 (18:09-18:20, two rounds; pictures <work>/research/watch/20261009_180847): the
BALCONY START WORKS ('Heist starts in 9 sec' outside the glass, then in), loot to $2,080,000, the
join, the street. Their report: (1) CRASH 'when i went to execute': kl2+0x98a1 in
ZFFActionShootHumanShield slot 11, null read (dumps: research/owner_round_1009_1820); (2) ran out
of ammo clearing everyone solo; (3) 'some of the police outside are invisible'; (4) enemies all
carry the same pistol - wants weapon variety (lead: kl_graft.dm_rename hands Dead Men pistol
carriers Dog Days' HUMAN SHIELD pistol template); (5) gunfire sound outside 'is sick' (good).
Agents s-combat and s-visible are on (1)-(4), q-repeat on the repeated guard lines. All offline.
STILL TO WIRE: the three kl_fa_street lines in kl_fa_author.py (re/retomoto_street.md); until then
only `kl_fa_street.py test` builds with the street.
INSTALLED FOR THE OWNER (2026-10-09 17:20, at their request "both parts and also the music"):
- F01 slot = Retomoto, <work>\build\play_rt\... (committed tools at 250a610, `kl_fa_author.py
  test --keep --guards-wait --blast-delay 9`; start still inside the boardroom), zip sha1 92e07f51.
- Hook = SHIP build <work>\build\klhook\ship (sha1 3f3f4f00; Steam guard on, real input NOT
  blocked) + its KLHook.ini; Scenes\Locations\F01\KLJoin.ini = klhook\KLJoin.retomoto.ini.
  The original hook pair is in <work>\build\klhook\direct_boot\.
- <DD>\PC_Def.str = kl_str's EXTENDED merge (1,684,486,009 bytes; old offsets kept, Retomoto's
  music / blast / ambience appended); <work>\build\PC_Def.str + map are the same pair, the
  previous pair is PC_Def.kl_audio.str(.map.json). KL_PortBackup's original untouched.
- One run (PLAY1, the owner at the controls): clean exit after 333 s; log shows the guard
  ('NOT stock', one SetAchievement BLOCKED), the join box resolved to entry 5 '06_Exit'; a
  picture at a samurai case.
- OWNER, 17:35, BY EAR: the Retomoto MUSIC plays (first sound confirmed by anyone). Asked for: more
  character VOICE LINES ('normally when you play idle too - it feels too quiet from the
  characters'), FASTER LOADING (game is on an SSD), and to be watched while playing: 
  `python tools/kl_watch.py` takes pictures of the game's own window with ffmpeg (passive: no
  input, no camera, no microphone) into <work>
esearch\watch\<run>\ with the hook's log.
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
- PLAYER MODELS + HEISTER PAGE (owner released stage 2 and asked for a character / mask screen, 2026-10-09
  evening; re/wardrobe.md). Built OFFLINE, nothing run live: `kl_chars.py wardrobe` (Dead Men heroes as extra
  models, 16 bodies x 8 masks as variants, KLWardrobe.ini; kept builds <work>\build\chars\wardrobe_F01 and
  wardrobe_bank, problems: 0), klhook\klchar.c (menu options KLChar / KLMask / KLOutfit by a private vtable;
  body through the game's own swap routine 0x8f5e90, look through 0x88c810; Arcade only), mkoverlay.py (button
  'Heister' + window KLHeister), tools/kl_view.py (software renderer: models can be LOOKED AT offline).
  Live checks W1..W6 of re/wardrobe.md are the next live work for this; the largest unknown is whether a model
  no entity names is drawn (W5). The bank's .prm becomes 96.5 MB with the wardrobe (over kl_graft's 90 MB).
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
- Go-ahead for PC_Def.str; <DD>\KLExpansion (360 MB) keep?
- Wardrobe / heister page: say when live runs may resume (checks W1..W6); they need the new hook DLL, the
  overlay Patch01.zip and a wardrobe build in the test slot - none of that is installed.
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
- OWNER, 2026-10-09 22:00, after playing the wardrobe build: guards good, blast and shake 'amazing',
  police show up, the armour shows. LOOT PROPS: briefcases (not bags) in the start room; the stacks
  on the left side from spawn cannot be picked up - move them closer to the outer ring; the statue
  loot gets a fitting prop instead of a bag (agent y-loot). Execute not tried yet.
- OWNER, 2026-10-09 18:40, after playing the balcony start: the blast must be more VOLATILE,
  'like the subway one in the original game when u start in': it does the explosion but there is
  no smoke and no camera shake. Wanted: smoke / dust, debris, shake (agent t-blast).
- OWNER, 2026-10-09 17:00, after SEEING the tower in the game (supersedes the start options A / C
  and the spawn row inside the boardroom): the heisters start OUTSIDE, on the ledge just before
  the glass of the main window, and THEN the blow-up sequence happens and they go in.
  To build: a standing surface outside the window (x > 5850, boardroom floor y ~20996; in the
  campaign the players hang there on ropes - whether any walkable geometry / collision exists
  there is NOT known: check, else author an invisible ledge), the intact glass keeping them out
  until the blast, START row outside facing -x into the room, guards unaware until the blast,
  a kill / bounds answer for stepping off the ledge.

## Payday 2 (owner, 2026-10-09)
Later wishes: play as a Cloaker, Payday 2's original maps, its characters, a first-person view.
DECIDED for now: only the Payday 2 MASKS ("the most iconic"), as further entries of the wardrobe's
Mask row (a mask is a rigid whole-head piece: tools/kl_chars.py wardrobe, klhook/klchar.c,
re/wardrobe.md). Bodies, first person, Cloaker and maps are not started.
State (2026-10-09 23:30): Payday 2 IS INSTALLED: `C:\Steam\steamapps\common\PAYDAY 2` (64-bit,
Steam build 25506656, 34.65 GB; the G:\SteamLibrary folder of that name is a stale remnant with two
2021 crash dumps). Its store is the NEW crate format, not the `all_N.bundle` / `bundle_db.blb` the
public tools read: `assets\*.crate` (98 files; header 'YAOI', u32 1, u64 n, then n x 48 bytes = ext
idstring, path idstring, u64 offset, u64 raw size, u64 stored size (0 = raw, else zlib), u64 ?;
data from offset 1,000,000; sorted by (ext, path)), a shipped text `hashlist` (186,212 paths
without extension), `crates.shipping_manifest`, `crates.properties`. idstring = Jenkins lookup8
hash64, level 0 (confirmed). 307 mask folders under `units/payday2/masks/` (the four crew masks:
msk_dallas, msk_chains, msk_wolf, msk_hoxton, each with `_df` / `_nm` textures). Owner: WOLF FIRST.
Readers: `tools/pd2_crate.py`, `tools/pd2_model.py` (in progress; research notes `re/pd2_*.md`);
extracted data lives in `<work>\pd2\` only. Same rule as for both Kane & Lynch games:
assets stay on the owner's machine, never committed, never shared.

## Roadmap for a rewrite (only after the port works)
Ghidra project of kl2.exe + kaneandlynch.exe, shared symbol/type database (classes, vtables,
property schemas dumped at runtime by KLHook), then an owned-asset engine reading original files
(hl2-rs model). Never redistribute game code or data.

## Working rules
- Verify before every install; commit each fix with a message saying what crashed and why.
- Don't guess silently: if a field mapping is a guess, say so in the code comment.
