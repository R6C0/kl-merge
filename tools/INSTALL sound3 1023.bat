@echo off
rem Installs sound pass 3 (Local + Panic clips, Payday 2 music by phase). Close the game first.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sound3_1023.ps1" -Dd "%DD%"
pause
