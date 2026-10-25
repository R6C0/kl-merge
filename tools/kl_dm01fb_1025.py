"""kl_dm01fb_1025.py - DM01 (Hot Coffee) owner feedback round "almost perfect", 2026-10-25.  Input = the live DM01 zip (c0e7b8ee, doors2 -> squads -> cars).

Owner's four points and what this module does:
  1 door kicks silent   -> sound(): the KL_Interact nodes carry Dog Days F03/F04 byte offsets into F03's / F04's .SND, which name nothing in DM01's
                           bank.  kl_snd.merge brings the donors' sounds into DM01's own bank, rewrite() points the fields at them (the club-music fix's method).
  2 extinguishers       -> ext_wall(): mounted on the wall at stock height (F08's wall cabinet geometry), facing out; floor fallback per spot.
  3 NPCs kick doors     -> kick_squad(): a Dog Days KickDoorBehaviourRout squad (F03 template) behind one hall door.
  4 police cars         -> cars(): re-lays the F03 lane: the cars start on the road east of the play area, drive in and stop near the van.

    python kl_dm01fb_1025.py cars <stage A zip> <out zip>
"""
import collections, hashlib, json, math, os, shutil, struct, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm01cars_1025 as CARS
import kl_snd as S
import kl_graft
import kl_fa_bots as KB

BS = chr(92)
R = 'ROOT' + BS
md5 = lambda b: hashlib.md5(b).hexdigest()

# ---------------------------------------------------------------- 4: the cars' road lane (all numbers read from the walk grid, work/s2.py, s3.py)
# The ground east of x 7850 (x 8000..8800, z 16800..24000) is a street outside the nav (not in the play area).  Cars enter from its south end (z 16900),
# drive north, turn west into the van lot and stop in a row facing the van (6153, 20659), 700 cm from it.
R_TURN = 450.0
START_Z = 17100.0
LANES = {CARS.BODIES[0]: (8250.0, 20000.0), CARS.BODIES[1]: (8400.0, 20550.0), CARS.BODIES[2]: (8550.0, 21100.0)}      # (road x, z of the turn)
STOP_X = 6850.0
CELLS = {1: [(6450.0, 0.0, 20000.0), (7300.0, 0.0, 19750.0)],
         2: [(6450.0, 0.0, 20550.0), (7300.0, 0.0, 20300.0)],
         3: [(6450.0, 0.0, 21100.0), (7300.0, 0.0, 20850.0)]}
BACKSTOP_S = 8.0


def lane_path(xr, zt, xs=STOP_X, r=R_TURN, z0=START_Z):
    """North along x = xr, a quarter circle of radius r to the west, west along z = zt to x = xs -> [(x, z)]."""
    pts = [(xr, z0), (xr, zt - r)]
    for a in range(15, 91, 15):
        t = math.radians(a)
        pts.append((xr - r + r * math.cos(t), zt - r + r * math.sin(t)))
    pts.append((xs, zt))
    return pts


def plan():
    return dict(paths={k: lane_path(*LANES[k]) for k in CARS.BODIES}, cells=CELLS, backstop=BACKSTOP_S)


def cars(src, dst, log=print):
    return CARS.cars(src, dst, log, plan=plan())


# ---------------------------------------------------------------- 1: the door-kick sound
# The KL_Interact nodes (kl_interact_graft) carry the donors' raw .SND byte offsets: F03 369088 / 367024 (door kick, door open) and F04 427664
# (extinguisher / can). In DM01's own bank they name nothing, so the kick was silent. Measured (work/g3.py): 3 roots, all inside the KL_Interact!1
# subtree, none elsewhere. The fix is the club-music one: kl_snd.merge brings those wave objects into DM01's bank, rewrite() repoints the fields.
SND_ROOTS = (('F03', {369088, 367024}), ('F04', {427664}))
INTERACT = R + 'KL_Interact!1'


