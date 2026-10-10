# First-person view, part C2: the player's body and the assets (Payday 2 style)

2026-10-10. RESEARCH ONLY: nothing run in the game, nothing installed, no hook change. Camera side = part C1
(re/firstperson_camera.md, another agent). Marks: (exe) read in kl2.exe (32-bit, base 0x400000);
(data) counted over files; ASSUMPTION / GUESS = not established. The two live minidumps
(`research/owner_round_1009_1820`, `_1755`) hold no process memory (113 / 82 regions, 0 MB readable; the
gamedata pointer 0xdd265c is not in them), so nothing here was checked against live memory.

## 1. Hiding or reducing the local player's own model

### 1.1 The variant filter is an exact byte compare at model build time (exe)

- The model builder is kl2 **0x67cc60** (frame 0x8154 bytes; it takes the renderer from 0x541960 =
  `[[[0xdd2640]+0x970]+0xfc]`, the same object 0x88c810 notifies). For every mesh object of a model it does,
  at **0x67cf68..0x67cf91**:
  ```
  ebp = chunk table[0xeac7b0][index]              ; the mesh object's 64-byte record (the fixed-size chunk table)
  test [ebp+0x1c], 0x800000  -> jne skip          ; a per-object HIDE bit in the record's dword +0x1c
  al = byte [ebx+0x158]                           ; the wanted variant of this build
  if al != 0: cmp byte [ebp+0xf], al -> jne skip  ; object variant byte (+0x0f, characters.md 4) must EQUAL it
  ```
  then `0x441e80(variant)`, `0x839550(LOD mask [ebp+0xe])`, `0x729f80([ebp+0x38], [ebp+0x3c])` (bone runs) on the
  draw object. What follows:
  - **Variant 0 draws every object** (the compare is skipped). Dead Men ZFFPlayers with variant 0
    (characters.md) therefore draw all 24 looks at once.
  - The compare is `cmp byte / jne`: EQUALITY, so signedness never matters (closes the open question in
    re/wardrobe.md 3: 128..255 are usable, 0 is the only special value).
  - **A variant number that no object of the model carries draws NOTHING**: no body, no head, no money bag;
    the skeleton and animation still run (the draw list is simply empty). This is the data-free way to hide the
    local player's body: `0x88c810(player, v_empty)` stores `[player+0x50] = v` and asks the renderer (vtable
    +0x70 of the 0x541960 object, args (node, 1)) to rebuild. NOT traced: the copy from `[player+0x50]` into the
    builder's `[ebx+0x158]` (six byte writes to +0x158 exist: 0x511a1e, 0x6a65ca, 0x7c0fa7, 0x827d02 (= 1),
    0x8d30f5 (= 1), 0x6df588; none reads +0x50 in the same window). ASSUMPTION: the rebuild copies the node's
    +0x50 there; the live wardrobe runs (variant 1 -> 6, 11, 92 drawn as asked, re/wardrobe.md 'Live outcome')
    show the chain works for existing variants.
  - **Hide only the head**: a variant whose objects are the body WITHOUT the head objects. The wardrobe already
    separates the two sets: Dog Days variant 2 = masked body + mask (`Merc_Masks`); Dead Men = head (materials
    head / hair / eyelash / eye / headset / glass) + body (re/wardrobe.md 3 step 2). A "headless" variant is the
    body objects of an existing variant copied under a new variant byte (64 bytes + bone runs each; `kl_chars`
    already copies objects between variants). No new geometry.
  - Alternative with no .prm change: set bit 0x800000 in dword +0x1c of the head objects' records at run time
    (the hook can write the loaded chunk table; klgun.c already writes variant bytes of loaded records). Meaning
    of the bit beyond "the builder skips the object": not established (ASSUMPTION: only a visibility flag).
- The money bag (Dog Days heisters carry it in both variants, characters.md 4) disappears with the body in a
  no-object variant; in a headless variant it stays unless left out of the copy.
- Who else calls 0x88c810: only the two mask routines 0x4b5b20 (ZGameRulesHeist; config `DisableFAVariants`
  0xb41d0c, xref 0x4b5baf) and 0x822830 (ZGameRulesFragileAlliance, xref 0x8228a4); they put 1 / 2 back. When
  they run (session start? every spawn?) was not traced; klchar.c's 'look' write already lives with that and
  re-applies when `[player+0x50]` differs (re/wardrobe.md 'Look').

### 1.2 Per-object owner-only flags: none found

