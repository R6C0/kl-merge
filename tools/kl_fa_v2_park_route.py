"""kl_fa_v2_park_route.py - Park II (DM06B, kl_fa_v2_park.py): can the crew WALK from the START rows to the loot, the stairs and the van? (OFFLINE)

kl-merge-e5, 2026-10-18. Template: kl_fa_v2_hc_route2.py (Hot Coffee II). Does not edit kl_fa_v2_park.py (kl-merge-3f's); reads its constants.
  python kl_fa_v2_park_route.py walk <finished folder or F02_Main.zip> [--cell 40] [--step 65] [--drop <path substring> ...] [--nocam] [--ramps] [--start-y 636] [--near 600]
Read-only. Floods (kl_walk2d's model, GUESS: coarse) from START, but keeping the HEIGHT of every state (the pagoda has several floors), then reports for
each station (loot cases, bridge, stairs foot / top, van stop / boarding place) whether a reached floor lies within 1 step of its height, and names the steep
collision pieces that wall the frontier cells (top-level subtree / entity), as kl_fa_v2_hc_route2 does.
  python kl_fa_v2_park_route.py mesh <finished folder or F02_Main.zip>     the AI's way over the navigation mesh, leg by leg, sampled against the collision (kl_route.mesh_way)
  python kl_fa_v2_park_route.py joinini <live folder> <OUT folder>     OPT-IN: OUT = copy of the folder (no *.before-* files) + a KLJoin.ini with two crew hops (see joinini_text)
--nocam: ignore shapes whose every .HVK flag is 0x40 (camera-only collision, GUESS from Hot Coffee II's twin-name pairs).
"""
import collections, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BOX = (-10200.0, 10200.0, -13200.0, 4200.0)     # x0, x1, z0, z1: the pagoda (z 2300) .. the stairs (z -10940) .. the ring (r 8244 about (0,-100)); GUESS: a margin
STATION_TOL = 90.0                              # a station counts as reached when a reached floor is within this height of its y (and within 1 cell). GUESS


def stations(P):
    """Name -> (x, y, z) from the module's own constants."""
    s = collections.OrderedDict()
    s['START row 0'] = P.START[0]
    s['START row 1 end'] = P.START[-1]
    for i, (pos, _yaw, _val, what) in enumerate(P.LOOT):
        s['loot %02d %s' % (i, what)] = pos
    s['bridge landing'] = P.BRIDGE
    s['sniper'] = P.SNIPER
    s['stairs foot'] = P.STAIRS_FOOT
    s['stairs top'] = P.STAIRS_TOP
    s['van stop'] = P.STOP
    s['van boarding place'] = P.BOARD_AT
    return s


def _camera_only_ground():
    import kl_map_escape as ESC, kl_hvk
    Base = ESC.Ground

    class Ground(Base):
        def __init__(self, L):
            Base.__init__(self, L)
            cam = set(kl_hvk.ref(i) for s in L.hvk.shapes if s.sub and all(x[1] == 0x40 for x in s.sub) for i in s.inst)
            self.tris = [t for t in self.tris if t[3] not in cam]
            self.boxes = [b for b in self.boxes if b[1] not in cam]
            self.camera_only = len(cam)
    ESC.Ground = Ground


def _ramp_ground(lo=0.45):
    """kl_walk2d counts only triangles with ny > 0.7 as floor; slopes between `lo` and 0.7 are neither floor nor wall. With --ramps they become floor
    (GUESS: the engine's walkable slope limit is not known; stairs modelled as ramps need this)."""
    import kl_map_escape as ESC
    Base = ESC.Ground

    class Ground(Base):
        def __init__(self, L):
            Base.__init__(self, L)
            self.tris = [(a, b, c, r, 0.71 if lo <= ny < 0.7 else ny) for (a, b, c, r, ny) in self.tris]
    ESC.Ground = Ground


