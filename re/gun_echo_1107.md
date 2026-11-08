# Gun echo / environment-adaptive sound: what the engine already has (2026-11-07, offline research)

Question (owner 11-07): make gun shots more echoey / adaptive to the environment, raw instead of vanilla.
Method: static reading of kl2.exe (32-bit, base 0x400000), .SND banks via tools/kl_snd.py, .prp controller census.
Nothing was launched, nothing written into the game folder. Items marked GUESS or OPEN are not verified.

## 1. Audio API (verified)
- kl2.exe imports OpenAL32.dll statically, with the EFX extension (ALC_EXT_EFX). No XAudio2, X3DAudio, FMOD or Miles.
  DSOUND.dll imports only ordinals #11 and #2 (GUESS: device enumeration / capture).
- System has OpenAL32.dll and wrap_oal.dll in SysWOW64 (the OpenAL32.dll hitch frames in KLHook.log are the mixer).
- Classes (RTTI): ZSynthOpenAL vtable 0xb9ac74, ZSoundBufferOpenAL 0xb9ad5c, ZSoundListenerOpenAL 0xb9ade0,
  ZEaxBase 0xb9ac14, ZEaxListener 0xb9ac2c, ZEaxSource 0xb9ac5c, ZDllSound 0xb9a3ec, ZSoundGraph 0xb9a614.
- DD creates ONE global auxiliary effect slot holding a standard AL reverb effect (type 0x8001). No EAX property-set strings in DD.
  Dead Men instead loads OpenAL at run time and has EAX 2-5 (EAXGet/EAXSet) plus an EFX string.
- SetReverb is at 0x5fff30 (ZSynthOpenAL::SetReverb). It takes a float[10] and maps it onto the AL reverb parameters.
  Voices get an aux send at their creation sites (AL_AUXILIARY_SEND_FILTER); no per-source send gain is set (default full send).
- init region to read for the slot/effect creation: 0x8f89ce alcOpenDevice, 0x8f89ef alcCreateContext, 0x8f8a50..0x8f8ad8 EFX setup.

## 2. Room reverb data already in the engine
- .SND roomeffect objects (table 7): DD size 0x50, DM size 0x70. Fields are EAX/I3DL2-style (room mB, decay seconds, ...).
  Counts: 490 in DD, 268 in DM (re/audio.md has the layout).
- Switching: controller Audio_ReverbActivater (class ZAudio_ReverbActivater, ClassInfo 0xd07164, vtable 0xbaa9fc,
  size 0x3c, created at 0x454b90). Serialized fields: roomeffect ref, string 'CheckInsideEnter', string 'CheckInsideLeave',
  float in 10..100 (GUESS: priority or box size).
- The 9 stock DD FA maps already carry 6 to 26 activaters each, so DD maps already change reverb per room.
- DM maps: ZROOM field 13 holds a roomeffect directly (DD field 14 = 0, DD uses activaters on boxes). DM campaign maps have no activaters,
  so a grafted DM map in DD has NO room reverb unless activaters are authored.
- ZSoundGraph (.sgp): portals (0x5c bytes, with openness), edges, rooms, routes; route finder 0x5866a0. This is occlusion/propagation, not reverb.

## 3. Gun banks (verified from re/gun_sounds.md and re/gun_raw_1107.md)
- `<gun>_shot_player#set` and `<gun>_shot_npc#set` share 3 `#sound` objects; one class-shared Distant_Shot_* layer per class
  (DD has 4 shared distant layers, DM has 36 per-gun ones). Group volumes: sfx_weapons_shot_npc 0.35, sfx_weapons_shot_player 0.70.
- DM shots are darker and longer (centroid 592 vs 996 Hz, low-freq 62% vs 38%, 1.1 s vs 0.8 s): this is the "raw" the owner hears missing.
- No *_Tail / *_Indoor / *_Outdoor named variants were looked for directly in PC_Def.str / .WHD: OPEN. The shot objects have a distance layer
  only, no indoor/outdoor split that I found. DM has distant variants DD lacks (36 vs 4).

## 4. OPEN (not resolved statically)
- The builder of the float[10] from the roomeffect ints, and what calls SetReverb (the ReverbActivater runtime path).
- What sets the voice reverb-send field (+0x54) and voice flags, so whether gun voices really get the aux send. One live A/B needed.
- Which .SND sound flag byte maps to the voice ctor flag bits.
- Whether a DD preset table exists. Meaning of the ReverbActivater float. DM-side EAX usage detail.

## 5. Ranked options (each a toggle, "(recommended on/off)")
1. Hook SetReverb 0x5fff30 (klhook ini key, e.g. [Sound] ReverbBoost, GUESS name): scale decay/reflections/gain of the incoming float[10],
   with a floor for "outside" rooms so streets get a long tail. Covers all 9 stock FA maps and online at once (no data change).
   Effort low-medium, risk low (one function, single global slot). Caveat: only helps if gun voices carry the aux send (OPEN above).
