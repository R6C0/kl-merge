# Glacier 1 level animation file (`.ANM`): Dead Men (DM, 2007) and Dog Days (DD, 2010)

Status: reverse-engineered from `kaneandlynch.exe` (DM) and `kl2.exe` (DD); both are 32-bit, base
0x400000. Every layout below was checked against all four samples (`dd.anm` = F03, `L01.anm`,
`dm.anm` = M01A, `dm_M02A.anm`). `anm_lib.py` parses all four and writes them back byte-identical.
`test_codec.py` decodes every key stream of every clip in them.

Tags used below:
- **[code]**: read from the exe disassembly (addresses given).
- **[data]**: holds for every instance in the four samples, but no code reading it was found.
- **[unknown]**: meaning not determined.

All integers are little-endian u32 unless stated otherwise. Floats are IEEE single.

---------------------------------------------------------------------------------------------------

## 0. The short answer: what differs between DM and DD

| # | Item | DM | DD | Consequence |
|---|------|----|----|-------------|
| 1 | Clip record size in the type-4 chunk | 0x50 bytes (20 u32) | 0x68 bytes (26 u32) | DD reads a DM file with a 0x68 stride, so every offset is garbage. This is the crash. **This is the only structural difference.** [code] DM 0x5be690 (`imul 0x50`), DD 0x7079f0 (`imul 0x68`) |
| 2 | Clip record fields 12..19 | A(3f) P(3f) f(1f) namePtr | A(3f) **A_end(3f)** P(3f) **P_end(3f)** f(1f) namePtr | DD added end-of-clip copies of the two "pose vectors". [code] DM 0x5c4b30, DD 0x8b4200 |
| 3 | Clip flag 0x1000 | never set | set exactly when A/P/A_end/P_end are valid (non-zero) | DD only blends pose vectors of clips with 0x1000 set. DM blends A/P of every active clip. [code] DD 0x8b427d, 0x8b42bf |
| 4 | Event-table offset when a clip has 0 events | 0 | points at a fixed dummy (0xaa74 in F03) | Harmless, because the count is 0. [data] |
| 5 | Bone-name table (C) | differs per level | differs per level | Entries 0..60 are identical in all four files, and the engine hard-codes indices in this range (GROUND = 57, the mirror table 0..0x42). Later entries differ, so a converted clip's bone indices must be remapped **by name**. [code]+[data] |
| 6 | Morph-channel table (E) | 37 names (adds `Pose`) | 36 names | Remap by name. [data] |
| 7 | Event type ids | uses 1, 13-19, 21, 24, 30, 37, 38 | never uses those (other ids match) | 675 of 708 same-named clips have identical events. The DM-only ids have unknown meaning in DD. [data] |
| 8 | DB condition bits | bits 0-2 weight, plus 3,4,6,7,8,11,12,13 | keys also use 17,18,19,20 (not 7). DD's weapon code also sets 16, 17, 20 and 22 | Same field (actor+0x84) and same weapon-class mapping for the shared bits. [code] DM 0x5e8ad0, DD 0x50d7c0 |
| 9 | ZEngineDataBase vtable slot of LoadAnm | +0xe0 | +0xe8 | Exe only, not file format. |

**Identical in both games:** the chunk container, types 5, 6 and 7, the type-4 header, the
C/D/E/F blocks, the track-block layout, the IdxT key-index streams, the rotation codec, the
position keys, the morph channels, variant selection and DB/name lookup. Evidence:
- The decoders were compared instruction by instruction:
  - DM 0x5bdbd0 ≡ DD 0x6663b0
  - DM 0x5bdd30 ≡ DD 0x834170. The only differences are register allocation.
- For the 708 clips present in both F03 and M01A under the same `anim:` name:
  - 93 % of bone rotations decode to identical quaternions;
  - 97 % of positions are bit-identical.

