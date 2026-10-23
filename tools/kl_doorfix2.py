#!/usr/bin/env python3
r"""
Escape-lift doors, TEST VARIANT (Retomoto Tower, 2026-10-23): ALSO send the two MatPosAnimProxy nodes the message from a
sender known to work, the BLAST TIMER (Gameplay!010_FirstFight!RivalMercVan!Timer, TriggerDelay2, field 0 = 16.5 s after
the round-start event, field 4 = the list it fires). The 10-09 build opened the doorway that way (re/campaign_fa.md G1.9).
The doors then open at the blast: fine for a test, NOT the design (the design is the TriggerBox_OpenExitElevator beat).

    python kl_doorfix2.py check <F06_Main.zip>              -> blast timer list, proxies in it or not (exit 1 if odd)
    python kl_doorfix2.py apply <in F06_Main.zip> <out F06_Main.zip>
        Only the *_Main.prp member is rewritten (byte-exact re-serialize checked first); every other member is copied RAW.
        Refuses a timer that is not [float, ..., list] TriggerDelay2 with the expected layout; an archive whose proxies
        are already in the timer list is copied as is.
    python kl_doorfix2.py diff <in> <out>                   -> before/after of the changed list + member byte comparison
"""
import hashlib, os, shutil, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa, kl_doorfix
import kl_fa_author as A
from kl_prp import units

R = 'ROOT\\'
TIMER = A.ROLE['blast timer']
CTRL = 'TriggerDelay2'


def _timer(sc):
    k = A.node_of(sc, TIMER)
    i = A.ctrl_of(sc, k, CTRL)
    v = [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][i][1][1:-1])]
    if len(v) != 5 or not isinstance(v[0], float) or not isinstance(v[4], list):
        raise ValueError('blast timer: not the expected 5-field TriggerDelay2 form: %s' % (v,))
    return k, i, v


def _proxy_paths(sc):
    out = []
    for n in kl_doorfix.PROXIES:
        hit = sc.resolve(R + n)
        if len(hit) != 1:
            raise ValueError('%s: %d nodes (expected 1)' % (n, len(hit)))
        out.append(R + n)
    return out


def fix_scene(sc, log=print):
    """Append both proxies to the blast timer's list. Returns the number added (0 = already there)."""
    k, i, v = _timer(sc)
    want = _proxy_paths(sc)
    add = [p for p in want if p not in v[4]]
    if not add:
        log('  kl_doorfix2: the blast timer already names both proxies')
        return 0
    for s in v[4]:
        if not sc.resolve(s):
            raise ValueError('blast timer entry %s does not resolve; refusing' % s)
    kl_fa.edit(sc, k, i, lambda us: A.setv(sc, us, 4, list(v[4]) + add))
    log('  kl_doorfix2: blast timer (%.1f s) list %d -> %d entries' % (v[0], len(v[4]), len(v[4]) + len(add)))
    return len(add)


def apply(src, dst, log=print):
    sc, _s, _l = kl_fa.load(src)
    with zipfile.ZipFile(src) as zf:
        prp_name = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        old = zf.read(prp_name)
    if sc.p.serialize() != old:
        raise ValueError('%s: the .prp does not re-serialize byte for byte; refusing' % src)
    if not fix_scene(sc, log):
        shutil.copyfile(src, dst)
        return False
    data = sc.p.serialize()
    if os.path.exists(dst):
        os.remove(dst)
    with zipfile.ZipFile(src) as zin, open(src, 'rb') as sfp, zipfile.ZipFile(dst, 'w') as zout:
        for zi in zin.infolist():
            if zi.filename == prp_name:
                ni = zipfile.ZipInfo(zi.filename, zi.date_time)
                ni.compress_type, ni.external_attr, ni.create_system = zi.compress_type, zi.external_attr, zi.create_system
                ni.comment, ni.extra = zi.comment, zi.extra
                zout.writestr(ni, data)
            else:
                kl_doorfix._raw_copy(sfp, zi, zout)
    # verify: the new archive re-serializes and holds the entries
    sc2, _s, _l = kl_fa.load(dst)
    if sc2.p.serialize() != data:
        raise ValueError('output .prp does not re-serialize byte for byte')
    return True


def timer_list(path):
    sc, _s, _l = kl_fa.load(path)
    _k, _i, v = _timer(sc)
    return v[0], v[4]


def diff(a, b):
    ta, la = timer_list(a)
    tb, lb = timer_list(b)
    print('blast timer delay: %.1f -> %.1f' % (ta, tb))
    print('before (%d):' % len(la))
    for s in la:
        print('   ' + s)
    print('after (%d):' % len(lb))
    for s in lb:
        print('   %s%s' % (s, '   <-- ADDED' if s not in la else ''))
    ok = lb[:len(la)] == la and set(lb) - set(la) == set(R + n for n in kl_doorfix.PROXIES)
    print('only the two proxies added, old entries unchanged: %s' % ok)
    ma, mb = kl_doorfix.sha1_members(a), kl_doorfix.sha1_members(b)
    names_a, names_b = [m[0] for m in ma], [m[0] for m in mb]
    print('member names/order identical: %s (%d members)' % (names_a == names_b, len(ma)))
    changed = [x[0] for x, y in zip(ma, mb) if x != y]
    print('members whose bytes differ: %s' % changed)
    return ok and names_a == names_b and len(changed) == 1 and changed[0].lower().endswith('_main.prp')


def main(a):
    if len(a) == 2 and a[0] == 'check':
        sc, _s, _l = kl_fa.load(a[1])
        _k, _i, v = _timer(sc)
        ps = _proxy_paths(sc)
        print('blast timer %.1f s, %d entries; proxies in list: %s' % (v[0], len(v[4]), [p in v[4] for p in ps]))
        return 0
    if len(a) == 3 and a[0] == 'apply':
        print('changed' if apply(a[1], a[2]) else 'already fixed (copied)')
        return 0
    if len(a) == 3 and a[0] == 'diff':
        return 0 if diff(a[1], a[2]) else 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
