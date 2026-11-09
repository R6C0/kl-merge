@echo off
rem Builds "..\KL Dead Men Rising.exe" from DeadMenRising.cs with the .NET Framework 4 C# compiler that ships with
rem Windows 10/11 (no SDK, no Visual Studio). Icon: dmr.ico (python make_icon.py redraws it). Manifest: app.manifest.
setlocal
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
if not exist "%CSC%" (echo .NET Framework 4 csc.exe not found. & exit /b 1)
set SMA=
for /d %%d in ("%WINDIR%\Microsoft.NET\assembly\GAC_MSIL\System.Management.Automation\v4.0_3.0.0.0__*") do set SMA=%%d\System.Management.Automation.dll
if not exist "%SMA%" (echo System.Management.Automation.dll ^(Windows PowerShell 5.1^) not found. & exit /b 1)
cd /d "%~dp0"
"%CSC%" /nologo /target:winexe /platform:anycpu /optimize+ /warn:4 /out:"..\KL Dead Men Rising.exe" ^
  /win32icon:dmr.ico /win32manifest:app.manifest ^
  /reference:"%SMA%" /reference:System.Windows.Forms.dll DeadMenRising.cs
if errorlevel 1 exit /b 1
echo built "..\KL Dead Men Rising.exe"