The earlier reading that "the DB payload layout differs" was wrong. DM's Lynch_Coop DB begins with
the conditional list `(0x100,3)(0x10,2)(8,1)(0,0)`. DD's Kane DB happens to begin with unconditional
one-entry lists `(0,n)`. The format is the same.

---------------------------------------------------------------------------------------------------

## 1. Loading (where the file comes from)

- **File name:** `<scene>.anm` (string "anm"; DM 0x93bb0c, DD 0xb7b84c).
  - DM: `ZEngineDataBase::vt+0xdc` returns the size (0x456950); `vt+0xe0` reads the file into a new buffer (0x456a00).
  - DD: the same pair is `vt+0xe4` (0x6635a0) and `vt+0xe8` (0x713610).
  - The caller stores the buffer at `ZEngineDataBase+0x24` and the size at `+0x28`: DM 0x459767..0x459794, DD 0x8205a1..0x8205ce.
- **The buffer is used in place.**
  - Some runtime pointers are stored as offsets from this buffer: DD 0x89f290 (offset→pointer) and 0x574910 / 0x819630 (pointer→offset).
  - So the whole file stays resident. A merged file of ~29 MB is resident too.
- **The engine reads only three child types of the root:**
  - type 4 (`find_child(root,4)`: DM 0x459bb2, DD 0x820a1b);
  - type 6 (scanned by name, §4);
  - type 7 (§5).
  - No code compares a chunk type with 5.
- **No magic or version check:** neither exe tests `MNA`, and no CRC or hash is involved anywhere.

## 2. Chunk container

```
u32 type
u32 sizeflags      bit31 = has children, bit30 = has array header, bits0-29 = total size incl. this header
if bit31:
    u32 dataOffset     (from chunk start; data runs to the end of the chunk)
    u32 childCount
    if bit30: u32 n, u32 extra[n]
    children (each a chunk, back to back; next = cur + (sizeflags & 0x3fffffff))
    data
else:
    payload at +8, length size-8
```
- [code] `find_child`: DM 0x4318e0, DD 0x74f710.
- [code] Element count: DM 0x431930, DD 0x81a050. It returns `[+0xc]` for 0x4000_0000 chunks, `[+0x10]` for 0xC000_0000 chunks, and 1 otherwise. Data-pointer and data-size are computed inline (DM 0x459be9, DD 0x820a52).
- Only flag values 0x80000000 (root and type 5) and 0 (all others) occur in ANM files.

**Root:**
```
u32 0x00414E4D ('MNA\0'), u32 0x80000000|fileSize, u32 fileSize (= dataOffset, no data), u32 childCount
children: (type5, type6) x nDB,  type7,  type4
```
- childCount = 2·nDB + 2 (68 in F03, 46 in M01A).

## 3. Type 5: the "new clips" list of a database [data]

```
u32 5, u32 0x80000000|total, u32 dataOffset (= 16 + 8 + 4N), u32 1 (childCount)
  child: u32 N (the child's "type" field holds the element count), u32 8+4N, u32 clipIndex[N]
data: resource name, NUL-terminated, zero-padded to 4  (e.g. "anmcol:animationdatabase#Kane")
```
- The list is the sorted set of clip indices that the next type-6 DB references and that no
  earlier DB in the file references. This holds for every DB in all four files.
- Clip indices are therefore numbered in order of first use. Kane's clips are 0..1742, Lynch's new
  clips 1743..1891, and so on.
- Not read by the game. `anm_lib` recomputes it on write.

## 4. Type 6: animation database [code]

Plain chunk. Payload (offsets relative to the payload):

```
name          cstr padded to 4   "anmcol:animationdatabase#<Name>"   (same string as the type-5 data)
base:  u32 nLists
       variant lists, back to back. Each list = (u32 key, u32 clipIndex)*, terminated by an entry with key == 0
       u32 reserved (always 0)
       u32 nIds
       u32 listOffset[nIds]    byte offset of the list relative to `base`; 0xFFFFFFFF = DB has no entry
```
- Code: holder init DD 0x864750 (base pointer, then skips the lists and the reserved dword to reach the index); lookup DD 0x876940.
- `nIds` = the highest name id the DB uses, plus 1.
- Lists appear in arbitrary order. They are never shared in the samples.

