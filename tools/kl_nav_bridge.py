"""kl_nav_bridge.py - add walkable bridge polygons to a Dog Days PF4 navigation mesh block (kl_pf4 form, no size dword).

Why: a campaign level's mesh can be split into islands that the campaign's own scripts (a blown wall, an opened gate) joined at run time;
a graft that fires the blast in the level keeps the map open for people but the AI's mesh stays split (Hot Coffee II: garage / alley / street).

The form is the one stock Dog Days uses for a one-polygon AREA with cross-area neighbours (F01 areas 1..3, 109 areas of the 9 stock FA meshes
with two portals; python kl_nav_bridge.py selftest rebuilds every such area of every stock mesh and compares). Everything is APPENDED, so no
existing index moves except the vertices behind an area that gains a portal vertex:
  * a new AREA per bridge quad: 0 waypoints, 4 corner vertices (x, z, y + a 2-D vertex normal) + one PORTAL vertex per portal edge (the
    edge's midpoint, normal 0 0; every stock area has exactly as many extra vertices as cross-area edges: 651 of 651 areas);
  * its polygon: 4 edges, edge k = vertex k -> k + 1; a neighbour in another area is stored as -2 - polygon on BOTH sides (1316 stock edges,
    269 of 269 checked pairs symmetric);
  * tree 0 (BSP per area): one node per edge, (outside = -1, inside = next node), the last node's inside child = leaf -2 - polygon; the plane of
    edge k is (a, b, c) = (dz, -dx, a * x0 + b * z0) with (dx, dz) = edge k's vector (length NOT normalised), inside when a x + b z - c >= 0;
  * tree 1 (height lookup, one tree per polygon, children relative): one node with both children = the leaf (-1 - record of array 2); the
    leaf is the height plane y = a x + b z + c;
  * the area record: box = the corners' box +-1 in x / z and +-100 in height, running starts = the counts before.
The EXISTING polygon on the other side of a portal edge gets neighbour -2 - bridge polygon, and its area gets a portal vertex appended at the end
of its vertex run (later vertices, edges and area starts shift by one).
GUESSES (not read in code): (1) where in an area's run a portal vertex goes and in which order: stock areas hold them in an order that is not
polygon / edge order (the engine may match them by position); the new ones are appended in the order the bridge is made. (2) the 2-D vertex
normal of a corner when BOTH its edges are portals (stock: 2 samples, no rule found; here: the normal of the edge that starts there). The other
corners follow a rule that holds for 99 % of the stock quad areas (bisector of the wall edges' inward normals; a portal edge is not counted).
(3) the height plane of a sloped quad is the plane through its first three corners; other corners must lie within TOL of it, else ValueError.
Checks: kl_pf4.check, kl_maps.nav_facts (every rule holds as for stock), and the parts of kl_fa_bots.Nav.
"""
import math, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_pf4

TOL = 2.0                       # corners off the height plane by more than this: refused
PAD_XZ, PAD_Y = 1.0, 100.0


def _norm(x, z):
    n = math.hypot(x, z) or 1.0
    return x / n, z / n


def _inward(dx, dz):
    return _norm(dz, -dx)


def corner_normals(P, portal):
    """P: 4 corners (x, y, z). portal: set of edge numbers that are portals. -> [(nx, nz)] per corner. GUESS (2): bisector of the two inward
    edge normals, a portal edge not counted when the other edge of the corner is a wall; both portals: that corner takes the normal of the
    edge that starts at it."""
    n = len(P)
    inn = []
    for k in range(n):
        a, b = P[k], P[(k + 1) % n]
        inn.append(_inward(b[0] - a[0], b[2] - a[2]))
    out = []
    for k in range(n):
        e0, e1 = (k - 1) % n, k
        use = [e for e in (e0, e1) if e not in portal] or [e1]
        sx, sz = sum(inn[e][0] for e in use), sum(inn[e][1] for e in use)
        out.append(_norm(sx, sz) if math.hypot(sx, sz) > 1e-6 else inn[use[0]])
    return out


