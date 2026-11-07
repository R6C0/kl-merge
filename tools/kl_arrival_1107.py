#!/usr/bin/env python3
r"""kl_arrival_1107.py - cinematic getaway ARRIVAL planning for the DM maps' escape vehicles. OFFLINE and READ-ONLY on the game folder.

  python tools/kl_arrival_1107.py geom   [--zip <F01_Main.zip>] [--out <npz>]      render triangles of the level (what the map DRAWS) -> npz
  python tools/kl_arrival_1107.py plan   [--npz <npz>]                             search ROUTE_2G, print its clearance table
  python tools/kl_arrival_1107.py stage  [--in-dir <dir>] [--out <dir>] [--expect-base 1d325299]   stage ROUTE_2G + Roof box on the live DM05A

Units: cm, y up. Collision triangles (Havok) are NOT what is drawn: BuildingJ_01's render shell is missing from the collision proxy
(c9 11-06), so every clearance here is measured against RENDER triangles (kl_fa_loot.Assets, vertex stride 40).
Nothing here writes into the game folder.
"""
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT = r'C:\kl_build_1024\arrival_1107'
HIDDEN = 0x1          # replaced below by kl_fa_loot.HIDDEN


def geom(zp, region=None, log=print):
    """Render triangles of every non-hidden entity under 'Locations/' -> (tris float32 [n,3,3], owner int32 [n], names list)."""
    import kl_fa_loot as L
    B, As = L.Built(zp), L.Assets(zp)
    fr = L.frames(B.scene)
    tris, owner, names, nameix = [], [], [], {}
    box = {}
    for k, e in enumerate(B.ents):
        if e.model <= 0 or e.flags & L.HIDDEN or not B.sc.names[B.sc.top[k + 1]].startswith('Locations/'):
            continue
        if e.model not in box:
            try:
                meshes = As.meshes(e.model)
                geo = [As.geometry(o) for o in meshes]
                pos = [np.array(g[0], np.float32).reshape(-1, 3) for g in geo]
                ii = [np.array(g[2], np.int32).reshape(-1, 3) for g in geo]
                box[e.model] = (pos, ii)
            except (ValueError, IndexError, struct.error):
                box[e.model] = None
        if box[e.model] is None:
            continue
        Rm, T = fr[e]
        R = np.array(Rm, np.float64)
        name = B.sc.path[k + 1][5:]
        for pos, ii in zip(*box[e.model]):
            if not len(pos) or not len(ii):
                continue
            w = (pos.astype(np.float64) @ R.T + np.array(T)).astype(np.float32)
            t = w[ii]
            if region is not None:
                lo, hi = t.min(axis=(0, 1)), t.max(axis=(0, 1))
                if (hi < region[0]).any() or (lo > region[1]).any():
                    continue
                m = ~(((t.max(axis=1) < region[0]).any(axis=1)) | ((t.min(axis=1) > region[1]).any(axis=1)))
                t = t[m]
            if not len(t):
                continue
            if name not in nameix:
                nameix[name] = len(names)
                names.append(name)
            tris.append(t)
            owner.append(np.full(len(t), nameix[name], np.int32))
    tris = np.concatenate(tris)
    owner = np.concatenate(owner)
    log('%d render triangles, %d entities' % (len(tris), len(names)))
    return tris, owner, names


def save(path, tris, owner, names):
    np.savez_compressed(path, tris=tris, owner=owner, names=np.array(names))


def load(path):
    d = np.load(path)
    return d['tris'], d['owner'], list(d['names'])


