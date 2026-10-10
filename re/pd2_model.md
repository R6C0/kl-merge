# Payday 2 (Diesel) .model and .texture - decoded (2026-10-10)

Tool: `tools/pd2_model.py` (pure Python, module + CLI; its docstring is the format reference). Everything
below was measured on the 661 `.model` files under `<work>\pd2\extract` (Steam build 25506656, extracted with
`tools/pd2_crate.py`). Pictures and OBJ / DDS exports: `<work>\pd2\models\` (53 files, 29 MB; never in the repo).
The K&L side (HEAD frame, target box, variant capacity) is `re/pd2_klside.md`; the Payday 2 attach side that
another workflow wrote is `re/pd2_attach.md`.

## 1. File format - established

* Header `'DODB' u32 1  u32 file size  u32 section count`, then sections `{u32 type, u32 id, u32 size, body}`
  back to back to the end (count and sizes add up exactly in all 661 files). The public tools describe an
  older bundle-era header (`u32 -1, size, count`); the crate-era files have this 16-byte one.
* Section ids are 1-based and what other sections refer to. Names are 64-bit Jenkins lookup8 hashes
  (`pd2_crate.hash64`) of the plain name: `hash64('rp_wolf_mask')` is the wolf's root object. The
  shipped `hashlist` holds paths, not object names; the module hashes candidates (bone names, every word
  of the unit's XML files next to the model, a built-in list) and prints `?<hash>` for the rest
  (the body: 3 of 104 objects unnamed; every mask root and mesh resolves).
* Section types seen (count over 661 files) and layouts: see the docstring table. Every hint from the
  public tools (Geometry 7ab072d3, Topology 4c507a13, Model 62212d88, Object3D 0ffcd100, Material 3c54609c,
  MaterialGroup 29276b1d, SkinBones 65cc1825, PassthroughGP e3a3b1ca, TopologyIP 03b634bd, Author 7623c465)
  was verified against the bytes. Not present in any of the 661 files: Bones 2eb43c77, ModelToolHashes
  7c7844fd. Extra: file header 5dc011b8 and two animation-key controllers (26a5128c position, 648a206c
  rotation; only the two fps strap models).
* Geometry streams are NOT interleaved: `u32 vertex count, u32 stream count, {u32 size code, u32 type}`,
  then each stream in turn, 8-byte tail (a hash; 6 distinct over 1067 geometries, ASSUMPTION: the vertex
  layout's name). Size codes proved by the section size: 3 = 12 B, 2 = 8, 7 = 8, 8 = 4, 9 = 4, 5 = 4.
  Types: 1 position 3f, 7 uv0 half2, 8 uv1 half2, 2 normal / 22 tangent / 23 binormal as 4 x u8 with
  x = byte 2, y = byte 1, z = byte 0 (mean dot with the face normals 0.83 for that order on the wolf,
  0.47 for the next best, 0.02 for the public tools' order), 17 bone indices 4 x u16, 19 bone weights 3f,
  5 colour 4 x u8, one geometry with an unknown type 9 (not used here).
* UVs: u 0..1 left to right; v is 0..-1 and counts from the BOTTOM: DDS row from the top = 1 + v. Proof on
  the wolf and dallas plates: chin vertices -v 0.09, eye-hole rims 0.43 / 0.46, brow 0.5..0.8, while the
  DDS has the chin at the bottom and the eye sockets at row 0.53. OBJ `vt = -v`. uv1 (second set, 721 of
  1067 geometries) is unused by this tool (ASSUMPTION: the pattern / customisation set).
* Model section (version 3): Object3D fields, `u32 PassthroughGP id, u32 TopologyIP id, u32 atom count,
  atoms {base vertex, triangle count, base index, vertex count, material index} , u32 MaterialGroup id,
  u32 lightset, u32 properties, float[6] box, float radius, u32 6, u32 SkinBones id (0 = rigid)`.
  Version 6 = collision primitives (c_sphere_head, c_capsule_body): box + radius only.
* Object3D: name hash, controller list, float[16] row-vector matrix (world = local x parent), float[3]
  position (repeats the translation), u32 parent id.
* SkinBones: list count, lists of bone slots, root object (Hips), bone object ids, float[16] inverse bind
  per bone, float[16] global (= Hips' matrix). Skinned vertices are stored in ROOT space (the g_* models
  hang under Hips with Hips' inverse as their local matrix), rigid ones in the Model's space.

## 2. Units and axes - established

Centimetres, Z up, +Y forward in a character file: the criminal body's Head object is at world
(0, 5.33, 166.76), the head meshes end at z 187.5..187.8, the nose points +y. The Hips matrix maps local
(x, y, z) to world (-x, z, y); every bone below keeps that frame, so Head local x = the character's LEFT,
y = up, z = forward.

A MASK FILE'S ROOT SPACE IS THAT HEAD FRAME: the mask is placed at the body's Head object with identity.
Evidence: placed so, the wolf's box is (-9.8, 6.5, 160.8)..(9.8, 23.9, 188.8) in world against the wolf
head mesh (-9.6, -3.3, 152.4)..(9.6, 20.5, 187.5): same width, same top, 1.2..18.6 cm in front of the
joint; and in `wolf_on_head.png` / `dallas_on_head.png` the head's eyes look out of the mask's eye holes
and the plate covers the face from the hairline to under the chin.

## 3. The crew masks (rigid plates; all by GUSTAVS-DATOR, all_masks.mb)

| unit | mesh | verts / tris | box in Head space (x left, y up, z fwd) | eye-hole centres | material | textures |
|---|---|---|---|---|---|---|
| msk_wolf | rp_wolf_mask > g_wolf | 853 / 926 | (-9.80, -6.01, 1.19)..(9.80, 22.05, 18.59) | (+-3.58, 7.96, 12.25), 2.9 wide | mtr_mask_wolf | wolf_df / wolf_nm DXT5 512x512x10 |
| msk_dallas | rp_dallas_mask > g_dallas | 976 / 1176 | (-9.66, -6.85, 1.19)..(9.65, 22.05, 18.72) | (+-3.58, 8.05, 12.30) | mtr_dallas_mask | dallas_df / _nm, same |
| msk_chains | rp_chains_mask > g_chains | 1193 / 1554 | (-9.80, -6.01, 1.19)..(9.80, 21.95, 18.73) | (+-3.83, 8.19, 11.68) | mtr_chains_mask | chains_df / _nm, same |
| msk_hoxton | rp_hoxton_mask > g_hoxton | 1089 / 1300 | (-9.63, -7.84, 1.19)..(9.63, 22.23, 19.75) | (+-3.40, 8.19, 12.25) | mtr_hoxton_mask | hoxton_df / _nm, same |
| msk_dallas_clean | same tree as dallas | 970 / 1176 | as dallas | as dallas | mtr_dallas_mask | dallas_clean_df / _nm |
| msk_dallas_glow (dlc_cop) | rp_dallas_glow_mask > g_dallas, g_glow1, g_glow2 + e_e_1 / e_e_2 (eye effect points at (+-3.89, 9.23, 12.55)) | 1079+487+473 | (-10.0, -6.0, 1.2)..(10.0, 23.4, 19.2) | - | mtr_dallas_glow, sweep1, glow2 | msk_dallas_glow_df / _nm / _il |
| fps_temp_dallas | rp_back_straps (rotated) > back (5 strap children), top; 3 meshes | - | first-person inside view, 1024 textures | - | mtr_backside, mat_dallas | temp_mask_dallas_*, temp_mask_inside_* |
| msk_fps_back_straps | rp_back_strapets > ? > back ...; 2 meshes, position / rotation controllers | - | the straps behind the head (fps) | - | mtr_backside | msk_fps_back_straps_df / _nm 1024 |

Every mesh has one render atom and one material; the Material sections are 52 identical bytes after the
name (the real material is the unit's `.material_config`). Each plate's boundary has three large loops
(outer rim, inner rim, the rim's edge band: the plate has thickness) and the two eye holes. The holes are
2.9..3.5 cm wide; the eye-hole centres are 6.8..7.7 cm apart.

What the pictures show (`<work>\pd2\models\msk_*.png`, front / side / top, textured with the top mip):
wolf = white skull dome, black eye sockets, red lower face with bared teeth; dallas = stars-and-stripes
over a white clown face, red nose, red grin; chains = white face, black eye markings with blue tear
lines, red nose and lips, purple cheeks, a blue star; hoxton = magenta eye and cheek patches, red lips,
small stars. `wolf_nm.png`: a proper tangent-space normal map (A2D5: x in alpha, y in green).

## 4. The criminal body (units/payday2/characters/npc_criminals_suit_1)

104 objects, 42 meshes (heads for dallas, chains, wolf, hoxton, old_hoxton, dragan, sokol, john_wick,
jiro, bodhi, jimmy, jacket; bodies, gloves, vests, bags, a shadow caster), 41 SkinBones, author
david.tornqvist@starbreeze.com. Joint chain root_point > Hips (0, 5.33, 101.78) > Spine 12.97 > Spine1
12.20 > Spine2 12.23 > Neck 20.16 > Head 7.43 (bone lengths along local y) = Head at z 166.76. Height:
head tops 187.5..187.8 (jimmy's mask 193.6); the g_body box ends at 165-167 (collar). The `.object` XML
enables one head (`g_head_dallas`) + `g_body` + `g_hands` + `s_body`; the `.unit` binds `c_sphere_head`
to Head (centre (0, 6.53, 2.11) local, radius 10.2).

Head meshes in Head space (vertices whose dominant bone is Head): wolf (-9.61, -5.05, -8.65)..(9.61,
20.73, 15.13); dallas (-8.82, -4.38, -8.14)..(8.80, 21.01, 14.66); chains, hoxton within 0.5 of these.
So a Payday 2 head is 19.2 wide, 21 above the joint, nose 15 in front.

`npc_criminals_suit_1.png`: a bald, bearded man in a tan suit, white shirt, dark tie, blue gloves,
A-pose, drawn from g_body + g_hands + g_head_wolf with suite_03_body_df / criminal_gloves_df /
wolf_head_df. `npc_criminals_suit_1.obj`: all 42 meshes, 90,802 faces, root space.

## 5. Fit to the Kane & Lynch 2 head - proposal

K&L HEAD frame (re/pd2_klside.md): X up, Y back (face -Y), Z right; eyes at (6.5, -11.5, +-3.3),
whole-head mask box (-14.7, -17.0, -10.2)..(20.9, 10.8, 10.4). Payday 2 Head frame: x left, y up,
z forward. Axis mapping: **X = y, Y = -z, Z = -x** (a pure rotation).

In K&L axes the wolf plate is X -6.0..22.1, Y -18.6..-1.2, Z +-9.8 with the eye holes at (7.96, -12.25,
+-3.58). Scale: 1.0 - the head tops agree (Payday 2 +21.0, K&L +20.9 above the joint) and the K&L heads
are WIDER (20.6 vs 19.2), so shrinking to the eye distance (0.86..0.97) would make the cheeks poke
through. Translation in HEAD space (eye-hole centres onto the K&L eye line):

| mask | translation (X, Y, Z) | mask front after | over the K&L box front -17.0 by |
|---|---|---|---|
| wolf | (-1.46, +0.75, 0) | Y -17.84 | 0.8 |
| dallas | (-1.55, +0.80, 0) | -17.92 | 0.9 |
| chains | (-1.69, +0.18, 0) | -18.55 | 1.6 |
| hoxton | (-1.69, +0.75, 0) | -19.00 | 2.0 |

A common (-1.6, +0.7, 0) is within 0.5 cm of all four. The plate's top (X 20.5 after the shift) stays
under the K&L box top 20.9; its bottom (X -7.6) reaches 3.6 below the chin bone (-4), as a plate that
covers the jaw should. The root's six box floats must widen by ~1-2 cm
at the front (re/pd2_klside.md section 2). ASSUMPTIONS: the K&L eye anchors are face-bone rest
positions, the Payday 2 ones are hole centroids; the 1.5 cm vertical difference may partly be that.
Check in kl_view on J.C. and Kane (poke-through at nose and cheeks) before fixing the numbers.
`python tools/pd2_model.py head <body> <mask>` prints the table's row for any mask.

## 6. Scan of all 661 .model files

`<work>\pd2\models\scan.json`: 661 parsed, 0 failed, 0 unknown section types. Stream layouts: 679
geometries `position uv0 uv1 normal tangent binormal`, 197 without uv1, 93 `position uv0 normal`, 44
skinned (`+ bone_indices bone_weights`), 39 `position uv0 uv1 normal`, 5 position only, 5 position +
normal, 3 with colour, 1 skinned shadow caster with 2-float weights, 1 with stream type 9. Model
sections: 1044 x 176 bytes (1 atom), 16 x 196 (2), 6 x 216 (3), 1 x 256 (5), 7 x 128 (version 6
primitives).

## 7. Still open

* Object-name hashes not resolved: 3 in the body (a Head child at (0, 8.2, 15) = ASSUMPTION a look-at
  point; two helpers under Spine2 / Spine1) and the unnamed intermediate of msk_fps_back_straps.
* uv1's meaning, the Geometry tail hash, the Model's `u32 6` and the material's 52 bytes.
* The `.material_config` -> texture binding for the plates is read by eye from the XML (mtr_mask_wolf:
  pattern_no_color_no_material_df + matcap layers in branch 1, tint colours in branch 2, re/pd2_attach.md);
  the plain `_df` is what the pictures use. Which branch the game renders for a crew mask is not known.
* Nothing is converted to a K&L .prm yet (that is tools/kl_pd2mask.py, next job).

## Verification (2026-10-10, skeptical re-run by a second agent; scripts in the session scratchpad: verify_a2.py / verify_b.py / verify_c.py)

Re-run on the real files: all 661 `.model` files, the four crew masks, the criminal body and 30 random other
masks (seed 20261010). Independent code (not the module's) for the header / section accounting, the head
chain, the normal byte order, the winding and the OBJ boxes.

HOLDS: header `'DODB' 1 size count`, section sizes add up and ids are 1..n in all 661; `scan` 661 / 0 / 0 and the
Model-section size histogram (1044 x 176, 16 x 196, 6 x 216, 1 x 256, 7 x 128); Material bodies: ONE distinct
52-byte value in all 1590; `u32 6` in all 1067 Model v3 sections (lightset 0, properties 3, the 7 v6 ones 0);
every Model box equals its raw vertex box to 0.00; hash64('rp_wolf_mask') = 03a3b6d53742e6fa = the wolf root;
Head chain reproduced by row-vector products, world (0, 5.33, 166.76), rows (-1 0 0 / 0 0 1 / 0 1 0) (column order
gives (0, 70.3, 101.8): wrong, so the convention is proved); inverse bind x Head world = identity; LeftHand at world
x -46 / RightHand +46 with the body facing +y, so Head local x = world -x = the character's LEFT; the four masks'
boxes, vertex / triangle counts, eye-hole centres (sep 7.17 / 7.17 / 7.65 / 6.80) and the fit lines reproduce to
the digit; OBJ boxes = module boxes, 926 / 1176 / 1554 / 1300 / 90,802 faces; packed-normal byte order (2,1,0)
is the best of all 24 permutations on 92 of 93 sampled meshes (one hair-like body part scores 0.15 for every
order), lengths 0.99..1.01; uv u 0..1, v 0..-1 in the masks (a few body parts tile to 1.42 / -1.99 / 3.31); the
UV-row claim: wolf chin band mean v -0.09, top band -0.69, and the DDS rows 0..204 are white (mean rgb 222),
rows 307..512 dark red (54,13,14): row = 1 + v is right; the PNGs show what section 3 says (wolf, dallas, chains,
hoxton, body, wolf_nm checked by eye; the on-head pictures have the eyes in the holes); no file under the PAYDAY 2
folder is newer than 2026-10-10 00:00 and nothing of this is in the repo or the Dog Days folder.

CORRECTIONS:
1. "No NVTT writer tag (reserved bytes ' \0\0\0')" is WRONG: `dds_info` reads offset 76, which is the pixel
   format's dwSize (32 = 0x20 = ' '). The reserved1 words at offset 60 hold 'UVER' and at 68 'NVTT' + version
   bytes 02 01 02 00 (NVTT 2.1.2) in wolf_df and wolf_nm. Harmless for decoding, but the docstring's 'writer'
   field and the summary's statement should say so.
2. The 8-byte Geometry tail has 368 distinct values over 1067 geometries, not 6; it equals neither the Model's
   nor the Topology's name hash. The 'vertex layout name' assumption is refuted; it is per-geometry data of
   unknown meaning.
3. SkinBones lists: 2 in 41 sections, 3 in 4 (all in the body, lists of 1 or 3 slots each); not "2 in every file".
4. FileHeader second / third u32: besides 0x3d088988 (157 files) and 0 (496) there are 1.0 (6 files) and
   two files with (-0.4667, 1.7) / (-0.4667, 1.8) as floats: not a mask / body split.
5. Section 5's "plate bottom X -7.6" holds for wolf / dallas only (-7.5 / -8.4); chains -7.7, hoxton -9.5.
6. "Head tops 187.5..187.8" excludes g_head_sokol (181.0; the mesh stops under its cap).

ADDED FACT (needed by kl_pd2mask.py, not stated before): the stored triangle order is COUNTER-clockwise seen
from the normal side: the right-hand face normal agrees with the stored vertex normals on 926 / 1176 / 1554 /
1300 of the four plates' triangles (0 disagree), and 95 % of the front triangles have it along +z. K&L stores
clockwise from outside (re/pd2_klside.md section 2), so the converter must REVERSE every triangle.
