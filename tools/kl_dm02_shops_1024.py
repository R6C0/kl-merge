"""kl_dm02_shops_1024.py - DATA pass for the Mall (DM02, F02 slot): more open shops with loot and co-op "lift shutters" with loot behind.
Written 2026-10-24 (kl-merge workflow wf_dd55429a, offline only). Reads a BUILT F02_Main.zip, writes a copy. Nothing imports it.
(owner request: "more open shops with loot and co-op lift shutters (like DD F04/F06 airlock shutter) with loot behind")

WHAT IT ADDS (one new top-level group 'KL_Shops!', all of it clones of nodes that already exist)
  1. LOOT: per shop one or two counter-and-cash-drawer sets: a clone of DM02's own 'PC0406_M02_FA_Montre_Desk_01' (the counter) and of the
     'PC0406_M02_FA_Cashdrawer_01' group (7 entities: collision box, drawer, sound, money container 'Money_Attachroot' with its
     OnlineMoneyCtrl, the 'Cashbox' with its own proximity 'Open' trigger, map icon) of the 'StoreWatch' shop. Every path inside the clone's
     controllers is rewritten to the clone ('ROOT\\KL_Shops!\\KLShopNN_Cashdrawer\\...'), nothing points at the original.
     Loot rules (re/bots_loot.md): the amount is set per shop; OnlineMoneyCtrl field 11 ('behind a door') = 1, so the AI heisters pass the
     object over unless an enabled KickDoor is within 500/250 (there is none); the shops are off the nav mesh anyway (report below).
     The level's loot total grows by the amounts; the bots' own total (TriggerLootDepleted waits on the bots' amount) is untouched.
  2. SHUTTER FRONTAGES: DM02 has 12 roller shutters 'SI0401_M02_FA_RollerShutterA_nn' (each ONE static HVK shape type 1 = what
     DeactivateGeom removes; the same mechanism as kl_hc2_garagedoor). Variant A opens two of them at the round start and makes three
     of them CO-OP shutters; variant B (the fallback) opens all five at the round start and adds no co-op node at all.
  3. CO-OP CONTROL SET (variant A only): a clone of Dog Days' own airlock set 'SI0100_F04_Coop_Move_Dxxr_04!' of stock F04 (Outside_LootHall):
     Controller (CoopAirlock), the two arrows and the two boxes (the places the two players have to stand on), PathBlocker, and a
     DeactivateGeom node (clone of F04's GeomDeactivator_shake_area) that takes the shutter off. The set is turned into the shutter's frame
     (F04's door spans its local Z, the DM02 shutter its local X: a 90 degree turn about Y, the door middle on the shutter's middle).
     The CoopAirlock's completion list (field 23) = [PathBlocker, the shutter's DeactivateGeom]; field 24 (CoverStateChanger 'AllCovers')
     is emptied: it would switch every cover of the map.
  4. ROUND START: a TriggerDelay2 (clone of the map's own Timer_start_bots) + a DeactivateGeom for the always-open frontages, the timer
     appended to AIMonitor field 2 (the list that already holds Timer_start_bots, ReinforcementsTimer, ...).

WHAT IT DOES NOT DO (the full leaf-model graft was proven infeasible offline, re/dm02_shops_1024.md): F04's two door leaves (models 19438
and 19452, MatPosAnim, ~218 x 218) cannot stand in a 640 x 331 frontage without a 32-chunk .prm append, a MAT/TEX merge, an hvk donor join
and a .buf key-block transplant that no tool of this repo does and nothing offline can validate. So the co-op shutter is the DM02 shutter
model itself; the F04 CONTROL SET drives its removal. GUESSES (each also in a code comment): that the CoopAirlock runs without its
MatPosAnimProxy and leaves, that DeactivateGeom is a valid 'completion list' target, that clones at the root render, the corridors
behind the shutters are dark and off the nav mesh, the cloned counters have no HVK collision (they are walk-through).

Usage (from tools/):
  python kl_dm02_shops_1024.py build <in F02_Main.zip> <out folder> [--variant A|B|both] [--force]
  python kl_dm02_shops_1024.py stage <in F02_Main.zip> <out folder> --rehearse <scratch>     both variants, md5-chained INSTALL/UNDO
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as F
import kl_fa_cover as C
import kl_octree as O
import kl_prpjoin as J
from kl_prp import units

SRC_MD5 = 'bb6fc9e0d5926f943c8ba1bf41bde649'      # the live DM02 zip this was built and checked on (2026-10-24)
GROUP = 'KL_Shops!'
TAG = '.before-1024shops'
ROOMS = 'M02_FA_A_Ins_StoreWatch_201a\\'
DESK_TAIL = ROOMS + 'PC0406_M02_FA_Montre_Desk_01'
DRAWER_TAIL = ROOMS + 'PC0406_M02_FA_Cashdrawer_01'
SHUTTER_TAIL = 'SI0401_M02_FA_RollerShutterA_'
F04_PREFIX = 'F04_Outside_LootHall\\SI0100_F04_Coop_Move_Dxxr_04!'
SPAN = 640.0                                      # the shutter's model: x 0..640 (spans local x), thickness along local z
# the five frontages (world position of the shutter node). coop = a co-op shutter in variant A; sets = counter+drawer sets behind it;
# amount = OnlineMoneyCtrl field 1 of each set. Shops 1..3 are the floor-2 corridors east/west (1000 deep x 600 wide, 'Corridore_201x').
SHOPS = [dict(at=(-1990.0, 500.0, 1032.0), coop=True, sets=2, amount=150000),
         dict(at=(1990.0, 500.0, 1660.0), coop=True, sets=2, amount=150000),
         dict(at=(1990.0, 500.0, -2033.0), coop=True, sets=2, amount=150000),
         dict(at=(-1990.0, 500.0, -2665.0), coop=False, sets=1, amount=80000),
         dict(at=(-1990.0, 0.0, 1032.0), coop=False, sets=1, amount=80000)]
LATERAL = {1: (320.0,), 2: (170.0, 470.0)}        # along the shutter's span from its origin (the span is 0..640)
DEPTH = 520.0                                     # into the shop, from the shutter plane
OPEN_DELAY = 1.0                                  # seconds after the round start
F04_DOOR_MID = None                               # computed from F04's two leaves
COOP_PARTS = (('Controller', 'Controller'), ('CoopAirLock_ArrowBegin_A_00', 'ArrowBegin_A'), ('CoopAirLock_ArrowBegin_B_00', 'ArrowBegin_B'),
              ('CoopAirLock_Box_A_00', 'Box_A'), ('CoopAirLock_Box_B_00', 'Box_B'), ('CoopAirLock_Pathblocker_00', 'Pathblocker'),
              ('GeomDeactivator_shake_area', 'Open'))


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ 3x3 maths (columns of a matrix = the images of local x, y, z)
def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def tr(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


def mv(A, v):
    return [sum(A[i][j] * v[j] for j in range(3)) for i in range(3)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def cols(a, b, c):
    return [[a[i], b[i], c[i]] for i in range(3)]


def col(R, j):
    return [R[i][j] for i in range(3)]


def stored(R):
    """ZGEOM[1] of a frame whose columns are R (kl_fa_bots.frames reads the 9 floats as rows Z, Y, X and transposes)."""
    return [R[0][2], R[1][2], R[2][2], R[0][1], R[1][1], R[2][1], R[0][0], R[1][0], R[2][0]]


def snap(v):
    """A horizontal direction of the shutters is an axis: 0 / +-1 (kills float dust)."""
    return [float(round(x)) for x in v]


EY = [0.0, 1.0, 0.0]


# ------------------------------------------------------------------ node helpers
def own(M, B, k, name, with_ctrls=True):
    """A clone of a node of THIS build (cover._node drops the controllers; these need theirs)."""
    sc, n, e = B.sc, B.sc.nodes[k], B.ents[k - 1]
    ctrls = [(M.adopt([nm], sc.p.keys)[0], M.adopt(body, sc.p.keys)) for nm, body in n['ctrls']] if with_ctrls else []
    node = F.Node(name, sc.tids[k], M.adopt(n['props'], sc.p.keys), ctrls, e)
    node.model = e.model
    node.raw = e.raw                                  # the 64-byte KEYS block of the drawer parts (same map: valid as is)
    return node


def remap(M, node, fn):
    """Rewrite every path string of the node's controllers: fn(str) -> new str, '' for a scalar / None in a list to drop it."""
    out = []
    for nm, body in node.ctrls:
        us = [list(u) for u in units(body[1:-1])]
        for u in us:
            op = u[0][0]
            if op in (0x0c, 0x0e):
                s = M.p.key(u[0])
                t = fn(s)
                if t is None:
                    t = ''
                if t != s:
                    u[:] = [(op, struct.pack('<I', M.p.key_index(t)))]
            elif op == 0x04 and not (len(u) > 1 and u[1][0] == 0x0d):
                strs = [M.p.key(t) for t in u[1:]]
                new = [fn(s) for s in strs]
                if new != strs:
                    new = [s for s in new if s is not None]
                    u[:] = [(0x04, struct.pack('<I', len(new)))] + [(0x0c, struct.pack('<I', M.p.key_index(s))) for s in new]
        out.append((nm, [body[0]] + [t for u in us for t in u] + [body[-1]]))
    node.ctrls = out


