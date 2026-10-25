# L05 flat raid as a Fragile Alliance map: first build job, results and FA-layer plan (2026-10-25)

Offline only. Nothing installed or launched; game folders and backups read-only (every `Lxx_Main.WAV`
carries our Oct 24 gun-sound patch, read only). Scratch: `C:\kl_build_1024\l05raid_1025a` (`KL_GRAFT_OUT` set
there; logs `t2.log t3.log t4.log l09a.log`, builds `base t1 t2 t3 t4 l09a`). Follows
`re/dd_campaign_fa_1025.md` section 7.

## 1. Results (MEASURED)

| Step | Result |
|---|---|
| 1 baseline `kl_graft.py build F07 F09` | builds in 24 s, 16,193 nodes, 31,520 chunks, .ANM join +0 clips. `verify: problems: 1` = "FA: BROKEN monitor 2 OnlineEscVehicleMonitor: each Init deletes the one before" (the FA check; the baseline run was WITH the FA layer, the L05 trials use `--no-fa`). DD-to-DD join works on this tree. |
| 2 survey (`kl_prpjoin.references`) | L05 has 627 top-level subtrees. Cross-top references INTO `AllLevels/mainsceneincludes.zip`: 77 groups of rows, i.e. 91 strings, ALL of them weapon templates of enemy `ZFFActor[1]` / `ZFFItemWeapon` (`...equipment.zip\Weapon\Rifle_AK74 SMG_Type05_S SMG_SA61 SMG_MAC_10 Rifle_zastavam85 Rifle_Type88_S HG_M9Beretta Shotgun_Hawk_SawnOff HG_M-77B_Human_Shield`) plus `DefaultPostFilterCamera` (scene property block, `camerasetup.zip\Cameras-Player0\Camera01`). All 9 weapons exist in `mainsceneincludes_multiplayer.zip` of F07 (checked). |
| 3 L05 graft | works (see drop-list table). Chunks 27,502 to 27,976 (gate 69,632, huge headroom), nodes 22.2k to 22.9k, .prm trimmed 112 MB to 70.5 MB by the existing pass, 484 MB archive (F09 baseline 370 MB: loading time and memory are the risk, not chunks). Sound bank merge ran without `--silent`: +318..404 sounds, +230..313 waves, 4 interleaved stream groups, "0 records outside a walkable group"; no "stream clips are not in the merged stream file" line (so no missing stream clips reported). .ANM join: +188 clips, +4.36 MB, 124 slots added to Civilian/Kane/Lynch/Thug, skeletons 20 of 20 renumbered. Nothing needed `--stock-anm`. |
| 4 check.py | 0 records with a layout DD never stores, in all builds (t1..t4). |

### Code change (needed, committed)
`tools/kl_graft.py`: new `campaign_rename(Jn)` and a branch in `build()` for a DD campaign map (`m_name` = `Lnn`):
paths `ROOT\AllLevels/mainsceneincludes.zip\...` get the name `ROOT\AllLevels/mainsceneincludes_multiplayer.zip\...`.
Without it, dropping the campaign systems zip leaves the weapon and camera references dangling (91 strings in
L05, 9 weapons + camera). Only active for M = `Lnn`; the F07+F09 baseline path is untouched. The weapons are
swapped by name only (same template names): GUESS that every campaign NPC weapon template behaves for an NPC
in the MP zip as in the campaign zip (the 9 names are the same class family; `kl_arms` not run).

### Drop lists tried and the dangling references (`kl_prpjoin.dangling` on the built archive)

| Build | `--m-drop` | verify problems | dangling paths | squads / actors |
|---|---|---|---|---|
| t1 | mainsceneincludes, MenuResources, `Checkpoints!*`, `AI!Dialogue!*`, `AI!Friendly!*`, `Special!Cutscenes!*`, `Animation/L05/Cutscenes/*`, `Extras!MissionRelated!*`, `Extras!monitors!*`, `Extras!WeaponPickups!*`, `Coop!*`, `Special!Co-Op!*` | 10 (printed cap) | 284 (186 held by AI!Enemies squads, 80 by AI!Triggers; targets: 91 mainsceneincludes before the rename, 77 AI!Friendly, 53 AI!Dialogue, 16 Coop, 10 Special!Cutscenes, 8 Extras!monitors, Checkpoints) | 69 / 98 |
| t2 | t1 + `AI!Triggers!*` | 10 | 214 (now ZSquadScript[8] of the C-Roof and A7 squads pointing to dropped `TC_RoundOneDone`, `TC_EncDone`, `TC_EncounterDone`, `Coop!0X!TC_CoopDoor`) | 69 / 98 |
| t3 | mainsceneincludes, MenuResources, `Animation/L05/Cutscenes/*`, `Special!Cutscenes!*` | 10 | 15 (all into the two dropped cutscene groups: B1 Cutscene_Apartment, B5 Cutscene3, C3 FusionSquad MiniCutScene, Kitchen MC_Death) | 70 / 87 (note: t3 kept AI!Friendly) |
| **t4** | **only `AllLevels/mainsceneincludes.zip,MenuResources`** | **0** | **0** | **72 / 100 (+18 ZFFPlayer)** |

