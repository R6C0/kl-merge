#!/usr/bin/env python3
"""
MORE COVER, MAP-WIDE (2026-10-24, owner: "majority of objects you can press C / the AI can go into cover; some maps
and Withdrawal do not let you; blown-up cars cannot be used for cover"). OFFLINE: starts nothing, installs nothing.

    python kl_cover_add.py plan  <zip>                 what would be added, nothing written
    python kl_cover_add.py build <zip> <out folder>    the zip with a 'KL_CoverMore!' group of new cover boxes + cover_add.json,
                                                       check + diff run (kl_fa_cover.check / diff); exit 1 on a FAIL
    options: --max N (new boxes of the sparse mode, default 150)   --no-sparse   --no-cars   --spread N (default 250)

It reuses kl_fa_cover (the stock DD cover box form: a clone of one of the build's own form-b boxes, flags 0x200, hidden
one-mesh model, in no room tree; kl_fa_cover.apply() writes it, renumbers the slot ids, and keeps the four large blocks'
sizes). Unlike kl_fa_cover.build it needs NO bots build: it works on a FINISHED map zip (the dynamic step's squads may
be in it already) and asks no route plan where cover is missing. Two sources of boxes:

  1. STATIC COPIES FOR PARKED CARS (cars()). In Dead Men a car is a group with VehicleEffects whose CoverBoxM/H_nn are
     children of the group. A parked car ('Static': no ZHavokCar below it) gets a copy of each of those boxes at the
     same world pose, in the new group, outside the car. WHY: PROVEN only that (a) the cover list is built ONCE at
     the load (0x6d6a80, the only caller of the box builder 0x603830) and snapshots the corners; nothing in the exe
     calls the builder again, and 0x5da8b0 (CoverStateChanger) has two callers, neither in the vehicle effects;
     (b) the boxes are plain ZSTDOBJ children of the group. NOT PROVEN: what a blast does to them (the code of
     ZVehicleEffects / ZHavokCar was not read to the end). This is a belt-and-braces data fix: if the blast hides or
     deactivates the group's children, or the car's own parent chain matters, the copies are independent of all that;
     if the cause is somewhere else (the C key's slot 14, the player's feet, a Havok wreck pose) they change nothing.
     Moving cars (a ZHavokCar below the group: police cars that drive in) are left alone - a static copy at their
     spawn pose would be a ghost.
  2. SPARSE COVER (sparse()). Places = the navigation mesh, thinned to one in SAMPLE; at each place kl_fa_cover.objects()
     finds solid STATIC collision outlines (40..700 long, at least 10 thick, there at 45 over the floor too = not a
     table; not glass / fence / door ... names), kl_fa_cover.fit() picks the build's box model that fits it (low
     95..150 / high 150..320 tall). No box when: one stands within 60 of the object or within APART of the new box,
     inside a NoCoverBox, in an exit box, near the escape road, longer than ENDS (a wall: corners are another
     matter), or when fewer than 3 mesh points lie in the ring 70..230 round the box (nobody can stand at it).
     Convex or moving collision (crates the HVK stores convex, cars) is not seen by kl_fa_cover.Solid: a GUESS that
     most of the missing cover is static walls/planters/counters; crates stay without.
"""
import collections, json, math, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa_bots as F
import kl_fa_cover as C

MAX_NEW = 150
SAMPLE = 600.0              # one place per 600 x 600 of the mesh
SPREAD = 250.0              # new boxes at least this far apart (APART is 150: stock maps keep 150 minimum)
RING = (70.0, 230.0)
RING_NEED = 3
NEAR = 700.0
GROUP = 'KL_CoverMore!'
TAG = '_KM_'               # CoverBoxH_KM_01 ...
SEP = '\\'


