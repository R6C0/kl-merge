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
(20 MB): the logs, the four manifests, result.json / log.txt / graft.txt of every build, the scripts in s/.

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
