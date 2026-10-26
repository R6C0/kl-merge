"""kl_arcade_sign_1026.py - bring DM01 / DM02 / DM03 / DM06 up to the stock Arcade standard (2026-10-26, OFFLINE: reads zips, writes only under <root>/<MAP>/stage).

Source of truth for the standard: C:/kl_build_1024/arcade_ref_1026 (audit.md).  Every node is a CLONE of a stock Fragile Alliance node (kl_fa_bots.Maker), never invented.

JOB 1  SIGNPOSTING (all four maps).  The DM maps carry the FA monitors (AIMonitor, OnlineEscVehicleMonitor, FAMissionBriefingTrigger) but none of the stock
  guidance.  Added, as flat top-level nodes 'PointOfIntrest!*' with F06's names (so every cloned reference resolves unchanged):
    Timer_POI_TheLootArea (11 s) -> CheckMPTutorialOption#01 (loot text 4 s later, first time only) + POI_TheLootArea (the loot marker, PointOfInterest + ActivateGameplayTrackerDisplay)
    Trigger_POI_TheEscapeArea (TriggerBox, ECPS_BOTH, a box over the loot-to-exit corridor) -> CheckMPTutorialOption#02 (escape text) + GeomDeactivator_TheLootArea (hides the loot marker) + POI_TheEscapeArea
    OnScreenMSG_LastEscape(+Timer_OSM_LastEscape): the 'last van / last chopper' text, named in OnlineEscVehicleMonitor field 8 (as F01 / F06 do it)
  The monitor's round-start list (AIMonitor field 2) gets Timer_POI_TheLootArea, as every stock map's does.
  Forms: all four use F06's wiring (the simplest of the stock forms; F01/F02/F03 are variants of the same rule: loot marker by timer, escape marker by trigger).
  Van maps (DM01 DM02 DM03): POI_TheEscapeArea is F01's (key Objectives/EscapeCar); the last-escape text is F01's LastVan.  DM06 (chopper): F06's EscapeChopper / LastChopper.
  Text: no new strings - the seven Objectives keys already exist in every LOC of the four zips (checked: sign_work/loc_check.py), so the LOC members are not touched.

TOGGLE: map content; install.py / install.py --undo is the on/off switch (tag .before-1026arcade); md5 pinned; nothing is written while kl2.exe runs.
usage (from tools/):  python kl_arcade_sign_1026.py stage <root> [DM01 DM02 DM03 DM06] [--rehearse <scratch>]
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_fa_bank as BK
import kl_octree as O
import kl_prpjoin as J
import kl_loot_1025 as LT
import kl_bots_kick_1025 as KK
import kl_lanes_stage_1025 as LS
import kl_fa_fed as FED
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
TAG = '.before-1026arcade'
GAME = KK.GAME
PFX = 'PointOfIntrest!'                      # the stock spelling (sic)
FAR = (10000.0, 0.0, 10000.0)                # where the non-spatial nodes stand (the AIMonitor's own place)

# name -> slot, live zip md5 (pinned), van|chopper, START centre, loot centre, exit trigger centre (MEASURED by the 2026-10-26 audit: arcade_ref_1026/out/<map>.json)
SPEC = collections.OrderedDict([
    ('DM01', dict(slot='F01', pin='5770263fc6e9536b7c1634823b5a27a8', kind='van', start=(1632, 76, 30643), loot=(5569, 18, 21843), exit=(1196, 160, 20978))),
    ('DM02', dict(slot='F02', pin='64275acd14732fde4331b365f99b5b5a', kind='van', start=(1490, 1091, -3342), loot=(-134, 530, 1730), exit=(-38, 182, -8952))),
    ('DM03', dict(slot='F03', pin='1aa8a1233b019be09ae9f23b51001c03', kind='van', start=(-1808, 793, -11838), loot=(318, 500, -6838), exit=(408, 396, 460))),
    ('DM06', dict(slot='F04', pin='7f9b76826ce7b6893f073fefa9ed1fa5', kind='chopper', start=(5514, 379, 4549), loot=(554, 347, 1545), exit=(-1593, 206, -8050)))])

# loot stacks with no mesh path from START (arcade_ref_1026 nopath check): group node -> new place.  GUESS: (-1807, 77, -3509) is on the diner counter line the lanes build
# already uses (x -1807, z -3379 / -3639), 130 cm from each neighbour and 20+ cm of spare floor at reach 165 (sign_work/d2spot.py); the stack keeps its model and amount.
MOVES = {'DM02': {23692: (-1807.0, 77.0, -3509.0)}}


def md5(p):
    return LT.md5(p)


# ------------------------------------------------------------------ signposting
def sign_nodes(M, sp):
    """-> (tops, info). All clones; positions from the audit's loot centre / exit."""
    tops = []

    def cl(level, path, name=None, at=FAR):
        n = M.clone(level, R + path, (PFX + name) if name else None)
        M.place(n, at)
        tops.append(n)
        return n
    for nm in ('OnScreenMSG_EscapeArea_Text', 'OnScreenMSG_EscapeArea_Timer', 'OnScreenMSG_LootArea_Text', 'OnScreenMSG_LootArea_Timer', 'Timer_POI_TheLootArea',
               'GeomDeactivator_TheLootArea', 'CheckMPTutorialOption#02', 'CheckMPTutorialOption#01'):
        cl('F06', PFX + nm, nm)
    L, E = sp['loot'], sp['exit']
    # POI_TheLootArea: F06's, 100 cm above the loot centre (stock: F01 +100, F06 +120 over the audit's loot centre)
    cl('F06', PFX + 'POI_TheLootArea', 'POI_TheLootArea', (float(L[0]), float(L[1]) + 100.0, float(L[2])))
    if sp['kind'] == 'van':
        cl('F01', 'Gameplay!PointOfIntrest!POI_TheEscapeArea', 'POI_TheEscapeArea', (float(E[0]), float(E[1]) + 20.0, float(E[2])))   # key Objectives/EscapeCar
    else:
        cl('F06', PFX + 'POI_TheEscapeArea', 'POI_TheEscapeArea', (float(E[0]), float(E[1]) + 20.0, float(E[2])))                      # key Objectives/EscapeChopper
    # Trigger_POI_TheEscapeArea: a box over the loot-to-exit corridor. GUESS: the stock boxes are 9079 x 585 x 7907 (F06), 125 x 264 x 1771 (F01) - hand-placed per map; this one is
    # the bounding box of loot centre and exit, 1000 cm of margin in x / z, y half = max(half the height gap + 250, 300); asserted to hold the loot centre and NOT the START.
    cx, cy, cz = (L[0] + E[0]) / 2.0, (L[1] + E[1]) / 2.0, (L[2] + E[2]) / 2.0
    hx, hy, hz = abs(L[0] - E[0]) / 2.0 + 1000.0, max(abs(L[1] - E[1]) / 2.0 + 250.0, 300.0), abs(L[2] - E[2]) / 2.0 + 1000.0
    inside = lambda p: abs(p[0] - cx) <= hx and abs(p[1] - cy) <= hy and abs(p[2] - cz) <= hz
    if not inside(L) or inside(sp['start']):
        raise ValueError('escape trigger box: loot inside %s, start inside %s' % (inside(L), inside(sp['start'])))
    tr = cl('F06', PFX + 'Trigger_POI_TheEscapeArea', 'Trigger_POI_TheEscapeArea', (cx, cy, cz))
    M.set(tr, None, {'ZBoxPrimitive[0]': hx, 'ZBoxPrimitive[1]': hy, 'ZBoxPrimitive[2]': hz})
    # the last-escape text and its 4 s timer
    if sp['kind'] == 'van':
        msg = cl('F01', 'Gameplay!EscapeVan_Anim!OnScreenMSG_LastEscapeVan', 'OnScreenMSG_LastEscape')
        tm = cl('F01', 'Gameplay!EscapeVan_Anim!Timer_OSM_LastEscape', 'Timer_OSM_LastEscape')
    else:
        msg = cl('F06', 'Escape!OnScreenMSG_LastEscapeChopper', 'OnScreenMSG_LastEscape')
        tm = cl('F06', 'Escape!Timer_OSM_LastEscape', 'Timer_OSM_LastEscape')
    M.set(tm, 'TriggerDelay2', {4: [R + PFX + 'OnScreenMSG_LastEscape']})
    info = dict(trigger=dict(centre=(cx, cy, cz), half=(hx, hy, hz)), loot_poi=(L[0], L[1] + 100, L[2]), escape_poi=(E[0], E[1] + 20, E[2]), kind=sp['kind'])
    return tops, info


