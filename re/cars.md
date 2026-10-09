# Dead Men classes kept as themselves (ZHavokCar and the rest of kl_gms.RETYPE)

Track `b-cars`, 2026-10-09. Static work only: both executables, `re/kaneandlynch.json` / `re/kl2.json`,
all 20 Dead Men and 21 Dog Days stock levels. **Nothing here ran in the game.** "ASSUMPTION" / "not
established" mark what is not proven. Code: `tools/kl_retype.py` (`table`, `test`).

## Result

| class (type id) | verdict | what it needs beyond "do not retype" | risk |
|---|---|---|---|
| ZIngameMapGroup 0x100486 | **must stay retyped** (-> ZROOM) | nothing new | none new: kl2.exe does not register it (the only Dead Men geometry class it lacks) |
| ZFFItemTemplateMultistage 0x100490 | **keep** | nothing | low. One per level (`...equipment.zip\Equipment\Claymore`), always in Dead Men's systems subtree, so a graft never carries it; it matters for whole-level builds only |
| ZSHADOWMESHOBJ 0x200110 | **keep** | nothing | low / medium: no Dog Days level has one |
| ZEnvSampler 0x20010f | **keep** | nothing in the .prp; see the note on material slots | low / medium: no Dog Days level has one |
| ZPlant 0x2000fd | **keep** | ZCloth's new float[3] = (0, 0, 0); sound handle ZCloth[10] zeroed; chunk indices ZCloth[15] / ZPlant[2] renumbered (kl_prmgraph already does) | medium: Dog Days levels use ZCloth (694) but no ZPlant and no HavokDeformation |
| ZHavokCar 0x2000d4 | **keep** | sound handle ZHavokCar[2] zeroed; animation set (ZLNKOBJ[2]) must exist in the shipped .ANM or be emptied; its .HVK type 3 shapes must come along with the right REF id (kl_hvk.join does) | medium / high: 164 Dead Men cars, 0 in Dog Days levels. The code is all there, but retail Dog Days never ran it |

`python tools/kl_retype.py test`: the six maps (M01/M02/M03/M06 FA, M09_A, M09_B) converted with the
five classes kept -> `problems: 0`. Kept objects: 30 ZHavokCar, 99 ZPlant, 494 ZSHADOWMESHOBJ,
8 ZEnvSampler, 6 ZFFItemTemplateMultistage (table under "Test").

## Why they were retyped

`git log -- tools/kl_gms.py`: the table is from the first commit (a2887b0, 2026-10-08), with the
comment "classes Dog Days still has but never saves in a level (layout unknown)". At that time the
converter learned layouts from level files, and no Dog Days level stores one of these five classes
(counted again here: 0 objects of each in all 21 levels), so there was nothing to learn from.
Since `kl_rtp.py` the layout comes from the exe; CLAUDE.md then kept them "pending pool categories
and room/portal data". Both are settled and neither concerns these classes:

- pool category (`kl_gms.category`): each class has the category of what it was retyped to (0 for
  the item template, 1 for the other four), so keeping it moves no entity to another pool and no
  slot id changes against today's builds. The group bit is unchanged too (cluster blocks).
- rooms / portals only concern ZROOM (kept since 99f20d6 / 3bcd15e) and ZIngameMapGroup.

So no reason is left. The retype was not harmless either: see "What the retype broke".

## Evidence per class

### Registered, and the same fields (all five)
`python tools/kl_retype.py table`. Every one is in kl2.exe's class registry under the same type id
and name, with the same base chain. The class's OWN stored fields are identical in type, order and
enum in both games (ZHavokCar 13, ZPlant 3, ZEnvSampler 7, ZSHADOWMESHOBJ 2, Multistage 4); the
enums involved (EVehicleType 10 values, UPDATE_FREQUENCY, ActorCollisionType, MovementType,
ITEMHANDS, ITEMSIZE, EBoundingBox) have the same options and values. What differs sits in base
classes every converted object already goes through:

