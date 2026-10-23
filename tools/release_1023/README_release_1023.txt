RELEASE 1023 - one install for today's hook work (Kane & Lynch 2: Dog Days + the expansion)
=========================================================================================

WHAT CHANGES IN THE GAME
1. New hook (dinput8.dll, SHIP build of branch feat/1023-release = everything merged on rtp-schemas on 2026-10-23).
   New features in it are off unless the ini turns them on, so with an old ini it plays like before.
2. Balance pass 2 (KLHook.ini [Balance]; you said the AI felt a bit too strong):
   - a guard at arm's length hits you for 4.5 bullets (was 6.0)
   - police bullets on you x0.7 (was 0.9); AI heister bullets on you x0.6 (new line)
   - your health is the game's own 550 (was 495)
   - NEW: police bullets from far away hurt less: full strength inside 12 m, x0.6 from 40 m on, in between smoothly
   Only the early Arcade levels feel it; from level 5 the game's own numbers stand.
   IMPORTANT: the whole [Balance] module does nothing while [Balance] Enable=0 (it is 0 in the current KLHook.ini, with old
   test values such as Risk=2, CopToCrew=0.01, YouToCop=2.0, RegenDelay/RegenTime=0.5 that this release does NOT change).
   The installer prints the live Enable/Risk/Tough/... values. To also switch the module on, run the installer with
   -BalanceOn (adds Enable=1); decide Risk/Tough/CopToCrew/Regen* yourself first, they stay as they are.
3. Two quality-of-life keys ([QoL]) - the keys are read live, the flash and the cursor release themselves are NOT proven in the game yet:
   - FlashOnReady=1: the game's taskbar button flashes when a level finished loading, when the Fragile Alliance lobby
     countdown starts, and when the round is over, while you are in another window.
   - ReleaseCursor=1: the mouse is freed when you alt-tab out of the game.
   Left OFF on purpose (not tested in the game yet): BackgroundMs (frame cap in the background) and everything in [QoL2]
   (stuck-bot watchdog, Heister page key, mute when in the background).

HOW TO INSTALL
 - Close the game (the script refuses while kl2.exe runs).
 - Double-click "INSTALL release 1023.bat" in this folder. Python must be on the PATH (kl_ini_patch.py needs it).
   (with balance on: powershell -ExecutionPolicy Bypass -File release_1023.ps1 -Root "<DD folder>" -BalanceOn)
 - The script checks the package dll against dinput8.dll.sha1 and prints the sha1 of the dll it replaces.
 - It copies your current dinput8.dll and KLHook.ini to ..\release_1023_backup with a time stamp, puts the new dll in,
   edits only the lines named above in KLHook.ini (comments, order and every other setting stay), and writes the undo.
 - Running it twice is harmless. Nothing else in the Dog Days folder is touched (not KL_PortBackup, no map zips).

HOW TO UNDO
 - Close the game, then double-click  ..\release_1023_backup\UNDO release 1023.bat
   (path: <work>\build\release_1023_backup\). It puts dinput8.dll and KLHook.ini back byte for byte (md5 checked).
   If you changed KLHook.ini after the install, your edited copy is first saved there as KLHook.ini.undo-<time>.
 - Only the dll or only the ini: copy dinput8.dll.<stamp> / KLHook.ini.<stamp> from that folder by hand.

EARLIER UNDO BATS (all independent of this release; <work> = G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools)
 - <work>\build\shopcut4_1023_undo\UNDO shopcut4 1023.bat   (newest shop cut; it copies from shopcut3_1023: keep that folder)
 - <work>\build\shopcut3_1023_backup\UNDO shopcut 1023.bat
 - <work>\build\shopbar_1023_backup\UNDO shopbar 1023.bat
 - <work>\build\ambience2_1023_backup\UNDO ambience2 1023.bat
 - G:\kl_build_1023\ambience_1023\UNDO ambience 1023.bat
 - <work>\build\acc75_1023_backup\UNDO acc75 1023.bat
 - <work>\build\locfit_1023_backup\UNDO locfit 1023.bat
 - <work>\build\balance2_1023\UNDO balance2 1023.bat  (only if INSTALL balance2 1023 was ever run; this release replaces it,
   do not run both: they write the same keys)
 - G:\kl_build_1023\voice_1023\UNDO voice 1023.bat
 - older: UNDO balance 1018.bat, UNDO everything 1018.bat, UNDO everything applied 1018.bat, UNDO all tests.bat, UNDO noblow.bat
   (C:\kl_build_1018 / the adopt_1018 folder; see re/open_work_log.md)
