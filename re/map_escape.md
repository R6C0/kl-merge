# The escape vehicles of the four Dead Men Fragile Alliance maps under Dog Days

2026-10-10, agent t-van. OFFLINE: both executables, the four builds in `<work>\build\z_maps\M01 M02
M03 M06` (read, not changed), the 21 stock Dog Days levels. Nothing was installed, the game was not
started. Tool: `tools/kl_map_escape.py`. Repaired copies: `<work>\build\t_van\<map>`.
Status words: **seen** = read in the files / the executables with the command given, **ASSUMPTION**,
**not established**. NOTHING HERE RAN IN THE GAME.

Owner, after playing Late Night Opening (M02_FA_A): 'the late night van sometimes is a bit weird?
camera goes under the map when ur in it'.

**SUPERSEDED FOR THE THREE CAR MAPS (2026-10-10 evening, agent p-van): sections 8 - 13.** The owner, after
playing all four maps with AI heisters: 'the van is such a damn problem'. Dead Men's spline car is
no longer repaired, it is REPLACED by stock F07's key-framed van (the one Retomoto has, 'almost
perfect') on the road Dead Men's designers drew for their car. Builds: `<work>\build\y_van\M01 M02
M03`. Sections 1 - 7 stay true for M06 (helicopter) and as the record of what the car maps were.

## 0. Answers

1. **The camera is the fault, on all four maps, and it is one enum.** Aboard, Dog Days puts the
   eye of the escape camera at the world origin (0, 0, 0) instead of at the place Dead Men's
   designers chose (section 1). At the origin is: M02 the plane of the mall's atrium floor (eye
   0.0 over `Si0402_M02_FA_Floor_Atrium_A_Right_01`, 88 m from the car, looking away from the
   player), M03 104 UNDER the street, M06 100 UNDER the water, M01 outside the map. Repair: the
   camera's mode `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (5 cameras in 4 maps).
2. **The vehicle does not drive under the ground on any of the four** - this is not Retomoto's
   fault. Retomoto's van is key-framed (baked position keys, laid 40 too low). These are Havok
   physics cars on a spline; no route point is under the collision (lowest 0.9 over it, section 2).
   No route point was moved.
3. **'Sometimes weird' is not explained by anything measurable in the route.** Lanes are clear of
   static collision, there is no kerb on them, no prop in them. What IS known: no stock Dog Days
   level contains a `ZHavokCar`, a `VehicleMoveBehaviourRout` or an `OnlineVehicleOnSpline` - the
   three car maps run code the retail game never ran; and on M02 a second physics car (the police
   SWAT car) drives the same road through the escape van's stop (section 3). Cause **not
   established**; it needs a look in the game (section 6).
4. M06 (helicopter) is the stock form (`ZHeli` + `HeliFlyBehaviourRout`, as F02 F03 F06 F08); its
   route is 200 .. 3,935 over the ground. Only its camera had the fault.

## 1. The camera

### 1.1 What the level has (all four alike; `python tools\kl_map_escape.py check <folder>`)

```
EscCameraSetup!CameraTrigger01 [ZBoxPrimitive] @OnlineEscCamTrigger('', -> EscCamera01)     a box around the stop
EscCameraSetup!EscCamera01     [ZBoxPrimitive at (0, 0, 0), 10 x 10 x 10]
     @CCameraBox(ECP_NotSet, 0, 99999, 99999, 40, 0, 50, 0, 0, -> EscCameraSetup!CamPos01,
                 eFMC_Unbreakable, eFMM_LookFromPosFA, 1, 0, [], 0, eBOTH_PLAYERS)
EscCameraSetup!CamPos01        [ZBoxPrimitive]   the camera place: M02 (981, 235, -9104)
EscCameraSetup!EscCameraLAST   [ZBoxPrimitive at (0, 0, 0)] @ZSetZDefine 'FAEscCameraLAST'
     @CCameraBox(..., all -1, field 9 '', eFMC_AngleBound, eFMM_LookFromPosFA, 0, 1, ...)
```
M01 has two (`CameraTrigger01 / 02` -> `EscCamera01 / 02` -> `CamPos01 / 02`).

### 1.2 What the two executables do with it (seen; capstone, `debug\dasm.py`)

`CCameraBox` fields by member (init: kl2 0x8b5560, Dead Men 0x698ea0, vtable slot 13): +0x24 the
box's own node, +0x30 field 0, +0x34..0x48 the six floats, +0x50 field 9 (a node), +0x54 field 10,
+0x58 field 11 (the mode), +0x5c field 12 ('by message only': with 12 and 13 both clear the box is
registered as an area camera), +0x5d field 13 ('release'). The camera data handed to the player's
camera starts at +0x6c: [0] = the box's own node, [4] = field 9's node, mode at +0x180 (Dog Days) /
+0x170 (Dead Men).

| | Dead Men (kaneandlynch.exe) | Dog Days (kl2.exe) |
|---|---|---|
| enum EFMMode | NotSet 0, LookAtPos 1, LookFromPos 2, **LookFromPosFA 3** | NotSet 0, LookAtPos 1, LookAtKane 2, **LookFromPos 3, LookFromPosFA 4** |
| LookFromPosFA | 0x62da0d: `cmp [box+0x170], 3` -> the eye's place is overwritten with the place of **[box+4] = field 9** (CamPos01); the view stays on the player | 0x4471a1: `cmp [box+0x180], 4` -> eye = place of **[box+0] = the box's own node**, direction built from it to the place of [box+4] (field 9) |
| LookFromPos | - | 0x447240: `cmp [box+0x180], 3` -> eye = place of **[box+4] = field 9**, direction to `[camera+0x540]` = the player |
| LookAtPos | - | 0x4472dd: eye = the player's place + offsets, looking at field 9 |

