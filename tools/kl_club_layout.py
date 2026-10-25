#!/usr/bin/env python3
"""kl_club_layout.py - Last Call (DM05A) crowd layout: floors, free standing cells, capacity, allocation for 70 / 90 / 110 civilians. READ-ONLY.

  python tools/kl_club_layout.py <folder holding the live F01_Main.zip (+ .hti, KLJoin.ini)> <out folder> [--wall 60] [--sep 130]

Writes only <out folder>/layout.json (floors, clusters, capacity) and <out folder>/places_<N>.json (N = 70, 90, 110: the NEW civilians' places,
on top of the civilians already in the zip). Never touches the zip, the game folder or any backup.

HOW (2026-10-25, owner: "40 people bruh theres two floors needs way more than 40 people")
 - Samples every nav-mesh polygon of the play part (the mesh part holding the START spawns) on a 55-unit grid, keeps FLAT polygons (y spread < 25,
   stairs are skipped), >= WALL from a mesh edge without neighbour at that height (default 60, as kl_fa_civs.plan_places), >= 150 from every
   LevelBound box, >= 600 (the 450 run box + 150) from every START spawn in x, z and y.
 - Floors are y bands (GUESS: bands read off the sample histogram, matched to the Dead Men crowd rooms by their centres): ground 20..60,
   balcony 340..380, upper 460, third 760..880, office 1060, roof 1460, pad 1900.
 - Clusters = the four Dead Men HFlow rooms of M05_A (re/campaign_fa_club.md 1.5), same x/z in DM05A: dance floor (601, 1614) ground, lounge
   (703, 1055) upper, rave (-3182, 800) upper, lounge+rave (-1188, 1100) third. The ground dance floor is the nominal centre; the radius is a GUESS.
 - Allocation weights are a GUESS (Dead Men's capacities 750 / 100 / 700 / 300 reduced to a share, then capped by the free cells of each cluster).
"""
import collections
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as F
import kl_fa_civs as C

STEP = 55.0
BANDS = [('ground', -50, 70), ('balcony', 300, 420), ('upper', 430, 520), ('third', 720, 900), ('office', 1000, 1100), ('roof', 1400, 1600), ('pad', 1850, 1950)]
# (name, floor, x, z, radius, Dead Men capacity). Centres are Dead Men's HFlow object places (re/campaign_fa_club.md 1.5); radius is a GUESS.
CLUSTERS = [('dance floor', 'ground', 601.0, 1614.0, 1300.0, 750), ('lounge', 'upper', 703.0, 1055.0, 900.0, 100),
            ('rave', 'upper', -3182.0, 800.0, 1300.0, 700), ('lounge+rave', 'third', -1188.0, 1100.0, 1500.0, 300)]
TARGETS = (70, 90, 110)
FLOORY = dict(ground=40.0, upper=460.0, third=860.0)   # representative floor heights of the cluster floors


def floor_of(y):
    for n, lo, hi in BANDS:
        if lo <= y <= hi:
            return n
    return None


def pip(x, z, vs):
    c, n = False, len(vs)
    for i in range(n):
        a, b = vs[i], vs[(i + 1) % n]
        if (a[2] > z) != (b[2] > z) and x < (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2]) + a[0]:
            c = not c
    return c


