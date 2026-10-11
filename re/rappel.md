# Rappel for Retomoto (track Y3, 2026-10-11 night; offline; nothing of it run in the game)

Owner: "definitely rappel and climb". Wish from the start: Retomoto from the very top, by rope. Today the crew starts on
the balcony (START row x 6000..6070, y 21011, z -930..770) and the blast lets them in. Tool: `tools/kl_fa_rappel.py`
(`facts`, `check`, `apply`). Build: `<work>\build\y_rappel\DM09r` (rebuilt after the review, same archive bytes as `DM09`; = `r_tab\DM09x` + Dog Days' own rappel clips in the
.ANM; only that member differs). luvsic: his repository (`G:\kl_scratch\luvsic\anp`, pulled 23:xx, "Already up to date")
has NO rappel code pushed; `loader\rappel.inc` is only planned in his CLAUDE.md 1b ("DM rappelling, grenades, giving
weapons are required to progress M02 and later"). Nothing to read there; the credit is for `clip +0x2C` (re/luvsic_pass.md
1.2), which this step uses.

## 1. Dead Men's rappel (kaneandlynch.exe, read)
Classes (RTTI, `re/kaneandlynch.json`): `ZFFPlayerMovementRappel` vtable 0x967144 (43 slots; made at 0x5ef287 by ctor
0x606dd0, movement kind 16 in the player's table), `Locomotion::ZFFRappelling` 0x9681d4 (NPC), controller
`ZRappellingBox` 0x97bca4 (size 92, no stored property of its own), `ZRappelCheckPoint` 0x97dff4 (52; saves a checkpoint),
`ZRopeLnkObj` 0x97a79c (a Havok link object, no stored property), `ZAppendage` 0x960144 (each hero carries
`GROUP_Apendage_ROPE\{PosBox_Dyn_COM, PosBox_Dyn_Attach, Ground_Appendage_Rope}` with this controller).
- The box is NOT the starter. `ZRappellingBox` (+0x30 a "on" byte, set by the event whose id is the word at 0xc8b510;
  0x6a0700) does two things: its tick 0x6a0590 posts a 0x64-byte record (owner, kind 0x18, float, -1) to the game's
  queue at `[[0xa8760c]+0x1550]` (0x6a04b0; the HUD prompt, icon `UI_KL_Communications_01#Rappel`, input names `rappel` /
  `rappel_kb` at 0x45d90e), and the movement tells it when the player takes the rope: 0x606f2c calls 0x6a0640 with the
  player, which, for the local player (0x66fbf0(0)), sends the box's eight event lists the event 0xc8b510 (0x6a0430).
  So the box is a PROMPT + notifier; the rope movement itself is entered by the player code (its search for a rappel
  point is in the unnamed 0x607420.. routine, `[movement+0x1388]` = the box, `+0x1384` = active).
- Clips: 15 slots `/Movement/Rappelling/{Fall Land Start Rappelling NPC_Rappelling 1 2 3 4 Jump_Start Jump_Loop Jump_End
  Start_On_Wall Wait_On_Wall Stop_On_Wall}` in 8 sets of every Dead Men file (PlayerCharacter, Lynch_Coop, Army,
  Mercenary_04, Female, Civilian, Bouncer, Thug), 12 clips (`anim:Movement/Soldier/Rappelling#...`), flags 0xc0 / 0x40,
  `Jump_End` has event 6, the others none. Root travel (units, local -y = down the rope): NPC_Rappelling 1636 in 119
  frames (13.8 / frame = 3.4 m/s), 3: 278/21, 4: 693/30, Jump_Loop 412/31, Jump_End 674/30. The movement looks the slots up
  by name at 0x60ac20 (Start, Jump_Start, Wait_On_Wall, Jump_Loop, Jump_End) and drives them: the descent is a code-driven
  rope slide that plays these clips, not one baked path.
- M09_A level data: `Ropes!Rope{,#01..#04}\Rope_Ground` (5 `ZRopeLnkObj`, nodes 1..10, no model, at the origin),
  `Characters!Hero!RappelPoint!` (nodes 11655..11673): `RappelBox` (the `RappellingBox` controller; box at (5999, 25483, -89),
  on the roof), `RappelFacingDir` (6049, 25650, -116), `Blocker_LynchImpatient`, ~12 `RappelCB_*` camera boxes with
  `Cam_RappelBegin` (7036, 26156, -102) and `Cam_RappelLookInsideBoardRoom` (4700, 21077, -105), `Activator_LookDown`
  (7518, 20208, -98); `Postfilers!Rappel_Postfilter_Box` (6621, 23167, -124); `RappelCheckPoint`; `Music!PlayMusic_Rappel`
  (TokyoRappel_Loop_V2_44_Wind, already in the stream); the squad `Characters!Mercenaries!020_MercSquad_Rappel` with the
  mini cutscenes `030_MiniCut_PreRappel`, `050_LynchHateHeights`, `060_LynchImpatient`, `070_LynchLockRappel_COOP`.
  The rope is 44.7 m (roof 25483 to the balcony 21011), straight down x ~6000.

## 2. What Dog Days still has
- All five classes are registered and the player movement is made: kl2 vtables ZFFPlayerMovementRappel 0xbb5ebc (ctor
  0x7b5bc0, called at 0x51d2cb, `push 0x10`, size 0x2020), ZFFRappelling 0xb6c648, ZRappellingBox 0xbc23bc (its tick
  0x69aca0 posts the same kind-0x18 record to `[[0xdd265c]+0x15e0]` via 0x452a60), ZRappelCheckPoint 0xbc3e14, ZRopeLnkObj
  0xbc14ec. The movement looks the same slot names up (0x77ac7a ..). Stock Dog Days levels use RappellingBox 0 times,
  RopeLnkObj 0 times, RappelCheckPoint 0 times. NOT KNOWN whether the code path still works (dead code since Dead Men).
- GONE: every `/Movement/Rappelling/*` slot and clip - none of the 21 stock .ANM files has one (`kl_fa_rappel.py facts`).
- Dog Days has a DIFFERENT, level-data rappel for NPCs, and it is the usable one:
  - L07 (`Construction_Area_End`): squads `Squad_Repelling_01..03`, each a `ZSquadScript` with a `MiniCutsceneRout` per
    stage: `005_MiniCutScene_Idle` plays slot `/Level_Specific/L07/Situations/L07_Repelling_Enemies/Repelling_0N_1F` (a
    2-frame hanging pose, flags 0x40) and `010_MiniCutScene_Repel` plays `.../Repelling_0N`, both from a `MiniCutPosObject` whose
    string names `POS_Repelling_0N` of the animation package `Animation/L07/Situations/L07_Construction_Midship_Repelling.zip`;
    rope models (`ROPE`, `ROPE01`, `ROPE02`, ZSTDOBJ with models) are shown by `ActivateGeom` / `DeactivateGeom` + a
    `TriggerDelay2`. The script text is
    `((Actor| Soldier_SnowWolf_01| ((act| ((subt| 1)| (anim| <slot>)| (lefthandik| 0)| (startpos| PosObject)| (blend| 1)| (_dep| ())))))| (Options| Options| ((mode| unbreakable-vulnerable))))`;
    the rout's reference list (`out-link`) hands the squad on to `RunToCover` / `DefendPlayerPos` when the clip ends.
    ZMiniCutsceneRout fields (kl2.json): s script, refs, b, b, I, e, b, b, s, s.
  - L10 (`Backlit_Squad_RapellingSW#01..07`): the same with slots `.../L10_Backlit_Repelling_Snowwolves/Male_01`, `Male_02`
    (97 frames, 7.8 m), L08 / L10 / L11 sets `SnowWolf` also have `/Special_moves/NPC_Moves/SnowWolf_repelling_High | Low`
    (105 frames, 15.9 m / 11.9 m).
  - THE DROPS: `POS_Repelling_01 / 02 / 03` stand at world y 1756 / 1487 / 1300 and the clips' root travel is -1756 /
    -1487 / -1300 (105 / 90 / 82 frames): each is the whole drop from its PosObject to the ground, identity rotation, so a clip's -y IS world
    down. They are ALTERNATIVES (three soldiers hang at three heights), not stages. The root adds up (45.4 m in 277
    frames = 11.1 s against Retomoto's rope of 44.7 m), BUT THE POSES DO NOT JOIN - measured from the clips' keys
    (`kl_fa_rappel.py joins`, 55 shared bones, local rotations, the decoder of kl_animsheet): end of 01 -> start of 02 30.1 degrees
    mean (pelvis 168), 01 -> 03 12.7 (pelvis 171), 02 -> 01 39.6, 02 -> 03 40.9 (pelvis 179), 03 -> 01 21.5, 03 -> 02 32.7. Each clip also
    drifts: 01 ends 1.6 m to one side with the heading unchanged, 02 turns 15 degrees and drifts 1.5 m, 03 turns 53 degrees. The
    `_1F` hang poses are exactly frame 0 of their clips (0.0 degrees); `Repelling_03_1F` is 8.5 degrees from frame 0 of `Repelling_01`,
    `_02_1F` 24.4. The clips have no events and flags 0x10c0 (record bit 8 clear -> "moved by animation", re/climb.md),
    +0x28 = 0 (full body).
  - The sets with the slots: L07 Police, Thug, Glazer, Civilian, Lynch, Kane_NPC, Kane (all five slots name the same five clips).

## 3. The three forms
**A. Bots: a scripted drop by MiniCutsceneRout (Dog Days' own pattern; level data + clips) - ONE clip, not a chain.**
(Review MUST 1: the first version of this note chained 01 -> 02 -> 03 over the whole 44.7 m; `joins` refutes it, see section 2.)
Each heister squad gets one `MiniCutsceneRout` playing `Repelling_01` from one `MiniCutPosObject`, started by the round-start
event and staggered; the idle before it is the hang pose `Repelling_03_1F` (assumed the nearest, 8.5 degrees). The PosObject
is placed from the LANDING, not the roof: `python tools/kl_fa_rappel.py plan Repelling_01 X Y Z [yaw]` -> for the feet at the
balcony row (6000, 21011, 0): yaw 0 gives (5998, 22767, -160), yaw 180 gives (6002, 22767, 160) (the clip ends 1.6 m to its
own side; z must be matched to the START slot of each bot). So the end is ON the row (review MUST 2: the first chain ended 0.7 m
under it) and the drop begins 17.6 m above the balcony, NOT at the roof - the other 27 m of Dead Men's rope are not descended
(no stock clip covers them; a 44.7 m rope would need Dead Men's own `/Movement/Rappelling/*` clips, form C). The rope models of
L07 are not in the build (their package is not): no rope is drawn, the bots hang from nothing for 4.2 s. Class check (review
SHOULD 5, done): L07's `Soldier_SnowWolf_01` is a group of ZFFActor (L07 has 148 ZFFActor and no ZSoldier; the first version
of this note said ZSoldier: wrong) and Retomoto's bots are ZFFActor (99 in the F06 build): the same entity class, so the Actor
head can name a Retomoto bot. NOT shown: the "unbreakable-vulnerable" mode on a bot whose health [Balance] Tough has changed, and
the group-name lookup. DONE here: the clips and slots (`apply`). NOT DONE: the nodes (a kl_fa_author-style insertion of 1 rout
+ 1 PosObject per squad, and the heading). The squads' later orders were timed for a start on the balcony (the blast is NOT touched:
KLTalk.ini byte-equal).
**B. The human.** FOUND IN re/climb.md (table row 'the mini cutscene (C)'), CONTRARY to the first version of this note ('a
human cannot be addressed by data'): a `MiniCutsceneRout` script entry with a `Lynch` head and an `act` task (`anim` = a slot
name, `startpos` = a pos object) makes `ZMiniPlayerActTask` for the player in gamedata slot 0 - put on the pos object (0x82cc40),
collision off, the slot played with its own root motion, the last frame held, input back at the script's end. 755 such scripts
in the 21 stock levels, 38 with a start place, ALL in campaign levels, none in a Fragile Alliance level; int3 at 0x872f70 /
0x5f6df0 when the player's slot byte [player+0x91d] is not 0 or 1; our clips carry no event ids, so the id-5 fault of
re/climb_crash.md cannot happen. So the human's drop may be LEVEL DATA too (B1: the same rout as the bots' with a Lynch head,
Repelling_01, from the PosObject `plan` gives, started at the round-start event - an idea, untested in FA). B2 = the hook part
`klhook/klrappel.c` on the klclimb.c pattern (put him on the place, play the clip, collision off, on at the end) is the fallback and is
NOT written. TIMING (review SHOULD 4, answered by the numbers): the round-start event is 8.4 - 8.8 s BEFORE GO, the blast (16.5 s after
the event) about GO + 8; a 4.2 s drop begun at the event + 2 s ends before GO. Whether the game moves a player in the pre-round at all
is NOT known: the live check shows it. (The 11.1 s chain would have ended about GO + 2.)
**C. Dead Men's free rappel (DM clips + Dog Days' ZFFPlayerMovementRappel).** The most "true" but least known: needs
the 15 DM slots merged (the same machinery, `kl_anmjoin`, event 6 of Jump_End is harmless), a rope the movement can
find (`ZRopeLnkObj` + the box + the player-side search at 0x607420 in DM, its Dog Days twin not located), the
player's input binding `rappel` (the Dog Days binding names exist: 'Rappel' at kl2 0x4f9431), and the HUD prompt;
and a start (who sets `[movement+0x1388]`): none of it is in the level format. Hook job of days; NOT recommended
before A / B have been seen.
RECOMMENDATION: ONE clip, `Repelling_01`, 4.2 s, landing on the balcony row, for the bots (A) and, if B1 loads, for the human; the
crew starts hanging 17.6 m over the balcony and drops to it while the countdown runs, before the blast. This is a shorter rappel than
the owner pictured (Dead Men's whole facade); the whole facade needs form C. If B1/B2 costs too much, the fallback is the present
start (balcony), nothing lost. STATE: NOTHING RAPPELS YET - `apply` is inert, no node is built, B2 is not written.

## 4. What `apply` built and its checks (2026-10-11, all on the file system)
`python tools/kl_fa_rappel.py apply <work>\build\r_tab\DM09x <work>\build\y_rappel\DM09` ->
- `.ANM 21,642,904 -> 21,716,708 bytes (+73,804): 5 clips added in 5 data blocks, slot names 2451 -> 2456, bones 236 (+0),
  poses 36 (+0); 35 lists in 7 sets (Kane, Lynch, Kane_NPC, Lynch_NPC, Thug, Civilian, Swat_02)`; clip sounds: 2 already 0, 3 cleared
  (+0x2C by name in the build's own .SND, none had a same-named record); proofs: reads back byte-identical, `kl_anm.audit`
  clean, the base is a prefix with no list changed, every added list = L07's (name, events + data, bone names, flags),
  no event ids at all in the clips (nothing for kl2 0x637060 to act on), no bone / pose added, slot index sorted.
- Only the `.ANM` member of the archive differs from `r_tab\DM09x` (30 members); the 43 files beside it are copies;
  `KLTalk.ini` byte-equal to `rt_full6\retomoto_full\KLTalk.ini` (`cmp` OK); `dyn.json` / `fed.json` large-block record continued if present.
- `kl_impact.py <out>`: `problems: 0`. `kl_fa_bots_rt.py check <out>`: `RESULT (kl_fa_bots_rt): PASS (0 FAIL, 12 NOTE)`.
  `kl_fa_fedpoints.py check <out>`: `RESULT (kl_fa_fedpoints): PASS (0 FAIL, 8 NOTE); 7 point(s): 7 good`.
  `kl_fa_rappel.py check <out>`: `RESULT (kl_fa_rappel): PASS (0 FAIL)`.
- IT CHANGES NOTHING IN PLAY: no node asks for the slots. The .ANM grew 74 KB (one of the four large blocks; 21.7 MB, still
  far under what loaded before). Not run in the game, so even the load is unproven (`kl_fa_climb`'s merge of the
  same kind loaded).

## 5. Live checks owed (owner away; hook ship_w8 or newer; none needs a code patch)
1. L-R0: load `y_rappel\DM09r` through slot F06 (tree: copy of the tab with this DM09), reach GO, no fault -> the merged .ANM
   (5 clips, 35 list entries, also in Swat_02 / Thug) is accepted. FIRST; nothing else is worth building before it. Do not put the
   build on the owner's tab: it changes nothing visible.
2. L-R1 (needs the form A nodes: ONE squad, one rout `Repelling_01` from the PosObject `plan` gave): the bot hangs, falls 17.6 m and
   lands upright at the row; read its y in the position log (`[Bots] Log=2` `MoveLog=1`): -1756 units in 4.2 s, 160 sideways. The
   heading shows in a picture (yaw 0 or 180: the one that faces the wall).
3. L-R2: the Lynch-head rout (B1) for the human: does the game run it in the pre-round or only after GO, and does input come back.
   Only if it refuses: L-R3 = the hook part B2, `[Rappel] Enable=1 Dry=1` logs the planned places, then Dry=0.
4. L-R4 (one dry probe, review SHOULD 6): ZFFPlayerMovementRappel made and logged without entering it - settles whether form C has
   any code to stand on.

## 6. ASSUMED / not read
- The Dog Days movement code (`ZFFPlayerMovementRappel`, 0x7b5bc0 ..) still works; the entry into it; the DM routine at
  0x607420 (rappel-point search) only seen, not read; the wire of "kind 0x18" in the HUD queue (read: posted by the box; the
  consumer is not located, "icon + prompt" is inferred from the string/ICON names).
- That the L07 clip plays on a Retomoto `ZFFActor` bot under "unbreakable-vulnerable" (same class: shown; the mode and Tough: not),
  and on the human through a Lynch-head rout in a Fragile Alliance level (never run there).
- `Repelling_03_1F` as the best idle before `Repelling_01` (8.5 degrees by the keys; nobody has looked at it).
- The heading (PosObject yaw 0 or 180 against the wall) and the sign convention of `plan`'s yaw (assumed x' = x cos + z sin).
- The pose maths of `joins` (local bone rotations, mean angle; the quaternion decoder of kl_animsheet, checked there against the
  skeleton): a mean of 12.7 .. 40.9 degrees with the pelvis 130 .. 179 is a clear snap whatever the small errors; a blend (`blend| 1`
  in the script) might soften one, NOT shown.
- Whether the bots' later orders fit; the rope (visual) and the camera (the DM camera boxes are not carried).

## 7. Review of 2026-10-11 (re/rappel_review.md): each point
MUST 1 (chain contradicts the evidence): DONE - measured (`joins`), the chain is REFUTED and removed; one clip. MUST 2 (end 0.7 m off,
sideways drift, heading): DONE - `plan` lands the feet on the row exactly and adds the 1.6 m; the heading stays an open parameter and
a requirement of the nodes. MUST 3 (nothing rappels): stated above and in the report. SHOULD 4 (timing): answered by the numbers, the
pre-round question left to the live check. SHOULD 5 (bot class): DONE for the class (both ZFFActor), the mode is open. SHOULD 6
(form C probe): written down as L-R4, not run. SHOULD 7 (naming): the clip is `Repilling_01` in the file; `clips_of` normalises it
and `apply` never used the spelling. SHOULD 8 (merge touches Swat_02 / Thug): L-R0 first, not on the tab. FOUND ON THE WAY: re/climb.md
already has the Lynch-head act for the player, so the first version's 'hook only' for the human was wrong.
