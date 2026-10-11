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
OWNER, 2026-10-11 ~13:00, AFTER MORE ROUNDS (the park and others; hook ship_main1, [Fed] Player=1), his words: 'for the fed on in the night park or maybe any map if you die too early you cant kill itll just say you cant kill before you heist like before the money is picked up they still on green crosshairs to indicate friendly when in reality it should be red and the enemies are the inverse of that. make sure to use a model thats correct for the map so i was normal swat but i should be the yakuza biker outfit and then on withdrawal normal swat etc. and make it so u have a chance to come back with an ak 47 instead of only just having the mp5. also the ai seems to leave early, they should have to get to the car physically and make it so they're normally moving majority of the time ... sometimes they just be standing still a bit, they need to know how to kill civs some of them otherwise they cant get money, they should go onto like a money square thing and if nothing happens for like 5ish seconds they get fed up n move but if they do end up getting the money they might go back for it, also need something for making them a bit more bullet spongey, feels a bit one sided so the player could just easily turn on them, i saw one backstab me it was too lenient i could get away with killing him, so make it a lil less forgiving and if i shoot them but before i turn traitor the more i shoot the more they shoot back or they might just try and kill me straight away or they just accept getting shot ... fed spawns definitely need a fix on all maps im guessing and still definitely want multiplayer to work at somepoint so maybe look into trying to fix netcode on your side / making it less spin botty in online ... on the private lobby so these maps can be started'. HIS LOG (the park, slot F04): round 12:41:23, the crew called the helicopter and 2 left GO+114 s 'without you', he died 3 s later, a fed 9 s after ('at (0, 0, 0)' = the place line reads too early); next round dead GO+15 s, a fed 5 s later with all seven heisters still at stage 0 (= 'cant kill before you heist'), 'dead for good' 82 s after; every police body is 'type 3 ... model 1919' (F07's policeman) on every map. RUNNING, OFFLINE (the owner is at the PC): workflow wf_69f9819b-26e, five tracks, each worked -> adversarially reviewed -> fixed (tasks: scratchpad wf/_RULES2.md + M_fed_kit.md, N_bots_move.md, O_bots_fight.md, P_bots_civs.md, Q_netcode.md): M = the fed can hunt from the first second + crosshair sides, the map's own enemy body (the park: yakuza bikers), a chance of an AK-47 (new klhook/klfedkit.c, tools/kl_fa_fedbody.py, re/fed_kit.md); N = why bots stand, a keep-moving watch with the owner's loot-square rule ([Bots] Restless), the crew does not go without you ([Bots] WaitForYou), a bot walks to the vehicle before it counts (new klhook/klmove.c, klescort.c, re/bots_move.md); O = crew tougher against the player, a backstab that means it, three answers to being shot by you (escalates / snaps / takes it: [Bots] Grudge) (klbot.c, klbalance.c, re/bots_fight.md); P = some bots kill the money civilians, the civilians' money back on (new tools/kl_fa_bots_civ.py, builds <work>/build/z_civ, re/bots_civs.md); Q = research: a private lobby starting a Dead Men map, which hook parts must be host-only / off online, the 'spin' of remote bodies (re/netcode_fa.md, maybe a log-only klhook/klnet.c). Each new hook part is its own file, NOT wired: the lead wires klhook.c after the reviews. STILL RUNNING FROM BEFORE: wf_3b10398f-598 (K street lanes, L fed places), wf_59d1d830-90b (H3). NOTHING of this is on the owner's game.
OWNER PLAYED THE NEW BUILD, 2026-10-11 12:28-12:35 (Retomoto = the gates, hook ship_main1, the fed on): 'okay yeah spawn as a fed but in a lift and also the ai is almost good, when doing the run to the car they need to spread out more like some try going to the other side some stay on that side etc. they need to use the map a bit more but the tower of retomoto tower is beautiful now'. HIS LOG: seven bots at the join ('crewjoin: 7 moved' 12:31:00), he dies on the STREET 40 s after it, 'fed: YOU ARE A FED ... at (1804, 19601, 812)' = IN THE TOWER BY THE LIFTS while the whole round is in the street half (and inside a lift); 'balance: you are POLICE now ... (44 value(s))' in the same tick; 'backstab: nobody was picked this round (Backstab=35%)'; three bots dead on the street in the next 80 s; he left the round. So: THE TOWER'S GATES ARE APPROVED BY THE OWNER; the fed respawn works in his game and its PLACE is wrong on Retomoto; the street run wants lanes. RUNNING: workflow wf_3b10398f-598 (two tracks, each worked -> reviewed -> fixed; tasks scratchpad wf/K_street_lanes.md, wf/L_fed_points.md): K = the street half of kl_fa_bots_rt (lanes on both sides, holds at cover, a different deal each round; builds <work>/build/z_lanes; the tower untouched), L = how kl2 picks the respawn place (slot 199), every AFTER_DEATH point of the five maps against collision / doors, Retomoto's answer for the two halves (level data by the JumpPoint's list, or klfed.c), a new tools/kl_fa_fedpoints.py as a step on finished builds (<work>/build/z_fedpts).
12:45 2026-10-11 (the owner at the PC: nothing is run in the game). (1) THE POINT-BLANK KEYS ARE IN THE HOOK'S SOURCE, OFF (1aff1be = kl-merge-9b's re/melee_damage.patch applied as written; [Balance] PointBlankToYou / ToCrew / ToCop = the number in place of the fire task's 100, 100 = log only; hooks <work>/build/klhook/test_pb1 ac21b576 / ship_pb1 fa400bca = the newest; NOT RUN, not on the owner's game: his hook is ship_main1). The decision for the owner once P0 has run: under his Risk=2 a firing guard within 1.6 m costs him 7,560 a step (stock at level 1: 756 of 550 - the game's own design), and an AI heister 432 of 252 at CopToCrew 0.05 = the bots' 'ONE STEP' deaths. (2) THE CAMPAIGN BANK (M03_A as a Fragile Alliance map) IS BEING BUILT BY kl-merge-9b, offline: its files tools/kl_maps.py, kl_graft.py, kl_fa_author.py, kl_map_escape.py + new kl_fa_bank.py, kl_route.py are OFF LIMITS for this session until it delivers <work>/build/c_bank/ and re/bank_campaign.md; packaging onto the tab and the live loads are this session's. (3) RUNNING OFFLINE: wf_59d1d830-90b (track H3: kl_playtest third round - the start delay after state 0x19, no stop beside a firing guard, `--die --fed-walk` scripts for all five maps into <work>/research/playtest/v3; task scratchpad wf/H3_playtest_fed.md). (4) THE AWAY QUEUE is written down: scratchpad now/QUEUE_live.txt (H1q with hud_test17 for kl-merge-3e; FollowOut hold / spare; the fed on the other four maps; point-blank P0; the climb K2d on w_tabK; Bribe / Leave / Van; Late Night with the scripted human; the campaign bank when delivered).
INSTALLED FOR THE OWNER 2026-10-11 12:25 - THE OWNER IS BACK AT THE PC (12:15: 'push everything to the main build including the campaign fa maps n stuff and enable come back as a fed and anytthing else that can be enabled like backstabbing if youve made the bots decide on their own'): WATCH-ONLY AGAIN, every queued scripted run was stopped before it started (H1q for kl-merge-3e, FO2_J4 / J2 / J3, K2d the climb). Game closed, then: tree <work>/build/w_tabM (= w_tabX with DM09 = <work>/build/z_rooms/retomoto_full = THE SEVEN GATES, second form, and the new settings block); hook SHIP <work>/build/klhook/ship_main1 5868b48f (built from the committed sources at the head of the branch: + FedMirror, FollowOut, klclimb fourth version (off), klhud (off); TEST sibling test_main1 d224a3c1; the previous pair is in <work>/build/klhook/owner_prev_1011_1230); his KLHook.ini: NEW [Fed] Enable=1 Player=1 Log=1 (come back as a fed: live on Withdrawal only - the other four maps have their 5..7 AFTER_DEATH points, kl_fa_fed.py plan, but no round with a death has run there), [Bots] FollowOut=1 (live once, FO_J1), Tune=1 + Backstab=35 (live in K2, 2026-10-10), Escort=1, BoardAll=1 as before, [Balance] Risk=2 CopToCrew=0.05 as before (FedMirror defaults to 1). Start-up check SHIPM1: 'bots: on; ... Tune=1 (Traitors=1 Limit=6.0 Retaliate=0) Backstab=35% ...', 'follow: on; FollowOut=1 ...', 'balance: on; ... FedMirror=1', menu reached, no fault (that start was before [Fed] went into the ini). NOT ENABLED, and why: [Fed] Bots (AI heisters as feds: needs the x_fed2 builds, never loaded), FollowOutHold / FollowOutSpare, Bribe, Leave, Van (none has run in the game), [Climb] (the crash fix has not run), [HUD] (kl-merge-3e: strings draw only through stock objects so far), [Guns] (the Guns page: klgun Version 2 never seen live since the owner's 'grey screen'). CAMPAIGN FA MAPS: NOTHING IS BUILT - re/campaign_fa*.md is a study (kl-merge-9b) and is on main; told the owner. TO RUN WHEN HE IS AWAY AGAIN (scratchpad now/): chain_h.py (FO2_J4 spare, FO2_J2 hold, FO2_J3 all), chain_g.py's K2d (the climb; needs the test tree w_tabK - and it must then put w_tabM back, not w_tabU), H1q for kl-merge-3e (stock.py H1q_stock hud_test16 60 "[HUD];Enable=1;Log=2;HideStock=0;"), the point-blank dry run P0 of re/melee_damage.md after its patch is applied to klbalance.c.
POINT-BLANK RULE FOUND (kl-merge-9b, 2026-10-11 12:20; asked by kl-merge-31; re/melee_damage.md, checked by three second
readers; STATIC READING + the logs, the patch NOT RUN): the 'one-step kill' is NOT melee. kl2 0x8c62e0 (ZFireWeaponTask, called
from 0x7c0748 / 0x7c0a14): at every burst step (0.1-0.2 s) while a soldier's target is within 160 units (1.6 m) it sends the
target a 'ProjectileHit' of its own gun at the head with scale 100.0 (hit record +0x18, from float 0xb5c050, hashed .rdata).
The victim's ordinary bullet routine multiplies it in (0x4db8a2 player, 0x61acc6 NPC) - and the Arcade dial too, so the dial
DOES apply: one step = 100 bullets. 151.2 = SMG_Type79 72.0 x 1.05 x 100 x CopToYou 0.02; 758.6 = HG_SW_MP45 361.25 x 2.1;
30.2 = the same-attacker limiter x 0.2 (over 0.75 x max health in 2 s: 0x4dbad9). At CopToYou 1.0 (Risk=2) a step is 7,560;
stock level 1 (0.1) is 756 of 550: the game's own rule, on every map. An AI heister: x 1.2 whole x CopToCrew = 432 at 0.05
of his 252 - most likely what kills the bots in rooms full of guards. The TRUE close combat (0x499570: 50.0 flat) is another
path, not in the logs. KEY READY, NOT APPLIED: re/melee_damage.patch for klbalance.c ([Balance] PointBlankToYou / ToCrew / ToCop =
bullets a step is worth; 100 = stock = logged only; a private vtable copy on the ZEngineDataBase object, slot 19 wrapped, +
one heap float; compiles SHIP + TEST, off-game harness 92 checks PASS). kl-merge-31 holds klbalance.c and the live order
P0 (dry) .. P5 of the note; P5 needs no patch: CopToYou=0.01 must give 'you lost 75.6' a step.
LIVE 2026-10-11 12:01-12:04, run FO_J1_DM03_follow - FOLLOWOUT WORKS IN THE GAME (the bank, hook test_fo1, [Bots] FollowOut=1, the scripted human): 'follow: you are at heist stage 3 (in play, $480000); vehicle state 1, timer 6.7 s: THE CREW IS CALLED - 7 AI heister(s) ...', per bot 'record N (stage 1, $M) at (...), 52 .. 83 m from the boarding place: heist stage set to 3' + 'sent to the boarding place (-2910, 278, 652), the game set (-2910, 150, 652); order 1' (the escort gets the byte, not the order), 'the vehicle arrives in 1.7 s (call 1): no order from here on'; at the wait edge five of six are 'coming (5.2 .. 7.0 m nearer in the last 2 s)' at 56 .. 68 m; 'record 7 aboard 7.0 s after the crew was called', records 3 and 1 aboard at 14 / 15 s, 'the vehicle leaves ... with you aboard: 3 of the crew aboard, 4 left in play', those four shot 44 .. 61 m short ('... - LEFT BEHIND'), 'over (you escaped): of the crew 3 escaped, 4 dead'. The control PB_DM03_board_hp: 2 aboard, 4 shot inside the bank. So the bots DO come (about 3 m/s) and the 15 s from the call to the departure are too short for a crew that is 60 .. 80 m back: FollowOutHold is what it needs. No fault, no soft line. THE OTHER THREE RUNS OF THAT CHAIN (J0 dry, J4 spare, J3 all) SHOW NOTHING: the scripted human was dead GO+31 .. 48 s at the control-room stairs (-349, 436, -5887) WITH 5,500 HEALTH - 'you lost 909.8', '758.6', '1341.4', '582.8' a tick = five to nine hits of 151.7 at once, a burst every 0.12 .. 0.19 s, none of it scaled by CopToYou 0.02 (a shotgun's pellets? told kl-merge-9b, who reads the 151). The second version of H's script stops there (its new 'real stops'), the first version runs through: the three checks are queued again on the first version's script (scratchpad now/chain_h.py: FO2_J4 spare, FO2_J2 FollowOut + Hold=15, FO2_J3 all three; hook test_climb2), then chain_g (K2d the climb; the owner's tree w_tabU). HUD: H1p (hud_test16) put its strings into the stock player list's five rows and hid the element in the same tick ('stock block hidden'): H1q with HideStock=0 is in the game.
12:05 2026-10-11 - (1) THE CLIMB'S CRASH IS EXPLAINED AND FIXED OFFLINE (d75436e; re/climb_crash.md, re/climb_crash_review.md; track F3 worked -> reviewed -> fixed): the animation update hands a clip's events to the player's current action; a Dog Days mini animation's event routine (kl2 0x637060) acts on event id 5 by aligning to the action's object, which a mini animation does not have (0x6370e7 -> 0x47e400 reads [0+0x60]); Dead Men marks the climb's first alignment with exactly id 5 at frame 6. Now the 7 players' climb clips carry id 105 (tools/kl_fa_climb.py; <work>/build/z_climb3/M03 = z_cover3/M03 + the clips, check PASS) and klclimb.c (fourth version) refuses / stops / calls off for any clip or other channel of his whose event the game would act on. THE CRASHING PAIRS STILL LIE IN THE WORK FOLDER: hooks test_climb1 / ship_climb1 with levels z_climb/M03, z_climb2/M03 (first form) - do not run them. Newest hooks, from the committed sources: <work>/build/klhook/test_climb2 ca4de08e / ship_climb2 fe71c95f (= everything: rig, FedMirror, FollowOut, klclimb fourth version). QUEUED (scratchpad now/chain_g.py): K2d_DM03_wall on the test tree <work>/build/w_tabK (DM03 = z_climb3/M03), the wall script with W let go before the climb (runs/K2d_DM03_wall.ini). (2) G2_DM09 = the gates' SECOND form with an idle player: clean, the gates' clock door GO+85, reception +120, atrium +136, gallery +171, second floor +205, first floor +239, lobby +273, the car +307; one 'ONE STEP' kill (240) at the reception GO+119 s, the other five deaths GO+216 .. 318 s on the second and first floor; the escort lives - the same picture as G1. (3) DECISION: RETOMOTO ON THE OWNER'S TAB BECOMES THE GATES BUILD (z_rooms/retomoto_full, second form): old chain = six dead by GO+79..122 s idle and all five dead 49 s after the join (J0); gates = nobody dead before GO+119..175 s idle (G1, G2), seven at the join and six alive 78 s after it (J1), a whole heist through both halves (B1). chain_g installs <work>/build/w_tabU (= w_tabX with DM09 = that build) as the owner's tree when its runs are through; the hook stays ship_vis2.
11:50 2026-10-11 - TRACK J IS IN (2b3f1fd; re/bots_follow_out.md, re/bots_follow_out_review.md; worked -> reviewed -> fixed; NOT RUN IN THE GAME): WHAT KILLS THE CREW LEFT BEHIND is stock Arcade's own rule - ZGameRulesHeist slot 194 (kl2 0x8fa6d0), vehicle state 5 'drives out', makes a shuffled table of times at rules+0xeec / +0xf1c ONLY WHEN THE HUMAN IS ABOARD, and slot 7 (0x74b6d0) then hits every AI record in play with 1,000,000 damage, one about every second for the 8.4 s of the drive-out; no distance / stage / traitor test; with an idle human none of it runs; not in the multiplayer classes. THE PAYOUT (0x796410): what the escaped non-traitors carried is pooled and each gets the same share - so the kill costs the human nothing, and every bot got aboard joins the split. NEW KEYS in klescort.c, all off by default, nothing on a stock level / for a police human / with VanLeftBehind: [Bots] FollowOut=1 (once the human has heist stage 3 every non-traitor AI heister in play gets stage 3 - one byte, only with a valid ZFFActor - and one order to the boarding place while the vehicle drives in and is 2 s or more away), FollowOutHold=N (while the human sits aboard and called crew still comes nearer, the wait timer [rules+0x1d8] gets up to 5 s more under 2 s, N s a visit at most), FollowOutSpare=1 (works alone: the kill times are put off, nobody is shot, the round ends as ever, no payout change), FollowOutDry=1. Hooks <work>/build/klhook/test_fo1 8dcd915c / ship_fo1 b999f0e2 = the newest, built from the committed sources. QUEUED (scratchpad now/chain_f.py, the bank, the scripted human + the keys): J0 dry, J4 spare alone, J1 follow alone, J3 all three; the control is PB_DM03_board_hp (four shot at the departure).
LIVE 2026-10-11 11:28-11:32, run B1_DM09_board_gates - A WHOLE RETOMOTO HEIST BY THE SCRIPTED PLAYER, BOTH HALVES (tree w_tabU = the gates' second form, hook test_pt5, Escort=1, BoardAll=1, position log): GO 11:29:15; the balcony, the table ($300,000 from two stacks), the tower's stairs, 'join: player 0 entered box 9' GO+110 s, 'crewjoin: 6 moved' (one bot had died in the tower), the lobby, 'record 0 (you): heist stage 1 -> 2' in the lobby's exit box, the square, the road, 'IN THE EXIT BOX: van called' + stage 3 GO+154 s, 'the vehicle's state is 3 (its timer 7.7 s)', 'record 0 (you): aboard' GO+162 s, 'status6' = ESCAPED with $300,000 GO+177 s, score page, PASS, no fault. THE CREW: when he boarded, four bots were on the road 60 .. 100 m behind him (z -4000 .. -2000 against the van's z 8700) and two still stood at the lobby's square ('board: record 2 (stage 2) at (5252, 160, -5966): held for 40 s with $285000 ...: heist stage set to 3', record 5 the same at (3443, 160, -6178)); two died in the street fight and the other four were killed as the van left ('lost 252.0 ... ONE STEP'). So the map is whole for a human; the crew cannot keep up with one who sprints (44 s from the join to the van) - track J's FollowOut. The owner's tree w_tabX was put back after the run. QUEUED: H1o (hud_test15: the stock player list draws the hook's strings), then G2_DM09 = the gates' second form with an IDLE player (against G1), then w_tabX again.
LIVE 2026-10-11 11:17-11:22, run J0_DM09_join_oldchain = THE CONTROL (the owner's own Retomoto build z_route4/retomoto_tab_fix, same walk, same hook test_pt5): two bots dead in the tower before the join (GO+97, +100 s), 'crewjoin: 5 moved', all five 'heist stage 1 -> 2' 1.6 .. 2.4 s later, they SPRINT the street (x -1450 within 40 s) and ALL FIVE ARE DEAD 40 .. 49 s after the join; nobody is left. Against it J1 (the gates, second form): seven of seven at the join, six alive 78 s after it and in the street fight at x 600 .. 3400. So the gates do not break the join (every bot's street step started within 3 s in both runs) and the crew is better off before AND after it; whether they get to the van is the next run: B1_DM09_board_gates (scratchpad runs/B1_DM09_board_gates.ini, made by `kl_playtest.py script <w_tabU> DM09 --until board --rig2`: tower, join, street, the van, aboard; about 614 s), queued behind H1n (hud_test14 for kl-merge-3e); the owner's tree w_tabX is reinstalled after it.
INSTALLED FOR THE OWNER 2026-10-11 11:20 (game closed): tree <work>/build/w_tabX = the same five builds as w_tabW (DM01 z_route3/M01, DM02 z_loot3/M02, DM03 z_cover3/M03, DM06 z_route/M06, DM09 z_route4/retomoto_tab_fix with the approved talk delays), BUILT AGAIN because w_tabW no longer installs ('the tree does not match its manifest: differs: Maps/DM09/KLTalk.ini' - the talk file had been put right by hand inside the tree; the build folder's backup copy now lies beside it as retomoto_tab_fix.KLTalk.ini.delays-9.29-0.60). NEVER edit a file inside a tree: fix the build folder and build the tree again. Between 09:20 and 11:20 the game folder held the test trees w_tabT / w_tabU (a chain's 'w_tabW back' step failed twice without stopping). Hook SHIP ship_vis2, the ini's keys checked (Risk=2, CopToCrew=0.05, Escort=1, BoardAll=1, Random=1); the test folder Maps/T01 is still there.
LIVE 2026-10-11 10:56-11:15 (hook test_pt5 = the newest): (1) THE RIG FIX HOLDS AND THE SCRIPTED PLAYER DOES A WHOLE HEIST ON HOT COFFEE AND THE PARK: PB_DM01_board_hp - 'scene ...F01_Main.gms is loaded', stage 1 GO+30 s, the cash register = $100,000, stage 2, exit box + stage 3 GO+67 s, 'the vehicle's state is 3 (its timer 8.0 s) after 3406 ms', aboard GO+75 s, escaped GO+91 s; PB_DM06_board_hp - four loot stops, exit box GO+74 s, in the helicopter's boarding box, aboard GO+87 s, escaped GO+98 s. The escort boards with him both times. AND BOTH TIMES FIVE AI HEISTERS STILL AT THE LOOT ARE KILLED AS THE VEHICLE LEAVES ('lost 252.0 (0.0 of 252.0) ... ONE STEP', one every 1-2 s from 9 s after he boarded) - three maps of three: the rule track J is reading. (2) THE RETOMOTO JOIN WORKS WITH BOTS AND WITH THE GATES, run J1_DM09_join (tree w_tabU, DM09 = z_rooms/retomoto_full second form, G's script z_rooms/live/J1_DM09_join.ini, position log on): the scripted player walks the tower with $300,000 and is in the jump box GO+110 s; 'join: player 0 entered box 9 ...', 'crewjoin: ... the AI heisters in play are moved first (EARLY)', seven lines 'crewjoin: bot N (actor ...) at (the third floor's holds) -> place k', 'crewjoin: 7 moved', 'join: player 0 is at (6272, 570, -6305) 500 ms after the request'; ALL SEVEN take 'heist stage 1 -> 2' 1.4 .. 2.7 s later (their street step starts: no late gate wait took it away) and walk out - lobby (5940, 560, -5963) -> the square -> the street at x 600 .. 3400, y 20 within 25 .. 70 s; one dies on the street, six alive and in the street fight when the script ends 78 s after the join (none at stage 3 yet: that comes at the van). The first run ever with bots through the join. The control J0 (old chain) did not run (the failed install) - running now. (3) HUD, H1m (hud_test13, texts borrowed from the hidden player list): 'player list +0xed0 = ... (vtable 00bacecc) is not a ZCHAROBJ: no text is made' - told kl-merge-3e.
11:00 2026-10-11 - THE SECOND WAVE IS IN AND COMMITTED (wf_dd99422f-502, each track worked -> reviewed -> fixed): 5cdabba tools/kl_playtest.py + re/playtest.md (second version: every goto driven through a model of the rig's steering, real stops where it would circle, `judge <ini> <log>`, PlayerHealth=10 in its 'bullet-proof' default; scripts regenerated in <work>/research/playtest/rig2, the second version's have not run), 67a00c5 kl_fa_bots_rt / kl_fa_bots_dyn + re/retomoto_bots_rooms.md (the gates; SECOND FORM builds <work>/build/z_rooms/retomoto_full 0bf668aa and _r: the reception's hold moved east, the second floor's hold at the foot of the first flight = the round's riskiest guess, no dyn hold or timer behind a gate; the FIRST form of run G1 is kept in z_rooms/round1), 9c8077d klclimb.c third version. QUEUED IN THE GAME (scratchpad now/chain_d.py, hook test_pt5): J0_DM09_join_oldchain (tree w_tabW) and J1_DM09_join (tree <work>/build/w_tabU = w_tabW with DM09 = the second form) = the scripted player walks the tower into the jump box and the bots are read for 83 s after it (z_rooms/live/README.txt: good = every bot alive at the end has stage 3 or is aboard); each with the TEST-ONLY position-log KLJoin.ini, put back after the run; THE OWNER'S TREE w_tabW IS REINSTALLED AT THE END OF THE CHAIN (until then the game folder holds w_tabT, then w_tabW / w_tabU in turn). HUD, run H1l for kl-merge-3e: 'TOTAL $0' IS DRAWN top right when the string is put into the CLOCK's own text object inside its render slot (research/shots/H1l_stock_86s.png) - so SetText, font and draw path are fine and the 24 texts the hook CREATES mid-level are what does not draw (their chunk handle never changes); suggested to kl-merge-3e: reuse the hidden ZFAPlayerListDisplay's own level-made row texts.
10:50 2026-10-11 - (1) FED WITH THE REVIEW'S FIXES, run FD3_DM03_die (hook test_climb1): 'balance: your health object ... a POLICEMAN: under the same dial as the hero (FedMirror=1)', 'your health set (a policeman): maximum 27.5 (the game gave 550.0)' (the test's PlayerHealth 0.05; the owner's 0.73 gives 401.5), the mirror line in the tick of the respawn, five of seven heisters alive 145 s later, PASS. So klbalance.c as committed (2b2b005) has run; a second round after a fed round (review S3) has not. (2) THE RIG MISSED FAST LOADS: PB_DM01_board_hp / PB_DM06_board_hp never walked - without the scene-load wrapper 'waitload' only saw a load as a pause of over 3 s between keyboard polls, and the maps in slots F01 / F04 load in 2 s (that is the 'no such scene load' FAIL of every F01 / F04 run since last night). Fixed 431bbc9 (the scene name is looked at four times a second); hooks <work>/build/klhook/test_pt5 b9584122 / ship_pt5 aa74118e, built from the COMMITTED sources in a scratch copy (git archive HEAD klhook: agents are editing klescort.c / klclimb.c in the shared tree) = the newest hook: rig patch + waitload fix + FedMirror + klclimb wired (off). Both walks are queued again with it. (3) RUNNING OFFLINE: wf_af0007cd-65d (F3: the climb's crash), wf_ace40f35-749 (J: what kills the AI heisters left behind + key [Bots] FollowOut in klescort.c, 'the crew follows you out'; task scratchpad wf/J_follow_out.md), wf_dd99422f-502's fix rounds for G (the gates and the join) and H (goto radii), kl-merge-9b on the close-combat damage, kl-merge-3e on the HUD (runs H1k: a string put into the clock's own text from the tick never shows - the clock rewrites it every frame; H1l from inside the render slot is in the game).
LIVE 2026-10-11 10:13-10:16, run PB_DM03_board_hp - A WHOLE HEIST BY THE SCRIPTED PLAYER (the bank on the test tree, hook test_climb1, H's script rig2/PT_DM03_board_r2.ini + [Balance] PlayerHealth=10 + [Bots] Log=2; scratchpad runs/PB_DM03_board_hp.ini): GO 10:13:43; stage 1 in the entry box GO+18 s, E at two stacks = $550,000, stage 2 in the exit box GO+78 s, 'IN THE EXIT BOX' and stage 3 GO+94 s, at the vehicle GO+103 s, 'script 132: the vehicle's state is 3 (its timer 5.8 s) after 0 ms' (waitvan), a step to the rear doors and E: 'record 0 (you): aboard' GO+104 s, 'record 0 (you): status6' = ESCAPED with $550,000 at GO+118 s, score page, PASS. Two of 76 gotos not reached (both recovered). THE ESCORT WITH A MOVING HUMAN: 12 re-points ('you are 26.7 m away', '44.5 m away' - a sprinting human outruns it), 'escort: record 1 released (the vehicle waits, state 3): it is at stage 3, its own board tactic takes it aboard', aboard 3 s after the human, escaped; one more bot aboard. WHAT THE RUN SHOWS ABOUT THE CREW: (1) bot 7 'lost 201.0 ... ONE STEP - DOWN' at (-449, 570, -5738) = the stairs to the control room where the player lost 151 + 151 + 30 in runs K1 / K2 / K2b: one guard there kills by close combat; (2) the four bots still inside the bank each 'lost 252.0 (0.0 of 252.0) ONE STEP' 8..13 s after the human boarded, while the vehicle drove off: THE GAME KILLS THE AI HEISTERS LEFT BEHIND WHEN THE VEHICLE LEAVES WITH THE HUMAN (not read in the exe yet; with an idle human the vehicle comes back and nobody is killed) - a human who is through in two minutes loses his crew that way, which may be part of the owner's 'dropping like flies'. QUEUED (scratchpad now/chain_c.py): the same on Hot Coffee and the park, then the fed again with test_climb1 (the fed's health under the dial).
LIVE 2026-10-11 10:00-10:02, run K2c_DM03_wall_hp - THE CLIMB STARTED IN THE GAME AND CRASHED 0.24 s LATER (hook test_climb1, <work>/build/z_climb/M03, H's wall script with [Balance] PlayerHealth=10). THE SCRIPTED PLAYER WALKS THE WHOLE BANK: 48 of 50 gotos reached (the first one again not - the ~10 s after state 0x19), stage 0 -> 1 in the entry box, E held 4 s at two money stacks = '0 you in-play g2 $550000', stage 1 -> 2 in the exit box, the yard, the wall. Then: 'climb: at the foot of edge 2: node (-2074, 201, -673), +0x460 (-2077, 220, -751), proxy (-2074, 201, -673), 48 from the face, speed 483, facing 1.00; the top is 202.5 over his feet = /Movement/Climb/Up/High, id 2505; 0 full-body channel(s)', 'climb: edge 2: started /Movement/Climb/Up/High (slot 2505) ... action 0150d1c4, clip 78168c98 of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned to (-2074, 201, -672) in 6 frames', 'collision off (count 0 -> 1)' - so the merged clip is found, the mini animation starts, the sign of 'facing' and the node / proxy reads are right - and 0.24 s later CRASH c0000005 at kl2+0x7e400 reading 0x60 (a member function on a null object; callers 006370f4 00446200 00818623 008b76f3 007c6ca2 0060c3c0 008b6917 0050af65 = inside the animation update, 0074f043 = ZPlayer's frame). Dumps + log: <work>/research/crash_1011_climb. RUNNING: workflow wf_af0007cd-65d (track F3: cause from the dump, fix, adversarial review, fix round; task scratchpad wf/F3_climb_crash.md; level builds to <work>/build/z_climb3). klclimb.c stays OFF everywhere (the owner's hook does not have it).
CLOSE COMBAT IS NOT SCALED BY THE DIAL (run K2b_DM03_wall_log, [Balance] Log=2): bullets cost the scripted player 1.0 .. 4.3 a hit at CopToYou 0.02, then on the stairs to the bank's control room, about (-392, 440, -5679): 'you lost 151.2', 0.19 s later 'you lost 151.2', 'you lost 30.2', dead - the death panel says 'Killed by: The police' (picture K2b_DM03_wall_log_98s.png); the same second in K1 / K2. With the owner's 401 health one guard at arm's length takes 332 in 0.3 s. Very likely also the bots' 'ONE STEP' kills (236 / 246 of 252). kl-merge-9b reads the routine (re/melee_damage.md to come, with a [Balance] key as a patch for klbalance.c; its first lead: 151.2 = 126 x 1.2, a fixed damage times a campaign-difficulty factor).
LIVE 2026-10-11 09:31-09:38, run G1_DM09 - THE SEVEN GATES WORK (<work>/build/z_rooms/retomoto_full through the test tree w_tabT, TEST test_climb1, idle player, Escort=1, BoardAll=1, [Bots] Log=2): loads (49 TriggerActorsDead nodes, a first in a build of ours), clean, 6.2 min. The escort's route place = the gates' clock: door GO+60 s, reception +96, atrium +105 (9 s: that fight was won), gallery +140, second floor +174, first floor +208, lobby +242, the car +276 - every other gate opened by its 30 s fall-back. The fighting follows the holds (losses by half minute: third floor to GO+180, second floor +180..210, first floor +210..300, the lobby +300..330). DEATHS: none before GO+175 s (rt_full7: six by GO+79..122 s); one at the gallery (GO+175), one on the second floor (+189), two on the first floor (+249, +295), two at the lifts (+312, +323, one of them 76 from the car's own places); the escort lives. So with nobody helping they now get DOWN the tower and die over 5.5 minutes instead of at the reception. NOT ON THE OWNER'S TAB YET: the review's D1 (a bot WAITING at a gate when the human takes the join) wants a joined run first - H's PT_DM09_join after its fix.
THE CLIMB IS NOT TESTED YET: K1_DM03_wall_dry and K2_DM03_wall (hook test_climb1, <work>/build/z_climb/M03, H's wall script) both ended 26 / 30 s after GO - the scripted player gets through the bank's hall and down the stairs, sticks at (-294, 440, -5751) (goto 61, a door?) and is DEAD 2 s later although police -> you is 0.02 and his health 401 (not bullets on that scale: close combat or a blast - K2b with [Balance] Log=2 and pictures every 2 s is queued). What the two runs do show: klclimb.c wired does no harm ('climb: 2 edge(s) from ...KLJoin.ini', the node / +0x460 / proxy places agree within 14 in height while he runs, 'near none of the 2 edge(s)'), z_climb/M03's merged .ANM loads and plays a round.
09:25 2026-10-11 - TEST TREE INSTALLED: <work>/build/w_tabT (= w_tabW with DM03 = <work>/build/z_climb/M03 = the bank with Dead Men's climb clips and two [Climb] edges, NO extra cover boxes, and DM09 = <work>/build/z_rooms/retomoto_full = seven gates). PUT w_tabW BACK (python tools/kl_expansion.py install "<work>/build/w_tabW/KLExpansion" --replace --no-stream --no-hook) unless the runs say these are better; the owner's hook is still SHIP ship_vis2. RUNNING (scratchpad now/chain_b.py, hook TEST test_climb1 55ab30e5 = everything below): K1_DM03_wall_dry ([Climb] Dry=1), K2_DM03_wall (the climb), G1_DM09 (the gates, 370 s, idle player).
FED RETEST, run PT_DM03_die_f2 09:09-09:13 (hook test_fed1 = FedMirror without the review's fixes; the owner's Ramp, [Bots] Log=2): dead GO+20 s, 'fed: YOU ARE A FED ... at (-4570, 300, -3349)' and in the same tick 'balance: you are POLICE now: ... the three pairs are written exchanged (54 value(s))'; 170 s later FIVE OF SEVEN heisters are alive at stage 3 with their loot (81 losses of median 13.0 = 857 health; before the fix 1,764 health in 47 s). Committed 2b2b005 with the review's fixes (re/balance_fedmirror_review.md ACCEPT WITH FIXES: an unset pair is left to the game, THE FED'S HEALTH IS UNDER THE SAME DIAL (401.5, 8 s / 8 s) - in that run it still read 'a POLICEMAN: left alone' 550 -, one record per health object, no doubled log line): builds test_fed2 / ship_fed2, and test_climb1 / ship_climb1 carry them; NOT RUN. Also committed: 1f8b617 the rig patch (ran live), 9c8077d klclimb.c WIRED, off by default (third version after its second review; re/climb_review2.md). REVIEWS IN: track G ACCEPT WITH FIXES (re/retomoto_bots_rooms_review.md: D1 = a gate can leave a bot WAITING in the tower when the human takes the join, and the tool's guard against that no longer looks; 'neither build on the owner's tab before a JOINED run'), track H ACCEPT WITH FIXES (re/playtest_review.md: one MUST - goto radii below the rig's turning circle, two way points cannot be reached, one of them on Retomoto's stairs: fix running before PT_DM09_join is run). HUD for kl-merge-3e: H1f (neither test draw shows), H1g (the Draw runs in the game and builds the object's matrix - '+0x60 3bc3b53f', 0 draws refused - and the texts are still invisible; guesses sent: a batch that is closed by the stock call, the font / glyph set at +0x24, the layer byte).
LIVE 2026-10-11 08:56-08:59, run PT_DM03_die_r2 - COME BACK AS A FED WORKS, AND THE SCRIPTED PLAYER WALKS (the bank as installed, TEST <work>/build/klhook/test_pt1 = the newest hook + the rig patch; script <work>/research/playtest/rig2/PT_DM03_die_r2.ini: [Fed] Enable=1 Player=1, [Balance] Ramp=0 CopToYou=20 PlayerHealth=0.05): 'players: the local one is #13 ... (the game's own pointer, slot 0)', 'the session state is 0x19 after 21437 ms', five gotos reached (the first one stuck for 9.5 s: THE PLAYER CANNOT MOVE FOR ~10 s AFTER STATE 0x19 on the bank - the scripts need a wait there), 'record 0 (you): heist stage 0 -> 1' in the bank's entry box, the escort re-pointed after a MOVING player ('you are 28.1 m away at (-84, 800, -8073)'). GO+19 s, in the hall: 'fed: you: status 0 -> 1 (dead, waiting to return as police; countdown 5.0 s ...)', 'escort: record 6 released (you are out of play)'; 5.0 s later 'fed: YOU ARE A FED: local player object 8 (475f5020, type 3, police byte 1) at (-4414, 300, -3486); ... 7 of 8 police bodies still free', the rig's pointer follows the new body. PICTURES research/shots/PT_DM03_die_r2_110s.png / _130s.png: a POLICE OFFICER (helmet, radio) in third person, the HUD's name / score / round in police blue, the AMMO PANEL SHOWS A PISTOL (150) AND A RIFLE (300) = the fed is armed. Then 'fed: nobody is left to hunt: the round clock 289.6 s -> 3.0 s', state 0x1f, the score page, PASS, no fault. So F1 and F2 of re/fed.md hold; F3 (die as a fed), F4 (a second round), the AI feds (x_fed2 builds) and whether the fed can leave the room he appears in (he stood before a double door; the scripted gotos could not move him far) are NOT run.
THE FED'S BALANCE FAULT, SEEN IN THAT RUN: all seven AI heisters were dead 15 .. 47 s after the human became police (none before). Cause READ again in kl2 (0x591bbe, 0x8b80a0, 0x7c1bf0): for a police player each of the three damage routines takes the OTHER float of its pair - the table is 'your enemies -> your side' etc., and the hook's keys are named for a criminal - so the owner's CopToCrew=0.05 stopped protecting the heisters and cut THEIR fire on the police to 0.05 instead. FIX WRITTEN, NOT RUN, NOT COMMITTED: klbalance.c key [Balance] FedMirror (default 1): while the local player is police the three pairs are written exchanged, every key keeps the meaning of its name (builds <work>/build/klhook/test_fed1 5ff1d18c / ship_fed1 9ae51cfc); adversarial review running (wf_d84858b8-21f, re/balance_fedmirror_review.md), live retest PT_DM03_die_f2 queued behind H1f (hud_test7 for kl-merge-3e). F1_T01 / F1b_T01 on the Subway copy: the idle player was never shot, even at 27 health (on stock Subway he dies in 2 runs of 5): an idle player is no test for the fed.
08:45 2026-10-11 - (1) RETOMOTO'S TALK TIMING WAS WRONG ON THE TAB SINCE 03:50 AND IS PUT BACK (found by track G): rt_full7 and everything made from it (z_route7, z_route4/retomoto_tab_fix, DM09 of w_tabC / w_tabN / w_tabW) carried kl_fa_talk's own delays (countdown 9.29, balcony 0.60 = Kane's countdown begins 1.3 s AFTER the blast) instead of the two the owner approved (countdown Delay=0.30, balcony Delay=11.50: 'the bang goes ON Kane's NOW!'). <DD>/KLExpansion/Maps/DM09/KLTalk.ini, the tree w_tabW's and z_route4/retomoto_tab_fix's are now rt_full6's file (sha1 6c78c079; the wrong one kept beside as KLTalk.ini.delays-9.29-0.60). RULE: after any Retomoto chain, compare KLTalk.ini with <work>/build/rt_full6/retomoto_full's. (2) FED, run F1_T01 (stock Subway + wardrobe in T01, [Fed] Player=1, the owner's balance): 'fed: this level is not the stock one ... Player / Bots may act', 'fed: police bodies: ... 7 of 8 free', 'fed: ARMED: your death will not end the round' at GO, switch 1 held - and the idle player LIVED (401 health under Risk=2; on stock Subway he dies about GO+82 s), the seven escaped at GO+220 s, switch back to 0: nothing to respawn. F1b with a fragile player ([Balance] Ramp=0 CopToYou=20 CrewToYou=20 PlayerHealth=0.05) is queued behind H1e (hud_test6 for kl-merge-3e). (3) TRACKS: G's builds <work>/build/z_rooms/retomoto_full (seven gates of TriggerActorsDead on the tower's way out; the wait fires by itself after 30 s) and retomoto_full_r pass every check (re/retomoto_bots_rooms.md), test tree <work>/build/w_tabG (= w_tabW with DM09 = z_rooms/retomoto_full) is built, not installed; H's scripted walking player is written (tools/kl_playtest.py, re/playtest.md, eight scripts in <work>/research/playtest + rig2 twins) and its rig patch is applied to klhook/klauto.c (waitstate, waitvan, the game's own local-player pointer; TEST only; hooks <work>/build/klhook/test_pt1 884c0c6c / ship_pt1 bf277c0a, not run); F2 (klclimb.c) second review: ACCEPT WITH FIXES, fix round running. (4) `kl_expansion.py build --help` STARTED A DEFAULT BUILD (four maps into <work>/build/expansion/_stage before it was stopped; nothing installed, nothing else written): --help now prints the usage (62a8828).
LIVE 2026-10-11 07:44-08:24, SERIES I = EVERY MAP ONCE AS INSTALLED (tree w_tabW, TEST test_vis2 = the sibling of the installed SHIP hook, the owner's settings: Escort=1, BoardAll=1, CopToCrew 0.05, Risk 2; idle player; [Bots] Log=2, [Vis] Log=1): FIVE CLEAN RUNS, no fault, no assert. I1 Hot Coffee: six of seven escape (one dead, one BoardAll raise 'record 5 (stage 2) ... held for 31 s'), the escort is released at the van and boards. I2 Late Night Opening: nobody dies, six escape, the seventh is the escort (released, at stage 3 when the 5.5 min were over). I3 Withdrawal: nobody dies, five escape, two at stage 3 on their way when the run ended; four BoardAll raises at the wall (stage 1, held 15-19 s). I4 the park: SEVEN OF SEVEN. I5 Retomoto: six die GO+79..99 s at the reception fight, the escort lives (as before: track G). No one-step kill in any of the five. The vision grid of all five maps is logged and record 0xff never holds 'no cell'. (Slot F01 / F04 runs still end 'no such scene load' in the test rig: the round is whole.)
THE MONITOR IS OFF SINCE ~08:09 (the owner has left): Windows offers only 50 / 59 / 60 Hz modes, the game cannot get its 2560x1440 @ 240 Hz and runs 640x480 for the run - pictures are 640x480 (4:3) from I4 on. The game's settings (HKCU\Software\IO Interactive\Kane & Lynch 2: Dog Days\Graphics: 2560 x 1440, 240, FullscreenID 131) are intact: DO NOT WRITE THEM. H1d_stock for kl-merge-3e (hud_test5, the texts drawn from the timer element's slot): no fault; the part stops after 'timer element ... now renders through the private vtable' - no texts made, stock block not hidden; told kl-merge-3e with the 640x480 caveat.
TEST-ONLY FOLDER <DD>/KLExpansion/Maps/T01 (= <work>/build/pd2/pd2_F01, stock Subway + wardrobe: a level that is NOT stock, where an idle player dies ~80 s after GO) for the first live runs of COME BACK AS A FED: scratchpad now/series.py F (live.py --redirect "F01=T01", [Fed] Enable=1 Log=2 Player=1, Escort / BoardAll off). Not on the owner's page; delete when the fed runs are done. Offline: <work>/build/x_fed2/M03 (fed squads on the installed bank, kl_fa_fed check PASS, impact 0) and x_fed2/M02 (on z_loot3/M02: built, impact 0, dyn check PASS; its own diff says '3 unexpected differences' = the clerks' money controllers the SOURCE build had already lost - a fault of the diff's expectation, not of the build; not corrected).
CAMPAIGN PLACES AS FRAGILE ALLIANCE MAPS - STUDY DONE, NOTHING BUILT TO PLAY (kl-merge-9b, 2026-10-11 08:30; owner: 'the bank
map but the campaign way, the club map, hasta / cuba & probably walk in the park perhaps prison too'; re/campaign_fa.md = the
summary, section 0 for the owner; six re/campaign_fa_<bank|club|havana|park|prison|tooling>.md, each written by one agent,
corrected by a second, then a critic and four gap closers; ALL OFFLINE, nothing ran in the game). All five can be made.
ORDER: bank (M03_A alone, ready-to-author, 0.5 of a Retomoto; chunk table 65,640 WITH its 22 squads + wardrobe; six door sets
in series) -> club (M05_A, 0.5; kl_mat stops on ONE TILU=MIRRORED string; no crowd, van on a 30 x 9 m slab) -> prison (M08_A
cell block B side, 0.7-1.0; 79,005 entries = over the table: needs `kl_chars.py compact` -> finished 65,509 with 8 masks,
70,925 = OVER with all four Payday 2 plates, two fit) -> Havana (M11_B only, ~1.0; 74,454 -> finished 60,902 / 66,318; .prm
84 MB; four geometry switches) -> park (M06_A, 0.45; the same garden, optional). BLOCKED: both Havana chapters in one map
(111,853 entries, 83,464 live), bank + M03_B (79,408; .HVK 6.9 MB), the prison's whole campaign route (three mesh pieces joined
by climbs). Cuba = M11_A / M11_B only (M12-M14 are Venezuela). BEFORE MAP 1: 'FFCoverList' into kl_maps.PASSIVE (the campaign
pre-pass drops the only cover list of M03_A / M06_A), author= as a module in kl_graft / kl_maps (kl_fa_author is imported by
name), a van plan from way points, the collision route test as a tool. DOORS: every route needs doors open; the build-time
fall-back (leaves sunk + collision cut by kl_escape.place_entities / cut_collision) is BUILT and walks offline for all four
(G:/kl_scratch/cfa_fill1/build_open.py). TWO LIVE PROOFS OWED: (1) a compacted level has NEVER loaded - test pair = fake-fix of
<work>/build/x_chunks/retomoto_wardrobe and ..._compact (both carry the 0x686a66 FakeTargets as they lie; commands in
re/campaign_fa.md 3.3 step 2); (2) the bare bank with its dock door sent 'Activate'. Page 2 of the menu has ONE entry left (F07):
a second new map needs page 3 (kl_expansion.PAGE is hard-coded 2). OWNER DECIDES: order, club without crowd, park or not, the two
test runs, page 3, a larger PC_Def.str per map (bank +56 MB; all five ~2.0 GB, never tried past 2 GB).
INSTALLED FOR THE OWNER 2026-10-11 07:35 (game closed; owner 07:00: 'pc is all yours ... keep going all night' = scripted runs ON until he says otherwise): hook SHIP <work>/build/klhook/ship_vis2 (88d8b1ec = ship_hop1 + BoardAll + [Balance] CrewOffStage + klhud.c (off) + klvis.c (off); the previous one is kept in <work>/build/klhook/owner_prev_1011_0735), his KLHook.ini + `[Bots] BoardAll=1` (inside the expansion block; kl_expansion's block carries the key since c9543aa). NEW FOR HIM: a held AI heister is sent to the waiting vehicle; under his Risk=2 a heister at another heist stage than his now hits police at 1.0 (stock 0.5..0.1). Tree w_tabW unchanged. Start-up check SHIPV2 (the SHIP hook itself, nobody at the keys): every part reports ('board: on; BoardAll=1 Still=15 s Stage=1 Order=0', 'crew off your stage x 1.00'), menu film reached, no fault in 221 s. RUNNING 07:50: series I (now/series.py I = each of the five maps once as installed, TEST sibling test_vis2, [Bots] Log=2, [Vis] Log=1, idle player).
FOR kl-merge-3e (HUD / UI), live 07:17-07:42: F2_DM03 = the bank with hud_font2's baked fonts: PASS, picture F2_DM03_130s.png shows name + skulls, 'Total score: $0', 'Round: 1', a bot tag, the timer and the ammo panel with whole glyphs. H1b_stock / H1c_stock (hud_test3 / hud_test4 on stock Subway, [HUD] Enable=1 Log=2): the part finds the display by vtable scan, makes 24 texts, hides the stock block (seen in the pictures) and writes the strings, and from H1c: the private render slot is reached, 1 call in 3 takes the HUD branch and each does 12 text draws with mesh non-null, alpha ff, layer 13 - and NOTHING of it is on the frame (H1c_stock_84s.png = GO+31 s). Cause open, with kl-merge-3e. The line 'hud: the tick is not on the game's thread' at start is a false alarm (printed before the main loop's tick exists).
LIVE 2026-10-11 07:09-07:15, run W1_DM02 - LATE NIGHT OPENING WITH BOTH STORES AND THE LOOT WINDOW FIX WORKS (build <work>/build/z_loot3/M02, TEST test_vis2, NO BoardAll, idle player, Escort=1, CopToCrew 0.05): loads, clean; all bots take stage 1 GO+45..79 s, loot both stores (the crew carries about 2,120,000), stage 2 / 3 GO+144..212 s by themselves, the van comes five times, SEVEN BOARDINGS, ALL SEVEN ESCAPE (the escort too), NOBODY DIES, nobody is held; the round is over GO+348 s. It is on the tab (tree w_tabW). The cost stands: the three clerks' 215,000 is out for everybody and the jewel store's glass bursts by the bots' relays. Hot Coffee and Withdrawal keep their tab builds (z_route3/M01, z_cover3/M03: clean live, they fail only the new civilian rule; z_loot3/M03 has no extra cover). Late Night Opening's grid logged too (no 'no cell'). Under way: H1b_stock (hud_test3) and F2_DM03 (hud_font2) for kl-merge-3e.
LIVE 2026-10-11 06:49-07:06 - THE FAKETARGET WRITE IS SEEN AND THE FIX HOLDS (hook TEST test_vis2 = the newest, klvis.c [Vis] Log=1; re/crash_686a66.md 'LIVE'): V2a_DM09 on rt_full7's archive: 'vis: record 0xff behind the grid holds 'no cell' ff100110 + (-3216.6, -60040.0, 3419.3)' at the second the round starts; V2b_DM09 on <work>/build/z_route4/retomoto_tab_fix: 'record 0xff has never held 'no cell''; V1_DM09 on the same build: loads, four minutes, clean. The game's grid on Retomoto = the tool's 'all' box bit for bit (`kl_fa_bots_dyn.py grid`). INSTALLED TREE NOW = <work>/build/w_tabW: DM01 z_route3/M01, DM02 z_loot3/M02 (BOTH stores + the loot window; run W1_DM02 under way), DM03 z_cover3/M03, DM06 z_route/M06, DM09 z_route4/retomoto_tab_fix. kl-merge-0e has fixed the source (202a29b, kl_fa_street.place_escape takes the FakeTarget off a parked van; compiled only). TRACK F IN (ce223cd; re/climb.md, re/climb_review.md): no climb by level data alone; Dead Men's three climb clips merged into the level's .ANM (tools/kl_fa_climb.py, <work>/build/z_climb/M03) + a hook part klhook/klclimb.c that is NOT WIRED and must not run as written (proxy sync missing). SECOND WAVE RUNNING, wf_dd99422f-502: G = Retomoto bots fight each room first (kl_fa_bots_rt; builds <work>/build/z_rooms), H = a scripted WALKING player for the test runs (tools/kl_playtest.py from the rig's `goto` + the bots' own route places), F2 = klclimb.c fixed after its review. Task files: scratchpad wf/G_reception_hold.md, H_playtest.md.
06:50 2026-10-11 - THE THREE TRACKS ARE IN (workflow wf_e831481a-b41, each worked -> adversarially reviewed -> fixed; commits 0bee9d3, 772e276, baa0669):
- B, THE 0x686a66 CRASH IS NOT THE ROUTE FORKS (re/crash_686a66.md): ZFakeTarget's frame update (kl2 0x560630) registers with ZCheckVisible and calls 0x7143f0 with the index unchecked; a target OUTSIDE THE VISION GRID gets 0xff, and record 0xff of the table of 200 lies 0x5a8 bytes behind the object: 16 bytes of the heap written EVERY FRAME ('no cell' ff100110 + the target's place). The dump of C_DM09 holds exactly that with the place of the FakeTarget on Retomoto's parked van 02 (y -60040). EVERY RETOMOTO BUILD SINCE play2 HAS TWO SUCH TARGETS (kl_fa_street.place_escape parks vans 02 / 03 below the map) - rt_full7 and z_route7 too; runs of them prove nothing about it. kl_fa_bots_dyn.py: a check rule, `fake-fix <build> <out>` (only the failing controllers off), `grid`; FORK_GAP's default is 0 again. Builds <work>/build/z_route4/retomoto_tab_fix (= rt_full7 minus the two controllers) and retomoto_full_r2 (with routes). SOURCE FIX OWED in tools/kl_fa_street.py place_escape (kl-merge-0e's file; told). klhook/klvis.c ([Vis] Log=1, reads only; builds ship_vis1 e7d789d1 / test_vis1 43a41520 = the newest hook) logs the grid and record 0xff: runs V0 (z_route7, to SEE the write) and V1 (retomoto_tab_fix) under way.
- A, THE LOOT WINDOW (re/bots_loot.md): candidates = the five nearest untaken money objects within 800 / 400 (kl2 0x8b94d0); a shut container is a candidate all round and inactive until 'Open'. kl_fa_bots 'window' (on in RECIPE): the squads' relays open EVERY case a bot comes near; a civilian's money controller + trigger are taken off his group (NOBODY gets that money, the human included: Late Night's three clerks 215,000, Hot Coffee's waitress 40,000, the bank's two 30,000); check() FAILs a place inside the window of money the bot cannot take - so the tab's M01 / M02 / M03 builds now FAIL kl_fa_bots_dyn check ON PURPOSE. Builds <work>/build/z_loot3/M01 M02 M03 M06 (M02 with BOTH stops again), not loaded. PLAN: M02 first (it needs it), M01 / M03 only after M02 has shown the edit loads (the tab's ran clean live). Why the watch shop's clerk never paid is not established.
- C, THE CONVERTER (re/convert_audit.md): FAULTS corrected in kl_convert - ZTriggerBox (Dog Days' new bool is field 8), ZSquadScript (8 of 12 event lists went to another event), ZFFActor's last bool, two enum names; CLEAN - grenades / items, vehicles that blow up, the soldier block. On the five maps 33 list entries move, none to a target nothing else names: it can ride on each map's next build (`kl_map_ai.py pairfix <build> [<out>]` patches a finished one). With it three one-civilian squads on Hot Coffee get a live 'attacked' list (a hit starts FrontMall_01's flank): left as Dead Men wired it. NOTE: .claude/workflows/retomoto-level-design.js line 1 reads 'okaexport const meta' (a stray keystroke; uncommitted, left for the owner).
LIVE 2026-10-11 06:26-06:32, run H1_stock for kl-merge-3e (hook <work>/build/klhook/hud_test, stock Subway through the Arcade page, [HUD] Enable=1 Log=2): clean exit, no fault, but THE NEW HUD NEVER APPEARED - three hud lines only ('hud: on ...', 'the tick is not on the game's thread ... the HUD does nothing' 0.15 s after start, 'osd 00000054 is over (the scene changed): texts dropped' during the level load), none after GO; pictures research/shots/H1_stock_*.png show the stock block unchanged. Told kl-merge-3e (look at: does the part latch itself off at the first fallback tick; the 0x54 read as an osd). UNDER WAY 06:35-07:35: F1_DM03 (<work>/build/hud_font/DM03's archive copied over the tab's DM03 for the one run, the test tree's put back after it) and R7d..R7i_DM09 (z_route7 six more times) - all with the newest hook test_bal2.
LIVE 2026-10-11 06:09-06:25 (TEST test_board4, BoardAll=1, idle player, Escort=1, tree w_tabN): B1_DM01 Hot Coffee (the gate build z_route3/M01): round runs, six of seven escape, the round is over GO+262 s; BoardAll raises four bots that stood 18-26 s at stage 2 near the van's stop ('record 2 (stage 2) at (3378, 0, 19923): held for 26 s'), they board; the one dead is the escort, released at the van and shot on his way. (The run's script says FAIL 'no such scene load' - the test rig misses the 2 s load of slot F01, as in E3_DM01; the round itself is whole.) B6_DM06 the park: SEVEN OF SEVEN ESCAPE, nobody dies, no raise needed. BoardAll has now run on four maps in five rounds and the hook test_board4 in nine rounds on all five maps: no fault. TRACK E DONE (b6fca85; re/balance.md 10, re/balance_offstage_review.md): key [Balance] CrewOffStage in klbalance.c, Risk 2 / 3 -> 1.0 (Ramp holds the product with CrewToCop at stock's own per level: 1 1 1 0.76 0.48 0.39, levels 7-11 untouched); builds <work>/build/klhook/ship_bal2 8953a2d2 / test_bal2 6d35d3cf = the NEWEST hook (BoardAll rework + klhud off + this), not run yet: every run from here on uses test_bal2 (its first lines are live check O0 of re/balance.md 10.9). WITH THE OWNER'S UNCHANGED Risk=2 THAT HOOK CHANGES HIS GAME: a heister off his stage hits police at 1.0 instead of 0.5 on Arcade levels 1-3 (CrewOffStage=-1 keeps the old).
LIVE 2026-10-11 05:38-06:08 (TEST test_board4, idle player, Escort=1, CopToCrew 0.05, tree w_tabN): R7a / R7b / R7c_DM09 = kl-merge-0e's <work>/build/z_route7/retomoto_full (room first + random routes + the 0.1 s gap timers), [Bots] Log=2, BoardAll off: THREE CLEAN RUNS of 4.5 min, no 0x686a66 (the old rate was 1 in 4: three clean runs prove little, more are queued); six of seven die GO+77..122 s at the reception fight each time, 246..268 bullet hits, no one-step kill. C3_DM03 = <work>/build/z_cover3/M03 (the bank with extra cover on the repaired wall link) with BoardAll=1: clean, NOBODY DIES, ALL SEVEN ESCAPE (the escort too: released when the van waited, aboard), one raise ('record 3 (stage 1) at (957, 240, -6295): held for 15 s'), round over GO+290 s. So far tonight the hook test_board4 ran in seven rounds on three maps without a fault. Under way: B1_DM01, B6_DM06 (BoardAll on Hot Coffee and the park), H1_stock (kl-merge-3e's HUD hook on stock Subway).
LIVE 2026-10-11 05:18-05:35: BoardAll WORKS IN THE GAME (Late Night Opening one-stop build, TEST test_board4, idle player, Escort=1, position log). L12a_DM02 (BoardAllStage=0, nothing written): the 'held' test names exactly the trapped bot - 'board: record 1 (stage 1) at (-1278, 500, 1884): held for 100 s with $210000' at each of three visits (the closed watch cases); that round 3 escape, 3 die, record 1 stands to the end. L12b_DM02 (the write): at the first wait (GO+134 s) 'board: record 2 / 4 / 5 / 6 (stage 1) ... held for 50 / 45 / 49 / 19 s ...: heist stage set to 3', klbot's 'heist stage 1 -> 3' 16 ms later; record 2 is 7.6 m away 2.3 s after the byte, on the ground floor 12 s after it, aboard at the next visit; ALL SIX non-escort bots board and escape (05:31:08 .. 05:33:24), nobody dies, no fault, the escort stays with the idle player. As the third review said, 'held' also takes bots that merely stood at the emptied jewel store (19-50 s without earning): the effect is that once somebody has called the van, everybody who is standing goes. NOT YET IN THE OWNER'S INI (it needs SHIP ship_board4 6de5f96e + [Bots] BoardAll=1): more maps first. TEST TREE INSTALLED DURING THE NEXT RUNS: <work>/build/w_tabN = w_tabC with DM09 = z_route7/retomoto_full (routes + gap timers) and DM03 = z_cover3/M03 - PUT w_tabC BACK afterwards unless the runs say these are better (runs R7a/b/c_DM09, C3_DM03 under way).
LIVE 2026-10-11 05:12-05:17, run T7_DM09 (the tab's Retomoto = rt_full7 'room first', TEST test_board4, [Bots] Log=2 Escort=1, CopToCrew 0.05, idle player): LOADS, 4.5 min, clean exit, no fault - the build on the owner's tab is now a loaded one. The seven take stage 1 at GO+19..35 s and are let past the window about GO+66 s (the escort's route-place lines); NOBODY DIES IN THE BOARDROOM; six die GO+73..114 s, 38..57 m inside at the next fight (030_Reception: Squad_Hallway, Squad_ShootBeforeStorm, and beyond) by 254 bullet hits of 1..21; the escort survives beside the player. ONE-STEP KILL WITH ITS PLACE: 'record 4 lost 16.0 ... at 2029 21000 -867', 0.2 s later 'lost 236.0 (0.0 of 252.0) g1 at 2032 21000 -846 - ONE STEP - DOWN'; no explosion / debris / bomb object within 7 m (scratchpad now/near.py), the nearest enemies are 030_Reception!Squad_Hallway henchmen 9.4 m away: GUESS a close-combat kill (not read). NEW IN THE QUEUE from kl-merge-3e (the HUD session): H1 = <work>/build/klhook/hud_test on stock Subway with [HUD] Enable=1 Log=2, F1 = <work>/build/hud_font/DM03 through the tab's Withdrawal slot; after this session's own runs.
OWNER, 2026-10-11 05:07 (to the first session, kl-merge-31): 'okay other ai is doing the ui want you to start having access to my pc and cracking on, if you really want to do animation help you can load up dead men to see how it is and properly look into it, go ahead and do your testing pc is all yours and keep going all night like previously where if usage runs out you can keep going floor is all yours'. So: SCRIPTED RUNS ARE ON AGAIN, kl-merge-31 holds the game and the game folder (kl-merge-0e agreed: it launches and installs nothing); Dead Men itself may be started to look at animation. The owner was still typing at 05:09: the runner (scratchpad now/live.py <tag> <map> <tree> <seconds> <hook> [--bots ..] [--poslog]) waits until keyboard and mouse have been idle for 2 minutes before each launch. QUEUE: T7 (rt_full7 as installed) -> L12a / L12b (BoardAll, test_board4) -> z_route7/retomoto_full x3+ with Log=2 -> z_cover3/M03 -> the slim sound pairs -> the tracks' builds. RUNNING OFFLINE: wf_e831481a-b41 (tracks A loot trap, B Defend crash, C converter audit), wf_3ae226ba-065 (E: the off-stage damage factor), wf_aec60fcb-d85 (F: the climb - Dog Days' vault, Dead Men's climb and clips, a hook plan; re/climb.md). The 20-minute wake-up job of this session is still scheduled.
HUD MERGE (owner asked 2026-10-11 ~04:30: 'merge the uis ... gritty yet polished ... for FA & arcade going forward'; kl-merge Fable).
Design draft for the owner: https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 (Dead Men crew list + Total/Loot/Rewards box back; Dog Days
clock, escape marker, ammo panel, announcements kept; dark plates, one amber accent, condensed numerals). FACTS: re/hud_data.md (the HUD's
data = 200 picture slots + 8 glyph-atlas fonts; layout is code) and re/hud.md (36 element objects under ZOnScreenDisplay2, texts are
ZCHAROBJ objects, pictures DrawChunk, 1280x720 virtual screen, hide byte elem+0x25, per-frame entry 0x8bf300). DONE OFFLINE, commit 012c18e:
tools/kl_hud.py `fonts` bakes any Windows face into the atlases (check PASS, preview looks right) and `pictures` / `all` (6c8f00d) restyle the
plates (dark, 2 px corners, amber ticks and bars; ASSUMED the code's tint is light); candidate <work>/build/hud_font/DM03 (the tab's bank with
Bahnschrift SemiCondensed + the plates) BUILT, NOT RUN - swap it in only on the owner's word. klhook/klhud.c Version 1 BUILT, NOT RUN (703d007; re/hud_hook.md): [HUD] Enable=0 default; the OSD's vtable slot 55 (Render) wrapped by a private
vtable copy (no .text patch), 24 ZCHAROBJ texts made once per level through the elements' own create path, crew list top-left (names, cash,
own name blue, traitor amber), TOTAL / LOOT / BANKED / ROUND under the stock timer, ZFAPlayerListDisplay hidden (+0x25); plates and localised
labels left out. RUN H1_stock 06:27 (kl-merge-31, hud_test): no fault, NOTHING DRAWN - [0x154da50] is the class's static property pair, not the
instance (it read 0x54). FIXED fc1275f: the OSD is found by its vtable in memory (klu_find_osd); hooks hud_test2 (f2a2c40c) / hud_ship2
(e8344ec6), rerun asked of kl-merge-31 (the game holder) together with F1 = hud_font/DM03 through the tab's Withdrawal slot. Riskiest
assumption left: a ZCHAROBJ made mid-level draws from slot 55 and is freed with the scene.
RUN F1_DM03 ~06:50 (kl-merge-31): THE BAKED FONTS AND PLATES LOAD AND DRAW (new face on HUD and name tags, dark ammo plate, no
fault). Seen and fixed (979e4f9): stair-stepped glyphs (now 4x supersampled), the magazine tick came out as a thin BLUE dotted line
(pixels were B G R A; now R G B A and the tick fills its cell). Candidate <work>/build/hud_font2/DM03 for F2. hud_ship3 (db0e2cd7) =
the SHIP hook with the scan gated to Arcade round states.
RUN H1b_stock 07:18 (hud_test3): no fault; OSD found, vtable wrapped, 24 texts made and SET (names, money following the bots), stock block
HIDDEN (picture: the top-left block is gone) - but NOTHING OF OURS IS DRAWN. Draw's arguments match ZFATimeDisplay::Render exactly (static).
hud_test4 (59426fd1; 6692f0d) counts the render wrapper's calls / branch refusals / draws and logs each text object's +0x30 / +0x14 / +0x3c /
+0x84..87 at Log=2. RUN H1c 07:37: the wrapper IS reached, Draw IS called 12x a HUD frame on good objects (mesh set, alpha ff, layer 13)
and NOTHING reaches the frame -> drawing after the OSD's slot 55 is too late. 00dbaf7: the hook now wraps the TIMER ELEMENT's own Render
(ZFATimeDisplay slot 2) and draws inside the element loop; RUN H1d 08:25 (hud_test5, game at 640x480: the
owner's monitor is asleep): the wrap went in, then my 'FA set shown' test refused the wrapped vtable and nothing was made. FIXED 5a029bb:
hud_test6 (4ef1f885) / hud_ship6 (b66e03f8), run H1e asked of kl-merge-31. (0x558370 only calls 0x8bf300 and returns, so 'after slot 55' was
not a flush problem: whether the element-loop wrap draws is still what H1e decides.) RUN H1e 08:41 (hud_test6): texts made, 12 Draw calls inside EVERY timer-element
call, stock block hidden, STILL NOTHING ON THE FRAME -> the objects or the position space. hud_test7 (1a262c1a; 8e68cc5) = split test: the
timer's own text drawn again at (64,200) + our text at the timer's place, both objects dumped side by side. RUN H1f 09:01: neither test draw visible; the dump: OUR objects keep +0x3c/+0x40 = 0 and an IDENTITY matrix at
+0x50.. while the timer's text holds the stored position and the virtual->view scale (0.005972) - the text Draw (0x8f7420) stores the position and
builds that matrix itself unless +0x30 == 0, so for ours the store never runs. hud_test8 (79281e4f; c06d4a3) probes text 8 inside the render
wrapper right after its Draw and counts refused draws. RUN H1g 09:16: Draw RUNS on ours (position stored, scale 0.005972, dirty cleared,
0 refused) and still nothing on the frame -> the emit loop (one DrawChunk per glyph run: count word +0x2a, chunks [+0x2c], descs [+0x30]) or
what the stock timer draw does after ours. hud_test9 (6ee9192e; fcd72c5): [HUD] Before=1 draws ours first + an emit probe of ours vs the
timer's. RUN H1h 09:41 (Before=1): still invisible; the emit probe: ours count 7, chunk 00011ee8 (same handle space as the timer's), desc
{7, 0, 6f45daa0} against the timer's {5, 0, 47e6cb80} - desc[2] (the material / atlas binding of the glyph run, made by our mid-level create
path) is the ONLY difference. hud_test10 (832460cf; 3d7b482): [HUD] Borrow=1 draws text 8 with the timer text's desc[2]. RUN H1i 09:53:
still nothing; desc[2] is the glyph-run data (walks with the clock), not a material. Last difference at the emit: the LAYER byte (ours 0x0d,
the timer's 0x0f): RUN H1j 10:05 (Layer=15): still nothing. Our glyph chunk handle is 00011ee8 in every process
while the timer's walks with its string (kl-merge-31's observation). hud_test11 (f34877f2; 69ba891): [HUD] Hijack=1 puts our string into the
TIMER's own text object 3 s in 10 (object identity test). RUN H1k 10:19: SetText works on the stock object (its chunk changes at our call) but the timer's
Update rewrites the clock the same frame, so nothing was seen. hud_test12 (08fb2e3c; d8ae6f3): the string goes in inside the wrapped render
slot right before the stock draw: RUN H1l 10:49: 'TOTAL  $0' DRAWN top right - a level-made
ZCHAROBJ draws our string; the 24 objects our create path makes never show (their chunk handle never changes; what the loader does for a
ZCHAROBJ that +0x19c alone does not is NOT established). ANSWER 14b8654: [HUD] Reuse=1 (default) draws the crew list + money box with the
hidden ZFAPlayerListDisplay's own 11 header text objects (+0xea8..+0xed0), string / colour / style set in the render slot before each draw;
RUNS H1m / H1n 11:07-11:25 (hud_test13/14): the ten borrowed objects (five text + shadow pairs, +0xed0 is
not a text) drawn by OUR Draw call are invisible too. So EVERY Draw the hook issues is invisible (cause NOT established: the call matches
the stock one argument by argument) and only strings the STOCK code draws show. 0df20f7: [HUD] Reuse=2 (default) wraps the player list's
own Render, keeps it shown and puts our first five crew rows into its pairs right before the stock draw; hud_test15 (2c88a32b) /
hud_ship15 (1e15149c), built from a clean worktree (the working tree's klescort.c is mid-edit by another session). RUN H1o 11:35: refused
after the wrap (the vtable test again); FIXED 1c817c8: hud_test16 (d1d5c94a) / hud_ship16 (5ad8867d). RUN H1p 11:49: the five pairs took our strings but HideStock still hid the element (the
forced-off line ran before the Reuse key was read; fixed 4636092 = hud_test17 / hud_ship17). OWNER BACK AT THE PC 12:15: runs paused; H1q (hud_test17, or hud_test16 + HideStock=0)
is kl-merge-31's first run when the owner is away again. The owner's game has ship_main1 (klhud.c in it, [HUD] off).
BUILD NOTE: build hook candidates from `git worktree add <scratch> HEAD`, never from the shared working tree. RUN F2_DM03 07:26 (hud_font2): PASS, glyphs smooth and whole - the font / plate build is
ready for the owner's tab once the hook side is settled.
05:50 2026-10-11: BoardAll's THIRD review (re/boardall_review_rework.md: a scripted test may run, no 'must') and its four points are in (b7fd218): the stillness clock starts again after a missed pass, an escort is no longer dropped for a passing state, BoardAll is off with VanLeftBehind, and the text says what it cannot do. HONEST SCOPE: BoardAll acts only once SOMEBODY HAS CALLED THE VEHICLE; the case of L8 / L10 (the whole crew held at the clerk, no vehicle) is NOT touched by it - that is track A's level-data fix. Replay of L10 / L11 by the reviewer: of 24 spells of 15 s standing without earning, 8 were the trap; L11's two held bots would have met the test at the first visit. Builds <work>/build/klhook/ship_board4 6de5f96e / test_board4 4cf87173 (supersede board1..3), not run. RUNNING besides wf_e831481a-b41 (tracks A / B / C): wf_3ae226ba-065 = track E, the seventh damage factor R+0x1c (a heister at another stage than the player hits police at 0.5 .. 0.1) as a key of the balance dial (klbalance.c; builds ship_bal2 / test_bal2).
05:10 2026-10-11: BoardAll REVIEWED TWICE AND REWORKED (999c304; re/boardall_review_exe.md, re/boardall_review_code.md; a third check of the rework runs, wf_4330a540-ca5). READ IN kl2 BY THE REVIEWS: slot 194 orders stage-3 AI when the vehicle is CALLED or LEAVES (states 1, 2, 5, 6; table 0x8fb0a0), not while it waits; while it waits a stage-3 bot boards by ZBoardEscapeVehicleTactic (0x4fb064), second in every soldier's tactic list, Loot last; the loot tactic's candidates lie within 800 units and 400 in height (tuning +0xc1c..); the vehicle waits 8 s a visit, one visit every ~29.5 s, and is only called by somebody standing in the exit trigger; a grab the bot walks away from is cleaned up by the rules one update later (0x727cb0). R+0x1c scales the FIRE of an Ally shooter whose stage is not the player's (0.5 on Arcade levels 1-3) - the notes had shooter and victim swapped; with the human outside and the crew inside 'crew->police 1.0' is really 0.5 (a balance key for it is owed). FORM NOW: only a HELD bot (stage 1 or 2, never an escort, 15 s without moving 1 m or earning) gets the stage byte, nothing else by default (BoardAllOrder=0). Builds <work>/build/klhook/ship_board3 47b609e8 / test_board3 079873ba, not run. Live queue: scratchpad now/QUEUE_live.txt.
STATE 2026-10-11 (kl-merge-01, Fable; the owner asked for frugal work). COMMITTED 76bfdcd: kl_fa_bots_dyn FORK_GAP 0.1 s timer before every RandomTrigger (candidate fix for the 0x686a66 crash) + the step builds on the room-first gate. PASS offline, NOT RUN LIVE: <work>/build/z_route7/retomoto_full (rt_full7 + routes) and <work>/build/z_cover3/M03 (bank + cover, dyn). Installed tab stays w_tabC. kl-merge-31 runs three offline tracks (loot-held bots: kl_fa_bots.py; 0x686a66: kl_fa_bots_dyn.py; converter vs luvsic: kl_convert/kl_fa/kl_map_ai) - do not edit those files until they report. kl-merge-9b 88ad206: .WAV slim candidate <work>/build/wavslim/DM09_l (swap two files, listen) for the next Retomoto run. NEXT LIVE (owner away only): z_route7 with hp_test [Bots] Log=2, then z_cover3/M03.
SOUND BANK SLIM (kl-merge-9b, 2026-10-11 03:05; commit 88ad206; BUILT, NOT LOADED LIVE): tools/kl_wavslim.py and
`kl_graft.py lighten <build> <out> --load wav`: the .WAV beside the archive (the fifth large block, read whole) without
the clips nothing in the level can play - on Retomoto 151 of F07's map sounds (sirens, traffic, machines), 27.8 -> 17.8 MB;
each of the four Dead Men maps would give 10 MB too. The .WHD keeps every record in place and the .SND is untouched (a
dropped record points at a shared silence block), so the archive is byte-identical. Stock FA levels lose nothing
(`kl_wavslim.py test` PASS). Candidate pair: <work>/build/wavslim/DM09_l (= w_tabA DM09 + slim bank). LIVE CHECK OWED
(game holder): swap only F06_Main.WHD/.WAV of the tab's DM09, load Retomoto, listen for the blast / music / guns, read
the 'memory: at the level's largest block' line (.WAV block 17.8 instead of 27.8 MB). RISK: a sound named by code or
by an animation event under SFX/Environment that no stock FA level uses (none found).
04:15 2026-10-11 (first session; the owner at the PC said 'continue'; OFFLINE): workflow wf_e831481a-b41 runs three tracks, each worked -> adversarially reviewed -> fixed (task files: scratchpad wf/A_loot_trap.md, B_defend_crash.md, C_convert_audit.md): A = bots held by loot they cannot take (the grab path, the window, a census of the five builds, the fix in kl_fa_bots; builds <work>/build/z_loot3), B = the 0x686a66 crash (kl_fa_bots_dyn; builds <work>/build/z_route4, Retomoto from rt_full7), C = the converter against luvsic's four faults (kl_convert / kl_fa / kl_map_ai; no rebuild). NOTHING of it is installed. BoardAll reworked (ad3070d: the stage byte no longer waits for the order test; builds ship_board2 8683b0ba / test_board2 735ad362, not run). Live queue for when the owner is away: scratchpad now/QUEUE_live.txt (L12 first). Resume the workflow after a usage limit with that run id.
INSTALLED 2026-10-11 03:50 (kl-merge-0e; game closed, the owner at the PC: watch-only): tree <work>/build/w_tabC = w_tabM with DM09 =
<work>/build/rt_full7/retomoto_full = rt_full6 + THE ROOM FIRST (commit be66e7b: the seven hold at the blown window; their chain starts from
kl_fa_author's room counter through Counter_room_clear when the boardroom's three squads are dead, fall-back Timer_start_bots at blast + 75 s =
91.5 s after the round-start event; --enter-after-blast = as before). Chain rt_full7: 1_guns (= rt_full6's) -> 2_bots -> 3_talk -> Bain (clips at the
same stream offsets as rt_full6: the installed PC_Def.str serves). All offline checks PASS; NEVER LOADED. Hook unchanged (ship_hop1 212f2641),
owner's ini checked after the install: Escort=1, [Crew] Random=1, Risk=2, CopToCrew=0.05. TO SEE (the owner, or a scripted run with hp_test
[Bots] Log=2 when they are away): the seven at the window after the blast, in once the room is clear, how long they live; a bot standing still =
look for loot it cannot take under it (kl-merge-31's Late Night finding).
03:36 2026-10-11: SOMEBODY IS AT THE PC (keyboard / mouse input at 03:35:18 with nothing of ours running; Discord in front since 03:22). WATCH-ONLY AGAIN: no scripted TEST-hook run until the owner says they are away. Game folder = the owner's state: SHIP ship_hop1, tree w_tabM (DM01 z_route3/M01 gate + dynamic, DM02 z_m02s1/M02 one loot stop, DM03 z_hop/M03, DM06 z_route/M06, DM09 rt_full6), ini Escort=1, CopToCrew=0.05. NEXT LIVE STEP when allowed: L12 = Late Night Opening with <work>/build/klhook/test_board1 and [Bots] BoardAll=1 (do the two bots at the watch cases get 'board: record N ... heist stage set to 3, sent' and board?), then ship_board1 + BoardAll=1 for the owner.
LATE NIGHT OPENING, WHY THE BOTS NEVER LEFT (2026-10-11 02:45-03:20; runs L8 / L9 / L10 / L11_DM02; positions by a TEST-ONLY KLJoin.ini with a [CrewHop] nobody can stand at + [CrewHop] Dry=1 Log=2 = every bot's place every 5 s; scratchpad now/cases.py, lootat.py, lootdep.py). With the two-stop build (z_route/M02, on the tab until 03:10) all bots loot the jewel store and the watch shop and then STAND ON ONE SPOT, (-1772, 500, 2792) = Civilians!Civ_male_watch/female_clerk (OnlineMoneyCtrl 75,000, TYPE_NORMAL), until the round timer ends the round at 6:00; nobody reaches stage 2, the van is never called. CAUSE (re/bots_squad.md 4 + these runs): the game's ZLootTactic (0x451920) goes on choosing any registered money object in reach that is not 'taken' ([obj+0x6c] != 0 and inside the tuning's distance window, kl2 0x8b94d0); one a bot cannot take holds him for good, and the tactic beats the route chain's Defend orders; it lets go only at stage 3 with the vehicle waiting. The loot wait is NOT the fault (0x811fb0: depleted OR the deadline). ONE STOP (kl_fa_bots owner ... M02 --stops 1 -> <work>/build/z_m02s1/M02, + dynamic step; ON THE TAB NOW as tree w_tabM): run L11_DM02 - five bots leave, the van comes three times, five escape; two stand at (-1278, 500, 1884) in front of the closed watch cases Watches_M6_01 / M5_01 (TYPE_CONTAINER, nobody opened them). HOOK ANSWER, BUILT, NOT RUN: [Bots] BoardAll=1 (klescort.c; <work>/build/klhook/ship_board1 0f36810f / test_board1 fc6d256e): while the vehicle waits, every AI heister under stage 3 gets stage 3 (one byte) and the boarding order. Its first live run (L12) never left the menu: DISCORD held the foreground from 03:22 on (the game only pumps messages when not in front) - check the foreground before the next scripted run, and whether the owner is back. OPEN: why the clerk's money cannot be taken by a bot; the same trap can sit on other maps wherever a bot passes loot nobody opened.
ESCORT RELEASE SEEN (2026-10-11 02:38, run E3_DM01, Hot Coffee as installed, TEST test_hop1, Escort=1, idle player): record 3 chosen 3 s after GO, 13 re-points while his route pulled him away, 'released (the vehicle waits, state 3): sent to the boarding place (6673, 122, 20766)' at GO+125 s from stage 0; he walked the ~100 m, took stages 1 -> 2 -> 3 on the way, was ABOARD on the van's second visit and escaped (status 6). No fault. Still unseen: an escort with a MOVING player. kl-merge-0e has taken kl_fa_bots_rt.py (the seven hold at the window until the boardroom squads are dead; asked for a timer fall-back); the balance keys stay with the first session.
STATE 2026-10-11 02:35 (the first session, still running after the hand-over). INSTALLED: tree <work>/build/w_tabB - DM01 = z_route3/M01 = z_gate/M01 + dynamic bots with routes (THE VAN THROUGH THE GATE; live run H_DM01: loads, full round, van leaves, three bots escape), DM02 z_route/M02, DM03 z_hop/M03, DM06 z_route/M06, DM09 rt_full6; hook SHIP ship_hop1 (212f2641); owner's ini [Bots] Escort=1 (an install had dropped it: put back; kl_expansion's block carries it from 5a0eeef on), [Balance] CopToCrew 0.15 -> 0.05.
RETOMOTO BOARDROOM, MEASURED (kl-merge-9b's health log, hook <work>/build/klhook/hp_test, runs HP_DM09 / T1_DM09 / T2_DM09, rt_full6, idle player): the bots die by BULLETS IN VOLUME - 151 hits in 85 s at police->crew 0.15 (steps 4..35), 552 hits in 190 s at 0.03 (steps 1..14), the hit rate rising to ~3 a second as more guards arrive; all seven dead at 85 / 116 / 190 s whatever the factor (0.15, 0.03 + crew->police 3.0 twice). PLUS two ONE-STEP KILLS a run that no factor scales (lost 246.0 of 252 in one tick at 0.03; 202 and 115, 120): source NOT known (close combat? a fall at the blown window?) - log the victim's place next. The bots LOOT while the room's guards live: the owner's design says the main room is looted 'once everyone in it is dead'. PROPOSAL for kl_fa_bots_rt: the seven hold at cover by the window and fight until the boardroom squads are dead (TriggerActorsDead + a timer, kl_fa_bots' --wait-guards is the model), then loot.
CRASH 0x686a66 READ FROM THE DUMP (kl-merge-0e, 2026-10-11 02:30; offline): the faulting object is a CPPScript::ZDefendBehaviourGoal (vtable
0xbccf54) whose +0x04 is its CPPScript::ZSquad; the goal's +0x2c list (3 entries, array at +0x8) had been FREED while the goal still iterates
it (first dwords overwritten, the array zeroed). No bot had died in that run (C_DM09): not a member death. Wiring census: z_route's
Retomoto has 57 chains Defend rout -> RandomTrigger -> Defend rout of the SAME squad, z_route M02 has 48 (five clean runs), rt_full6 none;
stock bots have the same pattern 119 times, so it is a chance race, not a forbidden shape. Untested data-side fix if it comes back: a
TriggerDelay2 of 0.1 s between a Defend rout's arrival list and the RandomTrigger (kl_fa_bots_dyn), so the old goal finishes its tick first
(ASSUMPTION). Until then Retomoto on the tab stays rt_full6 (no forks). Scratch readers: kl-merge-0e scratchpad goal*.py, rt_refs.py.
BOT HEALTH LOG (kl-merge-9b, 2026-10-11 02:30; commit 1e5674f; NOT RUN): for 'all seven bots die in the boardroom' - [Bots] Log=2
now says every loss of a bot's health ([actor+0x5fc], the NPC's 0x28-byte health object; 'record 3 (bot): lost 0.6 (279.4 of
280.0)'): many 0.6 steps = bullets at the stock 0.01 factor, one step to 0 = blast / fall / kill volume. Builds <work>/build/klhook/
hp_test (24c781b9) / hp_ship (78973f5d). NOTE: runs B/C_DM09 did NOT test zero police damage - Risk=2 takes max(dial, stock), so
CopToCrew 0.00 ran as 0.01; the deaths (one at a time, 28-85 s after GO, looters and non-looters alike) are still unexplained.
HAND-OVER 2026-10-11 02:10: this session (it held the game and the four maps / bots) hit the WEEKLY usage limit (agents fail; resets Oct 16); the owner asked kl-merge-0e to continue the queue. Nothing is running. State = the LIVE NIGHT entry below. Boot check of the installed SHIP hook ship_hop1: starts, every part reports, no fault (it sat at the menu and was ended by the tool - not a hang of the hook). kl_expansion install rewrites the ini's expansion block: check [Bots] Escort=1 and [Crew] Random=1 after any install. QUEUE: (1) the 0x686a66 Defend-step crash on z_route/retomoto_full (dump %TEMP%/kl_triage/20261011_013427) - until found, Retomoto stays rt_full6; (2) z_gate/M01 + `kl_fa_bots_dyn.py build` -> checks -> tree -> live load -> tab; (3) why Retomoto's bots all die in the boardroom (not bullet damage); (4) z_cover2 (M03 from z_hop/_bots/M03); (5) escort with a moving player and the release at the vehicle; (6) fed, Guns page, converter comparison with luvsic's findings. Live test recipe: scratchpad now/mkrun.py + kl_autotest --hook test_hop1.
LIVE NIGHT 2026-10-11 00:25-01:55 (the owner: 'im away you can test yourself'; scripted runs through the tab, TEST hooks, idle player, logs <work>/build/klhook/live/R12_* H0_* E0_* E1_* G_* A_* B_* C_*; scripts: scratchpad now/mkrun.py). INSTALLED NOW: tree <work>/build/w_tabA = DM01 z_route_ng/M01 (routes, NO gate), DM02 z_route/M02, DM03 z_hop/M03, DM06 z_route/M06, DM09 rt_full6 (the OLD bots: see the crash); hook SHIP <work>/build/klhook/ship_hop1 (212f2641: + klescort.c, klhop.c), owner's ini [Bots] Escort=1, [Shoulder] Log=0.
- LOADS + ROUNDS: all five route builds load and play 4 min. Park: 7 of 7 bots escape (helicopter, three trips). Hot Coffee: 6 of 7 escape. Late Night: 4 of 7 alive at 4 min, still looting (stage 1). Withdrawal: see below.
- HOT COFFEE GATE BUILD CRASHED AT LOAD (stack overflow 0x796ff4): a relay naming its own node + 'GetMatPosAnim' (re/map_escape.md 19.2). Re-wired; the new z_gate/M01 loads and the van drives its leave leg with six bots aboard (run G_DM01; the fence was not in the picture). Not on the tab yet: it needs the dynamic step on top (waits for the crash fix below).
- WITHDRAWAL WALL FIXED AND SEEN: polygon byte +1 = number of waypoints (re/bots_bank.md); run H0_DM03: 'bot 1 left From of hop 1 after 2.4 s by itself', stage 3, van called, three of three survivors aboard and escaped. klhop.c stayed in dry run: not needed.
- ESCORT WORKS LIVE (E0 dry, E1 Escort=2 on the bank): two bots re-pointed beside the idle player for 2.5 min by 0x760e50, no fault, picture research/shots/E1_DM03_170s.png (Tommy beside the player). Not seen: a moving player, the release at the vehicle.
- RETOMOTO: (1) CRASH 0x686a66 (in ZDefendBehaviourRout's member loop, garbage pointer) 70 s after GO in ONE of four runs of z_route/retomoto_full - an agent is on it (-> <work>/build/z_route2); until then the tab's Retomoto is rt_full6. The other four maps keep their route builds (five clean runs), same risk not excluded. (2) ALL SEVEN BOTS DIE in the boardroom within 95-150 s when the player does not help - with the old bots too (run A_DM09_old) and even with police->crew 0.01 (runs B_*): not bullets on that scale; cause open.
COVER STEP, SECOND ROUND (2026-10-11 night; re/bots_dyn_build.md 13; builds <work>/build/z_cover2/<map>, NOT INSTALLED): a cover record takes only the entity's 128-byte slot (kl2 0x603830: matrix, place, box middle +0x30 and half size +0x40, name) - no mesh, collision record or room tree, so the stock 'form b' box is a whole cover and form a is dropped (default --models b). Corner finder written (stock placement measured on F05 / F08) but gives only 6 boxes (M03 4, Retomoto 2): wall corners are NOT the big missing class. Boxes: M01 2, M02 9, M03 22, M06 15, Retomoto 4; holds 53->55, 87->92, 50->72, 61->70, 91->95. 4 low boxes (M01 2, M02 2) borrow F07's hidden 100-cube camera model (ASSUMPTION; --no-borrow). M01 has no thin high form-b model (alternative <work>/build/z_cover2/_ab/M01 with form a). All checks PASS. The tab stays on w_tab12 until the owner has played it; z_cover2 is the next swap (only Withdrawal gains much).
ESCORT BOTS WRITTEN, NOT INSTALLED, NOT RUN (2026-10-11 night; klhook/klescort.c, re/bots_escort.md): [Bots] Escort=N makes 1-2 non-traitor bots hold ~3 m beside the human by the game's own order routine ZSoldier vtable +0x13c = 0x760e50 (pos, soft 0, reset 1, 0) - the call the heist rules themselves make at 0x8fb04c to send AI records to the boarding place; released to the boarding place when the vehicle waits. Off by default. Builds <work>/build/klhook/ship_esc1 (f5fe0bbb) / test_esc1 (ee711e29): compile only. Live order E0 (EscortDry=1) .. E5 in re/bots_escort.md - needs the owner away. Scratch folder C:\kl_esc is left over (the agent's removal was refused).
COVER STEP BUILT, NOT INSTALLED (2026-10-10 late; tools/kl_fa_cover.py, re/bots_dyn_build.md 12; `python tools/kl_fa_cover.py all <work>` -> <work>/build/z_cover/<map> = cover boxes at real static objects near holds that found none + the dynamic step with routes): new boxes M01 8, M02 9, M03 20, M06 15, Retomoto 2; holds 53->60, 87->93, 50->69, 61->69, 91->95. All offline checks PASS. HELD BACK: most new boxes on M01 (8 of 8), some on M02 / M06 / Retomoto are 'form a' (a model with a collision record, listed in the root's room tree 0 - no stock cover box is), unproven; the tab stays on w_tab12 (z_route) until the owner has played it. Gaps that stay: open tarmac (M01 car park), M02's gallery, M03 beyond the drop, M06 lawns; wall CORNERS are not handled (largest class left).
INSTALLED 2026-10-10 22:14 (game closed; the owner: 'are u doing the routes yet'): tree <work>/build/w_tab12 = <work>/build/z_route/<map> = RANDOM ROUTES for the bots (`python tools/kl_fa_bots_dyn.py routes <work>`; re/bots_dyn_build.md 11): a RandomTrigger (stock F07 Squad#02 form) between the fixed places draws one of 2-3 ways per bot per round - another mesh corridor where there is one, else the way moved 1.7-3.2 m to a side; forks M01 32, M02 59, M03 34, M06 29, Retomoto 42. kl_fa_bots.check / kl_fa_bots_rt.check now walk every branch. Checks PASS on all five (dyn check, impact 0, audit, guns, van-check). NEVER LOADED IN THE GAME; RISK: squads of 707-1,256 nodes (largest stock squad 694), +550..950 entities a map. STEP BACK if a map does not load: `--ways 2`, then tree w_tab11 (no routes), w_tab10, w_tab9. The owner has not played since 20:47, so the dynamic bots, the gate and the plane fix are all unseen.
INSTALLED 2026-10-10 21:28 (game closed): tree <work>/build/w_tab11 = w_tab10 with Hot Coffee = <work>/build/z_dyn3/M01 = <work>/build/z_gate/M01 (re/map_escape.md 19: the van drives THROUGH THE GATE, 80 m, ends 13 m past the fence; Dead Men's car RAMS the gate - the fence piece's throw is a KEYS chunk that is in the .buf; wired from the van's leave message by a 7.32 s timer; second escape camera kept) + the dynamic bots. Checks PASS (van-check 0 faults, impact 0, bots PASS). NOT LOADED IN THE GAME. ASSUMPTIONS: Dog Days plays the Dead Men KEYS chunk; if not, the van passes through a fence that stands. Fall-backs: w_tab10 (no gate), w_tab9 (no dynamic bots).
INSTALLED FOR THE OWNER 2026-10-10 21:20 (game closed; pushed to main on the owner's word at 20:20): tree <work>/build/w_tab10 = <work>/build/z_dyn2/<map> = the DYNAMIC BOTS (tools/kl_fa_bots_dyn.py: holds at cover boxes, staggered starts, seven roles, no sprint; re/bots_dynamic.md, re/bots_dyn_build.md) re-applied on z_rumble/M01, z_final/M02 M03 M06 and rt_full6/retomoto_full. Offline checks all PASS (kl_fa_bots_dyn check, kl_impact 0, van-check 0 faults); NEVER LOADED IN THE GAME, the workflow's review agent died on the usage limit. FALL-BACK: tree w_tab9 (same maps without the dynamic step). [Balance] CopToCrew still 0.15: raise toward 1.0 once the bots are seen to live longer. Hot Coffee (M01; the owner calls it 'coffee walk' / 'the warehouse one'): the plane's DistanceRumbleCam is taken off (owner: 'can barely see anything for a few seconds after the plane comes by'; ASSUMED cause: its AnimatedRumbleCamera clip is Dead Men .ANM we do not carry) - in w_tab9 / w_tab10, not yet seen by the owner. Owner: 'the van is almost perfect on coffee walk you just dont go through the gate like the original game does' - the drive ends 900 before the fence gate on purpose (kl_map_escape GAP); an agent is extending it (<work>/build/z_gate/M01; then the dynamic step again). SHOULDER SWITCH: the klshoulder log of the owner's Late Night Opening round 20:24 (z_final/M02) shows every press in the open flipping want and side (4 of 4), as on Hot Coffee and stock; a press while being knocked (in 0x11, down state 2) is ignored. No fault seen in this build - ask the owner whether it still looks wrong. Fourth DiscordHook.dll+0x1f7fd fault at 20:23:14.
INSTALLED FOR THE OWNER 2026-10-10 19:43 (swap8, game closed): tree <work>/build/w_tab8 = z_final maps (key-framed F07 van + bots on M01/M02/M03) + rt_full6 Retomoto (street buses / car as cover, Lynch's balcony line at 11.5 s); hook ship_all5 (sha1 8e08d469, adds the read-only klshoulder.c) with [Shoulder] Log=1. The owner's sessions 19:02-19:37 were STOCK Subway from the stock Arcade page (log: 'menu page 0'), so the z_final vans and the shoulder log have NOT been played yet. Bots-dynamic workflow (tools/kl_fa_bots_dyn.py, builds <work>/build/z_dyn/<map>) had written its builds by 19:45, review pending; they sit on y_loot2 / rt_full4 and must be re-applied on z_final / rt_full6 before they go on the tab; then raise [Balance] CopToCrew (0.15) back toward 1.0.
OWNER 2026-10-10 ~21:40: the blast after the whole line 'comes too late now' -> the bang goes ON Kane's 'NOW!' (kl-merge-b6 v5:
BLAST_DELAY 12.5 = blast 16.5 s after the event; the lead's chain builds <work>/build/rt_full5 and tree w_tab6). RANDOM CREW SEEN BY
THE OWNER on the bank ('the ai heisters do go random on withdrawl'); on Retomoto not seen (the installer had reset [Crew] to 0:
fixed). NEW FAULT: 'on late night i think the thing u did broke my shoulder leaning but withdrawl its fine' - workflow
wf_3cfb5265-08b (re/lean_m02.md). Bank with bots: 'once the garage door comes open literally just get slimed out' = the bots die at
the garage door; the bots-dynamic workflow has it.
OWNER, 2026-10-10 ~21:00, after playing the swap of 20:35 (tree w_tab5, hook ship_all4, [Balance] Risk=2): 'the difficulty i love ...
but damn the ai heisters just path the same then die so quick now because of the changes ... make them more dynamic give them a bit
of personality ... utilise cover and they know whos infront of them'; THE COUNTDOWN IS RIGHT NOW ('the explosion actually plays
after the whole voiceline'); 'bain voice lines are all amazing'; Late Night Opening's cases not checked yet. So LIVE BY THE OWNER:
balance Risk=2, Retomoto v4 blast timing, Bain, the talk. Interim: [Balance] CopToCrew=0.6 in the owner's ini (read at the next
start). RUNNING: wf_0348ba9c-840 bots-dynamic (re/bots_dynamic.md -> tools/kl_fa_bots_dyn.py -> <work>/build/z_dyn/<map>, review)
and wf_e36051ed-52b van-plus-bots (<work>/build/z_final).
STATE 2026-10-10 20:30. RULE FROM THE OWNER: while they are at the PC, testing is WATCH-ONLY (SHIP hook, tools/kl_watch.py running,
KLHook.log) - no scripted TEST-hook runs unless they say they are away. PENDING AUTO-SWAP when they close the game (background
task, scratchpad now/swap5.py): tree <work>/build/w_tab5/KLExpansion = four maps <work>/build/y_loot2/<map> (bots open Late Night's
glass cases by 'Activate' / 'Open' relays, the diner's exit boxes cut so the warehouse people can be looted, a drop link on the
bank; still the SPLINE car) + Retomoto <work>/build/rt_full4/retomoto_full (kl-merge-b6 v4: blast 19 s after the round-start event;
countdown scene Delay=0.30 on the GO clock; bots, guns, talk, Bain); hook SHIP <work>/build/klhook/ship_all4 (e1227328: + klbalance.c);
owner's ini gets [Balance] Enable=1 Risk=2. BALANCE (re/balance.md): Arcade scales every hit by six floats per Arcade level (who
shoots whom), level 1: police -> you 0.1, you -> police 2.0 = police need 91 body hits on the player, the player 2 on a
policeman; stock Subway is the same. Risk=2 writes 1.0 for all six and 400 health. NOT RUN LIVE. RUNNING: wf_e36051ed-52b
van-plus-bots (review defects D2-D4, then <work>/build/z_final/M01..M06 = F07's key-framed van + bots).
STATE 2026-10-10 19:15. INSTALLED: tree <work>/build/w_tab3/KLExpansion (the tab's Retomoto = <work>/build/rt_full/retomoto_full: v3 +
wardrobe + plates + guns (Entries) + BOTS through both halves (kl_fa_bots_rt) + TALK (kl_fa_talk) + BAIN (kl_bain)), hook SHIP
<work>/build/klhook/ship_all3 (cd8c5f45), <DD>/PC_Def.str = <work>/build/v_bain/over_talk/PC_Def.str (1,694,610,488 bytes: base +
talk + Bain clips; the previous one is <work>/build/PC_Def.str), owner's ini: [Crew] Random=1, [Talk] Enable=1, [CrewJoin] Enable=1,
[Bots] Enable=1 Log=1. LIVE: T2 - Kane's six countdown lines are SAID and the owner HEARD them ('i hear the voiceline on kane but
it doesnt match the explosion timing'); bot chatter lines said. The round-start event is 8.4-8.8 s BEFORE GO (state 0x19 = GO),
so the blast (event + 13) is at GO + 4.5 and a clock started at GO is 8 s late. THE GAME DOES NOT SPEAK BEFORE GO: setting
[session+0x15d] in the pre-round (run T4) said the early lines and then froze the round grey 8 s after GO - removed, do not
retry. OWNER'S DECISION: the explosion comes AFTER Kane's last line; he also wants 'NOW! Let's get them all' (it is clip 5 + 6).
ASKED kl-merge-b6 for Retomoto with BLAST_DELAY 15 (blast 19.0 s after the event = GO + ~10.3); then: finish chain, countdown
scene Delay=0.30 on the GO clock, back onto the tab. Until then the countdown on the tab starts 5.8 s after GO (after the blast).
NOT YET LIVE: bots through the Retomoto lift ([CrewJoin]), Bain by ear, a fed at a death, [Fed] Player=1.
2026-10-10 18:40. HOOK INSTALLED FOR THE OWNER = SHIP <work>/build/klhook/ship_all1 (fa1b1eb6): + klcrew.c, klcrew_rt.c, kltalk.c,
klfed.c, all OFF unless enabled; the tick now runs ONLY from the main loop's two SteamAPI_RunCallbacks sites on the main thread
(the wrapper used to pass all twelve call sites as 'game thread'). The owner's KLHook.ini got [Crew] Random=1.
LIVE with the TEST sibling test_all1: C0 menu control clean (no new line); C1 RANDOM CREW WORKS on Late Night Opening - 'round
draw 1 (session state 16 ...)', bots became Liam, Pierre, Lynch, Tommy, Kane, Parker, Red through the game's own model routine,
variants and voice bytes set, no fault; F0 / F0b fed log: 8 police bodies, 7 free (one is taken at the session start), the squad-
script chain holds on all seven bots ('MUTED'). NOT YET LIVE: a bot's death releasing a fed, [Fed] Player=1, the Retomoto join
for bots ([CrewJoin]), the talk ([Talk] LogOnly=1 first). The 14:24 crash was the Copilot package's menu XML (element 5000 of
the frontend table was a plain Window; kl2 0x861720 has no 'no element' test), not klcrew.c - re/hook_review_talk.md.
OWNER PLAYED THE TAB'S MAPS WITH BOTS (2026-10-10 ~18:00): 'the issue on late night is they dont shoot open the casing stuff bc its
glass and u need to shoot it to loot, the van is such a damn problem and they dont loot the warehouse people on diner not sure about
park, the bank they gotta vault on the garbage then over the wall, one thing i can definitely say is they dont have much health
when i shoot them but when they shoot me i have a llot of health not proportional and the coppers dont seem too intimidating it
should be all the same kinda risk and how the traitors could be'. RUNNING: workflow owner-play-fixes wf_06722b28-02d: p-balance
(klhook/klbalance.c + kl_map_ai: player vs cop vs heister on one scale, MEASURED first), p-loot (kl_fa_bots: glass cases, the
diner's warehouse people without calling the vehicle early, a way over the bank wall), p-van (kl_map_escape: replace Dead Men's
ZHavokCar-on-a-spline by F07's key-framed van as on Retomoto), review re/play_fixes_review.md. Builds: <work>/build/y_bal, y_loot2, y_van.
COME BACK AS A FED (2026-10-10 17:45; re/fed_respawn.md, re/fed.md, re/fed_review.md; klhook/klfed.c + tools/kl_fa_fed.py written,
NOT wired, NOT run): the Arcade rules still hold the whole multiplayer 'dead criminal returns as police' path; Arcade skips it
because the round-over gate 0x67f480 says 'over' with one human - unless dword [0x168ea60] (zero .data, two readers, no writer,
unhashed) is not 0. klfed.c [Fed] Player=1 holds it at 1 while the human is alive or waiting: the game's own path gives the death
camera, a police body at an AFTER_DEATH point and the player switch. LIMITS: the life is still lost at the round end, a second
death is final, 8 police bodies per level load (the hook counts and stands down before the game's int3 at 0x4b2984), the fed's
WEAPONS are not established. BOTS: a parked one-man police squad per heister (kl_fa_fed.py; <work>/build/x_fed/M02), released by
the heister squad's 'wiped out' list; boarding also counts as wiped out, so [Fed] Bots=1 mutes the latch and re-fires it at a
real death. REVIEW: wire in switched off; fix klp_b[] not cleared at a new round before any second round with Bots=1; the stock
precedent for 'a squad list starts a hunt rout' is refuted (may still work). Live order F0, F0b, F1 (on the bank), F5b.
2026-10-10 17:00. BOTS ON RETOMOTO SEEN LIVE (run RB1, <work>/build/v_rtbots/retomoto_bots_tower, bot log): seven bots on the balcony,
all at heist stage 1 within 16 s of GO (in after the blast), loot $255,000-$820,000, three killed by the guards; no fault. The full
build (tower -> hook teleport at the join -> street -> van: retomoto_bots + klhook/klcrew_rt.c) waits for the hook. crew-talk-bain
RESULTS (re/crew_talk_review.md): klcrew.c random looks (not live), tools/kl_fa_bots_rt.py, tools/kl_fa_talk.py (Kane's countdown,
Kane / Lynch scenes, chatter: DATA only, the hook part kltalk.c is being written), tools/kl_bain.py (Bain for the driver and
briefing lines, 27 lines; needs a new PC_Def.str: <work>/build/v_bain). RUNNING: wf_1b137346-3c1 (kltalk.c + crew review fixes +
wiring + the 14:24 crash), wf_c2559c04-0b1 (come back as a fed). The 4 GB flag (kl-merge-39 prepared <work>/build/laa/kl2.exe) is
NOT to be run: the engine marks direct pointers by the top bit (klmem.c), and kl2.exe is a stock file - told kl-merge-39.
STATE 2026-10-10 16:50. INSTALLED TREE = <work>/build/w_tab2/KLExpansion: the tab's four maps are now <work>/build/u_maps/M01,
M02, M03, M06 (gun looks + escape camera + tougher enemies + seven AI heisters; KLGuns.ini carried), Retomoto = rt_guns3 (no
bots yet), map pictures on the page. Hook ship_bot1. LIVE on each u_maps build (runs U_M02, U_M01, U_M06, U_M03, bot log on): all
load and reach GO, no fault. Diner: the vehicle is called ~70 s after GO, all seven bots aboard and escaped by 2:50, the idle
player left behind (still early - '--loot-seconds' / the tuning's wait are the knobs). Park: same at 3:00. Late Night Opening:
bots loot (up to $150,000) and stay at stage 1 for the 3.5 min watched. Bank: bots loot up to $840,000, stage 2, stay in the yard
(the two mesh parts are not joined). The unknown hook of 14:24 was the owner's Copilot ('done nothing useful', owner): its
klhook.c lines were reverted; tools/kl_add_plates.py and the 'plates' command in kl_chars.py stay uncommitted scrap.
STATE 2026-10-10 16:20. INSTALLED: the EXPANSION TREE <work>/build/w_tab/KLExpansion (python tools/kl_expansion.py install ...
--replace --no-stream --no-hook; the old KLExpansion is KLExpansion.before-0): Arcade -> 'Dead Men maps' = Hot Coffee (F01),
Late Night Opening (F02), Withdrawal (F03), A Walk in the Park (F04), Retomoto Tower (F06 = rt_guns3 build); SUBWAY IS STOCK
AGAIN. LIVE: TAB_PAGE, TAB_DM09 (Retomoto through slot F06: wardrobe 12 masks, round at GO), TAB_DM03 (bank through F03) all PASS -
first levels loaded under another slot name than F01. Hook now = SHIP <work>/build/klhook/ship_bot1 (f4562d32; [Bots] / [Guns]
inert unless enabled). K2 live: Tune written, 'backstab: bot 6 may turn', record 6 TRAITOR, aboard, escaped (whether he SHOT at the
player was not seen: the player stood idle and lived). AT 14:24 A HOOK 'built 14:17:58' WITH klcrew.c WIRED (G:/kl_scratch/
ai_crew_hook, not this session's) CRASHED TWICE AT THE MENU (0x3f800000 called from 0x8618b9 <- 0x6175ac <- 0x7471ee; dump in
<work>/research/crash_1010_1424): klcrew.c is NOT to be installed before its review. klhook.c in the working tree has the three
klcrew lines uncommitted - a build from the tree includes it. RUNNING again after the 14:10 usage limit: crew-talk-bain
(wf_79796da2-0dc: Retomoto bots, talk, review; klcrew and Bain parts returned) ; come-back-as-fed must be relaunched.
THE FOUR MAPS IN THE TREE ARE STILL z_maps (no bots, no tune): swap in <work>/build/u_maps/<map> after a live load of each.
LIVE 2026-10-10 13:47-13:52, run K1 (TEST hook <work>/build/klhook/test_bot1 = ship_stall + klbot.c + klgun.c Version 2 after the
review fixes; SHIP sibling ship_bot1 f4562d32, NOT installed; b_bots/M02 Late Night Opening, [Bots] Enable=1 Log=1): THE CREW LOG
WORKS and settles the questions - records 1..7 are 'bot', actor vtable 00bb3bac = ZFFActor; every bot reaches heist stage 1 within
50-60 s of GO and LOOTS ($20,000-$120,000 each); stage 3; the van comes (state 3) about 2.4 min after GO, 'record 4 (bot):
aboard', 'record 7 (bot): aboard', the van leaves (state 5 -> 7) and three bots end 'status6 g3' (escaped), one 'dead', three
left in play with their money - with the idle player left behind. So the AI heisters DO go to the vehicle and board (the owner
had not seen it). Status 6 = escaped is new (the notes had 4 = aboard, 7 = dead). Next live: K2 Tune (traitors), Backstab, Bribe,
Leave; H1 guns (every KLGuns.ini needs Entries=<chunk count> now: kl_map_guns.py check prints the line).
OWNER 2026-10-10 ~14:00: 'i want to make it so you can come back as a fed or the ai heisters can come back as feds too'; through
kl-merge-b6: 'make sure that the ai also go to the vehicle', the Dead Men maps on 'its own tab', and 'the original FA dog days maps
to have these mods in the game too'. SPLIT with kl-merge-b6: stock maps with the mods = b6 (new tools/kl_stock_mod.py, builds in
G:/kl_scratch/stock_mod); bots boarding, the tab, the fed respawn = this session. RUNNING: wf_5d20ea26-dc8 come-back-as-fed
(re/fed_respawn.md -> klhook/klfed.c, tools/kl_fa_fed.py, <work>/build/x_fed; review re/fed_review.md); wf_2172effb-c70 dead-men-tab
(klslot.c page latch, mkoverlay expansion page, tree <work>/build/w_tab/KLExpansion). A TESTER PACKAGE (the owner asked kl-merge-39)
must not carry game data: hook + tools + a build script run on the tester's own installs - told kl-merge-39 and the owner.
OWNER ASKED 2026-10-10 ~13:45 (verbatim in .wf/round_prompts8.txt): AI heisters drawn at RANDOM from Dead Men and Dog Days bodies /
outfits; bots that backstab, stay by you, try to leave you behind; BOTS ON RETOMOTO; an EASTER EGG - a Kane in the round speaks the
campaign's countdown to the blast; a Kane - Lynch EXCHANGE when both are in (Retomoto, maybe the other maps); more of the games'
own voice lines; BAIN (Payday 2) as the announcer. RUNNING: workflow crew-talk-bain (.wf/crew.js): klhook/klcrew.c, tools/
kl_fa_bots_rt.py, kl_fa_talk.py, kl_bain.py -> <work>/build/v_rtbots, v_talk, v_bain; review re/crew_talk_review.md.
'Help you up' is NOT possible in Arcade (kl2 0x5fe270: the downed state exists only in session mode 2) - told the owner.
SLOT 2026-10-10 13:37 = <work>/build/rt_guns3/retomoto_ai3_guns: Retomoto v3 (kl-merge-b6 b7934cd: rifle guards eCustom 75 = really
sharper) + wardrobe + plates + gun looks REFITTED (turned 10 degrees into Dog Days' hold, Zastava-as-MP5 sounds like smg_type79,
P90 on the Type 05). Load check RT3 PASS. Hook still ship_stall (klgun Version 1: the Guns page does nothing yet).
LIVE TODAY: bots on Late Night Opening (BOT_M02: seven with money in the shop, round NOT ended in 3.5 min) and the park (BOT_M06:
round ended 189 s after GO); control BOT0 (diner, no bots): round does not end by itself -> on the diner and the park the BOTS end
the round early. HOOK PARTS WRITTEN, NOT INSTALLED: klhook/klbot.c ([Bots]: crew log, traitor tuning, backstab, bribe as data,
leave without you, van; help-up is impossible in Arcade - the exe only allows it in mode 2) and klgun.c Version 2 (hide bit);
review re/hook_review_1010.md (B1-B4, G1) being applied by workflow wf_490b2524-d5b; then live K0, K1, K2, H1. Also running:
wf_d5735753-e22 (map AI defects F1-F3 + bots on top -> <work>/build/u_maps).
2026-10-10 13:25 (the owner: 'carry on with everything you can have the whole pc to yourself' - live runs are free until they
say otherwise). AI HEISTERS SEEN LIVE on the diner (runs BOT1, BOT2: <work>/build/b_bots/M01 and M01_slow): seven bots with name
tags and money walk to the diner, loot and gather at the escape; no fault. The round ended 152-156 s after GO in BOTH runs (escape
countdown on the HUD) - not the squad's loot wait; control run BOT0 without bots under way. MAP-TUNE RESULTS (commit below):
ESCAPE CAMERA FOUND - Dead Men's eFMM_LookFromPosFA means something else in Dog Days (eye at the box's own node = the origin,
under the map): kl_map_escape.py sets eFMM_LookFromPos on the five cameras; no route point is under ground, the car's 'weird' is
not explained (ZHavokCar on a spline runs code no stock level uses). ENEMIES (kl_map_ai.py, re/map_ai.md): the maps have a third
of stock's soldiers, all present from the load; ZSoldier field 4 = accuracy %, 7 = health, a skill name other than eCustom
OVERWRITES the numbers (so kl_arms' 'sharp' row is not sharper than 'swat' - told kl-merge-b6); every car squad loses its
VehicleExitBehaviourRout in conversion. Review (re/map_tune_review.md): F1 reference lists written without ROOT\, F2 / F3 plan
faults on M02 / M03 - being fixed by workflow wf_d5735753-e22 -> <work>/build/t_maps2, then + bots -> <work>/build/u_maps.
2026-10-10 13:20. GUN LOOKS SEEN LIVE by the owner (told to kl-merge-b6): 'it holds the mp5 weird and if i try for the ak 74 starter
game goes grey feels like it crashed weird but it didnt because i could back out then equip the mp5 i dont like how it uses the ak
sound too' = the HIDE BIT WORKS (the MP5 look is drawn alone); the hold (rifle hand places), the fire sound and the grey round
(cause not established; the hook did nothing for that choice) are open. AI HEISTERS BUILT OFFLINE (commit fa75ad9): <work>/build/
b_bots/M01, M02, M06, M03 - load order and risks in re/bots_review.md; NOT loaded yet. RUNNING: workflow wf_b110f0e0-155
(.wf/hook.js): klhook/klbot.c (crew log, traitor tuning, pay the driver, van), klgun.c Version 2 (Guns page switches by hide bit),
kl_map_guns.py fit / sound / grey screen -> <work>/build/rt_guns2, t_guns2; then a reviewer. Also still running: map-tune.
SLOT 2026-10-10 12:46 = <work>/build/rt_guns/retomoto_ai2_guns (Retomoto v2 + baked gun looks) on the owner's word; load check RTG
PASS (GO, no fault; 'guns: on; starting rifle look 0' and no level line = the hook leaves the Version 2 KLGuns.ini alone). The
pictures do NOT show the gun (camera behind the head): G1 is for the owner's eyes. debug/slot.py does not copy KLGuns.ini -
copied by hand into the slot; TEACH slot.py that side file. TO WRITE (lead): klgun.c Version 2 + hide bit (re/map_guns.md 5).
GUN LOOKS, checked 2026-10-10 13:00 (agent t-guns; tools/kl_map_guns.py, re/map_guns.md; NOT RUN IN THE GAME): kl_guns' own way
(variant byte 100 + n) CANNOT work - a gun entity has variant 0 and kl2 0x67cf84 then takes every object, so stock gun and all
looks would be drawn in one another; what hides a part is bit 0x00800000 of the mesh object's dword +0x1c (0x67cf77). kl_map_guns
BAKES one look per gun with that bit (Zastava=MP5, SCAR=SG 552, AK-47=M4A1, UMP=P90, MAC-10=Steyr TMP, M9=USP), KLGuns.ini
Version 2. The Guns PAGE cannot switch until klgun.c takes Version 2 and writes the hide bit (re/map_guns.md 5; the lead's job).
READY TO SWAP IN: <work>/build/rt_guns/retomoto_ai2_guns (= the installed rt_ai2 + looks; problems 0, kl_impact 0, table 65,213,
.prm 79.4 MB, .TEX +8 MB). Live check G1 first: a Beretta carrier holds ONE pistol, a USP. Maps: <work>/build/t_guns/<map>.
SLOT 2026-10-10 12:40 = <work>/build/rt_ai2/retomoto_ai2 (Retomoto v2, e5dd45c9) on the owner's word; load check RT2 PASS (level in 2.4 s, Kane + Wolf, GO, no fault). Van leave leg, enemy lethality and voices are for the owner to judge by playing.
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
