@echo off
rem Removes sound pass 3 (its ini sections and KLExpansion\Ambience\local and \panic). Does not touch dinput8.dll. Close the game first.
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "PK=%~dp0..\sound3_1023"
if not exist "%PK%\sound3_1023.ps1" (echo sound3 package not found: %PK% & pause & exit /b 2)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PK%\sound3_1023.ps1" -Dd "%DD%" -Undo
pause
