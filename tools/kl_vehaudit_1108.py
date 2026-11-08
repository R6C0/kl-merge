#!/usr/bin/env python3
r"""kl_vehaudit_1108.py - REPORT-ONLY audit of every moving vehicle of a map (2026-11-08, OFFLINE, read-only on the game folder, writes no zip).

Extends kl_vehroutes_1108.py (which measured only the key-framed escape van V_Van_00 of DM01B) to every vehicle that moves by itself:
  KEYED   key-framed vehicle roots (a node with a KEYS chunk and Wheel*/Rotor* children, or named V_*): escape vans, cop-car arrivals, the
          stock maps' ambulances / taxis / trucks. Path = the position keys in key order (legs split at jumps > 400: crash pieces).
  HELI    every ZHeli's route splines (the escape chopper's Incomming / Escaping, DM06's boss chopper, the stock maps' SWAT / police heli).
  CARROUTE a ZHavokCar whose group holds a spline route (VehicleMoveBehaviourRout): Dead Men's AI / civilian / delivery cars.
  TRAFFIC every ZTrafficFlow's spline (cars spawn at its start, are removed at its end; 'Planes!' controllers are the sky traffic).
  PARKED  ZHavokCar without a route (listed only, not measured).
Measured against RENDER triangles (kl_arrival_1107.geom; collision is not what is drawn), the same way kl_vehroutes_1108 proved the DM01B wall:
  PIERCE  a body line segment (cars: lateral 0 / +-100, heights 73 / 163 / 263 over the route point; heli: centre and a ring of 800 at three heights)
          or a vertical column through the body crosses a drawn triangle. Reported per owner: first / last route sample, count, a point.
  TIGHT   (cars only) a route sample whose body points come within 130 of a WALL triangle (|normal.y| < 0.7; floors are dropped so a slope is not a hit).
  ENDS    for the start and the end: OFF-MAP (no drawn triangle within 2500), SEEN (a viewer within 6000 has a clear line to it) or HIDDEN.
          Viewers = the level's ZSpawnPoint places (+ eye 170) plus the vehicle's own stop (a van's creep plateau / a heli's Incomming end).
  SEEN%   share of the route (300 apart) with a clear line from some viewer within 5000 = 'players can see and shoot it' (GUESS: ray against
          drawn triangles, foliage planes and glass count as walls, so it under-reports).
GUESSES (marked in the report too): the engine's spline kind is unknown (linear AND Catmull-Rom are both checked, a finding stands if either
shows it); the spline y of a traffic / car route is the road surface (d0 checked this on DM06B); ZSpawnPoint places stand for 'where players are'.

usage: python kl_vehaudit_1108.py <map id>... [--json out.json] [--maps-dir DIR]     (map id = a folder of KLExpansion\Maps, DM01B, DD05, ...)
"""
import json
import math
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = os.path.join(GAME, 'KLExpansion', 'Maps')
HULL = 130.0
CAR_H = (73.0, 163.0, 263.0)
CAR_LAT = (0.0, 100.0, -100.0)
HELI_H = (0.0, 200.0, 400.0)
HELI_R = 800.0
STEP = 120.0
VIEW_R = 6000.0
SEE_R = 5000.0
EYE = 170.0


def zip_of(mid, maps=MAPS):
    d = os.path.join(maps, mid)
    return os.path.join(d, next(f for f in os.listdir(d) if f.endswith('_Main.zip') and 'bots' not in f))


