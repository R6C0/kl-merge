# First-person view: the Arcade player's camera code path in kl2.exe (C1)

Static reading of kl2.exe (base 0x400000) with debug/kl.py + capstone, re/kl2.json schemas, and the
.data section captured in the live dumps of the owner's 2026-10-09 rounds
(`<work>\research\owner_round_1009_1820\KLHook_1.dmp`). Nothing was run. Units are centimetres
(Glacier 1), angles in the camera code are radians (the code multiplies by 0.0174533 / 57.2958).
"ASSUMPTION" marks anything not read off the code or the dump.

## 1. Classes

RTTI names with Camera / Cam (re/kl2.json `classes`, controller map `controllers`):

| class | controller name | size | base | role |
|---|---|---|---|---|
| ZCAMERA | (geometry class) | - | ZGEOM | the camera NODE in the level; 22 level fields, +0x70 = FOV in radians (written by the controller every frame, see 3) |
| ZBaseCamera | BaseCamera | 152 | ZBaseConRout | base of all camera controllers; reads the look input |
| ZFFCam | FFCam | 1312 | ZBaseCamera | third-person follow camera: target object, collision, shake |
| **ZFFCamera1** | FFCamera1 | 3304 | ZFFCam | **the in-game player camera** (profiles, shoulder, FOV blend); vtable 0xbb76a4, ctor 0x5a6f30 |
| ZPIPCam | PictureInPictureCam | 1704 | ZFFCam | picture-in-picture |
| ZCutSequenceCamera | CutSequenceCamera | 200 | ZCAMERA | cut scenes |
| ZShakeCamera | ShakeCamera | 64 | ZGEOM | level-authored shake (4 fields: f, s, b, f) |
| ZDocuCamProfile | DocuCamProfile | 156 | ZGEOM | hand-held "documentary" profile per movement state (9 fields: s, s, f, f, f, ETYPE, I, b, EHAPTICSTYPE) |
| ZDocuCamControl | DocuCamControl | 56 | ZEventBase | triggers a profile (s, ETYPE) e.g. 'OnExplosion' |
| ZDistanceRumbleCam, ZCamOscillator, ZCheapCamValues, CCameraBox, ZOnlineEscCamTrigger, ZOnlinePIPCameraPoint, ZPreviewCamera, ZScreenshotCamera | | | | spawn / escape / effect cameras |

Serialized fields of ZFFCamera1: ONE string (ZFFCam and ZBaseCamera: none). So distance, shoulder
offset, pitch limits and FOV are **not level data**: they are compiled constants (section 2.4) plus
per-state parameter sets in `.data`. ETYPE (0xd008ac) lists the hand-held states: Standing, Walking,
Running, Sprinting, InHelicopter, Sneak*, Sniper*, KaneCam, OnCoverEnter, OnWeaponPickup, OnAiming,
OnChangeCover*, OnKickDoor, OnReload, OnHitFromLeft/Right, OnExplosion, OnElevatorFall,
OnTrainPassingBy, OnDownNotDead1-3, OnDead, OnCloseCombat, HumanShield* (41 profiles).
The script default `float CameraFOV=67.4;` sits in .rdata at 0xb2d314; the compiled base FOV is
1.16937 rad = 67.0 deg (0x6536a0).

## 2. Objects and layout (ZFFCamera1 `this`, offsets read from the code)

- +0x24 owner entity record (the ZCAMERA node); `[node+4]` = the ZGEOM object: 3x3 matrix at +0x00,
  position at +0x24, parent at +0x50 (0x7b3020 = local->world point, 0x717890 = direction,
  0x857110 = world basis). node+0x70 = FOV (radians), node+0x1b8 = room.
- +0x30 enabled byte; +0x44..+0x8c input action values (0x659e30), +0x90/+0x94 look deltas (mouse
  rel X/Y from the input device [0xddb958] axes 0/1), +0x74 pitch, +0x7c yaw (copied from the player
  through player vtable slots +0x5b8 / +0x5bc, so the ANGLES LIVE IN THE PLAYER).
- +0x398..+0x3a0 camera position taken from the player's rig (slot 51 = 0x548e60 -> 0x7a8b90 copies
  rig+0x1d4..+0x1dc; rig = `[player+0xbd4]`, getter 0x4446e0).
- +0x414 3x3 result matrix, +0x438 position copy, +0x444 previous frame's matrix (0x6dc150 tail).
- +0x498 target bone matrix (48 bytes), +0x4bc target bone position (0x6dc150: bone matrices array
  from 0x78c710, index from `[target+0xd50]` -> 0x4a01b0 / 0x88c520).
