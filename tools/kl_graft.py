#!/usr/bin/env python3
"""
Graft: the game systems of one Dog Days level (S) and the map of another level (M) as one level
archive in a slot. Milestone A = two stock Dog Days levels (no Dead Men data): proves the join.

    python kl_graft.py plain F02 [F01]         stock F02 under the slot's names (the baseline)
    python kl_graft.py build F07 F09 [F01]     systems of F07 + map of F09 -> the slot's archive,
                                               verified; exit code 1 if a check fails
    python kl_graft.py build F07 M01_FA_A      the same with a Dead Men map (converted on the fly)
                       ... --geometry          experiment: only M's geometry, S's game-mode layer
                       ... --m-add / --m-drop / --s-keep / --s-drop A,B   bisect by top-level
                                               subtree name or family (class Select)
                       ... --silent            the map's sound references set to 0 (no bank merge)
                       ... --no-loc            bank merge without Dead Men's voice lines / .LOC keys
                       ... --light stock|m01|keep|off   kl_light.normalise mode (default stock)
                       ... --stock-anm         one stock .ANM and renamed sets instead of the join
                       ... --no-fa             no kl_fa repairs, none of S's FA plumbing kept
                       ... --no-postfilter     Dead Men map: WITHOUT its PostFilterBoxes and filter sets (default:
                                               taken, its colour curves appended to S's palette,
                                               kl_light.graft_postfilter)
                       ... --no-escape         Dead Men map: WITHOUT kl_escape's repairs (default: the wall its players
                                               climb is opened, money-container reach 125; re/escape.md)
                       ... --ao 0.5            Dead Men map: strength of its ambient-occlusion light map baked
                                               into the vertex colours (kl_light.bake_ao; default 0.5, 0 = off)
                       ... --no-bones          WITHOUT renumbering the skeletons of M's models to the joined level
                                               (default: bone ids and animation bone numbers rewritten, kl_chars)
                       ... --no-arms           Dead Men map: its characters' weapons by dm_rename's old guess ('one of
                                               S's whose name starts alike') instead of kl_arms' table (re/combat.md)
                       ... --author [module]   an authored FA layer. Alone: kl_fa_author.py's (Retomoto Tower; the
                                               two-part level is built by 'kl_maps.py chain ... --author'). With a
                                               name: that module of tools/ (the name follows the option directly;
                                               kl_fa_bank builds through its own 'kl_fa_bank.py test' only).
                                               What such a module holds: build()'s docstring
                       ... --load trim,slim    packing / weight options (load_options(); also the environment
                                               variable KL_GRAFT_LOAD, for builds made through kl_maps): trim = S's
                                               dead vertex data emptied always, slim = S's dead map textures down to
                                               4 x 4, stored, level=N, stamp=now. re/loading.md says what each saves.
    python kl_graft.py lighten <build folder> <out folder> [--load trim,slim,level=6]
                                               an existing build repacked with those options (default trim,slim;
                                               fxc = the shader cache cut to what the materials ask for);
                                               nothing is renumbered. Install it with 'install --from <out folder>'
    python kl_graft.py install [F01] [--from <folder>]   put the last build (or a kept one) into Dog Days
                                               (each stock file is MOVED to KL_PortBackup once, never overwritten)
    python kl_graft.py pairs                   which S / M pairs need the least guessing

Outputs: <work folder>/build/install/Scenes/Locations/<slot>/ (kl_port_check.workdir()).

WHO OWNS WHAT (S = systems level, M = map level; top-level subtrees by kl_prpjoin.sides)
  S is the BASE of every file with an id space, so nothing of S is renumbered: its REF ids, .prm
  chunk indices, texture ids, material slots, .buf head offsets and .SND offsets stay as they are.
  M's map subtrees are appended and everything of M is renumbered:
  .gms/.buf  kl_scene: S's map subtrees removed, M's grafted (new REF ids), M's .buf head appended
             at a constant shift. Top-level order = kl_prpjoin.graft_picks. Room pairs and
             light<->geometry lists between two grafted subtrees are restored from M (graft() only
             keeps those inside one subtree). Navigation mesh: M's (built before any entity loads,
             names none). Dynamic list: per class the larger of the two counts, heap budget: the
             sum (both ASSUMPTIONS; neither is decoded). Surface table: S's (its REFs are all
             systems effects). FDX bone-dynamics block: M's, model indices renumbered
             (kl_members.fdx_join) - it belongs to the hanging lamps of the map.
  .prp       kl_prpjoin.join, then on every node that came from M:
             chunk indices (kl_prmgraph.prp_roots: ZGEOM[4], ZWINPIC[2] ...) through the .prm map;
             ZROOM[9] / ZROOM[10] (gate array, neighbour lists) + shift when the room has any;
             ZParticleEmitter[10] / [11] + shift (ASSUMPTION that they are .buf offsets: all 56
             non-zero values of F01..F09 lie in the head, the rest are 0 or -1);
             sound references (type handlers 70 and 46 = offsets into the level's .SND, re/audio.md)
             rewritten into the merged bank by kl_snd.graft_audio (see .SND below).
             Heroes! are S's (systems) but take rotation / position from M's group of that name.
             Scene block: camera far plane, fog, background, SSAO from M; PostFilterBoxes from M
             (world-space boxes) or none; PostFilterPalettes stays S's, so M's post-filter sets
             index S's palette - harmless only when the two blobs are equal (python kl_graft.py pairs).
  KEYS       FOUND HERE (2026-10-09): the .buf head is addressed from the .gms too. An entity's
             raw data block of 64 bytes with 'KEYS' at +0x10 holds six .buf offsets at +0x28..+0x3c
             (key-frame tracks). With the ZROOM arrays and the emitter fields they cover the head
             of F01, F02, F04, F05 without a gap larger than one track. Grafted entities get them
             + shift. The 11 fields kl_prpjoin lists as "probably .buf offsets" are .SND offsets
             (handler 70 / 46) and are NOT shifted.
  .prm       S's file whole + the closure of M's roots (kl_prmgraph.append). S's dead map models
             stay in (bloat, no risk); only +0x1c of S's roots moves with the .oct.
  .TEX .MAT  kl_texmat merges, M's ids renumbered; MAT ref table recomputed from the joined .prm.
  .fxc       union.
  .oct       five-tree sets in room_order of the JOINED scene; root set = S's + M's with the
             entities that left removed; slot ids of both sides renumbered (old and new slots
             from the scenes before and after); S's records all kept, M's records of the kept
             models appended.
  .rmi .rmc  M's boxes renumbered (+ S's, if a systems room has one).
  .HVK       M's file is the base (static collision and MOPP order untouched), M's systems
             shapes dropped, S's systems shapes added, REF ids renumbered (kl_hvk.join).
  .sgd       both sides' shatter / explodable octrees with REFs renumbered (kl_members.sgd_join).
  .sgp       sound portals of M's rooms + S's systems rooms (kl_members.Sgp.join).
  .hrd       M's if all its rigid bodies come along (kl_members.hrd_join), else none.
  .ANM       S's file + the sets and slot names the joined level names of M's (kl_anmjoin.join,
             re/anmjoin.md): Dead Men car sets converted, Dead Men character sets are stand-ins
             (GUESSES, kl_anmjoin.STAND_IN). --stock-anm: one stock file and renamed sets.
  .SND .WHD .WAV  S's bank with what M's map nodes name of M's bank appended (kl_snd.graft_audio);
             nothing of S moves. Dead Men: records converted, streamed clips through the merged
             PC_Def.str (must be the one installed in Dog Days), room effects -> 0.
  .LOC       S's + the keys M's map names and S lacks, with their clips (Dead Men's voice lines).
             With them in the bank the map's OnlineSpeakTrigger controllers stay (mute_speech).
  _LS files  S's loading-sound bank beside the archive, _LS.SND with the merged bank's trailer
             offset. install() moves the slot's stock _LS files to KL_PortBackup the first time.
  the .xml members, .sup .zgf: S's.
  .hti       S's; kl2.exe holds no ".hti" string, so nothing reads it.
  lights     Dead Men map: kl_light.normalise (re/lighting.md) - a sun paired with rooms gets
             bit 0x8000 like F09's street suns; dead ZLIGHT[2] references removed.
  look       Dead Men map (re/lighting.md, second pass): its PostFilterBoxes and filter sets come along and
             its colour curves are appended to S's palette (kl_light.graft_postfilter); its ambient-occlusion
             light map is baked into the vertex colours at strength 0.5 (kl_light.bake_ao). Both seen live.
  weapons    Dead Men map: every character of M gets Dog Days weapons from kl_arms' table (class, depth, seed;
             re/combat.md) - never a human-shield / helicopter / player-only template, which the old guess by
             name handed out. A clone template that sets a define after its pooled copies is renamed
             (kl_fa.define_master: the human-shield execution crash at kl2 0x4098a1, the owner's round of 18:20).
  FA layer   S's position-free plumbing is kept (kl_fa.host_keep: escape-vehicle monitor,
             AIMonitor, briefing trigger and timer, three speakers) and kl_fa.repair runs on the
             joined scene (re/fa_round.md). Needed for a real round only; a direct boot has none.
NOT JOINED YET: light<->geometry lists between systems and map (dropped by remove/graft), S's
unused map models/textures (kept; '--load trim,slim' empties them in place, ids unchanged: re/loading.md).
  archive    deflate level 1, members in S's order, one fixed time stamp (STAMP): equal members = equal file.

CHOICE OF S AND M FOR MILESTONE A: S = F07, M = F09 (python kl_graft.py pairs). S must be one of
F04..F09 (their systems hold the particle templates: no dangling path, kl_prpjoin). Of those
pairs only F07 + F09 has all three: equal PostFilterPalettes blobs, every animation set of M's
map in S's .ANM (and the reverse), and neither level has an FDX block or PostFilterBoxes.
(F04 + F02, the first idea: palettes differ, F04's .ANM lacks 'Police', F04 has an FDX block.)

LIVE RUNS 2026-10-09 (python kl_autotest.py <wait>; the default wait of 200 s is too short: a
healthy level needs 205 s or more to its AutoExit and is then reported as 'hung')
  1 stock F02 as F01 (plain), wait 200   RESULT: hung - still running after 200 s
  2 the same, wait 420                   RESULT: clean exit after 207 s. On screen: Buffering 52 %
                                         at 70 s, 99 % at 115 s, black from 160 s. = the baseline
  3 F07 systems + F09 map, first build   RESULT: clean exit after 205 s. At 100 s the player
                                         stands in F09's map with HUD and weapon (screenshot
                                         <work>/research/graft_A_F07sys_F09map_100s.png), black
                                         at 150 s like the baseline. MILESTONE A.
  4 F07 systems + M01_FA_A map (B1)      RESULT: crash kl2.exe+0x18a7fc after 39 s. All 14,993
                                         nodes had loaded. ZHavokCarScript (slot 2) walks the wheel
                                         list of a ZHavokCar that kl_gms.RETYPE made a ZSTDOBJ.
                                         Fix: DeadMen drops controllers owned by the class a
                                         retyped node no longer is (5 HavokCarScriptRout, 1
                                         InventoryBinding).
  5 the same, rebuilt (B2), twice        RESULT: crash outside kl2.exe after 80 s, both times.
                                         Still on the loading screen (Buffering 99 % at 70 s).
                                         eip = 0x1ad7945c = the object ZFFGameData keeps at
                                         +0x48ac (gamedata + 0x3e3c, all zero), reached from the
                                         update 0x4bca90 at 0x4bccd5 -> thunk 0x8af460 -> resolver
                                         0x45d600 -> jmp eax. Slot 10 (0x705200) arms that pointer
                                         when a scene other than KaneAndLynch / AttractMode starts.
                                         CAUSE NOT ESTABLISHED: the same call passes in runs 2, 3.
                                         Next: tell the map from Dead Men's game-mode layer
                                         (--geometry; kl_hvk.join first has to accept static
                                         collision from S's layer: F07's escape vehicles have it).
  6 F07 + F09 rebuilt with the final tool RESULT: hung - still running after 331 s, nothing logged
  7 the same installed build, wait 400   RESULT: clean exit after 324 s (black screen at 100 s).
                                         AutoExit counts engine ticks, not seconds: the same
                                         level left after 205 s and after 324 s. Run 6 was most
                                         likely the slow clock again (not proven). USE A WAIT OF
                                         420 s OR MORE.
LIVE RUNS 2026-10-09, second set (python kl_autotest.py --shots ... ; F07 systems + M01_FA_A map)
  B-1 rebuilt with the current converters RESULT: crash outside kl2.exe after 87 s: the same jump
      (kl_mat now gets the converted .prm)   into ZFFGameData+0x3e3c as run 5.
  B-2 the same build, tables watched      RESULT: crash outside kl2.exe after 61 s. A read-only
      from outside (ReadProcessMemory)       watch of the save-state tables 0xe0de38 / 0xe09e38
                                             (re/crash_gamedata.md) showed 9 of 1228 entries turn
                                             from ZOnlineSpeakTrigger (vtable 0xbc98fc) into
                                             ZSerializable and then freed memory within a second.
                                             Cause: mute_speech(). Fix: those controllers go.
  B-3 without the 9 speech triggers       RESULT: crash kl2.exe+0x41e714 after 92 s. The level
                                             started (checkpoint taken at 88 s). A ZMatPosAnim
                                             read a bit-packed key index far outside the .buf:
                                             the KEYS chunk of M01's AnimatedRumbleCamera sits at
                                             +0xaa0 of a 2804-byte raw block and its six offsets
                                             were not shifted. Fix: keys_tracks().
  B-4 with every KEYS chunk shifted       RESULT: clean exit after 219 s. At 130 s the player
                                             runs along the street of Dead Men's M01 (Sunny Hill
                                             Plaza), textured, lit, with Dog Days' HUD and pistol,
                                             Dead Men's agents and cars in the car park
                                             (<work>/research/graft_B_F07sys_M01map_130s.png).
                                             Black at 100 s and 160 s, as the baseline is at times.
                                             MILESTONE B. This build is what the F01 slot holds.
LIVE RUNS 2026-10-09, third set (kl_autotest.py --shots; each run changes one thing; all end in
AutoExit of a direct boot unless said; NOBODY HAS LISTENED: a sound fault may show only as silence)
  S1  F07 + F09, merged bank             RESULT: clean exit after 213 s. In F09's map at 100 /
      (first merged .SND/.WHD/.WAV ever     130 s. 72 sounds, 69 waves, 7 room effects added;
      loaded, S's _LS files installed)      457 references rewritten.
  S2  F07 + M03_FA_A, --no-loc           RESULT: clean exit after 219 s. Dead Men records in the
                                            bank: 216 sounds, 215 waves, 192 in-memory + 23
                                            stream records; 1169 references rewritten. 4649 waves
                                            (stock maximum 4568): no fixed pool hit.
  S3  the same with voice lines          RESULT: clean exit after 230 s. 135 .LOC keys per
                                            language, 4914 sounds / 4778 waves (stock maxima 4806
                                            / 4568). The 7 OnlineSpeakTrigger stay; the level-
                                            start checkpoint that crashed on them (run B-2) passes.
  R1  + ZPlant, ZSHADOWMESHOBJ,          RESULT: clean exit after 225 s. kl_gms.RETYPE is down to
      ZEnvSampler, Multistage kept          ZIngameMapGroup; 44 HavokDeformation stay on the plants.
  M01c F07 + M01_FA_A, tool as in R1     RESULT: clean exit after 201 s (cars kept, bank + voices;
                                            one speech trigger's line has no sound and is cut).
  L1  M03 + kl_light 'stock'             RESULT: clean exit after 221 s. THE PLAYER IS LIT NOW
      (--stock-anm --no-fa)                 (was a black silhouette in R1); palm trunks still
                                            black, the scene still grey. shots/L1_125s.png
  A1  + joined .ANM (--no-fa)            RESULT: clean exit after 217 s. 22.2 MB file, 69 clips
                                            and 13 bones added, Van / Police_USA converted from
                                            Dead Men. First re-serialised .ANM the game loaded.
  F1  + kl_fa (the full tool)            RESULT: clean exit after 217 s. 7 entities of F07's FA
                                            plumbing kept. = THE BUILD IN THE F01 SLOT.
  RD1-RD3  the same build, klauto DLL and klhook/KLHook.round.ini (menu route, re/fa_round.md):
      NO ROUND REACHED. CmdDrop works (boots into KaneAndLynch.gms), scripted keys arrive, 'sel'
      fails safely. But after the press-start page the keys RETURN, RETURN (RD1, RD3) and RETURN,
      DOWN, RETURN (RD2) all start a load of L00 - the story's intro - 0.5 s after the second
      RETURN, and a RETURN in L00 loads L01. No main menu was seen: the menu key sequence is still
      unknown (screen shots of that phase are black). RD1: crash kl2 0x8e5bbd (write to 0) while
      L01 loaded at 47 %, not looked into; RD3 loaded L01 in 155 s without a fault. The save
      file 0.kls was not written (same time stamp as before).
  WK1 the F1 build, direct boot, klauto with only a walk script (W 7 s, D 3, W 8, A 5, W 10, S 6)
      RESULT: clean exit after 225 s, asserts 0, faults 0. The player crosses M03's plaza
      (shots/WK1_118s .. 172s.png): ground collision holds, escalators / shop fronts / parasols
      drawn from every side seen; interiors not reached.
LIVE RUNS 2026-10-09, fourth set (r-live): THE MENU ROUTE AND A REAL ARCADE ROUND (re/fa_round.md 5).
Driver: kl_autotest.py <wait> --shots ... --tag <run>; hook = klauto DLL + the run's ini, both
kept with the log and result in <work>/build/klhook/live/<run>.*; slot = F01.
  OB1 build F1; klauto Hooks=1 (now with window / focus / input logging), [Engine]
      DisableSplashScreens, script ESC + 'focus Button_Heist DOWN'. RESULT: clean exit after 61 s,
      KLHook.result FAIL script line 9 (my focus tracking was wrong, not the game). FOUND: the
      frontend opens MainMenu > CampaignMenu, no press-start page; RETURN there is Story Mode.
      First picture of the main menu (shots/OB1_36s.png).
  RN1 the same DLL with focus tracking by input code 0x7b; route ESC, DOWN, RETURN, RETURN, sel,
      msg StartGame. Every window came up as named; F01 loaded in 99 s (19,828 nodes, 0 asserts).
      RESULT: clean exit after 151 s, KLHook.result EXIT - the process ended 84 ms after the load.
  RN2 + hardware write watch on the quit byte, armed in the menu. RESULT: clean exit after 63 s,
      KLHook.result FAIL stack overflow: Steam's probe 0xa8e3cb jumps to 0 with a debug register set.
  RN3 watch armed at the level load instead. RESULT: clean exit after 157 s, EXIT again 30 ms
      after the load; the quit byte was never written.
  RN4 + wrappers on the import slots of ExitProcess / exit / PostQuitMessage. RESULT: clean exit
      after 170 s; 'END ExitProcess(0x8000dead) called from kl2 00794ed8': the exe's anti-tamper exit.
  RN5 Hooks=0, no [Engine]; engine keys through the command line in memory (CmdAdd); route by
      waitwin only. RESULT: crash kl2.exe+0x4668b after 389 s (ended by hand). THE ROUND STARTED: session game mode
      4, 'FRAGILE ALLIANCE ARCADE - ROUND 1' (shots/RN5_190s.png, RN5_220s.png). One fault, again
      every 0.35 s: divide at kl2 0x44668b on the sound thread = a torn interleaved stream group
      of Dead Men's in the merged .WHD (the briefing line). Fix: stream_groups().
  RN6 the level rebuilt with stream_groups (verify: problems: 0), same hook. RESULT: clean exit
      after 585 s, KLHook.result PASS, asserts 0, faults 0. A WHOLE ROUND: start on the plaza,
      into the bank, 'Looting has started. Trust no-one.', guards shoot, the player dies, 'ROUND
      OVER - All the criminals died', the score page with Buy Weapons / Ready (shots/RN6_*.png).
      = THE BUILD IN THE F01 SLOT.
  DB1 the same build, ORIGINAL hook DLL and KLHook.ini back in place, direct boot.
      RESULT: clean exit after 223 s (the direct-boot test still works).
LIVE RUNS 2026-10-09, fifth set (f-live): THE REST OF A ROUND AND THE LOOK (re/fa_round.md 6, re/lighting.md).
Hook = klauto, Hooks=0, the run's ini in <work>/build/klhook/live/<run>.ini; slot = F01; map M03_FA_A unless said.
  PX1 direct boot, last round's DLL with Hooks=1, a read-only probe from outside. RESULT: clean exit after
      105 s - the process ended 2 frames after the load, ExitProcess from 0x794ed8: the anti-tamper exit
      on a DIRECT BOOT (detours + import wrappers).
  PX2 the same with Hooks=0. RESULT: clean exit after 235 s. Player position found at ZFFPlayer +0x460.
  PX3 + scripted mouse (new). RESULT: clean exit after 227 s. Heading at +0xc14, 0.17 degrees a count.
  GT1 'goto' steering from the start into the hall. RESULT: clean exit after 229 s; 9 s to the hall.
  RN7 real round, route by way points from the navigation mesh, E at cash drawer 06. RESULT: clean exit
      after 251 s (ended by hand). LOOT WORKS: 'Total score: $100,000'. Shot dead 10 s later.
  RN8 + 'onwin' (score page -> label), RETURN = Ready. RESULT: clean exit after 316 s, KLHook.result PASS.
      ROUND 2 STARTS on the same level. E for 1.5 s took no money.
  LK0 direct boot, three fixed views, the build as before. RESULT: clean exit after 216 s.
  LK1 the same views, built with the post filter (now the default). RESULT: clean exit after 227 s.
  LK2 the same, + --ao 0.5 (now the default). RESULT: clean exit after 225 s. Kept: both.
  RN9 test build --m-drop "AI_Enemies!*" (no guards). RESULT: clean exit after 318 s (ended by hand): through
      hall and garage into the yard; the yard's north wall stops the way to the exit box.
  EX1 EX2 EX3 EX4 direct boots on that build, the yard's edges tried by 'goto' (EX4 twice: the first script
      was wrong). RESULT: clean exit after 225 / 228 / 224 / 226 + 223 s. Closed on every side tried.
  RN10 the same build: loot, then 4.5 min in the yard. RESULT: clean exit after 628 s, PASS. $100,000 from
      the drawer, nothing from the garage boxes, no van, THE CLOCK ENDS THE ROUND, score page, round 2.
  RN11 the final build (post filter, AO 0.5, interleave groups in kl_snd.merge). RESULT: crash
      kl2.exe+0x438922 after 209 s: ZLeaderBoardServiceSteam slot 6 reads a null row 0.5 s after the
      score page opened (the sixth time that page came up). Cause not established.
  RN12 RN11 repeated, nothing changed (the reason: does the crash repeat). RESULT: clean exit after 319 s,
      PASS: death, score page, Ready, round 2.
  M01D F07 + M01_FA_A built with the final tool (verify: problems: 0), direct boot, a short walk. RESULT:
      clean exit after 195 s; the diner street with its own post filter (shots/M01D_130s.png).
  DB2 F07 + M03_FA_A final build, ORIGINAL hook DLL and ini, direct boot. RESULT: clean exit after 260 s.
      = THE BUILD IN THE F01 SLOT.
LIVE RUNS 2026-10-09, sixth set (g-live): M02 / M06, ANTI-TAMPER, OWN FOLDER, THE ESCAPE (re/maps.md 11, re/fa_round.md 7).
Rounds: klauto + klslot DLL (<work>/build/klhook/round5), Hooks=0, ini per run in <work>/build/klhook/live.
  M02a F07 + M02_FA_A, ZEnvSampler loaded as ZSTDOBJ (kl_maps --flat), direct boot. RESULT: clean exit after 271 s.
      The mall, lit and textured; the player is shot down at the start.
  M02b the same with the samplers alive. RESULT: crash kl2.exe+0xe5068 after 192 s: a bullet on car glass. The
      .HVK sub-parts name rows of the surface table; Dead Men's 25..31 lie past F07's 24 rows (0x4e5040 has no
      bounds test). Fix: kl_hvk.resurface in DeadMen + a verify test. EVERY Dead Men map had this.
  M02c rebuilt with the fix. RESULT: clean exit after 284 s. The seven env samplers are harmless.
  M06a F07 + M06_FA_A, direct boot. RESULT: clean exit after 231 s. The Japanese garden at night, lanterns lit.
  M06r a real Arcade round on it from the menu (walk, look round, wait). RESULT: clean exit after 617 s, PASS:
      HUD, clock, nobody attacks, the clock ends the round, score page, Ready, round 2.
  M02r the same on F07 + M02_FA_A. RESULT: clean exit after 647 s, PASS.
  X1  bank; + ten import-slot wrappers (klslot's five file ones with [Redirect] F01=DM03, klauto's five exit
      ones). RESULT: clean exit after 243 s, PASS: the round runs. The import table is not checked.
  X2  + data writes (slot name table, a netcode global, written back unchanged); STOCK F01 in the slot, the
      bank only in <DD>/KLExpansion/Maps/DM03. RESULT: clean exit after 238 s, PASS: 'Subway' loads the bank
      from its own folder. THE OWN FOLDER WORKS.
  X3  + only the five detours in unhashed pages. RESULT: clean exit after 240 s, PASS.
  ESC1 bank without guards, with kl_escape's repairs (now in build(): the wall Dead Men's players climb is
      opened). RESULT: crash kl2.exe+0x2a8902 after 332 s. Seen before it: $650,000 (the garage boxes pay),
      through the wall into the exit box, THE VAN IS CALLED AND COMES. The crash: a dropped wallet's
      TriggerBox2 hands the van (ZHavokCar) to the game rules as an actor. Fix: kl_fa.money_people.
  ESC2 + that fix. RESULT: clean exit after 436 s, PASS, but E at the van does nothing: Dead Men's boarding
      action is 'eONLY_KANE'. Fix: kl_fa.boarding (stock form).
  ESC3 + that fix. RESULT: clean exit after 386 s, PASS. A WHOLE ROUND WITH THE ESCAPE: 'You jumped into the
      getaway car', 'All surviving criminals escaped', $723,625 (Escape 50,000 + Loot 650,000 + Time bonus),
      Ready, 'Round: 2'.
  RN13 the FULL build (guards), same script. RESULT: clean exit after 329 s, PASS: shot dead in the garage.
  RN14 the full build, no stops for loot. RESULT: clean exit after 317 s, PASS: dead in the garage again. The
      escape is seen on the no-guards build only; the script cannot fight. = THE BUILD IN THE F01 SLOT (full).
LIVE RUNS 2026-10-09, seventh set (h-live): RETOMOTO TOWER (F07 + M09_B + M09_A with kl_fa_author's layer; re/retomoto_fa.md 9).
Slot F01; direct boots unless said; walks = klauto (round5 DLL, Hooks=0) with 'goto' along the level's own navigation mesh.
  RT1  first build, original hook. RESULT: crash kl2.exe+0x4e5bbd after 22 s: the .prm is read into ONE heap block and
       100.9 MB was refused (HeapAlloc null, header written to 0). Fix: PRM_LIMIT - dead vertex data of S emptied (60.3 MB).
  RT1b rebuilt. RESULT: hung - still running after 421 s, 'Buffering 69 %' from 130 s on.
  RT1c the same with breadcrumbs (Hooks=1) and the stall watchdog. RESULT: clean exit after 179 s, FAIL stall: main thread
       in 0x55f5a0 from ZActor slot 82, first actor's init. nav_join had shifted the children of tree 1, which are
       relative to their polygon's root. Fix in kl_maps.nav_join + a rule in nav_facts (21 stock meshes hold it).
  RT2  rebuilt. RESULT: assert kl2.exe+0x2682c5 after 185 s (and no frame after it): a SECOND FFCoverList - F07's
       Specials!CoverPoints!CoverControl, kept by the layer's 'Specials!'. Fix: kl_fa_author.DROP; verify counts them.
  RT2b rebuilt. RESULT: clean exit after 327 s. THE CHAIN LOADS (200 s to the first frame): the player stands at
       (5650, 20996, -700) at the intact main window - looking OUT (a player group looks along local -Z: look9) - and
       is shot by the boardroom guards every 10 s.
  RT3  test build without the campaign squads (--no-ai), walk start -> boardroom door -> reception -> atrium stairs ->
       elevator lobby -> into the tower car. RESULT: crash kl2.exe+0x4f40c9 after 239 s: the join's JumpPoint got its
       message and 0x8f3fa0 walked the crew of a player that has none. The walk itself: 193 m in 33 s, nothing in the way
       (the boardroom door does not stop the player on a direct boot).
  RT4  the same build and walk, stopping in front of the car; the game's DEBUG jump request written from outside
       (scratch jt.py: gamedata + 0x8d4 = 5, [0x156b358] = 1). RESULT: clean exit after 362 s (ended by hand).
       THE JOIN WORKS THAT WAY: (2721, 19601, 1100) -> (6400, 570, -6254) in the lobby car within 0.25 s; then out of
       the car, down the lobby, through the front entrance, across the square, 150 m up the road to both van stops,
       every way point reached. Road and square are at y -40 / -50 (the tables said 5 / 26).
  RT5  full build, ONE Arcade round from the menu, standing still, ended by 'pass' (no money, the session does not end:
       re/leaderboard.md 4.1). RESULT: clean exit after 307 s, PASS: 'FRAGILE ALLIANCE ARCADE - ROUND 1', countdown, GO,
       HUD, 'Loot area' marker, shot by the guards from the countdown on, 'Killed by: The police', score page $0.
       The START points looked out of the window: a ZSpawnPoint looks along local +Z (rot9), unlike a player group.
  M01W F07 + M01_FA_A built with this tool (verify: problems: 0; kl_fa: 0 CRASH / BROKEN), a walk towards the diner.
       RESULT: clean exit after 252 s; shot twice on the way (MissionFailedReload), no fault.
  RT6  Retomoto final build (spawn points turned, join box without the jump point, road height), one round as RT5.
       RESULT: clean exit after 317 s, PASS: the START point now faces the room (guards in sight during the countdown),
       shot dead 25 s after GO, score page $0. The window's blast was not seen (behind the player).
  DB3  final F07 + M03_FA_A (content equal to the build of RN13 / RN14: all 31 members CRC-equal), ORIGINAL hook.
       RESULT: clean exit after 275 s; the plaza at 150 s (shots/DB3_150s.png). = THE BUILD IN THE F01 SLOT.
LIVE RUNS 2026-10-09, eighth set (i-live, two passes; every run with its outcome: re/fa_round.md 8, re/maps.md 13,
re/retomoto_fa.md 10). Hooks: i-hook's SHIP / TEST builds; a TEST build blocks every Steam write (seen: S2).
  BN0 / BN1, CH0c, CH0d / CH1d  F07 + M03_FA_A before / after the skeleton rebind (kl_chars.reid / rebind after the .ANM
       join), same walk. RESULT: clean exit, PASS, every time: nothing worse, no visible difference at 640 x 480. Kept.
  CH0  the same build. RESULT: clean exit after 494 s, FAIL stall: the window lost focus after 4 frames (no build fault).
  BR1, S1, S5  bank rounds from the menu on the rebind build: PASS, score page, round 2.
  M01R F07 + M01_FA_A, FIRST ARCADE ROUND: PASS after 335 s; street, diner, register, both exits, alive after 2.5 min.
  S2   Retomoto, three lost rounds: the session ENDS, 29 SetStat + StoreStats + UploadLeaderboardScore all BLOCKED.
  J1   Retomoto --no-ai, the hook's jump box inside the tower car. RESULT: hung (901 s): the car's doors are shut.
  J1b, J2, J3, N0, N0b  the box in front of the car (kl_fa_author.JOIN_BOX now): the hook moves the player to the lobby
       car, direct boot and Arcade round; lobby -> entrance -> square -> road -> both van stops. The round ends with
       'Time ran out - You didn't escape' 3 - 5 min in: the van is not boarded by the script's E.
  GW1 / GW2  --guards-wait, and with --blast-delay 9: only the second keeps the countdown free of fire.
  X1j, HK4j, S4tb, J3s, MP1  hook checks (SHIP exit line, fatal fault ended by the hook, stock level allowed, stale
       KLJoin.ini, the expansion's menu page: opens, but the redirect is lost at StartGame).
  DB4  F07 + M03_FA_A with the rebind (build/install, zip sha1 791dbd15), ORIGINAL hook. RESULT: clean exit after
       156 s; the plaza at 100 s (shots/DB4_100s.png). = THE BUILD IN THE F01 SLOT.
BISECT (not needed in the end, but it works): build ... --geometry [--m-add A,B] [--m-drop ..]
  [--s-keep ..] [--s-drop ..], see Select. '--geometry --s-drop *' = M's geometry and no game-mode
  layer at all verifies with 0 problems; plain '--geometry' leaves S's game-mode layer with scene
  paths into S's map that is gone (verify reports them).
"""
import collections, os, shutil, struct, sys, time, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_package, kl_gms, kl_scene, kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_members as MB, kl_hvk, kl_anm, kl_snd
import kl_light, kl_anmjoin, kl_fa
import kl_prpjoin as J
from kl_prp import Prp, units
from kl_port_check import find, workdir, DD_GUESSES, DD_EXE

