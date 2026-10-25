#!/usr/bin/env python3
"""kl_club_lastcall3.py - Last Call (DM05A) pass 1025a: the heli leaves its spline start, guards on the roof, a FULL club. OFFLINE.

  python tools/kl_club_lastcall3.py build <live F01_Main.zip 7ef0404f> <out F01_Main.zip> [--alt] [--crowd 34] [--force] [--variant v3|full|lite]
  python tools/kl_club_lastcall3.py check <zip> [--variant ...]
  python tools/kl_club_lastcall3.py stage <live zip> <out folder> --rehearse <scratch> [--variant full,lite]   (main + alt per variant, INSTALL/UNDO bats, rehearsed)
  lastcall3b (2026-10-25): variants 'full' (56 civilians, >=120 apart) and 'lite' (40 civilians); roof squads on the LOWER roof, >=600 from the pad and climb top.

Owner report (2026-10-25, first live look at lastcall2): grey screen when boarding the helicopter and no chopper model; no enemies on
the roof; no music; citizens keep spawning in, the club should be full and mostly dancing.

WHAT IT DOES (chains over the live zip; every step is by NAME)
 1. CROWD: kl_club_crowd.plan + kl_fa_civs.add put N more civilians (default 34) on the ground floor and the upper floor
    (alert 450, as club_1024d) -> 22 + 34 = 56 civilians.
 2. f3 = 1 ("in the world from load", ZSquadScript field 3) on EVERY civilian squad (they were 0 = parked and hidden until a rout
    names them: the spawning-in the owner saw) and on the helicopter's squad (EscapeSetup!EscapeChopper, 0 before).
 3. ROOF: 3 squads x 4 men (OldWaves!Roof_1..3, f3 = 1, Yakuza / bodyguard actors of the map) posted on the roof stretch of the
    START -> pad route (approach, climb, pad strip); a TriggerDelay2 per squad in the AIMonitor START list names its Defend rout.
 4. HELI (main variant only): the type-3 vehicle placement of the .HVK goes back to the ORIGIN with the identity frame, as in stock
    M06_FA_A / F03 / F06. lastcall2 had moved it by D/100 with the rest of the set. --alt keeps it where lastcall2 left it.
 5. DANCE: kl_club_dance_1024.build(group='KL_Dance2!') gives the new civilians their own MiniCutsceneRout groups (the clip is
    already in the .ANM from the first dance pass).
GUESSES, said plainly: why the ZHeli stays at its spline start (KLHook.log: 15394, 6942, 18351 for the whole wait) is NOT proven;
f3 = 0 and the moved HVK placement are the two candidates (b5e45efa also had f3 = 0 and the old placement, so f3 alone is not a
proven cause). Main = both fixes, alt = f3 only. Totals ~ 99 + 34 + 12 = 145 actors / 53 + 34 + 3 = 90 squads: over the largest
build proven live (99 / 55), at stock Last Call (148 / 90). Roof posts are chosen from the mesh, not play-tested.
"""
import collections
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_fa_civs as CV
import kl_gms
import kl_graft
import kl_hvk
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_scene
import kl_club_crowd as CR
import kl_club_dance_1024 as DN
import kl_club_lastcall2 as L2
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
MD5_LIVE = '7ef0404f95c51f8755dba25174f130d7'
MD5_BASE4 = 'd5f8522bb45c1757e136e999e35d53f5'      # the live zip after lastcall3b lite + clubmusic (lastcall4 builds on it)
TAG = '.before-1025lastcall3'
CROWD, UPPER, ALERT, SEED = 34, 10, 450.0, 11
ROOF_SQUADS, ROOF_MEN, ROOF_Y = 3, 4, 1800.0
ROOF_AT = (0.12, 0.5, 0.92)               # along the roof stretch of the route
SIBLINGS = os.environ.get('KL_DM05A_DIR', 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days/KLExpansion/Maps/DM05A')
CIV_PREFIX = 'Gameplay!FA_Crowd!Civ_'
DANCE2 = 'KL_Dance2!'
md5 = L2.md5
one = L2.one

# ---- lastcall3b (2026-10-25): variants. 'v3' = the first pass, unchanged (default of build/check/stage without --variant).
# Verifier of lastcall3: roof squad R1_01 stood 73 units from the climb top and R3_02 ~125 from the pad centre (on Hasta a nearby squad
# destroyed the helicopter); 145 actors / 90 squads is over the proven 99 / 55; two civilians 50 units apart.
# 'lower' roof mode: the squads stand on the LOWER roof (y about 1460, the long approach stretch before the climb), every man at least
# `far` units (xz AND 3D) from the pad centre and from the climb top. The upper roof strip (x 6980..7380, z 3580..4460) is only 800 long
# from the climb top to the pad centre, so no cell of it can be 600 from both: nobody stands on it.
CLIMB_TOP = (7392.67, 1904.33, 4303.21)   # route.pts[first point at y >= 1800] of the live build (measured 2026-10-25 by explore.py)
LOWER_BACK = (100.0, 1500.0, 2900.0)      # roof squad i is posted this far (route length) back from the end of the lower stretch
VARIANTS = {
    'v3':   dict(crowd=34, sep=100.0, roof='stretch', far=0.0, spread=0.0, tag='.before-1025lastcall3', stem='lastcall3'),
    'full': dict(crowd=34, sep=130.0, roof='lower', far=600.0, spread=120.0, tag='.before-1025lastcall3b', stem='lastcall3b'),
    'lite': dict(crowd=18, sep=130.0, roof='lower', far=600.0, spread=120.0, tag='.before-1025lastcall3b', stem='lastcall3b'),
    # lastcall4 (2026-10-25): 'pack' / 'pack_lite' build on the LIVE zip d5f8522b (40 civilians, 129 actors / 74 squads). `add` new civilians
    # (`upper` of them on the upper floor), the parked campaign men in `remove` go (see PACK_REMOVE). Only a 'main' build per variant.
    'pack':      dict(mode='pack', base=MD5_BASE4, add=50, upper=24, sep=115.0, spread=110.0, roof='keep', far=600.0, civ_only=True,
                      remove=None, per=8, dgroup='KL_Dance3!', rout='KLDance3_%02d', doff=17, stagger=0.53, crowd=50,
                      tag='.before-1025lastcall4', stem='lastcall4', want=90, want_upper=30),
    'pack_lite': dict(mode='pack', base=MD5_BASE4, add=30, upper=12, sep=115.0, spread=110.0, roof='keep', far=600.0, civ_only=True,
                      remove=None, per=8, dgroup='KL_Dance3!', rout='KLDance3_%02d', doff=17, stagger=0.53, crowd=30,
                      tag='.before-1025lastcall4', stem='lastcall4', want=70, want_upper=24),
}
CFG = dict(VARIANTS['v3'])


# ------------------------------------------------------------------ roof squads
def plan_roof(B, nav, home, route, log):
    clear = lambda c: nav.clearance(c[0], c[1], c[2])
    pts = [i for i, p in enumerate(route.pts) if p[1] >= ROOF_Y]
    if len(pts) < 2:
        raise ValueError('the route has no stretch above y %g' % ROOF_Y)
    s0, s1 = route.cum[pts[0]], route.cum[-1]
    top = route.pts[pts[0]]
    far = CFG['far']
    if far and math.dist(top, CLIMB_TOP) > 5.0:
        raise ValueError('the climb top is %s, not the measured %s' % ([round(v) for v in top], CLIMB_TOP))
    pad = L2.NEW_PAD
    plan, used = [], []
    for i in range(ROOF_SQUADS):
        if CFG['roof'] == 'lower':
            T = route.at(route.cum[pts[0] - 1] - LOWER_BACK[i])
        else:
            T = route.at(s0 + (s1 - s0) * ROOF_AT[i])
        # (radius, least clearance, least spacing): the first that yields ROOF_MEN men. 'lower' relaxes (the strip is narrow, GUESS values);
        # 'stretch' (v3) uses the first row only, as before.
        for radius, minclear, gap in (((700.0, 40.0, 160.0), (1100.0, 40.0, 160.0), (1100.0, 25.0, 140.0), (1400.0, 25.0, 120.0)) if CFG['roof'] == 'lower'
                                      else ((700.0, 40.0, 160.0),)):
            cand = [c for c in nav.around(T, radius, home, step=40.0, dy=300.0) if abs(c[1] - T[1]) < 150.0 and clear(c) >= minclear]
            if far:
                cand = [c for c in cand if min(math.hypot(c[0] - q[0], c[2] - q[2]) for q in (pad, top)) >= far
                        and min(math.dist(c[:3], q) for q in (pad, top)) >= far]
            cand.sort(key=lambda c: math.hypot(c[0] - T[0], c[2] - T[2]))
            men = []
            for c in cand:
                if len(men) >= ROOF_MEN:
                    break
                if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= gap for q in men + used):
                    men.append(c)
            if len(men) >= ROOF_MEN:
                break
        if len(men) < ROOF_MEN:
            raise ValueError('roof squad %d: only %d cells around %s' % (i + 1, len(men), [round(v) for v in T]))
        used += men
        for c in men:
            if far and min(math.dist(c[:3], q) for q in (pad, top)) < far:
                raise ValueError('roof post %s is nearer than %g to the pad or the climb top' % (c, far))
        plan.append(dict(name='R%d' % (i + 1), kind='yakuza' if i % 2 == 0 else 'bodyguard', men=men, target=T))
        log('  roof squad %d (%s): around %s, cells %s' % (i + 1, plan[-1]['kind'], [round(v) for v in T], [[round(v) for v in c[:3]] for c in men]))
    return plan


