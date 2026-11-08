r"""kl_doors_clear_1108.py - does an OWN-LEAF kick door (kl_doors_1108) stand in the way of a spawn's exit or of the escape? OFFLINE, read only.
Written 2026-11-08 after the review of the doors stage: DM03 hosts 176 / 64 stood 198 / 276 cm from "a spawn" (that was Triggers!Respawn_Trigger and a NoCover marker,
the real ZSpawnPoints of that part are the SpawnPoint_Dead_NN 500..1100 away), and DM03A has no mapiconexit at all (its escape is the box Gameplay!EscapeSetup!otrExitLevel).

METHOD (kl_route's walker: 20-unit cells, body 60 x 60, 55..165 over the floor, STATIC + KEYFRAMED collision; see its docstring for what is assumed)
  For a door host and a start point S (a ZSpawnPoint, or the centre of an escape box):
    base   flood from S in the STAGED zip with the new door slab taken out (opened = its REF): every cell S can reach within RADIUS (the open map, door as if gone).
    closed flood in the INPUT zip (the static leaf as it stands today) and in the staged zip with the slab in: must reach exactly the cells the input does
           (the slab replaces the leaf's collision where the leaf stood: nothing may change while it is shut).
    swung  the leaf at rest, swung about its hinge by +-SWING degrees (default 90 and 120): its footprint (a segment hinge -> free end, grown by the walker's half width
           30 + half thickness) is blocked on top of 'base'. LOST = base cells that the walker no longer reaches and that are not inside the footprint itself.
           A swung leaf that cuts off cells (a dead end behind it) is "blocking". S inside a footprint is "on the spawn".
  Targets: the escape boxes (otrExitLevel / OnlineExitLevelTrigger boxes, boarding trigger, AllyEscapeBox, PathBlockerVan): the footprints (closed and swung) must not
  touch them (box grown 30), and every box centre reachable from S in 'base' stays reachable with the footprint blocked.
GUESSES (marked): (1) a kicked leaf rests at +-90..120 degrees (the stock kick door's end pose was not measured); (2) the kick volumes (KickDoor_Action_*, +-80 beside the
door) are triggers: they do not block anyone, they are only reported when a spawn stands in one; (3) the walker's body = kl_route's.
"""
import math, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BS = chr(92)
RADIUS = 4000.0
SWINGS = (90.0, 120.0)
BODY = 30.0            # the walker's half width
MIN_CUT = 8           # cells (20 cm grid, 8 = 3 m2): a smaller pocket is a nook beside the leaf, not a corridor or room (GUESS threshold; 6516 loses 3, 6770 loses 42)
ESCAPE_NAMES = ('otrexitlevel', 'onlineexitleveltrigger', 'boardingtrigger', 'allyescapebox', 'pathblockervan', 'cameratrigger_invan', 'mapiconexit')


def spawn_points(B):
    """Real ZSpawnPoint entities -> [(k, name, pos)]. (Triggers!Respawn_Trigger, NoCover markers etc. are NOT spawn points.)"""
    return [(k, B.sc.path[k].rsplit(BS, 1)[-1], B.fr[B.ents[k - 1]][1]) for k in range(1, len(B.ents) + 1) if B.sc.cls(k) == 'ZSpawnPoint']


def escape_things(B):
    """The escape-related nodes -> [(k, name, pos, half extents or None, rotation)]: boxes of ESCAPE_NAMES (compared on the last path element, case ignored)."""
    out = []
    for k in range(1, len(B.ents) + 1):
        last = B.sc.path[k].rsplit(BS, 1)[-1].lower() if B.sc.path[k] else ''
        if last.split('!')[-1] in ESCAPE_NAMES or last in ESCAPE_NAMES:
            R, P = B.fr[B.ents[k - 1]]
            sz = None
            if B.sc.cls(k) == 'ZBoxPrimitive':
                sz = B.box(k)
                if max(sz) <= 11.0:
                    continue                    # the 10 x 10 x 10 timer dummies parked at (10000, 0, 10000)
            out.append((k, B.sc.path[k].rsplit(BS, 1)[-1], P, sz, R))
    return out


def leaf_dir(h):
    """Unit vector (x, z) from the hinge to the leaf's free end (the leaf as it stands in the input)."""
    dx, dz = h['mid'][0] - h['hinge'][0], h['mid'][2] - h['hinge'][2]
    n = math.hypot(dx, dz) or 1.0
    return dx / n, dz / n


