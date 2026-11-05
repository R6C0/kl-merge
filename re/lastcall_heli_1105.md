# Last Call (DM05A): chopper not showing, grey screen, no escape screen (2026-11-05)

Offline only; nothing launched, nothing written into the game folder. Owner report after a real round: "last call the chopper still aint showing
and screen goes grey still and u dont see the escape screen or anything". Round log: scratchpad lc1105\r.log (SHIP hook 288fb016, 18:16-18:25).
Fix = tools/kl_club_heli_1105.py (level data only; NO hook change). Staged in C:\kl_build_1024\lastcall_heli_1105\stage (install.py, UNDO).

## What the log proves
- The escape vehicle state machine ran 1 -> 3 -> 5 -> 7 -> 0, you climbed in (status 4), escaped (status 6), round-over 0x1f -> shop 0x20. That is
  open-loop timers: it says nothing about the chopper (re/hasta_heli_move.md already said so).
- The ZHeli (zheli=5772bd00) sat at (15394, 6942, 18351) for the whole round (391 samples), the vehicle group at (15349, 6612, 18314); the box you
  board in is at (7361, 2014, 3201). `rout=0 goal=0` is the probe's default (it scans the entity table only): measures nothing.
- 15 km out is NOT itself the fault: the stock approach spline starts ~15k out in DM06 and Hasta too (debug/heli_call_read.py + world dump). The
  Incomming spline ends 368 over the pad platform in all three maps. Track "placement" of the three investigations (chopper 17.7 km off, never
  translated) is REFUTED on this point; the translation D=(10200,1022,-400) of lastcall2 is applied (world pad reached, heli_call_read PASS).

## Diagnosis (checked by me in the live zip e9fab045)
1. HIDDEN CHOPPER (PROVEN data difference, cause is a GUESS). `EscapeSetup!EscapeChopper\Escape_Chopper` (node 10807) is hidden from the load
   (ZGEOM[3]=1, .gms flag 0x400) AND a round-start `DeactivateGeom` (`RivalMercs!DisableVisionBlocker!GeomDeactivator`, in AIMonitor's round-start
   list) names it, with `ActivateGeom GeomActivator_TearGas_LEFT` on 30 s / 25 s timers as the only "show". The builds in which this chopper
   FLEW (DM06; Hasta no-hide, owner log 10-18) have the group visible and no such wire; every build in which it never moved (Hasta hide build,
   all Last Call builds) is hidden. re/heli_call.md: the rout's init 0x815aa0 skips nodes whose [ent+0x3c] bit 0x400 is set. GUESS: hidden at
   load = the rout is built without an actor (or the actor never ticks), so showing the model later with ActivateGeom does not start it. Not
   proven that the timers fire in an FA round; whether they fire does not matter for the fix.
2. ESCAPE CAMERA EYE == TARGET (PROVEN data fault; that it is the grey picture is a GUESS). `EscCameraSetup!EscCamera01` is mode
   `eFMM_LookFromPosFA`; Dog Days puts the eye at the box's own node and aims at field 9 = CamPos01 (kl2 0x4471a1). Pass 1024n
   (kl_club_lastcall.py) put box, CamPos01 and EscCameraLAST on one point (7800, 2271, 3500) assuming LookFromPos, so the view direction is zero.
   re/map_escape.md 1.2 already documents the repair (field 11 -> eFMM_LookFromPos) and DM06 has it; DM05A never got it. kl_map_escape.check
   did not flag it (its eye-in-air test passes). A map-wide check is cheap: eye == aim point while mode FromPosFA is a FAULT (not added to the checker here).
3. Missing escape screen: NOT explained offline. Nothing in the hook suppresses the stock escape camera or outro; klsb_render draws the scoreboard
   only in session 0x1f on every map. Most likely the same cause (camera on nothing, chopper 10 km away carrying the player). If the fix lands and the
   outro is still missing, that is a separate bug and needs the probe below.

## The fix (tools/kl_club_heli_1105.py, md5-pinned e9fab045, idempotent, by node NAME, no entity added or moved)
- Escape_Chopper: ZGEOM[3] 1 -> 0, flag 0x400 cleared (the DM06 / Hasta no-hide form).
- GeomDeactivator target list -> empty (stock has 100+ empty DeactivateGeom lists, e.g. the RoofGlas ones). ActivateGeom TearGas_LEFT left as is
  (no-op on a visible group).
