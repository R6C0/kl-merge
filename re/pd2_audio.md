# Payday 2 audio streams for the Kane & Lynch music merge

Research note, 2026-10-10 (Payday 2 Steam build 25506656 at `C:\Steam\steamapps\common\PAYDAY 2`,
read through `tools/pd2_crate.py`). Tool: `tools/pd2_audio.py` (`survey`, `banks`, `tracks`, `info`,
`wav`, `rms`). All numbers below were measured on this machine; outputs live under
`<KL_PortTools>\pd2\audio\` (stream_headers.json, track_streams.json, track_names.json, wav\*.wav,
music.bnk, menu.bnk, music_alesso.bnk, tweakdata.luajit). Nothing was installed or run in a game.
ASSUMPTIONS are labelled; everything else is read from the files.

## 1. What a `.stream` is: a Wwise .wem, and the codec is PTADPCM, not IMA

The crate index has 74,437 entries of extension `stream`, every one under `soundbanks/streamed/<bank>/<id>`
(227 bank folders), 6,743,467,461 bytes raw, none zlib-stored. Each is RIFF/WAVE with chunks
`fmt ` (24 bytes; 66 for Vorbis), `hash` (16: 'hash' + 12 bytes; ASSUMPTION: Wwise's source-file digest),
`junk` (12, zero; absent on Vorbis) and `data`; short stingers also carry `cue ` (28) and `LIST` (20) between hash and junk. The fmt header of all 74,437 (`pd2_audio.py survey`, 15 s):

| tag | channels | rate | bits | block align | cbSize | count |
|---|---|---|---|---|---|---|
| 0x8311 | 1 | 32000 | 4 | 36 | 6 | 29,387 |
| 0x8311 | 1 | 44100 | 4 | 36 | 6 | 28,345 |
| 0x8311 | 1 | 36000 | 4 | 36 | 6 | 6,672 |
| 0xFFFF | 1 | 48000 | 0 | 0 | 48 | 4,758 |
| 0xFFFF | 1 | 44100 | 0 | 0 | 48 | 2,449 |
| 0x8311 | 2 | 44100 | 4 | 72 | 6 | 995 |
| 0x8311 | 2 | 32000 | 4 | 72 | 6 | 868 |
| 0x8311 | 2 | 36000 | 4 | 72 | 6 | 376 |
| 0xFFFF | 1 | 36000 | 0 | 0 | 48 | 262 |
| 0x8311 | 1 | 28000 | 4 | 36 | 6 | 149 |
| 0xFFFF | 2 | 44100 | 0 | 0 | 48 | 76 |
| 0xFFFF | 1 | 32000 | 0 | 0 | 48 | 75 |
| 0xFFFE | 1 | 44100 | 16 | 2 | 6 | 15 |
| 0x8311 | 2 | 28000 | 4 | 72 | 6 | 7 |
| 0xFFFF | 2 | 48000 | 0 | 0 | 48 | 2 |
| 0x8311 | 4 | 36000 | 4 | 144 | 6 | 1 |

Totals: **0x8311 = 66,800** (4-bit, 36 bytes per channel per block), **0xFFFF = 7,622** (Wwise Vorbis; voice
lines: robbers_mission_gen 2,069, the char_* heister banks, regular_vox), **0xFFFE = 15** (plain 16-bit PCM:
ambiences, hud). The extra 6 bytes are `u16 0, u32 channel config`: 0x4101 mono (1 channel, type 1, mask
0x4 FC), 0x3102 stereo (mask 0x3 FL FR).

**The earlier reading "tag 0x11 = IMA ADPCM, block 0x24" was wrong**: the tag is 0x8311 (decimal 33553),
only its low byte is 0x11. 0x8311 is Wwise's **PTADPCM** ("Platinum ADPCM", the codec that replaced IMA in
Wwise 2019.2; the banks are version 145 = Wwise 2021.1). Proof from the data, not the tag: a 36-byte block
is `{s16 hist2, s16 hist1, u8 index, 31 bytes = 62 nibbles}` = 64 samples. Over the first 5,000 blocks of
`music/… ` and `robbers_mission_gen/41849207`: byte 4 never exceeds 12 (PTADPCM's table has 13 rows) and
byte 3 is not zero (an IMA block has `{s16 sample, u8 step 0..88, u8 0}`). Stereo = frame L then frame R
inside one 72-byte block.

Decoder (vgmstream `src/coding/ptadpcm_decoder.c`, "reverse engineered from .exes"; its 16x16x2 table is
copied into `pd2_audio._T`): `sample = clamp16(step + 2*hist1 - hist2)` with
`(step, next index) = TABLE[index][nibble]`, low nibble first, the two header samples output first.
Duration = `data bytes / block align * 64 / rate`.

Verification of my implementation: on `music/121224598` (203,174 block boundaries per channel) the mean
|x[n] - x[n+1]| ACROSS block boundaries is 16.7 / 17.9 (L / R) against 16.7 / 18.0 inside blocks, with
zero boundary jumps over 2000. A wrong table or formula drifts inside each block and jumps back at the
next header; this one does not. Pure Python decodes 13 M stereo frames in 3.5 s.

## 2. Which streams are music, and their names

The 781 streams of `soundbanks/streamed/music/` are 2,392.6 MB (679 stereo 44.1 kHz, 99 stereo 32 kHz,
3 mono 32 kHz; 20 over 10 MB, 300 over 3 MB; the largest 14.6 MB = 294.9 s). Other music-like folders:
`music_alesso` 60 / 26.3 MB, `menu` 103 / 26.7 MB, `club_music` 23, `safehouse_music` 50, `bex_mariachi`
50, `christmas_2013`, `halloween_*`. The 29,542 `regular_vox` and the `job_*` folders are dialogue.

Names come from three files, joined by hashes (`pd2_audio.py banks`):

1. `lib/tweak_data/tweakdata.lua` (LuaJIT bytecode; its constant strings) holds `track_list`: `track_01`
   .. `track_81`, `track_32/33/34/62/64_lcv`, `track_47_gen`, `track_pth_01..09` (90 names), the music
   events `music_heist_setup/control/anticipation/assault`, `music_stealth_*`, `music_stress_*`,
   `music_hit_*`, and unlock locks `{track, lock}`: track_09 armored, 11 infamy, 12 deathwish, 14 bigbank,
   17 assault, 18/19 miami, 24 diamond, 25 thebomb, 29 kenaz, 40/41 peta, 42/43 pal, 45/46 born,
   track_pth_01..09 payday (the PAYDAY: The Heist tracks).
2. `soundbanks/music.bnk` (1.94 MB; BKHD version 145, DIDX 323 embedded short sounds, HIRC 2,345 objects:
   193 x type 3, 97 x 4, 790 music segments (10), 790 music tracks (11), 9 music switch containers (12),
   464 playlists (13), 2 x 14). Four of the nine switch containers (ids 15731868, 862251872, 899948598,
   966935551; ASSUMPTION: the heist / stealth / stress / hit event sets) have a decision tree whose keys
   are the FNV-1 32-bit hashes of the track names (Wwise's name hash); the u32 four dwords after a key is
   the playlist. From a playlist, every u32 that is the id of another playlist / segment / track object is a
   child, and a track's u32s that are stream ids are its sources (a brute-force reference scan: no
   per-version HIRC record layout was decoded). All 90 tracks resolve to 4-10 streams each: 656 distinct
   streams, 652 of them in `music/` (1,788.9 MB). The remaining 129 `music/` streams are menu / loot-drop /
   unreferenced-here material (not followed).
3. `strings/menu.strings` (and `strings/hud.strings` for two): Diesel string tables, `u64 0, u64 n, u64 n,
   u64 0x38, 16 bytes, n x 32 {u64 key idstring, u64 0, u64 value offset, u32, u32 0}`, UTF-8 NUL-terminated
   values after the table (menu: n = 13,214, first value at 422,904 = exactly 0x38 + 32 n). Key =
   `hash64('menu_jukebox_' + track)`.

Result (full list: `python tools/pd2_audio.py tracks`; sizes are the PTADPCM bytes of all a track's
streams, time their summed length):

| track | name | streams | MB | s |
|---|---|---|---|---|
| track_01 | Black Yellow Moebius | 8 | 16.9 | 340 |
| track_02 | Full Force Forward | 7 | 22.7 | 457 |
| track_03 | Fuse Box | 7 | 16.9 | 342 |
| track_04 | Razormind | 7 | 15.7 | 317 |
| track_05 | The Mark | 7 | 25.2 | 509 |
| track_06 | Calling All Units | 8 | 13.5 | 273 |
| track_07 | Tick Tock | 8 | 12.8 | 259 |
| track_08 | Time Window | 4 | 13.6 | 275 |
| track_09 | Armed To The Teeth | 8 | 18.5 | 374 |
| track_10 | Sirens In The Distance | 7 | 24.0 | 484 |
| track_11 | Wanted Dead Or Alive | 6 | 16.2 | 326 |
| track_12 | Death Wish | 7 | 16.7 | 337 |
| track_13 | Shadows And Trickery | 6 | 19.9 | 402 |
| track_14 | Ode To Greed | 10 | 26.0 | 525 |
| track_16 | Where's The Van | 7 | 16.5 | 333 |
| track_18 | Evil Eye | 8 | 21.6 | 434 |
| track_19 | Hot Pursuit | 6 | 13.4 | 269 |
| track_20 | The Gauntlet | 7 | 18.9 | 381 |
| track_21 | Something Wicked This Way Comes | 9 | 16.7 | 337 |
| track_22 | Clowns Are Scary | 7 | 16.3 | 330 |
| track_24 | Breach 2015 | 6 | 29.9 | 602 |
| track_27 | Backstab | 7 | 15.3 | 308 |
| track_29 | Dead Man's Hand | 7 | 18.5 | 372 |
| track_31 | Gun Metal Grey 2015 | 7 | 20.2 | 408 |
| track_36 | Donacdum | 8 | 18.1 | 366 |
| track_pth_01 | Gun Metal Grey | 6 | 18.2 | 366 |
| track_pth_09 | Breach of Security | 6 | 19.7 | 398 |

"Criminal Intent" is a string in strings/menu but is NOT a jukebox track in this build (the jukebox has
no `menu_jukebox_*` key for it; the word pairs `criminals_ambition_instrumental` etc. in tweakdata are
the soundtrack-DLC listing, not music.bnk tracks). The per-track streams are the four event layers plus
stingers, e.g. Razormind: 152.7 s + 58.2 s x 2 + 43.6 s + 1.8 s x 2 + 0.5 s; Death Wish: 155.4 + 73.1 +
54.9 + 29.7 + 18.3 + 3.1 + 2.3 s. The longest stream of a track is its assault layer (ASSUMPTION from
the RMS: the 152.7 s Razormind stream is loud throughout, the 294.9 s `121224598` of Breach 2015 is
quiet, RMS 70-870, i.e. a control / stealth layer). Which stream is which layer is in the segment
structure, not read.

Heist -> track defaults are NOT in the data looked at: `levelstweakdata.lua` names only `track_47_gen` /
`track_47_flat` (the help heist) and `track_01` as a death_track. In this build any track can be chosen
per heist from the jukebox, so there is no fixed heist -> music mapping to recover.

## 3. One stream decoded

`python tools/pd2_audio.py wav soundbanks/streamed/music/312174304 <out.wav>` (Razormind's main layer):
PTADPCM stereo 44.1 kHz, 7,577,280 data bytes = 105,240 blocks = 6,735,360 frames = **152.73 s**, written
as 26,941,484 bytes of 16-bit PCM (`<work>\pd2\audio\wav\razormind_312174304.wav`). RMS per 30 s: 6131,
4682, 5363, 5613, 6090, 6344 (of 32767): music, no silence, no drift. Also decoded: `543863200` (Breach
2015, 219.4 s, RMS 6000-7800 throughout) and `121224598` (294.9 s, quiet layer, peak 8436). A PCM
(`ambiences/741104302`, 4.0 s) parses too; a Vorbis stream (`robbers_mission_gen/229440917`) reports its
header only.

## 4. Feeding it to the Kane & Lynch stream file

What `tools/kl_str.py` / `kl_audio.py` establish about Dog Days' `PC_Def.str`: codecs are 2 = PCM 16 bit
(format entry: `u32 2, samples, channels, rate, 16, 8 junk, u32 frame bytes`), 3 = IMA ADPCM block 0x400
(Dead Men only, never shipped by Dog Days, untested there), 4 = Ogg Vorbis, 0x1a = interleaved set.
Stock Dog Days music is PCM sets of 2-3 stereo layers at 32 kHz or Vorbis; the level's .WHD record carries
offset, size, rate, channels and codec (nothing in the engine resamples).

So a Payday 2 track goes in as `pd2_audio.py wav` writes it: **interleaved 16-bit PCM, stereo, its own
rate (44,100 Hz)**, as codec 2, one block per layer (or one PCM set of layers if the FA music controller
should fade between them the way Retomoto's two-layer sets do). The Wwise PTADPCM blocks can not be
appended as they are (no Glacier codec plays them) and the 7,622 Vorbis voice streams would need ww2ogg /
vgmstream (Wwise Vorbis carries stripped codebooks) - not music, not needed.

GAP: `kl_str.merge(base, dm_path, want, out)` copies whole blocks out of a Dead Men `.str` and has no
entry for an external clip. Needed: a `merge_external([(name, pcm bytes, channels, rate)])` that writes
a 0x100-aligned block without a LIP header, a 32-byte codec-2 format entry and an index row, and then
a .WHD record + sound definition on the level side (`kl_snd`; `kl_str.set_fa_music(sc, offset)` already
points the FA music field at a stream offset). The .map.json convention (Dead Men offset -> new offset)
does not fit an external clip; a name-keyed entry is wanted. None of that is written.

Size: PCM at 44.1 kHz stereo is 176.4 kB/s, 4 x the PTADPCM bytes: Razormind's 152.7 s layer = 26.9 MB,
its whole 7-stream set 63 MB, a full track set 50-150 MB; all 90 tracks would be 7.2 GB of PCM
(1,788.9 MB x 4). Dog Days' stock file is Vorbis for most music for that reason; a Vorbis encoder is not
available in pure Python (no numpy / PIL / ffmpeg assumed), so PCM is the only writable form today.
Resampling 44.1 -> 32 kHz would save 27 % and needs a resampler nobody has written yet.

## 5. Licensing / size note

The music is Starbreeze's / Overkill's commercial soundtrack (Simon Viklund, Gustavo Coutinho, Le Castle
Vania, Carl Norén ...; it is also sold separately as the PAYDAY 2 Soundtrack DLC, and the `_lcv` tracks are
licensed from a third party). Extracted or decoded copies stay in `<KL_PortTools>\pd2\` on the owner's
machine like every game asset here: never committed, never shared, never put in a build that leaves this
PC. Owner-side use (a merged PC_Def.str on the owner's own install, which already owns both games) is the
same footing as the Dead Men merge. A track's PCM cost in the stream file is 27-37 MB per layer at 44.1 kHz
stereo (section 4); the `.str` grows by that per clip and loads from disk, not memory.

## 6. Open

- Layer roles (setup / control / anticipation / assault) per stream: decode the music segment and
  playlist records of HIRC v145, or take the longest stream as the assault layer (ASSUMPTION above).
- `kl_str` external-clip entry point and the level-side record (section 4).
- Loudness: the loud layers are mastered to full scale (Razormind 312174304 and Breach 2015 543863200 both
  peak at 32,768, RMS 4,700-7,800; the quiet 121224598 peaks at 8,436). Dog Days' music gain is set by the
  sound controller, so a level match is a listening job.

## Verification (2026-10-10, second agent; independent scripts, nothing in the tool reused except `Stream.decode`)

Verdict: the format reading, the decoder and the track naming HOLD. Four details are corrected below;
`track_streams.json` carries four false stream ids that should be filtered.

1. **Format tags, re-tabulated on a random 5,000-entry sample** (seed 20261010, read straight from the crates,
   own parser): 0x8311 4,475 (89.5 %; full survey 66,800 / 74,437 = 89.7 %), 0xFFFF 524 (10.5 %; survey 10.2 %),
   0xFFFE 1 (survey 15 = 0.02 %); 0 non-RIFF. Rates and block aligns per tag as in section 1 (mono 36, stereo 72,
   PTADPCM extra `0000 01410000` / `0000 02310000`, Vorbis cbSize 48 with a per-stream extra, PCM block 2). All
   74,437 entries are under `soundbanks/streamed/` in 227 folders, 6,743,467,461 bytes, 0 zlib. CONFIRMED.
2. **Chunk layout - CORRECTED**: `cue ` + `LIST` streams are not rare and not "short stingers": 1,243 of the
   4,475 PTADPCM streams in the sample (28 %) carry them, and on a 600-stream sub-sample those with `cue ` have a
   MEDIAN duration of 2.9 s (max 22.5 s) against 1.4 s (max 98.7 s) without. `LIST` is 30-56 bytes (not 20),
   `cue ` is 28 or 52, and `junk` is a 0-14 byte alignment pad (not a fixed 12) - 12 only in the plain
   fmt/hash/junk/data layout (3,232 of 4,475). Vorbis: fmt 66 / hash / data, as stated.
3. **Decoder, different stream**: Death Wish's longest layer `music/567609487` (tag 0x8311, stereo 44.1 kHz,
   7,710,912 data bytes / 72 x 64 = 6,854,144 frames = **155.42 s**, matching the note's "155.4"), decoded in
   1.6 s, written to `<work>\pd2\audio\wav\verify_deathwish_567609487.wav`. RMS per 30 s 8970, 8257, 6704,
   9097, 9183, 8524, peak 32,768: loud music throughout. Index byte values seen 1..11 (never > 12), byte 3 zero in
   1.2 % of frames (random for a sample byte; an IMA block would be 100 %). The note's "0 jumps > 2000 at block
   boundaries" is a property of the QUIET layer it was measured on, not a decoder proof: on this loud layer 12.6 %
   of boundary steps exceed 2000. The proper control is per-phase: mean |step| at phase 0 (boundary) 943.1 / 1021.3
   (L / R) against 947.7 / 1018.8 at phase 1, 938.1 / 1009.3 at phase 32 and 942.1 / 1014.2 over all inside
   phases; fraction > 2000 at the boundary 0.1256 / 0.1415 against 0.1248 / 0.1389 inside. No boundary anomaly:
   the decoder is right on a loud signal too. Table and formula cross-checked against vgmstream
   `src/coding/ptadpcm_decoder.c` (fetched 2026-10-10): first and last table rows identical, frame = s16 hist2,
   s16 hist1, u8 index clamped to 12, nibbles low first, `sample = clamp16(step + 2*hist1 - hist2)`,
   `samples_per_frame = 2 + (frame_size - 5) * 2` = 64, header samples output first. CONFIRMED.
4. **music.bnk** (own parser): sections BKHD 52 / DIDX 3,876 / DATA 1,614,424 / HIRC 318,309; BKHD version 145,
   bank id 3991942870; DIDX 323 entries; HIRC 2,345 objects {3: 193, 4: 97, 10: 790, 11: 790, 12: 9, 13: 464,
   14: 2}, the walk ends exactly at the section end. CONFIRMED. CORRECTION on the DIDX: 292 of its 323 ids ARE the
   track streams' ids (e.g. 312174304 at DATA offset 466,896, 5,064 bytes; 262 entries are exactly 5,064 bytes):
   they are Wwise PREFETCH heads of the streamed music, not "embedded short sounds".
5. **Track keys**: FNV-1 32-bit (lower case) of the 90 `track_*` names of `lib/tweak_data/tweakdata.lua`
   (LuaJIT `\x1bLJ\x02`, 116,166 bytes; regex over the constant pool gives exactly 90; the other `track_` strings
   are `track_list`, `track_ghost_list`, `track_menu_list`) hit in exactly four of the nine switch containers, at
   byte offsets = 2 mod 4 (packed tree records), and in every hit the u32 four dwords on is a type-13 playlist:
   862251872, 899948598, 966935551 hold all 90 keys, **15731868 holds 89 (no `track_pth_01`)**. The note's
   "all 90 resolve" is true through the union; the four-set reading (heist / stealth / stress / hit) remains an
   ASSUMPTION - the 22 `music_*` event names in the lua are listed, nothing ties a container to one.
6. **Reference walk - CORRECTION**: the "656 distinct streams, 652 in music/" difference is four FALSE ids from
   the brute-force u32 scan, exactly the collision the note warned of: `4016`, `147619`, `2718159`
   (regular_vox) and `377262336` (job_g_hotline). 147619 is "shared" by track_21 and track_52 - the only stream in
   two tracks - which marks it as a field value, not a source. Filter `track_streams.json` to ids whose path is
   under `soundbanks/streamed/music/`; the per-track count stays 4-10 (min track_08 = 4; the tool's docstring says
   "6-10", the note's "4-10" is the measured one). 312174304 is named by exactly one type-11 track object
   (445531387) and belongs to track_04 only.
7. **Names**: `strings/menu.strings` (english, props 0): u64 0, n = 13,214 twice, table offset 0x38, first value
   offset 422,904 = 0x38 + 32 n. `hash64('menu_jukebox_' + track)` gives Razormind (04), Death Wish (12), Full
   Force Forward (02), Breach of Security (pth_09), Ode To Greed (14), Calling All Units (06), Dead Man's Hand
   (29), Black Yellow Moebius (01), And Now We Run (15), Supersledge (17), Ho Ho Ho (23): 88 of the 90 keys are
   there, `track_61` and `track_47_gen` are not (their names 'Trick of the trade' / 'The Take 2016' are in
   `strings/hud.strings`). 'Criminal Intent' exists as a menu value with no jukebox key. CONFIRMED.
8. **Razormind set** re-read from the crates: 152.7 + 58.2 + 58.2 + 43.6 + 1.8 + 1.8 + 0.5 s, all stereo 44.1 kHz
   PTADPCM, 15.7 MB. CONFIRMED. `kl_str.py` does define PCM / ADPCM / VORBIS / SET = 2 / 3 / 4 / 0x1a,
   `merge(base_path, dm_path, want, out_path, ...)` and `set_fa_music(sc, offset, field=157)`: the GAP as stated.

Not re-checked: the HIRC record layouts (no layer roles), the Vorbis streams (not decoded by anyone), whether Dog
Days plays a 44.1 kHz codec-2 clip (never tried live).
