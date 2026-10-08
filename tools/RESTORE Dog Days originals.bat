@echo off
cd /d "%~dp0"
echo Putting Dog Days' original files back from KL_PortBackup...
where py >nul 2>nul && (py -3 kl_package.py restore & goto done)
where python >nul 2>nul && (python kl_package.py restore & goto done)
echo Python 3 is not installed. You can also restore by hand: move everything from
echo the KL_PortBackup folder inside your Dog Days folder back into the Dog Days folder,
echo or use Steam: Properties - Installed Files - Verify integrity of game files.
:done
pause