def flood_h(w, x, z, y0):
    """kl_walk2d.Walk.flood with the start HEIGHT chosen (nearest floor to y0) and every (i, j, floor y) state kept."""
    i, j = w._ix(x), w._iz(z)
    fl = w.floors[i][j]
    if not fl:
        raise ValueError('no floor under (%s, %s)' % (x, z))
    f0 = min(fl, key=lambda f: abs(f - y0))
    STEP = sys.modules['kl_walk2d'].STEP
    seen = {(i, j, round(f0 / STEP))}
    q = collections.deque([(i, j, f0)])
    states = collections.defaultdict(list)
    while q:
        i, j, y = q.popleft()
        states[(i, j)].append(y)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if not (0 <= a < w.nx and 0 <= b < w.nz):
                continue
            best = None
            for f in w.floors[a][b]:
                if abs(f - y) <= STEP and not w.blocked(a, b, f) and (best is None or abs(f - y) < abs(best - y)):
                    best = f
            if best is not None and (a, b, round(best / STEP)) not in seen:
                seen.add((a, b, round(best / STEP)))
                q.append((a, b, best))
    return states, f0


def reached_at(w, states, p, tol=STATION_TOL):
    """-> (True/False, nearest reached floor y within 1 cell (or None), cell distance)."""
    i0, j0 = w._ix(p[0]), w._iz(p[2])
    best = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for y in states.get((i0 + di, j0 + dj), ()):
                if best is None or abs(y - p[1]) < abs(best - p[1]):
                    best = y
    return (best is not None and abs(best - p[1]) <= tol), best


def walk(src, cell=40.0, step=65.0, drop=(), near=600.0, nocam=False, start_y=None, ramps=False, log=print):
    import kl_walk2d as W, kl_fa_v2_park as P
    if nocam:
        _camera_only_ground()
    if ramps:
        _ramp_ground()
    W.CELL, W.STEP = float(cell), float(step)
    w = W.Walk(src, BOX, list(drop))
    log('  collision refs dropped by --drop: %d' % w.dropped)
    sx, _sy, sz = P.START[0]
    states, f0 = flood_h(w, sx, sz, P.PAGODA_Y if start_y is None else start_y)
    reach = {c: max(v) for c, v in states.items()}
    xs = [w.xz(c)[0] for c in reach]
    zs = [w.xz(c)[1] for c in reach]
    log('  start (%d, %d) floor y %.0f; reached cells %d; extent x %d .. %d, z %d .. %d' % (sx, sz, f0, len(reach), min(xs), max(xs), min(zs), max(zs)))
    res = collections.OrderedDict()
    for name, p in stations(P).items():
        ok, y = reached_at(w, states, p)
        res[name] = ok
        log('  %-34s (%6d,%5d,%6d)  %s%s' % (name, p[0], p[1], p[2], 'REACHED' if ok else 'not reached',
                                              '' if y is None else '  (nearest reached floor y %.0f)' % y))
    # frontier: unreached cell next to a reached one that holds a floor and a steep piece; nearest the farthest-reaching end (z min) gets the report
    zmin = min(zs)
    seen, cand = set(), []
    for (i, j), y in reach.items():
        if near is not None and w.xz((i, j))[1] > zmin + near:
            continue
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if (a, b) in reach or not (0 <= a < w.nx and 0 <= b < w.nz) or (a, b) in seen:
                continue
            seen.add((a, b))
            if w.floors[a][b] and w.walls[a][b]:
                cand.append((a, b, y))
    cells = {(a, b): w.xz((a, b)) for a, b, _ in cand}
    ys = {(a, b): y for a, b, y in cand}
    cnt = collections.Counter()
    for (typ, ref, lo, hi) in w.g.boxes:
        for c, (x, z) in cells.items():
            if lo[0] - cell <= x <= hi[0] + cell and lo[2] - cell <= z <= hi[2] + cell and lo[1] < ys[c] + W.BODY[1] and hi[1] > ys[c] + W.BODY[0]:
                cnt[ref] += 1
    for (a, b, c_, ref, ny) in w.g.tris:
        if ny >= 0.45:
            continue
        bx0, bx1 = min(a[0], b[0], c_[0]) - cell, max(a[0], b[0], c_[0]) + cell
        bz0, bz1 = min(a[2], b[2], c_[2]) - cell, max(a[2], b[2], c_[2]) + cell
        ylo, yhi = min(a[1], b[1], c_[1]), max(a[1], b[1], c_[1])
        for c, (x, z) in cells.items():
            if bx0 <= x <= bx1 and bz0 <= z <= bz1 and ylo < ys[c] + W.BODY[1] and yhi > ys[c] + W.BODY[0]:
                cnt[ref] += 1
                break
    sc = w.L.sc
    node_of = {e.ref: i + 1 for i, e in enumerate(w.L.ents)}
    out = []
    for ref, n in cnt.most_common(25):
        k = node_of.get(ref)
        out.append((sc.names[sc.top[k]] if k else '?', sc.path[k] if k else 'REF %d' % ref, n))
        log('   frontier piece (%4d cells)  %s   <- %s' % (n, out[-1][1], out[-1][0]))
    log('  frontier candidate cells (within %s of the southernmost reach): %d' % (near, len(cand)))
    return dict(reached=len(reach), extent=(min(xs), max(xs), min(zs), max(zs)), stations=res, frontier=out, w=w, states=states)


