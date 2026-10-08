# .HVK - the level's physics file (Dead Men and Dog Days)

Track `track-hvk`, 2026-10-09. Static analysis of both executables plus every stock level
(21 Dog Days: F01..F09 with F01 from `KL_PortBackup`, L00..L11; 20 Dead Men: all `*_Main.zip`).
Nothing here was tried in the running game. "ASSUMPTION" / "not established" mark what is not proven.

## Summary

1. Both games link the same Havok: the string `Havok-4.6.1-r1` is in kl2.exe (file offset 0x7e6100)
   and kaneandlynch.exe (0x5cfef0). RTTI: 183 `hk*` classes in Dog Days, 173 in Dead Men, none with
   the later `hkp` prefix; Dog Days' 10 extra are all debug display (`hkDisplayBox` ...).
2. The .HVK is not a Havok packfile. It is IO Interactive's own container with two sections:
   collision shapes with their placements, then precompiled MOPP bounding-volume code. The
   layout is **the same in both games**: one parser, written from Dog Days' reader, walks all 41
   files to the last byte and writes them back byte-identical.
3. Shapes are tied to scene entities by **REF id** (.gms record +0x30), nothing else.
4. A Dead Men .HVK is read by Dog Days as it is - not ignored, not partially read. No wrapper
   conversion is needed. What differs is semantic: surface indices, a shape type Dead Men lacks,
   and classes the converter retypes (below).
5. The .HVK holds no rigid-body dynamics, constraints or ragdolls: every byte is accounted for by
   shapes, placements, sub-part tables and MOPP code. Mass, hinges and so on are node/controller
   properties in the .prp (ZHavokRigidBody, `ZHavokRigidBody_ZHingeConstraint` ...).
6. The table at `[0xdd2598]+0x10` is **not filled from the .HVK**. It is `ZBoneExtendPool`, filled
   from an `FDX` block in the .buf that the .gms header points to at +0x38. `kl_gms.convert` sets
   +0x38 to -1, which is why the table was empty. See "The ZPhysicsBasedAnimated crash".
7. Graft: take the map level's .HVK whole, drop its systems shapes, add the systems level's
   (types 4 and 5 only: 61 placements in F01, F02 and F04), renumber REF ids. The MOPP section
   stays the map's, byte for byte. Tested in memory (F02 map + F01 systems). Code below.

## How kl2.exe loads it

| site | what |
|---|---|
| 0x42fd40 | ZEngineDataBase vtable slot 46 (+0xb8): size of `<level>.HVK` (extension string at 0xb4b130) |
| 0x5914f0 | slot 47 (+0xbc): read the file into a buffer |
| 0x8204b3..0x8204fe | scene loader 0x820300: allocates, reads, keeps pointer / size at database +0x1164 / +0x1168 |
| 0x8ade95..0x8adecc | entity loader, after the entities exist: `0x41ee80(ptr, size)` on the physics wrapper (database +0x52cc) stores them at wrapper +0x166a4 / +0x166ac and in the stream object at +0x166b4; read cursor +0x166a8 = 0; then `0x6204b0(handle table, count, 0)` |
| 0x6204b0 | builds the physics world. Copies the REF-indexed handle table to wrapper +0x1669c (count +0x166a0); 0x87b310 -> 0x8de150 reads the two header vectors for the world size; 0x495070 reads every shape; then one list shape + MOPP per 510 static children |
| 0x495070 | reads `count`, `section 1 end` (kept at wrapper +0x166b0), sets the cursor to 0x20, loops `count` times: 0x593840 reads one record, then a jump table at 0x495340 on the record type |
| 0x593840 | the record reader (all layout facts below are from it) |
| 0x5dd590 | reads one MOPP record at `section 1 end + [wrapper+0x1470]`, builds an `hkMoppCode` (vtable 0xbb05c4), advances the cursor to the next multiple of 16 of the **absolute** file offset |
| 0x7e37b0 / 0x477600 / 0x7d1e80 | stream helpers: u32, float, n bytes at cursor |

