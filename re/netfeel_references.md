# Net feel: reference designs for rigid, weighty remote characters (2026-10-19)

Goal: a model for how another player's body is DISPLAYED on this PC in Fragile Alliance (no "spinbot" look), with numbers
and where they come from. Display only; never touches own character or server hit logic.
Labels: CERTAIN = read in a file or exe on this PC. RECALL = documented behaviour from memory, not checked here. GUESS = my inference.

## 1. What was actually readable on this PC (CERTAIN)

Honest result: almost nothing. The other games ship their data packed or encrypted.
- CS:GO (G: and C:): `csgo/cfg` holds only gamestate_integration_*.cfg and server_blacklist.txt. Defaults are inside VPKs. No cl_interp text found.
- Deadlock (C:): `game/citadel`, packed VPK. GTA IV (G:): `GTAIV/pc`, `common` are RPF archives (encrypted); no pedpersonality.dat or handling.dat readable.
- PUBG (G:): `TslGame/Config` has only DefaultCompat.ini and DefaultLightmass.ini. Squad / Chivalry 2: the readable user configs in `%LOCALAPPDATA%\SquadGame`, `\TslGame`, `\Chivalry 2` (Engine.ini, Game.ini, GameUserSettings.ini) hold only paths, frame-rate limits and graphics. A grep for NetworkSmoothing, RotationRate, ClientNetSendMoveDeltaTime, MaxClientRate, TickRate, cl_interp, TurnRate in all of these found 0 hits. So the owner has no tweaked netcode ini; engine defaults apply (RECALL below).
- Halo MCC, Halo Infinite, Ghost Recon Breakpoint: packed / only logs. Nothing.

Everything in sections 2 and 3 is therefore RECALL, except Payday 2.

## 2. Payday 2 (CERTAIN, read from the shipped Lua bytecode; the best real reference found)

