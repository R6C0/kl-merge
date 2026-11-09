@echo off
rem Builds ANP_Loader.asi (32-bit). Needs MinGW-w64 i686 GCC: i686-w64-mingw32-gcc on PATH,
rem or MSYS2's (pacman -S mingw-w64-i686-gcc) at C:\msys64\mingw32\bin, found automatically.
rem usage: build.bat [output folder]   (default ..\build; a relative folder is relative to loader\)
rem   e.g. loader\build.bat ..\work\out_ceg
setlocal
cd /d "%~dp0"
set "OUT=%~1"
if not defined OUT set "OUT=..\build"
if not exist "%OUT%" mkdir "%OUT%"
if exist "%OUT%\ANP_Loader.asi" del "%OUT%\ANP_Loader.asi"
set "CC="
where i686-w64-mingw32-gcc >nul 2>nul && set "CC=i686-w64-mingw32-gcc"
if not defined CC if exist C:\msys64\mingw32\bin\gcc.exe set "CC=C:\msys64\mingw32\bin\gcc.exe"
if not defined CC (echo BUILD FAILED: no 32-bit MinGW gcc found & exit /b 1)
set "PATH=C:\msys64\mingw32\bin;%PATH%"
"%CC%" -O2 -shared -o "%OUT%\ANP_Loader.asi" anp_loader.c -static-libgcc -lgdi32
if errorlevel 1 (echo BUILD FAILED & exit /b 1)
if not exist "%OUT%\ANP_Loader.asi" (echo BUILD FAILED: no output & exit /b 1)
echo Built %OUT%\ANP_Loader.asi