Type dispatch (0x495340, index type-1):

| type | handler | what it does | entity classes seen (all 21 levels) |
|---|---|---|---|
| 1 | 0x4de4b0 -> 0x4acd90 | static collision: per placement a world-space `hkMeshShape` (12 sub-part bits) + its MOPP read by 0x5dd590; appended to the static list at wrapper +0x14e0; the record's flags go to the array at +0x14f0 | ZSTDOBJ 87,738, ZCloth 34, ZHavokRigidBody 14 |
| 2 | 0x650b40 | rigid body: entity = table[REF-1], skipped if null; sets the entity's matrix from the placement and creates the body (0x76dca0) | ZHavokRigidBody 564 |
| 3 | 0x49d660 | only stored (list at wrapper +0x14c4) for whoever asks later | ZHeli 42 |
| 4 | 0x76c0e0 -> 0x59d600 | key-framed body on an entity (table[REF-1], skipped if null); walks the parents for a `VehicleEffects` / `ZVehicleGetAwayEffects` controller (layer 0x13 then, else 2) | ZSTDOBJ 3,387 |
| 5 | 0x462cc0 | only stored (list at wrapper +0x14d0) | ZSTDOBJ 612, every one named `ColiObj_Gun` |

Dead Men's reader is 0x59dcb0 (found from the `PrintHavokMeshes` string) -> 0x59f850, jump table
0x59debc with **four** entries; a type above 4 is an `int3`. Its handlers: 1 0x59dc00, 2 0x59d080,
3 0x59ca70, 4 0x59d1c0. Differences seen between the two readers:
- Dead Men asserts (`int3`) on vertex / index counts >= 50,000, vertex stride outside 12..16, index
  stride > 8, and on a REF id >= the table count (0x59d1f7). **Dog Days has none of these checks**:
  a REF id beyond the table reads past it (0x76c11d, 0x650b91).
- Dog Days adds type 5 (treated like type 3 when the collision layer is chosen, 0x593cf1..0x593d39).
- Everything else that touches the stream is the same sequence of reads.

## File layout (both games)

All little-endian, no alignment inside section 1.

```
0x00  u32  shape record count
0x04  u32  end of section 1 = start of section 2 (file offset; not aligned)
0x08  f32 x3  world box minimum
0x14  f32 x3  world box maximum
0x20  shape records
....  section 2: MOPP records
....  16 zero bytes (all 41 files)
```

The box feeds the Havok world's size (0x87b310). It equals the bounding box of all static
geometry in 31 of 41 files (within 0.01); in the other 10 it is larger on one side (F04, F05, F09,
L07, M01FAA, M03B, M08A, M11B, M13B, M14A). What else it covers: not established.

### Shape record

```
u32 type            1..5 (table above)
u32 placements      count of 0x38-byte placement records
u32 sub-parts       count of 12-byte sub-part records
u32 flags           collision flags of the whole shape
u32 convex          0 = triangle mesh, else convex hull

mesh:    u32 vertices, u32 indices, u32 vertex stride (always 12), u32 index stride (always 6)
         vertices * 12 bytes   f32 x,y,z, in the shape's own space
         indices * 2 bytes     u16, three per triangle
convex:  u32 vertices, u32 vertex stride (always 16), u32 planes
         vertices * 16 bytes   f32 x,y,z,0
         planes * 16 bytes     f32 plane equation (hkConvexVerticesShape, built at 0x9d04c0)

placements * 0x38:  f32 x3 position, f32 x9 rotation (row-major), u32 REF id, u32 flag
sub-parts * 12:     u32 surface index, u32 collision flags, u32 primitive count
```

- Placement: world = position + R * v with `R[3*a+j]`. Proven on static shapes: for 121,266 of
  121,395 placements (both games) the MOPP offset equals that world minimum minus 0.01 to 1e-3;
  128 are within 0.05, one (M11A `SO0101_M11_InsWalls_01`) is 0.24 off.
