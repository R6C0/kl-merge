# The prison (Dead Men chapter 8 'Breakout', M08_A) as a Fragile Alliance map - study

2026-10-11, agent cfa-prison. OFFLINE study: nothing was installed, the game was not started, no
existing tool or note was edited, nothing was committed. Scratch scripts: `G:/kl_scratch/cfa_prison/`.
Trial builds, logs and pictures: `<work>/build/cfa/prison/` (`<work>` = `G:/SteamLibrary/steamapps/common/
Kane and Lynch Dead Men/KL_PortTools`). Every archive that was built has been deleted again; the
`result.json` / `log.txt` / `graft.txt` of each step are kept.

Evidence labels: **MEASURED** = output produced in this job (the command is named), **READ** = code or
an existing note (file and place named), **ASSUMED** = fits the evidence, reason given, **GUESS** = a
coordinate or value of mine that nothing measured. Scene paths are written with ` > ` between a node
and its child. World units: 100 = 1 m; x runs west to east, z south to north, y is up.

Scripts of this job (all read-only on the game files; `python <script> M08_A ...` from any folder):
`dump.py` (property tree with world positions), `tops.py` (subtrees and rooms), `squads.py` (squads by
kl_fa_author's rule), `doors.py` (scripted doors / swaps and what they move), `props.py` / `roomprops.py`
(name census), `leftovers.py`, `kept.py` (what the campaign pre-pass keeps), `ctrlwhere.py`, `navlinks.py`
(mesh links and parts), `nav.py` / `nav2.py` (mesh pictures, stations, walking distances; they take a
level name or a kept build folder), `cut.py` (model chunks a part of the map needs), `music.py`.

## 0. The answer in short

- The prison is one level, M08_A, and it grafts: `F07 + M08_A` is written, 23,307 entities, and every
  offline check but two passes. **The two: the model file has 79,005 chunk-table entries against the
  game's 73,728 (a crash if installed as it is), and there is no Fragile Alliance layer at all.**
- The chunk limit has an answer that already exists as a tool but has never been loaded in the game:
  `kl_chars.py compact` brings the same build to 50,617 entries (63,528 with the full wardrobe), 0 problems.
- The level is walkable in **three separate pieces**. The campaign crosses between them by climbing
  (visiting booth counters, a stack of crates in the kitchen yard) and by a rappel; Dog Days has no climb
  clip, and no stock Dog Days level has a rappel. So "the campaign way" (1.4 km through all three) is NOT the round to build.
- One piece is a complete round by itself: **cell block B -> the 'birdcage' yard under the control tower
  -> the last gate -> two fences -> the car park -> out of the prison's entrance gate**, 206 m, one
  connected navigation piece from start to vehicle. That is the recommendation: a break-OUT called here
  'Cell Block B'.
- A prison has no money prop. Loot has to be dressed with props of the Dead Men Fragile Alliance maps
  (the park's dope bag as contraband, the diner's suitcase as the guards' cash): the method exists
  (`tools/kl_fa_loot.py`, made for Retomoto's briefcases).
- Verdict: **feasible-with-work**, about 0.7 of the Retomoto effort.

## 1. What the place is

### 1.1 Size and sides

MEASURED, `python tools/kl_maps.py what M08_A`, `python tools/kl_maps.py sides M08_A`,
`python G:/kl_scratch/cfa_prison/tops.py M08_A`:

- 21,373 entities. The whole map is ONE top-level subtree, `Locations/M08_A/M08A_Locations.zip`
  (9,625 nodes: `M08A_LOC_Inside.zip` 7,055, `M08A_LOC_Outside.zip` 2,569).

| side (kl_prpjoin.sides) | nodes | family | campaign pre-pass (`campaign_drop`) |
|---|---:|---|---|
| map | 9,744 | `Locations/*` (map 9,625, effects 116, post filter 3) | stays |
| map | 3,558 | `CloneGroup_Locations` | stays |
| map | 861 | `AI_Players!` (squads, inmates, choppers, the crowd) | dropped (1 cover box stays) |
| map | 636 | `CloneGroup_Effects` of map templates | follows its template |
| map | 370 | `Specials!` (triggers, objectives, checkpoints, actions, bounds) | dropped, 15 stay (section 3.5) |
| map | 301 | `CutScenes/*` (13 cut scenes) | dropped |
| map | 197 | `Hero!` (Kane, Lynch, crew squads, mini cut scenes) | dropped |
| map | 106 | `Locations/M08_A/M08A_Audio.zip!*` (ambience, speakers, door sounds) | stays |
| map | 77 / 51 / 48 | `Music!` / `M08_Backdrop_A_00` / `COOP!` | dropped / stays / dropped |
| map | 25 + 21 + 10 + 10 + 6 + 3 + 2 | effect templates, `Effects!`, `Ropes!`, `Cutscenes!`, `Audio!` | templates stay, the rest dropped |
| systems | 3,199 + 2,135 + 3 | `CloneGroup_Effects`, `AllLevels/mainsceneincludes.zip`, CoverList etc. | not taken (Dog Days' own are used) |

  The pre-pass drops 586 subtrees / 1,874 nodes and keeps 14,162.

### 1.2 Rooms (world extents of the model-holding entities; MEASURED, tops.py)

| part of the prison | rooms | x | z | y |
|---|---|---|---|---|
| visiting area (the campaign's start) | VisitingRoom_A/B, Room_A/B, BoothHallway_A/B_101/102, MiddleHallway_A/B, EntranceHallway_101 | 6800..12160 | -5036..537 | -25..1344 |
| block A entry | SecurityRoom, MiddleHallway, EntranceRoom, EntranceHallway | 1900..4531 | -3100..-298 | -40..711 |
| cell block A | Inside_Main + six Cells_* + Entrance_N/S | 498..4122 | -621..3914 | -300..2252 |
| cantina | Main_Cantina_101, MainHallway_101, Hallway_102/103/201, two staircases, Left/RightRoom | 100..4900 | 3894..9100 | -170..833 |
| kitchen / laundry (basement) | Kitchen_101, Hallway_101 / LaundryRoom_101, SmallRoom_101, StairCase_B_101 | 700..5075 | 8141..11805 | -609..390 |
| kitchen yard | Outside_KitchenYard | -7300..10137 | 3800..19300 | -111..2922 |
| **cell block B** | Inside_MainArea, Left/RightCorridore (upper ring), GuardRoom = control room B, Inside_Entrance | 5645..10909 | 12142..14654 | -50..1220 |
| **the birdcage** (central yard) and its **control tower** | Outside_BirdCage; StairCaseTop, StairCase, StaircaseHallway; GroundRoom_A (north passage), GroundRoom_B (south passage = the last gate), UpperEntrance_Left/Right | 5700..11228 | 5556..12178 | -960..2283 |
| **escape yard and car park** | Outside_Escape (505 entities), Outside_BlockB | 5670..14540 | 3468..19132 | -34..1984 |
| outside the walls | Outside_VisitingToEntry, Visiting_Parking_01, Escape_Parking_01, the backdrop | to 80173 | | |

59 map rooms + the backdrop are kept by the graft (the trial build has 61 rooms with F07's one).

### 1.3 Pictures (MEASURED; one pixel = 6..12 units, north up)

All in `<work>/build/cfa/prison/pics/`, drawn from the level's own navigation mesh (walkable floor),
dark lines = edges with nothing behind them:

- `nav_parts.png` - the whole prison, one colour per connected piece of the mesh (grey = block A side,
  blue = block B side, orange = visiting area).
- `campaign_route.png`, `b_side_campaign.png` - the campaign's 27 places in order, floors coloured by
  height (grey ground, green tiers, blue the walkway level y 920..1000, orange the tower top).
- `round_cell_block_b.png`, `round_route.png`, `round_loot.png` - the recommended round's stations.

Rebuild any of them: `python G:/kl_scratch/cfa_prison/nav2.py M08_A <out.png> <stations.txt> [x0 x1 z0 z1 scale]`.

### 1.4 The campaign's flow, rebuilt from its scripted objects

MEASURED: `python G:/kl_scratch/cfa_prison/dump.py M08_A <out.txt>` (5,303 lines; kept as
`G:/kl_scratch/cfa_prison/tree_M08_A.txt`), `doors.py M08_A MatPosAnimProxy PathBlocker`,
`doors.py M08_A AIDWrapper DeactivateGeom ActivateGeom`. Coordinates are the objects' own.

1. **Start.** `Hero!Hero_01_Suit` (Kane) at (10982, 174, -3523), `Hero!Lynch_COOP_01` at (11075, 108, -3392), in
   the visiting area. Intro cut scene `CutScenes/M08/M08_Intro.zip`: `V_USA_MonsterTruck_A_00` at
   (9699, -47, -9471) comes through the outer wall (`Emitter_Wall_Crash_01` at (9986, 305, -7300)); the group
   `Mostertruck` stands in Room_B_101 at (10898, 335, -4346).
2. **Objective 01 'find block A'** (4325, 34, -2173): over the counters of the visiting booths
   (x 8430..8565, z -3474..-1056; twelve windows `FX0001_M08_Win_Visiting_Booth_A_*` with a path blocker each,
   eleven counters with a mesh crossing), checkpoint 01
   (7436, 11, -2296), a steel door blown open at (4306, 7, -2200).
3. **Security room**: `Action_01_Entry_ControlPanel` (2221, 8, -1498) opens the cage door (3100, 8, -1000) and the
   two block A entry doors (2200, 8, -300 / -700).
4. **Cell block A**: objective 02c (2172, 64, 1107); the alarm shuts the block's 56 cell doors in timed groups
   (`MatPosProxy_BlockA_Startup`, `MatPosProxy_BlockAClose#01..05`); `Action_02_BlockA_Control` (2203, 390, 3261) in control room A, cut scene
   `M08_Controlroom`; `Action_03_Merc01Cell` (3063, 10, 234) frees Rific (cut scene `M08_Merc_01`).
5. **Cantina**: north door (2200, 0, 3899), checkpoint 04 (2592, 1, 4676), cantina doors (1000 / 3400, 0, 4900)
   and guard-room slide doors opened by a mini cut scene; fight at (4519, 5, 8566).
6. **Kitchen and laundry**: kitchen gate (4348, 0, 9721); `Action_04_Merc02Free` (1309, -436, 9675) in the
   basement frees Thapa (cut scene `M08_Merc_02`); checkpoint 05 (877, 2, 11054).
7. **Kitchen yard**: over stacked crates - up at (1790, 0, 13678), across a roof at y 383, down at
   (3575, 0, 12058) ('Music_17_HopDown').
8. **Cell block B**: objective 07 (5895, 14, 13414), west door (5758, -2, 13400); riot fires burn (15 fire
   boxes); checkpoint 06 / Shelly at (8169, 22, 12417) (cut scene `M08_Merc_03`); SWAT storms in behind the
   crew (`Squad_SWAT_StormBlockB`); upstairs `Action_06_BlockBControl` (10139, 931, 13327) in control room B
   (cut scene `M08_ControlRoom_BlockB`) opens the cage doors (8302, 20, 12223), (8300, 20, 11579),
   (8300, 21, 10527) towards the yard and the slide doors (10000, 920, 12235), (10000, 920, 11566),
   (9997, 961, 11034) of the upper way.
9. **The birdcage and the tower**: along the upper walkway (objective 10 at (9996, 910, 11943)) to the tower
   entry (9345, 973, 8206), up to the top; `Action_07_Tower_Kane / _Lynch` (9178 / 9128, 1926, 8795) = the
   button (cut scene `M08_Control_Tower`): it opens **the last gate** `GroundRoom_B > SI0301_M08_CageDor_C_01 / _02`
   (8299, 20, 7071) / (8299, 21, 6019); a police helicopter (`AI_Players!Chopper_ShootTower`, ZHeli with a
   Minimi) shoots the tower, the stairs burn (`Pathblocker_stairs`), the crew **rappels**
   (`Specials!Rappel_Points!RappelPoint!RappelBox` (9076, 2102, 8798)) into the yard, objective 12
   (8383, 3, 8809).
10. **Out**: checkpoint 09 at the last gate (8399, 22, 6295); objective 13 (8203, -28, 4960); armed prisoners
    knock down two fences, `Outside_Escape > SO0106_M08_FenceFalling_A_01` (9300, 0, 4900) and `_A_02`
    (9941, 0, 4913) (message 'FenceFall' = a key-framed fall + a collision swap); tower machine guns and
    tear-gas launchers fire into the yard; objective 14 the car park (12455, -1, 6921).
11. **End**: objective 15 (11566, -23, 11380); `Specials!Triggers!07_Escape!EndOfLevel!EndOfLevel`
    (`EndOfLevelTrigger`) at (11612, 33, 11477) beside the parked `Cars!V_USA_PrisonerTransport_A_Static_00`
    at (11600, -8, 11593). Cut scene `CutScenes/M08/M08_Exit.zip` (its own `V_USA_PrisonerTransport_A_Group_00`);
    the static transport and the entrance gate `Outside_Escape > SO0106_M08_Entrance_Fence_01` at
    **(14000, 0, 8800)** are switched off, next scene `Locations/M09_A/M09A_Main.zip`. So the campaign leaves
    in the prisoner transport, through the gate in the east wall between guard towers 01 (14000, 0, 7800) and
    03 (14000, 0, 9799).
    (corrected by the second agent: (14000, 0, 8800) is the ORIGIN of the fence piece, not where it stands. MEASURED on the
    .HVK triangles, `skeptic/lanetri.py M08_A 10800 16000 8800 110 40 220` and `skeptic/lanebox.py`: its collision
    crosses the lane z 8800 at x 13226..13300 only; the piece is a fenced lock x 13226..13936, z 7781..9817 (static,
    type 1) INSIDE the wall. The wall's own opening at x 13958..14041 carries `Entrance_Open_03 / _04`, which are
    clear below y 350. The towers' origins are as given. See 'Verification (second agent)', the gate.)

Walking distance of the legs that exist on the mesh: 1,434 m (MEASURED, nav2.py with
`stations_campaign.txt`); three legs do not exist at all (section 3.3).

### 1.5 Who is in it

MEASURED, `python G:/kl_scratch/cfa_prison/squads.py M08_A` (kept as `squads_M08_A.txt`):

- 84 subtrees hold a squad controller, 175 actors.
- **Guards**: 105 enemy actors (`ZFFActor` + `ZSoldier`; profile eGuard / eRegular 77, eGuard / eVeteran 24,
  eThug / eAmateur 4; animation set Army on 101). By chapter part: entry 10, block A 17, cantina 10, kitchen and
  laundry 16, outside snipers 3, **block B 20, birdcage 18, escape 11**.
- Weapons Dead Men gives all 175: MP5 64, Remington 870 43, Mini-14 33, USP 24, Minimi 4, Remington 700 4,
  tear-gas launcher 3, M4A1 1.
- **Inmates**: 60 actors under `AI_Players!Civilians!` - 53 inmates (most `ZCivilian`, unarmed; 14 of them on
  the tiers of block B) and 7 visitors (`USA_civ_prison_vis_Female`) - and 9 armed allies in three squads
  (`AI_Players!Allies!PrisonerSquads!*`).
- **The riot crowd** is not people: six `ZHFlowFF2M08` flow objects (`AI_Players!Crowd01 > HumanFlow_01..06`,
  driven by crowd maps `Scenes/Locations/M08_A/m08crowdmap_NN_NN.tga`) and six `ZHFlowLnkObj` models with
  `Animation/Crowd/M08_Crowd.xanm`. Both classes exist in kl2.exe and no stock Dog Days level uses them
  (MEASURED, `python tools/kl_maps.py first M08_A`: '0 in NO LEVEL'). The pre-pass drops the crowd.
  ASSUMED not carriable without research of its own (a level-specific class, a second animation format).
- **Two police helicopters** (`ZHeli` + `HeliWeapon` + `HeliFlyBehaviourRout`): the only vehicle classes in the
  level ('escape / loot: {ZHeli: 2}'). Every car is static scenery (28 `Cars!V_USA_Sedan_A_Group_*`, the
  transport) or a cut-scene object.

### 1.6 M02_A 'Trial' and M01_A 'Impact' - prison places?

MEASURED, `python tools/kl_maps.py what M02_A` / `what M01_A`: no. M02_A is a three-storey atrium building
(rooms Atrium / Corridore / Hallway 101..301, words 'Shop' 405, 'escalator'): the mall. M01_A is streets,
alleys, a junkyard, the diner, the donut shop and a warehouse; its only prison thing is the 15-entity room
`M00_transport` (the transport truck of the opening).

## 2. Leftovers of a planned Fragile Alliance version

MEASURED, `python G:/kl_scratch/cfa_prison/leftovers.py M08_A` (kept as `leftovers_M08_A.txt`): **none in the level.**

- Map side: 0 `ZSpawnPoint`, 0 `Online*` controllers, no `eSPAWN_TYPE_*` value, no name with FA / Online /
  DL0 / Multiplayer. The one name hit, `PosObject_PIP`, is a mini-cut-scene position of Shelly.
- .TEX: `UserInterface/UI_FA_Respawn_pip_mask` (a HUD texture of the systems side). .ANM / .prm: only
  `fa_*` face bones and `Vehicles/Jeep#FA_Stand_Leave`. .SND: only the crew member 'Vaultbreaker'.
  (corrected by the second agent: the .SND also names eight `Dialog/Multiplayer/FA_Menu/Fragile_Alliance_0N.wav`, the menu
  announcer of the systems side - no map leftover; MEASURED `skeptic/leftchk.py M08_A`. The finding 'none' stands.)
- .LOC: `BriefingDL03` = 'Briefing DL03 - Prison' is in M08_A's text - with DL01..DL09 and the whole online
  menu: the shared menu text every level carries, a placeholder, no briefing.
- One real link, outside the level: Dead Men's own Fragile Alliance music is
  `Music/InHouse/FA_Slash/FA_SlashMixPrison.wav` (251.6 s; MEASURED `python tools/kl_str.py list <DM>/PC_Def.str
  SlashMix`; READ re/fa_gamemode.md 0.5: Dead Men's Fragile Alliance settings field 150 = `fa_all/music/fa_slashmixprison`). IO cut its
  Fragile Alliance theme from the prison chapter's music, and that clip is already in the merged
  `<work>/build/PC_Def.str` (MEASURED, same command on that file).

## 3. Can it be grafted

### 3.1 The trial graft

MEASURED, `python tools/kl_maps.py one "<work>/build/cfa/prison" F07 M08_A --campaign` (82 s; a second run
with `--keep` for the checks below; `result.json`, `log.txt`, `graft.txt` in
`<work>/build/cfa/prison/F07+M08_A campaign/`):

| | F07 + M08_A | Retomoto (READ re/retomoto_fa.md 0, re/prm_limit.md) | limit |
|---|---:|---:|---:|
| written | yes (`ok: true`) | | |
| `kl_graft.verify` problems | **12** = 1 limit + 1 sound + 10 FA | 2 known | 0 |
| entities / rooms / gates | 23,307 / 61 / 242 | 25,490 / 22 | (stock L10: 42,915 entities) |
| textures / materials | 1,964 / 1,286 | 2,195 / 1,429 | 4,096 / 2,048 |
| sounds / waves | 4,745 / 4,589 | 4,941 / 4,766 | (stock max 4,806 / 4,568) |
| **.prm chunk-table entries** | **79,005** | 65,119 | 73,728 hard, 69,632 the tools' limit |
| archive | 329 MB (190 MB lightened) | 331 MB (212 MB) | |

The 12 problems (result.json): the chunk table (3.2); '11 stream clips are not in the merged stream file'
(four lockdown announcements `Dialog/M08/Dialogue/M08_OneLiners/M08_Lockdown_Effect/M08_Lockdown_0N0_Effect.wav`,
seven ambience beds `SFX/Ambiences/M08_A/...` - silent, not broken); and ten Fragile Alliance findings that only
say the layer is missing (0 settings object = CRASH at the first death, no define, no exit trigger, no START /
AFTER_DEATH points, no ENTERS / EXITS / BOARDS triggers, no loot, no squads). 0 dangling scene paths, 0 misfits.

`python tools/kl_maps.py preflight "<build>"` (kept as `G:/kl_scratch/cfa_prison/preflight.txt`): CRASH 2 (the
two above), RISK 14, NOTE 66; every structural check 'ok' (self-deleting events, 210 KEYS chunks, controller
owners, torn streams, lights, shaders 0 of 1,286 without a compiled shader, 61 rooms / 242 gates / 127 neighbour
lists followed, .sgd sections, FDX).

### 3.2 The chunk table: the one hard limit, and what gets under it

- MEASURED: 79,005 entries; `python tools/kl_impact.py "<build>"` -> 'the loader writes 5277 pointers over the
  globals behind it'. READ re/prm_limit.md: entry 73,932 is the loading-progress object, the crash of run P4.
  Cause: F07's whole file (35,102 entries, MEASURED on the stock archive) + 43,848 chunks of the prison's map
  (log.txt); the prison's map is larger in models than any map grafted so far.
- **Compaction** (MEASURED, `python tools/kl_chars.py compact "<build>" "<out>"`, log in
  `<work>/build/cfa/prison/compact/log.txt`): 79,005 -> **50,617** entries, .prm 64.2 -> 62.4 MB, 13,430 .gms and
  15,165 .prp references rewritten, 'problems: 0'; `kl_impact.py` on the result: 0 problems.
- **With the wardrobe** (MEASURED, `kl_chars.py wardrobe "<build>" "<out>"` then `compact`; logs in
  `.../wardrobe/log.txt`, `.../wardrobe_compact/log.txt`): the wardrobe takes 15,509 of 24,323 dead indices,
  the table stays 79,005 and the .prm grows 64.2 -> 80.4 MB; compacted **63,528** entries, .prm 79.5 MB,
  0 problems, `kl_impact.py` 0 problems. That is 6,104 under the tools' limit - with all sixteen bodies.
- READ re/prm_limit.md ('Compaction'): the tool is proven offline on Retomoto and **never loaded in the game**;
  it renumbers the systems level's live chunks, which no build that ran has done. So the limit is a missing
  LIVE PROOF, not a missing converter.
- The other way, not written: **cut the map** to the block B side. MEASURED,
  `python G:/kl_scratch/cfa_prison/cut.py M08_A "LOC_INS_Block_B\.zip|LOC_INS_BirdCage\.zip|M08A_LOC_Outside\.zip"`:
  of the 44,776 model chunks the kept map reaches, block B + birdcage + everything outside reach 23,410; the
  other rooms alone need 21,366 (12.3 MB). 35,102 + about 23,400 = about 58,500 entries without compaction.
  It needs a tool that removes rooms INSIDE a top-level subtree (the whole map is one subtree, and
  `kl_graft`'s `--m-drop` takes top-level names): scene, .oct trees, .rmi / .rmc boxes, gates to removed
  rooms, static Havok placements. A fix by new code; described, not made.
- Third way, READ re/prm_limit.md 'Not done': put the map's chunks into F07's dead indices inside the graft.
- (corrected by the second agent: the list lacks a fourth way, and it is the only one that needs no new code and no
  renumbering.) ANOTHER SYSTEMS LEVEL. MEASURED, `python tools/kl_maps.py one "<P>/skeptic" F05 M08_A --campaign`
  (result.json kept in `<P>/skeptic/F05+M08_A campaign`): written, ok, **61,504 chunk-table entries** (17,600 of F05 +
  43,848), 11 problems = the sound line + the ten Fragile Alliance findings, NO chunk problem; .prm 85.2 MB (untrimmed:
  under kl_graft's 90 MB line), sounds 4,982 / waves 4,669. Its price, READ re/campaign_fa_tooling.md 5.1 and
  tools/kl_expansion.py (`SYSTEMS = 'F07'`): no Dead Men map has run under another systems level, and kl_fa_author,
  kl_fa_street and kl_map_escape name F07's objects (the escape van is F07's). So it trades one unproven first load
  (compaction) for another (a new host).

### 3.3 The navigation mesh: converted, but in three pieces

- MEASURED (preflight): 'kl_pf4.check passes: 155 areas, 1298 polygons, 314 waypoints, 38 links; Dead Men links
  dropped by kind: {1: 38, 6: 4}'. Nothing is refused (no array of a form Dog Days lacks). 354,868 bytes.
- MEASURED, `python G:/kl_scratch/cfa_prison/navlinks.py M08_A` (stock level) and `nav.py M08_A <png>`: 55 parts
  by polygon edges; three matter:

| piece | polygons | floor | where |
|---|---:|---:|---|
| A (part 0) | 528 | 3,782 m2 | block A entry, block A, cantina, kitchen, laundry, the west kitchen yard; x 65..8430, z -3634..13990 |
| **B (part 32)** | 502 | 5,809 m2 | east kitchen yard, block B with its upper ring, both ground passages, the birdcage, the walkways, the tower, the south yard, the car park; x 3479..13765, z 3879..15491, y 0..1925 |
| V (part 12) | 103 | 503 m2 | the visiting area; x 8565..11161, z -4234..-165 |

  The rest: eleven booth counters of 2 polygons, five guard-tower rings of 8, a roof and four crate tops in
  the kitchen yard, one upper entrance, two outdoor yards nobody walks (2,695 and 1,734 m2).
- The 80 links of Dead Men's mesh are exactly the three crossings: 22 + 22 at the booth counters (up kind 1,
  down kind 2; V <-> A), 16 + 16 at the kitchen yard crates (A -> crates -> roof y 383 -> crates -> B), 4 of kind 6
  from the tower top (y 1925) to the yard (y 74..107) = the rappel. After conversion only drops are left, and
  **no link leaves piece A, B or V** ('one-way part graph, kind 2 only').
- READ re/bots.md 12.3: Dog Days' mover knows kind 1 (`/Movement/Climb/Up/Low|Medium|High`) but no animation set
  has those clips ('The climb code is in the exe, the clips are not in the game'), and the Dog Days PLAYER
  cannot follow either; the bank's wall had to be sunk for him. READ tools/kl_fa_bots.py (class Nav): stock
  links are all kind 2, one way, never upward.
- So: a round that stays inside ONE piece needs nothing from the links. A round across two pieces needs a
  changed place (a lowered counter, a ramp) or the hook's teleport - for the human too.

### 3.4 The five large blocks of a level load

MEASURED: member sizes from result.json; `python tools/kl_graft.py lighten "<build>" "<out>" --load trim,slim,fxc,wav`
(log `.../light/log.txt`); stock sizes read off the stock archives. Retomoto: READ CLAUDE.md 'BUDGET for the builders'.

| block | stock F07 | stock F01 | Retomoto | prison as built | prison lightened |
|---|---:|---:|---:|---:|---:|
| scratch | 32.0 | 32.0 | 32.0 | 32.0 | 32.0 |
| .fxc | 7.7 | 5.9 | 16.9 (8.9 slim) | 17.8 | 8.3 (242 -> 119 entries) |
| .prm | 60.6 | 63.5 | 74.2 | 64.2 | 64.2 (62.4 compacted; 79.5 with the wardrobe) |
| .ANM | 20.6 | 19.8 | 20.6 | 21.6 | 21.6 |
| .WAV beside | 17.4 | 14.7 | 25.9 | 21.6 | 11.6 (151 clips nothing can play dropped) |
| .TEX (not one of the five) | 268.0 | 275.0 | 405.6 -> 234 | 421.4 | 231.1 (451 dead textures to 4 x 4) |

Lightened, the prison asks for about 138 MB in large blocks - stock F01 asks for 136, Retomoto 170.
READ CLAUDE.md: trim and slim have run live (Retomoto `play3s`, Late Night Opening `z_maps/M02`); the
slimmed shader cache was still waiting for its live check (F1) on 2026-10-10, and kl_graft.py's own text
marks 'wav' NOT LOADED LIVE.

(corrected by the second agent: the table above mixes two units. The stock columns are MiB - MEASURED on the stock archive:
F07 .prm 63.6 MB = 60.6 MiB, .fxc 8.1 = 7.7, .ANM 21.6 = 20.6, .WAV 18.3 = 17.4, .TEX 281.0 = 268.0 - the prison
columns are result.json's MB of 10^6 bytes, except '.fxc 8.3', which is MiB. In ONE unit (MiB): as built .fxc 16.9,
.prm 61.2, .ANM 20.6 (it IS F07's file: log '.ANM joined: 21570860 -> 21570860 bytes'), .WAV 20.6, .TEX 401.9; lightened
.fxc 8.3, .prm 61.2, .WAV 11.0, .TEX 220.4 = 133 MiB of large blocks against stock F07's 138. 'Stock-sized' stands,
and more strongly: the .prm is 0.6 MiB over F07's, not 3.6, and the .ANM did not grow.)

### 3.5 What this level has that no map that ran has

MEASURED, `python tools/kl_maps.py first M08_A` and the preflight's 'first' lines for the BUILD (what survives
the pre-pass), located by `python G:/kl_scratch/cfa_prison/ctrlwhere.py M08_A <name>`:

| in the build | count | where | Dog Days |
|---|---:|---|---|
| `EffectDmgBox` (the riot fires' burn boxes) | 15 | ALL on the block B side: block B 8, birdcage 4, outside 3 | class exists, 0 uses in stock levels: RISK |
| `LightToggle` | 7 | cantina hallway, kitchen | 0 uses: RISK |
| `AnimSequence` (swinging lamps) | 5 | block A 4, laundry 1 | 0 uses: RISK |
| `ZHingeConstraint` | 1 | a serving table in the cantina | 0 uses: RISK |
| `CheckInside` with a value stock never has | 1 | an ambience box in block B | value RISK |
| `ZGateLightSpotSquare`, `DiscoMove` (11), `PlayAudio` (4) | | | used by stock levels |

A block-B-side map meets one of these, the 15 fire boxes; taking the controller off leaves the fire as a
picture. Everything else the campaign has that is new to the graft (crowd classes, `ZRopeLnkObj`,
`RappellingBox`, `KaneLynchBox`, `PsychoticController`, `SmallTalkCtrl`, cut-scene players ...) is on dropped
subtrees.

(corrected by the second agent: the map is kept WHOLE, so all four first-time controllers are in the build and are
set up at load wherever the round is played: `LightToggle` 7 (cantina hallway 2, kitchen 5), `AnimSequence` 5 (block A
4, laundry 1), `ZHingeConstraint` 1 (cantina), besides the 15 fire boxes - MEASURED, `skeptic/sk.py M08_A ctrl ...` and
the four RISK lines of my own preflight. 'Meets one of these' is true of where the PLAYER walks, not of what the
loader runs: strip all four, or prove all four.)

MEASURED, `python G:/kl_scratch/cfa_prison/kept.py M08_A`: the pre-pass keeps 15 `Specials!` nodes as 'passive
markers' - six no-cover boxes and **three campaign level bounds**:

- `Specials!LevelBounds!LevelBound_BlockB01!Bound` at (8295, 23, 11329), half size (1000, 400, 250): across the
  ground passage from block B to the yard - **on the route of any block B round**;
- `...LevelBound_BlockB_stairs01!Bound` (9091, 142, 12977) and `..._stairs02!Bound` (7499, 123, 13818): on the two
  stairs to the tiers.
  The campaign switches them off by script (`GeomDeactivator_StairBounds`), which the pre-pass drops. They
  must be dropped by name (`--m-drop "Specials!LevelBounds!*"`).

### 3.6 Crash classes of CLAUDE.md this level is exposed to

| class | exposure |
|---|---|
| chunk table past 73,728 (kl2 0x607280, re/prm_limit.md) | **yes as built**; gone after compaction or a cut (3.2) |
| .prm block refused (0x8e5bbd) | 64 MB plain is stock size; 79.5 MB with the wardrobe is Retomoto's size (77.8 ran with klmem) |
| no navigation mesh (0x5503da) / refused mesh | no: converted, check passes |
| room fix-up (0x48e910), room index (0x719884) | 61 rooms / 242 gates pass verify; 61 rooms is three times what ran (Retomoto 22): NOTE (gap closed 2026-10-11, section 'Gap closed: 242 gates' at the end: 242 gates is 35 past the most in a stock level (F09: 207), but READ kl2 0x48e910 walks each room's own array in place with a 32-bit count and no table is sized by the total; the fixed sizes found are per room or per frame and the prison is under each - e.g. at most 67 of the 1,024 frustum records a frame, stock F09 87: MEASURED) |
| unregistered type id (0x46fe87 / 0x8add12) | none in the build; four first-time controllers (3.5) run code no stock level runs |
| second cover list (0x6682c5) | Dead Men's `CoverList` is systems side (not taken); an authored layer must keep exactly one |
| JumpPoint fired by a level object (0x8f40c9) | only if authored; the recommended round has no jump |
| execute crash (0x4098a1) | the build log shows the `ExecutionBloodSpatter` repair applied |
| bone ids (0x4c34b3) | kl_impact on the compacted builds: 0 problems |
| money trigger set off by a vehicle (0x6a8902) | `kl_fa.money_people` covers it once loot exists |
| ZDefendBehaviourRout loop (0x686a66, cause open) | yes if campaign squads with defend routs stay (they would) - corrected by the second agent: the cause is read since (re/crash_686a66.md): a `ZFakeTarget` outside the vision grid (parked vans), not a defend rout; exposure = wherever F07's unused vans 02 / 03 are parked |
| campaign squads' weapons (invisible / wrong gun) | kl_arms armed 0 actors here because no squad was kept; with squads: as Retomoto |
| DistanceRumbleCam with a Dead Men camera clip (blind seconds, M01) | only if the helicopters are kept: take the controller off |

## 4. The round

### 4.1 What the money is

MEASURED (`python tools/kl_maps.py what M08_A`, `props.py M08_A census`, `props.py M08_A find ...`): the prison has no
safe, no armoury, no evidence room, no money object and no loot class. What stands there: 10 vending
machines, 5 pay phones, 6 office desks, monitors and consoles in four control rooms, a fridge, 11 card
readers, laundry wagons and bags, crates, garbage. Two grenade pickups in the kitchen are the only items;
`python G:/kl_scratch/cfa_prison/moneyprops.py M08_A` lists no money object.

MEASURED (`python G:/kl_scratch/cfa_prison/moneyprops.py M06_FA_A M03_FA_A M01_FA_A M02_FA_A F07`): the props Dead
Men's Fragile Alliance maps have: `Money!DopeBag_00` (the park, 299), `KillDrop!Briefcase` (park),
`KillDrop!Suitcase` (diner), `Wallet`, `Box_Money` / `PC0500_M03_Money_Arranged` / `Cashbox` (bank), `Jewelbag`
(mall); F07 has only its sports bag. People can carry money too (`OnlineMoneyCtrl` NORMAL on an actor group:
'The_Senator', 'US_Boss', 'Clerk_Female' ...).

- **Break-out** (the crew is inside when the riot starts): the money is what a prison holds that is worth
  taking in a riot - **contraband** (the park's dope bag) at the cells and in the guards' rooms, and
  **the guards' cash** (the diner's suitcase, the prop Retomoto's boardroom uses) in the control rooms.
  READ re/retomoto_loot.md 0: a loot object can show another level's model (`kl_fa_loot.py`: M01_FA_A's
  suitcase on Retomoto, offline proof, 18 chunks).
- **Break-in for a payout per freed man**: Fragile Alliance has no 'freed' event. The nearest stock mechanic
  is money on a person; READ re/fa_gamemode.md 5 and re/retomoto_fa.md 5: a squad's 'wiped out' list can make
  hidden loot appear. So 'a payout per man' can only be built as loot that appears when a cell opens (one
  stack per cell, behind the control-room action) - or, grimly, as a bounty carried by the blacklisted men.

### 4.2 Three candidates

**R1 'Cell Block B' - break-out, piece B only (recommended, 4.3).**

**R2 'Visiting Hours' - break-in, pieces V + A.** Start where the campaign starts, at the truck in the
visiting room (10898, 335, -4346) - a true 'already in' opening; over the booths; security room panel; block
A; loot = one stack per cell that opens from control room A (2203, 390, 3261), up to 56 doors; out the way in.
Against it: the V - A crossing is the booth counters (79 high, climb-up links: no AI, the player's vault over
them NOT established); the only vehicle place is outside the mesh (the getaway van model
`Ground_USA_GetawayVan_01` stands at (19764, 0, 2394), the wall hole at z -7300; the mesh ends at z -4234); the
route doubles back; block A's alarm and 56 animated cell doors are the heaviest scripting in the level. It
would be a second map, not a variant of R1.

**R3 'The whole breakout' - the campaign way, V -> A -> B.** 1,434 m of legs and three that do not exist on
the mesh (MEASURED, 1.4); two climbs Dog Days has no clip for and a rappel no stock Dog Days level has; 25 door and gate proxies
with 56 cell doors among their targets. A Fragile
Alliance round is minutes long. Not a candidate; named because the owner's words for the bank were 'the
campaign way'.

### 4.3 Recommended: 'Cell Block B'

All places below are on piece B (MEASURED, `nav2.py M08_A <png> stations_route.txt` and `stations_loot.txt`:
every station 'off mesh 0', every leg exists). Places marked GUESS are mine.
(corrected by the second agent: true of the stations in those two files, not of every place named below. MEASURED,
`skeptic/navchk.py M08_A at ...`: the desk (10594, 919, 14520), the fridge (10413, 921, 14539) and the vending machine
(10635, 920, 12279) are 0.7 .. 0.9 m OFF the mesh and the four tower consoles `..._A_01..04` 2.5 m off it - they are
prop origins. Only the console (10100, 950, 13400) and the tower's `_B_Open` (0.1 m off) are at walkable floor: the
stacks go on the floor beside the props. And control room B lies BEHIND the block's slide doors: with them shut there
is no way from the START to the console on the mesh (`skeptic/bypass.py`, test F), and the stairs up carry the
campaign's level bound of section 3.5.)

- **Start - in the middle of the riot.** The eight heisters stand on the ground floor at the east end of
  cell block B, START row at x 9800, y 0, z 13150..13650 (GUESS; 9800, 0, 13400 is polygon 776), facing west
  down the hall: fires burn (the level's own `Rubble_Fire` groups at (7358, 1, 13165), (8586, 53, 13122),
  (9527, -1, 13509) ...), the lockdown announcement runs, and the first thing that happens is the campaign's own
  beat - **SWAT storms in through the west door** (5758, -2, 13400), 50 m down the hall from them (14 + 36 m, MEASURED). No walk-in: the
  loot is on the floor they stand on and above their heads.
- **Loot** (about 4 million, GUESS; Retomoto has 4.05):
  - contraband bags along the cell fronts of the ground floor and of the first tier, 10..12 small stacks
    (GUESS places on the hall's floor polygons; the two cell-light places tested, (10299, 19, 13301) and
    (9523, 19, 14132), have no ground polygon under them: the cells are not walkable floor);
  - the guards' cash in **control room B**, upper level east: at the console
    `FX0001_M08_BlockB_ControlCenter_A_Inside` (10100, 950, 13400), the desk (10594, 919, 14520), the fridge
    (10413, 921, 14539), the vending machine (10635, 920, 12279): 4 large stacks, 129 m from the START by
    the block's stairs;
  - **the tower** as the greedy option: 5 large stacks at the consoles of the top room
    (`FX0001_M08_ControlBirdCage_A_01..04` at (9072 / 10324, 1925, 8174 / 9427), `_B_Open` (9072, 1925, 8799)).
    It is 180 m beyond control room B along the east walkway and up, and **312 m back down to the south lobby**
    (the rappel links are dropped by the converter; `RappellingBox` has 0 uses in stock Dog Days levels): whoever goes for it is the last one at the van. That is the traitor's
    dilemma the mode is made for, and it costs nothing to leave out.
- **The beat in the middle - the yard.** South lobby (8169, 22, 12417), cage door (8302, 20, 12223), ground
  passage, cage door (8300, 21, 10527), and the crew is in the birdcage: open ground 40 m long (19 + 21 m, MEASURED), overlooked from
  the walkway ring (the two ledge squads, eight men at y 961) and the tower, with the south gate shut. GUESS: the last gate
  opens 30 s after the first heister enters the yard (a trigger box and a delay on the campaign's own
  `Specials!Triggers!06_BirdCage!TowerControlRoom!MatPosAnimProxy_LastGate`), with the door buzzer; the two
  fences fall with it. Hold the yard, then run. The police helicopter over the yard is the campaign's
  (`AI_Players!Chopper_ShootTower`); ZHeli with `HeliWeapon` and fly routs is in stock F02 / F03 / F06 / F08
  (MEASURED, kl_maps.py first) - an extra, not part of the first build.
- **Enemies.** By kl_fa_author's rule (a squad stays when it holds only squad objects, an actor and a
  behaviour rout) piece B keeps 7 enemy squads / 25 guards as they are (MEASURED, squads.py):

  | squad (`AI_Players!Enemies!...`) | men | weapons | where | role |
  |---|---:|---|---|---|
  | `06_CellblockB!Squad_Upper_Walkways`, `Squad_Walkways01`, `Squad_Walkways02` | 4 + 2 + 2 | Remington 870 | upper ring of block B, y 920, at control room B | the block's guards |
  | `06_CellblockB!Squad_SWAT_StormBlockB` | 6 | MP5, Mini-14 | (3879..4644, 0, 12821..13857), outside the west door | **the police arriving**, started by the loot trigger |
  | `07_Birdcage!Squad_Birdcage_Ledge#02`, `Squad_ExitTower` | 4 + 2 | Mini-14, Remington 870 | west ledge y 961; tower entry | the yard |
  | `08_Escape!Squad_Ground#01` | 5 | Mini-14, MP5 | (12382..13017, -7, 8421..8847): on the van's stop | the gate |

  Fifteen more squads / 24 men have no behaviour rout of their own (they act through mini cut scenes) and
  need one authored: `Squad_TowerTop` (4, y 1927), `Squad_Birdcage_Ledge` (4), `Squad_Birdcage_Floor01` (2),
  `08_Escape!Squad_Tower#02` (two Minimis in the gate towers (13812, 980, 7677), (13905, 980, 9544)),
  `Squad_Tower_CS` (two tear-gas launchers), `Squad_Tower_Garden_MG` (5997, 953, 4046). The 14 inmates on the
  tiers (`AI_Players!Civilians!05_CellblockB!Civ_Inmates_ledges*`, ZCivilian) can stay as bystanders
  (ASSUMED: plain ZCivilian squads run in the four Dead Men FA maps). Later police waves: F07's own squads
  re-placed, as Retomoto's street layer does (READ CLAUDE.md, 'RETOMOTO DYNAMIC AI + STRAIGHT VAN') - second step.
  The SWAT squad's own defend box is OUTSIDE the door at (4568, -2, 13400) (its mini cut scene fires into the
  hall at (6506, 110, 13400) and throws a grenade to (5544, -6, 13419)): to make them come in, the box is moved
  into the hall (authoring).
  Lesson to copy (READ re/retomoto_fa.md 9.2): every guard waits for the round-start timer.
- **Escape - the prison's own gate.** F07's key-framed van, laid on one straight line heading EAST along
  z 8800: it waits in the car park at about (11300, 0, 8800), stops at about (12900, 0, 8800) (polygon 949;
  both GUESS), and drives out through the entrance gate (14000, 0, 8800) between the two gate towers onto the
  road outside (the outside room runs to x 80173). The gate `SO0106_M08_Entrance_Fence_01` and the tyre-slicer
  road block (13830, -33, 8801) are hidden when the van is called (the level has the open-gate leaves
  `SO0106_M08_Entrance_Open_03 / _04` beside it). Flag poles and lamps stand clear of it at z 7999..8201
  and 9400..9600; two objects have their ORIGIN on the line (MEASURED, `lane.py M08_A 11000 16500 8500 9100`):
  `SO0106_M08_Wall_Walk_Plants_C_01` (11702, 0, 8800) and a second tyre slicer `..._RoadBlock_02`
  (12705, -30, 8801). What they are in the way of was not looked at: if the first is solid the van waits
  east of it (x 12000). READ tools/kl_fa_van.py: the drive is rewritten key by key onto a straight line - it writes
  'nose north'; a heading has to be added (a constant yaw, or the group's own turn). The parked prisoner
  transport stays as scenery at (11600, -8, 11593), 31 m from the stop.
  (corrected by the second agent; all MEASURED on the .HVK triangles with `skeptic/lanetri.py` / `lanebox.py`, pictures
  `<P>/skeptic/pics/gate_area.png`, `gate_zoom.png`, `south_yard.png`:
  (1) the lane z 8800 +- 110 is clear of collision at every height 5..220 from x 11000 to 13200 and again from 13300
  to 16000; (2) the fence the van must pass stands at x 13226..13300, not at 14000: 3.3 m east of the proposed stop,
  so the van's nose stops AT it, and the mesh ends at x 13171; the wall's portal at x 13958..14041 is clear below
  y 350; (3) `Wall_Walk_Plants_C_01` is flat (y -19..2) and both tyre slicers are strips of y -33..-3 across the whole
  lane (z 8561..9041) at x 12705 and 13830: nothing a key-framed van hits, they only look wrong if left visible;
  (4) (11300, 0, 8800) is not 'in the car park': it is under the canopy of the gate building
  `SO0106_M08_Wall_B_Entry_01` (roof at y 300..400 from x 10800 to 11900), in front of its shut steel doors
  `SI0301_M03_DoorSteel_A_01 / _02` at x 10900..11000 - the van would come out of the gatehouse porch;
  (5) the ground is two flat pieces at y -20 (`Ground_B_13`, `Ground_A_28`), not 0, and it ENDS at x 13955: under
  the lane east of the wall there is no collision at all (0 placements, x 14050..20000) - fine for a key-framed van;
  (6) the heading is NOT missing: READ tools/kl_map_escape.py (the comment before `van_plan`: 'a key's place AND heading
  can be anything'; `K.turned`; the check 'a rewritten rotation key is N degrees off its heading') - it lays F07's van on
  any curve with the keys turned to the drive, and that code has driven in the game on M01 / M02 / M03 (READ CLAUDE.md,
  runs G_DM01 and H0_DM03). What the prison lacks is only its INPUT: `van_plan` takes the path from a Dead Men spline
  car and the prison has none, so the path is given by hand.)
- **Level bounds.** The walls are the bounds. Authored: one behind the west door of block B (GUESS x 5600, so
  that the east kitchen yard is out; police come through it), one outside the gate (GUESS x 14200), and the
  campaign's three removed (3.5).
- **Music.** MEASURED (`music.py M08_A <offsets>`, `python tools/kl_str.py list <DM>/PC_Def.str M08`): the
  chapter's three `PlayMusic` objects hold two interleaved sets, each 250.3 s, three layers, 48 MB:
  `LevelSetup/Level/M08_A/Music/Prison_L1` = `Music/InHouse/M08/M08_Prison_Amb_Loop` + `..._Suspense_Layer_V2_Loop`
  + `..._Tension_Layer_V2_Loop` (parts 1 and 3: block A to the kitchen, and the tower to the end) and
  `Prison_L2` = `M08_Prison_Amb_Loop_L2` + `M08_Prison_Guitar_Layer_Loop` + `M08_Prison_Tension_Layer_V2_Loop_L2`
  (part 2: block B). Neither set is in the merged PC_Def.str (+96 MB). Round: `Prison_L2` from the start (it
  is block B's), `Prison_L1` with all three layers up from the yard on. `FA_SlashMixPrison` is in the
  merged file already and is the fall-back that needs no new stream file.
- **Voice.** In Dead Men's PC_Def.str (261 M08 clips, MEASURED same command): four lockdown announcements
  `Dialog/M08/Dialogue/M08_OneLiners/M08_Lockdown/M08_Lockdown_010 / _030 / _040 / _050` (5.5..14.1 s; each has a
  speaker-effect twin `M08_Lockdown_Effect/..._Effect`, the four clips the trial build misses - ASSUMED to be what
  the level's kept loudspeaker objects `Locations/M08_A/M08A_Audio.zip!Audio!Inside!SpeakerDialog!*` play, because
  only kept map nodes can name a clip in that list) - the round's opening sound; inmates' lines `M08_OneLiners/M08_Prisoners/M08_PrisonerAngry / Shock / Panic / Idle / Scream` (38);
  for the talk system (kl_fa_talk) Kane and Lynch: `Situations/M08_ControlTower/*`, `M08_Escape_010_Lynch`,
  `M08_Escape_020_Hero`, `M08_ToTower/*`.
- **The AI heisters' route** (one piece, 206 m over polygon centres; MEASURED):

  | # | station | x y z | leg |
  |---:|---|---|---:|
  | 1 | START, east end of the ground floor (GUESS) | 9800 0 13400 | |
  | 2 | hall centre (loot on the way) | 8701 5 13304 | 14 m |
  | 3 | south lobby | 8169 22 12417 | 25 m |
  | 4 | cage door B | 8302 20 12223 | 1 m |
  | 5 | ground passage | 8295 23 11329 | 14 m |
  | 6 | cage door C, north of the yard | 8300 21 10527 | 5 m |
  | 7 | yard centre (the hold) | 8383 3 8809 | 19 m |
  | 8 | last gate, inner door | 8299 20 7071 | 21 m |
  | 9 | last gate, outer door | 8299 21 6019 | 10 m |
  | 10 | south yard | 8203 -28 4960 | 16 m |
  | 11 | fence 1 | 9300 0 4900 | 5 m |
  | 12 | fence 2 | 9941 0 4913 | 4 m |
  | 13 | car park | 12455 -1 6921 | 45 m |
  | 14 | van stop (GUESS) | 12900 0 8800 | 26 m |

  No hop, no teleport, no hook part: nothing but polygon edges. (The bank needs a repaired drop link,
  Retomoto a hook jump.) The stations pass five door prefabs and two fences whose path blockers must be
  open (section 5).
- **Next to what?** There is no Fragile Alliance map of the prison on PC, so nothing to stand apart from.
  Among the maps on the tab it would be the only one with a hold-out in the open and a gate to leave by.

## 5. What has to be authored

READ tools/kl_fa_author.py (tables `PLACE`, `ROLE`, `SPAWN`, `KEEP`, `CAMPAIGN_KEEP`; `prepare_host`, `wire`) and
re/retomoto_fa.md 2: the layer re-places F07's own objects and wires them; nothing is created.

| what a layer needs | from | the prison holds already |
|---|---|---|
| settings, 'IsMultiplayerLevel' define, speakers, briefing, AI monitor, vehicle monitor | F07, kept as they are | nothing |
| 8 START, 4 TRAITOR, 7 AFTER_DEATH points; UCC / team points; 16 player groups; spawn cameras | F07, re-placed | places only: checkpoint markers `Specials!Checkpoint_Saves!CP_06..CP_09_PosP1/P2`, campaign actor positions for the police points (SWAT squad, car-park squad) |
| loot marker, ENTERS / EXITS triggers, escape marker | F07, re-placed | nothing |
| loot: 20..25 money objects | F07's pool stacks, re-placed and valued; two props from M06_FA_A / M01_FA_A (kl_fa_loot) | the places (4.3) |
| round-start timer and its wrappers | F07 (`Gameplay!010_FirstFight!RivalMercVan!Timer` idiom) | nothing |
| **doors on the route** | the campaign's own single nodes, kept by name and fired by the timer / the yard trigger | `Specials!Triggers!05_BlockB!ControlRoom!MatPosProxy_B_HallwayBars` (three cage doors), `...06_BirdCage!TowerControlRoom!MatPosAnimProxy_LastGate` (two), `...07_Escape!Activator_FenceAnim_A01 / A02` + `Activator_FenceColi_A01 / A02`, `AI_Players!Enemies!08_Escape!Pathblocker_Fence01 / 02`; for the upper way `MatPosAnimProxy_OpenBDoor#01 / #02`, `MatPosAnimProxy_ExitDoors`, `#01`, `#02`. Each door prefab carries its own path blocker ('eToggle', blocking) - corrected by the second agent: only `CageDor_B_01` and the slide doors carry one (MEASURED `skeptic/sk.py M08_A ctrl PathBlocker`: 46 in the level); the four `CageDor_C_*` of the route have none, and the fences' and the west door's blockers are on subtrees the pre-pass drops |
| the gate for the van | hide `SO0106_M08_Entrance_Fence_01` and the road block; path of the van (kl_fa_van + heading) | the gate, its open leaves, the lane |
| exit trigger, three vans, boarding | F07's `Animation/F07/F07_Escape_Vehicle_01..03.zip` | nothing (no vehicle class but two helicopters) |
| level bounds | F07's, re-placed; the campaign's three dropped | walls |
| squads | 7 campaign squads as they are, up to 15 more with an authored rout; mini-cut controllers stripped; weapons by kl_arms | 22 enemy squads / 49 men on piece B |
| the seven AI heisters | kl_fa_bots on the finished build | one connected mesh piece, 183 + 58 cover boxes in the level |
| music, announcements | a kept `Music!PlayMusic_Part_02` (as Retomoto keeps `PlayMusic_TokyoAction`), the clips into PC_Def.str (`kl_str.py build --extend`) | the objects and the clips |
| fires | take `EffectDmgBox` off the 15 fire boxes (or prove it live) | the fires |

**Size of the work: about 0.7 of Retomoto** (GUESS with reasons; 0.6 if the generic authoring tool of
re/campaign_fa_tooling.md exists first, 0.9 if compaction fails live and the room-cut tool must be written).

- Less than Retomoto: one level instead of two (no chain, no joined meshes, no three Havok parts); no join
  and no hook code; no ledge to build, no blast sequence; the bots' route needs no special case; the level
  is stock-sized in memory; the vehicle place, the gate and the fences are the campaign's own.
- The same: the whole table of places (spawns, cameras, markers, bounds, loot), squads and weapons, van
  re-lay, loot props, music into the stream file, wardrobe, lighten.
- More than Retomoto: the chunk table needs a step that has never run live; five animated cage doors,
  two falling fences and the entrance gate on the route, six slide doors more on the upper way to the loot
  (Retomoto: one door swap and two elevator doors); 61 rooms; kl_fa_author.py is
  Retomoto from its first constant, so the prison needs its own table or the generic tool.

**Order of steps to a first load**

1. `HERO_AT` in tools/kl_maps.py gets M08_A (`Specials!Checkpoint_Saves!CP_06_PosP1 / P2` -> `Heroes!Hero_01 / 02`);
   the pre-pass drops `Specials!LevelBounds!*`. Build `one F07 M08_A --campaign --heroes --keep`.
2. `kl_graft.py lighten` (trim, slim, fxc, wav), then `kl_chars.py compact`; `kl_impact.py` must say 0.
3. FIRST LOAD by direct boot: the player stands in block B. This one run settles compaction, 61 rooms,
   the fire boxes and the picture (lighting, shaders).
4. Scripted walk along the 14 stations with the door proxies fired by hand: which doors stop a player.
5. The layer: places table, doors on the round-start timer, loot, squads waiting for GO, bounds; `kl_fa.check`
   0 CRASH / 0 BROKEN. First Arcade round, guards off, then on.
6. Van: straight east through the gate; exit trigger, boarding. 7. Bots (kl_fa_bots plan + check).
8. Loot props, music and announcements (new PC_Def.str), wardrobe (compact after it), talk.

## 6. Risks, and what only a live run can settle

1. **Does a compacted level load and look right** (HUD, fonts, effects, post filters)? It is the only way
   under the chunk limit that exists today. If not: the room-cut tool (3.2).
2. **Do Dead Men's animated doors open in Dog Days** when their proxy is fired (cage doors and slide doors
   = `MatPosAnim` 'Activate' with KEYS chunks; fences = `MatPosAnim` 'FenceFall' + a geometry swap)? READ
   CLAUDE.md (z_gate entry): 'Dog Days plays the Dead Men KEYS chunk' is still an assumption. Do the closed
   doors stop the player and block the mesh, and do their path blockers open with them? Fall-back: remove the
   door leaves of the route and their Havok placements at build time.
   (corrected by the second agent: more is known than 'an assumption'. (a) A live hint exists - the owner saw the bank's
   roller doors open (READ CLAUDE.md, 'once the garage door comes open'; re/escape.md section 3: `SI0201_M03_BackDorAnim_01
   / _02` = `MatPosAnim` + type 4 key-framed collision, the construction of these doors; re/map_escape.md 19.6 calls it
   'live hint only'). (b) MEASURED, `skeptic/hvk.py`: every leaf of the five cage doors and both fences is a type 4
   key-framed body on its own entity, so the fall-back works for all seven; the entrance fence is type 1 static.
   (c) MEASURED, `skeptic/bypass.py`: there is NO way round any of them. Closing the mesh polygon under ANY ONE of the
   seven - cage door B, the two of the ground passage, the two of the last gate, either fence - leaves no way from the
   START to the car park; the upper walkways do not come down into the yard. Seven closures in series: one that stays
   shut ends the round. (d) A shut Dead Men door does stop a Dog Days player: READ re/retomoto_fa.md 10.1, run J1.)
3. The 15 `EffectDmgBox` fires (first-time code) - or strip them.
4. The first loads of the slimmed shader cache and the slimmed .WAV (not seen live anywhere yet, 3.4).
5. 61 rooms, 242 gates, 127 neighbour lists in one level: three times the rooms of anything that ran.
   (gap closed 2026-10-11, 'Gap closed: 242 gates' at the end: counted. No table of kl2.exe is sized by a level's gates
   (READ 0x48e910, 0x522cc0, 0x6e5b20, 0x83dca0, the .sgp reader 0x75ee20); per room and per frame the prison is under
   every fixed size found - 17 gates and 10 lists in a room (u32 / about 30), 67 of 1,024 frusta a frame, 24 of 32 sound
   routes: MEASURED. Four counts are firsts all the same: 242 gates (stock 207), 121 sound portals (102), 172 room boxes
   (108), 10 lists in one room (9). What is left of this risk is that the level was never loaded.)
6. The start: can the heisters stand the countdown in block B (guards above them; READ re/retomoto_fa.md 9.2)?
7. The van: the lane at z 8800, the height of the car park's ground (objects there stand at y -20..0), the
   hidden gate's collision (a static Havok shape stays when its entity is hidden: READ re/retomoto_fa.md 4),
   the five guards standing on the stop.
8. The yard as a hold-out: 30 s under eight rifles may be too much or nothing; only play tells.
9. Campaign squads with defend routs and the open 0x686a66 crash (CLAUDE.md).
   (corrected by the second agent: no longer open. READ re/crash_686a66.md section 0, written this night: the writer is a
   `ZFakeTarget` that stands outside the vision grid - F07's escape vans 02 / 03 parked 600 m under Retomoto's road - not
   a defend rout. For the prison the rule is: every FakeTarget of the vans that are not used stays INSIDE the rooms'
   bounds, or loses the controller (`tools/kl_fa_bots_dyn.py` check / fake-fix).)
10. Ally-faction armed prisoners, inmates as civilians, the helicopter: each an extra with its own first run.
11. NOT established offline: whether a Dog Days player can vault the visiting booth counters (R2 only);
    which `Rubble_Fire` emitters burn at load without the campaign's activators; whether the kept
    `SpeakerDialog` objects can be started by a plain trigger.
12. Slot: the 'Dead Men maps' page has one free slot (F07 of six); the prison competes for it with the other
    campaign places of this study.

## 7. Verdict

**feasible-with-work.** The prison can become a Fragile Alliance map, but not 'the campaign way': the story
runs a kilometre and a half through three areas that are only joined by climbing and a rope descent, which Dog
Days cannot do. One of those areas is a whole round on its own - cell block B, the yard under the tower,
the last gate, the fences, the car park and the prison's real exit - 200 metres that a player and the
seven AI heisters can walk without any trick. The map loads into the tools without a fault except one: its
models need more table slots than the game has, and the fix for that (a renumbering step that already
exists and passes every offline test, also with the wardrobe) has never been tried in the running game.
After that it is authoring of the kind done for Retomoto, somewhat less of it: places for the players,
loot dressed as contraband and guards' cash, the campaign's own guards and SWAT team, its doors and fences
opened by its own switches, Dog Days' van driving out of the prison gate, the prison music. Nothing here has
run in the game; the first load (step 3) decides whether the estimate holds.

## Appendix: the commands behind the numbers

Run from `c:/kl-merge/kl-merge`. `<P>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/cfa/prison`,
`<S>` = `G:/kl_scratch/cfa_prison`. Nothing below writes outside `<P>` and `<S>`.

    python tools/kl_maps.py what M08_A | sides M08_A | first M08_A        level, sides, first-timers
    python tools/kl_maps.py one "<P>" F07 M08_A --campaign --keep         the trial graft (82 s) -> "<P>/F07+M08_A campaign"
    python tools/kl_maps.py preflight "<P>/F07+M08_A campaign"            every offline check (needs --keep)
    python tools/kl_impact.py "<P>/F07+M08_A campaign"                    the chunk-table problem
    python tools/kl_chars.py compact "<P>/F07+M08_A campaign" "<P>/compact"          79,005 -> 50,617
    python tools/kl_graft.py lighten "<P>/F07+M08_A campaign" "<P>/light" --load trim,slim,fxc,wav
    python tools/kl_chars.py wardrobe "<P>/F07+M08_A campaign" "<P>/wardrobe"        then compact -> 63,528
    python <S>/navlinks.py M08_A                    the mesh's parts, all 80 links, the one-way part graph
    python <S>/nav.py M08_A <png>                   parts with sizes and boxes, picture by part
    python <S>/nav2.py M08_A <png> <S>/stations_route.txt 5300 14400 3600 14900 7      the round's route (206 m)
    python <S>/nav2.py M08_A <png> <S>/stations_campaign.txt                           the campaign's 27 places
    python <S>/squads.py M08_A                      squads, actors, weapons, who can stay
    python <S>/doors.py M08_A MatPosAnimProxy PathBlocker          scripted doors and what they move
    python <S>/kept.py M08_A                        what the campaign pre-pass keeps (the three level bounds)
    python <S>/ctrlwhere.py M08_A EffectDmgBox LightToggle AnimSequence ZHingeConstraint
    python <S>/leftovers.py M08_A                   Fragile Alliance leftovers (none)
    python <S>/cut.py M08_A "LOC_INS_Block_B.zip|LOC_INS_BirdCage.zip|M08A_LOC_Outside.zip"      chunks of the block B side
    python <S>/music.py M08_A 92624 92816 93008 93456 93648 93856       the PlayMusic layers by name
    python tools/kl_str.py list "<Dead Men>/PC_Def.str" M08            the chapter's 261 stream clips

Kept outputs: `<P>/F07+M08_A campaign/{result.json,log.txt,graft.txt,preflight.json}`, `<P>/compact/log.txt`,
`<P>/light/log.txt`, `<P>/wardrobe/log.txt`, `<P>/wardrobe_compact/log.txt` (the `result.copy_of_base.json` files in
those four folders are the tools' copies of the base build's result, renamed so that `kl_maps.py table` counts
one build), `<P>/pics/*.png`, and in `<S>`: `tree_M08_A.txt`, `tree_loc.txt`, `squads_M08_A.txt`, `doors_M08_A.txt`,
`swaps_M08_A.txt`, `navlinks_M08_A.txt`, `preflight.txt`, `first_M08_A.txt`, `census_M08_A.txt`, `leftovers_M08_A.txt`.

## Verification (second agent)

2026-10-11, agent cfa-prison-skeptic. OFFLINE: nothing installed, the game not started, no tool edited, nothing
committed. `<S2>` = `G:/kl_scratch/cfa_prison/skeptic` (my scripts; none imports a script of the first agent),
`<P2>` = `<work>/build/cfa/prison/skeptic` (my own trial builds: `result.json` / `log.txt` kept, every archive
deleted; pictures in `<P2>/pics`). Eleven statements above are corrected in place and marked 'corrected by the
second agent'; the report as it stood before is `<S2>/campaign_fa_prison.before_corrections.md`.

**My verdict: feasible-with-work - the same verdict, a different list of reasons.** The measurements of the
first agent hold almost without exception (24 re-derived, below). What does not hold is part of the DESIGN
as written: the vehicle gate is 7.7 m west of where the report puts it, the loot places upstairs are mostly
off the floor and behind doors, and the route is seven shut doors and fences in a row with no way round any
of them. None of that kills the round; all of it is authoring the report had not counted. And two things are
better than the report says: the chunk limit has a second way out that needs no new code (another systems
level, measured), and the van tool already drives in any direction.

My scripts (`python <S2>/<script> M08_A ...`): `navchk.py` (the mesh read from the Dead Men form by my own
parser: parts, links, stations, walking distance over edge middles), `bypass.py` (is a door the only way),
`sk.py` (property tree: find / near / ctrl / count), `hvk.py` (which Havok placement an entity has),
`lanebox.py` / `lanetri.py` (collision boxes / triangle-exact cuts of a swept lane), `colmap.py` (a top-down
picture from the collision triangles with the mesh over it), `squadchk.py`, `leftchk.py`, `swapchk.py`,
`boxlist.py`.

### Confirmed (how I checked)

1. **The trial graft.** Rebuilt: `python tools/kl_maps.py one "<P2>" F07 M08_A --campaign --keep` -> ok, 23,307
   entities, 61 rooms, 242 gates, 1,964 textures, 1,286 materials, 4,745 sounds / 4,589 waves, archive 329 MB,
   `verify: problems: 12` = the chunk table + the sound line (11 clips) + ten Fragile Alliance findings (1 CRASH,
   9 BROKEN). Same numbers as the first agent's `result.json`.
2. **The chunk table.** `python tools/kl_impact.py "<P2>/F07+M08_A campaign"`: 1 problem, '79005 chunk-table
   entries, the game's table has 73728'. The log: '43848 of 56576 chunks of M08_A appended to 35101'; stock F07
   has 35,102 entries (MEASURED on the stock archive, kl_prmgraph.read).
3. **Compaction.** `python tools/kl_chars.py compact ...`: 79,005 -> 50,617, problems 0; `kl_impact.py` on the
   result: 0 problems. 'Never loaded in the game': READ re/prm_limit.md ('Compaction ... offline only, NOT LOADED
   LIVE'); `grep -i compact CLAUDE.md` finds no live run.
4. **Wardrobe + compaction.** `kl_chars.py wardrobe` (15,509 of 24,323 dead indices taken, table stays 79,005,
   .prm 64.2 -> 80.4 MB), then `compact`: 63,528 entries, .prm 79.5 MB, problems 0, `kl_impact.py` 0.
5. **Lighten.** `python tools/kl_graft.py lighten ... --load trim,slim,fxc,wav`: .TEX 421.4 -> 231.1 MB (451
   textures to 4 x 4), shader cache 242 -> 119 entries, .WAV 21.6 -> 11.6 MB (151 clips dropped), archive
   329.3 -> 190.4 MB. (Units: see the correction in 3.4.)
6. **Preflight.** `python tools/kl_maps.py preflight "<P2>/F07+M08_A campaign"`: CRASH 2, RISK 14, NOTE 66; the
   four first-time controllers 15 / 7 / 5 / 1; one `CCheckInside` value RISK; NOTE 'larger than any Dead Men build
   that ran live: entities 23307 (19827), rooms 61 (20), nav_bytes 354868 (186672)'.
7. **The mesh converts.** My parser on the stock level and on the built archive (`navchk.py M08_A parts`,
   `navchk.py "<P2>/F07+M08_A campaign" parts`): 1,298 polygons, 155 areas, 314 waypoints; 80 links in Dead Men
   (kind 1: 38, kind 2: 38, kind 6: 4), 38 in the build.
8. **Three pieces.** 55 parts by polygon edges (0 edges named one way only); the large ones 528 / 502 / 103
   polygons with exactly the boxes of section 3.3. The links: 22 + 22 at the booth counters (parts 15..26
   between part 12 and part 0), 16 + 16 at the crates (32 -> 47 -> 48 -> 46 -> 49 -> 50 -> 0 and back), 4 of kind 6
   from part 32 to part 32. With kind 2 only, no link leaves part 0, 12 or 32.
9. **The route.** `navchk.py M08_A stations <S>/stations_route.txt` (and on the built mesh): all 14 stations on
   the 502-polygon part, floor under every one within 28 of the given height, every leg exists; 194 m over edge
   middles (the report's 206 m is over polygon centres). Loot detours: START -> console of control room B 136 m
   (report 129), on to the tower top 189 m (180), back down to the south lobby 323 m (312).
10. **The START stands on open floor.** Picture `<P2>/pics/blockB_ground.png` (collision cut y -60..300 with the
    mesh): the hall is x 6540..10060, z 12970..13890; the row x 9800, z 13150..13650 is a 3.6 m strip between a
    rubble pile (x 9390..9690, its fire box at (9527, -1, 13509)) and the east wall. Not inside geometry. Tight
    for eight.
11. **No climbing in Dog Days.** READ re/bots.md 12.3 (the table of kinds; 'The climb code is in the exe, the
    clips are not in the game'; stock links are all kind 2, never upward).
12. **The campaign's end and the vehicle classes.** `sk.py M08_A find ...`: transport group at (11600, -8, 11593),
    `EndOfLevelTrigger` at (11612, 33, 11477) naming `Locations\M09_A\M09A_Main.zip`; `SO0106_M08_Entrance_Fence_01`
    ORIGIN (14000, 0, 8800) (what that means: corrected); `sk.py count`: ZHeli 2, ZHavokCar 0; `kl_maps.py what`:
    21,373 entities, 'escape / loot: {ZHeli: 2}'.
13. **No leftover of a Fragile Alliance version.** `leftchk.py M08_A`: 0 ZSpawnPoint, 0 Online* classes or
    controllers, no spawn-type / eOGPT / OnlineMoney value; the only map-side name hit is `PosObject_PIP` (twice).
    Dead Men's level folder holds four FA levels (M01 M02 M03 M06): there is no prison FA map to stand next to.
14. **Enemies.** `squadchk.py M08_A`: 49 enemy squads, 105 actors; 16 squads / 43 actors stand on or at the
    502-polygon part itself (the report's 22 / 49 for 'piece B' counts the guard-tower rings and far towers too,
    which are small parts of their own, and two actor-less fusion squads); 7 squads / 25 actors have an actor,
    a behaviour rout and nothing odd - the seven the report names, with its counts and places (SWAT x 3879..4655,
    z 12821..13857; `Squad_Ground#01` x 12382..13017, z 8421..8847). 25 to 49 guards is inside what ran (Retomoto
    63; stock levels 21..45, READ re/map_ai.md).
15. **The three level bounds.** `sk.py M08_A find "LevelBound_BlockB.*Bound$" --vals`: kept by the pre-pass;
    `BlockB01` at (8296, 24, 11329), half (1000, 400, 250) = x 7296..9296, z 11079..11579, across the passage
    between its two doors; the two stair bounds at (9091, 142, 12977) and (7499, 123, 13818). `swapchk.py`: the
    campaign's `GeomDeactivator_StairBounds` that switches the stair bounds off is on a dropped subtree.
16. **Doors and fences.** `sk.py near / find`, `hvk.py`: cage door B (8302, 20, 12223); `GroundRoom_A` C_01
    (8300, 20, 11579) and C_02 (8300, 21, 10527); `GroundRoom_B` C_01 (8300, 21, 7071) and C_02 (8299, 21, 6020);
    fences at (9300, 0, 4900) and (9941, 0, 4913); proxies `MatPosProxy_B_HallwayBars` (frames 1..50, three doors)
    and `MatPosAnimProxy_LastGate` (0..50, two) on dropped subtrees. `lanetri.py` along the passage, the last gate
    and the fence line: each of the seven closes the way at load (collision at y 30..180).
17. **Where the first-time controllers are.** `sk.py M08_A ctrl ...`: `EffectDmgBox` 15 = block B's hall 8,
    birdcage 4, outside block B 1, east kitchen yard 2; `LightToggle` 7, `AnimSequence` 5, `ZHingeConstraint` 1 on
    the block A / cantina / kitchen / laundry side. Crowd: 6 `ZHFlowFF2M08` + 6 `ZHFlowLnkObj`, dropped.
    `sk.py count ...`: none of the four is in any stock level F01..F09 or in the four Dead Men FA maps or M09_B;
    M09_A has one `AnimSequence`, on `AI_Players!Enemies!020_Office!ChairsController` (a subtree the pre-pass drops;
    whether the Retomoto layer kept it was not looked at). So 'first time' is not an artefact of kl_maps.PROVEN.
18. **Music and announcements.** `python tools/kl_str.py list "<DM>/PC_Def.str" M08`: 261 clips; `Prison_L1` and
    `Prison_L2`, 250.3 s, three layers, 0x2dd4214 bytes each (48 MB); nothing of `InHouse/M08` in the merged file;
    `FA_SlashMixPrison` (251.6 s) in both; the four lockdown lines and their `_Effect` twins.
19. **The cut estimate.** Re-run of the FIRST agent's `cut.py` (not an independent derivation): 44,776 / 23,410 /
    21,366 chunks. `Select` takes top-level subtrees only: READ tools/kl_graft.py, class Select.
20. **Slots.** READ tools/kl_expansion.py lines 57-60: six free entries a page, five maps take the first five.
21. **The escape strip.** Picture `<P2>/pics/south_yard.png`: each fence spans the whole yard strip from wall
    to wall (z 4010..5795); the car park opens behind them.
22. **The west door of block B is an open doorway.** `lanetri.py M08_A 4600 6800 13400 60 30 180`: 0 shapes; the
    only thing there is `PathBlocker_B_Entry`, on a dropped subtree. So the SWAT squad can walk in - and the map
    is open to the east kitchen yard, which needs the level bound the report proposes.
23. **Nothing else of the campaign's scripts changes the route.** `swapchk.py M08_A 5000 14500 3400 15600`: 244
    switched things on this side; apart from the fences, the entrance fence and the stair bounds they are cell
    lights, the control room's wall map, sounds and smoke.
24. **`kl_fa_author.py` is Retomoto's.** READ: `HOST, PART_B, PART_A = 'F07', 'M09_B', 'M09_A'` and every table.

### Corrected (each is also marked in place)

1. **The gate is not at x 14000** (sections 1.4, 4.3; blocker 4). (14000, 0, 8800) is the fence piece's origin.
   Its collision crosses the lane at x 13226..13300; the piece is a fenced lock x 13226..13936 inside the wall;
   the wall's portal at x 13958..14041 (`Entrance_Open_03 / _04`) is clear below y 350. `lanetri.py M08_A 10800
   16000 8800 110 <y0> <y1>`, `lanebox.py`, pictures `gate_area.png`, `gate_zoom.png`. Consequences: the stop
   (12900) puts the van's nose AT the fence; the mesh ends at x 13171, so nobody walks beyond it.
2. **The van's lane, piece by piece** (4.3): clear from x 11000 to 13200 and from 13300 on; the planter and both
   tyre slicers are flat (y <= 2); the waiting place (11300) is under the canopy of the gate building
   `Wall_B_Entry_01` in front of shut steel doors, not 'in the car park'; the ground is y -20, not 0, and ENDS at
   x 13955 (no collision under the lane outside the wall).
3. **'A heading has to be added'** (4.3): it exists. READ tools/kl_map_escape.py - the van re-lay turns every
   rotation key to the drive and has driven on three maps in the game; only the path's input is missing.
4. **The chunk table has a fourth way** (3.2, blocker 1): host F05. MEASURED: F05 + M08_A = 61,504 entries, no
   chunk problem, no compaction. Unproven in its own way (no Dead Men map has run under another host; the tools
   name F07's objects).
5. **Units of the size table** (3.4): stock columns MiB, prison columns MB. In one unit the lightened prison is
   133 MiB of large blocks against stock F07's 138.
6. **'Every place is on piece B, off mesh 0'** (4.3): 3 of the 4 control-room places and 4 of the 5 tower places
   are prop origins 0.7 .. 2.5 m off the mesh; and control room B is behind slide doors (seven slide doors on
   the upper level, all type 4 with a path blocker: `hvk.py`; the report says six).
7. **'Each door prefab carries its own path blocker'** (5): only `CageDor_B_01` and the slide doors. The four
   `CageDor_C_*` have none - so AI (the seven heisters and the police) will path INTO those doors while they are
   shut; the hold in the yard has to be made by the squad's steps, not by the mesh.
8. **'A block-B-side map meets one of these'** (3.5): the map is kept whole; all four first-time controllers
   are set up at load.
9. **0x686a66** (3.6, risk 9): the cause is read since (re/crash_686a66.md): a FakeTarget outside the vision
   grid, not a defend rout.
10. **'Dog Days plays the Dead Men KEYS chunk is still an assumption'** (risk 2): a live hint exists (the bank's
    roller doors, seen by the owner), every route door is a key-framed body that can be removed with its entity,
    and - the other side of it - there is no way round any of the seven.
11. **.SND leftovers** (2): eight `Fragile_Alliance_0N.wav` menu names besides 'Vaultbreaker'; systems side.

### Holes in the proposed round (what the corrections add up to)

- **Seven closures in series, no bypass.** START -> yard needs three doors, yard -> south yard two, south yard
  -> car park two fences. `bypass.py`: closing the polygon under ANY ONE leaves no way. The 'beat' (the gate
  opens after 30 s) needs four proxied animations to play; the fall-back (remove the leaves) keeps the round and
  loses the beat. First live question after the load, before anything is authored.
- **The escape coordinates are wrong by the gate's place and the ground's height.** A van laid as written stops
  with its nose in a fence that is 7.7 m nearer than assumed and floats 20 over the ground.
- **Upstairs loot is the expensive part.** Control room B = stairs (campaign level bound on them) + one or two
  slide doors (opened in the campaign by a mini cut scene that is dropped) + stacks moved off the props onto the
  floor. A first build should put all loot on the hall's ground floor.
- **The START is under the guns.** The eight shotgun guards of the upper ring stand at x 10061..10541, y 920 -
  3 to 7 m east of the row and 9 m above it, not 'down the hall'. Retomoto's lesson (guards wait for GO) is not
  optional here.
- **Fires beside the route.** The fire box at (9527, -1, 13509) is 2.7 m from the START row, (8586, 54, 13122)
  2 m from the hall-centre station; whether `EffectDmgBox` burns a Dog Days player is not known.
- **Vans 02 / 03.** Wherever F07's two unused vans are parked, their FakeTargets must be inside the rooms'
  bounds (re/crash_686a66.md).

### Could not be verified

- That a compacted level, or a level under host F05, loads and shows right: live only. Either is the first load.
- That the door proxies open the doors in Dog Days and that the doors' collision goes with them: a live hint
  for one construction, nothing for these doors.
- The effort figure 0.7. My reading (GUESS): not below Retomoto's until the generic authoring tool of
  re/campaign_fa_tooling.md exists - one level and no join on one side, an unproven first load, seven serial
  closures, seven slide doors and 61 rooms on the other.
- About 4 million of loot, the 30 s hold, the SWAT squad coming in when its box is moved: design GUESSES.
- The census of inmates, weapons and animation sets (1.5), the room table (1.2), which `PlayMusic` object plays
  which set: not re-derived.
- The dope-bag prop on another level's loot object: READ only (re/retomoto_loot.md proves the suitcase offline).
- What the ground LOOKS like east of the wall (there is no collision; a `DesertGrass` terrain piece and the room
  `Escape_Parking_01` exist): the model was not drawn.
- Retomoto's comparison numbers (entities, rooms, blocks): READ from other notes, not measured here.

<!-- cfa-fill2 section begins -->
## Gap closed: 242 gates - nothing in kl2.exe is sized by a level's gate total; the fixed sizes that exist are per room or per frame, and the prison is under every one (2026-10-11, agent cfa-fill2)

**The gap (the critic's).** The prison graft has 61 rooms and 242 gates; the most in a stock Dog Days level is 207
(F09). The second tooling agent had answered '61 rooms' with stock L03 but counted rooms only, and nobody had read
whether the room fix-up (kl2 0x48e910, the old room crash) or anything behind it has a fixed capacity.

**The answer.** No. A gate record is never copied into a table: every reader walks ONE room's array in place, with a
32-bit count. There is no cap between 207 and 242, so no room had to be retyped and no rebuild was made (the step the
task kept for that case). What IS fixed is per room or per frame, and each was measured on the prison:

| fixed size / narrow counter (all READ off kl2.exe, sites below) | holds | the prison graft (MEASURED) | most in a stock level (MEASURED) |
|---|---:|---:|---:|
| gate count of a room | u32 | 17 (`M08_A_Inside_Main`) | 17 (F03, L03) |
| gate index inside a room (three readers) | u16 | 16 | 16 |
| neighbour-list count of a room | u8 = 255 | 10 (`M08_A_Inside_Main`) | 9 (L03) |
| distinct list heads of one room on the stack (0x83dca0, NOT tested) | 32, of which 1 - 2 are the room's own | 10 lists -> 12 at most | 9 lists -> 11 |
| a room's own items + entries of all its lists (0x83dca0, int3) | 5,120 | 55 list entries | 869 (L10) |
| gates one segment may cross (0x6e5b20; the callee stops at it) | 16 | bounded by the code | same |
| frustum records per camera per frame (0x522cc0, NOT tested in Dog Days) | 1,024 | **67 at most** (simulation, every direction at once) | **87** (F09) |
| room records per camera per frame (0x522cc0, NOT tested) | 4,096 | 31 rooms reached at most | 28 (F09) |
| neighbour runs of one room visit, on the stack (0x522cc0, NOT tested) | 256 | <= the room's gates = 17 | 17 |
| sound-route slots per update (0x576b10; int3 when the count reaches 32) | 31 = the listener's room + 30 routes | 24 at most (`M08_A_Outside_KitchenYard`) | 23 (F09) |
| .sgp route index / room number | u16 / 14 bits | 721 edges, 61 rooms | 732 edges (F09), 63 rooms (L03) |
| room boxes of the point index (.rmi), walked in place | octree: 12-bit items per node, 16-bit indices | 172 boxes, 11 in a node | 108 boxes, 15 in a node (F09) |
| level totals: gates / neighbour lists / list entries / .sgp portals | no table found | 242 / 127 / 550 / 121 | 207 (F09) / 147 (L03) / 1,111 (L10) / 102 (F09) |

So the prison is past stock in four counts - 242 gates (207), 121 sound portals (102), 172 room boxes (108), 10
neighbour lists in one room (9) - and by one in a fifth, 24 sound-route slots (23); none is near what the code can hold. The verdict of this
report does not change; risk 5 of section 6 changes from 'nobody counted' to 'counted, under every fixed size found;
still never loaded'.

### 1. What reads a gate record (READ: `python debug/dasm.py <address>`, listings kept in `G:/kl_scratch/cfa_fill2/`)

How the readers were found (MEASURED): `scan_imul.py` - 65 functions of kl2.exe multiply by the gate stride 0x74, five
of them next to a room's gate array `[r + 0x7c]` (0x44aeb0, 0x5e2b30, 0x5e4930, 0x8bcef0 and a false hit 0x761460);
`scan_add.py` - 12 functions step a pointer by 0x74 and read `[r + 0x7c]`, three of them gate walkers (0x48e910,
0x522cc0, 0x6e5b20; the other nine were looked at with `ctx.py` and walk other structures). ASSUMED: no reader walks
the array without one of these two instruction forms.

- **0x48e910, the load fix-up** (`dasm_48e910.txt`). Called once per room entity from the loader's walk over EVERY
  entity (0x8adf05 .. 0x8adf6f: class test against `[0x150c4dc]`, next entity through vtable +0x78): there is no room
  table. Room +0x78 = gate count, compared as a dword (0x48e975), +0x7c = the gate array in the .buf, walked in place
  with stride 0x74 (0x48e972): the neighbour's REF id at gate +0x30 becomes its pointer (0x48e95b), flag 2 of +0x36
  ('has a neighbour') is cleared when it names nothing (0x48e96d), flag 4 of the first gate marks the room as done
  (0x48e925). Room +0xa8 =
  the neighbour-list count, read as a BYTE (`movzx ecx, byte ptr [ebp + 0xa8]`, 0x48ea22), +0xa4 = the lists:
  {REF, n, offset} and n REF ids, all turned into pointers in place (0x48e9c7 .. 0x48ea1c). Nothing is allocated and
  no total is kept. The REF table it resolves through is `alloca((header +0x3c + 1) * 4)` (0x8ad888 .. 0x8ad898):
  sized by the file (the graft: 34,188 slots; stock L10 77,599 - MEASURED `gatecount.py`).
- **0x522cc0, the visibility walk** (`dasm_522cc0.txt`; started per frame by 0x54f870, which zeroes both counts at
  0x54f882 / 0x54f888). For every open gate of a room that faces the eye it hands the neighbour a frustum, clipped
  against each frustum the room itself was reached by (0x477af0, 0x43d8b0), and then visits the neighbours. It appends
  12-byte room records at this+0xe8 (count this+0xe4) and 0x34-byte frusta at this+0xc0ec (count this+0xc0e8; `rep
  movsd` of 13 dwords at 0x522ea9 / 0x522fad). The function holds 16 `cmp` / `test` and no `int3`: NEITHER count is
  tested. Sizes from the layout: (0xc0e8 - 0xe8) / 12 = **4,096** room records; the member after the frusta is
  this+0x190ec (written by 0x40a8d0 at 0x40a9df), (0x190ec - 0xc0ec) / 0x34 = **1,024** frusta, both divisions exact.
  **Dead Men has the same function with the tests still in it** (kaneandlynch.exe 0x4764d0, same 0x924-byte frame;
  `python G:/kl_scratch/cfa_fill2/dasm_dm.py 4764d0 400`): `cmp [ebp + 0xe4], 0x800 / jbe / int3` (0x4765f2) and
  `cmp [ebp + 0x60e8], 0x400 / jbe / int3` (0x4766f5, 0x476834). So the frustum pool is 1,024 in BOTH games, Dog Days
  doubled the room records and dropped the tests; a 1,025th frustum would be written over this+0x190ec (the camera's
  plane count) and this+0x190f4 (the camera's room). Also on its stack: 256 {room record, old list head} pairs
  ((0x924 + 0x10 - 0x134) / 8), one per run of consecutive gates to one neighbour - at most the room's gate count -
  and in 0x54f870 512 start rooms, filled by a query that is given the end of the array (0x54fa35).
- **0x6e5b20, gates crossed by a segment**: writes u16 gate indices into the caller's array and stops when the
  caller's capacity is reached (0x6e5c06). Its three call sites (0x44af91, 0x44b033, 0x5e4aba) pass 16.
- **0x8bcef0** (closes or opens the gates that lead into a room, flag 1 of +0x36) and **0x5e2b30** (sound, the
  listener's room) index a room's gates through a 16-bit register (`movzx eax, bx`, `movzx ecx, di`).
- **0x83dca0, the one reader of the neighbour lists besides the fix-up** (`scan_lists.py`, `dasm_83dca0.txt`; called
  from 0x495f45). It collects the objects that count for a room: the room's own (0x79dfe0, bounded by the end of a
  0x5000-byte buffer) and every entry of its lists. `cmp eax, 0x1400 / jbe / int3` at 0x83de78 (own items + all list
  entries) and `cmp edx, 0x1400 / jb / int3` at 0x83e018: asserts that are still in the retail exe. The heads of the
  lists go, distinct, into a stack array at esp+0x30 of 32 dwords ((0xa0 + 0x10 - 0x30) / 4; 0x83dec0 .. 0x83ded5)
  that is NOT tested; it starts with one or two objects of the room itself (0x83dcdb .. 0x83dcfe).

### 2. The counts (MEASURED: `python G:/kl_scratch/cfa_fill2/gatecount.py "<work>/build/cfa/fill2/F07+M08_A campaign/F01_Main.zip"`, output `gatecount.txt`)

The build is a fresh `python tools/kl_maps.py one "<work>/build/cfa/fill2" F07 M08_A --campaign --keep` (log
`G:/kl_scratch/cfa_fill2/build_keep.log`: 'verify: problems: 12', the known twelve; `result.json`, `log.txt`,
`graft.txt` kept, the archive deleted - the scripts below that take the archive need that command run again).

| | rooms | gates | most in a room | lists | most in a room | list entries | most in a list | gates closed at load | .sgp portals / edges / routes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| the prison graft | 61 | **242** | 17 | 127 | **10** | 550 | 50 | 0 | **121** / 721 / 9,289 |
| Dead Men M08_A itself | 65 | 242 | 17 | 127 | 10 | 550 | 50 | 0 | 121 / 721 / 9,289 |
| F09 (stock most gates) | 43 | 207 | 15 | 129 | 8 | 507 | 21 | 0 | 102 / 732 / 20,648 |
| L03 (stock most rooms) | 63 | 176 | 17 | 147 | 9 | 559 | 16 | 0 | 88 / 328 / 2,812 |
| F03 | 21 | 104 | 17 | 46 | 8 | 338 | 22 | 0 | 51 / 405 / 12,039 |
| L10 | 31 | 68 | 5 | 52 | 3 | 1,111 | 366 | 0 | 34 / 66 / 330 |

- The graft carries Dead Men's gates one for one: every count equals M08_A's own; of its 61 rooms 60 are the
  map's, each with the gate and list count of its M08_A room, and one is F07's `DebugRoom` without a gate. The five
  ZROOM-derived entities of M08_A that are not in the graft (`AI_Players!Crowd01`, three `Scope_Dragunov` rooms and
  `IngameMapGroup` of Dead Men's systems side) have no gate and no list (`lostrooms.py`, `toprooms.py`).
- Rooms are counted here as ZROOM-derived entities (`roomdata.py`, as `kl_graft.is_room` and the build's own '61'
  do); by that count stock L03 has 63 = 61 ZROOM + 2 ZBackdrop (the '61' of tooling 11.2 counts classes named
  ...ROOM: READ `G:/kl_scratch/cfa_tooling_v2/rooms2.py`). The graft's 61 hold one ZBackdrop too.
- The prison's gate histogram {gates: rooms}: {0: 4, 1: 9, 2: 16, 3: 6, 4: 5, 5: 6, 6: 3, 7: 3, 8: 4, 9: 2, 13: 1,
  14: 1, 17: 1} (`toprooms.txt`); the three big ones are `M08_A_Inside_Main` 17, `M08_A_Outside_BirdCage` 14,
  `M08_A_Outside_VisitingToEntry` 13.
- What the lists hold (`listkinds.py`): 127 heads, all ZROOM; 550 entries = 485 ZSTDOBJ, 3 lights, 62 REF ids that
  name nothing in the graft (the engine clears those: 0x48ea11; stock L10 has 355 such, L05 204).

### 3. The one pool that grows with gates seen through gates: the 1,024 frusta (MEASURED by simulation)

`python G:/kl_scratch/cfa_fill2/vissim.py <level or archive> [--grid 150] [--detail N]` replays 0x54f870 / 0x522cc0 /
0x477af0 / 0x43d8b0 on a level's own gate records and counts the frustum records one frame takes.

Simulated as read: start rooms = the rooms whose `.rmi` box holds the eye (0x927b30); a gate is skipped when closed,
without neighbour or when the neighbour is on the current path; the facing test `n = (c1 - c0) x (c2 - c0)`, eye on
n's side (0x477b80); from a start room every facing gate gives the frustum of four planes `norm(p_k x p_k+1)`; from
any other room every gate is tried against every NEW frustum of the room, a corner being outside a plane when the
dot product is > 0.0, the output plane of an edge being the gate's own edge plane or - when both ends are outside one
incoming plane - that plane (0x43dc0a .. 0x43de76); a neighbour is visited once per run of consecutive gates that
reached it, with the frusta added since. NOT simulated, each on the safe side: the camera's own planes (the count is
for EVERY direction at once - an upper bound for any view from that point, because the planes only decide pass or
fail in 0x477af0 and never shape a frustum), doors that close gates at run time (all open, as stored), the finer
ZBOUND test of 42 of the graft's 172 room boxes and the room flag at +0x118 (a start room too many, never one too
few). ASSUMED: the eye sample - every navigation polygon's centre and every waypoint raised 160 units, two points 40
units either side of every gate, and with `--grid 150` a 150-unit grid at three heights through every room box.

| level | eye points | frusta in one frame: median / 99 % / **most** | most rooms reached | deepest chain |
|---|---:|---|---:|---:|
| the prison graft, mesh + gates | 2,096 | 14 / 47 / **57** | 27 | 7 |
| the prison graft, + grid 150 | 169,627 | 24 / 51 / **67** (`M08_A_Inside_Main`, eye (1414, 770, 735)) | 31 | 8 |
| Dead Men M08_A itself, mesh + gates | 2,096 | 14 / 47 / 57 | 27 | 7 |
| F09, mesh + gates / + grid 150 | 1,797 / 736,033 | 22 / 61 / 77 and 11 / 39 / **87** | 28 | 7 |
| F03, mesh + gates / + grid 150 | 1,593 / 946,352 | 14 / 39 / 45 and 17 / 25 / 46 | 17 | 6 |
| L03 (63 rooms), mesh + gates | 2,788 | 5 / 23 / 28 | 18 | 5 |
| L03 (63 rooms), + grid 150 | 16,777 | 4 / 23 / 28 | 19 | 5 |
| every other stock level, mesh + gates | 8 .. 3,237 | most 30 (F05, L09) or less | 14 | 5 |
| every other stock level, + grid 150 | 1,338 .. 640,670 | most 32 (L09), 30 (F05), 28 (L08) or less | 16 | 5 |

(outputs `vissim_prison_omni.txt`, `vissim_stock_omni.txt`, `vissim_grid.txt`, `vissim_grid_a.txt`, `vissim_grid_b.txt`:
all 21 stock levels were run both ways.) The prison needs at most 67 of the 1,024 records, less than stock F09's 87
by the same measure and more than any other stock level's (F03 46, L09 32). Dead Men ran this level against the same 1,024 with the
test in place.

Checks of the simulation itself (MEASURED): `frames.py` - every room and every ancestor of a room has the one default
rotation and (a few backdrops and F05's two lift shafts aside) no translation, and a gate's four corners coincide with
its twin's in the neighbour room (the graft: 210 of 242 within 1 unit, the other 32 within 8; 11 stock levels all
within 1 unit, 8 more within 10), so the corners are world coordinates; `winding.py` - in every level the two
gates of a pair have opposite normals (the graft 242 of 242, stock 100 % in all 20 levels with gates) and a gate
faces the centre of its own room's `.rmc` box in 88 % of the graft's gates (stock 57 .. 93 %, Dead Men's M03_FA_A,
which has run in Dog Days, 85 %), so the sign of the facing test is read the right way round and Dead Men's gates are
wound as Dog Days' are (Dead Men's own test 0x475730 is the same instructions as 0x477af0: READ); `facing.py` - the
same test from the mesh points inside a room: 87 % (F07), 90 % (F09), but only 57 % for the graft, whose mesh points
lie in two or three overlapping boxes each (`boxes.py`: 1,502 of 1,612 in two, 109 in three) - the simulation
starts from every one of those rooms, as the engine does where a box has no ZBOUND; `boxes.py` - the mesh stores a
position as (x, z, y) (F07: 167 of 168 sampled points fall into a room box that way, 41 or 0 the other five ways).

### 4. Sound: the .sgp reader is found, and its arrays are as large as the file says (READ + MEASURED)

`tools/kl_members.py` says of the .sgp 'the code that walks it was NOT located' (READ its docstring). It is
`ZSoundGraph` (vtable 0xb9a614, an object of 0x128c bytes made at 0x70d35c): slot 1 = 0x75ee20 reads the five counts
and copies portals (count x 0x5c), edges (x 12), rooms (x 12), routes (x 4) and the portal list (x 4) into heap
blocks of exactly those sizes (0x75eea9 .. 0x75eff4, each multiplication tested for overflow), then gives every room
entity its .sgp number by its scene path (room +0xc4, 0x75f0bf). No fixed table, so 121 portals against stock's 102
meet nothing. The one fixed size is in the update (slot 3 = 0x576b10): 32 route slots of 0x8c bytes on the stack
(0x576b80 .. 0x576ba8), slot 0 the listener's own room, one more per DISTINCT route by which a playing sound reaches
that room (the search 0x71da90 compares the route's index list; a new one is appended at 0x57712c and the count
raised at 0x577131 with no test), and after the loop `cmp [esp + 0x14], 0x20 / jl / int3` (0x576d1f): the count
must stay under 32. The route finder 0x5866a0 takes only a direct route of the kind 'portal' or 'edge' (two
portals) between the sound's room and the listener's (the third kind, through a room, is skipped at 0x5867d7) and
chooses among a pair's alternatives by distances from ONE point (its sixth argument, made once per update at
0x576b52 .. 0x576b66, before the loop over the sounds; ASSUMED the listener's place) - so all sounds of one room
arrive by one route, and the most a listener's room can ask for is 1 + the rooms that have a portal or edge route
with it. MEASURED `sgpdeg.py`: the
graft 24 (`M08_A_Outside_KitchenYard`, 23 rooms), stock most 23 (`F09_Outside_C_CornerLeftFirst`); no room of any
level reaches 32. For the record the wider count, every portal / edge route RECORD that ends in one room
(`sgpdeg2.py`): the graft 80, stock F09 110, F03 101.

The room boxes. The graft's `.rmi` has 172 boxes (42 of them with a ZBOUND), the most in a stock level is 108 (F09,
20 with a ZBOUND); its `.rmc` 61 against 63 (L03) - MEASURED `rmicount.py`. The file is an octree the engine walks
in place: the point query 0x477830 hands the tree its callback 0x927b30, the base of the records (0x9a9c80) and
the caller's array with its end, so no table is sized by the boxes. The tree's own counters are 12 bits for the
items of a node and 16 bits for node and item numbers (READ `tools/kl_octree.py` docstring): the graft has 66
nodes and at most 11 items in one (stock: 15).

### 5. What this does not show

- Nothing here was loaded. That the prison is under every fixed size FOUND is a reading of kl2.exe plus counts; a
  size in code that was not found would not show (the scan rests on the two instruction forms of section 1).
- The frustum count is a simulation on sampled eye points, not a measurement in the game. It is an upper bound per
  point; the margin (67 of 1,024) is what carries the claim, not the exact figure.
- The room's 'own items' of 0x83dca0 (the other half of its 5,120) are objects registered with a room while the game
  runs: not countable offline. The list half is 55 for the prison's worst room against 869 for stock L10's.
- Four counts are firsts all the same (242 gates, 121 sound portals, 172 room boxes, 10 lists in one room). If a room-related fault
  ever shows on this map, the sites to look at first are 0x522cc0 (this+0xc0e8 over 1,024), 0x576d1f (int3) and
  0x83de78 / 0x83e018 (int3).

**Corrected in place** (marked 'gap closed'): 3.6 row 'room fix-up', section 6 risk 5; in `re/campaign_fa.md` the
limits table of section 1 and the 'Open:' line of 4.3 ('corrected after the critic'). Scripts and outputs:
`G:/kl_scratch/cfa_fill2/` (`roomdata.py`, `gatecount.py`, `vissim.py`, `frames.py`, `facing.py`, `boxes.py`,
`sgpdeg.py`, `sgpdeg2.py`, `rmicount.py`, `winding.py`, `listkinds.py`, `toprooms.py`, `lostrooms.py`, `scan_imul.py`, `scan_add.py`, `scan_lists.py`, `scan_dm.py`, `disp.py`,
`xref.py`, `ctx.py`, `dasm_dm.py` and the listings / outputs named above).
<!-- cfa-fill2 section ends -->
