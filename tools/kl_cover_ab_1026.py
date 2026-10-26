#!/usr/bin/env python3
"""
COVER A/B TEST MAP (2026-10-26, workflow w4zrc2bfc follow-up, task B). OFFLINE: reads the LIVE DM05A zip, writes a staging folder
and a live-test script. Starts nothing, installs nothing.

WHY. DM05A's 61 form-a cover clones 'CoverBoxH_K6_nn' (group KL_CoverSix!, tools/kl_cover_1026.py walls() + kl_fa_cover.apply) ARE in the engine's
cover list (CFFCoverList records) but C at their stand spots gives no cover, while the stock box SO0002_M05_Facade_A_Base_01!CoverBoxH_Right_01
at (-350, 10, -2650) does (movement id 3 stand / 8 cover). The decode of 0x849700 / 0x797480 / 0x653270 found these differences between the two:
  - origin y: ours 30 (the collision floor), stock 10 (nav 20 - 10)
  - rotation: ours rot9 (-1 0 0 / 0 1 0 / 0 0 1) = heading (-1, 0), stock identity
  - model: ours 38638 (off-centre, local mid 0,100,66.77), stock 52960 (100 x 200 x 100 centred)
  - listing: ours in the ROOT room's tree 0 under KL_CoverSix!, stock in the Street room's tree 0 (room 2) as a child of the room object
This tool adds FOUR new boxes (the 61 K6 boxes stay untouched) that vary one thing at a time. They stand in front of / in the wall z = -2600 of
facade object SO0002_M05_Facade_K_Base_01 (ref 26622, wall run x -1600 .. -3765, free side -z) west of the stock facade, in open street:

    V1 'room'      K6 form (model 38638, heading (-1,0), origin y 30 like walls()), parented under the Street room object and
                   listed in ITS tree 0 (found by the .rmi point query), instead of the root group / root tree 0.
    V2 'stockcopy' exact clone of the stock control box (model 52960, identity rotation, origin y 10.001068, same props), translated;
                   child of the Street room object, listed in the Street room's tree 0 - exactly as the stock box is.
    V3 'ylow'      K6 form with origin y 10 (30 - 20 = nav - 10), in the new root group KL_CoverAB! and the root's tree 0, as the K6 boxes are.
    V4 'stockroot' V2's box, but in the root group KL_CoverAB! / the root's tree 0 (separates room-tree from model + rotation).

    python kl_cover_ab_1026.py plan                 spots + every check, nothing written
    python kl_cover_ab_1026.py stage [<root>]       <root>/DM05A/{in,mid,stage}: stage/F01_Main.zip (live bytes + the 6 changed members), install.py,
                                                    ab_plan.json, build_report.json; then COVER10.ini next to COVER9.ini (live_1026)
    python kl_cover_ab_1026.py ini                  only rewrite COVER10.ini from stage/ab_plan.json

kl_fa_cover.apply writes ONE group under the root; here two of the boxes are children of an existing deep room object, so apply() is copied
(apply_ab) with a nested adopt: the .prp join puts them as extra tops and nest() moves them to the last children of the room node (the .gms
side appends to the room entity's kids: same preorder). Slot ids are renumbered by the same remap as apply(). Checks of this tool (verify): removing
the new nodes from the new .prp gives the old .prp (fingerprints), the old entities are unchanged, every .oct item of the old build is still in the
same tree, the new ones are listed exactly once where planned, .rmi/.rmc name the same rooms, .prm differs only in .oct record offsets.

GUESSes (not measured): that the cover-list builder reads nothing but the entity's own slot (so a room parent is irrelevant there - that is what
V1/V2 test); STAND points of the K6 forms = the decoded end-50 points of K6_45 (E-158.5 / E-50 along the face, 41 in front of it); thin-air test
here uses gather 2500 (kl_fa_cover.Solid.scan drops a segment whose both ends are > gather away; the 2165-long wall is two triangles).
"""
import collections, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_scene, kl_graft
import kl_fa_bots as F
import kl_fa_cover as C
import kl_cover_add as A
import kl_cover_1026 as K
import kl_octree as O
import kl_prpjoin as J
import kl_loot_1025 as LO

GAME = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
MAP = 'DM05A'
GROUP, TAG = 'KL_CoverAB!', '_AB_'
ROOT = 'C:/kl_build_1024/cover_ab_1026'
INI9 = 'C:/kl_build_1024/live_1026/COVER9.ini'
INI10 = 'C:/kl_build_1024/live_1026/COVER10.ini'
BACKUP_TAG = '.before-1026ab'
LIVE_MD5 = '340bb7d541dbb888610896c9e8ae020e'      # pinned: the live DM05A zip this was planned on

