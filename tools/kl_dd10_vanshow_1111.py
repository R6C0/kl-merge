#!/usr/bin/env python3
r"""kl_dd10_vanshow_1111.py - Flat Raid (DD10, slot F07): the escape van stays out of sight on the road until it is CALLED (stage only, nothing installed).

OWNER (2026-11-11, quoted): "put the spawn out here for where the van comes" -> picked "Van starts outside: the van stays out of sight on the road past the gate
and only drives in when called. It no longer appears early in the yard."
WHY: kl_dd10_vancall_1108 'hide' made node 22144 (Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn) the APPROACH box, half 800 x 300 x 450 at (8300, 200, 1100)
(x 7500..9100, z 650..1550): a heister walking into the yard shows the van (ActivateGeom 'AITrigger'), parked at its wait key (6280, 1100) beyond the gate,
long before anybody calls it. The call is otrExitLevel 22004, since kl_dd10_exitsouth_1110 the south strip half 450 x 300 x 125 at (8300, 200, 775) (MEASURED live).
FIX: the approach box gets EXACTLY the exit box (centre + half): the van is shown on the same enter edge that calls it, so it appears at its wait key past the gate
and drives in. The balcony landing (KLJoin [Join] Land 8300 0 750) is inside the strip: landing shows and calls it.
GUESS (kl_dd10_vancall_1108 GUESS 1): the drive-in runs while the group is hidden, so a show on the call frame is at worst a few undrawn frames.
Trigger fields (FA_MERCONLY, every edge, list = van on) are untouched. Changes the .prp (box values) and the .gms record trans (kept equal to the .prp as A.place does).
Input = the LIVE DD10 with kl_dd10_vanfix2_1111 installed (F07 a42a0495).

  python tools/kl_dd10_vanshow_1111.py stage|check [--in-dir <map dir>] [--out-root C:/kl_build_1024]
Undo: UNDO.bat (back to vanfix2's files byte for byte)."""
import os, struct, sys, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dd10_vanfix_1111 as V1
import kl_gms

APPROACH = V1.R + 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn'   # node 22144
EXIT_BOX = V1.R + 'Gameplay!EscapeSetup!otrExitLevel'                                 # node 22004
OLD_BOX = ((8300.0, 200.0, 1100.0), (800.0, 300.0, 450.0))
PARTS_ALL = ('show',)
LIVE_MD5 = {V1.ZIP: 'a42a0495037c318e5d30c84ab772dc2f', V1.BOTS: '068f047d580599a02f9db1ee344ebbc3', V1.BASE: ''}   # BASE filled from the live file in main()
NAME, TAG = 'dd10vanshow_1111', '.before-dd10vanshow_1111'


def box(sc, name):
    k = V1.A.node_of(sc, name)
    lab, vv = V1.J.labels('dd', sc.cls(k)), V1.kl_fa.node_values(sc, k)
    return k, tuple(vv[lab.index('ZGEOM[2]')]), tuple(vv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3))


def edit_scene(B, parts=PARTS_ALL, log=print):
    sc = B.sc
    k, at, half = box(sc, APPROACH)
    if (at, half) != OLD_BOX:
        raise SystemExit('REFUSED: approach box is %r %r, expected %r' % (at, half, OLD_BOX))
    _ke, eat, ehalf = box(sc, EXIT_BOX)
    V1.A.place(types.SimpleNamespace(prp=sc, ents=B.ents), k, eat, half=ehalf)
    log('  approach box node %d: %s half %s -> %s half %s (= otrExitLevel)' % (k, at, half, eat, ehalf))
    return [k]


def patch_zip(src, dst, parts=PARTS_ALL, log=print):
    B = V1.F.Built(src)
    edit_scene(B, parts, log)
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    new[B.ext['.gms']] = kl_gms.pack(B.scene.write()[0])
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    V1.SK.write_zip(dst, [(n, new[n]) for n in order], V1.SK.tex_level(src))


README = """DD10 VAN SHOW 1111 (Flat Raid, slot F07) - the van stays out of sight until called. (recommended on)
On top of kl_dd10_vanfix2_1111 (live F07 a42a0495). The approach box that showed the van is now exactly the exit (call) box. Parts: %(parts)s.
Staged md5: zip %(zip)s bots %(bots)s base %(base)s. INSTALL.bat installs (refuses unless the live files are vanfix2's), UNDO.bat puts them back.
"""


def _wire():
    V1._mods()
    V1.LIVE_MD5 = dict(LIVE_MD5)
    V1.NAME, V1.TAG = NAME, TAG
    V1.PARTS_ALL = PARTS_ALL
    V1.edit_scene = edit_scene
    V1.patch_zip = patch_zip
    V1.README = README


def check(in_dir, out_root, log=print):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    for n in (V1.ZIP, V1.BOTS):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order' % n)
            changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
            need(changed == ['.gms', '.prp'], '%s: only .prp + .gms differ (%s)' % (n, changed))
        Bb, Bs = V1.F.Built(base), V1.F.Built(stg)
        need(V1.F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip' % n)
        need(kl_gms.pack(Bs.scene.write()[0]) == Bs['.gms'], '%s: .gms round trip' % n)
        k, at, half = box(Bs.sc, APPROACH)
        _ke, eat, ehalf = box(Bs.sc, EXIT_BOX)
        need((at, half) == (eat, ehalf), '%s: approach box %s half %s = exit box' % (n, at, half))
        need(box(Bb.sc, EXIT_BOX) == box(Bs.sc, EXIT_BOX), '%s: exit box untouched' % n)
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or Bb.sc.nodes[j]['ctrls'] != Bs.sc.nodes[j]['ctrls']]
        need(diffn == [k], '%s: exactly node %d differs in the .prp (got %s)' % (n, k, diffn))
        de = [j for j in range(len(Bb.ents)) if (Bb.ents[j].trans, Bb.ents[j].rot, Bb.ents[j].flags) != (Bs.ents[j].trans, Bs.ents[j].rot, Bs.ents[j].flags)]
        need(de == [k - 1] and Bs.ents[k - 1].trans[:12] == struct.pack('<3f', *eat), '%s: exactly its .gms record moved (got %s)' % (n, de))
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check'):
        print(__doc__)
        return 2
    in_dir, out_root = opt('--in-dir', V1.LIVE), opt('--out-root', V1.OUT_ROOT)
    LIVE_MD5[V1.BASE] = V1.fmd5(os.path.join(in_dir, V1.BASE))
    _wire()
    if a[0] == 'stage':
        V1.stage(in_dir, out_root, PARTS_ALL)
    return 0 if check(in_dir, out_root) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
