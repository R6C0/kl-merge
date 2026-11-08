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