def make_roof(B, plan, clock_name='OldWaves!RoofClock', pre='Roof_', tmpl_path='AI_Players!Enemies!SecondRun!YokoGuards'):
    """-> (maker, tops, report). Pre-placed squads (f3 = 1) with a Defend rout each, a Go timer each (named in the START list)."""
    import kl_fa_fed as FED
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), clock_name)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops = [clock]
    rep = collections.OrderedDict(squads=[], go=[])
    tmpl = node(R + tmpl_path)
    pools = {'yakuza': [], 'bodyguard': []}
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor' or B.values(k).get('ZFFActor[0]') != 'Enemy':
            continue
        if not any(sc.p.key(nm) == 'ZSoldier' for nm, _b in sc.nodes[k]['ctrls']):
            continue
        if 'Bouncer' in str(B.values(k).get('ZLNKOBJ[2]')):
            continue
        t = sc.names[sc.top[k]]
        if t.startswith('AI_Players!Enemies!SecondRun!'):
            pools['yakuza'].append(k)
        elif t.startswith('AI_Players!Enemies!FirstRun!'):
            pools['bodyguard'].append(k)
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    for i, w in enumerate(plan):
        pool = pools[w['kind']]
        if not pool:
            raise ValueError('no %s actors to clone' % w['kind'])
        top = FED.clone_built(M, B, tmpl, 'OldWaves!' + pre + w['name'])
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 1, **{j: [] for j in range(4, 19)}})          # in the world from load
        me = R + 'OldWaves!' + pre + w['name']
        d = top.add(M.clone('F07', sq2(KOW.FORM), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, c in enumerate(w['men']):
            pp = d.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, c[:3])
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        for j, c in enumerate(w['men']):
            a = pool[(i * ROOF_MEN + j) % len(pool)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], pre + '%s_%02d' % (w['name'], j + 1)))
            dx, dz = w['target'][0] - c[0], w['target'][2] - c[2]
            if math.hypot(dx, dz) < 50.0:
                dx, dz = 1.0, 0.0
            L = math.hypot(dx, dz) or 1.0
            M.place(grp, c[:3], KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(M, B, a))
        go = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'Go_' + w['name']))
        M.place(go, (0.0, 0.0, 0.0))
        M.set(go, 'TriggerDelay2', {0: 0.1 + 0.4 * i, 4: [me + BS + '10_Defend']})
        rep['go'].append(R + clock_name + BS + 'Go_' + w['name'])
        rep['squads'].append(dict(name=w['name'], kind=w['kind'], squad=me, men=[[round(v) for v in c[:3]] for c in w['men']]))
        tops.append(top)
    return M, tops, rep


