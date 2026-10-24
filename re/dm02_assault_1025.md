# DM02 SWAT shutter assault (2026-10-25, staged, not installed)

Tool: tools/kl_dm02_assault_1025.py. Stage: C:/kl_build_1024/dm02assault_1025a (INSTALL/UNDO dm02 assault.bat, backup .before-1025dm02assault).
DM02 30b3ddf0 (shops A) -> ae193d9c. Chained on shops A; shops untouched.

Player sees: 150 s after round start the two unused ground-floor Atrium shutters (west side north end, x -1990 z -2665..-2025; east side south end,
x 1990 z 1660..1020) play Shutters_Sound; 2.4 s later they vanish (DeactivateGeom, no raise animation). Two squads of 6 PoliceSwats (released 0.8 s
after the sound, standing 60 cm behind the closed shutters, off the mesh) walk to posts 450-1500 cm into the atrium. Actors 49->61, squads 19->21.

Unproven: actors released ~100 cm off the nav mesh finding a path; DeactivateGeom hiding the model; Audio_PlaySound field 0 with the DM02 sound id;
timings; the 4 template actors are reused for 6 men per squad. `floor` probe: ground exists under all 12 entries.
