@echo off
rem Builds ..\bin\kl_oggdec.exe (32-bit, static CRT) from kl_oggdec.c + stb_vorbis.c (v1.22, public domain).
rem stb_vorbis.c is pinned: its sha256 is in stb_vorbis.sha256 and this script refuses a different file.
rem Re-fetch: curl -sL -o stb_vorbis.c https://raw.githubusercontent.com/nothings/stb/master/stb_vorbis.c
setlocal
set VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat
if not exist "%VCVARS%" (echo Visual Studio C++ tools not found. & exit /b 1)
cd /d "%~dp0"
set WANT=
for /f "tokens=1" %%h in (stb_vorbis.sha256) do set WANT=%%h
set GOT=
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile stb_vorbis.c SHA256') do if not defined GOT set GOT=%%h
if /i not "%GOT%"=="%WANT%" (echo REFUSED: stb_vorbis.c sha256 %GOT% is not the pinned %WANT% & exit /b 1)
if not exist ..\bin mkdir ..\bin
call "%VCVARS%" x86 >nul 2>nul
cl /nologo /O2 /MT /W3 /D_CRT_SECURE_NO_WARNINGS /Fe..\bin\kl_oggdec.exe /Fo%TEMP%\ kl_oggdec.c
if errorlevel 1 exit /b 1
echo built ..\bin\kl_oggdec.exe
