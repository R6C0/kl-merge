#!/usr/bin/env python3
r"""
STAGE 'cover3' (2026-10-24 17:30): for every Dead Men map that rev_1024 stripped, take the CURRENTLY LIVE zip, put the
NoCoverBox controllers of the hazard markers back (kl_cover_restore) and switch off the doubtful cover2 boxes
(kl_cover_add2), into <out>\<map>\<slot>_Main.zip, and write INSTALL cover3.bat / UNDO cover3.bat next to them.
OFFLINE: reads the game folder, writes ONLY <out>. Never installs.

    python kl_cover3_stage.py <out folder> [MAP ...]
"""
import hashlib, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_cover_restore as R
import kl_cover_add2 as A2

MAPS = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def live(m):
    d = os.path.join(MAPS, m)
    z = [f for f in os.listdir(d) if f.lower().endswith('_main.zip')]
    don = [f for f in os.listdir(d) if f.lower().endswith('_main.zip.before-1024cover')]
    return (os.path.join(d, z[0]), os.path.join(d, don[0])) if z and don else None


def stage(out, maps):
    rows = []
    for m in maps:
        lv = live(m)
        if not lv:
            print(m, 'no donor (.before-1024cover): skipped')
            continue
        lz, dz = lv
        mid = os.path.join(out, '_mid', m)
        fin = os.path.join(out, m)
        r = R.restore(lz, dz, mid) or lz
        f = A2.disable(r, dz, fin)
        rows.append((m, os.path.basename(lz).split('_Main')[0], md5(lz), md5(f)))
    return rows


def bats(out, rows):
    head = ('@echo off\nrem cover3 (2026-10-24): %s\nrem Per map: refused unless the live zip is exactly the one this was built on (md5); the live zip is MOVED to '
            '.before-1024cover3 (never overwrites a backup, never touches other *.before-* files).\nrem NOT RUN by the agent. Undo: UNDO cover3.bat.\n'
            'setlocal\ntasklist /FI "IMAGENAME eq kl2.exe" 2>nul | find /I "kl2.exe" >nul\nif not errorlevel 1 (\n  echo REFUSED: kl2.exe is running.\n  exit /b 1\n)\n'
            'set "SRC=%%~dp0"\nset "MAPS=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Maps"\n')
    ins = head % ('NoCoverBox back on the hazard markers (bug-fix, respawn, door, stairs, escalator, garage ...) + the doubtful cover2 boxes switched off.')
    und = head % ('undo: the zip moved to .before-1024cover3 goes back.')
    for m, slot, a, b in rows:
        ins += 'call :one %s %s %s %s\n' % (m, slot, a, b)
        und += 'call :undo %s %s %s\n' % (m, slot, b)
    ins += ('echo Done. Undo: UNDO cover3.bat\nexit /b 0\n\n:one\nset "M=%~1"\nset "F=%~2"\nset "OLDMD=%~3"\nset "NEWMD=%~4"\n'
            'set "DST=%MAPS%\\%M%\\%F%_Main.zip"\nset "NEW=%SRC%%M%\\%F%_Main.zip"\n'
            'if not exist "%DST%" (echo %M%: live zip missing & goto :eof)\nif not exist "%NEW%" (echo %M%: staged zip missing & goto :eof)\n'
            'if exist "%DST%.before-1024cover3" (echo %M%: backup .before-1024cover3 already exists, skipped & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:NEW).Hash.ToLower()"\') do set "GN=%%H"\n'
            'if /I not "%GN%"=="%NEWMD%" (echo %M%: staged zip is not the verified one, skipped & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:DST).Hash.ToLower()"\') do set "GL=%%H"\n'
            'if /I "%GL%"=="%NEWMD%" (echo %M%: already installed & goto :eof)\n'
            'if /I not "%GL%"=="%OLDMD%" (echo %M%: live zip is not the one cover3 was built on ^(md5 %GL%^), skipped - rebuild with kl_cover3_stage.py & goto :eof)\n'
            'move "%DST%" "%DST%.before-1024cover3" >nul || (echo %M%: FAILED to move & goto :eof)\n'
            'copy /Y "%NEW%" "%DST%" >nul || (echo %M%: copy FAILED, restoring & move "%DST%.before-1024cover3" "%DST%" >nul & goto :eof)\n'
            'echo %M%: installed\ngoto :eof\n')
    und += ('echo Done.\nexit /b 0\n\n:undo\nset "M=%~1"\nset "F=%~2"\nset "NEWMD=%~3"\n'
            'set "DST=%MAPS%\\%M%\\%F%_Main.zip"\nif not exist "%DST%.before-1024cover3" (echo %M%: no .before-1024cover3 backup, nothing to undo & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:DST).Hash.ToLower()"\') do set "GL=%%H"\n'
            'if /I not "%GL%"=="%NEWMD%" (echo %M%: live zip is not the cover3 one ^(md5 %GL%^), skipped - something newer was installed & goto :eof)\n'
            'del "%DST%" || (echo %M%: FAILED to remove & goto :eof)\n'
            'move "%DST%.before-1024cover3" "%DST%" >nul || (echo %M%: FAILED to move back & goto :eof)\n'
            'echo %M%: restored\ngoto :eof\n')
    for n, t in (('INSTALL cover3.bat', ins), ('UNDO cover3.bat', und)):
        with open(os.path.join(out, n), 'w', newline='') as fh:
            fh.write(t.replace('\n', '\r\n'))


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    out = a[0]
    maps = a[1:] or sorted(x for x in os.listdir(MAPS) if x.startswith('DM') or x == 'T01')
    rows = stage(out, maps)
    bats(out, rows)
    with open(os.path.join(out, 'cover3.json'), 'w') as fh:
        json.dump([{'map': m, 'slot': s, 'built_on_md5': a_, 'md5': b} for m, s, a_, b in rows], fh, indent=1)
    for r in rows:
        print('%-6s %s built on %s -> %s' % r)


if __name__ == '__main__':
    main()