- EscCamera01 mode -> eFMM_LookFromPos; CamPos01 -> (7093, 2181, 2727): 8 m from the pad centre, 3 m over the floor y 1881, the only ring with floor
  under it and a clear line to the pad (kl_map_escape Ground.between; 20 clear spots, 255 degrees picked). kl_map_escape.cameras after: "300 over
  Platform_C_Mod_02, looks at the player, to the stop (7300, 2249, 3499) 8 m: clear", 0 faults. EscCamera01's node and EscCameraLAST stay.
- Zip members changed (for chaining with kl_club_life_1105 / kl_club_fight_1105): ONLY `Scenes/Locations/F01/F01_Main.prp` and `.gms`
  (.buf written back byte-equal). .oct .rmi .rmc .sgd .HVK .prm untouched. The pass edits four named nodes' values and one flag, so it is chain-safe in
  either order (run it with --force after another pass; then re-stage install.py's md5 pins).
- The online variant `F01_Main.bots.zip` (the hook's BotGate swaps it in online) gets the same pass (--force) and `F01_Main.bots.base.md5` follows.

## Files and md5s
| item | in | out |
|---|---|---|
| F01_Main.zip (live DM05A) | e9fab0453a5260369c2fddd01bed5534 | 731c4b6b4f87ba4aee17663b00dcf3e6 |
| F01_Main.bots.zip | 7a1024ed8cb031596136717f7256545e | 72c3536f075b41f0a13f3d49317af088 |
| F01_Main.bots.base.md5 (content) | e9fab045... | 731c4b6b... |
Backups `<name>.before-1105heli` (never overwritten; install refuses if one exists). Install: `python install.py` in the stage folder (or the .bat);
UNDO: `python install.py --undo`; `--check` is read-only. Rehearsed on a scratch copy: install, a second install refused, undo byte-identical (3 files).
No hook change, so no new dll (live SHIP 288fb016 / TEST 5f52009d are what the test uses). Chaining: the other two agents' passes change the plain zip
too: whichever installs second must be rebuilt from the then-live zip (their md5 pins will say so), the bots zip likewise (see kl_botgate_stage_1026).

## Checks run
- tools/kl_club_heli_1105.py check: before NOT DONE, after DONE; a second build is a byte copy (idempotent).
- debug/heli_call_read.py --build staged: RESULT PASS ("hidden at start: NOTE not hidden", the rest unchanged).
- debug/check_passes.py on both staged zips: 0 failed (A oct offsets, B clones, C1-C3).
- kl_fa.check on live and staged plain zip: 0 findings each.
- kl_map_escape cameras: 0 faults, line of sight clear.
- klt_audit: not applicable (no .LOC / KLTalk change). tools/kl_tests.py: not run (no hook or tool library changed; only a new standalone script).

## Guesses (all)
(a) hidden-at-load is why the rout never moves the ZHeli; (b) the eye == target is the grey picture; (c) the camera spot is free air (collision-
checked only, not looked at); (d) the grey/outro symptom is one cause with the chopper being 10 km from the player. If a live round with the fix
still shows a static ZHeli, the next suspects are the rout's runtime preconditions ([actor+0x8c]/[0x90], re/hasta_heli_move.md (c)) and the HVK
type-3 placement (heli_hvk_origin.py), not the hide.

## Live test (when the game is free; the owner is playing now, do not run)
Needs the staged zips installed in a scratch / the DM05A slot via install.py, hook with `[Heli] Probe=2` (read-only; SHIP has it).
1. Round start: `grep "heli: t=" KLHook.log`: the ZHeli position must change within seconds of the vehicle call (state 1) and approach (7300, 2249, 3500);
   `rout=` non-zero, `started=1`, `goal=` non-zero. A ZHeli still at (15394, 6942, 18351) after state 3 = hypothesis (a) is wrong.
2. Human or scripted board in the box (7361, 2014, 3201): state 3 -> 4, then 5; the camera: `[Camera] Log=1` lines, eye (7093, 2181, 2727) while aboard.
   Screenshot at status 4/5: not grey, the chopper or the roof in view.
3. status 6: round-over panel (session 0x1f) appears; shop 0x20 follows. grep `escape` / `hud: ` for the panel; no panel with a good camera = separate bug.
4. A/B if needed: install.py --undo, same script, to confirm the change of behaviour. Online: bots.zip is used when BotGate is on; run one round.
