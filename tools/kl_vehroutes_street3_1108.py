r"""kl_vehroutes_street3_1108.py - DM01B (Hot Coffee II, slot F03): follow-up to the LIVE street2 van route (kl_vehroutes_street2_1108): WIDER TURNS and a SLOWER VAN over them.
Written 2026-11-09, OFFLINE: reads the live DM01B zip, writes NEW files (never the live ones). Pinned on the street2 files (LIVE_MD5); install ONE (it replaces street2's drive keys only).

WHY (review of the live route): both quarter turns were too tight. Arrival arc radius 407, departure 400, at 108..116 units per key (one key = one frame at 30 fps; if a unit is a cm that is
about 125 km/h): a lateral acceleration of v^2/r = 30 u/frame^2 (about 300 m/s^2) while ~500 viewers on the street can see the van.

WHAT THIS DOES (only the van's drive keys; the .prp, .HVK, nav, bots geometry, start pose and crash keys are untouched, key count and key 0 unchanged)
  1. ARRIVAL: the start pocket (-8000, 30500) is kept; the turn becomes ONE quarter circle of radius R_ARR = 31907 - 30500 = 1407 (the most the pocket's z allows: the arc starts at the
     pocket at once, tangent north, and meets the street lane z 31907 heading east), centre (-6593, 30500); then straight east to the stop (4454, 31907).
  2. DEPARTURE: the street is left earlier, at x = 17400 - R_DEP = 15893, and the quarter turn south has radius R_DEP = 31907 - 30400 = 1507 and ends at the old end (17400, 30400).
  3. SPEED: each leg gets a speed-vs-distance profile instead of the old per-key steps scaled: start accel, brake into the arc, constant arc speed VC, accel out, cap 116 (the stock vans'
     peak), brake at the end. The key count of each leg is FIXED (arrival keys 0..155 = frames 50..205 of Activate_Enter, departure keys 155..390), so the arc speed VC is solved as the
     smallest one the leg's key budget allows (bisection); a leg that needs fewer keys than it has HOLDS the surplus keys at its start pocket (arrival) / its end pocket (departure), where
     nobody can see or stand. The arrival budget is the tight one: 155 keys for 13250 units, so its arc speed cannot go below 65 u/frame (lateral accel v^2/r 3.0 u/frame^2, 11 x
     gentler than before; the departure arc runs at 39.8, 1.05 u/frame^2; a calmer arc needs more keys = a re-timed Activate_Enter, not done).
  4. Rotation keys: heading of the path at each frame's position key (sway kept), exactly as street2; frames at the held start keep the live rotation (no 0.1 degree drift of the start pose).
  5. CRASH KEYS (>= the drive) are LEFT AS THEY ARE: the four crash animations (Activate_Crash_01..04, frames 500/600/650/750) start at absolute positions 3501 / 4458 / 4971 / 6594 along
     the street (arrive, stop, leave, leave), i.e. relative to the stop, and which one plays follows the van's state, not its position; no run-time hook moves the wreck to the van's
     death place. A van shot while still in a pocket or on an arc therefore jumps to the crash start (same as before this stage). BENCH ITEM: shoot the van on the arrival arc, at the stop and
     on the departure arc and note where the wreck appears.
Proofs (tool `check`): hull check of every key, the street2 walk / nav / flood proofs (unchanged geometry), STRICT viewshed (viewshed2: 200-unit viewer blocks over every reachable floor cell,
range 30000, eye +300, point +250, EVERY key), start and end seen by nobody.
usage: python kl_vehroutes_street3_1108.py stage <live DM01B dir> <out dir>      python kl_vehroutes_street3_1108.py check <F03_Main.zip> [<live F03_Main.zip>]"""
import hashlib, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F, kl_graft, kl_gms
import kl_vehroutes_street_1108 as S
import kl_vehroutes_street2_1108 as T

# the live street2 files (pinned: another pass over them means re-stage)
LIVE_MD5 = {'F03_Main.zip': '778b075c7e0d1e92185ea250bca0d248', 'F03_Main.bots.zip': 'dccc9250c6e05b3f874630eb76aed8c1',
            'F03_Main.bots.base.md5': '6616525ad3caab8ce2029096cdb2f02b'}
