#!/usr/bin/env python3
"""
Balance pass for the OLD Dead Men Fragile Alliance maps DM01 (slot F01) and DM02 (slot F02), on a copy of the INSTALLED
folder (audit_1018 requests E5 + E7; re/owner_feedback_1017.md). OFFLINE: nothing here installs or starts anything.
EVERY CHANGE IS BEHIND ITS OWN FLAG, ALL OFF: without a flag the output folder is the source folder, file for file.

    python kl_old_waves.py build <installed folder> <out folder> [flags]
    python kl_old_waves.py check <folder>                 the facts of a built folder (men, squads, wave chain, accuracy)
    python kl_old_waves.py diff  <installed folder> <out folder>     member by member (CRC and size)

    --cap-acc N      E5. Every Enemy-team soldier whose accuracy AS USED (kl_map_ai.effective: preset of the skill name,
                     times 1.1 for No_Mercenary, clamped 100) is above N is set to N (default 75, GUESS: the audit asks
                     for 'about 75 instead of about 100'). A soldier that had a skill-name preset becomes eCustom with the
                     preset's numbers kept (a name would write over the new accuracy: kl2 0x46e410). Aim is not touched.
    --waves          E5. Three timed waves of parked squads (clones of the map's own armed enemy squad, the Defend rout
                     of the stock bot squad as kl_fa_bank.extras_make does): 9 + 9 + 9 = 27 men (GUESS: audit 'about
                     25-30'), at 60 / 130 / 200 s after the round starts (GUESS), started by AIMonitor field 2 -> Pace_1
                     -> Go_1 (0.1 s: names the rout, the next Pace) -> Pace_2 ... Entries and posts are cells of the crew's
                     ground (kl_fa_fedpoints.candidates) out of sight of the START row and of the crew place the wave is
                     meant for (quantiles 0.30 / 0.55 / 0.80 of the crew's places by distance from the START, GUESS).
    --trim-wait SEC  E7 DM02. The squads' TriggerLootDepleted '040_Timer_done_looting' with a wait of 45 s is cut to
                     SEC (default 20, GUESS): the bot squads waited 45 s twice (020_ and 040_).
    --rings          E7 DM02. The two jewel rings the bots cannot reach (OfficeJewel_201a JewelsRings_A_01 / _C_01, 250K)
                     move to the nearest cell of the BOTS' mesh part within RING_MAX of their place, keeping their height
                     above the floor (.prp ZGEOM[2] and the .gms record). They stay children of their own room's group.
    --ally-box       E7 DM01. The bots' AllyEscapeBox is grown (half extents, same middle) until the van's boarding place
                     and its stop lie inside with BOX_MARGIN to spare, at most BOX_MAX per axis. A box that holds them
                     already is left alone.
"""
import collections, json, math, os, shutil, struct, sys, zlib, zipfile

import kl_fa, kl_gms, kl_scene
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_map_ai as MAI
import kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp, units

R = 'ROOT\\'
CLOCK = 'OldWaves!Clock'
WAVE_G = 'OldWaves!'
MONITOR = R + 'Gameplay!AIMonitor'
TIMER_FORM = R + 'Gameplay!merc_bot_squad!Timer_start_bots'      # a TriggerDelay2 of the build itself: the clone form of the chain
FORM = '\\020_DefendBehaviour_rout_merc_fight_left'                 # the stock Defend rout (F07, Squad#02), as kl_fa_bank
GO_DELAY = 0.1                                                      # as kl_fa_bank.GO_DELAY
START_LIST = MAI.START_LIST                                         # AIMonitor field 2: the round-start list
# GUESS values (nothing of this has run in the game)
WAVES = ((60.0, 9, 0.30), (70.0, 9, 0.55), (70.0, 9, 0.80))         # (seconds after the previous link, men, quantile of the crew's places)
CAP_ACC = 75.0
TRIM_WAIT = 20.0
TRIM_FROM = 45.0            # only the 45 s waits (squads 04, 05, 07); the 60 s and 15 s ones stay
ENEMY_TEMPLATE = {'dm01': 'AI_Enemies!FrontMall_01', 'dm02': 'AIEnemies!PoliceSwats'}
SPAWN_FAR = 2500.0          # from the START row
POST_NEAR, POST_FAR = 1800.0, 3600.0   # from the crew place the wave is meant for
MEN_GAP = 350.0
RING_MAX = 900.0            # a ring moves at most this far (GUESS; the nearest cell of the bots' part with 40 to a wall is ~600 away)
RING_NAMES = ('PC0402_M02_FA_JewelsRings_A_01', 'PC0402_M02_FA_JewelsRings_C_01')
RING_ROOM = 'M02_FA_A_Ins_OfficeJewel_201a'
BOX_MARGIN, BOX_MAX = 120.0, 800.0
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55          # about; the notes say 'about 99 ZFFActor and 55 squads'
FLAGS = ('cap_acc', 'waves', 'trim_wait', 'rings', 'ally_box')


