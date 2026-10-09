# Invisible police on the Retomoto street

Agent `s-visible`, 2026-10-09. OFFLINE: nothing was launched or installed; every statement names
what was run on the level files. "ASSUMPTION" and "not seen live" are meant literally.
The build looked at is the one the owner played, `<work>\build\play2` (F07 systems + M09_B +
M09_A with the street layer of `tools/kl_fa_street.py`; made from `G:\kl_scratch\k_street`).
Owner's report after that round: "some of the police outside are invisible??".

## 1. Result

**One material. 12 of the 47 actors of the street are not drawn beyond close range.**

- The campaign's own policemen (Dead Men model `JPN_Police`, root chunk 52248 in the built .prm,
  12 actors in 8 squads) draw their near and middle detail with `JPN_Police_AllinOne` and
  `JPN_Headset_02`, and their FAR detail (mask 0x7c = detail levels 2-6) with ONE mesh of 668 - 930
  vertices on the material `Characters/_JPN/JPN_Police_LOD3`.
- That material is class Standard/SkinCloth with neither bump nor specular. Its weighted-mesh
  sub class draws the colour passes with `Cloth30.fx` / `Skin30.fx`, and the level's shader cache
  has NO permutation of either without `SPECULARENABLED`: the smallest it has is
  {BUMPENABLED, SPECULARENABLED, STDSAMPLERSTATE} (7 cloth, 7 skin entries for weighted meshes).
  Asked: `(cloth30.fx, MESH_WEIGHTED, {STDSAMPLERSTATE})` and the same of `skin30.fx`. On a miss
  kl2 0x8b8fd0 returns 0 and the layer loader leaves the pass empty (0x50c2ff; re/lighting.md 1).
  The passes it takes from `Standard30.fx` (shadow map, shadow drop, depth / normals) do resolve.
  So from the distance where the engine switches to detail level 2 the policeman has no body: he
  still shoots, is hit, shows his marker, and (ASSUMPTION, from the passes that are left) still
  casts a shadow. Variants 3 and 8 keep a 12-vertex pair of glasses (`Accessories_01_Glass`) at
  that distance.
- `kl_light.fit_shaders` could not help: it only switches features OFF, and this instance has
  none on. The build log said so both times (`G:\kl_scratch\k_street\test.log` lines 38-40 and
  82-84: "unresolved: ['Characters/_JPN/JPN_Police_LOD3' ...]", "note: material ... has no compiled
  shader (not drawn)") - a note, not a problem, so nothing stopped the build.
- Everything else that can hide a character was tested on the same files and is clear (section 3).
  F07's 14 moved squads (27 actors) and the campaign's 8 other actors have no fault in the data.

What only a live look settles: that these twelve are the ones the owner meant (the watcher's
pictures do not decide it, section 5); at what distance detail level 2 begins; how the body looks
in the plain shader.

## 2. The fix (in tools/kl_light.py; nothing of kl_graft has to change)

`kl_light.fit_shaders` now ends with a fallback, `plain_twin()`: an instance of a class in
`TWIN_CLASSES` (Standard/SkinCloth only) that no set of switches fits is rebuilt as a
Standard/Standard instance the way `kl_mat.convert_mat_full` builds one - that class's properties
in Dog Days' order, the instance's own node where it has a property of that name, Dog Days' most
common node for a property every stock instance has, with every added `...Enabled` switch OFF.
Texture, colour, render state, render group, surface type and mesh kind stay.

For `JPN_Police_LOD3` (slot 1229): class slot 2 -> 3, `mapDiffuse` 2045 kept; dropped: rim light
(4 properties), sub-surface (4), `mapTranslucency` (id 0). It then asks for
`(standard30.fx, MESH_WEIGHTED, {STDSAMPLERSTATE})`, which the cache has. That is exactly what the
same level's `JPN_Swat_LOD3` and `JPN_Police_female_LOD3` (Dead Men's own far-detail materials of
the SWAT and the police woman) already are. ASSUMPTION: a property both classes name means the
same in both. NOT SEEN LIVE.

