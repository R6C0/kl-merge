@echo off
rem Removes sound pass 3 (puts the replaced KLHook.ini sections back, deletes ambience local\ and panic\). Close the game first.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sound3_1023.ps1" -Dd "%DD%" -Undo
pause
