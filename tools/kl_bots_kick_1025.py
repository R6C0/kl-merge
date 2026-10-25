"""kl_bots_kick_1025.py - the heister bots KICK the grafted doors. Written 2026-10-25, OFFLINE only: nothing here is run in the game.

THE POST-PASS. The heister squads of a built map (ROOT\\Gameplay!merc_bot_squad!Squad#02..#08, made by kl_fa_bots and its _dyn / _rt variants)
walk from place to place with DefendBehaviourRout steps. The Dead Men maps carry KICK DOORS grafted from F03 (kl_interact_graft: KL_Interact!1\\KL_Door_N,
a KickDoor controller + ArrowFront / ArrowBack + a PathBlocker); a bot whose route leg runs through one simply walks into it. This pass gives such a
leg a door-kick step in the way Dog Days' own F03 bots have it (squad 'FASpecials!merc_bot_squad!Squad#08', '021_KickDoorBehaviourRout_...'):

    predecessor step --NEXT--> KickDoorBehaviourRout (+ PosInfo kid)  --NEXT--> the step B the leg led to

THE FORM (cloned from F03, nothing invented)
  - KickDoorBehaviourRout {0: [B], 1: 1}, named '<B prefix>_KickDoorBehaviourRout_<door>_<B suffix>', a kid of the SQUAD TOP (its init, 0x4aff50, looks up the
    parent's ZSquadScript). The squad top itself is NOT rebuilt: kl_prpjoin.join(adopt=) adds the new subtrees as the last children of the existing top, so every
    reference to the squad keeps resolving (0 dangling references is asserted).
  - PosInfo kid 'KickDoorBehaviour_PosInfo' {0: this squad's own Glazer_Bodyguard_0N group, 1: the door group}, standing on the approach side: 26 cm from the
    approach arrow toward the door, 14 cm above it, on the walking mesh part 'home' (F03: the same offsets).
  - one kick node per (successor step B, door sequence); every predecessor whose leg into B crosses the door has its NEXT entry for B pointed at it.
  - A leg crosses a door when its path (the Nav.path polyline when both ends are on the mesh, else the straight segment) passes through the DOORWAY: it
    crosses the plane through the PathBlocker centre, square to the arrows' line, within CROSS_LAT cm of that centre and CROSS_DY cm of the arrows' height.
    Near misses (the path runs past the door, along the wall) are skipped and logged, as is every other decision.

TOGGLE (owner's rule: every feature on/off). This is a map CONTENT change, so its on/off switch is the install / undo pair: `install.py` puts the staged zip
in and moves the original aside as '<zip>.before-1025hkick'; `install.py --undo` puts it back byte for byte (the live md5 is pinned before either).

Usage (from tools/):
  python kl_bots_kick_1025.py analyse <MAP zip> <slot>                 read-only: the doors, the legs, the decisions
  python kl_bots_kick_1025.py build <in zip> <slot> <out zip>          one map
  python kl_bots_kick_1025.py stage <root> [MAP ...]                   the four maps under <root>/<MAP>/{in,stage}, install.py, report.txt
  python kl_bots_kick_1025.py check <zip> <slot>
"""
import collections, hashlib, json, math, os, re, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_fa_fed as FED
import kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp, units

BS = chr(92)
R = 'ROOT' + BS
SQUAD = KB.SQUAD
TAG = '.before-1025hkick'
CROSS_LAT = 60.0         # cm: the path crosses the door plane this close to the PathBlocker centre (GUESS: the doorway is about 100 cm wide)
CROSS_DY = 250.0         # cm: ... and this close to the arrows' height
PI_OFF = 26.0            # cm from the approach arrow toward the door (F03)
PI_UP = 14.0             # cm above the arrow (F03)
KICK_SRC = 'FASpecials!merc_bot_squad!Squad#08' + BS + '021_KickDoorBehaviourRout_hangar_side_entrance#01'
# the fields that name the NEXT steps of a class (kl_fa_bots.check; RandomTrigger: the single-target lists 5..8)
NEXT = {'DefendBehaviourRout': (7,), 'SquadModifierBehaviour': (26,), 'TriggerDelay2': (4,), 'TriggerLootDepleted': (4,), 'TriggerActorsDead': (2,),
        'TriggerCounter': (4,), 'KickDoorBehaviourRout': (0,), 'RunToCoverBehaviourRout': (0,), 'RandomTrigger': (5, 6, 7, 8)}
