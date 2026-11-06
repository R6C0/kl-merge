# Last Call (DM05A, slot F01): "you dont see the escape screen or anything" (2026-11-06, static research)

Status: research only. No game launch, nothing installed, nothing built. P = proven in kl2.exe 0490 / level data / hook source.
GUESS = not provable offline. Read with `re/lastcall_heli_1105.md` (hidden chopper, EscCamera01 eye == target).

## 1. What a human sees after escaping in stock Dog Days Arcade (P)
1. The escape trigger puts the player aboard; heist status for the player becomes "escaped" (klfed logs `fed: you: status .. -> 6`).
2. A fixed camera takes over. Van maps (F01/F04/F05/F07/F09): `EscCameraInVan`, then `EscCamera01_01` (CCameraBox LookFromPos).
   Heli maps (F02/F03/F06/F08): `CameraInVan_01` (LookAtPos, in the vehicle) plus two outside cameras along the flight path
   (LookFromPosFA aimed at the heli). OnlineEscCamTrigger (0x5cd430) fires the box when the aboard player is in its trigger.
3. The vehicle panel ZFAEscapeDisplay (re/hud_escape.md) while waiting; when the round ends the rules enter state 0x1f
   (routine 0x5e8570, case at 0x5e8827 -> 0x7dede0 builds the nine round-over strings, hides clock and player list).
4. ROUND OVER panel (ZHeistOutroDisplay `[osd+0x10b4]`, Render 0x577e70, Arcade; online twin ZFAOutroDisplay 0x903830),
   8 s timer (deadline float `[el+0xd8]`), then state 0x20 score/shop page, then 0x25/0x16 next round.
5. The fixed escape camera is NOT released at 0x1f (release 0x7b68d0 is in the case at 0x5e8888), so the panel is a 2D layer
   over the still-active escape camera.

## 2. What the hook does (P)
- klhud_board2.c `klsb_ours` draws our board only when snapshot valid, state 0x1f and `0 < end < 2.0e6` and frame < end*1024;
  otherwise it calls the stock Render 0x577e70. Nothing hides ZHeistOutroDisplay or the camera. No klfed/klescort code touches cameras
  (klfed "phase 89" is a death-camera record byte, meaningless for escape; klescort "follow: over (you escaped)" is bot-follow logic).
- `[Camera]` in the live ini: UnstickOnline/LeanFollow/ShoulderCover all 0; `[Heli] Probe=1` is a probe only.
- Draw counters of the board are logged only at log level >= 2, so the existing logs cannot say whether our board or stock drew.

## 3. Last Call versus stock (P, from re/lastcall_heli_1105.md and the chain stage)
- Live DM05A (e9fab045): EscCamera01 is a box whose eye equals its target (degenerate look-at), no in-vehicle camera, no outside
  path cameras, empty vehicle field in the camera trigger, chopper hidden. Chain stage (c8dd18ee) repairs eye/target and the chopper.
- Timing matches the F06 graft bench: escape, about 3 s, then the 0x1f panel for 8 s.

## 4. Why the owner saw nothing: unresolved
- GUESS A (most likely): the camera trigger fires with a degenerate eye == aim (live zip), the 3D view is garbage/black and the
  owner reads that as "no escape screen". The 2D panel should still draw over it, so this alone does not explain a missing panel.
- GUESS B: the owner left before 0x1f (round-over only starts after the crew is resolved), so only the camera was ever shown.
- GUESS C: cut-scene/HUD-off mode `[0xcedfb8]` (written only at 0x82d028; 0x675470 then sets osd+0x1225 and few elements draw).
  Link from CCameraBox to that global is unproven.
- Not explained offline: no log shows `Scoreboard` draw counts for DM05A.

## 5. Concrete staged fix
Nothing staged (the data pass needs added entities, which renumbers slot ids across .oct/.rmi/.rmc, and a hook patch needs a live
look at the counters first). Proposed, in order:
1. Live check (when the owner says "test"): set `[Log] Level=2` once, escape on DM05A, grep `klsb` / `first snapshot ready` /
   "fed: you: status" in KLHook.log. This tells B from C in one run.
2. Data pass on top of the chain stage (`tools/kl_club_heli_1105.py` as template, md5-pinned to c8dd18ee, idempotent, edit-by-name only,
   no added entities): switch EscCamera01 to `eFMM_LookFromPosFA` with field 9 = Escape_Chopper node and CamPos moved to the
   flight path side, so the eye is the box node and the aim is the chopper (the form stock heli outside cameras use).
3. Only if step 1 shows the panel never drew: a `[HUD] ForceOutro` toggle (recommended on) that logs the Render result at 0x1f at level 1.

## 6. Open question list for the owner
Did the screen go black, show the sky, or show the map frozen? Did the round-over list appear at all before the next round started?
