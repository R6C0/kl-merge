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
