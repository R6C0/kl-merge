"""Self-test of kl_members.Sgp.translate / Octree.translate / sgd_translate (world translation of a
level's sound portals and point octrees, re/map_shift_int16_1027.md) and of the decoded fields behind
them (kl_members docstring: .sgp portal = openness, rooms, centre, normal, 4 corners; .sgd octree
centre stored as (z, y, x)).

usage: python tools/kl_sgp_sgd_translate_test.py [tx ty tz] [level.zip | X_Main.sgp | X_Main.sgd | folder ...]
  A folder is searched for *.sgp and *.sgd. No level given: every Scenes/Locations/*/*_Main.zip of the
  Dog Days install (tools/kl_port_check) that can be found, else only the hand-made fixtures. Default
  t = (-12288, 0, -16384) (the DM11B shift). Exit 1 on the first failure.

Per .sgp: (1) stock invariants that the decoding predicts: +0x00 is 1.0, +0x04/+0x08 are 0, the normal
is unit, the corners lie in the plane through the centre (within 1.5 units), every edge's distance is
the distance between its two portals' centres (within 0.01); (2) after translate every centre and
corner moved by exactly t (float32 rounding only), the normal, openness, rooms, edges, routes and the
portal list are byte-identical, the file size is unchanged; (3) translate back returns every float to
within 0.01 and everything else exactly.
Per .sgd octree: (1) the tree rebuilt from the file is byte-identical (as kl_members.selftest);
(2) after translate every leaf's world point moved by t (within one quantum + float32 rounding) and
the payload differs from the original ONLY in the 12 centre bytes; (3) back within 0.01.
"""
import glob, math, os, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_members as MB

TOL_MOVE, TOL_BACK, TOL_PLANE, TOL_EDGE = 0.002, 0.01, 1.5, 0.01


def hand_sgp():
    """Two rooms, one portal between them (a 200 x 300 opening at x = 1000), one edge-less graph."""
    g = MB.Sgp()
    p = bytearray(0x5c)
    struct.pack_into('<3f', p, 0, 1.0, 0.0, 0.0)
    struct.pack_into('<2I', p, 0x0c, 0, 1)
    struct.pack_into('<3f', p, 0x14, 1000.0, 150.0, 20000.0)
    struct.pack_into('<3f', p, 0x20, 1.0, 0.0, 0.0)
    for k, (y, z) in enumerate(((0, 19900), (300, 19900), (300, 20100), (0, 20100))):
        struct.pack_into('<3f', p, 0x2c + 12 * k, 1000.0, float(y), float(z))
    g.portals = [p]
    g.rooms = [['Locations/T/A', [0], [(0, 1)]], ['Locations/T/B', [0], []]]
    return g.serialize()


def hand_sgd():
    t = MB.Octree()
    t.centre, t.scale = (20000.0, 100.0, 1000.0), 2.0        # stored (z, y, x) of world (1000, 100, 20000)
    for i, (x, y, z) in enumerate(((1000, 100, 20000), (1100, 120, 20050), (900, 80, 19950))):
        q = tuple(int(round(0x8000 + (v - c) * t.scale)) for v, c in zip((z, y, x), t.centre))
        t.leaves.append((i + 1, q, tuple(v + 1 for v in q)))
    return MB.sgd_write([('HavokShatterOctree', t.serialize()), ('ExplodableOctree', t.serialize())])


def fail(msg):
    print('FAIL:', msg)
    sys.exit(1)


