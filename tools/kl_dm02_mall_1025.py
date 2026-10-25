#!/usr/bin/env python3
"""
kl_dm02_mall_1025.py - DM02 Late Night Opening (mall, Dog Days slot F02): the "extra stuff" pass, 2026-10-25.

    python kl_dm02_mall_1025.py build <in F02_Main.zip> <out F02_Main.zip>     one build (pinned on the live DM02 zip ae193d9c)
    python kl_dm02_mall_1025.py stage <in F02_Main.zip> <out folder> [--rehearse <scratch>]
                                  build + md5-chained INSTALL/UNDO (.bat + .ps1 + mall.json) and a rehearsal on a scratch game folder

WHAT THE PLAYER GETS (chain: kl_interact_graft.build -> kl_dm01b_gas_1025.build -> cars -> sound re-point; every step md5-pinned)
  1. 6 closed kick doors (Dog Days F03 KickableDoor, leaf shut in the doorway) on staff / service doorways of the mall: 4 on the first floor
     (the two shop-back corridors) and 2 on the ground floor (the south-west corridor).  The doorways are EMPTY openings (no door leaf in the
     Dead Men model), so each door stands on a "virtual" hinge (kl_interact_graft.virtual_host).
  2. 6 wall-mounted fire extinguishers (F04 can, rigid, explosive): 2 on the ground floor beside the south-west corridor / entrance corridor,
     2 in the atrium east / west on the ground floor, 2 on the first floor beside the doors.
  3. 4 fuel cans (F03 FuelCan with the stock gas explosion) at the foot of police cover lines: atrium centre, west corridor, east shops, the
     first-floor top line (all >= 900 cm from every heister / traitor start).
  4. Police cars arrive in the street south of the mall entrance (3 F03 police cars, MatPosAnim) and 6 SWAT men get out and hold by the
     entrance.  Timer: 'Backstop' (BACKSTOP_S after the round start, on the AIMonitor start list) lists 'Arrive'.
  5. The graft nodes' sound references (donor offsets) are re-pointed BY NAME into DM02's own sound bank (see resound()).

Everything is NEW top groups (KL_Interact!1, KL_Gas!1, KL_Cars!, KL_Cars!Clock, KL_Cars!Cop_1..3).  Nothing existing is deleted; the only
existing node edited is the AIMonitor start list (one entry added).  Budget: actors 61 -> 67 (cap 99), squads 21 -> 24 (cap 55).
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene, kl_light
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_fa_climb2 as C2
import kl_fa_cover as CV
import kl_interact_graft as IG
import kl_dm01b_gas_1025 as GS
import kl_dm01cars_1025 as C
import kl_dm02_assault_1025 as AS
import kl_octree as O
import kl_old_waves as KOW
import kl_prmgraph as G
import kl_texmat as T
import kl_prpjoin as J
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
SRC_MD5 = 'ae193d9cc8c3237405376306f98e1510'     # the live DM02 zip (assault, 2026-10-25)
TAG = '.before-1025dm02mall'
MAP, FILE = 'DM02', 'F02_Main.zip'
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55            # engine-proven caps

# ---- 1. doors: ('at', hinge (x, floor y, z), leaf direction cx) - empty doorways measured on the walk mesh / 10mDor walls / shop windows
#      (re/dm02_mall_1025.md).  The doorway is ~130 cm wide (z 2436..2565, x -1564..-1435); a 120 cm leaf fits.
DOORS = [('at', (-1000.0, 500.0, 2560.0), (0.0, 0.0, 1.0)),
         ('at', (-1440.0, 500.0, 1700.0), (1.0, 0.0, 0.0)),
         ('at', (993.0, 500.0, 2560.0), (0.0, 0.0, 1.0)),
         ('at', (1560.0, 500.0, 1693.0), (1.0, 0.0, 0.0)),
         ('at', (-998.0, 0.0, -3440.0), (0.0, 0.0, 1.0)),
         ('at', (-1440.0, 0.0, -2700.0), (1.0, 0.0, 0.0))]
# ---- 2. extinguishers: target (x, z, floor y); spot_near snaps each to the nearest wall edge of the right floor
# verifier 2026-10-25: the first target (-1000, -3250) snapped to (-1185, -3080), the middle of an 83 cm walk-mesh passage (walls 38 and 45 cm on both sides);
# (-640, -3230) snaps to a 461 cm wall with the next wall 127 cm away
EXT_NEAR = [(-640.0, -3230.0, 0.0), (0.0, -4600.0, 0.0), (2000.0, -400.0, 0.0), (-2000.0, -400.0, 0.0),
            (-1000.0, 2400.0, 500.0), (1000.0, 2600.0, 500.0)]
EXT_LIFT = 100.0      # cm above the floor: stock extinguishers hang on the wall ~100 cm up (stock survey, verifier 2026-10-25; the first build left them on the floor)
# ---- 3. fuel cans: anchors at the foot of police lines (Wave_1 atrium centre, Wave_W corridor, Wave_E shops, Wave_3 first-floor line)
FUEL = [(-300.0, -700.0, 0.0), (-1000.0, -1950.0, 0.0), (1100.0, 1450.0, 0.0), (100.0, 3500.0, 500.0)]
# ---- 4. cars.  The F03 lane runs 135 m towards -z; here it is turned 180 degrees (R(x, z) = (-x, -z)) so the cars come from the south
# (the street plaza, z -10750 .. -5250, all on the main walk-mesh part) and stop in front of the entrance (x ~ 600, z ~ -5000).
STOP = (1050.0, -6300.0)                          # car 1 stops here (x, z)
SCALE = 0.30                                     # lane scale: 135 m -> 41 m (the plaza is 55 m deep)
CELLS = {1: [(300.0, 0.0, -5700.0), (900.0, 0.0, -5700.0)],       # Defend posts in front of the entrance, >= 250 from the stops, >= 300 apart
         2: [(-100.0, 0.0, -5600.0), (1500.0, 0.0, -5700.0)],
         3: [(200.0, 0.0, -6050.0), (1150.0, 0.0, -6050.0)]}
ARRIVE_S, BACKSTOP_S = 0.3, 25.0                 # GUESS: ~25 s after the round start the first heisters are in the atrium; the lane takes ~10 s
KEYS_BODY_ROT = 2                                # the body's rotation track (int16 x4 quaternion x y z w / 32768) is the third of the six KEYS offsets
# F03's MiniCut cops use the Dead Men soldiers' animation collection; DM02's Wave_3 actors hold the token for 'anmcol:animationdatabase#Army'
# (read from the actor's property list, 2026-10-25), so the 18 F03_Police clips are merged into 'Army'.
ANM_COL = 'Army'
# Donor sound object name -> DM02 object name when DM02's bank does not hold the donor's own (GUESS: a wooden crack for the kick)
SOUND_FALLBACK = {b'audio:levelsetup/all/environment/doors/kickable_door/kickable_door#set':
                  b'audio:levelsetup/all/impacts/wood_crack/wood_crack_01#set'}


def md5(b):
    return hashlib.md5(b).hexdigest()


def yaw180_node(M, nd):
    """The rest place of a body turned with the lane: rotation rows (local Z, Y, X in world) of a yaw-only node get x and z negated."""
    r = list(struct.unpack_from('<9f', nd.rot, 0))
    if max(abs(r[1]), abs(r[3]), abs(r[5]), abs(r[7])) > 0.02 or abs(r[4] - 1.0) > 0.02:
        raise ValueError('body %s is not yaw-only: %s' % (nd.name, r))
    new = [-r[0], r[1], -r[2], r[3], r[4], r[5], -r[6], r[7], -r[8]]
    M.set(nd, None, {'ZGEOM[1]': new})
    nd.rot = struct.pack('<9f', *new) + nd.rot[36:]


def quat_yaw180(blob, what):
    """A track of int16 x4 quaternions (x, y, z, w) turned 180 degrees about y in the world: q' = (z, w, -x, -y).  The formula is exact for any q (a world turn about y); keys with more than ~10 degrees of pitch/roll are refused as a sanity check."""
    out = bytearray(blob)
    for i in range(len(blob) // 8):
        x, y, z, w = struct.unpack_from('<4h', blob, 8 * i)
        if abs(x) > 3000 or abs(z) > 3000:                  # the body bobs a little (pitch/roll up to ~10 degrees); the formula is exact for any q
            raise ValueError('%s key %d is not yaw-only: %s' % (what, i, (x, y, z, w)))
        struct.pack_into('<4h', out, 8 * i, z, w, -x, -y)
    return bytes(out)


def heading(q):
    """Yaw angle (rad) of a yaw-only int16 quaternion."""
    return 2.0 * math.atan2(q[1], q[3])


def _lane_y(plan, k):
    """Floor height of car body k's lane: plan['y'] (a number or {body: number}), default 0.0 (the DM01/DM01B/DM02 street level)."""
    y = plan.get('y', 0.0)
    return float(y[k] if isinstance(y, dict) else y)


def plan_lane(d, tracks, plan):
    """The lane of a plan (see cars): each car's donor position keys laid by arc fraction on its own polyline [(x, z), ...] (y 0), and its rotation
    rows turned to follow the polyline's tangent (kl_map_escape.van_prepare's rule, as kl_dm01cars_1025.cars(plan=)).  -> ({body: [(x, y, z)]}, {rotation
    track offset: [new int16 x4 rows]}).  A row is refused when it ends more than 1 degree off its wanted heading."""
    import kl_map_escape as ME
    lane, rotnew = {}, {}
    ends0 = sorted({o for e in d.ents if e.raw for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(d.head)})
    for k in C.BODIES:
        K = ME.VanKeys(d.head, d.ent(k).raw, ends0, kl_graft.keys_tracks)
        pts = tracks[k][1]
        if K.npos != len(pts) or K.pos[0] != pts[0]:
            raise ValueError('car %d: the key table is not the lane' % k)
        old = ME.Poly(pts)
        new = ME.Poly([(q[0], q[2] if len(q) > 2 else _lane_y(plan, k), q[1]) for q in plan['paths'][k]])      # y: a path point (x, z, y) carries its own ground height (DM06: the collision terrain, 2026-10-25 verifier), else the plan's floor height
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
    return lane, rotnew


# ------------------------------------------------------------------ step 4: the cars
def cars(src, dst, log=print, plan=None):
    """plan=None: the DM02 lane (the donor lane turned 180 degrees and scaled about STOP). plan = dict(paths={body k: [(x, z), ...]}, cells={n: [(x, y, z), ...]},
    backstop=seconds, anm_col=collection name, caps=(actors, squads)): each car's donor keys are laid by arc fraction on its own polyline and its rotation keys
    follow the new tangent (kl_map_escape.van_prepare's rule; the same plan form as kl_dm01cars_1025.cars). Added 2026-10-25 for kl_dm_overhaul_1025."""
    import kl_anm, kl_anmjoin as AJ
    data = open(src, 'rb').read()
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + C.TOP):
        log('%s already holds %s: copied unchanged' % (src, C.TOP))
        shutil.copyfile(src, dst)
        return None
    cells, backstop = (CELLS, BACKSTOP_S) if plan is None else (plan['cells'], plan['backstop'])
    cap_a, cap_s = (ENGINE_ACTORS, ENGINE_SQUADS) if plan is None else plan.get('caps', (ENGINE_ACTORS, ENGINE_SQUADS))
    anm_col = ANM_COL if plan is None else plan.get('anm_col', ANM_COL)
    C.CELLS, C.STOP, C.SCALE = CELLS, STOP, SCALE          # lane_map reads these module globals; squads_nodes gets the cells explicitly below
    if plan is not None and plan.get('wave3'):
        C.KOW_WAVE3 = plan['wave3']          # the squad/actor clone template (default OldWaves!Wave_3 of the DM01/DM02 builds)
    d = IG.Donor.get(C.DON)
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

    # ---- the lane: the donor's position keys, turned 180 degrees about the y axis and scaled about the stop
    tracks = {k: C.body_track(d, k) for k in C.BODIES}
    e1 = tracks[C.BODIES[0]][1][-1]
    mp = lambda p: (STOP[0] - SCALE * (p[0] - e1[0]), p[1], STOP[1] - SCALE * (p[2] - e1[2]))
    for k in C.BODIES:
        p0 = tracks[k][1][0]
        if max(abs(p0[i] - struct.unpack_from('<3f', d.ent(k).trans)[i]) for i in range(3)) > 1.0:
            raise ValueError('body %d: first key %s is not its placement' % (k, p0))
    lane = {k: [mp(p) for p in tracks[k][1]] for k in C.BODIES}
    rotnew = {}
    if plan is not None:
        lane, rotnew = plan_lane(d, tracks, plan)
    stops = [lane[k][-1] for k in C.BODIES]
    nav_dy = 60.0 if plan is None else float(plan.get('nav_dy', 60.0))      # DM06: the walk mesh floats 20..60 above the collision terrain the lane follows
    for st in stops:
        a = nav.at(st[0], st[1], st[2], dy=nav_dy)
        if a is None or nav.part[a[0]] != main:
            raise ValueError('stop %s is not on the main nav part' % (st,))
    off = []
    for k in C.BODIES:
        for p in lane[k][::6] + [lane[k][-1]]:
            a = nav.at(p[0], p[1], p[2], dy=nav_dy)
            if a is None or nav.part[a[0]] != main or nav.clearance(p[0], a[1], p[2], limit=200.0) < 100.0:
                off.append((round(p[0]), round(p[2])))
    if off:
        raise ValueError('lane points off the open street (main part, clearance 100): %s' % off[:6])
    for n in cells:
        for c in cells[n]:
            a = nav.at(c[0], c[1], c[2], dy=60.0)
            if a is None or nav.part[a[0]] != main or nav.clearance(c[0], c[1], c[2], limit=200.0) < 50.0:
                raise ValueError('post %s is not a main-part nav cell with clearance' % (c,))
            if min(math.hypot(c[0] - s[0], c[2] - s[2]) for s in stops) < 250.0:
                raise ValueError('post %s is within 250 cm of a stop' % (c,))
    say('  lane: %s' % '; '.join('car %d %d keys (%d,%d) -> (%d,%d)' % (i + 1, len(lane[k]), lane[k][0][0], lane[k][0][2], lane[k][-1][0], lane[k][-1][2])
                                for i, k in enumerate(C.BODIES)))
    # ---- nodes
    M = KB.Maker()
    topg = CV._node(M, B, CV.group_form(B), C.TOP)
    M.place(topg, (0.0, 0.0, 0.0))
    byk, cut, ndrop = C.car_nodes(M, d, topg)
    for k in C.BODIES:
        C.setpos(M, byk[k], lane[k][0])
        if plan is None:
            yaw180_node(M, byk[k])
    say('  car nodes: %d kept, %d dropped, %d proxy list entries cut' % (len(byk), ndrop, cut))
    pS, matS, texS = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    roots = sorted({nd.model for nd in topg.walk() if nd.model and getattr(nd, 'donor', None)})
    kinds, args = G.walk(d.prm, roots)
    slots = {d.prm.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(d.mat, slots))
    for i, k in kinds.items():
        for off_, typ, _k in G.fields(d.prm, i, k, args.get(i, 0)):
            if typ in 'tT' and d.prm.u32(i, off_):
                want.add(d.prm.u32(i, off_) % G.SLOTS['dd'])
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
            P = (stops[0][0], 0.0, stops[0][2])
            best = min(lit, key=lambda e: sum((B.fr[e][1][i] - P[i]) ** 2 for i in range(3)))
            nd.links = list(best.links)
    # squads, clock
    clock = FED.clone_built(M, B, sc.resolve(R + KB.SQUAD + 'Squad#02')[0], C.CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    cops, mcs = C.squads_nodes(M, B, d, byk, clock, None, cells)
    act = IG.clone(M, d, 18455, 'Activator_Cars', lambda s: C.NEW_PROXY + s[len(C.OLD_PROXY):] if s.lower().startswith(C.OLD_PROXY.lower()) else s)
    M.place(act, (0.0, 0.0, 0.0))
    clock.add(act)
    arrive = clock.add(FED.clone_built(M, B, sc.resolve(KOW.TIMER_FORM)[0], 'Arrive'))
    M.place(arrive, (0.0, 0.0, 0.0))
    arrive_p = R + C.CLOCK + BS + 'Arrive'
    act_p = R + C.CLOCK + BS + 'Activator_Cars'
    M.set(arrive, 'TriggerDelay2', {0: float(ARRIVE_S), 4: mcs + [act_p]})
    back = clock.add(FED.clone_built(M, B, sc.resolve(KOW.TIMER_FORM)[0], 'Backstop'))
    M.place(back, (0.0, 0.0, 0.0))
    back_p = R + C.CLOCK + BS + 'Backstop'
    M.set(back, 'TriggerDelay2', {0: float(backstop), 4: [arrive_p]})
    tops = [topg, clock] + cops
    fa_new = 6
    if a0 + fa_new > cap_a or s0 + 3 > cap_s:
        raise ValueError('budget: %d / %d' % (a0 + fa_new, s0 + 3))
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm02cars')
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [back_p]))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    for p in [C.NEW_PROXY, arrive_p, back_p, act_p] + mcs:
        if len(Jn.resolve(p)) != 1:
            raise ValueError('%s does not resolve' % p)
    prp = Jn.p.serialize()
    back_prp = Prp(prp)
    if back_prp.serialize() != prp or len(back_prp.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + fa_new or fs != s0 + 3 or fa > cap_a or fs > cap_s:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    say('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, cap_a, cap_s))
    # ---- the entities
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    for t in tops:
        nxt = C2._write_ent(A, t, None, nxt, made)
    A.ref_slots = max(A.ref_slots, nxt)
    # KEYS: the animated nodes' tracks copied once each; the bodies' position track moved to the lane, their rotation track turned 180 degrees
    raws = {k: d.ent(k).raw for k in byk if d.ent(k).raw}
    trk = {k: kl_graft.keys_tracks(r) for k, r in raws.items()}
    ev = sorted({o for e in d.ents if e.raw for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(d.head)})
    want_o = sorted({o for tl in trk.values() for _p, oo in tl for o in oo})
    rot_o = {trk[k][0][1][KEYS_BODY_ROT] for k in C.BODIES}
    for k, tl in trk.items():
        if k not in C.BODIES and rot_o & set(tl[0][1]):
            raise ValueError('node %d shares a body rotation track' % k)
    A.head += bytes(-len(A.head) % 16)
    newoff, body_new, rot_new = {}, {}, {}
    for o in want_o:
        end = next(x for x in ev if x > o)
        blob = bytearray(d.head[o:end])
        for k in C.BODIES:
            if o == tracks[k][0]:
                for i in range(len(tracks[k][1])):
                    x, y, z = struct.unpack_from('<3f', blob, 12 * i)
                    struct.pack_into('<3f', blob, 12 * i, *(mp((x, y, z)) if plan is None else lane[k][i]))
                body_new[k] = len(A.head)
        if plan is None and o in rot_o:
            blob = bytearray(quat_yaw180(bytes(blob), 'rotation track %#x' % o))
            rot_new[o] = len(A.head)
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
    for k in C.BODIES:
        n = len(lane[k])
        got = [struct.unpack_from('<3f', A.head, body_new[k] + 12 * i) for i in range(n)]
        if max(abs(got[i][j] - lane[k][i][j]) for i in range(n) for j in range(3)) > 0.05:
            raise ValueError('car %d: the moved keys differ from the lane' % k)
        g = struct.unpack('<I', made[id(byk[k])].raw[kl_graft.keys_tracks(made[id(byk[k])].raw)[0][0] + 4 * C.KEYS_BODY_POS:][:4])[0]
        if g != body_new[k]:
            raise ValueError('car %d: the raw block does not point at the moved track' % k)
    # heading proof: for each body, the last key's heading (donor and turned) against the last travel direction.  Same sign of the dot product
    # (heading vector (sin, cos) . travel) before and after = the turned rotation matches the turned lane; |dot| ~ 1 = it drives forward/backward.
    proof = []
    for k in (C.BODIES if plan is None else ()):      # plan mode: the rotation rows follow the polyline tangent (checked in plan_lane), no 180-degree proof
        o_rot = trk[k][0][1][KEYS_BODY_ROT]
        q0 = struct.unpack_from('<4h', d.head, o_rot + 8 * 40)
        q1 = struct.unpack_from('<4h', A.head, newoff[o_rot] + 8 * 40)
        p_a, p_b = tracks[k][1][39], tracks[k][1][41]
        l_a, l_b = lane[k][39], lane[k][41]
        tr0 = (p_b[0] - p_a[0], p_b[2] - p_a[2])
        tr1 = (l_b[0] - l_a[0], l_b[2] - l_a[2])
        n0, n1 = math.hypot(*tr0) or 1.0, math.hypot(*tr1) or 1.0
        h0, h1 = heading(q0), heading(q1)
        d0 = (math.sin(h0) * tr0[0] + math.cos(h0) * tr0[1]) / n0
        d1 = (math.sin(h1) * tr1[0] + math.cos(h1) * tr1[1]) / n1
        proof.append((round(d0, 2), round(d1, 2)))
        if d0 * d1 <= 0:
            raise ValueError('car %d: heading . travel flips sign (%s -> %s): the turned quaternion does not fit the turned lane' % (k, d0, d1))
    say('  KEYS: %d tracks of %d nodes copied to head %#x..%#x; body position tracks on the lane, rotation tracks %s (heading.travel before/after %s)' % (
        len(want_o), len(raws), min(newoff.values()), len(A.head), 'turned 180 degrees' if plan is None else 'follow the polyline', proof))
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
    xs = [p[0] for k in C.BODIES for p in lane[k]]
    zs = [p[2] for k in C.BODIES for p in lane[k]]
    items.append((slot1[made[id(topg)]] + 2, (min(xs) - 500.0, C.LANE_Y[0], min(zs) - 500.0), (max(xs) + 500.0, C.LANE_Y[1], max(zs) + 500.0)))
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
    anm_raw, nclip, c0, c1 = C.anm_pass(B['.ANM'], kl_anm.Anm(AJ.stock_anm(C.DON), 'dd'), tgt_col=anm_col)
    say('  .ANM: %d F03_Police slots merged into %s (%d -> %d clips)' % (nclip, anm_col, c0, c1))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octk.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    new[B.ext['.ANM']] = anm_raw
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    kl_graft.write_zip(dst, [(nm, new[nm]) for nm in B.order])
    say('  written %s: %d added, %d slot ids renumbered, members changed: %s' % (dst, len(order), moved, ' '.join(changed)))
    return dict(census=[a0, s0, fa, fs], slot_ids_moved=moved, prm_roots_repointed=repointed, members_changed=changed,
                stops=[[round(v, 1) for v in s] for s in stops], starts=[[round(v, 1) for v in lane[k][0]] for k in C.BODIES],
                posts={n: cells[n] for n in cells}, backstop_s=backstop, heading_proof=proof, lines=lines)


# ------------------------------------------------------------------ step 5: sound references of the graft nodes, by name
def resound(src, dst, log=print, scope=None, cars_donor=True):
    """The grafted nodes (KL_Door_*, KL_Fuel_*, KL_Cars!*) carry sound references that are byte offsets into the DONOR level's .SND (F03; the
    extinguisher groups F04).  Left as they are they name some other object of DM02's bank (or none).  Here each is mapped through its NAME to
    DM02's own bank (an object of that name, else SOUND_FALLBACK, else 0 = silent).  .SND / .WHD / .WAV are not touched (no beside files)."""
    import kl_snd
    B = KB.Built(src)
    sc = B.sc
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'resound')
    if J.fingerprints(Jn)[0] != J.fingerprints(sc)[0]:
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    mine = kl_snd.Snd('dd', B.files[B.ext['.SND']])
    byname = {}
    for o in mine.kind:
        try:
            byname.setdefault(mine.name(o), o)
        except Exception:
            pass
    groups = {'F03': [], 'F04': []}
    # KL_Cars!: only the nodes cloned from F03 (the cars group, each squad's MiniCut and modifier); the actors, squads and timers there are
    # clones of DM02's own nodes and keep their own (DM02) references
    f3 = IG.Donor.get('F03').sc.names
    donor_pre = [] if not cars_donor else [(R + C.TOP + BS + C.CARS).lower(), (R + C.CLOCK + BS + 'Activator_Cars').lower()] + [(R + C.COP % n + BS + f3[S[x]]).lower() for n in (1, 2, 3) for S in [C.SWAT[n]] for x in ('mc', 'mod')]
    for k in range(1, len(Jn.nodes)):
        p = Jn.path[k]
        if scope is not None and not scope(p):          # kl_dm_overhaul_1025: only the nodes this build added (an older graft keeps its references)
            continue
        if (BS + 'KL_Door_') in p or (BS + 'KL_Fuel_') in p:
            groups['F03'].append(k)
        elif any(p.lower() == q or p.lower().startswith(q + BS) for q in donor_pre):
            groups['F03'].append(k)
        elif (BS + 'KL_Ext_') in p:
            groups['F04'].append(k)
    rep = {}
    for lv, ks in groups.items():
        dsnd = kl_snd.bank(lv)
        roots = kl_snd.roots(Jn, ks)
        omap, table = {}, []
        for r in sorted(roots):
            nm = dsnd.name(r) if r in dsnd.kind else None
            tgt = byname.get(nm) or byname.get(SOUND_FALLBACK.get(nm, b'')) or 0
            if tgt:
                omap[r] = tgt
            table.append((hex(r), (nm or b'?').decode('latin1'), hex(tgt), 'same name' if byname.get(nm) else ('fallback' if tgt else 'silent')))
        cnt = kl_snd.rewrite(Jn, ks, omap)
        rep[lv] = dict(nodes=len(ks), table=table, counts=dict(cnt))
        log('  sound %s: %d nodes, %d roots: %s' % (lv, len(ks), len(roots), table))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    kl_graft.write_zip(dst, [(nm, new[nm]) for nm in B.order])
    return rep


# ------------------------------------------------------------------ the chain
def build(src, dst, log=print, keep=None):
    data = open(src, 'rb').read()
    if md5(data) != SRC_MD5:
        raise ValueError('%s: md5 %s is not the pinned %s' % (src, md5(data), SRC_MD5))
    work = keep or tempfile.mkdtemp(prefix='dm02mall_')
    os.makedirs(work, exist_ok=True)
    rep = collections.OrderedDict()
    try:
        s1, s2, s3 = [os.path.join(work, 's%d.zip' % i) for i in (1, 2, 3)]
        log('step 1: doors + extinguishers (kl_interact_graft.build)')
        IG.build(src, s1, ext=len(EXT_NEAR), doors=DOORS, ext_doors=0, spots_near=EXT_NEAR, pin=SRC_MD5, log=log, ext_lift=EXT_LIFT)
        m1 = md5(open(s1, 'rb').read())
        log('step 2: fuel cans (kl_dm01b_gas_1025.build)')
        GS.FUEL_ANCHORS, GS.EXT_WALL = FUEL, []
        GS.ext_spots_wall = lambda B, nav: []
        GS.build(s1, s2, pin=m1, log=log)
        log('step 3: police cars + SWAT')
        rep['cars'] = cars(s2, s3, log=log)
        log('step 4: sound references by name')
        rep['sound'] = resound(s3, dst, log=log)
        rep['md5'] = md5(open(dst, 'rb').read())
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    return rep


# ------------------------------------------------------------------ INSTALL / UNDO (the gas installer, renamed)
def ps_text():
    s = GS.PS1
    s = s.replace('gas.json', 'mall.json').replace('.before-1025dm01bgas', TAG).replace('gas.ps1', 'mall.ps1')
    first = s.index('\n')
    return ('# mall.ps1 - DM02 Late Night Opening, 2026-10-25 (tools/kl_dm02_mall_1025.py): 6 kick doors, 6 extinguishers, 4 fuel cans, police cars + SWAT.\n'
            '#   Chained on the live DM02 zip ae193d9c (assault): `old` in mall.json is that md5; the install refuses any other.\n') + s[first + 1:]


BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mall.ps1" {arg}\r\npause\r\n'


def run_ps(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'mall.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    if dry:
        a.append('-DryRun')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    old = md5(open(src, 'rb').read())
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, FILE)
    rep = build(src, z, log=log)
    new = md5(open(z, 'rb').read())
    man = dict(m=MAP, f=FILE, old=old, new=new, tag=TAG, chain='live DM02 zip ae193d9c (assault)')
    with open(os.path.join(out, 'mall.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'mall.ps1'), 'w', newline='\r\n') as fh:
        fh.write(ps_text())
    for nm, arg in (('INSTALL dm02 mall.bat', ''), ('UNDO dm02 mall.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(src, out, man, scratch, log)
    return man


def rehearse(src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', MAP, FILE)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    t = run_ps(d, g, dry=True); log(t.strip()); assert 'would install' in t and md5(open(live, 'rb').read()) == man['old'], t
    t = run_ps(d, g); log(t.strip()); assert 'installed' in t and md5(open(live, 'rb').read()) == man['new'], t
    assert md5(open(live + TAG, 'rb').read()) == man['old']
    assert 'already installed' in run_ps(d, g)
    t = run_ps(d, g, undo=True); log(t.strip())
    assert md5(open(live, 'rb').read()) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    assert 'already undone' in run_ps(d, g, undo=True)
    run_ps(d, g); assert md5(open(live, 'rb').read()) == man['new']
    run_ps(d, g, undo=True); assert md5(open(live, 'rb').read()) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run_ps(d, g); log(t.strip()); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.rmtree(g, ignore_errors=True)
    log('rehearsal ok (dry run, install, idempotent, undo byte-identical, undo twice, reinstall, wrong md5 refused)')


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 3 or a[0] not in ('build', 'stage'):
        print(__doc__)
        return 2
    if a[0] == 'build':
        print(json.dumps(build(a[1], a[2]), indent=1, default=str))
        return 0
    stage(a[1], a[2], opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
