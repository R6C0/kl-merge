# Payday 2: how a mask sits on a head, and what the crew masks look like (A3, 2026-10-10)

Research only. Sources: the installed game (Steam build 25506656, crate store read with `tools/pd2_crate.py`;
extracted copies under `<work>\pd2\extract\`), the installed LuaJIT bytecode (strings only: the files are
`1b 4c 4a 02` bytecode, not source), and the public decompiled Lua of mwSora/payday-2-luajit (downloaded with
curl into `<work>\pd2\public\lua\`, read, never executed). Cross-check of public source against the installed
bytecode: playerinventory 274/281, maskext 33/35, criminalsmanager 262/266, menuscenemanager 828/864 of the
public files' identifiers and string literals are present in the installed bytecode (the misses are
multi-line table fragments the regex cut badly, plus `stack_dump` and the renamed `mask_colors` -> `colors`),
so the public logic below is the installed logic. `tools/pd2_model.py` (the earlier, untracked decoder) was
read and used as is; it parsed every file touched here (its `info`, `head`, `png`, `tex` commands).
Model and texture facts below are measured on the extracted files. ASSUMPTION is written where it applies.

## 1. The attach rule

### (a) Which object, which call

`lib/units/beings/player/playerinventory.lua`, `PlayerInventory:set_mask_visibility(state)` (in-game, third
person, every criminal that is not the local player; husks inherit it, `huskplayerinventory.lua` has no
mask code of its own):

```lua
local mask_align = self._unit:get_object(Idstring("Head"))
local mask_unit  = World:spawn_unit(Idstring(mask_unit_name), mask_align:position(), mask_align:rotation())
mask_unit:base():apply_blueprint(managers.criminals:character_data_by_name(character_name).mask_blueprint)
self._unit:link(mask_align:name(), mask_unit)
...
self:update_mask_offset(mask_data)
```

- The parent object is the character's `Head` Object3D (`Idstring("Head")`; the installed bytecode holds the
  strings `Head`, `mask_obj`, `mask_align`, `update_mask_offset`, `set_mask_offset`, `set_position`,
  `set_rotation`, `orientation_object`, `units/payday2/masks/msk_backside/msk_backside` in this file).
- The call is the two-argument `unit:link(parent_object_name, child_unit)`: the child's whole unit is parented
  to `Head` and keeps the world pose it was spawned with (Head's position and rotation), i.e. IDENTITY
  relative to Head. (Weapons use the three-argument form `link(align, unit, unit:orientation_object():name())`;
  masks do not.)
- The menu (`menuscenemanager.lua` 2096-2103) does the same: `get_object(Idstring("Head"))`,
  `unit:link(mask_align:name(), mask_unit)`, then `update_mask_offset`.
- `mask_unit_name` comes from `tweak_data.blackmarket.masks[id].unit`
  (`BlackMarketManager:mask_unit_name_by_mask_id`); for Wolf `units/payday2/masks/msk_wolf/msk_wolf`.

### (b) Offsets after linking

`update_mask_offset` -> `set_mask_offset(mask_unit, mask_align, position, rotation)`:

```lua
mask_unit:set_rotation(mask_align:rotation() * rotation)
mask_unit:set_position(mask_align:position() + R:x()*position.x + R:z()*position.z + R:y()*position.y)
```

The offset is `tweak_data.blackmarket.masks[mask_id].offsets[character]` = `{Vector3, Rotation}`, per MASK
per CHARACTER (character after `convert_old_to_new_character_workname`: russian->dallas, german->wolf,
spanish->chains, american->hoxton). Without an entry it is `Vector3(0,0,0), Rotation(0,0,0)`. Menu and game
use the same table and the same formula, so menu and game agree.

For the four crew masks: `wolf`, `chains`, `hoxton` have NO offsets at all. `dallas` has
`jacket = {Vector3(0, 0, 0.554498), Rotation(0,0,0)}` and `joy = {same}` (0.55 cm along Head's local z);
none for the crew bodies. So on Dallas / Wolf / Chains / Hoxton the crew masks sit at Head with identity.
Masks with offsets at all: 79 of the ~1000 entries (oni on jacket: `Vector3(0, 0.67, 0.32)`; the big ones
are hats and tiaras, up to a few cm and ~20 degrees). The crew masks have no `scale` anywhere; no mask entry
has one (`grep scale` finds nothing in maskstweakdata.lua).

### (c) The mask unit's own transform and what third person draws

`msk_wolf.object`: `<diesel orientation_object="rp_wolf_mask" .../>`, graphics = one object `g_wolf`.
`msk_wolf.model` (33,631 bytes, 12 sections): Object3D `rp_wolf_mask` at (0,0,0), rotation identity, no
parent; Model `g_wolf` child of it, local position (0, 8.02, 9.89), rotation identity, 853 vertices, 926
triangles, one atom, material `mtr_mask_wolf`, rigid (no SkinBones). Same shape for the other three:

| mask | model object | local pos (x y z) | verts / tris | root-space box (cm) |
|---|---|---|---|---|
| msk_wolf | g_wolf | 0, 8.02, 9.89 | 853 / 926 | -9.8..9.8, -6.0..22.1, 1.2..18.6 |
| msk_dallas | g_dallas | 0, 7.60, 9.95 | 976 / 1176 | -9.7..9.7, -6.9..22.1, 1.2..18.7 |
| msk_chains | g_chains | 0, 7.97, 9.96 | 1193 / 1554 | -9.8..9.8, -6.0..22.0, 1.2..18.7 |
| msk_hoxton | g_hoxton | 0, 7.19, 10.47 | 1089 / 1300 | -9.6..9.6, -7.8..22.2, 1.2..19.8 |

The mask's root space IS the Head's local frame (Head local x = world -x, y = up, z = forward; the body's
Head sits at world (0, 5.33, 166.76), `pd2_model.py head`). Head-space box of the criminal body's
`g_head_wolf`: x -9.6..9.6, y -5.1..20.7, z -8.7..15.1. So the mask covers the head's full height
(-6..22 vs -5..21), the full width, and the FRONT HALF ONLY: z from 1.2 (just in front of the ears' plane,
Head origin is between the ears) to 18.6 (3.5 cm in front of the nose tip at 15.1). The straps / back of
the head are a second unit:

- `units/payday2/masks/msk_backside/msk_backside` (object `rp_backside`, mesh `g_back`, 1949 vertices,
  box x -10.3..10.0, y 0.4..21.7, z -11.5..14.2 = the rear shell of the head), spawned at Head and linked
  to the mask's orientation object with the three-argument `link` when the mask's tweak entry has no `type`
  (`type` exists only on 151 helmets, 23 glasses, 10 tiaras, 2 beards, 1 hat; none of the crew masks). Its
  material is `generic:DIFFUSE_TEXTURE:NORMALMAP` with `fps_temp_dallas/temp_mask_inside_df/_nm`
  (extracted). Third person therefore draws mask front + backside shell.
- `msk_fps_back_straps` and `fps_temp_dallas` are first-person-only: `type="wpn"` units with an animated
  `mask_on` group (the strap pieces are the animated objects) used by `menuscenemanager.lua` 3456 (the
  mask-on preview) and the FPS arms; `fps_temp_dallas` is a complete first-person mask (`g_straps`,
  `g_mask_dallas`, `g_inside`). Not drawn in third person.

### (d) Sizing

Modelled at the Head frame with identity: no scale anywhere in the Lua, no scale in the Object3D (all
rotation blocks are identity), the mask root at (0,0,0). One mask model fits every character because every
PD2 criminal shares the skeleton (`_char_joint_names` in the body `.unit`; the fourteen g_head_* meshes of
`npc_criminals_suit_1.model` all have Head-space boxes within x +-10, y -9..21, z -12..15.5); the few
characters with a different head (jacket, joy) get the per-character `offsets`, not a scale.

For the Kane & Lynch side (re/pd2_klside.md): the stock whole-head mask box in HEAD space is
(-14.7,-17.0,-10.2)..(20.9,10.8,10.4) with HEAD X = up, Y = back, Z = right, eyes at about (6.5,-11.5,+-3.3).
The PD2 mask in its own frame is x right (-9.8..9.8), y up (-6..22), z forward (1.2..18.6), so the axis map
PD2 -> KL HEAD is (x,y,z)_pd2 -> (X=y, Y=-z, Z=x) plus a translation to put the PD2 eye holes (ASSUMPTION
from the render: about y 12..13, z 15..17 in mask space) on KL's eye centres; the sizes are comparable
(PD2 head height 26 cm front shell vs KL mask box 35.6 cm along X including neck). Any scale will be a
KL-side decision; PD2 applies none.

### (e) Clean and glow variants

- `msk_dallas_clean` (and wolf_clean, chains_clean, hoxton_clean; all four folders exist in the hashlist and
  dallas_clean is extracted): same object name `rp_dallas_mask` / `g_dallas`, same unit type and extensions,
  same material name `mtr_dallas_mask` and render template; the ONLY difference is the texture pair
  `dallas_clean_df` / `dallas_clean_nm` (the undamaged paint). Tweak: `infamous = true, value = 9`, no
  offsets. Same linking.
- `msk_dallas_glow` (`units/pd2_dlc_cop/masks/`, Complete Overkill Pack): unit `type="msk"`, object
  `rp_dallas_glow_mask` with THREE graphics objects (`g_dallas`, `g_glow1`, `g_glow2`) and two particle
  spawners (`e_e_1`, `e_e_2` -> `effects/.../dallas_eyes`); material config adds `sweep1`
  (`effect:BLEND_ADD:DIFFUSE0_TEXTURE:DIFFUSE0_THRESHOLD_SWEEP`, texture `msk_dallas_glow_il`, orange sweep
  colours) and `glow2` (`effect:BLEND_ADD:DIFFUSE0_TEXTURE`, `msk_dallas_glow_constant_il`). The base
  material is the normal `solid_mask:MATS_3` with its own `_df/_nm`. `maskext.lua` strings mention
  `mat_glow_anim_`, `mat_glow_static_`, `mtr_bloom_glow`: glow materials are found by name and tinted.
  Not needed for a plain look.

## 2. The look of the crew masks: is `_df` final?

Yes for the default blueprint. Evidence:

- Every crew mask's `.material_config` is two documents joined by ` ELSE {` (platform / shader-level
  branch): branch 1 `render_template="solid_mask:MATS_3"`, branch 2 `render_template="solid_mask"`. Both
  name the same slots: `diffuse_texture` = `<mask>_df`, `bump_normal_texture` = `<mask>_nm`,
  `reflection_texture` = `units/payday2/matcaps/matcap_plastic_df`, `material_texture` =
  `units/payday2/masks/shared_textures/patterns/pattern_no_color_no_material_df`, `material_amount = 1`;
  MATS_3 adds `material_amounts = 2 2 2` and `diffuse_layer0..2_texture` = the plastic matcap again;
  the plain branch adds `tint_color_a = 0 0 0`, `tint_color_b = 0 0 0`. Material names: `mtr_mask_wolf`,
  `mtr_dallas_mask`, `mtr_chains_mask`, `mtr_hoxton_mask`.
- `MaskExt:apply_blueprint` only touches: `tint_color_a`, `tint_color_b` (from `colors[id].colors`),
  `material_amount` (from `materials[id].material_amount`, default 1), the `material_texture` slot
  (= `textures[pattern_id].texture`) and the `reflection_texture` slot (= `materials[material_id].texture`).
  It never changes the diffuse. The default blueprint (`get_default_mask_blueprint`) is
  colour_a = colour_b = `nothing`, pattern = `no_color_no_material`, material = `plastic` = EXACTLY the
  textures already baked into the material_config above. So the crew mask as shipped (and as drawn on the
  AI crew, `ai_mask_id`) renders with the material_config's own values.
- The pattern texture decides what the blueprint does: `pattern_no_color_no_material_df` is an 8x8 DXT1
  with every texel (0,0,0); `pattern_no_color_full_material_df` is all (0,0,255). ASSUMPTION (from the names
  and these two values): channel R selects tint_color_a, G tint_color_b, B the matcap "material" layer; all
  zero = plain diffuse + normal map, no tint, no matcap. `matcap_plastic_df` is a 64x64 DXT5 grey
  sphere-map (54 distinct greys, centre (213,214,213)) that would only show where the pattern's blue is set.
- Render check (`pd2_model.py png`, software renderer, `<work>\pd2\look\msk_wolf_df.png` etc.):
  `wolf_df` on `g_wolf` gives the known Wolf: white face, red crown and mouth, black eye pits. The `_df`
  textures are 512x512 DXT5 with 10 mips; `_nm` are DXT5 with the A2D5 swizzle (x in alpha, y in green).
  So for the KL wardrobe the painted look is `<mask>_df` (+ `_nm` if a normal map is wanted) and nothing
  has to be baked. Extra textures a baked default blueprint would need: none beyond what is already
  extracted (`matcap_plastic_df.texture`, `pattern_no_color_no_material_df.texture` are both under
  `<work>\pd2\extract\units\payday2\...`).

## 3. Does the mask hide the head or hair?

No, for the crew heads. Facts:

- The body `npc_criminals_suit_1.object` draws one `g_head_<name>` per character (all in one model; the
  `var_mtr_<name>` sequences switch them). `var_head_replace` (the only thing that hides a head mesh) is set
  by `set_character_visual_state` from `player_style ... body_replacement.head`, i.e. OUTFITS that bring their
  own head, never by a mask.
- The mask is a separate unit over the face; the head and its hair stay enabled underneath (the crew masks
  reach y 22 in Head space, above the scalp at 20.7, and the `msk_backside` shell closes the back, so the
  hair is covered, not removed).
- Sequence hooks exist only for characters whose hair must change under a mask: `mask_on_sequence` /
  `mask_off_sequence` in `blackmarkettweakdata.lua _init_characters` for sokol (`mask_on_sokol`: enables
  `g_sokol_mask_on`, disables `g_sokol_mask_off` and `g_sokol_hair`), jimmy (`g_jimmy_mask_on/off`),
  female_1, bonnie, joy, ecp_*, max (`face_mask_on`); dallas / wolf / chains / hoxton have none.
  `masks[id].skip_mask_on_sequence` (hats, glasses) runs the mask_OFF sequence instead, keeping the hair.
- Material-level: the body's `mtr_hair` material (`effect:...:VIEW_ANGLE_FALLOFF_OP`) is not touched by the
  mask code.

## 4. Further iconic candidates (folder present in the hashlist and in `maskstweakdata.lua`)

| folder (`units/payday2/masks/...`) | tweak id | why |
|---|---|---|
| msk_skull/msk_skull | skull | pre-order "Skull", the Infamy icon |
| msk_skulloverkillplus/... (also skullhard, skullveryhard, skulloverkill) | skulloverkillplus | Death Wish / difficulty skulls |
| msk_clown_56/msk_clown_56 | clown_56 | the base-game clown face |
| msk_anonymous/msk_anonymous | anonymous | Guy Fawkes |
| msk_hockey_a/msk_hockey_a_mask | hockey | hockey goalie (note the `_mask` file name) |
| msk_dillinger_death_mask/... | dillinger_death_mask | Infamous death mask |
| msk_alienware/msk_alienware | alienware | the Alienware alien |
| msk_oni/msk_oni, msk_samurai, msk_shogun | oni / samurai / shogun | Japanese set (oni has a jacket offset) |
| msk_bear/msk_bear | bear | "Bear" (pd2_clan) |
| msk_rubber_male/msk_rubber_male | rubber_male | the Nixon-style rubber face |
| msk_zipper/msk_zipper, msk_jaw, msk_mummy, msk_frank, msk_pumpkin_king, msk_cthulhu | as named | Halloween / horror set, all plain `solid_mask` units with a single `g_*` object |
| msk_dallas_clean, msk_wolf_clean, msk_chains_clean, msk_hoxton_clean | *_clean | the Infamous clean crew masks (same geometry, new textures) |

Characters' own masks with a different unit folder: `units/pd2_dlc_cop/masks/msk_{wolf,chains,hoxton}_glow`
(glow set), `units/pd2_dlc_clover/masks/msk_clover_begins`, `pd2_dlc_miami/masks/msk_tiger`,
`pd2_dlc_dec5/masks/msk_eagle`, `pd2_dlc_in32/masks/msk_goldenbrute`. Only folders, not checked further.

## What this means for `tools/kl_pd2mask.py`

- Take `<mask>.model`: the single rigid Model under the `rp_*` root, world = root space (identity root),
  vertices in cm, the mask's frame = PD2 Head local (x right, y up, z forward).
- Take `<mask>_df` as the colour (DXT5 512x512; the KL side needs its own DXT path) and optionally `_nm`.
- Add `msk_backside` (`g_back`, 1949 vertices) if the back of the head must be closed; the KL stock masks
  are whole heads, so the PD2 front + backside together make the equivalent.
- No scale, no offset for the crew masks; place by the Head frame mapping in section 1(d) and check the
  eye holes against KL's eye centres with `kl_view`.

Files: public Lua in `<work>\pd2\public\lua\` (12 files, mwSora/payday-2-luajit, master); renders in
`<work>\pd2\look\msk_{wolf,dallas,chains,hoxton}_df.png`; nothing added under the repo but this note.

## Verification (2026-10-10, skeptical re-run by a second agent; nothing above was edited)

Re-run against the installed bytecode (`<work>\pd2\extract\lib\...`, all `1b 4c 4a 02`), the saved public Lua, the
extracted XML / .model / .texture files, the shipped `hashlist` and `tools/pd2_model.py`. Verdict: HOLDS WITH
CORRECTIONS.

Confirmed:
- Installed `playerinventory.lua` bytecode holds `Head` (1), `mask_obj`, `mask_align` (4), `update_mask_offset` (2),
  `set_mask_offset` (2), `orientation_object` (3), `spawn_unit` (3), `apply_blueprint`, `mask_blueprint` and the
  `msk_backside` path; `huskplayerinventory.lua` holds no mask string at all. Installed `menuscenemanager.lua`:
  `Head`, `mask_align` (4), `update_mask_offset` (5), `_spawn_mask` (3), both backside / back_straps paths.
- Public lines exist as cited: `menuscenemanager.lua` 2096-2103 (get_object Head, link, update_mask_offset), 2416-2425
  (`_spawn_mask`, backside when no `type`), 3456 (back straps); `playerinventory.lua` 670-747 / 749-767 / 770-781.
  The two-argument `link`, the offset formula and `get_real_character` -> `convert_old_to_new_character_workname`
  (russian/german/spanish/american) are as described. `mask_unit_name` reaches the function as
  `character_data.mask_obj`, filled by `mask_unit_name_by_mask_id` (criminalsmanager 246, 250, 665, 670, 709) =
  `tweak_data.blackmarket.masks[real id].unit`.
- Tweak: wolf / chains / hoxton entries have no `offsets`; dallas has jacket and joy `Vector3(0, 0, 0.554498)`,
  `Rotation(0,0,0)`; oni jacket `Vector3(0, 0.673745, 0.316006)`; `scale` appears nowhere in maskstweakdata.lua;
  `type` counts 151 helmet / 23 glasses / 10 tiara / 2 beard / 1 hat; hockey's unit is `msk_hockey_a_mask`.
- Models (`pd2_model.py info`): the four tables rows (positions, verts / tris, root-space boxes) and msk_backside
  (rp_backside / g_back 1949 verts, box -10.31..9.95, 0.40..21.68, -11.49..14.17) match to the rounding shown.
  `head`: Head world matrix rows (-1 0 0)/(0 0 1)/(0 1 0), position (0, 5.33, 166.76); g_head_wolf Head-space box
  -9.61..9.61, -5.05..20.73, -8.65..15.13.
- Material configs of wolf / dallas / chains / hoxton / dallas_clean: two documents joined by ` ELSE {`,
  `solid_mask:MATS_3` and `solid_mask`, the slots and names exactly as in section 2; backside =
  `generic:DIFFUSE_TEXTURE:NORMALMAP` with `fps_temp_dallas/temp_mask_inside_df/_nm`; dallas_glow adds `sweep1`
  / `glow2` with the two BLEND_ADD templates, three graphics objects and two `dallas_eyes` spawners, unit type `msk`.
- Textures: `wolf_df` / `dallas_df` 512x512 DXT5, 10 mips; `wolf_nm` DXT5 with pixel-format rgbbits 0x35443241
  = 'A2D5'; `pattern_no_color_no_material_df` 8x8 DXT1, 4 mips, every block c0 = c1 = (0,0,0); `..._full_material_df`
  all (0,0,255); `matcap_plastic_df` 64x64 DXT5, 7 mips. `look/msk_wolf_df.png` shows the Wolf (white face, red crown
  and mouth, black eye pits).
- Default blueprint ids in the public tweak data: `textures.no_color_no_material.texture` =
  `.../patterns/pattern_no_color_no_material_df`, `materials.plastic.texture` = `.../matcaps/matcap_plastic_df`,
  `colors.nothing` = Color(0,0,0,0)/255 = the material_config's own values. Installed maskext has NO
  `diffuse_texture` string, so the diffuse is indeed never replaced.
- Body: `var_head_replace` is only a filter variable (`filter_not_head_replaced`); `mask_on_sokol` disables
  `g_sokol_hair` and `g_sokol_mask_off`, enables `g_sokol_mask_on`. All 34 candidate paths and the three shared
  textures are in the hashlist; the 21 candidate tweak ids exist.

Corrections:
1. Eye holes (section 1(d)'s ASSUMPTION "about y 12..13, z 15..17" from the render) are WRONG. Measured on the mesh
   (`pd2_model.py holes msk_wolf.model`): two 11-vertex boundary loops centred at (+-3.58, 7.96, 12.25) in mask /
   Head space, 7.17 cm apart (K&L eyes 6.6 apart). The `head` command's proposal: scale 1.0, translation
   (-1.46, 0.75, 0) in K&L HEAD space puts them on K&L's eye line.
2. Axis sign. PD2 Head local x = world -x, and the body's LeftShoulder sits at local +x of Spine2 (= world -x), so
   world +x is the character's RIGHT and the mask's +x is the character's LEFT, not right. The map to K&L HEAD
   (Z = right) is therefore (X = y, Y = -z, Z = -x); the note's "Z = x" mirrors the mask. The crew masks' geometry is
   symmetric, so only asymmetric paint / uv would show it. (`pd2_model.py head` already prints Z = -x.)
3. `dallas_clean` tweak: `value = 10, qlvl = 0` (wolf_clean / chains_clean / hoxton_clean are `value = 9`).
4. Counts: 78 entries carry an `offsets` key in the public maskstweakdata (one of them empty, line 1958), of 565
   `self.masks.<id> = {` entries, not "79 of ~1000".
5. Mask-on sequences: sydney / ai_sydney also have `mask_on_sequence = "mask_on"`; max's key is
   `face_mask_on_sequence` (found only in the installed bytecode next to `var_mtr_max`; the public file predates it).
6. The INSTALLED `maskext.lua` is newer than the public source: its strings add `color_c` / `_tint_color_c`,
   `_materials_mat3`, `diffuse_layer0..2_texture`, `material_amounts`, `MATCAP_MODE_TILE/MATCAP/STRIP`,
   `strip_paint`, `does_not_apply_color`, `swap_to_fps`, "Using outdated material modes please update this mask".
   The public-vs-installed check (33/35) only tested one direction. The list in section 2 ("only touches tint a/b,
   material_amount, material_texture, reflection_texture") is the public version; the installed one also drives a
   third tint and the three diffuse layers. The conclusion stands because no diffuse_texture is ever replaced and
   the defaults equal the config, but any future tint baking must follow the installed variant.
7. `fps_temp_dallas` is the folder; its unit / object / model files are `temp_mask_dallas.*` (type `wpn`, objects
   g_straps / g_mask_dallas / g_inside and the `mask_on` group confirmed).
8. `tools/pd2_model.py` is 48,479 bytes, modified 06:40, two minutes AFTER this note (06:38); the note's "38,984
   bytes, used unchanged" describes an earlier state. Another session is editing it; do not rely on "unchanged".

Not re-run: the full public-vs-installed identifier cross-check (274/281 etc.); the hidden-head claim was checked
on the body's sequence XML and criminalsmanager 431-442 only, not in a running game (none is to be run).
