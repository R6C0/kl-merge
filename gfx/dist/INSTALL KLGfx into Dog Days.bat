@echo off
rem Puts KLGfx (d3d9.dll + KLGfx.ini) and KLNR\ (the helper) into the Dog Days folder. Dog Days ships no d3d9.dll,
rem so no game file is replaced. "REMOVE KLGfx from Dog Days.bat" takes it out again.
rem   INSTALL KLGfx into Dog Days.bat [nrtest | nrzero | capture | off]     (default nrtest)
rem     nrtest  every frame goes through klnr.exe; the right half of the screen comes back grey (visible proof)
rem     nrzero  every frame goes through the full network with synthetic zero weights: no visible change, real cost
rem     capture no bridge; frame captures at 60 s and 90 s after the device is made (KLGfx\frame_*), to find the HUD
rem     off     the proxy is loaded but passes everything straight to Windows' Direct3D 9
setlocal
set "DD=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "PRESET=%~1"
if "%PRESET%"=="" set "PRESET=nrtest"
if not exist "%~dp0KLGfx.%PRESET%.ini" ( echo unknown preset %PRESET% & exit /b 1 )
if not exist "%DD%\kl2.exe" ( echo Dog Days not found at %DD% & exit /b 1 )
tasklist /fi "imagename eq kl2.exe" | find /i "kl2.exe" >nul && ( echo kl2.exe is running: close the game first & exit /b 1 )
if exist "%DD%\d3d9.dll.klgfx" del "%DD%\d3d9.dll.klgfx"
copy /y "%~dp0d3d9.dll" "%DD%\d3d9.dll" >nul || exit /b 1
copy /y "%~dp0KLGfx.%PRESET%.ini" "%DD%\KLGfx.ini" >nul || exit /b 1
xcopy /e /i /y /q "%~dp0KLNR" "%DD%\KLNR" >nul || exit /b 1
if exist "%DD%\KLNR\klnr.log" del "%DD%\KLNR\klnr.log"
echo KLGfx installed in %DD% with preset %PRESET%. Logs: KLGfx.log and KLNR\klnr.log there.
endlocal
