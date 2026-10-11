# Review of track K: Retomoto, the run to the car in lanes

**Verdict: ACCEPT WITH FIXES.**

Adversarial review, 2026-10-11 afternoon. OFFLINE: nothing was run in the game, no tool or source file was changed,
nothing committed. Reviewed: `re/retomoto_bots_street.md`, the uncommitted diff of `tools/kl_fa_bots_rt.py` /
`tools/kl_fa_bots_dyn.py`, the builds `<work>\build\z_lanes\retomoto_full` (sha1 858f830e84e9) and `retomoto_full_r`
(0188b5a2a673), the live scripts in `z_lanes\live\`, the logs `<work>\build\klhook\live\J0_ / J1_ / B1_DM09_*.log`.
My scripts and their outputs: scratchpad `Krev\` (`lanes_rev.py`, `lanes_rev2.py`, `lanes_rev3.py`, `tower3.py`,
`today_rev.py`, `cj.py`, `speed.py`, `recheck.sh`; outputs `lanes_rev_full.txt`, `lanes_rev2.txt`, `lanes_rev3.txt`,
`checks_retomoto_full\`, `checks_retomoto_full_r\`). They read the build's nodes themselves (controllers decoded with
`kl_fa.value`, places from `kl_fa_bots.Built.at`); none of them calls `lanes_plan`, `lanes_of` or `check()`.

Words: **READ** = in the file / log line named; **MEASURED** = counted by my own script on the build or the logs;
**REASONED** = follows from READ / MEASURED facts and an assumption that is named; **NOT SHOWN** = no evidence either way.

What stands: every check reproduces, the tower half is the same, the lanes are in the build as the note describes
them, and the reading of runs J0 / J1 / B1 is right. What does not stand as reported: the ways run through the
police's own cover points at arm's length, the 'holds of 5-9 s' are stops of 1.7..5.7 s (none at a slower walk), the
clock that is to rescue a stolen bot is only tight at 250 units / s or more, and the first live check is not J1's twin
and cannot tell 'no spread' from 'dead before they could spread'.

## 1. What was re-done, and what came out

| claim of the report | my test | result |
|---|---|---|
| every check on both builds | `Krev\recheck.sh`: the eight checks on each folder, logs compared with the worker's `checks_full*\` | **the same, byte for byte, all 16 logs**; rt PASS (0 FAIL, 10 NOTE), dyn PASS (4 / 6 NOTE), impact 0, guns 0, talk FAIL 1 (the known countdown line), Bain 0, sizes = z_rooms', street report = z_rooms' (I made z_rooms' report anew and compared). The build folders are unchanged by the checks (sha1 of every file before / after). MEASURED |
| the tower is z_rooms' node for node | `Krev\tower3.py`: nodes aligned by full path; raw `.prp` tokens of the properties and of every controller with key indices spelled out (opcodes 0c, 0e, 0f), class, child count, and of the scene record name, type id, flags, group, model, rotation, translation, raw block, aux, REF label, list key, light links | **holds, with one thing the worker's script does not look at** (N1): 26,004 common nodes in the same order; 98 nodes only in z_rooms, 606 only in z_lanes, every one of them a squad's node named 050..099; of the common nodes outside the street chain NONE differs in name, class, properties, controllers, rotation, translation, flags, group, model, raw, aux or links. `_r` against z_rooms' `_r`: the same (295 tower-kind nodes). The only node outside the squads that names a street node is `Specials!JumpPoints!06_Exit`, seven times `..\050_DefendBehaviour_street`, in both. MEASURED |
| other members | `Krev\tower_bytes.py`, `memdiff.py` | of 30 archive members 25 are byte-identical (.HVK .TEX .MAT .ANM .SND .sgp .rmc .rmi .sgd .fxc, the .LOC files, the XML); .prp .gms .buf differ (the squads); **.oct is 2,800 bytes longer and .prm differs in 2,628 dwords, each by exactly +2,800** (record offsets into the .oct) - the same picture as rt_full7 -> z_rooms (+560, 2,628 dwords). Heap budget 1,188,264 in all five builds looked at. MEASURED |
| the `_r` build keeps the street chain whole | `lanes_rev2.py` E | 655 street nodes in both, same paths, same order, every node equal (class, controllers, values, place); no tower node of `_r` names a street node. MEASURED |
| 3 lanes, the deal, no lane empty | `lanes_rev.py` 1 / 4: every way through each squad's chain from the nodes | #02 X; #03 E / X; #04 W; #05 E; #06 X / W; #07 W / E; #08 E / W; four `RandomTrigger` {1, 3, 3, 0, 0, [a], [b], [], []} = stock F07 `Squad#02\060_RandomTrigger_BeforeStreet` field for field (35 of F07's draws have that pattern; read from the stock archive). 16 deals, no lane empty **with seven alive** (S6). MEASURED |
| holds on the mesh and at cover | `lanes_rev.py` 2 / 3 | 329 street places, 0 off the mesh, all in the lobby's mesh part, none within 35 of a mesh edge; 55 holds, each within 169 of a cover box's model box (median 126), none inside one. MEASURED |
| no two bots on one hold | `lanes_rev.py` 4 | least distance between two squads' holds in any deal: 113 (#03 X (-3760, 800) / #07 W (-3680, 720)). True by place; by BOX see S5. MEASURED |
| no hold at a police post | my own post list (47 start places, 44 child boxes of the squads, 35 RunToCover points = 126) | least 402. True **for the holds**; not for the ways: M1. MEASURED |
| legs clear of the parked vehicles, the van's lane, the level exit box | `lanes_rev3.py`: every leg sampled every 20 units | lane, rally and to-van legs: 0 samples off the mesh, 0 in a parked vehicle's footprint (the seven nodes stand where `kl_fa_street` put them), 0 in the level exit box before the rally step, 0 in the van's lane. (The TIMED WAY's straight lines do leave the mesh - pillars -; nothing claims they are straight.) MEASURED |
| the gates: no line changed | `git diff -U0 tools/kl_fa_bots_rt.py` | no hunk between line 280 and `street_plan` (1185); removed lines are docstring, the import line, `DEFAULTS`, the old 'THE JOIN' note, one `warp` test and the RESULT line. dyn: +30 / -2, as described. READ |
| ten planted faults | not re-run (each needs a build); `neg_tests\summary.txt` and five of the logs read | 10 of 10 as reported. READ |
| today's reading of J0 / J1 / B1 | `today_rev.py`, `cj.py` | section 2 |

