#!/usr/bin/env python3
r"""kl_dd10_exitsouth_1110.py - Flat Raid (DD10 = Dog Days L05 in slot F07): shrink the exit box to its SOUTH strip so a heister who waits for the van is not run over by it.
Stage built from the LIVE files (2026-11-10, offline, stage only; nothing is installed, no game is launched).

Why (bench dd10call1109 / dd10side1109): Gameplay!EscapeSetup!otrExitLevel (OnlineExitLevelTrigger, field 2 = the van group) is centre (8300, 200, 1100), half 450 x 300 x 450
(x 7850..8750, z 650..1550). The key-framed van drives in on lane z 1030 (half width ~100..110 -> z ~920..1140, tools/kl_dd10_vanlane_1108.py) and stops at x ~8640. A seat at
(8300, 1100) died ~4 s into the drive-in (run over); a seat at (8300, 750) lived. The lane lies inside the box, so waiting in the box meant waiting under the van.

Change: otrExitLevel keeps x and y and its group, z becomes 650..900: centre (8300, 200, 775), half (450, 300, 125). ONLY that node's .prp ZGEOM[2] / ZBoxPrimitive[2] fields change.
The .gms record is NOT touched (the loader reads the .prp's; same as the vancall approach box, GUESS that nothing else reads the .gms translation of a trigger box).
The approach box (node 22127, half 800 x 300 x 450) is untouched: it only shows the van.

The strip is 25 cm clear of the lane edge (920 vs 900). A heister who walks in from the west or lands by the ledge route (KLJoin [Join.3] Land 8300 0 750) is inside it.
KLJoin.ini is NOT touched: Land (8300 0 750) is inside the strip (z 650..900); Target 8300 0 1100 is only a CHECK of the jump point (kljoin.c).

  python tools/kl_dd10_exitsouth_1110.py stage [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_dd10_exitsouth_1110.py check [--in-dir ...] [--out-root ...] [--no-undo]
  python tools/kl_dd10_exitsouth_1110.py report [--in-dir ...]      geometry facts for the README (reads only)
Never installs anything. REFUSES unless the live files are the expected md5s and the box holds the pre-edit values.
Toggle: a map-side staged option, "(recommended on)". Undo: UNDO.bat (python install.py --undo): every file back byte for byte."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DD10')
OUT_ROOT = 'C:/kl_build_1024'
MAP, SLOT = 'DD10', 'F07'
NAME, TAG = 'dd10evac_1113', '.before-dd10evac1113'
TEMPLATE = os.environ.get('KL_EXITSOUTH_TEMPLATE', 'C:/kl_build_1024/dd10exitsouth_1110/install.py')
ZIP, BOTS, BASE = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5'
LIVE_MD5 = {ZIP: 'b8c95d37e0c206cd72780b22e78cba50', BOTS: '7bda72206251c28a8ae18ea0ae1d34e3', BASE: 'd6b968430b391e9bd9b9d6250a574d9e'}
R = 'ROOT' + chr(92)
EXIT_BOX = R + 'Gameplay!EscapeSetup!otrExitLevel'
OLD_AT, OLD_HALF = [8300.0, 200.0, 775.0], [450.0, 300.0, 125.0]       # live (exitsouth_1110): z 650..900, but SideWall_06 stands at z 800
NEW_AT, NEW_HALF = [8450.0, 200.0, 860.0], [300.0, 300.0, 55.0]        # x 8150..8750, z 805..915: on the walkable street, off the lane
LANE_Z0, LANE_Z1 = 920.0, 1140.0
WALL_Z, BIN_X1 = 800.0, 8144.0


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _mods():
    global kl_fa, F, A, J, SK
    import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_prpjoin as J, kl_skyline_1108 as SK


def box_values(sc, k):
    lab = J.labels('dd', sc.cls(k))
    vv = kl_fa.node_values(sc, k)
    return [vv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3)], vv[lab.index('ZGEOM[2]')]


def edit_scene(B, log=print):
    sc = B.sc
    k = A.node_of(sc, EXIT_BOX)
    if k not in [c[0] for c in kl_fa.controllers(sc, 'OnlineExitLevelTrigger')]:
        raise SystemExit('REFUSED: %s has no OnlineExitLevelTrigger controller' % EXIT_BOX)
    half, at = box_values(sc, k)
    if [float(x) for x in half] != OLD_HALF or [float(x) for x in at] != OLD_AT:
        raise SystemExit('REFUSED: the exit box is not the pre-edit one: half %r at %r' % (half, at))
    lab = J.labels('dd', sc.cls(k))
    import kl_graft

    def fn(us):
        A.setv(sc, us, lab.index('ZGEOM[2]'), list(NEW_AT))
        A.setv(sc, us, lab.index('ZBoxPrimitive[0]'), NEW_HALF[0])
        A.setv(sc, us, lab.index('ZBoxPrimitive[2]'), NEW_HALF[2])
    kl_graft.edit(sc.nodes[k], 'props', fn)         # .prp only (A.place would also rewrite the .gms record in memory; it is never written)
    log('  exit box node %d: centre %s -> %s, half z %g -> %g (x 8150..8750, z 805..915)' % (k, OLD_AT, NEW_AT, OLD_HALF[2], NEW_HALF[2]))
    return k


def patch_zip(src, dst, log=print):
    B = F.Built(src)
    edit_scene(B, log)
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))


def make_install(out, stage_md5, template_text=None):
    t = template_text if template_text is not None else open(TEMPLATE, encoding='utf-8').read()
    rows = ", ".join("('%s', '%s', '%s')" % (n, LIVE_MD5[n], stage_md5[n]) for n in (ZIP, BOTS, BASE))
    t, k = re.subn(r"^FILES = \[.*?\]\n", lambda m: "FILES = [" + rows + "]\n", t, flags=re.S | re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES line')
    t, k = re.subn(r"^MAP, TAG = '[A-Z0-9]+', '[^']+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r'^r?"""Installs / undoes[^\n]*\n', 'r"""Installs / undoes DD10 EVAC 1113 on the live DD10 files: the exit box moves onto the walkable street strip (tools/kl_dd10_evac_1113.py).\n', t, count=1, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no docstring head')
    return t


README = """DD10 EVAC 1113 (Flat Raid, slot F07) - staged, NOT installed. (recommended on)
Tool: tools/kl_dd10_evac_1113.py. Tester: 'you cant put the evacuation point there because normally you cant get past it'.
Live now (pinned): F07_Main.zip b8c95d37, bots 7bda7220, bots.base.md5 d6b96843 (KLJoin.ini NOT touched; its Land 8300 0 860 lies inside the new box).
Staged:            F07_Main.zip %(zip)s, bots %(bots)s, bots.base.md5 %(base)s.

