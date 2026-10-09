# Streamed sound: the stream file, the merge, and Retomoto Tower's music

2026-10-09, agent g-audio. **Offline only**: the game was not started, nothing was installed.
Tool: `tools/kl_str.py`. Builds on `re/audio.md` (banks, .WHD, voice lines), `re/retomoto.md`
section 6 (the clips), `re/retomoto_fa.md` section 6 (the authored layer).

Words: **MEASURED** = counted on this machine's files; **EXE** = read in kl2.exe at the address
given; **ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a run can settle it.

    python tools/kl_str.py test            stock files + both merges + the six grafted banks (6 min, writes 3.3 GB)
    python tools/kl_str.py test quick      stock files only (2 s)
    python tools/kl_str.py need --names    the clips the six maps need, by Dead Men offset
    python tools/kl_str.py build           <work>\build\str\PC_Def.str from Dog Days' STOCK file
    python tools/kl_str.py build --extend  <work>\build\str\extend\PC_Def.str from the current merged file
    python tools/kl_str.py info|list <file.str> [text]

## 0. Result

1. Both games' stream files are the same format but for the width of one header field. The reader
   accounts for **every byte of all 9 files** (Dog Days PC_Def + PC_Eng, Dead Men PC_Def, PC_Eng,
   PC_Fre, PC_Ger, PC_Ita, PC_Spa, and the stock Dog Days file in KL_PortBackup).
2. `kl_str.need()` computes what the grafts of M01/M02/M03/M06_FA_A, M09_A and M09_B need from the
   same roots and closure `kl_snd.graft_audio` uses: **892 blocks, 2,075 clips, 351.3 MB**.
   `kl_str.merge()` appends them to Dog Days' file: **1,586,585,559 bytes** (stock 1,217,890,070).
   Re-read: 0 problems, every byte accounted for, the stock file's first 0x4888d700 bytes
   unchanged, all 5,926 stock clips where they were, all 892 blocks equal to Dead Men's.
3. With that file, the merged banks of all six maps (F07 as systems level) hold **0 stream records
   that resolve to no block** and 0 clips missing (before: 6 in M09_A, 9 in M09_B - and the two
   music layers the FA layer starts). Build id of the banks = the file's (4c08b8d5).
4. Retomoto's music is **7 clips = 3 two-layer pieces + 1 single**, all in the new file. The other
   8 of the "15 under Music/InHouse/Japan" are the club music of M05_A, not this level.
5. Dog Days has **two working routes** to music in a Fragile Alliance round, neither checks the game
   mode (EXE): a `PlayMusic` controller (starts on 'AITrigger' or 'Activate') and settings field
   157 (started by the settings' Init). The authored layer already uses the first; section 5 gives
   the lines for both.
6. Found on the way: the installed merged file (`kl_audio.merge`, 1,575,448,788 bytes, = the one
   in `<work>\build`) holds 1,944 Dead Men blocks, **1,118 of them (92 MB) needed by none of the
   six maps**, lacks 66 that are, and its index lacks the set entry or a member of 845 of its
   1,117 interleaved sets (84.6 MB of audio no index entry names). If the engine never reads the
   index (section 1.4) that is harmless; `merge()` repairs it either way.

## 1. The stream file

### 1.1 Files on this machine

| file | bytes | build id | language field | clips |
|---|---:|---|---:|---:|
| DD `KL_PortBackup\PC_Def.str` (the original, MOVED there 2026-10-08) | 1,217,890,070 | 4c08b8d5 | 0 | 5,926 |
| DD `PC_Def.str` (installed: the earlier merge, byte-identical to `<work>\build\PC_Def.str`, `cmp`) | 1,575,448,788 | 4c08b8d5 | 0 | 9,102 |
| DD `PC_Eng.str` | 56 | 4c08aec4 | 1 | 0 |
| DM `PC_Def.str` | 1,377,192,139 | 46e11c9f | 0 | 6,739 |
| DM `PC_Eng.str` | 56 | 46e11909 | 1 | 0 |
| DM `PC_Ger.str` / `PC_Fre.str` / `PC_Spa.str` / `PC_Ita.str` | 382.8 / 353.4 / 373.4 / 379.1 MB | 46e11e2b / 46e11f8e / 46e12105 / 46e12262 | 2 / 3 / 4 / 5 | 6,068 / 6,068 / 6,068 / 6,067 |

Every file has its own build id; the language field follows the .SND's stream-name order (Def Eng
Ger Fre Spa Ita). English audio is in PC_Def in both games; Dog Days has no other language file
here. A Dead Men language file has 44 Vorbis clips against PC_Def's 133 and 1,433 sets against 1,510.

