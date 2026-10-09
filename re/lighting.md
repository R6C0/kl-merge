# Lighting: Dog Days, Dead Men, and the dark bank graft

2026-10-09, offline only (nothing was launched or installed). Tool: `tools/kl_light.py`.
Evidence levels used below: **[code]** read in the exe at the address given, **[data]** counted
over the stock levels (21 Dog Days, 20 Dead Men), **[inference]**, **[not established]**.

## Second pass (2026-10-09, later): the renderer read

Offline again. Read this time: the compiled effects in the `.fxc` (disassembled with
`d3dcompiler_47`, 5,176 shaders of the 242 distinct stock effects), Dead Men's shader SOURCE
(`Shaders/PC/FX/*.fx`, shipped inside every Dead Men level archive), and kl2.exe at the addresses
given. Live state before this pass: `normalise('stock')` lit the player (run L1); palm trunks
black, the bank grey and flat.

### What was found

1. **Materials without a compiled shader are not drawn** [code]. A material instance reaches its
   effects by name: kl2 `0x50bac0` (layer loader) -> `0x7113f0` builds the defines (mesh kind +
   the upper-cased name of every true BOOL except the six at `[0xcda50c]`: StdCulling,
   RimLightingEnabled, IlluminationEnabled, SubsurfaceEnabled, DiffuseIsSpecularMask,
   SpecMaskIsReflMask) -> `0x8b8fd0` walks the loaded cache and **returns 0 on a miss**; the
   loader then leaves the pass slot empty (`0x50c2ff`). Nothing is compiled at run time. The
   model reproduces stock exactly: 13,528 of 13,528 effects the materials of the 21 levels ask
   for are in the level's own `.fxc` [data]. Dead Men materials ask for combinations no Dog Days
   level ever used: **the installed bank build (run F1) has 35 such materials on 920 objects** -
   `Stone_Pillar_06a_M03` x468, `Stone_Pillar_04a_M03` x193, `Stone_Stucco_06a`, `Concrete_Wall_10a`,
   `Plaster_Tiles_01a` (all bump + specular + PARALLAX, a combination Dog Days only has with
   more switches), every Dead Men car body (weighted mesh + bump + specular + reflection), glasses,
   two civilians. Whole `M03_FA_A`: 52 of 671 materials, 1,024 uses; `M01_FA_A`: 31 of 778, 165.
   This is missing geometry, not darkness; it has been in every graft screenshot so far.
2. **Dead Men's baked lighting is an ambient-occlusion light map** [source + data]. Stream
   (descriptor [4]) = `vLightMapVertexColor` (COLOR6, D3DCOLOR; rgb ff ff ff on all 151,519
   vertices of the bank, alpha 0..255) + `vLightMapVertexCoords` (TEXCOORD2, 2 x u16). Record
   (descriptor [5]) = `.TEX` id of the light map + `v4LightMapColor`. The bank has six DXT1
   atlases (`M03FAA_OutsideFAA_01A` 1024 x 1024, `..._InsideFAA_Bank_Main` ...). Shader
   (`Common.fx`): `AO = lerp(v4LightMapColor.rgb, c.rgb, tex2D(samplerLightmap, uv).g * c.a)`;
   `Standard20/30.fx` and `Glow20.fx` multiply the diffuse texel and the reflection by it, for
   `MESH_STANDARD` only. Evaluated per vertex its mean on the bank is 0.59: Dead Men's bank was
   considerably DARKER in corners and under roofs than the graft shows it, and its post filter
   was tuned on top of that.
   **Dog Days cannot consume it** [code]: kl2.exe still has the vertex declarations with COLOR6 /
   TEXCOORD2 (`0xb98568`, `0xb985f8`, `0xb98658`; constructor `0x61ca80`) and the effects still
   declare `mapLightmap` / `v4LightMapColor`, but none of the 5,176 compiled shaders reads
   COLOR6, TEXCOORD2 or `samplerLightmap`, and there is no run-time compile.
   The `ZSHADOWMESHOBJ` '..._Additive_Light_Tex0' meshes are a different thing (projected
   static shadow / light textures, classes StaticShadow*; their four effects ARE in the union
   cache and resolve for every instance).
