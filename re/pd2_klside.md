# Payday 2 masks, the Kane & Lynch side: what the converter needs

2026-10-10 (agent A4). Everything a tool needs to put a RIGID Payday 2 mask into the wardrobe's Mask row
(re/wardrobe.md; tools/kl_chars.py wardrobe, klhook/klchar.c). "Established" = measured on the stock Dog Days
F01 (`<DD>\KL_PortBackup\...\F01_Main.zip`), on the owner's build `<W>\build\x_chunks\retomoto_wardrobe`, or read
in kl2.exe at the address given. ASSUMPTION is meant literally. Scripts and their outputs: `<W>\pd2\kl\`
(f01_geometry.py/.log/.json, heads16.py/.log/.json, mask_dump.json, find_variant_cmp.py/.txt, find_158.py,
mat_tex.py/.txt, normals4.py, fix_dump.py, winding.py). Nothing here was run in the game.

Coordinates: model space is in centimetres (body boxes 180.5 .. 183.5 high), +y up, **-z = the face / front**,
**+x = the character's LEFT** (J.C. LEFT_HAND rest (51.1, 107.5, -1.2), RIGHT_HAND (-51.1, ..); fix_dump.py).

## 1. The skinned vertex (52 bytes, mesh subtype 3) - established

Per vertex (J.C.'s stock mask object 451, body 391, Jean's mask 974; f01_geometry.log 'THE 52-BYTE VERTEX',
fix_dump.py, normals4.py, winding.py):

| offset | content | evidence |
|---|---|---|
| +0 | f32 x3 position, model space, bind pose | boxes match the body / head |
| +12 | f32 x3 weights, the fourth = 1 - sum | sums 0.78 .. 1.0, median 1.0 |
| +24 | u8 x4 = **3 x palette entry** (index into the object's bone runs, +0x38 / +0x3c) | every byte a multiple of 3; max 18 = 3 x 6 for a 7-entry palette |
| +28 | normal, bytes B,G,R,0: `n = ((b2-128)/127, (b1-128)/127, (b0-128)/127)` | unit length (|v| 0.99 .. 1.02); 95.6 % point away from the mask's centroid; the 20 front-most vertices average (0.04, -0.29, -0.73), top-most (-0.06, 0.96, -0.02), right-most (0.95, ..) |
| +32 | vertex colour D3DCOLOR | 0xffffffff on every heister vertex |
| +36 | f32 x2 texture coordinate (u right, v down, 0..1) | u, v in 0.004 .. 0.997 |
| +44 | tangent = +dP/du, same packing as the normal | agrees in sign with the triangle's dP/du on 99.5 .. 100 % of triangles (winding.py) |
| +48 | binormal = +dP/dv, same packing | agrees with dP/dv on 99.2 .. 100 %; N x T . B > 0 on 93 % of the mask's vertices (67 % on the body: mirrored UV islands) |

Rejected packings for +28/+44/+48 (not unit length): int8/127, 10-10-10-2 signed and unsigned, 2 x f16.
A rigid Payday 2 mask: weights (1, 0, 0), palette bytes (0, 0, 0, 0), one bone run {12 x 1, 12 x 7} (count 1,
first bone HEAD = bone 7 in every one of the 16 skeletons), tangent / binormal computed from the UVs, colour
0xffffffff.

**Other vertex formats in F01's .prm** (f01_geometry.log 'ALL MESH OBJECTS'; walk from every root; stride =
vertex chunk bytes / descriptor[0]): subtype 0 (static, 3,536 objects) stride 40 (2,870) or 36 (51); subtype 1
(118, mostly without a vertex chunk of their own; one of stride 120); subtype 2 (278, rigid on ONE bone: +0x38 =
the bone number, not a chunk) stride 40; subtype 3 (357, weighted) stride 52 in all 345 that have vertices; one
128-byte mesh (static shadow). A Payday 2 mask could be a subtype-2 object (rigid, one bone, stride 40) but
every stock mask object is subtype 3 / stride 52 under material class 3 (SkinCloth / Skin / STYP Weighted);
kl_view and kl_chars.check_wardrobe assume 52 - keep subtype 3.

## 2. The geometry chunks - established

Mesh object (64 bytes, lType 8; mask_dump.json `object_dwords`, kl_prmgraph docstring):

| offset | J.C. mask value | meaning |
|---|---|---|
| +0 | 89 00 08 00 | header (lType 8 at +2) |
| +0x0c | 3 | subtype (3 weighted) |
| +0x0d | 0 | 0 on all 357 weighted objects |
| +0x0e | 1 / 2 / 0x7c | level-of-detail mask |
| +0x0f | 2 | **variant** (section 5) |
| +0x10 | 0 (u16) | 0 everywhere |
| +0x12 | 11 (u16) | material = .MAT instance slot |
| +0x14 | 0x102 | 258 on 3,406 of 4,290 objects (others 114, 0, 370, 102); not decoded, copy |
| +0x18 | 0xffe08f57 | one of five values (ff737373, ffe08f57 (all 353 weighted), ff588fe1 ..): not decoded, copy |
| +0x1c | 0x00000880 | draw mode (282 of 357 weighted; 0x000c0880 = eye shells / glasses; 0x800000 = skipped by the renderer at 0x67cf77) |
| +0x20, +0x24 | 0 | |
| +0x28 | 449 | **subtab** chunk: u32 descriptor index, 0-terminated (one entry in every stock object) |
| +0x2c .. +0x34 | 0 | |
| +0x38 | 4 | bone run count |
| +0x3c | 450 | bone runs chunk: count x {u32 12 * n, u32 12 * first bone}; mask: (48,48) (12,108) (12,204) (12,1128) = bones 4, 5, 6, 7, 9, 17, 94 |

Descriptor (48 bytes = 12 dwords; chunk 448): [0] vertex count 1018, [1] vertex chunk 447 (52,944 = 1018 x 52
bytes), [2..4] 0, [5] 1199, [6] index chunk 446, [7..11] 0. Dword 5 is NOT the vertex or index count (ratio to
vertices 0.25 .. 1.59, median 1.24; equal in 4 of 353); it is 0 on 256 stock objects (239 static, 13 subtype 1,
4 weighted), so **0 is a value the game accepts** (kl_prm also writes 0). ASSUMPTION: a buffer-size hint.

Index chunk: u16 segment count (1 in all 4,290 stock chunks), then per segment u16 count and count x u16
indices; **triangle list**; 4,872 indices = 1,624 triangles for the mask; chunk padded to 16. Winding
(winding.py, 0 of 12,517 triangles the other way): the outward normal is **(c - a) x (b - a)** for the stored
order (a, b, c) - the stored order is clockwise seen from outside under the right-hand rule. A converter must
emit Payday 2's triangles reversed if their normal is (b - a) x (c - a).

**Bounds.** No float of the mask's box (min (-10.38, 147.96, -18.89), max (10.22, 183.61, 8.91)) is in the mesh
object, the descriptor or the subtab. The model ROOT (64 bytes) holds at +0x20 .. +0x37 six floats = the union
box of all its objects (J.C.: (-62.74, -0.05, -18.90) .. (62.79, 183.68, 41.66); the mask's max.y 183.61 and
min.z -18.90 are its extremes). The root's .oct record is an EMPTY tree (nodes 1, items 0). So a mask inside the
body's box needs no bounds change; a mask sticking out past the box (e.g. above y 183.7 or in front of z -18.9)
must widen the root's six floats (kl_chars.put copies roots; whether the game culls by that box was not read -
ASSUMPTION that it is the culling box, from its contents).

## 3. The head frames of the 16 skeletons - established (heads16.log/.json)

All 16 (8 Dog Days + 8 Dead Men on the wardrobe build): HEAD = bone 7 'HEAD', parent NECK (bone 5) via neck1
(6); under HEAD: 'head attacher', fa_jaw, fa_chin, the fa_* face bones (22 .. 28 of them). The HEAD rest 3x3 is
BYTE-IDENTICAL on the 8 Dog Days heisters and the same numbers on the 8 Dead Men:

    rows  (-0.000 -0.025 -1.000)  (1.000 -0.000 -0.000)  (0.000 1.000 -0.025)
    position (0, 162.69, -1.91)   (Tommy, Pierre, Liam, Red: y 162.86 .. 162.88)

Convention: COLUMN (16 of 16 votes; skeleton [2] x [18] = identity, the translation residual decides):
model = R . h + t, so **h = R^T . (P - t)**. The columns are HEAD's axes in model space:
HEAD X = model +y (up), HEAD Y = model +z (BACK; the face is -Y, tilted 1.4 degrees), HEAD Z = model -x
(the character's RIGHT). Model -z (face front) in HEAD space = (0, -0.9997, 0.0249).

| character | height | NECK rest y | stock mask / head parts | box in HEAD space (X up, Y back, Z right) |
|---|---|---|---|---|
| J.C. | 183.5 | 153.16 | Merc_Masks 1018 v | (-14.73, -16.97, -10.23) .. (20.92, 10.81, 10.36) |
| Tommy | 180.7 | 153.34 | 1007 v | (-14.83, -16.86, -10.23) .. (20.92, 10.81, 10.36) |
| Pierre | 182.3 | 153.33 | 896 v | (-8.71, -16.86, -10.23) .. (20.92, 10.81, 10.36) |
| Liam | 182.1 | 153.33 | 1045 v | (-14.73, -18.12, -10.23) .. (20.92, 10.78, 10.36) |
| Jean | 182.4 | 153.16 | 1019 v | (-14.74, -16.59, -10.29) .. (20.92, 10.81, 10.50) |
| Elwood | 181.3 | 153.16 | 1052 v | (-14.42, -16.97, -10.23) .. (20.92, 10.81, 10.36) |
| Bud | 180.9 | 153.16 | 984 v | (-16.41, -15.45, -9.32) .. (18.96, 9.78, 9.45) |
| Mitchel | 180.9 | 153.16 | 986 v | (-14.75, -16.86, -10.23) .. (20.92, 10.81, 10.36) |
| Kane (dm) | 182.5 | 153.16 | Hero_HEAD_Multiplayer, Hero_Hair_Final, Eyelashes, eye_Outer_Alpha, headset: 2774 v | (-21.21, -14.76, -8.89) .. (19.65, 8.86, 9.44) |
| Lynch (dm) | 182.2 | 153.16 | Little_HEAD_Multiplayer, Little_Hair_01, Accessories_01_Glass, Eyelashes, eye, headset: 3151 v | (-12.49, -14.61, -14.75) .. (19.28, 14.58, 13.19) |
| Ashkanan (dm) | 180.8 | 153.16 | balaclava (multiplayer_headset01_Rank_01) + eye: 479 v | (-12.68, -14.36, -9.33) .. (17.90, 8.53, 9.30) |
| Meldal (dm) | 181.3 | 153.16 | balaclava + eye: 478 v | (-12.29, -13.86, -8.97) .. (18.41, 9.12, 8.93) |
| Red (dm) | 181.1 | 153.34 | balaclava + eye: 472 v | (-13.63, -14.57, -8.96) .. (18.41, 9.90, 8.72) |
| Parker (dm) | 180.9 | 153.16 | balaclava + eye: 443 v | (-20.74, -14.45, -8.89) .. (17.81, 9.31, 8.87) |
| Standen (dm) | 181.0 | 153.16 | balaclava + eye: 495 v | (-18.43, -14.48, -9.33) .. (18.08, 8.82, 9.30) |
| Hutchison (dm) | 180.7 | 153.16 | balaclava + eye: 510 v | (-19.30, -14.39, -8.55) .. (18.00, 8.19, 8.55) |

**THE TARGET BOX** (a Dog Days mask is a whole head with a collar; its X from -14.7 is the collar, the chin
bone is at X -4): HEAD space (-14.7, -17.0, -10.2) .. (20.9, 10.8, 10.4); width 20.6, height 35.6, depth 27.8.
Face anchors in HEAD space (rest positions of the face bones, 8 Dog Days heisters; the Dead Men heads lie
within 3 units of these, kl_chars._Fit): 

| | left eye (Z < 0 = the character's left) | right eye | nose bridge | chin | forehead01 |
|---|---|---|---|---|---|
| J.C. | (6.2, -10.5, -3.5) | (6.4, -10.4, 3.4) | (8.3, -12.4, -0.1) | (-4.4, -12.3, 0.0) | (8.1, 0.9, 0.0) |
| Tommy | (6.9, -7.9, -3.4) | (6.9, -7.8, 3.5) | (8.3, -10.4, -0.1) | (-3.4, -9.3, 0.3) | (8.3, 3.4, 0.0) |
| Pierre | (6.5, -9.9, -3.4) | (6.5, -9.9, 2.9) | (8.3, -12.4, 0.0) | (-3.9, -12.5, 0.1) | (8.1, 1.8, 0.0) |
| Liam | (7.1, -10.6, -3.3) | (7.1, -10.4, 3.1) | (8.3, -13.0, 0.0) | (-3.7, -12.7, 0.0) | (8.1, 0.6, 0.0) |
| Jean | (6.6, -9.8, -3.4) | (6.5, -9.8, 3.3) | (8.3, -11.2, 0.0) | (-4.0, -12.4, -0.5) | (8.1, 2.0, 0.0) |
| Elwood | (6.9, -7.7, -3.2) | (6.9, -7.6, 3.1) | (8.4, -10.1, -0.1) | (-3.2, -9.5, -0.2) | (8.1, 3.8, 0.0) |
| Bud | (6.6, -9.3, -2.9) | (6.7, -9.2, 2.7) | (8.5, -11.4, 0.0) | (-2.6, -11.6, 0.1) | (8.1, 2.5, 0.0) |
| Mitchel | (6.5, -9.4, -3.2) | (6.3, -9.0, 3.2) | (8.2, -12.5, 0.0) | (-4.0, -11.3, 0.1) | (8.1, 1.2, 0.0) |

So: eye line X ~ +6.5, eyes 6.5 .. 7 apart, the face surface at Y ~ -10 .. -13 (nose tip = mask front -17),
the chin at X ~ -4. Fit rule for a Payday 2 mask: scale it so its eye holes are 6.5 .. 7 units apart, put the
eye-hole centres at HEAD (6.5, -11.5, +-3.3), and check that nothing lies behind Y > -2 (ears) unless the mask
wraps the head. The low-detail prefix: HEAD (bone 7) is inside the 34 / 36 leading bones of every skeleton, so a
HEAD-only mask may be drawn at LOD 0x7c as well (kl_chars.check_wardrobe demands LODs 1, 2 and 0x7c per variant).

## 4. What a face-plate mask must leave in place - established (f01_geometry.log 'HEAD PARTS')

A Dog Days mask REPLACES the head: variant 1 (face look) has the head inside the Merc_0n body objects (main
object y up to 183, a second Merc_0n object 1,300 .. 1,900 vertices with head-weight 0.4 .. 0.7 = head + one
arm), variant 2 has the body cut at y 158 .. 164 and the small object reduced to a hand (y 90 .. 110), plus the
Merc_Masks head. A Payday 2 mask is a FACE PLATE, so its variant must be built from the **variant-1 objects**
(head included) plus the plate, not from the masked body:

| keep under a plate | drop under a plate |
|---|---|
| both Merc_0n objects of variant 1 (the face), MoneyBag_01* (shared by variants 1 and 2 already), eye_Outer_Alpha (eye shells at HEAD Y ~ -11; visible through the eye holes), Tommy's A_Glasses_Wideframe (on the hip, x 52, y 109: not on the face) | the face glasses: Liam SunGlasses_Glass_01 (y 167 .. 171, z -15.8 .. -14.6), Jean Merc_06_glasses (z -14.8 .. -13.3), Bud Merc_07_Glasses (z -14.1 .. -12.1), Lynch Accessories_01_Glass |
| hair objects: Elwood Merc_01_Hair_01 (y 156 .. 170, z +11.5 .. +20.2 = a tail at the back), Mitchel Merc_07_Hair_01 (y 162 .. 170, z +6.4 .. +14.5 = the back) - both behind the ears, clear of a plate | |

Hair above the brow is modelled in the Merc_0n head meshes (head tops at y 180.9 .. 183.4); a plate ending at
the forehead bone (X +8, i.e. y ~171) stays under it. Dead Men (kl_chars.DM_HEAD = 'head', 'hair', 'eyelash',
'eye_', 'headset', 'glass' are the materials the wardrobe drops under a mask): for a plate keep 'head', 'hair',
'eyelash', 'eye_', 'headset' (Kane: Hero_HEAD_Multiplayer + Hero_Hair_Final + earpiece; Lynch: Little_HEAD +
Little_Hair_01; heroes 3 .. 8: the balaclava IS the head, box Y to -14.6 at the nose) and drop 'glass'
(Lynch's Accessories_01_Glass). ASSUMPTION: Payday 2's plates (made for its own heads) clear the Kane & Lynch
faces once the eyes are aligned; nose and cheek poke-through must be looked at in kl_view (section 8).

## 5. Variant capacity - established in kl2.exe

- `[player+0x50]` is a **DWORD**: 0x88c810 `mov dword ptr [esi+0x50], eax` (then slot 0x70 of the object
  0x541960 returns, with ([player+4], 1)).
- It reaches the render node as a **BYTE**: 0x4646e0 `mov cl, byte ptr [edi+0x50]`; 0x4646e3
  `mov byte ptr [esi+0x158], cl` (function 0x464470; find_158.py).
- The renderer compares it for EQUALITY with the mesh object's +0x0f, unsigned, no range test:
  0x67cf84 `mov al, [ebx+0x158]; test al, al; je 0x67cf97 (draw); cmp byte ptr [ebp+0xf], al; jne skip`
  (function 0x67cc60, the per-mesh-object walk: `mov ebp, [eax*4 + 0xeac7b0]` = the chunk table) and the same
  pattern at 0x57ee6d .. 0x57ee7a (function 0x57ed50, shadow / second pass). No `movsx` of either byte exists
  on these paths (find_variant_cmp.txt lists all 241 byte reads at +0xf; the two above are the only compares
  against +0x158).
- So **variant 0 on the ENTITY draws every object** (whatever its +0x0f), and variants **1 .. 255** are usable;
  a mesh object with +0x0f = 0 is drawn only while the entity's variant is 0. The '< 128' limit of
  kl_chars.check_wardrobe and klchar.c's comments is unnecessary; klchar.c's own range test is `top > 255`.
- With 12 masks (8 Dog Days + 4 Payday 2): OUTFIT_STEP 14 (1 face, 2 own mask, 3 .. 14 = mask m), bodies
  0 .. 7 -> 1 .. 112, HEAD_BASE = 14 x 8 + 1 = 113, head block 113 .. 128. Fits (max 128 < 256); the
  `> 127` check in kl_chars.check_wardrobe:1128 must be raised or it refuses outfit 23 of a Dead Men body.

## 6. Material and textures - established (mat_tex.txt; dry run in mat_tex.py)

Merc_Masks in F01 = .MAT instance slot 11; in retomoto_wardrobe slot 22 (ref count 1,968). Entry: class slot 3
('Standard' class name, CLAS tree NAME 'SkinCloth': SUBC Skin / Standard | Rigid | Weighted (MPS) and Cloth ...;
the Weighted SUBC's Lighting layer = Skin fx 'DiffuseBumpSpecularTransRimLightMPS'), +0x08 flags 0x10, +0x0c
render group 32, +0x10 8, +0x14 mesh kind 3, +0x18 surface 14. Enabled BOOLs: BumpEnabled, BumpDetailEnabled,
ParallaxEnabled, BumpInterpolatedEnabled, DiffuseIsSpecularMask, StdSamplerState, StdCulling, SpecularEnabled
(v4SpecularColor 1,1,1,1; v4SpecularPower 64; vSpecularLevel 1.0), SubSurfaceEnabled 0. Texture stages:

| stage | .TEX id (F01) | record |
|---|---|---|
| mapDiffuse | 133 | DXT1 1024 x 1024, 11 mips (524288 .. 32, 8, 8, 8 bytes), flags 0, scale 1.0, name `tex:Characters/_Multiplayer/_All_Levels/Merc_Masks#Diffuse_a`, 699,205 bytes |
| mapNormal | 134 | DXT5 1024 x 1024, 11 mips (1048576 .. 16, 16, 16), **flags 0x40, scale 0.98431 (= 251/255)**, `..#Normal_a`, 1,398,268 bytes |
| mapTranslucency | 0 | none |
| mapSpecularMask | 135 | DXT1 512 x 512, 10 mips, flags 0, `..#Specular_a`, 174,914 bytes |

