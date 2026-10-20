# Rigid feel: heavier turning for Kane & Lynch 2, mapped onto kl2.exe (2026-10-19)

Owner question: "is it possible to slow players' rotations and stuff down, to make it feel more rigid? Look at Payday 2 or any
other game on the PC as a reference, get a foundation down."
Answer: YES for the local player (mouse input side, built: `klhook/klrigid.c`, off by default). For remote players the shaping
functions are built but are only used if `klnetsmooth.c` calls them (2 lines, section 4). For AI actors and for the body-facing
of any character there is no usable lever yet (no turn-speed field, no facing setter found).
Tags: CERTAIN = read in a file / the exe on this PC. RECALL = general knowledge, not checked here. GUESS = my inference.
Nothing here ran in the game. The maths of klrigid.c ran in an off-game harness (section 6). Nothing was written to a game folder.
Sources read: `re/pd2_netfeel.md`, `re/kl2_rotation.md`, `re/netfeel_references.md`, `klhook/klnetsmooth.c`, `klnetfix.c`, `klauto.c`, `klcam.c`.

## 1. What "rigid" means, from the references

PD2 (CERTAIN numbers, from its Lua bytecode via tools/pd2_lua.py; their combination is my reading):
- Weight is made of THREE things, not one: (1) an angular speed cap for the look that depends on the error, `lerp(40, 360, sqrt(min(err/90,1)))`
  deg/s (1 deg -> 74, 10 -> 147, 45 -> 266, 90+ -> 360; harness reproduced those), (2) legs that trail the look at 120 deg/s with the
  twist limited to 70 deg, (3) turn-in-place only past 65 deg, played as an authored animation (angle45/90/135 blends).
- Sender: look quantised to 1.41 deg and sent at most 20 Hz; position at most 20 Hz. The receiver follows a queued path at constant speed.
- AI turns: slerp at `dt*5*mul`, mul 0.75 cops / 0.5 shield cops (heavy things turn slower).
Other games on this PC expose no readable numbers (re/netfeel_references.md). Their values below are RECALL:
- Unreal CharacterMovement: RotationRate 360 deg/s (500 in the third-person template); simulated-proxy smoothing ~0.1 s location,
  ~0.05 s rotation; smooth distance 256 cm, snap 384 cm.
- Source: cl_interp ~16-31 ms, extrapolation cap ~0.25 s, smoothing ~0.1 s.
Rigid = a speed ceiling that bites on BIG turns (flicks), a tail that does not oscillate, and a body that does not follow every wobble of the
aim. It is not just "lower sensitivity": lowering sensitivity makes small aim corrections sluggish too.

## 2. Where rotation lives in kl2.exe (summary of re/kl2_rotation.md, CERTAIN unless marked)

| Part | Site | Writable by us? |
|---|---|---|
| Local mouse counts | ZMouseWintel update 0x650840 -> `IDirectInputDevice8::GetDeviceState`, 0x14 bytes, lX +0 / lY +4 | YES: wrap the call (heap vtable pointer of dinput8 objects) |
| Binding text TurnCamera=rel(ms,x) | .rdata 0xb87f68 | NO (hashed) |
| Local camera yaw/pitch | camera rig `[player+0xbd4]` +0x14/+0x1c (re/camera.md) | not needed |
| Local body turn | animation-driven: Stand/Crouch Turn_Left/Right_45/90, Walk/Run Turn_180 clips (table built at 0x78de09) | clip lengths only, via .ANM (untried, high effort) |
| Replicated heading | int16, 1024 per turn (double 0xb78bc8), sender 0x6300f0, tolerance 900, 100 ms min, 2000 ms refresh | tolerances are .bss (klnet.c) but they make it DENSER, not slower |
| Remote body facing | receiver 0x600eb0 only rotates the position error into the body frame; the facing setter was NOT found. klnetsmooth.c GUESSES it is the body matrix placed by `B->vtbl[0x8c]` | via klnetsmooth (heap vtable swap) |
| AI actors (ZFFActor, soldiers, civilians) | no turn-speed field with a known name; the AI turn path not found | NO |
| Teleport | 0x5f21c0, threshold 1,000,000 (double 0xb49b40) | no |

## 3. The model, mapped onto those sites

