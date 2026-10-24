"""kl_dm03a_swat_1025.py - DM03A bank (F07 slot): a SWAT squad that KICKS the installed kick door KL_Door_1, plus gas canisters in the garage.
Written 2026-10-25, OFFLINE only, nothing is run in the game. (re/dd_setpieces.md placement #4; wish: a Dog Days moment, enemies arrive
through a door, never appear in view, set-pieces where a level designer would put them.)

TWO JOBS, ONE ZIP (input = the live DM03A: kick doors + extinguishers installed, md5 SRC_MD5)
 1. GAS CANISTERS. Three stock Dog Days gas canisters (F07 'F07_Outside_EscapeAlley' FX0900_ALL_GasCanister_A_02: Can with BarrelEffects
    600 cm radius / 1000 damage, GeomActivator, hand box, the Explosion_Gas_S group with smoke, fire, flash, light, camera shake and sound)
    stand in the GARAGE (the room M03_A_Garage_AdoptRoomHack_01a that the heisters start in) beside the CoverBoxH cover pillars, 130..160 cm
    from them, a designer's 'shoot it when they hide behind it' place. The graft is kl_interact_graft.build driven with the canister donor
    (module globals swapped; the function body is the extinguisher's, make_gas below is make_extinguisher with the GeomActivator node 6140).
 2. THE DOOR SQUAD. KL_Door_1 (hinge -828,240,-6041; world frame: ArrowBack -943,-6043 on the corridor side, ArrowFront -784,-5938 on the
    room side) is the one installed door whose BOTH sides are on the walkable mesh part the crew is on (the other four stand on a cut-off
    island, part 1, asserted by the check). Wave_D08 of the bank's own police chain (3 men, a late street reinforcement at about 285 s) is
    REPLACED, so the budget stays 106 actors / 54 squads: 'KL_SWAT!Door_1' = three men of the same model, parked at the dead end of the
    corridor behind the door (250..330 cm from it, out of view of the room). At DOOR_AT seconds the squad is released: 10_Defend walks them to
    the door, KickDoorBehaviourRout (cloned from F03's squad 'Squad#08', its PosInfo names the first man and the door) kicks it, and
    30_Defend takes them into the room on the crew's side of it. The timer is a TriggerDelay2 in the AIMonitor round-start list
    (the bank has no alarm node: GUESS, a timer is the only trigger available).

GUESSES / UNPROVEN (each also in a code comment): (1) the bot-squad KickDoorBehaviourRout works for an ENEMY-team squad on a door grafted
from F03's PC0800 leaf (F03 uses it for heist-side bots; its SWAT squads use MiniCutsceneRout + KickDoorMonitor + an animation, not copied);
(2) PosInfo stands on the ArrowBack node (F03: 26 cm from it toward the door); (3) the door opens when the AI kick lands (the player-kick
controller on the grafted leaf also hears the AI kick: F03 proof only for its own leaves); (4) canister spots need cover to be where the
CoverBoxH boxes stand; (5) the canisters' model / HVK graft is the extinguisher's, only run for the donor change; (6) timing.

Usage (from tools/):
  python kl_dm03a_swat_1025.py build <in F07_Main.zip> <out F07_Main.zip> [--force]
  python kl_dm03a_swat_1025.py check <zip>
  python kl_dm03a_swat_1025.py stage <in F07_Main.zip> <out folder> [--rehearse <scratch>]
"""
import collections, json, math, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_interact_graft as IG
import kl_dm02_assault_1025 as AS
from kl_prp import Prp, units

