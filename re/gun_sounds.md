# snd - gun sounds for KL Merge ("Heat" gunfire)

Worker `snd`, 2026-10-15. Offline only: everything was measured on copies in `~/w_snd/` (F02 stock bank, the
installed DM03 map bank). Nothing was loaded by the game and the game folder was not written. There is no hook
patch: the deliverable is a tool, a processing prototype and a plan.

Files here:

| file | what |
|---|---|
| `kl_gunsnd.py` | list / extract / refs / replace / heat / groups / groupvol / selftest for a level bank (`.WHD` + `.WAV`, optionally `.SND`) |
| `weapons_F02.txt` | `list` output for stock F02: all 143 weapon records (shots, distant shots, reloads, clicks) |
| `preview/*_orig.wav` / `*_heat_*.wav` | the game's own clip decoded, and the same clip after `heat` (listen to these first) |

## 1. How Dog Days stores and plays gun sounds (MEASURED)

* **Not in `PC_Def.str`.** Gun shots are in-memory clips of each level bank: `<slot>_Main.WHD` (headers) +
  `<slot>_Main.WAV` (data, read whole into memory at load: klmem.c, 0x51cf80), both beside the zip. The stream
  file holds dialogue, music and long ambiences (Vorbis).
* Names: `SFX/Weapons_KL2_Final/<Gun>/<Gun>_Shot_01..03.wav` (three variations per gun) and one distant layer per
  class: `Common/Distant_Shots/{HandGuns,AssualtRiffle,SubMachineGuns,Shotguns}/Distant_Shot_*_01.wav`.
* Format of every one: **Microsoft IMA ADPCM (0x11), 4 bit, mono, 32,000 Hz, block align 0x400, 0x7f9 (2041)
  samples per block; data is stored as whole blocks** (e.g. 25,347 samples = 13 blocks = 13,312 bytes).
  Lengths 0.2 s (silenced SMG) to 1.6 s (heli MiniMi); pistols ~0.6-0.8 s, rifles ~0.9-1.3 s. The 61
  shot/distant clips take 799 KB.
* **Same clips in every FA bank**: F01-F09 and all eight of our `KLExpansion/Maps/<id>` banks (DM01 DM02 DM03
  DM03A DM05A DM06 DM09 T01) have the same 61 shot/distant records; story levels L00-L11 have 15-39. So a change
  has to be written into each map's own bank (the tool takes the same name list for every bank).
* Chain in the `.SND` (per gun, e.g. M9 Beretta in F02):
  `hg_m9beretta#def` (13 slots: [0] dry fire, [1] `..._shot_npc#set`, [2] bullet flyby set, [3] empty,
  [4] `..._shot_player#set`, [5] shell drop set, [7] ammo pickup, [8] weapon change, [6] [9-12] empty)
  -> each `#set` lists `shot_01..03#sound` **and** `distant_shot_01#sound` -> each `#sound` (+0x14) points at a
  `#wave` object -> the wave (+0x14) points at the `.WHD` record (offset - 4), +0x18 = length in seconds (f32).
  The set's parameters (type 8: -100/100 ... -4.5; type 4: 3, 15.0, two curve pointers) are probably pitch /
  volume randomisation and a near/distant crossfade distance (15 m?) - **meaning NOT established**.
* Volumes are group objects in the `.SND` (f32 at +0x24, same value at +0x30): `sfx_weapons_shot_npc` **0.35**,
  `sfx_weapons_shot_player` **0.70**, `sfx_weapons_impactbullet` 0.35, `_impactbullet_player` 0.63,
  `sfx_weapons_shelldrop` 0.5, `sfx` 0.39 (same in F02 and DM03). Enemy gunfire plays at half the player's level.
* Reverb: `#roomeffect` objects (type 7, 0x50 bytes) hold **I3DL2 / EAX-style parameters** (room -1000 mB,
  room HF, decay time s, decay HF ratio, reflections mB + delay, reverb mB + delay, HF reference 5000, diffusion,
  density), e.g. `f07/.../outside_alley`: decay 1.3 s, `outside_coveredarea`: 4.1 s. kl2.exe imports DSOUND.dll
  (and names OpenAL32.dll / EAX). They are switched by `Audio_ReverbActivater` boxes in the level. **Our Dead Men
  maps have no reverb at all** (re/audio.md 4 and 10.6: Dead Men rooms carry no Dog Days room effect and no boxes
  were authored) - one reason the gunfire on our maps sounds dry.

### Can a sound be replaced, and does the length matter?

Yes, and offsets are safe because **nothing points at clip data except its own `.WHD` record**:

* The `.WHD` keeps its layout; only the record's pcm-bytes / data-bytes / data-offset / samples fields change.
  The `.SND` points at the record, not at the data.
