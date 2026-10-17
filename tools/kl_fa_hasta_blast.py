#!/usr/bin/env python3
"""
HASTA (M11_B): the timer-driven corner blast that step 3b could not build. OFFLINE; nothing here installs anything or starts the game.
Behind a flag of kl_fa_hasta_layer (`--blast [S]`) and of the chain (`kl_fa_hasta.py chain <out> --blast [S]`); without it
the layer, and so the whole build, is untouched (the layer calls this module only when kl_fa_hasta_layer.BLAST_AT is not None).

    python kl_fa_hasta_blast.py check <folder-or-archive>   read the blast back from a built level: chain, values, particle groups -> exit 1 on a fault
    python kl_fa_hasta_blast.py selftest                    the plan against F07 itself (no build, 5 s): boxes exist, clusters resolve, matrices proper

WHY A NEW SET OF OBJECTS (re/hasta_fa.md 3b): M11_B's BoomBoxDust is an Explode with an EMPTY effect name (the bunker's dust), the rooftop BoomBox names
FX_Grenade_T72_02 inside the campaign's dropped mainsceneincludes.zip, and the tank shell is a T72 group. So the blast is made the way kl_fa_blast.py
made Retomoto's window blast (re/retomoto_blast.md), from F07's own systems, and its helpers are imported from there:
  * six spare single-node ZBoxPrimitive boxes of F07's shutter script (same six as Retomoto: the script is dropped from Hasta, none is named by the monitor)
    are re-placed at the Capitol corner and given new controllers: the FAN (its own AIDWrapper 'Activate' to the boxes below + DocuCamControl 'AITrigger'
    'OnExplosion', the hand-held camera jolt of stock Subway), CLOUD (Explode -> the rocket's fireball cluster FX_Grenade_RPG_01 + the rocket's sound),
    SPRAY (Explode -> Rocket_Default_01, blowing INTO the hall; + ShakeCamera 3.0, 'Activate', 0, 8000 = stock F01's scExplosion), DUST S / DUST N (Explode ->
    Concrete_02 concrete dust on both sides of the hole; Retomoto used Glass_Exit_01 there, a glass window), SECOND (off).
  * Explode and ShakeCamera are cloned token for token from stock F07's Rocket_RPG7; both radii 1 and tinnitus 0: pictures and sound, nobody is hurt.
  * a seventh spare box, F07's TimerShuttersClose_RIGHT (a TriggerDelay2, NOT named by the monitor; TimerShuttersOpen is, and it would switch the van on at 0 s),
    becomes the BLAST TIMER: delay BLAST_AT, names the fan; the AIMonitor names the timer (as it names the layer's start timer), so it starts with the round.
No bomb to edit: M11_B has none at the corner (Retomoto's InvisiBomb / BombWindow03 have no counterpart).

ASSUMED / GUESS (each marked where it stands): every coordinate (the corner marker is MEASURED, the rest is offsets from it), the inward direction, BLAST_AT,
the matrix layout of a turn that takes local +Y to an arbitrary horizontal direction (Retomoto's OUT turned about the world Y axis; seen live only for the
cardinal case +x), whether F07's rocket sound offset is still valid in the joined .SND (it is read from the joined scene at prepare time, as Retomoto's).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_author as au
import kl_fa_blast as B
import kl_prpjoin as J

R = 'ROOT\\'
BLAST = 1.0                             # strength knob (as kl_fa_blast.BLAST): shake strength 3.0 x BLAST. GUESS
FIRE = True                             # the cloud is the rocket's fireball (a tank shell burns); False = concrete dust
SOUND = True                            # the cloud plays the rocket's explosion sound
BLAST_AT = 1.5                          # s from the round-start event to the blast (the layer's hall squads wake at 2.0). GUESS
SH = 'Gameplay!010_FirstFight!Shutters!'
TIMER = SH + 'TimerShuttersClose_RIGHT'
HOLE = (32095.0, 888.0, 29022.0)        # MEASURED: the Capitol corner marker (re/hasta_fa.md 2); the corner piece spans x 31,432..32,350, z 28,500..29,616
FLOOR = 800.0                           # the hall's floor (kl_fa_hasta_layer.HALL_Y)
CENTRE = (33950.0, 30400.0)             # the middle of the START rows (x 33,900..34,000, z 29,950..30,850): "inward" is from the hole to here. GUESS
_d = (CENTRE[0] - HOLE[0], CENTRE[1] - HOLE[2])
IN = (_d[0] / math.hypot(*_d), _d[1] / math.hypot(*_d))     # unit vector hole -> hall (x, z)
SIDE = (-IN[1], IN[0])                  # across the hole


def at(along, across, up):
    """A place relative to the hole: `along` cm inward, `across` cm sideways, `up` above the hall floor."""
    return (HOLE[0] + IN[0] * along + SIDE[0] * across, FLOOR + up, HOLE[2] + IN[1] * along + SIDE[1] * across)


def turn9(d):
    """ZGEOM[1] that takes local +Y to the horizontal direction d (dx, dz): kl_fa_blast.OUT (local +Y -> world +x, +Z -> +z, +X -> -y) turned about the
    world Y axis so that +x goes to d. ASSUMPTION on the layout (kl_fa_author.rot9's [third, second, first column]); d = (1, 0) gives exactly OUT."""
    n = math.hypot(*d)
    dx, dz = d[0] / n, d[1] / n
    return [-dz, 0.0, dx, dx, 0.0, dz, 0.0, -1.0, 0.0]


FACE = turn9(IN)
# role -> (spare F07 box, world position, ZGEOM[1], cluster or None, why there). Positions are GUESSes from the measured marker.
PLAN = B.collections.OrderedDict([
    ('fan', (SH + 'Activator_Shutter_LEFT', at(50, 0, 150), B.UP, None, 'anywhere: it only passes the message on (and jolts the hand-held camera)')),
    ('cloud', (SH + 'Activator_Shutters_RIGHT', at(200, 0, 7), B.UP, 'fire', '2 m inside the hole on the floor')),
    ('spray', (SH + 'Activator_Shutter_Close_LEFT', at(50, 0, 157), FACE, 'spray', 'half a metre inside the hole, blowing into the hall; the shake\'s centre')),
    ('dust s', (SH + 'Activator_Shutter_Close_RIGHT', at(50, -150, 150), FACE, 'dust', 'the south edge of the hole, head height, inward')),
    ('dust n', (SH + 'TimerShuttersOpenDif', at(50, 150, 150), FACE, 'dust', 'the north edge of the hole, head height, inward')),
    ('second', (SH + 'TimerShuttersClose', at(450, 0, 7), B.UP, 'spray', 'off by default')),
])
SHAKER = 'spray'
SOUNDED = ('cloud',)
KEEP = tuple(v[0] for v in PLAN.values()) + (TIMER,)
MESSAGE = B.MESSAGE
SECOND = 0.0                            # seconds of a second pop; 0 = none (the box stays, named by nothing)


def _active():
    return [r for r in PLAN if r != 'fan' and not (r == 'second' and SECOND <= 0)]


def dress(sc):
    """Give the boxes their controllers and values (kl_fa_blast.dress, with this plan)."""
    rk = au.node_of(sc, B.ROCKET)
    pat = {n: sc.nodes[rk]['ctrls'][au.ctrl_of(sc, rk, n)] for n in ('Explode', 'ShakeCamera')}
    sound = B.values(sc, rk, 'Explode')[B.E_SOUND]
    paths = B.clusters(sc)
    done = {r: au.node_of(sc, v[0]) for r, v in PLAN.items() if sc.resolve(R + v[0])}
    for role, k in done.items():
        cluster = PLAN[role][3]
        if role == 'fan':
            wrap = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) == 'AIDWrapper']
            if len(wrap) != 1:
                raise ValueError('%s: %d AIDWrapper' % (PLAN[role][0], len(wrap)))
            sc.nodes[k]['ctrls'] = [wrap[0], B.docucam(sc, B.TRIGGER, 'OnExplosion')]
            def fn(us):
                au.setv(sc, us, 0, [R + PLAN[r][0] for r in _active() if r in done])
                au.setv(sc, us, 1, MESSAGE)
                au.setv(sc, us, 2, 0)
            kl_fa.edit(sc, k, 0, fn)
            continue
        cl = cluster if FIRE or cluster != 'fire' else 'dust'
        sc.nodes[k]['ctrls'] = [(pat['Explode'][0], list(pat['Explode'][1]))]
        def fn(us, role=role, cl=cl):
            au.setv(sc, us, B.E_REACH, 1.0)
            au.setv(sc, us, B.E_INNER, 1.0)
            au.setv(sc, us, B.E_TINNITUS, 0.0)
            au.setv(sc, us, B.E_MESSAGE, MESSAGE)
            au.setv(sc, us, B.E_PARTICLES, paths[cl])
            au.setv(sc, us, B.E_FUSE, float(SECOND) if role == 'second' else 0.0)
            au.setv(sc, us, B.E_SOUND_FUSE, 0)
            au.setv(sc, us, B.E_SOUND, sound if SOUND and role in SOUNDED else 0)
        kl_fa.edit(sc, k, 0, fn)
        if role == SHAKER:
            sc.nodes[k]['ctrls'].append((pat['ShakeCamera'][0], list(pat['ShakeCamera'][1])))
            def fn(us):
                au.setv(sc, us, B.S_STRENGTH, B.SHAKE[0] * BLAST)
                au.setv(sc, us, B.S_MESSAGE, MESSAGE)
                au.setv(sc, us, B.S_AT_START, 0)
                au.setv(sc, us, B.S_RADIUS, B.SHAKE[1])
            kl_fa.edit(sc, k, 1, fn)
    return done


