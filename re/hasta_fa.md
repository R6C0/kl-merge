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

## Handover, step 3a (2026-10-17): doors + opening, built and PROVEN on a scratch graft
New file `tools/kl_fa_hasta_layer.py` (nothing else changed; kl_fa_bank untouched, so bank builds stay byte-identical). `Doors` = generic copy of kl_fa_bank.Doors:
nodes matched BY NAME (+ ancestor filter, exactly one hit required), group specs sink the group node and send ALL descendants' REF ids to the collision cut, SINK_DY -4000 (GUESS, the
study's figure). `doors()` context manager / `Doors.arm(log, specs=, groups=, dy=)` for the next steps' build script. Sunk: ColiObj_Obj_Roadblock_01 (ancestor 'End_Corridor'; the rooftop one stays),
SI0100_M11_BarricadeB_01, M11B_OYCHECK_BEFORE01, SO0201_M11_Corner_01, SO0201_M11_BarricadeXX_01, and the wreck group `Vehicles!V_CUB_Chevy_B_Static_00#12` (40 nodes).
Proof (`python tools/kl_fa_hasta_layer.py proof`, 45 s, scratch C:/kl_scratch/hasta/proof.json, big archive deleted): bare `kl_maps.one F07 M11_B --campaign` with Doors armed -> every sunk entity
is exactly -4000 in world y against the campaign level (read back by name), .gms and .prp world places agreed inside Doors (raises otherwise), 24 HVK placements cut (shape types {1: 5, 4: 19}) and 0 left under the
cut REF ids, and `van_plan_points` on the built level with `clear=[]` (no REF list needed any more) plans 0 faults (lin 2,200 / lout 4,400, stop (25600, 2, 21800)).
Verify of that bare graft still prints its 12 expected FA-layer problems (no spawns, loot, squads: step 3b+) - not new.
NOT done / open: (1) run-time opening (locked-loot beat) is out of scope: the switches are open from tick 0, the wing is reachable at once (GUESS acceptable for a first playable). (2) The 'broken' siblings
SO0201_M11_CornerBroken_01 and SI0100_M11_BarricadeB_Broken01 are untouched; how the campaign hides them and whether their collision is live while hidden is NOT known (1 entity each; the proof lists them) -
check at the first live run. (3) Doors must be armed around the SAME kl_maps.one call that the layer's build uses (before lighten/compact); the lighten/wardrobe/compact stages come after and were not re-run
here, so the .prm/chunk numbers of the base are unchanged (Doors moves nodes, adds no geometry). (4) No live run: collision-gone is proven in the file, not in the game. (5) Heading None for the van is still unexplained.

