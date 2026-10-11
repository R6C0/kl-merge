# Retomoto Tower: the run to the car in lanes

Track K, 2026-10-11 afternoon. **SECOND FORM, after the adversarial review** (`re/retomoto_bots_street_review.md`:
ACCEPT WITH FIXES; what was done about each point: section 9). OFFLINE: nothing here was run in the game by this
track, nothing was installed, committed or pushed. Files: `tools/kl_fa_bots_rt.py` (the street half; the tower's gates
are untouched), `tools/kl_fa_bots_dyn.py` (one thing learnt, section 4.2), this note.
Builds: `<work>\build\z_lanes\retomoto_full` (lanes + the gates) and `retomoto_full_r` (+ the dynamic step). The FIRST
form's builds, checks, pictures and live scripts are kept in `<work>\build\z_lanes\round1` - they FAIL the tool's
check as it is now (129 FAIL: sections 5.4, 9) and are not to be run.
Pictures: `<work>\build\z_lanes\maps\` (`legend.txt` there).
Words: **READ** = disassembled in `kl2.exe` at the address given (by an earlier track; nothing new was read here);
**MEASURED** = counted on the build's files or on the live logs; **ASSUMED** / **GUESS** = not established.
**THE WALK MODEL** = `kl_fa_bots_rt.walk_model`: a bot walks straight lines through a step's places at a fixed
speed, a step is 'reached' 10 m (3D) before its last place, a timer starts then. Every 'at the rally after N s' and
'stands N s' below is that model's, at 300 units / s (a free bot) and at 150 (the slowest walk the chain is laid
for). Nothing of it was seen in the game.
Distances in world units (100 = 1 m) unless 'm'. North is +z, the tower stands EAST of the road (+x).

The owner, 2026-10-11 12:35, after the gates build: 'the ai is almost good, when doing the run to the car they need to
spread out more like some try going to the other side some stay on that side etc. they need to use the map a bit more
but the tower of retomoto tower is beautiful now'.

## 0. Short answers

- **Today the seven take one line down one side** (section 1): both ramps of the lobby, the middle of the door, one
  diagonal over the square, the east pavement. In three runs with place lines (42 lines after the join in J0, 104 in
  J1, 70 in B1) **no bot was ever west of the road's middle**; the police stand 22 west and 22 east of it.
- **And a bot that stood at a gate when the human took the lift stops ADVANCING.** What the gates' note 'THE JOIN'
  feared is what happened in J1 and B1: every bot within the 10 m of a hold whose men lived (its wait armed) lost its
  street step within 30 s and stayed in the lobby or on the square for the rest of the run, moving about among the
  planters but going nowhere - six of seven in J1, two of six in B1; the bots that were between two holds walked the
  street (1.3). The lead read J1 as 'in the street fight': their place lines say they never left the square.
- **The old chain's last leg runs through a bus.** `kl_fa_street` parked bus #10 on the strip the bots walk from
  the rally to the van's stop (the mesh has no hole under it); B1's scripted human, who walks the bots' places,
  stuck at its south end (1.5).
- **Built** (section 3; the pictures `maps\*_2_lanes*.png`): behind the lobby's EXITS_BANK box every bot's street
  chain is now (A) a timed way through the lobby in bounds of at most 6 m that runs by a clock for 31 s - the clock is laid for a walk of 150 units / s,
  so a bot at that speed or faster always has a timer pending, and a bot whose street step a late wait of the tower
  has taken is ordered on again by it -, (B) a draw between two lanes (a RandomTrigger; three squads always take one
  lane each), (C) the lane, which begins inside the building and crosses the square: holds at cover boxes with a
  timer each (the walk in at 150 units / s + a stand of 1..2.5 s), no sprint, **no leg within 2 m of any place the
  police stand at or are sent to** (the nearest is 2.6 m; point-blank is 1.6 m), (D) the old rally, then the level
  exit box and a way round bus #10 to the places beside the stop.
  Three lanes: **E** the east pavement (this side), **X** the east carriageway and through the median to the far
  side (as built: through its slit at z 1440 or round its south end, 3.3), **W** the far side from the square on.
- **The pace** (the walk model): at the rally E 109..112 s after the join, X 118..134 s, W 132..139 s at 300 units / s;
  149..201 s at 150. That is slower than the old chain (the first of J0's sprinters was at z -150 at 40 s; all
  five were dead by 49 s) and 10..30 s slower than this track's first form: the price of holds that are holds. A
  human who is at the van before the crew leaves it to the hook: `FollowOut` calls it when HE has stage 3, and
  **this build wants `FollowOutHold=15` beside it - a key that has never run in the game: K2 runs it first**
  (3.7, 6.3).
- Both builds pass every check; the talk check FAILs its one line on the hand-set delays exactly as z_rooms does
  (section 5). The tower half is z_rooms' node for node, REF labels apart (5.3).
- **Nothing of it has run.** The live checks are section 6: K0 (police -> crew at the floor: lanes or one file?),
  K1 (the owner's balance: who lives?), K2 (a walking human, the hook's parts on).

## 1. What the seven do today (MEASURED; `<work>\build\klhook\live\*.log`, pictures `maps\*_1_today_*`)

The hook's `hop: bot N stage S: node (x, y, z)` lines come every 5 s; 'bot n' is the n-th AI record in play. t = seconds
after `crewjoin: the jump .. is pending`. Scratch `K\logs.py`, `K\today.py`.

| run | build | the human | bots at the join | read |
|---|---|---|---|---|
| J0_DM09_join_oldchain | `z_route4\retomoto_tab_fix` (no gates; the same street chain) | walks the tower without a shot, takes the lift at GO+101, stands in the lobby car | 5 | the old street chain undisturbed |
| J1_DM09_join | `z_rooms\retomoto_full` (the gates) | the same walk, GO+110, stands 80 s | 7 | the join with waits armed |
| B1_DM09_board_gates | the same | the same walk, then SPRINTS to the van (in the level exit box at +44 s, aboard +52 s) | 6 | the whole street |
| the owner, 12:28..12:33 | the same, his hook (`Escort=1 BoardAll=1 FollowOut=1`) | plays; all seven at the tower car at the join; dies on the street at +40 s at about (-300, -1740) | 7 | no place lines; three bots dead in the next 85 s |

### 1.1 One file, one side

- Lobby: the hook puts them 3..5 m west of the lift car; `heist stage 1 -> 2` 1.4..4.0 s later for every bot of every
  run (the EXITS_BANK box lies across both ramps). They take both ramps (J1: 4 north, 3 south) and meet again in the
  middle of the door.
- Square: all through the two northern ways between the planters, on one diagonal, to the kerb at about
  (-460, -4020) (pictures `1_lobby_square_1_today_*`).
- Road: the east pavement / its kerb, x -500..-1500. **J0 at +40 s: all five within a band 3.8 m wide (x -1094..-1476).**
- **West of the road's middle (x < -3000): 0 bots at every one of the 216 place lines of the three runs.** Furthest
  west: -1638 (J0), -636 (J1), -2096 (B1: two who left the pavement for the taxis of the east carriageway, both dead
  there).
- Speed between two lines: about 230..440 units / s (J0's record 5: 296, 230, 403, 328, 288; the street steps are
  `eDMS_Sprint`); V_PLAN below is 300.

### 1.2 Where they die

| run | dead, t after the join (x, z) |
|---|---|
| J0 | r5 40.4 (-1296, -151); r1 41.7 (-1445, -3000); r4 42.6 (-1338, -4172); r3 45.0 (-1447, -1488); r2 49.4 (-1489, -2729): **all five, on the east kerb, z -4200..-150**, 34..61 hits each |
| J1 | r5 37.7 (-636, -2928), the one bot that kept its street step; alone on the pavement, 45 hits |
| B1 | r4 42.6 (-2092, -3153) and r3 49.0 (-1903, -2537) at the east carriageway's taxis; r7 60.4 (-438, -4032) at the kerb; r5, r2, r1 62.8..64.4 in ONE STEP of 252 as the van left with the human (the rules' own: `re/bots_follow_out.md`) |

The kerb between z -4200 and -150 is where wave 1's two east squads stand and run to (`020_FinancialAlley_LeftFurther`
(-1777, -1319) (-1813, -1885), `RightPlatform` (-1708, 188) ..; RunToCover points at (-1218, 594), (-600, -476),
(-906, 791) ON the pavement): the one file walks into five rifles 3..6 m away.

### 1.3 The join takes the street step of a bot whose wait is armed

A hold step of the gates sends its list - arms its `TriggerActorsDead` - within 10 m of the hold (READ, kl2 0x686c4c;
`re/retomoto_bots_rooms.md` 3.1). Where each bot stood when the human took the lift, against its own holds of the
build (`bots.json`), and what it did in the street:

| run | bot (record) | in the tower, from its hold | on the street |
|---|---|---|---|
| J1 | 1 | reception 1.9 m | furthest west x 617 at +26; behind the planters' walls to the end |
| J1 | 2 | reception 4.4 m | x 1394; stops advancing at +26 |
| J1 | 3 | reception 3.1 m | x 2245 at +16; walks BACK to (3417, -7226) |
| J1 | 4 | reception 8.8 m | x 3073 at +16; stands at (3406, -6132) |
| J1 | 5 | reception 12.6 m: not within 10 m | **walks on**: (-636, -2927) at +37, dead there |
| J1 | 6 | reception 0.4 m | x 850; stops advancing at +21 |
| J1 | 7 | 5.5 m from the table's place (its loot wait) | x 350 at +37; back to (976, -6301) |
| B1 | 2 | door 0.0 m | stands at (5262, -6000) from +11 to +51 ('board: record 2 .. held for 40 s') |
| B1 | 5 | door 0.0 m | stands at (3406, -6132) from +11 to +51 (the same line) |
| B1 | 4 | reception 2.1 m | walks on (the reception's men were dead: that gate is the one the bots win, run G1) |
| B1 | 1, 3, 7 | 10.5 m, 5.2 m (reception), 6.0 m (door: behind him) | walk on |

J1: **six of the six bots inside 10 m of a hold stopped advancing 16..26 s after the join, the one outside walked
on.** B1: the two that stood exactly at their door hold stopped within 11..16 s. None of them went on until the hook
raised it. ('Stopped advancing', not 'stood': J1's bots 1, 6 and 7 move among the planters to the end - bot 7's x
between +26 and +77 s: 587, 650, 350, 750, 1154, 1076, 976, 1137 - they are in the square's fight, they do not leave
it.) NOT SHOWN: why B1's bots 3, 4 and 7, 5.2 / 2.1 / 6.0 m from a hold, walked on - 'the reception's men were
dead, so the wait fired at once and was not armed' fits, and no log line says it (enemy deaths are not logged). The
rule fits 8 of 8 bots that stopped and rests on that explanation for the 3 that did not. So the late wait fires (at most 30 s after it was armed), starts the next TOWER step, that step takes the
place of the street step (ASSUMED until now, `re/bots_retomoto.md` N3) - and the old street chain, which only goes on
when the bot ARRIVES somewhere, is dead for him. In the owner's round all seven stood at the tower car (no wait is
armed there): nothing was taken. A human who runs ahead of the crew strands it.

### 1.4 The owner's round

`crewjoin: 7 moved`: six at their places beside the tower car (x 2307..2513, z 421..642), the escort 8 m short of his
(1696, 58), where the hook held him beside the owner - the gates had brought all seven to the car behind him. No place
lines. He ran the south ramp, the square's diagonal and the kerb (the escort's 'you are .. at' lines: (4423, -7194),
(3379, -6729), (1942, -5257), (41, -3139), (-56, -1812), (-304, -1737)) and died at +40 s; his escort was 40 m behind.

### 1.5 The last leg runs through bus #10

`kl_fa_street.COVER_PLACE` parked six buses and a car on the road as cover; **the navigation mesh has no hole under
them** (its own comment says so). Bus #10 stands at x -1385..-1115, z 8930..10070. The old chain's leg from the rally
(-1207, 7995) to its place in the level exit box (-1493, 10048) crosses that rectangle from z 8930 on, and one of the
seven box places, (-1333, 10048), is inside it. B1: `script 186: goto is stuck at (-1350, -40, 8889)`, the bus's south
end, on the walk along record 2's places. Whether an AI bot gets round it is not seen (no bot reached it in a run
with place lines).

## 2. What is there (MEASURED on `z_rooms\retomoto_full`; pictures `maps\*_0_what_is_there.png`)

The street part of the mesh: 1,615 polygons (41,200 m2 with the bus terminal the round never reaches).

### 2.1 Lobby and square

- The lift car's jump entry (6272, 563, -6305); a landing at y 570 (x 5780..6000); **two ramps** down to the lobby
  floor (y 160): north (z -5560..-5800) and south (z -7180..-7430). The EXITS_BANK box x 5500..5700 lies across both.
- The lobby: 28 m to the door, 35 cover boxes (pillars 100 x 100 every 5 m in four rows, benches at the door). The
  door is open from z -5830 to -7150.
- A terrace (y 50..60, x 1616..2550: **one polygon of 8 x 13 m whose corners lie 24 off its fitted plane**), then four
  planters (x 550..1616; z -4950..-5350, -5850..-6250, -6740..-7140, -7640..-8050) with a low wall (cover box 600 x 40)
  on both long sides and high boxes inside. Ways down to the road (y -50): steps at the terrace's north-east corner
  and along the north of the first planter; the bay between planters 1 and 2 (planes, 4.5 m wide). **The two
  southern bays are ramps whose polygons are no planes** (fitted heights off by 1.1 and 2.3 m) and open on the two
  police cars of `Squad_InFront`.
- 20 cover boxes on the square. Run J1 had five bots in a row a metre apart behind one of the low walls, of the
  game's own choosing: several men do share a long cover.

### 2.2 The road: what the mesh offers (x from east to west)

| corridor | x | where | cover boxes (z -9000..11500) | note |
|---|---|---|---|---|
| east pavement | -1150..-600 | z -4075..9425, 5.5 m wide | 26 with the kerb | **no cover box between z -100 and 5400**; the old line |
| kerb | -1500..-1150 | things every few metres | | open to the carriageway at z -1625..-225 in four gaps; **shut from z -225 to 2425** by the foot bridge's east ramp |
| east carriageway | -2800..-1500 | 13 m | 51 (parked taxis: three boxes a car) | **shut at z 1865..2135 by bus #14** laid across it (gaps of 0.3 and 1.3 m): a dead end for a way from the south |
| median | -3145..-2855 | z -1410..4666 | 2 | gaps: **z -109..79 (1.9 m)**; a slit z 1380..1470 |
| west carriageway | -4550..-3200 | 13.5 m | 52 | the police's road block z 3450..3960 shuts it from the median to 2 m short of the kerb |
| west pavement | -5650..-4650 | 10 m | 29 | |
| bollards | -3044..-2955 | z 4755..8845: 89 x 89 every 200, **gaps of 111** | | the only line between the two sides north of the median |
| foot bridge | | z 1000..1300, y 293..552 | | walkable; a box on it wakes a sniper. Not used |
| open road | -6000..0 | z -9000..-1600: no median | scattered cars | where the far side is reached without a gap |

### 2.3 The police (unchanged: `kl_fa_street.py report`, byte for byte the same on both builds as on z_rooms)

47 actors in 24 squads. By where they stand at the load: **22 west of the road's middle, 22 east, 3 at the square**;
their 35 RunToCover points: 17 west, 18 east. Waves: the lift box (x 5801..6001) starts `Squad_InFront` (3, the square's
south end) and 5 s later `Squad_Teargasguys` (2); wave 1 = the first criminal on the east pavement strip
`tbExitLoot` (x -1100..-500, z -11900..-1100): 5 F07 squads / 10 men in the traffic z -1900..300 on both carriageways,
4 campaign squads / 11 men from behind; wave 2 = `tbReleaseDog` (the whole width, z -3600..-3000): the road block,
6 squads / 13 men, the dog, 4 campaign men; wave 3 = `tbEscapeAI` (z 1700..2300): 3 at the SWAT truck (-3600, 10300);
`tbRunToEscape1Player` (z 6200..6800): 28 s later every F07 squad walks to its place round the van - **12 of those 13
places lie west of the van's lane**. Every lane trips all of these: the boxes span the road.

### 2.4 The van

Waits at (-1850, 2, 8700), stops at z 10800; its lane x -1850 +- 350 from z 7900 north (`lane()`); the level exit box
x -5700..-300, z 8300..12800; the boarding box rides with the van to (-1852, 121, 10463). Because the police gather
west of the lane, every lane ends EAST of it, as the old chain did.

## 3. The lanes (as built)

### 3.1 The chain of a squad (`Street.lane_nodes`; every node a clone of the F07 form the old steps use)

    JumpPoint 06_Exit -> 050_DefendBehaviour_street   [the squad's place in the EXITS_BANK box: its ramp]
      -> 050_Timer_out_start (0.5 s + the squad's stagger 0..5 s)
      -> 051_DefendBehaviour_out_01 [one place] -> 051_Timer_out_01 -> .._out_02 -> ..      A. THE TIMED WAY, 6..8 places, inside the building
      -> 060_RandomTrigger_lane {1; 3, 3; one lane's first step each}                       B. THE DEAL (four squads)
           06k_DefendBehaviour_lane_<K>_01 [way places, the hold] -> 06k_Timer_lane_<K>_01  C. THE LANE: a hold, a timer;
           -> .._02 -> .. -> 06k_DefendBehaviour_lane_<K>_in [way places to the lane's end]    the first holds are on the square
      -> 069_DefendBehaviour_rally -> 070_Timer_rally (10 s)                                D. where all lanes meet
      -> 080.._082_DefendBehaviour_to_van [the level exit box, round bus #10, beside the stop]
      -> 090_SquadModifier_tight_defense_van

Every step is the route form (`DefendBehaviourRout` field 1 = 1..3 places, the last the place the bot defends: the
form the tower's gates hold at), `eDMS_NotSet`, field 8 = 1; every timer `TriggerDelay2 {s, 0.0, -1.0, 0, [next]}`;
the draw is stock F07 `Squad#02\060_RandomTrigger_BeforeStreet` with two weights of 3 (147 of the stock bots' draws).
(k: 061 = E, 062 = X, 063 = W. A step of the timed way is `051_DefendBehaviour_out_NN` in the STREET chain; the
tower's own steps are `03n_DefendBehaviour_out_<gate>` in the other chain.) 915 squad nodes in all seven squads (z_rooms 367, the first form 875).

### 3.2 A. The timed way - and why it runs by a clock laid for a slow walk

Through the lobby towards the door in bounds of **at most 6 m** (`CALL_REACH` 600), at a cover box where one is free
(a pillar, a bench), else a place on the way. Two streams: the north ramp and the lobby's north aisle (squads #03 #05
#08, towards bay n = the steps at the terrace's north-east corner); the south ramp and the door's middle (#02 #04
#06 #07, towards bay a = between planters 1 and 2).

A step is 'reached' - and sends its list - within 10 m of its place (READ, 0x686c4c). With every place within 6 m of
the place before, **a step of this way is reached the moment it starts** - also for a bot that is up to 4 m short of
the place before: its timer runs while the bot walks the bound, the timer starts the next step, and so on. For a bot
on its way a timer is pending all the time; the chain runs by the clock, not by arrivals.

**The clock runs at `V_SLOW` = 150 units / s**: a place's timer is its way at that speed (+ 1.2 s at a cover box).
A bot that walks 150 or faster is AT the place when its timer fires (a faster one stands the rest: at 300 half of
the time); it cannot fall behind. The clock runs 31 s (`JOIN_SAFE`): as long as a wait of the tower chain can still
fire (it was armed before the join; 30 s is its limit, and the table's loot wait is 30 s). In 31 s at that speed the
way is 31..43 m, so **the timed way ends inside the building or at the door** (x 1800..3120), not on the square as in
the first form; the rest of the line to the bay is the first stretch of the bot's lane.
Why 150: the lanes' steps are `eDMS_NotSet`; such steps of the gates build's bots in the tower, fights and stairs
included, moved at a median 124..127 units / s over 5 s, 90 % under 259, top 368 (the review's measurement on the
J1 / B1 place lines before the join); a free bot does about 3.7 m / s. The first form's clock ran at 160..220 (the
timers were the walk at 300 + what was missing to 31 s): tight from 250 on, and by the walk model 3.1..10.2 s of
its 31 without a pending timer at 150 (the review's S2 table, reproduced by `check()` on the first build to the
decimal). MEASURED on this build (`check()`, and the review's own `lanes_rev.py`): **0 s without a pending timer at
150, 200, 250, 300 and 400; 0 s at 120; 0..4.4 s at 100.** What the pace on the square under fire is, is NOT KNOWN: a
bot slower than 100..120 falls behind the clock, and for him it is the first form again.

**What that buys** (1.3): a bot whose street step a late tower step has taken stops - until the pending timer
fires. The step it starts names a real place for him (the next of his way, up to two bounds off); he walks there,
it is reached, its timer runs, and he is on the clock again, one bound late. One wait a bot can be armed, none can be
armed after the join, so it happens once. The old chain had no timer before the rally.
**What it costs**: 31 s for the first 31..43 m (the old chain's J0 bots were at the kerb 24 s after the join), a
place every 3.4..6 m, a free bot standing about half of that time.
ASSUMED: that a step whose place the bot has within 10 m sends its list at once and the bot still walks on to the
place (the gates rest on the second half: B1's bots stood on their hold places to the centimetre); that a newly
started step takes the place of the running one.
NOTE (the review's N5): the first street place is one point for the squads of a ramp ((5600, 160, -7162): #02 #04
#06 #07; (5600, 160, -6239): #03 #05 #08); with the stagger timers up to four bots are sent to one point and wait
there 1..5 s. Left as it is: the game spreads men who share a defend place (J1's row behind the planter wall).

### 3.3 B / C. Three lanes (`LANES`: each a line of points read off the pictures - GUESS)

| lane | its line (it chooses the HOLDS) | where the ways of the build cross the road's middle (MEASURED on the nodes) | the road block (z 3450..3960) |
|---|---|---|---|
| **E** this side | from the square's north-west corner up the east pavement, x about -900 | never | passes it on the east pavement |
| **X** the middle | through the kerb at z -4040, the east carriageway among the taxis (x -2000..-2500), the median's gap at z 0, the west carriageway's inner side (x -3500) | #02, #03, #08: west **through the median's slit at z 1440**; #06: west at z -1730, south of the median's end; back east through a bollard gap at **z 5280..5320** (#06: z 6480) | round its west end along the kerb (x -4800) |
| **W** the other side | west over the open road in front of the square (z -5560..-5950), the west carriageway's parked row (x -3950) | west over the open road at **z -5390..-4350**; back east through a bollard gap at **z 6480** (#07: 6920), south of bus #07 and of the waiting van | over the west pavement (x -5080) |

**A line chooses the holds, not the way.** The way from hold to hold is the cheapest on the grid (`Walk.leg`), and
no way of the build - nor of the first form's, whose note said otherwise - goes through the median's gap at z 0
(1.9 m of mesh): three of the four X ways cross at the SLIT at z 1387..1473 (0.9 m of mesh; the grid's one row of
cells at z 1440 lies 33 from both edges, which `Walk.NARROW_MIN` 33 lets through - it was meant to shut it; scratch
`K2\cross.py`, `cross2.py`). Left so, and said: the mesh is drawn in from what stands on it, so by the mesh the slit
is walked, and every X and W way comes back east through a bollard gap of 1.1 m of mesh anyway - the build rests on
'the game walks the gaps its mesh has' with or without the slit. A bot standing at (-2960, 1440) in a live run says
the game does not walk it: `NARROW_MIN` 36 then puts those ways through the gap at z 0 or round the median's end.

All three end 6..8 m south of the rally, east of the van's lane. A lane's way starts where the bot's timed way
ends (in the lobby), follows the rest of its bay's line over the square and then the lane's line; **its first one
or two holds are at the square's planters** (x 440..1600).

A lane's hold = a place 35..170 outside the edge of a cover box's own box (`cover_geom`: the model's box, which is
what the game makes the cover of - a bus's end box has its origin 9 m from its middle), on a plane, 35 from the mesh's
edge, **400 from every post of the police** (a start place, a place a behaviour names, a RunToCover point: the police
are posted at the same cars), preferably with the box between it and the way on. **One bot a box, counted by the
box the place is NEAREST to** (a hold place is only given to a box that is its nearest: the first form gave three
squads a place each round one sign of 1.7 m, by way of its neighbours; `box_room`: a box 2 m long takes two and one
4 m long three, 110 apart). The next hold lies a bound along the lane from the last (24 m, or the lane's length
over 6 where that is more: 27..40 m), never within 11 m (else its step is reached where the bot stands). Where no
cover is free in reach the bot walks on (a way place, no timer).

**A hold's timer** = the walk in at 150 units / s by the walk model - from where the step is reached, through the
step's way places, to the hold: 6.7 s on a straight line, up to 9.5 s round a corner - + the stand wanted (E 2.0 s,
X / W 1.5 s, - 0.5 / + 0.5 by squad, 1.0 at least): **7.7..10.5 s**. A bot at 150 stands 1.0..2.6 s at every hold, one
at 300 4.4..6.0 s (the table). The first form's timers of 5..9 s were a stand of 1.7..5.7 s at 300 and of nothing at
150 (the review's S1; `check()` on the first build: 'stands [0.0, 0.0]' at 150 for four of the eleven ways, under
1.5 s for all but one).

**No leg at a police post.** The ground within 230 of EVERY post of the police (124: the start places, the places
their behaviours name, the RunToCover points; `wall_posts`) is no ground for a way: the grid a way is laid on has
no cell there (`Walk` `walls`), every straight piece is held to 200 (`straight_clear`), and `check()` FAILs a leg
under 195. MEASURED on the build: the nearest any leg of any way comes to a post is **262** (#05 E past
`020_FinancialAlley_RightPlatform`'s RunToCover point (-906, 791) on the east pavement). The first form laid its ways
with a COST near a post, and they passed a post within 160 twenty-five times, within 80 eleven times - record 1, in
every round, 57 and 54 from two RunToCover points 12 and 20 s after their squads woke (the review's M1;
point-blank is 160: one burst step of a man posted there is 432 against a bot's 252 at the owner's CopToCrew 0.05,
`re/melee_damage.md`). The review's own
sampler (`Krev\lanes_rev3.py`, which reads the build's nodes itself) on this build: **0 passes within 160** (the
first form: 25).
**Every leg is a straight line on the mesh, clear of the parked vehicles and of the van's lane** (`Walk`: a 40-unit
grid of the mesh without the seven vehicles, the lane, the wall posts, the polygons that are no planes - the square's
two southern bays - and, for the lanes, the level exit box; through a gap of 111 and, not as meant, through the
median's slit of 86: above; `straight_clear` then holds each piece to the mesh itself).

### 3.4 The deal (`DEAL`)

| squad (record) | lanes | | squad | lanes |
|---|---|---|---|---|
| #02 (1) | X, always | | #06 (5) | X or W |
| #04 (3) | W, always | | #07 (6) | W or E |
| #05 (4) | E, always | | #08 (7) | X or W |
| #03 (2) | E or X | | | |

Per round: E has 1..3 of the seven, X 1..4, W 1..4; 16 deals. With all seven alive 4..6 of them go to the far side
(W from the square on, X from z 1440 or z -1730 on) and 1..3 stay east. (Squad#0N = record N-1; the human is record 0.)
**#08 no longer draws E** (the review's S3): the east pavement has few cover boxes for a lane and none between
z -100 and 5400; the squad that chooses last had ONE hold in 135 m on it, was the first bot in every wake box and at
the rally alone at +79 s - run J1's record 5 again (alone on that pavement, dead at +37.7 s). Now every way of the
deal has 4..6 holds (`check()`: 3 at least).
**'No lane is empty' holds while the three fixed squads live** (the review's S6): with #02 dead before the join X is
empty in 2 of 16 deals, with #04 dead W in 2 of 16, with #05 dead E in 4 of 16. Bots do die in the tower (B1: one;
J0: two). A deal by who is alive cannot be made in level data.

### 3.5 The tables (the plan of the build; `<build>\bots.json` plan.rt.street.lanes; scratch `K2\tables.py`)

**the timed way (the first 31 s after the join; the clock runs at 150 units / s)**

| squad (record) | ramp | towards bay | places (at a cover box) | way, m | each from the last, m | at the ramp, s | on the clock, s | its last place (x, z) | of the bay's line left, points |
|---|---|---|---|---|---|---|---|---|---|
| #02 (1) | south | a | 7 (7) | 36 | 3.7..6.0 | 0.5 | 33.0 | 2600, -5920 | 2 |
| #03 (2) | north | n | 8 (1) | 41 | 3.4..6.0 | 3.5 | 33.9 | 2360, -5560 | 13 |
| #04 (3) | south | a | 8 (1) | 41 | 4.8..6.0 | 1.5 | 31.9 | 1800, -5880 | 2 |
| #05 (4) | north | n | 6 (5) | 31 | 3.7..6.0 | 4.5 | 31.5 | 3120, -5880 | 16 |
| #06 (5) | south | a | 8 (0) | 43 | 4.9..6.0 | 2.5 | 32.9 | 1840, -6000 | 2 |
| #07 (6) | south | a | 6 (3) | 33 | 5.0..6.0 | 5.5 | 32.1 | 2880, -6640 | 3 |
| #08 (7) | north | n | 8 (0) | 41 | 4.8..5.5 | 2 | 31.3 | 2320, -5320 | 13 |

**the lanes: every squad's holds**

| squad (record) | lane | holds at cover x timer, s | stretches without cover | way from the timed way's end to the rally, m | at the rally, s after the first street step: at 300 / at 150 | stands at a hold, s: at 300 / at 150 | its holds (x, z) |
|---|---|---|---|---|---|---|---|
| #02 (1) | X always | 6 x 8.7 | 0 | 204 | 125 / 169 | 4.4..4.9 / 1.1..1.1 | (440, -5000) (-1840, -3360) (-2360, 320) (-3920, 2440) (-4080, 5000) (-2160, 6320) |
| #03 (2) | E drawn (1st) | 4 x 8.7 | 0 | 161 | 109 / 149 | 5.4..5.4 / 2.1..2.1 | (1240, -5480) (-360, -4040) (-1240, -240) (-1320, 5480) |
| #03 (2) | X drawn (2nd) | 6 x 8.2 | 0 | 204 | 129 / 173 | 4.9..5.5 / 1.5..1.6 | (960, -5480) (-1280, -4120) (-2400, -1400) (-3440, 2080) (-4200, 5000) (-2280, 6320) |
| #04 (3) | W always | 6 x 8.3 | 0 | 214 | 132 / 181 | 4.9..5.3 / 1.5..1.6 | (-1400, -5480) (-4040, -3960) (-3840, -600) (-4440, 2320) (-4520, 5400) (-2040, 6600) |
| #05 (4) | E always | 4 x 8.7 | 0 | 173 | 110 / 154 | 5.4..5.4 / 2.1..2.1 | (1600, -5960) (-440, -4320) (-1280, -840) (-1440, 5400) |
| #06 (5) | X drawn (1st) | 6 x 8.7 | 0 | 212 | 134 / 182 | 5.4..6 / 2..2.1 | (-1960, -4160) (-2400, -1520) (-3680, 720) (-4080, 3000) (-4440, 5200) (-2000, 6720) |
| #06 (5) | W drawn (2nd) | 5 x 8.7 | 0 | 222 | 133 / 190 | 5.4..5.5 / 2..2.1 | (-2600, -5920) (-4120, -2600) (-3680, 720) (-4920, 5040) (-2200, 6200) |
| #07 (6) | W drawn (1st) | 5 x 8.7 | 0 | 240 | 139 / 201 | 5.4..5.6 / 2..2.1 | (-1040, -5600) (-3920, -3960) (-3840, -400) (-5640, 3320) (-3120, 7080) |
| #07 (6) | E drawn (2nd) | 4 x 9.4 | 1 | 169 | 112 / 155 | 5.9..6 / 2.6..2.6 | (1000, -5680) (-800, -4160) (-1160, -1800) (-1080, 5520) |
| #08 (7) | X drawn (1st) | 5 x 7.7 | 0 | 209 | 118 / 166 | 4.4..4.6 / 1..1.1 | (520, -4840) (-2000, -3760) (-2480, 320) (-3960, 3160) (-2280, 5480) |
| #08 (7) | W drawn (2nd) | 6 x 10.5 | 0 | 240 | 137 / 194 | 4.4..5.8 / 1..1.1 | (800, -4840) (-2400, -6160) (-4240, -2600) (-3640, 1440) (-4760, 5320) (-1640, 6600) |

The timer in the second column is the hold's first; a hold whose step turns a corner has up to 10.5 s (the walk in
is longer). 'At the rally' counts from the bot's first street step, which is reached at the join or up to 2 m of
walk later (the check's NOTE).

**the lanes as bands**

| lane | what | always | drawn by | holds | cover boxes | x of its holds | z of its holds | nearest post of the police from a hold |
|---|---|---|---|---|---|---|---|---|
| E | this side: the east pavement | #05 | #03 #07 | 12 | 11 | [-1440, 1600] | [-5960, 5520] | [572, 1910] |
| X | the middle: the east carriageway, through the median's gap at z 0, the west carriageway's inner side | #02 | #03 #06 #08 | 23 | 17 | [-4440, 960] | [-5480, 6720] | [413, 1902] |
| W | the other side: across the road in front of the square, the west carriageway's parked row | #04 | #06 #07 #08 | 22 | 19 | [-5640, 800] | [-6160, 7080] | [413, 2024] |

**rally, level exit box, beside the van**

| squad | rally (x, z) | in the level exit box | turning points round the parked bus | beside the stop |
|---|---|---|---|---|
| #02 | -1207, 7995 | -1212, 8525 | (-1000, 8920) (-800, 9480) (-840, 9600) (-1040, 10160) (-1160, 10200) (-1320, 10200) | -1491, 10302 |
| #03 | -1287, 7915 | -1293, 8605 | (-1000, 8880) (-800, 9480) (-840, 9600) (-1040, 10160) (-1160, 10200) (-1320, 10200) | -1371, 10262 |
| #04 | -1287, 8075 | -1132, 8605 | (-1000, 8920) (-800, 9480) (-840, 9600) (-1040, 10160) (-1160, 10200) | -1491, 10182 |
| #05 | -1127, 7915 | -1212, 8685 | (-1040, 8840) (-800, 9480) (-840, 9600) (-1080, 10520) (-1200, 10560) | -1331, 10462 |
| #06 | -1127, 8075 | -1373, 8525 | (-1000, 8880) (-800, 9480) (-840, 9600) (-1040, 10160) (-1160, 10200) (-1360, 10200) | -1371, 10142 |
| #07 | -1367, 7995 | -1052, 8525 | (-800, 9480) (-840, 9600) (-1040, 10160) (-1160, 10200) (-1440, 10200) | -1491, 10062 |
| #08 | -1207, 7835 | -1373, 8685 | (-1040, 8840) (-800, 9480) (-960, 10400) (-1200, 10560) | -1331, 10582 |

### 3.6 D. Rally, box, van

The rally is the old chain's own place and wait (seven places round (-1207, 7995), 10 s each from his own arrival).
In the level exit box: seven places round (-1212, 8525), 2..4 m inside its south edge, each a straight line from the
squad's rally place. From there **round the east side of bus #10** (4..6 turning points, 21..24 m) to the old places
beside the stop, north of the bus. (These places and ways are the first form's, to the unit: no post of the police
is within 200 of them.)
NOT SHOWN (the review's N2): whether a WAY place of a step of two or three places must be touched or is, like the
last, taken from 10 m. If from 10 m, corners are cut: by the reviewer's arithmetic the line round bus #10 then
crosses the bus's north-east corner by about 16 units, and the detours round posts shrink. A bot's place lines at
z 8900..10100 in a live run answer it.

### 3.7 Decided from the measurements

- **No sprint anywhere.** J0: five bots sprinting one line, all dead in 40..49 s. The gates took the sprint out of
  the tower and the owner calls the tower beautiful. A crossing is walked like every other bound: a way place
  without a hold where there is no cover.
- **Hold spacing**: the mesh and the covers give E four holds in 160..175 m (one or two on the square, nothing
  between z -240 and 5400), X and W five or six in 205..240 m.
- **The pace** (the walk model; 3.5): at the rally E 109..112 s after the join, X 118..134 s, W 132..139 s at
  300 units / s; E 149..155, X 166..182, W 181..201 s at 150. The first E bot is in the level exit box - and calls
  the van - after the rally's 10 s wait: from about +120 s. (The first note's table added the hold
  timers whole to the walk and said 83..117 / 121..137 / 130..158 for its build; by the model that build was
  79..104 / 98..116 / 109..129: the review's S7.) So this form is 10..30 s slower than the first: the hold timers
  count the walk in at 150 (+ 2..3 s a hold), and the first 31 s cover 31..43 m, not 49..68.
- **The lanes do not wait for the human, and the human is not waited for** (the review's S4, the hook's source
  read): `FollowOut` gives every bot stage 3 once HE has it and ORDERS them to the boarding place only while the
  vehicle drives in with 2 s or more to go (`klhook/klescort.c` 160-173, 898-925; renewed every 2 s in that window
  only); while the vehicle waits the game's board tactic has a stage-3 bot, between two visits nothing orders him.
  A called bot that comes within 10 m of his running lane step's hold starts that hold's timer, and 8..10 s later
  the next lane step orders him to the next lane hold - north as well, but for X before z 0 and W before z 6700 on
  the far side of the median / bollards from the boarding place. With FO_J1's numbers (15 s from the call to the
  departure, bots at about 3 m / s, 3 of 7 aboard from 52..83 m) **more are left behind than with the old chain for a
  human who is at the van within two minutes**: one who has stage 3 at +44 s (B1's sprint) finds all seven still in
  the building or on the square, one at +90 s finds X and W 50..120 m of lane and one to three holds away - and the
  rules shoot whoever is
  in play when the van leaves with him (`re/bots_follow_out.md`). `FollowOutHold=15` (the driver waits while called
  crew comes nearer; never run in the game) is what this build wants beside it; `FollowOutSpare=1` is the other key.
  A human who fights his way in 3 minutes finds E gone: the first E bot in the level exit box calls the van and,
  with the human elsewhere, boards and ESCAPES at that visit (stock; runs I1..I4) - he does not 'find the E squads at
  the van'.
- **BoardAll** (15 s without 1 m of movement, stage 1 / 2, once somebody has called the vehicle): a lane hold keeps
  a bot 8..10.5 s at most, the rally 10 s: a healthy lane bot is never 'held'; a stuck one is raised once an E bot has
  called the van. No conflict found (the review's reading; nothing run).
- **Escort**: during the first 31 s the lane chain re-orders every 3..5 s: an escort is pulled between it and the
  hook, as in the tower (run E3_DM01: 13 re-points).
- **The police are woken on the E lane's clock** (the review's N4): the first bot on the east pavement strip wakes
  wave 1 and wave 2; the X and W bots walk into squads that have had tens of seconds to take their cover points.
  No lane enters a wake box earlier than the old chain did, none later either: the far side is not asleep when the
  far lanes arrive. That is why the ways keep off those points (3.3).

## 4. What changed in the tools

### 4.1 `tools/kl_fa_bots_rt.py`

- `STREET_LANES` (on) / `--no-lanes`: `plan()` calls `lanes_plan()` behind `street_plan()`; `Street.nodes()` hands a
  plan with lanes to `Street.lane_nodes()`. **`--no-lanes` builds z_rooms' bots step byte for byte** (5.4).
- The tables `LANES`, `DEAL`, `BAYS`, `BAY`, `RAMP` and the numbers above them (every one a GUESS);
  `cover_geom` (cover boxes as boxes), `box_room`, `street_posts` (+ RunToCover points), `parked` (which of
  kl_fa_street's vehicles stand on the road in this build), `Ground` (bucketed `at` / `clearance`), `Walk` (the grid a
  way is laid on), `straight_clear`, `Line`, `street_ground`, `lanes_plan`, `Street.lane_nodes`, `lanes_of` + the
  command `kl_fa_bots_rt.py lanes <folder> <out.json>` (the street chain read back from a build's nodes).
- **The fix round after the review** (section 9 says which point each answers):
  - `V_SLOW` 150: the timed way's clock (a place's timer = its way at `V_SLOW`; the way ends when the clock has run
    `JOIN_SAFE`, the rest of the bay's line - `bay_rest` - goes to the lane) and the hold timers; `CALL_REACH` 780 -> 600.
  - `walk_model(steps, v)` (the model of the head of this note), `program_steps`: the plan's and the check's pace,
    the seconds without a pending timer, the stand at a hold. The plan no longer adds hold timers to the walk.
  - `hold_stand` / `hold_timer`, `LANE_STAND`, `STAND_MIN`: a hold's timer = the stand + the walk in at `V_SLOW` by the
    walk model, set per hold in `lanes_plan`. `LANE_HOLDS` 6 -> 5.
  - `wall_posts`, `post_gap`, `POST_WALL` 200: every post of the police is a wall for `Walk` (no cell within 230) and
    for `straight_clear` (200).
  - `spots()`: a hold place belongs to the cover box it is nearest to (one bot a box by box).
  - `DEAL`: #08 draws X or W.
  - `street_ground`: the grid leaves out polygons that are no planes (fitted height off by more than `WARP_WAY` 30:
    the square's southern bays), since the lanes' own ways now cross the square.
- `check()`:
  - 3b, read from the build's nodes in every branch set: **a.** the clock (one place a step, within 8.5 m of the
    place before, a timer behind each, 31 s in all; **by the walk model at 150 units / s no second of the timed way
    without a pending timer**); **b.** the deal (two lanes at least; every lane has a squad that always takes it; a
    lane with a hold west of x -3000 and one without; a fork's ways are different lanes with a weight each; **every
    way has 3 holds at least**); **c.** holds at cover (within 200 of a cover box's box, 380 from every police post,
    10 m from the place the bot waited at before, out of the level exit box; **its timer 7.7 s at least, and by the
    walk model at 150 a stand of 1 s**); **d.** no two squads' holds within 100 of one another, whatever each draws,
    **and no cover box the nearest box of more squads' holds than its length takes**; **e.** from the timed way's
    last place to the place beside the van every leg a straight line on the mesh clear of the parked vehicles and
    the van's lane, no place in a vehicle's footprint; **f.** no place and no leg inside the level exit box before
    `070_Timer_rally`; **g. no leg of the whole street chain within 195 of a post of the police.**
  - The old street rules run on every branch set as before. One is wider: a place nobody stands at - a place of the
    timed way, a way place of a lane's step - may lie on a polygon whose fitted height is off by up to 30
    (`WARP_WAY`; the terrace, 24) - said in a NOTE with the count.
  - NOTEs: 'THE JOIN' says what the runs established and whether the build's street chain runs by the clock; 'THE
    PACE' (the walk model's rally times at 300 and 150); 'NO LEG AT A POLICE POST' (the nearest any leg comes to
    one); 'NO LANES' on a build without them; the first street place against the [CrewJoin] places (476..1212: a
    bot the hook puts on the far side of the landing walks 2 m before the clock starts).
- The gates: no line changed (`git diff`: additions behind `street_plan` and in `check()` section 3 only).

### 4.2 `tools/kl_fa_bots_dyn.py` (30 lines; every existing rule kept)

`parse()` refused a build with any RandomTrigger in a squad ('the squad already has the steps of this module') and
any step naming two things. Now: **a street chain in lanes is kept whole** - it is recognised by its names
(`_DefendBehaviour_lane_`, `_RandomTrigger_lane`), every node it can reach is recorded as kept, and the chain stays in
the squad's list with no element, so the tower chain before it is still 'a chain that the jump cuts off' for every
rule of the module. `make()` makes nothing for a kept chain. Any other RandomTrigger in a squad is refused as before.
The module's `check()` needed no change: its `graph()` walks the lanes' draw as it walks its own forks, and holds
every way of it to its fork rules (the ways meet again, every place on the mesh, a path, not through the level exit
box, not in the van's lane). Its two NOTEs 'fork 060_RandomTrigger_lane: its ways are [..] long' are the lanes'
lengths (W is up to twice E): meant.
So `retomoto_full_r` = the lanes build + what the dynamic step does in the TOWER (forks between the gates' holds,
staggered starts, the opening modifier); the street chain is the lanes build's, node for node.

## 5. Builds and checks

### 5.1 How they were made (`<work>\build\z_lanes\checks.txt` is the run's own record; logs in `z_lanes\steps\`; scratch `K2\chain.sh`)

As `z_rooms\retomoto_full` (re/retomoto_bots_rooms.md 6.1), from `<work>\build\rt_full6\1_guns`:
`kl_fa_bots_rt.py build` (lanes on) -> `kl_fa_talk.py build --map retomoto` -> `kl_bain.py build --stream
v_talk\str\PC_Def.str` (the stream file it wrote was rt_full7's byte for byte and was deleted again) ->
`kl_fa_bots_dyn.py fake-fix` -> the two talk delays of rt_full6 (`KLTalk.ini` sha1 6c78c079) = **`retomoto_full`**;
`kl_fa_bots_dyn.py build retomoto_full retomoto_full_r` = **`retomoto_full_r`**. Kept: `steps\2_bots` (the bots step
alone); the talk and Bain steps were thrown away once the builds were proved. The first form's builds were moved to
`z_lanes\round1` before the chain ran (nothing was written into them).

### 5.2 The checks (last line of each)

The chain of 2026-10-11 15:48-16:12, with the tools as they are in the tree but for comments (two comment blocks of
`kl_fa_bots_rt.py` were written after it; `kl_fa_bots_rt.py check` was run again on `retomoto_full` with the file as
it is: its log is the chain's byte for byte).

| check | `retomoto_full` | `retomoto_full_r` |
|---|---|---|
| `kl_fa_bots_rt.py check` | PASS (0 FAIL, 12 NOTE); 7 gates on the tower's way out; 3 lanes on the street; jump list 7; [CrewJoin] places 7 | the same line |
| `kl_fa_bots.py check` (inside it) | PASS (0 FAIL, 10 NOTE); 7 bots, 915 squad nodes | PASS (0 FAIL, 10 NOTE); 7 bots, 1014 squad nodes |
| `kl_fa_bots_dyn.py check` | PASS (0 FAIL, 6 NOTE); FakeTargets 1, outside the vision space 0; loot window: no place has an object a bot cannot take | PASS (0 FAIL, 6 NOTE); the same |
| `kl_impact.py` | problems: 0 in 1 levels | problems: 0 in 1 levels |
| `kl_map_guns.py check` | 6 guns with looks; problems: 0 | the same |
| `kl_fa_talk.py check` | FAIL 1, NOTE 0: 'the countdown's NOW! starts at [7.51], the blast is at 16.50' - the KNOWN line of the hand-set delays, as on rt_full6 / z_rooms (the owner chose that timing) | the same |
| `kl_bain.py check` | 26 Bain sounds, 21241 streamed records, 0 not in PC_Def.str (rt_full7's = the installed one); 0 problems | the same |
| sizes | .prm 79879056, .ANM 21642904, .fxc 17760648, .WAV 27802960 = z_rooms' | the same |
| `kl_fa_street.py report` | 47 actors below y 5000, 0 with a drawing fault; the report is z_rooms' byte for byte (police waves, their boxes, the van) | the same |
| bots step against its base (`steps\2_bots_diff.log`) | only the squad was added | dyn step: only the squad's steps were made anew |
| side files | KLJoin.ini, KLGuns.ini, KLWardrobe.ini = z_rooms' byte for byte; KLTalk.ini sha1 6c78c079 = rt_full6's = z_rooms' | the same |
| archive | 218,953,468 bytes, sha1 85c884eb4bb5 | 218,957,886 bytes, sha1 3220509616a8 |

The twelve NOTEs of `kl_fa_bots_rt.py check` are the standing ones of the gates build plus the lanes' own: THE JOIN
(what runs J1 / B1 showed and that the clock covers it BY THE PLAN, not by a run), the [CrewJoin] distance, THE PACE,
NO LEG AT A POLICE POST (the nearest: 262), the two way places on the terrace. The six of `kl_fa_bots_dyn.py check`:
its THE JOIN, the lanes' lengths at #07's draw, and '86..97 s of timers (stock bots: 16..85 s)' for four squads -
the street chain has 14..16 timers a way. None is a fault found.

**The review's own samplers on the new build** (scratch `Krev\`, run unchanged; outputs `K2\rev\`): `lanes_rev3.py`
- posts a way passes within 160: **0** (the first form: 25); legs off the mesh on a lane, in a parked vehicle, in
the level exit box before the rally, in the van's lane: 0. `lanes_rev.py` - seconds of the timed way with no timer
pending at 150 / 200 / 250 / 300 / 400 units / s: **0 for every squad** (the first form: up to 10.2 at 150); a bot at
300 stands 4.4..6.0 s at every hold (the first form: 1.0..5.7); nearest post from a hold 413; 57 holds, none inside
a cover box's box, each within 169 of one. With these ways the police are woken LATER than by the first form:
`tbExitLoot` at +40 s (34), `tbReleaseDog` +54 s (34), `tbEscapeAI` +78 s (51), the first bot in the level exit box
at about +118 s (89) - the walk model at 300.

### 5.3 The tower is untouched (`checks_full*\tower_same.log`, `tower3.log`, `members.log`)

Two diffs of z_rooms' build against z_lanes': track K's `K\tower_same.py` (every string spelled out: name, class,
property values, controllers, place, the .gms record's flags / group / model / rotation / translation / aux) and the
review's `Krev\tower3.py` (raw .prp tokens with key indices spelled out, every record field - type id, raw block,
REF label, list key, light links - nodes aligned by full path).

- `retomoto_full`: `tower_same`: **THE TOWER IS UNTOUCHED: only the squads' street nodes differ** - 25,738 nodes
  outside the seven squads and 217 tower nodes of the seven squads compared, all equal. `tower3`: 26,004 common
  nodes in the same order; 98 nodes only in z_rooms and 646 only in z_lanes, every one a squad's street node
  (050..099); of the common nodes outside the street chain NONE differs in name, class, properties, controllers,
  rotation, translation, flags, group, model, raw block, aux or links.
- `retomoto_full_r` against `z_rooms\retomoto_full_r`: `tower_same`: the same line - 25,738 nodes outside the squads
  and 316 tower nodes of the squads. `tower3`: 26,096 common nodes; the 26,054 of them that are no street node are in
  the same order (the 42 street-named ones are not: the dynamic step kept the lanes' chain where z_rooms' build had
  made its own; scratch `K2\order.py`).
- **What does differ outside the street chain, in both, as after every bots step** (the review's N1): the REF label
  (record +0x30) of 168 tower nodes (267 in `_r`) and of 21 squad / actor-group nodes - the labels follow the count
  of nodes before them - and the child count of the seven squad nodes. REF labels are used by room gates,
  neighbour lists, the surface table and .HVK placements; the .HVK is byte-identical and no squad node is a room.
- **Members**: of the archive's 30 members .prp .gms .buf differ (the squads); **.oct is 2,912 bytes longer than
  z_rooms' (in `_r`: 1,968 shorter) and .prm differs in 2,628 dwords, each by exactly that number** (record offsets
  into the .oct: the same picture as rt_full7 -> z_rooms); the sizes of the large members are equal, their bytes
  are not. Everything else is byte-identical (the review's `tower_bytes.py` on the first form; `members.log` here).

What differs is, in each squad, the nodes from `050_` on (the street chain) and nothing else: no gate, no hold of the
tower, no timer of the tower, no police squad, no box, no loot, no van node.

### 5.4 Proofs beside the checks

- **`--no-lanes` is the old chain**: `kl_fa_bots_rt.py build <1_guns> <out> --no-lanes` gives z_rooms' `steps\2_bots`
  archive byte for byte (sha1 e8e634de) and the same `KLJoin.ini` (run again with the tool as it is after the fix
  round: the same).
- **The builds are what the tool as it is makes**: the bots step built once more after the last edits of the tool
  (comments, and step names beyond `_wayf`) = `steps\2_bots`' archive byte for byte (sha1 e46ae07f).
- **`KLJoin.ini` of the lanes builds is z_rooms' byte for byte**: the [CrewJoin] places did not move.
- **The first form FAILS the check as it is now**: `kl_fa_bots_rt.py check z_lanes\round1\retomoto_full` = FAIL (129
  FAIL; `round1\rt_check_with_the_fixed_tool.log`): 7 x the clock at 150 (the seven squads), 45 x a hold's timer under
  7.7 s, 46 x a stand under 1 s at 150 by the walk model, 25 x a leg within 195 of a post (the nearest 8, 13, 28),
  5 x a crowded cover box, 1 x a way with one hold.
- **The check has teeth** (`<work>\build\z_lanes\neg_tests\`, `summary.txt`; scratch `K2\neg.py`): one planted fault
  a build - the PLAN made with a table, number or function changed in memory, the build written, the change put
  back, the check as it is run on the folder, the build thrown away.

| case | what was planted | the check |
|---|---|---|
| control | nothing | PASS (0 FAIL) |
| clock_short | the timed way runs 12 s instead of 31 | 7 FAIL 'a wait of the tower chain that was armed at the join ..' |
| clock_far | bounds of the timed way up to 14 m | 20 FAIL 'its step is not 'reached' as it starts' (27 in all) |
| **fast_clock** | the first form's clock: laid for 300 units / s, bounds up to 7.8 m | 7 FAIL 'a bot at 150 units / s is 3.3 s (..) of its timed way without a pending timer' |
| empty_lane | no squad always takes lane E | 1 FAIL 'lane E has no squad that always takes it' |
| one_side | one lane, E, for everybody | FAIL 'the street has 1 lane(s): nobody spreads' (9 in all) |
| **lone_walker** | bounds of 90 m between holds: ways with one or two holds | 8 FAIL '2 hold(s) at cover on its whole way (wanted 3 at least)' |
| open_hold | holds 3..4.2 m off their cover box | 53 FAIL 'it would wait standing in the open' |
| **short_stand** | every hold's timer 5..7.8 s (the stand taken out) | 56 FAIL 'a slow bot is ordered on before he has stood there' (113 with the model's rule) |
| on_post | holds allowed near a post of the police | 14 FAIL 'is 333 from a post of the police ..: wanted 400' |
| **leg_at_post** | the ways laid without the wall posts (the first form's way) | 44 FAIL 'passes 17 from a post of the police ..: at point-blank range' |
| shared_hold | two bots may get one hold place, every box takes seven | 3 FAIL 'two bots on one hold' (12 in all) |
| **crowd_box** | every cover box takes seven squads (places still 110 apart) | 8 FAIL 'is the nearest box of holds of 4 squads ..: a box of that length takes 2' |
| through_bus | the plan does not know the parked vehicles | 25 FAIL 'the leg .. parked ..' |
| early_exit | lane E ends inside the level exit box | 3 FAIL 'BEFORE the rally' (6 in all) |

Fifteen of fifteen as they must (bold = the fix round's five). Three needed a second go, and `summary.txt` keeps the
first: `on_post` met an IndexError in the plan (a leg of over 18 way places; fixed in the tool, the build's archive
unchanged by it); `fast_clock` planted as 'V_SLOW 300' alone was refused by the plan itself (over 14 places on a timed
way), so the first form's bound of 7.8 m went in with it; `lone_walker` planted as the first form's deal (#08 on E) is
no fault any more - #08 gets three holds or more on E now that a lane begins at the square's planters - so the bound
was planted. Twelve cases ran before the tool's last edits (comments, step names): the check's code did not change.

## 6. The live checks (for the lead; nothing here has run)

Scripts in `<work>\build\z_lanes\live\` (made with `tools\kl_playtest.py script` against the tree `w_tabM` with
`--build z_lanes\retomoto_full`, NOT RUN; `README.txt` there). For each run `Maps\DM09` of the tree must hold
`z_lanes\retomoto_full` (archive 218,953,468 bytes, sha1 85c884eb4bb5) and `Maps\DM09\KLJoin.ini` must be
`z_rooms\live\KLJoin_with_poslog.ini` (the lanes builds' own KLJoin.ini is z_rooms' byte for byte, so that test file
serves unchanged); place lines need `[CrewHop] Enable=1 Dry=1 Log=2` (in the scripts). All three have `[Bots] Tune=0
Backstab=0`: a backstabber leaves his route, and the first form's K1 had Tune=1 / Backstab=35 where J1 ran with 0
(the review's M2).

The hook's `hop: bot N` is the n-th AI record in play at the join: with nobody dead before it, bot N = record N =
Squad#0(N+1) (B1 printed 1 2 3 4 5 7 with record 6 dead: the numbers are the records).

### 6.1 K0 FIRST: lanes or one file? (police -> crew at the floor)

`K0_DM09_lanes_floor.ini` = K1 with `[Balance] CopToCrew=0.01` (the floor: `Risk=2` takes the larger of the dial and
stock). The human walks the tower as in run J1 (nobody is shot: most bots stand at a gate with the wait ARMED at the
join), takes the lift at about GO+110 and stands in the lift car for 200 s; `[Bots] Escort=0 BoardAll=0 FollowOut=0`:
nothing of the hook touches the crew.
WHY FIRST: with the owner's balance (CopToCrew 0.05) the old chain's five were all dead +40.4..49.4 s after the join
(J0), while the first far-side bot is west of the road's middle only from +54 s (at 150 units / s: +68 s) and the
first X bot from +70 s: a run in which they die as
in J0 reads '0 west of -3000' exactly like a run without lanes. At the floor the bots live, and this one run decides
**lanes or one file**, shows the clock, the slit and the bollard gaps, bus #10, and how fast an `eDMS_NotSet` bot walks
the street (the number `V_SLOW` stands in for).

Read `python <scratch>\K\today.py <log> <z_lanes\retomoto_full>` (per bot: where it stood at the join, when it
stopped advancing, how far west and north it got; per place line the band) and the pictures (`K\logs.py <log> --json
x.json`, `K\maps.py geo.json <out> --logs x.json`). Said beforehand (times by the walk model, scratch `K2\when.py`:
at 300 units / s, in brackets at 150):

| read | lanes build, good | J1 (the control: the gates build, one file) |
|---|---|---|
| **the clock**: a bot that does not ADVANCE (no place line west of its westernmost so far) from before +35 s to +60 s, while it lives | none | 6 of 7 (they move among the planters, x 350..3400, and go nowhere) |
| bots alive at **+50 s** whose place line then is west of the door (x < 2500) | all of them (every way is west of the door by +25..36 s) | 4 of the 6 alive at +47 and +52 s (bots 3 and 4 are at x 2650..3400 and stay there) |
| **the spread**: bots west of the road's middle (x < -3000) | record 3 (W) from +54 s [+68] to +117 s [+162]; record 1 (X, through the slit at z 1440) from +80 s [+102] to +106 s [+140] - both in EVERY round; records 2, 5, 6, 7 by the draw (W ways from +54..67 s [68..85], X ways from +70..81 s [89..102]): 4..6 of seven in all | 0 at all 104 lines; J0 and B1: 0 of 112 |
| ... and east of x -1500 north of z -3000 while those are west | record 4 (E) in every round; records 2, 6 by the draw: 1..3 | - |
| **the lane of each bot** by its x: north of z -2000, E = -1500..-500; X = -2800..-1500 south of z 1440 and -4900..-3200 north of it; W = -5700..-3600 | records 1 X, 3 W, 4 E in every run; 2 E or X, 5 X or W, 6 W or E, 7 X or W | all in -2100..-500 |
| the band's width (most eastern x - most western x of the bots on the road) at +90 s | 2,500..4,700 | 380 (J0 at +40 s, its last line with five alive) |
| **a hold**: two place lines of a bot 5 s apart within 2 m, within 3 m of a hold of its lane (table 3.5) | 2..6 a bot (he stands 4.4..6 s at each when he walks 300; a place line every 5 s catches about every second hold) | - |
| **the walking speed** between two holds (place lines 5 s apart, both moving) | says whether 150 was the right floor; under about 110 the clock of 3.2 does not hold | 124..127 median in the tower |
| `heist stage 2 -> 3` | E squads from about +120 s [+160], the last W squad by about +150 s [+210: after the script's 200 s] | none |
| run it twice: the lanes of records 2, 5, 6, 7 | differ (the same deal twice: 1 in 16). NOT SHOWN so far: that a RandomTrigger of a build of ours comes out two ways in two rounds (the review's N3) | - |

Failure signs, and what each means: a bot that stops advancing inside the lobby or at the door after +35 s = the
clock does not order it on (the 10 m of 3.2 are wrong, a started step does not take the place of the tower's, or he
walks slower than 110); a bot standing at the median's slit (-2960, 1440) or at a bollard gap ((-3000, 5300),
(-3000, 6480), (-3000, 6920)) = the game does not walk a gap the mesh has (the slit: `Walk.NARROW_MIN` 36 and a
rebuild); a bot standing at a bus (#18 x -1700 z -1210..-70, #14 z 2000, #15, #07, #10) = a leg the game walks
otherwise than straight; place lines at z 8900..10100 that cut bus #10's north-east corner = a way place is taken
from 10 m (3.6); several bots of one lane dead at one hold = that hold (say which: the table has its x, z).

### 6.2 K1: who lives? (the owner's balance)

`K1_DM09_lanes_stand.ini`: the same script with `CopToCrew=0.05` (the owner's, and J0's / J1's). Read as K0, with
every row 'if alive'; its own question is the last column of J0 against it: of the old chain's five, none lived
past +49.4 s; how many of seven are alive at +60, +90, +120 s, in which lane and where do the others die (`lost ..
DOWN` lines with the place: `[Bots] Log=2`). A lane whose bots die at one hold in two runs wants that hold moved.

### 6.3 K2: a human who walks one side, the hook's parts on

`K2_DM09_lanes_walk_E.ini`: the whole map on Squad#05's places - the tower, the lift, then **walking, not sprinting,
lane E** to the van, and aboard; `[Bots] Escort=1 BoardAll=1 FollowOut=1` as in the owner's ini and
**`FollowOutHold=15`**, which his ini does not have and which has never run. It shows what K0 / K1 cannot: the far lanes
beside a human who is on the near one; `FollowOut` calling them when he has stage 3 (`follow: .. THE CREW IS CALLED`,
per bot `.. m from the boarding place`); a called bot bent back to a lane hold (`follow: record N sent .. order 2:
something had moved its place`); whether the hold of the van's wait gets them aboard (`follow:` lines of the hold,
`aboard`, `LEFT BEHIND`); and the way round bus #10 walked by a human (B1 stuck at the bus's south end on the old
places; `script NNN: goto is stuck` there again = the new way does not clear it). kl_playtest says of this script:
3 steered lines off the mesh and 1 goto 'behind him after a stop' in the rig's model (the `.route.txt` names
them): look at those gotos first when a leg fails.

### 6.4 Then

`retomoto_full` is the build for the owner's tab if K0 shows lanes and K1 shows them alive longer than J0's
five; with it `[Bots] FollowOutHold=15` if K2 shows it working. `retomoto_full_r` adds the tower's forks and is one
more unknown (it has never been his tab's build).

## 7. ASSUMED and GUESS, in one place

- GUESS: the three lanes' lines, the deal, the bays and ramps; every number of the section (`JOIN_SAFE` is the
  tower's 30 s + 1; `CALL_REACH` 600; `V_SLOW` 150 from the tower's median of 124..127 with fights and stairs and a
  free bot's 370; V_PLAN 300 from 240..440 measured with sprint; `POST_KEEP_ST` 400, `POST_WALL` 200 = point-blank
  160 + a grid cell; the stands of 1..2.5 s; that 35..170 from a box's edge is where a bot uses it).
- THE WALK MODEL is a model: straight lines at one speed, 'reached' 10 m from a step's last place, a way place
  touched. Every time in this note comes from it.
- ASSUMED: a step is reached at once when its place is within 10 m, and the bot still goes to the place; a newly
  started step takes the place of the running one - both the game's own doing in the tower, the second now also
  MEASURED in its effect (1.3); that the game's pathfinder walks a straight line where the mesh has one, and walks
  the gaps the mesh has (the median's slit of 0.9 m, the bollards' 1.1 m).
- ASSUMED: a man of the police is at or near a place his squad is posted at or sent to - and nowhere else worth a
  wall. Where the police really stand when a lane comes by is not known (they are woken 40..80 s before the far
  lanes pass and fight); the walls keep the ways off the 124 known places, no more.
- ASSUMED: the cover boxes of the parked taxis and the kerb things are covers in the game as the planters' walls
  are (seen: J1). A bus's END boxes are used by X and W; `kl_fa_bots_dyn.check` would measure them from an origin
  9 m off, and does not look at the lanes' holds (they are route-form steps).
- NOT KNOWN: the speed of a step that is `eDMS_NotSet` on the street; what the squad's modifier is when the street
  chain starts (leashed and tight if it stood at the tower car, nothing if it was taken from a gate) and what that
  does to a hold; with the dynamic step on top the opening modifier (loose, vision x 2) is still on in the street;
  whether a way place of a step is touched or taken from 10 m; whether the draw differs between rounds.
- The check's 'straight line on the mesh', 'no hold at a post' and 'no leg at a post' are this module's reading;
  nothing reads the collision or a line of fire, and the game lays its own path between two places.

## 8. Not done

- No run. No commit.
- The far pavement and the foot bridge are no lane; the two southern bays of the square are not used; no way uses
  the median's gap at z 0.
- No gate (`TriggerActorsDead`) on the street: the waves fall back to the van by design (re/retomoto_bots_rooms.md
  9.2); a lane's wait is a timer.
- The lanes do not wait for one another: an E squad is at the rally 10..30 s before a W squad and calls the van.
  One rally wait for all would need a counter between two steps, which three checks do not walk.
- A lane's draw is made once, at the timed way's end; a bot does not change sides on the way. A lane cannot be
  dealt by who is alive (3.4).
- E has four holds and 57 m without one (no cover box on the east pavement between z -100 and 5400): the lane that
  'stays on this side' is the open one. More cover there is `kl_fa_cover`'s / `kl_fa_street`'s to give.
- The first street place is one point for the squads of a ramp (3.2, the review's N5).
- The old chain (`--no-lanes`) keeps its fault at bus #10 and its sprint; it is there to rebuild z_rooms, not to use.
- `kl_fa_street`'s parked vehicles still have no hole in the mesh: the police's ways and the hook's orders
  (`FollowOut`: 'sent to the boarding place') are laid by the game over them. A hole belongs in `kl_fa_street` /
  the mesh, not here.
- `kl_fa_bots_dyn.check`'s own NOTE 'THE JOIN' still says 'not established': that text is that module's.
- The ten planted faults of the first form were run again with the tool as it is, and five new ones (5.4); the
  27 pictures: the eight `*_2_lanes*` and the by-squad overview were made anew, the others are the first form's.

## 9. The review and what was done about it (`re/retomoto_bots_street_review.md`: ACCEPT WITH FIXES)

Each point was checked again before it was acted on - by the tool's new check rules run on the FIRST form's build
(`round1\rt_check_with_the_fixed_tool.log`: 129 FAIL) - and none was refuted.

| point | checked again | what was done |
|---|---|---|
| **M1** the ways pass police posts at point-blank range; no rule looks at a leg | HOLDS: the new rule g on the first build: 25 legs within 195 of a post, the nearest 8 - the review's own sampler said 25 passes within 160, the nearest 8 | every post is a wall for the ways (`wall_posts`, `Walk` walls, `straight_clear`), rule g, planted fault `leg_at_post`. The build: nearest leg 262; the review's sampler: 0 within 160 |
| **M2** K1 is not J1's twin and cannot tell 'no spread' from 'dead' | HOLDS (the ini: Tune=1, Backstab=35; J1's log line: Tune=0, Backstab=0%) | scripts made anew: `Tune=0 Backstab=0` in all; **K0** (CopToCrew=0.01) first; the table reads the door at +50 s and says 'does not advance'; 200 s after the join |
| **S1** 'holds of 5-9 s' are stops of 1.7..5.7 s, none at a slow walk | HOLDS (the model on the first build: stands 1.0..5.7 s at 300, 0.0..2.4 at 150) | a hold's timer = the stand + the walk in at 150 by the walk model, per hold; rule c twice (the timer's floor; the stand by the model); planted fault `short_stand` |
| **S2** the clock is tight only from 250 units / s | HOLDS, to the decimal (3.1 / 6.4 / 4.5 / 3.2 / 10.2 / 4.9 / 10.2 s without a pending timer at 150) | the clock runs at `V_SLOW` 150, `CALL_REACH` 600; rule a by the model at 150; planted fault `fast_clock`. 0 s at 120..400 |
| **S3** #08 on E: one hold in 135 m, first in every wake box, alone | HOLDS (1 hold; at the rally at +79 s) | #08 draws X or W; rule b: 3 holds a way at least; planted fault `lone_walker` |
| **S4** FollowOut orders only during the drive-in; more are left behind | HOLDS (`klescort.c` read again) | no change in the build (the hook is not this track's). Said in 3.7 and 0; K2 runs with `FollowOutHold=15`; the lead is told that the tab wants that key with this build. The fix round made the lanes 10..30 s SLOWER, which makes this worse |
| **S5** one bot a box is not kept by box | HOLDS (five boxes over their room on the first build, one sign with three squads) | a hold place belongs to its nearest box; rule d by box; planted fault `crowd_box` |
| **S6** 'no lane empty' holds with seven alive only | HOLDS (now 2 / 2 / 4 of 16 for X / W / E) | said in 3.4 and in `DEAL`'s comment; not solvable in level data |
| **S7** the pace table counts the walk in twice | HOLDS (the model on the first build: 79..104 / 98..116 / 109..129) | every time in the plan, the check and this note is the walk model's |
| **N1** REF labels, .oct, .prm | HOLDS | 5.3 names them; the chain runs the review's `tower3.py` and `memdiff.py` beside `tower_same.py` |
| **N2** is a way place touched? | not answered by anybody | said in 3.6 and 6.1 (a failure sign) |
| **N3** does the draw differ between rounds? | not answered | 6.1: run it twice |
| **N4** the police are woken on the first lane's clock | HOLDS; with the new ways later (+40 / +54 / +78 s) | 3.7; it is why the ways keep off the posts |
| **N5** one first place for four squads | HOLDS | left; said in 3.2 and 8 |
| **N6** a leg 7 from a mesh edge | HOLDS for the first form | not ruled: the game lays its own path; the hold rule (35) stands |
| **N7** other people's files in the tree | - | nothing of theirs was touched; nothing committed |

Found beside the review: no way of either form uses the median's gap at z 0 - the X ways cross at the slit or round
the median's end (3.3); a leg with more than 18 way places raised an IndexError in `lanes_plan` (step names
`.._waya` .. `.._wayf`; now to `z`) - met by the planted fault `on_post`, not by a build.