### 1.2 Layout (MEASURED: `kl_str.Stream.account`, 9 of 9 files, 0 unexplained bytes)

```
0x00  'IOISNDSTREAM', u32 9
0x10  u64 build id
      Dog Days                     Dead Men
0x18  u64 index offset             0x18  u32 index offset
0x20  u32 clip count               0x1c  u32 clip count
0x24  u32 0x100                    0x20  u32 0x100       ASSUMPTION: the block alignment
0x28  u32 0, u32 1                 0x24  u32 0, u32 1    not established
0x30  u32 language                 0x2c  u32 language
0x34  u16 0x38 + 2 junk bytes      0x30  u16 0x38 + 6 junk bytes   (header size; the rest is stack fill)
0x38  zero to 0x100
0x100 DATA BLOCKS, each on a multiple of 0x100, zero padded, in id order
....  FORMAT TABLE (starts on a multiple of 0x100), id order
....  NAME TABLE, id order, each name + NUL
....  INDEX, 72 bytes per clip, sorted by name key, ends the file
```

A stub (PC_Eng.str) is the 0x38-byte header with index offset 0x100 and count 0.

Bytes by kind:

| | header + pad | LIP blocks | audio | padding | tail | formats | names | index |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DD stock | 256 | 11,165,696 | 1,205,031,739 | 729,797 | 0 | 166,412 | 369,498 | 426,672 |
| DM PC_Def | 256 | 12,402,688 | 1,363,315,672 | 226,344 | 32,768 | 222,828 | 506,375 | 485,208 |

"Tail": two Dead Men blocks (0x5f27300 `CellPhoneChitChat_001_JapaneseMale`, 0x14aeea00
`M12_LoudTalk_010_SpGuard`, both ADPCM with a LIP length over 0x1000) are 0x4000 bytes longer than
LIP block + index size, and those bytes are not zero. Not decoded; `merge()` copies a block up to
the next one, so they come along.

**Block.** `['LIP ', u32 length, lip-sync data: 0x1000 bytes in all]` when the clip has lip-sync,
then the audio. Dog Days 2,726 of 5,764 blocks have one, Dead Men 3,028 of 3,705.

**Format entry.** `u32 codec, samples, channels, rate, bits`, 8 junk bytes (uninitialised: pieces
of other names), then by codec:

| codec | what | bits | extra | entry size | DD stock | DM |
|---:|---|---:|---|---:|---:|---:|
| 2 | PCM 16 bit | 16 | u32 frame bytes (2 x channels) | 32 | 42 | 3,168 |
| 3 | IMA ADPCM, mono | 4 | u32 0x400 block, u32 0x7f9 samples per block | 36 | **0** | 1,928 |
| 4 | Ogg Vorbis | 0 (16 inside a set) | - | 28 | 5,805 | 133 |
| 0x1a | an interleaved SET (not a sound of its own) | 16 | u32 number of clips | 32 | 79 | 1,510 |

Dog Days' rates are odd numbers near 32000 (31,923 ... 32,000; resampled per clip), Dead Men's are
32000 / 16000 (and 22050 and odd ones for a few ADPCM clips).

**Index entry** (9 x u64 but for the split fourth):

| at | what |
|---|---|
| +0x00 | id = creation order: block offsets, format offsets and name offsets all ascend with it (5,926 / 6,739 of each) |
| +0x08 | offset of the BLOCK (the clips of a set hold the same one) |
| +0x10 | audio bytes, without the LIP block; the set entry: of the whole set |
| +0x18 | format offset |
| +0x20 | u32 format size, u32 **name key**: h = h * 5 + byte over the name as written (all entries of both games) |
| +0x28 | name length (without the NUL), +0x30 name offset |
| +0x38 | lip word: low dword 4 = this entry owns the block's LIP data; high dword 1..10 (not decoded). The .WHD record's 'lip' field is the same kind of value |
| +0x40 | layer: 0 = alone, n = the n-th clip of its set; the set entry holds the count |

The index is sorted by the key (135 / 112 key collisions, no name twice in a file). 12 names
exist in both games' PC_Def with different recordings (`Sniper_0n0_Lynch`, `Die_Helper_00n_Lynch`,
`AirlockLynch_0n0_Lynch`).

### 1.3 Interleaved sets (the X / X_R pairs)

