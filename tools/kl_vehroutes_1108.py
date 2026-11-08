r"""kl_vehroutes_1108.py - DM01B (Hot Coffee II, slot F03) escape van drive-away that no longer goes through the Donut Factory.
Written 2026-11-08, OFFLINE: reads the live zip, writes a NEW zip (never the live one).

WHAT WAS WRONG (proven with render triangles, not collision): the van's drive-away lane runs straight west along z=30800 from the stop
(x~1660) to x=-1400; the Donut Factory's east wall stands at x~-495 on that line, so the van drives into / through the wall (and the crash-piece
keys 522..562 reach x=-863, also inside it). kl_fa_v2_hotcoffee's ROAD plan only checked the lane against collision.
The lane is an ALLEY: the donut shop is its south side (z<30655), a continuous planter strip (SO1103_M01_DonutShop_PlantD_03, 125 high, z
31230..31610, x -4000..2000) its north side, the Donut Factory its dead-end west side; it is open only to the east (where the van arrives from).
FIX: the van backs OUT of the alley the way it came: every drive-away key (idx 172 .. 390) is mirrored about the stop (x' = 2*STOP_X - x), so the
van reverses along its own arrival lane (z=30800, nose still west) to x~4720; the rotation keys (sway only) are untouched. Arrival, stop, boarding,
escape box, bounds and bot boarding are unchanged. Crash-piece keys (idx >= cut) are clamped to x >= CRASH_MIN_X so no piece lands in the factory.
GUESS: that a reversing exit reads as 'logical' (the alley is a dead end: a forward exit would need a U-turn in 575 units, or crossing the planter
strip to the main street z~31930 where the Dead Men van really drives); STOP_X=1660 is read from the keys (the creep plateau), CRASH_MIN_X=-350 is the
wall (-496) plus the hull clearance 130 and a margin.
usage: python kl_vehroutes_1108.py <live F03_Main.zip> <out zip> [--check-only]"""
import math, os, struct, sys, zipfile, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F, kl_graft, kl_map_escape as ME

STOP_X = 1660.0
CRASH_MIN_X = -350.0
HULL = 130.0            # half width 110 + margin (GUESS)
BUF = 'Scenes/Locations/F03/F03_Main.buf'


def van_keys(zp):
    B = F.Built(zp)
    sc = B.sc
    k = next(k for k in range(1, len(B.ents) + 1) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    return B, ME.VanKeys(B.scene.head, B.ents[k - 1].raw, ends, kl_graft.keys_tracks)


def new_positions(K):
    cut = K.drive()
    first = next(i for i in range(cut) if K.pos[i][0] <= STOP_X)
    pos = list(K.pos)
    for i in range(first, cut):
        p = pos[i]
        pos[i] = (2 * STOP_X - p[0], p[1], p[2])
    for i in range(cut, K.npos):
        p = pos[i]
        if p != (0.0, 0.0, 0.0) and p[0] < CRASH_MIN_X:
            pos[i] = (CRASH_MIN_X, p[1], p[2])
    return pos, first, cut


def patch(src, dst):
    B, K = van_keys(src)
    pos, first, cut = new_positions(K)
    head = bytearray(B.scene.head)
    for i, p in enumerate(pos):
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
    zin = zipfile.ZipFile(src)
    buf = zin.read(BUF)
    if buf[:len(head)] != B.scene.head:
        raise ValueError('the .buf head is not the scene head')
    nbuf = bytes(head) + buf[len(head):]
    with zipfile.ZipFile(dst, 'w') as zo:
        for inf in zin.infolist():
            data = nbuf if inf.filename == BUF else zin.read(inf.filename)
            zo.writestr(inf, data, compress_type=inf.compress_type)
    return first, cut, pos


def check(zp, log=print, summary=False):
    """Hull clearance of the van's main drive and crash keys against RENDER triangles (kl_arrival_1107), in world space, heights relative to the
    van's first key (wheels 0, roof ~250). -> number of close samples. summary=True: one line per hit owner (first/last key index, min gap)."""
    import numpy as np
    import kl_arrival_1107 as A
    B, K = van_keys(zp)
    sc = B.sc
    van = next(k for k in range(1, len(B.ents) + 1) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    R, T = ME.Level(zp).frame(sc.parent[van])
    t, o, n = A.geom(zp)
    t, o = np.asarray(t), np.asarray(o)
    keep = [i for i, x in enumerate(n) if 'glow' not in x.lower() and 'distance' not in x.lower() and 'Van' not in x and 'Escape' not in x]
    w = lambda p: tuple(T[i] + sum(R[i][j] * p[j] for j in range(3)) for i in range(3))
    pts = [w(p) for p in K.pos if p != (0.0, 0.0, 0.0)]
    y0 = pts[0][1]
    ok = np.isfinite(t).all(axis=(1, 2)) & (np.abs(t).max(axis=(1, 2)) < 1e6) & np.isin(o, keep) & (t[:, :, 1].max(axis=1) > y0 + 53)
    M = A.Mesh(t[ok], o[ok], n)
    bad, seen = 0, {}
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        if math.dist(a, b) > 400:
            continue
        for s in (0.0, 0.5):
            p = tuple(a[j] + (b[j] - a[j]) * s for j in range(3))
            for dy in (73, 163, 263):
                d, ow = M.dist((p[0], p[1] + dy, p[2]), 400)
                if d < HULL:
                    bad += 1
                    r = seen.setdefault(ow.split(chr(92))[-1][:50], [i, i, d, p])
                    r[1], r[2] = i, min(r[2], d)
                    if not summary:
                        log('CLOSE key %d x=%d z=%d dy=%d d=%d %s' % (i, p[0], p[2], dy, d, ow[-40:]))
                    break
    if summary:
        for k, (i0, i1, d, p) in sorted(seen.items(), key=lambda kv: kv[1][0]):
            log('  keys %d..%d min gap %d near (%d, %d, %d) %s' % (i0, i1, d, p[0], p[1], p[2], k))
    return bad


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if '--check-only' in sys.argv:
        print('close samples:', check(a[0], summary='--summary' in sys.argv))
    else:
        first, cut, pos = patch(a[0], a[1])
        print('away keys %d..%d mirrored about x=%d: end (%d, %d); out %s' % (first, cut - 1, STOP_X, pos[cut - 1][0], pos[cut - 1][2], md5(a[1])))
        print('close samples:', check(a[1]))
