@echo off
rem Removes the event stingers (its ini block and KLExpansion\Stinger). No -Dll: dinput8.dll is not touched. Close the game first.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "PK=%~dp0..\stinger_1023"
if not exist "%PK%\stinger_1023.ps1" (echo stinger package not found: %PK% & pause & exit /b 2)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PK%\stinger_1023.ps1" -Dd "%DD%" -Undo
pause
