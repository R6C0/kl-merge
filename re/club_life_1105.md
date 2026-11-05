# Last Call (DM05A) life pass, 2026-11-05 (offline, staged, NOT installed)

Tool: `tools/kl_club_life_1105.py` (`stage`, `check`). Stage: `C:\kl_build_1024\lastcall_life_1105\stage`.
Owner feedback this answers: "all the same guy same voice lines / more women in suits"; "just outside the club is too quiet, car noises";
"inside the club at the entrance you can hear the music slightly then dead silent in some parts".

## Findings
- All 40 crowd civilians were Dog Days model 41803 variant 1 (one man) with the male voice pair (civilian_male_01, civilian_male_03).
  The map's .prm already holds 8 men looks (41803 v1..v4, 41556 v2,v3,v4,v6); only the women are new.
- Street: the live bank already holds the traffic sets (car_horns, truckbus, car_idle, mopeds_horns, moped_driving, squeals, sirens_short)
  from F07; the map only had Street_01 / Street_Amb_3D beds. No sound merge needed for the street.
- Music: ZROOM nodes with no SoundLimiterFade "on" entry in any club layer: `M05_A_Inside_CarShop_01a`, `_Stairs_01a`, `_Daughter_Room_01b`
  (the dead spots). The other 14 Inside rooms are covered.
- The .prp positions of ZSNDOBJ are what the exe reads, but the .gms record carries the same translation and tools (KB.Built.world) read it:
  the pass writes both (kl_scene round-trips the stock .gms/.buf byte for byte; .buf stays unchanged).

## What changes (zip members)
`.prp` always. `.gms` (+19 B: model id of the changed civilians, 7 emitter translations), `.prm`, `.TEX`, `.MAT`, `.oct` (kl_chars.put
registers the women's model), `.SND` (+1776 B). Unchanged: `.fxc`, `.ANM`, `.buf`, `.sgd`, `.rmi`, `.rmc`, `.HVK`, `.LOC` and every other member
(`check` proves it), `.WHD`, `.WAV` (every female wave is already in the live bank). Beside the zip: `F01_Main_LS.SND`, `F01_Main.bots.zip`
and `F01_Main.bots.base.md5` regenerated (`kl_botsonline.convert`, eAllTypes); `KLJoin.ini` / `KLGuns.ini` Entries stays 54305 (put re-uses
dead chunks; the pass rewrites `Entries=` itself if the count ever changes). No entity, squad, route, nav or door is touched: it chains with
`kl_club_fight_1105.py` in either order (chain run on the fight stage 4f05020c: PASS). A bare fight stage has no bots sibling; the pass then stages none.

## Memory (live src e9fab045 -> stage)
| member | before | after | delta |
|---|---|---|---|
| .prm | 63,402,640 | 62,195,232 | -1,207,408 (put drops dead chunks once) |
| .TEX | 143,764,816 | 147,261,040 | +3,496,224 (1 woman model, +6 textures, +2 materials) |
| .MAT | 922,304 | 923,840 | +1,536 |
| .SND | 2,698,496 | 2,700,272 | +1,776 |
| .prp / .gms | 4,163,781 / 448,359 | +80 / +19 | |
| .fxc | 9,196,096 | 9,196,096 | 0 |
Census unchanged: 116 actors / 68 squads / 40 civilians (no entity added); .prm chunk count 54305 -> 54305; 20334 entities.
`--wide` (adds F08 1680, a second woman look) measured: .TEX +5,768,640, .prm -403,424, .MAT +2,208. Default is lean (one woman look, 12 of 40).
Bots' time budget (`kl_club_budget budget`): identical before and after (worst case 382 s of 360 s, slack -22 s; the pass touches no wait node).
Zip on disk is 135 MB (kl_chars.Lv.write deflates at level 1) vs 112 MB live: disk only, not RAM.

## Checks run (all PASS)
`kl_club_life_1105 check` (40 civs, 9 looks, voices match gender, every model a walkable root, .SND a pure addition per `S.verify`, members, bots sibling),
`debug/check_passes.py` (6 PASS), `kl_entries_check` (stale 0, botgate OK), `kl_fa_fedbody check` (PASS), `klt_audit` (36 pools, 0 miss),
install.py rehearsal into a scratch game folder (install, re-run, `--undo`: all four originals byte for byte). `kl_fa_civs.check` with the stale
`civs.json` (club_1024d) fails on the live map too (18 renamed civilians, "0 nodes") and says "model 41803 is not a live root" for any civilian whose model
this pass changed (it compares to the recorded model); the tool's own check does the equivalent real test. dmlines --fed and gunpics not re-run:
no .LOC, no gun chunk and no KLTalk offset changed.

## GUESS list (also as GUESS comments in the code)
1. The traffic sets loop or retrigger themselves when an emitter plays them (F07 uses them that way); if one is one-shot it plays once.
2. Limiter roles: list 0 = on, list 1 = off, floats 2/3 = fade in/out (copied from Street_01: on Streetbox, off inside + rooftop boxes); fades set to 3.0.
3. The Streetbox extents (10000 x 1000 x 2000) read as half or full extents; the 7 positions (x -1500..3200, y 250, z -3000..-4300) sit in it either way.
4. Emitter flag (second value after the sound offset) kept as it was (0).
5. Which 7 emitters to repurpose: roof ventilation duplicates with no reference anywhere (checked by `refs_to`); the roof loses 7 of its ~16 hum emitters.
6. Voice slots (female, female_02, 0) copied from F08's own female civilians; the men keep (male_01, male_03). Only 2 male + 2 female sets exist.
7. Music: adding rooms to the muffled layer's on-list is enough (same mechanism the entrance uses); level is the layer's own.

## Live test list (owner PC, not run here)
- Crowd: women visible (suit/office look, correct skeleton, no T-pose, no invisible head), men in different suits; no crash at load (a new model chunk, 6 textures).
- Women speak female lines when scared/fleeing; men unchanged.
- Street: stand outside the entrance and on the road: horns, truck, moped, tyre squeal, siren audible, quiet again inside the club; sets re-trigger.
- Music: walk entrance -> wardrobe -> stairs -> car shop -> daughter room: always a muffled club bed, never silence.
- Load a second round (the new model chunk and the SND merge survive a restart); `[BotGate]` bots sibling still loads.
- Install: `python stage\install.py` (kl2.exe closed), undo `python stage\install.py --undo`.
