#!/usr/bin/env python3
"""kl_club_lastcall.py - Last Call (DM05A) pass 1024n: the helicopter escape camera (the GRAY escape screen). OFFLINE.

  python tools/kl_club_lastcall.py build <in F01_Main.zip> <out F01_Main.zip> [--force] [--cam-up N] [--cam-east N]
  python tools/kl_club_lastcall.py check <zip>        where the three camera nodes are, and how far from the pad

Input zip -> output zip, rerunnable: a zip that already has the cameras at the target is copied through unchanged
(idempotent); an input whose md5 is not one of KNOWN_IN is refused unless --force. Only the .prp and the .gms/.buf entity
places change (the same members as any node move, e.g. kl_old_waves.move_rings); no entity is added, so .oct/.rmi/.rmc
(slot ids) are untouched. Chain-safe: it edits three nodes by NAME.

WHY GRAY (found 2026-10-24 in the live DM05A, 257c7445; STATIC EVIDENCE, NOT RUN IN THE GAME)
  kl_fa_club.heli_place moves the chopper set to the pad (-2900, 859, 3900) with one rigid motion, but the escape CAMERA nodes
  ended up far from the pad:
      EscCameraLAST   (0, 0, 0)                      the world origin, below the floor
      EscCamera01     (-5758, 859, 9864)             6.0 km from the pad
      CamPos01        (-5512, 2678, 9584)            6.0 km from the pad
      CameraTrigger01 (-2825, 1038, 3504)            fine (1000 half box over the roof)
  The escape camera (CCameraBox eFMM_LookFromPosFA: look FROM the position object AT the player) is switched on when the
  crew boards; a camera that stands outside every room volume renders nothing, which is a gray screen. All three
  positions are outside the map. (GUESS: the donor offsets were applied without subtracting the donor landing point; the
  exact cause of the offset is not needed for the cure.)
CURE: CamPos01, EscCamera01 and EscCameraLAST go to (pad.x + CAM_EAST, pad.y + CAM_UP, pad.z), inside the exit box
  (x -3600..-2200, y 809..1309, z 3400..4400), 5 m east / 4 m above the landing. Rotation is irrelevant for LookFromPos.
GUESSES (said plainly): the spot is free air above the roof (not checked against geometry); the cause of the gray screen is the
  camera position and not the 'FAEscCameraLAST' ZSetZDefine, which exists in no stock FA map and is NOT touched here.
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

PAD = (-2900.0, 859.0, 3900.0)          # kl_fa_club.HELI_PAD
CAM_EAST, CAM_UP = 500.0, 390.0         # GUESS (see the docstring)
CAMS = ('EscCameraSetup!CamPos01', 'EscCameraSetup!EscCamera01', 'EscCameraSetup!EscCameraLAST')
# live DM05A after club_1024d + blowup_1024d (2026-10-24). Anything else needs --force (other passes may have been chained first).
KNOWN_IN = ('257c7445',)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def target(up=CAM_UP, east=CAM_EAST):
    return (PAD[0] + east, PAD[1] + up, PAD[2])


def positions(B):
    out = {}
    for n in CAMS:
        k = A.node_of(B.sc, n)
        lab = J.labels('dd', B.sc.cls(k))
        out[n] = (k, tuple(float(x) for x in kl_fa.node_values(B.sc, k)[lab.index('ZGEOM[2]')]))
    return out


def check(zp, log=print):
    B = F.Built(zp)
    import math
    for n, (k, p) in positions(B).items():
        log('%-32s node %d  (%.0f, %.0f, %.0f)  %.0f from the pad' % (n, k, *p, math.dist(p, PAD)))
    return 0


def build(src, dst, force=False, up=CAM_UP, east=CAM_EAST, log=print):
    h = md5(src)
    if not force and not any(h.startswith(k) for k in KNOWN_IN):
        raise SystemExit('refusing: %s md5 %s is not one of %s (use --force if other passes were chained first)' % (src, h, KNOWN_IN))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    B = F.Built(src)
    tgt = target(up, east)
    pos = positions(B)
    todo = [n for n, (k, p) in pos.items() if max(abs(p[i] - tgt[i]) for i in range(3)) > 0.5]
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if not todo:
        shutil.copyfile(src, dst)
        log('already at the target: copied unchanged')
        return 0
    sc = B.sc
    import kl_graft
    for n in todo:
        k, old = pos[n]
        par = sc.parent[k]
        if par > 0:
            raise SystemExit('%s has a parent node: a world position is not its place (refusing)' % n)
        lab = J.labels('dd', sc.cls(k))
        kl_fa.edit(sc, k, None, lambda us, lab=lab: A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in tgt]))
        e = B.ents[k - 1]
        e.trans = struct.pack('<3f', *tgt) + e.trans[12:]
        log('  %s: (%.0f, %.0f, %.0f) -> (%.0f, %.0f, %.0f)' % (n, *old, *tgt))
    prp = sc.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
        raise SystemExit('the new .prp does not round-trip')
    gms, buf = B.scene.write()
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    log('written %s md5 %s' % (dst, md5(dst)))
    return 0


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2

    def opt(flag, default):
        if flag in a:
            i = a.index(flag)
            v = float(a[i + 1])
            del a[i:i + 2]
            return v
        return default
    force = '--force' in a
    if force:
        a.remove('--force')
    up, east = opt('--cam-up', CAM_UP), opt('--cam-east', CAM_EAST)
    if a[0] == 'check':
        return check(a[1])
    if a[0] == 'build' and len(a) == 3:
        return build(a[1], a[2], force, up, east)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
