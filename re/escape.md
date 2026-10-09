# The escape on the Dead Men bank (F07 systems + M03_FA_A): why the van is out of reach

2026-10-09, agent g-escape. Offline only: Dead Men's original `M03_FA_A` archive, `kaneandlynch.exe`,
`kl2.exe`, the build in `<work>\build\install` (read, not changed). Nothing here was tried in the game.
Tool: `tools/kl_escape.py` (the repairs, the walk test, the route). Status words: **seen** = read in
the files / exe with the command given, **ASSUMPTION**, **not established**.

State: complete for what can be done offline. The fix is built and verified in a scratch folder
(section 5); it is NOT in kl_graft and NOT installed - three lines for the lead (5.2).

## 0. Answer

**Nothing opens a gate. In Dead Men the criminals CLIMB the yard's north wall, and Dog Days' player
cannot climb.**

- The yard behind the garage (floor y 200) and the street the van uses (y 150 in the west, 12 in the
  east) are separated by one straight wall at z -625..-575, top at y 404: 2.04 m above the yard.
  In the level's static collision (`.HVK`, the same bytes in the graft) nothing joins the two sides:
  a flood fill over the collision triangles from the garage door reaches 75,363 cells and none inside
  `ExitTrigger_01`; from the van's stop it reaches 60,675 cells and none in the yard (section 3).
- `kaneandlynch.exe` has a player movement class **`ZFFPlayerMovementClimb`** (RTTI
  `.?AVZFFPlayerMovementClimb@@`, vtable 0x966c44). Its slot 20 (0x603340) builds a table of three
  climbs: `/Movement/Climb/Up/Low` 120, `/Movement/Climb/Up/Medium` 170, `/Movement/Climb/Up/High`
  **220** (floats at 0x952e74, 0x94d438, 0x966ce4; plus `Sprint_Low`). The hero's animation table
  (0x5e53e0) pairs them with `/Movement/Fall/Fall_1m` and `Fall_2m`. A 2.04 m wall is inside 'High'.
- `kl2.exe` has **no** such class: its `ZFFPlayerMovement*` classes are BaseMove, COOPAirlock,
  CloseCombat, Die, Fall, Guide, HeliPassenger, MountedWeapon, Prone, Rappel, Roll, Stand, StandCover,
  VehiclePassenger. The three `/Movement/Climb/Up/*` strings are still in the exe, the class is gone;
  Dog Days only vaults over cover (`ZFFActionVaultOver`, `/Cover/Vaulting/Cover_Vault_*_1M / _2M`).
- The level design shows the climb was meant: where the far side is too deep, the wall carries a
  hero-only collision wall (`ColiObj_Player_02`, flags 0x108, x -1007..2333, y 200..527) and a chain
  link fence on top (x -559..2300); **west of x -1100 it carries neither** - four plain pieces
  `SO0101_M03_Wall_Low_8m_05 / _01 / _02 / _03` (x -4300..-1100) - and on the street side dumpsters
  stand against exactly that stretch (`SO0701_M03_Dumpster_A_10` x -1454..-1200, `_02`, `_03`
  x -3332..-2816, lids at y 285): wall top 404 -> lid 285 -> street 150 are the 'Fall_1m' steps.
- The three `SO0301_USA_animFence_02_FA_*` fences are not the way: they are STATIC collision (type 1,
  REF 9520 / 11488 / 11489), their `MatPosAnim` is named by nothing in the level, and they close the
  ramp along the bank's east side (yard y 200 up to the plaza y 700), not the street. The fourth,
  `..._FA_03` at (-499, 203, -755), has no controller at all; it stands in front of the wall (picture
  RN10_270s).
- So the conversion and the graft drop nothing here. Every object of Dead Men's escape is in the built
  level, in Dog Days' form (section 2). The route is cut by a missing player ability.

Fix (section 5): open the wall where Dead Men's players climb it - one 8 m piece sunk to yard height
and its collision placement taken out of the `.HVK`. Whether Dead Men's spline van then comes is the
next live question; it could not be reached so far, so nothing is known about it.

## 1. The round in Dead Men, object by object

