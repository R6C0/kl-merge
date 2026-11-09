"""Off-game self-test of tools/kl_dm07bury_1109.py: the bury edit in memory on the pinned live DM07 plain zip (skips when that zip is not the pinned one),
plus the generated install.py compiles and carries the new tag. One RESULT: line."""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07bury_1109 as T


def main():
    t = T.kit_text([('F06_Main.zip', 'a' * 32, 'b' * 32)])
    compile(t, 'install.py', 'exec')
    assert T.TAG in t and 'sink' not in t.lower() and '@' not in t.replace('@echo', ''), 'kit template'
    zp = os.path.join(T.LIVE_DIR, 'F06_Main.zip')
    if not os.path.isfile(zp) or T.md5(zp) != T.LIVE_MD5['F06_Main.zip']:
        print('RESULT: SKIP (kit template ok; pinned live DM07 zip not present)'); return 0
    import kl_fa_bots as KB, kl_gms
    B = KB.Built(zp, T.SLOT)
    prp, gms, rep = T.bury(B, log=lambda *a: None)
    gms0 = bytes(kl_gms.unpack(B.files[B.ext['.gms']]))
    assert len(gms) == len(gms0) and len(prp) == len(B.files[B.ext['.prp']])
    assert len(rep['_prp_diff']) <= 8 and len(rep['_gms_diff']) <= 10, (rep['_prp_diff'], rep['_gms_diff'])
    for name, ref in T.PANELS.items():
        r = rep[name]
        assert abs(r['new'][1] - (r['old'][1] - T.DROP)) < 1e-3 and r['new'][0] == r['old'][0] and r['new'][2] == r['old'][2]
        assert struct.unpack_from('<I', gms, r['rec'] + 28)[0] == T.NEW_FLAGS
    # a second application must refuse (panels no longer carry the hidden flags word)
    B2 = KB.Built(zp, T.SLOT)
    B2.ents[B2.sc.names.index(next(iter(T.PANELS))) - 1].flags = T.NEW_FLAGS
    try:
        T.find(B2)
        raise SystemExit('FAIL: an already-buried panel was accepted')
    except ValueError:
        pass
    print('RESULT: OK kl_dm07bury_1109 (gms %d bytes, prp %d bytes differ; HVK untouched by construction)' % (len(rep['_gms_diff']), len(rep['_prp_diff'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
