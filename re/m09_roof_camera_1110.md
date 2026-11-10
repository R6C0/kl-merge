# M09 (Retomoto) roof camera in the Dead Men campaign - research, 2026-11-10 (offline, nothing run, nothing edited in code)

Owner: camera problem at the "Retomoto roof scene" (M09_A: roof, helicopter, rappel). Which phase he means is NOT stated
(no screenshot). The evidence below says the roof part's camera-relevant events are (1) the rappel and (2) the landing after it.

## 1. What the owner's session shows (KLHook.log, only M09 session: 00:03:09 .. 00:09:05, lines ~194472-195900)
PROVEN (log):
- 00:03:36.845 `camprappel: level: native rappel clips 5/5` - the five /Movement/Rappelling clips are in the level, guards installed.
- 00:04:44.797 `camprappel: use pressed at a rappel point (mode 2, clips 5/5) -> native starts`. This is the ONLY rappel event in the
  whole session; klcamprappel.c logs no end/landing state, so how it ended is not visible.
- 00:04:48.164 `camev: GATE frozen for 1.0 s: [cam+0x30] 1 [cam+0xc54] 4 [cam+0x504] 37833cc0 [cam+0x540] 37833cc0 (P 37833cc0)` -
  3.4 s after the press the camera EYE stood still >= 0.25 s while the player/pivot kept moving (klcam_watch STUCK2 rule,
  klcam.c:823-870) for over 1 s. Gate values are NORMAL (byte 1, counter 4, owner = player, no ABNORMAL tag), so the camera
  tick is running; the eye is simply held. That is what a camera that views from a fixed PosObject looks like (see 2), so it is
  a symptom of the rappel camera, not a stuck tick. Not repeated afterwards.
- Hook camera features are ALL active on the campaign level (klcam.c / klcamsmooth.c have no klcmp_level_active gate; grep
  "klcmp" in them = 0 hits): Blend 0.40 (25 profiles' times rewritten), CineAim FOV 0.698->0.80, FovStep, ShakeScale 0.80,
  CamSmooth Enable=1 (PivotMs 60, BlendMs 250, DtFix 1, StanceMs 280). camsm summaries run through the descent (04:46-04:56)
  with 28-69 h rewrites and 0-1 hitch resets; Log=0, so no per-frame detail.
- No STUCK2/LAG2 detail, no `camsm:` takeover lines (Log off). Nothing in the log is a fault or a camera crash.

## 2. How the stock rappel camera works (luvsic, loader/rappel.inc 284-300, static RE of kl2; READ by me)
- The player camera ZFFCamera1 (vt 0xbb76a4) = [player+0xbd8]. A CCameraBox hands its profile record (box+0x6c) to 0x700830 ->
  camera+0x7fc; 0x78bbc0 re-applies it each frame via 0x5ea690 (writes camera+0xb2c = current profile).
- Record: +0x4 PosObject, +0x20 ECamProfile, +0x150..157 valid flags, +0x15c FOV, +0x160/164 offsets, +0x168/16c distances,
  +0x180 EFMMode (DD: 1 LookAtPos, 3 LookFromPos = view direction PosObject->player), +0x184.
- 0x5ea690's tail copies profile +0x156 into camera+0x7eb; 0x87ae90 runs the camera COLLISION (slot 55 0x897d60: probe spheres,
  raycast, +0x394 blocked, +0x3f4 distance) only while +0x7eb is set.
- luvsic's own comment: camfix=nocoll exists "so the collision can't pull the camera in under the facade girders" (default OFF in
  his loader, camdiag ON). So the M09/M02 facade rappel camera is KNOWN to get pulled in by collision; he left a switch, and
  LUVSIC_CLAUDE.md:715 says "M09 rappel: ECP tables, the camera boxes and the rappel move are all identical to DM (proved). Still
  open; needs W's screenshot / which phase." i.e. luvsic never closed this either.
