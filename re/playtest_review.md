# Review of track H: the scripted player (`tools/kl_playtest.py`, `re/playtest.md`, the rig patch)

2026-10-11, adversarial review. **Offline: no game was started, nothing was written in a game folder, nothing
committed.** I changed no tool or source file; this file is the only thing written in the repo. My own check
scripts are in the session scratchpad, folder `rev_h\` (`indep2.py`, `orbit.py`, `steer2.py`, `inicheck.py`,
`gotime.py`, `boxes.py`, `misc.py`, `kdis.py`).
`<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`.

Words: **re-derived** = I ran it or read it myself; **predicted** = follows from the rig's own constants, not
seen in the game.

## Verdict: ACCEPT WITH FIXES

The reading of the rig is right, the addresses in the patch are right, the patch is read-only and safe, the
generator does what its text says and every number of the report that I re-ran came out the same. The main
claim - no leg of any of the 35 routes leaves the navigation mesh - holds under a test of my own that shares no
code with the tool. What does not hold is the step from 'the lines between the way points are on the mesh' to
'the rig can walk it': the generator gives gotos a radius far below the tightest circle the rig can steer, and
at least two way points of the written scripts cannot be reached at all that way - one of them in
`PT_DM09_join`, the run proposed first. Fix that in the generator before the first live run (one must, section
4), and use the `rig2` scripts for everything that boards.

## 1. State of the tree when the review began (a fact the report does not have)

The report says 'klhook/ was not edited (the missing rig commands are a patch, not applied)' and 'no DLL was
built'. At 08:33 the tree's `klhook/klauto.c` **carries exactly that patch** (`git apply -R --check` of
`<work>\research\playtest\klauto_playtest.patch` passes, the forward check fails; file time 08:33:21, 69 s
after `re/playtest.md`), and `<work>\build\klhook\test_pt1\dinput8.dll` (08:33:23, holds the text 'waitstate')
and `ship_pt1` (no such text: klauto is TEST only) were built from it. The worker's scratch folder shows only
syntax checks on copies (`H\klhook_a`, `klhook_b`, `syn.bat`), and the build folder names follow the lead's
habit, so I take it the lead applied and built it; if the lead did not, the worker broke the task's rule.
Either way **the patch is what runs next**, so it was reviewed as live code (section 3).

## 2. Re-derived claims

| claim | how | result |
|---|---|---|
| local player = `[gamedata + 0x828 + 4 * (char)[gamedata + 0x898]]`, gamedata = `[0xdd265c]` (patch P3) | kl2.exe disassembled at 0x660b00: `mov eax,[esp+4]` / `mov al,[eax+ecx+0x898]` / `cmp al,0xff` / `jne` / `xor eax,eax` / `ret 4` / `movsx edx,al` / `mov eax,[ecx+edx*4+0x828]` / `ret 4`. Live, R7c_DM09.log: `escort: you: record 0, player 37be3300` and 1.3 s later `players: the moving one is #0 at 37be3300` | right; the game's pointer is the ZFFPlayer the rig found by moving. RTTI of vtable 0xbb45f4 = `ZFFPlayer` |
| vehicle state = byte `[rules+0x1dc]`, rules = `[[0x168e9e4]+0x54]`, vtable 0xbd3514 (P2) | RTTI of 0xbd3514 = `ZGameRulesHeist`; kl2 0x508ef0 returns `[this+0x54]` when `[[0x168e598]+0x5c] == 4`; klbot.c 219-274 reads the same and its `van <state> <timer>` lines are in every log of tonight | right |
| session state = `[[0x168e598]+0x70]`, 0x19 = GO (P1) | klsteam.c 148 / 343 (the `session:` line), klbot.c `KLB_ROUND 0x19` | right |
| what `goto` does | klauto.c 1365-1419 read whole | as the report says: reached = plan distance <= radius (1386-1388), a timeout goes on (1392-1394), stuck = 40 units in 1.5 s -> A / D 0.7 s, every third time C (1399-1414), `keep` leaves W / LSHIFT down (1374-1375), mouse rate `err / 0.17 * 5` clamped to 1800 (1396), no player for 6 s -> step skipped (1383) |
| 'level loaded' -> GO 20.5 .. 22.1 s | my `gotime.py` over every log in `live\` that has both lines: 67 runs (10-11: 37, 10-10: 22, late 10-09: 8) give 20.5 .. 22.1; 27 earlier runs of 10-09 give 0.0 .. 14.2 (another hook setting) | right for the present setting; the fixed 25 s leaves 2.9 s over the largest value seen. It depends on the hook's settings - `waitstate` is the sound form |
| the human stands on a START place at GO | START lists of three builds against `escort: you ... feet` of six logs (DM09: z 610, -930, 530, -770; DM06 (5510, 287, 4323); DM03 two places) | exact, and another place each run |
| the boarding box rides on the van, 337 behind its origin; the nose kills | my `boxes.py van`: `...\V_Van_00\BoardingTrigger` 337 behind the van's origin in the file, half sizes 95 x 135 x 80; `KillBox` 168 in front, half sizes 90 x 100 x 56 (so only the nose, 90 to either side); Retomoto board (-1850, 10459) = stop z 10796 - 337 | right. The wait place 230 beside the axis is clear of the KillBox by 140 |
| van cycle 29.5 s | first timer value of each state in eight logs: 1: 7.1 .. 7.5, 3: 7.9 .. 8.0, 5: 8.4 .. 8.5, 7: 5.5 .. 6.0 | the cycle is right; the split is in 7.5 / stands 8.0 / out 8.5 / 6.0 rather than 7.6 / 7.7 / 8.7 / 5.5 (no effect on the scripts) |
| a trigger box's size values are half sizes | `Triggers!ExitTrigger_01`: middle (408, 396, 460), values (4000, 400, 1000). H0_DM03 01:12:27.447: bot 1's node is 95 outside the box in z by the half-size reading (its feet 227), stage 3 is logged 0.218 s later **with the van's timer already at 7.1** (it starts at about 7.5) | half sizes is the better reading by far (the other is 600 off), but this one instance does not fit it to better than 100 .. 200 units. Say 'loose' where the doc says 'begins at z -540' |
| `Nav.height` is off on the stacked escalators (side finding) | `Nav.at(913, 399, 813)` returns polygon 331 (the UPPER escalator, corners at 498 .. 1000) with fitted height 388; the lower one is polygon 522 | confirmed - worth passing to the bots builder's owner. Note that the tool's own `floor()` gives 468 there and a fan from corner 0 gives 396 (the bot's place says 399): 'exact on every edge' is true, inside a polygon that is not flat it is an estimate too |

## 3. The files

**`tools/kl_playtest.py`** (new, 1,843 lines, read whole). It imports only `kl_fa` and `kl_fa_bots`, writes only
where it is told, and no check is weakened to pass: `bad_legs()` counts every leg whose `ok` is False, legs that
are off the mesh by their nature (the drop, the climb's foot) are printed as such and `route --until wall`
exits 1. Guesses are marked in the constants. Findings are in section 4.

**`re/playtest.md`** (new). Agrees with the code. Three places that are wrong or missing: the turning circle
(4.1), the friendly-fire risk of the fire button (4.4), 'GO_MS ... re\playtest.md 1.5' in the tool points at a
section that does not exist.

**The patch in `klhook/klauto.c`** (56 lines; now in the tree). Read as C:
- every read goes through `kla_rd` (ReadProcessMemory on the own process: cannot fault); nothing is written;
  no game function is called; it runs in `kla_script_step` / `kla_local_player`, on the game's thread like the
  rest of the script;
- `sel < 28` is the table's size ((0x898 - 0x828) / 4), 0xff falls out; a pointer that is not a ZFFPlayer falls
  back to the old 'one that moves' rule; the appended player is stored before it is read (`kla_npl++` first);
- the enum grows at its end, so no existing command changes its number; `waitstate` fails the script on a
  timeout the way `waitwin` does, `waitvan` logs and goes on; the `onwin` trap still runs in front of both;
- it compiles: the lead's `test_pt1` DLL exists (I did not run `cl` again).
No defect found. Two remarks: with P3 the line is `players: the local one is #k ...`, and a goto before GO now
runs into its own timeout instead of being skipped (the report says both).