def find(B, tail, exact_end=True):
    hit = [k for k in range(1, len(B.sc.names)) if B.sc.path[k] and B.sc.path[k].endswith('\\' + tail)]
    if len(hit) != 1:
        raise ValueError('%d nodes end in %s (this is not DM02)' % (len(hit), tail))
    return hit[0]


def kids_of(B, k):
    e = B.ents[k - 1]
    return [j for j in range(k + 1, B.sc.end[k]) if B.ents[j - 1].parent is e]


def shutter_nodes(B):
    out = []
    for k in range(1, len(B.sc.names)):
        p = B.sc.path[k]
        if p and SHUTTER_TAIL in p.rsplit('\\', 1)[-1]:
            out.append(k)
    return out


def shutter_at(B, at):
    hit = [k for k in shutter_nodes(B) if max(abs(B.at(k)[i] - at[i]) for i in range(3)) < 1.0]
    if len(hit) != 1:
        raise ValueError('%d shutters at %s' % (len(hit), at))
    return hit[0]


def shutter_frame(B, k):
    """-> (origin, x_s, z_s): the span axis and the thickness axis (into the shop) of a shutter, snapped to the axes."""
    R, T = B.fr[B.ents[k - 1]]
    return T, snap(col(R, 0)), snap(col(R, 2))


