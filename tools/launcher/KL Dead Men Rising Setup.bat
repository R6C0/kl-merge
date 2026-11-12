@echo off
setlocal EnableExtensions
rem ===========================================================================================
rem  KL Dead Men Rising Setup.bat - the one file a tester double-clicks (was "KLMerge Setup.bat"; inside, the
rem  project's files keep their KLMerge* names).
rem
rem  What it does, every time it runs (re-running = updating; nothing here needs admin rights):
rem    1. downloads the KL: Dead Men Rising release package (a zip) from RELEASE_URL into .\download\
rem       (only when the server copy is newer than what is already here),
rem    2. unpacks it into .\package\  (manifest.json, patches\*.klp, kl_release.py, optionally
rem       KLMergeSetup.exe, and launcher\ with the launcher files, which are copied up beside this .bat),
rem    3. makes sure a Python 3 with the 'zstandard' module is available when the package has no
rem       KLMergeSetup.exe: your own 'py' / 'python' if you have one, else the official embeddable
rem       Python from python.org is downloaded into .\python\ (nothing is installed system-wide),
rem    4. starts the launcher (KLMergeLauncher.ps1: PLAY DOG DAYS / PLAY DEAD MEN RISING / INSTALL / VERIFY / UNINSTALL).
rem
rem  The package holds ONLY the mod's own code and config plus binary patches; the game files are
rem  rebuilt on your PC from YOUR OWN Dog Days / Dead Men / Payday 2 installs (see README_TESTERS.md).
rem
rem  RELEASE_URL points at the newest release of the public repo github.com/R6C0/dead-men-rising
rem  (releases only, no game data). Each release carries the package as TWO assets named exactly
rem  KLMerge_package.zip (manifest, launcher, first half of the patches) and KLMerge_package_2.zip (the other
rem  patches): GitHub refuses one release file of 2 GiB or more. So this link never has to change.
rem ===========================================================================================

rem ---- the ONE line to edit -----------------------------------------------------------------
set "RELEASE_URL=https://github.com/R6C0/dead-men-rising/releases/latest/download/KLMerge_package.zip"
rem ---------------------------------------------------------------------------------------------
rem part 2 sits beside part 1 in the same release: the same link with .zip -> _2.zip
set "RELEASE_URL2=%RELEASE_URL:.zip=_2.zip%"

rem GUESS: Python 3.12.7 embeddable (64-bit). Any 3.9+ embeddable works; zstandard ships wheels for it.
set "PYTHON_EMBED_URL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
rem GUESS: the official get-pip bootstrap (the embeddable zip has no pip).
set "GETPIP_URL=https://bootstrap.pypa.io/get-pip.py"

cd /d "%~dp0"
set "HERE=%~dp0"
set "DL=%HERE%download"
set "PKG=%HERE%package"
set "PYDIR=%HERE%python"
set "ZIP=%DL%\KLMerge_package.zip"
set "ZIP2=%DL%\KLMerge_package_2.zip"
set "WINTAR=%SystemRoot%\System32\tar.exe"
set "LOG=%HERE%KLMerge_Setup.log"
set "PYEXE="
set "PYARG="

echo.
echo  ===== KL: DEAD MEN RISING - SETUP =====
echo  folder: "%HERE%"
echo  log:    "%LOG%"
echo.
echo [%date% %time%] setup started >> "%LOG%"

if not exist "%DL%" mkdir "%DL%"

rem ---- 0. is the URL still the placeholder? -------------------------------------------------
echo "%RELEASE_URL%" | findstr /i /c:"example.invalid" >nul
if not errorlevel 1 (
    if exist "%PKG%\manifest.json" (
        echo  RELEASE_URL is not set: skipping the download, using the package already in .\package\
        goto :python
    )
    echo  ERROR: RELEASE_URL at the top of this file still points at the placeholder.
    echo  This copy has no download link yet: ask @r6c0 on Discord for the current Setup file.
    goto :fail
)

rem ---- 1. download (both parts first, so a broken connection never leaves part 1 new and part 2 old unpacked) ----
echo  Downloading the package ^(2 parts^) ...
call :getpart "%RELEASE_URL%" "%ZIP%"
if errorlevel 1 goto :fail
call :getpart "%RELEASE_URL2%" "%ZIP2%"
if errorlevel 1 goto :fail

rem ---- 2. unpack both parts into .\package\ (each skipped when that exact zip was already unpacked) ----
rem part 1 brings manifest.json, part 2 brings package_part2.txt: each part's file proves that part is in .\package\
call :unpackpart "%ZIP%" "%DL%\unpacked.txt" "manifest.json"
if errorlevel 1 goto :fail
call :unpackpart "%ZIP2%" "%DL%\unpacked_2.txt" "package_part2.txt"
if errorlevel 1 goto :fail

:launcher_files
rem ---- 2b. the launcher files travel inside the package (launcher\) so that re-running updates them too
if exist "%PKG%\launcher\KLMergeLauncher.ps1" (
    copy /Y "%PKG%\launcher\KLMergeLauncher.ps1" "%HERE%" >nul
    rem the launcher start: a small exe (no console window; built from tools\launcher\exe\DeadMenRising.cs)
    if exist "%PKG%\launcher\KL Dead Men Rising.exe" copy /Y "%PKG%\launcher\KL Dead Men Rising.exe" "%HERE%" >nul
    if exist "%PKG%\launcher\README_TESTERS.md" copy /Y "%PKG%\launcher\README_TESTERS.md" "%HERE%" >nul
    rem the launcher's music tool (makes music\deadmen_riff.wav from YOUR Dead Men files; no audio is downloaded)
    if exist "%PKG%\launcher\kl_launcher_music.py" copy /Y "%PKG%\launcher\kl_launcher_music.py" "%HERE%" >nul
    if exist "%PKG%\launcher\kl_pyvorbis.py" copy /Y "%PKG%\launcher\kl_pyvorbis.py" "%HERE%" >nul
    if exist "%PKG%\launcher\kl_pybink.py" copy /Y "%PKG%\launcher\kl_pybink.py" "%HERE%" >nul
    rem the Ogg Vorbis decoder of the music tool (bin\kl_oggdec.exe, public-domain stb_vorbis; without it the tool tries ffmpeg, then kl_pyvorbis.py)
    if exist "%PKG%\launcher\bin\kl_oggdec.exe" (
        if not exist "%HERE%bin" mkdir "%HERE%bin"
        copy /Y "%PKG%\launcher\bin\kl_oggdec.exe" "%HERE%bin\" >nul
    )
    rem the two background pictures (bg\dead_men.jpg, bg\dog_days.jpg); the launcher also looks in package\launcher\bg itself
    if exist "%PKG%\launcher\bg\*.jpg" (
        if not exist "%HERE%bg" mkdir "%HERE%bg"
        copy /Y "%PKG%\launcher\bg\*.jpg" "%HERE%bg\" >nul
    )
)
if not exist "%HERE%KLMergeLauncher.ps1" (
    echo  ERROR: KLMergeLauncher.ps1 is neither beside this file nor in the package's launcher\ folder.
    goto :fail
)

:python
rem ---- 3. Python 3 + zstandard (only needed when the package has no frozen KLMergeSetup.exe) ----
if exist "%PKG%\KLMergeSetup.exe" (
    echo  package has KLMergeSetup.exe: no Python needed.
    goto :start
)
echo  Looking for Python 3 ...
rem PYEXE = the program (quoted on every call: a folder with spaces or '&' is fine), PYARG = '-3' for the py launcher
if exist "%PYDIR%\python.exe" (
    "%PYDIR%\python.exe" -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
    if not errorlevel 1 set "PYEXE=%PYDIR%\python.exe"
)
if defined PYEXE goto :py_found
py -3 -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
if errorlevel 1 goto :py_try_python
set "PYEXE=py"
set "PYARG=-3"
goto :py_found
:py_try_python
rem (the Windows Store 'python' alias prints a message and exits non-zero: it does not pass this test)
python -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
if not errorlevel 1 set "PYEXE=python"
if defined PYEXE goto :py_found

echo  No Python 3 found: fetching the embeddable Python into "%PYDIR%" ^(nothing is installed system-wide^) ...
if not exist "%PYDIR%" mkdir "%PYDIR%"
call :fetch "%PYTHON_EMBED_URL%" "%DL%\python_embed.zip"
if errorlevel 1 (
    echo  ERROR: could not download Python. Install Python 3 from python.org ^(tick "Add to PATH"^) and run this file again.
    goto :fail
)
set "PYZIP=%DL%\python_embed.zip"
rem Windows' own tar (System32): a tar.exe found on the PATH may be Git's GNU tar, which reads C: as a remote host
set "PYTAROK=0"
if exist "%WINTAR%" "%WINTAR%" -xf "%PYZIP%" -C "%PYDIR%" && set "PYTAROK=1"
if "%PYTAROK%"=="0" powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -LiteralPath $env:PYZIP -DestinationPath $env:PYDIR -Force"
if not exist "%PYDIR%\python.exe" (
    echo  ERROR: the Python zip did not unpack.
    goto :fail
)
set "PYEXE=%PYDIR%\python.exe"
echo  installing pip + zstandard into the embedded Python ...
call :embed_pip

:py_found
if defined PYARG (set "PYSHOW=%PYEXE% %PYARG%") else (set "PYSHOW=%PYEXE%")
echo  python: "%PYSHOW%"
"%PYEXE%" %PYARG% -c "import zstandard" >nul 2>nul
if not errorlevel 1 goto :py_ok
rem the embedded Python gets pip again (a first run stopped half-way leaves it without pip or zstandard);
rem it has no user site, so no --user there
if /i "%PYEXE%"=="%PYDIR%\python.exe" (
    echo  installing pip + zstandard into the embedded Python ...
    call :embed_pip
) else (
    echo  installing the 'zstandard' module ^(pip, for your user only^) ...
    "%PYEXE%" %PYARG% -m pip install --user --no-warn-script-location zstandard >> "%LOG%" 2>&1
)
"%PYEXE%" %PYARG% -c "import zstandard" >nul 2>nul
if errorlevel 1 (
    echo  ERROR: 'import zstandard' still fails. Open "%LOG%" and send it to @r6c0 on Discord, or install it by hand:
    echo         "%PYEXE%" %PYARG% -m pip install zstandard
    goto :fail
)
:py_ok
rem the launcher reads this: either "C:\...\python.exe" (quotes trimmed) or 'py -3'
rem (no ( ) block here: a ')' in the folder name would close it even in the branch not taken)
if defined PYARG goto :py_cmd_launcher
>"%HERE%python_cmd.txt" echo "%PYEXE%"
goto :py_cmd_done
:py_cmd_launcher
>"%HERE%python_cmd.txt" echo %PYEXE% %PYARG%
:py_cmd_done
echo [%date% %time%] python ok: "%PYSHOW%" >> "%LOG%"

:start
rem ---- 4. launcher ---------------------------------------------------------------------------
echo.
echo  Starting the launcher ...
echo [%date% %time%] launcher started >> "%LOG%"
rem the exe runs KLMergeLauncher.ps1 in its own process: no console window stays behind
if exist "%HERE%KL Dead Men Rising.exe" (
    start "" "%HERE%KL Dead Men Rising.exe"
    endlocal
    exit /b 0
)
rem no exe (an old package): minimized, not -WindowStyle Hidden: the hidden form trips Defender's heuristic
rem (Trojan:Win32/Ceprolad.A fired on a .bat with that line + Bypass)
start "KL Dead Men Rising" /min powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%HERE%KLMergeLauncher.ps1"
endlocal
exit /b 0

:fail
echo.
echo  Setup did not finish. Fix the line above and run this file again.
echo [%date% %time%] setup FAILED >> "%LOG%"
pause
endlocal
exit /b 1

rem ---- subroutines -----------------------------------------------------------------------------
:getpart
rem call :getpart <url> <zip>: errorlevel 1 = failed (the message is already printed)
rem the download lands in <zip>.part and replaces <zip> only when it finished: a broken connection never
rem leaves a half zip that a later run's -z would treat as current
set "GURL=%~1"
set "GZIP=%~2"
set "GPART=%~2.part"
echo      "%GURL%"
rem no del anywhere in this file (Defender flags .bat files that delete): a stale .part is emptied instead
type nul >"%GPART%"
where curl.exe >nul 2>nul
if errorlevel 1 goto :gp_ps
rem -z: only download when the server copy is newer than the file we already have (re-runs are cheap;
rem a 304 answer writes nothing, so the .part stays empty and the old zip stays)
rem -R: the zip keeps the server's Last-Modified time, so -z compares server time with server time (both parts stay in step)
if exist "%GZIP%" (
    curl.exe -L -f -R -# -z "%GZIP%" -o "%GPART%" "%GURL%"
) else (
    curl.exe -L -f -R -# -o "%GPART%" "%GURL%"
)
set "RC=%errorlevel%"
if not "%RC%"=="0" (
    type nul >"%GPART%"
    echo  ERROR: download failed ^(curl exit %RC%^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, curl exit %RC%, "%GURL%" >> "%LOG%"
    exit /b 1
)
goto :gp_move
:gp_ps
rem paths and URL reach PowerShell as environment variables: an apostrophe in a folder name cannot break the command
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri $env:GURL -OutFile $env:GPART -UseBasicParsing"
if errorlevel 1 (
    type nul >"%GPART%"
    echo  ERROR: download failed ^(PowerShell^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, powershell, "%GURL%" >> "%LOG%"
    exit /b 1
)
:gp_move
set "PARTSIZE=0"
for %%A in ("%GPART%") do set "PARTSIZE=%%~zA"
if "%PARTSIZE%"=="0" goto :gp_check
move /y "%GPART%" "%GZIP%" >nul
if errorlevel 1 (
    echo  ERROR: could not replace "%GZIP%" ^(open in another program?^)
    exit /b 1
)
:gp_check
if not exist "%GZIP%" (
    echo  ERROR: no file arrived at "%GZIP%"
    exit /b 1
)
for %%A in ("%GZIP%") do set "ZIPSIZE=%%~zA"
echo  downloaded: %ZIPSIZE% bytes
echo [%date% %time%] downloaded %ZIPSIZE% bytes, "%GZIP%" >> "%LOG%"
exit /b 0

:unpackpart
rem call :unpackpart <zip> <stamp file> <file this part puts into .\package\>: errorlevel 1 = failed
set "UZIP=%~1"
set "USTAMPF=%~2"
set "UMARK=%~3"
set "STAMP="
if exist "%USTAMPF%" set /p STAMP=<"%USTAMPF%"
for %%A in ("%UZIP%") do set "NOWSTAMP=%%~zA_%%~tA"
if not "%STAMP%"=="%NOWSTAMP%" goto :up_go
if not exist "%PKG%\%UMARK%" goto :up_go
echo  %~nx1 already unpacked ^(same download^).
exit /b 0
:up_go
echo  Unpacking %~nx1 into "%PKG%" ...
>"%USTAMPF%" echo none
rem an old marker would hide a failed unpack: it comes back only from this zip
if exist "%PKG%\%UMARK%" move /y "%PKG%\%UMARK%" "%DL%\%UMARK%.before-unpack" >nul
if not exist "%PKG%" mkdir "%PKG%"
if not exist "%WINTAR%" goto :up_ps
"%WINTAR%" -xf "%UZIP%" -C "%PKG%"
if errorlevel 1 goto :up_ps
goto :up_done
:up_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -LiteralPath $env:UZIP -DestinationPath $env:PKG -Force"
if errorlevel 1 (
    echo  ERROR: could not unpack "%UZIP%" ^(damaged download: it is set aside as .bad, run this file again^)
    echo [%date% %time%] unpack failed, "%UZIP%" >> "%LOG%"
    move /y "%UZIP%" "%UZIP%.bad" >nul 2>nul
    exit /b 1
)
:up_done
rem a zip with one top-level folder: pull its contents up so that the marker sits in .\package\
if not exist "%PKG%\%UMARK%" (
    for /d %%D in ("%PKG%\*") do (
        if exist "%%D\%UMARK%" (
            echo  ^(package was inside folder %%~nxD: moving it up^)
            rem /MOVE is a MOVE of the unpacked files one folder up (the emptied wrapper folder goes with it);
            rem it is the only thing in this file that takes a path away, and it only ever touches .\package\
            robocopy "%%D" "%PKG%" /E /MOVE /NFL /NDL /NJH /NJS /NP >nul
        )
    )
)
if not exist "%PKG%\%UMARK%" (
    echo  ERROR: "%UZIP%" has no %UMARK% ^(not a Dead Men Rising release package part^).
    echo [%date% %time%] no %UMARK% after unpack >> "%LOG%"
    move /y "%UZIP%" "%UZIP%.bad" >nul 2>nul
    exit /b 1
)
>"%USTAMPF%" echo %NOWSTAMP%
echo [%date% %time%] unpacked "%UZIP%" >> "%LOG%"
exit /b 0

:fetch
rem call :fetch <url> <file>: curl, else PowerShell (URL and path go in as environment variables); errorlevel 1 = failed
set "FURL=%~1"
set "FOUT=%~2"
type nul >"%FOUT%"
where curl.exe >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri $env:FURL -OutFile $env:FOUT -UseBasicParsing"
) else (
    curl.exe -L -f -# -o "%FOUT%" "%FURL%"
)
if errorlevel 1 (
    type nul >"%FOUT%"
    exit /b 1
)
set "FSIZE=0"
for %%A in ("%FOUT%") do set "FSIZE=%%~zA"
if "%FSIZE%"=="0" exit /b 1
exit /b 0

:embed_pip
rem pip + zstandard into .\python\ (embeddable). Safe to repeat. errorlevel 1 = failed (details in the log)
rem the embeddable Python ignores site-packages until its ._pth file says 'import site'
for %%F in ("%PYDIR%\python3*._pth") do (
    findstr /b /c:"import site" "%%F" >nul || (
        echo Lib\site-packages>>"%%F"
        echo import site>>"%%F"
    )
)
rem fetched every time: a failed fetch leaves an empty get-pip.py (this file never deletes)
call :fetch "%GETPIP_URL%" "%DL%\get-pip.py"
if errorlevel 1 (
    echo [%date% %time%] get-pip.py download failed >> "%LOG%"
    exit /b 1
)
"%PYDIR%\python.exe" "%DL%\get-pip.py" --no-warn-script-location >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%date% %time%] get-pip.py failed >> "%LOG%"
    exit /b 1
)
"%PYDIR%\python.exe" -m pip install --no-warn-script-location zstandard >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%date% %time%] pip install zstandard failed >> "%LOG%"
    exit /b 1
)
exit /b 0