FACE_Z = -3000.0                    # virtual face line: the boxes stand FREE in the open road (x -1175..0 has collision floor + nav; west of -1175 there is no collision floor, and facade A's wall is full) - GUESS: a wall behind the box is irrelevant to the cover list
ROOM_NAME = 'M05_A_Outside_Street_01a'
STOCK_SUFFIX = 'Facade_A_Base_01!CoverBoxH_Right_01'
K6_FORM = 'CoverBoxH_K6_45'         # the form the K6 boxes of the live zip are clones of (GUESS: kl_cover_1026 cloned a form-a box of the build)
K6_FRONT = 41.0                     # stand 41 in front of the face: COVER9's k6 spots (z -2641 on the face z -2600)
STOCK_FRONT = 91.0                  # COVER9's control: stand (-350,-2741) for the box at z -2650
# E = east end (x) of a K6-form box that runs west along the face: origin.x = E - 37.5 (heading (-1,0): local Z -> world -X, local X -> world Z),
# origin.z = FACE_Z + 37.5 (the box is 75 thick, its front on the face - exactly K6_45: origin (-437.5, -2562.5) for E = -400)
SPECS = [
    dict(v='V1', desc='room', form='k6', E=-900.0, y=30.0, where='room'),
    dict(v='V2', desc='stockcopy', form='stock', xc=-750.0, y=None, where='room'),
    dict(v='V3', desc='ylow', form='k6', E=-150.0, y=10.0, where='root'),
    dict(v='V4', desc='stockroot', form='stock', xc=-550.0, y=None, where='root'),
]


# ------------------------------------------------------------------ plan
def load(zp):
    zp = os.path.normpath(os.path.abspath(zp))
    A.use_slot(zp)
    C.GROUP, C.TAG = GROUP, TAG
    return A.Lite(zp)


def find_form(L, suffix, exact=False):
    hit = [b for b in L.boxes if (b['name'] == suffix if exact else b['name'].endswith(suffix))]
    if len(hit) != 1:
        raise ValueError('%d boxes for %s' % (len(hit), suffix))
    return hit[0]


def room_at(L, p):
    """Rooms (.rmi boxes) that hold the point p (x, y, z) -> [(volume, room entity name, room slot id)], smallest first. GUESS: the engine's choice is
    not read from kl2; the smallest box is the one a player is 'in' (the others are the huge Backdrop catch-all boxes)."""
    B = L.B
    rmi = O.RoomIndex.parse(B['.rmi'])
    t = rmi.tree
    q = [math.trunc((p[a] - t.origin[a]) * t.scale + 32768.0) for a in range(3)]
    by = {s + 2: e for e, s in B.scene.slots().items()}
    out = []
    for h in t.point(q):
        bx = rmi.boxes[h]
        half = struct.unpack_from('<3f', bx.raw, 0x40)
        out.append((abs(half[0] * half[1] * half[2]), by[bx.room].name.decode('latin1'), bx.room))
    return sorted(out)


