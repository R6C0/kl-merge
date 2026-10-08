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

## Pipeline
1. `tools/verify_levels.py` (run from KL_PortTools): converts M01/M02/M03/M06 FA prp and checks every
   object vs DD (layout, enums, lists, array sizes, duplicate items). Must report `problems: 0`.
2. `kl_package.build('M01_FA_A','F01')` → `build/install/...F01_Main.zip`; copy into DD (backup exists).
3. Test: DD → Arcade Mode → Subway → Accept. Keyboard only (game ignores synthetic mouse).
4. Crash → `<DD>\KLHook.log` + `KLHook_N.dmp` (from `klhook/`, installed as `<DD>\dinput8.dll`)
   and the game's own `kl2_490_crash_*.mdmp` → `debug/triage.sh`, `debug/dump.py`, `debug/locate.py`.

## Open work
- Test the exact-schema build (installed 2026-10-08 ~19:40). The previous room→group build asserted at
  kl2+4c1625 (end-of-object '}' check): ZROOM-shaped objects typed as ZGROUP; the exact path fixes that.
- Continue the crash loop until M01 FA loads and plays.
- Sound banks (SND/WHD/WAV): convert DM banks, rewrite streamed offsets via PC_Def.str.map.json,
  expand to DD's 7 language records.
- Restore removed FA controllers (OnlineVehicleOnSpline, OnlineTriggerBox) using exe layouts.
- Settings preamble 32→33 entries (SSAO_Blur, SSAO_Strength).
- Package M02/M03/M06 FA into other F slots; FA game-rule glue (loot, escape, betrayal) checks.
- Character suits/masks: DM character templates → DD multiplayer character list.

## Roadmap for a rewrite (only after the port works)
Ghidra project of kl2.exe + kaneandlynch.exe, shared symbol/type database (classes, vtables,
property schemas dumped at runtime by KLHook), then an owned-asset engine reading original files
(hl2-rs model). Never redistribute game code or data.

## Working rules
- Verify before every install; commit each fix with a message saying what crashed and why.
- Don't guess silently: if a field mapping is a guess, say so in the code comment.