# ------------------------------------------------------------------ gating (DM01) and box-woken cover squads (DM03, DM06)
STOCK_SQ = R + 'AI_Players!Enemys!031_policemen_insideoffices'          # F06's box-woken RunToCover squad (the stock form)
BACK = 2500.0                  # GUESS: wake box this far (along the walk) before the squad; stock boxes sit 1500-4000 from what they wake
GATE_HALF = (500.0, 300.0, 500.0)
GATE_MERGE = 800.0

# DM01: squads that are in the world at load and are woken by a box instead.  (name, place to walk to)
DM01_GATED = [('KL_Hold!Shop', (3145.0, -10.0, 22465.0)), ('KL_WH!Floor', (2285.0, 60.0, 18355.0)),
              ('KL_WH!Top', (2285.0, 60.0, 18355.0))]       # Top stands on a roof with no mesh path: it is woken with the Floor squad
DM01_TIMED = ['OldWaves!Wave_1', 'OldWaves!Wave_2']          # started by their own +60 s / +130 s timers: f3 = 0 only (stock timer waves are built so)
DM01_GO = 'KL_Squads!Clock' + BS + 'Go'

# new squads: the audit's 'no cover near the loot' places; the men are the map's OWN soldier groups (model / sound indices are per map)
NEW_SQUADS = {
    'DM03': dict(templ_squad='AI_Enemies!ParkingLotSWAT_01', loot=(318.0, 500.0, -6838.0), sites=[(1450.0, 700.0, -9934.0), (582.0, 800.0, -7367.0), (4210.0, 700.0, -9352.0)]),
    'DM06': dict(templ_squad='KL_Cars!Cop_1', loot=(554.0, 347.0, 1545.0), sites=[(1414.0, 199.0, 3800.0), (3401.0, 246.0, 3016.0)]),
}


