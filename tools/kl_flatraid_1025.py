"""kl_flatraid_1025.py - Flat Raid (DD10) post-pass: bots that know where to go, a van that arrives, more enemies, reachable loot. Written 2026-10-25, OFFLINE only.

Owner feedback on the live map: "everything but one npc (bud) knew where to go, needs more enemies throughout the floors and needs some outside the area, dont know where
the vehicle heli or van is to escape at the end got stuck".  One member-level patch of a COPY of the live zip (md5 pinned), four jobs in the critic's order:

  1 BOTS. Six campaign ActorDeactivator controllers (Special!DeactivationAreas!*) list an area box each; a heister bot standing in one has its node switched OFF (.gms flag
    0x400, runtime node+0x3c bit 10) and the hook refuses to order it ("no order: its node is off" for bots 1, 2, 3, 6, 7). The area list (field 0) of each is emptied. Nothing
    in the Flat Raid build needs the campaign's deactivation (it is campaign story streaming); the same lists would also have switched the new enemies off.
  2 VAN. RivalMercVan!Timer (backstop) 300 -> BACKSTOP s; the floor box tb_RIGHT_TheySpotYou (flats corridor, 1000 x 800) is widened over the whole flats floor; a text cue
    'The van is in the street. Get out the front.' (OnscreenMessage, a clone of EscapeSetup!OnScreenMSG_LastEscapeVan) fires with the van's show (DisableVisionBlocker!Timer, 8 s).
    The van's z is not touched. A waypoint / POI that only shows once the van has come needs hook code: see hook_proposal.txt next to the stage.
  3 ENEMIES. Squads of F07's police form (ZSquadScript group + 40_RunToEscape / 10_RunToCover + RunToPosInfo + men groups + 30_smUnleash + 10_Defend), cloned from TWO stock
    sources: F07 (Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left) and F04 (Gameplay!030_AfterLoot!035_RightFlankEnd_01) for the structure, the men from F07 (model indices
    are per level: F04's 1758 / 1874 would be wrong in this map). Stepped: one TriggerDelay2 per squad on the AIMonitor's round-start list.
  4 LOOT. The five stacks that no walking player can reach (750,000) move onto reachable tops (Floors.stand spare >= 20 at reach 165); the eight stacks are 500,000 each = 4,000,000.

TOGGLE (owner's rule): map CONTENT, so the on/off switch is the install / undo pair: install.py puts the staged zip in (original -> '<zip>.before-1025raid3'), --undo puts it back
byte for byte; the live md5 is pinned before either and nothing is written while kl2.exe runs.

Usage (from tools/):  python kl_flatraid_1025.py build <in zip> <out zip>   |   python kl_flatraid_1025.py stage <root> [--rehearse <scratch>]   (<root>/DD10/in/F01_Main.zip)
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene, kl_loc
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_fa_bank as BK
import kl_octree as O
import kl_prpjoin as J
import kl_loot_1025 as LT
import kl_bots_kick_1025 as KK
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
SLOT = 'F07'
TAG = '.before-1025raid3'
PIN = 'e826b4ea4400d114a1fca09b5237a863'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPNAME, ZIPNAME, INNAME = 'DD10', 'F07_Main.zip', 'F01_Main.zip'   # live file F07_Main.zip; the input COPY is named F01_Main.zip
MONITOR = 'ROOT' + BS + 'Gameplay!AIMonitor'

# ------------------------------------------------------------------ job 2: the van
POI_NODE = 'FASpecials!POI!POI_TheEscapeArea'          # stock sender is only the pad box; here the van-show timer also sends it (UNTESTED live, precedent kl_club_roof.py)
POI_TEXT = 'FASpecials!POI!CheckMPTutorialOption#02'
CIVS_DEACT = 'ActorDeactivatorCivs'   # node 17497, area Floor1Civs, fired by TB_DeactivateCivs
BACKSTOP = 165.0                    # s (was 300). GUESS: the crew is in the flats by about two minutes; the owner's round got stuck waiting for 300
BACKSTOP_NODE = 'Gameplay!010_FirstFight!RivalMercVan!Timer'
FLOOR_NODE = 'Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou'
FLOOR_BOX = ((11650.0, 1650.0, 2500.0), (1650.0, 150.0, 1500.0))   # centre, half size: x 10000..13300, y 1500..1800, z 1000..4000. MEASURED 2026-10-25 (nav, window x 8700..13500 z -800..4000): the flats floor is y 1600.0..1628.8 only (256 polys, dense x 10000..13150, z 1000..4000); the next floors under/over the footprint are y <= 1213 and y = 2000, both outside y 1500..1800. Was (12295,1600,1566) +- (500,100,400)
VAN_TIMER = 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!Timer'
CUE_SRC = 'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan'
CUE_NAME = 'Gameplay!EscapeSetup!OnScreenMSG_VanInStreet'
CUE_KEY = 'AllLevels/Interface/Online/Objectives/L05_VanInStreet'
CUE_TEXT = 'The van is in the street. Get out the front.'

# ------------------------------------------------------------------ job 4: loot (node -> new place, amount). Nodes are the MoneyStack_nnn of the build.
LOOT_MOVES = collections.OrderedDict([
    (21973, ((10660.0, 1650.0, 1900.0), 'flats: on crate B_03')),          # was (13059,1599,3287), unreachable
    (22059, ((10960.0, 1602.0, 1820.0), 'flats: floor, main mesh part')),         # was (10938,1600,2410). 1st try (10790,1650,1950) failed the layer: not on the main mesh part
    (22060, ((11800.0, 860.0, 1800.0), 'offices 2nd floor: on chair_B_02')),   # was (10652,1599,2393)
    (22061, ((10330.0, 802.0, 50.0), 'offices 2nd floor: floor, main mesh part')),   # was (10863,1599,2322). 1st try (10220,860,30) was 92 off the main part
    (22062, ((9550.0, 402.0, 810.0), 'offices 1st floor: floor, main mesh part'))])  # was (12547,1599,3108). 1st try (9530,450,940) was 128 from the mesh
# GUESS (every place): from a grid search 2026-10-25 (work/e21.py: main mesh part, mesh distance <= 25, Floors.stand spare >= 60, 300 from other loot, 450 from every START, layer way_proof);
# verified again on the output by verify_loot() (Floors.stand) and by kl_l05_layer.check.
LOOT_EACH = 500000                  # 8 x 500,000 = 4,000,000 (owner: every stock FA map totals exactly 4,000,000). GUESS: equal shares
LOOT_NODES = (21973, 22056, 22057, 22058, 22059, 22060, 22061, 22062)

# ------------------------------------------------------------------ job 3: enemies
ACTOR_CAP_LAYER = 55                # kl_l05_layer.ACTOR_CAP: the layer's own check fails above it BY DESIGN (see the report: stock evidence)
TPL_A = ('F07', R + 'Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left', dict(escape='40_RunToEscape', cover='10_RunToCover', info='RunToPosInfo#%02d'))
TPL_B = ('F04', R + 'Gameplay!030_AfterLoot!035_RightFlankEnd_01', dict(escape='20_MoveToEscape', cover='10_RunToCover', info='RunToPosInfo#%02d'))
MEN_SRC = ('F07', R + 'Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left')
MEN_GROUPS = ('Police_SWAT_01__#02', 'Police_SWAT_01__', 'Police_SWAT_01__#01')   # the leader (RadioCom + Ground) first
TIMER_SRC = ('F07', R + KB.SQUAD + 'Timer_start_bots')
# name, template, men, centre (x, y, z) the squad is laid round, start delay s from the round-start event.  GUESS: every site and every delay (stepped 20 .. 150 s).
SQUADS = [
    ('031_FlatRaid_StreetWest', TPL_A, 2, (9300.0, 0.0, 300.0), 20.0),        # in the street, west of the tower, toward the van
    ('032_FlatRaid_StreetMid', TPL_B, 2, (10700.0, 0.0, 700.0), 45.0),        # in the street, in front of the tower
    ('035_FlatRaid_Floor3', TPL_B, 2, (10000.0, 1200.0, 1750.0), 125.0),      # 3rd floor
    ('036_FlatRaid_Flats', TPL_A, 2, (12300.0, 1600.0, 3000.0), 150.0)]       # the flats
SQ_PREFIX = 'Gameplay!030_AfterLoot!'
SEED_DISTANCE = 1000.0              # cm from every START / TRAITOR / TEAM_MERC row (the layer's rule: no policeman in sight of them)
ACTOR_APART = 250.0                 # cm from any existing actor on the same floor
LANE = (5300.0, 12400.0, 1100.0)    # the van's drive: x from, to, z (y 0); LANE_CLEAR 250
MAN_APART = 110.0


def md5(p):
    return LT.md5(p)


# ------------------------------------------------------------------ the navigation mesh
class Mesh:
    def __init__(self, B, folder):
        self.nav = KB.Nav(B.scene.nav, links=True)
        self.home = KB.stations(B, self.nav)['home']
        import kl_l05_layer as L5
        sc, _scene, _ents, pos, _h, _s, _l, _z = BK.read_built(folder)
        self.rows = [pos[_ents[t - 1]] for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and kl_fa.node_values(sc, t)[8].endswith(('_START', 'TEAM_MERC', '_TRAITOR'))]
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'third_party', 'anp', 'scripts'))
        import hvk_ray
        self.C = hvk_ray.Collision(BK.archive_of(folder))
        self.seen_from = L5.seen_from

    def hidden(self, p):
        """True when no START / TEAM_MERC / TRAITOR row sees a man whose group stands at p (the layer's own exact casts; group y = floor + 1)."""
        return self.seen_from(self.C, self.rows, (p[0], p[1] + 1.0, p[2])) is None

    def at(self, x, y, z):
        h = self.nav.at(x, y, z, dy=60.0)
        return (x, h[1], z) if h and self.nav.part[h[0]] == self.home else None

    def grid(self, c, rad, step=60.0):
        out, x = [], c[0] - rad
        while x <= c[0] + rad:
            z = c[2] - rad
            while z <= c[2] + rad:
                p = self.at(x, c[1], z)
                if p:
                    out.append(p)
                z += step
            x += step
        return out


def d2(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def lay_site(mesh, centre, n, avoid, taken):
    """-> dict(anchor, men [n], cover [n], defend, escape) as (x, y, z) on the main mesh part; raises when the site has no room."""
    import kl_l05_layer as L5
    fixed = L5.START + L5.TRAITOR + L5.TEAM_MERC
    ok = []
    for p in mesh.grid(centre, 520.0):
        if min(d2(p, a) for a in fixed) < SEED_DISTANCE:
            continue
        if centre[1] == 0.0 and abs(p[2] - LANE[2]) < 400.0 and LANE[0] - 400 <= p[0] <= LANE[1] + 400:
            continue                                                  # the van's drive (LANE_CLEAR 250 + margin)
        if any(d2(p, a) < ACTOR_APART and abs(p[1] - a[1]) < 150 for a in avoid + taken):
            continue
        ok.append(p)
    if len(ok) < 2 * n + 3:
        raise ValueError('site %s: only %d mesh points' % (centre, len(ok)))
    ok.sort(key=lambda p: d2(p, centre))
    hid = [p for p in ok if mesh.hidden(p)]                     # the MEN start where no spawn row can see them (cover / defend / escape places need not)
    if len(hid) < n + 3:
        raise ValueError('site %s: only %d hidden mesh points' % (centre, len(hid)))
    anchor = hid[0]
    pick = lambda lo, hi, used, k: [q for q in [None] for _ in [0]]  # (unused placeholder keeps the names short)
    def choose(lo, hi, used, k, pool=None):
        got = []
        for p in (ok if pool is None else pool):
            if lo <= d2(p, anchor) <= hi and all(d2(p, q) >= MAN_APART for q in used + got):
                got.append(p)
                if len(got) == k:
                    return got
        raise ValueError('site %s: cannot place %d points %d..%d from the anchor' % (centre, k, lo, hi))
    men = [anchor] + choose(MAN_APART, 320.0, [anchor], n - 1, hid)
    cover = choose(150.0, 500.0, men, n)
    defend = choose(300.0, 750.0, men + cover, 1)[0]
    escape = choose(200.0, 900.0, men + cover + [defend], 1)[0]
    taken += men
    return dict(anchor=anchor, men=men, cover=cover, defend=defend, escape=escape)


# ------------------------------------------------------------------ small edits on the built level
def place_node(B, k, pos, half=None):
    """Node k (top level, identity at the origin) to the world place pos / box half sizes: .prp ZGEOM[2] (+ ZBoxPrimitive[i]) and the .gms record, kept equal (kl_fa_author.place)."""
    sc, e = B.sc, B.ents[k - 1]
    if sc.parent[k] != 0:
        raise ValueError('%s is not top level' % sc.path[k])
    lab = J.labels('dd', sc.cls(k))

    def fn(us):
        AU.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
        for i, v in enumerate(half or ()):
            AU.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
    kl_graft.edit(sc.nodes[k], 'props', fn)
    e.trans = struct.pack('<3f', *[float(x) for x in pos]) + e.trans[12:]


def by_name(sc, name):
    k = sc.resolve(R + name)
    if len(k) != 1:
        raise ValueError('%d nodes named %s' % (len(k), name))
    return k[0]


def job_bots(B, log):
    sc, n = B.sc, 0
    dead = []
    for k, i, v in kl_fa.controllers(sc, 'ActorDeactivator'):
        if CIVS_DEACT not in sc.path[k]:
            continue   # the other five fire only from jump points / a cutscene gate: kept as they are
        dead.append((sc.path[k].split(BS, 1)[1], [str(x) for x in v[0]]))
        kl_fa.edit(sc, k, i, lambda us: AU.setv(sc, us, 0, []))
        n += 1
    if n != 1:
        raise ValueError('expected exactly one Civs ActorDeactivator, found %d' % n)
    log('  1 bots: Civs ActorDeactivator area list emptied (other 5 kept)')
    return dead


def job_van(B, log):
    sc = B.sc
    k = by_name(sc, BACKSTOP_NODE)
    old = kl_fa.controllers(sc, 'TriggerDelay2')
    old = next(v for kk, i, v in old if kk == k)[0]
    kl_fa.edit(sc, k, AU.ctrl_of(sc, k, 'TriggerDelay2'), lambda us: AU.setv(sc, us, 0, BACKSTOP))
    kb = by_name(sc, FLOOR_NODE)
    was = (tuple(B.at(kb)), B.box(kb))
    place_node(B, kb, FLOOR_BOX[0], FLOOR_BOX[1])
    log('  2 van: backstop %.0f -> %.0f s; floor box %s -> %s' % (old, BACKSTOP, was, FLOOR_BOX))
    return dict(backstop=(old, BACKSTOP), floor_box=(was, FLOOR_BOX))


def job_loot(B, log):
    before = LT.money(B)
    if set(LOOT_NODES) != set(before):
        raise ValueError('the loot nodes of the map %s are not %s' % (sorted(before), sorted(LOOT_NODES)))
    pos0 = {k: LT.zgeom(B, k) for k in LOOT_MOVES}
    stuck = LT.listed_in_oct(B, list(LOOT_MOVES) + [by_name(B.sc, FLOOR_NODE)])
    if stuck:
        raise ValueError('nodes %s are listed in an .oct room tree: moving them needs an octree edit (not done)' % stuck)
    for k, (p, _why) in LOOT_MOVES.items():
        LT.move(B, k, p)
    for k in LOOT_NODES:
        LT.amount(B, k, LOOT_EACH)
    log('  4 loot: %d stacks moved, %d amounts set; total %d -> %d' % (len(LOOT_MOVES), len(LOOT_NODES), sum(before.values()), LOOT_EACH * len(LOOT_NODES)))
    return pos0, before


# ------------------------------------------------------------------ job 3 nodes
def val(M_level, k, label):
    sc, _e = M_level
    return kl_fa.node_values(sc, k)[J.labels('dd', sc.cls(k)).index(label)]


def make_squads(B, mesh, log):
    """-> (maker, [top Node], [specs], [(timer Node, squad top name)])"""
    sc = B.sc
    M = KB.Maker()
    existing = [tuple(B.at(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor']
    taken, tops, specs, timers = [], [], [], []
    src_f07 = KB.Maker.level('F07')
    for name, (lvl, tpath, f), n, centre, delay in SQUADS:
        site = lay_site(mesh, centre, n, existing, taken)
        full = SQ_PREFIX + name
        me = R + full
        up = lambda p: (p[0], p[1] + 1.0, p[2])
        top = M.clone(lvl, tpath, full)
        M.place(top, (0.0, 0.0, 0.0))
        tops.append(top)
        # 40_RunToEscape / 20_MoveToEscape: one Defend step with a Pos
        g = top.add(M.clone(lvl, tpath + BS + f['escape']))
        M.place(g, (0.0, 0.0, 0.0))
        p1 = g.add(M.clone(lvl, tpath + BS + f['escape'] + BS + 'Pos#01'))
        M.place(p1, up(site['escape']))
        M.set(g, 'DefendBehaviourRout', {1: [me + BS + f['escape'] + BS + 'Pos#01']})
        # 10_RunToCover + one RunToPosInfo per man (its last field names the man's group)
        rc = top.add(M.clone(lvl, tpath + BS + f['cover']))
        M.place(rc, (0.0, 0.0, 0.0))
        names = list(MEN_GROUPS[:n])
        for i in range(n):
            info = rc.add(M.clone(lvl, tpath + BS + f['cover'] + BS + 'RunToPosInfo#%02d' % (3 if i == 0 else 2 if i == 1 else 1), f['info'] % (i + 1)))
            M.place(info, up(site['cover'][i]))
            M.set(info, 'RunToCoverPosInfoRout', {5: me + BS + names[i]})
        # the men: F07's groups (model / sound indices of THIS map)
        for i, mg in enumerate(names):
            mp = MEN_SRC[1] + BS + mg
            grp = top.add(M.clone(MEN_SRC[0], mp))
            M.place(grp, up(site['men'][i]))
            kids = [c for c in range(1, len(src_f07[0].nodes)) if src_f07[0].path[c].startswith(mp + BS) and src_f07[0].parent[c] == src_f07[0].resolve(mp)[0]]
            for c in kids:
                kid = grp.add(M.clone(MEN_SRC[0], c))
                if src_f07[0].cls(c) == 'ZFFActor':
                    M.place(kid, (0.0, 0.0, 0.0))
                    kid.model = val(src_f07, c, 'ZGEOM[4]')            # the model index is a field of the actor in its own level (F07 = this map)
                else:
                    M.place(kid, (0.0, 93.0, 0.0))                      # the RadioCom: 93 cm above its man (as in F07, MEASURED on the .gms)
        sm = top.add(M.clone(lvl, tpath + BS + '30_smUnleash'))
        M.place(sm, (0.0, 0.0, 0.0))
        df = top.add(M.clone(lvl, tpath + BS + '10_Defend'))
        M.place(df, (0.0, 0.0, 0.0))
        d1 = df.add(M.clone(lvl, tpath + BS + '10_Defend' + BS + 'Pos#01'))
        M.place(d1, up(site['defend']))
        M.set(df, 'DefendBehaviourRout', {1: [me + BS + '10_Defend' + BS + 'Pos#01']})
        # the start timer
        tm = M.clone(TIMER_SRC[0], TIMER_SRC[1], SQ_PREFIX + 'FlatRaid_Timer_%02d' % (len(timers) + 1))
        M.place(tm, (0.0, 0.0, 0.0))
        M.set(tm, 'TriggerDelay2', {0: float(delay), 1: 0.0, 2: -1.0, 3: 0, 4: [me + BS + f['cover']]})
        tops.append(tm)
        timers.append((tm, full))
        specs.append(dict(name=full, template='%s %s' % (lvl, tpath.rsplit(BS, 1)[1]), men=n, site=site, delay=delay))
        log('  3 squad %s: %d men at (%d, %d, %d), template %s, starts at %.0f s' % (name, n, *site['anchor'], lvl, delay))
    return M, tops, specs, timers


def make_cue(M, tops):
    c = M.clone('F07', R + CUE_SRC, CUE_NAME)
    M.place(c, (10000.0, 0.0, 10000.0))
    M.set(c, 'OnscreenMessage', {0: CUE_KEY})
    tops.append(c)
    return c


# ------------------------------------------------------------------ the zip
def stock_evidence():
    """Total ZFFActor entities of each stock Fragile Alliance level (the engine's own load) -> {slot: n}."""
    out = collections.OrderedDict()
    for lv in ('F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09'):
        try:
            sc, _e = KB.Maker.level(lv)
            out[lv] = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor')
        except Exception as ex:
            out[lv] = 'ERR %s' % ex
    return out


def build(src, dst, log=print):
    h_in = md5(src)
    B = KB.Built(src, SLOT)
    sc = B.sc
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
    actors0 = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor')
    mesh = Mesh(B, os.path.dirname(os.path.abspath(src)))
    dead = job_bots(B, log)
    van = job_van(B, log)
    pos0, loot0 = job_loot(B, log)
    M, tops, specs, timers = make_squads(B, mesh, log)
    cue = make_cue(M, tops)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'raid')

    def add_to(path, cname, field, new):
        k = Jn.resolve(path)
        if len(k) != 1:
            raise ValueError('%d nodes at %s' % (len(k), path))
        k = k[0]

        def fn(us):
            have = [Jn.p.key(t) for t in us[field][1:]]
            for x in new:
                if x.lower() not in [h.lower() for h in have]:
                    have.append(x)
            us[field] = kl_fa._refs(Jn, have)
        kl_fa.edit(Jn, k, AU.ctrl_of(Jn, k, cname), fn)
    add_to(MONITOR, 'AIMonitor', 2, [R + t.name for t, _s in timers])
    add_to(R + VAN_TIMER, 'TriggerDelay2', 4, [R + CUE_NAME, R + POI_NODE, R + POI_TEXT])   # as kl_club_roof.py: the stock escape POI + its on-screen text, sent by the van-show timer
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- .gms / .buf
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for k in n.kids:
            ent(k, e)
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
    # the squad's step groups are listed in the root's group tree 3, as F07 lists its own (top, escape, cover, defend: the box of the places below, +- 10)
    items = []
    for n in order:
        if not n.tid & kl_scene.GROUP:
            continue
        if n.name.startswith(SQ_PREFIX) and not n.name.startswith(SQ_PREFIX + 'FlatRaid_Timer'):
            ps = [k.pos for k in n.walk() if k.name.startswith(('Pos#', 'RunToPosInfo')) or (k.kids and any(c.tid and c.name == 'Ground' for c in k.kids))]
        else:
            ps = [k.pos for k in n.kids if k.name.startswith(('Pos#', 'RunToPosInfo'))]
        if ps and any(k.name.startswith(('Pos#', 'RunToPosInfo')) for k in n.walk()):
            lo = tuple(min(p[a] for p in ps) - 10.0 for a in range(3))
            hi = tuple(max(p[a] for p in ps) + 10.0 for a in range(3))
            items.append((slot1[made[id(n)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    repointed, new_prm = 0, None
    if r3 is not None and items:
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
    # ---- the text cue, in every language's .LOC
    langs = 0
    for ext in sorted(B.ext):
        if ext.lower().endswith('.loc'):
            kids = kl_loc.parse(B[ext])
            if kids is None:
                continue
            BK.set_text(kids, CUE_KEY, CUE_TEXT)
            new[B.ext[ext]] = kl_loc.build(kids)
            langs += 1
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    repl = {B.ext[e]: new[B.ext[e]] for e in changed}
    n_prm0 = None
    if new_prm is not None:
        import kl_prmgraph
        n_prm0 = (len(kl_prmgraph.read(B['.prm']).chunks), len(kl_prmgraph.read(new_prm).chunks))
        if n_prm0[0] != n_prm0[1]:
            raise ValueError('.prm chunk count changed %s' % (n_prm0,))
    work = tempfile.mkdtemp(prefix='raid_')
    try:
        wz = os.path.join(work, os.path.basename(dst))
        KK.patch_zip(src, wz, repl)
        counts = []
        for zsrc in (src, wz):
            tmpd = tempfile.mkdtemp(prefix='raid_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, os.path.basename(dst)))
                counts.append(BK.seal(tmpd, log=lambda *_: None))
            finally:
                KK.rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        problems = BK.reverify(work, log=lambda *_: None)
        wi = tempfile.mkdtemp(prefix='raid_in_')
        try:
            shutil.copyfile(src, os.path.join(wi, os.path.basename(dst)))
            base_problems = BK.reverify(wi, log=lambda *_: None)
        finally:
            KK.rmtree(wi)
        problems = [x for x in problems if x not in base_problems]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(wz, dst)
    finally:
        KK.rmtree(work)
    # ---- read back
    A2 = KB.Built(dst, SLOT)
    bad = []
    after = LT.money(A2)
    if sum(after.values()) not in (4000000, __import__('kl_loot_scale_1026').TARGETS['DD10'][0]) or len(after) != 8:     # 2026-10-26: 4M as built, or DD10's per-map target after kl_loot_scale_1026
        bad.append('loot total %d in %d objects' % (sum(after.values()), len(after)))
    actors1 = sum(1 for k in range(1, len(A2.sc.nodes)) if A2.sc.cls(k) == 'ZFFActor')
    if actors1 != actors0 + sum(s['men'] for s in specs):
        bad.append('actors %d, expected %d' % (actors1, actors0 + sum(s['men'] for s in specs)))
    for k, i, v in kl_fa.controllers(A2.sc, 'ActorDeactivator'):
        if (CIVS_DEACT in A2.sc.path[k]) == bool(v[0]):
            bad.append('%s lists %s' % (A2.sc.path[k], v[0]))
    for n in A2.files:
        if n not in repl and A2.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(
        md5_in=h_in, md5_out=md5(dst), members_changed=changed, entities_before=len(B.ents), entities=len(ents), added=len(order), slot_ids_moved=moved,
        tree3_items=len(items), prm_roots_repointed=repointed, prm_chunks=n_prm0, actors_before=actors0, actors_after=actors1, loot_total=sum(after.values()),
        deactivators=dead, van=van, loot_moved=[(k, sc.names[k], pos0[k], LOOT_MOVES[k][0], LOOT_MOVES[k][1]) for k in LOOT_MOVES],
        loot_before=loot0, squads=specs, cue=dict(node=CUE_NAME, key=CUE_KEY, text=CUE_TEXT, languages=langs), room_sets=[str(pre), str(post)],
        stock_actors=stock_evidence())
    log('  members changed: %s; %d entities added, %d slot ids renumbered, %d tree-3 items, %d .prm roots re-pointed; actors %d -> %d' % (
        ' '.join(changed), len(order), moved, len(items), repointed, actors0, actors1))
    return rep


# ------------------------------------------------------------------ verify the loot places on the OUTPUT
def verify_loot(zp, log=print):
    import kl_fa_loot as L
    lv = L.Built(zp)
    B = KB.Built(zp, SLOT)
    nav = KB.Nav(B.scene.nav, links=True)
    st = KB.stations(B, nav)
    f = L.Floors(lv.hvk, (8700, 13500, -800, 4000), skip=(lv.soft() | lv.hidden))
    seen, _ = f.flood([tuple(p) for p, _f in st['starts']], snap=200.0)
    out = []
    for r in L.loot(lv):
        pl, h, n = f.stand(seen, r['at'], r['radius'])
        spare = None if h is None else r['radius'] + 40.0 - h
        out.append((r['k'], [round(v) for v in r['at']], r['value'], None if spare is None else round(spare), n))
        log('  loot %s %s %d spare %s (%d places)' % (r['k'], [round(v) for v in r['at']], r['value'], None if spare is None else round(spare), n))
    return out


# ------------------------------------------------------------------ stage
PROPOSAL = '''Flat Raid (DD10) - what the hook would add for the van (NOT done: klhook/*.c untouched, nothing installed). 2026-10-25.

1. The map side (staged): BACKSTOP 300 -> 165 s, the floor box over the whole flats floor, the text cue 'The van is in the street. Get out the front.' with the van's show.
2. A waypoint that appears when the van arrives. The POI (FASpecials!POI!POI_TheEscapeArea, the marker beside the boarding place) is drawn by Dog Days' own POI system;
   in this map nothing sends it the 'show' message at the van's arrival (Trigger_POI_TheEscapeArea is a box round the boarding place, so it shows only when a player is already there).
   Proposal (hook, klhook/klmapfix.c or a new small module, ini [Escape] VanWaypoint=0, default off, labelled '(recommended on)'): when the van's group
   (Animation/F07/F07_Escape_Vehicle_01.zip\\EscapeVehicle_Animation_F07) goes visible, send the same message Trigger_POI_TheEscapeArea sends on entry to the POI node. Needs the
   POI message id from a F03/F04 trace (research first); not guessed here.
3. Map-only (STAGED, as kl_club_roof.py, untested live): the van-show timer now also sends POI_TheEscapeArea and CheckMPTutorialOption#02 (target list field 4), so the marker
   and its text appear with the van. If the owner still sees no marker, the hook proposal in 2 stays open.
'''


def stage(root, scratch=None, log=print):
    d = os.path.join(root, MAPNAME)
    src = os.path.join(d, 'in', INNAME)
    h = md5(src)
    if h != PIN:
        raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, PIN))
    out = os.path.join(d, 'stage')
    KK.rmtree(out)
    os.makedirs(out)
    rep = build(src, os.path.join(out, ZIPNAME), log)
    rep['loot_check'] = verify_loot(os.path.join(out, ZIPNAME), log)
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write((KK.INSTALL_PY % dict(map=MAPNAME, zip=ZIPNAME, tag=TAG, game=GAME, old=h, new=rep['md5_out'])).replace('door-kick zip (tools/kl_bots_kick_1025.py', 'Flat Raid zip (tools/kl_flatraid_1025.py'))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'hook_proposal.txt'), 'w') as fh:
        fh.write(PROPOSAL)
    if scratch:
        rehearse(out, src, rep['md5_out'], h, scratch, log)
    return rep


def rehearse(d, old_zip, new_md5, old_md5, scratch, log=print):
    KK.MAPS[MAPNAME] = ('F07', ZIPNAME, PIN)
    KK.TAG = TAG
    KK.rehearse(d, MAPNAME, old_zip, new_md5, old_md5, scratch, log)


def main():
    a = sys.argv[1:]
    opt = lambda k, dflt=None: a[a.index(k) + 1] if k in a else dflt
    if len(a) >= 3 and a[0] == 'build':
        build(a[1], a[2])
    elif len(a) >= 2 and a[0] == 'stage':
        stage(a[1], opt('--rehearse'))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