STEP = ('DefendBehaviourRout', 'KickDoorBehaviourRout', 'RunToCoverBehaviourRout')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def hd(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


# ------------------------------------------------------------------ the doors
def doors(B):
    """Every KickDoor of the build: {'group': path, 'node': k (the controller's), 'pb': [(path, pos)], 'front', 'back': positions, 'n': unit (x, z) from front to back}."""
    sc = B.sc
    out = []
    for k, _i, v in kl_fa.controllers(sc, 'KickDoor'):
        grp = sc.path[k].rsplit(BS, 1)[0]

        def g(s):
            if isinstance(s, str) and s.startswith('<G>'):
                s = grp + s[3:]
            r = sc.resolve(s) if isinstance(s, str) and s else []
            return r[0] if r else None
        fr, bk = g(v[6]), g(v[7])
        pbs = []
        for s in (v[3] if isinstance(v[3], list) else []):
            j = g(s)
            if j and 'athblock' in sc.path[j]:
                pbs.append((sc.path[j], tuple(B.at(j))))
        if not (fr and bk and pbs):
            continue
        f, b = tuple(B.at(fr)), tuple(B.at(bk))
        L = hd(f, b) or 1.0
        out.append(dict(group=grp, node=k, pb=pbs, front=f, back=b, n=((b[0] - f[0]) / L, (b[2] - f[2]) / L), name=grp.rsplit(BS, 1)[1]))
    return out


def crossing(d, poly):
    """The first crossing of door d by the polyline `poly` ([(x, y, z)]): (index of the segment, side the path comes from (+1 = the back arrow's side, -1 = the front's),
    lateral cm from the PathBlocker centre, dy cm from the arrows' height) or None. Also the closest approach to the centre as the second value."""
    n = d['n']
    ay = (d['front'][1] + d['back'][1]) / 2.0
    best, near = None, 1e9
    for pbp, c in d['pb']:
        def s_of(p):
            return (p[0] - c[0]) * n[0] + (p[2] - c[2]) * n[1]
        for i in range(len(poly) - 1):
            a, b = poly[i], poly[i + 1]
            sa, sb = s_of(a), s_of(b)
            # closest approach (horizontal) of the segment to the centre
            dx, dz = b[0] - a[0], b[2] - a[2]
            L2 = dx * dx + dz * dz
            t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, ((c[0] - a[0]) * dx + (c[2] - a[2]) * dz) / L2))
            near = min(near, math.hypot(a[0] + t * dx - c[0], a[2] + t * dz - c[2]))
            if sa == sb or sa * sb > 0:
                continue
            t = sa / (sa - sb)
            x, y, z = a[0] + t * dx, a[1] + t * (b[1] - a[1]), a[2] + t * dz
            lat = abs((x - c[0]) * -n[1] + (z - c[2]) * n[0])
            dy = abs(y - ay)
            if lat <= CROSS_LAT and dy <= CROSS_DY:
                cand = (i + t, 1 if sa > 0 else -1, lat, dy)
                if best is None or cand[0] < best[0]:
                    best = cand
    return best, near


# ------------------------------------------------------------------ the squads as a graph
def squads(B):
    """{top: dict(name, actor (world place), nodes {k: (class, values)}, nxt {k: [(target node, field)]}, places {step: [pos]}, starts [first steps])}."""
    sc = B.sc
    res = sc.resolve
    timer = res(R + SQUAD + 'Timer_start_bots')
    tops = [t for t in sc.tops() if sc.names[t].startswith(SQUAD + 'Squad#')]
    out = collections.OrderedDict()
    allc = collections.defaultdict(dict)
    for cn in NEXT:
        for k, i, v in kl_fa.controllers(sc, cn):
            allc[sc.top[k]][k] = (cn, i, v)
    for t in tops:
        nodes = allc.get(t, {})
        nxt = collections.defaultdict(list)
        for k, (cn, _i, v) in nodes.items():
            for f in NEXT[cn]:
                if f < len(v) and isinstance(v[f], list):
                    for s in v[f]:
                        for j in res(s):
                            if sc.top[j] == t:
                                nxt[k].append((j, f))
        places = {}
        for k, (cn, _i, v) in nodes.items():
            if cn == 'DefendBehaviourRout':
                tg = ([v[0]] if v[0] else []) + list(v[1])
                places[k] = [tuple(B.at(r[0])) for s in tg for r in [res(s)] if r]
        actors = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        start = []
        for tm in timer:
            for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2'):
                if k == tm:
                    start = [j for s in v[4] for j in res(s) if sc.top[j] == t]
        out[t] = dict(name=sc.names[t], actor=tuple(B.at(actors[0])) if actors else None, actor_node=actors[0] if actors else None, nodes=nodes,
                      nxt=nxt, places=places, starts=start)
    return out


