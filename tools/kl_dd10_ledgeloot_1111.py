#!/usr/bin/env python3
r"""kl_dd10_ledgeloot_1111.py - Flat Raid (DD10, slot F07): a loot stack on the balcony ledge (stage only, nothing installed).

OWNER (2026-11-11, quoted): "as i have been saying the balcony better lead to loot and that road". The road half is kl_flatledge_1108 (KLJoin [Join.2] window sill
-> ledge Jump05 (6489, 1200, 3123), [Join.3] ledge north end x 6446..6583, z 2485..2720 -> the street, landing in the exit strip). Nothing to take on the ledge.
FIX: MoneyStack_097 (node 22128, one of the THREE stacks in the top corridor at y 1602, z ~300) moves onto the ledge between the landing and the ride box,
at (6515, 1189.5, 2850). Total loot unchanged; the corridor keeps two. REF labels untouched; .prp ZGEOM + .gms record trans only (A.place), like kl_dd10_flats_1108.
MEASURED (live c392528f): collision floor y 1189.5 every 25 cm from z 3060 to 2720 at x 6515 (the check walks it); the nav mesh has a gap mid-ledge (bots never use
this route: KLJoin boxes are heister-only). GUESS: the stack draws and picks up outside its old room (the 11-08 flats moves crossed rooms the same way, not proven in a shot).
Input = the LIVE DD10 with kl_dd10_vanshow_1111 installed (F07 c392528f).

  python tools/kl_dd10_ledgeloot_1111.py stage|check [--in-dir <map dir>] [--out-root C:/kl_build_1024]
Undo: UNDO.bat (back to vanshow's files byte for byte)."""
import os, struct, sys, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dd10_vanfix_1111 as V1
import kl_gms

STACK = V1.R + 'FASpecials!DropMoney!MoneyStack_097'      # node 22128
OLD_AT = (12870, 1602, 280)                               # rounded
NEW_AT = (6515.0, 1189.5, 2850.0)
LEDGE_X, LEDGE_Z = 6515.0, (2720.0, 3060.0)              # landing side 3060 (Jump05 snap), ride box edge 2720
PARTS_ALL = ('ledge',)
LIVE_MD5 = {V1.ZIP: 'c392528f7271b842cf3ab33d4604dbfe', V1.BOTS: 'efdc5acd228586edf378e6b6e7352f06', V1.BASE: ''}   # BASE filled from the live file in main()
NAME, TAG = 'dd10ledgeloot_1111', '.before-dd10ledgeloot_1111'


def edit_scene(B, parts=PARTS_ALL, log=print):
    sc = B.sc
    k = V1.A.node_of(sc, STACK)
    at = tuple(round(v) for v in B.at(k))
    if at != OLD_AT:
        raise SystemExit('REFUSED: %s is at %r, expected %r' % (STACK, at, OLD_AT))
    V1.A.place(types.SimpleNamespace(prp=sc, ents=B.ents), k, NEW_AT)
    log('  loot node %d: %s -> %s (balcony ledge)' % (k, at, NEW_AT))
    return [k]


def patch_zip(src, dst, parts=PARTS_ALL, log=print):
    B = V1.F.Built(src)
    edit_scene(B, parts, log)
    gms, buf = B.scene.write()
    if buf != B.files[B.ext['.buf']]:
        raise SystemExit('REFUSED: scene.write() does not reproduce the .buf')
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    new[B.ext['.gms']] = kl_gms.pack(gms)
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    V1.SK.write_zip(dst, [(n, new[n]) for n in order], V1.SK.tex_level(src))


README = """DD10 LEDGE LOOT 1111 (Flat Raid, slot F07) - a loot stack on the balcony ledge. (recommended on)
On top of kl_dd10_vanshow_1111 (live F07 c392528f). MoneyStack_097 moves from the top corridor to the ledge (6515, 1189.5, 2850). Parts: %(parts)s.
Staged md5: zip %(zip)s bots %(bots)s base %(base)s. INSTALL.bat installs (refuses unless the live files are vanshow's), UNDO.bat puts them back.
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
    import kl_dd10_flats_1108 as FL
    FL._import()
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
        k = V1.A.node_of(Bs.sc, STACK)
        need(tuple(round(v, 1) for v in Bs.at(k)) == NEW_AT, '%s: stack at %s' % (n, tuple(round(v, 1) for v in Bs.at(k))))
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or Bb.sc.nodes[j]['ctrls'] != Bs.sc.nodes[j]['ctrls']]
        need(diffn == [k], '%s: exactly node %d differs in the .prp (got %s)' % (n, k, diffn))
        de = [j for j in range(len(Bb.ents)) if (Bb.ents[j].trans, Bb.ents[j].rot, Bb.ents[j].flags) != (Bs.ents[j].trans, Bs.ents[j].rot, Bs.ents[j].flags)]
        need(de == [k - 1] and Bs.ents[k - 1].trans[:12] == struct.pack('<3f', *NEW_AT), '%s: exactly its .gms record moved (got %s)' % (n, de))
    G = FL.ME.Ground(FL.ME.Level(os.path.join(out, V1.ZIP)))
    zs = [LEDGE_Z[0] + 25.0 * i for i in range(int((LEDGE_Z[1] - LEDGE_Z[0]) / 25.0) + 1)]
    gaps = [z for z in zs if (lambda y: y is None or abs(y - NEW_AT[1]) > 15.0)(FL.floor_at(G, LEDGE_X, NEW_AT[1], z))]
    need(not gaps, 'ledge floor y %.1f +-15 at x %.0f every 25 cm z %.0f..%.0f (gaps at %s)' % (NEW_AT[1], LEDGE_X, LEDGE_Z[0], LEDGE_Z[1], gaps))
    y = FL.floor_at(G, NEW_AT[0], NEW_AT[1], NEW_AT[2])
    need(y is not None and abs(y - NEW_AT[1]) <= FL.FLOOR_TOL, 'stack stands on the floor (floor %s)' % y)
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
