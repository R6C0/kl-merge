#!/usr/bin/env python3
"""kl_club_lastcall2.py - Last Call (DM05A) pass 1024r2: the escape on the far roof, Yakuza/bodyguard waves, the actor budget. OFFLINE.

  python tools/kl_club_lastcall2.py build <in F01_Main.zip> <out F01_Main.zip> [--force]
  python tools/kl_club_lastcall2.py check <zip>        census (actors / squads), the heli set, the wave chain, the walkable route

Input zip -> output zip, rerunnable: a zip that already holds the wave clock node 'OldWaves!Clock' is copied through unchanged
(idempotent); an input whose md5 is not one of KNOWN_IN is refused unless --force (other passes may have been chained first).
The output must be another path than the input.

THREE JOBS, ONE PASS (all by NAME, so it chains over other passes)
 1. THE ESCAPE MOVES. The helicopter set (EscapeSetup!EscapeChopper with its splines, the OnMap box, boarding triggers, PIP point,
    the four escape-camera nodes, otrExitLevel, the POI / respawn boxes) is translated by D = new pad - old pad as ONE rigid
    motion. New pad (7300, 1881, 3500): the far end of the roof beyond the glass ceiling (Platform_C_Mod, floor y 1881,
    room M05_A_Outside_Roof_01a). Every node moved sits under parents at the origin unturned, so a translation of the node
    (the chopper group's top for its whole subtree) is exact; the script asserts that. Also moved: the chopper's non-STATIC
    .HVK placements (D / 100, metres), the three room-tree items (group + Incomming + Escaping; the group's box unions the pad).
    The bots' final stations (06_Exit, the Pos nodes of Squad#02..#08 \\037_ and \\050_) and AllyEscapeBox / ExitLootArea go to
    cells of the mesh part the crew walks (the walkable strip at the new pad is small: x 7000..7400, z 3600..4200).
 2. WAVES. Six timed waves of parked squads (5 men each: Yakuza model 41556 / bodyguards 41803, the map's own armed actors),
    entering at the club's own doors, stairwells, fire doors and backstage, walking to posts around where the crew will be
    (fraction of the START->pad route). The kl_old_waves chain: AIMonitor START list -> Pace_1 -> Go_1 (names the Defend rout and
    Pace_2) -> ... The round has no alarm node, so the first Pace starts with the round (GUESS: there is no alarm to hang it on).
 3. BUDGET. The input holds 107 actors / 79 squads (live-proven: 99 / 55). The four 030_AfterLoot police squads (they hang on
    the old escape) go, their gate-path entries are cut; civilians are trimmed to what fits under 99 / 55 with the waves added,
    keeping the ones nearest to the route.

GUESSES (said plainly): the chopper's spline start (far outside the map) and its landing geometry are moved rigidly and not
checked against the engine; the camera spot is free air (not checked); wave timing, entrances and posts are chosen from the
mesh, not play-tested; the bots' mesh strip at the pad is small, so 21 Pos nodes share it.
"""
import collections
import hashlib
import json
import math
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_gms
import kl_graft
import kl_hvk
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_scene
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
KNOWN_IN = ('b5e45efa',)                 # lastcall_1024n
OLD_PAD = (-2900.0, 859.0, 3900.0)
NEW_PAD = (7300.0, 1881.0, 3500.0)
D = tuple(NEW_PAD[i] - OLD_PAD[i] for i in range(3))
END = (7190.0, 1904.0, 3900.0)           # a cell at the far end of the strip (nav poly 1272 in lastcall_1024n)
PARK = (6950.0, 1881.0, 3370.0)          # the old bot park shifted by D
BOX_MARGIN, BOX_MAX = 120.0, 800.0
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55    # live-proven (re/engine_facts.md)
MEN = 5
GAPS = (40.0, 45.0, 50.0, 50.0, 55.0, 55.0)
FRACTIONS = (0.10, 0.20, 0.33, 0.50, 0.66, 0.82)
KINDS = ('bodyguard', 'yakuza', 'bodyguard', 'yakuza', 'bodyguard', 'yakuza')
ANCH = collections.OrderedDict([
    ('front door', (0, 19, -1100)), ('front lane', (-65, 19, -1307)), ('stairs01a bottom', (200, 159, 200)),
    ('wardrobe', (-500, 100, -440)), ('wardrobe2', (-140, 180, -120)), ('stairs01a top', (300, 460, 600)),
    ('lounge stairs', (900, 655, -600)), ('lounge stairs hi', (900, 650, -100)), ('rave', (-2900, 859, 1560)),
    ('daughter door A', (1500, 361, 3313)), ('daughter door B', (2500, 361, 3313)),
    ('firedoor W1', (-3190, 859, 2306)), ('storage 3rd', (-3180, 859, 2800)), ('firedoor W2', (-3790, 859, 3287))])
