# Gun sounds 1107: RAW + ECHO (staged offline, nothing installed, nothing launched)

Owner 11-07: "make gun shots more echoy or just adaptive to the environment ... all the guns ... sound like vanilla i want them to sound raw".
Research: `re/gun_raw_1107.md` (raw), `re/gun_echo_1107.md` (echo). This file = what was built.

## 1. RAW (data, "(recommended on)")
`python tools/kl_gunsnd_all.py build --body ...` (extension of the existing tool: `--body`, PROFILE table, gun_class, body(), timbre()).
Every gun record is rebuilt from the pre-raw backup source (no ADPCM generation loss), hard-clip "raw" drive (MP45 / Desert Eagle level and 19.8% flat-top as the target), in place at the same offsets, WHD untouched.
- Stage: `C:\kl_build_1024\gunraw_1107` (72 MB). 42 banks (21 maps = 9 stock DD + 11 DM + extra, 9 stock group, 12 story/online), 2161 records changed of 2161, 29.9 MB of spans.
- `python tools/kl_gunsnd_all.py verify C:/kl_build_1024/gunraw_1107`: 42 banks PASS (apply+undo reproduce the md5s, worst residual 0.64 dB excluding clips at the gain cap).
- md5: manifest.json dc39aa90f81eb1b413c7e1ccc1c2b147, report.json 90ea8d70bb9ee953f01022760e7f44cc, install_gunsnd2.ps1 4ef7562564c6c1f24bc91a3d5b5e4c81,
  INSTALL raw gun sounds all maps.bat cd849189a0716af8a0b586139b30d3c3, UNDO raw gun sounds all maps.bat 938d49cec5ad42d013a53286155c98d9.
- Install: run `INSTALL raw gun sounds all maps.bat` (owner, game closed). md5-chained, all-or-nothing, backups `*.before-1107gunraw`, refuses if any bank md5 differs from the pinned one. Undo: `UNDO raw gun sounds all maps.bat`.
- `tools/kl_gunsnd_all.pins.json` pins the live bank md5s as accepted inputs (re-pin if any bank changes before install).
- A/B previews: `preview\stock_F02`, `preview\maps_DM02`, list `AB_LIST.txt`.

## 2. ECHO / ENVIRONMENT (hook, ini key, default OFF)
`klhook/klecho.c` + `klecho_logic.h` + `klecho_test.c` (96 checks, in tools/kl_tests.py). Dog Days has ONE global OpenAL EFX reverb slot; ZSynthOpenAL::SetReverb (0x5fff30) calls alEffectf through the .data pointer at 0x14f356c, 12 calls per room. The hook swaps that DATA pointer for a wrapper (no code byte written; fine for a SHIP build). Per room kind (read from the decay and reflections the engine asked for): indoor, street, roof, hall change decay, reflections gain/delay, late tail gain/delay. Indoor, street and roof give different answers (tested). Applies on stock maps and online (same exe).
```
[Echo]
; Room reverb follows the place (recommended on once the owner has listened)
Enable=0
Strength=100
IndoorPct=100  StreetPct=100  RoofPct=100  HallPct=100
Log=1
```
- Builds (from HEAD, [Perf] fixes kept): TEST `klhook/out_echo1107_test/dinput8.dll` md5 532e41b0ac3de2f1dd019393a4661e31; SHIP `klhook/out_echo1107/dinput8.dll` md5 b6a293181e804e46b620d84851630e7e. Not installed.
- Toggle: ini key only; Enable=0 = byte-for-byte engine values (self-test checks strength 0 and each kind at 0%).

## 3. GUESS / needs a live test (owner present)
- Whether gun voices carry the aux send (static reading says default send gain; never listened). One A/B run with `[Echo] Enable=1, Log=1`; the log gives one line per distinct room ("echo: roof decay ...").
- Room kind thresholds (decay 0.6 / 2.5 s, reflections 0.08) come from the 3 stock F02 effects only.
- Dead Men maps only echo differently once they carry reverb boxes (gun_echo_1107.md).
- RAW: `body_src_live` = 854 of 2161 records had no pre-raw backup, so they are rebuilt from the live clip (some generation loss / already-driven source possible; the verify residual is fine but the sound is unheard).
- RAW level vs. the other mods (shop PD2 guns, DM guns) is by the measurement target, not by ear.
- Baked echo tails inside the banks were NOT done (record sizes fixed); adaptation is the hook only.

## 4. Tests
`python tools/kl_tests.py`: 97 pass, 0 fail, 5 skip (klvanshield_test.c listed as UNLISTED, pre-existing, not mine).