def footprints(h, swings=SWINGS):
    """[(label, (x0, z0), (x1, z1))]: the leaf shut and at rest swung +-s degrees about its hinge (plan view; the leaf is h['width'] long)."""
    hx, hz = h['hinge'][0], h['hinge'][2]
    ux, uz = leaf_dir(h)
    w = h['width']
    out = [('shut', (hx, hz), (hx + ux * w, hz + uz * w))]
    for s in swings:
        for sg in (1, -1):
            a = math.radians(s) * sg
            vx, vz = ux * math.cos(a) - uz * math.sin(a), ux * math.sin(a) + uz * math.cos(a)
            out.append(('%+d' % (sg * s), (hx, hz), (hx + vx * w, hz + vz * w)))
    return out


def seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / ((dx * dx + dz * dz) or 1.0)))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def seg_hits_box(a, b, centre, half, R, grow=BODY, step=10.0):
    """True when the segment a -> b (plan) comes within `grow` of the box (centre, half extents x/z, rotation R, rows = world axes of local x, y, z... as kl_fa_bots frames)."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    for i in range(n + 1):
        x, z = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
        d = (x - centre[0], 0.0, z - centre[2])
        q = [sum(R[r][j] * d[r] for r in range(3)) for j in range(3)]       # local = R^T d (kl_fa_bots.local)
        if abs(q[0]) <= half[0] + grow and abs(q[2]) <= half[2] + grow:
            return True
    return False


def _flood(run, start, opened, block=None, radius=RADIUS):
    """Cells {(i, j)} reachable from `start` (x, y, z) in run's grid; `block(x, z)` True = cell shut for the walker; bounded by `radius` round the start."""
    import kl_route as R
    g = run.g
    orig = g.step

    def step(i, j, y, op):
        x, z = (i + 0.5) * R.CELL, (j + 0.5) * R.CELL
        if math.hypot(x - start[0], z - start[2]) > radius:
            return None
        if block is not None and block(x, z):
            return None
        return orig(i, j, y, op)
    g.step = step
    try:
        feet = g.feet(start, opened)
        if block is not None:
            feet = [s for s in feet if not block((s[0] + 0.5) * R.CELL, (s[1] + 0.5) * R.CELL)]
        cost, _p, _e, _ed = R._search(g, feet, None, None, opened, None)
    finally:
        g.step = orig
    return {(s[0], s[1]) for s in cost}, bool(feet)


def door_ref(zp, top, n):
    """REF of the keyed slab's entity of kick door KL_Door_<n> under <top> (its 'Door' leaf)."""
    import kl_fa_bots as F
    B = F.Built(zp)
    want = BS.join(['ROOT', top, 'KL_Door_%d' % n, 'Door'])
    for k, p in enumerate(B.sc.path):
        if p == want:
            return B.ents[k - 1].ref, B.fr[B.ents[k - 1]][1]
    raise ValueError('no %s' % want)