TAG = '.before-vehroutes1108street3'
MIN_FREE_MB = T.MIN_FREE_MB
WAIT = T.WAIT_W[0]                     # (-8000, 30500)
LANE_Z = 31907.0
STOP_X = T.STOP_KEY_X                  # 4454
END = T.END_E                          # (17400, 30400)
R_ARR = LANE_Z - WAIT[1]               # 1407: the arc starts at the pocket and ends on the lane
R_DEP = LANE_Z - END[1]                # 1507: ends at the east pocket
CAP = 116.0                            # stock peak per key
B_IN_ARR, A_OUT_ARR, B_END_ARR = 1.5, 2.0, 2.4        # units / frame^2 (1 u/f^2 = 9 m/s^2 if a unit is a cm)
A_START_DEP, B_IN_DEP, A_OUT_DEP, B_END_DEP = 1.0, 1.5, 1.5, 4.0
V0_DEP = 2.0                           # speed at the first step of the departure (the arrival starts at its arc speed: out of sight in the pocket)
VC_MIN = 20.0


def md5(p):
    return S.md5(p)


# ------------------------------------------------------------------ paths
def arrival_path():
    c = (WAIT[0] + R_ARR, WAIT[1])                                  # north -> east about a centre east of the pocket's straight
    return T.Path([WAIT] + T.arc(c, R_ARR, 180.0, 90.0, 48)[1:] + [(STOP_X, LANE_Z)])


def departure_path():
    xa = END[0] - R_DEP
    c = (xa, LANE_Z - R_DEP)                                         # east -> south about a centre south of the lane
    return T.Path([(STOP_X, LANE_Z), (xa, LANE_Z)] + T.arc(c, R_DEP, 90.0, 0.0, 48)[1:] + [END])


# ------------------------------------------------------------------ speed profile
def zones(L, s0, s1, vc, v0, a_s, b_in, a_out):
    """Speed limits (functions of the distance s) of one leg: start accel, brake into the arc [s0, s1], arc speed, accel out."""
    return [lambda s: math.sqrt(v0 * v0 + 2 * a_s * s),
            lambda s: math.sqrt(vc * vc + 2 * b_in * (s0 - s)) if s < s0 else 1e9,
            lambda s: vc if s0 <= s <= s1 else 1e9,
            lambda s: math.sqrt(vc * vc + 2 * a_out * (s - s1)) if s > s1 else 1e9]


def profile(L, cons, vpk, b_end, vend=1.0):
    """Cumulative distances (len = keys + 1) of a leg: each step is the lowest of the limits at its start, the cap and the end brake; the last lands on L exactly."""
    s, out = 0.0, [0.0]
    while L - s > 1e-6 and len(out) < 4000:
        v = vpk
        for f in cons:
            v = min(v, f(s))
        v = min(v, math.sqrt(2 * b_end * (L - s)) + vend)
        s = L if L - s <= v else s + v
        out.append(s)
    out[-1] = L
    return out


def solve_arrival(A, nsteps):
    """-> (vc, distances of the leg's nsteps + 1 keys). Smallest arc speed whose profile fits in nsteps (the surplus holds at the pocket)."""
    arcL = R_ARR * math.pi / 2

    def keys(vc):
        return len(profile(A.L, zones(A.L, 0.0, arcL, vc, vc, A_OUT_ARR, B_IN_ARR, A_OUT_ARR), CAP, B_END_ARR)) - 1
    if keys(CAP) > nsteps:
        raise ValueError('the arrival cannot be driven in %d keys even at arc speed %g' % (nsteps, CAP))
    lo, hi = VC_MIN, CAP
    for _ in range(40):
        m = (lo + hi) / 2
        if keys(m) > nsteps:
            lo = m
        else:
            hi = m
    vc = hi
    d = profile(A.L, zones(A.L, 0.0, arcL, vc, vc, A_OUT_ARR, B_IN_ARR, A_OUT_ARR), CAP, B_END_ARR)
    d = [0.0] * (nsteps + 1 - len(d)) + d                           # surplus keys: held at the start
    return vc, d