F01's .TEX by (fourcc, flags): DXT1/0 555, DXT5/0 196, **DXT5/0x40 193**, DXT5/2 150, DXT1/0x4000 61, RGBA/0 32,
DXT3/0 24 ... ASSUMPTION: flag 0x40 (+ the scale) marks a normal map; copy both from record 134 for a Payday 2
`_nm`.

**.TEX record** (kl_texmat docstring; both games): `u32 size (including itself) | fourcc x2 stored reversed
('1TXD' = DXT1, '5TXD' = DXT5, 'ABGR' = raw RGBA) | u32 id | u16 height | u16 width | u32 mips | u32 flags | f32
scale | u32 +0x20 (0) | name\0 | mips x (u32 bytes, data)`; records 16-byte aligned, ids 128 .. 4095 (kl2
0x5d220b), table of 4096 at the file head. A DDS payload is re-wrapped by taking its mip chain as the `mips x
(u32 n, data)` list (DXT1 block = 8 bytes, DXT5 = 16; a 4 x 4 or smaller mip is one block, as the stock tails 8 /
16 show) and writing the header above; no DDS header is kept. Precedents in the repo: `kl_chars._darker`
(rewrites a DXT1/3/5 record under a new id), `kl_portraits.tex_record` (writes an 'ABGR' record with 1 mip).

