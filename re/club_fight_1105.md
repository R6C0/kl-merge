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

## Kick doors, doors variant (2026-11-06) - STAGED, NOT INSTALLED, NEVER RUN LIVE
Tool `tools/kl_club_doors_1106.py stage` (offline, ~50 s). Input = the chain stage zip c8dd18ee (`C:\kl_build_1024\lastcall_chain_1105\stage`).
Stage `C:\kl_build_1024\lastcall_chain_doors_1106\stage` (INSTEAD of the chain stage; same live files, install only one): F01_Main.zip 803a29c8, bots.zip 22a036e0,
bots.base.md5 448e426f, LS.SND b6fdd4c0, KLJoin.ini cfdf1b0e, KLGuns.ini 52f075e9. install.py pinned to live e9fab045 / 7a1024ed / fe3373c8 / 3b21242c / ea0446c1 / d7dbb7cc,
backups `.before-1106doors`, `--undo`, `--dry`; rehearsed on a scratch copy: install md5s as staged, undo byte-identical.

How stock does it: Dog Days' F03 has KickableDoor groups (stock leaf = type-4 key-framed Havok body + KickDoor controller + ArrowFront/Back + PathBlocker); its bot squads open them with a
KickDoorBehaviourRout step. kl_interact_graft clones that group; kl_bots_kick_1025 adds the same step to the heister squads (DM01/DM02/DM03A did the same, 10-25). No AI kicks a door otherwise.
Last Call has no static leaf (door_hosts finds 0), so all four doors are virtual (empty doorway).

Where (all on the nav route loot room -> roof pad, measured on the chain zip; loot floor is y 341, the stacks stand 70 cm above it):
- KL_Door_1 daughter door B, x 1500, hinge (1500,360,3433), leaf along -z. KL_Door_2 daughter door A, x 2500, same z. The mesh has two wall points 140 cm apart at z 3293 / 3433 on both
  (nav.clearance ~1), the route crosses at z 3360: a real 140 cm opening. The animated door groups DaughterRoomDoorB_01 / A_02 (group origin z 3313) have their leaves sunk (-1500 y) by the club build.
  The 3 `Fight!Loot` guards stand between the two: a kick door each side.
- KL_Door_3 storage Firedoor_03 (-3190,860,2306), KL_Door_4 roof Firedoor_02 (-3790,860,3287): both leaves sunk by the club build; the mesh is a 60 cm strip that starts right there. Leaf along x.
- NOT used: the stairs neck (19,168,254) of `kl_club_fight_1105.py --doors`. At 20 cm resolution there is no doorway shape there (a ~80 cm hole between blocks, gap 213-237 wide in neck_targets).
  Also its orientation in stage_doors looks wrong: neck_targets' u is the direction ALONG the jamb walls (travel), stage_doors puts the leaf along u, i.e. along the passage. Do not use `--doors` as is.
Width: one scale per map (median of the hosts), 140 x 240 (stock 120 x 220), scale x 1.1667, y 1.0909. 140 = the mesh gap of the daughter doors; the fire doors are probably narrower, a 140 leaf just overlaps the jambs.

What changed: +4 KL_Door groups (22 nodes each), 1 extinguisher (ext=0 still places one: harmless prop at (-1217,225,1963)), +47 KickDoorBehaviourRout nodes + 47 PosInfo kids, 41 NEXT entries redirected in Squad#02..#08
(the legs to_loot, out_floor1n / out_floor2 / out_walkway, out_car now kick Door 1/2 on the way in and out, Doors 3+4 on the way up to the roof), 94 entities added (20470 -> 20673 nodes with the doors),
.prm 54305 -> 54378 chunks (KLJoin.ini [FedBody] and KLGuns.ini [Guns] Entries set to 54378 by patching the one Entries= line; kl_fa_fedbody check PASS, the body/rifle lines untouched), +1388 slot ids renumbered.
dmlines --fed and gunpics NOT re-run: no .LOC or picture touched (gunpics is not idempotent). Census (actors/squads 130/73) unchanged: no actor added; the 15 `Fight!` tops are all there.

Checks (offline): debug/check_passes.py PASS A, B, C1-C3 on both F01_Main.zip and F01_Main.bots.zip; tools/kl_entries_check.py on a scratch tree: stale 0, botgate OK; tools/klt_audit.py Fed/AllDead/Shoot yes;
kl_fa_fedbody check PASS; kl_club_budget unchanged (382 s of 360 s, slack -22 s, pre-existing); kl_club_heli_1105 check DONE; kl_club_life_1105 check: 40 civs, 9 looks, 12 women/female voices OK, only its
'.buf changed' line fails (it compares with the pre-chain input; the chain stage fails the same way); tools/kl_tests.py: PASS 79, 0 fail, 5 skip.

GUESSES / risks (a live look is needed):
- The doors' look, kick trigger, PathBlocker effect and the hinge side are as unproven as on DM01/DM02. The leaf is cloned for a 120 x 220 door and scaled.
- ENEMY squads (Wave_*, Roof_*, Fight!*) have no kick step: a shut door with a PathBlocker may hold a guard who has to pass it (the F2/roof groups walking down through Firedoor_02 / 03, the Loot guards stay put).
  If guards stall at the fire doors, undo and build with `DOORS` cut to B01 + A02 (a one-line edit of the DOORS tuple in the tool).
- The heister bots' kick step is the cloned F03 one (Defend legs only; a leg that already ends inside a door, or a RunToCover step, is skipped as the 10-25 pass does).
- Door positions come from the nav, which is eroded by the actor radius: the true jamb distance is a few cm to 30 cm larger than the mesh gap.
- Owner-map post-pass order held: .LOC untouched -> fed/gunpics skipped, Entries regenerated after the last .prm change, check_passes, klt_audit.
- pd2guns also pins the live DM05A: install order is chain (or this variant) first, then the pd2guns rebase.