def origins(S, k, memo=None, stack=()):
    """The places a bot may come from into node k's NEXT target (k = a holder: a step, a timer, a fork..): {('place', pos, step) or ('spawn', pos)}."""
    if memo is None:
        memo = {}
    if k in memo:
        return memo[k]
    if k in stack:
        return set()
    cn = S['nodes'].get(k, (None,))[0]
    if cn == 'DefendBehaviourRout' and S['places'].get(k):
        r = {('place', S['places'][k][-1], k)}
    elif cn in STEP:
        r = {('unknown', None, k)}
    else:
        r = set()
        for p, lst in S['nxt'].items():
            if any(j == k for j, _f in lst):
                r |= origins(S, p, memo, stack + (k,))
        if k in S['starts'] and S['actor']:
            r.add(('spawn', S['actor'], None))
    memo[k] = r
    return r


# ------------------------------------------------------------------ the legs
def leg_path(nav, a, b):
    """The polyline of a leg a -> b: (points, 'nav' | 'line')."""
    if nav is not None:
        try:
            A, Q = nav.at(a[0], a[1], a[2], dy=400.0), nav.at(b[0], b[1], b[2], dy=400.0)
            if A and Q:
                r = nav.path((a[0], A[1], a[2], A[0]), (b[0], Q[1], b[2], Q[0]))
                if r:
                    return [tuple(p[:3]) for p in r[0]], 'nav'
        except Exception:
            pass
    return [tuple(a), tuple(b)], 'line'


def leg_doors(ds, nav, a, b, cache):
    """[(door index, side, lateral, dy, param)] of the doors the leg a -> b goes through, in walking order; and a list of near misses [(door index, cm)]."""
    key = (tuple(round(v, 1) for v in a), tuple(round(v, 1) for v in b))
    if key in cache:
        return cache[key]
    poly, via = leg_path(nav, a, b)
    line = [tuple(a), tuple(b)]
    hits, miss = [], []
    for di, d in enumerate(ds):
        c, near = crossing(d, poly)
        if c is None and via == 'nav':
            c2, near2 = crossing(d, line)        # the straight line crosses but the mesh path does not: logged, not acted on
            if c2 is not None:
                miss.append((di, round(near), 'the straight line crosses at %.0f cm, the mesh path goes round (nearest %.0f cm)' % (c2[2], near)))
            elif near <= 150.0:
                miss.append((di, round(near), 'near miss'))
        elif c is None:
            if near <= 150.0:
                miss.append((di, round(near), 'near miss'))
        else:
            hits.append((di, c[1], round(c[2]), round(c[3]), c[0]))
    hits.sort(key=lambda h: h[4])
    seen, seq = set(), []
    for h in hits:
        if h[0] in seen:
            miss.append((h[0], h[2], 'crossed again on the same leg: only the first crossing is kicked'))
            continue
        seen.add(h[0]); seq.append(h)
    cache[key] = (seq, miss, via)
    return cache[key]


def plan_legs(B, nav, log):
    """Per squad: the holders whose NEXT names a Defend step and the door sequence each origin walks into it."""
    sc = B.sc
    ds = doors(B)
    SQ = squads(B)
    cache = {}
    plan = []
    for t, S in SQ.items():
        memo = {}
        for h in sorted(S['nxt']):
            for j, f in S['nxt'][h]:
                cj = S['nodes'].get(j, (None,))[0]
                if cj != 'DefendBehaviourRout' or not S['places'].get(j):
                    continue
                b = S['places'][j][0]
                seqs = collections.OrderedDict()
                for o in sorted(origins(S, h, memo), key=lambda o: (o[0], str(o[1]))):
                    if o[0] == 'unknown':
                        seqs[o] = None
                        continue
                    seq, miss, via = leg_doors(ds, nav, o[1], b, cache)
                    seqs[o] = (seq, miss, via)
                plan.append(dict(top=t, holder=h, field=f, step=j, b=b, seqs=seqs))
    return ds, SQ, plan


# ------------------------------------------------------------------ the decisions
def sig_of(v):
    return tuple((h[0], h[1]) for h in v[0])


def approach(d, side):
    """(arrow position, name) of the arrow on the side the path comes from: side +1 is the back arrow's side (n points front -> back)."""
    return (d['back'], 'ArrowBack') if side > 0 else (d['front'], 'ArrowFront')


