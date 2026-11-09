# Vehicle routes audit (2026-11-08, offline)

Owner: "hot coffee 2 the car just goes through a building ... make sure all vehicles actually come from a logic place and leave to a logical place
where people can shoot it". Tool: `tools/kl_vehroutes_1108.py` (`--check-only --summary <zip>`): the van's key-framed drive (main drive + crash
keys) against RENDER triangles with a 130 hull (heights 73/163/263 over the first key; flat ground dropped). Older `kl_vanlane_1025.py` checks
collision only, so it reported DM01B "0 hits" while the van drove into a wall. Only the F07 key-framed `V_Van_00` is measured; choppers and
traffic cars are not (no tool yet).

## DM01B Hot Coffee II (slot F03): PROVEN bug, fix staged
The van's alley (donut shop south, 125-high planter strip north, Donut Factory west = dead end, open east) was left along z=30800 straight west;
the Factory's east wall is at x=-496, so keys 339..530 (drive-away and crash pieces down to x=-863) pass through it (gap 0).
Fix: the van BACKS OUT along its own arrival lane (drive-away keys 172..390 mirrored about the stop x=1660, end x=4720; rotation untouched);
crash keys clamped to x>=-350. After the fix: 0 close samples (live: 83). Stage `C:\kl_build_1024\vehroutes_1108\DM01B` (see its install.py).
GUESS: reversing out reads as logical. The alternatives are a forward exit across the planter strip onto the main street z~31930 (where the Dead Men
van really drives, from the west, stopping at x~4458; a 125 curb is crossed) or a U-turn (alley 575 wide, too tight). Arrival still pops at x=5360
(open east end of the alley, not seen from the start).