def start_of(B, nav):
    sc = B.sc
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint' and any(x == kl_fa.START for x in kl_fa.node_values(sc, k)):
            p = B.at(k)
            for dy in (260., 600., 1500.):
                h = nav.at(p[0], p[1], p[2], dy=dy)
                if h:
                    return p, h
    raise ValueError('no START on the mesh')


def floor_at(nav, p, part):
    h = nav.at(p[0], p[1], p[2], dy=250.0, part=part) or nav.at(p[0], p[1], p[2], dy=700.0, part=part)
    if h:
        return (float(p[0]), float(h[1]), float(p[2])), h[0]
    i = nav.nearest(p, part)
    return tuple(float(v) for v in nav.mid[i]), i


def gate_point(nav, st, h0, site, back=BACK):
    """Point `back` cm before `site` on the walk from START (nav path); -> ((x, floor, z), path length)."""
    q = floor_at(nav, site, nav.part[h0[0]])
    r = nav.path((st[0], h0[1], st[2], h0[0]), (q[0][0], q[0][1], q[0][2], q[1]))
    if not r:
        raise ValueError('no walk from START to %s' % (site,))
    pts, L = r
    acc = 0.0
    for i in range(len(pts) - 1, 0, -1):
        d = math.dist(pts[i], pts[i - 1])
        if acc + d >= back:
            f = (back - acc) / d
            return tuple(pts[i][k] + (pts[i - 1][k] - pts[i][k]) * f for k in range(3)), L
        acc += d
    raise ValueError('walk to %s is shorter than %d' % (site, back))


