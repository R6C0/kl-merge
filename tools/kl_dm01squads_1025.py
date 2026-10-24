"""kl_dm01squads_1025.py - DM01 (Hot Coffee) stage A, 2026-10-25: pre-placed holding squads (re/dm01_squads_1025.md).

Owner: "i want some to sit in that room where they come from then some others can do what they did that round, also want some more agents in
the warehouse ... and theres people on the scaffolding like the top part of the warehouse".

Three new squads, all PRE-PLACED (ZSquadScript f3 = 1: in the world from the load) with a Defend-only rout (no next rout, so they stay), started by
one timer 'KL_Squads!Clock\\Go' (0.1 s, on the AIMonitor round-start list, as OldWaves!Clock / kl_dm03a_swat_1025.py):
  KL_Hold!Shop   4 men in the shop room the push waves start from (the places of Wave_1_01..04, moved out of OldWaves!Wave_1: Wave_1 keeps 5 and
                 still pushes after dm01fix's f3 = 1 / timers)
  KL_WH!Floor    8 men on the warehouse floor (y 60) in the hall behind the kick doors, four pairs spread down the hall, out of the start view
  KL_WH!Top      4 men on the upper level (y 860, the control room / gallery of the NAV, part 1) on real nav cells
Their weapons are the removed men's (Hold) and Wave_3's own two actor forms (Floor / Top).

    python kl_dm01squads_1025.py squads <in.zip> <out.zip>      the squads on a DM01 zip (kl_fa_bots.Built); see chain() in the build folder's script
"""
import collections, json, math, os, shutil, struct, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_dm02_assault_1025 as AS
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55           # engine-proven
WAVE1, WAVE3 = 'OldWaves!Wave_1', 'OldWaves!Wave_3'
CLOCK = 'KL_Squads!Clock'
HOLD, FLOOR, TOP = 'KL_Hold!Shop', 'KL_WH!Floor', 'KL_WH!Top'
GO_DELAY = 0.1
N_HOLD = 4                                      # Wave_1_01..04 leave Wave_1 (and their Pos#01..04)
# FLOOR: hall cells (y 60), measured 2026-10-25 on the base zip's walk mesh and Havok line of sight (kl_fa_fedpoints G.sight): each is on the main part,
# clearance >= 90, NOT seen from the route points of the crew's walk to the van, >= 350 from the other pairs and from the door line z 19684.
# (ex13..ex16 in the build folder.) Pair order: south-west/south-east, mid, east wall, north.
FLOOR_CELLS = [(1770.0, 60.0, 17530.0), (2730.0, 60.0, 17570.0), (1650.0, 60.0, 18050.0), (2290.0, 60.0, 18170.0),
               (2930.0, 60.0, 18810.0), (2930.0, 60.0, 18450.0), (1650.0, 60.0, 19050.0), (2330.0, 60.0, 19210.0)]
# TOP: nav cells of the upper level (y 860), chosen by how much hall floor they see (ex16; G.sight)
TOP_CELLS = [(2931.0, 860.0, 17159.0), (2910.0, 860.0, 17080.0), (2919.0, 860.0, 17004.0), (2851.0, 860.0, 17159.0)]
FACE = (0.0, 1.0)                               # toward +z: the crew comes from the shop side (GUESS: only the first turn; Defend turns them)


def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


def hold_nodes(sc):
    """-> ([group nodes of Wave_1_01..04], [Pos nodes 01..04]) of the base."""
    w = one(sc, WAVE1)
    kids = [k for k in range(w + 1, sc.end[w]) if sc.parent[k] == w]
    grp = [k for k in kids if sc.names[k].startswith('Wave_1_')]
    grp.sort(key=lambda k: sc.names[k])
    d = [k for k in kids if sc.names[k] == '10_Defend'][0]
    pos = [k for k in range(d + 1, sc.end[d]) if sc.parent[k] == d]
    pos.sort(key=lambda k: sc.names[k])
    return grp[:N_HOLD], pos[:N_HOLD]


