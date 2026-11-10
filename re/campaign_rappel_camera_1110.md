# Campaign rappel: "our camera is better than his" - research + plan, 2026-11-10 (offline, nothing run, no code edited)

Owner: "our rappel camera is better than his, if you can fix it". The words do not say which of OUR cameras. Everything below is
labelled PROVEN (read in code/log/doc) or GUESS.

## 1. What "our rappel/climb/descent camera" is (searched klhook/ and re/)
There is NO dedicated rappel camera of ours. PROVEN by grep: klrappel.c (FA Retomoto cut descent) and klcamprappel.c touch the camera
only in the ways listed below; no module writes eye offsets for a descent. What exists:

A. The FA camera layer, active in every FA/Arcade round including the rappel/climb/lift moments (klcam.c, klcamsmooth.c, re/camera.md):
   Blend 0.40 (profile times of the global table), CineAim FOV 0.698->0.80, FovStep, ShakeScale 0.80, CamSmooth (PivotMs 60, BlendMs 250,
   DtFix, StanceMs 280: jump detector + eye rewrite through 0x7c9030), Unstick (slow-follow fix). This is the "feel" the owner tuned
   (owner log 10-23 "camera feel"). PROVEN that it ran during the campaign rappel before today (KLHook.log 00:04:44-00:04:56: camsm
   summaries, GATE frozen line, see re/m09_roof_camera_1110.md 1).
