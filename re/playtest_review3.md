# Review of track H3 (the scripted player, third round) - adversarial, offline

**Verdict: ACCEPT WITH FIXES.** One MUST (the `[Balance]` block of the eight `--fed-walk` scripts does the opposite
of what their `.expect.txt` says), five SHOULD, the rest holds under re-measurement.

Reviewed 2026-10-11, OFFLINE: no game started, nothing written in the game folder, no tool or source file changed,
nothing committed. What was looked at: `tools/kl_playtest.py` (working tree), `re/playtest.md` section 10, the twelve
scripts and the patch text in `<work>\research\playtest\v3\`, the logs in `<work>\build\klhook\live\`, the five
builds of `<work>\build\w_tabM`, `klhook/klauto.c`, `klhook/klbalance.c`. My own check scripts (none uses the tool's
`starts` / `danger` / `fed` / `judge` code; they do use its build loader and `kl_escape.Walk`, an older file the
worker did not touch) are in the session scratchpad `rev3\`: `parse.py`, `starts.py`, `stops.py`, `legs.py`,
`doors.py`, `corner.py`.

NOT checked by me: that (1386, 48, -316) of `H3_DM03_van_clear` lies inside the level exit box (I could not read the
box's size); the `danger` table's R2 counts; the mesh-way lengths; anything that needs the game.

---

## MUST

### M1. The fed scripts' balance keys: after the switch a heister's bullet costs the fed x 20 and the crew is unprotected

Files: `v3\H3_DM01_die_fed.ini`, `H3_DM02_die_fed.ini`, `H3_DM03_die_fed.ini`, `H3_DM06_die_fed.ini`,
`H3_DM09_die_fed_g1/_g2/_g3.ini` - each `[Balance]` is `FedMirror=0`, `PlayerHealth=0.05`, `CopToYou=20`, `Ramp=0`,
`Risk=2`, `CopToCrew=0.005` (lines 81 - 89 of each). Source: `tools/kl_playtest.py` 3126 - 3131 and the text at 3159
('CopToCrew=0.005 (the crew is to live)'); `re/playtest.md` 10.4 last paragraphs and 10.7.

`klhook/klbalance.c` 284 - 285: `klr_mir[] = { 1, 0, 4, 5, 2, 3 }` - 'a police player reads the OTHER float of each
pair: slot k then holds the meaning of key klr_mir[k]'; section a3 of its head comment (lines 112 - 131) says the same
and gives the live case (PT_DM03_die_r2). With `FedMirror=0` nothing is exchanged, so from the tick he is police:

| slot (the ini key that fills it) | value in these scripts | what a police player's game reads it as |
|---|---|---|
| +0x00 `CopToCrew` | 0.005 | a heister's bullet on a police AI: x 0.005 |
| +0x04 `CrewToCop` | 1.0 (Risk=2) | a police AI's bullet on a heister: **x 1.0 - the crew is NOT protected** |
| +0x08 `CopToYou` | **20** | **a heister's bullet on the fed: x 20** (about 47 a bullet at Risk=2 -> 940 against his 550) |
| +0x10 `CrewToYou` | 1.0 | a police AI's bullet on the fed |

So the key the script sets 'so that the crew lives' is the one that makes the crew harmless, the crew dies as in
PT_DM03_die_r2 (all seven dead 15 .. 47 s after the switch, at 0.05; here ten times weaker), and should the fed meet
a living heister - which is where `H3_DM03_die_fed` sends him, the crew's loot place - the first bullet is his second
death and the round is over. The run then shows neither 'the crew lives' nor a clean walk, and its `.expect.txt`
names the wrong cause. The 45 s 'unhurt' of r2 is no evidence for the keys: nobody shot at him in the stair room.

`H3_DM03_F3_fed_dies` (`FedMirror=1`) and `H3_DM03_F4_two_rounds` (no key = 1, `CopToCrew=0.05`) are NOT affected:
under the mirror `CopToCrew` keeps its meaning and the fed has the dial's 27.5 (live, FD3).

Fix (a reading, NOT RUN): for `--fed-walk` without `--fed-die` either
(a) stay with `FedMirror=0` and write `PlayerHealth=0.05` WITHOUT `CopToYou=20` (27.5 of health die to one bullet at
Risk=2's 1.0 as well: a Type 79 bullet is 75.6), plus `CrewToCop=0.005` beside `CopToCrew=0.005` - then a heister's
bullet costs the fed x 1.0 of 550 and the police AI's a heister x 0.005 on both sides of the switch; or
(b) `FedMirror=1` with `FedToCrew` / `CrewToYou` chosen for the walk. Either way correct the `.expect.txt` sentence
and 10.4 / 10.7 of `re/playtest.md`, and regenerate (`set3`).

---

## SHOULD

### S1. Every live death so far was ON THE WAY: on the unpatched rig the fed's part starts up to a minute late and from another place

Logs: PT_DM03_die_r2 `08:57:37.575 fed: you: status 0 -> 1` during script 52, PT_DM03_die_f2 `09:10:09.931` during
script 53 (19.1 / 20.0 s after 0x19); only FD3 reached its die place (and that was the old, nearer one). In
`H3_DM03_die_fed.ini` a death at script 53 leaves gotos 54 - 59 = 8.5 + 6.5 + 6 + 8 + 6 + 7.5 = 42.5 s of timeouts,
then the 20 s of lines 61 - 68: the fed's first goto (line 72) begins about 57 s after he appears, and for 42 s he
is pushed at the hero's way points (live: in 2 s he ran from (-4570, -3349) into the corner (-4155, 300, -3645)).
- Bank: harmless - my own flood (`corner.py`) has the straight line from (-4155, -3645) to the first fed way point
  (-4607, -3399) clear, the room is x -4870 .. -4130, z -3670 .. -3210 and convex; the worker's claim holds.
- Hot Coffee (`H3_DM01_die_fed.ini`: die place at line 57, 100 m into a map whose 13 enemies all hunt): a death at
  line 50 leaves about 60 s of pushing in a control room 8.6 m up with a landing and a catwalk. NOT SHOWN that he
  is then still where line 70's straight line starts. The park and Late Night Opening: the same, not shown.
The scripts say this in their `.expect.txt` (line 10); the report's 'up to 6 .. 8.5 s each' understates the sum.
Recommendation: apply `klauto_h3_onbody.patch` in a TEST hook (klauto.c is TEST-only) and run the fed scripts in
`--rig3` form on the four maps other than the bank; or shorten the hero's part of a `--die` script.

### S2. The park's BLIND goto: a 'reached' there proves nothing without the height

`H3_DM06_die_fed.ini` lines 85 / 87 / 89: `goto -975 -9784 100 6000`. In the plan that place lies INSIDE the fed's
own spawn row on the deck: my flood from every point has its cell at y 1549 (`legs.py`: 'in the flood of points
[1, 2, 3, 4, 5] y 1549'), 199 from points 3 and 4; the crew's mesh is 1,290 below. klauto's goto is 2-D
(`klauto.c` 1386 - 1388), so a fed who never left the deck, or came back up, 'reaches' it. The `.expect.txt` lines
19 - 21 read '"reached", or a y that FALLS ... = there IS a way': for this map 'reached' must be read only with
`pos fed-blind-N` y about 259. Same caution for Hot Coffee's (2045, 17479) (there the cell is outside the flood,
so the risk is smaller). Fix: say it in the expect text and let `judge` test the height.

### S3. Retomoto: a script fits the point the game picks in 3, 2 and 2 cases of 7

`H3_DM09_die_fed_g1 / _g2 / _g3`: the game picks the point, the script cannot. A run of `_g2` or `_g3` shows that
group's way with a chance of 2 in 7 (if the pick is uniform - how kl2 picks is track L's question, not read here);
otherwise its gotos aim 36 m or 196 m away and show only `pos fed-appeared`. The report says 'one script a group'
but not what that costs: plan on about three runs per group, or wait for `ifnear` / `jump` (in the patch text,
not used by the tool). Also: group 1's answer is partly known already - the owner's round of 12:31 has
`fed: YOU ARE A FED ... at (1804, 19601, 812)` = point 2 itself, and his words are 'in a lift'.

### S4. `H3_DM03_F4_two_rounds`: `onwin` is armed in the poll after `tap RETURN`, without the 9 s SH1 had

Lines 75 - 76 (`tap RETURN`, `onwin HeistStatusLeaderboard score2`); SH1.ini has `wait 9000` between (lines 121 -
123). If the page is still the top window when line 76 runs (80 ms and 2 frames after the key went down:
`klauto.c` 1267 - 1270, 1286), the trap fires at once, the script goes to `score2` and ends 'PASS' on round 1's
page. In SH1 the page was gone 2 ms after the key (`16:12:04.821` tap, `.823 windows: 0 []`), so it will most
likely work - but after a FED round nobody has seen this page. Put `wait 3000` before line 76; and read the run
by `session: state ... -> 0x19` appearing TWICE, not by RESULT PASS.

### S5. `H3_DM03_F3_fed_dies`: whether a heister comes while he stands is not shown

He ends at the level exit place (854, 70, -155) and stands 60 s (lines 96 - 105). The crew comes there only on its
way out; with a death about 20 s after 0x19 and a walk of about 60 - 100 s the crew may still be looting (live:
stage 3 about 80 - 95 s after GO for a HUMAN who sprints; bots later). If nobody passes in the 60 s the run shows
the walk and the drop but not F3. Stand longer (the round's clock allows it) or walk him on to the loot place.

---

## NOTE (checked, holds - or small)

- **N1. The start delay holds.** My `starts.py` on every log with a walking script: W held through the
  countdown - still on START at 10.16 .. 10.32 s, first seen off it 10.19 .. 10.84 s where a line falls close
  enough (bank K2 / K2b / K2c / die_r2 / die_f2, Retomoto N0, VAN1 .. VAN5); with the 11.0 s wait the first goto was reached in PB_DM03, FD3, FO_J0, FO_J1,
  FO_J4, PB_DM01, PB_DM06 (0.30 .. 1.33 s) and behind the 18.5 s blast wait in B1, J0, J1. The only 'NOT reached in
  9500 ms' first gotos are the six runs whose script had no wait (K1, K2, K2b, K2c, PT_DM03_die_r2, _f2). So the
  worker's correction of the task's premise is right: the SECOND version already waited, and
  `PB_DM03_board_hp.ini` IS the second version's script (`diff` of the `[Script]` sections against
  `rig2\PT_DM03_board_r2.ini`: three lines, radii / timeouts only). The position log is 2 s coarse
  (`PosLogMs=2000`): '10.16 .. 10.4' is 'last seen on START', a lower bound of the freedom, not its second.
  Late Night Opening: no log exists - not measured, as said. `FO_J3_DM03_all.log` shows the same first-goto line as
  FO_J1 (`+12.33 s ... reached in 1328 ms: at (-1734, 700, -11919)`); I did not look into why.
- **N2. The stairs.** Re-derived from `you lost` lines between the gotos' 'reached' lines: steps over 100 on the
  staircase - K2c (in motion) 3 = 455, PB 12, FO_J1 17 before script 69 was reached (all loss lines there sum to 6,357) and
  5 more = 758 after it, FO_J0 17
  then dead 0.33 s after script 67 was reached (in the wait of line 68), FO_J4 13 then dead 2.06 s after it at
  (-698, 303, -5937). The big sums fall after script 65 and 67 were reached = the two landing stops, as said.
  The SAME script lived twice (PB, FO_J1) and died twice: the stops raise the dose, they do not decide alone -
  the dial at 0.001 is what makes the route safe, not the motion. K2c also took one .45 step (759) in motion in
  the vault corridor (script 65 -> 66). `klbalance.c` 782 accepts 0.001 (0 .. 20) and Ramp=0 writes it as given;
  the hook's own lines print factors with `%.2f`, so the log will say 'police->you 0.00'.
- **N3. `H3_DM03_board` line 58** is `goto -990 -6072 40 7500 keep`; K2c's line 56 had no `keep` (W let go for a
  poll). Every other radius on the nine way points is K2c's. One untested difference, at a 50 degree turn.
- **N4. `--die` places** (`stops.py`, enemies by `kl_fa_bots_rt.enemy_squads`): 127 (Hot Coffee, FBI-Agents_01,
  SCAR), 128 (Late Night, 3rdFloorGuard_01, shotgun), 127 (bank, Guard_02, M9), 129 (park, US_Boss, AK-74), 128
  (Retomoto, Squad_Guards_Inside_01 #03, .45; that squad is NOT in the world at the load, field 3 = 0) from the
  placed post - as said. Whether the man is there is assumed, as said; with 27 of health and x 20 it hardly matters.
- **N5. The AFTER_DEATH points are where the report says**: centres by `kl_fa_fed.py plan` (another tool) agree on
  all five builds; live FD3 put him on point 2 itself. My own flood from EVERY point (`legs.py`): bank - one region
  for all seven, every leg of both fed scripts inside it up to the last (the vault's loot place, 4 of 59 samples
  off) and all of F3's legs to (854, 68, -155); Late Night - one region, the six off-mesh gotos and the mesh legs
  to (-836, 2597) inside it (the escalator legs after it are off the flood: stairs); Hot Coffee - 127 m2 at y
  860, mesh part 1; park - 129 m2 down to y 1005; Retomoto - 8 m2 (points 1 - 3), 16 m2 (4, 5), NO collision
  floor under points 6 and 7 (the cell's only floor is 20 against the points' -50). All as reported. The walk
  test ignores convex shapes and doors that move (`kl_escape.py` 375 - 380): a 'yes' is 'the static collision
  leaves a way'.
- **N6. Doors on the bank's fed way** (`doors.py`): the legs pass `SI0200_M03_Wall_Door_4m_A_13 / _14` (north-west,
  before script 77) with leaf `DoorSteelWin_A_11` 72 from the line, `Wall_Door_4m_A_12 / _11` with `DoorSteelWin_A_08`
  57 from it (script 80), `Wall_Door_4m_A_10` with `DoorSteelWin_A_04 / _03` (scripts 84 - 89), then
  `Garage_Wall_3xM_Door_03 / _02` and `DoorSteel_B_01`. All ZSTDOBJ, the same kind as the leaf that stopped him
  live in the south-east corner; the flood passes all of them, so their leaves stand open in the static collision.
  The frames are where the gotos have radius 25 at a sprint (lines 78, 80, 82): the first live run tests that.
- **N7. The scripts against klauto.c's parser** (`parse.py`, written from `klauto.c` 1145 - 1230): all twelve -
  `[Script]` keys contiguous from 1 (81 .. 205 of 640), every command known, every key name valid (ESCAPE, DOWN,
  RETURN, E), no line over 199 characters, every `goto` has numeric radius and timeout before `sprint` / `keep`,
  no `keep` goto followed by anything but a goto (or `pos` / `log` and then a goto), no key left down at the end,
  every `onwin` label exists, no section or key twice. The tool cuts `log` texts at 79 itself: two end mid-word
  (`H3_DM03_die_fed` line 69 '... police, if he die', `H3_DM03_F4_two_rounds` line 67). `set3` into a scratch
  folder reproduces all twelve byte for byte (comment lines aside); `set --rig2` on the same tree differs from
  the old rig2 set only in the first goto's timeout on M01 / M02 / M06, the bank's stairs and `--die`, and on
  Retomoto because the tree's DM09 is another build.
- **N8. The patch text** applies (`git apply --check`), and reads right: the trap frees the keys one event a
  poll as `onwin` does, a missing label ends the script as `onwin`'s does. One trap, one object: if it is still
  armed when a new round hands the human a new hero object it fires there - arm it again per round (the tool's
  `--rig3` does, per `label fed<round>`). Not compiled or run by me.
- **N9.** `judge` and `starts` run on the live logs without fault; `judge` with a `--fed-walk` ini on FD3's log
  prints the point ('0 from point 2 (group 1) ... ON THE GROUND'). Its fed-walk branch has seen no real fed-walk
  log yet.
- **N10.** Other sessions' new files (`tools/kl_fa_fedpoints.py`, `re/fed_kit.md`) may move the points or the
  body: the seven fed scripts are for the builds of `w_tabM` as they stand.

---

## What each script's first live run can and cannot show

| script | CAN show | CANNOT show (and why) |
|---|---|---|
| `H3_DM03_board` | the nine stair way points in motion with `keep` at line 58; the heist to the van at the dial 0.001 (loss lines stay visible); FollowOut on a route he survives | anything about police damage to a human; that the stairs are safe WITHOUT the dial |
| `H3_DM02_board` | the first walk of Late Night Opening at all: the start delay there (first goto, 20 s timeout), whether the intact glass doors stop him (lines 49, 92, 108, 123), the escalators, the van | which of several unknowns failed if it sticks early - expect two or three runs |
| `H3_DM03_van_clear` | the human in play, stage 3, not aboard for 90 s while the van comes and bots board | Bribe / Leave themselves (keys by `--extra`); that the stand place is in the exit box is the tool's word, not checked here |
| `H3_DM03_die_fed` | where he appears; with a death on the way, 40 s of pushing first, then whether the door frames let a fed through and how far he gets | 'the crew lives' and a fed among living heisters (M1); a walk that starts ON the point (S1) |
| `H3_DM02_die_fed` | appears on the car park's ground or not; whether a body can cross 26 m without mesh; the mall's east side | the same as above (M1, S1); the escalator legs if he is late |
| `H3_DM01_die_fed` | the height he appears at; whether he can leave the control room westward; `pos` on the stair tower's landing | a way DOWN - three blind gotos; after a long push (S1) even the first leg is not shown |
| `H3_DM06_die_fed` | the deck, the block, the FA stairs as far as y 1004 | that 'reached' on a blind goto means a way (S2) |
| `H3_DM09_die_fed_g1` | if the pick is points 1 - 3: whether the lift car's door stops a fed (line 65 / 66) | anything in 4 picks of 7 (S3) |
| `H3_DM09_die_fed_g2` | if the pick is 4 / 5: the atrium car, 2 gotos + 3 blind | anything in 5 picks of 7 |
| `H3_DM09_die_fed_g3` | if the pick is 6 / 7: on the square's ground or 70 under the road's collision | anything in 5 picks of 7 |
| `H3_DM03_F3_fed_dies` | the fed's way by the yard and the drop to the level exit; a second death IF a heister comes | F3 when nobody passes in his 60 s (S5) |
| `H3_DM03_F4_two_rounds` | whether RETURN on the page after a fed round starts round 2, which body he has there, `fed: police bodies:` of round 2 | nothing if the trap fires on the old page (S4): count the 0x19 lines |

RESULT PASS says only that the game did not fault and the script ended - true of all twelve, as each
`.expect.txt` already says.