A set is one block shared by 2 to 4 clips plus one codec-0x1a entry that names the layered sound
of the sound project (`LevelSetup/Level/M09_A/Music/TokyoAction1`; for a dialogue pair `X_R`
without '.wav'). The level's .WHD marks the members with the top format byte (0x82 = first of 2,
0x01 = second ...: re/audio.md 3).

- **PCM** (all of Dead Men's sets, 1 of Dog Days': three stereo music layers): sample frames in turn. One period = for each
  clip in layer order, (its rate / the set's lowest rate) frames. MEASURED by which
  de-interleaving gives smooth signals: a dialogue pair X (32 kHz mono) + X_R (16 kHz mono, the
  radio version) is `X X R`; three stereo layers `L1 R1 L2 R2 L3 R3`; stereo 32 kHz + stereo
  16 kHz `L R L R l r`; stereo + three mono `L R a b c`. Each clip's size is its own share; the
  shares add up to the set entry (1,510 of 1,510).
- **Vorbis** (78 of Dog Days' 79 sets): ONE Ogg stream whose channel count is the sum (two stereo
  layers = 4 channels, one logical stream, pages contiguous). The clips' sizes are total / n.

| sets in Dead Men's PC_Def | count |
|---|---:|
| X 32 kHz + X_R 16 kHz, mono (dialogue with its radio version) | 1,375 |
| X + X_R both 16 kHz / both 32 kHz | 102 / 9 |
| two stereo layers (music, ambience) | 11 |
| three / four stereo layers | 6 / 2 |
| other mixes of mono and stereo | 5 |

Dog Days has no X / X_R sets: its radio lines are separate Vorbis clips.

### 1.4 What the engine reads (EXE)

`ZDllSound` slot 36 (0x67e810) opens the file a level's .SND names, reads **0x38 bytes**
(`ReadFile(h, buf, 0x38)` at 0x67e8d9), closes it, and compares header +0x10 / +0x14 with the .SND
trailer's build id (0x67e8ff, 0x67e90b); on a mismatch it returns 0, else it queues command 0x102
with the file name for the sound thread. kl2.exe holds no 'IOISNDSTREAM' string (the magic is not
checked) and no 'LIP '. A level's .WHD record carries offset, sizes, rate, channels, codec, block
fields and the lip word. **ASSUMPTION** from that: the index, format and name tables are the build
tool's and the game plays by .WHD record alone. The sound thread's reader was not traced, so this
is not proven; `merge()` therefore writes complete tables in the stock layout.

Still open from re/audio.md: **Dog Days ships no streamed ADPCM clip** (0 of 5,926), and the six
maps need 205 of them (3.3).

## 2. What is installed today, and how it was made

- `DD\PC_Def.str` = `<work>\build\PC_Def.str` (byte-identical), written 2026-10-08 by
  `python kl_audio.py merge <DM PC_Def> <DD PC_Def> <out> fa_stream_names.txt`
  (`tools/kl_audio.py` `merge()`; `<work>\build\fa_stream_names.txt` = 3,149 names, `merge.log` is
  empty). Filter: names holding `Multiplayer/` or `Fragile_Alliance` + that list.
  `kl_package._backup_then_copy` installed it; **the original was MOVED to
  `DD\KL_PortBackup\PC_Def.str`** (1,217,890,070 bytes, dated Sep 13) and is intact (it is the
  stock file every test here reads).
- Its map `<work>\build\PC_Def.str.map.json` (1,944 entries) is what `kl_snd.stream_map()` reads.
- Its shape: Dog Days' data and tables untouched up to the old index (0x48910466), then per clip
  `[block][format][name]`, then a new index. Sets were entered by name match only: 845 of its
  1,117 sets have no set entry or lack a member. One block (Dead Men 0x5f27300) lost its 0x4000
  tail. Names were stored with the NUL counted in the length (stock: without).

## 3. Selection and merge

### 3.1 `need(levels)` - exactly what the grafts need

Per level: roots = `kl_snd.roots()` over the map-side nodes of `kl_snd.map_scene()` (the level
after `kl_convert`, sides by `kl_prpjoin.sides`) + the sound ids of the .LOC keys those nodes
name + (Fragile Alliance levels) every `Multiplayer/` leaf; closure over parameters, a sound's
wave, set / definition members and sequence targets (the rule of `kl_snd.merge`); then every
streamed PC_Def record of the reached waves with the other members of its set
(`kl_whd.group_of`). Language-file records are left out (only PC_Def is merged).

| level | roots | objects reached | stream records | blocks | MB | PCM sets | PCM | ADPCM | Vorbis |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M01_FA_A | 497 (72 fields + 134 named keys + 291 voice leaves) | 1,245 | 435 | 242 | 126.1 | 194 | 30 | 10 | 8 |
| M02_FA_A | 506 | 1,348 | 442 | 249 | 91.3 | 193 | 33 | 20 | 3 |
| M03_FA_A | 509 | 1,354 | 446 | 253 | 121.4 | 194 | 32 | 20 | 7 |
| M06_FA_A | 462 | 1,082 | 425 | 232 | 81.5 | 193 | 30 | 7 | 2 |
| M09_A | 74 | 2,145 | 775 | 548 | 116.1 | 338 | 20 | 170 | 20 |
| M09_B | 76 | 2,364 | 777 | 499 | 125.9 | 303 | 22 | 159 | 15 |
| the four FA maps together | | | | 273 | 184.6 | | | | |
| **all six** | | | | **892** | **351.3** | | | | |

M09's size is its characters' line definitions (`Dialog/AllLevels/Oneliners`: 487 blocks 52 MB in
A, 446 / 51 MB in B) and the music (53.7 MB in A, 39.7 MB in B) and B's two ambience sets (27 MB).

ASSUMPTION in the selection: for the two story levels "map-side" is everything outside the
systems, which is MORE than `kl_maps.campaign_drop` + `kl_fa_author.CAMPAIGN_KEEP` leave: all
eight `PlayMusic` objects, the cut-scene sounds (`M09A_Intro`, `M09A_Enter_Elevator`,
`M09A_Scar_Retomoto`, `M09_Tokyo_Exit`: 0.9 MB) and every squad's lines come along. Deliberate: the
authored layer picks from the campaign's objects and will pick more; the cost over the exact
kept set is the rooftop and rappel music (28 MB) and little else.

### 3.2 `merge(base, dm, want, out, prior=None)` - append only

1. Copy the base from 0 to the end of its last data block (a multiple of 0x100). Nothing the
   base holds moves: every offset a stock Dog Days .WHD holds stays valid.
2. Append the wanted Dead Men blocks, each on a multiple of 0x100, in Dead Men file order, whole
   (LIP block, audio, tail), byte for byte. Nothing is re-encoded.
3. Write one format table, one name table and one sorted index for all clips: the base's keep
   their ids, the new ones follow. All clips of a block are entered, the set entry included.
4. Write `<out>.map.json`: `{Dead Men block offset: [new offset, bytes]}` = the form
   `kl_snd.stream_map()` reads.

Header: the base's, with index offset and count replaced; build id unchanged (4c08b8d5).

Two bases:

| | `build` (base = stock) | `build --extend` (base = the current merged file + its map) |
|---|---|---|
| output | `<work>\build\str\PC_Def.str` | `<work>\build\str\extend\PC_Def.str` |
| size | **1,586,585,559** (+351.6 MB over stock; 11 MB more than the installed file) | 1,684,486,009 (+104.0 MB over the installed file) |
| Dead Men blocks | 892, the needed ones | 2,010 = 1,944 old + 66 new |
| clips in the index | 8,001 | 10,071 (the old sets completed: 969 entries added) |
| dead bytes | 0 | 0.68 MB (the old tables) + 0.39 MB of them read as tails |
| levels built against the old map | **stale: rebuild them** (every Dead Men clip has a new offset) | stay valid |
| reproducible from the two games' own files | yes | only with the old file and its map |

Recommended: the stock-based file, swapped in together with its map at a moment when no build
is running, followed by a rebuild of whatever is installed (section 6). `--extend` is there for
"must not disturb builds in flight".

### 3.3 Codecs that come along (not solved here)

Dead Men's formats are copied. Of the 892 blocks: 591 PCM sets, 55 single PCM, 41 Vorbis,
**205 ADPCM** (10 / 20 / 20 / 7 in the FA maps, 170 in M09_A, 159 in M09_B: Japanese guard and
police one-liners, screams, `Bomb_WarmUp`). Dog Days ships PCM singles, PCM sets and Vorbis, but
**no streamed ADPCM and no X / X_R set** (its one PCM set is three stereo music layers at one rate).
Whether its stream player decodes ADPCM and de-interleaves a 2 : 1 mono pair is LIVE. If ADPCM
is silent or noise: re-encode those 205 as PCM in `merge()` (`kl_audio.ima_to_pcm` exists) and
have `kl_snd.merge` write the record as PCM (format low word 1, bits 16, PCM size, block fields
0) - a change in two files; ADPCM is 4 bits a sample, so those clips (5.2 MB in M09_A alone) grow
fourfold.

## 4. Retomoto Tower: music, the blast, ambience

### 4.1 The clips (Dead Men PC_Def.str; all in the new merged file)

| piece | set entry (codec 0x1a) | layer 1 | layer 2 | length | form |
|---|---|---|---|---:|---|
| **action theme** (tower, from the window blast) | `LevelSetup/Level/M09_A/Music/TokyoAction1` @0x2f29db00 | `Music/InHouse/Japan/M09_A/TakyoAction_V3_44_Layer1_Loop.wav` | `.../TakyoAction_Layer2_TAmbient_Loop.wav` | 211.2 s | PCM set, 2 x stereo 32 kHz, 25.8 MB |
| roof | `.../Music/M09A_Rooftop` @0x162dd900 | `.../Rooftop_V2_New_44_Layer1_Loop.wav` | `.../Rooftop_Layer2_TAmbient_Loop.wav` | 220.7 s | PCM set, 26.9 MB |
| **street theme** (M09_B) | `.../Music/TokyoAction2` @0x3cd3f600 | `.../TokyoAction2a_MainGuitar_Layer1.wav` | `.../TokyoAction2b_MainGuitarEtnic_Layer2.wav` | 114.0 s | PCM set, 13.9 MB |
| rappel | - @0x5877c00 | `.../TokyoRappel_Loop_V2_44_Wind.wav` | - | 139.2 s | Vorbis stereo, 1.0 MB |

So "15 clips under Music/InHouse/Japan" = these 7 + 8 of `Music/InHouse/Japan/M05_A/` (two
four-layer club pieces of another level); "LevelSetup/Level/M09_A" in the stream file = the three
set entries above + three cut-scene sounds. In each piece **layer 1 is the driving layer, layer 2
('TAmbient', 'Etnic') the tension bed**; the two are one interleaved block and stay in step.

Sound objects (what a field holds), `kl_str.MUSIC` / `kl_str.music_roots(level)`:
M09_A 0x986e0 `levelsetup/level/m09_a/music/tokyoaction_v3_44_layer1_loop`, 0x987b0
`tokyoaction_layer2_tambient_loop`, 0x98a50 `rooftop_v2_new_44_layer1_loop`, 0x98b20
`rooftop_layer2_tambient_loop`, 0x988c0 `tokyorappel_v2_wind`; M09_B 0x9a420
`tokyoaction2a_mainguitar_layer1`, 0x9a4f0 `tokyoaction2b_mainguitaretnic_layer2`, 0x9a680
`tokyoaction_v3_44_layer1_loop`.

### 4.2 How the campaign plays them (M09_A / M09_B .prp, MEASURED)

`PlayMusic` (class `ZPlayMusic`, 14 fields, the same in both games): [3] a time in seconds
(2 - 5; ASSUMPTION: fade-in), [5]..[8] up to four layer sounds, [9] `EMusicLayersStart` flags
(which layers start), [10]..[13] each layer's start volume in dB (-100 = silent).
`PlayMusicLayerFade` on child boxes: [0] layer, [1] seconds, [2] target dB.
Every `Music!NN_*` object is a `TriggerDelay` that the level's scripts fire and that names a
`PlayMusic` or some of its fade children.

M09_A:

| object | what it does |
|---|---|
| `Music!PlayMusic_Rooftop` | layers 1 + 2, start -100 / -3 dB (bed only). `01_Start` starts it; `02_FirstShot`: layer 1 -> -2 dB in 2 s, layer 2 -> -15 in 5 s; `03_AllDead`: layer 1 -> -100 in 10 s, layer 2 -> -5 in 3 s |
| `Music!PlayMusic_Rappel` | one layer at -3 dB, [3] = 3; started by `05_RappelAnimation` |
| **`Music!PlayMusic_TokyoAction`** (22 fade children) | layers 1 + 2, start **-2 / -100 dB** (action only). Started by **`06_Explosion`** = the window blast (`Timer_ExplosionDelay_Kane`) |
| `06b_AlmostDead` | layer 1 -> -4 dB in 5 s |
| `07_SecureTheRoom` | layer 1 -> -100 in 8 s, layer 2 -> -5 in 3 s (boardroom cleared: bed only) |
| `09_Explosion` | layer 1 -> -2 in 1 s, layer 2 -> -17 in 1 s; + 37 s -> `10`: layer 1 -> -100 in 30 s, layer 2 -> -4 in 10 s |
| `10b_TopFloor`, `11_EnEtageNed`, `13_EnEtageNed` | per floor: layer 1 -> -4 / -5 in 5 s, layer 2 -> -17 in 7 s; the first two + 37 s -> layer 1 out in 30 s, layer 2 -> -4 in 10 s |
| `14_AllDead` (the elevator squads' counter), `15_EnterElevator` | both layers -> -100 in 25 / 35 s and 5 / 7 s |

So one piece runs from the blast to the elevator and the script only moves the two faders: fight
= layer 1, lull = layer 2.

M09_B: `Music!PlayMusic_Start` (street theme, -3 / -100 dB, [3] = 4) started by `01_FirstShoot`
(2 s); `02_NewObjective`: layer 2 -> -5 in 3 s; `03_LeavingSquare`: both out in 30 s, then 31 s
later `PlayMusic_Tom` ("tom" = empty: a `PlayMusic` with no sound = music off);
`PlayMusic_Overpass` (street theme, -100 / -3 dB: bed only) from `05_StreetMusic`;
`PlayMusic_End` (action theme layer 1 alone at -1 dB, [3] = 5) from `10_FirstShoot`, faded to -5
after 20 s and -7 after 40 s.

### 4.3 The blast and the ambience

| sound | clip | where | state |
|---|---|---|---|
| window explosion | `SFX/Explosions/Bomb/M09_Explosion_Window_Office/M09_Explosion_Window_Office_01.wav` | stream, Vorbis stereo 16.2 s (the long roar and debris) | in the old and the new file |
| bomb warm-up | `SFX/Explosions/Bomb/Bomb_WarmUp/Bomb_WarmUp.wav` | stream, **ADPCM** mono 2.7 s (re/retomoto.md says in memory: it is streamed) | new; codec risk 3.3 |
| glass | `Glass_Break_Big`, `Glass_Break_Small`, `Impact_Window_Small_No_FlyIn_04` | in memory (.WAV) | carried by `kl_snd.merge` |
| tower beds | `SFX/Ambiences/M09_A/Inside/Ambience_Atrium_M09`, `.../Ambience_Office_M09`, `SFX/Ambiences/M09_A/Outside/Ambience_Rooftop_M09`, `Panic_Boardroom_01` | stream | first three new |
| tower voices | `EmergencyAnnounce_Japanese_Male_01`, `GuardsBreakDoor_01`, `GuardsShoutAndShoot_01`, Japanese guard lines | stream | new |
| lobby | set `LevelSetup/Level/M09_B/Ambient/Inside/Inside` = `CrowdLobby_01` (stereo 32 kHz) + `Lobby_01` (stereo 16 kHz) | stream, PCM set 13.5 MB | new |
| street | set `.../Ambient/Outside/Highway_Busteminal` = `Highway_Distance_mono_01` + `100_Bullets_Tokyo_Street_02`; `100_Bullets_Tokyo_Street_01` | stream, 13.5 + 1.1 MB | new |
| police megaphone | `Dialog/M09/Dialogue/M09B_OneLiners/PoliceWarning/PoliceWarning_010..050_JapanesePolice` | stream | new |

`kl_graft.verify`'s "15 stream clips are not in the merged stream file" goes to 0 with the new
file (test 3 below: 0 missing for M09_A and M09_B).

## 5. Level music in a Fragile Alliance round

Stock: no FA level of either game has a `PlayMusic`; Dog Days' settings field 157 is 0 in 9 of 9.
Dead Men's FA maps use the settings (their field 149). Both routes exist in kl2.exe:

### 5.1 `PlayMusic` (EXE) - recommended

- `ZPlayMusic` vtable 0xbc38fc. Its message handler (slot 26, 0x72fde0) accepts exactly two
  messages, registered from "ff2\levelsetup\playmusic.cpp": **'AITrigger'** (id at 0x1689760,
  0x4618f7) and **'Activate'** (0x168975c, 0x461926); both call the start routine 0x8e7dd0.
- 0x8e7dd0 needs the sound system (`[0xdd2640]+0xb00`) and nothing else: no game-mode object is
  read. It keeps the playing `PlayMusic` in a static (`[0x1689764]`), so starting a second one
  replaces the first (that is how the campaign's pieces follow each other), and plays a sound
  member (`+0x34`; ASSUMPTION: field 0 or 1, 0 in every Retomoto object) as a one-shot. The only gate is `[0x1689768] != 0`, a global
  that is read in two places and **written nowhere** in the retail exe.
- Init (slot 13, 0x675710) only clears the static.

So `re/retomoto_fa.md`'s ASSUMPTION "'AITrigger' from the blast timer starts it" is what the exe
does. Nothing has to be authored beyond what `kl_fa_author` already keeps
(`Music!PlayMusic_TokyoAction`, sent 'AITrigger' by the blast `TriggerDelay2`). What was missing
was only the clip. To make the music follow the round the way the campaign does - optional, each
line is a name in an existing list of `tools/kl_fa_author.py`:

    # part 2 gets the street theme (it replaces the action theme when it starts)
    CAMPAIGN_KEEP[PART_B] += ('Music!PlayMusic_Start',)
    #   ... and R + 'Music!PlayMusic_Start' in the targets of the street starter (tbExitFinancialAlley)
    # the tower calms down when the main room is cleared: the campaign's own fade pair
    CAMPAIGN_KEEP[PART_A] += ('Music!07_SecureTheRoom',)          # a TriggerDelay -> 07_Layer1, 07_Layer2
    #   ... and R + 'Music!07_SecureTheRoom' in the 'room cleared' counter's targets, beside the ActivateGeom

(The fade boxes are children of `Music!PlayMusic_TokyoAction` and stay with it.) LIVE: that a
`TriggerDelay2` / `TriggerCounter` of an FA round delivers 'AITrigger' to these objects like any
other target; and section 3.3 (the pieces are PCM sets, which Dog Days ships for music).

### 5.2 Settings field 157 (EXE) - the fallback

- `ZOnlineFragileAllianceSettings` Init (0x88d780) at 0x88edba passes field 157 (member +0x2a0)
  to 0x8736d0: `gamemode[0x168e958]+0x944 = sound`, then 0x8ce720: stop what `+0x950` holds
  (0x7d9560), **play the sound at once** through `ZDllSound` slot 75 (0x589670: creates the
  instance, 2-D, returns its handle), keep the handle in `+0x950` and clear the instance's flag
  0x2. Fields 158 / 159 go to `+0x948` / `+0x94c` (0x41c7d0).
- The only other caller of 0x8ce720 is 0x67f0a9, inside the routine that speaks the 'Backstab'
  lines (0x67ee80), on the branch for the local player: one-shot `+0x94c` (field 159, the
  traitor sting), then `0x8ce720(+0x948)` = **the music is replaced by field 158**. In stock F07
  field 158 is 0: the music would stop for good when the player turns traitor.
- The game mode's destructor (0x404110) stops it.

So field 157 is "music from the moment the level is loaded" (briefing included - not "as the
window blows"), one sound, no layers, no fades. It does not need any message to arrive, which
is why it is the fallback. Lines for `tools/kl_graft.py` `build()`, at the `graft_audio` call
(line 909 today), before `Jn.p.serialize()`:

    import kl_str
    more = kl_str.music_roots(m_name)[:1] if music_157 else []      # the theme's layer 1; [] = leave the field alone
    audio = kl_snd.graft_audio(s_name, m_name, Jn, [mj[k] for k in sorted(m_nodes)], log, more_roots=more, loc=loc) if sound else None
    if audio and more and audio.map.get(more[0]):
        for field in (157, 158):                                    # 158: or the traitor event ends the music
            kl_str.set_fa_music(Jn, audio.map[more[0]], field, log)

`set_fa_music` was run on stock F07's tree (field 157 read back as written, 340 fields kept). In
the chain F07 + M09_B + M09_A the M09_A step writes last, so the action theme wins. ASSUMPTIONS:
one layer of a two-layer set plays alone (Dead Men's own FA maps do exactly that: M03_FA_A's
field 149 is `m02_training_fight_layer2_drums_loop`); the sound loops by its own parameters.
**Use one route, not both**: the two do not know of each other and would play together.

## 6. Installing (the live agent's step; nothing was installed by this job)

State today: `DD\PC_Def.str` is the earlier merge; **the original is already in
`DD\KL_PortBackup\PC_Def.str`. Do not move or copy anything into KL_PortBackup** - the file that
stands in the game folder is a build product, not an original.

Stock-based file (recommended), with no build running:

1. `python tools/kl_str.py build` -> `<work>\build\str\PC_Def.str` + `.map.json` (expect RESULT: PASS).
2. Copy both over `<work>\build\PC_Def.str` and `<work>\build\PC_Def.str.map.json` (keep the old
   pair aside as `PC_Def.kl_audio.str` / `.map.json` if wanted; they can be rebuilt with
   `kl_audio.py merge`). From here `kl_snd.stream_map()` hands out the new offsets.
3. Rebuild the level(s) to be tested (`kl_graft` / `kl_fa_author`): their .WHD records must hold
   the new offsets. A level built before step 2 points into the wrong clips of the new file.
4. Copy `<work>\build\PC_Def.str` to `DD\PC_Def.str` (replace; 1,586,585,559 bytes) and install the
   rebuilt level into the F01 slot. `kl_package`'s `_backup_then_copy(dd, 'PC_Def.str', merged)`
   does the copy and leaves the existing backup alone.
5. `tools/RESTORE Dog Days originals.bat` puts the original back as before.

With `build --extend` instead: steps 1, 2 (from `build\str\extend\`), 4; step 3 is not needed for
levels that only use clips the old file had.

First things to listen for (in this order): a Dog Days line (stock offsets untouched) - a Dead
Men voice line of the briefing (PCM X / X_R set) - the window explosion (Vorbis) - the action
theme at the blast (PCM set of two stereo layers) - `Bomb_WarmUp` or a Japanese guard shout
(ADPCM).

## 7. Tests (all run 2026-10-09)

`python tools/kl_str.py test`:

1. **Stock files read completely**: the 9 files of 1.1, every byte accounted for, 0 problems; the
   earlier merge is read too and reported (845 incomplete sets, 84.6 MB no entry names).
2. **Merge for the six maps, stock base**: 892 blocks / 2,075 clips added behind 0x4888d700;
   re-read: all bytes accounted for (0 dead, 0 tail), index sorted, ids 0..8000, bytes
   0x38..0x4888d700 hash-equal to stock, 5,926 stock clips found by name with offset, size, format
   and lip word unchanged, 892 blocks byte-equal to Dead Men's, 2,075 entries as Dead Men has them.
3. **Every stream record of the grafted levels' merged banks resolves** (`check_levels`: stock F07
   + each level through `kl_snd.merge` with the new map):

   | level | PC_Def stream records in the merged .WHD | added | name no block | larger than their block | clips missing |
   |---|---:|---:|---:|---:|---:|
   | M01_FA_A | 4,066 | 436 | 0 | 0 | 0 |
   | M02_FA_A | 4,072 | 442 | 0 | 0 | 0 |
   | M03_FA_A | 4,078 | 448 | 0 | 0 | 0 |
   | M06_FA_A | 4,055 | 425 | 0 | 0 | 0 |
   | M09_A | 4,516 | 886 | 0 | 0 | 0 |
   | M09_B | 4,432 | 802 | 0 | 0 | 0 |

   Build ids: merged bank 4c08b8d5 = merged stream file 4c08b8d5, six of six.
4. **The same with `--extend`** (base = the installed merge + its map): 66 blocks / 969 index
   entries added behind 0x5ddd2a00, 10,071 clips; re-read: 0 problems, 9,102 old entries
   unchanged, 2,010 placed blocks byte-equal to Dead Men's (the cut block 0x5f27300 up to where
   the old file has it), 0.68 MB dead + 0.39 MB read as tails (the old tables); the six banks: the
   same table as above, 0 / 0 / 0 in every row.

Not tested: anything in the game. Limits of the tests: they prove the file is well formed by the
rules the stock files obey and that every offset a level will hold is a block start with enough
bytes; they cannot prove the stream player accepts Dead Men's codecs (3.3) or that the index is
unused (1.4).

## 8. For the lead: other files

- `tools/kl_snd.py`: `stream_file()` / `stream_map()` keep working as they are once the new pair
  stands at `<work>\build\PC_Def.str(.map.json)`. Its messages name `kl_audio.merge`; the tool is
  `kl_str.py build` now. If ADPCM has to be re-encoded (3.3): `merge()`'s `stream_rec` must write
  the PCM form of the record.
- `tools/kl_graft.py` `build()`: the five lines of 5.2 behind a switch (default off).
- `tools/kl_fa_author.py`: the optional names of 5.1.
- `tools/kl_audio.py` `merge()` is superseded (name filter, incomplete sets, cut tail); its
  `StreamFile`, export and `ima_to_pcm` are still the tools for listening to clips.
- re/retomoto.md 6: `Bomb_WarmUp` is a streamed ADPCM clip, not in-memory; "15 clips under
  Music/InHouse/Japan" = 7 of M09_A + 8 of M05_A.
- re/audio.md 3: the open question "codec from the .WHD record or from the stream file's index"
  now leans to the record (1.4), still unproven.
