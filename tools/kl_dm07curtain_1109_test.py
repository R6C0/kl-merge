"""Off-game self-test of tools/kl_dm07curtain_1109.py: stages the curtain from the pinned live DM07 zips into a temp dir and audits it (skips when not pinned)."""
import os, sys, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07curtain_1109 as T


def main():
    for n, h in T.LIVE_MD5.items():
        p = os.path.join(T.LIVE_DIR, n)
        if not os.path.isfile(p) or T.md5(p) != h:
            print('SKIP: pinned live DM07 files not present'); return 0
    out = tempfile.mkdtemp(prefix='curtain_test_', dir='C:/kl_build_1024')
    try:
        files = T.stage(out=out, log=lambda s: None)
        assert len(files) == 3 and all(a != b for _n, a, b in files)
        for n in T.ZIPS:
            d = T.crc_compare(os.path.join(T.LIVE_DIR, n), os.path.join(out, n), log=lambda s: None)
            assert d and all(m.lower().endswith(('.prp', '.gms', '.buf')) for m in d), d
            assert T.check(os.path.join(out, n))
        assert open(os.path.join(out, 'F06_Main.bots.base.md5')).read().strip() == T.md5(os.path.join(out, 'F06_Main.zip'))
        assert T.check(os.path.join(T.LIVE_DIR, 'F06_Main.zip')) is False      # the stock zip has no curtain
        src = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
        compile(src, 'install.py', 'exec')
        assert T.TAG in src and 'dm07sink' not in src
        assert T.CENTRE == (-4640.0, 700.0, 10395.0) and T.HALF == (80.0, 400.0, 405.0)
    finally:
        shutil.rmtree(out, ignore_errors=True)
    print('OK: kl_dm07curtain_1109')
    return 0


if __name__ == '__main__':
    sys.exit(main())
