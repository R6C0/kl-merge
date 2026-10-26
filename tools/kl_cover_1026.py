#!/usr/bin/env python3
"""
REAL PLAYER COVER ON WALLS AND LONG OBJECTS (2026-10-26, owner: "needs more cover in every map ... they are like cover spots
but you can never get onto them, so make actual objects or spots you would be able to go into cover normally").
OFFLINE: reads a finished map zip, writes a staging folder. Starts nothing, installs nothing.

    python kl_cover_1026.py plan  <zip>                 what would be added, nothing written
    python kl_cover_1026.py build <zip> <out folder>    the zip with a 'KL_CoverSix!' group (boxes CoverBoxH/M_K6_nn) + cover_add.json
    options: --tiers ab (maps with NO hidden form-b box model, DM07: also clone form a = flags 0x302 boxes that have a collision record
             in the root's tree 0, like kl_dig_layer does for the Dig; default b)  --density D (target boxes per 100 m2 of mesh, default 3.5)  --max N (default 450)  --spread N (default 220)
             --no-safety (turn OFF the safety rules: no tile near a spawn / spawn trigger / loot / door / stair / ramp, no floating or sunk ground; recommended ON)

THE CAUSE (evidence in re/ notes and the report): a player can take cover only at a *coverbox*-named ZSTDOBJ box (CFFCoverList
builds the list ONCE at the load, 0x6d6a80 -> 0x603830, from the entity's own slot: matrix, box middle +0x30, half size +0x40;
the mesh and the collision are not read). A Dead Men wall, counter or crate is solid collision but has NO such box unless Dead
Men's AI had one there: 0.6..3.2 boxes per 100 m2 on the expansion maps against 4..8 on stock FA maps. Nothing else
(PlayerCoverModifier: all sides AUTO = fine; NoCoverBox only forbids) is missing.

THE MECHANISM = kl_cover_add's (clone one of the build's own hidden form-b box models, written by kl_fa_cover.apply) plus what
kl_cover_add.sparse() leaves out: it refuses every wall longer than ENDS (400) and every 'single plane'. Here the straight faces of
the static collision are read with kl_fa_cover.wall_runs (BASE plane, cut segments joined on one line, side known from the
winding) and TILED: boxes laid flat against the face with their back in the solid, like stock's corner boxes (kl_fa_cover._corner,
re/bots_dyn_build.md 13.1), one every TILE_STEP along it. A tile is kept when
  - it is HIGH (solid at 175 too) or LOW (solid at 45 and 75, not a ledge), by the outline planes of Solid.scan;
  - a model of the build fits it (length along the face <= what is left of the run, depth <= the solid behind the face + 25);
  - no cover box (stock or new) within APART of it, none of ours within SPREAD, not more than the density target per 1000 x 1000 cell;
  - its footprint is in no NoCoverBox, no exit box, not on the escape road;
  - >= STAND_NEED mesh points stand 70..230 in FRONT of the face (the player's side), at the floor the box stands on.
Convex or moving collision (crates the HVK stores convex) is invisible to Solid (kl_cover_add says the same): not tiled here.

GUESSes (not measured): TILE_STEP / DENSITY defaults (stock FA runs 1.4..7.9 per 100 m2, median ~5, measured by measure.py);
that a box in the solid behind a face (the corner form) is entered like one on a prop (the cover test reads the box only);
that the face's winding gives the free side (kl_fa_cover.wall_runs documents the same GUESS).
"""
import collections, json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F
import kl_fa_cover as C
import kl_cover_add as A

