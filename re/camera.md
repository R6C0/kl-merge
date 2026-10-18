# Camera rework: design for klhook/klcam.c (static, nothing run)

Scope: client-side camera only (ZFFCamera1, vtable 0xbb76a4, build 0490). No gameplay or netcode state is changed except the
local player's own camera-side bits that the shoulder key already writes. Works offline Arcade and online FA.
Labels: READ = from code/dump per the research reports, ASSUMPTION / GUESS = not verified. Nothing here was run.

## 0. Constraints that shape the design

- SHIP builds (the owner's build) may write only IAT, .data/.bss, heap. All kl2 code and .rdata are refused (CEG hashes them).
  So the default path uses only: data writes, calls into game routines, and a private vtable copy of a heap object (same recipe as
  klfreeclimb.c:499-514, klfc_vt). Byte patches of code are a TEST/session-only fallback, listed but never default.
- Game-thread hook point: `klh_rcb_ra == 0x87aa82` (after the world update at 0x87aa6a..0x87aa7c, ASSUMPTION: camera tick
  event 0x10 -> slot 25 0x8f3300 -> 0x650070 has run and render follows). Module code runs only `if(game_thread && klh_rcb_ra==0x87aa82)`.
  The 100 ms fallback thread (`klh_tick(0)`) does nothing except one-time data writes that are idempotent.
- dt = float [[0xdd2640]+0x50], frame counter int [[0xdd2640]+0x48]. All filters are dt-based; dt is clamped to [0.001, 0.1].
- Local player P = [gd+0x828+4*idx], gd=[0xdd265c], idx=byte [gd+0x898], valid only if klh_rd32(P)==0xbb45f4. Camera cam=[P+0xbd8],
  valid only if the locator test klh_rd32(klh_rd32(cam)-4)==0xc8e50c (NOT a raw vptr compare, so a swapped vtable still passes).
  Any read failure (klh_rd returns 0), null P/cam, menu, no round: the module returns at once and clears its filter state.
- Every read through klh_rd/klh_rd32, every write through klh_data (never raises, refuses non-RW pages). Calls to game code are
  wrapped in klfc_guard (__try/__except plus fnstcw/fninit/fldcw restore, klfreeclimb.c:162-185). Three guarded faults in a row
  disables the feature that faulted and logs `cam: feature X disabled after fault`.
- Hitches: the log showed 1.8-2.7 s frame hitches (2026-10-17 19:33). Part of "stuck" may be hitching, not the camera. The Log
  feature records frame time next to camera state so the two can be separated before any lever is blamed.

## 1. ini ([Camera] in KLHook.ini; all read once in klcam_init, restart to change)

```
[Camera]
Enable=1          ; master switch; 0 = module does nothing at all, no writes, no vtable swap
Log=0             ; read-only measurement (feature F4)
LogHz=20          ; 1..120
Blend=1           ; F1a profile blend times
BlendScale=0.4    ; GUESS, multiplier on the 3 blend times (min results clamped 0.05)
Unstick=1         ; F1b watchdog / counter / latch recovery
Recover=1         ; F1c collision pull-in recovery rate limit
RecoverSpeed=350  ; GUESS, cm/s the eye may move outward after a pull-in
ShoulderCover=1   ; F2 shoulder swap in cover and cover aim
LeanFollow=0      ; F2 stage 2 (lean-out side), default 0 until logged live (see 4.4)
Cine=1            ; F3 aim transitions, shoulder flip, shake
CineAim=1         ; F3a cover-aim profile softening
FlipTime=0.35     ; GUESS, F3b shoulder flip seconds (stock 0.2)
ShakeScale=0.8    ; GUESS, F3c per-state docu-cam multiplier for movement states
FovStep=0.20      ; GUESS, F3d FOV lerp per step (stock 0.295)
```
Master "on by default except Log" is satisfied. Because everything here is untested, the first live build ships the defaults above
but the test order in section 7 must be followed, and each feature has an independent off switch for bisecting.

## 2. Module wiring (klhook.c, by hand)

`#include "klcam.c"` directly after klshoulder.c (klhook.c:643, same translation unit); `klcam_tick(game_thread);` next to
`klo_tick` (klhook.c:767) inside klh_tick; `klcam_init();` in the DllMain init list after klp_init and before klvis_init; update
the file table in klhook.c's header comment. File shape: `#ifndef KLCAM_C / #define KLCAM_C`, static struct `kc`, init reads ini via
GetPrivateProfileIntA/StringA (floats: String + atof, klmove.c:1082-1097). OFF = return first thing in tick. The draft read-only
klcam.c (scratchpad\cam\klcam.c, compiled clean) is the starting point for F4. klshoulder.c is left alone, except its label for
[P+0x2954] should be changed from "aiming" to "coverside" (see 4.1); that is a separate small edit.

Unload/restore: the hook has no unload path that runs in a game session (process exit only), so "restore" means: (a) the private
vtable and profile writes are applied to objects/data the game recreates per level, and (b) Enable=0 or any disable-on-fault path
calls `klcam_restore()`, which writes back the saved original floats/vptr/bytes of every thing the module changed (each change is
recorded as {address, original bytes} when made). Restore is also called when P or cam changes identity (new level, respawn).

## 3. Root causes and fixes for "stuck / slow catch-up" (F1)

Ranked by evidence. Only (a) is a confirmed mechanism; (b)-(d) are candidates that the Log must confirm before being trusted.

### F1a Profile blend times (READ for values, effect DERIVED)
- 24 profile structs, 0x198 bytes, base 0x154a820, selected by 0x778f50, applied by 0x5ea690. Blend times at struct +0x170 (x/y? first),
  +0x174, +0x178; copied to camera +0x560/+0x564, timer +0x5a0, then 0x48ec00 turns them into smoothing constants +0x590/+0x594.
- FA default profile 0x154b810 = 0.2 / 3.0 / 2.0 s, cover low 0x154ab50 = 0.4 / 3 / 0.8, cover aim 0x154ace8 = 0.1 / 0.5 / 0.2.
  The chaser has a = 8*d/T^2 (0x51b430), so settling is about 0.71*T: 3 s -> ~2.1 s. That matches "takes forever to follow".
- Fix: data-only. At each level load (detect by P/cam identity change, plus once per 5 s while a round runs as the structs may be
  re-initialised, ASSUMPTION), for each of the 24 structs, `new = max(0.05, orig * BlendScale)` for the three floats, writing
  through klh_data. Skip any struct whose floats are not finite or outside (0, 20] (refuse and log), which also guards a wrong base.
  Original value check: before first write the module reads all 72 floats and verifies profile 0x154b810 +0x170/174/178 ==
  {0.2, 3.0, 2.0} within 1e-4 and 0x154ab50 == {0.4, 3.0, 0.8}; if they differ the whole feature is refused with a log line (build
  mismatch or already modified). The cover-aim profile (0.1/0.5/0.2) is handled by F3a, not here, so it is skipped by this loop.
  Special profiles 0x154c1a0 (0.01) and 0x154c4d0/0x154cff8 are not touched.
- Off-mode: no writes. Restore: saved originals. Thread: either, but only before the first write is the game thread required.
- Risk: low; too small a value looks twitchy (BlendScale 0.4 is a GUESS: 3 s -> 1.2 s, 2 s -> 0.8 s).

### F1b Unstick watchdog (candidates, ASSUMPTION; recovery only acts when the Log's stuck detector proves a stuck state)
Detector (game thread, per tick, dt-based): stuck if the player is alive and in a round, player speed vP > 200 cm/s, the camera eye
(cam+0x508) speed vE < 20 cm/s, continuously for > 0.5 s, and the frame time is normal (the last dt < 0.1; hitches are excluded).
It is the same latch as the measurement draft, so detection exists in F4 even with Unstick=0.
Recovery ladder, one step per 0.5 s while still stuck, in this order (each step is a local write to the camera, and each is
logged; a step is skipped if its precondition read fails):
1. Tick counter: if int [cam+0xc54] <= 0 while P alive and the camera-busy gate is false, write [cam+0xc54] = 4 (READ: 0x650178 returns
   early at <= 0; 0x6501a8 sets it to 4 each frame while the system byte [[[0xdd2640]+0xac]+0xbc] is 0). Also log the value of that
   system byte every time (it is unknown whether it can stay set in play; open question from `follow`).
2. Pull-in latch: if byte [cam+0x394] == 1 for > 0.5 s and the distance [cam+0x124] is not changing, write [cam+0x394] = 0 once.
   (0x56e4c0 only places the camera when +0x394 != 0; a latch that never clears keeps the old position.)
3. Blend timer: write float [cam+0x5a0] = 0 (blend finished) and [cam+0xca0] = 1.0, which is what the 0x5de5fe snap branch does
   (READ: message handler sets +0xca0 = [0xceb648] = 1.0).
4. Stale side: if byte [P+0x280c] != the byte at [cam+0xb40] for > 0.5 s, write [cam+0xb40] = [P+0x280c] (0x9088c0 compares them).
5. Give up: log `cam: stuck unrecovered` and stop for 5 s (no repeated writes).
Not done: skipping the [[0xdd265c]+0x4cd8] test at 0x6500e3 (that is a global pause/cut flag, ASSUMPTION; never touched).
Off-mode: detector runs only if Log or Unstick; no writes when Unstick=0.
Risk: medium; a false positive causes one small snap. Every precondition above is read first.

### F1c Collision pull-in recovery limit (READ for structure, effect ASSUMPTION)
0x897d60 sweeps from the pivot (cam+0x398) toward the previous eye; a hit sets +0x124 = distance, +0x394 = 1; 0x56e4c0 puts the eye at
pivot + dir*+0x124 + offset + Z lift (clamped 10). No smoothing: the eye snaps both in and out.
- Goal: pull in instantly (never clip), recover outward at <= RecoverSpeed cm/s.
- Method (SHIP-legal, no vtable required): after the camera tick, at gameplay site 0x87aa82, read eye E=[cam+0x508] and pivot
  Pv=[cam+0x398] (3 floats). Keep `prev_dist` = |E_prev - Pv_prev| of the last frame. If this frame's distance d > prev_dist +
  RecoverSpeed*dt AND the camera was blocked last frame (byte [cam+0x394] was 1 last frame, or [cam+0x124] changed) AND the move is
  mostly along the pivot->eye line (angle between the move and the line < 30 deg; a plain player run must not be filtered), then set
  E' = Pv + (E-Pv)/d * (prev_dist + RecoverSpeed*dt), write [cam+0x508] = E' and apply it by calling the node setter
  0x7c9030 (KLFC_CALL, __thiscall, under klfc_guard). Reset the state (no filter) on: d jump > 300 cm, teleport (player feet move
  > 300 cm in a frame), respawn, new cam, dt >= 0.1, cut cameras (see 6).
- Check before enabling: read the 5 bytes at 0x7c9030 and refuse the feature if the function prologue differs from the dump (`klh_rd`
  compare with the expected bytes recorded at design time; the implementer must fill these from kl2.exe, not guessed here).
- Safety: E' is always nearer to the pivot than E (it only shortens), so it can't push through geometry the game just cleared; the
  trade-off is E' may be 'inside' freed space only. Clipping risk is limited to the pivot side (already safe).
- UNKNOWNS that must be resolved before this is on: (1) is the render after the 0x87aa7c call in the same frame, (2) 0x7c9030 calling
  convention and whether it recomputes the orientation or only position, (3) whether the node position at [geom+0x24] equals
  [cam+0x508] unless a parent transform at node+0x50 applies. If the Log (F4) shows node pos != eye pos, this feature refuses itself.
  The feature has a self-test: after the setter call the module re-reads [geom+0x24]; if it is not within 0.5 cm of E', it disables
  itself with a log line.
- Off-mode: no writes. Restore: nothing persistent (eye is recomputed by the game each frame).

### F1d Smoothing reset pop (READ mechanism, fix is code => TEST-only)
0x48ec00 zeroes the six channels (+0x678, +0x6ac ...) whenever the smoothing time constant changes (every profile switch). A data-only
substitute that is SHIP-legal: do not remove the reset, but reduce how often the time changes. With F1a all 24 profiles are scaled by
one factor so no new switch is introduced. The alternative: write +0x590/+0x594 every frame with a constant (needs the 6 channels' dirty
semantics, not read) is NOT done. A code patch of the zeroing is listed only as a TEST/session experiment, no bytes are given
because the instruction addresses inside 0x48ec00 were not read. Default: not implemented.

## 4. Shoulder swap in cover and cover aim (F2)

### 4.1 Facts (READ)
- [P+0x2954] is a signed cover/aim-point side (0, +1, -1), nonzero whenever attached to cover (set 0x453580, negated 0x4520d0,
  written 0x6bbb40). The label "aiming" in re/shoulder_m02.md and klshoulder.c is wrong (from the `shoulder` report; the `aim` and `hook`
  reports still call it "aiming byte", they disagree; the code read in `shoulder` is authoritative: cmp at 0x64011d is the gate).
- Key handler 0x640080: `cmp byte [eax+0x2954],0` at 0x64011d (80 B8 54 29 00 00 00), `jne 0x640211` at 0x640124 (0F 85 E7 00 00 00).
  The toggle of [P+0x29a0] (wanted side) and the 0.08 s SwitchCameraSide timer are skipped when it is nonzero.
- Side in use: bit 10 of [P+0x818] and byte [P+0x280c]; only writer is setter 0x74a120(P, left, seconds). Cover forces its side
  only at enter (0x823a1c: 74a120(P,[state+0x104],0)) and leave (0x71f3f9: 74a120(P,(104==0),0)); the camera restores [P+0xb84] at
  0x5ea972..0x5ea984; exit routine 0x513d80 writes b84 = ([29a0]==0 ? +1 : -1). No per-frame forcing inside cover.
- Cover state (vtable 0xbb5b6c slot 17 0x8d7f60) copies the shoulder bit into [state+0x105] each frame; decider 0x89fd90 reacts to a
  change with action 1/2 (a re-seat; believed harmless, ASSUMPTION).
- Other gates in the handler: [[0x168d7c0]+0x209], [P+0x2720]&2, [P+0xd50], [P+0xed0] bit 7, [H+0x330]. They stay.

### 4.2 SHIP-legal method: wrap the key handler in a private vtable (preferred)
The handler 0x640080 is a method of the gameplay-input object (ZGameplayInput, heap). Steps at init/level load:
1. Find the input object H and the vtable slot that holds 0x640080 by scanning H's vtable (up to 120 dwords) for the value
   KLH_VA(0x640080). If it is not found exactly once, refuse F2 and log. (The slot index is not known from the reports.)
2. Verify the two gate instructions by reading 0x64011d (7 bytes) and 0x640124 (6 bytes) and comparing with the byte strings above.
   If they differ, refuse (build mismatch) and log. This check is read-only and so allowed in SHIP.
3. Copy the vtable (locator at [-4] kept), replace that slot with `klcam_key_wrap`, and write H's vptr with klh_data. Keep the old
   vptr for restore.
4. `klcam_key_wrap(this, args...)` (stdcall/thiscall exactly as the original, to be read from the prologue; ASSUMPTION): if ShoulderCover
   and P valid and byte [P+0x2954] != 0 and not in the "refuse" states below, then save s = [P+0x2954], write 0, call the original,
   write s back (restore even on fault via __try/__finally), then post-process (4.3). Otherwise just call the original.
   [P+0x2954] is only zero for the duration of one input call on the game thread, nothing else reads it in that window
   (single-threaded input handler; ASSUMPTION: the handler does not call into code that cares, e.g. network update 0x4520d0; the handler's
   own listing shows only the toggle).
5. Refuse states (no un-gating): dead/down ([P+0xed0] handled by original gates), cut scene or camera-busy (0x670210 true), cover
   transition in progress (state action != steady; unknown, so use: the wrap is skipped if the last 0.2 s saw a change of [P+0x2954]).
This keeps all other original gates in force. Because the original toggles [P+0x29a0] and the camera applies it through its own spline
path (0x9088c0 compares [P+0x280c] with [cam+0xb40]), no call of 0x74a120 is required for the first stage. If the Log shows [P+0x280c]
never follows [P+0x29a0] in cover (ASSUMPTION about who calls the setter), the wrap additionally calls 0x74a120(P, newwanted, FlipTime)
under klfc_guard.
TEST/session fallback (not default): NOP the 6-byte jne at 0x640124 (original bytes verified first; restore on disable). Not in SHIP.

### 4.3 After a successful in-cover toggle (all local, via klh_data)
- Keep the restore value in sync: [P+0xb84] = ([P+0x29a0]==0 ? +1 : -1) (same formula as 0x513dcb..0x513de9), so the camera's restore at
  0x5ea984 and the exit path at 0x71f3df..0x71f3f9 do not snap back to the pre-swap side on leaving cover. Written only if the
  old value is -1 or +1 (sanity).
- Camera: write [cam+0x5a0] unchanged (let the profile blend run); the shoulder blend [cam+0xb9c] is walked by 0x9088c0.
- Cover camera profiles (0x154ab50, 0x154ace8, 0x154ae80): whether the horizontal offset sign flips with the bit or the profile is
  mirrored is UNKNOWN (open question). The Log records [cam+0xb9c], the x offset at +0x530 and the profile pointer [cam+0xb2c] across a flip
  so this can be answered from the first run.

### 4.4 Lean-out side (LeanFollow, stage 2, default 0)
The lean-out comes from the cover state side (+0x104) and cover point data ([P+0xb50..0xb58], points array 0x7a26d0, clearance flags
[P+0x2d6c]), tried by 0x556b00. Flipping only the camera leaves the body leaning out of the old edge. Plan: only after F2 stage 1 is
confirmed live and the Log has recorded [state+0x104/0x105/0x29c] and [P+0x2d6c] in cover:
- Route to the active cover state object: NOT FOUND. Scan the player's movement-state slots/pointers for an object whose vptr ==
  0xbb5b6c (the Log's first job in cover); until found, LeanFollow stays unavailable and logs `cam: lean state object not found`.
- Safe condition: flip +0x104 and let 0x89fd90 do its own re-seat (assumed action 4) only if the opposite edge's clearance bit in
  [P+0x2d6c] is set; the bit meaning is NOT decoded. So the implementation is a stub gated by a table that the implementer fills from the
  first log. If the opposite edge is not free, the camera swap still happens but the body stays (camera-only mode) and the module
  does not flip +0x104.
- Aim-ray problem when the camera is on the wall side: GUESS, mitigation is none in v1 (logged only).
Netcode: the cover side is replicated through 0x4520d0 (network update of the cover side, READ). Writing +0x104 or 0x2954 would be a
gameplay change visible to peers. Therefore LeanFollow is the ONLY item that might alter replicated state, which is why it is off and
experimental; offline Arcade is where it is validated first. Stage 1 does not alter any replicated value: the toggle writes [P+0x29a0]
(the camera wanted-side, same value the stock key writes outside cover; whether that is replicated is unknown, ASSUMPTION it is local).

## 5. Cinematic smoothing (F3), all values GUESS

- F3a Cover-aim profile 0x154ace8 (FOV 0.698 rad at +0x550, h 35, dist 110, timing +0x170..0x178 = 0.1/0.5/0.2, READ): write the three
  timings to 0.25/0.5/0.35 and FOV to 0.80. Original value check: verify {0.1,0.5,0.2} and 0.698 (+-0.005) before writing; else refuse.
  CineAim=0 leaves it. (Offsets +0x550 for FOV are from the `aim` report; the `hook` report puts FOV at +0x15c. They disagree: the
  implementer must verify with a dump read of the profile before writing the FOV, and skip the FOV write if the field at the chosen
  offset is not near 0.698. The timing offsets agree across reports.)
- F3b Shoulder flip duration: floats at 0xceb5e0 (0.2), 0xceb5e4 (0.1), 0xceb5e8 (0.8). These are .rdata => hashed/refused in SHIP.
  So in SHIP the flip time is controlled instead through the setter call's seconds argument when the module calls 0x74a120 itself (see
  4.2 fallback), which means: in cover and in the open the module, on a want change, calls 0x74a120(P, left, FlipTime) and sets the
  key's own call to be a no-op by matching sides. If that proves fragile, F3b degrades to 'unchanged'. Easing the sweep through x=0
  (behind the head) is not possible without code; mark as a TEST-only experiment.
- F3c Shake: docu-cam shaker (docucamshaker.cpp, ctor 0x641410), 41 per-state float multipliers at shaker+0x34, all 1.0 (READ from dump).
  Heap object. Find it by scanning the camera object for a pointer whose target has the expected vptr (to be read from the ctor; the
  vptr value is NOT in the reports: the implementer reads it from 0x641410). Only if found: multiply entries for movement states by
  ShakeScale. Which indices are movement states is NOT known (GUESS: leave 0, write all but explosion/hit states if known). Initially
  scale all 41 by ShakeScale and leave explosions' camera shake alone via the separate explicit-shake path 0x4baa40 (not touched).
- F3d FOV lerp 0.295 at 0xb24824 (.rdata, refused in SHIP) and the FOV snap flags +0x7b4/+0x7b5 (heap bytes, writable). In SHIP:
  FovStep is not applied (log 'FovStep needs TEST'); the snap bytes are cleared after the tick if set and the FOV channel +0x790 is
  below the target by > 0.05 rad? NOT designed because the write sites are unknown: dropped from v1.
- F3e Cinematic follow: F1a (shorter than stock but critically damped chasers from the game itself, so motion stays ease-in/out) plus
  F1c. No new filter on orientation (the node orientation writer is unknown; a position-only filter would desync view direction).
  Decision: no extra low-pass on the eye in v1. The 'cinematic' feel comes from the game's own chasers, with sane timings.

## 6. Safety: no player, menus, cut cameras, death

- Return at once when: Enable=0; gd null; idx out of 0..3; P null or vptr != 0xbb45f4; cam null or locator wrong; P dead/down for F1c/F2
  (read the same dead flag kldown.c uses at its camera section kldown.c:1628-1640, ASSUMPTION it is reusable); camera-busy 0x670210 true
  (call is allowed, read-only? ASSUMPTION; if unsure, skip the call and use [[0xdd265c]+0x4cd8]!=0 as the cut/pause flag).
- A cut/scripted camera (not the ZFFCamera1 on the local player) is a different object; the locator test fails => nothing is done.
- On identity change (P or cam or scene) the module restores everything it changed on the old object (vtable pointers are on freed heap
  objects, so restore is a no-op when the old object is gone: guard with klh_rd before writing) and re-installs on the new one.
- Online FA: the hook writes only to the local player's camera object and local profile floats. Profile floats are client data. The
  local-camera wanted side is the only player-struct write in F2 stage 1 (see 4.4). Remote players are never touched (idx = local only).
- Per-frame cost target: < 20 microseconds. No allocation per frame, no log unless Log=1 or a state change.

## 7. Measurement (F4, read-only, [Camera] Log=1)

Line `cam:` at LogHz (default 20) from the game-thread site only. Fields: frame counter, dt, hitch flag (dt > 0.033), P feet (+0x460) and
speed, eye (+0x508) and speed, node pos ([geom+0x24]), pivot (+0x398) and dRig, horizontal and 3D distance eye-player, blocked
(+0x394), collision-enabled (+0x7eb), pull-in dist (+0x124), blend (+0x5a0), shoulder blend (+0xb9c), side (+0x280c), wanted (+0x29a0),
coverside (+0x2954), bit 10 of +0x818, [P+0xb84/b88/b8c], profile pointer (+0xb2c) and its three timings, FOV ([node+0x70]), the tick
counter +0xc54, system byte [[[0xdd2640]+0xac]+0xbc], flag [[0xdd265c]+0x4cd8]. A `STUCK` suffix when the detector in F1b fires. Extra
line `camev:` at every change of side, profile, stuck, blocked, coverside, with a reason. 10 s summary: max dist, stuck seconds, tau
percentiles (tau = dRig/vE while vE>5), pull-in frames, hitch frames.
Offline fit: after a 180-degree turn fit an exponential to (eye - (rig+offset)) to compare with the 0.2/3/2 constants.
Unattended scripted round (TEST build, not the owner's): `tools/kl_autotest.py` with a `[Script]` as in KLHook.round.ini: waitstate
0x19, goto, face/mouse turn, tap cover (C), hold X >= 0.2 s for SwitchCameraSide, mdown 1 for aim (ASSUMPTION button), `log` markers.
Run the script before and after each lever, compare stuck seconds, tau, blocked fraction, side settle time. Live runs are paused when the
owner plays; static phase now.

## 8. Implementation order (smallest robust first)

1. F4 Log (read-only), one scripted round: confirms hitches vs camera, tells which of F1b's candidates occurs, resolves the 4.3 and 4.4
   questions, and gives the node-vs-eye check for F1c.
2. F1a Blend (data only): immediate effect on "takes forever".
3. F2 stage 1 (vtable wrap + b84 sync), tested offline in cover, cover aim and leaving cover.
4. F1b recovery ladder with detector; F3a.
5. F1c only if the Log shows the snap-in/out pattern and the node equality holds.
6. F3c shake once the shaker's vptr and state indices are read; F2 stage 2 last, if at all.
Each step: build SHIP, `debug/check.py` unaffected (no level files), install only with the owner's OK (v82f HUD memory: do not
reinstall v82e-h; this module must build on the live hook 8d3ccf81, not on v82e/f).

## 9. Open items the implementer must resolve from kl2.exe (not in the reports)

1. Slot of 0x640080 in the input object's vtable, its calling convention and how to reach H from P or from gd.
2. Prologue bytes of 0x7c9030 and the setter's convention (thiscall, ecx=node?); expected bytes for the refusal checks.
3. Vptr of the docu-cam shaker; which of 41 states are movement.
4. Profile FOV offset (+0x550 vs +0x15c) and whether profile 0x154ace8 floats match before writing.
5. Whether render is after the 0x87aa7c call within the same frame; whether the node orientation is written elsewhere (view direction lag
   can't be fixed by a position filter).
6. Whether [P+0x29a0] is replicated; whether the cover animations support the opposite shoulder.
7. Disagreement between reports on [P+0x2954]: treated as the cover side per the shoulder report (detailed disassembly), the log will confirm.

## Review corrections (2026-10-17, applied to klhook/klcam.c)
- Blend: +0x178 is both the transition duration and the constant used during it (0x5eac54..0x5eac8b); 0x48ec00 uses cam+0x560/0x564 only when cam+0x568 bit 0x10 is set; a profile applies only when the profile POINTER changes (0x5ea6a1). Rewriting a profile mid-flight has no effect until the next change. Profiles 0..24 are scaled (27 exist; 25 is special-cased by address, 26 = 0.5/0.5/0.5, 27 zero: READ in KLHook_1/2.dmp). Profile floats stay changed until the game restarts; there is no put-back.
- Shoulder swap success = the side bit (bit 10 of [P+0x818]) changed; [P+0x29a0] is resynced by the handler first (0x640142..0x64016d). b84 = -1 if left else +1 from the post-call bit. The cover exit (0x71f3df) forces the side from state+0x104, so whether b84 wins is an ASSUMPTION until the camev lines are read live. Offline only (kl_online() gate; [Camera] ShoulderCoverOnline=1 lifts it for a test).
- Unstick: cam+0xca0 is a decaying slow-down (0x48ec78..0x48ecbb), never written; only the blend timer cam+0x5a0 -> 0 (when > 0.05). The "cut camera fails the locator test" claim is wrong: the locator test is on the player's own camera. The detector is gated to plain locomotion (movement id 2/3, no cover/seat/climb), 1.0 s.
- Recover: the apply does not need the latch (cleared by 0x898384 each call); default OFF until Log=1 shows the node equals the eye.

## Round 2 (2026-10-17): measurement and owner test plan (static; nothing run; klcam.c NOT edited, this is the spec)
Asked: stuck camera / slow follow, shoulder swap in cover and in cover aim, smoother/cinematic. This section = what Log=1 must print so ONE owner
session answers it, the gaps in the current log code, the owner checklist, and the summary script. Labels: READ = klcam.c or kl2.exe read now;
GUESS / ASSUMPTION otherwise.

### R2.1 Default keys (READ: the compiled binding string in kl2.exe, 'GameplayInput={...}', right behind SwitchCameraSide; file offset 0x74ed2c region)
Keyboard + mouse defaults: SwitchCameraSide = HOLD X (pad: right thumb click), TapCover/HoldCover = C, HoldPrecisionAim (aim) = HOLD RIGHT MOUSE
(pad: left trigger), TapFire = left mouse, HoldSprint = Left Shift or Space, crouch = Left Ctrl, move W A S D. X is also TapPulseCheck/HoldPulseCheck.
No binding file exists in the Dog Days folder (no input .ini/.xml; Patch01.zip holds only menu/frontend.xml and ingame.xml; the text is compiled in).
If the owner rebound keys in the options menu, where that is stored was not found: the checklist says "your keys for ...".
The shoulder hold needs about 0.2 s or more (the key record's 0.08 s timer, see the klcam.c comments).

### R2.2 What the current Log cannot show (READ klcam.c klcam_tick and klcam_cover)
1. HITCH SIZE IS LOST: `if (dt > 0.1f) dt = 0.1f;` runs BEFORE the log lines, so a 1.8-2.7 s hitch shows as dt 0.1 and one "hitch frame".
   Part of the "stuck" the owner feels may be a hitch plus catch-up. Needs the raw dt.
2. SILENT RETURNS: the `[gd+0x4cd8]` gate returns before every log line (one message after 5 s, never an end); klcam_lost() prints "no local player"
   without WHICH condition failed (gd/idx, P vptr, cam, locator, sys); a failed eye/feet/pivot read, `frame == lastframe` and a bad dt are silent; the tick runs only
   when `klh_rcb_ra == 0x87aa82`, so a frame without that callback site is invisible (no gap measure). A stuck camera that coincides with any of these leaves no line.
3. THE STUCK DETECTOR IS NARROW: `alive && loco && vP > 200 && vE < 20` for 1.0 s, loco = movement id 2/3 and not cover/seat/climb/free-climb. It cannot
   fire in cover, in cover aim, just after cover exit while the movement id is still the cover id, while walking (walk speed may be under 200 cm/s: GUESS),
   when the player stands and the camera lags a rotation, or after a profile switch. It compares the eye with the PLAYER, but the camera chases the pivot
   (+0x398). And it only says "stuck", never WHICH field froze.
4. SHOULDER: `camev: shoulder swapped in cover` prints only when this module fired the key (needs sc_on, cs != 0, kind == 2, cooldown, hold-off).
   Not logged: every raw press of X and why it did nothing (the gates: [[0x168d7c0]+0x209], [P+0x2720]&2, [P+0xd50], [P+0xed0] bit 7, [H+0x330], cover byte),
   a press outside cover, a press with ShoulderCover=0 or online, the lean side, the state after leaving cover. `coverside` prints with %u so -1 shows as 255;
   the generic camev side lines lack bit 10 of [P+0x818], [P+0xb84], [P+0x29a0].
5. AIM: no input edge (no way to time key -> profile switch -> FOV settled); fov only in the 20 Hz line; profiles are raw pointers (0x154ace8 cover aim,
   0x154a9b8 aim, 0x154b9a8 FA aim, 0x154b810 FA default, 0x154ab50 cover low: re/firstperson_camera.md) and no achieved timings. The profile timings are
   printed but not the live smoothing state (+0x560/+0x564 times, +0x568 flags, +0x590/+0x594 constants, +0xca0 slow-down): the real chase speed is missing.
6. No marker: the owner cannot say "NOW"; the wall clock stamp of klog (hh:mm:ss.mmm, klhook.c:216, READ) is the only anchor.

### R2.3 Additions (read-only through klh_rd, inside the Log=1 gate, game thread, same site 0x87aa82)
Time base: add `T <sec>` (QueryPerformanceCounter seconds since start; kc.qf exists) and `rdt` (RAW dt) to cam:/camev: lines.

A. Raw dt and wall gap
 - Keep `rawdt` before the 0.1 clamp. Print `rdt %.4f` in the cam: line. `camev: HITCH rdt %.3f f %ld skipped %ld` whenever rawdt > 0.1 or the frame counter
   ([[0xdd2640]+0x48]) jumped (skipped = frame - lastframe - 1 > 0). `camev: GAP wall %.3f` when QPC since the previous entered tick > 0.25 s (catches frames without the
   0x87aa82 call). One new kc field.
B. Every silent return prints on change (reason code in kc)
 - NOPLAYER (gd, idx, P vptr value), NOCAM (cam, locator value), NOSYS, GATE4CD8 (print the dword), READFAIL (which of eye/feet/pivot), ZERODT.
   `camev: SKIP <reason> begins | f T` and `camev: SKIP <reason> ends after %.2f s`. While GATE4CD8 stands, still one `cam:` line per second (eye, pivot, feet, tick counter).
C. Ungated freeze watch (answers 'what was frozen')
 - Each frame memcmp against the previous frame: F_P feet [P+0x460]; F_PIV pivot [cam+0x398]; F_B0 [cam+0xb0]; F_EYE [cam+0x508]; F_NODE [geom+0x24];
   F_BLEND [cam+0x5a0] (when > 0); F_TICK int [cam+0xc54]; F_SIDEB [cam+0xb9c] (while side != camside); F_FOV [node+0x70]. Consecutive-equal counters (time, sum of dt).
 - "Input active" = any of W A S D down by GetAsyncKeyState (VK 0x57 0x41 0x53 0x44) while the foreground window belongs to this process, or P moved > 1 cm last frame.
 - Episode STUCK2 begins when (input active OR pivot speed > 100 cm/s) AND the eye moved < 0.5 cm total for 0.25 s of dt AND rawdt < 0.1 for those frames (a hitch is not
   an episode); ends when the eye moves > 2 cm in a frame. NOT gated by movement id, cover, or the 0x4cd8 flag (its value is printed).
   LAG2: pivot speed > 100 cm/s, eye moving, but |eye - pivot| exceeds its median of the last 5 s by > 150 cm for > 0.5 s (distance only; the player facing field is not in these reports).
 - Begin line: `camev: STUCK2 begins frozen=PIV,EYE,.. | f T rdt | P .. piv .. eye .. node .. | mv %d kind %02x a54 %04x d50 %lx d44 %lx | blk cd | blend tick sysb flag4cd8`
   plus ONE `camdump:` block (raw hex dwords, 16 per line): cam+0x120..0x15f, 0x390..0x3cf, 0x500..0x53f, 0x590..0x5af, 0xb20..0xb5f, 0xc50..0xcaf; player P+0x810..0x81f, P+0x2940..0x297f,
   P+0xb80..0xb8f. At most 3 dumps a minute. End line: `camev: STUCK2 ends after %.2f s frozen=..` plus the diff list of watched fields that changed in the frame the eye moved again
   (profile ptr, cover byte, blocked flag, blend timer, side, tick counter, key edge).
 - F9 mark: edge of VK_F9 prints `camev: MARK n` + the begin-state + a camdump. (F9 is not among the keys in KL_MOD_SETTINGS.txt: F7, F8, #, Home; ASSUMPTION it is free in game; grep klhook.c before wiring.)

D. Live chase constants (the real follow speed)
 - cam: line adds `t560 %.3f t564 %.3f f568 %08lx k590 %.3f k594 %.3f slow %.3f` from cam+0x560, +0x564, +0x568, +0x590, +0x594, +0xca0 (section 3: 0x48ec00 turns times into constants; +0xca0 is the
   decaying slow-down; +0x568 bit 0x10 selects +0x560/564). A stuck episode with a tiny k590 or slow far from 1.0 is the cause; if those are normal the cause is upstream (pivot / tick / latch).
 - `camev: PROFILE old->new (name)` with the name looked up from the pointer list in R2.2 item 5 and the new timings.

E. Timings achieved (derived, no game call)
 - BLEND: `camev: BLEND start prof .. t a/b/c` when [cam+0x5a0] goes 0 -> > 0 or the profile pointer changes; `camev: BLEND end after %.2f s` when it returns to 0.
 - FOV: track f = [node+0x70]; after a profile change or an aim key edge: `camev: FOV a -> b settled after %.2f s since <profile|RMB down|RMB up>` (settled = |f - f_final| < 2 % of the step for 5 frames; f_final = value when change per frame < 0.0002 rad for 5 frames).
 - EYE settle: with P speed < 5 cm/s, time until eye speed < 5 cm/s: `camev: EYE settled after %.2f s`.
 - SIDEBLEND ([cam+0xb9c], walked by 0x9088c0): `camev: SIDEBLEND %.2f -> %.2f in %.2f s (side %u -> %u, x-off %.1f -> %.1f)` with [P+0x280c] and [cam+0x530]; the achieved flip time (stock 0.2 s, .rdata 0xceb5e0).

F. Input edges (GetAsyncKeyState; the game reads DirectInput only, so no interference)
 - `camev: KEY X|RMB|LMB|C|LSHIFT|F9 down|up` carrying cs, side bit, want, b84, profile, fov, blend, sideb: the key-to-effect delay is the T difference. A `keys` bit string in the cam: line.
 - On X down add the stock gate decision: `gates: cfg209 %u k2720&2 %u d50 %lx a54 %04x ed0b7 %u H330 %lx cs %d kind %u fired %u timer %.3f` and `would_toggle=yes|no(<which>)` for the STOCK handler plus
   `module=fired|skipped(<sc_on, online, cool, cs_s, sc_wait, kind>)`. Closes item 4 above.

G. Cover and lean
 - cs printed signed (`cs %d`, cast signed char). Every camev and cam: line gets bit818 (bit 10 of [P+0x818]), side [P+0x280c], want [P+0x29a0], b84, camside [cam+0xb40], mv (klfc_movid).
 - Lean state object: on the first frame with cs != 0 after a cover entry, ONE read-only scan, off = 0..0x3000 step 4: v = klh_rd32(P+off); if v >= 0x10000 and klh_rd32(v) == KLH_VA(0xbb5b6c) (the cover movement vtable, section 4.1), record off.
   Print `camev: COVERSTATE at P+0x%x obj %08lx` or `not found` (max 5 times a run). 3072 guarded reads once per entry (cost ASSUMED negligible). If found, in-cover cam: lines add `st104 %d st105 %d st29c %d` (state+0x104/0x105/0x29c) and P+0xb50..0xb58 and [P+0x2d6c] hex.
 - `camev: COVER enter|leave` at cs 0 <-> nonzero with the full side set; then `COVER+1.0s` and `COVER+3.0s` after a leave: the 'after leaving cover' answer (does b84 or the cover exit win).
 - Each swap: the existing line 294 plus st104/st105 and camside before/after, and a `SWAP+0.5s` line (sideb, x-off, st104): did the camera finish, did the body lean flip.
 - Cover aim: when RMB down AND cs != 0, a `coveraim` token on cam: lines and on the FOV/EYE/BLEND settle events.

H. Volume: the cam: line is ~600 bytes; 20 Hz = 12 KB/s (43 MB an hour on a log that is already 60 MB). Keep LogHz=20; when nothing moves (vP < 1, vE < 1, no blend, no key) print at 2 Hz.
   The 10 s summary adds STUCK2 count and seconds per frozen field, LAG2 seconds, frames with rdt > 0.1, swaps and failed swaps, max BLEND / FOV settle / SIDEBLEND.
Effort: about 150 lines of C in klcam_tick; no game calls, no writes; GetAsyncKeyState needs user32 (check what klhook already imports).

### R2.4 ini for the single owner session
Measure STOCK behaviour; Blend/Unstick/Recover would change or hide it: `[Camera] Enable=1 Log=1 LogHz=20 Blend=0 Unstick=0 Recover=0 ShoulderCover=1 CineAim=0 Cine=0`
(Unstick=0 keeps the detector and writes nothing: 'Off-mode' in 3/F1b. ShoulderCover=1 because the stock key is refused in cover, nothing to compare otherwise.)
Second session, if wanted: defaults (all features on), same checklist; the script compares the two.
The live hook (8d3ccf81) has no [Camera] section and no klcam; the test dll is built from klcam.c plus the klhook.c wiring and installed by the owner only (do not reinstall v82e-h).

### R2.5 Owner test checklist (about 12 minutes; keyboard and mouse defaults)
Before: close the game, rename KLHook.log to KLHook.log.old, install the test dinput8.dll and the KLHook.ini lines from R2.4 (a ready script comes with the build).
1. Start an Arcade Fragile Alliance round on a map with low walls (Subway is fine). Stand still 5 seconds, walk 5 seconds, then sprint (Left Shift) 10 seconds around a corner.
2. While sprinting, spin the mouse half a turn quickly, 3 times, and run one full circle. Whenever the camera lags or sticks, press F9 at once and stay put for 3 seconds.
3. At a low wall press C to take cover. Wait 2 seconds. Hold X for half a second (the shoulder swap). Wait 2 seconds. Do the swap 3 times.
4. In cover hold the right mouse button to aim for 2 seconds, let go, wait 2 seconds. Do it 3 times. Then once: aim (hold right mouse), and while aiming hold X half a second, then let go of both.
5. In cover swap the shoulder with X once, then leave cover (C again or walk away) and run 3 seconds. Do this 3 times. If you lean out one side while the camera is on the other, press F9.
6. Out of cover hold X half a second to swap shoulders 3 times, 2 seconds apart, sprinting 3 seconds after each. Aim with the right mouse in the open 3 times, 2 seconds each.
7. Play normally 3 more minutes (shoot, change covers, get shot). Press F9 every time the camera is wrong (stuck, late, jumps, wrong side) and jot one word on what you were doing ('after reload', 'leaving cover').
8. Quit through the menu (not Alt+F4). Send KLHook.log (and any new KLHook_*.dmp or kl2_490_crash file if it closed by itself). If you changed the keys from X (hold) shoulder, C cover, right mouse aim, say so.

### R2.6 tools/kl_camlog.py (spec; written once klcam.c has R2.3)
Usage `python tools/kl_camlog.py KLHook.log [--from HH:MM:SS] [--to HH:MM:SS] [--csv out.csv] [--selftest]`. Reads the log as text (cp1252, errors=replace), keeps lines whose text after the
`hh:mm:ss.mmm ` stamp starts with `cam:`, `camev:` or `camdump:` (the first `cam: on:` line gives the ini). Parses `key value` pairs by regex (`(\w+) (-?[\d.]+)`, triple fields `t a/b/c`, `eye x y z`),
tolerant of a missing token (old logs: prints n/a). Time = T when present, else the clock (midnight wrap aware). Prints plain text:
 1. Run: first/last stamp, cam: lines, fps estimate (f/T), HITCH events with the 10 worst rdt, GAP events, SKIP reasons with total seconds.
 2. Stuck: each STUCK2 / LAG2 (and old `STUCK`) episode: start, duration, frozen fields, what changed at the end, mv/cs/profile/blk/blend/tick/flag4cd8; counts per frozen-field set (the cause table);
    whether a hitch (rdt > 0.1) lay within 1 s before (hitch versus camera); each F9 MARK with the nearest episode.
 3. Chase: per profile, median/max tau = |eye - pivot| / vE during moves, k590/k594/slow values, BLEND durations achieved against the profile times.
 4. Shoulder: every X edge and SWAP: stamp, in cover, coveraim, would_toggle verdict, module fired, side bit before -> after, want, st104, camside, SIDEBLEND time, b84; per COVER leave the side/b84 at +0, +1.0, +3.0 s
    ('snapped back' = side after != side before the leave with no key). Flags: key down but no side change (with the gate reason), side change with no key, camera/body disagreement (st104 side != side bit for > 1 s).
 5. Aim: each RMB edge: in cover or open, delay to PROFILE change, BLEND, FOV from -> to and settle time, EYE settle; medians for cover versus open.
 6. Verdict sentences ('4 stuck episodes, 3 are frozen=EYE with the pivot moving -> check tick/latch'; 'hitches explain 2 of 7 F9 marks') and a CSV of the cam: samples (one column per token).
Exit code 0 always; `--selftest` runs on an embedded 60-line synthetic log and asserts the section counts.

## Round 2 (2026-10-17): implementation in klhook/klcam.c (built, NOT run; no install, no commit)
Test dll built from klcam.c into the scratch folder (see the work note for the md5). Read-only analysis script: `python tools/kl_camlog.py KLHook.log [--csv out.csv] [--selftest]`.
CORRECTIONS to the round-1 notes: (1) 0xceb5e0 / e4 / e8 (the shoulder flip times 0.2 / 0.1 / 0.8) are in .data, not .rdata (READ the section table), so FlipTime IS
writable from SHIP. (2) The FOV channel step is per camera at cam+0x7a4 (stock 1/30, alpha at +0x7a8), a heap field, so FovStep is writable too. (3) LeanFollow has a route, below.

### New ini keys (all read once; restart to change)
LeanFollow=1 (offline only), LeanGate=1, UnstickFilter=1, UnstickGate=0, UnstickTarget=0, LogKeys=1, ShakeKeep=list, FlipTime=0.35, ShakeScale=0.8,
FovStep=1.8 (CHANGED MEANING: a factor on the stock step interval, range 0.5..6; it was an absolute 0.20 that had no effect).

### Writes (all through klh_data, heap / .data only; each checks the stock value first and refuses otherwise)
- [P+0xb90] bit 0x20: LeanFollow. Set = lean left. 0x544780 copies it each frame into [P+0x438] bit 10; the decider 0x89fd90 re-seats the cover state. Re-asserted for 0.6 s while SC+0x105 differs, then the original bit is put back; two failures switch it off for the run. Replicated state, so offline and local player only. Validated: [SC]==0xbb5b6c, [SC+0x44]==8, [SC+0x100]==P, [P+0x6b4]==SC, [P+0xb64]==0. LeanGate: [P+0x2d6c] bit 4 = left, bit 8 = right (ASSUMPTION).
- cam+0x658 / 0x68c / 0x6c0 / 0x6f4 / 0x728 / 0x75c, +0x30 (substep h of the six chasers, stock 0.005): raised to dtavg/8 (0.0075..0.02) while the smoothed frame time is above 0.05 s, put back below 0.04 s. Substeps = trunc(dt/h) clamped 1..10 (0x5a3150), so below 20 fps the camera crawled. GUESS: the coefficients are not cached from h.
- BYTE [cam+0x30] = 1 and, if [cam+0xc54] <= 0, [cam+0xc54] = 4 (UnstickGate=1 only, off by default; CORRECTED, was dword 1 / 0: READ 0x65016e `cmp byte [esi+0x30],0 / je`, 0x650178 `cmp dword [esi+0xc54],0 / jle`, both to 0x650389 = tick skipped, so 0 would freeze it): only after 1 s of frozen camera with byte 0 or counter <= 0.
- [cam+0x540] = P (UnstickTarget=1 only, off by default): when the owner pointer is not the local player for 0.5 s.
- .data 0xceb5e0 (FlipTime) and 0xceb5e4 (0.5 x FlipTime, at most the stock 0.1); 0xceb5e8 left unless FlipTimeSpecial>0 (new key, default 0). CORRECTION: 0xceb5e8 (0.8) REPLACES the time at 0x908926 when owner movement id == 8 (cover) and 0x88c5e0 true and 0x492ff0 false = SC+0xf8 substates 14/15/30/31 (jump tables READ 0x88c604/0x88c60c, 0x493014/0x49301c); those flips take 0.8 s whatever FlipTime says. What the substates are: UNKNOWN. Only when all three read 0.2 / 0.1 / 0.8.
- cam+0x7a4 (FovStep x 1/30), only when it reads 1/30.
- S+0x34 .. S+0x34+160 (41 floats of the shaker S = [P+0x2c8c]), scaled by ShakeScale except the ShakeKeep indices, only when two reads 0.5 s apart agree.
- The round-1 profile floats (Blend, CineAim) are unchanged.
Not written (no verified route, so no effect): look smoothing, pitch limits, the 0xceb590.. base-offset constants, the +0x124 rest value and the chaser taus.

### Log additions (Log=1)
`T` and `rdt` (raw frame time before the 0.1 s clamp) in cam: lines; camev: HITCH / GAP / SKIP <reason> begins|ends; STUCK2 and LAG2 episodes with the frozen field set and ONE camdump block (3 a minute);
KEY edges (X, RMB, LMB, C, Shift) and F9 = MARK n; the stock X gate decision; COVER enter / leave with the +0.5 s, +1 s, +3 s snapshots; BLEND start / end; FOV settle; SIDEBLEND; EYE settled; LEAN lines;
GATE / TARGET / FILTER lines; the cam: line gains bit818, camside, keys, t560 t564 f568 k590 k594 slow, st104 st105 st10c c2d6c b90, a `coveraim` token and signed `cs`; it prints at 2 Hz when idle.
The 10 s summary adds STUCK2 / LAG2 counts, frames with rdt > 0.1 s, swaps ok / no change, and the max BLEND / FOV / SIDEBLEND times.

### Owner test (R2.4 ini, R2.5 checklist above; F9 is wired)
`[Camera] Enable=1 Log=1 Blend=0 Unstick=0 Recover=0 CineAim=0 Cine=0 UnstickFilter=0 ShoulderCover=1 LeanFollow=0` measures stock behaviour; a second session with the defaults compares.

### Review corrections, round 2 (2026-10-17, applied to klhook/klcam.c)
- Gate remedy fixed (byte 1 / counter 4, see Writes). LeanFollow: offline only (kl_online() in start and tick), polarity check before the write (b90 bit 0x20 and SC+0x105 must both equal the OLD side, else "LEAN skipped"), put-back of b90 bit 0x20 on every failure path (cover state gone, player/camera change, camera lost, online); NOT after a successful LEAN (that would re-seat the state to the old side). [P+0xccc] and [P+0x29a4] are only logged in the LEAN start line (whether they mirror the lean is UNKNOWN; 0x29a4 is a byte written at 0x44f8a9 / 0x44fa51 / 0x808aa5).
- UnstickFilter: a refusal is per camera and retried every 3 s (5 times); h is put back when the player is down; h never exceeds the real frame time; klcam_lost clears h/fv/fl/sh state. `kc.x.low_s = mv` removed (it broke the EYE-settled log line).
- GUESS / ASSUMPTION labels: that the cam+0x790 channel (FovStep) is the FOV one; that ShakeScale (table read by 0x510500) also scales the explosion states; the [P+0x2d6c] clearance bits (4 left / 8 right); polarity of b90 bit 0x20.
- Rejected: guarding the Cine knobs with kl_online() (client-side visual data only, deliberately not gated; the private-match requirement says features must work online too).


## The non-finite eye (2026-10-18; static, wf_e3b19273 trace + refute; nothing run)
Vault DM03A slow runs L12 / L17: [cam+0x508] non-finite from the first camera tick, all round (3f, by the hook's READFAIL bit 1).
- Per-frame route (READ): 0x87ae38 -> 0x48ec00, 0x87ae44 -> 0x446c40 (the rig): E = (O + [cam+0x5d0]) * M[cam+0x468] + [cam+0x48c],
  O = the chasers' output at cam+0x524..0x52c; 0x44739c calls 0x4b3160, which stores E into cam+0x508 unchecked (other callers of
  0x4b3160: 0x55cece 0x5de593 0x5ffc48 0x7076f3). 0x7c9030 (eye setter) is called by the pull-in 0x56e4c0 and the tick 0x650070.
- M / position: 0x892180 via ZFFPlayer vt[0x278] = 0x688660 -> 0x8dc650 reads [P+0xbd4] +0x1d4 (position: |p| >= 1e6 or NaN -> origin)
  and +0x1e0 (3x3, copied with NO check).
- Chasers (6 x 0x34 at cam+0x658..0x790, h at +0x30, velocity +0x0c, dirty byte +0x10): 0x51b430 a = 8d/T^2 (T = 0 -> Inf / NaN,
  the 'tiny' fix-up only for |a| < 1/8192); 0x5a3150 reloads its state from *out every step, so a NaN state LATCHES for good
  (x87 'test ah,5 / jp' treats NaN as 'far'; 0x65c160 stores it back). Profile times at cam+0x590 / 0x594 (constructor 0.25 / 1.0).
- Cinematic branch 0x446eb6 (byte cam+0xc28): O = lerp(cam+0xc2c.., target, t = cam+0xc3c) + cam+0xc40 into *out unchecked;
  the sanitiser at 0x4470d6 (test 0x41) lets NaN through. When the flag drops the chasers keep the NaN. Fits 'first tick, pre-round'.
- Low: pull-in ratio 0x56e5b1 (transient only, gated by cam+0x394); dt (ftol clamps 1..10, h constant); normalise 0x72a000 (guarded).
- Rewriting cam+0x508 alone is cosmetic: 0x4b3160 recomputes it next tick. NanRepair (klcam.c, b640f178) covers the latch
  (*out and the six chasers in +0x500..0x790) but NOT: dirty bytes / velocities, T = 0 (finite), cam+0x468 / 0x48c, cam+0xc10..0xc4c.
- The next failing run's NanDump decides: 0x590 <= 0 -> T = 0; *out NaN, 0x468 finite, 0xc2c.. NaN -> the cinematic branch;
  0x468 NaN -> the pawn matrix (then guard [P+0xbd4]+0x1d4..0x200 or substitute E at the 0x44739c call).