## Table (live zips as of 08 Nov; result of the render check)
| map | vehicle | from -> to | clips? | shootable | action |
|---|---|---|---|---|---|
| DM01 | van F07 | (8406,16687) -> (1522,24942) | gap 1..17 at the end into `SO1001_Fence_A_5m_Attach` (an AnimGroup fence = breaks open, Dead Men design) | van HP data (vans_1025) | none (by design) |
| DM01B | van F07 | (5360,30800) -> west | WALL: Donut Factory | yes | fixed in stage |
| DM02 | van F07 | (1116,-12896) -> (-4947,-13486) | 0 | yes | none (cop cars' paths cross the lane early, not at rest) |
| DM03 | van F07 | (-2555,558) -> (10290,-1103) | first 70 keys (arrival) brush `Traffic!Cars` Mpv / RamTruck / SuperTruck / CementMixer (gap 1..88) | yes | REPORT ONLY (another job stages DM03): the traffic cars stand ON the arrival lane at x -180..50; move them off the lane (or off at the van's arrival) |
| DM03A | van F07 | (-3248,-11859) -> (8000,-11173) | 0 | yes | none |
| DM05A | heli (Last Call roof) | d0's ROUTE_2H | d0 proved hull clearance | boards, not a hit target | d0 owns |
| DM06 | heli | not measured | - | - | not measured |
| DM06B | van F07 + 7 traffic cars (d0) | (-6264,-5459) -> (781,-8292) | 1005 samples within 53..58 of freeway spiral / junction rails (not pierced; road is tight) | yes | d0 owns, no change |
| DM07 | van F07 | (-6000,10400) -> (1800,10400) | PIERCES a chain-link fence at x~-4600 (z 9993..10798) during arrival and a 44 m concrete wall (x 1108/1147, z 8300..12700, y 457..807) near the END of the drive-away (keys 358..366) | yes | NEEDS A FIX, not staged (doors_sfx_1108 stages DM07): shorten the drive-away to stop short of x~1000 (end key) or turn it along the wall; arrival: gate gap in the fence or start east of x=-4500 |
| DM09 (Retomoto) | vans 01/02/03 | parked under the road (y -60040) by design, 02/03 drive after the lift | inter-van overlaps only (path gaps -330..-356 between vans 01/02/03 at the same x,z at different times) | vans 02/03 no FakeTarget on purpose | none |
| DM11B | heli (Hasta) | not measured | - | - | other job stages DM11B |
| DD10 Flat Raid | van F07 | (6280,1100) -> (11800,1100) | check failed (mesh read error in kl_fa_loot, DD10 stock geometry) | hook-side [VanBlow] | report only |
| DD04 | stock | - | stock van, 0 close | - | stock |
| DD01-03 | stock | - | no `V_Van_00` (other vehicle classes), not measured | - | stock, report only |
| DD05-09 | stock | - | not measured in this pass | - | stock, report only |

## What a live bench of the DM01B stage must check
1. Round start: van arrives from the east along the alley, stops at the escape box (unchanged), boards (crew aboard = hook shield).
2. After boarding the van reverses east along z 30800 (nose west) until it leaves the alley at x~4720; no wall, no pop; frames smooth (the mirrored
   speed profile accelerates to ~150/key; check it does not look absurd).
3. An EMPTY van that is shot to 0 (crash keys) lands no deeper west than x=-350 (not in the Donut Factory).
4. Cops/AI can still see and shoot it all the way (FakeTarget unchanged).

## 2026-11-08 DM01B literal version (street stage, staged only, NOT installed)
Tool `tools/kl_vehroutes_street_1108.py`; stage `C:\kl_build_1024\vehroutes_1108\DM01B_street` (zip dcae5e6e, bots 02cf84fc, base 0377d541; pinned to live 74d37233 / 73583df1 / c3535e34;
only ONE of the two DM01B stages can be installed, the other then refuses). Dead Men source (M01A_Main.zip `05_EscapeVehicle` spline): (-4998,31412) -> (-4322,31981) -> (-1668,31933) -> (4458,31907).
Van drive = old drive turned rigidly 180 degrees about the new stop (arrives from the west along z 31907, leaves east to x 7518, street ends ~7600); crash keys clamped z>=31907 (planter bushes).
Render check: 0 close samples. 29 nodes moved (van, blocker, boarding box, camera triggers/cams, exit/POI triggers, jump point, ally box, 14 merc Pos).
NOT REACHABLE ON FOOT as staged: bounded collision walk alley -> stop is free only after opening exactly two objects: `InvisibleBlocker_06` (ref 22709) and the planter strip
`SO1103_M01_DonutShop_PlantD_01` (ref 23079, 125 high, x 2000..8000). Nav mesh also has the street only as a 5-polygon island (part 17), no link to the alley. Needs: planter gap
(render + collision), blocker removal, a nav link. Alternative that works today: the reverse-out stage.

## 2026-11-08 ALL-VEHICLE AUDIT (report only, nothing staged, nothing installed)
Tool `tools/kl_vehaudit_1108.py` (tests `tools/kl_vehaudit_1108_test.py`, 5 pure checks), read-only on each map's own zip. Measured: key-framed roots (escape vans, cop-car arrivals, parked-truck anims),
ZHeli splines (Incomming / Escaping / Evacuate / ApproachEvacPoint), ZTrafficFlow lanes (+ "Planes!" sky traffic), AI ZHavokCar routes. Run on the 12 expansion maps + 9 stock DD maps (DD10 too: `kl_fa_loot.Assets.geometry`
now tolerates DD10's dead chunk, 2.23M tris read; DD10 stays partly stubbed (slim build), treat it as indicative).
Method: route densified (120 car / 300 heli+traffic), body = 3 heights x 3 lateral lines (heli 3 heights, radius 800) tested two-sided against RENDER triangles in a corridor (linear AND Catmull-Rom, the engine spline
kind is unknown); a wall-only TIGHT gap check; "seen" = share of samples with line of sight to any of up to ~63 stand-in viewers (ZSpawnPoint, eye +170, radius 5000). Start/end states: HIDDEN (viewers near, none see it),
no viewer within 6000 (unwatchable remote spot), OFF-MAP (no drawn surface within 2500, the sky/void), SEEN (pop-in in view).
Calibration: stock DD vans/choppers also touch tunnel sections, fog planes, lamp volumes, smoke columns, wires (DD05 vans live inside TunnelSect, DD02 bridge cars in "Tunnel_GHOST" helper meshes, DD04 vans through
EscapeShops_End, DD10 van past a pillar/garage). So only SOLID structures (wall, fence, building, factory, shop, garage, tunnel...) count; fog/light/foliage/vehicle hits are listed in the JSON only.
Raw output: scratchpad all.json + two.json (per vehicle: start/end state, stop, pierce {owner: key range, n, point}, tight, seen_pct).

### Real clips (solid pierce of an expansion map), with fix
| map | vehicle | pierces | fix (owner / chain) |
|---|---|---|---|
| DM01B | escape van V_Van_00 | SO1104_M01_DonutFactory_01 keys 343..528 x105 at (-457,-13,30800) (known, 410a8b0b) | already staged: vehroutes_1108 DM01B stages (reverse-out / street). Re-run this audit on the chosen stage: pierce list must be empty |
| DM07 | escape van | SO0300_M07_ConcreteWall_1x44 (x2) keys 360..364 at x 1064..1099, y 391, z 10400; Chainlink_Fence_4m_01 + _11 keys 50..55 at (-4644,402,10400) | doors_sfx_1108 chain. Drive-away: cut the key list at 359 (van x about 930), or shift its z by the wall gap. Fence: it starts at key 50..55 = the arrival, so delete the two fence objects (4m_01, 4m_11) from the .prp or start the van from key 56 |
| DM01 | escape van | SO1001_Fence_A_5m_Attach / _01 / FenceDor_A_1m_01 keys 359..544 x88 at (1572,2,23545) (185 keys = the whole end; stop (1523,2,24923)) | doors_sfx_1108 chain. Earlier note called this "by design" (AnimGroup fence); verify the fence AnimGroup plays a break/open before the van arrives, else cut the keys at 358 or open FenceDor_A_1m_01 |
| DM09 | escape van 01 | Z_CityScape_02 keys 400..562 x212 at (-1886,1,10392), SO0301_SkyC1_22 keys 92..394, Street_Wide_Geom_a_01 keys 489..519, SO0301_BaseA_08 key 319 | doors_sfx_1108 chain. CityScape/SkyC1 are probably backdrop shells with no collision (check the .HVK); if they are drawn solids, move the 3 pieces out of the lane (z 10164..10392, y about 0) |
| DM05A | Escaping heli | starts INSIDE SO0004_M05_BuildingF_01 + Building_H_03 at (7058,2271,3466), keys 0..3, start HIDDEN | d0 (DM05A). Add 3 keys before it: start it above the roof (y >= 3000) or at its ApproachEvac end, and keep the leaving leg at x 8799 y 6200 (ends no viewer: ok) |
| DM03 | escape van | parked traffic cars (Ground_USA_CementMixer/GetawayVan/RamTruck/SuperTruck, Traffic!Cars!) keys 57..66 at (-62..12,105..108,71..78) | dm03cops_1108 stage. These are the TrafficFlow template cars sitting on the arrival lane (earlier finding): move the 4 templates 400+ off the lane or hide them; van start is HIDDEN (good), end seen by the only viewer |
| DM03 | DeliveryCars!Deliverycar_01 route | same 4 template cars keys 62..66 at (-10169..-10409,710,-9250..-9669) | dm03cops_1108 stage, same fix |
| DM06 | CopCar01..03 arrival | only Ground_Base / Ground_Path / Tree_Thin keys 101..174 (ground tiles + a tree, cars sit ON the ground: not a wall) | none needed; tree Thin_D_12 at (-2381,190,-7875): remove if the car clips it |

No solid pierce: DM02, DM03A, DM06B (d0 van, SEEN both ends), DM11B (cops and choppers), every DM01B/DM01/DM03 cop car, all traffic lanes.

### Appears / leaves (logical?)
- GOOD (start HIDDEN or off-screen, ends in view): DM01B van (start hidden, end seen by 1 of 10), DM01B cop cars (start unwatchable, end seen), DM07 van, DM09 van 01, DM03 van, DM01 van, DM05A Incomming heli (OFF-MAP sky, ends seen), DM11B Incomming (OFF-MAP) and Escaping (leaves OFF-MAP), DM06 Escaping/Evacuate (leave OFF-MAP).
- POP-IN risk (start SEEN by viewers): DM03A van (start (-3248,702,-11859) seen by 10 of 10), DM03 DeliveryCar (start seen by 10 of 10), DM06B van (start AND end seen 10/10, d0), DM02 CopCar01 (start (1015,0,-8019) seen), DM06 cop cars (starts seen), DM11B cop cars (starts seen by 1/10, 4/10, 5/5). Fix: start these 150..400 earlier along their own path inside a no-viewer pocket, or add a 0.5 s fade/smoke; for cop cars check whether the engine activates KL_Cars at the key time (unproven, no live run).
- Traffic lanes: every lane is 0% seen and starts/ends no-viewer or OFF-MAP (DM07 Center_SideStreet lanes OFF-MAP). They are far background loops; players cannot shoot them. If the owner wants shootable traffic, the lane would have to be moved within SEE_R of the play space (not done).
- DM09 vans 02/03 stop at y -60039 (parked 60 km under the map = the engine's hide spot), both ends OFF-MAP: unused clones, never drawn. Same lengths (13811/15246) as DD07's vans 02/03, so they are copied stock tracks.
- Shootable: escape vans and cop cars are inside play space (seen_pct 7..100%). Weak spots: DM01 van 7% seen, DM03 19%, DM09 van 01 13%, DM03A cop-free: players barely see these vans before they go.

### Caveats (guesses)
Viewers = ZSpawnPoint standing in for players (guess); linear + Catmull both tested (engine spline kind unknown); foliage and glass count as blockers in the raw JSON but not in the SOLID table; DD10 geometry partly stubbed;
cop-car KL_Cars activation unproven; hull sizes (car lines +-100, heli radius 800) are estimates, so keys at a range edge (1..2 keys) are noise. No live run was made.

### Review addendum (2026-11-08, re-run of DM07 / DM01B / DD10 reproduced the numbers above)
Omitted from the real-clips table above: DD10 Flat Raid (d0) escape van V_Van_00 PIERCES SO0010_L05_Pillar_A_02 keys 90..395 x87 at (7890,11,1100), SO0700_ALL_BigFence_A_02 key 94 at (7962,10,1100),
PC1201_L05_Exit_01 keys 271..277 at (9391,2,1100) and Plane01 keys 58..65 (likely a helper plane, not solid); seen 21%, start HIDDEN, end seen by 2 of 10. DD10 geometry is partly stubbed, so the pillar
may be real stock behaviour (DD04/DD10 stock vans also pass such pieces); owner d0, check the pillar and fence against the stock zip before cutting keys. Also stale above: the first table's rows
"DD10 check failed", "DM06 / DM11B not measured" are superseded by the audit section (DM06 and DM11B measured, no solid pierce).

## DM01B street2 (2026-11-08, staged, not installed)
Fixes the street stage's unreachable stop. tools/kl_vehroutes_street2_1108.py: planter 23079 + blocker 22709 sunk -160 and collision cut, three appended nav bridges (alley 321 -> throat -> street 206; north quad off 210), bots zip re-derived. Stage C:/kl_build_1024/vehroutes_1108/DM01B_street2 (zip 1d68eade, bots d84ed410, base fcac2fd2). Gap = the whole planter length (x 2000..8000), flattened to the tarmac; bush rows and the west planter stay. Walk proofs free with nothing opened; flood contained by the walls at z~32550; cameras clear; no LevelBound near the street.

## DM07 gate + reverse out, DM09 no fix needed (2026-11-08, DM07 staged NOT installed)
Tool tools/kl_vehroutes_dm07_1108.py, stage C:/kl_build_1024/vehroutes_1108/DM07 (zip fef33e0f, bots bd95e0ad, base ce4842bf; pinned live e0a9e326 / 7e897565 / f6259849). Undo rehearsed byte-exact in scratch (dry, install, undo).
DM07 was: arrives through two fence panels (4m_01 / 4m_11, keys 50..55), leaves east through ConcreteWall_1x44_02/_03 (keys 360..364). Fix: panels hidden (gms flag 0x400) = a gate; drive-away keys 180..390 re-laid straight WEST along the arrival lane back to x=-6000 (reverse out, nose stays east, rotation keys untouched, old speed profile kept, height from the arrival keys); crash pieces clamped to x<=940 (Pillar_F_06 at 1089). A forward U-turn was tried and dropped: the yard floor is mud heaps (388..459 high), the loop ran tight over them.
Audit: kl_vehaudit_1108 on the stage: 0 close samples, 0 solid pierces (before: wall x2, fence x2, pillar, mud). Seen 87 % before, 100 % after (the open gate removes the fence blocker, so partly an audit artefact; the van is in the open yard at the stop).
GUESS: flag 0x400 hides in game; the hidden panels' HVK collision staying is harmless; a reversing exit reads as logical (DM01B precedent). Not benched (owner playing).
DM09 escape van 01: NO FIX NEEDED. CityScape / SkyC1 / Street_Wide are backdrop shells (no collision, not part of the walkable map; the van's lane runs beside them and is not seen inside them). Vans 02/03 are parked 60 km below the map, left alone. Evidence is structural (entity classes, no HVK, route clearance), not a render of the game.
Bench: van arrives through the gap, stops, boards as before, reverses out through the gap and stays shootable; shot-dead van; hidden panels not drawn.

## DM07 re-stage 2026-11-08 18:00 (review of the gate stage; staged, NOT installed)
Review points and what was done (tools/kl_vehroutes_dm07_1108.py, stage C:/kl_build_1024/vehroutes_1108/DM07, zip f35e4133, bots 1f514d51, base 08478b6e, pinned live e0a9e326 / 7e897565 / f6259849):
1. Hiding the fence panels with 0x400: research verdict = render only for static (type 1) placements, so the panels KEEP collision and the gap stays closed for players; kl_route's walk flood from the stop (it counts hidden collision) reaches 0 cells in the pocket. The van is key-framed (type 4) and moved by its keys (GUESS: not stopped by static collision; the old van drove through the same panels and the wall). KillBox at (-5832,490,10400) is the fallback.
2. Start / end: the pocket west of the fence (x -9760 .. -4600, z ~8200 .. 12200; closed by SO0300_M07_ConcreteWall_2x88_04 at x=-9759) has no walkable floor, so it is the one place where nobody can stand. The van now waits and ends at (-9300, 10400). Arrival keys stretched (x linear -6000..-2700 onto -9300..-2700; stop untouched), drive-away re-laid from the stop to -9300 with the old speed profile (peak 30 -> 61 and 37 -> 57 units per frame, ~66 km/h: GUESS, units cm). Heights = render floor under the lane + 2 (median of the old keys over the floor). No yaw snap on the way (rotation keys stay 90.9 deg through the exit); the 91 -> 35 deg turn is the crash keys (frame 500, wreck tumbling), unchanged.
3. Crash pieces: x clamped to <= 940 (25 keys); 115 keys that sat below the render floor (stock F07 wreck path, up to 20 low) lifted to floor + 3 (GUESS: key origin = wheel level). All stay on the flat lane strip (flood floor 389..402), none on a mud heap.
Proofs (tool `check`): hull check 0 close samples; flood from the stop 0 cells in the pocket; viewers = EVERY reachable floor cell (one per 400 block, 3861 of them; eye +170): the start is seen by 29 of 639 within 7000 (all stand in the 800 wide corridor of the gate, z 9990..10810), 56 if the chain link is see-through, 195 of 1121 for the stop itself. kl_vehaudit_1108 on the stage (scratch maps dir): 0 pierces, start and end 'no viewer within 6000' (spawn points). install.py docstring now names DM07 and the backup tag .before-vehroutes1108dm07; refuses on a running kl2.exe; --undo rehearsed byte-exact in scratch. The kit's free-space rule (files + 1 GB on the game drive) refuses today (C: ~0.7 GB): free space or pass --min-free-mb.


### DM07 review closed 2026-11-08 (stage unchanged: zip f35e4133, bots 1f514d51, base 08478b6e; live pins e0a9e326 / 7e897565 / f6259849 re-verified)
Research verdict applied: gms flag 0x400 on STATIC (type 1) placements hides the render only and keeps Havok collision (static reading of kl2.exe), so the two hidden fence panels still keep players in; the 8 m gap is a visual gate for the van only. The van is key-framed (type 4); that a static body does not stop it is a GUESS (the stock van already drove through these panels and the wall). KillBox (-5832,490,10400) stays as fallback. kl_dm02fix_1108's "0x400 also drops collision" guess is the unsupported one (cut the REFs from the .HVK instead).
Re-run: check = 0 close samples, flood from the stop 0 cells in the pocket; viewers = every reachable floor cell (3861): start/end (-9300,402,10400) seen by 29 of 639 within 7000 (all in the 800 wide gate corridor), stop 195 of 1121. kl_vehaudit_1108 on the stage: 0 pierces, start and end "no viewer within 6000"; only "tight" is Pillar_F_08 at the gate (gap 111 vs the 130 estimate, same lane as the stock arrival, noise). No yaw snap on the way. Kit rehearsed in scratch: --dry, install, --undo --dry, undo = all three md5s back byte-exact.

## DM01B street2 re-stage 2026-11-08 17:20: the van comes from, and leaves to, places nobody can see or stand (INSTALLED 11-09 02:29; its turns are SUPERSEDED by the street3 section at the end of this file)
SUPERSEDED (turns only): arc radii 407 / 400 at 108..116 units per key were far too tight (lateral accel ~30 u/frame^2); street3 replaces the drive keys. The rest of this section (planter, nav, pockets, proofs) still holds. Live after install: zip 778b075c / bots dccc9250 / base 6616525a (the pins "74d37233 / 73583df1 / c3535e34" below are the pre-install files).
Tool tools/kl_vehroutes_street2_1108.py (kit script template tools/kl_vehroutes_street2_install_tmpl.py), stage C:/kl_build_1024/vehroutes_1108/DM01B_street2: zip 778b075c, bots dccc9250, base 6616525a; pinned live 74d37233 / 73583df1 / c3535e34.
Was: the van popped in at (758,31907) and vanished at (7518,31907), inside the walkable street. Now (stock mechanism = key positions; no 0x400 hide, which is render-only and unproven for key-framed bodies):
- WAIT pocket west: (-8000,30500), the side gap behind the west block, yaw 0; straight north to z 31500, quarter turn (r 407) onto the street at x -7600, then east to the stop (4454,31907), arrival keys 0..155.
- END pocket east: street left at x 17000, quarter turn south (r 400), ends (17400,30400), yaw 180. Old speed profile kept, per-key step capped at 116 (stock vans 60..118; arrival averages ~83/key, GUESS: reads fine).
- Proofs (tool `check`): hull check 0 close samples; kl_vehaudit_1108 on the stage: pierce {} and tight {} (its "end SEEN by 1 of 1" is its own stop heuristic landing on the end key, not a player);
  viewshed from EVERY reachable floor block (385 viewers, eye +170, point +100): start and end seen by 0 at 7000 AND at 20000 range, solid and soft (bush/fence/glass see-through) occluder sets; the pockets are outside the walkable flood (x -410..10590).
  The van is first seen at x ~ -6700 (7 viewers) driving out from behind the corner, 23..200 viewers on the street = shootable.
- Planter strip: drawn ground exists under all 80 samples of the sunk strip (Tarmac_01..04 / Grit_01 at y -15, planter top now -35): nothing to change, sunk whole.
- .oct/.rmi: the van's 21 .oct items (room 0 slot 3) are in the van's local space around the origin and the tree spans +-179000, so no bound needs updating; LevelBound boxes none near the street.
- Disk: install need = backups (3 live files, 435 MB) + the largest .tmp (206 MB) + --min-free-mb. Default and INSTALL bat: 300 (about 940 MB total, 300 MB headroom). Rehearsed in scratch on hard links: refusal on running kl2.exe, --dry, install, re-install refused, --undo byte-exact.
GUESSES: key-framed van passes the invisible x -400 / 10590 street end walls (as every stock van passes collision); arrival speed; nobody stands in the pockets besides the flood (no jump/glitch spots known).
Not benched (owner playing). Bench: van appears from the west end, stops, boards, drives away east, never seen popping in; shot-dead van lands on the street.

## DM01B street3 2026-11-09: wider turns, slower arcs (follow-up of the live street2 route; staged, NOT installed)
Tool tools/kl_vehroutes_street3_1108.py (+ _test.py), stage C:/kl_build_1024/vehroutes_1108/DM01B_street3, pinned on the live street2 files 778b075c / dccc9250 / 6616525a -> zip 6466fd90, bots e08e1525, base 2cd9c0e0. Backup tag .before-vehroutes1108street3 (street2's backups sit beside it, never touched). Only the van's drive keys (.gms head, in the .buf) change; .prp, .HVK, nav, key 0, key count, frame tables, height and crash keys are byte-identical (audited by `check`).
- Arrival arc R 407 -> 1407 (the most the pocket allows: the arc starts at the pocket (-8000,30500) and must meet the lane z 31907, so R = 31907 - 30500). Departure R 400 -> 1507: the lane is left at x 15893, arc ends at the old end (17400,30400).
- Speeds. The key budgets are fixed (arrival keys 0..155, departure 155..390; Activate_Enter frame 50 plays key 1, one key per frame while moving, so 155 steps for 13257 units). Arrival: arc speed solved by bisection = smallest the budget allows = 65.4 u/frame (was 113-116), lateral v^2/r 3.0 u/f^2 (was 33): 11 x gentler but not calm (about 27 m/s^2 if a unit is a cm); then accel 2.0 u/f^2 to the cap 116 and the stock-like brake 2.4 to the stop. A calmer arrival needs MORE KEYS (a re-timed Activate_Enter / key table), not done. Departure: from rest accel 1.0, brake 1.5 into the arc, arc speed 39.8 u/frame (lateral 1.05 u/f^2, 31 x gentler), accel 1.5 out, peak 116, stops dead in the east pocket (unseen).
- Rotation keys follow the path heading (sway kept), each rot key set to the MEAN heading of the frames that play it (the rot table is sparser than the frames, "last frame wins" jerked up to 5.6 deg/frame; now <= 4.7 vs 35 before); frames held at the start keep the live rotation.
- CRASH KEYS: LEFT AS THEY ARE. Activate_Crash_01..04 (frames 500 / 600 / 650 / 750) start at absolute positions x 3501 / 4458 / 4971 / 6594 on the lane (arrive / stop / leave / leave), i.e. keyed to the stop, and the game picks the one by the van's state, not its position. No hook moves the wreck to the van's death place, so a van shot in a pocket or on an arc jumps to the crash start (same as street2). BENCH ITEM: shoot the van on the arrival arc, at the stop and on the departure arc; note where the wreck appears.
- Viewshed, strict (tool viewshed2): viewers = every reachable floor cell in 200-unit blocks, range 30000, eye +300, point +250, EVERY drive key (early exit per key; exact counts for the first / last 40 unique positions), solid and soft occluder sets. RESULT (final stage, PROBLEMS: 0 twice): 1249 viewers; keys 0..15 seen by 0 (solid and soft), key 16 soft 1 (the van is already on the arc), keys 17..374 seen (the street drive, 94 solid / 120 soft at key 17), keys 375..390 seen by 0 (end 17400,30400 seen by 0). Yaw max 4.69 deg/frame arrival, 4.06 departure.
- Kit: install.py pins live 778b075c / dccc9250 / 6616525a, refuses a running kl2.exe, --dry, --undo (needs each file to be exactly what this wrote), --min-free-mb 300 (backups 408 MB + .tmp 206 MB + 300). Rehearsed on scratch hard links (C:/kl_build_1024/_scratch_street3/game): dry, install, second install refused, min-free refusal, undo = all three md5s back byte-exact. Install template fixed: LIVE_ZIP_MD5 now derives from FILES (the hard-coded 74d37233 was stale).

## CORRECTION 2026-11-09 (live benches DM07GATE/UNHIDE/SINK_1109)
The 0x400 "render only, collision stays" verdict above is WRONG at runtime for these panels: every live walk that crossed went under a HIDDEN panel
(4m_01 / 4m_11, entity en? bit 0, flags 090285e6), and with 4m_01 un-hidden the walk at z 10334 stopped at its east face (x -4549); the sunk-slab
variant (13 slabs lowered to the mud) changed nothing because the crossings were still under the hidden pair. So the DM07 gate is a hole for players
too. Fix in progress: a KillBox curtain just west of the gate (tools/kl_dm07curtain_1109.py, DM11B recipe). SAME RISK on the live DD10 gate
(BigFence_A_02, REF 31255, hidden by tools/kl_dd10_vanlane_1108.py): needs a walk bench. Pillar 21329 blocks DM07 only for z 10636..12886.