def solve_departure(D, nsteps):
    """-> (vc, peak, distances of nsteps + 1 keys). Smallest arc speed vc whose profile at the cap fits in nsteps, then the smallest peak that still fits (the surplus holds at the end pocket)."""
    s0 = D.L - R_DEP * math.pi / 2

    def keys(vc, vpk):
        return len(profile(D.L, zones(D.L, s0, D.L, vc, V0_DEP, A_START_DEP, B_IN_DEP, A_OUT_DEP), vpk, B_END_DEP)) - 1
    if keys(CAP - 1, CAP) > nsteps:
        raise ValueError('the departure cannot be driven in %d keys (needs %d at arc speed %g)' % (nsteps, keys(CAP - 1, CAP), CAP - 1))
    lo, hi = VC_MIN, CAP - 1
    for _ in range(40):
        m = (lo + hi) / 2
        if keys(m, CAP) > nsteps:
            lo = m
        else:
            hi = m
    vc = hi
    lo, hi = vc + 1.0, CAP
    for _ in range(40):
        m = (lo + hi) / 2
        if keys(vc, m) > nsteps:
            lo = m
        else:
            hi = m
    d = profile(D.L, zones(D.L, s0, D.L, vc, V0_DEP, A_START_DEP, B_IN_DEP, A_OUT_DEP), hi, B_END_DEP)
    d = d + [D.L] * (nsteps + 1 - len(d))                           # surplus keys: held at the end
    return vc, hi, d


def relay_keys(K):
    """-> (positions, rotations, report): the live drive's keys re-laid on the two wider paths. Arrival keys 0..a (a = the stop key), departure a..cut-1, crash keys untouched."""
    cut = K.drive()
    a = next(i for i in range(cut) if K.pos[i][0] >= STOP_X)
    A, D = arrival_path(), departure_path()
    vc_a, da = solve_arrival(A, a)
    vc_d, vp_d, dd = solve_departure(D, cut - 1 - a)
    pos, yaw = list(K.pos), {}
    for i in range(cut):
        (px, pz), h = A.at(da[i]) if i < a else D.at(dd[i - a])
        pos[i] = (px, K.pos[i][1], pz)
        yaw[i] = h
    pos[0] = K.pos[0]
    rot = list(K.rot)
    use = {}                                                         # rot key -> the headings of every drive frame that plays it (the rot table is sparser than the frames)
    for f in range(len(K.f2p)):
        i = K.f2p[f]
        if i < cut and not (i < a and da[i] == 0.0):                 # frames held at the start keep the live rotation (pose untouched)
            use.setdefault(K.f2r[f], []).append(yaw[i])
    for r, hs in use.items():
        h0 = hs[0]
        mean = h0 + sum(((h - h0 + 180.0) % 360.0) - 180.0 for h in hs) / len(hs)      # mean heading over the frames the key serves (not the last one: it jerked by up to 5.6 deg/frame)
        delta = (mean - K.yaw(K.rot[r]) + 180.0) % 360.0 - 180.0
        if abs(delta) > 0.05:
            rot[r] = K.turned(K.rot[r], delta)
    rep = dict(stop_key=a, vc_arr=vc_a, vpeak_dep=vp_d, vc_dep=vc_d, hold_arr=sum(1 for x in da if x == 0.0) - 1,
               hold_dep=sum(1 for x in dd if x == D.L) - 1, lat_arr=vc_a ** 2 / R_ARR, lat_dep=vc_d ** 2 / R_DEP,
               len_arr=A.L, len_dep=D.L)
    return pos, rot, rep


