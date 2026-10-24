@echo off
rem Undoes k29d: dinput8.dll back to k29b, the [FrameLimit] block out of KLHook.ini (other lines untouched).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0k29d_install.ps1" -Undo %*
exit /b %errorlevel%
