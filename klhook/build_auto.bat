@echo off
rem Builds dinput8.dll (32-bit) WITH klauto.c (scripted input, breadcrumbs, [Engine] / CmdDrop; see the
rem comment at the top of klauto.c and re\fa_round.md). klauto.c includes klhook.c, so this DLL does
rem everything build.bat's does and behaves exactly like it while KLHook.ini has no [Auto] Enable=1.
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
cl /nologo /O2 /LD /W3 /D_CRT_SECURE_NO_WARNINGS "%~dp0klauto.c" /Fe:dinput8.dll /link /EXPORT:DirectInput8Create=_DirectInput8Create@20 || exit /b 1
echo built %OUT%\dinput8.dll