CAUSE (MEASURED on the live map): otrExitLevel (the exit / call box) is x 7850..8750, z 650..900, centre (8300, 775). The street is walled at z 800 (SideWall_06/07):
z 650..800 is OUTSIDE the street (no nav polygon, no floor), the centre is 25 cm behind the wall, and only a 100 cm strip z 800..900 of the box is walkable, with a
dustbin (x 8015..8144, z 798..894) at its west end. The closed gate (BigFence_A_02 x 8000..8014, hidden but solid, + ColiObj_HERO_Plane01 x 8018) ends the street at x 8018.
The rest of the way is open: nav flood from the start spawns (x 12300..13050, z -330..140) reaches the whole road x 8080..13349 (156 polys), no collision on the
poly-centre path at heights 40 and 120. Not done: a full body-width sweep, and no live walk.
FIX: the box becomes x 8150..8750, z 805..915 (centre (8450, 200, 860), half 300 x 300 x 55): wholly on the walkable street, east of the dustbin, clear of the van lane
(z 920..1140, van stop (8642, 1030)). Only the .prp of the plain and the bots zip differ (the box centre + 2 half extents of node otrExitLevel).
Install: python install.py (game closed; backups *.before-dd10evac1113 next to the files).   Undo: UNDO.bat  (python install.py --undo), byte exact.
GUESS: the loader reads the box from the .prp (same as exitsouth_1110; the .gms record keeps the old translation 8300 200 1100). If the game used the .gms centre the box would sit on the lane.
Bench: walk the street from the start to z 860 at x 8450 (van called), wait through the drive-in, board.
"""


def stage(in_dir, out_root, log=print):
    for n in (ZIP, BOTS, BASE):
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != LIVE_MD5[n]:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DD10 changed: re-stage)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', LIVE_MD5[n]))
    if open(os.path.join(in_dir, BASE)).read().strip() != fmd5(os.path.join(in_dir, ZIP)):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')
    out = os.path.join(out_root, NAME)
    os.makedirs(out, exist_ok=True)
    for old in (ZIP, BOTS, BASE):
        if os.path.exists(os.path.join(out, old)):
            os.remove(os.path.join(out, old))
    log('stage -> %s' % out)
    for n in (ZIP, BOTS):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), log)
    with open(os.path.join(out, BASE), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, ZIP)) + '\n')
    sm = {n: fmd5(os.path.join(out, n)) for n in (ZIP, BOTS, BASE)}
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(make_install(out, sm))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    open(os.path.join(out, 'README.txt'), 'w', newline='\n').write(README % dict(zip=sm[ZIP][:8], bots=sm[BOTS][:8], base=sm[BASE][:8]))
    json.dump(dict(md5=sm, live=LIVE_MD5, tag=TAG), open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def check(in_dir, out_root, log=print, undo_rehearsal=True):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    for n in (ZIP, BOTS):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
            need(changed == ['.prp'], '%s: only .prp differs (changed: %s)' % (n, changed))
            pa, pb = zb.read([m for m in zb.namelist() if m.endswith('.prp')][0]), zs.read([m for m in zs.namelist() if m.endswith('.prp')][0])
            need(len(pa) == len(pb), '%s: .prp same length (%d)' % (n, len(pa)))
            diff = [i for i in range(min(len(pa), len(pb))) if pa[i] != pb[i]]
            need(0 < len(diff) <= 8 and diff[-1] - diff[0] < 200, '%s: .prp %d bytes differ, span %s (one entity)' % (n, len(diff), (diff[0], diff[-1]) if diff else None))
        Bb, Bs = F.Built(base), F.Built(stg)
        need(F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip' % n)
        k = A.node_of(Bs.sc, EXIT_BOX)
        h, at = box_values(Bs.sc, k)
        need([float(x) for x in h] == NEW_HALF and [float(x) for x in at] == NEW_AT, '%s: exit box half %s at %s' % (n, h, at))
        need(NEW_AT[2] + NEW_HALF[2] < LANE_Z0 and NEW_AT[2] - NEW_HALF[2] > WALL_Z and NEW_AT[0] - NEW_HALF[0] > BIN_X1, '%s: box z %g..%g clear of the lane z %g..%g, inside the street (wall z %g), east of the dustbin x %g' % (n, NEW_AT[2] - NEW_HALF[2], NEW_AT[2] + NEW_HALF[2], LANE_Z0, LANE_Z1, WALL_Z, BIN_X1))
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or len(Bb.sc.nodes[j]['ctrls']) != len(Bs.sc.nodes[j]['ctrls'])
                 or any(x != y for x, y in zip(Bb.sc.nodes[j]['ctrls'], Bs.sc.nodes[j]['ctrls']))]
        need(diffn == [k], '%s: exactly node %d differs' % (n, k))
        need(Bs.files[Bs.ext['.gms']] == Bb.files[Bb.ext['.gms']] if hasattr(Bs, 'files') else True, '%s: .gms byte-equal' % n)
    need(open(os.path.join(out, BASE)).read().strip() == fmd5(os.path.join(out, ZIP)), 'bots.base.md5 = md5 of the plain staged zip')
    with zipfile.ZipFile(os.path.join(in_dir, ZIP)) as a, zipfile.ZipFile(os.path.join(in_dir, BOTS)) as b, zipfile.ZipFile(os.path.join(out, ZIP)) as c, zipfile.ZipFile(os.path.join(out, BOTS)) as d:
        ld = [m for m in a.namelist() if a.read(m) != b.read(m)]
        sd = [m for m in c.namelist() if c.read(m) != d.read(m)]
        need(ld == sd, 'plain and bots zips differ only in %s (live %s)' % (sd, ld))
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in (ZIP, BOTS, BASE):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    if undo_rehearsal:
        sg = tempfile.mkdtemp(prefix='exitsouthgame_', dir=out)
        try:
            d = os.path.join(sg, 'KLExpansion', 'Maps', MAP)
            os.makedirs(d)
            names = [x for x in os.listdir(in_dir) if x in LIVE_MD5 or x == 'KLJoin.ini']
            for n in names:
                shutil.copyfile(os.path.join(in_dir, n), os.path.join(d, n))
            before = {n: fmd5(os.path.join(d, n)) for n in names}
            run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', sg, '--skip-run-check'] + list(a), capture_output=True, text=True)
            r = run('--dry')
            need(r.returncode == 0, 'install.py --dry rc %d' % r.returncode)
            r = run()
            need(r.returncode == 0 and all(fmd5(os.path.join(d, n)) == (fmd5(os.path.join(out, n)) if n in LIVE_MD5 else before[n]) for n in names) and all(os.path.isfile(os.path.join(d, n + TAG)) for n in LIVE_MD5), 'scratch install lands the staged md5s, backups *%s made, KLJoin.ini untouched' % TAG)
            r2 = run()
            need(r2.returncode != 0, 'a second install is refused')
            r = run('--undo')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in names} == before and not any(os.path.exists(os.path.join(d, n + TAG)) for n in LIVE_MD5), 'scratch undo restores every file byte for byte')
        finally:
            shutil.rmtree(sg, ignore_errors=True)
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def report(in_dir, log=print):
    """Geometry facts: AllyEscapeBox, the landing, the lane."""
    sc = F.Built(os.path.join(in_dir, ZIP)).sc
    for cn in ('ZAllyEscapeBox', 'AllyEscapeBox'):
        for kk, _i, v in kl_fa.controllers(sc, cn):
            half, at = (None, None)
            try:
                half, at = box_values(sc, kk)
            except Exception:
                pass
            log('  %s node %d %s half %s at %s' % (cn, kk, sc.path[kk], half, at))
    log('  new exit strip x %g..%g z %g..%g y %g..%g' % (NEW_AT[0] - NEW_HALF[0], NEW_AT[0] + NEW_HALF[0], NEW_AT[2] - NEW_HALF[2], NEW_AT[2] + NEW_HALF[2], NEW_AT[1] - NEW_HALF[1], NEW_AT[1] + NEW_HALF[1]))
    for nm, (x, y, z) in (('Join.3 Land (live ini)', (8300, 0, 860)), ('Join.3 Target', (8300, 0, 1100))):
        inside = abs(x - NEW_AT[0]) <= NEW_HALF[0] and abs(y - NEW_AT[1]) <= NEW_HALF[1] and abs(z - NEW_AT[2]) <= NEW_HALF[2]
        log('  %-20s (%g,%g,%g): in new exit strip %s; in van lane z %g..%g: %s' % (nm, x, y, z, inside, LANE_Z0, LANE_Z1, LANE_Z0 <= z <= LANE_Z1))


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check', 'report'):
        print(__doc__)
        return 2
    _mods()
    in_dir, out_root = opt('--in-dir', LIVE), opt('--out-root', OUT_ROOT)
    if a[0] == 'report':
        report(in_dir)
        return 0
    if a[0] == 'stage':
        stage(in_dir, out_root)
    return 0 if check(in_dir, out_root, undo_rehearsal='--no-undo' not in a) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
