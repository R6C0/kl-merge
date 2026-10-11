"""Test spots for the loader climb in M01, checked against the level's collision with an offline copy of the probe.
Writes scripts/climb_spots.json for smoke_climb.py. Every spot: where Kane is teleported (feet, world cm) and his
yaw, so that he stands ~60 cm in front of a face, facing it. The probe (loader/climb.inc climb_probe, DM 0x605b50)
is simulated with feet 60, 45 and 30 cm from the face (W pushes him in until his capsule stops him).
Yaw convention (same as the loader's 'tp:' and 'pos:' lines): forward F = (sin yaw, 0, cos yaw); 0 = +z, 90 = +x.
The collision model (hvk_ray.py, conv 'col') reproduces the in-game rays of the 11 Oct 06:02 dry press to 0.2 cm.
usage: climb_spots.py [level.zip] [--all]   (--all also prints every candidate face it rejected)"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hvk_ray
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = next((a for a in sys.argv[1:] if not a.startswith('--')),
           r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\Scenes\Locations\M01\M01_Main.zip')
SHOW_ALL = '--all' in sys.argv
CLS = [('Low', 120, 81), ('Medium', 170, 47), ('High', 220, 47)]


def add(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


def probe(C, Pf, F):
    """climb_probe on the offline collision -> (result, class, h, detail)."""
    B = (-F[0], 0.0, -F[2]); rr = 25.0; cand = []
    for i in range(4):
        o = (Pf[0] + F[0] * (rr + 15 * i), Pf[1] + 310, Pf[2] + F[2] * (rr + 15 * i))
        r = C.ray(o, (0, -310, 0), 0x20)
        if not r:
            continue
        if r['type'] == 'RIGID':
            return 'abort:rigid', None, 0, r['name']
        cand.append((r['hit'][1] - Pf[1], r['hit'], i, r['name']))
    cur = 0.0
    for k, (h, hit, i, nm) in enumerate(cand):
        if h < cur:
            continue
        cur = h
        o = (Pf[0] + B[0] * 15, Pf[1] + h + 15, Pf[2] + B[2] * 15)
        c1 = C.ray(o, (F[0] * (rr + 15 * (i + 2)), 0, F[2] * (rr + 15 * (i + 2))), 0x28)
        if c1:
            continue
        c2 = C.ray((hit[0], hit[1] + 1, hit[2]), (0, 180, 0), 0x20)
        if c2:
            return 'abort:headroom', None, h, c2['name']
        o = (Pf[0] + B[0] * 10, Pf[1] + h - 1, Pf[2] + B[2] * 10)
        c3 = C.ray(o, (F[0] * (rr + 15 * i + 20), 0, F[2] * (rr + 15 * i + 20)), 0x20)
        if not c3:
            continue
        if h <= 25:
            continue
        for name, mx, off in CLS:
            if h <= mx:
                return 'OK', name, h, '%s (wall %s)' % (nm, c3['name'])
        return 'abort:too high', None, h, nm
    return 'none', None, 0, '%d candidates' % len(cand)


def ground(C, x, y_hint, z):
    r = C.ray((x, y_hint + 120, z), (0, -320, 0), 0x28)
    return (r['hit'][1], r['name']) if r and r['n'][1] > 0.7 else (None, r and r['name'])


def standing(C, p):
    """Problems with standing at feet p (ceiling below 1.95 m, something within 30 cm at knee/waist/head)."""
    bad = []
    r = C.ray((p[0], p[1] + 5, p[2]), (0, 190, 0), 0x28)
    if r:
        bad.append('ceiling %s at +%.0f' % (r['name'], r['hit'][1] - p[1]))
    for hgt in (40, 100, 160):
        for k in range(8):
            a = k * math.pi / 4
            r = C.ray((p[0], p[1] + hgt, p[2]), (30 * math.sin(a), 0, 30 * math.cos(a)), 0x28)
            if r:
                bad.append('%s within 30 cm at +%d' % (r['name'], hgt)); break
    return bad


def face_spots(C, inst, top_rel=None):
    """Faces of a box-like placement, one per local horizontal axis direction: a horizontal ray toward the
    centre at (top - 20) finds the face point and normal. -> [(F, face point)]"""
    lo, hi = inst.lo, inst.hi
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    y = (hi[1] - 20) if top_rel is None else top_rel
    R = inst.R; out = []
    for ax in ((1, 0, 0), (0, 0, 1)):
        d = C.dir_world(inst, ax); L = math.hypot(d[0], d[2])
        d = (d[0] / L, 0.0, d[2] / L)
        for s in (1, -1):
            o = (cx + d[0] * s * 400, y, cz + d[2] * s * 400)
            r = C.ray(o, (-d[0] * s * 400, 0, -d[2] * s * 400), 0x20)
            if not r or r['ref'] != inst.ref:
                continue
            n = r['n']; L = math.hypot(n[0], n[2])
            if L < 0.9:
                continue
            out.append(((-n[0] / L, 0.0, -n[2] / L), r['hit']))
    return out


def evaluate(C, name, expect, F, W, y_hint, d=60.0, target=None, note=''):
    """A spot d cm in front of face point W, facing F. -> dict (with 'ok')."""
    x, z = W[0] - F[0] * d, W[2] - F[2] * d
    gy, gname = ground(C, x, y_hint, z)
    res = dict(name=name, expect=expect, ok=False, note=note)
    if gy is None:
        res['why'] = 'no ground (%s)' % gname; return res
    p = (x, gy + 2.0, z)
    yaw = math.degrees(math.atan2(F[0], F[2])) % 360
    sims = {}
    for dd in (60, 45, 30):
        pf = (W[0] - F[0] * dd, gy, W[2] - F[2] * dd)
        r, cls, h, det = probe(C, pf, F)
        sims['d%d' % dd] = '%s%s h=%.1f %s' % (r, ' ' + cls if cls else '', h, det)
        sims['_r%d' % dd] = (r, cls)
    st = standing(C, p)
    app = C.ray((p[0], gy + 100, p[2]), (F[0] * (d + 40), 0, F[2] * (d + 40)), 0x28)
    res.update(x=round(p[0], 1), y=round(p[1], 1), z=round(p[2], 1), yaw=round(yaw, 1), ground=gname,
               face=[round(v, 1) for v in W], target=target,
               approach='%s at %.0f cm (waist ray)' % (app['name'], math.hypot(app['hit'][0] - p[0], app['hit'][2] - p[2])) if app else 'clear to %d cm' % (d + 40),
               standing='ok' if not st else '; '.join(st[:3]),
               sim={k: v for k, v in sims.items() if not k.startswith('_')})
    want = ('abort:too high', None) if expect == 'too high' else ('OK', expect)
    res['ok'] = all(sims['_r%d' % dd] == want for dd in (60, 45, 30)) and not st
    res['score'] = sum(sims['_r%d' % dd] == want for dd in (60, 45, 30)) - len(st)
    return res


def best_face(C, name, expect, pats, prefer_near=(-621.8, -14.0, -9156.0), extra=None):
    """Try every face of every placement whose name matches one of pats; best = all sims as expected,
    then nearest to prefer_near (the M01 player start: sections near it are the safest bet)."""
    tried = []
    for inst in C.insts:
        nm = C.name(inst.ref)
        if not any(p == nm or (p.endswith('*') and nm.startswith(p[:-1])) for p in pats):
            continue
        if extra and not extra(inst):
            continue
        for F, W in face_spots(C, inst):
            r = evaluate(C, name, expect, F, W, inst.lo[1], target='%s (ref %d, %s)' % (nm, inst.ref, C.name(inst.ref, True).split('\\')[-2]))
            r['dist_start'] = round(math.hypot(r.get('x', 0) - prefer_near[0], r.get('z', 0) - prefer_near[2]))
            tried.append(r)
    tried.sort(key=lambda r: (-r.get('score', -9), r['dist_start']))
    if SHOW_ALL:
        for r in tried:
            print('   cand %-14s %s' % (name, json.dumps({k: r.get(k) for k in ('ok', 'target', 'x', 'y', 'z', 'yaw', 'sim', 'standing', 'approach', 'why')})))
    return tried


def main():
    C = hvk_ray.Collision(ZIP, 'col')
    spots, alts = [], []
    # (a) van rear, from the ground: the van's HeroOnly hull, rear face (doors at z ~2238), facing +z
    van = next(i for i in C.insts if C.name(i.ref) == 'HeroOnly_01' and C.name(i.ref, True).endswith('Climb_01\\HeroOnly_01'))
    vx = (van.lo[0] + van.hi[0]) / 2
    r = C.ray((vx, 150, van.lo[2] - 300), (0, 0, 400), 0x20)
    F = (0.0, 0.0, 1.0)
    spots.append(evaluate(C, 'van_rear', 'High', F, r['hit'], 0.0, target='%s (ref %d) rear' % (r['name'], r['ref']),
                          note='van rear doors from the ground; DM ZFFPlayerMovementClimb High'))
    # (b) on the van roof facing the shelter (roof slab edge z ~2637.6, top y ~345.8): Medium h ~144
    sh = C.ray((vx, 330, 2500), (0, 0, 400), 0x20)
    spots.append(evaluate(C, 'van_top_shelter', 'Medium', F, sh['hit'], 205.0, target='%s (ref %d) front edge' % (sh['name'], sh['ref']),
                          note='teleported onto the van roof in front of the bus shelter; the hero-only barrier '
                               'ColiObj_obj_Hero (z 2373 at roof height) is behind him'))
    # (c) Crate_C (99 high, Low), (d) Crate_A (130, Medium)
    for name, expect, pats in (('crate_c', 'Low', ['PC0300_USA_Crate_C_*']), ('crate_a', 'Medium', ['PC0300_USA_Crate_A_*'])):
        t = best_face(C, name, expect, pats, extra=lambda i: abs(i.lo[1]) < 20 or True)
        good = [r for r in t if r['ok']]
        spots.append(good[0] if good else t[0])
        if len(good) > 1:
            a = dict(good[1]); a['name'] = name + '_alt'; alts.append(a)
    # (e) Crate_B lying on two Crate_As (StripmallBack, top 179): High. The B is narrower: approach along the B's long side.
    t = best_face(C, 'crate_stack', 'High', ['PC0300_USA_Crate_A_*', 'PC0300_USA_Crate_C_*'],
                  extra=lambda i: any(C.name(j.ref).startswith('PC0300_USA_Crate_') and j.lo[1] > 90 and
                                      j.lo[0] < i.hi[0] and j.hi[0] > i.lo[0] and j.lo[2] < i.hi[2] and j.hi[2] > i.lo[2]
                                      for j in C.insts))
    good = sorted([r for r in t if r['ok']], key=lambda r: 'Crate_B' not in r['sim']['d60'])   # B on A first (DM's yard stack)
    spots.append(good[0] if good else t[0])
    if len(good) > 1:
        a = dict(good[1]); a['name'] = 'crate_stack_alt'; alts.append(a)
    # (f) too high: the prisoner transport roof the 06:02 dry press hit (h 239.9, abort:too high in game);
    # plus the best plain wall with a top 230..300 cm above the street
    Fp = (0.93, 0.0, -0.36); L = math.hypot(Fp[0], Fp[2]); Fp = (Fp[0] / L, 0.0, Fp[2] / L)
    tr = C.ray((-621.8 - Fp[0] * 10, -14.0 + 238.9, -9156.0 - Fp[2] * 10), (Fp[0] * 75, 0, Fp[2] * 75), 0x20)
    spots.append(evaluate(C, 'truck_too_high', 'too high', Fp, tr['hit'], -14.0, d=50.0,
                          target='%s (ref %d)' % (tr['name'], tr['ref']),
                          note='the in-game dry press of 11 Oct 06:02 (RESULT abort:too high h=239.9) from the same place'))
    walls = []
    for inst in C.insts:
        if inst.shape.type != 1 or inst.shape.convex:
            continue
        hgt = inst.hi[1] - inst.lo[1]
        if not (225 <= hgt <= 300) or max(inst.hi[0] - inst.lo[0], inst.hi[2] - inst.lo[2]) < 150:
            continue
        for F2, W in face_spots(C, inst):
            r = evaluate(C, 'wall_too_high', 'too high', F2, W, inst.lo[1], target='%s (ref %d, %s)' % (C.name(inst.ref), inst.ref, C.name(inst.ref, True).split('\\')[-2]))
            r['dist_start'] = round(math.hypot(r.get('x', 0) + 621.8, r.get('z', 0) + 9156.0))
            walls.append(r)
    walls.sort(key=lambda r: (-r.get('score', -9), r['dist_start']))
    if SHOW_ALL:
        for r in walls[:40]:
            print('   cand wall %s' % json.dumps({k: r.get(k) for k in ('ok', 'target', 'x', 'y', 'z', 'yaw', 'sim', 'standing')}))
    if walls:
        spots.append(walls[0])
        okw = [w for w in walls if w['ok'] and w['target'] != walls[0]['target']]
        if okw:
            a = dict(okw[0]); a['name'] = 'wall_too_high_alt'; alts.append(a)
    for s in spots + alts:
        s.pop('score', None)
    out = dict(level='M01', zip=ZIP, yaw='F = (sin yaw, 0, cos yaw), degrees; 0 = +z, 90 = +x (loader tp/pos lines)',
               coords='feet, world cm, y up; y = ground + 2', model='scripts/hvk_ray.py conv col (matches in-game rays)',
               spots=spots + alts)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'climb_spots.json')
    json.dump(out, open(path, 'w'), indent=1)
    for s in spots + alts:
        print('%-18s %-8s ok=%-5s (%s, %s, %s) yaw %s  %s' % (s['name'], s['expect'], s['ok'], s.get('x'), s.get('y'), s.get('z'), s.get('yaw'), s.get('target')))
        print('%18s sim %s | standing %s | approach %s' % ('', s.get('sim'), s.get('standing'), s.get('approach')))
    print('->', path)


if __name__ == '__main__':
    main()
