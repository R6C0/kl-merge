# The bank the campaign way (M03_A under F07): the build, stage by stage

The study: re/campaign_fa.md (summary), re/campaign_fa_bank.md (the place; its section 8 and the notes
'corrected after the critic' weigh more than the first text), re/campaign_fa_tooling.md (the tools). This file is
the working note of the workflow that BUILDS the map: one section per stage, appended by the stage itself and kept
current while it runs (a usage limit can cut a stage off: what is here and on disk is what survives).
Evidence labels as in the study: MEASURED = an output produced here (command named), READ = code or a note,
ASSUMPTION = says why, GUESS = a value nobody measured. Everything is OFFLINE: nothing is installed, the game is
not started. Scratch: C:/kl_scratch/bank/<stage>/; delivered builds: <work>/build/c_bank/.

## Stage T1 - the cover list survives the campaign pre-pass; the authored layer is a MODULE (tools/kl_maps.py, tools/kl_graft.py)

STATE: DONE (2026-10-11 12:50). Checks (a), (b), (c) pass; every archive is deleted. Kept in C:/kl_scratch/bank/t1/
(1 MB): the logs, the four manifests, result.json / log.txt / graft.txt of every build, the scripts in s/.
Committed as 2b092c0 (tools/kl_maps.py, tools/kl_graft.py, this section).

### T1.0 Regression baseline, made BEFORE any change (tree at 40a8a7a + the two other sessions' uncommitted files)

- Command: `python tools/kl_fa_loot.py test "C:/kl_scratch/bank/t1/before" --no-wardrobe` (READ tools/kl_fa_loot.py
  `test`: kl_fa_blast.test = kl_maps.chain(F07, M09_B, M09_A, campaign, author=True) with the street, blast and loot
  hooks and the voices on, then `lighten trim,slim`; the wardrobe is a separate later step and is left out).
  7 minutes. MEASURED last lines of before.log: 'level: 25735 entities, 22 rooms, 313 MB', 'kl_graft.verify: 1
  problems, 0 of them not known', 'RESULT: PASS (C:/kl_scratch/bank/t1/before/light)', exit 0.
