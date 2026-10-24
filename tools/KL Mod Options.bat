@echo off
rem KL Mod Options: one checkbox per feature of the Kane & Lynch 2 mod, each marked (recommended on) / (recommended off).
rem Edits KLHook.ini of the Dog Days folder. Refuses to save while kl2.exe is running. Changes apply at the next game start.
rem Placed in <Dog Days>\KLModOptions\ it edits the KLHook.ini one folder up; run from tools\ it uses the default Dog Days path.
setlocal
cd /d "%~dp0"
set "GAMEARG="
if exist "%~dp0..\kl2.exe" set GAMEARG=--game "%~dp0.."
where py >nul 2>nul && (py -3 "%~dp0kl_mod_options.py" %GAMEARG% %* & goto done)
where python >nul 2>nul && (python "%~dp0kl_mod_options.py" %GAMEARG% %* & goto done)
echo Python 3 (with Tk) is not installed. Edit KLHook.ini by hand: re\mod_options.md in the repo lists every switch.
pause
:done