### 3a. Remote players and AI on a client (display only)
What `klnetsmooth.c` (other workflow; read, not edited) already covers:
- A flat turn-rate cap (`MaxTurnDegPerSec`, default 540) and a critically damped spring (`SmoothMs`, default 90), applied to the REMOTE body's yaw
  after the stock update, through a private ZFFPlayer vtable (slot 393 = 0x506350) and the body call vtbl[0x8c]. A position jump over
  `SnapUnits` resets it. That is the "yaw rate limit" and the "exponential smoothing" of the model.
What it lacks (and what klrigid.c now provides as pure functions):
1. An ERROR-DEPENDENT cap (PD2's sqrt curve). Flat 540 deg/s lets a 2 deg quantisation step move at 540 deg/s and then stop: jerky. The curve
   makes small corrections slow and only a big error reach the top. `klrigid_remote_cap(err_rad, fallback_rad_s)`.
2. A body-follows-look DEADBAND (turn-in-place threshold, PD2's legs): hold the body while the look is within 65 deg, then turn it at 120 deg/s
   until within 6 deg, never more than 70 deg apart. `klrigid_follow(body, &turning, look, dt)`. This is the "upper-body aim vs lower-body turn"
   part. WARNING (GUESS): klnetsmooth smooths the ONE body matrix. If the weapon/upper body is drawn from that same matrix, a deadband makes the
   gun point up to 70 deg away from where the owner aims, on screen. It is correct only if the aim visual comes from a separate channel
   (the camera angle / aim point models that klnetfix lists). That is not verified, so RemoteTurnInPlace stays 0 until someone looks at a
   remote player with it on. Hit tests are not affected either way (the server uses the shooter's own replicated aim: re/kl2_rotation.md 5A).
3. Position: PD2 follows a queued path at constant speed (350 walk / 575 run cm/s, +5 % per queued node above 2, snap at 30 nodes). The K&L receiver
   is a different machine: 0x600eb0 turns the position ERROR into stick input, so the remote body is steered toward the target (a proportional
   controller, CERTAIN from re/kl2_rotation.md section 3). There is no queue to tune, and nothing to replace without a code patch. What can
   be changed without one is the dead-reckoning end time (klnetfix.c HoldPosMs etc., 500..3500 ms, client only) and klnetsmooth's snap distance.
   UE numbers (RECALL): smooth up to 256 cm, snap past 384 cm; klnetsmooth's SnapUnits default 300 is in that range (units of the game are
   not verified to be cm: GUESS).
4. AI actors on a client: same idea, but the receiver path is 0x569eb0 and its vtable owner is unidentified (klnetsmooth.c header). Not
   covered. PD2's AI turn is `slerp(dt*5*0.75)`; the K&L equivalent cannot be put anywhere yet.

### 3b. Heavier turning for ALL characters, including the local player
Two levers exist, only one is usable.
- INPUT SIDE (usable, built): section 5. Affects the local human only (mouse). It is also the thing every other player sees, because the
  sender replicates the heading the camera actually has: a player who turns slower is shown turning slower. That is honest data and needs no
  agreement between machines.
- LEVEL-TEMPLATE side: `re/kl2_rotation.md` section 4 and D read ZFFPlayer, ZFFActor, ZSoldier, ZCivilian in stock F01 (49 actors, 16 players,
  36 soldiers, 13 civilians). There is NO turn-speed field with a known role. Candidates are float values whose purpose is unknown
  (ZFFActor fields 29 = 10.0, 32 = 1.0, 34 = 50.0 on all 49; ZSoldier field 7 = 175 / 280 / 100 / 65 by type). The exe holds no property names, so
  changing one blind would be guessing with a map-wide effect and no way to see it. Therefore NO `tools/kl_rigid.py` was written. Condition
  for writing it: a live differential (change one candidate on an owner map, watch an actor turn) or finding the property in the
  turn-in-place code at 0x7a43e0 / the callers of 0x429ff0 (the 27 references to 0xb78bc8 in re/kl2_rotation.md section 6 are the next list).
  Heavier AI and heavier body turns are therefore OPEN.
- ANIMATION side (untried): lengthening the turn-in-place clips in a map's .ANM would slow turn-in-place. The per-clip header is 0x68 bytes in
  Dog Days (CLAUDE.md); root motion and foot sync are baked (GUESS). High effort; not started.

## 4. Wiring klnetsmooth.c to the shaping functions (NOT done: that file belongs to the other workflow)
Both functions return their input unchanged when `[Rigid]` is off, so wiring them costs nothing when unused.
1. Include order: `#include "klrigid.c"` ABOVE `#include "klnetsmooth.c"` in klhook.c (klrigid.c only needs klhook.c's helpers).
2. In `kns_smooth()` replace the speed clamp line
   `{ float mx = kns.maxdps * 0.0174532925f; if (kns_st[i].vel > mx) ...` by
   `{ float mx = klrigid_remote_cap(fabsf(d), kns.maxdps * 0.0174532925f); if (kns_st[i].vel > mx) ...` (same clamp lines after it).
   With `Remote=1` the cap is PD2's curve between RemoteMinDps and RemoteMaxDps instead of the flat MaxTurnDegPerSec.
3. Optional (experiment, see warning 3a.2): feed the received yaw through `klrigid_follow` BEFORE the spring:
   `yaw = klrigid_follow(kns_st[i].body, &kns_st[i].turning, yaw, dt);` with `float body; int turning;` added to the per-player state.
Suggested klnetsmooth settings with this: `MaxTurnDegPerSec=360 SmoothMs=70` (its defaults 540 / 90 are looser than every reference above).
The spring's own velocity limit still applies after the curve (min of the two).

## 5. What klrigid.c does for the local player (built)
Hook: vtable-POINTER swap of two dinput8 HEAP objects (the IDirectInput8 object, then the mouse device from `CreateDevice(GUID_SysMouse)`),
each onto a private copy of its vtable; nothing in kl2.exe or .rdata is written, so the integrity checks (re/antitamper.md, klranges.h) are
not involved. The same recipe as klnetsmooth / klfreeclimb. Works on top of klauto.c's proxy objects (TEST build) because it only swaps
pointers and calls the previous function. `klrigid_di8(o)` is called from DirectInput8Create. Put back: when the filter faults it switches
itself off and `klrigid_tick` restores the stock pointers (a dinput8 object dies with the process; level end needs no action because the
device outlives levels).

Per frame, per axis (yaw = lX, pitch = lY):
```
pending += counts * Mul
out      = pending * (1 - exp(-dt / tau))                      # low pass (YawSmoothMs), optional
cap      = rate(pending) * dt ;  rate(e) = Min + (Max-Min) * sqrt(min(e/CurveFullDeg, 1))   # e in degrees = pending * DegPerCount
out      = clamp(out, +-cap) ;  pending -= out ;  pending clamped to Max/DegPerCount * BacklogSec
```
Counts are conserved except what overflows the backlog (BacklogSec, default 0.3 s), so slow, precise aim moves are 1:1, and only a flick is
stretched out. The remainder of the rounding is carried, not dropped.

What it does to AIMING (honest list):
- The camera is the aim ray, so a heavier turn is a heavier aim: a 100 degree flick that takes 0.1 s now takes ~0.4 s at 300 deg/s
  (harness: 600 counts = 102 deg in 3 frames came out over ~35 frames, 599 of 600 counts delivered). Quick turn-around shots get harder; tracking a
  target at normal speed (3 counts/frame = 31 deg/s at 0.17) is delayed by ~1 deg and 1:1 in amount.
- Pitch is NOT capped by default (PitchMaxDps=0): head-height aim stays direct. Yaw only is the "rigid" part, like PD2.
- While the camera's aim byte is set the filter is bypassed and the backlog is paid out at once (`AimExempt=1`). The byte [cam+0x640] is klcam.c's
  ASSUMPTION for "aiming"; `Log=1` prints every change, so the owner can see whether it follows right-mouse. If it does not, set `AimExempt=0`
  to filter all the time or give `AimByte=` another offset. A wrong byte cannot break input, it only moves the exemption.
- Menus: filter is bypassed when there is no local player or the pause / cut flag [gd+0x4cd8] is set (klcam.c ASSUMPTION). If a menu still
  inherits the filter, the cursor would feel heavy; Log=1 shows the bypass counts ("menu/none-bypass").
- Gamepad (gc0 binding) is not touched. A controller player gets nothing from this module (GUESS that a second hook on the gamepad device is
  needed; not examined).
- Online: it changes only this machine's own mouse counts, so it is safe for peers (they see slower turning, which is true). It is a
  self-handicap, not an advantage; it is NOT gated by ranked/unranked. (Flag if you want it gated: `kns_gate` of klnetsmooth.c is the model.)

## 6. Numbers to start with (all GUESS to be tuned live; sources in brackets)
| Key | Start | Rigid/heavy | Source |
|---|---|---|---|
| YawMaxDps | 300 | 180-240 | PD2 top 360 (non-combat); UE 360-500 (RECALL); rig 306 deg/s clamp (klauto.c) |
| YawMinDps | 60 | 40 | PD2 40 |
| CurveFullDeg | 90 | 90 | PD2 90 |
| YawSmoothMs | 40 | 60-100 | UE ~50 ms rotation, Source ~100 ms (RECALL) |
| PitchMaxDps / PitchSmoothMs | 0 / 0 | 0 / 0 | keep head-height aim direct |
| BacklogSec | 0.30 | 0.4 | design choice |
| DegPerCount | 0.17 | measure | klauto.c TurnDeg; depends on the owner's sensitivity setting |
| RemoteMaxDps / Min / FullDeg | 300 / 40 / 90 | 270 / 40 / 90 | PD2 |
| TurnStartDeg / TurnStopDeg / TwistMaxDeg / LegDps | 65 / 6 / 70 / 120 | same | PD2 (CERTAIN numbers) |
| klnetsmooth MaxTurnDegPerSec / SmoothMs | 360 / 70 | 270 / 90 | PD2 / UE |
Harness results (klrigid.c compiled off-game, 60 fps): curve 1/10/45/90 deg -> 74/147/266/360 deg/s (PD2: 74/147/267/360);
a 600-count flick delivers 599 counts, peak ~296 deg/s; 3 counts/frame for 300 frames delivers 894 of 900 (the rest is the 6-count tail);
`klrigid_follow` holds the body at 0 while the look is 29 deg away, then turns it and keeps the gap at most 70 deg, stopping 6 deg short of the look.

## 7. KLHook.ini block (not added to KLHook.ini: that file belongs to the shipped sample)
```
[Rigid]
Enable=0
;YawMaxDps=300  YawMinDps=60  CurveFullDeg=90  YawSmoothMs=40  YawMul=1.0
;PitchMaxDps=0  PitchSmoothMs=0  PitchMul=1.0
;BacklogSec=0.30  DegPerCount=0.17  AimExempt=1  AimByte=0x640  Log=0
;Remote=0  RemoteMaxDps=300  RemoteMinDps=40  RemoteFullDeg=90
;RemoteTurnInPlace=0  TurnStartDeg=65  TurnStopDeg=6  TwistMaxDeg=70  LegDps=120
```
Wiring for klhook.c (4 lines; compile-checked in a scratch copy, SHIP and TEST builds, 0 errors, no warnings at /W3):
`#include "klrigid.c"` above `#include "klnetsmooth.c"`; `klrigid_init();` after `klnetsmooth_init();`; `klrigid_tick(game_thread);` after
`klnetsmooth_tick(game_thread);`; in DirectInput8Create after the real call (and after kla_di8): `if (SUCCEEDED(hr)) klrigid_di8((void **)o);`.
DirectInput8Create runs once, after DllMain, so the ini is already read.

## 8. Live test plan (needs the owner at the PC; a scripted run cannot judge feel)
1. `Enable=1 Log=1`, Arcade solo. Check the log for the two "wrapped" lines (IDirectInput8, mouse device), then the "aim byte" lines when
   holding right mouse. If no "wrapped" line appears the game made its device another way (a second DirectInput8Create path): report.
2. Flick 180 deg, then track a walking target, then aim down sights. Tune YawMaxDps (240/300/360), YawSmoothMs. Report whether menus and the pause
   screen cursor feel normal.
3. `Remote=1` + the klnetsmooth edit of section 4.2 on two PCs (online FA, unranked), watch a remote player spin/flick. Only then try
   RemoteTurnInPlace=1 and look at where the remote gun points.
4. Open questions that would unlock the rest: the remote body-facing setter; the animation threshold that picks Turn_*_45/90; any AI turn rate.

## Review notes (2026-10-20)
- Fixed in klrigid.c: a stale heap address (device recreated) no longer blocks wrapping or fills the 4-slot tables; registry entry set before the vtable-pointer swap (no E_FAIL race); restore keeps the entry unless the stock pointer went back, so GetDeviceState never fails after a restore.
- Checked: no hashed byte written (heap objects only, klh_data/klh_may_write), klnetsmooth.c has no dinput code (no clash), SHIP + TEST builds compile with the 4 wiring lines.
- Still unproven live: that the game creates its mouse via IDirectInput8::CreateDevice with GUID_SysMouse on the object DirectInput8Create returned.

## SHIP crash and the proxy fix (2026-10-20 03:10-03:27)
- The SHIP build 1020e with [Rigid] Enable=1 crashed at load, kl2.exe+0xfbb90 (read of 0), every time (Z1, Z2, Z4, Z6). The
  bisect: switches off = OK, NetSmooth only = OK, Rigid only = crash. There was never a "mouse device wrapped" line.
- Cause: the vtable-pointer swap ran on dinput8's OWN objects in SHIP. dinput8 checks the interface pointer's vtable on
  each call, so CreateDevice through our copy failed and the game had no mouse. The TEST runs R1/R2 never saw this: there
  the swapped object was klauto.c's proxy.
- Fix (1020f SHIP / 1020k TEST): klrigid.c now hands out its own heap proxies ({vtable, real}; every method forwards; only
  mouse GetDeviceState filters). Z7 (SHIP, Rigid only) and Z8 (SHIP, Z1 = Shop + Rigid + NetSmooth + Probe): no crash, both
  objects wrapped. R3 (TEST 1020k, R2 script): PASS, 0 faults, the filter active in the round, 754 aim-bypass frames.

## Live results (2026-10-20, scripted, owner asleep; KLHook TEST 1020d, DM01 in the F01 slot, Arcade)
Runs R1 (Log=1) and R1b (Log=2), [Rigid] Enable=1 with the defaults above: both PASS, 0 asserts, 0 faults.
- The wrap works live: `IDirectInput8 ... CreateDevice wrapped`, `mouse device ... GetDeviceState wrapped`, the filter is
  bypassed in menus ("menu/none-bypass") and active in the round.
- Aim exemption PROVEN (R2): right mouse down -> `aim byte [cam+0x640] = 1 (filter bypassed)` 4 ms later, release -> 0; a
  510 deg flick while aiming went through unfiltered (747 aim-bypass frames). R2 repeated T0-T2 with the 0.1 s window peak:
  284 / 104 / 300 deg/s (cap 300). PASS, 0 faults.
- klauto's scripted mouse sits UNDER the filter (its proxy object gets the same vtable swap), so scripted turns measure it.
  The script's own steering still reached the shop and the round with the filter on.
- New `Log=2`: one line per yaw burst (counts in / out, dropped, peak rate over 0.1 s windows). Scripted probes in R1b:
  | probe | in | out | dropped | burst | prediction |
  |---|---|---|---|---|---|
  | T0 3000 c/s x 0.3 s | 159 deg | 159 deg | 0 | 1.0 s | 153 deg, nothing dropped, ~0.7 s |
  | T1 600 c/s x 1.0 s (102 deg/s) | 102 deg | 102 deg | 0 | 1.3 s | passes, ~3 deg behind |
  | T2 6000 c/s x 0.5 s (1020 deg/s) | 510 deg | 230 deg | 280 deg | 1.2 s | ~240 out, ~270 dropped |
  So a flick is slowed to the 300 deg/s cap and paid out over ~0.3 s more; a turn faster than cap x backlog loses the rest.
  (R1b's per-frame peak figure read 338-365 deg/s from whole-count rounding at ~500 fps; the 0.1 s window replaces it.)
- `pos` heading in klauto reads a wrong player for "me" in these runs (#8 / #10 at y = 0, fixed while the shots show the
  player moving): not usable for turn measurements.
- Still for the owner: the FEEL (a script cannot judge it) and DegPerCount at their sensitivity.