class Gates:
    """Wake boxes: one per place (sites within GATE_MERGE share one); each lists what it starts."""

    def __init__(self, M, tops, st):
        self.M, self.tops, self.st, self.boxes = M, tops, st, []

    def add(self, pt, target, tag):
        for b in self.boxes:
            if math.hypot(b['pt'][0] - pt[0], b['pt'][2] - pt[2]) < GATE_MERGE:
                b['targets'].append(target)
                b['tags'].append(tag)
                return b
        if abs(self.st[0] - pt[0]) <= GATE_HALF[0] + 600.0 and abs(self.st[2] - pt[2]) <= GATE_HALF[2] + 600.0:
            raise ValueError('wake box %s would hold START' % (pt,))
        n = len(self.boxes) + 1
        name = 'KL_Gates!tbWake_%02d' % n
        bx = self.M.clone('F06', STOCK_SQ + BS + 'tbPoliceInsideOffices', name)
        self.M.place(bx, (pt[0], pt[1] + 200.0, pt[2]), KB.rot9(0.0, 1.0))
        self.M.set(bx, 'TriggerBox', {17: []})
        self.M.set(bx, None, {'ZBoxPrimitive[0]': GATE_HALF[0], 'ZBoxPrimitive[1]': GATE_HALF[1], 'ZBoxPrimitive[2]': GATE_HALF[2]})
        self.tops.append(bx)
        b = dict(name=name, pt=tuple(round(v, 1) for v in pt), targets=[target], tags=[tag])
        self.boxes.append(b)
        return b


def cover_squads(M, B, nav, st, h0, cfg, gates, tops, log):
    """Box-woken RunToCover squads (F06's form): ZSquadScript f3 = 0, a RunToCover group with one RunToPosInfo per man, the men, a TriggerBox on the way."""
    sc = B.sc
    part = nav.part[h0[0]]
    top0 = sc.resolve(R + cfg['templ_squad'])[0]
    acts = [k for k in range(top0, sc.end[top0]) if sc.cls(k) == 'ZFFActor']
    if len(acts) < 2:
        raise ValueError('template squad %s has %d actors' % (cfg['templ_squad'], len(acts)))
    dm = nav.dist_map(h0[0], (st[0], h0[1], st[2]))[0]
    out = []
    for n, site in enumerate(cfg['sites'], 1):
        name = 'KL_Cover!Squad_%02d' % n
        me = R + name
        dx, dz = cfg['loot'][0] - site[0], cfg['loot'][2] - site[2]
        L = math.hypot(dx, dz) or 1.0
        ux, uz = dx / L, dz / L
        top = FED.clone_built(M, B, top0, name)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {0: 'eUnleashed', 1: 'eAllTypes', 3: 0, **{j: [] for j in range(4, 19)}})
        rc = top.add(M.clone('F06', STOCK_SQ + BS + 'RunToCover', 'RunToCover'))
        M.place(rc, (0.0, 0.0, 0.0))
        info = []
        for j in range(2):
            side = (-1 if j == 0 else 1) * 150.0
            sp_, spi = floor_at(nav, (site[0] - uz * side, site[1], site[2] + ux * side), part)
            dp, dpi = floor_at(nav, (site[0] + ux * 700.0 - uz * side * 1.6, site[1], site[2] + uz * 700.0 + ux * side * 1.6), part)
            if spi not in dm or dpi not in dm:
                raise ValueError('%s man %d: spawn or cover place is not reachable from START' % (name, j + 1))
            g = top.add(FED.clone_built(M, B, sc.parent[acts[j]], 'cop_#%02d' % (j + 1)))
            M.place(g, sp_, KB.rot9(ux, uz))
            g.add(FED.clone_built(M, B, acts[j], 'Ground'))
            pi = rc.add(M.clone('F06', STOCK_SQ + BS + 'RunToCover' + BS + 'RunToPosInfo#01', 'RunToPosInfo#%02d' % (j + 1)))
            M.place(pi, dp)
            M.set(pi, 'RunToCoverPosInfoRout', {5: me + BS + 'cop_#%02d' % (j + 1)})
            info.append(dict(spawn=[round(v, 1) for v in sp_], cover=[round(v, 1) for v in dp]))
        tops.append(top)
        gp, plen = gate_point(nav, st, h0, site)
        b = gates.add(gp, me + BS + 'RunToCover', name)
        out.append(dict(name=name, site=site, men=info, gate=b['name'], walk=round(plen)))
        log('    %s at %s: walk %d, wake box %s at %s' % (name, site, plen, b['name'], b['pt']))
    return out


