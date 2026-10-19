# Hot Coffee II (DM01B, F03): kicked-in diner door + warehouse staircase to the attic

Plan only (2026-10-19, offline). Nothing here was built, run in the game, or committed.
Labels: READ = read in a script/doc, MEASURED = measured on files offline, GUESS = inference.
Sources: three research reports (original M01_A, live cars-only build 21c6ed49, AI climbing).

## Summary for the owner (plain English)
1. Stairs: the original stairwell and attic are real, walkable geometry and already sit in the converted map, so people can walk up them. The bots can too, because the game's own pathfinder handles ramps and stairs; nothing needs "climbing".
2. The catch: today the crew skips the stairs (a nav bridge at z 17340 leads straight from the office to the warehouse floor), and the attic is a dead end with no loot, so nobody goes up. The plan removes the shortcut, puts the loot upstairs, and adds a way back down.
3. Diner door: it will start shut and be kicked open (swing + glass/dust + shake) when the first heister reaches it. Bots trigger it the same way. Whether it looks like a real boot-kick is the open question (see risks).
4. Bots coming back down from the attic is the riskiest piece. Plan A is a CrewHop (bots are carried), Plan B is authored nav polygons. Both need a live test.
5. Campaign cars: yes, there is a path to bring them back without the one-shot explosion, but it needs one offline schema check first (section D).

## A. What is known (facts the plan rests on)

- READ/MEASURED (R3): M01_A nav mesh is NOT flat around the stairs. Stair group `M01A_Ins_WarehouseStaircase_101a` (ZROOM, entity 7160) has four sloped flights (polys 731: z17050 y60 to z16750 y260; 721: y260-460; 726: y460-660; 729: y660-860, each ~50 wide), landings 724/727 (y460) and 728/730/766 (y860). The attic (`WarehouseControlRm_301a`, y860, x1545..3034, z16565..18464, 30 polys: 728-730, 763-779, 968-974, 987-989) is edge-connected to the stairs. From START poly 933 an edge path of 75 polygons reaches poly 987. Max edge height step 120, no teleports. (R2 independently: 29 of 37 attic polys are in part 0.)
  The builder comment "mesh is flat" (tools/kl_fa_v2_hotcoffee.py ~l.983 area, and R1) is wrong for the stairs.
- MEASURED (R1): collision is real stepped geometry; multi-floor flood finds floors 60/441/459/460/559/659/821/860 around (2800,18400). Hero-only blockers do not change the reach.
- MEASURED (R2/R3): the attic is a dead end for walking: north catwalk polys 968-974/987-989 (z17323..17636) end near z18480; the y460 / y556-659 / y859(z19110+) / y963 floors are separate mesh islands (parts 28, 36-39) joined only by 21 one-way kind-2 drop links (981->993, 964->976/977, 977->980/978, 980->996/1000). Nothing links the attic catwalk to those islands. The y460 floor is cut from landing 724/727 by ~90 units of wall and door.
- MEASURED (R2): NAV_GAPS gap 2 = polys 762, 1101, 1102, 1038 at z17340, x2860..2930, office to main warehouse floor, skipping the stairs. Bots take the shortest path, so they will keep using it.
- MEASURED (R2): no loot, squad or station above y60. Loot = 6 cases at warehouse floor (x2900/3100/3300, z20150/20300, 150000) + 6 at diner y-15 (200000). Bots' loot window is 800 (3D) and 400 (height), so floor loot is never taken from the attic.
- READ (R3): vaulting (klfreeclimb.c, klclimb.c) is local-player only; ZFFActor has no vault action; kind-1 climb links never seen working (`kl_pf4.DD_LINK_KINDS=(2,)`). So "the AI can climb" must be satisfied by the pathfinder on stairs + CrewHop/drop, not by the vault. Proven live: bank DM03 bot walked a stairwell y355 to 1144 with no hop (R3, re/bank_campaign.md:2817); Retomoto/Vault bots on stair routes; CrewHop carries (klhop.c, Retomoto). Not proven: HC2 nav bridges ever ran live; hop upward by ~800.
- CONFLICT to settle in test: R1 says the diner front door is `PC0901_M01_Dor_White_Anim_01` at (4160,2,21895), path `Locations\M01_A\M01A_LOC_Outside.zip\M01A_Out_StripmallBack_01a\...` (ZSTDOBJ + MatPosAnim controller; static twin `..._Hinges_01`; facade `SO1101_M01_FacB_8m_Dor_01` (4300,0,21900)). R2 says the diner front is `PC0901_M01_Dor_Diner_Anim_01` group at (6160,0,23088), a ZGROUP with MatPosAnim + RelayMessageList, leaves Dor_attach / Dor_Win_Whole / Dor_Win_Shattered / Dor_Win_Remains, emitters Emitter_Glass_Smoke/Dust/Debris at (6110,123,23088), opened by a plain `Activate` message (re/campaign_fa_bank.md ~359-403). Two different doors. In the live build the crew's path/stage boxes (DONUT_BOX 4500,24250; flood stops at diner front x5897..6300, z23080..23100) point at R2's door. Build step 0 = confirm which one the route uses by looking at which gets the flood stop; GUESS: R2's group is "the diner door" for this plan, `Dor_White_Anim_01` (4160,21895) is the stripmall-back door of the warehouse side.