- REF id: all 92,391 Dog Days and 44,688 Dead Men placements name an existing entity's REF id.
  The same REF id is used twice 21 / 126 times.
- Placement flag (last dword): 0 except on type 3 (Dog Days 18 of 42 are 1) and Dead Men type 4
  (1 on exactly the 7,994 convex ones). Meaning not established.
- Sub-part: for a mesh, the primitive counts sum to the triangle count (all 42,663 mesh shapes).
  For a convex shape the count's meaning is not established.
- A mesh of type 4 becomes a `ZDynMeshShape` (vtable 0xbb0648, 0xe0 bytes), any other mesh an
  `hkMeshShape` (0xc0 bytes).
- Collision filter word, built at 0x4e2700 (Dead Men 0x5a03a0, same arithmetic):
  `(arg << 16) | (layer << 10) | flags`, layer 6 for types 1 and 2, 2 for type 4, 3 for types 3
  and 5. Flags use bits 1,2,3,4,5,6,8 in both games with the same common values (0x72, 0x172,
  0x66, 0x102, 0x108 ...). Dead Men asserts flags < 0x400.
- Surface index is stored next to the filter word in the mesh's sub-part table (0x593d4d).
  Dog Days uses 0..24 (19 distinct), Dead Men 0..30 (26 distinct). ASSUMPTION: it indexes the
  surface table in the .buf at gms header +0x30: dword +0x18 of that block is 0x18 in F01 and F02
  and 0x1f in M01FAA and M06FAA, which fits the ranges. The consumer was not traced.

Type usage: Dog Days 15,317 shape records, Dead Men 31,929. Dead Men has no type 5. Dead Men type 3 is ZHavokCar (290, named `Ground_01`) and ZHeli (12);
Dog Days levels contain no ZHavokCar at all. Dead Men type 4 is mostly **convex** (7,994 of
9,455 placements); Dog Days type 4 is never convex in stock files, but its handler does test the
convex flag and has a path for it (0x59d76e).

### Section 2: MOPP records

```
f32 x4   hkMoppCode offset (x, y, z, scale)
u32      code size
bytes    MOPP byte code
pad      0xCD up to the next multiple of 16 of the file offset
```

Order: one record per **static (type 1) placement**, in file order (shape records in order,
placements in order), then one record per list of up to 510 static placements. Count =
static placements + ceil(static placements / 510) in all 41 files (87,967 and 33,686 codes).
The 510 is `0x1fe` at kl2 0x620760 and kaneandlynch 0x59e56b. Types 2 to 5 have no code in the file.

Consequences:
- A static placement's code depends only on that placement's world-space triangles. It can move
  inside the file with its placement. It is invalid if the placement's transform changes.
- A list code addresses its children by position in the 510-block (ASSUMPTION: standard
  hkListShape child index as MOPP terminal; the code was not interpreted). So the **sequence** of
  static placements must not change, unless the list codes are rebuilt.
- A child that no list code returns is never tested. That is what makes padding possible.

## What happens with a Dead Men file in Dog Days

Read fully and used: same container, same Havok, same mesh construction (12 sub-part bits and
a radius variable holding 0.05 in both images: kl2 0x4ad310 / 0xd47e70, kaneandlynch 0x59d7ee /
0xa85568), same 510 blocks, and the stored codes sit 0.01 outside the geometry in both games. So the static
collision and its MOPP codes are usable as they are. Open points, most likely first:

1. **Retyped classes.** `kl_gms.RETYPE` turns ZHavokCar into ZSTDOBJ. Type 3 shapes are only
   stored, so they become inert; the type 4 placements of the cars' parts (wheels, doors) still
   attach to their entities. Not a crash by this reading, but the cars have no body. Not tested.