BESIDE = ('.WHD', '.WAV', '.hti')      # files next to the archive that belong to its members (+ the _LS bank)
SOUND_TYPES = {70: '0x5f7640', 46: '0x6c4230'}   # re/kl2.json type handler index -> its load function
KEYS = 0x4b455953                      # 'SYEK': a key-frame track chunk in a raw data block (keys_tracks)
TAKE = ('CameraFar', 'CameraFogBegin', 'CameraFogFull', 'CameraFogMin', 'CameraBackgroundColor',
        'SSAO_Blur', 'SSAO_Strength')  # scene properties that describe the map
LANGS = kl_package.LANGS
PRM_LIMIT = 90000000                   # a joined .prm larger than this loses S's dead vertex data (build(); run RT1)
STAMP = (2010, 8, 17, 12, 0, 0)        # time stamp of every archive member (write_zip): a constant, any valid date
LOAD = {'stamp': True, 'level': 1, 'stored': False, 'trim': False, 'slim': False, 'fxc': False, 'wav': False}   # load_options() defaults


# ------------------------------------------------------------------ files in and out
def out_dir(slot):
    # KL_GRAFT_OUT: another build folder (a variant to compare; 'install' then installs that one)
    d = os.path.join(os.environ.get('KL_GRAFT_OUT') or os.path.join(workdir(), 'build', 'install'), 'Scenes', 'Locations', slot)
    os.makedirs(d, exist_ok=True)
    return d