GROUP = 'KL_CoverSix!'
TAG = '_K6_'
DENSITY = 3.5            # GUESS: boxes per 100 m2 of mesh to reach (stock FA median is ~5)
MAX_NEW = 450
SPREAD = 220.0           # our boxes at least this far apart (middles)
TILE_STEP = 40.0         # gap left between two tiles of one face
SAMPLE = 500.0           # a place per 500 x 500 of the mesh
REACH = 700.0
CELLBIG = 1000.0
STAND = (70.0, 230.0)
STAND_NEED = 2
MIN_RUN = 120.0
NAME_GROUP = 'KL_CoverSix!'
SAFETY = True            # (recommended on) skip tiles near spawns / loot / doors / stairs / spawn triggers or on a floating / sunk ground (audit 2026-10-26); --no-safety turns it off
SPAWN_PAD, SPAWN_DY = 60.0, 250.0   # footprint + 60 may not touch a ZSpawnPoint (|dy| < 250) or a spawn trigger box
LOOT_NEAR, DOOR_NEAR = 110.0, 150.0 # distance (footprint edge) to a loot stack / to a door, stair, ramp or ladder object
NEAR_DY = 300.0
SPAN_MAX, GROUND_TOL = 35.0, 30.0   # nav height span in front over 2 m; |plan ground - collision floor at the stand point|
TIERS = 'b'              # box model forms a clone may take: 'b' (flags 0x200, no collision record; default, unchanged) or 'ab' (also form a)


def _area(vs):
    return abs(sum(vs[i][0] * vs[(i + 1) % len(vs)][2] - vs[(i + 1) % len(vs)][0] * vs[i][2] for i in range(len(vs)))) / 2


def already(L):
    sc = L.B.sc
    return any(sc.names[k] == NAME_GROUP for k in range(1, len(sc.nodes)))


def _foot_overlap(q, mid, n, eu, ev):
    """Separating-axis test of two oriented footprints (x,z): planned box q against (mid, normal n, extents eu along the face, ev deep)."""
    def rect(c, nn, a, b):
        uu = (-nn[1], nn[0])
        return c, [(uu, a / 2.0), (tuple(nn), b / 2.0)]
    A1 = rect((q['mid'][0], q['mid'][2]), q['face_normal'], q['ext'][0], q['ext'][1])
    A2 = rect(mid, n, eu, ev)
    d = (A2[0][0] - A1[0][0], A2[0][1] - A1[0][1])
    for ax, _h in A1[1] + A2[1]:
        r = sum(h * abs(a[0] * ax[0] + a[1] * ax[1]) for a, h in A1[1] + A2[1])
        if abs(d[0] * ax[0] + d[1] * ax[1]) >= r - 1.0:    # touching edges (<1 unit) count as apart
            return False
    return True


def _fronts(nav, mid, y, n, u):
    """Mesh points in front of the face (n = the free side) -> count of 70..230 samples on the mesh at about the floor y."""
    c = 0
    for d in (80.0, 110.0, 150.0, 200.0):
        for t in (-40.0, 0.0, 40.0):
            if nav.at(mid[0] + d * n[0] + t * u[0], y, mid[1] + d * n[1] + t * u[1], dy=70.0) is not None:
                c += 1
    return c


def safety_features(L):
    """Places a cover box must keep away from (the 2026-10-26 audit's detection, moved here): spawn points, spawn trigger boxes, loot stacks / MoneyStack
    props, stair / ladder / ramp / step objects, door objects. Each list holds (place, name); triggers hold (node, box size)."""
    B, sc = L.B, L.B.sc
    ks = range(1, len(sc.nodes))
    low = {k: sc.names[k].lower() for k in ks}
    spawns = [(B.at(k), sc.names[k]) for k in ks if sc.cls(k) == 'ZSpawnPoint']
    loot = [(p, 'loot %s' % a) for _k, p, a in F.stations(B, L.nav)['loot']]
    loot += [(B.at(k), sc.names[k].split('!')[-1]) for k in ks if sc.cls(k) == 'ZSTDOBJ' and 'moneystack' in low[k]]
    stairs = [(B.at(k), sc.names[k]) for k in ks if sc.cls(k) == 'ZSTDOBJ' and any(w in low[k] for w in ('stair', 'ladder', 'ramp', 'step'))]
    doors = [(B.at(k), sc.names[k]) for k in ks if (sc.cls(k) in ('ZSTDOBJ', 'ZGROUP') and 'door' in low[k] and 'lod' not in low[k][-6:-2])
             or (sc.cls(k) == 'ZSTDOBJ' and 'door' in low[k] and low[k].endswith('lod00'))]
    trig = []
    for k in ks:
        if sc.cls(k) == 'ZBoxPrimitive' and 'spawnpointtrigger' in sc.path[k].lower() and k not in L.nocover:
            try:
                trig.append((k, B.box(k)))
            except Exception:
                pass
    return dict(spawns=spawns, loot=loot, near=[(stairs, 'stair/ladder/ramp object'), (doors, 'door object')], trig=trig)


