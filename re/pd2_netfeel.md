# PAYDAY 2: how remote players (husks) get their weight (2026-10-19)

Purpose: a reference for "slow remote rotations down, make them feel rigid" in Kane & Lynch 2 (`klhook/klnetsmooth.c`).
Source: PD2's own Lua, extracted to `<work>\pd2\lua\` (1,646 scripts, never committed). It is LuaJIT 2.1 BYTECODE
(dump v2, not stripped: chunk names, line info, upvalue and local names are present), not source. No decompiler was
available, so `tools/pd2_lua.py` (parser + disassembler; `dis`, `names`, `str`, `find`) was written. Run it with `python -I`.
Tags: CERTAIN = read in the bytecode, RECALL = general knowledge, GUESS = inference.

## 1. What the sender sends
- Position: `PlayerStandard._update_network_position` sends `player_action_walk_nav_point(pos, move_speed)`. Only when
  floor(dist_sq(last_sent, now)) != 0, and at most every 1/20 s (`tweak_data.network.player_tick_rate` = 20). CERTAIN.
  move_speed = clamp(|stick|, 0, 1); forced to 1 for non-PC controllers / above deadzone. CERTAIN.
- Look: `PlayerCamera.set_rotation` quantizes yaw to 0..255 (360/255 = 1.41 deg steps) and pitch to 0..127 over -85..85
  (1.34 deg steps). Sent via `set_look_dir` only if the quantized value changed AND >= 0.05 s since the last
  (`network.camera.network_sync_delta_t` = 0.05, i.e. 20 Hz max). CERTAIN.
- Receiver decode: yaw = in*360/255, pitch = lerp(-85,85,in/127). CERTAIN.
- Reliability of the sends: GUESS/RECALL (transport is below `network:send`; not read).

## 2. Husk look: two-stage smoothing (HuskPlayerMovement._sync_look_direction) CERTAIN
1. Vector stage: `mvector3.step(current, current, target, dt * 16)` then normalize (`look_direction_smooth_step` = 16).
   (step = linear, length-capped move: RECALL.)
2. Angular stage: target clamped to +-90 deg of the hips' forward; error = angle(target, look).
   rot_speed_rel = min(error/90, 1)^0.5; rot_speed = lerp(40, 360, rel) deg/s; in the combat stance the value is x10
   (ISNEV on a main-chunk local = 3; fairly sure, not independently verified); rot_amount = min(rot_speed*dt, error).
   Examples (non-combat): 1 deg -> ~74 deg/s, 10 deg -> ~147, 45 deg -> ~267, >=90 -> 360 deg/s.
3. The upper body follows through the engine's look modifier (`set_target_y`): internals not readable (engine side).
Older path `update_sync_look_dir` uses the same lerp(40,360) and sqrt curve without the x10.

## 3. Husk body/legs
- Legs trail the look: twist = look yaw relative to leg forward; legs close it at `min(|twist|, dt*120)` = 120 deg/s;
  twist clamped to +-70 deg. CERTAIN.
- Standing still and |twist| > 65 deg: plays redirect `turn_l`/`turn_r`, sets `_turning`, blends params
  angle45/angle90/angle135 by |angle| (>=135 only 135; 90-135 mix 135/90; 45-90 mix 90/45; <45 only 45), switches to
  animation-driven rotation (root motion) and returns to orientation-object driving when the turn anim ends. CERTAIN.
- Moving, turning, bleedout, in air or on zipline: legs are set directly from look_flat * Rotation(-twist). CERTAIN.
- The weight comes from: an angular speed cap, legs lagging behind the head at 120 deg/s, and turn-in-place that is
  authored animation time rather than a free spin. GUESS (interpretation).

## 4. Husk position
- Nav points are queued (`_movement_path`, history 20). A point is dropped if within 2 cm of the last. CERTAIN.
- The husk walks the queue at constant speed: `_get_max_move_speed * dt * node.speed`. Speeds cm/s: stand 350, run 575,
  crouch 225, steelsight 185, in air 185, climbing 200. CERTAIN.
- Elastic catch-up: extra = #path - 2; boost = clamp(extra/20 + 1, 1, 3) (+5 % per queued node above 2). CERTAIN.
- Teleport catch-up: path length >= `player_husk_path_threshold` (30) -> pop to the last 2 nodes and snap. CERTAIN.
- Start moving when path > `player_path_interpolation` (2) or the first node is > ~3 cm away. CERTAIN.
- Animation speed follows displacement (`_displacement_len` stepped at dt*100 up, dt*10 down); anim speed clamped
  [0.05, 2]; walk/run/sprint classes around 250/300/450/500 cm/s. CERTAIN.
- Stance blend times 0.8 / 0.5 / 0.3 s (ntl/hos/cbt), bezier ease. CERTAIN.

## 5. AI (cops) CERTAIN
`CopActionTurn.update`: slerp(current, end_rot, min(1, dt*5*turn_dt_mul)); `turn_dt_mul` = 0.75 for CopActionTurn,
0.5 for ShieldActionTurn (shield cops turn slower: heavier). Plays turn_l/r with the same 45/90/135 blends while
dot(forward, end_dir) < 0.98, then snaps to the end rotation. Server sends `action_turn` with yaw in 0..255 (ceil).
Not read: CopActionWalk / HuskCopMovement internals.

## 6. Recommendations for KL2 (GUESS, to be tuned live)
- klnetsmooth defaults (`MaxTurnDegPerSec`=540, `SmoothMs`=90) are far looser than PD2. For a rigid feel try
  MaxTurnDegPerSec 270-360 (PD2 non-combat top is 360) and an error-dependent cap like PD2: ~40 + 320*sqrt(err/90).
- Make the cap error-dependent (small corrections slow, large ones fast); this hides 20 Hz quantization jitter.
- Lag the legs/body behind the head at ~120 deg/s with a +-65-70 deg twist limit if the displayed heading is the body.
- Quantize like PD2 (1.4 deg) only on the sender; on the receiver, never extrapolate look.
- Position: keep a short queue (2 nodes), speed-boost 5 % per extra node, snap at 30 nodes.
- Heavy characters (shields, bosses) can use a lower multiplier (PD2: 0.5 vs 0.75).