## B. Staircase to attic

What the owner gets: the crew leaves the garage/alley, enters the warehouse through the steel door, goes UP the stairs to the attic (y860) for the loot, and comes back down to the diner route. Matches the original, where the stair route is the player path (campaign marker `009_MC_MoveToWarehouseEntranceDoor`: PosLeftOfEntrance (1980,61,16422), PosUpstairs (2595,864,16680); TB_WarehouseEntrance (2095,262,16288), R1 READ).

Changes, in builder order (tools/kl_fa_v2_hotcoffee.py unless named):

1. Remove the shortcut. NAV_GAPS entry 2 (polys 762 to 1038, z17340, x2860..2930) is deleted or replaced by a gap from the stair foot (poly 716, x1545..1595, z17050..17255, y60) region to the alley/office side if the foot is not already in part 0 (MEASURED: it is in part 0 via 933 to 987 path, so likely no replacement needed). Re-run `nav_bridge_step`'s one-part check. Consequence: the office-to-floor door (`ColiObj_HeroOnly_BlockDoor`, DoorSteel HEADS_01 (3100,60,19957) / TAILS_01, in ROUTE_OPEN) can stay open for humans; bots will only path to the floor if some other route exists, see 3.
2. Doors on the stair chain must not hold a player or bot: `SI0103_M01_DoorSteel_A_02` (1883,62,17207), `..._TAILS_01` (1896,462,17207), `SI0103_M01_DoorSteelWin_A_TAILS_03` (1643,462,17298), `..._TAILS_02` (1643,860,17298), `DoorSteelWin_A_01` (2477,60,19848), and `ColiObj_playblocker_01` (1702,128,17025, inside the stairwell). Add the ones the walk crosses to ROUTE_OPEN (`route_open(sc)` ~l.195). R3 measured `doors` check: stair foot to attic (1570,60,16700) to (2900,860,17500) = "no closure". So only add if an offline check on the real build shows a closure; playblocker effect on bots = GUESS, test it.
3. Way down. Plan A (chosen first): a `[CrewHop.n]` in the level KLJoin.ini (keys From/Radius/Height/Wait/Places/To.1..8/WalkTo/GiveUp/Again, klhop.c l.60-100; each needs Enable=1). From = attic catwalk end near z18400, y860 (e.g. x2800, z18400); To.1..8 = 100 apart on the warehouse floor in front of the cases (x2800..3500, z19800..20100, y0..60); WalkTo=1; Again=0 (one carry per bot). Plan B (fallback if hop up/down is bad): author nav polygons with `tools/kl_nav_bridge.py` (sloped quads, corners within 2 of a plane) from the attic catwalk end to the y859 island (polys 964-967/990-993, z19110+), whose drop links already go 860 to 659 to 556 to 460, then add a final kind-2 link or a quad down to the floor with `kl_fa_bots.add_drop`. Why A first: only proven mechanism for upward/vertical bot carry on converted maps; B depends on 600 units of unmeasured gap (GUESS) and on bots using kind-2 chains of 8 m falls (fall damage unknown).
   Humans: the same catwalk must have a physical way down. MEASURED floors 441/459/460/559/659/821 exist at (2800,18400), but how they connect (R1 "a drop or climb from the 440/570 level") is unresolved. If humans have no way down, a second hop (Player=1, if klhop.c supports it, Stage/Player keys exist per R3) or an author-placed ladder/one-way drop is needed. GUESS.
