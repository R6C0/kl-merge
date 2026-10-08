# Sound banks, voice lines and music: Dead Men -> Dog Days

Track `track-voice`, 2026-10-09. Everything here was measured on the files of this machine: the 21
stock Dog Days levels (F01 from `KL_PortBackup`, F02-F09, L00-L11) and the 20 Dead Men levels, plus
`kl2.exe` where an address is given. Nothing was tried in the game. Statements are marked

- **MEASURED**: counted on files, the count is given;
- **EXE**: read in `kl2.exe` at the address given;
- **ASSUMPTION** / **not established**: a guess, to be settled by a test.

The scripts that produced the numbers are in the session scratch folder `agents/track-voice`
(`snd2.py`, `whd.py`, `loc.py`, `merge.py`, `locmerge.py`, `d1.py`, `e1.py`, `m3.py`); the ones worth
keeping are reproduced in section 9.

## 0. Summary

1. A level's sound is five things: `<L>_Main.SND` (in the zip: the sound project, a pointer image),
   `<L>_Main.WHD` + `.WAV` (wave headers + in-memory wave data, beside the zip), the nine
   `<L>_Main<Language>.LOC` (in the zip: text and, per line, the offset of a sound in the .SND), the
   loading-sound bank `<L>_Main_LS.SND` + `_LS_<Language>.WHD/.WAV`, and the global stream file
   `PC_Def.str` that holds every streamed clip (dialogue, music, long ambiences).
2. **Every sound reference in a level is a byte offset into that level's .SND.** That holds for the
   .prp (property type handler 70 in Dog Days, 65 in Dead Men: 41,435 + 28,455 values, none stray)
   and for the .LOC (398,672 + 294,475 ids, all offsets of a `sound` object). So the bank of a grafted
   level must keep every Dog Days object at its stock offset, and every reference that comes with the
   Dead Men map has to be rewritten to wherever the Dead Men object ends up.