def plan(L, log=print):
    B, sc = L.B, L.B.sc
    prm = B['.prm']
    stock = find_form(L, STOCK_SUFFIX)
    k6 = find_form(L, K6_FORM, exact=True)
    se, ke = B.ents[stock['node'] - 1], B.ents[k6['node'] - 1]
    room_k = sc.resolve(sc.path[sc.parent[stock['node']]])
    if len(room_k) != 1 or not sc.names[room_k[0]] == ROOM_NAME or sc.cls(room_k[0]) != 'ZROOM':
        raise ValueError('the stock box is not a child of %s' % ROOM_NAME)
    room_k = room_k[0]
    Rm, T = B.fr[B.ents[room_k - 1]]
    if Rm != [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]] or T != (0.0, 0.0, 0.0):
        raise ValueError('the room object is not at the origin unturned: its children are not in world coordinates')
    stock_rot = list(struct.unpack('<9f', se.rot[:36]))
    stock_y = struct.unpack('<3f', se.trans[:12])[1]
    log('stock control: node %d %s origin %s model %d flags %#x rot %s' % (stock['node'], sc.names[stock['node']], [round(v, 4) for v in B.at(stock['node'])],
                                                                           se.model, se.flags, stock_rot))
    log('K6 form: node %d %s model %d flags %#x origin %s' % (k6['node'], k6['name'], ke.model, ke.flags, [round(v, 2) for v in B.at(k6['node'])]))
    SF = K.safety_features(L)
    import kl_cover_floornav as FN
    GN = FN.Ground(L, lambda *a, **k: None)
    boxes, rows = [], []
    for sp in SPECS:
        v = sp['v']
        if sp['form'] == 'k6':
            f, model = k6, ke.model
            bb = list(struct.unpack_from('<6f', C._root(prm, model), 0x20))
            head = (-1.0, 0.0)
            y = sp['y']
            origin = [sp['E'] - 37.5, y, FACE_Z + 37.5]
            rot = F.rot9(*head)
            cx = [origin[0] + 37.5 - bb[5], origin[0] + 37.5 + 0.0]            # x range: local z -> -x
            xr = (origin[0] - bb[5], origin[0] - bb[2])
            zr = (origin[2] + bb[0], origin[2] + bb[3])
            eu, ev = xr[1] - xr[0], zr[1] - zr[0]
            mid = ((xr[0] + xr[1]) / 2, (zr[0] + zr[1]) / 2)
            stands = [('a', xr[0] + 50.0, FACE_Z - K6_FRONT), ('b', xr[1] - 50.0, FACE_Z - K6_FRONT)]
            # the K6 box tiles are 'high' boxes (height 200 > HIGH_Y[0])
        else:
            f, model = stock, se.model
            bb = list(struct.unpack_from('<6f', C._root(prm, model), 0x20))
            head = (0.0, 1.0)
            y = sp['y'] if sp['y'] is not None else stock_y
            origin = [sp['xc'], y, FACE_Z]            # box z FACE_Z-50 .. FACE_Z+50, front face 41 behind the stand at origin z - 91 (reviewed 10-26: was FACE_Z-50 with the stand INSIDE the box)
            rot = stock_rot
            xr = (origin[0] + bb[0], origin[0] + bb[3])
            zr = (origin[2] + bb[2], origin[2] + bb[5])
            eu, ev = xr[1] - xr[0], zr[1] - zr[0]
            mid = ((xr[0] + xr[1]) / 2, (zr[0] + zr[1]) / 2)
            # STOCK_FRONT (91) is measured from the box ORIGIN (control: origin z -2650, stand -2741), so the stand is 41 in front of the box's front face
            # (reviewed 10-26: the first stage had FACE_Z - 91 = -3091, which is INSIDE the box z -3100..-3000)
            stands = [('', sp['xc'], origin[2] - STOCK_FRONT)]
        box = dict(v=v, desc=sp['desc'], name='CoverBoxH_AB_%s' % v, kind='high', where=sp['where'], origin=[round(o, 4) for o in origin], head=list(head),
                   rot=rot, model=model, form_node=f['node'], tier='a', borrowed=None, via='ab', bb=bb, ext=[round(eu, 2), round(ev, 2)],
                   mid=[round(mid[0], 2), round(origin[1] + (bb[1] + bb[4]) / 2, 2), round(mid[1], 2)], xr=[round(xr[0], 2), round(xr[1], 2)],
                   zr=[round(zr[0], 2), round(zr[1], 2)], stands=[[s[0], round(s[1], 2), round(s[2], 2)] for s in stands])
        # --- checks (the generator's own rules on these spots)
        n, u = (0.0, -1.0), (1.0, 0.0)
        gy = 30.0
        why = []
        for lab, sx, sz in stands:
            if L.nav.at(sx, 20.0, sz, dy=70.0) is None:
                why.append('no nav at stand %s' % lab)
            fl = L.solid.floor(sx, gy, sz)
            if fl is None or abs(fl - gy) > 5:
                why.append('collision floor at stand %s = %s' % (lab, fl))
            for dz in (-60, -120):                                   # room to move: nav 60 and 120 further out
                if L.nav.at(sx, 20.0, sz + dz, dy=70.0) is None:
                    why.append('no nav %d behind stand %s' % (-dz, lab))
        for fx in (xr[0], mid[0], xr[1]):                          # floor + nav under and in front of the whole box
            for fz in (FACE_Z - 40.0, FACE_Z + 40.0):
                if L.nav.at(fx, 20.0, fz, dy=70.0) is None or L.solid.floor(fx, gy, fz) is None:
                    why.append('no floor / nav at x=%.0f z=%.0f' % (fx, fz))
        if not A._free(L, (mid[0], origin[1] + 100.0, mid[1]), origin[1] + 100.0, [b for b in boxes]):
            why.append('has cover / crowded (a box within APART)')
        for b in boxes:
            if (xr[0] < b['xr'][1] + 100 and xr[1] > b['xr'][0] - 100):
                why.append('too near %s' % b['name'])
        foot = [(x, gy + 50.0, z) for x in xr for z in zr] + [(mid[0], gy + 50.0, mid[1])]
        if any(B.in_box(k_, q) for k_ in L.nocover for q in foot):
            why.append('NoCoverBox')
        if L.exits and any(F.in_exit(B, L.exits, q) for q in foot):
            why.append('exit box')
        if L.lane and min(F.lane_dist(L.lane, q) for q in foot) < F.LANE_CLEAR:
            why.append('escape road')
        bad = K._tile_unsafe(L, SF, mid, gy, n, u, eu, ev, (stands[0][1], gy, stands[0][2]))
        if bad:
            why.append('safety: ' + bad)
        bad = GN.tile_bad((mid[0], FACE_Z), n, gy)
        if bad:
            why.append('floornav: ' + bad)
        rooms = room_at(L, (mid[0], gy + 50.0, mid[1]))
        rs = room_at(L, (stands[0][1], gy + 50.0, stands[0][2]))
        box['rooms_at_box'] = [r[1] for r in rooms]
        box['rooms_at_stand'] = [r[1] for r in rs]
        box['room_name'] = rooms[0][1] if rooms else None
        if sp['where'] == 'room' and (not rooms or rooms[0][1] != ROOM_NAME):
            why.append('the smallest room box at the box is %s, not %s' % (rooms[0][1] if rooms else None, ROOM_NAME))
        box['problems'] = why
        boxes.append(box)
        rows.append(box)
        log('%s %-9s box x %s z %s origin %s mid %s model %d rot %s where %s | room(s) %s | stands %s | %s' % (
            v, sp['desc'], box['xr'], box['zr'], box['origin'], box['mid'], model, [round(r_, 1) for r_ in rot], sp['where'], box['rooms_at_box'][:2],
            box['stands'], 'OK' if not why else 'PROBLEMS: ' + '; '.join(why)))
    P = collections.OrderedDict(folder=L.folder, group=GROUP, room_node=room_k, stock_node=stock['node'], k6_node=k6['node'], boxes=boxes)
    if any(b['problems'] for b in boxes):
        raise SystemExit('plan has problems; see above')
    return P