def stock_beside(level, ext):
    """Stock <level>_Main<ext> next to the archive; a file moved to KL_PortBackup wins."""
    dd = find(DD_GUESSES, DD_EXE)
    for root in (os.path.join(dd, kl_package.BACKUP), dd):
        p = os.path.join(root, 'Scenes', 'Locations', level, level + '_Main' + ext)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(level + '_Main' + ext)


def member_name(name, level, slot):
    """Archive member of `level` under the slot's name (the UI .xml members have no level name)."""
    return name.replace('Locations/%s/%s_Main' % (level, level), 'Locations/%s/%s_Main' % (slot, slot))


def beside_of(level):
    """{suffix: path} of the stock files next to a level's archive: BESIDE and its loading-sound
    bank (_LS.SND, _LS_<Language>.WHD / .WAV). The _LS objects point into the level's own .SND,
    so a slot that runs S's bank needs S's _LS files, not the slot's."""
    out = {e: stock_beside(level, e) for e in BESIDE}
    out.update(kl_snd.ls_files(level))
    return out


def write_zip(path, members, opt=None):
    """members: [(member name, bytes)] in archive order -> the archive, packed as load_options() says.
    Every member carries the same fixed time stamp (STAMP), so two builds with equal members are equal
    files (before 2026-10-09 18:00 the build time was stamped in; 'stamp=now' gives that back).
    Method and order are what stock has: deflate, the directory in physical order. 'stored' writes
    members without compression. 'stored': the 45 stock archives use method 0 only for members of up
    to 32 bytes, but the reader (kl2 0x593010) takes a method-0 member of ANY size as one plain read,
    while method 8 is inflated on the loading thread in 128 KB chunks with the keep-alive pump after
    each (re/loading.md 4, read 2026-10-23). Still NOT run in the game, so not the default."""
    opt = opt or load_options()
    stamp = STAMP if opt['stamp'] else time.localtime()[:6]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=opt['level']) as z:
        for name, data in members:
            zi = zipfile.ZipInfo(name, stamp)
            zi.external_attr = 0o600 << 16              # what writestr(name, data) put there
            if opt['stored']:
                z.writestr(zi, data, zipfile.ZIP_STORED)
            else:
                z.writestr(zi, data, zipfile.ZIP_DEFLATED, opt['level'])
    return path


def write_level(slot, members, beside, log=print, opt=None):
    """members: [(member name, bytes)] in archive order; beside: {suffix: source path or bytes},
    written as <slot>_Main<suffix> (kl_snd.Audio.beside has that form). opt: load_options()."""
    d = out_dir(slot)
    path = write_zip(os.path.join(d, slot + '_Main.zip'), members, opt)
    for f in os.listdir(d):                             # nothing of an earlier build stays
        if f.startswith(slot + '_Main') and f != slot + '_Main.zip':
            os.remove(os.path.join(d, f))
    for suffix, v in beside.items():
        if isinstance(v, bytes):
            with open(os.path.join(d, slot + '_Main' + suffix), 'wb') as f:
                f.write(v)
        else:
            shutil.copyfile(v, os.path.join(d, slot + '_Main' + suffix))
    log('built %s, %.0f MB, %d members' % (path, os.path.getsize(path) / 1e6, len(members)))
    return path


def plain(level, slot='F01', log=print):
    """Stock `level` with nothing changed but the member names: what a healthy level looks like
    through the unattended launcher, and the proof that renaming alone is harmless. No member
    of F02 or F04 holds its own file name (searched 2026-10-09)."""
    with zipfile.ZipFile(J.level_zip(level)) as z:
        members = [(member_name(n, level, slot), z.read(n)) for n in z.namelist()]
    return write_level(slot, members, beside_of(level), log)


def install(slot='F01', log=print, src=None):
    """Copy the built archive and the files beside it into Dog Days' slot. Each stock file is
    moved to KL_PortBackup the first time (kl_package._backup_then_copy), never overwritten.
    src: a folder holding a kept build (<slot>_Main.zip and the files beside it, e.g. one of
    kl_maps.py deliver) instead of the last build.
    KLJoin.ini (the hook's jump boxes of a two-part map, klhook/kljoin.c reads it beside the
    archive) is ours, never a stock file: it is copied when the build's folder has one and
    REMOVED from the slot when it has none, so that Retomoto's file does not stay beside the bank
    (the hook refuses a stale box by its Name / Target, but the file is clutter)."""
    dd, d = find(DD_GUESSES, DD_EXE), src or out_dir(slot)
    if not os.path.isfile(os.path.join(d, slot + '_Main.zip')):
        raise FileNotFoundError(os.path.join(d, slot + '_Main.zip'))
    for f in sorted(f for f in os.listdir(d) if f.startswith(slot + '_Main')):      # archive, BESIDE, _LS bank
        kl_package._backup_then_copy(dd, os.path.join('Scenes', 'Locations', slot, f), os.path.join(d, f))
    join = os.path.join(dd, 'Scenes', 'Locations', slot, 'KLJoin.ini')
    if os.path.isfile(os.path.join(d, 'KLJoin.ini')):
        shutil.copyfile(os.path.join(d, 'KLJoin.ini'), join)
        log('installed %s' % os.path.relpath(join, dd))
    elif os.path.isfile(join):
        os.remove(join)
        log('removed %s (this build has no jump box)' % os.path.relpath(join, dd))


# ------------------------------------------------------------------ loading weight (re/loading.md)
def load_options(spec=None):
    """The packing / weight options of a build as a dict (defaults: LOAD). spec: 'trim,slim,level=6',
    a dict, or None = the environment variable KL_GRAFT_LOAD (so that kl_maps / kl_fa_author builds
    take them without a new argument). Names:
      trim       the .prm's vertex and index data that no root of the joined level reaches -> 16-byte
                 stubs, ALWAYS (without it only past PRM_LIMIT). Chunk indices stay. Loaded live in
                 every Retomoto build (the PRM_LIMIT path); the bank never ran with it.
      slim       the .TEX's pictures that only S's dead map models show -> their smallest mip levels
                 (4 x 4 and below). Ids, names, formats and the material file stay. NOT LOADED LIVE.
      fxc        the shader cache without the entries no material of the level asks for
                 (kl_light.slim_cache: what every stock level's cache is). Use it on the FINISHED build
                 ('lighten'), after the wardrobe and props: they add materials. NOT LOADED LIVE.
      wav        the in-memory sound bank beside the archive without the clips nothing in the level
                 can play (kl_wavslim: S's map sounds under SFX/Environment, 10 MB on Retomoto; the
                 .WHD keeps every record, the .SND is not touched). 'lighten' only. NOT LOADED LIVE.
      stored     archive members uncompressed (write_zip: an ASSUMPTION about the reader).
      level=N    deflate level 1..9 (1 = what the builds had so far).
      stamp=now  the build time as the members' time stamp (default: the constant STAMP)."""
    opt = dict(LOAD)
    if spec is None:
        spec = os.environ.get('KL_GRAFT_LOAD', '')
    if isinstance(spec, dict):
        spec = ','.join('%s=%s' % kv for kv in spec.items())
    for w in filter(None, (x.strip() for x in spec.replace(' ', ',').split(','))):
        k, _eq, v = w.partition('=')
        if k not in opt:
            raise ValueError('unknown load option %r (known: %s)' % (k, ', '.join(sorted(opt))))
        if k == 'level':
            opt[k] = int(v)
            if not 1 <= opt[k] <= 9:
                raise ValueError('deflate level %s' % v)
        elif k == 'stamp':
            opt[k] = v.lower() not in ('now', '0', 'false', 'off', 'no')
        else:
            opt[k] = v.lower() not in ('0', 'false', 'off', 'no')
    return opt


def live_roots(sc, gms_models):
    """Every .prm chunk the level's own files name: sc = the level's kl_prpjoin.Scene (ZGEOM[4],
    ZWINPIC[2], fonts, cloth, the scene block), gms_models = the .gms records' chunk indices."""
    return ([(c, k) if k else c for _w, c, k in G.prp_roots(sc.p, sc.tids, J.schema('dd'), 'dd')] +
            [m for m in gms_models if m])


def hud_textures(sc):
    """.TEX ids the HUD names directly: ZOnScreenDisplay2[7], 200 ids per object (kl_texmat docstring).
    No material stands between them and the .TEX, so dead_assets() has to be told."""
    out = set()
    for k in range(1, len(sc.nodes)):
        cls = sc.cls(k)
        if cls and 'ZOnScreenDisplay2[7]' in labels(cls):
            unit = units(sc.nodes[k]['props'][1:-1])[labels(cls).index('ZOnScreenDisplay2[7]')]
            out.update(v for v in (u32(t) for t in unit if len(t[1]) == 4) if 0 < v < G.SLOTS['dd'])
    return out


def dead_assets(prm, mat, tex, live, hud=()):
    """What of a joined level only S's removed map still holds.
    prm: kl_prmgraph.Prm, mat / tex: kl_texmat models, live: live_roots(), hud: hud_textures().
    -> {'reached': {chunk: kind} from the live roots,
        'data': chunks of vertex / index data that only dead model roots reach (kl_prmgraph.orphans:
                a dead root is found by its shape),
        'slots': material slots that a dead mesh uses and no live one,
        'tex': texture ids whose EVERY known user is dead}.
    A texture is in 'tex' only if a dead material or a dead sprite names it AND nothing else does:
    every material that is not in 'slots' counts as a user (also those no mesh names at all - the
    effect system and the HUD reach materials in ways this file does not follow), so do the live
    chunks' own texture fields, the HUD list, and the frame lists of what stays. The about 24 UI /
    font textures per level without a known user (kl_texmat) are therefore never in it.
    ASSUMPTION: no code path picks a material BY SLOT that the level's files name only on S's map
    meshes (e.g. a decal shared with a map prop). If one does, the picture is a 4 x 4 blur, not a
    crash: the texture still exists under its id."""
    obj = ('mesh', 'scatter', 'water')

    def named(kinds, args):
        slots, ids = set(), set()
        for i, k in kinds.items():
            if k in obj:
                slots.add(prm.u16(i, 0x12))
            for off, typ, _k in G.fields(prm, i, k, args.get(i, 0)):
                if typ in ('t', 'T') and prm.u32(i, off):
                    ids.add(prm.u32(i, off) % G.SLOTS['dd'])
        return slots, ids

    reached, args = G.walk(prm, live)
    roots = [i for i, l in G.orphans(prm, reached).items() if l == 'dead root']
    try:
        dk, da = G.walk(prm, [(i, 'root') for i in roots])
    except ValueError:                                  # a dead root that does not walk: nothing is called dead
        dk, da = {}, {}
    dk = {i: k for i, k in dk.items() if i not in reached}
    live_slots, live_ids = named(reached, args)
    dead_slots, dead_ids = named(dk, da)
    dead_slots = {s for s in dead_slots - live_slots if s in mat.insts}
    keep = T.used_textures(mat, [s for s in mat.insts if s not in dead_slots]) | live_ids | set(hud)
    keep = T.texture_closure(tex, [i for i in keep if i in tex.tex])
    cand = T.texture_closure(tex, [i for i in T.used_textures(mat, dead_slots) | dead_ids if i in tex.tex])
    return {'reached': reached, 'roots': roots,
            'data': sorted(i for i, k in dk.items() if k in ('vtx', 'idx') and len(prm.chunks[i]) > 16),
            'slots': dead_slots, 'tex': sorted(cand - keep)}


def mip_levels(entry):
    """[(offset of the level's u32 size, size)] of a .TEX record, or None when the record is not
    header + name + <mips> x (u32 n, n bytes) to its last byte (then it is left alone)."""
    mips = struct.unpack_from('<I', entry, 20)[0]
    p, out = entry.index(b'\0', 36) + 1, []
    for _k in range(mips):
        if p + 4 > len(entry):
            return None
        n = struct.unpack_from('<I', entry, p)[0]
        out.append((p, n)); p += 4 + n
    return out if out and p == len(entry) else None


def small_texture(x, least=4):
    """The texture with only its mip levels of `least` pixels and less on the shorter side - the
    tail of its own chain, so format, name, id, flags and the bytes of those levels are the file's
    own. `least` = 4: a block-compressed top level smaller than one 4 x 4 block is something no
    stock texture was checked for. None = not shrunk (cube map, animated, one level, already small,
    or a record mip_levels() does not read)."""
    if x.faces is not None or x.frames is not None or x.flags & (T.CUBE | T.ANIMATED):
        return None
    e = x.entry
    h, w = struct.unpack_from('<HH', e, 16)
    lv = mip_levels(e)
    if not lv or len(lv) < 2:
        return None
    k = max((j for j in range(len(lv)) if min(max(1, w >> j), max(1, h >> j)) >= least), default=0)
    if k == 0:
        return None
    body = e[4:lv[0][0]] + e[lv[k][0]:]
    out = bytearray(struct.pack('<I', 4 + len(body)) + body)
    struct.pack_into('<HHI', out, 16, max(1, h >> k), max(1, w >> k), len(lv) - k)
    return T.Texture(bytes(out), None, None, None, x.group)