# ------------------------------------------------------------------ the build
def build(src, dst, variant, force=False, log=print):
    """-> report dict, or None when src already holds the group (nothing written)."""
    if variant not in ('A', 'B'):
        raise ValueError('variant A or B')
    have = md5(src)
    if have != SRC_MD5 and not force:
        raise ValueError('%s: md5 %s is not the DM02 zip this was checked on (%s); use --force' % (src, have, SRC_MD5))
    B = F.Built(src)
    sc = B.sc
    if any(sc.names[t] == GROUP for t in sc.tops()):
        log('kl_dm02_shops_1024: %s already holds %s: nothing to do' % (src, GROUP))
        return None
    coop = variant == 'A'
    big_before = {n.rsplit('_Main', 1)[1]: B.files[n] for n in B.order if n.endswith(('_Main.prm', '_Main.ANM', '_Main.fxc'))}
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']

    M = F.Maker()
    gk = C.group_form(B)
    grp = C._node(M, B, gk, GROUP)
    M.place(grp, (0.0, 0.0, 0.0))
    base = F.R_ + GROUP + '\\'

    desk_k, draw_k = find(B, DESK_TAIL), find(B, DRAWER_TAIL)
    Rd, Pd = B.fr[B.ents[desk_k - 1]]
    desk_bb = list(struct.unpack_from('<6f', C._root(prm, B.ents[desk_k - 1].model), 0x20))

    # ---- F04's door frame (its two leaves are the door's ends) and the nodes of its co-op set
    b4 = F.Built(J.level_zip('F04'))
    s4 = b4.sc
    pre4 = [k for k in range(1, len(s4.names)) if s4.path[k] and (F04_PREFIX in s4.path[k])]
    byname = {s4.path[k].split(F04_PREFIX, 1)[1]: k for k in pre4 if '\\' not in s4.path[k].split(F04_PREFIX, 1)[1]}
    left, right = byname['left_dxxr_01'], byname['right_dxxr_01']
    C4 = [(b4.at(left)[i] + b4.at(right)[i]) / 2.0 for i in range(3)]
    D4 = cols([0.0, 0.0, 1.0], EY, [-1.0, 0.0, 0.0])      # the door frame of the F04 set (measured: arrows at local x -71, z -55 / +60)
    if max(abs(D4[i][j] - b4.fr[b4.ents[byname['Controller'] - 1]][0][i][j]) for i in range(3) for j in range(3)) > 1e-3:
        raise ValueError('F04 set is not in the frame that was measured')
    for old, _new in COOP_PARTS:
        if b4.ents[byname[old] - 1].raw is not None:
            raise ValueError('F04 %s carries raw data (not model-free)' % old)
    arrow_models = {old: b4.ents[byname[old] - 1].model for old, _n in COOP_PARTS}

    sites, open_paths, pts, desks = [], [], [], []
    for si, spec in enumerate(SHOPS, 1):
        sk = shutter_at(B, spec['at'])
        o, xs, zs = shutter_frame(B, sk)
        spath = sc.path[sk]
        is_coop = coop and spec['coop']
        D = cols(zs, EY, cross(zs, EY))                   # local x = into the shop, y up, z = x_s-ish (cross)
        site = {'shop': si, 'shutter_node': sk, 'shutter': spath, 'at': list(spec['at']), 'x_s': xs, 'z_s': zs,
                'mode': 'coop' if is_coop else 'open', 'sets': []}
        sites.append(site)
        if is_coop:
            mid = [o[i] + xs[i] * SPAN / 2.0 for i in range(3)]
            Cn = [mid[0], o[1], mid[2]]
            fix = {}
            made = {}
            for old, short in COOP_PARTS:
                made[old] = M.clone('F04', byname[old], 'KLCoop%d!%s' % (si, short))
            for old, short in COOP_PARTS:
                fix[s4.path[byname[old]]] = base + 'KLCoop%d!%s' % (si, short)
            def to_new(s, fix=fix):
                if s in fix:
                    return fix[s]
                if s.startswith(s4.path[left].rsplit('!', 1)[0] + '!') or s.startswith('ROOT\\Locations/F04'):
                    return None                           # a node of the F04 set that is not taken along
                return s
            for old, short in COOP_PARTS:
                nd = made[old]
                k4 = byname[old]
                R4, P4 = b4.fr[b4.ents[k4 - 1]]
                l = mv(tr(D4), [P4[i] - C4[i] for i in range(3)])
                Pn = [Cn[i] + v for i, v in enumerate(mv(D, l))]
                Rn = mm(D, mm(tr(D4), R4))
                M.place(nd, Pn, stored(Rn))
                remap(M, nd, to_new)
                grp.add(nd)
            ctl, opn = made['Controller'], made['GeomDeactivator_shake_area']
            M.set(opn, 'DeactivateGeom', {1: [spath]})
            # field 23 = completion list (measured on F04's Controller: MatPosAnimProxy, PathBlocker, sound, GeomActivator, Timer); 24 = the
            # CoverStateChanger 'AllCovers' (would switch every cover of the map): both rewritten here.
            M.set(ctl, 'CoopAirlock', {23: [fix[s4.path[byname['CoopAirLock_Pathblocker_00']]], fix[s4.path[byname['GeomDeactivator_shake_area']]]], 24: []})
            site['coop_origin'] = Cn
            pts += [tuple(P) for P in ((Cn[0] - 150, Cn[1] - 10, Cn[2] - 150), (Cn[0] + 150, Cn[1] + 320, Cn[2] + 150))]
        else:
            open_paths.append(spath)
        # ---- loot sets
        for li, lat in enumerate(LATERAL[spec['sets']]):
            P = [o[i] + xs[i] * lat + zs[i] * DEPTH for i in range(3)]
            P[1] = o[1] + (Pd[1] - 500.0)                 # the desk stands on the floor the shutter stands on (the original's floor is y 500)
            # G turns the original's world +Z (the drawer side of the counter) into +z_s: the counter's long axis runs INTO the shop
            G = cols(cross(EY, zs), EY, zs)
            nm = 'KLShop%02d_%d' % (si, li + 1)
            dk = own(M, B, desk_k, nm + '_Montre_Desk', with_ctrls=True)
            Rn = mm(G, Rd)
            M.place(dk, P, stored(Rn))
            grp.add(dk)
            corners = [mv(Rn, [x, y, z]) for x in (desk_bb[0], desk_bb[3]) for y in (desk_bb[1], desk_bb[4]) for z in (desk_bb[2], desk_bb[5])]
            lo = tuple(min(P[i] + c[i] for c in corners) for i in range(3))
            hi = tuple(max(P[i] + c[i] for c in corners) for i in range(3))
            desks.append((dk, lo, hi))
            pts += [lo, hi]
            # the drawer group: the same rigid motion as the counter (world = P + G (p - Pd))
            Rg, Pg = B.fr[B.ents[draw_k - 1]]
            gnew = nm + '_Cashdrawer'
            dg = own(M, B, draw_k, gnew)
            Pgn = [P[i] + v for i, v in enumerate(mv(G, [Pg[j] - Pd[j] for j in range(3)]))]
            M.place(dg, Pgn, stored(mm(G, Rg)))
            fix = {sc.path[draw_k]: base + gnew}
            sub = [(draw_k, dg)]
            for j in kids_of(B, draw_k):
                kd = own(M, B, j, sc.path[j].rsplit('\\', 1)[1])
                dg.add(kd)
                fix[sc.path[j]] = base + gnew + '\\' + sc.path[j].rsplit('\\', 1)[1]
                sub.append((j, kd))
            def to_clone(s, fix=fix):
                if s in fix:
                    return fix[s]
                if s.startswith(sc.path[draw_k] + '\\'):
                    raise ValueError('a reference into the drawer set that was not cloned: ' + s)
                return s
            for j, nd in sub:
                remap(M, nd, to_clone)
            # loot rules: amount; field 11 = 1 (stored 'behind a door': the AI passes it over); the container is the stock one
            mon = [nd for _j, nd in sub if any(M.p.key(c[0]) == 'OnlineMoneyCtrl' for c in nd.ctrls)]
            if len(mon) != 1:
                raise ValueError('the drawer set has %d OnlineMoneyCtrl nodes' % len(mon))
            M.set(mon[0], 'OnlineMoneyCtrl', {1: spec['amount'], 11: 1})
            for _j, nd in sub:                            # ambient light only: the originals link StoreWatch's lights, which are not here
                nd.links = None if nd.links is None else []
            grp.add(dg)
            site['sets'].append({'name': nm, 'at': [round(v, 1) for v in P], 'drawer_at': [round(v, 1) for v in Pgn], 'amount': spec['amount'],
                                 'money_path': base + gnew + '\\' + sc.path[[j for j, nd in sub if nd is mon[0]][0]].rsplit('\\', 1)[1]})
    # ---- the round start: DeactivateGeom of the always-open frontages + a timer, wired into AIMonitor field 2
    timer_path = None
    if open_paths:
        dn = M.clone('F04', byname['GeomDeactivator_shake_area'], 'KLShops_OpenNow')
        M.place(dn, (0.0, 0.0, 0.0))
        M.set(dn, 'DeactivateGeom', {1: open_paths})
        grp.add(dn)
        tk = sc.resolve(F.R_ + 'Gameplay!merc_bot_squad!Timer_start_bots')[0]
        tn = own(M, B, tk, 'KLShops_OpenTimer')
        M.place(tn, (0.0, 0.0, 0.0))
        M.set(tn, 'TriggerDelay2', {0: OPEN_DELAY, 1: 0.0, 2: -1.0, 3: 0, 4: [base + 'KLShops_OpenNow']})
        grp.add(tn)
        timer_path = base + 'KLShops_OpenTimer'

    q, order = M.scene([grp])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'shops')
    if timer_path:
        hit = Jn.resolve(F.R_ + 'Gameplay!AIMonitor')
        mk = [(k, i, v) for k, i, v in kl_fa.controllers(Jn, 'AIMonitor') if k in hit]
        if len(mk) != 1:
            raise ValueError('AIMonitor: %d controllers' % len(mk))
        k, i, v = mk[0]
        lst = list(v[2])
        if timer_path not in lst:
            lst.append(timer_path)
        def setl(us, lst=lst):
            us[2] = kl_fa._refs(Jn, lst)
        kl_fa.edit(Jn, k, i, setl)
    data = Jn.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made_e = nxt, {}
    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, getattr(n, 'raw', None), n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made_e[id(n)] = e
        for kd in n.kids:
            ent(kd, e)
    ent(grp, None)
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
    # listing (GUESS, as kl_fa_cover: a new top-level group goes in the root's group tree with the box of its children; the counters, which have
    # a collision record like the stock ones, in the root's tree 0 - where every level lists its room-less collision objects. The drawer parts
    # stay unlisted exactly as in StoreWatch (the whole Cashdrawer subtree is in no tree there either).
    root3, root0 = octn.rooms[0][3], octn.rooms[0][0]
    if root3 is None or root0 is None:
        raise ValueError('the root has no tree 0 / 3')
    items0 = [(slot1[made_e[id(dk)]] + 2, lo, hi) for dk, lo, hi in desks]
    octn.rooms[0][0] = O.join_trees(root0, C._tree(items0))
    octn.rooms[0][0].check()
    lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3))
    hi = tuple(max(p[a] for p in pts) + 10.0 for a in range(3))
    octn.rooms[0][3] = O.join_trees(root3, C._tree([(slot1[made_e[id(grp)]] + 2, lo, hi)]))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        pm = bytearray(prm)
        t, n = struct.unpack_from('<II', pm, 0)
        old = set(octx.record_refs())
        for i in range(1, n):
            o_, size = struct.unpack_from('<II', pm, t + 16 * i)
            if size == 64 and pm[o_:o_ + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, o_ + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, o_ + 0x1c, move[v]); repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(pm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    big_after = {n.rsplit('_Main', 1)[1]: new[n] for n in B.order if n.endswith(('_Main.prm', '_Main.ANM', '_Main.fxc'))}
    for e_ in ('.ANM', '.fxc'):
        if e_ in big_before and len(big_before[e_]) != len(big_after[e_]):
            raise ValueError('a large block changed its size: ' + e_)
    rep = collections.OrderedDict(
        variant=variant, source=src, source_md5=have, out=dst, out_md5=md5(dst), members_changed=changed, entities_before=len(B.ents),
        entities=len(ents), entities_added=len(order), ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=moved, prm_model_roots_repointed=repointed,
        slot_id_faults_before=pre, slot_id_faults_after=post, open_at_round_start=open_paths, timer=timer_path, sites=sites,
        f04_set_models=arrow_models)
    log('kl_dm02_shops_1024 %s: %d entities added, REF ids %s, members changed %s, %d slot ids renumbered, %d .prm roots re-pointed -> %s (%s)'
        % (variant, len(order), rep['ref_ids'], ' '.join(changed), moved, repointed, dst, rep['out_md5']))
    return rep


PS1 = r'''# shops.ps1 - DM02 mall: more open shops with loot (+ co-op shutters in variant A) (tools/kl_dm02_shops_1024.py, 2026-10-24).
#   powershell -ExecutionPolicy Bypass -File shops.ps1 [-Undo] [-DryRun] [-Game <folder>]
# WHAT: the WHOLE KLExpansion\Maps\DM02\F02_Main.zip is replaced by the build file next to this script (entities were added, so .prp .gms
#   .buf .oct .rmi .rmc .prm all change). The live zip is renamed F02_Main.zip.before-1024shops (never overwritten).
# A and B share the backup name on purpose: install only one; to switch, UNDO the installed one first.
# SAFETY: refuses while kl2.exe runs; the live zip md5 must be exactly the original (or already the new one); read-back md5 after the
#   copy; on failure the original is put back; UNDO only when live == the new build, and renames the backup back (byte identical).
param([switch]$Undo, [switch]$DryRun,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1024shops'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'shops.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
if (Get-Process kl2 -ErrorAction SilentlyContinue) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dst = Join-Path $Game ('KLExpansion\Maps\' + $man.m + '\' + $man.f)
$bak = "$dst$tag"; $tmp = "$dst.tmp1024"
$src = Join-Path $PSScriptRoot $man.f
"target: $dst  (variant $($man.variant))"
if (-not (Test-Path -LiteralPath $dst)) { "SKIP, $dst not installed"; exit 4 }
$cur = md5 $dst
if ($Undo) {
  if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $man.old) { 'already undone'; exit 0 } else { "SKIP, no backup and live is $cur"; exit 4 } }
  if ($cur -ne $man.new) { "SKIP, live is $cur, not this build (changed since, or the other variant?). Backup left in place."; exit 4 }
  if ((md5 $bak) -ne $man.old) { 'SKIP, backup is not the expected original'; exit 4 }
  if ($DryRun) { 'would restore the original (dry run)'; exit 0 }
  Remove-Item -LiteralPath $dst -Force
  Rename-Item -LiteralPath $bak -NewName $man.f
  if ((md5 $dst) -ne $man.old) { 'FAILED, restored file does not read back right!'; exit 4 }
  'original restored, read back ok'; exit 0
}
if ($cur -eq $man.new) { 'already installed'; exit 0 }
if ($cur -ne $man.old) { "SKIP, live md5 is $cur, expected $($man.old). Another install in between, or the other variant installed? Not changed."; exit 4 }
if (Test-Path -LiteralPath $bak) { "SKIP, $bak already exists. Not changed."; exit 4 }
if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $man.new) { "SKIP, build file $src missing or changed"; exit 4 }
if ($DryRun) { 'would install (dry run)'; exit 0 }
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
Copy-Item -LiteralPath $src -Destination $tmp
if ((md5 $tmp) -ne $man.new) { 'FAILED copying, live untouched'; Remove-Item -LiteralPath $tmp -Force; exit 4 }
Rename-Item -LiteralPath $dst -NewName ($man.f + $tag)
$ok = $false
try { Rename-Item -LiteralPath $tmp -NewName $man.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
if (-not $ok) {
  if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
  Rename-Item -LiteralPath $bak -NewName $man.f
  'FAILED swap, original put back'; exit 4
}
if ((md5 $dst) -ne $man.new) { 'FAILED read-back, run UNDO'; exit 4 }
"installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($man.f)$tag"
'''
BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0shops.ps1" {arg}\r\npause\r\n'
LIVE_DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'


def _ps(d, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'shops.ps1'), '-Game', game]
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    """Builds A and B into out/A and out/B with md5-chained INSTALL/UNDO; rehearses on copies under scratch only."""
    old = md5(src)
    if old != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (old, SRC_MD5))
    vdirs = {}
    for v in ('A', 'B'):
        d = os.path.join(out, v); os.makedirs(d, exist_ok=True)
        z = os.path.join(d, 'F02_Main.zip')
        rep = build(src, z, v)
        if rep is None:
            raise SystemExit('input already holds ' + GROUP)
        new = md5(z)
        man = dict(m='DM02', f='F02_Main.zip', variant=v, old=old, new=new, tag=TAG)
        with open(os.path.join(d, 'shops.json'), 'w') as fh:
            json.dump(man, fh, indent=1)
        with open(os.path.join(d, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        with open(os.path.join(d, 'shops.ps1'), 'w', newline='\r\n') as fh:
            fh.write(PS1)
        for nm, arg in (('INSTALL shops %s.bat' % v, ''), ('UNDO shops %s.bat' % v, '-Undo')):
            with open(os.path.join(d, nm), 'w', newline='') as fh:
                fh.write(BAT.format(arg=arg))
        vdirs[v] = (d, man)
        log('variant %s: %s -> %s' % (v, old, new))
    if scratch:
        rehearse(src, vdirs, scratch, log)
    return 0


def rehearse(src, vdirs, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', 'DM02', 'F02_Main.zip')
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    log('rehearsal target: ' + live)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    for v, (d, man) in vdirs.items():
        log('--- variant %s' % v)
        t = _ps(d, g); log(t); assert 'installed' in t and md5(live) == man['new'], t
        assert os.path.isfile(live + TAG) and md5(live + TAG) == man['old']
        t = _ps(d, g, True); log(t)
        assert md5(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
        t = _ps(d, g); assert md5(live) == man['new']
        t = _ps(d, g); assert 'already installed' in t, t
        # the other variant must be refused while this one is installed
        o = 'B' if v == 'A' else 'A'
        t = _ps(vdirs[o][0], g); log(t); assert 'SKIP' in t and md5(live) == man['new'], t
        t = _ps(vdirs[o][0], g, True); assert 'SKIP' in t and md5(live) == man['new'], t
        t = _ps(d, g, True); assert md5(live) == man['old'] and not os.path.exists(live + TAG)
        # wrong live md5 refused
        with open(live, 'ab') as fh:
            fh.write(b'x')
        t = _ps(d, g); log(t); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
        shutil.copy2(src, live)
        log('variant %s rehearsal ok (install, undo byte-identical, reinstall same md5, other variant refused, wrong md5 refused)' % v)
    shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 3 or a[0] not in ('build', 'stage'):
        print(__doc__)
        return 2
    src, out = a[1], a[2]
    if a[0] == 'build':
        vs = ['A', 'B'] if opt('--variant', 'both') == 'both' else [opt('--variant')]
        for v in vs:
            d = os.path.join(out, v) if len(vs) > 1 else out
            os.makedirs(d, exist_ok=True)
            rep = build(src, os.path.join(d, os.path.basename(src)), v, force='--force' in a)
            if rep:
                with open(os.path.join(d, 'shops.json'), 'w') as fh:
                    json.dump(rep, fh, indent=1, default=str)
        return 0
    return stage(src, out, opt('--rehearse'))


if __name__ == '__main__':
    sys.exit(main())
