@echo off
rem Undoes k29c: dinput8.dll back to k29b, the [FrameLimit] block out of KLHook.ini (other lines untouched).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0k29c_install.ps1" -Undo %*
exit /b %errorlevel%
