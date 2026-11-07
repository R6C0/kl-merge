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
