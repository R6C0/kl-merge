@echo off
rem Installs the 1023 event-stinger pass (clips + [Stinger] ini block). Add -Dll to also install the package hook (backup kept).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stinger_1023.ps1" -Dd "C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days" %*
pause
