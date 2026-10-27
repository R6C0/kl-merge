#!/usr/bin/env python3
r"""
Retomoto tower lift doors, re-arm (2026-10-27, owner: 'police still gets stuck in the lift ... closed door').
TriggerBox_OpenExitElevator (field 10 = re-arm, re/triggerbox.md) is -1 = fires ONCE. An AI heister crosses the box ~15 s before the human
(log 20:45), spends the single shot, and the human's crossing does nothing. Field 10 -> 10 (the stock van-door form: fires again 10 s later).
GUESS (not proven live): that this is why the doors looked shut; the other reading (the bot-fired play never reached the leaves) is covered
too, because the human-first order is proven to open the doors (LIFT10 / LIFT13). Cost: the leaf clips restart from frame 0 on each fire.

    python kl_lift_rearm.py check <F06_Main.zip>               -> field 10 of the box (exit 1 if the node is not as expected)
    python kl_lift_rearm.py apply <in F06_Main.zip> <out>      -> only the *_Main.prp member is rewritten (byte-exact re-serialize checked
                                                                  first), every other member copied RAW; reloads <out> and proves ONE int changed
"""
import os, shutil, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa, kl_doorfix
import kl_fa_author as A
from kl_prp import units

BOX = 'ROOT\\AI_Players!Enemies!070_Elevators!TriggerBox_OpenExitElevator'
CTRL = 'TriggerBox'
NEW = 10


def _field(sc):
    k = A.node_of(sc, BOX)
    i = A.ctrl_of(sc, k, CTRL)
    us = units(sc.nodes[k]['ctrls'][i][1][1:-1])
    v = [kl_fa.value(sc, u) for u in us]
    if len(v) != 18 or us[10][0][0] != 0x09 or v[14] != 'ECPS_FA_MERCONLY' or not isinstance(v[17], list):
        raise ValueError('TriggerBox_OpenExitElevator is not the expected 18-field form: %s' % (v,))
    return k, i, v


def apply(src, dst, log=print):
    sc, _s, _l = kl_fa.load(src)
    with zipfile.ZipFile(src) as zf:
        prp_name = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        old = zf.read(prp_name)
    if sc.p.serialize() != old:
        raise ValueError('%s: the .prp does not re-serialize byte for byte; refusing' % src)
    k, i, v = _field(sc)
    if v[10] == NEW:
        log('  kl_lift_rearm: field 10 is already %d' % NEW)
        shutil.copyfile(src, dst)
        return False
    if v[10] != 0xffffffff:
        raise ValueError('field 10 is %s, expected -1 (4294967295); refusing' % (v[10],))
    kl_fa.edit(sc, k, i, lambda us: A.setv(sc, us, 10, NEW))
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
    # verify: reload, re-serialize, and exactly one int differs
    sc2, _s, _l = kl_fa.load(dst)
    if sc2.p.serialize() != data:
        raise ValueError('output .prp does not re-serialize byte for byte')
    _k, _i, v2 = _field(sc2)
    want = list(v)
    want[10] = NEW
    if v2 != want:
        raise ValueError('after the edit the box reads %s, expected %s' % (v2, want))
    if len(data) != len(old):
        raise ValueError('the .prp changed length (%d -> %d)' % (len(old), len(data)))
    nd = sum(1 for a, b in zip(old, data) if a != b)
    log('  kl_lift_rearm: field 10 -1 -> %d; .prp %d bytes, %d byte(s) differ' % (NEW, len(data), nd))
    if nd > 4:
        raise ValueError('more than the 4 bytes of one int differ (%d)' % nd)
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member lists differ')
        for n in a.namelist():
            if n != prp_name and a.read(n) != b.read(n):
                raise ValueError('member %s differs' % n)
    return True


def main(argv):
    if len(argv) >= 3 and argv[1] == 'check':
        sc, _s, _l = kl_fa.load(argv[2])
        k, i, v = _field(sc)
        print('node %d field 10 = %s (%s)' % (k, v[10], 'fires once' if v[10] == 0xffffffff else 're-arm %s s' % v[10]))
        return 0
    if len(argv) == 4 and argv[1] == 'apply':
        print('changed' if apply(argv[2], argv[3]) else 'unchanged')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
