@echo off
rem SHIP build of KLHook: dinput8.dll (32-bit) from klhook.c + klfix.c + klslot.c + klsteam.c + kljoin.c, WITHOUT the
rem test rig klauto.c. This is what a player of the expansion runs: crash logging, the leaderboard fix, the
rem expansion's file redirect and menu page, the Steam write guard; import slots and data only (klhook.c's top
rem comment has the table of every site).
rem Does not install: copy <out>\dinput8.dll and KLHook.ini next to kl2.exe yourself.
rem   build.bat [out folder]      default: klhook\out
rem   build.bat --work            into <work>\build\klhook\ship\ : dinput8.dll, dinput8.dll.sha1 and KLHook.ini (the
rem                               sample of this folder) - the fixed place tools and the live agent take the SHIP
rem                               build from (re\hook_live.md 1). Other files there (READ ME.txt) are left alone.
rem dinput8.def is for MinGW (it names the function without the leading underscore MSVC adds),
rem so the export is given to the linker here instead.
setlocal
set VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat
if not exist "%VCVARS%" (echo Visual Studio C++ tools not found: add "Desktop development with C++" in the Visual Studio Installer. & exit /b 1)
set OUT=%~1
set PUB=
if /i "%OUT%"=="--work" goto work
if "%OUT%"=="" set OUT=%~dp0out
goto build
:work
rem the work folder: KL_WORK if set, else what tools\kl_port_check.workdir() answers (needs python on the PATH)
set PUB=1
set OUT=
if defined KL_WORK set "OUT=%KL_WORK%\build\klhook\ship"
if not defined OUT for /f "usebackq delims=" %%i in (`python "%~dp0workdir.py"`) do set "OUT=%%i\build\klhook\ship"
if not defined OUT (echo work folder not found: set KL_WORK, or put python on the PATH for klhook\workdir.py. & exit /b 1)
:build
if not exist "%OUT%" mkdir "%OUT%"
call "%VCVARS%" x86 >nul 2>nul
cd /d "%OUT%"
cl /nologo /O2 /LD /W3 /D_CRT_SECURE_NO_WARNINGS %KLHOOK_CFLAGS% "%~dp0klhook.c" /Fe:dinput8.dll /link /EXPORT:DirectInput8Create=_DirectInput8Create@20 || exit /b 1
echo built %OUT%\dinput8.dll (SHIP)
if not defined PUB exit /b 0
rem --work: the folder holds exactly what a run needs - the DLL, its sha1 and an ini; the compiler's by-products go
del /q dinput8.exp dinput8.lib klhook.obj 2>nul
set H=
for /f "skip=1 delims=" %%h in ('certutil -hashfile dinput8.dll SHA1') do if not defined H set "H=%%h"
set H=%H: =%
> dinput8.dll.sha1 echo %H%  dinput8.dll  SHIP  built %DATE% %TIME: =0% from %~dp0
copy /y "%~dp0KLHook.ini" KLHook.ini >nul
type dinput8.dll.sha1
