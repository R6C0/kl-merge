# Why "all guns still sound vanilla" (audit, 2026-11-07, offline, read-only)

Owner 11-07: "make gun shots more echoy or just adaptive to the environment ... all the guns need [the MP45 thing] as they all
just sound like vanilla ... i want them to sound raw". Nothing was launched or written in the game folder; measurements come
from the live banks read in place (`C:\Steam\...\Dog Days`), the pristine stock F01 bank in `KL_PortBackup`, and Dead Men's
M01_FA_A bank (`kl_dmgunsnd.records`). Scripts: scratchpad `an.py` / `rep.py` (not committed; metrics below are easy to redo).

## Root causes (short)

1. **The earlier passes only changed LEVEL and clipping, never timbre or space.** gunsnd_1024n / gunraw_1025 re-drive each
   record to the MP45 (Desert Eagle) head RMS and hard-clip it. The recordings are still Dog Days' own: spectral centroid, low-end
   share, HF share and decay length are the same as stock (table 2). Louder + clipped = the same sample, flatter. Crest factor
   fell 6.4 -> 3.1 dB and flat tops rose 4 -> 24 %, so it reads as "vanilla, squashed", not "raw".
2. **No echo / reverb has ever been installed.** `kl_gunsnd.py heat` (EQ + saturation + street/indoor IR tail, re/gun_sounds.md
   section 3) is a prototype that was run on DM03 copies and "nobody has listened"; no log entry installs it. Live clip lengths
   are identical to stock (dur column), distant layer included.
3. **Environment adaptation is not authored.** Stock F02 `.SND` has 3 room effects (inside_train, outside_coveredarea,
   outside_openarea); DM02's has 7 (f07 set: alley, loadingbay, metal_container, stairs, concrete_room, ...). Dead Men maps carry
   no `Audio_ReverbActivater` boxes (re/audio.md 4/10.6), so the rooms never switch. Whether gun shots are routed through the
   room effect at all is NOT established (GUESS, needs one live A/B).
4. **Group volumes untouched**: `sfx_weapons_shot_player` 0.70, `sfx_weapons_shot_npc` 0.35, `impactbullet` 0.35 in F02, DM02 and
   DD05 `.SND` (identical to stock). `[Sound] NpcShot/PlayerShot` hook keys proposed in gun_sounds.md section 4 were never built.
   Enemy fire is half the player's level, so distance/surround fire stays thin.
5. **Dead Men's own shots are cut to the Dog Days record length** (kl_dmgunsnd_build: "cut with a cosine fade to the record's
   CURRENT length"), so the DM look-alike guns on DM/DD KLExpansion maps lose the long DM tails (DM M4 1.22 s, Sig 1.25 s, Rem870 1.45 s)
   and are then raw-driven to the same clip level. Only 6 guns got DM clips (M4, Sig552, P90, Steyr TMP, MP5, USP).
6. **No near/far or first-person sample was missed.** Set chain: `<gun>_shot_player#set` and `<gun>_shot_npc#set` hold the same
   three `#sound` objects (same wave records); only the group volume differs. The one extra layer is the class-shared distant
   clip (HandGuns, AssualtRiffle, SubMachineGuns, Shotguns), 3.8 dB below the shots (head -6.9 vs -3.1) and unchanged in length.

## Did later installs overwrite the gun banks? No.

* All 42 banks of gunraw_1025 differ from its `output_md5` (every one "OTHER"), because fxraw_1025 and sndonline_1026 tier B rewrote
  other records in the same `.WAV`s afterwards (impact/glass/explosion, 6219 records). So md5 is the wrong check; the per-record
  check is `kl_gunsnd_all.py audit` (read-only): **2161 gun-shot records, 170 over target by 0.4 to 0.6 dB, which is the raw
  hard-clip overshoot allowed by `--raw` (+0.6 dB), none below target**. Stock F01-F09: only Shotgun_TPS_Shot_01 (-2.54 vs -3.15)
  and one more in L10; story L00-L11 all on target. So the levels are intact on every stock map, DM map and DD KLExpansion bank.
