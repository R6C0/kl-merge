# Review of the three play fixes (balance, bots at the loot, key-framed van) and how to join them

Agent p-review, 2026-10-10 evening. Adversarial. OFFLINE: the game was not started, nothing was installed,
nothing was written into the Dog Days folder, no repository file but this one was written. Words: **run** = I ran
it now, **read** = I disassembled it now, **measured** = my own script on the written files, ASSUMPTION, GUESS.

Reviewed: `klhook/klbalance.c` + `re/balance.md` (p-balance), `tools/kl_fa_bots.py` + `re/bots.md` 12 +
`<work>\build\y_loot2\M01 M02 M03 M06` (p-loot), `tools/kl_map_escape.py` + `re/map_escape.md` part 2 +
`<work>\build\y_van\M01 M02 M03` (p-van). `<work>\build\y_bal` does not exist - correctly: the balance piece
changes no level.

## 0. Verdicts

| piece | verdict | what stands in the way |
|---|---|---|
| balance (`klbalance.c`) | **GO for the live checks B0, B1** after one small fix (D1). Numbers confirmed against kl2.exe. No write can reach a stock level or another mode. | D1: a transient read failure makes the health factor apply twice (550 -> 401 -> 293). |
| bots (`y_loot2`) | **GO as built** for live checks on the spline-car builds (all four pass every checker; every reference resolves). | Nothing at load. The behaviour claims are unseen. |
| van (`y_van`) | M01, M03: **GO** for the van-alone checks. **M02: NO-GO until D2** (its .HVK is 15.7 MB). | D2: 2,087 filler copies of a mall wall in the .HVK. |
| the three together | **Possible, proven by a trial build of each car map (section 4), but NOT by the two notes' recipe**: van + bots as the notes say puts the bots ON the van's line on all three maps (2 .. 25 from its centre) and every checker still says PASS (D3). M03 also loses its fall-back box (D4). | D3, D4: two changes in `kl_fa_bots.py` (p-loot's file). |

| map | van | bots | together | first live build |
|---|---|---|---|---|
| M01 diner | GO | GO | GO after D3 (trial build passes all checkers) | `y_van\M01` (van alone), then the joined build |
| M02 Late Night Opening | NO-GO until D2 | GO | after D2 + D3 | `y_loot2\M02` (cases, spline car) - it needs neither fix |
| M03 bank | GO | GO | after D3; and only after check L3 on `y_loot2\M03` or after D4 | `y_loot2\M03` (does the AI take the drop?) |
| M06 park | no van (helicopter) | GO | = `y_loot2\M06` | `y_loot2\M06` |

## 1. Checkers, run by me on every delivered build

57 runs on the 7 delivered folders, then 21 on my joined trial builds (section 4).

| | `kl_fa_bots check` | `kl_map_guns check` | `kl_impact` | `kl_map_escape check` | `kl_maps preflight` | `kl_maps audit` | `kl_fa check` |
|---|---|---|---|---|---|---|---|
| `y_loot2\M01` | PASS 0 FAIL 0 NOTE | exit 0 | problems: 0 | exit 0 | CRASH 0 RISK 0 | PASS (1 known) | exit 0 |
| `y_loot2\M02` | PASS 0 / 1 | exit 0 | 0 | exit 0 | CRASH 0 RISK 3 | PASS (6) | exit 0 |
| `y_loot2\M03` | PASS 0 / 1 | exit 0 | 0 | exit 0 | CRASH 0 RISK 0 | PASS (0) | exit 0 |
| `y_loot2\M06` | PASS 0 / 1 | exit 0 | 0 | exit 0 | CRASH 0 RISK 2 | PASS (6) | exit 0 |
| `y_van\M01` | FAIL 3 (no bots yet: expected) | exit 0 | 0 | 0 faults | CRASH 0 RISK 0 | PASS (1) | exit 0 |
| `y_van\M02` | FAIL 3 (same) | exit 0 | 0 | 0 faults | CRASH 0 RISK 3 | PASS (6) | exit 0 |
| `y_van\M03` | FAIL 3 (same) | exit 0 | 0 | 0 faults | CRASH 0 RISK 0 | PASS (0) | exit 0 |

- These agree with both notes' tables. `debug\check.py` was NOT run properly (I gave it a folder; it wants the
  `.prp` beside its `.gms`): p-loot's '0 records' line is not re-checked.