**Outside the worker's files**: nothing of the worker's. The other modified files of the tree (`klclimb.c`,
`re/climb.md`, `kl_fa_bots_dyn.py`, `kl_fa_bots_rt.py`, `kl_chars.py`, the workflow file) and `klhook/out_auto/`
belong to sibling tracks and other sessions.

## 4. Defects

### 4.1 MUST - radii below the rig's turning circle: two way points of the written scripts cannot be reached

klauto.c clamps the mouse to 1800 counts/s at 0.17 degrees a count = 306 degrees/s. With W down the player
moves forward while he turns, so the tightest circle he can walk is speed / turn rate: **75 units at a walk
(400), 110 at a sprint (585)**. A target that lies inside that circle on its side, by more than its own radius,
is never 'reached': the pursuit law keeps the turn at its limit and he circles the target until the timeout.
He is never 'stuck' by the rig's test (a circle of 75 moves him more than 40 in 1.5 s), so nothing breaks the
circle.

The generator does not know this. `Route.finish()` shrinks a radius to `max(20, 0.45 x leg)` and passes the way
point before it with `keep`. Of the 311 way points of the six bot-2 routes, 267 have a radius below the circle
of their own speed (the hand-made walk that worked, `klhook/KLHook.round.ini`, used 110 .. 200 at a sprint, 90
at a walk, and 50 .. 60 only where it stopped).