BS = chr(92)
R = 'ROOT' + BS
SRC_MD5 = '3d4ae43a35e24459d0bf08d0cff87cab'      # live DM03A (kick doors + extinguishers installed, .before-1024interact = 89256d16)
TAG = '.before-1025dm03aswat'
GAS_TOP = 'KL_Gas!1'
SWAT_TOP = 'KL_SWAT!1'                            # the clock group (timer)
SQUAD = 'KL_SWAT!Door_1'
OLD_WAVE = 'Gameplay!bank_waves!Wave_D08'
DOOR = 'KL_Interact!1' + BS + 'KL_Door_1'
DOOR_AT = 75.0            # s after the round start (GUESS; the bank's lobby police come at 110 s, the crew has been in the garage for a minute)
N_MEN = 3
CLEAR = 30.0
ENGINE_ACTORS, ENGINE_SQUADS = 106, 55          # owner's cap for this pass (live: 106 / 54; engine-proven 99 / 55)
# gas canisters: floor y 200 of the garage; beside the CoverBoxH pillars H_01 (301,-5549), H_02 (850,-5549), H_04 (850,-5093)
GAS_SPOTS = [(301.0, 200.0, -5420.0), (800.0, 200.0, -5390.0), (700.0, 200.0, -5090.0)]
COVER = [(301.0, -5549.0), (850.0, -5549.0), (850.0, -5093.0)]
CREW_START = (500.0, 200.0, -4350.0)
GAS_DONOR = 'F07'
GAS_PARENT = BS.join(['ROOT', 'Locations/F07/F07_Locations.zip', 'Locations/F07/F07_LOC_Outside.zip', 'F07_Outside_EscapeAlley'])
GAS_CAN = 6142
GAS_ACT = 6140
GAS_KEEP = [6142, 6140, 6141] + list(range(5714, 5732))
GAS_DROP = ('FX0900_ALL_GasCanister_A_02!ShatterTrigger',)


# ------------------------------------------------------------------ job 1: the canisters
def make_gas(M, B, don, n, at, tmpl_ok):
    """IG.make_extinguisher for the gas canister: the activator is node 6140 (F04's extinguisher: 5269), the group KL_Gas_n."""
    import kl_fa_cover as CV
    gk = CV.group_form(B)
    grp = CV._node(M, B, gk, 'KL_Gas_%d' % n)
    M.place(grp, (0.0, 0.0, 0.0))
    newp = IG.TOP_PATH + BS + grp.name + BS
    old = IG.EXT_PARENT + BS
    rn = lambda s: (newp + s[len(old):]) if s.lower().startswith(old.lower()) else s
    can0 = struct.unpack_from('<3f', don.ent(IG.EXT_CAN).trans)
    d = tuple(at[i] - can0[i] for i in range(3))
    byk = {}
    for k in IG.EXT_KEEP:
        nd = IG.clone(M, don, k, don.sc.names[k], rn)
        byk[k] = nd
        par = don.sc.parent[k]
        (byk[par] if par in byk else grp).add(nd)
        if don.sc.parent[k] not in byk:
            IG.shift(M, nd, d)
    dropped = lambda s: any(x.lower() in s.lower() for x in IG.EXT_DROP)
    can = byk[IG.EXT_CAN]
    cuts = IG.list_filter(M, can, None, 'ZHavokRigidBody[13]', lambda s: not dropped(s))
    cuts += IG.list_filter(M, byk[GAS_ACT], 'ActivateGeom', 1, lambda s: not dropped(s))
    gone = []
    for k in list(byk):
        nd = byk[k]
        if nd.tid == 0x2000ff:
            nm = IG._emitter_template(M, nd)
            if nm and nm.lower() not in tmpl_ok:
                gone.append(nd)
    for nd in gone:
        for k, v in list(byk.items()):
            if v is nd:
                del byk[k]
        for v in grp.walk():
            if nd in v.kids:
                v.kids.remove(nd)
    import kl_gms
    for nd in byk.values():                      # GUESS: the donor's explosion lights keep no object list (a light's list may only hold non-lights;
        if kl_gms.category(nd.tid) == 2:          # IG.build would give them the nearest MAP object's LIGHT list, which the loader check refuses)
            nd.links = None
    return grp, can, byk, [g.name for g in gone], cuts


