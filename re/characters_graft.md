# Dead Men character models on Dog Days heisters

Track `h-chars`, 2026-10-09. OFFLINE work: nothing was installed and the game was not started. Stage 2
groundwork (the owner has not released stage 2). Tool: `tools/kl_chars.py` (its docstring is the format
reference). Predecessor: `re/characters.md`; where this file contradicts it, this file was measured later
and says so. "ASSUMPTION" and "not established" are meant literally.

Commands that produced every number below (run from `tools/`):

    python kl_chars.py survey      character models of the four FA maps
    python kl_chars.py bones       skeleton <-> .ANM / bone-id rules on all 41 stock levels: problems: 0
    python kl_chars.py pose        rest poses, Dead Men heroes against Dog Days heroes
    python kl_chars.py build all   the three experiments (+ `build heroes --free=alias`)
    python kl_chars.py check F01   a stock level under the same checker: problems: 0 (F01 and F07 tried)

## 0. Summary for the lead

1. The prototype exists and its three builds pass every checker: `put()` replaces the MODEL of chosen
   Dog Days people by Dead Men character models and changes nothing else. Kept builds, section 6.
2. **New fact that matters beyond characters: a skeleton is baked against its level's .ANM.** Three
   tables in every skeleton map bones to the index of the bone's name in the LEVEL'S OWN .ANM bone table
   (66,957 bones in 41 levels, 0 exceptions). The tables of all 41 files agree on the first 61 names
   only. A model moved to another level therefore animates its body correctly and its face, muscle
   helper, car-door and weapon bones wrongly. **`kl_graft` does not rewrite these tables for the map's
   models** (Dead Men agents, civilians, cars, the map's weapons): section 3.3 says what to call.
3. Game code finds bones by a numeric BONE ID through a per-model table, never by name. The ids code
   asks for are all in every Dead Men person except `free_bone01` (id 33). Its three readers do not
   crash on a missing bone but go on with uninitialised vectors. Two repairs are built in (a real bone,
   or an alias); which is right needs a live run.
4. Body proportions are not a risk: the eight Dead Men heroes and the eight Dog Days heroes are the SAME
   rig - every main bone length equal to 0.1 unit, rest rotations equal (section 4).
5. Dead Men has no masked Kane or Lynch. Variant 2 (what Dog Days shows with "Criminal Masks" on) is
   given to every transplanted model so nobody turns invisible; what it shows is a choice (section 5).
6. "One of each character per match" is what the engine already does when the eight `Hero_0N` objects
   carry eight different models, which the `heroes` build does (section 7).

## 1. Who the Dead Men Fragile Alliance characters are (`survey`)

The eight hero models are byte-for-byte the same size and shape in all four FA maps (M01 / M02 / M03 /
M06_FA_A); only the "police" model (the body a dead player comes back in) differs per map.

| object | who | bones | objects | variants | materials (LOD 0) | textures | size |
|---|---|---|---|---|---|---|---|
| `Heroes!Hero_01` | **Kane** (`Hero_HEAD_Multiplayer`, `Hero_Hair_Final`) | 101 | 432 | 1..24 | head, hair, eyelashes, eye, earpiece x3, `Merc_Rank3_8` body, play-style kit x2 | 16 | 2.10 MB |
| `Heroes!Hero_02` | **Lynch** (`Little_HEAD_Multiplayer`, `Little_Hair_01`, glasses) | 102 | 528 | 1..24 | as Kane + `Accessories_01_Glass` | 21 | 2.12 MB |
| `Heroes!Hero_03..08` | the crew: six balaclava heads, no name in the level, no head material of their own | 95-102 | 216-288 | 1..24 | balaclava x3 (`multiplayer_headset01_Rank_01` / `02` / `03`, about 380 vertices), `Merc_Rank3_8`, eye, play-style kit x2 (Hero_06: none) | 8 | 1.75-2.21 MB |
| M01 `Heroes!Henchmen_01..08` | FBI agent in a black suit, sunglasses (one model, 8 users) | 95 | 16 | 1 | `USA_Headset_01`, sunglasses x2, `FBI_Agents_BlackSuit`, `Merc_Rank3_8` | 12 | 0.59 MB |
| M02 `Heroes!USA_SecurityGuard_01..` | security guard (8 users) | 94 | 13 | 0 | 5 materials | 10 | 0.57 MB |
| M03 `Heroes!Hero_Police_01..08` | police (8 users) | 98 | 9 | 0 | 4 materials | 8 | 0.56 MB |
| M06 `Heroes!Hero_Respawn_01..08` | Japanese gang member (8 users) | **76** | 10 | 0 | 3 materials | 7 | 0.47 MB |

All use animation set `PlayerCharacter`, LOD masks 0x01 / 0x02 / 0x7c (as Dog Days). NPC models of the
same maps (FBI agents with 8 variants, the senator, civilians, guards, SWAT, Retomoto, the drug squads)
are listed by `survey`; any of them can be a source for `put()`.
Story Kane and Lynch (suits, not the FA mercenary outfit) are in the story levels and were not surveyed
here; `put()` takes any Dead Men level and scene path, so they can be tried the same way.

The 24 variants of a hero, decoded from the objects (LOD 0 vertex counts per material):
`variant = 1 + equipment (0..3) + 4 * play style (0..1) + 8 * head gear (0..2)`.
- equipment 0..3: the `Merc_Rank3_8` body grows (Kane: 3114 / 3540 / 4464 / 5037 vertices), the kit
  shrinks; on the crew, level 3 adds a bigger head mesh (about 940-1020 vertices instead of 380).
- play style: material `playstyle_01a` or `playstyle_04` on the same mesh.
- head gear: material `multiplayer_headset01_Rank_01`, `headset02` or `headset03`. On Kane and Lynch it
  is a 12-vertex earpiece - **their face and hair are in all 24 variants**. On the crew it IS the head.
Which rank / play style selected which variant in Dead Men is still not established (not needed here).

## 2. What the prototype does

`kl_chars.put(base, picks)`; a pick = (targets in the Dog Days level, Dead Men map, character, optional
variant choice). Everything else of the level stays byte for byte (checked).

| file | change |
|---|---|
| `.prm` | base file + the model sub-graph, converted (`kl_prm.convert`: 48-byte descriptors), one NEW root per pick with its own object table; skeleton repaired (section 3). Appended, nothing of the base moves |
| `.MAT` `.TEX` | the 5-11 materials and 7-21 textures per character, renumbered (`kl_texmat`); use counts recomputed; `kl_light.fit_shaders` on the new slots only |
| `.fxc` | base + `<work>/build/shared/union.fxc` (as `kl_graft` for a Dead Men map) |
| `.oct` | one record per new root. A character's record is an EMPTY tree (0 items on every hero of both games) but every root names its own; a source record with items is refused |
| `.gms` / `.prp` | record +0x0c and ZGEOM[4] of each target = the new root |
| `.ANM` | only if a bone name is missing from its table (then appended; not needed for F01 or F07) |

Not touched: class, controllers, animation set (Kane / Lynch / Kane_NPC / Lynch_NPC / Civilian stay),
sound offsets, variant id, position. Conversion of materials and textures is the path four Dead Men maps
already run live with; Dead Men NPC models have been drawn in Dog Days since milestone B.

Shaders: one material per build asked for a permutation no cache entry has and lost
`REFLECTIONENABLED` (the sunglasses / Lynch's glasses lens). Nothing unresolved.

## 3. Skeleton

### 3.1 Layout (20 dwords; n = bone count; every claim checked by `bones` on 2,247 skeletons unless marked)

| slot | content |
|---|---|
| 0 | n |
| 1 | 64 B per bone: +0 vec3, +0x0c parent (-1 root), +0x10 vec3, +0x1c name, padded with 0xcd |
| 2, 3 | 48 B per bone: rest matrix (3x3 + position), global. 18: its inverse |
| 4 | 36 B per bone (3x3, not decoded). 6: 28 B per bone, quaternion + position (local rest) |
| 5 | 256 B: **bone id -> bone index** (0xff none); one id per bone |
| 8 | 1022 B + 2 zero: **animation bone number -> bone index** (0xff none) |
| 9 | u16 per bone: bone index -> animation bone number |
| 10 | 1022 u16 + 2 zero: animation bone number -> 12 * bone index (0xffff none) |
| 13 | u8 per bone: parent (0xff root); a parent always precedes its child |
| 19 | u32 x (n - 1): 48 * parent of bone k + 1 |
| 14..17 | eight u16 = bone counts per level of detail: words 0 and 7 = n, words 1..5 = the leading bones kept at lower detail (36 / 34 in Dog Days people, 33 / 35 in Dead Men), word 6 varies. Read by kl2 0x4beab1 (largest of those a mesh's LOD mask selects). Meaning of word 6: not established |
| 7, 11, 12 | IK chains (44-byte records), face block, a 1: not decoded, travel with the model |

Getters: ZPrimControlWintel vtable 0xb91484, slots 40 (count, 0x4cefb0), 46 (slot 1), 45 (slot 4), 47
(slot 7), **48 (slot 5, 0x685bf0)**; all go through kl2 0x570b50 (root -> prop -> skeleton).
A mesh object names its bones as runs `{12 * count, 12 * first bone}` (+0x38 count, +0x3c chunk), so
appending a bone at the end disturbs no mesh.

### 3.2 Bone ids: how the game's code finds a bone

`ZLNKOBJ::GetBoneIndex(id)` kl2 0x5575a0: `table5[id]`, -1 when 0xff. 103 call sites. No lookup by name.

- FIXED ids, equal in all levels of both games: the names in the exe table 0xcd8850 / enum `eBoneID`:
  1 GROUND, 2 PELVIS, 3 SPINE, 4 SPINE_1, 6 NECK, 7 HEAD, 9-16 legs, 17-26 arms, hands, first fingers,
  31 / 32 `r / l hand attacher`, 33 `free_bone01` (`FREE_ATTACHER` in Dead Men's exe), 34 `spine1
  attacher`, 35 `hip attacher`, 36 `head attacher`.
- Constants the code passes (83 of the 103 sites): 2 (14 sites), 3, 4, 6, 7 (21 sites), 9, 0xa, 0xc,
  0xd, 0xe, 0x10, 0x11, 0x12, 0x13, 0x14, 0x16, 0x17, 0x18, 0x19, **0x1f = right-hand attacher (9
  sites: the weapon)**, 0x20 left-hand attacher, **0x21 free_bone01 (3 sites)**. The other 20 sites pass
  a register. So: pelvis, spine, neck, head (camera / aim), limbs (IK, cover), the two hand attachers.
  There is no `camera_bone` in any character: that name is in the .ANM table for camera clips only.
- Measured: 62 of the 64 character models of the four FA maps (the two others fell outside the test's
  "has PELVIS and SPINE_2" filter and were not looked at) have every one of those ids **except 0x21**.
- PER-LEVEL ids: every other bone has a number that is consistent inside a level (41 of 41) and differs
  between levels: 5 is SPINE_2 in F01 and M01_FA_A but a car's `body` in M02 / M03 / M06_FA_A; 90 of
  F01's ids name another bone in M03. Who reads these ids was **not found**. `put()` renumbers the new
  skeleton to the destination's ids anyway (`reid`; 0 changes M01 -> F01, 72 changes M03 -> F07).

### 3.3 Animation binding: by .ANM bone number, not by name (new; corrects characters.md section 5)

Slots 8 / 9 / 10 hold, per bone, the index of its name in the bone table of the level's own .ANM
(case-insensitive). `bones`: 41 levels, 2,247 skeletons, 66,957 bones, problems: 0; rebuilding the three
tables from names alone reproduces every stock chunk byte for byte.
The bone tables of all 41 .ANM files agree on entries 0..60 (PELVIS ... `r hand attacher`; body, fingers
0, hand attachers). Entry 61 is `free_bone01` in Dog Days and `FREE_ATTACHER` in Dead Men; 62..66 agree
inside each game; after that every level has its own order (`fa_jaw`: 67 in F01 and F07, 72 in
M01_FA_A, 80 in M03_FA_A; cars and weapons differ everywhere).

Consequences:
- A transplanted model MUST get new tables: `kl_chars.rebind(prm, skeleton, anm_number(anm.bones))`.
  The builds here: 29-37 bones renumbered per character (face, `xtra_mus_*`).
- **`kl_graft` (not my file).** The map's models keep the numbers of the MAP'S .ANM, while the joined
  .ANM is the systems level's table with new names appended. Effect on what is installed today
  (static reading, not seen live): Dead Men people's face / muscle bones are driven by the tracks of other
  bones (M01: Dog Days' `fa_jaw` track 67 moves Dead Men's `fa_left_eye`), and a Dead Men car's `DOOR_*` /
  `WHEEL_*` / `SEAT_*` bones (M03: numbers 68-79; appended in the joined table from 143 on) are not
  moved by the car clips `kl_anmjoin` converts - which would explain doors that do not open. Change
  wanted in `kl_graft.build`, after the .ANM join and the .prm append: for every appended skeleton
  `kl_chars.reid(prm, sk, ids)` with `ids = kl_chars.level_ids(prm_s)` and
  `kl_chars.rebind(prm, sk, kl_chars.anm_number(joined.bones))`; then
  `kl_chars.check_bones(prm, joined.bones)` in verify (a stock level returns []). The same holds for a
  Dog Days map under another Dog Days level's systems (F09 under F07: `fa_*` order differs).

### 3.4 free_bone01

In all 333 Dog Days people (characters.md), in no Dead Men model. On the 102 looked at here (F01, F03,
F07, L01, L03): always among the leading low-detail bones, parent GROUND, zero definition, id 33; the
rest matrices differ from model to model (16 different sets). Readers, all through `GetBoneIndex(0x21)`:
- kl2 0x42f900 and 0x7db520, both called from 0x4a1b40 (an action object, `+8` = the player; runs when
  0x8fde70(player) returns an object);
- kl2 0x5f2c66 in `ZFFActionCheckPulse` slot 2 (vtable 0xbb55b8).
With the bone missing: index -1 -> matrix getter 0x693490 -> 0x55c7b0 compares the index unsigned with
the bone count and returns false WITHOUT writing its outputs. No crash in the lookup; the callers go on
with uninitialised stack vectors and hand them to 0x5c9540 / 0x798d00 of the object 0x8fde70 returned.
What that object is (ASSUMPTION: the other person of a two-person action - held hostage, downed mate)
was not established, so the visible effect is not known; a crash further down cannot be excluded.

Repairs (`put(..., free=)`):
- `add` (default; builds `civ`, `bot`, `heroes`): a real bone appended at the end, parent GROUND, rest
  values copied from the Dog Days model the target had, bound to .ANM bone 61 so Dog Days' clips move
  it (about 150 clips per set do). ASSUMPTIONS: it lies past the low-detail prefix (Dog Days keeps it
  inside); detail word 6 raised only where it equalled n; slots 7 / 11 need nothing.
- `alias` (build `heroes_alias`): id 33 -> GROUND in table 5, one byte. The readers get the ground
  matrix: defined values, the animated offset lost. Animation untouched (other key).
- `none`: Dead Men's state.

## 4. Will Dog Days' Kane / Lynch sets drive a Dead Men skeleton? (`pose`)

| bone (local rest length) | Dog Days Hero_01..08 | Dead Men Hero_01..08 |
|---|---|---|
| PELVIS height | 96.2-96.4 | 96.2-96.4 |
| SPINE / SPINE_1 / SPINE_2 / NECK / HEAD | 9.9 / 12.2 / 14.0 / 20.9 / 4.9, all eight | the same, all eight |
| clavicle / upper arm / forearm / hand | 14.2 / 17.0 / 25.1 / 24.2 | the same |
| thigh / calf / foot / toe | 9.7 / 43.8 / 43.1 / 16.1 | the same |
| head height at rest | 162.7-162.9 | 162.7-162.9 |
| right-hand attacher height | 106.2-106.4 | 106.2 (Hero_04: 107.9) |

Largest bone-length distance from any Dead Men hero to the nearest Dog Days hero: 0.00; rest rotations
equal (1 - |q.q| = 0.0000) except Hero_04's clavicles (0.0036, arms slightly raised at rest; hands 1.7
higher). 89 bones are in all 16 heroes; the only bone every Dog Days hero has and no Dead Men hero has
is `free_bone01`. Bones a Dead Men hero lacks otherwise are optional face / muscle helpers that Dog Days
heroes lack here and there too.
Verdict: the same rig; weapon grip, cover and aim poses will sit as on a Dog Days hero. Not answered
offline: whether faces animate well (face clips are bound correctly now, but were authored for other
heads), and the M06 respawn model with 76 bones (no fingers / face bones: static hands).

## 5. Variants, LODs, the mask

- Dog Days sets variant 2 on heisters when "Criminal Masks" is on (characters.md 6). `put()` gives every
  new root exactly the variants the target can be asked for - 1, 2 and the target's own - and drops the
  objects of all others (Kane: 432 -> 36 objects). A source without that number gets its first variant
  under it (henchman: 1 and 2 are the same 16 objects; M02 / M03 / M06 police have only variant 0).
  `check()` fails a heister model that lacks 1 or 2.
- Default for the heroes is Dead Men's own 1 and 2: mask off = equipment level 0, mask on = level 1 (a
  little more kit). Since Dead Men has no masked Kane / Lynch, a truer "masked" look needs a decision:
  `{1: 1, 2: 4}` (heaviest kit), or for the crew the bigger head of level 3. Syntax: `...:1,4`.
- LOD masks equal in both games; untouched.
- The money bag Dog Days heisters wear from the start of a round (mesh `MoneyBag_01` in both variants,
  weighted to spine and clavicle) is NOT on a Dead Men model. Transplanting it = copying those objects and
  renumbering their bone runs by name; not done.

## 6. Kept builds (stock F01 as base; all `problems: 0`; none installed, none run)

Folder `<work>\build\chars\<name>` = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\chars\<name>`,
each a complete slot (archive + the stock files beside it) and `chars.json` (what was done).
Install, by a later LIVE agent only: `python tools/kl_graft.py install F01 --from "<folder>"`.

| build | what | .prm | materials | textures |
|---|---|---|---|---|
| `civ` | M01 henchman (95 + 1 bones, one variant given as 1 and 2) on civilian `Gameplay!CiviliansFront!Civ_Platform1_Runnning\JPN_CIV_05\Ground` (set Civilian) | 24843 -> 24970 chunks, +0.6 MB | 622 -> 627 | 1266 -> 1277 |
| `bot` | Dead Men Lynch on `Heroes!Hero_02\Ground` and on `Gameplay!merc_bot_squad!Squad#02\Glazer_Bodyguard_02\Ground` (they share a model in stock too) | -> 25031, +1.2 MB | -> 630 | -> 1286 |
| `heroes` | Dead Men Hero_01..08 on Dog Days Hero_01..08 and the seven bots | -> 25971, +7.6 MB | -> 632 | -> 1292 |
| `heroes_alias` | the same with `free=alias` | the same | | |

`check()` on each: every node fits its class; .gms model = .prp model; `kl_prm.check` and every root
reachable; `kl_mat.check`; `kl_tex.simulate_dd_loader`; every material slot and texture exists; use
counts equal the .prm's; no new material without a compiled shader; .oct re-packs, each root its own
record, the base's records did not move; skeletons bound to the level's .ANM and bone ids level-wide
consistent; every person has its variant (heisters 1 and 2) and its animation set; base chunks,
materials, textures and all other members unchanged. Negative tests: without `rebind` the checker
reports "31 bones carry another level's animation number"; a hero model without variant 2 is reported.
Also built in memory (not kept): F07 as base with M03_FA_A Kane (variants 4 and 12) and the 76-bone
M06 respawn model: problems: 0.

Police after death (`Heroes!RespawnPolice#01..08`, one shared model) are untouched; they can take a
Dead Men police model with one pick listing the eight targets joined by `+`.

## 7. One of each character per match

- A heister's body is the `Hero_0N` object the game rules hand the player: `GetHero(2, index)` =
  `[rules + 0x208 + 4 * index]`, filled from the objects' rank property (menus.md 5). Arcade: index = the
  byte at `rules + 0x33d` (random 0..7 from the constructor, to be written as data by the hook,
  antitamper.md 5.4); the bot that had that hero is swapped (0x8f5e90, partly decoded). Online: a
  per-player session number, clamped to 0..7.
- So with eight different models on the eight objects (build `heroes`) nobody can appear twice BY DATA,
  as long as two players never get the same index. Arcade: one human, guaranteed. Online: the session
  number being unique per player is an ASSUMPTION of menus.md, and a CHOSEN hero (stage 3 / 4) has to
  be made unique by the host - a permutation of 0..7 kept by the hook; no data-only way was found.
- The bots keep their identity by the digit in their object name and share the hero's model chunk, so
  the `heroes` build changes hero and bot together.
- More than eight characters cannot be done with objects (eight ranks, eight slots). Route worth a
  study, not built: two characters in ONE model as different variants (Dog Days merc = 1 / 2, Dead Men
  character = 3 / 4) and the engine's own variant setter 0x88c810 to switch. It needs both bodies on one
  skeleton; the body rigs are equal (section 4), the mesh bone runs would be renumbered by name. With
  only two looks per slot even the stock "Criminal Masks" toggle would switch them without any hook.

## 8. What only a live run can settle, in this order (one variable per run)

1. `civ` - loads? the figure in a suit runs on the platform with the civilian set, not collapsed,
   textured? Fails here = model / skeleton conversion (descriptors, appended bone, tables).
2. `bot` - Dead Men Lynch stands beside the player in Arcade as team mate 2: weapon in the right hand
   (id 0x1f), cover, firing, dying (ragdoll: slot 7 / Havok data travel unconverted - watch this), face.
3. `heroes`, Arcade, several rounds until the random index gives each body: the LOCAL PLAYER as Kane,
   Lynch, crew: camera, aim, cover, vault, loot, the van. Then "Criminal Masks" on (variant 2 visible?).
4. A two-person action (the readers of free_bone01): grab / be downed and helped. If it misbehaves:
   `heroes_alias`, same test - tells whether the appended bone or the missing animation is at fault.
5. Low detail: a bot far away (LOD masks 0x02 / 0x7c with the free bone past the prefix).
6. After the lead adds `rebind` / `reid` to `kl_graft`: do Dead Men car doors open and agents' faces
   stop twitching on the bank map.

## 9. Not established

- What reads the per-level bone ids; what object 0x8fde70 returns and what the free bone positions.
- Skeleton slots 4, 7, 11, 12, detail word 6; the first and third vector of a bone definition.
- Whether ragdoll / hit-zone data depends on anything a Dead Men model lacks (not looked at).
- Which Dead Men rank / play style picked which variant; whether a session number is unique online.
- The 20 `GetBoneIndex` sites that pass a register (ids from data).