3. **Trunks** [data]. `Plant_PalmStem_01a_USA` (44 objects): Standard/Standard, bump + parallax,
   diffuse / normal / parallax textures all present, render group 0, surface Wood 13 -> 11; its
   permutation exists. Stock `Wood_F07_Tree_01a`: the same class and group, bump + specular.
   Vertex format is the same 40 bytes in both games (declaration `0xb98408` / Dead Men
   `0x93ffb8`). Mean vertex colour of the trunk meshes 210 / 255 (level mean 234; F07 225). So
   class, technique, textures and vertex format are NOT the cause. In WK1_142s the trunks are
   textured grey where the sun hits them; in L1 the camera looks into the sun and sees their
   unlit side. What is left is the unlit side itself: ambient only (see 4) under a neutral
   grade. **Not proven**; the picture after step 2 decides.
4. **The grey, flat look** [data]. What `M03_FA_A` has in Dead Men and the graft ships:
   - fog / far plane / background colour (`CameraFar` 50000, fog 0.1 .. 1.2, colour 0x505050):
     shipped (TAKE list). SSAO: Dead Men has none, F07's values (blur 2, strength 0.8) stay.
   - **post filter: not shipped.** The map has 13 `PostFilterBox` boxes (`Locations/M03_FA_A/
     M03FAA_Postfilter.zip`: Outside_LookAt x5, Outside_Dark x5, Inside x3) naming three filter
     sets; the first two carry their own colour curves (palette entries 0x2b..0x31). The box
     entities come along but the scene's `PostFilterBoxes` chunk is dropped, so the bank runs on
     the camera's neutral set. Stock F02 / F05 / F01 use the very same mechanism.
   - the AO light map (2): dropped by the converter.
   - sun and ambient: `Environment_env` c8bf99 x 1.3, ambient 505764 x 1.3 - the same order as
     F09's suns (ffe79f x 1.55, 283a34 x 1.55). Shipped.

### The palette and the sets [code + data]

`PostFilterPalettes` = one `.prm` chunk: u16 offsets (count = first / 2, kl2 `0x442779`), then
run-length coded 256-byte curves; the engine decodes the 37 curves of the active set into
37 x 256 bytes at `0x1536278` and keeps one byte per entry in a 0x8000-byte table, so the count
has no small limit. Entries 0..26 are byte-identical in all 41 levels of both games. A filter set
(176 bytes) = 25 floats + 37 u16 entry numbers at +0x64 (0xffff none) + one 0; no set of the 558
names an entry past its palette. So two levels' palettes can be joined by appending.

### Steps (each optional and separate; order = expected gain)

| # | step | call | what it changes on F07 + M03_FA_A | picture to take |
|---|---|---|---|---|
| 1 | `fit_shaders` | `kl_light.fit_shaders(mat, fxc, log=log)` before the archive members are made | 35 materials get a permutation the cache has: PARALLAX off x15, REFLECTION off x16, SPECULAR x2, ALPHAFADE x3 ... (920 objects appear) | the plaza from the spawn, as L1_125s / WK1_142s: walls and pillars that were holes; a parked Dead Men car (M01: the car park, M01c_130s view) |
| 2 | `graft_postfilter` | `kl_light.graft_postfilter(prm, S palette chunk, M palette bytes, M's set chunks, log=log)` + take `PostFilterBoxes` of a Dead Men M | palette 39 -> 53 curves, 15 sets, 4 renumbered; the three box sets work | same two views, and one indoors (the box changes at the bank door) |
| 3 | `bake_ao` | `kl_light.bake_ao(dm_prm, dd_prm, roots, dm_tex, strength=0.5, log=log)` in `kl_graft.DeadMen` | 2,250 meshes, 151,519 vertex colours x mean 0.59 (at strength 1), 2,009 vertex chunks cloned, +5.1 MB | under the escalators / the shop fronts of WK1_166s: corners and undersides should darken, open floor not |