## 2. Do the lanes answer what the seven really do today?

- **One side: confirmed.** 216 place lines after the join in the three runs, 0 west of x -3000; furthest west -636
  (J1), -2012 (B1), -1638 (J0). MEASURED (`today_rev.py`; the logs' `hop: bot N` lines).
- **The stolen street step: the table of the note's 1.3 reproduces to the decimal** from the `crewjoin: bot N (actor ..)
  at (..)` lines against each squad's own tower places: J1 1.9 / 4.4 / 3.1 / 8.8 / 12.6 / 0.4 m from the reception
  hold and 5.5 m from the loot place; B1 0.0 / 0.0 m from the door hold for bots 2 and 5. J1's six stop advancing by
  +16..26 s, bot 5 (12.6 m) walks on and dies at +37.7; B1's 2 and 5 stand from +11 s to BoardAll's raise at +51.3.
  MEASURED. Two limits of that evidence:
  - B1's bots 3, 4 and 7 were 5.2, 2.1 and 6.0 m from a hold and WALKED ON. The note explains it with 'the
    reception's men were dead' (a wait that fires at once is not armed). No log line says so: enemy deaths are not
    logged. The rule fits 8 of 8 bots that stopped and rests on that explanation for 3 that did not. NOT SHOWN.
  - 'stood for good' is not what J1's bots 1, 6 and 7 do: they move among the planters (bot 7: x 587, 650, 350, 750,
    1154, 1076, 976, 1137 between +26 and +77 s; three of them in a row at z -5393). They stop ADVANCING. The live
    check's wording must be 'does not advance', not 'stands' (M2).
- **The owner's round had no stolen bot** (all seven at the tower car), so his 'spread out, other side' is about the
  line itself. The lanes answer that by construction: by the walk model 32..70 % of an X / W way lies west of the
  road's middle, 0 % of an E way (`lanes_rev2.py` A). Whether a bot lives to walk it: M1, S3. NOT SHOWN.
- **Where they died today is where two of the three lanes still go.** J0's five died on the east kerb z -4200..-150:
  E's first two or three holds lie there ((-600, -3800), (-1000, -4320), (-1280, -840), (-1400, -320), (-1240, -1880)).
  B1's records 3 and 4 died among the east carriageway's taxis at (-1903, -2537) and (-2092, -3153): X's second
  hold is at (-2000, -2280) / (-2360, -1640) / (-2360, -1480). READ (the note's own tables) + MEASURED (the logs).

## 3. MUST

### M1 - the ways pass within point-blank range of the police's cover points; no rule looks at a leg and a post

`lanes_rev3.py`, last table: each way from the timed way to the rally sampled every 20 units against the 126 posts,
with the time the bot passes (walk model, 300 units / s) and the time the post's squad is woken (the first bot of any
way inside a trigger box that names the squad: `tbExitLoot` and `tbReleaseDog` both at +34 s, by the first E bot).
**25 passes within 160 units, 11 within 80.** The ones that matter (RunToCover points = where an F07 squad is sent
first; a road-block man's start place):

| way | from the post | post | the bot passes | its squad awake since |
|---|---|---|---|---|
| #02 X (record 1, EVERY round) | 57 | `020_FinancialAlley_LeftFurther` RunToCover #01 (-2097, -2671) | +46 s | +34 s |
| #02 X (every round) | 54 | `020_FinancialAlley_RightPlatform` RunToCover #01 (-2350, -969) | +54 s | +34 s |
| #03 X | 36 | `LeftFurther` RunToCover #01 | +48 s | +34 s |
| #03 X | 70 | `020_FinancialAlley_RunForDumpster` RunToCover #02 (-4023, 1774) | +72 s | +34 s |
| #03 X | 75 | `Enemies!020_Street!Squad_RoadBlock_L` START (-4318, 3839) | +83 s | +34 s |
| #06 X | 56 | `030_FinancialAlleyExit_Left` RunToCover #02 (-4502, 3919) | +91 s | +34 s |
| #08 W | 73 | `020_FinancialAlley_LeftParking` RunToCover #01 (-3686, -2826) | +57 s | +34 s |
| #06 W | 13 | `Squad_SWAT_From_Behind` START (-3889, -2251) | +64 s | +34 s (they will have left) |
| #08 E | 28 | `RightPlatform` RunToCover #01 (-906, 791) | +49 s | +34 s |
| #07 E | 61 | the same point | +74 s | +34 s |

Why it matters: `re/melee_damage.md` (READ there, kl2 0x8c62e0): a soldier whose target is within 160 units sends 100
bullets a burst step; at the owner's CopToCrew 0.05 that is 432 against a bot's 252 - the 'ONE STEP' deaths of every
Retomoto run. The note says 'a way is laid 3 m round a police post where there is room' (3.3) and the report says
'none at a police post'; that is true of the 55 holds (least 402) and of nothing else. `check()` rule 3b c tests
holds only (`tools/kl_fa_bots_rt.py` line 2869); the planted fault `on_post` moved HOLDS. Whether a man stands on his
RunToCover point 12..60 s after his squad woke is NOT SHOWN - but that is what the point is for.
MEASURED (the distances, the times by the model); REASONED (the consequence).
Fix: a check rule 'no leg of a lane within 200 of a RunToCover point or of a start place of a squad that is awake
when the bot passes and does not move off (the road blocks)', the ways laid again (the `Walk.DANGER` cost is a
preference, it must be a wall for those points), and a planted fault for it. Before the build goes on the owner's tab.

### M2 - the first live check is not J1's twin and cannot tell 'no spread' from 'dead'

- `z_lanes\live\K1_DM09_lanes_stand.ini` against `z_rooms\live\J1_DM09_join.ini` (diff of the two files; READ):
  K1 adds `[Bots] Tune=1` and `Backstab=35` (lines 47-48); J1 ran with `Tune=0 .. Backstab=0%` (its log, line 12).
  A backstabber leaves his route. Also CrewToYou / CopToYou 0.001 against 0.02 (harmless). The note's 6.1 calls K1
  'J1 line for line up to the join'.
- With K1's balance (Risk=2, CopToCrew=0.05 - J0's and J1's) the old chain's five were ALL dead +40.4..49.4 s after
  the join (J0, MEASURED), on the kerb the E lane holds at and 10 m from the X lane's first holds. The first W bot
  is west of x -3000 at about +50 s, the first X bot at about +60 s (walk model). K1's evidence window is +60..110 s
  and every row of its table says 'if alive'. A run in which they die as in J0 shows nothing about lanes, and a
  lead who reads '0 west of -3000' cannot tell which of the two happened.
- The first row ('alive at +40 s -> x < 600: all') is set for 300 units / s: the timed way's last places are at
  x 480..1200 at +31 s (#03 1120, #04 1040, #05 1200, #06 1080, #07 1000), and the speed of an `eDMS_NotSet` step is
  not known (S2). A healthy run can fail that row.
- 'stopped for good' / 'standing' must read 'does not advance' (section 2).
Fix (ini and text only, no build): K1 with `Tune=0`, `Backstab=0`; a run BEFORE it with police -> crew at the floor
(`CopToCrew=0.01`; `Risk=2` takes the larger of the dial and stock: CLAUDE.md, the bot health log entry) so that the
lanes' geometry shows whatever the police do - that run alone decides 'lanes or one file' (per bot: its x band north
of z -2000, against J1's -2100..-500); then K1 at 0.05 for who lives; the first row read at +50 s.
Can the place lines tell lanes from one file at all? Yes: records 1 (X) and 3 (W) are west of x -3000 in every
round by the build, record 4 (E) never, and J0 / J1 / B1 have 0 of 216 lines there. The hook's 'bot N' is the record
(B1 prints 1 2 3 4 5 7), so the bot -> squad -> lane table of the note can be applied. MEASURED / READ.

## 4. SHOULD

### S1 - 'holds of 5..9 s' are timers; by the note's own model the bot stands 1.7..5.7 s, and not at all at a slower walk

A hold's timer starts when the step is 'reached', 10 m (3D) before the place (the note's 3.2, kl2 0x686c4c). Walk
model at 300 units / s (`lanes_rev.py` 5): seconds the bot is bodily at the hold before the next step starts -
#02 X (every round) **1.7** each, 1.0 the last; #08 W 1.7; #03 X 2.3..2.7; #04 W 2.5..2.7; #06 3.6..3.7; #07 W
2.8..3.7; #03 / #05 E 4.3..4.7; #07 E 5.6..5.7. The report's summary says 'six per squad and lane, each at a cover box,
5-9 s'; the note's 3.7 does say 'about 3 s of each are the walk in'. At 200 units / s a 5 s timer fires as the bot
arrives; at 150 before he is there, and the next step turns him away: no hold. In that case the lanes are a walk
past covers - which still spreads them, but is not the leap-frog asked for, and the survival guess rests on it.
MEASURED (timers, distances) + REASONED (the model is the note's own).
Fix: timer = the stand wanted + 1000 / the slowest speed planned for; a check rule for it.

### S2 - the clock is tight only from 250 units / s; the measured pace of `eDMS_NotSet` steps is lower

The note: 'for a bot on its way a timer is pending all the time'. A started step is 'reached' at once only when the
bot is within 10 m of its place, i.e. within 2.2 m of the place before for a bound of 7.8 m. Simulated on the
build's own places and timers (`lanes_rev.py` 5), seconds of the timed way during which NO timer is pending (a wait
of the tower that fires then leaves the bot without a street order for good, as before):

| walking speed | #02 | #03 | #04 | #05 | #06 | #07 | #08 |
|---|---|---|---|---|---|---|---|
| 300, 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 250 | 0 | 0 | 0 | 0 | 0.2 | 0 | 0 |
| 200 | 0 | 1.0 | 0.5 | 0 | 3.9 | 0 | 2.5 |
| 150 | 3.1 | 6.4 | 4.5 | 3.2 | 10.2 | 4.9 | 10.2 |

`V_PLAN` 300 was measured on the OLD chain's `eDMS_Sprint` steps; the lanes are `eDMS_NotSet`. Displacement over
5 s of the gates build's bots in the tower (`eDMS_NotSet`, fights and stairs included; `speed.py` on the J1 / B1
place lines before the join): median 124 / 127, 75 % under 207 / 161, 90 % under 247 / 259, top 366 / 368 units / s.
So a free bot does about 3.7 m / s and a bot under fire - the square has `Squad_InFront` and `Squad_Teargasguys`
awake from +6 s - much less. MEASURED; what the pace on the square will be is NOT SHOWN.
Fix: `CALL_REACH` about 500 (a lag of 5 m is then covered), or the check's clock rule run at 150..200 as well. Also
`JOIN_SAFE` counts from the join but the clock from the first step's 'reached' (up to 212 units of walk later, the
check's own NOTE): that errs on the safe side.

### S3 - #08 drawn E (one round in two) is J1's record 5 again

Its E way has ONE hold, (-600, 6160), 56 m and more of pavement without a stop before it (`lanes_rev.py` 5: 'legs
between holds 56 m'; the note's table: 1 x 7 s, 3 stretches without cover). It is the first bot in `tbExitLoot` /
`tbReleaseDog` (+34 s) and `tbEscapeAI` (+51 s), at the rally at +76 s alone, and passes 28 units from a RunToCover
point (M1). J1's record 5 walked that pavement alone: dead at +37.7 s with 45 hits. MEASURED + READ.
Fix: #08's E way with the holds the other E squads have, or #08 dealt X / W.

### S4 - FollowOut and BoardAll against a bot in a lane (the hook's source read; nothing run)

- `klhook/klescort.c` 160-173, 898-925 (READ): FollowOut gives the stage byte once and ORDERS only while the vehicle
  drives in (state 1 / 2) with 2 s or more to go, renewed when the defend place has moved over 6 m, at most every
  `FollowOutEvery` = 2 s. While the vehicle waits the hook orders nothing (the board tactic has the stage-3 bot);
  between two visits (about 20 of every 29.5 s) nothing either. The note's 'FollowOut repeats its own every 2 s' is
  true for the drive-in only.
- A lane step that was running 'waits for its man' (klescort.c 172): a called bot that comes within 10 m of that
  hold on his way north starts its timer, and 5..9 s later the next lane step orders him to the next hold; outside a
  drive-in nothing answers. Every lane leads north to the same rally, so this bends his way rather than turning him
  round - except X before z 0 and W before z 6700, whose next holds are on the far side of the median / bollards
  from the boarding place. REASONED; K2 would show it as `follow: record N sent .. order 2: something had moved its
  place`.
- **More are left behind than before for a human who takes one to two minutes.** FO_J1 (CLAUDE.md, live): 15 s from
  the call to the departure, bots at about 3 m / s, 3 of 7 aboard from 52..83 m. With the lanes a human who has stage 3
  at +44 s (B1's sprint) finds all seven 170 m and more back (they leave the square at +31..45 s); one at +90 s finds
  the X and W bots still 60..150 m of lane away (rally by the walk model: E +76..100, X +95..113, W +106..126). The
  rules shoot whoever is in play when the van leaves with him (`re/bots_follow_out.md`). `FollowOutHold` and
  `FollowOutSpare` are off in the owner's ini. REASONED from MEASURED numbers.
  Fix: say it to the lead; the lanes build wants `FollowOutHold=15` (queued as FO2_J2, never run) on the tab with it.
- BoardAll (klescort.c: 15 s without 1 m of movement, stage 1 / 2, once somebody has called the vehicle): a lane
  hold keeps a bot 1.7..5.7 s (S1), the rally 10 s at most: a healthy lane bot is never 'held'. A stuck one (the
  clock failed, a gap he cannot pass) is raised once an E bot has called the van - from about +90 s. No conflict
  found. REASONED.
- The first E bot in the level exit box calls the van and, with the human elsewhere, boards and ESCAPES at that
  visit (stock; runs I1..I4): a slow human does not 'find the E squads at the van' (note 3.7), he finds them gone.
  READ (CLAUDE.md, run K1 of 2026-10-10).

### S5 - one bot a box: three at a sign of 1.7 m in the same seconds

By the model box nearest to each hold (`lanes_rev2.py` B): `CoverBoxH_Sign02` (173 x 140 at (-1030, -4188)) holds
#02 X (-800, -4120) at +38..39 s, #05 E (-1000, -4320) at +39..43 s - both in EVERY round - and #03 X (-1160, -4120)
at +39..42 s when drawn; they stand on its east, south and west sides, so one of them is on the road's side.
`CoverBoxM_05` (190 x 100 at (-2595, -6095)): #06 W and #08 W, +42..47 s. The note's rule is one bot a box under 2 m.
Nine boxes take two or three squads in all; the other seven at different times or with 2 m and more. MEASURED.
(My attribution is the nearest model box; the plan may have meant a neighbour. The check's rule d is 100 between
places, which these pass.)

### S6 - 'no lane can come up empty' holds with seven alive

With the squad that always takes a lane dead before the join: record 1 dead -> X empty in 4 of 16 deals; record 3 ->
W empty in 2 of 16; record 4 -> E in 2 of 16 (`lanes_rev.py` 4). Bots do die in the tower (B1: one; J0: two; G1 /
G2 idle: six). Say it in the note; or deal by who is alive (not possible in level data) / give X a second fixed
squad. MEASURED.

### S7 - the note's pace table counts the walk-in twice

'At the rally' by the walk model: E 76..100 s, X 95..113 s, W 106..126 s after the join; the note and the report say
83..117 / 121..137 / 130..158 (the timers added whole to the walk). The live check's 'heist stage 2 -> 3 from
about +100 s' should read 'from about +90 s' (first E bot in the exit box +89 s). MEASURED on the build's numbers.

## 5. NOTE

- **N1 - REF labels.** `K\tower_same.py` compares flags, group, model, rotation, translation, aux and 'has links';
  not the record's REF label (+0x30), raw block or type id. Mine did: 168 tower nodes and 21 squad / actor nodes
  have another REF label (e.g. `Squad#03` 35520 -> 35582: the labels follow the node count before them), nothing
  else. REF labels are used by gates, neighbour lists, the surface table and .HVK placements (CLAUDE.md); the .HVK
  is byte-identical and no squad node is a room. Every bots step has done this. The note's 5.3 'node for node ..
  all equal' should name it, and the .oct / .prm lines of section 1 with it ('sizes equal' is true, 'bytes equal'
  is not).