def canisters(src, dst, log=print):
    """src -> dst: three gas canisters (kl_interact_graft.build with the module globals swapped, restored after)."""
    B = KB.Built(src)
    nav = KB.Nav(B.scene.nav, links=True)
    for x, y, z in GAS_SPOTS:
        h = nav.at(x, y, z, dy=60)
        if h is None or nav.part[h[0]] != KB.stations(B, nav)['home']:
            raise ValueError('canister spot (%d,%d,%d) is not on the crew\'s part of the mesh' % (x, y, z))
        if abs(h[1] - y) > 3.0:
            raise ValueError('canister spot (%d,%d,%d): floor is at %.1f' % (x, y, z, h[1]))
        if math.dist((x, z), (CREW_START[0], CREW_START[2])) < 600.0:
            raise ValueError('canister spot (%d,%d) is within 6 m of the crew start' % (x, z))
        if min(math.dist((x, z), c) for c in COVER) > 200.0:
            raise ValueError('canister spot (%d,%d) is not beside a cover pillar' % (x, z))
        for k in range(1, len(B.sc.nodes)):          # nothing that moves, burns or pays within 120 cm
            if any(B.sc.p.key(nm) in ('ZHavokRigidBody', 'OnlineMoneyContainer', 'BarrelEffects') for nm, _b in B.sc.nodes[k]['ctrls']):
                p = B.at(k)
                if math.dist((x, z), (p[0], p[2])) < 120.0 and abs(p[1] - y) < 150.0:
                    raise ValueError('canister spot (%d,%d): %s within 120 cm' % (x, z, B.sc.path[k][-60:]))
    save = {k: getattr(IG, k) for k in ('TOP', 'TOP_PATH', 'EXT_DONOR', 'EXT_PARENT', 'EXT_CAN', 'EXT_KEEP', 'EXT_DROP', 'EXT_PREFIX', 'EXT_TREE0', 'make_extinguisher')}
    try:
        IG.TOP, IG.TOP_PATH = GAS_TOP, R + GAS_TOP
        IG.EXT_DONOR, IG.EXT_PARENT, IG.EXT_CAN = GAS_DONOR, GAS_PARENT, GAS_CAN
        IG.EXT_KEEP, IG.EXT_DROP, IG.EXT_PREFIX, IG.EXT_TREE0 = GAS_KEEP, GAS_DROP, 'FX0900_ALL_GasCanister_A_02!', []
        IG.make_extinguisher = make_gas
        return IG.build(src, dst, ext=len(GAS_SPOTS), doors=(), spots=[s + (0.0,) for s in GAS_SPOTS], log=log)
    finally:
        for k, v in save.items():
            setattr(IG, k, v)


# ------------------------------------------------------------------ job 2: the door squad
def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