Source: `<work>\pd2\lua\lib\units\beings\player\huskplayermovement.luac` and `lib\tweak_data\networktweakdata.luac`
(already extracted under `<work>\pd2\`; parsed with a throwaway LuaJIT-bytecode reader, constants only; `husk` = the remote player's body).
Bytecode gives names and numeric constants per function, NOT the logic, so how the numbers combine is GUESS.
- Remote player is split in layers (names in the file): `_look_modifier`, `_head_modifier`, `_arm_modifier`, `_mask_off_modifier`
  (animation modifiers that aim the body parts), `set_modifier_blend`, `segment_state upper_body`, `_sync_look_dir` (the replicated aim direction),
  `_smooth_look`, and a separate `_update_rotation_standard` (lower body / root).
- `look_direction_smooth_step` is a tweak value read from `tweak_data.network.camera` (networktweakdata). The look functions
  (protos 78..92) use `lerp`, `min`, `pow`, `angle`, `rotate_with`, `to_polar_with_reference`, and the constants 90 and 0.5 (and 0.15 in the
  blend function). GUESS: the head/arm follow the aim within +-90 degrees, blended by `min(angle/90, 1)^0.5`-style easing, 0.15 a blend step.
- Turn in place (proto 130, `_update_rotation_standard`): it plays `turn_l/turn_r` redirects with parameters `angle45`, `angle90`, `angle135`
  and holds the constants 45, 90, 120 (and 3). GUESS: legs turn only when body-vs-aim yaw exceeds 45 degrees, picking a 45/90/135 turn clip
  by size; below that the root does not move at all (that is what makes it feel rigid). `_turning` is a state flag; `set_root_blending` is used.
- Walking position: remote movement is NOT snapped to packets. It keeps `_movement_path`, `_movement_history`, uses
  `player_path_interpolation`, `player_path_history`, `player_husk_path_threshold` (all in networktweakdata) and `_perform_path_catchup`:
  the husk walks along the sender's recent path at `_get_max_move_speed` (walk/run/crouch multipliers) and speeds up (constant 1.1 in proto 240)
  to catch up. So position follows with speed limits, distance_sq threshold for a teleport/catch-up.
- Other numbers present in networktweakdata: 0.05 and 1.005. Name mapping not recoverable from constants: RECALL says
  `network_sync_delta_t = 0.05` (a 20 Hz look sync) and `stealth_speed_boost = 1.005`; GUESS. `player_tick_rate`, `player_path_history`,
  `player_husk_path_threshold`, `player_path_interpolation` values sit in an inlined table template and were not decoded. RECALL: tick rate about 30 Hz.
- Lesson (GUESS from structure): the heavy feel comes from (a) aim replicated as a DIRECTION and applied to upper body only with a cap, (b) legs
  re-oriented only past a threshold with an authored clip, (c) position as speed-limited path following.

## 3. Documented engine behaviour (all RECALL, from memory; treat as starting points)

### Source (CS:GO, Deadlock is Source 2 with the same ideas)
- Remote entities are drawn in the past: render time = now - lerp, lerp = max(cl_interp, cl_interp_ratio / cl_updaterate). CS:GO defaults
  cl_interp_ratio 1 to 2, update rate 64 -> about 16 to 31 ms; Source 2 / Deadlock similar. Rule: at least 2 snapshots so one lost packet does not stall.
- Extrapolation is capped (cl_extrapolate_amount about 0.25 s), then entity holds.
- Server lag compensation: rewinds other players to the shooter's view time (command time minus lerp), limit sv_maxunlag 0.2 s (200 ms). So the
  shooter's screen is authoritative within 200 ms. Visual smoothing is separate and never changes the hitbox history.
- Body animation: eye yaw drives the upper body pose parameters (aim_yaw, aim_pitch clamped to about +-58 degrees standing in CS:GO);
  the feet yaw trails the eye yaw and only turns when the difference passes the clamp or the player moves; slow trailing speed (tens of degrees
  per second when idle, GUESS on the exact figure). Source SDK constant: a minimum turn angle of about 15 degrees before a turn animation.
- Local view error from prediction is smoothed over cl_smoothtime 0.1 s (applies to own player only).

### Unreal Engine 4/5 (Squad, Chivalry 2, PUBG): CharacterMovementComponent simulated proxies
- NetworkSmoothingMode: Exponential (default for clients), Linear, Disabled. Smoothing moves only the MESH relative to the capsule; the capsule
  (hit, gameplay position) snaps to the replicated value. This is the fairness trick: visuals smooth, authority unsmoothed.
- NetworkSimulatedSmoothLocationTime 0.100 s, NetworkSimulatedSmoothRotationTime 0.050 s; listen-server variants 0.040 / 0.033 s.
- NetworkMaxSmoothUpdateDistance 256 cm (larger error = fast catch up), NetworkNoSmoothUpdateDistance 384 cm (larger = hard snap).
- Client sends moves at ClientNetSendMoveDeltaTime about 1/60 s (throttled 1/45 s); server NetServerMaxTickRate 120; Character NetUpdateFrequency 100 default.
- RotationRate default (0, 360, 0) deg/s; the Third Person template sets 500 and bOrientRotationToMovement = true. Rotation of the body toward a target
  is a rate limit (RInterpConstantTo-style), not instant.
- Aim offsets: pitch replicated as one byte (RemoteViewPitch, about 1.4 degree steps); the aim offset blendspace covers +-90 yaw and +-90 pitch;
  the character body turns only when the aim yaw leaves that window (turn in place, usually from about 45 to 90 degrees). Common aim smoothing: RInterpTo speed about 15 (time constant about 65 ms).
- Exponential smoothing: error decays by about e^(-dt/tau) each frame, tau on the order of the smooth time divided by about 3 (GUESS on the exact divisor).

### GTA IV, Halo, GR Breakpoint
- Nothing numeric recalled with confidence. GTA IV peds turn with a heading-per-second limit and cover/aim states; Halo runs a 60 Hz simulation with
  client-side prediction of others and server authority. Not usable as numbers. Left out on purpose rather than invented.

## 4. Model to use for Kane & Lynch remote players (starting values, all GUESS to be tuned live)

What K&L already does (CERTAIN, re/netcode_receiver.md): heading is a 16-bit int, 1024 counts per turn (162.9746 per radian); it is extrapolated with
c + v*dt + 0.5*a*dt^2 with NO cap on dt; deltas are plain sign-extended differences (no shortest-arc wrap); position is steered with stick bytes,
teleport past a squared-distance value 1,000,000 (maybe, unproven); the dead-reckoning end time is 3500 ms, the sender refreshes about every 2 s.

Proposed display model, display layer only:
| item | value | basis |
|---|---|---|
| interpolation delay | 100 ms (two 50 ms steps) | PD2 0.05 s sync, Source 2 ticks, UE 100 ms |
| extrapolation cap (dt bound) | 250 ms, then hold | Source cl_extrapolate_amount |
| max displayed yaw rate, root/legs | 270 to 360 deg/s (=770 to 1024 counts/s); "heavy" 180 | UE default 360; GUESS for heavy |
| yaw delta between samples | take shortest arc: ((d + 512) mod 1024) - 512 | fixes wrap spin (H2), sound practice |
| any single step > 180 degrees | treat as sender glitch, rate-limit instead of following | GUESS |
| upper body aim offset | follows aim up to +-90 degrees, easing, time constant 50 to 65 ms | PD2 constant 90, UE aim offset |
| lower body turn in place | legs stay until |aim - legs| > 45 degrees, then rotate at the rate limit | PD2 45/90/120, Source ~15 to 58 |
| rotation smoothing | exponential, tau about 50 ms | UE NetworkSimulatedSmoothRotationTime 0.05 |
| position smoothing | exponential, tau about 100 ms visual offset only | UE 0.1 s |
| position catch-up | error < 2.5 m smooth, 2.5 to 4 m fast catch-up, over 4 m snap | UE 256 / 384 cm; K&L unit scale unverified (GUESS) |
| catch-up speed | up to 1.1x of the actor's run speed | PD2 constant 1.1 |

Fairness and hit registration: all of the above change only what this PC draws for other players (the mesh offset), as UE does. Do not change the
replicated state, packets or the server's view of positions. Source-style rewind is not needed because K&L hits are decided by the host/shooter
under the stock rules; a display delay of 100 ms is below Source's 200 ms rewind budget and is not fed back into any game logic.
The visual body must not drive the aim ray of the remote player on this PC if it ever feeds local effects (GUESS, check before building).

## 5. Open items
- `klhook/klnetsmooth.c` did not exist when this was written (checked), so no comparison with the other workflow's constants was done.
- To make the PD2 numbers firm: decode the networktweakdata table template (needs the KTAB hash part plus the KNUM mapping of the instruction stream) and the bytecode of `_update_rotation_standard`; not done.
- Source and UE numbers need a source other than memory if they matter; none installed here exposes them.
