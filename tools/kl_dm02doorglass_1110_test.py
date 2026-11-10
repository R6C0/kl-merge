"""Off-game self-test of kl_dm02doorglass_1110 (light; no live files needed).
Heavy proof: python kl_dm02doorglass_1110.py stage ; python kl_dm02doorglass_1110_test.py --rehearse <stage dir> [--tmp <scratch dir>]"""
import ast, hashlib, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm02doorglass_1110 as G

fails = []


def ok(c, m):
    if not c:
        fails.append(m)
        print('FAIL', m)


def main(a):
    ok(G.DEFAULT_VARIANT in G.VARIANTS and len(G.GUESSES) >= 5, 'variants / guesses')
    ok(set(G.DEFAULT_OPEN) <= set(G.DOOR_REFS) and set(G.DEFAULT_HIDE) <= set(G.DEFAULT_OPEN), 'door sets')
    ok(G.GLASS_FLAGS | G.HIDE == 0x2205e6 and G.TAG != '.before-dm02shop1110', 'flags / own backup tag (the prompt pass uses .before-dm02shop1110)')
    ok(G.FORCE_MSG == 'ForceTriggerShotActivate' and G.DEFAULT_GLASS_DELAY > 1 and G.DEFAULT_DOOR_DELAY > 0, 'constants')
    ok(G.POSES == ('closed', 'stock') and G.DEFAULT_POSE == 'closed', 'poses')
    for r in G.GLASS:                                                 # closed pane geometry: unit rotation, tip inside the opening, a gap under the 40 cm capsule
        M, T = G.closed_pose(type('B', (), dict(fr={'e': (None, (0, 523.67, 0))}, ents=['e']))(), 1, r)
        det = M[0][0] * M[2][2] - M[0][2] * M[2][0]
        ok(abs(det - 1.0) < 1e-6 and M[1] == [0.0, 1.0, 0.0], 'closed_pose rotation %d' % r)
        ax, a0, a1 = G.OPENING[r]
        tip = G.GLASS[r][0 if ax == 0 else 1] + (M[0 if ax == 0 else 2][0] * 94.2)
        ok(a0 - 3 <= tip <= a1 + 3 and (a1 - a0) - 94.2 <= 40, 'closed pane inside opening %d (tip %.1f)' % (r, tip))
    # pane_code / wrap_list on synthetic data: a 2-box code is walked clean and returns the right terminals
    import kl_mopp
    off = struct.pack('<4f', 0.0, 0.0, 0.0, 254.0 * 65536.0 / 10.02)
    base = bytes([0x26, 0, 254, 0x27, 0, 254, 0x28, 0, 254, 0x30])    # one terminal 0 over the whole domain
    lst = G.wrap_list((off, base), [(3, ([1.0, 1.0, 1.0], [2.0, 2.0, 2.0]))])
    c = kl_mopp.Code(*lst)
    ok(3 in c.query([1.5, 1.5, 1.5]) and 0 in c.query([5.0, 5.0, 5.0]) and 3 not in c.query([5.0, 5.0, 5.0]), 'wrap_list returns the new child only inside its box')
    src = G.make_install_py({'shop': {}, 'doors': {}})
    ast.parse(src)
    ok("TAG = '.before-dm02door1110'" in src and '--undo' in src and 'never overwritten' in src and '--dry' in src and '--skip-run-check' in src and 'shop|doors' in src,
       'install.py features')
    ok(G.LIVE_PIN in src and G.LIVE_BOTS_PIN in src, 'install.py pins')
    if '--rehearse' in a:                                     # scratch install / 2nd install refused / undo byte exact on a copy of the live layout
        stage = a[a.index('--rehearse') + 1]
        base = a[a.index('--tmp') + 1] if '--tmp' in a else os.path.dirname(stage)
        tmp = tempfile.mkdtemp(prefix='dm02door_rehearse_', dir=base)
        try:
            g = os.path.join(tmp, 'game')
            d = os.path.join(g, 'KLExpansion', 'Maps', 'DM02')
            os.makedirs(d)
            for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5'):
                shutil.copyfile(os.path.join(G.MAPDIR, n), os.path.join(d, n))
            md = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
            snap = lambda: {n: md(os.path.join(d, n)) for n in os.listdir(d)}
            before = snap()
            run = lambda *x: subprocess.run([sys.executable, os.path.join(stage, 'install.py'), '--game', g, '--skip-run-check'] + list(x), capture_output=True, text=True)
            r = run('--dry'); ok(r.returncode == 0, 'dry install %s' % r.stdout[-200:])
            ok(snap() == before, 'dry wrote nothing')
            r = run(); ok(r.returncode == 0, 'install %s' % r.stdout[-300:])
            ok(snap() != before and any(n.endswith(G.TAG) for n in os.listdir(d)), 'install changed files and left .before backups')
            r = run(); ok(r.returncode == 1 and 'REFUSED' in r.stdout, '2nd install refused')
            r = run('--undo'); ok(r.returncode == 0, 'undo %s' % r.stdout[-300:])
            ok(snap() == before, 'undo byte exact (and no backups left)')
            for v in G.VARIANTS:
                r = run('--variant', v); ok(r.returncode == 0, 'install ' + v)
                r = run('--undo'); ok(r.returncode == 0, 'undo ' + v)
            ok(snap() == before, 'undo byte exact x3')
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print('PASS' if not fails else 'FAIL %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
