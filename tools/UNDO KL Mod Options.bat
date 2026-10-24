@echo off
rem Removes the KL Mod Options tool again (restores any .before-1024modopts file). KLHook.ini is not touched.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0modopts_install.ps1" -Mode undo
pause
