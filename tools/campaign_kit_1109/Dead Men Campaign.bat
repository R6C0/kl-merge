@echo off
rem Dead Men campaign level picker (KL Merge; luvsic's campaign port, in contribution with luvsic).
rem Start Dog Days first and wait for the main menu, then run this and pick a level.
rem It writes KLCampaign_load.txt next to kl2.exe; KLHook ([Campaign] Trigger=1) loads that level within a second.
setlocal
cd /d "%~dp0"
:menu
echo.
echo  Dead Men campaign levels
echo  ------------------------
echo   1  M01  Impact
echo   2  M02  Trial
echo   3  M03  Withdrawal
echo   4  M03B Cracking Up
echo   5  M05  The Mizuki
echo   6  M06  Exchange
echo   7  M07  Reunion
echo   8  M08  Breakout
echo   9  M09  Retomoto Tower
echo  10  M09B Tokyo Streets
echo  11  M11  Freedom Fighters
echo  12  M11B El Capitol
echo  13  M12  Bird's Eye View
echo  14  M13  Within The Walls
echo  15  M13B Choice
echo  16  M14  Consequence
echo   Q  quit
echo.
set "pick="
set /p pick=Level number:
if /i "%pick%"=="q" goto :eof
set "id="
if "%pick%"=="1" set id=M01
if "%pick%"=="2" set id=M02
if "%pick%"=="3" set id=M03
if "%pick%"=="4" set id=M03B
if "%pick%"=="5" set id=M05
if "%pick%"=="6" set id=M06
if "%pick%"=="7" set id=M07
if "%pick%"=="8" set id=M08
if "%pick%"=="9" set id=M09
if "%pick%"=="10" set id=M09B
if "%pick%"=="11" set id=M11
if "%pick%"=="12" set id=M11B
if "%pick%"=="13" set id=M12
if "%pick%"=="14" set id=M13
if "%pick%"=="15" set id=M13B
if "%pick%"=="16" set id=M14
if not defined id (echo Not a level number. & goto menu)
if not exist "Scenes\Locations\%id%\%id%_Main.zip" (echo %id% is not installed. & goto menu)
>"KLCampaign_load.txt" echo %id% 1
echo Loading %id% ... switch back to the game. (Check KLHook.log for "campaign:" lines if nothing happens.)
goto menu