def height_plane(P):
    """(a, b, c): y = a x + b z + c through the first three corners; the others within TOL, else ValueError."""
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = P[:3]
    ux, uy, uz, vx, vy, vz = x1 - x0, y1 - y0, z1 - z0, x2 - x0, y2 - y0, z2 - z0
    d = ux * vz - uz * vx
    if abs(d) < 1e-6:
        raise ValueError('degenerate quad')
    a = (uy * vz - uz * vy) / d
    b = (ux * vy - uy * vx) / d
    c = y0 - a * x0 - b * z0
    for p in P:
        if abs(a * p[0] + b * p[2] + c - p[1]) > TOL:
            raise ValueError('quad is not planar: corner %s is %.1f off the plane' % (p, a * p[0] + b * p[2] + c - p[1]))
    return a, b, c


def signed(P):
    """Twice the signed area in the (x, z) plane. Stock polygons are NEGATIVE in this convention (inward normal = (dz, -dx))."""
    return sum(P[k][0] * P[(k + 1) % len(P)][2] - P[(k + 1) % len(P)][0] * P[k][2] for k in range(len(P)))


def build_area(P, links, base, n_old_edges_first=None):
    """The records of ONE new one-polygon area. P: corners (x, y, z) in stock winding. links: {edge k: -2 - neighbour polygon}.
    base: dict of the counts before it (n3 polygons, n9 edges, n6 vertices, n0 / n1 / n2 tree sizes, n5 waypoints) and 'poly' (index of the
    new polygon). -> dict of record lists to append."""
    if signed(P) >= 0:
        raise ValueError('corners are not in stock winding (signed area %.0f >= 0)' % signed(P))
    n = len(P)
    plane = height_plane(P)
    portal = sorted(links)
    norms = corner_normals(P, set(portal))
    verts = [struct.pack('<5f', p[0], p[2], p[1], *norms[k]) for k, p in enumerate(P)]
    for k in portal:
        a, b = P[k], P[(k + 1) % n]
        verts.append(struct.pack('<5f', (a[0] + b[0]) / 2, (a[2] + b[2]) / 2, (a[1] + b[1]) / 2, 0.0, 0.0))
    edges = [struct.pack('<iII', links.get(k, -1), base['n6'] + k, 0) for k in range(n)]
    t0 = []
    for k in range(n):
        a, b = P[k], P[(k + 1) % n]
        dx, dz = b[0] - a[0], b[2] - a[2]
        A_, B_ = dz, -dx
        nxt = base['n0'] + k + 1 if k + 1 < n else -2 - base['poly']
        t0.append(struct.pack('<ii3f', -1, nxt, A_, B_, A_ * a[0] + B_ * a[2]))
    leaf = -1 - base['n2']
    xs = [p[0] for p in P]; zs = [p[2] for p in P]; ys = [p[1] for p in P]
    spanx, spanz = max(xs) - min(xs), max(zs) - min(zs)
    t1 = [struct.pack('<ii3f', leaf, leaf, -spanz, -spanx, -spanz * P[0][0] - spanx * P[0][2])]    # unused when both children agree (GUESS: stock form)
    a2 = [struct.pack('<3f', *plane)]
    poly = struct.pack('<BBHIIIIIII', n, 0, 0, 0, 0, base['n9'], base['n5'], 0, base['n1'], 0)         # area filled in by the caller
    box = struct.pack('<6f', min(xs) - PAD_XZ, min(ys) - PAD_Y, min(zs) - PAD_XZ, max(xs) + PAD_XZ, max(ys) + PAD_Y, max(zs) + PAD_XZ)
    return dict(verts=verts, edges=edges, t0=t0, t1=t1, a2=a2, poly=poly, box=box, nverts=len(verts))