def prepare_host(S, log=print):
    """After kl_fa_hasta_layer.prepare_host(S): re-place the spare boxes at the corner and dress them. S: kl_graft.Level('F07')."""
    sc = S.prp
    if getattr(S, 'blast', None):
        return S.blast
    for role, (name, pos, m9, _cl, _why) in PLAN.items():
        k = au.node_of(sc, name)
        if sc.parent[k] != 0 or sc.end[k] - k != 1 or sc.cls(k) != 'ZBoxPrimitive':
            raise ValueError('%s is not a single top-level ZBoxPrimitive' % name)
        B.place(S, k, pos, m9)
    t = au.node_of(sc, TIMER)
    if sc.parent[t] != 0 or sc.end[t] - t != 1 or not B.has(sc, t, 'TriggerDelay2'):
        raise ValueError('%s is not a single top-level TriggerDelay2' % TIMER)
    done = dress(sc)
    gone = B.scrub(sc, [R + n for n in KEEP], but={done['fan']})
    S.blast = {'boxes': done, 'scrubbed': gone}
    log('  kl_fa_hasta_blast: %d boxes at the Capitol corner (%s) + the blast timer; %d references to their old job removed' % (len(done), ', '.join(done), sum(n for _k, n in gone)))
    return S.blast


def wire(sc, log=print):
    """After kl_fa_hasta_layer.wire(sc): the timer (delay BLAST_AT) names the fan; the AIMonitor names the timer. Idempotent."""
    node = lambda n: au.node_of(sc, n)
    done = dress(sc)
    if 'fan' not in done:
        raise KeyError('kl_fa_hasta_blast: NOT IN THE LEVEL: %s' % PLAN['fan'][0])
    fan, t, mon = R + PLAN['fan'][0], node(TIMER), node('Gameplay!AIMonitor')
    def fn(us):
        au.setv(sc, us, 0, float(BLAST_AT))
        au.setv(sc, us, 4, [fan])
    kl_fa.edit(sc, t, au.ctrl_of(sc, t, 'TriggerDelay2'), fn)
    cur = B.values(sc, mon, 'AIMonitor')[2]
    if (R + TIMER).lower() not in [p.lower() for p in cur]:
        kl_fa.edit(sc, mon, au.ctrl_of(sc, mon, 'AIMonitor'), lambda us: au.setv(sc, us, 2, cur + [R + TIMER]))
    stray = B.scrub(sc, [R + n for n in KEEP], but={done['fan'], t, mon})
    if stray:
        log('  kl_fa_hasta_blast: %d references to the boxes from elsewhere removed: %s' % (sum(n for _k, n in stray), [sc.path[k][-60:] for k, _n in stray][:4]))
    on = [r for r in _active() if r in done]
    sp = B.values(sc, node(PLAN[SHAKER][0]), 'ShakeCamera')
    far = [math.dist(PLAN[SHAKER][1], p) for p in _starts()]
    log('  kl_fa_hasta_blast: blast timer %.1f s after the round start -> fan -> %d boxes (%s); shake %.2f / %.0f (factor %.2f - %.2f at the START rows %d - %d away; Subway %.2f)' % (
        BLAST_AT, len(on), ', '.join(on), sp[B.S_STRENGTH], sp[B.S_RADIUS], B.shake_at(max(far), sp[B.S_STRENGTH], sp[B.S_RADIUS]),
        B.shake_at(min(far), sp[B.S_STRENGTH], sp[B.S_RADIUS]), min(far), max(far), B.SUBWAY_SHAKE))
    return {'boxes': done, 'on': on, 'timer': t}


