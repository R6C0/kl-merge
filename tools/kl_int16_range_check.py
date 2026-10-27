"""Read-only audit: which maps keep entities beyond the online int16 position range (+-32767).
usage: python tools/kl_int16_range_check.py <map.zip> [...]   (self-test: --selftest)
World positions compose the scene tree (rot 3x4 rows at 0:3,4:7,8:11 + trans). See re/engine_facts.md 0x5e4a22."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
LIM = 32767.0


def mul(parent, local):
    """parent, local = (rot12, trans3); returns the composed world (rot12, trans3)."""
    pr, pt = parent; lr, lt = local
    t = tuple(pt[i] + sum(lt[j] * pr[j * 3 + i] for j in range(3)) for i in range(3))
    r = []
    for a in range(3):
        for c in range(3):
            r.append(sum(lr[a * 3 + k] * pr[k * 3 + c] for k in range(3)))
    return tuple(r), t


def audit(zipfile):
    import kl_scene
    import zipfile as _z
    with _z.ZipFile(zipfile) as zf: sc = kl_scene.read(zf)
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))
    out = []

    def go(e, par):
        import struct
        rot = struct.unpack('<12f', e.rot)[:12] if isinstance(e.rot, (bytes, bytearray)) else e.rot
        tr = struct.unpack('<4f', e.trans)[:3] if isinstance(e.trans, (bytes, bytearray)) else e.trans
        w = mul(par, (tuple(rot), tuple(tr)))
        p = w[1]
        if max(abs(p[0]), abs(p[2])) > LIM: out.append((e.name, p))
        for k in getattr(e, 'kids', []) or []: go(k, w)
    for r in sc.roots: go(r, ident)
    return out


def selftest():
    I = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    assert mul((I, (30000.0, 0, 0)), (I, (4000.0, 0, 0)))[1][0] == 34000.0
    import ctypes
    assert ctypes.c_int16(34000).value == -31536 and ctypes.c_int16(34153).value == -31383   # Q27 wrapped values
    print('selftest ok')


if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest(); sys.exit(0)
    for z in sys.argv[1:]:
        o = audit(z); print('%s: %d entities beyond +-%d' % (z, len(o), LIM))
        for n, p in o[:5]: print('   ', n, tuple(round(v) for v in p))
