# DM09 Retomoto: route down the steps to the terminal van (d0, 2026-11-09)

Owner ask (11-09): "extend it to the original mission where you gotta go down the steps to the van all the way down".

## Nav flood of the LIVE DM09 (tools/kl_dm09_flood_1109.py, read only, offline)
- Live `KLExpansion\Maps\DM09\F06_Main.zip`, every polygon (no PLAY filter): the road mouth (-5700, 9000) and the campaign's
  terminal van V_USA_GetawayVan_Chase_00 (-24630, -979, 8958) / EndOfLevel are in ONE mesh component (1615 polygons).
- Shortest polygon path 279 m, 49 polygons, road y -40 -> terminal y -1040, 0 steep hops (>60 within 2 m): the stairs are
  continuous slopes on the mesh. Route: west along the road to x -12900, down Stairs_Overpass (-13545 -150 -> -14359 -942,
  z 12000..13230), west on the terminal floor (y -950) through (-16600, 12950), (-18400, 10600), (-19500, 8400) to the van.
- So the AI CAN path there already; what blocks players today is authored: the west slab 030_LevelBound_StreetLeft
  (x -7500..-6500), otrExitLevel/boarding boxes and van at the live stop (-1853, 10800).

## What a "terminal" variant needs (not built; GUESSES until benched)
1. Bound: move/drop the west slab, add a new bound west of the terminal (x < -26000) and on the overpass edges (fall 10 m).
2. Escape: van stop + otrExitLevel + boarding box + PathBlockerVan at the terminal van; keep DD's F07 Escape_Vehicle_01.
3. Hook consumers of the van position: [BotFillWay_DM09] P1..P8, OnlineVanPosSane, klescort.c exit walk / FollowOut.
4. Round time (re/dm09_timing_1102.md): +279 m on foot is about +45..60 s; raise the round timer to match.
5. Ship as a toggle-able third variant so the current DM09 stays the shipped one.
Open: bus clearance (17 buses) on the terminal floor, lighting/streaming of the far terminal, police along the new leg.
