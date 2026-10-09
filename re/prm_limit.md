# The .prm chunk limit (kl2.exe) and how a build stays under it

2026-10-09, agent x-chunks. Offline work: kl2.exe read with `debug/dasm.py`, the counters read out of
the crash dumps that were already on disk. Nothing here was run in the game.

## The number

| | table entries (header entry 0 included) | highest chunk index |
|---|---|---|
| **Table size in kl2.exe (hard)** | **73,728** = 0x12000 | 73,727 |
| **Limit the tools enforce** (`kl_impact.CHUNK_SAFE`) | **69,632** = table - 4,096 run-time slots | 69,631 |
| Largest stock Dog Days level (L10) | 36,778 | 36,777 |
| Retomoto without wardrobe (loads, plays) | 65,119 | |
| Retomoto, full wardrobe, run P4 (crashed) | 80,628 | |
| Retomoto, full wardrobe, built here | 65,119 | |

"Table entries" is the count in the .prm header (+4), one more than what the logs call "chunks".
The limit is NOT 65,536 and chunk indices are not 16-bit anywhere that was found (below).

## Evidence

**The table.** One pointer per chunk index at `0xeac7b0`, 4 bytes each. Both level loaders
(`0x496d80` = ZRenderWintelDll slot 27, `0x8007f0` = ZRenderWintelD3DDll slot 28) do

    memset(0xeac7b0, 0, 0x48000)                 ; 0x48000 / 4 = 0x12000 slots: the table's size
    [0xeac7a4] = [0xeac7a8] = count              ; from the .prm header +4
    [0xcda384] = 0x11fff                         ; the table's LAST slot
    for i < count: if entry[i].refcount != 0: table[i] = file base + entry[i].offset
    table[0] = 0

There is no comparison of `count` with anything: 429 code sites name the table (418 reads
`mov r, [r*4 + 0xeac7b0]`, 5 writes, 3 memsets), none is bounds-tested, and none loads its index
with `movzx` / a 16-bit load within the twelve instructions before it. `.gms` record +0x0c, the
.prp fields and every reference inside the .prm are u32.

**The table is shared with chunks made at run time.** `0x509970` (ZPrimControl slot 10: copy
`size` bytes into the spare 0x60000 bytes behind the loaded .prm and give them an index):

    if (heap room < size  ||  [0xeac7a8] > [0xcda384]) int3
    front:  table[[0xeac7a8]++] = p            ; upwards from the file's count
    back:   table[[0xcda384]--] = p            ; downwards from slot 0x11fff

So the file's count, the run-time chunks above it and the run-time chunks below the top must fit
73,728 together, and the test is an `int3` (a crash in retail). Measured in the 14 kept dumps of
grafted levels (`KLHook*.dmp`, values of 0xeac7a4 / 0xeac7a8 / 0xcda384):

| run | file count | made above | made below the top |
|---|---|---|---|
| menu | 3,587 | 10 | 140..144 |
| M02b | 58,291 | 435 | 136 |
| ESC1 | 61,761 | 437 | 187 |
| stack overflow run | 62,565 | 435 | 251 |
| RT2 / RT3 | 65,019 / 63,956 | 429 | 125 / 137 |
| owner's crash 17:42 / 17:59 | 65,099 | 429 | 140 / 276 |
| 18:22 | 65,119 | 429 | 266 |
| P4 (the crash) | 80,628 | 0 | 0 |

At most 713 run-time chunks were seen (20, 44 and 64 bytes each). The enforced limit keeps 4,096
slots for them. ASSUMPTION: that is enough for a full round - the callers of `0x509970` were not
found (it is reached through the vtable), so the number of 20-byte chunks made from the top is not
bounded by anything read here; it grew from 125 to 276 between a fresh level and a few minutes in.

**What P4 overwrote.** The table ends at `0xef47b0`. Entry i lies at `0xeac7b0 + 4*i`:

| entry | address | what the code holds there (sites) |
|---|---|---|
| 73,728..73,744 | 0xef47b0..0xef47f0 | nothing kl2.exe names |
| 73,745 / 73,746 | 0xef47f4 / 0xef47f8 | globals read at 0x8b8c3d, 0x546f95 |
| 73,747..73,793 | 0xef47fc..0xef48b4 | a static-constructed block (16 x 12 bytes, 0xadea06..) |
| 73,794 | 0xef48b8 | an object pointer, 13 sites (0x45f37d, 0x518955, 0x55ec4f, 0x6afba5 ..) |
| 73,795..73,798 | 0xef48bc..0xef48c8 | globals (0x502271, 0x6c43ef, 0x542af6, 0x4f1973) |
| 73,926..73,931 | 0xef4ac8..0xef4adc | globals (0x5ad2eb, 0x7a7a9b, 0x87166c, 0x5e3eb2) |
| **73,932** | **0xef4ae0** | **the loading-progress object, 11 sites: 0x607272 = the P4 crash** |
| 73,934.. | 0xef4ae8.. | more statics |