Exact insertion points: end of the `tools/kl_light.py` docstring. Take step 3 only after 2 (it
darkens; Dead Men's grade was made for the darkened scene), and start with `strength=0.5`.

### Tests (`python tools/kl_light.py render-test`, `problems: 0`)

- 21 stock Dog Days levels: 13,528 needed effects all present; `fit_shaders` changes no byte.
- 41 stock levels: 2,149 curves pack back byte for byte; 558 sets in range.
- `M01_FA_A`, `M03_FA_A` converted, against F07's `.fxc` + `union.fxc`: after `fit_shaders` only
  the reported unresolved remain (`Items_Dynamic/MobilePhone_Front_01a`: Glow, rigid, opaque -
  the cache only has the blended form; `Glass_Grid_01b_M01`: no common subset of Glass.fx and
  Standard30.fx; 3 objects in all, they would need a switch turned ON), `.MAT` passes
  `kl_mat.check`; filter sets of S and of M see the same curves before and after the graft;
  `bake_ao` output passes `kl_prm.check`, changes nothing but bytes 16..18 of lit vertices,
  raises no colour, leaves unlit meshes alone, strength 0 = no change.
- The installed F1 build (`build\install\...\F01_Main.zip`): 35 materials / 920 uses without an
  effect -> 0 after `fit_shaders`, `kl_mat.check` passes.
- `python tools/kl_light.py test` still ends with `problems: 0`.

### ASSUMPTIONS / not established

- That a pass slot left empty simply draws nothing (the loader was read, the draw loop not; 13
  clean runs with such materials say it does not crash).
- `bake_ao`: that the CPU-side vertex lighting multiplies the AMBIENT term by the vertex colour
  as well (the shader takes ambient from stream 1, COLOR2, filled on the CPU; that code was not
  found). The dynamic-light pass does multiply by COLOR3 in the shader (`Lighting` vertex
  shader: `mul o0.xyz, c16, v2`). uv = u16 / 65536. Record colour = `v4LightMapColor`.
- `SWITCH_COST` (which feature to give up first) is my ranking.
- Why the unlit side of the trunks is black (3).

## Answer in short (first pass)

- The grafted bank (`F07` systems + `M03_FA_A`) is **not dark because of the dropped baked
  lighting**. The baked data is per-vertex ambient occlusion [inference]: it only darkened.
- Nothing is lost in the join: 0 lists and 0 room pairs of the map are dropped, the light
  classes have identical fields in both games [data + code].
- What the bank has and the good-looking `M01_FA_A` graft has not is an outdoor **environment
  setup no stock Dog Days level uses**: rooms paired with a *directional* environment that
  (a) is linked by name to a *non-directional* character light and (b) carries entity flag
  `0x10000` without `ZENVIRONMENT[2]`. Which of the two blacks out the characters is
  **[not established]** - the renderer was not read.
- Fix delivered: `kl_light.normalise()` rewrites exactly those cases into combinations stock
  Dog Days has (and empties `ZLIGHT[2]`, which Dog Days never uses). It changes nothing in any
  of the 21 stock levels. It has **not been seen in the game**.

## How a level describes light (both games)

| piece | where | notes |
|---|---|---|
| light entity | `.gms` / `.prp`, classes `ZOMNILIGHT` `ZSPOTLIGHT` `ZSPOTLIGHTSQUARE` `ZGateLight*` `ZENVIRONMENT` | fields identical in both games (only `ZGEOM` gains one bool in Dog Days) [data: schemas] |
| light record | `.prm` chunk named by `.gms` record +0x0c, lType 12, 48 / 64 / 80 bytes | below |
| light <-> geometry lists | `.gms` list pool (kl_scene) | built offline; none belongs to an environment (0 of 763) [data] |
| room -> environment | `.gms` room pairs, one per room | 797 pairs [data] |
| character light | **by name**, at run time | below [code] |
| post filter | scene block `PostFilterPalettes` / `PostFilterBoxes`, `PostFilter*` controllers | the graft keeps S's palette and drops Dead Men's boxes; not looked at here |

### Light record (`.prm`)

`+0x0c` type: low word 0 spot, 1 omni, 2 square spot, 3 ambient environment, 4 directional
environment; high word flag bits. `+0x10` colour `0x00RRGGBB`, `+0x14` intensity (float),
`+0x1c` colour 2, `+0x20` colour 3, `+0x24` byte "directional" (1 on every type 4 record, 0 on
every type 3 record: 763 of 763 [data]).

Two CPU-side readers (kl2 `0x8c9690`, `0x7bed90`) take a record through
`[[0xdda798]+0x18]` vtable +0x80 and use it so [code]:
not directional -> ambient += colour x intensity / 255;
directional -> light = colour x intensity along the entity's rotation, ambient += colour 3 x
intensity / 255. Colour 2 is not used there; its meaning is [not established].

### ZLIGHT / ZENVIRONMENT fields

| field | object | meaning |
|---|---|---|
| `ZLIGHT[0]` | +0x10 bit 4 | (kl2 getter `0x85e1a0`) |
| `ZLIGHT[1]` | +0x14 list | each resolved object is given to the light manager with the light (`0x46b7e0`); 105 Dog Days lights, 16 Dead Men [data] |
| `ZLIGHT[2]` | +0x1c list | setter `0x638bb0` keeps only objects of one class, null otherwise. Dead Men: the light's `ZSHADOWMESHOBJ` entities (202 of 5,364 lights). **Dog Days: empty on all 18,944 lights** [data] |
| `ZENVIRONMENT[0..3]` | +0x10 bits 0x1000, 0x4000, 0x8000, 0x2000 | same accessors in both exes (kl2 `0x42daa0` `0x55b510` `0x713aa0` `0x806810`; Dead Men `0x4f6f10`..) [code] |
| `ZENVIRONMENT[4..7]` | +0x28..+0x34 | colours; 0 = colour / colour 3 of the record (`0x5683d0`); always 0 in both games [data] |

### The character light is found by name [code]

`ZENVIRONMENT` init, kl2 `0x5683d0` (vtable slot 82), Dead Men `0x4f7170` (slot 83), same logic:

```
if this has bit 0x4000 or 0x8000: return            (it is itself a character light)
for each sibling ZENVIRONMENT named "*_env_character*":      (0x8dfa90: _memicmp, any case)
    if it has bit 0x4000: this+0x20 = it
    if it has bit 0x8000: this+0x24 = it
```

Who reads `+0x20` / `+0x24` was not found: 13 functions carry the ZENVIRONMENT type check
(global `0x15038c0`); the eight read here do not touch them - **[not established]**.

## Stock usage [data]

`python tools/kl_light.py survey <level>` prints a level; `catalogue` the table.

| paired environment | character light linked | Dog Days | Dead Men |
|---|---|---|---|
| type 3 | none | 54 | 25 |
| type 3 | type 4 | 246 (the campaign standard: ambient for the room, a directional light for characters) | 0 |
| type 3 | type 3 | 2 (F01, F02) | 13 |
| type 4 | none | 20 (F02, F05, F09 ...) | 8 |
| type 4 | type 4 | 11 | 0 |
| **type 4** | **type 3** | **0** | **3 (M03_A x2, M03_FA_A)** |
| itself a character light (bit 0x4000 / 0x8000), type 3 | - | 7 | 24 |
| itself a character light, type 4 | - | 13 (9 of them F09's street suns: bits 1011, entity flags 0x10080) | 12 |

Entity flag `0x10000` on a paired type 4 environment: Dog Days 9 of 44, and those 9 are exactly
the ones with bit 0x8000; Dead Men has it on suns that own static shadow meshes
(type 4 environments: `ZLIGHT[2]` not empty <=> flag, 18 of 18). So the flag does not mean the same thing in the two
games' data [inference]; what the Dog Days loader does with it was not read.

## The three grafts compared

Built into a scratch folder with `kl_graft.build` (never installed), verify 0 problems each.

| | F07 + F09 | F07 + M01_FA_A | F07 + M03_FA_A |
|---|---|---|---|
| looks | right | right | dark, characters and palms black |
| lists / pairs of M lost in the join | 0 / 0 | 0 / 0 | 0 / 0 |
| room pairs of the map | 42 | 10 | 18 |
| list elements (light->geometry + back) | - | 1321 + 2367 | 4096 + 6470 |
| lights with `ZLIGHT[2]` | 0 | 16 (44 refs) | 26 (90 refs) |
| meshes that lost baked data | 0 | **0** | 2250 |
| `ZAMBIENTOCCLUSION` objects | 0 | **0** | 6 |
| outdoor rooms are paired with | type 4 suns, no link | `Environment#Character`: **type 3**, bits 1111, flags 0x80, no link | `Environment_env`: **type 4**, bits 1001, **flags 0x10080**, 44 null `ZLIGHT[2]` entries, **linked to `Environment_env_character` (type 3)** |
| the sun | paired | `Environment#01` type 4: paired with **no** room | paired with 4 rooms |

M01's outdoors is therefore lit by a flat ambient light only (which is what the screenshot
shows: no sun shading, no shadows), and it has no baked meshes at all - it cannot tell us
whether the bake matters. The bank is the first Dead Men map through the graft that uses a sun.

Indoors both maps pair their rooms with type 3 lights (`*_characters`, bits 1101), a stock form.

## Dead Men's baked lighting

(First-pass notes. Superseded where they say "inference" or "not read": the shader source was
read in the second pass, see the top of this file. The stream is colour + light-map uv, the
record is a `.TEX` id + fade colour; the "colour that is mostly 0" below is the uv pair.)

- Mesh descriptor (32 bytes) `[4]` = stream of 8 bytes per vertex, `[5]` = shared 16-byte record;
  the mesh has draw-mode bit `0x01000000` (kl_prm / kl_prmgraph).
- Stream: `ff ff ff AA` + a colour dword that is mostly 0. Record: `{number, colour, 0, 0}`.
- Distinct records per level = number of `ZAMBIENTOCCLUSION` objects: M02_FA_A 6 / 6, M03_FA_A
  6 / 6, M09_A 4 / 4, M09_B 5 / 5; M01_FA_A none of either. Each such object lists rooms
  (`AmbientOcclusion!OutsideFAA_01A` -> room `M03_FAA_Outside_01A`).
- `ZAMBIENTOCCLUSION` overrides only the class-info slots 11-14 of `ZLIST` in both exes: it does
  nothing at run time.
- **[inference]** the stream is baked ambient occlusion (a factor <= 1 per vertex, plus an
  optional colour). The Dead Men shader that consumes it was not read.
- Can Dog Days use it? **No**: 0 of 94,851 Dog Days meshes have the bit, the 48-byte descriptor
  has no field for a second stream, and no Dog Days level has a `ZAMBIENTOCCLUSION`. Dog Days'
  only per-vertex colour data is the rare `inst` chunk at model root +0x3c (16 roots in F07, 0 in
  F09; Dead Men M01 has 6), a different mechanism (one chunk per model clone). Dog Days has
  screen-space AO instead (`SSAO_*` scene properties, taken from M by the graft).
- Loss: contact / corner darkening on 2250 meshes of the bank. Cosmetic.
- Not examined: the 128-byte static-shadow meshes (`ZSHADOWMESHOBJ`, 57 in M01_FA_A, 97 in
  M03_FA_A, some named `..._Chunk0_Additive_Light_Tex0`; F07 and F09 have none). Both exes hold
  the shader names `mapLightmap`, `v4LightMapColor`, `mapShadowColor`. After the retype to
  `ZSTDOBJ` they are drawn as ordinary objects; whether that is right is open.

## The fix: `kl_light.normalise`

| rule | what | stock backing |
|---|---|---|
| R1 | `ZLIGHT[2]` loses every reference that names no `ZSHADOWMESHOBJ` (empty strings, retyped objects: the setter stores null for them). `shadows='none'` empties the list, `'keep'` leaves it | stock: empty on 18,944 of 18,944 |
| R2 | paired type 4 environment, no character bit, entity flag 0x10000 -> set `ZENVIRONMENT[2]` | the form of F09's 9 street suns; with the bit it stops looking for a character light |
| R3 | paired type 4 environment without the flag, linked to a type 3 character light -> that light loses bits 0x4000 / 0x8000 | "type 4, no link" x20 |
| `links='m01'` | instead of R2 / R3: the rooms are paired with the character light | M01_FA_A's outdoor layout, the one seen to work in this pipeline (flat ambient, no sun) |

On `M03_FA_A`: R1 removes the sun's 44 empty references (the 46 that name a shadow mesh stay;
all 90 go if the shadow meshes are retyped to `ZSTDOBJ`, as they were when the dark screenshots
were taken), R2 turns `Environment_env` into bits 1011 (stock form x9); every environment of
the map is then in a stock combination. On `M01_FA_A`: R1 only (29 dead references on the sun,
15 kept); its unpaired sun stays as Dead Men has it.