def archive(folder):
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def open_built(folder):
    z = archive(folder)
    return KB.Built(folder, os.path.basename(z)[:-len('_Main.zip')])


def values(sc, k, name):
    return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][AU.ctrl_of(sc, k, name)][1][1:-1])]


def enemy_actors(B):
    sc = B.sc
    return [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and B.values(k).get('ZFFActor[0]') == 'Enemy'
            and any(sc.p.key(nm) == 'ZSoldier' for nm, _b in sc.nodes[k]['ctrls'])]


# ------------------------------------------------------------------ edits of the joined .prp
def cap_accuracy(Jn, B, cap, log):
    """Enemy soldiers: accuracy as used > cap -> cap. -> [(path, was, now)]"""
    rep = []
    team = J.labels('dd', 'ZFFActor').index('ZFFActor[0]')
    for k in range(1, len(Jn.nodes)):               # the joined tree: the waves' men too
        if Jn.cls(k) != 'ZFFActor' or kl_fa.node_values(Jn, k)[team] != 'Enemy':
            continue
        hit = [(i, v) for i, n, v in MAI.ctrls(Jn, k) if n == 'ZSoldier']
        if not hit:
            continue
        i, v = hit[0]
        e = MAI.effective(v)
        if e[MAI.ACC] <= cap + 0.01:
            continue
        fac = MAI.ACC_FACTOR if v[MAI.MERC] == 'No_Mercenary' else 1.0
        new = {}
        if v[MAI.SKILL] != 'eCustom':
            new[MAI.SKILL] = 'eCustom'
            for fi, x in zip(MAI.PRESET_FIELDS, MAI.PRESET[v[MAI.SKILL]]):
                new[fi] = float(x)
        new[MAI.ACC] = round(cap / fac, 1)
        new = {fi: x for fi, x in new.items() if x != v[fi]}
        kl_fa.edit(Jn, k, i, lambda us, new=new: [MAI.setv(Jn, us, fi, x) for fi, x in new.items()])
        after = MAI.effective([new.get(fi, x) for fi, x in enumerate(v)])
        rep.append((Jn.path[k], round(e[MAI.ACC], 1), round(after[MAI.ACC], 1)))
    log('  cap-acc %g: %d soldiers lowered (%s)' % (cap, len(rep), ', '.join('%g->%g' % (a, b) for _p, a, b in rep[:6])))
    return rep


def trim_waits(Jn, sec, log):
    """'040_Timer_done_looting' (TriggerLootDepleted field 1 = seconds) of TRIM_FROM -> sec. -> [(path, was)]"""
    rep = []
    for k in range(1, len(Jn.nodes)):
        if Jn.names[k].endswith('040_Timer_done_looting') and 'Squad#' in Jn.path[k]:
            i, _n, v = MAI.ctrl(Jn, k, 'TriggerLootDepleted')
            if abs(v[1] - TRIM_FROM) < 0.01 and sec < TRIM_FROM:
                kl_fa.edit(Jn, k, i, lambda us: MAI.setv(Jn, us, 1, float(sec)))
                rep.append((Jn.path[k], v[1]))
    log('  trim-wait %g: %d waits cut (%s)' % (sec, len(rep), ', '.join('%s %g' % (p.rsplit('\\', 2)[-2], w) for p, w in rep)))
    return rep


