#!/usr/bin/env python3
r"""
kl_talk_bats.py - writes "INSTALL talk 1023.bat" and "UNDO talk 1023.bat" beside the staged KLTalk.ini files.

    python tools/kl_talk_bats.py [C:\kl_build_1019\talk_1023] [--game <Dog Days folder>]

INSTALL: refuses while kl2.exe runs; per map folder under <game>\KLExpansion\Maps that has a staged file: checks the staged file's
md5 and size (recorded here when the bat is written), keeps the old KLTalk.ini as KLTalk.ini.before-1023talk (an absent one leaves
KLTalk.ini.before-1023talk.absent; an existing backup is never overwritten), copies, re-checks the md5.
UNDO: same game-closed check; restores the backup (a file that is not the staged one is first kept as .edited-1023talk), or removes
the file INSTALL added. Only KLTalk.ini files are touched. The hook DLL is NOT part of these bats.
"""
import os, sys, hashlib

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'C:\kl_build_1019\talk_1023'

HEAD = r'''@echo off
setlocal enableextensions enabledelayedexpansion
set "GAME=@GAME@"
set "STAGE=%~dp0"
set FAIL=0
tasklist /fi "imagename eq kl2.exe" 2>nul | find /i "kl2.exe" >nul
if not errorlevel 1 (
  echo kl2.exe is running. Close the game first.
  exit /b 1
)
if not exist "%GAME%\KLExpansion\Maps\" (
  echo Not found: %GAME%\KLExpansion\Maps
  exit /b 1
)
'''

INSTALL_ONE = r'''goto :end

:one
set "SRC=%STAGE%%1\KLTalk.ini"
set "DIR=%GAME%\KLExpansion\Maps\%1"
set "DST=%DIR%\KLTalk.ini"
if not exist "%DIR%\" (echo %1: map folder absent, skipped& exit /b 0)
if not exist "%SRC%" (echo %1: staged file missing& set /a FAIL+=1& exit /b 0)
call :hash "%SRC%"
if /i not "!H!"=="%2" (echo %1: staged file md5 !H! is not the expected %2& set /a FAIL+=1& exit /b 0)
for %%F in ("%SRC%") do if not "%%~zF"=="%3" (echo %1: staged file size %%~zF is not %3& set /a FAIL+=1& exit /b 0)
if exist "%DST%" (
  if not exist "%DST%.before-1023talk" if not exist "%DST%.before-1023talk.absent" (
    copy /y "%DST%" "%DST%.before-1023talk" >nul
    for %%A in ("%DST%") do for %%B in ("%DST%.before-1023talk") do if not "%%~zA"=="%%~zB" (echo %1: backup size differs& set /a FAIL+=1& exit /b 0)
  )
) else (
  if not exist "%DST%.before-1023talk.absent" echo none> "%DST%.before-1023talk.absent"
)
copy /y "%SRC%" "%DST%" >nul
call :hash "%DST%"
if /i not "!H!"=="%2" (echo %1: installed file md5 !H! differs& set /a FAIL+=1& exit /b 0)
echo %1: installed
exit /b 0
'''

UNDO_ONE = r'''goto :end

:one
set "DIR=%GAME%\KLExpansion\Maps\%1"
set "DST=%DIR%\KLTalk.ini"
if not exist "%DIR%\" (echo %1: map folder absent, skipped& exit /b 0)
if exist "%DST%.before-1023talk" (
  if exist "%DST%" (
    call :hash "%DST%"
    if /i not "!H!"=="%2" (copy /y "%DST%" "%DST%.edited-1023talk" >nul& echo %1: KLTalk.ini was not the staged one, kept as KLTalk.ini.edited-1023talk)
  )
  copy /y "%DST%.before-1023talk" "%DST%" >nul
  for %%A in ("%DST%") do for %%B in ("%DST%.before-1023talk") do if not "%%~zA"=="%%~zB" (echo %1: restored size differs& set /a FAIL+=1& exit /b 0)
  echo %1: restored
  exit /b 0
)
if exist "%DST%.before-1023talk.absent" (
  if exist "%DST%" (
    call :hash "%DST%"
    if /i "!H!"=="%2" (del "%DST%"& echo %1: removed the installed file) else (echo %1: KLTalk.ini is not the staged one, left alone& set /a FAIL+=1)
  )
  exit /b 0
)
echo %1: nothing to undo
exit /b 0
'''

TAIL = r''':hash
set "H="
for /f "skip=1 delims=" %%L in ('certutil -hashfile "%~1" MD5') do if not defined H set "H=%%L"
set "H=%H: =%"
exit /b 0

:end
echo.
if %FAIL%==0 (echo @NAME@: done) else (echo @NAME@: %FAIL% problem^(s^), see above& exit /b 1)
exit /b 0
'''


def md5_size(path):
    b = open(path, 'rb').read()
    return hashlib.md5(b).hexdigest(), len(b)


def main():
    a = sys.argv[1:]
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--game')]
    out = pos[0] if pos else OUT
    maps = sorted(m for m in os.listdir(out) if os.path.isfile(os.path.join(out, m, 'KLTalk.ini')))
    rows = [(m,) + md5_size(os.path.join(out, m, 'KLTalk.ini')) for m in maps]
    for name, one, args in (('INSTALL talk 1023', INSTALL_ONE, lambda r: '%s %s %d' % r),
                            ('UNDO talk 1023', UNDO_ONE, lambda r: '%s %s' % r[:2])):
        text = HEAD.replace('@GAME@', game)
        text += 'rem %s: KLTalk.ini of %d maps (kl_talk_bats.py). Hook DLL not included.\n' % (name, len(rows))
        text += ''.join('call :one %s\n' % args(r) for r in rows)
        text += one + '\n' + TAIL.replace('@NAME@', name)
        with open(os.path.join(out, name + '.bat'), 'wb') as f:
            f.write(text.replace('\n', '\r\n').encode('ascii'))
    print('wrote %d maps and 2 bats in %s' % (len(rows), out))


if __name__ == '__main__':
    main()