2. **Surface indices** are Dead Men's numbering (0..30) against Dog Days' table (0..24) if the
   surface table comes from the Dog Days systems level: wrong impact effects / sounds, and an
   index above 24 may read past a table. The mapping is not established (neither executable has
   surface names).
3. **REF ids** must be exactly the converted level's. Dog Days does not bounds-check them.
4. Type 4 convex shapes: supported by code, never exercised by a stock Dog Days level.

## The ZPhysicsBasedAnimated crash (0x5daf70)

`[0xdd2598]` is the `ZBoneExtendPool` singleton (vtable 0xbaf79c, registered at 0xae78c0 with the
name string, constructed at 0x736150: +0x10 array, +0x14 u16 count). The array of 0x5c-byte entries
is allocated by 0x4dd4d0, called only from 0x7a68b0, called only from the scene loader at 0x820ae0
with `.buf base + gms header[+0x38]` when that dword is not -1.

Block at that offset: `'F','D','X'`, version byte (must be 4 in Dog Days; 4 in every file of both
games), u16 bone-pool count, u16 vertex-pool count (0 everywhere), 10 bytes not read (constant per
game: `f4 00 78 02 9e 5f 4e 00 00 cd` Dead Men, `a4 cc bd 03 ae 90 59 00 00 cd` Dog Days), then one
record per pool (reader 0x428d20: u8 kind, u8, u16 n, n entries via 0x515c40 / 0x69fee0, u32,
f32, then 0x71ae80).

The `PhysicsBasedAnimated` controller's last two properties are u16 pool index (+0x58) and u16
entry (+0x5a). Evidence that this is the link: the levels with an FDX block are exactly the levels
with such controllers (Dog Days F04, L00..L05; Dead Men M01A, M01FAA, M02FAA, M06A, M06FAA,
M08A, M09A - 7 of 21 and 7 of 20), and every controller's pool index is below the block's pool
count (315 controllers checked: 268 Dog Days, 47 Dead Men).

CLAUDE.md says "+0x38 = -1" and kl_gms.py "Dog Days levels use -1 here"; that is true for F01..F03
only. The Dead Men block is still in the converted .buf; only the pointer was cleared.

Proposal (not tested): keep header +0x38 pointing at the Dead Men block and keep the controller.
Dead Men's readers (0x586f40, 0x586ec0, 0x5865f0, 0x5867f0, 0x5869f0) accept version 4 and make
the same number of stream reads of the same widths as Dog Days' (instruction streams compared,
differences are register choice only). Record-level compatibility was not proven by a parser.

Graft: all these controllers and the block sit on the map side (`Locations/...` subtree in F04,
M01FAA, M06FAA). One map: take the map's block, no renumbering. Two maps that both have one
(M09A has 1 pool): the blocks must be merged and the second map's pool indices shifted - needs
the record layout decoded first.

## Joining two levels' .HVK (graft)

Which shapes belong to which side, by the top-level subtree of the placement's entity:

| level | subtree | placements by type |
|---|---|---|
| F01, F02, F04 | `AllLevels/mainsceneincludes_multiplayer.zip` (systems) | 4: 10, 5: 51 - identical in the three |
| F01 | `Locations/F01/...` | 1: 1710, 2: 19, 4: 80 |
| F01 | `Animation/F01/Escape_Vehicle_0x.zip` (three) | 1: 2, 4: 10 each |
| F02 | `Locations/F02/...` | 1: 785, 2: 15, 4: 74; three helicopters 3: 1 each |
| M01FAA, M02FAA, M03FAA, M06FAA | `Locations/...` | every static placement and every type 2 |
| M01FAA | AI_Enemies!, CivilianCars!, DropMoney! ... | types 3 and 4 only |
| M09A / M09B | `Locations/...` plus a cut-scene subtree with 2 static each | |

So the systems side never owns static collision. Rules:

1. Base = the map level's file. Its static placements stay in file order, its section 2 is
   copied unchanged.