The level files store the enum by NAME, so the conversion keeps `eFMM_LookFromPosFA` - and the
name changed its meaning between the games. How the stock levels use the two modes (census of F01
.. F09 and L00 .. L11, read-only):

- `eFMM_LookFromPosFA`: 60 boxes, every one with the camera AT the box and field 9 the thing looked
  at: `...SpawnCam_000_A!Camera_000_A` at (10840, 627, 2811) -> `CameraLookAt_000_A`; F02
  `Escape!EscapeHelicopter_01\CameraOutside_01` at (-1999, 7165, 2777) -> the helicopter.
- `eFMM_LookFromPos`: 18 boxes (F01 6, F04 F05 F07 F09 3 each), all the escape vans' outside
  cameras, e.g. F07 `...\EscCamera_01\EscCamera01_02` (the box at (0, 0, 0)) -> `...\CamPos01`,
  floats (0, 99999, 99999, 40, 0, 50), field 12 = 1, `eFMC_Unbreakable`. **This is Dead Men's
  camera, field for field, in the mode Dog Days gives that meaning.**

When it fires (kl2 0x5cd430, `ZOnlineEscCamTrigger` slot 25, the branch for an empty field 0): for
each of the two local players it asks the rules object three questions about the player's id and
then tests the PLAYER's own place against the trigger box; inside -> 0x68f440 sends the camera box
its message. So: aboard and inside `CameraTrigger01`, the eye jumps to (0, 0, 0). What the three
questions are was not read (ASSUMPTION from the owner's words and the stock helicopter boxes in the
sky: 'this player is in the escape vehicle').

`EscCameraLAST` is not the fault and is not changed: kl2 0x7b68d0 / Dead Men 0x5eac60 (the same
routine in `ff2\characters\ffplayer.cpp`) look the define `FAEscCameraLAST` up and send its box
'AITrigger'; a box with field 13 set answers by RELEASING the fixed camera (kl2 0x68a410 ->
0x55e6c0), it places nothing.

### 1.3 Where the eye is, before and after (`<work>\build\t_van\<map>\escape.txt`)

| map | camera | before: Dog Days' eye | after: eye | over the ground | to the vehicle's stop |
|---|---|---|---|---:|---|
| M01 | EscCamera01 | (0, 0, 0): **outside the map**, no collision above or below; 216 m from the stop | CamPos01 (4049, 525, 19453) | 526 | 25 m, clear |
| M01 | EscCamera02 | (0, 0, 0): the same | CamPos02 (1803, 210, 27410) | 226 | 80 m (it films the road out, not the stop) |
| M02 | EscCamera01 | (0, 0, 0): **0.0 over the atrium floor**, 88 m from the stop, through the atrium's plants | CamPos01 (981, 235, -9104) | 235 | 16 m, clear |
| M03 | EscCamera01 | (0, 0, 0): **104 under** `SO0201_M03_Road_Asphalt_Slope_36mx20m_02` | CamPos01 (1576, 328, 407) | 290 | 15 m, clear |
| M06 | EscCamera01 | (0, 0, 0): **100 under** `water_plane_01` | CamPos01 (245, 1819, -279) | 1716 | 64 m, clear |

'Clear' = no static collision triangle between the eye and a point 1 m over the route's last point.

### 1.4 The repair

`kl_map_escape.fix_cameras`: a `CCameraBox` that an `OnlineEscCamTrigger` names, with mode
`eFMM_LookFromPosFA`, its own node within 1 of the origin and field 9 naming a node that is not:
field 11 = `eFMM_LookFromPos`. Seen in the written files (token-level comparison of the two .prp):
one enum per camera differs, one key (`eFMM_LookFromPos`, 17 bytes) is added to the key table;
15,000 / 21,935 / 19,828 / 15,600 nodes otherwise equal. A camera box that stands somewhere (a
Dog Days one) is not touched.

Not done, and why: moving the box to CamPos01 and keeping the FA mode would put the eye right but
keep it looking at field 9 (itself) instead of at the player.

## 2. The routes against the ground

A route is a `ZEditorSpline` under `VehicleMoveBehaviour_Incomming / _Escaping` (M06: `Incomming` /
`Escaping`), named by `OnlineEscHavokCar` fields 0 and 1. Raw field: 12 bytes (tag `WP01`, point
count, 1), then 24 bytes a point = x, y, z in the spline node's frame, an angle, 10.0 and four bytes
of 0xcdcdcdcd; after the points comes editor heap memory. Ground = a vertical ray on the map's
`.HVK` collision (static and key-framed non-convex shapes of entities below `Locations/`; the ten
`Projectile_*` template shapes that lie at the origin are left out).