**Clone call sequence** (mat_tex.py main(), run on retomoto_wardrobe in memory; result: slot 1440
'Characters/_MultiPlayer/_All_Levels/PD2_Mask_Dallas', texture 2341, .MAT re-read with 1440 instances, .TEX
rewritten 254,515,744 bytes, `kl_tex.simulate_dd_loader` 2214 textures):

    tex = T.read_tex(lv['.TEX']); mat = T.read_mat(lv['.MAT'])
    src = <Entry whose name ends with 'Merc_Masks'>
    new_tid = next(i for i in range(128, tex.slots) if i not in tex.tex)
    tex.tex[new_tid] = T.Texture(<record bytes with id new_tid>, group=tex.tex[old].group)
    clone = T.Entry(src.cls, list(src.f), T._copy(src.root))
    for name, node in T.texture_stages(clone): if name == 'mapDiffuse': node[3] = new_tid   (same for mapNormal, mapSpecularMask)
    <NAME node>[3] = b'Characters/_MultiPlayer/_All_Levels/PD2_Mask_<x>'
    mat.insts[max(mat.insts) + 1] = clone;  mat.refs = T.material_refs(prm_bytes)   (after the .prm is written)
    lv['.MAT'] = T.write_mat(mat); lv['.TEX'] = T.write_tex(tex)

