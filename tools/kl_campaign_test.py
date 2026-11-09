#!/usr/bin/env python3
"""Offline self-test of tools/kl_campaign.py: env defaults, id table, run tree + shim, schema step (git show 8466319),
install/undo round trip on a temp fake Dog Days tree, every refusal. Touches no game folder.
Exit 0 only when every check passes; the last line is RESULT: ..."""
import os, sys, json, re, shutil, tempfile, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_campaign as K

FAILS = []; N = [0]
def check(name, cond, extra=''):
    N[0] += 1
    if not cond: FAILS.append(name); print('FAIL', name, extra)

def raises(fn, text):
    try: fn()
    except SystemExit as e: return text in str(e)
    return False

def write(p, data=b'x'):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data if isinstance(data, bytes) else data.encode())

def main():
    tmp = tempfile.mkdtemp(prefix='klc_test_')
    try:
        run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('RESULT: %s (%d checks, %d failed)' % ('PASS' if not FAILS else 'FAIL ' + ','.join(FAILS), N[0], len(FAILS)))
    return 1 if FAILS else 0

def run(tmp):
    # ---- id table: matches luvsic's DM_SCENE_IDS (read from the vendored file) and the prefix rule
    src = open(os.path.join(K.VENDOR, 'tools', 'port_level.py'), encoding='utf-8').read()
    m = re.search(r'DM_SCENE_IDS=\{(.*?)\}', src, re.S)
    theirs = dict(re.findall(r"'(M\d\d_[AB])':'(M\d+B?)'", m.group(1)))
    ours = {f: i for i, (f, n) in K.LEVELS.items() for f in [K.LEVELS[i][0]]}
    check('ids: 16 levels', len(K.LEVELS) == 16 and len(theirs) == 16)
    check('ids: same folder->id map as port_level', {K.LEVELS[i][0]: i for i in K.LEVELS} == theirs)
    check('ids: prefix = folder without underscore', all(n == f.replace('_', '') for f, n in K.LEVELS.values()))
    check('ids: M07F special', 'M07F' in K.SPECIAL and K.ALL_IDS[-1] == 'M07F' and len(K.ALL_IDS) == 17)
    check('convert args', K.convert_args('M03B') == ['M03_B', 'M03B', 'M03B'] and K.convert_args('M07F') == ['M07F'])
    check('pick all', K.pick_ids('all') == K.ALL_IDS and K.pick_ids('m01, m03b') == ['M01', 'M03B'])
    check('pick bad', raises(lambda: K.pick_ids('F01'), 'unknown id'))
    check('schema commit pinned = anp_paths', ("SCHEMA_COMMIT = '%s'" % K.SCHEMA_COMMIT) in open(os.path.join(K.VENDOR, 'tools', 'anp_paths.py')).read())

    # ---- env defaults
    work = os.path.join(tmp, 'work'); out = os.path.join(tmp, 'out')
    dd = os.path.join(tmp, 'DD'); dm = os.path.join(tmp, 'DM')
    P = dict(wd=tmp, work=work, out=out, dd=dd, dm=dm)
    env, notes = K.converter_env(P, base={'PATH': 'p'})
    check('env: HUD off', env['ANP_DM_HUD'] == '0' and env['ANP_DM_FONTS'] == '0')
    check("env: DD's own menu/OSD graft stays on", env['ANP_GRAFT_MENU'] == '1' and env['ANP_GRAFT_OSD'] == '1')
    check('env: SMB fix off, klmerge = repo', env['ANP_SMB_FIX'] == '0' and env['ANP_KLMERGE'] == K.REPO)
    check('env: out is not the game', env['ANP_OUT'] == out and not out.startswith(dd))
    check('env: shim on PYTHONPATH', env['PYTHONPATH'].startswith(os.path.join(work, 'runtree', 'shim')))
    env2, n2 = K.converter_env(P, base={'ANP_DM_HUD': '1'})
    check('env: owner override wins', env2['ANP_DM_HUD'] == '1' and n2['ANP_DM_HUD'] == 'environment')

    # ---- run tree: no UI module, shim present, idempotent, union.pkl survives
    n = K.stage_runtree(work); rt = K.runtree(work)
    check('runtree: files copied', n > 50 and os.path.isfile(os.path.join(rt, 'tools', 'port_level.py')))
    for ui in ('dmhud.py', 'dmfont.py', 'anp_menu.py', 'anp_movie.py'):
        check('runtree: no ' + ui, not os.path.exists(os.path.join(rt, 'tools', ui)) and not os.path.exists(os.path.join(K.VENDOR, 'tools', ui)))
    write(os.path.join(rt, 'fxc', 'union.pkl'), b'u')
    check('runtree: 2nd stage writes nothing', K.stage_runtree(work) == 0)
    check('runtree: union.pkl kept', os.path.exists(os.path.join(rt, 'fxc', 'union.pkl')))
    r = subprocess.run([sys.executable, '-I', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import dmhud; print(dmhud.xhair_props())',
                        os.path.join(rt, 'shim')], capture_output=True, text=True)
    check('shim: xhair_props() is None', r.stdout.strip() == 'None', r.stderr)
    check('no game data vendored', not [f for d, _, fs in os.walk(K.VENDOR) for f in fs
                                        if f.lower().endswith(('.zip', '.str', '.bik', '.pkl', '.pyc', '.dll', '.exe', '.tex', '.prm'))])
    check('no vendored file over 1 MB', all(os.path.getsize(os.path.join(d, f)) < (1 << 20) for d, _, fs in os.walk(K.VENDOR) for f in fs))

    # ---- schemas through git show (needs the commit reachable; reported, not failed, in a shallow clone)
    has = subprocess.run([K.git_exe(), '-C', K.REPO, 'cat-file', '-t', K.SCHEMA_COMMIT], capture_output=True, text=True).stdout.strip() == 'commit'
    if has:
        got = K.install_schemas(work)
        check('schemas: 3 files + empty enum supplement', [g[0] for g in got] == ['schemas_dd.json', 'schemas_dm.json', 'dd_enums.json', 'dd_enums_extra.json'])
        check('schemas: valid json', all(json.load(open(os.path.join(work, 'ext', 'schemas', g[0]))) is not None for g in got))
    else:
        print('SKIP schemas: commit %s not reachable in this clone' % K.SCHEMA_COMMIT)
    check('workspace_ready reports a missing pickle', K.workspace_ready(work) != [])

    # ---- install / undo on a fake tree
    stock = os.path.join(dd, 'Scenes', 'Locations', 'F01', 'F01_Main.zip'); write(stock, b'stock-f01')
    stock_md5 = K.md5_file(stock)
    write(os.path.join(out, 'M01', 'M01_Main.zip'), b'zip-m01' * 100); write(os.path.join(out, 'M01', 'Loader_Sequence.WAV'), b'wav')
    write(os.path.join(out, 'M01', 'sub', 'x.bin'), b'sub')
    write(os.path.join(out, 'M02', 'M02_Main.zip'), b'zip-m02')
    write(os.path.join(out, 'CutScenes', 'M07', 'M07_A_Funeral.zip'), b'fun')
    idle = lambda: False
    check('install: refused while kl2.exe runs', raises(lambda: K.install_level('M01', out, dd, work, running=lambda: True), 'kl2.exe is running'))
    check('install: nothing written by the refusal', not os.path.exists(os.path.join(dd, 'Scenes', 'Locations', 'M01')))
    check('install: unbuilt id refused', raises(lambda: K.install_level('M03', out, dd, work, running=idle), 'not built'))
    check('install: stock id refused', raises(lambda: K.install_level('F01', out, dd, work, running=idle), 'unknown id'))
    man = K.install_level('M01', out, dd, work, running=idle, log=lambda s: None)
    t = os.path.join(dd, 'Scenes', 'Locations', 'M01')
    check('install: files + manifest', os.path.isfile(os.path.join(t, 'M01_Main.zip')) and os.path.isfile(os.path.join(t, 'sub', 'x.bin'))
          and os.path.isfile(os.path.join(t, K.MANIFEST)) and len(man['files']) == 3)
    check('install: undo list outside the game', os.path.isfile(os.path.join(work, 'anp_install', 'UNDO_M01.json')))
    check('install: status sees it', K.is_installed('M01', dd) and not K.is_installed('M02', dd))
    check('install: stock untouched', K.md5_file(stock) == stock_md5)
    check('install again over ours ok', K.install_level('M01', out, dd, work, running=idle, log=lambda s: None)['id'] == 'M01')
    # foreign folder
    write(os.path.join(dd, 'Scenes', 'Locations', 'M02', 'M02_Main.zip'), b'someone elses')
    check('install: foreign target refused', raises(lambda: K.install_level('M02', out, dd, work, running=idle), 'not ours'))
    check('install: foreign file kept', open(os.path.join(dd, 'Scenes', 'Locations', 'M02', 'M02_Main.zip'), 'rb').read() == b'someone elses')
    check('undo: foreign folder has no manifest -> nothing removed',
          K.undo_level('M02', dd, work, running=idle, log=lambda s: None) == ([], []) and os.path.isfile(os.path.join(dd, 'Scenes', 'Locations', 'M02', 'M02_Main.zip')))
    # edited file of ours
    write(os.path.join(t, 'Loader_Sequence.WAV'), b'edited by hand')
    check('install: edited file blocks reinstall', raises(lambda: K.install_level('M01', out, dd, work, running=idle), 'changed since'))
    check('undo: refused while running', raises(lambda: K.undo_level('M01', dd, work, running=lambda: True), 'running'))
    rem, kept = K.undo_level('M01', dd, work, running=idle, log=lambda s: None)
    check('undo: edited file kept, rest removed', kept == ['Loader_Sequence.WAV'] and len(rem) == 2
          and os.path.isfile(os.path.join(t, 'Loader_Sequence.WAV')) and os.path.isfile(os.path.join(t, K.MANIFEST)))
    write(os.path.join(t, 'Loader_Sequence.WAV'), b'wav')       # back to the original bytes
    rem, kept = K.undo_level('M01', dd, work, running=idle, log=lambda s: None)
    check('undo: finishes once the md5 matches again, folder gone', kept == [] and not os.path.exists(t))
    check('undo: stock untouched, Locations kept', K.md5_file(stock) == stock_md5 and os.path.isdir(os.path.join(dd, 'Scenes', 'Locations')))
    # funeral: creates Scenes\CutScenes\M07, undo removes the dirs it created
    K.install_level('M07F', out, dd, work, running=idle, log=lambda s: None)
    check('funeral: installed under Scenes\\CutScenes\\M07', os.path.isfile(os.path.join(dd, 'Scenes', 'CutScenes', 'M07', 'M07_A_Funeral.zip')))
    K.undo_level('M07F', dd, work, running=idle, log=lambda s: None)
    check('funeral: undo removes the dirs it made', not os.path.exists(os.path.join(dd, 'Scenes', 'CutScenes')))
    # backup guard
    bk = os.path.join(tmp, 'KL_PortBackup'); os.makedirs(bk)
    check('guard: KL_PortBackup refused', raises(lambda: K._guard_target(os.path.join(dd, 'Scenes', 'KL_PortBackup', 'x'), dd), 'KL_PortBackup'))
    check('guard: outside Scenes refused', raises(lambda: K._guard_target(os.path.join(dd, 'Other', 'x'), dd), 'not under'))
    # convert refuses an unprepared workspace / an out folder inside the game
    check('convert: needs setup', raises(lambda: K.run_convert('M01', P), 'not set up'))
    # CLI env prints
    r = subprocess.run([sys.executable, os.path.join(HERE, 'kl_campaign.py'), '--work', work, '--out', out, '--dd', dd, '--dm', dm, 'env'],
                       capture_output=True, text=True)
    check('cli env runs', r.returncode == 0 and 'ANP_DM_HUD=0' in r.stdout, r.stderr)

if __name__ == '__main__':
    sys.exit(main())
