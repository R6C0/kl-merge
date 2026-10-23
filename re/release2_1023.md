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