Nothing is missing from kl_texmat for this; the .fxc needs no entry (the clone keeps Merc_Masks' class and
BOOLs, so the same compiled effect serves it). If a Payday 2 mask has no specular mask, point mapSpecularMask
at 0 and set SpecularEnabled VALU 0, or reuse 135 (ASSUMPTION either works; stock materials do both).

**Limits and current counts** (retomoto_wardrobe): .TEX 2,213 textures, ids 128 .. 2340 of 4096; .MAT 1,439
instances of 2048, 12 classes of 32; .prm 65,119 chunk entries (0 free; table limit 73,728, safe 69,632 =
kl_impact.CHUNK_TABLE / CHUNK_SAFE), 77.8 MB; .TEX 253.8 MB. Four masks cost: 4 .MAT slots, 8 .. 12 textures
(about 2.1 MB each at 1024 DXT1 + DXT5), and per mask 1 vertex + 1 index + 1 descriptor + 1 subtab + 1 bone-run
chunk shared by all wearers plus one 64-byte mesh object per (character, body, LOD) = 16 characters x 1 .. 8
bodies x 3 LODs = 3 x (8 + 8 x 8) = 216 objects per mask (the wardrobe already uses 'reuse' of dead indices;
the 4 masks add about 900 chunks: inside the safe limit).

