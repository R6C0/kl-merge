# A scripted player for the unattended runs: the rig's `goto`, the maps' own routes

2026-10-11, track H; revised the same day after its review (`re/playtest_review.md`; what was done about each
defect is at that file's end and in section 9 here). **This track's own work is OFFLINE: it started no game,
wrote nothing into a game folder and committed nothing.** Files: `tools/kl_playtest.py`, this file, and the
scripts in `<work>\research\playtest\` (`<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead
Men\KL_PortTools`). The lead has run six scripts of this tool in the game (section 8): five of the FIRST
version, and at 10:13 an early copy of THIS version's Withdrawal script - **it walked the whole route, looted
$550,000, boarded the van and escaped.** What those runs showed is used here. The scripts as they are written
now (that run's two failed gotos repaired) have not run; the four other maps have not been walked at all.

Words: **read** = seen in `klhook/klauto.c` or another hook source at the place named; **measured** = counted
on logs (`<work>\build\klhook\live\`) or on the build files, with what was counted; **live** = seen in a log of
a run in the game (the lead's or an earlier one); **model** = `kl_playtest.steer()`, the rig's steering law run
offline; **ASSUMED / GUESS**; **not run**.

## 0. Short answers

1. **`goto` is straight-line steering by keys and mouse**, nothing more: W held, the mouse turned by the bearing
   error, 'reached' = within a radius *in the plan*. No path finding, no sense of a wall, a door, a floor, the
   round, the vehicle or the player's death. Section 1.
2. **Because W is down while he turns, he cannot turn tighter than a circle of 75 (walk) or 110 (sprint).** A
   way point inside that circle is circled until the timeout. The first version of the routes ignored this (the
   review's must). Now every goto of a route is driven by a model of the rig's steering from where the goto
   before left him, and a way point the model cannot do in motion is made a STOP. Sections 1.4 and 2.
3. **A full route to the vehicle exists on all five maps of the tab for every one of the seven bots' plans (35
   routes): no leg leaves the navigation mesh, the first way point is reached by a straight line on the mesh
   from every START place, and the model reaches every goto of all 35** under the rig's turn rate and under one
   a quarter lower. What stays risky is printed per way point and listed in section 4.
4. **Eighteen scripts are written** (section 5): nine for the hook that has the rig patch (`rig2\`), the same
   nine for an unpatched hook (those do not board). Each has a `.route.txt`, an `.expect.txt` and a
   `.plan.json`; `kl_playtest.py judge <ini> <log>` reads a run's log against its script.
5. **What the live runs taught** (section 8): the human cannot move for 10.1 .. 10.4 s after session state 0x19
   (the first way point of all five runs of the first scripts was lost); a `goto` without `keep` is no stop; the
   patch's `waitstate`, `waitvan` and local-player pointer all work; **the 'bullet-proof' human was dead on the
   bank's stairs in three runs of three** and lives with ten times the health (two runs of two); and **with the
   wait, the stops and the radii of this version 50 of 53 gotos were reached on Withdrawal and he boarded** -
   the two that were not reached stand at things the mesh does not know (money boxes; something in the yard),
   and both are repaired here.

## 1. The rig (`klhook/klauto.c`, TEST build only; all read)

### 1.1 `goto <x> <z> [radius 120] [timeout ms 20000] [sprint] [keep]`

| what | how (klauto.c `C_GOTO`, `kla_script_step`) |
|---|---|
| who is steered | with the patch (section 6): the game's own local player. Without it: of the ZFFPlayer objects found by their vtable, the one whose place has travelled farthest since the scan, once it has moved 30 units; until then the goto only holds W, and after 6 s without anybody moving: `no moving player found ... step skipped` |
| forward | W (DIK 0x11) down for the whole goto; `sprint` = LSHIFT (0x2a) down too. One key event per keyboard poll |
| turning | the heading = minus the unit vector at player +0xc14 (the BODY's heading); error = bearing to (x, z) minus heading; mouse x rate = error / 0.17 x 5 counts a second, clamped to 1800 = **306 degrees a second at most, a time constant of 0.2 s below that**. The mouse turns the camera and W walks where the camera looks |
| reached | distance **in the plan** (x and z of player +0x460) <= radius. The height is not looked at: a way point one floor above or below counts when he passes over or under it |
| timeout | `goto (x, z) NOT reached in N ms: at (...) heading h, d away, bearing error e` is logged **and the script goes on with the next line from wherever he stands** |
| stuck | no 40 units of way in 1.5 s: a side step (A or D in turn, 0.7 s), every third time a 120 ms tap on C ('Get Up' when he is down - and 'take cover' when he is not). It never gives up before the timeout. **Circling a way point is not 'stuck': he keeps moving** |
| `keep` | W (and LSHIFT) stay down when the goto ends: a following goto goes on without a stop. `pos` and `log` between two gotos cost no frame. **A `wait` after a `keep` walks him on blind** |
| the end without `keep` | LSHIFT and W are let go, one event a poll. **That alone is NOT a stop** (1.4): when a goto follows at once, W is down again two polls later and he goes on as fast as before. He stands only when a `wait` follows: 20 units farther on |

So, at a **wall**: he walks into it, side-steps, taps C, until the timeout. **Stairs / an escalator**: nothing
special is done - the line is straight in the plan and the engine carries him up or down; what can go wrong is
'reached' on the wrong floor (above). **A door**: nothing - no key is pressed; a shut door is a wall.
**A corner**: the turn starts `radius` before the way point and the line is cut by `radius x sin(turn)`; his
momentum then carries him wide on the far side. **A way point close behind a turn**: see 1.4.

Other commands a route uses: `pos <label>` (`pos label: me #k (x, y, z) heading h`), `log`, `wait`,
`down / up / tap <KEY>`, `mdown 0 / mup 0` (the fire button through the scripted mouse), `onwin <window>
<label>` (jump when the score page comes up), `peek`, `pass`, and with the patch `waitstate` / `waitvan`.
`face x z` turns only while he walks. A script has at most 640 lines; a `log` / `pos` text is cut at 79
characters.

### 1.2 What the rig cannot do

- No path finding and no obstacle sense (above). It does not know the mesh, a car, a person, a pane of glass.
- **The round's clock is not the moment he can move.** `waitload` ends when the level is loaded; session state
  0x19 comes 20.5 .. 22.1 s later (measured: the 67 scripted Arcade runs of late 10-09 .. 10-11 that have both
  lines; `waitstate 0x19` of the patch waits for it). **And for another 10.1 .. 10.4 s the human stands on his
  START place and nothing moves him** (live, seven runs: in N0, N0b and VAN5 the rig saw his first 30 units of
  way 10.16 / 10.17 / 10.17 s after 0x19; in the four runs of the first scripts he left the START place 10.25 ..
  10.4 s after it, and in K1 a `pos` line has him still there at 10.32). It is the round's own countdown. A
  goto given in that time holds W, counts as 'stuck', and is lost with its timeout: so it went with the first
  way point of all five runs of the first scripts. The scripts now wait 11.0 s after 0x19 (`FREE_S` 10.4 + 0.6);
  live, PB_DM03_board_hp: the first goto started 11.0 s after 0x19 and was reached.
- Retomoto's window: the level's blast timer (`blast_timer` 16.5 in `bots.json`) runs from 0x19, not from 8.4 s
  before it as the first version assumed: the AI heisters, who start 1.0 s after the blast and stand at the
  window, take stage 1 18.4 .. 18.5 s after 0x19 (live, runs R7c and I5), and Kane's 'NOW' is said 16.5 s after
  it. The scripts wait on the balcony until 18.5 s after 0x19.
- **It cannot see the vehicle** without the patch (`waitvan`), nor whether he is alive, down or aboard.
- Without the patch the 'moving one' is fixed by who moved first: after a death and a return as police the
  local player is another ZFFPlayer. With the patch the pointer follows (live: slot 0 -> slot 8).
- RSHIFT cannot be scripted (klauto.c's own note); `GetAsyncKeyState` does not see a scripted key (klclimb.c's
  `Key=` must stay 0 in a scripted run).

### 1.3 The keys the actions need (kl2.exe's default binding text, klauto.c's note; live where said)

| action | key | evidence |
|---|---|---|
| use / pick up / heal | E | live: a cash drawer and two money boxes of the bank paid after E was held 3.5 .. 5 s inside the object's trigger (runs RN7, ESC1 - ESC3); 1.5 s paid nothing (RN8, RN9) |
| board the vehicle | E inside the boarding box while the vehicle waits | live, ESC3: 'tap E, then E for 2 s' -> 'You jumped into the getaway car'. Which of the two did it was not separated. The box is the node with `PlayerAction` 'EnterVehicle' |
| sprint | LSHIFT (SPACE too) | live: 585 units a second (median of the sprint legs of ESC3 556, N0b 586, VAN5 589, J2 584; 596 .. 601 in today's runs); a walk about 400 (ESC3, five legs: 386) |
| cover, 'Get Up' | C | the goto's stuck step taps it |
| fire / aim | mouse 0 / 1 (`mdown 0`) | the scripted button was pressed in runs RN7 - RN12; **that the gun fired was never recorded** |
| reload, weapon | R, Q | not used |

### 1.4 The steering as a model, held against the game (`steer()`, `python tools\kl_playtest.py rigfit <runs>`)

**The turning circle.** W is down while the mouse turns, so the tightest circle he can walk is speed / turn
rate: **75 at a walk, 110 at a sprint**. A target inside that circle on its side, by more than its own radius,
is never 'reached': the law keeps the turn at its limit and he circles until the timeout.
`cannot_turn_in()` is that test exactly (the BEST turn he could make). The rig's law is not the best turn - the
rate falls with the error - so it circles more than the exact test says, never less: of 5,496 random gotos in
the open the exact test calls 176 unreachable, the model reaches none of those that lie more than 6 inside the
circle (`selftest`), and circles 136 more. So the review's exact test is the lower bound and the model the
stricter of the two; the routes are judged by the model.

**The model.** `steer()`: every 1/60 s the heading turns by 5 x the bearing error, at most 306 degrees a second,
and he moves at 585 or 400 along it; a sprint decays to a walk by 300 units/s^2 (live, ESC3 script 40), to
speed he is at once (live, four runs' script 46: 436 .. 447 units in 0.70 .. 0.72 s from a stand).
`rigfit` replays it against the logs of every scripted walk that ran (ESC1-3, RN13, N0, N0b, J2, VAN5 and the
six runs of this tool's scripts): each goto that was reached in motion is started from the place and heading
the log gives for the goto before it.

| measured on 794 gotos reached in motion (radius 25 .. 200; 215 with the target 45 degrees or more off) | the rig's rate, 306 | 230 ('wide') | 400 |
|---|---|---|---|
| gotos the model does not reach although the game did | 0 | 7 | 0 |
| time, model minus log: median; 8 in 10 within | +13 ms; -90 .. +48 | +15; -74 .. +56 | +12; -98 .. +45 |
| place of 'reached', model against log: median; 9 in 10 within; median of the 215 turns | 9; 72; 52 | 9; 80; 55 | 9; 67; 50 |

So the law as read predicts the game to a few hundredths of a second and, on turns, to about half a metre; the
game does not turn slower than 230 degrees a second (it would have missed gotos it reached); whether the clamp
is 306 or higher the logs cannot say. `kl_playtest` asks every goto in motion to be reached under 306 AND
under 230 (`TURN_WIDE`: the circle a third wider, 100 / 146).

**A goto without `keep` is not a stop.** 28 gotos in those logs came right after a goto without `keep`, no
wait between: his speed over the whole goto was 1.01 of the goto's own speed in the median and 0.76 at the
least. Four of the 28 are the first scripts' own 'stop in front of a door' (live, K1 / K2 / K2b / K2c script
56 -> 57: 304 .. 313 units a second at a walk). **He stands only when a `wait` follows**: 19 .. 20 units farther on,
within 0.75 s (live: ESC3 scripts 40 and 67 from a walk, VAN5 198 from a sprint). The scripts now write
`wait 600` after every stop.

**From a stand he turns BEFORE he walks** (this is where the review's replay and the game part: the review
reads a start from a stand as an arc from his old heading). 31 gotos of the logs started from a stand with the
target 45 degrees or more off - **every one was reached**, 12 of them in the run of this version's own script
(PB_DM03_board_hp: stops with `wait 600`, then targets 46 .. 130 degrees off, radius 30 .. 70, each reached in
0.4 .. 1.7 s). In the five clean ones (his place taken from a `pos` line of the wait, nothing in his way) the
place of 'reached' is where a turn on the spot and a straight walk put it, not where an arc does:

| run, script | target | log: time, place of 'reached', heading | he turns first: place off | an arc at 306, 0.3 s to speed: place off |
|---|---|---|---|---|
| ESC3 73 | 142 away, 143 degrees off, radius 60, walk | 1313 ms, (596, -6210), -81 | 1 | 78 |
| ESC1 73 | 143 away, 144 degrees | 1329 ms | 3 | 75 |
| ESC2 73 | 143 away, 142 degrees | 1344 ms | 4 | 76 |
| RN13 73 | 130 away, 137 degrees | 1344 ms | 2 | 78 |
| VAN5 202 | 366 away, 117 degrees, radius 70, walk | 1313 ms, (-1887, 8955), 133 | 5 | 34 |

(Of the other 26: three U-turns of 108 .. 167 degrees over 11 m at a sprint, both readings within 5 .. 17;
three of 55 .. 59 degrees, 20 against 30; six where he had been stuck on a prop or the hook had just moved
him; and the 14 of K2c / PB, whose place of standing is only known as 'reached' + 20: over all 31 the turn-first
reading is 17 off in the median, the arc 37.) The turn costs time: about 0.6 s for 118 degrees, 1.1 s for 140.
`kl_playtest` therefore takes a start
from a stand as a straight line, and prints the arc reading as a note ('IF HE DOES NOT TURN ON THE SPOT'), never
as a pass.

### 1.5 How the player boards (read in the builds with `kl_fa_bots.stations` / `van_drives`)

- Hot Coffee, Late Night Opening, Withdrawal, Retomoto: stock F07's key-framed van. The boarding box
  (`...\V_Van_00\BoardingTrigger`, half sizes 95 x 135 x 80, `PlayerAction` 'EnterVehicle') is a child of the van,
  337 behind its origin: **it rides with the van and stands at its rear doors**, on the side the van came from.
  The van's nose carries a `KillBox` (168 in front, 90 to either side). In the file the box lies at the van's
  waiting place; where it stands at the stop is `van_drives()['board']`.
- A Walk in the Park: a helicopter; `Triggers!BoardingTrigger_Heli` stands still at (-1686, 132, -6541).
- The AI heisters do not use that box: they are taken aboard from their `AllyEscapeBox` beside the stop
  (`bots.txt`). The human has to use the box.

## 2. The route rule (`tools/kl_playtest.py`, class `Route`; its docstring is the spec)

1. **Guide points** are the AI heister's own planned places: `bots.json` `plan.bots[N].places`, one per station
   (Retomoto also `plan.rt.street`). They are on the mesh by construction and in the order the squad's chain
   walks them. Must-pass: loot stops, the level exit place, the gate (the bank's drop), the rally place. A stage
   box's place (enter / exit) is must-pass unless it is a detour of more than 150 and the way to the next place
   crosses the box anyway. 'way' places only say which corridor the bots take.
2. **Between two guide points**: the polygon corridor of `kl_fa_bots.Nav.dist_map`, then the shortest line
   inside that corridor by the funnel method, every shared edge drawn in by 60 from both ends. A shared edge
   shorter than 150 near the mesh's border is a **door**: its middle is a way point.
3. **Thinning**: a 'way' place, a corner or a door goes when the straight line past it stays on the mesh and
   keeps 50 from every border edge - or is no nearer to one than that way point and the two legs it replaces.
4. **Doors along their axis**: where the line turns by more than 30 degrees at a door, a way point goes on the
   door's axis 160 / 120 / 90 in front of it (he **stops** there - a real stop, with a wait) and / or behind
   it. Where none fits, the door itself is a stop. When such a place comes right after the first way point and
   every START place has a straight line to it, it IS the first way point (the park: the first one lay 98
   beyond it).
5. **Stair / escalator foot and top**: a way point where a leg goes onto a slope that rises or falls 60 or more
   and where it leaves it.
6. **Nothing farther apart than 1500** (a timeout must tell 'blocked' from 'slow' quickly; the longest leg the
   earlier walks reached is 1924).
7. **The start**: the human gets one of the level's START points, another each run, looking along that point's
   own +Z (live: `pos spawn ... heading 15` on the point whose +Z is 15). The first way point is one that a
   straight line on the mesh reaches from all of them.
8. **Every leg is walked on the mesh** in steps of 12 (`trace()`) and printed: `OFF THE MESH`, `RISKY` (the line
   nearer than 30 to a border edge), `TIGHT` (the way point itself nearer than 20).
9. **What the rig makes of it** (`Route.drive()`; new - the review's must and its first should). The gotos are
   driven in order by `steer()`, from every START place, each from where the one before left him (place,
   heading, speed):
   - **reach**: under 306 and under 230 degrees a second the goto must be reached without circling (not more
     than 300 degrees of turning in all); `cannot_turn_in()` is printed where it bites;
   - **the line he really walks**: the steered line is followed over the mesh (any sample off it = fail; under
     the wide rate one more than 25 outside), and so are three straight chords to the next way point - from
     where the model has him, from where W went up should he not roll on, and the review's chord (the goto's
     radius before the way point, taken back along the leg's own line; judged by `trace()` as the review did);
   - **the cure**: a goto that fails makes the way point BEFORE it a **stop** - he comes within 40 of it, W
     is let go, the script waits 600 ms, and the next goto starts from a stand, where he turns before he walks.
     When a chord from there still leaves the mesh the stop is made at 25 - the least radius any goto gets (24 /
     25 were reached live; a way point he misses is one he circles);
   - **from a stand** the goto must also be reached when he starts to walk 15 degrees off its line;
   - **radii**: a way point passed in motion keeps 110 (open) / 70 (a turn of 45 degrees, a door, near the
     border) / 60 (a must-pass place) and **never under 60**; the first version's 'never more than 0.45 of the
     leg' (which gave 20 .. 35 on short legs) is gone. A stop has 40, or what its place needs (30 at a money
     object, 20 at the wall's foot);
   - **behind him after a stop**: a target nearer than 150 and more than 120 degrees off gets radius 60 (the
     value seen live), then 75 / 90 while the arc reading still circles it - unless the next chord needs it small;
   - the **stage boxes** are those the steered lines enter from every START place, not those the straight legs
     cross;
   - what no stop cures stays in the print with the way point: `NOT REACHED BY THE MODEL`, `STEERED LINE OFF
     THE MESH`, `THE REVIEW'S CHORD IS OFF THE MESH`, `BEHIND HIM AFTER A STOP`, `IF HE DOES NOT TURN ON THE
     SPOT`. `route` exits 1 when a leg is off the mesh **or the model does not reach a goto**.

Two things `kl_fa_bots.Nav` could not be used for as it is, both found on the way:

- **Heights.** `Nav.height` fits a plane to three corners. On a polygon that is not flat it is off by
  hundreds: Late Night Opening's two escalators are six-sided polygons (a landing and a ramp) stacked one above
  the other, and a bot's place on the LOWER one, (913, 399, 813), is found on the UPPER one by `Nav.at` (the
  review confirmed it). `kl_playtest.floor()` takes the height from the polygon's fan triangles: exact on every
  edge; inside a polygon that is not flat it is an estimate too (the review: 468 there, a bot's place 399).
- **A trigger box's size values are HALF sizes** - loosely shown. Live, run H0_DM03: bot 1's node was at z -655
  at 01:12:27.447 and its heist stage went 2 -> 3 at 01:12:27.665; `Triggers!ExitTrigger_01` (middle z 460, size
  value 1000) begins at z -540 as half sizes and at -40 as full ones. One instance, and it fits the half-size
  reading to 100 .. 200 units, not better (the review: the van's timer had run 0.4 s already). The routes cross
  the boxes deep.

**What was checked** (all offline; the numbers of the last run are in section 9):
`selftest <build>`: 300 random pairs of places a mesh part, 4,985 .. 7,079 funnel legs walked by `trace()` - none
leaves the mesh on any of the five builds, Retomoto's street part included (6,510 legs); and `steer()` against
`cannot_turn_in()`. `rigfit`: 1.4. Against the logs: the human's place when the round starts is **exactly** one
of the build's START places in all runs looked at; of the bots' logged places 97 % (Hot Coffee), 92 / 94 % (Late
Night Opening), 100 % (Withdrawal), 78 % (the park; the rest within 60) lie on the mesh by `floor()`. The
review's own three test scripts were run on the new routes (section 9).

**What a mesh does not know**: parked or arriving cars, people, props, panes of glass, level bounds. And the
model knows no wall: where the real player touches one he slides or sticks, and the model says neither.

## 3. The vehicle

Measured on the logs (`bots: L1 s19 van <state> <timer>`; the first timer value of each state in eight runs):
it drives in 7.1 .. 7.5 s (state 1 / 2), stands 7.9 .. 8.0 s (3 / 4), leaves 8.4 .. 8.5 s (5), 5.5 .. 6.0 s (7),
then again while somebody stands in a level exit box: **one visit every 29.5 .. 30 s** (the helicopter: every
26 s).

- The van is called when somebody enters a level exit box with the vehicle in state 0. `kl_playtest` puts a way
  point 60 inside the box where the route first enters it (`call`).
- **He waits 230 to the side of the van's axis, level with its rear doors** (100 of body, 60 of a man, 70 more:
  GUESS), inside a level exit box so that the van keeps coming. On Hot Coffee that place lies inside the bots'
  `AllyEscapeBox`: up to seven bodies may stand between him and the doors (the route print says so).
- **`--rig2` (the patched hook): `waitvan 3` before every step to the doors**, with a timeout longer than the
  round (420 s). He steps only when the van is SEEN to stand. When no van comes the script sits there until the
  round's clock ends the round and the score page (`onwin`) takes the script to its end - he is never sent to
  the doors by a timeout. For the second and third visit: `waitvan 1` (the NEXT one drives in), then `waitvan 3`.
  The first visit can be wasted when the van stood already as he arrived (it leaves while he holds E).
- **Without the patch a script does NOT board a key-framed van** (the review's 4.3): it stands beside the doors
  and watches. The first version timed the step from the `call` point by the estimated walk (49 m on
  Withdrawal); 1.4 s early and he stands where the van drives. `--blind-board` still writes that form.
- The helicopter's box stands still: he stands in it and presses E every 3.3 s for 81 s (either rig).

## 4. The five maps (bot 2's places; numbers from the `.route.txt` files of the set)

All 35 routes (7 bots x 5 maps): 29 .. 83 way points (1,845 in all), 0 legs off the mesh, the first way point
reached from 8 of 8 START places, **0 gotos the model does not reach**; `route` exits 0 for all 35. 574 of the
way points are stops, 225 of them made for the turning circle; no goto has a radius under 25 (but the wall's
foot: 20). **37 turns are still marked**: a chord leaves the mesh there, by less than 2 units at 15 of them and
by 2 .. 17 at the rest, although the stop before it is made at 25 - nine on Hot Coffee (all by less than 2), 17
on Late Night Opening, eight on Withdrawal (seven of them the garage's west door, by 14 .. 17, one in each
route), three on Retomoto (bots 5, 6, 7), none on the park. And 5 targets lie 'behind him after a stop' with a
radius under 60: one place, Late Night Opening's corner behind the cash drawer, in the routes of bots 2, 4, 5,
6, 7 (radius 25, 112 .. 116 away).
(A stop at 12 was tried: it takes about 21 of the marked turns off the list by making a goto of radius 12 of
each - a way point he misses is one he circles, so 25, which is seen live, stays the floor and the turns stay
marked.)

| map (tree id, build) | way points, m | stops (made) | stage 1 / 2 / 3 on the steered line at way point | what the rig print still marks |
|---|---|---|---|---|
| Hot Coffee (DM01, `z_route3\M01`) | 36, 207 | 14 (2) | 13 the diner's east door / 31 the west door / 33 x 4666 | way point 21 (the door (6258, 22099)): the review's chord off by 1; one arc note (19) |
| Late Night Opening (DM02, `z_loot3\M02`) | 58, 333 | 15 (8) | 17 floor 2 / 49 the ground floor / 51 the entrance hall | way point 37: behind him after a stop (115 away, 174 degrees, radius 25); way point 38 (the hallway door): the review's chord off by 3; way point 52: by 7; three arc notes |
| Withdrawal (DM03, `z_cover3\M03`) | 53, 257 | 21 (10) | 4 the front door / 39 the garage's west door / 47 the landing of the drop | way point 40: the review's chord off by 14 (the west door: the mesh is 2 wide there); three arc notes |
| A Walk in the Park (DM06, `z_route\M06`) | 39, 214 | 11 (3) | 13 the bridge house / 27 / 37 | nothing; three arc notes |
| Retomoto Tower (DM09, `z_route4\retomoto_tab_fix`) | 52 + 28, 445 | 21 (7) | 2 through the window / street 3 the lobby's stairs / street 24, z 8363 | nothing; one arc note (8, after the table stack) |

**A. Hot Coffee.** Open street for 110 m (legs up to 1493, clear of the border by 50 and more), then the diner:
the mesh inside is aisles 20 .. 50 wide - 12 legs 'risky', 6 way points 'tight', all between way points 12 and
30. The east door (6900, 23156): a stop at (6902, 23316), 160 north of it on its axis, then south through two
door frames 105 apart (the ENTERS box is entered there, on the steered line), a second stop at (6877, 22988),
and the three doors of the aisle (6746, 22896), (6654, 22895), (6599, 22872) as stops (59 .. 160 apart: he
walks from stand to stand there). The cash register's stand place is 120 from it (its trigger reaches 200). The
five other money objects of the two stops are on people: not walked to. The west door is turned through from a
stop at (4100, 22093); stage 2 comes right behind it. The leg into way point 32 (the Senator's place) runs
within 7 of the van's drive-away line: harmless before anybody called the van. The van's doors: wait (6194,
20463) - inside the bots' AllyEscapeBox -, box (6164, 20691).

**B. Late Night Opening.** Three floors (y 1000, 500, 0) and **two escalators stacked exactly above each
other**, (625, 1056) -> (1928, -237), 18 m long, the mesh on them 69 wide; way points at both ends and one in
the middle. If a goto times out on the wrong floor the next ones will be 'reached' above or below their places.
Whether the escalators run is not known. **Three shatter-glass doors** (`SI0401_M02_FA_Door_Shatter_Glass_03 /
_01 / _06`, `ShotActivate`) stand 63 .. 150 from four legs: the START floor's only door (the leg into way point
2), the watch shop's hallway (twice), the entrance hall. **The script does NOT fire at them any more** (the
review's 4.4): the seven AI heisters leave through the same door at the same time, a hit on one is friendly
fire at full weight under Risk=2 (and the tuning has a retaliation limit), and a run that fires cannot say
whether an intact pane stops a walker. So `PT_DM02_board` answers the glass question: `reached` at script line
49 = it does not (or the crew had opened it); `goto is stuck` / `NOT reached` there = it does - then
`PT_DM02_shoot` (the same route with `--shoot`: `mdown 0` over the last 2.5 m before each door) is the second
run. That the scripted button fires the gun is itself not established. Loot: the two cash drawers; the 35 jewel
and watch objects are in cases only a shot or the squads' relays open. From the second drawer he turns back to
the corner (-1850, 2711), 120 away, with radius 25 from a stand (script line 106): the one goto of the set that
the review's replay circles - by the live from-stand cases he turns first and walks to it. Tight: the watch shop's door (-1683,
2669) at 13, the hallway door (-955, 2490) at 14, the entrance (-391, -5003) at 19 - at the last two the
review's chord to the way point behind still clips the mesh, by 3 and by 7.

**C. Withdrawal.** The route is the one run ESC3 walked by hand-picked way points: the same doors and the same
two money boxes (`Money_Arranged_04` / `_05`). Tight: the security corridor at 14 and the garage's west door,
where the mesh is 2 wide at (-1143, -4763). The switchback stairs (-997, -5912) .. (-875, -5945) are five stops
now (way points 15 - 19). **The drop**: way point 45 is the take-off at the sunk wall piece; he walks off it,
falls 70 and is carried about 230 on (ESC3), so the next way point lies 60 beyond the landing and is the `call`
point. From there 49 m of street to the van: wait (2946, -189), box (2970, 40).
**LIVE (section 8).** With the two damage factors alone the human was dead on the stairs down to the garage,
at (-292 .. -392, 440, -5679 .. -5784), 25.6 .. 29.8 s after 0x19, in three runs of three. With ten times the
health he lived (two runs of two), and **PB_DM03_board_hp walked an early copy of this route to the end**: 50
of 53 gotos reached, stages 1 / 2 / 3 at 0x19 + 18 / 78 / 94 s, $550,000 from the two boxes, the van seen
waiting, aboard a second after he stepped to its doors, escaped. Its two failed gotos are repaired:
- **the bots' loot place (424, -6154)** stands among the money boxes: with radius 40 the goto stuck 54 .. 73
  from it and ran out (the first scripts' radius 60: reached after one side step, 4.8 s). A loot place that is
  followed by money places now has radius 110 - he goes on to stand at each object anyway;
- **the bots' way place (-1237, -1504) in the yard**: in both runs that came there (K2c, PB) the goto stuck 115
  .. 140 short of it, at (-1322, 220, -1580) and (-1288, 220, -1615), and ran out; what stands there is not
  known (the mesh is open for 4 m around). It is in the tool's `BLOCKED` table now: the route no longer goes
  to it but up the yard's west side to the gate, 3 m and more from where he stuck (way points 41 - 44) - the
  stretch PB walked from (-1513, -1406) to the gate without trouble. Not seen as a whole.

**D. A Walk in the Park.** Terrain: the mesh's polygons are not flat (heights by `floor()`). One START point,
(5484, 473, 5000), stands 100 outside the mesh: the first leg from it is checked from the nearest mesh place -
one round in eight starts with a leg nobody checked. The first way point is the place in front of the first
door now (5514, 4783). All four loot objects are on people: he only stands 5 s at each of the bots' loot
places. Tight: the gate (-392, -4090) .. (-357, -4231), 8 from the border, between the pillars of
`SO0100_M06_Spiritual_Gate_A`. The boarding box stands still.

**E. Retomoto Tower.** *Tower*: the eight START places are on the balcony (x 6000, z -930 .. 770); he waits
there until 18.5 s after 0x19 (2 s after the glass has gone), walks to the balcony's middle and in through the
window; the ENTERS box is entered on the way to way point 2. The two stacks on the boardroom table: the mesh
ends 160 from them and their trigger reaches 165, so from the mesh's border he is pushed straight at the stack
for 1.2 s and then holds E (ASSUMPTION that this gets him inside). **These two push gotos (script lines 58 and
77) end by their timeout by design: their `NOT reached` lines are expected** and are named so in the expect
file and the plan. Then the office door on a straight leg of 1225 (its far end a stop now), the corridors, and
the staircase (-708, -1728) .. (-1840, -1263): the doors of its two flights are stops, and **the lower
landing's way point (-1823, -1179), which the review found unreachable in all seven routes with radius 26, has
radius 70 after a stop at the door 148 before it** (the model: reached at once; the chords from there to the
next two way points stay on the mesh).
*The join*: he is not steered into the jump box (run J2 lost 15 s that way). He stops at (2294, 634), 360 in
front of the box on the line into it, walks that line to a second stop at (2471, 811), and W alone for 0.8 s
takes him in. *Pace*: he reaches the join about 0x19 + 100 s; the crew's own fall-back start is the blast + 75 s
= 0x19 + 91.5 s, so by then the seven have set off by themselves (the review's note); `--join-after S` holds him
in the tower longer. *Street*: from the lobby car through its door (a stop), the lobby's stairs down to the
street, the bots' east side of the road, x -860, in legs of 1431, to the level exit box at z 8300 and the van's
stop: wait (-1620, 10459), box (-1850, 10459).

## 5. The set (`<work>\research\playtest\`; `python tools\kl_playtest.py set <work>\build\w_tabW [--rig2]`)

`rig2\PT_*_r2.ini` are for a hook with the rig patch (`<work>\build\klhook\test_pt1` has it); `PT_*.ini` are the
same routes for an unpatched hook - **those do not board a van** and wait 23 s + 10 s after the load instead of
`waitstate`.

| script (`rig2\..._r2.ini`) | what | lines, about |
|---|---|---|
| `PT_DM01_board` | Hot Coffee to the van and aboard | 177, 514 s |
| `PT_DM02_board` | Late Night Opening to the van and aboard; no shot fired (the glass question) | 205, 557 s |
| `PT_DM02_shoot` | the same with the fire button before each glass door - only if the first sticks at one | 216, 559 s |
| `PT_DM03_board` | Withdrawal to the van and aboard (an early copy ran live and boarded: section 8) | 203, 533 s |
| `PT_DM06_board` | the park to the helicopter and aboard | 279, 523 s |
| `PT_DM09_join` | Retomoto: the tower, into the jump box, 30 s in the lobby | 147, 339 s |
| `PT_DM09_board` | Retomoto: tower, join, street, the van, aboard | 241, 602 s |
| `PT_DM03_wall` | Withdrawal to the foot of climb edge 2, (-2075, -665), looking at the wall | 135, 287 s |
| `PT_DM03_die` | Withdrawal: into the bank's hall and stand; the first hit kills | 85, 393 s |

('about' = every wait of the script run out. No script outlasts the round: its clock ends it, the score page
comes and `onwin` takes the script to its end - about 565 s after the start at the latest; `MaxRunMs`,
`AutoExit` and kl_autotest's wait are set past that, so a run ends by `pass`, not by the clock.)

Each is a complete `KLHook.ini` for a TEST hook: the tree's `KLHook.expansion.ini` block as `mk_tab_inis.py`
writes it, the gameplay sections of the lead's `mkrun.py`, `[Auto]`, `[Script]`. Run, as its head says:
`python tools\kl_autotest.py <wait> --tag <name> --hook <TEST dinput8.dll folder> --ini <the file>`.
`--extra "[Section];Key=V"` adds keys (the review: the lead's series I ran `[Bots] BoardAll=1 Log=2`; these
take `[Bots]` from the tree - add `--extra "[Bots];BoardAll=1;Log=2"` to compare).

- **He is as hard to kill as the keys make him**: `[Balance] Ramp=0 CopToYou=0.02 CrewToYou=0.02
  PlayerHealth=10 RegenDelay=0.5 RegenTime=0.5 Log=2`. The first version had the two factors only and called
  him bullet-proof: **he was dead on the bank's stairs in three live runs of three** (section 8). With 5,500
  of health he lived through the bank in two runs of two (K2c, PB; steps of up to 583 and 759 came through).
  A test aid, not proof for the other maps. `--no-survive` leaves the owner's balance. What the police do to
  the human is NOT measured by these runs.
- `PT_DM03_wall` needs the tree's `Maps\DM03` replaced by `<work>\build\z_climb\M03` and a hook with
  `klclimb.c` wired; `[Climb] Enable=1 Key=0 Log=2` is in the ini. He stops 340 from the face at square to it,
  walks at it and lets go of W at most 60 from it (the hook's window is 15 .. 70). The last 96 of that leg are
  off the mesh (it ends 136 from the wall): `route --until wall` exits 1 for that, by design.
- `PT_DM03_die`: `[Balance] Ramp=0 CopToYou=20 PlayerHealth=0.05` and `[Fed] Enable=1 Player=1`. **Live once
  (the first version, run PT_DM03_die_r2): he was dead 19.1 s after 0x19, on the way, and came back as a
  fed.** One run; where nobody shoots him the run says nothing. After his death the gotos that are left steer
  the FED's body (the patch follows the new body) at the old way points, through walls: their `stuck` / `NOT
  reached` lines mean nothing, and `judge` leaves them out.

**`python tools\kl_playtest.py judge <ini> <the run's log>`** reads a run against its script (`.plan.json`):
when the first goto started after 0x19, which gotos were reached / NOT reached / stuck (those that end by their
timeout by design, and those after his death or after he is aboard, apart), which stage lines came and when,
whether the escort was called to a place that moved, whether he died - and a verdict. Exit 0 only when every
stage the script asks for came and every goto was reached. **`RESULT PASS` alone proves nothing** for these
scripts (the review's 4.5): it comes whenever the game did not fault and the script reached its end.

**The log lines that show each stage** (the `.expect.txt` beside each script has them with script line numbers
and seconds after 0x19):

| stage | line | from |
|---|---|---|
| the menu route | `script 39: level loaded: <name>` | klauto |
| the round | `session: state 0x18 -> 0x19 (game mode 4)`; rig2: `script 41: the session state is 0x19 after N ms` | klsteam, klauto |
| he is found | rig2: `players: the local one is #k at ... (the game's own pointer, slot N)` (live); unpatched: `players: the moving one is #k` | klauto |
| he walks | for every goto `script N: goto (x, z) reached in T ms: at (...)`. A `NOT reached` or `goto is stuck` names the leg (not the two push lines on Retomoto) | klauto |
| stage 1 / 2 / 3 | `bots: record 0 (you): heist stage 0 -> 1`, `1 -> 2`, `N -> 3` (live: 0 -> 1 in six runs, 1 -> 2 in K2c and PB, 2 -> 3 in PB) | klbot |
| loot | `0 you in-play gN $M` with M growing while E is held (live, PB: `$550000`) | klbot |
| the escort follows a MOVING human | `escort: record N re-pointed: you are X m away at (x, y, z)` with a place that changes (live, six runs: places up to 120 m apart) | klescort |
| the join | `join: player 0 entered box 9 at (x, 19601, z): jump to entry 5 ... requested`, `join: player 0 is at (6272, 5xx, -6305) 500 ms after the request` | kljoin |
| the crew follows the join | `crewjoin: ... moved first (EARLY)`, `crewjoin: N moved` | klcrew_rt |
| the van is called | `bots: L1 s19 van 1 ...` after `script N: IN THE EXIT BOX` (live, PB: 0.7 s after his stage 3) | klbot |
| the van waits for him | rig2: `script N: the vehicle's state is 3 (its timer x.x s) after T ms` (live, PB) | klauto |
| the escort is let go | `escort: record N released (the vehicle waits, state 3): sent to the boarding place (x, y, z)` (live, PB) | klescort |
| aboard, escaped | `bots: record 0 (you): aboard`, then `status6`; `script: window 'HeistStatusLeaderboard' is up` (live, PB) | klbot, klauto |
| the climb | `climb: at the foot of edge 2: ...`, `climb: edge 2: started /Movement/Climb/Up/High`, `pos after-the-climb` with y about 424 | klclimb, klauto |
| the fed | `fed: ARMED`, `fed: you: status 0 -> 1`, `fed: YOU ARE A FED: local player object ...` (live); NOT the score page within seconds of his death | klfed |

**A run proves nothing** when the `nudge:` lines say `game window in front at the last one: no`, when a leg
before the stage in question was `NOT reached` (the push lines apart), when the first goto was `stuck` for
seconds (he could not move yet), or when `bots: record 0 (you): dead` comes in a script that is not `--die`.

**An order for the next runs** (a hook with the rig patch, the `rig2` scripts; Withdrawal is done once):
`PT_DM09_join_r2` (does `goto` carry him down the tower and into the box: no way point of it is marked for the
rig; 5.5 min) -> `PT_DM01_board_r2` (the narrowest mesh; fourteen stops) -> `PT_DM02_board_r2` (the glass
doors, the escalators; script line 106 is the one goto of the set that is marked 'behind him') ->
`PT_DM06_board_r2` -> `PT_DM09_board_r2` -> `PT_DM03_board_r2` again (the loot place and the yard as repaired:
`judge` should say 'every goto was reached') -> `PT_DM03_wall_r2` -> `PT_DM03_die_r2`. After each:
`python tools\kl_playtest.py judge <the ini> <its log>`; if it says HE DIED, the `balance: you lost` lines
before it say by what. When a leg fails: `--bot N` gives another bot's places through the same doors, `--walk`
the same route without a sprint; a place where a goto stuck on something the mesh does not know goes into
`BLOCKED` in the tool (map, x, z, radius, the run that showed it).

## 6. The rig patch (`klhook/klauto.c`): in the tree since 09:14

`<work>\research\playtest\klauto_playtest.patch` was written by this track as a proposal and NOT applied by it.
**The lead applied it** (the tree's file carried it at 08:33, the hook `<work>\build\klhook\test_pt1` was built
from it then; commit 1f8b617 'klauto (TEST rig): waitstate, waitvan and the local player from the game's own
pointer'). The review read it as live code and found no defect.

- **P1 `waitstate <state> [timeout ms, 60000]`**: wait until the session state `[[0x168e598]+0x70]` is the
  value; a timeout fails the script (exit 26). **Live** (six runs): `script 41: the session state is 0x19
  after 21437 / 21562 ms`.
- **P2 `waitvan <state> [timeout ms, 60000]`**: wait until the vehicle's state byte `[rules+0x1dc]` (rules =
  `[[0x168e9e4]+0x54]`, ZGameRulesHeist's vtable 0xbd3514) is the value; 3 also takes 4, 1 also 2; a timeout is
  logged and the script goes on. **Live** (PB_DM03_board_hp): `script 132: the vehicle's state is 3 (its timer
  5.8 s) after 0 ms` - the van stood already when he came beside it (the crew had called it) - `goto (2970, 40)
  reached in 828 ms`, `bots: record 0 (you): aboard` 0.1 s later.
- **P3 the local player from the game's own pointer**: `[gamedata + 0x828 + 4 * (char)[gamedata + 0x898]]`,
  gamedata = `[0xdd265c]` (kl2 0x660b00). **Live**: `players: the local one is #13 at 6f795120 (the game's own
  pointer, slot 0)` before anybody moved, and after his death `#0 at 475f5020 (... slot 8)` - the fed's body.
  One side effect seen: the tick the body changes, a goto in progress says `no moving player found ... step
  skipped`.

Not written as a patch, would help: a `goto` that is 'reached' only within a height of its target as well; a
`goto` that ends at once when the player's place jumps more than 5 m (the join); a wait for 'he can move' in
place of the fixed 11 s after 0x19 (the flag is not known: `waitstate` on a later session state, if there is
one, or 'W held until he has moved 30 units').

## 7. ASSUMED, guessed, not done

ASSUMED (each is what the first run of a script tests):

- **The model's two readings bracket the game**: 306 and 230 degrees a second for a goto in motion (measured
  on 794 gotos, few of them a walk at a radius under 60 after a sharp turn), and 'he turns first' from a stand
  (31 live gotos from a stand reached, 12 of them among the bank's rooms and stairs; the place of 'reached'
  checked closely in five). A stop costs about 1.2 s.
- **W alone walks where he last walked.** The join's last 0.8 s and the climb's 'looking at the face' rest on
  it. He now comes to both from a stand on a straight line.
- **A person fits where the mesh is narrow.** 12 (Hot Coffee), 14 (Withdrawal), 12 (Retomoto) legs run nearer
  than 30 to the border; where the steered line is on the mesh the real player may still touch a frame.
- **A stage box fires for somebody who sprints through it.** Hot Coffee's ENTERS box is a plane 40 thick; the
  bank's EXITS box is 20 thick (the steered line is sampled every 7 .. 10 units).
- **An intact pane of a shatter-glass door**: not known; `PT_DM02_board` is the test.
- **E takes a money object when he stands in its trigger** (live for the bank's drawer and boxes only - again
  in PB: $350,000 + $200,000 with E held 4 s at each stand place), and 1.2 s of walking at a stack on Retomoto's
  table puts him inside its trigger.
- **The escalators stand still**, the level bounds are nowhere crossed, no car is parked on a leg.
- **Trigger boxes are half sizes** (one loose live instance, section 2).
- `VAN_SIDE` 230 (live once: from there the step to the doors took 0.83 s and he boarded), `ROLL` 20 (three
  live values: 19, 20, 20), `STOP_MS` 600 (live: PB's 17 stops that have only this wait), `MESH_SLACK` 25.
- That 5,500 of health is enough on the four other maps (seen on Withdrawal only).
- That nothing else stands on a leg: the two things the mesh did not know on Withdrawal were found by running it.

Not done:

- Of this version only an early copy of the Withdrawal script has run (the lead, PB_DM03_board_hp); the scripts
  as written now, and every other map, have not.
- `dyn.json`'s other ways (the RandomTrigger forks) are not walked: only the build's own way.
- Money on people, and money in cases that only a shot opens, is not walked to.
- `--until wall` ends at the foot; the step off the wall into the street is not scripted.
- After `--die` the fed does not walk a route of its own (the old way points are 50 m away through walls).
- No route for a stock level (they have no `bots.json`); no picture of a route.
- A way point is not re-planned when a goto fails: the script goes on from wherever he is.
- The model has no walls: 'IF HE DOES NOT TURN ON THE SPOT' (73 notes on the 35 routes), the 37 clipped chords
  and the 5 targets behind him are printed, not cured.

## 8. What has run in the game (the lead's six runs of this tool's scripts) and what it changed

Read from `<work>\build\klhook\live\`; `judge` gives the same for each (`python tools\kl_playtest.py judge
<live>\PB_DM03_board_hp.ini <live>\PB_DM03_board_hp.log`).

| run (hook) | script | what the log shows |
|---|---|---|
| PT_DM03_die_r2, 08:56 (test_pt1) | `rig2\PT_DM03_die_r2.ini`, first version | first goto lost (stuck 9.5 s, `NOT reached`); 5 gotos reached; stage 0 -> 1 at 0x19 + 15.8 s; the escort re-pointed after a moving human; dead 19.1 s after 0x19 (one hit, as designed), on the way; a fed 5.0 s later at (-4414, 300, -3486); the three gotos left steered the fed (`NOT reached`, 50 m off); round over when no heister was left; PASS |
| K1_DM03_wall_dry 09:22, K2_DM03_wall 09:27, K2b_DM03_wall_log 09:48 (test_climb1) | `rig2\PT_DM03_wall_r2.ini`, first version | each: first goto lost the same way; 14 / 14 / 13 gotos reached (plaza, front door, hall, the first steps of the stairs); stage 0 -> 1 at 0x19 + 16.0 / 16.0 / 15.9 s; the escort called to places up to 55 m apart; **`bots: record 0 (you): dead` 25.8 / 29.8 / 25.6 s after 0x19 at (-292, 440, -5784) / (-294, 440, -5751) / (-392, 440, -5679)**; round over 3 s later; 29 / 28 / 30 gotos never ran; PASS |
| K2c_DM03_wall_hp 10:01 (test_climb1) | the same first-version wall script, the lead added `PlayerHealth=10` | first goto lost; **42 of 44 gotos reached - through the whole bank, garage and yard to the wall**; the second failure is the yard's way place (-1237, -1504); stage 1 at 0x19 + 15.6 s, stage 2 at + 61.2 s; `climb: at the foot of edge 2: ... 48 from the face, speed 483, facing 1.00`, `climb: edge 2: started /Movement/Climb/Up/High` at + 78.4 s; then `unhandled exception c0000005 at KL2.exe+0x7e400`, RESULT FAIL (the climb's own matter, not the walk's). Largest loss 758.6 of 5,500 |
| **PB_DM03_board_hp 10:13 (test_climb1)** | **`rig2\PT_DM03_board_r2.ini` of THIS version**, as it stood at 10:05 (the script lines differ from the final file in one radius, one stop, and the two repairs below) | **first goto 11.0 s after 0x19, reached; 50 of 53 gotos reached; 17 stops with `wait 600`; 12 gotos from a stand with the target 46 .. 130 degrees off, all reached; stage 1 / 2 / 3 at 0x19 + 17.9 / 77.6 / 93.9 s; `$550000` (both boxes, E 4 s at each); the escort called to 12 places up to 120 m apart, and `released (the vehicle waits, state 3)`; `script 132: the vehicle's state is 3 (its timer 5.8 s) after 0 ms`; `bots: record 0 (you): aboard` at + 104.2 s; `status6` (escaped) at + 117.6 s; the score page; PASS.** Not reached: script 79 (the loot place, among the money boxes) and 119 (the yard's way place). 86 losses, the largest 584 of 5,500 |

What it changed here:

1. **The wait after 0x19** (section 1.2): 11.0 s before the first goto; on Retomoto 18.5 s (the blast was taken
   8.4 s too early as well - that would have walked him into the intact window).
2. **The stops are real** (1.4): the first scripts' stop in front of a door was passed at 313 units a second.
3. **88 gotos of the first version were reached** in its five runs (radius 20 .. 110) and 50 of this version's
   in PB; those that followed a `keep` goto are in `rigfit`'s 794 (on the 59 of K2c and PB the model's place of
   'reached' is 8 units off in the median). None of them circled - the two way points the review found
   unreachable are on Retomoto and Late Night Opening, which nobody has walked yet.
4. **His death on the stairs** - for the lead, whose file `klbalance.c` is: K2b ran with `[Balance] Log=2`. For
   6 s he lost 0.7 .. 4.3 a hit, 28 hits (police bullets at the 0.02): 51 of 401.5 in all. Then `you lost 151.2`,
   0.19 s later `151.2`, 0.12 s later `30.2`, and 0.19 s later he was dead with 17.9 left. 151.2 is 100 x the
   1.512 of the burst just before it, and 5 x 30.24: **the same weapon at a factor a hundred times the dial's,
   or five pellets and then one of a shotgun at about full weight** - either way a shooter the two keys
   `CopToYou` / `CrewToYou` did not scale. `Tune=0`, no traitor line, no fed. Who it was is not established. All
   three deaths are within a metre in height and 1.5 m in the plan of the same landing.
   The scripts answer with `PlayerHealth=10` and half a second to full health; that is the keys' most - and
   in K2c and PB he came through (steps of 583 .. 759 among the losses: the same thing, larger).
5. `--die` works as written once; P1, P2 and P3 of the patch work.
6. **From PB, the run of this version**: the loot place's radius (110 when money places follow; it was 40 and
   he stuck among the boxes) and the `BLOCKED` table (the yard's way place is no longer walked to). Everything
   else of that run is as the tool writes it now.

## 9. The review (`re/playtest_review.md`) and what was done

Verdict ACCEPT WITH FIXES: one must, four should, notes. Each is answered at the end of that file; in short:

| the review | done |
|---|---|
| 4.1 MUST radii below the turning circle; two way points of the scripts unreachable (13 over the 35 routes) | **fixed**: `steer()`, `cannot_turn_in()`, `Route.drive()` (rule 9); the review's own `orbit.py` finds 0 unreachable way points over 7 bots x 6 routes (was 13); radii in motion never under 60; the turning-circle model is held against 794 live gotos. The review's third point ('after a stop a target behind him needs radius 75') is **refuted in its premise** - from a stand the game turns him first (1.4: 31 live gotos from a stand with the target 45 degrees or more off, all reached, 12 of them in the run of this version's own script) - and applied all the same where a chord allows (60, then 75 / 90). The review's replay `steer2.py`, which reads a stand as an arc, still circles one place, from a stand, in three routes (Late Night Opening's corner (-1850, 2711) behind the cash drawer, radius 25, bots 2, 5, 7 - script line 106 of `PT_DM02_board_r2`): printed there as 'BEHIND HIM AFTER A STOP' and named in the expect file |
| 4.2 SHOULD the mesh check walks lines the rig never walks (152 of 1,753 chords off) | **fixed**: the steered line under two turn rates and three chords are followed over the mesh and cured by a stop (40, then 25); the review's own `indep2.py` finds 33 of 1,746 chords off the mesh (was 152 of 1,753), every one from a stop of radius 25 - the floor -, and no leg (0 of 1,803); the tool prints them (37 turns of 1,845 way points; 15 of them by less than 2 units) |
| 4.3 SHOULD boarding is timed blind on the unpatched rig | **fixed**: unpatched scripts do not board; rig2 steps only on a seen `waitvan 3` |
| 4.4 SHOULD the fire button is on by default | **fixed**: off by default, `--shoot` and `PT_DM02_shoot` for the second run; friendly fire named (section 4 B) |
| 4.5 SHOULD the expect files contradict themselves | **fixed**: the push lines are named expected; the rig2 files quote the patched rig's line; `RESULT PASS` is said to prove nothing; `judge` |
| notes | selftest covers Retomoto's street part; the join's pace (`--join-after`; the later start already puts him behind the crew's own timer); `MaxRunMs` past the round's own end; the AllyEscapeBox note; `floor()` and the box sizes worded as the review found them; the section 6 text |