def check_host(zp_in, zp_out, host, top, n, starts, things, log=print, swings=SWINGS, radius=RADIUS, cache=None, others=()):
    """-> dict(host, rows=[...], problems=[...]). zp_in = the input zip, zp_out = the staged one, host = a door_hosts dict (input zip), top / n = the staged door group."""
    import kl_route as R
    ref, pos = door_ref(zp_out, top, n)
    if math.hypot(pos[0] - host['hinge'][0], pos[2] - host['hinge'][2]) > 10.0:  # own-leaf frame sits a few cm off the measured hinge (3 cm seen); a wrong host is metres away
        raise ValueError('KL_Door_%d stands at %s, not at host %d hinge %s (door numbering is not host order)' % (n, [round(v) for v in pos], host['k'], [round(v) for v in host['hinge']]))
    cache = {} if cache is None else cache
    if 'runs' not in cache:
        cache['runs'] = (R._Run(zp_in, mesh=False), R._Run(zp_out, mesh=False))
    run_in, run_out = cache['runs']
    gone = frozenset([ref])
    rep = dict(host=host['k'], ref=ref, rows=[], problems=[])
    fps = footprints(host, swings)
    for lab, a, b in fps:
        for tk, tn, tp, sz, tR in things:
            if sz and seg_hits_box(a, b, tp, sz, tR):
                rep['problems'].append('footprint %s touches escape box %s' % (lab, tn))
    for sk, sn, sp in starts:
        if math.hypot(sp[0] - host['hinge'][0], sp[2] - host['hinge'][2]) > radius or abs(sp[1] - host['hinge'][1]) > 600:
            continue
        if sk not in cache:
            cache[sk] = _flood(run_in, sp, frozenset(), radius=radius) + _flood(run_out, sp, frozenset(), radius=radius)
        c_in, f_in, c_closed, f_c = cache[sk]
        base, f_b = _flood(run_out, sp, gone, radius=radius)
        row = dict(start=sn, pos=[round(v) for v in sp], dist=round(math.hypot(sp[0] - host['hinge'][0], sp[2] - host['hinge'][2])),
                   cells_input=len(c_in), cells_closed=len(c_closed), cells_open_map=len(base), swung={})
        if not (f_in and f_c and f_b):
            row['note'] = 'no floor at the start (input %s staged %s base %s)' % (f_in, f_c, f_b)
            rep['rows'].append(row)
            continue
        # shut: the slab (6 cm) is thinner than the static leaf's box (24..28 cm), so the walker may reach a few cells the leaf's thickness used to cover: allowed ONLY
        # within BODY + 25 of a shut leaf of ANY door of the map (`others`: every host dict of the stage); losing a cell, or gaining one elsewhere, is a problem
        shut = [footprints(hh, ())[0][1:] for hh in (others or [host])]
        near = lambda c: any(seg_dist((c[0] + 0.5) * R.CELL, (c[1] + 0.5) * R.CELL, a, b) <= BODY + 25.0 for a, b in shut)
        extra, short = c_closed - c_in, c_in - c_closed
        if short or [c for c in extra if not near(c)]:
            rep['problems'].append('%s: shut door changes the reachable set (input %d cells, staged %d; %d lost, %d gained away from any leaf)' % (
                sn, len(c_in), len(c_closed), len(short), len([c for c in extra if not near(c)])))
        row['gained_at_leaf_edge'] = len([c for c in extra if near(c)])
        row['gated_by_this_door'] = len(base - c_closed - {c for c in base if seg_dist((c[0] + .5) * R.CELL, (c[1] + .5) * R.CELL, *fps[0][1:]) <= BODY + 3.0})
        for lab, a, b in fps[1:]:
            blk = lambda x, z, a=a, b=b: seg_dist(x, z, a, b) <= BODY + 3.0
            sw, ok = _flood(run_out, sp, gone, block=blk, radius=radius)
            foot = {c for c in base if blk((c[0] + 0.5) * R.CELL, (c[1] + 0.5) * R.CELL)}
            lost = base - sw - foot
            on = blk(sp[0], sp[2])
            row['swung'][lab] = dict(lost=len(lost), footprint=len(foot), on_start=on, start_ok=ok)
            if len(lost) >= MIN_CUT:
                rep['problems'].append('%s: leaf swung %s cuts off %d cells beyond it' % (sn, lab, len(lost)))
            if on:
                rep['problems'].append('%s: stands in the leaf swung %s' % (sn, lab))
            for tk, tn, tp, sz, tR in things:
                ti, tj = int(tp[0] // R.CELL), int(tp[2] // R.CELL)
                near = any((ti + di, tj + dj) in base for di in range(-8, 9) for dj in range(-8, 9))
                if near and not any((ti + di, tj + dj) in sw for di in range(-8, 9) for dj in range(-8, 9)):
                    rep['problems'].append('%s: escape node %s no longer reachable with the leaf swung %s' % (sn, tn, lab))
        rep['rows'].append(row)
    return rep


def check_map(zp_in, zp_out, hosts, top, base, starts_of=spawn_points, log=print, swings=SWINGS, radius=RADIUS):
    """All hosts of one map. door n = base + index + 1 in host order. -> {host k: report}."""
    import kl_fa_bots as F, kl_interact_graft as IG
    B_in = F.Built(zp_in)
    nav = F.Nav(B_in.scene.nav)
    allh = {h['k']: h for h in IG.door_hosts(B_in, nav)}
    B_out = F.Built(zp_out)
    starts, things = starts_of(B_in), escape_things(B_in)
    cache, out = {}, {}
    for i, k in enumerate(hosts):
        out[k] = check_host(zp_in, zp_out, allh[k], top, base + i + 1, starts, things, log, swings, radius, cache, [allh[x] for x in hosts])
        r = out[k]
        log('  host %d (%s): %d starts within %d, %d problems' % (k, allh[k]['name'][-34:], len(r['rows']), radius, len(r['problems'])))
        for row in r['rows']:
            log('    %-28s %5d cm  cells input/closed/open %d/%d/%d  gated %s  swung(lost,on) %s' % (row['start'][-28:], row['dist'], row['cells_input'], row['cells_closed'], row['cells_open_map'],
                                                                        row.get('gated_by_this_door'), {k2: (v['lost'], v['on_start']) for k2, v in row['swung'].items()}))
        for p in r['problems']:
            log('    PROBLEM: ' + p)
    return out


def hvk_equal(zp_in, zp_out, new_refs=(), gone_refs=()):
    """Shape-by-shape proof that only the door slabs changed in the .HVK: every REF but `gone_refs` / the filler keeps its placements, shape records and MOPP code,
    static placements keep their positions in the list, non-static shapes are identical. -> list of problems ([] = equal)."""
    import collections, kl_hvk

    def load(zp):
        with zipfile.ZipFile(zp) as z:
            return kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))

    def sig(s):
        return (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub))

    def pl(h):
        d = collections.defaultdict(list)
        for s in h.shapes:
            for j, i in enumerate(s.inst):
                d[kl_hvk.ref(i)].append((s.type, sig(s), bytes(i), s.mopp[j][1] if s.mopp else None))
        return d
    a, b = load(zp_in), load(zp_out)
    bad = []
    pa, pb = pl(a), pl(b)
    gone = set(pa) - set(pb)
    if gone_refs and gone != set(gone_refs):
        bad.append('refs gone %s, expected %s' % (sorted(gone), sorted(gone_refs)))
    new = set(pb) - set(pa)
    if new_refs and new != set(new_refs):
        bad.append('refs new %s, expected %s' % (sorted(new), sorted(new_refs)))
    if any(x[0] != 4 for r in new for x in pb[r]):
        bad.append('a new ref is not a key-framed (type 4) slab')
    diff = [r for r in pa if r in pb and pa[r] != pb[r]]
    # the changed ones may only be the FILLER ref (a static placement kept for the cut ones, gaining copies)
    for r in diff:
        if {x[0] for x in pa[r]} != {1} or {x[2] for x in pa[r]} != {x[2] for x in pb[r]} or len({(x[1], x[3]) for x in pb[r]}) != 1 or len(pb[r]) != len(pa[r]) + len(gone):
            bad.append('REF %d changed beyond taking the cut placements as filler copies' % r)
    if len(diff) > 1:
        bad.append('more than one ref changed: %s' % diff)
    if a.static_count() != b.static_count():
        bad.append('static count %d -> %d' % (a.static_count(), b.static_count()))
    sa = [kl_hvk.ref(i) for s in a.shapes if s.type == 1 for i in s.inst]
    sb = [kl_hvk.ref(i) for s in b.shapes if s.type == 1 for i in s.inst]
    for k, (x, y) in enumerate(zip(sa, sb)):
        if x != y and not (x in gone and y in diff):
            bad.append('static list position %d: REF %d -> %d' % (k, x, y))
            break
    ns = lambda h: [(s.type, sig(s), tuple(bytes(i) for i in s.inst)) for s in h.shapes if s.type != 1]
    na, nb = ns(a), ns(b)
    if [x for x in na if x not in nb]:
        bad.append('a non-static shape of the input is missing or changed')
    if len([x for x in nb if x not in na]) != len(new):
        bad.append('%d non-static shapes are new, %d new refs' % (len([x for x in nb if x not in na]), len(new)))
    if a.box != b.box:
        bad.append('the .HVK box changed')
    return bad


if __name__ == '__main__':
    import json
    if len(sys.argv) < 6:
        print('usage: kl_doors_clear_1108.py <input zip> <staged zip> <top group> <door base> <host k,k,...> [radius]'); sys.exit(2)
    zi, zo, top, base, hs = sys.argv[1:6]
    rep = check_map(zi, zo, [int(x) for x in hs.split(',')], top, int(base), radius=float(sys.argv[6]) if len(sys.argv) > 6 else RADIUS)
    print(json.dumps({k: v['problems'] for k, v in rep.items()}, indent=1))
    sys.exit(1 if any(v['problems'] for v in rep.values()) else 0)