def grow_ally_box(Jn, B, log):
    """-> dict(before, after, board, stop, inside_before) or None when there is nothing to do."""
    k = Jn.resolve(R + 'Gameplay!merc_bot_squad!AllyEscapeBox')[0]
    drives = KB.van_drives(B)
    if not drives:
        log('  ally-box: the map has no key-framed van: nothing to do')
        return None
    d = drives[0]
    size = list(B.box(k))
    pts = [d['board'], d['stop']]
    loc = [B.local(k, p) for p in pts]
    inside = all(all(abs(q[a]) <= size[a] for a in range(3)) for q in loc)
    new = [max(size[a], max(abs(q[a]) for q in loc) + BOX_MARGIN) for a in range(3)]
    if any(new[a] > BOX_MAX for a in range(3)):
        raise ValueError('ally-box: the needed half extents %s pass BOX_MAX %g' % (['%.0f' % x for x in new], BOX_MAX))
    rep = dict(before=size, after=new, board=[round(x) for x in d['board']], stop=[round(x) for x in d['stop']],
               local=[[round(x) for x in q] for q in loc], inside_before=inside)
    if inside and all(abs(new[a] - size[a]) < 1e-6 for a in range(3)):
        log('  ally-box: board and stop lie inside %s already (margin applied: grows %s)' % (size, new))
    lab = J.labels('dd', Jn.cls(k))
    kl_fa.edit(Jn, k, None, lambda us: [MAI.setv(Jn, us, lab.index('ZBoxPrimitive[%d]' % a), float(new[a])) for a in range(3)])
    log('  ally-box: half extents %s -> %s (board %s, stop %s, in the box frame %s)' % (
        [round(x) for x in size], [round(x) for x in new], rep['board'], rep['stop'], rep['local']))
    return rep


def move_rings(Jn, B, nav, home, ents, log):
    """The two rings onto the bots' mesh part. Changes the joined .prp's ZGEOM[2] and the entity's .gms translation."""
    rep = []
    hits = [k for k in range(1, len(Jn.nodes)) if Jn.names[k].endswith(RING_NAMES) and RING_ROOM in Jn.path[k]]
    if len(hits) != 2:
        raise ValueError('rings: %d nodes named %s in %s' % (len(hits), RING_NAMES, RING_ROOM))
    floor0 = min(B.at(k)[1] for k in hits)
    for k in hits:
        w = B.at(k)
        cand = nav.around(w, RING_MAX, home, step=20.0, dy=600.0)
        cand = [c for c in cand if nav.clearance(c[0], c[1], c[2]) >= 40.0]
        if not cand:
            raise ValueError('rings: no cell of the bots\' mesh part within %g of %s' % (RING_MAX, [round(x) for x in w]))
        c = min(cand, key=lambda c: math.hypot(c[0] - w[0], c[2] - w[2]))
        new_w = (c[0], c[1] + 20.0 + (w[1] - floor0), c[2])
        par = Jn.parent[k]
        loc = B.local(par, new_w) if par > 0 else new_w
        lab = J.labels('dd', Jn.cls(k))
        old = list(kl_fa.node_values(Jn, k)[lab.index('ZGEOM[2]')])
        back = B.local(par, w) if par > 0 else w
        if max(abs(back[a] - old[a]) for a in range(3)) > 1.0:
            raise ValueError('rings: %s: the .prp place %s is not the world place %s in its parent frame %s' % (Jn.path[k], old, w, back))
        kl_fa.edit(Jn, k, None, lambda us, lab=lab, loc=loc: AU.setv(Jn, us, lab.index('ZGEOM[2]'), [float(x) for x in loc]))
        e = ents[k - 1]
        e.trans = struct.pack('<3f', *loc) + e.trans[12:]
        rep.append(dict(name=Jn.names[k], was=[round(x) for x in w], now=[round(x) for x in new_w],
                        moved=round(math.dist(w, new_w)), part=nav.part[c[3]]))
    log('  rings: ' + '; '.join('%s %s -> %s (%d)' % (r['name'][-8:], r['was'], r['now'], r['moved']) for r in rep))
    return rep