def mesh(src, log=print):
    """The way the AI is GIVEN (kl_route.mesh_way over the navigation mesh, sampled against the collision), leg by leg along the round's order:
    START -> pagoda cases -> bridge -> tea house / shrines / statues (south to north order of the garden walk, GUESS) -> stairs foot -> stairs top -> boarding place."""
    import kl_route, kl_fa_v2_park as P
    st = stations(P)
    order = ['START row 0', 'loot 05 the pagoda', 'bridge landing', 'loot 07 shrine B1', 'loot 06 the tea house', 'loot 11 statue 1',
             'loot 12 statue 2', 'loot 08 shrine B2', 'loot 09 shrine A1', 'loot 13 statue 3', 'loot 14 statue 4', 'loot 10 shrine A2',
             'stairs foot', 'stairs top', 'van boarding place']
    pts = [st[k] for k in order]
    legs = kl_route.mesh_way(src, pts)
    if legs is None:
        log('  no navigation mesh in the level')
        return None
    for k0, k1, r in zip(order, order[1:], legs):
        log('  %-20s -> %-20s way %s  length %s m  samples %d  no floor %d  hits %d  path blockers %d  %s' % (
            k0, k1, 'YES' if r['length'] is not None else 'NO ', r['length'], r['samples'], len(r['nofloor']), sum(n for _o, n, _p in r['hit']),
            len(r['blockers']), r['note']))
        for o, n, at in r['hit'][:3]:
            log('       hit %4d x %s at %s' % (n, o, at))
        for path, _s, n, at in r['blockers'][:3]:
            log('       path blocker %4d x %s at %s' % (n, path, at))
    return legs


# ---- joinini: opt-in KLJoin.ini with two CrewHop "stall rescues" (kl-merge-e5, 2026-10-18; NOT RUN IN THE GAME) -------------------------------
# Evidence (KLHook.log, 3 Park II rounds, klmove 'move: ... stood' lines): bots stand at two exact spots on the early route and are never freed:
#   tea house  (697,174,-2322): 1.7 m short of the case (802,175,-2456), just past the 165-unit pickup reach; 7 events, 41.6 s, one 'FED UP - nothing was paid'
#   statue 1   (-547,228,-4313) / (-503,213,-4299): on a 24..60 unit mound, 4.9 m from its order place; 7 events, 43 s, '3 orders none nearer - target DROPPED'
# Fix: a [CrewHop] each (klhop.c): a bot that stands at From for Wait s at heist stage >= 1 is put on the mesh beside the case by the game's own actor
# teleport. Landing y 220 = the mesh height at both cases (the cases' own y 175 / 184 lie below it); landings are 70..90 from the case (pickup reach 165). ALL numbers are GUESSES (Radius, Height, Wait, the landing offsets); the landing places are checked on the mesh and the collision here.
HOPS = [('tea house', (697, 174, -2322), 130, 80, 8, [(847, 220, -2533), (741, 220, -2491)]),
        ('statue 1', (-525, 220, -4306), 130, 80, 8, [(-539, 220, -4671), (-616, 220, -4786)])]