def _starts():
    return [(float(x), FLOOR, float(z)) for z in (29950, 30250, 30550, 30850) for x in (33900, 34000)]


# ------------------------------------------------------------------ reading a built level back
def present(sc):
    return bool(sc.resolve(R + TIMER)) and bool(sc.resolve(R + PLAN['fan'][0])) and B.has(sc, sc.resolve(R + PLAN['fan'][0])[0], 'DocuCamControl')


def check(archive, log=print):
    """-> [faults] for a built level (an _Main.zip or a folder holding one)."""
    if os.path.isdir(archive):
        archive = next(os.path.join(archive, f) for f in os.listdir(archive) if f.lower().endswith('_main.zip'))
    sc, snd, _loc = kl_fa.load(archive)
    prm, tex = B.members(archive)
    bad = []
    node = lambda n: au.node_of(sc, n)
    pos = lambda k: tuple(kl_fa.node_values(sc, k)[2])
    if not present(sc):
        return ['no Hasta blast in %s' % archive]
    t, mon = node(TIMER), node('Gameplay!AIMonitor')
    td = B.values(sc, t, 'TriggerDelay2')
    fan = node(PLAN['fan'][0])
    mine = {(R + v[0]).lower(): r for r, v in PLAN.items()}
    if (R + TIMER).lower() not in [p.lower() for p in B.values(sc, mon, 'AIMonitor')[2]]:
        bad.append('the AIMonitor does not name the blast timer')
    if [p.lower() for p in td[4]] != [(R + PLAN['fan'][0]).lower()]:
        bad.append('the blast timer names %s, not only the fan' % td[4])
    cs = [sc.p.key(nm) for nm, _b in sc.nodes[fan]['ctrls']]
    named = set()
    if cs != ['AIDWrapper', 'DocuCamControl']:
        bad.append('the fan holds %s' % cs)
    else:
        w, d = B.values(sc, fan, 'AIDWrapper'), B.values(sc, fan, 'DocuCamControl')
        named = {p.lower() for p in w[0]}
        if w[1] != MESSAGE or w[2] or d != [B.TRIGGER, 'OnExplosion']:
            bad.append('fan values: %s %s' % (w, d))
        for p in w[0]:
            if p.lower() not in mine or mine[p.lower()] == 'fan':
                bad.append('the fan names %s' % p)
    allowed = {fan: set(mine) - {(R + PLAN['fan'][0]).lower()}, mon: {(R + TIMER).lower()}, t: {(R + PLAN['fan'][0]).lower()}}
    watch = set(mine) | {(R + TIMER).lower()}
    for k in range(1, len(sc.nodes)):
        for _h, _f, u in J.fields(sc, k):
            for s in J.strings(sc, u):
                if s.lower() in watch and s.lower() not in allowed.get(k, ()):
                    bad.append('%s names %s' % (sc.path[k][-70:], s[-45:]))
    rk = node(B.ROCKET)
    rsound = B.values(sc, rk, 'Explode')[B.E_SOUND]
    t0 = td[0]
    rows, groups, sounds = [(t0, 'fan', pos(fan), 'AIDWrapper \'%s\' + DocuCamControl OnExplosion' % MESSAGE)], B.collections.OrderedDict(), B.collections.OrderedDict()
    for role, (name, _p, _m, _cl, _why) in PLAN.items():
        if role == 'fan':
            continue
        if not sc.resolve(R + name):
            bad.append('role %s: %s is not in the level' % (role, name)); continue
        k = node(name)
        on = (R + name).lower() in named
        cs = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if cs != ['Explode'] + ['ShakeCamera'] * (role == SHAKER):
            bad.append('%s box holds %s' % (role, cs)); continue
        v = B.values(sc, k, 'Explode')
        if v[B.E_MESSAGE] != MESSAGE or v[B.E_REACH] > 1.0 or v[B.E_INNER] > 1.0 or v[B.E_TINNITUS] > 0:
            bad.append('%s box is not harmless / not on the fan\'s message: %s' % (role, v))
        if v[B.E_SOUND] not in (0, rsound):
            bad.append('%s box: sound %d is not the rocket\'s (%d)' % (role, v[B.E_SOUND], rsound))
        if role != 'second' and not on:
            bad.append('the fan does not name the %s box' % role)
        if on:
            groups.setdefault(v[B.E_PARTICLES], []).append(role)
            if v[B.E_SOUND]:
                sounds.setdefault(v[B.E_SOUND], []).append(role)
        p = pos(k)
        if math.dist(p, PLAN[role][1]) > 1.0:
            bad.append('%s box lies at %s, planned %s' % (role, p, PLAN[role][1]))
        rows.append((t0 + v[B.E_FUSE], role, p, 'Explode -> %s%s%s' % (v[B.E_PARTICLES].split('\\')[-1], ', the rocket\'s sound' if v[B.E_SOUND] else '', '' if on else ' (OFF)')))
        if role == SHAKER:
            s_ = B.values(sc, k, 'ShakeCamera')
            if s_[B.S_MESSAGE] != MESSAGE or s_[B.S_AT_START]:
                bad.append('shake values: %s' % s_)
            far = [math.dist(p, q) for q in _starts()]
            rows.append((t0, 'shake', p, 'ShakeCamera %.2f reach %.0f: factor %.2f - %.2f at the START rows %d - %d away (Subway %.2f)' % (
                s_[B.S_STRENGTH], s_[B.S_RADIUS], B.shake_at(max(far), s_[B.S_STRENGTH], s_[B.S_RADIUS]), B.shake_at(min(far), s_[B.S_STRENGTH], s_[B.S_RADIUS]), min(far), max(far), B.SUBWAY_SHAKE)))
    for path, who in groups.items():
        lines, b = B.cluster_parts(sc, path, prm, tex)
        bad += b
        short = path.split('.zip\\')[-1]
        pool = next((n for _nm, (sub, n, _w) in B.CLUSTER.items() if path.lower().endswith(sub.lower())), None)
        if pool is not None and len(who) > pool:
            bad.append('%s is asked for %d times at once, its clone group has %d' % (short, len(who), pool))
        log('  particle group of %s:' % ', '.join(who))
        for l in lines:
            log('    ' + l)
    for o, who in sounds.items():
        if not (snd is not None and 0 < o < len(snd)):
            bad.append('sound %d of %s is outside the .SND' % (o, who))
        try:
            import kl_snd
            log('  sound %d %s (%s)' % (o, kl_snd.Snd('dd', snd).name(o).decode('latin1'), ', '.join(who)))
        except Exception:
            pass
    log('  timeline, seconds from the round start:')
    for t_, role, p, what in sorted(rows, key=lambda r: r[0]):
        log('    %5.1f  %-8s (%d %d %d) %s' % (t_, role, *p, what))
    return bad


