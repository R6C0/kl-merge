# Ambience pass (2026-10-23, branch feat/1023-ambience)

Owner: "maps feel more lively: music, more ambience all around, more unique sounds". OFFLINE work: nothing here has run in the game.

## What it is
- `klhook/klambience.c`, `[Ambience] Enable=1` (default off). Pattern of klmusic.c: one worker thread owns winmm MCI (`mpegvideo`, aliases
  `kamb` = bed, `kam0..3` = one-shots; the jukebox uses `kmua/kmub`, so both run together). The game thread only reads the round
  (`klb_read`) and posts. No map zip, .LOC or .SND is touched, so it cannot conflict with the voice pass.
- Silent: no round, online (`kl_online()`), `[Solo]` bench unless `[Ambience] SoloPlay=1`, `[Ambience.<key>] Enable=0`.
- Map key as klmusic.c: redirected folder (DD01..09, DM01..) or F01..F09 on a stock slot.

## Triggers (round phase read like klmusic.c; GUESS: no police signal exists, "police phase" = time after the heist went loud)
| group | what | default timing |
|---|---|---|
| bed | looping street / alley / harbour / park layer | starts at the round (fade 2.5 s), ends with it; skipped on BedSkip maps |
| Radio | police radio chatter (14 PoliceRadio lines + 7 RadioCom, radio-filtered) | action phase, 60 s after round start, every 40-90 s |
| Alarm | alarm bell / buzzer / car alarm | once, 1.5 s after the action phase (Min=Max=0 means once) |
| Heli | Chopper_Flying / Bell rotor / supersonic fly-over | action, after 90 s, every 150-300 s |
| Distant | distant gunfire (4 gun classes) + debris explosions | action, after 10 s, every 30-80 s |
| Siren | 13 police sirens | action, after 30 s, every 60-150 s |
| Spot | city life per map: dogs+horns (city), gulls+ship horn (sea), birds+dogs (park), planes (air) | from calm, after 15 s, every 45-120 s |
Keys per group G: `G=list`, `GMin`, `GMax` (s), `GFrom=calm|action|escape|dead`, `GAfter` (s), `GVol` (0..100). Phase "action" = a
heister's stage >= 1, money rose, or `ActionAfter` s (installer writes 20). Maps in BedSkip (DM09 and variants, DM06B, DM03A, DM05A, T01)
have engine ambience or music: no bed; DM09* also no Spot (a tower). Stock maps F01/F02/F03/F06/F07 already carry MultiPlayer ambience
(streams under SFX/Ambiences/MultiPlayer), so they get a quiet distance layer (BedVol 25); F04/F05/F08/F09 a fuller one (GUESS, unheard).

## Files
- `tools/kl_ambience.py build|ini|music|check`: extract (PC_Def.str streams via kl_audio, in-memory IMA clips via kl_gunsnd from the DD
  banks) -> ffmpeg mp3 -> `<out>/<group>/*.mp3`; writes `KLHook.ambience.patch.ini` and `KLHook.music2.patch.ini`. The per-map bed choice
  (`MAPS`) and music pools (`MUSIC`) are GUESSES from the map names.
- Staging: `G:\kl_build_1023mbience_1023\` (98 mp3, 22 MB, patch inis, `dll\dinput8.dll` = SHIP out_1023a, `INSTALL ambience 1023.bat`,
  `UNDO ambience 1023.bat`, `ambience_1023.ps1`). Install refuses while kl2.exe runs, copies the library to `<DD>\KLExpansion\Ambience` with md5 per file,
  appends the ini blocks between `; ambience-1023 block (...)` and `; ambience-1023 block end` (idempotent), widens the global `[Music]` Calm/Action,
  never re-adds `[Music.DM01B]`/`[Music.DM11B]`, and writes one timestamped `KLHook.ini.before-1023amb-<time>` per run (manual recovery only).
- The hook dll is NOT copied by default (the merged-tree hook is installed separately). `-Dll` copies the package dll: refused unless the live dll's md5
  equals `dinput8.dll.before-1023amb` or the package dll; `-Undo -Dll` restores it only while the live dll is still the package's.
- UNDO is surgical: removes only the marker block(s), strips only the exact Calm/Action suffixes, deletes the library folder; it never restores an ini
  snapshot, so later edits to KLHook.ini survive. Tested on copies (`-SkipRunCheck`): install, re-run (no change), undo with a user section added after the block.
- Worker: every silencing path (round end, online, map change, map off) posts a stop-shots command: all one-shot slots are closed and the queue emptied.
  A one-shot slot is force-closed only after 300 s (safety).
- ORDER with the voice pass: independent (no shared file unless -Dll is used). If the voice pass ships a DLL, merge feat/1023-voice + feat/1023-ambience,
  rebuild and install that one.

## Live test recipe
KLHook.ini after install has `[Ambience] Enable=1 Log=1`. Start a FA round on e.g. Subway and read `KLHook.log`:
`ambience: on (...)`, `ambience: map F01: bed bed_highway.mp3, radio 21 / alarm 3 ...`, `ambience: bed bed_highway.mp3 (fade 2500 ms)`,
`ambience: phase 1 on F01`, then `ambience: Alarm alarm_2.mp3 (map F01, round second 22)`, later `Radio`, `Distant`, `Siren`, `Heli`, `Spot` lines.
Quick check: `[Ambience] ActionAfter=5 RadioAfter=5 RadioMin=5 RadioMax=8` for chatter within 15 s. Volume: `[Ambience] Volume` (0..100) and `BedVol`.
Offline worker test: `klhook\klambience_test.c` (bed at volume 0, shots, bed off; exit 0).

## Not done / untested
Everything in the game (audibility, loudness balance, whether MCI `play` of 4 one-shots plus 2 jukebox tracks coexists, loop gap of the bed, whether
stock maps double their own ambience). Civilians: tools/kl_fa_civs.py has never run in the game and rewrites the map zips (voice agent's files): skipped.