ENTRANCES = (('front door', 'front lane', 'stairs01a bottom'), ('wardrobe', 'wardrobe2', 'stairs01a top'),
             ('lounge stairs', 'lounge stairs hi', 'rave'), ('daughter door A', 'daughter door B'),
             ('firedoor W1', 'storage 3rd'), ('firedoor W2', 'daughter door B', 'front door'))
# nodes translated by D (names under ROOT). The chopper group's top carries its whole subtree (children are local to it).
HELI_TOP = 'EscapeSetup!EscapeChopper'
MOVE = ('Triggers!BoardingTrigger_Heli', 'Triggers!BoardingGameplayTrigger', 'PIP_Points!Boarding',
        'EscCameraSetup!CameraTrigger01', 'EscCameraSetup!CamPos01', 'EscCameraSetup!EscCamera01', 'EscCameraSetup!EscCameraLAST',
        'Gameplay!EscapeSetup!otrExitLevel', 'FASpecials!POI!POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeArea',
        'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn', 'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly')
EXIT06 = 'Specials!JumpPoints!06_Exit'
ALLYBOX = 'Gameplay!merc_bot_squad!AllyEscapeBox'
LOOTAREA = 'FASpecials!PIP!ExitLootArea'
OCT_HELI = ('EscapeSetup!EscapeChopper', 'EscapeSetup!EscapeChopper' + BS + 'Incomming', 'EscapeSetup!EscapeChopper' + BS + 'Escaping')
PAD_BOX = ((6500.0, 1881.0, 2700.0), (8000.0, 2800.0, 4300.0))


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


# ------------------------------------------------------------------ census
def census(sc, skip=()):
    """-> (actors, squads) of the .prp: ZFFActor nodes, nodes with a ZSquadScript controller; subtrees in `skip` (top nodes) left out."""
    skipped = set()
    for t in skip:
        skipped.update(range(t, sc.end[t]))
    a = s = 0
    for k in range(1, len(sc.nodes)):
        if k in skipped:
            continue
        if sc.cls(k) == 'ZFFActor':
            a += 1
        s += sum(1 for nm, _b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'ZSquadScript')
    return a, s


