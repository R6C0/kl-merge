#!/usr/bin/env python3
r"""kl_lc_depart_1108.py - Last Call (DM05A): the escape heli's DEPARTURE route ('Escaping') starts INSIDE a building. Stage built from the LIVE files
(2026-11-08, offline, stage only; nothing is installed, no game is launched).

Audit (tools/kl_vehaudit_1108.py, re/vehicle_routes_1108.md): the 'Escaping' ZHeli spline of DM05A starts at (7058, 2271, 3467) = the OLD pad point, which lies
INSIDE SO0004_M05_BuildingF_01 + Building_H_03 (keys 0..3). That point was right when the heli LANDED on the pad; since ROUTE_2H (kl_arrival_1107.py, live) the
arrival (Incomming spline) ends as a HOVER at (8000, 2700, 3000) above the pad's east edge, 1.1 km away from Escaping's first key and on the other side of BuildingF's cleft.

What Escaping is (P = proven in data / docs, G = guess; no live run proves the hand-over, it is read from the docs and the bench logs):
  P  The ZOnlineEscHavokCar controller names two rout groups, field 0 'EscapeSetup!EscapeChopper\Incomming' and field 1 '...\Escaping' (re/heli_call.md, re/map_escape.md).
     The call that summons the vehicle (RESET) goes to field 0 only; field 1 is reached in the ZMOVEMENT_MSG_GOTO_NEXT_SPLINE case (kl2 0x549860) = 'the way out'.
     So Escaping IS the leg flown after boarding, started when Incomming has finished.
  G  The engine hands the heli from the END of Incomming to Escaping by flying it (the ZHeliFlyBehaviour goal flies to waypoints; no teleport has been found in the exe),
     it does not warp it to key 0. Evidence: bench lcarr2h1108 (11-08): heli boarded at the hover, then drawn lifting away over the roof; the 2C/2E benches saw the heli
     leave the pad and stop short of the last key. Not provable offline whether the first keys are ever seen: if the heli flies from the hover to key 0 the first
     segment is visible (the outro eye (7400, 2500, 2800) looks at it, Roof .rmi box 7 draws it); if it teleports to key 0 the heli would POP from the hover to key 0.
  =  Either reading is solved by ONE rule: key 0 of Escaping = the END POINT OF INCOMMING (8000, 2700, 3000), exactly. Zero-length hand-over: nothing to fly, nothing to pop.

FIX: ROUTE_DEPART = 5 points (the live field holds 5: SAME KEY COUNT, so nothing renumbers; only the 5 xyz triples change, 60 bytes; the editor angle / 10.0 / 0xcdcdcdcd
bytes of every point and the editor memory after the points are kept). Old -> new (world cm):
    0  (7058, 2271, 3467) -> (8000, 2700, 3000)   = ROUTE_2H's last point (the hover)
    1  (7493, 3253, 3375) -> (8700, 3000, 2800)   slide EAST out of the cleft, away from BuildingF/H (hull 156 cm at key 0 is the min)
    2  (7929, 4235, 3283) -> (8900, 4300, 2900)   climb
    3  (8364, 5217, 3191) -> (8900, 5300, 3000)
    4  (8800, 6200, 3100) -> (8800, 6200, 3100)   unchanged: the leaving leg's end (the audit says it ends no viewer: ok)
Hull-checked with tools/kl_heli_hull_1107.py (yaw-agnostic cylinder R 990, y -10..420, conservative field) AND the exact point-triangle distance at every hull sample
(kl_arrival_1107.Mesh), linear and Catmull-Rom (GUESS: the engine's spline kind is unknown), against the level's RENDER triangles: needs >= 150 cm like ROUTE_2H.
Every key centre stays inside Roof .rmi box 7 (x 6676..16300, y 1460..7000, z -300..6800; the hull at key 4 pokes ~190 past y 7000, not checked in code), so the heli is drawn the whole way (GUESS: a dynamic object
outside every room box is not drawn, 2c-2e benches).

Changes ONLY the .prp member of F01_Main.zip and of F01_Main.bots.zip (the sibling carries the same prp structure; the same edit is applied to it and verified on its
own). F01_Main.bots.base.md5 = md5 of the plain staged zip. KLGuns.ini is copied, NOT in install.py's FILES (same md5 both sides).

  python tools/kl_lc_depart_1108.py stage [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_lc_depart_1108.py check [--in-dir <map dir>] [--out-root C:/kl_build_1024]       (also runs 'clearance')
  python tools/kl_lc_depart_1108.py clearance [--zip <F01_Main.zip>]                               hull clearance of Incomming + Escaping (field + exact)
  python tools/kl_lc_depart_1108.py audit [--out-root C:/kl_build_1024]                            kl_vehaudit_1108 on the staged zip (scratch copy), DM05A only
Never installs anything. REFUSES unless the live files are the expected md5s and the splines hold the pre-edit values."""
import hashlib, os, re, shutil, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))
import kl_fa
import kl_skyline_1108 as SK
import kl_club_outro_1106 as O
import kl_arrival_1107 as ARR

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT_ROOT = 'C:/kl_build_1024'
NAME, TAG, TITLE = 'lcdepart_1108', '.before-lcdepart1108', 'LCDEPART1108'
TEMPLATE = 'C:/kl_build_1024/citylights_1108/install.py'
PRP = 'Scenes/Locations/F01/F01_Main.prp'
LIVE_MD5 = {'F01_Main.zip': '80b5547c9852808d0c4f28abaf6dd6a1', 'F01_Main.bots.zip': '1e02dbe5503661a804f758541dc8d98a',
            'F01_Main.bots.base.md5': 'c009e5afbb4bd3bf57aff2182601c281', 'KLGuns.ini': '33432bb94d8c9ea009b7255cdb4a430e'}