**DB lookup by name:** DM 0x524360, DD 0x824d00.
- The requested name first passes through `[gameMgr]->vt+0xa8` (DM) or `vt+0xa4` (DD). [unknown] What this transform does.
- The engine then scans the root's type-6 children in file order.
- It returns the first DB whose payload name **ends with** the requested string, compared case-insensitively. DD 0x80b970 calls `_stricmp` on the tail; DM uses 0x431bc0.
- The result points just after the padded name, at `nLists`.
- **Consequence:** a DB named X is shadowed by any *earlier* DB whose name ends in X. For example, `Police` placed after `HG_Revolver_Police` is never found. `anm_lib.AnmFile.add_db` orders new DBs to avoid this.

**Path to clip (per actor):**
1. `nameId` = binary search of the path in the type-7 table (§5). These ids are cached by
   systems at start-up, e.g. the DD movement-name registration at 0x579920.
2. `list` = `base + listOffset[nameId]` (DD 0x876940; id < nIds is checked).
3. Variant selection (DD 0x7c6750, DM 0x429090, the same algorithm). `mask` = the actor's state flags `actor+0x84`.
   - Walk the list.
   - An entry qualifies if `(key & ~7) ⊆ mask`.
   - The first qualifying entry fixes the "group" `key & ~7`. Only later entries with the same group join it.
   - Each candidate has weight 1.0. It becomes 0.1 if `key & 4`, then is ×0.33 if `key & 2` and ×0.5 if `key & 1`.
   - One candidate is chosen with the random number `r`. The LCG at gameMgr+0xb30 is `x = x*0x10dcd+1` and `r = ((x>>8)&0x7fff)/32768` (DD 0x59d550).
   - The terminator's clip (key 0) is also returned as a second "default" clip: DD 0x5c2f60 returns the pair (chosen, default).
4. The clip index becomes a record pointer:
   - DD 0x48bc90: `recs + i*0x68`
   - DM 0x5be550: `recs + i*0x50`

**Condition bits:** the mask is the actor flag word at +0x84, the same field in both games.
- The weapon class bits are set by DM 0x5e8ad0 and DD 0x50d7c0:

  | Weapon | Bit set |
  |---|---|
  | none | 0x10 |
  | type 6 | 0x800 (DD: 0x400000 when weapon+0x1d8 is set) |
  | type 7 | 0x100 |
  | types 8, 10-13 | 0x10 |
  | type 14 | 0x200 |
  | type 9 / other | 0x8, unless subtype 2 |

- DD only:

  | Condition | Bit set |
  |---|---|
  | type 16 | 0x10000 |
  | type 17 | 0x20000 |
  | special state actor+0x2d48 | 0x100000 |

- Other bits (0x40, 0x80, 0x1000, 0x2000, …) are set from many places in both exes. [unknown] Their individual meaning.
- Bits used in DB keys:
  - DM: 3,4,6,7,8,11,12,13
  - DD: 3,4,6,8,11,12,13,17,18,19,20
- A DM key with a bit DD never sets simply never qualifies. The list then falls through to later entries; the key-0 terminator always qualifies.
- Bit 7 (0x80) appears only in DM keys (31 entries). DD code does set 0x80 on actors (DD 0x49d8c0, 0x555873, 0x6d3062). [unknown] Whether it means the same thing as in DM.

## 5. Type 7: animation path names [code]

