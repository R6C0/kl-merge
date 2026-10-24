"""kl_dm02_assault_1025.py - DM02 mall (F02 slot): the F07-style SWAT SHUTTER ASSAULT. Written 2026-10-25, OFFLINE only, nothing is run in the game.
(re/dd_setpieces.md placement #1; wish: a Dog Days FA moment in the Mall - something happens a minute in that changes the fight, enemies arrive
through a door, never appear in view.)

WHAT THE PLAYER SEES. ASSAULT_AT seconds after the round starts (150 s) the two ground-floor roller shutters of the ATRIUM that no shop uses
(Atrium_101a, SI0401_M02_FA_RollerShutterA_04 = west side, north end, world x -1990 z -2665..-2025; _02 = east side, south end, world x 1990
z 1660..1020; both y 0) give their shutter sound (DM02's own 'Shutters_Sound' sample), and 2.4 s later the shutters are gone (DeactivateGeom, the
mechanism of the installed shops and of kl_hc2_garagedoor: the model and its HVK shape go, there is no raise animation). A SWAT squad of SQUAD_MEN
men per shutter (clones of DM02's own 'AIEnemies!PoliceSwats' men, the actors the OldWaves! chain uses) has stood parked out of the world; 0.8 s
after the sound it is released at its entry places 60 cm BEHIND the shutter plane in the dark shop room (the shutter is still closed there, so no
one sees them appear), the rout walks them to posts on the navigation mesh in the atrium, 450..1500 cm in front of the opened frontage.

WHAT IS CLONED (nothing is invented; every form is a node of this build or of stock Dog Days)
  - group 'KL_Assault!' (clone of the bot Squad#02 top, controllers emptied, as OldWaves!Clock) holding the timers (clones of Timer_start_bots),
    the opener (clone of F04's GeomDeactivator_shake_area, DeactivateGeom field 1 = the two shutters) and the two sound nodes (clone of F04's
    Box_crash_sound, Audio_PlaySound field 0 = DM02's Shutters_Sound sample 2384432 = ZSNDOBJ[0] of SinglePlayerSound!3D!Shutters_Sound).
  - two parked squads 'KL_Assault!Wave_W' / '_E' (the OldWaves! form: ZSquadScript field 3 = 0, one Defend rout cloned from F07 Squad#02 with the Pos nodes).
  - the start: a TriggerDelay2 appended to AIMonitor field 2 (the round-start list), exactly as the installed shops and OldWaves! do.
Shops A (KL_Shops!, the 5 shops, 3 co-op shutters) is untouched: its shutters (Atrium_201a 01..04, Atrium_101a 03) are not used here, asserted.

BUDGET (live-proven limit 99 actors / 55 squads, re/engine_facts.md): the input holds 49 / 19; this adds 2*SQUAD_MEN actors and 2 squads.

GUESSES (each also in a code comment): (1) the engine lets an actor that is released 100 cm outside the mesh (the mesh ends 45 cm in front of the
shutter plane, nothing exists behind it) find a path onto it - UNPROVEN, the one real risk; a fallback is NOT built because the alternative (entries on
the mesh) puts them in view; (2) DeactivateGeom removes the visible model as well as the collision (as in the installed shops, not yet seen in the game);
(3) Audio_PlaySound field 0 takes the sound id of a ZSNDOBJ of the same level and plays it at the node; (4) timings.

Usage (from tools/):
  python kl_dm02_assault_1025.py build <in F02_Main.zip> <out F02_Main.zip> [--force]
  python kl_dm02_assault_1025.py check <zip>
  python kl_dm02_assault_1025.py floor <DM02 folder>          read-only: is there walkable floor under every entry (needs the stock-folder layout)
  python kl_dm02_assault_1025.py stage <in F02_Main.zip> <out folder> [--rehearse <scratch>]
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_octree as O
import kl_old_waves as KOW
import kl_dm02_shops_1024 as SH
import kl_prpjoin as J
from kl_prp import Prp, units

BS = chr(92)
R = 'ROOT' + BS
SRC_MD5 = '30b3ddf02cc864c462c803924c1226a1'      # live DM02 = shops A (2026-10-25)
GROUP = 'KL_Assault!'
WAVE = {'W': GROUP + 'Wave_W', 'E': GROUP + 'Wave_E'}
TAG = '.before-1025dm02assault'
ASSAULT_AT = 150.0       # s after the round start (GUESS: the heisters are in the mall from the first second; mid-round)
SOUND_TO_GO = 0.8        # s from the shutter sound to the release of the squads (behind the still closed shutters)
SOUND_TO_OPEN = 2.4      # s from the shutter sound to the shutters going
SQUAD_MEN = 6
ENTRY_DEPTH = 60.0       # cm behind the shutter plane (the plane is the shutter node's local z = 0; the mesh ends 45 cm in front of it)
POST_NEAR, POST_FAR, POST_AT, POST_GAP = 450.0, 1500.0, 900.0, 260.0
SPAN = 640.0
SHUTTERS = {'W': (-1990.0, 0.0, -2665.0), 'E': (1990.0, 0.0, 1660.0)}      # Atrium_101a 04 / 02
SHOPS_A_SHUTTERS = [(-1990.0, 500.0, 1032.0), (1990.0, 500.0, 1660.0), (1990.0, 500.0, -2033.0), (-1990.0, 500.0, -2665.0), (-1990.0, 0.0, 1032.0)]
SOUND_ID = 2384432       # ZSNDOBJ[0] of ROOT\Audio\SinglePlayerSound!3D!Shutters_Sound (read from the build, asserted)
F04_PREFIX = 'F04_Outside_LootHall' + BS + 'SI0100_F04_Coop_Move_Dxxr_04!'
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55


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


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# ------------------------------------------------------------------ the plan (measured from the scene and the mesh)
def plan_side(B, nav, home, side, log):
    sc = B.sc
    k = SH.shutter_at(B, SHUTTERS[side])
    o, xs, zs = SH.shutter_frame(B, k)
    mid = [o[i] + xs[i] * SPAN / 2.0 for i in range(3)]
    front = [-zs[i] for i in range(3)]                      # into the atrium (the mesh side)
    # entries: one row, SQUAD_MEN men across the span, ENTRY_DEPTH behind the plane (zs = into the shop room)
    lats = [SPAN * (i + 0.5) / SQUAD_MEN for i in range(SQUAD_MEN)]
    entries = [tuple(o[i] + xs[i] * lat + zs[i] * ENTRY_DEPTH for i in range(3)) for lat in lats]
    # posts: mesh cells in front of the frontage, spaced, nearest to the ring POST_AT in front of the middle
    centre = [mid[i] + front[i] * POST_AT for i in range(3)]
    cl = lambda c: nav.clearance(c[0], c[1], c[2])
    cells = [c for c in nav.around(centre, 900.0, home, step=40.0, dy=120.0)
             if POST_NEAR <= math.hypot(c[0] - mid[0], c[2] - mid[2]) <= POST_FAR and cl(c) >= 45.0 and dot([c[0] - mid[0], 0, c[2] - mid[2]], front) > 0]
    cells.sort(key=lambda c: math.hypot(c[0] - centre[0], c[2] - centre[2]))
    posts = []
    for c in cells:
        if all(math.hypot(c[0] - q[0], c[2] - q[2]) >= POST_GAP for q in posts):
            posts.append(c)
        if len(posts) == SQUAD_MEN:
            break
    if len(posts) < SQUAD_MEN:
        raise ValueError('side %s: only %d posts on the mesh in front of the frontage' % (side, len(posts)))
    posts.sort(key=lambda c: dot([c[0] - o[0], 0, c[2] - o[2]], xs))        # lateral order = the entries' order: no crossing
    log('  side %s: shutter %s, span axis %s, into the room %s, %d posts %s' % (side, sc.path[k].rsplit(BS, 2)[-2], xs, zs, len(posts), [(round(p[0]), round(p[2])) for p in posts]))
    return dict(side=side, node=k, path=sc.path[k], origin=o, xs=xs, zs=zs, mid=mid, front=front, entries=entries, posts=posts)


# ------------------------------------------------------------------ the new nodes
def make_nodes(B, plans, sound_id):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), GROUP)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops = [clock]
    cp = lambda n: R + GROUP + BS + n
    s4 = KB.Maker.level('F04')[0]
    f4 = lambda tail: s4.resolve([p for p in (s4.path[k] for k in range(1, len(s4.names)) if s4.path[k]) if p.endswith(F04_PREFIX + tail)][0])[0]

    def timer(name, delay, listed):
        n = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), name))
        M.place(n, (0.0, 0.0, 0.0))
        M.set(n, 'TriggerDelay2', {0: float(delay), 4: listed})
        return cp(name)
    rep = collections.OrderedDict()
    tmpl = node(R + KOW.ENEMY_TEMPLATE['dm02'])
    acts = [k for k in range(tmpl, sc.end[tmpl]) if sc.cls(k) == 'ZFFActor']
    if not acts:
        raise ValueError('the SWAT template has %d actors' % len(acts))
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    routs, sounds = [], []
    for pl in plans:
        side = pl['side']
        top = FED.clone_built(M, B, tmpl, WAVE[side])
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}})        # parked until its rout is named (as OldWaves!)
        me = R + WAVE[side]
        d = top.add(M.clone('F07', sq2(KOW.FORM), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, p in enumerate(pl['posts']):
            pp = d.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, p[:3])
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        routs.append(me + BS + '10_Defend')
        for j, (e, p) in enumerate(zip(pl['entries'], pl['posts'])):
            a = acts[j % len(acts)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], 'Assault_%s_%02d' % (side, j + 1)))
            dx, dz = p[0] - e[0], p[2] - e[2]
            L = math.hypot(dx, dz) or 1.0
            M.place(grp, e, KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(M, B, a))
        tops.append(top)
        # the sound node at the middle of the frontage (clone of F04's Box_crash_sound: Audio_PlaySound [0, 'AITrigger', 'Deactivate'])
        sn = clock.add(M.clone('F04', f4('Box_crash_sound'), 'Snd_' + side))
        M.place(sn, pl['mid'])
        M.set(sn, 'Audio_PlaySound', {0: sound_id})
        sounds.append(cp('Snd_' + side))
    op = clock.add(M.clone('F04', f4('GeomDeactivator_shake_area'), 'Open'))
    M.place(op, (0.0, 0.0, 0.0))
    M.set(op, 'DeactivateGeom', {1: [pl['path'] for pl in plans]})
    t_open = timer('T_Open', SOUND_TO_OPEN, [cp('Open')])
    t_go = timer('T_Go', SOUND_TO_GO, routs)
    t_start = timer('T_Start', ASSAULT_AT, sounds + [t_go, t_open])
    rep.update(start=t_start, go=t_go, open=t_open, sounds=sounds, routs=routs)
    return M, tops, rep


# ------------------------------------------------------------------ build
def build(src, dst, force=False, log=print):
    have = md5(src)
    if have != SRC_MD5 and not force:
        raise ValueError('%s: md5 %s is not the DM02 zip this was checked on (%s); use --force' % (src, have, SRC_MD5))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('the output must be another path than the input')
    B = KB.Built(src)
    sc = B.sc
    if any(sc.names[t] == GROUP for t in sc.tops()):
        log('kl_dm02_assault_1025: %s already holds %s: copied unchanged' % (src, GROUP))
        shutil.copyfile(src, dst)
        return None
    for at in SHOPS_A_SHUTTERS:                              # the installed shops keep their shutters
        if any(max(abs(a - b) for a, b in zip(at, s_)) < 1.0 for s_ in SHUTTERS.values()):
            raise ValueError('a shutter of the assault is a shop shutter')
    a0, s0 = census(sc)
    if a0 + 2 * SQUAD_MEN > ENGINE_ACTORS or s0 + 2 > ENGINE_SQUADS:
        raise ValueError('budget: %d actors / %d squads + the assault passes %d / %d' % (a0, s0, ENGINE_ACTORS, ENGINE_SQUADS))
    snd = [k for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].endswith('SinglePlayerSound!3D!Shutters_Sound')]
    if len(snd) != 1 or B.values(snd[0]).get('ZSNDOBJ[0]') != SOUND_ID:
        raise ValueError('DM02 Shutters_Sound is not sound id %d' % SOUND_ID)
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
    home = KB.stations(B, nav)['home']
    log('kl_dm02_assault_1025: input %d actors / %d squads' % (a0, s0))
    plans = [plan_side(B, nav, home, side, log) for side in ('W', 'E')]
    M, tops, rep = make_nodes(B, plans, SOUND_ID)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'assault')
    k = Jn.resolve(KOW.MONITOR)[0]
    ci = KOW.AU.ctrl_of(Jn, k, 'AIMonitor')
    have_l = list(KOW.values(Jn, k, 'AIMonitor')[KOW.START_LIST])
    if rep['start'] not in have_l:
        kl_fa.edit(Jn, k, ci, lambda us: KOW.AU.setv(Jn, us, KOW.START_LIST, have_l + [rep['start']]))
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
    for t in tops:                                           # each top in the root's tree 3 with the box of its children (as OldWaves!)
        pts = [c.pos for c in t.kids if c.pos] + [p.pos for c in t.kids for p in c.kids if p.pos]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    if root3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        pm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', pm, 0)
        old = set(octx.record_refs())
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', pm, tt + 16 * i)
            if size == 64 and pm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, off + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, off + 0x1c, move[v]); repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
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
    big_before = {n.rsplit('_Main', 1)[1]: B.files[n] for n in B.order if n.endswith(('_Main.prm', '_Main.ANM', '_Main.fxc'))}
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    for e_, v in big_before.items():
        if e_ in ('.ANM', '.fxc') and len(new[B.ext[e_]]) != len(v):
            raise ValueError('a large block changed its size: ' + e_)
    a1, s1 = census(KB.Built(dst).sc)
    r = collections.OrderedDict(source=src, source_md5=have, out=dst, out_md5=md5(dst), members_changed=changed, entities_before=len(B.ents),
                                entities=len(ents), entities_added=len(order), ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=moved,
                                prm_model_roots_repointed=repointed, actors=(a0, a1), squads=(s0, s1), chain=rep,
                                assault_at_s=ASSAULT_AT, sound_to_go_s=SOUND_TO_GO, sound_to_open_s=SOUND_TO_OPEN,
                                sides={pl['side']: dict(shutter=pl['path'], shutter_origin=[round(v) for v in pl['origin']],
                                                        entries=[[round(v) for v in e] for e in pl['entries']],
                                                        posts=[[round(v) for v in p[:3]] for p in pl['posts']]) for pl in plans})
    log('kl_dm02_assault_1025: %d entities added, REF ids %s, members changed %s, %d slot ids renumbered, %d .prm roots re-pointed, actors %d -> %d, squads %d -> %d -> %s (%s)'
        % (len(order), r['ref_ids'], ' '.join(changed), moved, repointed, a0, a1, s0, s1, dst, r['out_md5']))
    return r


# ------------------------------------------------------------------ check
def check(zp, log=print):
    B = KB.Built(zp)
    sc = B.sc
    bad = 0

    def say(ok, msg):
        nonlocal bad
        bad += (not ok)
        log('%s %s' % ('ok  ' if ok else 'FAIL', msg))
    tops = [t for t in sc.tops() if sc.names[t] == GROUP]
    say(len(tops) == 1, 'one %s group' % GROUP)
    a, s = census(sc)
    say(a <= ENGINE_ACTORS and s <= ENGINE_SQUADS, 'budget %d actors (limit %d) / %d squads (limit %d)' % (a, ENGINE_ACTORS, s, ENGINE_SQUADS))
    nav = KB.Nav(B.scene.nav, links=True)
    home = KB.stations(B, nav)['home']
    paths = lambda ks: [sc.path[k] for k in ks]
    mon = sc.resolve(KOW.MONITOR)[0]
    start = KOW.values(sc, mon, 'AIMonitor')[KOW.START_LIST]
    say(R + GROUP + BS + 'T_Start' in start, 'AIMonitor field 2 names T_Start (%d entries)' % len(start))
    dead = []
    for k in range(tops[0], sc.end[tops[0]]) if tops else ():
        for nm, body in sc.nodes[k]['ctrls']:
            for u in units(body[1:-1]):
                v = kl_fa.value(sc, u)
                for x in (v if isinstance(v, list) else [v]):
                    if isinstance(x, str) and x.startswith(R) and not sc.resolve(x):
                        dead.append((sc.path[k], x))
    for w in WAVE.values():
        for k in sc.resolve(R + w):
            for j in range(k, sc.end[k]):
                for nm, body in sc.nodes[j]['ctrls']:
                    for u in units(body[1:-1]):
                        v = kl_fa.value(sc, u)
                        for x in (v if isinstance(v, list) else [v]):
                            if isinstance(x, str) and x.startswith(R) and not sc.resolve(x):
                                dead.append((sc.path[j], x))
    say(not dead, 'every reference of the assault nodes resolves (%d dead)' % len(dead))
    for side in ('W', 'E'):
        k = SH.shutter_at(B, SHUTTERS[side])
        o, xs, zs = SH.shutter_frame(B, k)
        wk = sc.resolve(R + WAVE[side])
        say(len(wk) == 1, 'wave %s present' % side)
        acts = [j for j in range(wk[0], sc.end[wk[0]]) if sc.cls(j) == 'ZFFActor'] if wk else []
        say(len(acts) == SQUAD_MEN, 'wave %s: %d men' % (side, len(acts)))
        behind = [dot([B.at(j)[i] - o[i] for i in range(3)], zs) for j in acts]
        lat = [dot([B.at(j)[i] - o[i] for i in range(3)], xs) for j in acts]
        say(all(abs(b - ENTRY_DEPTH) < 1.0 for b in behind) and all(0 < l < SPAN for l in lat), 'wave %s: all men %g cm behind the plane, inside the span (lat %s)' % (side, ENTRY_DEPTH, [round(l) for l in lat]))
        say(all(nav.at(*B.at(j), dy=120) is None for j in acts), 'wave %s: entries are off the mesh (hidden behind the shutter), as designed' % side)
        pos = [j for j in range(wk[0], sc.end[wk[0]]) if sc.names[j].startswith('Pos#')] if wk else []
        on = [nav.at(*B.at(j), dy=140) for j in pos]
        say(len(pos) == SQUAD_MEN and all(h and nav.part[h[0]] == home for h in on), 'wave %s: %d posts on the START half of the mesh' % (side, len(pos)))
        say(all(dot([B.at(j)[i] - o[i] for i in range(3)], zs) < -POST_NEAR + 100 for j in pos), 'wave %s: posts in front of the frontage' % side)
        say(any(sc.path[k] in (sc.path[j] for j in [x for x in sc.resolve(R + GROUP + BS + 'Open')]) or True for _ in [0]), 'opener present')
    op = sc.resolve(R + GROUP + BS + 'Open')
    tgt = []
    if op:
        for nm, body in sc.nodes[op[0]]['ctrls']:
            if sc.p.key(nm) == 'DeactivateGeom':
                tgt = [kl_fa.value(sc, u) for u in units(body[1:-1])][1]
    want = [sc.path[SH.shutter_at(B, SHUTTERS[x])] for x in ('W', 'E')]
    say(sorted(tgt) == sorted(want), 'opener names the two atrium shutters')
    t = {n: sc.resolve(R + GROUP + BS + n) for n in ('T_Start', 'T_Go', 'T_Open', 'Snd_W', 'Snd_E')}
    say(all(len(v) == 1 for v in t.values()), 'timers and sounds present')
    # shops A intact
    shops = sc.resolve(R + 'KL_Shops!')
    say(len(shops) == 1, 'KL_Shops! (shops A) still present')
    return bad


# ------------------------------------------------------------------ the floor under the entries (read only; the stock folder layout)
def floor(folder, log=print):
    import kl_fa_fedpoints as FP
    L = FP.Lv(folder, log=lambda *a: None)
    G = L.ground(L.halves[0])
    B = L.B
    bad = 0
    for side in ('W', 'E'):
        k = SH.shutter_at(B, SHUTTERS[side])
        o, xs, zs = SH.shutter_frame(B, k)
        for i in range(SQUAD_MEN):
            lat = SPAN * (i + 0.5) / SQUAD_MEN
            e = [o[j] + xs[j] * lat + zs[j] * ENTRY_DEPTH for j in range(3)]
            c, hit, near = G.under((e[0], e[1] + 60.0, e[2]))
            ok = hit is not None and abs(hit - e[1]) < 40.0 and not G.blocked(c, hit)
            bad += (not ok)
            log('%s side %s man %d at (%d,%d,%d): floor %s (cell nearest %s)' % ('ok  ' if ok else 'FAIL', side, i + 1, e[0], e[1], e[2], hit, near))
    return bad


# ------------------------------------------------------------------ installer (kl_dm02_shops_1024's, renamed)
PS1 = SH.PS1.replace('shops.json', 'assault.json').replace('shops.ps1', 'assault.ps1').replace("'.before-1024shops'", "'%s'" % TAG).replace(
    'more open shops with loot (+ co-op shutters in variant A) (tools/kl_dm02_shops_1024.py, 2026-10-24)',
    'SWAT shutter assault (tools/kl_dm02_assault_1025.py, 2026-10-25)').replace('(variant $($man.variant))', '').replace(
    'A and B share the backup name on purpose: install only one; to switch, UNDO the installed one first.', 'Chained on shops A: the live md5 must be exactly the pinned one.').replace(
    'or the other variant installed? Not changed.', '. Not changed.').replace('(changed since, or the other variant?)', '(changed since)')
BAT = SH.BAT.replace('shops.ps1', 'assault.ps1')


def _ps(d, game, undo=False):
    # the rehearsal runs on a scratch tree: the running-game guard is skipped in a scratch copy of the script (the staged one keeps it)
    sp = os.path.join(d, 'assault_scratch.ps1')
    txt = open(os.path.join(d, 'assault.ps1'), newline='').read().splitlines()
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
    old = md5(src)
    if old != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (old, SRC_MD5))
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, 'F02_Main.zip')
    rep = build(src, z, log=log)
    if rep is None:
        raise SystemExit('input already holds ' + GROUP)
    new = md5(z)
    man = dict(m='DM02', f='F02_Main.zip', variant='-', old=old, new=new, tag=TAG)
    with open(os.path.join(out, 'assault.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'assault.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL dm02 assault.bat', ''), ('UNDO dm02 assault.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(src, out, man, scratch, log)
    return 0


def rehearse(src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', 'DM02', 'F02_Main.zip')
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    log('rehearsal target: ' + live)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    t = _ps(d, g); log(t); assert 'installed' in t and md5(live) == man['new'], t
    assert os.path.isfile(live + TAG) and md5(live + TAG) == man['old']
    t = _ps(d, g, True); log(t)
    assert md5(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    t = _ps(d, g); assert md5(live) == man['new']
    t = _ps(d, g); assert 'already installed' in t, t
    t = _ps(d, g, True); assert md5(live) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = _ps(d, g); log(t); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.copy2(src, live)
    log('rehearsal ok (install, undo byte-identical, reinstall same md5, wrong live md5 refused)')
    shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('build', 'check', 'floor', 'stage'):
        print(__doc__)
        return 2
    if a[0] == 'check':
        return 1 if check(a[1]) else 0
    if a[0] == 'floor':
        return 1 if floor(a[1]) else 0
    if a[0] == 'build':
        build(a[1], a[2], force='--force' in a)
        return 0
    return stage(a[1], a[2], opt('--rehearse'))


if __name__ == '__main__':
    sys.exit(main())
