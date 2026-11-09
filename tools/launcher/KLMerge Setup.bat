@echo off
setlocal EnableExtensions
rem ===========================================================================================
rem  KLMerge Setup.bat - the one file a tester double-clicks.
rem
rem  What it does, every time it runs (re-running = updating; nothing here needs admin rights):
rem    1. downloads the KL Merge release package (a zip) from RELEASE_URL into .\download\
rem       (only when the server copy is newer than what is already here),
rem    2. unpacks it into .\package\  (manifest.json, patches\*.klp, kl_release.py, optionally
rem       KLMergeSetup.exe, and launcher\ with the launcher files, which are copied up beside this .bat),
rem    3. makes sure a Python 3 with the 'zstandard' module is available when the package has no
rem       KLMergeSetup.exe: your own 'py' / 'python' if you have one, else the official embeddable
rem       Python from python.org is downloaded into .\python\ (nothing is installed system-wide),
rem    4. starts the launcher (KLMergeLauncher.ps1: PLAY DOG DAYS / PLAY KL MERGE / INSTALL / VERIFY / UNINSTALL).
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
set "PYCMD="

echo.
echo  ===== KL MERGE SETUP =====
echo  folder: %HERE%
echo  (log: %LOG%)
echo.
echo [%date% %time%] setup started >> "%LOG%"

if not exist "%DL%" mkdir "%DL%"

rem ---- 0. is the URL still the placeholder? -------------------------------------------------
echo %RELEASE_URL% | findstr /i /c:"example.invalid" >nul
if not errorlevel 1 (
    if exist "%PKG%\manifest.json" (
        echo  RELEASE_URL is not set: skipping the download, using the package already in .\package\
        goto :python
    )
    echo  ERROR: RELEASE_URL at the top of this file still points at the placeholder.
    echo  Josh must set it to the real package URL before handing the file out.
    goto :fail
)