def free_cells(B, nav, wall_min):
    """-> (cells [(x, y, z, floor)], actors [(kind, x, y, z)], the play part). One entry per 55-unit grid point."""
    area = C.play_area(B, nav)
    part = area['part']
    W = np.array(nav.walls)
    bounds, starts = C.bound_boxes(B), C.start_points(B)

    def wall_d(x, z, y):
        w = W[np.abs(W[:, 4] - y) < 150]
        if not len(w):
            return 1e9
        dx, dz = w[:, 2] - w[:, 0], w[:, 3] - w[:, 1]
        L = dx * dx + dz * dz
        L[L == 0] = 1
        t = np.clip(((x - w[:, 0]) * dx + (z - w[:, 1]) * dz) / L, 0, 1)
        return float(np.min(np.hypot(x - w[:, 0] - t * dx, z - w[:, 1] - t * dz)))

    cells = []
    for i, vs in enumerate(nav.pv):
        if not nav.ok[i] or nav.part[i] != part:
            continue
        ys = [v[1] for v in vs]
        if max(ys) - min(ys) >= 25:
            continue                                   # stairs / ramps
        y = nav.mid[i][1]
        fl = floor_of(y)
        if fl is None:
            continue
        bx = nav.box[i]
        x = math.ceil(bx[0] / STEP) * STEP
        while x <= bx[1]:
            z = math.ceil(bx[2] / STEP) * STEP
            while z <= bx[3]:
                if pip(x, z, vs) and wall_d(x, z, y) >= wall_min and C.in_bound(B, bounds, (x, y, z), 150.0) is None \
                        and all(not (abs(x - s[0]) < 600 and abs(z - s[2]) < 600 and abs(y - s[1]) < 600) for s in starts):
                    cells.append((x, y, z, fl))
                z += STEP
            x += STEP
    acts = []
    sc = B.sc
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor':
            p = B.at(k)
            acts.append(('civ' if kl_fa.has(sc, k, 'ZCivilian') else 'man', float(p[0]), float(p[1]), float(p[2])))
    return cells, acts, part


def pack(rs, sep, taken=()):
    """Greedy: centre-most first, keep a cell >= sep from every kept one and from `taken` (x, z) points."""
    acc = []
    pts = list(taken)
    for r in rs:
        if all((r[0] - a[0]) ** 2 + (r[2] - a[1]) ** 2 >= sep * sep - 1 for a in pts):
            acc.append(r)
            pts.append((r[0], r[2]))
    return acc


