@echo off
rem Removes the 1023 event-stinger pass (only its ini block and KLExpansion\Stinger). Add -Dll to also put the old hook back.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stinger_1023.ps1" -Dd "C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days" -Undo %*
pause