# ------------------------------------------------------------------ build
def build(src, log=print):
    """live street2 zip -> ({member: bytes} of the whole archive in order, report)."""
    B = F.Built(src)
    if B.sc.p.serialize() != B.files[B.ext['.prp']]:
        raise ValueError('the .prp does not round-trip (stop: nothing was written)')
    orig_gms = kl_gms.unpack(B.files[B.ext['.gms']])
    if B.scene.write()[0] != orig_gms:
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    vk, K = S.van_keys(B)
    if abs(K.pos[0][0] - WAIT[0]) > 1 or abs(K.pos[0][2] - WAIT[1]) > 1 or abs(K.pos[K.drive() - 1][0] - END[0]) > 1:
        raise ValueError('the live zip is not the street2 route (key 0 %r, last drive key %r): wrong input' % (K.pos[0], K.pos[K.drive() - 1]))
    npos, nrot, rep = relay_keys(K)
    head = bytearray(B.scene.head)
    for i, p in enumerate(npos):
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
    for i, q in enumerate(nrot):
        struct.pack_into('<4h', head, K.offs[2] + 8 * i, *q)
    B.scene.head = bytes(head)
    gms, buf = B.scene.write()
    out = {B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf}
    members = [(n, out[n] if n in out else B.files[n]) for n in B.order]
    steps = [math.dist(npos[i], npos[i - 1]) for i in range(1, K.drive())]
    log('kl_vehroutes_street3_1108: arrival R %d (len %d) arc speed %.1f u/frame (lateral %.2f u/f2), %d start holds; departure R %d (len %d) arc %.1f (lateral %.2f u/f2), peak %.1f, %d end holds; '
        'max step %.1f (live %.1f)' % (R_ARR, rep['len_arr'], rep['vc_arr'], rep['lat_arr'], rep['hold_arr'], R_DEP, rep['len_dep'], rep['vc_dep'], rep['lat_dep'], rep['vpeak_dep'],
                                      rep['hold_dep'], max(steps), max(math.dist(K.pos[i], K.pos[i - 1]) for i in range(1, K.drive()))))
    rep['max_step'] = max(steps)
    return members, rep


def write(src, dst, log=print):
    members, rep = build(src, log)
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    return rep


# ------------------------------------------------------------------ checks
VIEW_RANGE = 30000.0
BLOCK = 200.0
EYE, POINT = 300.0, 250.0


