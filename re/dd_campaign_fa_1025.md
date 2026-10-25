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

## 7. Critic corrections and first build job (2026-10-25, second agent, still research only)

Re-measured with `kl_prpjoin.Scene.from_zip` on all twelve `Lxx_Main.zip` (read-only; scratch scripts in the
session scratchpad, not in the repo).

CONFIRMED (MEASURED): all 12 node counts of section 1 are exact. No level has any `FASpecials*`, `OnlineMoney*`
or `OnlineEsc*` node (0 of 12). The "money 1 / spawn 2" hits in L05 are false friends: `Debris_Money_01` (a
particle template inside `mainsceneincludes.zip`) and `Gate_Xiu_Spawn` / `Timer_Xiu_Balcony_Spawn` (a civilian
script). F07 for comparison: 17,305 nodes, 9,137 of them systems, 8,167 map, and 19 `FASpecials!SpawnPoint` nodes.
Each L level carries `AllLevels/mainsceneincludes.zip` as one top-level subtree of 3.0k-4.0k nodes (L05 3,987).

CORRECTED:
1. The node counts overstate what the graft takes. The map proper is the `Locations/Lxx/Lxx_Locations.zip`
   subtree: L05 10,880, L09 11,060, L07 9,199, L06 16,052, L03 16,901, L02 19,782, L01 21,272, L04 18,605,
   L08 22,822, L11 25,619, L10 29,399. Add the Lxx_Audio, situations and AI groups. L05 and L09 are the light
   ones, L06 comes third; the order of section 6 (L05, L06, L03, L09) stands for design value, but L09 is
   cheaper than L03 on size.
2. `kl_prpjoin.sides()` on an L level gives systems = 2 nodes, map = 22,781: `mainsceneincludes.zip` is not in
   `SYSTEMS['dd']` (only the `_multiplayer` zip is), so it lands on the map side. The "one code change" is therefore
   only needed to make it automatic. For the FIRST trial no code change is needed: `kl_graft.py build` already has
   `--m-drop` (top-level names, fnmatch), so `--m-drop "AllLevels/mainsceneincludes.zip"` removes it. UNVERIFIED
   that nothing in the map points into that subtree (REF paths into `ROOT\AllLevels/mainsceneincludes.zip\...`
   would dangle; `kl_prpjoin.references()` finds them).
3. `kl_maps.campaign_drop` is NOT generic: it does `Scene.load(level, 'dm')` and keeps names by Dead Men geometry
   rules, so it cannot take an L level as is. The L pre-pass is a new small function (drop list = the groups
   of section 3 strip list), or hand-written `--m-drop` names for the first trial.
4. ANM: section 5 says the join is untested. There is a tool for it: `kl_anmjoin.join(S.ANM, M.ANM, ...)`
   (re/anmjoin.md), written for DD to DD first, and `kl_graft.build` calls it by default (`anim=True`). Its
   `test` command covers F levels x F levels and Dead Men maps, not L levels, so L-as-M is still untried but is
   the normal path, not a new one. The "never copy .ANM" rule in CLAUDE.md is about the DM header size and does
   not apply DD to DD.
5. Sound: the section 4 wording is DM-shaped. A slot's `Fxx_Main.zip` finds its sound through `Fxx_Main.SND`
   in the zip plus `.WHD/.WAV/.hti` BESIDE the zip (kl_graft `BESIDE`, kl_snd docstring). The campaign
   level's own bank is `Lxx_Main.WAV/.WHD` beside its zip (L05 7.97 MB, L06 22.1 MB, L03 14.1 MB, L09 5.97 MB;
   F07 18.3 MB). `kl_snd.graft_audio` (called by `build`, `sound=True`) appends what M's map nodes name into S's
   bank for M of either game, so campaign effects ride the normal path. Streamed music/dialog clips live in
   `PC_Def.str`; whether the L levels' clips are in DD's stream file is UNVERIFIED (kl_graft reports
   "N stream clips are not in the merged stream file" if not). Side fact: every `Lxx_Main.WAV` carries our own
   Oct 24 gun-sound patch (`.WAV.before-1024gunsnd2` beside each); reading them is fine, never write them.
6. Slots and folders: the exe loads only `Locations/Fxx/Fxx_Main.zip` (engine_facts.md line 10). A "map in its own
   folder" means a `KLExpansion\Maps\<id>` folder whose archive is named for a stock slot and which the hook's
   `[Redirect.N] F0x=<folder>` points a menu-page entry at (kl_expansion.py, campaign_fa_tooling.md section 4).
   Page 2 has one free entry (F07), further maps need page 3. A DD campaign map therefore competes for the same
   few slots as the DM maps; the build still goes through an F-slot name (F01 for tests), never a new
   `Locations/Lxx` name. Dropping the L zip itself into an F slot is not what the note means and would not work.
7. "Simpler than a DM graft": true for formats (no kl_convert, no texture/material port, same .prm/.TEX/.MAT, same
   .ANM header, no voice-line .LOC conversion), not true for content: the L levels are story levels with the
   same scripting weight as the Dead Men chapters (checkpoints, objectives, cutscenes, friendly squads, 72
   squads in L05). The strip list, the FA layer (spawns, money, escape, bounds, AI waves) and the actor/squad caps
   are the same work as for M05_A. Saved effort: conversion only.

FIRST BUILD JOB (L05 flat raid, offline, nothing installed; est. the same minutes as the F07+F09 baseline):
1. Baseline: `python tools/kl_graft.py build F07 F09` must still pass (proves the DD to DD join on this tree).
2. Survey what dangles: with `kl_prpjoin.Scene.load('L05')` list `references()` whose holder sits outside
   `Locations/L05/L05_Locations.zip` and target inside `AllLevels/mainsceneincludes.zip`, and the same for each
   campaign-only top group (`Checkpoints!*`, `Dialog*`, `MenuResources`, `Animation/L05/Cutscenes`,
   `AI!Friendly!*`). Output is the drop list.
3. Trial graft into the test slot with output kept out of the game: set `KL_GRAFT_OUT=<scratch>` then
   `python tools/kl_graft.py build F07 L05 F01 --m-drop "AllLevels/mainsceneincludes.zip,<campaign groups>" --no-fa`
   (add `--silent` first if the sound merge trips). Read `result.json` / `log.txt` for chunk count (gate 69,632),
   actors and squads, sound, ANM, "stream clips".
4. `python debug/check.py` on the output, then `kl_prpjoin` `references()` on the joined scene (0 dangling).
5. Only after steps 3-4 are clean and the owner's stage allows: author the FA layer (kl_fa_author style spawns on the
   stairwell landing, briefcases in B5 rooms and on the roof, van on the street), then install into F01 and run
   `python tools/kl_autotest.py` (needs the owner away from the machine and Steam signed in).
Decision rule: if step 3 shows chunks over 69,632 or more than ~10 dangling references to the dropped subtree,
switch to L09 (11k map proper) before spending time on L05's FA layer.