def _tile_unsafe(L, SF, mid, y, n, u, eu, ev, stand):
    """Reason string when the planned tile (middle mid, free-side normal n, extents eu along u / ev deep, ground y, stand point) breaks a safety rule, else None."""
    B, S, nav = L.B, L.solid, L.nav
    def rect(pad):       # footprint corners + middle, grown by pad
        return [(mid[0] + su * (eu / 2 + pad) * u[0] + sv * (ev / 2 + pad) * n[0], mid[1] + su * (eu / 2 + pad) * u[1] + sv * (ev / 2 + pad) * n[1])
                for su in (-1, 0, 1) for sv in (-1, 0, 1)]
    def dist(p):         # from a place to the footprint edge (oriented rectangle)
        dx, dz = p[0] - mid[0], p[2] - mid[1]
        a, b = abs(dx * u[0] + dz * u[1]) - eu / 2, abs(dx * n[0] + dz * n[1]) - ev / 2
        return math.hypot(max(a, 0.0), max(b, 0.0))
    for p, _nm in SF['spawns']:
        if abs(p[1] - y) < SPAWN_DY and dist(p) < SPAWN_PAD:
            return 'touches a spawn point (footprint + %d)' % SPAWN_PAD
    pad = [(q[0], y + 50.0, q[1]) for q in rect(SPAWN_PAD)]
    for k, sz in SF['trig']:
        if any(B.in_box(k, q, size=sz) for q in pad):
            return 'touches a spawn trigger box (footprint + %d)' % SPAWN_PAD
    for p, _nm in SF['loot']:
        if abs(p[1] - y) < NEAR_DY and dist(p) < LOOT_NEAR:
            return 'within %d of a loot stack' % LOOT_NEAR
    for lst, what in SF['near']:
        for p, _nm in lst:
            if abs(p[1] - y) < NEAR_DY and dist(p) < DOOR_NEAR:
                return 'within %d of a %s' % (DOOR_NEAR, what)
    hs = []
    for dd in (0, 40, 80, 120, 160, 200):
        i_ = nav.at(stand[0] + n[0] * dd, y, stand[2] + n[1] * dd)
        if i_ is not None:
            hs.append(i_[1])
    if len(hs) >= 3 and max(hs) - min(hs) > SPAN_MAX:
        return 'stairs / ramp in front (nav height span over %d in 2 m)' % SPAN_MAX
    sf = S.floor(stand[0], y, stand[2], reach=60.0)
    if sf is not None and abs(sf - y) > GROUND_TOL:
        return 'plan ground and collision floor at the stand point differ by more than %d' % GROUND_TOL
    return None


