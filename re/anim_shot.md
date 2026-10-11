# What a heister plays when he is shot - the picture sheets (track R5, 2026-10-11)

Owner, after watching `Flop=1` (`Hero_Torso_Back`) in run G1_DM03_flop: *'nah i meant to say that looks like the dead men
belly flop, do you not have the animations for the ai heisters is my point like cant you just dig for the ones when
theyre shot at and port them to the current character?'* Three guesses were wrong, so this track SHOWS him every clip
and lets him point at a number. **Offline; pictures only; nothing ran in the game; nothing was built for the game.**
FILE = the `.ANM` / `.prm` / `.prp` of stock F01, F07 and the five tab builds; READ (R2 / R3) = kl2.exe as
re/player_down.md 9 and 10 read it (not read again here); NEW = read or measured by this track.

## 0. The short answer

- **There is nothing to port.** The AI heisters (`Kane_NPC` / `Lynch_NPC` sets) and the human (`Kane` / `Lynch`) hold the
  SAME clips for every `/Damage` slot but two: `/Damage/Death/Die_On_Spot` (another clip each) and `/Damage/Hit/Front/Front`
  (a 7-frame twitch only the NPC sets have). 664 of 2,419 slots differ between `Kane` and `Kane_NPC`: `/Weapon_Handling`
  473, `/Cover` 122, `/Movement` 63 (among them `Fall/Fall_1m`, `Fall_2m`, `Walk/Forward_Wounded`), `/Special_moves` 4 (the
  heals), `/Damage` 2 (FILE, counted again in the fix round; the same in F01, F07 and all five tab builds). Every body the
  human can wear - the eight heisters and the sixteen wardrobe bodies, Dead Men's included - has the same 58 body bones by
  name (all five tab builds), and on `z_cover3\M03` the review tested the 56 bones the ten candidate clips move (41 42 43
  12 7 25 26 71 6 20) against all 24 bodies: none lacks one, same parents, bone lengths within 0.2. So each numbered clip
  below can be played on the human as it lies in the level.
- **What differs is which clip the CODE picks**, not what the files hold: a bot that is hit and lives draws from
  `/Damage/Impact/FB/...`, a bot that dies from `/Damage/Wounded/<stance>/...` or `/Damage/Death/...`; the human's knock-down
  draws from `/Damage/Down_Not_Dead/...` (stock) or whatever slot `kldown.c`'s `FlopFallSlot` names.