| map | vehicle | route | points | length | points over ground | lowest on a straight walk between the points |
|---|---|---|---:|---:|---|---|
| M01 | ZHavokCar VAN, origin 6.5 over the ground where parked | incoming | 15 | 75 m | 3.2 .. 29.2 | 3.2 |
| | | escaping | 18 | 229 m | 4.0 .. 54.4 | 4.0 |
| M02 | ZHavokCar VAN, 5.5 | incoming | 12 | 151 m | 3.6 .. 11.6 | 3.6 |
| | | escaping | 14 | 191 m | 0.9 .. 35.3 | 0.9 |
| M03 | ZHavokCar VAN, 11.2 | incoming | 9 | 120 m | 7.1 .. 26.3 (the stop: 25.7) | 1.8 (on the slope) |
| | | escaping | 8 | 87 m | 6.7 .. 34.3 | 6.7 |
| M06 | ZHeli | incoming | 11 | 180 m | 202 (the stop) .. 3,935 | 202 |
| | | escaping | 17 | 254 m | 224 .. 3,638 | 200 |

Every point with its ground is in `escape.txt` (BEFORE and AFTER are equal: no point moved).

- No point under the ground, none nearer than 0.9. M02's ground is flat y 0 along both routes.
- The points float 1 .. 54 over the road with no pattern (M03's van stop is 25.7 up, a route point
  on M01 is 54 up beside one 9 up). A vehicle laid on those heights would hop; Dead Men drove them.
  With the class names this says the heights are not what places the car: both executables link
  Havok's vehicle kit (`hkVehicleInstance`, `hkVehicleWheelCollide`, `ZHavokVehicleInstance`), the
  car's `.HVK` shape is type 3 (vehicle) placed relative to its entity, and Dead Men's
  `ZOnlineVehicleOnSpline` message handler (0x75c300) resets a rigid body's place, rotation and
  velocity. ASSUMPTION: the car is steered along the spline in x / z and stands on its wheels. The
  steering routine itself (`ZVehicleMoveBehaviourRout`, kl2 slot 14 0x7cdb00) was not read through.
- The lanes: five rays across a 2 m body every 50 units - nothing of the static collision stands
  25 .. 170 over the ground in any car lane; no step of the ground over 25; no rigid prop, no other
  vehicle parked in a lane.
- Level bounds: every car route passes through one `LevelBound` box on the way in and one on the
  way out (M02: `LevelBounds!LevelBound_Street!Bound`, 1,089 .. 1,352 along the escaping route,
  with the players aboard). The same in Dead Men's own game; `ZLevelBound`'s tick has the same
  shape in both executables (kl2 0x62e1b0, Dead Men 0x6ba240). Whether a passenger is warned or
  ended there in Dog Days: **not established**.

`--level` (off by default) puts points more than 30 over the ground down to the car's own height;
`fix_heights` always lifts a point that is UNDER the ground. Neither changed anything here.

## 3. What could make the car 'weird' (none of it proven)

1. **Code no stock level runs.** Census of all 21 stock Dog Days levels: 0 `ZHavokCar`, 0
   `VehicleMoveBehaviourRout`, 0 `OnlineVehicleOnSpline`. Dog Days' own
   escape cars are key-framed (`OnlineEscAnimatedVehicle`), its helicopters `ZHeli`. The classes
   are in kl2.exe with Dead Men's layouts and the same `EVehicleType` enum ('VAN' = 2 in both), but
   Dog Days' retail game never drove one. One difference seen: Dead Men's `ZOnlineVehicleOnSpline`
   overrides the per-frame slot 25 (0x75c500; read once: on the host, on a timer, it compares the
   body's place with a stored one and acts past a limit); Dog Days' class leaves slot 25 the base's
   empty one. Not followed further.
2. **A second physics car on the same road (M02).** `AIEnemies!PoliceSwats\PoliceCar_01` (called
   by `Triggers!PoliceSwats_01_Trigger`, an `OnlineTriggerBox` inside the mall) drives a route that
   is within 250 of the escape van's incoming route for 111 of its 151 m and passes about 3 m from
   the van's stop on its way to (-1691, 24, -6920). If it is on that road, or wrecked on it, when
   the van comes, two Havok cars meet. That would be 'sometimes'. M03: the `EscSquad` police car
   shares 61 m of the van's escaping road. M01: the cement truck's route runs within 250 of the
   escaping route from 87 to 182 m along it.
3. The level bound the van crosses with the players in it (section 2).

## 4. The tool

```
python tools\kl_map_escape.py check <build folder>          the tables; exit 1 on a FAULT
python tools\kl_map_escape.py fix <build folder> <out>      copy + repairs, BEFORE / AFTER, <out>\escape.txt, escape.json
python tools\kl_map_escape.py all <folder of builds> <out root> [M01 ...]
```
A FAULT is: a route point under the ground; a camera eye outside the map, under it, or within 50
of the floor under it. `fix` changes the .prp member only (it refuses anything else: the member
lists are compared by CRC), keeps every other member's bytes, name, order, time stamp and packing
method, copies the files beside the archive, and records itself in the folder's `steps.json`
(`escape: [.prp]`, `final` = the new member list) so that `kl_maps.py audit` still knows the folder.
It uses kl_fa (load, edit), kl_maps (world frames, member ids), kl_hvk, kl_scene - nothing of
kl_fa_van: that one rewrites key tables of a key-framed van, and these vehicles have none.

## 5. Result (2026-10-10, `<work>\build\t_van\run.log`, `<map>.audit.log`)

| map | cameras changed | route points moved | check faults before -> after | .prp bytes | `kl_maps.py audit` | content id |
|---|---:|---:|---|---|---|---|
| M01 | 2 | 0 | 2 -> 0 | 3,109,877 -> 3,109,894 | PASS (1 known) | `316ade5a2f` |
| M02 | 1 | 0 | 1 -> 0 | 4,642,089 -> 4,642,106 | PASS (6 known) | `cd06c6458f` |
| M03 | 1 | 0 | 1 -> 0 | 4,259,788 -> 4,259,805 | PASS (0 known) | `6f5cbac295` |
| M06 | 1 | 0 | 1 -> 0 | 3,123,108 -> 3,123,125 | PASS (6 known) | `53f8522e9f` |

Budget, bytes, before = after on every map (only the .prp member differs; nothing was added):

| map | .prm | .ANM | .fxc | F01_Main.WAV beside |
|---|---:|---:|---:|---:|
| M01 | 55,088,000 | 22,061,764 | 17,760,648 | 21,722,704 |
| M02 | 54,619,216 | 22,202,472 | 17,760,648 | 22,527,568 |
| M03 | 60,469,040 | 22,202,616 | 17,760,648 | 22,716,752 |
| M06 | 49,585,744 | 21,642,576 | 17,760,648 | 21,775,744 |

No chunk was added to any .prm (chunk-table entries unchanged).

## 6. For the lead

- Live check C1 (one variable): `<work>\build\t_van\M02` in the slot, board the car, watch where
  the camera goes. Expected: a fixed view from 2.4 m up at (981, 235, -9104), 16 m from the car,
  following the player as the car leaves; released at the end by `EscCameraLAST`.
- What to watch for the 'weird' part, since it cannot be found offline: is the police SWAT car on
  the car park road when the van arrives; does the van hop or slide while standing; does anything
  happen at the level bound 11 .. 13 m into the drive away.
- This step is not in `kl_maps.ready_one`. Wanted there (kl_maps.py is not mine): after the
  wardrobe step, `kl_map_escape.repair(final, out)`; or `kl_map_escape.fix_cameras` on the joined
  scene inside `kl_fa.repair` (kl_fa.py is not mine either) - the test is the same, it needs only
  world places. `kl_maps.audit` prints 'lighten changed ..; the wardrobe changed ..' from
  steps.json; a third clause for `escape` would show this step.
- `kl_fa.check` could carry the camera test as a finding (a `CCameraBox` in `eFMM_LookFromPosFA`
  standing at the origin and named by an escape camera trigger = BROKEN).
- Retomoto is not affected: its van and its cameras are F07's (`eFMM_LookFromPos`, moved with the
  van by kl_fa_van).