- Recorded: `python C:/kl_scratch/bank/t1/s/manifest.py make before before.manifest.json` -> 68 files, 3 archives
  (first step chain/F07+M09_B/R09_Main.zip, the dressed level 'R09+M09_A (R09 = F07+M09_B)'/F01_Main.zip, the
  lightened light/F01_Main.zip), 91 members with name, size and CRC, and size + sha1 of every file beside them.
  The hashes of tools/*.py, re/*.json and klhook/KLJoin.retomoto.ini at that moment: tools_before.sha1.

### T1.1 What was changed (two files, nothing else)

**tools/kl_maps.py**
- `PASSIVE` gains `'FFCoverList'` (with the comment that says why and for which levels).
- `HERO_AT` gains `'M03_A': {'Special!JumpPoints!Jump#060': 'Heroes!Hero_01'}` (T1.3).
- `one()`: the campaign pre-pass asks `kl_graft.author_module(opt.get('author')).campaign_names(m_name)` instead of
  importing kl_fa_author by name; `result.json`'s `options.author` is the module's NAME when a module object was
  handed in (True and a name are written as they are, so Retomoto's result.json is unchanged).
- `main()`: `--author [module]` for `one` and `chain` through `kl_graft.author_arg` (was: a bare flag).
- docstring: the option under "options of 'one'", the cover list in the CAMPAIGN PRE-PASS paragraph.
  `chain()` itself needed no change: it hands `**opt` to both steps.

**tools/kl_graft.py**
- new, in front of `build()`: `AUTHOR = 'kl_fa_author'`, `AUTHOR_NAMES` (the nine names), `author_module(author)`
  (None / False -> None; True -> kl_fa_author; a str -> `importlib.import_module`; a module -> itself; a module
  that lacks one of the nine names is a ValueError BEFORE anything is built) and `author_arg(a)` (takes
  `--author [module]` out of an argument list: False / True / the name; the name is the argument directly behind
  the option when it does not start with `--`).
- `build()`: `au = author_module(author)` instead of `import kl_fa_author as au`; `au.DROP` and
  `au.layer_names(Jn)` are wrapped in `tuple()` (a module may hand a list); the five call sites are otherwise as
  they were and still read every name off the module at the moment of use (kl_fa_street.hook / kl_fa_blast.hook
  replace kl_fa_author's prepare_host / strip / wire / KEEP from outside; KEEP is a module `__getattr__` there).
- `__main__`: `author = author_arg(a)`.
- docstrings: the option line at the top; **the interface is written down in `build()`'s docstring, under
  `author:`** - the nine names and what each must be.
- NOT changed, on purpose: `verify()` still reports only MORE than one cover list (the study's item A also asks
  for a line for ZERO: it would add a problem to every build without a list and is outside this stage's two
  changes - see T1.6). kl_fa_author.py is untouched (no export was needed).

Every other place that names kl_fa_author (MEASURED `grep -n kl_fa_author tools/*.py`): kl_expansion.py (its
`join_ini` and `build_map(..., author=True)`: Retomoto's own, still valid), kl_fa_blast / kl_fa_street / kl_fa_loot
/ kl_fa_van / kl_fa_bots_rt / kl_map_escape / kl_fa_talk (Retomoto's layer and its measurements, other sessions'
files): none of them is 'the layer handed to the graft'. In kl_graft.py and kl_maps.py no import of kl_fa_author is
left; the name stands only in `AUTHOR` and in comments / the run log.

### T1.2 The cover list: what the one word changes, on all 20 Dead Men levels (no build)

MEASURED `python C:/kl_scratch/bank/t1/s/passive.py` (campaign_drop() with and without the entry, in memory; output
C:/kl_scratch/bank/t1/passive.txt). Every level has exactly ONE FFCoverList (a single ZLIST node). 15 levels have
it as the top-level `CoverList` (systems side by kl_prpjoin.sides: never a candidate of the pre-pass) - among them
M09_A and M09_B, so Retomoto's pre-pass is untouched (M09_A 259 -> 259 dropped, M09_B 256 -> 256). Five keep it in a
campaign subtree and lost it; with the entry exactly that one subtree stays and nothing else moves:

| level | its list | dropped subtrees before -> after |
|---|---|---|
| M03_A | `Special!CoverList` | 489 -> 488 |
| M06_A | `Specials!CoverPoints!CoverControl` | 238 -> 237 |
| M07_A | `Special!CoverPoints!CoverControl` | 126 -> 125 |
| M12_A | `Specials!CoverPoints!CoverControl` | 240 -> 239 |
| M13_B | `Specials!CoverPoints!CoverControl` | 220 -> 219 |

(The study named M03_A and M06_A only; M07_A, M12_A and M13_B are the same case.) For a layer that keeps F07's
`Specials!`: F07's own list is `Specials!CoverPoints!CoverControl` - the layer must DROP it (kl_fa_author.DROP =
`('Specials!CoverPoints!*',)`), or the level has two and verify() says so. On M06_A / M12_A / M13_B the map's
list even has the same top-level NAME as F07's.

### T1.3 HERO_AT for M03_A: a real marker in the secure yard

- MEASURED `awk` over the study's node dump G:/kl_scratch/cfa_bank/M03_A.tsv (every node with class,
  controllers, world place): inside the yard (x -450..2450, z -4700..-700, y 150..320) the level has TWO
  top-level nodes that are not geometry: `Special!JumpPoints!Jump#060` (ZSTDOBJ + JumpPoint) at (-313, 205, -4398)
  and the path blocker of the roller door (557, 234, -4682). The checkpoint markers (`Special!Checkpointsave!
  CP_0n_PosP1/2`, what HERO_AT uses on M09) are elsewhere: CP_01 back streets, CP_02 car-park roof, CP_03 vault
  lobby (394, 241, -7129) / hall, CP_03b / CP_04 vault, CP_05 hall. `Jump#131` (266, 202, -5002) is 5 m INSIDE the
  dock, behind the roller door, not in the yard.
- So: `Special!JumpPoints!Jump#060` -> `Heroes!Hero_01`. It is the developers' own jump point behind the rappel
  (re/campaign_fa_bank.md 1.3 beat 4). MEASURED `python G:/kl_scratch/cfa_bank/stations.py M03_A
  "Jump#060:-313:205:-4398" "study start:300:200:-4350"`: 'polygon 367 part 0 (566 polygons) off the mesh by 0
  height off -4'; the study's START place is polygon 368 of the same part, 6 m east (12 m over polygon centres).
- Its rotation (MEASURED `python C:/kl_scratch/bank/t1/s/marker.py M03_A "Special!JumpPoints!Jump#060"`): a turn
  about Y, ZGEOM[1] = [0.724 0 0.690, 0 1 0, 0.690 0 -0.724]. Read as a player group (local -Z, kl_fa_author.look9)
  it FACES (-0.72, -0.69): into the yard's south-west corner, away from the dock door. Cosmetic for a bare boot.
- kl_maps.one's `Story` class retypes the marker to a model-less ZGROUP named Heroes!Hero_01 and takes its
  controllers off (the JumpPoint goes), exactly as for M09's markers; kl_graft then puts F07's group there.
- Only ONE group is placed (the yard has one marker): Hero_02..08 and the Henchmen stay at F07's coordinates, as
  14 of the 16 do on M09. A direct boot starts at Hero_01. The authored bank (kl_fa_bank.prepare_host) places all
  sixteen itself and is built WITHOUT --heroes, as kl_fa_author.test is (heroes=False).
- ASSUMPTION (as for M09's entries): a player can stand there. Not seen in Dog Days. The yard is closed by the
  roller door: a bare boot stands locked in until that door is opened (re/campaign_fa.md 3.3 step 3).

### T1.4 Checks (a) and (c): Retomoto is the same archive, by default and through a module's name

Tool hashes: `sha1sum tools/*.py re/*.json klhook/KLJoin.retomoto.ini` before the baseline and before the rebuild
differ in tools/kl_graft.py and tools/kl_maps.py ONLY (MEASURED `diff tools_before.sha1 tools_after.sha1`); HEAD
moved 40a8a7a -> ada8830 in between (another session, CLAUDE.md only).

**(a) rebuilt after the change** - `python tools/kl_fa_loot.py test "C:/kl_scratch/bank/t1/after" --no-wardrobe`,
exit 0, 'RESULT: PASS'. MEASURED `python s/manifest.py diff before.manifest.json after.manifest.json`:
- chain/F07+M09_B/R09_Main.zip: '31 members / 31 members, 31 equal (name, size, CRC), 0 differ; archive bytes
  299581770 / 299581770'
- 'R09+M09_A (R09 = F07+M09_B)'/F01_Main.zip (the dressed level): '30 members / 30 members, 30 equal, 0 differ;
  archive bytes 187929451 / 187929451'
- light/F01_Main.zip: '30 / 30, 30 equal, 0 differ; 187929451 / 187929451'
- all 57 binary files beside the archives (.WAV .WHD .hti, the _LS bank, KLJoin.ini) and the three graft.txt: same
  size and sha1.
- the six that differ by sha1 are log.txt and result.json of the three folders. MEASURED `python s/beside.py before
  after`: 'RESULT: SAME but for the folder name and the seconds' (log.txt: the out folder in its 'built ...' line;
  result.json: 'seconds' 33 / 39 and 40 / 36). The two 203-line build logs are equal line for line after the same
  replacement (`diff`, exit 0).

**(c) through a module's name** - a dummy tools/kl_t1_dummy.py (a module `__getattr__` that hands on
kl_fa_author's nine names at the moment each is asked for; DELETED after the check) and
`python C:/kl_scratch/bank/t1/s/dummy_build.py "C:/kl_scratch/bank/t1/dummy"`: kl_fa_loot.test's steps one for one
(voices on, the street / blast / loot hooks, the loot dressed on the written level, lighten trim,slim), but the
chain is asked for through kl_maps' own command line: `kl_maps.main()` with the arguments `chain <out> F07 M09_B
M09_A --author kl_t1_dummy --keep`. MEASURED `python s/manifest.py diff after.manifest.json dummy.manifest.json`:
the same three lines - 31 / 30 / 30 members equal, 0 differ, archive bytes equal - and every binary file beside
the same. `python s/beside.py after dummy`: the only line that differs besides folder name and seconds is
result.json's `"author": true` -> `"author": "kl_t1_dummy"` (three folders). The build asked the dummy for every
one of the nine names (its counter: HOST 6, prepare_host 5, strip 6, KEEP 6, DROP 6, layer_names 6, complete 6,
wire 5, campaign_names 6 over the two steps, the presence test included).
So: default = name = the build of before the change, to the byte of every member.

Small tests of the two helpers (`python - <<` in the session, not kept): `author_arg` on `--author` at the end,
before `--load`, with a name before `--keep`, and absent -> True / True / 'kl_fa_bank' / False with the list
shortened by exactly the option (and its name); `author_module(True) is author_module('kl_fa_author')`;
a module with only HOST -> 'ValueError: authoring module thin lacks prepare_host, strip, KEEP, DROP, layer_names,
complete, wire, campaign_names'; an unknown name -> ImportError.

**(a) once more, on the files as committed** (a docstring line of kl_maps.py was touched after the builds above):
`python s/dummy_build.py "C:/kl_scratch/bank/t1/final"` = the same steps with the command line `chain <out> F07
M09_B M09_A --author --keep` (the option ALONE, through `kl_maps.main()`). MEASURED `python s/manifest.py diff
before.manifest.json final.manifest.json`: 31 / 30 / 30 members equal, 0 differ, archive bytes 299581770 /
187929451 / 187929451 as the baseline; `python s/beside.py before final`: 'RESULT: SAME but for the folder name and
the seconds' (result.json `"author": true`, as before the change).

### T1.5 Check (b): the bare campaign grafts hold exactly ONE cover list, the other numbers are the study's

Commands (with `--keep` only so that the archive can be read back; archives deleted afterwards). Each ends with
exit code 1 because verify's problems are not 0 - the findings of a level without a layer, as in the study:
- `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m03" F07 M03_A --campaign --keep` -> 'campaign pre-pass: 488
  subtrees dropped', 'verify: problems: 11', 'built ... 310 MB, 31 members'.
  `python s/covers.py "C:/kl_scratch/bank/t1/m03/F07+M03_A campaign"`: '19676 nodes, 439 top-level, 1 FFCoverList,
  165 nodes named *coverbox*', 'FFCoverList on ROOT\Special!CoverList (ZLIST)'. Of the 165: 118 ZSTDOBJ under
  Locations (what the game makes covers of - the study's 118) and 47 ZBoxPrimitive (the kept PlayerCoverCollision /
  NoCoverBox markers, 46 under Special!).
- `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m06" F07 M06_A --campaign --keep` -> '237 subtrees dropped',
  'verify: problems: 10', '327 MB'. covers.py: '19158 nodes, 318 top-level, 1 FFCoverList, 242 nodes named
  *coverbox*', 'FFCoverList on ROOT\Specials!CoverPoints!CoverControl (ZLIST)'; 225 ZSTDOBJ (the study's 225) + 17
  ZBoxPrimitive.
- Against the study's kept results (`python s/results.py <mine> <study plain> <study coverfix>`, the files under
  `<work>/build/cfa/tooling/` and `.../v2/`), every key of result.json but 'seconds':
  - against the second tooling agent's cover-fix builds: 1 key of 34 (M06_A: of 32) differs - the folder's 'tag'.
  - against the plain builds: 5 keys. M03_A: campaign_dropped 'Special!' 229 -> 228, campaign_kept 'Special!' 100 ->
    101, tops 438 -> 439, entities 19,675 -> **19,676**, ref_slots 30,556 -> 30,557. M06_A: 'Specials!' 99 -> 98 and
    41 -> 42, tops 317 -> 318, entities 19,157 -> **19,158**, ref_slots 30,038 -> 30,039.
  - unchanged, as re/campaign_fa.md section 1 has them: M03_A rooms 28, textures 1,866, materials 1,221, .prm
    chunks 64,870 (= 64,871 chunk-table entries), mesh 232,480 bytes, sounds / waves 4,724 / 4,586, archive 310.2 MB,
    .prm 85.7, .TEX 373.9, .HVK 3.0 MB, dangling 0, problems 11 (1 stream clip + the 10 findings of a level without
    a layer), kl_fa.check 1 CRASH / 9 BROKEN / 4 DEGRADED / 1 NOTE. M06_A rooms 7, textures 1,589, materials 1,002,
    chunks 53,959 (53,960 entries), mesh 258,988 bytes, archive 326.8 MB, .prm 79.5, .HVK 2.2 MB, dangling 0,
    problems 10.
- **HERO_AT**: `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/m03h" F07 M03_A --campaign --heroes --keep` ->
  log 'kl_maps: Heroes!Hero_01 stands at Special!JumpPoints!Jump#060 (-313, 205, -4398)', 'Heroes! groups placed
  where M03_A has them: 1' (without --heroes: 0). Read back from the built .prp (covers.py with the names):
  'Heroes!Hero_01 (ZGROUP): ZGEOM[2] [-312.7, 204.7, -4398.4], ZGEOM[1] [0.724, 0.0, 0.69, 0.0, 1.0, 0.0, 0.69, 0.0,
  -0.724]' - the marker's place and turn; Hero_02 stays at F07's (10558.2, 440.0, 3222.6), where Hero_01 is in the
  build without --heroes. result.json differs from the build without --heroes in 'heroes' only.
- **A module that is NOT kl_fa_author, on the bank** (tools/kl_t1_min.py: the nine names and nothing else, KEEP /
  DROP / layer_names / campaign_names handed as LISTS, one campaign node named by campaign_names; DELETED after
  the check): `python tools/kl_maps.py one "C:/kl_scratch/bank/t1/min" F07 M03_A --campaign --author kl_t1_min
  --keep` -> 'campaign pre-pass: 487 subtrees dropped' (488 less the one kept), 'kl_t1_min: prepare_host(F07)',
  'kl_t1_min: strip(M03_A), 864 top-level subtrees', 'kl_t1_min: wire() on the joined scene: 19677 nodes,
  GamePlay!2_Secure_Parking!AnimProxy_Garage_Open is in it 1 time(s)', 'verify: problems: 11'; read back: 19,677
  nodes, 440 top-level, 1 FFCoverList, the kept node in the scene; result.json `options: {'author': 'kl_t1_min'}`,
  dangling 0. So the command of T1.7 works on this level with a module of its own.

### T1.6 What is GUESS / ASSUMED, what is open

- ASSUMPTION (kl_maps.HERO_AT, marked there): a player can stand at Jump#060. It is on the mesh (MEASURED) and is
  the campaign's own jump point; nobody has stood there in Dog Days. Its facing (into the south-west corner) is
  the marker's own, not chosen.
- NOT DONE, on purpose: a verify() line for a level with NO cover list (the study's item A, second half:
  re/campaign_fa.md 3.1). kl_graft.verify still fails only on more than one (`ncov > 1`). It is one line
  (`elif not ncov: bad.append('no cover list (FFCoverList): no cover box becomes a cover')`), but it changes the
  problem count of every build that has none, in a file other sessions' builds go through, and it is outside the
  two changes this stage was given. Until it is in, count them: `python C:/kl_scratch/bank/t1/s/covers.py <folder>`
  (the next stages' check 'exactly one FFCoverList').
- NOT DONE: `kl_fa_author.FINISH` is still not called by kl_graft / kl_maps (that file's own comment asks for
  it). What works on the WRITTEN level stays the authoring module's own step after `kl_maps.one` returns - as
  kl_fa_author.test / kl_fa_blast.test do it. For the bank that is kl_fa_bank's `test` / `build` command.
- The other tools that import kl_fa_author for Retomoto's numbers (kl_fa_bots_rt, kl_fa_loot.survey / walk
  defaults, kl_map_escape.van_prepare, kl_fa_talk.BLAST_TIMER, kl_expansion.join_ini: re/campaign_fa_tooling.md
  11.4 item 5) are untouched: where a later stage runs one of them on the bank it meets those names there.
- M07_A, M12_A and M13_B now keep their cover list too (T1.2). Nobody has built them; the change is the same one
  node as on M03_A / M06_A.
- Nothing here was run in the game.

### T1.7 For the next stages: how a build is called with a module of its own

```
python tools/kl_maps.py one "<out>" F07 M03_A --campaign --author kl_fa_bank --keep
```
- -> `<out>/F07+M03_A campaign/` with F01_Main.zip, the files beside it (.WAV .WHD .hti, the _LS bank), graft.txt,
  log.txt, result.json (`options.author` = 'kl_fa_bank'). Exit code 0 only when verify's problems are 0: a build
  with KNOWN problems ends with 1 and is written all the same (read result.json: 'ok', 'problems').
  Without `--keep` the archive is measured and deleted. NO `--heroes`: the module places the sixteen player
  groups itself (prepare_host); `--heroes` is for the bare boot `one <out> F07 M03_A --campaign --heroes --keep`.
- The module's name stands DIRECTLY behind `--author` (an argument that starts with `--` is not taken as a name;
  `--author` alone stays kl_fa_author = Retomoto). From Python: `kl_maps.one(out, 'F07', 'M03_A', keep=True,
  campaign=True, tag=' campaign', author='kl_fa_bank')` (a name, or the module object; `author=True` is
  kl_fa_author), `kl_maps.chain(..., author=...)` and `kl_graft.build(..., author=...)` take the same.
- tools/kl_fa_bank.py must hold the nine names of `kl_graft.AUTHOR_NAMES` - `kl_graft.build`'s docstring, under
  `author:`, says what each must be. In short, in the order they are used:
  `campaign_names(level)` (kl_maps, before the build: exact top-level names of M03_A that the pre-pass must leave
  in; `[]` for any other level) -> `HOST` ('F07') and `prepare_host(S, log)` (the stock kl_graft.Level, before the
  subtrees are chosen: places and values of F07's own objects) -> `strip(M, log)` (the converted kl_graft.DeadMen,
  before the join: controllers off kept nodes, map nodes re-placed) -> `KEEP` / `DROP` (patterns of F07's MAP
  subtrees that stay / go: `DROP` must name F07's cover list `Specials!CoverPoints!*` when `KEEP` holds
  `Specials!`, because M03_A's own `Special!CoverList` now stays) -> `layer_names(Jn)` (top-level names of the
  layer in the joined scene, for kl_fa.repair's prune) -> `complete(Jn)` (True: one map) -> `wire(Jn, log)` (once,
  on the joined scene: reference lists; values of existing controllers only). Each name is read off the module at
  the moment it is used, so a `test` command may set module globals (NO_AI, flags) before it calls kl_maps.one in
  the same process - import the module by its own name first (`import kl_fa_bank` at the bottom, as kl_fa_author
  does), or the build imports a second copy that has not seen the flags.
- A module that lacks a name fails at once: 'ValueError: authoring module kl_fa_bank lacks ...'.
- New entities and anything that needs chunk numbers are NOT part of the interface: do them on the written folder
  after `kl_maps.one` returns (kl_fa_author.FINISH is the pattern).
- Scratch scripts that stay (read-only helpers): C:/kl_scratch/bank/t1/s/covers.py (cover lists and named
  top-level nodes of a built folder), manifest.py + beside.py (two build trees member for member), results.py,
  marker.py, passive.py, dummy_build.py (the Retomoto regression through kl_maps' command line: `dummy_build.py
  <out>` rebuilds what `before.manifest.json` records; 1.5 minutes).

## Stage T3 - the collision route test as a tool (NEW tools/kl_route.py)

STATE: DONE (2026-10-11 13:40), committed as 812565b. One new file, `tools/kl_route.py` (1,316 lines), and this
section; no other file was touched, no build was run (T1 was editing kl_maps / kl_graft: every input is an
archive that existed).
Scratch C:/kl_scratch/bank/t3/ (0.2 MB): `checks.py` (every check below is one name of it: it prints the command
and runs it), `out/<name>.txt` (the outputs quoted here), `place_agree.py`, `flags_census.py`, `dbg.py` (what the
grid holds round a place). `<f1>` below = `<work>/build/cfa/fill1`.

### T3.0 What was read, and what the tool takes from each

- bank: `G:/kl_scratch/cfa_bank/skeptic/walk8.py` / `walk9.py` - kl_escape.Walk's sampled grid, a flood over
  (cell, floor height), REF ids taken out at flood time. TAKEN: the cell (20), the sampling pitch (10), the floor
  rule, the step (45 up / 60 down), the body heights (55..165), 'a place is reached from a floor near it', and
  'shut each set again in turn' as the test of NECESSARY.
- club: `G:/kl_scratch/cfa_club/skeptic/walk5.py` (kl_escape.Walk as it is: one floor per cell) - nothing new.
- Havana / prison / the critic: `G:/kl_scratch/cfa_critic/hwalk.py`, `prison_walk.py`, and on built archives
  `G:/kl_scratch/cfa_fill1/hwalk_built.py`, `prison_walk_open.py`, `havana_walk_open.py`. TAKEN: the body's
  half width (30), the 'thinnest crossing' search that names what is in the way in the order it is met, 'take
  out what was crossed and ask again', a crossing only where the mesh lies, and the snap of a place that stands
  in something to the nearest walkable spot (they took the nearest mesh cell within 2 m without saying so).
- park: `G:/kl_scratch/cfa_park/skeptic/sk_walk.py` - TAKEN whole as 'the way an AI is given': polygon middles
  joined through the middles of the shared edges, a sample every 25, a floor within 90, the body column free.
- `G:/kl_scratch/cfa_fill1/blockers.py`, `front_blockers.py` - TAKEN: the path blockers' boxes, tested against
  that mesh way. `closures.py` - read for what a closure is in the files.
NOT taken: walking only on mesh cells (hwalk: a player walks off the mesh, and a build with a broken mesh would
read as shut), and a body without width (walk8).

### T3.1 The tool

`python tools/kl_route.py walk | stations | doors <level> ...` and `route()`, `blockers()`, `stations()`,
`doors()`, `mesh_way()`, `load()` for other tools; `<level>` = a build folder, an archive or a stock level's name
of either game. The docstring is the spec: every number of the walker with whose it is, and what is ASSUMED.
In short: a lazy grid of 20-unit cells over the .HVK (floors under the cell middles, everything else sampled,
convex shapes by their planes); a walker with a body 60 x 60, 55..165 over its floor, stepping 45 up / 60 down;
a search that, when the way is shut, goes on through objects and names them; the navigation mesh for 'on the
mesh / which part', for where a crossing may be, and for the line an AI is given (with the path blockers).
Run times here: a walk 3 - 6 s, stations / doors over the whole bank 18 - 25 s.

New against the study's scripts (each one MEASURED on real files, below): the body has a width AND the walk is
not tied to the mesh; convex shapes are rasterized, not boxed; a place is walked from GROUND (not from a table
top); hidden bodies count by default and the verdict says when it hangs on them; a placement that does not
stand where its entity does is reported; path blockers and mesh links are part of the AI's line; every object
named carries its collision flags and their reading.

### T3.2 MEASURED while writing it

- Placements against entities (`python C:/kl_scratch/bank/t3/place_agree.py M03_A F07 "<f1>/F07+M03_A campaign
  open/walk_members.zip" "<f1>/F07+M03_A campaign beats/walk_members.zip"`): every STATIC / KEYFRAMED placement
  stands exactly where its entity's .gms chain puts it, in place and rotation: 0 of 3,653 (M03_A), 0 of 1,859
  (F07), 0 of 3,467 and 0 of 3,479 (the two built bank archives) differ by more than 2 units. (RIGID agrees too;
  VEHICLE placements stand elsewhere, 13 of 13 in M03_A; WEAPON placements agree in place and differ in
  rotation, 48 of 51 in F07 - neither is counted by the walker.) So 'a leaf moved, its collision left'
  is detectable: with the roller door's entity sunk by 2,500 in memory `Level.moved()` returns exactly
  `[(23559, 2500, 'M03_A_Garage_01a\SI0201_M03_BackDorAnim_01')]`, and `[]` on all four files as they are.
- Convex shapes: on the 850 convex shapes of M03_A, M11_B and F07 every vertex satisfies n.v + d <= 0 for every
  plane (largest value 1e-5) and every plane touches a vertex. Rasterized from the planes and clipped to the
  vertices' box, the 431 / 259 convex placements of M03_A / M08_A stay inside their world boxes, reach top and
  bottom, and fill 84 % / 76 % of the boxes' cells (what a turned door or car leaves free). Without the clip
  35 flat shapes (car windows) ran up to 43 over their own box: their planes do not close them.
- Collision flags by object name (`python C:/kl_scratch/bank/t3/flags_census.py M03_A M11_B M08_A F07`): 0x40
  alone = `ColiObj_Camera*` / `ColiObj_CamLamp`; 0x10 alone = `ColiObj_BlockSight` / `ColiObj_Vision` /
  `BlockVisionPlane`; 0x20 alone = `InvisibleBlock_*` / `ColiObj_NPCBlock`; 0x108 = `ColiObj_Hero*` / `OnlyHero`
  / `HeroOnly` / `ColiObj_Player*` / `ColiObj_HERO_hack`; 0x102 / 0x42 = shards, lamps, monitors; the plain world
  is 0x72. Read as: 0x20 stops every character, 0x8 the heroes only, 0x40 the camera, 0x10 sight, 0x2 shots.
  BY NAMES ONLY. One thing fits it from another side: at the Capitol's wing door the campaign has BOTH a
  hero-only plane (`ColiObj_Obj_Roadblock_01`, 0x108) and path blockers in state eBlocking
  (`PathBlocker_BunkerBackDoor_01`, `PathBlocker_LastGuys_01`) - one for the heroes, one for the AI
  (`python tools/kl_route.py walk M11_B --from 39211,830,30410 --to 40500,830,31900 --who npc`: FREE in the
  collision, 9 samples of the mesh way in those boxes; `--who hero`: BLOCKED by the plane).
- The bank's mesh: its narrowest shared edge on the round's way is 49 (a doorway: the mesh is drawn in from the
  walls), so 'no edge under 100' (the park's rule) cannot be a condition; the tool prefers 100, then 50, then
  any, and prints the narrowest it used. (The tab's Fragile Alliance bank: narrowest edges 18 and 29 on the two
  legs through its garage exit. Recorded; whether that has to do with the bots' deaths there was not looked at.)
- Path blockers as the tool reads them: bank 'open' build 4, all eBlocking, at the front entrance (boxes round
  (108, 802, -9400), (129, 802, -9359), (467, 802, -9356), (486, 802, -9399): G1.2's four); prison 'open' build
  35 with `PathBlocker_CageDoorB` eNotBlocking, prison 'beats' build the same one eBlocking (G1.4); the tab's
  Fragile Alliance bank 2 (`Triggers!GarageDoors!PathBlocker` eBlocking at (296, 203, -4682)).
- Places that are not ground: the Capitol's checkpoint 5 (37600, 830, 30521) lies INSIDE the block
  `Collapsed_Rubble_005` (collision y 696..963) and 75 off the mesh; 'wing C_01' is a display case; 'table' is
  the table. The study's walk snapped such a place to the nearest mesh cell within 2 m; this tool walks to the
  nearest GROUND within 2 m and says how far that is. A free floor is not enough: the chairs round the
  Capitol's table have free seats 54 over the floor, and a place given at the mesh's height (830 over a floor
  at 800) is nearer to a seat than to the floor - hence 'ground' (300 away and more than 400 floors reachable,
  by steps that can be taken back).

### T3.3 The checks (each: `python C:/kl_scratch/bank/t3/checks.py <name>`; output `out/<name>.txt`)

| what the study measured | input | the tool's line |
|---|---|---|
| bank: six door sets in series, each necessary (`walk9.py`) | `doors "<f1>/F07+M03_A campaign beats" --from "START yard=300,200,-4350" --via vault=399,-960,-12818 --to "street east=3958,700,-11173"` (name `bank_doors`: the built level with every door in its place) | `-> 7 closure(s) in 6 set(s); 7 necessary; with all of them out the way is FREE` - the roller door (REF 23559), a leaf of glass door 1 (27653), of glass door 2 (27648), the vault door (27063), the airlock's two planes (27787, 27790: one set), the hall / foyer leaf (26950) |
| the same on the stock level | `doors M03_A ...` (`bank_stock`) | the same line; REF 7437, 13998, 13986, 12805, 14012, 14015, 12596 = the ids of `G:/kl_scratch/cfa_fill1/closures_M03_A.txt` |
| bank, 'campaign open' build: free from the yard to the street (`walk8.py`: flood A reaches 45 of 46, the statue not) | `stations "<f1>/F07+M03_A campaign open"` + walk8's 46 places (`bank_open`) | `-> 45 of 46 places reached from the first in the collision; NOT: statue (behind bars)`; the statue: `NOT reached even through objects` |
| | `walk` yard -> vault -> street east on it (`bank_open_walk`) | `FREE, 86 m of cells, floor y -960..242` and `FREE, 173 m of cells, floor y -960..803`; `RESULT: FREE; the mesh way: 1187 samples, all free` |
| the plain build: only the yard (`walk8_built.txt`: 5 of 46) | `stations "<f1>/F07+M03_A campaign beats"` + the 46 (`bank_plain`) | `-> 5 of 46 places reached` (START, both stacks, the traitor row, the dock door) |
| Capitol: four static switches, each on the only way (`walk3.py`) | `doors M11_B --from START=33981,830,30387 --via table=42500,830,31915 --to "van stop=27000,20,22600"` (`havana_strict`) | `-> 5 closure(s) in 5 set(s); 5 necessary; with all of them out the way is FREE`: `M11B_OYCHECK_BEFORE01` (4333) and `SI0100_M11_BarricadeB_01` (4617) = the bunker's ONE switch, `ColiObj_Obj_Roadblock_01` (5313, the wing door), `SO0201_M11_Corner_01` (10618), `SO0201_M11_BarricadeXX_01` (10619) - the five static pieces G1.5 took out for the four switches |
| Capitol 'open' build: all 13 legs free | `walk "<f1>/F07+M11_B campaign open"` + walk3's chain (`havana_open`) | 13 x FREE (39, 14, 15, 26, 41, 53, 24, 47, 5, 32, 14, 39, 29 m) |
| prison: seven closures in series (`prison_walk.py`) | `doors M08_A` + the critic's ten stations, `--hidden-out` (`prison`) | `-> 7 closure(s) in 7 set(s); 7 necessary; with all of them out the way is FREE`: cage door B, two in the ground passage, two of the last gate, the two fences |
| | the same with hidden bodies counted (`prison_strict`) | the same seven; the two fences now each hold `FenceFall_Pre` AND its hidden twin `FenceFall` (13736, 13730) |
| prison 'open' build: 9 of 9 legs free | `walk "<f1>/F07+M08_A campaign open"` + the ten (`prison_open`) | 9 x FREE; `the mesh way: 788 samples, all free` |
| park: 1,271 samples free (`sk_walk.py`) | `walk M06_A` + its eight places (`park`) | `RESULT: FREE; the mesh way: 1271 samples, all free`; per leg 18, 128, 61, 272, 311, 270, 211 samples over 4, 30, 14, 66, 74, 62, 51 m: sk_walk.txt's own figures, leg for leg |
| club (not asked; for the record) | `stations "<f1>/F07+M05_A campaign open"` + round A's 14; `doors` on the 'beats' build (`club_open`, `club_doors`) | `14 of 14 places reached`; `4 closure(s) in 4 set(s); 4 necessary`: a leaf of each office door and the two entrance seals (`HeroColi`, `Plane01`, both 0x108) |
| the tab's Fragile Alliance bank: a known-good route | `walk "<work>/build/w_tabM/KLExpansion/Maps/DM03"` through the places of its bots' own route (`<work>/build/z_route/M03/bots.txt`: START row (-1808, 700, -11838) -> entrance -> hall -> stairs -> the dock's loot (424, 224, -6154) -> garage exit -> yard -> before the opened wall -> alley (-1650, 149, -170) -> level exit -> boarding place) (`fa_bank`) | 10 x FREE (31, 16, 30, 29, 29, 32, 10, 6, 26, 12 m; the opened wall: `floor y 150..200`); the mesh way crosses by `a LINK of the mesh (kind 2) from (-1704, 220, -766) to (-1700, 150, -534): 232 across, 70 down` - the link bots.txt names |
| the other way round: the stock map, the wall standing | `python tools/kl_route.py walk M03_FA_A --from -1706,219,-899 --to -1650,149,-170` | `NO WAY even through objects`; first of what bounds the reached area: `SO0101_M03_Wall_Low_8m_05` - the piece tools/kl_escape.py opens |

Also run: `--open` by name and by REF (the 'beats' build with five sets named out and the vault door left:
both legs `BLOCKED` by REF 27063 `SI0102_M03_BankVault_Door_PRE` and nothing else, `with them out: FREE`, 9
samples of the mesh way in the door; with the door named too: `RESULT: FREE`), `--rigid`, `--who`, `--no-mesh`,
bad arguments (exit 2 with one line), and the five functions called from Python in one process (48 s for a route,
its blockers, a stations run, a doors run and a mesh way on the bank).

### T3.4 Where the tool's figures differ from the study's, and why

- Lengths are of cells through the collision (bank 86 m in, 173 m out), not of mesh polygons (the study: 120 /
  164 m; the tool's own mesh way: 96 / 188 m).
- `doors` names the LEAF crossed, not the whole door: one leaf of a double door out is a gap of 1.2 m and enough
  for the walker (it needs 0.8). Sets are counted by parent + name (less the number, less LEFT / RIGHT), so the
  bank's airlock (two planes, four leaves) is one set and its vault door, crossed twice by one way, one closure.
  The Capitol's bunker is one switch in the campaign and two closures here (two static pieces 5 m apart).
- 'Reached' is 'the walk comes to a free floor within 86 of the place, nothing between the two but what the
  place stands in'. 86 = the bank walk's rule (a floor within two cells: a square, 56 at its corners) plus the
  half width (30) the bank walk's walker did not have. With 70 (40 + 30) the trolley place fails by 2 units -
  the walk comes to within 72 of it, the trolley and two cartons stand there - which is why the constant is
  argued in the source. For loot use `--near 125` (a money container's reach); for a spawn point read 'gap'.
- Hidden bodies COUNT by default (the study's second agents left them out, fill1 ran both). It matters once in
  these checks: at the Capitol's corner the only floor on the way is that of the HIDDEN `SO0201_M11_CornerBroken_01`
  (`dbg.py M11_B 32255,864,28907`), so with `--hidden-out` the stock level has no way there at all - not even
  through `Corner_01`; hwalk did not see it because it walked on the mesh where it found no collision floor.
- In the bank 'open' build the six loot-wall places stand inside `Vault_POST` (REF 26914, the vault's blasted
  state, hidden at load) - `stations` prints it. The walk comes to within 50 of each all the same.

### T3.5 GUESS / ASSUMED (all in the docstring and at the constants)

ASSUMED: the step (45 / 60) and the body (60 x 60, 55..165) - never read in kl2.exe; that a hidden body may
collide (counted, `--hidden-out` for the other reading); the flag reading behind `--who` (names only); that the
.HVK's place of a key-framed body is the one that holds when its entity was moved (the tool only reports the
disagreement). GUESS: `ISLAND` / `ISLAND_N` (what is ground: 300 away, 400 floors), `PB_DY` (a path blocker's box
counts 100 above and below itself: what a blocker does to the mesh was not read), `GAP` (2 m, the Havana walk's).
LIMITS: no climb, vault or drop over 60 (`--down`); RIGID bodies, vehicles and weapons do not count (`--rigid`
for the first two) but a car's KEYFRAMED doors, wheels and windows do, where the file has the car (the tab's
bank has one on its yard way point: 45 samples of the mesh way); a convex plate thinner than 5 can slip through;
a convex shape is never a floor (a lift, a plank); the mesh way runs between polygon MIDDLES, so a leg inside
one polygon is one sample.

### T3.6 For the next stages: testing the bank's route

From the command line (`<b>` = the build folder; exit 0 = free / all reached):
```
python tools/kl_route.py walk <b> --from "START=<x,y,z>" --via "vault=399,-960,-12818" --to "street=3958,700,-11173"
python tools/kl_route.py walk <b> ... --open SI0102_M03_BankVault_Door_PRE_01      (the same with the vault door out)
python tools/kl_route.py doors <b> --from ... --via ... --to ...                   (what is still a closure, and is each necessary)
python tools/kl_route.py stations <b> "START=<x,y,z>" <every spawn place> --near 30
python tools/kl_route.py stations <b> "START=<x,y,z>" <every loot place> --near 125 --open SI0102_M03_BankVault_Door_PRE_01
```
What to expect of the authored bank with the lead's defaults (every door set open at build time EXCEPT the vault
door) - MEASURED on the study's 'beats' build with the five other sets named out by `--open`, not on a build of
the layer, which does not exist yet: `walk` without the vault door named: the legs into and out of the vault
`BLOCKED` by `SI0102_M03_BankVault_Door_PRE` (there REF 27063) and nothing else, `with them out: FREE`, 9 samples
of the mesh way in the door; with it named (or once its fall-back took its collision out at build time):
`RESULT: FREE; the mesh way: 1187 samples, all free`. `doors` should then say `1 closure(s) in 1 set(s); 1
necessary`. A `MOVED:` line in the head means a leaf was sunk and its placement left behind, or the reverse:
fix the build, do not argue with the line.
From a module (the same answers as dicts; one Level and one grid per process, so several questions cost one read):
```
import kl_route
r = kl_route.route(folder, [START, VAULT, STREET], opened=['SI0102_M03_BankVault_Door_PRE_01'])   # r['free'], r['legs'][k]['crossed']
objs, free = kl_route.blockers(folder, [START, VAULT, STREET])            # [{'ref', 'name', 'kind', 'at', 'dist', 'hidden'}] nearest first
rows = kl_route.stations(folder, [START] + places, near=30)               # row['mesh'], row['part'], row['reached'], row['gap'], row['in']
d = kl_route.doors(folder, [START, VAULT, STREET])                        # d['closures'][k]['necessary'], d['sets'], d['free']
m = kl_route.mesh_way(folder, [START, VAULT, STREET])                     # per leg: 'samples', 'nofloor', 'hit', 'blockers', 'links'
```
`opened` takes REF ids and / or text looked for in the entities' paths (a group's name opens its subtree).
What the bank's later stages should look at beside FREE: (1) the four path blockers at the front entrance are
eBlocking in the bare build; the mesh way passes between their boxes (0 samples in them) - if the layer moves
the way or the engine blocks whole polygons (not read), `walk` shows it as `PATH BLOCKER ...`; (2) `stations`
puts every place on a mesh PART: all of the round must be on the part of the START (566 polygons); (3) hidden
things the layer shows or blows (`Vault_POST`) are in the walk by default - use `hidden=False` / `--hidden-out`
to see the level as it is at load, and both when a beat swaps geometry.

### T3.7 Open

- Nothing of the walker was held against the running game beyond what kl_escape.Walk's rules already were (the
  yard wall). The body width is the new part: a FREE of this tool means a gap of at least 60 - 80.
- What a path blocker does to the mesh, and whether a hidden body collides: both would be read in kl2.exe, not
  measured in files.
- tools/kl_maps.py and tools/kl_graft.py were neither imported nor run by this stage. The tool imports kl_gms,
  kl_hvk, kl_pf4 and kl_scene, and kl_prpjoin / kl_fa only for a stock level's archive and for the path blockers
  (when those two cannot read a .prp the walk still runs and says that the path blockers were not read).

(end of Stage T3)

## Stage T2 - the escape van from WAY POINTS (tools/kl_map_escape.py: a second front end)

State 2026-10-11: DONE, all three checks PASS. Offline; nothing installed, the game not started (the owner was
playing). Scratch: C:/kl_scratch/bank/t2/ (2 MB: scripts `s/`, outputs `out/`, the three manifests, the build logs;
every archive deleted, the bare graft too).

### T2.0 Baseline, made BEFORE any edit

`python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/before M03` (tree at dca38bf + the
other sessions' uncommitted files) -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`;
`before.manifest.json` = 2 archives, 62 members (the graft step and the tuned map), `before/M03/*` = its 32 text
files. sha1 of tools/*.py and re/*.json before and after the stage: only kl_map_escape.py (mine) and
kl_fa_bots_rt.py (another session's, not used by this build) differ.

### T2.1 What was changed (one file)

tools/kl_map_escape.py, +219 / -20 lines. The old `van_plan` is CUT IN TWO at the line after its two routes are
read; nothing of what follows was rewritten, only guarded for 'no car':
- `van_plan(src, log)`: as before reads the ONE Dead Men escape car and its two spline routes, then calls
- `_van_road(src, L, G, P, pin, pout, log, v=None, back=BOARD_BACK, heading=None, cam=None, clear=())`: the old
  body from the curve on (road height, LIMIT_IN / LIMIT_OUT / MIN_IN / MIN_OUT, the lane, the cuts, wait / stop /
  end / heading / board, bounds, other cars, camera, drop list, the log). Guards: `v` None -> no own REFs, no gate,
  no 'things the car switched' loop, `car` None, `drop` empty, no boarding action looked for, the first log line
  says 'the road as way points'. `back` = how far beyond the last way-in point the van's origin stands (337 = the
  old rule, 0 = the point IS the origin). `clear` REFs are left out of the lane AND of the road height.
- NEW `van_plan_points(src, arrive, stop, leave, heading=None, at='origin', cam=None, clear=(), log=print)`: THE
  SECOND FRONT END. Docstring = the spec. `at='box'` gives the stop the meaning a Dead Men car's stop has (rear
  box there). `heading` given is MADE by two guide points STRAIGHT = 300 either side of the stop and a plan more
  than REL_MAX (6 degrees) off is a fault. A build that still has ONE escape car is planned as `van_plan` plans it
  (drop list, gate, switches) with only the road from the points: that is what makes check (a) an identity.
- NEW `van_road(src)`: a car map's own road in that form (`arrive`, `stop`, `at='box'`, `leave`).
- NEW `cam_spot(L, G, stop, heading, must, wish)` + `_van_cam(L, G, P, cam)`: a campaign level has no escape camera.
  `cam` given = that eye; None = the designers' when the build has one (old rule), else cam_spot's: a ring CAM_FAR
  = 18 / 22 m round the stop, CAM_OVER = 330 / 430 / 530 over the road, a floor under the eye, clear sight to the
  stop and to the drive CAM_SEES = 850 and 2500 after it; chosen: sees the end if any does, then most nearly behind
  the standing van. Faults: eye outside / under the map, within EYE_MIN of a floor, or NOT SEEING THE STOP.
- NEW `van_layer(P, log)`: a context manager for a build whose layer is an authoring module (T2.5).
- `van_build(..., road=None)`: with `road` the plan is made from points (the test); `other_cars(L, v, ...)` takes
  `v` None; `main()`: `van-plan <build> --points <road.json> [--json]`, `van-plan <build> --road`,
  `van <builds> <out> M03 --points <road.json>`. Without `--points` the argument list is parsed as before.
Not touched: `curve`, `lane`, `Poly`, `van_prepare`, `van_wire`, `van_hvk`, `van_check`, `gate_*`, `repair`, `check`.

### T2.2 Check (a): M03_FA_A's own two spline routes, given back as points, give the same van - PASS

- THE PLAN. `python C:/kl_scratch/bank/t2/s/check_a.py <work>/build/t_maps2/M03 out/road_M03.json` (van_plan against
  van_plan_points(**van_road(src)), every key of the two plans compared as JSON):
  `keys of the plan: 23 (spline front end), 24 (points front end); only in one: ['points']; in both and different:
  none`, `path 701 points, SAME, every coordinate`, `RESULT: SAME PLAN`. Numbers: lin 6000.0, lout 7999.9, waits
  (-2555.4, 152.0, 558.5), stops (3305.6, 2.0, 3.8), ends (10289.6, 2.0, -1102.8), headings 129.1 / 95.3 / 171.7,
  rear box (2970.0, 0.0, 34.8), camera (1576.7, 328.8, 407.6) from EscCameraSetup!CamPos01 = re/map_escape.md 10.4's
  bank row. The same on M01 (25 / 26 keys: gate and second camera too) and M02: `RESULT: SAME PLAN` twice
  (`out/check_a_M01.txt`, `_M02.txt`, `_M03.txt`).
- THE BUILD. `python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/points M03 --points
  C:/kl_scratch/bank/t2/out/road_M03.json` -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`.
  `python s/compare.py before.manifest.json points.manifest.json before points`:
  `M03/F01_Main.zip: 31 / 31 members, 0 differ; archive bytes 200762666 / 200762666`,
  `_graft/M03/F01_Main.zip: 31 / 31 members, 0 differ; archive bytes 196717360 / 196717360`,
  `M03/van.json: equal once the plan's "points" key (8 + 1 + 8 points) is taken out`,
  `RESULT: archive members that differ: 0; files beside M03's archive: 32 equal (but for the folder name), 0
  different, 0 only in one`. So the van laid from points IS the map's existing van, byte for byte.

### T2.3 Check (b): the old front end is unchanged - PASS

`python tools/kl_map_escape.py van <work>/build/t_maps2 C:/kl_scratch/bank/t2/after M03` on the file as committed
(its sha1 checked again after the run) -> `RESULT M03: van built; kl_map_tune PASS; van check: 0 fault(s)`;
`python s/compare.py before.manifest.json after.manifest.json before after`: both archives `31 / 31 members, 0
differ`, same archive bytes; `RESULT: archive members that differ: 0; files beside M03's archive: 32 equal (but for
the folder name), 0 different, 0 only in one` (van.json and van.txt among them: the plan's key order and every log
line are the old ones). `python tools/kl_map_escape.py van-plan <bare bank graft>` (old front end, no car) prints
nothing, as before (the '0 escape cars' fault is returned in the plan; that path is the old code, line for line).

### T2.4 Check (c): the bank's through lane against M03_A's collision - PASS, with ONE change to the study's road

Bare graft: `python tools/kl_maps.py one C:/kl_scratch/bank/t2/m03 F07 M03_A --campaign --keep` (310 MB, 11
problems as T1 says; deleted after the checks). Ground: 103,131 triangles of map collision, 525 convex bodies.
- THE STUDY'S LANE AS WRITTEN FAILS ONE LIMIT, on the leave leg: `FAULT only 2426 of clear lane after the stop
  (least 3000)`. Not collision: the designers' away road ENDS at (3958, 713, -11173), 30.1 m after the stop, the lane
  is tested VAN_NOSE = 600 beyond the drive's end, and MIN_OUT is 3000. Everything else of it passes (lane clear,
  drive in 48 m).
- THE CURE: the away road carried on east along its own line to (8600, 705, -11173). MEASURED (`s/east.py`,
  `s/probe.py`): the square's ground plane (S00701_M03_Square_PlaneA_03 / _15, y 700.0) runs unbroken along z -11173
  from x -2900 to 8600; the square is furnished out to x 8000 (benches, walls, palms; 12 - 15 map entities per
  1000 of x), 'UNIQUE_StreetFAR' stands at 9000 - 10000. What is DRAWN in the lane out there was not looked at.
- THE PASSING PLAN = `C:/kl_scratch/bank/t2/out/road_bank.json`:
  ```
  arrive  (-3248, 710, -11859) (-1917, 712, -12126) (-231, 707, -12332)        the designers' in-road, first three points
  stop    (949, 704, -11105)   at = origin, heading not forced
  leave   (2473, 705, -11177) (3958, 713, -11173) (8600, 705, -11173)          their away road + the extension
  ```
  `python tools/kl_map_escape.py van-plan "<bare graft>" --points out/road_bank.json` -> exit 0, 0 faults:
  `waits (-3248, 702, -11859) heading 102 -> 48 m in 7.2 s -> stops (949, 702, -11105) heading 67 (rear box at (638,
  700, -11235)) -> 71 m in 8.48 s -> ends (8000, 702, -11172) heading 90`; `road under the drive y 700.0 .. 700.0`;
  lane first pass: nothing (no cut); exact: lin 4805.3, lout 7068.2, wait [-3248.0, 702.0, -11859.0], stop [949.1,
  702.0, -11105.0], end [8000.0, 702.0, -11172.9], headings 101.6 / 67.3 / 90.0, board [638.3, 700.0, -11235.3],
  camera [-711.5, 1030.0, -11799.6] (cam_spot, GUESS: 18 m behind the stop, 330 over the square; `54 of the 144
  places tried see the stop and the drive 850 and 2500 after it; this one does not see the end` - ColiObj_Camera_01
  and SO0502_M03_Coner_01_01 are between, as on two of the three car maps).
  The four limits: 4805 of at most 6000 in (least 2000), 7068 of at most 8000 away (least 3000).
- MARGIN (`s/bank.py through`): the lane is also clear 260 and 320 wide (the test is 220); at 400 wide the planter
  S00701_M03_Square_DirtB_04 comes in 27 m before the stop, at 520 four benches on the drive away. The study's own
  script found 7 ray places on that planter: it walked straight legs, the tool walks the curve through the points.
- LEVEL BOUNDS the drive passes: Special!Levelbound!LevelBound_Outside_Right!Bound 46.3 .. 41.5 m BEFORE the stop
  (empty van), ...LevelBound_Outside_Left!Bound 25.8 .. 30.6 m AFTER it (players aboard). The same case as the
  Fragile Alliance bank's van (its Back_West bound 15.8 .. 17.6 m after the stop), where bots boarded and escaped
  live (CLAUDE.md, run H0_DM03). Not seen for a human passenger.
- ON F07'S KEYS (`s/prepare_dry.py`, van_prepare on stock F07 in memory): `563 position and 550 rotation keys
  rewritten in place (391 of them the drive, stop at key 159); drive in 5063 -> 4805 (x 0.95), away 7019 -> 7068 (x
  1.01)`, speed away 8.3 m/s mean, 14.8 top (stock 14.7): nearly F07's own drive, unscaled.
- END TO END (`s/trial.py`: F07 + M03_A --campaign with a throw-away module = KEEP VAN_KEEP, prepare_host ->
  van_prepare, the build inside van_layer; no layer, so no exit trigger to wire): the build `ok True, problems 10`
  (the layer findings), `.HVK: 9 static placements of the van's subtree cut, 5 key-framed placements of the van put
  at its waiting place`, then van_check on the WRITTEN folder with the plan: `keys 0.0 off the road height at most,
  largest step 59, nose up to 1.1 degrees off the tangent ... lane (5 rays, every 20, 350 before and 600 beyond):
  clear`, `boarding box at the stop: (636, 702, -11230); key-framed placements 5, at most 1.1 from their entities;
  camera: {'eye': [-712, 1030, -11800], 'over': 330, 'far': 1814, 'sight': []}`, `.HVK 3268992 bytes`, `0 fault(s)`.
  One note it prints: `no define FAEscCameraLAST in the level` (the layer's to bring: T2.5).
- THE CREW CAN GET THERE: `python tools/kl_route.py stations <bare graft> ... "rear box=638,700,-11235" "van
  stop=949,702,-11105"`: both `on the mesh, part 0 (566 polygons)` = the START's part; `kl_route.py walk --from
  "front entrance=300,800,-9350" --to "rear box=638,700,-11235"`: `FREE, 18 m of cells, floor y 700..800`, mesh way
  20 m, narrowest shared edge 310.
- OTHER STOPS TRIED (`s/paths.py`, `out/paths.txt`): heading 90 asked -> 93.7 made, rear box (613, 700, -11083), 0
  faults; heading 44 -> 39.9, 0 faults; heading 0 -> fault (-8 made, the bend refuses it); `at='box'` with the box at
  (638, 700, -11235) -> 0 faults; the first agent's stop (250, 707, -10700): `FAULT only 414 of clear lane before
  the stop (least 2000)` - confirmed dead. A way in laid THROUGH the planter and a bench: fault (1075 of lane);
  with both named in `clear`: 0 faults.

### T2.5 For the layer stage: the calls

```
import kl_map_escape as E
ROAD = dict(arrive=[(-3248, 710, -11859), (-1917, 712, -12126), (-231, 707, -12332)], stop=(949, 704, -11105),
            leave=[(2473, 705, -11177), (3958, 713, -11173), (8600, 705, -11173)])       # at='origin', heading None
P = E.van_plan_points(<a built F07 + M03_A folder>, log=log, **ROAD)      # P['faults'] must be empty
KEEP          += E.VAN_KEEP             # 'Animation/F07/F07_Escape_Vehicle_01.zip', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01'
prepare_host:    E.van_prepare(S, P, log)       # F07's keys + the 19 objects beside the drive
wire:            E.van_wire(Jn, P, log)         # names the van in EVERY OnlineExitLevelTrigger; raises when there is none
with E.van_layer(P, log): kl_maps.one(out, 'F07', 'M03_A', keep=True, campaign=True, tag=' campaign', author='kl_fa_bank')
rep = E.van_check(E.Level(<written folder>), log, P)                      # rep['faults'] must be empty
```
- The plan needs a BUILT folder for its collision (`Level` reads a build's F01_Main.zip, not a stock Dead Men
  archive). Either plan once on a bare graft and keep P as JSON beside the module (`van-plan ... --points ROAD.json
  --json` prints it; it is the map's collision that counts, and the layer does not change the square), or build
  twice. If the layer puts ANYTHING with collision on the square (kept squads' cars, cover objects), plan again on
  the layered build: the lane test sees only what stands under a 'Locations/' subtree plus every convex body.
- `van_layer` raises on leaving when one of van_prepare / van_wire / the collision join did not run.
- P['board'] (638.3, 700.0, -11235.3) = where the van's own BoardingTrigger stands at the stop: the bots' boarding
  station, the exit box and the escape marker go round it. In the FILE that box stands at the waiting place (it
  rides on the van): kl_fa_bots takes its place from the file - re/map_escape.md 12 and 15 say what was done for
  the three car maps ('--park' is superseded there).
- The layer brings: at least one OnlineExitLevelTrigger (F07's or a made one) and the box with the define
  FAEscCameraLAST (van_check prints a note without it; the three car maps have Dead Men's EscCameraSetup!EscCameraLAST).
- F07's second and third van are not kept by this (VAN_KEEP is the first only). Whatever unused van stays: CLAUDE.md's
  rule about a FakeTarget outside the rooms' bounds (crash 0x686a66) is the layer's to hold; the kept van's own
  waiting place (-3248, 702, -11859) is on the square, 46 m from the stop.
- Command-line twin: `python tools/kl_map_escape.py van-plan <folder> --points C:/kl_scratch/bank/t2/out/road_bank.json`
  (exit 1 on a fault), `python tools/kl_map_escape.py van-check <folder>`.

### T2.6 GUESS / ASSUMED (each marked in the code)

- GUESS (the lead's to turn): the leave leg's extension to x 8600. The collision floor and the furniture are
  MEASURED; that the square LOOKS like a road out there, and that nothing only drawn stands in the lane, is not.
  A shorter drive away should pass too - by arithmetic, not run: the end 3000 after the stop is at about x 3950, and
  the lane is tested 600 beyond it, so a leave leg that reaches x 4600.
- GUESS: cam_spot's choice (CAM_FAR, CAM_OVER, CAM_SEES, 'behind the van first'). The eye (-711, 1030, -11800) is
  over the square west of the stop, looking east along the drive. `cam=(x, y, z)` in ROAD overrides it.
- ASSUMPTION: STRAIGHT = 300 (what a forced heading means). Not used by the delivered plan (heading None).
- ASSUMPTION (the old ones, unchanged and now also the bank's): the Catmull-Rom curve, LIMIT_IN / LIMIT_OUT (GUESS
  in the code), the van not pitched to the road (flat here: y 700.0 all the way), a key-framed body moves with its
  entity, a passenger of a key-framed van passing a level bound.
- The stop's heading 67 is what the curve gives at the bend between the straight in (44) and the away road (90):
  the van stops already turning. Heading 90 (east) passes too and puts the rear box at (613, 700, -11083), nearer
  the steps; not chosen - the lead's / the owner's taste.

### T2.7 Open

- Nothing ran in the game. First live questions for this van: does it show and drive on the square; the bound
  25.8 .. 30.6 m after the stop with a human aboard; the camera's picture.
- `kl_fa_bots` / the talk and tune tools that read `van.json` of a `van_build` folder were not run on a
  points plan; the plan has the same keys plus 'points' ('car' is None, 'drop' and 'exits' empty on a level
  without a layer).
- The lane test does not see what is only DRAWN, nor what a layer adds outside 'Locations/' unless it is a convex
  body. van_check on the layered build is the gate.
- Another systems level than F07: `_van_nodes` still looks the van up by F07's names (re/campaign_fa.md, 'Another systems level as the way out of the chunk table');
  not this stage's.

(end of Stage T2)