# ------------------------------------------------------------------ the waves
def plan_waves(src, B, tag, log):
    """-> [dict(name, delay, gap, men=[(entry, post)], target)] and the facts it was planned from."""
    import kl_fa_fedpoints as FP
    L = FP.Lv(src, log=lambda *a: None)
    h = L.halves[0]
    G = L.ground(h)
    cands = FP.candidates(L, h, step=3)
    start = tuple(L.start)
    crew = sorted({(round(p[0] / 50) * 50, p[1], round(p[2] / 50) * 50) for p in L.bots}, key=lambda p: FP.hdist(p, start))
    eye = lambda p: (p[0], p[1] + 160.0, p[2])
    sees = lambda a, b: G.sight(eye(a), eye(b))
    log('  waves: %d cells, %d crew places, START %s' % (len(cands), len(crew), [round(x) for x in start]))
    used, plan, t = [], [], 0.0
    for w, (gap, n, quant) in enumerate(WAVES):
        t += gap
        T = crew[min(len(crew) - 1, int(len(crew) * quant))]
        pool = [c for c in cands if POST_NEAR <= FP.hdist(c, T) <= POST_FAR and FP.hdist(c, start) >= SPAWN_FAR and abs(c[1] - T[1]) < 400.0]
        pool.sort(key=lambda c: abs(FP.hdist(c, T) - 2400.0))
        centre = None
        for c in pool[:400]:
            if not sees(start, c) and not sees(T, c):
                centre = c
                break
        if centre is None:
            raise ValueError('waves: wave %d found no cell out of sight of the START and of %s' % (w + 1, T))
        ents = []
        for radius, gap_ in ((1400.0, MEN_GAP), (2200.0, MEN_GAP), (2200.0, MEN_GAP * 0.7)):      # widen before giving up (GUESS ladder)
            near = sorted((c for c in cands if FP.hdist(c, centre) <= radius and abs(c[1] - centre[1]) < 150.0 and FP.hdist(c, start) >= SPAWN_FAR),
                          key=lambda c: FP.hdist(c, centre))
            ents = []
            for hide_from_crew in (True, False):             # first the unseen ones, then (when too few) whoever is left
                for c in near:
                    if len(ents) >= n:
                        break
                    if any(FP.hdist(c, q) < gap_ for q in used + ents) or c in ents:
                        continue
                    if hide_from_crew and (sees(T, c) or sees(start, c)):
                        continue
                    ents.append(c)
            if len(ents) >= n:
                break
        if len(ents) < n:
            raise ValueError('waves: wave %d found %d of %d places' % (w + 1, len(ents), n))
        men, posts = [], []
        for e in ents:
            ps = [c for c in cands if FP.hdist(c, e) <= 600.0 and abs(c[1] - e[1]) < 120.0 and FP.hdist(c, T) >= 900.0
                  and all(FP.hdist(c, q) >= 250.0 for q in posts + used)]
            q = min(ps, key=lambda c: FP.hdist(c, T)) if ps else e
            posts.append(q)
            men.append((e, q))
        used += ents
        plan.append(dict(name='%d' % (w + 1), delay=t, gap=gap, men=men, target=T))
        log('  wave %d: %d men at %g s, around %s, meant for crew place %s (%d from it)' % (
            w + 1, len(men), t, [round(x) for x in centre], [round(x) for x in T], FP.hdist(centre, T)))
    return plan