2. Drop the map level's own systems shapes (types 4 / 5), add the systems level's. No MOPP involved.
3. Renumber every placement's REF id (+0x30 of the placement) to the joined scene's REF ids. This
   is the only id in the file. Surface indices follow whichever level supplies the surface table.
4. A static placement whose entity is dropped (cut-scene geometry, say) must keep its slot:
   replace it with a copy of another static placement and that one's code. The list code still
   returns the slot for the old volume, the child there now reports no contact.
5. Two maps in one level (Retomoto A + B): pad the first map's static placements to a multiple of
   510 with copies of one of its placements, then append the second map. Each map keeps its list
   codes; the padding is never returned by any of them. ASSUMPTION as under section 2.
6. Header box = union of the maps' boxes.
7. None of this survives **moving** a map in world space: placements, static codes and list codes
   are all world-space. Then every code must be rebuilt (next section).

### Rebuilding MOPP code (only if a map must be moved or re-cut) - not tested

Dog Days still contains the builder: with the third argument of 0x6204b0 non-zero, 0x4ad449 and
0x620818 call 0x9d5460 (ASSUMPTION: `hkMoppUtility::buildCode`, by its arguments and its place
opposite the file read) instead of reading the file, then call
0x68ac30, which in retail is `int3; ret 4` (bytes `cc c2 04 00`) - the stripped "save" step. The
argument is `push 0` at 0x8adeb8, but setting it also skips creating the `ZSafetyNetPhantom`
(0x620a16), so it is not a play mode. A KLHook experiment would instead patch, in memory:
0x4ad3d6 (`0f 84 8c 00 00 00` -> six `90`), 0x62080b (`74 1f` -> `90 90`) and 0x68ac30 (`cc` ->
`90`, or a hook that appends offset / size / bytes from the `hkMoppCode` at +0x10 / +0x24 / +0x20
to a file, which regenerates section 2 exactly). Static reading only.

## Proposed module (`tools/kl_hvk.py`)

Tested from the scratch folder; results under "Validation".