def close(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def check_sgp(name, data, t):
    g = MB.Sgp(data)
    if g.serialize() != data:
        fail('%s: round trip' % name)
    for k, p in enumerate(g.portals):
        o, a, b = struct.unpack_from('<3f', p, 0)
        if (o, a, b) != (1.0, 0.0, 0.0):
            fail('%s: portal %d head %r, expected (1, 0, 0)' % (name, k, (o, a, b)))
        c, *K = g.points(k)
        n = struct.unpack_from('<3f', p, MB.Sgp.NORMAL)
        if abs(math.dist(n, (0, 0, 0)) - 1) > 1e-5:
            fail('%s: portal %d normal %r not unit' % (name, k, n))
        for q in K:
            if abs(sum((q[i] - c[i]) * n[i] for i in range(3))) > TOL_PLANE:
                fail('%s: portal %d corner %r off the plane of centre %r normal %r' % (name, k, q, c, n))
    for pa, pb, d in g.edges:
        ca, cb = g.points(pa)[0], g.points(pb)[0]
        if abs(math.dist(ca, cb) - d) > TOL_EDGE:
            fail('%s: edge %d-%d distance %.3f vs centres %.3f' % (name, pa, pb, d, math.dist(ca, cb)))
    m = g.translate(t)
    md = m.serialize()
    if len(md) != len(data):
        fail('%s: moved size %d vs %d' % (name, len(md), len(data)))
    for k, p in enumerate(g.portals):
        q = m.portals[k]
        if bytes(p[:MB.Sgp.CENTRE]) != bytes(q[:MB.Sgp.CENTRE]) or bytes(p[MB.Sgp.NORMAL:MB.Sgp.CORNERS[0]]) != bytes(q[MB.Sgp.NORMAL:MB.Sgp.CORNERS[0]]):
            fail('%s: portal %d head/normal changed' % (name, k))
        for a, b in zip(g.points(k), m.points(k)):
            if not close([v + d for v, d in zip(a, t)], b, TOL_MOVE):
                fail('%s: portal %d point %r moved to %r, not by %r' % (name, k, a, b, t))
    if m.edges != g.edges or m.rooms != g.rooms:
        fail('%s: edges or rooms changed' % name)
    # the non-portal tail is byte-identical
    tail = 0x14 + 0x5c * len(g.portals)
    if md[tail:] != data[tail:] or md[:0x14] != data[:0x14]:
        fail('%s: bytes outside the portals changed' % name)
    back = m.translate(tuple(-v for v in t))
    for k in range(len(g.portals)):
        for a, b in zip(g.points(k), back.points(k)):
            if not close(a, b, TOL_BACK):
                fail('%s: portal %d back %r vs %r' % (name, k, b, a))
    return len(g.portals), len(g.edges)


def check_sgd(name, data, t):
    secs = MB.sgd_read(data)
    moved = MB.sgd_read(MB.sgd_translate(data, t))
    back = MB.sgd_read(MB.sgd_translate(MB.sgd_translate(data, t), tuple(-v for v in t)))
    n = 0
    for (nm, body), (nm2, mbody), (_, bbody) in zip(secs, moved, back):
        if nm != nm2:
            fail('%s: section order changed' % name)
        if 'Octree' not in nm:
            continue
        tr = MB.Octree(body)
        if tr.serialize() != body:
            fail('%s: %s not rebuilt byte-identical' % (name, nm))
        mt, bt = MB.Octree(mbody), MB.Octree(bbody)
        if body[:4] != mbody[:4] or body[0x10:] != mbody[0x10:]:
            fail('%s: %s changed outside the centre' % (name, nm))
        tol = TOL_MOVE + 1.0 / tr.scale
        for a, b, c in zip(tr.leaves, mt.leaves, bt.leaves):
            if a[1:] != b[1:] or a[0] != b[0]:
                fail('%s: %s leaf changed' % (name, nm))
            pa, pb, pc = tr.world(a), mt.world(b), bt.world(c)
            if not close([v + d for v, d in zip(pa, t)], pb, tol):
                fail('%s: %s leaf REF %d at %r moved to %r, not by %r' % (name, nm, a[0], pa, pb, t))
            if not close(pa, pc, TOL_BACK + 1.0 / tr.scale):
                fail('%s: %s leaf REF %d back %r vs %r' % (name, nm, a[0], pc, pa))
            n += 1
    return n


def inputs(args):
    """[(label, kind, bytes)] from zips, member files and folders."""
    out = []
    for a in args:
        if os.path.isdir(a):
            out += inputs(sorted(glob.glob(os.path.join(glob.escape(a), '*.sgp')) + glob.glob(os.path.join(glob.escape(a), '*.sgd'))))
        elif a.lower().endswith('.zip'):
            with zipfile.ZipFile(a) as zf:
                for n in zf.namelist():
                    if n.lower().endswith(('.sgp', '.sgd')):
                        out.append((os.path.basename(a) + ':' + os.path.basename(n), n[-3:].lower(), zf.read(n)))
        elif a.lower().endswith(('.sgp', '.sgd')):
            out.append((os.path.basename(a), a[-3:].lower(), open(a, 'rb').read()))
        else:
            fail('not a level zip, .sgp, .sgd or folder: %s' % a)
    return out


def main():
    a = sys.argv[1:]
    t = (-12288.0, 0.0, -16384.0)
    if len(a) >= 3:
        try:
            t = tuple(float(v) for v in a[:3]); a = a[3:]
        except ValueError:
            pass
    items = [('hand-made.sgp', 'sgp', hand_sgp()), ('hand-made.sgd', 'sgd', hand_sgd())]
    if a:
        items += inputs(a)
    else:
        try:
            from kl_port_check import find, DD_GUESSES, DD_EXE
            dd = find(DD_GUESSES, DD_EXE)
            if dd:
                items += inputs(sorted(glob.glob(os.path.join(glob.escape(dd), 'Scenes', 'Locations', '*', '*_Main.zip'))))
        except Exception as e:                                   # no install here: fixtures only
            print('no Dog Days install (%s): hand-made fixtures only' % e)
    files = portals = edges = leaves = 0
    for name, kind, data in items:
        if kind == 'sgp':
            p, e = check_sgp(name, data, t); portals += p; edges += e
        else:
            leaves += check_sgd(name, data, t)
        files += 1
    print('ok: %d files, %d portals, %d edges, %d octree leaves moved by %r and back' % (files, portals, edges, leaves, t))


if __name__ == '__main__':
    main()
