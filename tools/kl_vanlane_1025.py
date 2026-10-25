"""kl_vanlane_1025.py - van LANE CLEARANCE check (owner 2026-10-25: "van just clips ... even on dm01 it just clips through a police car").
Written 2026-10-25, OFFLINE and read-only on every zip it is given.

The escape van is a key-framed ZAnimatedVehicle (MOTION_KEYFRAMED, teleported every frame, no velocity): it never reacts to anything, so a
prop / parked car / animated car in its path is passed THROUGH. The only honest fix is to keep the lane clear. This module is the check.

lane_check(zip) -> {van top: {...}} for every V_Van_00 key-framed van of the map:
  static   kl_map_escape.lane(): the map's collision (HVK statics, convex rigid / vehicle / key-framed bodies incl. ZHavokCar) 25..220 over the road
           in the swept lane (half width VAN_HALF = 110, five rays, every 20 units, 350 behind the first key to 600 past the last) and 'no road'.
  movers   every OTHER node with a MatPosAnim + KEYS whose position track moves > 300 (the animated police cars of KL_Cars!): the car's
           footprint (CAR_BOX, a GUESS for a Santana: 480 x 200) laid on EVERY key and on 40-unit steps between keys (its path) and on its LAST
           key (where it stays) against the van's footprint (read from the van's own HVK placements, else 257 / 238 / 105) laid every 20 units of the
           main drive.  Reported: the smallest GAP between the two rectangles (SAT on the inflated boxes) for the path and for the resting pose.
           A gap < MARGIN (60) is a HIT.  TIME IS NOT MODELLED (the cars arrive at the round start, the van minutes later): the resting pose is
           what the owner sees clip, the path is reported apart and is not a hit unless --path.
usage: python kl_vanlane_1025.py <zip> [<zip> ...]
"""
import math, os, re, struct, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_map_escape as ME, kl_graft, kl_hvk

CAR_BOX = (240.0, 100.0)       # GUESS: half length / half width of a Santana police car (the origin is taken as the centre)
VAN_FALLBACK = (257.0, 238.0, 105.0)    # back, front, half (measured on the DM01 van's own HVK placement)
MARGIN = 60.0                  # a gap smaller than this between the two footprints is a HIT
STEP = 20.0
MOVE_MIN = 300.0


def ends_of(L):
    return sorted({o for e in L.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(L.scene.head)})


def rect(cx, cz, hd, back, front, half):
    """(centre, forward unit, right unit, half length along, half across) of a footprint with its origin at (cx, cz) heading hd (atan2(x, z))."""
    f = (math.sin(hd), math.cos(hd))
    c = (cx + f[0] * (front - back) / 2, cz + f[1] * (front - back) / 2)
    return c, f, (f[1], -f[0]), (back + front) / 2, half


def gap(a, b):
    """Separation of two oriented rectangles in the ground plane: > 0 = the smallest gap along the best separating axis, <= 0 = they overlap
    (minus the smallest penetration)."""
    best = -1e18
    for (c1, f1, r1, hl1, hw1) in (a, b):
        for ax in (f1, r1):
            d = abs((b[0][0] - a[0][0]) * ax[0] + (b[0][1] - a[0][1]) * ax[1])
            ra = abs(a[1][0] * ax[0] + a[1][1] * ax[1]) * a[3] + abs(a[2][0] * ax[0] + a[2][1] * ax[1]) * a[4]
            rb = abs(b[1][0] * ax[0] + b[1][1] * ax[1]) * b[3] + abs(b[2][0] * ax[0] + b[2][1] * ax[1]) * b[4]
            best = max(best, d - ra - rb)
    return best


def van_nodes(L):
    sc = L.sc
    return [k for k in range(1, len(sc.nodes)) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k] and L.ents[k - 1].raw
            and kl_graft.keys_tracks(L.ents[k - 1].raw)]