ESCAPING = 'EscapeSetup!EscapeChopper\\Escaping\\Spline'
INCOMING = 'EscapeSetup!EscapeChopper\\Incomming\\Spline'
OLD_ESCAPING = ((7058.0, 2271.0, 3467.0), (7493.0, 3253.0, 3375.0), (7929.0, 4235.0, 3283.0), (8364.0, 5217.0, 3191.0), (8800.0, 6200.0, 3100.0))   # = kl_club_outro_1106.ROUTE_2E
HOVER = ARR.ROUTE_2H[-1]                                  # (8000, 2700, 3000): where Incomming ends
ROUTE_DEPART = (HOVER, (8700.0, 3000.0, 2800.0), (8900.0, 4300.0, 2900.0), (8900.0, 5300.0, 3000.0), (8800.0, 6200.0, 3100.0))
MIN_CLEAR = 150.0                                         # cm, as ROUTE_2H (its own minimum is 156 at the hover itself)
# GUESS: which render-owner names are SOLID (the audit report's rule: fog / light / foliage / smoke / wire / vehicle hits are listed in its JSON only)
SOLID = ('wall', 'fence', 'building', 'factory', 'shop', 'garage', 'tunnel', 'roof', 'pillar', 'tower', 'house', 'block')
SOFT = ('fog', 'light', 'lamp', 'tree', 'foliage', 'smoke', 'wire', 'glow', 'plane', 'v_', 'helicopter', 'chopper', 'heli')


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def spline_of(zp, name):
    """-> (scene, node, raw field bytes, R, T) of the named ZEditorSpline; REFUSES unless the .prp round-trips through the scene reader."""
    import kl_fa_author as A
    import kl_prpjoin as J
    sc, _snd, _loc = kl_fa.load(zp)
    with zipfile.ZipFile(zp) as z:
        if sc.p.serialize() != z.read(PRP):
            raise SystemExit('REFUSED: %s: the .prp does not round-trip through the scene reader' % zp)
    k = A.node_of(sc, name)
    lab = J.labels('dd', sc.cls(k))
    i = lab.index('ZEditorSpline[0]')
    raw = kl_fa.node_values(sc, k)[i]
    R, T = O.frame_of(zp, k)
    return sc, k, lab, raw, R, T