* Equal or shorter: written in place in the `.WAV` (old span zero-filled). Longer: appended to the end of the
  `.WAV` (16-aligned), record moved there, `.WAV` header size (+4) updated. Nothing else moves.
* The `.SND` wave object's seconds field (+0x18) is rewritten for longer/shorter clips when `--snd` is given (same
  file size). Whether the engine reads it is not known; kept consistent. That changed `.SND` has to go back into
  `<slot>_Main.zip` (e.g. `tools/kl_hud_menu.py _rezip(src, dst, {'scenes/locations/f03/f03_main.snd': data})`).
  `--fit` mode keeps every clip at its stock length, so the `.SND` and the zip stay untouched.
* Checks run (`selftest`, plus `verify` after every write): no-op rebuild is byte-identical (WHD and WAV); a
  re-encoded stock clip has the same sample and byte count (-30 to -46 dB re-encode error = normal 4-bit IMA);
  every replaced record re-parses and decodes to its sample count; the `refs` command found exactly one wave
  object per shot record (the AR distant layer has two).

## 2. The tool

```
python kl_gunsnd.py list     <bank.WHD> [regex]               # default /weapons/
python kl_gunsnd.py refs     <bank.SND> <bank.WHD> [regex]    # wave + #sound objects that use each record
python kl_gunsnd.py extract  <bank.WHD> <outdir> [regex]      # decoded 16-bit .wav files
python kl_gunsnd.py replace  <bank.WHD> <outdir> <map.txt> [--snd <bank.SND>]
        map.txt:  SFX/Weapons_KL2_Final/HG_DesertEagle/HG_DesertEagle_Shot_01.wav = my_shot.wav
        (any PCM/float wav, any rate/channels: resampled to 32 kHz, mixed to mono, IMA-encoded)
python kl_gunsnd.py heat     <bank.WHD> <outdir> <regex> [--style street|indoor] [--tail s] [--fit] [--snd <bank.SND>]
python kl_gunsnd.py groups   <bank.SND>
python kl_gunsnd.py groupvol <bank.SND> <out.SND> sfx_weapons_shot_npc=0.6 sfx_weapons_shot_player=0.85
python kl_gunsnd.py selftest <bank.WHD>
```

Outputs always go to a new folder; the tool never writes its inputs. numpy only (scipy is not installable in
the VM). Reads `.WHD` the way re/audio.md 9.3 (whd.py) does; IMA decoder after luvsic's
`third_party/anp/loader/adpcm.h`; the encoder is the standard IMA quantiser, written here.

Recommended regex for "all guns, not the silenced ones":
`^(?!.*Silenced).*(_Shot_0\d\.wav|Distant_Shot|Shotgun_Hawk_Police_0\d)` (58 clips in DM03: 55 shots + distant layers, 3 police Hawk shotgun).

## 3. "Heat" design

What the film's street fight has that the game lacks: a heavy low-mid punch, raw clipped loudness, and long
slap-back echoes off buildings, with the distant fire of the others rolling under your own.