```python
"""
.HVK physics file, same layout in Dead Men and Dog Days (re/havok.md; reader kl2 0x495070 /
0x593840 / 0x5dd590). Section 1: shape records, each with its placements (transform + REF id of
the entity) and sub-parts. Section 2: one MOPP code per static placement in file order, then
one per 510 static placements. Both games link Havok 4.6.1, so codes are interchangeable.
"""
import struct

CHUNK = 510          # children per static list shape (kl2 0x620760: cmp edx, 0x1fe)
STATIC, RIGID, VEHICLE, KEYFRAMED, WEAPON = 1, 2, 3, 4, 5


class Shape:
    """One shape record. inst = [0x38-byte placement: position x3, rotation 3x3, REF id, flag],
    sub = [(surface index, collision flags, primitive count)], mopp = one (offset, code) per
    placement of a STATIC shape, else []."""
    def clone(self, inst, mopp):
        s = Shape(); s.__dict__.update(self.__dict__); s.inst, s.mopp = list(inst), list(mopp)
        return s


class Hvk:
    def __init__(self, d):
        n, size = struct.unpack_from('<II', d, 0)
        self.box = struct.unpack_from('<6f', d, 8)
        self.shapes, p = [], 0x20
        for _ in range(n):
            s = Shape()
            s.type, ni, ns, s.flags, s.convex = struct.unpack_from('<5I', d, p); p += 20
            if s.convex:
                nv, s.vstride, npl = struct.unpack_from('<3I', d, p); p += 12
            else:
                nv, nidx, s.vstride, s.istride = struct.unpack_from('<4I', d, p); p += 16
            s.verts = d[p:p + (s.vstride >> 2) * nv * 4]; p += len(s.verts)
            if s.convex:
                s.planes = d[p:p + 16 * npl]; p += 16 * npl
            else:
                s.idx = d[p:p + 2 * nidx]; p += 2 * nidx
            s.inst = [d[p + 0x38 * i:p + 0x38 * i + 0x38] for i in range(ni)]; p += 0x38 * ni
            s.sub = [struct.unpack_from('<3I', d, p + 12 * i) for i in range(ns)]; p += 12 * ns
            s.mopp = []
            self.shapes.append(s)
        if p != size:
            raise ValueError('shape section ends at %#x, header says %#x' % (p, size))
        codes = []
        while p + 20 <= len(d) and d[p:p + 20] != bytes(20):
            k = struct.unpack_from('<I', d, p + 16)[0]
            codes.append((d[p:p + 16], d[p + 20:p + 20 + k]))
            p = (p + 20 + k + 15) & ~15
        self.tail = d[p:]
        static = [s for s in self.shapes if s.type == STATIC]
        n1 = sum(len(s.inst) for s in static)
        if len(codes) != n1 + -(-n1 // CHUNK):
            raise ValueError('%d MOPP codes for %d static placements' % (len(codes), n1))
        it = iter(codes)
        for s in static:
            s.mopp = [next(it) for _ in s.inst]
        self.lists = list(it)               # one per CHUNK static placements, in file order

    def serialize(self):
        out = bytearray(0x20)
        for s in self.shapes:
            out += struct.pack('<5I', s.type, len(s.inst), len(s.sub), s.flags, s.convex)
            nv = len(s.verts) // s.vstride
            if s.convex:
                out += struct.pack('<3I', nv, s.vstride, len(s.planes) // 16) + s.verts + s.planes
            else:
                out += struct.pack('<4I', nv, len(s.idx) // 2, s.vstride, s.istride) + s.verts + s.idx
            out += b''.join(s.inst)
            for x in s.sub:
                out += struct.pack('<3I', *x)
        struct.pack_into('<II6f', out, 0, len(self.shapes), len(out), *self.box)
        for off, code in [m for s in self.shapes for m in s.mopp] + self.lists:
            out += off + struct.pack('<I', len(code)) + code
            out += b'\xcd' * (-len(out) & 15)
        return bytes(out + self.tail)

    def static_count(self):
        return sum(len(s.inst) for s in self.shapes if s.type == STATIC)


def ref(inst):
    return struct.unpack_from('<I', inst, 0x30)[0]


def renumber(inst, refs):
    return inst[:0x30] + struct.pack('<I', refs[ref(inst)]) + inst[0x34:]


def remap(hvk, refs, filler=None):
    """Shapes of `hvk` with REF ids renumbered through `refs` (old -> new); a placement whose
    REF id is missing is dropped. With `filler` (a map: a (shape, placement, code) of a kept static
    placement) a dropped STATIC placement is replaced by it instead, because the list codes address
    static placements by position: the list code never returns the filler where it now lies."""
    out = []
    for s in hvk.shapes:
        keep = [k for k, i in enumerate(s.inst) if ref(i) in refs]
        if s.type != STATIC or filler is None:
            if keep:
                out.append(s.clone([renumber(s.inst[k], refs) for k in keep],
                                   [s.mopp[k] for k in keep] if s.mopp else []))
        elif len(keep) == len(s.inst):
            out.append(s.clone([renumber(i, refs) for i in s.inst], s.mopp))
        else:
            for k, i in enumerate(s.inst):          # one record per placement keeps the order
                if k in keep:
                    out.append(s.clone([renumber(i, refs)], [s.mopp[k]]))
                else:
                    out.append(filler[0].clone([filler[1]], [filler[2]]))
    return out


def first_static(shapes, refs=None):
    for s in shapes:
        if s.type == STATIC:
            for i, m in zip(s.inst, s.mopp):
                if refs is None or ref(i) in refs:
                    return s, (renumber(i, refs) if refs else i), m


def join(maps, systems, box=None):
    """maps: [(Hvk, refs)], systems: (Hvk, refs) or None; refs = {old REF id: new REF id} of the
    entities that survive. Every map keeps its static placements in file order and its own list
    codes; each map but the last is padded to a multiple of CHUNK static placements with copies of
    one of its own, which no list code refers to. The systems level must not contribute static
    placements (none does in stock levels)."""
    out = Hvk.__new__(Hvk); out.shapes, out.lists, out.tail = [], [], maps[0][0].tail
    for n, (h, refs) in enumerate(maps):
        fill = first_static(h.shapes, refs)
        out.shapes += remap(h, refs, fill)
        pad = -h.static_count() % CHUNK if n < len(maps) - 1 else 0
        if pad:
            out.shapes.append(fill[0].clone([fill[1]] * pad, [fill[2]] * pad))
        out.lists += h.lists
    if systems:
        extra = remap(*systems)
        if any(s.type == STATIC for s in extra):
            raise ValueError('systems level contributes static collision')
        out.shapes += extra
    lo = [min(h.box[k] for h, _ in maps) for k in range(3)]
    hi = [max(h.box[k] for h, _ in maps) for k in range(3, 6)]
    out.box = tuple(box or lo + hi)
    return out
```

