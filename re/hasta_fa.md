# Hasta (Dead Men M11_B) as a Fragile Alliance map under F07 - handovers

Tool: `tools/kl_fa_hasta.py` (build-base, proof-pair, measure). Plan: re/campaign_v2_plan.md, numbers: re/campaign_fa.md (Havana rows).
OFFLINE only. Nothing was installed, the game was not started. Builds live in `<work>/build/hasta_1017/`.

## handover, step 1 (2026-10-17): graft and fit

What I changed: added `tools/kl_fa_hasta.py` (new file; no shared tool edited). `build-base` runs the MEASURED order of
campaign_fa_tooling.md 3.5: `kl_maps one F07 M11_B --campaign --keep` -> `kl_graft lighten --load trim,slim,fxc` ->
`kl_chars wardrobe` -> `kl_chars compact` -> `kl_impact`, measures each stage, wipes the previous stage's archive.
`<out>/base.json` has every number; `<out>/logs/*.log` the stage outputs.

Measured (this run, `python tools/kl_fa_hasta.py build-base`, about 2 min of tool time):

| stage | chunk-table entries | .prm | .TEX | archive |
|---|---|---|---|---|
| graft F07 + M11_B --campaign | 74,454 (726 over the game's 73,728) | 69.0 MB | 433.3 MB | 362 MB |
| lighten | 74,454 | 69.0 MB (lighten does not shrink the .prm here) | 242.9 MB | 223 MB |
| wardrobe (15,509 dead indices reused, plates none) | 74,454 (8,799 free indices left but the table counts the top) | 85.2 MB | 264.1 MB | 250 MB |
| compact | **58,992** | **84.4 MB** | 264.1 MB | 249 MB |

`kl_impact` on the compacted folder: problems 0. Verdict: chunk table under the tools' line (69,632) by 10,640; .prm 84.4 MB under 90 MB
(the plan's allocator figure; exact edge a GUESS). Reproduces the earlier havana_ward.sh numbers (58,992 / 84.4 MB). The wardrobe's own
`problems: 1` is the chunk table line before compaction (expected; build-base accepts exit 1 for build and ward). Other stage detail:
1,862 textures, 1,191 materials (647 used), 19,189 nodes, 16 people, 73 skeletons, .HVK 4.3 MB, .ANM 21.6 MB, 54 gates (graft log).

Where things are:
- Compacted base: `<work>/build/hasta_1017/final/` (F01_Main.zip 249 MB + .WAV/.WHD + KLWardrobe.ini; slot name F01 as always, F07 host systems).
  It is a BARE base: no spawns, loot, van, bots, wake, guns, masks beyond the wardrobe's. The 8-mask / 12-mask figures
  (60,902 / 66,318, campaign_fa.md) are what the finished layer adds on top.
- Compaction proof pair (prepared, NOT loaded): `<work>/build/hasta_1017/proof_pair/uncompacted/` (Retomoto + wardrobe, 65,119 entries,
  fake-fix applied) and `.../proof_pair/compacted/` (50,703 entries). Made by `python tools/kl_fa_hasta.py proof-pair` (kl_fa_bots_dyn
  fake-fix of `build/x_chunks/retomoto_wardrobe` and `_compact`, PASS both, 2 FakeTargets off each; the x_chunks folders were only read).
  A live session loads the uncompacted one first (known to work shape), then the compacted one in the F01 slot; the question is
  only whether a compacted chunk table loads. Do not load the raw x_chunks folders (campaign_fa.md live proof I).

What the next step must know:
- Build base is stage-wiped: `--from light|ward|compact` only works with `--keep-all` on the first run (earlier archives are deleted).
  Rerun whole = about 2 minutes, 1.2 GB peak; G: had 11 GB free after (final 283 MB + proof pair 505 MB stay).
- Compaction happens before the layer (kl_map_guns/KLGuns.ini names chunk indices and compact does not rewrite that file):
  author the Hasta layer (spawns, loot, bounds, escape, van) ON `final/`, i.e. the layer module must be applied after compact or
  re-numbered; the club/bank modules apply their layer inside `build()` before finish, so a Hasta module needs the compact step
  between its graft and its guns/bots (GUESS: order `one` -> layer -> lighten -> wardrobe -> compact -> guns -> bots, as the tooling note 3.5 lists).
- Still open from the plan: four geometry switches (loot wing door, bunker, Capitol corner, stair barricade) built open; no opening
  blast object (use a trigger-driven beat); no van line (kl_map_escape.van_plan); a compacted level has never loaded.

## design, step 2 (2026-10-17): Hasta as a Retomoto-shaped round (read from the files; NOT built, NOT loaded)

Reader: `python tools/kl_fa_hasta.py read` -> `<work>/build/hasta_1017/design_read.json` (switch collision boxes, loot, squads by group,
start floor, van trial). Sources: Dead Men `M11B_Main.zip` (actors, props, switches) and the step 1 base `final/` (road, van lane).
Units are the game's (100 = 1 m). Coordinates in the campaign level and in `final/` are the same (checked: floor y 800 under the start
row in `final/`). REF ids differ between the two (the graft renumbers): switches below are by NAME; refs given are the CAMPAIGN's.
Everything marked GUESS is my proposal, not a measurement.

### Shape of the round (Retomoto's model)
| beat | where (x, y, z) | what |
|---|---|---|
| 0 start | row x 33,900..34,000, z 29,900..30,900, floor y 800 (3 probes: 800 each), facing +x | under the dome, in the middle of the action |
| 0 opening blast | corner marker (32,095, 888, 29,022): 23 m from the row | the tank-shell blast at the Capitol corner (no such object in M11_B: borrow the Retomoto/club timer pattern, kl_fa_author event -> BLAST_DELAY 12.5 s -> bang; the 'post on / pre off' lists as kl_fa_bank.blast_lists reads them) |
| 1 hall fight | hall x 28,200..40,260, z 28,850..32,560, y 800 | guards at the bunker, 47 m from the row |
| 1 bunker beat | bunker wall x 38,597..38,768 (z 30,251..30,628) | when the bunker squads are dead: dust BoomBox (38,613, 902, 30,398), wall swap, wing door opens |
| 2 loot | wing: corridor x 39,300..41,400, end room x 41,000..43,600 | 11 cases, 5 paintings, briefcases on the table |
| 3 join | wing -> hall -> corner hole -> gallery -> side stair | the police (army) are released when the crew leaves the wing with loot; 79 m wing door to the hole |
| 4 street | gallery (28,380, 840, 29,370), stair (27,540, 470, 30,193), foot (26,667, 20, 27,758), square y 0 | fight down the stair to the square |
| 5 van | stop (25,600, 2, 21,800), 61 m from the stair foot | escape |

### 1. Rooms (campaign M11_B, `kl_maps what`; extents of modelled entities)
Part 1 rooms: Main_Hall (724 entities, x 28,200..40,260, z 28,850..32,560, floor y 800..830), End_Corridor (302, x 39,300..41,400,
z 31,000..32,500), End_Room (255, x 41,000..43,600, z 30,700..33,300). Part 2 rooms: Side_Entrance (58, x 26,470..29,600, z 28,250..30,300,
stair y 200 -> 810), Capitolio square (1,350, x 21,100..31,500, z 21,350..28,000, y 20 mesh; terrace y 800). Not used (stay as backdrop, no
players): courtyard house, roof, side street east (x 32,500..36,200, z 15,400..25,500). 16 rooms in all.

### 2. The four geometry switches (MEASURED, HVK world boxes in the campaign, all STATIC type-1 shapes; box = x / y / z min..max)
| switch | node (campaign REF) | collision box | built | wanted |
|---|---|---|---|---|
| loot wing door block | `End_Corridor_01a\ColiObj_Obj_Roadblock_01` (5313) | x 39,458..39,754, y 800..1500, z 31,295..31,374 | blocks the wing's ONLY door | sunk by the bunker beat (not at start): nobody reaches the loot before it |
| bunker | `SI0100_M11_BarricadeB_01` (4617) + `M11B_OYCHECK_BEFORE01` (4333) | wall x 38,597..38,768, y 781..1177, z 30,251..30,628; check block x 37,883..38,440, y 778..2133, z 29,662..31,152 | both solid | both sunk at the bunker beat; the `..._Broken01` pieces shown (the campaign's `GeomDeactivatorSandbags` names exactly these two) |
| Capitol corner | `SO0201_M11_Corner_01` (10618) -> `..._CornerBroken_01` (10617, hidden) | whole: x 31,432..32,350, y 0..2000, z 28,500..29,616 | whole corner shut | at the opening blast: whole sunk, broken shown (it is the way OUT) |
| stair barricade | `SO0201_M11_BarricadeXX_01` (10619) | x 26,875..27,540, y 160..443, z 28,481..28,580 | wall across the stair foot | sunk at round start (cheaper than a beat of its own; GUESS) or with the corner |

The graft built all four open (sink by 4,000 / hidden state off, campaign_fa.md G1.5); this design says WHEN each is wanted open, so the layer would
have to move the 'open' state from build time to a trigger for two of them (door block, bunker). OPEN QUESTION: whether a static piece can be switched at
run time (the bank/prison only open at build time; the campaign's own `GeomDeactivator_Coli` controller removes collision at run time and the bunker uses it).
Fallback if not: build the door and bunker open from the start and keep the guards behind the sandbag MODEL only (loses the 'locked loot' beat).

### 3. Opening beat (no object exists in the level)
Campaign objects that exist: `BoomBoxDust` (38,613, 902, 30,398) is the BUNKER's blast, not the corner's; shake boxes `GeomDeactivator_FarShake / NearShake /
AllCamShake` sit at (45,438, 1,967, 36,386) (far east, outside the map; what they drive is a GUESS from the names). The corner's campaign bang is
the tank's shell (T72 `Destruction` group: `GeomDeactivator_ShotColiHack`, `_CapEntranceCorner`, `_Barricade`, all parked at (2,003, 0, 731)).
Design (GUESS): reuse the Retomoto/club timer chain (round-start event -> BLAST_DELAY -> bang) with the bang at the corner marker (32,095, 888, 29,022):
at the bang the lists swap the corner pieces and the stair barricade, and dust/emitters and camera shake from F07's blast effects play. The crew spawns
23 m from the bang, facing +x (away from it, as Retomoto faces its window). Needs the pre-GO seconds the host has.

### 4. Loot props (MEASURED places)
Display cases (11; glass cases of the Retomoto samurai family), place = group origin, y 800:
corridor (39,360, 31,015), (39,550, 31,915), low case (39,724, 31,537), (40,200, 31,365), (40,200, 32,465), (40,800, 31,675), (40,800, 32,155);
end room (42,020, 31,430), (42,020, 32,390), (42,620, 31,260), (42,620, 32,560).
Paintings: (39,900, 31,015), (40,500, 32,365), (40,500, 31,465), (41,400, 31,615), (41,400, 32,215), all y 800. Table with briefcases:
(42,650, 802, 31,915). All 17 sit behind the door block, 57..89 m from the start row. The case groups are `Montre_Shotactivate_*`
objects (shooting the glass = the campaign's break); how a Fragile Alliance loot object attaches to them is the loot module's job (kl_fa_author).
All loot is in one wing, so the join has to make the crew LEAVE with it (the police gate below).

### 5. Enemies (MEASURED: `design_read.json` squads, 50 groups; counts are ZFFActor nodes, group name = squad)
Inside, The7 soldiers (enemy): `SevenDudes_01` (38,822, 901, 29,959) 1, `SevenDudes_02` (38,831, 915, 30,895) 1 (the bunker's two flanks, y 900 =
on the dais), `LastSeven_01` (39,643, 802, 31,628) 1 (carries the swap), `LastRoomFight_01` 2 (41,850..41,983, 30,813..30,821, y 807),
`LastRoomFight_02` 1 (41,850, 803, 33,118), `FuentesSquad` 1 (43,084, 800, 32,038: the boss; GUESS: drop or keep as a tough guard).
2 bunker guns are `MountedWeapon` (left, per the study). `CarlosSquad` sits at (2,002, 0, 731), a parked group: drop.
Hall entrance / terrace (the study's police): `RebelMainBarricadeEntrance` 2 (33,927..34,391, 28,841..28,899, y 826) = 15 m from the start row; `RebelGotoHole`
1 (33,400, 803, 28,848) = 16 m; `RebelMainBarricadeNearHole` 1 (31,619, 801, 29,125); `RebelMainBarricadeShootCro` 2 (32,934..34,306, 28,214..28,236);
`RebelMainBarricade_RPGBefo` 1 (32,822, 801, 28,358); `RebelMainBarricade_RPG_01` 2 (28,040..32,712, 28,326..29,231). These stand at the START's elbow: they must be moved
or held (GUESS: start them held, release at the join).
Side stair: `RebelSideBarricadeSideEntr` 2 (27,601..27,635, 29,190..29,341, y 802), `...TopFloor` 2 (27,797, 29,385), `RebelSideBarricade_01` 6 (26,950..27,422,
29,152..29,431, y 209), `...Guard` 2 (26,963..27,383, 29,132..29,152), `RebelSideEngage_01/02` 4+4 (26,611..26,903, 29,525..29,783, y 162),
`MountedMachinegun!...` 7 (26,773..27,522, 28,809..29,417, y 161; MountedWeapon: left). `GainAccess` RPG squad 1 (32,592, 805, 28,997): left.
Square (Ally faction, 'loyalists'): `LoyalistChargeF/H` 4 + 9 at (21,992..22,201, 20,686..21,115, y 31) and `LoyalistChargeM` 6 at (33,203..33,990, 18,242..18,896, y 10).
The first two groups stand 16 m from the van's waiting place (below): drop them (FA has no allies; GUESS). Kane's mercs and `AllySquad_01..04` (x 19,060..19,950, z 20,520..21,040)
are west of the rubble, outside the playable square: drop. Courtyard/roof squads (`AreaBeforeChopper*`, `ChopperBattle_Rooftop*`, 12 groups) are in other rooms: not used.
Civilians: none (no civilian ZFFActor; the 3 `Crowd!` groups are human-flow objects, 7 nodes each). GUESS: Fragile Alliance wants none here.

### 6. Round plan
- Part 1 (hall): crew starts, blast, hall guards (bunker flanks 2) engage from the dais; about 47 m to the bunker. The bunker beat is 'its squads dead' as in the campaign.
- Beat: bunker swap + door block sunk + BoomBox dust -> the wing opens (loot 57..89 m from the start).
- Loot: 11 cases, 5 paintings, the table; wing guards 4 (+ boss GUESS).
- Join: the FIRST loot pick-up (or the crew leaving the corridor) releases the police: entrance/terrace squads come in through the front door and the corner
  hole BEHIND the crew (79 m back to the hole), so the way out is fought, not walked. The side stair squads (about 16 men, y 162..209) hold the stair foot = the street.
- Street: hole (32,095, 888, 29,022) -> gallery (28,380, 840, 29,370) -> stair top (27,540, 470, 30,193) -> (27,168, 200, 29,095) -> foot (26,667, 20, 27,758): about 460-470 m
  for a bot (study; one mesh part of 606). The ONLY way between the hall floor (y 800) and the square (y 0..20).
- Van: see 7. The Heat-style street fight = the stair foot to the van, 61 m across a cratered square.

### 7. Van line (MEASURED trial: `kl_map_escape.van_plan_points` on `final/`; 0 faults)
Findings on the square (scan of the `final/` collision, cells of 100..500): the road is y 0 (mesh y 20 floats above it). West end closed at x 21,500..21,800 by rubble
(PC0300_M11_RubblePiles02) plus walls at x 20,100..20,300; craters (road -12 .. -90) at x 29,600..31,000 and a concrete roadblock line x 31,400..31,900, z 22,000..23,000;
a wrecked car `Vehicles!V_CUB_Chevy_B_Static_00#12` (29,444, 1, 21,826; 40 nodes) in the lane at z 21,750..21,910; `ColiObj_Obj_Roadblock_01` (square) at x 23,900..28,109,
z 21,104..21,192, y up to 2,100 (south edge, not in the lane). A south side street (x 32,500..35,000, z 12,000..21,000, 90 m straight, y 0) also leads in, but its arrival
crosses the craters/roadblocks: refused by the lane test (trials: rough 82, or 'only 1,040 clear lane').
The road that PASSES: arrive `(23400,0,21800) (24500,0,21800)`, stop (origin) `(25600,0,21800)`, leave `(29100,0,21800) (30600,0,21800)`, heading from the curve (east),
`clear` = the wreck's 40 REFs (the layer must take the wreck out; in `final/` its refs are 22997..23036 and change on every graft: select by name).
Result: drive in 22 m (lin 2,200; wait (23400, 2, 21800)), drive away 44 m (lout 4,400; end (30000, -17, 21800)), rough 5.6, camera (cam_spot's choice, GUESS) (23,800, 330, 21,800)
= 18 m behind the stop. MIN_IN 20 m / MIN_OUT 30 m met. The arrival is NOT out of sight (rubble is 16..20 m west of the wait point; the van would have to start waiting at x 23,400
behind the rubble line or simply appear - GUESS), and the drive away ends at the craters. Stop to stair foot 61 m; the loyalist groups at (22,000, 20,900) must go.
With `heading=270` the planner reported 'heads 90'; the trials use heading None - do not pass a heading until that is understood.
Reproduce: `python tools/kl_fa_hasta.py read` (the `van_trial` block of design_read.json).

### 8. What is NOT known (all need a live run or more reading)
- Whether sinking the door block / bunker wall can happen at run time (item 2); whether a compacted level loads (step 1).
- The corner blast effects (which F07 template is borrowed) and whether the level's shake boxes do anything.
- The squad release as a trigger (the 'join'): kl_fa_author has the pattern for Retomoto; not read for this level.
- The hall's light under a Dog Days level; the mesh runs through the standing bunker wall in a 79 cm slot (study).
- Everything marked GUESS above.

## handover, step 2 (2026-10-17): the level read and the design
What I changed: `tools/kl_fa_hasta.py` got a `read` subcommand (read-only; DM_ZIP, SWITCHES, VAN_TRY, read_design). Output `<work>/build/hasta_1017/design_read.json`.
No shared tool edited, nothing installed or built, no game started, nothing committed. Design: section 'design, step 2' above.
Measured: the four switches' collision boxes (6 nodes), start floor y 800 at three probes, 11 display cases + 5 paintings + table, 50 actor groups (counts above),
and a van road that plans with 0 faults on the base (lin 2,200 / lout 4,400, stop (25600, 2, 21800), clear = the wreck group). Key distances: row -> bunker 47 m, -> wing door 57 m,
-> far case 89 m, -> corner hole 23 m; wing door -> hole 79 m; hole -> stair top 47 m; stair foot -> van stop 61 m.
Next step must know: (1) actors, switches and the wreck are matched BY NAME - the graft renumbers REFs, so the layer must too; (2) the nearest enemy squads stand 15-16 m from the
start row and need holding or moving; (3) the door block and bunker are built open, the design wants them opening at run time (open question, section 2); (4) `van_plan_points` with
heading=270 faulted 'heads 90': leave heading None; (5) the loyalist groups (13 men near x 22,000, z 20,900) stand 16 m from the van's waiting place; (6) the layer comes after compact
(step 1 note) and the .prm must be re-measured: the layer adds about 7 MB, 84.4 -> about 91.6 MB is over the 90 MB figure (GUESS edge), so lighten/trim needs another look before spawns are added.

## Handover, step 3 (2026-10-17) - NOT DONE, only reading finished

Nothing was built and tools/kl_fa_hasta.py was not changed (still: build-base, proof-pair, measure, read).
Findings for the next session:
- The plain `kl_maps.one --campaign` graft leaves the four switches CLOSED (steps 1 and 2 said open: wrong).
  Only a Doors-style wrapper (sink nodes -4000 world y, cut their HVK placements, clear hidden state on shown
  nodes; pattern tools/kl_fa_bank.py class Doors, /g/kl_scratch/cfa_fill1/build_open.py) opens them.
- Plain graft verify: chunk table 74,454 vs 73,728 (needs compaction, then a KNOWN entry) and 7 missing
  stream clips (known). Compacted base 58,992 chunks / 84.4 MB .prm; the layer adds ~7 MB (~91.6 MB,
  above the ~90 MB GUESS edge: lighten may need another pass).
- Plan: copy the kl_fa_v2_park.py structure (do not import; another session owns it) with HOST F07,
  LEVEL M11_B, the nine author names, wreck group sunk + its descendants' REFs as the van `clear` list,
  squads held by SQUAD_ACTIVE=0 until a timer/TriggerBox. Chain: lighten, wardrobe, compact, bots, guns, fxc, dyn.
- MEASURED: only the chunk counts above. Everything else in the plan is GUESS. No sha1, no checks/summary.txt.

## Handover, step 3 (2026-10-17) - NOT DONE, layer module not written
Nothing was built; no <work>/build/hasta_1017/M11B exists from this step. Findings for the next attempt:
- The plain `--campaign` graft leaves the four geometry switches CLOSED (steps 1-2 said open: wrong). A generic Doors-style wrapper
  (copy of kl_fa_bank.Doors, which is hard-wired to the bank's leaves / DOOR_DY=-2500) must sink them by -4000 y in .prp + .gms and cut their HVK placements.
- M11_B scene indices (kl_prpjoin.Scene.load('M11_B','dm')): Roadblock block 4863 (End_Corridor_01a), bunker wall BarricadeB_01 4046
  (BarricadeB_Broken01 3973 hidden), OYCHECK_BEFORE01 3969, Corner_01 7363 (CornerBroken_01 7362), BarricadeXX_01 7364,
  van wreck group Vehicles!V_CUB_Chevy_B_Static_00#12 6555 (to go via van_plan_points `clear`). Rooftop Roadblock 8949 is a different object.
- Design to follow: copy kl_fa_v2_park.py structure (do not import), HOST F07, LEVEL M11_B, A.SQUADS['M11_B']=('',), squads held by SQUAD_ACTIVE=0.
- Open: F07 loot pool size vs 16 loot places; chunk table KNOWN entry; .prm size vs the 90 MB GUESS edge. All still GUESS/unmeasured.