```
u32 n
n x { u32 strOffset, u32 nameId }   sorted by the string, unsigned byte compare (strcmp)
string block: names in nameId order, each NUL-terminated and zero-padded to 4; strOffset is relative to the block
```
- Found by DM 0x429370 and DD 0x534ea0 (scans root children for type 7).
- Binary search in DD 0x68a730. It is exact and **case-sensitive**, and returns the id as u16.
- Ids are later treated as signed 16-bit (DD 0x5c2f60, 0x876940), so at most 32767 names.
- The paths look like `/Movement/Run/Forward` and `/Level_Specific/M01_A/Intro/Sc1_Kane`. Several
  DM paths differ from DD only in case (e.g. `MG_Minimi_SPW` vs `MG_MiniMi_SPW`). They are distinct names.

## 6. Type 4: clips [code]

Plain chunk. The payload is loaded by DM 0x5be640 (ctor) + 0x5be690, and DD 0x404aa0 + 0x7079f0.
The manager object is global: DM 0xc85134, DD 0x1546f6c. It is also stored at ZEngineDataBase+0x14.

```
u32 hdr[13]
   0 N  (clip count)
   1 |B|  2 |C|  3 |D|  4 |E|  5 |F| (0)
   6 #C (bone names)
   7 #D (= N, clip names)
   8 #E (morph-channel names)
   9 #F (0)
   10, 11, 12  [unknown]: copied to mgr+0x5c, +0x20, +0x24; no reader found in either exe
ClipRecord[N]          0x50 (DM) / 0x68 (DD) bytes each
B   clip data blobs
C   bone names, NUL-separated, block zero-padded to 4
D   clip names "anim:<Path>#<Name>", NUL-separated, padded to 4. D[i] belongs to clip i;
    the loader stores &D[i] into record +0x4c (DM) / +0x64 (DD)
E   morph-channel names (facial: "L Blink", …, "Push"; DM adds "Pose")
F   empty
```
- The chunk size satisfies `8 + 52 + N·recSize + Σ|B..F|` exactly.
- `anm_lib` uses this to tell the variants apart.

### 6.1 Clip record

| u32 | DM | DD | Meaning |
|---|---|---|---|
| 0 | ✓ | ✓ | lo u16: [unknown] (0..1607, equal in DM/DD for the same clip). hi u16: frame count. [code] DM 0x5bfa77 `movsx [clip+2]` |
| 1 | ✓ | ✓ | lo u16: fps (25; a few 24). hi s16: event count. [code] DD 0x4a75ed |
| 2 | ✓ | ✓ | flags: 0x1 loop (DD 0x8b42cc uses start vectors only); 0x10 baked-matrix block (§6.4); 0x1000 DD pose vectors valid; 0x800 alternative blend path (DD 0x8b4289); 0x8/0x40/0x80 [unknown] |
| 3 | ✓ | ✓ | track-block offset in B. [code] DM 0x5bfb6f, DD 0x5a5148 |
| 4 | ✓ | ✓ | event-table offset in B. [code] DD 0x4a75dc |
| 5 | ✓ | ✓ | float, 0..10, usually integral. [unknown] |
| 6-8 | ✓ | ✓ | vec3: total GROUND displacement (last minus first position key of the GROUND track). [data] Holds for every clip whose first track is GROUND |
| 9 | ✓ | ✓ | blob size in B (events + track block). 0 = alias clip (§6.2) |
| 10 | ✓ | ✓ | 0 / 8 / 24. [unknown] |
| 11 | ✓ | ✓ | [unknown] (equal in DM/DD for the same clip) |
| 12-14 | A | A | unit vec3 "pose vector" at clip start |
| 15-17 | P | A_end | DM: vec3 P at start. DD: A at clip end |
| 18 | f | P | DM: float (~96.7). DD: P at start |
| 19 | namePtr | (P) | DM: runtime name pointer (0 in file) |
| 21-23 | – | P_end | DD: P at clip end |
| 24 | – | f | DD: float (~96.7) |
| 25 | – | namePtr | DD: runtime name pointer (0 in file) |