# ------------------------------------------------------------------------------------------- routes
def keyed_routes(zp, L, B, ME, kl_graft):
    """[(name, kind, [legs of world points])] of the key-framed vehicle roots."""
    sc = B.sc
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    kids = {}
    for k in range(1, len(B.ents) + 1):
        kids.setdefault(sc.parent[k], []).append(k)
    out = []
    for k in range(1, len(B.ents) + 1):
        p = sc.path[k]
        nm = sc.names[k]
        if 'Reflection' in p or re.match(r'Wheel|Rotor|Blade|Door|Pos_|Shadow|V_Coli', nm) or not sc.parent[k]:
            continue
        ch = [sc.names[c] for c in kids.get(k, [])]
        if not (any(re.match(r'Wheel|Rotor|Blade', c) for c in ch) or re.match(r'V_|Heli|Chopper', nm)):
            continue
        if re.search(r'Shadow_Plane', nm) or not kl_graft.keys_tracks(B.ents[k - 1].raw):
            continue
        try:
            K = ME.VanKeys(B.scene.head, B.ents[k - 1].raw, ends, kl_graft.keys_tracks)
        except (ValueError, StopIteration, struct_error()) as e:
            out.append((p[5:], 'KEYED', None, str(e)))
            continue
        R, T = L.frame(sc.parent[k])
        w = lambda q: tuple(T[i] + sum(R[i][j] * q[j] for j in range(3)) for i in range(3))
        legs, cur = [], []
        for q in K.pos:
            if q == (0.0, 0.0, 0.0):
                continue
            q = w(q)
            if cur and math.dist(cur[-1], q) > 400:
                legs.append(cur)
                cur = []
            cur.append(q)
        if cur:
            legs.append(cur)
        out.append((p[5:], 'KEYED', legs, ''))
    return out


def struct_error():
    import struct
    return struct.error


def spline_routes(L, ME, B):
    """HELI, CARROUTE, TRAFFIC routes from the entity tree -> [(name, kind, [legs], note)], plus parked cars [(name, place)]."""
    sc = L.sc
    out, parked, seen = [], [], set()
    for k in range(1, len(sc.nodes)):
        c = sc.cls(k)
        if 'Reflection' in sc.path[k]:
            continue
        if c in ('ZHeli', 'ZHavokCar'):
            top = sc.top[k]
            sp = [j for j in range(top, sc.end[top]) if sc.cls(j) == 'ZEditorSpline']
            routes = []
            for j in sp:
                if c == 'ZHavokCar' and not L.ctrl(sc.parent[j], 'VehicleMoveBehaviourRout'):
                    continue
                if j in seen:
                    continue
                seen.add(j)
                try:
                    routes.append((sc.path[j][5:], ME.spline(L, j)[0]))
                except ValueError:
                    pass
            if not routes and c == 'ZHavokCar':
                parked.append((sc.path[k][5:], tuple(int(x) for x in L.place(k))))
            for name, pts in routes:
                out.append((name, 'HELI' if c == 'ZHeli' else 'CARROUTE', [pts], ''))
        elif c == 'ZTrafficFlow':
            v = L.values(k)
            tgt = v.get('ZTrafficFlow[0]')
            sp = None
            for h in (sc.resolve(tgt) if isinstance(tgt, str) and tgt else []):
                sp = next((j for j in range(h, sc.end[h]) if sc.cls(j) == 'ZEditorSpline'), None)
                if sp is None and sc.cls(h) == 'ZEditorSpline':
                    sp = h
                if sp is not None:
                    break
            if sp is None:
                out.append((sc.path[k][5:], 'TRAFFIC', None, 'spline not resolved'))
                continue
            kind = 'SKY' if 'Planes' in sc.path[k] else 'TRAFFIC'
            cars = v.get('ZTrafficFlow[2]') or []
            note = 'cars %d, max %s, speed %s' % (len(cars), v.get('ZTrafficFlow[1]'), v.get('ZTrafficFlow[4]'))
            out.append((sc.path[k][5:], kind, [ME.spline(L, sp)[0]], note))
    return out, parked


def catmull(pts, n=8):
    import kl_arrival_1107 as A
    return [tuple(float(x) for x in p) for p in A.catmull(pts, n)]


def densify(pts, step=STEP):
    out = []
    for a, b in zip(pts, pts[1:]):
        ln = math.dist(a, b)
        n = max(1, int(ln / step))
        for i in range(n):
            out.append(tuple(a[j] + (b[j] - a[j]) * i / n for j in range(3)))
    out.append(tuple(pts[-1]))
    return out


