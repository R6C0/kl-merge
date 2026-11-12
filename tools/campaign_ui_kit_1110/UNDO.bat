@echo off
rem campaign_ui_1110 undo: the 17 campaign levels back to the campaign_1109 files, the menu copies removed, dll + ini back.
rem Run with the game CLOSED. Undo this BEFORE campaign_1109\UNDO.bat and before campaign_1110's dll is undone.
cd /d "%~dp0"
python install.py --undo --dry || (echo Refused, nothing written. & pause & exit /b 1)
python install.py --undo
pause