# ------------------------------------------------------------------ the walkable route
class Route:
    def __init__(self, B, nav, home, start):
        sx, sy, sz = start
        hs = nav.at(sx, sy, sz, lo=sy - 260, hi=sy + 40, part=home)
        ge = nav.at(END[0], END[1], END[2], dy=300.0, part=home)
        if hs is None or ge is None:
            raise ValueError('the START or the far cell is off the mesh part the crew walks')
        r = nav.path((sx, sy, sz, hs[0]), (END[0], ge[1], END[2], ge[0]))
        if r is None:
            raise ValueError('NO WALKABLE PATH from the START to the new pad')
        self.pts, self.length = r[0], r[1]
        self.nav = nav
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.total = self.cum[-1]

    def at(self, s):
        s = min(max(s, 0.0), self.total)
        for i in range(1, len(self.pts)):
            if self.cum[i] >= s:
                d = self.cum[i] - self.cum[i - 1] or 1.0
                t = (s - self.cum[i - 1]) / d
                return tuple(self.pts[i - 1][j] + (self.pts[i][j] - self.pts[i - 1][j]) * t for j in range(3))
        return tuple(self.pts[-1][:3])

    def samples(self, step=200.0):
        n = max(1, int(self.total // step))
        return [self.at(self.total * i / n) for i in range(n + 1)]

    def dist(self, p, samples=None):
        return min(math.dist((p[0], p[2]), (q[0], q[2])) for q in (samples or self.samples(100.0)))

    def facts(self):
        sm = self.samples(100.0)
        cl = [self.nav.clearance(q[0], q[1], q[2]) for q in sm]
        return dict(length=round(self.total), polyline_points=len(self.pts), samples=len(sm), min_clearance=round(min(cl)),
                    y_min=round(min(q[1] for q in sm)), y_max=round(max(q[1] for q in sm)), end=[round(v) for v in self.pts[-1][:3]])


def pick_spaced(cells, n, gap, clear, nav, min_clear):
    """n cells of `cells` ([(x, y, z, poly)], best first) at least `gap` apart (xz) and with clearance >= min_clear."""
    out = []
    for c in cells:
        if len(out) >= n:
            break
        if clear(c) < min_clear:
            continue
        if any(math.hypot(c[0] - q[0], c[2] - q[2]) < gap for q in out):
            continue
        out.append(c)
    return out


# ------------------------------------------------------------------ the plan
def plan_stations(B, nav, home, route, log):
    """Park cells (21 Pos + 06_Exit), 037 cells, loot-area place -> dict."""
    clear = lambda c: nav.clearance(c[0], c[1], c[2])
    cells = sorted(nav.around(PARK, 900.0, home, step=40.0, dy=300.0), key=lambda c: math.dist((c[0], c[2]), (PARK[0], PARK[2])))
    park = pick_spaced(cells, 22, 70.0, clear, nav, 25.0)
    if len(park) < 22:
        park = pick_spaced(cells, 22, 50.0, clear, nav, 15.0)
    if len(park) < 22:
        raise ValueError('only %d park cells near the new pad' % len(park))
    t037 = route.at(route.total - 2500.0)
    c37 = sorted(nav.around(t037, 350.0, home, step=40.0, dy=300.0), key=lambda c: math.dist((c[0], c[2]), (t037[0], t037[2])))
    p37 = pick_spaced(c37, 7, 110.0, clear, nav, 25.0)
    if len(p37) < 7:
        c37 = sorted(nav.around(t037, 700.0, home, step=40.0, dy=300.0), key=lambda c: math.dist((c[0], c[2]), (t037[0], t037[2])))
        p37 = pick_spaced(c37, 7, 90.0, clear, nav, 20.0)
    if len(p37) < 7:
        raise ValueError('only %d cells for the 037 stations' % len(p37))
    loot = route.at(route.total - 1200.0)
    log('  stations: %d park cells, 037 near %s, loot area at %s' % (len(park), [round(v) for v in t037], [round(v) for v in loot]))
    return dict(park=park, p37=p37, loot=loot)


def plan_waves(B, nav, home, route, log):
    sc = B.sc
    clear = lambda c: nav.clearance(c[0], c[1], c[2])
    plan = []
    for w in range(len(GAPS)):
        names = ENTRANCES[w]
        lists = {}
        for nme in names:
            a = ANCH[nme]
            cl = sorted(nav.around(a, 900.0, home, step=40.0, dy=300.0), key=lambda c, a=a: math.dist(c[:3], a))
            lists[nme] = [c for c in cl if clear(c) >= 30.0]
        ents = []
        for j in range(MEN):
            order = [names[(j + i) % len(names)] for i in range(len(names))]
            for nme in order:
                c = next((c for c in lists[nme] if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= 220.0 for q in ents)), None)
                if c is not None:
                    ents.append(c)
                    break
        if len(ents) < MEN:
            raise ValueError('wave %d: only %d entrance cells' % (w + 1, len(ents)))
        T = route.at(route.total * FRACTIONS[w])
        cand = [c for c in nav.around(T, 1500.0, home, step=40.0, dy=300.0) if 300.0 <= math.hypot(c[0] - T[0], c[2] - T[2]) <= 1500.0 and clear(c) >= 40.0]
        cand.sort(key=lambda c: abs(math.hypot(c[0] - T[0], c[2] - T[2]) - 700.0))
        posts = []
        for e in ents:
            best = None
            for c in cand:
                if any(math.hypot(c[0] - q[0], c[2] - q[2]) < 250.0 for q in posts):
                    continue
                d = math.dist(c[:3], e[:3])
                if best is None or d < best[0]:
                    best = (d, c)
            if best is None:
                raise ValueError('wave %d: no post left' % (w + 1))
            posts.append(best[1])
        plan.append(dict(name='%d' % (w + 1), gap=GAPS[w], kind=KINDS[w], men=list(zip(ents, posts)), target=T, fraction=FRACTIONS[w]))
        log('  wave %d (%s, %g s after the previous link): entrances %s, posts around %s' % (
            w + 1, KINDS[w], GAPS[w], '/'.join(names), [round(v) for v in T]))
    return plan


def make_waves(B, plan):
    """The new nodes (kl_old_waves.make_waves with the pools and the entrances of this pass) -> (maker, [tops], report)."""
    import kl_fa_fed as FED
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), KOW.CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops = [clock]
    rep = collections.OrderedDict(waves=[])
    cp = lambda n: R + KOW.CLOCK + BS + n

    def single(name, delay, listed):
        n = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), name))
        M.place(n, (0.0, 0.0, 0.0))
        M.set(n, 'TriggerDelay2', {0: float(delay), 4: listed})
        return cp(name)
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    tmpl = node(R + 'AI_Players!Enemies!SecondRun!YokoGuards')
    pools = {'yakuza': [], 'bodyguard': []}
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor' or B.values(k).get('ZFFActor[0]') != 'Enemy':
            continue
        if not any(sc.p.key(nm) == 'ZSoldier' for nm, _b in sc.nodes[k]['ctrls']):
            continue
        t = sc.names[sc.top[k]]
        if 'Bouncer' in str(B.values(k).get('ZLNKOBJ[2]')):
            continue
        if t.startswith('AI_Players!Enemies!SecondRun!'):
            pools['yakuza'].append(k)
        elif t.startswith('AI_Players!Enemies!FirstRun!'):
            pools['bodyguard'].append(k)
    for i, w in enumerate(plan):
        nxt = plan[i + 1] if i + 1 < len(plan) else None
        pool = pools[w['kind']]
        if not pool:
            raise ValueError('no %s actors to clone' % w['kind'])
        top = FED.clone_built(M, B, tmpl, KOW.WAVE_G + 'Wave_' + w['name'])
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})      # parked until a rout names it
        me = R + KOW.WAVE_G + 'Wave_' + w['name']
        d = top.add(M.clone('F07', sq2(KOW.FORM), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, (e, q) in enumerate(w['men']):
            pp = d.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, q[:3])
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        for j, (e, q) in enumerate(w['men']):
            a = pool[(i * MEN + j) % len(pool)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], 'Wave_%s_%02d' % (w['name'], j + 1)))
            dx, dz = q[0] - e[0], q[2] - e[2]
            if math.hypot(dx, dz) < 50.0:
                dx, dz = w['target'][0] - e[0], w['target'][2] - e[2]
            L = math.hypot(dx, dz) or 1.0
            M.place(grp, e[:3], KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(M, B, a))
        go = cp('Go_' + w['name'])
        pace = single('Pace_' + w['name'], w['gap'], [go])
        single('Go_' + w['name'], KOW.GO_DELAY, [me + BS + '10_Defend'] + ([cp('Pace_' + nxt['name'])] if nxt else []))
        rep['waves'].append(dict(name=w['name'], kind=w['kind'], squad=me, pace=pace, go=go, gap=w['gap'], fraction=w['fraction'],
                                 men=[[[round(v) for v in e[:3]], [round(v) for v in q[:3]]] for e, q in w['men']]))
        tops.append(top)
    rep['first'] = rep['waves'][0]['pace']
    return M, tops, rep