* Zips (`F02_Main.zip` etc.) hold only `.SND` + `.sgp`, no `.WAV`; pd2guns 1106*, pics, entries, glass chain rebuilds rewrite zips
  (Nov 6) and never the `.WAV`/`.WHD` banks. Sampled gun-bank `.WAV` mtimes: F02 Oct 26 19:27, DM02 Oct 27 00:26. Nothing re-stocked.
* Online: bots.zip is a plain zip with the same bank redirects (re/sound_online_1026.md); same `.WAV`, so same state.
* Patch01.zip (game root) holds no sound members; it is not an override path for these banks.
* PD2 guns (items 35-63): ordinary DD weapon templates whose shot is a DD `.SND` sound object (re/pd2_guns_page2_1025.md): they
  play stock DD gun clips (the clip of the template they were cloned from). A PD2 AKM bank test (1025b) was staged, never installed.

## Table 1: live banks (median over the 51 non-silenced shot clips per bank; distant = 4 class clips)

head = RMS dBFS of the first 250 ms after onset; crest = peak - head; flat = % samples within 2 % of peak in the head window;
centroid Hz of the head; lf = % energy under 200 Hz; tail = RMS 0.4-0.8 s relative to head; dur = time above -50 dBFS.

| bank | what it is | head | crest | flat % | centroid | lf % | hf>4k % | tail dB | dur s |
|---|---|---|---|---|---|---|---|---|---|
| F01 KL_PortBackup | pristine stock | -6.4 | 6.4 | 4.4 | 996 | 38 | 5.7 | -20.1 | 0.80 |
| F02 live (= all stock F0x) | gunraw + sndon | -3.1 | 3.1 | 24.2 | 1030 | 39 | 6.4 | -18.0 | 0.80 |
| DD05 KLExpansion live | DM look clips on 5 guns | -3.1 | 3.1 | 24.6 | 901 | 44 | 5.3 | -19.1 | 0.80 |
| DM02 live | DM look clips + raw | -2.8 | 2.8 | 25.0 | 1107 | 41 | 6.7 | -13.6 | 0.80 |
| distant F01 stock / F02 live | class layer | -11.3 / -6.9 | 11.3 / 6.9 | 0.5 / 3.1 | 509 / 500 | 48 / 46 | 1.3 | -19.6 / -17.7 | 0.7 |
| Dead Men M01_FA_A (54 shots) | original DM | -5.3 | 5.3 | 7.9 | **592** | **62** | 3.8 | -21.0 | **1.1** |
| Dead Men distant (36) | original DM | -11.8 | 11.8 | 0.1 | 387 | 54 | 0.2 | -19.7 | 1.0 |

Reading: levels and clipping changed (head, crest, flat), timbre did not (centroid, lf, hf, tail, dur within noise of stock).
Dead Men's guns are darker and fuller (centroid 590 vs 1000 Hz, 62 % vs 38 % under 200 Hz) and ring ~0.3 s longer: that is the
"raw/boomy" character, and it is exactly what the cut-to-length + clip passes removed from the six DM look guns.

## Table 2: per gun, stock F01 / live F02 (+ DM02 where it differs), first take of each gun

