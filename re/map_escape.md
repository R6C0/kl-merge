# The escape vehicles of the four Dead Men Fragile Alliance maps under Dog Days

2026-10-10, agent t-van. OFFLINE: both executables, the four builds in `<work>\build\z_maps\M01 M02
M03 M06` (read, not changed), the 21 stock Dog Days levels. Nothing was installed, the game was not
started. Tool: `tools/kl_map_escape.py`. Repaired copies: `<work>\build\t_van\<map>`.
Status words: **seen** = read in the files / the executables with the command given, **ASSUMPTION**,
**not established**. NOTHING HERE RAN IN THE GAME.

Owner, after playing Late Night Opening (M02_FA_A): 'the late night van sometimes is a bit weird?
camera goes under the map when ur in it'.

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
