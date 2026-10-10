# Payday 2 third-person weapon models as inputs for the gun-looks pipeline

Research only (2026-10-10, agent G). Nothing built, nothing installed, no game run. Everything below was
measured on the files of Steam build 25506656 (`C:\Steam\steamapps\common\PAYDAY 2`) with `tools/pd2_crate.py`
and `tools/pd2_model.py`, and on stock Dog Days F01 with `tools/kl_chars.py` / `tools/kl_prmgraph.py`
(scratch script, output kept as `<work>\pd2\guns\dd_guns_F01.txt`). Extracted data: `<work>\pd2\guns\`
(`src\units\...` = the extracted units with `.xml` text beside the binaries, `png\` = renders, `lua\` = the two
tweak-data files as LuaJIT bytecode plus their printable strings). Nothing of it is in the repo.

The target is `tools/kl_guns.py`: a look is extra rigid PARTS of a Dog Days gun's model, each on a `w_bone_*`
bone of that gun, hidden by variant until `klhook/klgun.c` shows them.

## 0. The main findings

1. Payday 2 has TWO kinds of third-person gun model, and the second one is the better input:
   - `wpn_third_*` = the player's modular guns. A gun is an EMPTY FRAME unit (`wpn_fps_<gun>_npc`, which
     reuses the first-person base `.object` / `.model`: only `a_*` attach points, animation dummies and a
     collision box, no visible mesh) plus one unit per PART (`wpn_third_<gun>_pts/...`, `wpn_third_upg_*`),
     each part linked at an `a_*` object. The stock look of a gun is its `default_blueprint` in
     `lib/tweak_data/weaponfactorytweakdata` (LuaJIT bytecode; the part names are readable as strings).
   - `wpn_npc_*` = the enemies' guns: ONE unit, one `g_body` mesh (+ `g_body_lod1`), one diffuse + one
     normal map. 22 of them under `units/payday2/weapons/`, 17 more in DLC folders. No assembly needed.
2. Third-person Payday 2 guns are NOT denser than Dog Days'. They are lighter: an NPC gun is 250-450
   triangles, an assembled player gun 330-1,350; Dog Days' are 1,200-3,100 (section 5). The dense Payday 2
   meshes are the FIRST-person ones (`wpn_fps_*_pts`: the MP5 body alone is 6,332 triangles), which the
   looks pipeline does not want.
3. Frame: Payday 2 guns are centimetres, +Y = muzzle, +Z = up, +X = the gun's right side (shell ejection),
   origin = the pistol-grip attach point. Dog Days guns are centimetres, +X = muzzle, +Y = up, -Z = the gun's
   right side (the AK's charging handle), origin = `GROUND`, just behind the grip. The map is a pure rotation:
   `DD(x, y, z) = (PD2.y, PD2.z, -PD2.x)` (determinant +1), plus a per-gun translation of a few centimetres
   (section 3). Scale 1:1 (the AK-47 is 89.7 cm in Payday 2, 87.5 cm in Dog Days).
4. All of it is rigid geometry (no SkinBones section in any weapon model read), with the vertex layout
   `pd2_model.py` already decodes (position, uv0, normal, tangent, binormal), and DXT5 textures of 64-256 px.

## 1. Inventory

### 1.1 `wpn_third_*` units in the shipped `assets\hashlist`

`grep -E '^units/(payday2|pd2_dlc[^/]*)/weapons/wpn_third_' hashlist` = 2,772 paths in 216 unit folders
(`<work>\pd2\wpn_third_paths.txt`, `wpn_third_units.txt`). By the family word after `wpn_third_`:

| family | folders | what it is |
|---|---|---|
| upg | 81 (+2 `m4_uupg_*`, +1 `aug_body_f90`) | shared PARTS: sights `upg_o_*`, suppressors `upg_ns_*`, lights `upg_fl_*`, grips `upg_vg_*`, the AK and M4 part pools `upg_ak_reusable`, `upg_m4_reusable` |
| ass | 24 | assault rifles: 74 (AK-74), ak5, akm, amcar, asval, aug, contraband, corgi, fal, famas, flint, g36, galil, l85a2, m14, m16, m4, s552, scar, sub2000, vhs (+ 3 `_b_short` / `_g_engraved` extras) |
| smg | 21 | akmsu, baka, coal, hajk, m45, mac10, mp5, mp7, mp9, olympic, p90, schakal, scorpion, speen, sterling, tec9, uzi (+ 4 mod extras) |
| pis | 20 | 1911, 2006m, b92fs, c96, deagle, g17, g18c, g22c, hs2000, peacemaker, pl14, pmm, ppk, rage, shrew, sparrow, usp, welrod (+ 2 engraved) |
| sho + shot | 7 + 5 | basset, ben, bleckert, boot, ksg, r870 (`sho_r870` = an old single-file example), striker; huntsman, m37, r870 (parts), saiga, shorty (the Locomotive's extra parts) |
| snp | 9 | desertfox, model70, mosin, msr, r93, tti, victor, wa2000, winchester |
| lmg | 5 | m249, mg42, par, rpk, shuno |
| mel | 25 | melee |
| saw 5, gre 3, bow 2, rpg7 2, spe 2, ray 1, fla 1 | | special / launchers |

56 folders are under `units/payday2/`, the rest under 45 `pd2_dlc_*` prefixes (list in `wpn_third_units.txt`).
Many modern DLC guns are absent from the hashlist's `wpn_third_*` set because their third-person parts live
beside the first-person ones under other names; the hashlist names 278,508 of 278,511 crate keys, so the
list above is the complete `wpn_third_` set, not a sample.

### 1.2 `wpn_npc_*` units (single-piece third-person guns)

`units/payday2/weapons/wpn_npc_*` (22): ak47, benelli, beretta92, c45 (1911), g36, lmg_m249, m4, m4_yellow,
mac11, mp5, mp5_tactical, r870, r870_taser, raging_bull, s552, saiga, sawnoff_shotgun, scar_murkywater,
smg_mp9, sniper, ump, upg_fl_ass_smg_sho_peqbox. DLC (17): bleckert, snowthrower, sg417, heavy_zeal_sniper,
mini, ak47 (mad), akmsu, asval, rpk, sr2, svd, flamethrower, svd_silenced, smoke, dmr, deagle (usm2),
sko12_conc. Full file lists: `<work>\pd2\wpn_npc_paths.txt`.

Each has: `<x>.unit` (type `wpn`, class `NPCRaycastWeaponBase`), `<x>.object` (orientation object `rp_*`,
`g_body` + `g_body_lod1` in a lod group, an `a_effect_flashlight` light), `<x>.material_config`
(`mtr_<gun>`: render template `generic:DIFFUSE_TEXTURE:NORMALMAP:RL_3RD_WEAPONS`, `<gun>_df` + `<gun>_nm`;
`weapon_lod1` = the diffuse at mip 2), `<x>.model`, `<x>.cooked_physics`, `<x>.sequence_manager`, and a
`<x>_contour.material_config` (the outline material the game swaps in). Read them in
`<work>\pd2\guns\src\units\payday2\weapons\wpn_npc_mp5\`.

### 1.3 Matches to the guns the looks pipeline knows

Dog Days F01 has 58 weapon templates (`dd_guns_F01.txt`); `kl_guns.LOOKS` pairs six of them with Dead Men
guns. Payday 2 units that are the same weapon (unit ids are the evidence; the in-game Payday 2 display names
in brackets are from memory, ASSUMPTION):

| weapon | Dog Days / Dead Men template | Payday 2 player assembly | Payday 2 single piece |
|---|---|---|---|
| AK-47 / AKM | DD `Rifle_AK47` (1,690 tris) | `wpn_third_ass_akm_pts` + `wpn_third_upg_ak_reusable` (AK.762) | `wpn_npc_ak47` (396) |
| AK-74 | DD `Rifle_AK74` | `wpn_third_ass_74_pts` + `upg_ak_reusable` | - |
| M4 / CAR-4 | DM `Rifle_M4A1_01` (look on DD AK47) | `wpn_third_ass_m4_pts` + `upg_m4_reusable` (CAR-4); `wpn_third_ass_amcar_pts` (AMCAR) | `wpn_npc_m4` (299) |
| MP5 | DM `Smg_MP5-A3_01` (look on the Zastava); DD `SMG_HK_sp89` is an MP5K | `wpn_third_smg_mp5_pts` (Compact-5) | `wpn_npc_mp5` (342), `wpn_npc_mp5_tactical` |
| P90 | DM `Smg_FN_P90_01` (look on the UMP) | `wpn_third_smg_p90_pts` | - |
| MAC-10 | DD `SMG_MAC_10` | `wpn_third_smg_mac10_pts` | `wpn_npc_mac11` |
| USP | DM `HG_HK_USP_01` (look on the M9) | `wpn_third_pis_usp_pts` | - |
| M9 / B92FS | DD `HG_M9Beretta` (1,724) | `wpn_third_pis_b92fs_pts` | `wpn_npc_beretta92` |
| Desert Eagle | DD `HG_DesertEagle` (1,204) | `wpn_third_pis_deagle_pts` | `wpn_npc_deagle` (pd2_dlc_usm2, 1,923: a newer, denser model) |
| SCAR | DD `Rifle_FN_SCAR` (2,432) | `wpn_third_ass_scar_pts` (pd2_dlc_dec5) | `wpn_npc_scar_murkywater` |
| G36 | neither game's FA levels (not in LOOKS) | `wpn_third_ass_g36_pts` | `wpn_npc_g36` |
| M14 | - | `wpn_third_ass_m14_pts` | - |
| UMP | DD `SMG_UMP` (3,112) | none (no player UMP in Payday 2) | `wpn_npc_ump` |
| SG 552 | DM `Rifle_SG552_01` (look on the SCAR) | `wpn_third_ass_s552_pts` (pd2_dlc1) | `wpn_npc_s552` |
| Steyr TMP | DM `Smg_SteyrTMP_01` | none | - |
| Remington 870 | DD `Shotgun_Remington_870` (1,182) | `wpn_third_shot_r870_pts` (Reinfeld 880) | `wpn_npc_r870` (441) |
| sawn-off | DD `Shotgun_Hawk_SawnOff` (2,955) | `shot_r870_pts` + `shot_shorty_pts` (Locomotive 12G, tweak id `serbu`) | `wpn_npc_sawnoff_shotgun` (254, a Mossberg) |
| Saiga | - | `wpn_third_shot_saiga_pts` | `wpn_npc_saiga` |
| Spas-12, TPS, Type 88/95/81, Minimi | DD only | - | `wpn_npc_lmg_m249` for the Minimi |

## 2. The six extracted guns

Extraction: `python tools/pd2_crate.py extract-prefix units/payday2/weapons/<folder>/ <work>\pd2\guns\src --xml`
for amcar_pts, upg_m4_reusable, ass_m4_pts, ass_akm_pts, upg_ak_reusable, smg_mp5_pts, pis_deagle_pts,
shot_r870_pts, shot_shorty_pts, sho_r870 and the npc ak47 / m4 / mp5 / r870 / sawnoff / beretta92 / c45 /
deagle (996 files, 8.9 MB), then `extract <path> object|model|unit` for the frame units
`wpn_fps_ass_amcar`, `wpn_fps_ass_akm`, `wpn_fps_smg_mp5`, `wpn_fps_pis_deagle`, `wpn_fps_shot_r870`,
`wpn_fps_shot_shorty`, `wpn_fps_ass_m4`. Parsed with `python -I tools/pd2_model.py info <file.model>`.

### 2.1 The single-piece NPC guns (model `.model`; all meshes rigid, `skin -`)

| unit | g_body tris / verts | lod1 tris | bounds (root space, cm: x right, y forward, z up) | textures |
|---|---|---|---|---|
| wpn_npc_mp5 | 342 / 518 | 199 | x -3.4..3.3, y -24.3..39.2, z -11.5..13.7 (63 cm) | mp5_df 256x256 DXT5 9 mips, mp5_nm 256x256 16-bit uncompressed |
| wpn_npc_ak47 | 396 / 575 | 174 | y -28.2..61.5 (90 cm), z -14.7..12.0 | ak_df 256x256 DXT5, ak_nm 256x256 16-bit |
| wpn_npc_m4 | 299 / 461 | 166 (+ s_body shadow 100) | y -23.8..51.7 (76 cm), z -11.6..16.2 | m4_df / m4_nm 256x256 |
| wpn_npc_r870 | 441 / 589 | 102 | y -34.7..81.8 (117 cm), z -11.6..11.2 | r870_df / r870_nm 256x256 |
| wpn_npc_sawnoff_shotgun | 254 / 302 | 146 | y -6.5..40.2 (47 cm), z -4.6..10.3 | sawnoff_df 128x64 DXT5, _nm 128x64 16-bit |
| wpn_npc_deagle (dlc_usm2) | g_base 1,284 + g_mag 221 + g_slide 418 | g_base_lod 1,923 | y -8.5..23.4 (32 cm), z -10.9..8.8 | wpn_npc_deagle_df 512x512 DXT1, _nm 512x512 DXT5 |

Object tree of every one: `rp_<gun>` (root) > `g_body`, `g_body_lod1`, `c_box` / `c_convex` (collision),
`co_weapon` (culling box), `a_effect_flashlight`, `fire` (the muzzle point: MP5 (0, 38.6, 8.7), AK
(0, 60.8, 6.5), M4 (0, 51.3, 7.9), R870 (0, 86.2, 7.6), sawn-off (0, 39.7, 6.5)), `a_shell` (ejection: MP5
(2.5, 9.0, 10.0), AK (1.9, 13.4, 9.0), M4 (1.9, 11.3, 7.9), R870 (2.3, 20.2, 7.6): always +x). The names
`fire` and `a_shell` were recovered by hashing candidates (`pd2_crate.hash64`); the lod material and the
collision material hashes (`aaf7523d2286628c` = `lambert1`, `84ea363244e1050b`) are not weapon data.

Renders (`pd2_model.py png ... --tex <df> --objs g_body --size 360`, default `--up y`, so the pictures show the
gun pointing up in the side view): `<work>\pd2\guns\png\npc_{mp5,ak47,m4,r870,sawnoff,deagle}.png`. Looked
at: the MP5 with magazine, rail and a light on top, the AK with wooden furniture, the pump shotgun, the Desert
Eagle are all recognisable and textured correctly (uv v is negative and counts from the bottom, as
`pd2_model.py` documents).

### 2.2 The modular player guns: frame + parts

The frame (`wpn_fps_<gun>_npc.unit` -> `<object file="units/payday2/weapons/wpn_fps_<gun>/wpn_fps_<gun>">`,
the same `.object` / `.model` as the first-person base; `.object` holds only the `orientation_object` and
`animation_group`s). The frame `.model` has NO visible mesh: `rp_*` root, the `a_*` attach points, animation
dummies (`anim_reload`, `anim_bolt_recoil` ...) and one 24-vertex box (`?f038c1cef41cc83f`, collision).
Attach points, named by hashing the identifiers of the tweak-data strings (`<work>\pd2\guns\lua\*.strings.txt`):

| hash | name | AMCAR (y fwd, z up) | AKM | MP5 (file x = 100: the whole MP5 family is modelled 100 cm off in x) | Deagle | R870 | Locomotive (`wpn_fps_shot_shorty`) |
|---|---|---|---|---|---|---|---|
| 3b827a5729b84e62 | a_body | 0,0,0 | 0,9.4,5.2 | 0,0,0 | 0,0.1,-0.4 | 0,21.7,7.6 | 0,21.7,7.6 |
| ff6acbe9fcf86ef3 | a_fg (foregrip) | 0,15.9,7.8 | -0.02,20.9,6.3 | 0,15.8,6.9 | 0,15.5,3.8 | 0,35.1,4.8 | 0,35.1,4.8 |
| 58bca285ef4abee3 | a_m (magazine; under the reload dummies) | 0,15.2,-3.6 | -0.04,14.5,-3.6 | 0,11.7,3.3 | 0,-2.8,-4.3 | 0,80.3,4.3 | 0,48.0,4.3 |
| a6ef6738f72b46f3 | a_s (stock) | 0,-4.4,7.8 | -0.02,-5.2,4.5 | 0,-3.9,7.0 | - | 0,-7.2,7.8 | 0,-7.2,7.8 |
| 9830bb4bc1da6a56 | a_g (grip) | 0,0,0 | 0,0,0 | - (part of the body) | 0,-0.5,-0.3 | 0,-1.3,-0.4 | 0,-1.3,-0.4 |
| d5219d441537330e | a_b (barrel) | 0,8.3,7.8 | -0.02,20.9,6.3 | 0,15.8,6.9 | 0,4.9,7.0 | 0,22.9,7.6 | 0,22.9,7.6 |
| 82f75e4a47d1c70d | a_o (optic) | 0,15.9,10.5 | 0,37.8,10.0 | 0,15.0,11.5 | 0.01,-17.1,0.5 (under the slide dummies) | 0,22.9,10.8 | 0,22.9,10.8 |
| 59fc1e8ad2056ef7 | a_bolt (under `anim_bolt_*`) | 0.74,11.0,8.4 | 3.0,18.9,7.5 | - | - | - | - |
| 59b6849c35623d8e | a_sight | 0,0.9,14.5 | 0,18.3,11.1 | 0,-3.6,12.7 | 0,-2.7,9.5 | 0,-3.4,11.7 | same |
| 44874e38d36501da | a_fl (light) | 3.75,29.2,7.8 | 2.5,37.2,6.4 | 2.3,22.9,7.8 | 0,15.5,2.8 | 0,56.3,0.7 | 0,48.0,0.7 |
| b4c6eb4590ce576e | a_vg (vertical grip) | - | 0,33.3,3.9 | 0,25.2,5.4 | - | 0,41.1,1.9 | same |
| 676b8e6cc3f3cbb5 | a_ns (suppressor) | - | 0,48.5,6.2 | 0.46,9.8,8.4 | - | - | - |
| 444b88323fc386e6 | fire (muzzle) | 0,54.0,7.8 | 0,48.5,6.2 | 0.46,9.8,8.4 (the MP5 barrel part carries its own) | 1.2,35.5,6.9 | 0,79.9,7.6 | 0,79.9,7.6 |
| 8edc2870924a7df7 | a_shell | 0.74,11.0,8.4 | 0.9,15.4,7.8 | 0.46,9.8,8.4 | 1.2,5.0,6.9 | 1.2,16.9,7.6 | same |
| others | a_os, a_dh (drag handle), a_charm, a_co, a_of, a_or, a_ol, a_o_2, a_fl_2, a_o_sm, a_o_krebs, a_b_beowulf, a_rds, a_quite | | | | | | |

Default blueprints (the strings right before `default_blueprint` in each `_init_<gun>` prototype of
`weaponfactorytweakdata`; part id -> `third_unit`, model, full-detail triangles, suggested Dog Days bone):

AMCAR (`wpn_fps_ass_amcar`, strings 3103-3170): frame `wpn_fps_ass_amcar_npc`; parts
`wpn_fps_m4_lower_reciever` (third: `wpn_third_ass_m4_pts/wpn_third_m4_lower_reciever`, g_lower_reciever
151 tris, w_bone_frame), `wpn_fps_amcar_uupg_body_upperreciever` (`wpn_third_ass_amcar_pts/..._uupg_body_upperreciever`,
g_body 245, frame), `wpn_fps_amcar_uupg_fg_amcar` (g_a2 116, frame), `wpn_fps_m4_uupg_b_medium_vanilla`
(`wpn_third_ass_m4_pts/wpn_third_m4_uupg_b_medium`, g_barrel 128, frame), `wpn_fps_upg_m4_m_straight_vanilla`
(`wpn_third_upg_m4_reusable/wpn_third_upg_m4_m_straight`, g_straight_mag 40, w_bone_clip),
`wpn_fps_upg_m4_s_standard_vanilla` (g 54, frame), `wpn_fps_upg_m4_g_standard_vanilla` (g 62, frame),
`wpn_fps_amcar_bolt_standard` (g_bolt 36, w_bone_slide). Total 832 triangles, 8 parts.
The part -> third_unit paths are in the strings too (line 3233: the three amcar `_pts` units, 3237-3266 the
first-person ones).

AKM (strings 5063-5148): frame `wpn_fps_ass_akm_npc`; `wpn_fps_ass_ak_body_lowerreceiver`
(`upg_ak_reusable/wpn_third_ass_ak_body_lowerreceiver`, 234), `wpn_fps_ass_akm_body_upperreceiver_vanilla`
(`ass_akm_pts/..._upperreceiver`, 80), `wpn_fps_ass_akm_b_standard` (`ass_akm_pts/..._b_standard`, 403; carries
its own `fire` at y 38 + rp 21.6 = 59.6 and `a_ns`), `wpn_upg_ak_fg_standard` (103), `wpn_upg_ak_m_akm`
(g_mag 100, clip), `wpn_upg_ak_g_standard` (72), `wpn_upg_ak_s_folding_vanilla` (g_folding 350). Total 1,342.

MP5 (strings 7985-8042): frame `wpn_fps_smg_mp5_npc`; `wpn_fps_smg_mp5_body_mp5` (g_mp5 228),
`wpn_fps_smg_mp5_fg_mp5a4` (244), `wpn_fps_smg_mp5_m_std` (g_std 56, clip), `wpn_fps_smg_mp5_s_solid`
(g_solid 148). Total 676. (The npc crew variant at 33358-33360 uses `s_ring` instead.)

Desert Eagle (strings 7571-7628): frame `wpn_fps_pis_deagle_npc`; `body_standard` (g_base 185 + g_slide 44:
slide -> w_bone_slide), `b_standard` (g_barrel 44), `g_standard` (g_grip 29), `m_standard` (g_mag 30, clip).
Total 332.

Reinfeld 880 = `wpn_fps_shot_r870` (strings 8790-8850): frame `wpn_fps_shot_r870_npc`; `body_standard`
(g_receiver 100), `b_long` (g_long_barrel 145, own `fire` at rp 22.9 + 63.3 = 86.2), `fg_big` (g_bigpump 50:
the pump -> w_bone_slide, as Dog Days' R870 has it), `s_solid_vanilla` (g_solid 66), `wpn_fps_upg_m4_g_standard`
(62). Total 423.

Locomotive 12G = `wpn_fps_shot_serbu` (strings 9150-9212): frame `wpn_fps_shot_shorty_npc` (same frame as
the R870 but `a_m` and `a_fl` moved back to y 48 and the muzzle box shortened); `body_standard` (100),
`b_short` (g_short 95, `fire` at 22.9 + 27.2 = 50.1), `fg_small` (g_smallpump 50), `s_nostock_vanilla`
(`shot_r870_pts/wpn_third_shot_r870_s_nostock`, g_folding 40), `upg_m4_g_standard` (62). Total 347. Its
own folder `wpn_third_shot_shorty_pts` holds only the three `_short` extras (strings 9278).

CAR-4 (`wpn_fps_ass_m4`): same frame family as the AMCAR; its default blueprint was not isolated in the
strings (the m4 prototype's constants are interleaved with the Para's) - AMCAR stands in for it here.

Part files: every part is one unit with `rp_<part>` + one (rarely two) `g_*` mesh, authored IN THE WEAPON'S
FRAME: the part's `rp_` sits where the frame's attach point is (AMCAR: fg rp (0, 15.86, 7.78) = a_fg; stock rp
(0, -4.39, 7.78) = a_s; mag rp (0, 15.20, -3.60) = the magazine dummy; bolt rp (0.74, 11.0, 8.38) = the bolt
dummy; grip rp = a_g = origin), so the root-space bounds of the parts tile the gun directly (MP5: stock y
-27..-3, body -6..17, magazine 11..20 reaching z -11.6, foregrip 15..39; all at x 100). EXCEPTION found: the
Desert Eagle body's rp is (0, 4.0, 0) while a_body is (0, 0.14, -0.42): there the engine's link
(`unit:link(a_obj, part, part:orientation_object())`) moves the part by (0, -3.9, -0.4). So a converter must
do the real thing - part world = a_obj frame x (part geometry relative to its rp) - and needs each part's
`a_obj`. The strings show the `a_obj` key but LuaJIT constants do not keep the part -> value pairing;
ASSUMPTION until the bytecode is decoded: body/upper/lower -> a_body, fg -> a_fg, m -> a_m, s -> a_s, g -> a_g,
b -> a_b, o -> a_o, bolt -> a_bolt, ns -> a_ns, fl -> a_fl, vg -> a_vg (the Payday 2 naming convention; the
rp = attach point equality above confirms it for every AMCAR / AKM / MP5 / R870 part measured).

Part materials: one material per part (`generic:DIFFUSE_TEXTURE:NORMALMAP`), own `_df` / `_nm` textures,
64x64 to 256x256 DXT5 (the AMCAR upper 256x256 both maps, its foregrip 128x128). Over the 208 textures
extracted: 51 are 128x128, 41 are 64x64, 26 256x128, 16 256x256, 8 at 32x32; one 512x512 pair (the DLC
Deagle). All DXT5 except 7 uncompressed 16-bit normal maps of the older npc guns (DDS pixel-format flags
without FOURCC, 16 bits; two-channel, ASSUMPTION V8U8) and the DLC Deagle's DXT1 diffuse.

## 3. The frame: grip and muzzle, Payday 2 vs Dog Days

Payday 2 (all weapon models read): origin = `a_g` / the grip attach point (AMCAR, AKM, CAR-4: exactly (0,0,0);
Deagle (0, -0.5, -0.3); R870 (0, -1.3, -0.4)); the grip part itself hangs below it (AMCAR g_standard box
y -6.9..2.0, z -7.0..2.9; AK g_grip y -4.4..2.5, z -7.7..3.0; Deagle g_grip y -2.1..5.9, z -7.3..3.9).
Muzzle = `fire`: AMCAR y 54.0, AKM 48.5 (plus the barrel part's own at 59.6), M4 51.4, MP5 npc 38.6,
Deagle 35.5, R870 79.9, Locomotive 50.1; all at z 6-8.4 (the bore line is 6-8 cm above the grip point).
Magazines go down (a_m z -3.6, magazine boxes to z -11..-15), optics up (a_o z 10-11.5), ejection +x.

Dog Days (stock F01 `.prm`, `dd_guns_F01.txt`): origin = bone `GROUND`; the gun's length runs along +x
(rifles x -18..70-76, the R870 -21..89, pistols 3.4..32), up is +y (magazines reach y -14.7 on the AK, the
Beretta grip bottom y -4.9, slide top +9.7), the thin axis is z (-3.8..3.7). The AK's `w_bone_slide` part
(the charging handle, right side on an AK) has its vertices at z -3.8..-1.0 (centroid -2.6; the Zastava's
-2.2..0.1, the SCAR's -2.4..-0.7): the gun's RIGHT is -z. So

    DD.x = PD2.y   (forward)
    DD.y = PD2.z   (up)
    DD.z = -PD2.x  (left)      a rotation, det +1; no mirroring of triangles or normals needed.

Grip place: Dog Days' pistol grips start at x 3.4-3.8 behind the trigger and span y -5..+5 (Deagle: the
89-vertex grip part x 3.5..12.7, y -5.2..5.2; Beretta clip x 4.7..11.1, y -4.9..2.3), so the Dog Days origin
is ~4 cm behind and ~2 cm below Payday 2's grip point. Rifles: Dog Days AK magazine x 20.8..30.6 vs Payday 2
AK a_m y 14.5 with the magazine box y 9.5..23 -> ~+4 cm in Dog Days too. So the per-gun translation after the
rotation is of the order of (+4, +2, 0) cm (ASSUMPTION from two pistols and one rifle; tune by overlaying
with `kl_guns.py sheet` / `kl_view`, exactly as the Dead Men looks were checked). Scale: both centimetres;
Payday 2 npc AK 89.7 cm vs Dog Days 87.5, MP5 63 vs the Zastava 60; Deagle 32 vs 29.

Dog Days bone rest positions: the 64-byte bone definitions (`kl_chars.bone_names` reads +0x1c name, +0x0c
parent) hold floats at +0x00 and +0x10 that this survey printed as "rest positions" (Zastava w_bone_frame
(-0.7, -0.7, 19.4) / (2.3, 13.1, 29.5)); they do not land on the mesh, so they are not plain model-space
positions - NOT DECODED, not needed for the looks (parts are in model space; kl_guns relies on the same).

## 4. How Payday 2 assembles a third-person gun, and what a converter must assemble

Evidence: `weaponfactorytweakdata` strings (`<work>\pd2\guns\lua\weaponfactorytweakdata.strings.txt`): each
weapon has `unit` (first person), the `_npc` frame unit (`units/.../wpn_fps_<gun>/wpn_fps_<gun>_npc`, strings
3103, 5063, 7572, 7985, 8790, 9151), `uses_parts` (every part allowed on it, ~60-120 ids) and
`default_blueprint` (5-8 ids); each part has `unit` (first person), `third_unit`, `a_obj`, `type`, `parent`,
`stats` ... (keys visible around 3231-3266: `stock_adapter`, `unit`, `bolt`, `foregrip`, `third_unit`). The
frame `.unit` names the class `NewNPCRaycastWeaponBase` and the sound bank; the parts' `.unit` files are bare
(`ScriptUnitData` only). The frame `.object` only lists animation groups whose objects are the `anim_*`
dummies: reload moves the `a_m` subtree, recoil / bolt the `a_bolt` subtree (AMCAR: `anim_bolt_recoil >
anim_bolt_last_recoil > anim_bolt_reload > a_bolt`), the Deagle's slide dummies hold `a_o` and `a_rds`.

For the STOCK look a converter assembles: the default_blueprint's parts, each `third_unit` model's `g_*`
mesh(es) placed by `a_obj` frame x (geometry - rp) (section 2.2), with the x = 100 modelling offset of the
MP5 family removed (the frame's rp is at x 100 as well, so "world = root space - frame rp" handles it),
then the axis rotation and translation of section 3. Textures: one `_df` (+ `_nm`) per part -> one Dog Days
material per part (or atlas them; 4-8 small DXT5 maps per gun is fine against the 4096-texture limit).
Variants (`_vanilla` suffixes are stat variants of the same unit; `_gold` the golden AK) need no separate
geometry. Skins (`weapon_skins`) are material swaps and are out of scope.

The npc single-piece guns need NONE of that: one mesh, one material, the rotation and translation.

## 5. Sizes

Full-detail triangles (Dog Days from `dd_guns_F01.txt`, Payday 2 from `pd2_model.py info`):

| gun | Dog Days stock model | Payday 2 npc single piece | Payday 2 assembled default blueprint | Payday 2 first person (for contrast) |
|---|---|---|---|---|
| MP5 / Zastava M85 | Rifle_zastavam85 1,786 (5 parts, 1,786 verts) | wpn_npc_mp5 342 | 676 (4 parts) | mp5 body alone 6,332 |
| AK-47 | Rifle_AK47 1,690 (6 parts) | wpn_npc_ak47 396 | AKM 1,342 (7 parts) | - |
| M4 | (DM M4A1 look) | wpn_npc_m4 299 | AMCAR 832 (8 parts) | - |
| Beretta M9 | HG_M9Beretta 1,724 | wpn_npc_beretta92 (not parsed) | - | - |
| Desert Eagle | HG_DesertEagle 1,204 (7 parts) | wpn_npc_deagle 1,923 (DLC remake) | 332 (4 parts) | - |
| Remington 870 | Shotgun_Remington_870 1,182 | wpn_npc_r870 441 | 423 (5 parts) | - |
| sawn-off | Shotgun_Hawk_SawnOff 2,955 | wpn_npc_sawnoff 254 | Locomotive 347 | - |
| UMP | SMG_UMP 3,112 | wpn_npc_ump (not parsed) | - | - |
| SCAR | Rifle_FN_SCAR 2,432 | wpn_npc_scar_murkywater (not parsed) | - | - |

So the premise "Payday 2 models are far denser" holds only for the first-person meshes. The third-person
Payday 2 guns are 2-5x LIGHTER than Dog Days' and their textures (64-256 px) smaller than the Dog Days gun
textures. A Payday 2 look costs the level a few KB of `.prm` and a few small textures: the `.prm` size budget
(90 MB cap in kl_graft, the fixed chunk table) is not touched by a handful of guns. Per-part chunk count:
each look adds one 64-byte object chunk per part plus the shared geometry chunks; an assembled gun of 8
parts is 8 objects, an npc gun 1.

Dog Days lod: every stock gun has lod parts (`w_bone_frame(lod16)` 20-38 tris, some lod2/4/8 copies). A
Payday 2 look with only the full-detail meshes marked at full detail passes `kl_guns.check` (it asks for at
least one full-detail part per look); the npc guns' `g_body_lod1` could be put in as the lod part if the lod
mask bits are reproduced (ASSUMPTION on which bits; copy the stock gun's).

## 6. Plan, in tiers

Tier 1 - npc single-piece guns as looks (smallest step, no assembly, no Lua):
  `tools/pd2_gun.py` (new): read `wpn_npc_<x>.model` (`pd2_model.Model`), take `g_body` (full detail) and
  `g_body_lod1` (lod), rotate (section 3), translate (per-gun constant, default (+4, +2, 0)), build ONE rigid
  part on `w_bone_frame` (nothing moves: the magazine stays put during reloads - accepted for tier 1), a
  material from `mtr_<x>` with the `_df` (DXT5 -> the Dog Days `.TEX` form; the normal map can wait: the
  stock Dog Days gun materials' stage set has to be checked before a bump map is wired), and hand it to
  `kl_guns.LOOKS` as a third source game `'pd2'` next to `'dm'` / `'dd'`. Candidates: MP5 on the Zastava,
  AK on the AK47, M4 on the AK47, R870 on the Remington, sawn-off on the Hawk, Beretta on the M9, the DLC
  Deagle on the Desert Eagle. The geometry path exists in `tools/kl_pd2mask.py` (Diesel vertex streams,
  uv v flip, DXT decode / re-encode to Dog Days textures) for skinned masks; the rigid gun part is the same
  minus bones - CHECK the rigid part vertex layout of the stock gun parts (the stride the survey script
  divided by) against what kl_pd2mask writes.
  Check: `kl_guns.check` 0 problems, `kl_guns.py sheet` picture over the Dog Days gun, verify problems: 0.
Tier 2 - the modular stock look (recognisably the Payday 2 crew's guns, moving magazine / bolt):
  decode `default_blueprint` + `third_unit` + `a_obj` per part. Two routes: (a) decode the LuaJIT 2
  bytecode constant tables and table constructors of the `_init_<gun>` prototypes (the strings are in
  first-use order per prototype, so a small LuaJIT reader gives the key -> value pairs exactly), or
  (b) a hand-written table for the 6-10 guns wanted (the blueprints above) with the a_obj convention as an
  ASSUMPTION and the rp = attach-point equality as the check (flag any part whose rp differs from the
  frame's point, like the Deagle body). Parts -> bones: m_* -> w_bone_clip, bolt / slide / pump ->
  w_bone_slide, the rest -> w_bone_frame (same pivot caveat as the Dead Men looks: the Payday 2 magazine
  turns about the Dog Days gun's clip pivot).
Tier 3 - more: the other 20 matched guns of section 1.3, mods from `uses_parts` as further looks (sights,
  suppressors), the lod part, normal maps, the shop name / picture (not done for the Dead Men looks either),
  the engraved / gold variants. Payday 2 skins and the first-person meshes: no.

Unknowns, in order of risk:
  - whether a part's variant byte is read every frame or cached (kl_guns' G2; decides whether any look
    switch works at all; not a Payday 2 question).
  - the exact grip offset per gun (section 3, a few cm; a picture settles it).
  - the Dog Days rigid-part vertex format and material stage set for guns (whether a normal map slot exists
    in the stock gun materials' technique; `kl_texmat` / `.MAT` entry).
  - the a_obj pairing without decoding LuaJIT (tier 2 only).
  - how Dog Days' lod mask bits for gun parts are chosen (copy the stock gun's pattern).
  - rights: Payday 2 assets stay on the owner's machine (CLAUDE.md rule), as for the masks.

## Files

- `<work>\pd2\wpn_third_paths.txt`, `wpn_third_units.txt`, `wpn_npc_paths.txt`: the inventories.
- `<work>\pd2\guns\src\units\...`: the extracted units (+ `.xml` beside the binary XML files).
- `<work>\pd2\guns\lua\weaponfactorytweakdata.luac|.strings.txt`, `weapontweakdata.luac|.strings.txt`.
- `<work>\pd2\guns\png\npc_*.png`: renders. `<work>\pd2\guns\dd_guns_F01.txt`: the Dog Days survey.
- Scratch survey script: the session scratchpad `ddguns.py` (uses `kl_chars.Lv('F01')`, `C.objects`,
  `C.skeleton`, `C.bone_names`; reproduce from section 3's description if needed).