def plan(B, nav, log):
    sc = B.sc
    home = KB.stations(B, nav)['home']
    kd = one(sc, DOOR)
    kids = {sc.names[j]: j for j in range(kd, sc.end[kd])}
    ab, af = B.at(kids['KickDoor_ArrowBack_01']), B.at(kids['KickDoor_ArrowFront_01'])
    hb, hf = nav.at(ab[0], ab[1], ab[2], dy=60), nav.at(af[0], af[1], af[2], dy=120)
    if not hb or nav.part[hb[0]] != home:
        raise ValueError('ArrowBack of KL_Door_1 is not on the crew\'s mesh part')
    cands = lambda p, r: [c for c in nav.around(p, r, home, step=40.0, dy=60.0) if nav.clearance(c[0], c[1], c[2]) >= CLEAR]
    # parked cells: corridor side, 180..340 cm from the door, south of the arrow (the dead end), 40+ cm apart
    nrm = (af[0] - ab[0], af[2] - ab[2])
    back_side = lambda c: (c[0] - ab[0]) * nrm[0] + (c[2] - ab[2]) * nrm[1] < -50.0 * math.hypot(*nrm)
    far = [c for c in cands(ab, 400.0) if back_side(c) and 150.0 <= math.dist(c[:3], ab) <= 400.0 and c[2] < ab[2] - 100.0]
    far.sort(key=lambda c: abs(math.dist(c[:3], ab) - 250.0))
    park = []
    for c in far:
        if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= 30.0 for q in park):
            park.append(c)
        if len(park) == N_MEN:
            break
    # hold cells beside the door
    near = [c for c in cands(ab, 140.0) if math.dist(c[:3], ab) <= 130.0 and back_side(c)]
    near.sort(key=lambda c: math.dist(c[:3], ab))
    hold = []
    for c in near:
        if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= 30.0 for q in hold):
            hold.append(c)
        if len(hold) == N_MEN:
            break
    # room cells: the crew's side of the door, 250..650 cm from the front arrow, roomy, 150+ cm apart, nearest the garage last
    room = [c for c in cands(af, 650.0) if 250.0 <= math.dist(c[:3], af) <= 650.0 and nav.clearance(c[0], c[1], c[2]) >= 60.0]
    room.sort(key=lambda c: math.dist(c[:3], af))
    posts = []
    for c in room:
        if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= 150.0 for q in posts):
            posts.append(c)
        if len(posts) == N_MEN:
            break
    if min(len(park), len(hold), len(posts)) < N_MEN:
        raise ValueError('cells found: park %d hold %d posts %d' % (len(park), len(hold), len(posts)))
    # the posts are reached from the door side only through the door (the room cells are on the crew's mesh part: asserted); the route
    # from the parked cells to the posts over the mesh alone is the long way round (reported)
    a = (park[0][0], park[0][1], park[0][2], park[0][3])
    r = nav.path(a, posts[0][:3] + (posts[0][3],))
    log('  door %s: back %s front %s; park %s; hold %s; posts %s; mesh-only walk from the park to post 1: %s cm' % (
        DOOR[-6:], [round(v) for v in ab], [round(v) for v in af], [(round(c[0]), round(c[2])) for c in park],
        [(round(c[0]), round(c[2])) for c in hold], [(round(c[0]), round(c[2])) for c in posts], 'none' if r is None else round(r[1])))
    return dict(back=ab, front=af, park=park, hold=hold, posts=posts, walk=None if r is None else r[1], door=kd)


def make_nodes(B, P):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), SWAT_TOP)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    t = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'T_Start'))
    M.place(t, (0.0, 0.0, 0.0))
    me = R + SQUAD
    M.set(t, 'TriggerDelay2', {0: float(DOOR_AT), 4: [me + BS + '10_Defend']})
    old = node(R + OLD_WAVE)
    acts = [k for k in range(old, sc.end[old]) if sc.cls(k) == 'ZFFActor']
    if len(acts) != N_MEN or sum(1 for nm, _b in sc.nodes[old]['ctrls'] if sc.p.key(nm) == 'ZSquadScript') != 1:
        raise ValueError('%s: %d actors' % (OLD_WAVE, len(acts)))
    top = FED.clone_built(M, B, old, SQUAD)
    top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
    M.place(top, (0.0, 0.0, 0.0))
    M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})          # parked until its rout is named (OldWaves! form)
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    s4 = KB.Maker.level('F03')[0]
    f3 = lambda tail: s4.resolve([p for p in (s4.path[k] for k in range(1, len(s4.names)) if s4.path[k]) if p.endswith(tail)][0])[0]
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
    M.place(pi, (ab[0], ab[1] + 14.0, ab[2]))                       # F03: 26 cm from its ArrowBack toward the door, 14 cm above the door's y
    M.set(pi, 'KickDoorBehaviour_PosInfo', {0: me + BS + names[0], 1: R + DOOR})
    defend('30_Defend', P['posts'], [])
    for j, a in enumerate(acts):
        e = P['park'][j]
        dx, dz = ab[0] - e[0], ab[2] - e[2]
        L = math.hypot(dx, dz) or 1.0
        grp = top.add(FED.clone_built(M, B, sc.parent[a], names[j]))
        M.place(grp, e[:3], KB.rot9(dx / L, dz / L))
        grp.add(FED.clone_built(M, B, a))
    return M, [clock, top]