# ------------------------------------------------------------------------------------------- geometry
def corridor_mesh(t, o, n, paths, viewers, log=print):
    """A Mesh of the render triangles within ~6500 of the route samples (and every big triangle inside the padded box)."""
    import kl_arrival_1107 as A
    pts = []
    for P in paths:
        pts.extend(densify(P, 500.0))
    pts = np.array(pts, float)
    pad = 6500.0
    lo, hi = pts.min(axis=0) - pad, pts.max(axis=0) + pad
    c = t.mean(axis=1)
    cell = 1000.0
    cs = set()
    for p in pts:
        i0, j0 = int(p[0] // cell), int(p[2] // cell)
        for di in range(-7, 8):
            for dj in range(-7, 8):
                cs.add((i0 + di) * 100003 + (j0 + dj))
    key = np.floor(c[:, 0] / cell).astype(np.int64) * 100003 + np.floor(c[:, 2] / cell).astype(np.int64)
    m = np.isin(key, np.fromiter(cs, np.int64))
    ext = (t.max(axis=1) - t.min(axis=1)).max(axis=1)
    big = (ext > 2000) & ((t.max(axis=1) >= lo).all(axis=1)) & ((t.min(axis=1) <= hi).all(axis=1))
    m |= big
    log('    corridor: %d of %d triangles' % (m.sum(), len(t)))
    M = A.Mesh(t[m], o[m], n)
    ny = np.abs(np.cross(M.t[:, 1] - M.t[:, 0], M.t[:, 2] - M.t[:, 0]))
    ln = np.linalg.norm(ny, axis=1)
    M.wall = (ny[:, 1] / np.where(ln > 0, ln, 1)) < 0.7
    return M


def heading(a, b):
    dx, dz = b[0] - a[0], b[2] - a[2]
    h = math.hypot(dx, dz)
    return (dx / h, dz / h) if h > 1e-6 else (1.0, 0.0)


def body_lines(kind, p, hd):
    """Segments (a, b) of the vehicle body at route point p heading hd (x, z)."""
    px, pz = hd[1], -hd[0]
    segs = []
    if kind == 'HELI':
        for dy in HELI_H:
            segs.append(((p[0], p[1] + dy, p[2]), (p[0], p[1] + dy + 1, p[2])))
        for ang in (0, 90, 180, 270):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for dy in HELI_H:
                q = (p[0] + HELI_R * ca, p[1] + dy, p[2] + HELI_R * sa)
                segs.append(((p[0], p[1] + dy, p[2]), q))        # spoke from the centre to the ring (the rotor disc sweeps these)
        return segs
    for lat in CAR_LAT:
        x, z = p[0] + px * lat, p[2] + pz * lat
        for dy in CAR_H:
            segs.append(((x - hd[0] * STEP / 2, p[1] + dy, z - hd[1] * STEP / 2), (x + hd[0] * STEP / 2, p[1] + dy, z + hd[1] * STEP / 2)))
        segs.append(((x, p[1] + 30, z), (x, p[1] + 263, z)))       # the column: a deck / ceiling over the body
    return segs


def batch_hits(M, ks, segs):
    """[(segment index, owner)] of the triangles ks (indices into M) pierced by any of segs [(p, q)] (Moller-Trumbore, two-sided, one vector pass per segment)."""
    T = M.t[ks]
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    out = []
    for si, (p, q) in enumerate(segs):
        p, d = np.array(p, float), np.array(q, float) - np.array(p, float)
        h = np.cross(d, e2)
        det = (e1 * h).sum(1)
        ok = np.abs(det) > 1e-9
        det = np.where(ok, det, 1)
        sv = p - T[:, 0]
        u = (sv * h).sum(1) / det
        qv = np.cross(sv, e1)
        v = (d * qv).sum(1) / det
        t = (e2 * qv).sum(1) / det
        m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)
        out.extend((si, M.names[M.o[ks[i]]]) for i in np.nonzero(m)[0])
    return out


