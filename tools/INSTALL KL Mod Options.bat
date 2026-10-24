@echo off
rem Installs the KL Mod Options tool into <Dog Days>\KLModOptions\ (new folder, md5-checked, refuses while kl2.exe runs).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0modopts_install.ps1" -Mode install
pause