def sound(src, dst, folder, log=print):
    """src zip + the live bank files in `folder` (.WHD .WAV _LS.SND, read only) -> dst zip (new .prp and .SND members) and, beside dst,
    F01_Main.WHD / F01_Main.WAV / F01_Main_LS.SND. -> report dict."""
    B = KB.Built(src)
    sc = B.sc
    if sc.p.serialize() != B['.prp']:
        raise ValueError('the .prp does not round-trip before the edit')
    snd = B.files[B.ext['.SND']]
    rd = lambda n: open(os.path.join(folder, n), 'rb').read()
    whd, wav, ls = rd('F01_Main.WHD'), rd('F01_Main.WAV'), rd('F01_Main_LS.SND')
    top = sc.resolve(INTERACT)
    if len(top) != 1:
        raise ValueError('KL_Interact!1: %d nodes' % len(top))
    top = top[0]
    ks = list(range(top, sc.end[top]))
    want = S.roots(sc, ks)
    allr = set().union(*[r for _l, r in SND_ROOTS])
    if want != allr:
        raise ValueError('sound roots of KL_Interact are %s, expected %s' % (sorted(want), sorted(allr)))
    for k in range(1, len(sc.nodes)):
        if top <= k < sc.end[top]:
            continue
        if S.roots(sc, [k]) & allr:
            raise ValueError('node %s outside KL_Interact names one of the roots' % sc.path[k])
    base = S.Snd('dd', snd, ls).walk()
    cur, omap, st = (snd, whd, wav), {}, collections.Counter()
    b2 = base
    for lv, roots in SND_ROOTS:
        src_b = S.bank(lv)
        s2, w2, v2, om = S.merge(b2, src_b, cur[1], cur[2], S.read(S.beside(lv, '.WHD')), S.read(S.beside(lv, '.WAV')), roots, stats=st)
        omap.update({r: om[r] for r in roots})
        cur = (s2, w2, v2)
        b2 = S.Snd('dd', s2, ls).walk()
    nls = S.ls_bank(ls, S.u32(cur[0], 0))
    bad, n = S.verify(base, cur[0], cur[1], cur[2], nls)
    bad = [x for x in bad if not x.startswith('stock bytes below')]
    if bad:
        raise ValueError('kl_snd.verify: %s' % bad[:5])
    cnt = S.rewrite(sc, ks, omap)
    log('  sound: %s; omap %s' % (dict(cnt), {hex(k): hex(v) for k, v in omap.items()}))
    fin = S.Snd('dd', cur[0], nls).walk()
    for r, v in omap.items():
        if not v or fin.kind.get(v) is None:
            raise ValueError('root %#x has no object in the new bank' % r)
    prp = sc.p.serialize()
    if len(__import__('kl_prp').Prp(prp).nodes()) != len(sc.nodes) - 1 + 0 and False:
        pass
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.SND']] = prp, cur[0]
    work = tempfile.mkdtemp(prefix='dm01fbsnd_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, os.path.basename(dst)), [(nm, new[nm]) for nm in B.order])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    d = os.path.dirname(os.path.abspath(dst))
    for nm, b in (('F01_Main.WHD', cur[1]), ('F01_Main.WAV', cur[2]), ('F01_Main_LS.SND', nls)):
        open(os.path.join(d, nm), 'wb').write(b)
    return dict(omap={hex(k): hex(v) for k, v in omap.items()}, counts=dict(cnt), old=dict(snd=md5(snd), whd=md5(whd), wav=md5(wav), ls=md5(ls)),
                new=dict(snd=md5(cur[0]), whd=md5(cur[1]), wav=md5(cur[2]), ls=md5(nls)), verify=dict(n))


# ---------------------------------------------------------------- 3: a squad that kicks a door open (NPCs kick doors)
# GUESS (unproven in the engine, offline checks only): Dog Days' native NPC door kick is KickDoorBehaviourRout + KickDoorBehaviour_PosInfo (F03's heist
# bots use it on their own door). No stock level makes an ENEMY squad kick a KickableDoor, so this is the closest honest equivalent: the same rout
# cloned from F03 under three of the map's own cops (Wave_3's actors), their PosInfo naming the first man and the door KL_Door_1 of the grafted set.
import kl_fa, kl_gms, kl_scene
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_dm02_assault_1025 as AS
import kl_dm03a_swat_1025 as D3
from kl_prp import Prp

KICK_TOP, KICK_SQUAD = 'KL_Kick!1', 'KL_Kick!Door_1'
KICK_AT = 45.0              # s after the round start (GUESS: the crew needs about 40 s from the start to reach Door_1 at z 21910)
N_MEN = 3
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55
WAVE3 = 'OldWaves!Wave_3'


def kick_nodes(B, P):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), KICK_TOP)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    t = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'T_Start'))
    M.place(t, (0.0, 0.0, 0.0))
    me = R + KICK_SQUAD
    M.set(t, 'TriggerDelay2', {0: float(KICK_AT), 4: [me + BS + '10_Defend']})
    w3 = node(R + WAVE3)
    acts = [k for k in range(w3, sc.end[w3]) if sc.cls(k) == 'ZFFActor']
    top = FED.clone_built(M, B, w3, KICK_SQUAD.split('!')[0] + '!Door_1')
    top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
    M.place(top, (0.0, 0.0, 0.0))
    M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})          # parked until the timer names its first rout
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    names = ['Kick_%02d' % (j + 1) for j in range(N_MEN)]

    def defend(name, cells, nxt):
        d = top.add(M.clone('F07', sq2(KOW.FORM), name))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, p in enumerate(cells):
            pp = d.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, p[:3])
            refs.append(me + BS + name + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: nxt, 8: 1, 9: 0})
        return d
    defend('10_Defend', P['hold'], [me + BS + '20_KickDoor'])
    kick_src = 'FASpecials!merc_bot_squad!Squad#08' + BS + '021_KickDoorBehaviourRout_hangar_side_entrance#01'
    kr = top.add(M.clone('F03', R + kick_src, '20_KickDoor'))
    M.place(kr, (0.0, 0.0, 0.0))
    M.set(kr, 'KickDoorBehaviourRout', {0: [me + BS + '30_Defend'], 1: 1})
    pi = kr.add(M.clone('F03', R + kick_src + BS + 'KickDoorBehaviour_PosInfo', 'KickDoorBehaviour_PosInfo'))
    ab = P['back']
    M.place(pi, (ab[0], ab[1] + 14.0, ab[2]))                     # F03: 26 cm from its ArrowBack toward the door, 14 cm above (copied from dm03a)
    M.set(pi, 'KickDoorBehaviour_PosInfo', {0: me + BS + names[0], 1: R + D3.DOOR})
    defend('30_Defend', P['posts'], [])
    for j in range(N_MEN):
        a = acts[j % 2]
        e = P['park'][j]
        dx, dz = ab[0] - e[0], ab[2] - e[2]
        L = math.hypot(dx, dz) or 1.0
        grp = top.add(FED.clone_built(M, B, sc.parent[a], names[j]))
        M.place(grp, e[:3], KB.rot9(dx / L, dz / L))
        grp.add(FED.clone_built(M, B, a))
    return M, [clock, top], R + KICK_TOP + BS + 'T_Start'