def check_route(M, kind, legs, flat=False, step=STEP):
    """-> (pierces {owner: [first, last, n, point]}, tight {owner: [first, last, min gap, point]}, samples). One candidate gather per route sample."""
    import kl_arrival_1107 as A
    pierce, tight, idx = {}, {}, 0
    reach = 950.0 if kind == 'HELI' else 450.0
    for leg in legs:
        dens = densify(leg, step)
        for a, b in zip(dens, dens[1:] + dens[-1:]):
            idx += 1
            ks = M.near(a, reach)
            if not len(ks):
                continue
            hd = heading(a, b)
            for si, ow in batch_hits(M, ks, body_lines(kind, a, hd)):
                ow = ow.split(chr(92))[-1][:60]
                r = pierce.setdefault(ow, [idx - 1, idx - 1, 0, tuple(int(x) for x in a)])
                r[1] = idx - 1
                r[2] += 1
            if kind != 'HELI':
                kw = ks[M.wall[ks]]
                for dy in (73.0, 163.0):
                    q = np.array((a[0], a[1] + dy, a[2]), float)
                    k2 = kw[((M.lo[kw] - HULL) <= q).all(axis=1) & ((M.hi[kw] + HULL) >= q).all(axis=1)] if len(kw) else kw
                    if len(k2):
                        d = A.point_tri(q, M.t[k2])
                        i = int(np.argmin(d))
                        if d[i] < HULL:
                            ow = M.names[M.o[k2[i]]].split(chr(92))[-1][:60]
                            r = tight.setdefault(ow, [idx - 1, idx - 1, float(d[i]), tuple(int(x) for x in a)])
                            r[1] = idx - 1
                            r[2] = min(r[2], float(d[i]))
    return pierce, tight, idx


def seen_from(M, viewers, p, r=VIEW_R):
    """Number of viewers within r with an unobstructed line to p (+60 up)."""
    import kl_arrival_1107 as A
    n, tot = 0, 0
    q = (p[0], p[1] + 100.0, p[2])
    near = sorted((math.dist(v, q), v) for v in viewers if math.dist(v, q) < r)[:10]
    for d, v in near:
        tot += 1
        if not A.seg_hits(M, (v[0], v[1] + EYE, v[2]), q):
            n += 1
    return n, tot


def end_state(M, viewers, p):
    d, _ = M.dist(tuple(p), 2500.0)
    if d >= 2500.0:
        return 'OFF-MAP (no drawn surface within 2500)'
    n, tot = seen_from(M, viewers, p)
    if tot == 0:
        return 'no viewer within %d' % VIEW_R
    return ('SEEN by %d of %d viewers' % (n, tot)) if n else 'HIDDEN (0 of %d viewers see it)' % tot


def seen_share(M, viewers, pts):
    dens = densify(pts, 300.0)
    ok = 0
    for p in dens:
        n, tot = seen_from(M, viewers, p, SEE_R)
        ok += 1 if n else 0
    return 100.0 * ok / max(1, len(dens)), len(dens)


def stop_of(pts):
    """The creep plateau farthest from the start (a van waits, drives in, stops): the longest run of near-equal keys after the first move."""
    best, run = None, 1
    for i in range(1, len(pts)):
        if math.dist(pts[i], pts[i - 1]) < 8:
            run += 1
        else:
            run = 1
        if run >= 4 and (best is None or math.dist(pts[i], pts[0]) > math.dist(best, pts[0])):
            best = pts[i]
    return best


