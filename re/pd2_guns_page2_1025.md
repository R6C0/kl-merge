# Payday 2 gun model + sound for Dog Days shop page II: how far, and a minimal test plan

2026-10-25 (research only; nothing built, nothing installed, no game launched; game folders read-only). Sources: re/pd2_guns.md
(model survey 2026-10-10), re/pd2_klside.md + tools/kl_pd2mask.py (the mask path, which DID draw in the game: log 2026-10-10
"WOLF plate on his face, drawn and textured"), re/pd2_audio.md + tools/pd2_audio.py, tools/kl_gunsnd.py, tools/kl_guns.py,
re/shop_more_guns.md, re/shop_cap.md, klhook/klshoppage.c, tools/kl_shop_sets.py. New measurements today (scratch only) are marked NEW.
ASSUMPTION / GUESS is meant literally.

## 0. Verdict

Close on the data side, one new tool away. Every input already exists and is readable on this machine: a single-piece Payday 2 gun mesh
(`wpn_npc_ak47`, 396 triangles, rigid, 256x256 DXT5), the axis map into Dog Days' gun frame, a texture/material writer that has put a
Payday 2 mask on screen, a gun-sound replacer, and a page II whose guns are ordinary Dog Days weapon templates. What is missing:
(1) a rigid-gun-part writer (`tools/pd2_gun.py`, about 300-400 lines on top of kl_pd2mask: 40-byte vertex, subtype 2 object, gun
material), (2) a Payday 2 gun-shot picker (which clip of the bank is the shot; today only a duration heuristic), (3) the in-game
proof that a rigid part with PD2 data draws on a w_bone of a gun. Nothing hook-side is needed for the first test. One real limit: the
data-side route only reaches maps whose archive we may edit (the F01 test slot and our own expansion maps), NOT Dog Days' stock F02-F09
(CLAUDE.md: never touch stock files outside the F01 slot) - see section 7.

## 1. What a Payday 2 gun needs (what to extract)

Two kinds of third-person model (re/pd2_guns.md 0): `wpn_npc_<gun>` = ONE unit (one `g_body` + `g_body_lod1`, one diffuse + one normal
map, 250-450 triangles), and `wpn_third_*` = modular player guns (an empty frame unit + 4-8 part units; 330-1,350 triangles). The
single-piece kind is the test input. Files of `units/payday2/weapons/wpn_npc_ak47/`:

| file | needed? | use |
|---|---|---|
| `wpn_npc_ak47.model` | yes | Diesel model: `g_body` (396 tris / 575 verts), `g_body_lod1` (174), bounds y -28.2..61.5 cm; decoded by `pd2_model.py` |
| `.object` | no (read once) | node tree: root `rp_*`, `fire` (muzzle, AK at (0, 60.8, 6.5)), `a_shell` (ejection) - gives the muzzle point |
| `.material_config` | read once | names the textures `ak_df` (diffuse), `ak_nm` (normal) |
| `ak_df.texture` | yes | DDS DXT5 256x256, 9 mips; `kl_pd2mask.dds_mips/tex_record` wrap it into a Dog Days `.TEX` record |
| `ak_nm.texture` | later | uncompressed 16-bit two-channel (V8U8, ASSUMPTION), NOT DXT: needs conversion to a DXT5 normal map. Skip in test 1 |
| `.unit`, `.sequence_manager`, `.cooked_physics`, `_contour.material_config` | no | game logic / physics / outline |
| animations | no | reload/bolt animation is the `anim_*` dummy objects of the FRAME unit; Dog Days plays its own handling clips per item. Tier 1 = a static mesh, the magazine does not move |

