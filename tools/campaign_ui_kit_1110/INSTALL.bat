@echo off
rem campaign_ui_1110: luvsic's Dead Men UI (HUD art + typefaces in the 17 campaign levels, Dead Men Campaign row in the Play menu).
rem Run with the game CLOSED. Dry check first, then the install. Undo: UNDO.bat in this folder.
cd /d "%~dp0"
python install.py --dry || (echo Refused, nothing written. & pause & exit /b 1)
python install.py
pause
