# Review of track R5 (re/anim_shot.md, tools/kl_animsheet.py, the sheets) - 2026-10-11

Adversarial review. Offline; nothing ran in the game; the worker's files were not changed. My scripts and one extra
sheet are in the session scratchpad, folder `r5rev` (`rev1.py` slots and sets, `rev2.py` / `rev4.py` trunk direction per
frame from the keys, `rev3.py` clip numbers and skeletons on a tab build, `ub.png`).

## Verdict: ACCEPT WITH FIXES

The renders are right and the porting facts hold from the files. Two statements of the MATCH do not hold and must be
put right before the sheet and its 'best fit' go to the owner: the frames given for picture 2, and the candidates for
picture 3.

## What was tried and HOLDS

| claim | how it was checked | result |
|---|---|---|
| who wears which set | `kl_chars.person` on every ZFFPlayer / ZFFActor of stock F01, `z_cover3\M03`, `z_rooms\retomoto_full` | heroes 1 3 5 7 `Kane`, 2 4 6 8 `Lynch`; bots 3 5 7 `Kane_NPC`, 2 4 6 8 `Lynch_NPC`; a bot has hero N's model. (F01's `RespawnPolice#01..08` are ZFFPlayer with `Lynch` too.) |
| belly is belly, up is up | from the keys, without the renderer: chest normal (shoulder line x pelvis-head line, sign fixed by the toes at rest) and the pelvis-head line against +y, 12 frames a clip | `Get_Up_From_Stomach` starts chest.y -0.92 (belly), `Die_Backwards` ends +1.00 (back), the stock `Down_Not_Dead_Get_Down` +0.98 (back), `Die_Forward` -0.90; #41 chest.y -1.00 for frames 39 - 78, #25 -0.95 for 50 - 118, #12 -0.92 for 65 - 108. Every clip starts and ends upright (0.9 - 1.0). Rest pose: head y 163, pelvis 96, foot 10 = y is up; forward is -z |
| frame order | every track's frame table strictly increasing, the last key = frames - 1, in all nine clips looked at | holds |
| the draw's shares | kl2 0x7c6750 read again: a pair is a candidate when its word's bits 3.. are all in the caller's mask AND equal the first accepted pair's; weight 1.0, bit 2 -> `[0xb4c788]` = 0.1, bit 1 x `[0xb4ed98]` = 0.33, bit 0 x `[0xb35790]` = 0.5; the list ends after the pair whose word is 0 | 60 / 20 / 20 for `Running/Front_Torso`, 50 / 50 for `Hero_Torso_F`, #12 alone: hold |
| clip numbers and slot ids in the builds | `z_cover3\M03`: names -> numbers, slot lists of the four sets | 770 / 769 / 768 (slot 1801), 719 (1768), 715, 731 / 730 (1775), 701 (1755), 737 (1781): hold; the four sets' lists are identical for these slots |
| skeleton | `z_cover3\M03`: TEN clips (41 42 43 12 7 25 26 71 6 20; 56 bones tracked in all) against heroes 1 - 8 and the 16 wardrobe roots: bone present, parent's name, distance to the parent | none lacks a bone, no other parent, lengths within 0.2. More than the worker showed (he tested 25's bones only). The other four builds were not done again |
| events the action acts on | compared with re/climb_crash.md's decoded table of 0x637060 | the same ids (5, 9 - 11, 20, 21, 24 - 35, 42, 48 - 51, 53); of the candidates' only 31 |
| 664 of the slots differ, two under `/Damage` | counted | 664; `/Damage/Death/Die_On_Spot` and `/Damage/Hit/Front/Front` only |

## MUST

