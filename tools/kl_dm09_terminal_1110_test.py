#!/usr/bin/env python3
"""Self-test of the pure logic of kl_dm09_terminal_1110.py (no game, no zips)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm09_terminal_1110 as T

ok = True
def chk(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

# lane_delta: stop lands on the target, y lifted by the floor
d = T.lane_delta((-1853.2, 2.0, 10800.0), -25500.0, 8100.0, -980.0)
chk('lane_delta', abs(-1853.2 + d[0] + 25500) < 1e-6 and abs(10800 + d[2] - 8100) < 1e-6 and d[1] == -980.0)

# to_box
c, h = T.to_box(-7500, -6500, -1000, 2000, -2500, 14000)
chk('to_box', c == (-7000, 500, 5750) and h == (500, 1500, 8250))

# slab_split
chk('split mid', T.slab_split(0, 100, (30, 60)) == ((0, 30), (60, 100)))
chk('split gap covers south', T.slab_split(0, 100, (-10, 60)) == (None, (60, 100)))
chk('split gap covers north', T.slab_split(0, 100, (30, 120)) == ((0, 30), None))
chk('split gap covers all', T.slab_split(0, 100, (-5, 105)) == (None, None))

# corridor_gap: polygons 0 (inside slab, west reaching), 1 (joined), 2 (inside slab but no west reach, unjoined), 3 (far z), 4 (wrong height)
boxes = [(-8000, -7000, 100, 200, 0), (-7200, -6000, 200, 300, 0), (-7400, -7000, 600, 700, 0), (-8000, -7000, 5000, 6000, 0), (-8000, -7000, 120, 180, 900)]
nb = [{1}, {0}, {3}, {2}, set()]
g = T.corridor_gap(boxes, nb, {0, 1, 2, 3, 4}, -7500, -6500, -100, 100, 10)
chk('corridor_gap joined run (no z range: the far seed joins poly 2)', g == (90, 6010))
chk('corridor_gap z range drops far polygons', T.corridor_gap(boxes, nb, {0, 1, 2, 3, 4}, -7500, -6500, -100, 100, 10, zr=(0, 1000)) == (90, 310))
chk('corridor_gap far polygon alone w/o z range', T.corridor_gap(boxes, nb, {3}, -7500, -6500, -100, 100, 0) == (5000, 6000))
chk('corridor_gap far polygon alone with z range', T.corridor_gap(boxes, nb, {3}, -7500, -6500, -100, 100, 0, zr=(0, 1000)) is None)
chk('corridor_gap none', T.corridor_gap(boxes, nb, set(), -7500, -6500, -100, 100, 0) is None)

# in_box, identity and turned
chk('in_box in', T.in_box((0, 0, 0), (0, 0, 0), (1, 1, 1)))
chk('in_box out', not T.in_box((2, 0, 0), (0, 0, 0), (1, 1, 1)))
chk('in_box turned 90 (local +Z = world +X): long z half runs along x', T.in_box((5, 0, 0), (0, 0, 0), (1, 1, 6), face=(1, 0)) and not T.in_box((0, 0, 5), (0, 0, 0), (1, 1, 6), face=(1, 0)))

# sample_path / path_before
pts = [(0, 0, 0), (100, 0, 0), (100, 0, 100)]
sp = T.sample_path(pts, 50)
chk('sample_path ends', sp[0] == (0, 0, 0) and sp[-1] == (100, 0, 100) and len(sp) == 5)
p, dr = T.path_before(pts, 150)
chk('path_before', abs(p[0] - 50) < 1e-6 and p[2] == 0 and dr == (1.0, 0.0))

# run_box orientation
rc, rh, f = T.run_box((10, -980, 20), (1.0, 0.0), -980)
chk('run_box along x', rh == (300.0, 400.0, 2700.0) and rc[1] == -980 + T.RUN_Y_OFF)
rc, rh, f = T.run_box((10, -980, 20), (0.0, 1.0), -980)
chk('run_box along z', rh == (2700.0, 400.0, 300.0))

# exit_box
c, h = T.exit_box((-25500.0, -978.0, 8100.0), -980.0)
chk('exit_box holds stop, ends 25 m before / 20 m after', c[2] - h[2] == 8100 - 2500 and c[2] + h[2] == 8100 + 2000 and T.in_box((-25500, -978, 8100), c, h))

# way_fragment keeps 8 points
w = T.way_fragment([(i, i, i) for i in range(8)], [(100, 0, 100), (200, 0, 200)])
chk('way_fragment', len(w) == 8 and w[0] == 'P1=0 0 0' and w[-1] == 'P8=200 0 200' and w[5] == 'P6=5 5 5' and w[6] == 'P7=100 0 100')

# lane_bad over a fake grid
cell = lambda x, z: (int(x // 20), int(z // 20))
grid = {}
for z in range(0, 200, 20):
    for dx in (-250, -110, 0, 110, 250):
        grid[cell(-1000 + dx, z)] = [(-980.0, 1, 5)]
chk('lane_bad clean', T.lane_bad(grid, cell, -1000.0, -980.0, 0, 200) == [])
grid[cell(-1000, 100)] = [(-980.0, 1, 5), (-900.0, 1, 5)]
chk('lane_bad finds a wall', len(T.lane_bad(grid, cell, -1000.0, -980.0, 0, 200)) == 1)
grid[cell(-1000, 100)] = [(-940.0, 1, 5)]
chk('lane_bad finds a step', len(T.lane_bad(grid, cell, -1000.0, -980.0, 0, 200)) == 1)

# terminal walls: warn_rect grows toward the allowed side only, rects_overlap, in_corridor, the planned walls
chk('warn_rect north', T.warn_rect(0, 10, 100, 120, (0.0, -1.0)) == (0, 10, -200.0, 120))
chk('warn_rect west', T.warn_rect(0, 10, 100, 120, (1.0, 0.0)) == (0, 310.0, 100, 120))
chk('rects_overlap', T.rects_overlap((0, 10, 0, 10), (5, 15, 5, 15)) and not T.rects_overlap((0, 10, 0, 10), (10, 20, 0, 10)))
chk('in_corridor lane / stairs / hall', T.in_corridor(-25500, 8100) and T.in_corridor(-14000, 12000) and T.in_corridor(-20000, 10000))
chk('in_corridor rejects the far hall', not T.in_corridor(-32000, 10000) and not T.in_corridor(-20000, 20000) and not T.in_corridor(-25500, 3000))
chk('4 walls, 4 distinct trios', len(T.TERM_TRIOS) == 4 and len({t[0] for t in T.TERM_TRIOS}) == 4)
chk('no wall touches CORRIDOR', not any(T.rects_overlap(t[2:6], r) for t in T.TERM_TRIOS for r in T.CORRIDOR))
chk('walls span the lane van stop and wait', all(not T.rects_overlap(t[2:6], (-25500 - 1, -25500 + 1, 6000, 8100)) for t in T.TERM_TRIOS))
chk('walls are 3 m or thicker', all(min(t[3] - t[2], t[5] - t[4]) >= 200 for t in T.TERM_TRIOS))

print('RESULT: %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