Prototype (`heat`, implemented, run on DM03's copy):

1. EQ (zero-phase, FFT): +5 dB low shelf at 120 Hz (body), +3 dB around 2.5 kHz (crack), -2 dB at 450 Hz (box),
   cut below 30 Hz.
2. Saturation: tanh drive 2.2 - dense and "raw".
3. Echo tail by convolution with a **self-generated** impulse response: `street` = 7 discrete slap echoes
   45-900 ms (building faces) + a 2.6 s diffuse noise tail, darker with time (air absorbs highs); `indoor` = dense
   early reflections + 1.0 s tail. Wet signal high-cut at 3.5 kHz, mixed under the dry.
4. Soft limiter (tanh) and -0.5 dBFS peak; trim below -60 dB, 50 ms fade.

Measured on the previews (orig -> heat):

| clip | length | first 100 ms | 40-200 Hz share | level 0.8-1.6 s |
|---|---|---|---|---|
| HG_M9Beretta_Shot_01 street | 0.79 -> 2.91 s | -2.6 -> -2.7 dBFS | 19 -> 32 % | silent -> -24 dBFS |
| HG_M9Beretta_Shot_01 indoor | 0.79 -> 1.46 s | -2.7 dBFS | 19 -> 28 % | -> -39 dBFS |
| Rifle_AK74_Shot_01 street, --tail 1.2 | 0.87 -> 1.71 s | -5.4 -> -3.6 dBFS | 20 -> 37 % | -46 -> -30 dBFS |
| Distant_Shot_HandGuns_01 street | 0.68 -> 2.90 s | -6.4 -> -4.5 dBFS | 13 -> 38 % | silent -> -26 dBFS |

Nobody has listened to them yet - the numbers say "heavier and longer", the ear decides.

Plan, per gun class (all with the game's own clips):

* **Pistols / revolvers / shotguns** (semi-auto): `--style street` full tail (2.6 s) on outdoor maps.
* **Rifles / SMGs / MGs** (automatic, ~10 shots/s): short tail `--tail 1.0-1.2`; a 3 s tail on every round
  means ~30 overlapping voices per gun and the mix turns to mush (and may hit a voice limit). The long roll goes
  on the **distant layer** instead.
* **Distant_Shot_*** (one per class, shared by every gun of that class): the biggest "Heat" win - full street
  tail, heavier low end. This is the far gunfire you hear across the street.
* Leave silenced guns, reloads, clicks alone.
* **Per environment = per map bank**: every map has its own bank, so outdoor maps (the bank / street maps) get
  `street`, interior maps get `indoor`. No hook needed for that.
* **Louder**: `groupvol sfx_weapons_shot_npc=0.6 sfx_weapons_shot_player=0.85` (from 0.35 / 0.70). In-place
  float write in the `.SND` (needs the zip repack). Raising NPC fire nearer to the player's is what makes a
  firefight feel like it is all around you.
* **Echo engine-side**: tune `outside_*` room effects in the bank (decay 1.3 -> ~3 s, reverb level up) and author
  `Audio_ReverbActivater` boxes on our Dead Men maps (they have none). That is level work, outside this tool.

Cost: the full street set (64 clips) grows DM03's `.WAV` 22.7 -> 25.7 MB (+3.0 MB in the 32-bit address space
klmem.c is fighting for); `--fit` costs 0 bytes (EQ/saturation/short tail only, cut at stock length).
Do Distant_Shot + pistols at full length and rifles at `--tail 1.0` for about half of that; `kl_wavslim` already
frees 10 MB on these banks.

### Sourcing - honest note

* Only **the game's own clips processed** (what `heat` does), **self-generated** material (the IRs in
  `synth_ir` are made from seeded noise and a few delays - no third-party audio), or samples that are clearly
  **CC0 / public domain** with the licence saved next to them.
* **Never** rip from Heat (the film), other films, or other games (Battlefield, Payday 2, etc.), however
  tempting. Not for "just a test" either: the mod gets shared.
* Even "free" packs often say royalty-free but no redistribution - check before shipping inside a mod.

## 4. A runtime layer in the hook? (feasibility only)

* **Group volumes: cheap and feasible.** The `.SND` is used in place as a memory image (re/audio.md 2: pointers
  are file offsets, the engine adds the base). A hook on the image hand-over (ZDllSound vtable 0xb9a3ec slot 35,
  0x402000) or a scan for the `audio:groups/sfx_weapons_shot_npc#group` string after load could write +0x24/+0x30
  from INI keys (e.g. `[Sound] NpcShot=0.6 PlayerShot=0.85`). Unverified: whether the engine copies the value
  into its own mixer group at load (then it would have to be written before slot 35 runs) - one live run decides.
* **Per-environment echo variants at runtime: not cheap.** Switching which clip a shot plays would mean
  rewriting set lists / wave pointers in the live image on a trigger, plus knowing the player's environment.
  The engine already has the right mechanism (room effects via `Audio_ReverbActivater`); a hook could force one
  room effect for the whole map (an outdoor preset on our Dead Men maps), but that needs RE of the
  activater -> ZDllSound call (address not known). Doing it offline per map bank is far simpler.
* **An extra distant layer at runtime**: the sets already contain the distant clip; how the engine picks between
  near and distant (the type-4 parameter with 15.0) is not traced. Changing the distant clip offline is the
  realistic route.

## 5. How to test live (for the lead; nothing here was run in the game)

1. Lowest risk first - `--fit` (only the two beside-files change, the zip does not):
   `python kl_gunsnd.py heat <DM03>/F03_Main.WHD <out> "^(?!.*Silenced).*(_Shot_0\d\.wav|Distant_Shot)" --fit`
   (measured on DM03: the .WHD comes out byte-identical, 55 clips rewritten in place in the .WAV) then swap `F03_Main.WHD` + `F03_Main.WAV` of a test tree's DM03, load it, fire every gun, listen for clicks or
   noise (an encoder fault) and whether the guns sound heavier.
2. Full tails: same with `--snd <F03_Main.SND extracted>` and without `--fit`; put the `.SND` back into the zip;
   watch KLHook.log's klmem 'largest block' line for the 3 MB larger `.WAV`.
3. Volumes: `groupvol` on the `.SND`, repack, compare enemy fire by ear.

## 6. Risks / unverified

* Not loaded by the game. The encoder writes standard MS IMA blocks with the same block size, samples per block
  and whole-block padding as stock, but a decoder quirk would only show in game.