**M1. The frames given for picture 2 are wrong for 41 and 9 / 12, and late for 25; the one clip with a held upright
kneel is 71.** Picture 2 is a man upright on a knee with the rifle shouldered. From the keys (`rev4.py`: pelvis-head
line's y; 'upright kneel' = over 0.8 with the pelvis under 65 and a knee under 22):

| clip | the doc says | the keys say |
|---|---|---|
| 41 `Running_torso_Front_3` | 156 - 176, 'trunk upright' | trunk y -0.13 at 150, +0.13 at 165, +0.34 at 180, +0.43 at 195, 0.89 at 210: on all fours, then straight up. NO upright kneel anywhere in the rise (the sheet G shows the same: frame 176 is on hands and knees) |
| 9 / 12 `(Merc_)Run_Torso_Back_03` | 195 - 216 | +0.37 .. +0.48 from 187 to 221, 0.95 at 238: none in the rise |
| 25 `Hero_Torso_Back` | 151 - 168 | +0.18 at 143, +0.41 at 156, +0.53 at 169; upright kneel only 174 - 181 (0.3 s) |
| 71 `Get_Up_From_Stomach` | 128 - 164 ('also fits') | **upright kneel 145 - 182 = 1.5 s** (trunk 0.93 - 0.98, pelvis 47, both knees low, head 108) |
| 10 `Run_Torso_Back_02` | not named | upright kneel 122 - 130 |

So 'pictures 1 and 2 are 41 / 7 / 13, 9 / 12 or 25 - the same lying pose and the same rise' cannot stand as written: the
lying pose yes, the knee of picture 2 no. The best fit for picture 2 is **71** (`/Movement/Rise/Rise_From_Stomach`, the
get-up of `Flop=2`, which the owner has never been shown), then 25's last eight frames. Correct section 0, section 3
and the report; tell the lead, because 'picture 1 then 71' is a different thing to build than 'one clip 41 / 12'.
(Still open either way: picture 2 could be a crouched man aiming and no rise at all.)

**M2. Picture 3: the ten upper-body impact clips were left out, and they are what a standing heister plays when he is
hit and lives.** The HUD text of picture 3 is the warning for shooting a fellow heister; nothing shows that he dies,
yet both candidates named (20, 6) are death clips. I drew the ten with the worker's own tool (`sheet F01 ub.png
'^/Damage/Impact/UB/'`): `Shoot_Pose_Impact_Back_UB`, `Shoot_Pose_Impact_Left_UB`, `Stand_impact_back_UB` and
`Stand_impact_left_UB` throw an arm up and out within 0.1 - 0.2 s, as picture 3 does; the full-body #29
`Front_Left_Shoulder` (already on sheet H) does too. Put the ten on the overview with numbers (an 'upper body over a
standing pose' page) and name them and #29 for picture 3, or say that picture 3 is not matched. Note for a port: the
four `Stand_impact_*_UB` carry event 10 at frame 8, which the action DOES act on (case 0x637147).

## SHOULD

1. **#42 is 'onto his side', not 'onto his back'.** Frames 20 - 119: trunk flat, chest.y +0.49, +0.46, 0.00, -0.22,
   -0.17, +0.08 (sideways), then belly (-0.75 .. -0.99) from 139 and up. Report, section 1's table and the legend.
2. **Section 0 says the 664 differing slots are 'all of them cover, weapon handling and shoot poses'.** They are
   `/Weapon_Handling` 473, `/Cover` 122, `/Movement` 63 (among them `Fall/Fall_1m`, `Fall_2m`, `Walk/Forward_Wounded`),
   `/Special_moves` 4 (the heals), `/Damage` 2. The report's wording ('the largest groups') is right; the doc is not.
3. **The list is not 'complete' as titled: say what was left out.** Slots a heister set holds that are neither drawn
   nor named: `/Damage/Death/Dead_Loop_01..03` (the 2-frame lying poses of the dead), `/Damage/Down_Not_Dead/
   Down_Not_Dead_Crawl_Left|Right(_Sprint)` and `_Over_Item`, `/Movement/Fall/Fall_High_Enter|Loop|Impact` (the fatal
   fall), `/CloseCombat/Dog/Impact*_Victim` (13 / 28 frames, a man hit by hand), `/Close_Combat/Engage/
   Human_Shield_Victim_Death` and `/Close_Combat/Human_Shield_Victim/Thug_Die|Thug_Dead`, `/Heal/Heal_Player_Character/
   Healer|Patient`, `/Face/Pain_01`, `/Face/Die_01`. None looks like the owner's pictures; one line each is enough.
4. **Which of these a bot really plays in a round is still a reading, not a sight** (`[generic+0x98]`, what cuts a
   'wounded' death at event 8 - both NOT ESTABLISHED, as the doc says). A log line in the game would settle it faster
   than the owner's finger: at every health loss of an AI heister (klbot's `Log=2` already has the moment) the clip
   number his full-body channel plays, 0.2 s and 1 s later; clip numbers are global, the sheet's legend gives the
   names. Suggested as the next live check beside the owner's number.
5. **The 3 m of the running clips**: the clip record's root vector agrees with the keys (`Get_Up_From_Stomach`
   (-12, 0, -126), `Die_Forward` (0, 0, -88)); 'stopped by collision' stays ASSUMED. A knocked-down man at a wall or
   a ledge is where it would show.
6. **The skeleton sentence** can now say 'the 56 bones the ten candidate clips move' for `z_cover3\M03` (my run);
   the worker's own test was 25 only. The other four builds: his name comparison, not repeated per clip.
7. `check` proves only a standing clip against the rest pose. Add the two cheap proofs used here to the tool so the
   next sheet is checked by itself: `Rise_From_Stomach` must start chest down, `Die_Backwards` must end chest up.

## Not checked by this review

The pickers' addresses (0x4aba20, 0x72ab60, 0x865180, 0x730be0, 0x789b10: R2 / R3's readings, reviewed there); the
rotation-key unpacking against kl2 0x834170 (taken from the tool; every pose it gives is anatomically whole and agrees
with the clip names, which a wrong unpacking would not survive); `kldown.c`'s behaviour with
`FlopFallSlot=.../Merc_Back` (the key exists; one pair, thrown forward, so `FlopBelly` leaves it - by reading only);
sheets C, E, F and the overview were not looked at frame by frame.