| gun | head dB | crest dB | flat % | centroid Hz | dur s | note |
|---|---|---|---|---|---|---|
| HG_DesertEagle (MP45 ref) | -3.2/-3.2 | 3.2 | 23.5 | 2288 | 0.81 | untouched, defines "MP45 raw" |
| HG_M9Beretta | -3.0/-3.0 | 3.0 | 23.7 | 994 | 0.79 | already raw in stock; DM02/DD05 = USP clip 528 Hz |
| HG_TaurusJudge | -3.1/-3.1 | 3.1 | 21.2 | 1211 | 0.69 | stock already hot |
| HG_ColtCobra | -6.6/-3.1 | 6.6->3.1 | 2.9->23.8 | 717->664 | 0.67 | gain + clip only |
| HG_M-77B | -7.6/-3.3 | 7.6->3.3 | 4.0->26.8 | 2892 | 0.60 | gain + clip only |
| HG_Revolver_Police | -6.4/-3.0 | 6.4->3.0 | 3.4->24.3 | 977 | 0.49 | tail -26.8 dB: nearly dry |
| Rifle_AK74 | -7.1/-3.1 | 7.1->3.1 | 4.0->23.7 | 1261->1335 | 0.85 | DM02/DD05 = DM M4 (835 Hz) |
| Rifle_FN_SCAR | -4.3/-2.9 | 4.3->2.9 | 8.2->23.3 | 347 | 1.23 | already dark/long |
| Rifle_Type88 / Type95 | -6.8/-3.0 | 6.8->3.0 | 1.1->24.5 | 1061 | 1.32 | the one with a real tail (-8 dB) |
| MG_GP_Type88 | -3.1/-3.1 | 3.1 | 23.2 | 1460 | 0.72 | untouched |
| MG_MiniMi_SPW (+Heli) | -5.1/-3.1 | 5.1->3.1 | 11.8->25.6 | 237->280 | 0.68 (heli 1.2->1.6) | |
| SMG_MPI69 | -8.4/-3.0 | 8.4->3.0 | 0.4->24.6 | 862->911 | 0.89 | biggest gain: +5.4 dB, tail -8.4 dB |
| SMG_MAC_10 | -6.9/-3.2 | 6.9->3.2 | 3.6->26.8 | 957->903 | 0.36 | tail -99: no decay at all |
| SMG_Type79 | -6.5/-3.1 | 6.5->3.1 | 4.7->23.2 | 1529->1425 | 0.70 | |
| SMG_*_Silenced (2) | -11.0/-6.9, -8.6/-6.9 | 11 -> 6.9 | 0.3->5.0 | 825/960 | 0.45/0.20 | left quiet on purpose (ref -3.7 dB) |
| Shotgun_Remington_870 | -4.0/-3.1 | 4.0->3.1 | 17.7->24.4 | 808 | 0.94 | |
| Shotgun_Spas_12 | -6.5/-3.0 | 6.5->3.0 | 3.2->23.7 | 555->531 | 0.49 | DM02 = DM Spas-like 1219 Hz |
| Shotgun_TPS | -2.6/-2.5 | 2.5 | 29.5->27.3 | 637 | 0.91 | the +0.6 dB under-target record |

DM02 centroids differ from F02 for ~35 further records (Cobra 664 -> 1326, TPS, Revolver, M-77B, Type88/95, Deagle +150 Hz):
GUESS: DM02's bank also carries the owner's 10-19..10-24 DM look passes and ADPCM re-encodes at other seeds; not traced further.

## Dead Men's own gun sounds as raw candidates (kl_dmgunsnd.py, M01_FA_A)

| DM clip | head | crest | flat % | centroid | lf % | tail dB | dur s |
|---|---|---|---|---|---|---|---|
| Assault_Rifle_M4 | -6.1 | 6.1 | 6.8 | 740 | 61 | -20 | 1.22 |
| Assault_Rifle_Sig_552 | -3.8 | 3.8 | 9.7 | 309 | 91 | -14 | 1.25 |
| Assault_Rifle_AK_74 | -5.3 | 5.3 | 7.8 | 842 | 67 | -20 | 0.90 |
| Assault_Rifle_RugerMini_14 | -5.3 | 5.3 | 8.7 | 485 | 69 | -10 | 1.08 |
| Pistol_HK_USP | -5.2 | 5.2 | 8.0 | 449 | 61 | -24 | 0.85 |
| Pistol_Taurus | -5.1 | 5.1 | 7.7 | 861 | 39 | -24 | 0.99 |
| Shotgun_Remington_870 | -3.5 | 3.5 | 19.9 | 531 | 53 | -15 | 1.45 |
| Shotgun_Spas_12 | -5.3 | 5.3 | 7.4 | 850 | 57 | -17.5 | 1.08 |
| Grenade_Launcher_HK_69 | -3.7 | 3.7 | 24.9 | 132 | 96 | -23 | 1.03 |
| Sniper Remington_700 (NPC) | -4.6 | 4.6 | 11.3 | 711 | 52 | -8 | 1.34 |
| Rocket_Rpg_7 / Tank_T72 | -3.2 / -5.0 | 3.2 / 5.0 | 20.6 / 8.9 | 1222 / 515 | 56 / 80 | -5 / -6.5 | 1.9 / 2.1 |
| Sub P90 / MP5 / Steyr TMP | -8.1 / -12.4 / -15.4 | 8-15 | 6 / 0.6 / 0 | 616-906 | 17-41 | -31..-39 | 0.4-0.8 (quiet, small) |
| Distant layers (AK74, Ruger, Rem870, Spas, Sig, Taurus, USP) | -10 .. -12 | 10-12 | 0.1 | 155-548 | 40-83 | -8 .. -22 | 0.7-1.5 |

