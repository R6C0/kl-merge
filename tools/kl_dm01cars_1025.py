"""kl_dm01cars_1025.py - DM01 (Hot Coffee) stage B, 2026-10-25: three police cars drive in and six SWAT men get out (re/dm01_cars_1025.md, option C).

Owner: "the agents or swat should come in cars and get out".  Input = stage A (kl_dm01squads_1025.py, md5 11c874cb...).

What it grafts from Dog Days' F03 (Backside police cars, nothing is copied whole):
  KL_Cars!\\Cars        the F03 MatPosAnimProxy group 12578 with the three V_Santana_CopCar groups (bodies, wheels, doors, shadow planes,
                       Pos_Police helpers).  Dropped: particle emitters, lights, GlassShatter groups, KillBox, CoverBoxCar_05; controllers
                       ShotActivate / LightFlicker / VertAnim / Audio_*.  The cars are animated (MatPosAnim), not driven: no collision.
  KL_Cars!Cop_1..3     the F03 squads 30_SWAT01..03 (MiniCutsceneRout + PosObject + modifier), game type eAllTypes, f3 = 0 (unspawned), a
                       Defend rout with two posts, DM01's own Wave_3 actor forms (anmcol Mercenary_04) named SWAT#01 / SWAT#02.
  KL_Cars!Clock        'Arrive' (TriggerDelay2: the 3 MiniCuts, the cars' AIDWrapper 'Activate_Anim', FrontMall Hunt routs, the radio) and
                       'Backstop' (BACKSTOP_S s after the round start, AIMonitor start list); MercsClosingIn names Arrive too.
  .ANM                 the 18 F03_Police clips merged into collection Mercenary_04 (kl_anm.merge on a one-collection stand-in).
  .buf head            the KEYS tracks of the 26 animated nodes copied; the three bodies' world position keys scaled about the stop.
The F03 lane is 135 m long on F03's map.  Here: Pos' = E + S * (Pos - E1) (uniform, so headings stay): E1 = car 1's last key in F03, E = STOP.

    python kl_dm01cars_1025.py cars <in.zip> <out.zip>
"""
import collections, hashlib, json, math, os, shutil, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene, kl_light
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_fa_climb2 as C2
import kl_fa_cover as CV
import kl_interact_graft as IG
import kl_octree as O
import kl_old_waves as KOW
import kl_prmgraph as G
import kl_texmat as T
import kl_prpjoin as J
import kl_dm02_assault_1025 as AS
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55           # engine-proven
PIN = '11c874cb138db1a30ea63e9e9aeb0f58'        # stage A output (dm01squads_1025a)
DON = 'F03'
TOP, CARS, CLOCK = 'KL_Cars!', 'Cars', 'KL_Cars!Clock'
COP = 'KL_Cars!Cop_%d'
OLD_PROXY = BS.join(['ROOT', 'Animation/F03/F03_Anim_PoliceCars.zip', 'Animation_Backside_Policecars_01'])
NEW_PROXY = R + TOP + BS + CARS
PROXY_K, KEEP_LO, KEEP_HI = 12578, 12578, 13104         # F03 .prp node numbers: the proxy, kept range [lo, hi)
BODIES = (12579, 12754, 12929)
DROP_CLASS = ('ZParticleEmitter', 'ZSPOTLIGHT', 'ZOMNILIGHT')
DROP_NAME = ('KillBox', 'CoverBoxCar_05')
DROP_PREFIX = 'FX0700_ALL_GlassShatter'
DROP_CTRL = ('ShotActivate', 'LightFlicker', 'VertAnim', 'Audio_AttachToGeom', 'Audio_PlaySound', 'KillBox')
SWAT = {1: dict(top=298, mc=299, mod=302), 2: dict(top=319, mc=320, mod=323), 3: dict(top=183, mc=184, mod=187)}      # F03 nodes
OLD_SWAT = R + 'Gameplay!30_SWAT%02d'
E1 = None                                       # set from the donor: car 1's last real key
STOP = (6000.0, 26250.0)                        # where car 1 stops (x, z); the lane search (work/lane1.py) found it: ground, unblocked, on the main nav part
SCALE = 0.35                                    # lane scale (the F03 lane is 135 m, ours 47 m)
# Defend posts per squad (work/cells1.py: each seen from 6 of 8 route points, >= 250 from the stops, main part, clearance >= 90, >= 300 apart)
CELLS = {1: [(6200.0, 0.0, 26400.0), (5900.0, 0.0, 26500.0)],
         2: [(5600.0, 0.0, 26800.0), (6200.0, 0.0, 27000.0)],
         3: [(6000.0, 0.0, 27200.0), (5600.0, 0.0, 27200.0)]}
