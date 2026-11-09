"""Off-game self-test for tools/kl_dd10_doorfix_1109.py (no game, no zips): host lists, pins, install.py generation and a scratch install / refuse / undo round trip."""
import hashlib, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dd10_doorfix_1109 as D

TPL = '''"""Installs / undoes DM03 DOOR FIX 1109 on the live DM03 files.
"""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days'
MAP, TAG = 'DM03', '.before-dm03doorfix1109'
FILES = [('F03_Main.zip', 'aa', 'bb'), ('F03_Main.bots.zip', 'cc', 'dd')]


def main():
    pass
'''


def check(c, msg):
    print('%s %s' % ('ok  ' if c else 'FAIL', msg))
    return 0 if c else 1


def main():
    bad = 0
    bad += check(len(D.REVERTED_LIVE) == 19 and not set(D.REVERTED_LIVE) & set(D.KEPT_LIVE), '19 reverted doors, none of them kept')
    bad += check(sorted(D.REVERTED_LIVE + list(D.KEPT_LIVE)) == list(range(1, 22)), 'reverted + kept = the 21 doors of the flats build')
    bad += check(len(set(D.HOSTS)) == len(D.HOSTS) and all(h in D.HOSTS for h in D.KEPT_LIVE.values()), 'HOSTS unique and hold both kept doors')
    bad += check(all(len(v) == 32 for v in D.LIVE_MD5.values()), 'live pins are full md5s')
    sm = dict(D.LIVE_MD5)
    sm[D.ZIP], sm[D.BOTS], sm[D.BASE] = 'a' * 32, 'b' * 32, 'c' * 32
    t = D.make_install(None, sm, TPL)
    bad += check("MAP, TAG = 'DD10', '.before-dd10doorfix1109'" in t and "F07_Main.zip', '%s', '%s'" % (D.LIVE_MD5[D.ZIP], 'a' * 32) in t, 'install.py: map, tag, zip row')
    bad += check('KLJoin.ini' not in t and 'F03' not in t, 'install.py: unchanged KLJoin.ini not pinned, no F03 left')
    # scratch round trip with the generated installer (tiny stand-in files; the template's logic is the dm03doorfix one, only text is substituted)
    real = open(D.TEMPLATE, encoding='utf-8').read() if os.path.isfile(D.TEMPLATE) else None
    if real is None:
        print('SKIP scratch round trip (no template %s)' % D.TEMPLATE)
    else:
        with tempfile.TemporaryDirectory() as td:
            kit, game = os.path.join(td, 'kit'), os.path.join(td, 'game')
            md = os.path.join(game, 'KLExpansion', 'Maps', 'DD10')
            os.makedirs(kit); os.makedirs(md)
            old, new = {}, {}
            for n in (D.ZIP, D.BOTS, D.BASE):
                old[n], new[n] = ('old ' + n).encode(), ('new ' + n).encode()
                open(os.path.join(md, n), 'wb').write(old[n]); open(os.path.join(kit, n), 'wb').write(new[n])
            m5 = lambda b: hashlib.md5(b).hexdigest()
            saved = dict(D.LIVE_MD5)
            for n in old:
                D.LIVE_MD5[n] = m5(old[n])
            sm = {n: m5(new[n]) for n in new}
            sm[D.JOIN] = D.LIVE_MD5[D.JOIN]
            open(os.path.join(kit, 'install.py'), 'w', newline='\n').write(D.make_install(None, sm, real))
            D.LIVE_MD5.update(saved)
            run = lambda *a: subprocess.run([sys.executable, os.path.join(kit, 'install.py'), '--root', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
            r1 = run(); bad += check(r1.returncode == 0 and all(open(os.path.join(md, n), 'rb').read() == new[n] for n in new), 'install lands the staged files')
            r2 = run(); bad += check(r2.returncode != 0 and 'REFUSED' in r2.stdout, 'second install refused')
            r3 = run('--undo'); bad += check(r3.returncode == 0 and all(open(os.path.join(md, n), 'rb').read() == old[n] for n in old), 'undo restores byte for byte')
            bad += check(not any(x.endswith(D.TAG) for x in os.listdir(md)), 'undo removes its backups')
    print('RESULT: %s' % ('PASS' if not bad else 'FAIL %d' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
