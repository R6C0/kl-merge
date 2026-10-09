@echo off
rem Takes KLGfx out of Dog Days: d3d9.dll is moved to KLGfx_removed\ (KLGfx.ini and KLNR\ do nothing without it).
setlocal
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
tasklist /fi "imagename eq kl2.exe" | find /i "kl2.exe" >nul && ( echo kl2.exe is running: close the game first & exit /b 1 )
if not exist "%DD%\d3d9.dll" ( echo no d3d9.dll in %DD%: nothing to remove & exit /b 0 )
if not exist "%DD%\KLGfx_removed" mkdir "%DD%\KLGfx_removed"
move /y "%DD%\d3d9.dll" "%DD%\KLGfx_removed\d3d9.dll" >nul && echo KLGfx removed (d3d9.dll moved to KLGfx_removed\).
endlocal