* Longer clips: unknown voice limit / voice stealing in ZDllSound; unknown use of wave +0x18 seconds.
* Group volume semantics (+0x24 vs +0x30) are read from stock values, not traced.
* The set / sound parameter meanings (distance, randomisation) are not established.
* Memory: +3 MB for the full set on a 32-bit process already near its limit on some maps.

## 7. Gun sounds matched to the S&W MP45 (2026-10-24, owner: "make the guns wavesound like the sw mp45 ... loudness ... getting distorted")

* The MP45 has no clips of its own: `hg_sw_mp45` plays the **HG_DesertEagle_Shot_01..03** records (re/map_guns.md, in every bank).
  Measured (head = RMS of the first 250 ms after the onset, 32 kHz decode): head **-2.8 dBFS**, crest 2.8 dB, ~7 % of the samples sit
  AT the ceiling (hard-clipped at the source), envelope above -7 dB for 250 ms. Others: AK74 -7, Type79 -6.5, MPi69 -8.3, MAC-10 -8.8,
  silenced SMGs -9..-11.6, M9 -5, distant layers -8..-14, rifles/revolvers -3.3..-4.4. Every stock clip already peaks at 0 dBFS, so the gap is
  RMS/sustain, not peak.
* `tools/kl_gunsnd_match.py` (`analyze` / `build` / `verify` / `manifest`): per map bank, every `_Shot_0N`, `Distant_Shot_*` and Hawk police
  record except the Desert Eagle reference is decoded, gain-driven (bisect, cap +18 dB) into a knee soft clipper (linear to 0.8, tanh above)
  until its head RMS equals the reference's (silenced and distant layers: reference - 3.7 dB), 30 ms end fade, re-encoded into the SAME
  record (same sample count, same bytes). WHD, SND, zips and all other records stay byte-identical; only the 61 records' data spans in each
  `.WAV` change (about 0.26..0.33 MB per map). 27 maps (all KLExpansion banks, so the Dead Men gun clips already written by
  kl_dmgunsnd_build are included, and the stock DD01-09 copies).
* The disk was full while building (G: 88 KB, C: 5 GB), so the staging holds SPANS (`Maps/<id>.new` / `.old`, 53 MB total), not 27 WAV copies;
  the installer patches in place, md5-checks input and output, and UNDO writes the old bytes back (md5-checked).
* Staged: `<work>\build\gunsnd_1024c\` (`INSTALL gun sounds.bat`, `UNDO gun sounds.bat`, `AB_LIST.txt`, `preview\*_A_before.wav` / `*_B_after.wav`
  from DM01). That pair IS the on/off ("gunsound", recommended on): no hook part, no ini key. mod_options row to add by hand:
  `gunsound - Gun fire sounds as loud/driven as the S&W MP45 (recommended on)`, switch = INSTALL / UNDO gun sounds.bat.
* Not changed: the `.SND` group volumes (`sfx_weapons_shot_player` 0.70 / `_npc` 0.35) - the NPC half-level stays. Not listened to in game.
* Risk: harder-driven clips (MAC-10 +16 dB, MPi69 +13..15 dB, Type79 +9 dB, AK74 +6..8 dB) also lift their decay tails and ADPCM noise by the
  same gain; full-auto guns will sound denser. If one is too harsh, lower `MAXGAIN` in the tool and rebuild.

## 8. One loudness on EVERY bank (2026-10-24 night; owner: "some guns arent at the same loudness ... applied to all maps")
Audit (tools/kl_gunsnd_all.py audit, head RMS 250 ms vs the bank's own Desert Eagle = MP45): the section-7 pass only touched the 27
KLExpansion\Maps banks. Dog Days' 9 stock FA slots (Scenes\Locations\F01..F09) and the story levels L00..L11 were never processed: 54 of 61
shot records per stock bank are off by up to -5.2 dB (guns), -4.7 (silenced), -11.2 (Distant_Shot_AssualtRiffle, head -18). The 27 map banks
are on target (0 records beyond 0.35 dB; the DM maps' own Deagle sits at -2.87, the others at -3.15, a 0.28 dB bank-to-bank difference left as is).
Pass staged: C:/kl_build_1024/gunsnd_1024n (21 banks, 777 records, 10.5 MB of spans, WHD/SND/zip/hti untouched, sizes identical).
Left alone on purpose: RPG7 launch (-5), Rpg_Loop, explosions, reload/cock/dry-fire, npc 0.35 / player 0.70 group volumes (+0x24/+0x30 in the
.SND; design choice), the first 70 ms of some guns (M9, Type88/95, silenced are 1.5-2.7 dB softer in the attack than the Deagle's).
Sound-object +0x20 (int16) looks like pitch in cents, not volume (about 85 %, data-based); not touched.
