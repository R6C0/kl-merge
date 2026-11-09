"""Read-only: flood the live DM09 nav mesh from the road mouth, without the play-box filter, and report
whether the terminal (campaign van V_USA_GetawayVan_Chase_00 / EndOfLevel) can be reached and by which path."""
import sys, os, math, heapq, collections
sys.path.insert(0, r'C:\kl-merge\kl-merge\tools')
import kl_fa_street as S

ARCH = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\DM09\F06_Main.zip'
S.PLAY = ((-1e9, 1e9), (-1e9, 1e9), (-1e9, 1e9))     # every polygon counts
nav = S.Nav.of_archive(ARCH)
N = len(nav.pv)
cen = [(sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs), sum(v[2] for v in vs) / len(vs)) if vs else None for vs in nav.pv]

def poly_at(x, z, y=None):
    c = [i for i in range(N) if nav.box[i] and nav.box[i][0] <= x <= nav.box[i][1] and nav.box[i][2] <= z <= nav.box[i][3] and nav.inside(i, x, z)]
    if y is not None and c:
        c.sort(key=lambda i: abs(nav.box[i][4] - y))
    return c

def nearest(x, y, z):
    return min((i for i in range(N) if cen[i]), key=lambda i: math.dist((x, y, z), cen[i]))

def comp(i):
    seen, st = {i}, [i]
    while st:
        for j in nav.nb[st.pop()]:
            if j not in seen:
                seen.add(j); st.append(j)
    return seen

print('polygons', N)
POINTS = {'road mouth': (-5700, -45, 9000), 'live van stop': (-1853, 117, 10800), 'road start': (-3000, -45, -6000),
          'stairs overpass': (-14330, -487, 11800), 'flight 1': (-16550, -988, 11700), 'flight 2': (-18750, -988, 12705),
          'terminal van': (-24630, -979, 8958), 'EndOfLevel': (-24400, -929, 8986)}
pid = {}
for k, (x, y, z) in POINTS.items():
    at = poly_at(x, z, y)
    i = at[0] if at and abs(nav.box[at[0]][4] - y) < 300 else None
    n = nearest(x, y, z)
    pid[k] = i if i is not None else n
    print('%-16s on poly %s (h %s); nearest centre poly %d at (%d %d %d) dist %.0f' % (k, i, None if i is None else round(nav.box[i][4]), n, *map(round, cen[n]), math.dist((x, y, z), cen[n])))

road = comp(pid['road mouth'])
print('\nroad component: %d polygons' % len(road))
for k in POINTS:
    print('  %-16s reachable from road mouth: %s' % (k, pid[k] in road))

# components touching the terminal / stairs area
tc = comp(pid['terminal van'])
print('terminal component: %d polygons, x %d..%d, z %d..%d, y %d..%d' % (len(tc), min(cen[i][0] for i in tc), max(cen[i][0] for i in tc),
      min(cen[i][2] for i in tc), max(cen[i][2] for i in tc), min(cen[i][1] for i in tc), max(cen[i][1] for i in tc)))
print('road component: x %d..%d, z %d..%d, y %d..%d' % (min(cen[i][0] for i in road), max(cen[i][0] for i in road),
      min(cen[i][2] for i in road), max(cen[i][2] for i in road), min(cen[i][1] for i in road), max(cen[i][1] for i in road)))

# closest gap between the two components (vertex to vertex), the bridge a nav fix would have to add
if pid['terminal van'] not in road:
    rv = [(v, i) for i in road for v in nav.pv[i] if cen[i][0] < -4000]
    tv = [(v, i) for i in tc for v in nav.pv[i]]
    grid = collections.defaultdict(list)
    for v, i in tv:
        grid[int(v[0] // 500), int(v[2] // 500)].append((v, i))
    best = []
    for v, i in rv:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for w, j in grid.get((int(v[0] // 500) + dx, int(v[2] // 500) + dz), ()):
                    best.append((math.dist(v, w), v, w, i, j))
    best.sort()
    print('closest road<->terminal vertex gaps:')
    seen = set()
    for d, v, w, i, j in best:
        if (i, j) in seen: continue
        seen.add((i, j))
        print('  %.0f  road (%d %d %d) poly %d  -- term (%d %d %d) poly %d' % (d, *map(round, v), i, *map(round, w), j))
        if len(seen) >= 8: break
    # other components lying between them (x -24000..-5000)
    allc, done = [], set()
    for i in range(N):
        if i in done or not cen[i] or not (-25000 < cen[i][0] < -5000): continue
        c = comp(i); done |= c
        allc.append(c)
    allc.sort(key=len, reverse=True)
    print('components with centres in x -25000..-5000: %d; largest:' % len(allc))
    for c in allc[:10]:
        print('  %5d polys x %d..%d z %d..%d y %d..%d %s' % (len(c), min(cen[i][0] for i in c), max(cen[i][0] for i in c), min(cen[i][2] for i in c),
              max(cen[i][2] for i in c), min(cen[i][1] for i in c), max(cen[i][1] for i in c), '(road)' if c & road else '(terminal)' if c & tc else ''))
else:
    # shortest path length over polygon centres
    dist, prev, q = {pid['road mouth']: 0.0}, {}, [(0.0, pid['road mouth'])]
    while q:
        d, i = heapq.heappop(q)
        if d > dist[i]: continue
        for j in nav.nb[i]:
            nd = d + math.dist(cen[i], cen[j])
            if nd < dist.get(j, 1e18):
                dist[j] = nd; prev[j] = i; heapq.heappush(q, (nd, j))
    t = pid['terminal van']
    print('path length road mouth -> terminal van: %.0f m' % (dist[t] / 100))
    path = [t]
    while path[-1] in prev: path.append(prev[path[-1]])
    path.reverse()
    steep = [(path[k], path[k + 1]) for k in range(len(path) - 1) if abs(cen[path[k]][1] - cen[path[k + 1]][1]) > 60 and math.dist(cen[path[k]][::2], cen[path[k + 1]][::2]) < 200]
    print('steps on the path: %d polygons; height %d -> %d; steep hops (>60 up within 2 m): %d' % (len(path), cen[path[0]][1], cen[path[-1]][1], len(steep)))
    for k in range(0, len(path), max(1, len(path) // 25)):
        print('   (%d %d %d)' % tuple(map(round, cen[path[k]])))