# ------------------------------------------------------------------ build
def build(src, dst, force=False, log=print):
    h = md5(src)
    if not force and not any(h.startswith(k) for k in KNOWN_IN):
        raise SystemExit('refusing: %s md5 %s is not one of %s (use --force if other passes were chained first)' % (src, h, KNOWN_IN))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    B = KB.Built(src)
    sc = B.sc
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if sc.resolve(R + KOW.CLOCK):
        shutil.copyfile(src, dst)
        log('%s already holds the wave clock: copied unchanged' % src)
        return 0
    # ---- round trips
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
    hv = kl_hvk.Hvk(B['.HVK'])
    if hv.serialize() != B['.HVK']:
        raise ValueError('kl_hvk does not reproduce the .HVK')
    big0 = {e: len(B[e]) for e in KB.BIG}
    a0, s0 = census(sc)
    log('input: %d actors / %d squads (engine-proven %d / %d)' % (a0, s0, ENGINE_ACTORS, ENGINE_SQUADS))

    # ---- the walkable route and the places on it
    nav = KB.Nav(A.nav, links=True)
    st = KB.stations(B, nav)
    home, start = st['home'], st['start_mid']
    route = Route(B, nav, home, start)
    rf = route.facts()
    log('route START -> new pad: %s' % rf)
    sp = plan_stations(B, nav, home, route, log)
    plan = plan_waves(B, nav, home, route, log)

    # ---- the budget: civilians nearest to the route stay
    tops = sc.tops()
    after = [t for t in tops if '030_AfterLoot' in sc.names[t]]
    civ = [t for t in tops if sc.names[t].startswith('Gameplay!FA_Crowd!Civ_')]
    ba, bs = census(sc, after + civ)
    wa, ws = MEN * len(plan), len(plan)
    per_a = (census(sc, after)[0] - ba) / max(1, len(civ))
    per_s = (census(sc, after)[1] - bs) / max(1, len(civ))
    K = int(min((ENGINE_ACTORS - ba - wa) // max(1, per_a), (ENGINE_SQUADS - bs - ws) // max(1, per_s), len(civ)))
    if K < 1:
        raise ValueError('no room for a civilian: base %d/%d + waves %d/%d' % (ba, bs, wa, ws))
    smp = route.samples(100.0)
    rank = sorted(civ, key=lambda t: route.dist(B.at(t + 5), smp))
    keep_civ, drop_civ = rank[:K], rank[K:]
    removed = after + drop_civ
    log('budget: base %d/%d (no civilians, no AfterLoot), waves +%d/%d, civilians kept %d of %d -> %d actors / %d squads' % (
        ba, bs, wa, ws, K, len(civ), ba + wa + int(K * per_a), bs + ws + int(K * per_s)))

    # ---- the waves
    M, wtops, wrep = make_waves(B, plan)
    q, order = M.scene(wtops)
    picks = [(sc, t) for t in tops if t not in set(removed)] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'lastcall2')
    gone_nodes = set()
    for t in removed:
        gone_nodes.update(range(t, sc.end[t]))

    # ---- node places (.prp ZGEOM[2] and the .gms record)
    moves = []

    def setpos(path, pos, why):
        ks, kj = one(sc, path), Jn.resolve(R + path)
        if len(kj) != 1:
            raise ValueError('%s: %d nodes in the joined tree' % (path, len(kj)))
        kj = kj[0]
        lab = J.labels('dd', Jn.cls(kj))
        old = tuple(float(x) for x in kl_fa.node_values(Jn, kj)[lab.index('ZGEOM[2]')])
        ent = B.ents[ks - 1]
        eo = struct.unpack_from('<3f', ent.trans, 0)
        if max(abs(eo[i] - old[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: .prp place %s and .gms place %s differ' % (path, old, eo))
        pa = sc.parent[ks]
        if pa > 0 and max(abs(B.at(pa)[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: the parent is not at the origin' % path)
        new = tuple(float(x) for x in pos)
        kl_fa.edit(Jn, kj, None, lambda us: AU.setv(Jn, us, lab.index('ZGEOM[2]'), list(new)))
        ent.trans = struct.pack('<3f', *new) + ent.trans[12:]
        moves.append((path, [round(v) for v in old], [round(v) for v in new], why))

    shift = lambda p: tuple(p[i] + D[i] for i in range(3))
    for nme in (HELI_TOP,) + MOVE:
        ks = one(sc, nme)
        lab = J.labels('dd', sc.cls(ks))
        old = tuple(float(x) for x in kl_fa.node_values(sc, ks)[lab.index('ZGEOM[2]')])
        if nme == HELI_TOP:
            if sc.parent[ks] != 0 or max(abs(v) for v in old) > 0.5:
                raise ValueError('the chopper group is not a top at the origin')
        setpos(nme, shift(old), 'heli set +D')
    # bot stations
    park, p37 = sp['park'], sp['p37']
    setpos(EXIT06, (park[0][0], park[0][1], park[0][2]), '06_Exit: nearest park cell')
    pi = 1
    for n in range(2, 9):
        sq = 'Gameplay!merc_bot_squad!Squad#%02d' % n
        for k in range(one(sc, sq), sc.end[one(sc, sq)]):
            if sc.names[k].startswith('Pos#') and sc.names[sc.parent[k]] in ('037_DefendBehaviour_out_car', '050_DefendBehaviour_out', '050_DefendBehaviour_out_b'):
                par = sc.names[sc.parent[k]]
                rel = sc.path[k].split(R, 1)[1]
                if par.startswith('037'):
                    c = p37[n - 2]
                else:
                    c = park[pi]
                    pi += 1
                setpos(rel, c[:3], 'bot station')
    if pi != 1 + 14 + 7:
        raise ValueError('bot Pos nodes found %d, wanted 21' % (pi - 1))
    # ally box: centre on the park cells (floor + the old offset), half extents grown to hold them with a margin
    kb = one(sc, ALLYBOX)
    half = list(B.box(kb))
    cx = sum(c[0] for c in park) / len(park)
    cz = sum(c[2] for c in park) / len(park)
    cy = min(c[1] for c in park) + 201.0
    need = [max(abs(c[0] - cx) for c in park), max(abs(c[1] - cy) for c in park), max(abs(c[2] - cz) for c in park)]
    new_half = [max(half[a], need[a] + BOX_MARGIN) for a in range(3)]
    if any(v > BOX_MAX for v in new_half):
        raise ValueError('ally box needs half extents %s (max %g)' % (new_half, BOX_MAX))
    setpos(ALLYBOX, (cx, cy, cz), 'ally box over the park')
    kj = Jn.resolve(R + ALLYBOX)[0]
    lab = J.labels('dd', Jn.cls(kj))
    kl_fa.edit(Jn, kj, None, lambda us: [AU.setv(Jn, us, lab.index('ZBoxPrimitive[%d]' % a), float(new_half[a])) for a in range(3)])
    log('  ally box: half %s -> %s, centre %s' % ([round(v) for v in half], [round(v) for v in new_half], [round(cx), round(cy), round(cz)]))
    setpos(LOOTAREA, (sp['loot'][0], sp['loot'][1] + 41.0, sp['loot'][2]), 'exit loot area on the route')

    # ---- references into the removed subtrees: cut the dead entries (the gate paths)
    dead = []
    for k, holder, field, s, hit in J.references(sc):
        if not hit or k < 0 or k in gone_nodes:
            continue
        tgt = sc.resolve(s)
        if tgt and tgt[0] in gone_nodes:
            dead.append(k)
    dead = sorted(set(dead))
    cut = 0
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
    log('  references into the removed subtrees: %d holders (%s), %d entries cut' % (len(dead), ', '.join(sc.names[k] for k in dead[:4]), cut))
    # the first Pace of the chain: AIMonitor START list
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [wrep['first']]))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = census(Jn)
    if fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('over the budget: %d actors / %d squads' % (fa, fs))
    log('census after: %d actors / %d squads (limit %d / %d)' % (fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))

    # ---- the heli's place in the .HVK and the room tree: items looked up before the renumbering
    slot0 = A.slots()
    heli_ents = {n: B.ents[one(sc, n) - 1] for n in OCT_HELI}
    heli_ids = {n: slot0[e] + 2 for n, e in heli_ents.items()}
    root3 = octx.rooms[0][3]
    boxes = {}
    for n, iid in heli_ids.items():
        it = next((x for x in root3.items if x[0] == iid), None)
        if it is None:
            raise ValueError('%s is not an item of the root group tree' % n)
        lo, hi = root3.world(it[1:4]), root3.world([v + 1 for v in it[4:7]])
        lo, hi = shift(lo), shift(hi)
        if n == OCT_HELI[0]:
            lo = tuple(min(lo[a], PAD_BOX[0][a]) for a in range(3))
            hi = tuple(max(hi[a], PAD_BOX[1][a]) for a in range(3))
        boxes[n] = (lo, hi)
    chop = one(sc, HELI_TOP)
    crefs = {B.ents[j - 1].ref for j in range(chop, sc.end[chop])}
    moved_hvk = []
    for si, s in enumerate(hv.shapes):
        if s.type == kl_hvk.STATIC:
            continue
        for j, inst in enumerate(s.inst):
            if kl_hvk.ref(inst) in crefs:
                p = struct.unpack_from('<3f', inst, 0)
                q3 = tuple(p[i] + D[i] / 100.0 for i in range(3))
                s.inst[j] = struct.pack('<3f', *q3) + inst[12:]
                moved_hvk.append((si, j, [round(v, 2) for v in p], [round(v, 2) for v in q3]))
    log('  .HVK: %d non-static placements of the chopper moved by D/100 %s' % (len(moved_hvk), moved_hvk))

    # ---- .gms / .buf: remove, then add (freed REF ids are reused, as kl_fa_bots_dyn does)
    gone_ents = set()
    for t in removed:
        top = B.ents[t - 1]
        gone_ents.update(top.walk())
    free = sorted(e.ref for e in gone_ents)
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    cuts = collections.Counter()
    for t in removed:
        r = A.remove(B.ents[t - 1])
        cuts['links'] += r['links']
        cuts['pairs'] += r['pairs']
    log('  scene: %d entities out (%d list entries and %d room pairs dropped with them)' % (len(gone_ents), cuts['links'], cuts['pairs']))
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
    for t in wtops:
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
    # ---- .oct / .rmi / .rmc
    elsewhere = sum(1 for r, room in enumerate(octx.rooms) for ti, t in enumerate(room) if t is not None and (r, ti) != (0, 3)
                    for it in t.items if it[0] in {slot0[e] + 2 for e in gone_ents})
    if elsewhere:
        raise ValueError('%d room-tree items outside the root group tree name a removed entity' % elsewhere)
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    drop = {slot0[e] + 2 for e in gone_ents} | set(heli_ids.values())
    octn, rmin, rmcn = O.remap_ids(octx, ids, drop), O.remap_ids(rmi, ids, drop), O.remap_ids(rmc, ids, drop)
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for n, (lo, hi) in boxes.items():
        items.append((slot1[heli_ents[n]] + 2, lo, hi))
    for t in wtops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    repointed, new_prm = 0, None
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
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.HVK']] = hv.serialize()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    big1 = {e: len(new[B.ext[e]]) for e in KB.BIG}
    if big0 != big1:
        raise ValueError('a large block changed its size: %s -> %s' % (big0, big1))
    # ---- write into a scratch folder, seal (room-list strays) and re-verify there, then copy the zip out
    work = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc2_work')
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    zp = kl_graft.write_zip(os.path.join(work, 'F01_Main.zip'), [(n, new[n]) for n in B.order])
    import kl_fa_bank
    sealed = kl_fa_bank.seal(work, log=lambda *_: None)
    problems = kl_fa_bank.reverify(work, log=lambda *_: None)
    if problems:
        raise ValueError('reverify: %s' % problems[:5])
    shutil.copyfile(zp, dst)
    shutil.rmtree(work)
    rep = collections.OrderedDict(
        source=src, source_md5=h, out=dst, out_md5=md5(dst), members_changed=changed, entities_before=len(B.ents), entities=len(allents),
        entities_removed=len(gone_ents), entities_added=len(order), census_before=[a0, s0], census_after=[fa, fs],
        civilians_kept=K, civilians_removed=len(drop_civ), afterloot_removed=len(after), slot_ids_moved=moved, prm_roots_repointed=repointed,
        room_tree_items_added=len(items), sealed=sealed, route=rf, moves=moves, hvk=moved_hvk, waves=wrep, refs_cut=cut)
    with open(os.path.splitext(dst)[0] + '.lastcall2.json', 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    log('written %s md5 %s; members changed: %s; %d slot ids renumbered' % (dst, rep['out_md5'], ' '.join(changed), moved))
    return 0


def check(zp, log=print):
    B = KB.Built(zp)
    sc = B.sc
    a, s = census(sc)
    log('census: %d actors / %d squads (limit %d / %d)' % (a, s, ENGINE_ACTORS, ENGINE_SQUADS))
    civ = [t for t in sc.tops() if sc.names[t].startswith('Gameplay!FA_Crowd!Civ_')]
    log('civilians: %d' % len(civ))
    for nme in (HELI_TOP, 'EscapeSetup!EscapeChopper' + BS + 'EscapeChopper_OnMap', EXIT06, ALLYBOX, LOOTAREA, 'EscCameraSetup!EscCamera01'):
        k = one(sc, nme)
        log('%-60s %s' % (nme, [round(v) for v in B.at(k)]))
    log('wave clock: %s' % ('yes' if sc.resolve(R + KOW.CLOCK) else 'no'))
    nav = KB.Nav(B.scene.nav, links=True)
    st = KB.stations(B, nav)
    r = Route(B, nav, st['home'], st['start_mid'])
    log('route: %s' % r.facts())
    bad = 0
    if a > ENGINE_ACTORS or s > ENGINE_SQUADS:
        log('FAIL over the budget')
        bad = 1
    return bad


def main():
    a = sys.argv[1:]
    force = '--force' in a
    if force:
        a.remove('--force')
    if len(a) == 2 and a[0] == 'check':
        return check(a[1])
    if len(a) == 3 and a[0] == 'build':
        return build(a[1], a[2], force)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
