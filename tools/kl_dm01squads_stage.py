"""kl_dm01squads_stage.py - stage the 2026-10-25 DM01 'squads' build (kl_dm01squads_1025.py + 4 warehouse kick doors) with md5-chained INSTALL/UNDO.

    python kl_dm01squads_stage.py <new F01_Main.zip> <old F01_Main.zip> <out folder> [scratch]

`old` must be the doors2 build (md5 10359141...), which is about to be installed over live 3f503f58: install doors2 FIRST. The installer is the one of
kl_dm01b_gas_1025 (whole-zip replace, refuses while kl2.exe runs or when the live md5 is not `old`, read-back, undo only on the new md5 and byte
identical), backup suffix .before-1025dm01squads. The real game folder is never touched; the rehearsal works on a scratch copy."""
import hashlib, json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TAG = '.before-1025dm01squads'
OLD_PREFIX = '10359141'


def md5f(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def ps_text():
    import kl_dm01b_gas_1025 as G
    s = G.PS1.replace('gas.json', 'dm01squads.json').replace('.before-1025dm01bgas', TAG).replace('gas.ps1', 'dm01squads.ps1')
    first = s.index('\n')
    return ('# dm01squads.ps1 - DM01 Hot Coffee, 2026-10-25 (tools/kl_dm01squads_1025.py): shop-room holding squad (4), warehouse floor squad (8), upper-level squad (4),\n'
            '#   and four warehouse kick doors (the hall door + three across the west bay) so the hall starts shut with men inside.\n'
            '#   Chained: `old` in dm01squads.json is the doors2 build (10359141...); install doors2 first.\n') + s[first + 1:]


def run(d, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'dm01squads.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(new, old, out, scratch=None, log=print):
    om = md5f(old)
    assert om.startswith(OLD_PREFIX), (om, OLD_PREFIX)
    os.makedirs(out, exist_ok=True)
    shutil.copy2(new, os.path.join(out, 'F01_Main.zip'))
    nm = md5f(os.path.join(out, 'F01_Main.zip'))
    man = dict(m='DM01', f='F01_Main.zip', old=om, new=nm, tag=TAG, chain='doors2_1025a (doors2.ps1)')
    json.dump(man, open(os.path.join(out, 'dm01squads.json'), 'w'), indent=1)
    with open(os.path.join(out, 'dm01squads.ps1'), 'w', newline='\r\n') as fh:
        fh.write(ps_text())
    for n, arg in (('INSTALL dm01squads.bat', ''), ('UNDO dm01squads.bat', '-Undo')):
        with open(os.path.join(out, n), 'w', newline='') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dm01squads.ps1" ' + arg + '\r\npause\r\n')
    log('DM01: old %s -> new %s' % (om[:8], nm[:8]))
    rehearse(out, old, man, scratch or os.path.join(out, 'scratch'), log)
    return man


def rehearse(d, oldsrc, man, scratch, log):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'game_DM01')
    live = os.path.join(g, 'KLExpansion', 'Maps', 'DM01', man['f'])
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(oldsrc, live)
    t = run(d, g); log(t.strip()); assert 'installed' in t and md5f(live) == man['new'], t
    assert md5f(live + TAG) == man['old']
    assert 'already installed' in run(d, g)
    t = run(d, g, True); log(t.strip())
    assert md5f(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    assert 'already undone' in run(d, g, True)
    run(d, g); assert md5f(live) == man['new']
    run(d, g, True); assert md5f(live) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run(d, g); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.rmtree(g, ignore_errors=True)
    log('  rehearsal ok (install, idempotent, undo byte-identical, undo twice, reinstall, wrong md5 refused)')


if __name__ == '__main__':
    stage(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