4. Loot: move the warehouse case set to the attic. Candidate spots: catwalk polys 968-974 / 987-989, y860, x2800..3034, z17323..17636 (BOT_OPT stop). Keep the briefcase props (owner 2026-10-09). Move EnterLootArea (3100,60,20250), POI_TheLootArea (3100,160,20250) and FLOOR_BOX (3500,100,22500, half 3000,200,500) accordingly, or split: 3 cases upstairs, 3 on the floor so bots that come back still have loot. Size 700x150x300 trigger must be given a y of ~860 (height 150 matters, 400 loot window).
5. Warehouse squads (04_Squad_01/02/03, 03_OutBack, 05_Squad_07_StripmallBack, IntoWarehouseFRONT) all stand on the floor; leave most there so the floor still defends, add 1 squad to the attic landing so it is not a free loot walk.
6. Civilians: `civilians_step` uses the biggest mesh part, which now includes stairs and attic. Exclude y > 300 polys. GUESS: otherwise civilians appear upstairs.

Why bots need no "climb": ramp/stair quads up to 41 degrees are the norm in stock Dog Days (F04 18, F05 18, F07 41, L11 83 sloped polys; M01_A 6 at max 34 degrees, same in the built mesh). The owner's "vaulting now" is the hook's player vault; it never reaches a ZFFActor.

## C. Kicked diner door

What the owner gets: the diner front starts shut; when the first heister reaches it, it bursts open with glass/dust and a shake; the bots do the same.

Changes:
1. Keep the door group closed at the start: confirm `PC0901_M01_Dor_Diner_Anim_01` is not in ROUTE_OPEN or any blast list (MEASURED R2: it is not, and the live diner front is probably shut already). MainWallB (z17321) and the diner door are in `tools/kl_fa_v2_hc_route2.py` EXTRA_OPEN but that is opt-in and not live: do NOT enable that for the door (it opens at the blast, which is the opposite).
2. Add a TriggerBox just outside the front: x5900..6300, z22900..23080, y0..200 (GUESS size; the flood stopped at x5897..6300, z23080..23100), wired through a RelayMessageList to `Activate` on the door group (re/campaign_fa_bank.md ~359-403 shows the Activate wiring). Reuse the builder's existing trigger-box + relay pattern in `wire()` (~l.616-637). Do not reuse the speak box (4500,100,24250, half 3500): too wide, fires too early.
3. Fire the shake/dust: the group's own Emitter_Glass_Smoke/Dust/Debris (6110,123,23088) fire with Activate (MEASURED R2). Add the garage-blast style shake/sound entities (GARAGE_BLAST keys, `Specials!GarageWallExplosion!`, tools/kl_fa_vaultfx.py for vault fx patterns) to the same relay list.
4. Collision: the door's collision must be dropped or moved when it opens. `ColiObj` for the door is a GUESS; if the swing animation does not move it, add the door's collision node to a Deactivate message in the same relay list (the way `DeactivateGeom` is used for the blast).
5. Bots: they need a path through. Check that the diner front polys are in part 0 and the door gap is inside the mesh (not measured, R2). If not, add a gap with `nav_bridge_step`. Bots must not wait forever at a shut door: because the trigger fires on a heister entering the box (and the bots are heisters), they open it themselves; GUESS that a bot ignores the closed door until it collides, so also put a short hop or an AI-usable trigger. Test.
6. Real kick option (more faithful): copy Dog Days F07/F01's KickDoor + KickDoorMonitor + RelayList_Door0n wiring (field 7 of the monitor to the doors, field 6 to the relay list, 'AITrigger' to 'DoorOpened'; `tools/kl_fa_bots.py` lines 216/1081/2283-2286/2745 and `kl_fa_bots_civ.py` already handle KickDoor controllers; bots use KickDoorBehaviourRout/PosInfo, re/fa_gamemode.md ~211-214). Risk: KickDoor needs a KickDoor-class controller bound to the door; whether it works on a Dead Men MatPosAnim group is unknown (GUESS) and no hook-side kick exists. Netcode has KickDoorRequest (re/netcode.md:188) so it would replicate. Choose trigger box first (cheap), KickDoor as an upgrade.
7. Plain-Dor_White door at (4160,2,21895): optional second door in the same way (MatPosAnim 'Activate', R1 did not decode the keyframes, so swing angle and duration are unread). Do not do both in the first build.