- Side effect: `kl_maps.py audit` / `preflight` rewrite `audit.json`, `audit.txt`, `preflight.json` inside the
  folder they check. The archives were not touched.
- Hook: a scratch copy of `klhook\` as it was at 18:29 with p-balance's three lines compiles as SHIP
  (`build.bat`) and TEST (`build_auto.bat`); no warning in the output's last lines.

Budget, bytes (measured from the archives; chunk table 69,632 usable):

| | .prm | .ANM | .fxc | F01_Main.WAV | chunk entries | .HVK | .TEX |
|---|---|---|---|---|---|---|---|
| M01 `t_maps2` = `y_loot2` | 55,917,968 | 22,061,764 | 17,760,648 | 21,722,704 | 50,254 | 1,401,088 | 242,724,752 |
| M01 `y_van` = joined trial | 56,992,176 | 22,039,292 | 17,760,648 | 21,145,936 | 49,973 | 2,077,840 | 246,355,616 |
| M02 `t_maps2` = `y_loot2` | 55,449,184 | 22,202,472 | 17,760,648 | 22,527,568 | 58,583 | 1,647,280 | 224,349,952 |
| M02 `y_van` = joined trial | 56,522,544 | 22,180,036 | 17,760,648 | 22,113,616 | 58,300 | **15,734,304** | 227,980,720 |
| M03 `t_maps2` = `y_loot2` | 61,299,008 | 22,202,616 | 17,760,648 | 22,716,752 | 62,892 | 2,536,304 | 225,939,136 |
| M03 `y_van` = joined trial | 62,581,504 | 22,202,616 | 17,760,648 | 22,669,648 | 62,892 | 3,588,400 | 237,631,936 |
| M06 `t_maps2` = `y_loot2` | 50,415,712 | 21,642,576 | 17,760,648 | 21,775,744 | 47,114 | - | 212,826,208 |

The bot step adds nothing to the four blocks on either base. The four blocks are as the notes say; the .HVK is
the number neither note printed.

## 2. Defects

### D1 (balance, PLAUSIBLE, small): the health factor can be applied twice
`klr_player_tick` clears `klr_p.have` on ANY failed read or sanity test (local index 0xff, vtable, `[H+0x24]`,
`cur > max * 1.01 + 1`). The next good pass is then `fresh`, and `klr_track(fresh)` takes what is in the object
as 'what the game gave' - which is the hook's own 401.5. Result: 401.5 x 0.73 = 293, and the log says 'the game
gave 401.5'. Read off the code; whether a pass ever fails while the same object lives was not established (the
death camera, the fed switch and any routine that sets health without the maximum are the candidates).
Fix (two lines): `fresh = klr_p.player != pl || klr_p.h != h;` and do not clear `have` on a failed pass - a new
object at the same address is still caught, because `klr_track` compares VALUES (the game's 550 is neither the
old base's successor nor `wrote`). Until then check B1 must watch for a second 'your health set' line with
'the game gave 401.5'.

### D2 (van, CONFIRMED, M02 only): the .HVK is 15.7 MB
`kl_escape.cut_collision` replaces every static placement it cuts by a copy of the FIRST kept static placement
of the file, one shape record each (vertices and MOPP code repeated). Measured, placements of one entity:

| | t_maps2 | y_van | the filler | bytes of it |
|---|---|---|---|---|
| M01 | 2,056 placements | 3,867 | 1,816 x `ColiObj_blocker_03` | 434,024 |
| M02 | 2,010 | 4,092 | **2,087 x `PC0401_M02_FA_Wall_Bottom_01`** | **15,364,494** |
| M03 | 3,667 | 5,560 | 1,899 x `Neon_ON_06` | 833,661 |
| Retomoto (`v_rtbots\retomoto_bots`, loaded and played) | | 7,275 | 1,733 x `Geometry_HeadLightR_LOD09` | 374,328 |

- So `re/map_escape.md` 10.3 'the 1,748 filler copies ... are cut' is not what the file holds: they are swapped
  for copies of a map object. Retomoto has the same thing and loads and plays, so the mechanism is live-proven;
  the SIZE on M02 is not: the largest stock .HVK is 3,165,936 (L10), Retomoto's is 5,002,128.
- The owner's two load crashes (0x8e5bbd) were a failed allocation in a full 2 GB address space. 14 MB more
  in a member whose loading was never measured is exactly that class. ASSUMPTION that the file is read whole.
- Fix (p-van, in `van_hvk` or by passing a filler): take the kept static placement with the SMALLEST
  vertices + code as the filler, not the first. A van check line 'largest share of one entity in the .HVK' would
  have caught it. Then rebuild M02 (M01 / M03 gain a little too).

### D3 (joining, CONFIRMED): van + bots as the notes prescribe stands the bots in the van's lane
`re/map_escape.md` 12 tells the lead to pass `--park` = `van.json` plan.board. That point is the van's boarding
box = 337 behind its stop ON its line: the van's nose (with its `KillBox`, half 90 x 100 x 56 at the nose,
'CheckInsideEnter', 'FA_DieFromSelf') passes through it on the way in. And `kl_fa_bots.lanes()` finds no route
on a van build (it reads `OnlineEscHavokCar` splines only), so `--lane` does nothing and the way-out places go
back into the road. Run (`kl_fa_bots.py build <y_van\Mxx> <scratch> <recipe> --park <plan.board>`), then
measured against the van's own keys (distance from a bot's PLACE to the van's centre line; half width 100):

| | notes' recipe | `y_loot2` places against the same van line | trial of section 4 |
|---|---|---|---|
| M01 | **2** (the park place, drive in), **25** (way place, drive away) | 254 .. 449 | 257 .. 449 |
| M02 | **7** (park), **66** (level exit place) | 213, 216 | 250, 330 |
| M03 | **6** (park), **9, 10, 20** (the three street places, drive in - the van comes from behind them) | 212 .. 274 | 250 .. 352 |

Every checker passed on those builds (`kl_fa_bots check` PASS, `van-check` 0 faults): **a checker gap**.
p-van's `--park 1967,220,-1073` for M03 does not build with `--drop` at all (`ValueError: no path on the mesh
from level to park`: the drop is one way). Whether the KillBox kills an AI actor was not read; a key-framed van
drives through whatever is there either way.
Fix (p-loot, `kl_fa_bots.py`): (a) `lanes()` also returns, for an `OnlineEscAnimatedVehicle`, the polyline of
the van's position keys from the first frame of `Activate_Enter` to the last of `Activate_Exit` (decode as
`kl_map_escape.VanKeys`); (b) the ally-box park place obeys `off()` too; (c) `check()` FAILs a way-out or park
place nearer than `LANE_CLEAR` to that line. (a) was tried by replacing the function in a scratch process: section 4.

### D4 (joining, CONFIRMED, M03): with `--park` the fall-back box at the wall is gone
`y_loot2\M03` has ONE `AllyEscapeBox`, at the gather place (-1707, 420, -900) in front of the drop - p-loot's
fall-back 'if the AI does not take the link they are taken aboard from there'. On a van build the bots must end
in an ally box at the street (the van's own box rides on the van; in the file it lies at the waiting place,
5,833 away), and the tool writes one box only: measured on the joined M03, the single box is at (3105, 200, -403).
So if the hand-written drop link is not taken (ASSUMPTION of 12.3, never loaded by the game), seven bots stand
in the yard for the rest of the round. Either run L3 on `y_loot2\M03` FIRST, or let the tool write both boxes
(stock F02 / F06 have several).

### Smaller
- With `--park` the bots of M01 and M02 now VANISH in an ally box beside the van (`u_maps` M01 / M02 walked to
  the car through the tactic). Expected by both notes, but it is what the owner will see.
- `re/bots.md` 12.2 'the boarding action is in box 02' and 12.5's table are about the spline car; on a van
  build the action lies at the waiting place. Nothing fails on it.
- Balance, `Ramp=1` at Arcade level 11 (run `kl_map_ai.py balance`): police kill a heister in 5 hits, a
  heister needs 34 for a policeman (stock's 0.1 is kept, the 0.01 .. 0.5 the other way is raised to 1.0). 'Never
  easier than stock', but the AI heisters are worse off than in stock there. A choice, not a fault.
- Balance: a `[Bots] Retaliate` under 1 would make `klr_table`'s shape test (+0x18 in 1..100000) fail, and then
  the table is neither written NOR put back. klbot.c accepts any value over 0. Clamp one of the two.

## 3. Claims I tried to refute and could not

Balance, against kl2.exe (read):
- The table: my own sweep of the constructor 0x524050 (every `fld [const]` before each `lea reg, [edi+off]`)
  gives the eleven rows of `re/balance.md` 2 exactly, all eight columns, and the player blocks 550 / 4 / 4
  (Arcade, +0x604), 550 / 5 / 3 (+0x5c4), 100 / 5 / 2 (+0x5e4).
- The readers 0x591b60, 0x8b8050, 0x7c1ba0: the record address `[0x168d7c0] + 0x6ac + L * 0x70`, L clamped to
  1..11, the team test `[[actor+0x54]+4] == 2`, the police swap on `[player+0x2723]`, +0x1c on a differing
  stage - as written. 0x4206f0 picks +0x604 when 0x7f6850 says Arcade. 0x7f6850's jump table is
  {mode test, mode test, false, false}: `klr_arcade` mirrors it. `inc byte [score+0x45]` at 0x74bcf0 only with
  status 6; 0x56955a sets it to 1. 0x46ef60 reads +0xe4, +0x13c for a ZActor owner (0x150cce0), +0x140 in mode 4.
- `kl_map_ai.py balance u_maps\M02` reproduces section 4's rows (91 / 2 / 417 / 2 today, 7 / 3 / 5 / 4 at Risk=2).
- A write on a stock level or in another mode: none found. Both writes need `klr_arcade` (mode 4) AND
  `klb_level` = verdict 2 (which needs the Steam guard on); the table goes back when either stops holding, the
  process keeps nothing, the tuning object is heap. Between a session start and the archive's verdict the table
  may hold the dial for one pass on a stock level - before any shot.
- Not checked: the hits-to-kill unit ASSUMPTION (distance), NPC health x 0.9, who else reads R+0x00..+0x14.

Bots (read / measured):
- 'Activate' on a `ZHavokShatterGlass`: 0x471410 compares the message with the ids of 'ProjectileHit'
  (-> 0x53f6d0), 'CanPenetrate', 'Collision' (ignored) and 'Activate' (-> 0x8d1b60); the four names were found by
  the initialisers of the four static objects. As 12.1 says.
- `t_maps2\M02`: 26 containers, 23 opened by nothing but their pane's `RelayMessage`. `y_loot2\M02`: all 23 are
  also named by a squad `RelayMessageList` 'Open', all 23 panes by an 'Activate' relay, 0 relay targets of
  another kind, 0 containers nothing opens. M01 / M03 / M06 have no glass-only container.
- Every `ROOT\` reference of every build resolves to exactly one node (y_loot2: 3,652 / 7,004 / 6,447 / 3,301;
  y_van: 3,529 / 6,402 / 6,270; joined: 3,726 / 7,087 / 6,530). No squad timer, relay or step is left unnamed
  (only the seven squads, their soldiers and the ally box, which nothing needs to name).
- The drop link changes the mesh block by 80 bytes; M01 / M02 meshes are byte-identical in t_maps2, y_van,
  y_loot2 and the joined builds, and M03's joined mesh equals y_loot2's (md5) - the link lands on the same polygons.
- 'Can never fire' was not shown for any step. NOT established by anyone: that the AI takes a hand-written
  link, that a relay from the squad breaks glass in a room, the container's countdown unit, what
  `TriggerLootDepleted` does with objects still inactive in a shut case.

Van (measured on the written keys):
- No reference names a removed object: the only strings with the old names are the settings' text key
  'Multiplayer/Objectives/EscapeCar' and the van's own `EscCamera01_01`. Exit triggers name the van alone.
- 563 position keys, all finite, y -19 .. 152; frame 0 is the waiting place.
- Level bounds, with players aboard: M02 frames 358..370, M03 360..367 of the drive away (M01: frames 100..102
  of the drive in only). **Stock does the same**: all three vans of stock F07 and of stock F04 pass through a
  `LevelBound` box, on the way in and on the way out (F07 van 1: frames 427..430 of exit 273..485). p-van's open
  point V5 is therefore low risk.
- Through collision: not re-tested by a method of my own; `van-check`'s lane test (0 faults) stands alone.

## 4. Can they be combined, and in what order

Yes. Proven by a trial (scratch only; `kl_fa_bots.lanes` replaced in the process by the van's key line, park =
`y_loot2`'s last station pushed to 420+ from that line): three joined archives, **all seven checkers exit 0 on
each (21 of 21)**, bots 250+ from the van's line, blocks as `y_van`.

    M01  --stops 4 --cases glass --exit-boxes cut --loot-seconds 30 --lane --park 5826,0,20213
    M02  --stops 4 --cases glass --loot-seconds 45 --lane --park -564,0,-8264
    M03  --stops 4 --cases glass --drop --lane --park 3105,0,-403
    (the recipe = kl_fa_bots.RECIPE; these parks are only right WITH fix D3 a; the trial archives are in this
     session's temp folder and are not a delivery)

Order - it is forced:

1. **Van first**: `python tools\kl_map_escape.py van <work>\build\t_maps2 <out> M01 M02 M03`. It is a whole new
   graft (kl_graft.build with four patches, then lighten, wardrobe, kl_map_tune): it rewrites EVERY member -
   .prp .gms .buf .HVK .oct .prm .TEX .MAT .ANM .SND .sgd, the .WAV / .WHD beside the archive, the two ini
   files. Run on a folder that has bots it would drop them. (After D2.)
2. **Bots second**, on the van's folder: `python tools\kl_fa_bots.py build <out>\Mxx <final>\Mxx <line above>`.
   It patches .prp .gms .buf .oct .rmi .rmc and 4 bytes per model root in the .prm (same size), and
   `KLGuns.ini` only if `Entries=` is missing. M01: the two exit boxes are cut here (the van's wiring in fields
   0 and 2 survives: read back). M03: the drop link is written here. (After D3; M03 after D4 or L3.)
3. **M06**: `y_loot2\M06` as it is.
4. **Balance last and separate**: the hook only, no member. Its three lines go into `klhook.c` after klbot.c's;
   `[Balance] Enable=0` until its own checks.
5. On each final folder: `kl_maps.py audit`, `kl_fa_bots.py check`, `kl_map_guns.py check`, `kl_impact.py`,
   `kl_map_escape.py check`, and - until D3 c exists - the distance table of D3 by hand.

## 5. Live checks, in order (one variable each)

| # | build / ini | proves |
|---|---|---|
| 1 | `y_loot2\M06` | L0, L5 of re/bots.md: the four stops. Needs no fix; no van on this map |
| 2 | `y_loot2\M02` (spline car) | L1, L2: panes burst about 1 s after a bot passes the store door, the jewels can be taken, the bots' money rises in klbot's log. The owner's first complaint, with nothing else changed |
| 3 | `y_loot2\M03` (spline car) | L3: do the bots hop down at (-1704, 220, -766)? This decides D4 and whether the teleport of 12.3 is needed, BEFORE the van is in the picture |
| 4 | `y_loot2\M01` | L4: the car's countdown does not start at the back door; the Senator is looted |
| 5 | `y_van\M03`, then `y_van\M01` (no bots) | V0 .. V4, V6 of re/map_escape.md: M03's van waits inside the bounds at (-2555, 152, 558) and can be looked at first. A picture of it on the road proves the yaw sign |
| 6 | `y_van\M02` rebuilt after D2 | V0, V2, V5 (the bound with players aboard: no warning) |
| 7 | joined M01, M03, M02 (after D3) | V7: the bots stand beside the van's line when it arrives and are gone with it; pictures at the stop. M03: the van comes down the street from BEHIND the bots that have dropped - nobody is run over |
| 8 | any of the above + `[Balance] Enable=1 Log=2`, no Risk | B0: the eleven table lines equal section 2, 'Arcade 550 4.0 4.0', the difficulty option, 'you lost 6.x'. Writes nothing, so it may ride on run 1 |
| 9 | + `Risk=2` on a map whose bots and van are already seen | B1 .. B5; and D1: no second 'your health set' with 'the game gave 401.5' |
| 10 | `Risk=2` on M01 / M03 | B6: the never-missing pistol guards (accuracy 100) at police->you 1.0 |

Balance comes last on purpose: under Risk=2 a heister dies after 5 police hits instead of 417, so every bot
claim above (who reaches the loot, who reaches the van) must have been seen with stock damage first.

## 6. My scripts (session temp folder, not kept: `rev.py`, `rev2.py`, `combo2.py`)

`rev.py one <folder>`: every `ROOT\` reference resolved, strings naming removed objects, the van's keys against
level bounds / exit boxes / a `bots.json`, unnamed squad nodes. `rev2.py`: who opens each money container, the
.HVK's placements per entity, the van against `LevelBound` boxes (also stock F07 / F04). `combo2.py`: the trial
of section 4. They read the builds through `kl_map_escape.Level` and `VanKeys`; the tests on them are mine.
