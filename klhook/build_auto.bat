@echo off
rem TEST build of KLHook: the SHIP build plus klauto.c (scripted input, breadcrumb detours, [Auto] / [Engine] /
rem [Script], result file, watchdog; see the comment at the top of klauto.c and re\fa_round.md). Same sources,
rem one more define. It behaves like the SHIP build while KLHook.ini has no [Auto] Enable=1.
rem [KLHook] SessionSafe=1 (default) refuses every patch inside a range the game's integrity checks hash;
rem a direct-boot load test that wants all breadcrumbs sets SessionSafe=0.
rem Does not install: copy <out>\dinput8.dll and a KLHook.ini next to kl2.exe yourself.
rem   build_auto.bat [out folder]      default: klhook\out_auto
setlocal
set VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat
if not exist "%VCVARS%" (echo Visual Studio C++ tools not found: add "Desktop development with C++" in the Visual Studio Installer. & exit /b 1)
set OUT=%~1
if "%OUT%"=="" set OUT=%~dp0out_auto
if not exist "%OUT%" mkdir "%OUT%"
call "%VCVARS%" x86 >nul 2>nul
cd /d "%OUT%"
cl /nologo /O2 /LD /W3 /D_CRT_SECURE_NO_WARNINGS /DKLHOOK_TEST %KLHOOK_CFLAGS% "%~dp0klhook.c" /Fe:dinput8.dll /link /EXPORT:DirectInput8Create=_DirectInput8Create@20 || exit /b 1
echo built %OUT%\dinput8.dll (TEST)