So a gun is 1 mesh + 1 texture for the test. Extraction commands already documented: `python tools/pd2_crate.py extract-prefix
units/payday2/weapons/wpn_npc_ak47/ <work>\pd2\guns\src --xml` (already done on this machine under `<work>\pd2\guns\src\`).

Sound (NEW, measured today with `pd2_crate.Index` + the DIDX/DATA section of the bank): Payday 2 gun sounds are NOT in the 74,437
`soundbanks/streamed` .stream files (those hold only a few: weapon_bow, rpg, turret, minigun, grenade, `regular_weapon_sfx` 283).
Each gun has its own Wwise bank `soundbanks/weapon_<name>.bnk` (about 130 of them: weapon_akm, weapon_m4, weapon_amcar4, weapon_mp5_x,
weapon_deagle, weapon_g17, weapon_beretta, weapon_m1911, weapon_c45, weapon_serbu, weapon_reinbeck880 ...) with the audio EMBEDDED:
BKHD / DIDX / DATA / HIRC, version 145 (Wwise 2021.1), the same as music.bnk. `weapon_akm.bnk` = 436 KB, DIDX 45 clips, DATA 396 KB;
`weapon_deagle.bnk` 37 clips. Every embedded clip I checked is a `.wem` RIFF with tag 0x8311 = PTADPCM (weapon_akm: all 45;
weapon_deagle: all 37; mono 44.1/36/32 kHz or stereo 44.1), which `pd2_audio.Stream.decode()` already decodes. Not Vorbis, so no new
codec. Clip list of weapon_akm (id, ch, rate, length): ten mono 44.1 kHz clips of 0.31-0.39 s (ids 210564, 386009, 585938, 950872,
1884264, 2888844, 3694175, 5554408, 9533249, 9912342) = the shot variations (ASSUMPTION: by length and position in the bank only;
the HIRC object that says which event plays which clip is NOT parsed - `pd2_audio.banks()` parses HIRC only for music), one 32 kHz
0.77 s clip (tail?), the 0.10 s 36 kHz clips (clicks/dry fire?), stereo 0.2-0.3 s clips (distant/close layers, reload?). Picking
the shot by ear costs 5 minutes once the clips are written out as wav (`pd2_audio.write_wav`). No ear is available offline, so this
list is unverified.

## 2. Can pd2_model.py export a mesh to the Glacier .prm / .MAT / .TEX Dog Days uses? Mostly yes

- READ side: `pd2_model.py` decodes Diesel `.model` meshes (position, uv0, normal, tangent, binormal) - proven on the mask path and
  on 6 guns (`pd2_model.py info`, renders in `<work>\pd2\guns\png\npc_*.png`).
- WRITE side exists as `tools/kl_pd2mask.py`, which turns a rigid Plate (positions, normals, uvs, triangles) into a 52-byte-vertex
  chunk, an index chunk, a 48-byte descriptor, a subtab, a 64-byte mesh object, a `.TEX` record from a DDS (DXT1/3/5 only), a cloned
  `.MAT` entry. Payday 2 wolf/dallas/chains/hoxton masks went through it and one DREW in the game (2026-10-10). That is the "does
  the pipeline work" proof; gun parts differ only in three details:
  1. **Vertex layout: 40 bytes, not 52** (NEW, decoded today from stock Rifle_Type81 in F01, all five objects, `nv * 40` exact):
     +0 f32 x3 position, +12 normal (4 bytes packed like the 52-byte one), +16 colour 0xffffffff, +20 f32 x2 uv, +28 tangent (packed),
     +32 binormal (packed), +36 pad (the stock bytes are `cd cd cd cd`; write zeros or cd). I.e. the 52-byte layout minus the weights
     (+12) and palette bytes (+24). First vertex of Type81 body: pos (61.69, 5.71, 0.69), normal bytes 00 88 80 00, colour ff ff ff ff,
     uv bytes 74fe743f ef466d3f -> (0.957, 0.927). Evidence is the stock data (high), the exact pad content is unproven (the engine
     probably ignores it; stock leaves 0xcdcdcdcd).
  2. **Object: subtype 2** (rigid, one bone): +0x0c = 2, +0x38 = 1, +0x3c = the BONE NUMBER (not a bruns chunk, re/pd2_klside.md 1;
     kl_guns._part checks `c[0x0c] == 2 and u32(0x38) == 1`). Easiest: copy a stock Type81 part object (64 bytes), change +0x28 subtab,
     +0x12 material, +0x0e lod mask, +0x0f variant exactly as kl_guns does. Stock gun mesh values: lod mask 15 (full detail) or 1,
     material slot 589, draw mode 0x880 (0x80880 for the lod-16 box part).
  3. **Material**: gun parts use a gun material (Type81: slot 589), not Merc_Masks. `kl_pd2mask.clone_material` hardcodes the
     Merc_Masks source; it needs a `source` parameter. Its texture stages must be inspected first (`kl_texmat.texture_stages`):
     UNKNOWN whether the stock gun material has a normal-map stage (re/pd2_guns.md 6). Test 1 sets only `mapDiffuse`.
- Frame and winding (re/pd2_guns.md 3, measured): `DD = (PD2.y, PD2.z, -PD2.x)`, a pure rotation (det +1) plus a per-gun shift of about
  (+4, +2, 0) cm (ASSUMPTION from two pistols and one rifle; tune by `kl_guns.py sheet` overlay). Rotation keeps triangle sense,
  but DD wants the outward normal as (c-a)x(b-a) (clockwise, re/pd2_klside.md 2), so test the Payday 2 winding with
  `kl_pd2mask.outward_share` and flip if it is under 50 %. Scale 1:1 (AK 89.7 cm vs Type 81 about 95 cm: one muzzle-flash node
  of the template stays at the stock muzzle, so scale the mesh to the Type 81's length, about 1.05, so flash and bullet start
  line up).
- Limits: `.TEX` ids (limit 4096 textures; a gun adds 1), chunk table (a gun adds about 10 chunks), `.prm` cap 90 MB: none touched.

Not needed for test 1: skinned/animated parts, lod beyond one box (the stock lod-16 20-triangle box part can stay), normal maps.

## 3. How Dog Days defines a weapon (what is the unit of replacement)

(re/weapon_slots.md, re/shop_more_guns.md, kl_guns.py docstring.) One item (eFF2Item, 64 of them) = one **template** in the level's
equipment tree: `ZFFItemTemplateWeapon` with a child `Ground` (`ZLNKOBJ`, variant 0, model = the gun's .prm root). Stats, sound
references and the animation/handling set belong to the template; the model root holds the rigid parts on bones GROUND /
w_bone_frame / w_bone_clip / w_bone_slide / w_bone_hammer (+ attachers), each part with a variant byte and a lod mask. Sound: each
template's shot is a `.SND` sound object that points at in-memory clip records of the level bank `<L>_Main.WHD` (+ `.WAV`),
names like `SFX/Weapons_KL2_Final/<gun>/<gun>_Shot_NN.wav`, MS-IMA ADPCM block 0x400, mostly mono 44.1 kHz (kl_gunsnd.py docstring).
The shop table (36 rows x 24 bytes at 0xbd1f68) is hashed code-side data; a shop row only names an ITEM, and the item's template
decides everything the player sees and hears. Existing tool surface:
- model: `kl_guns.py` (LOOKS: Dead Men gun parts added as variant-gated extra parts of a Dog Days gun, needs `klhook/klgun.c` to switch
  the variant); `with_variants`, `_retarget` (point a node's ZGEOM at a NEW root so other guns sharing the old root are unaffected).
- sound: `kl_gunsnd.py replace <bank.WHD> <outdir> <map.txt>` (map.txt: `<wave name> = <wav>`, resamples to the record's rate and
  channels, keeps every offset; `--fit` keeps the stock data size), `repoint <zip> <zip> <gun> <gun to sound like>` (re-aims a gun's
  sound objects at another gun's records), `refs` (which .SND objects use each record = who else would change).

## 4. How page II adds guns: data vs hook (this decides who owns what)

`klhook/klshoppage.c` (e8): F6/P in the Arcade between-rounds shop flips to set B. A set-B row shows another USABLE ITEM from
33 35 38 40..59 62 63 (guns the stock FA maps carry but the shop table never lists) with its own name/description (from
`KLShopPage.ini`, written by `tools/kl_shop_sets.py`), the nearest stock picture, the CARRIER row's price/rank/stars. Buying hands the
set-B item over through klshop.c's pool trick (park the carrier's stock objects, add 8 objects made with 0x710ad0 from the template
0x5d2f50(item), labelled with the carrier's item). So the hook picks an ITEM; the gun's model, sound, ammo and handling are the
item's TEMPLATE in the level archive. Consequence: a Payday 2 look for a page II gun is 100 % a LEVEL-ARCHIVE change (.prm/.MAT/.TEX
for the model, .SND/.WHD/.WAV for the sound) plus, optionally, the name/description in `KLShopPage.ini` (data). The hook needs no
change for tier 1: the template is just a different gun when it is made.

Which item to use as the model host (set B, usable, rifle category = KLShopPage rifle carriers 28-35): **item 33 Type 81**
(`Rifle_Type81`, 1,605 tris, 5 parts, own root 21176, shop picture row 30) or item 35/38. Type 81 is an AK-pattern rifle, so a Payday
2 AKM on it is the least surprising swap; it is only reachable through page II or a pickup, so no stock-shop gun changes. Handling
clips: it is already proven as a hand-over (shop_more_guns.md S10: Type 81 held, fired, reloaded).

## 5. Minimal test plan: one gun, AK model + AK sound on item 33 (Type 81)

Build only into the F01 test slot or an own expansion map folder; never a stock F02-F09 zip.

Model (data side, me):
1. `tools/pd2_gun.py` (new), inputs: `wpn_npc_ak47.model` (`g_body`, `g_body_lod1` optional), `ak_df.texture`. Steps: decode mesh;
   rotate DD = (y, z, -x), scale to the Type 81's length, shift (+4, +2, 0); check winding; build the 40-byte vertex chunk, index
   chunk, descriptor, subtab (kl_pd2mask builders with the stride changed); one mesh object copied from the Type 81 body object
   (21148: subtype 2, bone w_bone_frame, lod mask 15, variant 0) with the new subtab and a NEW material; `.TEX` from the DDS.
2. Material: clone Type81's material (slot 589) with `mapDiffuse` -> the new TEX id (clone_material with a `source` argument).
3. Root: NEW root = copy of 21176 with an object table of [the new body part, the stock lod-16 box part] only (the magazine /
   slide / hammer parts dropped for tier 1: magazine does not move). Retarget Rifle_Type81's `Ground` ZGEOM at it (`kl_guns._retarget`).
   Widen the root's six bounds floats if needed (`kl_pd2mask.widen_root`).
4. Checks: `python debug/check.py`, `kl_chars.check`, `kl_guns.py sheet` (overlay of the PD2 AK on the Dog Days Type 81 in kl_view;
   this is where the grip shift is set), the verify pipeline `problems: 0`.

Sound (data side, me):
5. `python tools/kl_gunsnd.py refs <bank.SND> <bank.WHD> type81` to see which records Type 81's shot uses and who shares them. If a
   record is shared with another gun, `repoint` Type 81 to a spare gun's records first, or accept both changing.
6. Write the AKM bank clips to wav (new small `pd2_audio.py bank` command: parse DIDX/DATA, `Stream.decode`, `write_wav`), pick 2-3 shot
   clips (by ear, or by "0.3-0.4 s mono 44.1 kHz and loudest"), then `kl_gunsnd.py replace ... map.txt --fit`, and run
   `kl_gunsnd_all.py` matching afterwards so loudness agrees with the owner's rule (one loudness for every gun shot).
7. Optional: page II text for the swapped gun: `KLShopPage.ini` name e.g. `AKM (PAYDAY 2)` via `kl_shop_sets.py`.

Test (live, other session / owner): install the single-gun build into the F01 slot, Arcade, F6 to page II, buy the Type 81 row's
carrier, start the round, look at the gun in hand (third person), fire, hear the shot, reload, switch, drop. A scripted run exists
(S7-S11 recipe in shop_more_guns.md) with the Type 81 swap `16:33` already proven to hand over; add a screenshot after firing.

## 6. Effort, risks, what is unknown

Effort (me, data side): tools/pd2_gun.py about 300-400 lines (reuses 80 % of kl_pd2mask) = the main cost, 1 work block; sound
bank dump + pick + replace about 100 lines and 1 short block; overlay/tuning and the verify run 1 block; reviews 1 block. If the 40-byte
rigid path draws first time: one session. Add one iteration for each unknown below that goes wrong.

Risks, most dangerous first:
1. A malformed rigid part crashes the renderer (a wrong subtype/bone/stride has historically ended in int3 or a black/invisible
   model; the mask path was cheap to fix because it was visible). Mitigation: copy the stock part's 64-byte object byte for byte,
   change only subtab/material/lod/variant; byte-diff against stock; `check.py`.
2. Material class of gun parts expects a vertex stream/tangent layout or a normal map that a diffuse-only clone does not give
   (Type81 stage list unread). Mitigation: read `texture_stages(slot 589)` first (offline, 1 minute); fall back to keeping the stock
   texture stage list and replacing only the diffuse id.
3. Muzzle flash, shell ejection, grip place: the template's FX nodes sit at the stock gun's points. A 5 cm offset is visible;
   scale + shift tune it (pictures needed, `kl_view` overlay; ASSUMPTION about the shift is from 3 guns).
4. First-person aiming/"over the shoulder" view uses the same model, so no extra work, but the right-hand pose is authored for
   the Type 81's grip; a PD2 AK grip 2-4 cm off will look a little off. Cosmetic.
5. Sound: the correct shot clip is unverified (needs HIRC or an ear); PTADPCM decodes fine but the Wwise bank has layers
   (close + distant + tail + mechanical) as separate clips - a single dry clip will sound thin next to Dog Days' tails. Pick two
   layers and mix, or add the tail clip as the `_Distant_Shot` record.
6. Licensing/rules: Payday 2 data stays under `<work>\pd2` and the build (owner's machine), never committed (CLAUDE.md).
7. Shared records: replacing Type 81's shot records changes every NPC/AI holding a Type 81 on that map (acceptable; same as the
   Dead Men looks note "It changes the gun for EVERYONE who carries that item").

## 7. Stock maps and online (owner: "every feature must also work on Dog Days' 9 stock FA maps and in private match")

The model/sound route above edits the LEVEL archive, so it works only on our own maps (expansion folders, the F01 slot). A stock
F02-F09 map holds stock templates; editing its zip is outside the rules. Two honest options: (a) accept "Payday 2 guns on our maps" for
now (the 27 expansion maps are most of the play space), (b) a hook-side injection of a model/sound into a running stock map, which means
loading a `.prm` fragment at runtime - a large new hook subsystem with crash risk, not recommended before a test proves the data path.
Online: the shop swap is already gated off online (`kl_online()`), a peer would see the stock gun; same for models.

## 8. Division of labour

Data side (me, all in tools/ and the level archive; no game running needed):
- tools/pd2_gun.py (model + texture + material + root), `pd2_audio.py bank` (dump a weapon bank's clips), clip pick, `kl_gunsnd.py`
  replace map, `kl_shop_sets.py` text for the swapped gun, the build/verify/stage scripts, review.
Hook side (kl-merge-e8, klshoppage.c / klshop.c):
- Nothing required for tier 1 (the template swap is invisible to the hook). Optional later: a real picture for the swapped gun
  (the shop uses the NEAREST of 36 stock pictures, so a PD2 AK shows a Type 81 picture - runtime texture swap was judged "not
  recommended" in shop_cap.md); Dog Days' stock-map route (section 7b); making sure `PreMake` makes the item-33 objects as for any set-B
  item (already general).
- Also theirs: the live test run and install, since this session does not run the game.

## 9. Next concrete step (first thing to do when work starts)

1. `kl_texmat.texture_stages` on Type 81's material slot 589 (offline, answers risk 2).
2. Write `pd2_gun.py` with the 40-byte vertex builder and a selftest that round-trips a stock Type 81 body part (decode the stock
   40-byte chunk to Plates and rebuild it byte for byte, as kl_pd2mask.selftest does for the mask), THEN feed it the PD2 AK.
3. `pd2_audio.py bank weapon_akm` to dump 45 wavs for an ear check by the owner.

## 10. Critic corrections (2026-10-25, checked against code and stock data)

- CONFIRMED (read the stock data again): Rifle_Type81 in F01 has 5 rigid parts (subtype 2, +0x38 = 1), vertex chunks of exactly 40 bytes
  per vertex (body 1,467 verts / 58,688 bytes incl. padding; others 50/60/53/52 verts), body material slot 589, box part slot 550 lod 16.
  The mask-drawn-in-game claim is in open_work_log.md (2026-10-10, "WOLF plate ... drawn and textured").
- CORRECTION, section 2 headline: "Can pd2_model.py export a mesh to the Glacier .prm / .MAT / .TEX? Mostly yes" is misleading.
  `pd2_model.py` only READS Diesel models (and writes .obj and PNG previews); it has no Glacier writer. The export is `tools/kl_pd2mask.py`
  (52-byte skinned vertex, mask material), and it has no gun path. `tools/pd2_gun.py` does not exist. It was already proposed in
  re/pd2_guns.md line 307, so it is not a new finding either.
- ANSWERED, risk 2 and "unknown" in section 2.3: the stock gun material (slot 589, `Weapons/W_Rifle_Type81_01`) has stages mapDiffuse 997,
  mapNormal 998, mapSpecularMask 999, mapEnvironment (none), mapReflectionMask 999, mapReflectionFallOff 176, mapLightMap 0. So it HAS a
  normal map and specular/reflection masks. A clone that swaps only the diffuse leaves the stock normal (998) and masks on the PD2 UVs,
  which will shade wrongly (visible bumps of the old gun). Test 1 must also point mapNormal and the masks at something neutral (a flat
  normal TEX; the PD2 `ak_nm` is V8U8 and needs conversion), or accept the visual error. `clone_material` still needs a `source` argument.
- Effort: "one session if the 40-byte path draws first time" is optimistic. The mask path needed several live iterations (log 10-10), the
  material has 7 stages, the vertex pad and the bound floats are unproven, the shot clip is picked by ear without HIRC, and the live proof
  needs e8. Plan 2 to 3 blocks of work plus 2 live runs. The risk list order is right.
- Alternative worth considering: `kl_guns.py` already adds foreign rigid parts as variant-gated looks on a gun root, so the PD2 AK can ride
  that machinery (a look) instead of a second replacement root; it needs `klgun.c` to switch the variant (hook) and it changes the gun for
  everyone who carries that item. The replacement route in section 5 avoids the hook but has the same everyone-changes property.
- Not checked: "reachable only through page II" for item 33 (taken from shop_more_guns.md), the grip shift, and the 74,437-stream count.
