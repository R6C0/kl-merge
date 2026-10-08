@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -3 kl_convert.py %* & goto done)
where python >nul 2>nul && (python kl_convert.py %* & goto done)
echo Python 3 is not installed. Get it from https://www.python.org/downloads/ (tick "Add to PATH"), then run this again.
pause
exit /b
:done
if exist "converted" start "" "converted"