## Handover, step 3b (2026-10-17): the Fragile Alliance layer, built and impact-clean (OFFLINE, not run in the game)
`python tools/kl_fa_hasta.py build` = bare graft for the van plan (Doors armed) -> `kl_fa_hasta_layer.py test <out> --keep` (doors + layer + finish + own check) -> lighten -> wardrobe -> compact -> kl_impact.
Result in `<work>/build/hasta_1017/final` (+ van.json): kl_impact `problems: 0`, chunk table 58,992 (limit 73,728), .prm 84.4 MB (under the 90 MB GUESS edge), archive 249 MB; light/ward/build folders deleted.
`tools/kl_fa_hasta_layer.py` is now a Park-style author module (HOST F07, LEVEL M11_B): `test` / `check` / `finish` / `plan` / `proof`; `kl_fa_hasta.py` gained `build` (build_base(layer=True)).
Made: START 8 (2x4 rows x 33,900/34,000, z 29,950..30,850, facing +x), TRAITOR/TEAM_MERC/TEAM_MERC1-3/AFTER_DEATH/police spawns re-placed (heights snapped to the navigation mesh); 0 spawn/men off the mesh.
Loot: 16 places (11 cases at 150,000, 5 paintings at 300,000 = 3.15 M), F07's drop pool holds 108 ALL + 25 TM_ONLY stacks (MEASURED) so the pool is not the limit; briefcase prop (DM FA case x1.25).
Bounds: 4 F07 bounds re-placed outside the playable area (AlleyTop, StreetLeft, StreetRight, AlleyRight; all rectangles GUESS), 020_AlleyRight / 040_AlleyLeft parked at y -60000; campaign's own two bounds kept.
Escape: van_plan ROAD (heading None), 0 faults, stop (25600,2,21800), boarding (25263,0,21800), exit box 200 from it; van hidden until the alarm (FakeTarget removed, as the club).
Squads (26 men, 12 M11_B squads, all held, ZSquadScript field 3 = 0): start timer +2 s -> 6 gallery/hall squads; box at the wing mouth -> LastRoomFight_01/02; box at the stair top -> 4 street squads
(SideBarricade_01, SideEngage_01/02, Guard) + alarm (+8 s van + exit line) + gate (F07's four 030_AfterLoot police squads re-placed on the square, 10 men); backstop 300 s. Soldier rows: sharp 24, cop 1, swat 1.
Own check: PASS apart from KNOWN lines (stream clips as Park; pre-compaction chunk table 74,763 > 73,728, fixed by compact). kl_fa.check DEGRADED 'no bot squads' (same as other graft maps), 1 cover list.
NOT built: the timer-driven corner blast: no reusable object (BoomBoxDust = Explode with an EMPTY effect name; rooftop BoomBox needs FX_Grenade_T72_02 from the dropped mainsceneincludes.zip). Needs kl_fa_blast-style objects: later step.
Open GUESSes: every coordinate not marked MEASURED in the layer (spawn grid, bound rectangles, police and loot offsets, stage boxes), START_AT 2 s, VAN_DELAY 8 s, BACKSTOP 300 s, and whether naming the start child
wakes a squad (fallback flag `--squads-awake`). Not loaded in the game; "a compacted level has never been loaded" caveat from step 2 still holds. Did not touch klhook, kl_fa_bank, kl_fa_club, v2 files.

## Handover, step 3c (2026-10-17): the chain, the delivery and every check (OFFLINE, NOT RUN IN THE GAME)
Delivered: `<work>/build/hasta_1017/M11B/` (slot-named `F01_Main.zip` + the 18 side files + `KLGuns.ini` (Version 2) + `KLWardrobe.ini` + `van.json`, `bots/dyn/guns/map_guns.json`, `checks/`, `chain_logs/`); the bare map before the chain beside it as `M11B_bare` (kept for a new chain). Nothing installed, no game, no commit.
Command: `python tools/kl_fa_hasta.py chain <out> [--start N] [--plates] [--armour 0,3]` (9 steps, about 6 min), then `python tools/kl_fa_hasta.py checks <folder>` -> `checks/summary.txt`. Chain: layer `test --keep` (doors + layer) -> lighten (trim,slim,fxc) -> wardrobe -> compact -> `kl_fa_bots.py build` (bank's BOT_OPT: stops 1, cases glass, lane, window, 30 s loot wait; no Hasta recipe: GUESS) -> `kl_map_guns.py build` -> lighten --load fxc -> `kl_fa_bots_dyn.py build` (LAST) -> `kl_fa_bank.py seal`.
MEASURED (checks/summary.txt): F01_Main.zip sha1 `7f9331411dee4a097f57b72d0da53d8c640eb125`, 263,691,899 bytes; chunk table 60,242 (limit 73,728, tools 69,632); .prm 84.0 MB; .TEX 293.4 MB; 20,958 nodes. kl_impact `problems: 0`; reverify 0; layer check PASS; kl_chars/kl_arms/kl_fa/kl_map_guns/kl_fa_bots(7 bots, PASS 0 FAIL 2 NOTE)/kl_fa_bots_dyn (PASS, 1 NOTE) OK; dyn fake-test PASS; route START -> van boarding FREE (226 m of mesh way).
CORRECTIONS to step 2/3b: (1) that `final` had NO side files (no KLWardrobe.ini), so `compact` did not know the wardrobe's roots and dropped its bodies (47,843 entries / 72.5 MB / 9,101 mesh chunks). With the side files the same compaction keeps them: 59,739 entries, 83.0 MB, 20,022 mesh chunks. The 84.4 / 72.5 MB figures of steps 2-3b are wrong; use 84.0 MB (this build). (2) the wardrobe + 4 plates (`--plates`) came to .prm 91.0 MB (compacted) and the full 4 armour levels to 90.6 MB: both past the 90 MB GUESS edge; the delivery uses `--armour 0,3` (leaves two body meshes out; KLWardrobe.ini says so). Retomoto ran live at 79.9 MB, so 84.0 is above anything proven: if the first load trips 0x8e5bbd (large block refused), cut the wardrobe further (`--armour 0` only).
Known lines, not new: (a) 6 stream clips missing from the merged PC_Def.str (audit + preflight count it as 'CRASH 1/verify 1 problem'; silent music only). (b) `van-check` 1 fault: the .HVK is 5,003,424 bytes, 1,296 over 5,002,128 (the largest that has loaded, Retomoto - a measurement, not a limit; GUESS that +0.03 % is fine). (c) result.json carried the bare map's stale chunk-table line (74,763); `checks` moved it to `problems_at_bare`. (d) fa.check lists no active escape vehicle: the van is hidden until the alarm, as designed. (e) the bare graft keeps F07's money pool: audit counts 133 money objects / 8.16 M; the 16 layer places are the extra ones the round is designed around.
NOT done: talk (`kl_fa_talk` has scene tables for retomoto/M01/M02/M03/M06 only, no M11: needs a Hasta table; no KLTalk.ini); `kl_map_ai retomoto-style` (its spawnfix wakes every squad, which would defeat the three-stage release of the layer: left out, GUESS that the layer's soldier rows are enough); kl_hud (menu/overlay fonts, nothing per map); no KLJoin.ini (the mesh has 19 parts / 6 links; the bots' route does not need a join, `route walk` FREE); the timer-driven corner blast of 3b; the run-time locked-loot beat; no slot/menu entry (another session).
FIRST LIVE RUN MUST SHOW: (1) the level loads at all (the compacted-with-wardrobe base has never been loaded; if it dies in the load, run `proof-pair` first); (2) 8 heisters at x 33,900-34,000 facing +x, wardrobe/guns pages working; (3) the six gallery squads wake ~2 s in, nothing else before the box at the wing mouth; (4) the sunk switches are really open (loot wing, bunker wall, corner, barricade) and the wreck is gone - note CornerBroken_01 / BarricadeB_Broken01 untouched; (5) the stair-top box fires the street squads + alarm; 8 s later the van arrives at (25600, 2, 21800) and the exit line works; (6) police come to the square, AI heisters walk (bots 1083 squad nodes) and take loot; (7) KLHook.log: no 0x8e5bbd, no 0x607272.

## 2026-10-17 handover, review fixes (loot reach, TEAM_MERC1 spawns)
Both findings were RIGHT (reproduced with `kl_route.py stations`). Fixed in `tools/kl_fa_hasta_layer.py`:
(1) `LOOT_FIX`: the three painting places the 110 shift left unreachable (p1, p2, p3) are now MEASURED reached points by grid probe: (39800,31125), (40400,32255), (40400,31575) (gap 11 to the walk; the other 13 places unchanged). (2) `STAGE_B` (TEAM_MERC1) no longer starts at WING_DOOR (inside Collapsed_Walls_001/002): (39430,31415), (39510,31415), (39430,31495), (39510,31335) - on the mesh, in no object, reached from START. WING_DOOR itself still serves the camera / trigger / JumpPoint (a JumpPoint in a wall is a position marker, not a spawn; GUESS that is harmless).
`check()` now also runs `kl_route.stations` (loot at near 125 from START; STAGE_B/C/D at near 60, none may stand in an object) so PASS no longer hides this. STAGE_C/D pass too.
`kl_fa_hasta.py chain`: the `9_seal` step no longer drops its own delivery folder first (that bug made the seal fail with FileNotFoundError and lose the build; seal works in place).
Rebuilt (chain, ~6 min) and replaced `<work>/build/hasta_1017/M11B` (old one deleted; chain logs in `M11B/chain_logs_r2`). `checks`: impact 0, reverify 0, layer_check PASS, bots/dyn/guns/chars/arms OK; van_check 1 fault, audit FAIL 2 and preflight CRASH 1 are the known 6 missing stream clips / HVK +1,296 bytes lines, unchanged. Stations on the final level: 16/16 loot reached, 4/4 STAGE_B clean. Not run in game; not committed.

2026-10-17 15:40 - Stream file rule (from kl-merge-3f, commit 9ca1dd0a, tools/kl_v2_str.py): if Hasta ever gets its own PC_Def.str extension for its 6 missing music / ambience clips, build it ON TOP OF C:/kl_build/v_v2/PC_Def.str (v_club + Dead Men M01_A / M06_A blocks, every old offset kept), so Hot Coffee II (DM01B) and Hasta share one installed file. Nothing of v_v2 is installed yet (game has v_vault).

## 2026-10-17 handover, talk (voice lines) - OFFLINE, NOT RUN IN THE GAME
`tools/kl_fa_talk.py` has an `M11` table (aliases M11_B / hasta / DM11B; source campaign level M11_B; `HASTA_STAIR` box). 15 Dead Men lines, 11 scenes (5 names), ALL streamed IMA ADPCM
(they move into the level's .WAV; StreamBytes=0, so the installed PC_Def.str serves; Lynch's interleaved 'pcm set' lines are left out):
start (Start +9 s): K Intro_030 / L Intro_040 / K Intro_050 (Kane only: StormingElCap_010; Lynch only: Intro_020); inside (Stage1 = wing entered, +4): L FightLibrary_010 / K FightLibrary_030
(K StormingElCap_020; L MeetCarlos_110); out (Stage2 = wing left, +1): K EntranceSquare02_010 / L Courtyard_010 / K Courtyard_020 (K +SaveMen02_070; L Courtyard_010); alarm (Box = the stair top,
NotBefore 20 s, Kane): K OLMortar_010 'MORTAR! Let's move!'; van (Aboard +0.5, Kane): K SaveMen02_060 'Good. Let's go.'. Plus the shared chatter pools / pairs of every talk build (Kane 22, Lynch 23, Any 13, squad 20+20 keys, 7 pairs).
Build (copy, M11B untouched): `<work>/build/hasta_1017/M11B_talk` via the voice2r wrapper (build_talk.py pattern; only F01_Main*, the .ini files and the small .json of M11B copied), stream file `build/v_bain/over_talk/PC_Def.str`
(= the installed size 1,694,610,488). Growth: .prm 0 (84,009,648), .ANM 0, .fxc 0, .WAV +671,744 (23,026,000 -> 23,697,744), .WHD +2,480, .SND/.LOC in the zip +7,335 bytes archive (263,692,114 -> 263,699,449), bank sounds 4777 -> 4792, waves 4635 -> 4650.
Checks (`kl_fa_hasta.py checks M11B_talk`): same as M11B (impact 0, reverify 0, layer PASS, van 1 fault, audit/preflight the known 6 stream clips, fa/arms/chars/guns/bots ok) EXCEPT `dyn` FAIL: 'a large block changed its size' = .WAV grew,
compared with dyn.json big_before (expected, not a defect). kl_fa_talk check FAIL 0 (NOTE: the 300 s backstop timer is read as a blast timer, no countdown scene). Bank walk clean, 8 .LOC round-trip with 15 KLTalk leaves.
ASSUMED/GUESS: which line suits which moment (by the texts); the stage = event mapping (Stage1 enters the wing, Stage2 leaves it); the alarm box (kl_fa_hasta_layer.FLOOR_BOX, GUESS) and its NotBefore 20 s; Start +9 s as the other maps;
Kane=9 / Lynch=10 from KLWardrobe.ini; the stream-vs-memory ADPCM decode of memory clips as the other talk builds (heard live on DM05A only through the hook's say call). Needs the KLTalk hook part (kltalk.c) installed to be heard.

## 2026-10-17 handover, the corner blast (flag `--blast [S]`; OFFLINE, NOT RUN IN THE GAME; nothing committed)
New `tools/kl_fa_hasta_blast.py` (selftest / check), hooks in `kl_fa_hasta_layer.py` (global BLAST_AT, None = off; `test ... --blast [S]`) and `kl_fa_hasta.py chain <out> --blast [S]` (S default 1.5 s). Built the kl_fa_blast way (re/retomoto_blast.md), no bomb: F07's six spare shutter boxes (the same six Retomoto uses) re-placed at the Capitol corner marker (32095, 888, 29022), +1 spare TriggerDelay2 (`Shutters!TimerShuttersClose_RIGHT`) as the BLAST TIMER (NOT `TimerShuttersOpen`: the AIMonitor names it and it would switch the van on at 0 s). Timer (1.5 s, named by the AIMonitor) -> fan (AIDWrapper 'Activate' + DocuCamControl OnExplosion) -> cloud (Explode, FX_Grenade_RPG_01 + the rocket's sound), spray (Rocket_Default_01 blowing into the hall + ShakeCamera 3.0 / 8000, shake factor 0.76-0.95 at the START rows, Subway 0.70), dust s / dust n (Concrete_02 either side of the hole; Retomoto's glass jets would be wrong on a wall), second (off). Explode / ShakeCamera cloned from Rocket_RPG7, reach 1/1, tinnitus 0: nobody is hurt.
Default identical: the layer step without the flag gives F01_Main.zip md5 b9425458 for both the HEAD layer (git show) and the edited one (van.json differs only by its folder path). Chain with the flag -> `<work>/build/hasta_1017/M11B_blast` (F01_Main.zip md5 5e4f787c, sha1 280d82db; chain_logs beside; the bare before the chain as `M11B_blast_bare`). M11B / M11B_bare untouched (M11B md5 f44a4048).
.prm growth: 0 bytes (84,009,648 both; chunk table 60,242 both): the clusters, templates, sprites and textures were already in F07's systems and survive lighten/compact. .prp +2,060, .gms +160 bytes; .buf/.oct/.rmc/.rmi differ only because 7 more kept nodes move the slot ids (expected). 20,967 nodes (+9).
Checks (`kl_fa_hasta.py checks`, now adds `blast` when van.json has BLAST_AT): impact 0, reverify 0, layer_check PASS (incl. new blast check: timer/monitor/fan chain, harmless values, nobody else names the boxes, 3 particle groups followed to sprite+texture, clone-group pools, rocket sound 407600 inside the .SND), bots / dyn / guns / arms / chars / fa ok; van_check 1, audit FAIL 2, preflight CRASH 1 are the known HVK +1,296 bytes / 6 stream-clip lines, unchanged.
ASSUMED / GUESS: all offsets from the marker, "inward" = towards the middle of the START rows, BLAST_AT 1.5 s, the matrix layout of the +Y-to-arbitrary-direction turn (Retomoto's OUT yawed; proven live only for +x), fireball on a tank shell, whether the Shutters boxes' ZBoxPrimitive keeps working once the script is dropped (Retomoto: yes), rocket sound offset valid in the joined .SND (read from the joined scene; check confirms it is inside), the CornerBroken_01 model is still not shown (the hole is the sunk corner, as before). LIVE TO LOOK AT: at 1.5 s fireball + dust + debris at the hole, camera shake, no damage; KLHook.log clean.

## Handover, load crash at 0x4c63f2 (2026-10-17): orphaned clone groups (OFFLINE, fix NOT RUN IN THE GAME)
Crash: Hasta M11B (zip f44a4048) in the F01 slot, c0000005 at kl2 0x4c63f2 reading 0, 0.3 s after state 0x12 -> 0x15. 0x4c63b0 is ZParticleEmitter vtable slot 0x154 (4th init stage, run by 0x7f3b80; 0x88cb30 is the child recursion). It asks the parent ZAllocMany: `[+0x5e]` set (a copy) -> `[+0x58]` (template pointer) -> calls through it. Faulting node `Emitter_Spark_02`.
Cause (two independent triages agree): M11B kept two clone groups whose templates were dropped. `+0x58` is written only by the template's own init (0x48e1b0, re/combat.md 1.2), so the copies keep 0.
- `CloneGroup_ROOT/Effects/010_MarketSquare/Artillery/Artillery_Impact_Group` (5 copies, 21 emitters each, 111 entities): the crash.
- `CloneGroup_ROOT/050_Rooftop/Helicopter/HelicopterSquad/V_CUB_Hind_Placeholder_Group/Shards_Group_A` (1 copy, 9 entities, no emitters): harmless but removed too.
Why: the templates are top-level `Effects!010_MarketSquare!Artillery!...` / `050_Rooftop!Helicopter!...` (scripting, dropped by `kl_maps.campaign_drop`); `kl_prpjoin.templates()` reads only '/', so it never links a '!' template to its clone group and calls the group 'map'. The "proof pair" did not cover this: it was Retomoto + wardrobe, not M11B; M11B_bare had the same orphans.
Fix (builder, `tools/kl_fa_hasta_layer.py`): `orphan_clones(LEVEL)` lists clone groups that hold ZAllocMany copies and have no template once the campaign drop is applied ('!' read as '/'); `build()` adds them to `m_drop`. `check()` now FAILS on any such group in the built scene (`orphan_clones(LEVEL, sc)`); it flags the old M11B (both groups) and passes the new one. Other maps' builders (kl_maps.campaign_drop, kl_prpjoin.templates) are NOT changed: DM03A and T01 installed maps carry the same kind of Shards_Group_A orphan (not rebuilt, no emitters).
Rebuilt: `<work>/build/hasta_1017/M11B_fix/M11B` (chain defaults, no blast), F01_Main.zip md5 c23cb618, sha1 61ecfc90, 20,840 nodes (-120 vs before), chunk table 60,101, .prm 83.7 MB. `checks`: impact 0, reverify 0, layer_check PASS (incl. the new check), fa / arms / chars / guns / bots / dyn / mapai ok; van_check 1, audit FAIL 2, preflight CRASH 1 are the known HVK +1,296 bytes / 6 stream-clip lines. Independent scan (scratchpad s9 orphans()): 0 orphans.
GUESS / still open: this is the first M11B with the orphans gone, never loaded; the next first-time problem, if any, comes after it. 48 clone groups (BulletImpacts, WeaponsEffects) have their template after them in scene order: not proven harmless (earlier grafts with that order loaded). The Hasta proof pair was another map. The 120 dropped entities were effects (artillery impact, helicopter shards) nothing in the FA layer names.

## 2026-10-17 handover, locked loot beat (flag `--lock-wing`; OFFLINE, NOT RUN IN THE GAME; nothing committed)
Built the Retomoto main-room way (squads' dead list -> TriggerCounter -> geometry switch) with the campaign's own switch. `python tools/kl_fa_hasta.py chain <out> --lock-wing` (or `kl_fa_hasta_layer.py test <out> --lock-wing`). Build: `<work>/build/hasta_1017/M11B_lockwing/M11B`, F01_Main.zip md5 dcd6783b, sha1 4a7c2d29, 20,842 nodes (+2: opener, counter vs c23cb618's 20,840), chunk table 60,101, .prm 83.7 MB (0 growth: no new geometry).
What it does: the loot wing door block (`End_Corridor_01a\ColiObj_Obj_Roadblock_01`), the bunker wall (`SI0100_M11_BarricadeB_01`) and the check block (`M11B_OYCHECK_BEFORE01`) are NOT sunk at build time (Doors gets `switches()`; the Capitol corner and stair barricade stay sunk, as before). The campaign's top-level `070_CapitolioInside!Enemies!GeomDeactivatorSandbags` (a DeactivateGeom, kept by `campaign_names` under the flag) gets those three nodes as targets (the wing door block's own deactivator sits inside the LastSeven squad, which is not kept, so its target is added here). F07's spare `Gameplay!020_Loot!FollowPlayers!TriggerCounter` (kept under the flag) counts the 6 'start' hall squads: each squad's dead list names it; count 6 -> the opener. The 300 s backstop timer names the opener too, so the wing always opens. `check()` reads the folder (lock_present) and then asks: three nodes in place, chain squads -> counter -> opener -> nodes, nobody else names the counter/opener, backstop opens; reach and stage-spawn checks run with the three nodes OPENED (kl_route `opened=LOCK_OPEN`). Default (no flag) unchanged.
Default identical: fresh chains from a HEAD worktree and from the edited tree both give F01_Main.zip md5 c23cb618 (= M11B_fix), WAV/WHD/KLGuns/KLWardrobe byte-identical.
Checks (`kl_fa_hasta.py checks`): impact 0, reverify 0, layer_check PASS (incl. orphan-clone check and lock-wing), fa/arms/chars/guns/bots/dyn/mapai ok; van_check 1, audit FAIL 2, preflight CRASH 1 = the known HVK +1,296 bytes / 6 stream-clip lines, unchanged.
GUESS: (1) a DeactivateGeom run at run time on a static ColiObj whose HVK placements stay does open the passage (the campaign does it with the same controller on the bunker; not shown for the door block, whose own deactivator we replaced); (2) f0 'AITrigger' kept as the campaign's value; (3) a squad's wiped-out list fires TriggerCounter once per squad (as Retomoto's main room does); (4) the 'start' squads (6) are the ones whose death should open the wing, not only the bunker pair; (5) the three nodes are in no cluster change: ordering/REF ids move only by the +2 kept nodes; (6) LOCK_OPEN path match by substring; (7) the .HVK keeps the three nodes' placements (not cut), so the shut state is physical until the deactivator fires. The wing door is also the route to the loot for the bots: bots start while it is shut (they wait for the beat or the backstop; not checked). LIVE TO LOOK AT: wing shut at start, guards dead -> sandbags/door open, backstop at 300 s, no BoomBox dust/wall swap yet (open: bunker model swap + dust).

## 2026-10-17 rebuild of the add-ons on the orphan-fixed base (OFFLINE, NOT RUN IN THE GAME, not installed, not committed)
The old M11B_talk / M11B_blast sit on the pre-fix base (load crash at 0x4c63f2) and were KEPT (disk had 5.8 GB free, still 4.1 GB after; nothing deleted). New folders under `<work>/build/hasta_1017/`:
- `M11B_fix_blast/M11B` (chain --blast): F01_Main.zip md5 d3291097, sha1 dc25e475, 20,847 nodes; WAV f9f3b329, WHD 2f6035cd, LS.SND 947153a1, KLGuns.ini 1c1ad77a, KLWardrobe.ini 405f7937.
- `M11B_fix_talk` (M11B_fix + kl_fa_talk M11 via voice2r/scripts/build_talk.py, stream file build/v_bain/over_talk/PC_Def.str): zip cba4e5bd, sha1 363742ff, 20,840 nodes; WAV dd5b2c37, WHD b014ed19, LS.SND 25ff1a6c, KLTalk.ini e4455b1c, KLGuns/KLWardrobe as above.
- `M11B_full` (chain --blast --lock-wing, then the talk pass; the chain output before talk is `M11B_full_pre/M11B`, zip dd6b2071, sha1 7a552f04): zip 75c6be55, sha1 5c995007, 20,849 nodes; WAV dd5b2c37, WHD b014ed19, LS.SND 25ff1a6c, KLTalk.ini e4455b1c.
Chunk table 60,101, .prm 83.7 MB in all. Checks (`kl_fa_hasta.py checks`, logs in build/hasta_1017/logs/chk_*.log): impact 0, reverify 0, layer_check PASS (orphan-clone check included; blast check on fix_blast, full; lock-wing on full), fa/arms/chars/guns/bots/mapai ok; van_check 1, audit FAIL 2, preflight CRASH 1 = the known HVK +1,296 bytes / 6 stream-clip lines. The two talk folders: `dyn` FAIL (WAV grew, expected) and kl_fa_talk check FAIL 0 (one NOTE: the 300 s backstop is read as a blast timer). Talk folders carry the small side jsons copied from their chain output.

## 2026-10-17 handover, lock-show: the bunker blast of the locked-loot beat (flag `--lock-show`, needs `--lock-wing`; OFFLINE, NOT RUN IN THE GAME; nothing committed)
The open item named by the lock-wing handover ('no BoomBox dust / wall swap yet'). `python tools/kl_fa_hasta.py chain <out> --lock-wing --lock-show` (or `kl_fa_hasta_layer.py test <out> --lock-wing --lock-show`). Build: `<work>/build/hasta_1017/M11B_lockshow/M11B`, F01_Main.zip md5 640378b6, sha1 09e87db6, 20,847 nodes (+5 vs M11B_lockwing's 20,842), chunk table 60,101, .prm 83,712,224 (83.7 MB, 0 growth: only scripting nodes are added; the chain's `bots` check prints the same large-block size as M11B_fix).
What it does: the campaign's checkpoint 'SevenDudesDead' fires two timers; both are kept whole (top-level scripting the campaign drop would take; `campaign_names` under the flag) and the beat now sets them off instead of naming OPENER alone: `Enemies!Timer_SandbagsDeactive` (-> `GeomActivatorSandbagsRemains` shows `SI0100_M11_BarricadeB_Broken01` + `M11B_OYCHECK_AFTER01`; -> OPENER, which already carries the 3 locked nodes; -> `GeomDeactivatorExplosiveStuff` removes 2 barrels + `Collapsed_Crates_003`) and `Enemies!Timer` (-> `GeomActivatorDustExplosion` switches on the map's `Capitolio_Explosion` group at (38,797, 800, 30,415): 6 debris, 4 fireball, 2 flash, 6 smoke emitters + 1 light, all hidden at load already). The 6 hall squads' counter and the 300 s backstop both name the two timers. `BoomBoxDust` is NOT kept (an Explode with an EMPTY effect name: nothing to show; see BLAST). No node is rewritten except the counter's and the backstop's target lists (the campaign nodes keep their own values, delays and 'AITrigger').
New code (layer): `LOCK_SHOW`, `SAND_TIMER`, `DUST_TIMER`, `SHOW_NODES`, `beat_fires()`, `show_wire()` (at build: single top-level nodes + the chain read back, else ValueError), `show_check()` / `show_present()` (on the folder: timer -> remains / OPENER / barrels, timer -> dust activator -> >= 10 emitter/light names, none dangling, emitters hidden at load); `lock_check` asks the show chain when it is present (counter holds exactly the two timers, backstop names both, only the known owners name them). `flags_of` records LOCK_SHOW in van.json.
Default identical: the layer step (`kl_fa_hasta_layer.py test --keep`) from a HEAD worktree and from the edited tree gives F01_Main.zip md5 36ab6a82 both without a flag, and b66cd37f both with `--lock-wing` (no `--lock-show`). The full default chain from the HEAD worktree gives c23cb618 = M11B_fix; the edited tree's full default chain stopped at 'STOP: 2.9 GB free' (G: nearly full, MIN_FREE_GB 4) before its seal step, so the whole-chain default of the edited tree was NOT compared (steps 2..9 do not read the flags; step 1 is the compared one). The scratch builds were deleted to make room (M11B_fix, M11B_lockwing, M11B_talk/blast, full* untouched).
Checks: `kl_fa_hasta.py checks` on the folder: impact 0, reverify 0, layer_check PASS (lock-wing + lock-show lines), fa / arms / chars / guns / bots / dyn / mapai ok; van_check 1, audit FAIL 2, preflight CRASH 1 = the known HVK +1,296 bytes / 6 stream-clip lines. `python debug/check_passes.py <folder>`: PASS A (3636 type-7 roots, 2927 .oct records), PASS B (163 clone groups, no orphan), PASS C1 / C2 / C3.
GUESS: (1) the campaign's timer delays and message ('AITrigger') are right for Dog Days' TriggerDelay / ActivateGeom / DeactivateGeom (same classes, values unchanged); (2) un-hiding the Capitolio_Explosion emitters makes them play in Dog Days (the Retomoto/Hasta blast uses emitters from clone templates; these are the map's own); (3) Broken01 and AFTER01 are NOT hidden at load in the built level (flag and ZGEOM[3] equal to their intact siblings): the campaign evidently shows them from the start, so ActivateGeom's visible effect on them is unknown (may switch collision only); not hidden by this flag; (4) GeomDeactivatorExplosiveStuff removing the barrels / crates is wanted in FA (the campaign's own explosion does it); (5) one dust beat per round: the counter fires once, the backstop may fire it again at 300 s (re-activating emitters again: harmless?); (6) the dust may play at the bunker with the crew still in the hall (the beat is 'six squads dead', not the campaign's SevenDudesDead checkpoint). LIVE TO LOOK AT: wall/dust/smoke at the bunker when the hall is clear, barrels gone, wing open, no crash at load (the new nodes are scripts only; the emitters were in the lockwing build already).

## Handover 2026-10-18 (kl-merge workflow, track 4): the second objective, "you fall to your death"

Owner 2026-10-17: "you cannot reach the second objective point, you fall to your death". Second objective = the van / escape area (`POI_TheEscapeArea`, exit box at (25263, 0, 21800)).

Finding (static, from `kl_route.py walk ... --hidden-out`, NOT yet seen live): the corner-hole route (START row y 800 -> HOLE (32095, 888, 29022) -> street) stands on
`SO0201_M11_CornerBroken_01` (REF 23930), which the campaign HIDES until its corner blast; `Corner_01` (the intact corner) is sunk by Doors. The default walker counts hidden
collision, so every earlier route proof passed. With hidden collision left out, the shipped build (`build/hasta_1017/M11B_lockshow/M11B`) has NO WAY on both legs
(START -> HOLE: floors do not join; HOLE -> van: 93 floors reached) and its mesh way has 18 samples without a floor and 2 in a body column. If hidden collision does not collide in
the game, the crew drops from y 800 to the street (y 0..20): the fall. GUESS: that is the cause; the game's treatment of hidden collision was not read.

Fix: new flag `--corner-floor` (`kl_fa_hasta_layer.CORNER_FLOOR`; also `kl_fa_hasta.py chain ... --corner-floor`). Doors.repair sets the .prp `ZGEOM[3]=0` of `CORNER_FLOOR_NODES`, Doors.place clears the
.gms flag 0x400 (both, as `kl_fa_author.place` does). Corner_01 stays sunk. `check()` under the flag (`check <folder> --corner-floor`) walks START -> HOLE -> boarding place with `hidden=False`.
Proof on the built folder: both legs FREE (29 m + 157 m, floors y 800..873), mesh way 945 samples all free (kl_route walk --hidden-out).
GUESS to watch live: the shown piece does not close the hole itself (the walk and the mesh way pass through it with 0 blockers).

Builds (C:, G: has < 1 GB free; copy whole to `<work>/build/hasta_owner_1018/M11B_cornerfloor` when space exists):
- `C:\kl_scratch\hasta_owner_1018\M11B` = `chain --blast --lock-wing --lock-show --corner-floor`; F01_Main.zip md5 ccdde3e86a1816b06566f8c38d1d725a; .prm 83.7 MB (limit 84.0 proven live); layer check PASS,
  check_passes 0 failed. (3_ward `problems: 1` and 6_guns "6 stream clips" are the known expected lines.)
- Default unchanged: layer step built from a HEAD worktree and from the edited tree, F01_Main.zip md5 36ab6a823797a3870344bd6e03f860ad both.
- `kl_fa_hasta.py checks` reports layer_check FAIL on the OLD `hasta_1017/M11B` only (the pre-fix orphan clone groups Shards_Group_A / Artillery_Impact_Group), unrelated.

HELICOPTER escape: NOT built. Plan for the next agent: a Hasta R09 donor (F07 + M06_FA_A chopper tops) via `kl_fa_club.heli_*` globals, exit trigger naming the chopper group,
no `van_wire`, pad on the square (`SQUARE_Y` 20), bots parked at the pad, behind `--heli`; wiring must use the same fix as Last Call's `Incomming` rout (`re/heli_call.md`), which
has not reached its rout live. The van is wired into `prepare_host`, `wire`, `build` and `van_check`, so removing it is a larger change than this flag.

Review 2026-10-18 (adversarial): PASS. Copied whole to `<work>/build/hasta_owner_1018/M11B_cornerfloor` (md5 ccdde3e8 verified); default layer step re-built from a fresh HEAD worktree = 36ab6a82 both; CornerBroken shown (ZGEOM[3]=0, flag 0x400 off, HVK placement 23930 present), Corner_01 sunk (placement gone).