- The variant is per NODE and every process sets it for every player itself (0x822830 loops over the session's
  players; the choice comes from the per-player flag at session player +0x338, obfuscated). A variant the hook
  writes into the LOCAL player's node is not sent anywhere that was found (re/netcode.md: peers address objects
  by 16-bit scene references and send state, not looks), so hiding the local body is naturally owner-only: the
  copy of the same heister in another process keeps its own variant. ASSUMPTION until a two-machine run.
- Strings `Visible` 0xb6deb0 / `Invisible` 0xb37170 belong to `SquadModifier: SetVisibility %s` (0x7e7d8e: AI
  squads, not rendering). `InvisibleToOthers` 0xb7cfca and `ForceVisible` 0xb2d900 have NO code reference.
  `AT_HIDEBODYTABLE` 0xb20e48 is referenced only from data 0xd00b84. The controllers `CutSequenceShowHide`,
  `HideItemOnPickup`, `HideEscapeVehicle` act on whole scene objects.
- No camera-distance body fade: the camera config strings (`CameraFOV`, `CameraNear`, `CameraFar`,
  `CameraTargetLen`, `CameraAutoCentering` ...) carry nothing about culling the owner near the eye.

### 1.3 First-person remnants in kl2.exe: none

- Strings: `FirstPerson`, `firstperson`, `1stPerson`, `ThirdPerson`, `ViewModel`, `viewmodel`, `FPView`,
  `CameraMode`, `HideHead`: 0 hits (ASCII and UTF-16). `FPS` once, the frame counter text (0xb3e7c0, beside
  `Resolution`). `Hands` hits are `LEFT_HAND` (a bone), `HandsOn` 0xb354c8 (xref 0x40d610, a mode name next to
  `FreeCamMouseSensitivity`), `EFM_HandsOnModeOnly` 0xb3dbdc (an enum text) and the subtitle 'Hands Behind Your
  Head'. The source names `engine\geomsextend\zlnkwhands.cpp` / `zlnkwhandsactions.cpp` are the ZLNKWHANDS class
  ("link object with hands" = a character that holds things), not a view.
- Classes (re/kl2.json, 583 names): cameras are ZBaseCamera, ZCAMERA, ZFFCam, ZFFCamera1, ZDocuCamControl /
  ZDocuCamProfile (the documentary camera), ZShakeCamera, ZCutSequenceCamera, ZPreviewCamera, ZScreenshotCamera,
  ZPIPCam, ZOnlinePIPCameraPoint, ZOnlineEscCamTrigger, ZOverlayCameraClass, ZCamOscillator, ZDistanceRumbleCam,
  CCameraBox, CCameraFog, ZCheapCam*. No view-model, hands or first-person class.
- A FREE CAMERA exists in the exe: config `FreeCamMode` 0xb54f70 (read at 0x4546b1 in the
  `engine\camera\basecamera.cpp` defaults block), `FreeCamMouseSensitivity` 0xb354d0 (0x4546f1), class name
  `FreeCamInputWintel`. Whether it can be switched on in retail is part C1's question.

## 2. Arms and weapon in the third-person animation (exe + data)

- A character is ONE skinned model: body, arms, hands and head are mesh objects of the same root with one
  skeleton (characters.md 1, 4). Arms are not a separate object; the only per-object rules are 1.1 (variant,
  hide bit). An "arms-only" variant needs copies of arm / hand mesh objects under a new variant byte, but the
  meshes are cut by MATERIAL, not by limb (a Dog Days heister body is two `Merc_0N` objects), so arms-only means
  NEW geometry: a mesh split by bone weight (the 52-byte skinned vertex carries indices into the object's bone
  palette, re/wardrobe.md), which no tool does yet.
- The WEAPON is a separate scene object (ZLNKOBJ, `equipment.zip\Weapon\<name>`, characters.md 2, tools/kl_guns.py)
  with rigid parts on `w_bone_*` bones and `GROUND`, posed by the character's `/Weapon_Handling/<item>/...` clips.
  It is placed on the character by bone id **0x1f = `r hand attacher`** (`ZLNKOBJ::GetBoneIndex` 0x5575a0,
  characters_graft.md 3.2): nine `push 0x1f` sites: 0x440c6d (object `[player+0x7fc]`, result into its vtable
  +0x340), 0x54e17f, 0x5f5785 (via `[esi+8]`, vtable +0x340 again), 0x6d06bc, 0x7ea45f, **0x836a16 / 0x836a30**
  (function 0x8369c0: `[player+0x2d48]`, type-checked through vtable +0x30 against the masks at 0x153a8f0 /
  0x153a8ec, then the bone's 48-byte pose matrix `bone*48 + 0x24 / 0x28` is read: the hand matrix for the held
  item), 0x8b7cbe, 0x8b7d43. 0x20 = `l hand attacher` for the off hand. Which of +0x7fc / +0x2d48 is the gun
  and which the held item (shield / bag) is NOT established. The attach mechanism itself is the `ZHandAttacher`
  controller (`ZGEOM_ZHandAttacher`, 52 bytes) and the general `AttachGeomToBone` controller
  (`ZGEOM_AttachGeomToBone`, 68 bytes; resolved by name at 0x49d889): a level-data way to hang ANY geometry on a
  bone of a character, which is how a Payday 2 arm or weapon model could be placed without new code
  (ASSUMPTION: it accepts a skinned character as bone owner; its fields were not decoded).