def lighten(prm_bytes, tex_bytes, mat_bytes, live, hud, opt, log=print):
    """Apply 'trim' and 'slim' (load_options) to the written members -> (.prm, .TEX, report).
    Nothing is renumbered and nothing the live roots reach changes: that is checked here (every
    reached chunk byte-equal, the .MAT ref table the .prm implies unchanged, the .TEX re-read)."""
    prm, tex, mat = G.read(prm_bytes, 'dd'), T.read_tex(tex_bytes), T.read_mat(mat_bytes)
    d = dead_assets(prm, mat, tex, live, hud)
    rep = {'prm before': len(prm_bytes), 'tex before': len(tex_bytes), 'dead roots': len(d['roots']),
           'dead data chunks': len(d['data']), 'dead data bytes': sum(len(prm.chunks[i]) for i in d['data']),
           'dead materials': len(d['slots']), 'dead textures': len(d['tex']),
           'dead texture bytes': sum(len(tex.tex[i].entry) for i in d['tex']), 'textures': len(tex.tex)}
    new_prm, new_tex = prm_bytes, tex_bytes
    if opt['trim'] and d['data']:
        before = {i: prm.chunks[i] for i in d['reached']}
        for i in d['data']:
            prm.chunks[i] = bytes(16)
        new_prm = G.write(prm)
        if any(prm.chunks[i] != c for i, c in before.items()) or G.walk(G.read(new_prm, 'dd'), live)[0] != d['reached']:
            raise ValueError('trim changed something the level reaches')
        if T.material_refs(new_prm) != T.material_refs(prm_bytes):
            raise ValueError('trim changed the material reference counts')
    if opt['slim'] and d['tex']:
        shrunk = 0
        for i in d['tex']:
            s = small_texture(tex.tex[i])
            if s is not None:
                tex.tex[i] = s; shrunk += 1
        new_tex = T.write_tex(tex)
        back = T.read_tex(new_tex)
        if set(back.tex) != set(T.read_tex(tex_bytes).tex) or T.write_tex(back) != new_tex:
            raise ValueError('slim changed the texture ids or the .TEX does not round-trip')
        rep['textures shrunk'] = shrunk
    rep['prm after'], rep['tex after'] = len(new_prm), len(new_tex)
    log('  load weight: %d dead model roots; .prm %.1f -> %.1f MB (%d dead vertex / index chunks, %s); '
        '.TEX %.1f -> %.1f MB (%d of %d textures only dead materials name, %.1f MB, %s)' % (
            rep['dead roots'], len(prm_bytes) / 1e6, len(new_prm) / 1e6, len(d['data']), 'emptied' if opt['trim'] else 'kept: no trim',
            len(tex_bytes) / 1e6, len(new_tex) / 1e6, len(d['tex']), len(tex.tex), rep['dead texture bytes'] / 1e6,
            '%d shrunk to 4 x 4' % rep.get('textures shrunk', 0) if opt['slim'] else 'kept: no slim'))
    return new_prm, new_tex, rep


def open_built(path):
    """A built (or stock) Dog Days level archive read for lighten() / kl_loadtime: (member names in
    order, {name: bytes}, {'.prm': name ...}, kl_prpjoin.Scene, live_roots, hud_textures)."""
    with zipfile.ZipFile(path) as z:
        order = z.namelist()
        files = {n: z.read(n) for n in order}
    ext = {n.rsplit('_Main', 1)[1]: n for n in order if '_Main' in n}
    raw, buf = kl_gms.unpack(files[ext['.gms']]), files[ext['.buf']]
    import kl_rtp
    names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
    for decl, tid, _prio in kl_gms.entities(raw):       # as kl_prpjoin.Scene.load
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
    sc = J.Scene(Prp(files[ext['.prp']]), names, tids, 'dd', os.path.basename(path))
    # a wardrobe's Dead Men roots are named by no entity (KLWardrobe.ini lists them): without this
    # 'lighten' would empty them as dead (re/prm_limit.md)
    import kl_chars
    extra = [(r, 'root') for r in kl_chars.wardrobe_roots(os.path.join(os.path.dirname(path), 'KLWardrobe.ini'))]
    return order, files, ext, sc, live_roots(sc, G.gms_roots(raw)) + extra, hud_textures(sc)


def relight(src, dst, opt=None, log=print):
    """A built level (folder with <slot>_Main.zip, or the archive) repacked into folder `dst` with
    the load options applied - the way to weigh an option on a build that exists, and to make a
    lighter copy of a delivered one ('install --from <dst>'). Files beside the archive are copied.
    -> (path, report)."""
    opt = opt or load_options()
    zp = src if src.lower().endswith('.zip') else next(os.path.join(src, f) for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip'))
    order, files, ext, _sc, live, hud = open_built(zp)
    rep = {}
    if opt['trim'] or opt['slim']:
        files[ext['.prm']], files[ext['.TEX']], rep = lighten(files[ext['.prm']], files[ext['.TEX']], files[ext['.MAT']], live, hud, opt, log)
    if opt['fxc']:
        import kl_light
        files[ext['.fxc']], frep = kl_light.slim_cache(T.read_mat(files[ext['.MAT']]), files[ext['.fxc']], log)
        rep.update({'fxc ' + k: v for k, v in frep.items()})
    os.makedirs(dst, exist_ok=True)
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('relight: the output folder is the build\'s own')
    out = write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order], opt)
    for f in os.listdir(os.path.dirname(zp)):
        p = os.path.join(os.path.dirname(zp), f)
        if os.path.isfile(p) and p != zp:
            shutil.copyfile(p, os.path.join(dst, f))
    if opt['wav'] and os.path.isfile(zp[:-4] + '.WAV'):
        import kl_wavslim
        whd0, wav0 = open(zp[:-4] + '.WHD', 'rb').read(), open(zp[:-4] + '.WAV', 'rb').read()
        whd1, wav1, wrep = kl_wavslim.slim(_sc, files[ext['.SND']], files[ext['English.LOC']], whd0, wav0, log)
        bad = kl_wavslim.check(whd0, wav0, whd1, wav1)
        if bad:
            raise ValueError('kl_wavslim: ' + '; '.join(bad[:5]))
        open(out[:-4] + '.WHD', 'wb').write(whd1); open(out[:-4] + '.WAV', 'wb').write(wav1)
        rep.update({'wav ' + k: v for k, v in wrep.items()})
    rep.update({'zip before': os.path.getsize(zp), 'zip after': os.path.getsize(out)})
    log('repacked %s: %.1f -> %.1f MB (%s)' % (out, rep['zip before'] / 1e6, rep['zip after'] / 1e6,
                                             ', '.join('%s=%s' % kv for kv in sorted(opt.items()))))
    return out, rep


class Level:
    """One stock Dog Days level: its members, property tree (kl_prpjoin.Scene) and scene
    (kl_scene.Scene). ents[k - 1] is the entity of .prp node k."""

    def __init__(self, name):
        self.name = name
        with zipfile.ZipFile(J.level_zip(name)) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}   # '.gms', 'English.LOC'
        self.prp = J.Scene.load(name)
        self.scene = kl_scene.Scene(kl_gms.unpack(self[".gms"]), self['.buf'])
        self.ents = list(self.scene.entities())
        if [e.name.decode('latin1') for e in self.ents] != self.prp.names[1:]:
            raise ValueError('%s: .gms and .prp disagree on the entities' % name)
        self.slot0 = self.scene.slots()                 # before any edit
        self.side = J.sides(self.prp)
        self.dm = False

    def __getitem__(self, ext):
        return self.files[self.ext[ext]]


class DeadMen(Level):
    """A Dead Men level presented in Dog Days form, with the converters as they are today:
    .prp kl_convert (schema-driven; pairings marked 'assumed' there), classes kl_gms.RETYPE,
    navigation mesh kl_pf4, gates 0x38 -> 0x74 (kl_rooms.dd_gate) appended to the .buf head,
    .prm / .TEX / .MAT kl_prm / kl_tex / kl_mat. Chunk indices, REF ids, slot ids, .buf offsets
    and texture / material ids are still Dead Men's own: build() renumbers them like any M.
    NOT converted (copied, ASSUMPTION that Dog Days reads them alike): entity flags and raw data
    blocks (KEYS, light curves), .sgd octrees, .sgp, .hrd, FDX block.
    Dead Men's 'CoverList' (a top-level list with FFCoverList) is counted as map: Dog Days keeps
    its own under Specials!CoverPoints!, which leaves with S's map."""

    def __init__(self, name, log=print, ao=0.0):
        import kl_convert as K, kl_pf4, kl_rooms, kl_prm, kl_mat, kl_tex
        self.name, self.dm = name, True
        with zipfile.ZipFile(J.level_zip(name, 'dm')) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
        src = J.Scene.load(name, 'dm')
        self.side = J.sides(src)
        for k in range(1, len(src.nodes)):
            if src.names[src.top[k]] == 'CoverList':
                self.side[k] = 'map'
        raw = kl_gms.unpack(self['.gms'])
        conv = K.converter(find(DD_GUESSES, DD_EXE), workdir())
        data, st = K.convert_level(self['.prp'], conv, src.tids)
        tids = [src.tids[0]] + [K.RETYPE.get(t, t) for t in src.tids[1:]]
        self.prp = J.Scene(Prp(data), src.names, tids, 'dd', name)
        # A controller written for the class a node WAS: HavokCarScriptRout on a ZHavokCar that
        # kl_gms.RETYPE made a ZSTDOBJ walks the car's wheel list at object +0x96c, far behind a
        # ZSTDOBJ (crash kl2 0x58a7fc right after the load, run B1). Such controllers go.
        sch, cut = J.schema('dd'), collections.Counter()
        for k in range(1, len(tids)):
            if tids[k] != src.tids[k]:
                node, chain = self.prp.nodes[k], sch.bases(sch.geoms[src.tids[k]]) if src.tids[k] in sch.geoms else None
                keep = []
                for nm, body in node['ctrls']:
                    owners = [e[0] for e in sch.controllers.get(self.prp.p.key(nm), [])]
                    if chain and owners and not set(owners) & set(sch.bases(self.prp.cls(k))) and set(owners) & set(chain):
                        cut[self.prp.p.key(nm)] += 1
                    else:
                        keep.append((nm, body))
                node['ctrls'] = keep
        if cut:
            log('%s: controllers of retyped nodes removed: %s' % (name, dict(cut)))
        sc = kl_scene.Scene(raw, self['.buf'])
        self.slot0 = sc.slots()
        for e in sc.entities():
            e.tid = K.RETYPE.get(e.tid, e.tid)
        if sc.slots() != self.slot0:
            raise ValueError('a retype in kl_gms.RETYPE moves entities to another pool: slot ids would be stale')
        sc.game = 'dd'
        if sc.nav is not None:
            sc.nav = kl_pf4.convert(sc.nav)
        self.scene, self.ents = sc, list(sc.entities())
        ngates = 0
        for k, node in enumerate(self.prp.nodes):       # gate arrays in Dog Days' record size
            lab = labels(self.prp.cls(k))
            if 'ZROOM[9]' not in lab:
                continue
            def fn(us):
                nonlocal ngates
                n, off = u32(us[lab.index('ZROOM[0]')][0]), u32(us[lab.index('ZROOM[9]')][0])
                us[lab.index('ZROOM[2]')] = [(0x09, bytes(4))]      # as kl_rooms.convert_gates (ASSUMPTION there)
                if n:
                    if off + 0x38 * n > len(sc.head):
                        raise ValueError('room gates lie outside the .buf head')
                    sc.head += bytes(-len(sc.head) % 16)
                    us[lab.index('ZROOM[9]')] = [(0x09, struct.pack('<I', len(sc.head)))]
                    sc.head += b''.join(kl_rooms.dd_gate(sc.head[off + 0x38 * i:off + 0x38 * i + 0x38]) for i in range(n))
                    ngates += n
            edit(node, 'props', fn)
        roots = [c for c in G.gms_roots(raw) if c] + [(c, k) if k else c for _w, c, k in G.prp_roots(src.p, src.tids, J.schema('dm'), 'dm')]
        dm_prm = self['.prm']
        self.files[self.ext['.prm']], rep = kl_prm.convert(dm_prm, roots)
        if ao:                                          # re/lighting.md second pass, step 3 (reads Dead Men's .TEX)
            self.files[self.ext['.prm']], arep = kl_light.bake_ao(dm_prm, self['.prm'], roots, self['.TEX'], strength=ao, log=log)
            log('%s: light map baked at strength %g: %s' % (name, ao, {k: v for k, v in arep.items() if not isinstance(v, (list, dict))}))
        # as kl_dmassets.convert_level: the .MAT's use counts and surface numbers follow the
        # CONVERTED .prm and Dog Days' surface table (the graft keeps S's .buf tail)
        tex_ids = set(T.read_tex(self['.TEX']).tex)
        self.files[self.ext['.TEX']] = kl_tex.convert(self['.TEX'])[0]
        self.files[self.ext['.MAT']] = kl_mat.convert_mat_full(self['.MAT'], prm=self['.prm'], surface='dd',
                                                               texture_ids=tex_ids)[0]
        # .HVK sub-parts name rows of the surface table too (kl_hvk.resurface): the same map as the
        # .MAT's, 14 of its rows GUESSES by meaning (kl_mat.SURFACE_GUESS: CarGlass -> Glass ...)
        self.files[self.ext['.HVK']], srep = kl_hvk.resurface(self['.HVK'], {k: v[0] for k, v in kl_mat.surface_map().items()})
        log('%s converted: %s; %d gates; .prm %s; .HVK surfaces %s' % (name, dict(st), ngates, {k: v for k, v in rep.items() if v and not isinstance(v, list)},
                                                                      {'%d>%d' % k: v for k, v in sorted(srep.items())}))


GEOMETRY = ('Locations/*', 'CloneGroup_Locations')      # + anything with 'Backdrop' in its name


def geometry(name):
    return J.family(name) in GEOMETRY or 'backdrop' in name.lower()


class Select:
    """Which top-level MAP subtrees go into the graft (systems subtrees are always S's).
    Default: all of M's, none of S's. geometry: of M only the geometry, and S keeps its own
    game-mode layer (FASpecials!, Gameplay!, Specials!, Animation/...), which then stands in M's
    geometry at S's coordinates. The four pattern lists then adjust that, one bisect step per
    command; a pattern is matched (fnmatch, case-insensitive) against the subtree's name and its
    kl_prpjoin.family ('Settings!', 'Locations/*', 'CloneGroup_Effects' ...):
      m_add   M's subtrees taken although geometry-only would leave them out
      m_drop  M's subtrees left out
      s_keep  S's map subtrees kept
      s_drop  S's map subtrees left out although geometry-only would keep them"""

    def __init__(self, geometry=False, m_add=(), m_drop=(), s_keep=(), s_drop=()):
        self.geometry, self.m_add, self.m_drop, self.s_keep, self.s_drop = geometry, m_add, m_drop, s_keep, s_drop

    @staticmethod
    def match(name, pats):
        import fnmatch
        return any(fnmatch.fnmatch(x.lower(), p.lower()) for p in pats for x in (name, J.family(name)))

    def m(self, name):
        return (not self.geometry or geometry(name) or self.match(name, self.m_add)) and not self.match(name, self.m_drop)

    def s(self, name):
        return ((self.geometry and not geometry(name)) or self.match(name, self.s_keep)) and not self.match(name, self.s_drop)

    def __str__(self):
        return ' '.join(['--geometry'] * self.geometry + ['--%s %s' % (k.replace('_', '-'), ','.join(v)) for k, v in
                        (('m_add', self.m_add), ('m_drop', self.m_drop), ('s_keep', self.s_keep), ('s_drop', self.s_drop)) if v]) or 'whole map'