def posinfo_at(d, side, nav, home):
    """Where the PosInfo of a kick of door d from `side` stands: 26 cm from the approach arrow toward the PathBlocker centre, 14 cm above the arrow.
    -> (position, note) or (None, why). The mesh test is nav.at(.., dy=60) on part `home` (the walking part of the crew)."""
    a, an = approach(d, side)
    c = d['pb'][0][1]
    L = hd(a, c) or 1.0
    ux, uz = (c[0] - a[0]) / L, (c[2] - a[2]) / L
    for off, note in ((PI_OFF, '%d cm toward the door' % PI_OFF), (0.0, 'ON the arrow (the 26 cm point is off the mesh part; GUESS)')):
        p = (a[0] + ux * off, a[1] + PI_UP, a[2] + uz * off)
        h = nav.at(p[0], p[1], p[2], dy=60.0)
        if h and nav.part[h[0]] == home:
            return p, '%s, %s' % (an, note)
    return None, '%s is not on the walking mesh part (the bot could not reach a PosInfo there)' % an


def slug(name):
    m = re.match(r'(\d+)_(.*)$', name)
    pre, rest = (m.group(1), m.group(2)) if m else ('021', name)
    return pre, re.sub(r'^DefendBehaviou?r(_)?', '', rest) or 'step'


def decide(B, nav, log):
    """-> dict(kicks [spec], redirects [(top, holder, field, step, kick key)], skipped [text], doors, squads)."""
    sc = B.sc
    home = KB.stations(B, nav)['home']
    ds, SQ, plan = plan_legs(B, nav, log)
    pos = {}
    for di, d in enumerate(ds):
        for side in (1, -1):
            pos[di, side] = posinfo_at(d, side, nav, home)
    kicks = collections.OrderedDict()          # (top, step, sig) -> spec
    redirects, skipped, seen_msgs = [], [], set()
    stat = collections.Counter()
    for p in plan:
        S = SQ[p['top']]
        nm = lambda k: sc.names[k]
        sets = collections.OrderedDict()
        for o, v in p['seqs'].items():
            if v is None:
                continue
            sets.setdefault(sig_of(v), []).append(o)
            for di, near, why in v[1]:
                msg = '%s %s -> %s: door %s: %s (%s) - skipped' % (S['name'][-8:], nm(o[2]) if o[2] else 'spawn', nm(p['step']), ds[di]['name'], why, near)
                if msg not in seen_msgs:
                    seen_msgs.add(msg); skipped.append(msg)
        real = {s: os_ for s, os_ in sets.items() if s}
        if not real:
            stat['no crossing'] += 1
            continue
        where = '%s %s -> %s' % (S['name'][-8:], nm(p['holder']), nm(p['step']))
        if len(sets) > 1:
            stat['mixed holder skipped'] += 1
            skipped.append('%s: MIXED - origins %s walk different door sequences (%s) and the holder cannot tell them apart - not redirected' % (
                where, ', '.join(nm(o[2]) if o[2] else 'spawn' for os_ in sets.values() for o in os_), ' | '.join(
                    '+'.join('%s/%+d' % (ds[di]['name'], sd) for di, sd in s) or 'none' for s in sets)))
            continue
        sig = next(iter(real))
        bad = [(di, sd) for di, sd in sig if pos[di, sd][0] is None]
        if bad:
            stat['no PosInfo spot'] += 1
            skipped.append('%s: %s - %s - not redirected' % (where, '+'.join('%s/%+d' % (ds[di]['name'], sd) for di, sd in sig), pos[bad[0]][1]))
            continue
        stat['redirected'] += 1
        key = (p['top'], p['step'], sig)
        kicks.setdefault(key, dict(top=p['top'], step=p['step'], sig=sig, via=[]))['via'].append((p['holder'], p['field']))
        redirects.append((p['top'], p['holder'], p['field'], p['step'], key))
        log('  %s: %s via %s' % (where, ' then '.join('%s (from the %s side)' % (ds[di]['name'], 'back' if sd > 0 else 'front') for di, sd in sig),
                                 sets[sig][0][0]))
    log('  decisions: %s' % dict(stat))
    return dict(kicks=kicks, redirects=redirects, skipped=skipped, doors=ds, squads=SQ, pos=pos, stat=stat, home=home)


# ------------------------------------------------------------------ the nodes
def kick_name(D, key_sig, step_name):
    pre, sl = slug(step_name)
    ds = D['doors']
    part = lambda di, sd: '%s%s' % (re.sub(r'^KL_', '', ds[di]['name']).replace('_', ''), 'b' if sd > 0 else 'f')
    return '%s_KickDoorBehaviourRout_%s_%s' % (pre, '_'.join(part(*s) for s in key_sig), sl)


