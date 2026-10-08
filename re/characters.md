# Characters: players and NPCs in Dead Men and Dog Days

Track `track-characters`, 2026-10-09. Read-only study of the stock level archives and both exes.
Every statement names what was run and what it showed. "ASSUMPTION" and "not established" are
meant literally. Scripts: `%TEMP%\claude\c--kl-merge-kl-merge\1e45a579-...\scratchpad\agents\track-characters\`
(`lv.py` level loader, `t5/t6/t7/t16.py` models and bones, `t12.py` sound references, `t15.py`
variants and materials, `t8.py` .ANM bones, `xref.py` / `calls.py` / `disp.py` exe searches).
Stock F01 is always `KL_PortBackup\...\F01_Main.zip`.

## 1. What a character is (both games)

One scene object. No head / hands / mask child objects exist.

    Heroes!Hero_01            ZGROUP      position and heading of the spawn; no model
      Ground                  ZFFPlayer   .gms record +0x0c = chunk index of the model root in the .prm

- `Ground` is the root bone. The body, skeleton, LODs and every outfit are inside the .prm model
  the record points at. The .prp object has no children and (Dog Days) no controllers.
- NPCs are the same shape with class ZFFActor and a `ZSoldier` or `ZCivilian` controller.
- ZCHAROBJ is not a character: the single one per level is `...FFOsdMP1.zip\CharObj`, a HUD font.
- ZLNKOBJ objects (66 in F01, 65 in M01FAA) are weapons, blood decals, lamps, a plane - not people.

.gms record of `Hero_01\Ground`, F01 against M01FAA: identical except the name offset (+0x00) and
the model (+0x0c): type 0x2003e8, flags (+0x1c) 0x00030182, +0x04 0x60, +0x08 0x50 (shared matrix /
zero vector) in both. The parent ZGROUP record differs only in flags 0x07044000 / 0x03044000 and
in +0x28 (aux count 0x0e in Dog Days, 0 in Dead Men for heroes, 6 for henchmen) and +0x35 (pool
group 2 in Dog Days and for Dead Men henchmen, 0 for Dead Men heroes).

## 2. The properties, field by field (schemas from `re/*.json`, values from the levels)

ZFFPlayer: Dead Men 18 fields, Dog Days 23. Same base chain in both
(ZFFPlayer > ZPlayer > ZLNKWHANDS > ZCTRLIKLNKOBJ > ZIKLNKOBJ > ZLNKOBJ > ZSTDOBJ > ZGEOM).
Instance size 5200 bytes in Dead Men, 12168 in Dog Days.

| level | Dead Men | Dog Days | meaning (how known) |
|---|---|---|---|
| ZGEOM | e f*9 f*3 b I | e f*9 f*3 b I **b** | bounding mode, matrix, position, ?, I = the model chunk index again (516 = record +0x0c in F01, 3117 in M01FAA), extra bool 0 |
| ZSTDOBJ | I b | I b | 0, 0 on every hero |
| ZLNKOBJ | I I s | I I s | **variant id** (section 4); **.SND offset** of the footstep property; **animation set** `anmcol:animationdatabase#<set>` |
| ZLNKWHANDS | I I f | I I I I I I f | Dead Men: voice set, material sound def, float. Dog Days: voice set x3 (slots 0-2), two more slots (always 0 in the levels read), material sound def, float |
| ZPlayer | I | I | 0 |
| ZFFPlayer | I e e s | I e e s | 0, EZFFPlayerType, EZFFPlayerRank, '' |

Enums are the same in both exes' schemas. EZFFPlayerType: SINGLEPLAYER 0, SINGLEPLAYER_COOP 1,
MULTIPLAYER_NORMAL 2, MULTIPLAYER_POLICEMAN 3. EZFFPlayerRank: RANK_NONE -1, RANK_1..8 = 0..7,
NUM_RANKS 8.

There is NO property for head, hands, mask, suit or team on a player. Team exists only on
ZFFActor (enum TEAM: 'Enemy', 'Neutral', 'Ally').

ZFFActor: Dead Men 23 fields, Dog Days 39. Shared levels as above; own level
Dead Men `e:TEAM s b s s s I I b`, Dog Days the same nine plus `I f s s f b f s I b b`
(the first `s` is the weapon path `ROOT\AllLevels/mainsceneincludes...\equipment.zip\Weapon\<name>`;
one of the added strings is the kill-message key, e.g. `AllLevels/Interface/Online/Kill/FA_Civilian`).
Controllers: `ZSoldier` -> ZSoldierRout (200 bytes Dead Men, 240 Dog Days), `ZCivilian` ->
ZCivilianRout (68 / 100). Dead Men heroes carry a `MapControl` controller (ZMapControl); Dog Days
does not register that name (the engine skips unknown controllers, CLAUDE.md).

### The integer fields are offsets into the level's .SND

Run: `t12.py` over F01, F05, F09, L01, L03 and M01FAA, M06FAA, M09_A. Every non-zero value of the
ZLNKOBJ / ZLNKWHANDS integers (1514 in Dog Days, 424 in Dead Men) lands on a .SND record
`[type u32][0xcdcdcdcd][name offset]...`, none misses. Names found:

| field | Dog Days | Dead Men |
|---|---|---|
| ZLNKOBJ int 2 | `audio:materials/object/shoe#objectproperty` (type 18); dogs: `.../object/hand#objectproperty` | the same name (type 18) |
| ZLNKWHANDS slot 0-2 | `.../sounddefs/character_sounddefs/<group>/<set>#def` - police_01/02/03, civilian_male_01/03, kane_default, lynch_default ... | one slot: `audio:dialog/characterbehaviors/hero/hero_default#def`, `.../little/little_coop#def` ... |
| ZLNKWHANDS last int | `.../sounddefs/engine/material#def` (type 5) | the same name (type 5) |

- Fragile Alliance heroes in Dog Days have NO voice set (slots 0-4 are 0 in F01, F05, F09). Story
  players have one: Kane -> kane_default, Lynch -> lynch_default (L01, L03).
- Dead Men FA: Hero_07 and Hero_08 have `hero_default` (and no footstep reference); Hero_01..06 and
  the henchmen have none (M01FAA, M06FAA).
- Consequence for conversion: these four values must be rewritten to offsets of the DESTINATION
  level's .SND. A Dead Men value copied as it is points into the middle of unrelated data.
- Converter bug candidate (`kl_convert.Converter.plan`, no LEVEL_MAPS entry for ZLNKWHANDS): the
  type-only pairing puts Dead Men `I I f` on Dog Days fields 0, 1 and 6. Dead Men's second integer is
  the material sound def, which is Dog Days field 5, not field 1 (a voice slot). Correct map by
  the names above: Dead Men 0 -> Dog Days 0, 1 -> 5, 2 -> 6. Not marked "assumed" by the tool today.

## 3. Who the Fragile Alliance characters are

Every stock FA level of both games has exactly 16 ZFFPlayer: 8 MULTIPLAYER_NORMAL + 8
MULTIPLAYER_POLICEMAN, on 9 distinct models (`t16.py`: F01..F09 and M01/M02/M03/M06 FA).
Story levels have 2 (SINGLEPLAYER + SINGLEPLAYER_COOP).

| | Dog Days F01 | Dead Men M01FAA |
|---|---|---|
| heisters | `Heroes!Hero_01..08`, RANK_1..8, one model each (roots 516, 648, 778, 912, 1046, 1173, 1307, 1430) | `Heroes!Hero_01..08`, RANK_1..8, one model each (3117, 3787, 4222, 4659, 5096, 5438, 5880, 6300) |
| animation set | Kane on 01/03/05/07, Lynch on 02/04/06/08 | PlayerCharacter on all 16 |
| police | `Heroes!RespawnPolice#01..08`, RANK_NONE, ONE shared model (1526), set Lynch | `Heroes!Henchmen_01..08`, RANK_NONE, ONE shared model (6336) |
| body materials | `Characters/_MultiPlayer/_Mercs/Merc_01..08` | head per hero + `Characters/_Multiplayer/Merc_Rank3_8` shared by all |
| who they are | generic mercenaries; exe names C1..C9 | Hero_01 = Kane (`Hero_HEAD_Multiplayer`, `Hero_Hair_Final`), Hero_02 = Lynch (`Little_HEAD_Multiplayer`, `Little_Hair_01`, glasses); 03..08 not identified |
| AI team mates | `Gameplay!merc_bot_squad!Squad#02..08\Glazer_Bodyguard_02..08` (ZFFActor, team Ally, sets Kane_NPC / Lynch_NPC) use the SAME model chunks as Hero_02..08 | none in the level |
| police NPC | SWAT model 1543 = the RespawnPolice meshes with 2 variants | FBI-Agents model 878, 8 variants |

Henchmen model materials: USA_Headset_01, SunGlasses_Glas_01, SunGlasses_Frame_Black_01,
FBI_Agents_BlackSuit, Merc_Rank3_8.

## 4. The model (.prm)

Root = 64-byte record, type 7: +0x10 property chunk -> +4 = bone declaration, +0x14 object count,
+0x18 object table, +0x20 bounding box (6 floats). Object = 64-byte record, type 8:
+0x0c sub type (3 = weighted mesh on every character object), +0x0e LOD mask, +0x0f **variant id**,
+0x12 material id (u16, 1-based index into the .MAT entry table), +0x28 sub-mesh table.
Seen on all 24 character models of F01 and all 16 of M01FAA (`t5.py`).
Not decoded: root +0x1c (0x7a0c5, 0x79b05 ... in Dog Days, 0x2df15 ... in Dead Men; it is not a
consistent chunk index).

- LOD masks are 0x01, 0x02, 0x7c in both games (the dog: 0x01, 0x02, 0xfc): three levels of detail.
- Variant: the engine draws the objects whose variant byte equals the object's variant
  (ZLNKOBJ field 0; kl2 0x88c810 stores it at object +0x50 and refreshes the model).
  .prp values over all levels: Dog Days ZFFPlayer always 1 (168 objects), ZFFActor 1..6;
  Dead Men ZFFPlayer 0 or 1, ZFFActor 0..10.

| model | bones | objects | variants | per variant, LOD 0 |
|---|---|---|---|---|
| DD Hero_01 | 103 | 21 | 2 | 1: Merc_01 x2, eye_Outer_Alpha, MoneyBag_01. 2: Merc_01 x2, **Merc_Masks**, MoneyBag_01 |
| DD Hero_02..08 | 101-104 | 22-24 | 2 | the same pattern (+ glasses / hair materials) |
| DD RespawnPolice | 104 | 15 | 1 | Police_SWAT_01 x2, Goggle_Visor_01, eye, W_Hg_M77_01, H_Balaclava_03 |
| DM Hero_01 | 101 | 432 | 24 | head, headset, eye, Merc_Rank3_8 x2, playstyle, hair, eyelashes |
| DM Hero_02..08 | 95-102 | 216-528 | 24 | as above |
| DM Henchmen | 95 | 16 | 1 | see section 3 |

- Dog Days variant 2 is the masked look. Proof: the only material difference is `Merc_Masks` in
  place of the eye mesh (and a smaller head mesh), and the code in section 6.
- Dead Men's 24 variants are 3 headset materials (multiplayer_headset01_Rank_01, headset02,
  headset03) x 2 "playstyle" materials (playstyle_01a, playstyle_04) x 4 equipment levels (LOD 0
  vertex totals of Hero_01: 6811, 6786, 7515, 8088, repeating in that order through all 24).
  Hero_06 has no playstyle material. Which rank / play style selects which variant: not established
  (Dead Men exe strings: `/Menu/Online/Profile/FragileAllianceRank_01..08`, nine
  `/Menu/Online/Leaderboard/Playstyle_*`, `m_iPlayStyleMasks`).
- Size: a Dog Days hero model is 123-134 chunks, 1.2-1.6 MB; a Dead Men hero 342-670 chunks,
  1.7-2.2 MB; the henchmen model adds 36 chunks, 0.3 MB (it reuses meshes of earlier models).
- Dog Days heroes carry a MoneyBag mesh (2157 vertices at LOD 0) inside both variants. Dead Men
  models have none. How the bag is shown or hidden: not established.
- Mesh descriptor 32 bytes (Dead Men) against 48 (Dog Days), vertex strides and weighted-mesh
  copy-bone runs identical: earlier research (`research/v2_046ec...json`), not re-checked here.

## 5. Skeleton and animation compatibility

Bone declaration: 20-dword header, slot 0 = bone count, slot 1 = 64-byte definitions (parent +0x0c,
name +0x1c), slots 2 / 3 / 18 = 48 bytes per bone, 4 = 36, 6 = 28. The same in Hero_01, Hero_02,
RespawnPolice (F01) and Hero_01, Hero_02, Hero_04, Henchmen (M01FAA) (`t7.py`).

Survey of every character model with PELVIS and SPINE_2 (people, and Dog Days' 9 dog models),
all levels of both games (`t16.py`): 333 Dog Days models in 21 levels, 238 Dead Men models in 20.

- Bone names: Dead Men uses 103 distinct names, Dog Days 127. **No Dead Men name is missing from
  Dog Days** (set difference empty).
- Dog Days only: `free_bone01` (in ALL 333 models; in none of the 238 Dead Men ones), `NECK1` and
  the `tail*` / `xtra_align_* / xtra_chain_* / xtra_target_* / xtra_solver_* / xtra_up_*` helpers
  (9 models each: the dogs / special rigs).
- In the 39 human models of F01 + M01FAA: 83 bones are in every one, and those 83 have the same
  parent everywhere (`t6.py`). The rest (`xtra_mus_*`, some `fa_*` face bones, `fa_forehead02`)
  are optional inside each game too: Dog Days Hero_03 has 101 bones, Hero_01 103, both on set Kane.
- Bone indices differ between models that share one animation set: Hero_01 (103 bones) and
  Hero_03 (101) are both on set Kane, and 4 of F01's civilian models on set Civilian have the 83
  common bones in a different relative order. So animation data cannot be bound by bone index.
  Binding by name is the only reading that fits; the code that does it was not located.
- The 64-byte definition's first three floats differ between any two characters by up to 19 units
  inside Dog Days (Hero_02 against Hero_01) and up to 15 between a Dead Men and a Dog Days hero.
  Dead Men proportions are inside the spread Dog Days already animates. What those floats are
  (rest offset?) was not decoded.
- Both exes hold the same {id, name} bone table (kl2 0xcd8850, kaneandlynch 0xa31868, 41 rows:
  GROUND 1, PELVIS 2 ... head attacher 36). The single difference: id 33 is `FREE_ATTACHER` in
  Dead Men and `free_bone01` in Dog Days. Its users were not found (no direct reference to the
  table start). The table also names PONYTAIL, which no model has.

.ANM: one bone-name table per level (F01 143 names, F05 121, L03 239, M01FAA 153, M06FAA 168,
M09_A 235), upper-case variants of the same names (`NECK1`). F01's table holds every human bone
name; the Dead Men tables lack `free_bone01` and the `xtra_align_*` family and add vehicle bones
(`DOOR_*`, `WHEEL_*`, `SEAT_*`), `FREE_ATTACHER`, `FA_FOREHEAD`.

Animation sets present: F01 Kane, Lynch, Swat_02, Civilian, Police, Dog, Lynch_NPC, Kane_NPC;
M01FAA Mercenary_04, Police_USA, Female, Civilian, Generic, Van, PlayerCharacter, M4 (earlier
research). A ZFFPlayer whose set is missing from the .ANM crashes at kl2 0x493d95
(`kl_package.py` comment). So a Dead Men character in Dog Days must name a Dog Days set.

Verdict: skeletons are the same family and name-compatible. The one open risk is `free_bone01`:
every Dog Days model has it, no Dead Men model does, and whether kl2.exe tolerates its absence is
**not established**.

## 6. How Dog Days gives a player a character today

There is no character select and no character list in data. Evidence:
- `menu/frontend.xml` (Patch01), `menu/ingame.xml`, `Menu/online.xml`: no element or option
  matching character / suit / skin / avatar / outfit / Hero / Merc_0. The only appearance control
  is one toggle: `<GuiElement Type="DLCMaskToggler" Option="UseMask" Text="GameUseMask">`,
  LOC text "Criminal Masks (Multiplayer)".
- The eight heisters are the eight Hero_0N objects; the level fixes model, animation set and rank.
- kl2 0x478df0 maps an index 0..8 to the LOC key `/AllLevels/Interface/FACharacters/C1..C9`
  (else `<InvalidRank>`). English: C1 J.C., C2 Tommy, C3 Pierre, C4 Liam, C5 Jean, C6 Elwood,
  C7 Bud, C8 Mitchel, C9 Glazer. Used for AI team mates' names.
- ZGameRulesHeist vtable slot 198 (0x588980): character index = `name[0x12] - '1'`, stored in a
  byte table at game rules +0x33e. `Glazer_Bodyguard_0N` has its digit at index 18. So an AI team
  mate's identity is the digit in its object name; its look is whatever model its record names.
  The table is initialised to 0..7 (loop to 8 at 0x835843) - eight slots.
- ZGameRulesFragileAlliance 0x822830, per player: skipped when player +0x273c == 3 (policeman);
  unless config key `DisableFAVariants` is set, calls 0x88c810 with variant 2 when an obfuscated
  per-player flag is true (session player +0x338, read by 0x76adb0 -> 0x5b1400, byte xor 0xac),
  else variant 1. ZGameRulesHeist 0x4b5b20 reads the same config key and calls 0x88c810 with 2
  when an option object answers the name `UseMask` (0x4b5bf6).
  That flag being the mask option is an ASSUMPTION (names and materials agree; the writer of
  +0x338 was not traced).

Not established: the rule that hands a joining human player one of Hero_01..08 (join order,
lobby slot or random). The rank enum on the objects and the per-player index getter 0x6c7700
(player +0x2748) suggest "by slot"; `rand() % n` at 0x421de3 is in the name builder for AI
characters, not in a player assignment.

## 7. How many characters a level can hold

- Heister objects: 8. EZFFPlayerRank has 8 values, the game-rules slot table has 8 entries, all 13
  stock FA levels of both games have 8 + 8 players. A ninth heister object: not supported by
  anything seen; untested.
- Character MODELS: no limit met. L01 has 2 player + 23 actor models; F01 9 + 15.
- Looks per model: the variant byte. Dead Men ships 24 per hero; Dog Days uses up to 4 in F01.
- Shared budgets: texture ids (4096 slots in Dog Days .TEX), material ids (u16).

So "each character usable once per match" is what the engine already does (one player per
Hero_0N). A select screen with MORE than eight characters needs either model swapping per slot or
extra variants, plus new code (KLHook) to store the choice: no data-only route was found.

## 8. Putting one Dead Men character into a Dog Days level

Keep Dog Days' object, replace only its model. Per the tables above nothing else in the object has
to change: the variant (1) exists in Dead Men hero models, the animation set stays Kane / Lynch,
the sound offsets stay those of the Dog Days level.

To convert:
1. Model sub-graph from the Dead Men .prm (root -> objects -> sub-mesh tables -> descriptors ->
   vertex / index chunks, bone declaration and its slots), appended to the Dog Days .prm with
   chunk indices renumbered; descriptors 32 -> 48 bytes (`kl_prm` rule).
2. Materials (.MAT entries, 5 for the henchman, 8-9 per hero) and their textures (.TEX, new ids),
   with the Dead Men -> Dog Days material differences listed in CLAUDE.md (.MAT section). Object
   material ids renumbered. Texture count per character: not measured.
3. .gms: record +0x0c of the target `Ground` entity (and ZGEOM field 4 in the .prp, which repeats
   it) -> the new root.
4. Variants: Dog Days sets variant 2 on heisters when masks are on. A Dead Men hero has variants
   1..24, so 2 exists (same body, slightly different equipment). The henchman model has only 1:
   as a heister it would have nothing to draw under variant 2 (ASSUMPTION), as a policeman it is
   never re-varianted.
5. Nothing for animation: Dead Men .ANM clips are not needed for a character that uses a Dog Days set.

Voice lines are separate: Dog Days FA players have no voice set; Dead Men's sets
(`dialog/characterbehaviors/...`) would have to exist in the level .SND first.

Blockers / risks, most likely first:
1. `free_bone01` missing from every Dead Men skeleton (section 5). Fix if needed: append one bone
   (parent GROUND, as in Dog Days) - needs every bone-declaration slot understood (slots 5, 7-11,
   19 are not per-bone sized; not decoded).
2. Bone-declaration header slots 14-17 hold packed counts that differ (Dog Days 0x24 where Dead Men
   has 0x21 / 0x1f / 0x23): meaning not decoded; they travel with the model.
3. Root +0x1c not decoded.
4. Material conversion (known open items in CLAUDE.md).
5. Player-only code paths (camera bone, cover, first-person hands) that an NPC never runs.

## 9. Smallest experiment: a Dead Men model standing in a Dog Days level

Goal: answer risk 1-3 with no material, texture, sound or animation work.

- Base: unmodified stock F01 (all files), tested in the F01 slot as usual.
- Source: Dead Men M01FAA `Heroes!Henchmen_01\Ground`, model root 6336 (95 bones, 16 objects,
  1 variant, 3 LODs).
- Target: one ZFFActor civilian with a model nobody else uses, e.g.
  `Gameplay!CiviliansFront!Civ_Platform1_Runnning\JPN_CIV_05\Ground` (model 1589, set Civilian,
  variant 1, 6 objects). An NPC avoids the player-only code and the mask variant.
- Change exactly: (a) append the model sub-graph to F01's .prm, descriptors widened;
  (b) set every copied object's material id to one existing Dog Days id (e.g. the id of
  `Police_SWAT_01`) - wrong texture, but no .MAT / .TEX edit; (c) point the civilian's record
  +0x0c and ZGEOM field 4 at the new root.
- Pass: the level loads and a figure in Dead Men proportions runs with Dog Days' civilian
  animation. Fail at load or a collapsed / exploded mesh tells which of risks 1-3 is real.
- Next steps in order: the same model on `Hero_02\Ground` and `Glazer_Bodyguard_02\Ground`
  (model 648; the AI team mate stands next to the player in Arcade), using Dead Men Hero_02
  (root 3787, has variant 2); then real materials; then the local player.

## 10. Not established (summary)

- Whether kl2.exe needs `free_bone01`; where bones are bound by name.
- How a human player is matched to a Hero_0N object.
- That the +0x338 player flag is the "Criminal Masks" option.
- Which Dead Men rank / play style picks which of the 24 variants.
- Bone header slots 5, 7-11, 14-17, 19; root +0x1c; the first floats of a bone definition.
- How the Dog Days money-bag mesh is hidden; ZLNKWHANDS slots 3-4; texture count per character.
- Whether a ninth heister object or per-policeman models are accepted (untested).
