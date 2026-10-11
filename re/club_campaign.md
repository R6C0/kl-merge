# The club (Dead Men M05_A 'The Mizuki') as a Fragile Alliance map - build notes

Map 2 of the campaign places (map 1: re/bank_campaign.md, the worked example of every step). The study:
re/campaign_fa_club.md (its section 8 and the notes 'corrected after the critic' weigh more than the first text),
re/campaign_fa.md 4.2 and G1.3 / G1.8, re/campaign_fa_tooling.md 11 - 12. Each stage appends a section here.
`<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`.

## Stage T - the converter case (tools/kl_mat.py: TEXT/TILU = MIRRORED)

STATE: DONE (2026-10-11 19:45). All checks pass; no archive is left (the builds ran without `--keep`). Kept in
C:/kl_scratch/club/t/ (0.2 MB): s/ (baseline.py, mirror.py, results.py), out/ (before.json, after.json, mirror.txt,
check.txt, bare.log, nobounds.log, results_*.txt) and result.json / log.txt / graft.txt of the two builds.
Offline only; nothing run in the game.

### T.0 Baseline, made BEFORE the edit (tree at 26ea22d, tools/kl_mat.py sha1 fa8db3da)

`python C:/kl_scratch/club/t/s/baseline.py C:/kl_scratch/club/t/out/before.json`: for ALL 20 Dead Men levels (not only
the seven that are built today) the sha1 of the converted .MAT, twice - 'plain' = `kl_mat.convert_mat_full(data)` with
every default, 'build' = `kl_dmassets.convert_level(level)` (the path a graft takes: the converted .prm and the .TEX's
ids handed in) - plus a hash of the converter's report. MEASURED: 18 levels convert, two are refused:
M05_A (`material 538 ... TEXT/TILU value b'MIRRORED' never occurs in Dog Days`) and M01_A (material 615, the same).
The 'build' hashes of the seven named levels: M01_FA_A 4acc31b5, M02_FA_A 0250c1f1, M03_FA_A 69052ef3, M06_FA_A
ef95b22e, M03_A 5890e380, M09_A 98d3e153, M09_B 988021ef (whole values in before.json).

### T.1 What was changed (one file, tools/kl_mat.py, +19 lines)

- NEW table `STRING_MAP = {('TEXT', 'TILU', b'MIRRORED'): b'TILED'}` beside CLASS_MAP, with the comment that says
  what Dog Days has instead and what the look difference is.
- In `convert_mat_full`'s string guard (was line 396-397): a value Dog Days never has on that (node, key) is looked
  up in STRING_MAP first; a hit whose target Dog Days does have is written (node count = length + 1, value) and
  counted in the report's NEW key `strings` {('slot node/key', old, new): n}; everything else raises as before.
  The table is consulted ONLY where the old code raised, so a level that converted before cannot change.
- Docstring: the report key, and point 2's 'every string value is the same in both games' gains 'but for
  STRING_MAP's one case'.
- NOT done, on purpose: the study's other proposal (accept MIRRORED on U because Dog Days has it on V). READ
  re/campaign_fa_club.md 8 'Not corrected, but weaker than it reads': how kl2.exe turns the value's name into an
  addressing mode was not found ('MIRR' is nowhere in the exe), so MIRRORED on U stays ASSUMED; TILED is the one
  value certain to be read there (27,965 stock bindings).

THE LOOK DIFFERENCE (MEASURED `python C:/kl_scratch/club/t/s/mirror.py M05_A M01_A` -> out/mirror.txt): the picture
repeats along U where Dead Men flipped every second repeat. Carried by
- M05_A slot 538 `Locations/M05/Concrete/Concrete_Walkway_01a_M05` (class Standard/Standard, 5 uses in the .prm): three
  stages - mapDiffuse (texture 941 `Locations/M05/Concrete/Concrete_Walkway_01_M05`), mapNormal (184
  `Locations/M05/Plaster/Plaster_Basic_01_M05`), mapSpecularMask (no texture). TILV is TILED on all three already.
  ONE material of the club: a concrete walkway surface. Where its five meshes stand was NOT looked up; if a seam
  shows on a walkway's concrete in the game, this is the cause.
- M01_A slot 615 `Vechicles/Civil_USA_01/V_Civ_USA_01_02` (2 uses): mapDiffuse only. Not this job's level; it now
  converts too.
No other Dead Men level has the value.

### T.2 Checks

1. **The baselines are byte-identical - PASS.** `python C:/kl_scratch/club/t/s/baseline.py .../out/after.json`, then
   the comparison of the two files: 'identical levels: 18 of 20' - for each of the 18 the 'plain' hash, the 'build'
   hash, both sizes AND the report's hash (without the new, empty `strings` key) are the same; the two that differ
   are the two that were refused: M05_A now 527,600 bytes (build e7efc9cd, `strings` {'538 TEXT/TILU -> MIRRORED ->
   TILED': 3}), M01_A 763,872 bytes (build 40e5e693, {'615 ...': 1}). So the bank (M03_A), Retomoto (M09_A / M09_B)
   and the four Fragile Alliance maps get the same .MAT as before; no rebuild of any of them was made or is needed.
2. **The written file reads back - PASS** (out/check.txt): M05_A `kl_mat.check` (690, 9), `kl_dmassets.cross_check`
   []; slot 538's three stages read TILU (6, b'TILED'); M01_A (1014, 9), [] and slot 615 the same.
3. **The stock command builds, with the study's numbers - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/bare" F07 M05_A --campaign` (34 s; exit code 1 because verify's
   problems are not 0, as for every level without a layer) -> 'verify: problems: 11', 'built ... F01_Main.zip, 284
   MB, 30 members'. result.json: entities **26,106**, rooms 20, textures 1,676, materials 1,135, prm_chunks 52,934
   (= **52,935** chunk-table entries), dangling [], tops 395, ref_slots 36,987, archive 284.4 MB; problems **11** =
   1 sound ('5 stream clips are not in the merged stream file') + 1 CRASH (no OnlineFragileAllianceSettings) + 9
   BROKEN (define, exit trigger, START / AFTER_DEATH points, three gameplay triggers, loot, squads).
   `python s/results.py <mine> "<work>/build/cfa/club/patched/F07+M05_A campaign" ".../sk_patched/..."`: **0 of 34
   keys differ** from the first agent's and from the second agent's build made with the outside wrapper (every key
   of result.json but 'seconds').
4. **The variant without the campaign's bounds - PASS.**
   `python tools/kl_maps.py one "C:/kl_scratch/club/t/nobounds" F07 M05_A --campaign --m-drop "Boundaries!*"` ->
   'verify: problems: 11'; entities **26,091** (15 fewer), tops 380, ref_slots 36,972, dangling [], the rest as in 3;
   0 of 34 keys differ from `<work>/build/cfa/club/nobounds` and `.../sk_nobounds`.

### T.3 GUESS / ASSUMED

- ASSUMED: TILED on U is drawn as plain repetition in Dog Days (it is what 27,965 stock bindings have; not seen in
  the game for this material). The look difference itself is by definition, not measured on a picture.
- Not established (unchanged from the study): what Dog Days would draw for MIRRORED on U.

### T.4 For the next stages

- The bare build: `python tools/kl_maps.py one <out> F07 M05_A --campaign --m-drop "Boundaries!*"` (add `--keep` to
  read the archive back; the folder inside <out> is 'F07+M05_A campaign' with or without --m-drop, so two variants
  need two <out> folders). 34 s, 284 MB archive.
- No outside wrapper is needed any more: G:/kl_scratch/cfa_club/run_maps.py and the study's `build_open.py` patch of
  `TM.read_mat` give the same bytes as the stock tools now (check 3), but they substitute on TILV too and on every
  node - use the stock command.
- kl_whoref.py and every other tool that converts M05_A through kl_graft.DeadMen now runs on it (they died at the
  same line; not re-run here).
- The report key `strings` is new: `kl_dmassets`'s log line does not print it (that file is another session's).

### T.5 Open

- Whether the walkway material's five meshes are on the round's route (then the tiling is in sight) - not looked up.
- The bank's regression (`kl_fa_bank.py check` on `<work>/build/c_bank/bank_vault`) was NOT re-run: M03_A's converted
  .MAT is byte-identical (check 1) and that tree is not this stage's to touch.

## Stage L1 - the authoring module, first half: a round without enemies (NEW tools/kl_fa_club.py)

