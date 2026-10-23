# Character rotation in kl2.exe: what is known, what is not, where a "more rigid" turn can be put (2026-10-19)

Question (owner): can players' rotation be slowed so it feels more rigid? Static reading of kl2.exe (read only),
re/kl2.json schemas, stock F01 level data, existing re/*.md and klhook sources. Nothing was run, nothing written to a game folder.
Labels: CERTAIN = read in the exe or a file on this PC. RECALL = general knowledge, not checked here. GUESS = my inference.
Honest summary first: the one place that applies the LOCAL body yaw and any turn-rate constant were NOT found. See section 6.
(2026-10-23: both were found afterwards, AI and player; see the dated section at the end.)

## 1. The four places rotation lives

1. Camera input layer (local human). Mouse deltas come from DirectInput: the game reads the mouse state once a frame in
   ZMouseWintel update 0x650840 (GetDeviceState, 0x14 bytes = DIMOUSESTATE2, lX at +0, lY at +4) (CERTAIN, klhook/klauto.c
   comment). The binding text `TurnCamera=rel(ms,x); TiltCamera=rel(ms,y)` and `TurnCameraGC=ana(gc0,righty)` are one
   string in .rdata at VA 0xb87f68 (CERTAIN, found); .rdata is partly hashed, so the text must not be edited.
   Camera rig: `[player+0xbd4]` +0x14 / +0x1c = yaw / pitch (re/camera.md; CERTAIN as reported there). Options names that scale
   the turn: MouseSensitivity, Sensitivity, InvertHorizontal, GameSteadyCam, CameraAutoCentering (re/menus.md).
2. Stick axes. Move stick (front/back, sides) are set with 0x72cf20 / 0x7e4510 on the player object (CERTAIN, seen in the
   receiver 0x600eb0 at 0x60188a..0x6018e6 and in 0x7a43e0). re/firstperson_camera.md calls player slots 0x5b8/0x5bc yaw/pitch:
   that is WRONG, they are the move stick (+0xb94/+0xb98).
3. Body turn is ANIMATION-DRIVEN, with turn-in-place clips (CERTAIN that the clips exist). Exe strings: /Movement/Stand/Turn_Left_45,
   Turn_Left_90, Turn_Right_45, Turn_Right_90, Crouch/Turn_{Left,Right}_{45,90}, Walk/Turn_180, Run/Turn_180,
   Transitions/{Walk,Run}_To_Stand_Turn_{Left,Right,180}, Stand_To_Run_Turn_180, Shoot_Pose/Turn_{Left,Right}_90_{Left,Right}_Hand,
   Shoot_Pose_Enter_Turn_{Left,Right}_180_{LH,RH}, /Turn/Left_90_Quick, Left_180_Quick, Human_Shield turns. They are registered in a table of
   {id, path} pairs built on the stack at 0x78de09.. (ids 0x10, 0x12, 0x14 ... = Stand/Turn_Left_45 is id 0x12, Stand/Turn_Left_90
   id 0x14; CERTAIN). So 45 and 90 degree steps are authored clips; the angle threshold that picks one was not found (GUESS: in
   the BaseMove state machine 0x7a43e0 or a callee).
   Also in the exe: `TurnAnimWait` (CPPScript task), Havok `m_fTurnAngleSpd`, `m_fTurnAngle`, `MinTwist`, `MaxTwist`,
   `m_fGravityTurnSpdParam` (all ragdoll/Havok behaviour constants, CERTAIN they exist; NOT the player's turn: excluded).
4. Replicated heading (sender and receiver). Section 3.

## 2. What 0x7a43e0 does (ZFFPlayerMovementBaseMove update) - a false lead removed
`add [esi+0x1ee4], (int)(0x5e0db0() * 1024)` at 0x7a4884..0x7a4894 looked like a heading accumulator. 0x5e0db0 returns
`[ecx+0x4c]` if non-zero else `[[0xdd2640]+0x50]`: a frame delta time (CERTAIN reading; GUESS that it is dt). So [+0x1ee4] is
a time accumulator in 1/1024 s units, NOT a heading. Constants seen at the top of 0x7a43e0: 0.3 (0xbb5f68, a compare with [edi+0x960]), 0.2, 0.5, -0.7
(0xb40260), 0.1 (double 0xb4e7e8), 0.00012207 (0xb22900): all in .rdata (hashed or not not checked: treat as hashed).
No turn-rate constant was identified there.

## 3. Remote players (online)
Sender 0x6300f0: heading = angle from 0x429ff0 * 162.97466 (double 0xb78bc8 = 1024/2pi), truncated to an unwrapped int16; tolerance
900 (= 30 squared) in the object 0x168f4b0, 100 ms minimum interval, 2000 ms forced refresh (re/netcode.md 8.1-8.3, CERTAIN).
Receiver chain: ZFFPlayer vtable slot 393 = 0x506350 -> 0x600eb0 (CERTAIN, re/netcode_receiver.md).
NEW in this pass (CERTAIN, read 0x600eb0 line by line):
- 0x600eb0 refreshes the dataset with 0x519e80 for three groups (move input +0x2a0.., position +0x58/+0x60 block, camera angle +0xd8/+0xe0).
  It does `heading = movsx word [esi+0x60] / 162.97466` (0x60143c..0x60145d), builds a 3x3 from it with 0x7f07a0 + 0x589440 into a
  stack matrix at [esp+0x120] (0x601461, 0x601471). That matrix is used ONLY to rotate the position-error offset into the body frame
  (0x455b40 at 0x601597, 0x6015ef, 0x601723, 0x601735: vector transforms), before the offset becomes stick input.
- The camera angle (+0xe0) is refreshed there but NOT read in 0x600eb0.
- Therefore 0x600eb0 does NOT place or rotate the remote body by the heading. The remote body's FACING is not set in this function.
  GUESS: it comes from the same machinery as a local body (turn-in-place clips driven by the replicated camera angle through the movement
  state machine, plus the stick steering), which would explain why a bad heading sample shows up as a spin of the steering
  and not as a snapped rotation. This is the key open question for remote rotation (section 6).
- Teleport path 0x5f21c0 (squared distance > 1,000,000, double 0xb49b40) re-seeds the models and places the body through vtable +0x8c;
  0x5f225d inside it divides/multiplies by 162.97: the body heading IS applied at a teleport (CERTAIN that 0x5f21c0 uses 0xb78bc8 at 0x5f225d).
Per-class vtable hooks: ZFFPlayer vtable 0xbb45f4 (RTTI). Swapping the pointer of a heap ZFFPlayer to a private vtable copy is allowed
(re/antitamper.md); slot 393 (0x506350) is the remote update entry. A replacement slot could call 0x600eb0 and then post-process, but without
knowing which function sets facing there is nothing yet to post-process. GUESS.

## 4. AI actors (ZFFActor) and bots
Stock F01 data, 49 ZFFActor and 16 ZFFPlayer nodes (read with tools/kl_fa.py and the exe schema, CERTAIN values):
- ZFFPlayer: the only float level field is index 17 = 0.0 on all 16. No turn speed.
- ZFFActor: float fields 17 = 0.0 (49x), 29 = 10.0 (49x), 32 = 1.0 (49x), 34 = 50.0 (49x). Names/roles unknown (the exe holds no property names).
  None can be called a turn speed on evidence.
- Controller `ZSoldier` (class ZSoldierRout, 36 in F01) values: fields 4/5/6 = 50.0/50.0/50.0 (32x; 70/40 in 4), field 7 differs by
  soldier type (eArmy 175.0 x18, eThug 280.0 x7, eStreetCop 100.0 x6, eGuard 65.0 x4), 8 = 50 or 0, 9..12 = 1.0, 13/14 = 50.0,
  15 = 5000.0 or 1.0, 16/17 = 800.0 or 600000.0. Field 7 varies by type, so it could be a speed or an HP-like value: UNKNOWN, GUESS only.
- Controller `ZCivilian` (ZCivilianRout, 13): 5000.0, 0, 5.0, 50.0, 1.0 x5.
- Controller `DiscoMove` (scene decoration): 30.0/20.0 rate values: not characters.
- RotateOnActivate (409 instances): 0, 360.0, 0/60.0: doors and props, not characters.
AI bots: re/playtest*.md records the TEST RIG's bot turn rate (mouse clamp 1800 counts/s at 0.17 degrees per count = 306 degrees/s,
klauto.c TurnDeg 0.17), which is the rig and not the game's own AI. The AI's own facing turn rate is NOT found.
Co-op partner bots: not examined in this pass (GUESS: same movement class as AI).

## 5. Where a "more rigid" feel can be implemented, and what each choice breaks
Rules: hashed code/.rdata are never written; allowed: dinput8 proxy (KLHook), IAT, .data/.bss, heap, private vtable copies, level data.

A. LOCAL INPUT SIDE (the player's own turn) - the realistic lever, no code patch:
   Scale or clamp lX (and lY) of the mouse in the dinput8 proxy's GetDeviceState wrapper (already exists for the scripted mouse in klauto.c,
   hook of IDirectInputDevice8 slot 9; the game reads 0x14 bytes at 0x650840). Options: (1) multiply the counts by a factor (equals lowering
   MouseSensitivity), (2) cap counts per frame or degrees per second (0.17 degrees per count at the rig is a measurement of the rig, scale
   by the owner's setting), (3) apply a low-pass so the camera accelerates (heavy feel), time constant 50 to 100 ms (RECALL: UE exponential smoothing).
   Breaks: aiming. The camera IS the aim ray (rig yaw/pitch). A cap makes flick shots impossible: apply to yaw only, and only while NOT aiming
   (the aim state can be read like klauto does), or keep the cap high (360 degrees/s, RECALL UE default RotationRate).
   Hit registration: the server/host decides hits from the shooter's replicated aim, which stays consistent with what the shooter saw. So input-side
   slowing is self-consistent and does not desynchronize anything; the remote copy of the slowed player rotates slower too (honest data).
   Gamepad: the gamepad path is a separate device (gc0 in the binding text); the proxy would need the same treatment (not examined).
B. REMOTE DISPLAY SIDE (other players' bodies): needs the facing setter, which is not located (section 6). Without it only these are possible:
   (1) the existing klnetfix.c experiments (dead-reckoning end time, policy +0x14 3500 ms, .bss objects); (2) sender tolerance tuning (klnet.c Tune:
   PosTol, AngTol, PlayerMs): lowering AngTol / interval makes heading samples denser, which SMOOTHS remote turning, it does not make it slower.
   The other workflow's klnetsmooth.c (receiver-side turn cap + blending, not present on disk when this was written) must find the same setter first.
C. SENDER SIDE: a cap on the replicated heading (limit change per packet in the sender 0x6300f0) would make others see a slowed turn while the
   owner turns freely - this DISAGREES with the owner's own view (his bullets still go where he aims). Not recommended: breaks the
   consistency between the aim ray and the displayed body.
D. LEVEL DATA (owner maps): no turn-speed field exists in ZFFPlayer / ZFFActor / ZSoldier / ZCivilian with a known name. The turn clips are in the
   level's .ANM / animation database (CERTAIN that the engine loads them as clips; the DD clip header is 0x68 bytes per clip, CLAUDE.md). Making a turn
   clip longer would slow a turn-in-place, but root motion and foot sync are baked: GUESS, high effort, not tried.
Both "slow" and "rigid" are different things (RECALL, Payday 2 / UE / Source): rigid = body yaw changes only after the aim leaves a window of +-45 to 90
degrees, then a fixed-rate turn (re/netfeel_references.md section 2 and 4, the PD2 constants 45/90/120 are from shipped Lua bytecode, CERTAIN
that they exist; how they combine is GUESS). K&L already has the 45/90 turn-in-place clip structure, so the local body is already "rigid" in that sense.

## 6. NOT found (do not assume)
- The instruction that writes the local body's yaw each frame (candidates: root-motion application plus an orientation setter; callers of
  the atan2 wrapper 0x429ff0 at 0x7e1a50, 0x7dd7b0, 0x82cc40, 0x8d1f90, and the helpers 0x41ad30). 0xb78bc8 has 27 code references
  (0x41f97b 0x491a76 0x4d0f3c 0x4e76df 0x557e3e 0x56a010 0x5d31dd 0x5f225d 0x601459 0x60c6cd 0x62aae4 0x62ab18 0x6301c8 0x63abb3 0x6a53e2
  0x71d66e 0x7464a8 0x789838 0x796344 0x7dd7e6 0x7e1b57 0x803fe4 0x81b250 0x82cdd6 0x82ce23 0x83299b 0x892aea): a list for the next pass.
- Any turn-rate limit, turn-in-place angle threshold or blend time, and whether it sits in hashed .rdata or writable .data.
- The remote body's facing setter, the AI actor turn path, co-op bot turn path.
- Whether the mouse sensitivity factor sits in a writable global (not searched).

## 7. Recommended next steps
1. Cheapest experiment, no game code touched: a [Look] section in the KLHook mouse wrapper (scale lX/lY, optional per-frame cap, smoothing with
   tau 60 ms). Default off. Measure with the existing klauto rig (TurnDeg per count). Needs the owner at the PC to judge the feel.
2. To find the facing setter: log writes via a hardware watch on a remote ZFFPlayer's matrix, or trace readers of 0xb78bc8 from the list in section 6.
3. For remote players, wait for klnetsmooth.c, then compare its hook point with section 3.

## 2026-10-23 cloud static reading: where the turn rate lives (AI found, player found; nothing ran)
Read in kl2.exe build 0490; member offsets from the RTP records (record +0x10 = member offset, established here). CERTAIN unless
marked GUESS. Nothing ran.

### A. AI actors (ZFFActor: soldiers, civilians, Arcade AI heisters) - one tuning global in .data
- ZFFActor slot 400 = 0x62a710 calls the actor move step 0x812b70 every frame. At 0x814326 it loads **float [0xcdea94] = 720.0 (.data,
  its only code reference)**, multiplies by 1.0 (or 0.2 = .rdata 0xb18700 when the root-motion speed is under 30 units/s, 0xb45350, mode
  byte [actor+0x4ad] = 0) and by deg2rad (0xb84910), and passes it as the 4th argument of **ZActor slot 396 = 0x660780** (vtable +0x630; its only
  4-argument caller).
- 0x660780 turns the body: angle = acos(dot(current, wanted)) (0x925da0; under 2 deg, 0xb46640, counts as 0); step = |[actor+0x578]| x
  rate x dt, capped at the angle, signed by the cross product; the current direction is rotated by step (0x4f2c50). **[actor+0x578]
  (float, per actor) is a ramp fraction in [-1, 1]** moving toward clamp(2 x angle / pi, -1, 1) by rate x dt per frame. So an actor turns
  at min(1, 2 x angle / pi) x 720 deg/s (360 at 45 deg, 72 at 9) and is at full speed after 1/rate = 80 ms. The result reaches the node
  through actor slot 343 (0x7084c0 -> 0x6d0240 -> node vtable +0x94, GUESS "SetDirection"); every move mode but 5 takes this turn.
- No serialized property reaches it: 0x812b70 reads no ZSoldierRout member (slot 4 = 0x846340 copies its floats +0xa0..+0xd4 to
  [rout+0x44..+0x78]; none read here) and no ZFFActor level field.

### B. The local player (ZFFPlayer): deadband in .data, rate in heap + .rdata
- ZFFPlayer slot 87 = 0x57fae0 runs the steer 0x6d9380 (0x7f8b20: a second copy): acos(dot(wanted move
  dir, body forward)) at 0x6d9b4d -> [player+0xafc]; **[player+0xaf8] = 0.15708 (9 deg) from .rdata 0xb2f260 every tick**; flag 0x20 / 0x40
  in [player+0x438] when |cross.y| >= 0.01 (0xbb01b4).
- ZFFPlayerMovementBaseMove slot 29 = 0x84d790 hands [player+0xaf8] as base step `s` to **0x54d1a0**, the one function that turns the
  player's body (frames = dt x 60):
  - moving (anim state id not in {0xe, 0xf, 0x12..0x16}): rotation per frame-unit = s x (0.2 + 0.7 x clamp((angle - 18 deg) / 72 deg, 0, 1)),
    never overshooting: 108 deg/s for small errors, 486 from 90 deg. Constants 0xb7d8f0, 0xb16850, 0xb53d90, 0xb70260: .rdata.
  - turn-in-place states (those ids = the Turn_45/90 clips of section 1): the remaining angle is spread over the clip's remaining
    frames ([state+0x58] -> clip header word +2, [state+0x40] = phase) when 0x6db900 (session +0x54 <= 1, GUESS "not online"). The
    clip's only speed scalar is its length in the .ANM; no playback-rate field was found (GUESS: none).
  - deadband: **0x4533a0 returns the threshold T from four .data floats in degrees: 0xce9750 = 90 (default), 0xce9754 = 90 (move flags
    & 0x400), 0xce9758 = 90 (0x651000: flag 0x40 of [player+0x818] or a state test), 0xce975c = 12.5 (bit 1 of [player+0xa54], GUESS
    human-shield hold)**. 0x41ad30 (from 0x7a4747) compares T with [player+0xafc] for the turn-in-place entry; in 0x54d1a0 the part
    beyond T goes at once, inside T the body creeps at 0.028 rad per frame-unit (0xb54e90).
- ZMovementBaseMove slot 29 (0x63c100, +-5 deg per frame-unit, .rdata) is ZPlayer's state only; ZFFPlayer overrides its factory
  (slot 405 = 0x5bda20). Remote players are ZFFPlayer: same code (GUESS).

### C. What KLHook may write (re/antitamper.md: no code patch, nothing in .rdata)
| lever | where | allowed | effect |
|---|---|---|---|
| AI turn rate 720 deg/s | float 0xcdea94, .data | YES (ceg_ranges.py 0xcdea94:4 first; .data predicted outside) | every AI actor: top speed and ramp (240 -> 120 deg/s at 45 deg, full after 240 ms) |
| AI ramp fraction | [actor+0x578], heap | yes, but rewritten every frame by 0x660780: a tick-thread clamp is racy | per-actor cap, second choice |
| player deadband 90 / 12.5 | 0xce9750 / 54 / 58 / 5c, .data | YES | higher = the body lags the aim longer before a turn clip; 65 = Payday 2 |
| player base step 9 deg | [player+0xaf8], heap | only from a private-vtable wrapper of ZFFPlayer slot 87 (write after stock 0x57fae0); a tick-thread write loses to 0x6d9bce | scales the moving body turn 108..486 deg/s |
| 0.2..0.9 curve, 18 / 72 deg, 0.028, 5 deg, 9 deg, 0.2, 2 deg, 0.01 | .rdata | NO | - |

### D. Live experiment for A (the owner's "heavier AI")
1. TEST hook, `[Rigid] AiTurnDps=240` (0 = off): at init (nothing in the exe writes the global), if klh_may_write allows
   0xcdea94..+4, `*(float*)0xcdea94 = value`; log `rigid: AI turn 720 -> 240 deg/s`.
2. Measure: sample each AI heister's node forward ([node+0x24] / [node+0x2c], what 0x51f910 returns) every tick; log the peak heading
   change in deg/s per bot. Expect peaks near 700 with the key off, none above the key with it on.
3. Watch a bot pivot at a corner; count `move:` stuck lines against a control round (path overshoot: GUESS). Then 360 and 180.
4. For B: `[Rigid] BodyTurnDeg=65` writes 0xce9750 / 54 / 58: the Turn_45/90 clips should start at 65 deg of aim lag; log
   [state+0x1e38] with [player+0xafc] at each change into a turn id.
