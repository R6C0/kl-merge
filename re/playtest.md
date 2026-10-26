# A scripted player for the unattended runs: the rig's `goto`, the maps' own routes

2026-10-11, track H; revised the same day after its review (`re/playtest_review.md`; what was done about each
defect is at that file's end and in section 9 here). **This track's own work is OFFLINE: it started no game,
wrote nothing into a game folder and committed nothing.** Files: `tools/kl_playtest.py`, this file, and the
scripts in `<work>\research\playtest\` (`<work>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead
Men\KL_PortTools`). The lead has run six scripts of this tool in the game (section 8): five of the FIRST
version, and at 10:13 an early copy of THIS version's Withdrawal script - **it walked the whole route, looted
$550,000, boarded the van and escaped.** What those runs showed is used here. The scripts as they are written
now (that run's two failed gotos repaired) have not run; the four other maps have not been walked at all.

**THIRD ROUND (track H3, the same day; section 10).** Since then the lead has run the scripts on Hot Coffee,
the park and Retomoto too (whole heists, section 10.0). Section 10 is what those runs showed and what the tool
does about it; it SUPERSEDES sections 0 - 9 in four things: the scripts' damage dial (0.001, not 0.02), the
bank's stairs (walked in motion again, not from stop to stop), `--die` (a guard's post, not 'near a guard'),
and the fed, who now has a walk of his own (`--fed-walk`). The third round's work was offline as well.

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
`tele <x> <y> <z>` (TEST only, 2026-10-26: the local player's actor [[0xdd265c]+0x4cf0] through the game's teleport 0x62a900 via klcrew_rt.c klt_teleport, guarded by klt_tele_known / klt_refuse and __try; a refusal is logged and the script goes on; logs `tele: from (..) to (..) now (..)`), `ents <name-substring> [maxN=20, cap 200]` (TEST only, read only: scene entities whose name [[obj+4]+0x6c] contains the text - slot, object, class, `ref?` = [node+0x30] (GUESS: REF label), `en?` = not bit 10 of [node+0x3c] (GUESS: enabled), place). `face x z` turns only while he walks. A script has at most 640 lines; a `log` / `pos` text is cut at 79
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

## 10. The third round (track H3): what the live runs showed, the point-blank rule, the fed's own walk

OFFLINE: no game was started, nothing written in a game folder, nothing committed. Changed: `tools/kl_playtest.py`,
this file. Written: `<work>\research\playtest\v3\` (15 scripts since the review's fix round, 10.8; each with `.route.txt` / `.expect.txt` / `.plan.json`,
and `klauto_h3_onbody.patch`, a patch TEXT for the rig that is NOT applied). Every number below is from the logs in
`<work>\build\klhook\live\` or from the five builds of the tree `<work>\build\w_tabM` (`z_route3\M01`, `z_loot3\M02`,
`z_cover3\M03`, `z_route\M06`, `z_rooms\retomoto_full`); the commands that print them are named.

### 10.0 The runs

Whole heists by the scripted player: `PB_DM03_board_hp`, `PB_DM01_board_hp`, `PB_DM06_board_hp`,
`B1_DM09_board_gates`, `J1_DM09_join`, `J0_DM09_join_oldchain`, `FO_J1_DM03_follow`, `K2c_DM03_wall_hp` (to the
wall). Deaths on the bank's stairs with 5,500 of health: `FO_J0_DM03_dry`, `FO_J4_DM03_spare`, `FO_J3_DM03_all`.
The fed: `PT_DM03_die_r2`, `PT_DM03_die_f2`, `FD3_DM03_die`. Late Night Opening has still not been walked by anybody.

### 10.1 The start (`python tools\kl_playtest.py starts <run> ..`)

MEASURED: the second after `session: state 0x18 -> 0x19` at which the human is last seen on his START place and
first seen off it, from every line of a log that has his place (`pos`, a goto's result or 'stuck', klescort's
'you are ... at').

| runs | the first goto began | last line ON the START place | first line OFF it | the first goto |
|---|---|---|---|---|
| the bank, W held through the countdown: S5, SH1, K1, K2, K2b, K2c, PT_DM03_die_r2 / _f2 (8) | before he could move | 10.22 / 10.38 s ('stuck' lines of S5, SH1), 10.32 s (K1, a `pos`) | 10.42 .. 10.84 s, 34 .. 289 units off | K1 .. die_f2 (began at 0x19, timeout 9.5 s): **NOT reached, 6 of 6**; S5 / SH1 (earlier scripts, longer gotos): reached |
| Retomoto's earlier builds, W held: N0, N0b, VAN1 - 5 (7) | before he could move | 10.16 .. 10.19 s | 10.33 .. 10.56 s (five), 98 .. 236 off | reached in six; VAN1 not (another cause) |
| the bank, the wait of 11.0 s: PB_DM03, FD3, FO_J0, FO_J4, FO_J1, FO_J3 (6) | + 11.0 s | 9.47 .. 10.70 s | 11.31 .. 12.33 s | **reached, 6 of 6**, in 0.30 .. 1.33 s |
| Hot Coffee PB_DM01, the park PB_DM06 (1 each) | + 11.0 s | 10.79 / 10.53 s | 12.28 / 12.25 s | reached in 1.27 / 1.25 s: he walked from its first tick |
| Retomoto J1, J0, B1 (3) | + 18.5 s (the blast) | 17.99 .. 18.16 s | 19.99 .. 20.16 s | reached in 1.7 .. 2.0 s |

So: **he is free 10.16 .. 10.4 s after 0x19 on both maps where W was held through it (15 runs), and with the 11.0 s
wait the first goto was reached in 11 runs of 11 on four maps.** The loss of 'the first goto' is the six runs of
the first scripts, which had no wait; all six are bank runs because nothing else was walked then. The second
version's first goto on the bank was reached in 0.3 .. 1.3 s; in PB_DM03 / FD3 it was 'reached' 218 units from
the START place after an arc (the target lay 160 away and 122 degrees off, radius 110: W is down while he turns)
and the next goto took a loop of about a second - no time lost to the countdown. Retomoto's script is covered by
its own wait for the blast (18.5 s). **Not measured: Late Night Opening** (never walked), and on Hot Coffee and
the park only 'free by 11.0 s'. What the scripts do: the wait stays (FREE_S 10.4 + 0.6), and **the first goto of
every round now has a timeout of 20 s** (`FIRST_TIMEOUT`): should a map's countdown be longer, W is simply held
until he can move (S5, SH1 and six of the Retomoto runs held W through the countdown and their goto was reached)
- a first goto 'whose loss does not matter', because it is not lost. The rig cannot wait for 'he can move'
itself: no session state changes then (0x19 holds to the round's end).

### 10.2 The bank's stairs and the point-blank rule (`python tools\kl_playtest.py danger <build>`)

**The rule (re/melee_damage.md, read there in kl2.exe):** a soldier who fires at a target within 160 units (node
to node, 3-D) sends at every step of his burst a hit worth 100 bullets of his gun; the Arcade dial scales it. At
`CopToYou=0.02` one step costs the human 151.2 from a Type 79, 449.2 from the M9, 582.8 from the Sig, 758.6 from
the .45, 81.6 from the shotgun - `danger` prints the map's guards with their guns' steps, and they are the very
numbers of the logs. MEASURED in the logs: a guard sends about six steps a second (0.12 .. 0.19 s apart). The
5,500 of health (PlayerHealth=10) last 1.1 s beside the .45.

**The scripts compared.** The lead's `PB_DM03_board_hp.ini` and `rig2\PT_DM03_board_r2.ini` are the same on the
stairs line for line (script lines 47 - 68; line 69's radius is 40 against 25): both have the five REAL stops
there (lines 58, 61, 63, 65, 67, each with `wait 600`; then 69, 71, 73). The script that differs is the FIRST
one (`K2c_DM03_wall_hp.ini`, lines 56 - 64), whose 'stops' had no wait and were none: `keep` gotos of radius 35 ..
70. The staircase = from 'reached' at (-997, -5912) to 'reached' at (-875, -5945):

| run (script) | the staircase took | point-blank steps on it (from the logs' `balance: you lost`) | least health | end |
|---|---|---|---|---|
| K2c (first script: in motion) | **3.7 s** | 3 x Type 79 = 454 | 4,981 | lived (one .45 step later, at the vault) |
| PB_DM03_board_hp (stops) | 7.65 s | 12 lines: Type 79 x 10, Sig x 3 = 3,262 | 3,442 | lived |
| FO_J1_DM03_follow (stops) | 7.95 s | 16 lines: Type 79 x 12, .45 x 5 = 5,608 | **796** | lived |
| FO_J3_DM03_all (stops) | 7.4 s | 10 lines on the stairs (Type 79 x 10 = 1,514); behind them 13 shotgun lines and nine steps of the .45 in 15 s | 293 | dead 47.7 s after 0x19 in the vault corridor, after 9.4 s on one leg ('goto is stuck' at (-838, 240, -6948)) |
| FO_J0_DM03_dry (stops) | - | 16 lines = 4,583 in 2.6 s | - | **dead 31.1 s after 0x19 at (-346, 438, -5879)**: in the wait of line 68 |
| FO_J4_DM03_spare (stops) | - | 13 lines = 6,097; the last second alone 5,190 (.45 x 3, Sig x 5; one line of 1,341.4 is one step of each) | - | **dead 31.5 s after 0x19 at (-571, 344, -5949)**: the lower flight, line 69 |
| K1, K2, K2b (first script, 401.5 of health) | - | K2b: 2 x Type 79 + the rest of a third | - | dead 25.6 .. 29.8 s after 0x19 on the upper flight |

**Which stop did it:** the two at the ends of the staircase's middle landing - script lines **65 / 66** (the stop at
(-321, -5692)) and **67 / 68** (at (-322, -5910)), 217 apart. In every run of the stop scripts the first step (always
a Type 79) comes on the upper flight at x -640 .. -390, which he WALKS (310 .. 350 units a second: the flight runs
from one stop to the next); 2 .. 4 more come while he stands the 0.6 s of line 66 (PB 4, FO_J0 4, FO_J1 2, FO_J3
4); the 217 units to the second stop he covers at 105 .. 190 units a second (a turn of 90 degrees from a stand
first), 1 .. 4 more steps, and by the second stop the .45 and the Sig have come up from the garage floor: FO_J0
died standing in the wait of line 68, FO_J4 one second behind it. K2c crossed the landing in 0.48 s.

**Where the guards are.** All 15 armed enemies of the bank are in the world when the level loads, 'eUnleashed', in
squads with a hunt or flanking rout: they come to him. The posts of those that sent the steps lie 2,128 .. 3,890 of
mesh way from the landing (Type 79: `Guard_03` (-505, 240, -4973) 2,128, `Guard_01` (624, 802, -5995) 2,904; the
.45 `SecurityGuard_02` 3,226 to the landing's south end; the Sig `Guard_04` 3,890; the shotgun 2,430 to the foot),
and the first step of each gun came 7.4 .. 15 s after the human's stage 1 (17.3 .. 17.9 s after 0x19): **160 .. 390
units a second along the mesh, most 215 .. 300** (5 runs). So a rule by POSTS alone cannot keep him clear of
hunters: the straight distance from the landing to the nearest post is 424 (the M9's, which sent no step in any
of the eight runs), to the posts of the guns that killed him 600 .. 2,000.

**The rule the tool now has** (`Route.danger()`; printed in every `.route.txt`, counted in every `.expect.txt`):

- **R1 - a stop, or a walk under sprint speed, within 400 units (3-D) of an armed enemy's post** (`PB_POST`: the
  160 of the rule + 240 for his own steps, the 240 a GUESS), every post counted, also of a squad that comes into
  the world later. **Live it holds where guards STAY**: Retomoto's two stops in front of the jump box (way points
  67, 68 of the tower part) stand 30 and 95 from the posts of `Atrium_1st_CoverMiddle_Squad_02` and
  `010_Squad_Elevators`, and both runs that came there took 4 .. 5 steps in the 0.6 s wait of the first (B1: sp89 /
  MPi69 x 3 + a double; J1: sp89 x 3 + Type 79 x 2). It says nothing where they hunt: Hot Coffee's way stops 84
  from `KitchenBoy`'s post and stands 5 s ON the Senator's (the bots' loot place is the man with the .45) and
  PB_DM01 took no step at all; the park's four loot stops are 4 .. 83 from the bosses' posts and PB_DM06 took two
  SCAR steps elsewhere, in motion.
- **R2 - a stop that a guard can have reached**: his mesh way from his post at `GUARD_RUN` = 300 units a second,
  counted from the human's stage 1 (a route without an ENTERS box: from its start), against the second the model
  has him leave the way point. MEASURED on the bank only; a GUESS elsewhere, and blind to squads that come later.
- **What is done about a hit.** (a) Where a LIVE run walked the place in motion, the stop is taken out whatever
  the model says: `LIVE_MOVING`, so far the bank's nine way points of the stairs with K2c's radii and `keep`
  (reached in K1 / K2 / K2b up to his death and all nine in K2c; `--stops` puts the stops back). (b) Everything
  else stays - a door stop is there because the mesh is 14 .. 50 wide and nobody has walked it in motion, a loot
  stop is the thing itself - and is covered by the dial: **a route script now carries `[Balance] CopToYou=0.001
  CrewToYou=0.001`** (`COP_DIAL`; `--cop 0.02` = the old). A .45 step is then 37.9, a Type 79's 7.6, the shotgun's
  4.1: still in the log's `you lost` lines (which is why it is not 0), and FO_J4's worst second, 5,190, would have
  been 260 of the 5,500.

| the board route of | armed enemies in the world at the load (later) | R1: stops / walks within 400 of a post | R2: stops in reach, of the route's stops | stops that MOVE |
|---|---|---|---|---|
| Hot Coffee | 13 (0), all hunt | 11: way points 10 - 16 (the diner's east door, 84 .. 367 from `KitchenBoy`; 13 is a stop 84 from him), 18 (money), 25, 26 (walks at `CornerShop`'s Type 79), 32 (the loot stop = the Senator, 3) | 13 of 14 | none (no live run in motion) |
| Late Night Opening | 12 (0), all hunt | 4: 20, 22, 26 (walks), 28 (money, 325 from `DiamondGuards_02`) | 11 of 15 | none |
| Withdrawal | 15 (0), all hunt | 4: 30, 31, 32 (stops 183 .. 297 from `Guard_03`'s post at the garage's west door), 33 | 13 of 13 | **eight stops gone: way points 11, 13 - 19 (the stairs; with 12, nine way points in motion). 21 stops -> 13** |
| A Walk in the Park | 14 (0), 12 hunt | 9: the four loot stops 14, 20, 25, 29 (83, 40, 4, 49 from the bosses' posts: the money is on them) and the legs beside them | 9 of 11 | none |
| Retomoto Tower | 3 (88) | 16, all of squads that come later; INSIDE the 160: the two stops and the last step of the join (30, 95, 46) | 4 of 24 (blind to the 88) | none (the join needs its two stands) |

### 10.3 `--die`

Was: the first way point with a guard within 700 by a straight line on the mesh ('near a guard and hope'). Is:
**he walks to the POST of an armed enemy and stands 110 .. 130 from it** (`DIE_STAND`: inside the 160, where every
shot of that guard is the point-blank step) - the guard that costs the least way (the route up to one of its way
points, then up to 2,500 of mesh way), those in the world at the load first. The balance is as before (`CopToYou=20
PlayerHealth=0.05`: 27 of health, any bullet kills) - but NOT in a `--fed-walk` script without `--fed-die`, which
has no `CopToYou` key (10.4: unmirrored, that float is a heister's bullet on the fed): there the 27 of health die
to one police bullet at Risk=2's 1.0 (a Type 79's is 75.6 near, 39 at 50 m; a far shotgun hit may take two). The
place only makes sure somebody fires. Live so far (the old
rule, the bank, 3 runs): dead 19.1 / 20.0 / 25.4 s after 0x19 in the hall, twice ON THE WAY.

| map | he stands at | the guard |
|---|---|---|
| Hot Coffee | (5839, 0, 23884) | `FrontMall_01\\FBI-Agents_01` (SCAR), post 126 away; the squad hunts |
| Late Night Opening | (1486, 1000, 1283), on the START floor | `3rdFloor_Guard_01` (shotgun), 128 |
| Withdrawal | (-184, 800, -6067), the hall | `BankMainSquad_02\\Guard_02` (M9), 126 |
| A Walk in the Park | (928, 239, 6490) | `US_Boss` (AK-74), 128; attitude eStayBack |
| Retomoto | (5850, 21021, -247): IN the blown window (he walks 18.5 s after 0x19) | `Squad_Guards_Inside_01` (.45), 128; the squad comes into the world later |

ASSUMED: a hunter has not left his post for somebody else when the human comes (then another comes to him: the
bank shows it).

### 10.4 The fed (`python tools\kl_playtest.py fed <build> [--fed-group N]`; `script ... --die --fed-walk`)

**Live so far (the bank, 3 runs):** he is police exactly 5.0 s after his death, **ON an AFTER_DEATH point and on
the floor**: `fed: YOU ARE A FED ... at (-4414, 300, -3486)` (r2: 20 from point 1), `(-4570, 300, -3349)` (f2: 26
from point 4), `(-4457, 300, -3593)` (FD3: point 2 itself); the floor there is 300 by mesh and by collision. **He
CAN move**: r2 and f2 walked him 5 .. 6 m - the hero's gotos that were left steer the new body at the old way
points - into the room's south-east corner, (-4155, 300, -3645), where both stuck for the rest of the run: 44
from `SI0200_M03_DoorSteelWin_A_09`, a static steel door in the south wall (the picture's double door) that is
SHUT in the collision. The room's way out is its north-west door. FD3 had no goto left and stood.

**How a script copes with what it cannot see.** No window comes up at his death and the session state stays 0x19:
the rig has nothing to wait on (`waitstate`, `waitwin`, `onwin` see neither; there is no loop and no jump but
`onwin`). So: he stands `--die-wait` seconds (20) at the die place with a `pos` every 5 s; then `peek 0x168ea60`
(klfed's switch: 0 once he stands as police, 1 while he is alive or waiting - a 1 says the run shows nothing of
the fed) and `pos fed-appeared`; then gotos that steer whatever body the game calls local.

**A death ON THE WAY** (2 of the 3 live deaths: r2 during script 52, f2 during 53; only FD3 reached its place): the
hero's gotos that are left run out one after the other, each to its timeout, and steer the FED at the hero's way
points; then come the 20 s of `--die-wait`. With the ordinary timeouts (3 x the model's time + 4 s, at least 6 s)
that was 42.5 s on the bank after a death at script 53 and up to 94 s on Hot Coffee - not '6 .. 8.5 s', which is
one goto. So the HERO's gotos of a `--die --fed-walk` script now have short timeouts (`DIE_GOTO`: 1.5 x the
model's time + 2.5 s, at least 4 s; the first goto of the round keeps its 20 s): after a death in the second goto
the fed's own first goto begins at most **70 s (Hot Coffee), 43 (Late Night), 68 (the bank), 60 (the park), 19
(Retomoto)** after he appeared (each `.expect.txt` has its number), and usually about half of that. Whether he
then still stands where a straight line reaches his first way point is shown for the bank only (its room is convex,
and the review's flood has the line from the live corner (-4155, -3645) clear); NOT for Hot Coffee (a control room
8.6 m up with a landing and a catwalk), the park (a deck with stairs) and Late Night Opening. For those three the
set has an `onbody` twin (`H3_DM01 / DM02 / DM06_die_fed_rig3`, 10.6): the trap skips the leftover gotos and the
wait. They need a TEST hook with the patch, which nobody has built.

**The point is the game's (a random free one): the gotos are written for one GROUP of points** (points within
1,500 of each other), the first way point being one a straight line reaches from every point of the group.
Retomoto has three groups - two lift cars 36 m apart on one floor, and the square 196 m below them: one script a
group (`--fed-group 1 / 2 / 3`), and the `pos fed-appeared` line (and `judge`) says which group the run got.
**What that costs:** a run of `_g1` fits 3 picks of 7, `_g2` and `_g3` 2 of 7 each - IF the pick is uniform over
the free points (how kl2 picks is not read here; track L's question) - and a run that got another group shows only
where he appeared: plan on about 3 runs for group 1 and 4 for each of the others, or wait for `ifnear` / `jump`
(10.6). Group 1 is partly answered already: the owner's own round of 2026-10-11 12:31 has `fed: YOU ARE A FED ...
at (1804, 19601, 812)` = point 2 itself, and his words are 'spawn as a fed but in a lift'.

**The BLIND gotos must be read by the height.** klauto's `goto` is 2-D ('reached' = a distance in x, z), and a
blind target is the crew's mesh UNDER the place he stands at: in the park it is (-975, 259, -9784), which in the
plan lies inside the fed's own row on the deck - 199 from points 3 and 4, whose floor is at 1549, and 372 from the
stairs' end the blind gotos start at; on Hot Coffee (2045, 60, 17479) is 800 under the landing. A fed who never
came down, or went back up, can 'reach' it. So `pos fed-blind-N` shows a way only when its y is within 150
(`BLIND_DY`) of the crew's mesh there (259 / 60); the `.expect.txt` says so and `judge` tests the y, not the goto.
On Retomoto's group 2 the target is on his own floor (2.6 m outside the car's door): there 'reached' does mean he
got out.

What the rig lacks for a better answer: 10.6.

**What is known offline, per map** (`fed`; 'collision' = `kl_escape.Walk` on the level's .HVK: the static,
non-convex shapes only - no door that opens, no character radius; it takes a slab's underside for a floor and the
flight above for a ceiling, so on stacked stair flights its 'no' is weak):

| map | the points | mesh under them | collision | the way to the crew, what stands between | the script (`v3\\H3_..`) |
|---|---|---|---|---|---|
| **Withdrawal** | 7, x -4791 .. -4317, z -3593 .. -3369, y 391 .. 396: the parkade's stairway room (`M03_FAA_Parkade_StairwayRoom_01a`) | 91 .. 96 under each: **the crew's own part** (649 polygons) | floor 300 under each; from them the collision alone reaches 5,555 m2 (the whole map read), among it the EXITS box, the gate and the level exit | **joined by both.** North-west door (-4565 .. -4435, 300, -3054), three more frames east of it where the mesh is 10 wide ((-4165, -3162), (-4045, -3162), (-3755, -3048)), down to the parkade floor, then 21 m east to the garage's west door (-1299, -4574) - 87 m to the loot (424, -6154) through the garage against the crew's way; to the level exit 77 m by the yard and **the same drop the crew takes** | `DM03_die_fed`: 35 gotos to the loot place. `DM03_F3_fed_dies`: to the level exit (854, 70, -155) by the drop, and he stands on the crew's way to the van |
| **Late Night Opening** | 7, x 4228 .. 4716, z -2616 .. -2042, y 90: the car park east of the mall (`M02_FA_A_Out_Parkinglot_101a`) | **none**: the crew's mesh begins 1,800 .. 2,350 west | floor 0 under each (90); the collision reaches 10,071 m2, the ground floor's EXITS box and the level exit among it | **joined by the collision**: 26 m west over the car park and in along z -2366 .. -2426 to where the mesh begins, (1888, 0, -2386); then the mesh. The collision shows nothing shut between the car park and the ground floor's two boxes; what bounds the flood near the way are plants, the escalators and `WallA_10mDor_*` | `DM02_die_fed`: 6 gotos OFF the mesh, then 18 on it up the lower escalator to loot stop 2 (-1892, 500, 2593) |
| **Hot Coffee** | 7, x 2105 .. 2789, z 16923 .. 17129, y 951: the warehouse's control room, 8.6 m above its floor (`WarehouseControlRm_301a`) | 91 under each, **a part of its own: 16 polygons, x 1935 .. 3034, z 16565 .. 17264 at y 860, joined to nothing**; one polygon of it, 10 x 49, points west at x 1935 .. 1945, z 17125 .. 17174 | floor 859; the collision reaches 127 m2: the room, a landing west of it and a catwalk (`MainBridgeA / C`) north to z 17893, all at 859 .. 872 | **NOT joined by mesh or collision.** West of the room stands `Si0105_M01_Staircase_FA_version_01` (x 1499 .. 1900, z 16499 .. 17300, y 23 .. 1244; landings at 860 / 650 / 450 / 266 / 62; its north face has wall only at x 1500 .. 1540 and 1860 .. 1900) - a stair tower built for Fragile Alliance, GUESSED to be the way a Dead Men policeman comes down. The walk test does not take it: across the top landing's south edge (z 17031 .. 17097) the collision has a strip 90 .. 150 over the floor - a parapet or the next flight up, not told apart - and of the flights only undersides and side walls are in the non-convex shapes it reads | `DM01_die_fed`: 4 gotos over the collision to the tower's top landing (1695, 860, 17093), then 3 BLIND ones at the crew's mesh (2044, 60, 17478), 8 m below. The `pos` heights say whether he comes down |
| **A Walk in the Park** | 5, x -1158 .. -1001, z -10246 .. -9473, y 1630 .. 1656: on a freeway deck 13.4 m above the park (`SO0201_M06_FreeW_Junction_E_Stairs_FA_01`) | the park's own polygons are 1,345 .. 1,396 BELOW three of them; none at their height | floor 1539 .. 1561 (the deck); the collision reaches 129 m2: the deck inside `ColiObj_Police_spawn_BLOCK_01` (an unseen wall round the spawn, x -1354 .. -428, z -10742 .. -8777) and **the FA stairs down to y 1004** | **NOT joined.** The stairs wind down a pillar (collision way: (-606, 1556, -9996) (-266, 1451, -9896) (-226, 1238, -9496) (-506, 1124, -9456) (-586, 1056, -9656) (-606, 1004, -9736)); the walk test stops at 1004, where the next floors of its cell lie at 871 / 438 / 195. The park's mesh is at (-975, 259, -9783), 4 m to the side and 7.5 m below | `DM06_die_fed`: 7 gotos down the stairs as far as the walk test went, then 3 BLIND ones at the park's mesh |
| **Retomoto**, group 1 (points 1 - 3; 3 of 7) | (1904 / 1800 / 1987, 19601, 818 / 812 / 973): INSIDE the lift car `SI0101_JPN_Elevator_Int_A_04` on the join's floor | the crew's tower part under two; none under (1800, 812) | floor 19600; the collision reaches **8 m2: the car**, bounded by `Elevator_Main_A_00` and the door leaves `Elevator_DrInt_A / B_00` | the mesh runs out through the car's door; **the collision says the door is shut** - as the neighbour car's was live (run J1, 2026-10-09: 'the car's doors are shut and stop the player') | `DM09_die_fed_g1`: 2 gotos in the car, then the mesh way up to the boardroom's loot (193 m); a goto that sticks at the fed's way point 2 = the door |
| group 2 (points 4, 5) | (-1764 / -1508, 19613, -61 / -147): the atrium lift `SI0103_M09_ElevatorCar_00` | a mesh part of ONE polygon | floor 19604 / 19620; 16 m2: the car, bounded by `ElevatorCar_00`, `Elevator_01`, `ElevatorDoor_01` | NOT joined; the crew's mesh is 2.6 m outside the door, at (-2054, 19600, -167) | `DM09_die_fed_g2`: 2 gotos, 3 BLIND at that place |
| group 3 (points 6, 7) | (447, -50, -7956), (-367, -50, -7594): the square in front of the lobby | the street's part (the crew's after the join), at the points' own height | **the only floor of the collision in their cells is at 19: 69 ABOVE the points** (the street's mesh lies 40 .. 50 under the road's collision; the player's feet read -50 there in run RT4) - whether he is put on the ground or under it is for the `pos` line | joined by the mesh: 34 m to the crew's first street place (2054, 54, -6019) | `DM09_die_fed_g3`: 7 gotos |

So, by what the files say: **a fed can leave on the bank and on Late Night Opening; on Hot Coffee and in the
park he stands at the head of stairs made for him which only a run can judge; on Retomoto five of the seven points
are inside two lift cars whose doors are shut in the collision** (the authored points of `kl_fa_author.POLICE`:
'the elevator lobby, the atrium lift, the square'), and the two on the square lie 69 under the road's collision.

**The fed's balance keys** (`FED_WALK` / `FED_DIE` in the tool; corrected after the third review's M1 - the first
form did the opposite of what it said; what follows is a READING of `klhook/klbalance.c` 2 a3 and `klr_mir`, NOT
RUN). A police player's game reads the OTHER float of each of the three pairs. With `FedMirror=1` the hook writes
the pairs exchanged and every key keeps the meaning of its name (live: f2, FD3) - and puts the fed's health under
the hero's dial. With `FedMirror=0` the fed keeps the game's own 550 (live: r2, 'a POLICEMAN: left alone') and
nothing is exchanged, so each key means two things in one run:

| key (slot) | while he is the hero | once he is police | a `--fed-walk` script writes |
|---|---|---|---|
| `CopToCrew` (+0x00) | a police bullet on a heister | a heister's bullet on a police AI | 0.005 |
| `CrewToCop` (+0x04) | a heister's bullet on the police | a police AI's bullet on a heister | 0.005 |
| `CopToYou` (+0x08) | a police bullet on him | **a heister's bullet on him** | no key = Risk=2's 1.0 |
| `CrewToYou` (+0x10) | a heister's bullet on him | a police AI's bullet on him (a stray) | 0.001 |

The first form had `CopToYou=20` and `CopToCrew=0.005` alone: after the switch a heister's bullet cost the fed x 20
(about 940 against his 550 - one bullet = his second, final death, at the very place the bank's script sends him:
the crew's loot place), and a police AI's bullet cost a heister `CrewToCop` = x 1.0 - the crew NOT protected, as
in r2 at 0.05 (all seven dead 15 .. 47 s after the switch), while the 0.005 only made the crew harmless. Now: the
hero's 27 of health die to one police bullet at 1.0 just the same; a heister's bullet costs the fed x 1.0 of 550
(about 12 hits - he can still be shot dead by the crew he walks to, as in the owner's game); a police bullet costs
a heister x 0.005 on BOTH sides of the switch. **The price:** a heister's bullet costs the police x 0.005 too, all
round long - the crew cannot clear a room, and a guard who comes close still takes 43 of a heister's 252 with every
point-blank step. That a crew is then in play for the 2 .. 4 minutes of the walk is a GUESS. (The other way,
`FedMirror=1` with `CrewToYou` low, was not taken: the fed then has the hero's 27 of health and a colleague's stray
bullet - `CopToYou` - ends the walk.) The hook prints factors with two decimals: 'police->crew 0.01' / '0.00' in
the `balance: on` line are these numbers. `[Fed] EndSeconds=0`: klfed does not end the round when no heister is
left.

`--fed-die` (F3): `FedMirror=1`, `CopToYou=20`, `CopToCrew=0.005` - under the mirror the names hold: the fed has
the hero's 27 of health and a heister's bullet (`CrewToYou` = 1.0) is his second death. A colleague's stray is x 20
there and kills him as well; the log's `you lost` line cannot tell the two apart (a loss is at most his 27).
`H3_DM03_F4_two_rounds` has no `FedMirror` key (= 1) and `CopToCrew=0.05`: the same reading, nothing to correct.
A police player in a stage box: only a `pos fed-in-..` line; what the rules make of it is not known.

`judge` reads a `--fed-walk` run: the point he appeared on (and its group), whether he was on the floor, klfed's
switch, every `pos fed-..` line (a blind one with its height against the crew's mesh), which of his gotos were
reached (the blind ones counted apart), how far from his goal he ended; for `--rounds 2` it counts the
`session: state 0x18 -> 0x19` lines and the verdict is not clean when fewer rounds began than the script is for.

### 10.5 The set (`python tools\kl_playtest.py set3 <work>\build\w_tabM` -> `<work>\research\playtest\v3\`; rig2 form)

| script | what | lines, about |
|---|---|---|
| `H3_DM03_board` | the bank to the van and aboard: the stairs in motion, the dial at 0.001 (the FollowOut tests ride on it) | 195, 524 s |
| `H3_DM02_board` | Late Night Opening to the van and aboard (never walked: the glass doors, the escalators; its first goto holds W up to 20 s) | 205, 557 s |
| `H3_DM03_van_clear` | the bank `--until van --clear`: he calls the van and stands at (1386, 48, -316), inside the level exit box, 19 m from the van's stop, 451 from its line, outside the bots' box, 90 s, a `pos` every 10 s - in play and NOT aboard while the bots board (Bribe / Leave) | 148, 388 s |
| `H3_DM01_die_fed`, `H3_DM02_die_fed`, `H3_DM03_die_fed`, `H3_DM06_die_fed` | `--die --fed-walk` (10.3, 10.4): the fed's keys of 10.4, the hero's gotos with short timeouts | 99 .. 130, 349 .. 387 s |
| `H3_DM01_die_fed_rig3`, `H3_DM02_die_fed_rig3`, `H3_DM06_die_fed_rig3` | the same three with `onbody` (10.6): **only for a TEST hook with `klauto_h3_onbody.patch` - none exists; any other hook loads NO script** | 101 .. 112 |
| `H3_DM09_die_fed_g1` / `_g2` / `_g3` | Retomoto, one script a group of points; a run fits 3 / 2 / 2 picks of 7 (10.4) | 81 .. 129, 311 .. 370 s |
| `H3_DM03_F3_fed_dies` | F3 of re/fed.md: the fed walks to the level exit, where the crew runs to the van, and stands **180 s** (to the round's end; with the first form's 60 s the crew might still have been looting - it passes there only on its way out) with the hero's 27 of health; expected: the stock end about 3 s after his second death, no `status 7 -> 1`. If nobody passes, the run shows the walk and the drop, not F3 | 128, 486 s |
| `H3_DM03_F4_two_rounds` | F4: `--die --rounds 2`. At the score page `tap RETURN` after 8 s, **`wait 3000` and `windows`**, then `onwin` armed again (armed in the poll after the tap it would fire on round 1's page if that were still up and the script would 'PASS' there; SH1 had 9 s between, and the page was gone 2 ms after the key - but nobody has seen this page after a fed round), `waitstate 0x19`, 11 s, the same walk: he dies in each round (round 2's `fed: police bodies:` shows the first body used). **Read the run by `session: state 0x18 -> 0x19` appearing TWICE** (`judge` counts them), not by RESULT PASS | 111, 479 s .. 14 min |

The second round of a session (READ in klauto.c and in run SH1 of 2026-10-09, three rounds): `onwin` is ONE trap
and is spent when it fires - it is armed again behind its label; RETURN on `HeistStatusLeaderboard` goes 0x20 ->
0x23 -> 0x24 (`FAWaitForPlayers`) -> 0x25 -> 0x26 -> 0x16 -> 0x18 -> 0x19 in about 2 s, no load; when the last life is
lost the page is `HeistStatusLeaderboard_EndGame`, another window - no trap, the run then ends by `MaxRunMs`.
Every script takes the tree's own `[Bots]` block as it is installed (the owner's: BoardAll, FollowOut, Tune,
Backstab 35); `--extra` changes it.

### 10.6 What the rig lacks, as a patch text (NOT applied: `v3\\klauto_h3_onbody.patch`; `git apply --check` passes on the tree's klhook/klauto.c of 2026-10-11 13:30)

- **`onbody <label>`**: a second trap beside `onwin` - armed, it remembers the game's local player object, and the
  poll in which the game's pointer names ANOTHER object (his return as police) it lets go of every key and goes to
  the label, logging the new body's place. The hero's leftover gotos are then skipped instead of steering the fed,
  the 20 s of `--die-wait` are not needed, and the logged place IS the AFTER_DEATH point.
- **`ifnear <x> <z> <radius> <label>`** and **`jump <label>`**: with them ONE script can carry the gotos of every
  group of points (Retomoto) and take the right ones.

The text compiles in a TEST build (`cl /c /W3 /DKLHOOK_TEST klhook.c` on a scratch copy of klhook\\ with the
patched file: no new warning) and has run nowhere. `kl_playtest.py script ... --fed-walk --rig3` writes the
`onbody` form (the trap after `pos spawn`, `label fed<round>` in front of the fed's part); `ifnear` / `jump` are not
used by the tool yet.

### 10.7 ASSUMED, not done

ASSUMED: `GUARD_RUN` 300 outside the bank; `PB_POST`'s 240; that the dial at 0.001 is all a route needs (the
limiter and the regeneration are as before); that a guard chosen for `--die` is at his post or sends another;
that the fed's keys of 10.4 (`FedMirror=0`, no `CopToYou`, `CopToCrew` = `CrewToCop` = 0.005, `CrewToYou=0.001`,
`EndSeconds=0`) do what the reading of klbalance.c says and keep a round going long enough for the fed's walk -
NOT RUN; r2's 45 s 'unhurt' is no evidence for any key (nobody shot at him in the stair room), and a crew that
cannot kill a policeman may not live either; that the pick of the AFTER_DEATH point is uniform; that a hero's goto
with the short timeout (`DIE_GOTO`) still gets him near the die place (when not, he is shot where he is); that
3 s are enough for round 1's score page to go after RETURN following a fed round; that the first way point of the
fed's part is still in a straight line from where the hero's leftover gotos have pushed him (the bank's room is
convex: yes there; Hot Coffee, the park, Late Night Opening: not shown - their `_rig3` twins are the answer); that `kl_escape.Walk`'s 'reached' means a player gets there (no character radius); everything BLIND in
10.4. The collision's floor under Retomoto's square (19) against the height the player's feet were logged at
there (-50) is a contradiction this note does not resolve.

Not done: nothing of the third round has run in the game. No way DOWN the two stair towers (Hot Coffee, the park):
the walk test does not take them and the tool has no other. The stops that R1 / R2 name are not moved but on the
bank's stairs. `--fed-to van` ends at the crew's level exit place, not beside the van. No `--die` place is checked
against where the guard really is. Late Night Opening's countdown is not measured. The `onbody` patch is a text.

### 10.8 The review of this round (`re/playtest_review3.md`: ACCEPT WITH FIXES) and what was done

Every point was re-checked against the code and the files before it was taken; none is refuted.

| point | what it said | done |
|---|---|---|
| **M1** | the `[Balance]` block of the seven `--fed-walk` scripts without `--fed-die` did the opposite of its `.expect.txt`: unmirrored, `CopToYou=20` is a heister's bullet on the fed x 20 and `CrewToCop` 1.0 a police AI's on a heister | HOLDS (`klbalance.c` `klr_mir = {1, 0, 4, 5, 2, 3}`; with `FedMirror=0` the pass writes slot k = key k). The review's form (a) taken, plus `CrewToYou=0.001`: `FED_WALK` / `FED_WALK_DROP` in the tool, the table and the price in 10.4, the `In the ini:` sentence of each `.expect.txt`, the die line's text. F3 / F4 untouched in their keys (10.4) |
| **S1** | a death on the way leaves 42.5 s (the bank) of the hero's timeouts + the 20 s wait; 'harmless' is shown for the bank only; '6 .. 8.5 s each' understates | HOLDS. The hero's gotos of a `--die --fed-walk` script have short timeouts (`DIE_GOTO`; the sums are in 10.4 and in each `.expect.txt`); `_rig3` twins of Hot Coffee, Late Night Opening and the park are in the set for a hook with `onbody`. The patch is NOT applied (klhook\\ is not this track's) |
| **S2** | the park's blind goto lies in the plan inside the fed's own row; a 2-D 'reached' proves no way | HOLDS (199 from points 3 / 4; `klauto.c`'s goto compares x, z). The expect text says 'read the y', with the target's height and its distance in the plan; `judge` tests each `pos fed-blind-N` against the crew's mesh height (`BLIND_DY` 150) and counts the blind gotos apart; where the target is on his own floor (Retomoto's group 2) it says that 'reached' is the test |
| **S3** | Retomoto: a script fits 3, 2, 2 picks of 7 | HOLDS as arithmetic (the pick's law is not read). Said in each group script's `.expect.txt`, in 10.4 and 10.5, with the owner's 12:31 round for group 1 |
| **S4** | F4 arms `onwin` in the poll after `tap RETURN` | HOLDS. `wait 3000` + `windows` before it (`PAGE_GONE_MS`); `judge` counts the 0x19 lines and a run with fewer rounds than the script's is not clean |
| **S5** | F3's fed stands 60 s where the crew only passes on its way out | HOLDS. `--linger 180` for that script: he stands to the round's end. Not walked on to the loot place: the level exit is where F3 wants him |
| N7 | two `log` texts cut mid-word at 79 | shortened |
| N3 | `H3_DM03_board` line 58 has `keep` where K2c's line 56 had none | LEFT: one untested difference at a 50 degree turn; the first run of that script tests it |
| N10 | other sessions' `tools/kl_fa_fedpoints.py` may move the points | LEFT, and it stands: the fed scripts are for the builds of `w_tabM` as they are - after a `kl_fa_fedpoints` step run `set3` again on the new tree |

`set3` now writes 15 scripts; the three board / van scripts' `.ini`, `.route.txt` and `.expect.txt` came out byte
for byte as before (their `.plan.json` gained each goto's timeout), the nine other old ones changed as above and
three are new. All 15 pass the review's own parser check (`rev3\\parse.py`, written from klauto.c: 0 problems,
`onbody` allowed for the three twins) and a second `set3` reproduces them. Nothing of it has run in the game.