Top-level subtree of each entity (to build `refs`), from the entity table's first dword
(`>> 25` = levels closed before this entity, bit 0x1000000 = has children; the rule
`kl_gms.rebuild_clusters` already uses):

```python
def tops(names, decls):
    stack, out, pending = [], [], None
    for name, d in zip(names, decls):
        del stack[len(stack) - (d >> 25):]
        if pending is not None:
            stack.append(pending); pending = None
        out.append(stack[0] if stack else name)
        if d & 0x1000000:
            pending = name
    return out
```

## Validation

| check | Dog Days | Dead Men |
|---|---|---|
| files parsed to the last byte and serialized byte-identical | 21 / 21 | 20 / 20 |
| shape records / placements | 15,317 / 92,391 | 31,929 / 44,688 |
| MOPP codes = static placements + ceil(/510) | 21 / 21 (87,967 codes) | 20 / 20 (33,686) |
| 16 zero bytes after the last code | 21 / 21 | 20 / 20 |
| placement REF id is an entity's REF id | 92,391 / 92,391 | 44,688 / 44,688 |
| static code offset = placement's world minimum - 0.01 (1e-3) | 87,676 / 87,786 | 33,590 / 33,609 |
| mesh: sub-part counts sum to the triangle count | 14,736 / 14,736 | 27,927 / 27,927 |
| header box = static geometry's box (0.01) | 19 / 21 min, 19 / 21 max | 14 / 20 min, 19 / 20 max |
| levels with `PhysicsBasedAnimated` = levels with an FDX block | 7 = 7 | 7 = 7 |

Join, in memory only:
- `join([(F02, identity)], None)` is byte-identical to stock F02.
- F02 map + F01 systems (F02's 61 systems placements dropped, F01's 61 added with other REF ids):
  356 records, placements by type 785 / 15 / 3 / 84 / 51 as in F02, section 2 byte-identical to
  F02's, output re-parses and round-trips.
- F02 + F05 as two maps: 785 + 235 padding + 2006 static placements, second map starts at slot
  1020 (a multiple of 510), 2 + 4 list codes.
- One static placement dropped from F02: count stays 785, 2 list codes, the REF id is gone.

## Not established

- Whether a grafted or Dead Men .HVK loads and collides correctly in the game (nothing was run).
- MOPP terminals of list codes = child index in the 510-block (the padding and filler rules rest
  on it).
- Surface index target and the Dead Men -> Dog Days surface mapping.
- The placement flag dword and the convex sub-part count.
- What widens the header box in 10 files.
- FDX record layout; whether Dead Men's block is accepted by Dog Days record for record.
- Who consumes the stored type 3 and type 5 shapes (lists at wrapper +0x14c4 / +0x14d0) and what
  happens when the REF id's entity has another class than expected.