- Weapon models are the same format in both games and already swapped as looks (kl_guns.py: parts on
  `w_bone_frame / clip / slide / hammer`, `l hand attacher`, `spine1 attacher`, same grip place). The gun seen from
  behind is already there in third person; the first-person question is the camera and the arms.

## 3. Payday 2 first-person assets (hashlist only: 186,213 paths, no extensions; no .crate opened)

- Arms: `units/payday2/characters/fps_criminals_suit_1/fps_criminals_suit_1` + 14 material files
  `mtr_dallas / wolf / chains / hoxton / old_hoxton / jacket / bodhi / bonnie / dragan / fem1 / jimmy / jiro /
  john_wick / sokol`: ONE arm unit with per-character materials (sleeves / gloves). Textures
  `units/payday2/characters/shared_textures/fps_arms_jacket_df / _nm`, `fps_arms_bodhi_df / _nm` (7 files in that
  folder; the others share the suit textures). Mover: `units/payday2/characters/fps_mover/fps_mover`,
  `fps_female_1_mover`, `bain`. DLC characters add `.../characters/<id>_acc_<name>/shared_textures/fps/...`
  (12 files each: gentleman, gunslinger, t800 ...). VR hands: `anims/units/fps_hands_vr/fps_hand_left_vr /
  _right_vr` + 32 `anims/fps/fps_hands_vr/anim_hand_*` clips.
- Weapons: 18,276 `wpn_fps_` paths, 700 distinct `wpn_fps_*` unit folders; **361 base first-person weapon
  units** (`.../weapons/wpn_fps_<fam>_<name>/wpn_fps_<fam>_<name>`), by family: mel 93, pis 75, smg 60, ass 37,
  sho 19, snp 17, lmg 11, bow 8, gre 8, shot 7, fla 4, saw 4, x (akimbo) 4, m4 2, spe 2 and singles; 138
  `wpn_fps_upg_*` folders are attachments / charms. Each weapon has a `_pts` parts folder (`wpn_fps_ass_m4_pts`:
  113 paths: receivers, barrels, stocks, mags, `_df / _nm / _cc / _thq` textures, matching `wpn_third_*` parts).
  Third-person base units: 45 `wpn_third_*`. Counterparts of our guns: `wpn_fps_ass_m4`, `wpn_fps_ass_akm`
  (no ak47), `wpn_fps_smg_mp5`, `wpn_fps_smg_p90`, `wpn_fps_smg_mac10`, `wpn_fps_pis_usp`, `wpn_fps_ass_g36`,
  `wpn_fps_ass_m14`, `wpn_fps_pis_deagle`, `wpn_fps_ass_scar` (dec5 DLC), `wpn_fps_x_b92fs`; no ump, sg552, tmp.
- Animations: `anims/fps/` 3,710 paths in 186 folders, one per weapon animation family: m4, ak47, mp5, p90 have
  25 each (`_idle, _equip, _unequip, _reload, _reload_not_empty, _recoil, _recoil_enter / _loop / _exit,
  _sprint(_enter / _exit), _melee, _melee_miss, _inspect, _use, _tased*, _gogo, _get_up, _com_var1/5/6/7`), usp 3,
  deagle 7 (pistols share a generic set), `anims/fps/melee` 222, `anims/fps/unarmed` 60 (`mask_equip`,
  `hands_hidden`, `hands_falling`, throws, cuffs, watch). These are Diesel animation files for the fps arm rig;
  nothing we have reads them.
- Formats: Payday 2 is Diesel (`.model`, `.texture`, `.unit`, `.object`, `.material_config`, `.animation`) inside
  the `.crate` store (tools/pd2_crate.py reads the store; `tools/pd2_model.py` does NOT exist yet despite the
  CLAUDE.md note, nor any `re/pd2_*.md`). The arm rig's bone names and the fps weapon units' bones stay unknown
  until a `.model` is parsed; the community's Diesel model layout is public but untested here.

