# DD campaign levels as Fragile Alliance maps (research, 2026-10-25)

Research only. Nothing launched, nothing written to game folders. Numbers marked MEASURED come from
`kl_prpjoin.Scene.from_zip` over `<DD>\Scenes\Locations\Lxx\Lxx_Main.zip` (node count n, ZFFPlayer-style
actor count, squads, rooms). Everything else is GUESS until a live run. See also `re/campaign_fa.md`,
`re/campaign_fa_tooling.md`, `re/dd_setpieces.md`, `re/actor_caps.md`.

## 1. The L levels (MEASURED: nodes / actors / squads / rooms)

Setting is read from the big top-level groups and the situation/cutscene names (partly GUESS).

| Folder | Setting (what the groups say) | Nodes | Actors | Squads | Rooms |
|---|---|---|---|---|---|
| L00 | Intro: Shanghai skyline, apartment, torture room (cutscene level) | 9,474 | 4 | 3 | 4 |
| L01 | Markets: techmarket, fish market, submarket, alleys, cafe | 34,288 | 97 | 73 | 32 |
| L02 | Street combat, freeway, garage, Glazer escape, limo, taxis | 38,213 | 124 | 81 | 28 |
| L03 | Sweatshop / packing facility, minibus pickup | 29,779 | 140 | 71 | 61 |
| L04 | Restaurant, big street, preconstruction site, police van drop, heli | 34,215 | 140 | 78 | 30 |
| L05 | Stairways, apartments (masked goons), roof last fight: the flat raid | 22,784 | 100 | 72 | 23 |
| L06 | Street, bus, burger place with SWAT fortify/move-in, taxi | 27,480 | 76 | 39 | 17 |
| L07 | Ship: propeller, midship, construction area, bow | 20,932 | 148 | 90 | 13 |
| L08 | Rail yard / warehouses, train | 33,541 | 88 | 36 | 29 |
| L09 | Office tower: pre-office, office, foyer, restaurant, backlit, helichase | 23,049 | 95 | 60 | 10 |
| L10 | Rooftop club, restaurant, dampener, office heli attack, elevators | 42,916 | 126 | 77 | 29 |
| L11 | Airport: no-mans-land, hangar, luggage handling, passenger stairs | 37,359 | 139 | 74 | 21 |

MEASURED across all twelve: money controllers 0, kick doors 0 in the controller count (kick-door groups
exist as KickDemolishDoor subtrees, e.g. L02), no OnlineMoneyCtrl / ZSpawnPoint / escape vehicle /
bounds. No campaign level has an FA layer. They load `AllLevels/mainsceneincludes.zip` (2 ZFFPlayer),
not `mainsceneincludes_multiplayer.zip` (16 ZFFPlayer, Heroes!).

## 2. Coverage against the FA maps F01-F09

FA maps are thematic parallels with their own scene trees, not shared geometry (MEASURED: level-tagged
prop names shared are tiny: F05/L07 163, F04/L01 26, F08 carries an L10 backdrop).

| FA map (slot) | Same place in campaign |
|---|---|
| F01 Subway, F02 Hot Coffee 2, F03, F04, F05, F06, F07, F08, F09 | parallels: F05 ~ L07 ship, F04 ~ L01 market/street, F08 ~ L10 backdrop (names above); the rest are by theme only, GUESS |

Uncovered places (no FA map has them): L02 street/freeway/garage, L03 sweatshop, L05 apartments and
roof (the flat raid), L06 burger place + street, L08 rail yard, L09 office tower, plus the L01 apartment
interiors. L00 is a cutscene level, skip. L10, L11 are partly covered by F08 and airport-type maps.

## 3. Four heist round designs

Common frame (all four): systems level S = F07 (default host, MEASURED path `kl_graft.py build F07 F09`
already works DD-to-DD), map M = the L level, campaign systems zip dropped (`mainsceneincludes.zip`,
cutscene groups, `Checkpoints!*`, `Dialog*`, `MenuResources`, friendly-AI Kane/Glazer squads).
Delivered in its own folder like DLC. Chunk headroom with S = F07 is the first gate (section 5).