def kick_squad(src, dst, log=print):
    """src zip -> dst zip with the KL_Kick squad (nothing removed: +3 actors, +1 squad). -> report dict."""
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + KICK_TOP):
        log('already holds %s: copied unchanged' % KICK_TOP)
        shutil.copyfile(src, dst)
        return None
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    big0 = {e: len(B[e]) for e in KB.BIG}
    a0, s0 = AS.census(sc)
    nav = KB.Nav(A.nav, links=True)
    P = D3.plan(B, nav, log)
    for c in P['park'] + P['hold'] + P['posts']:              # nobody else stands within 120 cm of a cell
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZFFActor':
                q = B.at(k)
                if math.dist((c[0], c[2]), (q[0], q[2])) < 120.0 and abs(c[1] - q[1]) < 150.0:
                    raise ValueError('cell (%d,%d) is within 120 cm of the actor %s' % (c[0], c[2], sc.path[k][-50:]))
    if a0 + N_MEN > ENGINE_ACTORS or s0 + 1 > ENGINE_SQUADS:
        raise ValueError('budget: %d / %d' % (a0 + N_MEN, s0 + 1))
    M, tops, start = kick_nodes(B, P)
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm01kick')
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [start]))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + N_MEN or fs != s0 + 1 or fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    log('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
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
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t in tops:
        ent(t, None)
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
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in tops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    if r3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
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
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    if big0 != {e: len(new[B.ext[e]]) for e in KB.BIG}:
        raise ValueError('a large block changed its size')
    work = tempfile.mkdtemp(prefix='dm01kick_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F01_Main.zip'), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        sealed = kl_fa_bank.seal(work, log=lambda *_: None)
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    log('  written %s: %d added, %d slot ids renumbered, members changed: %s; reverify %s' % (dst, len(order), moved, ' '.join(changed), problems[:3]))
    return dict(census=[a0, s0, fa, fs], slot_ids_moved=moved, sealed=sealed, members_changed=changed, start=start, at_s=KICK_AT,
                park=[[round(v) for v in c[:3]] for c in P['park']], hold=[[round(v) for v in c[:3]] for c in P['hold']],
                posts=[[round(v) for v in c[:3]] for c in P['posts']], back=[round(v) for v in P['back']], reverify=problems)


# ---------------------------------------------------------------- 2: the extinguishers hang on the wall
# Stock wall extinguishers (F08, read in work/w2.py): the Can's origin is 104 cm over the floor (14546 y 104 over its cabinet body at 0; 12697 y 504 over 400),
# the same ZHavokRigidBody as our floor cans; the cabinet's static Body holds it. The graft's cans stood on the floor 45 cm from the walk-mesh edge.
# Here each can is moved to 104 cm, back against the wall plane found by exact ray casts (third_party/anp/scripts/hvk_ray), and a small key-framed
# slab (a clone of the door leaf's slab shape, scaled) under it plays the cabinet's shelf. A spot whose wall is not flat, is a door, or is out of reach
# stays on the floor (the fallback), and the report says which.
import types, re
MOUNT_H = 104.0                 # cm, can origin over the floor (F08)
CAN_R = 7.6                     # cm, the can shape's radius (F04 shape 126: x -7.2..7.5, z -7.1..6.9) rounded up
WALL_GAP = 1.0                  # cm between the can and the wall
SHELF = (20.0, 3.0, 20.0)       # cm, the slab under the can (w, h, d); its top touches the can's base
HOLD_TOP = 'KL_Holder!1'
HOLDER_MODEL_FROM = 'DirectionBoxDummy05'     # a ZSTDOBJ of the can group with a model of this map (never drawn: a group-0 mesh no tree lists)
HOLDER_FLAGS = 0x201f2          # the stock key-framed static ZSTDOBJ's flags (F04 ventilator boxes, F03 light covers)


def _cast(C, o, seg, skip):
    return C.ray(o, seg, 0x20, skip=skip)


def wall_probe(C, can_xyz, zdir, skip, reach=140.0):
    """-> (ok, why, info). Exact casts toward the wall from the can's place at the mounting height: three lateral rays at two heights must all hit
    a vertical face, facing back at the can, within 3 cm of one another."""
    x, y, z = can_xyz
    zx, zz = zdir
    fl = C.ray((x, y + 60.0, z), (0.0, -160.0, 0.0), 0x20, skip=skip)
    floor = fl['hit'][1] if fl and abs(fl['hit'][1] - (y - 1.0)) <= 3.0 else y - 1.0      # the can stood 1 cm over the walk mesh; a hit far from that is not the floor
    ax = (zz, -zx)                                      # the can's local X in the plane
    hits = []
    for h in (MOUNT_H + 2.0, MOUNT_H + 40.0):
        for lat in (-8.0, 0.0, 8.0):
            o = (x + ax[0] * lat, floor + h, z + ax[1] * lat)
            r = _cast(C, o, (zx * reach, 0.0, zz * reach), skip)
            if not r:
                return False, 'no wall within %d cm at height %d' % (reach, h), None
            if abs(r['n'][1]) > 0.3 or r['n'][0] * zx + r['n'][2] * zz > -0.9:
                return False, 'face %s is not a wall facing the can (normal %s)' % (r['name'], tuple(round(v, 2) for v in r['n'])), None
            if 'door' in r['name'].lower():
                return False, 'the face is a door (%s)' % r['name'], None
            hits.append((r['frac'] * reach, r['name']))
    ds = [d for d, _n in hits]
    if max(ds) - min(ds) > 3.0:
        return False, 'the wall is not flat there (%.1f..%.1f cm)' % (min(ds), max(ds)), None
    # the place in front of the can must be clear (a man walks past): nothing within 40 cm in front of the new can at its height
    d = sum(ds) / len(ds)
    return True, 'ok', dict(floor=floor, dist=d, name=hits[0][1], spread=max(ds) - min(ds))


def ext_wall(src, dst, log=print):
    """src zip -> dst zip with every wall-eligible extinguisher mounted. -> report dict."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'third_party', 'anp', 'scripts'))
    import hvk_ray
    import kl_hvk, kl_interact_graft as IG
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + HOLD_TOP):
        log('already holds %s: copied unchanged' % HOLD_TOP)
        shutil.copyfile(src, dst)
        return None
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    big0 = {e: len(B[e]) for e in KB.BIG}
    top = sc.resolve(INTERACT)[0]
    groups = [k for k in range(top, sc.end[top]) if sc.cls(k) == 'ZGROUP' and re.match(r'KL_Ext_\d+$', sc.names[k])]
    if not groups:
        raise ValueError('no KL_Ext_n groups in KL_Interact!1')
    cans = {g: next(k for k in range(g + 1, sc.end[g]) if sc.cls(k) == 'ZHavokRigidBody') for g in groups}
    skip = {B.ents[c - 1].ref for c in cans.values()}
    C = hvk_ray.Collision(src)
    hvk = kl_hvk.Hvk(B['.HVK'])
    hrd = bytearray(B.files[B.ext['.hrd']])
    t2 = [kl_hvk.ref(i) for s in hvk.shapes if s.type == kl_hvk.RIGID for i in s.inst]
    S = types.SimpleNamespace(prp=sc, ents=B.ents)
    rep, mounted = [], []
    for g in groups:
        c = cans[g]
        e = B.ents[c - 1]
        p = struct.unpack_from('<3f', e.trans)
        rot = struct.unpack_from('<9f', e.rot)
        zdir = (rot[0], rot[2])                                  # the stored rows are the local Z, Y, X axes: row 0 = the can's +Z, toward its wall
        row = dict(group=sc.names[g], was=[round(v, 1) for v in p], zdir=[round(v, 2) for v in zdir])
        why0 = None
        for reach in (140.0, 260.0):                                # a wall close by first (any side, its own side first), then a farther one
            for cand in [zdir] + [dd_ for dd_ in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)) if math.dist(dd_, zdir) > 0.1]:
                ok, why, info = wall_probe(C, p, cand, skip, reach)
                if why0 is None:
                    why0 = why
                if ok:
                    break
            if ok:
                if cand != zdir:                                    # the wall is on another side: the can turns to face out from it
                    row['turned_from'] = [round(v, 2) for v in zdir]
                    zdir = cand
                break
        if not ok:
            why = 'original side: %s; no flat wall on any side within 260 cm' % why0
        if not ok:
            row.update(mounted=False, why=why)
            rep.append(row); log('  %s: stays on the floor: %s' % (sc.names[g], why))
            continue
        move = info['dist'] - (CAN_R + WALL_GAP)                   # cm along zdir
        new = (p[0] + zdir[0] * move, info['floor'] + MOUNT_H, p[2] + zdir[1] * move)
        d = tuple(new[a] - p[a] for a in range(3))
        # the records the can owns: its HVK instance and the .hrd line (positions in metres; checked equal before the edit)
        ref = e.ref
        turned = 'turned_from' in row
        if turned:                                                 # IG.make_extinguisher / IG.build: node rot = rows Z, Y, X; HVK columns = X, Y, Z
            rot9 = IG.stored_rot(*IG.can_axes(zdir))
            kl_graft.edit(sc.nodes[c], 'props', lambda us: AU.setv(sc, us, J.labels('dd', sc.cls(c)).index('ZGEOM[1]'), rot9))
            e.rot = struct.pack('<9f', *rot9) + e.rot[36:]
        done = 0
        for s in hvk.shapes:
            for j, inst in enumerate(s.inst):
                if kl_hvk.ref(inst) == ref:
                    if s.type != kl_hvk.RIGID:
                        raise ValueError('the can %s is not a rigid-body instance' % sc.names[g])
                    q = bytearray(inst)
                    old = struct.unpack_from('<3f', q, 0)
                    if max(abs(old[a] * 100.0 - p[a]) for a in range(3)) > 0.5:
                        raise ValueError('the HVK instance of %s is at %s, the entity at %s' % (sc.names[g], old, p))
                    struct.pack_into('<3f', q, 0, *(v / 100.0 for v in new))
                    if turned:
                        cx_, cy_, cz_ = IG.can_axes(zdir)
                        struct.pack_into('<9f', q, 12, *(col[r] for r in range(3) for col in (cx_, cy_, cz_)))
                    s.inst[j] = bytes(q)
                    done += 1
        hi = t2.index(ref)
        ho = struct.unpack_from('<3f', hrd, 28 * hi)
        if max(abs(ho[a] * 100.0 - p[a]) for a in range(3)) > 0.5:
            raise ValueError('the .hrd line of %s is at %s, the entity at %s' % (sc.names[g], ho, p))
        struct.pack_into('<3f', hrd, 28 * hi, *(v / 100.0 for v in new))
        if done != 1:
            raise ValueError('%s: %d HVK instances' % (sc.names[g], done))
        n = 0
        for k in range(g + 1, sc.end[g]):                          # every node below the group carries a world place (the group itself stays at 0)
            q = struct.unpack_from('<3f', B.ents[k - 1].trans)
            AU.place(S, k, pos=tuple(q[a] + d[a] for a in range(3)))
            n += 1
        row.update(mounted=True, now=[round(v, 1) for v in new], wall=info['name'], dist=round(info['dist'], 1), moved_nodes=n)
        rep.append(row); mounted.append((g, c, new))
        log('  %s: %s -> %s on %s (wall %.1f cm away, flat to %.1f cm)' % (sc.names[g], [round(v) for v in p], [round(v) for v in new], info['name'], info['dist'], info['spread']))
    if not mounted:
        shutil.copyfile(src, dst)
        log('no can could be mounted: copied unchanged')
        return dict(cans=rep, mounted=0)
    # ---- the shelves: new ZSTDOBJ nodes (hidden mesh, key-framed slab) under one new top group
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    dummy = next(k for k in range(groups[0], sc.end[groups[0]]) if sc.names[k] == HOLDER_MODEL_FROM)
    htop = FED.clone_built(M, B, groups[0], HOLD_TOP)
    htop.ctrls = []
    M.place(htop, (0.0, 0.0, 0.0))
    holders = []
    for g, c, new in mounted:
        n = int(sc.names[g].split('_')[-1])
        h = htop.add(FED.clone_built(M, B, dummy, 'Holder_%d' % n))
        base = (new[0], new[1] - SHELF[1], new[2])               # the slab's origin is its bottom centre; its top touches the can's base
        M.place(h, base)
        M.set(h, None, {'ZGEOM[3]': 0})                           # not hidden-flagged (a hidden node's hits are skipped in game, hvk_ray notes)
        h.flags = HOLDER_FLAGS
        h.group = 0
        holders.append((h, base))
    tops = [htop]
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm01ext')
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
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
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t in tops:
        ent(t, None)
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
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    moved = sum(1 for a, b in ids.items() if a != b)
    allp = [b for _h, b in holders]
    lo = tuple(min(p[a] for p in allp) - 400.0 for a in range(3))
    hi = tuple(max(p[a] for p in allp) + 400.0 for a in range(3))
    r3 = octn.rooms[0][3]
    if r3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree([(slot1[made[id(htop)]] + 2, lo, hi)], r3.origin, r3.scale))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
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
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    # ---- the slab: one key-framed shape (clone of the door leaf's), vertices remapped to a 20 x 3 x 20 cm box, bottom centre at the origin
    dd = IG.Donor.get(IG.DOOR_DONOR)
    ds = dd.hvk.shapes[IG.DOOR_SHAPE]
    leaf = dd.ent(IG.DOOR_LEAF)
    di = next(i for i in ds.inst if kl_hvk.ref(i) == leaf.ref)
    v = list(struct.unpack('<%df' % (len(ds.verts) // 4), ds.verts))
    if ds.type != kl_hvk.KEYFRAMED or len(v) != 24:
        raise ValueError('the door slab shape is not the 8-vertex key-framed box (%d floats)' % len(v))
    ext = [(min(v[a::3]), max(v[a::3])) for a in range(3)]
    tgt = [(-SHELF[0] / 200.0, SHELF[0] / 200.0), (0.0, SHELF[1] / 100.0), (-SHELF[2] / 200.0, SHELF[2] / 200.0)]
    for j in range(0, len(v), 3):
        for a in range(3):
            f = (v[j + a] - ext[a][0]) / (ext[a][1] - ext[a][0])
            v[j + a] = tgt[a][0] + f * (tgt[a][1] - tgt[a][0])
    news = []
    for h, base in holders:
        i = bytearray(di)
        struct.pack_into('<3f', i, 0, *(c / 100.0 for c in base))
        struct.pack_into('<9f', i, 12, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        struct.pack_into('<I', i, 0x30, made[id(h)].ref)
        news.append(bytes(i))
    sh = ds.clone(news, [])
    sh.verts = struct.pack('<%df' % len(v), *v)
    hvk.shapes.append(sh)
    hvk_bytes = hvk.serialize()
    if kl_hvk.Hvk(hvk_bytes).serialize() != hvk_bytes:
        raise ValueError('.HVK does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.HVK']], new[B.ext['.hrd']] = hvk_bytes, bytes(hrd)
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    if big0 != {e: len(new[B.ext[e]]) for e in KB.BIG}:
        raise ValueError('a large block changed its size')
    work = tempfile.mkdtemp(prefix='dm01ext_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F01_Main.zip'), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        sealed = kl_fa_bank.seal(work, log=lambda *_: None)
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    log('  written %s: %d cans mounted, %d slot ids renumbered, members changed: %s; reverify %s' % (dst, len(mounted), moved, ' '.join(changed), problems[:3]))
    return dict(cans=rep, mounted=len(mounted), slot_ids_moved=moved, members_changed=changed, sealed=sealed, reverify=problems)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'cars':
        import json
        print(json.dumps(cars(sys.argv[2], sys.argv[3]), indent=1, default=str))
    elif len(sys.argv) == 4 and sys.argv[1] == 'kick':
        print(json.dumps(kick_squad(sys.argv[2], sys.argv[3]), indent=1, default=str))
    elif len(sys.argv) == 4 and sys.argv[1] == 'ext':
        print(json.dumps(ext_wall(sys.argv[2], sys.argv[3]), indent=1, default=str))
    elif len(sys.argv) == 5 and sys.argv[1] == 'sound':
        print(json.dumps(sound(sys.argv[2], sys.argv[3], sys.argv[4]), indent=1, default=str))
    else:
        print(__doc__)