- **The sheets**: `<work>\research\animsheet\overview.png` (105 numbered clips, 3972 x 10546; numbers 1 - 95 are the first
  round's, 96 - 105 are new), the same rows by family in `A_death.png` .. `F_cover.png` and `I_upper.png`, three closer
  looks `G_zoom_belly.png` (side view, 12 frames), `H_zoom_thrown.png` (the first 1.8 s) and `J_zoom_knee.png` (side view,
  the rise only), `legend.txt`. Every row now carries a green line 'pose:' = STANDS / KNEELS / BELLY / BACK / SIDE / bent
  by frame range, MEASURED from the keys (section 5), not read off the picture.
  Made by `python tools/kl_animsheet.py shot F01 <folder>` (65 s).
- **The match** (corrected after the review, section 3): picture 1 (flat on the belly) fits every clip with a belly
  phase and cannot be narrowed from a still; picture 2 (upright on the knees, rifle up) fits ONE clip well: **71**
  `Rise_From_Stomach` (an upright kneel held 1.5 s) - the get-up of `Flop=2`, which the owner has never been shown; the
  clips 41 and 9 / 12 have NO upright kneel in their rise, 25 has 0.3 s of one. Picture 3 (a standing man, arm thrown
  up) fits best the upper-body flinches **98 / 99** (new on the sheet), then 29, then the death clips 20 / 6; it is not
  settled.

## 1. Who wears which set, and what the code picks

| who | set (`ZLNKOBJ[2]`) | model | FILE |
|---|---|---|---|
| the human, `Heroes!Hero_0N\Ground` (ZFFPlayer) | `Kane` (N = 1 3 5 7) / `Lynch` (2 4 6 8) | heister N | F01, F07, all five tab builds |
| a stock AI heister AND a bot of our builds, `...merc_bot_squad!Squad#0N\Glazer_Bodyguard_0N\Ground` (ZFFActor) | `Kane_NPC` (3 5 7) / `Lynch_NPC` (2 4 6 8) | the same model as hero N | the same seven, 3 + 4 actors each |

The pickers (READ, R2 / R3; addresses as re/player_down.md 9.1 / 10.1 give them):

| what happens to the AI heister | routine | slots | sheet numbers |
|---|---|---|---|
| hit, lives, full body | `ZGeneric` 0x4aba20 (slot ids built by 0x5681d0): full body only when `[generic+0x98]` is 2 and the clip's root movement has room; 'Running' above 250 a second | `/Damage/Impact/FB/Running/Front_Torso`, `.../Standing/Front_<part>`, `.../Crouched/...`, `.../Cover_*/...` | **41 42 43**; 27 - 34; 35 - 39; 78 - 95 |
| hit, lives, upper body only | the same | `/Damage/Impact/UB/...` (39 slots, 10 clips of 14 - 19 frames, the flash bang's 81): `Standing/Front|Back|Left|Right_Torso` and the covers' fire positions = 97 98 99 100; `Crouched/...` and the covers' idle positions = 101 102 103 104; `Running/...` (all four) = 105; flash bang 96 | **96 - 105** (page I; drawn over the rest legs - in the game the legs keep what they were doing) |
| dies, no ragdoll | death chooser 0x72ab60 | `/Damage/Death/Die_Forward` (shot from behind), `Die_Backwards` (from the front), `Die_On_Spot` | 5, 6, 2 |
| dies, 'wounded' death | `ZWounded` 0x865180: stance x front / back x 'Merc' | `/Damage/Wounded/Running|Crouched|Standing/Torso/Merc_Front|Merc_Back|Front_01|Back_01`, `.../Standing/Front_Head` | 7 - 22 (the 'Merc' words: 12 13 14, 17 18, 19 20 21) |
| dies, ragdoll | events 36 of two 2-frame clips | `/Damage/Death/Standing`, `Instant_Ragdoll` | 3, 4 (the ragdoll itself cannot be drawn) |
| 'down not dead' (NPC state graph 0x730be0; never seen for a bot in Arcade: 235 of 235 stay dead) | `ZDownNotDeadNPC` | `/Damage/Down_Not_Dead/...` | 45 - 59 |
| the human's stock knock-down | `ZFFPlayerMovementProne` 0x750900 / 0x5d6060 | `Down_Not_Dead_Get_Down`, loop, `_Get_Up` | 48 (47 without a weapon), 45, 46 |
| the human's own death | `ZFFPlayerMovementDie` 0x789b10 | `/Damage/Wounded/Hero_Torso_F`, `Stand_To_Crouch_Wounded`, `Down_Not_Dead_wounded` | 25 26, 23, 58 |

NOT ESTABLISHED (as in R3): when an AI heister's `[generic+0x98]` is 2; what cuts a 'wounded' death at its event 8.
So WHICH of these a bot really plays in a round is a reading, not a sight. Live check proposed by the review (for the
lead; nothing was built for it): at every health loss of an AI heister (klbot's `Log=2` has the moment) log the clip
number his full-body channel plays 0.2 s and 1 s later; clip numbers are global and section 4 gives the names.

**Left off the sheets** (slots a heister set holds for a man who is hurt; none looks like the owner's pictures):
`/Damage/Death/Dead_Loop_01..03` (2-frame lying poses of the dead); `/Damage/Down_Not_Dead/Down_Not_Dead_Crawl_Left|Right
(_Sprint)`, `..._Crawl_Over_Item_*`, `Down_Not_Dead_Over_Item` (sideways crawls of the stock knock-down, 61 - 167 frames)
and its upper-body `Aim_*` / `Recoil*` poses; `/Movement/Fall/Fall_High_Enter|Loop|Impact` (the fatal fall, 14 / 61 / 8
frames); `/CloseCombat/Dog/ImpactFront|Back_Victim` (13 / 28 frames, a man hit by hand); `/Close_Combat/Engage/
Human_Shield_Victim_Death`, `Execution_Human_Shield_Victim`, `Throw_Human_Shield_Victim` and `/Close_Combat/
Human_Shield_Victim/Thug_Die|Thug_Dead` + the struggles (a man held as a shield); `/Heal/Heal_Player_Character/
Healer|Patient` (30 frames); `/Face/Pain_01`, `/Face/Die_01` (face only).

**Which clip of a slot** (kl2 0x7c6750, READ by R3; NEW: worked out per slot by `kl_animsheet.py list`): bits 0-2 of a
pair's condition word are weights. So:

| slot | the draw |
|---|---|
| `/Damage/Impact/FB/Running/Front_Torso` | **60 % #43** (a stumble, 2.1 s, he stays up), **20 % #41** (dive, belly 22 - 169, up over all fours), **20 % #42** (goes down turning: on his back for frames 21 - 39 only, on his SIDE 40 - 135, belly 136 - 171, up) |
| `/Damage/Impact/FB/Standing/Front_Torso` | 73 % #27, 27 % #28 (flinches) |
| `/Damage/Wounded/Running/Torso/Front_01` | 50 % #7, 50 % #8; `Merc_Front`: 50 % #13, 50 % #14 |
| `/Damage/Wounded/Running/Torso/Back_01` | a third each #9, #10, #11; `Merc_Back`: #12 always |
| `/Damage/Wounded/Standing/Torso/Front_01` and `Merc_Front` | 50 % #20, 50 % #21 |
| `/Damage/Wounded/Hero_Torso_F` | 50 % #25, 50 % #26 |

## 2. The sheet's legend

One row a clip (one per clip DATA: aliases of one data block are one row). Heister 1, masked, posed by the clip's keys
on the whole skeleton, skinned and textured; 8 frames spread evenly over the clip (12 on G and H), the frame number
and second under each; the grey line is his floor; he is centred in every panel, so travel is in the text ('root:');
**no weapon is drawn**, no ragdoll, no blend. Orange text = a clip only one side's sets have. Events: 7 = he has
landed, 8 = the end of lying (the rise begins), 31 = weapon, 36 = ragdoll, 2 / 5 / 6 = the stock fall's own.

| numbers | page | what |
|---|---|---|
| 1 - 6 | A | death clips: `Die_On_Spot_Player` (human only), `Die_On_Spot` (NPC only), the two ragdoll starters, **5 `Die_Forward`** (`Flop=2`'s dive), **6 `Die_Backwards`** |
| 7 - 26 | B | the 'Wounded' family: running 7 - 14, crouched 15 - 18, standing 19 - 21, head shot 22, to a crouch 23 24, **25 `Hero_Torso_Back`** (`Flop=1`, what the owner watched), 26 `Hero_Torso_Front` |
| 27 - 44 | C | hit and lives: standing flinches 27 - 34, crouched 35 - 39, flash bang 40, **running 41 42 43**, 44 `Hit#Front` (NPC only) |
| 45 - 59 | D | 'down not dead': loop 45, get-up 46, **48 the stock player knock-down** ('the gun one'; 47 its no-weapon twin), crawl back 49 57, on the spot 50 - 52, compact 53 - 56, 58, 59 from a crouch |
| 60 - 77 | E | heal 60 - 65 (60 62 human only, 61 63 NPC only), wounded walk 66 67, wounded stand 68 (69 is a stray pair of that slot), `Rise_From_Back` 70, **71 `Rise_From_Stomach`** (`Flop=2`'s get-up), crawl 72 - 75, drag 76 77 |
| 78 - 95 | F | flinches at a cover, 15 - 48 frames, he stays put |
| 96 - 105 | I | upper-body flinches (NEW in the fix round): flash bang 96; standing / firing 97 front, **98 back**, **99 left**, 100 right; crouched / idle at a cover 101 front, 102 back, 103 left, 104 right (these four carry event 10); running 105 |

Closer looks, same numbers: G (belly clips from the side: 5 7 8 9 10 12 13 14 25 41 42 43 71 72 75), H (the first 1.8 s:
6 19 20 21 22 25 26 27 28 29 32 48 and 97 - 104), J (the rise only, from the side: 10 12 25 41 46 70 71).
Not drawn: see 'Left off the sheets' in section 1.

## 3. The match with the owner's three pictures

First round's match was wrong in two places (review M1, M2); this is the corrected one. The frame ranges are the tool's
measured 'pose:' ranges (`trunk`), not read off the pictures; the pictures J / H / I were looked at again and agree.

**Picture 1 - flat on the belly, head toward the camera, elbows out, rifle on the floor in front.** Every clip with a
BELLY phase fits and one still does not separate them:

| clip | lies chest down | then |
|---|---|---|
| **71** `Get_Up_From_Stomach` (`/Movement/Rise/Rise_From_Stomach`) | 0 - 93 (3.7 s; it STARTS lying) | all fours 94 - 144, **upright kneel 145 - 182**, stands 183 |
| 70 `Hero_Die_End` (`/Movement/Rise/Rise_From_Back` - the clip under that name starts chest DOWN) | 0 - 35 | bent 36 - 57, upright kneel 58 - 65, ends crouched |
| 41 = 7 = 13 `Running_torso_Front_3` / `(Merc_)Run_Torso_Front_03` | 22 - 169 (5.9 s) | all fours 170 - 206, stands 207 (41 only; 7 / 13 end bent) - no upright kneel |
| 9 = 12 `(Merc_)Run_Torso_Back_03` | 25 - 36, 44 - 171 | all fours / bent 172 - 232, stands 233 - no upright kneel |
| 25 `Hero_Torso_Back` (`Flop=1`, watched) | 16 - 27, 36 - 151 | bent 152 - 173, upright kneel 174 - 181 (0.3 s), stands 183 |
| 10 `Run_Torso_Back_02` | 42 - 58, 71 - 98 | bent 99 - 121, upright kneel 122 - 130 (0.4 s), stands 132 |
| 5 `Die_Forward` (`Flop=2`'s dive) | 26 - 49 (the end; no rise) | - |

**Picture 2 - the same man, same spot, UPRIGHT on his knees (both knees look down), rifle held up in front.**
'Upright kneel' = pelvis-head line over 0.8 up, pelvis under 65, a knee under 22 (the review's limits, now
`pose_word`). Best: **71, frames 145 - 182** - the only clip that HOLDS it (1.5 s; trunk 0.93 - 0.98, pelvis 47, both
knees low, head 108 by the review's numbers; J_zoom_knee.png frames 144 - 176). Then the passing kneels of 0.3 - 0.4 s:
70 (58 - 65), 25 (174 - 181), 10 (122 - 130). **41 and 9 / 12 have none in their rise** (they push up over hands and
knees and straight to standing) - the first round's frames for them (156 - 176, 195 - 216) showed a man on all fours
and were wrong. Every clip that throws a standing man down also passes a kneel of 0.2 - 0.3 s ON THE WAY DOWN (41:
11 - 16, 25: 3 - 9, 5: 13 - 19, 6: 23 - 28); that is before the belly, not after. Still open: picture 2 could be a
crouched man aiming and no rise at all (the crouched stance was not drawn).

**Pictures 1 + 2 together** (one man, one place, belly then knees) are therefore best read as **71 `Rise_From_Stomach`
after some fall onto the belly** - which is `Flop=2`'s get-up, the one of the three guesses the owner has NOT been
shown - rather than as one clip 41 / 12 / 25. Which fall precedes it cannot be told from the stills. For the lead:
'a belly fall, then 71' is another thing to build than 'one clip 41 / 12'.

**Picture 3 - a standing man seen from behind-left, legs apart, his right arm thrown up; the HUD text is the warning for
shooting a fellow heister, and nothing shows that he dies.**

| candidate | why | against |
|---|---|---|
| **98** `Shoot_Pose_Impact_Back_UB` (`/Damage/Impact/UB/Standing/Back_Torso`) | an arm thrown up over the head at frames 3 - 6 (0.1 - 0.25 s); he is hit from behind, as the camera stands | upper body only: the wide legs are then his own movement |
| **99** `Shoot_Pose_Impact_Left_UB` (`.../Standing/Left_Torso`) | an arm flung up and out at frames 1 - 4 | the same |
| 102 / 103 `Stand_impact_back|left_UB` | the same gestures | their slots are `Crouched/...` and the covers' idle positions, and he stands in the open |
| 29 `Front_Left_Shoulder` (full body, `/Damage/Impact/FB/Standing/Front_Left_Arm`, the 0.5-weight pair) | arm up, a step back and aside (root -0.28 m, -0.30 m), he stays up | a hit from the FRONT |
| 20 `Stand_Torso_Front_02` frames 4 - 12, 6 `Die_Backwards` frames 4 - 8 | arms flung, trunk arched | death clips; he goes down by frame 28 / 33 |
| a ragdoll (3 / 4) | cannot be drawn | - |

Picture 3 is NOT settled: 98 / 99 are the likeliest by gesture and by what a living standing heister plays, by eye only.

**Plainly:** of the two clips already tried, 25 fits picture 1 and only brushes picture 2; `Flop=2`'s second half (71)
is the best fit for picture 2 and its first half (5) is a death dive the owner rejected unseen. What an AI heister
plays that the human has never been given: the RUNNING falls **41** (alive, one draw in five of
`/Damage/Impact/FB/Running/Front_Torso`) and **12 / 13** (killed while running) - a 3.0 - 3.3 m dive against 25's
0.66 m - and the upper-body flinches 97 - 105. None of the candidates is a clip only the NPC sets have. The stock
knock-down (48) is on the back.

## 4. Porting facts (nothing was built)

- **In the human's sets already, under the same slot names**: every clip named in section 3. Clip numbers in all five
  tab builds and F07 (the builds carry F07's animation table; in stock F01 the numbers differ): 41 = clip **770**,
  42 = 769, 43 = 768 (slot id 1801); 12 = clip **719** (`.../Running/Torso/Merc_Back`, slot id 1768, ONE pair);
  7 = 715, 8 = 714 (slot id 1766); 25 = 731, 26 = 730 (slot id 1775); 71 = 701 (slot id 1755); 6 = 737 (slot id 1781).
  NEW (read on `z_cover3\M03` and `z_rooms\retomoto_full`, the four sets alike): 70 = clip **700** (`Rise_From_Back`, slot
  id 1754); 97 98 99 100 = clips 775 777 776 778 (slot ids 1804 1806 1805 1807, `UB/Standing/Front|Back|Left|Right_Torso`);
  101 - 104 = 780 - 783 (slot ids 1809 - 1812, `UB/Crouched/...`); 105 = 784 (slot ids 1837 - 1840); 29 = 743 (slot id
  1786, with 30 = 742).
- **'A belly fall, then 71'** is what `Flop=2` already does with 5 as the fall. Whether another fall (25, 41, 12) can be
  cut at its event 8 into 71 without a jump was NOT measured (71's first frame lies chest down, head 14 over the floor;
  the falls' lying poses were not compared bone by bone with it), and how `kldown.c` chains the two was not read again.
- **With today's `kldown.c`, keys only**: `FlopFallSlot=/Damage/Wounded/Running/Torso/Merc_Back` plays 12 every time
  (one pair, no draw). `FlopFallSlot=/Damage/Impact/FB/Running/Front_Torso` would give the stumble 43 three times in
  five and the roll onto the back 42 once in five: `FlopBelly` re-points only pairs that are NOT thrown forward (record
  +0x18 z not under -20), and all three go forward - so 41 alone needs the pair list pointed at clip 770 directly
  (`FlopBelly`'s write with a chosen number; clip records are global, `[[0x1546f6c]] + number x 0x68`), which would
  also change what a BOT of that set draws for the slot (the list is the set's, not the player's). A slot of the
  human's own with one pair (the level step R3 left undone, `tools/kl_fa_flop.py`) avoids that.
- **Skeleton** (NEW, FILE): 58 body bones (face, attacher and muscle helpers aside), the same names in heisters 1 - 8
  and in the sixteen wardrobe bodies of `z_cover3\M03`, `z_route3\M01`, `z_loot3\M02`, `z_route\M06`,
  `z_rooms\retomoto_full` (J.C. .. Mitchel and the eight Dead Men bodies Kane .. Hutchison; 96 - 104 bones in all).
  Per clip: this track tested 25's 55 bones; the REVIEW tested the 56 bones the ten candidates 41 42 43 12 7 25 26 71
  6 20 move against the 24 bodies of `z_cover3\M03` (present, same parent, length within 0.2). The other four builds
  have the name comparison only; 70 and the upper-body clips 96 - 105 were not tested per clip. A clip addresses bones
  by the level's animation bone number, which `kl_chars check` already holds every skeleton to.
- **Events the player's action would act on** (NEW: the switch of kl2 0x637060 read from the exe's two tables,
  0x637314 / 0x6372e0): it acts on ids 5, 9 - 11, 20, 21, 24 - 35, 42, 48 - 51, 53. Of the candidates' events (0, 2, 6,
  7, 8, 31) only **31** is one (case 0x637147, with 10 and 30 - 35: the weapon item, as R3 read) - carried by 41 (at
  43), 42 (53), 43 (18), 7 / 13 (43), 9 / 12 (7), 25 (1), 20 (9), 19 (45). `kldown.c` lets 7, 8 and 31 through for
  `Flop=1` already and G1 ran with 25's; id 5 (the climb's crash) is in none of them (it is in 47 / 48 / 59, the stock
  fall's own, and 61). 71 and 70 carry none but 70's 8 at 0. **The four `Stand_impact_*_UB` clips 101 - 104 carry
  event 10 at frame 8, which the action DOES act on** (the same case 0x637147 as 31); 96 - 100 and 105 carry no event.
- **Root movement**: 41 goes 3.01 m forward (12: 3.28 m) in its first 40 frames, 25 only 0.66 m, 71 1.26 m while he
  gets up. The clip record's root vector agrees with the keys (review: 71 (-12, 0, -126), 5 (0, 0, -88)). On a man
  knocked down while STANDING the running clips slide him 3 m; that collision stops it like any movement of his is
  ASSUMED - a wall or a ledge in front of him is where it would show (a live check for whoever builds it).

## 5. The tool

`tools/kl_animsheet.py` (new; docstring = what is read and how sure): `list <level> [regex]` (the slot table per set
with the draw's shares), `shot <level> <folder>` (these sheets), `sheet <level> <out.png> <regex> ...` (any clips;
`--frames`, `--view side|quarter|front`, `--to F` (below 0: the last |F| per cent), `--hero N`), `trunk <level> <clip
regex> ...` (NEW: no picture - per clip the pose by frame ranges and the numbers behind it: y of the pelvis-head line,
y of the chest's normal, heights of pelvis / head / lower knee over the GROUND bone; `pose_word` holds the limits; the
sheets print the same in green), `check <level>` (a standing clip against the skeleton's rest places, and NEW three
proofs by clip NAME: `Get_Up_From_Stomach` starts chest down (-0.92), `Die_Backwards` ends chest up (+1.00),
`Die_Forward` ends chest down (-0.90); last line `PASS: the pose reader fits this skeleton (standing clip within 25 of
the rest pose; from-stomach starts chest down, backwards ends chest up, forward ends chest down)`). Pose = each tracked bone's
key as its local rotation and place under its parent in the model's own hierarchy; untracked helpers keep their rest
place; the forearm twist bones follow the forearm. In Git Bash set `MSYS_NO_PATHCONV=1` (a regex beginning with `/`
is rewritten as a path otherwise).

## 6. ASSUMED / not done

- ASSUMED: the game composes a pose as this does (it agrees with the rest matrices, with the clip names - 'from
  stomach' starts chest down - and with R3's reviewer's own reading); 'front' view is not a true front.
  The 3 m of the running clips is stopped by collision (section 4). `pose_word`'s limits are a choice: 'KNEELS' is an
  upright kneel OR a deep crouch (the cover flinches 94 / 95 read KNEELS), 'bent' is everything in between.
- NOT DONE: the code was not read again (section 1's pickers are R2 / R3's); `[generic+0x98]`; the weapon in the
  hands; a front view good enough to tell 41, 9 and 25 apart on the floor; the crouched stance beside picture 2; the
  join of a fall's lying pose to 71's first frame; anything for the game (no hook change, no level build). The next
  step is the owner's number from the overview, and beside it the review's log line (section 1) for the lead.
- FIX ROUND (after re/anim_shot_review.md): M1, M2 and SHOULD 1 - 7 all applied; none was refuted.