# ------------------------------------------------------------------ apply
def nest(Jn, count, room_k, base_end):
    """The last `count` top-level nodes of the joined scene Jn (leaves) become the LAST children of node room_k of the base (base_end = the preorder
    index where room_k's subtree ends in the base). -> a new kl_prpjoin.Scene (kl_prpjoin.join has `adopt` for top-level nodes only)."""
    P = Jn.p
    ds, st = [], [P.root]
    while st:
        n = st.pop()
        ds.append(n)
        st.extend(reversed(n['children']))
    if len(ds) != len(Jn.nodes):
        raise ValueError('nest: node count')
    kids = P.root['children'][-count:]
    del P.root['children'][-count:]
    if any(k['children'] for k in kids):
        raise ValueError('nest: a moved node has children')
    ds[room_k]['children'].extend(kids)
    names, tids, origin = list(Jn.names), list(Jn.tids), list(Jn.origin)
    t = len(names) - count
    mv = (names[t:], tids[t:], origin[t:])
    del names[t:], tids[t:], origin[t:]
    names[base_end:base_end] = mv[0]
    tids[base_end:base_end] = mv[1]
    origin[base_end:base_end] = mv[2]
    out = J.Scene(P, names, tids, Jn.game, Jn.label)
    out.origin = origin
    return out