## 7. Not established

- Everything in the running game: nothing here was loaded.
- The three rule questions of the camera trigger (1.2); what `eFMC_Unbreakable` and the six floats
  do (they are stock F07's values).
- How `ZVehicleMoveBehaviourRout` steers, and what Dog Days does where Dead Men's
  `ZOnlineVehicleOnSpline` corrected the car each frame (3.1).
- Whether a level bound acts on a passenger (section 2).
- The curve the engine lays through a route's points (the corridor check walks straight lines).

---

# Part 2 (2026-10-10 evening, agent p-van): the key-framed van in place of the spline car

OFFLINE: stock F07, the builds `<work>\build\t_maps2\M01 M02 M03` (read), both tools' sources. Nothing
was installed, the game was not started, nothing was written into the Dog Days folder.
Tool: `tools/kl_map_escape.py van / van-plan / van-check / van-keys`. Builds: `<work>\build\y_van\M01
M02 M03` (+ `van.json`, `van.txt`, `<map>.van.log`). **NONE OF IT RAN IN THE GAME.**

Owner, after rounds on the four maps with AI heisters: 'the van is such a damn problem'. Earlier,
Late Night Opening: 'the late night van sometimes is a bit weird'. Retomoto (stock F07's key-framed
van on a rewritten drive, `tools/kl_fa_van.py`): 'almost perfect'.

## 8. Answers

1. **Keeping F07's animated van IS possible on all three car maps, and it is built.** So the spline
   car was not repaired in kl2.exe (the task's fall-back): no map needs it. Dead Men's escape car,
   its two routes, its boarding box, its BOARDS trigger and its escape cameras are LEFT OUT of the
   three maps; no `OnlineEscHavokCar`, no escape `ZHavokCar` is in them any more (the police cars
   and M01's civilian cars, which are also spline cars, are not this job and stay).
2. **A van's drive is not limited to straight legs.** The key tables are decoded (section 9): every
   key has a place AND a heading, so the van can follow any curve. What is fixed without rewriting
   the four index tables is the timing: 7.2 s in, 8.48 s away, with the baked ease in and out.
   `kl_fa_van`'s 'straight lane only' was a choice (all rotation keys = identity), not a limit.
3. **The route on each map is the road Dead Men's designers drew for their car** (their two spline
   routes joined into one smooth curve): the lane is already known to be the road, and it is
   tested again every 20 units for the van (section 10). The van's REAR box - where one boards -
   stands where Dead Men's car stopped.
4. M06 (helicopter) is untouched: no fault found beyond the camera of section 1, which
   `t_maps2\M06` already has repaired.

## 9. What the files say (seen; `python tools\kl_map_escape.py van-keys`, the dumps in `van.txt`)

### 9.1 Why the graft dropped the van, and what Retomoto did to keep it

`kl_graft.build` keeps the systems level's SYSTEMS subtrees and, of its map side, only the names in
`Select(s_keep=...)`. `kl_fa.host_keep` puts there the position-free plumbing (briefing trigger,
`Gameplay!AIMonitor`, `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor`, speakers, single timers).
`Animation/F07/F07_Escape_Vehicle_0n.zip` (223 nodes each) counts as F07's MAP and goes with it.
Retomoto keeps it because `kl_graft.build(author=True)` adds `kl_fa_author.KEEP` = `FASpecials!`,
`Specials!`, `Gameplay!EscapeSetup!*` and the three van archives, re-places them on the stock
`Level` BEFORE the graft (`prepare_host`, then `kl_fa_van.straighten`) and wires them after the
join. That path is Retomoto's own (campaign squads, tower places); it is not used here. This
module patches four things in from outside for the length of one build, as `kl_escape.applied`
does: `kl_fa.host_keep` (+ the van's archive and `Gameplay!EscapeSetup!RelayDestroyedEsc_01`, the
relay the kept monitor's list 3 names for van 1), `kl_graft.Level` (the van is laid out on stock
F07 as soon as it is read), `kl_fa.repair` (then the exit triggers are pointed), `kl_hvk.join`
(then the collision placements), and `kl_maps.READY[<map>]['m_drop']` (Dead Men's objects left out).
No file of another agent is edited.

### 9.2 The van (stock F07, `Animation/F07/F07_Escape_Vehicle_01.zip`)

```
EscapeVehicle_Animation_F07 [ZGROUP at the origin] @OnlineEscAnimatedVehicle(boarding box, 'Activate_Enter', 'Activate_Exit',
        'Activate_Crash_01..04', 144, 230, 355, 444, proxy node, van, F07_EscapeVan_01, 7.2, 8.0, 8.48, 6.0)
  F07_Escape_Vehicle_01 [ZGROUP] 6 x @MatPosAnimProxy: Activate_Enter = frames 50..230, Activate_Exit 273..485,
                                   Crash_01 500..562, Crash_02 600..632, Crash_03 650..709, Crash_04 750..795
    V_Van_00 [ZGROUP] @MatPosAnim + KEYS chunk        the body; nose = local +Z
      Body\Body_Main ... @RelayAnimatedVehicleHit, @FakeTarget('Mercenary')    police shoot it; it can be destroyed
      BoardingTrigger [box 95 x 135 x 80 at (-1, 119, -337)] @PlayerAction('EnterVehicle', eONLY_LYNCH, UA_FA_ESCAPE)
      KillBox [at the nose], doors, wheels, Audio_* (9 sounds of F07's bank)
    BoardingCar @OnlineGamePlayTrigger(eOGPT_PLAYER_BOARDS)
    PathBlockerVan, TriggerBox_RearDoors_Open, Timer_10sec, relays
  EscCamera_01: CameraTrigger_InVan -> EscCameraInVan_01 (eFMM_LookAtPos -> CamPos_InVan_FocusPoint),
                CameraTrigger01 -> EscCamera01_01 (eFMM_LookFromPos -> CamPos01); both triggers name the vehicle in field 0
  F07_EscapeVan_01 [ZAnimatedVehicle]
V_Van_Reflection (31 low-detail pieces) at (-449, 0, 0), 8 x Smear_*, 2 x ShadowCaster_Van at (+-88, 74..102, +-250)
```
Named from outside the archive by two things only: the exit trigger (fields 2..4) and the relay.

### 9.3 The key tables (the part `kl_fa_author.van_path` left 'not decoded')

The KEYS chunk of `V_Van_00`: 'SYEK', 0x30, 796 frames, 0, 795, 1, six offsets into the .buf head.

| table | what | form |
|---|---|---|
| 5 | 563 positions | 3 floats a key, in the node's local space (every parent is identity at the origin) |
| 2 | 550 rotations | 4 x int16 / 32767 = quaternion x y z w |
| 3, 0 | for every FRAME the index of its position / rotation key | first byte = bits a value (10), then the values packed most significant bit first |
| 4, 1 | for every key its frame (+1) | the same packing |

- The yaw of local +Z from a rotation key (the usual quaternion formula) is the tangent of the
  positions: frame 100: yaw 101.1, tangent 104.3; 150: 103.7 / 104.0; 400: 1.3 / 2.0. It lags the
  bends by 0..3 degrees and leads by up to 8 at the end of the drive away. Pitch and roll parts
  are small (up to 1852 of 32767): the body's sway.
- 25 frames a second: `Activate_Enter` 180 frames = 7.2 s and `Activate_Exit` 212 frames = 8.48 s
  are the controller's own fields 14 and 16.
- Frames 0..49 the van waits at key 0; 50..230 it drives 5,063 units; 230..273 it stands (12 keys
  within 2 units); 273..485 it drives 7,019 units (top step 53 units a frame = 13 m/s).
- Crash pieces start where the drive is at frames 144, 230, 355 and 444 - the controller's fields
  7..10: which piece plays depends on how far the van had come when it was destroyed.
- **Rotation keys are interpolated (ASSUMPTION, strong):** 19 rotation keys of the drive serve 3..6
  frames while the van turns. Each of them and its successor sit on the tangent at their OWN first
  frames (with the same lag), and the straight run from one to the other at the middle frame is
  the tangent there within 0.2 degrees in all 19 (`van-keys` prints the table; key 264: yaw 43.9 ->
  35.0 over 6 frames, tangent 47.1 / 42.6 / 38.1, run at the middle 39.4 against 39.5). A key held
  for six frames would snap the van by 9 degrees in stock F07. So a rewritten key gets the heading
  of its own first frame. If the engine does NOT interpolate, the nose is up to 5.7 / 10.7 / 12.1
  degrees off for a frame or two in a bend (M01 / M02 / M03; `van-check` prints both numbers).

## 10. What is built

### 10.1 The plan (`van_plan`, on `<work>\build\t_maps2\<map>`, which still has the car)

- Dead Men's incoming route + its escaping route (points nearer than 150 to the stop left out) ->
  one centripetal Catmull-Rom curve through every point, sampled every 20 units. ASSUMPTION: not
  the curve Dead Men's engine laid through the points (not read); the lane test walks THIS curve.
- The road under it: the map's collision (`Ground`), smoothed over +-100 units (a kerb must not
  make the van hop). The van's origin is 2 over the road, as F07's keys are over F07's road.
- The stop = 337 past the place Dead Men's car stopped (so the boarding box, 337 behind the van's
  origin, stands there). The drive in is the last 60 m before it, the drive away at most 80 m
  (both GUESSES: F07's own are 51 m and 70 m, Retomoto's away is 102 m on a straight road).
- The drive away ends 900 before anything Dead Men's car switched on its way (M01: the fence gate
  `SO1001_Fence_A_5m_AnimGroup_00`, opened by `Escape!EscapeCars\GateTrigger` for the CAR - a van
  does not open it), and before anything in the lane.