Exact test (`orbit.py`: the best turn the rig can make, no simulation; P = where the goto before is 'reached'):

| script | lines | what | result |
|---|---|---|---|
| `PT_DM09_join`, `PT_DM09_board` (and `_r2`) | 101-103: `goto -1840 -1263 35 .. keep` / `goto -1881 -1183 41 .. keep` / `goto -1823 -1179 27 6000 keep` | the lower landing of the tower's staircase: 56 from where line 102 ends, 72 degrees off his heading, radius 27 | 20 inside the unreachable disc at 400 units/s; still inside at 300; reachable only under 250, or with a radius of 50 |
| `PT_DM02_board` (and `_r2`) | 58-60: `goto 1928 -237 70 .. sprint keep` / `goto 1991 -301 40 .. keep` / `goto 2023 -252 26 6000 keep` | the foot of the upper escalator: 63 away, 63 degrees off, radius 26, entered from a sprint | 16 inside at 400; reachable under 300 or with a radius of 50 |

Over all 35 routes the same test finds 13 such way points: the staircase landing (-1822, -1179) in **all seven**
Retomoto routes (so `--bot N` does not get round it) and the escalator foot (2022, -252) in four of the seven
Late Night Opening routes.

A replay of the rig's own steering law (`steer2.py`: heading rate 5 x the error, at most 306 degrees/s, 0.3 s
to walking speed from a stand, no collision) also circles, without ever reaching: `PT_DM01_board` line 72
(`goto 6456 22101 25`, 54 from the door before it, 61 degrees), `PT_DM06_board` line 46 (`goto 5514 4783 40`
right after the first way point, from some START places), `PT_DM09_*` line 78 (`goto 4731 182 20`: 35 BEHIND
him after the table stack - the rig cannot turn on the spot, `face` only works while walking).

PREDICTED, not seen: in the game the walls of a landing will stop the circle and the stuck step will push him
about. But by the worker's own rule ('a NOT reached on a leg before the stage that is looked at proves
nothing') a run that loses script 103 says nothing about the join, and `PT_DM09_join` is the run proposed
first.

Fix (in `Route.finish()` / `align()`; my two scripts can be the check):
- with rho = speed / 5.34: when the next target is inside the unreachable disc of the point where the goto
  before ends, either make the way point before it a stop and raise the target's radius to rho - d + 10, or
  drop the short corner (two way points nearer than about 120 with a turn over 45 degrees are one place for
  this rig);
