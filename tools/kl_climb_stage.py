#!/usr/bin/env python3
r"""
STAGE 'climb3' (2026-10-24 18:00): the free climb ([Climb], luvsic's, klhook\klfreeclimb.c) plays ONLY where the level's .ANM has
the slots /Movement/Climb/Up/Low|Medium|High (+ Sprint_Low). Measured on the live zips (tools\kl_fa_climb.py read_anm): the 9 stock
Dog Days FA copies (KLExpansion\Maps\DD01..DD09) and the Dead Men maps DM01B, DM05A, DM06B, DM11B have NONE; DM01, DM02, DM03,
DM03A, DM06, DM09 (+ its Retomoto variants) and T01 have them. The hook is not the limit (it is not gated to a level) - the clips
are. This stage adds them with kl_fa_climb.apply (players-only, no [Climb] sections: the free climb needs no level data), per map:
  - the 9 DD maps and any other map lacking them: built on the CURRENTLY LIVE zip;
  - DM01B, DM05A, DM06B, DM11B also get cover3 (kl_cover3_stage.py): built on the cover3 zip (<cover3 folder>\<map>\...), so the
    INSTALL asks for cover3 first (it refuses with that message when the live zip is not the cover3 one).
Only the .ANM member differs from its source (kl_fa_climb.apply proves it, and this tool checks the md5 of the source).
OFFLINE: reads the game folder, writes ONLY <out>. Never installs.

    python kl_climb_stage.py <out folder> <cover3 folder> [MAP ...]
"""
import glob, hashlib, json, os, shutil, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm, kl_fa_climb as K

MAPS = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def lacks(zp):
    n, raw = K.read_anm(zp)
    a = kl_anm.Anm(raw)
    return not any(s in a.slots for s in K.SLOTS)


def stage(out, c3, maps):
    rows = []
    for m in maps:
        zs = glob.glob(os.path.join(MAPS, m, '*_Main.zip'))
        if len(zs) != 1:
            print(m, 'skipped (%d level zips)' % len(zs))
            continue
        live = zs[0]
        src, base = live, md5(live)
        staged3 = os.path.join(c3, m, os.path.basename(live))
        need3 = os.path.isfile(staged3)
        if need3:
            src = staged3
        if not lacks(src):
            print(m, 'has the climb slots already: skipped')
            continue
        tmp = tempfile.mkdtemp(prefix='climb_')
        try:
            shutil.copyfile(src, os.path.join(tmp, os.path.basename(live)))
            dst = os.path.join(out, m)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            rep = K.apply(tmp, dst, players_only=True, edges=False, log=lambda s='': None)
            res = [r for r in rep['check'] if r[0] == 'FAIL']
            if res:
                raise ValueError('%s: check FAIL %s' % (m, res))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        for x in os.listdir(dst):                          # the zip only: climb.json / climb.txt are reports, kept beside
            pass
        f = os.path.join(dst, os.path.basename(live))
        rows.append((m, os.path.basename(live).split('_Main')[0], md5(src), md5(f), 'cover3' if need3 else 'live'))
        print('%-6s %s built on %s (%s) -> %s' % (m, rows[-1][1], rows[-1][2], rows[-1][4], rows[-1][3]))
    return rows