ARRIVE_S, BACKSTOP_S = 0.3, 8.0                 # Arrive's own delay; the round-start backstop (GUESS: the crew reaches x 2700 at ~15 s; cars need ~9 s)
KEYS_BODY_POS = 5                               # the body's position track is the sixth of the six KEYS offsets (read: 220 float triples, the last is 0)
FACE = (0.0, 1.0)
ENEMY_TOP = 'AI_Enemies!'
LANE_Y = (-50.0, 600.0)


def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


def md5(b):
    return hashlib.md5(b).hexdigest()


# ------------------------------------------------------------------ the lane
def body_track(d, k):
    """(offset, [position triples without the trailing zero key]) of car body k in the donor head."""
    import kl_graft as KG
    (_p, offs), = KG.keys_tracks(d.ent(k).raw)
    ev = sorted({o for e in d.ents if e.raw for _p2, oo in KG.keys_tracks(e.raw) for o in oo} | {len(d.head)})
    o = offs[KEYS_BODY_POS]
    nxt = next(x for x in ev if x > o)
    pts = [struct.unpack_from('<3f', d.head, o + 12 * i) for i in range((nxt - o) // 12)]
    while pts and pts[-1] == (0.0, 0.0, 0.0):
        pts.pop()
    return o, pts


def lane_map(e1):
    """The map of a donor key (x, y, z) -> ours; uniform scaling about the stop keeps the headings."""
    return lambda p: (STOP[0] + SCALE * (p[0] - e1[0]), p[1], STOP[1] + SCALE * (p[2] - e1[2]))


def setpos(M, nd, pos):
    M.set(nd, None, {'ZGEOM[2]': [float(v) for v in pos]})
    nd.trans = struct.pack('<3f', *pos) + nd.trans[12:]
    nd.pos = tuple(pos)


# ------------------------------------------------------------------ the car clone
def car_nodes(M, d, topg):
    """-> (proxy Node, {donor k: Node}) cloned from the F03 subtree with the drops and the ctrl filters."""
    sc = d.sc
    rn = lambda s: (NEW_PROXY + s[len(OLD_PROXY):]) if s.lower().startswith(OLD_PROXY.lower()) else s
    gone, byk = set(), {}
    for k in range(KEEP_LO, KEEP_HI):
        par = sc.parent[k]
        if par in gone or sc.cls(k) in DROP_CLASS or sc.names[k] in DROP_NAME or sc.names[k].startswith(DROP_PREFIX):
            gone.add(k)
            continue
        nd = IG.clone(M, d, k, CARS if k == PROXY_K else sc.names[k], rn)
        nd.ctrls = [c for c in nd.ctrls if M.p.key(c[0]) not in DROP_CTRL]
        byk[k] = nd
        (byk[par] if par in byk else topg).add(nd)
    kept = {NEW_PROXY.lower() + (sc.path[k][len(OLD_PROXY):] if k != PROXY_K else '').lower() for k in byk}
    cut = IG.list_filter(M, byk[PROXY_K], 'MatPosAnimProxy', 3, lambda s: s.lower() in kept)
    return byk, cut, len(gone)


def sget(M, tok):
    return M.p.keys[struct.unpack('<I', tok[1])[0]]


# ------------------------------------------------------------------ the squads
def squads_nodes(M, B, d, byk, clock, go_paths, CELLS=CELLS):
    sc = B.sc
    node = lambda path: sc.resolve(path)[0]
    w3 = one(sc, KOW_WAVE3)
    acts3 = [k for k in range(w3, sc.end[w3]) if sc.cls(k) == 'ZFFActor']
    if len(acts3) < 2:
        raise ValueError('Wave_3 shape')
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    tops, mcs = [], []
    for n in (1, 2, 3):
        S = SWAT[n]
        name = COP % n
        me = R + name
        rn = lambda s, n=n, me=me: (me + s[len(OLD_SWAT % n):]) if s.lower().startswith((OLD_SWAT % n).lower()) else (
            NEW_PROXY + s[len(OLD_PROXY):] if s.lower().startswith(OLD_PROXY.lower()) else s)
        top = FED.clone_built(M, B, w3, name)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        # f3 = 0: unspawned until its first rout (the MiniCut) is listed by Arrive; game type eAllTypes (F03's was eFragileAllianceUCC); lists empty
        M.set(top, 'ZSquadScript', {0: 'eUnleashed', 1: 'eAllTypes', 3: 0, **{j: [] for j in range(4, 19)}})
        mc = IG.clone(M, d, S['mc'], d.sc.names[S['mc']], rn)
        top.add(mc)
        for k in range(S['mc'] + 1, d.sc.end[S['mc']]):
            if d.sc.parent[k] != S['mc']:
                continue
            mc.add(IG.clone(M, d, k, d.sc.names[k], rn))
        mod = IG.clone(M, d, S['mod'], d.sc.names[S['mod']], rn)
        top.add(mod)
        dfn = top.add(M.clone('F07', sq2(KOW.FORM), '20_DefendBehaviour_a_01'))
        M.place(dfn, (0.0, 0.0, 0.0))
        refs = []
        for j, cell in enumerate(CELLS[n]):
            pp = dfn.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, cell)
            refs.append(me + BS + '20_DefendBehaviour_a_01' + BS + 'Pos#%02d' % (j + 1))
        # keep F03's field 2 = 0; gates (field 7) cleared: nothing here feeds them (GUESS: stock F03 fills them from its own gate chain)
        M.set(dfn, 'DefendBehaviourRout', {0: '', 1: refs, 2: 0, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        for j, cell in enumerate(CELLS[n]):
            g = top.add(FED.clone_built(M, B, sc.parent[acts3[j % 2]], 'SWAT#%02d' % (j + 1)))
            M.place(g, cell, KB.rot9(*FACE))
            a = g.add(FED.clone_built(M, B, acts3[j % 2], 'Ground'))
        tops.append(top)
        mcs.append(me + BS + mc.name)
    return tops, mcs


KOW_WAVE3 = 'OldWaves!Wave_3'


# ------------------------------------------------------------------ the anm
def anm_pass(dd_raw, donor, src_col='Swat_02', tgt_col='Mercenary_04', pre='/Level_Specific/F03/Situations/F03_Police'):
    import kl_anm
    dd = kl_anm.Anm(dd_raw, 'dd')
    src = donor.col(src_col)
    lists = src.lists()
    slots = [s for s, n in enumerate(donor.slots) if n.startswith(pre) and s in lists]
    pool, table = [], [-1] * len(donor.slots)
    for s in slots:
        table[s] = len(pool)
        pool += lists[s]
    while table and table[-1] < 0:
        table.pop()
    dm = kl_anm.Anm(donor.save(), 'dd')
    dm.cols = [kl_anm.Collection(kl_anm.PREFIX + 'KLCarTmp', [], pool, table)]
    out = kl_anm.merge(dd, dm, {'KLCarTmp': 'KLCarTmp'})
    tmp = out.cols.pop()
    tl = tmp.lists()
    tgt = out.col(tgt_col)
    n0 = len(dd.clips)
    for s in slots:
        sid = out.slots.index(donor.slots[s])
        if sid < len(tgt.table) and tgt.table[sid] >= 0:
            raise ValueError('slot %s already in %s' % (donor.slots[s], tgt_col))
        tgt.table += [-1] * (sid + 1 - len(tgt.table))
        tgt.table[sid] = len(tgt.pool)
        tgt.pool += tl[sid]
    kl_anm.relist(out)
    for i in range(n0, len(out.clips)):
        struct.pack_into('<I', out.clips[i], 0x2c, 0)
    bad = kl_anm.audit(out)
    if bad:
        raise ValueError('anm audit: %s' % (bad[:5],))
    raw = out.save()
    back = kl_anm.Anm(raw, 'dd')
    if kl_anm.audit(back) or back.save() != raw:
        raise ValueError('merged anm does not round-trip')
    for s in slots:
        ci = back.lookup(tgt_col, donor.slots[s])
        if ci is None or 'Police' not in back.names[ci]:
            raise ValueError('lookup %s in %s' % (donor.slots[s], tgt_col))
    return raw, len(slots), len(dd.clips), len(back.clips)


# ------------------------------------------------------------------ the build
def cars(src, dst, log=print, plan=None):
    """plan=None: the stage-B lane (md5 c0e7b8ee). plan = dict(paths={body: [(x, z), ...]}, cells=CELLS-like, backstop=seconds): each car's donor keys
    are laid by arc fraction on its own polyline and its rotation keys follow the new tangent (kl_map_escape.van_prepare's rule)."""
    import kl_anm, kl_anmjoin as AJ
    data = open(src, 'rb').read()
    if md5(data)[:8] != PIN[:8]:
        raise ValueError('%s: md5 %s is not stage A (%s)' % (src, md5(data), PIN[:8]))
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + TOP):
        log('%s already holds %s: copied unchanged' % (src, TOP))
        shutil.copyfile(src, dst)
        return None
    d = IG.Donor.get(DON)
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
    a0, s0 = AS.census(sc)
    nav = KB.Nav(A.nav, links=True)
    main = collections.Counter(nav.part[i] for i in range(len(nav.pv)) if nav.ok[i]).most_common(1)[0][0]
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)

    # ---- the lane, from the donor's keys, proved against the map
    tracks = {k: body_track(d, k) for k in BODIES}
    e1 = tracks[BODIES[0]][1][-1]
    mp = lane_map(e1)
    for k in BODIES:
        p0 = tracks[k][1][0]
        if max(abs(p0[i] - struct.unpack_from('<3f', d.ent(k).trans)[i]) for i in range(3)) > 1.0:
            raise ValueError('body %d: first key %s is not its placement' % (k, p0))
    lane = {k: [mp(p) for p in tracks[k][1]] for k in BODIES}
    cells, backstop, rotnew = CELLS, BACKSTOP_S, {}
    if plan is None:
        stop1 = STOP
        if (round(lane[BODIES[0]][-1][0], 3), round(lane[BODIES[0]][-1][2], 3)) != STOP:
            raise ValueError('car 1 does not stop at %s' % (STOP,))
    else:
        import kl_map_escape as ME
        cells, backstop = plan['cells'], plan['backstop']
        ends0 = sorted({o for e in d.ents if e.raw for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(d.head)})
        for k in BODIES:
            K = ME.VanKeys(d.head, d.ent(k).raw, ends0, kl_graft.keys_tracks)
            pts = tracks[k][1]
            if K.npos != len(pts) or K.pos[0] != pts[0]:
                raise ValueError('car %d: the key table is not the lane' % k)
            old = ME.Poly(pts)
            new = ME.Poly([(x, 0.0, z) for x, z in plan['paths'][k]])
            lane[k] = [new.at(old.cum[i] / old.len * new.len) for i in range(len(pts))]
            first = {}
            for f in range(K.frames - 1, -1, -1):
                first[K.f2r[f]] = f
            rots, worst = [], 0.0
            for r, q in enumerate(K.rot):
                kp = K.f2p[first[r]]
                s_old = old.cum[min(kp, len(pts) - 1)]
                s_new = s_old / old.len * new.len
                rel = ME._wrap(K.yaw(q) - ME._heading(old.tan(s_old, ME.AXLES)))
                want = ME._heading(new.tan(s_new, ME.AXLES)) + rel
                q2 = K.turned(q, want - K.yaw(q))
                worst = max(worst, abs(ME._wrap(K.yaw(q2) - want)))
                rots.append(q2)
            if worst > 1.0:
                raise ValueError('car %d: a rotation key is %.1f degrees off its heading' % (k, worst))
            rotnew[K.offs[2]] = rots
        stop1 = (lane[BODIES[0]][-1][0], lane[BODIES[0]][-1][2])
    stops = [lane[k][-1] for k in BODIES]
    for st in stops:
        a = nav.at(st[0], 0.0, st[2], dy=60.0)
        if a is None or nav.part[a[0]] != main:
            raise ValueError('stop %s is not on the main nav part' % (st,))
    for n in cells:
        for c in cells[n]:
            a = nav.at(c[0], c[1], c[2], dy=60.0)
            if a is None or nav.part[a[0]] != main or nav.clearance(c[0], c[1], c[2], limit=200.0) < 50.0:
                raise ValueError('post %s is not a main-part nav cell with clearance' % (c,))
    say('  lane: %s' % '; '.join('car %d %d keys (%d,%d) -> (%d,%d)' % (i + 1, len(lane[k]), lane[k][0][0], lane[k][0][2], lane[k][-1][0], lane[k][-1][2])
                                for i, k in enumerate(BODIES)))
    # ---- nodes
    M = KB.Maker()
    topg = CV._node(M, B, CV.group_form(B), TOP)
    M.place(topg, (0.0, 0.0, 0.0))
    byk, cut, ndrop = car_nodes(M, d, topg)
    for k in BODIES:
        setpos(M, byk[k], lane[k][0])
    say('  car nodes: %d kept, %d dropped, %d proxy list entries cut' % (len(byk), ndrop, cut))
    # models: the closure of every model root (one leg), a dry run first
    pS, matS, texS = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    roots = sorted({nd.model for nd in topg.walk() if nd.model and getattr(nd, 'donor', None)})
    kinds, args = G.walk(d.prm, roots)
    slots = {d.prm.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(d.mat, slots))
    for i, k in kinds.items():
        for off, typ, _k in G.fields(d.prm, i, k, args.get(i, 0)):
            if typ in 'tT' and d.prm.u32(i, off):
                want.add(d.prm.u32(i, off) % G.SLOTS['dd'])
    tex, tmap = T.merge_tex(texS, d.tex, want)
    mat, mmap = T.merge_mat(matS, d.mat, slots, tmap)
    pS, cmap = G.append(pS, d.prm, roots, mmap, None, tmap)
    lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
    if lack:
        raise ValueError('shaders missing in the map .fxc: %s' % lack)
    say('  .prm: %d chunks, %d model roots, %d materials, %d textures; shaders missing: none' % (len(kinds), len(roots), len(slots), len(want)))
    for nd in topg.walk():
        if getattr(nd, 'donor', None) and nd.model:
            nd.model = cmap[nd.model]
            M.set(nd, None, {'ZGEOM[4]': nd.model})
    lit = [e for e in B.ents if e.tid == 0x200002 and e.links]
    for nd in topg.walk():
        if nd.links is not None and getattr(nd, 'donor', None):
            P = nd.pos or STOP + (0.0,)
            P = (stop1[0], 0.0, stop1[1])
            best = min(lit, key=lambda e: sum((B.fr[e][1][i] - P[i]) ** 2 for i in range(3)))
            nd.links = list(best.links)
    # squads, clock
    clock = FED.clone_built(M, B, sc.resolve(R + KB.SQUAD + 'Squad#02')[0], CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    cops, mcs = squads_nodes(M, B, d, byk, clock, None, cells)
    proxy_path = NEW_PROXY
    act = IG.clone(M, d, 18455, 'Activator_Cars', lambda s: NEW_PROXY + s[len(OLD_PROXY):] if s.lower().startswith(OLD_PROXY.lower()) else s)
    M.place(act, (0.0, 0.0, 0.0))
    clock.add(act)
    radio = [sc.path[k] for k in (117,)]
    hunts = [R + 'AI_Enemies!FrontMall_01' + BS + 'HuntBehaviour', R + 'AI_Enemies!FrontMall_02' + BS + 'HuntBehaviour']
    for h in hunts:
        if len(sc.resolve(h)) != 1:
            raise ValueError('%s not found' % h)
    arrive = clock.add(FED.clone_built(M, B, sc.resolve(KOW.TIMER_FORM)[0], 'Arrive'))
    M.place(arrive, (0.0, 0.0, 0.0))
    arrive_p = R + CLOCK + BS + 'Arrive'
    act_p = R + CLOCK + BS + 'Activator_Cars'
    M.set(arrive, 'TriggerDelay2', {0: float(ARRIVE_S), 4: mcs + [act_p] + hunts + radio})
    back = clock.add(FED.clone_built(M, B, sc.resolve(KOW.TIMER_FORM)[0], 'Backstop'))
    M.place(back, (0.0, 0.0, 0.0))
    back_p = R + CLOCK + BS + 'Backstop'
    M.set(back, 'TriggerDelay2', {0: float(backstop), 4: [arrive_p]})
    tops = [topg, clock] + cops
    fa_new = 6
    if a0 + fa_new > ENGINE_ACTORS or s0 + 3 > ENGINE_SQUADS:
        raise ValueError('budget: %d / %d' % (a0 + fa_new, s0 + 3))
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm01cars')
    # ---- the edits on existing nodes
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [back_p]))
    mci = Jn.resolve(R + 'Triggers!MercsClosingIn')[0]
    ci = AU.ctrl_of(Jn, mci, 'TriggerBox')
    have = list(KOW.values(Jn, mci, 'TriggerBox')[17])
    kl_fa.edit(Jn, mci, ci, lambda us: AU.setv(Jn, us, 17, have + [arrive_p]))
    for nm in ('FrontMall_01', 'FrontMall_02'):
        k = Jn.resolve(R + ENEMY_TOP + nm)[0]
        ci = AU.ctrl_of(Jn, k, 'ZSquadScript')
        kl_fa.edit(Jn, k, ci, lambda us: AU.setv(Jn, us, 3, 0))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    for p in [proxy_path, arrive_p, back_p, act_p] + mcs:
        if len(Jn.resolve(p)) != 1:
            raise ValueError('%s does not resolve' % p)
    prp = Jn.p.serialize()
    back_prp = Prp(prp)
    if back_prp.serialize() != prp or len(back_prp.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + fa_new or fs != s0 + 3 or fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    say('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
    # ---- the entities
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    for t in tops:
        nxt = C2._write_ent(A, t, None, nxt, made)
    A.ref_slots = max(A.ref_slots, nxt)
    # KEYS: the 26 animated nodes' tracks, copied once each; the bodies' position track scaled
    raws = {k: d.ent(k).raw for k in byk if d.ent(k).raw}
    trk = {k: kl_graft.keys_tracks(r) for k, r in raws.items()}
    ev = sorted({o for e in d.ents if e.raw for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(d.head)})
    want_o = sorted({o for tl in trk.values() for _p, oo in tl for o in oo})
    A.head += bytes(-len(A.head) % 16)
    newoff, body_new = {}, {}
    for o in want_o:
        end = next(x for x in ev if x > o)
        blob = bytearray(d.head[o:end])
        for k in BODIES:
            if o == tracks[k][0]:
                n = len(tracks[k][1])
                for i in range(n):
                    x, y, z = struct.unpack_from('<3f', blob, 12 * i)
                    struct.pack_into('<3f', blob, 12 * i, *(mp((x, y, z)) if plan is None else lane[k][i]))
                body_new[k] = len(A.head)
        for i, q in enumerate(rotnew.get(o, ())):
            struct.pack_into('<4h', blob, 8 * i, *q)
        newoff[o] = len(A.head)
        A.head += bytes(blob) + bytes(-len(blob) % 16)
    for k, r in raws.items():
        raw = bytearray(r)
        for p, oo in trk[k]:
            for i, o in enumerate(oo):
                struct.pack_into('<I', raw, p + 4 * i, newoff[o])
        made[id(byk[k])].raw = bytes(raw)
    # prove by data: read the scaled tracks back from the new head and compare with the intended lane
    for k in BODIES:
        n = len(lane[k])
        got = [struct.unpack_from('<3f', A.head, body_new[k] + 12 * i) for i in range(n)]
        if max(abs(got[i][j] - lane[k][i][j]) for i in range(n) for j in range(3)) > 0.05:
            raise ValueError('car %d: the scaled keys differ from the lane' % k)
        g = (struct.unpack('<I', made[id(byk[k])].raw[kl_graft.keys_tracks(made[id(byk[k])].raw)[0][0] + 4 * KEYS_BODY_POS:][:4])[0])
        if g != body_new[k]:
            raise ValueError('car %d: the raw block does not point at the scaled track' % k)
    say('  KEYS: %d tracks of %d nodes copied to head %#x..%#x; body position tracks scaled (last keys %s)' % (
        len(want_o), len(raws), min(newoff.values()), len(A.head), [tuple(round(v) for v in s) for s in stops]))
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
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    xs = [p[0] for k in BODIES for p in lane[k]]
    zs = [p[2] for k in BODIES for p in lane[k]]
    items.append((slot1[made[id(topg)]] + 2, (min(xs) - 500.0, LANE_Y[0], min(zs) - 500.0), (max(xs) + 500.0, LANE_Y[1], max(zs) + 500.0)))
    for t in [clock] + cops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    if r3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    # .oct records of the donor models, then the .prm for real
    unref = lambda v: (v & ~1) - 4
    rec_d = {v: n for n, v in enumerate(d.oct.record_refs())}
    keep = sorted({rec_d[d.prm.u32(i, 0x1c)] for i, k in kinds.items() if k == 'root' and d.prm.u32(i, 0x1c)})
    octk, _same, refs_b = O.append_records(octn, d.oct, cmap, keep)
    refs_a = dict(zip(octx.record_refs(), octk.record_refs()))
    pcur = G.read(B['.prm'], 'dd')
    pnew, cmap2 = G.append(pcur, d.prm, roots, mmap, {unref(a): unref(b) for a, b in refs_b.items()}, tmap)
    if cmap2 != cmap:
        raise ValueError('kl_prmgraph.append numbers chunks differently on the second run')
    repointed = 0
    for i in range(1, len(pcur.chunks)):
        c = pnew.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
            v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
            if v != struct.unpack_from('<I', c, 0x1c)[0]:
                pnew.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]
                repointed += 1
    prm_bytes = G.write(pnew)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    if G.write(G.read(prm_bytes, 'dd')) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    # ---- the ANM
    anm_raw, nclip, c0, c1 = anm_pass(B['.ANM'], kl_anm.Anm(AJ.stock_anm(DON), 'dd'))
    say('  .ANM: %d F03_Police slots merged into Mercenary_04 (%d -> %d clips)' % (nclip, c0, c1))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octk.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    new[B.ext['.ANM']] = anm_raw
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    work = tempfile.mkdtemp(prefix='dm01cars_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F01_Main.zip'), [(nm, new[nm]) for nm in B.order])
        import kl_fa_bank
        sealed = kl_fa_bank.seal(work, log=lambda *_: None)
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        if problems:
            log('  reverify notes: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep = collections.OrderedDict(entities_before=len(B.ents), entities=len(allents), added=len(order), census=[a0, s0, fa, fs], slot_ids_moved=moved,
                                  prm_roots_repointed=repointed, sealed=sealed, members_changed=changed, reverify=problems[:5],
                                  stops=[[round(v, 1) for v in s] for s in stops], starts=[[round(v, 1) for v in lane[k][0]] for k in BODIES],
                                  posts={n: cells[n] for n in cells}, backstop_s=backstop, lines=lines)
    log('  written %s: %d added, %d slot ids renumbered, members changed: %s' % (dst, len(order), moved, ' '.join(changed)))
    return rep


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'cars':
        print(json.dumps(cars(sys.argv[2], sys.argv[3]), indent=1, default=str))
    else:
        print(__doc__)
