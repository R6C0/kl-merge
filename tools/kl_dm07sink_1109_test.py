"""Off-game self-test of tools/kl_dm07sink_1109.py: the HVK sink on the pinned live DM07 plain zip (skips when that zip is not the pinned one)."""
import os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07sink_1109 as T


def main():
    zp = os.path.join(T.LIVE_DIR, 'F06_Main.zip')
    if not os.path.isfile(zp) or T.md5(zp) != T.LIVE_MD5['F06_Main.zip']:
        print('SKIP: pinned live DM07 zip not present'); return 0
    with zipfile.ZipFile(zp) as z:
        raw = z.read(T.hvk_member(z))
    new, rep = T.sunk(raw)
    assert len(rep) == 13 and len(new) == len(raw) and new != raw
    nb, nf = T.audit(raw, new, rep)
    assert nf == 26 and nb <= 4 * 26, (nb, nf)
    try:                                   # a second sink of the sunk HVK must still be clean (idempotent at the float level) ...
        new2, _ = T.sunk(new)
        assert new2 == new
    except ValueError as e:                # ... or refuse; never silently write something else
        print('note: re-sink refused: %s' % e)
    try:
        T.sunk(raw[:-4096])
        raise SystemExit('FAIL: a damaged HVK was accepted')
    except (ValueError, Exception) as e:
        if isinstance(e, SystemExit):
            raise
    print('OK: kl_dm07sink_1109 (13 pieces, %d bytes / %d words differ)' % (nb, nf))
    return 0


if __name__ == '__main__':
    sys.exit(main())
