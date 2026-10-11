#!/usr/bin/env python3
r"""kl_playtest.py - a scripted PLAYER for the unattended test runs: a walkable route for the human through a finished
map build, and the complete KLHook.ini (TEST hook, klhook\klauto.c [Script]) that walks it.

    python tools\kl_playtest.py route  <build folder> [--bot N] [--until ...] [--die] [--no-loot] [--shoot] [--out <file.txt>]
        prints the route: every way point with its leg (length, least distance to the mesh's border), the goto's radius and
        speed, where he STOPS, what the rig's steering makes of each goto (THE RIG below), the stage boxes it enters, the
        loot stops, the join, the vehicle; the legs that do NOT stay on the mesh; the gotos the rig's model does not reach
        and the steered lines that leave the mesh. Exit code 1 when a leg is off the mesh or the model does not reach a
        goto. <build folder> = a folder with <slot>_Main.zip, bots.json[, KLJoin.ini].
    python tools\kl_playtest.py script <installed tree folder> <map id> <out ini> [options]
        the complete ini for one run through the tree's 'Dead Men maps' page (the route is read from the tree's own copy
        of the map: Maps\<id> + BuildInfo\<id>), <out>.route.txt, <out>.expect.txt and <out>.plan.json beside it.
        --until enter|loot|exit|join|van|board|wall   how far he walks (default board): into the ENTERS_BANK box / through the
                       last loot stop / through the EXITS_BANK box / Retomoto: into the jump box (the hook moves him to the
                       lobby) / to the vehicle's stop, where he watches it come and go / + he boards / Withdrawal's climb
                       build: to the foot of a [Climb] edge of the yard wall, looking at it
        --die          he walks to the first way point that has a guard near, and stands; one hit kills ([Fed] Player=1 is on)
        --bot N        whose planned places are walked (2 .. 8 = Squad#02 .. #08; default 2)
        --build <folder>   take the route from this build instead (it must then be what Maps\<id> holds for the run)
        --extra "[Section];Key=V;[Other];Key=V"   more ini keys; a key goes into the FIRST section of that name
        --no-survive   leave the owner's balance (default: [Balance] CopToYou / CrewToYou = --cop - he never shoots)
        --no-loot / --loot N / --loot-hold S / --loot-wait S   money objects walked to at a loot stop (default 2), seconds
                       of E at each (4), seconds he stands after a stop (5)
        --shoot        hold the fire button over the last 2.5 m before a shatter-glass door. NOT the default: the AI heisters
                       leave through the same doors (a hit on one is friendly fire at full weight under Risk=2), and a run
                       that fires cannot say whether an intact pane stops a walker
        --visits N     boarding: how many visits of the vehicle are tried (3)        --linger S   seconds at the end
        --walk         never sprint
        --rig2         use waitstate / waitvan (klauto.c with the patch of re\playtest.md 6: the hook <work>\build\klhook\
                       test_pt1 has it). WITHOUT it a script does NOT board a key-framed van: that rig cannot see the van and
                       a step to its doors by the clock is blind (--blind-board writes the timed steps all the same)
        --join-after S Retomoto: he stands in the tower until about S seconds after the round began, so that the crew has
                       started by itself (its fall-back timer is the blast + 75 s = 91.5 s) before he takes the join
        --cop F        [Balance] CopToYou and CrewToYou of a route script (default 0.001: THE THIRD ROUND below; 0.02 = the
                       scripts before it). Not for --die
        --stops        keep the stops the model asks for where a live run walked the place in motion (LIVE_MOVING)
        --clear        with --until van: he does not wait beside the van's doors but stands CLEAR of the vehicle and of the
                       place the AI heisters gather at, inside a level exit box, for --linger seconds (default 90)
        --fed-walk     with --die: after his death the script goes on FROM THE AFTER_DEATH POINTS (where a police player
                       appears): `pos`, then gotos that work from every point of the group, along the collision where
                       the mesh does not reach and along the mesh to where the heisters are (THE FED below)
        --fed-group N  the group of AFTER_DEATH points the gotos are written for (1 = the largest; Retomoto has three
                       groups far apart and the game picks the point: one script a group)
        --fed-to K     loot | exit | level | enter | van: the crew's place the fed walks to (default loot; when that is
                       not on the mesh part he can reach: the nearest of the crew's places that is)
        --fed-die      F3: [Balance] FedMirror=1 (the fed has the hero's 27 of health): he walks into the heisters and the
                       first of their bullets is his second death. Without it FedMirror=0 (550, the game's own), NO
                       CopToYou key, CopToCrew = CrewToCop = 0.005, CrewToYou 0.001 and [Fed] EndSeconds=0 (FED_WALK below:
                       unmirrored, a police player's game reads the OTHER float of each pair): the walk is seen
        --die-wait S   seconds he stands at the --die place before the fed's gotos begin (default 20). When he dies ON THE
                       WAY (2 live deaths of 3) the hero's gotos that are left run out first, each to its timeout, and push
                       the fed about: up to 28 .. 55 s in all on the four maps with a long way, 4 s on Retomoto (DIE_GOTO
                       keeps them short; the .expect.txt has the sum) - `onbody` (--rig3) is the answer to that
        --linger S     with --fed-walk: seconds the fed stands at the end of his walk (default 60)
        --rounds 2     F4: at the score page the script taps RETURN, waits 3 s for the page to go, arms the page's trap
                       again, waits for the next round's 0x19 and walks the same route again (the level is not loaded
                       again: run SH1). Read such a run by its TWO 0x19 lines (judge counts them), not by RESULT PASS
        --rig3         a --fed-walk script for a klauto.c that has `onbody` (the patch text <work>\research\playtest\v3\
                       klauto_h3_onbody.patch; NOT applied, in no hook): the trap is armed after 0x19 and brings the
                       script to the fed's part the tick the local player is another object
    python tools\kl_playtest.py set    <installed tree folder> [out folder] [--rig2]     the first set (re\playtest.md 5)
    python tools\kl_playtest.py set3   <installed tree folder> [out folder]     the third round's set, rig2 (re\playtest.md 10)
    python tools\kl_playtest.py fed    <build folder> [--fed-group N] [--fed-to K]     what is known OFFLINE about the map's
        AFTER_DEATH points: over which mesh part, over which floor of the collision, how far the collision alone lets a
        walker get from them and what bounds that, the way to the crew
    python tools\kl_playtest.py danger <build folder> [--bot N] [--until ..]     the route's stops against the map's armed
        enemies (THE POINT-BLANK RULE below)
    python tools\kl_playtest.py starts [<log folder>] <run> [<run> ..]      per run: when the first goto began after 0x19,
        when the human was last seen on his START place and first seen off it, how the first goto ended
    python tools\kl_playtest.py selftest <build folder>      the geometry against itself: funnel legs walked by trace()
    python tools\kl_playtest.py rigfit [<log folder>] <run> [<run> ..]      the steering model against the logs of scripted
        walks that ran in the game (<run>.ini + <run>.log; default folder <work>\build\klhook\live): every goto that was
        reached in motion is replayed from the place and heading the log gives for the goto before it
    python tools\kl_playtest.py judge  <script ini> <KLHook log of its run>      what the run showed, stage by stage: reads
        <ini>.plan.json and the log; says which gotos were NOT reached (those that end by their timeout by design left
        out), which stage lines came, and whether the run can be used at all. Exit code 0 only when every stage came

WHY (2026-10-11, track H). Every live run so far had the human STANDING at the start. The heist stages are raised by
trigger boxes for whoever walks through them, Retomoto's crew only reaches the lobby when the PLAYER takes the join,
the escort bot was only seen beside a standing player, and boarding, the fed respawn and the climb never ran
unattended. SIX runs of this tool's scripts were made in the game by the lead on 2026-10-11 (re\playtest.md 8): five of
the first version, and PB_DM03_board_hp, an early copy of this version's Withdrawal script, which walked the whole
route, looted, boarded the van and escaped. The scripts as written now (that run's two failed gotos repaired) and
the four other maps have NOT run. Account, per-map routes, risks and the rig patches: re\playtest.md.

THE RIG (klhook\klauto.c, read whole; re\playtest.md 1). `goto x z [radius 120] [timeout 20000] [sprint] [keep]` holds W
and turns the mouse by the bearing error (5 / s, at most 1800 counts/s = 306 degrees/s); 'reached' is a distance IN THE
PLAN (x, z only: a way point one floor up or down counts); no path finding; 1.5 s without 40 units of way -> a side
step (A / D, 0.7 s), every third time a tap on C; a timeout is logged and the script goes on FROM WHEREVER HE IS.
So a route is a list of way points with a straight, walkable line between each two. Speeds measured in the logs of the
earlier walks (ESC3, N0b, VAN5, J2: median of the legs): sprint 585 units/s, walk about 400 (100 units = 1 m).
  THE TURNING CIRCLE. W is down while the mouse turns, so he cannot turn tighter than speed / turn rate: 75 at a walk,
110 at a sprint. A target inside that circle on its side by more than its own radius is NEVER reached - he circles it
until the timeout (the stuck test does not fire: he keeps moving). steer() is that law as a model; `rigfit` replays it
against the logs of the walks that ran (runs ESC1-3, RN13, N0, N0b, J2, VAN5 and the six runs of this tool's own
scripts, PT_DM03_die_r2, K1 / K2 / K2b / K2c_DM03_wall, PB_DM03_board_hp: 794 gotos reached in motion, radius
25 .. 200, most at a sprint: the model reaches every one of them, its time is within -90 .. +48 ms of the log for 8
in 10, the place of 'reached' 9 units off in the median and 52 for the 215 with a turn of 45 degrees or more; under
TURN_WIDE it misses 7 the game reached). cannot_turn_in() is the exact test of the circle (the BEST turn he could
make): the rig's law is not the best turn, so the model circles more than that test does, never less.
  A STOP. A goto without `keep` that is followed at once by a goto is NOT a stop: W is up for two polls and he goes
on (28 such gotos in those logs: 1.01 of the goto's own speed in the median over the whole goto, 0.76 at the least -
four of them the first scripts' own 'stop' in front of a door). He
stands only when a `wait` follows: 20 units farther on, within 0.75 s (ESC3 scripts 40, 67; VAN5 198). From a stand a
goto to a target far off his heading turns him BEFORE he walks: all 31 such gotos of the logs (the target 45 degrees
or more off) were reached, 12 of them in PB with this tool's stops; in the five clean cases (ESC1-3 / RN13 script 73:
130 .. 143 away, 137 .. 144 degrees off, radius 60, 1.3 s each; VAN5 202: 118 degrees) his place at 'reached' lies
1 .. 5 units from where a turn on the spot and a straight walk put it, and 34 .. 78 from where an arc from his old
heading would.
  GO. Session state 0x19 is the round's clock starting, NOT the moment he can move: the human stood on his START place
for 10.1 .. 10.4 s after it in the seven runs that held W through it (N0, N0b, VAN5, PT_DM03_die_r2, K1 / K2 /
K2b_DM03_wall: the first goto of every run of the first scripts was lost to it). Retomoto's window goes blast_timer =
16.5 s after 0x19 (runs R7c, I5: the bots take stage 1 18.4 s after it).

THE ROUTE RULE (Route; every number is a constant below with its reason)
  1. Guide points = the AI heister's own planned places (bots.json: plan.bots[N].places, one per station; Retomoto also
     plan.rt.street) - on the navigation mesh by construction, in the order the squad's chain walks them. Stations of
     kind loot, level, gate and rally are MUST-PASS; a stage box (enter / exit) is must-pass unless its bot place is a
     detour and the way to the next place crosses the box anyway; 'way' places only say which corridor the bots take
     (one nearer than MARGIN to the mesh's border is moved to where the mesh is wider). dyn.json's other ways (the
     RandomTrigger forks) are not walked: the build's own way is in every one of them.
  2. Between two guide points: the shortest polygon corridor (kl_fa_bots.Nav.dist_map, the bots builder's stand-in for
     the game's pathfinder), then the shortest line inside it by the funnel method, every shared edge drawn in by
     MARGIN from both ends. A shared edge too short for that (under DOOR) near the mesh's border is a DOOR: its middle
     is a way point. So: a way point at every corner (MARGIN off the mesh's corner) and in every door.
  3. A 'way' place, a corner or a door is dropped when the straight line past it stays on the mesh and keeps KEEP_CLEAR
     from every border edge, or is no nearer to one than the way point and the two legs it replaces (a row of doors in
     a straight aisle becomes one leg; a door the line would pass off its middle stays).
  4. A door is walked through ALONG ITS AXIS: where the line turns at a door, a way point goes on the axis in front of
     it (he stops there) and / or behind it. A way point goes where a leg goes onto a slope that rises 60 or more and
     where it leaves it (stair / escalator foot and top). No two way points are farther apart than LEG_MAX.
  5. Every leg is then walked on the mesh in steps of STEP (trace(): from polygon to polygon over shared edges - the
     way kl_fa_bots_rt.straight samples a line, with the height of the polygon the walk is on): a leg that leaves the
     mesh is printed as OFF THE MESH, one whose line comes nearer than RISK_CLEAR to a border edge as RISKY, a way
     point nearer than TIGHT as TIGHT. Off the mesh by design: a drop link (the bank's sunk wall piece: he falls 70 and
     is carried about 230 on - run ESC3), the last step to a van's rear doors when the road is no mesh, the foot of a
     climb edge, a money object the mesh does not reach.
  6. The human starts on ONE of the level's START points, another one each run (seen live: he stood exactly on one of
     them in every log looked at): the first way point is one that a straight line on the mesh reaches from EVERY one.
  7. SPECIAL PLACES. A loot stop: the bot's own loot place, then the money objects that stand still and that the use
     key can take (not those on a person, not the cases only a shot opens), E held at each. Retomoto's jump box: he is
     NOT steered into it (the hook jumps him the tick he is inside and the goto would walk him about the lobby until
     its timeout): a goto ends in front of it, on a line into it, and W alone takes him in. The vehicle: he waits
     beside the van's rear doors, out of its line (its nose kills), and steps to the doors only while it stands:
     --rig2 by `waitvan 3` (it waits for the van however long: the score page ends the script when none comes). The
     unpatched rig cannot see the van: its scripts stop beside the doors and do not board.
  8. WHAT THE RIG MAKES OF IT (Route.drive; the review's must). Every goto is driven by steer() from where the goto
     before it left him - his place, heading and speed - under the rig's own turn rate and under one a quarter lower
     (TURN_WIDE: the circle a third wider), and the line he steers is followed over the mesh; so are three straight
     chords to the next way point: from where the model has him, from where W went up (should he not roll on after a
     stop), and the review's (the goto's radius BEFORE the way point, taken back along the leg's own line; judged by
     trace(), all the way). A goto that is not reached without circling under either rate, or whose steered line or
     a chord leaves the mesh, makes the way point BEFORE it a STOP: he walks to within R_STOP of it, W is let go, the
     script waits STOP_MS, and the next goto starts from a stand, where he turns before he walks (then R_TIGHT when a
     chord from there still leaves the mesh; no goto gets a smaller radius than that: a way point he misses is one
     he circles). A way point passed in motion keeps its radius (R_OPEN / R_TURN / R_HARD) and never less than
     R_MOVE: no radius is cut to a share of a short leg any more. From a stand a target nearer than NEAR_BACK and
     more than BACK_DEG off gets R_BACK, then 75 / 90 while the pessimistic arc still circles it, where the next
     chord allows; and a goto from a stand must also be reached when he starts to walk AIM degrees off its line.
     What no stop cures is printed with the way point: 'NOT REACHED BY THE MODEL', 'STEERED LINE OFF THE MESH' (how
     deep), 'BEHIND HIM AFTER A STOP', and 'IF HE DOES NOT TURN ON THE SPOT' (the pessimistic reading of a start from
     a stand: an arc at the wide rate from where he looks - what that would circle or leave the mesh by).
     The stage boxes are those the STEERED lines enter, from every START place.
LEG_MAX = 1500: a timeout must tell 'blocked' from 'slow' quickly (2.6 s of sprint, 3.8 s of walk a leg; the goto
gets about three times that), a failed leg leaves the next line starting at most that far from where it was
planned, and the log gets a 'reached' line every few seconds. The earlier walks' longest leg that was reached is 1924.
GUESS / ASSUMPTION are marked where they are used. A MESH SAYS NOTHING about cars, people, props or panes of glass
that stand on it, and nothing about a level's bounds.

CHECKED (offline): `selftest` - 300 random pairs of places a map part, 5,000 .. 7,000 legs of the funnel walked by
trace(), none leaves the mesh on any of the five maps of the tab (two pieces of code that share only the polygons;
Retomoto's street part too), and steer() against cannot_turn_in() on 5,496 gotos in the open. `rigfit` - the model
against the game (above). Against tonight's logs: the human's place at the round's start is one of the build's START
places on every map (0 units off, seven runs, two different places on Retomoto) and his heading there the START
point's own +Z; 92 .. 100 % of the bots' logged places lie on the mesh by floor() (the park: 78 %, the rest within
60 of it). floor() is exact on a polygon's edges and an estimate inside one that is not flat.

THE THIRD ROUND (2026-10-11, track H3; re\playtest.md 10 has the numbers). What the lead's runs of this tool's scripts
showed, and what the tool does about it:
  THE START (`starts`). With the wait of FREE_S + FREE_PAD after 0x19 the first goto was reached in all 11 runs that
have it (the bank 6, Hot Coffee 1, the park 1, Retomoto 3 - whose 18.5 s wait for the blast covers it: 0.3 .. 2.0 s);
without it, it was lost in 6 of 6 (all on the bank: nothing else was walked so). He is free 10.16 .. 10.4 s after
0x19 wherever W was held through it (the bank's build 8 runs, Retomoto's 7); Hot Coffee and the park: free by 11.0 s
(one run each); Late Night Opening: never walked. So: the wait stays, and the first goto of a round gets
FIRST_TIMEOUT - should a map's countdown be longer, W is held until he can move, and nothing is lost.
  THE POINT-BLANK RULE (re\melee_damage.md: a guard that fires at a target within PB_REACH sends, at every step of
his burst, a hit worth 100 bullets). At CopToYou 0.02 that is 151.2 a step from a Type 79 and 758.6 from the .45,
about six steps a second a guard: the 5,500 of health last 1.1 s beside the .45. The bank's guards are all
'unleashed' hunters: they come to him. In all eight bank runs the steps began on the stairs down to the garage
(his way point 14 - 15), 7 .. 15 s after his stage 1, 2,100 .. 3,900 of mesh way from the posts of the guards that
sent them: about GUARD_RUN a second. The scripts with real stops (five on those stairs, 7.7 s for the staircase)
were dead there in 3 runs of 5; the first scripts, whose 'stops' were none, took 3.7 s and 4 steps (K2c).
  So (Route.danger(), `danger`): R1 - a stop or a walk within PB_POST of an armed enemy's post (as the level places
him; also one whose squad comes into the world later) is printed: 11 way points on Hot Coffee, 4 on Late Night
Opening, 4 on the bank, 9 in the park, 16 on Retomoto. Live it holds where the guards STAY: Retomoto's two stops in
front of the jump box stand 30 and 95 from posts and cost him 4 .. 5 steps there in both runs that came to them (B1,
J1); it says nothing where they hunt (Hot Coffee's way passes 84 from a post: no step in PB_DM01). R2 - a stop a
guard can have reached (his mesh way from his post at GUARD_RUN, from the human's stage 1 on) is IN REACH: nearly
every stop behind the entrance, on every map. NOTHING IS MOVED BY EITHER but where a live run walked the place in
motion (LIVE_MOVING: the bank's nine way points of the stairs, eight of them stops before): a door stop is there
because the mesh is 14 .. 50 wide, a loot stop is the thing itself (the park's four are the bosses' own places).
What cannot move is what COP_DIAL is for: a route script now carries [Balance] CopToYou = CrewToYou = 0.001 (a .45
step 37.9, a Type 79's 7.6 - still in the log's 'you lost' lines; FO_J4's worst second, 5,190, would have been 260).
  --die: he walks to the post of the first armed enemy the route comes near and stands DIE_STAND from it (inside
PB_REACH: any shot is point-blank; with CopToYou 20 and 27 of health the first bullet from anywhere kills as before -
a --fed-walk script has no CopToYou key: 1.0, and the 27 still die to one bullet of anything but a far shotgun hit).
  THE FED (klhook\klfed.c). The game puts a dead human on a random free AFTER_DEATH spawn point as police; the rig's
pointer follows the new body. The script cannot SEE the death (no window comes, the session state stays 0x19): it
stands --die-wait seconds, writes `peek 0x168ea60` (klfed's switch: 0 once he stands as police) and `pos`, and then
steers whatever body the game calls the local player. `fed` prints what is known offline; the gotos are written for
ONE group of points (all of them, where they stand together), the first way point being one a straight line reaches
from every point of the group. Where the points are off the crew's mesh part the first gotos follow the collision
(kl_escape.Walk: the non-convex static shapes, no doors that open, no character radius), and where neither joins
the crew's part the script walks to the edge of what the collision leaves open, tries FED_BLIND gotos toward the
crew and stands: the `pos` lines say how far he got - BY THEIR HEIGHT: a goto's 'reached' is a distance in the plan,
and a blind target can lie under (the park: inside) the very place he starts from; `judge` tests the y (BLIND_DY).
  THE FED'S BALANCE (FED_WALK / FED_DIE; the third review's M1). A police player's game reads the OTHER float of each
of the three pairs (klbalance.c 2 a3). --fed-die: FedMirror=1, the hook writes the pairs exchanged and every key keeps
its name's meaning (live: FD3). Without it: FedMirror=0 for the game's own 550 of health - then nothing is exchanged
and CopToYou becomes 'a heister's bullet on the fed', CrewToCop 'a police AI's bullet on a heister': so NO CopToYou=20
(the hero's 27 of health die to one bullet at 1.0 too), and CrewToCop = CopToCrew = 0.005 so that the crew is
protected before and after his death - at the price that it cannot kill a policeman all round long. NOT RUN.
  WHAT THE GAME PICKS. The point is the game's: on a map with several groups (Retomoto: 3 + 2 + 2 points) a script
fits only the runs that get its group - if the pick is uniform (not read), 3 / 2 / 2 runs in 7.
  --rounds 2: `onwin` for round 2's page is armed PAGE_GONE_MS after `tap RETURN` (armed at once it would fire on
round 1's page if that were still up, and the script would 'PASS' there); `judge` counts the 0x19 lines.

OUTPUT of `script`: <out>.ini (complete: the tree's KLHook.expansion.ini block as mk_tab_inis.py writes it, the
gameplay sections of the lead's mkrun.py, [Auto], [Script]), <out>.route.txt (the route as `route` prints it),
<out>.expect.txt (the log lines that show each stage, in order) and <out>.plan.json (the same for `judge`: every
goto with its script line, the gotos that end by their timeout by design, a pattern for every stage's log line).
Outputs belong under <work>\research\playtest.
"""
import collections, glob, json, math, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as KB

WORK = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools'
OUT = os.path.join(WORK, 'research', 'playtest')

# ---- the rig's numbers (klauto.c; re\playtest.md 1)
SPRINT, WALK = 585.0, 400.0     # units a second: medians of the 'reached in N ms' lines of runs ESC3, N0b, VAN5, J2
LOAD_GO = (20.5, 22.1)          # s from 'level loaded' to session state 0x19 in the 67 runs with tonight's hook settings (re\playtest.md 1.2)
FREE_S = 10.4                   # s after session state 0x19 before the human can MOVE (the round's own countdown), at the most seen: in the seven
                                # runs that held W through it the rig saw his first 30 units of way 10.16 / 10.17 / 10.17 s after 0x19 (N0, N0b,
                                # VAN5) and he left the START place 10.25 .. 10.4 s after it (K1 / K2 / K2b_DM03_wall; K1 still stood there at
                                # 10.32; PT_DM03_die_r2: by 10.66). Until then a goto only wastes its timeout: the first way point of all four
                                # runs of this tool's first scripts was lost that way (9.5 s of 'goto is stuck', 'NOT reached')
FREE_PAD = 0.6                  # ... and this much more before the first goto
SCRIPT_MAX = 640                # kla_cmd[640]
TEXT_MAX = 79                   # KCMD.text[80]: a log / pos text is cut there
ROUND_S = 360.0                 # the Arcade round's clock (klfed.c's 'round clock 360 s'): a script cannot outlast it - the score page ends it
# ---- the rig's steering as a model (klauto.c C_GOTO; `rigfit` holds it against the logs of the walks that ran; re\playtest.md 1.4)
TURN_GAIN = 5.0                 # 1 / s: the mouse rate is the bearing error / TurnDeg x 5 ...
TURN_MAX = 1800 * 0.17          # ... clamped to 1800 counts a second at 0.17 degrees a count = 306 degrees a second
TURN_WIDE = 0.75 * TURN_MAX     # the pessimistic rate: the turning circle a third wider (100 at a walk, 146 at a sprint). At 220 the model
                                # misses 7 gotos the game reached and at 260 six, so the game does not turn slower than this
DECEL = 300.0                   # units / s^2 from a sprint to a walk when LSHIFT goes up (ESC3 script 40: 324 units in 0.656 s). To speed: at once
                                # (ESC1-3 / RN13 script 46, from a stand: 436 .. 447 units in 0.70 .. 0.72 s)
ROLL = 20.0                     # after W is let go he stands this much farther on (ESC3 scripts 40 and 67, VAN5 198: 19 .. 20, from a walk and a sprint)
STOP_MS = 600                   # the wait that makes a stop (ESC3: 15 of the 20 are done 0.73 s after 'reached', and the wait starts 2 polls after it)
STAND_TURN = 200.0              # degrees a second of turning before he walks, from a stand (VAN5 202: 118 degrees cost 0.6 s over the straight walk)
STAND_ARC = 0.3                 # s to full speed in the PESSIMISTIC reading of a start from a stand: no turn first, an arc (the review's replay)
ORBIT = 300.0                   # a goto that turns him by more than this many degrees in all is circling its target, not reaching it
DT = 1.0 / 60                   # the model's step
MESH_TOL = 0.5                  # a steered line or chord is 'off the mesh' when a sample lies this far outside it: any sample off it but for
                                # rounding on a shared corner (trace() itself has no tolerance; the review's chord is judged by trace())
MESH_SLACK = 25.0               # ... and under the wide rate when it lies this far outside: under a person's radius. GUESS that a wall stands that far out
R_MOVE = 60.0                   # no way point that is passed in motion has a radius under this (the review: 50; live in motion: 60 .. 200, and 24 straight ahead)
R_TIGHT = 25.0                  # a stop he must stand closer to: when the chord from R_STOP short of the way point (or ROLL less) still leaves the mesh.
                                # The least radius a goto gets here but for the wall's foot: 24 / 25 were reached live (the first scripts' line 50,
                                # four runs; VAN5 205), nothing smaller was tried, and a way point he MISSES is one he then circles. (A stop at 12
                                # was tried here: it takes 21 of the 35 turns that stay marked on the 35 routes off the list, by making a goto of
                                # radius 12 of each - the review's replay then circles more of them from a stand, not fewer)
AIM = 15.0                      # from a stand: the goto must also be reached when he starts to walk this many degrees off the line to it
# ---- places where something that is NOT in the mesh stands: known from live runs only. {map: [(x, z, radius, what was seen)]}. A 'way' place of
#      the bots inside one is not walked to (the way goes on to the next place over the mesh); a leg that passes one is said so in the print.
BLOCKED = {'M03_FA_A': [(-1237.0, -1504.0, 200.0, 'live, runs K2c_DM03_wall_hp and PB_DM03_board_hp (2026-10-11): the goto to it stuck 115 .. 140 short of it, at '
                                                   '(-1322, 220, -1580) and (-1288, 220, -1615), both times, and ran out; what stands in the bank\'s yard there is not known')]}
NEAR_BACK, BACK_DEG, R_BACK = 150.0, 120.0, 60.0    # from a stand: a target nearer than this and more than this many degrees off his heading wants a
                                # radius of this at least (ESC1-3 / RN13 script 73 reached one 128 away at 134 .. 140 degrees with radius 60, 1.3 s each)
# ---- the route rule
MARGIN = 60.0                   # a corner way point lies this far inside the shared edge from the mesh's corner. A person's radius is
                                # about 30 and a goto of radius r that turns by t cuts the corner by r * sin(t) (re\playtest.md 2). GUESS
DOOR = 2 * MARGIN + 30.0        # a shared edge shorter than this is a door: its middle is the way point
DOOR_CLEAR = 90.0               # ... when that middle is nearer than this to a border edge (else: a short edge in open ground)
KEEP_CLEAR = 50.0               # a soft way point goes when the line past it keeps this from every border edge
RISK_CLEAR = 30.0               # a leg nearer than this to a border edge is printed as risky (a person's radius)
END_ZONE = 80.0                 # ... measured without this much at either end: a door is narrow by itself (its own clearance is printed)
TIGHT = 20.0                    # a way point nearer than this to a border edge is printed as tight
LEG_MAX = 1500.0                # see the docstring
STEP = 12.0                     # trace(): one sample this often
FLOOR_JUMP = 90.0               # trace(): the next polygon's height may differ this much from the last sample's: a step (the bank's
                                # is 70), never a storey (350 and more). Heights by floor(), which is exact on shared edges
SLOPE = 0.12                    # a polygon steeper than this (rise per unit) is a stair / ramp / escalator
R_OPEN, R_TURN, R_HARD, R_STOP = 110.0, 70.0, 60.0, 40.0    # goto radius: open ground / a turn of 45 degrees or a door / a must-pass place / where he
                                # stops (before E; a door he has to turn in; a way point drive() makes a stop). Stops stand R_STOP - ROLL short of the place
ALIGN_TURN = 30.0               # degrees: a door the line turns at by more than this gets a way point on its axis, in front and / or behind
ALIGN_RUNS = (160.0, 120.0, 90.0)       # ... this far from the door's middle, the first that fits
START_FLOOR = (260.0, 40.0)     # a START point floats about 100 over the floor (kl_fa_bots.stations)
# ---- the escape vehicle (measured in tonight's logs, klbot.c's 'bots: ... van <state> <timer>' lines; re\playtest.md 3)
VAN_IN, VAN_STANDS, VAN_OUT, VAN_GAP = 7.6, 7.7, 8.7, 5.5        # seconds in state 1 / 3 / 5 / 7; one visit every 29.5 s while somebody calls
VAN_SIDE = 230.0                # the human waits this far to the side of the van's axis, level with its rear doors: body 100 (kl_fa_bots
                                # LANE_HALF) + a man 60 (LANE_MAN) + 70. GUESS for the 70
E_HOLD = 2500                   # ms the use key is held at the doors (run ESC3 boarded with 'tap E, then E for 2 s')
LOOT_HOLD = 4.0                 # s of E at a money object (runs RN7 / ESC1 - ESC3: 3.5 .. 5 s paid, 1.5 s did not)
# ---- the climb (klhook\klclimb.c: at the foot = over 15 and at most 70 from the face (KLQ_NEAR / KLQ_FAR), within 40 of Floor=, slower than
#      150 a second, looking at the face within 60 degrees, for 400 ms; Key=0: no key is asked - a scripted key is not seen by GetAsyncKeyState)
CLIMB_STAND = 40.0              # he is aimed at this far from the face; the goto's radius is 20, so he lets go of W 60 from it at most
CLIMB_RUN = 300.0               # ... from this far back, at square to the face, so that he arrives looking at it
DIE_SIGHT = 2000.0              # --die: a guard counts when a straight line on the mesh reaches him within this. GUESS for 'he is seen'
DIE_NEAR = 700.0                # --die: ... and he stands at the first way point that has one this near (the bank's hall: 6.4 m from a guard,
                                # where the scripted player of runs RN6 / RN13 was down 10 .. 25 s after he came in at the STOCK damage)
WAY_NUDGE = 120.0               # a bot's 'way' place nearer than MARGIN to a border edge is moved up to this far, to where the mesh is wider
JOIN_BACK, JOIN_IN, JOIN_W = 110.0, 40.0, 800      # Retomoto's jump box: the goto ends this far in front of a face; W for this many ms then carries
                                                   # him at least JOIN_IN into it (walk 400 a second: 320 of way against 30 + 110 + 40)
JOIN_RUN = 250.0                                   # ... after this much of a run on the line into the box (the turn is over in 0.5 s = 200)
JOIN_SLOP = 15.0                                   # ... and W must take him in when he looks this many degrees to either side of that line
STAGE_DETOUR = 150.0            # a stage box's own bot place is left out when it costs more than this and the way crosses the box anyway
BOX_SHARE = 0.9                 # a ZBoxPrimitive's three size values are HALF sizes - LOOSELY shown: live, run H0_DM03, a bot got heist stage 3
                                # 0.2 s after its node was at z -655 going north, and Triggers!ExitTrigger_01 (middle z 460, size value 1000)
                                # begins at z -540 by that reading and at -40 by the other; the one instance fits the half-size reading to
                                # 100 .. 200 units, not better (the review). 0.9: a tenth of margin
GLASS_NEAR = 200.0              # a shatter-glass door pane (ShotActivate) within this of a leg and ahead on it: said in the route; --shoot: he fires on that leg
GLASS_RUN = 250.0               # ... over its last stretch of this length, at a walk
LOOT_NEAR = 1500.0              # a money object belongs to a loot stop within this of the bot's loot place (the bots' loot window is 800)
LOOT_OFF = 40.0                 # he stands at least this far from a money object's own place (it is a thing he would run into)
LOOT_PUSH, LOOT_PUSH_MS = 120.0, 1200     # a money object whose trigger the mesh does not reach: a mesh place up to this far outside it, then a goto
                                          # straight at the object for this long (under the 1.5 s after which a goto side-steps)
# ---- the third round (2026-10-11; re\playtest.md 10)
FIRST_TIMEOUT = 20000           # ms: the first goto of a round. Should a map's countdown outlast the wait, W is held until he can move
PB_REACH = 160.0                # kl2 0x8c62e0: a firing soldier's target within this (node to node, 3-D) gets the x100 step (re\melee_damage.md 2)
PB_POST = 400.0                 # R1: no stop / walk within this of an armed enemy's post: PB_REACH + 240 for his own steps round it. GUESS for the 240
GUARD_RUN = 300.0               # R2: a hunting guard's way along the mesh, units a second, from the human's stage 1 on. MEASURED on the bank only (5 runs:
                                # the first step of each gun against its carrier's mesh way from his post - Type 79 2,128 / 2,904 in 7.4 .. 11.4 s, the
                                # .45 3,226 in 12.5 .. 15, the Sig 3,890 in 13.4, the shotgun 2,430 in 15: 160 .. 390, most 215 .. 300); a GUESS elsewhere