- +0x4c8 target frame, +0x4ec target position, +0x4f8 shake offset (vec3), +0x504 target entity,
  +0x508 the position handed to the node, +0x524..+0x52c offset vector, +0x530/+0x534/+0x538 base
  offset (x right, y, z back: 30 / -18 / -30 normally, 45 / -27 / -spline in cover, 0x7a1440),
  +0x53c base FOV, +0x540 the player (ZFFPlayer), +0x550 profile FOV, +0x554/+0x558 profile
  horizontal/vertical offsets, +0x55c profile distance (negated), +0x568 "set" flags
  (1 FOV, 2|4 offsets, 8 distance, 0x10 override), +0x56c pivot offset (profile +0x14 or the player's
  slot +0x328), +0x5a0 blend speed, +0x5ac shake rotation matrix, +0x5d0 shake translation,
  +0x5e0 rumble multiplier, +0x628..+0x63c explicit shake (duration, amplitude x/y, rate),
  +0x658..+0x78c six smoothed channels of 0x34 bytes (ctor), +0x7c8/+0x7cc FOV scaled values,
  +0x7d8 "ShakeFilter" object (looked up by name at init 0x4fbf10), +0xb2c current profile pointer,
  +0xb44 "CameraTransitionSpline" (level spline named at init), +0xb9c shoulder side blend
  (0x9088c0: (t - 0.5) * -2 from the spline parameter; `[player+0x280c]` = left/right shoulder,
  RMC SetLeftShoulder), +0xc58 override mode flag, +0xc8c..+0xc98 FOV transition.