2. Author ReverbActivater boxes + roomeffects on DM and graft maps (INSTALL/UNDO bat pair), retune outside_* decay on DD maps.
   Effort medium-high (per-map authoring), risk low-medium. Needed anyway so DM maps have any room reverb; stacks with option 1.
3. Bake the `heat` IR tail (tools/kl_gunsnd.py: EQ + tanh saturation + street IR 7 slap echoes 45-900 ms + 2.6 s tail, indoor IR 1.0 s)
   into per-bank gun sounds, optionally restoring DM distant layers. Effort medium, risk low, bank size grows; not environment-adaptive
   (fixed tail), but does not depend on the engine send. Online banks (bots.zip) must be baked identically.

Suggested order: one live A/B to settle the aux-send question, then 1, then 2 for DM maps, 3 as the fallback for "raw" timbre.

## 6. Aux send: what the engine does per voice (static, 2026-11-08, kl2.exe read with debug/dasm.py; NOT yet seen in a run)
Corrects section 1 ("no per-source send gain, default full send") and the OPEN item about +0x54: the send is conditional, per voice, and +0x54 is NOT a send field.
- OpenAL is imported statically: alSourcei IAT 0xb104fc, alSource3i 0xb10504, alSourcef 0xb10508, alSourcePlay 0xb10518, alSourceStop 0xb10500, alGenSources 0xb10510
  (only alEffectf and the EFX calls go through alGetProcAddress pointers). So the aux send is observable by wrapping two IMPORT slots (no code byte, allowed in SHIP).
- Voice = ZSoundBufferOpenAL (vtable 0xb9ad5c, base voice vtable 0xb9a89c; ctor 0x71d480 / 0x74785x; size 0x43d0). Slots: +4 create 0x658340, +0x10 play 0x5dbd50.
  Fields: +0x10 byte send3d, +0x11 byte send2d, +0x54 dword relative (arg 2 of the init), +0x5c gain (1.0), +0x60 wave descriptor ptr (its +0xa bit 0x80 = streamed,
  +0xc / +0x14 / +0x1c sizes), +0x78 kind (1 in-memory, 3 streamed), +0x43bc AL source id, +0x7d/+0x7e play bookkeeping.
- Voice init 0x4465f0 (called by create): its 3rd argument is the sound's flag byte: send3d = !(flags >> 5 & 1), send2d = (flags >> 6) & 1. Arg 2 -> +0x54.
- Create 0x658340: alGenSources, then alSourcei(src, AL_SOURCE_RELATIVE 0x202, +0x54 != 0). Then, iff the listener says EFX is on (listener vtable +0xd8)
  AND +0x54 == 0 AND +0x10 != 0: alSource3i(src, 0x20006 = AL_AUXILIARY_SEND_FILTER, [listener + 0x23c18] = the aux slot, 0, 0). (site 0x6584a7)
- Play 0x5dbd50: alSourceStop, set AL_LOOPING (0x1007), alSourcePlay (site 0x5dbe12, return address 0x5dbe18), THEN iff +0x54 != 0 AND +0x11 != 0:
  alSource3i(src, 0x20006, [[voice+4] + 0x23c18], 0, 0) (site 0x5dbe49). So a relative (2D) voice only gets the send after it started playing.
