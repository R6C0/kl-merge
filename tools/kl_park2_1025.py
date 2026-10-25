#!/usr/bin/env python3
"""
kl_park2_1025.py - DM06B "A Walk in the Park II" (Dog Days slot F02, campaign level M06_A): the REDESIGN pass, 2026-10-25.
Design: re/park2_redesign_1025.md.  OFFLINE only: nothing here installs or launches anything.

    python kl_park2_1025.py build <in F02_Main.zip> <out F02_Main.zip>
    python kl_park2_1025.py stage <in F02_Main.zip> <out folder> [--rehearse <scratch>]
                              build + md5-chained INSTALL/UNDO (.bat + .ps1 + park2.json) and a rehearsal on a scratch game folder

CHAIN (every step md5-pinned, the first on the live DM06B zip 64bb5dc9)
  1. kl_interact_graft.build   4 wall extinguishers (F04 can) on the walk mesh, no doors (the map has none that fit)
  2. kl_dm01b_gas_1025.build   4 fuel cans on the plaza (F03 FuelCan, stock gas explosion); this step now tolerates a map WITHOUT .hrd
  3. park()                    the REDESIGN (below)
  4. kl_dm02_mall_1025.resound the graft nodes' sound references re-pointed BY NAME into DM06B's own bank

park(): WHAT CHANGES
  * the crew starts on the HIGHWAY (the ring road, west arc -117..-124 deg, the part of the mesh the park is connected to): 8 START rows, 4 TRAITOR,
    the UCC copies, the team-mode TEAM_MERC set; the team-mode start camera follows.  They then go ring -> stairs -> garden -> plaza -> causeway ->
    pagoda (the loot) and back to the van on the ring (ExitLootArea moves to the van's stop).
  * the trigger roles are re-laid for the reversed route (the stock FA layer assumed pagoda -> stairs -> ring):
      tb_LEFT_TheySpotYou   -> the STAIRS' FOOT (first thing met):  the garden flankers + the stair sniper and the 04 squad
      tb_RIGHT_TheySpotYou  -> the pagoda's loot room (the end of the run): the ALARM (van timer, gate) as before
      KL_Park!PlazaBox      NEW, the garden's north edge (z -3150): the PLAZA AMBUSH (3 police squads + 2 sniper nests, all parked until then)
  * ambush = 9 police (3 squads of 3: cover line, flankers, a shotgun-side row at the causeway mouth) clones of the ring police men, and 2 snipers on
    the pagoda terrace (clones of the campaign's own sniper squad, 5000 hp, vision factor from its Alert modifier)
  * backstop timer 240 -> 300 s (the loot route is about 20,000 units long)
Budget (engine-proven 99 actors / 55 squads): live 58 / 38 -> 69 / 43 plus nothing for the grafted props.

GUESSES (each also in a code comment): the plaza trigger box position (the mesh has gaps at z -3000..-3300), that the bots' planner copes with a ring start,
the parked-squad wake pattern for cloned sniper squads (names both the Alert modifier and the Defend rout), sight lines of the snipers, the round length.
NOT DONE: shootable vans (needs a hook change), parked police cars, barriers / dumpsters / kick doors (no prop donor chain proven for them here),
DD campaign sound carry-over beyond what the grafted props already bring.
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_interact_graft as IG
import kl_dm01b_gas_1025 as GS
import kl_dm02_mall_1025 as MALL
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
SRC_MD5 = '64bb5dc9ee15501904cff612dbea592d'     # the live DM06B zip (2026-10-25)
TAG = '.before-1025park2'
MAP, FILE = 'DM06B', 'F02_Main.zip'
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55
C0, C1 = 0.0, -100.0

# ---- the highway start (re/park2_redesign_1025.md section 1; MEASURED on the nav mesh, all five probes inside it)
START = [(-6417, 2379, -5205), (-6309, 2383, -5338), (-6198, 2387, -5469), (-6084, 2391, -5597),
         (-6558, 2379, -5317), (-6448, 2382, -5453), (-6334, 2387, -5587), (-6218, 2391, -5718)]
TRAITOR = [(-5913, 2400, -5911), (-5811, 2405, -6013), (-5706, 2408, -6113), (-5601, 2411, -6212)]
TEAM_MERC = [(-6700, 2368, -4879), (-6616, 2372, -4995), (-6529, 2375, -5110), (-6783, 2364, -4762),
             (-6798, 2368, -4949), (-6712, 2371, -5067), (-6625, 2375, -5183), (-6881, 2362, -4829)]
FACE_TO = (106.0, -10934.0)                       # the stair tower's top: they look along the road towards it
STOP = (-2572.0, 2498.0, -7933.0)                 # the van's stop
STAIRS_FOOT = (-1.0, 580.0, -10940.0)
CAM_A = ((-6000.0, 2700.0, -5000.0), (-6300.0, 2385.0, -5400.0))   # GUESS: over the START rows / the point looked at

# ---- trigger roles
FF = R + 'Gameplay!010_FirstFight!'
WALK_BOX, FLOOR_BOX = FF + 'tb_LEFT_TheySpotYou', FF + 'tb_RIGHT_TheySpotYou'
BACKSTOP_TIMER = FF + 'RivalMercVan!Timer'
BACKSTOP_S = 300.0                                # was 240 (GUESS: the loot route is about 20,000 units)
STAIRS_BOX = ((STAIRS_FOOT[0], STAIRS_FOOT[1] + 100.0, STAIRS_FOOT[2]), (400.0, 150.0, 300.0))
ALARM_BOX = ((800.0, 700.0, 2150.0), (450.0, 150.0, 80.0))     # GUESS: the loot room's south edge (EnterLootArea box is x 350..1250 z 2160..2560)
PLAZA_BOX = ((700.0, 230.0, -3150.0), (1900.0, 200.0, 150.0))  # GUESS: the garden's north edge; the mesh has gaps at z -3000..-3300, so wide
EXIT_BOX = ((STOP[0], STOP[1] + 120.0, STOP[2]), (300.0, 150.0, 300.0))
GE = R + 'Gameplay!Enemy!02_JapaneseGarden!'
SNIPER_SQ = GE + '01_Squad_Sniper'
FLOOR_SQUADS = [SNIPER_SQ + BS + '03_DefendBehaviour', GE + '04_RetoMoto_Squad' + BS + '10_DefendBehaviour']
ALARM_KEEP = [FF + 'RivalMercs!DisableVisionBlocker!Timer', R + 'Gameplay!RunToEscape!RunToEscapeGate' + BS + 'Way#01']
RING_COPS = R + 'Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left'

# ---- the ambush (plain mesh points, snapped onto the main part; cover quality is not checked: GUESS)
COPS = collections.OrderedDict([
    ('PlazaA', [(420.0, 220.0, -2150.0), (700.0, 220.0, -2250.0), (1000.0, 220.0, -2200.0)]),
    ('PlazaB', [(1250.0, 220.0, -2000.0), (1400.0, 220.0, -2150.0), (300.0, 220.0, -2000.0)]),
    ('PlazaCauseway', [(550.0, 220.0, -1850.0), (850.0, 220.0, -1850.0), (1150.0, 220.0, -1850.0)])])
SNIPERS = collections.OrderedDict([('Nest1', (971.0, 583.0, 897.0)), ('Nest2', (695.0, 596.0, 1075.0))])
NEW_GROUPS = 'KL_Park!'
SNAP_RADIUS, POST_GAP = 260.0, 120.0


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def census(sc):
    a = s = 0
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor':
            a += 1
        s += sum(1 for nm, _b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'ZSquadScript')
    return a, s


def snap(nav, part, p, taken, why):
    """The mesh cell of `part` nearest to p (within SNAP_RADIUS) with the clearance KB.CLEAR, POST_GAP from every point already taken."""
    best = None
    for c in nav.around(p, SNAP_RADIUS, part, step=20.0, dy=150.0):
        if nav.clearance(c[0], c[1], c[2]) < KB.CLEAR or any(math.hypot(c[0] - q[0], c[2] - q[2]) < POST_GAP for q in taken):
            continue
        d = math.hypot(c[0] - p[0], c[2] - p[2])
        if best is None or d < best[0]:
            best = (d, c)
    if best is None:
        raise ValueError('%s: no mesh cell within %g of %s' % (why, SNAP_RADIUS, p))
    return (float(best[1][0]), float(best[1][1]), float(best[1][2]))


# ------------------------------------------------------------------ the new nodes
def make_nodes(B, nav, part, log):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    tops, rep, taken = [], collections.OrderedDict(), []
    # --- police: 3 parked squads of 3 (the OldWaves!/Assault form: ZSquadScript parked, one Defend rout with a Pos per man)
    tmpl = node(RING_COPS)
    men = [k for k in range(tmpl, sc.end[tmpl]) if sc.cls(k) == 'ZFFActor']
    if not men:
        raise ValueError('the ring police squad has no men')
    defend_t = node(RING_COPS + BS + '10_Defend')
    pos_t = node(RING_COPS + BS + '10_Defend' + BS + 'Pos#01')
    routs = []
    for name, wants in COPS.items():
        top = FED.clone_built(M, B, tmpl, NEW_GROUPS + name)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})        # parked until a rout is named (as OldWaves!)
        me = R + NEW_GROUPS + name
        d = top.add(FED.clone_built(M, B, defend_t, '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs, pts = [], []
        for j, w in enumerate(wants):
            c = snap(nav, part, w, taken, name)
            taken.append(c)
            pts.append(c)
            pp = d.add(FED.clone_built(M, B, pos_t, 'Pos#%02d' % (j + 1)))
            M.place(pp, c)
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
            a = men[j % len(men)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], 'Cop_%02d' % (j + 1)))
            M.place(grp, c, KB.rot9(0.0, -1.0))                                   # facing south: the crew comes up from the garden
            grp.add(FED.clone_built(M, B, a))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        routs.append(me + BS + '10_Defend')
        tops.append(top)
        rep[name] = [[round(v) for v in p] for p in pts]
    # --- snipers: the campaign's own sniper squad cloned (top, Alert modifier, Defend rout + its Pos, the man)
    st = node(SNIPER_SQ)
    alert_t, def_t = node(SNIPER_SQ + BS + '01_Alert'), node(SNIPER_SQ + BS + '03_DefendBehaviour')
    spos_t = node(SNIPER_SQ + BS + '03_DefendBehaviour' + BS + 'Pos#01')
    man_t = node(SNIPER_SQ + BS + 'RetoMoto_Sniper_01')
    wake = []
    for name, want in SNIPERS.items():
        c = snap(nav, part, want, taken, name)
        taken.append(c)
        top = FED.clone_built(M, B, st, NEW_GROUPS + name)
        top.ctrls = [c_ for c_ in top.ctrls if M.p.key(c_[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})
        me = R + NEW_GROUPS + name
        al = top.add(FED.clone_built(M, B, alert_t, '01_Alert'))
        M.place(al, (0.0, 0.0, 0.0))
        d = top.add(FED.clone_built(M, B, def_t, '03_DefendBehaviour'))
        M.place(d, (0.0, 0.0, 0.0))
        pp = d.add(FED.clone_built(M, B, spos_t, 'Pos#01'))
        M.place(pp, c)
        M.set(d, 'DefendBehaviourRout', {1: [me + BS + '03_DefendBehaviour' + BS + 'Pos#01']})
        grp = top.add(FED.clone_built(M, B, man_t, 'Sniper_01'))
        M.place(grp, c, KB.rot9(0.0, -1.0))                                       # looks south down the causeway
        grp.add(FED.clone_built(M, B, man_t + 1))
        wake += [me + BS + '01_Alert', me + BS + '03_DefendBehaviour']
        tops.append(top)
        rep[name] = [round(v) for v in c]
    # --- the plaza trigger box (a clone of tb_LEFT_TheySpotYou, list replaced)
    holder = FED.clone_built(M, B, tmpl, NEW_GROUPS + 'Plaza')                   # tree 3 of the octree lists group-class tops only
    holder.ctrls = []
    M.place(holder, (0.0, 0.0, 0.0))
    box = holder.add(FED.clone_built(M, B, node(WALK_BOX), 'PlazaBox'))
    M.place(box, PLAZA_BOX[0])
    M.set(box, None, {'ZBoxPrimitive[%d]' % a: float(PLAZA_BOX[1][a]) for a in range(3)})
    M.set(box, 'TriggerBox', {17: routs + wake})
    tops.append(holder)
    rep['plaza_box'] = dict(at=PLAZA_BOX[0], half=PLAZA_BOX[1], wakes=routs + wake)
    return M, tops, rep


# ------------------------------------------------------------------ park(): moves + rewiring + the new nodes
def park(src, dst, log=print):
    B = KB.Built(src)
    sc = B.sc
    if any(sc.names[t].startswith(NEW_GROUPS) for t in sc.tops()):
        log('kl_park2_1025: %s already holds %s*: copied unchanged' % (src, NEW_GROUPS))
        shutil.copyfile(src, dst)
        return None
    a0, s0 = census(sc)
    add_a, add_s = sum(len(v) for v in COPS.values()) + len(SNIPERS), len(COPS) + len(SNIPERS)
    if a0 + add_a > ENGINE_ACTORS or s0 + add_s > ENGINE_SQUADS:
        raise ValueError('budget: %d actors / %d squads + %d / %d passes %d / %d' % (a0, s0, add_a, add_s, ENGINE_ACTORS, ENGINE_SQUADS))
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    g0, b0 = B.scene.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(B.scene, octx, rmi, rmc)
    nav = KB.Nav(B.scene.nav, links=True)
    p0 = START[0]
    hit = nav.at(p0[0], p0[1], p0[2], dy=100.0)
    if not hit:
        raise ValueError('the first START point %s is off the mesh' % (p0,))
    ring_part = nav.part[hit[0]]
    for grp, pts in (('START', START), ('TRAITOR', TRAITOR), ('TEAM_MERC', TEAM_MERC)):
        for p in pts:
            h = nav.at(p[0], p[1], p[2], dy=100.0, part=ring_part)
            if not h or nav.clearance(p[0], h[1], p[2]) < KB.CLEAR_MIN:
                raise ValueError('%s point %s is not on the ring part of the mesh' % (grp, p))
    # the plaza cops stand on the garden's part: the part of the mesh at the tea house (802,175,-2456) (the pagoda side is the same part)
    gh = nav.at(802.0, 175.0, -2456.0, dy=150.0)
    if not gh:
        raise ValueError('the tea house is off the mesh')
    garden_part = nav.part[gh[0]]
    log('kl_park2_1025: input %d actors / %d squads; ring part %d, garden part %d' % (a0, s0, ring_part, garden_part))
    M, tops, rep = make_nodes(B, nav, garden_part, log)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'park2')

    moves = []

    def one(path):
        ks = sc.resolve(path)
        kj = Jn.resolve(path)
        if len(ks) != 1 or len(kj) != 1:
            raise ValueError('%s: %d / %d nodes' % (path, len(ks), len(kj)))
        return ks[0], kj[0]

    def move(path, pos=None, face=None, half=None):
        ks, kj = one(path)
        lab = J.labels('dd', Jn.cls(kj))
        old = tuple(float(x) for x in kl_fa.node_values(Jn, kj)[lab.index('ZGEOM[2]')])
        ent = B.ents[ks - 1]
        eo = struct.unpack_from('<3f', ent.trans, 0)
        if max(abs(eo[i] - old[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: .prp place %s and .gms place %s differ' % (path, old, eo))
        pa = sc.parent[ks]
        if pa > 0 and max(abs(B.at(pa)[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: the parent is not at the origin' % path)
        m9 = AU.look9(face) if face is not None else None

        def fn(us):
            if m9 is not None:
                AU.setv(Jn, us, lab.index('ZGEOM[1]'), m9)
            if pos is not None:
                AU.setv(Jn, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
            for i, v in enumerate(half or ()):
                AU.setv(Jn, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
        kl_fa.edit(Jn, kj, None, fn)
        if m9 is not None:
            ent.rot = struct.pack('<9f', *m9) + bytes(12)
        if pos is not None:
            ent.trans = struct.pack('<3f', *[float(x) for x in pos]) + ent.trans[12:]
        moves.append((path.split(BS, 1)[1] if BS in path else path, [round(v) for v in old], [round(v) for v in pos] if pos else None))

    def setlist(path, kind, field, paths):
        ks, kj = one(path)
        kl_fa.edit(Jn, kj, AU.ctrl_of(Jn, kj, kind), lambda us: AU.setv(Jn, us, field, list(paths)))

    sp = R + 'FASpecials!SpawnPoint!'
    names = [sc.path[k] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint']

    plain_start = sorted(p for p in names if p.startswith(sp + 'SpawnPoint_Start_0') and 'Traitor' not in p)
    plain_trait = sorted(p for p in names if p.startswith(sp + 'SpawnPoint_Start_Traitor_0'))
    ucc_start = sorted(p for p in names if p.startswith(sp + 'UCC!SpawnPoint_Start_0') and 'Traitor' not in p)
    ucc_trait = sorted(p for p in names if p.startswith(sp + 'UCC!SpawnPoint_Start_Traitor_0'))
    team = sorted(p for p in names if p.startswith(sp + 'TeamMode!SpawnPoint_TEAM_Merc#'))
    for what, got, want in (('START', plain_start, 8), ('TRAITOR', plain_trait, 4), ('UCC START', ucc_start, 8), ('UCC TRAITOR', ucc_trait, 4), ('TEAM_MERC', team, 6)):
        if len(got) != want:
            raise ValueError('%s spawn points: found %d, expected %d' % (what, len(got), want))
    shift = lambda p, d: (p[0] + d[0], p[1], p[2] + d[2])
    for rows, pts, d in ((plain_start, START, (0, 0, 0)), (ucc_start, START, (30, 0, 20)), (plain_trait, TRAITOR, (0, 0, 0)),
                         (ucc_trait, TRAITOR, (0, 0, 40)), (team, TEAM_MERC[:len(team)], (0, 0, 0))):
        for path, p in zip(rows, pts):
            move(path, shift(p, d), face=(FACE_TO[0] - p[0], FACE_TO[1] - p[2]))
    # cameras, loot / exit areas
    move(sp + 'TeamMode!SpawnCam_000_A!Camera_000_A', CAM_A[0])
    move(sp + 'TeamMode!SpawnCam_000_A!CameraLookAt_000_A', CAM_A[1])
    move(R + 'FASpecials!PIP!ExitLootArea', EXIT_BOX[0], half=EXIT_BOX[1])
    # trigger roles
    move(WALK_BOX, STAIRS_BOX[0], half=STAIRS_BOX[1])
    move(FLOOR_BOX, ALARM_BOX[0], half=ALARM_BOX[1])
    walk_old = [x for x in KOW.values(sc, one(WALK_BOX)[0], 'TriggerBox')[17]]
    floor_old = [x for x in KOW.values(sc, one(FLOOR_BOX)[0], 'TriggerBox')[17]]
    if sorted(floor_old) != sorted(FLOOR_SQUADS + ALARM_KEEP):
        raise ValueError('the old floor box lists %s' % floor_old)
    setlist(WALK_BOX, 'TriggerBox', 17, walk_old + FLOOR_SQUADS)
    setlist(FLOOR_BOX, 'TriggerBox', 17, ALARM_KEEP)
    # backstop
    ks, kj = one(BACKSTOP_TIMER)
    old_t = KOW.values(sc, ks, 'TriggerDelay2')[0]
    if abs(old_t - 240.0) > 1e-6:
        raise ValueError('the backstop timer is %s, expected 240' % old_t)
    kl_fa.edit(Jn, kj, AU.ctrl_of(Jn, kj, 'TriggerDelay2'), lambda us: AU.setv(Jn, us, 0, BACKSTOP_S))
    rep['moves'] = moves
    rep['walk_box_list'] = walk_old + FLOOR_SQUADS
    rep['alarm_box_list'] = ALARM_KEEP

    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made = nxt, {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t in tops:
        ent(t, None)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in tops:
        pts = [c.pos for c in t.kids if c.pos] + [p.pos for c in t.kids for p in c.kids if p.pos]
        if t.pos:
            pts.append(t.pos)
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    if root3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
    octn.rooms[0][3].check()
    move_ = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move_:
        pm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', pm, 0)
        old = set(octx.record_refs())
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', pm, tt + 16 * i)
            if size == 64 and pm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, off + 0x1c)[0]
                if v in move_:
                    struct.pack_into('<I', pm, off + 0x1c, move_[v]); repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move_))
        new_prm = bytes(pm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    for e_ in ('.ANM', '.fxc'):
        if e_ in B.ext and len(new[B.ext[e_]]) != len(B.files[B.ext[e_]]):
            raise ValueError('a large block changed its size: ' + e_)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    a1, s1 = census(KB.Built(dst).sc)
    log('kl_park2_1025: %d entities added, REF ids %d..%d, members changed %s, %d slot ids renumbered, %d .prm roots re-pointed, actors %d -> %d, squads %d -> %d, %d nodes moved'
        % (len(order), ref0, nxt - 1, ' '.join(changed), moved, repointed, a0, a1, s0, s1, len(moves)))
    return dict(census=[a0, s0, a1, s1], members_changed=changed, slot_ids_moved=moved, prm_roots_repointed=repointed, ref_ids='%d..%d' % (ref0, nxt - 1), plan=rep)


# ------------------------------------------------------------------ the chain
def build(src, dst, log=print, keep=None):
    if md5(src) != SRC_MD5:
        raise ValueError('%s: md5 %s is not the pinned %s' % (src, md5(src), SRC_MD5))
    work = keep or tempfile.mkdtemp(prefix='park2_')
    os.makedirs(work, exist_ok=True)
    rep = collections.OrderedDict()
    try:
        s1, s2, s3 = [os.path.join(work, 's%d.zip' % i) for i in (1, 2, 3)]
        log('step 1: extinguishers (kl_interact_graft.build)')
        IG.build(src, s1, ext=4, necks=4, doors=[], pin=SRC_MD5, log=log, ext_lift=100.0)
        m1 = md5(s1)
        log('step 2: fuel cans (kl_dm01b_gas_1025.build)')
        GS.FUEL_ANCHORS = [(300.0, -2100.0, 220.0), (1300.0, -2100.0, 220.0), (700.0, -1800.0, 220.0), (1000.0, -2400.0, 220.0)]
        GS.EXT_WALL = []
        GS.ext_spots_wall = lambda B, nav: []
        GS.build(s1, s2, pin=m1, log=log)
        log('step 3: the redesign (park)')
        rep['park'] = park(s2, s3, log=log)
        log('step 4: sound references by name')
        rep['sound'] = MALL.resound(s3, dst, log=log, cars_donor=False)
        rep['md5'] = md5(dst)
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    return rep


# ------------------------------------------------------------------ INSTALL / UNDO (the gas installer, renamed; as the mall's)
def ps_text():
    s = GS.PS1
    s = s.replace('gas.json', 'park2.json').replace('.before-1025dm01bgas', TAG).replace('gas.ps1', 'park2.ps1')
    s = s.replace('Maps\\DM01B\\F03_Main.zip', 'Maps\\DM06B\\F02_Main.zip').replace('renamed F03_Main.zip', 'renamed F02_Main.zip')
    s = s.replace('.MAT .TEX .HVK .hrd change', '.MAT .TEX .HVK change; DM06B has no .hrd')
    first = s.index('\n')
    return ('# park2.ps1 - DM06B A Walk in the Park II redesign, 2026-10-25 (tools/kl_park2_1025.py): highway start, plaza ambush, pagoda snipers, extinguishers, fuel cans.\n'
            '#   Chained on the live DM06B zip 64bb5dc9: `old` in park2.json is that md5; the install refuses any other.\n') + s[first + 1:]


BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0park2.ps1" {arg}\r\npause\r\n'


def run_ps(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'park2.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    if dry:
        a.append('-DryRun')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    old = md5(src)
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, FILE)
    rep = build(src, z, log=log)
    new = md5(z)
    man = dict(m=MAP, f=FILE, old=old, new=new, tag=TAG, chain='live DM06B zip 64bb5dc9')
    with open(os.path.join(out, 'park2.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'park2.ps1'), 'w', newline='\r\n') as fh:
        fh.write(ps_text())
    for nm, arg in (('INSTALL dm06b park2.bat', ''), ('UNDO dm06b park2.bat', '-Undo')):
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
    t = run_ps(d, g, dry=True); log(t.strip()); assert 'would install' in t and md5(live) == man['old'], t
    t = run_ps(d, g); log(t.strip()); assert 'installed' in t and md5(live) == man['new'], t
    assert md5(live + TAG) == man['old']
    assert 'already installed' in run_ps(d, g)
    t = run_ps(d, g, undo=True); log(t.strip())
    assert md5(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    assert 'already undone' in run_ps(d, g, undo=True)
    run_ps(d, g); assert md5(live) == man['new']
    run_ps(d, g, undo=True); assert md5(live) == man['old'] and not os.path.exists(live + TAG)
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