def picks_of(S, M, sel=None):
    """kl_prpjoin.graft_picks with each level's own sides: M's top-level order, its map subtrees
    kept, each systems subtree replaced by S's of the same name; S's other systems subtrees go in
    before the closing systems objects. A MAP subtree of M with the name of a systems subtree of
    S also gives way to S's (Dead Men M01 keeps bullet-impact effects, and so their clone groups,
    inside the map: two top-level subtrees of one name would make every path to them ambiguous;
    no pair of Dog Days levels has such a name). -> (picks, names of M left out).
    sel (Select) narrows M's map subtrees and keeps map subtrees of S: the bisect of a crash."""
    sel = sel or Select()
    def owner(lv, t):
        """The name the selection goes by: a clone group follows the subtree of its template
        (M01's Locations hold ZAllocMany templates whose groups are CloneGroup_Effects/...)."""
        if lv not in tpl:
            tpl[lv] = J.templates(lv.prp)
        return lv.prp.names[lv.prp.top[tpl[lv][t]]] if t in tpl[lv] else lv.prp.names[t]
    tpl = {}
    mine = {}
    for t in S.prp.tops():
        if S.side[t] == 'systems':
            mine.setdefault(S.prp.names[t], []).append(t)
    out, dropped, seen = [], [], set()
    for t in M.prp.tops():
        if mine.get(M.prp.names[t]):
            out.append((S.prp, mine[M.prp.names[t]].pop(0)))
            if M.side[t] == 'map':
                dropped.append(M.prp.names[t])
        elif M.side[t] == 'map' and sel.m(owner(M, t)) and M.prp.names[t] not in seen:
            # a name M itself brings twice (Dead Men M03: one car-explosion clone group) is taken
            # once: paths to the second could not be told apart from paths to the first anyway
            seen.add(M.prp.names[t])
            out.append((M.prp, t))
        else:
            dropped.append(M.prp.names[t])
    taken = {M.prp.names[t] for sc, t in out if sc is M.prp}
    out += [(S.prp, t) for t in S.prp.tops() if S.side[t] == 'map' and sel.s(owner(S, t)) and S.prp.names[t] not in taken]
    rest = sorted(t for ts in mine.values() for t in ts)
    at = next((i for i, (sc, t) in enumerate(out) if sc is S.prp and S.prp.names[t] in ('TrackLinkObjects', 'ZParticleController')), len(out))
    return out[:at] + [(S.prp, t) for t in rest] + out[at:], dropped


# ------------------------------------------------------------------ small helpers
def u32(tok):
    return struct.unpack('<I', tok[1])[0]


def labels(cls):
    return J.labels('dd', cls)


def objects(sc, k):
    """(class, object holder, key) of node k and of its controllers the game registers; the
    object's tokens are holder[key]."""
    n, cls = sc.nodes[k], sc.cls(k)
    out = [(cls, n, 'props')]
    for i, (nm, _body) in enumerate(n['ctrls']):
        impl = J.schema('dd').controller(sc.p.key(nm), cls)
        if impl:
            out.append((impl, n['ctrls'], i))
    return out


def get_obj(holder, key):
    return holder[key] if key == 'props' else holder[key][1]


def set_obj(holder, key, toks):
    if key == 'props':
        holder[key] = toks
    else:
        holder[key] = (holder[key][0], toks)


def edit(holder, key, fn):
    """Run fn(list of field units) on an object and store the result."""
    obj = get_obj(holder, key)
    us = [list(u) for u in units(obj[1:-1])]
    fn(us)
    set_obj(holder, key, [obj[0]] + [t for u in us for t in u] + [obj[-1]])


def is_room(tid):
    sch = J.schema('dd')
    return 'ZROOM' in sch.bases(sch.geoms.get(tid, ''))


def rooms_of(scene):
    """(entities, room_order as entities with None for the root) of a kl_scene.Scene."""
    ents = list(scene.entities())
    idx = {e: i for i, e in enumerate(ents)}
    order = O.room_order([idx[e.parent] if e.parent else -1 for e in ents], [is_room(e.tid) for e in ents])
    return ents, [None if i < 0 else ents[i] for i in order]


def keys_tracks(raw):
    """[(position in the raw data block, the six .buf offsets)] of every KEYS chunk in it.
    A chunk is 'SYEK', its size 0x30, key count, 0, count - 1, 1 and six .buf offsets at +0x18
    (reader kl2 0x422c50: [chunk + 0x18 + 0x10 .. 0x24] + .buf base). Mostly it is the whole of a
    64-byte block (chunk at +0x10), but a camera or a light with several animated parameters
    carries it at the end of a longer block: M01's AnimatedRumbleCamera (2804 bytes, chunk at
    +0xaa0), stock F01's too, lights in L02 / L04 / L05. Missing those left the track offsets
    unshifted: crash kl2 0x81e714 (bit-packed key index read far outside the .buf)."""
    out = []
    if raw is not None:
        for p in range(0, len(raw) - 0x2c, 4):
            if struct.unpack_from('<II', raw, p) == (KEYS, 0x30):
                out.append((p + 0x18, struct.unpack_from('<6I', raw, p + 0x18)))
    return out


def mute_speech(sc, ctrl, snd):
    """True for an OnlineSpeakTrigger controller whose line the level's .SND does not hold.
    ZOnlineSpeakTrigger's init (kl2 0x4eae60, vtable 0xbc98fc slot 13) looks its line up by name
    (0x828fa0; the bank lists it as 'audio:dialog/<name, lower case>#sound') and, when that
    fails, deletes itself through slot 30 - but it has already been entered in the save-state
    table at 0xe09e38, which has no 'unregister'. The level-start checkpoint (0x65a4d0) then
    calls slot 21 of the freed object: nine such triggers of M01_FA_A (AI_Enemies!, Civilians!)
    were the jump into ZFFGameData+0x3e3c at Buffering 99 % (seen live 2026-10-09: the nine
    table entries go ZOnlineSpeakTrigger -> ZSerializable -> freed within a second).
    The line is the object's first string (F06's only stock trigger: Multiplayer/F06/
    Chopper_response_R, and its bank has audio:dialog/multiplayer/f06/chopper_response_r#sound)."""
    nm, body = ctrl
    if sc.p.key(nm) != 'OnlineSpeakTrigger':
        return False
    line = next((sc.p.key(t) for t in body if t[0] == 0x0c), '')
    return ('audio:dialog/%s#sound' % line.lower()).encode('latin1') not in snd.lower()


ANIM_FALLBACK = {'Police': 'Swat_02', 'Army': 'Swat_02'}


def campaign_rename(Jn):
    """{string: string}: scene paths into a Dog Days campaign level's systems zip (AllLevels/
    mainsceneincludes.zip) get the multiplayer zip's name, the systems S brings."""
    old, new = 'ROOT\\AllLevels/mainsceneincludes.zip', 'ROOT\\AllLevels/mainsceneincludes_multiplayer.zip'
    return {s: new + s[len(old):] for s in Jn.p.keys if s.lower().startswith(old.lower() + '\\')}


def dm_rename(Jn, S, log=print, anim=True, arms=True):
    """{string: string} for a Dead Men map under Dog Days systems: scene paths into Dead Men's
    systems subtree get Dog Days' top-level name; animation sets the .ANM lacks take the stand-ins of
    kl_package.ANIM_SETS (guesses, see there).
    Weapons: arms=True (default) leaves a Dead Men weapon's path as it is under the new top-level name -
    kl_arms.arm() gives every actor its weapon afterwards (re/combat.md). arms=False is the old rule:
    a template Dog Days does not have is replaced by one of S's whose name starts alike. That rule
    handed 57 characters of Retomoto the pistol a PLAYER holds behind a human shield (the tree is in
    file order and HG_M9Beretta_Human_Shield is its first 'HG_'), SMG_UMP_SBR and a helicopter gun:
    templates no stock level gives an NPC."""
    old, new = 'ROOT\\AllLevels/mainsceneincludes.zip', 'ROOT\\AllLevels/mainsceneincludes_multiplayer.zip'
    weapons = [S.prp.path[k] for k in range(1, len(S.prp.nodes))
               if S.prp.path[k].lower().startswith((new + '\\AllLevels/equipment.zip\\Weapon\\').lower())
               and S.prp.path[k].count('\\') == 4]
    have = {c.name for c in kl_anm.Anm(S['.ANM'], 'dd').cols}
    out, guessed = {}, {}
    for s in Jn.p.keys:
        if s.lower().startswith(old.lower() + '\\'):
            t = new + s[len(old):]
            if not arms and not S.prp.resolve(t) and '\\Weapon\\' in t and weapons:
                fam = t.rsplit('\\', 1)[1].split('_')[0].lower()
                t = guessed[s.rsplit('\\', 1)[1]] = next((w for w in weapons if w.rsplit('\\', 1)[1].lower().startswith(fam)), weapons[0])
            out[s] = t
        elif s.startswith(kl_anm.PREFIX) and s not in have and not anim:   # anim: kl_anmjoin supplies the set
            name = s[len(kl_anm.PREFIX):]
            # ANIM_FALLBACK: GUESSES for sets neither the table nor S's .ANM has (F07 has no
            # 'Police'; Dead Men's 'Army' has no Dog Days namesake): the armed-NPC set every
            # Fragile Alliance level ships
            for cand in (kl_package.ANIM_SETS.get(name), name, ANIM_FALLBACK.get(kl_package.ANIM_SETS.get(name) or name)):
                if cand and kl_anm.PREFIX + cand in have:
                    out[s] = kl_anm.PREFIX + cand
                    break
            else:
                if name in kl_package.ANIM_SETS and kl_package.ANIM_SETS[name] is None:
                    # a vehicle set Dog Days has nothing for ('Van'): emptied. ASSUMPTION
                    # (re/cars.md): a ZHavokCar with no set is as harmless as the stock
                    # helicopters, which all have none; its passengers' door clips are missing
                    out[s] = ''
    log('  Dead Men paths re-pointed: %d; weapons replaced: %s' % (
        len(out), 'by kl_arms, below' if arms else {k: v.rsplit('\\', 1)[1] for k, v in guessed.items()}))
    return out


# ------------------------------------------------------------------ the authored layer: a module
AUTHOR = 'kl_fa_author'                 # the layer '--author' alone / author=True means: Retomoto Tower
AUTHOR_NAMES = ('HOST', 'prepare_host', 'strip', 'KEEP', 'DROP', 'layer_names', 'complete', 'wire', 'campaign_names')


def author_module(author):
    """build()'s `author` as a module, or None for no layer: True = AUTHOR, a name = that module of
    tools/ (imported here, late: an authoring module imports this file), a module = itself. It must
    hold AUTHOR_NAMES - build()'s docstring says what each is; one that is missing is an error here,
    before anything is built. kl_maps.one asks the same module for campaign_names()."""
    if not author:
        return None
    if author is True:
        author = AUTHOR
    if isinstance(author, str):
        import importlib
        author = importlib.import_module(author)
    lack = [n for n in AUTHOR_NAMES if not hasattr(author, n)]
    if lack:
        raise ValueError('authoring module %s lacks %s (kl_graft.build\'s docstring: author)' % (getattr(author, '__name__', author), ', '.join(lack)))
    return author


def author_arg(a):
    """'--author [module]' taken out of the argument list a -> build()'s `author`: False without the
    option, True for the option alone, else the module's name = the argument that follows it when
    that is not an option itself (so the name stands directly behind '--author', before any slot)."""
    if '--author' not in a:
        return False
    i = a.index('--author')
    named = i + 1 < len(a) and not a[i + 1].startswith('--')
    author = a[i + 1] if named else True
    del a[i:i + 1 + named]
    return author