- The lane: every 20 units, five rays across 220, from 350 behind the waiting place to 600 beyond
  the end: road within 25 of the drive's height under every ray, no collision of the map 25..220
  over it, no convex body (prop, parked car, key-framed piece). All three: clear, nothing cut.
- The camera place = the designers' `EscCameraSetup!CamPos0n` nearest the stop.

### 10.2 The van's keys (`van_prepare`, on stock F07 before the graft)

No key is added, dropped or re-timed; tables 0 / 1 / 3 / 4 are not touched.
- A key of the drive keeps its share of its leg (so the van's speed profile is the baked one,
  scaled): drive in x 1.18 on all three, away x 0.74 (M01), 1.14 (M02), 1.14 (M03).
- A crash key keeps its distance along the drive and its offset to the side, clamped to +-120.
- A rotation key: heading = the chord of the new drive from the rear axle to the front one (+-140)
  at the key's own first frame; F07's baked lead / lag is NOT carried over (on another bend it
  would be a slide); a crash key keeps its angle to the drive; the sway (pitch / roll) is kept.
  M03's road falls 150 over 43 m (2 degrees): the van is NOT pitched to it (wheels up to ~9 off).
- Rigid with the stopped van: `PathBlockerVan`, `CameraTrigger_InVan`, `CamPos_InVan_FocusPoint`.
  On the drive at their own distance from the stop: `TriggerBox_RearDoors_Open` (4.9 m before),
  `CameraTrigger01` (8.5 m after). `CamPos01` = Dead Men's camera place; `EscCamera01_01` beside it.
