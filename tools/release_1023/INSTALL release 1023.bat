@echo off
rem Installs the 1023 owner release: the SHIP hook (dinput8.dll) and the KLHook.ini patch (balance pass 2 + safe QoL keys).
rem Close the game first. Backups and "UNDO release 1023.bat" go to ..\release_1023_backup (next to this folder). See README_release_1023.txt.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release_1023.ps1" -Root "%DD%"
pause
