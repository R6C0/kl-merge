# release2 1023 - refreshed owner install kit (branch feat/1023-release2, from rtp-schemas 751c25d20)

Offline only; nothing launched, nothing written under the Dog Days folder. Details of the kit: `re/release_1023.md` section "Kit b".

## What it does
Stages `<work>\build\release_1023b\` (source `tools/release_1023b/`): SHIP hook with klstinger.c + the 1023 ini patch (balance pass 2, [QoL] FlashOnReady/ReleaseCursor)
+ optional wrappers for sound pass 3 and the event stingers. No hook C change. New ini keys: none (the kit uses existing keys; [Stinger] and sound3 sections
come from the add-on packages, `[Stinger] Enable` default 0 in the hook; the add-on block sets it to 1).

## Hooks
SHIP `klhook/out_release2_1023/dinput8.dll` (copy in `klhook/out_release_1023b`, staged) sha1 EE6CCCAAAFD72FCFFD611099855E957BB4CF0B58
TEST `klhook/out_release2_1023_test/dinput8.dll` sha1 AC68FA061D96C22489A67C5067DE471902AB9F58

## Install / undo
Close the game. `INSTALL release 1023b.bat`; then optionally `OPTIONAL 1 sound3.bat`, `OPTIONAL 2 stinger.bat`. Undo: `OPTIONAL 2 UNDO stinger.bat`,
`OPTIONAL 1 UNDO sound3.bat`, then `<work>\build\release_1023b_backup\UNDO release 1023b.bat`. Never pass `-Dll` to the stinger installer (its dll is the older 89A9B475;
the sound3 package dll 9F968EB1 is never copied by its installer).

## GUESS
None new (no offsets). Inherited: re/balance2_1023.md section 4, re/qol_1023.md, re/stinger_1023.md (event signals, clip choice).

## Proposed live test (lead; game closed first, owner agrees, kit installed on the real DD)
1. Install the kit and both add-ons. Scripted Arcade round on DM01 (the map of the 10:35 PASS) with `[Stinger] Log=1`, `[Balance] Log=2`.
2. KLHook.log must show: `balance: CopToYouFar=0.60: ...`, `qol: FlashOnReady=1 ... ReleaseCursor=1`, `stinger: on ...`, `stinger: map DM01...: Loud n / Loot n ... clips`,
   then in play `stinger: Loud ...` / `stinger: Loot ...` lines, and the sound3 Local/Panic one-shot lines as in the 10:35 run. Police at range: `balance: copfar: ... police->you x Y`.
3. Pass: `RESULT PASS`, 0 faults, no `qol2:` lines. Check the live dll sha1 is EE6CCCAA (installer prints it before/after).
4. Undo check: run the three undos, compare md5 of dinput8.dll and KLHook.ini with `manifest_<stamp>.txt` and with the pre-install copies.

## Open risks
- The release dll was never booted in the game after this build (only the installer was exercised on a fake folder).
- Release undo restores the whole ini (documented; add-ons first).
- G: has ~1.8 GB free; the add-on packages are referenced by relative path (`..\sound3_1023`, `..\stinger_1023`), so those folders must stay beside the kit.

## Review fixes (branch feat/1023-release2-fix)
No hook C change, so no rebuild: SHIP EE6CCCAA... and TEST AC68FA06... above stand. Build record: tree rtp-schemas 751c25d20, `klhook\build.bat` into
`klhook\out_release2_1023` (SHIP) and the TEST variant (`build_auto.bat`) into `klhook\out_release2_1023_test`; both dirs are untracked output. Identify the dll by
the staged `dinput8.dll.sha1` (EE6CCCAA...), it contains the string "stinger:" (old d25393d9 does not).
- README: add-on live claim narrowed (earlier dll builds; this exact dll untested until the live run); `[Stinger] Log` note.
- `stinger_1023.ps1`: refuses with exit 2 if KLHook.ini is missing (before any clip is copied); new switch `-Log` (default: block written with `Log=0`; was `Log=1`).
  For the live test run it with `-Log` (or set `Log=1` by hand). The OPTIONAL bat is unchanged, so it installs with Log=0.
- `sound3_1023.ps1`: wording no longer sends the owner to `out_sound3_1023` (the 1023b dll has the sound3 code); a stale `KLHook.ini.before-sound3` from an earlier run
  (clip folders absent, ini differs) is kept as `.stale-<time>` and refreshed. Documented: DM09* ambience/music sections are replaced whole.
- The staged copies in `<work>\build\sound3_1023\` and `<work>\build\stinger_1023\` were NOT updated (write refused here): copy `tools/sound3_1023.ps1` and
  `tools/stinger_1023/stinger_1023.ps1` over them before installing. Kit README in `build\release_1023b\` likewise needs `tools/release_1023b/README_release_1023b.txt`.
- Not run (no fake-DD retest of the edited scripts; syntax by inspection only).

## Rebuilt on rtp-schemas (lead, 11:00)
Cherry-picked onto rtp-schemas as c9cd2a83b / 2b4726be5. The staged SHIP dll is now `klhook\out_cc6_release_1023b\dinput8.dll` sha1 C7557D81DBD01BDFA8AD24853D76FD294AA0FB8A
(built at 2b4726be5 with `klhookuild.bat <abs dir>`: stinger + mciwrap clock fix + CEG guard); EE6CCCAA is superseded. TEST twin
`klhook\out_cc6_release_1023b_test` BC667026 played DM01 (KITB): PASS, 0 faults. Staged sound3/stinger installers refreshed to the fixed versions.

## Chain rehearsal (11:30) and undo guard
Offline rehearsal on fake DD folders (workflow, real clips, logs in scratchpad chain_wf): kit -> sound3 -> stinger and the reverse undo end byte-identical; kit twice is a no-op; add-ons before the kit are inert until the dll is in. Hazard CONFIRMED: the kit undo restores the whole ini, so undoing it before the add-ons drops their ini lines and orphans their clips. Fix: release_1023b.ps1 -Undo refuses (exit 4, nothing changed) while KLExpansion\Stinger exists or (Ambience\local AND KLHook.ini.before-sound3) exist; -Force overrides. Tested on a fake DD (stinger in: refused; local only: allowed; sound3 in: refused; -Force: ini restored). Staged copy and the backup folder copy (used by its UNDO bat) updated. README lists the stray before-* files left by a full undo.