COP_DIAL = 0.001                # [Balance] CopToYou / CrewToYou of a route script: a point-blank step is then 7.6 (Type 79) .. 37.9 (the .45) of 5,500
# way points a LIVE run walked IN MOTION although the model asks for a stop there: {map: [(x, z, goto radius, sprint)]}. The bank's stairs from
# the hall down to the garage: runs K1 / K2 / K2b (the first five, until his death) and K2c (all nine) of the first scripts, whose gotos there had
# these radii and `keep` - every one reached, the staircase in 3.7 s (K2c) against 7.4 .. 8.0 s with the five real stops (PB, FO_J1, FO_J3)
LIVE_MOVING = {'M03_FA_A': [(-990, -6072, 40, False), (-997, -5912, 70, False), (-960, -5791, 35, False), (-797, -5680, 35, False), (-321, -5692, 70, False),
                            (-322, -5910, 70, False), (-875, -5945, 70, True), (-950, -6400, 70, True), (-914, -6915, 70, True)]}
DIE_STAND = 110.0               # --die: he stands this far from the chosen guard's post (inside PB_REACH with 50 to spare)
DIE_REACH = 2500.0              # --die: ... the guard whose post is within this of mesh way from a way point of the route, the first on the route
DIE_WAIT = 20.0                 # --fed-walk: seconds at the --die place before the fed's gotos begin: live he was dead 8 .. 15 s after he could move
                                # (PT_DM03_die_r2 / _f2, FD3_DM03_die: on the way, before he stood) and police 5.0 s after that. The hero's gotos that
                                # are left when he dies run out first (each to its timeout, steering the new body at the old way points): the wait
                                # is for the case that he reaches the place alive
DIE_GOTO = (1.5, 2.5, 4000)     # --die --fed-walk, rig2: the timeout of a goto of the HERO = 1.5 x the model's time + 2.5 s, at least 4 s (any other
                                # goto: 3 x + 4 s, at least 6 s). Room for one 'stuck' side step (1.5 + 0.7 s); the model's time was within 0.1 s of
                                # the log for 8 gotos in 10 (rigfit). NOT RUN with these
PAGE_GONE_MS = 3000             # --rounds 2: between `tap RETURN` on the score page and the `onwin` for the next round's page (review 3, S4)
BLIND_DY = 150.0              # a fed's BLIND goto shows a way down only when his `pos` after it is within this of the crew's mesh height there
FED_GROUP = 1500.0              # AFTER_DEATH points nearer than this to another (3-D) are one group
FED_PAD = 1800.0                # the collision is read this far round a group and its way
FED_BLIND, FED_BLIND_MS = 3, 6000   # where neither mesh nor collision joins the crew's part: this many gotos toward it, each this long
FED_SPAWN_UNDER = (260.0, 60.0)     # a spawn point floats: the floor is looked for this far below / above it
CLEAR_MIN = 450.0               # --clear: he stands at least this far from the van's line, its boarding box and the bots' AllyEscapeBox
R_ = 'ROOT\\'


def cross2(o, a, b):
    """> 0: b lies to the LEFT of a seen from o, in the plan (x east, z north)."""
    return (a[0] - o[0]) * (b[2] - o[2]) - (a[2] - o[2]) * (b[0] - o[0])


def d2(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ------------------------------------------------------------------ a build, read light
class Light(KB.Built):
    """kl_fa_bots.Built with three members of the archive only (.gms .buf .prp: 0.4 s instead of the whole 200 MB)."""

    def __init__(self, src):
        self.folder = src if os.path.isdir(src) else os.path.dirname(src)
        zs = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(src, '*_Main.zip')))
        if len(zs) != 1:
            raise SystemExit('%s: %d level archives (*_Main.zip) - expected one' % (src, len(zs)))
        self.zp = zs[0]
        with zipfile.ZipFile(self.zp) as z:
            self.order = z.namelist()
            self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
            self.files = {self.ext[e]: z.read(self.ext[e]) for e in ('.gms', '.buf', '.prp')}
        raw, buf = KB.kl_gms.unpack(self['.gms']), self['.buf']
        names, tids = ['ROOT'], [KB.kl_rtp.ROOT_TYPE]
        for decl, tid, _prio in KB.kl_gms.entities(raw):
            o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        self.sc = KB.J.Scene(KB.Prp(self['.prp']), names, tids, 'dd', os.path.basename(self.zp))
        self.scene = KB.kl_scene.Scene(raw, buf)
        self.ents = list(self.scene.entities())
        if [e.name.decode('latin1') for e in self.ents] != names[1:]:
            raise ValueError('%s: .gms and .prp disagree on the entities' % self.zp)
        self.fr = KB.frames(self.scene)
        rj = os.path.join(self.folder, 'result.json')
        self.result = json.load(open(rj)) if os.path.isfile(rj) else {}


class Level:
    """A build folder: the scene, the mesh, the bots' plan, the hook's side file."""

    def __init__(self, folder, info=None):
        self.folder = folder
        self.B = Light(folder)
        info = info or folder
        bj = os.path.join(info, 'bots.json')
        if not os.path.isfile(bj):
            raise SystemExit('%s: no bots.json (the AI heisters\' plan the route is taken from)' % info)
        self.bots = json.load(open(bj))
        self.plan = self.bots['plan']
        self.map = self.plan.get('map') or self.B.result.get('M') or '?'
        self.rt = self.plan.get('rt')                                   # Retomoto: tower + street
        drops = bool((self.plan.get('edits') or {}).get('drops'))       # the plan was made with the mesh's links (the bank's drop)
        self.nav = KB.Nav(self.B.scene.nav, links=drops)
        self.st = KB.stations(self.B, self.nav)
        self.home = self.st['home']
        jp = os.path.join(folder, 'KLJoin.ini')
        self.join_ini = open(jp).read() if os.path.isfile(jp) else ''
        self.vans = KB.van_drives(self.B)
        self._money = None

    def money(self):
        if self._money is None:
            self._money = KB.money_objects(self.B)
        return self._money

    def ini_sections(self, name):
        """[name], [name.2] .. of KLJoin.ini -> [dict of its keys]."""
        out, cur = [], None
        for line in self.join_ini.splitlines():
            line = line.strip()
            m = re.match(r'\[(.+?)\]$', line)
            if m:
                cur = None
                if re.match(r'%s(\.\d+)?$' % re.escape(name), m.group(1)):
                    cur = {}; out.append(cur)
            elif cur is not None and '=' in line and not line.startswith(';'):
                k, v = line.split('=', 1)
                cur[k.strip()] = v.strip()
        return out

    def hvk(self):
        """The level's Havok file (kl_hvk.Hvk), read when the collision is asked for."""
        if getattr(self, '_hvk', None) is None:
            import kl_hvk
            with zipfile.ZipFile(self.B.zp) as z:
                self._hvk = kl_hvk.Hvk(z.read(next(n for n in z.namelist() if n.lower().endswith('_main.hvk'))))
        return self._hvk

    def refs(self):
        """{REF label: node} of the build's entities (a collision shape names its entity by that)."""
        if getattr(self, '_refs', None) is None:
            self._refs = {e.ref: i + 1 for i, e in enumerate(self.B.ents)}
        return self._refs

    def soldiers(self):
        """The armed Enemy soldiers as the level places them -> [dict node, name, at, weapon, squad (node or None),
        active (ZSquadScript field 3: in the world when the level loads), attitude (field 0), hunts (the squad has a
        hunt or flanking rout), place (x, y, z, polygon on the mesh or None), g (one bullet of his gun on a body at
        arm's length before any factor: kl_map_ai.bullet; None when the gun is not read)]."""
        if getattr(self, '_soldiers', None) is not None:
            return self._soldiers
        B, sc, nav = self.B, self.B.sc, self.nav
        sq, guns = {}, {}
        for t, _i, v in kl_fa.controllers(sc, 'ZSquadScript'):
            hunts = any(sc.p.key(nm) in ('HuntBehaviourRout', 'FlankingBehaviourRout') for k in range(t + 1, sc.end[t]) for nm, _b in sc.nodes[k]['ctrls'])
            for k in range(t + 1, sc.end[t]):
                sq[k] = (t, v[0], v[3], hunts)
        try:
            import kl_map_ai as MA
            for n, g in MA.guns(sc).items():
                guns[n] = MA.bullet(g, 1.0, True)
        except Exception as e:                           # the gun table is a nicety: the rule does not need it
            self.gun_note = 'the gun templates were not read (%s: %s)' % (type(e).__name__, e)
        out = []
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) != 'ZFFActor' or not any(sc.p.key(nm) == 'ZSoldier' for nm, _b in sc.nodes[k]['ctrls']):
                continue
            v = B.values(k)
            w = (v['ZFFActor[1]'] or '').rsplit('\\', 1)[-1] if isinstance(v['ZFFActor[1]'], str) else ''
            if v['ZFFActor[0]'] != 'Enemy' or not w:
                continue
            p = B.at(k)
            t, att, act, hunts = sq.get(k, (None, '?', 1, False))
            a = snap(nav, p, dy=200.0) or nearest(nav, p, 200.0, dy=260.0)
            out.append(dict(node=k, name=sc.path[k][5:], at=p, weapon=w, squad=t, active=bool(act), attitude=att, hunts=hunts, place=a, g=guns.get(w)))
        self._soldiers = out
        return out

    def dead_points(self):
        """The FRAGILE_ALLIANCE_AFTER_DEATH spawn points (where a police PLAYER appears: kl2 0x518e30 takes a random
        free one) -> [(node, place, heading of its +Z as klauto logs one)]."""
        B, sc, out = self.B, self.B.sc, []
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZSpawnPoint' and any(isinstance(x, str) and x == kl_fa.DEAD for x in kl_fa.node_values(sc, k)):
                Rm = B.fr[B.ents[k - 1]][0]
                out.append((k, B.at(k), math.degrees(math.atan2(Rm[0][2], Rm[2][2]))))
        return out

    def walk(self, box):
        """kl_escape.Walk (where a character can walk by the collision alone) over box = (x0, x1, z0, z1)."""
        import kl_escape
        return kl_escape.Walk(self.hvk(), box)


def vec(text):
    return tuple(float(v) for v in re.split(r'[\s,]+', text.strip()) if v)


# ------------------------------------------------------------------ the mesh: a place, a line, a corridor
def at(nav, x, y, z, dy=KB.DY, part=None, lo=None, hi=None):
    """(polygon, its height there) under (x, z) whose height is nearest to y and within dy of it (or within lo .. hi),
    of `part` only when given; None off the mesh. kl_fa_bots.Nav.at with floor() for the height: its fitted plane
    puts Late Night Opening's two stacked escalators (six-sided polygons, a landing and a ramp) 500 off, so that a
    place on the lower one is found on the upper."""
    best = None
    for i, b in enumerate(nav.box):
        if nav.ok[i] and b[0] <= x <= b[1] and b[2] <= z <= b[3] and (part is None or nav.part[i] == part) and nav.inside(i, x, z):
            h = floor(nav, i, x, z)
            if (lo is None and abs(h - y) <= dy) or (lo is not None and lo <= h <= hi):
                if best is None or abs(h - y) < abs(best[1] - y):
                    best = (i, h)
    return best


def snap(nav, p, part=None, dy=KB.DY, under=None):
    """(x, height, z, polygon) of the mesh under p, or None. under = (below, above): look for a floor in that range
    (a START point floats)."""
    hit = at(nav, p[0], p[1], p[2], part=part, lo=p[1] - under[0], hi=p[1] + under[1]) if under else at(nav, p[0], p[1], p[2], dy=dy, part=part)
    return (p[0], hit[1], p[2], hit[0]) if hit else None