def make_waves(B, plan, tag):
    """The new nodes -> (maker, [top nodes], report)."""
    import kl_fa_fed as FED
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops = [clock]
    rep = collections.OrderedDict(waves=[])
    def single(name, delay, listed):
        n = clock.add(FED.clone_built(M, B, node(TIMER_FORM), name))
        M.place(n, (0.0, 0.0, 0.0))
        M.set(n, 'TriggerDelay2', {0: float(delay), 4: listed})
        return R + CLOCK + '\\' + name
    cp = lambda n: R + CLOCK + '\\' + n
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    tmpl = node(R + ENEMY_TEMPLATE[tag])
    acts = [k for k in range(tmpl, sc.end[tmpl]) if sc.cls(k) == 'ZFFActor']
    for i, w in enumerate(plan):
        nxt = plan[i + 1] if i + 1 < len(plan) else None
        top = FED.clone_built(M, B, tmpl, WAVE_G + 'Wave_' + w['name'])
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})        # parked: out of the world until a rout is named
        me = R + WAVE_G + 'Wave_' + w['name']
        d = top.add(M.clone('F07', sq2(FORM), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, (e, q) in enumerate(w['men']):
            pp = d.add(M.clone('F07', sq2(FORM + '\\Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, q)
            refs.append(me + '\\10_Defend\\Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        for j, (e, q) in enumerate(w['men']):
            a = acts[j % len(acts)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], 'Wave_%s_%02d' % (w['name'], j + 1)))
            dx, dz = q[0] - e[0], q[2] - e[2]
            if math.hypot(dx, dz) < 50.0:                 # no walk: face the crew place the wave is meant for
                dx, dz = w['target'][0] - e[0], w['target'][2] - e[2]
            L = math.hypot(dx, dz) or 1.0
            M.place(grp, e, KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(M, B, a))
        go = cp('Go_' + w['name'])
        pace = single('Pace_' + w['name'], w['gap'], [go])
        single('Go_' + w['name'], GO_DELAY, [me + '\\10_Defend'] + ([cp('Pace_' + nxt['name'])] if nxt else []))
        rep['waves'].append(dict(name=w['name'], squad=me, pace=pace, go=go, at=w['delay'], men=[[list(map(round, e)), list(map(round, q))] for e, q in w['men']]))
        tops.append(top)
    rep['first'] = rep['waves'][0]['pace']
    return M, tops, rep


# ------------------------------------------------------------------ writing (kl_fa_fed.apply / kl_fa_bank.extras)
def build(src, dst, opt, log=print):
    import kl_graft
    on = [f for f in FLAGS if opt.get(f)]
    B = open_built(src)
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    tag = 'dm01' if B.sc.resolve(R + ENEMY_TEMPLATE['dm01']) else 'dm02'
    os.makedirs(dst, exist_ok=True)
    zname = os.path.basename(B.zp)
    slot = zname[:-len('_Main.zip')]
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and f != zname:
            shutil.copyfile(p, os.path.join(dst, f))
    rep = collections.OrderedDict(source=B.folder, out=dst, flags=opt, map=tag, members_changed=[])
    if not on:
        shutil.copyfile(B.zp, os.path.join(dst, zname))
        log('kl_old_waves: no flag: %s copied unchanged' % zname)
        return rep
    sc = B.sc
    before = KB.sizes(B.folder, slot)
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
    M, tops, order, wrep, plan = None, [], [], None, None
    if opt.get('waves'):
        plan = plan_waves(src, B, tag, log)
        M, tops, wrep = make_waves(B, plan, tag)
        q, order = M.scene(tops)
        Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'oldwaves')
    else:
        Jn = same
    nav = KB.Nav(B.scene.nav, links=True)
    home = KB.stations(B, nav)['home']
    ents = B.ents
    if opt.get('cap_acc'):
        rep['cap_acc'] = cap_accuracy(Jn, B, float(opt['cap_acc']), log)
    if opt.get('trim_wait'):
        rep['trim_wait'] = trim_waits(Jn, float(opt['trim_wait']), log)
    if opt.get('ally_box'):
        rep['ally_box'] = grow_ally_box(Jn, B, log)
    if opt.get('rings'):
        rep['rings'] = move_rings(Jn, B, nav, home, ents, log)
    if wrep:                                            # the chain's start: the round-start list of the AIMonitor
        k = Jn.resolve(MONITOR)[0]
        ci = AU.ctrl_of(Jn, k, 'AIMonitor')
        have = list(values(Jn, k, 'AIMonitor')[START_LIST])
        kl_fa.edit(Jn, k, ci, lambda us: AU.setv(Jn, us, START_LIST, have + [wrep['first']]))
        rep['waves'] = wrep
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    moved = listed = repointed = 0
    if tops or opt.get('rings'):
        A = B.scene
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
            for c in n.kids:
                ent(c, e)
        for t in tops:
            ent(t, None)
        A.ref_slots = nxt
        faults = A.check()
        if faults:
            raise ValueError('kl_scene.check: %s' % faults[:3])
        allents = list(A.entities())
        if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
            raise ValueError('the new .gms and .prp disagree on the entities')
        gms, buf = A.write()
        new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
        if tops:
            slot1 = A.slots()
            ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
            ids[1] = 1
            octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
            moved = sum(1 for a, b in ids.items() if a != b)
            items = []
            for t in tops:
                pts = [k.pos for k in t.kids if k.pos] + [p.pos for k in t.kids for p in k.kids if p.pos]
                lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
                hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
                items.append((slot1[made[id(t)]] + 2, lo, hi))
            root3 = octn.rooms[0][3]
            new_prm = None
            if root3 is not None and items:
                octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
                listed = len(items)
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
                                struct.pack_into('<I', prm, off + 0x1c, move[v]); repointed += 1
                            elif v and v not in old:
                                raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
                    if not repointed:
                        raise ValueError('%d .oct records moved and no model root names one' % len(move))
                    new_prm = bytes(prm)
            post = KB.room_sets_check(A, octn, rmin, rmcn)
            if post != pre:
                raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
            new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
            if new_prm is not None:
                new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    zp = kl_graft.write_zip(os.path.join(dst, zname), [(n, new[n]) for n in B.order])
    after = KB.sizes(dst, slot)
    if after != before:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    rep.update(members_changed=changed, entities_added=len(order), slot_ids_moved=moved, groups_listed_in_root_tree_3=listed,
               prm_model_roots_repointed=repointed, big_before=before, big_after=after)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_old_waves: flags %s; members changed %s\n' % (json.dumps(opt, sort_keys=True), ' '.join(changed)))
    with open(os.path.join(dst, 'old_waves.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    log('written %s: %d entities added; members changed: %s; %d slot ids renumbered, %d groups listed, %d model roots repointed'
        % (zp, len(order), ' '.join(changed) or '-', moved, listed, repointed))
    return rep


# ------------------------------------------------------------------ check / diff
def check(folder, log=print):
    """-> [(FAIL | ok | note, text)]"""
    B = open_built(folder)
    sc = B.sc
    out = []
    say = lambda s, t: (out.append((s, t)), log('%-4s %s' % (s, t)))
    acts = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor')
    squads = sum(1 for k in range(1, len(sc.nodes)) if any(sc.p.key(nm) == 'ZSquadScript' for nm, _b in sc.nodes[k]['ctrls']))
    say('FAIL' if acts > ENGINE_ACTORS else 'ok', 'ZFFActor %d (engine limit about %d)' % (acts, ENGINE_ACTORS))
    say('FAIL' if squads > ENGINE_SQUADS else 'ok', 'squads (ZSquadScript) %d (engine limit about %d)' % (squads, ENGINE_SQUADS))
    top = collections.Counter(MAI.effective(v)[MAI.ACC] for k in enemy_actors(B) for _i, n, v in MAI.ctrls(sc, k) if n == 'ZSoldier')
    say('note', 'Enemy-team accuracy as used: %s' % ', '.join('%g x%d' % kv for kv in sorted(top.items())))
    pace = sc.resolve(R + CLOCK)
    if not pace:
        say('note', 'no wave chain in this folder')
        return out
    mon = values(sc, sc.resolve(MONITOR)[0], 'AIMonitor')[START_LIST]
    first = R + CLOCK + '\\Pace_1'
    say('ok' if first in mon else 'FAIL', 'AIMonitor field %d names %s' % (START_LIST, first))
    nav = KB.Nav(B.scene.nav, links=True)
    home = KB.stations(B, nav)['home']
    n, men = 1, 0
    while True:
        p = sc.resolve(R + CLOCK + '\\Pace_%d' % n)
        if not p:
            break
        g = sc.resolve(R + CLOCK + '\\Go_%d' % n)
        sq = sc.resolve(R + WAVE_G + 'Wave_%d' % n)
        if not g or not sq:
            say('FAIL', 'wave %d: Go %s squad %s' % (n, bool(g), bool(sq)))
            break
        pv, gv = values(sc, p[0], 'TriggerDelay2'), values(sc, g[0], 'TriggerDelay2')
        want = [R + CLOCK + '\\Go_%d' % n]
        ok = [x.lower() for x in pv[4]] == [x.lower() for x in want]
        rout = R + WAVE_G + 'Wave_%d\\10_Defend' % n
        ok2 = gv[4] and gv[4][0].lower() == rout.lower() and all(sc.resolve(x) for x in gv[4])
        z = values(sc, sq[0], 'ZSquadScript')
        mine = [k for k in range(sq[0], sc.end[sq[0]]) if sc.cls(k) == 'ZFFActor']
        men += len(mine)
        bad = []
        for k in mine:
            c = B.at(k)
            hit = nav.at(c[0], c[1], c[2], dy=200.0, part=home)
            if hit is None:
                bad.append(sc.names[sc.parent[k]])
        say('ok' if ok and ok2 and z[3] == 0 and not bad else 'FAIL',
            'wave %d: Pace %.0f s -> Go -> rout + %s; parked=%s; %d men, %d off the bots\' mesh part %s' % (
                n, pv[0], 'Pace_%d' % (n + 1) if len(gv[4]) > 1 else 'end', z[3] == 0, len(mine), len(bad), bad[:3]))
        n += 1
    say('ok', '%d waves, %d men' % (n - 1, men))
    return out


def diff(src, dst, log=print):
    """Member by member (CRC, size) and file by file beside the archive. -> list of differing names."""
    a, b = archive(src), archive(dst)
    out = []
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        ia, ib = {i.filename: i for i in za.infolist()}, {i.filename: i for i in zb.infolist()}
        if list(ia) != list(ib):
            out.append('member list/order differs')
        for n in ib:
            if n not in ia:
                out.append('new member ' + n)
            elif (ia[n].CRC, ia[n].file_size) != (ib[n].CRC, ib[n].file_size):
                out.append('%s %d -> %d bytes' % (n, ia[n].file_size, ib[n].file_size))
    names = set(os.listdir(src)) | set(os.listdir(dst))
    for f in sorted(names):
        if f.lower().endswith('_main.zip') or f in ('graft.txt', 'old_waves.json'):
            continue
        pa, pb = os.path.join(src, f), os.path.join(dst, f)
        if not os.path.isfile(pa) or not os.path.isfile(pb):
            out.append('file only on one side: ' + f)
        elif zlib.crc32(open(pa, 'rb').read()) != zlib.crc32(open(pb, 'rb').read()):
            out.append('file differs: ' + f)
    for x in out:
        log('  ' + x)
    log('diff: %d differences' % len(out))
    return out


def options(a):
    opt = {}
    def num(name, default):
        if name in a:
            i = a.index(name)
            if i + 1 < len(a) and not a[i + 1].startswith('--'):
                v = float(a[i + 1]); del a[i:i + 2]
            else:
                v = default; del a[i]
            return v
        return None
    for name, key, d in (('--cap-acc', 'cap_acc', CAP_ACC), ('--trim-wait', 'trim_wait', TRIM_WAIT)):
        v = num(name, d)
        if v is not None:
            opt[key] = v
    for name, key in (('--waves', 'waves'), ('--rings', 'rings'), ('--ally-box', 'ally_box')):
        if name in a:
            a.remove(name); opt[key] = True
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        build(a[1], a[2], opt)
    elif len(a) == 2 and a[0] == 'check':
        out = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2]) else 0)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
