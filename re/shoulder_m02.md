# Late Night Opening: the SWITCH CAMERA SHOULDER key does nothing (2026-10-10, offline; nothing here ran in the game)

Owner: *'wont switch keybind'* - on Late Night Opening (Dead Men M02_FA_A; on the tab as `KLExpansion\Maps\DM02`,
slot F02; build `<work>\build\z_final\M02`, before that `y_loot2\M02`) the key that swaps the camera's shoulder does
nothing; on the bank (M03) it works. Continues `re\lean_m02.md` (the mechanism's first reading, the no-cover boxes).

**Verdict: static reading does not name the cause, and it rules the level out as far as files can.** Everything in
kl2.exe that can refuse the key or hold the side is listed below with what sets it. None of it is something either
build contains, and every camera / input / hero object of the M02 build equals the M03 build's. The body is the
SAME on both maps. So no fixed map was built (`z_lean\M02b` does not exist). A log-only hook part,
`klhook\klshoulder.c`, is written and compiled: one round with the key held a few times names the holder.

## 1. Established (read in kl2.exe build 0490, capstone; addresses are the code places)

### 1.1 The key

- `ZGameplayInput` (vtable 0xbb7c74; PC: `ZGameplayInputWintel` 0xbb7d0c), update 0x846430, runs the handler
  0x640080 over three 16-byte records at +0x10 / +0x20 / +0x30: `{action*, type, timer, fired, once, ?}`.
  Type 2 at **+0x30 is `SwitchCameraSide`** (default binding in the exe: hold X / pad right stick click; X is also
  Tap / HoldPulseCheck). The timer starts at 0.08 s (`[0xbb7c6c]`), runs down while the key is held, the record acts
  once when it reaches 0 (`fired` = 1 until release). `[H+8]` = the player.
- Nothing runs while `[H+0x330] > 0` (an input lock, seconds; set by the input's own 'reset', slot 4, 0x8180cc) or
  while the action is not pressed (0x5f4310: the action map, nothing of the level).
- The handler then returns WITHOUT toggling when any of these holds (0x6400aa .. 0x640131):

| gate | what it is | who sets it | can a level hold it? |
|---|---|---|---|
| `[P+0xed0]` bit 7 | the player's input mask | ONLY `LevelSetup::ZPlayerInputManipulator` (controller `PlayerInputManipulator`, 0x84af60: six tri-state fields at +0x34..+0x48 -> mask bits 2, 4, 0x20, 0x40, **0x80**, 0x100; 1 = block, 2 = free; applied on its message or its first frame, 0x901360) | **yes - and neither build has one** (no stock FA level either; Dead Men has no such class) |
| byte `[[0x168d7c0]+0x209]` == 0 | a bool of the tuning object | its constructor only (default 1, 0x5267a9); the other writers of a +0x209 are other classes (ZSquadScript, the session manager) | no |
| `[P+0x2720]` bit 1 clear | the player's control kind | given when the player is attached to a screen (0x60a7fa), zeroed on detach (0x7b6a77); 2 = the local human | no (the mode) |
| byte `[P+0x2954]` | named 'aiming' in re\firstperson_camera.md; the cover code clears it on entering a cover (0x44f9a2) | player code | no |
| `[P+0xd50]` | the helicopter seat | ONLY the message `HeliSeatAttach` (id `[0x1548de8]`, 0x5c7e5b in ZFFPlayer slot 89), cleared by the reset 0x80448a. NOT a camera bone (lean_m02.md guessed that) | by a level's helicopter - the string is in no build |

- When no gate holds: `[P+0x29a0]` (the WANTED side, 0 right / 1 left) is first set to the side in use if they
  differ, then toggled; then 0x74a120(P, left, 0.0) and the RMC `SetLeftShoulder`. **`[P+0x29a0]` has no other
  writer** (constructor 0x6ef2de = 0). No bone, no model, no weapon and no level object is read on this path.

### 1.2 The setter 0x74a120 and its 26 call sites

`0x74a120(P, left, seconds)`: with seconds > 0 it only stores the request (`[P+0xb88]` time, `[P+0xb8c]` -1 left /
+1 right; applied by the player's frame 0x580512). Otherwise `[P+0x818]` bit 10 and byte `[P+0x280c]` = the side.
Before that the wish is OVERRIDDEN:

- **LEFT** while the object `D = [P+0x2948]` has byte `[D+8]` bit 0 and `[D+4] != 3`. D is the **down-not-dead state**
  (constructor 0x57cf90; start 0x658700 -> 0x76a450 writes the kill-feed line, sets the flag, state 2, keeps the
  old side in `[D+0x30]`, forces left; end 0x88a990 clears flag and state and puts the kept side back).
- **RIGHT** while word `[P+0xa54]` has bit 1: the player lies down (set at 0x6fb885 / 0x8b1322, cleared on getting
  up 0x451269 / 0x4b2ce3 / 0x7cba99). The other bits of that word are health-regeneration states (0x50fb80).

| call site (function) | what | side asked |
|---|---|---|
| 0x64019e (0x640080) | the key | the toggled `[P+0x29a0]` |
| 0x71f3f9 (StandCover slot 14), 0x823a1c (StandCover slot 15) | taking / moving along a cover | the cover's side `[cover+0x104]` |
| 0x5ea984 (0x5ea690, called by ZFFCamera1 slot 26) | after a cover is left: `[P+0xb84]` (-1 / +1), written by 0x44f260 from `[P+0x29a0]` | back to the WANTED side |
| 0x7a5263, 0x7a52ff, 0x7a53b1, 0x7a5429 (BaseMove / CloseCombat slot 17) | walking: by the move direction against the view, only in move states 0x15 / 0x16 and by a latch `[move+0x1f12]`; not while 0x651000 (bit 6 of `[P+0x818]`) | left or right |
| 0x580512 (ZFFPlayer slot 87, the frame) | a delayed request coming due | as stored |
| 0x82f7bf (VaultOver slot 5) | end of a vault | the WANTED side |
| 0x76a889, 0x5a756c, 0x71089a, 0x88aa3a | down-not-dead: start (left), three ends (the kept side) | |
| 0x6fb836, 0x8d65eb | going down / a state that sets flag 0x80 of `[P+0xbbc]`: keep the side in `[P+0xa98]`, force right | right |
| 0x4b2d9c, 0x7167f8, 0x7cba79 | getting up / respawn: the side kept in `[P+0xa98]` | |
| 0x4b63c9 (0x4b6340), 0x803dab (ZFFPlayer slot 18, reset) | reset | right |
| 0x8044e7 (slot 18) | the side read back from a saved state | |
| 0x83ad2a, 0x8c848e (HeliPassenger) | helicopter seat | by seat |
| 0x407a56, 0x62ef55 | a network copy of a player / the RMC `SetLeftShoulder` arriving | the sender's |

(lean_m02.md counted 27; a scan for `call` / `jmp` to 0x74a120 finds these 26.)
None of them reads a level object except through a COVER (the `*coverbox*` entities) - and a cover's side is given
back to the wanted side when the cover is left.

### 1.3 Who uses the side

- 0x9088c0 (the camera object, `[cam+0x540]` = the player): when byte `[P+0x280c]` differs from `[cam+0xb40]` it
  turns the blend around and walks along the spline `[cam+0xb44]` (the level object of the define
  `CameraTransitionSpline`; one in every build, in `AllLevels/camerasetup.zip`, Dog Days' own).
- 0x41ad30 (the base move): the stance animations 0x13 / 0x14.

## 2. Looked for in the builds (`z_final\M02` against `z_final\M03`; also M01, M06 and the stock F01 F02 F03 F07 on disk)

- `PlayerInputManipulator`: **0** controllers in M02 and in M03; the string is in no `.prp` / `.gms` / `.buf` of any
  of the eight levels. `HeliSeatAttach`: in none.
- Every controller / class / name matching camera, cam, shoulder, tight, indoor, input, manip: the SAME census in
  both builds - controllers `CCameraBox` 3, `DocuCamProfile` 21, `PictureInPictureCam` 2, `FFCamera1` 2,
  `ShakeCamera` 2, `OnlineEscCamTrigger` 2; classes `ZCAMERA`, `ZOnlinePIPCameraPoint`, `ZOverlayCameraClass`.
  Nothing is named *Shoulder*, *Tight* (but the squad modifier `..._tight_defense_van`, in both) or *Indoor*.
- The three `CCameraBox`: `EscCameraSetup!EscCameraLAST` (field 13 = 1: a release), the van's `EscCamera01_01`
  (field 12 = 1: by message) and `EscCameraInVan_01` (fields 12 and 13 clear = an area camera, a 20 x 20 x 20 box,
  `eONLY_LYNCH`, in the escape vehicle's group `EscCamera_01`) - identical values in M02 and M03. No box covers the mall.
- All 149 nodes under `AllLevels/camerasetup.zip`, `AllLevels/FA_Cam_Handheld.zip`, `AllLevels/FFOsdMP1.zip`,
  `Heroes!` and `EscCameraSetup!`, compared by path with every value and controller value decoded: equal, except
  the places of the eight `Heroes!Hero_0N` groups (where the map starts).
- Dead Men has no shoulder switch and none of the classes above; what is in the builds is Dog Days' own.

## 3. The character (the question that would have changed everything: it does not)

`<DD>\KLHook.log`, the one process of the evening: Late Night Opening 18:53:33 - 18:57:23 (the FIRST level of the
process), the bank from 18:57:31. Both rounds: `heister table entry 0: model 9235 -> 9011 (Kane)`, `the player
wears model 9011 (slot 0)`, `look: variant 2 -> 1`, 'the player is Kane', the same seven-bot draw kind, `[Balance]`
Risk=2 (health 550 -> 401.5). **The same Dead Men body (Kane, model 9011) where the key fails and where it works.**
(An earlier Late Night round, 17:00 - 17:08, was Hutchison 9128; the complaint came after 18:53.) The key's code
reads no bone and no model. The gun looks: the same module state on both. No log line of that round tells the two
maps apart, and no module of the hook writes any field of section 1.

## 4. Not established / guesses

- What the owner's own binding of the key is (the exe's default is hold X; a changed binding lives in the profile,
  not looked at). If the game never sees the key held, nothing above matters - the log shows that first.
- GUESS: a stuck state rather than data - the down-not-dead flag left set (side forced left for the rest of the
  round), or the input lock. Nothing in the files supports or refutes it. The pictures of the round
  (`<work>\research\watch\20261010_185258`, one per ~10 s) show the player on both halves of the screen on both
  maps; they do not show the fault and do not prove a forced side.
- Byte `[P+0x2954]`: its meaning ('aiming') is taken from re\firstperson_camera.md, not re-read here.
- The call sites 0x4b63c9, 0x8d65eb, 0x407a56 are named by their code only (their callers were not followed).
- Slot F02 against F01 / F03 (lean_m02.md 5.5) was not read: nothing found on the key's path asks for the slot.

## 5. The log part: `klhook\klshoulder.c` (prefix `klo_`; NOT wired into klhook.c, NOT installed, never run in the game)

READS ONLY (klh_rd), no write, no call of a game routine, any thread; off unless `[Shoulder] Log=1`.
Built in a scratch copy of klhook with the three lines below: `build.bat` and `build_auto.bat` succeed without a
warning; an off-game exercise (a made-up player / down object / input object in memory, `klo_test.c` in the
scratch copy) prints the expected lines for every case of the table below, the 30-a-second cap, a vanished player
and a wild pointer.

Wiring (klhook.c):

    #include "klshoulder.c"          after  #include "klbalance.c"
    klo_tick(game_thread);           in klh_tick, after  klr_tick(game_thread);
    klo_init();                      in the init list, after  klr_init();

KLHook.ini:

    [Shoulder]
    ; a log of what holds the camera's shoulder side (reads only). 0 = off
    Log=1

One line a second while a local ZFFPlayer exists, and one at once on every change (`CHANGE name old->new ...`):

    shoulder: f02\f02_main model 9011 P 6fafa990 | want R side R (280c 0, 818 00000000) pend 0/0.00 cover 0 saved 2
      | 2954 0 heli 00000000 kind 02 in 00000000 st 00000000 tun 1 lock 0.00
      | down D 12345678 state 0 flag 00 keep 2 a54 0080 | key held 0 fired 0 timer 0.080 action .. bound ..
      | key free; side free

(one line in the file). `want` = `[P+0x29a0]`, `side` = bit 10 of `[P+0x818]`, `pend` = `[P+0xb8c]` / `[P+0xb88]`,
`cover` = `[P+0xb84]`, `saved` = `[P+0xa98]`, `kind` = `[P+0x2720]`, `in` = `[P+0xed0]`, `st` = `[P+0xbbc]`, `tun` =
the tuning bool, `lock` = `[H+0x330]`, `down` = D with `[D+4]`, `[D+8]`, `[D+0x30]`, `a54` = `[P+0xa54]`, `key` = the
record at H+0x30 (held = its timer is running), `model` = `[[P+4]+0x68]`. The end of the line is the hook's own
reading: `key free` / `key REFUSED by <tun kind 2954 heli in.80 lock>` and `side free` / `side FORCED LEFT` /
`side FORCED RIGHT`.

**What one round on Late Night Opening with the key held a few times decides:**

| seen in the log | means | next step |
|---|---|---|
| never `held 0->1` | the game does not see the key (binding / action map / `bound 00000000`) - not the level | the owner's key settings; try the pad's stick click |
| `held 0->1` but never `fired 0->1`, `lock` > 0 | the input lock stays up | who calls the input reset (0x8180cc) on this map |
| `fired 0->1`, `want` unchanged, line says `key REFUSED by ...` | that gate: `in.80` = a PlayerInputManipulator after all; `2954` / `heli` / `kind` / `tun` = that field | follow the named field's writer |
| `want` toggles, `side` does not, `side FORCED LEFT` | the down-not-dead flag is stuck (`state`, `flag`, `keep` say how) | why 0x88a990 did not run (revive by a bot? the fed respawn?) |
| `want` toggles, `side` does not, `side FORCED RIGHT` | `a54` bit 1 stuck | the same for the lying-down bit |
| `want` and `side` toggle, `side` flips back within a second | another caller: `cover` / `pend` / `saved` on the lines around it say which (a cover box the player stands in, the base move) | the cover boxes at that place (`kl_fix_lean.py check`) |
| `want` and `side` toggle and stay | the player code did its part | the camera: 0x9088c0, the `CameraTransitionSpline` object, the camera profile - or the picture is right and the complaint is something else |

The same round on the bank gives the reference lines.