def gating_nodes(M, B, name, tops, log):
    """-> (gates, plan).  DM01: existing squads are re-woken by boxes; DM03 / DM06: new squads."""
    nav = KB.Nav(B.scene.nav, links=True)
    st, h0 = start_of(B, nav)
    gates = Gates(M, tops, st)
    plan = dict(start=[round(v) for v in st])
    if name == 'DM01':
        pts = {}
        for q, walk in DM01_GATED:
            if walk not in pts:
                pts[walk] = gate_point(nav, st, h0, walk)
            b = gates.add(pts[walk][0], R + q + BS + '10_Defend', q)
            log('    gate %s -> %s at %s (walk %d)' % (q, b['name'], b['pt'], pts[walk][1]))
        plan['gated'] = [q for q, _ in DM01_GATED]
        plan['timed'] = list(DM01_TIMED)
    elif name in NEW_SQUADS:
        plan['squads'] = cover_squads(M, B, nav, st, h0, NEW_SQUADS[name], gates, tops, log)
    plan['boxes'] = [dict(name=b['name'], at=b['pt'], half=GATE_HALF, wakes=b['tags']) for b in gates.boxes]
    return gates, plan


def find_one(sc, cname):
    ks = [k for k, i, v in kl_fa.controllers(sc, cname)]
    if len(ks) != 1:
        raise ValueError('%d %s controllers' % (len(ks), cname))
    return sc.path[ks[0]]