- Landing: his loader default `land=auto` (rappel.inc 69-72, 357-385): when the movement leaves id 0x10 with state 5 and the
  rappel is not active, a ray from chest height (130 cm), 150 cm along the facing, mask 0x28: wall hit -> `turncam` (M02),
  miss -> `cam` (M09). `cam` = call the player placement 0x82cc40(P, M, feet, 1, 1, 0) with force=1 to RE-AIM THE CAMERA behind
  the player (stock leaves the camera on the outward descent look; `turn` also flips the player 180 deg so his face is not in
  the corner of the screen).

## 3. What our port dropped (PROVEN by reading)
klhook/klcamprappel.c header (line 12) says it: "NOT PORTED: the loader's LIVE descent, the camera diag / camfix, the land= re-aim,
the ANP_rappel_cmd.txt test command." Mode=2 is native rappel only. So on M09 the campaign build has:
- no landing re-aim (luvsic's M09 default would be `cam`), so after the descent the camera keeps the outward look (probable
  "camera wrong after rappel" report);
- no camfix=nocoll (collision pull-in under the girders during the descent stays; luvsic also had it OFF by default, so he saw
  the same);
- no diagnostics, so we cannot see which profile/box was active.

## 4. Converter side (PROVEN from anp_logs/convert_M09.log; scene of the installed zip read with tools/kl_scene)
- 14 CCameraBox (9 aligned cost 0.6 + 5 same), 3 CutSequenceCamera, 8 CutSequence, 3 CutSequenceList/Player, 2 FFCamera1, 7
  ShakeCamera, 2 PictureInPictureCam; `camprofile kept 2`; player filter swap on CCameraBox: ONLY_KANE->ONLY_LYNCH x4,
  ONLY_LYNCH->ONLY_KANE x5 (ANP_PFILTER_SWAP, consistent with luvsic's "DD numbering reversed" and the human being "Lynch" in
  DD terms: `section Player->Lynch 12`). Rappel: 15 Kane + 15 Lynch DB rappel paths, RappelCB handlers kept both
  (RappelCB_BeforeVertigo, RappelCB_Leave node 220, RappelCheckPoint REF 215).
- Roof camera-relevant entities in the installed level (REF): Characters!Hero!CameraControl 53, Cam_Explosion 54,
  030_MiniCut_PreRappel 216 / _COOP 199, 070_MiniCut_LynchLockRappel_COOP 191, Trigger_StartMercsRappel 212, Timer_RappelDelay 211,
  RappelCheckPoint 215, Trigger_RappelBriefing 222, camera-stop colliders ColiObj_Camerastopper_01..03 (9839-9841),
  ColiObj_Obj_Camera_Blocker_01/02 (4860/4861), ColiObj_CAM_Box01 x5 (7169..7198). Those collision objects exist for DM's camera
  collision; DD's 0x897d60 probe is the same function family (luvsic: identical), so they should still act.
- GUESS: if the owner means the mini-cutscene before the rappel (030_MiniCut_PreRappel, camera in a DM mini-cutscene), the
  hook's CamSmooth would treat each cut as a "jump" and glide it (BlendMs 250): see 5b.

## 5. Candidate causes, ranked
a. (PROVEN missing, GUESS it is what he sees) NO LANDING RE-AIM after the roof rappel. luvsic's own default fixes exactly M09 with `cam`.
b. (GUESS) Hook camera features running on the campaign camera: klcamsmooth.c's jump detector (eye pose vs prediction, JumpCm 12)
   takes over any camera-box profile switch / cutscene cut / rappel start as an "aim transition" and rewrites the eye through
   node setter 0x7c9030 with a 250 ms decay; Blend 0.40 shortens profile times in the global table. Neither module checks
   klcmp_level_active() or the movement id. The GATE-frozen line shows the eye held at a fixed point during the rappel, the exact
   case the detector would fight. Cheap to rule out: ini [CamSmooth] Enable=0 / [Cam] Blend=0 for one M09 run (owner's call; I did
   not touch it).