- Duration = frames / fps.
- **Pose vectors A and P:**
  - DM 0x5c4b30 forms a weight-blended sum of A and of P over the 16 active animation slots (stride 0x38).
  - DD 0x8b4200 does the same, but only for clips with flag 0x1000. It lerps start→end by
    normalised clip time; looping clips use the start values only.
  - [unknown] The physical meaning. They look like an aim/facing direction (unit) and a body point, in GROUND space.
  - 994 F03 clips have no 0x1000 flag and all-zero vectors.

### 6.2 B: blobs, sharing and aliases [data]

- B is the exact concatenation of *owner* blobs (clips with size ≠ 0).
  - In each owner blob the events (8 bytes each) are immediately followed by the track block.
  - There are no gaps and no overlaps.
- Clips with size 0 (F03 1553, M01A 137) are aliases. Their track-block offset equals an owner's,
  and their events lie inside that owner blob. A converter must copy the owner blob.
- All offsets inside a track block are relative to the block start `p`, so blobs are freely relocatable.
- **Event** = `u32 type, u16 frame, s16 -1`. DD 0x4a75d0 finds the n-th event of a given type.

### 6.3 Track block (flag 0x10 clear)

```
p+0x00  5 x u32 0
p+0x14  float duration (s)
p+0x18  u32 frame count
p+0x1c  u32 nTracks
p+0x20  u32 nChannels  (morph)
p+0x24  nTracks x { u32 rotIdxOff, u32 rotDataOff, u32 posIdxOff, u32 posDataOff, u32 bone }
        nChannels x { u32 idxOff, u32 valueOff, u32 channel }      (channel = index into E)
        36 zero bytes
        streams: all rot IdxT, then all pos IdxT, then all rot data, then all pos data, then morph data;
        each group padded to 4
```
- `bone` = index into C. GROUND (57) is the first track whenever the clip has root motion.
  DM 0x5bfb72 and DD 0x5a514b test `[p+0x34] == 0x39`.
- Track samplers:
  - root: DM 0x5bfa60, DD 0x5a5030
  - all tracks: DM 0x5c0660, DD 0x49f040
  - morph: DM 0x5be8a0, DD 0x6ccba0
  - "does the clip have bone b": DM 0x5be830, comparing `[p+0x34+0x14k]`
- Mesh binding: the bone index goes through a per-skeleton byte table (`movzx eax, byte [table+bone]`, 0xFF = not bound; DM 0x5bea4b).
  - [unknown] How that table is built.
  - The per-level variation of C proves C is not a fixed global id list beyond index 60, so the
    binding must be by name.
- Hard-coded C indices:
  - GROUND = 57 (0x39), r/l hand attacher = 0x3c/0x3b
  - a left/right mirror table for indices 0..0x42 (DM 0x5beae0, DD 0x86d2d0, identical content)
- **IdxT key-time stream** (DM 0x5bdbd0, DD 0x6663b0):
  - `'IdxT'`, then u32 w with bits 0-1 = 1 (always), bits 2-5 = b (bits per frame) and bits 6-21 = K (key count).
  - Then K frame numbers of b bits each, LSB-first, starting at bit 0x36 of the stream.
  - Size = ⌈(54 + bK)/8⌉. Key 0 = frame 0 and key K-1 = the last frame (always, K ≥ 2).
  - The sampler binary-searches the key interval containing the frame.
- **Position data:** K × float3 (one per key of the position IdxT). These are local translations
  relative to the parent bone, interpolated linearly. Every bone has a position track, so clips
  impose bone lengths.