`kl_graft.build` already calls `kl_light.fit_shaders(mat, fxc, log=log)` on the WHOLE joined .MAT
in each step of a chain (the second step's log lists the first step's material again), so the next
build of any map carries the fix with no other change.

Not rebuilt on purpose: Standard/Glow (`Weapons/BombWindow_02`, the bomb on the boardroom window,
`glow30.fx` for a rigid mesh without defines; the lamps and beams of M02 / M06, re/maps.md 9).
A glow drawn as a lit surface may look worse than a missing one. `kl_light.TWIN_CLASSES` takes
the class if someone wants to try (it was tried offline: the twin resolves).

### Counts, before / after

| | `build\play2` (played) | `build\s_visible` |
|---|---|---|
| materials without a compiled shader (`kl_light.missing_shaders`) | 2 of 1,429 | 1 (`Weapons/BombWindow_02`) |
| people with a drawing fault (`kl_chars.undrawn`) | 12 of 108 | 0 of 108 |
| street actors (y < 5000) with a fault | 12 of 47 (0 of F07's 27, 12 of the campaign's 20) | 0 of 47 |
| `kl_fa_street.py report` | 12 faults (the new section) | 0 faults |
| `kl_impact.py` (bone ids) | 0 | 0 |

`<work>\build\s_visible\` = `play2` with `kl_light.refit` applied
(`python tools/kl_light.py refit <work>\build\play2 <work>\build\s_visible`): the archive's 30
members in the same order, 29 with equal CRC and size, only `F01_Main.MAT` differs, in it only
instance 1229; the use-count table is equal; `kl_mat.check` passes; the 20 files beside the
archive are byte-identical. It is the played build (balcony start and all) plus this one change -
NOT a new chain build, so nothing of other agents' work in progress is in it. NOT INSTALLED.

## 3. Every other reason, tested on the built level

Tool: `python tools/kl_chars.py invisible <folder | level> [--all]` (`kl_chars.people` /
`undrawn`). Stock F01, F07, L03: 65 / 59 / 142 people, 0 faults.

| # | reason | test | result on `play2` |
|---|---|---|---|
| 1 | model has no object of the variant asked | ZLNKOBJ[0] of each of the 108 ZFFPlayer / ZFFActor against the variant bytes (+0x0f) of its model's objects | clear: 108 of 108 have it. Campaign police ask 1, 2, 3, 4, 8 of a model with 1..8; F07's ask 1, 2 of models with 1..2 / 1..4. The FA variant setter (kl2 0x822830, variant 2 for a masked heister) runs for players only (re/characters.md 6); an NPC keeps its .prp value. |
| 1b | a detail level with no object | mask bytes (+0x0e) of the asked variant against levels 0-6 | clear: every variant of every model has 01 + 02 + 7c (the dog 01 + 02 + fc) |
| 2 | material without its compiled shader | `kl_light.missing_shaders` on the written .MAT / .fxc, then which person's objects use those slots | **THE FAULT: slot 1229 on model 52248.** The other slot (1410, the window bomb) is on no person. `fit_shaders` runs on the whole joined .MAT in both chain steps (log lines 38 and 82). |
| 3 | F07's moved squads: model left behind / in no room | the actor IS the model (one entity, record +0x0c = the root; re/characters.md 1), so it moves with the node. Room: `.rmi` point query at each actor's world position | clear: all 27 stand in `M09_B_Retomoto_Square_01a` or `M09_B_Street_01a`, the same two boxes the campaign's street actors are in. No person of either level is a member of a room tree (parent room: none, in no .oct tree) - the same in stock F07 (0 of 43 actors). |
| 3b | two levels' room boxes over one place | the same query | NOTE, not a fault found: M09_A's `M09_Backdrop_A_00` and `M09_A_Out_CityScapeBack` boxes also cover the whole street (the two campaign levels share coordinates). Which room a point in several boxes gets was not read. Against it being a cause: the owner's own character, a person of the same kind, is drawn everywhere on the street (pictures 0081, 0083). |
| 4 | skeleton / animation numbers / bone ids | `kl_chars.check_bones` against the level's .ANM and `kl_impact.bone_faults`, per model | clear: 0 on all 17 person models |
| 4b | black figure (no light) | `kl_light.environments` on the built level | not a fault found: `M09_B_Street_01a` and six more rooms of M09_B are paired with `Environment#02_Character_EDITOR` (type 3, white, 1.0). The owner's character is lit there in every street picture. |
| 5 | **PRM_LIMIT trim emptied a mesh** (99.6 -> 61.5 MB, 8,368 chunks) | walk from every root the level names (`kl_graft.live_roots`: 27,306 roots = the .gms records' chunk + ZGEOM[4] of every node - people, weapons, clone-group templates are nodes like any other - + ZWINPIC, fonts, cloth, particle templates, the scene block) and, separately, from each person's model root | **clear.** Of 8,794 vertex / index chunks the walk reaches, 0 are zeroed stubs (18 are 16 bytes long: real index lists of 3 - 6 indices that 538 descriptors share, none all zero). All 8,377 zero stubs of the file are unreached, except 9 that are reached as `prop` / `skel7` - 16-byte zero chunks by nature. Every one of the 17 person models (39 - 439 chunks each) is wholly inside the reached set, and no descriptor with vertices has less data than 4 bytes per vertex. Variants and detail levels are objects of the ONE object table of a root, so the walk takes them all. |

## 4. The street's actors (built level, y < 5000: 47)

`materials at far detail` = what the asked variant draws at mask 7c. All use animation set
`Army` (campaign) or `Swat_02` / `Dog` (F07). F07's models carry a holstered pistol as part of
the body mesh (`W_Hg_M77_01`, `W_Hg_TT_01`) - a look, not the weapon they fire.

| squad | actor | from | model root | bones | variant | set | world x y z | materials at far detail (mask 7c) | drawn |
|---|---|---|---|---|---|---|---|---|---|
| Squad_Teargasguys | JPN_Teargas_Police_01#02 | M09_B | 52248 | 102 | 2 | Army | 429 26 -6849 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_Teargasguys | JPN_Teargas_Police_01#01 | M09_B | 52248 | 102 | 4 | Army | 420 26 -6222 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_InFront | JPN_Police_01#06 | M09_B | 52248 | 102 | 3 | Army | 446 25 -7955 | Accessories_01_Glass, JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_InFront | JPN_Police_01#08 | M09_B | 52248 | 102 | 2 | Army | -366 25 -7594 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_InFront | JPN_PoliceWoman01 | M09_B | 52323 | 96 | 1 | Army | -137 22 -7262 | JPN_Police_female_LOD3 | ok |
| Squad_SniperResponse | JPN_Police_01#01 | M09_B | 52248 | 102 | 1 | Army | -4808 23 2650 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_RoadBlock_South#02 | JPN_Police_01#02 | M09_B | 52248 | 102 | 1 | Army | -5390 22 -13592 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_RoadBlock_South#02 | JPN_Police_01#01 | M09_B | 52248 | 102 | 1 | Army | -5343 22 -13624 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_SWAT_From_Behind_South | SWAT_Beam03 | M09_B | 52003 | 99 | 1 | Army | -3747 3 -14188 | JPN_Swat_LOD3 | ok |
| Squad_SWAT_From_Behind_South | SWAT_Beam02 | M09_B | 52003 | 99 | 1 | Army | -3715 3 -14118 | JPN_Swat_LOD3 | ok |
| Squad_SWAT_From_Behind_South | SWAT_Beam01 | M09_B | 52003 | 99 | 1 | Army | -3797 3 -14097 | JPN_Swat_LOD3 | ok |
| Squad_SWAT_From_Behind | JPN_Police_01#02 | M09_B | 52003 | 99 | 1 | Army | -3838 5 -2159 | JPN_Swat_LOD3 | ok |
| Squad_SWAT_From_Behind | JPN_Police_01#03 | M09_B | 52003 | 99 | 1 | Army | -3889 0 -2251 | JPN_Swat_LOD3 | ok |
| Squad_SWAT_From_Behind | JPN_Police_01#01 | M09_B | 52003 | 99 | 1 | Army | -3914 5 -2179 | JPN_Swat_LOD3 | ok |
| Squad_RoadBlock_South | JPN_Police_01#05 | M09_B | 52248 | 102 | 3 | Army | -2392 3 -12983 | Accessories_01_Glass, JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_RoadBlock_South | JPN_Police_01#04 | M09_B | 52248 | 102 | 1 | Army | -2236 3 -12894 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_RoadBlock_South | JPN_Police_01#03 | M09_B | 52248 | 102 | 8 | Army | -2516 32 -12993 | Accessories_01_Glass, JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_Launcher_Dude_North | JPN_Police_01#01 | M09_B | 52248 | 102 | 1 | Army | -3468 4 2804 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| Squad_RoadBlock_R2 | JPN_Police_Woman | M09_B | 52323 | 96 | 1 | Army | -1454 8 3616 | JPN_Police_female_LOD3 | ok |
| Squad_RoadBlock_L | JPN_Police_01#01 | M09_B | 52248 | 102 | 1 | Army | -4318 8 3839 | JPN_Police_LOD3 | NOT DRAWN at detail 2-6 |
| 021_FinancialAlley_Dog | Dog | F07 | 599 | 96 | 1 | Dog | -2825 -39 6101 | Dog_German_Shepherd_01 | ok |
| 020_FinancialAlley_LeftParking | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -4059 -42 -1919 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_LeftParking | Police_SWAT_01__ | F07 | 718 | 104 | 1 | Swat_02 | -4137 -42 -1898 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_LeftFurther | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -1776 -39 -1318 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_LeftFurther | Police_SWAT_01__ | F07 | 841 | 103 | 1 | Swat_02 | -1812 -47 -1885 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 020_FinancialAlley_RunForDumpster | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -4166 -39 94 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_RunForDumpster | Police_SWAT_01__#02 | F07 | 718 | 104 | 1 | Swat_02 | -4106 -39 82 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_RightPlatform | Police_SWAT_01__#02 | F07 | 718 | 104 | 1 | Swat_02 | -1708 -39 187 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_RightPlatform | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -1760 -39 312 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_RightPlatform | Police_SWAT_01__ | F07 | 718 | 104 | 1 | Swat_02 | -1931 -39 249 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 020_FinancialAlley_RightGround | Police_SWAT_01__ | F07 | 718 | 104 | 1 | Swat_02 | -2900 -39 -1430 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExitStreet_Left | Police_SWAT_01__#02 | F07 | 841 | 103 | 1 | Swat_02 | -3467 -39 5545 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExitStreet_Left | Police_SWAT_01__#01 | F07 | 841 | 103 | 1 | Swat_02 | -3521 -39 5705 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExitStreet_Right | Police_SWAT_01__#02 | F07 | 718 | 104 | 1 | Swat_02 | -2721 -39 5647 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExitStreet_Right | Police_SWAT_01__#01 | F07 | 841 | 103 | 1 | Swat_02 | -2678 -39 5652 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExit_Right | Police_SWAT_01__ | F07 | 718 | 104 | 1 | Swat_02 | -1896 -39 5799 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExit_Right | Police_SWAT_01__#02 | F07 | 841 | 103 | 1 | Swat_02 | -1889 -39 5886 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExit_Right | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -1917 -39 5714 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExitSkywalkNoCover | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -2300 -39 4420 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExitSkywalk | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -3396 -39 3657 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExitSkywalk | Police_SWAT_01__ | F07 | 841 | 103 | 1 | Swat_02 | -3301 -39 3673 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExit_Left | Police_SWAT_01__#02 | F07 | 841 | 103 | 1 | Swat_02 | -4056 -39 5540 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 030_FinancialAlleyExit_Left | Police_SWAT_01__#01 | F07 | 718 | 104 | 1 | Swat_02 | -4123 -39 5558 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 030_FinancialAlleyExit_Left | Police_SWAT_01__ | F07 | 718 | 104 | 1 | Swat_02 | -4089 -39 5551 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 040_EscapeEntranceLeft | Police#05 | F07 | 718 | 104 | 2 | Swat_02 | -3588 -39 11950 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |
| 040_EscapeEntranceRight | Police#05 | F07 | 841 | 103 | 1 | Swat_02 | -2613 -39 12500 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | ok |
| 040_EscapeEntranceRight | Police#06 | F07 | 718 | 104 | 2 | Swat_02 | -2613 -39 12500 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | ok |

| model root | chunks | bones | variants | near (mask 01) | middle (02) | far (7c) |
|---|---|---|---|---|---|---|
| 52248 | 250 | 102 | 1, 2, 3, 4, 5, 6, 7, 8 | Eyelashes, JPN_Headset_02, JPN_Police_AllinOne, eye_Outer_Alpha | JPN_Headset_02, JPN_Police_AllinOne | JPN_Police_LOD3 |
| 52323 | 80 | 96 | 1 | Eyelashes, Ffemale_Hair_black_01, JPN_HEAD_Female2, JPN_Police_female, eye_Outer_Alpha | Ffemale_Hair_black_01, JPN_HEAD_Female2, JPN_Police_female | JPN_Police_female_LOD3 |
| 52003 | 92 | 99 | 1, 2 | JPN_SWAT_GLASSes, Swat_BODY_01, eye_Outer_Alpha | JPN_SWAT_GLASSes, Swat_BODY_01 | JPN_Swat_LOD3 |
| 599 | 39 | 96 | 1 | Dog_German_Shepherd_01 | Dog_German_Shepherd_01 | Dog_German_Shepherd_01 |
| 718 | 122 | 104 | 1, 2 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01, eye_Outer_Alpha | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 | Goggle_Visor_01, H_Balaclava_03, Police_SWAT_01, W_Hg_M77_01 |
| 841 | 127 | 103 | 1, 2, 3, 4 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01, eye_Outer_Alpha | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 | Normal_Body_Male, Police_Special_01, W_Hg_TT_01 |

## 5. The watcher's pictures

`<work>\research\watch\20261009_180847\` 0076 - 0086 (the street): they do not decide it. 0082
shows a policeman drawn at about 5 m with his kill marker; 0084 two bodies on the road at about
25 m and hit indicators from the north with no shooter visible between the cars; 0080 a small
blue-white shape with red marks at the kerb at about 30 m that could be a far-detail remnant.
No picture shows a marker or a muzzle flash over empty ground beyond doubt. (No image library
is installed here, so nothing was enlarged.)

## 6. For the lead

1. Nothing to patch in `kl_graft.py` for the fix. Optional line for `verify()`, after the bones
   block (`out` = the members it is given; needs `.gms .buf .prp .prm .MAT .fxc .rmi .ANM`):

       import kl_chars
       bad += ['people: ' + x for x in kl_chars.undrawn(out)[:8]]

   On `play2`'s members it returns the 12 lines; on `s_visible`'s and on stock levels none.
2. `kl_fa_street.py report / test` and `kl_fa_author.py test` now run the check and fail on it.
3. To give the owner the fix without a rebuild: `python tools/kl_graft.py install F01 --from
   <work>\build\s_visible` (when the game is not running). KLJoin.ini and the hook are untouched.
4. Live, in this order: (a) on the street, look north from the door at the road block (z 3600 -
   4300, 100 m): campaign police should have bodies at every distance; (b) walk towards one and
   watch for a visible change of look where the far detail begins - the plain shader has no rim
   light; (c) if they are still missing, the cause is not in the level's files as read here:
   suspect 3b (room choice) and test it by standing inside the lobby and on the road in turn.
