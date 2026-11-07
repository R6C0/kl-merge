#!/usr/bin/env python3
"""kl_dd10_vanshow_1107.py - Flat Raid (DD10 = F07) pass 1107: the escape van must be in the world from the load. OFFLINE.

  python tools/kl_dd10_vanshow_1107.py build <in zip> <out zip> [--force]
  python tools/kl_dd10_vanshow_1107.py check <zip>

Owner 2026-11-07: the burning van on Flat Raid never picks the crew up. Same family as the Last Call chopper (kl_club_heli_1105.py).
DATA FACT: the live DD10 van group EscapeVehicle_Animation_F07 is hidden at the load (.prp ZGEOM[3]=1 and .gms flag 0x400) and the
round-start DeactivateGeom 'RivalMercs!DisableVisionBlocker!GeomDeactivator' (retargeted to the van by kl_l05_layer/kl_dig_layer) hides
it again. GUESS (precedent: the chopper that never flew while hidden; kl2 0x815aa0 skips nodes with [ent+0x3c] bit 0x400): a hidden
group gives the rout no actor, so the later ActivateGeom shows the model without the rout. The ActivateGeom is left alone: on a visible
group it does nothing (kl2 0x4c4900 returns). Edits are by node NAME, values only; no entity added or moved.
Plain zip and bots zip are both built (they differ only in .prp); bots.base.md5 = md5 of the new plain zip.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as F
import kl_fa_author as A
import kl_gms
import kl_prpjoin as J
from kl_prp import Prp

HIDDEN = 0x400
GROUP_END = 'EscapeVehicle_Animation_F07'
DEACT_END = 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!GeomDeactivator'
KNOWN_IN = ('bc4d0bc3', '3cca3236')   # live DD10 plain zip, live DD10 bots zip (2026-11-07)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def find(sc, end):
    r = [k for k in range(1, len(sc.nodes)) if sc.path[k].endswith(end)]
    if len(r) != 1:
        raise SystemExit('expected one node ending %r, found %d' % (end, len(r)))
    return r[0]


def state(B):
    sc = B.sc
    g = find(sc, GROUP_END)
    d = find(sc, DEACT_END)
    out = {'group': g, 'zgeom3': kl_fa.node_values(sc, g)[3], 'flag': bool(B.ents[g - 1].flags & HIDDEN), 'deact': []}
    for n, b in sc.nodes[d]['ctrls']:
        if sc.p.key(n) == 'DeactivateGeom':
            out['deact'] = list(kl_fa.value(sc, kl_fa.units(b[1:-1])[1]))
    return out


def check(zp, log=print):
    st = state(F.Built(zp))
    for k, v in st.items():
        log('%-8s %s' % (k, v))
    done = st['zgeom3'] == 0 and not st['flag'] and not st['deact']
    log('RESULT: %s' % ('DONE' if done else 'NOT DONE'))
    return 0


def build(src, dst, force=False, log=print):
    h = md5(src)
    if not force and not any(h.startswith(k) for k in KNOWN_IN):
        raise SystemExit('refusing: %s md5 %s not in %s (--force)' % (src, h, KNOWN_IN))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    B = F.Built(src)
    sc = B.sc
    st = state(B)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if st['zgeom3'] == 0 and not st['flag'] and not st['deact']:
        shutil.copyfile(src, dst)
        log('already done: copied unchanged')
        return 0
    g = st['group']
    lab = J.labels('dd', sc.cls(g))
    kl_fa.edit(sc, g, None, lambda us: A.setv(sc, us, lab.index('ZGEOM[3]'), 0))
    B.ents[g - 1].flags &= ~HIDDEN
    log('  node %d: ZGEOM[3] %s -> 0, .gms 0x400 cleared' % (g, st['zgeom3']))
    d = find(sc, DEACT_END)
    ci = [i for i, (n, b) in enumerate(sc.nodes[d]['ctrls']) if sc.p.key(n) == 'DeactivateGeom'][0]
    kl_fa.edit(sc, d, ci, lambda us: us.__setitem__(1, kl_fa._refs(sc, [])))
    log('  deactivator targets %s -> []' % st['deact'])
    prp = sc.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
        raise SystemExit('the new .prp does not round-trip')
    gms, buf = B.scene.write()
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
    import kl_graft
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    st2 = state(F.Built(dst))
    import zipfile
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise SystemExit('member list differs')
        diff = [x.filename for x in a.infolist() if a.read(x.filename) != b.read(x.filename)]
    log('members that differ: %s' % ', '.join(diff))
    if not (st2['zgeom3'] == 0 and not st2['flag'] and not st2['deact']):
        raise SystemExit('read-back failed: %r' % st2)
    log('written %s md5 %s' % (dst, md5(dst)))
    return 0


def main():
    a = sys.argv[1:]
    force = '--force' in a
    if force:
        a.remove('--force')
    if len(a) == 2 and a[0] == 'check':
        return check(a[1])
    if len(a) == 3 and a[0] == 'build':
        return build(a[1], a[2], force)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
