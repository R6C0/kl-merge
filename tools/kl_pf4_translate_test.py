"""Self-test of kl_pf4.translate (world translation of a Dog Days navigation mesh) and of the
decoded floats behind it (kl_pf4 docstring, THE FLOATS).

usage: python tools/kl_pf4_translate_test.py [tx ty tz] [level.zip | level_Main.gms | mesh.nav ...]
  No level given: every Scenes/Locations/*/*_Main.zip of the Dog Days install (tools/kl_port_check)
  that can be found, else only the hand-made mesh. Default t = (-12288, 0, -16384) (the DM11B
  shift of re/map_shift_int16_1027.md). Exit 1 on the first failure.

Per mesh: (1) the hand-made or stock mesh passes kl_pf4.check before and after; (2) every vertex,
waypoint and area box moved by exactly t (float32 rounding only); (3) the centroid of every
polygon, moved by t, descends tree 0 of the moved mesh to the SAME polygon as the unmoved
centroid on the original (a locate that changed would send a bot to another polygon); (4) the
height plane under the moved centroid is the original height + ty (within 0.05 units); (5)
moving back by -t returns every float to within 0.01 of the original and every byte of the index
and count fields exactly.
"""
import glob, math, os, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_pf4

TOL_MOVE, TOL_HEIGHT, TOL_BACK = 0.002, 0.05, 0.01


def hand_mesh():
    """A valid one-area mesh: a square of two triangles on the plane h = 0.5 x + 10, one wall each."""
    V = [(0, 0), (100, 0), (100, 100), (0, 100)]
    vert = [struct.pack('<5f', x, z, 0.5 * x + 10, 0, 0) for x, z in V]
    plane = [struct.pack('<3f', 0.5, 0.0, 10.0)]
    # tree 0: the diagonal x - z >= 0 splits the square into polygon 1 (x >= z) and polygon 0
    tree0 = [struct.pack('<ii3f', -2 - 0, -2 - 1, 1.0, -1.0, 0.0)]
    # tree 1: one node per polygon, both children the same plane leaf (relative start = itself)
    tree1 = [struct.pack('<ii3f', -1, -1, 0.0, 0.0, 0.0), struct.pack('<ii3f', -1, -1, 0.0, 0.0, 0.0)]
    # polygons: 0 = (0, 2, 3) above the diagonal, 1 = (0, 1, 2) below; edges: neighbour, vertex, 0
    polys = [struct.pack('<BBHIIIIIII', 3, 0, 0, 0, 0, 0, 0, 0, 0, 0),
             struct.pack('<BBHIIIIIII', 3, 0, 0, 0, 0, 3, 0, 0, 1, 0)]
    edges = [(1, 0), (-1, 2), (-1, 3), (-1, 0), (-1, 1), (0, 2)]
    edges = [struct.pack('<iII', nb, v, 0) for nb, v in edges]
    area = [struct.pack('<12I6f', 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 100, 60, 100)]
    return kl_pf4.join([tree0, tree1, plane, polys, area, [], vert, [], [], edges, [], [], []])


def meshes_of(arg):
    """(name, Dog Days mesh block) of a level zip, an unpacked or packed .gms, or a raw block."""
    import kl_gms
    if arg.lower().endswith('.zip'):
        with zipfile.ZipFile(arg) as z:
            name = [x for x in z.namelist() if x.endswith('_Main.gms')][0]
            raw = kl_gms.unpack(z.read(name))
    elif arg.lower().endswith('.gms'):
        raw = kl_gms.unpack(open(arg, 'rb').read())
    else:
        return os.path.basename(arg), open(arg, 'rb').read()
    o = struct.unpack_from('<I', raw, 0x34)[0]
    if not o:
        return os.path.basename(arg), None
    return os.path.basename(arg), bytes(raw[o + 4:o + 4 + struct.unpack_from('<I', raw, o)[0]])


def centroids(mesh):
    n, A = mesh
    V = [struct.unpack('<3f', r[:12]) for r in A[6]]
    for i, r in enumerate(A[3]):
        cnt, first = r[0], struct.unpack_from('<I', r, 0xc)[0]
        vs = [V[struct.unpack_from('<I', A[9][first + k], 4)[0]] for k in range(cnt)]
        yield i, sum(v[0] for v in vs) / cnt, sum(v[1] for v in vs) / cnt, sum(v[2] for v in vs) / cnt


