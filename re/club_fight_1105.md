# Last Call (DM05A) fight variety pass, 2026-11-05

Tool: `tools/kl_club_fight_1105.py stage [--src zip] [--out dir] [--no-new] [--doors] [--force]`. Offline; stage in
`C:\kl_build_1024\lastcall_fight_1105\stage` (F01_Main.zip, install.py, build_report.json). Input copy in `...\in\`.
Input pinned to live md5 e9fab0453a5260369c2fddd01bed5534 (`--force` to chain over another pass).
Output md5 4f05020c469ded207bc0f24c578adf97. install.py: refuses while kl2.exe runs, md5-pinned, backup
`F01_Main.zip.before-1105fight` (never overwritten), `--undo`.

## What it does (owner feedback 2026-11-05)
Census 116/68 -> 130/73 (+14 actors, +5 squads; the 147/110 build failed on memory, 129/74 and 116/68 are proven).
New tops (all `Fight!*`, found by name; the Go timers are appended to the AIMonitor START list):
- Rush (3 SMG): spawn on the front lane (-65,20,-1307), released at 20 s, Defend eDMS_Run into the foyer, 5 s, then run to cover boxes. (front assault runs in and takes cover)
- F2_Hold (3 rifles, 45 s): hold ahead of the stairs on floor 2, SquadModifier tight + UseCovers.
- F2_Flank (3 SMG, 70 s): spawn at the west end of floor 2 (-3146,460,-299), RandomTrigger of two lanes, run back along the route.
- F2_Shot (2 Hawk shotguns, 90 s): eUnleashed, run to the stairs top, loose.
- Loot (3, in the world from load): corridor between the two daughter-room doors (2300,362,3330), shotgun + 2 rifles, tight + covers.
Edits of existing squads (no actor added; the Defend's field 7 gets a chain in `Fight!W1..6`, `Fight!Roof1..3`):
Wave_1/6 hold tight + covers, Wave_2/4 run to cover boxes, Wave_3 push deeper (loose), Wave_5 flank (RandomTrigger of two lanes),
Roof_R1 hold, Roof_R2 push forward after 60 s, Roof_R3 side-step after 75 s.
Weapons come from cloning an existing Enemy actor that carries the weapon (no field edit).

## Members changed
F01_Main.zip: .prp .gms .buf .oct .rmi .rmc .prm (the .prm only re-points 1771 model roots; chunk count stays 54305, so KLJoin.ini/KLGuns.ini Entries stay valid).
Nothing else (no LOC/WAV/WHD/bots.zip). Chains over kl_club_life_1105 if that pass is run first with `--force` (the md5 pin is the only coupling; everything is found by name).

## Checks run (all offline)
Self-checks in the tool (join reproduces .prp, scene reproduces .gms/.buf, octree round-trip, room sets unchanged, no new dangling refs, seal/reverify, read-back).
debug/check_passes.py: PASS A, B, C1-C3. tools/klt_audit.py: Fed/AllDead/Shoot yes. kl_club_budget: unchanged (382 s of 360 s, slack -22 s, no gate added; pre-existing).
dmlines --fed and gunpics are not re-run: this pass touches no .LOC/picture; running gunpics again is not idempotent.

## Doors
DM05A has no static door leaves (door_hosts finds 0); the fire doors are animated, closed sliding doors on the route; the only mesh doorway near the
route is a neck at the stairs. `--doors` stages `stage/doors/F01_Main.zip` (kl_interact_graft virtual doorway, ext=0, one door near (19,168,254)); it builds and passes check_passes,
but is UNTESTED and adds .prm chunks (54305 -> 54378), so KLJoin.ini/KLGuns.ini Entries must be regenerated (kl_fa_fedbody) before installing it. Not installed by default.

## GUESSES (need a live test)
- Defend field 4 eDMS_Run makes the squad run to its posts; field 7 fires on arrival (proven in the bot squads, not for OldWaves).
- Cover place = a CoverBox position snapped to the walk mesh (clearance 60, relaxed to 40/25).
- SquadModifier field 15 eCOM_UseCovers, field 9 eDM_Tight/Loose, vision left NotSet.
- ZSquadScript field 0 eUnleashed for rushers.
- The street (y 20) is a separate walk-mesh part from the building; the Rush squad spawns on the street part. Assumed the engine path-finds across (the route does).
- Wave posts near the walls: Roof_R2/R3 targets are polygon-middle fallbacks on the roof part (no strip at -900 cm).
Test: watch rounds 1-2 for the Rush squad entering the foyer at ~20 s, 2nd-floor groups at 45/70/90 s, the loot-corridor guards, no crash at load (memory: 130/73).
