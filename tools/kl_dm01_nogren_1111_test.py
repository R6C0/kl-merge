"""Off-game self-test for tools/kl_dm01_nogren_1111.py (no game, no zips): pickup name rule, install.py generation, and a scratch install / 2nd install
refused / dry / undo byte-exact / changed-live-refused round trip on tiny fake files (the rehearsal of the real kit runs inside `stage`)."""
import hashlib, os, subprocess, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm01_nogren_1111 as D


def check(c, msg):
    print('%s %s' % ('ok  ' if c else 'FAIL', msg))
    return 0 if c else 1


def h(b):
    return hashlib.md5(b).hexdigest()


def main():
    bad = 0
    names = ['Special!Pickups!Grenade_Frag_0%d' % i for i in (1, 2, 3)]
    bad += check(all(D.is_pickup(n) for n in names), 'the three pickup names match')
    bad += check(not any(D.is_pickup(n) for n in ('Special!Pickups!Grenade_Frag_04', 'Special!Pickups!Grenade_Frag_011', 'KL_Door_1', 'Weapon\Grenade_Fragmentation')),
                 'other names (4th pickup, longer suffix, templates, doors) do not match')
    bad += check(all(len(v) == 32 for v in D.PINS.values()) and set(D.PINS) == set(D.FILES[:2]), 'pins are full md5s of the two zips')
    tmp = tempfile.mkdtemp()
    try:
        old = {'F01_Main.zip': b'plain old', 'F01_Main.bots.zip': b'bots old', 'F01_Main.bots.base.md5': b'base old\n'}
        new = {'F01_Main.zip': b'plain new', 'F01_Main.bots.zip': b'bots new', 'F01_Main.bots.base.md5': b'base new\n'}
        kit, game = os.path.join(tmp, 'kit'), os.path.join(tmp, 'game')
        d = os.path.join(game, 'KLExpansion', 'Maps', 'DM01')
        os.makedirs(kit); os.makedirs(d)
        files = [(n, h(old[n]), h(new[n])) for n in D.FILES]
        open(os.path.join(kit, 'install.py'), 'w').write(D.render_install(files))
        for n in D.FILES:
            open(os.path.join(kit, n), 'wb').write(new[n]); open(os.path.join(d, n), 'wb').write(old[n])
        py = [sys.executable, os.path.join(kit, 'install.py'), '--game', game, '--skip-run-check']

        def run(*x):
            r = subprocess.run(py + list(x), capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr
        rd = lambda n, t='': open(os.path.join(d, n + t), 'rb').read()
        rc, t = run('--dry')
        bad += check(rc == 0 and all(rd(n) == old[n] for n in D.FILES), 'dry run writes nothing')
        rc, t = run()
        bad += check(rc == 0 and all(rd(n) == new[n] and rd(n, D.TAG) == old[n] for n in D.FILES), 'install: new live, originals kept as %s' % D.TAG)
        rc, t = run()
        bad += check(rc == 1 and 'REFUSED' in t and all(rd(n) == new[n] for n in D.FILES), 'second install refused, nothing changed')
        rc, t = run('--undo')
        bad += check(rc == 0 and all(rd(n) == old[n] and not os.path.exists(os.path.join(d, n + D.TAG)) for n in D.FILES), 'undo restores byte for byte')
        rc, t = run('--undo')
        bad += check(rc == 1, 'undo without a backup refused')
        open(os.path.join(d, D.FILES[1]), 'ab').write(b'x')
        rc, t = run()
        bad += check(rc == 1 and 'pinned' in t and rd(D.FILES[0]) == old[D.FILES[0]], 'a changed live file refuses ALL (nothing installed)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('RESULT: %s' % ('FAIL %d' % bad if bad else 'PASS'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
