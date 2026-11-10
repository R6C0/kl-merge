@echo off
rem builds and runs klmemfree_test.c (x86). Output into %TEMP%.
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul 2>nul
cd /d "%~dp0"
cl /nologo /O2 /W3 /D_CRT_SECURE_NO_WARNINGS klmemfree_test.c /Fe:%TEMP%\klmemfree_test.exe /Fo:%TEMP%\klmemfree_test.obj || exit /b 1
%TEMP%\klmemfree_test.exe