A slot is only written when the chunk's refcount is not zero, which every chunk of P4 had. So:
Retomoto at 65,119 was NOT past the end and not living on luck: it had 8,609 slots free and used
about 700 of them. Everything from 73,729 entries on destroys globals; P4 had 6,900 too many.

**Other per-chunk limits.** None found: no second table is indexed by chunk number (the 256-slot
list at 0xeac3a0, count 0xeac7ac, belongs to `0x45f260`, the render's "drop the models on this list
and close the gaps" routine, and holds indices, not one slot per chunk). The .prm is read into ONE
heap block of file size + 0x60000 (kl_graft, run RT1): size is the other limit, not the count.

## The check

`kl_impact.chunk_limit(prm)` -> `[]` or one problem text (bytes or a kl_prmgraph.Prm). It is part of
`kl_impact.check()` (so `python tools/kl_impact.py <build>` reports it) and of the wardrobe command.
For `kl_graft.verify()`, next to the bone test:

    bad += kl_impact.chunk_limit(out['.prm'])

## Staying under it: the dead chunks' indices

A grafted level's .prm is S's whole file + M's map. S's removed map is still in it as dead chunks:
nothing in the .gms, the .prp or the scene block reaches them (`kl_graft lighten` empties their
vertex data but keeps every index).

| base | entries | live | dead | of those named by the .oct tail |
|---|---|---|---|---|
| Retomoto `build/play3s` | 65,119 | 37,791 | 27,327 | 5,388 meshes (20,510 pairs) |
| bank `build/i_bank` | 62,657 | 34,251 | 28,405 | 5,631 meshes (21,613 pairs) |

`kl_prmgraph.reuse(p, live, keep)` turns every dead chunk that `keep` does not hold into a 16-byte
stub and lists its index in `p.free`; `kl_prmgraph.new_chunk()` and `append()` fill those indices
(lowest first) before they add one at the end, numbering every reference inside the new sub-graphs
accordingly. Nothing live moves, so no holder of a chunk index has to be rewritten.

- live = `kl_prmgraph.level_roots(prp, tids, raw .gms, extra)`: the .gms records, the .prp fields and
  scene block (the same set as `kl_graft.live_roots`, no kl_graft import), plus `extra` = model
  roots that NO entity names. The wardrobe's roots are such: `kl_chars.wardrobe_roots(folder)` reads
  them from `KLWardrobe.ini`. A chunk a dead root reaches and a live root also reaches is live.
- keep = the chunks of the .oct tail pairs. The graft keeps S's removed map's collision records, and
  `kl_graft.verify` wants every pair on a 64-byte mesh, so those dead meshes stay byte for byte.
  They now point at stubs or re-used chunks. Why that is safe: no code loops over the chunk table
  (its count 0xeac7a4 is read only by the two loaders, by 0x638c90 "is this a file chunk" and by
  0x45f260); every use is an index taken from a holder, and a dead chunk has no live holder. The
  dead roots that owned those .oct records are stubs now: the records stay in the .oct unowned -
  the same thing for the engine as owned by a root no entity has.
- `kl_chars.put()` and `kl_chars.wardrobe()` do this by default (`--no-reuse` = the old way).
  `kl_impact.sync_bone_ids` (--fix-bones) takes free indices too.

**Order matters:** `lighten` (trim / slim) finds the dead materials and textures through the dead
roots. After a reuse there are none left, so lighten FIRST, wardrobe second. And lighten on a
wardrobe build must be told the wardrobe's roots, or it calls the eight Dead Men heroes dead and
empties them (no entity names them). For `kl_graft.open_built()`, replacing its last line:

    import kl_chars                                    # the wardrobe's roots: no entity names them
    extra = [(r, 'root') for r in kl_chars.wardrobe_roots(os.path.join(os.path.dirname(path), 'KLWardrobe.ini'))]
    return order, files, ext, sc, live_roots(sc, G.gms_roots(raw)) + extra, hud_textures(sc)

(`relight` takes `live` from there; `G.walk` accepts the pairs.) The trim step inside
`kl_graft.build` runs before any wardrobe exists and needs no change.

## Not done / open

- Who calls `0x509970`, i.e. a real bound on the run-time chunks. The 4,096 is a margin over what
  was seen, not a proof.
- Re-use inside the graft itself (M's map into S's dead indices: a grafted level would have about
  40,000 entries instead of 65,000). It needs more than a line in kl_graft: `build` precomputes the
  numbering (`cmap = {old: len(prm_s.chunks) + k ...}`), and insists that every S .oct record is
  owned by a root (`moved != len(oct_s.records)`), so S's dead records would have to be dropped
  from the .oct first (`kl_octree.select_records`). `kl_prmgraph.append` numbers exactly as before
  when `a.free` is empty, so kl_graft is unaffected as it stands.
- Compaction (renumbering the live chunks): written and proven offline, not loaded - next section.

## Compaction (`python tools/kl_chars.py compact <build> <out>`) - offline only, NOT LOADED LIVE

`kl_chars.compact_level` = `kl_prmgraph.compact` (the live closure, renumbered in the old order)
plus every holder rewritten: `.gms` record +0x0c, the `.prp` fields and scene-block entries of
`kl_prmgraph.prp_roots`, the `.oct` (only records a live root owns are kept, so record offsets
change and every live root's +0x1c is rewritten; tail pairs renumbered), `KLWardrobe.ini`. It proves
itself offline: the rewritten files must reach the new file completely, chunk for chunk as the same
kinds. On the Retomoto wardrobe build: 65,119 -> 50,703 entries, 12,900 .gms and 14,406 .prp
references, 2,616 of 3,585 .oct records kept; kl_impact 0 problems, 108 of 108 people drawn.

What is missing to call it safe: it moves the systems level's LIVE chunks, which no build has done
(the graft and the wardrobe only add). The .prp field list was found statistically; an index held
only now and then, or inside a raw blob (.buf, .sgd, .HVK, KEYS tracks), is not in it. Nothing
suggests there is one (the known holders reach 99.991 % of Dog Days' chunks), but only a live load
with HUD, fonts, effects and post-filters visibly right settles it. It is not needed for the limit
today - re-use is enough - so the deliverables below are NOT compacted.

## Results (2026-10-09, offline; logs in `<work>\build\x_chunks\*.log`)

| build (`<work>\build\x_chunks\`) | base | entries | highest index | .prm | archive |
|---|---|---|---|---|---|
| `retomoto_wardrobe` | `play3s` (65,119; 61.6 MB) | 65,119 | 65,118 | 77.8 MB | 212 MB |
| `bank_wardrobe` | `bank_light` = `i_bank` after `lighten` (trim, slim), --fix-bones | 62,657 | 62,656 | 60.5 MB | 189 MB |
| `bank_wardrobe_noslim` | `bank_trim` = `i_bank` after `lighten --load trim`, --fix-bones | 62,657 | 62,656 | 60.5 MB | 325 MB |
| `retomoto_wardrobe_compact` (experiment) | `retomoto_wardrobe` | 50,703 | 50,702 | 77.0 MB | |
| for comparison: `play4` (crashed) | | 80,628 | | 79.0 MB | |
| for comparison: `v_wardrobe\wardrobe_bank` | `i_bank` (86.6 MB) | 78,189 | | 104.1 MB | |

All with the full wardrobe: 16 characters, 8 masks, 24 Dead Men outfits (11,818 mesh objects).
The wardrobe took 15,509 of Retomoto's 23,409 free indices (7,900 left) and 15,532 of the bank's
24,340 (8,808 left): neither file grew by one index.

Checks run on each of the three deliverables:
- the wardrobe command: `problems: 0` (check_wardrobe, kl_chars.check on the new roots, undrawn, chunk_limit);
- `python tools/kl_impact.py <build>`: `problems: 0` (bone ids, surface table, chunk limit);
  the same command on `play4`: the limit problem (80,628 entries, 6,900 pointers past the table);
  `kl_impact.py stock`: 0 problems in 41 levels;
- `python tools/kl_chars.py invisible <build>`: 108 of 108 people drawn (Retomoto), 36 of 36 (bank);
- `python tools/kl_chars.py check <build>`: bank 0; Retomoto 1 - material 1410 Weapons/BombWindow_02
  asks for a shader the .fxc lacks. `play3s` and `play4` have the same line: it is the base's;
- a separate comparison with the base (scratch script): every chunk the base's files reach has the
  same index and the same bytes in the build (Retomoto 37,791 of 37,791; bank 34,228 of 34,251,
  the 23 others are the skeletons --fix-bones repaired); the .oct tail and the base's records are
  unchanged and every pair still names a 64-byte mesh; .MAT ref table = the .prm's; the .prm
  round-trips; only the 8 heister entities changed model.
- a later trim WITHOUT the wardrobe roots would empty 453 chunks (15.8 MB: the eight Dead Men
  heroes) of `retomoto_wardrobe`; with `kl_chars.wardrobe_roots` it empties nothing. Hence the
  `open_built` lines above - the same holds for every wardrobe build made before today.

Not loaded live: all of it. `bank_wardrobe` sits on a trim + slim base and the bank has never run
with either option (kl_graft.load_options says so); `bank_wardrobe_noslim` has the textures whole.