# ------------------------------------------------------------------ the graft
def build(s_name, m_name, slot='F01', log=print, sel=None, sound=True, loc=True, light='stock', anim=True, fa=True,
          postfilter=True, ao=0.5, escape=True, author=False, bones=True, load=None, arms=True, arms_seed=None):
    """Systems of S + map of M -> (path of the archive, problems found by verify()).
    sound: merge what M's map names of M's bank into S's (kl_snd.graft_audio); False = the map's
    sound references are set to 0 (the silent builds of milestones A and B). loc: also graft the
    .LOC keys M's map names and S lacks, with their voice clips (only a Dead Men map has any).
    light: kl_light.normalise mode for a Dead Men map ('stock', 'm01', 'keep') or None (re/lighting.md).
    anim: the .ANM is S's + the sets and slots the level names of M's (kl_anmjoin, re/anmjoin.md);
    False = one stock file and renamed sets, as before. fa: keep S's position-free Fragile Alliance
    plumbing (escape-vehicle monitor, AIMonitor, briefing trigger, speakers) and repair the joined
    scene for a real round (kl_fa, re/fa_round.md). postfilter: a Dead Men map keeps its
    PostFilterBoxes and its filter sets get their curves (kl_light.graft_postfilter). ao: strength
    0..1 of Dead Men's light map baked into the vertex colours (kl_light.bake_ao); 0 = not baked.
    Both are on by default since the live runs LK0 - LK2 (re/lighting.md, second pass, outcome).
    escape: kl_escape's repairs of a Dead Men map's way to the escape vehicle (re/escape.md; needs fa).
    author: an authored Fragile Alliance layer, as a MODULE (author_module()): True = kl_fa_author
    (Retomoto Tower, re/retomoto_fa.md), a name = that module of tools/ (the bank the campaign way:
    'kl_fa_bank'), or a module. With kl_fa_author: host F07's own FA layer is re-placed before the graft
    and kept, the campaign squads that stay lose their mini-cutscene controllers, and once both parts are
    in the scene the layer is wired. THE INTERFACE is nine names (AUTHOR_NAMES), each read off the module
    at the moment it is used - kl_fa_street / kl_fa_blast replace kl_fa_author's from outside, and its KEEP
    is a module __getattr__ - so a module may be a thin one that hands on another's:
      HOST                   name of the systems level the layer is written for ('F07'). prepare_host runs
                             only when S is that level: the second step of a chain (S = the pseudo level
                             of step one) is not prepared again
      prepare_host(S, log)   on the stock Level S, before the subtrees are chosen: places (.prp ZGEOM[1] /
                             [2] and the .gms record of the same entity), box extents, values of S's own
                             objects. S.prp's nodes and S.ents stay paired by index
      strip(M, log)          on each converted Dead Men part M (DeadMen; not called for a Dog Days map),
                             before the join, where nothing goes by controller index yet: controllers off
                             nodes that stay, map nodes re-placed
      KEEP                   tuple of names / patterns (Select.match: fnmatch on the name and its family)
                             of S's MAP subtrees that stay, on top of kl_fa.host_keep's
      DROP                   tuple of patterns of S's map subtrees that go although KEEP names them (the
                             host's cover list when the map brings its own: a second one is an assert)
      layer_names(Jn)        -> the top-level names of the layer in the joined scene Jn: what
                             kl_fa.repair's prune may cut dead references from
      complete(Jn)           -> True once every part of the map is in Jn (one map: always; a chain: in
                             its last step only). Then, once:
      wire(Jn, log)          every reference list that names a map node. Values of existing controllers
                             only: it runs after kl_fa.repair, before anything goes by controller index
      campaign_names(level)  -> the top-level names of Dead Men level `level` that the campaign pre-pass
                             must leave in (asked by kl_maps.one(campaign=True); exact names, and () for a
                             level the layer does not know)
    layer_names / complete / wire run only with fa. What needs the WRITTEN level (chunk numbers, new
    entities: kl_fa_author.FINISH) is the module's own step after the build; nothing here calls it.
    bones: the skeletons that came with M's models are renumbered to the joined level (kl_chars.reid /
    rebind, re/characters_graft.md); False = left as M had them (the builds up to 2026-10-09 12:40).
    arms: a Dead Men map's characters get their weapons from kl_arms' table by class, depth and seed
    (arms_seed, default kl_arms.SEED; re/combat.md); False = dm_rename's old guess by name.
    load: the packing / weight options, see load_options() ('trim,slim,level=6'; None = the environment
    variable KL_GRAFT_LOAD, and without it the archive is packed as before, with a fixed time stamp)."""
    lopt = load_options(load)
    sch = J.schema('dd')
    for t, load in SOUND_TYPES.items():
        if sch.types[t]['load'] != load:
            raise ValueError('re/kl2.json was rebuilt: type handler %d is no longer the sound reference' % t)
    S, M = Level(s_name), (DeadMen(m_name, log, ao) if m_name.startswith('M') else Level(m_name))
    au = author_module(author)                          # None, kl_fa_author, or the module named / handed in
    if au:
        if s_name == au.HOST:
            au.prepare_host(S, log)                     # before picks_of: positions and values on the stock Level
        if M.dm:
            au.strip(M, log)
    notes = []
    note = lambda s: (notes.append(s), log('  note: ' + s))

    # ---- which subtrees
    sel = sel or Select()
    kept = kl_fa.host_keep(S.prp) if fa else ()
    if kept or au:
        sel = Select(sel.geometry, sel.m_add, sel.m_drop, tuple(sel.s_keep) + tuple(kept) +
                     tuple(x for x in (au.KEEP if au else ()) if x not in sel.s_keep),
                     tuple(sel.s_drop) + tuple(au.DROP if au else ()))
    picks, dropped = picks_of(S, M, sel)
    s_tops = {t for sc, t in picks if sc is S.prp}
    m_tops = [t for sc, t in picks if sc is M.prp]
    m_nodes = {k for t in m_tops for k in range(t, M.prp.end[t])}
    log('%s systems (%d subtrees, %d nodes) + %s map (%d subtrees, %d nodes); left out of %s: %s' % (
        s_name, len(s_tops), sum(S.prp.end[t] - t for t in s_tops), m_name, len(m_tops), len(m_nodes), m_name,
        collections.Counter(J.family(n) for n in dropped).most_common()))

    # ---- .gms / .buf: remove S's map, graft M's map
    A, B = S.scene, M.scene
    lost = collections.Counter()
    for t in S.prp.tops():
        if t not in s_tops:
            r = A.remove(S.ents[t - 1])
            lost['S links'] += r['links']; lost['S pairs'] += r['pairs']
    s_kept = set(A.entities())
    copy, refs_m, shift = {}, {}, None
    for t in m_tops:
        r = A.graft(B, M.ents[t - 1], head=True)
        refs_m.update(r['refs']); shift = r['buf']
        copy.update(zip(M.ents[t - 1].walk(), r['top'].walk()))
    top_ent = {(id(S.prp), t): S.ents[t - 1] for t in s_tops}
    top_ent.update({(id(M.prp), t): copy[M.ents[t - 1]] for t in m_tops})
    A.roots = [top_ent[id(sc), t] for sc, t in picks]
    # lists and pairs between two grafted subtrees (graft() keeps only those inside one)
    for e, c in copy.items():
        if e.links is not None:
            c.links = [(copy[t] if t is not None else None, b) for t, b in e.links if t is None or t in copy]
            lost['M links'] += len(e.links) - len(c.links)
    have = set(A.pairs)
    for a, b in B.pairs:
        if (a is None or a in copy) and b in copy:
            p = (copy.get(a), copy[b])
            if p not in have:
                A.pairs.append(p); have.add(p)
        else:
            lost['M pairs'] += 1
    log('  lists / pairs that crossed the cut and are gone: %s' % dict(lost))
    # KEYS tracks of grafted entities live in M's head, now at + shift
    nkeys = 0
    for e, c in copy.items():
        r = e.raw
        for p, ko in keys_tracks(e.raw):
            if any(not 16 <= v < len(B.head) for v in ko):
                raise ValueError('%r: KEYS offset outside the .buf head' % e)
            r = r[:p] + struct.pack('<6I', *(v + shift for v in ko)) + r[p + 24:]
            nkeys += 1
        if r is not e.raw:
            c.raw = r
    A.nav = B.nav
    A.budget += B.budget                                # ASSUMPTION, see kl_scene
    if A.dyn is not None and B.dyn is not None:
        if [c for c, _n in A.dyn] != [c for c, _n in B.dyn]:
            note('dynamic lists name different classes; kept %s\'s' % s_name)
        else:
            A.dyn = [(c, max(n, m)) for (c, n), (_c, m) in zip(A.dyn, B.dyn)]   # ASSUMPTION
    slot1 = A.slots()
    final = list(A.entities())

    # ---- .prp join
    base_settings = S.prp.p.settings
    mblock, sblock = dict(J.block(M.prp)), dict(J.block(S.prp))
    take = {n: M.prp for n in TAKE if n in mblock}
    if 'PostFilterBoxes' in mblock and (not M.dm or postfilter):   # Dead Men's sets index Dead Men's palette: only with graft_postfilter
        take['PostFilterBoxes'] = M.prp
    elif 'PostFilterBoxes' in sblock:                   # S's boxes lie in S's world: none
        ent = [(n, t) for n, t in J.block(S.prp) if n != 'PostFilterBoxes']
        S.prp.p.settings = [(0x04, struct.pack('<I', len(ent)))] + [x for _n, t in ent for x in t]
    try:
        label = '%s systems + %s map' % (s_name, m_name)
        Jn = J.join(S.prp, picks, label, take=take)
        if not M.dm and m_name[:1] == 'L' and m_name[1:].isdigit():
            # Dog Days CAMPAIGN level as the map (re/dd_campaign_fa_1025.md): its actors' weapons and its
            # camera setup name the dropped campaign systems zip; re-point those to the multiplayer zip
            # (all 9 weapons L05 uses exist there, MEASURED). Paths only; no animation or arms rule
            # (same exe, same .ANM family, kl_anmjoin covers the sets). Not run for any F level.
            rn = campaign_rename(Jn)
            log('  campaign paths re-pointed: %d' % len(rn))
            Jn = J.join(S.prp, picks, label, rename=lambda s: rn.get(s, s), take=take)
        if M.dm:
            rename = dm_rename(Jn, S, log, anim, arms)
            Jn = J.join(S.prp, picks, label, rename=lambda s: rename.get(s, s), take=take)
            if arms:                                    # before anything goes by controller index; values only
                import kl_arms
                kl_arms.arm(Jn, S['.ANM'], m_name, nodes={j for j, (sc_, _k) in enumerate(Jn.origin) if sc_ is M.prp},
                            seed=kl_arms.SEED if arms_seed is None else arms_seed, log=log)
    finally:
        S.prp.p.settings = base_settings
    esc = None
    if fa:                                              # before anything goes by controller index
        kl_fa.repair(Jn, tuple(kept) + tuple(au.layer_names(Jn) if au else ()), log)
        if au and au.complete(Jn):                      # both parts are in: every list that names a map node
            au.wire(Jn, log)
        if escape and M.dm:                             # re/escape.md: the wall Dead Men's players climb is opened,
            import kl_escape                            # container reach 80 -> 125 (values of existing objects only)
            esc = kl_escape.repair(Jn, log)
        if sel.m_drop:                                  # a test build without some of M's subtrees (e.g. AI_Enemies!*):
            kl_fa.prune(Jn, [M.prp.names[t] for t in m_tops], log)     # what named them names nothing now
    if Jn.names[1:] != [e.name.decode('latin1') for e in final]:
        raise ValueError('joined .prp and joined .gms list different entities')
    at = {(id(sc), k): j for j, (sc, k) in enumerate(Jn.origin)}      # source node -> joined node
    mj = {k: at[id(M.prp), k] for k in m_nodes}

    # ---- roots of M in its .prm
    prm_s, prm_m = G.read(S['.prm'], 'dd'), G.read(M['.prm'], 'dd')
    proots = [r for r in G.prp_roots(M.prp.p, M.prp.tids, sch, 'dd')
              if (r[0][0] == 'scene' and r[0][1] in take) or (r[0][0] != 'scene' and r[0][0] in m_nodes)]
    roots = [(c, k) if k else c for _w, c, k in proots] + [e.model for e in copy if e.model]
    kinds, _args = G.walk(prm_m, roots)
    order = sorted(kinds)
    cmap = {old: len(prm_s.chunks) + k for k, old in enumerate(order)}   # what append() will hand out
    # materials and textures M's kept chunks name
    slots = {prm_m.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    tex_s, tex_m, mat_s, mat_m = T.read_tex(S['.TEX']), T.read_tex(M['.TEX']), T.read_mat(S['.MAT']), T.read_mat(M['.MAT'])
    want = set(T.used_textures(mat_m, slots))
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm_m, i, k, _args.get(i, 0)):
            if typ in 'tT' and prm_m.u32(i, off):
                want.add(prm_m.u32(i, off) % G.SLOTS['dd'])
    tex, tmap = T.merge_tex(tex_s, tex_m, want)
    mat, mmap = T.merge_mat(mat_s, mat_m, slots, tmap)
    log('  .prm: %d of %d chunks of %s appended to %d; materials %d -> %d slots (+%d), textures %d -> %d ids (+%d)' % (
        len(order), len(prm_m.chunks) - 1, m_name, len(prm_s.chunks) - 1, len(mat_s.insts), len(mat.insts),
        len(mat.insts) - len(mat_s.insts), len(tex_s.tex), len(tex.tex), len(tex.tex) - len(tex_s.tex)))

    # ---- .oct / .rmi / .rmc: slot ids of both sides, then the sets in the joined room order
    oct_s, oct_m = O.Oct.parse(S['.oct']), O.Oct.parse(M['.oct'])
    ids_s = {S.slot0[e] + 2: slot1[e] + 2 for e in s_kept}
    drop_s = {S.slot0[e] + 2 for e in S.ents if e not in s_kept}
    ids_m = {M.slot0[e] + 2: slot1[c] + 2 for e, c in copy.items()}
    drop_m = {M.slot0[e] + 2 for e in M.ents if e not in copy}
    ids_s[1] = ids_m[1] = 1                             # the scene root
    sets = {}
    for lv, octx, ids, drop, to in ((S, oct_s, ids_s, drop_s, lambda e: e), (M, oct_m, ids_m, drop_m, copy.get)):
        ro = O.room_order([lv.prp.parent[k] - 1 for k in range(1, len(lv.prp.nodes))],
                          [is_room(t) for t in lv.prp.tids[1:]])
        if len(ro) != len(octx.rooms):
            raise ValueError('%s: %d rooms, %d tree sets in the .oct' % (lv.name, len(ro), len(octx.rooms)))
        new = O.remap_ids(octx, ids, drop)
        for i, five in zip(ro, new.rooms):
            e = None if i < 0 else to(lv.ents[i])
            if i < 0:
                sets.setdefault(None, []).append(five)
            elif e is not None and e in slot1:
                sets[e] = five
    _ents, ro = rooms_of(A)
    rooms = [O.join_room_trees(*sets[None]) if e is None else sets[e] for e in ro]
    rec_m = {v: n for n, v in enumerate(oct_m.record_refs())}
    keep_m = sorted({rec_m[prm_m.u32(i, 0x1c)] for i, k in kinds.items() if k == 'root' and prm_m.u32(i, 0x1c)})
    base = O.Oct(oct_s.header, rooms, oct_s.records, oct_s.tail)
    octj, _same, refs_b = O.append_records(base, oct_m, cmap, keep_m)
    refs_a = dict(zip(oct_s.record_refs(), octj.record_refs()))        # S's records moved with the room trees
    unref = lambda v: (v & ~1) - 4
    prm, cmap2 = G.append(prm_s, prm_m, roots, mmap, {unref(a): unref(b) for a, b in refs_b.items()}, tmap)
    if cmap2 != cmap:
        raise ValueError('kl_prmgraph.append numbers chunks differently than assumed here')
    if postfilter and M.dm and 'PostFilterPalettes' in mblock and 'PostFilterPalettes' in sblock:
        # M's filter sets (named by its PostFilterBoxes chunk) get their own colour curves: appended to
        # S's palette, the sets' 37 entry numbers rewritten (re/lighting.md second pass, step 2)
        blk = lambda b: u32([t for t in b['PostFilterPalettes'] if t[0] == 9][-1])
        prep = kl_light.graft_postfilter(prm, blk(sblock), prm_m.chunks[blk(mblock)],
                                         [cmap[i] for i, k in kinds.items() if k == 'pf'], log=log)
        log('  post filter: %s' % {k: v for k, v in prep.items() if not isinstance(v, (list, dict))})
    moved = 0
    for i in range(1, len(prm_s.chunks)):               # S's model roots: (.oct record offset + 4) | 1 at +0x1c
        c = prm.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
            v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
            prm.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]
            moved += 1
    if moved != len(oct_s.records):
        raise ValueError('%d of %s\'s %d .oct records are named by a model root' % (moved, s_name, len(oct_s.records)))
    prm_bytes = G.write(prm)
    mat.refs = T.material_refs(prm_bytes)
    index = {}
    for ext in ('.rmi', '.rmc'):
        a = O.remap_ids(O.RoomIndex.parse(S[ext]), ids_s, drop_s)
        b = O.remap_ids(O.RoomIndex.parse(M[ext]), ids_m, drop_m)
        b = O.RoomIndex(b.tree, [x.sized(O.BOX['dd']) for x in b.boxes], O.BOX['dd'])
        index[ext] = (O.join_index(a, b) if a.boxes and b.boxes else b if b.boxes else a).pack()
        log('  %s: %d boxes of %s + %d of %s' % (ext, len(a.boxes), s_name, len(b.boxes), m_name))
    log('  .oct: %d room sets, %d + %d records' % (len(rooms), len(oct_s.records), len(keep_m)))

    # ---- entity models, then the properties of M's nodes
    for e, c in copy.items():
        if e.model:
            c.model = cmap[e.model]
    for where, chunk, _kind in proots:
        node, ctrl, f = (tuple(where) + (None,))[:3]    # a scene-block root is ('scene', name)
        if node == 'scene':
            s = Jn.p.settings
            k = next(i for i, t in enumerate(s) if t[0] == 0x0c and Jn.p.key(t) == ctrl)
            if u32(s[k + 4]) != chunk:
                raise ValueError('scene property %s is not where prp_roots found it' % ctrl)
            s[k + 4] = (s[k + 4][0], struct.pack('<I', cmap[chunk]))
            continue
        n = Jn.nodes[mj[node]]
        def fn(us, f=f, chunk=chunk):
            if u32(us[f][0]) != chunk:
                raise ValueError('chunk field moved')
            us[f][0] = (us[f][0][0], struct.pack('<I', cmap[chunk]))
        edit(n, 'props', fn) if ctrl is None else edit(n['ctrls'], ctrl, fn)
    count = collections.Counter()
    room_cells = set()
    for k in sorted(m_nodes):
        for cls, holder, key in objects(Jn, mj[k]):
            fs, lab = sch.fields(cls), labels(cls)
            hot = [] if sound else [i for i, f in enumerate(fs) if f.type in SOUND_TYPES and f.kind == 'I']
            pos = {l: i for i, l in enumerate(lab) if l in ('ZROOM[0]', 'ZROOM[1]', 'ZROOM[9]', 'ZROOM[10]',
                                                           'ZParticleEmitter[10]', 'ZParticleEmitter[11]')}
            if not hot and not pos:
                continue
            def fn(us):
                for i in hot:
                    if u32(us[i][0]):
                        us[i][0] = (us[i][0][0], bytes(4)); count['sound references set to 0'] += 1
                if 'ZROOM[9]' in pos:
                    ng, nl = u32(us[pos['ZROOM[0]']][0]), us[pos['ZROOM[1]']][0][1][0]
                    g, l = u32(us[pos['ZROOM[9]']][0]), u32(us[pos['ZROOM[10]']][0])
                    if ng:
                        us[pos['ZROOM[9]']][0] = (us[pos['ZROOM[9]']][0][0], struct.pack('<I', g + shift))
                    if nl:
                        us[pos['ZROOM[10]']][0] = (us[pos['ZROOM[10]']][0][0], struct.pack('<I', l + shift))
                    if ng or nl:
                        room_cells.update(kl_scene.room_refs(A.head, 'dd', g + shift, ng, l + shift, nl))
                        count['rooms with gates or lists'] += 1
                for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
                    if l in pos and u32(us[pos[l]][0]) not in (0, 0xffffffff):
                        v = u32(us[pos[l]][0])
                        if not 16 <= v < len(B.head) and not M.dm:
                            raise ValueError('emitter offset %#x outside the .buf head' % v)
                        if not 16 <= v < len(B.head):   # a converted field that is not an offset: none
                            v = 0xffffffff - shift; count['emitter fields cleared'] += 1
                        us[pos[l]][0] = (us[pos[l]][0][0], struct.pack('<I', v + shift)); count['emitter offsets'] += 1
            edit(holder, key, fn)
    # ---- S's dead map models. The loader reads the whole .prm into ONE heap block (kl2 0x82049b:
    # HeapAlloc of file size + 0x60000 through 0x89e850); the block of the first Retomoto build
    # (100.6 MB) was refused and the header write at 0x8e5bbd went to address 0 (run RT1). Vertex and
    # index data of S's map models that no root of the joined level reaches (F07: 42 MB of 64) become
    # 16-byte stubs; their chunk INDICES stay, so nothing is renumbered. Only when the file is past
    # PRM_LIMIT: smaller files loaded as they were (the bank's 86.5 MB ran live many times).
    # ASSUMPTION: nothing but the model graph reads a vtx / idx chunk (the dead roots, object tables,
    # meshes and descriptors stay as they are, so a walk over the .oct tail still finds them).
    size = sum(len(c) for c in prm.chunks if c)
    if size > PRM_LIMIT:
        live = [(c, k) if k else c for _w, c, k in G.prp_roots(Jn.p, Jn.tids, sch, 'dd')] + [e.model for e in final if e.model]
        reached = G.walk(prm, live)[0]
        # what the unreached chunks are: G.orphans walks from every unreached chunk shaped like a model
        # root (in a chained build the dead models are those of the FIRST step's S: no level file names them)
        dead = [i for i, k in G.orphans(prm, reached).items() if k in ('dead:vtx', 'dead:idx') and len(prm.chunks[i]) > 16]
        for i in dead:
            prm.chunks[i] = bytes(16)
        prm_bytes = G.write(prm)
        mat.refs = T.material_refs(prm_bytes)
        log('  .prm: %.1f MB is past %d MB: %d vertex / index chunks that nothing reaches emptied -> %.1f MB' % (
            size / 1e6, PRM_LIMIT // 1000000, len(dead), len(prm_bytes) / 1e6))
    # REF ids in M's gates and neighbour lists; an id no entity has (stock has them) goes to a free one
    A.head = kl_scene.remap_refs(A.head, sorted(room_cells), refs_m, missing=A.ref_slots)
    log('  M nodes: %s; %d KEYS blocks moved by %#x; %d REF cells in gates / lists' % (dict(count), nkeys, shift, len(room_cells)))

    # ---- sound: S's bank + what M's map nodes name of M's bank; the fields are rewritten in place
    audio = kl_snd.graft_audio(s_name, m_name, Jn, [mj[k] for k in sorted(m_nodes)], log, loc=loc) if sound else None
    if audio:                                           # interleaved stream groups: kl_snd.merge carries them whole; checked here
        import kl_whd
        torn = set(kl_whd.torn_groups('dd', audio.beside['.WHD']))
        named = sum(off in torn for _w, _i, off in kl_snd.Snd('dd', audio.members['.SND']).walk().waves())
        log('  stream groups: %d records of the .WHD stand outside a walkable group, %d of them named by a wave' % (len(torn), named))
        if named:
            audio.problems.append('%d wave references name a record of a torn interleaved stream group (divide fault at kl2 0x44668b)' % named)
    snd = audio.members['.SND'] if audio else S['.SND']

    # Heroes!: S's nodes at M's places
    placed = 0
    m_top = {M.prp.names[t]: t for t in M.prp.tops()}
    for t in s_tops:
        name = S.prp.names[t]
        if name.startswith('Heroes!') and name in m_top:
            src = units(M.prp.nodes[m_top[name]]['props'][1:-1])
            lab = labels(S.prp.cls(t))
            if lab != labels(M.prp.cls(m_top[name])):
                continue
            def fn(us):
                for l in ('ZGEOM[1]', 'ZGEOM[2]'):
                    us[lab.index(l)] = list(src[lab.index(l)])
            edit(Jn.nodes[at[id(S.prp), t]], 'props', fn)
            S.ents[t - 1].rot, S.ents[t - 1].trans = M.ents[m_top[name] - 1].rot, M.ents[m_top[name] - 1].trans
            placed += 1
    log('  Heroes! groups placed where %s has them: %d' % (m_name, placed))

    # ---- lights of a Dead Men map in forms stock Dog Days has (re/lighting.md)
    if light and M.dm:
        lrep = kl_light.normalise(Jn, A, prm, nodes=set(mj.values()), links=light, log=log)
        log('  lights (%s): %s' % (light, {k: (len(v) if isinstance(v, list) else v) for k, v in lrep.items()}))

    # ---- speech triggers without their line (after every edit that goes by controller index)
    cut = collections.Counter()
    for k in range(1, len(Jn.nodes)):
        keep = [c for c in Jn.nodes[k]['ctrls'] if not mute_speech(Jn, c, snd)]
        cut['M' if Jn.origin[k][0] is M.prp else 'S'] += len(Jn.nodes[k]['ctrls']) - len(keep)
        Jn.nodes[k]['ctrls'] = keep
    if sum(cut.values()):
        note('OnlineSpeakTrigger controllers removed, their line is not in the level\'s .SND: %s' % dict(cut))

    # ---- FDX (bone dynamics of the map's hanging objects)
    A.fdx = None
    if B.fdx is not None:
        block = MB.fdx_join([(M['.buf'], B.fdx, cmap)])
        if block:
            A.head += bytes(-len(A.head) % 16)
            A.fdx = len(A.head)
            A.head += block + bytes(-len(block) % 16)
    # surface table: S's; every REF must still be there
    table = MB.SurfaceTable(A.tail)
    gone = table.refs() - {e.ref for e in final}
    if gone:
        note('surface table: %d effects were in %s\'s map and are cleared' % (len(gone), s_name))
        table.remap({e.ref: e.ref for e in final}, missing=MB.NONE)
        A.tail = table.serialize()
    cut = kl_escape.place_entities(Jn, list(A.entities()), esc, log) if esc else ()     # the sunk wall in the .gms too
    gms, buf = A.write()

    # ---- the members no id space module covers
    refs_s = {e.ref: e.ref for e in s_kept}
    hvk = kl_hvk.join([(kl_hvk.Hvk(M['.HVK']), refs_m)], (kl_hvk.Hvk(S['.HVK']), refs_s))
    hvk = (kl_escape.cut_collision(hvk, cut, log) if cut else hvk).serialize()           # ... and its collision gone
    sgd = MB.sgd_join([(M['.sgd'], refs_m), (S['.sgd'], refs_s)])
    s_names = {S.prp.names[t] for t in s_tops}
    m_names = {M.prp.names[t] for t in m_tops}
    room_paths = [Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k])]
    sgp = MB.Sgp.join([(MB.Sgp(M['.sgp']), lambda p: p.split('\\')[0] in m_names),
                       (MB.Sgp(S['.sgp']), lambda p: p.split('\\')[0] in s_names)], room_paths).serialize()
    body = [k for k, v in sch.geoms.items() if v == 'ZHavokRigidBody']
    nb = lambda ents: sum(e.tid in body for e in ents)
    hrd = MB.hrd_join([(M['.hrd'] if '.hrd' in M.ext else None, nb(M.ents), nb(copy)),
                       (S['.hrd'] if '.hrd' in S.ext else None, nb(S.ents), nb(s_kept))])
    if hrd is None:
        note('.hrd left out: the rigid bodies do not all come from one level')
    # animations: one file that has every set the joined .prp names
    used = {s for s in Jn.p.keys if s.startswith(kl_anm.PREFIX)}
    if anim:
        # S's file is the base (nothing of it moves); sets and slot names the joined level names
        # come from M's file (Dead Men clips converted 0x50 -> 0x68), character sets Dog Days has
        # no namesake for are stand-ins (GUESSES, kl_anmjoin.STAND_IN); donor F03 has Police,
        # Thug, Civilian and Dog
        aj, arep = kl_anmjoin.join(S['.ANM'], M['.ANM'], Jn.p.keys, donors=[kl_anmjoin.stock_anm('F03')], log=log)
        for b in kl_anmjoin.verify(aj, arep):
            note('.ANM: ' + b)
        anm_bytes = aj.save()
        log('  .ANM joined: %d -> %d bytes; %s; guesses: %s; missing: %s' % (
            len(S['.ANM']), len(anm_bytes), dict(arep['stats']), arep['guesses'], arep['missing']))
    else:
        anm = None
        for lv in ((S,) if M.dm else (M, S)):            # Dead Men's .ANM has another clip header
            have = {c.name for c in kl_anm.Anm(lv['.ANM'], 'dd').cols}
            if anm is None and used <= have:
                anm = lv
            log('  .ANM of %s lacks %s' % (lv.name, sorted(x[len(kl_anm.PREFIX):] for x in used - have) or 'nothing the level names'))
        if anm is None:
            anm = S
            note('no single .ANM has every animation set; %s\'s is used' % s_name)
        anm_bytes = anm['.ANM']
    # ---- skeletons of M's models. A skeleton is baked against ITS level: table [5] maps the level's
    # bone ids to bones and tables [8] [9] [10] map bones to the index of their name in the level's own
    # .ANM bone table (kl_chars docstring; 2,247 stock skeletons, no exception). M's models came with
    # M's numbers, but the level now has S's ids and the joined .ANM table (S's names first, M's car
    # bones appended), so above the 61 names all levels share a clip drove the wrong bone: faces,
    # fingers, car doors and wheels. Rewritten here; the new tables are new chunks at the END of the
    # .prm, so no index moves. S's skeletons need nothing: S's ids and S's part of the table are kept.
    if bones:
        import kl_chars
        sks = sorted(cmap[i] for i, k in kinds.items() if k == 'skel')
        # a bone no clip of the joined file moves (M01's 'bone01'..'bone04') has no entry in its bone
        # table; it gets one at the end, as kl_chars.put does, so that every bone has a number of its
        # own (in its own level it had one too). ASSUMPTION: a name without tracks is harmless there.
        table = kl_anm.Anm(anm_bytes, 'dd')
        number, lack = kl_chars.anm_number(table.bones), []
        for sk in sks:
            for nm in kl_chars.bone_names(prm, sk):
                if nm.lower() not in number:
                    table.bones.append(nm); lack.append(nm)
                    number[nm.lower()] = len(table.bones) - 1
        if lack:
            anm_bytes = table.save()
            log('  .ANM bone table: +%d names that only skeletons of %s have (%s)' % (len(lack), m_name, ', '.join(lack[:6])))
        try:
            ids = kl_chars.level_ids(prm_s)
        except ValueError as x:                         # S is a build made before this step existed
            ids = None
            note('bone ids of %s are not one numbering (%s): the ids of the skeletons of %s are left as they were' % (s_name, x, m_name))
        done = collections.Counter()
        for sk in sks:
            try:
                if ids is not None:
                    done['bone ids'] += kl_chars.reid(prm, sk, ids)
                done['animation numbers'] += kl_chars.rebind(prm, sk, number)
                done['skeletons'] += 1
            except (KeyError, ValueError, StopIteration) as x:
                note('skeleton %d of %s not renumbered: %r' % (sk, m_name, x))
        if done:
            # reid() renumbers the skeleton's id table only; each bone definition carries its id a
            # second time (+0x3e), which the bullet-mark code 0x88c840 looks up: a stale one gave
            # table[old id] = 0xff as a matrix index (crash kl2 0x4c34b3 when the owner shot a
            # guard on Retomoto, 2026-10-09; re/crash_owner_1009.md)
            import kl_impact
            done['bone id bytes'] += kl_impact.sync_bone_ids(prm, sks)
            prm_bytes = G.write(prm)
            mat.refs = T.material_refs(prm_bytes)
        log('  skeletons of %s: %d of %d renumbered to the joined level: %d bone ids, %d animation numbers changed' % (
            m_name, done['skeletons'], len(sks), done['bone ids'], done['animation numbers']))

    union = os.path.join(workdir(), 'build', 'shared', 'union.fxc')    # Dead Men has no cache of its own
    fxc = T.merge_fxc(S['.fxc'], M['.fxc'] if '.fxc' in M.ext else open(union, 'rb').read())
    if M.dm:
        # converted Dead Men materials can ask for a shader permutation no Dog Days cache holds;
        # the object is then not drawn at all (35 materials on 920 objects of M03: re/lighting.md,
        # second pass). kl_light.fit_shaders switches features off until a compiled one fits.
        fit = kl_light.fit_shaders(mat, fxc, log=log)
        log('  shaders: %d materials fitted, %d without any compiled shader' % (len(fit['fixed']), len(fit['unresolved'])))
        for slot_, (nm, lack) in sorted(fit['unresolved'].items())[:10]:
            note('material %s has no compiled shader (not drawn)' % nm)
    out = {'.gms': kl_gms.pack(gms), '.buf': buf, '.prp': Jn.p.serialize(), '.prm': prm_bytes,
           '.TEX': T.write_tex(tex), '.MAT': T.write_mat(mat), '.fxc': fxc,
           '.oct': octj.pack(), '.rmi': index['.rmi'], '.rmc': index['.rmc'], '.HVK': hvk, '.sgd': sgd,
           '.sgp': sgp, '.hrd': hrd, '.ANM': anm_bytes}
    if audio:
        out.update(audio.members)                       # '.SND', and '<Language>.LOC' when keys were grafted
    if lopt['trim'] or lopt['slim']:                    # re/loading.md: what only S's removed map holds; ids all stay
        out['.prm'], out['.TEX'], _lrep = lighten(out['.prm'], out['.TEX'], out['.MAT'],
                                                  live_roots(Jn, [e.model for e in final]), hud_textures(Jn), lopt, log)
    members = []
    for n in S.order:                                   # S's archive order; everything else is S's
        ext = n.rsplit('_Main', 1)[1] if '_Main' in n else None
        data = out.get(ext, S.files[n]) if ext else S.files[n]
        if data is not None:
            members.append((member_name(n, s_name, slot), data))
    problems = verify(dict(out, snd=snd), Jn, S, M, copy, s_kept, mj, shift, log, audio,
                      light=light in ('stock', 'm01') and M.dm, fa=fa, bones=bones)
    problems += [n for n in notes if n.startswith('.ANM: ')]
    for p in problems:
        log('  PROBLEM: ' + p)
    log('verify: problems: %d' % len(problems))
    beside = beside_of(s_name)
    if audio:
        beside.update(audio.beside)                     # merged .WHD / .WAV, _LS.SND with the new trailer offset
    path = write_level(slot, members, beside, log, lopt)
    with open(os.path.join(out_dir(slot), 'graft.txt'), 'w') as f:
        f.write('%s systems + %s map (%s; %s)\nproblems: %d\n%s\n' % (
            s_name, m_name, sel, ', '.join(['silent map' if not sound else 'merged bank' + ' + voice lines' * loc, 'lights %s' % light,
                                         'joined .ANM' if anim else 'stock .ANM', 'FA repairs' if fa else 'no FA repairs',
                                         'post filter of M' if postfilter else 'no post filter boxes', 'light map baked at %g' % ao if ao else 'no baked light']),
            len(problems), '\n'.join(problems + notes)))
    return path, problems