class Lite:
    """What kl_fa_cover.apply needs (B) and what the sparse search needs, without a bots build."""

    def __init__(self, zp):
        self.B = B = F.Built(zp)
        self.folder = B.folder
        self.nav = F.Nav(B.scene.nav)
        st = F.stations(B, self.nav)
        self.exits = st['exits']
        self.lane = F.lanes(B)
        self.solid = C.Solid(B)
        self.boxes = C.all_boxes(B)
        sc = B.sc
        self.nocover = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZBoxPrimitive' and 'NoCoverBox' in [sc.p.key(c[0]) for c in sc.nodes[k]['ctrls']]]
        self.nocover += [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZBoxPrimitive' and 'nocoverbox' in sc.names[k].lower()]
        self.nocover = sorted(set(self.nocover))


def _ctl(sc, k):
    return [sc.p.key(c[0]) for c in sc.nodes[k]['ctrls']]


def cars(L, log=print):
    """Static copies of the cover boxes of parked cars -> [box dict for kl_fa_cover.apply]."""
    B, sc = L.B, L.B.sc
    groups = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZGROUP' and 'VehicleEffects' in _ctl(sc, k)]
    out, skipped = [], collections.Counter()
    form_ok = {f['node'] for f in C.forms(B, L.boxes, 'b', False)}
    for g in groups:
        pp = sc.path[g]
        below = [j for j in range(1, len(sc.nodes)) if sc.path[j].startswith(pp + SEP)]
        if any(sc.cls(j) == 'ZHavokCar' for j in below):
            skipped['moving car (ZHavokCar)'] += 1
            continue
        for j in below:
            if sc.path[j].count(SEP) != pp.count(SEP) + 1 or 'coverbox' not in sc.names[j].lower() or sc.cls(j) != 'ZSTDOBJ':
                continue
            e = B.ents[j - 1]
            if e.flags != 0x200 or sc.nodes[j]['ctrls'] or e.raw is not None or e.links is not None or e.aux or e.group:
                skipped['box not form b'] += 1
                continue
            Rm, T = B.fr[e]
            hx, hz = Rm[0][2], Rm[2][2]
            if Rm[1][1] < 0.95 or abs(math.hypot(hx, hz) - 1.0) > 0.02 or abs(Rm[0][0] - hz) > 0.02 or abs(Rm[2][0] + hx) > 0.02:
                skipped['box tilted or mirrored'] += 1       # (rot9's frame: local X = (hz, -hx))
                continue
            low = sc.names[j].lower()
            kind = 'high' if 'coverboxh' in low else 'low' if ('coverboxm' in low or 'coverboxl' in low) else None
            if kind is None:
                skipped['kind unknown'] += 1
                continue
            out.append({'kind': kind, 'origin': [round(v, 3) for v in T], 'head': [round(hx, 5), round(hz, 5)], 'model': e.model, 'form_node': j,
                        'tier': 'b', 'borrowed': None, 'via': 'car', 'object': sc.path[g].rsplit(SEP, 1)[-1], 'name': None})
    log('cars: %d vehicle groups, %d static copies of parked cars\' boxes (left out: %s)' % (len(groups), len(out), dict(skipped)))
    return out


def _free(L, mid, y, new):
    """No cover box (stock or planned) within APART of the new box's middle (x, z) = mid at height y: the rule
    kl_fa_cover.check() puts on every box of its group (APART - 1, 200 in height)."""
    for b in L.boxes + new:
        if b.get('kind') is None or b.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ':
            continue
        if math.hypot(b['mid'][0] - mid[0], b['mid'][2] - mid[1]) < C.APART and abs(b['mid'][1] - y) < 200:
            return False
    return True


def sparse(L, fs, new, max_new, spread, log=print):
    """Add boxes on solid objects the map has no cover on -> the number added. `new` is extended."""
    B, nav, S = L.B, L.nav, L.solid
    cell, picks = collections.defaultdict(list), []
    for i, v in enumerate(nav.pv):
        if not nav.ok[i]:
            continue
        m = nav.mid[i]
        cell[int(m[0] // SAMPLE), int(m[2] // SAMPLE)].append(i)
    for key, ps in sorted(cell.items()):
        ps.sort(key=lambda i: (nav.mid[i][0] - (key[0] + .5) * SAMPLE) ** 2 + (nav.mid[i][2] - (key[1] + .5) * SAMPLE) ** 2)
        picks.append(nav.mid[ps[0]])
    log('sparse: %d navigation polygons -> %d places' % (len(nav.pv), len(picks)))
    seen, why, cand = set(), collections.Counter(), []
    for p in picks:
        g = S.floor(p[0], p[1], p[2])
        y = p[1] if g is None else g
        for o in C.objects(S, B, p[0], y, p[2], NEAR):
            if o['no']:
                why[o['no'].split(' (')[0]] += 1
                continue
            cx, cz = o['rect'][0], o['rect'][1]
            key = (o['ref'], round(cx / 60), round(cz / 60), o['high'])
            if key in seen:
                continue
            seen.add(key)
            cand.append((o, p, y))
    log('sparse: %d solid objects seen; refused: %s' % (len(cand), dict(why)))
    # biggest first: a long counter before a post (the cap, if it bites, drops the small ones)
    cand.sort(key=lambda t: -(t[0]['rect'][4] * t[0]['rect'][5]))
    for o, p, y in cand:
        if len(new) >= max_new:
            why['cap'] += 1
            continue
        cx, cz, ux, uz, a, b = o['rect']
        if 2 * a > C.ENDS:
            why['long'] += 1
            continue
        got = C.fit(o, fs, (p[0], y, p[2]))
        if got is None:
            why['no model fits'] += 1
            continue
        f, mid = got['form'], got['mid']
        if not _free(L, mid, y + f['size'][1] / 2, new):
            why['has cover / crowded'] += 1
            continue
        if any(math.hypot(n['mid'][0] - mid[0], n['mid'][2] - mid[1]) < spread and abs(n['mid'][1] - y) < 300 for n in new):
            why['spread'] += 1
            continue
        org = (got['origin'][0], y - f['lo_y'], got['origin'][1])
        c3 = (mid[0], y + f['size'][1] / 2, mid[1])
        vx, vz = -uz, ux
        foot = [(mid[0] + su * got['ext'][0] / 2 * ux + sv * got['ext'][1] / 2 * vx, y + 50.0, mid[1] + su * got['ext'][0] / 2 * uz + sv * got['ext'][1] / 2 * vz)
                for su in (-1, 1) for sv in (-1, 1)] + [(mid[0], y + 50.0, mid[1])]
        if any(B.in_box(k, q) for k in L.nocover for q in foot):
            why['NoCoverBox'] += 1
            continue
        if L.exits and any(F.in_exit(B, L.exits, q) for q in foot):
            why['exit box'] += 1
            continue
        if L.lane and min(F.lane_dist(L.lane, q) for q in foot) < F.LANE_CLEAR:
            why['escape road'] += 1
            continue
        ring = 0
        for ix in range(-4, 5):
            for iz in range(-4, 5):
                x, z = mid[0] + ix * 40.0, mid[1] + iz * 40.0
                if RING[0] <= math.hypot(x - mid[0], z - mid[1]) <= RING[1] and nav.at(x, y, z, dy=60.0) is not None:
                    ring += 1
        if ring < RING_NEED:
            why['nobody can stand there'] += 1
            continue
        new.append({'kind': 'high' if o['high'] else 'low', 'origin': [round(v, 2) for v in org], 'head': [round(v, 5) for v in got['head']],
                    'mid': [round(v, 1) for v in c3], 'ext': [round(v, 1) for v in got['ext']], 'height': round(f['size'][1], 1), 'model': f['model'],
                    'form': f['path'], 'form_node': f['node'], 'tier': f['tier'], 'borrowed': f.get('borrowed'), 'object': o['name'], 'object_ref': o['ref'],
                    'ground': round(y, 1), 'via': 'sparse', 'name': None})
    log('sparse: added %d; not added: %s' % (sum(1 for n in new if n['via'] == 'sparse'), dict(why)))


def plan(zp, opt, log=print):
    use_slot(zp)
    L = Lite(zp)
    log('%s: %d entities, %d cover boxes (%d of the three kinds), %d NoCoverBox, %d solid triangles'
        % (zp, len(L.B.ents), len(L.boxes), sum(1 for b in L.boxes if b['kind']), len(L.nocover), len(L.solid.tris)))
    fs = C.forms(L.B, L.boxes, 'b', True)
    log('box models a new box may take: %s' % sorted('%dx%dx%d' % tuple(f['size']) for f in fs))
    new = []
    if opt['cars']:
        for c in cars(L, log):
            new.append(dict(c, mid=[c['origin'][0], c['origin'][1], c['origin'][2]]))
    n_cars = len(new)
    if opt['sparse'] and fs:
        sparse(L, fs, new, n_cars + opt['max'], opt['spread'], log)
    cnt = collections.Counter()
    for c in new:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', C.TAG, cnt[c['kind']])
    P = collections.OrderedDict(folder=L.folder, options=dict(opt), boxes=new)
    log('PLAN: %d boxes (%d low, %d high; %d car copies, %d sparse)' % (len(new), cnt['low'], cnt['high'], n_cars, len(new) - n_cars))
    return L, P


def _sizes(folder, slot=None):
    """kl_fa_bots.sizes without the loose .WAV (a staged map is the zip alone): the four large blocks of the zip."""
    import zipfile
    with zipfile.ZipFile(os.path.join(folder, (slot or F.SLOT) + '_Main.zip')) as z:
        return collections.OrderedDict((e, next(i.file_size for i in z.infolist() if i.filename.endswith('_Main' + e))) for e in F.BIG)


def use_slot(zp):
    """kl_fa_bots and kl_fa_cover default to the F01 slot; this map's zip is <slot>_Main.zip."""
    slot = os.path.basename(zp).split('_Main')[0]
    F.SLOT = slot
    F.Built.__init__.__defaults__ = (slot,)
    F.sizes = _sizes
    # the maps already carry a 'KL_CoverMore!' group (kl_fa_cover's own step, boxes CoverBox?_KL_nn): this step's group and
    # box tag are its own, or kl_fa_cover.check would find two groups of one name
    C.GROUP, C.TAG = GROUP, TAG
    return slot


def build(zp, dst, opt, log=print):
    use_slot(zp)
    L, P = plan(zp, opt, log)
    if not P['boxes']:
        log('nothing to add')
        return L, None, [], []
    rep = C.apply(L, P, dst, log)
    rep['plan'] = P
    with open(os.path.join(dst, 'cover.json'), 'w') as f:      # (kl_fa_cover.check reads the plan from it)
        json.dump(rep, f, indent=1, default=str)
    out = C.check(dst, log)
    # the car copies sit where a stock cover box of a parked car already stood: they fail kl_fa_cover's rules for NEW
    # boxes (no static collision under them - a car is not static -, a box of the same place, the plan's height) by design
    cn = tuple(c['name'] for c in P['boxes'] if c['via'] == 'car')
    out = [('NOTE', 'car copy: ' + t) if s == 'FAIL' and t.startswith(cn) and cn else (s, t) for s, t in out]
    for s_, t in out:
        if s_ == 'FAIL':
            log('FAIL after the car-copy exemption: ' + t)
    log('CHECK (car copies exempt from the new-box rules): %d FAIL, %d car-copy lines' % (sum(1 for s_, _t in out if s_ == 'FAIL'),
        sum(1 for s_, t in out if t.startswith('car copy'))))
    bad = C.diff(L.folder, dst, log)
    rep['check'] = [list(x) for x in out]
    with open(os.path.join(dst, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    return L, rep, out, bad


def options(a):
    opt = {'max': MAX_NEW, 'sparse': True, 'cars': True, 'spread': SPREAD}
    for flag, key in (('--no-sparse', 'sparse'), ('--no-cars', 'cars')):
        if flag in a:
            a.remove(flag); opt[key] = False
    for flag, key, conv in (('--max', 'max', int), ('--spread', 'spread', float)):
        if flag in a:
            i = a.index(flag); opt[key] = conv(a[i + 1]); del a[i:i + 2]
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 2 and a[0] == 'plan':
        plan(a[1], opt)
    elif len(a) == 3 and a[0] == 'build':
        _L, rep, out, bad = build(a[1], a[2], opt)
        sys.exit(1 if rep is None or any(s == 'FAIL' for s, _t in out) or bad else 0)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