def around(nav, p, radius, part=None, step=20.0, dy=200.0):
    """The mesh places on a grid of `step` within `radius` of p in the plan, each (x, height, z, polygon)."""
    out, k = [], int(radius // step)
    for ix in range(-k, k + 1):
        for iz in range(-k, k + 1):
            if math.hypot(ix, iz) * step > radius:
                continue
            x, z = p[0] + ix * step, p[2] + iz * step
            hit = at(nav, x, p[1], z, dy, part)
            if hit:
                out.append((x, hit[1], z, hit[0]))
    return out


def nearest(nav, p, reach, part=None, dy=200.0, need=RISK_CLEAR):
    """The mesh place nearest to p within `reach` in the plan (a grid of 20), with `need` to the border when one has it."""
    c = around(nav, p, reach, part, dy=dy)
    if not c:
        return None
    good = [q for q in c if clear(nav, q[0], q[1], q[2]) >= need]
    return min(good or c, key=lambda q: d2(q, p))


CELL = 400.0


def clear(nav, x, y, z, limit=400.0):
    """Distance in the plan from (x, y, z) to the nearest border edge of the mesh (an edge without a neighbour) that
    is within 150 of its height there; at most `limit` (never over 400). As kl_fa_bots.Nav.clearance, with the edge's
    own height at its nearest point (a ramp's border is not at one height) and a grid over the edges."""
    g = getattr(nav, '_pt_grid', None)
    if g is None:
        g = collections.defaultdict(list)
        for i, vs in enumerate(nav.pv):
            if not nav.ok[i]:
                continue
            for e, j in enumerate(nav.en[i]):
                if j >= 0:
                    continue
                a, b = vs[e], vs[(e + 1) % len(vs)]
                for cx in range(int(math.floor((min(a[0], b[0]) - 400.0) / CELL)), int(math.floor((max(a[0], b[0]) + 400.0) / CELL)) + 1):
                    for cz in range(int(math.floor((min(a[2], b[2]) - 400.0) / CELL)), int(math.floor((max(a[2], b[2]) + 400.0) / CELL)) + 1):
                        g[(cx, cz)].append((a, b))
        nav._pt_grid = g
    best = min(limit, 400.0)
    for a, b in g.get((int(math.floor(x / CELL)), int(math.floor(z / CELL))), ()):
        dx, dz = b[0] - a[0], b[2] - a[2]
        LL = dx * dx + dz * dz
        t = 0.0 if LL < 1e-9 else max(0.0, min(1.0, ((x - a[0]) * dx + (z - a[2]) * dz) / LL))
        if abs(a[1] + t * (b[1] - a[1]) - y) > 150.0:
            continue
        best = min(best, math.hypot(x - a[0] - t * dx, z - a[2] - t * dz))
    return best


def floor(nav, i, x, z):
    """Height of polygon i at (x, z): between its middle and the two corners of the fan triangle the point lies in.
    kl_fa_bots.Nav.height fits a plane to three corners, which is off by hundreds on a polygon that is not flat (the
    park's ground, the bank's street, Retomoto's window, the escalators); this one is exact on every edge, so two
    polygons agree on the edge they share. INSIDE a polygon that is not flat it is an estimate too (the review: on the
    mall's lower escalator at (913, 813) it says 468, a fan from corner 0 says 396, a bot's own place there 399)."""
    vs, c = nav.pv[i], nav.mid[i]
    best = None
    for k in range(len(vs)):
        a, b = vs[k], vs[(k + 1) % len(vs)]
        den = (a[0] - c[0]) * (b[2] - c[2]) - (a[2] - c[2]) * (b[0] - c[0])
        if abs(den) < 1e-9:
            continue
        u = ((x - c[0]) * (b[2] - c[2]) - (z - c[2]) * (b[0] - c[0])) / den
        v = ((a[0] - c[0]) * (z - c[2]) - (a[2] - c[2]) * (x - c[0])) / den
        out = max(0.0, -u) + max(0.0, -v) + max(0.0, u + v - 1.0)        # 0 inside this triangle
        if best is None or out < best[0]:
            best = (out, c[1] + u * (a[1] - c[1]) + v * (b[1] - c[1]))
            if out == 0.0:
                break
    return best[1] if best else c[1]


def steep(nav, i):
    """Is polygon i a stair / ramp: its corners' heights against its size in the plan."""
    vs = nav.pv[i]
    ys = [v[1] for v in vs]
    return (max(ys) - min(ys)) / max(1.0, max(d2(a, b) for a in vs for b in vs)) > SLOPE


def ring_find(nav, cur, h, x, z):
    """The polygon under (x, z) that is reached from polygon `cur` over shared edges: up to three rings of neighbours,
    its height there within FLOOR_JUMP of h; the nearest in height of the first ring that has one. None: off the mesh."""
    seen, ring, found, best = {cur}, [cur], None, 0.0
    for _depth in range(3):
        nxt = []
        for i in ring:
            for j in nav.nb[i]:
                if j in seen or not nav.ok[j]:
                    continue
                seen.add(j); nxt.append(j)
                if nav.inside(j, x, z):
                    dh = abs(floor(nav, j, x, z) - h)
                    if dh <= FLOOR_JUMP and (found is None or dh < best):
                        found, best = j, dh
        if found is not None:
            return found
        ring = nxt
    return None


class Foot:
    """A place that is followed over the mesh as it moves (the polygon it is on, the height there)."""

    def __init__(self, nav, p):
        self.nav, self.cur, self.h = nav, p[3], p[1]
        if self.cur is not None:
            self.h = floor(nav, self.cur, p[0], p[2])

    def copy(self):
        f = Foot.__new__(Foot)
        f.nav, f.cur, f.h = self.nav, self.cur, self.h
        return f

    def find(self, x, z):
        """Look for the mesh under (x, z) anywhere near the height he has (a goto starts here after one that ended off it)."""
        hit = at(self.nav, x, self.h, z, dy=FLOOR_JUMP)
        if hit:
            self.cur, self.h = hit
        return hit is not None

    def to(self, x, z):
        """Move to (x, z) -> 0.0 when that is on the mesh (trace()'s step: this polygon or one within three rings), else
        how far outside it the place lies: the distance to the nearest border edge (the polygon is kept)."""
        nav = self.nav
        if self.cur is None:
            return 400.0
        if not nav.inside(self.cur, x, z):
            j = ring_find(nav, self.cur, self.h, x, z)
            if j is None:
                return max(0.1, clear(nav, x, self.h, z))
            self.cur = j
        self.h = floor(nav, self.cur, x, z)
        return 0.0


def wrap(a):
    """An angle in degrees into -180 .. 180."""
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a


def bearing(x, z, tx, tz):
    """The heading from (x, z) to (tx, tz) as klauto logs one: degrees, 0 = +z, 90 = +x."""
    return math.degrees(math.atan2(tx - x, tz - z))


def steer(x, z, head, v0, tx, tz, r, v, omega=TURN_MAX, foot=None, ramp=0.0, limit=25.0, path=None):
    """klauto's goto as a model (C_GOTO): every step the heading turns by TURN_GAIN x the bearing error, at most `omega`
    degrees a second, and he moves v along it; 'reached' when the distance in the plan is <= r. v0 = his speed when it
    starts (a sprint decays to a walk by DECEL; faster is at once), ramp = seconds from 0 to v (the pessimistic start
    from a stand). foot: a Foot that is moved along. path: a list that gets every (x, z, the mesh's height there or None).
    -> dict reached, t, x, z, head, v, turned (degrees in all), near (least distance to the target), off (how far outside
    the mesh the deepest sample lay), off_way (units of way off it)."""
    t, sp, turned, near, off, off_way = 0.0, max(v0, 0.0), 0.0, 1e9, 0.0, 0.0
    while True:
        d = math.hypot(tx - x, tz - z)
        near = min(near, d)
        if d <= r:
            return dict(reached=True, t=t, x=x, z=z, head=head, v=sp, turned=turned, near=near, off=off, off_way=off_way)
        if t >= limit or turned > 2 * 360.0:
            return dict(reached=False, t=t, x=x, z=z, head=head, v=sp, turned=turned, near=near, off=off, off_way=off_way)
        rate = max(-omega, min(omega, TURN_GAIN * wrap(bearing(x, z, tx, tz) - head)))
        head = wrap(head + rate * DT)
        turned += abs(rate) * DT
        if ramp > 0.0 and t < ramp:
            sp = v * (t + DT) / ramp
        elif sp > v:
            sp = max(v, sp - DECEL * DT)
        else:
            sp = v
        x += math.sin(math.radians(head)) * sp * DT
        z += math.cos(math.radians(head)) * sp * DT
        t += DT
        if foot is not None:
            dep = foot.to(x, z)
            if dep > 0.0:
                off, off_way = max(off, dep), off_way + sp * DT
        if path is not None:
            path.append((x, z, None if foot is None else foot.h))


def line_off(foot, x, z, tx, tz, r=0.0):
    """Follow the straight line from (x, z) to where it comes within r of (tx, tz) with a copy of `foot`, a sample every
    STEP -> (how far outside the mesh the deepest sample lay, units of the line off it, the copy at its end)."""
    f, L = foot.copy(), math.hypot(tx - x, tz - z)
    n = max(1, int(max(0.0, L - r) // STEP))
    off = way = 0.0
    for k in range(1, n + 1):
        t = (L - r) * k / n / L if L > 1e-6 else 0.0
        dep = f.to(x + (tx - x) * t, z + (tz - z) * t)
        if dep > 0.0:
            off, way = max(off, dep), way + (L - r) / n
    return off, way, f


def cannot_turn_in(d, off, r, v, omega=TURN_MAX):
    """The exact test, no simulation: a target d away and `off` degrees off his heading, radius r, at speed v. The
    tightest circle he can walk has radius rho = v / omega; the target is never reached when it lies inside that circle
    on its side by more than r. -> how far inside (> 0: unreachable in motion), else 0."""
    rho = v / math.radians(omega)
    if r >= rho:
        return 0.0
    a = math.radians(abs(off))
    dc = math.sqrt(max(0.0, rho * rho - 2.0 * rho * d * math.sin(a) + d * d))        # from the circle's middle to the target
    return max(0.0, rho - r - dc)


def trace(nav, a, b):
    """Walk the straight line from a = (x, y, z, polygon) to b = (x, y, z[, polygon]) on the mesh, a sample every STEP:
    from polygon to polygon over shared edges (up to three rings of neighbours, the height within FLOOR_JUMP of the
    last sample's). -> dict ok, way (how far it got), end (x, y, z, polygon), clear (least distance to a border edge
    on the way, at most 400), mid (the same without the first and the last END_ZONE of the line: what the LINE costs,
    apart from how narrow its two ends are), slopes [(distance, 'slope' | 'level')] where the floor's class changes,
    polys (the polygons in order)."""
    L = d2(a, b)
    n = max(1, int(L // STEP))
    cur, h = a[3], floor(nav, a[3], a[0], a[2])
    out = {'ok': True, 'way': 0.0, 'end': (a[0], h, a[2], cur), 'clear': 400.0, 'mid': 400.0, 'slopes': [], 'polys': [cur], 'len': L}
    was = steep(nav, cur)
    for t in range(n + 1):
        x, z = a[0] + (b[0] - a[0]) * t / n, a[2] + (b[2] - a[2]) * t / n
        if not nav.inside(cur, x, z):
            found = ring_find(nav, cur, h, x, z)
            if found is None:
                out['ok'] = False
                return out
            cur = found
            out['polys'].append(cur)
            if steep(nav, cur) != was:
                was = steep(nav, cur)
                out['slopes'].append((L * t / n, 'slope' if was else 'level'))
        h = floor(nav, cur, x, z)
        out['way'], out['end'] = L * t / n, (x, h, z, cur)
        c = clear(nav, x, h, z)
        out['clear'] = min(out['clear'], c)
        if L * t / n > END_ZONE and L - L * t / n > END_ZONE:
            out['mid'] = min(out['mid'], c)
    if L <= 2 * END_ZONE:
        out['mid'] = out['clear']                       # a short line is all end
    return out


def shared_edge(nav, i, j):
    """The two ends (x, y, z) of the edge polygons i and j share, or None."""
    for a, b in ((i, j), (j, i)):
        vs = nav.pv[a]
        for e, n in enumerate(nav.en[a]):
            if n == b:
                return vs[e], vs[(e + 1) % len(vs)]
    return None


def corridor(nav, a, b):
    """The polygon corridor from a to b (both (x, y, z, polygon)) -> [piece] or None (no way). A piece is
    ('mesh', start, goal, [polygons]) or ('drop', take-off, landing): a link of the mesh, walked one way."""
    dist, prev, _at = nav.dist_map(a[3], a[:3])
    if b[3] not in dist:
        return None
    steps, i = [], b[3]
    while i != a[3]:
        st = prev[i]
        steps.append((st[0], i, st[1:]))
        i = st[0]
    steps.reverse()
    out, start, polys = [], a, [a[3]]
    for frm, to, how in steps:
        if len(how) == 2:                               # (landing, take-off)
            land, take = how
            out.append(('mesh', start, tuple(take) + (frm,), polys))
            out.append(('drop', tuple(take) + (frm,), tuple(land) + (to,)))
            start, polys = tuple(land) + (to,), [to]
        else:
            polys.append(to)
    out.append(('mesh', start, b, polys))
    return out


def funnel(nav, a, b, polys):
    """The shortest line from a to b inside the polygon corridor `polys`, every shared edge drawn in by MARGIN from
    both ends (a shared edge shorter than DOOR: its middle). -> [((x, y, z), kind, polygon, axis)] without a and b;
    kind 'corner' or 'door', polygon = the one the line enters there, axis = for a door the direction through it, at
    square to its edge. A 'door' whose middle has DOOR_CLEAR to every border edge is a short shared edge in open
    ground, not a door: it is called a corner (and may be dropped later)."""
    portals = [(a[:3], a[:3], None, polys[0], None)]
    for i, j in zip(polys, polys[1:]):
        e = shared_edge(nav, i, j)
        if e is None:
            m = nav.portal(i, j)
            portals.append((m, m, 'door', j, None))
            continue
        u, v = e
        w = d2(u, v)
        axis = None
        if w < DOOR:
            m = lerp(u, v, 0.5)
            L = R = m
            kind = 'door' if clear(nav, m[0], m[1], m[2]) < DOOR_CLEAR else 'corner'
            if kind == 'door' and w > 1e-3:             # the way through a door: at square to the edge, from polygon i into j
                axis = (-(v[2] - u[2]) / w, (v[0] - u[0]) / w)
                if axis[0] * (m[0] - nav.mid[i][0]) + axis[1] * (m[2] - nav.mid[i][2]) < 0:
                    axis = (-axis[0], -axis[1])
        else:
            u2, v2 = lerp(u, v, MARGIN / w), lerp(u, v, 1.0 - MARGIN / w)
            c, m = nav.mid[i], lerp(u, v, 0.5)
            L, R = (u2, v2) if cross2(c, m, u2) > 0 else (v2, u2)
            kind = 'corner'
        portals.append((L, R, kind, j, axis))
    portals.append((b[:3], b[:3], None, polys[-1], None))
    same = lambda p, q: abs(p[0] - q[0]) < 1e-6 and abs(p[2] - q[2]) < 1e-6
    out, apex, left, right, li, ri, i, guard = [], a[:3], a[:3], a[:3], 0, 0, 1, 0
    while i < len(portals) and guard < 100000:
        guard += 1
        L, R = portals[i][:2]
        if cross2(apex, right, R) >= 0:                 # the right side narrows
            if same(apex, right) or cross2(apex, left, R) < 0:
                right, ri = R, i
            else:                                       # ... past the left side: the left end is a corner
                out.append((left, portals[li][2] or 'corner', portals[li][3], portals[li][4]))
                apex, i = left, li + 1
                left, right, ri = apex, apex, li
                continue
        if cross2(apex, left, L) <= 0:
            if same(apex, left) or cross2(apex, right, L) > 0:
                left, li = L, i
            else:
                out.append((right, portals[ri][2] or 'corner', portals[ri][3], portals[ri][4]))
                apex, i = right, ri + 1
                left, right, li = apex, apex, ri
                continue
        i += 1
    return [(p, k, poly, axis) for p, k, poly, axis in out if not same(p, a) and not same(p, b)]


def way(nav, a, b):
    """The player's line from a to b over the mesh -> [dict p, kind] (b included, a not) or None. A drop link gives a
    'drop' point (the take-off) and a 'land' point."""
    cor = corridor(nav, a, b)
    if cor is None:
        return None
    out = []
    for n, piece in enumerate(cor):
        if piece[0] == 'drop':
            out.append({'p': piece[2][:3], 'kind': 'land', 'poly': piece[2][3]})
            continue
        _m, s, g, polys = piece
        out += [{'p': p, 'kind': k, 'poly': poly, 'axis': axis} for p, k, poly, axis in funnel(nav, s, g, polys)]
        out.append({'p': g[:3], 'kind': 'goal' if n == len(cor) - 1 else 'drop', 'poly': g[3]})
    return out


# ------------------------------------------------------------------ the fed: where a police player appears, and his way to the crew
def crew_places(L, bot=2):
    """The crew's places on the mesh, in the order of the round -> [(kind, (x, y, z, polygon), what)]: the START row's
    middle, then the stations of bots.json (the bot's own place of each), Retomoto's street stations too."""
    nav, plan, out = L.nav, L.plan, []
    me = plan['bots'].get(str(bot)) or next(iter(plan['bots'].values()))
    mid = tuple(sum(p[i] for p, _f in L.st['starts']) / len(L.st['starts']) for i in range(3))
    rows = [('start', mid, 'the START row')]
    for i, st in enumerate(plan['stations']):
        rows.append((st['kind'], tuple(me['places'][i]) if i < len(me['places']) else tuple(st['places'][0]), st['what']))
    if L.rt:
        rows += [(st['kind'], tuple(st['places'][0]), 'street: ' + st['what']) for st in L.rt['street']['stations']]
    for kind, p, what in rows:
        q = snap(nav, p, under=START_FLOOR) if kind == 'start' else (snap(nav, p) or nearest(nav, p, 150.0))
        if q:
            out.append((kind, q, what))
    return out


def coll_floor(W, p, under=FED_SPAWN_UNDER):
    """The floor of the collision a body put at p comes to stand on: the highest floor sample of p's cell that is not
    more than under[1] above p (a spawn point floats) -> (height or None, every floor of the cell)."""
    fl = sorted(y for y, f, _r in W.grid.get(W.cell(p[0], p[2]), ()) if f)
    below = [y for y in fl if y <= p[1] + under[1]]
    return (below[-1] if below else None), fl


def coll_line(W, seen, a, b):
    """Can the straight line a -> b be walked over the cells the flood reached: every cell on it reached, no step over
    the walk test's own limits."""
    n = max(1, int(d2(a, b) // (W.CELL / 2)))
    last = None
    for t in range(n + 1):
        c = W.cell(a[0] + (b[0] - a[0]) * t / n, a[2] + (b[2] - a[2]) * t / n)
        if c not in seen or (last is not None and not -W.DOWN <= seen[c] - last <= W.UP):
            return False
        last = seen[c]
    return True


def fed_facts(L, group=1, to='loot', bot=2, log=None):
    """What is known OFFLINE about the place a police PLAYER appears at, and his way to the crew -> dict:
    points [dict n, name, at, head, mesh (polygon, height, part) under it or None, off (distance in the plan to the
    nearest polygon of a crew part, when none is under it), floor (the collision's, or None), floors, group],
    groups [[n]] (the largest first), group (the chosen one's n), crew_parts, seen / W (the walk test's flood from the
    group and the test itself; None when no point of the group has a floor), area, bounds, blockers [(name, cells)],
    reached {kind: bool} (the crew's places by the collision alone), entries + heads (the group's points when every one
    stands over a crew part), pre [(x, y, z)] (the collision's way to the mesh, when they do not and the flood gets
    there), join (x, y, z, polygon), blind [(x, y, z)] (when nothing joins), goal (kind, place, what), notes."""
    B, sc, nav = L.B, L.B.sc, L.nav
    F = dict(points=[], groups=[], group=[], notes=[], pre=[], blind=[], entries=[], heads=[], join=None, goal=None, seen=None, W=None, blockers=[], reached={},
             area=0.0, bounds=None, edge=None)
    crew = crew_places(L, bot)
    parts = {nav.part[q[3]] for _k, q, _w in crew}
    F['crew_parts'], F['crew'] = parts, crew
    dead = L.dead_points()
    if not dead:
        F['notes'].append('the build has no FRAGILE_ALLIANCE_AFTER_DEATH spawn point: a fed stays where the level put the police body')
        return F
    for n, (k, p, head) in enumerate(dead):
        under = []
        for i, b in enumerate(nav.box):
            if nav.ok[i] and b[0] <= p[0] <= b[1] and b[2] <= p[2] <= b[3] and nav.inside(i, p[0], p[2]):
                h = floor(nav, i, p[0], p[2])
                if p[1] - FED_SPAWN_UNDER[0] <= h <= p[1] + FED_SPAWN_UNDER[1]:
                    under.append((nav.part[i] not in parts, abs(h - p[1]), i, h))
        m = min(under)[2:] if under else None
        off = None
        if m is None or nav.part[m[0]] not in parts:
            c = [(math.hypot(nav.mid[i][0] - p[0], nav.mid[i][2] - p[2]), nav.mid[i][1] - p[1], i) for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] in parts]
            off = min(c) if c else None
        F['points'].append(dict(n=n + 1, node=k, name=sc.path[k][5:], at=p, head=head, mesh=(m[0], m[1], nav.part[m[0]]) if m else None, off=off, floor=None, floors=[]))
    left, groups = list(range(len(dead))), []
    while left:                                         # single-link groups
        g, todo = [left.pop(0)], None
        grew = True
        while grew:
            grew = False
            for j in list(left):
                if any(math.dist(dead[j][1], dead[i][1]) <= FED_GROUP for i in g):
                    g.append(j); left.remove(j); grew = True
        groups.append(sorted(g))
    groups.sort(key=lambda g: (-len(g), g[0]))
    F['groups'] = [[i + 1 for i in g] for g in groups]
    for gi, g in enumerate(groups):
        for i in g:
            F['points'][i]['group'] = gi + 1
    if not 1 <= group <= len(groups):
        raise SystemExit('--fed-group %d: the AFTER_DEATH points stand in %d group(s)' % (group, len(groups)))
    G = [F['points'][i] for i in groups[group - 1]]
    F['group'] = [q['n'] for q in G]
    # ---- the collision round the group: the floor under each point, the flood from them
    gx, gz = [q['at'][0] for q in G], [q['at'][2] for q in G]
    near = min(((math.hypot(q[0] - sum(gx) / len(gx), q[2] - sum(gz) / len(gz)), q) for _k, q, _w in crew), key=lambda x: x[0])[1]
    cx, cz = gx + [near[0]], gz + [near[2]]
    if max(cx) - min(cx) > 9000 or max(cz) - min(cz) > 9000:    # the crew is far: only round the group (the flood then ends at the box)
        cx, cz = gx, gz
    try:
        W = L.walk((min(cx) - FED_PAD, max(cx) + FED_PAD, min(cz) - FED_PAD, max(cz) + FED_PAD))
    except Exception as e:
        F['notes'].append('the collision could not be read (%s: %s): the mesh alone is used' % (type(e).__name__, e))
        W = None
    start = None
    if W is not None:
        for q in G:
            q['floor'], q['floors'] = coll_floor(W, q['at'])
            if q['floor'] is not None and start is None:
                start = (q['at'][0], q['floor'], q['at'][2])
    if start is not None:
        seen, par, block = W.flood(start)
        F.update(seen=seen, W=W, par=par, area=len(seen) * W.CELL * W.CELL / 1e4)
        cs = [W.centre(c) for c in seen]
        F['bounds'] = (min(x for x, _ in cs), max(x for x, _ in cs), min(z for _, z in cs), max(z for _, z in cs), min(seen.values()), max(seen.values()))
        refs = L.refs()
        F['blockers'] = [(sc.path[refs[r]][5:] if r in refs else 'REF %d' % r, len(c)) for r, c in sorted(block.items(), key=lambda kv: -len(kv[1]))[:10]]
        for q in G:
            c = W.cell(q['at'][0], q['at'][2])
            q['flood'] = q['floor'] is not None and c in seen and abs(seen[c] - q['floor']) < 30.0
        for kind, q, _w in crew:
            c = W.cell(q[0], q[2])
            F['reached'][kind] = F['reached'].get(kind, False) or (c in seen and abs(seen[c] - q[1]) < 150.0)
    # ---- the way onto the crew's mesh
    on = [q for q in G if q['mesh'] and q['mesh'][2] in parts]
    if len(on) == len(G):
        F['entries'] = [(q['at'][0], q['mesh'][1], q['at'][2], q['mesh'][0]) for q in G]
        F['heads'] = [q['head'] for q in G]
        e0 = F['entries'][0]
    else:
        e0 = None
        if F['seen'] is not None:
            seen, depth = F['seen'], {}
            def deep(c):                                # steps of the flood from its start: the way's length in cells
                stack = []
                while c is not None and c not in depth:
                    stack.append(c); c = F['par'][c]
                d = depth[c] if c is not None else -1
                for s in reversed(stack):
                    d += 1; depth[s] = d
                return d
            best, idx = None, collections.defaultdict(list)
            for i in range(len(nav.pv)):                # the crew's polygons by a grid of 400: 250,000 cells are asked
                if nav.ok[i] and nav.part[i] in parts:
                    b = nav.box[i]
                    for ix in range(int(b[0] // 400), int(b[1] // 400) + 1):
                        for iz in range(int(b[2] // 400), int(b[3] // 400) + 1):
                            idx[ix, iz].append(i)
            for c, y in seen.items():
                x, z = W.centre(c)
                for i in idx.get((int(x // 400), int(z // 400)), ()):
                    if nav.inside(i, x, z) and abs(floor(nav, i, x, z) - y) <= 80.0 and clear(nav, x, floor(nav, i, x, z), z) >= 40.0:
                        d = deep(c)
                        if best is None or d < best[0]:
                            best = (d, (x, floor(nav, i, x, z), z, i), (x, y, z))
                        break
            if best:
                F['join'] = e0 = best[1]
                w = W.way(seen, start, best[2], margin=3) or [best[2]]
                k0 = next((k for k in range(len(w)) if all(q['floor'] is not None and coll_line(W, seen, (q['at'][0], q['floor'], q['at'][2]), w[k]) for q in G)), None)
                if k0 is None:
                    F['notes'].append('no way point of the collision\'s way is reached by a straight line from EVERY point of the group: the way is the one from point %d' % G[0]['n'])
                    k0 = 0
                F['pre'] = [tuple(q) for q in w[k0:]]
            else:
                # nothing joins. The gotos go to the EDGE of what the collision leaves open, and from there blind at the crew's mesh.
                # The edge: where the flood went DOWN (it spans more than 150 in height: stairs it took part of) its lowest cell;
                # else the cell nearest to an object named 'stair' among those that bound it; else the cell nearest to the crew's
                # mesh in the plan. (A walk test that knew a stair's stacked flights would do better: kl_escape.Walk takes a
                # slab's underside for a floor and the flight above for a ceiling.)
                polys = [i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] in parts]
                refs = L.refs()
                lo, hi = min(seen.values()), max(seen.values())
                stairs = [n_ for n_, _c in F['blockers'] if 'stair' in n_.lower()]
                if hi - lo > 150.0:
                    c, F['edge_why'] = min(seen, key=lambda c: seen[c]), 'the lowest place the walk test came to (it went down %d from the points)' % (hi - lo)
                elif stairs:
                    pts_ = [W.centre(c_) for c_, g in W.grid.items() for _y, _f, r in g[:1] if r in refs and 'stair' in sc.path[refs[r]].lower()]
                    mx, mz = sum(x for x, _ in pts_) / len(pts_), sum(z for _, z in pts_) / len(pts_)
                    c = min(seen, key=lambda c: math.hypot(W.centre(c)[0] - mx, W.centre(c)[1] - mz))
                    F['edge_why'] = 'the place of the region nearest to the middle of %s, which bounds it' % stairs[0].split('\\')[-1]
                else:
                    cells = list(seen)
                    c = min(cells[::max(1, len(cells) // 3000)], key=lambda c: min(math.hypot(nav.mid[i][0] - W.centre(c)[0], nav.mid[i][2] - W.centre(c)[1]) for i in polys))
                    F['edge_why'] = 'the place of the region nearest to the crew\'s mesh in the plan'
                ex, ez = W.centre(c)
                F['edge'] = (ex, seen[c], ez)
                w = W.way(seen, start, F['edge'], margin=2) or [F['edge']]
                F['pre'] = [tuple(q) for q in w]
                i = min(polys, key=lambda i: math.hypot(nav.mid[i][0] - ex, nav.mid[i][2] - ez) + 0.25 * abs(nav.mid[i][1] - seen[c]))
                F['blind'] = [tuple(nav.mid[i])]
        if e0 is None and not F['blind']:
            c = [(q['off'][0], q) for q in G if q['off']]
            if c:
                F['notes'].append('no floor of the collision under the group and no mesh of the crew\'s under it: nothing to walk on is known')
    if F['pre']:                                        # no goto of the collision's way longer than LEG_MAX
        out = [F['pre'][0]]
        for q in F['pre'][1:]:
            n = int(math.ceil(d2(out[-1], q) / LEG_MAX))
            a = out[-1]
            out += [lerp(a, q, k / n) for k in range(1, n + 1)]
        F['pre'] = out
    # ---- where the fed walks to: the crew's place of kind `to`, or the nearest of the crew's places he has a mesh way to
    if e0 is not None:
        dist = nav.dist_map(e0[3], e0[:3])[0]
        ok = [(dist[q[3]], kind, q, what) for kind, q, what in crew if q[3] in dist and kind != 'start']
        want = {'van': 'level', 'hall': 'enter'}.get(to, to)
        pick = [x for x in ok if x[1] == want]
        if pick:
            x = pick[-1] if want == 'loot' else pick[0]
        elif ok:
            x = min(ok)
            F['notes'].append('--fed-to %s: no such place of the crew on the mesh part he can reach: the nearest of the crew\'s places instead (%s)' % (to, x[1]))
        else:
            x = None
            F['notes'].append('none of the crew\'s places has a way on the mesh from where the fed comes onto it')
        if x:
            F['goal'] = (x[1], x[2], x[3], x[0])
    return F


def fed_text(L, F):
    """fed_facts() as lines (the `fed` command; the route print of a --fed-walk route)."""
    nav, o = L.nav, []
    if not F['points']:
        return ['THE FED: ' + t for t in F['notes']]
    o.append('THE FED (klfed.c, [Fed] Player=1: the dead human comes back as police on a random free AFTER_DEATH point; the points float as START points do): '
             '%d point(s) in %d group(s) %s (a group = within %d of another); the crew\'s mesh part(s) %s; the gotos are written for group %s'
             % (len(F['points']), len(F['groups']), F['groups'], FED_GROUP, sorted(F['crew_parts']), F['group']))
    for q in F['points']:
        m = q['mesh']
        mesh = 'NO mesh under it' if not m else 'mesh %d under it, part %d (%d polygons%s)' % (q['at'][1] - m[1], m[2], nav.part_size[m[2]],
                                                                                         ' = the crew\'s' if m[2] in F['crew_parts'] else ': NOT the crew\'s')
        if q['off']:
            mesh += '; the crew\'s mesh is %d away in the plan and %+d in height' % (q['off'][0], q['off'][1])
        coll = ''
        if q['n'] in F['group']:
            coll = '; collision: ' + ('the floor he stands or falls on is %d (%d under the point)' % (q['floor'], q['at'][1] - q['floor']) if q['floor'] is not None else
                                      'NO floor at or under it' + (' - the floors of its cell are %s (the lowest %d ABOVE it)' % (', '.join('%d' % y for y in q['floors'][:5]),
                                                                                                                         min(q['floors']) - q['at'][1]) if q['floors'] else ' - its cell has no floor at all'))
        o.append('   point %d (group %d) %s at (%d, %d, %d), heading %d: %s%s' % (q['n'], q['group'], q['name'].split('!')[-1], *q['at'], q['head'], mesh, coll))
    if F['seen'] is not None:
        b = F['bounds']
        yes, no = [k for k, v in F['reached'].items() if v], [k for k, v in F['reached'].items() if not v]
        o.append('   the walk test over the collision from the group (kl_escape.Walk: the static shapes only - no door that opens, no character radius; stacked stair flights it '
                 'often does NOT take, so a \'no\' is weaker than a \'yes\'): %d m2, x %d..%d z %d..%d, floors %d..%d; of the crew\'s places it reaches: %s; not: %s'
                 % (F['area'], *b, ', '.join(yes) or 'none', ', '.join(no) or 'none'))
        o.append('   what bounds that region (cells blocked): ' + '; '.join('%s x%d' % (n.split('\\')[-1][-44:], c) for n, c in F['blockers']))
    elif any(q['n'] in F['group'] for q in F['points']):
        o.append('   the walk test over the collision could not start: no point of the group has a floor of the collision at or under it')
    if F['entries']:
        o.append('   every point of the group stands over the crew\'s mesh: the fed\'s gotos follow the mesh from the points (the first way point: a straight line from each)')
    if F['pre']:
        o.append('   %s: %s' % ('the collision\'s way from the group to where the crew\'s mesh begins, (%d, %d, %d) - gotos OFF the mesh' % F['join'][:3] if F['join'] else
                               'NEITHER the mesh NOR the collision joins the group to the crew\'s part: the way to the edge of what the collision leaves open, (%d, %d, %d)' % F['edge'],
                               ' '.join('(%d, %d, %d)' % q for q in F['pre'])))
    if F['blind']:
        o.append('   the edge is %s; from it %d BLIND goto(s) of %d ms straight at the crew\'s mesh at (%d, %d, %d), %d under it (a GUESS that there is a way: the `pos` lines say '
                 'how far he got)' % (F.get('edge_why', '?'), FED_BLIND, FED_BLIND_MS, *F['blind'][-1], F['edge'][1] - F['blind'][-1][1]))
    if F['goal']:
        o.append('   the fed walks to the crew\'s \'%s\' place (%d, %d, %d): %d of mesh way' % (F['goal'][0], *F['goal'][1][:3], F['goal'][3]))
    if F.get('coll_end') is not None:
        o.append('   THE MESH WAY LEAVES THE REGION THE COLLISION LEAVES OPEN at way point %d of the fed\'s part (a door that is shut in the collision, or stairs the walk test '
                 'does not take): a goto that sticks there in the game says which' % (F['coll_end'] + 1))
    for t in F['notes']:
        o.append('   NOTE ' + t)
    return o


# ------------------------------------------------------------------ the route
HARD = ('first', 'enter', 'exit', 'level', 'call', 'loot', 'gate', 'rally', 'board', 'wait', 'join', 'foot', 'approach', 'money', 'drop', 'land', 'die', 'stair', 'align',
        'fedgoal')
KIND_TEXT = {'first': 'the first way point', 'way': 'a place of the bot\'s way', 'corner': 'a corner of the mesh', 'door': 'a door (a short shared edge)',
             'stair': 'foot / top of a slope', 'long': 'on a long leg', 'drop': 'the take-off of a drop', 'land': 'where the drop lands (not a goto)'}
UNTIL = ('enter', 'loot', 'exit', 'join', 'van', 'board', 'wall')


def wp(p, kind, what='', poly=None, **kw):
    d = {'p': tuple(p[:3]), 'kind': kind, 'what': what or KIND_TEXT.get(kind, ''), 'poly': poly, 'hard': kind in HARD}
    d.update(kw)
    return d


def at4(w):
    return tuple(w['p']) + (w['poly'],)


class Route:
    """The human's way through one build (the docstring's route rule).
    segs = [{'name', 'entries' [(x, y, z, polygon)], 'pts' [way point]}]; between two segments the hook moves the
    player (Retomoto's join). A way point = {'p', 'kind', 'what', 'poly' (None = off the mesh), 'hard', 'leg' {...},
    'r' (goto radius), 'sprint', 'stop' (something else than a goto follows), 'boxes' [...], and for the script:
    'keys' (lines after it is reached), 'say' (what the log should show there)}."""

    def __init__(self, L, bot=2, until='board', loot=2, die=False, walk=False, shoot=False, stops=False, clear=False, fed=None):
        self.L, self.nav, self.B = L, L.nav, L.B
        self.bot, self.until, self.loot_n, self.die, self.walk, self.shoot = bot, until, loot, die, walk, shoot
        self.keep_stops, self.clear, self.fed = stops, clear, None      # (fed: the facts of fed_facts() once the fed's part is made)
        self.notes, self.segs, self._doors = [], [], None
        self.lanes = KB.lanes(self.B)
        self.boarding = None                    # 'van' (the box rides on a key-framed van) | 'fixed' | None (not walked)
        self.van = self.the_van()
        self.exits = list(L.st['exits'])
        if until not in UNTIL:
            raise SystemExit('--until %s: one of %s' % (until, ' '.join(UNTIL)))
        if until == 'join' and not L.rt:
            raise SystemExit('--until join: %s has no join (Retomoto Tower only)' % L.map)
        if until == 'wall' and not L.ini_sections('Climb'):
            raise SystemExit('--until wall: %s has no [Climb] section in its KLJoin.ini (the climb build is <work>\\build\\z_climb\\M03)' % L.folder)
        segs = self.cut(self.guides())
        for n, s in enumerate(segs):
            self.segs.append(self.segment(s))
        if die:
            self.die_place()
        elif until in ('van', 'board'):
            self.call_point()
        if fed:
            if not die:
                raise SystemExit('--fed-walk goes with --die (the fed is the human after his death)')
            self.fed_part(fed)
        for s in self.segs:
            self.split(s)
            self.finish(s)
            self.drive(s)
        self.stage_boxes()
        self.danger()
        if self.fed:
            self.fed_collision()

    # ---- what the plan gives
    def note(self, text):
        if text not in self.notes:
            self.notes.append(text)

    def the_van(self):
        """The key-framed van the round uses (kl_fa_bots.van_drives), or None (a helicopter, a spline car)."""
        name = (self.L.plan.get('vehicle') or {}).get('node')
        vans = [d for d in self.L.vans if d['name'] == name] or [d for d in self.L.vans if abs(d['stop'][1]) < 30000]
        return vans[0] if vans else None

    def guides(self):
        plan, idx = self.L.plan, self.bot - 2
        me = plan['bots'].get(str(self.bot))
        if me is None:
            raise SystemExit('--bot %d: the plan has the bots %s (Squad#02 .. #08)' % (self.bot, ' '.join(sorted(plan['bots']))))
        pick = lambda st, i: tuple(me['places'][i]) if i is not None and i < len(me['places']) else tuple(st['places'][min(idx, len(st['places']) - 1)])
        g = [{'p': pick(st, i), 'kind': st['kind'], 'what': st['what'], 'node': st.get('node')} for i, st in enumerate(plan['stations'])]
        segs = [{'name': 'tower' if self.L.rt else 'map', 'guides': g, 'entry': None}]
        if self.L.rt:
            s = self.L.rt['street']
            for x in g:
                if x['kind'] == 'park':                 # the tower's gather place beside the jump box: on the way, no more
                    x['kind'] = 'way'
            g2 = [{'p': pick(st, None), 'kind': st['kind'], 'what': st['what'], 'node': st.get('node')} for st in s['stations']]
            j = s['join']
            segs.append({'name': 'street', 'guides': g2, 'entry': (j['at'][0], j.get('floor', j['at'][1]), j['at'][2])})
        return segs

    def cut(self, segs):
        """The guides up to --until, and the special places behind them (seg['tail'])."""
        u = self.until
        for s in segs:
            s['tail'] = []
        flat = [(si, gi, g['kind']) for si, s in enumerate(segs) for gi, g in enumerate(s['guides'])]
        def upto(si, gi):
            out = segs[:si + 1]
            out[-1]['guides'] = out[-1]['guides'][:gi + 1]
            return out
        if u == 'join':
            segs = segs[:1]
        elif u in ('enter', 'loot', 'exit'):
            hits = [(si, gi) for si, gi, k in flat if k == u]
            if not hits and u == 'exit':
                self.note('--until exit: the plan has no EXITS_BANK station (stage 2 is skipped on this map); the route ends at the last loot stop')
                hits = [(si, gi) for si, gi, k in flat if k == 'loot']
            if not hits:
                raise SystemExit('--until %s: the plan has no such station' % u)
            segs = upto(*(hits[0] if u == 'enter' else hits[-1]))
        elif u == 'wall':
            hits = [(si, gi) for si, gi, k in flat if k == 'gate']
            if not hits:
                raise SystemExit('--until wall: the plan has no gate (the place in front of the drop)')
            segs = upto(hits[0][0], hits[0][1] - 1)
            segs[-1]['tail'] = self.wall_tail(segs[-1]['guides'][-1]['p'])
        else:                                           # van, board
            hits = [(si, gi) for si, gi, k in flat if k == 'level']
            if not hits:
                raise SystemExit('--until %s: the plan has no level exit station' % u)
            park = [g for s in segs[hits[-1][0]:] for g in s['guides'] if g['kind'] == 'park']
            segs = upto(*hits[-1])
            segs[-1]['tail'] = self.vehicle_tail(segs[-1]['guides'][-1]['p'], park[-1]['p'] if park else None)
        if self.L.rt and len(segs) == 2 or u == 'join':
            segs[0]['tail'] = self.join_tail(segs[0]['guides'][-1]['p'])
        return segs

    # ---- the special places
    def join_tail(self, frm):
        """Retomoto: into the jump box of KLJoin.ini [Join] (kljoin.c: the feet inside the box -> the game's jump)."""
        nav = self.nav
        sec = self.L.ini_sections('Join')
        if not sec or 'Min' not in sec[0]:
            raise SystemExit('%s: no [Join] box in KLJoin.ini' % self.L.folder)
        lo, hi = vec(sec[0]['Min']), vec(sec[0]['Max'])
        lo, hi = tuple(min(a, b) for a, b in zip(lo, hi)), tuple(max(a, b) for a, b in zip(lo, hi))
        # He must not be steered INTO the box: the hook jumps him the tick he is inside, the goto then never 'reaches' and
        # walks him about the lobby until its timeout (run J2: 15 s, side steps, C). So: a goto to a place JOIN_BACK in
        # front of one face of the box, at square to it, and from there the W key alone for JOIN_W ms.
        # W alone walks where he LOOKS, and he looks where he last walked: so the last goto is JOIN_RUN long and ON the line
        # into the box. The line: through a place of the mesh inside the box, in one of 16 directions; the one whose three
        # places and two legs keep the most from the mesh's border and that enters the box farthest from its corners.
        a0, best = snap(nav, frm) or nearest(nav, frm, 150.0), None
        inbox = lambda p, m=0.0: lo[0] + m <= p[0] <= hi[0] - m and lo[2] + m <= p[2] <= hi[2] - m
        inside = [q for q in around(nav, ((lo[0] + hi[0]) / 2, frm[1], (lo[2] + hi[2]) / 2), math.hypot(hi[0] - lo[0], hi[2] - lo[2]) / 2, step=20.0, dy=150.0)
                  if inbox(q, 60.0) and lo[1] <= q[1] <= hi[1]]
        for qj in inside:
            for k in range(16):
                dx, dz = math.sin(k * math.pi / 8), math.cos(k * math.pi / 8)
                back = 0.0
                while inbox((qj[0] - dx * back, 0, qj[2] - dz * back)):
                    back += 5.0                         # where the line comes into the box
                ent = (qj[0] - dx * back, qj[1], qj[2] - dz * back)
                corner = min(abs(ent[0] - lo[0]) + abs(ent[2] - lo[2]), abs(ent[0] - hi[0]) + abs(ent[2] - lo[2]), abs(ent[0] - lo[0]) + abs(ent[2] - hi[2]), abs(ent[0] - hi[0]) + abs(ent[2] - hi[2]))
                off = lambda dist: (ent[0] - dx * dist, ent[1], ent[2] - dz * dist)
                q0, qp = snap(nav, off(JOIN_BACK + JOIN_RUN), dy=150.0), snap(nav, off(JOIN_BACK), dy=150.0)
                if not q0 or not qp or a0 is None or back < JOIN_IN:
                    continue
                # he may look JOIN_SLOP degrees to either side of the line when the goto ends: W must still take him in
                slop = True
                for turn in (-JOIN_SLOP, JOIN_SLOP):
                    h = k * math.pi / 8 + math.radians(turn)
                    slop = slop and any(inbox((qp[0] + math.sin(h) * s, 0, qp[2] + math.cos(h) * s), 15.0) for s in range(0, int(JOIN_W * WALK / 1000) - 60, 5))
                if not slop:
                    continue
                t0, t = trace(nav, q0, qp), trace(nav, qp, qj)
                if not t0['ok'] or not t['ok']:
                    continue
                got = nav.path(a0, q0)
                if got is None:
                    continue
                key = (min(clear(nav, *q0[:3]), clear(nav, *qp[:3]), t0['clear'], t['clear'], corner, 80.0), -got[1])
                if best is None or key > best[0]:
                    best = (key, q0, qp, qj, t, ent, math.degrees(math.atan2(dx, dz)))
        if best is None:
            raise SystemExit('the jump box of KLJoin.ini [Join] has no line of %d on the mesh into it that the route reaches' % (JOIN_BACK + JOIN_RUN))
        key, q0, qp, qj, t, ent, head = best
        name = sec[0].get('Name', '')
        # (he STOPS at the first of the two: the run on the line then starts from a stand, where he turns before he walks)
        return [wp(q0, 'approach', '%d in front of the jump box, on the line into it (heading %.0f)' % (JOIN_BACK + JOIN_RUN, head), q0[3], stop=True, r=40.0),
                wp(qp, 'approach', '%d in front of the jump box, looking into it' % JOIN_BACK, qp[3], stop=True, r=30.0),
                wp(qj, 'join', 'into the jump box %s (KLJoin.ini [Join]) by the W key alone, %d ms: he crosses its edge at (%d, %d), %d from the nearest corner of the box; the hook '
                               'moves him to the lobby' % (name, JOIN_W, ent[0], ent[2], key[0] if key[0] < 80 else 80), qj[3], stop=True, blind=JOIN_W, box=(lo, hi))]

    def vehicle_tail(self, frm, park):
        """Where the human waits for the vehicle and where he boards it."""
        nav, B, st = self.nav, self.B, self.L.st
        act = st['action']
        if self.van:                                    # the boarding box rides on the van: beside its rear doors, then at them
            d = self.van
            h = math.radians(d['heading'])
            side = (math.cos(h), -math.sin(h))
            ref = park or frm
            cands = []
            for sgn in (1.0, -1.0):
                c = (d['board'][0] + sgn * side[0] * VAN_SIDE, d['board'][1], d['board'][2] + sgn * side[1] * VAN_SIDE)
                q = snap(nav, c, dy=150.0) or nearest(nav, c, 90.0, dy=150.0)
                cands.append((0 if q else 1, d2(c, ref), q or (c[0], c[1], c[2], None)))
            q = min(cands)[2]
            what = 'beside the van\'s rear doors at its stop'
            if self.clear and self.until == 'van':
                # --clear: in play and NOT aboard while the AI heisters board. A place of the mesh inside a level exit box (the
                # van keeps coming while somebody stands in one), CLEAR_MIN from the van's line and its boarding box at the stop and
                # outside the box the bots gather in - the nearest such place to where the route enters the exit box
                ally, a0 = self.L.plan.get('ally_at'), snap(nav, frm) or nearest(nav, frm, 150.0)
                best = None
                for c in around(nav, d['stop'], 2000.0, nav.part[a0[3]] if a0 else None, step=80.0, dy=260.0):
                    if clear(nav, *c[:3]) < 60.0 or d2(c, d['board']) < CLEAR_MIN or d2(c, d['stop']) < CLEAR_MIN:
                        continue
                    if self.lanes and KB.lane_dist(self.lanes, c) < CLEAR_MIN:
                        continue
                    if ally and abs(c[0] - ally[0]) <= KB.ALLY_SIZE[0] + 150.0 and abs(c[2] - ally[2]) <= KB.ALLY_SIZE[2] + 150.0:
                        continue
                    if not KB.in_exit(B, self.exits, c[:3]):
                        continue
                    key = d2(c, frm)
                    if best is None or key < best[0]:
                        best = (key, c)
                if best:
                    q = best[1]
                    what = 'CLEAR of the vehicle (--clear): %d from the van\'s stop, %d from its boarding box, outside the bots\' AllyEscapeBox, inside a level exit box' \
                           % (d2(q, d['stop']), d2(q, d['board']))
                else:
                    self.note('--clear: no place of the mesh inside a level exit box is %d from the van\'s line, its stop and the bots\' box: he waits beside the rear doors' % CLEAR_MIN)
            lane = KB.lane_dist(self.lanes, q) if self.lanes else 1e9
            inbox = [B.sc.path[k][5:] for k in KB.in_exit(B, self.exits, q[:3])]
            w = wp(q, 'wait', '%s, %.0f from its line' % (what, lane), q[3], stop=True, r=45.0, lane=lane, in_exit=inbox)
            if q[3] is None:
                self.note('the waiting place beside the van\'s stop is NOT on the mesh (neither side of the van within 90)')
            ally = self.L.plan.get('ally_at')
            if ally and abs(q[0] - ally[0]) <= KB.ALLY_SIZE[0] and abs(q[2] - ally[2]) <= KB.ALLY_SIZE[2]:
                self.note('the waiting place beside the van (%d, %d) lies inside the bots\' AllyEscapeBox (middle (%d, %d), %d to each side): the AI heisters gather there - '
                          'up to seven bodies may stand between him and the doors' % (q[0], q[2], ally[0], ally[2], KB.ALLY_SIZE[0]))
            if not inbox:
                self.note('the waiting place beside the van is in NO level exit box: nobody calls the van a second time while he waits there')
            out = [w]
            if self.until == 'board':
                b = snap(nav, d['board'], dy=150.0)
                out.append(wp(b or d['board'], 'board', 'the van\'s boarding box at the stop (PlayerAction EnterVehicle, %s)' % B.sc.names[act] if act else 'the boarding box',
                              b[3] if b else None, stop=True, r=35.0))
            self.boarding = 'van'
            return out
        if not act:
            self.note('no boarding action (PlayerAction EnterVehicle) in the build: the route ends in the level exit box')
            return []
        ap = B.at(act)                                  # a box that stands still (a helicopter's landing place, a spline car's stop)
        cands = [c for c in ([park] if park else []) + [ap] if c]
        best = None
        for c in cands:
            q = snap(nav, c, dy=260.0) or nearest(nav, c, 120.0, dy=260.0)
            if q and (best is None or d2(q, ap) < d2(best, ap)):
                best = q
        if best is None:
            self.note('the boarding box %s at (%d, %d, %d) has no mesh under it' % (B.sc.names[act], *ap))
            return []
        self.boarding = 'fixed'
        ins = B.sc.cls(act) == 'ZBoxPrimitive' and (B.in_box(act, best[:3]) or B.in_box(act, (best[0], best[1] + KB.CHEST, best[2])))
        return [wp(best, 'board' if self.until == 'board' else 'wait', 'in the boarding box %s (PlayerAction EnterVehicle; it stands still)%s' %
                   (B.sc.names[act], '' if ins else ' - NOT inside it by its size values'), best[3], stop=True, r=45.0)]

    def wall_tail(self, frm):
        """Withdrawal's climb build: the foot of a [Climb] edge of KLJoin.ini, walked at square to the face (klclimb.c:
        15 .. 70 from the face on the side Normal= points to, within 40 of Floor=, slower than Speed, looking at it)."""
        nav, best = self.nav, None
        a0 = snap(nav, frm) or nearest(nav, frm, 150.0)
        for n, e in enumerate(self.L.ini_sections('Climb')):
            A, Bq, N, fl = vec(e['A']), vec(e['B']), vec(e['Normal']), float(e['Floor'])
            L = d2(A, Bq)
            for k in range(int(L // 50) + 1):
                t = k * 50.0 / L
                if t * L < 120 or (1 - t) * L < 120:
                    continue
                top = lerp(A, Bq, t)
                foot = (top[0] + N[0] * CLIMB_STAND, fl, top[2] + N[1] * CLIMB_STAND)
                app = (top[0] + N[0] * (CLIMB_STAND + CLIMB_RUN), fl, top[2] + N[1] * (CLIMB_STAND + CLIMB_RUN))
                qa = snap(nav, app, dy=80.0)
                if not qa or a0 is None:
                    continue
                got = nav.path(a0, qa)
                if got is None:
                    continue
                tr = trace(nav, qa, foot)
                key = (got[1], n, k)
                if best is None or key < best[0]:
                    best = (key, n, qa, foot, tr, top, N)
        if best is None:
            raise SystemExit('--until wall: no [Climb] edge has mesh %d in front of its foot that the route reaches' % CLIMB_RUN)
        _key, n, qa, foot, tr, top, N = best
        qf = snap(nav, foot, dy=80.0)
        self.facts_wall = {'edge': n + 1, 'top': top, 'normal': N, 'foot': foot, 'mesh_way': tr['way'], 'len': tr['len']}
        return [wp(qa, 'approach', 'square in front of climb edge %d, %d from its face' % (n + 1, CLIMB_STAND + CLIMB_RUN), qa[3], stop=True, r=40.0),
                wp(qf or foot, 'foot', 'the foot of climb edge %d: %d from the face, looking at it (the mesh ends %d short of it)' % (n + 1, CLIMB_STAND, tr['len'] - tr['way']),
                   qf[3] if qf else None, stop=True, r=20.0, heading=math.degrees(math.atan2(-N[0], -N[1])))]

    def loot_places(self, g, part):
        """The money objects of a loot stop the human can take by standing in their trigger (kl_fa_bots.money_objects;
        re\\bots_loot.md 1), the richest first -> [way point 'money'] (at most --loot of them)."""
        nav, B, out = self.nav, self.B, []
        near = [o for o in self.L.money() if o['amount'] > 0 and o['radius'] and abs(o['at'][1] - g['p'][1]) < 300 and d2(o['at'], g['p']) < LOOT_NEAR]
        people = [o for o in near if o['kind'] in ('armed', 'civilian')]
        if people:
            self.note('%s: %d of its money objects are on a person (%s): not walked to - where the person will be is not known'
                      % (g['what'].split(':')[0], len(people), ', '.join(B.sc.names[o['node']] for o in people[:4])))
        glass = [o for o in near if o['kind'] == 'case' and not o['self_open']]
        if glass:
            self.note('%s: %d of its money objects are in cases that open when their glass breaks (a shot, or the squads\' relays when the bots come): '
                      'the use key does not open them - not walked to' % (g['what'].split(':')[0], len(glass)))
        # the ones that stand on the floor first (the bank's garage: the two the live run ESC3 took are at floor height, six
        # others lie 88 higher), then the richest
        near = sorted((o for o in near if o['kind'] == 'plain' or (o['kind'] == 'case' and o['self_open'])), key=lambda o: (abs(o['at'][1] - g['p'][1]) > 50.0, -o['amount']))
        for o in near:
            if len(out) >= self.loot_n:
                break
            R, pos, best, push = o['radius'] + KB.TRIGGER_PAD, o['at'], None, None
            for x, h, z, poly in around(nav, pos, R + LOOT_PUSH, part, step=20.0, dy=R + 190.0):
                dd = math.hypot(x - pos[0], z - pos[2])
                if abs(h + 90.0 - pos[1]) > math.sqrt(max(0.0, R * R - min(dd, R) ** 2)) + 100.0:
                    continue                            # kl_fa_bots.trigger_reach's test of the height
                cl = clear(nav, x, h, z)
                # 25 inside the ball if the mesh goes there, and LOOT_OFF from the thing itself (the bank's money stands ON the mesh:
                # a goto to its own place would run into it and never be 'reached'; run ESC3 stood 41 and 45 from the two it took)
                key = (0 if LOOT_OFF <= dd <= R - 25.0 else 1 if dd <= R - 25.0 else 2, 0 if cl >= RISK_CLEAR or dd > R - 25.0 else 1, dd)
                if best is None or key < best[0]:
                    best = (key, (x, h, z, poly), dd)
            if best is None:
                continue
            name = B.sc.names[o['node']]
            if name == 'Money_Attachroot':
                name = B.sc.path[o['node']][5:].split('\\')[-2] + '\\' + name
            name = name.split('!')[-1]
            what = '%s %d at (%d, %d, %d): %d from it, its trigger reaches %d%s' % (name, o['amount'], *pos, best[2], R, '' if o['kind'] == 'plain' else ' - a container with its own Open trigger')
            if best[0][0] == 2:
                # the mesh ends outside the trigger (Retomoto's stacks lie on the boardroom table): from the mesh's border he
                # is pushed at the object for LOOT_PUSH_MS, as far as the table lets him. ASSUMPTION that this gets him in
                push = (pos[0], pos[2])
                what += ' - THE MESH ENDS OUTSIDE ITS TRIGGER: from there %d ms of walking straight at it (off the mesh)' % LOOT_PUSH_MS
            out.append(wp(best[1], 'money', what, best[1][3], stop=True, r=30.0, amount=o['amount'], name=name, push=push))
        order, cur = [], g['p']                          # the nearest first, from the bot's loot place on
        while out:
            m = min(out, key=lambda q: d2(q['p'], cur))
            out.remove(m); order.append(m); cur = m['p']
        return order

    # ---- threading the places on the mesh
    def link(self, cur, g):
        """The way points from `cur` to way point g (g last)."""
        if cur.get('poly') is None or g.get('poly') is None:
            return [g]                                  # a place off the mesh: the straight line, said so by its leg
        w = way(self.nav, at4(cur), at4(g))
        if w is None:
            self.note('no way on the mesh from (%d, %d, %d) to (%d, %d, %d) [%s]: a straight line is written' % (*cur['p'], *g['p'], g['kind']))
            return [g]
        return [g if q['kind'] == 'goal' else wp(q['p'], q['kind'], poly=q['poly'], axis=q.get('axis')) for q in w]

    def first(self, entries, g0, part, near=2 * END_ZONE, what='START places'):
        """The first way point: a straight line on the mesh from EVERY entry (the human gets one START point of the row
        at random), as far along the way to the first guide as LEG_MAX allows. near: how near to an entry it may lie
        (the fed's part: 0 - a goto that is reached at once costs nothing, and a way point that only SOME of the
        AFTER_DEATH points see is worse)."""
        nav = self.nav
        c = tuple(sum(e[i] for e in entries) / len(entries) for i in range(3))
        cs = snap(nav, c, part=part, dy=150.0) or min(entries, key=lambda e: d2(e, c))
        w = way(nav, cs, at4(g0))
        line = [cs] + ([q['p'] + (q['poly'],) for q in w if q['kind'] != 'land'] if w else [at4(g0)])
        cands = []
        for a, b in zip(line, line[1:]):
            n = max(1, int(d2(a, b) // 100))
            for k in range(1, n + 1):
                t = trace(nav, a, lerp(a, b, k / n))
                if t['ok']:
                    cands.append(t['end'])
        cands = [cs] + cands
        best = None
        for q in reversed(cands):                       # the farthest first; a START place may stand at a wall, so the line's 'mid'
            if max(d2(e, q) for e in entries) > LEG_MAX or min(d2(e, q) for e in entries) < near:
                continue
            ts = [trace(nav, e, q) for e in entries]
            ok = [t for t in ts if t['ok'] and abs(t['end'][1] - q[1]) < 60]
            key = (len(ok), min(min([t['mid'] for t in ok] or [0]), clear(nav, *q[:3]), KEEP_CLEAR))
            if best is None or key > best[0]:
                best = (key, q, ts, ok)
            if len(ok) == len(entries) and key[1] >= KEEP_CLEAR:
                break
        if best is None:
            best = ((0, 0.0), cs, [], [])
        _key, q, ts, ok = best
        info = {'starts': len(entries), 'ok': len(ok), 'clear': min([t['clear'] for t in ok] or [0]), 'mid': min([t['mid'] for t in ok] or [0]),
                'len': (min([t['len'] for t in ts] or [0]), max([t['len'] for t in ts] or [0]))}
        if len(ok) < len(entries):
            self.note('only %d of the %d %s have a straight line on the mesh to the first way point (%d, %d, %d)' % (len(ok), len(entries), what, *q[:3]))
        return wp(q, 'first', 'the first way point: a straight line from %d of the %d %s' % (len(ok), len(entries), what), q[3], starts=info)

    def segment(self, s):
        nav, st = self.nav, self.L.st
        if s.get('entries'):                            # given places on the mesh (the fed's: the AFTER_DEATH points, or where the collision way joins it)
            entries, heads = list(s['entries']), list(s['heads'])
        elif s.get('entry'):
            e = snap(nav, s['entry'], dy=200.0) or nearest(nav, s['entry'], 200.0)
            if e is None:
                raise SystemExit('the entry (%d, %d, %d) of the %s part has no mesh under it' % (*s['entry'], s['name']))
            entries, heads = [e], [None]                # where he looks after the jump is not known
        else:
            entries, heads = [], []
            for p, f in st['starts']:
                q = snap(nav, p, under=START_FLOOR)
                if q is None:                           # the park has one START point 100 outside the mesh's border
                    q = nearest(nav, (p[0], p[1] - 80.0, p[2]), 150.0, dy=300.0)
                    self.note('the START point (%d, %d, %d) has no mesh under it within %d below: %s' % (
                        *p, START_FLOOR[0], 'no mesh within 150 either - a round that starts him there begins with a leg nobody checked' if q is None else
                        'the first leg from it is checked from the nearest place of the mesh, (%d, %d, %d), %d away' % (*q[:3], d2(q, p))))
                if q:
                    entries.append(q)
                    # he looks along the START point's own +Z (live, PT_DM03_die_r2: 'pos spawn ... heading 15' on the point whose +Z is 15)
                    heads.append(math.degrees(math.atan2(f[0], f[1])))
            if not entries:
                raise SystemExit('no START point stands over the mesh')
        part = nav.part[entries[0][3]]
        G = []
        for g in s['guides']:
            hit = next((b for b in BLOCKED.get(self.L.map, ()) if g['kind'] == 'way' and math.hypot(g['p'][0] - b[0], g['p'][2] - b[1]) <= b[2]), None)
            if hit:
                self.note('the bots\' way place (%d, %d, %d) is NOT walked to: %s' % (*g['p'], hit[3]))
                continue
            q = snap(nav, g['p'], part=part) or snap(nav, g['p']) or nearest(nav, g['p'], 150.0, part)
            if q is None:
                self.note('the bot\'s place (%d, %d, %d) [%s] has no mesh under it: left out' % (*g['p'], g['kind']))
                continue
            if g['kind'] == 'way' and clear(nav, *q[:3]) < MARGIN:
                # a place of the corridor only: moved to where the mesh is widest within WAY_NUDGE (a bot's own place on the
                # mall's escalator is 5 from its border; the line through it would enter the escalator off its middle)
                c = [o for o in around(nav, q, WAY_NUDGE, part, step=10.0, dy=60.0) if trace(nav, q, o)['ok']]
                if c:
                    q = max(c, key=lambda o: (min(clear(nav, *o[:3]), MARGIN), -d2(o, q)))
            G.append(wp(q, g['kind'], g['what'], q[3], node=g.get('node')))
        G += s['tail']
        if not G:
            raise SystemExit('the %s part has no place to walk to' % s['name'])
        pts = []
        if len(entries) > 1:
            cur = self.first(entries, G[0], part) if s['name'] != 'fed' else self.first(entries, G[0], part, near=0.0, what='AFTER_DEATH points of the group')
            pts.append(cur)
        else:
            cur = wp(entries[0], 'entry', poly=entries[0][3])
        plen = lambda c, ws: sum(d2(a['p'], b['p']) for a, b in zip([c] + ws, ws))
        for j, g in enumerate(G):
            new = self.link(cur, g)
            if g['kind'] in ('enter', 'exit') and g.get('node') and j + 1 < len(G):
                # a stage box the way to the NEXT place crosses anyway: the bot's own place in it is left out when it is
                # a detour (Hot Coffee's is a dead end in a doorway: in, a turn on the spot, out)
                alt = self.link(cur, G[j + 1])
                if plen(cur, new) + plen(g, self.link(g, G[j + 1])) > plen(cur, alt) + STAGE_DETOUR and self.inside_len(g['node'], [cur['p']] + [q['p'] for q in alt]) >= 10.0:
                    self.note('%s: the bot\'s own place (%d, %d, %d) is %d of detour and the way to the next place crosses the box anyway: not walked to'
                              % (g['what'], *g['p'], plen(cur, new) + plen(g, self.link(g, G[j + 1])) - plen(cur, alt)))
                    continue
            pts += new
            cur = pts[-1]
            if g['kind'] == 'loot' and self.loot_n and not self.die:
                for m in self.loot_places(g, part):
                    pts += self.link(cur, m)
                    cur = pts[-1]
        seg = {'name': s['name'], 'entries': entries, 'heads': heads, 'pts': pts, 'part': part}
        self.simplify(seg)
        self.align(seg)
        p = seg['pts']
        if len(entries) > 1 and len(p) > 1 and p[0]['kind'] == 'first' and p[1]['kind'] == 'align' and p[1].get('stop'):
            # the place in front of a door comes right after the first way point: when every START place has a straight line to
            # it, it IS the first way point (the park: the first one lay beyond it, 98 back and 173 degrees round from a stand)
            ts = [trace(nav, e, p[1]['p']) for e in entries]
            if all(t['ok'] and abs(t['end'][1] - p[1]['p'][1]) < 60.0 and t['mid'] >= RISK_CLEAR for t in ts) and max(t['len'] for t in ts) <= LEG_MAX:
                p[1]['starts'] = {'starts': len(entries), 'ok': len(entries), 'clear': min(t['clear'] for t in ts), 'mid': min(t['mid'] for t in ts),
                                  'len': (min(t['len'] for t in ts), max(t['len'] for t in ts))}
                p[1]['what'] += '; the first way point: a straight line from %d of the %d START places' % (len(entries), len(entries))
                del p[0]
        self.stairs(seg)
        return seg

    def inside_len(self, node, line):
        """How much of the polyline `line` lies inside the box of `node`, feet or chest, BOX_SHARE of its size values
        taken as half sizes."""
        B = self.B
        hit = [k for k in B.sc.resolve(R_ + node) if B.sc.cls(k) == 'ZBoxPrimitive']
        if not hit:
            return 0.0
        k, s, got = hit[0], B.box(hit[0]), 0.0
        for a, b in zip(line, line[1:]):
            n = max(1, int(d2(a, b) // 4))
            for t in range(n):
                p = lerp(a, b, (t + 0.5) / n)
                if B.in_box(k, p, BOX_SHARE, s) or B.in_box(k, (p[0], p[1] + KB.CHEST, p[2]), BOX_SHARE, s):
                    got += d2(a, b) / n
        return got

    def call_point(self):
        """Where the route first is inside a level exit box (that calls the vehicle when nobody called it before): a
        way point 60 behind that place, so that the script knows the moment."""
        B = self.B
        for seg in self.segs:
            for i, w in enumerate(seg['pts']):
                a = self.before(seg, i)
                if a is None or w['kind'] == 'land':
                    continue
                L = d2(a['p'], w['p'])
                n = max(1, int(L // 10))
                for t in range(n + 1):
                    p = lerp(a['p'], w['p'], t / n)
                    hit = KB.in_exit(B, self.exits, p)
                    if not hit:
                        continue
                    box, dist = B.sc.path[hit[0]][5:], L * t / n
                    if t == 0 and i == 0:
                        self.note('the route is inside level exit box %s from its first step: the vehicle is called at once' % box)
                    if L - dist > 150.0 and a.get('poly') is not None:
                        e = trace(self.nav, at4(a), lerp(a['p'], w['p'], min(1.0, (dist + 60.0) / L)))
                        if e['ok']:
                            seg['pts'].insert(i, wp(e['end'], 'call', 'in level exit box %s (60 inside): the vehicle is called here when nobody called it before' % box,
                                                    e['end'][3], call=box, r=60.0))
                            return
                    w['call'] = box
                    return
        self.note('the route never enters a level exit box: nobody calls the vehicle by walking it')

    def before(self, seg, i):
        """The way point a leg starts at (None: the first leg of a segment with several entries)."""
        if i:
            return seg['pts'][i - 1]
        return wp(seg['entries'][0], 'entry', poly=seg['entries'][0][3]) if len(seg['entries']) == 1 else None

    def straight(self, a, b):
        """trace() between two way points when both are on the mesh and no drop lies between -> dict or None."""
        if a is None or a.get('poly') is None or b.get('poly') is None or a['kind'] == 'drop' or b['kind'] == 'land':
            return None
        t = trace(self.nav, at4(a), b['p'])
        t['good'] = t['ok'] and abs(t['end'][1] - b['p'][1]) < 60.0     # ... and it arrives on the floor of b, not under or over it
        return t

    def simplify(self, seg):
        """Rule 3: a 'way' place, a corner or a door goes when the straight line past it stays on the mesh and either
        keeps KEEP_CLEAR from every border edge or is no nearer to one than the way point itself and the two legs it
        replaces (a row of doors in a straight aisle becomes one leg; a door the line would pass off its middle stays).
        Lines are compared by trace()'s 'mid': how narrow the two END places are is theirs, not the line's."""
        nav, pts, i = self.nav, seg['pts'], 0
        while i < len(pts) - 1:
            w, a = pts[i], self.before(seg, i)
            if w['kind'] in ('way', 'corner', 'door'):
                t = self.straight(a, pts[i + 1])
                if t and t['good']:
                    t1, t2 = self.straight(a, w), self.straight(w, pts[i + 1])
                    old = min(clear(nav, *w['p']), t1['mid'] if t1 and t1['good'] else 0.0, t2['mid'] if t2 and t2['good'] else 0.0)
                    if t['mid'] >= KEEP_CLEAR or t['mid'] >= old - 2.0:
                        del pts[i]
                        continue
            i += 1

    def align(self, seg):
        """A door is walked through ALONG ITS AXIS. A goto that turns at a way point starts the turn its radius early
        and cuts the corner by radius x sin(turn); at a door that is the frame. So where the line turns by more than
        ALIGN_TURN at a door, a way point is put on the door's axis in front of it (he STOPS there: a goto from a
        stand turns on the spot) and / or behind it, the first of ALIGN_RUNS that is on the mesh, no nearer to its
        border than the door's middle and reached by a straight line. Where none fits the door is marked 'slow'."""
        nav, out = self.nav, []
        turn = lambda u, v: abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))) if math.hypot(*u) > 1e-6 and math.hypot(*v) > 1e-6 else 0.0
        for i, w in enumerate(seg['pts']):
            ax = w.get('axis') if w['kind'] == 'door' and w.get('poly') is not None else None
            a = out[-1] if out else self.before(seg, i)
            b = seg['pts'][i + 1] if i + 1 < len(seg['pts']) else None
            pre = post = None
            need_pre = bool(ax and a is not None and a.get('poly') is not None and turn((w['p'][0] - a['p'][0], w['p'][2] - a['p'][2]), ax) > ALIGN_TURN)
            need_post = bool(ax and b is not None and b.get('poly') is not None and b['kind'] != 'land' and turn(ax, (b['p'][0] - w['p'][0], b['p'][2] - w['p'][2])) > ALIGN_TURN)
            for sign, need in ((-1.0, need_pre), (1.0, need_post)):
                if not need:
                    continue
                for d in ALIGN_RUNS:
                    t = trace(nav, at4(w), (w['p'][0] + sign * ax[0] * d, w['p'][1], w['p'][2] + sign * ax[1] * d))
                    if not t['ok'] or clear(nav, *t['end'][:3]) < clear(nav, *w['p']):
                        continue
                    c = wp(t['end'], 'align', '%d %s the door, on its axis' % (d, 'in front of' if sign < 0 else 'behind'), t['end'][3], post=sign > 0)
                    frm, to = (a, w) if sign < 0 else (w, b)
                    if (c['p'][0] - frm['p'][0]) * (to['p'][0] - frm['p'][0]) + (c['p'][2] - frm['p'][2]) * (to['p'][2] - frm['p'][2]) <= 0 and sign < 0:
                        continue                        # it would send him back the way he came
                    if (to['p'][0] - c['p'][0]) * (to['p'][0] - frm['p'][0]) + (to['p'][2] - c['p'][2]) * (to['p'][2] - frm['p'][2]) <= 0 and sign > 0:
                        continue                        # ... or past the next way point
                    s = self.straight(a, c) if sign < 0 else self.straight(c, b)
                    if s and s['good'] and s['mid'] >= min(RISK_CLEAR, clear(nav, *w['p'])):
                        if sign < 0:
                            pre = dict(c, stop=True, r=40.0)
                        else:
                            post = c
                        break
            if (need_pre and not pre) or (need_post and not post):
                w['slow'] = True
            if pre and len(out) >= 2 and out[-1].get('post'):
                s = self.straight(out[-2], pre)         # the way point behind the door before: not needed when this one is reached from that door
                if s and s['good'] and s['mid'] >= min(RISK_CLEAR, clear(nav, *out[-2]['p'])):
                    out.pop()
            out += [p for p in (pre, w, post) if p]
        seg['pts'] = out

    def stairs(self, seg):
        """A way point where a leg goes from level floor onto a slope that rises or falls 60 or more, and where it
        leaves it."""
        out = []
        for i, w in enumerate(seg['pts']):
            a = self.before(seg, i) if not out else out[-1]
            t = self.straight(a, w)
            if t and t['good'] and t['slopes']:
                marks = [(0.0, None)] + [(dist, cls) for dist, cls in t['slopes']] + [(t['len'], None)]
                for (d0, cls), (d1, _c) in zip(marks[1:], marks[2:]):
                    if cls != 'slope':
                        continue
                    e0 = trace(self.nav, at4(a), lerp(a['p'], w['p'], d0 / t['len']))['end']
                    e1 = trace(self.nav, at4(a), lerp(a['p'], w['p'], d1 / t['len']))['end']
                    if abs(e1[1] - e0[1]) < 60.0:
                        continue
                    for e, dd in ((e0, d0), (e1, d1)):
                        if dd > 90.0 and t['len'] - dd > 90.0 and (not out or d2(out[-1]['p'], e) > 90.0):
                            out.append(wp(e, 'stair', '%s of a slope (%+d over %d)' % ('the top' if (e is e0) == (e1[1] < e0[1]) else 'the foot', e1[1] - e0[1], d1 - d0), e[3]))
            out.append(w)
        seg['pts'] = out

    def split(self, seg):
        out = []
        for i, w in enumerate(seg['pts']):
            a = self.before(seg, i) if not out else out[-1]
            if a is not None and w['kind'] != 'land' and a['kind'] != 'drop':
                L = d2(a['p'], w['p'])
                n = int(math.ceil(L / LEG_MAX))
                for k in range(1, n):
                    p = lerp(a['p'], w['p'], k / n)
                    t = trace(self.nav, at4(a), p) if a.get('poly') is not None else None
                    out.append(wp(t['end'] if t and t['ok'] else p, 'long', poly=t['end'][3] if t and t['ok'] else None))
            out.append(w)
        seg['pts'] = out

    def die_place(self):
        """--die: he walks to the POST of an armed enemy that is in the world when the level loads and stands DIE_STAND
        from it - inside PB_REACH, where every shot of that guard is the point-blank step (re\\melee_damage.md) - the
        guard that costs the least way: the route up to one of its way points, then the mesh way to him (DIE_REACH at
        most). With the --die balance the first bullet from anybody kills as before; the place only makes sure that
        somebody fires. Where no post can be walked to: the old rule (die_sight)."""
        nav, best, seg = self.nav, None, self.segs[0]
        # (those in the world at the load first; a map whose guards all come in later - Retomoto: 88 of 91 - takes any post)
        for sol in ([s for s in self.L.soldiers() if s['active'] and s['place'] is not None], [s for s in self.L.soldiers() if s['place'] is not None]):
            run = 0.0
            for i, w in enumerate(seg['pts']):
                a = self.before(seg, i)
                run += d2(a['p'], w['p']) if a is not None else 0.0
                if w.get('poly') is None or w['kind'] in ('land', 'drop'):
                    continue
                dist, _prev, at_ = nav.dist_map(w['poly'], w['p'])
                for s in sol:
                    j = s['place'][3]
                    if j in dist:
                        dm = dist[j] + math.dist(at_[j], s['place'][:3])
                        if dm <= DIE_REACH and (best is None or run + dm < best[0]):
                            best = (run + dm, i, s, dm)
            if best is not None:
                break
        if best is None:
            return self.die_sight()
        _key, i, s, dm = best
        w0, post = seg['pts'][i], s['place']
        dist0 = nav.dist_map(w0['poly'], w0['p'])[0]
        c = [q for q in around(nav, post, PB_REACH - 20.0, nav.part[post[3]], step=20.0, dy=120.0)
             if 70.0 <= math.dist(q[:3], s['at']) <= DIE_STAND + 20.0 and clear(nav, *q[:3]) >= RISK_CLEAR and q[3] in dist0]
        if not c:
            self.note('--die: no place of the mesh stands %d from the post of %s: the old rule' % (DIE_STAND, s['name']))
            return self.die_sight()
        q = min(c, key=lambda q: d2(q, w0['p']))
        self.segs = self.segs[:1]
        seg['pts'] = seg['pts'][:i + 1]
        step = 100.0 * (s['g'] or 0.0) * 1.05
        target = wp(q, 'die', '--die: he stands here, %d from the post (%d, %d, %d) of %s (%s%s; squad %s%s) - inside the %d of the point-blank rule; %d of mesh way from way point %d'
                    % (math.dist(q[:3], s['at']), *s['at'], s['name'].split('!')[-1], s['weapon'], ', one point-blank step = %.0f x the dial' % step if step else '',
                       s['attitude'], (', it hunts' if s['hunts'] else '') + ('' if s['active'] else ', it comes into the world LATER'), PB_REACH, dm, i + 1),
                    q[3], stop=True, r=40.0, guards=1, soldier=s['name'])
        if d2(q, w0['p']) > 60.0:
            seg['pts'] += self.link(w0, target)
        else:
            seg['pts'][-1] = dict(target, p=w0['p'], poly=w0['poly'])
        if s['hunts']:
            self.note('--die: %s belongs to a squad that hunts: he may have left his post when the human comes (then he, or another, comes to the human)' % s['name'].split('!')[-1])

    def fed_part(self, opt):
        """--fed-walk: the fed's part of the route (fed_facts()): on the mesh from the AFTER_DEATH points of one group -
        or from where the collision's way joins the crew's mesh - to the crew's place asked for. The gotos BEFORE the
        mesh (the collision's way; the blind ones where nothing joins) are not way points: the script writes them
        from self.fed['pre'] / ['blind']."""
        F = self.fed = fed_facts(self.L, opt.get('group', 1), opt.get('to', 'loot'), self.bot)
        F['opt'] = dict(opt)
        for t in F['notes']:
            self.note('the fed: ' + t)
        if F['goal'] is None:
            return
        kind, q, what, dist = F['goal']
        guide = [{'p': q[:3], 'kind': 'fedgoal', 'node': None,
                  'what': 'the fed\'s goal: the crew\'s \'%s\' place (%s), %d of mesh way from where he comes onto the mesh' % (kind, what[:50], dist)}]
        ent, heads = (F['entries'], F['heads']) if F['entries'] else ([F['join']], [None])
        self.segs.append(self.segment({'name': 'fed', 'guides': guide, 'tail': [], 'entries': ent, 'heads': heads}))

    def fed_collision(self):
        """Which way points of the fed's mesh part the walk test over the collision reaches from where he appears
        (w['coll']: True / False / None = outside the box that was read); F['coll_end'] = the first that it does not."""
        F = self.fed
        seg = next((s for s in self.segs if s['name'] == 'fed'), None)
        F['coll_end'] = None
        if seg is None or F['seen'] is None:
            return
        W, seen = F['W'], F['seen']
        for i, w in enumerate(seg['pts']):
            c = W.cell(w['p'][0], w['p'][2])
            w['coll'] = None if not (W.x0 + 40 <= w['p'][0] < W.x1 - 40 and W.z0 + 40 <= w['p'][2] < W.z1 - 40) else (c in seen and abs(seen[c] - w['p'][1]) < 120.0)
            if w['coll'] is False and F['coll_end'] is None:
                F['coll_end'] = i

    def danger(self):
        """THE POINT-BLANK RULE (the docstring). Every way point of the human's own route against the armed enemies
        that are in the world when the level loads: w['t'] = the model's seconds from the route's start to its
        'reached', w['dwell'] = how long he then stays (about); w['pb_post'] = (distance, soldier) when a post is within
        PB_POST of it (3-D): R1; w['pb_reach'] = [(soldier, his mesh way from his post, the second he can be within
        PB_REACH)] for those that can be there before he leaves it - from the human's stage 1 (the ENTERS box; a
        route without one: its start) at GUARD_RUN along the mesh: R2. A GUESS but for the bank (see GUARD_RUN)."""
        nav, sol = self.nav, [s for s in self.L.soldiers() if s['active']]
        t, t1, rows = 0.0, None, []
        for seg in self.segs:
            if seg['name'] == 'fed':
                break
            for i, w in enumerate(seg['pts']):
                if w['kind'] == 'land':
                    continue
                rig = w.get('rig')
                t += rig['t'] if rig and rig.get('clean') else w['leg']['len'] / (SPRINT if w.get('sprint') else WALK)
                if t1 is None and any(nm.startswith('ENTERS') for nm, _p, _b in w.get('boxes', [])):
                    t1 = t
                nxt = seg['pts'][i + 1] if i + 1 < len(seg['pts']) else None
                dwell = STOP_MS / 1000.0 if w.get('stop') else 0.0
                if w['kind'] == 'money':
                    dwell = LOOT_HOLD + 0.3 + (0.0 if nxt is not None and nxt['kind'] == 'money' else 5.0)
                elif w['kind'] == 'loot' and not (nxt is not None and nxt['kind'] == 'money'):
                    dwell = 5.0
                elif w['kind'] in ('wait', 'board', 'die', 'foot'):
                    dwell = 30.0
                w['t'], w['dwell'] = t, dwell
                t += dwell
                rows.append(w)
        self.t_stage1 = t1
        t1 = t1 or 0.0
        for s in sol:
            if s['place'] is not None and '_d' not in s:
                s['_d'] = nav.dist_map(s['place'][3], s['place'][:3])
        for w in rows:
            near = [(math.dist(s['at'], w['p']), s) for s in self.L.soldiers()]      # R1: every post, also of a squad that comes into the world later
            near = [x for x in near if x[0] <= PB_POST]
            w['pb_post'] = min(near, key=lambda x: x[0]) if near else None
            w['pb_reach'] = []
            if w.get('poly') is None:
                continue
            for s in sol:
                if s['place'] is None or w['poly'] not in s['_d'][0]:
                    continue
                dm = s['_d'][0][w['poly']] + math.dist(s['_d'][2][w['poly']], w['p'])
                tg = t1 + max(0.0, dm - PB_REACH) / GUARD_RUN
                if tg <= w['t'] + w['dwell']:
                    w['pb_reach'].append((s, dm, tg))
            w['pb_reach'].sort(key=lambda r: r[2])

    def danger_rows(self):
        """-> (R1 rows, R2 rows): [(part, way point, w)] of the way points where he stops or walks within PB_POST of a
        post, and of the stops a guard can have reached."""
        r1 = [(si, i, w) for si, _seg, i, w in self.points() if w.get('pb_post') and (w.get('stop') or not w.get('sprint'))]
        r2 = [(si, i, w) for si, _seg, i, w in self.points() if w.get('pb_reach') and w.get('stop') and not w.get('blind')]
        return r1, r2

    def danger_text(self):
        o, sol = [], [s for s in self.L.soldiers() if s['active']]
        later = len(self.L.soldiers()) - len(sol)
        r1, r2 = self.danger_rows()
        made = [x for x in r2 if x[2].get('halt')]
        live = [(si, i, w) for si, _seg, i, w in self.points() if w.get('live')]
        o.append('THE POINT-BLANK RULE (a firing guard within %d sends a hit worth 100 bullets a step): %d armed enemies are in the world at the load (%d come later: their posts '
                 'count for R1, not for R2 - when they come is not read), %d of them in squads that hunt; the human\'s stage 1 %s' % (PB_REACH, len(sol), later, sum(1 for s in sol if s['hunts']),
                 'about %.0f s after the route starts' % self.t_stage1 if self.t_stage1 is not None else 'is not on this route: the guards are taken to hunt from its start'))
        o.append('   R1, a stop or a walk within %d of a post: %s' % (PB_POST, 'none' if not r1 else ''))
        for si, i, w in r1:
            d, s = w['pb_post']
            o.append('      part %d way point %d [%s%s] (%d, %d, %d): %d from the post of %s (%s%s)%s' % (si + 1, i + 1, w['kind'], ', STOP' if w.get('stop') else ', walk', *w['p'], d,
                     s['name'].split('!')[-1], s['weapon'], '' if s['active'] else '; his squad comes into the world LATER', ' - INSIDE the %d' % PB_REACH if d <= PB_REACH else ''))
        o.append('   R2, stops a guard can have reached by then (%d units a second along the mesh from his post; measured on the bank, a GUESS elsewhere): %d of the route\'s %d stops, '
                 '%d of them made for the turning circle%s' % (GUARD_RUN, len(r2), len(self.stops()), len(made),
                 '; %d way point(s) are walked in motion because a live run did so (LIVE_MOVING)' % len(live) if live else ''))
        for si, i, w in r2:
            s, dm, tg = w['pb_reach'][0]
            o.append('      part %d way point %d [%s] (%d, %d, %d): he is there %.0f s after the start for %.1f s; %d guard(s) can be, the first %s (%s) %.0f s after it, %d of mesh way%s'
                     % (si + 1, i + 1, w['kind'], *w['p'], w['t'], w['dwell'], len(w['pb_reach']), s['name'].split('!')[-1], s['weapon'], tg, dm, ' [made for the turning circle]' if w.get('halt') else ''))
        return o

    def die_sight(self):
        """--die, the rule of the first two rounds: the route is cut at the place from which the most guards (Enemy
        actors as the level places them) can be reached by a straight line on the mesh within DIE_SIGHT - a stand-in
        for 'they see him' - and he stands."""
        nav, guards = self.nav, [p for _g, p in self.L.st['guards']]
        best = first = None
        for si, seg in enumerate(self.segs):
            for i, w in enumerate(seg['pts']):
                if w.get('poly') is None or w['kind'] in ('land', 'drop'):
                    continue
                seen = []
                for g in guards:
                    if abs(g[1] - w['p'][1]) > 300 or d2(g, w['p']) > DIE_SIGHT:
                        continue
                    t = trace(nav, at4(w), g)
                    if t['ok'] or t['way'] > t['len'] - 150:
                        seen.append(d2(g, w['p']))
                if seen and (best is None or len(seen) > best[0]):
                    best = (len(seen), si, i, min(seen))
                if seen and min(seen) <= DIE_NEAR and first is None:
                    first = (len(seen), si, i, min(seen))
        pick = first or best
        if pick is None:
            self.note('--die: no guard of the level can be reached by a straight line on the mesh from any way point: he stands at the end of the route')
            seen, si, i, near = 0, len(self.segs) - 1, len(self.segs[-1]['pts']) - 1, 0
        else:
            seen, si, i, near = pick
        self.segs = self.segs[:si + 1]
        seg = self.segs[-1]
        seg['pts'] = seg['pts'][:i + 1]
        w = seg['pts'][-1] = dict(seg['pts'][-1])
        w.update(kind='die', hard=True, stop=True, r=50.0, guards=seen,
                 what='--die: he stands here: the first way point with a guard within %d by a straight line on the mesh (%d such guard(s) within %d, the nearest %d away, as the level '
                      'places them; it has %d)' % (DIE_NEAR, seen, DIE_SIGHT, near, len(guards)) if first else
                      '--die: he stands here: no way point has a guard within %d; this one has the most within %d (%d, the nearest %d away)' % (DIE_NEAR, DIE_SIGHT, seen, near))

    # ---- the legs, the radius, the speed
    def finish(self, seg):
        nav, pts = self.nav, seg['pts']
        for i, w in enumerate(pts):
            a = self.before(seg, i)
            leg = {'len': d2(a['p'], w['p']) if a else w.get('starts', {}).get('len', (0, 0))[1], 'ok': None, 'clear': None, 'why': ''}
            if 'starts' in w:                           # the first way point (it may be the --die place too)
                s = w['starts']
                leg.update(ok=s['ok'] == s['starts'], clear=s['mid'], why='' if s['ok'] == s['starts'] else '%d of %d START places' % (s['ok'], s['starts']))
            elif w['kind'] == 'land':
                leg.update(why='the drop: he falls and is carried on (off the mesh by its nature)')
            elif a is not None and a['kind'] == 'drop':
                leg.update(why='from the take-off of the drop')
            elif a is None or a.get('poly') is None:
                leg.update(ok=False, why='it starts off the mesh')
            else:
                t = trace(nav, at4(a), w['p'])
                leg['clear'] = t['mid']
                if w.get('poly') is None:
                    leg.update(ok=False, why='the place is off the mesh: the last %d of %d' % (t['len'] - t['way'], t['len']) if not t['ok'] else 'the place is off the mesh')
                elif not t['ok']:
                    leg.update(ok=False, why='OFF THE MESH after %d of %d, at (%d, %d, %d)' % (t['way'], t['len'], *t['end'][:3]))
                elif abs(t['end'][1] - w['p'][1]) >= 60.0:
                    leg.update(ok=False, why='it arrives %+d from the place\'s height (another floor)' % (t['end'][1] - w['p'][1]))
                else:
                    leg['ok'] = True
                if a['kind'] == 'land' and i >= 2:      # the goto runs from the take-off: the landing is no way point
                    leg['len'] += d2(pts[i - 2]['p'], a['p'])
            if self.lanes and a is not None and w['kind'] not in ('board', 'land'):
                n = max(1, int(d2(a['p'], w['p']) // 40))
                near = min(KB.lane_dist(self.lanes, lerp(a['p'], w['p'], t / n)) for t in range(n + 1))
                if near < KB.LANE_HALF + KB.LANE_MAN:
                    leg['lane'] = near
            for bx, bz, br, what in BLOCKED.get(self.L.map, ()):
                for src in ([a['p']] if a else [e[:3] for e in seg['entries']]):
                    n = max(1, int(d2(src, w['p']) // 20))
                    near = min(math.hypot(src[0] + (w['p'][0] - src[0]) * t / n - bx, src[2] + (w['p'][2] - src[2]) * t / n - bz) for t in range(n + 1))
                    if near < br * 0.75 and w['kind'] != 'land':
                        leg['blocked'] = min(leg.get('blocked', 1e9), near)
                        self.note('the leg into way point %d [%s] passes %d from (%d, %d): %s' % (i + 1, w['kind'], near, bx, bz, what))
            w['leg'] = leg
            nxt = pts[i + 1] if i + 1 < len(pts) and pts[i + 1]['kind'] != 'land' else (pts[i + 2] if i + 2 < len(pts) and pts[i + 1]['kind'] == 'land' else None)
            turn = 0.0
            if a is not None and nxt is not None:
                u, v = (w['p'][0] - a['p'][0], w['p'][2] - a['p'][2]), (nxt['p'][0] - w['p'][0], nxt['p'][2] - w['p'][2])
                if math.hypot(*u) > 1 and math.hypot(*v) > 1:
                    turn = abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))
            w['turn'] = turn
            cl = clear(nav, *w['p']) if w.get('poly') is not None else 0.0
            w['clear'] = cl
            # He STANDS at: a loot stop, a door he has to turn in (no room for a way point on its axis), the last way point of
            # a part, and whatever was marked a stop when it was made. drive() adds the stops the turning circle asks for.
            if w['kind'] == 'loot' or w.get('slow') or i + 1 == len(pts):
                w['stop'] = True
            r = R_OPEN
            if w['kind'] == 'door' or turn >= 45.0 or cl < 100.0:
                r = R_TURN
            if w['kind'] in ('enter', 'exit', 'level', 'loot', 'gate', 'rally', 'drop', 'stair'):
                r = min(r, R_HARD)
            if w.get('stop'):
                r = min(r, R_STOP)
            if w['kind'] == 'loot':
                # the bots' own loot place has the loot standing round it. LIVE, PB_DM03_board_hp: with radius 40 the goto to the
                # bank's stuck 54 .. 73 from it among the money boxes and ran out (K2c, radius 60: reached after one side step, 4.8 s).
                # He goes on to stand at each money object anyway: near is enough; where the money is on people he only stands
                r = R_OPEN if i + 1 < len(pts) and pts[i + 1]['kind'] == 'money' else R_HARD
            r = w.get('r') or r
            if not w.get('stop'):
                r = max(r, R_MOVE)                      # in motion: never under the review's floor (it was 0.45 of a short leg: 20 .. 35)
            w['r'] = r
            w['sprint'] = not self.walk and not w.get('stop') and leg['len'] >= 250.0 and w['kind'] not in ('money', 'board', 'foot', 'join') \
                and not (w['kind'] == 'first' and cl < 150.0) \
                and not (a is not None and a.get('slow'))
            # ('first' on a narrow place - Retomoto's balcony - is walked; so are the legs into and out of a door that is turned at)
            live = None if self.keep_stops or seg['name'] == 'fed' else \
                next((e for e in LIVE_MOVING.get(self.L.map, ()) if math.hypot(w['p'][0] - e[0], w['p'][2] - e[1]) <= 30.0), None)
            if live and w['kind'] in ('corner', 'door', 'align', 'way', 'stair', 'long') and i + 1 < len(pts):
                # a live run walked this place in motion with this radius: no stop here, whatever the model says (the stops
                # put him at rest where the guards come: THE POINT-BLANK RULE)
                w.pop('slow', None)
                w.update(stop=False, r=float(live[2]), sprint=bool(live[3]) and not self.walk, live=True)
            for src in ([a['p']] if a else [e[:3] for e in seg['entries']]):
                for name, g in self.doors():            # a pane of glass that goes when it is shot, beside or in this leg
                    dx, dz = w['p'][0] - src[0], w['p'][2] - src[2]
                    LL = dx * dx + dz * dz
                    t = 0.0 if LL < 1e-9 else max(0.0, min(1.0, ((g[0] - src[0]) * dx + (g[2] - src[2]) * dz) / LL))
                    dist = math.hypot(g[0] - src[0] - t * dx, g[2] - src[2] - t * dz)
                    if t >= 0.5 and dist <= GLASS_NEAR and abs(g[1] - (src[1] + t * (w['p'][1] - src[1]))) < 250.0 and (not w.get('glass') or dist < w['glass'][1]):
                        w['glass'] = (name, dist)               # t >= 0.5: the pane lies ahead on this leg, not behind its start
            w['from'] = a['p'] if a else None

    # ---- what the rig makes of it (rule 8)
    TIGHTEN = ('corner', 'door', 'way', 'stair', 'long', 'align', 'first', 'enter', 'exit', 'level', 'gate', 'rally', 'call')      # (not a loot place: finish())

    def box_list(self):
        """The stage boxes -> [(name, node, middle, reach)]: ENTERS_BANK, EXITS_BANK, the level exit boxes."""
        if getattr(self, '_boxes', None) is None:
            B, st = self.B, self.L.st
            boxes = [('ENTERS_BANK (stage 1)', k) for k in st['triggers'].get('ENTERS', [])] + [('EXITS_BANK (stage 2)', k) for k in st['triggers'].get('EXITS', [])] + \
                    [('level exit (stage 3, calls the vehicle)', k) for k in self.exits]
            self._boxes = []
            for nm, k in boxes:
                if B.sc.cls(k) == 'ZBoxPrimitive':
                    s = B.box(k)
                    self._boxes.append((nm, k, B.at(k), math.sqrt(sum(v * v for v in s)) + 150.0, s))
        return self._boxes

    def in_boxes(self, S, x, y, z, left):
        """Note in state S the stage boxes that (x, y, z) is inside (feet, or CHEST above them; the size values as half
        sizes, kl_fa_bots.in_box): S['boxes'][node] = (the way point whose goto it was, how far before its 'reached')."""
        B = self.B
        for _nm, k, mid, reach, s in self.box_list():
            if k not in S['boxes'] and abs(x - mid[0]) <= reach and abs(z - mid[2]) <= reach and \
                    (B.in_box(k, (x, y, z), 1.0, s) or B.in_box(k, (x, y + KB.CHEST, z), 1.0, s)):
                S['boxes'][k] = (self._at, left)

    def one(self, S, w, wide):
        """One goto to way point w from state S = dict x, z, head (None: not known), v, stand, foot, boxes -> (result,
        state after). wide: under TURN_WIDE and, from a stand, an arc from where he looks instead of a turn first."""
        tx, tz, r, v = w['p'][0], w['p'][2], w['r'], SPRINT if w['sprint'] else WALK
        foot, path, t0 = S['foot'].copy(), [], 0.0
        if foot.cur is None:
            foot.find(S['x'], S['z'])
        blind = foot.cur is None or w.get('poly') is None           # a place off the mesh by its nature: nothing to follow
        b = bearing(S['x'], S['z'], tx, tz)
        off0 = wrap(b - S['head']) if S['head'] is not None else 0.0
        if S['stand'] and not (wide and S['head'] is not None):
            t0 = abs(off0) / STAND_TURN                 # from a stand he turns before he walks
            res = steer(S['x'], S['z'], b, 0.0, tx, tz, r, v, TURN_WIDE if wide else TURN_MAX, None if blind else foot, path=path)
        elif S['stand']:
            res = steer(S['x'], S['z'], S['head'], 0.0, tx, tz, r, v, TURN_WIDE, None if blind else foot, ramp=STAND_ARC, path=path)
        else:
            res = steer(S['x'], S['z'], S['head'], S['v'], tx, tz, r, v, TURN_WIDE if wide else TURN_MAX, None if blind else foot, path=path)
        res.update(t=res['t'] + t0, d0=math.hypot(tx - S['x'], tz - S['z']), off0=off0, stand=S['stand'], clean=res['reached'] and res['turned'] <= ORBIT, blind=blind)
        if blind:                                       # where the mesh is under him afterwards is looked for when the next goto starts
            foot.cur = None
        after = dict(x=res['x'], z=res['z'], head=res['head'], v=res['v'], stand=False, foot=foot, boxes=dict(S['boxes']))
        if not wide:
            n = len(path)
            self.in_boxes(after, S['x'], S['foot'].h, S['z'], res['d0'])
            for k, (x, z, h) in enumerate(path):        # the stage boxes on the line he steers
                self.in_boxes(after, x, S['foot'].h if h is None else h, z, (n - k) * v * DT + r)
        return res, after

    def judge(self, states, w, ideal=None):
        """The goto to way point w from every state (one per START place while they differ) -> the worst of each test.
        ideal = (x, z, Foot): where the goto before would be 'reached' if he came in on the leg's own line (the review's
        chord: the radius before the way point); the chord from there is followed too."""
        out = dict(t=0.0, reached=True, clean=True, wide=True, off=0.0, off_wide=0.0, chord=0.0, chord0=0.0, chord_i=0.0, inside=0.0, stand=states[0]['stand'], behind=None,
                   back=None, near=0.0, arc=0.0, arc_reached=True, aim=True, d0=0.0, off0=0.0)
        after = []
        if ideal and w.get('poly') is not None:
            # as the review tests it: trace() all the way to the way point, on or off (a chord that is off gets its depth, 1 at least)
            f = ideal[2]
            t = trace(self.nav, (ideal[0], f.h, ideal[1], f.cur), w['p'])
            if not t['ok'] or abs(t['end'][1] - w['p'][1]) >= 60.0:
                out['chord_i'] = max(1.0, line_off(f, ideal[0], ideal[1], w['p'][0], w['p'][2])[0])
        for S in states:
            nom, A = self.one(S, w, False)
            wid, _A = self.one(S, w, True)
            out['t'] = max(out['t'], nom['t'])
            out['reached'] = out['reached'] and nom['reached']
            out['clean'] = out['clean'] and nom['clean']
            if not nom['clean']:
                out['near'] = max(out['near'], nom['near'])
            if not nom['blind']:
                out['off'] = max(out['off'], nom['off'])
                c_off, _way, _f = line_off(S['foot'], S['x'], S['z'], w['p'][0], w['p'][2], w['r'])
                out['chord'] = max(out['chord'], c_off)
                if S.get('short'):                      # from a stand: the chord from where he was when W went up, too (should he not roll on)
                    x0, z0, f0 = S['short']
                    c_off, _way, _f = line_off(f0, x0, z0, w['p'][0], w['p'][2], w['r'])
                    out['chord0'] = max(out['chord0'], c_off)
            if S['stand']:                              # the wide reading of a start from a stand is a note, not a verdict
                b, v = bearing(S['x'], S['z'], w['p'][0], w['p'][2]), SPRINT if w['sprint'] else WALK
                for da in (-AIM, AIM):                  # ... and so is this: he starts to walk a little off the line
                    g = steer(S['x'], S['z'], b + da, 0.0, w['p'][0], w['p'][2], w['r'], v, limit=12.0)
                    out['aim'] = out['aim'] and g['reached'] and g['turned'] <= ORBIT
                out['arc_reached'] = out['arc_reached'] and wid['clean']
                if not wid['blind']:
                    out['arc'] = max(out['arc'], wid['off'])
                if nom['d0'] < NEAR_BACK and abs(nom['off0']) > BACK_DEG and nom['d0'] > w['r']:
                    out['back'] = (nom['d0'], abs(nom['off0']))
                    if w['r'] < R_BACK:
                        out['behind'] = out['back']
            else:
                out['wide'] = out['wide'] and wid['clean']
                if not wid['blind']:
                    out['off_wide'] = max(out['off_wide'], wid['off'])
                out['inside'] = max(out['inside'], cannot_turn_in(nom['d0'], nom['off0'], w['r'], SPRINT if w['sprint'] else WALK))
            if abs(nom['off0']) > abs(out['off0']):
                out['d0'], out['off0'] = nom['d0'], nom['off0']
            after.append(A)
        if out['stand']:
            out['bad'] = max(out['chord'], out['chord0'], out['chord_i'], out['off']) > MESH_TOL
        else:
            out['bad'] = not out['clean'] or not out['wide'] or max(out['chord'], out['chord_i'], out['off']) > MESH_TOL or out['off_wide'] > MESH_SLACK
        return out, after

    def ideal(self, seg, i):
        """Where the goto to way point i of the segment is 'reached' when he comes in on the leg's own line: its radius
        before the way point -> (x, z, Foot there) or None (no leg, a drop, a place off the mesh)."""
        w, a = seg['pts'][i], self.before(seg, i)
        if a is None or a.get('poly') is None or w.get('poly') is None or w['kind'] in ('drop', 'land') or a['kind'] in ('drop', 'land'):
            return None
        L = d2(a['p'], w['p'])
        if L < 1.0:
            return None
        p = lerp(w['p'], a['p'], min(w['r'], L) / L)
        t = trace(self.nav, at4(a), p)
        return (p[0], p[2], Foot(self.nav, t['end'])) if t['ok'] else None

    def settle(self, seg, i, states):
        """The states after the goto to way point i of the segment: where he stands when it is a stop, where a drop lands
        him; the same state kept once."""
        pts, w, out, seen = seg['pts'], seg['pts'][i], [], set()
        for S in states:
            if w['kind'] == 'drop' and i + 1 < len(pts) and pts[i + 1]['kind'] == 'land':
                q = pts[i + 1]
                S.update(x=q['p'][0], z=q['p'][2], foot=Foot(self.nav, at4(q)))        # he falls and is carried on: in motion still
            elif w.get('stop'):
                h = S['head'] if S['head'] is not None else 0.0
                x, z = S['x'] + math.sin(math.radians(h)) * ROLL, S['z'] + math.cos(math.radians(h)) * ROLL
                S['short'] = (S['x'], S['z'], S['foot'].copy())
                if S['foot'].cur is None or S['foot'].to(x, z) == 0.0:
                    S.update(x=x, z=z)                  # (a roll that would leave the mesh: he is taken to stand where he was)
                S.update(v=0.0, stand=True)
                if w.get('push'):                       # then a push at a money object off the mesh: where it leaves him is not known
                    S.update(head=bearing(S['x'], S['z'], w['push'][0], w['push'][1]))
            key = (round(S['x'] / 15.0), round(S['z'] / 15.0), None if S['head'] is None else round(S['head'] / 10.0), S['stand'], tuple(sorted(S['boxes'])))
            if key not in seen:
                seen.add(key); out.append(S)
        return out

    def escalate(self, w, res):
        """Make way point w, the one BEFORE a goto the rig cannot do, more exact: a stop, then a closer stop -> said or not."""
        why = ('the rig\'s model does not reach the next way point from here in motion' if not res['clean'] else
               'under the wide turn rate the next way point is circled' if not res['wide'] else
               'the next steered line leaves the mesh by %d' % max(res['chord'], res['chord0'], res['chord_i'], res['off'])
               if max(res['chord'], res['chord0'], res['chord_i'], res['off']) > MESH_TOL else
               'under the wide turn rate the next steered line leaves the mesh by %d' % res['off_wide'])
        if w['kind'] == 'drop' or w.get('live'):
            return False                                # the take-off of a drop: he must walk on; a place a live run walked in motion
        if not w.get('stop'):
            w.update(stop=True, halt=why, r=min(w['r'], R_STOP))
            return True
        if res['stand'] and w['r'] > R_TIGHT and w['kind'] in self.TIGHTEN:
            w.update(r=R_TIGHT, tight=True, halt=(w.get('halt') or 'a stop') + '; nearer, because ' + why)
            return True
        return False

    def drive(self, seg):
        """Rule 8: every goto of the segment driven by steer() in order, from every START place; a goto the rig cannot do
        makes the way point before it a stop (escalate()) and is driven again. w['rig'] = judge()'s verdict."""
        pts = seg['pts']
        G = [i for i, w in enumerate(pts) if w['kind'] != 'land' and not w.get('blind')]
        first = [dict(x=e[0], z=e[2], head=h, v=0.0, stand=True, foot=Foot(self.nav, e), boxes={}) for e, h in zip(seg['entries'], seg['heads'])]
        before, k, tries = {0: first}, 0, 0
        while k < len(G):
            w = pts[G[k]]
            self._at = G[k]
            res, after = self.judge([dict(S, foot=S['foot'].copy(), boxes=dict(S['boxes'])) for S in before[k]], w, self.ideal(seg, G[k - 1]) if k else None)
            if res['bad'] and k and tries < 4 * len(G) and self.escalate(pts[G[k - 1]], res):
                tries += 1
                k -= 1                                  # the goto before is driven again: it ends in a stand now
                continue
            if res['back'] and (res['behind'] or not res['arc_reached']) and not w.get('tight') and w['kind'] in self.TIGHTEN:
                # behind him after a stop: the radius that was seen to do, then what the pessimistic arc asks for (the review:
                # 75); a later chord may take it back (escalate() marks it 'tight': then it is printed, not widened again)
                r = next((r for r in (R_BACK, 75.0, 90.0) if r > w['r'] and r < res['back'][0]), None)
                if r:
                    w['r'] = r
                    continue
            w['rig'] = res
            before[k + 1] = self.settle(seg, G[k], after)
            k += 1
        # the stage boxes the STEERED lines enter, from every START place: said at the way point where the last of them is in
        end, got = before.get(len(G), first), self.__dict__.setdefault('_got', set())
        for nm, node, _mid, _reach, _s in self.box_list():
            if node in got or not all(node in S['boxes'] for S in end):
                continue
            got.add(node)
            i = max(S['boxes'][node][0] for S in end)
            pts[i].setdefault('boxes', []).append((nm, self.B.sc.path[node][5:], max(S['boxes'][node][1] for S in end if S['boxes'][node][0] == i)))

    def doors(self):
        """The level's shatter-glass doors: nodes with a ShotActivate controller whose path says 'door' (Late Night
        Opening has them in three doorways of the route; whether an intact pane stops a walking player is NOT known)."""
        if self._doors is None:
            sc = self.B.sc
            self._doors = [(sc.path[k][5:].split('\\')[-1], self.B.at(k)) for k, _i, _v in kl_fa.controllers(sc, 'ShotActivate') if 'door' in sc.path[k].lower()]
        return self._doors

    def stage_boxes(self):
        """Which leg first puts him inside each stage box (feet, or 90 above them): ENTERS_BANK, EXITS_BANK, the level
        exit boxes. A box's three size values are taken as HALF sizes (kl_fa_bots.in_box); a bot's own place lies
        within 0.45 of them, inside by either reading."""
        B = self.B
        seen = set()                                    # by the straight legs of the plan (drive() has done the steered lines: w['boxes'])
        for seg in self.segs:
            for i, w in enumerate(seg['pts']):
                a = self.before(seg, i)
                srcs = [a['p']] if a else [e[:3] for e in seg['entries']]
                for src in srcs:
                    n = max(1, int(d2(src, w['p']) // 20))
                    for t in range(n + 1):
                        p = lerp(src, w['p'], t / n)
                        for _nm, k, mid, reach, s in self.box_list():
                            if k not in seen and abs(p[0] - mid[0]) <= reach and abs(p[2] - mid[2]) <= reach and \
                                    (B.in_box(k, p, 1.0, s) or B.in_box(k, (p[0], p[1] + KB.CHEST, p[2]), 1.0, s)):
                                seen.add(k)
        got = self.__dict__.get('_got', set())
        self.boxes_missed = [(nm, B.sc.path[k][5:]) for nm, k, _m, _r, _s in self.box_list() if k not in got and k not in seen]
        for nm, k, _m, _r, _s in self.box_list():
            if k in seen and k not in got:
                self.boxes_missed.append((nm, B.sc.path[k][5:] + ' - the straight legs of the plan cross it, the line the rig steers does NOT, from at least one START place'))

    # ---- numbers and text
    def points(self):
        for si, seg in enumerate(self.segs):
            for i, w in enumerate(seg['pts']):
                yield si, seg, i, w

    def length(self):
        return sum(w['leg']['len'] for _si, _seg, _i, w in self.points())

    def bad_legs(self):
        return [(si, i, w) for si, _seg, i, w in self.points() if w['leg']['ok'] is False]

    def risky_legs(self):
        return [(si, i, w) for si, _seg, i, w in self.points() if w['leg']['ok'] and w['leg']['clear'] is not None and w['leg']['clear'] < RISK_CLEAR]

    def tight_points(self):
        return [(si, i, w) for si, _seg, i, w in self.points() if w.get('poly') is not None and w['kind'] != 'land' and w['clear'] < TIGHT]

    # the rig's verdicts (drive()): each -> [(part, way point, w, text)]
    def rigged(self):
        return [(si, i, w, w['rig']) for si, _seg, i, w in self.points() if 'rig' in w]

    def not_reached(self):
        """Gotos the model does not reach without circling: under the rig's own rate, or in motion under the wide one."""
        out = []
        for si, i, w, g in self.rigged():
            if not g['clean']:
                out.append((si, i, w, 'NOT REACHED BY THE MODEL: %d away and %d degrees off his heading when it starts, radius %d at %s; it comes no nearer than %d%s'
                            % (g['d0'], abs(g['off0']), w['r'], 'a sprint' if w['sprint'] else 'a walk', g['near'],
                               '; by the exact test it lies %d inside the circle he cannot leave' % g['inside'] if g['inside'] > 0 else '')))
            elif not g['wide']:
                out.append((si, i, w, 'CIRCLED UNDER THE WIDE TURN RATE (%d degrees a second; reached under the rig\'s %d): %d away and %d degrees off when it starts, radius %d'
                            % (TURN_WIDE, TURN_MAX, g['d0'], abs(g['off0']), w['r'])))
        return out

    def steered_off(self):
        """Gotos whose steered line, or the straight chord from where the goto before was 'reached', leaves the mesh."""
        out = []
        for si, i, w, g in self.rigged():
            deep = lambda v: '%d' % v if v >= 1.0 else 'under 1' if v > 0.0 else '0'
            if max(g['chord'], g['off']) > MESH_TOL:
                out.append((si, i, w, 'STEERED LINE OFF THE MESH by %s (the straight chord from where the goto before leaves him: %s; the line the rig steers: %s)'
                            % (deep(max(g['chord'], g['off'])), deep(g['chord']), deep(g['off']))))
            elif g['chord_i'] > MESH_TOL:
                out.append((si, i, w, 'THE REVIEW\'S CHORD IS OFF THE MESH by %s (from the radius of the way point before, taken back along ITS leg\'s own line; the chord from where '
                                      'the model has him, and the line the rig steers, stay on the mesh)' % deep(g['chord_i'])))
            elif g['chord0'] > MESH_TOL:
                out.append((si, i, w, 'STEERED LINE OFF THE MESH by %s IF HE DOES NOT ROLL ON after the stop before it (the chord from where W goes up, %d short of where he is taken to '
                                      'stand; from there it stays on the mesh)' % (deep(g['chord0']), ROLL)))
            elif g['off_wide'] > MESH_SLACK:
                out.append((si, i, w, 'UNDER THE WIDE TURN RATE THE STEERED LINE IS OFF THE MESH by %d (on it under the rig\'s own)' % g['off_wide']))
        return out

    def behind(self):
        """From a stand: a target close behind him with a small radius; a target he circles when his aim is AIM off."""
        out = []
        for si, i, w, g in self.rigged():
            if g['behind']:
                out.append((si, i, w, 'BEHIND HIM AFTER A STOP: %d away, %d degrees off his heading, radius %d (seen live from a stand: 130 .. 143 away at 137 .. 144 degrees with '
                                      'radius %d)' % (*g['behind'], w['r'], R_BACK)))
            if g['stand'] and not g['aim']:
                out.append((si, i, w, 'FROM A STAND IT NEEDS HIS AIM: when he starts to walk %d degrees off the line he circles it (%d away, radius %d)' % (AIM, g['d0'], w['r'])))
        return out

    def stand_arcs(self):
        """From a stand, read pessimistically (no turn first: an arc at the wide rate): where that would not do."""
        out = []
        for si, i, w, g in self.rigged():
            if g['stand'] and not g['arc_reached']:
                out.append((si, i, w, 'IF HE DOES NOT TURN ON THE SPOT he circles it (%d away, %d degrees off, radius %d)' % (g['d0'], abs(g['off0']), w['r'])))
            elif g['stand'] and g['arc'] > MESH_SLACK:
                out.append((si, i, w, 'IF HE DOES NOT TURN ON THE SPOT the arc leaves the mesh by %d (he turns by %d degrees)' % (g['arc'], abs(g['off0']))))
        return out

    def stops(self):
        return [(si, i, w) for si, _seg, i, w in self.points() if w.get('stop') and not w.get('blind')]

    def text(self):
        L, B, st, o = self.L, self.B, self.L.st, []
        o.append('kl_playtest route %s' % L.folder)
        o.append('map %s; the places of AI heister %d (Squad#%02d) of bots.json, --until %s%s; mesh: %d polygons, the START row\'s part %d'
                 % (L.map, self.bot, self.bot, self.until, ' --die' if self.die else '', sum(self.nav.ok), self.nav.part_size[self.L.home]))
        n = sum(1 for _ in self.points())
        o.append('%d way points in %d part(s), %.0f m; legs off the mesh: %d; risky legs (the line nearer than %d to a border edge): %d; tight way points (nearer than %d): %d; longest leg %d'
                 % (n, len(self.segs), self.length() / 100, len(self.bad_legs()), RISK_CLEAR, len(self.risky_legs()), TIGHT, len(self.tight_points()),
                    max(w['leg']['len'] for _a, _b, _c, w in self.points())))
        halts = [w for _si, _i, w in self.stops() if w.get('halt')]
        rigs = self.not_reached() + self.steered_off() + self.behind() + self.stand_arcs()
        o.append('the rig (steer(): its turn rate %d degrees a second = a circle of %d at a walk, %d at a sprint; and the wide rate %d): gotos it does not reach: %d; '
                 'steered lines off the mesh: %d; behind him after a stop: %d; arcs if he does not turn on the spot: %d; stops: %d, of them %d made for the turning circle'
                 % (TURN_MAX, WALK / math.radians(TURN_MAX), SPRINT / math.radians(TURN_MAX), TURN_WIDE, len(self.not_reached()), len(self.steered_off()), len(self.behind()),
                    len(self.stand_arcs()), len(self.stops()), len(halts)))
        o.append('columns: leg = its length; line = least distance of the leg to a border edge of the mesh, its first and last %d left out; at = the same at the way point;'
                 ' r = the goto\'s radius; how = sprint / walk, STOP = W is let go there and the script waits %d ms; s = the model\'s seconds for the goto' % (END_ZONE, STOP_MS))
        for si, seg in enumerate(self.segs):
            e = seg['entries']
            o.append('')
            if seg['name'] == 'fed':
                o.append('PART %d (the FED, after his death; group %s of the AFTER_DEATH points): %s' % (si + 1, self.fed['group'],
                         'he appears on one of %d points, x %d..%d z %d..%d (the game picks one)' % (len(e), min(q[0] for q in e), max(q[0] for q in e), min(q[2] for q in e),
                                                                                                    max(q[2] for q in e)) if len(e) > 1 else
                         'he comes onto the mesh at (%d, %d, %d)%s' % (*e[0][:3], ' after the collision\'s way (%d gotos, below)' % len(self.fed['pre']) if self.fed['pre'] else '')))
            else:
                o.append('PART %d (%s): %s' % (si + 1, seg['name'], 'he starts on one of %d START places, x %d..%d z %d..%d (which one differs from run to run)' %
                                               (len(e), min(q[0] for q in e), max(q[0] for q in e), min(q[2] for q in e), max(q[2] for q in e)) if len(e) > 1 else
                                               'he arrives at (%d, %d, %d) (the jump entry)' % e[0][:3]))
            o.append('   #  kind          x       y       z    leg  line   at    r  how            s  what')
            for i, w in enumerate(seg['pts']):
                leg = w['leg']
                flag = 'OFF THE MESH: ' if leg['ok'] is False else 'RISKY: ' if leg['ok'] and leg['clear'] is not None and leg['clear'] < RISK_CLEAR else ''
                if w.get('poly') is not None and w['kind'] != 'land' and w['clear'] < TIGHT:
                    flag += 'TIGHT: '
                how = '-' if w['kind'] == 'land' else 'W only' if w.get('blind') else ('sprint' if w['sprint'] else 'walk') + (' STOP' if w.get('stop') else '')
                o.append('%4d  %-8s %7d %7d %7d  %5d  %4s %4s  %3d  %-11s %4s  %s%s%s' % (
                    i + 1, w['kind'], *(round(v) for v in w['p']), leg['len'], '-' if leg['clear'] is None else '%d' % leg['clear'], '-' if w.get('poly') is None else '%d' % w['clear'], w['r'],
                    how, '%.1f' % w['rig']['t'] if 'rig' in w and w['rig']['clean'] else '-' if 'rig' not in w else 'NO', flag, w['what'],
                    (' [' + leg['why'] + ']' if leg['why'] else '') + (' [IN THE VEHICLE\'S ROAD: %d from its line]' % leg['lane'] if 'lane' in leg else '') +
                    (' [PASSES %d FROM A PLACE WHERE A GOTO STUCK IN THE GAME: see the NOTE]' % leg['blocked'] if 'blocked' in leg else '') +
                    (' [GLASS DOOR %s %d from this leg: %s]' % (*w['glass'], 'he fires over its last %d, at a walk (--shoot)' % GLASS_RUN if self.shoot else 'not shot at')
                     if w.get('glass') else '') + (' [STOP: %s]' % w['halt'] if w.get('halt') else '') +
                    (' [LIVE: walked in motion with this radius in the game (LIVE_MOVING): no stop]' if w.get('live') else '') +
                    (' [THE WALK TEST OVER THE COLLISION DOES NOT REACH THIS PLACE from where he appears: see THE FED]' if w.get('coll') is False and
                     self.fed and self.fed.get('coll_end') == i and seg['name'] == 'fed' else '')))
                for a, b, _w, t in rigs:
                    if (a, b) == (si, i):
                        o.append('%s-> RIG: %s' % (' ' * 60, t))
                for nm, path, back in w.get('boxes', []):
                    o.append('%s-> inside %s %s, %d before this way point (on the line the rig steers)' % (' ' * 60, nm, path, back))
        o.append('')
        if self.boxes_missed:
            o.append('stage boxes the route never enters: ' + '; '.join('%s %s' % x for x in self.boxes_missed))
        if self.van:
            d = self.van
            o.append('vehicle: key-framed van %s: waits (%d, %d, %d), stops (%d, %d, %d) heading %d, boarding box at the stop (%d, %d, %d); in %.1f s, stands %.1f s, out %.1f s'
                     % (d['name'].split('\\')[-1], *d['wait'], *d['stop'], d['heading'], *d['board'], *d['seconds']))
        elif st['action']:
            o.append('vehicle: %s; boarding box %s at (%d, %d, %d) (it stands still)' % ('%s / %s' % (st['vehicle'][2], st['vehicle'][0]) if st['vehicle'] else '?',
                                                                                     B.sc.names[st['action']], *B.at(st['action'])))
        bad = self.bad_legs()
        o.append('LEGS THAT DO NOT STAY ON THE MESH: %s' % ('none' if not bad else ''))
        for si, i, w in bad:
            o.append('   part %d way point %d [%s] (%d, %d, %d): %s' % (si + 1, i + 1, w['kind'], *w['p'], w['leg']['why']))
        risky = self.risky_legs()
        o.append('RISKY LEGS (on the mesh, the line nearer than %d to a border edge): %s' % (RISK_CLEAR, 'none' if not risky else ''))
        for si, i, w in risky:
            o.append('   part %d way point %d [%s] (%d, %d, %d): %d from a border edge over %d of leg' % (si + 1, i + 1, w['kind'], *w['p'], w['leg']['clear'], w['leg']['len']))
        tight = self.tight_points()
        o.append('TIGHT WAY POINTS (nearer than %d to a border edge: a door or an aisle the mesh leaves under %d wide): %s' % (TIGHT, 2 * TIGHT, 'none' if not tight else
                 ', '.join('%d.%d (%d)' % (si + 1, i + 1, w['clear']) for si, i, w in tight)))
        for head, rows in (('GOTOS THE RIG\'S MODEL DOES NOT REACH (the turning circle: he would circle the way point until the timeout)', self.not_reached()),
                           ('RISKY: STEERED LINES THAT LEAVE THE MESH (the line from where the goto before was \'reached\', not the leg between the way points)', self.steered_off()),
                           ('RISKY: A TARGET BEHIND HIM AFTER A STOP', self.behind()),
                           ('RISKY ONLY IF HE DOES NOT TURN BEFORE HE WALKS, from a stand (the wide circle, no turn first)', self.stand_arcs())):
            o.append('%s: %s' % (head, 'none' if not rows else ''))
            for si, i, w, t in rows:
                o.append('   part %d way point %d [%s] (%d, %d, %d): %s' % (si + 1, i + 1, w['kind'], *w['p'], t))
        made = [(si, i, w) for si, i, w in self.stops() if w.get('halt')]
        o.append('STOPS MADE FOR THE TURNING CIRCLE (the way point is walked to within its radius, W is let go, %d ms; the next goto starts from a stand): %s'
                 % (STOP_MS, 'none' if not made else ', '.join('%d.%d' % (si + 1, i + 1) for si, i, w in made)))
        o += self.danger_text()
        if self.fed:
            o += fed_text(self.L, self.fed)
        for t in self.notes:
            o.append('NOTE ' + t)
        return o


# ------------------------------------------------------------------ the tree, the ini
ROWS_DOWN = 7           # Arcade page: Start, Rules, Stats, Highscores, Leaderboards, Heister, Guns -> 'Dead Men maps' (mk_tab_inis.py; run TAB_PAGE)
HEAD = """; %(tag)s (tools\\kl_playtest.py %(args)s): %(what)s
; A SCRIPTED PLAYER: the route is the AI heisters' own planned places of the build, thinned for klauto's straight-line 'goto'
; (re\\playtest.md). NOT RUN IN THE GAME when this file was written. The route and what the log must show:
;   %(name)s.route.txt, %(name)s.expect.txt beside this file.
; Needs: <DD>\\KLExpansion = the tree %(tree)s%(needs)s
;   and a TEST hook (klhook\\build_auto.bat; it blocks every Steam write). Run:
;   python tools\\kl_autotest.py %(wait)d --tag %(tag)s --hook <TEST dinput8.dll folder> --ini <this file> --shots %(shots)s
; The game window must be in front for the whole run (memory: scripted-run-needs-foreground).
[KLHook]
ContinueAsserts=1
MaxDumps=4
MaxAsserts=200
[Steam]
%(block)s
[Character]
Enable=1
Char=9
Mask=0
Outfit=0
Log=1
[Guns]
Start=0
Set=0
[Load]
NudgeMs=1000
[Memory]
Enable=1
ReserveMB=128
[Talk]
Enable=1
[CrewJoin]
Enable=1
[Shoulder]
Log=0
[Balance]
Enable=1
Risk=2
CopToCrew=0.05
Log=1
[Auto]
EndHooks=1
Enable=1
Hooks=0
Nodes=0
CmdDrop=DefaultScene,AutoExit
CmdAdd=-o DisableSplashScreens -o AutoExit=%(autoexit)d
StallMs=600000
MaxRunMs=%(maxrun)d
LoadedMs=0
Unfocused=1
BlockReal=1
FirstChance=1
PosLogMs=2000
"""
TO_PAGE = ['waitwin CampaignMenu 180000', 'wait 1500', 'tap ESCAPE', 'waitwin MainMenu 8000', 'wait 1500', 'tap DOWN', 'wait 1200', 'tap RETURN',
           'waitwin HeistModeMenu 8000', 'wait 3000', 'windows'] + ['tap DOWN', 'wait 500'] * ROWS_DOWN + \
          ['wait 2500', 'log focus should be on the eighth row, Dead Men maps', 'windows', 'tap RETURN', 'waitwin HeistPlayMenu2 8000', 'wait 3000', 'windows']
# the scripted player never shoots; at the owner's balance (Risk=2: a police bullet at full weight, 400 health) and even at the stock
# one he is dead in the first room with guards (runs RN6, RN13, RN14: 10 .. 40 s). So a route script makes him bullet-proof ...
# ... LIVE (the lead's runs K1_DM03_wall_dry, K2_DM03_wall, K2b_DM03_wall_log of this tool's first wall script, 2026-10-11 09:24 - 09:50): the two
# factors alone did NOT keep him alive - he was dead on the bank's stairs to the garage, near (-300 .. -390, 440, -5680 .. -5780), 25.6 .. 29.8 s
# after 0x19 in three runs of three. K2b's balance log: bullets cost him 0.7 .. 4.3 each (the 0.02), then 151.2, 151.2 and 30.2 within 0.31 s -
# 151.2 is 100 x the bullets of the burst before it (and 5 x 30.24): the same weapon at a factor the two keys did not set, or a shotgun at about
# full weight; who shot was not established. So the keys' most: ten times the health (5,500) and all of it back half a second after a hit.
# LIVE with that (K2c_DM03_wall_hp, PB_DM03_board_hp): he came through the bank twice of twice (steps of up to 759 among his losses). A TEST AID.
# THE THIRD ROUND (re\playtest.md 10.2): that 151.2 is the fire task's point-blank rule (re\melee_damage.md: kl2 0x8c62e0, a firing guard within 160
# units sends a hit worth 100 bullets a step, and the dial DOES scale it: 72.0 x 1.05 x 100 x 0.02). With the 5,500 he was still dead on those stairs
# in 3 runs of 5 of the scripts that STOP there (FO_J0 / J4 / J3; FO_J1 came through with 796 left): the .45 costs 758.6 a step, six steps a second.
# So the dial is COP_DIAL now: 0.001 = 37.9 a step from the .45, 7.6 from a Type 79 - still seen in the log's 'you lost' lines - and the stairs are
# walked in motion again (LIVE_MOVING). What the police do to the human is not what these runs measure.
def survive(cop=COP_DIAL):
    v = '%.4g' % cop
    return [('Balance', 'Ramp', '0'), ('Balance', 'CopToYou', v), ('Balance', 'CrewToYou', v), ('Balance', 'PlayerHealth', '10'), ('Balance', 'RegenDelay', '0.5'),
            ('Balance', 'RegenTime', '0.5'), ('Balance', 'Log', '2')]


SURVIVE = survive()
# ... and --die makes the first hit his last (27 of health, a police bullet times 20)
FRAGILE = [('Balance', 'Ramp', '0'), ('Balance', 'CopToYou', '20'), ('Balance', 'PlayerHealth', '0.05'), ('Fed', 'Enable', '1'), ('Fed', 'Player', '1'), ('Fed', 'Log', '1')]
# ... and --fed-walk without --fed-die: the keys for a fed who is to WALK (review 3, M1; a READING of klbalance.c, NOT RUN).
# FedMirror=0 = the game's own 550 of health for a police player (klbalance.c 2 a3; live, PT_DM03_die_r2: 'a POLICEMAN: left alone: 550.0 of
# 550.0') - and then NOTHING is exchanged: from the tick he is police his game reads the OTHER float of each pair (klr_mir = {1, 0, 4, 5, 2, 3};
# kl2 0x591bbe, 0x8b80a0, 0x7c1bf0), so every key means two things in one run:
#     key (slot)          while he is the hero                 once he is police
#     CopToCrew (+0x00)   a police bullet on a heister         a heister's bullet on a police AI
#     CrewToCop (+0x04)   a heister's bullet on the police     a police AI's bullet on a heister
#     CopToYou  (+0x08)   a police bullet on him               a HEISTER's bullet on him (the fed)
#     CrewToYou (+0x10)   a heister's bullet on him            a police AI's bullet on him (a colleague's stray)
# The first round's scripts had CopToYou=20 and CopToCrew=0.005 'so that the crew lives': after the switch that was a heister's bullet on the fed
# x 20 (about 940 against his 550: his second, final death) and a police AI's bullet on a heister x 1.0 (CrewToCop under Risk=2) - the crew NOT
# protected, as in PT_DM03_die_r2 (all seven dead 15 .. 47 s after the switch) - while the 0.005 only made the crew harmless. So:
#   no CopToYou key (FED_WALK_DROP): Risk=2's 1.0. The hero's 27.5 of health still die to one bullet (a Type 79's is 75.6 near, 39 at 50 m;
#       a shotgun's hit far off may take two), and a heister's bullet costs the fed x 1.0 of his 550 - about what it costs in the owner's game;
#   CopToCrew = CrewToCop = 0.005: a police bullet costs a heister x 0.005 on BOTH sides of the switch. The price: a heister's bullet costs
#       the police x 0.005 too, all round long - the crew cannot clear a room, the guards live and come close (their point-blank step is still
#       43 of a heister's 252, six a second). ASSUMED that this leaves a crew in play for the 2 .. 4 minutes of the walk; a GUESS;
#   CrewToYou = 0.001: a colleague's stray bullet does not end the fed's walk (while he is the hero it is a heister's bullet on him: only a
#       traitor fires one, and the police kill him all the same).
# EndSeconds=0: klfed does not end the round when no heister is left to hunt (the walk is what the run is for).
FED_WALK_DROP = ('CopToYou',)
FED_WALK = [('Balance', 'FedMirror', '0'), ('Balance', 'CopToCrew', '0.005'), ('Balance', 'CrewToCop', '0.005'), ('Balance', 'CrewToYou', '0.001'), ('Fed', 'EndSeconds', '0'),
            ('Fed', 'Log', '2')]
# --fed-die (F3): FedMirror=1 - the pairs are written exchanged, every key keeps the meaning of its name on both sides (live: FD3_DM03_die), the
# fed has the hero's 27.5 of health and a heister's bullet costs him CrewToYou = 1.0: the first is his second death. (A colleague's stray is
# CopToYou = 20 there: it kills him as well - the run then shows a second death, not F3's 'shot by the crew', and the log's 'you lost' line
# cannot tell the two apart: a loss is at most his 27.)
FED_DIE = [('Balance', 'FedMirror', '1'), ('Balance', 'CopToCrew', '0.005'), ('Fed', 'EndSeconds', '0'), ('Fed', 'Log', '2')]


def find_tree(folder):
    """-> (the KLExpansion folder, its manifest)."""
    for f in (folder, os.path.join(folder, 'KLExpansion')):
        if os.path.isfile(os.path.join(f, 'manifest.json')):
            return f, json.load(open(os.path.join(f, 'manifest.json')))
    raise SystemExit('%s: no manifest.json (an installed tree: <work>\\build\\<name> or its KLExpansion folder)' % folder)


def ini_set(text, section, key, value):
    """Set key=value in the FIRST [section] of an ini text (Windows reads only the first of two sections of one name:
    the tree's block and the run's sections both have [Bots]); a new section goes in front of [Auto]."""
    lines = text.split('\n')
    head = next((i for i, l in enumerate(lines) if l.strip().lower() == '[%s]' % section.lower()), None)
    if head is None:
        at = next(i for i, l in enumerate(lines) if l.strip().lower() == '[auto]')
        lines[at:at] = ['[%s]' % section, '%s=%s' % (key, value)]
        return '\n'.join(lines)
    end = next((i for i in range(head + 1, len(lines)) if lines[i].strip().startswith('[')), len(lines))
    for i in range(head + 1, end):
        if lines[i].split('=')[0].strip().lower() == key.lower() and not lines[i].lstrip().startswith(';'):
            lines[i] = '%s=%s' % (key, value)
            return '\n'.join(lines)
    lines.insert(head + 1, '%s=%s' % (key, value))
    return '\n'.join(lines)


def parse_extra(text):
    """"[Section];Key=V;Key=V;[Other];Key=V" -> [(section, key, value)]."""
    out, sec = [], None
    for part in (p.strip() for p in (text or '').split(';')):
        if not part:
            continue
        if part.startswith('['):
            sec = part.strip('[]')
        elif '=' in part and sec:
            k, v = part.split('=', 1)
            out.append((sec, k.strip(), v.strip()))
        else:
            raise SystemExit('--extra: "%s" is neither [Section] nor Key=Value behind one' % part)
    return out


# ------------------------------------------------------------------ the script
class Script:
    """The [Script] lines for a route, and what the hook's log must show beside them."""

    def __init__(self, route, opt):
        self.R, self.o = route, opt
        self.lines, self.expect, self.secs, self.clock, self.go_line, self.go_secs = [], [], 0.0, [], 0, 0.0
        self.by_design, self.gotos, self.stages = [], [], []      # script lines of gotos that end by their timeout on purpose; every goto; the log lines of each stage
        self.L = route.L
        self.first_goto, self.in_fed, self.round, self.fed_line, self.label_n = False, False, 1, None, 0

    def add(self, line, secs=0.0):
        cmd = line.split(' ', 1)
        if cmd[0] in ('log', 'pos') and len(cmd) > 1 and len(cmd[1]) > TEXT_MAX:
            line = cmd[0] + ' ' + cmd[1][:TEXT_MAX]
        if len(line) > 190:
            raise ValueError('script line too long: ' + line)
        self.lines.append(line)
        self.secs += secs
        self.clock.append(self.secs)                    # the estimated time at which this line is done
        return len(self.lines)

    def want(self, text, at=None):
        self.expect.append((at or len(self.lines), text))

    def wait(self, ms):
        return self.add('wait %d' % ms, ms / 1000.0)

    def hold_e(self, ms):
        self.add('down E'); self.wait(ms); self.add('up E')

    def goto(self, w, keep):
        v = SPRINT if w['sprint'] else WALK
        rig = w.get('rig')
        nominal = rig['t'] + 0.1 if rig and rig['clean'] else w['leg']['len'] / v + 0.4      # the model's time for it (drive()), else the leg at its speed
        timeout = int(min(20000, max(6000, math.ceil((3.0 * nominal + 4.0) * 2) * 500)))
        if self.R.die and self.R.fed and not self.in_fed and not self.o['rig3']:
            # --die --fed-walk on a rig that cannot see his death (review 3, S1): when he dies on the way - 2 live deaths of 3 - every goto of the
            # hero that is left runs to its timeout and steers the FED at the hero's way points. So these are short: DIE_GOTO. (A hero who misses a
            # way point by it goes on from where he is; he is there to be shot.)
            timeout = int(min(timeout, max(DIE_GOTO[2], math.ceil((DIE_GOTO[0] * nominal + DIE_GOTO[1]) * 2) * 500)))
        if w.get('timeout'):
            timeout = w['timeout']
        if self.first_goto:                             # the first goto of a round: should the countdown outlast the wait, W is held until he can move
            timeout, self.first_goto = FIRST_TIMEOUT, False
        n = self.add('goto %d %d %d %d%s%s' % (round(w['p'][0]), round(w['p'][2]), round(w['r']), timeout, ' sprint' if w['sprint'] else '', ' keep' if keep else ''), nominal)
        w['line'] = n
        self.gotos.append(dict(line=n, x=round(w['p'][0]), z=round(w['p'][2]), r=round(w['r']), kind=w['kind'], stop=not keep, ms=int(nominal * 1000), fed=self.in_fed,
                               round=self.round, to=timeout))
        return n

    def raw_goto(self, p, r, ms, kind, what):
        """A goto that is no way point of the route (the fed's way over the collision; his blind ones): at a walk."""
        n = self.add('goto %d %d %d %d' % (round(p[0]), round(p[2]), r, ms), min(ms / 1000.0, 8.0))
        self.gotos.append(dict(line=n, x=round(p[0]), z=round(p[2]), r=r, kind=kind, stop=True, ms=ms, fed=True, round=self.round, what=what, to=ms))
        return n

    def stage(self, key, pattern, what, need=True, after=None):
        """A log line that shows a stage (for `judge`): a regular expression, what it means, whether the run needs it."""
        self.stages.append(dict(key=key, re=pattern, what=what, need=need, after_line=after or len(self.lines)))

    def menu(self, entry):
        for s in TO_PAGE:
            self.add(s)
        k = entry['menu_entry']
        for s in ('sel HeistLevel_P2 0xceceec %d' % k, 'wait 2500', 'expect 0xceceec %d' % k, 'log starting entry %d = %s (slot %s, Maps\\%s)' % (k, entry['name'], entry['slot'], entry['id']),
                  'msg HeistLevel_P2 StartGame', 'waitload 300000'):
            self.add(s)
        n = self.add('log level loaded: %s' % entry['name'])
        self.want('script %d: level loaded: %s   [the menu route worked: Arcade -> Dead Men maps -> entry %d -> StartGame]' % (n, entry['name'], k), n)
        self.secs += 62.0                               # start .. 'level loaded' in tonight's runs: 58 .. 62 s
        self.add('onwin HeistStatusLeaderboard score')

    def go(self):
        """Wait for the round (session state 0x19: the hero is put on a START place then) AND for the moment he can move:
        FREE_S later (the round's own countdown). A goto before that only wastes its timeout - live, PT_DM03_die_r2: the
        first way point was lost that way - and on the unpatched rig it is SKIPPED after 6 s ('no moving player found').
        Retomoto: he waits on the balcony until 2 s after the glass has gone (blast_timer after 0x19: runs R7c, I5)."""
        rig2, rt = self.o['rig2'], self.L.rt
        free = FREE_S + FREE_PAD
        why = 'he can move 10.1 .. %.1f s after 0x19; the route starts %.1f s after it' % (FREE_S, free)
        if rt:
            blast = float(rt.get('blast_timer', 16.5))
            free = max(free, blast + 2.0)
            why = 'balcony: the glass goes %.1f s after 0x19; he walks %.1f s after it' % (blast, free)
        if rig2:
            n = self.add('waitstate 0x19 90000', sum(LOAD_GO) / 2)
            self.go_secs = self.secs
        else:
            # the unpatched rig cannot see the state: 0x19 came LOAD_GO after 'level loaded' in every run of tonight's hook settings
            n = self.wait(int(math.ceil(LOAD_GO[1] + 0.4) * 1000))
            self.go_secs = self.secs - (math.ceil(LOAD_GO[1] + 0.4) - sum(LOAD_GO) / 2)
            free -= math.ceil(LOAD_GO[1] + 0.4) - LOAD_GO[1]        # ... so at least this much of the countdown is over already
        self.go_line = n
        self.want('session: state 0x18 -> 0x19 (game mode 4)   [the round begins; it must come BEFORE the next line]', n)
        self.stage('the round begins', r'session: state 0x18 -> 0x19', 'session state 0x19', after=n)
        if not self.R.die:
            self.stage('the escort follows', r'escort: record \d+ re-pointed', 'the escort bot was called after a human who moved', need=False, after=n)
        n = self.add('peek 0x168e598+0x70 session-state-must-be-0x19')
        self.want('script %d: peek 0168e598+70 = 00000019 ...' % n, n)
        self.add('pos spawn')
        if self.o['rig3'] and self.R.fed:
            k = self.add('onbody fed%d' % self.round)
            self.want('script %d: when the local player becomes another object (now xxxxxxxx), go to label \'fed%d\'   and, 5 s after his death,   script: the local player is another '
                      'object (... -> ...) at (x, y, z), line N: going on at label \'fed%d\'   [--rig3: the hero\'s gotos that were left are skipped: the place in this line is the very '
                      'AFTER_DEATH point he was put on]' % (k, self.round, self.round), k)
        self.add('log ' + why)
        self.wait(int(round(free * 2) * 500))
        n = self.add('log GO+: the route starts (--until %s%s)%s' % (self.R.until, ' --die' if self.R.die else '', ' round %d' % self.round if self.o['rounds'] > 1 else ''))
        self.first_goto, self.in_fed = True, False
        self.want('script %d: GO+: the route starts   [%.1f s or more after the session state became 0x19: he can move. The first goto has a timeout of %d s: should the countdown '
                  'be longer on this map, W is held until he can move and the goto is not lost]' % (n, free, FIRST_TIMEOUT / 1000), n)
        if self.R.die:
            self.want('fed: ARMED: your death will not end the round - you come back as police (N AI heister(s) in play, ...)   [said when the round starts; needs [Fed] Enable=1 Player=1]', n)
        else:
            self.want('escort: you: record 0, player ..., feet (x, y, z) ...   and 3 s later   escort: record N (actor ..., soldier ...) chosen: ...   [needs [Bots] Escort=1]', n)

    # ---- one way point
    def walk(self):
        R, o = self.R, self.o
        flat = [(si, seg, i, w) for si, seg, i, w in R.points() if w['kind'] != 'land']
        nloot = nmoney = 0
        self.t_call = None
        stops0 = [n for n, x in enumerate(flat) if x[0] == 0 and x[3]['kind'] in ('loot', 'money')]
        hold_at = stops0[-1] if (o.get('join_after') and self.L.rt and stops0) else None       # the tower's last loot stop
        for n, (si, seg, i, w) in enumerate(flat):
            nxt = flat[n + 1][3] if n + 1 < len(flat) and flat[n + 1][0] == si else None
            if seg['name'] == 'fed' and not self.in_fed:
                self.fed_start()
            elif i == 0 and si > 0:
                k = self.add('pos part-%d-%s-starts' % (si + 1, seg['name']))
            stop = bool(w.get('stop') or w['kind'] == 'loot' or nxt is None)
            if w['kind'] == 'board' and R.boarding == 'van':
                if o['rig2'] or o['blind_board']:
                    self.board_van(w, flat[n - 1][3])
                else:
                    self.no_board(flat[n - 1][3])
                continue
            mark = len(self.lines)
            if w.get('blind'):                          # the jump box: W alone, no steering (Route.join_tail)
                self.add('down W')
                self.wait(w['blind'])
                g = w['line'] = self.add('up W')
            elif w.get('glass') and R.shoot:            # --shoot. A shatter-glass door: the fire button is down for the last GLASS_RUN of this leg,
                if w.get('from') and w['leg']['len'] > GLASS_RUN + 100.0:      # which is walked (nobody fires at a sprint)
                    p = lerp(w['from'], w['p'], 1.0 - GLASS_RUN / w['leg']['len'])
                    self.goto(dict(w, p=p, r=R_MOVE, leg=dict(w['leg'], len=w['leg']['len'] - GLASS_RUN), rig=None), keep=True)
                    w = dict(w, leg=dict(w['leg'], len=GLASS_RUN), rig=None)
                w = dict(w, sprint=False)
                self.add('mdown 0')
                g = self.goto(w, keep=not stop)
                k = self.add('mup 0')
                self.want('script %d: goto (%d, %d) reached ...   [--shoot: he FIRES from script %d to %d: the glass door %s is %d from this leg; the AI heisters use the same door]'
                          % (g, round(w['p'][0]), round(w['p'][2]), g - 1, k, *w['glass']), k)
            else:
                g = self.goto(w, keep=not stop)
                if w.get('glass'):
                    self.want('script %d: goto (%d, %d) reached ...   [the glass door %s is %d from this leg and he does NOT fire: "reached" = an intact pane does not stop a walking '
                              'player (or the crew had opened it); "goto is stuck" / "NOT reached" here = it does: then run the --shoot script]'
                              % (g, round(w['p'][0]), round(w['p'][2]), *w['glass']), g)
            first_goto = n == 0
            if first_goto and o['rig2']:
                self.want('players: the local one is #k at ... (the game\'s own pointer, slot N)   [the patched klauto takes the player from the game: seen live, run PT_DM03_die_r2. '
                          'Then, for every goto, "script N: goto (x, z) reached in T ms: at (x, y, z)" - a "NOT reached" or "goto is stuck" line names a bad leg]', g)
            elif first_goto:
                self.want('players: the moving one is #k at ...   [klauto found him: only then does a goto steer; then, for every goto,'
                          ' "script N: goto (x, z) reached in T ms: at (x, y, z)" - a "NOT reached" or "goto is stuck" line names a bad leg]', g)
            if self.t_call is not None:
                self.t_call += w['leg']['len'] / (SPRINT if w['sprint'] else WALK) + 0.4
            for nm, path, _back in w.get('boxes', []):
                k = self.add('pos %sin-%s' % ('fed-' if self.in_fed else '', path.split('!')[-1].split('\\')[-1]))
                if self.in_fed:                         # a police player in a stage box: what the rules make of it is not known; the `pos` line is all
                    continue
                if nm.startswith('ENTERS'):
                    self.want('bots: record 0 (you): heist stage 0 -> 1   [%s; between script %d and %d]' % (path, max(1, g - 1), k), k)
                    self.stage('stage 1', r'bots: record 0 \(you\): heist stage \d -> 1', 'he walked into %s' % path, after=k)
                elif nm.startswith('EXITS'):
                    self.want('bots: record 0 (you): heist stage 1 -> 2   [%s; between script %d and %d]' % (path, max(1, g - 1), k), k)
                    self.stage('stage 2', r'bots: record 0 \(you\): heist stage \d -> 2', 'he walked into %s' % path, after=k)
                else:
                    self.want('bots: record 0 (you): heist stage N -> 3   [%s; between script %d and %d] and, when nobody called the vehicle before, '
                              '"bots: L1 s19 van 1 ..." (it drives in)' % (path, max(1, g - 1), k), k)
                    self.stage('stage 3', r'bots: record 0 \(you\): heist stage \d -> 3', 'he walked into the level exit box %s' % path, after=k)
                    self.stage('the vehicle comes', r'bots: L\d+ s\w+ van [1-4] ', 'somebody in a level exit box called it', need=False, after=k)
            kind = w['kind']
            if kind == 'call':
                self.add('log IN THE EXIT BOX: van called NOW if nobody did (want van 1, then 3 = it waits)')
                self.t_call = 0.0
            elif w.get('call') and self.t_call is None:
                self.add('log IN THE EXIT BOX: van called NOW if nobody did (want van 1, then 3 = it waits)')
                self.t_call = 0.0
            if kind == 'loot':
                nloot += 1
                k = self.add('pos loot-stop-%d' % nloot)
                self.want('pos loot-stop-%d: me #k (%d, %d, %d) ...   [at the bots\' loot place: %s]' % (nloot, *w['p'], w['what'][:90]), k)
                if not (nxt is not None and nxt['kind'] == 'money'):
                    self.wait(int(o['loot_wait'] * 1000))
            elif kind == 'money':
                nmoney += 1
                if w.get('push'):
                    self.wait(STOP_MS)
                    k = self.add('goto %d %d 40 %d' % (round(w['push'][0]), round(w['push'][1]), LOOT_PUSH_MS), LOOT_PUSH_MS / 1000.0)
                    self.by_design.append(k)
                    self.want('script %d: goto (%d, %d) NOT reached in %d ms ...   [EXPECTED, by design: a push at the money object from the mesh\'s border - the table stops him and the '
                              'goto ends by its timeout. This line does NOT void the run]' % (k, round(w['push'][0]), round(w['push'][1]), LOOT_PUSH_MS), k)
                self.hold_e(int(o['loot_hold'] * 1000))
                self.wait(300)
                k = self.add('pos money-%d-%s' % (nmoney, w['name'].split('\\')[0][-40:]))
                self.want('bots: ... | 0 you in-play gN $M ...   [$M grows by up to %d while script %d - %d hold E at %s; a part is paid every 0.2 .. 0.7 s x the tuning factor]'
                          % (w['amount'], g + 1, k - 1, w['name']), k)
                if not (nxt is not None and nxt['kind'] == 'money'):
                    self.wait(int(o['loot_wait'] * 1000))
            elif kind == 'join':
                self.wait(2500)
                k = self.add('pos after-the-join')
                self.want('join: player 0 entered box N at (x, 19601, z): jump to entry 5 \'Specials!JumpPoints!06_Exit\' requested ...   [script %d walked him into the box]' % g, g)
                self.want('crewjoin: the jump to entry 5 \'...06_Exit\' is pending: the AI heisters in play are moved first (EARLY)   and   crewjoin: N moved; ...   [needs [CrewJoin] Enable=1]', g)
                self.want('join: player 0 is at (6272, 5xx, -6305) 500 ms after the request   and   pos after-the-join: me #k (62xx, 57x, -63xx) ...   [he is in the lobby car]', k)
                self.stage('the join', r'join: player 0 entered box', 'the W-only step took him into the jump box', after=k)
                self.stage('the crew follows', r'crewjoin: \d+ moved', 'klcrew_rt moved the AI heisters to the lobby', need=False, after=k)
            elif kind == 'wait':
                self.at_vehicle(w)
            elif kind == 'board':                       # a box that stands still (the park's helicopter)
                self.board_fixed(w)
            elif kind == 'foot':
                self.wait(1000)
                k = self.add('pos at-the-foot-of-the-wall')
                self.want('pos at-the-foot-of-the-wall: me #k (%d, 220, %d +-25) heading %.0f +-20   [he stands %d from the face, looking at it]'
                          % (w['p'][0], w['p'][2], w.get('heading', 0.0) + 0.0, CLIMB_STAND), k)
                self.want('climb: at the foot of edge N: node (...), ... from the face, speed 0, facing 0.9x; ...   then   climb: edge N: started /Movement/Climb/Up/High ...'
                          '   [needs a hook with klclimb.c wired and [Climb] Enable=1 Key=0; re\\climb.md K1 / K2]', k)
                self.wait(6000)
                k = self.add('pos after-the-climb')
                self.want('pos after-the-climb: me #k (x, 42x, z) ...   [y about 424 = he stands on the wall; 220 = he is still at its foot]', k)
                self.stage('at the foot', r'climb: at the foot of edge \d+', 'klclimb saw him stand at the wall, looking at it', after=k)
                self.stage('the climb', r'climb: edge \d+: started', 'klclimb started the climb', after=k)
            elif kind == 'die':
                self.add('log --die: he stands here until he is dead (the first hit: CopToYou %s, health 27)' % ('1' if R.fed and not o['fed_die'] else '20'))
                if R.fed and not o['rig3']:             # review 3, S1: what a death ON THE WAY costs on a rig that cannot see it
                    left = [g['to'] for g in self.gotos if not g['fed'] and g['round'] == self.round]
                    self.want('WHEN HE DIES ON THE WAY (2 live deaths of 3 did): the hero\'s gotos that are left run out one by one, each to its timeout, and steer the FED at the '
                              'hero\'s way points - after a death in the second goto that is up to %d s (in the last one %.1f s), then the %d s of --die-wait: the fed\'s first goto '
                              'begins up to %d s after he appeared, from wherever he was pushed to, and "pos fed-appeared" is that place, not the point (the point is in "fed: YOU '
                              'ARE A FED ... at"). The hero\'s gotos of this script have short timeouts for that reason (1.5 x the model\'s time + 2.5 s). A rig with `onbody` skips '
                              'all of it: --rig3' % (sum(left[1:]) / 1000, left[-1] / 1000.0, o['die_wait'], sum(left[1:]) / 1000 + o['die_wait'] - 5), len(self.lines))
                if R.fed:                               # --fed-walk: the script cannot see his death: it stands --die-wait seconds, a `pos` every 5
                    for t in range(max(1, int(o['die_wait'] // 5))):
                        self.wait(5000)
                        self.add('pos die-%ds' % ((t + 1) * 5))
                else:
                    for t in range(int(o['linger'] // 15) or 1):
                        self.wait(15000)
                        self.add('pos die-%ds' % ((t + 1) * 15))
                self.want('fed: you: status 0 -> N (...)   [he is dead or down]   then   fed: YOU ARE A FED: local player object N (..., type 3, police byte 1) at (x, y, z); ...   [the respawn]',
                          len(self.lines))
                self.want('NOT: script: window \'HeistStatusLeaderboard\' is up ... within seconds of his death   [= the round ended with him: the fed did not arm]', len(self.lines))
                self.stage('his death', r'fed: you: status 0 -> 1', 'he was shot dead (on the way or at the place)', after=self.go_line)
                self.stage('the fed', r'fed: YOU ARE A FED', 'he came back as police', after=self.go_line)
                if o['rig2']:
                    self.want('players: the local one is #k at ... (the game\'s own pointer, slot N)   again after his death, and pos die-NNs: me #k = the FED\'s body from then on '
                              '[seen live, PT_DM03_die_r2: slot 0 -> slot 8]. He may die ON THE WAY (that run: 9 s after he could move): the gotos left then steer the fed at the old '
                              'way points, through walls - "goto is stuck" / "NOT reached" lines AFTER "fed: you: status 0 -> 1" mean nothing', len(self.lines))
                else:
                    self.want('pos die-NNs: me #k ...   [the unpatched klauto still means the DEAD body - the one that moved first; where the fed stands is in the fed: lines only]',
                              len(self.lines))
            # a stop is a stop only when a wait follows it (a goto right after a goto without keep finds him as fast as before)
            if stop and nxt is not None and not any(s.startswith('wait ') for s in self.lines[mark:]):
                self.wait(STOP_MS)
            if n == hold_at:                            # --join-after: he stands in the tower until the crew has started by itself
                rest = sum((x[3]['rig']['t'] if x[3].get('rig') and x[3]['rig']['clean'] else x[3]['leg']['len'] / WALK) + (STOP_MS / 1000.0 if x[3].get('stop') else 0.0)
                           for x in flat[n + 1:] if x[0] == 0)
                ms = int(max(0.0, o['join_after'] - (self.secs - self.go_secs) - rest) // 0.5) * 500
                if ms > 0:
                    self.add('log --join-after %d: he stands %d ms, then %d s of way to the join' % (o['join_after'], ms, rest))
                    while ms > 0:
                        self.wait(min(ms, 15000))
                        ms -= 15000
                    self.add('pos stood-in-the-tower')
        if R.fed:
            if not self.in_fed:                         # no part on the mesh (nothing joins): the gotos over the collision and the blind ones all the same
                self.fed_start()
            self.fed_end()
        elif R.until in ('enter', 'loot', 'exit', 'join') and not R.die:
            self.linger(o['linger'])
        elif not R.die:
            self.want('escort: record N re-pointed: you are X m away at (x, y, z); ...   [from here on all through the walk, at most every 5 s: the place "at (x, y, z)" must MOVE with him]',
                      flat[0][3].get('line', 1) + 1)

    # ---- the fed
    def fed_start(self):
        """The fed's part begins: klfed's switch, where he stands, then the gotos that are not way points of the mesh
        (the collision's way to it; the blind ones where nothing joins)."""
        F, o = self.R.fed, self.o
        self.in_fed = True
        G = [q for q in F['points'] if q['n'] in F['group']]
        if o['rig3']:                                   # the rig with `onbody` (re\playtest.md 10.6): the trap armed after 0x19 brings the script here
            self.add('label fed%d' % self.round)        # the tick the game's local player is another object; without a death it comes here by the wait
        self.fed_line = self.add('log FED: from here the gotos steer the game\'s local body: police, if he died')
        k = self.add('peek 0x168ea60 fed-switch-1-armed-0-he-is-police-or-never-armed')
        self.want('script %d: peek 0168ea60 = 00000000 ...   [klfed\'s switch: 1 while it is armed (the human alive, or dead and waiting), 0 once he stands as police. 00000001 here = '
                  'he is NOT police yet (still alive: nobody shot him in the %d s of --die-wait): the gotos after it steer the hero and the run shows nothing of the fed]' % (k, o['die_wait']), k)
        k = self.add('pos fed-appeared')
        floors = '; '.join('%d (%d, %s, %d)' % (q['n'], q['at'][0], '%d' % q['floor'] if q['floor'] is not None else '%d' % q['mesh'][1] if q['mesh'] else '?', q['at'][2]) for q in G)
        self.want('pos fed-appeared: me #k (x, y, z) ...   [the FED\'s body: "fed: YOU ARE A FED: ... at (x, y, z)" has the very place he was put on - one of the points of group %s, at '
                  'the floor\'s height: %s. He may have been moved since by the hero\'s gotos that were left when he died (they steer the new body too). A y far under the floor = he '
                  'fell through; a place of another group = the gotos below are for the wrong group]' % (F['group'], floors), k)
        self.stage('the fed is seen', r'pos fed-appeared: me #', 'the script\'s own `pos` when the fed\'s part begins', after=k)
        if len(F['groups']) > 1:                        # review 3, S3: the game picks the point, the script cannot
            np_, ng = len(F['points']), len(G)
            self.want('THE GAME PICKS THE POINT: this script\'s gotos fit %d of the map\'s %d AFTER_DEATH points (group %s; the groups are %s). If the pick is uniform over the free '
                      'points - how kl2 picks is NOT read - a run fits with a chance of %d in %d: plan on about %d runs for this group. In a run that got another group the gotos '
                      'below aim at the wrong place and ONLY "fed: YOU ARE A FED ... at" and pos fed-appeared are of use (judge says which group it was). One script for all '
                      'groups needs `ifnear` / `jump` in the rig (re\\playtest.md 10.6)' % (ng, np_, F['group'], F['groups'], ng, np_, math.ceil(np_ / ng)), k)
        for j, q in enumerate(F['pre']):
            prev = F['pre'][j - 1] if j else max(G, key=lambda g: d2(g['at'], q))['at']
            ms = int(min(20000, max(6000, math.ceil((3.0 * d2(prev, q) / WALK + 4.0) * 2) * 500)))
            g = self.raw_goto(q, 60, ms, 'fedpre', 'the collision\'s way, point %d of %d' % (j + 1, len(F['pre'])))
            k = self.add('pos fed-way-%d' % (j + 1))
            self.want('script %d: goto (%d, %d) reached ...   then   pos fed-way-%d: me #k (x, %d +-40, z)   [the fed on the collision\'s way, OFF the mesh: point %d of %d%s]'
                      % (g, q[0], q[2], j + 1, q[1], j + 1, len(F['pre']), '' if F['join'] else '; its end is the edge of what the collision leaves open'), k)
        for j in range(FED_BLIND if F['blind'] else 0):
            q = F['blind'][min(j, len(F['blind']) - 1)]
            g = self.raw_goto(q, 100, FED_BLIND_MS, 'fedblind', 'blind')
            self.by_design.append(g)
            k = self.add('pos fed-blind-%d' % (j + 1))
            if F['edge'][1] - q[1] < 2 * BLIND_DY:      # the crew's mesh is on his own floor (Retomoto's lift cars): the height says nothing, the plan does
                self.want('script %d: goto (%d, %d) ...   then   pos fed-blind-%d: me #k (x, y, z)   [BLIND, try %d of %d: straight at the crew\'s mesh at y %d, on the floor he '
                          'stands on (the edge of what the collision leaves open is at y %d), %d away in the plan. "reached" = he is out of what the collision shuts him in (a '
                          'door that opens); "NOT reached": the pos line says where he stuck. Neither voids the run]'
                          % (g, q[0], q[2], j + 1, j + 1, FED_BLIND, q[1], F['edge'][1], math.hypot(q[0] - F['edge'][0], q[2] - F['edge'][2])), k)
                continue
            self.want('script %d: goto (%d, %d) ...   then   pos fed-blind-%d: me #k (x, y, z)   [BLIND, try %d of %d: straight at the crew\'s mesh at y %d, %d under the edge of what '
                      'the collision leaves open (y %d). READ THE y, NOT THE GOTO\'S LINE: the goto\'s "reached" is a distance in the plan (x, z only) and this place lies %d in the '
                      'plan from the edge he starts at%s - a fed who is still up there can "reach" it. There IS a way down only when y is within %d of %d (stairs the walk test did '
                      'not take, a door that opens); a y that falls from one pos line to the next = he came part of the way; the same y as fed-way-%d = no way shown, whatever the '
                      'goto says. Neither voids the run]'
                      % (g, q[0], q[2], j + 1, j + 1, FED_BLIND, q[1], F['edge'][1] - q[1], F['edge'][1], math.hypot(q[0] - F['edge'][0], q[2] - F['edge'][2]),
                         ' and %d from the nearest point he can appear on' % min(math.hypot(q[0] - g_['at'][0], q[2] - g_['at'][2]) for g_ in G),
                         BLIND_DY, q[1], len(F['pre'])), k)

    def fed_end(self):
        F, o = self.R.fed, self.o
        n = self.add('log FED: his walk is done; he stands %d s (%s)' % (o['linger'], 'the crew shoots him: F3' if o['fed_die'] else 'pos every 15 s'))
        for t in range(int(o['linger'] // 15) or 1):
            self.wait(15000)
            self.add('pos fed-end-%ds' % ((t + 1) * 15))
        if F['goal']:
            self.want('pos fed-end-15s: me #k (%d, %d, %d) +-60   [he stands at the crew\'s \'%s\' place: every goto of the fed\'s part was reached. Any other place: the last "reached" '
                      'line and the "goto is stuck at" lines of the fed\'s part say where the way ended%s]'
                      % (*F['goal'][1][:3], F['goal'][0], '; the walk test over the collision does not reach beyond way point %d of his part' % (F['coll_end'] + 1)
                         if F.get('coll_end') is not None else ''), n)
        else:
            self.want('pos fed-end-15s: me #k ...   [how far the fed got: neither the mesh nor the collision joins the place he appears at to the crew\'s part]', n)
        self.stage('the fed walks', r'pos fed-end-15s: me #', 'the fed\'s part of the script ran to its end', need=False, after=n)
        if o['fed_die']:
            self.want('F3 (re\\fed.md): the fed is shot by the crew he walked into: "balance: you lost ..." lines of a policeman with 27 of health, then the round ends about 3 s after '
                      'his second death ("session: state 0x19 -> 0x1f") and NOT a line "fed: you: status 7 -> 1" (a second death is final)', len(self.lines))
            self.stage('the fed\'s death ends the round', r'session: state 0x19 -> 0x1f', 'F3: a second death is final', need=False, after=n)

    def linger(self, secs):
        n = self.add('log ROUTE DONE (--until %s); he stands %d s' % (self.R.until, secs))
        self.want('script %d: ROUTE DONE ...   [it comes whatever happened: the route WAS walked only when every goto before it was "reached"%s]'
                  % (n, ' - script line(s) %s apart, which end by their timeout by design' % ', '.join(str(k) for k in self.by_design) if self.by_design else ''), n)
        for t in range(int(secs // 15)):
            self.wait(15000)
            self.add('pos end-%ds' % ((t + 1) * 15))
        self.want('escort: record N re-pointed: you are X m away at (x, y, z); ...   [all through the walk, at most every 5 s: the place "at (x, y, z)" must MOVE with him]', n)

    # ---- the vehicle
    def at_vehicle(self, w):
        """He stands beside the vehicle's stop: --until van watches it come and go."""
        k = self.add('pos at-the-vehicle')
        self.want('pos at-the-vehicle: me #k (%d, y, %d) ...   [%s]' % (w['p'][0], w['p'][2], w['what'][:80]), k)
        if self.R.until == 'van':
            self.watch_van(w, 'CLEAR OF THE VAN: in play, not aboard, in the exit box; %d s' % self.o['linger'] if 'CLEAR' in w['what'] else
                           'AT THE VAN: he waits beside its rear doors and does not board')
            if 'CLEAR' in w['what']:
                self.want('bots: record N (bot): aboard   ...   and   bots: record 0 (you): in-play all the time, NOT aboard   [--clear: the human is in play and not aboard while the AI '
                          'heisters board - for the Bribe / Leave / FollowOut tests; what the rules do to the one left behind is theirs to show]', len(self.lines))

    def watch_van(self, w, text):
        n = self.add('log ' + text)
        for t in range(int(self.o['linger'] // 10) or 1):
            self.wait(10000)
            self.add('pos van-%ds' % ((t + 1) * 10))
        self.want('bots: L1 s19 van 1 7.xs | 0 you in-play g3 ...   then   van 3 (it waits, 8 s)   van 5 (it leaves)   van 7   and again 1: one visit every 29.5 s while he stands in the exit box%s'
                  % ('' if w.get('in_exit') else ' - BUT this place is in no exit box'), n)
        self.want('escort: record N released (the vehicle waits, state 3): sent to the boarding place (x, y, z)   [the escort bot; needs [Bots] Escort=1]', len(self.lines))
        self.stage('the escort is let go', r'escort: record \d+ released \(the vehicle waits', 'the escort bot was sent to the boarding place', need=False, after=n)

    def no_board(self, w):
        """The unpatched rig at a key-framed van: it cannot see the van, and a step to the rear doors by the clock puts
        him where the van drives when the clock is off by 1.4 s (the review, 4.3). He stays beside the doors."""
        self.o['linger'] = max(self.o['linger'], 70.0)
        self.want('NOT: bots: record 0 (you): aboard   [this script does NOT board: it is written for the unpatched klauto, which cannot see the van. Boarding: the --rig2 script]', len(self.lines))
        self.watch_van(w, 'NOT BOARDING: this rig cannot see the van (run the rig2 script)')

    def board_van(self, b, w):
        """The boarding box rides on the van and the van's nose kills (KillBox): he steps to the rear doors only while it
        stands. rig2: `waitvan 3` with a timeout longer than the round - the step is taken only when the van is SEEN to
        wait; when none comes the round's end (the score page, `onwin`) ends the script. --blind-board on the unpatched
        rig: the steps are TIMED from the moment he entered the exit box, which is right only when HE called the van
        (state 0 before) and his walk from there took what the model says, within -1.4 / +2.5 s."""
        o, d = self.o, self.R.van
        tb = d2(w['p'], b['p']) / WALK + 0.4
        gb = 'goto %d %d %d 3000' % (round(b['p'][0]), round(b['p'][2]), round(b['r']))
        gw = 'goto %d %d 50 3000' % (round(w['p'][0]), round(w['p'][2]))
        first = len(self.lines)
        never = int((ROUND_S + 60) * 1000)              # longer than the round can last from here
        for visit in range(1, o['visits'] + 1):
            if o['rig2']:
                if visit > 1:                           # the visit he just stood at may still wait: first see the NEXT one drive in
                    self.add('waitvan 1 %d' % never, 12.0)
                n = self.add('waitvan 3 %d' % never, 15.0 if visit == 1 else 7.5)
                self.add('log van visit %d: it WAITS (waitvan 3): he steps to its rear doors' % visit)
                self.t_call = 0.0
            else:
                stands = (visit - 1) * (VAN_IN + VAN_STANDS + VAN_OUT + VAN_GAP) + VAN_IN       # seconds after the call
                if self.t_call is None:
                    self.t_call = 0.0
                if self.t_call > stands + VAN_STANDS - (tb + E_HOLD / 1000.0 + 1.0):
                    self.add('log van visit %d: he is too late for it (%.0f s after the call)' % (visit, self.t_call))
                    continue
                ms = int(max(0.0, stands + 1.4 - self.t_call) * 1000)
                n = self.add('log van visit %d: step in %d ms (TIMED from the exit box: blind)' % (visit, ms))
                self.wait(ms)
                self.t_call += ms / 1000.0
            self.add(gb, tb)
            k = self.add('pos at-the-rear-doors-%d' % visit)
            self.hold_e(E_HOLD)
            self.wait(200)
            self.add('tap E')
            self.wait(400)
            self.hold_e(2000)
            self.add(gw, tb)
            self.add('pos back-beside-%d' % visit)
            if self.t_call is not None:
                self.t_call += 2 * tb + (E_HOLD + 200 + 400 + 2000) / 1000.0
        if o['rig2']:
            self.want('script N: the vehicle\'s state is 3 (its timer x.x s) after T ms   then   script N+1: van visit 1: it WAITS ...   [waitvan saw the van stand: only then does he step '
                      'to the doors. No such line = no van came while he stood there: the script sits in waitvan until the score page ends it, and he was never in the van\'s way]', first + 1)
            self.stage('the van waits for him', r'script \d+: the vehicle\'s state is [34] ', 'waitvan 3 saw the van stand while he stood beside its doors', after=first + 1)
        else:
            self.want('bots: L1 s19 van 3 x.xs | ...   [--blind-board: the van must WAIT (state 3) when "script N: goto (%d, %d) reached" is logged - if it shows van 1 he stepped into its '
                      'way (the timing is blind: it holds only when nobody called the van before him and his walk took what the model says, -1.4 / +2.5 s)]' % (b['p'][0], b['p'][2]), first + 1)
        self.want('bots: record 0 (you): aboard   [status 4: "You jumped into the getaway car"]   then   bots: record 0 (you): status6   [escaped]', len(self.lines))
        self.stage('aboard', r'bots: record 0 \(you\): aboard', 'E at the rear doors took him aboard', after=first + 1)
        self.stage('escaped', r'bots: record 0 \(you\): status6', 'the van left with him', need=False, after=first + 1)
        self.after_board()

    def board_fixed(self, w):
        k = self.add('pos in-the-boarding-box')
        n = self.add('log IN THE BOARDING BOX (it stands still): E every 3.3 s for %d s' % (self.o['visits'] * 27))
        for t in range(int(self.o['visits'] * 27 / 3.3)):
            self.add('tap E')
            self.wait(500)
            self.hold_e(2000)
            self.wait(700)
            if t % 4 == 3:
                self.add('pos boarding-%d' % (t + 1))
        self.want('bots: record 0 (you): aboard   [status 4: "You jumped into the getaway car"; the vehicle must wait then: "van 3"]   then   bots: record 0 (you): status6', len(self.lines))
        self.stage('aboard', r'bots: record 0 \(you\): aboard', 'E in the boarding box took him aboard', after=k)
        self.stage('escaped', r'bots: record 0 \(you\): status6', 'the vehicle left with him', need=False, after=k)
        self.after_board()

    def after_board(self):
        n = self.add('log BOARDING DONE: waiting for the score page (onwin) up to 120 s')
        for t in range(8):
            self.wait(15000)
            self.add('pos after-%ds' % ((t + 1) * 15))
        self.want('script: window \'HeistStatusLeaderboard\' is up at line N: going on at label \'score\'   [the round ended: with him aboard = "All surviving criminals escaped"]', n)

    def tail(self):
        self.add('windows')
        self.add('pass 1000')
        self.add('label score2' if self.o['rounds'] > 1 else 'label score')
        n = self.add('log SCORE PAGE: the round is over')
        self.wait(8000)
        self.add('windows')
        self.add('pass 1000')
        self.want('RESULT PASS (script reached pass) exit code 0, asserts 0, faults 0, ...   [and in kl_autotest\'s output: RESULT: clean exit. THIS LINE SAYS ONLY that the game did not '
                  'fault and the script ran to its end: it comes just the same when every goto timed out. What the run showed: python tools\\kl_playtest.py judge <this ini> <its log>]',
                  len(self.lines))

    def next_round(self):
        """--rounds 2 (F4). The first round's walk is done: wait for the score page, tap RETURN, and the same level's
        next round begins about 2 s later without a load - session states 0x20 -> 0x23 -> 0x24 (FAWaitForPlayers) ->
        0x25 -> 0x26 -> 0x16 -> 0x18 -> 0x19 (live: run SH1, 2026-10-09, three rounds by `tap RETURN` 8 s after the page
        came). `onwin` is armed once: it is armed again for the next round's page. When his last life is lost the page
        is 'HeistStatusLeaderboard_EndGame' - another window: no trap, the run ends by its own clock (MaxRunMs)."""
        n = self.add('log ROUND 1: the walk is done; waiting for the score page (the clock ends it)')
        self.add('wait %d' % int((ROUND_S + 60) * 1000), 60.0)          # (the page's trap ends this wait: a minute is the guess for the estimate)
        self.add('log ROUND 1: no score page came: the script ends')
        self.add('pass 1000')
        self.add('label score')
        self.add('log SCORE PAGE of round 1: RETURN in 8 s, then round 2 on the same level')
        self.wait(8000)
        self.add('windows')
        k = self.add('tap RETURN')
        self.want('script: window \'HeistStatusLeaderboard\' is up ...: going on at label \'score\'   then   script %d: tap key 0x1c   then   session: state 0x20 -> 0x23 ... -> 0x16 -> '
                  '0x18 -> 0x19   [the next round of the same session, about 2 s after RETURN, no load (run SH1). "windows: 1 [HeistStatusLeaderboard_EndGame]" instead = his last life was '
                  'lost: no second round]' % k, k)
        # review 3, S4: `onwin` fires the poll it finds its window on top. Armed in the poll after the tap (80 ms and 2 frames after the key went
        # down) it would fire on ROUND 1's page if that were still up, and the script would end 'PASS' there. In SH1 the page was gone 2 ms after
        # the key, but nobody has seen this page after a FED round: PAGE_GONE_MS first (SH1 itself had 9 s here; round 2's 0x19 comes about 2 s
        # after RETURN and the waitstate behind this takes a state that already holds)
        self.wait(PAGE_GONE_MS)
        k = self.add('windows')
        self.want('windows: 0 []  (or the next round\'s windows) - NOT windows: 1 [HeistStatusLeaderboard]   [script %d, %.0f s after RETURN: round 1\'s page must be gone before the '
                  'trap for round 2\'s page is armed in the next line; if it is still up the trap fires at once and the script ends on round 1\'s page. READ THIS RUN BY "session: state '
                  '0x18 -> 0x19" APPEARING TWICE, not by RESULT PASS (judge counts them)]' % (k, PAGE_GONE_MS / 1000), k)
        self.add('onwin HeistStatusLeaderboard score2')
        self.round = 2
        self.secs += 10.0

    def build(self, entry):
        self.menu(entry)
        self.go()
        self.walk()
        if self.o['rounds'] > 1:
            self.next_round()
            self.go()
            self.walk()
            self.want('fed: round N: ... / fed: police bodies: ...   [F4 (re\\fed.md): in round 2 the body round 1 took shows "used 1"; his second return takes the next one and '
                      '"N of 8 police bodies still free" counts down]', len(self.lines))
        self.tail()
        if len(self.lines) > SCRIPT_MAX:
            raise SystemExit('the script has %d lines; klauto reads %d (kla_cmd[640])' % (len(self.lines), SCRIPT_MAX))
        return self


def write_script(tree_folder, mid, out, opt):
    tree, man = find_tree(tree_folder)
    entry = next((e for e in man['maps'] if e['id'].lower() == mid.lower()), None)
    if entry is None:
        raise SystemExit('%s: the tree has the maps %s' % (mid, ' '.join(e['id'] for e in man['maps'])))
    build = opt.get('build')
    if build:
        L = Level(build)
    else:                                               # the tree's own copy of the map: the archive it will load, the plan it was adopted with
        L = Level(os.path.join(tree, 'Maps', entry['id']), os.path.join(tree, 'BuildInfo', entry['id']))
    R = make_route(L, opt)
    S = Script(R, opt).build(entry)
    name = os.path.splitext(os.path.basename(out))[0]
    total = int(S.secs * 1.25 + 60)                     # a quarter for turns, stuck steps and slow legs
    # no script outlasts the round: its clock ends it and the score page (onwin) ends the script. The run's own limits are
    # set past that, so that a run ends by `pass` and not by the clock even when every goto and waitvan runs out
    worst = 62.0 + LOAD_GO[1] + ROUND_S + 120.0         # the menu and the load, the wait for the round, the round, the score page and a slow load
    if opt['rounds'] > 1:
        worst += ROUND_S + 40.0
    budget = max(total * 1.3, worst)
    block = open(os.path.join(tree, 'KLHook.expansion.ini')).read().replace('Log=1', 'Log=2', 1).rstrip('\n')
    needs = ''
    if build:
        needs += '\n;   WITH Maps\\%s REPLACED by the build %s (the tree has another build of this map)' % (entry['id'], build)
    if opt['until'] == 'wall':
        needs += '\n;   and a hook that has klclimb.c WIRED (klhook.c: three lines, klclimb.c\'s end of comment) - without it he only stands at the wall'
    if opt['rig2']:
        needs += '\n;   and klauto.c WITH THE PATCH of re\\playtest.md 6 (waitstate, waitvan; the TEST hook <work>\\build\\klhook\\test_pt1 has it): an unpatched\n' \
                 ';   hook answers "unknown command" and loads NO script'
    if opt['rig3']:
        needs += '\n;   and klauto.c WITH THE THIRD ROUND\'S PATCH (`onbody`: <work>\\research\\playtest\\v3\\klauto_h3_onbody.patch, re\\playtest.md 10.6) - NOT in the\n' \
                 ';   tree and in no built hook when this file was written: a hook without it loads NO script'
    elif opt['until'] == 'board' and R.boarding == 'van' and not opt['blind_board']:
        needs += '\n;   WRITTEN FOR THE UNPATCHED klauto: it does NOT board (that rig cannot see the van; a step to its doors by the clock is blind).\n' \
                 ';   For boarding run the rig2 script of the same name (rig2\\%s_r2.ini)' % name
    elif opt['blind_board']:
        needs += '\n;   --blind-board: the steps to the van\'s doors are TIMED (-1.4 / +2.5 s of tolerance): he may stand where the van drives'
    args = 'script <tree> %s <out> ' % entry['id'] + ' '.join(a if ' ' not in a else '"%s"' % a for a in opt.get('argv', []) if a.startswith('--') or not os.path.isabs(a) and os.sep not in a and '/' not in a
                                                           and a not in (tree_folder, mid, out, 'script'))
    text = HEAD % dict(tag=name, args=args, name=name, tree=tree, needs=needs, wait=int(budget) + 400, shots='%d-%d:20' % (90, min(total, 600)),
                       what='Arcade -> Dead Men maps -> entry %d "%s" (slot %s, Maps\\%s), then the human WALKS: --until %s%s, bot %d\'s places, %d way points, %.0f m'
                            % (entry['menu_entry'], entry['name'], entry['slot'], entry['id'], opt['until'], (' --die' if opt['die'] else '') +
                               (' --fed-walk (the AFTER_DEATH points of group %s%s)' % (R.fed['group'], ', F3: the fed dies' if opt['fed_die'] else '') if R.fed else '') +
                               (' --clear' if opt['clear'] else '') + (' --rounds 2' if opt['rounds'] > 1 else ''), opt['bot'],
                               sum(1 for _ in R.points()), R.length() / 100),
                       block=block, autoexit=int(budget) + 300, maxrun=(int(budget) + 200) * 1000)
    sets = list(FRAGILE if opt['die'] else [] if opt['no_survive'] else survive(opt['cop']))
    if opt['die'] and opt['fed_walk']:                  # the fed's keys: FED_WALK / FED_DIE above have the reasons (review 3, M1)
        if opt['fed_die']:
            sets += FED_DIE
        else:
            sets = [s for s in sets if not (s[0] == 'Balance' and s[1] in FED_WALK_DROP)] + FED_WALK
    if opt['until'] == 'wall':
        sets += [('Climb', 'Enable', '1'), ('Climb', 'Key', '0'), ('Climb', 'Log', '2')]
    for sec, k, v in sets + parse_extra(opt.get('extra')):
        text = ini_set(text, sec, k, v)
    text += '[Script]\n' + ''.join('%d=%s\n' % (i + 1, s) for i, s in enumerate(S.lines))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', newline='\r\n') as f:
        f.write(text)
    base = os.path.splitext(out)[0]
    with open(base + '.route.txt', 'w', newline='\r\n') as f:
        f.write('\n'.join(R.text()) + '\n')
    ex = ['%s: what KLHook.log must show, in this order (kl_autotest keeps the run\'s part as <work>\\build\\klhook\\live\\%s.log).' % (os.path.basename(out), name),
          'A line is quoted as the hook writes it; [..] is the reason. "script N" = line N of the ini\'s [Script]. THIS SCRIPT HAD NOT RUN when it was written.',
          'Times are seconds after the session state became 0x19 (the round\'s clock starts; the human can move 10.1 .. %.1f s LATER).' % FREE_S,
          'The same, read by a program:   python tools\\kl_playtest.py judge %s <the run\'s KLHook log>' % os.path.basename(out), '']
    when = lambda at: '0x19 %+4d s' % round(S.clock[min(at, len(S.clock)) - 1] - S.go_secs) if at >= S.go_line else 'the menu   '
    ex += ['%3d. after script %-3d (about %s)  %s' % (i + 1, at, when(at), t) for i, (at, t) in enumerate(sorted(S.expect, key=lambda e: e[0]))]
    ex += ['', 'What says the run proves NOTHING: "game window in front at the last one: no" in the nudge: lines (the window was not in front: the round stood still);',
           '"RESULT FAIL"; a "NOT reached" on a leg before the stage that is looked at' + (' - EXCEPT script line(s) %s, which end by their timeout by design (a push at a money '
           'object the mesh does not reach)' % ', '.join(str(n) for n in S.by_design) if S.by_design else '') + ';',
           ('a first goto that is "stuck" for seconds and "NOT reached" (he could not move yet: the wait after 0x19 was too short).' if opt['rig2'] else
            '"no moving player found" (a goto ran before he could move: the unpatched rig skips it after 6 s).'),
           '"RESULT PASS" alone proves nothing either: it comes whenever the game did not fault and the script reached its end.',
           'After "bots: record 0 (you): aboard" the gotos that are left steer nobody: their "NOT reached" lines mean nothing.',
           'Length of the run: about %d s when every wait of the script runs out; the round\'s own clock ends a run about %d s after its start at the latest (the score page '
           'comes and the script goes to its end); script lines: %d of %d.' % (total, worst, len(S.lines), SCRIPT_MAX)]
    fed_keys = ''
    if opt['die'] and opt['fed_walk'] and opt['fed_die']:
        fed_keys = ('[Balance] Ramp=0 CopToYou=20 PlayerHealth=0.05 and [Fed] Enable=1 Player=1: the first hit kills him; and for the fed [Balance] FedMirror=1 (the pairs are written '
                    'exchanged: every key keeps the meaning of its name on both sides; live in FD3_DM03_die), so he has the hero\'s 27 of health and a heister\'s bullet costs him x 1.0 '
                    '(CrewToYou): the first is his second death. CopToCrew=0.005: a police bullet costs a heister x 0.005 before and after the switch. A COLLEAGUE\'s stray bullet is '
                    'CopToYou = x 20 on him too and kills him as well: the log\'s "balance: you lost" line cannot tell the two apart (a loss is at most his 27) - where the crew '
                    'stood then is in the bots: lines. [Fed] EndSeconds=0 (klfed does not end the round when nobody is left to hunt)')
    elif opt['die'] and opt['fed_walk']:
        fed_keys = ('[Balance] Ramp=0 PlayerHealth=0.05, NO CopToYou key (Risk=2\'s 1.0) and [Fed] Enable=1 Player=1: he has 27 of health and one police bullet kills him (75.6 from a '
                    'Type 79 near, 39 at 50 m; a shotgun\'s far hit may take two). For the fed [Balance] FedMirror=0: the game\'s own 550 of health for a police player (live in '
                    'PT_DM03_die_r2) and NOTHING exchanged - once he is police his game reads the OTHER float of each pair (klbalance.c 2 a3), so the keys change their meaning at '
                    'his death:  CopToYou (1.0) is then a HEISTER\'s bullet on him - x 1.0 of 550, he can be shot dead by the crew he walks to, about 12 hits;  CrewToYou=0.001 a '
                    'police AI\'s stray on him;  CrewToCop=0.005 a police AI\'s bullet on a heister, as CopToCrew=0.005 was before the switch: the crew is protected on both sides '
                    'of it, AND ITS OWN BULLETS COST THE POLICE x 0.005 ALL ROUND LONG (it cannot clear a room; whether it then lives for him to walk to is a guess). The balance '
                    'lines print two decimals: "police->crew 0.01" / "0.00" are these numbers. A READING of klbalance.c, NOT RUN. [Fed] EndSeconds=0 (klfed does not end the round '
                    'when nobody is left to hunt). The first round\'s scripts had CopToYou=20 here: a heister\'s bullet on the fed x 20 (review 3, M1) - do not run those')
    ex += ['', 'In the ini: ' + (fed_keys if fed_keys else '[Balance] Ramp=0 CopToYou=20 PlayerHealth=0.05 and [Fed] Enable=1 Player=1: the first hit kills him' if opt['die'] else
                              'the owner\'s balance, nothing more (--no-survive): he does not shoot and will be shot' if opt['no_survive'] else
                              '[Balance] Ramp=0 CopToYou=%.4g CrewToYou=%.4g PlayerHealth=10 RegenDelay=0.5 RegenTime=0.5 Log=2: as hard to kill as the keys make him, because he '
                              'never shoots (a test aid: what the police do to HIM is not measured by this run). At 0.02 he was dead on the bank\'s stairs in 3 live runs of 5 with the '
                              '5,500 of health: the point-blank rule (a firing guard within %d sends a hit worth 100 bullets a step: 758.6 from the .45 at 0.02, %.1f at this dial). '
                              '"bots: record 0 (you): dead" = the run ends there; the "balance: you lost" lines before it say by what'
                              % (opt['cop'], opt['cop'], PB_REACH, 37931.25 * opt['cop']))]
    r1, r2 = R.danger_rows()
    ex += ['', 'THE POINT-BLANK RULE on this route (the .route.txt has each): %d stop(s) or walked leg(s) within %d of a guard\'s post; %d of its %d stops are where a guard can have come '
           'to by then (a model: %d units a second along the mesh from his post, measured on the bank only)%s' % (len(r1), PB_POST, len(r2), len(R.stops()), GUARD_RUN,
           '; %d way point(s) are walked in motion although the model asks for a stop (a live run did so)' % sum(1 for _a, _b, _c, w in R.points() if w.get('live'))
           if any(w.get('live') for _a, _b, _c, w in R.points()) else '')]
    rigs = R.not_reached() + R.steered_off() + R.behind() + [x for x in R.stand_arcs() if 'circles' in x[3]]
    if rigs:
        ex += ['', 'Gotos the route print marks for the rig (the .route.txt has the reason at each; those he would circle if he did not turn before he walks from a stand are among '
               'them): script line(s) ' + ', '.join(str(n) for n in sorted({w['line'] for _si, _i, w, _t in rigs if 'line' in w})) + ' - look at these first when a leg fails.']
    with open(base + '.expect.txt', 'w', newline='\r\n') as f:
        f.write('\n'.join(ex) + '\n')
    plan = dict(script=os.path.basename(out), map=entry['id'], until=opt['until'], die=bool(opt['die']), rig2=bool(opt['rig2']), bot=opt['bot'], go_line=S.go_line,
                free_s=FREE_S, by_design=S.by_design, gotos=S.gotos, stages=S.stages, lines=len(S.lines), seconds=total, rounds=opt['rounds'], cop=opt['cop'])
    if R.fed:
        F = R.fed
        plan['fed'] = dict(line=S.fed_line, group=F['group'], groups=F['groups'], goal=[F['goal'][0]] + [round(v) for v in F['goal'][1][:3]] if F['goal'] else None,
                           points=[dict(n=q['n'], at=[round(v) for v in q['at']], group=q['group'], floor=None if q['floor'] is None else round(q['floor']),
                                        mesh=None if not q['mesh'] else round(q['mesh'][1])) for q in F['points']],
                           pre=[[round(v) for v in q] for q in F['pre']], blind=[[round(v) for v in q] for q in F['blind']], joined=bool(F['entries'] or F['join']),
                           edge=[round(v) for v in F['edge']] if F.get('edge') else None)
    with open(base + '.plan.json', 'w') as f:
        json.dump(plan, f, indent=1)
    return R, S, total


# ------------------------------------------------------------------ the command line
def options(a):
    def take(name, default=None, flag=False):
        if name in a:
            i = a.index(name)
            if flag:
                del a[i]
                return True
            v = a[i + 1]
            del a[i:i + 2]
            return v
        return False if flag else default
    argv = list(a)
    o = {'until': take('--until', 'board'), 'bot': int(take('--bot', '2')), 'die': take('--die', flag=True), 'extra': take('--extra', ''), 'rig2': take('--rig2', flag=True),
         'no_survive': take('--no-survive', flag=True), 'no_loot': take('--no-loot', flag=True), 'loot': int(take('--loot', '2')), 'loot_hold': float(take('--loot-hold', str(LOOT_HOLD))),
         'loot_wait': float(take('--loot-wait', '5')), 'linger': float(take('--linger', '30')), 'walk': take('--walk', flag=True), 'build': take('--build'),
         'shoot': take('--shoot', flag=True), 'blind_board': take('--blind-board', flag=True), 'join_after': float(take('--join-after', '0')),
         'visits': int(take('--visits', '3')), 'out': take('--out'), 'argv': argv,
         'cop': float(take('--cop', str(COP_DIAL))), 'stops': take('--stops', flag=True), 'clear': take('--clear', flag=True), 'fed_walk': take('--fed-walk', flag=True),
         'fed_group': int(take('--fed-group', '1')), 'fed_to': take('--fed-to', 'loot'), 'fed_die': take('--fed-die', flag=True),
         'die_wait': float(take('--die-wait', str(DIE_WAIT))), 'rounds': int(take('--rounds', '1')), 'rig3': take('--rig3', flag=True)}
    o['rig2'] = o['rig2'] or o['rig3']
    take('--no-shoot', flag=True)                       # (the default now; the old spelling is taken and means nothing)
    if o['die'] and '--linger' not in argv:
        o['linger'] = 60.0 if o['fed_walk'] else 150.0
    if o['until'] == 'van' and '--linger' not in argv:
        o['linger'] = 90.0 if o['clear'] else 70.0
    if o['fed_to'] not in ('loot', 'exit', 'level', 'enter', 'van', 'hall', 'gate', 'rally'):
        raise SystemExit('--fed-to %s: one of loot exit level enter van' % o['fed_to'])
    if o['rounds'] not in (1, 2):
        raise SystemExit('--rounds %d: 1 or 2' % o['rounds'])
    return o


def make_route(L, o):
    """The Route of the options `o` on level L."""
    return Route(L, bot=o['bot'], until=o['until'], loot=0 if o['no_loot'] else o['loot'], die=o['die'], walk=o['walk'], shoot=o['shoot'], stops=o['stops'], clear=o['clear'],
                 fed={'group': o['fed_group'], 'to': o['fed_to']} if o['fed_walk'] else None)


# the third round's set (re\playtest.md 10.5): rig2 only, into <work>\research\playtest\v3
DIE_FED = ['--until', 'loot', '--die', '--fed-walk']
SET3 = [('H3_DM03_board', 'DM03', ['--until', 'board']),                # the bank with the stairs in motion and the dial at 0.001: the FollowOut tests ride on it
        ('H3_DM02_board', 'DM02', ['--until', 'board']),                # Late Night Opening, never walked: the glass doors, the escalators
        ('H3_DM03_van_clear', 'DM03', ['--until', 'van', '--clear']),   # in play and not aboard for 90 s while the bots board (Bribe / Leave)
        ('H3_DM01_die_fed', 'DM01', DIE_FED), ('H3_DM02_die_fed', 'DM02', DIE_FED), ('H3_DM03_die_fed', 'DM03', DIE_FED), ('H3_DM06_die_fed', 'DM06', DIE_FED),
        ('H3_DM09_die_fed_g1', 'DM09', DIE_FED + ['--fed-group', '1']), ('H3_DM09_die_fed_g2', 'DM09', DIE_FED + ['--fed-group', '2']),
        ('H3_DM09_die_fed_g3', 'DM09', DIE_FED + ['--fed-group', '3']),
        # F3: the fed walks to where the crew runs to the van and is shot. He stands until the round's clock ends the run (--linger 180: review 3,
        # S5 - the crew passes the level exit place only on its way out, stage 3 came 80 .. 95 s after 0x19 for a human who sprints and later
        # for bots; with 60 s nobody might have passed)
        ('H3_DM03_F3_fed_dies', 'DM03', DIE_FED + ['--fed-to', 'level', '--fed-die', '--linger', '180']),
        ('H3_DM03_F4_two_rounds', 'DM03', ['--until', 'loot', '--die', '--rounds', '2', '--linger', '45']),     # F4: a death in each of two rounds
        # the `onbody` form (review 3, S1) of the three maps where a fed pushed about by the hero's leftover gotos may no longer stand where his own
        # first goto starts (a control room with a catwalk, a deck with stairs, a car park): for a TEST hook with klauto_h3_onbody.patch - none has it
        ('H3_DM01_die_fed_rig3', 'DM01', DIE_FED + ['--rig3']), ('H3_DM02_die_fed_rig3', 'DM02', DIE_FED + ['--rig3']), ('H3_DM06_die_fed_rig3', 'DM06', DIE_FED + ['--rig3'])]
SET = [('PT_DM01_board', 'DM01', ['--until', 'board']), ('PT_DM02_board', 'DM02', ['--until', 'board']), ('PT_DM03_board', 'DM03', ['--until', 'board']),
       ('PT_DM06_board', 'DM06', ['--until', 'board']), ('PT_DM09_join', 'DM09', ['--until', 'join']), ('PT_DM09_board', 'DM09', ['--until', 'board']),
       ('PT_DM03_wall', 'DM03', ['--until', 'wall', '--build', os.path.join(WORK, 'build', 'z_climb', 'M03')]), ('PT_DM03_die', 'DM03', ['--until', 'loot', '--die']),
       # the second run of Late Night Opening, only when the first one sticks at a glass door: the same route with the fire button
       ('PT_DM02_shoot', 'DM02', ['--until', 'board', '--shoot'])]


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('route', 'script', 'set', 'set3', 'selftest', 'rigfit', 'judge', 'fed', 'danger', 'starts'):
        sys.exit(__doc__)
    cmd = a.pop(0)
    if cmd in ('rigfit', 'starts'):
        folder = a.pop(0) if os.path.isdir(a[0]) else os.path.join(WORK, 'build', 'klhook', 'live')
        return rigfit(folder, a) if cmd == 'rigfit' else starts(folder, a)
    if cmd == 'judge':
        if len(a) != 2:
            sys.exit(__doc__)
        return judge(a[0], a[1])
    o = options(a)
    if cmd == 'fed':
        L = Level(a[0])
        print('\n'.join(['kl_playtest fed %s (map %s)' % (a[0], L.map)] + fed_text(L, fed_facts(L, o['fed_group'], o['fed_to'], o['bot']))))
        return 0
    if cmd == 'danger':
        L = Level(a[0])
        R = make_route(L, o)
        print('kl_playtest danger %s (map %s; the places of AI heister %d, --until %s)' % (a[0], L.map, o['bot'], o['until']))
        for s in L.soldiers():
            step = 100.0 * 1.05 * s['g'] if s['g'] else None
            print('   %-52s %-22s at (%6d, %5d, %6d)  %-11s %-9s %s  a point-blank step on the human: %s'
                  % (s['name'][-52:], s['weapon'], *s['at'], s['attitude'], 'in world' if s['active'] else 'LATER', 'hunts' if s['hunts'] else '     ',
                     '%.1f x the dial = %.1f at %.3g, %.1f at 0.02' % (step, step * o['cop'], o['cop'], step * 0.02) if step else '?'))
        if getattr(L, 'gun_note', None):
            print('   NOTE ' + L.gun_note)
        print('\n'.join(R.danger_text()))
        return 0
    if cmd == 'route':
        R = make_route(Level(a[0]), o)
        text = '\n'.join(R.text())
        print(text)
        if o['out']:
            os.makedirs(os.path.dirname(os.path.abspath(o['out'])), exist_ok=True)
            open(o['out'], 'w', newline='\r\n').write(text + '\n')
        return 1 if R.bad_legs() or R.not_reached() else 0
    if cmd == 'script':
        if len(a) != 3:
            sys.exit(__doc__)
        R, S, total = write_script(a[0], a[1], a[2], o)
        print('%s: %d script lines, about %d s; %s; %d line(s) to look for in the log (%s)' % (a[2], len(S.lines), total, tally(R), len(S.expect), os.path.splitext(a[2])[0] + '.expect.txt'))
        for t in R.notes:
            print('  NOTE ' + t)
        return 0
    if cmd in ('set', 'set3'):
        if cmd == 'set3':
            o['rig2'] = True
        out = a[1] if len(a) > 1 else (OUT if cmd == 'set' else os.path.join(OUT, 'v3'))
        for name, mid, args in (SET if cmd == 'set' else SET3):
            name += '_r2' if o['rig2'] and cmd == 'set' else ''         # another tag: kl_autotest keeps a run's log under its tag
            oo = options(list(args) + (['--rig2'] if o['rig2'] else []))
            oo['argv'] = ['script', a[0], mid, os.path.join(out, name + '.ini')] + oo['argv']
            R, S, total = write_script(a[0], mid, os.path.join(out, name + '.ini'), oo)
            print('%-16s %3d script lines, about %3d s; %s' % (name, len(S.lines), total, tally(R)))
        return 0
    return selftest(a[0])


def tally(R):
    return '%d way points, %.0f m; legs off the mesh %d, risky legs %d, tight way points %d; the rig: not reached %d, steered lines off the mesh %d, behind after a stop %d, stops %d (%d made)' % (
        sum(1 for _ in R.points()), R.length() / 100, len(R.bad_legs()), len(R.risky_legs()), len(R.tight_points()), len(R.not_reached()), len(R.steered_off()), len(R.behind()),
        len(R.stops()), sum(1 for _si, _i, w in R.stops() if w.get('halt')))


def selftest(folder, n=300):
    """The geometry against itself on a build: n random pairs of places on the START row's mesh part - every leg the
    funnel gives must be walked by trace() without leaving the mesh (two independent pieces of code). Then the same
    on every other part of the mesh a route uses (Retomoto: the street, entered by the join)."""
    import random
    L = Level(folder)
    nav = L.nav
    parts = [(L.home, 'the START row\'s part')]
    if L.rt:
        j = L.rt['street']['join']
        e = snap(nav, (j['at'][0], j.get('floor', j['at'][1]), j['at'][2]), dy=200.0)
        if e and nav.part[e[3]] != L.home:
            parts.append((nav.part[e[3]], 'the part the join lands on (the street)'))
    total = 0
    for part, what in parts:
        random.seed(7)
        polys = [i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == part]
        def place():
            while True:
                i = random.choice(polys)
                vs = nav.pv[i]
                w = [random.random() for _ in vs]
                x, z = sum(v[0] * q for v, q in zip(vs, w)) / sum(w), sum(v[2] * q for v, q in zip(vs, w)) / sum(w)
                if nav.inside(i, x, z):
                    return (x, floor(nav, i, x, z), z, i)
        legs = bad = noway = 0
        for _k in range(n):
            a, b = place(), place()
            w = way(nav, a, b)
            if w is None:
                noway += 1
                continue
            prev = a
            for q in w:
                if q['kind'] != 'land':
                    t = trace(nav, prev, q['p'])
                    legs += 1
                    bad += not t['ok'] or abs(t['end'][1] - q['p'][1]) > 60.0
                prev = tuple(q['p']) + (q['poly'],)
        print('%s, %s (%d polygons): %d pairs of places (%d without a way: a one-way link), %d legs of the funnel walked by trace(): %d leave the mesh'
              % (folder, what, len(polys), n, noway, legs, bad))
        total += bad
    # the steering model against the exact test of the turning circle (two pieces of code again): 6,000 gotos in the open.
    # The exact test is the BEST turn he could make; the rig's law (a rate in proportion to the bearing error) is not the
    # best, so the model may circle what the exact test calls reachable - never the other way round.
    random.seed(11)
    n = inside = a = b = 0
    for _k in range(6000):
        v, d, off, r = random.choice((WALK, SPRINT)), random.uniform(20.0, 600.0), random.uniform(-180.0, 180.0), random.uniform(15.0, 130.0)
        if d <= r:
            continue
        n += 1
        g = steer(0.0, 0.0, 0.0, v, d * math.sin(math.radians(off)), d * math.cos(math.radians(off)), r, v, limit=12.0)
        ok, ins = g['reached'] and g['turned'] <= ORBIT, cannot_turn_in(d, off, r, v)
        inside += ins > 0.0
        a += ok and ins > 6.0                           # reached although it lies well inside the circle he cannot leave: must not be
        b += not ok and ins == 0.0
    print('steer() against the exact test: %d gotos in the open (walk / sprint, 20 .. 600 away, any bearing, radius 15 .. 130): %d lie inside the turning circle by the exact test, '
          'and the model reaches %d of those that lie more than 6 inside (must be 0); the model circles %d more that the best possible turn would reach (the rig\'s law is not the best turn)'
          % (n, inside, a, b))
    total += a
    print('RESULT (selftest): %s' % ('PASS' if not total else 'FAIL'))
    return 1 if total else 0


# ------------------------------------------------------------------ the model against the game; a run against its script
POS_RE = re.compile(r'(\d\d):(\d\d):(\d\d)\.(\d+) pos [^:]*: me #\d+ \(([-\d]+), ([-\d]+), ([-\d]+)\) heading ([-\d]+)')
GOTO_RE = re.compile(r'(\d\d):(\d\d):(\d\d)\.(\d+) script (\d+): goto \(([-\d]+), ([-\d]+)\) (reached|NOT reached) in (\d+) ms: at \(([-\d]+), ([-\d]+), ([-\d]+)\) heading ([-\d]+)')


def clock(g):
    return int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + float('0.' + g[3])


def read_script(ini):
    """The [Script] of an ini -> {line number: [words]}."""
    cmds, on = {}, False
    for line in open(ini, errors='replace'):
        line = line.strip()
        if line.startswith('['):
            on = line.lower() == '[script]'
        m = re.match(r'(\d+)=(.*)', line)
        if on and m:
            cmds[int(m.group(1))] = m.group(2).split()
    return cmds


def read_walk(log):
    """A KLHook log -> ({script line: dict t, ms, ok, x, y, z, h} of the gotos, [(t, x, z, heading)] of the pos lines,
    {script line: times it was 'stuck'})."""
    gotos, pos, stuck = {}, [], collections.Counter()
    for line in open(log, errors='replace'):
        m = GOTO_RE.search(line)
        if m:
            g = m.groups()
            gotos[int(g[4])] = dict(t=clock(g), ms=int(g[8]), ok=g[7] == 'reached', x=float(g[9]), y=float(g[10]), z=float(g[11]), h=float(g[12]))
            continue
        m = POS_RE.search(line)
        if m:
            g = m.groups()
            pos.append((clock(g), float(g[4]), float(g[6]), float(g[7])))
            continue
        m = re.search(r'script (\d+): goto is stuck', line)
        if m:
            stuck[int(m.group(1))] += 1
    return gotos, pos, stuck


def rigfit(folder, runs):
    """steer() against the logs of scripted walks that ran in the game. (1) Every goto that was reached IN MOTION (the
    script line before it is a goto ... keep that was reached too) is replayed from the place and heading of that
    'reached' line: the model's time, place and heading at 'reached' against the log's, under three turn rates. (2) The
    gotos that started from a STAND (the goto before had no keep and 0.4 s or more passed): the place of 'reached' by
    'he turns first, then walks' and by 'an arc from where he looks'. (3) A goto right after a goto WITHOUT keep and
    with no wait between: how fast he was (is that a stop?)."""
    q = lambda s, f: sorted(s)[min(len(s) - 1, int(f * len(s)))]
    moving, stand, nowait = [], [], []
    for run in runs:
        ini, log = os.path.join(folder, run + '.ini'), os.path.join(folder, run + '.log')
        if not os.path.isfile(ini) or not os.path.isfile(log):
            print('%s: no %s.ini / .log in %s' % (run, run, folder))
            continue
        cmds, (gotos, pos, stuck) = read_script(ini), read_walk(log)
        order = sorted(n for n in gotos if gotos[n]['ok'])
        for k, n in enumerate(order):
            c = cmds.get(n)
            if not c or c[0] != 'goto' or k == 0 or stuck[n]:
                continue
            tx, tz = float(c[1]), float(c[2])
            r = float(c[3]) if len(c) > 3 and re.match(r'^[\d.]+$', c[3]) else 120.0
            v, b = SPRINT if 'sprint' in c else WALK, gotos[n]
            p = cmds.get(n - 1)
            if p and p[0] == 'goto' and 'keep' in p and (n - 1) in gotos and gotos[n - 1]['ok']:
                if b['ms'] >= 60:                       # (a goto that was reached at once has nothing to compare)
                    moving.append((run, n, gotos[n - 1], b, tx, tz, r, v, SPRINT if 'sprint' in p else WALK))
                continue
            pn = order[k - 1]
            p, a0 = cmds.get(pn), gotos[pn]
            if not p or 'keep' in p:
                continue
            start = b['t'] - b['ms'] / 1000.0
            if start - a0['t'] >= 0.4:
                at = [s for s in pos if a0['t'] + 0.3 <= s[0] <= start + 0.02]
                x, z, h = (at[-1][1], at[-1][2], at[-1][3]) if at else (a0['x'] + math.sin(math.radians(a0['h'])) * ROLL, a0['z'] + math.cos(math.radians(a0['h'])) * ROLL, a0['h'])
                stand.append((run, n, x, z, h, b, tx, tz, r, v, bool(at)))
            else:
                nowait.append((run, n, a0, b, tx, tz, r, v))
    print('kl_playtest rigfit: %s; runs %s' % (folder, ' '.join(runs)))
    print('(1) %d gotos reached IN MOTION (radius %s; %d of them with the target 45 degrees or more off his heading when the goto starts)'
          % (len(moving), '%d .. %d' % (min(m[6] for m in moving), max(m[6] for m in moving)) if moving else '-',
             sum(1 for m in moving if abs(wrap(bearing(m[2]['x'], m[2]['z'], m[4], m[5]) - m[2]['h'])) >= 45)))
    for omega, name in ((TURN_MAX, 'the rig\'s turn rate'), (TURN_WIDE, 'the wide rate'), (220.0, 'a rate of 220'), (400.0, 'a rate of 400')):
        dt, dp, dh, dpt, miss = [], [], [], [], []
        for run, n, a0, b, tx, tz, r, v, v0 in moving:
            g = steer(a0['x'], a0['z'], a0['h'], v0, tx, tz, r, v, omega, limit=20.0)
            if not g['reached'] or g['turned'] > ORBIT:
                miss.append('%s script %d' % (run, n))
                continue
            dt.append(g['t'] * 1000 - b['ms'])
            dp.append(math.hypot(g['x'] - b['x'], g['z'] - b['z']))
            dh.append(abs(wrap(g['head'] - b['h'])))
            if abs(wrap(bearing(a0['x'], a0['z'], tx, tz) - a0['h'])) >= 45:
                dpt.append(dp[-1])
        if dt:
            print('    %-20s (%3.0f): the model does not reach %d the game reached%s; time model - log: median %+.0f ms, 8 in 10 within %+.0f .. %+.0f; place of \'reached\': median %.0f, '
                  '9 in 10 within %.0f (turns of 45+: median %.0f); heading: median %.0f degrees'
                  % (name, omega, len(miss), ' (%s)' % ', '.join(miss[:8]) if miss else '', q(dt, .5), q(dt, .1), q(dt, .9), q(dp, .5), q(dp, .9), q(dpt, .5) if dpt else 0, q(dh, .5)))
    # (left out: a target within 45 degrees - both readings agree; one he is at already; one over 1500 away - the hook had moved him, the join)
    stand = [s for s in stand if abs(wrap(bearing(s[2], s[3], s[6], s[7]) - s[4])) >= 45 and s[8] < math.hypot(s[6] - s[2], s[7] - s[3]) <= 1500]
    print('(2) %d gotos FROM A STAND with the target 45 degrees or more off his heading (his place from a pos line of the wait where there is one):' % len(stand))
    e1, e2 = [], []
    for run, n, x, z, h, b, tx, tz, r, v, seen in stand:
        off = wrap(bearing(x, z, tx, tz) - h)
        d = math.hypot(tx - x, tz - z)
        g1 = steer(x, z, bearing(x, z, tx, tz), 0.0, tx, tz, r, v)
        g2 = steer(x, z, h, 0.0, tx, tz, r, v, TURN_MAX, ramp=STAND_ARC)
        p1, p2 = math.hypot(g1['x'] - b['x'], g1['z'] - b['z']), math.hypot(g2['x'] - b['x'], g2['z'] - b['z'])
        e1.append(p1); e2.append(p2)
        print('    %-5s script %3d: %4d away, %+4d degrees off, radius %3d, %s: log %4d ms, reached at (%d, %d) heading %d | he turns first: %4.0f ms, place %3.0f off, heading %+4.0f | '
              'an arc: %s' % (run, n, d, off, r, 'sprint' if v == SPRINT else 'walk', b['ms'], b['x'], b['z'], b['h'], (g1['t'] + abs(off) / STAND_TURN) * 1000, p1,
                             wrap(g1['head'] - b['h']), '%4.0f ms, place %3.0f off, heading %+4.0f' % (g2['t'] * 1000, p2, wrap(g2['head'] - b['h'])) if g2['reached'] else 'NOT REACHED'))
    if e1:
        print('    place of \'reached\', model against log: he turns first: median %.0f, worst %.0f; an arc from where he looks: median %.0f, worst %.0f' % (q(e1, .5), max(e1), q(e2, .5), max(e2)))
    sp = [math.hypot(b['x'] - a0['x'], b['z'] - a0['z']) / (b['ms'] / 1000.0) / v for run, n, a0, b, tx, tz, r, v in nowait
          if b['ms'] >= 150 and abs(wrap(bearing(a0['x'], a0['z'], tx, tz) - a0['h'])) < 45]
    if sp:
        print('(3) %d gotos right after a goto WITHOUT keep, no wait between, the target within 45 degrees: his speed over the whole goto was %.2f of its own speed (walk %d, sprint %d) in the '
              'median and %.2f at the least: a goto without keep is NOT a stop unless a wait follows' % (len(sp), q(sp, .5), WALK, SPRINT, min(sp)))
    return 0


HUMAN_RE = re.compile(r'escort: (?:record \d+ .*re-pointed: you are [\d.]+ m away at|you: record 0, player \w+, feet) \(([-\d]+), ([-\d]+), ([-\d]+)\)')


def starts(folder, runs):
    """THE START, measured (re\\playtest.md 10.1): per run the second after 0x19 at which the first goto began, the last
    line that has the human on his START place and the first that has him off it (every line with his place: `pos`,
    a goto's result or 'stuck', klescort's 'you are ... at'), how far off, and how the first goto ended. A goto that
    began before he could move ('held') shows the moment he was let go to within the lines' spacing."""
    print('%-26s %-20s %8s  %-18s %-24s %s' % ('run', 'level', 'goto at', 'last on START', 'first off it (units)', 'the first goto'))
    for run in runs:
        log = os.path.join(folder, run + '.log')
        if not os.path.isfile(log):
            print('%-26s no %s' % (run, log))
            continue
        t19, seq, first, name, end, held = None, [], None, '?', '', False
        for s in open(log, errors='replace'):
            m = re.match(r'(\d\d):(\d\d):(\d\d)\.(\d+) (.*)', s)
            if not m:
                continue
            t, b = clock(m.groups()), m.group(5)
            mm = re.search(r"scene '([^']*)' is loaded", b)
            if mm:
                name = re.split(r'[\\/]', mm.group(1))[-1]
            if t19 is None:
                t19 = t if 'session: state 0x18 -> 0x19' in b else None
                continue
            mm = GOTO_RE.search(s)
            if mm:
                g = mm.groups()
                if first is None:
                    first = t - t19 - int(g[8]) / 1000.0
                if not end:
                    end = '%s in %s ms, %d from the START place' % (g[7], g[8], 0)
                    end_at = (float(g[9]), float(g[11]))
                seq.append((t - t19, float(g[9]), float(g[11]), 'goto'))
                continue
            mm = re.search(r'script \d+: goto is stuck at \(([-\d]+), ([-\d]+), ([-\d]+)\)', b)
            if mm:
                held = held or first is None
                seq.append((t - t19, float(mm.group(1)), float(mm.group(3)), 'stuck'))
                continue
            mm = POS_RE.search(s)
            if mm:
                seq.append((t - t19, float(mm.group(5)), float(mm.group(7)), 'pos'))
                continue
            mm = HUMAN_RE.search(b)
            if mm:
                seq.append((t - t19, float(mm.group(1)), float(mm.group(3)), 'escort'))
        if t19 is None or not seq:
            print('%-26s %-20s no round, or no line with his place' % (run, name[:20]))
            continue
        sp, last, off = seq[0][1:3], None, None
        for t, x, z, k in seq:
            d = math.hypot(x - sp[0], z - sp[1])
            if d <= 30.0 and off is None:
                last = (t, k)
            elif d > 30.0 and off is None:
                off = (t, k, d)
        if end:
            end = end.replace(', 0 from', ', %d from' % math.hypot(end_at[0] - sp[0], end_at[1] - sp[1]))
        print('%-26s %-20s %8s  %-18s %-24s %s' % (run, name[:20], 'held' if held else '-' if first is None else '%+.2f' % first, '-' if last is None else '%.2f s (%s)' % last,
                                             '-' if off is None else '%.2f s (%s) %d' % off, end or '-'))
    return 0


STAGES = [('the round begins', r'session: state 0x18 -> 0x19'), ('stage 1', r'bots: record 0 \(you\): heist stage \d -> 1'), ('stage 2', r'bots: record 0 \(you\): heist stage \d -> 2'),
          ('stage 3', r'bots: record 0 \(you\): heist stage \d -> 3'), ('the vehicle comes', r'bots: L\d+ s\w+ van [1-4] '), ('the join', r'join: player 0 entered box'),
          ('the crew follows', r'crewjoin: \d+ moved'), ('the escort follows', r'escort: record \d+ re-pointed'), ('the escort is let go', r'escort: record \d+ released \(the vehicle waits'),
          ('the van waits for him', r'script \d+: the vehicle\'s state is [34] '), ('aboard', r'bots: record 0 \(you\): aboard'), ('escaped', r'bots: record 0 \(you\): status6'),
          ('his death', r'fed: you: status 0 -> 1'), ('the fed', r'fed: YOU ARE A FED'), ('the climb', r'climb: edge \d+: started')]


def judge(ini, log):
    """What a run showed, read from its log against the script that ran (and <ini>.plan.json when it is there)."""
    pj = os.path.splitext(ini)[0] + '.plan.json'
    plan = json.load(open(pj)) if os.path.isfile(pj) else None
    cmds = read_script(ini)
    by_design = set(plan['by_design']) if plan else set()
    stages = [dict(s) for s in plan['stages']] if plan else [dict(key=k, re=r, what='', need=False) for k, r in STAGES]
    kinds = {g['line']: g['kind'] for g in plan['gotos']} if plan else {}
    lines = open(log, errors='replace').read().splitlines()
    tm = lambda s: clock(re.match(r'(\d\d):(\d\d):(\d\d)\.(\d+)', s).groups()) if re.match(r'\d\d:\d\d:\d\d\.\d+', s) else None
    t19 = death = gone = None                           # gone: dead, or aboard - the gotos after that steer nobody (or a fed)
    res, stuck, skipped, front_no, result, away, n19 = {}, collections.Counter(), {}, 0, None, set(), 0
    for s in lines:
        t = tm(s)
        if t is None:
            continue
        if 'session: state 0x18 -> 0x19' in s:
            n19 += 1
        if t19 is None and 'session: state 0x18 -> 0x19' in s:
            t19 = t
        if death is None and re.search(r'fed: you: status 0 -> 1|bots: record 0 \(you\): (dead|status1|aboard)', s):
            death, gone = t, 'he was aboard' if 'aboard' in s else 'his death'
        m = GOTO_RE.search(s)
        if m:
            g = m.groups()
            res[int(g[4])] = (g[7] == 'reached', t, int(g[8]), s.split(': ', 1)[-1][:150])
        m = re.search(r'script (\d+): goto is stuck', s)
        if m:
            stuck[int(m.group(1))] += 1
        m = re.search(r'script (\d+): no moving player found', s)
        if m:
            skipped[int(m.group(1))] = t
        if 'game window in front at the last one: no' in s:
            front_no += 1
        if 'RESULT ' in s:
            result = s.split('RESULT ', 1)[1][:90]
        m = re.search(r'escort: record \d+ re-pointed: you are [\d.]+ m away at \(([-\d]+), ([-\d]+), ([-\d]+)\)', s)
        if m:
            away.add(m.groups())
        for st in stages:
            if 'at' not in st and t19 is not None and re.search(st['re'], s):
                st['at'] = t
    o = ['kl_playtest judge: %s against %s%s' % (os.path.basename(ini), log, '' if plan else ' (no .plan.json beside the ini: every known stage line is looked for, none is asked for)')]
    if t19 is None:
        o.append('THE ROUND NEVER BEGAN (no "session: state 0x18 -> 0x19"): nothing to judge')
        print('\n'.join(o))
        return 1
    gl = sorted(n for n, c in cmds.items() if c and c[0] == 'goto')
    first = next((n for n in gl if n in res or stuck[n]), None)
    if first is not None and first in res:
        o.append('the round began at %s; the first goto (script %d) started %.1f s after it (he can move 10.1 .. %.1f s after it)'
                 % (time_text(t19), first, res[first][1] - res[first][2] / 1000.0 - t19, FREE_S))
    fedp = plan.get('fed') if plan else None
    fedl = {g['line'] for g in plan['gotos'] if g.get('fed')} if plan else set()
    live = [n for n in gl if n not in by_design and n not in fedl]
    done = [n for n in live if n in res or n in skipped]
    dead = lambda n: death is not None and ((n in res and res[n][1] > death) or (n in skipped and skipped[n] > death))
    okn = [n for n in done if n in res and res[n][0] and not dead(n)]
    bad = [n for n in done if (n in skipped or not res[n][0]) and not dead(n)]
    o.append('gotos: %d in the script (and %d that end by their timeout by design%s); %d ran before the round ended%s: %d reached, %d NOT reached or skipped; %d \'stuck\' line(s) on %d goto(s)'
             % (len(live), len([n for n in gl if n in by_design and n not in fedl]), '; the fed\'s %d are judged below' % len(fedl) if fedl else '', len(done),
                ', %d of them after %s (left out)' % (sum(1 for n in done if dead(n)), gone) if death else '', len(okn), len(bad),
                sum(stuck[n] for n in live if not dead(n)), sum(1 for n in live if stuck[n] and not dead(n))))
    if len(done) < len(live):
        o.append('   %d goto(s) of the script never ran (script %d and after): the round was over, or the script was still waiting when it ended'
                 % (len(live) - len(done), next(n for n in live if n not in done)))
    for n in bad:
        o.append('   script %d [%s]: %s' % (n, kinds.get(n, ' '.join(cmds[n][:5])), 'no moving player found - skipped' if n in skipped else res[n][3]))
    for n in live:
        if stuck[n] and n in res and res[n][0] and not dead(n):
            o.append('   script %d [%s]: reached after %d \'stuck\' line(s), in %d ms' % (n, kinds.get(n, ' '.join(cmds[n][:5])), stuck[n], res[n][2]))
    for n in sorted(by_design):
        if n in res:
            o.append('   script %d: %s - EXPECTED (a push by design)' % (n, 'reached' if res[n][0] else 'NOT reached'))
    last_ok = None
    missing = []
    for st in stages:
        if 'at' in st:
            o.append('   %-22s FOUND %s (0x19 %+.1f s)%s' % (st['key'], time_text(st['at']), st['at'] - t19, '   ' + st['what'] if st.get('what') else ''))
            last_ok = st['at'] if st.get('need') else last_ok
        elif plan:
            o.append('   %-22s MISSING%s%s' % (st['key'], '' if st.get('need') else ' (not asked for: it depends on the crew)', '   ' + st['what'] if st.get('what') else ''))
            if st.get('need'):
                missing.append(st['key'])
    if away:
        pl = [(float(a), float(c)) for a, _b, c in away]
        span = max(math.hypot(p[0] - q[0], p[1] - q[1]) for p in pl for q in pl)
        o.append('   the escort was called to %d different place(s) of the human, up to %.0f m apart (he %s)' % (len(away), span / 100, 'MOVED' if span > 300 else 'stood'))
    if fedp:                                            # the fed's part: where he appeared, what his gotos did, how far he got
        o.append('THE FED (the script\'s part from line %s on, written for group %s of the AFTER_DEATH points):' % (fedp['line'], fedp['group']))
        m = next((re.search(r'fed: YOU ARE A FED: .*? at \(([-\d]+), ([-\d]+), ([-\d]+)\)', s) for s in lines if 'fed: YOU ARE A FED' in s), None)
        if m:
            p = tuple(float(v) for v in m.groups())
            q = min(fedp['points'], key=lambda q: math.hypot(q['at'][0] - p[0], q['at'][2] - p[2]))
            fl = q['floor'] if q['floor'] is not None else q['mesh']
            o.append('   he appeared at (%d, %d, %d): %d from point %d (group %d%s); the floor there is %s: %s' % (
                *p, math.hypot(q['at'][0] - p[0], q['at'][2] - p[2]), q['n'], q['group'], '' if q['n'] in fedp['group'] else ' - NOT the group the gotos were written for',
                'not known' if fl is None else '%d' % fl, '' if fl is None else 'ON THE GROUND' if abs(p[1] - fl) <= 40 else '%+d from it' % (p[1] - fl)))
        else:
            o.append('   no "fed: YOU ARE A FED" line: he did not come back as police (was he shot at all? "fed: you: status 0 -> 1" %s)' % ('came' if death is not None else 'did not come'))
        pk = next((s for s in lines if re.search(r'script %d: peek 0168ea60 = ' % (fedp['line'] + 1), s)), None)
        if pk:
            o.append('   klfed\'s switch when the fed\'s part began: %s' % ('0 = he stood as police' if '= 00000000' in pk else 'NOT 0: he was not police yet - the gotos steered the hero'))
        last = None
        by = fedp['blind'][-1][1] if fedp.get('blind') else None        # the crew's mesh height a BLIND goto aims at
        if by is not None and fedp.get('edge') and fedp['edge'][1] - by < 2 * BLIND_DY:
            by = None                                   # ... on his own floor (a lift car): the height says nothing, the goto's 'reached' does
        down = False
        for s in lines:
            mm = re.search(r'pos (fed-[^:]*): me #\d+ \(([-\d]+), ([-\d]+), ([-\d]+)\)', s)
            if mm:
                note = ''
                if by is not None and mm.group(1).startswith('fed-blind'):      # review 3, S2: a goto's 'reached' is 2-D - only the height says he came down
                    dy = float(mm.group(3)) - by
                    down = down or abs(dy) <= BLIND_DY
                    note = '   AT THE CREW\'S HEIGHT (%d): there IS a way down' % by if abs(dy) <= BLIND_DY else \
                           '   %+d from the crew\'s mesh (%d): NOT down - a "reached" of the blind goto before it is a distance in the plan and shows no way' % (dy, by)
                o.append('   %-22s (%s, %s, %s)%s' % (*mm.groups(), note))
                last = tuple(float(v) for v in mm.groups()[1:])
        fg = [g for g in plan['gotos'] if g.get('fed')]
        ok = [g for g in fg if g['line'] in res and res[g['line']][0] and g['kind'] != 'fedblind']
        nb = [g for g in fg if g['kind'] == 'fedblind']
        o.append('   his gotos: %d in the script%s, %d ran, %d reached%s' % (len(fg) - len(nb), ' (and %d blind ones, judged below)' % len(nb) if nb else '',
                 sum(1 for g in fg if g['line'] in res and g['kind'] != 'fedblind'), len(ok),
                 '; the last one reached: script %d (%d, %d) [%s]' % (ok[-1]['line'], ok[-1]['x'], ok[-1]['z'], ok[-1]['kind']) if ok else ''))
        if nb:
            nr = sum(1 for g in nb if g['line'] in res and res[g['line']][0])
            if by is None:
                o.append('   the blind gotos: %d of %d reached (the crew\'s mesh is on his own floor there: reached = he got out of what the collision shuts him in)' % (nr, len(nb)))
            else:
                o.append('   the blind gotos: %d of %d "reached" in the plan, which shows nothing by itself; by the height he %s' % (nr, len(nb),
                         'CAME DOWN to the crew\'s mesh' if down else 'did NOT come down (or no pos fed-blind line is in the log)'))
        for g in fg:
            if g['line'] in res and not res[g['line']][0]:
                o.append('      script %d [%s]: %s%s' % (g['line'], g['kind'], res[g['line']][3], ' - a blind one: expected either way' if g['kind'] == 'fedblind' else ''))
        if last and fedp.get('goal'):
            d = math.hypot(last[0] - fedp['goal'][1], last[2] - fedp['goal'][3])
            o.append('   at the end he stood %d from his goal, the crew\'s \'%s\' place (%d, %d, %d): %s' % (d, *fedp['goal'], 'HE GOT THERE' if d <= 150 else 'he did not get there'))
    why = []
    if plan and plan.get('rounds', 1) > 1:              # review 3, S4: RESULT PASS comes on round 1's page too when the page's trap fired early
        o.append('ROUNDS: "session: state 0x18 -> 0x19" came %d time(s); the script is written for %d (gotos and stage lines above are of BOTH rounds: a goto\'s line is the last '
                 'one logged for it, a stage is found at its first line)' % (n19, plan['rounds']))
        if n19 < plan['rounds']:
            why.append('only %d round(s) began of the %d the script is for (the page\'s trap fired on the old page, the last life was lost, or RETURN did not start a round)'
                       % (n19, plan['rounds']))
    if front_no:
        why.append('the game window was not in front (%d nudge line(s) say so): the round stood still' % front_no)
    if result:
        o.append('RESULT %s   (says only that the game did not fault and the script ended)' % result)
    if death is not None and gone == 'his death' and not (plan and plan.get('die')):
        last = max([n for n in res if res[n][1] <= death] or [0])
        loss = [float(m.group(1)) for m in (re.search(r'balance: you lost ([\d.]+)', s) for s in lines) if m]
        why.append('HE DIED %.1f s after 0x19, after script %d: nothing after that was walked%s'
                   % (death - t19, last, ' (his largest losses: %s)' % ', '.join('%.1f' % v for v in sorted(loss)[-3:]) if loss else ''))
    if missing:
        why.append('stage(s) that did not come: %s' % ', '.join(missing))
    if bad:
        why.append('%d goto(s) NOT reached (script %s): the leg after each started from wherever he stood' % (len(bad), ', '.join(str(n) for n in bad)))
    if result and result.startswith('FAIL'):
        why.append('the game or the script failed: RESULT %s' % result[:70])
    if plan:
        o.append('VERDICT: %s' % ('every stage the script asks for came, every goto was reached' if not why else 'NOT a clean run - ' + '; '.join(why)))
    else:
        o.append('VERDICT (no plan: no stage is asked for): %s' % ('every goto was reached, he lived' if not why else 'NOT a clean run - ' + '; '.join(why)))
    print('\n'.join(o))
    return 1 if why else 0


def time_text(t):
    return '%02d:%02d:%06.3f' % (t // 3600, t % 3600 // 60, t % 60)


if __name__ == '__main__':
    sys.exit(main())