# ------------------------------------------------------------------ verification
def verify(out, Jn, S, M, copy, s_kept, mj, shift, log=print, audio=None, light=False, fa=False, bones=False):
    """Re-read every written member with its module and follow every cross-reference this file
    knows. Returns the problems ([] = install)."""
    sch, bad = J.schema('dd'), []
    # .gms / .buf
    sc = kl_scene.Scene(kl_gms.unpack(out['.gms']), out['.buf'])
    bad += sc.check()
    g2, b2 = sc.write()
    if kl_gms.pack(g2) != out['.gms'] or b2 != out['.buf']:
        bad.append('.gms / .buf do not round-trip')
    ents = list(sc.entities())
    slot = sc.slots()
    by_slot = {v + 2: e for e, v in slot.items()}
    by_ref = {e.ref: e for e in ents}
    head = len(sc.head)
    # .prp
    data, misfits, paths, names = J.check(Jn, log=lambda *_a: None)
    if data != out['.prp']:
        bad.append('.prp changed after it was written')
    bad += ['%s: %s: %s' % (Jn.path[k], what, why) for k, what, why in misfits[:10]]
    bad += ['scene path does not resolve: %s %s -> %s' % (h, f, s) for _k, h, f, s in paths[:10]]
    # stock Dog Days levels carry 0..18 emitter names without a template (kl_prpjoin); Dead Men's
    # Impacts_Default_Smoke has no Dog Days template
    base_names = max(len(J.dangling(M.prp)[1]), 18)
    twice = [n for n, c in collections.Counter(Jn.names[k] for k in Jn.tops()).items() if c > 1]
    if twice:
        bad.append('%d top-level names are used twice, e.g. %s' % (len(twice), twice[0]))
    if len(names) > base_names:
        bad.append('%d particle template names do not resolve (stock %s: %d)' % (len(names), M.name, base_names))
    p = Prp(out['.prp'])
    nodes = p.nodes()
    if len(nodes) != len(ents) + 1 or Jn.names[1:] != [e.name.decode('latin1') for e in ents] or Jn.tids[1:] != [e.tid for e in ents]:
        bad.append('.prp nodes and .gms entities differ')
    items = collections.Counter()
    for k in range(len(Jn.nodes)):
        for nm, obj in Jn.nodes[k]['ctrls']:
            if Jn.p.key(nm) == 'InventoryBinding':
                item = [Jn.p.key(t) for t in obj if t[0] == 0x0e][0]
                items[item] += item != 'eFF2ItemNoItem'
    bad += ['item %s is bound %d times' % (k, v) for k, v in items.items() if v > 1]
    mute = sum(mute_speech(Jn, c, out['snd']) for k in range(len(Jn.nodes)) for c in Jn.nodes[k]['ctrls'])
    if mute:
        bad.append('%d OnlineSpeakTrigger name a line the .SND lacks (they delete themselves; crash at the first checkpoint)' % mute)
    # .prm, with the roots of the joined level
    prm = G.read(out['.prm'], 'dd')
    if G.write(prm) != out['.prm']:
        bad.append('.prm does not round-trip')
    proots = G.prp_roots(p, Jn.tids, sch, 'dd')
    geom = {w[0]: c for w, c, k in proots if w[0] != 'scene' and w[1] is None and k is None}
    wrong = sum(1 for k, e in enumerate(ents, 1) if e.model != geom.get(k, 0))
    if wrong:
        bad.append('%d entities: .gms model differs from ZGEOM[4]' % wrong)
    try:
        kinds, args = G.walk(prm, [(c, k) if k else c for _w, c, k in proots] + [e.model for e in ents if e.model])
    except ValueError as x:
        kinds, args = {}, {}
        bad.append('.prm: %s' % x)
    tex, mat = T.read_tex(out['.TEX']), T.read_mat(out['.MAT'])
    if T.write_tex(tex) != out['.TEX'] or T.write_mat(mat) != out['.MAT']:
        bad.append('.TEX / .MAT do not round-trip')
    octj = O.Oct.parse(out['.oct'])
    if octj.pack() != out['.oct']:
        bad.append('.oct does not round-trip')
    recs, seen = set(octj.record_refs()), collections.Counter()
    miss = collections.Counter()
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm, i, k, args.get(i, 0)):
            if typ == 'm' and prm.u16(i, off) not in mat.insts:
                miss['material'] += 1
            elif typ in 'tT' and prm.u32(i, off) and prm.u32(i, off) % G.SLOTS['dd'] not in tex.tex:
                miss['texture'] += 1
            elif typ == 'o':
                seen[prm.u32(i, off)] += 1
                miss['.oct record'] += prm.u32(i, off) not in recs
    bad += ['.prm names %d missing %ss' % (v, k) for k, v in miss.items() if v]
    if any(v > 1 for v in seen.values()):
        bad.append('.oct record named by two live model roots')
    if bones:                                           # every skeleton against the level's own .ANM (kl_chars; [] on stock levels)
        import kl_chars
        cb = kl_chars.check_bones(prm, kl_anm.Anm(out['.ANM'], 'dd').bones)
        bad += cb[:6] + (['... %d more skeleton problems' % (len(cb) - 6)] if len(cb) > 6 else [])
        import kl_impact
        bf = kl_impact.bone_faults(prm)
        bad += kl_impact.chunk_limit(out['.prm'])       # the game's chunk table has 73,728 slots (re/prm_limit.md)
        bad += bf[:6] + (['... %d more bone id faults' % (len(bf) - 6)] if len(bf) > 6 else [])
    if mat.refs != T.material_refs(out['.prm']):
        bad.append('.MAT ref table is not the .prm\'s')
    lost = T.used_textures(mat) - set(tex.tex)
    if lost:
        bad.append('%d material textures are not in the .TEX' % len(lost))
    if any(not (0 < c < len(prm.chunks) and len(prm.chunks[c]) == 64 and prm.u16(c, 2) == 8) for _f, c in octj.tail):
        bad.append('.oct tail names a chunk that is not a 64-byte mesh')
    # room trees: order, and every id an entity of the right kind under that room
    _e, ro = rooms_of(sc)
    if len(ro) != len(octj.rooms):
        bad.append('.oct has %d tree sets, the scene %d rooms' % (len(octj.rooms), len(ro)))
    def room_above(e):
        e = e.parent
        while e is not None and not is_room(e.tid):
            e = e.parent
        return e
    wrong = collections.Counter()
    for owner, five in zip(ro, octj.rooms):
        for ti, t in enumerate(five):
            for it in (t.items if t else ()):
                e = by_slot.get(it[0])
                if e is None:
                    wrong['no entity'] += 1
                elif room_above(e) is not owner:
                    wrong['other room'] += 1
                elif (ti == 4) != is_room(e.tid) or (ti < 4 and kl_gms.category(e.tid) != {0: 1, 1: 2, 2: 3, 3: 0}[ti]):
                    wrong['wrong tree'] += 1
            if t:
                try:
                    t.check()
                except Exception as x:
                    wrong['tree: %s' % x] += 1
    bad += ['.oct room trees: %d items: %s' % (v, k) for k, v in wrong.items()]
    for ext in ('.rmi', '.rmc'):
        ri = O.RoomIndex.parse(out[ext])
        if ri.pack() != out[ext]:
            bad.append(ext + ' does not round-trip')
        for b in ri.boxes:
            if b.room not in by_slot or not is_room(by_slot[b.room].tid):
                bad.append('%s: box names slot id %d, not a room' % (ext, b.room))
            if b.second and b.second not in by_slot:
                bad.append('%s: second id %d is no entity' % (ext, b.second))
    # .buf offsets: rooms (with their REFs), emitters, KEYS
    cells = 0
    for k in range(len(Jn.nodes)):
        cls = Jn.cls(k)
        lab = labels(cls)
        if 'ZROOM[9]' in lab:
            us = units(Jn.nodes[k]['props'][1:-1])
            ng, nl = u32(us[lab.index('ZROOM[0]')][0]), us[lab.index('ZROOM[1]')][0][1][0]
            g, l = u32(us[lab.index('ZROOM[9]')][0]), u32(us[lab.index('ZROOM[10]')][0])
            if (ng and not 16 <= g <= head - 0x74 * ng) or (nl and not 16 <= l < head):
                bad.append('%s: gates / lists outside the .buf head' % Jn.path[k]); continue
            for o in kl_scene.room_refs(out['.buf'], 'dd', g, ng, l, nl):
                v = struct.unpack_from('<I', out['.buf'], o)[0]
                cells += 1
                if (o - g) % 0x74 == 0x30 and g <= o < g + 0x74 * ng and (v not in by_ref or not is_room(by_ref[v].tid)):
                    bad.append('%s: gate leads to REF %d, not a room' % (Jn.path[k], v))
        for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
            if l in lab:
                v = u32(units(Jn.nodes[k]['props'][1:-1])[lab.index(l)][0])
                if v not in (0, 0xffffffff) and not 16 <= v < head:
                    bad.append('%s: %s outside the .buf head' % (Jn.path[k], l))
    for e in ents:
        if any(not 16 <= v < head for _p, ko in keys_tracks(e.raw) for v in ko):
            bad.append('%r: KEYS offset outside the .buf head' % e)
    # grafted KEYS tracks and room data still read the bytes M had
    mh = len(M.scene.head)
    if shift is not None and out['.buf'][shift:shift + 16] != M['.buf'][:16]:
        bad.append('M\'s .buf head is not at the shift')
    # other members
    h = kl_hvk.Hvk(out['.HVK'])
    if h.serialize() != out['.HVK']:
        bad.append('.HVK does not round-trip')
    stray = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) not in by_ref)
    if stray:
        bad.append('.HVK: %d placements name no entity' % stray)
    for name, payload in MB.sgd_read(out['.sgd']):
        if name in ('HavokShatterOctree', 'ExplodableOctree'):
            stray = sum(1 for leaf in MB.Octree(payload).leaves if leaf[0] not in by_ref)
            if stray:
                bad.append('.sgd %s: %d leaves name no entity' % (name, stray))
    g = MB.Sgp(out['.sgp'])
    if g.serialize() != out['.sgp']:
        bad.append('.sgp does not round-trip')
    want = sorted(Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k]))
    if sorted(r[0] for r in g.rooms) != want:
        bad.append('.sgp rooms are not the level\'s rooms')
    table = MB.SurfaceTable(sc.tail)
    if table.refs() - set(by_ref):
        bad.append('surface table names %d entities that are gone' % len(table.refs() - set(by_ref)))
    past = sum(1 for s in h.shapes for su, _f, _n in s.sub if su > len(table.materials))    # run M02b: read past the rows at kl2 0x4e5068
    if past:
        bad.append('.HVK: %d sub-parts name a surface row past the %d of the table' % (past, len(table.materials)))
    if sc.fdx is not None:
        for r in MB.fdx_read(out['.buf'], sc.fdx)[1]:
            if kinds.get(r['model']) != 'root':
                bad.append('FDX record names chunk %d, not a model' % r['model'])
    # sound references: every one is an object of the level's bank (S's, or the merged one), or
    # 0xffffffff = the sound of the _LS bank; without the merge M's must all be 0
    objs = kl_snd.Snd('dd', out['snd']).kind
    left = stray = 0
    for k in range(1, len(Jn.nodes)):
        from_m = Jn.origin[k][0] is M.prp
        for cls, holder, key in objects(Jn, k):
            fs = sch.fields(cls)
            for f, u in zip(fs, units(get_obj(holder, key)[1:-1])):
                if f.type in SOUND_TYPES and f.kind == 'I' and u32(u[0]):
                    left += from_m and audio is None
                    stray += u32(u[0]) not in objs and u32(u[0]) != kl_snd.LS_SOUND
    if stray:
        bad.append('%d sound references name no object of the .SND' % stray)
    if left:
        bad.append('%d sound references of the map still point into another bank' % left)
    if audio:
        bad += ['sound: ' + x for x in audio.problems]
    if light:
        bad += ['lights: ' + x for x in kl_light.check(Jn, sc, prm, nodes=set(mj.values()))]
    if fa:                                              # what a real Fragile Alliance round would crash or break on
        bad += ['FA: ' + str(f) for f in kl_fa.check(Jn, out['snd'], out.get('English.LOC', S['English.LOC']), out['.ANM']) if f.sev <= kl_fa.BROKEN]
    ncov = sum(Jn.p.key(nm) == 'FFCoverList' for k in range(1, len(Jn.nodes)) for nm, _b in Jn.nodes[k]['ctrls'])
    if ncov > 1:                                        # run RT2: assert kl2 0x6682c5 in the second one's init
        bad.append('%d cover lists (FFCoverList): the game data takes one' % ncov)
    a = kl_anm.Anm(out['.ANM'], 'dd')
    lack = {s for s in p.keys if s.startswith(kl_anm.PREFIX)} - {c.name for c in a.cols}
    if lack:
        bad.append('animation sets the .ANM lacks: %s' % sorted(lack))
    log('  verified: %d entities, %d nodes, %d reachable chunks, %d room sets, %d gate / list REF cells, %d textures, %d materials' % (
        len(ents), len(nodes), len(kinds), len(octj.rooms), cells, len(tex.tex), len(mat.insts)))
    return bad