STATE: DONE (2026-10-11 20:30). `tools/kl_fa_club.py` (1,256 lines) holds the nine names of the interface and builds
F07 + M05_A with the first half of the layer; every check of the stage passes with TWO known findings, both justified
below (L1.3). NOTHING RAN IN THE GAME (another session holds it). Kept for the next stage:
`C:/kl_scratch/club/l1/build/F07+M05_A campaign/` (174 MB: F01_Main.zip 135,476,152 bytes, sha1 f109b3ca4bda..., lightened,
briefcases and texts in; result.json, log.txt, graft.txt, preflight.json). A second build of the same command gave the
same archive (`out/again.txt`). Scratch `C:/kl_scratch/club/l1/`: `s/` (b.py nodes of a built folder by regex, scan.py a
character map of mesh + free floor, floors.py the collision floors under points, vt.py / vt34.py vtables in kl2.exe),
`out/` (every output named below), `bare/` (result and log of the bare graft the places were measured on; its archive is
deleted - rebuild: T.4's command with `--keep`, 34 s). No other file of the repo was touched: kl_fa_author.py,
kl_fa_bank.py, kl_fa_loot.py, kl_route.py, kl_maps.py are only imported / run. No per-level table of another tool gained
an entry (kl_maps.FLAT is lent one class pair for the length of the build, in memory).

### L1.1 What the file is

Pattern: kl_fa_bank.py. Its generic parts are IMPORTED (`import kl_fa_bank as BK`: `Doors`' frame arithmetic and arm /
disarm, `put` / `values` / `facing` / `world_of`, `set_text`, `archive_of`, `read_built`, `lost_clips`, `reverify`,
`BOT_SQUAD`, `BLOCKS_LIVE`, `WARDROBE_CHUNKS`), none of its tables; kl_fa_author's small tools as there. No new entity,
no new controller. NOTE FOR WHOEVER EDITS kl_fa_bank.py: those names are now used from outside (another job was
changing that file while this stage ran; the builds before and after its change gave the same archive).

| part | where | what |
|---|---|---|
| the build's own arguments | `M_DROP IK NO_BUILD`, `build()` | `Boundaries!*` out; the two `Beat_M05` objects loaded as plain ZSTDOBJ (kl_maps' `flat`) |
| the measured club | `START TRAITOR POLICE BODIES STAGE_B/C/D SPAWN SLAB LANE_MOUTH DOOR_IN` | 8 START in two rows of four in Yoko's office (x 2700..3050, z 2420 / 2560, y 342), 4 TRAITOR east of the desk (z 2290), 7 AFTER_DEATH on the pavement slab (x -900..-600 and 1300..1500, z -2760), 8 police bodies beside them (z -2830), every other kind F07 has in rows of their own; 16 player groups |
| loot | `LOOT LOOT_REACH CASE CASE_SCALE` | 11 briefcases, 2,200,000: 6 x 300,000 in the office (2 on the desk, 2 on the sofa table, 2 on the floor), 3 x 100,000 on dance floor 1's bar (top y 158), 50,000 on the coat check's counter (y 284) and on the ticket counter's shelf (y 128) - each on the PUBLIC edge; shown from the load |
| doors and the seal | `LEAVES DOORS_ANIMATE DOOR_DY DOOR_LAST DOORS_AT SEAL SEAL_PLANE SEAL_OPEN SEAL_AT MUFFLE`, class `Doors`, `doors()`, `gate()` | four office leaves; the seal's two pieces `HeroColi` / `Plane01` |
| what never ran in Dog Days | `LIGHT_SHOW BEAT_ANIM FAN_DAMAGE BEAT NEVER_RAN`, `strip()`, `take_off()` | three flags, all OFF = dropped (L1.2 'The three kinds') |
| host layer | `PLACE BOUNDS PARKED KILL ROLE KEEP_MORE VAN VAN_GROUP VAN_WAIT ESCAPE _KEEP` -> `KEEP`, `DROP` | 41 re-placed objects (markers, planes, cameras, stage boxes, jump points, three bound trios), 9 parked bound boxes, 3 campaign kill boxes, 9 objects with a new job |
| texts, sound | `TITLE TEXTS START_KEY START_FIELDS LINES EXIT_LINE MUSIC_CLIPS AMBIENCE_CLIPS` | 5 .LOC keys of the level's own, 8 briefing / reminder lines, the exit line; the 12 clips the stream file lacks |
| the interface | `HOST prepare_host strip KEEP DROP layer_names complete wire campaign_names` | as kl_graft.build's docstring asks; `campaign_names` keeps the three kill boxes and no squad (`NO_AI = True`, fixed in this half) |
| the written level | `finish(folder)` | lighten (trim, slim) -> briefcase model into dead chunk indices -> texts |
| checks | `check(folder)`, `inventory(folder)`, `ROUTE_IN ROUTE_OUT LOOT_WALKS KNOWN` | L1.3 |
| commands | `test <out> [--keep] [flags]`, `finish`, `check`, `inventory`, `reverify` | `test` = build + finish + check in one process |

