@echo off
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% kl_package.py build M01_FA_A F01 || goto fail
%PY% kl_package.py install F01 || goto fail
echo.
echo Installed. Originals are in the KL_PortBackup folder inside Dog Days.
pause
exit /b
:fail
echo Something went wrong - nothing further was changed.
pause