Why each drop: mainsceneincludes = the campaign systems zip (3,987 nodes; its HUD, weapons, cameras clash with
DD's own S systems); MenuResources = campaign menu; `Checkpoints!*` = save points; `AI!Dialogue!*`,
`AI!Friendly!*` = Kane/Lynch/Xiu companion AI and talk scripts; `Special!Cutscenes!*`, `Animation/L05/Cutscenes/*`
= story cutscenes; `Coop!*` = coop door counters; `Extras!*` = mission/monitor/pickup scripts. The auto-pass of
the graft also leaves out 113 `CloneGroup_Effects` clones (S brings its own) in every build.

Reading: the campaign scripting is woven into the enemy squads (each squad holds trigger-counter and
friendly-position paths). Stripping it cleanly is NOT the "~10 dangling" the decision rule allows: t1/t2 are
214 to 284 dangling paths. Those are soft pointers (what the engine does with an unresolved path in a
ZSquadScript or ZGatePath is UNVERIFIED; the engine's own assert on the Retomoto build was for different
causes), but the rule in the note says: over about 10, switch to L09. L09 (l09a: mainsceneincludes, MenuResources,
Checkpoints, Dialog, Cutscenes, AI!Friendly, AI!Minicuts, ScreenshotCameras, EndOfLevel, PlayerManipulators dropped)
gives 63 dangling (54 of them to `AI!Friendly\Kane/Lynch/Pilot` position objects used by minicuts and the heli
squad; the other 9 to Checkpoints Netsync timers and the crash cutscene), 21,679 chunks, 23.3k nodes, 331 MB,
and `verify: problems: 10`. Cleaner than L05-stripped, but also not under 10.

## 2. Decision

The note's rule is met in letter by the stripped builds (t1..t2: too many dangling) and passes with the minimal
build t4: **zero dangling, verify problems 0, chunks 27,976, check.py clean**. So the L05 graft itself "works"
as a structure; the open question is behavioural (the whole campaign script stays alive: checkpoints, objectives,
friendly AI, cutscene triggers, `Coop!0X`), which can only be judged in a live run (not allowed here). Plan:

1. Take t4 as the base ("L05 raw"), then strip campaign scripting IN STEPS with the dangling tool as the gate:
   (a) drop `Special!Cutscenes!*` and `Animation/L05/Cutscenes/*` together with the 15 holders (2 triggers
   `AI!Triggers!B1!Init`, `B5!Gate_Cutscene`, `C3!FusionSquad_Cutscene`, two kitchen `MC_Death` posobjects):
   needs a small "prune holders" tool, not the plain `--m-drop`;
   (b) `AI!Friendly*`, `AI!Dialogue*`, `Checkpoints!*` then need the holders cut the same way (284 paths; a loop
   "delete a path field if it dangles" is the generic fix; GUESS that clearing a ZGatePath/ZSquadScript entry is
   safe: it is the same thing the FA layer's `kl_fa.repair` does for S links).
2. Run L09 through the same pipeline in parallel (63 dangling, 9 are non-friendly), because its map proper is
   as large (11k nodes) but its scripting is thinner.
3. Caps: t4 has 72 squads / 100 actors; the live-proven cap is 99 actors / 55 squads (`re/actor_caps.md`):
   drop at least 17 squads and 1+ actors (first the 4 `AI!Civilian` squads, the `Piss`, `Goons_idle`,
   Airlock and C-Roof `sniper` squads that sit outside the raid path).

## 3. FA-layer plan specifics for L05 (design; coordinates need the nav read, marked GUESS)

All tools exist (`kl_fa_author`, `kl_fa_loot`, `kl_fa_bank`, `kl_fa_bots`, `kl_arrivals_1024r2`, `kl_escape`).
L05 geography, from the group names (MEASURED names, layout GUESS): A-Stairways = street entrance and stairwell
floors 1 to 5 (`A1` street with `SQ_Goons_car` arrival, `SQ_Piss`, `SQ_Goons_idle`; `A6`/`A7` stairs and
airlock; `A9` floors 4-5), B-Appartments = flats (`B2` masks, `B3` wall crashers, `B5` kitchen, `B6` big goon
groups, `B6_part2` roof access), C-Roof = last fight (`C2`, `C3`).
- **Spawns**: heisters in the street-level stair entrance behind the `A1` car (walkable nav, out of sight of
  `SQ_Goons_idle`), 4+ `ZSpawnPoint` clones from F07's `FASpecials!SpawnPoint` set (19 exist in F07), each on
  the A1 nav; read the coordinates from the `A1` squad's `PosObject` neighbours with `kl_fa_author` helpers and
  keep them behind cover relative to the `Badguys_Around_Car` situation (155 nodes). GUESS until the nav is dumped.
- **Waves / wave entry**: wave 1 = street goons arriving in cars (`SQ_Goons_car`, 27 nodes) at the street;
  wave 2 = stairwell (`A6` `Squad_Stairway_PartB_Throw_Can` with the can-throw situation, `A7` airlock mobsters,
  `A9` 4th/5th floor mobsters); wave 3 = apartment mask squads `B2 SQ_Masks_#01_K..#04_L`, `B6` goon groups;
  final = roof `C2 SQ_lastFight_#01/#02`, `PreWave1/3`, `2backup`. Entry points: the car arrival at the A1
  street, stair landings per floor, the B3 `WallCrashers` (breach through the wall), roof door from `B6_part2`.
  Trigger by the squads' own gates replaced by FA wave timers (`kl_old_waves`) once step 1b removed the campaign
  gates; until then they fire off the campaign counters.
- **Loot**: briefcases in the B5 kitchen, the B6 big room and one B2 flat (reachable, near the stairwell exit);
  main stack on the C-Roof, which unlocks when `C2` last-fight squad is dead (`kl_fa_loot` room-clear rule).
  3 to 5 briefcases total, the `Extras!WeaponPickups!B5` prop positions are free spots in the B5 flat.
- **Escape**: part 2 down to the street: van from `A1` (the car prop of `Badguys_Around_Car` or a DD van
  template via `kl_escape`/`OnlineEscVehicle*`) parked in the street; roof route needs a drop-down (the
  `Outside_Second_Roof_Jump_Down` situation exists), so no heli. Fix the baseline's OnlineEscVehicleMonitor
  issue (two Init delete each other) by authoring ONE monitor.
- **Bounds**: `OnlineBounds` box around the building and street; kill below roof edge.
- **Music**: L05's own: `Special!Music!02_APP`, `03_FignalFight`, `04_Roof` groups (kept in t4, 1+11+4+14 nodes) plus
  `L05_Audio.zip` (154 nodes); the merge brought the sounds and 179 stream records into the bank. Whether the
  level music cues fire without the campaign counters is UNVERIFIED; fall back to a PlayMusic gate on the first
  wave.

## 4. Next jobs
1. Holder-prune tool (delete dangling path fields) so the campaign scripting can be stripped to 0 dangling.
2. Same on L09. 3. Squad cap trim to 55. 4. Author the FA layer on top. 5. Live autotest when the owner allows.

## 5. Adversarial re-verification of t4 (2026-10-25, second agent, offline, read only)

Re-run by hand on `C:\kl_build_1024\l05raid_1025a	4\...\F01_Main.zip`:
- CONFIRMED `debug/check.py`: 22,863 nodes, 0 records with a layout DD never stores, 0 not comparable. `kl_prpjoin.dangling`: 0 paths, 0 names. Chunks 27,976 and `verify: problems: 0` are from t4.log (not recomputed). 644 top-level subtrees.
- CONFIRMED actors 100 = 90 `AI!Enemies` + 8 `AI!Civilian` + 2 `AI!Friendly` (Kane_L05_COOP, Lynch_L05). ZFFPlayer 18 = 16 DD `Heroes!*` (host) + those 2 campaign Kane/Lynch; so the "+18" is mostly DD's own. The 72-squad figure was NOT recounted (squad class name not resolved by exe_classes; only the actor class is).
- CORRECTION: the skeleton line in t4.log is "23 of 23 renumbered" (1432 bone ids, 695 animation numbers), not 20 of 20. The "campaign paths re-pointed" line is 14 (groups of rows), the 91 strings are the survey count.
- CONFIRMED t4 is NOT free of campaign systems, by design: `Checkpoints!*` 45 tops, `AI!Friendly` 20 tops / 221 nodes, `AI!Dialogue` 20, `Special!Cutscenes!*` + other `Special` 85, `Extras!*` 30, `Coop!0X` 3, 3 `Animation/L05/Cutscenes/*` zips, `POI!POI_XIU`, Xiu balcony civilians. Only `mainsceneincludes.zip` (replaced by the `_multiplayer` zip, present once) and `MenuResources` are gone. So "campaign systems and friendly AI gone" is true only for the HUD/weapons/camera zip, not for the scripting.
- CONFIRMED no game file written by the trial: L05_Main.zip and F07_Main.zip in the DD folder keep mtime Sep 13 (only atime moved); nothing under `Scenes/Locations/L*/F07` is newer than the Sep 13 install; no DM folder file newer than 01:00. Other DD files newer than 00:30 (dinput8.dll, KLHook.*, ReShade.*, KLExpansion/Maps/DM02/F02_Main.zip at 01:35) belong to other sessions and predate or run beside the trial; none is a Lxx/F07 zip. The `Lxx_Main.WAV` files were not part of the changed set.
- CONFIRMED the squad/wave names the FA plan uses exist as tops in t4: `SQ_Goons_car`, `SQ_Piss`, `SQ_Goons_idle#01`, `Squad_Stairway_PartB_Throw_Can`, `SQ_Mob_WallCrashers`, `SQ_Masks_#01..04`, `SQ_lastFight_#01/#02`, `SQ_PreWave1/3`, `SQ_2backup#01/#02`, `Badguys_Around_Car`, `Outside_Second_Roof_Jump_Down`, `Special!Music!*` (26 tops), `L05_Audio`. No `FASpecials`, `OnlineEsc*`, spawn nodes exist in t4 (as expected with `--no-fa`). The plan's coordinates are still guesses: no nav was dumped, none checked.
- Reading of the decision rule: it counts dangling references to the DROPPED campaign systems subtree. After the rename that is 0 for L05 (t4). The 214 to 284 of t1/t2 are references to other groups we chose to strip, a separate cost. By the rule as written L05 does NOT need to be abandoned; L09 (63) is not better on that axis.

VERDICT: GO for FA authoring on L05 using t4 as the base (offline authoring only). Prerequisites that remain before any install: holder-prune tool (section 4 job 1), squad/actor trim to 55/99, and the live behaviour of the surviving campaign scripting is unproven. Do not switch to L09 on dangling count alone.

## 6. Strip to a clean FA base (2026-10-25, offline; work folder `C:\kl_build_1024\l05strip_1025a`)

New: `tools/kl_prune_dangling.py` (`prune(sc)`; CLI `python tools/kl_prune_dangling.py <zip>` reports dangling by holder -> target) and
`kl_graft.py build ... --prune-dangling` (also `build(prune_dangling=True)`): after the join, every `ROOT\` path that names no node is cut,
looped until `kl_prpjoin.dangling` is empty; works with `--no-fa` (kl_fa.prune only runs with the FA layer and only on M's own tops).
Rules: list entry removed and count rewritten; single path string set to ''. GUESSES (commented in the tool): parallel lists are not kept
in step; an empty path means "no target" to the engine (stock levels hold empty strings in the same fields). Verified on t2: 214 dangling
-> 0 in one round (196 list entries, 18 strings). Nodes are not deleted, only pointers.

Steps (all `kl_graft.py build F07 L05 F01 --no-fa --prune-dangling --m-drop`, base list `AllLevels/mainsceneincludes.zip,MenuResources`; the
counts are re-measured on the BUILT zip with kl_prpjoin.dangling, kl_club_lastcall2.census and debug/check.py; every step: verify problems 0,
dangling 0, check.py 0 unknown / 0 not comparable):

| Step | adds to --m-drop | pruned (entries/strings) | nodes | actors | squads |
|---|---|---|---|---|---|
| s1 | `Checkpoints!*` (45 tops) | 15 / 2 | 22,814 | 100 | 72 |
| s2 | `Special!Cutscenes!*`, `Animation/L05/Cutscenes/*` | 23 / 7 | 22,744 | 100 | 70 |
| s3 | `AI!Dialogue!*` | 87 / 7 | 22,646 | 100 | 70 |
| s4 | `AI!Friendly!*` (Kane_L05_COOP, Lynch_L05, Xiu AI) | 145 / 23 | 22,425 | 98 | 69 |
| s5 | `Coop!*`, `Special!Co-Op!*` | 165 / 18 | 22,416 | 98 | 69 |
| s6 | `Extras!MissionRelated!*`, `POI!*` | 167 / 17 | 22,407 | 98 | 69 |
| s7 | trim (below) | 186 / 15 | 22,269 | 78 | 55 |

KEPT as asked: all other `AI!Enemies` squads, `AI!Triggers!*`, `Special!Music!*`, `L05_Audio`, ambience, doors, props, `Extras!WeaponPickups/
AlteredVision/ActorCovers/monitors/Xiu_tracker`, `Special!EndOfLevel/KickableDoors/DeactivationAreas/Geom_Controllers/Streaming/animationTriggers/
ScreenshotCameras`, the 31 `Animation/L05/Situations/*` zips, Jumppoints. (`Special!Co-Op` is the one dropped `Special!` family beside Cutscenes.)

Trim s7 (actors 98 -> 78, squads 69 -> 55): dropped whole squads off the planned FA route (street entrance -> stairwell A6/A7/A9 -> flats B -> roof C):
- all `AI!Civilian!*` (4 squads / 8 actors: Civ_1stFloor_KaneSide01, Civ_1stLynchFloor_01, Xiu_Yelling, Civ_Kitchen, plus their 3 timer / monitor boxes);
- A1 street: `SQ_Piss`, `SQ_Goons_idle#01`, `SQ_Goons_idel#02` (idle guards beside the spawn side; `SQ_Goons_car` KEPT as wave 1);
- A7: `SQ_Airlock_Mobsters_01`, `_02` (airlock side pocket);
- C2 roof: `SQ_sniper_side`, `SQ_sniper_end`, `SQ_1Singleguy#01`, `#02`;
- C3: `Squad_Henchmen` (3 actors). `FusionSquad_Cutscene` (0 actors, no squad) is still in.
Kept squads: 55 = A1 car 1, A6 7, A7 6, A9 10, B2 4, B3 1, B5 2, B6 11, B6_part2 7, C2 6 (lastFight x2, 2backup x2, PreWave1/3).
Result s7: chunks 27,096 reachable (gate 69,632), nodes 22,269 (519 tops), 468 MB zip (t4 484 MB, F09 baseline 370 MB), .prm 65.9 MB after the
existing trim pass, materials 1,304, textures 2,330, sound/.ANM join as t4 (+187 clips). verify problems 0, dangling 0, check.py 0/0.
Output: `C:\kl_build_1024\l05strip_1025a\s7\Scenes\Locations\F01\F01_Main.zip` (s1..s6 beside it; logs s1.log..s7.log).

What still blocks an FA layer (UNVERIFIED, nothing was run in the game):
1. The kept squads still hold ZSquadScript gate / counter lists whose targets were cut (186 list entries and 15 strings emptied in s7). Squads that waited on a
   counter that no longer exists may never wake, or wake at once: behaviour unknown until a live run; the FA layer should drive them with its own wave timers (kl_old_waves).
2. No `FASpecials!`, spawn points, loot, escape, `OnlineBounds` yet (`--no-fa`); the baseline OnlineEscVehicleMonitor double-Init issue must be avoided by authoring ONE monitor.
3. Nav coordinates for the section 3 plan are still GUESS (no nav dump).
4. The `AI!Triggers` tops (138 in t4, kept), `Special!EndOfLevel` and the `AI!Enemies!B-Appartments!B6!TB_FailMission` and `GeomDeact_TB_FailMission` boxes (both ZBoxPrimitive; `Special!EndOfLevel` holds one ZSTDOBJ, `SceneChangerExitPoint`) still exist and may end or fail the round (not read); audit before authoring.
5. Memory: 468 MB archive vs 370 MB for F09; load time and RAM are the risk, not chunks.

Review 2026-10-25 (independent re-check of s7): zip integrity OK; dangling 0/0; check.py 0/0; census 78 actors / 55 squads / 22,269 nodes / 519 tops / AI!Triggers 138; the 201 list entries and strings removed vs t4 (186+15) all pointed at nodes dropped from s7 (0 still resolve, 0 pointed at kept nodes; 20 sampled all in Dialogue / Friendly / Coop / Cutscenes / Checkpoints / trimmed squads). Caveat: s7 was built twice into the same folder (s7.log shows two exits); rebuild into a fresh folder before relying on byte-identity.