# ------------------------------------------------------------------------------------------- one map
def audit_map(mid, maps=MAPS, log=print):
    import kl_arrival_1107 as A
    import kl_fa_bots as F
    import kl_graft
    import kl_map_escape as ME
    t0 = time.time()
    zp = zip_of(mid, maps)
    L = ME.Level(zp)
    B = F.Built(zp)
    sc = L.sc
    rows = []
    for name, kind, legs, err in keyed_routes(zp, L, B, ME, kl_graft):
        rows.append(dict(name=name, kind=kind, legs=legs, note=err))
    sroutes, parked = spline_routes(L, ME, B)
    for name, kind, legs, note in sroutes:
        rows.append(dict(name=name, kind=kind, legs=legs, note=note))
    viewers = [tuple(L.place(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and 'Reflection' not in sc.path[k]]
    viewers = [v for v in viewers if v != (0.0, 0.0, 0.0)]
    paths = [leg for r in rows if r['legs'] for leg in r['legs'] if len(leg) > 1 and r['kind'] != 'SKY']
    res = dict(map=mid, zip=zp, vehicles=[], parked=parked, viewers=len(viewers))
    if not paths:
        return res
    t, o, n = A.geom(zp, log=lambda *a: None)
    t, o = np.asarray(t), np.asarray(o)
    keep = [i for i, x in enumerate(n) if 'glow' not in x.lower() and 'distance' not in x.lower()]
    ok = np.isfinite(t).all(axis=(1, 2)) & (np.abs(t).max(axis=(1, 2)) < 1e6) & np.isin(o, keep)
    t, o = t[ok], o[ok]
    M = corridor_mesh(t, o, n, paths, viewers, log)
    del t, o
    for r in rows:
        v = dict(name=r['name'], kind=r['kind'], note=r['note'])
        if not r['legs']:
            res['vehicles'].append(v)
            continue
        legs = [l for l in r['legs'] if len(l) > 1]
        if not legs:
            v['note'] += ' (a single key, does not move)'
            res['vehicles'].append(v)
            continue
        main = legs[0]
        v['start'] = tuple(int(x) for x in main[0])
        v['end'] = tuple(int(x) for x in main[-1])
        v['length'] = int(sum(math.dist(a, b) for l in legs[:1] for a, b in zip(l, l[1:])))
        v['legs'] = len(legs)
        if r['kind'] == 'SKY':
            res['vehicles'].append(v)
            continue
        vw = list(viewers)
        stop = None
        if r['kind'] == 'KEYED':
            stop = stop_of(main)
        elif r['kind'] == 'HELI' and 'ncom' in r['name']:
            stop = main[-1]
        if stop:
            vw.append(tuple(stop))
            v['stop'] = tuple(int(x) for x in stop)
        v['start_state'] = end_state(M, vw, main[0])
        v['end_state'] = end_state(M, vw, main[-1])
        v['seen_pct'], _ = seen_share(M, vw, main)
        variants = [('linear', legs)]
        if r['kind'] in ('HELI', 'CARROUTE', 'TRAFFIC'):
            variants.append(('catmull', [catmull(l) for l in legs]))
        v['pierce'], v['tight'] = {}, {}
        for vn, lg in variants:
            pierce, tight, ns = check_route(M, 'HELI' if r['kind'] == 'HELI' else 'CAR', lg, False, 300.0 if r['kind'] in ('HELI', 'TRAFFIC') else STEP)
            for ow, x in pierce.items():
                v['pierce'].setdefault(ow, dict(x=x, how=vn))
            for ow, x in tight.items():
                v['tight'].setdefault(ow, dict(x=x, how=vn))
        v['pierce'] = {k: dict(first=d['x'][0], last=d['x'][1], n=d['x'][2], at=d['x'][3], how=d['how']) for k, d in v['pierce'].items()}
        v['tight'] = {k: dict(first=d['x'][0], last=d['x'][1], gap=int(d['x'][2]), at=d['x'][3], how=d['how']) for k, d in v['tight'].items()}
        res['vehicles'].append(v)
        log('  %-9s %-60s %s' % (r['kind'], r['name'][-60:], summary(v)))
    res['seconds'] = round(time.time() - t0)
    return res


def summary(v):
    s = 'len %s start %s [%s] end %s [%s] seen %.0f%%' % (v.get('length'), v.get('start'), v.get('start_state'), v.get('end'), v.get('end_state'), v.get('seen_pct', 0))
    if v.get('pierce'):
        s += ' PIERCES ' + ', '.join('%s keys %d..%d x%d at %s (%s)' % (k, d['first'], d['last'], d['n'], d['at'], d['how']) for k, d in list(v['pierce'].items())[:4])
    return s


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    maps = MAPS
    out = None
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        a = [x for x in a if x != out]
    if '--maps-dir' in sys.argv:
        maps = sys.argv[sys.argv.index('--maps-dir') + 1]
        a = [x for x in a if x != maps]
    allres = []
    for mid in a:
        print('==', mid, flush=True)
        r = audit_map(mid, maps)
        allres.append(r)
        print('  %d vehicles, %d parked cars, %d viewers, %ss' % (len(r['vehicles']), len(r['parked']), r['viewers'], r.get('seconds')), flush=True)
        if out:
            json.dump(allres, open(out, 'w'), indent=1)