The 24 static profile structs (0x198 bytes each, `.data` 0x154a820 .. 0x154d190; selected by
0x778f50 from the player's state) read from the live dump (values identical in both 1820 dumps):

| struct | FOV rad (deg) +0x15c | h.off +0x160 | v.off +0x164 | dist +0x168 / alt +0x16c | blend +0x170 / +0x174 / +0x178 | pivot +0x14..+0x1c (flag +0x157) |
|---|---|---|---|---|---|---|
| 0x154a820 default (also 0x154b4e0) | 1.169 (67) | 45 | -5 | 200 / 100 | 0.4 / 1.0 / 2.0 | player's own |
| 0x154a9b8 aim | 0.873 (50) | 45 | -5 | 200 / 100 | 0.6 / 0.5 / 0.2 | player's own |
| 0x154ab50 cover low | 1.169 | 40 | 0 | 110 / 110 | 0.4 / 3 / 0.8 | -30, 160, 10 |
| 0x154ace8 cover aim | 0.698 (40) | 35 | 0 | 110 / 110 | 0.1 / 0.5 / 0.2 | -50, 160, 30 |
| 0x154ae80 / 0x154b018 / 0x154b1b0 / 0x154b348 cover variants | 1.169 / 1.169 / 0.785 / 0.785 | 40 / 65 / 35 / 40 | 0 | 110 / 110 | | -30,120,10 / 0,120,10 / -60,120,40 / 0,120,10 |
| 0x154b810 FA default | 1.169 | 30 | 0 | 180 / 140 | 0.2 / 3 / 2 | player's own |
| 0x154b9a8 FA aim | 0.873 | 30 | 0 | 180 / 140 | 0.2 / 0.5 / 0.2 | player's own |
| 0x154bb40 | 1.169 | 30 | -5 | 110 / 110 | 0.8 / 3 / 0.6 | |
| 0x154bcd8 / 0x154be70 sprint (`[player+0x850]`) | 1.169 | 25 | -15 | 300 / 350 | 0.4 / 3 / 0.4 | |
| 0x154c1a0 human-shield carrier | 1.518 (87) | 45 | 10 | 100 / 100 | 0.2 / 3 / 0.5 | 10, 50, 45 |
| 0x154c338 | 1.169 | 45 | -5 | 200 / 100 | 0.4 / 2 / 2 | 0, 160, 0 |
| 0x154c4d0 (player slot +0x3d0 true) | 1.344 (77) | 0 | 15 | 250 / 100 | 0.2 / 3 / 1 | |
| 0x154c800 | 1.169 | 45 | -30 | 250 / 250 | | |
| 0x154c998 (FA, after death / 0xad4 == self) | 1.169 | 45 | -5 | 100 / 100 | 0.4 / 3 / 0.4 | |
| 0x154cb30 / 0x154ccc8 | 0.873 / 1.169 | 45 | -5 / -10 | 100 / 100 | 0.2 / 0.5 / 0.2 | |
| 0x154ce60 | 1.047 (60) | 25 | 5 | 200 / 80 | | |
| 0x154cff8 shield (`[player+0xad4]` self) | 1.047 | 0 | 0 | 80 / 60 | 0.1 / 0.5 / 0.2 | -10, 160, 60 |

The names in the first column are from the selecting conditions in 0x778f50 (state ids from player
vtable slot +0x5d8: 8 = cover, 0x12 = human shield; `[player+0x2954]`, 0x6e2740, 0x780b80 = aiming
tests); they are interpretations, the structs carry no names (+0 and +4 are null). Flags +0x150..
+0x156 are all 1,1,1,1,0,0,1 (fields valid). The profile is applied by 0x5ea690 into +0x550 /
+0x554 / +0x558 / +0x55c / +0x56c / +0x5a0; distance is clamped by `100` and `220` constants and
the alternative distance is used when the "clear line" test (slot +0x5c4 > 300) fails.

**The shoulder offset as a measured number**: the heap was not in the dumps (the hook writes
stacks + register targets + `.data`; a vtable scan for 0xbb76a4 / 0xbb75b4 / 0xb9beb4 found no
camera object in any of the four dumps), so the live camera matrix and head-bone position could NOT
be read. The numbers above are the live `.data` parameters: default third-person = 200 cm behind the
pivot, 45 cm to the right, 5 cm down (FA: 180 / 30 / 0), FOV 67 deg; aiming 50 deg.

## 3. The per-frame routine

Event dispatch: ZBaseConRout slot 27 (0x617590) maps event 0x10 -> vtable slot 25 (tick).
ZFFCamera1 slot 25 = **0x8f3300** -> 0x650070 (the tick body) when `this+0xba0` or the game flag
`[[0xdd2640]+0xac]+0xbc` is set. Frame time is `[[0xdd2640]+0x50]`, frame counter `+0x48`.

0x650070, in order:
1. 0x5e4b50 (ZFFCam tick): slot 58 **0x6dc150** = target update: bone matrix of the target
   (`[target+0xd50]` bone binding -> 48-byte matrix from 0x78c710) into +0x498/+0x4bc, else
   0x857110 (target basis); target frame +0x4c8/+0x4ec; then slot 51 0x548e60 (copies the player
   rig's camera position rig+0x1d4 -> +0x398) and slot 52 0x892180 (target offset +0x48c); then
   +0x508 -> +0x438, +0x414 -> +0x444 (last frame's result kept). Then ZBaseCamera 0x5aaf90:
   slot 38 **0x8d6360** (input: 0x659e30 reads the input actions and the mouse deltas into
   +0x44..+0x94; +0x74/+0x7c = pitch/yaw from the player; recoil `[rig+0x9c] * 7` added to +0x90)
   and slot 47 0x8a3b90 (debug camera, only when `[0x15470ac] == 6`).
2. If a target: **0x87add0** = the camera's own steps:
   0x4baa40 explicit shake offset -> +0x4f8 (random 2D, decays; routed through the "ShakeFilter"
   object slot +0x120 when one exists); 0x778f50 profile selection (table above) -> 0x5ea690;
   0x9088c0 shoulder-side blend along the CameraTransitionSpline (+0xb9c); 0x82c210 hit / recoil
   transition timing (+0xc10..+0xc24, constants 150/5, 180/5, 150/10+40, 35/2, 200/2/0.5);
   0x7a1440 base offsets and base FOV (+0x530..+0x53c, +0x598); 0x48ec00 + **0x4fe150 FOV**: writes
   `node+0x70` = blended FOV (x0.9 when 0x9018e0, 45 or 70 deg in special states, rumble channel
   +0x5dc/+0x5e0/+0x5ec mixed in); 0x446c40 weapon / cover kick table (-10,33,35 / -10,33,60 /
   33,-5 / 30,-10,-200 / 60,-70,-170 -> +0x5d0); 0x6ed8d0 shake apply (+0x5ac matrix -> +0xbb4,
   rumble to the controller slot +0x40 scaled by +0x5e0, then +0x5ac..+0x5e8 cleared);
   when `this+0x7eb`: slot 55 **0x897d60** = collision (probe spheres from +0xb0 along the view,
   constants 2500 / 850 / 750 / 15 / 20 / 10, distance result +0x124 / +0x3f4) ending in
   0x6e0b20 (raycast toward -750 along +0x468, `this+0x394` = blocked) and slot 57 **0x56e4c0**
   = final position: 0x658220 (+0x398 rig position) plus +0x524..+0x52c offset (x1 / x3 when
   aiming, limits 10 / 15 / 20) -> **0x7c9030** = `this+0x508 = pos; node->vtable[36](&pos)`.
3. 0x511f20 -> 0x6f8710: room of the camera into node+0x1b8.
4. Override block (only when `this+0xc58`): 0x7c9030 position and **0x4d8080** orientation
   (3x3 at +0x414 built by 0x47b750 from a direction and roll, then `node->vtable[37](&+0x414,
   &+0x508)`), FOV from +0xc8c..+0xc98.

Node setters (ZCAMERA vtable 0xb9beb4): slot 33 0x8779f0 -> geom 0x8374b0 (SetMatrix),
slot 36 0x7ca930 -> geom 0x66d0f0 (SetPosition), slot 37 0x826870 -> geom 0x75c520 (both).

OPEN: on a normal frame the controller sets only the POSITION (0x7c9030) and FOV; the orientation
setter 0x4d8080 is reached only from the override block and from slot 50 (0x4cfd60, reset: position
= bone + (0,500,0)). 0x8374b0 has no direct caller; 0x75c520 has seven (0x41be90, 0x55bf80,
0x6d2730, 0x6d8b00, 0x72d530, 0x760780, 0x84a850), none inside the camera class. So the view
orientation most likely comes from the PLAYER side (yaw/pitch are the player's state, slots
+0x5b8/+0x5bc; the rig `[player+0xbd4]` holds +0x14/+0x1c angles, +0xc0 distance, +0x2f0/+0x2f4
recoil) and is written to the node or read by the renderer from the player's angles: ASSUMPTION,
not followed to the instruction. Candidates for the rig update: 0x653e00, 0x7d72c0 (both write
rig+0x1d4..+0x1dc, +0x2f0, +0xc0). 0x88d780 is a field printer (debug), not it.

## 4. Shake: where applied, one multiplier?

Three layers, no single multiplier:
- Explicit shakes (`msgExplicitShakeCamera`, `msgShakeCamera`, `msgWindShakeCamera`, ZShakeCamera,
  ZDistanceRumbleCam): 0x4baa40 random 2D offset (+0x61c/+0x620, amplitude +0x634/+0x638, time
  +0x628/+0x62c) -> +0x4f8, or handed to the "ShakeFilter" object (`this+0x7d8`, slot +0x120).
- The hand-held layer (DocuCamProfile, `ff2\gamedata\docucamshaker.cpp` 0x641410): the matrix at
  +0x5ac / translation +0x5d0 composed in 0x446c40 and consumed in 0x6ed8d0 (copied to +0xbb4,
  zeroed each frame). The rumble multiplier `this+0x5e0` scales the pad rumble and the FOV wobble
  (0x4fe150 reads +0x5dc/+0x5e0/+0x5ec) but not the matrix.
- Recoil: `[rig+0x9c] * 7.0` added to the yaw input (0x8d6433); hit transitions in 0x82c210.
For a first-person prototype the cheap kill is to zero +0x5e0 and skip 0x6ed8d0's copy (one `ret`
at 0x6ed8d0 is enough for the matrix part: it only writes +0xba8/+0xbb4 and clears +0x5ac..+0x5e8).

## 5. Aim

The aim ray starts at the CAMERA, not the muzzle: 0x559060 (on the rig) takes the rig's camera
position (0x7a8b90 = rig+0x1d4) and direction from angles rig+0x14 + recoil +0x2f0 and rig+0x1c
+0x2f4 (0x7ff980), starts at distance rig+0xc0 (plus the camera's own distance from the player's
slot +0xc4) and casts 100000 cm (0x8a4730); the hit point is the crosshair world point used by the
weapon code. Crosshair textures: `tex:UserInterface/Crosshairs/KL2_Crosshair_01#Rifle|MachineGun|
Shotgun|Gun...`, states eCROSSHAIR_STAND/WALK/RUN/SPRINT/COVER/CROUCH/AIM. Net: the "aim point" and
"camera angle" are replicated per player (re/netcode.md). A head-mounted camera therefore keeps aim
consistent for free as long as the rig position moves with it (section 6, point 2).

## 6. Cheapest patch points for a "camera at the head bone" prototype

Everything below is a per-tick write or a 5-byte patch in kl2.exe; none has been tried.
1. **Position**: the node gets its position only through 0x7c9030 (`this+0x508` then node slot 36).
   Patch 0x7c9030 (14 instructions, `ret 4`-style tail-jump) to copy `this+0x4bc` (the target's
   bone position, already the head when `[player+0xd50]` binds a bone; see 3) instead of the
   argument, plus a forward nudge of ~10-15 cm along the view to leave the head mesh. The bone
   update (0x6dc150) runs BEFORE the steps every frame, so +0x4bc is fresh. The collision step
   (0x897d60) must be disabled (clear `this+0x7eb`, or `ret` at 0x897d60; slot 57 is then not
   called, so the position write moves to the patch).
   Alternative with no code patch: per tick write `this+0x508` AFTER the game's tick and call
   node slot 36 yourself: the hook runs after the game's main-thread tick (klnudge's hook point).
2. **Which bone**: `[player+0xd50]` is the camera bone binding record `{geom*, bone index}`
   (0x6dc150 reads `[ebx]` and `[ebx+4]`); the bone matrix array is 0x78c710(`[geom+0x88]`), 48
   bytes per bone, translation at +0x24. There is no head/camera bone selected by name in the
   camera code (re/characters_graft.md: no `camera_bone` in any character); the head bone index
   per skeleton is in re/pd2_klside.md's head-bone frames (12 masks work). ASSUMPTION: binding the
   record to the head index gives a +0x4bc at the head.
3. **Orientation**: not set by the controller on a normal frame (section 3 OPEN). A prototype
   should force it: call 0x4d8080(dir, roll=0) per tick with dir from the player's yaw/pitch
   (player slots +0x5bc/+0x5b8, the values the game itself uses for the aim ray), or set `this+0xc58`
   and fill +0xc5c..+0xc98 (the override block does position + orientation + FOV itself).
4. **Offsets / distance**: zero the profile numbers at load: +0x160/+0x164/+0x168/+0x16c of the 24
   structs at 0x154a820 + i*0x198 (24 writes), and the base offsets at 0x7a1440's constants
   (`.rdata` 0xceb590 30, 0xceb594 -18, 0xceb5a0 30, 0xceb5a4 40, 0xceb574 45, 0xceb578 -27) if
   the controller's own position path is kept instead of point 1.
5. **FOV**: node+0x70 is rewritten every frame by 0x4fe150 (and by 0x650070's override block);
   the base is 0x6536a0's 1.16937 rad; widen by patching the `qword 0xb319d0` (1.16937) or by a
   per-tick write of node+0x70 after the tick. Per-state FOVs are +0x15c of the structs.
6. **Near plane / own model**: ZFFCamera1 slot 42 returns the global float `[0xb5fb50]` = 5001
   (ZCAMERA level fields 8/9/10 are f,f,f after the ZGEOM header: FOV, near, far by position:
   ASSUMPTION; `CameraFar` 50000 is the scene block value, re/lighting.md). The player's own model is
   not culled by the camera code; hiding it needs the body swap or variant bytes the wardrobe
   already uses (klchar.c, 0x88c810), or the first-person hands model if one exists
   (re/firstperson_assets.md is the other track). Wall clipping of the head: Glacier draws nothing
   nearer than the near plane, so a 5-10 cm forward nudge is needed to avoid seeing the inside of
   the head mesh.
7. **Per-frame rewrite**: yes for position (0x7c9030 each frame via slot 57), FOV (0x4fe150) and
   room (0x6f8710); the matrix 0x414 is only rewritten by the override block / reset. So a KLHook
   per-tick write must come after the camera tick (0x8f3300) each frame, or the two sites above are
   patched once.

## 7. Facts vs assumptions, in one place

Facts (addresses read): class list and sizes; tick chain 0x617590 -> 0x8f3300 -> 0x650070 ->
0x5e4b50 / 0x6dc150 / 0x8d6360 / 0x87add0 (steps 0x4baa40, 0x778f50, 0x9088c0, 0x82c210,
0x7a1440, 0x48ec00, 0x4fe150, 0x446c40, 0x6ed8d0) -> 0x897d60 -> 0x56e4c0 -> 0x7c9030 -> node
slot 36; 0x4d8080 -> node slot 37; node setters 0x8779f0 / 0x7ca930 / 0x826870; profile structs
and their live values; FOV constants; ETYPE list; aim ray 0x559060 from the camera position.
Assumptions: names of the profile structs; which player-side function orients the node; ZCAMERA
field order FOV/near/far; that `[player+0xd50]` can be pointed at the head bone without the
animation code objecting; everything in section 6 (untested).
