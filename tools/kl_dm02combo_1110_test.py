r"""Self-test of kl_dm02combo_1110: light checks, and --rehearse <stage> [--tmp dir]: install / 2nd install refused / dry / undo byte-exact on a scratch copy of the live DM02 files."""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm02combo_1110 as C


def md5(p):
    return C.md5(p)


def light():
    src = C.make_install_py({'full': {'a': '1'}, 'nodress': {'a': '2'}})
    compile(src, 'install.py', 'exec')
    assert C.LIVE_PIN in src and C.TAG in src and '@' not in src.replace('@@', '')
    assert C._shop_of(b'KLDress3_x') == 3 and C._shop_of(b'KLShop05_desk') == 5 and C._shop_of(b'Plant') is None
    assert set(C.SHOP_ROOM) == {1, 2, 3, 4, 5} and C.DEFAULT_GLASS_DELAY == 60.0
    print('light: PASS')


def run(py, args):
    r = subprocess.run([sys.executable, py] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rehearse(stage, tmp, variant):
    live = C.MAPDIR
    game = os.path.join(tmp, 'game')
    d = os.path.join(game, 'KLExpansion', 'Maps', 'DM02')
    os.makedirs(d, exist_ok=True)
    names = ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')
    for n in names:
        shutil.copyfile(os.path.join(live, n), os.path.join(d, n))
    before = {n: md5(os.path.join(d, n)) for n in names}
    # run from a copy of the stage folder so installed.json stays out of the real stage
    st = os.path.join(tmp, 'stage')
    shutil.copytree(stage, st, ignore=shutil.ignore_patterns('variant_*') if False else None)
    py = os.path.join(st, 'install.py')
    base = ['--game', game, '--skip-run-check', '--variant', variant]
    rc, o = run(py, base + ['--dry'])
    assert rc == 0 and all(before[n] == md5(os.path.join(d, n)) for n in names), o
    rc, o = run(py, base)
    assert rc == 0, o
    new = {n: md5(os.path.join(d, n)) for n in names}
    assert new['F02_Main.zip'] == md5(os.path.join(st, 'variant_' + variant, 'F02_Main.zip')) != before['F02_Main.zip']
    assert all(os.path.isfile(os.path.join(d, n + C.TAG)) for n in names)
    rc, o = run(py, base)
    assert rc == 1 and 'REFUSED' in o and all(new[n] == md5(os.path.join(d, n)) for n in names), o
    rc, o = run(py, ['--game', game, '--skip-run-check', '--undo', '--dry'])
    assert rc == 0 and all(new[n] == md5(os.path.join(d, n)) for n in names), o
    rc, o = run(py, ['--game', game, '--skip-run-check', '--undo'])
    assert rc == 0, o
    assert all(before[n] == md5(os.path.join(d, n)) for n in names), 'undo not byte-exact'
    assert not any(os.path.exists(os.path.join(d, n + C.TAG)) for n in names)
    print('rehearsal %s: PASS (install, 2nd install refused, dry writes nothing, undo byte-exact)' % variant)


if __name__ == '__main__':
    light()
    a = sys.argv[1:]
    if '--rehearse' in a:
        stage = a[a.index('--rehearse') + 1]
        tmp = a[a.index('--tmp') + 1] if '--tmp' in a else r'C:\kl_build_1024\scratch_dm02combo'
        for v in C.VARIANTS:
            t = os.path.join(tmp, v)
            shutil.rmtree(t, ignore_errors=True)
            os.makedirs(t)
            rehearse(stage, t, v)