**The round as wired** (MEASURED: `python tools/kl_fa_club.py inventory <kept folder>` -> `out/inventory.txt`, check()'s
'chain' line):
- round start (AIMonitor list 2): F07's `FASpecials!Timer_MissionBriefing`, the seal's clock
  `Gameplay!010_FirstFight!RivalMercVan!Timer` (TriggerDelay2 `SEAL_AT` = 75 s) and `...!Activator_VanSound` (AIDWrapper
  'Doors_Opening' -> the music's two muffle switches `...Audio.zip!STREAMS!Inside!Music!GeomActivator_Door_01 / _02`).
  wire() WRITES that list (F07's own names five timers of its opening).
- the clock -> `...RivalMercVan!GeomDeactivator_DriveInVan` (DeactivateGeom) -> `M05_A_Inside_Entrance_01a\HeroColi`.
- `Specials!LevelSpeak!TriggerBox` in the wardrobe -> its speaker, line `Multiplayer/F04/ExitHeist_01_R`.
- ENTERS box ROUND the START rows (2800, 450, 2450) half (450, 150, 320): all 8 START points and the 6 office cases
  inside (check()); EXITS plane behind the entrance door (125, 120, -1440); loot marker over the desk, its 11 s box
  round the START rows; escape marker on the slab (300, 218, -2800); exit trigger `otrExitLevel` = the slab
  (300, 200, -3050) half (1450, 250, 400): x -1150..1750, z -3450..-2650, wholly beyond the seal's box.
- team mode: stages front office / wardrobe / entrance hall with their triggers at the inner office door, the stair
  landing and the hall's top (all GUESS; nothing of that mode was thought through).

**The doors** (the lead's default). `DOORS_ANIMATE = False`: the four office leaves `D1 D2` (inner) `D04 D05` (outer) are
SUNK 1,500 in world y and their key-framed placements cut, by `Doors` = `kl_fa_bank.Doors` with this level's nodes (the
three wrappers are this file's, about 60 lines the bank's class has bound to its own tables; the frame arithmetic and
arm / disarm are inherited). Build lines: '5 nodes sunk by 1500', '5 entities moved in the .gms (2 of them hold another
local place there than in the .prp; the world places agree)' - trap 2 of G1.1, the outer door - 'placements by shape type
{4: 4, 1: 1}; none is left'. `--doors-animate`: the leaves stay, store LAST 30 and get 'Activate' from
`...RivalMercVan!TimerVanGo` 10.4 s after the round-start event (GO + 2 s), the muffle switch with them.

**The seal - and one choice of mine the lead should see.** The stage asked for 'the entrance SEAL of the beat present
from the start with its guaranteed clock'. The seal is two STATIC, heroes-only objects, each alone enough to shut the
lane (MEASURED `out/bare_doors.txt`: 4 closures, 4 necessary). By default ONE of them stands: `HeroColi` (.gms flags
0x200308, the very form of the storage room's `HeroColi`, which the campaign itself switches off with a DeactivateGeom);
`Plane01` (flags 0x308, switched by nothing in the campaign: the study's open question whether DeactivateGeom frees it)
is taken out at build time with the leaves. So the seal is present, the clock opens it, and what opens it has the
campaign's own precedent. `--seal-plane` = both stand and both are named; `--seal-open` = neither (no gate).
NOT DONE and said plainly: the gate is INVISIBLE (a wall of air 3 m before the lane's mouth); the campaign's visible
version - the entrance door shut by `Doors!Entrance!CloseEntranceDoor` - needs a Dead Men door clip to play and is the
next stage's to decide (L1.6).

**The three kinds that never ran in Dog Days** (READ in kl2.exe: `python C:/kl_scratch/club/l1/s/vt.py <Class> <Base>`,
`vt34.py`; the reasoning stands at the flags in the file):

| kind | read | default | flag |
|---|---|---|---|
| `PositionLightControl` x 7 (the light show) | own init (slot 13, 0x671cb0, 244 instructions) and an own routine in slot 25 (0x72c400, 289: ASSUMED the per-frame step), own save / load; reads `Beat_M05\Ground_Beat05` and `Club_01_Clean_Music_01` | OFF: the controller comes off, the lights are static | `--light-show` |
| `ZIKLNKOBJ` + `StartAnim` x 2 (`Beat_M05`) | StartAnim: own init (0x8f6b90, 92), no step; it starts a Dead Men .ANM clip converted by kl_anm's GUESS | OFF: loaded as plain ZSTDOBJ, no model, hidden, no StartAnim; the .ANM then holds NO Dead Men clip ('.ANM joined: clips +0') | `--beat-anim` |
| `ShotActivateDamage` x 5 (roof fans) | differs from stock `ZShotActivate` (439 in this build) in ONE routine, slot 34 (0x4bb9b0, 132); its init is the base's (0x5aa380, 22 instructions, no call of slot 34). Where slot 34 is called from was NOT found | OFF: taken off (the fans cannot be shot to pieces); they stand on the roof, off this round | `--fan-damage` |

`--light-show` without `--beat-anim` reads a still object: the two belong together. With all three off preflight's 'first'
list is down to `ZEnvSampler` x 3 and `SoundSpline` x 1, both of which ran live on Late Night Opening / the park
(re/campaign_fa_club.md 3.5).

**Bounds.** The campaign's five go (`M_DROP`). Three of F07's bound trios stand outside the slab's open edges - Bound box
6 m deep from the edge outwards, warn boxes the same and 1.2 m onto the slab - the other three are parked; the campaign's
three single `Specials!KillBox` (kept by campaign_names, re-placed in strip) lie under the edges, tops y -100: west
x -4020..-1220, east x 1820..6020, kerb and road z -5350..-3450. They punish, they do not stop (GUESS, marked).

**The van.** F07's first van only, STANDING at `VAN_WAIT` (-3000, 32, -3100) with F07's own baked drive; the exit trigger
names it alone. A first-half state, as the bank's L1: the next stages replace `park_van` by `kl_map_escape.van_prepare`.

### L1.2 The build

```
python tools/kl_fa_club.py test C:/kl_scratch/club/l1/build --keep        (about 2 min; 'RESULT: PASS', exit 0: out/test2.txt)
python tools/kl_fa_club.py check "C:/kl_scratch/club/l1/build/F07+M05_A campaign"       (25 s, 'PASS': out/check.txt)
```
`python tools/kl_maps.py one ... --author kl_fa_club` alone does NOT build this map: prepare_host stops with a line that
says why (the build needs `M_DROP` and the retype). Lines of the build:
- 'kl_maps: --flat ZIKLNKOBJ: 0x200027 is loaded as 0x200002 in this build'; 'F07 systems (411 subtrees, 9636 nodes) +
  M05_A map (242 subtrees, 16950 nodes)'; 'verified: 26586 entities, 26587 nodes, 25102 reachable chunks, 21 room sets,
  566 gate / list REF cells, 1676 textures, 1134 materials'
- 'spawn points placed: START 8, TRAITOR 4, AFTER_DEATH 7, UCC 8, UCC_TRAITOR 4, UCC_POLICE 7, TEAM_MERC 6, TEAM_MERC1..3 4
  each, TEAM_POLICE 7' + 8 + 8 player groups; 'Heroes! groups placed where M05_A has them: 0'
- 'verify: problems: 2'; 'built ... F01_Main.zip, 284 MB, 30 members'
finish: 'load weight: 1346 dead model roots; .prm 78.9 -> 38.0 MB ...; .TEX 342.3 -> 163.9 MB'; 'briefcase M01_FA_A root
6380 (DropMoney!KillDrop!Suitcase) -> chunk 70: 18 chunks into dead indices, 0 at the end'; '11 briefcases (model 70,
x 1.25, its underside 0.3 over its origin); chunk table 52910 entries, as before'; '5 text keys in 8 languages'.

### L1.3 The checks (all on the kept, finished build; outputs in `C:/kl_scratch/club/l1/out/`)

| check | command | result |
|---|---|---|
| verify problems | the build's last lines; check()'s 'verify:' lines | **2, both KNOWN**: (1) 'sound: 5 stream clips are not in the merged stream file' = the club's music and ambience (L1.5 lists the 12 names); (2) 'FA: BROKEN squads no ZSquadScript: no police' = this half IS a round without enemies. The bare graft has 11 |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 1 BROKEN** = the same 'no ZSquadScript'; 1 DEGRADED (no bot squads: a later stage). settings 1, exit trigger 1, monitor 1, animated vehicle 1, AIMonitor 1, OnlineMoneyCtrl 133 |
| cover list | check() | 'cover lists (FFCoverList): 1' (the club's own top-level `CoverList`; F07's is dropped) |
| doors and seal read back | check() | four leaves at their stock x / z, 1,500 lower, 0 placements; `HeroColi` at (131, 0, -2478) with 1; `Plane01` sunk, 0 |
| spawn points | check() (kl_route.stations, near 30, the gate taken out) | '79 places, 79 on the mesh part of the START (401 polygons) and on free floor within 30' = 63 ZSpawnPoint + 16 player groups; every one outside the building is on the slab |
| bounds, kill boxes | check() | '3 LevelBound in their place (18 bound and warn boxes with the parked ones), 3 kill boxes; 0 of the 93 spawn points, player groups and stations inside one'; at each of the slab's three edges a walker 1 m before it is in no bound, 1.2 m beyond it in one; kill boxes' tops 130 under the slab |
| loot | check() (kl_fa_loot's pick-up test as read at kl2 0x783e60, from floors a walk reaches) | '11 objects, 2200000; 11 can be taken', least 87 of reach to spare (the ticket shelf from (150, 19, -1250), 78 away, 107 up; the bar from 72 away, 137 up) |
| ... its standing places | `python tools/kl_route.py stations <folder> START=... desk=... bar_1=... --near 30` -> `stations_loot.txt` | 'RESULT: ALL REACHED', 10 of 11 on the mesh; the place before the coat check is 16 off it |
| the route as built | `python tools/kl_route.py walk <folder> --from START=2817,342,2420 --via ... --to pavement=300,30,-2800` (12 places) -> `route_built.txt` | 'NOT FREE': the leg queue lane -> street end 'BLOCKED - the thinnest crossing (11 m) goes through REF 23632 M05_A_Inside_Entrance_01a\HeroColi [STATIC mesh 0x108; stops heroes only]', nothing else |
| ... up to the seal | the same to `lane_club=105,20,-1500` -> `route_inside.txt` | 'RESULT: FREE; the mesh way: 716 samples, 1 with something in the body column' (the level's own stair `Si0102_M05_StairsA_01` beside the mesh line at (268, 40, 3150)); check(): 'FREE, 122 m' |
| ... the seal out | `... --open "M05_A_Inside_Entrance_01a\HeroColi"` -> `route_open.txt` | 'RESULT: FREE; the mesh way: 767 samples'; check(): 'FREE, 133 m' |
| doors | `python tools/kl_route.py doors <folder> ...` -> `route_doors.txt` | '1 closure(s) in 1 set(s); 1 necessary; with all of them out the way is FREE' (bare graft: 4 / 4, `bare_doors.txt`) |
| the chain | check() | 'round start -> [Timer_MissionBriefing, Timer, Activator_VanSound]; -> 75 s -> seal off [HeroColi]; doors: open at build time; the music's muffle switch Doors_Opening -> 2 objects' |
| never-run kinds | check() | PositionLightControl 0, StartAnim 0, ShotActivateDamage 0; the beat objects 'ZSTDOBJ, model none, hidden' |
| exit box, van, FakeTarget | check() | 'exit box x -1150..1750, z -3450..-2650: on the slab True; holds the pavement station True, the lane's street end False; it names [EscapeVehicle_Animation_F07]'; 'FakeTarget ... at (-2995, 31, -3084): inside the vision space, kl2's arithmetic gives a record' (vision space x -6725..10906, z -7074..6724) |
| chunk table, blocks | check() | 'chunk table: 52910 entries (the tools' line: 69632); .prm 37.3, .fxc 17.8, .ANM 21.6, .WAV 21.2 MB; the five load blocks 131 MB (...: 171)'; '23799 of its indices are dead (the wardrobe takes 20989)' |
| written level | check() / `kl_fa_club.py reverify` -> `reverify.txt` | 'problems: 0' (26,586 entities, 566 gate / list cells, 24 list entries parked on the free REF id 36975) |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | 'preflight: CRASH 1, RISK 4, NOTE 64': CRASH = 'kl_graft.verify reported 2 problems' (the two above); RISK = 'fa:squads', `ZEnvSampler` x 3 (twice) and `SoundSpline` x 1 (both ran live on other maps). The bare graft: CRASH 2, RISK 16, NOTE 65 |
| the flags | `test <out> --doors-animate --seal-plane --fan-damage` -> `var_a.txt`; `test <out> --seal-open --light-show --beat-anim --loot-bags --seal 40` -> `var_b.txt` | a: PASS - four leaves stand with LAST 30, both seal pieces stand and are named, 'route with the 6 standing piece(s) out: FREE, 133 m', ShotActivateDamage 5. b: PASS - 6 nodes sunk ({4: 4, 1: 2}), 'route ... as built: FREE, 133 m', the clock names nothing, 7 PositionLightControl, the beat objects 'ZIKLNKOBJ with its StartAnim'. Both archives deleted |

The van's five key-framed bodies still stand at F07's place, 30,083 from their entities (check()'s notes; the next
stage's van_hvk); the nine static bits of `V_Van_Reflection` lie at F07's origin = under the coat check, y -183..-66,
below every floor (MEASURED inline, kl_route's grid): in nobody's way.

### L1.4 GUESS / ASSUMED (each marked in the file)

- GUESS: every spawn row (measured only: on the mesh, on free floor, in no bound or kill box), every camera, stage
  box and trigger of team mode, the loot's places, turns and values, `SEAL_AT` 75 s, `DOORS_AT` 10.4 s, the exit and
  escape-area boxes, `ESC_AT`, `VAN_WAIT`, the bound and kill boxes, every wording in `TEXTS`, the choice of `LINES`.
- ASSUMPTION: a body switched off by a DeactivateGeom at run time stops colliding - here a STATIC placement (the bank's
  vault door is key-framed); the campaign's own storage `HeroColi` is the precedent. If not: `--seal-open`.
- NOT KNOWN: whether 'heroes only' collision (flags 0x108) stops a Fragile Alliance player at all, and whether it stops
  an AI heister or a policeman. kl_route counts it for everybody. If it stops nobody, there is no gate and no harm.
- ASSUMPTION: the music plays from the load (nothing starts it); 'Doors_Opening' un-muffles it (from the names; the
  suppress boxes are not hidden in the file, so the message may change nothing).
- ASSUMPTION carried from the study: a piece sunk 1,500 under its room does nothing to the room's draw list (G1.6).
- GUESS: a level bound / a kill box does something useful to a player who steps off the slab; the kill boxes keep
  the campaign's field values ([1, 1, 0, 0, 'CheckInsideEnter', [], 0, 'FA_DieFromSelf', 'OFF', 'Placholder_Died', 1];
  F07's van has [1, 0, ..., 0]: fields 1 and 10 differ, their meaning was not read).
- ASSUMED from vtables only: which slot is a controller's init (13) and step (25) - consistent over the three kinds,
  not read further.
- Nothing was LOOKED AT: no picture of the briefcases on the counters was rendered.

### L1.5 For the next stage

- **Build with `python tools/kl_fa_club.py test <out> --keep`**; in a script `r, folder = kl_fa_club.build(out)`.
- **Squads** (L2): `campaign_names()` returns the kept squads beside `tuple(KILL)`; `NO_AI` becomes a real flag and
  `KNOWN_NO_AI` conditional as in the bank; the strip of `AttachGeomToBone` / `WarnBehaviourRout` goes into `strip()`.
  `YokoGuards` needs its 'active' flag in data, `Rave#01` stands off the mesh (club 8.2 item 5).
- **The beat's fast way**: the two dance-floor squads' field 8 -> a counter (free: `Gameplay!020_Loot!FollowPlayers!
  TriggerCounter`) -> `R + ROLE['seal off']`; the clock stays. A free-object list stands above `KEEP_MORE` in the file.
- **Police that arrive**: F07's squad groups re-placed on the pavement's mesh strip (x -3765..5786, z -3500..-2650; only
  x -1200..1800 has collision floor) as `kl_fa_bank.place_hall` does. LESSON OF THE BANK'S RUN V2 (re/bank_campaign.md,
  tonight): police standing in the mouth of the only exit killed the crew - the queue lane is 0.96 m of mesh and 12.5 m
  long. The west / east bound boxes begin at the slab's edges: squads come THROUGH them (ASSUMED harmless for AI).
- **The van** (L3): `park_van` -> `kl_map_escape.van_prepare`, wire -> `van_wire`, build inside `van_layer`; `_KEEP`
  holds the van already. The slab is 30 x 8 m: the police rows are at z -2760 / -2830 so that a lane along z -3100 has
  250 either side; the east bound begins 8.2 m after a stop at x 1000 (the bank's rule wants 10 m: move the stop or
  the bound). The boarding place must be on the slab; the road's height is a constant (no floor west of x -1200).
- **Music**: the build is complete without it. The stream file's extension must bring 12 clips (check() prints them from
  the built .WHD): `Music/InHouse/Japan/M05_A/M05_A_Club_Clean.wav`, `_Clean_3D`, `_Muffled`, `_Muffled_3D`,
  `M05_A_Club_2_Clean.wav`, `_2_Clean_3D`, `_2_Muffled` (the two interleaved four-layer sets 'M05_A_Club_Layers' 32.4 MB
  and 'M05_A_Club_2_Layers' 49.5 MB; the second set's fourth layer `_2_Muffled_3D` is named by no object) and
  `SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav`, `.../Inside/M05_Club_Ambience_01.wav`,
  `.../Inside/Yoko_Office_Ambience.wav`, `.../Outside/Roftop/Ambience_Rooftop_M05_A.wav`, `.../Outside/Street/Street_01.wav`.
  Then `kl_fa_bank.use_stream(<file>)` before the build (the bank's `--str`; not yet a flag here).
- **finish()** is where anything goes that needs chunk numbers or the .LOC; check() takes no flag and reads what the
  build did off the level.

### L1.6 Open

- The 'no ZSquadScript' finding stands until the squads are in.
- The gate is invisible. Whether to shut the ENTRANCE DOOR as the campaign does (a visible 'exit blocked') is open: it
  needs `Doors!Entrance!CloseEntranceDoor` (a `MatPosAnimProxy`, frames 0..50) and a Dead Men door clip that plays.
- AI heisters walk the mesh: nothing holds a bot at the seal (the study's station 8, 'wardrobe: hold until the door
  goes', is the bots' stage's).
- Van: stands in sight 18 m west of the slab with F07's drive; vans 2 and 3 are dropped.
- The upstairs bars' loot (the study's four stacks) waits for the stairs to be proven.
- `ZEnvSampler` x 3 stays as on Late Night Opening; `flat` takes a second class with one word in build() if a load says so.
- Team mode / Undercover Cop: spawn sets placed and measured, nothing else thought through.
- Nothing ran in the game; no picture was rendered.

(end of Stage L1; committed as 95ff22a)

## Stage L2 - the enemies, the beat, the music (tools/kl_fa_club.py, second half)

STATE: DONE (2026-10-11 21:05; the stage was cut off once about 20:41 after its first passing build and continued from
the working tree - the second sitting re-ran every build and check below, corrected one claim (L2.1 'STAGED') and one
check (L2.3 'police-slab'), and added `--str`). `tools/kl_fa_club.py` keeps 40 of the campaign's guards in 17 squads,
staged, brings ten of F07's police onto the pavement when the seal opens, opens the seal by 'both dance-floor squads
wiped out' or the clock, and still builds the round without enemies (`--no-ai`). NOTHING RAN IN THE GAME. Kept:
`C:/kl_scratch/club/l2/build/F07+M05_A campaign/` (F01_Main.zip 150,086,073 bytes, sha1 b64b85eb2b8c...; three builds
of the same command gave that archive). l1's build is deleted (rebuild: `test <out> --no-ai`).
Scratch `C:/kl_scratch/club/l2/`: `s/` (sq.py squads of a level, sqnamed.py / amact.py / gates.py the stock censuses,
los.py / hidden.py / seen_strip.py / plan.py lines of sight, f07free.py free host objects), `out/` (every output named
below). No other file of the repo was edited; no per-level table of another tool gained an entry. kl_fa_bank.py has
another job's uncommitted changes in the tree: every `BK.` name this file uses is in the committed version too.

### L2.1 What was built into the module

| part | where | what |
|---|---|---|
| the squads that stay | `SQUADS E1 E2`, `squad_plan()`, `campaign_names()` | 17 squads, 40 men: the nine usable as they stand and eight 'first run' squads on the round's way. kl_fa_author's rule wants a behaviour rout; 16 of the 17 have none, so the rule is widened: only plain squad kinds and what `STRIP` takes off, a ZSoldier for every actor, a start child that holds a rout or a SquadModifierBehaviour |
| what comes off them | `STRIP MESSAGE_KINDS`, `strip_squads()` | MiniCutsceneRout 3, MiniCutSlot 3, MiniCutPosObject 7, AttachGeomToBone 18 (each prop hidden with its group), WarnBehaviourRout 1; 5 message-list entries that would name a node left without a controller are cut in wire() |
| men moved | `MEN MAN_OFF MAN_IN` | 7 by table (below), 3 who stood 19 - 30 beside the mesh put 15 inside it |
| stages | `SQUADS`' second column, `STAGED MOD_ACTIVE SQUAD_ACTIVE SQUADS_AWAKE OFFICE_AT WALK_BOX FLOOR_BOX`, ROLE 'office timer' / 'walk box' / 'floor box' | 'load' 7 squads (15 bouncers, ZSquadScript field 3 = 1); 'office' 2 (4 men) by F07's `RivalMercs!Timer` 10 s after the round-start event = GO + 1.2 .. 1.6 s; 'walk' 2 (5) by the box at the inner office door; 'floor' 5 (13) by the box on the walkway's upper half; 'open' 1 (the 3 hunters) by the beat's gate |
| rows | `STOCK_ROWS`, `BK.soldier_rows` | stock Fragile Alliance rows by weapon class: swat 23, cop 12, sharp 5 (read back: 23 x eCustom 50 / 175, 12 x eCustom 50 / 100, 5 x eCustom 75 / 175) |
| police that arrive | `ARRIVE ARRIVE_SLAB ARRIVE_START ARRIVE_Y POLICE_ARRIVE POLICE_ON_SLAB LANE_CLEAR`, `place_police()`, `police()` | four of F07's squads (`Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left / _Right`, `...ExitStreet_Left / _Right`), ten men, on the pavement's mesh strip beyond the slab's two ends (x -2500..-2100 and 1950..2350, z -2750 / -2850), started by the gate naming their `10_RunToCover`; ten cover points at the slab's ends |
| the beat | `BEAT_SQUADS GATE_WAYS SEAL_AT`, ROLE 'floors counter' / 'gate' | `SecondRun!Dance#01` and `Dance#02`: field 8 ('wiped out') -> `Gameplay!020_Loot!FollowPlayers!TriggerCounter` (2) -> the seal's DeactivateGeom + the gate's `Way#01`; the clock (`SEAL_AT`) -> the same DeactivateGeom + `Way#02`; both ways name the hunters' `HuntBehaviour` and the four `10_RunToCover` |
| checks | `Sight`, `way_views()`, `LANE_VIEWS LATE_CLEAR POLICE_CLEAR ACTORS_LIVE`, check()'s 'enemies' block | L2.3 |
| flags | `--no-ai --squads-awake --no-police --police-slab --office S --dead-men-rows --str FILE` | docstring |

**What differs from the stage's order, each on purpose - for the lead to confirm:**
- THE HUNTERS DO NOT COME INTO THE WORLD IN THE WARDROBE. The campaign has them there, 1.3 - 3 m from the round's own
  station (MEASURED `out/sight_neg.txt`: 'campaign hunter, wardrobe seen from 8 of 103' places of the way) - the bank's
  review finding 6 again. They are re-placed in the second floor's lounge over the stairs ('hunter as placed seen from
  0 of 103'), 21 - 27 m of mesh from the stair landing: they come DOWN to the wardrobe on foot. GUESS: the three places.
- `SEAL_AT` 75 -> 120 s (about 111 s after GO). With 40 guards on 80 m of way a clock of 66 s after GO would nearly
  always come before the two squads are dead, and the beat would be no beat. GUESS; `--seal S`.
- The front office comes at GO + 1.2 .. 1.6 s (`OFFICE_AT` 10.0), not + 2 s: the nearest START point is 7.8 m from
  the inner doorway and nobody is to stand in it when four men come into the world 2 m behind it. `--office S`.
- `YokoGuards`: its 'flag' is the STAGED value written into its `SquadModifier` child (below), and both men are moved
  2 m into the front office's south half - at the campaign's place one is seen through the inner doorway from a START
  point ('Yoko guard, campaign place seen from 1 of 8').
- `Rave#01`'s two men go from behind the rave bar (105 / 154 off the mesh) to its public side.

**STAGED - corrected in the second sitting.** 'office', 'walk' and 'floor' start a squad that has NO behaviour rout by
naming its SquadModifierBehaviour child whose field 4 (`EActivationModifier`) is `eAM_Activate` - the campaign's own
way (six 'Alert' children have the value; it is written into the three that lack it). The first sitting called this
'used by no stock Dog Days level'. MEASURED on all levels (`s/amact.py` -> `out/amact.txt`): no FRAGILE ALLIANCE level
has such a modifier, but the STORY levels have 19 (L02 8, L06 4, L09 2, L11 5), 16 of them on a squad with field 3 = 0,
named by a TriggerBox (6), a GatePath, a TriggerCounter, a CheckPointSave - and one (L11) on a squad without any rout,
from a TriggerBox, exactly this file's 'walk' / 'floor' case. So it is stock behaviour that no build of OURS has run.
Not in stock: the value named from a TriggerDelay2 (the 'office' stage; ASSUMPTION that the sender does not matter -
F07 names modifiers from a TriggerDelay2 18 times, with NotSet or Deactivate). If it fails, 22 men never come: `--squads-awake` (all 17 squads
in the world from the load).

**The gate** (`Gameplay!RunToEscape!RunToEscapeGate`, F07's own). MEASURED `s/gates.py` -> `out/gates.txt`: stock names
a GatePath from a TriggerCounter (F08) and from TriggerDelay2 (F05 F07 F08), and a GatePath names a DefendBehaviourRout
once (F01), else modifiers, timers and geom switches. ASSUMPTION (GateGroup not read in kl2.exe): only the first path
passes; if both do, the five routs are named twice. The SEAL does not hang on the gate.

**Music** (the stage's item 4). Nothing new had to be wired: the two tracks are the kept audio subtree's own layered
stream objects (`Locations/M05_A/M05A_Audio.zip!STREAMS!Inside!Music!Club_01_* / Club_02_*`, `out/music_nodes.txt`),
which nothing starts and nothing stops; L1's host AIDWrapper sends 'Doors_Opening' to `GeomActivator_Door_01 / _02`
at the round start (the doors are open from the load); with `--doors-animate` the door timer sends it. The light show
is OFF by default (L1.1; `--light-show --beat-anim`). check(): 'music: 0 of the 7 clips of the club's two tracks have a
record in the built .WHD'. THE 12 CLIPS THE STREAM FILE LACKS are L1.5's list, unchanged - and MEASURED against the
bank's extended file too: `test <out> --str <work>/build/v_vault/PC_Def.str` (read only) lists the same 12
(`out/var_a.txt` line 77). `--str FILE` is now a flag (kl_fa_bank.use_stream) for the build after the club's extension.

### L2.2 The build

```
python tools/kl_fa_club.py test C:/kl_scratch/club/l2/build --keep     (80 s; 'RESULT: PASS', exit 0: out/test3.txt)
python tools/kl_fa_club.py check "C:/kl_scratch/club/l2/build/F07+M05_A campaign"            ('PASS': out/check2.txt)
```
Lines: 'the police that arrive: 4 of F07's squads re-placed (10 men) on the pavement's mesh strip beyond the slab's two
ends, out of sight'; 'M05_A: 17 squads stay (40 men); taken off them: {MiniCutsceneRout 3, MiniCutSlot 3,
MiniCutPosObject 7, AttachGeomToBone 18, WarnBehaviourRout 1}; 18 props hidden'; '7 men re-placed (MEN)'; '3 men stood
beside the navigation mesh and were put on it: WaitingRoom\Guard#02 20 off, Dancefloor02a#02\Guard#03 30 off,
...\Guard#04 19 off'; 'enemies: 17 campaign squads (40 men): 7 in the world from the load; round start + 10 s -> 2
(front office); the box at the inner office door -> 2; the box on the walkway -> 5; the gate -> 1 hunt + 4 of F07's
police squads; 5 dead entries cut from the squads' message lists; soldier rows: {swat 23, sharp 5, cop 12}';
'.ANM joined: clips +0' with the guesses 'Bouncer plays copy of Thug', 'Army plays copy of Swat_02' (kl_anm STAND_IN);
'verify: problems: 1'; 26,824 entities.

### L2.3 The checks (all on the kept build; outputs in `C:/kl_scratch/club/l2/out/`)

| check | command | result |
|---|---|---|
| verify problems = KNOWN | check()'s 'verify:' lines | **1, known**: 'sound: 5 stream clips are not in the merged stream file' (the 12 clip names). L1's 'no ZSquadScript' is gone |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | **0 CRASH, 0 BROKEN**, exit 0, 'problems: 0'; 2 DEGRADED: no bot squads (a later stage); '5 of 21 squads are named by no object' = squads of the 'load' stage, which are in the world from the load (field 3 = 1) and need no start |
| one cover list | check() | 'cover lists (FFCoverList): 1' |
| route | check() | as built 'NOT free; crossed: [HeroColi]'; 'office -> queue lane, club end: FREE, 122 m'; 'with the 1 standing piece out: FREE, 133 m' |
| every man on the mesh | check() (kl_route.stations near 30, the seal out) | '17 campaign squads (40 men) + 4 of F07's police squads (10 men); 50 of the 50 men on the mesh part of the START and on free floor within 30 - 10 of them police on the mesh strip beside the slab, where there is NO collision floor (ASSUMPTION: an AI walks the mesh)' |
| the places their routs go by | check() | '19 places; 1 not on the START's mesh part': the hunters' `SearchBox` (546, 638, 740), a volume, the campaign's own. The police's ten cover points: all on that part and on free floor (else FAIL), 'the nearest 12.0 m from the lane's mouth; men and cover points 250 and more from the van's line' |
| no dropped node named | check(); result.json | 'dangling' [] ; no list of a squad node names a node that is not there or a node of its squad without a controller |
| behaviour kinds | check() | 'ZSquadScript 21, SquadModifierBehaviour 19, ZSoldier 50, TriggerBox 4, HuntBehaviourRout 1, DefendBehaviourRout 8, RunToCoverBehaviourRout 4, RunToCoverPosInfoRout 10': all in kl_fa_author.PLAIN / BEHAVE (ran live on Retomoto / the bank). The first for a build of ours is not a kind but a VALUE: 'started: {floor 5, office 2, walk 2, load 7, open 1}; 9 of them by a SquadModifierBehaviour with eAM_Activate' |
| squads start where they should | check() | each squad's field 3 against its stage, each start child named by its stage's object, the two boxes 'in use, once, criminals only' (TriggerBox fields 0 / 15 / 14 = 1 / 0 / ECPS_FA_MERCONLY: the bank's review finding 4), the gate's two paths name the same 5 objects |
| the beat | check() | 'Dance#01 + Dance#02 wiped out -> counter of 2 -> [GeomDeactivator_DriveInVan, Way#01]; the clock (120 s) -> the same'; chain 'round start -> [Timer_MissionBriefing, Timer, Timer, Activator_VanSound]' |
| nobody comes into the world in sight | check(): `Sight` (lines through kl_route's collision grid, eyes 160, head 160 / chest 90) from every place the crew can be before a stage | 'office 4 men / 39 places / nearest 430, walk 5 / 55 / 1367, floor 13 / 91 / 693, open 13 / 103 / 324 - nobody in sight of one'. The check does fail: `sight_neg.txt` (the campaign's places: seen) |
| police who come back | check() | '8 bodies, 7 AFTER_DEATH points; the nearest of the squads' men stands 450 from one'. Nothing adds a police body |
| actors against the limits | check() | 'people: 50 ZFFActor in 21 squads + 16 player bodies (ran live: 99 actors, 55 squads)' |
| chunk table, blocks | check() | 'chunk table: 53873 entries (the tools' line: 69632); .prm 44.8, .fxc 17.8, .ANM 21.6, .WAV 21.4 MB; the five load blocks 139 MB (...: 171)'; '23683 of its indices are dead (the wardrobe takes 20989)' - the study's 53,898 was with the wardrobe appended; here it goes into dead indices |
| written level | `kl_fa_club.py reverify` | 'problems: 0' (26,824 entities, 3,498 .HVK placements, 24 list entries parked) |
| kl_impact | `python tools/kl_impact.py <archive>` -> `impact.txt` | 'problems: 0 in 1 levels' |
| kl_arms | `python tools/kl_arms.py check <archive>` -> `arms.txt` | '0 findings' |
| preflight | `python tools/kl_maps.py preflight <folder>` -> `preflight.txt` | exit 1: **'CRASH 1, RISK 3, NOTE 65'**: CRASH = 'kl_graft.verify reported 1 problems' (the known one); RISK = `ZEnvSampler` x 3 (two lines) and `SoundSpline` x 1, as L1; 'fa:squads' is gone |
| NO_AI still builds | `test <out> --no-ai` -> `var_noai.txt` | 'RESULT: PASS': 26,593 entities, 'verify: problems: 2' both known (the clips; 'no ZSquadScript' = KNOWN_NO_AI), 'enemies: none (a build without squads); the seal opens by its clock'; the timer, both boxes and the counter name nothing (else FAIL) |
| the fall-backs | `test <out> --str <v_vault>/PC_Def.str --squads-awake --police-slab --dead-men-rows --office 12` -> `var_a.txt` | 'RESULT: PASS': all 17 squads in the world from the load, Dead Men's rows read back (18 x eRegular 50 / 50, 17 x eAmateur 50 / 50, ...), 'POLICE ON THE SLAB: 2 of the police come into the world IN SIGHT of a place in the queue lane (the cost of that fall-back)'. (The first sitting's check FAILED this variant on exactly those two men although the flag's text says 'in sight': check() now reads a police man ON the slab as that variant and says so; anybody else in sight still fails.) |
| the other flags | `test <out> --no-police --seal-open --doors-animate --light-show --beat-anim --fan-damage` -> `var_b.txt` | 'RESULT: PASS': 26,761 entities, the gate lets in 1 object (the hunt), four leaves stand ('with the 4 standing piece(s) out: FREE, 133 m'), the clock names no seal |

Variant archives are deleted; only the default build is kept.

### L2.4 GUESS / ASSUMED (each marked in the file)

- ASSUMPTION, the largest: a squad WITHOUT a behaviour rout that is in the world fights whoever it sees (16 of the 17;
  the campaign's own form; every Fragile Alliance squad of stock Dog Days has a rout; L11 has one such squad).
- ASSUMPTION: `eAM_Activate` brings a waiting squad into the world (STAGED above), also when a TriggerDelay2 sends it.
- ASSUMPTION: ZSquadScript field 8 is sent when the last man is dead (Retomoto's room counter hangs on it; not seen
  live for a squad that was started by a modifier). If never: the clock.
- ASSUMPTION: an AI character walks the navigation mesh where there is no collision floor (the ten police start on
  the strip beside the slab). If a man falls he falls into a kill box and the wave is thinner: `--police-slab`.
- ASSUMPTION: only the first of the gate's two paths passes (stock use; GateGroup not read).
- ASSUMPTION: the round-start event comes 8.4 - 8.8 s before GO here as on Retomoto (OFFICE_AT, SEAL_AT count from it).
- NOT KNOWN (L1): whether the heroes-only seal stops an AI at all - the three hunters and the police are let in by the
  gate, not by the seal, so they may walk through it either way; the bouncer in the lane stands inside it from the load.
- GUESS: the split into stages, both stage boxes, every place in `MEN` and `ARRIVE`, `LATE_CLEAR` 300, `Sight`'s three
  heights and its tolerance (a drawn wall without collision hides nobody for it; a window's collision does).
- GUESS carried by kl_anm: the bouncers play a copy of the 'Thug' set, 'Army' a copy of 'Swat_02'.
- ASSUMED harmless: the 18 props (flashlights, the wand) hidden with their groups; AI through the bound boxes at the
  slab's ends.

### L2.5 For the next stage

- **L3 (van)**: as L1.5. NEW: the police's cover points keep 250 from the line z -3100 (`LANE_CLEAR`; check() fails
  otherwise), and their men start at x -2500..-2100 / 1950..2350 on the strip - a drive along the strip passes
  THROUGH the west group's start places (z -2750 / -2850 against the lane's z -3100: 250 - 350 off the line) before the
  seal opens; they are not in the world then. `VAN_WAIT` (-3000, 32, -3100) is 500 west of them.
- **Bots (F)**: nothing holds an AI heister at the seal; a hold in the wardrobe until the seal's clock (the bank's
  `GATE_NAME` pattern) reads `SEAL_AT` off the built level. The 'walk' and 'floor' boxes are criminals-only and fire
  ONCE: the first bot through the inner office door starts the walkway's squads.
- **Stream stage**: the 12 clips of L1.5; then `test <out> --str <file>`; KNOWN's first entry goes away by itself
  (check() lists what the built .WHD lacks).
- **Live order** (owner away): `--no-ai` first (the seal, loot, exit box, bounds), then the default, then
  `--squads-awake` if the log shows no guard beyond the 15 bouncers, `--police-slab` if no police reach the slab.
  What to look for: do the bouncers fight; do four men appear in the front office just after GO; does the seal open
  when the six `Dance#01 / #02` men are dead; police from both sides of the pavement.

### L2.6 Open

- Nothing ran in the game; no picture was rendered.
- The gate is still invisible (L1.6); the entrance door is not shut.
- No dancing crowd, no civilians, no Yoko (the lead's order).
- The upstairs squads (`Lounge#01 / #02`, `Rave#01 / #02`, 10 men) are off the round's way: they are there for a crew
  that wanders, and nothing leads it up (no loot upstairs yet, L1.6).
- `kl_fa`'s DEGRADED line about 5 unnamed squads is its heuristic not reading field 3; kl_fa.py is not this stage's.
- The 'office' squads come 4.3 m and more from the nearest START point, behind a wall: a sprinting human reaches the
  inner doorway about when they appear. Measured as 'out of sight of every START point', not of a moving player.
- The bank's regression was not re-run: no shared file was edited.

(end of Stage L2)

## Stage L3 - the escape (tools/kl_fa_club.py: F07's van on a way-point plan along the pavement)

STATE: DONE (2026-10-11 21:50). `tools/kl_fa_club.py` lays F07's first key-framed van on a straight road along the
pavement, FROM THE WEST, and check() has a block 'the escape'; every check of the stage passes and all of L1's / L2's
still do ('RESULT: PASS', the same one known verify finding). NOTHING RAN IN THE GAME. Kept = 'THE BARE MAP' the
finishing stage starts from: `C:/kl_scratch/club/l3/build/F07+M05_A campaign/` (188 MB: F01_Main.zip 150,075,064 bytes,
sha1 2eb2edb526ff..., finished = lightened + briefcases + texts; result.json, log.txt, graft.txt, NEW van.json). A
second build with `--plan <its van.json>` gave the same archive and the same van.json. `C:/kl_scratch/club/l2/build`
is deleted. Scratch `C:/kl_scratch/club/l3/`: `s/` (drawn.py what the map DRAWS along the pavement, plan0.py the plan by
the unchanged tool, plan1.py the plan, rooms.py room boxes and the vision grid, dl.py drawn_lane with its negative
controls), `out/` (every output named below). No other file of the repo was edited: kl_map_escape.py is only called.
ONE THING IS NOT AS THE STAGE'S ORDER READS, and is said first (L3.1): 'van-check 0 faults' holds on the DRAWN
pavement, through a wrapper of this module; the plain `kl_map_escape.py van-check` has 217, every one the missing
collision floor outside the slab.

### L3.1 The hard part: a drive where nothing has collision - what was measured, and how the tool is used

- **The unchanged tool refuses every road that leaves the slab** (`python C:/kl_scratch/club/l3/s/plan0.py <bare graft>`
  -> `out/plan0.txt`): the planner holds each ray of the lane against 'the road under it', so the study's line gives
  'FAULT only -340 of clear lane before the stop (least 2000)', 'only 610 of clear lane after the stop (least 3000)';
  a drive that stays on the slab cannot be had either (the slab is 30 m, the least drive is 20 + 30 m: 'only -39 ...',
  'only 1099 ...'). van_check does the same per key ('drive key N: no ground under it').
- **What is DRAWN there was never looked at (the study's open point). It is now** (`python C:/kl_scratch/club/l3/s/drawn.py
  <bare graft>` -> `out/drawn.txt`: every mesh of every map entity that has a model, by kl_fa_loot.Assets, in world
  space, rastered from above into 20-unit cells over x -7200..7600, z -3700..-2500; 1,707 model roots read):
  - the pavement is drawn at **y 30.0 under every cell** of the eleven rows tested between z -3460 and -2620, from
    x -7200 to 7600: seven pieces `M05_A_Outside_Street_01a\SO0100_M05_Street_Wide_A_03, B_04, B_03, B_02, B_01, B_05,
    A_01` (sidewalk tiles `Stone_SidewalkTiles_07a_M05` + a dirt overlay; the asphalt of the road is y 10 beyond the
    kerb). So the collision slab (y 30) is one piece of a pavement 148 m long and 8.8 m deep that is drawn at the
    same height everywhere;
  - **nothing is drawn 25..220 over it between z -3280 and -2880** (the map at the end of `drawn.txt`): street lamps
    `PC0100_JPN_Metal_OldStreetLamp_B_Group_06 / 04 / 01 / 08` at x -3200, -1200, 800, 2800 and two bins
    `PC0100_JPN_Trashcan_B_02 / _01` at x -3000 and -520 stand at z -3300..-3400; the house fronts at z -2620
    (`SO0002_M05_Facade_K_Base_01`, `..._Facade_A_Base_01` glass x -1420..-400, `FrontBuilding`, a switch box at
    x 1680); four parked cars beyond the kerb (z -3520..-3750);
  - west of x -400 the fronts are modelled buildings; **east of x 2100 the street's north side is a glow plane**
    (`M05_A_Outside_Roof_01a\UNIQUE_StreetGLOW`, material `Effects_StreetGLOW_DistFADE`, z above -2860) - the faked
    far end of the street. Hence the side: the van COMES along the real fronts and LEAVES into the faked distance.
- **How the tool is used: the road's height is DECLARED** (`PAVEMENT`, class `Pavement`, `pavement()`).
  `Pavement` is kl_map_escape.Ground with one more floor: inside `PAVEMENT` = x -7200..7600, z -3460..-2580 a vertical
  line that meets no collision floor within the tool's own tolerance (25) of y 30 meets one at y 30, owned by the REF
  id -5 that no entity has. `pavement()` puts it in kl_map_escape.Ground's place for the length of the plan and of
  van_check (the idiom of kl_map_escape.van_layer, which swaps kl_hvk.join). Everything else is the tool's own:
  collision in the van's body, convex bodies, the four lengths, the bounds, the boxes at the stop, the camera's sight,
  the collision file. kl_map_escape.py IS NOT CHANGED (it is a finished file, and this is no bug of it: the study
  foresaw 'a road-height constant: small tool change' - it is done from outside instead).
  WHY THIS IS HONEST AND WHERE IT IS NOT: a key-framed van needs no floor (Retomoto's first drove 40 UNDER its road:
  re/retomoto_fa.md 9.3); what the height must be is what is DRAWN, and that is measured - by drawn.py once, and by
  check() on every build along the actual drive (`drawn_lane`, L3.3). NOT covered: what a key-framed van does to
  people in its lane where there is no floor, bodies and dropped money at the slab's rim, a model switched off or on
  at run time. The plain tool's verdict is printed beside the wrapper's on every check.

### L3.2 What was changed (one file, tools/kl_fa_club.py, 1,866 -> 2,332 lines)

| part | where | what |
|---|---|---|
| the road | `ROAD` (replaces `VAN_WAIT`) | `arrive` (-5300, 30, -3100), (-2800, 30, -3100); `stop` (-300, 30, -3100) at = origin; `leave` (3000, 30, -3100), (7300, 30, -3100); heading and camera not forced |
| the drawn road | `PAVEMENT`, `Pavement`, `pavement()` | L3.1 |
| the plan | `van_plan(src)`, `plan_of(file)`, `lay_van(P)`, `van_path()`, `PLAN NO_PLAN` | kl_fa_bank's four, with this file's ROAD; van_plan runs inside pavement() |
| the build | `build(out, log, plan=None)` | bare graft into `<out>/_bare` (35 s, 284 MB, deleted again; `kl_maps.one(..., m_drop=M_DROP)`) -> plan -> `with kl_map_escape.van_layer(plan), doors(): kl_maps.one(...)`; -> (result, folder, plan, what was done to the van) - FOUR values now, as kl_fa_bank.build |
| the layer | `prepare_host()` | `park_van()` is gone: `kl_map_escape.van_prepare(S, PLAN, log)`; the escape marker held against the plan's drive (`LANE_CLEAR`) |
| | `wire()` | `kl_map_escape.van_wire(sc, PLAN, log)` |
| places moved for the van | `ESC_AT`, `POLICE`, `BODIES`, `ARRIVE` | below |
| test | `test(out, keep, log, plan)`, `--plan FILE`; NEW command `van-check <folder>` | van.json beside the archive (kl_map_escape.van_build's form: tag, plan, van, wired, hvk, check) |
| check | check(): 'the escape'; NEW `drawn_lane()`, `van_check()`; `BOARD_NEAR BOUND_AFTER MOUTH_SIDE BOARD_CLEAR FED_CLEAR STREET_ROOM` | L3.3 |

**The plan** (MEASURED: `out/plan1.txt`, the build's lines in `out/test1.txt`, `van.json`): 0 faults, lane empty on the
first pass, no cut.
```
waits (-5300, 32, -3100) heading 90 -> 50.0 m in 7.2 s -> stops (-300, 32, -3100) heading 90 (rear box (-637, 30, -3100))
      -> 70.0 m in 8.48 s -> ends (6700, 32, -3100) heading 90;  600 path points, y 30.0 all the way
camera eye (-2100, 360, -3100) (cam_spot: 18 m BEHIND the standing van, 330 over the pavement; '15 of the 144 places
      tried see the stop and the drive 850 and 2500 after it; this one sees the end')
```
'kl_map_escape: ... 563 position and 550 rotation keys rewritten in place (391 of them the drive, stop at key 159);
drive in 5063 -> 5000 (x 0.99), away 7019 -> 6999 (x 1.00); crash pieces -120..120 to the side; 19 objects moved' -
**F07's own drive, unscaled, laid straight**. 'exit trigger Gameplay!EscapeSetup!otrExitLevel calls ...
EscapeVehicle_Animation_F07'; '.HVK: 9 static placements of the van's subtree cut, 5 key-framed placements of the van
put at its waiting place' (.HVK 1,910,256 bytes). F07's second and third van are NOT in the level (L1's decision,
kept): one `OnlineEscAnimatedVehicle`, one `FakeTarget`; check() fails any other count.

**Why from the west, why the stop at x -300** (GUESS as a design; each number below is MEASURED by check()):
- The van's nose (250 ahead of its origin) stops at x -50: **168 short of the line straight out of the lane's mouth
  (x 118)** - the arriving van sweeps the slab from x -1193 to -50 (11.4 m) and never passes before the door the crew
  comes out of. The study's road (stop x 1000) swept 22 m of slab in front of it; `MOUTH_SIDE` 150 is check()'s rule.
- The rear doors (the boarding box rides 337 behind the origin) are at (-637, 30, -3100): on the slab, 5.6 m inside
  its west edge, 3.5 m from the kerb's rim, 2.4 m from the nearest warn box (the kerb's), 8.9 m from the lane's
  mouth; 'queue lane, street end -> boarding place in the collision (the seal out): FREE, 7 m'.
- 50 m in and 70 m away are F07's own lengths. It waits at x -5300: where the pavement is drawn, 15 m west of the
  mesh strip's end (x -3765: it stands OFF the navigation mesh - the bank's van stood on it, L3.4 there) and 14 m
  inside the street room's west edge.
- It leaves east: over the rest of the slab with its passengers (the away leg must cross the slab either way) and
  through the east level bound 21.3 .. 26.8 m after the stop - the stock form (kl_fa_bank L3.3: stock vans pass one
  10.9 .. 105 m after their stops); the west bound 15.1 .. 9.3 m before the stop, empty.

**Places that moved for the van** (all in this file; each was a GUESS of L1 / L2 made before the stop was known):
- `ESC_AT` (300, 30, -2800) -> **(-640, 30, -2800)**: the escape marker (and jump point 06_Exit, and the route's last
  station) beside the lane, level with the rear doors - 300 from the drive, 295 from the boarding place, 7.8 m from
  the lane's mouth. NOT over the stop and not in the sweep (the bank's review finding).
- `POLICE` / `BODIES`: the four points and bodies that stood at x -900..-600 (ON the new marker, 3.4 m from the rear
  doors) are now east with the other three: x 900..1500, z -2760, the eighth body (1600, -2830). The nearest point of
  police who come back is 15.2 m from the boarding place (`FED_CLEAR` 10 m), 8 m from the lane's mouth; the nearest
  squad man 359 from one (was 450; `POLICE_CLEAR` 100).
- `ARRIVE`: two cover points of the WEST police squads, (-950, -3400) and (-800, -3400), stood 4.3 and 3.4 m from the
  rear doors of the standing van; now (-1160, -3410) and (-1000, -2680). The nearest cover point is 5.4 m from the
  boarding place (`BOARD_CLEAR` 5 m), 11.2 m from the lane's mouth (rule 10 m), 250 from the drive.

### L3.3 The checks (all on the kept build; outputs in `C:/kl_scratch/club/l3/out/`)

| check | command | result |
|---|---|---|
| build + finish + check | `python tools/kl_fa_club.py test C:/kl_scratch/club/l3/build --keep` -> `test1.txt` (112 s: bare graft, plan, build, finish, check; 84 s with `--plan`) | **'RESULT: PASS'**, exit 0; 26,824 entities, 20 rooms, 'verify: problems: 1' (the known stream clips) |
| the same archive again | `... test C:/kl_scratch/club/l3/again --keep --plan "<kept>/van.json"` -> `again.txt` | 'RESULT: PASS'; sha1 2eb2edb526ff... = the kept one; van.json byte-equal; deleted |
| check alone | `python tools/kl_fa_club.py check "<kept>"` -> `check.txt` | 'PASS', exit 0 |
| **van-check** | `python tools/kl_fa_club.py van-check "<kept>"` -> `van_check.txt`; inside check() with the plan | **'0 fault(s)' on the drawn pavement** (van_check and the escape cameras' table): 'keys 0.0 off the road height at most, largest step 58, nose up to 0.9 degrees off the tangent, crash pieces up to 120 to the side; lane (5 rays, every 20, 350 before and 600 beyond): clear'; 'boarding box at the stop: (-636, 32, -3094); key-framed placements 5, at most 1.1 from their entities'; wait / stop / end within 25 of the plan's. One note: 'no define FAEscCameraLAST' = the stock form |
| ... the plain tool | `python tools/kl_map_escape.py van-check "<kept>"` -> `van_check_plain.txt` | exit 1, **217 faults: 211 x 'drive key N: no ground under it', 5 x 'in the van's lane: no road within 25 of the drive's height' (one per ray), 1 x 'camera ...: the eye is outside the map: no collision above or below it'** - nothing else. check() counts them on every run and FAILS on any fault of another kind |
| what the van drives over | check() | 'of the 391 keys of the drive 180 have a collision floor under them (x -1193..1796: ColiObj_01), 211 the drawn pavement alone (PAVEMENT y 30); the stop: origin y 32.0, the floor under it y 30.0' (the stop must stand on real floor, else FAIL) |
| **the lane, drawn** | check(): `drawn_lane`; `python C:/kl_scratch/club/l3/s/dl.py <bare graft>` -> `dl_bare.txt` | 'DRAWN in its lane (the map's models, 128 triangles near it; 5 rays every 20, 350 before and 600 beyond): a surface within 25 of the road under 3240 of 3240 samples, y 30.0..30.0 (SO0100_M05_Street_Wide_B_04 x 500, B_03 x 500, B_02 x 500, B_01 x 500, B_05 x 500, A_01 x 375, A_03 x 365); in the van's body (25..220 over the road): nothing'. The test does fail: the same on the line z -3300 finds the four lamps and two bins, on z -2620 six pieces of the fronts and 214 samples without a surface, on z -3560 the four parked cars |
| the lane, collision | the plan's own test on the bare graft (`test1.txt`, 'van plan for ...') and van_check's on the finished build | both clear |
| **fake-test** | `python tools/kl_fa_bots_dyn.py fake-test <work>/build/z_route/M01 <work>/build/rt_full6/retomoto_full "<kept>"` -> `fake_test.txt` | **'RESULT (fake-test): PASS (grid control 1, parked control 1, lattice 3)'**; the club: 'FakeTarget Animation/F07/F07_Escape_Vehicle_01.zip at (-5316.6, 32.0, -3099.9): inside; kl2's arithmetic: cell (1, 0, 4) (a record)', the only FakeTarget of the level (vision space x -6725..10906, y -31..3000, z -7074..6724). check(): the same, and 'on the drive: at the stop inside; at the end of the drive inside' |
| the street's room | check(); `python C:/kl_scratch/club/l3/s/rooms.py <folder> wait=... stop=... end=... cam=...` -> `rooms.txt` | 'the room box of M05_A_Outside_Street_01a (1 record(s): x -6725..9274, y 20..3000, z -7074..-2489) holds: waits yes, stops yes, ends yes, the camera's eye yes' |
| **the boarding place** | check() (`kl_route.stations` near 30, `kl_route.route`); `python tools/kl_route.py stations "<kept>" START=2817,342,2420 "lane street end=105,20,-2600" "escape marker=-640,30,-2800" "boarding place=-637,30,-3100" "van stop=-300,32,-3100" "van waits=-5300,32,-3100" --near 30 --open "M05_A_Inside_Entrance_01a\HeroColi"` -> `route_stations.txt` | 'boarding place at the stop (-637, 32, -3095): on the slab True, mesh True, part 0 (the START's: 0), free floor within 30: True; the van's stop: mesh True, part 0'. stations: '5 of 6 places reached ... 5 of 6 on the mesh, on 1 part(s)'; the WAITING place is 'OFF the mesh by 1535 ... NOT reached' (exit 1 for that): as it should be |
| ... reached | `python tools/kl_route.py walk "<kept>" --from "lane street end=105,20,-2600" --to "boarding place=-637,30,-3100" --open ...HeroColi` -> `route_board.txt`; the whole round with 13 places -> `route_open.txt`; as built -> `route_built.txt` | 'FREE, 8 m of cells, floor y 30..30 ... the mesh way: 35 samples, all free'; the whole round 'RESULT: FREE'; as built 'NOT FREE', the leg through the seal alone |
| ... **the way an AI is given** | check() (`way_views` on kl_route's mesh model) | 'lane's street end -> boarding place: on the slab all the way; by way of the escape marker: 94 samples off the slab (as far as x -2326)' - L3.4 |
| the slab's rim against the bounds | check() | L1's three edge tests still pass (a walker 1 m before each open edge in no bound, 1.2 m beyond it in one); '3 LevelBound in their place ..., 3 kill boxes; 0 of the 93 spawn points, player groups and stations inside one'; neither the stop nor the boarding place in a bound, warn or kill box; the two bounds on the drive as above |
| path blocker | check() | 'PathBlockerVan at (-294, 147, -3096) half (101, 130, 250): the boarding place is outside it' |
| exit box | check() | 'exit box x -1150..1750, z -3450..-2650: on the slab True; holds the pavement station True, the lane's street end False'; 'holds the van's stop True, the boarding place True; drive in 7.2 s' (the stock form) |
| nobody in the lane | check() | 'the escape marker stands 300 from the drive, 295 from the boarding place'; 'of 52 spawn points, player bodies, men, cover points, the marker and stations on the pavement the nearest to the drive is FinancialAlleyExitStreet_Right\10_RunToCover\RunToPosInfo#02, 250 from it' (`LANE_CLEAR` 250) |
| the police and the rear doors | check() | 'the nearest cover point of the arriving squads 5.4 m (5 m wanted), the nearest point or body of police who come back 15.2 m (10 m wanted)' |
| **the camera** | check(); `kl_fa_club.py van-check` (kl_map_escape.check's table) | 'EscCamera01_01 ... mode eFMM_LookFromPos ... Dog Days' eye: (-2100, 360, -3100), 330 over [the pavement]; looks at the player' - F07's own camera, the mode that puts the eye at its place; 'the escape camera's eye: 330 over the road, 18 m from the stop, over the drawn pavement (no collision under it); between it and the van at the stop: nothing'. The in-van camera eFMM_LookAtPos as stock |
| is the waiting van in sight | check() | 'waits at (-5300, 32, -3100), 50 m from its stop, off the navigation mesh; from the queue lane before the seal: hidden by SI0101_WallB_Front_01; from the lane's mouth: hidden by SO0002_M05_Facade_A_Base_01...; from the escape marker: SEEN (46 m); from the boarding place: SEEN (46 m)' - L3.5 |
| L1's / L2's checks | check() on the kept build | all as L2.3: verify 1 known; 79 spawn places on the mesh; loot 11 / 2,200,000 takable; route as built crossed = the seal alone, 'office -> queue lane: FREE, 122 m', 'with the 1 standing piece out: FREE, 138 m' (the last station moved: was 133); 50 of 50 men on the mesh; staging; the beat's chain; nobody in sight; 50 actors in 21 squads; chunk table 53,873 entries, 23,683 dead; five load blocks 139 MB; written level 'problems: 0'; no collision placement off its entity (the van's five included now) |
| kl_fa.check | `python tools/kl_fa.py check <archive>` -> `fa.txt` | exit 0: 0 CRASH, 0 BROKEN, 2 DEGRADED (no bot squads; the heuristic's '5 of 21 squads named by no object') |
| kl_impact / kl_arms | `kl_impact.py <archive>`, `kl_arms.py check <archive>` -> `impact.txt`, `arms.txt` | 'problems: 0 in 1 levels'; '0 findings' |
| preflight | `python tools/kl_maps.py preflight "<kept>"` -> `preflight.txt` | exit 1: 'preflight: CRASH 1, RISK 3, NOTE 65' (CRASH = the known verify problem; RISK = ZEnvSampler x 3 twice, SoundSpline x 1): as L2 |
| the flags | `test <out> --no-ai --plan <van.json>` -> `var_noai.txt`; `... --squads-awake --police-slab --dead-men-rows --office 12 --plan ...` -> `var_a.txt`; `... --no-police --seal-open --doors-animate --light-show --beat-anim --fan-damage --plan ...` -> `var_b.txt` | 'RESULT: PASS' three times, exit 0: no-ai 26,593 entities; (a) the ten police on the slab, 'POLICE ON THE SLAB: 2 of the police come into the world IN SIGHT' (that fall-back's cost, as L2); (b) four leaves standing, no seal, the three never-run kinds in. Archives deleted |

### L3.4 What the stage found beside laying the van

- **THE PAVEMENT'S NAVIGATION MESH LEADS OFF THE SLAB.** Its polygons run from x -3765 to 5786 and the slab is
  x -1200..1800. kl_route's model of the way an AI is given (through the middles of the polygons' shared edges) from
  the lane's street end STRAIGHT to the boarding place stays on the slab (35 samples, all with floor); from the
  escape marker (-640, -2800) to the boarding place (-637, -3100), 3 m apart, it goes **17 m west of the slab and
  back** (to x -2346; 50 of 86 samples without a floor: `route_open.txt`). The model's 'middle of the shared edge'
  is cruder than what the game's path-finder does (not read), but the polygons ARE that long, and L2's police already
  rest on 'an AI walks the mesh where there is no collision floor'. FOR THE BOTS' STAGE: the last stations are the
  lane's street end and then the boarding place, nothing between; check() fails a build in which that leg leaves the slab.
- **The whole drive lies in one room box and inside the vision grid** (`rooms.txt`): the wait place, the stop, the end
  and the camera's eye are inside `M05_A_Outside_Street_01a`'s box (x -6725..9274, y 20..3000). The road's y 30 is
  10 over that box's floor; a van at F07's own height (y -198) or 'under the map' would not be.
- **The escape marker and four police points stood where the van's rear doors now are** (L3.2).

### L3.5 GUESS / ASSUMED (each marked in the file), and what is not met

- **NOT MET, as on the bank: 'out of sight'.** The waiting van is hidden from the queue lane and from the lane's mouth
  (the house fronts), and SEEN from the pavement, 46 m up a straight street; the first criminal on the slab calls it,
  so it is seen driving in, not standing. Nothing hides a van on this street; nothing was tried.
- GUESS: the side it comes from, the stop, both lengths, `MOUTH_SIDE` 150, `BOARD_CLEAR` 500, `FED_CLEAR` 1000, the new
  places of the marker, the seven police points, the two cover points; the camera's eye (cam_spot's).
- ASSUMPTION, the stage's largest: **a key-framed van is drawn and drives where there is no collision floor** - and the
  van's own five key-framed bodies collide there with players' bullets and bodies as anywhere. Retomoto's van drove
  under its road; no van of ours has stood off every floor.
- ASSUMPTION: being inside a room's box matters for being drawn (STREET_ROOM); the van's and the camera's are.
- ASSUMPTION: the camera's eye over the drawn pavement, with no collision under it, is as good as one over a floor
  (kl_map_escape calls it 'outside the map'; its rule is there to keep an eye out of the void under a level). If the
  picture is wrong: `cam=(1500, 360, -3100)` in ROAD is an eye over the slab, ahead of the van (cam_spot's choice
  when only real floor counts: `out/plan0.txt`).
- NOT KNOWN: what the van's kill box does to a policeman who crosses its line - the west squads run to their cover
  from z -2750 / -2850 and three of their five points lie north of the line, two south (they cross it). Their men
  come into the world when the seal opens; the van comes 7.2 s after a criminal is on the slab.
- NOT KNOWN: what the passengers see of the east end - the drive ends at x 6700 beside the glow plane (z above
  -2860, 1.3 m from the van's flank).
- kl_map_escape's own (unchanged): a key-framed body moves with its entity; the engine interpolates rotation keys.
- A build made by `kl_maps.py one ... --author kl_fa_club` alone still stops in prepare_host (NO_BUILD, then NO_PLAN):
  READ, not run.

### L3.6 For the next stage

- **Build**: `python tools/kl_fa_club.py test <out> --keep [flags] [--plan "<kept>/van.json"]`; from Python
  `r, folder, plan, did = kl_fa_club.build(out)` (FOUR values now), then `finish(folder)`, `check(folder)`.
  `--plan` saves the bare graft (35 s) while ROAD is unchanged (plan_of refuses the plan of another road).
- **Whoever copies the build folder copies van.json with it**: check() holds the drive against its plan.
- **Any tool that calls kl_map_escape.van_check / check / van_plan_points on this map** (the finishing chain's bots,
  tune and talk tools read van.json and may call them) must do it inside `kl_fa_club.pavement()`, or it gets the 217
  floor faults. `kl_fa_club.van_check(folder, log, plan)` -> (report, Level, the plain tool's faults) is the ready call.
- **Bots**: the boarding place at the stop is (-636, 32, -3094) (`van.json` 'check' 'board'; the plan's (-637, 30,
  -3100)); in the FILE the box rides on the van at the waiting place (re/map_escape.md 12 / 15). Stations: ... queue
  lane, street end (105, 20, -2600) -> boarding place, NOT by the marker (L3.4). `ROUTE_OUT`'s last station is the
  marker's place (for the route test), not a bot's.
- **Anything a later stage puts on the pavement**: run check() again - `LANE_CLEAR` sees spawn points, player bodies,
  squads' men, the police's cover points, the marker and the stations of the way out; van_check's lane sees collision
  under 'Locations/' and convex bodies; `drawn_lane` sees the map's models (below 'Locations/'), not a layer's object.
- Still not wired (as the bank's L3.5): the vehicle monitor's list 4 is empty; nothing retreats when the van is called.
- **Live order** (owner away; after L2.5's): does the van show 50 m up the pavement when the slab is entered, and is
  it DRAWN all the way in (no floor under it until x -1200); 'Get in' at the rear doors at (-637, -3100); the in-van
  view, then the fixed camera from behind; the east bound 21 m into the drive away; the score page. If the van is not
  seen west of the slab, the cure is a shorter way in that starts on the slab's edge - which the tool's 20 m least
  drive does not allow from x -300 (the slab's edge is 9 m west): that would be a tool change.

### L3.7 Open

- Nothing ran in the game; no picture was rendered (drawn.py's map is a raster of the models, not a view).
- 'Out of sight' (L3.5).
- The gate is still invisible (L1.6); no dancing crowd; the upstairs squads lead nowhere (L2.6).
- What is drawn was tested for the map's static models with the 40-byte vertex; a model with another vertex form
  would be read wrong or not at all (219 entities of the band had no model root: lights, sprites, sound objects).
- The bank's regression was not re-run: no shared file was edited (kl_map_escape.py, kl_route.py, kl_fa_bank.py are
  only called; kl_fa_bank.py has another job's uncommitted changes in the tree, and every `BK.` name used here is in
  the committed version too).
- check()'s FakeTarget and room-box tests lean on kl_fa_bots / kl_fa_bots_dyn / kl_octree (another session's files; it
  prints 'NOT CHECKED' if their names change - then run the fake-test command of L3.3).

(end of Stage L3)