| base level | Dead Men | Dog Days | new field |
|---|---|---|---|
| ZGEOM | e f\*9 f\*3 b I | e f\*9 f\*3 b I **b** | ZGEOM[5], Dog Days' usual value (as for every node today) |
| ZItemTemplate | e e b I b | e e b **s** I b | ZItemTemplate[3], as for every item template today |
| ZCloth | I f I f f f b e e b I I refs refs I | ... I I **f\*3** refs refs I | ZCloth[12], see ZPlant |
| ZLNKOBJ, ZSTDOBJ, ZGROUP | same | same | - |

Each of these alignments is unique (the Dead Men list is the Dog Days list with fields left out in
exactly one way), so nothing is an "assumed pairing"; `kl_retype.expected()` derives the pairing
without kl_convert and the test compares the two and then every value.

### The code is alive in kl2.exe
- Overridden vtable slots against the base class, both exes (slot numbers shift by one, sizes in
  instructions): the same set of overrides with bodies of comparable size. ZHavokCar 24 slots
  (Dead Men 23), e.g. init 0x798d50 (206), 0x72d530 (653; Dead Men 624), 0x427410 (249; 284).
  ZPlant 8 / 8, ZEnvSampler 8 / 8, ZSHADOWMESHOBJ 9 / 9, Multistage 8 / 8. No override is a stub.
- Code sites that use the class's run-time type id (the global its slot 12 returns):
  ZHavokCar 123 sites in 46 functions (Dead Men 125 / 47), ZPlant 9 / 5 (9 / 5), ZEnvSampler 14 / 7
  (14 / 7), ZSHADOWMESHOBJ 10 / 5 (12 / 6), Multistage 9 / 5 (9 / 5). Whoever asks "is this a
  ZHavokCar" in Dead Men still asks in Dog Days.

### ZHavokCar
A Dead Men car (all 164 have this shape; example M01_FA_A `ROOT\AI_Enemies!FrontMall_02\Bentley_02`):

```
Bentley_02 [ZGROUP]            @VehicleEffects (+ ZVehicleChaseEffects / OnlineEscHavokCar ... on some)
  Ground_01 [ZHavokCar]        @HavokCarScriptRout (+ @VehicleWeapon on 33 of 164)   .HVK type 3, convex
  WheelLeftFront .. WheelRightRear [ZSTDOBJ]                                         .HVK type 4, convex
  Left_Front_Door, Right_Front_Door [ZGROUP > ZSTDOBJ], Window* [ZGROUP > ZSTDOBJ]   .HVK type 4
  BackLeft, BackRight, FrontLeft, FrontRight [ZSTDOBJ]   @PassengerAnimPos ('/Vehicles/Police_USA/Back_Left' ...)
  CoverBox*, V_Coli_Shot_01, V_Coli_Hero_01 [ZSTDOBJ]
```

- **The list at car +0x96c..+0x970 is not a wheel list.** It is the car's weapon list: 8-byte
  entries appended by 0x84b7d0, whose only caller is ZVehicleWeapon slot 14 (0x59d38e), i.e. the
  `VehicleWeapon` controller on the car. The constructor (0x428eb0, stamps vtable 0xbcb00c) zeroes
  begin / end / capacity (0x429088..0x429094). HavokCarScriptRout (ZHavokCarScript slot 2,
  0x58a7b0) walks it for a weapon that is not in use (byte +0x1a6) to start a
  ZVehicleFireWeaponTask. On a real ZHavokCar without VehicleWeapon the list is empty and the loop
  is skipped (0x58a7ee). The crash at 0x58a7fc was the same walk over whatever lies 0x96c bytes
  behind a 0x20-byte ZSTDOBJ.