- The loose pieces of the archive (`V_Van_Reflection`, `Smear_*`, `ShadowCaster_Van*`: no
  controller, no reference of any kind in F07, not hidden, lying at F07's world origin) are put
  at y -60000. In F07 the origin is outside the map; in M02_FA_A it is the atrium's floor.

### 10.3 The joined level

- `Select(m_drop=...)`: M01 `Escape!EscapeCars` (36 nodes), `EscCameraSetup!EscCamera01/02`,
  `CamPos01/02`, `CameraTrigger01/02`, `Triggers!BoardingTrigger_Car`, `Triggers!BoardingGameplayTrigger`;
  M02 / M03 `EscapeSetup!EscapeCars` (31), the three camera objects, the two triggers.
  `EscCameraSetup!EscCameraLAST` (the define `FAEscCameraLAST`, which releases the camera) stays.
  Node counts: 15,000 -> 15,180, 21,935 -> 22,123, 19,828 -> 20,016 = + 224 - 44 / 36 / 36 exactly.
- Exit triggers (`Triggers!CallExitVehicle_01 / _02`, `Triggers!ExitTrigger_01`: Dead Men's own
  boxes, where they were): field 0 = 0, field 2 = `ROOT\Animation/F07/F07_Escape_Vehicle_01.zip\EscapeVehicle_Animation_F07`.
- `.HVK`: the 9 static placements of the reflection template (and the 1,748 filler copies of one
  of them that `kl_hvk.join` puts where F07's map was) are cut (`kl_escape.cut_collision`); the 5
  key-framed placements of the van's parts are put at the waiting place (ASSUMPTION that the game
  moves them with the entity anyway - Retomoto's were left at F07's place; here the file is right
  either way).
- Then `kl_graft lighten`, `kl_chars wardrobe` (kl_maps.ready_one, unchanged) and
  `kl_map_tune.build` (guns, escape, ai) as on every delivered map.

### 10.4 Per map (world units, 100 = 1 m; heading = degrees from +z towards +x)

| | waits | drive in | stops | boarding box | drive away | ends |
|---|---|---|---|---|---|---|
| M01 diner | (8405, 2, 16687) heading -8, in the back alley, beyond `LevelBound_back` | 60 m in 7.2 s, north up the alley, left round the corner | (5829, 2, 20648) heading -98 (west) | (6163, 0, 20696) = where the car stopped | 52 m in 8.48 s (top 13 m/s): west, then right | (1441, 2, 22179) heading -1, 9 m before the gate's trigger box, 15 m before the fence |
| M02 Late Night Opening | (1116, 2, -12896) heading -25, on the car-park road, beyond `LevelBound_Street` | 60 m in 7.2 s, north, then left in front of the mall | (-793, 2, -9009) heading -150 | (-625, 0, -8717) | 80 m in 8.48 s (top 17 m/s): south down the car park, right onto the street | (-4947, 2, -13485) heading -88 (west) |
| M03 bank | (-2555, 152, 558) heading 129, on the upper road west of the yard | 60 m in 7.2 s, east, down the slope | (3305, 2, 3) heading 95 (east) | (2970, 0, 34) | 80 m in 8.48 s (top 17 m/s): east, then right | (10289, 2, -1102) heading 172 |

'top' = the largest step between two keys x 25. The compass words are read off the coordinates
(+z called north), not off a picture of the map.
Level bounds the drive passes (a strip across the road; tested at chest height): M01 35 m before
the stop (empty van); M02 38..36 m before (empty) and 15.4..18.4 m after (PLAYERS ABOARD); M03
15.9..17.6 m after (players aboard). Dead Men's car passed the same strips. Whether a passenger
of a key-framed van is warned or ended there: **not established** (live check V5).
Other spline cars on the same road, as before: M02 the police SWAT car (the van's drive in, 56 m
of it), M03 the `EscSquad` police car (the drive away). ASSUMPTION: a key-framed van is not pushed
off its drive by them (it is not a physics body); it pushes them.
Camera: M01 (4049, 526, 19453), 22 m from the stop, clear sight to the stop and to the end; M02
(981, 235, -9104), 18 m, clear to the stop, the end is behind plant pots; M03 (1576, 328, 407),
18 m, clear to the stop, the end is behind `SO0301_M03_BuildingYellow_Small_A_02`.

### 10.5 What the owner will see (expected; nothing of it was seen)

The van stands at its waiting place from the round's start (M01 and M02: outside the level bound,
M03: up the road). When a crew member enters the map's own exit box the van drives in for 7.2 s
on the road, with F07's van sounds, and stops with its REAR towards the way it came; the rear
doors open as it arrives. 'Get in' is offered at the rear doors (the box rides on the van), not at
a box lying in the road beside a car. Aboard: the in-van camera, then - 8.5 m into the drive away -
the fixed camera the map's designers placed, following the van out for 8.48 s. It is not a
physics car: it cannot hop, slide or stop short of its place. Police shoot at it (stock:
`FakeTarget`); destroyed, it plays one of F07's four crash pieces on the same road.