def squads(src, dst, log=print):
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + SQUAD):
        log('%s already holds %s: copied unchanged' % (src, SQUAD))
        shutil.copyfile(src, dst)
        return None
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
    big0 = {e: len(B[e]) for e in KB.BIG}
    a0, s0 = AS.census(sc)
    nav = KB.Nav(A.nav, links=True)
    P = plan(B, nav, log)
    gone_top = one(sc, OLD_WAVE)
    ga, gs = AS.census(sc)[0], 0
    removed = [gone_top]
    gone_nodes = set(range(gone_top, sc.end[gone_top]))
    if a0 - N_MEN + N_MEN > ENGINE_ACTORS or s0 > ENGINE_SQUADS:
        raise ValueError('budget: %d / %d' % (a0, s0))
    M, tops = make_nodes(B, P)
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops() if t not in set(removed)] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm03aswat')
    # ---- references into the removed squad (Go_D08's list): cut the dead entries
    dead = []
    for k, holder, field, s, hit in J.references(sc):
        if not hit or k < 0 or k in gone_nodes:
            continue
        tgt = sc.resolve(s)
        if tgt and tgt[0] in gone_nodes:
            dead.append(k)
    dead, cut = sorted(set(dead)), 0
    for k in dead:
        kj = Jn.resolve(sc.path[k])
        if len(kj) != 1:
            raise ValueError('%s: %d nodes in the joined tree' % (sc.path[k], len(kj)))
        kj = kj[0]
        for i in [None] + list(range(len(Jn.nodes[kj]['ctrls']))):
            def fn(us):
                nonlocal cut
                for j, u in enumerate(us):
                    if u[0][0] == 0x04 and len(u) > 1 and u[1][0] == 0x0c:
                        live = [x for x in u[1:] if Jn.p.key(x)[:5].upper() != 'ROOT' + BS or Jn.resolve(Jn.p.key(x))]
                        cut += len(u) - 1 - len(live)
                        us[j] = [(0x04, struct.pack('<I', len(live)))] + live
                    elif u[0][0] == 0x0c and Jn.p.key(u[0])[:5].upper() == 'ROOT' + BS and not Jn.resolve(Jn.p.key(u[0])):
                        us[j] = [kl_fa._str(Jn, '')]
                        cut += 1
            kl_fa.edit(Jn, kj, i, fn)
    log('  references into %s: %d holders (%s), %d entries cut' % (OLD_WAVE, len(dead), ', '.join(sc.names[k] for k in dead[:4]), cut))
    # ---- the AIMonitor round-start list
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    start = R + SWAT_TOP + BS + 'T_Start'
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [start]))
    # ---- the grafted canisters' sound references name objects of F07's bank, not DM03A's .SND: set to 0 (silent canisters; GUESS: no sound
    # object of this level's bank is the gas explosion, borrowing another would play the wrong sound)
    import kl_snd
    objs = kl_snd.Snd('dd', B.files[B.ext['.SND']]).kind
    sch = J.schema('dd')
    zeroed = 0
    for k in range(1, len(Jn.nodes)):
        if GAS_TOP not in Jn.path[k]:
            continue
        for cls, holder, key in kl_graft.objects(Jn, k):
            hot = [i for i, f in enumerate(sch.fields(cls)) if f.type in kl_graft.SOUND_TYPES and f.kind == 'I']
            if not hot:
                continue
            def fz(us, hot=hot):
                nonlocal zeroed
                for i in hot:
                    v = kl_graft.u32(us[i][0])
                    if v and v not in objs and v != kl_snd.LS_SOUND:
                        us[i][0] = (us[i][0][0], bytes(4))
                        zeroed += 1
            kl_graft.edit(holder, key, fz)
    stray0 = 0
    for k in range(1, len(Jn.nodes)):
        if GAS_TOP in Jn.path[k]:
            continue
        for cls, holder, key in kl_graft.objects(Jn, k):
            for f, u in zip(sch.fields(cls), units(kl_graft.get_obj(holder, key)[1:-1])):
                if f.type in kl_graft.SOUND_TYPES and f.kind == 'I' and kl_graft.u32(u[0]):
                    v = kl_graft.u32(u[0])
                    stray0 += v not in objs and v != kl_snd.LS_SOUND
    log('  %d sound references of the canisters set to 0 (not in this level .SND)' % zeroed)
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('over the budget: %d actors / %d squads' % (fa, fs))
    log('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
    # ---- .gms / .buf: remove, then add (the freed REF ids are reused)
    slot0 = A.slots()
    gone_ents = set()
    for t in removed:
        gone_ents.update(B.ents[t - 1].walk())
    free = sorted(e.ref for e in gone_ents)
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    for t in removed:
        A.remove(B.ents[t - 1])
    made = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
        if free:
            e.ref = free.pop(0)
        else:
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
    gids = {slot0[e] + 2 for e in gone_ents}
    elsewhere = sum(1 for r, room in enumerate(octx.rooms) for ti, t in enumerate(room) if t is not None and (r, ti) != (0, 3) for it in t.items if it[0] in gids)
    if elsewhere:
        raise ValueError('%d room-tree items outside the root group tree name a removed entity' % elsewhere)
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, gids), O.remap_ids(rmi, ids, gids), O.remap_ids(rmc, ids, gids)
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
    work = tempfile.mkdtemp(prefix='dm03aswat_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, os.path.basename(dst)), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        sealed = kl_fa_bank.seal(work, log=lambda *_: None)
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        base = '%d sound references name no object of the .SND' % stray0     # already so in the input (measured above), not this pass's
        problems = [x for x in problems if x != base]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep = collections.OrderedDict(entities_before=len(B.ents), entities=len(allents), removed=len(gone_ents), added=len(order), census=[a0, s0, fa, fs],
                                  refs_cut=cut, slot_ids_moved=moved, prm_roots_repointed=repointed, sealed=sealed, members_changed=changed, start=start,
                                  door_at_s=DOOR_AT, park=[[round(v) for v in c[:3]] for c in P['park']], hold=[[round(v) for v in c[:3]] for c in P['hold']],
                                  posts=[[round(v) for v in c[:3]] for c in P['posts']], back_arrow=[round(v) for v in P['back']],
                                  front_arrow=[round(v) for v in P['front']], mesh_walk_cm=P['walk'])
    log('  squad stage: %d entities out, %d in, %d slot ids renumbered, members %s' % (len(gone_ents), len(order), moved, ' '.join(changed)))
    return rep


# ------------------------------------------------------------------ build / check
def build(src, dst, force=False, log=print):
    h = AS.md5(src)
    if h != SRC_MD5 and not force:
        raise SystemExit('refusing: %s md5 %s is not the pinned %s (use --force)' % (src, h, SRC_MD5))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    sc = KB.Built(src).sc
    if sc.resolve(R + GAS_TOP) and sc.resolve(R + SQUAD):
        shutil.copyfile(src, dst)
        log('%s already holds the pass: copied unchanged' % src)
        return None
    tmp = tempfile.mkdtemp(prefix='dm03aswat1_')
    try:
        mid = os.path.join(tmp, os.path.basename(dst))
        g = canisters(src, mid, log)
        r = squads(mid, dst, log)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r = r or collections.OrderedDict()
    r['source_md5'], r['out_md5'] = h, AS.md5(dst)
    r['canisters'] = [list(s) for s in GAS_SPOTS]
    r['canister_members_changed'] = (g or {}).get('changed')
    log('written %s md5 %s' % (dst, r['out_md5']))
    return r


def check(zp, log=print):
    B = KB.Built(zp)
    sc = B.sc
    bad = 0

    def say(ok, msg):
        nonlocal bad
        bad += (not ok)
        log('%s %s' % ('ok  ' if ok else 'FAIL', msg))
    a, s = AS.census(sc)
    say(a <= ENGINE_ACTORS and s <= ENGINE_SQUADS, 'budget %d actors / %d squads (cap %d / %d)' % (a, s, ENGINE_ACTORS, ENGINE_SQUADS))
    say(not sc.resolve(R + OLD_WAVE), '%s is gone (replaced by the door squad)' % OLD_WAVE)
    nav = KB.Nav(B.scene.nav, links=True)
    home = KB.stations(B, nav)['home']
    top = sc.resolve(R + SQUAD)
    say(len(top) == 1, 'squad %s present' % SQUAD)
    if top:
        t = top[0]
        men = [j for j in range(t, sc.end[t]) if sc.cls(j) == 'ZFFActor']
        say(len(men) == N_MEN, '%d men' % len(men))
        say(all(nav.at(*B.at(j), dy=60) and nav.part[nav.at(*B.at(j), dy=60)[0]] == home for j in men), 'the parked men stand on the crew\'s mesh part')
        kd = one(sc, DOOR)
        kids = {sc.names[j]: j for j in range(kd, sc.end[kd])}
        ab = B.at(kids['KickDoor_ArrowBack_01'])
        say(all(math.dist(B.at(j), ab) > 150.0 for j in men), 'the men stand 150+ cm from the door (out of the room)')
        pos = [j for j in range(t, sc.end[t]) if sc.names[j].startswith('Pos#')]
        say(len(pos) == 2 * N_MEN and all(nav.at(*B.at(j), dy=60) for j in pos), '%d Pos nodes, all on the mesh' % len(pos))
        pi = [j for j in range(t, sc.end[t]) if sc.names[j] == 'KickDoorBehaviour_PosInfo']
        say(len(pi) == 1, 'one KickDoorBehaviour_PosInfo')
        if pi:
            v = [kl_fa.value(sc, u) for u in units(sc.nodes[pi[0]]['ctrls'][0][1][1:-1])]
            say(v[1] == R + DOOR and sc.resolve(v[0]) and sc.resolve(v[1]), 'PosInfo names the first man and KL_Door_1 (%s)' % [str(x)[-34:] for x in v[:2]])
        dead = []
        for j in range(t, sc.end[t]):
            for nm, body in sc.nodes[j]['ctrls']:
                for u in units(body[1:-1]):
                    v = kl_fa.value(sc, u)
                    for x in (v if isinstance(v, list) else [v]):
                        if isinstance(x, str) and x.startswith(R) and not sc.resolve(x):
                            dead.append((sc.path[j][-40:], x[-50:]))
        say(not dead, 'every reference of the squad resolves (%s)' % dead[:3])
    mon = sc.resolve(KOW.MONITOR)[0]
    say(R + SWAT_TOP + BS + 'T_Start' in KOW.values(sc, mon, 'AIMonitor')[KOW.START_LIST], 'AIMonitor round-start list names T_Start')
    say(len(sc.resolve(R + SWAT_TOP + BS + 'T_Start')) == 1, 'timer present')
    isl = [n for n in ('KL_Door_2', 'KL_Door_3', 'KL_Door_4', 'KL_Door_5') if sc.resolve(R + 'KL_Interact!1' + BS + n)]
    say(len(isl) == 4, 'the four other doors are still there (unwired: cut-off island)')
    gas = sc.resolve(R + GAS_TOP)
    say(len(gas) == 1, 'gas top present')
    cans = [k for k in range(1, len(sc.nodes)) if GAS_TOP in sc.path[k] and sc.names[k].endswith('!Can_A')]
    say(len(cans) == len(GAS_SPOTS), '%d canisters' % len(cans))
    for k in cans:
        p = B.at(k)
        h = nav.at(p[0], p[1] + 1, p[2], dy=60)
        say(h is not None and nav.part[h[0]] == home, 'canister at (%d,%d,%d) on the crew\'s mesh part' % tuple(p))
        say(math.dist((p[0], p[2]), (CREW_START[0], CREW_START[2])) > 600.0, '  more than 6 m from the crew start')
    say(sc.resolve(R + 'KL_Interact!1') != [], 'KL_Interact!1 (extinguishers, doors) intact')
    return bad


# ------------------------------------------------------------------ installer (kl_dm02_assault_1025's, renamed)
PS1 = AS.PS1.replace('assault.json', 'swat.json').replace('assault.ps1', 'swat.ps1').replace("'%s'" % AS.TAG, "'%s'" % TAG).replace(
    'SWAT shutter assault (tools/kl_dm02_assault_1025.py, 2026-10-25)', 'DM03A SWAT kick-door squad + gas canisters (tools/kl_dm03a_swat_1025.py, 2026-10-25)').replace(
    'DM02 mall', 'DM03A bank').replace('Chained on shops A: the live md5 must be exactly the pinned one.', 'Chained on the installed kick doors / extinguishers: the live md5 must be exactly the pinned one.')
BAT = AS.BAT.replace('assault.ps1', 'swat.ps1')


def _ps(d, game, undo=False):
    sp = os.path.join(d, 'swat_scratch.ps1')
    txt = open(os.path.join(d, 'swat.ps1'), newline='').read().splitlines()
    with open(sp, 'w', newline='') as fh:
        fh.write((chr(13) + chr(10)).join(l for l in txt if 'Get-Process kl2' not in l))
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', sp, '-Game', game]
    if undo:
        a.append('-Undo')
    try:
        r = subprocess.run(a, capture_output=True, text=True)
    finally:
        os.remove(sp)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    old = AS.md5(src)
    if old != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (old, SRC_MD5))
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, 'F07_Main.zip')
    rep = build(src, z, log=log)
    if rep is None:
        raise SystemExit('input already holds the pass')
    new = AS.md5(z)
    man = dict(m='DM03A', f='F07_Main.zip', variant='-', old=old, new=new, tag=TAG)
    with open(os.path.join(out, 'swat.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'swat.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL dm03a swat.bat', ''), ('UNDO dm03a swat.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(src, out, man, scratch, log)
    return 0


def rehearse(src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', 'DM03A', 'F07_Main.zip')
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    log('rehearsal target: ' + live)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    t = _ps(d, g); log(t); assert 'installed' in t and AS.md5(live) == man['new'], t
    assert os.path.isfile(live + TAG) and AS.md5(live + TAG) == man['old']
    t = _ps(d, g, True); log(t)
    assert AS.md5(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    t = _ps(d, g); assert AS.md5(live) == man['new']
    t = _ps(d, g); assert 'already installed' in t, t
    t = _ps(d, g, True); assert AS.md5(live) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = _ps(d, g); log(t); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.copy2(src, live)
    log('rehearsal ok (install, undo byte-identical, reinstall same md5, wrong live md5 refused)')
    shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    force = '--force' in a
    if force:
        a.remove('--force')
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('build', 'check', 'stage'):
        print(__doc__)
        return 2
    if a[0] == 'check':
        return 1 if check(a[1]) else 0
    if a[0] == 'build':
        build(a[1], a[2], force)
        return 0
    return stage(a[1], a[2], opt('--rehearse'))


if __name__ == '__main__':
    sys.exit(main())