def pairs(log=print):
    """For every S in F04..F09 (systems without dangling paths, kl_prpjoin) and every M: are the
    post-filter palettes equal, and which animation sets of M's map does S's .ANM lack."""
    pal, cols, used = {}, {}, {}
    for L in J.DD_FA:
        lv = Level(L)
        blk = dict(J.block(lv.prp))
        prm = G.read(lv['.prm'], 'dd')
        pal[L] = prm.chunks[[u32(t) for t in blk['PostFilterPalettes'] if t[0] == 9][-1]]
        cols[L] = {c.name for c in kl_anm.Anm(lv['.ANM'], 'dd').cols}
        side = J.sides(lv.prp)
        used[L] = {lv.prp.p.keys[u32(t)] for k in range(1, len(lv.prp.nodes)) if side[k] == 'map'
                   for toks in [lv.prp.nodes[k]['props']] + [b for _n, b in lv.prp.nodes[k]['ctrls']]
                   for t in toks if t[0] == 0x0c and lv.prp.p.keys[u32(t)].startswith(kl_anm.PREFIX)}
        log('%s: FDX %s, PostFilterBoxes %s' % (L, lv.scene.fdx is not None, 'PostFilterBoxes' in blk))
    for s in J.DD_FA[3:]:
        for m in J.DD_FA:
            if s != m:
                log('S %s M %s: palettes %s; map animation sets S lacks: %s' % (
                    s, m, 'equal' if pal[s] == pal[m] else 'DIFFER', sorted(x[len(kl_anm.PREFIX):] for x in used[m] - cols[s])))


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'plain':
        plain(a[1], *a[2:3])
    elif len(a) >= 3 and a[0] == 'build':
        opt = {}
        for o in ('--m-add', '--m-drop', '--s-keep', '--s-drop'):
            while o in a:
                i = a.index(o)
                opt.setdefault(o[2:].replace('-', '_'), []).extend(a[i + 1].split(','))
                del a[i:i + 2]
        light = 'stock'
        if '--light' in a:
            i = a.index('--light'); light = None if a[i + 1] == 'off' else a[i + 1]; del a[i:i + 2]
        ao = 0.5
        if '--ao' in a:
            i = a.index('--ao'); ao = float(a[i + 1]); del a[i:i + 2]
        flags = ('--geometry', '--silent', '--no-loc', '--stock-anm', '--no-fa', '--no-postfilter', '--no-escape', '--no-bones', '--no-arms')
        g, quiet, noloc, noanm, nofa, pf, noesc, nobones, noarms = (f in a for f in flags)
        author = author_arg(a)                          # False, True (kl_fa_author) or a module's name
        load = None
        if '--load' in a:
            i = a.index('--load'); load = a[i + 1]; del a[i:i + 2]
        a = [x for x in a if x not in flags]
        sys.exit(1 if build(a[1], a[2], *a[3:4], sel=Select(g, **opt), sound=not quiet, loc=not noloc, light=light,
                            anim=not noanm, fa=not nofa, postfilter=not pf, ao=ao, escape=not noesc, author=author,
                            bones=not nobones, load=load, arms=not noarms)[1] else 0)
    elif a and a[0] == 'install':
        src = None
        if '--from' in a:
            i = a.index('--from'); src = a[i + 1]; del a[i:i + 2]
        install(*a[1:2], src=src)
    elif a and a[0] == 'pairs':
        pairs()
    elif len(a) >= 3 and a[0] == 'lighten':
        relight(a[1], a[2], load_options(a[a.index('--load') + 1] if '--load' in a else 'trim,slim'))
    else:
        print(__doc__)