Paths without `ROOT\`. Boxes: `ZBoxPrimitive[0..2]` are HALF extents (tools/kl_fa_author.py; here:
`ExitBankTrigger_01` = centre x 291, half 480 covers the two garage doors x -171..770 exactly). A box
whose rotation is `(0,0,1, 0,1,0, 1,0,0)` is unrotated: its first size runs along x.

| step | object [class] @controller | where | what it does (field values) |
|---|---|---|---|
| start | `SpawnPoint!SpawnPoint_Start_01..08` [ZSpawnPoint] | plaza, (-2262..-1214, 791, -12275..-11224) | criminals |
| | `Triggers!SpawnTrigger` @TriggerBox | (-1624, 707, -11808) half 800 x 150 x 1000 | -> `DeliveryCar_Timer` (6) -> delivery car drives off, sounds |
| enter | `Triggers!EnterBankTrigger_01` @OnlineGamePlayTrigger ENTERS_BANK | (303, 974, -9407) half 300 x 200 x 100 | game rules: 'looting has started' |
| | `Triggers!Start_Heist` @TriggerBox | (309, 803, -9424) | -> BankMainSquad_01..03 Hunt, ArrivingCops_Squad_01 + ParkingLotSWAT_01 VehicleEnter |
| | `Triggers!ArrivingCops_Squad_01/_02/_03_Trigger` @OnlineTriggerBox | (292, 789, -9250) | field 5 = 3 / 0 / 2, message 'AITrigger' -> police cars; see 4.2 |
| loot | 4 x `...Bank_Main_01\PC0500_M03_FA_Cashdrawer_03..06\Cashbox` @OnlineMoneyContainer + @TriggerBox2 'Open' 125 | hall, y 875 | $100,000 each (works live) |
| | 8 x `...Garage_01a\PC0500_M03_MoneyBox_nn\Attach01` @OnlineMoneyContainer + @TriggerBox2 'Open' **80** on boxes 10 and 11 (01-03, 07-09: 145) | garage, y 241 / 328 | $200,000 each (`PC0500_M03_Money_Arranged_nn`, a sibling, not a child) |
| | `Money!ContainerMoney!Box_Money_01..10`, `Money!KillDrop!Wallet_*`, `Money!...` 316 DROP stacks | - | pools |
| leave | `Triggers!ExitBankTrigger_02` @OnlineGamePlayTrigger EXITS_BANK | west door (-1231, 424, -4730), 10 x 200 x 120 | the door that is always open |
| | `Triggers!ExitBankTrigger_01` @OnlineGamePlayTrigger EXITS_BANK | garage doors (291, 399, -4668), half 480 along x | |
| | `Triggers!GarageDoors!TriggerBox` @OnlineTriggerBox + @TriggerBox2 | (-36, 340, -5779) half 150 x 150 x 1000 (garage's west aisle) | TriggerBox2: 'Activate' -> `...Garage_01a\SI0201_M03_BackDorAnim_01 / _02` (the two roller doors, x -171..250 and 349..770 at z -4706; @MatPosAnim frames 1..150, @MatPosAnimNetSync, @Audio_PlaySound; type 4 key-framed collision REF 3895 / 3896). OnlineTriggerBox: 'Activate' -> `Triggers!GarageDoors!Timer` (3) -> `...!PathBlocker` @PathBlocker eUnblock (297, 204, -4683) -> door sound. Field 5 / 6 = **5**: see 4.2 |
| yard | `Triggers!EscSquad_Triggere` @TriggerBox | (-589, 310, -2630) half 3100 x 304 x 2172 = the yard | -> `AI_Enemies!EscSquad\VehicleEnterBehaviour`: a police car drives down the east street to (2978, 15, -1612), below the yard |
| | `Triggers!Respawn_Trigger`, `Parkinglot_SWAT_Trigger_01/_02`, `Balcony_SWAT_Trigger` @TriggerBox | - | -> `Parkinglot_SWAT_Timer`, `ArrivingCops_Timer` |
| **wall** | `...Outside_01A\SO0101_M03_Wall_Low_8m_05 / _01 / _02 / _03` [ZSTDOBJ], no controller | x -1900..-1100 / -2700..-1900 / -3500..-2700 / -4300..-3500, y 0..404, z -625..-575 | **climbed** (`ZFFPlayerMovementClimb`); nothing in the level refers to them |
| call | `Triggers!ExitTrigger_01` @OnlineExitLevelTrigger -> `EscapeSetup!EscapeCars\EscapeCare` | (408, 396, 460) half 4000 x 400 x 1000: x -3592..4408, **z -540..1460**, y -4..796 = the whole street north of the wall | a criminal inside calls the van |
| van | `EscapeSetup!EscapeCars\EscapeCare` [ZGROUP] @OnlineEscHavokCar @OnlineEscVehicleController @VehicleEffects, child `Ground_01` [ZHavokCar 'VAN'] @HavokCarScriptRout | waits at (-8554, 161, 2660) | field 0 -> `...\VehicleMoveBehaviour_Incomming` (@VehicleMoveBehaviourRout 50, @OnlineVehicleOnSpline; spline (-8410, 163, 2370) (-7530, 163, 1461) (-5461, 167, 1097) (-3137, 169, 945) (-2262, 169, 352) (-1325, 157, 22) (458, 111, 110) (1910, 50, 130) **(2970, 25, 41)**), field 1 -> `..._Escaping` (70; (3592, 6, -1) (4736, 6, 246) (7296, 11, 209) (9064, 10, 332) ... (10435, 33, -2125)), 2 -> boarding trigger, 3 -> map icon |
| board | `Triggers!BoardingTrigger_Car` @PlayerAction 'EnterVehicle' -> `Triggers!BoardingGameplayTrigger` (@OnlineGamePlayTrigger BOARDS) | (3252, 133, -20) half 400 x 200 x 300 | hold use at the van |
| | `EscCameraSetup!CameraTrigger01` @OnlineEscCamTrigger -> `EscCamera01` | (2537, 9, 96) half 1119 x 400 x 680 | escape camera |
| bounds | `Level_Bounds!LevelBound_Back_East / _Back_West` @LevelBound | (-4136, 278, 1179), (4950, 172, 366) | the two ends of the van's street: the street is play area |

The intended route: plaza -> bank hall (y 800, cash drawers) -> stairs down -> garage (y 200 - 330,
money boxes) -> west door (or the roller doors) -> yard (y 200) -> over the wall anywhere between
x -3500 and x -1100 -> street (y 150) -> east along it, 40 m downhill -> van at (2970, 25, 41).
No object opens anything on that route except the roller doors.

## 2. What the conversion and the graft do to each

Read from `<work>\build\install\Scenes\Locations\F01\F01_Main.zip` (19,828 nodes) with
`kl_fa.load` and compared with the source node by node:

| object | in the built level |
|---|---|
| every trigger above | kept, same place; `TriggerBox` 14 -> 18 fields, `TriggerDelay` + 1 bool (kl_convert) |
| `OnlineTriggerBox`, `TriggerBox2`, `PathBlocker`, `MatPosAnim`, `MatPosAnimNetSync`, `Audio_PlaySound`, `OnlineVehicleOnSpline`, `VehicleMoveBehaviourRout`, `HavokCarScriptRout`, `PassengerAnimPos`, `OnlineEscHavokCar`, `VehicleEffects` | kept field for field (same layouts in both exes). kl_convert.UNSUPPORTED holds only `PhysicsBasedAnimated`; CLAUDE.md's old note that `OnlineVehicleOnSpline` / `OnlineTriggerBox` are removed is out of date |
| `ExitTrigger_01` | vehicle moved to field 2 (kl_fa.exit_trigger): `0:0 1:'' 2:ROOT\EscapeSetup!EscapeCars\EscapeCare` |
| monitor | F07's `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor`, all nine lists empty after kl_fa.prune |
| `EscapeCare` / `Ground_01` | still ZGROUP / ZHavokCar (kl_retype keeps the class), `anmcol:animationdatabase#Van` converted by kl_anmjoin |
| `EscCameraSetup!CameraTrigger01` | camera moved to field 1 (kl_fa.cam_trigger) |
| `EscapeCar_OnMap` @Ingamemap, `GUIResources!MapIcon*` | controller dropped (not registered by kl2.exe) - no escape marker on the HUD |
| the wall pieces, the fences, the roller doors | kept; collision = Dead Men's `.HVK` (the graft's base), REF ids renumbered |
| the nav mesh | Dead Men's, 16 -> 32 bit. Its single link (kind 6, cost 1265, waypoint 83 on the garage roof (43, 1435, -4709) -> the yard) is dropped by kl_pf4: that is the SWAT's rappel, not a way out. Parts A and B were never joined in Dead Men either: its AI does not cross the wall |

