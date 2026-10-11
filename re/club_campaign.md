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
