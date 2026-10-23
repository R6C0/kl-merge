# Music hook (klhook/klmusic.c), 2026-10-23

A jukebox so every Fragile Alliance map has music, with the owner's own PAYDAY 2 soundtrack played IN PLACE (never copied, never in the
repo). Off unless `[Music] Enable=1`. Why not the engine route: the 9 stock FA maps have no ZPlayMusic node (settings field 157 = 0), and
an engine route needs a rebuilt sound bank per map plus PC_Def.str (scout 7, S3/S4). This part needs no game file at all.

## How it works
- winmm MCI (`mpegvideo`, MP3 native), loaded with LoadLibrary/GetProcAddress (no new import, build lines unchanged).
- ONE worker thread makes every MCI call. The game thread (`klmu_tick`, every 250 ms, from klhook.c's tick) only reads the round and posts a
  command {mood, playlist, lead stinger, volume, fade} under a lock + SetEvent. It never waits for the worker.
- Crossfade: two aliases (`kmua`, `kmub`), `setaudio <alias> volume to N` stepped every ~40 ms over `Fade` ms; the same fade is used when
  the next track of one mood starts `Fade` ms before the playing one ends, and for a mood change.
- Reading only: nothing in the game is patched or written.

## Cues (round state = klbot.c `klb_read`: Arcade / FA offline, rules ZGameRulesHeist, session 0x168e598)
| mood | when |
|---|---|
| NONE | no round (frontend, load, pre-round state), online (`kl_online()`), engine-music map, `[Music.<map>] Enable=0`, [Solo] bench |
| CALM | session state 0x19 (round runs) |
| ACTION | any heister's heist stage >= 1 (record +0x78), or the crew's money rose since the round began, or `ActionAfter` s (default 45) |
| ESCAPE | rules+0x1dc in 3..5 (escape vehicle waiting / arriving), or any stage >= 2, or YOU aboard (record status 4) |
| DOWN | YOU dead (record status 7) - only if a `Down` list or a Stinger-on-down exists, else the base mood goes on |
| END | the session state left 0x19 after a round: Stinger once (if `StingerOn` has `end`), then fade to silence; NONE after 20 s |
Moods only climb inside a round. A new round (state back to 0x19 or another rules object) starts at CALM.
An empty list uses the lower mood's (ESCAPE -> ACTION -> CALM, CALM -> ACTION).
GUESSES: `ActionAfter` time and the money rule stand in for "the shooting began"; there is NO police cue (the actor team field offset is
unknown, see klcensus.c); veh 3..5 as "escape coming" is read from klbot.c's notes, not heard.

## Maps
Key = the redirected map's folder (`klmv_pm_folder`, e.g. DM01B) or `F01`..`F09` on a stock slot. `[Music.<key>]` overrides any key.
`EngineMaps` (default DM09, DM06B, DM03A, DM05A = Retomoto, Park II, Vault, Last Call, which carry engine music) are silent unless that
map's section has `Force=1`. Hot Coffee II (DM01B) is wired too (scout 7 says no ear report); it is NOT in the default skip list.

## Keys
`[Music]` Enable, Volume (0..100, default 60), Fade (ms, 3000), Folder, FolderB, Calm, Action, Escape, Down, Stinger (semicolon lists of
file names or full paths, at most 32), StingerOn (any of action,escape,down,end; default down,end), ActionAfter, Random (1: a list
starts at a random track), EngineMaps, SoloPlay (0), Log (1). Missing files are dropped with a log line at map load.
Volume: the game's music slider is not read (field unknown); MCI volume 0..1000 = Volume x 10 (linear, GUESS), under the Windows mixer.
Nothing ducks for speech.

## [Solo] bench
With `[Solo] Enable=1` in the same ini the part stays silent unless `[Music] SoloPlay=1` (set it in one instance's ini only).

## Playlist (the owner's, C:\kl_build_1019\music_1023\KLHook.music.patch.ini)
Folders: `...\PAYDAY 2\PAYDAY 2 the Soundtrack` (47 MP3, numbered; the scout's "B-Sides" are a SEPARATE folder `...\PAYDAY 2\Payday 2 - B-Sides`, 28 MP3, FolderB).
- Calm (planning, waiting): 02 Master Plan, 03 Time Window, 05 The Mark, 07 Tick Tock, 08 Fuse Box, 21 And Now We Wait, 20 Shadows and Trickery, 36 Searchlights, 25 Blueprints
- Action: 09 Razormind, 19 Death Wish, 35 Breach 2015, 42 Gun Metal Grey 2015, 43 Crime Wave 2015, 40 Dead Man's Hand, 41 Utter Chaos, 37 Kicking Ass and Taking Names, 16 Armed to the Teeth, 10 Calling All Units, 06 Full Force Forward, 45 Locke and Load
- Escape: 11 Where's the Van, 13 Clean Getaway, 24 And Now We Run, 30 Hot Pursuit, 46 Drop Zone, 47 Pimped out Getaway
- Down: 12 Hard Time, 17 Sirens in the Distance, 18 Wanted Dead or Alive
- Stinger (leads ACTION): B-Sides 04 Double LMGs (26 s). None of the 47 main tracks is shorter than 141 s, so no END stinger by default.
`tools/klmusic_check.py <ini>` proves every named file exists (exit 0).

## Verified (offline)
- `klhook/build.bat out_1023a_music` and `build_auto.bat out_1023a_music_test`: built, 0 compiler warnings (/W3).
- `klhook/klmusic_test.c` (worker only, MCI at VOLUME 0): CALM two 6 s files with 1 s fade: a, b 4.9 s later, a again; ACTION with a
  4 s stinger lead: stinger, then b; END: stinger once; NONE: both aliases closed, 0 MCI errors.
- Not tried in the game: the cues (`klmu_tick`), the map key, the log lines in a real round, audibility, the window unfocused.

## Live test (for the lead, game closed first, then install)
1. `C:\kl_build_1019\music_1023\INSTALL music 1023.bat` (SHIP dll 5244aff9..., ini playlist appended; `UNDO music 1023.bat` reverses).
   TEST-build run instead: copy `dinput8_TEST.dll` (same source) and the `[Music]` block into the test ini.
2. Scripted run on a stock map (DM-free): `python tools/kl_autotest.py` with the F02 slot / an Arcade FA round ini of the lead's choice.
   PASS = `KLHook.log` has `music: on (...)`, `music: map F02: Calm 9 / Action 12 ...`, `music: cue CALM on F02`, a `music: CALM <file> (N s, fade 3000 ms)`
   line within ~1 s of the round start, then `cue ACTION` (loot, stage, or 45 s) with `stinger 04 Double LMGs` + `ACTION <file>`; at the round end
   `cue END` then `cue NONE`. No `MCI ... failed` lines, clean exit, 0 faults. Loopback RMS (S0 `kl_listen.py`, not built) would show the track.
3. Silence checks: DM09 log has `music: DM09 has its own engine music - the jukebox is silent here`; an online/lobby session logs no cue;
   a `[Solo] Enable=1` ini logs `music: [Solo] bench on ...`.
4. A short ini for a fast check: `[Music] Enable=1 ActionAfter=10 Fade=1000 Volume=20` + the lists above.

## Open questions
- Does MCI play while the game window is unfocused / fullscreen-exclusive? (GUESS yes; a fullscreen D3D9 game normally keeps winmm audio.)
- The game's music volume slider, a duck for speech, and a police cue are not done.
- Playing the owner's PAYDAY 2 files is a local convenience; the hook never copies them, but a build that is shared must not ship the ini's Folder paths as a default.
