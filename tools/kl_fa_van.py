#!/usr/bin/env python3
"""
Retomoto Tower: the escape van drives STRAIGHT, on the road. Offline; nothing here installs anything
or starts the game. Spec and evidence: re/retomoto_ai.md 1.2 and 6.

Owner, 2026-10-09: 'make sure the car doesn't clip ... so you can see the van actually leave like a
normal car since currently its trajectory is pretty silly and clips in the floor'.

WHY IT CLIPPED AND SWERVED (all measured on the files)
  F07's van is key-framed: the KEYS chunk of `V_Van_00` names six tables in the .buf head
  (kl_graft.keys_tracks). Table 5 = positions, 3 floats a key, in the node's LOCAL space; table 2 =
  rotations, 4 x int16 a key = a quaternion (x, y, z, w) / 32767 (CONFIRMED: the heading of local +Z
  from these keys follows the tangent of the positions; the keys turn about Y only). Tables 0 / 3 map
  frames to keys and tables 1 / 4 are not decoded - they are not touched, and no key is added,
  dropped or reordered, so they address the same keys as before.
  - height: the van's origin is 2 above F07's road (baked y -198, road -200). kl_fa_author laid it at
    ROAD_Y = -40, the y the HOOK reports for the player's feet. The collision floor of Retomoto's
    carriageway is y 0 (raised strips at y 20: the median x -3100..-2900 and both sides), so the van
    drove 40 under the road.
  - path: van 01's drive is L-shaped in F07; fitted across the road it started in the west lane,
    crossed the median to the east kerb and swerved back west.

WHAT IS BUILT
  The main drive (wait -> stop -> away) is laid on ONE straight line: x = LANE_X, heading north,
  y = VAN_Y. A key keeps its distance along the drive (so the van's speed profile is the baked one)
  and its sideways offset from the drive (the four crash pieces swerve as they did, clamped to the
  carriageway). The approach is scaled so that the van waits at WAIT_Z and stops at STOP_Z. All
  rotation keys become the identity: nose north. Everything else with a place below the van's group
  (stop marker, rear-door box, escape cameras) moves with the same mapping. The group itself becomes
  identity at the origin: the keys are world positions now.
  GUESS: that a crash piece reads well without its yaw. The main drive is exact.

THE LANE (measured, re/retomoto_ai.md 1.2 and the table in section 6): the east carriageway is at
y 0 for x -2800..-1500 from z 5000 to 16000. x -1850 passes every static vehicle from z 8200 north:
bus #02 (x -1695..-1357) ends at z 6629 and V_JPN_Civilian_B_00#18 (x -1861..-1681) at z 8120, both
SOUTH of the waiting place; the far road block's cars are west of x -2238. So NO PROP IS REMOVED.

    python kl_fa_van.py plan        the drive before and after, on stock F07 (no build; 15 s)
    python kl_fa_van.py check <archive>   the van of a built level: straight? on the floor? clear?

FOR kl_fa_street: `kl_fa_van.straighten(S, log)` after kl_fa_author.prepare_host(S) and before the
street layer reads the van (kl_fa_street.prepare_host does it; '--van-bent' = the old drive).
"""
import math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_gms, kl_scene, kl_maps
import kl_fa_author as au