def make_specs(B, D):
    """The kick nodes to make -> (specs [dict], first {(top, step, sig): name of the chain's first node}). One node per (top, step B, door sequence suffix)."""
    sc = B.sc
    specs, first, made = [], {}, {}
    for key in D['kicks']:
        t, j, sig = key
        me = sc.names[t]
        grp = [k for k in range(t, sc.end[t]) if sc.parent[k] == t and sc.names[k].startswith('Glazer_Bodyguard')]
        if len(grp) != 1:
            raise ValueError('%s: %d Glazer_Bodyguard groups' % (me, len(grp)))
        actor_grp = R + me + BS + sc.names[grp[0]]
        for i in range(len(sig)):
            sub = sig[i:]
            kk = (t, j, sub)
            if kk in made:
                continue
            name = kick_name(D, sub, sc.names[j])
            if any(n['name'] == name and n['top'] == t for n in specs):
                raise ValueError('%s: kick name %s used twice' % (me, name))
            nxt = sc.path[j] if len(sub) == 1 else R + me + BS + kick_name(D, sub[1:], sc.names[j])
            di, sd = sub[0]
            made[kk] = name
            specs.append(dict(top=t, name=name, step=j, door=di, side=sd, next=nxt, actor=actor_grp, sig=sub,
                              pos=D['pos'][di, sd][0], note=D['pos'][di, sd][1]))
        first[key] = made[(t, j, sig)]
    return specs, first


def build_scene(B, D, specs):
    sc = B.sc
    M = KB.Maker()
    tops, per = [], collections.OrderedDict()
    for s in specs:
        me = sc.names[s['top']]
        d = D['doors'][s['door']]
        kr = M.clone('F03', R + KICK_SRC, s['name'])
        M.place(kr, (0.0, 0.0, 0.0))
        M.set(kr, 'KickDoorBehaviourRout', {0: [s['next']], 1: 1})
        pi = kr.add(M.clone('F03', R + KICK_SRC + BS + 'KickDoorBehaviour_PosInfo', 'KickDoorBehaviour_PosInfo'))
        M.place(pi, s['pos'])
        M.set(pi, 'KickDoorBehaviour_PosInfo', {0: s['actor'], 1: d['group']})
        tops.append(kr)
        per.setdefault(s['top'], []).append(len(tops) - 1)
    q, order = M.scene(tops)
    qt = q.tops()
    if len(qt) != len(tops):
        raise ValueError('kick scene: %d tops for %d nodes' % (len(qt), len(tops)))
    return M, q, order, tops, per, qt


# ------------------------------------------------------------------ the zip, a member-level patch
def patch_zip(src, dst, repl):
    """src with the members in `repl` {name: bytes} replaced and every other member copied unchanged (bytes, compression, stamp, order)."""
    n = 0
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            i2 = zipfile.ZipInfo(info.filename, info.date_time)
            i2.compress_type, i2.external_attr, i2.create_system = info.compress_type, info.external_attr, info.create_system
            i2.comment = info.comment
            if info.filename in repl:
                zo.writestr(i2, repl[info.filename], compress_type=info.compress_type)
                n += 1
            else:
                with zi.open(info) as fi, zo.open(i2, 'w', force_zip64=info.file_size > 0x7fffffff) as fo:
                    while True:
                        c = fi.read(1 << 20)
                        if not c:
                            break
                        fo.write(c)
    if n != len(repl):
        raise ValueError('%s: %d of %d members to replace were found' % (src, n, len(repl)))


