@echo off
rem Installs the 1023b owner release: the SHIP hook (dinput8.dll, includes klstinger.c) and the KLHook.ini patch (balance pass 2 + safe QoL keys).
rem Close the game first. Backups and "UNDO release 1023b.bat" go to ..\release_1023b_backup (next to this folder). See README_release_1023b.txt.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release_1023b.ps1" -Root "%DD%"
pause