3. The merge is therefore an **append**: stock Dog Days .SND bytes stay put up to the type tables,
   converted Dead Men objects are added behind them, the tables and the trailer are rewritten. A trial
   merge (stock F01 + what M01FAA's map, music and voice lines need) re-parses clean: 0 unclaimed
   bytes, 0 stray pointers, 596 sounds / 594 waves / 24 sets / 3 sequences / 3 definitions added, all
   33,040 wave -> .WHD references valid (section 7). It has not been loaded by the game.
4. Fragile Alliance voice lines are **LOC keys stored as strings in `ZOnlineFragileAllianceSettings`**
   (controller `OnlineFragileAllianceSettings` on `...Settings!GameSettings`): Dead Men fields 12-175,
   Dog Days fields 12-339. Between Dead Men field 19 and 164 the two lists are the same list shifted
   by 8 (section 6). Playing Dead Men's lines = writing Dead Men's keys into the Dog Days slots and
   adding those keys to the LOC.
5. Fragile Alliance music in Dead Men is two sound fields of the same settings object (149 = the
   level's music, 150 = `fa_slashmixprison`). Stock Dog Days FA levels have **no music at all**: no
   `PlayMusic` controller in F01-F09 and field 157 (= Dead Men 149 + 8) is 0 in all nine. Whether Dog
   Days still plays field 157 is not established; the fallback is a `PlayMusic` controller (87 uses in
   the story levels).
6. Hard requirement found in the exe: the .SND carries the build id of the stream file. `kl2.exe`
   0x67e8f8-0x67e90e compares stream-file header +0x10/+0x14 with .SND trailer +0x30/+0x34 and refuses
   the stream file when they differ. Dog Days: `4c08b8d5 00000000`, Dead Men: `46e11c9f 00000000`.
   A Dead Men .SND copied as it is therefore gets no streamed sound; the merged bank keeps Dog Days' id.

## 1. Files

| | Dog Days | Dead Men |
|---|---|---|
| `<L>_Main.SND` in the zip | 1.13-2.46 MB | 1.58-1.73 MB |
| `<L>_Main.WHD` / `.WAV` beside the zip | all levels | all levels |
| `<L>_Main_LS.SND`, `_LS_<Lang>.WHD/.WAV` | 20 of 21 (not L00); Default French German Italian Japanese Russian Spanish | 20 of 20; Default French German Italian Spanish |
| LOC members | 9: English German French Spanish Italian Russian Polish Japanese, Dutch (a 5- or 9-byte stub in all 21) | 5: English German French Spanish Italian |
| stream files named by the .SND | PC_Def Eng Ger Fre Spa Ita Dut Rus Pol Jap (10) | PC_Def Eng Ger Fre Spa Ita (6) |
| stream files on this machine | `PC_Def.str` (1.2 GB), `PC_Eng.str` (56-byte stub) | `PC_Def.str` (1.4 GB), `PC_Eng.str` (stub), `PC_Fre/Ger/Ita/Spa.str` |

English audio lives in `PC_Def.str` in both games (the `PC_Eng.str` stubs hold no clip). The Dog Days
install here has no other language file, so F02's 18,067 language-file records (format bit 0x400000) refer to
`PC_Ger.str` and the like, which are not there (18,024 of their offsets are no clip of `PC_Def.str`).

`Scenes\Locations\F01` in the game folder holds **our** zip but the **stock** `.WHD/.WAV/_LS*` files
(dated Sep 13): only the zip was replaced.

The level loader hands the bank to the sound system `ZDllSound` (vtable 0xb9a3ec) from 0x820739 on:
slot 35 (0x402000) takes the .SND image, slot 36 (0x67e810) the stream file name and checks the build
id, slot 37 (0x805800) the .WHD name, slot 34 (0x701fe0) the .WAV name; the last three only queue
commands 0x102 / 0x101 / 0x100 for the sound thread. The `_LS` names are built at 0x8ffde1-0x90002e
(`<zip name>` + `_LS_` + a string + `.WHD` / `.WAV`, and `_LS` + `.SND`). EXE.

## 2. `.SND`

A memory image used in place: pointers are file offsets, zero = none. No relocation table exists and
the engine adds the base when it follows a pointer (`mov ecx,[eax]; add ecx,eax` at 0x67e8f4), so the
only way to move anything is to know every pointer field. `snd2.py` (section 9.2) does: on all 41
level banks it claims every non-zero byte by a typed item with no overlap (Dog Days 475,903 items,
1,251,457 pointers; Dead Men 392,937 items, 882,228 pointers), every pointer lands on the start of an
item, and moving the whole image by 0x1230 bytes, re-walking it and moving it back gives the original
bytes and the same item and pointer sets, 21 of 21 and 20 of 20. MEASURED. (Limit of that test: a
pointer hidden in a field I treat as a number would survive it. The trailer's group pointer was found
that way only by reading it, so the test is necessary, not sufficient.)

### 2.1 Layout

```
0x00  u32 T         offset of the trailer
0x04  u32 size      file size
0x08  u32 3, u32 4
0x10  stream file names, 16 bytes each (10 in Dog Days, 6 in Dead Men)
...   objects, strings, lists          (creation order, everything 16-aligned)
      material matrix
      type tables, parameter tables
T     trailer
```

Trailer (H = T + 4 + 4 * streams, rounded up to 8: T+0x30 in Dog Days, T+0x20 in Dead Men):

| at | what |
|---|---|
| T+0 | pointer to the material matrix |
| T+4 | pointers to the stream file names, then `cd cd cd cd` |
| H+0 | u64 build id; must equal the stream file's header +0x10 (EXE 0x67e8ff) |
| H+8 | pointer to a group: `audio:groups/sfx_user#group` in 21/21 Dog Days, `audio:groups/sfx#group` in 20/20 Dead Men |
| H+0x10 | 25 x u32 object count, index = object type - 1 |
| H+0x74 | 25 x u32 pointer to that type's table (object pointers) |
| H+0xd8 | u32 0 |
| H+0xdc | {u32 count, u32 pointer} per parameter type 1..33 (Dog Days) / 1..32 (Dead Men); Dog Days then `cd cd cd cd`, 0, 0 |

A type table is not sorted by offset (19 of 187 Dog Days tables are not ascending) nor by name. A
table entry of 0xffffffff (sounds) / 0xfffffffe (waves) marks an object that lives in the `_LS` bank.
A parameter table lists one entry per *use*: in 685 of 693 Dog Days tables (21 files x 33 types, empty
ones included) and 577 of 640 Dead Men tables the entry count equals the number of parameter-list
entries of that type over all objects; the others are off by a few. What the
engine does with either table is not established.

Material matrix: `(N+1) * N` pointers, N = number of object properties + surface properties (Dog Days
7 + 16 = 23 -> 552 pointers, Dead Men 8 + 26 = 34 -> 1190). Every non-zero entry is a `set` or `seq`
(impact sounds per material pair). MEASURED on 41 files by the walker.

### 2.2 Objects

Common head: `+0 u32 type`, `+4 cd cd cd cd`, `+8 name*` (`audio:<path>#<kind>`, lower case), `+0xc
u16 parameter count`, `+0xe cd cd`, `+0x10 parameter list*` (that many parameter pointers).

| type | kind | size DD / DM | fields after the head |
|---|---|---|---|
| 1 | sound | 0x34 / 0x30 | +14 wave* (0xfffffffe = in the `_LS` bank); +18 f32; **DD only +1c f32**; then (DM +1c, DD +20) u16 0, u16 360, u16 360, i16 -60; u32 0; 4 flag bytes; DM 1 byte, DD 3 bytes |
| 2 | set | 0x30 | +14 list* of n object pointers, +18 u16 n, +1a u16 n, +20 u32 (0/1/2) |
| 3 | seq | 0x20 | +14 events*, +18 u16 n, +1a u16 n, +1c u16; event = {u32 kind, u32 time, u32 target}: target is an object pointer for kinds 2, 4, 5, 6 |
| 4 | wave | 0x20 | see 2.3 |
| 5 | def | 0x20 | +14 list* of n object pointers (0 allowed), +18 u16 n, +1a u16 n |
| 7 | roomeffect | 0x50 / 0x70 | different content, see 4 |
| 0x12 | objectproperty | 0x20 | +14 u32 material id, +18 u32 1 |
| 0x13 | surfaceproperty | 0x30 | +14 u32 material id, +18 i32 -10000, +20 f32 1.0 |
| 0x17 | group | 0x50 | +14 list* of n child groups, +18 u16 n, +1a u16 0x28, +1c slots* (u16 count at +22, count x 4 zero bytes), +24/+30 f32, +3c display name*, +40 parent* |

Sound, same-named in M01FAA and F01 (115 names): the 8 cone bytes equal in 87, the last flag byte
(DM +2c = DD +30) equal in 115, the first float equal in 30, the 4 flag bytes equal in 14. So the
fields correspond, the values were retuned. What each means is not established (the cone triple
360/360/-60 is the DirectSound default; the second flag byte is 0-100).

Parameter record: `{u32 type, ...}`, 0x10 bytes; types 5, 0x1b, 0x1d are 0x20, type 0x13 is 0x30.
Pointers: type 0x12 `+4` = group (71,306 of 71,306 in Dog Days), type 0x13 `+0x1c` = an object. Types
in use: Dog Days 1 2 4 5 8 9 d e 12 13 15 16 17 19 1a 1b 1c 1d 1e 1f 21; Dead Men 1 2 3 4 5 6 7 8 9 d
e 12 13 16 19 1a 1b 1d 1e 1f. **Type 0x21 is new in Dog Days (57,054 uses), types 3, 6, 7 are used
only by Dead Men (18,957 / 104 / 326 uses).** What the types mean is not established, except 0x12.

Strings: a sound's `#wave` alias name follows its `#sound` name and nothing points at it.

### 2.3 Waves

| first dword | +0xc | meaning | size |
|---|---|---|---|
| 4 | u16 0/1 | one .WHD record (in memory, or streamed from `PC_Def.str`) | 0x20 |
| 0 | 1 | one .WHD record, streamed | 0x20 |
| 0 | 0xb (0xa) | localized: one record per language | 0x20 + 0x1c * (languages - 1) |

Head: `+0 type, +4 0 (cd cd cd cd for type 4 in Dog Days, junk in Dead Men), +8 file name* (as in the
.WHD, e.g. "Dialog/Multiplayer/You_Esc/YouEsc_04_R_C8.wav"), +0xc flags, +0x10 0, +0x14 .WHD offset,
+0x18 f32 seconds, +0x1c 0`. A localized wave continues with `{u32 0, name*, u32 3 (2), u32 0, u32
.WHD offset, f32 seconds, u32 0}` per further language (the last one without its trailing dword);
an all-zero record = no clip in that language (18 in L06, 6 each in L09 and L11). Languages in stream-name order without
PC_Def: Eng Ger Fre Spa Ita (+ Dut Rus Pol Jap in Dog Days). The first five are the same order in
both games. The **.WHD offset points 4 bytes before the record** (at its zero lead-in).

### 2.4 The `_LS` bank

"LS" = loading sound: `audio:loadingsounds/multiplayer/f02_loadingsound#sound`, in Dead Men
`audio:dialog/loading_sounds/m01_fa_load#sound` plus the loading music. `_LS.SND` = the 16-byte header
(first dword = T of the level's .SND in 20/20 and 20/20) + sound objects (Dog Days 1 or 2, Dead Men FA 2,
Dead Men story up to 36) whose wave is 0xfffffffe and whose **name and parameter list are offsets into
the level's .SND**. `_LS_<Lang>.WHD` (96 bytes Dog Days, 80 Dead Men, in every level) = one record without
a name (16-bit PCM stereo 32 kHz), `_LS_<Lang>.WAV` = its data. How several sounds share that one record
is not established.

## 3. `.WHD` / `.WAV`

`.WHD`: `{u32 T, u32 size, 3, 4}`, then names and records, then 16 zero bytes at T (`_LS`: T = 0, no
terminator). `.WAV`: `{0, size, 3, 4}` + data. `whd.py` parses all 343 files (184 + 159) with every
byte accounted for (anything that is not a name, a record or zero raises) and rebuilds 183 of 184 Dog
Days and 149 of 159 Dead Men files byte for byte from the parsed list; the other 11 differ in the
padding of entries with two or three names (not chased further). All 19,372 + 14,604 in-memory
records have their data inside the .WAV. MEASURED.

Layout rules (from the rebuild): a name starts 16-aligned and takes `len + 1` bytes, padded to 16
(`len + 2` when two names stand together); a record starts at `16n + 4` after 4 zero bytes (an alias
record follows its partner after 4 zero bytes without re-aligning).

Record (dwords):

| # | Dead Men (0x38) | Dog Days (0x44) |
|---|---|---|
| 0 | name offset | same |
| 1 | format | same |
| 2 | sample rate | same |
| 3 | bits (4 = ADPCM, 16, 0 = Vorbis) | same |
| 4 | size as PCM | same |
| 5 | data size | same |
| 6 | channels | same |
| 7 | data offset (.WAV, or stream file) | data offset low |
| 8 | samples | **data offset high** (0 in all 353,434) |
| 9 | block align (0x400 ADPCM) | samples |
| 10 | samples per block (0x7f9) | block align |
| 11 | lip-sync word (0, 4, 0x100004, 0x200004 ...) | samples per block |
| 12-13 | cd / junk | lip-sync word; cd / junk |
| 14-16 | | cd / junk; **two new dwords** (stream records: 0 and 0x10 in 219,147 of 334,062) |

Format: low word 1 = PCM, 0x11 = IMA ADPCM, 0x1000 = Ogg Vorbis (in Dog Days 0x1000 also appears with
16 bits). `0x00800000` = streamed; `0x00400000` = in a language file rather than `PC_Def.str`; top
byte 0x82 / 0x83 = first of 2 / 3 clips interleaved in one stream block, 0x01 / 0x02 = second / third
(a line and its `_R` radio version are such a pair: same offset, half the bytes each). A streamed
record's offset is the clip's offset in the stream file: 2,751 of 2,751 (M02A) and 3,703 of 3,703
(F02) default-file records hit a clip of `PC_Def.str`. MEASURED.

In memory: Dog Days 19,136 ADPCM + 236 PCM; Dead Men 14,145 + 459. Same codec, same block size:
in-memory data can be copied as it is.

Streamed formats per game:

| | Dog Days (334,062) | Dead Men (282,846) |
|---|---|---|
| Vorbis 0x1000 | 333,908 | 4,085 |
| PCM, single | 2 | 8,132 |
| PCM interleaved pair/triple | 149 (mostly as 0x82801000 / 0x01801000 with 16 bits) | about 196,600 |
| **IMA ADPCM 0x11** | **0** | 74,007 |

So Dead Men dialogue is mostly interleaved PCM, which Dog Days also ships (its own `PC_Def.str` has
42 PCM and 79 pair clips), but **Dog Days ships no streamed ADPCM clip.** Whether its stream player
still decodes one is not established. Affected in the FA set: 6 of the 421 English voice clips, 12
map streams in M02FAA and M03FAA, 1 in M06FAA, none in M01FAA's map. `kl_audio.ima_to_pcm` exists to
re-encode them as PCM when they are added to the stream file.

Whether the engine takes a streamed clip's codec from the .WHD record or from the stream file's own
index is not established; the proposal keeps both consistent (the .WHD record copies Dead Men's
format, the merged stream file keeps the clip's header).

## 4. What differs, field by field

| | Dead Men | Dog Days | conversion |
|---|---|---|---|
| build id (trailer H+0) | 46e11c9f | 4c08b8d5 | must be Dog Days' (EXE) |
| stream names | 6 | 10 | Dog Days' |
| sound | 0x30 | 0x34 | insert f32 at +0x1c (0.6 = most common stock value, 0.6/0/0.3/0.5/1.0 occur: ASSUMPTION), append two zero bytes |
| localized wave | 5 language records | 9 | first five as they are, Dut Rus Pol Jap = the English record |
| parameter types | 3, 6, 7 used | never used, 0x21 added | drop 3, 6, 7 (ASSUMPTION: unknown meaning); 0x21 not added |
| parameter 0x12 | Dead Men group | Dog Days group | by group name, table in `merge.py` (ASSUMPTION, by meaning) |
| groups | 20-25 per level: Ambient AmbientRAM AmbientUser Chopper Dialog DialogUser Environment Explosions FlashBacks Footsteps Master Music MusicUser Plane Sfx SfxImpacts SfxShatter SfxShatterShellDrop SfxSuper SfxUser Vehicles Weapon | 25-30: Ambient Ambient_User CreditsMusic Dialog Dialog_user Master Music Music_User SFX SFX_Character SFX_CutScene SFX_Explosions SFX_Footstep SFX_ImpactHit SFX_Shatter SFX_Special SFX_User SFX_Vehicles SFX_Vehicles_Trains SFX_Weapons_* SFX_weapons | not copied |
| object properties | ids 27-34: shoe body head foot hand ammo grenade_can grenade | ids 17-23: shoe body head foot hand ammo grenade | by name; not copied |
| surface properties | ids 1-26: default concrete ceramic stone metal "perforated metal" grate wood grass soil mud flesh water waterdeep fabric plastic rubber plaster plant paper gravel car glass glassfloor carclass bricks | ids 1-16: default metal ceramic concrete stone metalheavy wood soil puddle flesh fabric plastic plaster plant paper glass | by name, else `default`; **the ids are numbered differently** (concrete 2 -> 4, metal 5 -> 2 ...), which matters to whoever converts the .MAT surface type and the .buf impact table |
| roomeffect | 0x70: EAX-style block (i32 room levels, f32 times) | 0x50: other fields | **not converted**; reference set to 0 |
| reverb selection | `ZROOM` field 13 = roomeffect (268 rooms) | `ZROOM` field 14 is 0 in all 511 rooms; reverb comes from `Audio_ReverbActivater` controllers on boxes (490) | a Dead Men map has no reverb until boxes are authored |
| definitions (`#def`) | list sizes 4, 13, 20, 29 (M01FAA) | 4, 6, 13, 35 (F02) | copied as lists; whether the slots mean the same is not established (weapons: 13 in both) |
| .WHD record | 0x38 | 0x44 | section 3 |
| `ZSNDOBJ` | ..., sound | ..., sound, bool | converter's business; sound value remapped |
| `OnlineSpeakTrigger` | 8 fields | 9: enum `EZOST_SPEAKER` inserted at index 5 (TEAM_CRIMINAL -2, TEAM_POLICE -3, DRIVER -4) | converter's business |
| LOC leaf | 229 leaves per file with the sound flag but no id | none | write the Dog Days form |

## 5. How level objects name sounds

Census over every node and controller of every stock level, by exact schema (`d1.py`): values of
fields with type handler 70 (Dog Days) / 65 (Dead Men):

| value | Dog Days | Dead Men |
|---|---|---|
| 0 | 12,306 | 11,074 |
| set | 9,587 | 11,107 |
| seq | 12,286 | 492 |
| sound | 2,850 | 2,930 |
| objectproperty | 2,462 | 2,534 |
| surfaceproperty | 1,453 | 19 |
| roomeffect | 490 | 268 |
| wave | 1 | 31 |
| anything else | **0** | **0** |

Type handler 46 / 45 holds a `def` (6,528 / 4,117), 0 (7,516 / 2,009), or in Dead Men a sound, set or
objectproperty (48). None stray.

Main carriers (Dog Days counts): `ZSNDOBJ` field 8 (6,979), controllers `Audio_PlaySound` #0
(7,829), `Audio_AttachToGeom` #0 (4,059), `HavokShatter` #9-11, `Audio_ReverbActivater` #0
(roomeffect), `GetAudioDefinition` #0 (def), `PlayMusic` #5-7, `PlayAudio` #0, `LightFlicker` #0,
`ZFFActor`/`ZFFPlayer` field 9 (objectproperty), `ZHavokRigidBody` field 22,
`OnlineFragileAllianceSettings` #2-5 and #157-159. Dead Men adds `VehicleEffects`, `SmokeEffects`,
`GasEffects`, `IncendiaryEffects`, `HavokShatterGlass`, `ZPlant`, `ZHFlow*`, `ZHavokCar` (def).
The full table is `d1_dd.json` / `d1_dm.json` in the scratch folder.

**Rule for the graft:** after the property conversion, every type-70 and type-46 field of a node that
came from the Dead Men level is replaced through the offset map the merge returns; fields of nodes
from the Dog Days level are left alone.

Dialogue is named by LOC key, not by offset:

- `ZOnlineFragileAllianceSettings`: 316 string fields in Dog Days, 167 in Dead Men (section 6).
- `OnlineSpeakTrigger` (key in field 6 Dog Days / 5 Dead Men) and `OnlineSpeakPlayer` (field 1).
  Dog Days FA: one `OnlineSpeakPlayer` per level (`Multiplayer/F0x/ExitHeist_01_R`, 6 of 9 levels),
  one `OnlineSpeakTrigger` (F06). Dead Men FA maps: 9 / 6 / 5 / 1 distinct keys on AI and civilian
  groups, e.g. `Multiplayer/Mall/FA_MallGuards_02`, `AllLevels/Oneliners/CivillianPanic/...`. None
  of them exists in a Dog Days LOC.
- Speakers: every Dog Days FA level has `ZSpeakerDriver` ("Pilot" or "Driver"),
  `ZSpeakerTeamCriminals`, `ZSpeakerTeamPolice` under `FASpecials!Speakers!` (F02, F06:
  `Specials!Speakers!`). Dead Men has no such class. The graft has to keep these three nodes.
- A LOC leaf: `name\0`, flags, then `text\0 + u32` if flag 0x01, then `u32 sound id` if flag 0x20;
  flag 0x08 is set on every leaf, 0x10 = a child table follows. In Dog Days the dword after the text
  equals the sound id in 364,280 of 364,280 leaves that have both. All languages of a level have the
  same keys and ids (21/21, 20/20). `loc.py` rebuilds all 168 + 100 non-stub LOC files byte for byte.
- Children are in lower-case order in 33,315 of 33,315 Dead Men tables and 38,176 of 38,944 Dog
  Days tables (the rest fit no simple order, e.g. `DisplayNotSupported` before
  `d3d_device_problems`). How the engine searches a table is not established.
- **Character voices (Dog Days only).** For a key K the engine also looks up `K_C1` ... `K_C9`
  (`kl2.exe` 0x6b879d-0x6b889e: loop 1..9, `sprintf("_C%d")`, lookup 0x828fa0, result or null stored
  per index) and then K itself. In the LOC, 221 of 657 `Multiplayer/` bases exist only as `_C1.._C8`,
  401 only plain, none as both. Dead Men's LOC has no `_C<n>` key (0 of 430): one voice per line. Which of the ten
  results is spoken when is not traced.
- All 9 Dog Days FA levels share the same 2,328 `Multiplayer/` leaves, all 4 Dead Men FA levels the
  same 430. None of the 430 exists in Dog Days.

## 6. Fragile Alliance events: Dead Men -> Dog Days

`ZOnlineFragileAllianceSettings` field index (0-based, as `kl_rtp` lists them). Folder names are the
LOC folders under `Multiplayer/`; "x3" = three alternative lines; `_R` = radio version, heard by the
others; plain = heard by the speaker. Dead Men level-specific names: `<Map>` = Diner (M01), Mall
(M02), Bank (M03), JapGarden (M06).

**For Dead Men fields 19-164 the Dog Days field is the Dead Men field + 8; for 12-16 it is + 5.** The
folders agree by meaning in every row below, the empty slots line up (Dead Men 93, 103, 107-109, 121, 124, 130 against Dog Days 101, 111, 115-117,
129, 132, 138; 17-18 against 22-23),
and the three sound fields sit at 149-151 and 157-159. MEASURED on M01FAA, M03FAA, F01, F02, F05; that
the engine reads them in this order is exactly what the schema says, that field N+8 *means* the same
is supported by the names, not proven.

| Dead Men field | Dead Men key (`Multiplayer/...`) | Dog Days field | Dog Days key | event |
|---|---|---|---|---|
| 12 | Mission_Briefing/FA_1time_MissionBriefing`<Map>`_01_R | 17 | `<F0x>`/MissionBriefing_0n_R | briefing, first round |
| 13-15 | Mission_Briefing/FA_MissionBriefing`<Map>`_01..03_R | 18-20 | `<F0x>`/MissionBriefing_01..03_R | briefing |
| 16 | PoliceMissionBriefing/FA_PoliceMissionBriefing`<Map>`_01_R | 21 | `<F0x>`/PoliceBriefing_01_R | briefing for the dead (police) |
| - | - | 12-16 | AllLevels/Interface/Online/GameStart/* | on-screen start texts (Dog Days only) |
| - | - | 24-26 | UCC_MissionBriefing/* | undercover cop (Dog Days only) |
| 19-21 | Backstab/FA_Backstab_0n_R | 27-29 | Backstab/Backstab_0n_R | somebody turned traitor |
| 22-24, 25-27 | Backstab/FA_BackstabReply_0n_R, plain | 30-32, 33-35 | Backstab_Reply/BackstabReply_0n_R, plain | the traitor answers |
| 28-30, 40-42 | Revenge/FA_Revenge_0n_R, plain | 36-38, 48-50 | Revenge/Revenge_0n_R, plain | traitor killed |
| 31-33, 43-45 | PersonalRevenge/FA_PersonalRevenge_0n_R, plain | 39-41, 51-53 | Personal_Revenge/PersonalRevenge_0n_R, plain | killed by his victim |
| 34-39, 46-51 | PersonalRevengeRejected/FA_PersonalRevengeRejected_0n 2nd time_R, plain | 42-47, 54-59 | Personal_Revenge_Rejected/PersonalRevengeRejected_0n_R, plain | revenge failed |
| 52-54 | PoliceReward/FA_PoliceReward_0n_R | 60-62 | Police_Reward/PoliceReward_0n_R | police kill reward |
| 55-57 | Alliance_Reminder/FA_AllianceReminder_0n_R | 63-65 | Alliance_Reminder/AllianceReminder_0n_R | shot a partner |
| 58-60, 61-63 | Shoot_Off_Money/FA_ShootOffMoney_0n_R, plain | 66-68, 69-71 | Shoot_Off_Money/ShootOffMoney_0n_R, plain | money shot off |
| 64-66, 67-69 | Drop_Cash/FA_Drop_Cash_0n_R, plain | 72-77 | (empty in all 9 levels; no `Drop_Cash` folder) | dropped cash: **Dead Men only** |
| 70-72, 73-75 | Call_Exit_Vehicle/FA_CallExitVehicle_0n_R, plain | 78-80, 81-83 | Call_Esc/CallEsc_0n_R, plain | escape vehicle called |
| 76-78 | CallExitVehiclePolice/FA_CallExitVehiclePolice_0n_R | 84-86 | Call_Esc_Police/CallEscPolice_0n_R | same, police side |
| 79-81 | Call_Exit_Vehicle_Response/FA_CallExitResponse_0n_R | 87-89 | Call_Esc_Response/CallEscResponse_0n_R | the driver answers |
| 82-84 | Shoot_Exit_Vehicle/FA_ShootExitVehicle_0n_R | 90-92 | Shoot_Esc/ShootEsc_0n_R | vehicle shot at |
| 85 | ShootExitVehiclePolice/FA_ShootExitVehiclePolice_02_R | 93-94 | Shoot_Esc_Police/ShootEscPolice_0n_R | same, police |
| 88-90 | ExitVehicleHeavelyDamaged/FA_ExitVehicleHeavelyDamaged_0n_R | 96-98 | Esc_Heavely_Damaged/EscHeavelyDamaged_0n_R | vehicle nearly destroyed |
| 91-92 | ExitVehicleHeavelyDamagedPolice/..._0n_R | 99-100 | Esc_Heavely_Damaged_Police/..._0n_R | same, police |
| 94-96 | ExitVehicleDestroyed/..._01_R, ExitVehicleAndDestroyed/..._01_R, ExitVehicleDestroyed/..._03_R | 102-104 | Esc_Destroyed/EscDestroyed_0n_R | vehicle destroyed |
| 97-99 | ExitVehicleDestroyedPolice / ExitVehicleAndDestroyedPolice ..._R | 105-107 | Esc_Destroyed_Police/EscDestroyedPolice_0n_R | same, police |
| 100 | Boarding/FA_Boarding_01_R | 108 (109: a second Dog Days line) | Boarding/Boarding_0n_R | get in |
| 102 | Boarding/FA_BoardingEnd_03_R | 110-111 | (empty; Dog Days uses 185-187 Boarding_End, 188-190 Boarding_End_Inside) | vehicle leaves |
| 104-106 | LastPossibleTransport/FA_LastPossibleTransport_0n_R | 112-114 | Last_Esc/LastEsc_0n_R | last vehicle |
| 110-112 | Cash_Majority/FA_CashMajority_0n_R | 118-120 | Cash_Majority/CashMajority_0n_R | one player holds most of the loot |
| 113-115 | Dirty_Money/FA_DirtyMoney_0n | 121-123 | Dirty_Money/DirtyMoney_0n | took a dead partner's money |
| 116-118 | JackPot/FA_JackPot_0n | 124-126 | JackPot/JackPot_0n | big pick-up |
| 119-120 | Hitting_The_Score/FA_HittingTheScore`<Map>`_0n_R | 127 | `<F0x>`/ReachlootArea_01_R | reached the loot |
| 122-123 | `<Map>`/Exit_`<Map>`_0n_R (FA_ExitMall, FA_ExitBank, FA_ExitJapGarden) | 130 | `<F0x>`/ExitLootArea_01_R | leaving with the loot |
| 125-127 | Police_Kill_Police/FA_PoliceKillPolice_0n_R | 133-135 | Police_Kill_Police/PoliceKillPolice_0n_R | police shot police |
| 128-129 | Mission_Reminder/FA_MissionReminder`<Map>`_0n_R | 136-137 | `<F0x>`/MissionReminder_0n_R | reminder |
| 131-132 | OneTwoLeft/FA_OneLeft_0n_R | 139-140 | One_Criminal_Left/OneCriminalLeft_0n_R | one criminal left |
| 133-134 | OneTwoLeft/FA_TwoLeft_0n_R | 141-142 | Two_Criminals_left/TwoCriminalsLeft_0n_R | two left |
| 135-137, 138-140 | GameEnds/FA_YouEscaped0n_R, plain | 143-145, 146-148 | You_Esc/YouEsc_0n_R, plain | you escaped |
| 141-143 | Level_Bounds/FA_LevelBound_0n_R | 149-151 | Level_Bounds/LevelBound_0n_R | leaving the map |
| 144-146 | Level_Bounds/FA_LevelBoundsPolice_0n_R | 152-154 | Level_BoundsPolice/LevelBoundsPolice_0n_R | same, police |
| **149, 150, 151** | **sounds**: level music, `fa_slashmixprison`, 0 | **157, 158, 159** | **sounds**: 0 (9/9), `traitorsounds#set` (1/9), `traitorsound_01#sound` or the set (8/9) | see 8 |
| 153 | TimeReminder/FA_TimeReminder_02_R | 161 | One_Min_Left/OneMinLeft_01_R | time warning |
| 154 | 2minTimeReminder/FA_2minTimeReminder_02_R | 162 | Two_Min_left/TwoMinleft_01_R | two minutes |
| - | - | 163 | Three_Min_left/ThreeMinleft_01_R | three minutes (Dog Days only) |
| 156-157 | TimeReminderPolice/FA_TimeReminderPolice_0n_R | 164 | One_Min_Left_Police/OneMinLeftPolice_01_R | time warning, police |
| 159 | GameEnds/FA_TimeOut_R | 167 | Time_Out/TimeOut_02_R | time is up |
| 160 | GameEnds/FA_TimeOutPolice_02_R | 168 | Time_Out_Police/TimeOutPolice_04_R | same, police |
| 161 | GameEnds/FA_AllEscaped_01_R | 169 | All_Esc/AllEsc_01_R | everybody escaped |
| 162 | GameEnds/FA_AllEscapedPolice_R | 170 | All_Escaped_Police/AllEscPolice_01_R | same, police |
| 163 | GameEnds/FA_AllDead_R | 171 | All_Dead/AllDead_01_R | all criminals dead |
| 164 | GameEnds/FA_PlayerEscaped_R | 172 | Criminal_Esc/CriminalEsc_01_R | a criminal escaped (police hear it) |
| 165-175 | Tutor/FA_Tutor_{spawn, traitorspawn, loot, traitorloot, traitor, respawn, revenge, personal_revenge, mercexit, traitorexit, EscapeDying}_R | 173-183 | HoldEscapeVehicle, -, -, Esc_And_Player_Dead x3, Esc_And_Player_Dead_Police x3, -, - | **not the same**: Dead Men's tutorial voice has no Dog Days slot |
| 182-187 | Objectives/{LootMoney, Extract, EscapeCar, PoliceKill, CashReward, PoliceCash} | 333-338 | AllLevels/Interface/Online/Objectives/{Loot, Extract, EscapeCar, PoliceKill, CashReward, PoliceCash} | objective texts (no sound) |
| - | - | 191-199, 209-308 | Driver_Bribe*, Driver_Traitor, UCC_*, Team_* | Dog Days only: bribing the driver, undercover cop, team mode |

Dead Men lines that no settings slot names (they are in the LOC and the stream file, used elsewhere
or not at all): `FA_Menu/*` (29: the lobby announcer), `Civilians/*`, `Diner/Civilian_GangMember_*`,
`Mall/FA_MallGuard*`, `Mall/FA_MallCivilians*`, `Mall/FA_ShopDisplaymall*`, `Bank/FA_BankBoxes_*`,
`JapGarden/FA_CivilJapGarden_*`, `JapGarden/FA_JapBossEsc` (on `OnlineSpeakTrigger` /
`OnlineSpeakPlayer` controllers of the maps), and the unused alternatives of each group.

## 7. What has to be produced for a grafted level

Inputs: the Dog Days slot level S (the systems), the Dead Men level M (the map), the merged
`PC_Def.str` and its `PC_Def.str.map.json` (already built: all 421 English `Dialog/Multiplayer`
clips and every stream the four FA maps and their two music fields use are in it: 0 missing,
MEASURED by `e1.py`).

**(a) Dog Days' weapon, impact and UI sounds unchanged.** Use S's bank as the base and keep every
byte below its first type table; then every offset in the Dog Days nodes and in S's LOC stays valid.
Nothing else is needed for (a). The `_LS` bank of S is copied; its first dword is set to the new T
(the stock relation, 40 of 40; whether the engine reads it is not established).

**(b) The map's ambience and music.** Roots = every non-zero type-65 / type-45 value on a node that
is taken from M (everything except `gamemenu.zip`, `AllLevels/mainsceneincludes.zip`,
`CloneGroup_Effects`, `Heroes!`) + settings fields 149 and 150. Closure over sets, sequences,
definitions and waves:

| | roots | sounds | sets | seqs | defs | room effects | in-memory waves | streamed |
|---|---|---|---|---|---|---|---|---|
| M01FAA map | 74 | 175 | 24 | 3 | 3 | 10 | 163 (3.2 MB) | 10 |
| M02FAA map | 84 | 210 | 44 | 2 | 4 | 28 | 189 (3.9 MB) | 19 (12 ADPCM) |
| M03FAA map | 87 | 220 | 41 | 2 | 4 | 17 | 196 (4.1 MB) | 23 (12 ADPCM) |
| M06FAA map | 42 | 105 | 20 | 4 | 1 | 4 | 97 (2.6 MB) | 4 (1 ADPCM) |
| music, each | 2 | 2 | | | | | | 2 |
| the Dead Men systems that are dropped, for comparison | 45 | 253 | 116 | 13 | 26 | | 195 | 49 |

Music per map (field 149): M01FAA `levelsetup/multiplayer/m01_fa_a/music/m01_b_bustout_sus_ambient`,
M02FAA `.../m02_fa_a/music/fa_m02_muzak_filter_loop`, M03FAA
`levelsetup/level/m02_a/music/m02_training_fight_layer2_drums_loop`, M06FAA
`levelsetup/level/m06_a/music/retomotoaction_ambient_v2_loop`; field 150 is
`levelsetup/multiplayer/fa_all/music/fa_slashmixprison` in all four. Retomoto Tower (M09_A/M09_B) is
a campaign level: its music comes from `PlayMusic` controllers, not from settings; not surveyed here.

**(c) Dead Men's voice lines.** Roots = the sound ids of the LOC keys that will be named: the keys
in M's settings fields 12-175 (about 150) with their `_R` / plain partners, plus the keys on M's
`OnlineSpeakTrigger` / `OnlineSpeakPlayer` controllers. Taking all 430 `Multiplayer/` leaves costs
421 sounds and 421 localized waves, no in-memory data (all streamed, all in the merged stream file).
Then:

1. LOC: add those leaves to each of S's eight real LOC files (Dutch stays a stub), text from M's
   file of the same language (English for Russian, Polish, Japanese), sound id = new offset.
2. Settings: in the Dog Days `GameSettings` (kept from S), write M's key from field N into field
   N + 8 (N = 19..164, except 149-151) and N + 5 (N = 12..16). Slots Dead Men has no line for keep
   Dog Days' key and voice. Fields 72-77 can take Dead Men's `Drop_Cash` keys; whether Dog Days still
   fires that event is not established.
3. If a line stays silent because the engine wants `K_C<n>` (section 5): add nine alias leaves
   `K_C1..K_C9` with the same text and id. ASSUMPTION that the plain key is enough; not tested.

Output files of the graft, beside and inside the new level's zip:

| file | content |
|---|---|
| `<New>_Main.SND` (zip) | merged bank |
| `<New>_Main.WHD`, `.WAV` | S's + appended records / data |
| `<New>_Main<Lang>.LOC` x9 (zip) | S's + grafted leaves |
| `<New>_Main_LS.SND`, `_LS_<Lang>.WHD/.WAV` x7 | S's, first dword of the .SND patched |
| `PC_Def.str` | the merged one (already installed: same size as `KL_PortTools\build\PC_Def.str`) |
| offset map | Dead Men .SND offset -> new offset, for the .prp and the LOC |

### 7.1 Merge algorithm (two banks into one)

1. Walk both images (section 9.2). `cut` = the first type table of the base (in Dog Days the order
   is objects, matrix, type tables, parameter tables, trailer, so everything referenced by a level
   lies below `cut`; asserted).
2. Needed set = closure of the roots in the Dead Men image.
3. For each needed wave: append its .WHD record(s) (converted, name first) to the base .WHD cut at
   its terminator; in-memory data is appended to the .WAV, 16-aligned; a streamed record takes its
   offset from `PC_Def.str.map.json`. A stream that is not in the map is dropped and its sound's wave
   pointer becomes 0.
4. Append to `base[:cut]`, 16-aligned, in dependency order: strings, parameter records, parameter
   lists, child lists / events, objects, each converted (section 4), remembering old -> new.
   References to groups and to object / surface properties are replaced by the base's own objects of
   that name; room effects by 0.
5. Write new type tables (the base's entries, then the new ones; 0xffffffff / 0xfffffffe entries stay
   where they are), new parameter tables (base entries, then one per new use), then the base trailer
   with counts and pointers replaced; set T and size in the header.
6. Return {old offset: new offset}.

Trial run (`merge.py`, stock F01 + M01FAA, roots = all map references + all 430 voice leaves + music):

```
added {'sound': 596, 'wave': 594, 'set': 24, 'def': 3, 'seq': 3}; 0 stream clips not in the merged stream file
merged .SND 2681600 bytes (stock 2420320): unclaimed 0 overlap 0 stray pointers 0 errors {}
stock bytes below 0x238560 unchanged: True
objects per type stock -> merged {'sound': (4616, 5212), 'set': (266, 290), 'seq': (468, 471), 'wave': (4463, 5057), 'def': (38, 41), ...}
merged .WHD 2189520 bytes (stock 2102064), 23121 records; wave->WHD references checked 33040, not a record: 0
merged .WAV 18686352 bytes (stock 15392912); memory records with data inside: 911 of 911
offset map entries 1237 mapped to 0: 10          (the ten room effects)
```

and the LOC graft (`locmerge.py`): 430 leaves added to each of the eight files, 5,798 stock leaves
unchanged, 421 of 421 new ids are sounds of the merged bank, rebuilt file re-parses to itself.

That proves the output is well formed by the same rules the stock files obey. It does not prove the
game accepts it.

## 8. Music

- `ZPlayMusic` (controller `PlayMusic`), same 14 fields in both games: sound, sound, bool, 2 floats,
  4 sounds, `EMusicLayersStart` flags (eLayer1..4 = 1, 2, 4, 8), 4 floats. Used: fields 5, 6, 7 hold
  sounds (Dog Days 80 / 69 / 1 of 87; Dead Men 49 / 38 / 20 of 70): up to three layers of one piece.
  `ZPlayMusicLayerFade` (`EMusicLayer` 0..3, two floats) fades a layer. Dog Days story music is
  `SFX/Music/L0x/*_Basic_Loop.wav`, `*_Action_Loop.wav` pairs, streamed interleaved.
- Dog Days FA: no `PlayMusic`, no `PlayMusicLayerFade`, no `Audio_Set3DMusic`, no `ZMusicLocations`
  in F01-F09 (0 of 9). Settings field 157 is 0 in 9 of 9; 158 / 159 hold the traitor sting.
- Dead Men FA: no `PlayMusic` either (0 of 4); settings 149 = the level loop, 150 =
  `fa_slashmixprison` in 4 of 4, 151 = 0.
- By the + 8 rule Dog Days 157 / 158 / 159 are Dead Men's 149 / 150 / 151. That reading makes 157
  "level music" (unused by stock Dog Days) and 158 "the sting when somebody turns traitor"
  (`fa_slashmixprison` in Dead Men, `traitorsounds` in one Dog Days level). ASSUMPTION; in most Dog
  Days levels the traitor sound sits in 159, not 158, so the two games do not line up cleanly here.

Proposal, cheapest first: (1) put the converted level loop into field 157 and listen; (2) if silent,
add a `PlayMusic` controller (sound in field 5) to a map node and start it with the event that opens
the round. For Retomoto: the owner wants the level's music; its 15 `Music/InHouse/Japan` clips have
to be added to the merged stream file first (they are not FA clips, so they are not in the map file
now: not checked here).

## 9. Code

Tested against the stock files as stated above; none of it has produced a file the game has loaded.
`c.py` is the helper the others import. If these become tools: `tools/kl_snd.py` (9.2 + 9.5),
`tools/kl_whd.py` (9.3), `tools/kl_loc.py` (9.4).

### 9.1 `c.py`: level list, zip member

```python
import os, sys, glob, zipfile, struct
sys.path.insert(0, r'C:\kl-merge\kl-merge\tools')
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
DM = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
def levels(game):
    """-> [(label, zip path)] stock level archives"""
    out = []
    if game == 'dd':
        for z in sorted(glob.glob(DD + r'\Scenes\Locations\*\*_Main.zip')):
            if os.sep + 'F01' + os.sep in z: continue
            out.append((os.path.basename(z)[:-9], z))
        out.append(('F01', DD + r'\KL_PortBackup\Scenes\Locations\F01\F01_Main.zip'))
    else:
        for z in sorted(glob.glob(DM + r'\Scenes\Locations\*\*_Main.zip')):
            out.append((os.path.basename(z)[:-9], z))
    return sorted(out)
def member(z, ext):
    zf = zipfile.ZipFile(z)
    for n in zf.namelist():
        if n.lower().endswith(ext.lower()): return zf.read(n)
def hd(b, off=0, n=256, w=16):
    for i in range(off, min(len(b), off+n), w):
        r = b[i:i+w]
        print('%08x  %-*s %s' % (i, w*3, ' '.join('%02x'%x for x in r), ''.join(chr(x) if 32<=x<127 else '.' for x in r)))
```

### 9.2 `snd2.py`: .SND item map, pointer map, self-test

```python
"""Kane & Lynch .SND (sound project image): item map and pointer map.  Both games.
The file is a memory image; pointers are file offsets.  walk() claims every byte by a typed
item and lists every dword that holds a pointer, so the image can be relocated."""
from c import *
import collections
NAMES = {1: 'sound', 2: 'set', 3: 'seq', 4: 'wave', 5: 'def', 7: 'roomeffect', 0x12: 'objectproperty',
         0x13: 'surfaceproperty', 0x17: 'group'}
GAME = {'dd': dict(streams=10, sizes={1: 0x34, 2: 0x30, 3: 0x20, 4: 0x20, 5: 0x20, 7: 0x50, 0x12: 0x20, 0x13: 0x30, 0x17: 0x50}),
        'dm': dict(streams=6, sizes={1: 0x30, 2: 0x30, 3: 0x20, 4: 0x20, 5: 0x20, 7: 0x70, 0x12: 0x20, 0x13: 0x30, 0x17: 0x50})}
PARAM_SIZE = {5: 0x20, 0x1b: 0x20, 0x1d: 0x20, 0x13: 0x30}      # others 0x10
NTYPES = 25
NUL = bytes(1)
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]
u16 = lambda b, o: struct.unpack_from('<H', b, o)[0]


class Snd:
    def __init__(s, game, data, ls=b''):
        s.game, s.b, s.ls = game, data, ls; G = GAME[game]; b = data
        s.T, s.size, v3, v4 = struct.unpack_from('<4I', b, 0)
        assert s.size == len(b) and (v3, v4) == (3, 4)
        s.matrix = u32(b, s.T)
        s.H = s.T + 4 + 4 * G['streams']; s.H += -s.H % 8
        s.build = struct.unpack_from('<Q', b, s.H)[0]
        s.counts = struct.unpack_from('<%dI' % NTYPES, b, s.H + 16)
        s.tabs = struct.unpack_from('<%dI' % NTYPES, b, s.H + 16 + 4 * NTYPES)
        s.P = s.H + 16 + 8 * NTYPES + 4                      # {count, pointer} per parameter type, 1-based
        s.nparam = 33 if game == 'dd' else 32
        s.tables = {t + 1: list(struct.unpack_from('<%dI' % s.counts[t], b, s.tabs[t])) for t in range(NTYPES) if s.counts[t]}
        s.nmat = len(s.tables[0x12]) + len(s.tables[0x13])

    def walk(s):
        b, G = s.b, GAME[s.game]; L = G['streams'] - 1
        s.items = {}; s.ptrs = set(); s.err = collections.Counter(); s.lsptrs = set()

        def claim(o, n, tag):
            if o in s.items:
                m, was = s.items[o]
                if {was, tag} == {'paramtable', 'paramlist'}: s.items[o] = (max(m, n), 'paramtable'); return False   # a list that is also a table
                if (m, was) != (n, tag): s.err['clash %s/%s' % (was, tag)] += 1
                return False
            s.items[o] = (n, tag); return True

        def cstr(o, tag): claim(o, b.index(NUL, o) - o + 1, tag)

        def plist(o, n, tag):
            claim(o, 4 * n, tag); s.ptrs.update(a for a in range(o, o + 4 * n, 4) if u32(b, a) < s.T and u32(b, a))
            return struct.unpack_from('<%dI' % n, b, o)

        def wavename(q):
            a = b.rfind(b'audio:', 0, q)
            if a < 0: return
            text = b[a:q].rstrip(NUL)
            if text.endswith(b'#wave') and NUL not in text: claim(a, len(text) + 1, 'wavename')

        def wave(o):
            if u32(b, o) == 4:
                if claim(o, 0x20, 'wave'): cstr(u32(b, o + 8), 'wavfile'); wavename(u32(b, o + 8))
                s.ptrs.add(o + 8); return
            n = L if u32(b, o + 0xc) & 2 else 1
            if not claim(o, 0x20 + 0x1c * (n - 1), 'streamwave'): return
            for i in range(n):
                q = o + 8 + 0x1c * i
                if u32(b, q): cstr(u32(b, q), 'wavfile'); s.ptrs.add(q)      # a language without a clip is all zero
            wavename(u32(b, o + 8))

        def params(o, n):
            for q in plist(o, n, 'paramlist'):
                t = u32(b, q); claim(q, PARAM_SIZE.get(t, 0x10), 'param'); seen.add(q)
                if t == 0x12 and u32(b, q + 4): s.ptrs.add(q + 4)
                if t == 0x13 and u32(b, q + 0x1c): s.ptrs.add(q + 0x1c)
        seen = set()
        claim(0, 16, 'header'); s.ptrs.add(0)
        for i in range(G['streams']): cstr(u32(b, s.T + 4 + 4 * i), 'streamname'); s.ptrs.add(s.T + 4 + 4 * i)
        claim(s.T, len(b) - s.T, 'trailer'); s.ptrs.update((s.T, s.H + 8))
        plist(s.matrix, (s.nmat + 1) * s.nmat, 'matrix')
        for t in range(NTYPES):
            if s.counts[t]: plist(s.tabs[t], s.counts[t], 'typetable'); s.ptrs.add(s.H + 16 + 4 * NTYPES + 4 * t)
        tabparams = set()
        for k in range(s.nparam):
            n, p = struct.unpack_from('<2I', b, s.P + 8 * k)
            if n: tabparams.update(plist(p, n, 'paramtable')); s.ptrs.add(s.P + 8 * k + 4)
        for q in tabparams:
            t = u32(b, q); claim(q, PARAM_SIZE.get(t, 0x10), 'param')
            if t == 0x12 and u32(b, q + 4): s.ptrs.add(q + 4)
            if t == 0x13 and u32(b, q + 0x1c): s.ptrs.add(q + 0x1c)
        for t, offs in s.tables.items():
            for o in offs:
                if o >= s.T: continue                        # -1 / -2: lives in the _LS bank
                if t == 4: wave(o); continue
                if u32(b, o) != t: s.err['type %d' % t] += 1
                claim(o, G['sizes'][t], NAMES[t]); cstr(u32(b, o + 8), 'name'); s.ptrs.add(o + 8)
                if u32(b, o + 0x10): params(u32(b, o + 0x10), u16(b, o + 0xc)); s.ptrs.add(o + 0x10)
                n, c = u16(b, o + 0x18), u32(b, o + 0x14)
                if t == 1:
                    if c and c < s.T: s.ptrs.add(o + 0x14); wave(c)
                    wavename_after(s, o, claim)
                elif t in (2, 5, 0x17) and c: plist(c, n, 'list'); s.ptrs.add(o + 0x14)
                elif t == 3 and c:
                    claim(c, 12 * n, 'events'); s.ptrs.add(o + 0x14)
                    s.ptrs.update(c + 12 * i + 8 for i in range(n) if u32(b, c + 12 * i) in (2, 4, 5, 6) and u32(b, c + 12 * i + 8))
                if t == 0x17:
                    cstr(u32(b, o + 0x3c), 'groupname'); s.ptrs.add(o + 0x3c)
                    if u32(b, o + 0x40): s.ptrs.add(o + 0x40)
                    if u32(b, o + 0x1c): claim(u32(b, o + 0x1c), 4 * u16(b, o + 0x22), 'slots'); s.ptrs.add(o + 0x1c)
        # the loading-sound bank: sound records whose name and parameter list live in this file
        z = s.ls; step = G['sizes'][1] + (-G['sizes'][1] % 16)
        for o in range(0x10, len(z), step):
            if u32(z, o) != 1: s.err['ls type'] += 1
            q = u32(z, o + 8); cstr(q, 'name')
            a = q + len(b[q:b.index(NUL, q)]); a += 16 - a % 16
            if b[a:a + 6] == b'audio:' and b[a:b.index(NUL, a)].endswith(b'#wave'): cstr(a, 'wavename')
            if u32(z, o + 0x10): params(u32(z, o + 0x10), u16(z, o + 0xc))
            s.lsptrs.update((o + 8, o + 0x10))
        s.orphans = 0                                       # objects nothing refers to: streamed waves
        end = {o + n for o, (n, tag) in s.items.items()}
        for o in range(0x10, s.T, 16):
            if o not in s.items and u32(b, o) == 0 and u32(b, o + 4) == 0 and u32(b, o + 0xc) in (1, 0xb) and 0 < u32(b, o + 8) < o                     and b[u32(b, o + 8):b.index(NUL, u32(b, o + 8))].lower().endswith(b'.wav') and u32(b, o + 8) not in s.items:
                wave(o); s.orphans += 1
        s.unlisted = len(tabparams - seen)
        s.err['param on a list but in no table'] += len(seen - tabparams)
        return s

    def check(s):
        """-> (unclaimed nonzero bytes, overlapping bytes, pointers that do not hit an item start)"""
        cover = bytearray(len(s.b)); over = 0
        for o, (n, tag) in s.items.items():
            over += sum(cover[o:o + n]); cover[o:o + n] = b'\1' * n
        s.cover = cover
        un = sum(1 for i, c in enumerate(cover) if not c and s.b[i])
        stray = sum(1 for a in s.ptrs if u32(s.b, a) not in s.items and a != 0)
        return un, over, stray


def wavename_after(s, o, claim):
    """A sound's own '#wave' alias string follows its name even when the wave object is shared."""
    b = s.b; q = u32(b, o + 8); e = b.index(NUL, q); a = e + 16 - e % 16
    if b[a:a + 6] == b'audio:':
        t = b[a:b.index(NUL, a)]
        if t.endswith(b'#wave'): claim(a, len(t) + 1, 'wavename')


def shifted(s, delta):
    """The same image with everything after the 16-byte header moved by delta (a multiple of 16)."""
    out = bytearray(s.b[:16] + bytes(delta) + s.b[16:])
    for a in s.ptrs:
        struct.pack_into('<I', out, a + (delta if a >= 16 else 0), u32(s.b, a) + delta)
    struct.pack_into('<I', out, 4, len(out))
    ls = bytearray(s.ls)
    for a in s.lsptrs:
        if u32(ls, a): struct.pack_into('<I', ls, a, u32(ls, a) + delta)
    return bytes(out), bytes(ls)


def ls_path(z):
    p = z[:-4].replace('KL_PortBackup' + os.sep, '') + '_LS.SND'
    return open(p, 'rb').read() if os.path.isfile(p) else b''


if __name__ == '__main__':
    tot = collections.Counter(); D = 0x1230
    for g in ('dd', 'dm'):
        for l, z in levels(g):
            if len(sys.argv) > 1 and l not in sys.argv[1:]: continue
            s = Snd(g, member(z, '.SND'), ls_path(z)).walk()
            un, over, stray = s.check(); err = {k: v for k, v in s.err.items() if v}
            b2, ls2 = shifted(s, D)
            s2 = Snd(g, b2, ls2).walk(); un2, over2, stray2 = s2.check(); err2 = {k: v for k, v in s2.err.items() if v}
            same_shape = collections.Counter(t for n, t in s.items.values()) == collections.Counter(t for n, t in s2.items.values())
            b3 = bytearray(b2[:16] + b2[16 + D:])
            same_ptrs = {a + (D if a >= 16 else 0) for a in s.ptrs} == s2.ptrs
            if not same_ptrs:
                d1 = sorted(s2.ptrs - {a + (D if a >= 16 else 0) for a in s.ptrs})[:5]; d2 = sorted({a + (D if a >= 16 else 0) for a in s.ptrs} - s2.ptrs)[:5]
                print(g, l, 'pointer sets differ', [(hex(a - D), hex(u32(b2, a))) for a in d1], [(hex(a - D), hex(u32(b2, a))) for a in d2])
            for a in s.ptrs: struct.pack_into('<I', b3, a, u32(b2, a + (D if a >= 16 else 0)) - D)
            struct.pack_into('<I', b3, 4, len(b3))
            ok = bytes(b3) == s.b and same_ptrs
            tot[g, 'files'] += 1; tot[g, 'clean'] += (un, over, stray, len(err)) == (0, 0, 0, 0)
            tot[g, 'shift ok'] += ok and same_shape and (un2, over2, stray2, len(err2)) == (0, 0, 0, 0)
            tot[g, 'items'] += len(s.items); tot[g, 'pointers'] += len(s.ptrs)
            for n, t in s.items.values(): tot[g, 'item ' + t] += 1
            if (un, over, stray, len(err)) != (0, 0, 0, 0) or not ok or not same_shape or (un2, over2, stray2) != (0, 0, 0):
                print(g, l, 'unclaimed', un, 'overlap', over, 'stray', stray, err, '| shifted:', un2, over2, stray2, err2, same_shape, ok)
                if '-v' in sys.argv:
                    i = 0; k = 0
                    while i < len(s.b) and k < 12:
                        if s.cover[i] or not s.b[i]: i += 1; continue
                        j = i
                        while j < len(s.b) and not s.cover[j]: j += 1
                        print('   %#x..%#x' % (i, j), s.b[i:min(j, i + 40)]); i = j; k += 1
    for k in sorted(tot): print(k, tot[k])
```

### 9.3 `whd.py`: .WHD parse and rebuild

```python
"""Kane & Lynch .WHD (wave headers) + .WAV (wave data): parse, rebuild, convert Dead Men -> Dog Days."""
from c import *
import collections
NUL = bytes(1)
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]
REC = {'dm': 0x38, 'dd': 0x44}
# record fields (dword index) : name, format, rate, bits, pcm bytes, data bytes, channels, offset [, offset high], samples, block, spb
DM_F = 'name fmt rate bits pcm size ch off samples block spb x2c x30 x34'.split()
DD_F = 'name fmt rate bits pcm size ch off offhi samples block spb x30 x34 x38 x3c x40'.split()


def parse(game, b):
    """-> [('name', offset, bytes) | ('rec', offset, tuple of dwords)] in file order, and the terminator offset"""
    T, size, v3, v4 = struct.unpack_from('<4I', b, 0)
    assert size == len(b) and (v3, v4) == (3, 4), 'not a WHD'
    R = REC[game]; out = []; names = {0}; p = 0x10; end = T if T else len(b)
    while p < end:
        v = u32(b, p)
        if v in names and (v or (len(names) == 1)) and p + R <= end and 0 < (u32(b, p + 4) & 0xffff) <= 0x1000:
            out.append(('rec', p, struct.unpack_from('<%dI' % (R // 4), b, p))); p += R
        elif v == 0:
            p += 4
        elif p % 16 == 0 and 32 <= b[p] < 127:
            e = b.index(NUL, p); out.append(('name', p, b[p:e])); names.add(p); p = e + 1; p += -p % 4
        else:
            raise ValueError('%#x: neither a name nor a record (%08x)' % (p, v))
    return out, T


def build(game, items, T_zero=False, tail=16):
    """Canonical layout: a name is padded to 16; a record is preceded by 4 zero bytes; the file ends with 16 zero bytes."""
    R = REC[game]; out = bytearray(16); prev = None
    for i, (kind, off, val) in enumerate(items):
        if kind == 'name':
            pair = prev == 'name' or (i + 1 < len(items) and items[i + 1][0] == 'name')   # two names, then their two records
            out += bytes(-len(out) % 16); out += val + NUL + (NUL if pair else b''); out += bytes(-len(out) % 16)
        else:
            if not (prev == 'rec' and alias(val)): out += bytes(-len(out) % 16)
            out += bytes(4)
            out += struct.pack('<%dI' % (R // 4), *val)
        prev = kind
    out += bytes(-len(out) % 16)
    T = 0 if T_zero else len(out)
    out += bytes(tail if not T_zero else 0)
    struct.pack_into('<4I', out, 0, T, len(out), 3, 4)
    return bytes(out)


def alias(rec):
    return (rec[1] >> 24) == 0x01


def files(game):
    root = (DD if game == 'dd' else DM) + r'\Scenes'
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.upper().endswith('.WHD'): yield os.path.join(d, f)


if __name__ == '__main__':
    for g in ('dd', 'dm'):
        tot = collections.Counter(); fm = collections.Counter(); cols = collections.defaultdict(collections.Counter)
        for p in files(g):
            b = open(p, 'rb').read(); tot['files'] += 1
            try: items, T = parse(g, b)
            except Exception as e: tot['parse failed'] += 1; print(g, p[-40:], e); continue
            ls = '_LS_' in p
            ok = build(g, items, T_zero=(T == 0), tail=16) == b
            tot['identical'] += ok
            if not ok and tot['shown'] < 4:
                tot['shown'] += 1; r = build(g, items, T_zero=(T == 0))
                d = next((i for i in range(min(len(r), len(b))) if r[i] != b[i]), None)
                print(g, p[-44:], 'len', len(b), len(r), 'first diff', d and hex(d), 'T', hex(T))
            wav = os.path.getsize(p[:-4] + '.WAV') if os.path.isfile(p[:-4] + '.WAV') else -1
            for kind, off, v in items:
                tot[kind] += 1
                if kind == 'rec':
                    f = dict(zip(DD_F if g == 'dd' else DM_F, v)); fm[(hex(f['fmt']), f['bits'], f['ch'])] += 1
                    streamed = bool(f['fmt'] & 0x800000)
                    if not streamed:
                        o = f['off'] | (f.get('offhi', 0) << 32)
                        tot['in-memory'] += 1; tot['in-memory data inside .WAV'] += (16 <= o and o + f['size'] <= wav)
                    else: tot['streamed'] += 1
                    for k, x in f.items():
                        if k.startswith('x') or k in ('block', 'spb', 'offhi'): cols[(k, 'stream' if streamed else 'mem')][x] += 1
        print(g, dict(tot)); print('   formats (fmt, bits, channels):', fm.most_common(14))
        for k in sorted(cols): print('   ', k, [(hex(x), n) for x, n in cols[k].most_common(5)])
```

### 9.4 `loc.py` and `locmerge.py`: LOC tree, round trip, graft

```python
"""LOC trie: parse to a tree and write it back (round trip)."""
from c import *
import collections
class Node:
    __slots__ = ('name', 'flags', 'kids', 'raw')      # raw: bytes after the flags byte of a leaf
def parse(d):
    def table(t, bound):
        n = d[t]; base = t + 4 * n - 3
        offs = [0] + list(struct.unpack_from('<%di' % (n - 1), d, t + 1)) if n else []
        pos = [base + o for o in offs]; out = []
        for i, no in enumerate(pos):
            e = d.index(b'\0', no); nd = Node(); nd.name = d[no:e]; nd.flags = d[e + 1]
            nxt = pos[i + 1] if i + 1 < n else bound
            if nd.flags & 0x10: nd.kids = table(e + 2, nxt); nd.raw = None
            else: nd.kids = None; nd.raw = d[e + 2:nxt]
            out.append(nd)
        return out
    return table(0, len(d)) if len(d) > 9 else None
def build(kids):
    parts = []
    for k in kids:
        parts.append(k.name + b'\0' + bytes([k.flags]) + (build(k.kids) if k.kids is not None else k.raw))
    offs, p = [], 0
    for x in parts[:-1]:
        p += len(x); offs.append(p)
    return bytes([len(kids)]) + struct.pack('<%di' % len(offs), *offs) + b''.join(parts)
def leaves(kids, path=()):
    for k in kids:
        if k.kids is not None: yield from leaves(k.kids, path + (k.name.decode('latin1'),))
        else: yield '/'.join(path + (k.name.decode('latin1'),)), k
def fields(k):
    """-> (text, x, sound id) of a leaf; x is the dword after the text"""
    r = k.raw; text = x = sid = None; q = 0
    if k.flags & 1:
        e = r.index(b'\0'); text = r[:e]; q = e + 1
        if len(r) >= q + 4: x = struct.unpack_from('<I', r, q)[0]; q += 4
    if k.flags & 0x20 and len(r) >= q + 4: sid = struct.unpack_from('<I', r, q)[0]; q += 4
    return text, x, sid, len(r) - q
if __name__ == '__main__':
    for g in ('dd', 'dm'):
        tot = ok = stub = 0; fl = collections.Counter(); rest = collections.Counter(); xs = collections.Counter()
        for l, z in levels(g):
            zf = zipfile.ZipFile(z)
            for n in zf.namelist():
                if not n.upper().endswith('.LOC'): continue
                d = zf.read(n); tot += 1; t = parse(d)
                if t is None: stub += 1; continue
                ok += build(t) == d
                for path, k in leaves(t):
                    text, x, sid, left = fields(k); fl[k.flags] += 1; rest[(k.flags, left)] += 1
                    xs[(k.flags, 'x==sid' if x == sid else 'x==0' if x == 0 else 'x?')] += 1
        print(g, 'files', tot, 'stubs', stub, 'round trip identical', ok)
        print('  flags', dict(fl)); print('  unparsed bytes per leaf', dict(rest)); print('  x', dict(xs))
```

```python
"""Add Dead Men LOC subtrees to a Dog Days LOC, with the sound ids moved to the merged .SND."""
from loc import *
import json


def graft(dd_kids, dm_kids, want, sndmap, path=()):
    """Insert every Dead Men leaf whose path satisfies want() and that Dog Days does not have.
    Returns the number of leaves added.  Children stay in lower-case order."""
    added = 0; have = {k.name.lower(): k for k in dd_kids}
    for k in dm_kids:
        p = path + (k.name.decode('latin1'),)
        mine = have.get(k.name.lower())
        if k.kids is not None:
            if mine is None:
                mine = Node(); mine.name, mine.flags, mine.kids, mine.raw = k.name, 0x10, [], None
                n = graft(mine.kids, k.kids, want, sndmap, p)
                if n: dd_kids.append(mine); added += n
            elif mine.kids is not None:
                added += graft(mine.kids, k.kids, want, sndmap, p)
        elif mine is None and want('/'.join(p)):
            text, x, sid, left = fields(k)
            new = sndmap.get(sid, 0) if sid else 0
            leaf = Node(); leaf.name, leaf.kids = k.name, None
            # Dog Days leaf: flags 0x08 | 0x01 text | 0x20 sound; text, then the dword after it (= the id), then the id
            if new: leaf.flags = 0x29; leaf.raw = (text or b'') + b'\0' + struct.pack('<II', new, new)
            else: leaf.flags = 0x09; leaf.raw = (text or b'') + b'\0' + bytes(4)
            dd_kids.append(leaf); added += 1
    dd_kids.sort(key=lambda k: k.name.lower())
    return added


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    sndmap = {int(k): v for k, v in json.load(open(os.path.join(here, 'merged', 'snd_map.json'))).items()}
    zd = zipfile.ZipFile(dict(levels('dd'))['F01']); zm = zipfile.ZipFile(dict(levels('dm'))['M01FAA'])
    from snd2 import Snd, u32
    msnd = Snd('dd', open(os.path.join(here, 'merged', 'F01_Main.SND'), 'rb').read())
    sounds = set(msnd.tables[1])
    for lang in ('English', 'German', 'French', 'Spanish', 'Italian', 'Russian', 'Polish', 'Japanese', 'Dutch'):
        dn = [n for n in zd.namelist() if n.endswith(lang + '.LOC')][0]
        src = [n for n in zm.namelist() if n.endswith(lang + '.LOC')] or [n for n in zm.namelist() if n.endswith('English.LOC')]
        d = zd.read(dn); t = parse(d)
        if t is None: print(lang, 'stub of %d bytes: left as it is' % len(d)); continue
        before = {p: (k.flags, k.raw) for p, k in leaves(t)}
        n = graft(t, parse(zm.read(src[0])), lambda p: p.startswith('Multiplayer/'), sndmap)
        out = build(t); t2 = parse(out); after = {p: (k.flags, k.raw) for p, k in leaves(t2)}
        kept = all(after.get(p) == v for p, v in before.items())
        ids = [fields(k)[2] for p, k in leaves(t2) if p not in before]
        print('%-9s %d -> %d bytes, leaves %d -> %d (added %d, from %s); stock leaves unchanged: %s; rebuilt file re-parses to itself: %s; new ids that are sounds of the merged bank: %d of %d with an id' % (
            lang, len(d), len(out), len(before), len(after), n, src[0].split('Main')[-1], kept, build(t2) == out, sum(1 for i in ids if i in sounds), sum(1 for i in ids if i)))
    # the _LS.SND header
    from c import DD, DM
    import collections
    c = collections.Counter()
    for g in ('dd', 'dm'):
        for l, z in levels(g):
            p = z[:-4].replace('KL_PortBackup' + os.sep, '') + '_LS.SND'
            if os.path.isfile(p): c[(g, u32(open(p, 'rb').read(), 0) == u32(member(z, '.SND'), 0))] += 1
    print('_LS.SND first dword == first dword of the level .SND:', dict(c))
```

### 9.5 `merge.py`: append a Dead Men bank to a Dog Days bank

`lv.py` (not reproduced) only lists a level's nodes with class, path and decoded fields through
`kl_prp`, `kl_gms`, `kl_rtp`; the roots can equally be collected inside `kl_convert`. The test at the
bottom also reads `loc_eng.pkl` (every level's English LOC as {key: (flags, text, sound id)}, written
by `loc2.py`) and writes its result to `merged/` in the scratch folder; `locmerge.py` reads that.
`merge()` itself needs only its arguments.

```python
"""Append the part of a Dead Men sound bank a grafted level needs to a Dog Days bank.
merge() -> new .SND, .WHD, .WAV bytes and {Dead Men .SND offset: new .SND offset}.
Everything of the Dog Days bank keeps its offset; Dead Men objects are converted and appended."""
from snd2 import *
import whd as W
GROUP = {'Master': 'Master', 'Dialog': 'Dialog', 'DialogUser': 'Dialog_user', 'Music': 'Music', 'MusicUser': 'Music_User',
         'Ambient': 'Ambient', 'AmbientRAM': 'Ambient', 'AmbientUser': 'Ambient_User', 'Sfx': 'SFX', 'SfxUser': 'SFX_User',
         'SfxSuper': 'SFX_Special', 'Explosions': 'SFX_Explosions', 'Footsteps': 'SFX_Footstep', 'SfxImpacts': 'SFX_ImpactHit',
         'SfxShatter': 'SFX_Shatter', 'SfxShatterShellDrop': 'SFX_Weapons_ShellDrop', 'Weapon': 'SFX_weapons',
         'Vehicles': 'SFX_Vehicles', 'Chopper': 'SFX_Vehicles', 'Plane': 'SFX_Vehicles', 'Environment': 'SFX',
         'FlashBacks': 'SFX_CutScene'}                      # by meaning: ASSUMPTION, not read from either exe
cs = lambda b, o: b[o:b.index(NUL, o)]
pad16 = lambda x: x + bytes(-len(x) % 16)


def merge(dd, dm, dd_whd, dd_wav, dm_whd, dm_wav, roots, strmap, log=print):
    """dd, dm: walked Snd.  roots: Dead Men .SND offsets used by the map's objects, the LOC and the music fields.
    strmap: PC_Def.str.map.json (Dead Men stream offset -> [offset in the merged file, size])."""
    b, d = dd.b, dm.b
    kind = {o: t for t, offs in dm.tables.items() for o in offs if o < dm.T}
    ddname = {t: {cs(b, u32(b, o + 8)).lower(): o for o in dd.tables.get(t, []) if o < dd.T} for t in (0x12, 0x13, 0x17)}
    ddgroup = {cs(b, u32(b, o + 0x3c)).decode(): o for o in dd.tables[0x17]}
    # ---- 1. what is needed, in dependency order
    order, seen, st = [], set(), list(roots)
    def kids(o):
        t = kind.get(o); n, c = u16(d, o + 0x18), u32(d, o + 0x14); out = []
        if t in (None, 4, 7, 0x12, 0x13, 0x17): return out
        if u32(d, o + 0x10):
            for q in struct.unpack_from('<%dI' % u16(d, o + 0xc), d, u32(d, o + 0x10)):
                if u32(d, q) == 0x13 and u32(d, q + 0x1c): out.append(u32(d, q + 0x1c))
        if t == 1 and c and c < dm.T: out.append(c)
        elif t in (2, 5) and c: out += [x for x in struct.unpack_from('<%dI' % n, d, c) if x]
        elif t == 3 and c: out += [u32(d, c + 12 * i + 8) for i in range(n) if u32(d, c + 12 * i) in (2, 4, 5, 6) and u32(d, c + 12 * i + 8)]
        return out
    while st:
        o = st.pop()
        if o and o < dm.T and o not in seen: seen.add(o); order.append(o); st += kids(o)
    # ---- 2. wave headers and wave data
    ditems, _ = W.parse('dm', dm_whd); drec = {o - 4: v for k, o, v in ditems if k == 'rec'}
    whd = bytearray(dd_whd[:u32(dd_whd, 0)]); wav = bytearray(dd_wav); whdmap = {}; dropped = []
    def whd_rec(old):
        if old not in whdmap:
            v = drec[old]; name = cs(dm_whd, v[0]); fmt, off = v[1], v[7]
            if fmt & 0x800000:                               # streamed: the clip must be in the merged stream file
                if str(off) not in strmap: dropped.append(name); whdmap[old] = None; return None
                off = strmap[str(off)][0]
            else:
                wav.extend(bytes(-len(wav) % 16)); new = len(wav); wav.extend(dm_wav[off:off + v[5]]); off = new
            whd.extend(bytes(-len(whd) % 16)); npos = len(whd); whd.extend(pad16(name + NUL))
            whdmap[old] = len(whd)
            # Dog Days record: 64-bit offset, two more dwords at the end (most common stock values: ASSUMPTION)
            x3c, x40 = (0, 0x10) if fmt & 0x800000 else (0xcdcdcd00, 0xcdcdcdcd)
            whd.extend(struct.pack('<I17I', 0, npos, fmt & ~0x400000, v[2], v[3], v[4], v[5], v[6], off & 0xffffffff, off >> 32,
                                   v[8], v[9], v[10], v[11], v[12], v[13], x3c, x40) + bytes(8))
        return whdmap[old]
    # ---- 3. lay out the new items
    cut = min(p for p in dd.tabs if p)                       # Dog Days: objects | matrix | type tables | parameter tables | trailer
    assert dd.matrix + 4 * (dd.nmat + 1) * dd.nmat <= cut
    out = bytearray(b[:cut]); new = {}; fix = []             # fix: (position, key of the target)
    def put(key, data, refs=()):
        out.extend(bytes(-len(out) % 16)); new[key] = len(out)
        fix.extend((len(out) + r, k) for r, k in refs); out.extend(data)
    def string(p):
        if ('s', p) not in new: put(('s', p), cs(d, p) + NUL)
        return ('s', p)
    def target(x):
        """Key or Dog Days offset a Dead Men object pointer becomes."""
        t = kind.get(x)
        if t == 0x17: return ('abs', ddgroup[GROUP[cs(d, u32(d, x + 0x3c)).decode()]])
        if t in (0x12, 0x13):
            n = cs(d, u32(d, x + 8)).lower()
            return ('abs', ddname[t].get(n, ddname[0x13][b'audio:materials/surface/default#surfaceproperty'] if t == 0x13 else 0))
        if t == 7: return ('abs', 0)                         # Dead Men reverb block: no Dog Days form
        return ('o', x)
    uses = collections.Counter(); newtab = collections.defaultdict(list); newpar = collections.defaultdict(list)
    for o in order:
        t = kind.get(o)
        if t in (7, 0x12, 0x13, 0x17): continue
        if t is None or t == 4:                              # a wave
            if u32(d, o) == 4:
                r = whd_rec(u32(d, o + 0x14))
                if r is None: new[('o', o)] = 0; continue
                put(('o', o), d[o:o + 0x14] + struct.pack('<I', r) + d[o + 0x18:o + 0x20], [(8, string(u32(d, o + 8)))])
                struct.pack_into('<I', out, new[('o', o)] + 4, 0xcdcdcdcd)
            else:
                n = 5 if u32(d, o + 0xc) & 2 else 1
                recs = [struct.unpack_from('<7I', d, o + 8 + 0x1c * i) for i in range(n)]
                r0 = whd_rec(recs[0][3])
                if r0 is None: new[('o', o)] = 0; continue
                if n == 5:                                   # Eng Ger Fre Spa Ita -> + Dut Rus Pol Jap; only English audio exists
                    recs = [recs[0]] + [(recs[0][0], 3, 0, recs[0][3], recs[0][4], 0, 0)] * 8
                blob = bytes(8); refs = []
                for i, r in enumerate(recs):
                    refs.append((8 + 0x1c * i, string(r[0])))
                    blob += struct.pack('<7I', r[0], r[1], r[2], r0, r[4], r[5], 0)
                put(('o', o), blob[:0x20 + 0x1c * (len(recs) - 1)], refs)
            newtab[4].append(('o', o)); continue
        body = bytearray(d[o:o + GAME['dm']['sizes'][t]])
        if t == 1:                                           # 0x30 -> 0x34: one float more at +0x1c, two bytes more at the end
            body = body[:0x1c] + struct.pack('<f', 0.6) + body[0x1c:0x2d] + b'\0\0\xcd'
        refs = [(8, string(u32(d, o + 8)))]
        np_, pl, n, c = u16(d, o + 0xc), u32(d, o + 0x10), u16(d, o + 0x18), u32(d, o + 0x14)
        if pl:
            keep = []
            for q in struct.unpack_from('<%dI' % np_, d, pl):
                pt = u32(d, q)
                if pt in (3, 6, 7): continue                 # no stock Dog Days level uses these types
                if ('p', q) not in new:
                    rec = bytearray(d[q:q + PARAM_SIZE.get(pt, 0x10)]); pr = []
                    if pt == 0x12 and u32(d, q + 4): pr.append((4, target(u32(d, q + 4))))
                    if pt == 0x13 and u32(d, q + 0x1c): pr.append((0x1c, target(u32(d, q + 0x1c))))
                    put(('p', q), rec, pr)
                keep.append(('p', q)); newpar[pt].append(('p', q))
            struct.pack_into('<H', body, 0xc, len(keep))
            if keep: put(('pl', o), bytes(4 * len(keep)), [(4 * i, k) for i, k in enumerate(keep)]); refs.append((0x10, ('pl', o)))
            else: struct.pack_into('<I', body, 0x10, 0)
        if t == 1 and c and c < dm.T: refs.append((0x14, ('o', c)))
        elif t in (2, 5) and c:
            put(('cl', o), bytes(4 * n), [(4 * i, target(x)) for i, x in enumerate(struct.unpack_from('<%dI' % n, d, c)) if x]); refs.append((0x14, ('cl', o)))
        elif t == 3 and c:
            ev = bytearray(d[c:c + 12 * n])
            put(('ev', o), ev, [(12 * i + 8, target(u32(d, c + 12 * i + 8))) for i in range(n) if u32(d, c + 12 * i) in (2, 4, 5, 6) and u32(d, c + 12 * i + 8)]); refs.append((0x14, ('ev', o)))
        put(('o', o), bytes(body), refs); newtab[t].append(('o', o))
    for pos, key in fix:
        v = key[1] if key[0] == 'abs' else new.get(key, 0)
        struct.pack_into('<I', out, pos, v)
    # ---- 4. tables and trailer
    counts, tabs = list(dd.counts), list(dd.tabs)
    for t in range(NTYPES):
        add = [new[k] for k in newtab.get(t + 1, []) if new[k]]
        if dd.counts[t] or add:
            out.extend(bytes(-len(out) % 16)); tabs[t] = len(out); counts[t] = dd.counts[t] + len(add)
            out.extend(b[dd.tabs[t]:dd.tabs[t] + 4 * dd.counts[t]] + struct.pack('<%dI' % len(add), *add))
    pairs = []
    for k in range(dd.nparam):
        n, p = struct.unpack_from('<2I', b, dd.P + 8 * k); add = [new[x] for x in newpar.get(k + 1, [])]
        if n or add:
            out.extend(bytes(-len(out) % 16)); pairs += [n + len(add), len(out)]
            out.extend(b[p:p + 4 * n] + struct.pack('<%dI' % len(add), *add))
        else: pairs += [0, 0]
    out.extend(bytes(-len(out) % 16)); T = len(out); tr = bytearray(b[dd.T:])
    struct.pack_into('<%dI' % NTYPES, tr, dd.H - dd.T + 16, *counts)
    struct.pack_into('<%dI' % NTYPES, tr, dd.H - dd.T + 16 + 4 * NTYPES, *tabs)
    struct.pack_into('<%dI' % len(pairs), tr, dd.P - dd.T, *pairs)
    out.extend(tr); struct.pack_into('<2I', out, 0, T, len(out))
    whd.extend(bytes(-len(whd) % 16)); Tw = len(whd); whd.extend(bytes(16)); struct.pack_into('<2I', whd, 0, Tw, len(whd))
    wav.extend(bytes(-len(wav) % 16)); struct.pack_into('<I', wav, 4, len(wav))
    log('added %s; %d stream clips not in the merged stream file' % (dict(collections.Counter(NAMES.get(kind.get(o), 'wave') for o in order if new.get(('o', o)))), len(dropped)))
    return bytes(out), bytes(whd), bytes(wav), {o: (new.get(('o', o), 0) if target(o)[0] == 'o' else target(o)[1]) for o in order}


if __name__ == '__main__':
    import json, pickle, lv, kl_rtp
    slot, src = 'F01', 'M01FAA'
    zd = dict(levels('dd'))[slot]; zm = dict(levels('dm'))[src]
    dd = Snd('dd', member(zd, '.SND'), ls_path(zd)).walk(); dm = Snd('dm', member(zm, '.SND'), ls_path(zm)).walk()
    base = zd[:-4].replace('KL_PortBackup' + os.sep, '')
    S = kl_rtp.Schema.load('dm'); roots = set()
    for n in lv.load('dm', src):
        top = n['path'].split(chr(92))[1] if chr(92) in n['path'] else ''
        if any(top.startswith(x) for x in ('gamemenu.zip', 'AllLevels/mainsceneincludes.zip', 'CloneGroup_Effects', 'Heroes!')): continue
        for cls, units in [(n['cls'], n['props'])] + [(cc, cu) for cn, cc, cu in n['ctrls'] if cc]:
            for f, (k, v) in zip(S.fields(cls) or (), units):
                if f.type in (65, 45) and k == 'I': roots.add(v[0])
    roots |= {v[2] for p, v in pickle.load(open('loc_eng.pkl', 'rb'))[('dm', src)][0].items() if p.startswith('Multiplayer/') and v[2]}
    snd, whd, wav, mp = merge(dd, dm, open(base + '.WHD', 'rb').read(), open(base + '.WAV', 'rb').read(),
                              open(zm[:-4] + '.WHD', 'rb').read(), open(zm[:-4] + '.WAV', 'rb').read(), roots - {0},
                              json.load(open(DM + r'\KL_PortTools\build\PC_Def.str.map.json')))
    m = Snd('dd', snd, dd.ls).walk(); un, over, stray = m.check()
    print('merged .SND %d bytes (stock %d): unclaimed %d overlap %d stray pointers %d errors %s' % (len(snd), len(dd.b), un, over, stray, {k: v for k, v in m.err.items() if v}))
    cut = min(p for p in dd.tabs if p); print('stock bytes below %#x unchanged:' % cut, snd[16:cut] == dd.b[16:cut])
    print('objects per type stock -> merged', {NAMES[t]: (len(dd.tables[t]), len(m.tables[t])) for t in sorted(m.tables)})
    items, T = W.parse('dd', whd); recs = {o - 4: v for k, o, v in items if k == 'rec'}
    bad = 0; nw = 0
    for o in m.tables[4]:
        if o >= m.T: continue
        nrec = (9 if u32(snd, o + 0xc) & 2 else 1) if u32(snd, o) == 0 else 1
        for i in range(nrec):
            q = o + (0x14 if i == 0 else 0x14 + 0x1c * i); nw += 1
            if u32(snd, q - 0xc if i else o + 8) and u32(snd, q) not in recs: bad += 1
    print('merged .WHD %d bytes (stock %d), %d records; wave->WHD references checked %d, not a record: %d' % (len(whd), os.path.getsize(base + '.WHD'), len(recs), nw, bad))
    inside = sum(1 for v in recs.values() if not v[1] & 0x800000 and 16 <= v[7] and v[7] + v[5] <= len(wav)); mem = sum(1 for v in recs.values() if not v[1] & 0x800000)
    print('merged .WAV %d bytes (stock %d); memory records with data inside: %d of %d' % (len(wav), len(dd_wav := open(base + '.WAV', 'rb').read()), inside, mem))
    print('offset map entries', len(mp), 'mapped to 0:', sum(1 for v in mp.values() if not v))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'merged'); os.makedirs(out, exist_ok=True)
    for ext, blob in (('.SND', snd), ('.WHD', whd), ('.WAV', wav)): open(os.path.join(out, 'F01_Main' + ext), 'wb').write(blob)
    json.dump({str(k): v for k, v in mp.items()}, open(os.path.join(out, 'snd_map.json'), 'w'))
```

## 10. Open questions and risks

Most likely to bite first:

1. **Nothing was loaded by the game.** The merged bank is consistent by the stock files' own rules;
   the engine may rely on something they do not show (the order of a type table, the meaning of the
   parameter tables, a name lookup).
2. **Table sizes.** The trial merge has 5,212 sounds and 5,057 waves; the largest stock level has
   4,806 (F05) and 4,568 (F04). If the sound system has fixed pools this overflows. Take only the
   voice keys that are named (about 150 with partners instead of 430) to stay below the stock maximum.
3. **Streamed ADPCM** (format 0x800011) does not occur in Dog Days; 6 voice clips and the M02/M03
   map streams use it. Re-encode to PCM if they are silent or noise.
4. **The `_C<n>` lookup.** A Dead Men key has no character variants. If the engine only speaks a
   variant, the lines are silent until alias leaves are added.
5. **Sound field +0x1c** (new float, 0.6 written), the two new .WHD dwords (0 / 0x10 written),
   dropped parameter types 3, 6, 7, the group table: all by analogy with stock values.
6. **No reverb** on a Dead Men map (room effects not converted, Dog Days rooms carry none).
7. **Impact sounds on Dead Men geometry** go through the Dog Days material matrix, so the surface
   ids in the converted .MAT / .buf table have to be Dog Days ids (table in section 4). Not this
   track's file, but the numbers differ and nothing remaps them yet as far as I know.
8. **Definitions** (`#def`) from Dead Men vehicles and characters are copied as lists; Dog Days code
   may read other slots. Dead Men cars' engine sounds may be wrong or silent.
9. **Music field 157** may be dead in Dog Days.
10. **Languages.** Only English Dead Men audio is in the merged stream file; on another language the
    Dead Men lines stay English (all nine language records point at the English clip).
11. LOC table search order is not established; grafted leaves are inserted in lower-case order.
12. The `.sgp` (sound propagation: rooms by scene path) belongs to the map and was not examined here.
