# The black box round a burning car

Track T, 2026-10-11 (second version, after the review `re/carfx_review.md`). Owner, playing Withdrawal (slot F03):
*"btw fix that black box on these cars that are blown up"*. Pictures `<work>\research\watch\20261011_155753\`
`0007_150s.jpg` (close, beside a burning police car: the right half of the frame is dark) and `0006_104s.jpg`
(from the garage: a dark block over the burning car).

**Everything here is file reading and shader reading. NOTHING RAN IN THE GAME.** Tool: `tools/kl_fa_carfx.py`
(`check`, `apply`, `apply --alpha-only`, `apply --smoke-clear`, `material`). Builds: `<work>\build\z_carfx\`.

## 0. Where this stands

- **Two candidates, not decided.** A burning car that has blown up switches on (a) a Dead Men heat-shimmer MESH
  in a material form Dog Days never draws for that class, and (b) Dead Men smoke EMITTERS with near-black smoke.
  The pictures fit (b) better than (a) (section 2). Neither was seen in the game on its own.
- **What is built:** the fix for (a) on all five maps (the mesh off), and for the bank a TEST TWIN that does the
  opposite (mesh kept, the dark smoke invisible), so that one look in the game says which it is (section 5).
- **Do not install `z_carfx` for the owner as "the fix" before that look.** With the mesh off a dark column over
  a burning car MAY WELL REMAIN: that would be the smoke.
- Switching the mesh off is harmless either way: Dog Days has no heat shimmer on any of its own fires.

## 1. The mesh (facts)

| | |
|---|---|
| entity | `HeatShimmer` (ZSTDOBJ), child of the fire group a vehicle's `VehicleEffects` controller names: `...\Effects/AllocMany/All_level/CarFire_USA_Sedan_01_Cheap.zip\Car_Fire_USA_Sedan_01_Cheap\Group_CarFire_ALL` (the template in the map + 3 copies in `CloneGroup_Effects/...`). The bank: nodes 3939.. / 9795.. of `z_cover3\M03`, model root chunk 58429, mesh 58427. The same entity with the same matrix is in Dead Men's M03_FA_A (node 6507) |
| shape | an open box, 28 vertices (a bottom cap and four walls, no top): bounds (-164 0 -305) .. (162 367 320) = 3.3 m wide, 3.7 m high, 6.3 m long. Vertex alpha 0 on the bottom ring (y 0) and the top ring (y 367), **0.75** on the ring at y 195 |
| lie | the 6.3 m side is along the car: in the group's frame the wheel fires stand at x about +-85, z about -118 (front) and +148 (back), so the car's length is z, as the mesh's. The matrix (0 0 1 / 0 1 0 / 1 0 0) is this engine's stored "no rotation" (every plain group above the fire, all 2028 particle templates of F01 + F03 + F07); the mesh's and its group's (0 0 -1 / 0 1 0 / -1 0 0) is half a turn about y, which a box that is the same both ways does not show |
| material | `Effects/Heat_Shimmer_01` (bank: slot 1129), class **Standard/Glass**, blend `TRANS_ON_OPAQUE`, render group 0x41, `Refraction2DEnabled` + `BumpEnabled`; `mapDiffuse` = texture 1901 `Heat_Shimmer_01` DXT3 256x256, grey, **alpha 0 in every texel**; `mapNormal` = 1902 DXT5; `gm_mapRefraction2DMask` = no texture (TXID 0) |
| shader | `glass.fx`, MESH_STANDARD + BLENDENABLED + BUMPENABLED + REFRACTION2DENABLED + STDSAMPLERSTATE: **in the level's cache** (so it is drawn, not skipped) |

The yard's two police cars are `AI_Enemies!ArrivingCops_Squad_01\PoliceCar_Reinforcement_01` at
(1080, 212, -1736) and `...Squad_02\PoliceCar_Reinforcement_02` at (-1283, 208, -1416), both ZHavokCar with
`BlowupChanceDefinite`. Their `VehicleEffects` names two fires:

| fire | when | the mesh | smoke emitters |
|---|---|---|---|
| `Car_Fire_USA_Sedan_01` | burning, before the blast | **none** | two |
| `Car_Fire_USA_Sedan_01_Cheap` | after the blast | `HeatShimmer` | five |

Also switched on by a blast: `Car_Explotion_01` (glass, fireball and smoke emitters; `Omni_Explode`, a ZOMNILIGHT
whose record is the stock rocket light's with intensity 0), the damage smoke `Car_Damage_Smoke_USA_Sedan_*`
(texture `FX_Par_Smoke_White_01`), the wreck model `V_Coli_Shot_02`, the siren quads.

### What the files say about how the mesh is drawn

The shader is the same in both games. Dead Men ships the source (`Shaders/PC/FX/Glass.fx`, `AmbientHQ_PS20`);
Dog Days' compiled entry, disassembled with `D3DDisassemble` from the build's .fxc, is that code:

```
refr   = tex(samplerRefraction2D, screen uv - bump.xy * gm_vRefraction2DScale)       the copy of the frame
colour = lerp(refr * gm_vRefraction2DColor * tex(samplerRefraction2DMask, uv),
              2 * light * diffuse.rgb,  diffuse.a)                                    diffuse.a = 0 -> the first