c. (GUESS, luvsic documented) camera collision pull-in under facade girders during the descent (+0x7eb collision flag).
d. (GUESS, low) the 4 + 5 swapped CCameraBox filters: only matters if the human were not "Lynch"; luvsic proved the swap and the
   tables identical, and the roof boxes would show as WRONG camera everywhere, not at one scene.

## 6. Fix proposal (for the porting workflow; I changed no code)
1. klhook/klcamprappel.c, new function `kcamr_land_tick(P, mov)` called from kcamr_tick_body (after kcamr_vt_apply): port
   rp_monitor's landing detector - previous snapshot {mov+0x1f68 entry, 0x1f6c prompt, 0x1f6d started, 0x1f64 active, movement id
   = [[P+0x6b4]+0x44], state [P+0x25c0]}; landed = prev.movid == 0x10 && prev.state == 5 && now.movid != 0x10 && !active.
   On landed: yaw from the player node matrix (klfc_pose/KLFC pose helper as klfreeclimb.c cl_pose, line 191), ray at chest+130,
   150 cm forward, mask 0x28 (klfreeclimb.c ray helper); wall hit -> turn 180 + cam, else cam only. Call
   `KLFC_CALL(void(__fastcall*)(DWORD,DWORD,const float*,const float*,int,int,int), KLFC_TELE /*0x82cc40*/)(P, 0, M, feet, 1, 1, 0)`
   inside klfc_guard, exactly the form klfreeclimb.c:477 uses (there with 0,0,0). force=1 arms the stock 0.8 s cooldown (see the
   KLFC comment at klfreeclimb.c:34), fine after a rappel. New ini key `[CampRappel] Land=auto|off|turn|cam|turncam` default auto,
   labelled "(recommended on)" per the toggle rule; add a `camprappel: land=...` log line like luvsic's.
2. Same file, `kcamr_cam_tick(P, rappelling)`: port rp_cam_tick - read-only diagnostics first (cam = [P+0xbd8] with vt 0xbb76a4,
   profile [cam+0xb2c], box [cam+0x7fc], flag [cam+0x7eb], blocked [cam+0x394], dist [cam+0x3f4]) logged on profile change and at
   1 Hz while movement id == 0x10, so the next owner run answers "which profile". Then `CamNoColl=0/1`: while rappelling, zero
   prof[0x156] via klh_data (save/restore the byte list like g_rpCamSaved), restore on rappel end. Default 0 until a bench says
   it helps (luvsic left it off).
3. klcam.c / klcamsmooth.c: add a one-line guard `if (klcmp_level_active() && klh_rd32(klh_rd32(P + 0x6b4) + 0x44) == 0x10) { kcs_reset(); return; }`
   at klcamsmooth.c:~224 (next to the 0x4cd8 pause/cut test) and the equivalent in klcam's Blend/CineAim writers' tick, so the
   hook never smooths or rewrites the eye during a campaign rappel; optionally also skip while a CutSequence/MiniCutscene owns the
   camera (cam+0x4cd8 already resets camsm - check it covers the pre-rappel mini cutscene; GUESS). Coordinate with the workflow
   that is porting camera code into klhook: it touches the same files.
4. Test plan (no kl2 launched by me): extend klcamprappel_test.c / klcamprappel_logic.h with the landed-transition predicate and
   the Land= parse; bench on M09 later: log lines `camprappel: cam profile ...`, `camprappel: landed ... land=cam`, check 0 faults.
5. First thing to ask the owner (cheap): which moment - mini-cutscene before the rappel, the descent, or after landing? One
   M09 run with [CamSmooth] Enable=0 tells whether (b) is the cause without any new code.

## 7. Not found / limits
- No earlier Retomoto camera note exists in re/retomoto_owner_log.md (only the FA start-blast shake wish, line 40); this problem
  is new to the campaign build.
- I did not decode the 14 CCameraBox records of M09 with kl_rtp (no per-box dump was made); luvsic's claim "identical to DM"
  is taken as READ, not re-verified.
- The log has just one rappel and no after-rappel lines; the real symptom (wrong view vs frozen vs clipping) is unconfirmed.