NOTE on the moving ground: during this work `kl_gms.RETYPE` stopped retyping `ZSHADOWMESHOBJ`,
`ZPlant` and `ZEnvSampler`. With the class kept, Dead Men lights own a static-shadow-mesh list
again - something no stock Dog Days level exercises. If the next live run of the bank looks
wrong in a new way, try `shadows='none'`.

ASSUMPTIONS: that bit 0x8000 on the sun is harmless beyond the link rule (it is what F09 does);
that one of the two odd properties is the cause at all.

### Call in `kl_graft.build`

After the `Heroes!` block and before `gms, buf = A.write()`:

```python
import kl_light
kl_light.normalise(Jn, A, prm, nodes=set(mj.values()), log=log)
```

and in `verify()` on the re-read files (`sc` there is the kl_scene.Scene, `prm` the read .prm):

```python
bad += kl_light.check(Jn, sc, prm, nodes=set(mj.values()))
```

`Jn` joined kl_prpjoin.Scene, `A` joined kl_scene.Scene, `prm` joined kl_prmgraph.Prm (read
only). It edits `.prp` tokens of M's lights, and with `links='m01'` `A.pairs`. Options:
`links='stock' | 'm01' | 'keep'`, `shadows='valid' | 'none' | 'keep'`.

### Tests run (`python tools/kl_light.py test`, `problems: 0`)

