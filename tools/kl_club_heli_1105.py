#!/usr/bin/env python3
"""kl_club_heli_1105.py - Last Call (DM05A) pass 1105: the chopper must be in the world from the load, and its escape camera must look. OFFLINE.

  python tools/kl_club_heli_1105.py build <in F01_Main.zip> <out F01_Main.zip> [--force]
  python tools/kl_club_heli_1105.py check <zip>

Owner, 2026-11-05, after a real round: "last call the chopper still aint showing and screen goes grey still and u dont see the escape screen".
Input zip -> output zip, md5-pinned (KNOWN_IN; --force when other DM05A passes were chained first), idempotent (a zip that is already
right is copied through unchanged). Chain-safe: every edit is by node NAME and touches only values; no entity is added or moved, so
.oct / .rmi / .rmc / .sgd / .HVK (slot ids, placements) are untouched. Members that change: the .prp and the .gms entity flags (the .buf is
rewritten by kl_scene but must come out byte-equal; the build says if it did not).

THREE EDITS
 1. EscapeSetup!EscapeChopper\\Escape_Chopper is no longer hidden at the load: .prp ZGEOM[3] 1 -> 0 and .gms flag 0x400 cleared.
    WHY (PROVEN data difference, cause GUESS-grade but best evidence): of the builds with this Dead Men chopper the ones that FLY (DM06 'A Walk in the
    Park', DM11B Hasta in its no-hide build, 10-18 'the chopper FLIES') have the group visible; every build that did not fly (Hasta hide build, all
    Last Call builds, the owner's round of 11-05: ZHeli parked at its spline start (15394, 6942, 18351) for 391 samples while the vehicle state
    machine ran 1 -> 3 -> 5 -> 7) has it hidden at the load. kl2 0x815aa0 (the rout's init, which builds the goal and finds the ZHeli) skips
    nodes whose [ent+0x3c] bit 0x400 is set; GUESS: the group's own bit hides the ZHeli from that search too, so the rout gets no actor and a later
    ActivateGeom (the club's 30 s 'van on' timer) shows the model but does not give the rout its actor back.
 2. The round-start DeactivateGeom ('RivalMercs!DisableVisionBlocker!GeomDeactivator', in AIMonitor's round-start list) named the chopper group
    and hid it again at every round start. Its list becomes empty (stock has 100+ empty DeactivateGeom lists, e.g. the RoofGlas ones). The
    ActivateGeom 'Shutters!GeomActivator_TearGas_LEFT' that the 30 s / 25 s timers fire is left as it is: on a visible group it does nothing
    (kl2 0x4c4900 returns), and it still heals a hide that anything else does.
 3. The escape camera: CCameraBox EscCameraSetup!EscCamera01 is in mode eFMM_LookFromPosFA. In Dog Days that mode puts the eye at the BOX's own
    node and aims at field 9 (CamPos01) (kl2 0x4471a1). Pass 1024n (kl_club_lastcall.py) put the box, CamPos01 and EscCameraLAST on one point
    (7800, 2271, 3500) because it assumed LookFromPos: eye == target, no view direction (PROVEN data fault; that it IS the grey picture is a GUESS).
    The repair is the one kl_map_escape.fix_cameras made on DM06 (re/map_escape.md 1.2): field 11 -> eFMM_LookFromPos (eye = field 9, looks at the
    player). CamPos01 moves to CAM_POS: 8 m from the pad centre on the roof platform, 3 m over the floor (the one ring with floor under it and a
    clear line to the pad, found with kl_map_escape.Ground.between; see re/lastcall_heli_1105.md). EscCamera01's own node and EscCameraLAST stay.
GUESSES said plainly: the camera spot is free air above the platform (collision-checked, not looked at); the grey screen may also be the player
being carried with a chopper that was never at the pad - edit 1 is meant to cure that, so the two are tested together.
"""
import hashlib
import os
import shutil
import struct
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
GROUP = 'EscapeSetup!EscapeChopper\\Escape_Chopper'
DEACT = 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!GeomDeactivator'
CAMBOX = 'EscCameraSetup!EscCamera01'
CAMPOS = 'EscCameraSetup!CamPos01'
FROM_POS = 'eFMM_LookFromPos'
CAM_POS = (7093.0, 2181.0, 2727.0)      # pad (7300, 1881, 3500) + 8 m at 255 degrees, 3 m over the floor y 1881 (collision-checked, GUESS: free air)
KNOWN_IN = ('e9fab045',)                # the live DM05A of 2026-11-05 (SHIP round of the owner)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def state(B):
    """The facts this pass sets, read back: dict."""
    sc = B.sc
    g = A.node_of(sc, GROUP)
    d = A.node_of(sc, DEACT)
    cb = A.node_of(sc, CAMBOX)
    cp = A.node_of(sc, CAMPOS)
    out = {'group': g, 'group_zgeom3': kl_fa.node_values(sc, g)[3], 'group_flag': bool(B.ents[g - 1].flags & HIDDEN)}
    out['deact_targets'] = []
    for n, b in sc.nodes[d]['ctrls']:
        if sc.p.key(n) == 'DeactivateGeom':
            v = [kl_fa.value(sc, u) for u in kl_fa.units(b[1:-1])]
            out['deact_targets'] = list(v[1])
    for n, b in sc.nodes[cb]['ctrls']:
        if sc.p.key(n) == 'CCameraBox':
            out['cam_mode'] = kl_fa.value(sc, kl_fa.units(b[1:-1])[11])
    lab = J.labels('dd', sc.cls(cp))
    out['campos'] = tuple(float(x) for x in kl_fa.node_values(sc, cp)[lab.index('ZGEOM[2]')])
    return out