- **Wheels are found by name, by VehicleEffects, not by the car.** ZVehicleEffects init (slot 13,
  0x7c6f00) walks the group's children for a ZHavokCar (kept at effects +0xb94) or a ZHeli
  (+0xb98), then 0x727a00 looks the children up by the names at 0xcf03d4: `WheelLeftFront`,
  `WheelRightFront`, `WheelLeftRear`, `WheelRightRear`, then `ExtraWheel...` pairs, and hangs a
  `VehicleEffectsWheelListener` on each (0x4cd0e0); 0x467f80 does the same for `Left_Front_Door`,
  `Right_Front_Door`, `Left_Rear_Door`, `Right_Rear_Door`, `Trunk` (table 0xcf03c0). The names are
  entity names from the .buf, which the converter and the graft keep. All 30 cars of the six maps
  have the four wheel entities as siblings and a VehicleEffects on the parent group.
- **Physics.** ZHavokCar init (slot 83, 0x798d50) -> 0x88cff0 -> 0x72e160:
  1. `0x5d11b0(EVehicleType)` returns the vehicle's parameter block from a map filled by a
     10-case switch (jump table 0x5d1800), one case per EVehicleType value. Suspension, wheel
     positions, engine: all constants in the exe, none from level data.
  2. `0x86ad30` collects every .HVK **type 3** shape whose placement REF id resolves
     (handle table [REF-1], 0x8ccde0) to the car itself. That is the chassis. One shape for 133 of
     the 164 Dead Men cars, 4 / 5 / 9 for the rest (compound bodies), never none.
  3. With no shape it returns without building anything (0x72e25f -> 0x72e5ea).
  ZHeli goes the same way (slot 83 0x566960 -> 0x47a8a0 -> 0x86ad30), and Dog Days levels do use
  ZHeli (21 objects, 42 type 3 placements): the shape list, the handle table and the ZHavokLnkObj
  base are exercised by retail levels; the car-specific part is not.
- **.HVK**: nothing to convert. Type 3 records are only stored by the reader (0x49d660) and the
  format is the same (re/havok.md). `kl_hvk.join` keeps a map level's type 3 shapes and renumbers
  their REF ids; the cars are map-side entities (AI_Enemies!, CivilianCars!, Escape! ...).
  The chassis sub-part's surface index is 0 in the one car dumped (M01 Bentley_02); not surveyed.
- **Fields that point outside the .prp**: ZHavokCar[2] (type handler 46, a .SND offset: 86624,
  244336 ... in Dead Men's bank) and ZLNKOBJ[1] (handler 70; 0 on all cars). `kl_graft` zeroes
  both handler types on every map node already; a whole-level build must do it too
  (`kl_retype.finish`). ZLNKOBJ[2] is the animation set: `Police_USA`, `Generic`, `Van` (FA maps),
  `Police_Japan`, `Swat_Van`, `Van` (M09_B). It is the set of the car's passengers (the
  PassengerAnimPos clips are `/Vehicles/<set>/<seat>`). As a ZSTDOBJ the car had no such field;
  kept, it names a set, and `kl_package.ANIM_SETS` has no entry for `Police_Japan` / `Swat_Van`
  and `None` for `Van`. Either the animation join supplies them or `kl_retype.finish(have=...)`
  empties the name. ASSUMPTION that an empty set is harmless: one Dead Men car (M03_B) and all 21
  Dog Days ZHeli have ''.
- **Controllers on it**: HavokCarScriptRout (ZHavokCarScriptRout, 5 fields b e b b b, identical;
  owner ZHavokCar) and VehicleWeapon (13 fields, identical; owner ZHavokCar; none in the six maps).
  With the class kept both have their owner among the node's bases, so the stopgap in
  `kl_graft.DeadMen` no longer removes anything from cars.
