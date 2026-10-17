@echo off
rem TEST build of KLHook: the SHIP build plus klauto.c (scripted input, breadcrumb detours, [Auto] / [Engine] /
rem [Script], result file, watchdog; see the comment at the top of klauto.c and re\fa_round.md). Same sources,
rem one more define. It behaves like the SHIP build while KLHook.ini has no [Auto] Enable=1 - except that a TEST
rem build never lets a write through to Steam (klsteam.c).
rem [KLHook] SessionSafe=1 (default) refuses every patch inside a range the game's integrity checks hash;
rem a direct-boot load test that wants all breadcrumbs sets SessionSafe=0.
rem Does not install: copy <out>\dinput8.dll and a KLHook.ini next to kl2.exe yourself.
rem   build_auto.bat [out folder]      default: klhook\out_auto
rem   build_auto.bat --work            into <work>\build\klhook\test\ : dinput8.dll, dinput8.dll.sha1, KLHook.ini (the
rem                                    plain sample: no script) and KLHook.round.ini (the scripted bank round) - the
rem                                    fixed place `kl_autotest.py --hook` takes the TEST build from (re\hook_live.md 1)
setlocal
set VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat
if not exist "%VCVARS%" (echo Visual Studio C++ tools not found: add "Desktop development with C++" in the Visual Studio Installer. & exit /b 1)
set "OUT=%~1"
set PUB=
if /i "%OUT%"=="--work" goto work
if "%OUT%"=="" set "OUT=%~dp0out_auto"
goto build
:work
rem the work folder: KL_WORK if set, else what tools\kl_port_check.workdir() answers (needs python on the PATH)
set PUB=1
set OUT=
if defined KL_WORK set "OUT=%KL_WORK%\build\klhook\test"
if not defined OUT for /f "usebackq delims=" %%i in (`python "%~dp0workdir.py"`) do set "OUT=%%i\build\klhook\test"
if not defined OUT (echo work folder not found: set KL_WORK, or put python on the PATH for klhook\workdir.py. & exit /b 1)
:build
if not exist "%OUT%" mkdir "%OUT%"
call "%VCVARS%" x86 >nul 2>nul
cd /d "%OUT%"
cl /nologo /O2 /LD /W3 /D_CRT_SECURE_NO_WARNINGS /DKLHOOK_TEST %KLHOOK_CFLAGS% "%~dp0klhook.c" /Fe:dinput8.dll /link /EXPORT:DirectInput8Create=_DirectInput8Create@20 || exit /b 1
echo built "%OUT%\dinput8.dll" (TEST)
if not defined PUB exit /b 0
rem --work: the folder holds exactly what a run needs - the DLL, its sha1 and an ini; the compiler's by-products go
del /q dinput8.exp dinput8.lib klhook.obj 2>nul
set H=
for /f "skip=1 delims=" %%h in ('certutil -hashfile dinput8.dll SHA1') do if not defined H set "H=%%h"
set H=%H: =%
set "SRC=%~dp0"
setlocal enabledelayedexpansion
> dinput8.dll.sha1 echo !H!  dinput8.dll  TEST  built %DATE% %TIME: =0% from !SRC!
copy /y "%~dp0KLHook.ini" KLHook.ini >nul
copy /y "%~dp0KLHook.round.ini" KLHook.round.ini >nul
type dinput8.dll.sha1