rem ---- 1. download ---------------------------------------------------------------------------
echo  Downloading the package ...
echo      %RELEASE_URL%
where curl.exe >nul 2>nul
if errorlevel 1 goto :dl_ps
rem -z: only download when the server copy is newer than the file we already have (re-runs are cheap)
if exist "%ZIP%" (
    curl.exe -L -f -# -z "%ZIP%" -o "%ZIP%" "%RELEASE_URL%"
) else (
    curl.exe -L -f -# -o "%ZIP%" "%RELEASE_URL%"
)
if errorlevel 1 (
    echo  ERROR: download failed ^(curl exit %errorlevel%^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, curl exit %errorlevel% >> "%LOG%"
    goto :fail
)
goto :dl_done

:dl_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%RELEASE_URL%' -OutFile '%ZIP%' -UseBasicParsing"
if errorlevel 1 (
    echo  ERROR: download failed ^(PowerShell^). Check the URL / your connection and run this file again.
    echo [%date% %time%] download failed, powershell >> "%LOG%"
    goto :fail
)

:dl_done
if not exist "%ZIP%" (
    echo  ERROR: no file arrived at %ZIP%
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
echo  Unpacking into %PKG% ...
if not exist "%PKG%" mkdir "%PKG%"
where tar.exe >nul 2>nul
if errorlevel 1 goto :unpack_ps
tar.exe -xf "%ZIP%" -C "%PKG%"
if errorlevel 1 goto :unpack_ps
goto :unpacked

:unpack_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PKG%' -Force"
if errorlevel 1 (
    echo  ERROR: could not unpack %ZIP%
    echo [%date% %time%] unpack failed >> "%LOG%"
    goto :fail
)

:unpacked
rem a zip with one top-level folder: pull its contents up so that package\manifest.json exists
if not exist "%PKG%\manifest.json" (
    for /d %%D in ("%PKG%\*") do (
        if exist "%%D\manifest.json" (
            echo  (package was inside folder %%~nxD: moving it up)
            robocopy "%%D" "%PKG%" /E /MOVE /NFL /NDL /NJH /NJS /NP >nul
        )
    )
)
if not exist "%PKG%\manifest.json" (
    echo  ERROR: the package has no manifest.json ^(not a KL Merge release package^).
    echo [%date% %time%] no manifest.json after unpack >> "%LOG%"
    goto :fail
)
echo %NOWSTAMP%>"%DL%\unpacked.txt"
echo [%date% %time%] unpacked >> "%LOG%"

:launcher_files
rem ---- 2b. the launcher files travel inside the package (launcher\) so that re-running updates them too
if exist "%PKG%\launcher\KLMergeLauncher.ps1" (
    copy /Y "%PKG%\launcher\KLMergeLauncher.ps1" "%HERE%" >nul
    if exist "%PKG%\launcher\KLMerge.bat" copy /Y "%PKG%\launcher\KLMerge.bat" "%HERE%" >nul
    if exist "%PKG%\launcher\README_TESTERS.md" copy /Y "%PKG%\launcher\README_TESTERS.md" "%HERE%" >nul
    rem the launcher's music tool (makes music\deadmen_menu.wav from YOUR Dead Men files; no audio is downloaded)
    if exist "%PKG%\launcher\kl_launcher_music.py" copy /Y "%PKG%\launcher\kl_launcher_music.py" "%HERE%" >nul
    if exist "%PKG%\launcher\kl_pyvorbis.py" copy /Y "%PKG%\launcher\kl_pyvorbis.py" "%HERE%" >nul
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
if exist "%PYDIR%\python.exe" (
    "%PYDIR%\python.exe" -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
    if not errorlevel 1 set "PYCMD=%PYDIR%\python.exe"
)
if defined PYCMD goto :py_found
py -3 -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if defined PYCMD goto :py_found
rem (the Windows Store 'python' alias prints a message and exits non-zero: it does not pass this test)
python -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=python"
if defined PYCMD goto :py_found

echo  No Python 3 found: fetching the embeddable Python into %PYDIR% ^(nothing is installed system-wide^) ...
if not exist "%PYDIR%" mkdir "%PYDIR%"
where curl.exe >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_EMBED_URL%' -OutFile '%DL%\python_embed.zip' -UseBasicParsing; Invoke-WebRequest -Uri '%GETPIP_URL%' -OutFile '%DL%\get-pip.py' -UseBasicParsing"
) else (
    curl.exe -L -f -# -o "%DL%\python_embed.zip" "%PYTHON_EMBED_URL%"
    curl.exe -L -f -s -o "%DL%\get-pip.py" "%GETPIP_URL%"
)
if not exist "%DL%\python_embed.zip" (
    echo  ERROR: could not download Python. Install Python 3 from python.org ^(tick "Add to PATH"^) and run this file again.
    goto :fail
)
where tar.exe >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%DL%\python_embed.zip' -DestinationPath '%PYDIR%' -Force"
) else (
    tar.exe -xf "%DL%\python_embed.zip" -C "%PYDIR%"
)
if not exist "%PYDIR%\python.exe" (
    echo  ERROR: the Python zip did not unpack.
    goto :fail
)
rem the embeddable Python ignores site-packages until its ._pth file says 'import site'
for %%F in ("%PYDIR%\python3*._pth") do (
    findstr /b /c:"import site" "%%F" >nul || (
        echo Lib\site-packages>>"%%F"
        echo import site>>"%%F"
    )
)
set "PYCMD=%PYDIR%\python.exe"
echo  installing pip + zstandard into the embedded Python ...
"%PYDIR%\python.exe" "%DL%\get-pip.py" --no-warn-script-location >> "%LOG%" 2>&1
"%PYDIR%\python.exe" -m pip install --no-warn-script-location zstandard >> "%LOG%" 2>&1

:py_found
echo  python: %PYCMD%
%PYCMD% -c "import zstandard" >nul 2>nul
if errorlevel 1 (
    echo  installing the 'zstandard' module ^(pip, for your user only^) ...
    %PYCMD% -m pip install --user --no-warn-script-location zstandard >> "%LOG%" 2>&1
    %PYCMD% -c "import zstandard" >nul 2>nul
    if errorlevel 1 (
        echo  ERROR: 'import zstandard' still fails. Open %LOG% and send it to Josh, or install it by hand:
        echo         %PYCMD% -m pip install zstandard
        goto :fail
    )
)
echo %PYCMD%>"%HERE%python_cmd.txt"
echo [%date% %time%] python ok: %PYCMD% >> "%LOG%"

:start
rem ---- 4. launcher ---------------------------------------------------------------------------
echo.
echo  Starting the launcher ...
echo [%date% %time%] launcher started >> "%LOG%"
start "" powershell -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%HERE%KLMergeLauncher.ps1"
endlocal
exit /b 0

:fail
echo.
echo  Setup did not finish. Fix the line above and run this file again.
echo [%date% %time%] setup FAILED >> "%LOG%"
pause
endlocal
exit /b 1