So: dropped = only map icons; retyped = nothing on the route; left without trigger = the roller doors
in a solo round (4.2); kept but unusable = the wall (the climb), and behind it everything of the escape.

## 3. Evidence that the wall is the cut

`python tools/kl_escape.py walls` (the walk test: every non-convex static / key-framed collision
triangle of the `.HVK` sampled every 10 units into 20-unit cells; a step is allowed 45 up, 60 down,
blocked by any collision 55..165 above the floor. Its limits: it knows no climbing and no
character radius).

- From the yard (300, 220, -4500): 77,120 cells, x -4870..2450, z -7550 up to **-650**, 0 cells in the exit
  box (75,363 with the test area cut at z -7000: the figure in section 0). The run takes 82 s.
  Allowing drops of 120 / 250 / 450 changes nothing (74,968 cells, 0 in the box): there is no ledge to
  jump from either - the east side (street at y 0) has `SO0101_M03_Wall_High_8m_*` and
  `ColiObj_Player_03`.
- From the van's stop (3100, 5, 0): 60,675 cells, x -4670..5670, **z from -570** (the wall) to 2790,
  30,365 of them inside the exit box, 1,200 inside the boarding box.
- Taking one object out of the collision: any single `Wall_Low_8m_05 / _01 / _02 / _03`, or
  `Wall_Slope_36m_02`, joins the two (30,365 exit cells reached). Taking out the garage doors, the
  four animFence, every flags-0x108 shape (95 hero-only walls), `ColiObj_OnlyHero_01`, the gate
  `..._FA_03`, `ColiObj_Player_02` or `_03` does not.
