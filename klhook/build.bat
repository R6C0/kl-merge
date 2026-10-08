@echo off
rem Builds dinput8.dll (32-bit) with Visual Studio's compiler into the work folder; does not install it.
rem dinput8.def is for MinGW (it names the function without the leading underscore MSVC adds),
rem so the export is given to the linker here instead.
setlocal
set VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat
if not exist "%VCVARS%" (echo Visual Studio C++ tools not found: add "Desktop development with C++" in the Visual Studio Installer. & exit /b 1)
set OUT=%~1
if "%OUT%"=="" set OUT=%~dp0out
if not exist "%OUT%" mkdir "%OUT%"
call "%VCVARS%" x86 >nul 2>nul
cd /d "%OUT%"
cl /nologo /O2 /LD /W3 /D_CRT_SECURE_NO_WARNINGS "%~dp0klhook.c" /Fe:dinput8.dll /link /EXPORT:DirectInput8Create=_DirectInput8Create@20 || exit /b 1
echo built %OUT%\dinput8.dll