## 11. Checks (all on the WRITTEN folders)

| | M01 | M02 | M03 |
|---|---|---|---|
| `kl_graft.verify` | problems: 0 | problems: 0 | problems: 0 |
| `kl_maps.py audit` | PASS (1 known) `54c80cb398` | PASS (6 known) `b37791938b` | PASS (0 known) `57dee29f9e` |
| `kl_maps.preflight` | CRASH 0, RISK 0 | CRASH 0, RISK 3 (as the source) | CRASH 0, RISK 0 |
| `kl_impact.py` | problems: 0 | problems: 0 | problems: 0 |
| `kl_map_guns.py check` | problems: 0 | problems: 0 | problems: 0 |
| `kl_map_escape.py check` (with `van-check`) | 0 faults | 0 faults | 0 faults |
| `kl_map_tune` (all its checkers) | PASS | PASS | PASS |
| `kl_fa.py check` | the DEGRADED 'vehicle ... ZHavokCar driven along a spline ... UNTESTED' finding is gone; the rest as the source | same | same |
| `kl_fa_bots.py check` on the folder as built | FAIL 3: there are no bots yet (`t_maps2\M01` gives the same 3) | same | same |
| trial: `kl_fa_bots.py build --park ...` then `check` (folder removed again; `_bots_<map>.log`) | PASS 0 FAIL, 1 NOTE | FAIL 7: the glass-case finding, which `u_maps\M02` gives too with today's kl_fa_bots - not the van | PASS 0 FAIL, 8 NOTE (as `u_maps\M03`) |

