@echo off
rem Installs hook k29d (frame limiter + k29b). Refuses while kl2.exe runs or unless the live dll is k29b. NOT RUN by the agent.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0k29d_install.ps1" %*
exit /b %errorlevel%
