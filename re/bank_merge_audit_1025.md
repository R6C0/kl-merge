# Bank merge audit, 2026-10-25 (read-only; nothing in the game folder was written)

Question: does the .WHD/.WAV merge of the PD2 AKM (stock F01) or of the DM01 door-kick fix break an EXISTING
entry, so that kl2 0x6d2107 (IMA decoder 0x6d2020 writes to 0 after the in-memory fill 0x7a001e / Lock reported
success with a null pointer) follows?

## Verdict: NO structural defect found in either merge

Every check below passed. The hypothesis "the merge corrupts an existing entry" is not supported by the bytes.

### F01 PD2 AKM (stage C:/kl_build_1024/pd2gun_1025a/stage vs base = live = game folder)
Not a growing merge: `kl_gunsnd.rebuild` rewrites THREE records in place (tools/pd2_gun.py build_sound).
- WHD: same length 2,102,064; 18 bytes differ; 22,527 records both sides, same offsets; only the 3 records
  `MG_MiniMi_SPW_Heli_Shot_01/02/03.wav` changed. Fields (old -> new): pcm 0x19000 -> 0x58e4/0x5542/0x525c,
  size 0x6800 -> 0x1800 (6 blocks), samples 0xc800 -> 0x2c72/0x2aa1/0x292e. off, offhi, rate 0x7d00, bits 4,
  ch 1, block 0x400, spb 0x7f9, fmt 0x11, lip, x34..x40 (cd fill) unchanged. T/size/3/4 header unchanged.
- WAV: same length 15,392,912, header {0,size,3,4} intact; 74,503 bytes differ, all inside the three old spans
  (0xac6c10, 0xacd410, 0xad3c10, 0x6800 each; first 0x1800 = new data, rest zero). No other record's data
  changed (mem records whose data differ outside the 3: 0).
- Block headers of the new data: 6 blocks each, step index 0..83 (<= 88), reserved byte 0 (same as the 14,588
  stock blocks: 0 with index > 88, 0 with nonzero reserved byte). samples <= blocks*spb and > (blocks-1)*spb
  (11378 in 5..6 blocks of 2041), pcm == 2*samples (same rule as all 746 stock ADPCM records).
- Invariants over all 746 in-memory ADPCM records, stock and stage: size % 0x400 == 0, off % 16 == 0, no overrun,
  no zero size, no overlap, pcm == 2*samples: 0 violations in both.
- .SND (zip member, same 2,420,320 bytes, T 0x24ec40 unchanged, _LS.SND untouched and still names T): 21 bytes:
  the three heli WAVE objects' +0x18 seconds (1.6 -> 0.35/0.34/0.33) and the three AK47 shot SOUND objects'
  +0x14 wave pointer (AK74 wave 0x70560/0x70690/0x707c0 -> heli waves 0x6f900/0x6fa70/0x6fbe0). kl_snd Snd.walk
  clean() is empty, all 29,076 wave -> record references hit a record.
- Only non-stock feature: three 20,480-byte zero gaps in the WAV (stock gaps are 0 except the two -3072 shared
  spans and a few big jumps). Harmless to the reader (records carry absolute offsets).

### DM01 door-kick merge (live KLExpansion/Maps/DM01 vs *.before-1025dm01fb)
Growing merge (kl_snd.merge): appends 6 records + 6 data spans + wave objects.
- WHD 2,202,784 -> 2,203,648 (+864 = 6 x (name 16..32 + 4 + 0x44 record)). The old bytes 0x10..T are IDENTICAL
  (no existing record changed: changed 0, missing 0, new 6). Terminator moved to the new T (16 zero bytes), size field right.
- WAV 23,263,568 -> 23,362,896 (+99,328 = 0x18400): header size field == file length; old data identical for all
  in-memory records; the 6 new records are 16-aligned, packed back to back from 0x162f950, the last ends exactly
  at EOF (stock rule: WAV ends where the last data ends; F01/F02/F03/F05/F09 stock all tail pad 0). All new block
  headers valid (index <= 88, reserved 0). Record geometry identical to stock (fmt 0x11, 0x7d00 Hz, 4 bit, mono,
  block 0x400, spb 0x7f9, cd-fill x34..x40, offhi 0, pcm == 2*samples, samples in the last-block range).