def selftest(log=print):
    import kl_graft
    S = kl_graft.Level('F07')
    sc = S.prp
    bad = []
    for role, (name, pos, m9, cl, _w) in PLAN.items():
        k = sc.resolve(R + name)
        if len(k) != 1 or sc.parent[k[0]] != 0 or sc.end[k[0]] - k[0] != 1 or sc.cls(k[0]) != 'ZBoxPrimitive':
            bad.append('%s: not a single top-level ZBoxPrimitive' % name)
        d = [m9[0:3], m9[3:6], m9[6:9]]
        cross = lambda a, b: [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
        z, y, x = d
        if max(abs(a - b) for a, b in zip(cross(x, y), z)) > 1e-6:
            bad.append('%s: matrix is not a proper rotation' % role)
    if any(abs(a - b) > 1e-9 for a, b in zip(turn9((1.0, 0.0)), B.OUT)):
        bad.append('turn9((1, 0)) is not kl_fa_blast.OUT')
    t = sc.resolve(R + TIMER)
    if len(t) != 1 or not B.has(sc, t[0], 'TriggerDelay2'):
        bad.append('timer %s' % TIMER)
    if bad == []:
        log('  paths: %s' % B.clusters(sc))
    log('inward (%.3f, %.3f); spray matrix %s; ' % (IN[0], IN[1], [round(x, 3) for x in FACE]) + ('SELFTEST FAIL: %s' % bad if bad else 'SELFTEST PASS'))
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['selftest']:
        sys.exit(1 if selftest() else 0)
    if len(a) == 2 and a[0] == 'check':
        bad = check(a[1])
        for b in bad:
            print('  FAIL: ' + b)
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
        sys.exit(1 if bad else 0)
    print(__doc__)