def joinini_text(src=None, log=print):
    """-> KLJoin.ini text. With src (the finished folder / zip) the landing places are checked on the navigation mesh (kl_route.Mesh.on) and reported."""
    L = ['; --joinini (kl_fa_v2_park_route.py, kl-merge-e5 2026-10-18): crew hops for the two early-route stalls of Park II. ALL VALUES ARE GUESSES, NOT RUN.',
         '; Wait 8 s: the 14 stall events averaged 6 s (84 s total, KLHook.log move: ... stood lines), so a hop fires only on the longer ones. GUESS.',
         '; Stage=1: the round has begun; Player=0: no human needed; Again=0: once a round per hop.']
    mesh = None
    if src:
        import kl_route
        mesh = kl_route.load(src).mesh()
    for n, (name, frm, rad, hgt, wait, tos) in enumerate(HOPS):
        keep = []
        for t in tos:
            if mesh is not None:
                hit = mesh.on(*t)
                log('  %-9s landing %s: %s' % (name, t, 'on the mesh (height %.0f)' % hit[1] if hit else 'NOT ON THE MESH - dropped'))
                if not hit:
                    continue
            keep.append(t)
        if not keep:
            raise SystemExit('refused: no landing place of hop %s is on the mesh' % name)
        L += ['', '; %s: From = the exact stall spot' % name, '[CrewHop]' if n == 0 else '[CrewHop.%d]' % (n + 1),
              'From=%d %d %d' % frm, 'Radius=%d' % rad, 'Height=%d' % hgt, 'Wait=%d' % wait, 'Stage=1', 'Player=0', 'Again=0', 'Places=%d' % len(keep)]
        L += ['To.%d=%d %d %d' % (i + 1, *t) for i, t in enumerate(keep)]
    return '\r\n'.join(L) + '\r\n'


def joinini(src, out, log=print):
    """Copy the finished folder SRC to OUT (no *.before-* backups) and add KLJoin.ini. Refuses a game-folder OUT or an existing KLJoin.ini."""
    import shutil, hashlib
    src, out = os.path.abspath(src), os.path.abspath(out)
    if 'steamapps' in out.lower() or os.path.exists(os.path.join(src, 'KLJoin.ini')):
        raise SystemExit('refused: OUT inside a Steam folder, or SRC already has a KLJoin.ini')
    os.makedirs(out, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if '.before-' in f or not os.path.isfile(os.path.join(src, f)):
            continue
        shutil.copy2(os.path.join(src, f), os.path.join(out, f))
    txt = joinini_text(os.path.join(src, 'F02_Main.zip'), log)
    with open(os.path.join(out, 'KLJoin.ini'), 'wb') as fh:
        fh.write(txt.encode('ascii'))
    md = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
    for f in sorted(os.listdir(out)):
        o, s = os.path.join(out, f), os.path.join(src, f)
        log('  %-28s %s %s' % (f, md(o), 'NEW' if not os.path.exists(s) else ('same' if md(o) == md(s) else 'DIFFERS')))


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'joinini':
        joinini(a[1], a[2])
        sys.exit(0)
    if len(a) >= 2 and a[0] == 'walk':
        g = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
        r = walk(a[1], g('--cell', 40.0), g('--step', 65.0), [a[i + 1] for i, v in enumerate(a) if v == '--drop'], g('--near', 600.0),
                 '--nocam' in a, g('--start-y', None) if '--start-y' in a else None, '--ramps' in a)
        sys.exit(0 if r['stations'].get('van boarding place') else 1)
    if len(a) >= 2 and a[0] == 'mesh':
        legs = mesh(a[1])
        sys.exit(0 if legs and all(r['length'] is not None for r in legs) else 1)
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