## 7. The constants that move together for 12 masks

| file:line | now | for 12 |
|---|---|---|
| tools/kl_chars.py:756 `MASKS = 8` | 8 | 12 (and the mask SOURCE list: lines 1020 .. 1053 take mask m from heister m's objects `mask[m]`; Payday 2 masks need a second source: plate objects per mask + variant-1 head objects, section 4) |
| tools/kl_chars.py:758 `OUTFIT_STEP = 10` | 10 | 14 (>= MASKS + 2) |
| tools/kl_chars.py:790 `HEAD_BASE = OUTFIT_STEP * DM_BODIES + 1` | 81 | 113 (derived) |
| tools/kl_chars.py:857-863 `variant_of` docstring '1..8' | | '1..12' |
| tools/kl_chars.py:1127-1128 `if max(want) > 127` | 127 | 255 (section 5) |
| tools/kl_chars.py:1100 `wardrobe_ini` writes Masks / OutfitStep / HeadBase | | follows |
| klhook/klchar.c:105 `#define KLC_MASKS 8` | 8 | 12 |
| klhook/klchar.c:118 `klc_upper[] = { KLC_NCHAR, KLC_MASKS + 1, KLC_OUTFITS - 1 }` | | follows |
| klhook/klchar.c:203 default OutfitStep 10; :206 `klc_w.masks == KLC_MASKS && klc_w.step >= KLC_MASKS + 2` | | an old build (Masks=8) is then refused as 'not usable'; better `klc_w.masks <= KLC_MASKS` with the row clamped |
| klhook/klchar.c:340 `klc_mask > KLC_MASKS + 1` | | follows |
| klhook/klchar.c:70-73 comment '1..96, below 128' | | update |
| klhook/mkoverlay.py:183 `MASK_LOOKS` (8 names); :184 `MASKS = ['Game option', 'No mask'] + ...` | 10 entries | 14 entries (4 Payday 2 names appended; must equal KLC_MASKS + 2, :174) |
| klhook/mkoverlay.py:196 `HEISTER_PICS` `KLPic_Mask%d for n in range(1, 9)` | 8 | 12 |
| tools/kl_portraits.py:52 `NMASK = 8`; :54 NAMES; :160 jobs; :189 `_files` | 8 | 12 (MASK_BOX :61 (146, 188) still frames the head) |
| tools/kl_view.py:245-249 `masks` command `range(1, 9)`, `cols=8` | 8 | 12 |
| KLWardrobe.ini `Masks=8 OutfitStep=10 HeadBase=81` | | regenerated by wardrobe_ini |
| re/wardrobe.md section 1 table (KLMask 0..9) | | KLMask 0..13 |

## 8. Looking at a mask on a body (kl_view)

    python tools/kl_view.py masks <build folder> <out.png>      # masks 1..N on J.C. (chars.json character 1), front and side, head box
    python tools/kl_view.py look <build folder> <out.png> <character 1..16> <variant> [...]   # any look, front and back

From Python (what both commands do; tools/kl_view.py:228-249, kl_portraits._shot):

    lv = C.Lv(build); p = G.read(lv['.prm'], 'dd'); mat = T.read_mat(lv['.MAT']); tx = V.Textures(mat, T.read_tex(lv['.TEX']))
    root = json.load(open(build + '/chars.json'))['characters'][k - 1]['root']          # k = 1 J.C. .. 9 Kane
    panels = [(axis, V.HEADBOX if axis == 'front' else (-22, 22, 148, 186), V.posed(p, mat, root, C.variant_of(0, m), V.REST, textures=tx))
              for axis in ('front', 'side') for m in masks]                              # 'side': u = z, v = y, depth x
    V.sheet(out_png, panels, 220, 190, cols=len(masks))

`posed` draws the objects whose +0x0f == variant and +0x0e == lod (1), skinned with the file's own weights and
palette, textured from mapDiffuse; it skips eye_Outer / Eyelash materials. HEADBOX = (-22, 22, 148, 186) in
model units. No normal map, no alpha: a plate's cut-outs read as holes only if the geometry has them.

## Open

- The Payday 2 unit (metre or centimetre) and the mask's own frame come from the A-side (re/pd2_attach.md); the
  fit test is the eye distance 6.5 .. 7 and the anchors of section 3.
- Whether the root's +0x20 box is used for culling (section 2) was not read in kl2.exe.
- ASSUMPTIONS listed in sections 2 (dword 5), 4 (plates clear the faces), 6 (flag 0x40, specular stage).

## Verification (2026-10-10, skeptical re-check; scripts in the verifier's scratchpad: v_vertex.py, v_head.py, v_conv.py)

Re-derived on data the document did not use: Bud's stock mask (F01 object 1251), Bud's Merc_07 body at LOD 2 (object
1179), Kane's Dead Men head Hero_HEAD_Multiplayer (wardrobe object 10241) and Lynch's Accessories_01_Glass (12071).

**Holds (section 1, 2, 5, 6, 7).**
- 52-byte vertex: stride exactly 52 on all four (chunk = 52 n rounded to 16); weights' sum 0.78 .. 1.0, none negative;
  palette bytes all multiples of 3 and max/3 < the run count (Bud body: max 186, 63 entries); +32 = ffffffff only; uv
  inside 0 .. 1; +28 under (b2, b1, b0): |v| 0.99 .. 1.02 and cos with (b-a) x (c-a) = -0.94 .. -1.00 on 99 .. 100 %
  of the vertices (so the outward normal IS (c-a) x (b-a), as section 2 says); the byte orders (b0, b1, b2) and int8
  fail (cos ~ -0.2, |v| 0.73 .. 1.42). +44 agrees with +dP/du on 99.8 .. 100 %, +48 with +dP/dv on 99.5 .. 100 %;
  N x T . B > 0 on 94 % (masks, Kane's head), 77 % (body), 50 % (glasses). Index chunk: 1 segment, triangle list.
- kl2.exe (debug/dasm.py): 0x67cf77 `test [ebp+0x1c], 0x800000 / jne skip`; 0x67cf84 `mov al, [ebx+0x158]; test al,
  al; je draw; cmp byte ptr [ebp+0xf], al; jne skip`; 0x57ee6d .. 0x57ee7a the same pattern; 0x4646e0 `mov cl, [edi+
  0x50]; mov [esi+0x158], cl`; 0x88c810 `mov dword ptr [esi+0x50], eax`. Equality of two bytes, no sign extension, no
  range test: unsigned, variant 0 draws every object, 1 .. 255 usable - as stated. The only other read of +0x158 that
  widens it is 0x44a202 `movzx` (unsigned too). The `movsx` reads of a +0xf byte in find_variant_cmp.txt (0x46be8b,
  0x80ae85, 0x8f7952, 0x9b9b14..) are in functions that never touch the chunk table 0xeac7b0.
- Section 7: every file:line checked (kl_chars 756/758/790/857-863/1100/1127-1128; klchar.c 73/105/118/203/206/
  219-220/340; mkoverlay 183/184/195-196; kl_portraits 52/54/61/160/188-189; kl_view 245-250; KLWardrobe.ini
  Masks=8 OutfitStep=10 HeadBase=81).
- Section 6 clone recipe, dry run re-run (mat_tex.py on retomoto_wardrobe): slot 1440 PD2_Mask_Dallas, texture 2341,
  .TEX 254,515,744 bytes, loader simulation 2214 - identical to the document. Note: Merc_Masks is class slot 3 in F01
  but class slot 2 in the wardrobe build (the recipe copies `src.cls`, so it does not matter). The dry run clones only
  mapDiffuse and does not refresh `mat.refs`; the normal / specular stages and the refs step are untested.
- HEAD = bone 7, parent neck1 (6), the HEAD [2] record byte-identical on the 8 F01 heisters, position (0, 162.69, -1.91).

**Does not hold: the convention claim of section 3.** `heads16.py` casts `conv_votes['col'] += 1` unconditionally -
"16 of 16 votes" is not a measurement - and `[2] x [18]` is NOT the identity (its own log: dev 1.0; R2 * R18^T dev
0.025). `skel_conv.py` compares HEAD with NECK (bone 5), not with its parent neck1 (bone 6), and even so neither reading
yields (4.862, 0, 0) (its output: row (0.14, 0, 9.72), column (9.53, -1.88, 0.35)). Measured on EVERY bone of J.C.
(F01, 102 bones with a parent) and Kane (wardrobe, 101):
- det of every stored 3x3 in [2] is -1.000: the stored matrix is improper, so neither the column nor the row reading
  of it is a rotation frame. The document's "HEAD space" (X up, Y back, Z right) is LEFT-handed.
- Let P swap x and z. With S' = P S (the stored rows taken in the order 2, 1, 0) in the ROW convention
  (v_model = v_bone . S' + t): the local translation of [6] = (t - t_parent) . S'_p^T exactly on 102/102 and 101/101
  bones (the document's column reading: 3/102); the local quaternion of [6] = S' S'_p^T under the DirectX
  (transposed) formula on 102/102 and 101/101 (column reading: 20/102); [18] = (P S^T P | -P S t) on 102/102 and
  101/101, i.e. the inverse (S'^T | -t S'^T) stored in the same row order (the pure readings: 0/102).
- Hence the engine's HEAD frame is: **X = stored row 2 = model +y (up), Y = stored row 1 = model +x (the character's
  LEFT), Z = stored row 0 = model -z (the FACE / front)**, right-handed, HEAD's own local offset (4.862, 0, 0) along X.
  Relative to the document's frame: (X, Y, Z)_engine = (X, -Z, -Y)_document. "HEAD X = up" survives; "Y = back,
  Z = right" do not.
- Consequence: the boxes and anchors of section 3 are correct numbers in the document's own (left-handed) frame and
  stay usable if the fit is done entirely in that frame or, better, in model space (the vertex positions ARE model
  space). They must not be used as the bone's frame: any A-side mapping of Payday 2's head frame onto "X up, Y back,
  Z right" by axis names is wrong in two axes and flips handedness (a mirrored mask).

Not re-checked here: the root +0x20 box, descriptor dword 5, the .oct record, the LOD prefix (section 2 / 3 end),
sections 4 and 8.
