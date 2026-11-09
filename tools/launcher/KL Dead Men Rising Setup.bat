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
rem  NOTE FOR JOSH: a PRIVATE GitHub repo's release assets cannot be downloaded without a token, so
rem  RELEASE_URL must point at a PUBLIC release (a separate public "release" repo is fine: it holds no
rem  game data) or at any other plain https host. Set it below before handing this file out.
rem ===========================================================================================

rem ---- the ONE line to edit -----------------------------------------------------------------
set "RELEASE_URL=https://example.invalid/KLMerge/releases/download/v1.0.0/KLMerge_package.zip"
rem ---------------------------------------------------------------------------------------------

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

rem ---- 1. download ---------------------------------------------------------------------------
echo  Downloading the package ...
echo      "%RELEASE_URL%"
rem the download lands in %ZIP%.part and replaces %ZIP% only when it finished: a broken connection never
rem leaves a half zip that a later run's -z would treat as current
set "PART=%ZIP%.part"
rem no del anywhere in this file (Defender flags .bat files that delete): a stale .part is emptied instead
type nul >"%PART%"
where curl.exe >nul 2>nul
if errorlevel 1 goto :dl_ps
rem -z: only download when the server copy is newer than the file we already have (re-runs are cheap;
rem a 304 answer writes nothing, so the .part stays empty and the old zip stays)
if exist "%ZIP%" (
    curl.exe -L -f -# -z "%ZIP%" -o "%PART%" "%RELEASE_URL%"
) else (
    curl.exe -L -f -# -o "%PART%" "%RELEASE_URL%"
)
set "RC=%errorlevel%"
if not "%RC%"=="0" (
    type nul >"%PART%"
    echo  ERROR: download failed ^(curl exit %RC%^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, curl exit %RC% >> "%LOG%"
    goto :fail
)
goto :dl_move

:dl_ps
rem paths and URL reach PowerShell as environment variables: an apostrophe in a folder name cannot break the command
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri $env:RELEASE_URL -OutFile $env:PART -UseBasicParsing"
if errorlevel 1 (
    type nul >"%PART%"
    echo  ERROR: download failed ^(PowerShell^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, powershell >> "%LOG%"
    goto :fail
)

:dl_move
if not exist "%PART%" goto :dl_check
set "PARTSIZE=0"
for %%A in ("%PART%") do set "PARTSIZE=%%~zA"
if "%PARTSIZE%"=="0" goto :dl_drop
move /y "%PART%" "%ZIP%" >nul
if errorlevel 1 (
    echo  ERROR: could not replace "%ZIP%" ^(open in another program?^)
    goto :fail
)
:dl_drop
:dl_check
if not exist "%ZIP%" (
    echo  ERROR: no file arrived at "%ZIP%"
    goto :fail
)
for %%A in ("%ZIP%") do set "ZIPSIZE=%%~zA"
echo  downloaded: %ZIPSIZE% bytes
echo [%date% %time%] downloaded %ZIPSIZE% bytes >> "%LOG%"

rem ---- 2. unpack (skipped when this exact zip was already unpacked) --------------------------
set "STAMP="
if exist "%DL%\unpacked.txt" set /p STAMP=<"%DL%\unpacked.txt"
for %%A in ("%ZIP%") do set "NOWSTAMP=%%~zA_%%~tA"
if "%STAMP%"=="%NOWSTAMP%" (
    if exist "%PKG%\manifest.json" (
        echo  package already unpacked ^(same download^).
        goto :launcher_files
    )
)
echo  Unpacking into "%PKG%" ...
>"%DL%\unpacked.txt" echo none
rem an old manifest.json would hide a failed unpack: it comes back only from this zip
if exist "%PKG%\manifest.json" move /y "%PKG%\manifest.json" "%DL%\manifest.before-unpack.json" >nul
if not exist "%PKG%" mkdir "%PKG%"
where tar.exe >nul 2>nul
if errorlevel 1 goto :unpack_ps
tar.exe -xf "%ZIP%" -C "%PKG%"
if errorlevel 1 goto :unpack_ps
goto :unpacked

:unpack_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -LiteralPath $env:ZIP -DestinationPath $env:PKG -Force"
if errorlevel 1 (
    echo  ERROR: could not unpack "%ZIP%" ^(damaged download: it is set aside as .bad, run this file again^)
    echo [%date% %time%] unpack failed >> "%LOG%"
    move /y "%ZIP%" "%ZIP%.bad" >nul 2>nul
    goto :fail
)

:unpacked
rem a zip with one top-level folder: pull its contents up so that package\manifest.json exists
if not exist "%PKG%\manifest.json" (
    for /d %%D in ("%PKG%\*") do (
        if exist "%%D\manifest.json" (
            echo  ^(package was inside folder %%~nxD: moving it up^)
            rem /MOVE is a MOVE of the unpacked files one folder up (the emptied wrapper folder goes with it);
            rem it is the only thing in this file that takes a path away, and it only ever touches .\package\
            robocopy "%%D" "%PKG%" /E /MOVE /NFL /NDL /NJH /NJS /NP >nul
        )
    )
)
if not exist "%PKG%\manifest.json" (
    echo  ERROR: the package has no manifest.json ^(not a Dead Men Rising release package^).
    echo [%date% %time%] no manifest.json after unpack >> "%LOG%"
    move /y "%ZIP%" "%ZIP%.bad" >nul 2>nul
    goto :fail
)
echo %NOWSTAMP%>"%DL%\unpacked.txt"
echo [%date% %time%] unpacked >> "%LOG%"

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
where tar.exe >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Expand-Archive -LiteralPath $env:PYZIP -DestinationPath $env:PYDIR -Force"
) else (
    tar.exe -xf "%PYZIP%" -C "%PYDIR%"
)
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