def walls(L, fs, new, max_new, density, spread, log=print, safety=SAFETY):
    B, nav, S = L.B, L.nav, L.solid
    area = sum(_area(nav.pv[i]) for i in range(len(nav.pv)) if nav.ok[i]) / 1e4
    want = int(area * density / 100.0)
    # existing boxes per big cell
    have = collections.Counter()
    for b in L.boxes:
        if b.get('kind') is not None:
            have[int(b['mid'][0] // CELLBIG), int(b['mid'][2] // CELLBIG)] += 1
    capcell = max(2, int(round(density * (CELLBIG * CELLBIG / 1e6))))      # per 1000 x 1000 (10 m x 10 m = 1 per 100 m2 -> x density)
    cell, picks = collections.defaultdict(list), []
    for i, v in enumerate(nav.pv):
        if nav.ok[i]:
            m = nav.mid[i]
            cell[int(m[0] // SAMPLE), int(m[2] // SAMPLE)].append(i)
    for key, ps in sorted(cell.items()):
        ps.sort(key=lambda i: (nav.mid[i][0] - (key[0] + .5) * SAMPLE) ** 2 + (nav.mid[i][2] - (key[1] + .5) * SAMPLE) ** 2)
        picks.append(nav.mid[ps[0]])
    log('walls: %.0f m2 of mesh, target %d boxes at %.1f per 100 m2, %d have a cover box; %d places' % (area, want, density, sum(have.values()), len(picks)))
    why, cand, seen = collections.Counter(), [], set()
    SF = safety_features(L) if safety else None
    if SF:
        log('walls: safety rules on: %d spawns, %d spawn triggers, %d loot, %d stairs/ramps, %d doors' % (len(SF['spawns']), len(SF['trig']), len(SF['loot']), len(SF['near'][0][0]), len(SF['near'][1][0])))
    for p in picks:
        g = S.floor(p[0], p[1], p[2])
        y = p[1] if g is None else g
        for r in C.wall_runs(S, B, p[0], y, p[2], REACH):
            if r['len'] < MIN_RUN:
                why['run shorter than %d' % MIN_RUN] += 1
                continue
            key = (r['ref'], round(r['a'][0] / 40), round(r['a'][1] / 40), round(r['b'][0] / 40), round(r['b'][1] / 40))
            if key in seen:
                continue
            seen.add(key)
            cand.append((r, y))
    log('walls: %d wall runs (>= %d long) round %d places' % (len(cand), MIN_RUN, len(picks)))
    # longest runs first; tiles are then picked cell by cell up to the cap
    cand.sort(key=lambda t: -t[0]['len'])
    placed = collections.Counter()
    for r, y in cand:
        if len(new) >= max_new:
            why['cap'] += 1
            break
        a, b, u, n = r['a'], r['b'], r['u'], r['n']
        occ, _s = S.scan(a[0], y, a[1])
        t = 0.0
        L_run = r['len']
        while t < L_run - 50.0 and len(new) < max_new:
            p0 = (a[0] + t * u[0], a[1] + t * u[1])
            left = L_run - t
            # which height: solid at 175 along this stretch (HIGH) or at 45 and 75 only (LOW)
            def share(h, span):
                got = 0
                for s in range(0, 5):
                    q = (p0[0] + span * s / 4.0 * u[0] - 6 * n[0], p0[1] + span * s / 4.0 * u[1] - 6 * n[1])
                    cell_ = (int(q[0] // C.CELL), int(q[1] // C.CELL))
                    if any(cell_ in C._grow(cs, 1) for cs in ([occ[h].get(r['ref'], set())])):
                        got += 1
                return got / 5.0
            span = min(left, 150.0)
            hi, lo = share(C.HIGH, span) >= 0.6, share(C.LOW, span) >= 0.6
            if not lo:
                why['not on the ground (ledge, table top)'] += 1
                t += 60.0
                continue
            ky = C.HIGH_Y if hi else C.LOW_Y
            # the solid behind the face: up to the first mesh behind it (a thin shell), at most MODEL_MAX
            depth = C.MODEL_MAX
            for sdep in range(20, int(C.MODEL_MAX) + 1, 20):
                q = (p0[0] + 30.0 * u[0] - sdep * n[0], p0[1] + 30.0 * u[1] - sdep * n[1])
                if nav.at(q[0], y, q[1], dy=70.0) is not None:
                    depth = sdep - 10.0
                    break
            best = None
            for f in fs:
                if not ky[0] <= f['size'][1] < ky[1]:
                    continue
                for along_u in (True, False):
                    eu, ev = (f['size'][2], f['size'][0]) if along_u else (f['size'][0], f['size'][2])
                    if eu > left + 25.0 or ev > depth + C.CORNER_OVER or eu < C.CORNER_MIN or ev < min(C.CORNER_MIN, 0.7 * depth):
                        continue
                    key = (-min(eu, left), abs(ev - min(depth, 100.0)), f['model'])
                    if best is None or key < best[0]:
                        best = (key, f, along_u, eu, ev)
            if best is None:
                why['no model fits'] += 1
                t += 60.0
                continue
            _k, f, along_u, eu, ev = best
            mid = (p0[0] + eu / 2 * u[0] - ev / 2 * n[0], p0[1] + eu / 2 * u[1] - ev / 2 * n[1])
            step = eu + TILE_STEP
            ccell = (int(mid[0] // CELLBIG), int(mid[1] // CELLBIG))
            if have[ccell] + placed[ccell] >= capcell:
                why['cell is at the density target'] += 1
                t += step
                continue
            t += step
            if not A._free(L, mid, y + f['size'][1] / 2, new):
                why['has cover / crowded'] += 1
                continue
            if any(math.hypot(q['mid'][0] - mid[0], q['mid'][2] - mid[1]) < spread and abs(q['mid'][1] - y) < 300 for q in new):
                why['spread'] += 1
                continue
            # review 2026-10-26: the mid-point spread test let footprints overlap (DM09 17 pairs, some back to back in one thin wall),
            # which makes the side the player enters ambiguous: no new box may overlap another new box's footprint
            if any(abs(q['mid'][1] - (y + f['size'][1] / 2)) < 300 and _foot_overlap(q, mid, n, eu, ev) for q in new):
                why['overlaps a new box'] += 1
                continue
            head = u if along_u else n
            eu_, ev_ = (f['size'][2], f['size'][0])      # extents along local Z / local X of the model (what check() reads from the box)
            xax = (head[1], -head[0])
            org = (mid[0] - f['mid'][0] * xax[0] - f['mid'][1] * head[0], mid[1] - f['mid'][0] * xax[1] - f['mid'][1] * head[1])
            foot = [(mid[0] + su * eu / 2 * u[0] + sv * ev / 2 * n[0], y + 50.0, mid[1] + su * eu / 2 * u[1] + sv * ev / 2 * n[1])
                    for su in (-1, 1) for sv in (-1, 1)] + [(mid[0], y + 50.0, mid[1])]
            if any(B.in_box(k, q) for k in L.nocover for q in foot):
                why['NoCoverBox'] += 1
                continue
            wide = [(mid[0] + su * (eu / 2 + 25) * u[0] + sv * (ev / 2 + 25) * n[0], y + h, mid[1] + su * (eu / 2 + 25) * u[1] + sv * (ev / 2 + 25) * n[1])
                    for su in (-1, 0, 1) for sv in (-1, 0, 1) for h in (10.0, 50.0, 150.0)]
            if L.exits and any(F.in_exit(B, L.exits, q) for q in wide):
                why['exit box'] += 1
                continue
            if L.lane and min(F.lane_dist(L.lane, q) for q in foot) < F.LANE_CLEAR:
                why['escape road'] += 1
                continue
            # nobody may stand IN the box: the mesh is carved round props, so a footprint corner on the mesh means a thin wall
            if sum(1 for q in foot[:4] if nav.at(q[0], y, q[2], dy=70.0) is not None) >= 2:
                why['box reaches the other side (thin wall)'] += 1
                continue
            # kl_fa_cover.check's own 'thin air' rule: >= 4 raster cells of static collision in the footprint (+ CELL) at BASE
            occ2, _s2 = S.scan(mid[0], y, mid[1], 500.0)
            hx, hz = head
            inside = 0
            for _r2, cells2 in occ2[C.BASE].items():
                for c2 in cells2:
                    dx, dz = (c2[0] + 0.5) * C.CELL - mid[0], (c2[1] + 0.5) * C.CELL - mid[1]
                    lz, lx = dx * hx + dz * hz, dx * hz - dz * hx
                    if abs(lx) <= ev_ / 2 + C.CELL and abs(lz) <= eu_ / 2 + C.CELL:
                        inside += 1
            if inside < 4:
                why['no collision in the footprint (thin air)'] += 1
                continue
            fr = (mid[0] + (ev / 2 + 1) * n[0], mid[1] + (ev / 2 + 1) * n[1])
            if _fronts(nav, fr, y, n, u) < STAND_NEED:
                why['nobody can stand in front'] += 1
                continue
            if SF:
                bad = _tile_unsafe(L, SF, mid, y, n, u, eu, ev, (fr[0], y, fr[1]))
                if bad:
                    why['safety: ' + bad] += 1
                    continue
            k = S.node.get(r['ref'])
            nm = B.sc.path[k].rsplit(A.SEP, 1)[-1] if k else 'REF %d' % r['ref']
            new.append({'kind': 'high' if hi else 'low', 'origin': [round(org[0], 2), round(y - f['lo_y'], 2), round(org[1], 2)],
                        'head': [round(v, 5) for v in head], 'mid': [round(mid[0], 1), round(y + f['size'][1] / 2, 1), round(mid[1], 1)],
                        'ext': [round(eu, 1), round(ev, 1)], 'height': round(f['size'][1], 1), 'model': f['model'], 'form': f['path'],
                        'form_node': f['node'], 'tier': f['tier'], 'borrowed': f.get('borrowed'), 'object': nm, 'object_ref': r['ref'],
                        'ground': round(y, 1), 'via': 'wall', 'name': None,
                        'face_normal': [round(n[0], 3), round(n[1], 3)], 'run': [[round(a[0]), round(a[1])], [round(b[0]), round(b[1])], round(L_run), round(t - step)], 'stand': [round(fr[0], 1), round(y, 1), round(fr[1], 1)]})
            placed[ccell] += 1
    log('walls: added %d; not added: %s' % (sum(1 for q in new if q['via'] == 'wall'), dict(why)))


def plan(zp, opt, log=print):
    # (normalised: kl_fa_cover.apply skips copying the source zip by comparing path strings; a '/' path would copy the original over the output)
    zp = os.path.normpath(os.path.abspath(zp))
    A.use_slot(zp)
    C.GROUP, C.TAG = GROUP, TAG
    L = A.Lite(zp)
    log('%s: %d entities, %d cover boxes, %d NoCoverBox' % (zp, len(L.B.ents), len([b for b in L.boxes if b['kind']]), len(L.nocover)))
    if already(L):
        log('the %s group is already in this zip: nothing to add (idempotent)' % GROUP)
        return L, collections.OrderedDict(folder=L.folder, options=dict(opt), boxes=[])
    fs = C.forms(L.B, L.boxes, opt.get('tiers', TIERS), True)
    log('box models: %s' % sorted('%dx%dx%d' % tuple(f['size']) for f in fs))
    new = []
    if fs:
        walls(L, fs, new, opt['max'], opt['density'], opt['spread'], log, opt.get('safety', SAFETY))
    cnt = collections.Counter()
    for c in new:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', TAG, cnt[c['kind']])
    P = collections.OrderedDict(folder=L.folder, options=dict(opt), boxes=new)
    log('PLAN: %d boxes (%d low, %d high)' % (len(new), cnt['low'], cnt['high']))
    return L, P


def build(zp, dst, opt, log=print):
    L, P = plan(zp, opt, log)
    if not P['boxes']:
        log('nothing to add')
        return L, None, [], []
    rep = C.apply(L, P, dst, log)
    rep['plan'] = P
    with open(os.path.join(dst, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out = C.check(dst, log)
    nfail = sum(1 for s_, _t in out if s_ == 'FAIL')
    log('CHECK: %d FAIL of %d lines' % (nfail, len(out)))
    bad = C.diff(L.folder, dst, log)
    rep['check'] = [list(x) for x in out]
    with open(os.path.join(dst, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    return L, rep, out, bad


def options(a):
    opt = {'max': MAX_NEW, 'density': DENSITY, 'spread': SPREAD, 'tiers': TIERS, 'safety': SAFETY}
    a = list(a)
    while a and a[0].startswith('--'):
        if a[0] == '--no-safety':
            opt['safety'] = False
            a.pop(0)
            continue
        k = a.pop(0)[2:]
        opt[k] = type(opt[k])(a.pop(0))
    return opt, a


def main():
    opt, a = options(sys.argv[2:])
    if len(a) == 1 and sys.argv[1] == 'plan':
        plan(a[0], opt)
    elif len(a) == 2 and sys.argv[1] == 'build':
        L, rep, out, bad = build(a[0], a[1], opt)
        sys.exit(1 if any(s_ == 'FAIL' for s_, _t in out) or bad else 0)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