## D. Campaign cars (optional)
Live build removes 45 leftover campaign cars (tools/kl_hc2_strip.py, cars-only 21c6ed49) because they exploded and one-shot the crew (L70/L71/L93/L102 vs L103/L104). None of the three reports found a way to keep them: no report read the car classes. Plan to get them back, offline first:
1. From `re/kl2.json` read the vehicle class's stored fields (ZHavokCar and the damage/explosion controllers) with `python tools/kl_rtp.py` data; look for health, explode-on-death or ZExplosion links. GUESS: a damage-threshold field set very high, or a missing explosion-effect reference, disables the blast.
2. Cheapest candidate: keep the car as a static prop by retyping to the stock static-car class used by `kl_gms.RETYPE` flattening (cars become unmovable and non-explosive), as the builder already does for other Havok classes. Counts L70/L71/L93/L102 are the build's lines, check them against kl_hc2_strip.py.
3. Verify with the explosion count (zero ZExplosion-triggering controllers on the 45) and run `verify_levels` and `debug/check.py`. Live test shoots a car.
Not promised until step 1 finds a field.

## E. Risks and unknowns
- Two candidate diner doors (section A): wrong choice = the kicked door is not on the route. GUESS-level pick, confirmed by the offline entity dump.
- MatPosAnim swing/keyframes unread; a trigger box does not make a "kick" animation (character clip), only a burst open.
- Door collision on open, trigger fire by bots, and nav through the door: all unmeasured.
- Hop down from y860 to the floor: unproven vertically; kind-2 drops of 8 m may kill or be refused (GUESS).
- Humans' way down from the attic is unresolved (R1 unresolved, R2 says dead end).
- `ColiObj_HeroOnly*`: whether bots count as heroes: GUESS.
- Stair jam: 50-wide flights with 8 bots (GUESS).
- Nav bridges of HC2 have never run live; hook climb crashed its first live run (R3).
- Kick-door ownership: online peers need identical builds; ADOPT 5 changes slot order (private_match.md).
- Report 1 said the nav mesh was flat and AI could not path up; Report 3 measured the contrary. This plan follows the measurement (R2 and R3 agree).

## F. Offline checks (before any live run)
1. `python tools/kl_route.py walk` and `doors` for stair foot (1570,60,16700) to attic (2900,860,17500) on the NEW build (R3 only ran them on the old one); also warehouse floor (3100,0,20250) to the attic catwalk end (two runs hung; use a smaller sample step).
2. `kl_pf4`/`kl_route.Mesh`: assert one part holds the stair foot, attic and diner front, and that no path from spawn to the floor exists except the stairs (shortcut gone).
3. `tools/kl_fa_bots.py check` and `hop_check` on the new hop (From/To inside the mesh or accepted by the hop code).
4. `verify_levels.py` problems: 0; `debug/check.py` pre-flight; `kl_netcheck.py` vs the old build to see slot-order change.
5. Entity dump of M01_A for the door groups and loot spots (coordinates in A) to confirm names.
Build only into `<DM>\KL_PortTools\build\hc2_attic_<name>`.

## G. Live tests (when the owner is away; `-o` launch hints already in use: `-dx10 -o DefaultScene=Locations/F03/F03_Main.gms -o AutoExit=120`; use the existing KLJoin/test-ini and the MPMap override, not new launch options)
1. Boot and bots path: start with bots only (no human), 120 s; expect them at the stair foot, then attic loot, by log of positions (KLHook.log). Check for stuck bots at the stair foot, door, playblocker.
2. Hop: log whether the CrewHop at the catwalk end fires, bots land on the floor, `GiveUp` not hit.
3. Door: walk a human to the box; expect the door open, emitters, no hang; then run it with bots only to see that a bot opens it.
4. Humans: confirm a way down from the attic (jump onto the 660/556 catwalk, or a second hop); check the free-climb and vault do not conflict.
5. Cars (D) only after the schema step.
Pause per memory when the owner is playing; install into the F03 test slot only, never touch KL_PortBackup.