STRAIGHT = True                         # False ('--van-bent'): F07's drive as kl_fa_author fits it
VAN = 0                                 # index into kl_fa_author.VANS: the van kl_fa_street calls
LANE_X = -1850.0                        # measured free lane of the east carriageway (docstring)
VAN_Y = 2.0                             # carriageway floor y 0 (kl_escape.Walk on M09_B's .HVK) + the 2 the van has over F07's road
STOP_Z = 10800.0                        # GUESS: 173 m from the front door (kl_fa_author had 9300, in the old lane)
WAIT_Z = 8700.0                         # GUESS: north of V_JPN_Civilian_B_00#18 (z ..8120) + the van's own length and a gap
# THE ONE PROP TAKEN AWAY (owner: 'maybe remove some props so you can see the van actually leave like a normal
# car'): the police barricade across the east carriageway, x -2869..-389, z 13467..13821, 1.5 m high - one static
# object, 27 m past the stop, in every lane the van could leave by. Hidden (ZGEOM[3] + .gms flag 0x400, as the
# level's own blown window). It stands INSIDE the campaign's north level bound (z 13036..13798), so no player
# ever reaches the gap; the west carriageway's barricade (_01) stays.
# ... and (owner, 2026-10-10, after playing it: 'when it finally leaves ... it goes into a car just make sure it drives
# off down the road the whole time') the QUEUE OF CARS behind that barricade: ONE static object, PC0700_M09_Cars_Qeue_A_01,
# collision x -2648..-1755, z 14832..16158, across the whole east carriageway. The first build ended the drive at z 14900,
# measured against a coarser sample of that collision: the van's nose stood in the first car.
_STREET = r'Locations/M09_B/M09B_Locations.zip\Locations/M09_B/M09B_LOC_Outside.zip\M09_B_Street_01a' + '\\'
PROPS_OFF = (_STREET + 'Collapse_JPN_PoliceBarricade_02', _STREET + 'PC0700_M09_Cars_Qeue_A_01')
END_Z = 21000.0                         # the drive away ends here: 102 m up the road in the baked 8.48 s (F07: 70 m). GUESS.
                                        # The road and its collision run on to z 30000; nothing else stands in the lane
SIDE = (-900.0, 300.0)                  # a crash piece may swerve this far west / east of the lane: the carriageway
NEAR = 8000.0                           # a child of the group farther than this from the drive is not part of it


def tables(S, k):
    """(position in the raw block, the six .buf offsets, key counts of table 5 and table 2) of node k's
    KEYS chunk. A table ends where the next table of ANY entity begins."""
    (p, offs), = kl_graft.keys_tracks(S.ents[k - 1].raw)
    every = sorted({o for e in S.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(S.scene.head)})
    size = lambda o: next(x for x in every if x > o) - o
    return p, offs, size(offs[5]) // 12, size(offs[2]) // 8


def project(main, cum, q):
    """(distance along the polyline `main`, signed sideways offset) of point q (x, y, z)."""
    best = None
    for i in range(len(main) - 1):
        ax, az, bx, bz = main[i][0], main[i][2], main[i + 1][0], main[i + 1][2]
        dx, dz = bx - ax, bz - az
        l2 = dx * dx + dz * dz
        if l2 < 1e-6:
            continue
        t = max(0.0, min(1.0, ((q[0] - ax) * dx + (q[2] - az) * dz) / l2))
        px, pz = ax + t * dx, az + t * dz
        d2 = (q[0] - px) ** 2 + (q[2] - pz) ** 2
        if best is None or d2 < best[0]:
            ln = math.sqrt(l2)
            best = (d2, cum[i] + t * ln, ((q[0] - ax) * dz - (q[2] - az) * dx) / ln, (dx / ln, dz / ln))
    return best[1], best[2], best[3]