- `STOCK` equals a fresh catalogue of the 21 levels (20 combinations, 630 environments).
- All 21 stock Dog Days levels: `normalise` leaves `.prp`, entity flags and pairs unchanged;
  `check(strict)` 0 problems (446 .. 1367 lights each).
- `M01_FA_A`, `M03_FA_A` through `kl_graft.DeadMen`, both modes: `check` 1 -> 0 and 3 -> 0
  (16 -> 0 and 28 -> 0 while the shadow meshes were still retyped);
  `.prp` and `.gms` / `.buf` written and re-read, `kl_scene.check` clean, same lights, pairs and
  environments after the re-read.
- The three scratch grafts (built before the retype change), whole level: `check` 28 -> 0
  (M03), 16 -> 0 (M01), 0 -> 0 (F09);
  0 class misfits in the whole `.prp` after the edit.

## Live test plan (one run each, in this order)

1. Default (`links='stock'`) on F07 + M03_FA_A. Expect lit characters and a sun.
2. If still dark: `links='m01'`. Reproduces M01's known-good layout; expect flat ambient light.
3. If run 1 is lit: `links='keep'` (R1 only) once, to learn whether the environment rules
   or the list mattered.
Whatever the outcome, it settles which property was the cause; write it here.

## Open

- Readers of environment +0x20 / +0x24 and of the room pair in the renderer; meaning of colour 2,
  of `ZENVIRONMENT[3]`, of entity flag 0x10000 in Dog Days.
- `PostFilterBoxes` of Dead Men are left out by the graft (they index Dead Men's palette); M01
  and M03 both have them (18 and 13 `PostFilterBox` controllers), so they do not explain the
  difference, but the maps lose their per-area grading.
- `ZEnvSampler` is still retyped to `ZSTDOBJ` (none in M01_FA_A / M03_FA_A's light setup was
  looked at here; see re/cars.md).
- Static shadow meshes (above).
