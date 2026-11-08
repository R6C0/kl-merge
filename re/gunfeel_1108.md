# Gun feel 1108: why the MP45 is "the best", and gunpunch_1108 (offline, nothing installed, game not touched)

Owner 11-08: "make the guns more raw, i still feel like the mp45 is the best, none of the other guns give the same delivery as it".
Tool `tools/kl_gunpunch.py` (on top of `kl_gunsnd_all.py`), stage `C:\kl_build_1024\gunpunch_1108`. Table columns (`kl_gunpunch.py measure [bank]`):
peak / head RMS 250 ms (dB), crest, trans = RMS first 20 ms over RMS 60-250 ms (dB), centroid Hz and band shares % of the first 60 ms,
flat = % of the head window at the clip's own peak (DC kept: the clips carry DC), tail = RMS 0.4-0.8 s vs head (dB), d20 = ms until the 10 ms envelope is 20 dB down.

## 1. What the MP45 is (PROVEN, measured)
The MP45 (`HG_SW_MP45`) has no clips of its own: it plays `HG_DesertEagle_Shot_01..03`, which every raw pass (gunsnd 1024, gunraw 1025, gunraw 1107) left
untouched as the reference. Its clip: head -3.2, flat 20 %, a clean front (trans 3.0 dB), energy in the mids (120 Hz-500 Hz 33 %, 500 Hz-2 kHz 50 %, only 4 % under 120 Hz,
centroid 1104 Hz), and a SHORT DRY DECAY (tail -20.5 dB, d20 455 ms).

## 2. Why the others do not deliver the same (PROVEN by the live tables below)
After gunraw_1107 every gun has the MP45's head level and flat-top share, but not its shape. The raw body pass added a +4..6 dB low shelf at 120 Hz and an echo tail,
and the hard clip to 20 % flat needs +10..18 dB of drive, which lifts the quiet tail by the same amount:
- tail -5 .. -15 dB (MP45 -20.5): Type95/88 -5.7, Remington 870 -5.3, SCAR -5.4, TPS -3.8, MPi69 -6.5, Hawk -9.6, MG -8..-10: a wash behind the shot;
- transient 0..2 dB on the rifles / MG / shotguns (MP45 3.0): Type95 0.1, Remington 0.3, GP Type88 1.0, MPi69 1.0: no front;
- 30..80 % of the energy under 120 Hz on MG / SCAR / shotguns / SMGs (MP45 4 %): boom, not crack.
Only the pistols (M9, M-77B, Judge, Cobra) were already close in shape. The distant layers and silenced clips are meant to be quiet and stay as they are.

