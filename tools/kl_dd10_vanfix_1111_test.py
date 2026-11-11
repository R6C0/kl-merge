"""Off-game self-test for tools/kl_dd10_vanfix_1111.py (no game, no zips): pins, geometry constants, install.py generation and a scratch install / refuse / undo round trip."""
import hashlib, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dd10_vanfix_1111 as D

TPL = r'''"""Installs / undoes DD10 DOOR FIX 1109 on the live DD10 files.
"""
import hashlib, os, shutil, subprocess, sys

GAME = 'C://game'
MAP, TAG = 'DD10', '.before-dd10doorfix1109'
FILES = [('F07_Main.zip', 'aa', 'bb')]


def main(a):
    return 0
'''


def check(c, msg):
    print('%s %s' % ('ok  ' if c else 'FAIL', msg))
    return 0 if c else 1


def main():
    bad = 0
    bad += check(all(len(v) == 32 for v in D.LIVE_MD5.values()) and D.LIVE_MD5[D.ZIP].startswith('e822d75d') and D.LIVE_MD5[D.BOTS].startswith('f16b4bc1')
                 and D.LIVE_MD5[D.BASE].startswith('0a1c00d0'), 'live pins are the full md5s of the 11-11 live files')
    bad += check(D.KB_HALF_NEW == [1.0, 1.0, 1.0] and D.KB_Y_NEW < D.KB_POS_OLD[1] - 400 and set(D.PARTS_ALL) == {'killbox', 'nohit'}, 'killbox goal: 1 cm box 4 m under; parts killbox,nohit')
    bad += check(len(D.HITS) == 3 and all(h.startswith(D.VAN) for h in D.HITS + [D.KILLBOX]) and D.VAN_ENT.endswith('F07_EscapeVan_01'), 'node names are the van group ones')
    bad += check(D.main(['bogus']) == 2 and D.main(['stage', '--parts', 'nope']) == 2, 'unknown command / part refused with 2')
    sm = {D.ZIP: 'a' * 32, D.BOTS: 'b' * 32, D.BASE: 'c' * 32}
    t = D.make_install(None, sm, TPL)
    bad += check("MAP, TAG = 'DD10', '.before-dd10vanfix1111'" in t and "'F07_Main.zip', '%s', '%s'" % (D.LIVE_MD5[D.ZIP], 'a' * 32) in t and 'KLJoin.ini' not in t,
                 'install.py: map, tag, three pinned rows, KLJoin.ini not pinned')
    if os.path.isfile(D.TEMPLATE):
        with tempfile.TemporaryDirectory() as tmp:
            kit, game = os.path.join(tmp, 'kit'), os.path.join(tmp, 'game')
            d = os.path.join(game, 'KLExpansion', 'Maps', 'DD10')
            os.makedirs(kit)
            os.makedirs(d)
            data = {n: n.encode() + b' live' for n in D.LIVE_MD5}
            stg = {n: n.encode() + b' staged' for n in D.LIVE_MD5}
            md = lambda b: hashlib.md5(b).hexdigest()
            sm2 = {n: md(stg[n]) for n in stg}
            live = dict(D.LIVE_MD5)
            for n in data:
                open(os.path.join(d, n), 'wb').write(data[n])
                open(os.path.join(kit, n), 'wb').write(stg[n])
                live[n] = md(data[n])
            D.LIVE_MD5.update(live)
            open(os.path.join(kit, 'install.py'), 'w', newline='\n').write(D.make_install(None, sm2))
            run = lambda *a: subprocess.run([sys.executable, os.path.join(kit, 'install.py'), '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
            bad += check(run('--dry').returncode == 0, 'scratch --dry')
            bad += check(run('--bogus').returncode == 2, 'unknown arg refused with exit 2')
            bad += check(run().returncode == 0 and all(open(os.path.join(d, n), 'rb').read() == stg[n] for n in stg), 'scratch install')
            bad += check(run().returncode != 0, 'second install refused')
            bad += check(run('--undo').returncode == 0 and all(open(os.path.join(d, n), 'rb').read() == data[n] for n in data), 'scratch undo byte exact')
    print('RESULT: %s' % ('FAIL %d' % bad if bad else 'PASS'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
