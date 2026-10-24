"""kl_doors2_stage.py - stage the 2026-10-25 'doors2' kick-door / extinguisher rebuild of five maps with md5-chained INSTALL/UNDO.

    python kl_doors2_stage.py <build folder with out/>   writes <build folder>/<MAP>/{F0x_Main.zip, doors2.json, doors2.ps1, INSTALL doors2.bat, UNDO doors2.bat}
                                                         and rehearses every installer on a scratch game folder (never the real one)

The installer is the one of kl_dm01b_gas_1025 (whole-zip replace, refuses while kl2.exe runs or when the live md5 is not `old`, read-back,
undo only on the new md5 and byte-identical) with the backup suffix .before-1025doors2. `old` per map = the md5 the build was chained on:
DM01 live 3f503f58, DM01B the STAGED gas build 119c9cd2 (install dm01bgas first), DM03A the STAGED swat build 7852abd9 (install dm03aswat
first), DM06 live 38b20312, DM09 live 99a4ff75. The real game folder is only READ here (the rehearsal copies the old zips to scratch)."""
import hashlib, json, os, shutil, subprocess, sys

TAG = '.before-1025doors2'
GAME = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
MAPS = {   # map: (slot file, built file, where the `old` zip is read from, old md5)
    'DM01': ('F01_Main.zip', 'DM01_F01_Main.zip', GAME + '/KLExpansion/Maps/DM01/F01_Main.zip', '3f5e'),
    'DM01B': ('F03_Main.zip', 'DM01B_F03_Main.zip', 'C:/kl_build_1024/dm01bgas_1025a/F03_Main.zip', '119c9cd2'),
    'DM03A': ('F07_Main.zip', 'DM03A_F07_Main.zip', 'C:/kl_build_1024/dm03aswat_1025a/F07_Main.zip', '7852abd9'),
    'DM06': ('F04_Main.zip', 'DM06_F04_Main.zip', GAME + '/KLExpansion/Maps/DM06/F04_Main.zip', '38b20312'),
    'DM09': ('F06_Main.zip', 'DM09_F06_Main.zip', GAME + '/KLExpansion/Maps/DM09/F06_Main.zip', '99a4ff75'),
}
MAPS['DM01'] = MAPS['DM01'][:3] + ('3f503f58',)


def md5f(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def ps_text():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kl_dm01b_gas_1025 as G
    s = G.PS1
    s = s.replace('gas.json', 'doors2.json').replace('.before-1025dm01bgas', TAG).replace('gas.ps1', 'doors2.ps1')
    first = s.index('\n')
    s = ('# doors2.ps1 - one map, 2026-10-25 (tools/kl_interact_graft.py, kl_doors2_stage.py): VISIBLE kick doors that can be reached (leaf and group in the dynamic\n'
         '#   pool like the stock door, doors only on the main walk-mesh part) and fire extinguishers on the wall beside the door exits.\n'
         '#   Chained: `old` in doors2.json is the md5 of the build this one was made on (see doors2.json "chain"); install that first.\n') + s[first + 1:]
    return s


def stage(build, log=print):
    ps = ps_text()
    report = {}
    for m, (slot, built, oldsrc, oldpre) in MAPS.items():
        d = os.path.join(build, m)
        os.makedirs(d, exist_ok=True)
        new_src = os.path.join(build, 'out', built)
        old = md5f(oldsrc)
        assert old.startswith(oldpre), (m, old, oldpre)
        shutil.copy2(new_src, os.path.join(d, slot))
        new = md5f(os.path.join(d, slot))
        chain = {'DM01B': 'dm01bgas_1025a (gas.ps1)', 'DM03A': 'dm03aswat_1025a (swat.ps1)'}.get(m, 'the live file')
        json.dump(dict(m=m, f=slot, old=old, new=new, tag=TAG, chain=chain), open(os.path.join(d, 'doors2.json'), 'w'), indent=1)
        with open(os.path.join(d, 'doors2.ps1'), 'w', newline='\r\n') as fh:
            fh.write(ps)
        for nm, arg in (('INSTALL doors2.bat', ''), ('UNDO doors2.bat', '-Undo')):
            with open(os.path.join(d, nm), 'w', newline='') as fh:
                fh.write('@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0doors2.ps1" ' + arg + '\r\npause\r\n')
        log('%s: old %s -> new %s' % (m, old[:8], new[:8]))
        report[m] = rehearse(d, oldsrc, dict(m=m, f=slot, old=old, new=new), os.path.join(build, 'scratch'), log)
    return report


def run(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'doors2.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def rehearse(d, oldsrc, man, scratch, log):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'game_' + man['m'])
    live = os.path.join(g, 'KLExpansion', 'Maps', man['m'], man['f'])
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
    return 'ok'


if __name__ == '__main__':
    print(stage(sys.argv[1]))
