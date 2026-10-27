"""Read-only audit for translating a whole map by T so every position fits the online int16 range (+-32767).
usage: python tools/kl_shift_audit.py <map.zip> [dx dy dz]     default T = (-12288, 0, -16384) (powers of two: float32 shifts stay exact)
Reports (1) gameplay extents (system includes / clone groups excluded), (2) whether T fits, (3) how many top-level entities a root-level
shift moves, (4) per member file the count of float32 values in the map's coordinate band = places that hold ABSOLUTE positions and
would need their own translation (HVK placements+MOPP offsets, .oct/.rmi/.rmc origins, PF4, .buf head, .sgp ...). See re/map_shift_int16_1027.md."""
import sys, os, struct, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
from kl_int16_range_check import mul, LIM

SYSTEM = (b'AllLevels', b'CloneGroup', b'Heroes')


def positions(zf):
    sc = kl_scene.read(zf)
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))
    out = []

    def go(e, par, top):
        rot = struct.unpack('<12f', e.rot)[:12]; tr = struct.unpack('<4f', e.trans)[:3]
        w = mul(par, (tuple(rot), tuple(tr))); out.append((w[1], e.name, top))
        for k in e.kids: go(k, w, top)
    for r in sc.roots: go(r, ident, r.name)
    return sc, out


def main():
    z = sys.argv[1]; T = tuple(float(v) for v in sys.argv[2:5]) if len(sys.argv) >= 5 else (-12288.0, 0.0, -16384.0)
    zf = zipfile.ZipFile(z); sc, pts = positions(zf)
    far = [p for p in pts if not p[2].startswith(SYSTEM) and (abs(p[0][0]) > 5000 or abs(p[0][2]) > 5000)]
    lo = [min(p[0][i] for p in far) for i in range(3)]; hi = [max(p[0][i] for p in far) for i in range(3)]
    print('gameplay extents (%d placed entities): min %s max %s' % (len(far), [round(v) for v in lo], [round(v) for v in hi]))
    nlo = [lo[i] + T[i] for i in range(3)]; nhi = [hi[i] + T[i] for i in range(3)]
    ok = all(abs(v) <= LIM for i in (0, 2) for v in (nlo[i], nhi[i]))
    print('after T=%s: min %s max %s -> %s' % (T, [round(v) for v in nlo], [round(v) for v in nhi], 'FITS int16' if ok else 'STILL OUT OF RANGE'))
    movers = [r for r in sc.roots if not r.name.startswith(SYSTEM)]
    print('top-level entities: %d, a root-level shift moves %d (system includes stay)' % (len(sc.roots), len(movers)))
    import numpy as np
    bx = (lo[0] - 1000, hi[0] + 1000); bz = (lo[2] - 1000, hi[2] + 1000)
    for n in zf.namelist():
        if n.rsplit('.', 1)[-1].lower() in ('tex', 'wav', 'loc', 'anm', 'xml', 'fxc', 'snd') or zf.getinfo(n).file_size < 64: continue
        d = zf.read(n); a = np.frombuffer(d[:len(d) // 4 * 4], dtype='<f4')
        with np.errstate(all='ignore'): m = (a > 15000) & (a < 48000)
        print('  %-24s floats in band: %8d   (x..z pairs 2 apart: %d)' % (n.split('/')[-1], int(m.sum()), int((m[:-2] & m[2:]).sum())))


if __name__ == '__main__':
    main()