`van-check` per map: the exit triggers name the van alone; no escape `OnlineEscHavokCar`; one
boarding action (the van's); no camera trigger outside the van; the van's group at the origin; every
key of the drive within 6 of 'road + 2' (0.0 / 0.0 / 1.1); the lane clear; the nose within 6 degrees
of the chord (1.2 / 2.7 / 1.2 interpolated); crash pieces within 120 of the drive and not under
the ground; the node at its first key; `PathBlockerVan` at the stop; the stop inside
`CameraTrigger_InVan`; the drive 8.5 m on inside `CameraTrigger01`; the rear-door box on the drive;
the camera eye over ground; no static collision placement of the van's subtree; the 5 key-framed
ones within 1.1 of their entities; no loose piece in the map.

Budget, bytes, `t_maps2` -> `y_van` (each a single block; chunk table: 69,632 usable):

| | .prm | .ANM | .fxc | F01_Main.WAV | chunk-table entries | .TEX (not a single block) |
|---|---|---|---|---|---|---|
| M01 | 55,917,968 -> 56,992,176 (+1.07 MB) | 22,061,764 -> 22,039,292 | 17,760,648 = | 21,722,704 -> 21,145,936 | 50,254 -> 49,973 | 242.7 -> 246.4 MB |
| M02 | 55,449,184 -> 56,522,544 (+1.07 MB) | 22,202,472 -> 22,180,036 | 17,760,648 = | 22,527,568 -> 22,113,616 | 58,583 -> 58,300 | 224.3 -> 228.0 MB |
| M03 | 61,299,008 -> 62,581,504 (+1.28 MB) | 22,202,616 = | 17,760,648 = | 22,716,752 -> 22,669,648 | 62,892 = 62,892 | 225.9 -> 237.6 MB |

The .prm grows by the van's model less the car's; .ANM and .WAV shrink because the car's animation
sets and sounds are no longer named. CONTROL: `kl_maps.py ready` + `kl_map_tune.py build` of M03
WITHOUT the van, run today, gives t_maps2\M03's sizes exactly and the same bytes in every member
but the .prm (same size, other CRC; `tools/kl_chars.py` has uncommitted changes) - so the tools
have not drifted in anything that is counted here; the y_van builds are made with today's tools.

## 12. For the lead

- Rebuild: `python tools\kl_map_escape.py van <work>\build\t_maps2 <work>\build\y_van [M01 M02 M03]`
  (2.5 min a map). Install as any tuned map: `python debug\slot.py put <work>\build\y_van\M02 F01`.
- **AI heisters: pass `--park x,y,z` to `kl_fa_bots.py build`.** `kl_fa_bots.stations` takes the
  boarding action's place from the FILE; the van's box rides on the van, so in the file it stands
  at the WAITING place (M01 (8453, 121, 16353), 49 m from the stop). Without `--park` the bots end
  at the mesh point nearest to that. Values (= `van.json` plan.board): M01 `--park 6163,0,20696`,
  M02 `--park -625,0,-8717`, M03 `--park 1967,220,-1073` (M03: the bots' side of the yard wall,
  the place `u_maps\M03` had). `--park` puts an AllyEscapeBox there (the bots vanish into the van's
  place when it is in state 3 / 4). The tactic form (`--ally-box off`) needs the van's live box on
  the mesh at the stop: the mesh has a place within 400 of all three points; whether the tactic
  takes a box that MOVED there was not read. (`kl_fa_bots_rt.py` already knows a boarding action
  that is a child of a waiting van, for Retomoto.)
- No hook code, no ini key: the van is data.
- `kl_map_tune`'s 'escape' step still runs on these folders (it finds nothing to change); its
  check lists the van's inside camera apart (`cameras_no_eye`) because kl_map_tune prints every
  camera by its eye.
- Not done, could be: F07's HUD marker `FASpecials!POI!POI_TheEscapeArea` at the stop (kl_fa.check
  'markers' stays DEGRADED), F07's escape music (`Specials!Audio!EscSoundHandling!*`), a second and
  third van (the archive names differ only in the digit; a second lane is needed), M01's gate
  opened for the van so that it can leave by the street, re-timing (tables 0 / 1 / 3 / 4).

## 13. Live checks, in order (one variable each; what proves it)

Differences from Retomoto's van, which is the only key-framed van seen live on a grafted map:
real headings in the rotation keys (Retomoto: all identity), a curved drive, key-framed collision
placements moved, the reflection template's collision cut and its pieces put away, one van kept of
three, Dead Men's exit boxes instead of F07's, the camera on a Dead Men place.

- **V0 load**: `y_van\M01` in the slot, `kl_autotest`. Proof: `RESULT: clean exit`, first frame.
- **V1 the van stands right**: at the round's start go to the waiting place (M03's is the one
  inside the bounds: (-2555, 152, 558)). Proof: a picture of the van on the road, wheels on the
  ground, nose along the road. If it stands sideways or backwards, the yaw sign is wrong (one
  place: `VanKeys.turned`).
- **V2 it comes**: enter the map's exit box. Proof: KLHook.log / pictures of the van arriving in
  7 s and standing at the stop of 10.4; no fault at the `PathBlocker` on Dead Men's mesh.
- **V3 boarding**: at the rear doors, hold the use key. Proof: 'You jumped into the getaway car'.
  The box is `eONLY_LYNCH` in stock (as on Retomoto, where the owner boarded).
- **V4 the drive away and the camera**: Proof: pictures - in-van view, then the fixed camera of
  10.4 following the van; the round's score page.
- **V5 the level bound** (M02, M03): the van passes one 15..18 m into the drive away with the
  players aboard. Proof: no 'leaving the area' warning, no death, in V4's run on M02.
- **V6 it is shot**: let the police destroy it at the stop. Proof: the crash piece plays on the
  road, the round goes on as it does in stock F07 with its vans.
- **V7 with bots** (after the lead's bot step with `--park`): bots reach the box and are gone
  with the van; none stands in the van's lane (its `KillBox` kills what it runs over).

## 14. Not established (part 2)

- Everything in the running game.
- That the game interpolates rotation keys (9.3) and moves key-framed bodies with their entity (10.3).
- What `OnlineEscCamTrigger` tests when field 0 names a vehicle (ASSUMPTION from F07's boxes: the
  VEHICLE with a player aboard inside the box), and what `OnlineEscAnimatedVehicle` fields 15 and
  17 (8.0, 6.0) are.
- How long the van waits at the stop and what happens after it is destroyed when it is the only
  vehicle of the level (the rules; Dead Men's maps had one car too).
- Whether a `PathBlocker` on a converted Dead Men mesh behaves as on Retomoto's (it did there).