def add_bridges(block, bridges, log=print):
    """block: a Dog Days mesh block. bridges: list of dicts
         corners: 4 points (x, y, z) in stock winding (negative signed area in x / z), edge k = corner k -> k + 1
         joins:   {edge k: ('old', polygon, edge)} the existing polygon's border edge this edge lies on (it is reversed there), or
                  {edge k: ('new', bridge index, edge)} another bridge of this call
       -> (new block, report). Raises ValueError when the result breaks kl_pf4.check or a kl_maps.nav_facts rule."""
    n, A = kl_pf4.split(block, True)
    A = [list(a) for a in A]
    polys = [list(struct.unpack('<BBHIIIIIII', r)) for r in A[3]]
    areas = [list(struct.unpack('<12I', r[:48])) for r in A[4]]
    boxes = [r[48:] for r in A[4]]
    edges = [list(struct.unpack('<iII', r)) for r in A[9]]
    nb0 = len(polys)
    # ---- 1. the existing side of every join
    touched = {}
    for bi, br in enumerate(bridges):
        for k, j in sorted(br['joins'].items()):
            if j[0] != 'old':
                continue
            pi, pe = j[1], j[2]
            p = polys[pi]
            if not 0 <= pe < p[0]:
                raise ValueError('bridge %d edge %d: polygon %d has no edge %d' % (bi, k, pi, pe))
            e = edges[p[5] + pe]
            if e[0] != -1:
                raise ValueError('bridge %d edge %d: polygon %d edge %d is not a border (neighbour %d)' % (bi, k, pi, pe, e[0]))
            a, b = edges[p[5] + pe][1], edges[p[5] + (pe + 1) % p[0]][1]
            va, vb = struct.unpack('<5f', A[6][a]), struct.unpack('<5f', A[6][b])
            ca, cb = br['corners'][k], br['corners'][(k + 1) % 4]
            # the bridge edge runs the other way round: its start is the old edge's end
            d1 = math.hypot(ca[0] - vb[0], ca[2] - vb[1]) + math.hypot(cb[0] - va[0], cb[2] - va[1])
            if d1 > 1.0:
                raise ValueError('bridge %d edge %d does not lie on polygon %d edge %d (off by %.1f; the old edge is (%.0f,%.0f)->(%.0f,%.0f))' % (
                    bi, k, pi, pe, d1, va[0], va[1], vb[0], vb[1]))
            e[0] = -2 - (nb0 + bi)
            touched.setdefault(p[4], []).append(((va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2, (va[2] + vb[2]) / 2))
    # ---- 2. a portal vertex at the end of each touched area's vertex run (everything behind it shifts)
    verts = [r for r in A[6]]
    for ai in sorted(touched, reverse=True):
        for mid in reversed(touched[ai]):
            pos = areas[ai][6] + areas[ai][1]
            verts.insert(pos, struct.pack('<5f', mid[0], mid[1], mid[2], 0.0, 0.0))
            for e in edges:
                if e[1] >= pos:
                    e[1] += 1
            for q in areas[ai + 1:]:
                q[6] += 1
            areas[ai][1] += 1
    # ---- 3. the new areas
    out = dict(t0=[], t1=[], a2=[], polys=[], edges=[], verts=[], areas=[])
    base = dict(n0=n[0], n1=n[1], n2=n[2], n3=nb0, n5=n[5], n6=len(verts), n9=len(edges))
    new_polys = []
    for bi, br in enumerate(bridges):
        links = {}
        for k, j in br['joins'].items():
            if j[0] == 'old':
                links[k] = -2 - j[1]
            else:
                links[k] = -2 - (nb0 + j[1])
        b = dict(base, poly=nb0 + bi)
        r = build_area(br['corners'], links, b)
        area_index = len(areas) + bi
        pr = list(struct.unpack('<BBHIIIIIII', r['poly'])); pr[4] = area_index
        out['polys'].append(struct.pack('<BBHIIIIIII', *pr))
        out['edges'] += r['edges']; out['verts'] += r['verts']; out['t0'] += r['t0']; out['t1'] += r['t1']; out['a2'] += r['a2']
        av = [0, r['nverts'], 1, 0, 0, base['n5'], base['n6'], nb0 + bi, 0, base['n0'], base['n1'], base['n2']]
        out['areas'].append(struct.pack('<12I', *av) + r['box'])
        base['n0'] += 4; base['n1'] += 1; base['n2'] += 1; base['n6'] += r['nverts']; base['n9'] += 4
    A[0] += out['t0']; A[1] += out['t1']; A[2] += out['a2']
    A[3] = [struct.pack('<BBHIIIIIII', *p) for p in polys] + out['polys']
    A[4] = [struct.pack('<12I', *a) + bx for a, bx in zip(areas, boxes)] + out['areas']
    A[6] = verts + out['verts']
    A[9] = [struct.pack('<iII', *e) for e in edges] + out['edges']
    data = kl_pf4.join(A)
    kl_pf4.check(data, kl_pf4.DD_LINK_KINDS)
    import kl_maps
    bad = {k: v for k, v in kl_maps.nav_facts(data).items() if v[0] != v[1]}
    if bad:
        raise ValueError('the mesh with the bridges breaks %s' % bad)
    return data, dict(polygons=list(range(nb0, nb0 + len(bridges))), areas=list(range(len(areas), len(areas) + len(bridges))),
                      touched_areas=sorted(touched))


# ------------------------------------------------------------------ self-test against the stock single-polygon areas
def selftest(log=print):
    """Rebuild every one-polygon stock area (4 corners) from its corners and its links and compare: tree 0, edges' vertex numbers, vertices
    (positions; normals reported), area box, tree-1 children. -> (matched, of)."""
    import kl_maps
    ok = tot = 0
    nrm_ok = nrm_tot = 0
    for L in ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']:
        b = kl_maps.nav_of(L)
        n, A = kl_pf4.split(b, True)
        polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        edges = [struct.unpack('<iII', r) for r in A[9]]
        V = [struct.unpack('<5f', r) for r in A[6]]
        for ai, r in enumerate(A[4]):
            a = struct.unpack('<12I', r[:48])
            if a[2] != 1 or polys[a[7]][0] != 4:
                continue
            p = polys[a[7]]
            es = [edges[p[5] + k] for k in range(4)]
            P = [(V[e[1]][0], V[e[1]][2], V[e[1]][1]) for e in es]
            if signed(P) >= 0:
                continue
            tot += 1
            links = {k: e[0] for k, e in enumerate(es) if e[0] < -1}
            try:
                base = dict(n0=a[9], n1=a[10], n2=a[11], n3=a[7], n5=a[5], n6=a[6], n9=p[5], poly=a[7])
                m = build_area(P, links, base)
            except ValueError as ex:
                continue
            t0 = [struct.unpack('<ii3f', x) for x in A[0][a[9]:a[9] + 4]]
            mine = [struct.unpack('<ii3f', x) for x in m['t0']]
            same = all(x[0] == y[0] and x[1] == y[1] and all(abs(x[i] - y[i]) <= 1e-3 * max(1.0, abs(x[i])) for i in (2, 3, 4)) for x, y in zip(t0, mine))
            box = struct.unpack('<6f', r[48:])
            mb = struct.unpack('<6f', m['box'])
            same = same and all(abs(u - v) < 0.5 for u, v in zip(box, mb)) and m['nverts'] == a[1]
            ok += same
            for k in range(4):
                nrm_tot += 1
                v = struct.unpack('<5f', m['verts'][k])
                w = V[es[k][1]]
                nrm_ok += abs(v[3] - w[3]) < 0.05 and abs(v[4] - w[4]) < 0.05
    log('kl_nav_bridge selftest: %d of %d stock one-polygon quad areas rebuilt (tree 0, box, vertex count); corner normals %d of %d' % (ok, tot, nrm_ok, nrm_tot))
    return ok, tot


if __name__ == '__main__':
    if sys.argv[1:] == ['selftest']:
        ok, tot = selftest()
        sys.exit(0 if ok == tot else 1)
    sys.exit(__doc__)