alpha  = vertex alpha            Dog Days vertex shader:  mov o1.w, v4.w  (COLOR3 = vertex +16)
       = vertex alpha * CalculateAlphaFade(position, normal)                          Dead Men (Glass.fx line 31)
```

In Dead Men the box puts the frame behind it back on the screen, displaced by a scrolling normal map: the air
wobbles. `CalculateAlphaFade` with the material's `gm_vAlphaFadeDistScaleOffset` (0, -0.002, 1, 2.167) is 1 up
to 5.8 m from the eye and 0 from 10.8 m. In the build:

1. **`AlphaFadeEnabled` and `ScrollEnabled` are off** and the two `gm_vAlphaFade*` values are gone
   (`kl_mat.convert_mat_full` drops properties Dog Days' Glass class never has; `kl_light.fit_shaders` then
   switches the BOOLs off because no `glass.fx` entry of the cache has those defines). FACT. What follows from
   it - the mesh is drawn at any distance - is the shader's arithmetic; **no picture shows it** (2.2).
2. **The form.** Dog Days has 50 Standard/Glass instances in its 21 stock levels, every one a refraction, in
   five (blend, render group) forms: opaque in group 0 (5), `TRANS` in 0x6c (42), `TRANS` in 0x46 (1), `ADD` in
   0x6f (1), `ADD_BEFORE_TRANS` in 0x69 (1). `TRANS_ON_OPAQUE` in 0x41 is none of them - **for the class Glass
   only**: the same blend and group is Dog Days' commonest decal form (1045 Standard/Standard instances).
3. **GUESS, the whole chain: that the refraction comes out dark there.** Nothing in the files says so. The
   candidates would be the frame copy not made yet when the "on opaque" groups are drawn (stock refracts in
   groups 0, 0x46, 0x69, 0x6c, 0x6f only), the mask stage without a texture (33 stock Glass materials have none
   either), or the effect's second technique `RefractionMask`, whose pixel shader writes (0, 0, 0, 1). If the
   frame copy IS right at that point, the mesh shows a still, slightly displaced copy of the picture behind it
   and is nearly invisible.

If it were dark, it would be a band: 0 at the ground, 75 % at 1.95 m (just above a sedan's roof), 0 again at
3.67 m, the same on all four sides, and it would not move.

## 2. The smoke (the other candidate) and what the pictures say

### 2.1 The fires' smoke

`check` now lists it (lines "smoke of the fires the vehicles name"). The bank, the two fires + the blast:

| template | emitters | darkest colour key, highest alpha key | sprite texture (mean alpha of 255) |
|---|---|---|---|
| `Smoke_CarFire_02a` | 3 | **(26, 24, 22)**, 178 | 264 `FX_Par_Smoke_Dark_05` DXT5 (68) |
| `Smoke_CarFire_02` | 2 | (26, 24, 22), 128 - in one of TWO unlike templates of that name (the other is (75, 12, 0)-based); which one the game takes was not read | 226 `FX_SmokeAnimated_A_4x4_01` (29), the sprite of 218 other templates too |
| `Smoke_CarFire_01a` | 2 | white (255, 255, 255), 178 | 264 `FX_Par_Smoke_Dark_05` |
| `Smoke_Blowout_01` | 1 | white, 51 | 226 |

Near-black smoke at alpha 0.7; many particles stacked reach full black. What was compared (scratch scripts, this
round):

- **The templates are Dog Days' own.** Every template the car fires name lies in
  `AllLevels/mainsceneincludes_multiplayer.zip\AllLevels/equipment.zip\Effects/ParticleTemplates.zip\Template_Car...`
  = F07's systems, which the graft keeps. The reviewer found them field for field equal to Dead Men's M03_FA_A
  templates but for the sprite chunk index. So Dog Days shipped Dead Men's car-fire templates unchanged.
- **No stock Dog Days emitter uses them.** In the 21 stock levels no ZParticleEmitter names any of the 15 template
  names the vehicles' fires use (`Smoke_CarFire_01 / 01a / 02 / 02a`, `Smoke_Blowout_01`, `Flames_CarFire_01b /
  01c / 02b / 02c`, `Sparks_CarFire_01`, `Car_Exp_Fire_FireBall_01 / Flash_01 / Spark_01`, `Gren_Default_ShockWave`,
  `Flash_Hind_01`); on the bank that is 28 of the 29 emitters of the three groups. The flames among them draw
  right in the owner's picture, so this alone proves nothing - but these fires are Dead Men emitters on leftover
  templates that Dog Days itself never plays through an emitter.
- **The emitter pairing loses no number.** Dead Men's emitter has 33 fields, the build's 35
  (`kl_convert.LEVEL_MAPS['ZParticleEmitter']`). For the car fire / blast / damage emitters with a Dead Men twin
  of the same path:

  | build against | emitters | every mapped field = Dead Men's | unequal |
  |---|---|---|---|
  | `z_route3\M01` / M01_FA_A | 122 | 118 | DD11<-DM13 x4 |
  | `z_loot3\M02` / M02_FA_A | 136 | 122 | DD10<-DM12 x10, DD11<-DM13 x4 |
  | `z_cover3\M03` / M03_FA_A | 646 | 632 | DD10<-DM12 x10, DD11<-DM13 x4 |
  | `z_route\M06` / M06_FA_A | 648 | 644 | DD11<-DM13 x4 |

  DD10 / DD11 are the two id fields (0xffffffff = none in most), not a size, rate or colour; why 14 differ was
  not looked at. The three Dog Days-only fields DD14, DD22, DD33 are 0 in all 1552, which is stock's commonest
  value (14,103 of 14,121; all; 13,694). Dropped: DM9, 0 in every object.
- **What stays ASSUMED:** the pairing itself (`re/pairings.md`: high confidence, DD8 medium, DD16 weak) and that
  Dog Days' emitter code makes the same smoke from the same numbers (size, growth, sorting, the template's new
  field 37). Neither can be decided from files.

### 2.2 The pictures (corrected after the review; the reviewer's measurements, my own look agrees)

- **`0007_150s.jpg` is darker than the mesh can make it, and dark in the wrong place.** Luminance right of x 760
  is 1..10 of 255 for y 0..210 and 9..37 for y 240..330; the same building is about 100 in `0009` / `0010`:
  over 97 % covered at the top of the frame. The mesh's alpha is 0.75 at most, at roof height, and 0 at its
  3.67 m top: it would be darkest just above the roof and clear above. The picture is the other way round. The
  car, which stands inside the box, is not darkened. (The first version of this note said "up to 75 %, darkest
  in a band, never opaque": wrong.)
- **The "hard vertical edge" is not a box corner.** The same purple vertical streak is in `0004_54s.jpg` (inside
  the bank, with the same one-sided veil and flare) and `0005_97s.jpg` (garage), where no car burns: the game's
  own light streak. In `0007` the building's corner against the burnt-out sky lies at the same place.
- **`0006_104s.jpg` does not show the box either.** The car's body and the wall beside it at roof height are not
  darkened; the dark block starts about 0.6 m inside the car's rear end, reaches about 4.5 m up and has a soft
  top. A box round the car would darken a band wider than the car. This reads as a smoke column - blocky, with
  square pieces, which is why it looks like "a box" and not like smoke.
- So the pictures support: thick near-black smoke over the car, seen from inside it in `0007`. They do not
  exclude the mesh adding to it.

**The HUD step of 15:20** (`kl_hud.py all ... --look deadmen`): `<work>\build\hud_new\_src\DM03` -> `hud_new\DM03`
changed .TEX (18 textures: borders, weapon / ammo / tracker / meter plates, eight font atlases) and .prm (font
chunks); none of the 41 fire / smoke / shimmer textures, not the .MAT, not the mesh. That is shown for the
archive installed NOW (200,754,498 bytes, written 16:02, installed 16:04). **The round in the pictures loaded
another one** (`KLHook.log` 15:58:13: `F03_Main.zip` 200,772,920 bytes) that is no longer on disk - an earlier
run of the same step, by its size neither the build before the step (200,801,333) nor the one after. For that
archive nothing can be shown. The mesh and the smoke are in the build before the step already, so the step did
not bring them; whether that earlier run changed a smoke texture cannot be said.

## 3. What `apply` makes

| command | what changes | for |
|---|---|---|
| `apply <build> <out>` | the mesh **off**: its 28 vertices moved to the mesh's local origin (no triangle has an area, so no technique of the effect draws a pixel, the refraction mask included) and every vertex alpha 0. One vertex chunk of 1120 bytes per mesh; only the `.prm` member differs, same size | the fix for candidate (a) |
| `apply --alpha-only <build> <out>` | the same chunk, the vertices left in place, alpha 0 | if a blast misbehaves with the fix (a zero-area mesh is in no stock level): this tells the two changes apart |
| `apply --smoke-clear <build> <out>` | **TEST ONLY, NOT A FIX.** The mesh is left as it is; the alpha of the sprite textures that ONLY the fires' smoke templates use is set to 0 in every mip (the bank: texture 264 `FX_Par_Smoke_Dark_05`, 9 mips, the sprite of `Smoke_CarFire_01a` / `02a`). Only the `.TEX` member differs, same size. `check` on it still FAILs, on purpose | the twin for the live look: smoke gone, mesh there |

In the smoke test `Smoke_CarFire_02` and `Smoke_Blowout_01` stay (their texture is the sprite of 218 other
templates): a thinner smoke can remain.

**Lost with the fix:** the heat shimmer over a burning vehicle. Flames, smoke, sparks, the blast, the light:
untouched.

`check` needs no Dead Men file. Rule: a Standard/Glass instance whose (blend, mode, render group) is not one of
the five stock forms is "a glass form no stock level draws"; every mesh that uses it must have vertex alpha 0
(it says whether the shape is kept). It also walks every emitter (template by name -> sprite chunk -> texture)
and lists the fires' smoke. The smoke is a fact line, never a fault.

**For the source** (not changed: other sessions hold the files): `kl_mat.convert_mat_full` should not keep a Dead
Men Standard/Glass instance in a form Dog Days never draws that class in, and `kl_light.fit_shaders` should not
switch `ALPHAFADEENABLED` off on a refraction as if it were a detail - that fade is all that hides the surface.
Either take the mesh out of its model in `kl_graft`, or stop and say so.

## 4. The five maps

`python tools/kl_fa_carfx.py check [--cars] <build>`. Same material and the same car box in all five; Retomoto
has two more meshes, on its trucks and buses.

| map (build) | material slot | meshes | where (entities) | vehicles with VehicleEffects -> name a fire with the box | emitters / template missing / sprite or texture missing |
|---|---|---|---|---|---|
| Hot Coffee `z_route3\M01` | 1345 | 1 (49623) | `Car_Fire_USA_Sedan_01_Cheap\Group_CarFire_ALL` x4, 3.3 x 3.7 x 6.2 m | 9 -> 9 (4 ZHavokCar: Bentley_01 / _02, the ram truck, the cement truck; 5 parked) | 4832 / 3 (`Impacts_Default_Smoke`, known) / 0 |
| Late Night Opening `z_loot3\M02` | 1019 | 1 (55928) | the same, x4 | 7 -> 7 (PoliceCar_01 + 6 parked in the car park) | 6535 / 0 / 0 |
| Withdrawal `z_cover3\M03` | 1129 | 1 (58427) | the same, x4 | 10 -> 10 (5 ZHavokCar: three police cars, the SWAT sedan, the delivery car; 5 parked) | 6246 / 0 / 0 |
| A Walk in the Park `z_route\M06` | 788 | 1 (46064) | the same, x4 | 3 -> 1 (`Traffic!V_JPN_GetawayVan_A_Static_00`; the two helicopters name no fire) | 4964 / 0 / 0 |
| Retomoto `z_rooms\retomoto_full` | 1154 | 3 (50232, 50238, 50244) | the car box x4; `SWAT_Explosion_AM.zip\Explosion_and_Fire_01` x3, **3.4 x 6.9 x 8.2 m**; `Bus_Explosion_AM.zip\Explosion_and_Fire_01` x3, **3.4 x 6.9 x 11.9 m** | 68 -> 67 (45 cars and taxis, 2 SWAT trucks + 20 buses with the big ones; the roof helicopter none) | 5713 / 39 (the known `*_Art_M02_*`) / 0 |

The same four smoke templates are in all five (Retomoto also `Smoke_CarFire_01`, black (0, 0, 0), and ten
`Smoke_CarFire_02` emitters on its trucks and buses).

Results of `apply`, REBUILT 2026-10-11 16:48 with the second version of the tool (the archives came out byte
for byte as in the first round; `carfx.json` / `carfx.txt` now carry the smoke lines). Each: check before FAIL,
after PASS; only the `.prm` member differs, same size; no member grew; every file beside the archive copied;
`steps.json` continued.

| out | chunks changed | archive sha1 | kl_impact | kl_fa_bots_dyn check, source / out | kl_maps audit |
|---|---|---|---|---|---|
| `z_carfx\M01` | 49620 | c2c623e9 | problems: 0 | exit 1 / 1, 42 lines, 0 differ (the known civilian-money FAIL, on purpose) | no audit in the source |
| `z_carfx\M02` | 55925 | 4414a471 | problems: 0 | 0 / 0, 31 lines, 0 differ | bad 0 -> 0 (first round; not re-run, the archive is the same) |
| `z_carfx\M03` | 58424 | 720be205 | problems: 0 | 1 / 1, 43 lines, 0 differ (as M01) | bad 0 -> 0 (as M02) |
| `z_carfx\M06` | 46061 | 26df702f | problems: 0 | 0 / 0, 26 lines, 0 differ | bad 0 -> 0 (as M02) |
| `z_carfx\retomoto_full` | 50229, 50235, 50241 | 521186a0 | problems: 0 | 0 / 0, 65 lines, 0 differ | no audit in the source |
| `z_carfx\M03_alpha` (`--alpha-only`) | 58424 | c12284bb | problems: 0 | 1 / 1, 43 lines, 0 differ | not run |
| `z_carfx\M03_smoketest` (`--smoke-clear`, TEST ONLY) | none; `.TEX` texture 264 | 602c4ffb | problems: 0 | 1 / 1, 43 lines, 0 differ | not run |

THE z_carfx BUILDS ARE MADE FROM THE BUILDS BEFORE THE HUD STEP. What is installed went through `kl_hud.py`
afterwards. The mesh's vertex chunk is byte for byte the same in `hud_new\DM03` (the reviewer), and `apply` on
`hud_new\DM03` (tried in the first round, the result deleted) changes that one chunk and nothing else. So: run
`kl_fa_carfx.py apply` on the HUD build (or the HUD step on `z_carfx\<map>`). The smoke test's texture 264 is not
one of the 18 the HUD step changes.

## 5. Live check (the lead; nothing here was run)

The question is WHICH of the two the dark block is. Three bank builds, the same spot, one difference each:

| | build in the slot | mesh | dark smoke |
|---|---|---|---|
| A | `z_cover3\M03` (as installed, + the HUD step) | drawn | drawn |
| B | `z_carfx\M03` (+ the HUD step) | off | drawn |
| C | `z_carfx\M03_smoketest` (+ the HUD step) | drawn | not drawn (texture 264 clear) |

Withdrawal, any hook. Get into the yard; the two police cars stand at (1080, 212, -1736) and (-1283, 208, -1416).

1. **A car that burns but has NOT blown up** (shoot it until flames show, stop). That fire
   (`Car_Fire_USA_Sedan_01`) has no mesh in any build. A dark block there, in A or B, is smoke and nothing else.
2. **After the blast, the same two spots in A, B and C:** 2 - 4 m from the car's front corner looking along its
   side (as `0007_150s.jpg`), and from the garage door, 20 - 25 m (as `0006_104s.jpg`). Take the pictures and
   say what changed:
   - **B looks like A, C is clear** -> it is the smoke. The mesh fix is not the owner's fix. Next step: the smoke
     emitters (size, rate and sorting of `Smoke_CarFire_02a` / `02` against what Dead Men shows for the same
     car; the emitter's assumed pairing, `re/pairings.md`; the two unlike `Smoke_CarFire_02` templates) -
     NOT `V_Coli_Shot_02`.
   - **B is clear, C looks like A** -> it is the mesh. `z_carfx` is the fix.
   - **Both B and C are better, neither is clear** -> both add; the smoke still needs its own look.
   - **Neither changes** -> neither; then the wreck model and the blast's emitters.
3. **Judge the mesh by its shape, not by "something dark":** a band at roof height (0 at the ground, strongest
   at about 2 m, gone at 3.7 m), the same on all four sides of the car, that does NOT move or drift. Smoke
   moves, rises above 4 m and thins with the wind. In C, where the smoke is gone, the mesh is alone on the
   screen: if nothing of that shape is there, the mesh never was the box.
4. In B, flames, sparks, smoke and the blast must be as in A (the fix must take nothing else).
5. If the game misbehaves at a blast in B (a fault, a missing fire): run `z_carfx\M03_alpha` - the same fix with
   the mesh's shape kept. It fine there = the zero-area mesh is the cause.
6. Retomoto's street, once the bank is decided: a burning bus or SWAT truck from the pavement beside it (its
   mesh was 12 m long and 6.9 m high; ten `Smoke_CarFire_02` emitters).

No log line tells any of this: it is a look at the picture. `tools/kl_watch.py` pictures of the three runs from
the same spot are what to compare.

## 6. Assumed / not established / not done

- **NOT ESTABLISHED: what the dark block of the pictures is.** GUESS in the first version: the mesh. After the
  review the smoke fits the pictures better (2.2); the mesh may add to it or be invisible. Section 5 decides.
- **GUESS, all of it:** that the refraction is dark in Dog Days in this form, and why (section 1, point 3).
- ASSUMED: a mesh of zero area is harmless (D3D draws nothing for degenerate triangles; the model root and its
  bounds are untouched). No stock mesh is like that; `--alpha-only` is the fall-back.
- ASSUMED: with vertex alpha 0 alone (`--alpha-only`) nothing of the mesh is drawn - true for the technique
  read; where the engine sends `RefractionMask` was not read.
- Not done: any change to the smoke for the owner. `--smoke-clear` is a test, it removes smoke the owner may
  want; a real answer (thinner, lighter, or Dead Men's look) needs the live look first and is the owner's call.
- Not done: a material that shows the shimmer the Dog Days way (it would need AlphaFade in `glass.fx`, which the
  cache does not have, or a Standard/Standard SmoothSmear material like L11's jet exhaust - a new look).
- Not read: which of two unlike templates of one name the game takes; why DD10 / DD11 differ on 14 emitters.
- Seen on the way, not changed: three more materials lost `AlphaFadeEnabled` in the conversion -
  `Locations/_USA/Glass/Glass_Plain_01a_USA` (Hot Coffee, Standard/Standard ADD), `Locations/M03/Glass/
  Glass_Opaque_01a_SemiShadow_M03` (bank, ADD_BEFORE_TRANS), `Locations/M08/Effects/Effects_GlowRED_01a_M08` (bank,
  Glow, opaque). One mesh each; they may show at distances where Dead Men hid them. The police cars'
  `LOD_Light_*` / `Light_*` siren quads (28 x 54 cm, `Glow_Siren_01a`) are Standard/Standard with blending OFF
  in the build: not looked at further.

## 7. The review's points

| | |
|---|---|
| M1 picture darker than the mesh allows, dark in the wrong place | accepted: 2.2, section 0, section 6; the first version's "up to 75 %, never opaque" withdrawn |
| M2 the vertical edge is the game's light streak | accepted: 2.2 |
| M3 the smoke was not excluded | accepted: 2.1 (templates, colours, the emitter pairing compared on four maps), `check` lists the smoke, `apply --smoke-clear` makes the twin build, section 5 rewritten, next step = the emitters |
| S1 `0006` does not show the box | accepted: 2.2; "drawn at any distance" is marked as arithmetic without a picture |
| S2 the photographed archive is not the one compared | accepted and checked in `KLHook.log`: 2.2, last paragraph |
| S3 "a form no stock level draws" holds for the class only; the cause chain is a guess | accepted: section 1 points 2 and 3, the tool's docstring |
| S4 50 instances, not 49 | corrected (note and tool) |
| S5 the box's orientation | done: section 1, "lie" (the wheel fires give the car's axis; the stored no-rotation matrix) |
| S6 an alpha-only variant | done: `apply --alpha-only`, `z_carfx\M03_alpha` |

## 6. The club map (DM05A, 2026-10-12): what `check` counts now

The first rule (every Standard/Glass instance in a form no stock level draws) counted **489** places on the club
(`q_club/DM05A_w`) and `apply` refused ('vertex chunk 46906 of mesh 46910 is also used by meshes [46909]'). The 489:
- 4 x `HeatShimmer` (the car fires, 4 entities of ONE mesh, material 1016 `Effects/Heat_Shimmer_01`, diffuse alpha 0)
  = the cars' fault; the club has 7 static cars (Bentleys, Taxi, Civilians) that name `Car_Fire_USA_Sedan_01_Cheap`.
- 480 x `Shard_N` / `Test02_undefined01` (shards of the dance-floor window `FX_0001_WindowA_SpecA01` and the stairs
  window `..._SpecB_02`; material 812 `Water_01a_NoScroll_M05`, ADD, group 0x46), 2 x `..._SpecB_N!Window` (material
  1020) and `..._SpecA01!Window_Glas01` (1077) (`Water_01a_Scroll_M05`, TRANS_ON_OPAQUE 0x41), 1 x
  `Whole_Railing_A` (812): Dead Men's own glass. The shared vertex chunk was the dance-floor window pane (46910) and
  its collision mesh (46909, material `_Glacier/Collision`).
The glass is not the cars' fault: its diffuse texture (`Water_01_M05`) has mean alpha 197 of 255, so the shader's
lerp (factor = diffuse alpha) draws the lit diffuse texture, not `refr * mask` with the missing mask. Live pictures
(`C9_club_wake_100s/220s/340s`, `C7_club_gates_botdown_250s`, `P3_DM05A_page3_100s`): the dance-floor window is a
pale frosted pane with a hard vertical edge, NO dark rectangle; near the tree behind it small white speckled
fragments with colour fringes hang in the air (possibly shards that stand drawn before the window breaks: seen, NOT
established, not touched here).
**Rule now** (`glass_forms`): a Standard/Glass instance in a form stock Dog Days lacks is a fault only when its
diffuse alpha is under `REFRACTION_LED` = 0.35 x 255 (or it has no readable diffuse); the rest is logged as 'glass
NOT counted'. Club: 1 mesh / 4 entities (the HeatShimmer); the six older maps give the same result lines as before
(DM01 1 place, DM02 1, DM03v 1, DM06 1, DM09x 5, DM03A_v2 3; all PASS).
**`apply` with a shared vertex chunk** (`_own_vertices`, not needed on the club once the rule is right; tested on the
pane 46910 without writing): the mesh gets its own sub-chunk -> descriptor -> vertex chunk (3 new table entries); the
other meshes keep the old ones; refcounts of the old chunks are left (ASSUMED harmless). Build
`q_club/DM05A_cfx`: one chunk changed (50691, the HeatShimmer's vertices), 0 added, only the .prm differs.
