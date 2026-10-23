@echo off
rem OPTIONAL add-on 1 (run AFTER "INSTALL release 1023b"): sound pass 3 = local + panic one-shots and Payday 2 assault music. Close the game first.
rem Runs the staged sound3 installer. That installer never copies a dll, so dinput8.dll is not touched. Undo: "OPTIONAL 1 UNDO sound3.bat".
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "PK=%~dp0..\sound3_1023"
if not exist "%PK%\sound3_1023.ps1" (echo sound3 package not found: %PK% & pause & exit /b 2)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PK%\sound3_1023.ps1" -Dd "%DD%"
pause
