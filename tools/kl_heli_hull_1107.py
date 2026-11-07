#!/usr/bin/env python3
r"""kl_heli_hull_1107.py - swept-HULL clearance of the DM05A escape heli against the level's RENDER triangles. OFFLINE, read-only.

What the hull is (all numbers are READ from the live zip, F01_Main.zip md5 1d325299, by tools/kl_heli_hull_1107.py facts):
  The ZHeli node 'EscapeSetup!EscapeChopper\Escape_Chopper\V_Coli_Shot_01' (model root chunk 35251, local (0, 330, -58.26) in the group) is the WHOLE visible
  helicopter, despite its name: 13 drawn meshes. Its bounds in the model frame are x -781..785, y -333..81, z -920..781:
    - V_Helicopter_Rotor_01a (mesh 35238) = the MAIN ROTOR: a flat 9-vertex disc, x -781..785, z -784..781, y 38..81  <- the '785 cm' of the brief
    - V_Helicopter_Rotor_01a (mesh 35242) = the TAIL ROTOR, z -920..-636, x = 2 (a plane), y -244..40
    - V_VEN_Escape_Helicopter_Exterior (mesh 35185) = the fuselage, x +-141, y -333..39, z -902..451; police-heli interior meshes inside it.
  In the heli GROUP frame (group origin = the point the route moves = the 'pivot') add the node offset (0, 330, -58.26):
    fuselage x +-141, y -3..369, z -978..393; main rotor disc: radius 785, centre (2, 390..411, -60), thickness ~43; tail rotor to z -978.
  So the lowest point of the model is ~ the pivot (y -3), the rotor is ~3.9 m above the pivot, the disc radius is 7.85 m.
  P = proven from the live zip. G = guess: the heli's YAW on the route is not known offline (the group has a fixed 'editor' yaw, the engine's ZHeli
  controller may turn it along the spline). The hull is therefore YAW-AGNOSTIC: a vertical cylinder of radius R_HULL around the pivot (horizontal reach
  of the tail tip is 978 from the pivot, of the rotor tip 785 + 60 = 845), y from -10 to Y_TOP, sampled on a polar grid <= SPACING apart. SPHERE_PAD_
  below says how far every sample must be from any triangle.

Clearance measure: unsigned distance field (50 cm voxels, exact Euclidean transform capped at CAP) of densely sampled render triangles; the voxel
quantisation error is <= 0.87 * CELL (half a voxel diagonal) and is SUBTRACTED (conservative). `verify()` then re-measures a route with the exact
point-to-triangle distance of kl_arrival_1107.Mesh at every hull sample of every route sample.

  python tools/kl_heli_hull_1107.py facts
  python tools/kl_heli_hull_1107.py field     # builds C:\kl_build_1024\arrival_1107\field50.npz
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = r'C:\kl_build_1024\arrival_1107'
NPZ = os.path.join(OUT, 'dm05a_render.npz')
FIELD = os.path.join(OUT, 'field50.npz')

CELL = 50.0
CAP = 1500.0
LO = np.array([3500.0, 500.0, -3000.0])
HI = np.array([18500.0, 9000.0, 8500.0])

# hull (P: from the live zip, see the docstring)
ROTOR_R = 785.0
ROTOR_Y = (368.0, 411.0)            # rotor disc y band above the pivot (node 330 + model 38..81)
ROTOR_C = (2.0, -58.0)              # disc centre (x, z) in the group frame
TAIL_Z = -978.0                     # tail rotor tip, group frame
BODY_Y = (-3.0, 369.0)
R_HULL = 990.0                      # yaw-agnostic cylinder radius around the pivot (G: the yaw is unknown)
Y_BOT, Y_TOP = -10.0, 420.0
SPACING = 140.0


def hull_samples(r=R_HULL, spacing=SPACING):
    """Offsets (n,3) from the pivot: a polar grid over the cylinder (3 layers) plus the rim rings (the extremes)."""
    pts = []
    ys = (Y_BOT, (Y_BOT + Y_TOP) / 2, Y_TOP)
    pts.extend((0.0, y, 0.0) for y in ys)
    k = 1
    while k * spacing < r + spacing:
        rad = min(k * spacing, r)
        n = max(6, int(math.ceil(2 * math.pi * rad / spacing)))
        for i in range(n):
            a = 2 * math.pi * i / n
            for y in ys:
                pts.append((rad * math.cos(a), y, rad * math.sin(a)))
        if rad >= r:
            break
        k += 1
    return np.array(pts, np.float64)


def sample_triangles(T, step=CELL / 2):
    """Dense surface points of triangles T [n,3,3] (float64), every point <= step from the true surface along an edge direction."""
    out = []
    e = np.maximum(np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.maximum(np.linalg.norm(T[:, 2] - T[:, 1], axis=1), np.linalg.norm(T[:, 0] - T[:, 2], axis=1)))
    nsub = np.maximum(1, np.ceil(e / step).astype(int))
    for n in np.unique(nsub):
        sel = T[nsub == n]
        uv = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
        u = np.array([a for a, _ in uv])[None, :, None]
        v = np.array([b for _, b in uv])[None, :, None]
        p = sel[:, 0:1] * (1 - u - v) + sel[:, 1:2] * u + sel[:, 2:3] * v
        out.append(p.reshape(-1, 3))
    return np.concatenate(out)


def build_field(npz=NPZ, log=print):
    d = np.load(npz)
    t, o, names = d['tris'].astype(np.float64), d['owner'], list(d['names'])
    keep = np.array([('glow' not in x.lower() and 'distance' not in x.lower()) for x in names])
    t = t[keep[o]]
    m = ~(((t.max(axis=1) < LO).any(axis=1)) | ((t.min(axis=1) > HI).any(axis=1)))
    t = t[m]
    log('%d triangles in the region' % len(t))
    P = sample_triangles(t)
    log('%d surface samples' % len(P))
    shape = tuple(int(math.ceil((HI[a] - LO[a]) / CELL)) for a in range(3))
    ix = np.floor((P - LO) / CELL).astype(np.int64)
    ok = ((ix >= 0) & (ix < np.array(shape))).all(axis=1)
    ix = ix[ok]
    big = (CAP + 2 * CELL) ** 2
    f = np.full(shape, big, np.float32)
    f[ix[:, 0], ix[:, 1], ix[:, 2]] = 0.0
    w = int(CAP / CELL) + 2
    for ax in range(3):
        g = f.copy()
        for s in range(1, w + 1):
            c = np.float32((s * CELL) ** 2)
            a = [slice(None)] * 3
            b = [slice(None)] * 3
            a[ax], b[ax] = slice(s, None), slice(0, -s)
            np.minimum(g[tuple(a)], f[tuple(b)] + c, out=g[tuple(a)])
            a[ax], b[ax] = slice(0, -s), slice(s, None)
            np.minimum(g[tuple(a)], f[tuple(b)] + c, out=g[tuple(a)])
        f = np.minimum(g, big)
    dist = np.sqrt(f).astype(np.float32)
    np.savez_compressed(FIELD, dist=dist, lo=LO, cell=CELL)
    log('field %s saved, occupied voxels %d' % (shape, len(np.unique(ix, axis=0))))
    return dist


class Field:
    def __init__(self, path=FIELD):
        d = np.load(path)
        self.d, self.lo, self.cell = d['dist'], d['lo'], float(d['cell'])

    def at(self, P):
        """Conservative distance (cm) to the nearest triangle at points P [n,3]: trilinear-free nearest voxel minus half a voxel diagonal, >= 0."""
        i = np.floor((np.asarray(P) - self.lo) / self.cell + 0.5).astype(np.int64)
        i = np.clip(i, 0, np.array(self.d.shape) - 1)
        return np.maximum(0.0, self.d[i[..., 0], i[..., 1], i[..., 2]] - 0.87 * self.cell)

    def hull(self, p, hs=None):
        """Smallest conservative clearance of the hull at pivot positions p [n,3] -> [n]."""
        hs = hull_samples() if hs is None else hs
        p = np.atleast_2d(p)
        out = np.empty(len(p))
        for k in range(len(p)):
            out[k] = self.at(p[k] + hs).min()
        return out


def main(a):
    if not a:
        print(__doc__)
        return 2
    if a[0] == 'field':
        build_field()
        return 0
    if a[0] == 'facts':
        print('hull samples:', len(hull_samples()), 'R_HULL', R_HULL)
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