def viewers(zp):
    """Every reachable floor cell of the walk flood, one viewer per BLOCK x BLOCK x 150 block (the first cell found)."""
    import kl_route as R
    cost, _r = T.flood(zp)
    seen = {}
    for i, j, y in cost:
        x, z = (i + .5) * R.CELL, (j + .5) * R.CELL
        seen.setdefault((int(x // BLOCK), int(z // BLOCK), int(y // 150)), (x, float(y), z))
    return list(seen.values())


def viewshed2(zp, log=print, full_below=40):
    """STRICT viewshed of the van on EVERY drive key (not a sample): viewers = every reachable floor block (200 units), range 30000, eye +300, point +250. Two occluder sets as in
    street2 (SOLID: every drawn triangle but fog / glow / sky / the van; SOFT: also without bushes, trees, fences, glass = the stricter reading). Early exit: a key stops at its first
    seeing viewer (so it is reported as 'seen'); only keys that nobody sees get the whole viewer list tested, and for those, and for the first / last `full_below` unique keys, the
    exact count is kept. -> dict(viewers, keys=[(key, x, z, near, solid, soft)]) with solid / soft = viewers seeing (exact when <= full_below else 1 + 'seen')."""
    import numpy as np, kl_arrival_1107 as A
    vs = viewers(zp)
    B = F.Built(zp)
    _k, K = S.van_keys(B)
    cut = K.drive()
    lo = np.array([-10000.0, -1500.0, 28500.0])
    hi = np.array([18500.0, 4500.0, 34500.0])
    tr, ow, nm = A.geom(zp, region=(lo, hi), log=lambda *a: None)
    tr, ow = np.asarray(tr, np.float64), np.asarray(ow)
    bad = [i for i, x in enumerate(nm) if any(w in x for w in T.SKIP)]
    ok = np.isfinite(tr).all(axis=(1, 2)) & (np.abs(tr).max(axis=(1, 2)) < 2e5) & ~np.isin(ow, bad)
    tr, ow = tr[ok], ow[ok]
    soft = [i for i, x in enumerate(nm) if any(w in x for w in T.SOFT)]
    keep = ~np.isin(ow, soft)
    meshes = (A.Mesh(tr.astype(np.float32), ow, nm), A.Mesh(tr[keep].astype(np.float32), ow[keep], nm))
    uniq, order = [], {}
    for i in range(cut):
        p = K.pos[i]
        if p not in order:
            order[p] = len(uniq)
            uniq.append(p)
    res = {}
    for n, p in enumerate(uniq):
        q = (p[0], p[1] + POINT, p[2])
        near = sorted((v for v in vs if math.dist(v, q) < VIEW_RANGE), key=lambda v: math.dist(v, q))
        exact = n < full_below or n >= len(uniq) - full_below
        row = []
        for M in meshes:
            c = 0
            for v in near:
                if not A.seg_hits(M, (v[0], v[1] + EYE, v[2]), q):
                    c += 1
                    if not exact:
                        break
            row.append(c)
        res[p] = (len(near),) + tuple(row)
        if n % 25 == 0:
            log('    viewshed2 key position %d / %d' % (n, len(uniq)))
    keys = [(i, K.pos[i][0], K.pos[i][2]) + res[K.pos[i]] for i in range(cut)]
    return dict(viewers=len(vs), keys=keys)


def print_view(vr, log=print):
    log('  8 STRICT viewshed: %d viewers (200-unit blocks of every reachable floor cell), range %d, eye +%d, point +%d, every key (solid / soft = viewers seeing; 1 = at least one)' % (
        vr['viewers'], VIEW_RANGE, EYE, POINT))
    last = None
    for key, x, z, near, a, b in vr['keys']:
        row = (a > 0, b > 0)
        if last is None or row != last[0] or key == len(vr['keys']) - 1:
            log('    key %-3d (%6d,%6d) within %5d solid %4d soft %4d' % (key, x, z, near, a, b))
        last = (row, key)


def profile_audit(zp, live, log=print):
    """The key table against the live one: only drive keys move, key 0 / crash keys / key count unchanged, steps and heading rates, lateral acceleration on both arcs."""
    bad = []
    B, K = S.van_keys(F.Built(zp))
    B0, K0 = S.van_keys(F.Built(live))
    cut = K.drive()
    if cut != K0.drive() or K.npos != K0.npos or K.nrot != K0.nrot or K.f2p != K0.f2p or K.f2r != K0.f2r:
        bad.append('key counts / frame tables differ from live')
    if K.pos[0] != K0.pos[0]:
        bad.append('key 0 moved')
    if K.pos[cut:] != K0.pos[cut:]:
        bad.append('crash keys changed')
    if any(abs(p[1] - q[1]) > 1e-3 for p, q in zip(K.pos[:cut], K0.pos[:cut])):
        bad.append('a key height changed')
    st = [math.dist(K.pos[i], K.pos[i - 1]) for i in range(1, cut)]
    if max(st) > CAP + 0.5:
        bad.append('step %.1f over the cap' % max(st))
    # heading rate and radius over the arcs (three-point circle radius at every 4th key)
    worst = {}
    for lab, lo, hi in (('arrival', 0, 160), ('departure', 340, cut)):
        rr = []
        for i in range(lo + 4, hi - 4, 2):
            a, b, c = K.pos[i - 4], K.pos[i], K.pos[i + 4]
            if a == b or b == c:
                continue
            ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
            area = abs((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0])) / 2
            if area > 1e-6:
                rr.append((ab * bc * ca / (4 * area), i))
        worst[lab] = min(rr) if rr else None
        yr = max(abs(((K.yaw(K.rot[K.f2r[f]]) - K.yaw(K.rot[K.f2r[f - 1]]) + 180) % 360) - 180) for f in range(1, len(K.f2p)) if K.f2p[f] < cut and K.f2p[f - 1] < cut and lo <= K.f2p[f] <= hi)
        log('  7 %s: tightest 3-point radius %.0f at key %s, max yaw change %.2f deg/frame' % (lab, worst[lab][0], worst[lab][1], yr))
        if worst[lab][0] < 1000:
            bad.append('%s radius %.0f < 1000' % (lab, worst[lab][0]))
        if yr > 6.0:
            bad.append('%s yaw rate %.1f deg/frame' % (lab, yr))
    log('  7 steps: max %.1f (cap %g), live max %.1f; arrival keys 0..%d, steps at arc keys 0..45: %s' % (
        max(st), CAP, max(math.dist(K0.pos[i], K0.pos[i - 1]) for i in range(1, cut)), next(i for i in range(cut) if K.pos[i][0] >= STOP_X),
        ' '.join('%d' % round(x) for x in st[:45:3])))
    return bad


def check(zp, live=None, log=print, view=True):
    """Offline proofs on a staged zip -> list of problems ([] = all pass): hull check of the drive and crash keys, street2's walk / nav / flood proofs (no geometry changed here),
    the key-table audit against live, and the strict viewshed (start and end seen by nobody)."""
    import kl_vehroutes_1108 as V
    bad = []
    n = V.check(zp, log, True)
    log('  1 render check of the drive: %s close samples' % n)
    if n:
        bad.append('van render check: %s close samples' % n)
    bad += T.check(zp, live, log, view=False)
    if live:
        bad += profile_audit(zp, live, log)
    if view:
        vr = viewshed2(zp, log)
        print_view(vr, log)
        r = vr['keys']
        for lab, row in (('start', r[0]), ('end', r[-1])):
            if row[4] or row[5]:
                bad.append('the van %s (%d,%d) is seen by %d (solid) / %d (soft) viewers' % (lab, row[1], row[2], row[4], row[5]))
    log('PROBLEMS: %d' % len(bad))
    for b in bad:
        log('  ' + b)
    return bad


def stage(live_dir, out, log=print):
    import kl_botsonline
    src = os.path.join(live_dir, 'F03_Main.zip')
    for nm, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, nm)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (nm, h))
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, 'F03_Main.zip')
    write(src, final, log)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F03_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F03_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = [(nm, LIVE_MD5[nm], md5(os.path.join(out, nm))) for nm in LIVE_MD5]
    t = open(os.path.join(HERE, 'kl_vehroutes_street2_install_tmpl.py'), encoding='utf-8').read()      # the kit script template (shared with street2); FILES + the tag are filled in here
    nl = chr(10)
    i, j = t.index('FILES = ['), t.index(nl + ']' + nl) + 3
    t = t[:i] + 'FILES = [   # name, live md5 before, staged md5 after' + nl + nl.join('    (%r, %r, %r),' % f for f in files) + nl + ']' + nl + t[j:]
    t = t.replace('.before-vehroutes1108street2', TAG)
    t = t.replace('DM01B VAN ON THE MAIN STREET + OPEN PLANTER + NAV BRIDGE 1108 (tools/kl_vehroutes_street2_1108.py; replaces tools/kl_vehroutes_street_1108.py and tools/kl_vehroutes_1108.py: install ONE)',
                  'DM01B VAN WIDER TURNS + SLOWER ARCS 1108 (tools/kl_vehroutes_street3_1108.py; follow-up of the LIVE street2 route: it changes the van drive keys only, the undo returns the street2 files)')
    if 'street2' in t.split('FILES = [')[0].split('GAME =')[1] or TAG not in t or 'LIVE_ZIP_MD5 = FILES[0][1]' not in t:
        raise ValueError('the install template was not re-tagged / still carries a hard-coded pin')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    open(os.path.join(out, 'INSTALL DM01B vehroutes street3 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%%~dp0install.py" --min-free-mb %d' % MIN_FREE_MB + cr + nl + 'pause' + cr + nl)
    open(os.path.join(out, 'UNDO DM01B vehroutes street3 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py" --undo' + cr + nl + 'pause' + cr + nl)
    for f in files:
        log('  %-24s %s -> %s' % f)
    return files


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3:
        stage(a[1], a[2])
    elif a[:1] == ['check'] and len(a) in (2, 3):
        sys.exit(1 if check(a[1], a[2] if len(a) == 3 else None) else 0)
    else:
        print(__doc__)
        sys.exit(2)