- **What a Dog Days level has instead.** No Dog Days level contains a ZHavokCar or a driving ground
  vehicle. F01's escape vans are animated props: `EscapeVehicle_Animation_F01 [ZGROUP]
  @OnlineEscAnimatedVehicle` with `Body_Main` / doors as ZSTDOBJ + `MatPosAnim` +
  `RelayAnimatedVehicleHit` and .HVK types 1 and 4. Its helicopters are the nearest relative:
  `V_Police_Helicopter_01 [ZGROUP] @OnlineEscHavokCar @OnlineEscVehicleController @VehicleEffects`
  with the child `V_Coli_Shot_01 [ZHeli] @HeliWeapon @HeliScriptRout`: the same group + VehicleEffects +
  ZHavokLnkObj child with a type 3 shape, ZLNKOBJ = 0 | 0 | ''. So the frame a car sits in is what
  Dog Days ships; the ZHavokCar class inside it is not.

### ZPlant (ZCloth > ZSTDOBJ)
- Code compared instruction by instruction, kl2 against kaneandlynch: ZPlant init (0x7cfa20 /
  0x58df40), its message handler (0x816e60 / 0x58dee0), its simulation step (0x7ab5c0 / 0x58e120)
  and ZCloth's set-up (0x84f220 / 0x58c990) are the same routines; only member offsets moved (+0xc
  to +0x14, the new ZCloth field) and Dead Men's `int3` asserts are gone.
- The plant blob (.prm chunk named by ZPlant[2]) is read with the same stride and offsets in both:
  `u32 n`, then n x 16 bytes `{u16 a, u16 b, u16 c, u16, f32, f32}`, a / b / c = particle numbers
  of the cloth blob (ZCloth[15], Dead Men ZCloth[14]). The test checks size and index range on all
  99 plants. The cloth blob has the same header shape in both games (`0 0 1 n a 0 b 0 n` + floats);
  its parser was NOT compared (not established), only the routines that use the parsed arrays.
- `kl_prmgraph.PRP_FIELDS` / `PRP_GAME` already know ZPlant[2] and ZCloth[15] / [14], so the Dead
  Men walk keeps both chunks and the graft renumbers them once the node IS a ZPlant. Retyped to
  ZSTDOBJ the fields were dropped and nothing named the chunks. In `build\FA\<map>\*.prm`
  (kl_dmassets output) all 99 + 99 chunks are byte-identical to Dead Men's and at the same index.
- **ZCloth[12]** (Dog Days only, float[3]): Dog Days' ZCloth init 0x552ff0 sets a flag at +0xfc
  when the vector's squared length exceeds a constant; Dead Men's init (0x58d330) has no such step.
  kl_convert would write Dog Days' most common value, (0, 0, 8). `kl_retype.LEVEL_MAPS['ZCloth']`
  writes (0, 0, 0). ASSUMPTION: zero = Dead Men's behaviour (124 of 694 stock cloths store zero);
  what the vector does was not read. This also changes plain Dead Men ZCloth objects (1 in
  M03_FA_A, 3 in M06_FA_A / M09_A).
- ZCloth[10] / [11] are sound handles (handler 70): 232864, 193104 ... on every plant -> zero.
- ZCloth[0] / [2] (plain integers, handler 81): Dead Men plants 1 and 2..7, Dog Days cloths
  1..20 and 1..5. Left as they are; meaning not read (iteration counts by their range).
- Controller: `HavokDeformation` on all 99 (owner ZCloth; ZHavokDeformation, 2 bools, identical).
  **No stock Dog Days cloth carries any controller**, so this controller is unexercised in retail
  although registered; its init (slot 14, 0x905550) still tests for ZPlant.

### ZSHADOWMESHOBJ (ZSTDOBJ)
Names like `Light0_..._Chunk0_Additive_Light_Tex0`: the additive light meshes of a room. Fields:
[0] an entity handle (0 in all 494), [1] a scene path (the room or zone it belongs to, or '').
Its init (slot 82, 0x4acb10) only resolves [0] and does NOT run ZSTDOBJ's init (0x66bec0), and its
slot 31 returns 1 where ZSTDOBJ returns 0 (as ZAMBIENTOCCLUSION does). So the engine treats it
differently from a plain mesh; as ZSTDOBJ it went through the ordinary path. What slot 31 gates
was not read. The path in [1] is inside the map and survives a graft's renaming like any other
scene path.

### ZEnvSampler (ZSTDOBJ)
Fields: [0] slot 0..3, [1] a range (1000 / 5000 / 100000), [2] 0, [3] 1, [4] 0, [5] UF_ONCE,
[6] bool. Init (0x7a4150 / 0x4f3d40) computes a bounding box from the node's matrix in both
games; the copy routine (0x8f4970) copies the same seven members. The slot range 0..3 matches the
"engine texture slots" 0x80000000..3 of Dead Men materials that `kl_mat.py` rewrites to slot 0
(10 materials in M02_FA_A) on the guess that they are sampled environment cubes: this is the
other half of that guess. With the samplers alive, slots 1..3 could be kept in the .MAT instead -
not established that Dog Days' renderer still serves slots 1..3; not changed here.

### ZFFItemTemplateMultistage (ZItemTemplate > ZGROUP)
Slot 149 returns the class id 0x10048f in both exes. Its `InventoryBinding` (owner
ZItemTemplate) is legitimate only while the node is an item template; as a ZGROUP the graft's
stopgap had to remove it. It binds `eFF2ItemClaymore` -> `eFF2ItemNoItem` (kl_convert.ITEM_RENAME),
which may be bound any number of times.

### ZIngameMapGroup
Not in kl2.exe's registry (an unregistered type id crashes the loader at 0x46fe87 / 0x8add12).
ZROOM is its base, it adds no stored field, and it sits in Dead Men's HUD (`FFOsdMP1.zip`), which
a graft drops. No change.

## What the retype broke (found on the way)
- VehicleEffects looks for a ZHavokCar or ZHeli child (0x7c6f27 / 0x7c6f5c). With the car a
  ZSTDOBJ it finds neither and keeps running without a vehicle (effects +0xb94 = 0); what its
  update does then was not followed.
- PassengerAnimPos init (0x6c19d0) and the .HVK type 4 handler (0x59d600) test for ZHavokCar too.
- HavokDeformation (owner ZCloth) sat on 99 plants that were ZSTDOBJ: the whole-level converter
  kept it (kl_rtp `controller()` falls back to the only implementation when no owner fits); the
  graft's stopgap now removes it together with HavokCarScriptRout. Neither is needed once the
  classes are kept.
- A ZSTDOBJ with flags & 0x200000 == 0 and no raw data is "plain": the loader gives it no object
  at all (kl_scene, kl2 0x8adb82). A retyped car / plant / sampler could fall under that rule; as
  its own class it always gets its object.

## The change (for the owners of kl_gms / kl_convert / kl_graft; I edited none of them)
1. `tools/kl_gms.py`: `RETYPE = {0x100486: 0x100021}` - delete the five lines 0x100490, 0x200110,
   0x2000fd, 0x20010f, 0x2000d4 and the "never saves in a level (layout unknown)" comment.
   Nothing else in the file changes (`retype`, `category`, `rebuild_clusters` are class-agnostic).
   kl_convert, kl_graft, kl_package, verify_levels all read this one dict.
2. `tools/kl_convert.py`: add to `LEVEL_MAPS` the entry `kl_retype.LEVEL_MAPS['ZCloth']`
   (`'map': {0..11: same, 13: 12, 14: 13, 15: 14}, 'values': {12: [array of three 0.0]}`), or
   `LEVEL_MAPS.update(kl_retype.LEVEL_MAPS)`. The cache `dd_typical.json` rebuilds itself (the set
   of wanted fields grows by the kept classes' enums).
3. `tools/kl_graft.py` `DeadMen.__init__`: nothing to add. The block that cuts controllers of
   retyped nodes becomes a no-op for cars and plants (it only looks at nodes whose class
   changed) and should stay for ZIngameMapGroup. Its sound pass (handlers 46 / 70 on map nodes)
   already covers ZHavokCar[2] and ZCloth[10]; its chunk renumbering (kl_prmgraph.prp_roots)
   already covers ZPlant[2] / ZCloth[15]. New to it: the animation sets `Van`, `Swat_Van`,
   `Police_Japan` named by cars - give them stand-ins / join the clips, or call
   `kl_retype.finish(prp, tids, schema, have=<set names of the shipped .ANM>)`.
4. `tools/kl_package.py` (whole-level build): after `kl_convert.convert_level`, call
   `kl_retype.finish(Prp(data), dd_tids, dd)` to zero the sound handles; same animation-set note.
5. Until 1 and 2 are in, `with kl_retype.applied():` gives the same result without editing the
   files (it swaps the dict's content and restores it); `kl_retype.convert()` = convert_level +
   finish.
6. Pre-flight: `python tools/kl_retype.py test` -> `problems: 0`, next to verify_levels.

Expected in the first live run with cars kept (not tried): the five M01 cars become simulated
Havok vehicles driven by HavokCarScriptRout + the VehicleMove* behaviours on their squads. If it
crashes inside vehicle code, the cheap bisect is to put only 0x2000d4 back into RETYPE; the four
other classes are independent of it.

## Test
`python tools/kl_retype.py test` (about 1 min; reads the six Dead Men archives, writes nothing but
its own cache `<work>/dd_typical_retype.json`). Per map, with the classes kept:
- `verify_levels.problems`: every node and controller fits its Dog Days class (Schema.misfit),
  every enum value exists, every controller is registered, no item bound twice;
- every kept object is its own class, and each field comes from the Dead Men field that
  `expected()` derives independently of kl_convert, with the same value (except sound handles);
- every controller on a kept object has its registered owner among the object's bases;
- ZHavokCar: at least one .HVK type 3 shape on its REF id; wheels / VehicleEffects counted;
- ZPlant: both chunk indices are still followed by kl_prmgraph on the converted file, the plant
  blob parses and names only particles the cloth blob has, and (if kl_dmassets output exists) the
  converted .prm holds both blobs unchanged.
Two mutations were tried: swapping ZCloth's two lists in the pairing is reported (20 problems on
M02_FA_A); putting ZHavokCar back into RETYPE makes `convert()` refuse.

| map | ZHavokCar | ZPlant | ZSHADOWMESHOBJ | ZEnvSampler | Multistage | controllers on them | sound handles zeroed | problems |
|---|---|---|---|---|---|---|---|---|
| M01_FA_A | 5 (type 3 shapes: 1,1,1,1,4) | 0 | 57 | 0 | 1 | 5 HavokCarScriptRout, 1 InventoryBinding | 3 | 0 |
| M02_FA_A | 2 | 10 | 188 | 7 (slots 0,1,2,3) | 1 | 2 + 10 HavokDeformation + 1 | 12 | 0 |
| M03_FA_A | 6 | 44 | 97 | 0 | 1 | 6 + 44 + 1 | 50 | 0 |
| M06_FA_A | 0 | 45 | 0 | 0 | 1 | 45 + 1 | 45 | 0 |
| M09_A | 0 | 0 | 98 | 1 | 1 | 1 | 0 | 0 |
| M09_B | 17 | 0 | 54 | 0 | 1 | 17 + 1 | 17 | 0 |

Counted but not a problem: `GatePath` (owner ZGROUP) on a ZBoxPrimitive, 2 / 9 / 8 nodes in M02 /
M09_A / M09_B - an owner mismatch that is in the Dead Men source and has nothing to do with the
kept classes (the engine does not enforce owners).

## Not established
- Anything about run-time behaviour: no build with kept classes was made or launched.
- The cloth blob parser (only its consumers were compared); what ZCloth[12], ZCloth[0] / [2] mean.
- What ZSHADOWMESHOBJ slot 31 gates and how Dog Days' renderer draws such a mesh (Dead Men's
  baked-light data is dropped by kl_prm; these meshes may need it).
- Whether Dog Days' renderer still fills environment slots 1..3 from ZEnvSampler objects.
- VehicleEffects' own pairing guesses (re/pairings.md: DM3 -> DD3, DM14 -> DD21) now matter more,
  because the effects object finally has a car to act on.
- Cars need drivers' clips (`/Vehicles/<set>/...`) from the animation join; without them the
  enter / exit behaviours have nothing to play.