def straighten(S, log=print):
    """Rewrite van VAN's baked drive as a straight line up LANE_X (see the docstring). S: the stock
    kl_graft.Level('F07') after kl_fa_author.prepare_host(S). -> what was done, for the report."""
    if getattr(S, 'van', None) or not STRAIGHT:
        return getattr(S, 'van', None)
    sc = S.prp
    top = au.node_of(sc, au.VANS[VAN])
    grp = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'EscapeVehicle_Animation_F07')
    van = next(k for k in range(top, sc.end[top]) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    main, _all, stop = au.van_path(S, top)                  # F07's local space, as baked
    _p, offs, npos, nrot = tables(S, van)
    head = bytearray(S.scene.head)
    pts = [struct.unpack_from('<3f', head, offs[5] + 12 * i) for i in range(npos)]
    if [tuple(round(v, 2) for v in p) for p in pts[:len(main)]] != [tuple(round(v, 2) for v in p) for p in main]:
        raise ValueError('kl_fa_van: the position table does not begin with the drive kl_fa_author reads')
    cum = [0.0]
    for i in range(1, len(main)):
        cum.append(cum[-1] + math.hypot(main[i][0] - main[i - 1][0], main[i][2] - main[i - 1][2]))
    s_stop = project(main, cum, stop)[0]
    y0 = main[0][1]
    scale = (STOP_Z - WAIT_Z) / s_stop                      # the approach, squeezed between WAIT_Z and STOP_Z
    away = (END_Z - STOP_Z) / (cum[-1] - s_stop)            # ... and the drive away, stretched to END_Z
    def to(q, exact=None, clamp=True):
        s, d, tan = project(main, cum, q) if exact is None else (exact, 0.0, None)
        lo, hi = SIDE if clamp else (-NEAR, NEAR)       # a camera stands where it stood beside the drive
        z = STOP_Z - (s_stop - s) * scale if s <= s_stop else STOP_Z + (s - s_stop) * away
        return (LANE_X + min(max(d, lo), hi), VAN_Y + q[1] - y0, z), tan
    new = [to(p, cum[i])[0] if i < len(main) else to(p)[0] for i, p in enumerate(pts)]
    for i, p in enumerate(new):
        struct.pack_into('<3f', head, offs[5] + 12 * i, *p)
    for i in range(nrot):                                   # nose north on every key
        struct.pack_into('<4h', head, offs[2] + 8 * i, 0, 0, 0, 32767)
    # the same bytes in both places the tools read the .buf from (the head is its first part)
    S.scene.head = bytes(head)
    buf = S.files[S.ext['.buf']]
    S.files[S.ext['.buf']] = S.scene.head + buf[len(head):]
    # what else has a place below the group: the same mapping; boxes keep their extents ALONG / ACROSS the drive
    moved = []
    def go(k):
        for c in range(k + 1, sc.end[k]):
            if sc.parent[c] != k or c == van:
                continue
            t = struct.unpack('<3f', S.ents[c - 1].trans[:12])
            if not any(abs(v) > 0.5 for v in t):
                go(c)
                continue
            s, d, tan = project(main, cum, t)
            if abs(d) > NEAR:
                continue                                    # e.g. the explosion template under the ground
            p, _t = to(t, clamp=False)
            lab = au.J.labels('dd', sc.cls(c))
            v = kl_fa.node_values(sc, c)
            if 'ZBoxPrimitive[0]' in lab:                   # a box: world extents, then along / across the drive
                i0 = lab.index('ZBoxPrimitive[0]')
                bx, bz = v[1][0], v[1][2]                   # rot9: local +Z -> (bx, bz), local +X -> (bz, -bx)
                wx, wz = abs(bz) * v[i0] + abs(bx) * v[i0 + 2], abs(bx) * v[i0] + abs(bz) * v[i0 + 2]
                along, across = abs(tan[0]) * wx + abs(tan[1]) * wz, abs(tan[1]) * wx + abs(tan[0]) * wz
                au.place(S, c, p, None, (across, v[i0 + 1], along), turn=(0.0, 1.0))
            else:                                           # a camera, a point: turned with the drive
                th = math.atan2(tan[0], tan[1])             # the drive's heading there; turn by -th about Y
                cs, sn = math.cos(-th), math.sin(-th)
                m = list(v[1])
                for j in (0, 3, 6):                         # three stored columns (x, y, z each)
                    x, z = m[j], m[j + 2]
                    m[j], m[j + 2] = x * cs + z * sn, -x * sn + z * cs
                au.place(S, c, p)
                def fn(us, m=m, lab=lab):
                    au.setv(sc, us, lab.index('ZGEOM[1]'), m)
                kl_graft.edit(sc.nodes[c], 'props', fn)
                S.ents[c - 1].rot = struct.pack('<9f', *m) + bytes(12)
            moved.append((sc.names[c], tuple(round(x) for x in t), tuple(round(x) for x in p)))
    go(grp)
    au.place(S, van, new[0], turn=(0.0, 1.0))              # the node's own place = its first key
    au.place(S, grp, (0.0, 0.0, 0.0), turn=(0.0, 1.0))     # the keys are world positions now
    S.van = {'wait': new[0], 'stop': to(stop, clamp=False)[0], 'end': new[len(main) - 1], 'keys': (npos, nrot), 'main': len(main),
             'scale': scale, 'moved': moved, 'crash_x': (min(p[0] for p in new[len(main):]), max(p[0] for p in new[len(main):]))}
    log('  kl_fa_van: van %d drives straight up x %d at y %d: waits z %d, stops z %d, leaves to z %d (approach x %.2f, away x %.2f); '
        '%d position and %d rotation keys rewritten in place; crash pieces x %d..%d; %d children moved: %s' % (
            VAN + 1, LANE_X, VAN_Y, new[0][2], STOP_Z, new[len(main) - 1][2], scale, away, npos, nrot, *S.van['crash_x'],
            len(moved), ', '.join(n for n, _a, _b in moved)))
    return S.van


def clear_props(M, log=print):
    """Hide PROPS_OFF in the converted Dead Men part M (kl_graft.DeadMen), before the join."""
    if not STRAIGHT:
        return 0
    n = 0
    for path in PROPS_OFF:
        for k in M.prp.resolve(au.R + path):
            au.place(M, k, hidden=True)
            n += 1
    log('  kl_fa_van: %s: %d of %d props in the way of the van hidden' % (M.name, n, len(PROPS_OFF)))
    return n


def plan(log=print):
    S = kl_graft.Level(au.HOST)
    au.prepare_host(S, lambda *_a: None)
    v = straighten(S, log)
    for n, a, b in v['moved']:
        log('  %-28s F07 %s -> %s' % (n, a, b))
    sc = S.prp
    top = au.node_of(sc, au.VANS[VAN])
    main, pts, stop = au.van_path(S, top)
    log('read back through kl_fa_author.van_path: %d drive keys, x %.1f..%.1f, y %.1f..%.1f, z %.0f..%.0f, stop %s; largest step %.0f' % (
        len(main), min(p[0] for p in main), max(p[0] for p in main), min(p[1] for p in main), max(p[1] for p in main),
        main[0][2], main[-1][2], tuple(round(x) for x in stop), max(math.dist(main[i], main[i - 1]) for i in range(1, len(main)))))


def check(archive, log=print):
    """The van of a built level -> [faults]: its drive is one straight line on the carriageway floor
    and no static vehicle of the map stands in it."""
    import kl_hvk, kl_escape
    bad = []
    sc, _snd, _loc = kl_fa.load(archive)
    with zipfile.ZipFile(archive) as z:
        m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
        hvk = kl_hvk.Hvk(z.read(m['.hvk']))
    ents = list(scene.entities())
    pos = kl_maps.world(scene)
    (k, _i, v), = kl_fa.controllers(sc, kl_fa.EXIT)
    grp = sc.resolve([x for x in v[2:6] if x][0])[0]
    top = sc.top[grp]
    van = next(j for j in range(top, sc.end[top]) if sc.names[j] == 'V_Van_00' and 'Reflection' not in sc.path[j])
    (_p, offs), = kl_graft.keys_tracks(ents[van - 1].raw)
    every = sorted({o for e in ents for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(scene.head)})
    size = lambda o: next(x for x in every if x > o) - o
    pts = [struct.unpack_from('<3f', scene.head, offs[5] + 12 * i) for i in range(size(offs[5]) // 12)]
    rot = {struct.unpack_from('<4h', scene.head, offs[2] + 8 * i) for i in range(size(offs[2]) // 8)}
    cut = next((i for i in range(1, len(pts)) if math.dist(pts[i], pts[i - 1]) > 400), len(pts))
    g = pos[ents[grp - 1]]
    main = [(p[0] + g[0], p[1] + g[1], p[2] + g[2]) for p in pts[:cut]]
    xs, ys = [p[0] for p in main], [p[1] for p in main]
    log('van %s: %d drive keys of %d, x %.1f..%.1f, y %.1f..%.1f, z %.0f..%.0f; rotation keys: %s' % (
        sc.names[top][-26:], cut, len(pts), min(xs), max(xs), min(ys), max(ys), main[0][2], main[-1][2],
        'all identity' if rot == {(0, 0, 0, 32767)} else '%d different' % len(rot)))
    if max(xs) - min(xs) > 1.0:
        bad.append('the drive is not straight: x %.0f..%.0f' % (min(xs), max(xs)))
    if rot != {(0, 0, 0, 32767)}:
        bad.append('the rotation keys are not all the identity')
    if any(main[i][2] < main[i - 1][2] - 0.5 for i in range(1, len(main))):
        bad.append('the drive goes backwards somewhere')
    gone = {e.ref for e in ents if e.flags & au.HIDDEN}     # a hidden entity has no collision (ASSUMPTION, kl_fa_author.ledge)
    w = kl_escape.Walk(hvk, box=(min(xs) - 400, max(xs) + 400, main[0][2] - 600, main[-1][2] + 800), skip=gone)
    off = []
    # every 20 units of the drive and 6 m beyond its last key (the van's nose), across the van's width: whatever
    # collision stands higher than the road there is in its way (the first check sampled one cell every few metres)
    z = main[0][2]
    while z <= main[-1][2] + 600:
        for dx in (-110.0, -55.0, 0.0, 55.0, 110.0):
            ys = [y for y, _f, _r in w.grid.get(w.cell(main[0][0] + dx, z), ()) if y < main[0][1] + 250]
            fl = [y for y in ys if y <= main[0][1] + 6.0]
            if not fl or abs(max(fl) - (main[0][1] - 2.0)) > 6.0 or len(fl) != len(ys):
                off.append((round(z), round(max(ys)) if ys else None))
        z += 20.0
    if off:
        bad.append('the lane is not a clear floor 2 below the van at %d sampled places, e.g. z %s: collision up to y %s (van y %.0f)' % (len(off), *off[0], main[0][1]))
    # static vehicles of the map: the bounding box of each group's parts against the van's body (half width 120)
    hit = []
    for j in range(1, len(sc.nodes)):
        if 'Vehicles_static!' in sc.names[j] and sc.end[j] - j > 1:
            ps = [pos[ents[c - 1]] for c in range(j + 1, sc.end[j])]
            ps = [p for p in ps if abs(p[0]) + abs(p[2]) > 1 and abs(p[1]) < 400]
            if ps and min(p[0] for p in ps) - 150 < max(xs) and max(p[0] for p in ps) + 150 > min(xs) \
                    and max(p[2] for p in ps) > main[0][2] - 450 and min(p[2] for p in ps) < main[-1][2]:   # the van's tail: 3.4 m
                hit.append(sc.names[j].split('!')[-1])
    if hit:
        bad.append('static vehicles in the van\'s lane: %s' % ', '.join(hit))
    log('lane under the drive and 6 m beyond its end: %s; static vehicles in the lane: %s' % ('clear floor 2 below the van' if not off else 'NOT CLEAR', ', '.join(hit) or 'none'))
    return bad


def main():
    a = sys.argv[1:]
    if a == ['plan']:
        plan()
    elif len(a) == 2 and a[0] == 'check':
        bad = check(a[1])
        for b in bad:
            print('FAULT ' + b)
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_van
    kl_fa_van.main()