B. Free-climb camera (klfreeclimb.c:406-409, luvsic's climb.inc:415): at climb start `0x8fde70(player)` -> camera, then
   `0x798d00(cam, 67.0f, 40.0f, 0.5f)` ("the vault's camera settings", [Climb] Camera=1). Semantics of the 3 floats NOT decoded (GUESS:
   FOV-ish / distance / blend time of the vault camera). Same source as luvsic's, so it is NOT "ours vs his".
C. FA Retomoto start rappel (klrappel.c + level cut, re/rappel.md 8.4-8.5): the camera is the CUT's camera; owner-facing note in the log
   (10-12 09:35) says "the camera sits at the facade during the fall and the body was not in the few frames captured", never judged
   better. NOT a model to copy. PROVEN (doc).
D. Landing re-aim: only luvsic's (rappel.inc 357-385). Not ours.

Conclusion: the only thing that can be "better" and be OURS is A (the FA camera layer: smoothing, blend, FOV, shake). GUESS: that is
what the owner means, i.e. he saw luvsic's stock-camera rappel (jerky cuts between RappelCB boxes, outward look) next to ours.
ASK THE OWNER ONCE (cheap): "better = smoother box changes, FOV, framing during the fall, or the view after landing?"

## 2. State of the code today (worktree integ, uncommitted edits by the concurrent workflow, READ)
- klcamprappel.c (327 lines) now HAS: Land= (kcamr_land_watch -> kcamr_do_land, ray 130 cm / 150 cm / mask 0x28, 0x82cc40 with force=1 for
  the camera re-aim) and CamFix=nocoll (kcamr_cam_watch, zeroes prof+0x156, restores at rappel end). Both default off in code
  (`Land=off`, `CamFix=0`); the 1110 ini fragment presumably sets Land=auto. Both "GUESS (not run in kl2 yet)".
- klcam.c / klcamsmooth.c now have `klcam_campaign_idle()` = [Camera] CampaignOff=1 -> the WHOLE FA camera layer idles on a campaign level.
  THIS IS THE OPPOSITE of the owner's wish if CampaignOff=1 is shipped for the campaign: it removes A. PROVEN by the diff. The log of 00:04
  predates it (A was running).
- Hook points that exist: kcamr_tick_body (once per gameplay frame, game thread, guarded by klfc_guard, only on `klcmp_level_active()`
  cached 1 s, not online, not when klrappel owns the level), movement id `klfc_movid(P)` == 0x10 (rappel) or mov+0x1f64 (active byte).

## 3. Plan: [CampRappel] OurCamera=1 "(recommended on)"
Meaning: during a campaign rappel and a short tail after it, our camera layer (A) is ACTIVE even when [Camera] CampaignOff=1, and the
landing sets the view behind the player. Four steps, in order of value/risk:

1. Rappel exception to CampaignOff (PROVEN need, low risk, pure logic). In klcam_campaign_idle(): return 0 while
   `kcamr_rappelling()` (new, exported by klcamprappel.c: movid == 0x10 || [mov+0x1f64]) or within OurCameraTailMs (default 1500) after
   landing. klcam.c is included before klcamprappel.c: declare `static int kcamr_cam_ours(void);` forward, or move a flag
   `static volatile int klcmp_rappel_now` set by kcamr_tick_body (simplest: a global int in klcam.c, written by klcamprappel).
   Hysteresis matters: CamSmooth state (kcs_reset) must not flap; start resets once on entry (it does so itself on a jump).
   If CampaignOff=0 (current default) nothing changes: A already runs. Then OurCamera is a no-op and the log should say so
   ("camprappel: OurCamera: FA camera layer already active (CampaignOff=0)").
2. Landing: keep Land=auto (ported 1110): on the landing edge call 0x82cc40(P, M, feet, 1, 1, 0) (re-aim behind the player). With A active,
   CamSmooth treats the re-aim as a jump and glides it over BlendMs 250 (GUESS; if it fights, call kcs_reset() after the teleport).
   Add `[CampRappel] OurCamera` log line at landing: `camprappel: OurCamera: landed, tail 1500 ms`.
3. Descent framing (GUESS, optional, default off: OurCameraVault=0): at rappel start (edge of mov+0x1f64 0->1) call the vault camera
   setter exactly as klfreeclimb.c:406-409 does: `cam = KLFC_CALL(DWORD(__fastcall*)(DWORD,DWORD), KLFC_CAM_GET)(P,0)`; if
   `klfc_ok(cam,0xca0)` then `KLFC_CALL(void(__fastcall*)(DWORD,DWORD,float,float,float), KLFC_CAM_SET)(cam,0,67,40,0.5)` inside
   klfc_guard. UNKNOWN whether the stock rappel profile re-applies each frame and overwrites it (0x78bbc0 re-applies the profile record every
   frame) - probably yes, so this would only act for one frame. Do NOT ship without a bench; skip unless the owner names framing.
4. Collision: CamFix=nocoll stays an independent toggle (owner says his is worse; luvsic left it off). Recommend a bench pair
   CamFix=0/1 on the M09 facade; if OurCamera=1 the log lines from kcamr_cam_watch already name the profiles.

Fault guards: all engine calls inside klfc_guard (existing pattern); a fault sets kcamr_land_dead / kcamr_dead and OurCamera falls back to
"as CampaignOff says". No code-byte writes; heap/.data only via klh_data/klfc_put. Gate: `klcmp_level_active()` and `!kl_online()`.
Toggle rule: ini key plus a Mod Options row, label "(recommended on)", default 0 in code, 1 in the campaign ini fragment (ini_campaign_1110.txt).

## 4. Risks
- Biggest: shipping CampaignOff=1 as "recommended on" for the whole campaign while the owner wants our camera in the rappel (see 3.1).
- CamSmooth's jump detector vs the box switch at rappel start (RappelCB_BeforeVertigo etc.) and the GATE frozen 1.0 s line at 04:48: the
  eye is held at a PosObject by design (LookFromPos), which is the pattern the detector fights (GUESS; harmless in the log: gates normal).
- Teleport re-aim on landing could also re-aim a frame late and show one outward frame; `turn` variants flip the body 180 deg (M02 only).
- 0x798d00 semantics unknown (3.3); the collision flag edit touches shared profile records (restored at end, 16-record cap).
- Everything here has not run in kl2. Status of the ported Land/CamFix: unbenched.

## 5. Owner test (M09 roof, the 00:04:44 rappel in his KLHook.log)
Run 1 (A only, no new code needed): ini `[Camera] CampaignOff=0`, `[CamSmooth] Enable=1`, `[CampRappel] Mode=2 Land=auto CamFix=0`.
Rappel off the M09 roof; note: smooth start? eye held at fixed point? view after landing (behind him or outward)?
Log must show: `camprappel: use pressed ... native starts`, later `camprappel: land=... -> action ...`; 0 faults.
Run 2: same with `CamFix=1` (collision off during the descent): is the body in frame under the facade girders? log `camfix: N profile collision flag(s) restored`.
Run 3 (after step 1 is implemented): `CampaignOff=1 OurCamera=1`: rappel keeps our feel while the rest of the campaign is stock.
Comparison point for "better": [CamSmooth] Enable=0 and [Camera] Blend=0 for one rappel (= luvsic's stock feel).
Pause while the owner plays; scripted runs need the foreground.