def bats(out, rows):
    head = ('@echo off\nrem climb3 (2026-10-24): %s\nrem Per map: refused unless the live zip is exactly the one this was built on (md5); the live zip is MOVED to '
            '.before-1024climb3 (never overwrites a backup, never touches other *.before-* files).\nrem NOT RUN by the agent. Undo: UNDO climb3.bat.\n'
            'setlocal\ntasklist /FI "IMAGENAME eq kl2.exe" 2>nul | find /I "kl2.exe" >nul\nif not errorlevel 1 (\n  echo REFUSED: kl2.exe is running.\n  exit /b 1\n)\n'
            'set "SRC=%%~dp0"\nset "MAPS=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Maps"\n')
    ins = head % "Dead Men's free climb clips (.ANM) for the maps that lack them: the 9 stock FA copies DD01..DD09 and DM01B DM05A DM06B DM11B (the last four AFTER cover3)."
    und = head % 'undo: the zip moved to .before-1024climb3 goes back.'
    for m, slot, a, b, how in rows:
        ins += 'call :one %s %s %s %s %s\n' % (m, slot, a, b, how)
        und += 'call :undo %s %s %s\n' % (m, slot, b)
    ins += ('echo Done. Undo: UNDO climb3.bat\nexit /b 0\n\n:one\nset "M=%~1"\nset "F=%~2"\nset "OLDMD=%~3"\nset "NEWMD=%~4"\nset "HOW=%~5"\n'
            'set "DST=%MAPS%\\%M%\\%F%_Main.zip"\nset "NEW=%SRC%%M%\\%F%_Main.zip"\n'
            'if not exist "%DST%" (echo %M%: live zip missing & goto :eof)\nif not exist "%NEW%" (echo %M%: staged zip missing & goto :eof)\n'
            'if exist "%DST%.before-1024climb3" (echo %M%: backup .before-1024climb3 already exists, skipped & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:NEW).Hash.ToLower()"\') do set "GN=%%H"\n'
            'if /I not "%GN%"=="%NEWMD%" (echo %M%: staged zip is not the verified one, skipped & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:DST).Hash.ToLower()"\') do set "GL=%%H"\n'
            'if /I "%GL%"=="%NEWMD%" (echo %M%: already installed & goto :eof)\n'
            'if /I not "%GL%"=="%OLDMD%" (echo %M%: live zip is not the one climb3 was built on ^(%HOW%, md5 %GL%^) - for cover3 maps run "INSTALL cover3.bat" first - skipped & goto :eof)\n'
            'move "%DST%" "%DST%.before-1024climb3" >nul || (echo %M%: FAILED to move & goto :eof)\n'
            'copy /Y "%NEW%" "%DST%" >nul || (echo %M%: copy FAILED, restoring & move "%DST%.before-1024climb3" "%DST%" >nul & goto :eof)\n'
            'echo %M%: installed\ngoto :eof\n')
    und += ('echo Done.\nexit /b 0\n\n:undo\nset "M=%~1"\nset "F=%~2"\nset "NEWMD=%~3"\n'
            'set "DST=%MAPS%\\%M%\\%F%_Main.zip"\nif not exist "%DST%.before-1024climb3" (echo %M%: no .before-1024climb3 backup, nothing to undo & goto :eof)\n'
            'for /f %%H in (\'powershell -NoProfile -Command "(Get-FileHash -Algorithm MD5 -LiteralPath $env:DST).Hash.ToLower()"\') do set "GL=%%H"\n'
            'if /I not "%GL%"=="%NEWMD%" (echo %M%: live zip is not the climb3 one ^(md5 %GL%^), skipped - something newer was installed & goto :eof)\n'
            'del "%DST%" || (echo %M%: FAILED to remove & goto :eof)\n'
            'move "%DST%.before-1024climb3" "%DST%" >nul || (echo %M%: FAILED to move back & goto :eof)\n'
            'echo %M%: restored\ngoto :eof\n')
    for n, t in (('INSTALL climb3.bat', ins), ('UNDO climb3.bat', und)):
        with open(os.path.join(out, n), 'w', newline='') as fh:
            fh.write(t.replace('\n', '\r\n'))


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    out, c3 = a[0], a[1]
    maps = a[2:] or sorted(x for x in os.listdir(MAPS) if x.startswith('DD') or x.startswith('DM') or x == 'T01')
    os.makedirs(out, exist_ok=True)
    rows = stage(out, c3, maps)
    bats(out, rows)
    with open(os.path.join(out, 'climb3.json'), 'w') as fh:
        json.dump([{'map': m, 'slot': s, 'built_on_md5': a_, 'md5': b, 'built_on': h} for m, s, a_, b, h in rows], fh, indent=1)


if __name__ == '__main__':
    main()