def apply_ab(L, P, dst, log=print):
    """kl_fa_cover.apply for boxes that may be children of an existing room object (copy of it; see the module docstring)."""
    B, sc = L.B, L.B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    before = F.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']
    room_k = P['room_node']
    room_ent = B.ents[room_k - 1]
    ents0, ro = kl_graft.rooms_of(B.scene)
    if len(ro) != len(octx.rooms) or room_ent not in ro:
        raise ValueError('room order does not match the .oct room sets')
    ri = ro.index(room_ent)
    stock_ent = B.ents[P['stock_node'] - 1]
    sid0 = B.scene.slots()
    if sid0[stock_ent] + 2 not in {it[0] for it in octx.rooms[ri][0].items}:
        raise ValueError('the stock control box is not in the Street room\'s tree 0 (room %d)' % ri)

    M = F.Maker()
    gk = C.group_form(B)
    grp = C._node(M, B, gk, GROUP)
    M.place(grp, (0.0, 0.0, 0.0))
    room_nodes, root_nodes = [], []
    for c in P['boxes']:
        n = C._node(M, B, c['form_node'], c['name'])
        if c['where'] == 'root':
            grp.add(n)
        M.place(n, c['origin'], c['rot'])
        if n.model != c['model'] or n.links is not None or n.flags != 0x302:
            raise ValueError('%s: not the form that was planned' % c['name'])
        (root_nodes if c['where'] == 'root' else room_nodes).append((c, n))
    tops = [grp] + [n for _c, n in room_nodes]
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'cover-ab')
    Jn = nest(Jn, len(room_nodes), room_k, sc.end[room_k])
    data = Jn.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    A_ = B.scene
    slot0 = A_.slots()
    nxt = max([A_.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made = nxt, {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A_.roots).append(e)
        made[id(n)] = e
        for k in n.kids:
            ent(k, e)
    ent(grp, None)
    for _c, n in room_nodes:
        ent(n, room_ent)
    A_.ref_slots = nxt
    faults = A_.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A_.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A_.write()
    slot1 = A_.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)

    def item(c, n):
        cs = C.box_corners(dict(c, bb=c['bb']))
        return (slot1[made[id(n)]] + 2, tuple(min(p[a] for p in cs) for a in range(3)), tuple(max(p[a] for p in cs) for a in range(3)))
    root3, root0 = octn.rooms[0][3], octn.rooms[0][0]
    if root0 is None or root3 is None or slot0[B.ents[gk - 1]] + 2 not in {it[0] for it in octx.rooms[0][3].items}:
        raise ValueError('the root has no tree 0 / 3, or the group form is not listed in the root\'s group tree')
    items0 = [item(c, n) for c, n in root_nodes]
    itemsR = [item(c, n) for c, n in room_nodes]
    if items0:
        octn.rooms[0][0] = O.join_trees(root0, C._tree(items0))
        octn.rooms[0][0].check()
    if itemsR:
        if octn.rooms[ri][0] is None:
            raise ValueError('the room has no tree 0')
        octn.rooms[ri][0] = O.join_trees(octn.rooms[ri][0], C._tree(itemsR))
        octn.rooms[ri][0].check()
    cs = [p for c, _n in root_nodes for p in C.box_corners(c)]
    lo = tuple(min(p[a] for p in cs) - 10.0 for a in range(3))
    hi = tuple(max(p[a] for p in cs) + 10.0 for a in range(3))
    octn.rooms[0][3] = O.join_trees(root3, C._tree([(slot1[made[id(grp)]] + 2, lo, hi)]))
    octn.rooms[0][3].check()
    new_prm, repointed = None, 0
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    if move:
        pm = bytearray(prm)
        t, n = struct.unpack_from('<II', pm, 0)
        old = set(octx.record_refs())
        for i in range(1, n):
            o, size = struct.unpack_from('<II', pm, t + 16 * i)
            if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(pm)
    post = F.room_sets_check(A_, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'cover.', 'cover_map')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    rep = collections.OrderedDict(
        source=B.folder, out=dst, members_changed=changed, entities_before=len(B.ents), entities=len(ents), entities_added=len(order),
        group=GROUP, room_index=ri, room=ROOM_NAME, ref_ids='%d..%d' % (ref0, nxt - 1), ref_slots=[B.scene.ref_slots, nxt], slot_ids_moved=moved,
        prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post,
        listed_in_root_tree_0=[c['name'] for c, _n in root_nodes], listed_in_room_tree_0=[c['name'] for c, _n in room_nodes],
        big_before=before, big_after=after)
    log('written %s: %d entities added (%s group + %d under it, %d under the room), REF ids %s; members changed: %s; %d slot ids renumbered; %d model roots re-pointed'
        % (zp, len(order), GROUP, len(root_nodes), len(room_nodes), rep['ref_ids'], ' '.join(changed), moved, repointed))
    if before != after:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    return rep


# ------------------------------------------------------------------ verify
def verify(src, dst, P, log=print):
    """Old zip vs new zip -> list of problems (must be empty)."""
    bad = []
    A0, A1 = F.Built(src), F.Built(dst)
    s0, s1 = A0.sc, A1.sc
    new_names = {b['name'] for b in P['boxes']} | {GROUP}
    newk = [k for k in range(1, len(s1.nodes)) if s1.names[k] in new_names]
    if len(newk) != 1 + len(P['boxes']):
        bad.append('%d new nodes, expected %d' % (len(newk), 1 + len(P['boxes'])))
    # .prp: without the new nodes it is the old tree
    red = J.join(s1, [(s1, t) for t in s1.tops() if s1.names[t] != GROUP], 'reduced', skip=set(newk))
    if J.fingerprints(red)[0] != J.fingerprints(s0)[0] or J.text(red, red.p.settings) != J.text(s0, s0.p.settings):
        bad.append('.prp: without the new nodes the tree is not the old one')
    # .gms: old entities unchanged (by REF label), new ones appended behind their parent
    key = lambda e: (e.name, e.tid, e.flags, e.group, e.model, e.rot, e.trans, e.raw, e.aux, e.ref)
    new_e = [e for e in A1.ents if e.name.decode('latin1') in new_names]
    old_e = [e for e in A1.ents if e.name.decode('latin1') not in new_names]
    if [key(e) for e in old_e] != [key(e) for e in A0.ents]:
        bad.append('.gms: an old entity differs (record, order or REF id)')
    refs = [e.ref for e in A1.ents]
    if len(set(refs)) != len(refs) or max(refs) >= A1.scene.ref_slots:
        bad.append('.gms: two entities share a REF id, or one is over the REF slot count')
    if (A0.scene.head, A0.scene.tail, A0.scene.dyn, A0.scene.tags, A0.scene.budget, A0.scene.fdx, A0.scene.nav) != \
            (A1.scene.head, A1.scene.tail, A1.scene.dyn, A1.scene.tags, A1.scene.budget, A1.scene.fdx, A1.scene.nav):
        bad.append('.buf head / tail / dynamic list / tags / budget / FDX / navigation mesh differ')
    # each new box: parent, flags, model, place, rotation
    want = {b['name']: b for b in P['boxes']}
    for k in newk:
        nm = s1.names[k]
        if nm == GROUP:
            continue
        b = want[nm]
        e = A1.ents[k - 1]
        par = s1.names[s1.parent[k]]
        exp_par = GROUP if b['where'] == 'root' else ROOM_NAME
        if par != exp_par:
            bad.append('%s: parent %s, expected %s' % (nm, par, exp_par))
        if e.flags != 0x302 or e.model != b['model']:
            bad.append('%s: flags %#x model %d' % (nm, e.flags, e.model))
        v = A1.values(k)
        if list(v['ZGEOM[2]']) != list(struct.unpack('<3f', e.trans[:12])) or list(v['ZGEOM[1]']) != list(struct.unpack('<9f', e.rot[:36])):
            bad.append('%s: .prp and .gms disagree on its place' % nm)
        if [round(x, 3) for x in struct.unpack('<3f', e.trans[:12])] != [round(x, 3) for x in b['origin']]:
            bad.append('%s: origin %s, planned %s' % (nm, struct.unpack('<3f', e.trans[:12]), b['origin']))
        ob = A1.at(k)
        if math.dist(ob, b['origin']) > 0.01:
            bad.append('%s: world place %s differs from the plan' % (nm, ob))
        # same props as the form it was cloned from, except place + rotation
        f0 = [kk for kk in range(1, len(s1.nodes)) if s1.names[kk] == (K6_FORM if b['form_node'] == P['k6_node'] else s1.names[P['stock_node'] + 0 * kk])]
        src_k = b['form_node'] if b['form_node'] <= len(s0.nodes) else None
    # .oct / .rmi / .rmc
    o0, o1 = O.Oct.parse(A0['.oct']), O.Oct.parse(A1['.oct'])
    by0 = {s + 2: e for e, s in A0.scene.slots().items()}
    by1 = {s + 2: e for e, s in A1.scene.slots().items()}
    if len(o0.rooms) != len(o1.rooms):
        bad.append('.oct: room set count differs')
    ents1 = {e.ref: e for e in A1.ents}
    new_refs = {e.ref for e in new_e}
    listed_new = collections.defaultdict(list)
    for r, (ra, rb) in enumerate(zip(o0.rooms, o1.rooms)):
        for t, (x, y) in enumerate(zip(ra, rb)):
            ia = collections.Counter(by0[it[0]].ref for it in (x.items if x else ()))
            ib = collections.Counter(by1[it[0]].ref for it in (y.items if y else ()))
            extra = ib - ia
            if ia - ib:
                bad.append('.oct: room %d tree %d lost items' % (r, t))
            for ref, n in extra.items():
                if ref in new_refs:
                    listed_new[ref].append((r, t))
                elif t == 3 and r == 0:
                    pass
                else:
                    bad.append('.oct: room %d tree %d gained an old entity %d' % (r, t, ref))
            if not x and not y:
                continue
            if x and y and ia == ib:
                continue
    _, ro1 = kl_graft.rooms_of(A1.scene)
    ri = ro1.index(A1.ents[[k for k in range(1, len(s1.nodes)) if s1.names[k] == ROOM_NAME][0] - 1])
    for b in P['boxes']:
        e = [e for e in new_e if e.name.decode('latin1') == b['name']][0]
        got = listed_new.get(e.ref, [])
        exp = [(0, 0)] if b['where'] == 'root' else [(ri, 0)]
        if got != exp:
            bad.append('%s: listed in %s, expected %s' % (b['name'], got, exp))
    g = [e for e in new_e if e.name.decode('latin1') == GROUP][0]
    if listed_new.get(g.ref, []) != [(0, 3)]:
        bad.append('%s group listed in %s, expected the root\'s tree 3' % (GROUP, listed_new.get(g.ref)))
    for nm, ext in (('.rmi', '.rmi'), ('.rmc', '.rmc')):
        a = [(b.raw[:0x4c], by0[b.room].ref, by0[b.second].ref if b.second else 0) for b in O.RoomIndex.parse(A0[ext]).boxes]
        c = [(b.raw[:0x4c], by1[b.room].ref, by1[b.second].ref if b.second else 0) for b in O.RoomIndex.parse(A1[ext]).boxes]
        if a != c:
            bad.append('%s: boxes name other rooms' % nm)
    if [r.pack() for r in o0.records] != [r.pack() for r in o1.records] or o0.tail != o1.tail:
        bad.append('.oct collision records or tail differ')
    # .prm: only record offsets
    p0, p1 = A0['.prm'], A1['.prm']
    if p0 != p1:
        if len(p0) != len(p1):
            bad.append('.prm: size differs')
        else:
            mv = dict(zip(o0.record_refs(), o1.record_refs()))
            t, cnt = struct.unpack_from('<II', p0, 0)
            spans = 0
            for i in range(1, cnt):
                o, size = struct.unpack_from('<II', p0, t + 16 * i)
                if p0[o:o + size] != p1[o:o + size]:
                    va, vb = struct.unpack_from('<I', p0, o + 0x1c)[0], struct.unpack_from('<I', p1, o + 0x1c)[0]
                    if size != 64 or p0[o:o + 0x1c] != p1[o:o + 0x1c] or p0[o + 0x20:o + 64] != p1[o + 0x20:o + 64] or mv.get(va) != vb:
                        spans += 1
            if spans or p0[t:] != p1[t:] or p0[:16] != p1[:16]:
                bad.append('.prm: %d chunks differ in more than their .oct record offset' % spans)
    rest = [e for e in A0.ext if e not in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm') and A0[e] != A1[e]]
    if rest or A0.order != A1.order:
        bad.append('other members differ: %s' % rest)
    for x in bad:
        log('UNEXPECTED: ' + x)
    log('VERIFY: %s' % ('PASS (only the 4 boxes and the group were added; old data equal)' if not bad else '%d problems' % len(bad)))
    return bad


# ------------------------------------------------------------------ live test script
def ini_block(label, desc, gx, gz_front, face_x, stand_z):
    """The block COVER9 uses for one stand spot (goto 40 short of the spot, then to it, face +z, peek, C, peek)."""
    g = lambda v: ('%g' % v)
    return [
        'log === %s: %s; stand (%s,%s) facing +z ===' % (label, desc, g(gx), g(stand_z)),
        'goto %s %s 60 40000' % (g(gx), g(stand_z - 40)),
        'goto %s %s 20 15000 keep' % (g(gx), g(stand_z)),
        'face %s -2400 6 4000' % g(face_x if face_x is not None else gx),
        'up W',
        'wait 800',
        'pos %s-at-stand' % label,
        'peek 0xdd265c+828+6b4+44 %s-0-before-C-movement-id(3=stand,8=cover)' % label,
        'tap C 400',
        'wait 1500',
        'peek 0xdd265c+828+6b4+44 %s-1-after-C-movement-id' % label,
        'peek 0xdd265c+828+2954 %s-1-cover-side' % label,
        'peek 0xdd265c+828+818 %s-1-flags-bit80-incover' % label,
        'pos %s-after-C' % label,
        'log %s: SHOT NOW' % label,
        'wait 1500',
        'tap C 400',
        'wait 1200',
    ]


def write_ini(plan_json, out=INI10, src=INI9, log=print):
    boxes = json.load(open(plan_json))['boxes']
    lines = open(src, encoding='latin-1').read().split('\n')
    at = lines.index('[Script]')
    head = lines[:at]
    head[0] = '; COVER10 (2026-10-26): cover A/B on DM05A - 4 new boxes CoverBoxH_AB_V1..V4 beside the 61 K6 boxes (tools/kl_cover_ab_1026.py). Generated from COVER9.ini.'
    scr = [l for l in lines[at + 1:] if l.strip() and not l.startswith('[')]
    cd = head.index('[CoverDump]')           # explicit keys for the 10-26 klcoverdump.c stage 5 / finder (TEST default is 1 anyway)
    head[cd + 1:cd + 1] = ['FullRecords=1   ; (recommended on for test runs, off for players)', 'Finder=1   ; (recommended on for test runs, off for players)', 'FinderMax=400']
    tail_start = next(i for i, l in enumerate(lines[at + 1:], at + 1) if l.startswith('[') and l != '[Script]') if any(l.startswith('[') for l in lines[at + 1:]) else len(lines)
    tail = lines[tail_start:]
    s = []
    for l in lines[at + 1:tail_start]:
        if not l.strip():
            continue
        s.append(l.split('=', 1)[1])
    # steps 1-34 (menu walk, level select) are COVER9's as they are; the log line and the checks after the load are rewritten
    cut = next(i for i, l in enumerate(s) if l.startswith('log COVER9: DM05A'))
    out_s = s[:cut]
    out_s.append('log COVER10: DM05A (Last Call, F01 slot) - [CoverDump] run with 4 A/B boxes CoverBoxH_AB_V1..V4: load, idle, then the stock control and each V1..V4 stand spot (goto, face +z, peek movement id, C, peek). Read-only. Expect coverlist records ~267 (263 + 4)')
    load_i = next(i for i, l in enumerate(s) if l.startswith('msg HeistLevel_P3 StartGame'))
    out_s += s[cut + 1:load_i + 1]
    out_s += s[load_i + 1:next(i for i, l in enumerate(s) if l.startswith('ents KL_CoverSix'))]
    out_s += ['ents KL_CoverAB 8', 'ents CoverBoxH_AB_V 8', 'ents CoverBoxH_K6_45 3',
              'log === COVER10: idle 25 s at the spawn (coverdump dumps after the list is stable 2 s) ===', 'wait 25000', 'pos idle-end']
    out_s += ini_block('ctl', 'STOCK SO0002 CoverBoxH_Right_01 (form a, worked in COVER8/9)', -350, 0, None, -2741)
    out_s[-18] = out_s[-18].replace('goto -350 -2781 60 40000', 'goto -350 -2781 60 40000')
    out_s += ['log ctl: SHOT NOW'] if False else []
    exp = {'V1': 'expect FAIL like K6 if room tree/parent is not the cause; PASS if it is',
           'V2': 'expect PASS (movement 8) if it is a clone of the control; FAIL means position/facade/room matters',
           'V3': 'expect PASS if origin y 30 vs 10 is the cause',
           'V4': 'expect PASS if model+rotation+y of the stock box is all that matters; FAIL with V2 PASS = the room tree/parent'}
    for b in boxes:
        for lab, sx, sz in b['stands']:
            label = (b['v'] + lab).lower()
            out_s += ini_block(label, 'OUR %s (%s: model %d, origin %s, %s); stand point %s; %s' % (b['name'], b['desc'], b['model'], b['origin'], b['where'], lab or 'middle', exp[b['v']]),
                               sx, 0, sx, sz)
    out_s.append('log COVER10 DONE')
    out_s.append('pass 1000')
    body = ['[Script]'] + ['%d=%s' % (i + 1, l) for i, l in enumerate(out_s)]
    with open(out, 'w', encoding='latin-1', newline='\n') as f:
        f.write('\n'.join(head + body + [''] + tail))
    log('wrote %s: %d script lines' % (out, len(out_s)))


# ------------------------------------------------------------------ stage
INSTALL_PY = LO.INSTALL_PY.replace('loot-placement', 'cover A/B test (CoverBoxH_AB_V1..V4)').replace('tools/kl_loot_1025.py', 'tools/kl_cover_ab_1026.py')


def stage(root, log=print):
    live = os.path.join(GAME, 'KLExpansion', 'Maps', MAP, 'F01_Main.zip')
    h = LO.md5(live)
    if h != LIVE_MD5:
        raise SystemExit('REFUSED: the live %s is md5 %s, this tool was planned on %s' % (live, h, LIVE_MD5))
    d = os.path.join(root, MAP)
    for sub in ('in', 'mid', 'stage'):
        LO.rmtree(os.path.join(d, sub))
        os.makedirs(os.path.join(d, sub))
    src = os.path.join(d, 'in', 'F01_Main.zip')
    shutil.copyfile(live, src)
    for f in os.listdir(os.path.dirname(live)):
        if f.lower().endswith('.ini'):
            shutil.copyfile(os.path.join(os.path.dirname(live), f), os.path.join(d, 'in', f))
    L = load(src)
    P = plan(L, log)
    mid = os.path.join(d, 'mid')
    rep = apply_ab(L, P, mid, log)
    bad = verify(src, os.path.join(mid, 'F01_Main.zip'), P, log)
    if bad:
        raise SystemExit('verify failed')
    with zipfile.ZipFile(os.path.join(mid, 'F01_Main.zip')) as z, zipfile.ZipFile(src) as a:
        repl = {i.filename: z.read(i.filename) for i in a.infolist() if z.read(i.filename) != a.read(i.filename)}
    final = os.path.join(d, 'stage', 'F01_Main.zip')
    LO.patch_zip(src, final, repl)
    h2 = LO.md5(final)
    bad = verify(src, final, P, log)                                   # (the patched live bytes, not the rewritten zip)
    if bad:
        raise SystemExit('verify of the patched zip failed')
    with open(os.path.join(d, 'stage', 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=MAP, zip='F01_Main.zip', tag=BACKUP_TAG, game=GAME, old=h, new=h2))
    for b in P['boxes']:
        b['rot'] = [float(v) for v in b['rot']]
    plan_json = os.path.join(d, 'stage', 'ab_plan.json')
    with open(plan_json, 'w') as fh:
        json.dump(dict(P, boxes=P['boxes']), fh, indent=1, default=str)
    rep2 = dict(rep, map=MAP, md5_in=h, md5_out=h2, members_patched=sorted(n.rsplit('_Main', 1)[-1] for n in repl), tag=BACKUP_TAG)
    with open(os.path.join(d, 'stage', 'build_report.json'), 'w') as fh:
        json.dump(rep2, fh, indent=1, default=str)
    LO.rmtree(mid)
    log('STAGED %s md5 %s -> %s (members %s)' % (final, h[:8], h2, rep2['members_patched']))
    write_ini(plan_json, log=log)
    return rep2


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == 'plan':
        live = os.path.join(GAME, 'KLExpansion', 'Maps', MAP, 'F01_Main.zip')
        d = os.path.join(ROOT, MAP, 'in')
        src = os.path.join(d, 'F01_Main.zip')
        if not os.path.isfile(src):
            os.makedirs(d, exist_ok=True)
            shutil.copyfile(live, src)
        plan(load(src))
        return 0
    if a[0] == 'stage':
        stage(a[1] if len(a) > 1 else ROOT)
        return 0
    if a[0] == 'ini':
        write_ini(os.path.join(ROOT, MAP, 'stage', 'ab_plan.json'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