def points_of(zp, name):
    sc, k, lab, raw, R, T = spline_of(zp, name)
    return O.world_points(raw, R, T), raw


def near(a, b, tol=0.5):
    return len(a) == len(b) and all(abs(x - y) <= tol for p, q in zip(a, b) for x, y in zip(p, q))


def refuse_unless_pre(zp):
    esc, _ = points_of(zp, ESCAPING)
    inc, _ = points_of(zp, INCOMING)
    if not near(esc, OLD_ESCAPING):
        raise SystemExit('REFUSED: %s Escaping is %r, not the pre-edit ROUTE_2E %r (re-stage on the new live files)' % (zp, [tuple(round(x) for x in p) for p in esc], OLD_ESCAPING))
    if not near(inc, ARR.ROUTE_2H):
        raise SystemExit('REFUSED: %s Incomming is not ROUTE_2H (the arrival this fix continues from)' % zp)


def patch_zip(src, dst, log):
    sc, k, lab, raw, R, T = spline_of(src, ESCAPING)
    new, n = O.route_raw(raw, ROUTE_DEPART, R, T)
    if n != len(ROUTE_DEPART):
        raise SystemExit('REFUSED: Escaping holds %d points, this fix is written for the same count (%d)' % (n, len(ROUTE_DEPART)))

    def fn(us):
        u = us[lab.index('ZEditorSpline[0]')]
        if u[1][0] != 0x0d or u[1][1][4:] != raw:
            raise SystemExit('REFUSED: the raw field is not where it was read')
        u[1] = (0x0d, u[1][1][:4] + new)
    kl_fa.edit(sc, k, None, fn)
    out = sc.p.serialize()
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    members = [(m, out if m == PRP else d) for m, d in members]
    SK.write_zip(dst, members, SK.tex_level(src))
    log('  Escaping node %d: %d points rewritten in place (same count), field %d bytes unchanged in size' % (k, n, len(raw)))