def run(name, block, t, log=print):
    tx, ty, tz = t
    kl_pf4.check(block)
    moved = kl_pf4.translate(block, t)
    kl_pf4.check(moved)
    back = kl_pf4.translate(moved, (-tx, -ty, -tz))
    m0, m1, m2 = kl_pf4.split(block, True), kl_pf4.split(moved, True), kl_pf4.split(back, True)
    n = m0[0]
    bad = []
    # (2) vertices, waypoints, boxes moved by t
    for k, off, cnt in ((6, 0, 3), (5, 0, 3)):
        for i, (a, b) in enumerate(zip(m0[1][k], m1[1][k])):
            o = struct.unpack_from('<3f', a, off); p = struct.unpack_from('<3f', b, off)
            d = (p[0] - o[0] - tx, p[1] - o[1] - tz, p[2] - o[2] - ty)       # record order x, z, h
            if max(abs(v) for v in d) > TOL_MOVE * max(1.0, abs(o[0]) / 8192, abs(o[1]) / 8192):
                bad.append('array %d record %d moved by %r, not t' % (k, i, d))
            if a[12:] != b[12:]:                        # links / polygon of a waypoint, normal of a vertex
                bad.append('array %d record %d: a non-position field changed' % (k, i))
    for i, (a, b) in enumerate(zip(m0[1][4], m1[1][4])):
        if a[:48] != b[:48]:
            bad.append('area %d: an index field changed' % i)
        o = struct.unpack_from('<6f', a, 48); p = struct.unpack_from('<6f', b, 48)
        if any(abs(p[j] - o[j] - (tx, ty, tz)[j % 3]) > TOL_MOVE * max(1.0, abs(o[j]) / 8192) for j in range(6)):
            bad.append('area %d: box moved by %r' % (i, [p[j] - o[j] for j in range(6)]))
    for k in (0, 1, 3, 7, 9, 10):
        for i, (a, b) in enumerate(zip(m0[1][k], m1[1][k])):
            if (a[:8] != b[:8] or a[8:16] != b[8:16]) if k in (0, 1) else a != b:
                bad.append('array %d record %d: a non-float field changed' % (k, i))
    # (3) + (4) locate and height on every polygon centroid
    same = other = 0; worst_h = worst_c = 0.0
    for i, cx, cz, ch in centroids(m0):
        p0, h0 = kl_pf4.locate(m0, cx, cz)
        p1, h1 = kl_pf4.locate(m1, cx + tx, cz + tz)
        if p0 != p1:
            other += 1
            if other <= 3:
                bad.append('polygon %d centroid: original locate %d, moved locate %d' % (i, p0, p1))
            continue
        same += 1
        if p0 >= 0:
            worst_h = max(worst_h, abs((h1 - ty) - h0))
            if abs((h1 - ty) - h0) > TOL_HEIGHT:
                # a centroid within float32 rounding of a tree-1 split line may land on the other
                # side after the move (the moved c is rounded at |c| ~ 1e7, ulp 1): allowed when the
                # original mesh gives that height within 0.01 units of the point (a non-planar polygon)
                band = [kl_pf4.height(m0, p0, cx + dx, cz + dz) for dx in (-0.01, 0.0, 0.01) for dz in (-0.01, 0.0, 0.01)]
                if not min(band) - TOL_HEIGHT <= h1 - ty <= max(band) + TOL_HEIGHT:
                    bad.append('polygon %d: height %.3f before, %.3f - ty after' % (i, h0, h1 - ty))
    if other:
        bad.append('%d of %d centroids locate another polygon after the move' % (other, same + other))
    # (5) round trip
    for k in range(13):
        for i, (a, b) in enumerate(zip(m0[1][k], m2[1][k])):
            if a == b:
                continue
            fl = {0: (8, 3), 1: (8, 3), 2: (0, 3), 4: (48, 6), 5: (0, 3), 6: (0, 5)}.get(k)
            if fl is None:
                bad.append('array %d record %d differs after the round trip' % (k, i)); continue
            off, cnt = fl
            if a[:off] != b[:off] or a[off + 4 * cnt:] != b[off + 4 * cnt:]:
                bad.append('array %d record %d: a non-float field differs after the round trip' % (k, i)); continue
            fa = struct.unpack_from('<%df' % cnt, a, off); fb = struct.unpack_from('<%df' % cnt, b, off)
            if k in (0, 1):                             # split line a x + b z = c: the error in units is dc / |(a, b)|
                mag = abs(fa[2]) + abs(fa[0] * tx) + abs(fa[1] * tz); ab = math.hypot(fa[0], fa[1]) or 1.0
                worst_c = max(worst_c, abs(fa[2] - fb[2]) / ab)
                tol = (TOL_BACK, TOL_BACK, TOL_BACK + mag * 2 ** -22)
            elif k == 2:                                # plane h = P x + Q z + R
                mag = abs(fa[2]) + abs(fa[0] * tx) + abs(fa[1] * tz)
                tol = (TOL_BACK, TOL_BACK, TOL_BACK + mag * 2 ** -22)
            else:
                tol = [TOL_BACK * max(1.0, abs(x) / 8192) for x in fa]
            if any(abs(x - y) > tl for x, y, tl in zip(fa, fb, tol)):
                bad.append('array %d record %d: %r -> %r after the round trip' % (k, i, fa, fb))
    log('%-22s polygons %5d  areas %4d  vertices %6d  nodes %6d  centroids same %d other %d  worst split %.4f u, height %.4f u  %s' % (
        name, n[3], n[4], n[6], n[0] + n[1], same, other, worst_c, worst_h, 'FAIL' if bad else 'ok'))
    for b in bad[:12]:
        log('   ' + b)
    return not bad


def main(argv):
    t = (-12288.0, 0.0, -16384.0)
    a = list(argv)
    if len(a) >= 3:
        try:
            t = tuple(float(v) for v in a[:3]); a = a[3:]
        except ValueError:
            pass
    ok = run('hand-made', hand_mesh(), t)
    ok &= run('hand-made t=(4096,100,-8192)', hand_mesh(), (4096.0, 100.0, -8192.0))
    if not a:
        try:
            import kl_port_check
            dd = kl_port_check.find(kl_port_check.DD_GUESSES, kl_port_check.DD_EXE)
            a = sorted(glob.glob(os.path.join(glob.escape(dd), 'Scenes', 'Locations', '*', '*_Main.zip'))) if dd else []
        except Exception:
            a = []
    for arg in a:
        name, block = meshes_of(arg)
        if block is None:
            print('%-22s no navigation mesh' % name); continue
        ok &= run(name, block, t)
    print('kl_pf4.translate: %s (t = %r)' % ('every mesh ok' if ok else 'FAILED', t))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