## 3. Gameplay delivery (data, F02 templates, `ZFFItemTemplateWeapon`; field numbers = kl_rtp property index, names unknown unless noted)
| field | MP45 | SigSauer | M9 | DesertEagle | AK74 | SCAR | Type79 | MAC10 | Hawk Police | GP Type88 |
|---|---|---|---|---|---|---|---|---|---|---|
| rpm (27) | 300 | 390 | 350 | 250 | 650 | 600 | 650 | 1200 | 150 | 900 |
| NPC damage mult (37) | 1.7 | 1.5 | 1.5 | 1.5 | 0.8 | 0.6 | 1.0 | 0.8 | 0.4 | 1.0 |
| Arcade band 1 mult (39) | 2.5 | 2.5 | 2.3 | 1.3 | 0.9 | 0.9 | 1.6 | 1.6 | 1.0 | 1.0 |
| mag (43) | 32 | 30 | 32 | 28 | 120 | 120 | 120 | 120 | 20 | 250 |
| f53 | 1.6 | 1.3 | 1.35 | 1.75 | 1.2 | 1.2 | 0.9 | 0.6 | 4.0 | 0.8 |
| f93 | 2.3 | 1.6 | 1.1 | 3.0 | 7.0 | 6.0 | 1.75 | 1.5 | 3.0 | 2.0 |
The MP45 is the hardest-hitting gun per bullet (361 at 10 m, AK74 65: re/balance.md 3) at a slow 300 rpm: every shot is an event. That is gameplay delivery, and it is
BALANCE: not touched. Camera shake / recoil: no field of the template is named in any note and none of f53 / f93 / f20 / f35 is proven to be recoil (GUESS: f53 and f93
are recoil / spread-like, they do not rank guns the way the MP45's feel does: the Hawk has f53 4.0). The per-shot camera kick is run-time code in kl2.exe that was never read
(re/camera.md shaker = 41 movement-state floats, not shots). So NO feedback change was made: DEFERRED until the kick site is read (needs the disassembly, no game run).

## 4. gunpunch_1108 (data, "(recommended on)" = INSTALL, off = UNDO)
Per gun record, from its PRE-RAW source (`.before-1025gunraw`, else `.before-1107gunraw`; 1307 of 2161 from the 1025 backup, 854 from the 1107 backup; the live gunraw clip is
never re-encoded): sub cut, small low shelf, 900 Hz body + 2.8 kHz crack + air (the MP45 spectrum), transient emphasis (first ~10 ms up to +6 dB before the saturation), tanh drive,
the SAME hard clip to the MP45 head level / flat-top share (no clipping beyond it, peak <= full scale), then a tail duck from 120 ms that goes only as far as needed to reach a
class tail target (pistol -20, SMG -18, rifle -16, shotgun / MG -14 dB; floor -9..-12 dB). Distant and silenced layers keep their tails. Rooms are the hook's job (`[Echo]`, live).
Same offsets / sizes: WHD, .SND, zips and every other record byte-identical. Banks: 42 (21 maps, 9 stock, 12 story), 2161 records, 29.9 MB of spans. Stock DD banks are handled
exactly like gunraw_1107 (in place, md5-chained, backups next to the bank: `*.WAV.before-1108gunpunch`). Online uses the same banks (bots.zip redirects): nothing else to change.
After (F02 applied in memory): tails -12.5 .. -21 (rifles -15.6 .. -17.6, pistols -19.7 .. -21.3, MP45 -20.5), heads -2.6 .. -3.7 (a few clips 0.3-0.5 dB under the old target: the
duck lowers the head window slightly; verify tolerates it), transient 0..3.5, lt120 on pistols/rifles 1..12 %. MG / SCAR / TPS stay bass-heavy by nature (33..57 %).
Open (GUESS, unheard): Remington 870 and GP Type88 still have transient ~0 (their source has no sharper front); the targets in PUNCH are tastes, not measured needs.

## 5. Tables (F02 first take of each gun)
```
BEFORE (live F02 = gunraw_1107)
gun                               peak    head   crest   trans    cent   lt120b120_500 b500_2k   b2_6k    flat    tail     d20
HG_M9Beretta                       0.0    -2.6     2.6     0.7  2160.9     4.4     7.8    54.4    25.8    22.8   -15.2   590.0
HandGuns                           0.0    -6.9     6.9     2.8   826.7    24.2    26.0    40.6     7.8     0.1   -13.0   525.0
HG_M-77B                           0.0    -2.7     2.7     1.9  3145.9    13.1     7.9    26.9    37.3    23.3   -14.3   495.0
Rifle_Type95                       0.0    -2.6     2.6     0.1  1290.7    33.4    29.7    13.1    19.5    22.7    -5.7   835.0
AssualtRiffle                      0.0    -6.8     6.8     5.4   679.1    54.0    22.0    14.8     7.7     0.0   -10.6   505.0
Rifle_Type88                       0.0    -2.6     2.6     0.1  1354.7    30.6    31.0    14.5    18.9    21.8    -5.8   835.0
MG_MiniMi_SPW_Heli                 0.0    -3.1     3.1     2.8   188.1    82.1    13.5     3.1     0.9    21.0   -17.0   360.0
Shotgun_Spas_12                    0.0    -3.1     3.2     3.0  1156.8    35.6    25.4    22.8    11.3    24.2   -15.2   455.0
MG_GP_Type88                       0.0    -2.8     2.8     1.0   970.5    73.0     5.0     9.7     6.2    21.4   -10.0   560.0
Rifle_AK74                         0.0    -2.7     2.7     2.0  1290.3    16.4    36.0    29.5    13.8    21.9   -14.2   550.0
HG_DesertEagle                     0.1    -3.2     3.2     3.0  1104.4     4.0    33.5    49.7    11.0    20.0   -20.5   455.0
HG_TaurusJudge                     0.0    -2.7     2.7     0.6  2061.6    35.1     9.5    22.7    22.3    21.9   -14.0   555.0
Shotgun_Remington_870              0.0    -2.8     2.8     0.3  1408.7    17.4    41.3    16.8    18.9    21.1    -5.3   830.0
Shotguns                          -0.1    -6.8     6.8     1.5   329.2    71.0     9.8    17.8     1.2     0.0    -6.8  1205.0
Shotgun_Hawk_Police                0.0    -3.1     3.1     2.8   879.2    19.5    45.3    20.7    12.9    21.6    -9.6   715.0
Rifle_FN_SCAR                      0.0    -3.1     3.1     3.2   365.3    78.7     9.4     6.8     3.8    29.3    -5.4   600.0
SMG_Type05_Silenced                0.0    -6.9     6.9     6.5  2008.7    28.5    26.9    14.5    18.9     0.5   -99.0   145.0
SMG_MAC_10                         0.0    -3.2     3.2     2.6  2834.4     6.4    19.2    31.4    28.9    28.2   -99.0   275.0
SubMachineGuns                     0.0    -6.8     6.8     2.7  1139.7    21.4    20.2    42.5    13.7     0.0   -12.4   615.0
HG_Revolver_Police                 0.0    -2.7     2.7     1.2  2204.1     6.0     9.2    47.7    29.3    22.2   -20.4   405.0
HG_ColtCobra                       0.0    -3.2     3.2     2.2  2721.8     2.0    11.8    30.5    48.4    22.8   -14.3   510.0
SMG_MPI69                          0.0    -2.5     2.5     1.0   868.1    52.7    17.7    16.5    10.3    21.5    -6.5   725.0
SMG_HK_SP89_Silenced               0.0    -6.8     6.8     7.0  1462.6    29.7    17.6    31.7    15.0     0.2   -39.9   225.0
SMG_Type79                         0.0    -2.6     2.6     1.7  1734.8    34.4    15.3    27.0    14.1    21.7   -16.3   520.0
Shotgun_TPS                        0.0    -3.0     3.1     1.7   671.1    60.8    22.9     7.8     5.6    21.3    -3.8   755.0
MG_MiniMi_SPW                      0.0    -3.1     3.1     3.5   658.7    62.7    20.9     6.4     7.5    27.8    -8.3   570.0

AFTER (gunpunch_1108 applied in memory to F02)
gun                               peak    head   crest   trans    cent   lt120b120_500 b500_2k   b2_6k    flat    tail     d20
HG_M9Beretta                       0.0    -2.6     2.6     0.9  2043.0     1.4     8.5    60.1    23.0    23.4   -21.3   445.0
HandGuns                           0.0    -6.9     6.9     2.8   930.8    14.0    28.7    47.3     8.4     0.0   -13.2   525.0
HG_M-77B                           0.0    -3.1     3.1     2.4  3242.0     4.0     8.8    32.4    41.1    20.7   -19.8   470.0
Rifle_Type95                       0.0    -3.0     3.0     1.0  1618.1    11.8    37.1    21.4    24.7    14.7   -15.6   565.0
AssualtRiffle                     -0.0    -6.9     6.9     5.6   797.0    40.3    30.2    18.9     9.0     0.1   -11.3   505.0
Rifle_Type88                       0.0    -2.9     2.9     0.8  1614.2    12.1    38.5    21.0    22.9    14.4   -15.5   565.0
MG_MiniMi_SPW_Heli                 0.0    -3.2     3.2     3.5   362.7    56.6    30.3     9.5     2.7    28.5   -15.8   495.0
Shotgun_Spas_12                    0.0    -3.2     3.2     3.4  1632.8    11.4    32.8    33.3    15.2    28.2   -17.1   430.0
MG_GP_Type88                       0.0    -3.5     3.5    -0.1  1981.5    29.5    21.1    22.0    15.3    14.1   -13.6   505.0
Rifle_AK74                         0.0    -3.0     3.0     2.4  1385.9     4.0    38.5    38.6    14.9    21.1   -17.6   470.0
HG_DesertEagle                     0.1    -3.2     3.2     3.0  1104.4     4.0    33.5    49.7    11.0    20.0   -20.5   455.0
HG_TaurusJudge                     0.0    -3.4     3.4     1.4  2803.4     4.2    14.2    36.1    32.5    15.3   -19.6   475.0
Shotgun_Remington_870              0.0    -2.9     2.9     0.0  1516.7     7.0    43.4    23.7    20.5    16.2   -12.5   740.0
Shotguns                          -0.2    -6.8     6.7     1.4   444.5    57.4    14.5    26.3     1.5     0.0    -6.9  1205.0
Shotgun_Hawk_Police                0.0    -3.1     3.2     3.2  1003.7     7.6    51.0    25.6    14.0    25.7   -15.9   555.0
Rifle_FN_SCAR                      0.0    -3.4     3.4     2.5  1070.8    33.7    24.9    26.6    10.2    25.5   -15.7   475.0
SMG_Type05_Silenced                0.0    -6.9     6.9     6.6  2441.5    12.3    31.0    20.2    22.9     1.3   -99.0   135.0
SMG_MAC_10                         0.0    -3.3     3.3     3.1  2687.4     3.7    20.3    35.8    27.5    31.5   -99.0   295.0
SubMachineGuns                     0.0    -6.8     6.8     2.2  1187.3     9.7    26.7    47.6    13.9     0.1   -12.2   615.0
HG_Revolver_Police                 0.0    -3.0     3.0     1.7  2031.3     1.6     8.9    56.6    26.9    21.6   -28.8   370.0
HG_ColtCobra                       0.0    -3.3     3.3     2.8  2660.6     0.9    12.5    32.9    46.6    21.8   -19.8   450.0
SMG_MPI69                          0.0    -3.7     3.7     2.4  1207.1    25.7    26.5    29.6    15.0    13.3   -17.4   505.0
SMG_HK_SP89_Silenced               0.0    -6.9     6.9     6.5  1797.1     8.4    23.1    42.7    18.7     1.0   -41.9   220.0
SMG_Type79                         0.0    -3.1     3.1     1.4  2104.1     4.8    21.9    45.1    18.1    16.7   -17.8   460.0
Shotgun_TPS                        0.0    -3.3     3.3     2.3  1189.7    33.4    35.7    15.1    10.3    19.5   -11.9   605.0
MG_MiniMi_SPW                      0.0    -3.5     3.6     4.1  1100.0    43.4    24.9    14.1    13.4    22.3   -13.6   555.0
```

## 6. Stage and checks
Stage C:\kl_build_1024\gunpunch_1108: `install.py` (`--check`, `--undo`, `--root` for a scratch copy; refuses unless every live bank md5 = gunraw_1107 output, refuses with kl2.exe threads,
free-space check), `UNDO.bat`, `INSTALL punchy gun sounds all maps.bat` + `UNDO punchy gun sounds all maps.bat` (PowerShell twin), preview wav pairs (`preview\stock_F02`, `preview\maps_DM02`:
`*_live.wav` = gunraw now, `*_punch1108.wav` = punchy). Undo order: THIS kit first, then gunraw_1107 (out of order refuses). Checks done: build 42 banks, `kl_gunpunch.py verify` 42 PASS
(apply+undo reproduce the md5s, worst residual 0.58 dB), scratch round trip on 3 banks (F02, DM02, L00) install + undo byte-exact, `install.py --check` on the live game folder OK (42 banks).
md5 (before the 11-08 peak fix, superseded by section 7): manifest 16f2ab34, report f6fcc3e6.
Needs one owner A/B (listen to the preview pairs first).

## 7. Peak fix 2026-11-08 (review: every staged clip decoded at 0.0 dBFS)
Cause: hard clip at full scale + ADPCM re-encode put samples on the rail (60/61 already did in gunraw_1107). Fix in `tools/kl_gunpunch.py` only (gunraw untouched):
hard clip ceiling `CEIL` 0.88 (-1.1 dBFS; head target still solved, so the cost is flat-top share, not head level) and `limited_encode_for`: encode, DECODE the bytes,
pull in only the samples over `LIMIT_INT` 31600 (-0.32 dBFS) and re-encode until none is (global scale = last resort, never reached). `peaks <outdir>` / `verify`
decode every staged record from the staged spans: 2161 records PASS, worst true peak -0.315 dBFS (limit -0.3). kl_gunpunch_test.py asserts it on synthetic clips
and a full-scale square wave.
Level cost (1796 gun records vs the MP45 head target; before = full-scale build): head error mean 0.00 -> -0.29 dB (min -1.07, max +0.01); flat-top share 20.9 % -> 0.2 %
(the MP45's own 20 % flat tops decode at 32767 and cannot exist under -0.3 dBFS; the hard-clip LOOK is gone, the crack/front/tail shaping is unchanged);
clips short of target at the 18 dB gain cap 30 -> 58 (of 2161). ceiling trials on DM02 (head err mean): 0.955 -1.20, 0.90 -0.48, 0.88 -0.27, 0.85 -0.24 (more shorts), 0.84 breaks ADPCM corr. All GUESS taste values.
Installer `install.py` (source `tools/kl_gunpunch_install.py`, copied by `kl_gunpunch.py kit <stage>`) is now ALL-OR-NOTHING: a write error or md5 mismatch part-way rolls back
every bank touched in that run from the kit's own span files (rc 5 rolled back, rc 8 incomplete + backups named). The PowerShell twin was dropped (no roll back): both INSTALL/UNDO bats call install.py.
Tests: kl_gunpunch_test.py 44 checks (fake 4-bank folder: read-only bank mid-loop, corrupt span file, clean install, no-op, byte-exact undo, foreign bank refused);
real kit on a scratch copy of 4 banks (DM02, F02, L00, F04): read-only last bank -> rolled back identical, install, undo byte-exact; `install.py --check` on the live folder: 42 banks would change.
Pins unchanged semantics (inputs = gunraw_1107 live output). NOTE: INSTALL writes over stock Dog Days sound banks IN PLACE (backups *.WAV.before-1108gunpunch), needs the owner OK, like gunraw_1107.
Rebuilt stage md5: manifest 3f8b0b84, report 6f866838, install.py 3f292a0e, UNDO.bat 9241e550. Preview pairs regenerated (preview\stock_F02, preview\maps_DM02).
