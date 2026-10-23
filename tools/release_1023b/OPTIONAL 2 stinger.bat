@echo off
rem OPTIONAL add-on 2 (run AFTER "INSTALL release 1023b"): event stingers = short cues when the heist goes loud, loot, down, dead, betrayal, last 30 s, escape open, reached.
rem Runs the staged stinger installer WITHOUT its -Dll switch: the dll in that folder is OLDER than the release hook and must never be copied. Close the game first.
rem Undo: "OPTIONAL 2 UNDO stinger.bat".
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "PK=%~dp0..\stinger_1023"
if not exist "%PK%\stinger_1023.ps1" (echo stinger package not found: %PK% & pause & exit /b 2)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PK%\stinger_1023.ps1" -Dd "%DD%"
pause