# ------------------------------------------------------------------ build
def build(src, slot, dst, log=print):
    """src zip -> dst zip (the kicks in) -> report dict. Nothing to kick -> report with md5_out None, nothing written."""
    import kl_fa_bank
    B = KB.Built(src, slot)
    sc = B.sc
    h_in = md5(src)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    nav = KB.Nav(A.nav, links=True)
    D = decide(B, nav, log)
    if not D['kicks']:
        log('  no leg runs through a kick door: nothing to do')
        return collections.OrderedDict(md5_in=h_in, md5_out=None, kicks=[], decisions=dict(D['stat']), skipped=D['skipped'], doors=[d['name'] for d in D['doors']])
    specs, first = make_specs(B, D)
    M, q, order, tops, per, qt = build_scene(B, D, specs)
    adopt = {t: [(q, qt[i]) for i in idx] for t, idx in per.items()}
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'hkick', adopt=adopt)
    # ---- the predecessors' NEXT entries: B -> the first kick node of the chain
    cut = collections.Counter()
    for t, h, f, j, key in D['redirects']:
        me = sc.names[t]
        kh = Jn.resolve(sc.path[h])
        if len(kh) != 1:
            raise ValueError('%s: %d nodes in the joined tree' % (sc.path[h], len(kh)))
        kh = kh[0]
        cn = D['squads'][t]['nodes'][h][0]
        ci = AU.ctrl_of(Jn, kh, cn)
        old, new = sc.path[j].lower(), R + me + BS + first[key]

        def fn(us, h=h, f=f, j=j, old=old, new=new):
            ks = [Jn.p.key(x) for x in us[f][1:]]
            hit = [i for i, x in enumerate(ks) if x.lower() == old]
            if len(hit) != 1:
                raise ValueError('%s field %d names %s %d times' % (sc.path[h], f, sc.path[j], len(hit)))
            ks[hit[0]] = new
            us[f] = kl_fa._refs(Jn, ks)
            cut['entries'] += 1
        kl_fa.edit(Jn, kh, ci, fn)
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    log('  %d kick nodes (+ %d PosInfo kids), %d NEXT entries redirected' % (len(specs), len(specs), cut['entries']))
    # ---- .gms / .buf: the new entities are the last kids of their squad tops
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
        e.ref = nxt
        nxt += 1
        e.parent = parent
        e.kids = []
        parent.kids.append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t, idx in per.items():
        for i in idx:
            ent(tops[i], B.ents[t - 1])
    A.ref_slots = max(A.ref_slots, nxt)
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    # the step groups are listed in the root's group tree 3 (kl_fa_bots.apply): the kick groups join them, box of the PosInfo +- 10
    listed = [s for s in specs if (slot0[B.ents[s['step'] - 1]] + 2) in {it[0] for it in (octx.rooms[0][3].items if octx.rooms[0][3] is not None else [])}]
    items = []
    if listed:
        for s in specs:
            nd = tops[specs.index(s)]
            p = nd.kids[0].pos
            items.append((slot1[made[id(nd)]] + 2, tuple(v - 10.0 for v in p), tuple(v + 10.0 for v in p)))
    repointed, new_prm = 0, None
    if items:
        r3 = octn.rooms[0][3]
        octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(B['.prm'])
            tt, nn = struct.unpack_from('<II', prm, 0)
            old = set(octx.record_refs())
            for i in range(1, nn):
                off, size = struct.unpack_from('<II', prm, tt + 16 * i)
                if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, off + 0x1c, move[v])
                        repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('room sets after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    repl = {B.ext[e]: new[B.ext[e]] for e in changed}
    work = tempfile.mkdtemp(prefix='hkick_')
    try:
        wz = os.path.join(work, os.path.basename(dst))
        patch_zip(src, wz, repl)
        # seal is run on throwaway COPIES (it rewrites the .buf in place): the stray room-list entries it would move must be exactly the input's own
        counts = []
        for zsrc in (src, wz):
            tmpd = tempfile.mkdtemp(prefix='hkick_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, os.path.basename(dst)))
                counts.append(kl_fa_bank.seal(tmpd, log=lambda *_: None))
            finally:
                rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        log('  seal: %d stray room-list entries, the same as in the input, none of them new' % counts[1])
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        base_problems = []
        try:
            wi = tempfile.mkdtemp(prefix='hkick_in_')
            shutil.copyfile(src, os.path.join(wi, os.path.basename(dst)))
            base_problems = kl_fa_bank.reverify(wi, log=lambda *_: None)
        finally:
            rmtree(wi)
        problems = [x for x in problems if x not in base_problems]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(wz, dst)
    finally:
        rmtree(work)
    kicks = []
    for s in specs:
        d = D['doors'][s['door']]
        kicks.append(collections.OrderedDict(squad=sc.names[s['top']].rsplit('!', 1)[1], node=s['name'], step=sc.names[s['step']], door=d['name'],
                                             side='ArrowBack' if s['side'] > 0 else 'ArrowFront', posinfo=[round(v, 1) for v in s['pos']],
                                             note=s['note'], next=s['next'].rsplit(BS, 1)[1], redirected_entries=0))
    byname = {(k['squad'], k['node']): k for k in kicks}
    for t, h, f, j, key in D['redirects']:
        byname[sc.names[t].rsplit('!', 1)[1], first[key]]['redirected_entries'] += 1
    rep = collections.OrderedDict(
        md5_in=h_in, md5_out=md5(dst), members_changed=changed, entities_before=len(B.ents), entities=len(allents), added=len(order), kicks=kicks,
        redirected=cut['entries'], slot_ids_moved=moved, tree3_items=len(items), prm_roots_repointed=repointed, decisions=dict(D['stat']),
        skipped=D['skipped'], doors=[d['name'] for d in D['doors']], room_sets=[str(pre), str(post)])
    log('  members changed: %s; %d entities added, %d slot ids renumbered, %d tree-3 items, %d .prm roots re-pointed' % (
        ' '.join(changed), len(order), moved, len(items), repointed))
    return rep


# ------------------------------------------------------------------ the maps, the installer, the report
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = collections.OrderedDict([                  # name -> (slot, zip name, pinned live md5)
    ('DM01', ('F01', 'F01_Main.zip', '3858b4417e503de26a956182392dec7a')),      # e8's AKM sound fix (1025akmsound) on top of c1b92f9b
    ('DM02', ('F02', 'F02_Main.zip', 'b0252fde90cd3d4100c80a8018d4ee84')),
    ('DM03A', ('F07', 'F07_Main.zip', 'a869705b8f65232a40ec97dac0ca4ab6')),
    ('DM01B', ('F03', 'F03_Main.zip', '186cf3f81e16bd900c90230213336b7e'))])

INSTALL_PY = '''"""Installs / undoes the staged %(map)s door-kick zip (tools/kl_bots_kick_1025.py, 2026-10-25). This pair IS the feature's on/off switch.
  python install.py           put %(zip)s in (the original moves to %(zip)s%(tag)s)
  python install.py --undo    put the original back, byte for byte
  --game <dir>                a Dog Days folder other than the default (rehearsals)
The live md5 is pinned before either step; nothing is written while kl2.exe runs."""
import hashlib, os, shutil, subprocess, sys

GAME = %(game)r
MAP, ZIP, TAG = %(map)r, %(zip)r, %(tag)r
OLD, NEW = %(old)r, %(new)r


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    a = sys.argv[1:]
    undo = '--undo' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    live = os.path.join(game, 'KLExpansion', 'Maps', MAP, ZIP)
    bak = live + TAG
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), ZIP)
    if '--skip-run-check' not in a and 'kl2.exe' in subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower():
        print('REFUSED: kl2.exe is running'); return 3
    if not os.path.isfile(live):
        print('REFUSED: %%s is not there' %% live); return 2
    cur = md5(live)
    if undo:
        if not os.path.isfile(bak):
            print('nothing to undo: no %%s' %% bak); return 0
        if cur != NEW:
            print('REFUSED: live md5 %%s is not the installed %%s' %% (cur, NEW)); return 2
        if md5(bak) != OLD:
            print('REFUSED: backup md5 %%s is not %%s' %% (md5(bak), OLD)); return 2
        os.replace(bak, live)
        print('undone: %%s md5 %%s' %% (live, md5(live))); return 0
    if cur == NEW and os.path.isfile(bak):
        print('already installed'); return 0
    if cur != OLD:
        print('REFUSED: live md5 %%s is not the pinned %%s (the map was changed since this was staged)' %% (cur, OLD)); return 2
    if os.path.exists(bak):
        print('REFUSED: %%s exists already' %% bak); return 2
    if md5(here) != NEW:
        print('REFUSED: the staged zip next to install.py is not md5 %%s' %% NEW); return 2
    os.replace(live, bak)
    shutil.copyfile(here, live)
    if md5(live) != NEW:
        os.replace(bak, live)
        print('copy failed, original put back'); return 2
    print('installed: %%s md5 %%s' %% (live, NEW)); return 0


if __name__ == '__main__':
    sys.exit(main())
'''


def rmtree(p):
    def w(f, q, _e):
        os.chmod(q, 0o666)
        f(q)
    if os.path.isdir(p):
        shutil.rmtree(p, onexc=w)


def rehearse(d, name, old_zip, new_md5, old_md5, scratch, log=print):
    """Install, undo (byte-identical), reinstall, again, undo, wrong live md5 refused - on a COPY tree under scratch, never the game folder."""
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game_' + name)
    slot, zn, _p = MAPS[name]
    live = os.path.join(g, 'KLExpansion', 'Maps', name, zn)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    rmtree(g)
    os.makedirs(os.path.dirname(live))
    shutil.copy2(old_zip, live)
    run = lambda *x: subprocess.run([sys.executable, os.path.join(d, 'install.py'), '--game', g, '--skip-run-check'] + list(x), capture_output=True, text=True).stdout
    t = run(); log('  ' + t.strip()); assert 'installed' in t and md5(live) == new_md5, t
    assert os.path.isfile(live + TAG) and md5(live + TAG) == old_md5
    t = run('--undo'); log('  ' + t.strip())
    assert md5(live) == old_md5 and not os.path.exists(live + TAG), 'undo not byte identical'
    assert open(live, 'rb').read() == open(old_zip, 'rb').read()
    t = run(); assert md5(live) == new_md5, t
    t = run(); assert 'already installed' in t, t
    t = run('--undo'); assert md5(live) == old_md5 and not os.path.exists(live + TAG)
    os.chmod(live, 0o666)                          # the input copy is read-only
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run(); log('  ' + t.strip()); assert 'REFUSED' in t and not os.path.exists(live + TAG), t
    rmtree(g)
    log('  rehearsal ok (install, undo byte-identical, reinstall, again = no-op, wrong live md5 refused)')


def report_text(name, rep, extra=()):
    L = ['%s - door kicks for the heister bot squads (tools/kl_bots_kick_1025.py, 2026-10-25, STAGED, not installed)' % name, '']
    L.append('doors in the map: %s' % ', '.join(rep['doors']))
    L.append('decisions: %s' % dict(rep['decisions']))
    if not rep['kicks']:
        L.append('NO kick nodes added: no heister leg runs through a kick door\'s doorway on this map (zip not rebuilt, no installer).')
    else:
        L.append('md5 in  %s' % rep['md5_in'])
        L.append('md5 out %s' % rep['md5_out'])
        L.append('members changed: %s; %d entities added; %d slot ids renumbered; %d tree-3 items; %d .prm model roots re-pointed (only the .oct record numbers moved)' % (
            ' '.join(rep['members_changed']), rep['added'], rep['slot_ids_moved'], rep['tree3_items'], rep['prm_roots_repointed']))
        L.append('NEXT entries redirected: %d' % rep['redirected'])
        L.append('')
        L.append('kick nodes (squad / node / B step / door / side / PosInfo position / NEXT / entries pointing at it):')
        for k in rep['kicks']:
            L.append('  %s  %s  B=%s  %s  %s  PosInfo %s (%s)  -> %s  x%d' % (k['squad'], k['node'], k['step'], k['door'], k['side'], tuple(k['posinfo']), k['note'], k['next'], k['redirected_entries']))
    L.append('')
    L.append('skipped (%d):' % len(rep['skipped']))
    L += ['  ' + s for s in rep['skipped']]
    L += list(extra)
    return '\n'.join(L) + '\n'


def stage(root, names=None, scratch=None, log=print):
    free = shutil.disk_usage(root).free
    if free < 3 << 30:
        raise SystemExit('only %d MB free under %s (need 3 GB)' % (free >> 20, root))
    for name in names or MAPS:
        slot, zn, pin = MAPS[name]
        d = os.path.join(root, name)
        src = os.path.join(d, 'in', zn)
        if not os.path.isfile(src):
            raise SystemExit('%s is not there (copy the live zip and its .WAV in first)' % src)
        h = md5(src)
        if not h.startswith(pin):
            raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, pin))
        log('== %s (%s) ==' % (name, zn))
        out = os.path.join(d, 'stage')
        rmtree(out)
        os.makedirs(out)
        rep = build(src, slot, os.path.join(out, zn), log)
        if not rep['kicks']:
            for f in os.listdir(out):
                os.remove(os.path.join(out, f))
            open(os.path.join(d, 'report.txt'), 'w').write(report_text(name, rep))
            continue
        with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
            fh.write(INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=h, new=rep['md5_out']))
        with open(os.path.join(out, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        open(os.path.join(d, 'report.txt'), 'w').write(report_text(name, rep))
        if scratch:
            rehearse(out, name, src, rep['md5_out'], h, scratch, log)
    return 0


def analyse(src, slot, log=print):
    B = KB.Built(src, slot)
    nav = KB.Nav(B.scene.nav, links=True)
    D = decide(B, nav, log)
    for s in D['skipped']:
        log('  skipped: ' + s)
    return D


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('analyse', 'build', 'stage', 'check'):
        print(__doc__)
        return 2
    if a[0] == 'analyse':
        analyse(a[1], a[2])
    elif a[0] == 'build':
        build(a[1], a[2], a[3])
    elif a[0] == 'stage':
        return stage(a[1], [x for x in a[2:] if x in MAPS] or None, opt('--rehearse'))
    else:
        import kl_fa_bots_dyn as DYN
        o, _f = DYN.check(a[1], base=True)
        bad = [t for s, t in o if s == 'FAIL']
        for s, t in o:
            print(s, t)
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