# ------------------------------------------------------------------ the build
def build(src, slot, name, dst, log=print):
    sp = SPEC[name]
    h_in = md5(src)
    B = KB.Built(src, slot)
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
    moves = MOVES.get(name, {})
    mv_before = {g: [round(float(v), 1) for v in B.at(g)] for g in moves}
    if moves:
        stuck = LT.listed_in_oct(B, [j for g in moves for j in range(g, sc.end[g])])
        if stuck:
            raise ValueError('loot nodes %s are listed in an .oct room tree' % stuck)
        for g, pos in moves.items():
            LS.move_group(B, g, pos)
    for k in range(1, len(sc.nodes)):
        if sc.parent[k] == 0 and sc.names[k].startswith(PFX):
            raise ValueError('%s already has %s' % (name, sc.names[k]))
    mon, esc = find_one(sc, 'AIMonitor'), find_one(sc, 'OnlineEscVehicleMonitor')
    M = KB.Maker()
    tops, info = sign_nodes(M, sp)
    gates, gplan = gating_nodes(M, B, name, tops, log)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'arcade')

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
    add_to(mon, 'AIMonitor', 2, [R + PFX + 'Timer_POI_TheLootArea'])
    add_to(esc, 'OnlineEscVehicleMonitor', 8, [R + PFX + 'OnScreenMSG_LastEscape', R + PFX + 'Timer_OSM_LastEscape'])
    for b in gates.boxes:
        add_to(R + b['name'], 'TriggerBox', 17, b['targets'])
    if name == 'DM01':
        def set_f3(path):
            k = Jn.resolve(R + path)
            if len(k) != 1:
                raise ValueError('%d nodes at %s' % (len(k), path))
            kl_fa.edit(Jn, k[0], AU.ctrl_of(Jn, k[0], 'ZSquadScript'), lambda us: AU.setv(Jn, us, 3, 0))
        for q_, _w in DM01_GATED:
            set_f3(q_)
        for q_ in DM01_TIMED:
            set_f3(q_)
        kg = Jn.resolve(R + DM01_GO)
        if len(kg) != 1:
            raise ValueError('%d nodes at %s' % (len(kg), DM01_GO))
        kl_fa.edit(Jn, kg[0], AU.ctrl_of(Jn, kg[0], 'TriggerDelay2'), lambda us: us.__setitem__(4, kl_fa._refs(Jn, [])))
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

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
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
    repointed, new_prm = 0, None
    if moved:
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
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    repl = {B.ext[e]: new[B.ext[e]] for e in changed}
    n_prm = None
    if new_prm is not None:
        import kl_prmgraph
        n_prm = (len(kl_prmgraph.read(B['.prm']).chunks), len(kl_prmgraph.read(new_prm).chunks))
        if n_prm[0] != n_prm[1]:
            raise ValueError('.prm chunk count changed %s' % (n_prm,))
    work = tempfile.mkdtemp(prefix='asign_')
    try:
        wz = os.path.join(work, os.path.basename(dst))
        KK.patch_zip(src, wz, repl)
        counts = []
        for zsrc in (src, wz):
            tmpd = tempfile.mkdtemp(prefix='asign_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, os.path.basename(dst)))
                counts.append(BK.seal(tmpd, log=lambda *_: None))
            finally:
                KK.rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        problems = BK.reverify(work, log=lambda *_: None)
        wi = tempfile.mkdtemp(prefix='asign_in_')
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
    A2 = KB.Built(dst, slot)
    bad = []
    s2 = A2.sc
    for n in A2.files:
        if n not in repl and A2.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    for nm in ('Timer_POI_TheLootArea', 'Trigger_POI_TheEscapeArea', 'POI_TheLootArea', 'POI_TheEscapeArea', 'OnScreenMSG_LastEscape', 'Timer_OSM_LastEscape'):
        if len(s2.resolve(R + PFX + nm)) != 1:
            bad.append('missing %s' % nm)
    mons = [v for k, i, v in kl_fa.controllers(s2, 'AIMonitor')]
    if len(mons) != 1 or (R + PFX + 'Timer_POI_TheLootArea').lower() not in [str(x).lower() for x in mons[0][2]]:
        bad.append('AIMonitor does not list the POI timer')
    ev = [v for k, i, v in kl_fa.controllers(s2, 'OnlineEscVehicleMonitor')]
    if len(ev) != 1 or len(ev[0][8]) != 2:
        bad.append('OnlineEscVehicleMonitor field 8: %s' % (ev and ev[0][8]))
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(md5_in=h_in, md5_out=md5(dst), members_changed=changed, entities_before=len(B.ents), entities=len(ents), added=len(order),
                                  loot_moved={str(g): [mv_before[g], list(moves[g])] for g in moves}, slot_ids_moved=moved, prm_roots_repointed=repointed, prm_chunks=n_prm, signpost=info, gating=gplan, room_sets=[str(pre), str(post)])
    log('  %s: members %s; %d entities added (%d -> %d), %d slot ids renumbered, %d .prm roots re-pointed' % (name, ' '.join(changed), len(order), len(B.ents), len(ents), moved, repointed))
    return rep


# ------------------------------------------------------------------ stage
def zip_name(name):
    return SPEC[name]['slot'] + '_Main.zip'


def stage_map(root, name, scratch=None, log=print):
    sp = SPEC[name]
    zn = zip_name(name)
    d = os.path.join(root, name)
    src = os.path.join(d, 'in', zn)
    h = md5(src)
    if h != sp['pin']:
        raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, sp['pin']))
    out = os.path.join(d, 'stage')
    KK.rmtree(out)
    os.makedirs(out)
    log('== %s (%s) ==' % (name, zn))
    rep = build(src, sp['slot'], name, os.path.join(out, zn), log)
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write((KK.INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=h, new=rep['md5_out'])).replace('door-kick zip (tools/kl_bots_kick_1025.py', 'Arcade-standard zip (tools/kl_arcade_sign_1026.py'))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    if scratch:
        KK.MAPS[name] = (sp['slot'], zn, sp['pin'])
        KK.TAG = TAG
        KK.rehearse(out, name, src, rep['md5_out'], h, scratch, log)
    return rep


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__)
        return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    names = [x for x in a[2:] if x in SPEC] or list(SPEC)
    for n in names:
        stage_map(a[1], n, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