### 3.1 L05 flat raid (the wanted apartment heist) - best candidate
- Start: heisters on the street/stairway entrance (A-Stairways group, `SQ_Goons_car` car arrival is
  DD's own set-piece). GUESS: spawn on the stairwell landing, trigger starts the round when the street
  goons arrive.
- Loot: briefcases/bags placed in the B-Appartments rooms (the masked-goon rooms `SQ_Masks_#01..#03`)
  and a main stack on the C-Roof. The flat is the "vault": last stack opens when the room squad is dead.
- Cop waves (DD's own): street cars with goons (`SQ_Goons_car`, `Badguys_Around_Car` situation), stairs
  `Stairway_PartB3_Throw_Can` can-throw scene, apartment mask squads as heavy defenders, roof last fight
  squads `SQ_lastFight_#01/#02` as the final wave. Kick doors from the DD door kit on the flat doors.
- Escape: roof. Vehicle: a van/car on the street (`OnlineEscVehicle*`) or, GUESS, a heli pad if the
  roof has a landing node. Part 2 = down to the street. Same shape as the Retomoto two-part design.
- Music: the L05 level music set (Special!Music groups) plus Audio zip `L05_Audio.zip` (MEASURED 154 nodes).
- Risk: 22.8k nodes, smallest of the interior candidates, 100 actors / 72 squads before stripping:
  must cap to the live-proven 99 actors / 55 squads (`re/actor_caps.md`).

### 3.2 L06 burger place + street
- Start: street by the bus. Loot: till and back room of the burger shop plus a taxi trunk prop.
- Waves: `Burger_SWAT_Fortify`, `Burger_SWAT_Movein` (SWAT movein is a known DD set-piece), taxi
  arrival `L06_Street01_Taxi`, street life situation as civilians.
- Escape: bus or taxi (vehicle prop already in level). Music: L06 set.
- Risk: lowest counts (76 actors, 39 squads, 17 rooms): cheapest. Small area, so expect a short round.

### 3.3 L03 sweatshop
- Start: sweatshop floor. Loot: packing floor stacks; cash in the manager office.
- Waves: `Packing_FloorGoons`, `Packing_WalkwayCops` on walkways (good elevated cover), `Packing_Squad_*`
  and the `L03_Inside_P_Facility_Minibus_Squad_Pickup` minibus arrival as the reinforcement.
- Escape: the minibus (4 vehicles MEASURED in the level).
- Risk: 61 rooms (most of any level), 140 actors: needs a heavy strip. 29.8k nodes.

### 3.4 L09 office tower (or L08 rail yard / L02 street, pick after the first three)
- L09: pre-office, office, foyer, backlit restaurant, 10 rooms only. Waves are LMG/RPG squads
  (`Server_RPGSquad`, `Office_BossArea_LMGSquad`, `Foyer_RPGSquad`) plus `HeliSquad` (536 nodes) as DD's
  own heli set-piece; chopper strafes (`Office_Strafe01A/B`, `Strafe02`). Escape: heli or foyer exit.
  Fits the Retomoto idea but is a different building; it is the natural second tower map.
- L02: street combat with freeway and garage, 81 squads; escape in the limo (`Limo!*` groups).
- L08: warehouse blocks (`Sq_FirstWarehouses_01..04`), escape by train drive-off situation.

## 4. Sound effects and music
DD campaign SFX are in each level's `Lxx_Audio.zip` and `.SND` members; the graft renumbers .SND for M
(`re/graft_formats.md`). Campaign `Special!Music` groups give a per-level track (L02 has 46 music nodes,
MEASURED). To "carry over" campaign effects into existing FA maps, copy the used clips as Patch01 members
rather than adding nodes (GUESS, untested).

## 5. How much simpler than a DM graft
- No format conversion: DD to DD, same exe, same class IDs, same .prm/.TEX/.MAT versions, same .ANM
  version (a join is untested, GUESS that it is clean). DM grafts need kl_convert and texture/material work.
- What must be stripped: campaign scripting (checkpoints, objectives, dialog, MenuResources), cutscenes
  (`Animation/Lxx/Cutscenes`, `Special!Cutscenes`), friendly Kane/Glazer squads, `mainsceneincludes.zip`
  (2 ZFFPlayer). The generic pre-pass is `kl_maps.campaign_drop`; `kl_prpjoin.sides()` and
  `SYSTEMS['dd']` need the one code change to drop the campaign systems zip when an L level is M.
- Then add the FA layer from `mainsceneincludes_multiplayer` (it ships with S = F07).
- Tools per step: survey/join `kl_prpjoin`; build `kl_graft build`; FA layer `kl_fa`, `kl_fa_author`
  (spawns, bounds, POI), `kl_fa_loot`, `kl_fa_bank`; AI `kl_fa_bots`, `kl_old_waves`, `kl_fa_civs`,
  `kl_fa_fed`; arrivals `kl_arrivals_1024r2`; escape `kl_escape`; impact/shootable vans `kl_impact`;
  lighting `kl_light`; pack/install `kl_package`, `kl_expansion`; pre-flight `debug/check.py`,
  `tools/verify_levels.py`; run `tools/kl_autotest.py`, triage `debug/triage.py --keep`.
- Chunk gate: 73,728 table limit (tools refuse above 69,632). F07 plus a 20-30k node level is tight; L05
  (22.8k nodes), L06 (27.5k), L09 (23.0k) are the three that most likely fit after stripping. L10/L11/L02
  (37-43k nodes) likely need aggressive stripping. All GUESS until the join is run (the survey did not
  compute chunks). F01 chunk figure 24,844 seen in the survey is the test slot and unreliable.

## 6. Open points needing a live run
1. Does the campaign ANM join cleanly with S ANM? (untested)
2. Does the L-level nav/cover survive without the campaign systems group?
3. L05 roof escape: is there a drivable or heli-landing node, or do we place the van on the street?
4. Actor/squad caps after strip for each candidate.
5. Do campaign kick doors and airlock-style doors still work without campaign scripting?
6. Recommended order: L05 flat raid, then L06, then L03, then L09. Do not start before the owner
   approves the stage; nothing here touches the game.