- _LS.SND: first dword (the level bank's trailer T) 0x29e480 -> 0x29eb70 == the new main .SND header T. Correct.
- Main .SND 2,746,016 -> 2,747,792; kl_snd walk clean, 33,493 wave refs, 0 dangling.

### Stock layout comparison (F01, F02, F03, F05, F09 + DM01 old)
All: first in-memory datum at 16, data packed contiguous (gap 0 for 99 % of records), off % 16 == 0 and never
2048-aligned (so no sector alignment rule), size a multiple of the 0x400 block, WAV length == end of last datum,
records in WHD order have increasing offsets (all but 1-5), pcm % 16 is arbitrary (633 of 746 are not
multiples of 16; 371 are not multiples of 4), so an odd pcm size is normal. Both merged banks keep every one of
these properties. No count/total/stream-region/second-file pointer in the WHD header exists beyond {T, size, 3, 4}
(parse() consumes every byte; the merge tools update T and size).

## What this means for the crash
The Lock wrapper is `_ZSoundBufferDS::LockBuffer` (0x6d67c0): mode != 3 calls IDirectSoundBuffer::Lock(0, 0, ..., flags 2 =
DSBLOCK_ENTIREBUFFER) and the caller (0x79ff50..0x7a00a2, mode 1 = whole clip in one buffer, size [this+8] = record pcm)
only tests the HRESULT. A null ptr1 with S_OK means the DirectSound buffer/voice itself was not backed (buffer-creation
or driver/memory failure), not that the record or its data is wrong: the decoder gets src from the loaded WAV (vtbl+0xa4
of the manager, offset [rec+0x20]) and only the DEST is null. A bad record would fault on the SOURCE or write inside a
valid buffer. Nothing in the three changed records or the six appended ones can produce a null destination.
Caution: the other session's 03:50 note says "every 0x6d2107 followed a sound-bank edit"; the same runs also carried
other changes (klmem reserve, new zip content, DM05A heap pressure), so the correlation is confounded.

## Fix needed in the merge code
None demonstrated. Do not "fix" kl_gunsnd.rebuild / kl_snd.merge on this evidence. Cheap discriminating experiments:
1. Control: run stock F01 with the ORIGINAL bank and the same hook/ini, 60+ s past the stage 0->1 change. If it also
   crashes at 0x6d2107, the bank is innocent (hook/klmem reserve or DirectSound voice exhaustion).
2. A/B on the PD2 stage: ship only the new zip (no WHD/WAV; AK47 sound objects pointing at the untouched heli records).
3. Make the three records geometry-identical to stock (variant, removes every difference except the audio bytes):
   keep size 0x6800, pcm 0x19000, samples 0xc800, write the 6 new blocks then 20 zero blocks (zero blocks decode to
   silence). In kl_gunsnd.rebuild that is `f[size] = old_size` and keep old samples/pcm (a second, optional
   `keep_geometry` flag), plus leave the .SND seconds as they were.
4. Bisect the .SND change: the repointed AK47 sound objects now share the heli wave objects; the stock AK74/AK47/Zastava
   share ONE set of three waves (comment in pd2_gun.py), the heli ones were used by nothing in FA; bots firing AK47s at
   the 0->1 transition (~30 s) are the first to play them.
5. Log the Lock site: hook 0x7a0043 return value and the buffer pointer `[esp+0x20]`, plus `[this+0x78]`, `[this+8]` and
   the record pcm; if `[this+8]` is 0 or the DS buffer pointer `[this+0x43c4]` is null, the voice was never created.

## Follow-up (2026-10-25, merge hardening, no defect found)
- tools/kl_gunsnd.py: `check_bank_preserved` (re-parse; every original record not listed keeps fields and data span byte for byte,
  header/size, 16-aligned block-multiple spans, no new overlaps) now runs inside `rebuild` and in kl_dm01fb_1025.sound (passes on the live DM01 merge).
- `rebuild(keep_geometry=True)` (used by pd2_gun): the 3 heli records keep size 0x6800 / pcm 0x19000 / samples 0xc800 (6 new blocks + 20 zero
  blocks) and the .SND keeps the old seconds => WHD byte-identical to stock d61b9a8a, only WAV spans + .SND pointers differ (audit test 3).
- Stage C:/kl_build_1024/pd2gun_1025b/stage (tag .before-1025pd2gun2). DM01 has no defect, so no dm01snd stage; a sound-only restore would
  leave the new zip's .SND pointing at records the old bank lacks (dangling), so use the full dm01fb UNDO instead.