- The wall: `SO0101_M03_Wall_Low_8m_05` at (-1500, 0, -600), HVK shape = 6 triangles (top y 404, faces
  z -625 and z -575); visual bounds of its model -400..400 x 0..403.5 x -25..25. Yard asphalt
  `SO0201_M03_Road_Asphalt_20mx20m_09 / _10` at y 200 ends at z -600; street asphalt at y 150 begins there.
- live, f-live: seven places along the wall tried from the yard side, all closed (EX1, EX2).

## 4. Other findings

### 4.1 The garage's money boxes
Compared field by field with the cash drawer that works and with stock F01 / F03 / F08 (117 containers):

| | stock (117) | drawer 06 (works) | garage box 10 / 11 |
|---|---|---|---|
| `OnlineMoneyContainer` 1 / 2 / 3 / 4 / 6 | 0 / 0 / 0 / 10 / 'Activate' | **2** / 0 / 0 / 10 / 'Activate' | **3** / 0 / 0 / 10 / 'Activate' |
| its `TriggerBox2` (0 = itself, 5 = 'Open') radius | 125 | 125 | **80** (boxes 01-03, 07-09: 145) |
| field 0, the loot | a child, `OnlineMoneyCtrl` CONTAINER, field 11 = 1 (F01) | a child, field 11 = 0 | a SIBLING of the case (`...Garage_01a\PC0500_M03_Money_Arranged_05`, same place), field 11 = 0 |
| loot's own `TriggerBox2` 'AI_TRIGGER_WITH_ACTIVATOR' radius | 150 | 125 | 80 |
| field 5 | a `MatPosAnimProxy` box | 2 nodes with `MatPosAnim` 'Activate' | 4 nodes with `MatPosAnim` 'Activate' |

