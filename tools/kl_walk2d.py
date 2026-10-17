"""kl_walk2d.py - a coarse 'can a person walk from A to B' flood fill over a built level's collision (kl_map_escape.Ground).

Why: the campaign levels hold doors and walls that the campaign's scripts open; a graft that drops the scripts keeps the
closed doors. This tool answers, OFFLINE, which pieces of the map enclose a start place, by flooding a plan grid from it.

Model (GUESS: coarse, it is a planning aid, not a proof):
  * a cell has FLOOR heights: the up-facing collision triangles (|ny| > 0.7) that cover the cell's centre;
  * a cell is WALLED when a steep triangle (|ny| < 0.45) crossing the cell spans body height (y 30 .. 150 over the floor)
    or a convex/key-framed box does (kl_map_escape.Ground.boxes);
  * a step from cell to cell is allowed when some floor of one is within STEP of a floor of the other and the target is not walled.
Usage (from tools/):
  python kl_walk2d.py <built folder or zip> x0,z0 x1,z1 [--drop <node-path-substring> ...] [--box xmin,xmax,zmin,zmax]
  --drop removes every collision piece whose entity lies under a node whose path contains the substring (the pieces a script would open).
"""
import collections, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import kl_map_escape as ESC

CELL = 40.0
STEP = 45.0
BODY = (30.0, 150.0)


class Walk:
    def __init__(self, src, box, drop=(), log=print):
        self.L = ESC.Level(src)
        self.g = ESC.Ground(self.L)
        self.box = box                                   # (xmin, xmax, zmin, zmax)
        sc = self.L.sc
        node = {e.ref: i + 1 for i, e in enumerate(self.L.ents)}
        gone = set()
        for pat in drop:
            for k in range(1, len(sc.names)):
                if pat in sc.path[k]:
                    gone.add(k)
        # all nodes under a dropped node
        gone_ref = set()
        for ref, k in node.items():
            j = k
            while j > 0:
                if j in gone:
                    gone_ref.add(ref)
                    break
                j = sc.parent[j]
        self.dropped = len(gone_ref)
        x0, x1, z0, z1 = box
        self.nx, self.nz = int((x1 - x0) / CELL) + 1, int((z1 - z0) / CELL) + 1
        self.floors = [[[] for _ in range(self.nz)] for _ in range(self.nx)]
        self.walls = [[[] for _ in range(self.nz)] for _ in range(self.nx)]       # (ylo, yhi) of steep pieces in the cell
        for (a, b, c, ref, ny) in self.g.tris:
            if ref in gone_ref:
                continue
            xs, zs = (a[0], b[0], c[0]), (a[2], b[2], c[2])
            if max(xs) < x0 or min(xs) > x1 or max(zs) < z0 or min(zs) > z1:
                continue
            if ny > 0.7:
                self._floor(a, b, c)
            elif ny < 0.45:
                self._wall(a, b, c)
        for (typ, ref, lo, hi) in self.g.boxes:
            if ref in gone_ref or hi[0] < x0 or lo[0] > x1 or hi[2] < z0 or lo[2] > z1:
                continue
            for i in range(self._ix(lo[0]), self._ix(hi[0]) + 1):
                for j in range(self._iz(lo[2]), self._iz(hi[2]) + 1):
                    if 0 <= i < self.nx and 0 <= j < self.nz:
                        self.walls[i][j].append((lo[1], hi[1]))

    def _ix(self, x):
        return int(math.floor((x - self.box[0]) / CELL))

    def _iz(self, z):
        return int(math.floor((z - self.box[2]) / CELL))

    def _floor(self, a, b, c):
        x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        z0, z1 = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-9:
            return
        for i in range(max(0, self._ix(x0)), min(self.nx - 1, self._ix(x1)) + 1):
            px = self.box[0] + (i + 0.5) * CELL
            for j in range(max(0, self._iz(z0)), min(self.nz - 1, self._iz(z1)) + 1):
                pz = self.box[2] + (j + 0.5) * CELL
                l1 = ((b[2] - c[2]) * (px - c[0]) + (c[0] - b[0]) * (pz - c[2])) / d
                l2 = ((c[2] - a[2]) * (px - c[0]) + (a[0] - c[0]) * (pz - c[2])) / d
                l3 = 1 - l1 - l2
                if l1 >= -0.02 and l2 >= -0.02 and l3 >= -0.02:
                    self.floors[i][j].append(l1 * a[1] + l2 * b[1] + l3 * c[1])

    def _wall(self, a, b, c):
        ylo, yhi = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        # sample the triangle's plan projection along its edges and its middle line
        pts = []
        for p, q in ((a, b), (b, c), (c, a)):
            n = max(2, int(math.hypot(q[0] - p[0], q[2] - p[2]) / (CELL / 2)))
            for t in range(n + 1):
                f = t / n
                pts.append((p[0] + (q[0] - p[0]) * f, p[2] + (q[2] - p[2]) * f))
        seen = set()
        for x, z in pts:
            i, j = self._ix(x), self._iz(z)
            if 0 <= i < self.nx and 0 <= j < self.nz and (i, j) not in seen:
                seen.add((i, j))
                self.walls[i][j].append((ylo, yhi))

    def blocked(self, i, j, y):
        return any(lo < y + BODY[1] and hi > y + BODY[0] for lo, hi in self.walls[i][j])

    def flood(self, start, limit=400000):
        x, z = start
        i, j = self._ix(x), self._iz(z)
        fl = sorted(self.floors[i][j])
        if not fl:
            raise ValueError('no floor under the start (%s, %s)' % (x, z))
        seen = {(i, j, round(fl[0] / STEP))}
        q = collections.deque([(i, j, fl[0])])
        reach = {}
        while q and len(seen) < limit:
            i, j, y = q.popleft()
            reach[(i, j)] = max(reach.get((i, j), -1e9), y)
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if not (0 <= a < self.nx and 0 <= b < self.nz):
                    continue
                best = None
                for f in self.floors[a][b]:
                    if abs(f - y) <= STEP and not self.blocked(a, b, f) and (best is None or abs(f - y) < abs(best - y)):
                        best = f
                if best is not None and (a, b, round(best / STEP)) not in seen:
                    seen.add((a, b, round(best / STEP)))
                    q.append((a, b, best))
        return reach

    def xz(self, cell):
        return (self.box[0] + (cell[0] + 0.5) * CELL, self.box[2] + (cell[1] + 0.5) * CELL)


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    src = a[0]
    p0 = tuple(float(v) for v in a[1].split(','))
    p1 = tuple(float(v) for v in a[2].split(','))
    drop = [a[i + 1] for i, v in enumerate(a) if v == '--drop']
    box = tuple(float(v) for v in a[a.index('--box') + 1].split(',')) if '--box' in a else (-3000.0, 6000.0, 3000.0, 13000.0)
    w = Walk(src, box, drop)
    print('dropped collision refs: %d' % w.dropped)
    reach = w.flood(p0)
    print('reached cells: %d' % len(reach))
    zs = [w.xz(c)[1] for c in reach]
    xs = [w.xz(c)[0] for c in reach]
    print('extent x %d .. %d  z %d .. %d' % (min(xs), max(xs), min(zs), max(zs)))
    i, j = w._ix(p1[0]), w._iz(p1[1])
    print('target cell reached: %s' % ((i, j) in reach))


if __name__ == '__main__':
    main()
