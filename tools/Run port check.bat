@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -3 kl_port_check.py %* & goto open)
where python >nul 2>nul && (python kl_port_check.py %* & goto open)
echo Python 3 is not installed. Get it from https://www.python.org/downloads/ (tick "Add to PATH"), then run this again.
pause
exit /b
:open
if exist "report\report.html" start "" "report\report.html"
