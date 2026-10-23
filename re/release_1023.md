# Release 1023 install package (branch feat/1023-release, from rtp-schemas ab08f42b1 (includes sound3-fix music/ambience))

Offline only. Nothing was launched, nothing written under the Dog Days folder. No hook C change was needed: the hook is
rtp-schemas' tip built as it is. New behaviour stays behind ini keys with old-behaviour defaults.

## What it does
`tools/release_1023/` holds the kit (copy staged to `<work>\build\release_1023\` on G:, plus `dinput8.dll`, `dinput8.dll.sha1`,
and `kl_ini_patch.py`):
- `release_1023.ps1 -Root <DD> [-BackupDir d] [-SkipRunCheck]` install; `-Undo [-Stamp s]` undo.
- `INSTALL release 1023.bat` (DD path fixed to the owner's), `KLHook.release1023.patch.ini`, `README_release_1023.txt`.
Install: refuse while kl2.exe runs; pre-check files, python and the ini patch (to a temp file) before writing anything; back up
`dinput8.dll` and `KLHook.ini` to `<work>\build\release_1023_backup\` as `<name>.<stamp>` (md5-checked) with `manifest_<stamp>.txt`;
copy the dll (md5, rollback on mismatch); apply the ini patch; write `UNDO release 1023.bat` (+ stamped copy, + a copy of the
script) in the backup folder. Idempotent: nothing to change = no new backup, no new undo. Undo: verifies the backups against
the manifest first, saves what is live as `<name>.undo-<time>`, restores byte for byte (md5-checked), removes a file that did not exist before.

## Ini keys (patch)
`[Balance]` PointBlankToYou=4.5 CopToYou=0.7 CrewToYou=0.6 PlayerHealth=1.0 CopToYouFar=0.6 CopToYouNearAt=12 CopToYouFarAt=40
(identical to `balance2_1023\KLHook.balance2.patch.ini`, checked line by line; basis re/balance2_1023.md).
`[QoL]` FlashOnReady=1 ReleaseCursor=1 BackgroundMs=0 (key names match klqol.c lines 117-122; the effects are not proven live; `Ramp` defaults to 1 in klbalance.c:1281).
No `Enable` line: the owner's ini already has Enable=1 (see "Review fixes" 1); `-BalanceOn` only for an ini where it is not.
Not written: `[QoL2]` anything, BackgroundMs > 0.

## Review fixes (feat/1023-release-fix)
1. PREMISE WRONG (lead, 10:10). The reviewer read KLHook.ini while kl-merge-27's BUY test ini was swapped in (Enable=0, CopToYou=0.001,
   PlayerHealth=10 are test values). The owner's real ini (sha1 a4de872a, restored after every run) has `[Balance] Enable=1`, Risk=2,
   CopToYou=0.9, PlayerHealth=0.9, PointBlankToYou=6.0, RegenDelay=RegenTime=6 = pass 1, so the plain install turns pass 2 on.
   Kept from the fix: the installer prints live Enable/Risk/Tough/CopToCrew/YouToCop/RegenDelay/RegenTime and a NOTE when Enable is not 1;
   `-BalanceOn` adds Enable=1 for that case. Do not run the installer while a test ini is swapped in (a test run in progress).
2. ACCEPTED. Wording changed: key names match klqol.c and are read live; FlashOnReady/ReleaseCursor effects (flash, load detection when not in front, ClipCursor(NULL) sticking) are NOT proven live.
3. ACCEPTED. Installer verifies the package dll against `dinput8.dll.sha1` (first token) before anything is written. Staged files are now byte copies of the committed kit (line endings identical).
4. ACCEPTED. Rollback removes the new dll when none existed before (tested on a fake DD without a dll: install, undo removes it).
5. ACCEPTED. No redundant backups: an unchanged file is `SAME` in the manifest, not backed up, and undo skips it (tested: dll-only/ini-only install, then undo leaves the other file alone).
6. ACCEPTED. Installer prints the sha1 of the live dll before replacing it. Build reproducibility: MSVC builds are NOT byte-reproducible (rebuilding the same commit gave
   7C6F86CE... for SHIP and B69F7AF9... for TEST vs the first build's D25393D9.../37CA3A56...). So the sha1 identifies the staged FILE, not a source state. Command:
   `klhook\build.bat <abs dir>` (SHIP) / `klhook\build_auto.bat <abs dir>` (TEST) at commit eb2deca84 (+ this fix, which changes no C).
7. ACCEPTED (by grep, no boot test): defaults in the C sources are old-behaviour. `[Music] Enable`, `[Ambience] Enable`, `[Voice] Enable`, `[NetSmooth] Enable` (CamYaw only with Enable=1) all default 0;
   `[QoL2]` Watchdog/WatchDry/MuteBackground default 0, HeisterKey 0; `[QoL]` FlashOnReady/ReleaseCursor 0, BackgroundMs 0; `[Balance] Enable` 0. The live ini already has `Enable=1` in several other sections,
   so check that a section of those new modules is not already enabled there. Not boot-tested (no live runs allowed).

## Builds (from this branch)
SHIP `klhook/out_release_1023/dinput8.dll` sha1 D25393D96D026840664A4B7547D63D051E646B82 (staged copy equals it)
TEST `klhook/out_release_1023_test/dinput8.dll` sha1 37CA3A56ECA67468F280FFEBA215388AB9684865 (not staged: tests use it from klhook/)
Rebuilt on feat/1023-release-fix (no C change): SHIP 7C6F86CEDF21A15B45388F65BC6EB9B2FBF44B7A, TEST B69F7AF9BDF3066E58ABE00248A08DACC8931A7B
(`klhook/out_release_1023*`, untracked). The STAGED ship dll stays the D25393D9 file (its .sha1 is what the installer checks).
(`build.bat <abs dir>` / `build_auto.bat <abs dir>`; out dirs are untracked and not committed.)

## Tested (offline, copies)
Fake DD in `%TEMP%\rel1023test` (dummy kl2.exe, copies of the real KLHook.ini and dinput8.dll): install -> 10 ini lines changed,
dll md5 ok; second install -> "already installed", no new backup; edit ini, undo -> both files restored to the manifest md5s, the edited ini kept as
`.undo-<time>`; generated UNDO bat runs (with `-SkipRunCheck` added only for the test because the real game was running).
The refusal while kl2.exe runs was seen for real (the lead's game was up).

## GUESS / not proven
- No engine offset is touched by the kit. The hook's own GUESS lists stand: re/balance2_1023.md section 4 (attacker at player+0x2778,
  team byte, the 12/40 m numbers), re/qol_1023.md (load = main-loop silence, state 0xd/0x28, ClipCursor once sticks).
- Pass-2 numbers are judgment (no owner play after pass 1 exists).
- The release dll contains all merged work (QoL2, CamYaw, voice, ...). Only what the installed hook already did is known live; QoL2 keys are off.

## Live test for the lead (TEST hook after install, or the SHIP hook by hand; owner away, monitor on)
Install first onto the real DD only when the game is closed and the owner agrees: `INSTALL release 1023.bat`.
Then a scripted Arcade round on a non-stock map (Retomoto f06 or DM03) with the ini unchanged except `[Balance] Log=2`:
1. Boot lines in KLHook.log: `balance: CopToYouFar=0.60: ...`, `qol: FlashOnReady=1 (LoadGapMs=3000) BackgroundMs=0 ReleaseCursor=1`.
2. Put another window in front during the load: `qol: main loop silent for N ms - a load ended (game in front: no)` then
   `qol: taskbar flash (level loaded), #1`; later `qol: game left the foreground - mouse clip released`.
3. Police at range: `balance: copfar: last bullet on you came from ... at X m: police->you x Y`, Y 1.00 inside 12 m, 0.60 from 40 m; no value outside 0.60..1.00.
4. Pass: `RESULT PASS` exit, 0 faults, no `qol2:` lines (all off), no `BackgroundMs` sleep line.
Undo test: run the generated UNDO bat; compare md5 of `<DD>\KLHook.ini` and `dinput8.dll` with `manifest_<stamp>.txt` (`*_backup_md5`).

## What the release dll switches on with the owner's ini (audit 10:55, saved copy sha1 a4de872a, audit + refute pass)
- Inert (no key in the owner ini, all old-behaviour defaults): [QoL], [QoL2], CopToYouFar (every new path gated on far_>0),
  [Music] ASSAULT, [Ambience] Local/Panic (no folder scan: the 145 placed clips stay unused until the sound3 ini), [NetSmooth] CamYaw,
  [HUD] HeadMaxDist/HeadFade. TEST-only, not in SHIP: klprobe.c, klauto.c, klsolo.c.
- Active and new/changed today: [Music] Enable=1 (8 s round-start grace, jukebox/stinger), [Ambience] Enable=1 (whole module new
  today, DOOR1 live), [Voice] Enable=1 (guessed speech-manager layout, partly live-tested: the highest risk), [Talk] v2, [Traits],
  [Lobby] MinPlayers=2, klslot HideUnused (default 1; PH3 PASS). Whether the installed hook already has each of them was not checked.
- kljoin lift ride keys come from a map's KLJoin.ini (Delay=0 default = no ride); the game-folder KLJoin.ini files were not read.

## Open risks
- The installed hook (md5 changes over the day) may be newer than rtp-schemas ab08f42b1 (includes sound3-fix music/ambience): if another branch has merged since, rebuild first.
- `kl_ini_patch.py` drops a trailing `; comment` on a replaced line (prints the old value). The owner's comments above the lines stay.
- Undo restores the whole ini: later owner edits survive only as the `.undo-<time>` copy.
- Do not run `INSTALL balance2 1023.bat` as well (same keys, its own undo would restore an older ini).

## Kit b (branch feat/1023-release2, from rtp-schemas 751c25d20; 2026-10-23 ~10:40)
Why: the first kit's dll (d25393d9, ab08f42b1) has no klstinger.c (string "stinger:" absent; present in the new one). Kit b is a NEW staged folder,
`<work>\build\release_1023b\` (the 1023 folder is untouched). Source `tools/release_1023b/`; no hook C change (rtp-schemas tip built as it is).
- Files: `release_1023b.ps1` (the 1023 installer with the names changed: backup `<work>\build\release_1023b_backup`, `UNDO release 1023b.bat`, copy of the
  script `release_1023b.ps1` there), `INSTALL release 1023b.bat`, `KLHook.release1023.patch.ini` (byte copy of the 1023 patch: balance pass 2 + [QoL]),
  `README_release_1023b.txt` (plain words: what changes, install order, undo order), `OPTIONAL 1 sound3.bat` / `OPTIONAL 1 UNDO sound3.bat`,
  `OPTIONAL 2 stinger.bat` / `OPTIONAL 2 UNDO stinger.bat`, plus staged `dinput8.dll`, `dinput8.dll.sha1`, `kl_ini_patch.py`.
- SHIP dll sha1 EE6CCCAAAFD72FCFFD611099855E957BB4CF0B58 (`klhook/out_release2_1023`, copied to `klhook/out_release_1023b`; staged copy equal).
  TEST dll AC68FA061D96C22489A67C5067DE471902AB9F58 (`klhook/out_release2_1023_test`, `build_auto.bat`; not staged). MSVC builds are not byte-reproducible.
- Add-on installers checked (read, then run on a fake DD): both refuse while kl2.exe runs; neither touches dinput8.dll unless the stinger one gets `-Dll`
  (its package dll is the older 89A9B475 hook: the OPTIONAL bats never pass it; the README says never add it). sound3: clips md5-checked, `KLHook.ini.before-sound3`
  saved once, [Ambience]/[Music] merged key by key, other sections replaced; undo section by section. stinger: marker block appended, timestamped ini copy
  "for manual recovery only", undo removes only the block and `KLExpansion\Stinger`. Their undo is by the add-on's own bat (no shared backup folder), so the
  two kits' undos cannot mix. The OPTIONAL bats call `..\sound3_1023\*.ps1` and `..\stinger_1023\*.ps1` (the already staged packages, not copied: G: is tight).
- Order: install release 1023b, then add-ons. Undo: add-ons, then release (the release undo restores the whole ini, so add-on ini lines vanish, clips stay).
- Tested offline on a fake DD in %TEMP% (dummy kl2.exe, the saved owner ini a4de872a, the 1023 dll as the "live" one, `-SkipRunCheck`): install (10 ini lines,
  dll md5 ok), repeat (already installed, no new backup), sound3 + stinger (dll md5 unchanged, balance keys kept, 1 [Stinger] block), stinger undo, sound3 undo
  (ini byte-identical to the post-release state, both clip folders gone), release undo (dll D25393D9 and ini A4DE872A back). The wrapper bats were NOT run (they point
  at the real DD).
- GUESS / risk: no engine offset touched by the kit. Stinger cue choice and the PD2 clip offsets are unjudged; the stinger and sound3 hook code ran live once (DM01).
  The release dll was not booted by the installer test (offline); a live run is the lead's (proposed run in re/release2_1023.md).