# ------------------------------------------------------------------ queries
class Mesh:
    def __init__(self, tris, owner, names, cell=400.0):
        self.t, self.o, self.names, self.cell = tris.astype(np.float64), owner, names, cell
        self.lo, self.hi = self.t.min(axis=1), self.t.max(axis=1)
        self.grid = {}
        c = cell
        for k in range(len(self.t)):
            for i in range(int(self.lo[k, 0] // c), int(self.hi[k, 0] // c) + 1):
                for j in range(int(self.lo[k, 2] // c), int(self.hi[k, 2] // c) + 1):
                    self.grid.setdefault((i, j), []).append(k)

    def near(self, p, r):
        """Indices of triangles whose AABB is within r of point p."""
        c = self.cell
        ks = set()
        for i in range(int((p[0] - r) // c), int((p[0] + r) // c) + 1):
            for j in range(int((p[2] - r) // c), int((p[2] + r) // c) + 1):
                ks.update(self.grid.get((i, j), ()))
        if not ks:
            return np.zeros(0, int)
        ks = np.fromiter(ks, int)
        pp = np.array(p)
        m = ((self.lo[ks] - r) <= pp).all(axis=1) & ((self.hi[ks] + r) >= pp).all(axis=1)
        return ks[m]

    def dist(self, p, r=3000.0):
        """(distance, owner name) to the nearest triangle, searched within r; (r, '') when none."""
        ks = self.near(p, r)
        if not len(ks):
            return r, ''
        d = point_tri(np.array(p, np.float64), self.t[ks])
        i = int(np.argmin(d))
        return float(d[i]), self.names[self.o[ks[i]]]


def point_tri(p, T):
    """Distance from point p to each triangle of T [n,3,3] (Ericson, vectorised)."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    vc, vb, va = d1 * d4 - d3 * d2, d5 * d2 - d1 * d6, d3 * d6 - d5 * d4
    n = len(T)
    q = np.empty((n, 3))
    # general interior case
    den = va + vb + vc
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    v, w = vb / den, vc / den
    q[:] = a + ab * v[:, None] + ac * w[:, None]
    # edge/vertex regions (applied in Ericson's order; later assignments are for exclusive regions)
    m = (d1 <= 0) & (d2 <= 0)
    q[m] = a[m]
    m2 = (d3 >= 0) & (d4 <= d3)
    q[m2] = b[m2]
    m3 = (d6 >= 0) & (d5 <= d6)
    q[m3] = c[m3]
    me = (vc <= 0) & (d1 >= 0) & (d3 <= 0) & ~m & ~m2
    t = np.where(np.abs(d1 - d3) < 1e-12, 0, d1 / np.where(np.abs(d1 - d3) < 1e-12, 1, d1 - d3))
    q[me] = (a + ab * t[:, None])[me]
    me = (vb <= 0) & (d2 >= 0) & (d6 <= 0) & ~m & ~m3
    t = np.where(np.abs(d2 - d6) < 1e-12, 0, d2 / np.where(np.abs(d2 - d6) < 1e-12, 1, d2 - d6))
    q[me] = (a + ac * t[:, None])[me]
    me = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0) & ~m2 & ~m3
    dd = (d4 - d3) + (d5 - d6)
    t = np.where(np.abs(dd) < 1e-12, 0, (d4 - d3) / np.where(np.abs(dd) < 1e-12, 1, dd))
    q[me] = (b + (c - b) * t[:, None])[me]
    return np.linalg.norm(q - p, axis=1)


def seg_hits(M, p, q):
    """[(t in 0..1, owner)] triangles pierced by the segment p->q (Moller-Trumbore, two-sided)."""
    p, q = np.array(p, float), np.array(q, float)
    d = q - p
    ln = np.linalg.norm(d)
    if ln < 1e-6:
        return []
    ks = set()
    n = int(ln / (M.cell / 2)) + 1
    for i in range(n + 1):
        x = p + d * i / n
        ks.update(M.near(x, M.cell).tolist())
    if not ks:
        return []
    ks = np.fromiter(ks, int)
    T = M.t[ks]
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    h = np.cross(d, e2)
    det = (e1 * h).sum(1)
    ok = np.abs(det) > 1e-9
    det = np.where(ok, det, 1)
    s = p - T[:, 0]
    u = (s * h).sum(1) / det
    qv = np.cross(s, e1)
    v = (d * qv).sum(1) / det
    t = (e2 * qv).sum(1) / det
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)
    return sorted((float(t[i]), M.names[M.o[ks[i]]]) for i in np.nonzero(m)[0])


def catmull(pts, n=24):
    """Centripetal-free uniform Catmull-Rom through pts (GUESS: the engine's spline kind is not known; linear is checked too)."""
    P = [np.array(x, float) for x in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        for k in range(n):
            t = k / n
            a, b, c, d = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    out.append(P[-2])
    return out


def route_table(M, pts, step=150.0, kind='linear'):
    """Clearance along a route: -> (min clearance, where, owner, total length). Samples every `step` cm."""
    path = catmull(pts) if kind == 'catmull' else [np.array(p, float) for p in pts]
    best = (1e9, None, '')
    L = 0.0
    prev = None
    for a, b in zip(path, path[1:]):
        ln = np.linalg.norm(b - a)
        n = max(1, int(ln / step))
        for i in range(n + 1):
            p = a + (b - a) * i / n
            d, o = M.dist(tuple(p), 2500.0)
            if d < best[0]:
                best = (d, tuple(np.round(p)), o)
        L += ln
    return best[0], best[1], best[2], L


# ---------------------------------------------------------------- ROUTE_2G
# The Incomming (arrival) spline of DM05A, 9 points (the live field holds 11: 2..11 allowed), WORLD cm. Replaces the live route, which pierces
# SO0004_M05_BuildingJ_01 (render shell; segment 0.78..0.9 of the path, 3 cm clearance at (9851,3465,6297)) and ends 120-197 cm from Building_H_03.
# 2g flies in from the north-east over open air, passes down the open void south-east of BuildingJ (x 8800..12800, z 400..2600), then turns back
# north-west over Building_H_03 and descends onto the pad from its OPEN (east) side: the pad sits against BuildingF's west wall.
# Checked offline against RENDER triangles (glow/Distance planes excluded): 0 segment piercings; clearance >= 706 cm (Catmull) / 764 cm (linear)
# everywhere farther than 1000 cm from the pad; 238 / 251 cm at the landing itself (the pad is in a cleft, the live route is the same there). NOT benched.
ROUTE_2G = ((15500.0, 6400.0, 6000.0), (14200.0, 5600.0, 4200.0), (12800.0, 4800.0, 2600.0), (11400.0, 4200.0, 1200.0), (10000.0, 3900.0, 400.0),
            (8800.0, 3700.0, 900.0), (8000.0, 3300.0, 1900.0), (7500.0, 2800.0, 2800.0), (7300.0, 2249.0, 3500.0))      # 2g: its last third clips the HULL (see ROUTE_2H)
# ROUTE_2H (2026-11-07, task heli2g): HULL-clear. Checked with tools/kl_heli_hull_1107.py (yaw-agnostic cylinder R 990, y -10..420, i.e. rotor disc 785 + tail 978 around
# the pivot) against the RENDER triangles: conservative field min 156 cm (linear and Catmull) at the HOVER point, exact point-triangle min 192 cm (hull sample
# (7012,2690,3069) vs BuildingF_01); en route >= 156 everywhere. The old 2g landing pivot (7300,2249,3500) is INSIDE the cleft by BuildingF (hull clearance 0).
# The route ends as a HOVER over the pad's east edge: pivot 8.2 m above the floor (y 1881), 670 cm horizontally / 686 cm above the centre of Triggers!BoardingTrigger_Heli.
# GUESS: boarding (EnterVehicle) works from that hover; the engine reading only x,y,z+count of the spline points. Start 15200 so start + 990 stays inside Roof box 7 (x<=16300).
ROUTE_2H = ((15200.0, 5500.0, 3600.0), (13500.0, 4400.0, 3000.0), (11500.0, 3500.0, 2700.0), (10000.0, 3400.0, 2700.0), (9000.0, 3300.0, 2700.0),
            (8500.0, 3100.0, 2800.0), (8000.0, 2700.0, 3000.0))
ROUTE = ROUTE_2H
INCOMING = r'EscapeSetup!EscapeChopper\Incomming\Spline'
# Roof .rmi box 7 for 2g: a SUPERSET of the 2f box (x 6676..9266, y 1460..6600, z 2594..4426) so the whole approach is drawn. Overlap-checked
# against every non-Roof box (box 1 street room 4086 ends at z -2490, box 58 room 877 at x 6591): none touched.
BOX_LO, BOX_HI = (6676.0, 1460.0, -300.0), (16300.0, 7000.0, 6800.0)


def box_2g():
    c = tuple(float(np.float32((BOX_LO[a] + BOX_HI[a]) / 2)) for a in range(3))
    h = tuple(float(np.float32((BOX_HI[a] - BOX_LO[a]) / 2)) for a in range(3))
    return c, h


def stage(in_dir=MAPDIR, out=os.path.join(OUT, 'lcarr_2h'), expect=None, log=print):
    """live DM05A -> ROUTE_2G Incomming spline + Roof box 7 enlarged to the 2g volume, one stage with install.py / UNDO bat. Reads in_dir only."""
    import json
    import shutil
    import kl_botsonline
    import kl_club_outro_1106 as O
    import kl_club_rmi_1106 as R
    names = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')
    src = os.path.join(in_dir, 'F01_Main.zip')
    h = O.md5(src)
    if expect and not h.startswith(expect):
        raise ValueError('refusing: live zip %s is not the expected base %s' % (h, expect))
    os.makedirs(out, exist_ok=True)
    cp, mid = os.path.join(out, '_in.zip'), os.path.join(out, '_mid.zip')
    shutil.copyfile(src, cp)
    if O.md5(cp) != h:
        raise ValueError('the input changed while it was copied')
    old_spline = O.SPLINE
    O.SPLINE = INCOMING
    try:
        n = O.build(cp, mid, log=log, route=ROUTE)
    finally:
        O.SPLINE = old_spline
    c, hh = box_2g()
    saved = (R.OLD_CENTRE, R.OLD_HALF, R.NEW_CENTRE, R.NEW_HALF, R.ROOF_POINTS)
    R.OLD_CENTRE, R.OLD_HALF = saved[2], saved[3]            # the live zip carries the 2f box
    R.NEW_CENTRE, R.NEW_HALF = c, hh
    R.ROOF_POINTS = tuple(ROUTE) + saved[4]
    final = os.path.join(out, 'F01_Main.zip')
    try:
        info = R.build(mid, final, log)
    finally:
        R.OLD_CENTRE, R.OLD_HALF, R.NEW_CENTRE, R.NEW_HALF, R.ROOF_POINTS = saved
    os.remove(cp)
    os.remove(mid)
    plain = O.md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = {nm: (O.md5(os.path.join(in_dir, nm)), O.md5(os.path.join(out, nm))) for nm in names}
    old_tag = O.TAG
    O.TAG = '.before-arrival1107'
    txt_pin = files['F01_Main.zip'][0]
    fl = ''.join("    (%r, %r, %r),\n" % (nm, o, w) for nm, (o, w) in files.items() if o != w)
    txt = (O.INSTALL % dict(files=fl, keep=0, pin=txt_pin)).replace('.before-outro1106', '.before-arrival1107').replace('OUTRO pass (2026-11-06)', 'ARRIVAL 2h pass (2026-11-07)').replace(
        "the escape heli's route is cut to its first 0 points\nso the fixed escape camera keeps it in view (tools/kl_club_outro_1106.py). Only the .prp inside the zips changes.",
        "the escape heli's INCOMING route is replaced by a %d-point hull-clear route\nending in a hover over the pad's east edge, and Roof .rmi box 7 is enlarged to cover it (tools/kl_arrival_1107.py). Only the .prp inside the zips changes." % len(ROUTE))
    O.TAG = old_tag
    compile(txt, 'install.py', 'exec')
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(txt)
    bat = '@echo off\r\npython "%%~dp0install.py"%s\r\npause\r\n'
    open(os.path.join(out, 'INSTALL arrival 2h 1107.bat'), 'w', newline='').write(bat % '')
    open(os.path.join(out, 'UNDO arrival 2h 1107.bat'), 'w', newline='').write(bat % ' --undo')
    rep = {'in_dir': in_dir, 'in_md5': h, 'incomming_points_before': n, 'route': ROUTE, 'box': [c, hh], 'rmi': {k: v for k, v in info.items() if k != 'old_item'}, 'files': files}
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    log('staged %s plain md5 %s' % (out, plain))
    return rep


def main(a):
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    if not a:
        print(__doc__)
        return 2
    zp = opt('--zip', os.path.join(MAPDIR, 'F01_Main.zip'))
    npz = opt('--npz', os.path.join(OUT, 'dm05a_render.npz'))
    if a[0] == 'geom':
        os.makedirs(os.path.dirname(npz), exist_ok=True)
        region = (np.array([0.0, -2000.0, -12000.0]), np.array([20000.0, 12000.0, 22000.0]))
        t, o, n = geom(zp, region)
        save(opt('--out', npz), t, o, n)
        return 0
    if a[0] == 'plan':
        t, o, n = load(npz)
        keep = [i for i, x in enumerate(n) if 'glow' not in x.lower() and 'distance' not in x.lower()]
        M = Mesh(t[np.isin(o, keep)], o[np.isin(o, keep)], n)
        for kind in ('linear', 'catmull'):
            d, w, ow, L = route_table(M, ROUTE, 150, kind)
            print('ROUTE %s: min clearance %d at %r (%s), length %d' % (kind, d, w, ow[-24:], L))
        return 0
    if a[0] == 'stage':
        stage(opt('--in-dir', MAPDIR), opt('--out', os.path.join(OUT, 'lcarr_2h')), opt('--expect-base'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
