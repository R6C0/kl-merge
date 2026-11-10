r"""Self-test of kl_lc_doors_1110 (Last Call front-office doors). Offline. SKIPs when the live DM05A zip / luvsic's M05 are not on this machine.
  python kl_lc_doors_1110_test.py"""
import hashlib, os, struct, sys, tempfile, zipfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_lc_doors_1110 as D

LIVE = os.path.join(D.MAPDIR, 'F01_Main.zip')
FAILS = []


def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond:
        FAILS.append(msg)


def main():
    # pure logic first (no game files needed)
    ok(D.set_int([(0x09, struct.pack('<I', 4294967295))], 30) == [(0x09, struct.pack('<I', 30))], 'set_int keeps the token type')
    ok(set(D.LEAVES.values()) == {7289, 7290, 7299, 7300} and len(set(D.LEAVES)) == 4, 'leaf map: four distinct REFs')
    src = D.INSTALL_PY % dict(tag=D.TAG, live=D.LIVE_PIN, bots=D.LIVE_BOTS_PIN, base=D.LIVE_BASE_PIN, staged=repr({'timer': {}}), default='timer', vars='timer', delay='20')
    try:
        compile(src, 'install.py', 'exec')
        ok(True, 'install.py template compiles')
    except SyntaxError as e:
        ok(False, 'install.py template: %s' % e)
    ok(D.LIVE_PIN in src and D.TAG in src, 'install.py carries the pins and the backup tag')
    if not (os.path.isfile(LIVE) and os.path.isfile(D.M05)):
        print('SKIP build tests (no live DM05A zip / M05 here)')
        print('RESULT: %s' % ('FAIL' if FAILS else 'PASS'))
        return 1 if FAILS else 0
    live = LIVE
    if D.md5(live) != D.LIVE_PIN:
        print('NOTE live DM05A zip is not the pinned %s (another layer): build tests run on it anyway' % D.LIVE_PIN)
    tmp = tempfile.mkdtemp(prefix='lcdoors_')
    try:
        for var, office in (('timer', False), ('trigger', True)):
            out = os.path.join(tmp, var)
            try:
                rep = D.build(live, out, var, 20.0, 'leaves', 'silent', office, log=lambda *a: None)
            except ValueError as e:
                if D.md5(live) != D.LIVE_PIN:
                    print('SKIP %s: live differs from the pin (%s)' % (var, e))
                    continue
                raise
            plain = os.path.join(out, 'F01_Main.zip')
            bad = D.check(plain, live, var, office)
            ok(not bad, '%s%s: check() clean %s' % (var, '+office' if office else '', bad[:2]))
            ok(rep['members_changed'] == ['F01_Main.HVK', 'F01_Main.gms', 'F01_Main.prp'], '%s: only prp / gms / HVK change' % var)
            ok(os.path.isfile(os.path.join(out, 'F01_Main.bots.zip')) and open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip() == rep['out_md5'], '%s: bots zip + base sidecar' % var)
            # negative: a zip with one leaf left buried must be refused by check()
            if var == 'timer':
                bad2 = D.check(live, live, 'timer', False)
                ok(bad2 != [], 'check() refuses the unpatched live zip (%d problems)' % len(bad2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('RESULT: %s' % ('FAIL' if FAILS else 'PASS'))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
