#!/usr/bin/env python3
r"""city_pano_1107.py - OFFLINE, READ-ONLY. What the live DM05A DRAWS around the roof eyes: a sky panorama by ray casting the render triangles
(the npz of tools/kl_arrival_1107.py geom; Glow / Distance planes excluded, they are billboards).

  python tools/city_pano_1107.py pano [--eye x,y,z] [--az-step 5] [--max-el 45]     skyline elevation per azimuth (first unobstructed elevation)
  (library) Occluder(npz).blocked(eye, pts)                                          True per point whose segment eye->point meets a triangle

Azimuth: 0 = +x (east), 90 = +z (north), degrees; y is up; units cm.
"""
import os
import sys

import numpy as np

NPZ = r'C:\kl_build_1024\arrival_1107\dm05a_render.npz'
BS = chr(92)
EYES = {'escape': (7400.0, 2500.0, 2800.0), 'pad': (8100.0, 3800.0, 4600.0), 'land': (7300.0, 2249.0, 3500.0)}


class Occluder:
    def __init__(self, npz=NPZ):
        d = np.load(npz)
        names = [str(n).lower() for n in d['names']]
        bad = np.array(['glow' in n or 'distance' in n for n in names])
        keep = ~bad[d['owner']]
        t = d['tris'][keep].astype(np.float64)
        self.v0 = t[:, 0].copy()
        self.e1 = t[:, 1] - t[:, 0]
        self.e2 = t[:, 2] - t[:, 0]
        self.n = len(t)

    def first_hit(self, eye, d, tmax=1e12):
        """distance along unit d from eye to the first triangle (or inf)."""
        eye = np.asarray(eye, np.float64)
        p = np.cross(d, self.e2)
        det = np.einsum('ij,ij->i', self.e1, p)
        ok = np.abs(det) > 1e-9
        inv = np.zeros_like(det)
        inv[ok] = 1.0 / det[ok]
        s = eye - self.v0
        u = np.einsum('ij,ij->i', s, p) * inv
        ok &= (u >= 0) & (u <= 1)
        q = np.cross(s, self.e1)
        v = (q @ d) * inv
        ok &= (v >= 0) & (u + v <= 1)
        tt = np.einsum('ij,ij->i', self.e2, q) * inv
        ok &= (tt > 1.0) & (tt < tmax)
        return float(tt[ok].min()) if ok.any() else float('inf')

    def blocked(self, eye, pts):
        eye = np.asarray(eye, np.float64)
        out = []
        for P in pts:
            d = np.asarray(P, np.float64) - eye
            L = float(np.linalg.norm(d))
            out.append(self.first_hit(eye, d / L, L - 1.0) < float('inf'))
        return np.array(out)


def pano(eye, az_step=5, max_el=45, el_step=2.5):
    oc = Occluder()
    els = np.arange(0.0, max_el + 0.01, el_step)
    res = []
    for az in range(0, 360, az_step):
        low = None
        for el in els:
            a, e = np.radians(az), np.radians(el)
            d = np.array([np.cos(e) * np.cos(a), np.sin(e), np.cos(e) * np.sin(a)])
            if oc.first_hit(eye, d) == float('inf'):
                low = el
                break
        res.append((az, low))
    return res


def main(a):
    eye = EYES['escape']
    if '--eye' in a:
        k = a[a.index('--eye') + 1]
        eye = EYES[k] if k in EYES else tuple(float(x) for x in k.split(','))
    step = int(a[a.index('--az-step') + 1]) if '--az-step' in a else 5
    me = float(a[a.index('--max-el') + 1]) if '--max-el' in a else 45
    print('eye', eye, 'azimuth: 0 east, 90 north; value = lowest unobstructed elevation (deg), >%g = walled' % me)
    for az, low in pano(eye, step, me):
        print('%3d %s' % (az, '>%g' % me if low is None else '%.1f' % low))


if __name__ == '__main__':
    main(sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == 'pano' else sys.argv[1:])