def make_install(out, stage_md5):
    t = open(TEMPLATE, encoding='utf-8').read()
    rows = ["    ('%s', '%s', '%s')," % (n, LIVE_MD5[n], stage_md5[n]) for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')]
    t, k = re.subn(r"FILES = \[.*?\n\]\n", lambda m: "FILES = [   # name, live md5 before, staged md5 after (KLGuns.ini unchanged: not listed)\n" + '\n'.join(rows) + "\n]\n", t, flags=re.S)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES block')
    t, k = re.subn(r"TAG = 'DM05A', '\.before-[a-z0-9]+'", "TAG = 'DM05A', '%s'" % TAG, t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single TAG line')
    t, k = re.subn(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5['F01_Main.zip'], t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single LIVE_ZIP_MD5 line')
    t = t.replace('CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)', '%s (bench only) (tools/kl_lc_depart_1108.py)' % TITLE)
    t = t.replace('.before-skyline1108', TAG)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)


def stage(in_dir, out_root, log=print):
    out = os.path.join(out_root, NAME)
    for n, want in LIVE_MD5.items():
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != want:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DM05A changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', want))
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        refuse_unless_pre(os.path.join(in_dir, n))
    os.makedirs(out, exist_ok=True)
    log('stage -> %s' % out)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), log)
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, 'F01_Main.zip')) + '\n')
    shutil.copyfile(os.path.join(in_dir, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    sm = {n: fmd5(os.path.join(out, n)) for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
    make_install(out, sm)
    for n in sorted(os.listdir(out)):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def node_diff(a, b):
    """[(node, 'props'|ctrl index)] where the two scenes differ"""
    if len(a.nodes) != len(b.nodes):
        return [('node count', len(a.nodes), len(b.nodes))]
    out = []
    for k in range(1, len(a.nodes)):
        na, nb = a.nodes[k], b.nodes[k]
        if na['props'] != nb['props']:
            out.append((k, 'props'))
        if len(na['ctrls']) != len(nb['ctrls']):
            out.append((k, 'ctrl count'))
            continue
        for i, (x, y) in enumerate(zip(na['ctrls'], nb['ctrls'])):
            if x != y:
                out.append((k, i))
    return out


# ------------------------------------------------------------------ clearance
def clearance(zp, log=print, exact=True):
    """Hull clearance (cm) of Incomming and Escaping of `zp`: conservative field min (linear + Catmull) and the exact point-triangle min at every hull sample.
    -> {name: {kind: (field min, where, exact min)}}. Needs the render geometry / field in C:/kl_build_1024/arrival_1107 (built from the live DM05A render triangles;
    the heli routes do not change what the level draws)."""
    import numpy as np
    import kl_heli_hull_1107 as H
    F, hs = H.Field(), H.hull_samples()
    t, o, n = ARR.load(os.path.join(ARR.OUT, 'dm05a_render.npz'))
    keep = [i for i, x in enumerate(n) if 'glow' not in x.lower() and 'distance' not in x.lower()]
    sel = np.isin(o, keep)
    M = ARR.Mesh(t[sel], o[sel], n) if exact else None
    res = {}
    for name, label in ((INCOMING, 'Incomming'), (ESCAPING, 'Escaping')):
        pts, _ = points_of(zp, name)
        res[label] = {}
        for kind in ('linear', 'catmull'):
            path = ARR.catmull(pts) if kind == 'catmull' else [np.array(p, float) for p in pts]
            dense = []
            for a, b in zip(path, path[1:]):
                m = max(1, int(np.linalg.norm(b - a) / 60.0))
                dense.extend(a + (b - a) * i / m for i in range(m))
            dense.append(path[-1])
            dense = np.array(dense)
            c = F.hull(dense, hs)
            i = int(c.argmin())
            ex = None
            if exact:
                ex = 1e9
                for p in dense[::max(1, int(150 / 60))]:
                    for h in hs:
                        d, _ow = M.dist(tuple(p + h), 600.0)
                        ex = min(ex, d)
            res[label][kind] = (float(c.min()), tuple(int(x) for x in dense[i]), ex)
            log('  %-9s %-8s field min %4d at %s   exact min %s' % (label, kind, c.min(), res[label][kind][1], 'n/a' if ex is None else '%d' % ex))
    return res


def audit(out_root, log=print):
    """kl_vehaudit_1108 on a scratch copy of the staged zip (maps-dir layout <dir>/DM05A/F01_Main.zip) -> {vehicle: {solid pierce owner: info}}"""
    import kl_vehaudit_1108 as V
    scratch = os.path.join(out_root, NAME, '_audit')
    d = os.path.join(scratch, 'DM05A')
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(out_root, NAME, 'F01_Main.zip'), os.path.join(d, 'F01_Main.zip'))
    try:
        r = V.audit_map('DM05A', scratch, log=log)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    bad = {}
    for v in r['vehicles']:
        if v.get('kind') != 'HELI':
            continue
        solid = {k: p for k, p in (v.get('pierce') or {}).items() if any(s in k.lower() for s in SOLID) and not any(s in k.lower() for s in SOFT)}
        log('  HELI %-60s start %s end %s pierce %s' % (v['name'][-60:], v.get('start'), v.get('end'), 'NONE' if not v.get('pierce') else sorted(v['pierce'])))
        bad[v['name']] = solid
    return bad


def check(in_dir, out_root, log=print):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(ok, msg):
        log('  %s %s' % ('ok  ' if ok else 'FAIL', msg))
        if not ok:
            bad.append(msg)
    log('check (%s)' % out)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = [m for m in zb.namelist() if zb.read(m) != zs.read(m)]
            need(changed == [PRP], '%s: only the .prp differs (changed: %s)' % (n, changed))
        sb, kb, labb, rawb, Rb, Tb = spline_of(base, ESCAPING)
        ss, ks, labs, raws, Rs, Ts = spline_of(stg, ESCAPING)
        diff = node_diff(sb, ss)
        need(diff == [(kb, 'props')], '%s: exactly the Escaping spline node changed %s (node %d, no node/controller added)' % (n, diff, kb))
        need(len(raws) == len(rawb), '%s: spline field size unchanged (%d)' % (n, len(raws)))
        pts = O.world_points(raws, Rs, Ts)
        need(near(pts, ROUTE_DEPART, 0.5), '%s: Escaping reads back as ROUTE_DEPART (5 points, key count unchanged)' % n)
        need(near([pts[0]], [HOVER], 0.5), '%s: key 0 = Incomming end %s' % (n, HOVER))
        # only the 5 x,y,z triples (12 bytes each) may differ; header, per-point angle/10.0/0xcdcdcdcd and the editor memory after the points are kept
        keep = [i for i in range(len(rawb)) if not any(O.HDR + O.POINT * p <= i < O.HDR + O.POINT * p + 12 for p in range(5))]
        need(all(rawb[i] == raws[i] for i in keep), '%s: every byte outside the 5 xyz triples equal (header, editor angles, editor memory)' % n)
        ib, _ = points_of(base, INCOMING)
        is_, _ = points_of(stg, INCOMING)
        need(near(ib, is_, 0.0), '%s: Incomming spline unchanged' % n)
    md = open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip()
    need(md == fmd5(os.path.join(out, 'F01_Main.zip')), 'bots.base.md5 = md5 of the plain staged zip')
    need(fmd5(os.path.join(out, 'KLGuns.ini')) == LIVE_MD5['KLGuns.ini'], 'KLGuns.ini copied byte for byte')
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    need("'%s'" % TAG in inst and "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5['F01_Main.zip'] in inst, 'install.py TAG %s and LIVE_ZIP_MD5 pinned' % TAG)
    try:
        import check as CK
        zp = os.path.join(out, 'F01_Main.zip')
        with zipfile.ZipFile(zp) as z:
            m = {x.rsplit('_Main', 1)[1].lower(): x for x in z.namelist() if '_Main' in x}
            probs, _n = CK.problems(lambda e: z.read(m['.' + e.lstrip('.').lower()]))
        with zipfile.ZipFile(os.path.join(in_dir, 'F01_Main.zip')) as zb:
            bprobs, _n = CK.problems(lambda e: zb.read(m['.' + e.lstrip('.').lower()]))
        need(set(probs) <= set(bprobs), 'debug/check.py: %d layout findings, none new against the live zip (%d there)' % (len(probs), len(bprobs)))
    except SystemExit:
        raise
    except Exception as e:
        log('  skip debug/check.py (%s: %s)' % (type(e).__name__, e))
    r = subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--dry'], capture_output=True, text=True)
    need(r.returncode == 0, 'install.py --dry exit %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:120]))
    try:
        cl = clearance(os.path.join(out, 'F01_Main.zip'), log)
        for label in ('Incomming', 'Escaping'):
            for kind, (fmin, _w, ex) in cl[label].items():
                need(fmin >= MIN_CLEAR and (ex is None or ex >= MIN_CLEAR), '%s %s hull clearance field %d / exact %s >= %d' % (label, kind, fmin, ex, MIN_CLEAR))
    except (OSError, ImportError) as e:
        need(False, 'clearance could not run (%s: %s)' % (type(e).__name__, e))
    log('check: %s' % ('OK' if not bad else '%d FAIL' % len(bad)))
    return not bad


def main(a):
    if not a or a[0] not in ('stage', 'check', 'clearance', 'audit'):
        print(__doc__)
        return 2
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    in_dir, out_root = get('--in-dir', LIVE), get('--out-root', OUT_ROOT)
    if a[0] == 'clearance':
        zp = get('--zip', os.path.join(out_root, NAME, 'F01_Main.zip'))
        cl = clearance(zp)
        return 0 if all(v[0] >= MIN_CLEAR and v[2] >= MIN_CLEAR for d in cl.values() for v in d.values()) else 1
    if a[0] == 'audit':
        bad = audit(out_root)
        print('SOLID pierces:', {k: sorted(v) for k, v in bad.items()})
        return 0 if not any(bad.values()) else 1
    if a[0] == 'stage':
        stage(in_dir, out_root)
    return 0 if check(in_dir, out_root) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