# ------------------------------------------------------------------ civilians too close together
def spread_civs(B, Jn, nav, minsep, log):
    """Move any civilian that stands nearer than `minsep` (xz) to an EARLIER civilian (scene order) to the nearest mesh cell that keeps
    `minsep` + 10 from every actor of the build and clear of walls and LevelBound boxes. Moves the group node (the place) and the
    tbCivRunToGate box (place + 300 in y), in the joined .prp (ZGEOM[2]) and the .gms record. The octree item boxes of a moved civilian
    are NOT updated (the shift is under 300 units and civilians are dynamic actors; GUESS, not play-tested). -> list of moves."""
    sc = B.sc
    civs = [(k, g) for k, g, _n in DN.dancers(B)]
    actors = [tuple(B.at(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor']
    kill = CV.bound_boxes(B)
    pos = {g: list(B.at(g)) for k, g in civs}
    moves = []

    def setpos(node, new):
        kj = Jn.resolve(sc.path[node])
        if len(kj) != 1:
            raise ValueError('%s: %d nodes in the joined tree' % (sc.path[node], len(kj)))
        kj = kj[0]
        lab = J.labels('dd', Jn.cls(kj))
        old = tuple(float(x) for x in kl_fa.node_values(Jn, kj)[lab.index('ZGEOM[2]')])
        ent = B.ents[node - 1]
        eo = struct.unpack_from('<3f', ent.trans, 0)
        if max(abs(eo[i] - old[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: .prp place %s and .gms place %s differ' % (sc.path[node], old, eo))
        kl_fa.edit(Jn, kj, None, lambda us: AU.setv(Jn, us, lab.index('ZGEOM[2]'), [float(v) for v in new]))
        ent.trans = struct.pack('<3f', *new) + ent.trans[12:]
        return old

    for _round in range(len(civs)):
        bad = None
        for ia in range(len(civs)):
            for ib in range(ia + 1, len(civs)):
                a, b = civs[ia][1], civs[ib][1]
                if math.hypot(pos[a][0] - pos[b][0], pos[a][2] - pos[b][2]) < minsep:
                    bad = (a, b)
                    break
            if bad:
                break
        if not bad:
            return moves
        g = bad[1]
        p0 = pos[g]
        hit = nav.at(p0[0], p0[1], p0[2], dy=100.0)
        if not hit:
            raise ValueError('civilian %s is off the mesh' % sc.names[g])
        others = [pos[h] for _k, h in civs if h != g] + [a for a in actors if math.dist(a, p0) > 1.0]
        best = None
        for c in nav.around(p0, 300.0, nav.part[hit[0]], step=20.0, dy=100.0):
            if abs(c[1] - p0[1]) > 60.0 or nav.clearance(c[0], c[1], c[2]) < KB.CLEAR:
                continue
            if any(math.hypot(c[0] - o[0], c[2] - o[2]) < minsep + 10.0 for o in others):
                continue
            if CV.in_bound(B, kill, (c[0], c[1], c[2]), CV.BOUND_MARGIN) is not None:
                continue
            d = math.hypot(c[0] - p0[0], c[2] - p0[2])
            if best is None or d < best[0]:
                best = (d, c)
        if best is None:
            raise ValueError('no cell within 300 units keeps civilian %s %g from the others' % (sc.names[g], minsep))
        c = best[1]
        new = (float(c[0]), float(c[1]), float(c[2]))
        top = sc.top[g]
        box = [k for k in range(top, sc.end[top]) if sc.names[k] == 'tbCivRunToGate']
        if len(box) != 1:
            raise ValueError('%s: %d tbCivRunToGate nodes' % (sc.names[top], len(box)))
        setpos(g, new)
        setpos(box[0], (new[0], new[1] + 300.0, new[2]))
        pos[g] = list(new)
        moves.append([sc.names[g], [round(v) for v in p0], [round(v) for v in new]])
        log('  spread: %s %s -> %s' % (moves[-1][0], moves[-1][1], moves[-1][2]))
    raise ValueError('civilian spread did not settle')


# ------------------------------------------------------------------ stage 2: roof, f3, heli
def squads_f3(Jn, want, log):
    """f3 = 1 on every ZSquadScript whose top matches `want(top name)`. -> list of (path, before)."""
    done = []
    for k, i, v in kl_fa.controllers(Jn, 'ZSquadScript'):
        t = Jn.names[Jn.top[k]]
        if not want(t, Jn.path[k]):
            continue
        before = v[3]
        if before == 1:
            continue
        kl_fa.edit(Jn, k, i, lambda us: AU.setv(Jn, us, 3, 1))
        done.append((Jn.path[k], before))
    return done


def roof_pass(src, dst, hvk_origin, log=print):
    B = KB.Built(src)
    sc = B.sc
    fresh = not sc.resolve(R + 'OldWaves!RoofClock')
    if not fresh and not CFG.get('civ_only'):
        shutil.copyfile(src, dst)
        log('already holds the roof clock: copied unchanged')
        return dict(unchanged=True)
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
    a0, s0 = L2.census(sc)
    nav = KB.Nav(A.nav, links=True)
    if fresh:
        st = KB.stations(B, nav)
        home, start = st['home'], st['start_mid']
        route = L2.Route(B, nav, home, start)
        log('route START -> pad: %s' % route.facts())
        plan = plan_roof(B, nav, home, route, log)
        M, tops, rrep = make_roof(B, plan)
        q, order = M.scene(tops)
        Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'lastcall3')
    elif CFG.get('guards'):                 # lastcall5: bodyguard squads inside (same maker as the roof squads, own clock and names)
        route = None
        M, tops, rrep = make_roof(B, CFG['guards'], 'OldWaves!GuardClock', 'Guard_', 'OldWaves!Roof_R1')
        q, order = M.scene(tops)
        Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'lastcall5')
    else:                                   # lastcall4 (civ_only): the roof squads are already in; only f3 / spread of the new civilians
        route, tops, order, rrep = None, [], [], dict(squads=[], go=[])
        Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'lastcall4')
    # ---- f3
    f3 = squads_f3(Jn, lambda t, p: t.startswith(CIV_PREFIX) or t == L2.HELI_TOP, log)
    ncivs = sum(1 for p, _b in f3 if CIV_PREFIX in p)
    nheli = sum(1 for p, _b in f3 if p.endswith(L2.HELI_TOP))
    if fresh and nheli != 1:
        raise ValueError('the heli squad: %d nodes changed (wanted 1; already f3 = 1?)' % nheli)
    log('  f3 = 1: %d civilian squads, %d heli squad' % (ncivs, nheli))
    # ---- civilians nearer than CFG['spread']
    smoves = spread_civs(B, Jn, nav, CFG['spread'], log) if CFG['spread'] else []
    # ---- AIMonitor START list
    if rrep['go']:
        km = Jn.resolve(KOW.MONITOR)[0]
        ci = AU.ctrl_of(Jn, km, 'AIMonitor')
        have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
        kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [g for g in rrep['go'] if g not in have]))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = L2.census(Jn)
    # ---- .HVK
    hrep = []
    if hvk_origin and fresh:
        hits = [(s, j) for s in hv.shapes if s.type == kl_hvk.VEHICLE for j in range(len(s.inst))]
        if len(hits) != 1:
            raise ValueError('expected exactly one vehicle placement in the .HVK, found %d' % len(hits))
        s, j = hits[0]
        inst = s.inst[j]
        p = struct.unpack_from('<3f', inst, 0)
        s.inst[j] = struct.pack('<3f9f', 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0) + inst[48:]
        hrep = [[round(v, 2) for v in p], [0, 0, 0]]
        log('  .HVK: the vehicle placement %s -> origin, identity' % (hrep[0],))
    # ---- .gms / .buf
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
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in tops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    if items:
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
    new[B.ext['.HVK']] = hv.serialize()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    return dict(census_before=[a0, s0], census_after=[fa, fs], f3_civs=ncivs, f3_heli=nheli, roof=rrep, hvk=hrep, members_changed=changed,
                slot_ids_moved=moved, entities_added=len(order), route=route.facts() if route else None, spread=smoves)


# ------------------------------------------------------------------ lastcall4 (2026-10-25): the packed club
# WHY: the owner (2026-10-25): "40 people bruh theres two floors needs way more than 40 people". The live lastcall3b-lite build holds 129 actors /
# 74 squads (40 civilians). Civilians share the actor pool with the enemies (re/actor_caps.md: no fixed cap found in kl2.exe; stock Last Call
# runs 148 / 90; 99 / 55 was the largest build proven before lastcall3b; the live lastcall3b-lite 129 / 74 has been played). To add 30 or 50
# civilians the PARKED campaign men (Dead Men's own guards, not part of the Fragile Alliance flow: the bots' TriggerActorsDead gates wake
# them) go first; the 6 OldWaves (30 men), the bots (7), the roof squads (12) and the helicopter stay.
SECOND = 'AI_Players!Enemies!SecondRun!'
FIRST = 'AI_Players!Enemies!FirstRun!'
PACK_REMOVE = [SECOND + n for n in ('Rave#02', 'Rave#01', 'Lounge#02', 'Lounge#01', 'YokoGuards', 'Dance#02')] + [
    FIRST + n for n in ('SurpriseStairs', 'Backroom!WaitingRoom', 'Bodyguards_First_Floor!Entrance', 'DanceFloor01!On_Dancefloor#02',
                        'DanceFloor02!Dancefloor02a#03', 'DanceFloor02!Dancefloor02a#01', 'DanceFloor02!Dancefloor02a#02',
                        'DanceFloor02!FatBounceronWalkway')]                      # 32 men / 14 squads; kept: Dance#01, Surprise2, HunterKillers (8 men)
LITE_REMOVE = [SECOND + n for n in ('Rave#02', 'Rave#01', 'Lounge#02', 'Lounge#01', 'YokoGuards')] + [
    FIRST + n for n in ('SurpriseStairs', 'Backroom!WaitingRoom', 'Bodyguards_First_Floor!Entrance')]      # 19 men / 8 squads
REFILL_FROM = [FIRST + 'Surprise2', FIRST + 'Hunters!HunterKillers', SECOND + 'Dance#01', FIRST + 'DanceFloor01!On_Dancefloor#02',
               FIRST + 'DanceFloor02!Dancefloor02a#02', FIRST + 'DanceFloor02!Dancefloor02a#01']


def trim_pass(src, dst, remove, log=print, post=None, room_items=False):
    """Take the top groups named in `remove` out of the build `src` -> `dst` (a folder-free zip): .prp (J.join without them), .gms / .buf
    (A.remove), .oct / .rmi / .rmc (O.remap_ids with the dead slot ids dropped), .prm (model roots repointed). References INTO the removed
    groups (the bots' TriggerActorsDead gates, their wake lists) are cut. A gate whose 'these men dead' list (field 0) was non-empty and
    is now empty would never fire (re/bots_squad.md: an empty list does nothing), so it names a living guard of REFILL_FROM instead (GUESS:
    the gates are the bots' stage clock; which man opens which stage was never tuned). -> report."""
    B = KB.Built(src)
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
    a0, s0 = L2.census(sc)
    byname = {sc.names[t]: t for t in sc.tops()}
    missing = [n for n in remove if not isinstance(n, int) and n not in byname]
    if missing:
        raise ValueError('not in the build (already trimmed?): %s' % missing[:3])
    removed = [n if isinstance(n, int) else byname[n] for n in remove]      # a name = a top group; an int = any node of the build (lastcall6: nested effect templates)
    nested = {t for t in removed if sc.parent[t] != 0}
    gone_nodes = set()
    for t in removed:
        gone_nodes.update(range(t, sc.end[t]))
    ra, rs = sum(1 for k in gone_nodes if sc.cls(k) == 'ZFFActor'), L2.census(sc)[1] - L2.census(sc, removed)[1]
    # the living guards that may stand in for an emptied gate list
    pool = []
    for n in REFILL_FROM:
        t = byname.get(n)
        if t is not None and t not in removed:
            pool += [sc.path[k] for k in range(t + 1, sc.end[t]) if sc.parent[k] == t and sc.names[k].startswith('Guard#')]
    Jn = J.join(sc, [(sc, t) for t in sc.tops() if t not in set(removed)], 'lastcall4', skip=nested)
    if post:
        post(Jn)                                           # lastcall6: field edits on the joined scene (paths of `sc` resolve in it)
    # ---- references into the removed groups: cut the dead entries
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
    log('  references into the %d removed groups: %d holders, %d entries cut' % (len(removed), len(dead), cut))
    # ---- gates left with an empty "dead" list: name a living guard
    before = {sc.path[k]: v for k, _i, v in kl_fa.controllers(sc, 'TriggerActorsDead')}
    refilled, used, stage_pick = [], 0, {}
    for k, i, v in list(kl_fa.controllers(Jn, 'TriggerActorsDead')):
        p0 = before.get(Jn.path[k])
        if p0 is None or not p0[0] or v[0]:
            continue
        key = Jn.path[k].split(BS)[-1]                       # one man per STAGE (035_..., 036_...) for all seven bots, not one per bot
        if key not in stage_pick and pool:
            stage_pick[key] = pool[min(used, len(pool) - 1)]
            used += 1
        pick = [stage_pick[key]] if key in stage_pick else []
        if not pick:
            raise ValueError('%s: its list of men is empty and no living guard is left to name' % Jn.path[k])
        kl_fa.edit(Jn, k, i, lambda us, pick=pick: AU.setv(Jn, us, 0, pick))
        refilled.append([Jn.path[k].split(BS)[-2] + BS + Jn.path[k].split(BS)[-1], pick[0].split('!')[-1]])
    log('  gates whose men list went empty and now name a living guard: %d %s' % (len(refilled), refilled))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = L2.census(Jn)
    log('  trimmed: %d actors / %d squads -> %d / %d' % (a0, s0, fa, fs))
    # ---- .gms / .buf
    slot0 = A.slots()
    gone_ents = set()
    for t in removed:
        gone_ents.update(B.ents[t - 1].walk())
    cuts = collections.Counter()
    for t in removed:
        r = A.remove(B.ents[t - 1])
        cuts['links'] += r['links']
        cuts['pairs'] += r['pairs']
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    elsewhere = sum(1 for r, room in enumerate(octx.rooms) for ti, t in enumerate(room) if t is not None and (r, ti) != (0, 3)
                    for it in t.items if it[0] in {slot0[e] + 2 for e in gone_ents})
    if elsewhere and room_items:
        log('  %d room-tree items outside the root group tree (shard objects in room 0) are dropped with their entities' % elsewhere)
    elif elsewhere:
        raise ValueError('%d room-tree items outside the root group tree name a removed entity' % elsewhere)
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    drop = {slot0[e] + 2 for e in gone_ents}
    octn, rmin, rmcn = O.remap_ids(octx, ids, drop), O.remap_ids(rmi, ids, drop), O.remap_ids(rmc, ids, drop)
    moved = sum(1 for a, b in ids.items() if a != b)
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
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    log('  scene: %d entities out (%d list entries, %d room pairs dropped), %d slot ids renumbered, %d model roots repointed' % (
        len(gone_ents), cuts['links'], cuts['pairs'], moved, repointed))
    return dict(removed=[sc.names[t] for t in removed], men_removed=ra, squads_removed=rs, census_before=[a0, s0], census_after=[fa, fs],
                refs_cut=cut, holders=len(dead), refilled=refilled, members_changed=changed, slot_ids_moved=moved)


def seal_verify(zp, log=print):
    """kl_fa_bank.seal + reverify on a scratch folder holding the zip; the zip is replaced by the sealed one."""
    import kl_fa_bank
    work = os.path.join(os.path.dirname(os.path.abspath(zp)), '_seal_' + os.path.basename(zp))
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    shutil.copyfile(zp, os.path.join(work, 'F01_Main.zip'))
    n = kl_fa_bank.seal(work, log=lambda *_: None)
    problems = kl_fa_bank.reverify(work, log=lambda *_: None)
    if problems:
        raise ValueError('reverify: %s' % problems[:5])
    shutil.copyfile(os.path.join(work, 'F01_Main.zip'), zp)
    shutil.rmtree(work)
    log('  sealed %d room list entries, reverify: no problems' % n)
    return n


def build_pack(src, dst, force, log, variant):
    h = md5(src)
    if h != CFG['base'] and not force:
        raise SystemExit('refusing: %s md5 %s is not the live DM05A %s (use --force)' % (src, h, CFG['base']))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    W = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc4_work_' + variant)
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(os.path.join(W, 'src'))
    for f in os.listdir(SIBLINGS):                      # the .WAV / .WHD beside the zip (kl_fa_civs.add measures them); read only
        p_ = os.path.join(SIBLINGS, f)
        if os.path.isfile(p_) and '.before-' not in f and not f.startswith(('audit.', 'civs.')) and not f.endswith(('.bak', '.old', '.zip')):
            shutil.copyfile(p_, os.path.join(W, 'src', f))
    rep = collections.OrderedDict(source=src, source_md5=h, variant=variant, cfg=dict(CFG))
    # 0. trim
    rep['trim'] = trim_pass(src, os.path.join(W, 'src', 'F01_Main.zip'), CFG['remove'], log)
    # 1. crowd
    B0 = KB.Built(os.path.join(W, 'src'), 'F01')
    before = {n for _k, _g, n in DN.dancers(B0)}
    c0 = CV.census(B0)
    CR.GROUND_SEP = CR.UPPER_SEP = CFG['sep']
    civs, _play = CR.plan(B0, CFG['add'], CFG['upper'], ALERT, SEED)
    log('crowd: %d of %d new places found; census before %d actors / %d squads / %d civilians' % (len(civs), CFG['add'], c0['actors'], c0['squads'], c0['civilians']))
    if len(civs) < CFG['add']:
        raise ValueError('only %d of %d civilian places' % (len(civs), CFG['add']))
    CV.add(os.path.join(W, 'src'), os.path.join(W, 'civ'), civs, 'F01', 'auto', ALERT, True, play=None, log=lambda *_: None)
    fails, _ = CV.check(os.path.join(W, 'civ'), 'F01', play=False)
    if fails:
        raise ValueError('kl_fa_civs.check: %s' % fails[:5])
    # 2. f3 = 1 on the new civilian squads, spacing
    mid = os.path.join(W, 'mid.zip')
    rep['civ_pass'] = roof_pass(os.path.join(W, 'civ', 'F01_Main.zip'), mid, False, log)
    # 3. a third dance group (own rout names, other delays) for the new civilians
    Bm = KB.Built(mid)
    new_names = {n for _k, _g, n in DN.dancers(Bm)} - before
    log('dance: %d new civilians' % len(new_names))
    drep = DN.build(mid, dst, per=CFG['per'], force=True, log=log, group=CFG['dgroup'], only=new_names, prefix=CFG['rout'],
                    offset=CFG['doff'], stagger=CFG['stagger'])
    if drep is None:
        raise ValueError('the dance pass wrote nothing')
    rep['dance'] = dict(new_civilians=len(new_names), routs=drep['routs'])
    seal_verify(dst, log)
    rep['out_md5'] = md5(dst)
    shutil.rmtree(W, ignore_errors=True)
    with open(os.path.splitext(dst)[0] + '.' + CFG['stem'] + '.json', 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    log('written %s md5 %s' % (dst, rep['out_md5']))
    return 0


# ------------------------------------------------------------------ the chain
def configure(variant):
    if variant not in VARIANTS:
        raise SystemExit('variant %r: one of %s' % (variant, sorted(VARIANTS)))
    CFG.clear()
    CFG.update(VARIANTS[variant])
    if CFG.get('mode') == 'pack':
        CFG['remove'] = PACK_REMOVE if variant == 'pack' else LITE_REMOVE
    CFG['variant'] = variant


def build(src, dst, alt=False, crowd=None, force=False, log=print, variant='v3'):
    configure(variant)
    if CFG.get('mode') == 'pack':
        if alt:
            raise SystemExit('the pack variants have a main build only')
        return build_pack(src, dst, force, log, variant)
    crowd = CFG['crowd'] if crowd is None else crowd
    h = md5(src)
    if h != MD5_LIVE and not force:
        raise SystemExit('refusing: %s md5 %s is not the live DM05A %s (use --force)' % (src, h, MD5_LIVE))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    W = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc3_work_' + variant + ('_alt' if alt else '_main'))
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(os.path.join(W, 'src'))
    for f in os.listdir(SIBLINGS):                      # the .WAV / .WHD beside the zip (kl_fa_civs.add measures them); read only
        p_ = os.path.join(SIBLINGS, f)
        if os.path.isfile(p_) and '.before-' not in f and not f.startswith(('audit.', 'civs.')) and not f.endswith(('.bak', '.old', '.zip')):
            shutil.copyfile(p_, os.path.join(W, 'src', f))
    shutil.copyfile(src, os.path.join(W, 'src', 'F01_Main.zip'))
    rep = collections.OrderedDict(source=src, source_md5=h, alt=alt, variant=variant, cfg=dict(CFG))
    # 1. crowd
    B0 = KB.Built(os.path.join(W, 'src'), 'F01')
    before = {n for _k, _g, n in DN.dancers(B0)}
    c0 = CV.census(B0)
    CR.GROUND_SEP = CR.UPPER_SEP = CFG['sep']
    civs, _play = CR.plan(B0, crowd, UPPER, ALERT, SEED)
    log('crowd: %d of %d places found; census before %d actors / %d squads / %d civilians' % (len(civs), crowd, c0['actors'], c0['squads'], c0['civilians']))
    if len(civs) < crowd * 0.8:
        raise ValueError('only %d of %d civilian places' % (len(civs), crowd))
    crep = CV.add(os.path.join(W, 'src'), os.path.join(W, 'civ'), civs, 'F01', 'auto', ALERT, True, play=None, log=lambda *_: None)
    fails, _ = CV.check(os.path.join(W, 'civ'), 'F01', play=False)
    if fails:
        raise ValueError('kl_fa_civs.check: %s' % fails[:5])
    rep['crowd'] = dict(added=len(civs), report_keys=sorted(crep)[:8])
    # 2. roof, f3, heli
    mid = os.path.join(W, 'mid.zip')
    rrep = roof_pass(os.path.join(W, 'civ', 'F01_Main.zip'), mid, not alt, log)
    rep['roof_pass'] = rrep
    # 3. dance for the new civilians
    Bm = KB.Built(mid)
    new_names = {n for _k, _g, n in DN.dancers(Bm)} - before
    log('dance: %d new civilians' % len(new_names))
    drep = DN.build(mid, dst, per=DN.PER_ROUT, force=True, log=log, group=DANCE2, only=new_names)
    if drep is None:
        raise ValueError('the dance pass wrote nothing')
    rep['dance'] = dict(new_civilians=len(new_names), routs=drep['routs'])
    rep['out_md5'] = md5(dst)
    shutil.rmtree(W, ignore_errors=True)
    with open(os.path.splitext(dst)[0] + '.' + CFG['stem'] + '.json', 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    log('written %s md5 %s' % (dst, rep['out_md5']))
    return 0


def check(zp, log=print, variant='v3'):
    configure(variant)
    fails = []
    B = KB.Built(zp)
    sc = B.sc
    a, s = L2.census(sc)
    log('census: %d actors / %d squads' % (a, s))
    # ---- distances: roof men to the pad centre / climb top, civilians to each other (xz)
    pad = L2.NEW_PAD
    roof = [(sc.names[sc.top[k]], tuple(B.at(k))) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and sc.names[sc.top[k]].startswith('OldWaves!Roof_')]
    if roof:
        xz = lambda p, q: math.hypot(p[0] - q[0], p[2] - q[2])
        dpad = min(min(xz(p, pad), math.dist(p, pad)) for _n, p in roof)
        dtop = min(min(xz(p, CLIMB_TOP), math.dist(p, CLIMB_TOP)) for _n, p in roof)
        log('roof men: %d; nearest to the pad centre %.0f, to the climb top %.0f (xz and 3D, the smaller)' % (len(roof), dpad, dtop))
        if CFG['far'] and min(dpad, dtop) < CFG['far']:
            fails.append('a roof man is %.0f from the pad or climb top (< %g)' % (min(dpad, dtop), CFG['far']))
    cv = [(sc.names[g], tuple(B.at(k))) for k, g, _n in DN.dancers(B)]
    mind = min((math.hypot(p[0] - q[0], p[2] - q[2]), n1, n2) for i, (n1, p) in enumerate(cv) for n2, q in cv[i + 1:])
    log('civilians: %d; closest pair (xz) %.0f: %s / %s' % (len(cv), mind[0], mind[1], mind[2]))
    if CFG['spread'] and mind[0] < CFG['spread'] - 0.5:
        fails.append('two civilians %.0f apart (< %g)' % (mind[0], CFG['spread']))
    if CFG.get('mode') == 'pack':
        up = sum(1 for _n, p in cv if p[1] >= 250.0)
        log('civilians per floor: %d ground, %d upper (%d total)' % (len(cv) - up, up, len(cv)))
        if len(cv) < CFG['want'] or up < CFG['want_upper'] or up < len(cv) / 3.0 or len(cv) - up < up * 0.5:
            fails.append('civilians: %d total / %d upper (wanted >= %d / >= %d)' % (len(cv), up, CFG['want'], CFG['want_upper']))
        if a > 147 or a < 100:
            fails.append('%d actors (cap 147)' % a)
        # no civilian within 150 of a START spawn or the escape pad (stairs / doors / route are the mesh's own narrow cells; plan_places keeps clear of walls)
        import zipfile
        with zipfile.ZipFile(zp) as z:
            snd = [n for n in z.namelist() if n.lower().endswith('.snd') and not n.lower().endswith('_ls.snd')]
            for n in snd:
                m = hashlib.md5(z.read(n)).hexdigest()
                log('  %s md5 %s' % (n, m))
                if not m.startswith('498cc81d'):
                    fails.append('the SND member %s changed (md5 %s, wanted 498cc81d...)' % (n, m))
    f3 = collections.Counter()
    for k, i, v in kl_fa.controllers(sc, 'ZSquadScript'):
        t = sc.names[sc.top[k]]
        if t.startswith(CIV_PREFIX):
            f3[('civ', v[3])] += 1
        elif t == L2.HELI_TOP:
            f3[('heli', v[3])] += 1
        elif t.startswith('OldWaves!Roof_'):
            f3[('roof', v[3])] += 1
    log('f3 by kind: %s' % dict(f3))
    if f3.get(('civ', 0)) or f3.get(('heli', 0)) or f3.get(('heli', 1), 0) != 1:
        fails.append('f3: %s' % dict(f3))
    if f3.get(('roof', 1), 0) != ROOF_SQUADS:
        fails.append('roof squads: %s' % dict(f3))
    mon = [v for k, i, v in kl_fa.controllers(sc, 'AIMonitor')]
    if not any('RoofClock' in r for v in mon for r in v[2]):
        fails.append('AIMonitor START list does not name the roof timers')
    f, nr, nc = DN.verify(zp, DN.DEFAULT_CLIPS)
    fails += f
    log('dance: %d routs, %d civilians dance' % (nr, nc))
    hv = kl_hvk.Hvk(B['.HVK'])
    for s_ in hv.shapes:
        if s_.type == kl_hvk.VEHICLE:
            for inst in s_.inst:
                log('  .HVK vehicle placement %s' % (tuple(round(v, 2) for v in struct.unpack_from('<3f', inst, 0)),))
    for x in fails:
        log('FAIL ' + x)
    log('check: %s' % ('PASS' if not fails else 'FAIL'))
    return 1 if fails else 0


# ------------------------------------------------------------------ install / undo
def _ps1():
    st = CFG['stem']
    s = DN.PS1.replace('dance.json', st + '.json').replace(DN.TAG, CFG['tag']).replace('dance.ps1', st + '.ps1')
    s = s.replace('# %s.ps1 - Last Call (DM05A): the club civilians dance until the panic (tools/kl_club_dance_1024.py, 2026-10-24).' % st,
                  '# %s.ps1 - Last Call (DM05A): %s (tools/kl_club_lastcall3.py, 2026-10-25).' % (st, 'a PACKED club on both floors, parked campaign men trimmed' if CFG.get('mode') == 'pack' else 'heli fix, roof guards, a full club'))
    return s


def _bat(arg, name):
    n = chr(13) + chr(10)
    return ('@echo off{n}cd /d "%~dp0"{n}powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{{st}}.ps1" {{arg}}{n}pause{n}'.format(n=n)).format(arg=arg, st=CFG['stem'])


NOPROC = [False]       # --no-proc-check: rehearse with a COPY of the .ps1 whose kl2.exe-is-running guard line is removed (the game is being played)


def _run(d, game, undo=False):
    ps = os.path.join(d, CFG['stem'] + '.ps1')
    if NOPROC[0]:
        txt = open(ps, encoding='utf-8', newline='').read()
        lines = [l for l in txt.split(chr(10)) if 'Get-Process kl2' not in l]
        if len(lines) != len(txt.split(chr(10))) - 1:
            raise ValueError('the kl2.exe guard line was not found exactly once in %s' % ps)
        ps = os.path.join(d, '_rehearse_noproc.ps1')
        open(ps, 'w', encoding='utf-8', newline='').write(chr(10).join(lines))
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ps, '-Game', game]
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    if NOPROC[0]:
        os.remove(ps)
    return r.stdout + r.stderr


def stage(live, out, scratch=None, log=print, variants=('v3',)):
    """Each variant gets <out>/<variant>/{main,alt}; with a single variant 'v3' the folders are <out>/{main,alt} as in lastcall3_1025a."""
    allv = {}
    for variant in variants:
        configure(variant)
        tag, stem = CFG['tag'], CFG['stem']
        base = out if variant == 'v3' else os.path.join(out, variant)
        vd = {}
        for v, alt in ((('main', False),) if CFG.get('mode') == 'pack' else (('main', False), ('alt', True))):
            d = os.path.join(base, v)
            os.makedirs(d, exist_ok=True)
            z = os.path.join(d, 'F01_Main.zip')
            if not os.path.isfile(z):
                build(live, z, alt=alt, log=log, variant=variant)
                configure(variant)
            if check(z, log, variant):
                raise SystemExit('check FAIL on %s %s' % (variant, v))
            man = dict(m='DM05A', f='F01_Main.zip', variant='%s/%s' % (variant, v), old=md5(live), new=md5(z), tag=tag)
            with open(os.path.join(d, stem + '.json'), 'w') as fh:
                json.dump(man, fh, indent=1)
            with open(os.path.join(d, stem + '.ps1'), 'w', newline=chr(13) + chr(10)) as fh:
                fh.write(_ps1())
            for nm, arg in (('INSTALL %s %s %s.bat' % (stem, variant, v), ''), ('UNDO %s %s %s.bat' % (stem, variant, v), '-Undo')):
                with open(os.path.join(d, nm), 'w', newline='') as fh:
                    fh.write(_bat(arg, nm))
            vd[v] = (d, man)
            log('%s %s: %s -> %s' % (variant, v, man['old'], man['new']))
        allv[variant] = vd
    if scratch:
        scratch = os.path.abspath(scratch)
        g = os.path.join(scratch, 'rehearse_game')
        live_t = os.path.join(g, 'KLExpansion', 'Maps', 'DM05A', 'F01_Main.zip')
        every = [(variant, v, d, man) for variant, vd in allv.items() for v, (d, man) in vd.items()]
        for variant, v, d, man in every:
            configure(variant)
            tag = CFG['tag']
            shutil.rmtree(g, ignore_errors=True)
            os.makedirs(os.path.dirname(live_t))
            open(os.path.join(g, 'kl2.exe'), 'wb').close()
            shutil.copy2(live, live_t)
            t = _run(d, g); log(t); assert 'installed' in t and md5(live_t) == man['new'], t
            assert md5(live_t + tag) == man['old']
            t = _run(d, g, True); log(t)
            assert md5(live_t) == man['old'] and not os.path.exists(live_t + tag), 'undo not byte identical'
            t = _run(d, g); assert md5(live_t) == man['new']
            for variant2, v2, d2, man2 in every:                 # every OTHER build is refused while this one is installed
                if (variant2, v2) != (variant, v):
                    configure(variant2)
                    t = _run(d2, g); assert 'SKIP' in t and md5(live_t) == man['new'], t
            configure(variant)
            t = _run(d, g, True); assert md5(live_t) == man['old']
            with open(live_t, 'ab') as fh:
                fh.write(b'x')
            t = _run(d, g); assert 'SKIP, live md5' in t and not os.path.exists(live_t + tag), t
            log('%s/%s rehearsal ok (install, byte-identical undo, other builds refused, wrong md5 refused)' % (variant, v))
        shutil.rmtree(g, ignore_errors=True)
    return 0


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('build', 'check', 'stage'):
        print(__doc__)
        return 2
    variant = opt('--variant', 'v3')
    NOPROC[0] = '--no-proc-check' in a
    if a[0] == 'check':
        return check(a[1], variant=variant)
    if a[0] == 'build':
        r = build(a[1], a[2], '--alt' in a, int(opt('--crowd')) if opt('--crowd') else None, '--force' in a, variant=variant)
        return r or check(a[2], variant=variant)
    return stage(a[1], a[2], opt('--rehearse'), variants=tuple(variant.split(',')))


if __name__ == '__main__':
    sys.exit(main())