The box differs from the working drawer in the reach (80), in field 1 (3 against 2; meaning not
established - stock has only 0) and in the loot not being a child. RN10 stood at (640, -6230) and
(440, -6230) with a way-point radius of 60: 78 to 138 from the trigger centres (662, 241, -6155) and
(424, 241, -6154). **Most likely it was out of reach** (ASSUMPTION; the reach is measured from the
controller's node, which is how the drawer behaved: in front of the counter '3 units out of reach').
`kl_escape.money_reach` sets every container reach below 125 to 125 (GUESS: the stock value); the
route in section 6 gives a standing place for each box.

### 4.2 The roller doors
RN10's route went to (291, -4700) and back, then out by the west door: the doors were shut. What
opens them is `Triggers!GarageDoors!TriggerBox`, whose `OnlineTriggerBox` field 5 and `TriggerBox2`
field 6 are both **5**. The same field is 3 / 0 / 2 on the three `ArrivingCops_Squad_0n_Trigger`
boxes at the bank door (which call one more police car each) and 0 on every money trigger.
ASSUMPTION: a player count - the second exit is for crews of five and more, and a solo Arcade round
never opens it. Not read in code. The doors are not needed: the west door (`ExitBankTrigger_02`) is open.

### 4.3 Dog Days' own van as a fallback
`tools/kl_fa_author.py` (Retomoto) lays F07's three baked vans by one rigid transform. Their drives
are 28 - 37 m wide across the road; the bank's street is 12.8 m (z -534..744). A baked van would
drive through the buildings: not a fallback for this map unless a new animation is made. Dead Men's
spline car is the only fitting vehicle; kl_fa.check lists it as DEGRADED / untested.

## 5. The fix

### 5.1 What `tools/kl_escape.py` does
Dog Days' exe has no climb to give back, so the wall is opened where Dead Men's players climb it.
All repairs change values of existing objects; no entity or controller is added or removed.

| function | what | marked |
|---|---|---|
| `open_wall(Jn)` | `...Outside_01A\SO0101_M03_Wall_Low_8m_05` (x -1900..-1100, the piece nearest the van) is sunk by 203.5: `.prp` ZGEOM[2].y 0 -> -203.5. Its model is 403.5 high, so its top is the yard's floor (y 200) and what is left is a kerb with a 50 cm step down to the street (y 150) | GUESS: one piece is enough, and which one. A dumpster stands behind its east third (x -1454..-1200); x -1900..-1457 is free |
| `place_entities(Jn, ents, done)` | the same move in the `.gms` record (3 bytes of the file change); returns the entity's REF id | - |
| `cut_collision(hvk, refs)` | its static placement in the joined `.HVK` is replaced by a filler (a copy of another kept static placement with that one's MOPP code), exactly what `kl_hvk.remap` does for a map object that left: the list MOPP addresses static placements by position, so the count must not change (2,920 before and after, 1 shape record differs) | the filler is kl_hvk's own device, in every graft that ran live |
| `money_reach(Jn)` | the `TriggerBox2` of garage boxes 10 and 11 and of their loot: reach 80 -> 125 (4 values) | GUESS (4.1) |
| `repair(Jn)` | `open_wall` + `money_reach` | |

Not moved: the `.oct` room trees still list the wall with its old box (it is drawn or culled as
before, 2 m lower), the baked vertex light is the wall's old one. Not done: the roller doors (4.2),
HUD markers (kl_fa: 0 PointOfInterest), anything about the van.

Why sink and not remove: removing an entity renumbers slot ids (`.oct`, `.rmi`, list pool); a moved
one changes one float. Why not only cut the collision: the player would walk through a wall that
is still drawn. Why not move the collision down with it: a static placement's place is baked into
its MOPP code and the list code; under the kerb the two asphalt planes already meet at z -600.

### 5.2 For kl_graft.build
```python
if fa:
    kl_fa.repair(Jn, kept, log)
    esc = kl_escape.repair(Jn, log)                                   # after dm_rename / the second join
...
cut = kl_escape.place_entities(Jn, list(A.entities()), esc, log)      # before  gms, buf = A.write()
...
hvk = kl_escape.cut_collision(kl_hvk.join(...), cut, log).serialize()
```
`repair` opens nothing on a level that has none of the walls in `kl_escape.OPEN` (a Dog Days map,
M01); `money_reach` still runs. Until the lines are in, `kl_escape.applied()` patches the same three
places from outside (kl_fa.repair, kl_scene.Scene.write, kl_hvk.join), as kl_maps and kl_fa_author do.

### 5.3 The offline test (run 2026-10-09, twice)
`python tools/kl_escape.py test <scratch folder>` (1 to 2 minutes; builds through `KL_GRAFT_OUT`,
refuses the work folder's `build\install`):

- `kl_escape: SO0101_M03_Wall_Low_8m_05 sunk by 203.5`, `4 money-container triggers ... set to 125`,
  `collision of 1 entities taken out of the .HVK (placements by shape type: {1: 1})`
- `verify: problems: 0`; `kl_fa.check: 0 CRASH / BROKEN findings` (DEGRADED as before: spline van
  untested, no team / UCC spawns, no markers, no bots, 1 idle squad)
- built files: the node's y is -203.5, 0 placements left under its REF
- against the build in `<work>\build\install`: 28 of 31 members are byte-equal; `.gms` differs in 3
  bytes, `.prp` in 7, `.HVK` in one shape record (the file is 256 bytes longer: the filler's shape)
- walk test on the built `.HVK` from the yard: 138,113 cells, x -4870..5670, z -7550..2790;
  **30,365 inside `ExitTrigger_01`, 1,200 inside `BoardingTrigger_Car`** (before: 0 and 0)
- `RESULT: ok`

What the test cannot say: whether Dog Days' player takes the 50 cm step (it has
`ZFFPlayerMovementFall`; ASSUMPTION that walking off a kerb is like walking off any low edge), and
whether the kerb's missing collision shows (the feet sink into its last 25 units).

## 6. Route for the steering script

From `python tools/kl_escape.py test` / `route <archive>`: cheapest way over the walk test's cells,
kept 6 cells off anything, thinned to corners. y is the floor (feet). Up to the yard the way points
of RN10 stand (`<work>\build\klhook\live\RN10.ini`, its steps 92 - 112, ending at (-1244, -1243)).

```
; yard (f-live's way point by the west door) -> through the opened wall -> the van
goto -1250 -1250 110 12000 sprint keep        ; y 199
goto -1590  -790 110 12000 sprint keep        ; y 199   in front of the opened piece (free part x -1900..-1457)
goto -1590  -670 110 12000 sprint keep        ; y 199
goto -1590  -550 110 12000 sprint keep        ; y 149   the step down; z -625..-575 was the wall
goto -1590  -330 110 12000 sprint keep        ; y 149   INSIDE ExitTrigger_01 (z >= -540): the van is called here
goto  3110    10 110 12000 sprint keep        ; y 0     47 m east, downhill; inside BoardingTrigger_Car
; length 5744 units
```
- `ExitTrigger_01`: x -3592..4408, y -4..796, z -540..1460. Wait there with loot and watch the west:
  the van starts at (-8554, 161, 2660) and its spline passes (-1325, 157, 22) - 350 units north of
  the way point - on its way to (2970, 25, 41). How long it takes: not established.
- `BoardingTrigger_Car`: x 2852..3652, y -67..333, z -320..280; `PlayerAction` 'EnterVehicle',
  eOnly_Mercs, UA_FA_ESCAPE - hold E at the van. The escape camera box is x 1418..3656, z -584..776.
- from the garage (money box 11) the tool prints a second leg: (690, -6190) -> (650, -6310) ->
  (310, -6330) -> (110, -5710) -> (50, -4870) -> ... west door (-1150, -4770) -> (-1370, -4590) ->
  (-1590, -710) -> as above; 12,843 units.
- money boxes, where to stand (trigger node, reach after `money_reach`, nearest walk cell 40+ away):
  box 10 (424, 241, -6154) reach 125: **(390, -6130)**; box 11 (661, 241, -6155) reach 125:
  **(690, -6190)**; box 09 (857, 327, -6422) reach 145: (810, -6390); box 08 (894, 327, -6389):
  (850, -6350); box 07 (1064, 327, -6734): (1070, -6670); box 03 (-101, 327, -6275): (-50, -6270);
  box 02 (-91, 327, -6391): (-90, -6450); box 01 (-98, 327, -6314): (-50, -6290). Boxes 01-03 and
  07-09 hang 88 above the floor (y 327 against 239) with reach 145: untried live, try them too.

## 7. Not established

- Whether Dead Men's spline van drives in Dog Days when called (classes and layouts are equal, no
  stock FA level uses a ground car; kl_fa.check DEGRADED). First thing the live run shows.
- The exact rule of `ZFFPlayerMovementClimb` (which surfaces, the 81 / 47 beside the heights): only
  its height table was read. That the wall is climbed in a Dead Men round was not seen in the
  running game - it follows from the class, the heights, the sealed collision and the dressing.
- The meaning of `OnlineTriggerBox` field 5 / `TriggerBox2` field 6 (4.2) and of
  `OnlineMoneyContainer` field 1 (4.1).
- What the collision flags mean per bit (0x72 ground and walls, 0x108 hero-only, 0x66 fences,
  0x172 detailed props); nothing above depends on it.
- The walk test joins the yard and the garage but not the bank hall (y 800) or the plaza: the stairs
  between are outside what it models. f-live's nav-mesh way points cover that part.