def spread(rs, n, sep, taken):
    """n cells from rs, each >= sep from the rest and `taken`, spread by farthest-point choice (not the first n of a sorted list)."""
    pts = list(taken)                                  # (x, z, y): a point blocks only cells on its own floor (|dy| < 200)
    out = []

    def clear(r, pts):
        return all((r[0] - a[0]) ** 2 + (r[2] - a[1]) ** 2 >= sep * sep - 1 or abs(r[1] - a[2]) >= 200 for a in pts)
    pool = [r for r in rs if clear(r, pts)]
    if not pool:
        return out
    # start from the cell nearest the cluster centroid, then farthest-first among cells that still fit (a dense, even fill)
    cx, cz = sum(r[0] for r in pool) / len(pool), sum(r[2] for r in pool) / len(pool)
    pool.sort(key=lambda r: (r[0] - cx) ** 2 + (r[2] - cz) ** 2)
    while pool and len(out) < n:
        r = pool.pop(0)
        out.append(r)
        pool = [q for q in pool if (q[0] - r[0]) ** 2 + (q[2] - r[2]) ** 2 >= sep * sep - 1]
    return out


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    src, dst = a[0], a[1]
    wall = float(a[a.index('--wall') + 1]) if '--wall' in a else 60.0
    sep = float(a[a.index('--sep') + 1]) if '--sep' in a else 130.0
    os.makedirs(dst, exist_ok=True)
    B = F.Built(src, 'F01')
    nav = F.Nav(B.scene.nav)
    cells, acts, part = free_cells(B, nav, wall)
    civs = [(x, z, y) for k, x, y, z in acts if k == 'civ']
    men = [(x, z, y) for k, x, y, z in acts if k == 'man']
    print('play part %d: %d free cells (55-grid, wall >= %g)' % (part, len(cells), wall))
    print('actors %d = %d civilians + %d men' % (len(acts), len(civs), len(men)))
    # clusters: assign a cell to the nearest cluster centre on its floor within the radius
    per = collections.defaultdict(list)
    for c in cells:
        best = None
        for nm, fl, cx, cz, rad, dm in CLUSTERS:
            if fl == c[3]:
                d = math.hypot(c[0] - cx, c[2] - cz)
                if d <= rad and (best is None or d < best[0]):
                    best = (d, nm)
        # GUESS: ground cells south of z 600 are the street/pavement (START spawns are at z -2790), not the club
        per[best[1] if best else ('street' if c[3] == 'ground' and c[2] < 600 else 'other:' + c[3])].append(c)
    report = {}
    taken = list(civs) + list(men)                  # already occupied (civilians and men): new ones keep sep from them on their floor
    print('%-16s %6s %8s %8s %8s %6s' % ('area', 'cells', 'm2', 'cap110', 'cap%g' % sep, 'civs'))
    for nm in sorted(per):
        rs = sorted(per[nm], key=lambda r: (r[0], r[2]))
        c110 = len(pack(rs, 110.0))
        csep = len(pack(rs, sep))
        xs, zs = [r[0] for r in rs], [r[2] for r in rs]
        report_y = sum(r[1] for r in rs) / len(rs) if rs else 0
        have = sum(1 for x, z, y in civs if min(xs) - 60 <= x <= max(xs) + 60 and min(zs) - 60 <= z <= max(zs) + 60 and abs(y - report_y) < 200) if rs else 0
        report[nm] = dict(cells=len(rs), area_m2=round(len(rs) * STEP * STEP / 1e4), cap_110=c110, cap_sep=csep, civs_now=have,
                          x=[min(xs), max(xs)], z=[min(zs), max(zs)], y=round(sum(r[1] for r in rs) / len(rs)))
        print('%-16s %6d %8d %8d %8d %6d' % (nm, len(rs), report[nm]['area_m2'], c110, csep, have))
    fl = collections.defaultdict(lambda: [0, 0, 0, 0])
    for nm, r in report.items():
        f = 'street' if nm == 'street' else (nm.split(':')[1] if nm.startswith('other:') else dict((c[0], c[1]) for c in CLUSTERS)[nm])
        for i, key in enumerate(('area_m2', 'cap_110', 'cap_sep', 'civs_now')):
            fl[f][i] += r[key]
    print('per floor (club cells only): floor, m2, cap110, cap%g, civilians now' % sep)
    for f in sorted(fl):
        print('  %-8s %5d %6d %6d %4d' % ((f,) + tuple(fl[f])))
    json.dump(dict(part=part, wall=wall, sep=sep, areas=report), open(os.path.join(dst, 'layout.json'), 'w'), indent=1)
    # allocation: the NEW civilians (target - len(civs)) by weight over the four clusters, capped by free spots at `sep`
    weights = {nm: dm for nm, fl, cx, cz, rad, dm in CLUSTERS}
    for tgt in TARGETS:
        need = tgt - len(civs)
        wsum = float(sum(weights.values()))
        # existing civilians count toward their cluster's share (by nearest cluster centre on any floor): GUESS, simple
        share = {nm: tgt * weights[nm] / wsum for nm in weights}
        have = collections.Counter()
        for x, z, y in civs:
            have[min(CLUSTERS, key=lambda c: math.hypot(x - c[2], z - c[3]) + (0 if abs(y - FLOORY[c[1]]) < 200 else 1e6))[0]] += 1
        want = {nm: max(0, int(round(share[nm])) - have[nm]) for nm in weights}
        # fix rounding so the total is exactly `need`: add/remove at the largest shares
        order = sorted(weights, key=lambda n: -weights[n])
        while sum(want.values()) < need:
            want[order[sum(want.values()) % len(order)]] += 1
        while sum(want.values()) > need:
            n = max(want, key=lambda k: want[k])
            want[n] -= 1
        placed, used = [], list(taken)
        for nm in order:
            got = spread(per.get(nm, []), want[nm], sep, used)
            for r in got:
                used.append((r[0], r[2], r[1]))
                placed.append(dict(pos=[r[0], round(r[1], 1), r[2]], floor=r[3], cluster=nm))
        out = os.path.join(dst, 'places_%d.json' % tgt)
        json.dump(dict(target=tgt, existing=len(civs), new=len(placed), wanted=want, places=placed), open(out, 'w'), indent=1)
        print('target %3d: +%d wanted %s -> placed %d (%s)' % (tgt, need, dict(want), len(placed), collections.Counter(p['floor'] for p in placed)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
