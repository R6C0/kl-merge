"""Offline ray casts against a level's .HVK collision: a model of Dog Days' player ray 0x7daa80 for the loader climb.
Reads the level zip (the installed one or a build), every shape placement in world cm (y up), and answers
segment casts with DD's filter rule for the climb masks: a sub-part is hit when (its flags & mask & 0xff) != 0
(0x20 = solid for rays, 0x08 = hero-only walls; mask 0x28 sees both). Layers are ignored: row 11 of DD's layer
matrix takes static, keyframed and rigid bodies alike. Not modelled: hidden/disabled entities (node flags
0x400/0x800 skip a hit in game), moving bodies (doors, the van's keyframed parts are taken where the file puts them).
Placement transform: world = 100 * (P + R v) (conv 'col'). Checked against the game: the five rays of the
11 Oct 06:02 dry press (work/smoke/1011_060124/log.txt) come out within 0.2 cm, same normal; conv 'row' (v R) does not.
usage: hvk_ray.py <level.zip> x y z dx dy dz [mask=0x20]"""
import math, os, struct, sys, zipfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'work', 'ext', 'kl-merge', 'tools'))
import kl_hvk, kl_gms, kl_scene

TYPES = {1: 'STATIC', 2: 'RIGID', 3: 'VEHICLE', 4: 'KEYFRAMED', 5: 'WEAPON'}


class Inst:
    __slots__ = ('shape', 'P', 'R', 'ref', 'lo', 'hi', 'tris', 'wverts')