def check(zp, log=print):
    st = state(F.Built(zp))
    for k, v in st.items():
        log('%-14s %s' % (k, v))
    done = (st['group_zgeom3'] == 0 and not st['group_flag'] and not st['deact_targets']
            and st['cam_mode'] == FROM_POS and max(abs(st['campos'][i] - CAM_POS[i]) for i in range(3)) < 0.5)
    log('RESULT: %s' % ('DONE' if done else 'NOT DONE'))
    return 0


def build(src, dst, force=False, log=print):
    h = md5(src)
    if not force and not any(h.startswith(k) for k in KNOWN_IN):
        raise SystemExit('refusing: %s md5 %s is not one of %s (use --force if other passes were chained first)' % (src, h, KNOWN_IN))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    B = F.Built(src)
    sc = B.sc
    st = state(B)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    todo = []
    if st['group_zgeom3'] != 0 or st['group_flag']:
        todo.append('unhide')
    if st['deact_targets']:
        todo.append('deact')
    if st['cam_mode'] != FROM_POS:
        todo.append('mode')
    if max(abs(st['campos'][i] - CAM_POS[i]) for i in range(3)) > 0.5:
        todo.append('campos')
    if not todo:
        shutil.copyfile(src, dst)
        log('already done: copied unchanged')
        return 0
    if 'unhide' in todo:
        g = st['group']
        lab = J.labels('dd', sc.cls(g))
        kl_fa.edit(sc, g, None, lambda us: A.setv(sc, us, lab.index('ZGEOM[3]'), 0))
        B.ents[g - 1].flags &= ~HIDDEN
        log('  %s (node %d): ZGEOM[3] %s -> 0, .gms flag 0x400 cleared' % (GROUP, g, st['group_zgeom3']))
    if 'deact' in todo:
        d = A.node_of(sc, DEACT)
        ci = [i for i, (n, b) in enumerate(sc.nodes[d]['ctrls']) if sc.p.key(n) == 'DeactivateGeom'][0]
        kl_fa.edit(sc, d, ci, lambda us: us.__setitem__(1, kl_fa._refs(sc, [])))
        log('  %s: target list %s -> []' % (DEACT, st['deact_targets']))
    if 'mode' in todo:
        cb = A.node_of(sc, CAMBOX)
        ci = [i for i, (n, b) in enumerate(sc.nodes[cb]['ctrls']) if sc.p.key(n) == 'CCameraBox'][0]

        def fn(us):
            if us[11][0][0] != 0x0e:
                raise SystemExit('CCameraBox field 11 is not an enum')
            us[11] = [(0x0e, struct.pack('<I', sc.p.key_index(FROM_POS)))]
        kl_fa.edit(sc, cb, ci, fn)
        log('  %s: mode %s -> %s' % (CAMBOX, st['cam_mode'], FROM_POS))
    if 'campos' in todo:
        cp = A.node_of(sc, CAMPOS)
        if sc.parent[cp] > 0:
            raise SystemExit('%s has a parent node: a world position is not its place (refusing)' % CAMPOS)
        lab = J.labels('dd', sc.cls(cp))
        kl_fa.edit(sc, cp, None, lambda us: A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in CAM_POS]))
        e = B.ents[cp - 1]
        e.trans = struct.pack('<3f', *CAM_POS) + e.trans[12:]
        log('  %s: (%.0f, %.0f, %.0f) -> (%.0f, %.0f, %.0f)' % (CAMPOS, *st['campos'], *CAM_POS))
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
    # read back + member diff
    st2 = state(F.Built(dst))
    ok = (st2['group_zgeom3'] == 0 and not st2['group_flag'] and not st2['deact_targets'] and st2['cam_mode'] == FROM_POS)
    import zipfile
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise SystemExit('member list differs')
        diff = [x.filename for x in a.infolist() if a.read(x.filename) != b.read(x.filename)]
    log('members that differ: %s' % ', '.join(diff))
    if not ok:
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
