#!/usr/bin/env python3
"""
VET THE COVER BOXES OF A FINISHED MAP: can the player stand at every side of every cover box? (2026-10-24 17:00)
OFFLINE: reads a map zip, writes nothing but a JSON report when asked.

    python kl_cover_vet.py scan <zip> [--json out.json] [--all]    per cover box, per side: is the place the player would
                                                                    stand at (side middle + STAND outward) free?
    (library)  vet(L) -> {node: report}  with L = kl_cover_add.Lite(zip)

WHY (owner 2026-10-24 16:50: 'sometimes going into cover it puts me inside the object and im stuck for the round').
A cover is a box and its FOUR sides (kl2 0x603830: four corners on the box floor, re/bots_dynamic.md 3.1); the player's
cover places are on its sides. kl_cover_add.sparse() lays a box 'IN the solid' object it found, a model that fits the
object's rectangle within OVER (40) on each axis - so a box may be SHORTER than the object (kl_fa_cover.fit: pushed to the
end / side nearest the place) and then two of its four sides are INSIDE the object, and a box against a wall has a side
inside the wall. A player who takes cover from the diagonal / the end of such a box is put on a side that has no free
floor. This tool measures exactly that on the map's own static collision (kl_fa_cover.Solid):
    side S = side middle + STAND outward (in the plan), on the box's floor;
    BLOCKED  when static collision outlines of the planes 45 / 75 / 110 over the floor come within BODY of S
             (kl_fa_cover.scan, raster CELL 10), or
    ELEVATED when the collision floor at S is more than STEP over the box floor (S is on / in a solid), or
    DROP     when it is more than DROP under it (S is over an edge / pit).
GUESSES: STAND = 55 and BODY = 35 (the player's radius and where the cover movement puts him are NOT read from the exe:
the numbers are a plausible player, and the tool is for RANKING boxes, not a proof); a movable thing (crate, car) is not
in the static collision and is not seen.
"""
import collections, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa_cover as C

STAND = 55.0        # GUESS: how far out of a side the player's centre is
BODY = 35.0         # GUESS: the player's radius against a wall
STEP = 30.0         # a floor this far over the box floor at S: S is on / in a solid
DROP = 70.0         # ... under it: S is over an edge
GATHER = 500.0
PLANES = (45.0, 75.0, 110.0)


def sides(B, b):
    """The four sides of the box dict b (kl_fa_cover.all_boxes) -> [(name, side middle xz, outward unit xz)] and the
    box floor height in the world, the middle xz; None for a box without a plain model box."""
    bb = b['bb']
    if not bb:
        return None
    k = b['node']
    cx, cz = (bb[0] + bb[3]) / 2, (bb[2] + bb[5]) / 2
    hx, hz = (bb[3] - bb[0]) / 2, (bb[5] - bb[2]) / 2
    fy = bb[1]
    mid = B.world(k, (cx, fy, cz))
    out = []
    for nm, q in (('+x', (cx + hx, fy, cz)), ('-x', (cx - hx, fy, cz)), ('+z', (cx, fy, cz + hz)), ('-z', (cx, fy, cz - hz))):
        w = B.world(k, q)
        dx, dz = w[0] - mid[0], w[2] - mid[2]
        n = math.hypot(dx, dz)
        if n < 1e-6:
            return None
        out.append((nm, (w[0], w[2]), (dx / n, dz / n)))
    return mid, out, (2 * hx, 2 * hz, bb[4] - bb[1])


def side_state(S, occ, mid_y, p):
    """'free' | 'blocked' | 'elevated' | 'drop' for the standing place p = (x, z)."""
    for h in PLANES:
        for cells in occ[h].values():
            for c in cells:
                if abs((c[0] + .5) * C.CELL - p[0]) < BODY + C.CELL and abs((c[1] + .5) * C.CELL - p[1]) < BODY + C.CELL \
                        and math.hypot((c[0] + .5) * C.CELL - p[0], (c[1] + .5) * C.CELL - p[1]) < BODY:
                    return 'blocked'
    g = S.floor(p[0], mid_y, p[1], reach=150.0)
    if g is not None:
        if g - mid_y > STEP:
            return 'elevated'
        if mid_y - g > DROP:
            return 'drop'
    return 'free'


def vet(L, only=None, log=print):
    """-> {node: {'name', 'mid', 'size', 'sides': {name: state}, 'bad': n}} for every cover box (or the names `only` accepts)."""
    B, S = L.B, L.solid
    rep = {}
    for b in L.boxes:
        if b.get('kind') is None or b.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ':
            continue
        if only and not only(b['name']):
            continue
        sd = sides(B, b)
        if sd is None:
            continue
        mid, ss, size = sd
        gy = S.floor(mid[0], mid[1] + 5.0, mid[2], reach=60.0)
        fy = mid[1] if gy is None else gy
        occ, _segs = S.scan(mid[0], fy, mid[2], GATHER)
        st = {}
        for nm, m, d in ss:
            p = (m[0] + d[0] * STAND, m[1] + d[1] * STAND)
            st[nm] = side_state(S, occ, fy, p)
        bad = [n for n, v in st.items() if v != 'free']
        rep[b['node']] = {'name': b['name'], 'mid': [round(v, 1) for v in mid], 'size': [round(v, 1) for v in size], 'sides': st, 'bad': len(bad)}
    return rep


def summary(rep, log=print):
    c, by = collections.Counter(), collections.Counter()
    for r in rep.values():
        tag = 'KM' if '_KM_' in r['name'] else 'KL' if '_KL_' in r['name'] else 'map'
        c[tag, r['bad']] += 1
        for v in r['sides'].values():
            by[tag, v] += 1
    for tag in ('map', 'KL', 'KM'):
        n = sum(v for (t, _b), v in c.items() if t == tag)
        if n:
            log('%-4s %4d boxes: sides blocked on 0/1/2/3/4 sides = %s   side states %s' % (
                tag, n, [c.get((tag, i), 0) for i in range(5)], {k[1]: v for k, v in sorted(by.items()) if k[0] == tag}))


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'scan':
        import kl_cover_add as A
        A.use_slot(a[1])
        L = A.Lite(a[1])
        rep = vet(L)
        summary(rep)
        if '--json' in a:
            with open(a[a.index('--json') + 1], 'w') as fh:
                json.dump(rep, fh, indent=1)
        if '--all' in a:
            for n, r in sorted(rep.items()):
                if r['bad']:
                    print(r['name'], r['mid'], r['size'], r['sides'])
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