- => gunshots: a world voice (3D) has the send unless its sound flag bit 5 is set. A gun voice played relative to the listener (the player's own gun?) has it only with bit 6.
  OPEN: which flag bits the gun sounds (.SND sound, the 4 flag bytes after the cone fields, audio.md 2.2) carry, and whether player shots are played relative.
  The 4 flag bytes of `*_shot_player#sound` vs `*_shot_npc#sound` in the .SND (tools/kl_snd.py) would answer it offline: not done here.
- No per-source send gain/filter is ever set (alSource3i's last two args are 0 = no filter): a voice with a send gets the full wet signal of the one global slot.
- Other alSourcePlay callers (not Play): 0x43d3bb (vtable slot 0xb9ada8, probably resume), 0x4893ca (a second voice class). alSourceStop callers 0x4e65de, 0x74d01b.

## 7. [Echo] Probe=1: the one live A/B (TEST build; logs only, changes no sound)
Build: klhook/out_echoprobe1108_test (TEST, has klauto, for the bench) and out_echoprobe1108 (SHIP: the probe works there too, import slots only). Source: klecho.c, klechoprobe_logic.h
(klechoprobe_test.c, 40+ checks in tools/kl_tests.py). Needs the game folder's KLHook.ini or the bench inst ini to carry:
```
[Echo]
Enable=1
Log=1
Probe=1
```
(Enable=0 + Probe=1 also works: the room lines then show the engine's values unchanged, which is the right A/B baseline for a sound comparison.)
Maps: (1) Dog Days stock DD09 (the usual bench map, many shots, bots) and (2) one Dead Men map with gunfights, e.g. DM05A or DM01B; run each as a normal 2-seat FA round
(kl_solo_test.py --hook klhook/out_echoprobe1108_test --tag EP_DD09 ... with the ini above in --ini1/--ini2), 300 s is enough once the bots shoot. Owner not playing (live run).
Grep the instance KLHook.log:
- `echo-probe: wrapped alSourcePlay + alSource3i` once (and whether alGetSource3i was found; MISSING = states are predicted from the flags, the lines say "predicted").
- `echo-probe play src N voice: <name> [gun-like] | rel R send3d A send2d B kind K gain G pred P | SEND ATTACHED / NO SEND / send expected right after play`
  (budget: the first 40 plays, then one line per new (name, state); max 500). `echo-probe dump voice ...` (12 lines): hex of the wave descriptor and voice fields,
  to decode the name layout if names show as `(unnamed kK)`.
- `echo-probe 10s: played N, send A (late L), no send B, unknown U | gun-like: send X, no send Y | no-send top: <name> xN ...` every 10 s, and `echo-probe total: ...`.
  `send attaches seen` = alSource3i(0x20006) calls observed (null slot = a detach).
- `echo-room #n t T: <kind> engine decay D refl R late L delay d -> sent ...` for EVERY SetReverb room change (DD09 should show changes as the bots move between rooms;
  a DM map should show none or one: no activaters, section 2).
How to judge:
- Gun-like plays WITH send (X large, Y ~0, the `*_shot_*` names SEND ATTACHED): the global reverb reaches guns; [Echo] Enable=1 (klecho_logic.h) will change gun tails. Next: owner listens.
- Gun-like plays WITHOUT send (Y large, `NO SEND` on shot names, rel 0 send3d 0 = flag bit 5 set; or rel 1 send2d 0): guns bypass the reverb. Then [Echo] cannot make them echoey: the options are
  re/gun_echo_1107.md section 5 item 3 (baked tails in the banks) or setting the send at Play (a code patch of the flag byte, TEST only first; flag bits: send3d = !(flags>>5&1), send2d = flags>>6&1).
- Mixed: compare the names. `rel 1` player guns without send but npc guns with send would explain "my gun is dry".
- `(foreign ret XXXXXX)` lines are alSourcePlay calls from other sites (not the voice Play): counted, named by return address.
- If the names are junk or `(unnamed)`, decode the wave descriptor from the dump lines (the name layout is a GUESS: best printable string behind a pointer of voice+0x60 / voice+0x18).
Cost: two import-slot swaps, one alGetSource3i + alGetError per played source (same thread as the engine's call), a spinlock; no files, no code bytes. Not run in the game.

## 8. Voice name decode (2026-11-08, static + the OSS_DD09_ECHO_S2 dump lines; TEST build klhook/out_echoname1108_test, not yet run)
Why "(unnamed k1)": voice+0x60 is NOT a descriptor with a name pointer. It is a **.WHD record minus 4** (the wave object's "WHD offset", re/audio.md 2.3) inside the loaded .WHD image.
- Proof in kl2.exe: voice init 0x4465f0 stores its arg1 at `mov [esi+0x60], edi` (0x44663b), then `test byte [edi+0xa], 0x80` (0x446641, format 0x00800000 = streamed: d+8 = record dword 1),
  `mul [edi+0xc]` (0x446677 / 0x4466a1, sample rate: the DM11S div-by-zero), `[edi+0x14]` (0x4466c1, size as PCM), `[edi+0x1c]` (0x446694, channels), `cmp word [edi+0x34]` (0x44664e, lip-sync word).
  The creator 0x658340 passes its args straight to 0x4465f0 (call at 0x658373); the ctors (0x71d480 from 0x843787, 0x747850) only set the vtable and zero +0x43bc/c0/c4: no name is stored in the voice.
- Record dword 0 (= desc+4) is the **name offset inside the .WHD file**, not a pointer. Dump `00000000 000064d0 00000011 00007d00 00000004 00002b06 00000c00 00000001 0016bc10 ...`
  = kaneandlynch.WHD record at 0x64f4 (name 0x64d0 = "SFX/OSD/Up_Down.wav", rate 0x7d00, size 0x2b06; checked with tools/kl_whd.py read-only). Name sits 16-aligned just before the record: desc = name + pad16(len+1).
  The two dumped descriptors differ by 0x70 and so do their name offsets (0x64d0 / 0x6460): the in-memory image keeps the file layout (offsets are base-relative). Both were k1 UI sounds (Menu / Up_Down), rel 1.
- Decode now: klecho_wave_name (klecho.c) reads 0x100 bytes before voice+0x60 (guarded klh_rd) and kpr_name_before (klechoprobe_logic.h) takes the nearest 16-aligned printable string with a "." or "/" that fits
  the padding and is not the tail of a longer name. Fallback: the old pointer scan. The name is the WAVE FILE name ("SFX/.../x.wav"), not the .SND `*_shot_*` sound name (nothing in the voice leads to it).
  GUESS: that the loaded image has the name bytes in memory right before the record (the offsets match the file layout, not verified by a name dump); if names stay "(unnamed)" the dump line
  `echo-probe dump voice ... wave W` still has the name offset (dword 1): map offline with tools/kl_whd.py (parse('dd', bytes of the level / kaneandlynch .WHD): name at that offset).
- Stable id fallback: (desc dword 1 = name offset, dword 8 = data offset) pair; which .WHD (level or global) is not in the voice.
