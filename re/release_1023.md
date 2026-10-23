# Release 1023 install package (branch feat/1023-release, from rtp-schemas e9490bbdd)

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
`[QoL]` FlashOnReady=1 ReleaseCursor=1 BackgroundMs=0 (key names checked against klqol.c lines 117-122; `Ramp` defaults to 1 in klbalance.c:1281).
Not written: `[QoL2]` anything, BackgroundMs > 0.

## Builds (from this branch)
SHIP `klhook/out_release_1023/dinput8.dll` sha1 531D61485B5D22B0ABFACA466B6B39A082097E0C (staged copy equals it)
TEST `klhook/out_release_1023_test/dinput8.dll` sha1 EBAEECA59F48994DCE4891142CA9961C2095323D (not staged: tests use it from klhook/)
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

## Open risks
- The installed hook (md5 changes over the day) may be newer than rtp-schemas e9490bbdd: if another branch has merged since, rebuild first.
- `kl_ini_patch.py` drops a trailing `; comment` on a replaced line (prints the old value). The owner's comments above the lines stay.
- Undo restores the whole ini: later owner edits survive only as the `.undo-<time>` copy.
- Do not run `INSTALL balance2 1023.bat` as well (same keys, its own undo would restore an older ini).