class Collision:
    def __init__(self, zip_path, conv='col'):
        self.conv = conv
        z = zipfile.ZipFile(zip_path)
        nm = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        self.hvk = kl_hvk.Hvk(z.read(nm['.hvk']))
        sc = kl_scene.Scene(kl_gms.unpack(z.read(nm['.gms'])), z.read(nm['.buf']))
        self.ents = {}
        for e in sc.entities():
            self.ents.setdefault(e.ref, e)
        self.insts = []
        for s in self.hvk.shapes:
            s.lverts = [struct.unpack_from('<3f', s.verts, k * s.vstride) for k in range(len(s.verts) // s.vstride)]
            if s.convex:
                s.lplanes = [struct.unpack_from('<4f', s.planes, 16 * k) for k in range(len(s.planes) // 16)]
            else:
                s.ltris = struct.unpack('<%dH' % (len(s.idx) // 2), s.idx)
                fl = []
                for _su, f, n in s.sub:
                    fl += [f] * n
                s.triflags = fl
            for raw in s.inst:
                i = Inst(); i.shape = s; i.ref = kl_hvk.ref(raw)
                i.P = struct.unpack_from('<3f', raw, 0); i.R = struct.unpack_from('<9f', raw, 12)
                w = [self.to_world(i, v) for v in s.lverts]
                i.wverts = w; i.tris = None
                i.lo = tuple(min(v[a] for v in w) for a in range(3)); i.hi = tuple(max(v[a] for v in w) for a in range(3))
                self.insts.append(i)
        self.grid = {}                       # xz cells of CELL cm -> instance indices (short rays only touch a few)
        for k, i in enumerate(self.insts):
            for cx in range(int(i.lo[0] // self.CELL), int(i.hi[0] // self.CELL) + 1):
                for cz in range(int(i.lo[2] // self.CELL), int(i.hi[2] // self.CELL) + 1):
                    self.grid.setdefault((cx, cz), []).append(k)

    CELL = 1000.0

    def _near(self, o, seg):
        x0, x1 = sorted((o[0], o[0] + seg[0])); z0, z1 = sorted((o[2], o[2] + seg[2]))
        ks = set()
        for cx in range(int((x0 - 2) // self.CELL), int((x1 + 2) // self.CELL) + 1):
            for cz in range(int((z0 - 2) // self.CELL), int((z1 + 2) // self.CELL) + 1):
                ks.update(self.grid.get((cx, cz), ()))
        return [self.insts[k] for k in sorted(ks)]

    # -- transforms (local metres <-> world cm)
    def to_world(self, i, v):
        P, m = i.P, i.R
        if self.conv == 'col':
            return tuple(100.0 * (P[a] + m[3 * a] * v[0] + m[3 * a + 1] * v[1] + m[3 * a + 2] * v[2]) for a in range(3))
        return tuple(100.0 * (P[c] + v[0] * m[c] + v[1] * m[3 + c] + v[2] * m[6 + c]) for c in range(3))

    def to_local(self, i, w, point=True):
        P, m = i.P, i.R
        d = [w[a] / 100.0 - (P[a] if point else 0.0) for a in range(3)]
        if self.conv == 'col':
            return tuple(m[j] * d[0] + m[3 + j] * d[1] + m[6 + j] * d[2] for j in range(3))
        return tuple(d[0] * m[3 * j] + d[1] * m[3 * j + 1] + d[2] * m[3 * j + 2] for j in range(3))

    def dir_world(self, i, n):
        m = i.R
        if self.conv == 'col':
            return tuple(m[3 * a] * n[0] + m[3 * a + 1] * n[1] + m[3 * a + 2] * n[2] for a in range(3))
        return tuple(n[0] * m[c] + n[1] * m[3 + c] + n[2] * m[6 + c] for c in range(3))

    def name(self, ref, full=False):
        e = self.ents.get(ref)
        if not e:
            return '?%d' % ref
        if not full:
            return e.name.decode('latin1')
        p = []
        while e:
            p.append(e.name.decode('latin1')); e = e.parent
        return '\\'.join(reversed(p[:4]))

    # -- casting
    @staticmethod
    def _seg_box(o, seg, lo, hi, pad=1.0):
        t0, t1 = 0.0, 1.0
        for a in range(3):
            if abs(seg[a]) < 1e-9:
                if o[a] < lo[a] - pad or o[a] > hi[a] + pad:
                    return False
            else:
                ta, tb = (lo[a] - pad - o[a]) / seg[a], (hi[a] + pad - o[a]) / seg[a]
                if ta > tb:
                    ta, tb = tb, ta
                t0, t1 = max(t0, ta), min(t1, tb)
                if t0 > t1:
                    return False
        return True

    def _hit_mesh(self, i, o, seg, mask):
        s = i.shape; w = i.wverts; best = None
        T = s.ltris
        for t in range(len(T) // 3):
            if not (s.triflags[t] & mask & 0xff):
                continue
            a, b, c = w[T[3 * t]], w[T[3 * t + 1]], w[T[3 * t + 2]]
            e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            p = (seg[1] * e2[2] - seg[2] * e2[1], seg[2] * e2[0] - seg[0] * e2[2], seg[0] * e2[1] - seg[1] * e2[0])
            det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2]
            if abs(det) < 1e-9:
                continue
            inv = 1.0 / det
            tv = (o[0] - a[0], o[1] - a[1], o[2] - a[2])
            u = (tv[0] * p[0] + tv[1] * p[1] + tv[2] * p[2]) * inv
            if u < 0 or u > 1:
                continue
            q = (tv[1] * e1[2] - tv[2] * e1[1], tv[2] * e1[0] - tv[0] * e1[2], tv[0] * e1[1] - tv[1] * e1[0])
            v = (seg[0] * q[0] + seg[1] * q[1] + seg[2] * q[2]) * inv
            if v < 0 or u + v > 1:
                continue
            f = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv
            if 0 <= f <= 1 and (best is None or f < best[0]):
                n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
                ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
                n = tuple(x / ln for x in n)
                if n[0] * seg[0] + n[1] * seg[1] + n[2] * seg[2] > 0:      # face the ray origin (Havok convention)
                    n = tuple(-x for x in n)
                best = (f, n)
        return best

    def _hit_convex(self, i, o, seg, mask):
        s = i.shape
        if not any(f & mask & 0xff for _su, f, _n in s.sub):
            return None
        lo_, ld = self.to_local(i, o), self.to_local(i, seg, point=False)
        t0, t1, nin = 0.0, 1.0, None
        for p in s.lplanes:
            num = -(p[0] * lo_[0] + p[1] * lo_[1] + p[2] * lo_[2] + p[3])
            den = p[0] * ld[0] + p[1] * ld[1] + p[2] * ld[2]
            if abs(den) < 1e-12:
                if num < 0:
                    return None
                continue
            t = num / den
            if den < 0:
                if t > t0:
                    t0, nin = t, p
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return None
        if nin is None:          # origin inside the hull: Havok reports no entry hit
            return None
        return (t0, self.dir_world(i, nin[:3]))

    def ray(self, o, seg, mask=0x20, skip=()):
        """-> None or dict(frac, hit, n, ref, name, type) of the nearest hit along o -> o + seg (cm)."""
        best = None
        for i in self._near(o, seg):
            if i.ref in skip or not self._seg_box(o, seg, i.lo, i.hi):
                continue
            h = self._hit_convex(i, o, seg, mask) if i.shape.convex else self._hit_mesh(i, o, seg, mask)
            if h and (best is None or h[0] < best[0]):
                best = (h[0], h[1], i)
        if not best:
            return None
        f, n, i = best
        return dict(frac=f, hit=tuple(o[a] + seg[a] * f for a in range(3)), n=tuple(n), ref=i.ref, name=self.name(i.ref),
                    path=self.name(i.ref, True), type=TYPES.get(i.shape.type, i.shape.type), flags=i.shape.flags)

    def find(self, pat):
        return [i for i in self.insts if pat in self.name(i.ref)]


if __name__ == '__main__':
    C = Collision(sys.argv[1])
    a = [float(x) for x in sys.argv[2:8]]
    print(C.ray(a[:3], a[3:6], int(sys.argv[8], 0) if len(sys.argv) > 8 else 0x20))
