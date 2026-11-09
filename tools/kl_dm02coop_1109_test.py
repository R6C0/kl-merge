"""Off-game self-test of kl_dm02coop_1109 (light: no live files needed except the F07 donor, which is skipped when absent).
Heavy proof (build both variants on the live DM02 + check + scratch install/undo): python kl_dm02coop_1109.py stage ; python kl_dm02coop_1109_test.py --rehearse <stage dir>"""
import ast, hashlib, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm02coop_1109 as C

fails = []


def ok(c, m):
    if not c:
        fails.append(m)
        print('FAIL', m)


def main(a):
    I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    ok(C.quat(I3) == (0, 0, 0, 32512), 'identity quat')
    q = C.quat([[0, 0, -1], [0, 1, 0], [1, 0, 0]])           # columns (0,0,1),(0,1,0),(-1,0,0) = yaw -90 (F07 camera: (0,-22989,0,22989))
    ok(q == (0, -22989, 0, 22989), 'yaw -90 quat %s' % (q,))
    ok(C.set_int([(0x09, b'\0\0\0\0')], 82) == [(0x09, struct.pack('<I', 82))], 'set_int')
    ok(C.OPEN_FRAMES[0] == 0 and C.OPEN_FRAMES[1] > 0, 'frames')
    ok(C.DEFAULT_VARIANT in C.VARIANTS and len(C.GUESSES) >= 8, 'variants / guesses')
    src = C.INSTALL_PY % dict(tag=C.TAG, live='a' * 32, bots='b' * 32, base='c' * 32, staged=repr({'timer': {}, 'coop': {}}), default='timer')
    ast.parse(src)
    ok('--undo' in src and 'never overwritten' in src and '--dry' in src and '--skip-run-check' in src, 'install.py features')
    try:
        k = C.key_donor()
        ok(k['K'].frames == 201 and abs(k['rise'] - 290.0) < 1.0, 'F07 profile %s' % k['rise'])
        head, kbase, raw = C.put_keys(k['don'].head, k, (10.0, 20.0, 30.0), (0, 0, 0, 32512))
        ok(len(raw) == 64 and kbase % 16 == 0 and len(head) == kbase + (k['hi'] - k['lo']), 'put_keys layout')
    except Exception as e:                                    # no F07 game files on this machine
        print('SKIP donor checks:', e)
    if '--rehearse' in a:                                     # scratch install / 2nd install refused / undo byte exact on a copy of the live layout
        stage = a[a.index('--rehearse') + 1]
        live = os.path.join(C.MAPDIR)
        tmp = tempfile.mkdtemp(prefix='dm02coop_rehearse_', dir=os.path.dirname(stage))
        try:
            g = os.path.join(tmp, 'game')
            d = os.path.join(g, 'KLExpansion', 'Maps', 'DM02')
            os.makedirs(d)
            for n in C.os.listdir(live):
                if n.startswith('F02_Main.') and n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5'):
                    os.link(os.path.join(live, n), os.path.join(d, n)) if False else shutil.copyfile(os.path.join(live, n), os.path.join(d, n))
            md = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
            before = {n: md(os.path.join(d, n)) for n in os.listdir(d)}
            run = lambda *x: subprocess.run([sys.executable, os.path.join(stage, 'install.py'), '--game', g, '--skip-run-check'] + list(x), capture_output=True, text=True)
            r = run('--dry'); ok(r.returncode == 0, 'dry install %s' % r.stdout[-200:])
            ok({n: md(os.path.join(d, n)) for n in os.listdir(d)} == before, 'dry wrote nothing')
            r = run(); ok(r.returncode == 0, 'install %s' % r.stdout[-300:])
            r = run(); ok(r.returncode == 1 and 'REFUSED' in r.stdout, '2nd install refused')
            r = run('--undo'); ok(r.returncode == 0, 'undo %s' % r.stdout[-300:])
            ok({n: md(os.path.join(d, n)) for n in os.listdir(d)} == before, 'undo byte exact (and no backups left)')
            for v in ('timer', 'coop'):
                r = run('--variant', v); ok(r.returncode == 0, 'install ' + v)
                r = run('--undo'); ok(r.returncode == 0, 'undo ' + v)
            ok({n: md(os.path.join(d, n)) for n in os.listdir(d)} == before, 'undo byte exact x3')
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print('PASS' if not fails else 'FAIL %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
