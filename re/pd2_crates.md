# Payday 2 asset crates (2026-10-10)

Reader: `tools/pd2_crate.py` (pure Python; module + CLI). Game: `C:\Steam\steamapps\common\PAYDAY 2`
(64-bit, Steam build 25506656). Store: `assets\*.crate`, 98 files, 34.65 GB, plus `hashlist`
(186,212 paths without extension), `crates.shipping_manifest`, `crates.properties`. Nothing from
the game is in the repo; extracted data lives in `<KL_PortTools>\pd2\` only. Everything below was
measured on the files unless marked ASSUMPTION; the previous public tools (DieselBundleViewer,
payday2-tools-rust) read the OLD `all_N.bundle` / `bundle_db.blb` store and do not apply to this
format - only their scriptdata notes were used (`pd2\public\`).

## Established: crate layout

| offset | content |
|---|---|
| 0x00 | `'YAOI'`, u32 version = 1, u64 n |
| 0x10 | n x 48 bytes: u64 ext idstring, u64 path idstring, u64 offset (from file start), u64 raw size, u64 stored size, u64 properties |
| after | u64 0, u64 m, m x 40 {ext, path, 0, offset, size 512}: signature table; m = 1,646 (scripts), 2 (engine), 0 elsewhere |
| 1,000,000 | data blobs, sorted by offset, each at align16 of the previous end, zero padding |
| end | signature blocks (scripts, engine) or the last blob |

- stored == 0: raw bytes of `raw` size. stored > 0: one zlib stream (`78 0d ..`) of `stored` bytes
  inflating to exactly `raw`. raw == 0 (20,260 entries, all `cooked_physics`): offset 0, empty file.
- The table is sorted by (ext, path); the blobs are not in table order.
- properties: 0 on 278,441 entries, a single bit on 237: 14 language bits on `strings/*.strings`
  and `fonts/*_mf.merged_font` (one entry per installed language, 167 duplicate keys), d3d11
  (bit 0) on the 7 `core/shaders/*.shaders`, dds (bit 18) on 55 and dds_hcm (bit 19) on 7 `.swatch`,
  model (bit 8) on one `.old`. Bit names from `crates.properties` (`'YURI'`, u64 21, 21 x
  {u64 idstring, u64 bit}). ASSUMPTION: an entry with a bit is used only when the property is on.
- idstring = Bob Jenkins lookup8 `hash64(bytes, level 0)` of the lower-case path or extension
  (`hash64('lua')` = ab2664bf82e6460c = the extension of every scripts.crate entry).
- 98 crates: `assets_NN_S`, `init_NN_S`, `default_NN_0` (NN 0..15, S 0 = big blobs, 1 = small),
  `movies_NN_0`, `engine`, `scripts`. The shard is not derivable from the hash (measured: the five
  files of one unit sit in five crates). Only the (path, ext) key matters.
- `crates.shipping_manifest` lists every (ext, path) once per crate (278,605 records) and repeats
  the 21 properties as 12-byte records; `pd2_crate.py manifest` prints it. 94 flagged records point
  to files in no crate table (ASSUMPTION: dangling references).

Verified 2026-10-10 with `python tools/pd2_crate.py verify scripts engine assets_00_1` (every blob
inflated, size == raw, 16-byte layout, zero padding, end at tail):

| crate | entries | empty | zlib | faults | time |
|---|---|---|---|---|---|
| scripts.crate | 1,646 | 0 | 1,646 | 0 | 0.1 s |
| engine.crate | 73 | 0 | 73 | 0 | 0.1 s |
| assets_00_1.crate | 5,917 | 853 | 5,064 | 0 | 0.7 s |

Index of all 98 headers: 278,678 entries, 278,511 distinct keys, cached as `pd2\index.json`
(24 MB, keyed by crate size + mtime); names from the hashlist cached as `pd2\names.json`.
278,508 keys have a named path; the 3 unnamed are two `.unit` (196 and 242 bytes) and one
1.4 MB `.texture`. All 77 extension hashes are named (the engine's types plus words that stand
in the hashlist as lines of their own: continents, swatch, blacklist, bmfc ...).

## Established: extensions (entries, raw bytes)

| ext | entries | raw bytes | content |
|---|---|---|---|
| stream | 74,437 | 6.74 GB | raw WAV |
| texture | 51,347 | 33.97 GB | DDS (`'DDS '` + 124-byte header) |
| unit | 24,633 | 9.5 MB | text XML `<unit type=.. slot=..>` |
| model | 23,537 | 3.22 GB | Diesel binary, first dword 0x44424f44 (`tools/pd2_model.py`) |
| object | 23,453 | 36.7 MB | text XML `<dynamic_object>` (1 binary in the first 3,000) |
| cooked_physics | 23,446 | 46.4 MB | PhysX cooked mesh (`NXS\x01MESH` after 8 bytes); 20,260 EMPTY |
| material_config | 22,431 | 31.7 MB | text XML `<materials version="3">`; 606 are an ELSE pair (below) |
| animation | 8,046 | 496 MB | |
| package | 6,849 | | |
| sequence_manager | 3,865 | 21.2 MB | binary scriptdata |
| mission / continent / world / nav_data / cover_data / massunit / world_* / continents | 1,091-2,734 each | | binary scriptdata, world files |
| lua | 1,646 | 25.3 MB | LuaJIT 2 bytecode `1b 4c 4a 02`, NOT source; each has a 512-byte RSA signature |
| movie | 170 | 3.66 GB | |
| others (effect, bnk, environment, gui, strings, font, menu, shaders ...) | | | see `pd2_crate.py stats` |

material_config ELSE pair (606 of 22,431; the crew masks among them): the blob is
`\n<materials ...>...</materials>\n ELSE {\n<materials ...>...</materials>\n}`. For msk_wolf the
first branch has `render_template="solid_mask:MATS_3"` with three `diffuse_layerN_texture` matcaps,
the second `render_template="solid_mask"` with `tint_color_a/b`. No IF line is in the blob.
ASSUMPTION: a build / platform preprocessor keeps one branch. `text_documents()` splits them;
`write_xml` writes `.xml` (first) and `.else.xml` (second).

Binary scriptdata (`.sequence_manager`, world files): 6 sections x 32 bytes {0, count, capacity,
offset} (float, string, vector, quaternion, idstring, table), u64 0 + u32 root item at 0xc0, items
are `type << 24 | index` (0 nil .. 8 table), tables are 40-byte {meta string, count, capacity,
items offset, 0}, 4 trailing bytes. `xml_text(data, check)` prints the tree and proves it: for
`npc_criminals_suit_1.sequence_manager` tables 274 = printed 274, strings 155 = used 155, floats
60 = used 60, opened 274 = closed 274, trailing 4. Text documents are proved with a parse of each
branch. All 32 extracted documents pass (`xml_ok`).

## Usage (from the repo root)

```
python tools/pd2_crate.py index                       rebuild pd2\index.json + names.json
python tools/pd2_crate.py find <substring>            paths containing it (ext, raw size, crate)
python tools/pd2_crate.py extract <path> <ext> [<out>] [--xml]
python tools/pd2_crate.py extract-prefix <prefix> [<out dir>] [--xml]
python tools/pd2_crate.py verify <crate> ...          inflate every blob, check layout
python tools/pd2_crate.py stats                       per-extension table
python tools/pd2_crate.py masks                       pd2\masks_list.json
python tools/pd2_crate.py manifest                    shipping manifest + properties
python tools/pd2_crate.py xml <file> [<out.xml>]      document -> text (+ proof when writing)
```
Module: `Index().get(path, ext)` -> `Entry`; `Index.read(ent)` -> bytes; `Index.extract(ent, out,
root, xml)`; `hash64`, `xml_text`, `text_documents`, `write_xml`, `xml_ok`.

## What is extracted (`<KL_PortTools>\pd2\extract\`, 461 files, 349 MB)

- `units/payday2/masks/`: msk_wolf, msk_dallas, msk_chains, msk_hoxton, msk_dallas_clean,
  fps_temp_dallas, msk_fps_back_straps - every extension (.unit .object .model .material_config
  .cooked_physics, `<x>_df` / `<x>_nm` .texture) + .xml beside each document.
  msk_dallas_glow is `units/pd2_dlc_cop/masks/msk_dallas_glow/` (10 files, with `_il` glow
  textures), extracted there. The crew masks' `.cooked_physics` are empty entries (raw 0).
  A mask unit: `<unit type="static" slot="1">` with extensions ScriptUnitData + `MaskExt`; its
  object: `<diesel orientation_object="rp_wolf_mask" materials=...>` + graphics object `g_wolf`.
- `units/payday2/masks/shared_textures/patterns/`: 116 pattern textures (`pd2\shared_textures.txt`).
- lua (18): playerinventory, huskplayerinventory, playerbase, huskplayerbase, criminalsmanager,
  blackmarketmanager, playermanager, menu/menuscenemanager, blackmarkettweakdata, playertweakdata,
  charactertweakdata, and every lua path containing 'mask' or 'criminal' (maskext,
  blackmarket/maskstweakdata, states/playermaskoff(+vr), ingamemaskoff,
  elementpickupcriminaldeployables, criminalactionwalk). All LuaJIT bytecode: a decompiler is
  needed to read them (the public decompiled sources are the way; untrusted, `pd2\public\` only).
- `units/payday2/characters/npc_criminals_suit_1/`: .unit .object .model .sequence_manager
  (.cooked_physics empty), `mtr_dallas.material_config`, `dallas/npc_criminal_suit_dallas.unit`
  (`<unit type="being" slot="16">`, ManageSpawnedUnits with the joint list Hips .. Head ..).
  Every `units/payday2/characters/` entry with 'head' or 'mask' in its name (head textures of the
  shared_textures folder and civilians, `ene_spook_1/debris/ene_spook_head_debris.*`).
- `pd2\criminal_paths.txt` (399 lines): every path with 'criminal' under units/ and its
  extensions - the other bodies (fps_criminals_suit_1 with per-heister mtr_*.material_config,
  npc_criminal_casual_1, npc_criminal_female_1, ...).
- `pd2\masks_list.json`: {folder: [{name, ext, raw, crate}]} for the 804 folders with '/masks/'
  in the path (578 distinct folder names across the DLC prefixes).

## Mask folders directly under units/payday2/masks/ (70 + shared_textures)

fps_temp_dallas msk_alienware msk_anonymous msk_baby_angry msk_baby_cry msk_baby_happy msk_babyrhino msk_backside msk_base msk_bear msk_biglips msk_brainiack msk_brazil_baby msk_buha msk_bullet msk_chains msk_chains_clean msk_clown_56 msk_clowncry msk_cthulhu msk_dallas msk_dallas_clean msk_dawn_of_the_dead msk_day_of_the_dead msk_demon msk_demonictender msk_dillinger_death_mask msk_dripper msk_fps_back_straps msk_frank msk_gagball msk_greek_tragedy msk_grin msk_hockey_a msk_hog msk_hoxton msk_hoxton_clean msk_irondoom msk_jaw msk_kawaii msk_monkeybiss msk_mr_sinister msk_mummy msk_oni msk_outlandish_a msk_outlandish_b msk_outlandish_c msk_pumpkin_king msk_rubber_female msk_rubber_male msk_samurai msk_scarecrow msk_shogun msk_shrunken msk_skull msk_skullhard msk_skulloverkill msk_skulloverkillplus msk_skullveryhard msk_stonekisses msk_tounge msk_troll msk_unicorn msk_vampire msk_venomorph msk_witch msk_wolf msk_wolf_clean msk_zipper msk_zombie

The earlier "307 mask folders" figure (CLAUDE.md) matches none of the counts measured here
(70 / 578 / 804); the DLC masks live under `units/pd2_dlc_*/masks/`, `units/pd2_crimefest_*/...`.

## Verification (2026-10-10, independent re-run against the 98 crates)

Re-run by a verifier session with its own scripts; nothing in `tools/pd2_crate.py` was changed.

Holds (measured):
- `verify` on init_03_0 (1,977 entries, 305 raw / 1,672 zlib), default_07_0 (5,283, 45 empty),
  init_11_1 (1,523, 332 empty), movies_02_0 (14, all raw), scripts, engine, assets_00_1: 0 size /
  inflate / layout / padding faults, every one ends at the tail; the numbers in the table above
  are reproduced exactly.
- Index: 278,678 entries, 278,511 keys, 77 extensions all named, 3 unnamed keys (unit 196 B,
  unit 242 B, texture 1,398,256 B), 20,260 raw == 0 entries all cooked_physics with offset 0,
  properties single-bit only with the per-extension counts given above, hash64('lua') =
  ab2664bf82e6460c, tables sorted by (ext, path) as unsigned u64 (4 crates checked), shard !=
  path hash mod 16 (18,783 of 20,000 differ).
- 10 random non-empty entries of 10 extensions read back with len == raw and the expected magic
  (DDS, DOBD, 1b4c4a02, RIFF, BKHD, BIK for movies, '<unit' for units).
- Signature tables: scripts 1,646 x 512 bytes (all lua, every key in the table), engine 2
  (security_settings, game_config); the blocks run to the file end. The PEM is at path
  `crate_public_key` (no `core/`), 814 bytes, a 4096-bit RSA public key header.
- Hashlist: all 336 lines under `units/payday2/masks/` resolve to a path hash in the index;
  70 folders + shared_textures, 578 / 804 as stated. Manifest: 278,605 records, flag 1 on 105,
  94 of them in no table; every table key is in the manifest.
- 20 random documents from other folders (5 each of unit, object, material_config,
  sequence_manager) convert and pass `xml_ok`; ALL 3,865 sequence_manager files are binary
  scriptdata and all pass the proof counters (tables, strings, floats, open/close, trailing 4).

Corrections:
- ELSE pairs: 606 is right, but 8 of them use `\r\n ELSE {\r\n`; `text_documents()` matches only
  the LF form, so those 8 (e.g. pd2_dlc_bbq/masks/msk_gasmask, pd2_dlc_casino/masks/
  msk_croupier_hat) come back as ONE document with the second branch inside it, and `xml_ok`
  reports 'junk after document element'. 598 split correctly. Not one of the four crew masks.
- "1 binary in the first 3,000 objects": there are no binary objects or units. 5 objects and 1
  unit (e.g. off_prop_officehigh_whiteboard_wall.object, rvd_ext_jewelry_store_window_02.unit)
  are text XML with one or two stray bytes before `<` ('2', 'f', ' w'); `is_text_xml` rejects them,
  `xml_text` then tries the scriptdata reader and raises ValueError, so `extract --xml` and
  `extract-prefix --xml` abort on such a file. material_config: 0 binary, as stated.
- Strict well-formedness is not a property of the game's text documents: a sample (every 25th
  unit / object plus all ELSE material_configs) found duplicate attributes, mismatched tags and
  invalid tokens in genuine files (3 units, 4 objects, 16 material_configs). `xml_ok` False on a
  text document means minidom refused it, not that the extraction is wrong.
- The docstring says the hashlist names 278,490 keys (line "IDSTRING = ..."); the measured and
  otherwise stated figure is 278,508.
- "167 duplicate keys": 16 keys are duplicated (10 x 15 languages, 3 x 5, 3 x 6) = 167 extra
  entries.
- `Index.names` hashes hashlist lines as raw bytes, not lower-cased as `hash64(str)` does; the one
  line with upper case (`soundbanks/TRAI_H`) is also present lower-cased, so nothing is lost today.