- **Rotation stream** (DM 0x5bdd30, DD 0x834170), with header byte h:
  - `L = h & 3` is the omitted component, `c = (h>>2)&1` the constant flag, `b = h>>3` the bit width.
  - **b = 31: raw.** Floats: key i at stream+4+16i (4 floats). Never occurs in the samples.
  - **Otherwise:**
    - Three signed b-bit base values m0..m2 follow at bit 8, LSB-first. Scale `s = 1/(2^(b-1)-1)`.
    - **c = 1:** one sign bit follows; every key = (m0, m1, m2)·s.
    - **c = 0:** three 5-bit widths n0, n1, n2 follow. Each key i occupies `1+n0+n1+n2` bits at
      `8+3b+15+i(1+n0+n1+n2)`: a sign bit, then unsigned deltas d0..d2. Key = (m+d)·s.
  - **Quaternion assembly:**
    - The three values fill components ≠ L in order.
    - `q[L] = ±sqrt(1 − min(1, Σ²))`, negative if the sign bit is set.
    - Component order is the engine's (x, y, z, w) slot order.
  - Keys are slerped (DM 0x430a60, DD 0x8441f0). The stream length follows from K (taken from the rotation IdxT).
- **Morph channel:** IdxT at idxOff, K floats at valueOff, linear interpolation (DM 0x5be8a0).

### 6.4 Baked-matrix block (flag 0x10)

- Layout: `u32 n, u32 bone[n]`, then per frame per bone 7 floats (quaternion + position).
- [code] DM 0x5be9a0 / 0x5bfa90.
- No clip in the samples uses it. The converter still remaps its bone list.

---------------------------------------------------------------------------------------------------

## 7. Converting DM → DD (what `anm_merge.py` does)

1. **Parse both files.** The base must be DD format; the source can be either.
2. **Clips** are converted lazily, only those referenced by a list that gets added.
   - **Blob:** the owner blob is copied verbatim to the end of B, 4-aligned. The two kinds of index inside it are rewritten **by name**:
     - each track's `bone` (C table);
     - each morph `channel` (E table).
   - New names are appended to C and E. The base's C/E entries never move, so GROUND stays at 57.
   - **Record:** u32 0..11 are copied, with the offsets in fields 3 and 4 rebased. A/P are copied to
     both start and end (A_end = A, P_end = P). Flag 0x1000 is set iff A or P is non-zero. This
     reproduces DM behaviour, where only the start values were used. `--pose-vectors drop` instead
     clears the flag and zeroes the vectors, as DD stores its own flagless clips.
   - The clip name is appended to D.
3. **Mapped DB (`db_map`):** each DM path that the target DD DB does not already resolve gets a new
   variant list.
   - The DM condition keys are kept and clip indices remapped.
   - The path is added to type 7 if missing (new ids are appended, so existing ids never change).
   - The DB's index is extended.
   - Paths the DD DB resolves keep DD's clips.
   - When several DM DBs feed one DD DB, the same-named one goes first, then file order; the first DB to add a path wins.
4. **Unmapped DM DB:**
   - If a DD DB of the same name exists, it is merged into that DB (needed: a second DB of that name would be shadowed).
   - Otherwise it becomes a new DB `anmcol:animationdatabase#<Name>`, inserted so the suffix lookup finds it (§4).
5. **Rebuild:** type-5 lists are recomputed, sizes and header totals rebuilt, hdr[10..12] = max(base, DM).

---------------------------------------------------------------------------------------------------

## 8. Open questions

- hdr[10..12] of type 4: [unknown]. They are stored by the loader, but no reader was found.
- Record u32 0 (lo u16), 5, 10, 11 and flags 0x8/0x40/0x80: meaning [unknown]. They are identical in DM/DD for the same clip, so they are copied.
- Pose vectors A/P: what they physically are, and which DD systems read the blended result beyond 0x8b4200: [unknown].
- The name transform `gameMgr->vt+0xa4/0xa8` applied before the DB suffix match: not analysed. The converter assumes the request is the short DB name, which is the most restrictive case.
- How track bone indices are bound to mesh bones (the byte table): not located. It must be by name, given the per-level tables. A byte-sized table may limit C to 255 entries; the merged F03+M01A file has 184.
- DM-only event ids (1, 13-19, 21, 24, 30, 37, 38): semantics in DD unknown. They are copied unchanged.
