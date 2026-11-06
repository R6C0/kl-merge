# Last Call escape outro goes black (2026-11-06)

Bench lclive1106 run2: boarded 11:29:17, heli leaves ~11:29:59, shots 19-21 (11:30:09-11:30:49) fully black except the HUD,
round-over (0x1f) at 11:31:00. Units are cm.

## Cause
- P: EscCamera01 is eFMM_LookFromPos (kl2 0x447240). Eye FIXED at CamPos01 (7093, 2181, 2727), view toward the player pivot, and the
  player rides the heli (log: `camev: STUCK2 ... eye 7093 2181 2727`, piv398 moving ~1000 per 0.3 s).
- P: the Escaping spline (17 points) flies the heli 196 m from the pad (7058, 2271, 3467) to (-11691, 5616, -1819), 11 degrees up. It
  is 76 m out after 3 s and parked at the end from 11:30:13 until the round ends. Vehicle timers do not wait for the spline end.
- P: the ~60 s are two vehicle visits (visit 1 state 5 = 20 s, then the game's own last-vehicle visit 2 = 40 s), so the camera
  has no cut-away. Stock heli maps have in-heli / path cameras; DM05A has one fixed eye.
- G: black because the far direction is an unlit night sky and the chopper model is unlit. The waiting heli at 7.5 m (shots 17/18)
  is dark but visible. Not provable offline.

## Fix (data only): `tools/kl_club_outro_1106.py`
Cut the Escaping spline to its first 6 points (count at raw[4:8] 17 -> 6; field size unchanged, no entity added or moved, so .oct /
.rmi / .rmc / .HVK ids stay). The heli lifts off and slides to (4839, 2760, 4761), 31 m from the eye, and stays there in the same
framing as shots 17/18. Only the .prp changes. `--keep N` picks another length (distances from the eye: pts 0..6 = 7, 9, 12, 16, 24,
31, 40 m). G: the engine reads only the count. Rejected for now: switching to LookAtPos / chase eye (floats / setter unproven
offline), a light (unproven), trimming visit 2 in the hook (code, needs a live run; second step if the shots stay dark).

## Staging and install
- Stage C:\kl_build_1024\lcoutro_1106\ (230 MB): F01_Main.zip 77a42f74 (from e6d2f73e), F01_Main.bots.zip 2cef6d0b (from 54cb9e26),
  F01_Main.bots.base.md5. `install.py` pins e6d2f73e, backup tag `.before-outro1106`, `--undo`, `--dry`. Not installed.
- Chain: the doors stage (lcdoors_1106, a24d7432) and lcspawn2f_1106 are pinned to e6d2f73e too, so only one installs first. Restage the
  other on the new live files: `python tools/kl_club_outro_1106.py stage --in-dir <live DM05A dir or the other stage dir>`. Tested on
  the doors stage (-> 424f752e, only .prp differs; the doors stage was only read). The bots zip is rebuilt with kl_botsonline from the
  final plain zip, as the doors pass does; install.py of both passes covers F01_Main.zip, .bots.zip, .bots.base.md5.
- Test: `python tools/kl_club_outro_1106_test.py` PASS; `python tools/kl_tests.py` 89 pass, 0 fail, 5 skip.

## Bench plan (game free, owner OK)
Rerun lclive (E held in BoardingTrigger_Heli) with `D3dShotPost=1`, ReShade Bridge=1, `[Log] Level=2`.
- `heli: ... tick` lines (klheliprobe) after 11:29:59: the position stops near (4839, 2760, 4761) instead of (-10339, 5673, -1877).
- `cam:` / `camev:` lines: piv398 stays within ~35 m of the eye (before: 11 km by 11:30:08); eye unchanged.
- Shots 19-21 should show the heli silhouette (like 17/18) instead of black. If still black: the sky/light cause is right, next step is
  a light node or the hook trim of visit 2 (shorter outro).
- State sequence unchanged: veh1dc 5 -> 7 -> 0 -> 2 -> 4 -> 5 -> 7, session 0x1f about 60 s after departure, 0x20, fine score screen.

## 11-06 ~12:15 bench lcoutro1106 (stage 77a42f74, spline 17->6 pts): PARTIAL
- PASS 4/4, 0 faults, undo restored e6d2f73e. Player boarded 12:10:26, the vehicle left 12:11:07, session 0x1f at 12:11:30.
  The outro is now ONE visit, ~23 s (was 60 s: two visits). The forced last-vehicle visit 2 did not happen.
- The heli parks at zheli (6046, 2802, 4052), piv398 (5999, 2731, 4021): 17.8 m from the fixed eye (7093, 2181, 2727). The spline cut works as designed.
- Shots: 21 (12:11:00) shows the heli silhouette at the hover point. 22 (12:11:20, heli parked 18 m away) is ALL BLACK. 23 is the score screen.
  => distance was not the cause: from this eye, the view toward the parked heli is unlit (night sky / unlit heli).
- Next: an in-heli LookAtPos camera like stock F06 CameraInVan_01 (eFMM_LookAtPos, in-heli focus point, OnlineEscCamTrigger),
  or a light at the hover point. lcoutro_1106 is worth keeping either way (60 s -> ~20 s).
