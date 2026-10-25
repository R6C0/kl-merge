#!/usr/bin/env python3
"""
pd2_gun_fit.py - how pd2_gun.SCALE / SHIFT were found (1025d). OFFLINE, reads only the stock slot folder and the PD2 mesh.

    python pd2_gun_fit.py <slot folder with the STOCK Type 81 (F01_Main.zip)> [scale ...]

The PD2 AKM (axis map + the 10 degree nose-down turn, pd2_gun.TURN_DEG) is laid on the stock Type 81 by a grid search over the shift
(x, y) at each given scale (default 1.077 1.04 1.02 1.0). Cost, all centimetres, on area-sampled triangle surfaces:
  grip   mean distance (worst 20 % left out) from the AKM's points in kl_map_guns.GRIP_ZONE to the Type 81's, and back
  fore   mean |difference| of the two guns' lowest surface y in 2 cm bins over x 36 .. 52 (what the left hand holds from below)
  muzzle 0.3 x |AKM x max - 71.43|
The z shift is not fitted: it is the gun's axis, w_bone_frame z (0.65). Prints the best (cost, shift) per scale.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import pd2_gun as P, pd2_gun_preview as V, kl_chars as C, kl_guns, kl_prmgraph as G, kl_map_guns as MG

MUZZLE_X = 71.43                         # the stock Type 81's x max
BINS = np.arange(36, 52, 2.0)


def sample(pos, tris, rng, dens=0.8):
    """the vertices + random points on every triangle (about `dens` per cm2, at most 60 per triangle)"""
    pos = np.array(pos); out = [pos]
    for a, b, c in tris:
        A, B, K = pos[a], pos[b], pos[c]
        n = int(min(60, np.linalg.norm(np.cross(B - A, K - A)) / 2 * dens))
        if n < 1:
            continue
        u = rng.random((n, 2)); m = u.sum(1) > 1; u[m] = 1 - u[m]
        out.append(A + u[:, :1] * (B - A) + u[:, 1:] * (K - A))
    return np.vstack(out)


def _nn(a, b):
    out = np.empty(len(a))
    for i in range(0, len(a), 500):
        out[i:i + 500] = np.sqrt(((a[i:i + 500, None, :2] - b[None, :, :2]) ** 2).sum(2).min(1))
    return out


def _trim(d, k=0.8):
    d = np.sort(d); return d[:max(8, int(len(d) * k))].mean()


def _zone(Pt, g=0.0):
    z = MG.GRIP_ZONE
    return (Pt[:, 0] >= z[0] - g) & (Pt[:, 0] <= z[1] + g) & (Pt[:, 1] >= z[2] - g) & (Pt[:, 1] <= z[3] + g)


def _under(Pt):
    return np.array([Pt[(Pt[:, 0] >= b) & (Pt[:, 0] < b + 2), 1].min() if ((Pt[:, 0] >= b) & (Pt[:, 0] < b + 2)).any() else np.nan for b in BINS])


def main(folder, scales):
    lv = C.Lv(folder); lv.beside, lv.side = {}, {}
    sc, _raw = lv.scene(); p = G.read(lv['.prm'], 'dd')
    root = C.person(sc, kl_guns.gun_node(sc, 'Rifle_Type81'))[0]
    rng = np.random.default_rng(1)
    parts = [o for o in C.objects(p, root) if p.u32(o, 0x3c) in (1, 4) and p.chunks[o][0x0e] != 16]      # body, sight, slide: not the magazine, not the box
    host = np.vstack([sample(*V.part_mesh(p, o), rng) for o in parts])
    hz, hu = host[_zone(host, 2)], _under(host)
    plate, _df = P.pd2_plate(1.0, (0.0, 0.0, 0.0))          # axis map + turn only
    A1 = sample(plate.pos, plate.tris, rng)

    def cost(s, tx, ty):
        A = A1 * s + np.array([tx, ty, 0.0])
        az = A[_zone(A)]
        if len(az) < 10:
            return 1e9
        au = _under(A)
        if np.isnan(au - hu).any():
            return 1e9
        return _trim(_nn(az, hz)) + _trim(_nn(hz, A[_zone(A, 2)])) + np.abs(au - hu).mean() + 0.3 * abs(A[:, 0].max() - MUZZLE_X)
    for s in scales:
        best = min((cost(s, a, b), a, b) for a in np.arange(5, 14, 0.5) for b in np.arange(-1, 6, 0.5))
        fine = min((cost(s, a, b), a, b) for a in np.arange(best[1] - 0.5, best[1] + 0.51, 0.1) for b in np.arange(best[2] - 0.5, best[2] + 0.51, 0.1))
        print('scale %.3f: cost %.3f shift x %.1f y %.1f' % (s, fine[0], fine[1], fine[2]))


if __name__ == '__main__':
    main(sys.argv[1], [float(x) for x in sys.argv[2:]] or [1.077, 1.04, 1.02, 1.0])