- **N2 - what a way place is.** The plan's legs are straight lines between places; a step is 'reached' 10 m before
  its LAST place by the note's reading. Whether a WAY place of a step of two or three places must be touched, or is
  also taken from 10 m, was not read by anybody. If from 10 m, corners are cut: the six turning points round bus #10
  (four of them within 10 m of the next) then give a line that crosses the bus's north-east corner by about 16
  units at z 10000 (my arithmetic on the note's table 3.5; REASONED), and the detours round posts shrink likewise.
  K2's scripted human does not answer this (the rig's `goto` has its own radius); a bot's place lines at z 8900..10100
  in K1 do. NOT SHOWN.
- **N3 - does the draw differ from round to round?** The form is stock's. That a `RandomTrigger` of a build of ours
  has ever come out two ways in two rounds is not in any log I found (the dynamic step's forks were never read back
  from place lines). K1 'run it twice' covers it; until then NOT SHOWN.
- **N4 - the police are woken on the E lane's clock.** `tbExitLoot` (9 squads) and `tbReleaseDog` (11) at +34 s by
  the first E bot, `tbEscapeAI` at +51 s (+62 without #08 on E); the X and W bots walk into squads that have had
  12..60 s to take their cover points. No lane enters a wake box earlier than the old chain did (its bots were on
  the kerb at +24..35 s, J0); nothing is tripped 'early', but nothing is later either: the far side is not asleep
  when the far lanes arrive. MEASURED (`lanes_rev.py` 6).
- **N5 - the first street place is one point for four squads** ((5600, 160, -7162): #02 #04 #06 #07; (5600, 160,
  -6239): #03 #05 #08). The stagger timers (0.5..5.5 s) start when that step is reached, which for a [CrewJoin]
  place within 10 m of it is the join itself: up to four bots are sent to the same point and wait there for 1..5 s.
  Short; the game spreads men who share a defend place (J1's row behind the planter wall). MEASURED + REASONED.
- **N6 - least clearance of a leg**: 7 units from a mesh edge at (-3691, 846) (#03 X), 16..19 on five other ways. The
  check asks 35 of holds only. The game's pathfinder lays the path itself. MEASURED.
- **N7 - `.claude/workflows/retomoto-level-design.js`, `re/bank_campaign.md`, `tools/kl_chars.py` are modified in
  the tree and are not this track's** (git status); commit `tools/kl_fa_bots_rt.py`, `tools/kl_fa_bots_dyn.py`,
  `re/retomoto_bots_street.md` and this file by name.
- **N8 - not looked at**: K2's script beyond its header; the 27 maps; whether a hold is on the box's side away from
  the police (the plan's 'preferably'); the ten planted-fault builds themselves.

## 6. What I would do next, in order

1. M2: the two ini edits and the floor-damage run first (`K0`: K1 with `CopToCrew=0.01`, `Tune=0`, `Backstab=0`) on
   the build AS IT IS - it shows lanes or no lanes, the clock (do J1's six advance now?), the gaps at z 0 / 4900 /
   6700, bus #10, and how fast an `eDMS_NotSet` bot walks the street (S2's open number).
2. With that speed: M1, S1, S2, S3 in one rebuild (posts as walls for the ways, hold timers, `CALL_REACH`, #08's E
   way), the planted faults for the new rules, the chain and `tower3.py` again.
3. K1 at the owner's balance, K2 with `FollowOutHold=15`; then his tab.
