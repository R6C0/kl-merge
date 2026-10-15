# Adrenaline shot animation (worker 'syringe', 2026-10-15) - to become re/adrenaline_anim.md

Owner: *'what animation plays for when they adrenaline you - I want it to be the Dead Men revive where they get a syringe whilst kneeling'*.
Today (kladren.c v76): none. **Offline; nothing below has run in the game.** FILE = measured in .ANM files; EXE = read in kl2.exe 0490 / kaneandlynch.exe (objdump).

## 1. The clips (FILE)
| clip (`anim:Special_Moves/Heal_Wounded#...`) | slot | frames | events | sets | where |
|---|---|---|---|---|---|
| `Heal_Wounded_01` | `/Special_moves/Heal_wounded` | 55 (2.2 s) | none | players (DM PlayerCharacter, Lynch_Coop; DD Kane, Lynch) | all 20 DM levels; F01 F07 L02 and builds DM01 DM02 DM03 DM03A DM05A DM06 DM09 |
| `Heal_Wounded_01_Low` | `/Special_moves/Heal_Wounded_Low` | 55 | none | players | same |
| `Heal_Wounded_NPC` | `/Special_moves/Heal_wounded` | 73 (2.9 s) | 5 @ 0, 5 @ 18 | every NPC set (DM 13, DD Kane_NPC, Lynch_NPC, Police, Thug ...) | same |
| `Heal_Wounded_NPC_Low` | `/Special_moves/Heal_Wounded_Low` | 73 | none | NPC sets | same |
| `Get_Up_From_Stomach` | `/Movement/Rise/Rise_From_Stomach` | 202 | none | all | same (kldown Flop=2's get-up) |
| DD only: `Heal_Down_no_dead` / `_Crouch` | `/Special_moves/Heal_Down_not_dead` / `.._no_dead_Crouch` | 19 / 22 | none | all | DD + builds |
| DD only: `Heal/Heal_Player_Character#Healer` / `#Patient` | `/Heal/Heal_Player_Character/Healer` / `Patient` | 30 / 30 | none | all | DD + builds (a paired heal; no code reference found) |
| level-specific (cut scenes, not reusable): `M14_Carry_Jenny#Heal_Jenny` (70, ev 5@0,18), `M07_Wakeup01/02#Lynch/merc/Delay`, `M03B_Hill_Crash_Wake_Up#Kane/Lynch` | | | | | one DM level each |
Nothing named adrenaline / syringe / injection / medic exists as a clip. Pose (kl_animsheet legend rows 60/61): `Heal_Wounded_01` KNEELS 0-19, bent 20-32, KNEELS 33-49, up 50-54; `_NPC` STANDS 0-8, KNEELS 9-46, bent 47-61, KNEELS 62-68.
Skeleton: 55 tracks, the standard 58-bone body (GROUND..fingers, face bones) - the rig every heister wears (re/anim_shot.md 0); it is already in Dog Days, so it fits.
**Dog Days' `Heal_Wounded_01` is NOT Dead Men's**: same name and length, other data (15,032 vs 12,912 bytes); `_NPC`, `_NPC_Low`, `Get_Up_From_Stomach` are byte-identical. Measured (local rotations, kl_fa_rappel._pose_gap): mean 4 - 21 degrees, right hand / forearm / upper arm 58 - 110 degrees in frames 10 - 54: Dog Days re-did the arms (Dead Men's right hand holds the syringe).
Sound: Dead Men's player clip has +0x2C -> `audio:animation/resources/special_moves/heal_wounded_01#seq`, the NPC one `audio:levelsetup/all/characters/healed_by_adrenaline/healed_by_adrenaline_01_withdelay#sound` (DM bank); Dog Days' copies have none.
Prop: Dead Men's levels carry a geom `syringe` (.prp), model/texture `Items_Dynamic/Syringe_01(a)`; no build has it; kl2.exe has no 'syringe' string.

## 2. How Dead Men played it (EXE)
- `ZFFActionHealWounded` (DM vtable 0x966998, 12 slots), made by the PLAYER's action factory as kind 0x12 at 0x5f64e0: ctor 0x601470(0x12, player, target `[player+0xaf8]`, clip `[player+0x868]`); `[player+0x868]` = the clip of `/Special_moves/Heal_wounded` (filled at 0x5e651c). The ctor looks up a child geom named `syringe` (0x601540, the scene's find-by-name, class check) - the syringe shown in the hand.
- The injection moment is NOT a clip event (the player clip has none); it is in the action's code (slots 2 0x5fd940 / 4 0x5fdb80 / 5 0x5fef00: not read).
- The downed side is the player state machine `[player+0x2940]` 0x5fe270 (state 5 'waiting for a healer'); AI healers: `ZHealTactic` -> `ZHealPlayerBehaviourGoal` / `ZSoldierHealGoal` (NPC clip `Heal_Wounded_NPC`). No 'receive' clip: the downed man lies and rises with the normal rise.

## 3. What Dog Days kept (EXE)
- Same class, kl2 vtable 0xbb54fc (slots 2 0x6244b0, 4 0x4c7850, 5 0x4ea150, 8 0x664e50 'HealWounded', 10 0x655a40), factory kind 0x12 at 0x83985f: ctor 0x907300(0x12, player, target `[player+0xd34]`, clip `[player+0x99c]` crouched (vt +0x3cc) / `[player+0x998]`) - those are `/Special_moves/Heal_Down_not_dead` / `_no_dead_Crouch` (0x8f6064). **Dog Days' heal action plays its own 19-frame help-up, not the shot.** Its Start 0x6244b0 calls the TARGET's vt +0x340 and 0x7b3020 on it: built for a player target; not usable on an AI heister.
- `/Special_moves/Heal_wounded` is still resolved into the player's name table (0x78d9d0, word +0x28) but nothing plays it.
- `ZHealTactic` (0xbd027c, evaluate 0x64ed60) looks for a PLAYER with `[[player+0x2940]+0x24] == 5` within 500 units; state 5 is reached only in session mode 2 (klbot.c section 6): never in Arcade.
- NPC animation: the state graph built in code at 0x730be0 (`[0x1549040]`; states Stand, Sneak, ShootPose, DownNotDead (`/Damage/Down_Not_Dead/...Get_Down / Down_Not_Dead / Get_Up`), cover, close combat). **No heal state.** 0x8cc8f0 / 0x8d41c0 take STATE ids, not .ANM slots. The only proven way to play an arbitrary .ANM slot on an NPC is a level MiniCutscene act (`ZMiniActTask` 0xbce638; the rappel bots, re/rappel.md).

## 4. Route per case
| case | route | needs |
|---|---|---|
| **helper = the human** (by a downed bot) | the free-climb form (luvsic): a VaultOver action with a DLL vtable copy plays the slot on the player; AlignTo turns him to the man | **hook only - BUILT** (kladren.c `Anim`); the clip is in every map; optional level step for Dead Men's exact arms (kl_fa_syringe.py, BUILT for DM03) |
| helper = an AI heister | no NPC state plays an arbitrary slot (3). Options: (a) a MiniCutsceneRout per heister per map (`Actor| <name>` act `(anim| /Special_moves/Heal_wounded)` from a PosObject) that the hook re-places at the downed man and starts by its event - level data (tools/kl_fa_rappel_bots.py pattern) + hook (move the PosObject node, send the start); (b) find the act task's play call (ZMiniActTask slots) and call it from the hook | not built; (a) is the realistic one, 1 - 2 tracks |
| downed = a bot | the game's DND state graph plays `/Damage/Down_Not_Dead/Down_Not_Dead_Get_Up`; the graph is global (police share it). Dead Men has no 'receive' clip. AnimInject ends his lie at the shot, so the stock get-up follows the shot | built (Inject); a different get-up clip would need the graph's slot word swapped for crew only: not safe |
| downed = the human | kldown.c Flop=2 already gets him up with Dead Men's `Rise_From_Stomach` (Heal_Wounded family); a helper bot's anim = row 2 | nothing new |

## 5. Built
- `klhook/kladren.c` section 'Anim' (patch `~/w_syringe/syringe.patch` = on HEAD + v76; `~/w_syringe/syringe_build.patch` = on HEAD, what was compiled: ship exit 0, test exit 0). `kladren_test.c`: `#define KAD_TEST_NOANIM` (the harness has no engine).
- `build/claude_stage/agents/syringe/kl_fa_syringe.py` (`facts`, `apply`): adds `/Special_moves/Heal_wounded_DM` = Dead Men's own `Heal_Wounded_01` (from M01_FA_A PlayerCharacter) to Kane, Lynch, Kane_NPC, Lynch_NPC; proofs: re-read byte-equal, audit, base unchanged, clip signature = Dead Men's; +0x2C cleared (the DM sound is not in the bank). Output: `agents/syringe/DM03_syringe/` (from the INSTALLED KLExpansion\Maps\DM03; only `F03_Main.ANM` differs; 14,364 bytes more).