DM full-size guns (Sig552, Rem870, Ruger, AK74, Spas, M4, Sniper) are the ones with real body and room tail; the P90/MP5/TMP
are weak (head -8..-15, 0.4 s) and are the worst candidates (which is why the six-gun DM set was level-matched upward with
+18 dB caps, amplifying their noise). Distant layers have many more variants (3 per class, up to 7 classes) than DD's 4
shared clips: an easy source of variety and long tails (Ruger/Rem870/Spas tail -8..-11 dB for 1.2-1.5 s).

## Fix plan (all as toggles; data = INSTALL/UNDO bat pair, runtime = ini key "(recommended on/off)")

A. **Timbre first, data-only, zero growth (`heat --fit` style)**: new pass `kl_gunsnd_all.py build --raw --body` that, before the
   existing hard clip, adds (per class) +4..6 dB low shelf at 120 Hz, a short transient emphasis (2-4 kHz, 3 ms), and mild
   saturation, then re-levels to the MP45 head. Skip the Deagle/M9/Judge/TPS/Type88 family (already raw). Records stay at stock
   length: .WHD/.SND/zips untouched. Offline preview wavs into D: (tiny) for the owner to audition BEFORE any install.
B. **Echo on the shared distant layer (4 records per bank) and on pistols/shotguns**: `heat --style street` full tail (2.6 s) for
   Distant_Shot_* and semi-autos; rifles/SMGs/MGs 1.0 s tail max (an auto gun with a 3 s tail = 30 overlapping voices). Growth
   about +3 MB per bank (32-bit address space: pair it with kl_wavslim, which frees ~10 MB). Needs the `.SND` wave seconds
   (+0x18) rewritten and the `.SND` repacked into the zip, so do stock F0x via the md5-chained installer.
C. **Use Dead Men's long tails**: for the six DM look guns stop truncating to the DD record length: append longer records (the
   rebuild() "longer" path, no geometry change) so M4 1.22 s / Sig 1.25 s keep their ring; take the distant variants from the DM
   Rem870/Ruger/Spas/Sig sets for the matching DD classes (`--distant-all`).
D. **Adaptive**: (1) cheap data pass: raise decay and reverb level of `outside_openarea` / `outside_coveredarea` (F0x) and
   `outside_alley` etc. (DM maps carry the f07 set) with in-place float writes in the `.SND` (as groupvol does); (2) author
   `Audio_ReverbActivater` boxes for DM maps in kl_fa_author (they have none); (3) hook key `[Sound] NpcShot=0.6 PlayerShot=0.85`
   (group volumes, 0.35/0.70 now) with a one-run check that the engine reads the live image value (gun_sounds.md 4 unverified).
   Do one OWNER-PRESENT A/B first to settle the unknown "do shots go through room effects?" (GUESS): stock F02, outside_openarea
   decay 1.3 -> 3 s, listen to one pistol outdoors.
E. Order: A + B previews (offline, now) -> owner listens -> install A+B on F01..F09 + KLExpansion banks + bots.zip path (same `.WAV`
   files) -> D(3) hook key -> D(1)/(2) after the A/B. PD2 guns need nothing extra: they follow their template's `.SND` sounds, so A-C
   cover items 35-63 on every map; a PD2-original shot (AKM bank 1025b) stays an optional later swap.
F. Risks: C: 6 GB free, D: 0.5 GB free (stage previews only, banks wait for space); all banks grow in the 32-bit heap; re-driving
   an already ADPCM clip a 3rd time adds generation loss (keep sources as the pre-raw backups `.before-1025gunraw` or the DM originals,
   never re-encode live).