def make_nodes(B):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    grp, pos = hold_nodes(sc)
    w3 = one(sc, WAVE3)
    acts3 = [k for k in range(w3, sc.end[w3]) if sc.cls(k) == 'ZFFActor']
    if len(grp) != N_HOLD or len(pos) != N_HOLD or len(acts3) < 2:
        raise ValueError('Wave_1 / Wave_3 shape: %d groups, %d posts, %d actors' % (len(grp), len(pos), len(acts3)))
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    tops, paths = [clock], []

    def squad(name, men):
        """men = [(cell, source group node, source actor node)] -> the squad top (pre-placed, Defend-only)."""
        top = FED.clone_built(M, B, w3, name)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 1, **{j: [] for j in range(4, 19)}})       # f3 = 1: in the world from the load (what dm01fix does to Wave_1)
        me = R + name
        d = top.add(M.clone('F07', sq2(KOW.FORM), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, (cell, _g, _a) in enumerate(men):
            pp = d.add(M.clone('F07', sq2(KOW.FORM + BS + 'Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, cell)                                                       # the post is the man's own place: he stays
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        short = name.split('!')[-1]
        for j, (cell, g, a) in enumerate(men):
            gr = top.add(FED.clone_built(M, B, g, 'M_%s_%02d' % (short, j + 1)))
            M.place(gr, cell, KB.rot9(*FACE))
            gr.add(FED.clone_built(M, B, a))
        paths.append(me + BS + '10_Defend')
        tops.append(top)

    squad(HOLD, [((float(B.at(g)[0]), float(B.at(g)[1]), float(B.at(g)[2])), g, g + 1) for g in grp])
    squad(FLOOR, [(c, sc.parent[acts3[j % 2]], acts3[j % 2]) for j, c in enumerate(FLOOR_CELLS)])
    squad(TOP, [(c, sc.parent[acts3[j % 2]], acts3[j % 2]) for j, c in enumerate(TOP_CELLS)])
    go = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'Go'))
    M.place(go, (0.0, 0.0, 0.0))
    M.set(go, 'TriggerDelay2', {0: float(GO_DELAY), 4: paths})
    return M, tops, R + CLOCK + BS + 'Go'


def squads(src, dst, log=print):
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + CLOCK):
        log('%s already holds %s: copied unchanged' % (src, CLOCK))
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
    main = collections.Counter(nav.part[i] for i in range(len(nav.pv)) if nav.ok[i]).most_common(1)[0][0]
    for c in FLOOR_CELLS:                                   # real cells: on the mesh at the floor, main part, room to stand
        a = nav.at(c[0], c[1], c[2], dy=60.0)
        if a is None or nav.part[a[0]] != main or nav.clearance(c[0], c[1], c[2], limit=200.0) < 50.0:
            raise ValueError('floor cell %s is not a main-part nav cell with clearance' % (c,))
    for c in TOP_CELLS:
        a = nav.at(c[0], c[1], c[2], dy=60.0)
        if a is None or nav.clearance(c[0], c[1], c[2], limit=200.0) < 50.0:
            raise ValueError('top cell %s is not a nav cell with clearance' % (c,))
    grp, pos = hold_nodes(sc)
    skip = set(grp) | set(pos)
    gone_nodes = set()
    for t in skip:
        gone_nodes.update(range(t, sc.end[t]))
    M, tops, go = make_nodes(B)
    fa_new = len(FLOOR_CELLS) + len(TOP_CELLS)                  # Hold's four are the four that left Wave_1
    if a0 + fa_new > ENGINE_ACTORS or s0 + 3 > ENGINE_SQUADS:
        raise ValueError('budget: %d / %d' % (a0 + fa_new, s0 + 3))
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm01squads', skip=skip)
    # ---- references into the removed nodes (the Wave_1 Defend rout's Pos list): cut the dead entries
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
    log('  references into the removed Wave_1 nodes: %d holders (%s), %d entries cut' % (len(dead), ', '.join(sc.names[k] for k in dead[:4]), cut))
    # ---- the AIMonitor round-start list
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [go]))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + fa_new or fs != s0 + 3 or fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    log('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
    # ---- .gms / .buf: remove, then add (new REF ids from ref_slots up, as kl_old_waves)
    slot0 = A.slots()
    gone_ents = set()
    for t in skip:
        gone_ents.update(B.ents[t - 1].walk())
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    for t in skip:
        A.remove(B.ents[t - 1])
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
    work = tempfile.mkdtemp(prefix='dm01squads_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F01_Main.zip'), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        sealed = kl_fa_bank.seal(work, log=lambda *_: None)
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        if problems:
            log('  reverify notes: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep = collections.OrderedDict(entities_before=len(B.ents), entities=len(allents), removed=len(gone_ents), added=len(order), census=[a0, s0, fa, fs],
                                  refs_cut=cut, slot_ids_moved=moved, prm_roots_repointed=repointed, sealed=sealed, members_changed=changed, go=go,
                                  reverify=problems[:5], hold=[[round(v) for v in B.at(g)[:3]] for g in grp],
                                  floor=[list(c) for c in FLOOR_CELLS], top=[list(c) for c in TOP_CELLS])
    log('  written %s: %d removed, %d added, %d slot ids renumbered, members changed: %s' % (dst, len(gone_ents), len(order), moved, ' '.join(changed)))
    return rep


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'squads':
        print(json.dumps(squads(sys.argv[2], sys.argv[3]), indent=1, default=str))
    else:
        print(__doc__)