- never let `0.45 x leg` take a radius under about 50 for a way point reached in motion;
- after a stop, a target behind him (over 120 degrees) nearer than 150 needs a radius of 75 or a way point to
  run out to first;
- print the result of both tests in `route` (as RISKY lines) so that the next map is checked too.

### 4.2 SHOULD - the mesh check walks lines the rig never walks

Every leg is traced from way point to way point. A goto is 'reached' its radius BEFORE the way point and the
next one starts from there. Traced from that place (`indep2.py`), **152 of the 1,753 turns of the 35 routes
leave the mesh by the tool's own `trace()`** (150 by my sampler); for bot 2: 20 of 253 - Late Night Opening 6
(way point 37 -> 38: 142 units off the mesh, 29 -> 30: 92), Withdrawal 7 (the switchback stairs, way points
15 -> 20: 48 .. 68 each), Retomoto 5, Hot Coffee 1, the park 1. `re/playtest.md` 1.1 knows the effect ('cuts
the corner by radius x sin(turn)') and answers it for doors only; a corner gets radius 70 and stands 60 from
the mesh's corner. Momentum works the other way (he swings wide), so the true path lies between the two; neither
is checked. '0 legs off the mesh' is therefore a statement about the plan, not about the walk. Fix: trace the
chord in `finish()` and shrink the radius (not below 4.1's floor) or flag the turn.

### 4.3 SHOULD - boarding with today's rig is timed blind over up to 49 m; use the `rig2` scripts only

`board_van()` without `--rig2` steps to the rear doors a fixed time after the script's `call` point. The report
names one way this fails (a bot called the van first). The second is not named: the wait is counted from when
the SCRIPT arrives beside the van, on the estimate that the walk from the call point took its nominal time
(Withdrawal: five legs, 49 m, 'about 11 s'; then `wait 27291`). The window is about 1.4 s early to 2.5 s late.
Two seconds faster than nominal and he stands at the rear doors' place while the van is still driving over it
(the box is 337 behind the origin: the body covers that place until the last half second); a stuck step or one
`NOT reached` (6 .. 13 s) and he is late on every visit, because all three waits hang on the same clock. VAN5
(10-09) already failed to board by script. With the patch built, run `rig2\PT_*_board_r2.ini` and treat the
others as not for boarding. In `rig2`: a `waitvan 3` that times out still walks him to the doors - let that
step be skipped, or make the timeout fail the script for boarding runs; `waitvan` could also ask for 3 s left
on the timer it already reads.

### 4.4 SHOULD - the fire button at the glass doors is on by default; it can hit the crew and it hides the answer

`PT_DM02_board` holds the fire button over the last 2.5 m before each of four doorways, the first one 195 from
the first way point: the START floor's only door, through which the seven AI heisters leave at the same time.
You -> crew is 1.0 under Risk=2 and the tuning has a retaliation limit ([R+0x18], klbot.c); a hit on a heister
can turn the round into another one. Neither doc names this. And a run that fires cannot say whether an intact
pane stops a walker, which is the open question. Make `--no-shoot` the default (or the first run), fire only in
a second run if the first one sticks.

### 4.5 SHOULD - the expect files contradict themselves in three places

- `PT_DM09_*` lines 56 and 71 (`goto 4750 -220 40 1200`, the push at a table stack off the mesh) are built to
  end by their timeout: the log will say `NOT reached`. The expect file's rule calls any `NOT reached` before
  the stage in question a void run. Say in the expect file that these two are expected (or give them a radius
  that the mesh's edge already meets).
- All eight `rig2` expect files ask for `players: the moving one is #k`; the patched rig writes `players: the
  local one is #k at ... (the game's own pointer, slot N)` and never the other line while the pointer reads.
  Their 'no moving player found' rule cannot happen either (the goto times out instead).
- `RESULT PASS` is reached whether or not anything worked (every goto may time out and the script still
  passes). The expect files do say which lines count; `live.py`'s summary should not be read for these runs.

### 4.6 NOTES

- `selftest` only walks the START row's mesh part: Retomoto's street half is not in it (the routes there pass
  my own test all the same).
- `PT_DM09_join` takes the join about 94 s after GO; the crew's own start is the room counter or the fall-back
  timer at blast + 75 s = GO + 83 s. The human never shoots, so the seven are most likely moved from the window
  with nothing done in the tower. The street half then runs, but not as a round would. A wait in the boardroom
  before the stairs (an option of the generator) would make the run say more.
- The scripts take `[Bots]` from the tree: Log=1, no BoardAll. The lead's series I ran BoardAll=1 Log=2 -
  compare with care (`--extra "[Bots];BoardAll=1;Log=2"`).
- Worst case (every goto and `waitvan` into its timeout, the menu part at its usual 62 s) is longer than
  `MaxRunMs` for five of the 16 scripts (`PT_DM01 / 02 / 03 / 09_board_r2`, `PT_DM09_board`; the largest:
  `PT_DM09_board_r2`, 1,241 s against 981 s): such a run ends by the clock, not by `pass`.
- The human waits inside the bots' `AllyEscapeBox` on Hot Coffee ((6194, 20463) in (6004 +- 350, 20211 +- 350)):
  seven bodies may stand between him and the doors.
- One START place of the park is 100 outside the mesh (the tool says so): one round in eight begins with a leg
  nobody checked.
- `--die`: the route's place has ONE guard with a line on the mesh within 20 m (639 away, of 15 in the level).
  The lead's run F1_T01 (another level, idle player, Risk=2) lived to the end. 'Reliability unknown' is the
  honest word.

## 5. Checks re-run

| check of the report | my run | same? |
|---|---|---|
| `selftest` on the five builds: 4,985 / 7,079 / 5,454 / 5,402 / 5,399 legs, 0 leave the mesh, PASS x5 (51 pairs without a way on Withdrawal) | the same command | identical |
| 35 routes (7 bots x 5 builds): 30 .. 83 way points, 0 legs off the mesh, exit 0 | the same command, 35 times | identical (30 .. 83; 0; exit 0) |
| first way point reached from every START place | my sampler from all 8 places, five maps | holds |
| tree copies and build folders give the same route | diff of the five bot-2 prints | identical (the archives themselves differ by hash on four maps: the tree's are the adopted copies) |
| the 16 inis and their route / expect files | `set` and `set --rig2` run again into a scratch folder | all 48 files identical |
| the inis against `kla_script_load` | my own `inicheck.py`: numbering, commands, key names, goto fields, 199 / 79 characters, `keep` followed by a goto, no section twice, CRLF, labels, nothing left held | no problem in any of the 16 |
| ini keys exist | klbalance.c 152, 427-444 (`Ramp`, `CopToYou`, `CrewToYou` 0 .. 20, `PlayerHealth` 0.05 .. 10), klclimb.c 1033-1054 (`Enable`, `Key`, `Log`; 15 .. 70 from the face, 150 a second, 400 ms), kl_autotest's arguments | all exist with the meaning used |
| the other `--until` forms and `--die` | `enter / loot / exit / van` on five builds, `wall` on `z_climb\M03`, `--die` on four | all run; `wall` exits 1 by design |
| the patch applies / compiles | see section 1 | already applied; a TEST DLL built from it exists |

**The independent mesh test** (the main claim): 1,809 legs of the 35 routes sampled every 2 units with a ray-
crossing point-in-polygon test and a height from a corner-0 fan, no neighbour walk, the height within 70 of the
last sample's: **0 leave the mesh.** (A first version with a cruder height filter failed 6 stair legs; looked at
one by one they are on the mesh.) So `trace()`'s three rings of neighbours hop no gap.

## 6. Can the live checks tell success from failure?

Mostly yes: the lines the expect files quote exist as quoted (klbot.c 392-393 `bots: record 0 (you): heist stage
a -> b` and the status line, kljoin.c 242 / 254, klescort.c 396-398 at Log=1 every 5 s, klauto.c 1389 / 1393),
and each stage has a line that only success writes (`join: player 0 entered box`, `bots: record 0 (you):
aboard`, `status6`). A boarding that fails can be told apart by cause: the last `bots:` line gives the van's
state at `goto (<box>) reached`, `pos at-the-rear-doors-N` gives his place.

Where they cannot, as written:
- a run with a `NOT reached` by design (4.5) or by the turning circle (4.1) is void by the files' own rule -
  after the fix of 4.1 this is the criterion to keep;
- the glass question, while the script fires (4.4);
- `--die` when nobody shoots him (said by the worker);
- the `rig2` twins' item 6 (4.5).

Order I would run, once 4.1 is in: `PT_DM09_join_r2` -> `PT_DM03_board_r2` -> `PT_DM01_board_r2` ->
`PT_DM02_board_r2 --no-shoot` -> the rest. Without the fix, the Withdrawal scripts are the only ones of the set
with no way point that my tests call unreachable (`PT_DM03_board`, `PT_DM03_die`: neither test; `PT_DM03_wall`:
the exact test only, the replay was not run on it) - so `PT_DM03_board_r2` is the one to run first as it is.

## 7. What track H did about each defect (the finishing pass, 2026-10-11; written by the track, not by the reviewer)

Offline again: no game started, nothing written in a game folder, nothing committed; only
`tools/kl_playtest.py`, `re/playtest.md`, this section and the files under `<work>\research\playtest\` were
written. The reviewer's scripts in `rev_h\` were run as they are, on the new routes. Between the review and
the end of this pass the lead ran six scripts of the tool in the game (`re/playtest.md` 8): five of the FIRST
version (PT_DM03_die_r2, K1 / K2 / K2b / K2c_DM03_wall) and, at 10:13, an early copy of the NEW Withdrawal
script (PB_DM03_board_hp), which walked the whole route and boarded. What their logs show is used below and
marked live.

| defect (where) | fixed or refuted | what was done, and the evidence |
|---|---|---|
| **4.1 MUST** `Route.finish()` / `align()` / `Script.walk()`; PT_DM09_join / _board line 103, PT_DM02_board line 60 | **FIXED** | New in the tool: `steer()` (the rig's law as a model: 5 x the error, at most 306 degrees a second, W down), `cannot_turn_in()` (the review's exact test) and `Route.drive()`: every goto is driven from where the one before left him, from every START place, under 306 and under 230 degrees a second; a goto that is circled, or whose line leaves the mesh, makes the way point before it a STOP (walked to within 40, W up, `wait 600`, then from a stand). Radii in motion: never under 60; `0.45 x leg` is gone. Printed in `route` as RIG lines and lists; `route` exits 1 when the model does not reach a goto. **Result: the reviewer's `orbit.py` over 7 bots x 6 routes: 0 unreachable in motion (was 13); the tool's own stricter test: 0 on all 35 routes + 7 wall routes.** The two named way points: Retomoto's lower landing (-1823, -1179) has radius 70 after a stop at the door before it (script 115 / 118 of the new PT_DM09_join); the escalator foot (2023, -252) has radius 70 too (script 63 of PT_DM02_board; the model reaches both at once under both rates, and the chords from there stay on the mesh). **The model is held against the game** (`kl_playtest.py rigfit`): 794 gotos reached in motion in fourteen logged walks - it reaches every one, time within -90 .. +48 ms for 8 in 10, place 9 units off in the median; under 230 it misses 7 the game reached, so 230 is a pessimistic second rate. **And live**: an early copy of the new Withdrawal script (the lead's run PB_DM03_board_hp, 10:13) reached 50 of 53 gotos with these stops and radii and boarded the van; its two failures were places where something the mesh does not know stands (below) |
| 4.1, third point ('after a stop, a target behind him nearer than 150 needs a radius of 75 or a run-out way point'; 'the rig cannot turn on the spot') | **REFUTED in its premise, applied all the same** | From a stand the game turns him BEFORE he walks: in the five clean from-stand gotos of the logs (ESC1-3 / RN13 script 73: 130 .. 143 away, 137 .. 144 degrees off, radius 60, reached in 1.3 s each; VAN5 202: 118 degrees) his place at 'reached' is 1 .. 5 units from where a turn on the spot and a straight walk put it and 34 .. 78 from where the review's arc does (`rigfit`, part 2). All 31 live gotos from a stand with the target 45 degrees or more off were reached - 12 of them in the run of the new script itself (targets 46 .. 130 degrees off, radius 30 .. 70, 0.4 .. 1.7 s each). So a stop is the cure, not a risk. And a goto without `keep` followed at once by a goto is NOT a stop (28 live gotos: 1.01 of their own speed in the median, 0.76 at the least; four of them the first scripts' own 'stop'): every stop now has its `wait`. The rule is applied where a chord allows: radius 60 (the live value), then 75 / 90 while the arc reading still circles. What is left - 5 targets with radius 25 because the next chord needs it - is printed 'BEHIND HIM AFTER A STOP', and the arc reading of every start from a stand is printed as 'IF HE DOES NOT TURN ON THE SPOT' (73 notes on the 35 routes). **`steer2.py` on the new routes: 3 'NOT reached', all three from a stand and all the same place** - Late Night Opening's corner (-1850, 2711) behind the cash drawer, radius 25, 115 from where he stands, bots 2, 5, 7 (the tool marks it 'BEHIND HIM' in five routes); in the set it is script line 106 of PT_DM02_board, named in its expect file. A further test was added for a stand: the goto must also be reached when he starts to walk 15 degrees off its line (no goto of the 42 routes fails it) |
| **4.2 SHOULD** `finish()` / `trace()`; 're/playtest.md 0.2, 4' | **FIXED** | The steered line (both rates) and three chords are followed over the mesh in `drive()`: from where the model has him, from where W went up, and the review's own chord judged by `trace()`. A failure is cured by a stop at 40, then at 25. **`indep2.py`: 33 of 1,746 chords off the mesh by the tool's trace (was 152 of 1,753), every one of them from a stop of radius 25; 0 of 1,803 legs fail the independent sampler.** The tool prints those turns as RISKY (37 of 1,845 way points on the 35 routes: a chord off by less than 2 units at 15 of them, by 2 .. 17 at the rest; seven are the bank's west garage door, where the mesh is 2 wide). NOT taken further on purpose: a stop at radius 12 was tried and takes about 21 of them off the list - by making a goto of radius 12 of each, and a way point he misses is one he circles; 25 is the least radius seen reached live (24 / 25), so it is the floor and the turns stay flagged, as the review's own fix allows ('shrink the radius ... or flag the turn'). `re/playtest.md` now says what '0 legs off the mesh' is a statement about |
| **4.3 SHOULD** `Script.board_van()` without `--rig2` | **FIXED** | A script for the unpatched rig does not board a key-framed van: it stands beside the doors and watches (`--blind-board` keeps the timed form, marked). rig2: `waitvan 3 420000` - longer than the round - so the step to the doors is taken only when the van is SEEN to stand; when none comes the round's end (`onwin`) ends the script: no step on a timeout. Visits 2 and 3: `waitvan 1`, then `waitvan 3`. The walker's travel-time error is named in the doc (3) |
| **4.4 SHOULD** `Script.walk()` glass branch; PT_DM02_board | **FIXED** | No shot by default; `--shoot` and a second script `PT_DM02_shoot` for the run after one that sticks at a door. The friendly-fire risk is named (`re/playtest.md` 4 B, the tool's usage text); the expect file says what 'reached' / 'stuck' at each glass door answers |
| **4.5 SHOULD** the expect files | **FIXED** | (1) the two push gotos (script 58 and 77 of PT_DM09_*) are named 'EXPECTED, by design' at their place and in the rule at the end, and are in `.plan.json` (`by_design`); (2) the rig2 files quote `players: the local one is #k ... (the game's own pointer, slot N)` (live now) and their 'he could not move yet' rule is the one that can happen; (3) every expect file says that RESULT PASS proves nothing, and **`kl_playtest.py judge <ini> <log>`** reads a run against its script (run on the six live logs: it reports the lost first goto of the five first-version runs, 'HE DIED 25.6 .. 29.8 s after 0x19' in three, the crash that ended K2c, and for PB every stage FOUND up to 'aboard' and 'escaped' with the two gotos that were not reached) |
| note: who applied the patch | answered | Not this track. The lead: commit 1f8b617 (09:14), hook test_pt1. `re/playtest.md` 6 is rewritten; P1 and P3 are seen live, P2 not yet |
| note: box sizes 'loose' | done | worded so in the doc (2) and at `BOX_SHARE` |
| note: `floor()`, `selftest` | done | docstrings say what `floor()` is inside a polygon that is not flat; `selftest` walks every mesh part a route uses (Retomoto's street: 6,510 legs, 0 off) and holds `steer()` against the exact test (5,496 gotos: none more than 6 inside the circle is reached) |
| note: the pace of PT_DM09_join | done | the later start (below) puts him at the join about 0x19 + 100 s, behind the crew's own 91.5 s; `--join-after S` holds him longer |
| note: `[Bots]`, `MaxRunMs`, AllyEscapeBox, the park's START place, GO_MS comment | done | `--extra "[Bots];BoardAll=1;Log=2"` named in the doc; `MaxRunMs` / `AutoExit` are set past the round's own end (no script outlasts the round: 764 s at the least), the reviewer's worst-case sum counts timeouts the score page cuts short; the route print notes the AllyEscapeBox; the START place note stands; the constant is gone |
| note: `--die` | answered by a run | live once (PT_DM03_die_r2): dead 19.1 s after 0x19, on the way, a fed 5 s later. One run; still 'not known' elsewhere |

**Found in this pass, not in the review** (each from a log; `re/playtest.md` 1.2, 1.4, 8):

1. **The human cannot move for 10.1 .. 10.4 s after session state 0x19** (seven runs). The first way point of
   all four live runs of the first scripts was lost to it (9.5 s of 'goto is stuck', `NOT reached`). The
   scripts now wait 11.0 s after 0x19 before the first goto.
2. **Retomoto's blast is 16.5 s after 0x19**, not 8.1 s (the first version subtracted 8.4 s): the bots take
   stage 1 18.4 .. 18.5 s after 0x19 in runs R7c and I5. The first version would have walked him at the intact
   window 6 s before it goes. Now: 18.5 s after 0x19.
3. **The 'bullet-proof' human died**: dead on the bank's stairs in three live runs of three (K1, K2, K2b) with
   `CopToYou=0.02 CrewToYou=0.02`: steps of 151.2, 151.2, 30.2 that the factors did not scale. The scripts now
   add `PlayerHealth=10 RegenDelay=0.5 RegenTime=0.5`; with 5,500 of health he lived through the bank in the two
   runs that had it (K2c, PB). What the unscaled steps are is the lead's question (`klbalance.c`).
4. **Two things the mesh does not know on Withdrawal**, both from PB (and K2c): the bots' loot place stands
   among the money boxes (a goto with radius 40 stuck 54 .. 73 from it: a loot place followed by money places
   now has radius 110), and something stands at the bots' way place (-1237, -1504) in the yard (the goto stuck
   115 .. 140 short of it in both runs: the place is in a `BLOCKED` table now and the route goes up the yard's
   west side). Places like these can only be found by running a map; the four other maps have not been run.

**Checks, all run again on the final tool** (offline): `selftest` x5 PASS (4,985 / 7,079 / 5,454 / 5,402 / 5,399
legs as before, + 6,510 on Retomoto's street, 0 off the mesh); 35 routes through `route`: exit 0, 29 .. 83 way
points, 0 legs off the mesh, first way point from 8 of 8 START places, 0 gotos the model does not reach; the
tree's copies give the same route prints as the five build folders; every `--until` form and `--die` run
(`wall` exits 1 by design); `set` and `set --rig2`: 18 inis, the reviewer's `inicheck.py` 18 of 18 'no problem
found', the first worker's `chk_ini.py` PASS; `orbit.py`, `steer2.py`, `indep2.py` as in the table; `rigfit` on
the fourteen logged walks and `judge` on the six live logs of the tool's scripts. **Not run by this track:
anything in the game.**