## 4. What an animation import would mean (.ANM)

Established (tools/kl_anm.py docstring, re/anmjoin.md, re/characters_graft.md 3.3):
- One .ANM per level: type 5 lists, type 6 sets (slot -> (condition flags, clip) pairs), type 7 slot names,
  type 4 manager + clip records (0x68 bytes in Dog Days) + data + name tables. Clip data: +0x14 seconds, +0x18
  frames, +0x1C tracks, +0x24 tracks x {4 offsets, bone index}, then pose tracks; the bone index points into the
  file's own bone table. Dead Men and Dog Days clip data are byte-identical for same-named clips, so join / merge /
  renumber work and round-trip all 41 files.
- A character set is chosen by name (`anmcol:animationdatabase#<set>`, ZLNKOBJ[2]); slots are asked by name
  from code (405 whole names in the exe: `/Weapon_Handling/<item>/...`, `/Cover/...`, `/Movement/Shoot_Pose/...`).
- Skeletons are bound to the .ANM by bone NUMBER (skeleton tables 8 / 9 / 10; `kl_chars.rebind`).

UNKNOWN for a NEW clip (no tool has written one; everything so far copies existing data blocks):
- The track data behind the 4 offsets per track (compressed keys: quantisation, key times, quaternion packing).
  kl_anm never decodes a key. Flag 0x10 "uncompressed" exists in the reader (kl2 0x5a50.. maps bone index ->
  u8) but no stock clip uses it and its layout is not established; it would be the entry point, read first from
  0x5a5060 / 0x8b4200.
- The type 6 condition bits (weapon / stance), pose tracks and the pose name table, record +0x2C, the root
  motion vectors +0x30..+0x5C (start / end blend at 0x8b4200), float +0x60, and the event id enum.
- A Payday 2 arm clip targets another rig (fps arms, camera-relative) and needs retargeting to Dog Days bone
  names and rest pose; no retargeting exists. The .ANM is per level, so every expansion map's file changes, and
  nothing in the exe asks for first-person slots: new slot names are inert until a hook drives them.

## 5. Three tiers

(a) **Camera only, own head hidden** (Dog Days data only; smallest):
   - Camera: part C1. Body: `0x88c810(player, v)` with v = a headless copy of the current variant's objects
     (a wardrobe build; kl_chars copies objects), OR the whole body off with a variant no object has (nothing to
     build; the gun stays, it is its own object). The third-person animation keeps running: the player sees his
     gun and whatever body parts remain, posed by clips authored for the shoulder camera.
   - Unknowns: the +0x50 -> +0x158 copy (1.1); whether the shadow and other passes use the same builder
     (ASSUMPTION yes: one draw list); when 0x822830 / 0x4b5b20 put variant 1 / 2 back (klchar.c re-applies);
     near clipping of the own torso at the eye position (C1).
(b) **Payday 2 arms + weapon models, static** (data import, no animation):
   - Needs tools/pd2_model.py (Diesel .model / .texture), a 52-byte skinned-vertex WRITER (none exists: kl_chars
     only moves stock objects), new mesh objects bound to Dog Days arm bones by name, materials / textures within
     kl_texmat's limits, and a variant that shows them without the body. PD2 arms are modelled for a camera at
     the eyes in the PD2 fps weapon pose; driven by Dog Days' third-person arm bones they will not meet the gun.
     A PD2 fps weapon hung by `AttachGeomToBone` / `ZHandAttacher` on `r hand attacher` is the easier half
     (rigid, like kl_guns parts).
   - Unknowns: Diesel formats (untested), PD2 arm rig vs the Dog Days rig, whether a new mesh needs .oct
     collision records (.oct records are referenced from .prm chunks), texture formats.
(c) **Animated Payday 2 first person**: (b) + new-clip writing (section 4) + retargeting + a hook that drives
   first-person slots per weapon state (idle / fire / reload / sprint, shadowing the game's own state machine,
   which asks third-person slots by name) + reconciling gun part motion (PD2 animates mag / bolt in its fps
   clips, Dog Days in `/Weapon_Handling`). Nothing of it has a decoded format on either side today.

Answer to "can it be done": (a) is a hook feature plus one wardrobe variant and can be tried as soon as C1 has a
camera; (b) is a format project (PD2 .model reader + a .prm skinned writer); (c) is a new animation pipeline on an
undecoded key format and should not be promised.