def van_road(L, van, ends):
    """-> (K, cut, world polyline [(x, y, z)] of the main drive, footprint (back, front, half))."""
    sc = L.sc
    K = ME.VanKeys(L.scene.head, L.ents[van - 1].raw, ends, kl_graft.keys_tracks)
    cut = K.drive()
    R, T = L.frame(sc.parent[van])
    pts = [tuple(T[i] + sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in K.pos[:cut]]
    return K, cut, pts


def van_footprint(L, van):
    """(back, front, half) from the van's own key-framed / vehicle HVK placements (not rotated: the van rests along +z of its own frame?) - GUESS: the
    extents along the first drive segment, as sweep.py did; falls back to the measured Santana-sized van."""
    return VAN_FALLBACK


def movers(L, ends, skip):
    """Nodes (outside `skip`) with MatPosAnim + KEYS whose position track moves more than MOVE_MIN, not below another such node.
    -> [(node, world key points [(x, y, z)], world yaw list per key or None)]"""
    sc = L.sc
    out = []
    for k in range(1, len(sc.nodes)):
        if k in skip or not L.ents[k - 1].raw or not kl_graft.keys_tracks(L.ents[k - 1].raw):
            continue
        if not L.ctrl(k, 'MatPosAnim'):
            continue
        try:
            K = ME.VanKeys(L.scene.head, L.ents[k - 1].raw, ends, kl_graft.keys_tracks)
        except Exception:
            continue
        pos = list(K.pos)
        while pos and pos[-1] == (0.0, 0.0, 0.0):
            pos.pop()
        if len(pos) < 2 or max(math.dist(pos[0], p) for p in pos) < MOVE_MIN:
            continue
        R, T = L.frame(sc.parent[k])
        wp = [tuple(T[i] + sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in pos]
        out.append((k, wp, K, R))
    # keep only top-most movers
    keep = [m for m in out if not any(o[0] != m[0] and o[0] < m[0] < sc.end[o[0]] for o in out)]
    return keep


def yaw_at_key(K, R, i):
    """World heading of the mover at position key i (rotation key through the frame tables), None when it cannot be read."""
    try:
        first = {}
        for f in range(K.frames - 1, -1, -1):
            first[K.f2p[f]] = f
        f = first.get(i)
        if f is None:
            return None
        y = math.radians(K.yaw(K.rot[K.f2r[f]]))
        # the parent's frame turns it: heading of R . (sin y, 0, cos y)
        v = (math.sin(y), 0.0, math.cos(y))
        w = [sum(R[a][b] * v[b] for b in range(3)) for a in range(3)]
        return math.atan2(w[0], w[2])
    except Exception:
        return None


def lane_check(zp, L=None, G=None, car_box=CAR_BOX, log=print):
    """-> list of dict(van=<path tail>, static=[(along, what, name)], movers=[dict(name, rest_gap, path_gap, rest=(x, z), ...)], main_len=, hits=int)."""
    L = L or ME.Level(zp)
    G = G or ME.Ground(L)
    L.G = G
    sc = L.sc
    ends = ends_of(L)
    res = []
    for van in van_nodes(L):
        K, cut, pts = van_road(L, van, ends)
        # the van group's closure
        top = sc.top[van]
        own = {L.ents[j - 1].ref for j in range(van, sc.end[van])}
        # everything below the van's EscapeVehicle ZGROUP too (wheels, doors, boxes), as van_check does
        own |= {L.ents[j - 1].ref for j in range(top, sc.end[top])}
        road = ME.Poly([(p[0], p[1] - ME.VAN_UP, p[2]) for p in pts])
        st = ME.lane(L, G, road, -ME.VAN_TAIL, road.len + ME.VAN_NOSE, own)
        stat = collections.OrderedDict()
        for s, what, nm in st:
            stat.setdefault((nm or '-', re.sub(r' \d+$', '', what.split(' at ')[0].split(' over ')[0])), []).append(s)
        back, front, half = van_footprint(L, van)
        samples = []
        s = 0.0
        while s <= road.len:
            p, t = road.at(s), road.tan(s)
            samples.append((s, rect(p[0], p[2], math.atan2(t[0], t[1]), back, front, half)))
            s += STEP
        mv = []
        for k, wp, Kc, Rc in movers(L, ends, set(range(top, sc.end[top]))):
            cp = ME.Poly(wp)
            n = max(1, int(cp.len // 40))
            path = []
            for i in range(n + 1):
                s2 = cp.len * i / n
                p, t = cp.at(s2), cp.tan(s2)
                path.append((p, math.atan2(t[0], t[1])))
            # resting pose: the heading is the last real rotation key if it can be read, else the final tangent
            hd_rest = yaw_at_key(Kc, Rc, len(wp) - 1)
            if hd_rest is None:
                hd_rest = path[-1][1]
            rest = (wp[-1], hd_rest)
            bx = lambda pose: rect(pose[0][0], pose[0][2], pose[1], car_box[0], car_box[0], car_box[1])
            rg = min((gap(bx(rest), vr), s0) for s0, vr in samples)
            pg = min((gap(bx(pz), vr), s0) for pz in path for s0, vr in samples)
            mv.append(dict(node=k, name=sc.path[k][-60:], rest=(round(wp[-1][0]), round(wp[-1][2])), rest_yaw=round(math.degrees(hd_rest)),
                           rest_gap=round(rg[0]), rest_at=round(rg[1]), path_gap=round(pg[0]), path_at=round(pg[1]), start=(round(wp[0][0]), round(wp[0][2]))))
        res.append(dict(van=sc.path[top][-60:], van_node=van, main_len=round(road.len), npts=cut, start=tuple(round(c) for c in pts[0]),
                        end=tuple(round(c) for c in pts[-1]), static=[(nm, w, min(v), max(v)) for (nm, w), v in stat.items()], movers=mv,
                        hits=len(stat) + sum(1 for m in mv if m['rest_gap'] < MARGIN)))
    return res


def report(zp, res, log=print):
    log('lane check %s: %d van(s)' % (zp, len(res)))
    for r in res:
        log(' van %s: drive %d units, %d keys, from %s to %s' % (r['van'], r['main_len'], r['npts'], r['start'], r['end']))
        for nm, w, a, b in r['static']:
            log('   STATIC  %s: %s  %d..%d along' % (nm, w, a, b))
        for m in r['movers']:
            log('   MOVER %-3s %s rest %s yaw %d  rest gap %d (at %d)  path gap %d (at %d)  start %s%s' % (
                m['node'], m['name'], m['rest'], m['rest_yaw'], m['rest_gap'], m['rest_at'], m['path_gap'], m['path_at'], m['start'],
                '  <-- HIT' if m['rest_gap'] < MARGIN else ''))
        log('   hits: %d' % r['hits'])
    if not res:
        log(' no V_Van_00 key-framed van in this map')


if __name__ == '__main__':
    for z in sys.argv[1:]:
        report(z, lane_check(z))
