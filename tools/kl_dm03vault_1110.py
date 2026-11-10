#!/usr/bin/env python3
r"""kl_dm03vault_1110.py - DM03 (Withdrawal, F03 slot) BLOW-UP VAULT DOOR, 2026-11-10. STAGE ONLY: reads a DM03 stage, writes C:\kl_build_1024\dm03vault_1110\stage, never installs.

Owner (11-09): "the double door before the garage as a BLOW-UP vault door with loot" (re/dm03_vault_swat_1109.md).
Door A = the lobby-to-dock doorway at (0, 240, -6806): an EMPTY doorway today (no leaves), 210 cm wide, hinges at x +-105. This pass:
  1. two kick-door groups (kl_interact_graft virtual hosts, own_leaf False = the white DD leaf, 105 cm wide: scale x 0.875) KL_Door_N / KL_Door_N+1 shut the doorway;
     the KickDoor controller of both KickDoor_Action_01 is taken off (nobody kicks the vault open), the Audio_PlaySound of the Front proxies too (the blast is the sound);
  2. ROOT\KL_Vault!1: Arm (TriggerBox, FA mercenaries, 2 m in front of the door in the lobby) -> Fuse (TriggerDelay2, --fuse s) -> Boom (Explode + ShakeCamera, the
     Hasta blast of kl_hasta_blast_1108.dress) + both Front proxies (MatPosAnimProxy swing) + both KickDoor_Pathblocker_01 (bots may walk through);
     Backstop (TriggerDelay2, --backstop s, started by the AIMonitor start list) opens the proxies and pathblockers WITHOUT a second bang (nobody blocks the dock for good);
  3. loot L1 (default): 3 of the 8 big piles (the ones with no bot place within 140 cm) move behind the door onto dock nav cells at 1,000,000 each, the other five are re-split
     so the map total stays exactly 7,000,000; --loot L2 is NOT built (refused: needs loot clones, no node-clone path for loot objects here).
No actor or squad is added (census unchanged). Both zips (plain + bots) are rebuilt the same way; Entries= of KLJoin.ini / KLGuns.ini follows the new .prm chunk count.

  python tools/kl_dm03vault_1110.py stage [--in-dir DIR] [--out DIR] [--accept-input] [--fuse S] [--backstop S] [--loot L1|L2] [--keep-kick (diagnostic)]
Default in-dir C:\kl_build_1024\dm03backswat_1110; restage on the live zip stage with --in-dir C:\kl_build_1024\dm03doorfix_1109 --accept-input (pins what it finds).
"""
import collections, hashlib, json, math, os, re, shutil, statistics, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BS = chr(92)
R = 'ROOT' + BS
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM03')
IN_DIR = r'C:\kl_build_1024\dm03backswat_1110'
OUT = r'C:\kl_build_1024\dm03vault_1110\stage'
TAG = '.before-dm03vault_1110'
# --keep-kick (DIAGNOSTIC stage only, never ship): keep the KickDoor controller + kick sound. Bench 11-10 DM03VAULTB_1110: the shut leaves did NOT block a
# walk; every proven kick door keeps its controller, so this tests whether the stripped controller leaves the leaf (and its keyed slab) out of the shut pose
KEEP_KICK = False
FILES = ('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5')
INIS = ('KLJoin.ini', 'KLGuns.ini')
KNOWN_INPUTS = {('a81ede87c6798642ebf8261499762fd0', 'e8c06e13d5bc2182fe005a1bf2bae741'): 'dm03backswat_1110 output',
                ('8e23cbd308d0a6bea1e2661a939c9881', '2528e8f08e0b1f96ca76d3aa9b3aac18'): 'dm03doorfix_1109 (the live DM03 zips of 11-10)'}

# ---- the doorway (measured on the backswat stage; Door A)
DOOR_Y = 240.0
DOOR_Z = -6806.0                 # the doorway's z (nav cell clearance 66 at (0, -6806))
HINGE_Z = -6812.0                # GUESS: the wall's middle, read to a few cm off the doorway cells
HINGE_X = 105.0                  # half the 210 cm opening
LEAF_W = 105.0                   # each of the two leaves
DOOR_H = 240.0                   # GUESS: the virtual default; the opening height was not measured
DOOR_STOCK_W = 120.0             # kl_interact_graft.DOOR_W
# left hinge: the leaf lies along +x from it, so cx (free end -> hinge) = -x
HOSTS = [('at', (-HINGE_X, DOOR_Y, HINGE_Z), (-1.0, 0.0, 0.0)), ('at', (HINGE_X, DOOR_Y, HINGE_Z), (1.0, 0.0, 0.0))]
DOOR_CHILD_FRONT = 'KickableDoor_Proxy_Variation01Front_A_01'
DOOR_CHILD_PB = 'KickDoor_Pathblocker_01'
DOOR_CHILD_ACTION = 'KickDoor_Action_01'
VAULT = 'KL_Vault!1'
FUSE_S, BACKSTOP_S = 3.0, 240.0  # GUESS: 3 s of "something is about to go" after the Arm box, a 4 min backstop
ARM_AT = (0.0, 340.0, -7006.0)   # lobby, 2 m in front of the door; GUESS: a nav cell
ARM_HALF = (150.0, 120.0, 150.0)
# TriggerBox f10 (re-arm): -1 = fires ONCE, 0 = every enter edge (re/triggerbox.md). The clone of Respawn_Trigger already carries -1; it is pinned here on purpose (review 11-10):
# every-edge would re-send the Fuse (a 2nd bang + the proxies/pathblockers again) each time a heister re-enters the box. GUESS: a spent one-shot box does not fire in round 2 (the Backstop
# then opens the doors); the doc (re/dm03_vault_swat_1109.md) said f10 0 = the DD10 van-box setting, which is right for a box that only SHOWS something.
ARM_REARM = 0xFFFFFFFF
BOOM_AT = (0.0, 360.0, DOOR_Z)
BOOM_HALF = (50.0, 50.0, 50.0)

# ---- loot (backswat stage; world positions of the 8 big piles, parent chain 682 > 22 > 21 all identity rotation)
LOOT_TOTAL = 7000000
LOOT_MOVE = [(-101.665, 327.917, -6275.82), (-98.307, 327.917, -6314.2), (-91.533, 327.917, -6391.63)]     # nodes 797 / 798 / 799: nearest bot place 160 / 161 / 189 cm
LOOT_EACH = 1000000
LOOT_Y_ABOVE_FLOOR = 1.3         # GUESS: the piles at y 241.18 / 241.45 stand on a floor near 240 (the nav cell y)
DOCK_AT = (0.0, 240.0, -6620.0)
DOCK_MIN_Z = -6660.0             # behind the swung leaves (they reach z -6812 + 105)
DOCK_SEP = 140.0
DOCK_CLEAR = 50.0
AMOUNT_STEP = 10000


# ================================================================ pure helpers (kl_dm03vault_1110_test.py)
def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def host_width_sx(widths, stock=DOOR_STOCK_W):
    """kl_interact_graft.build: sx = round(median(host widths) / DOOR_W, 4)."""
    return round(statistics.median(widths) / stock, 4)


def split_amounts(old, target, step=AMOUNT_STEP):
    """{key: amount} -> the same keys scaled so they sum to exactly `target`, every value a multiple of `step`, largest-remainder rounding (the shares keep their order)."""
    if not old or target % step or any(v <= 0 for v in old.values()):
        raise ValueError('split_amounts: bad input')
    tot = float(sum(old.values()))
    units = target // step
    raw = {k: v / tot * units for k, v in old.items()}
    got = {k: int(math.floor(x)) for k, x in raw.items()}
    for k in sorted(raw, key=lambda k: (-(raw[k] - got[k]), k))[:units - sum(got.values())]:
        got[k] += 1
    if sum(got.values()) != units:
        raise ValueError('split_amounts: %d != %d' % (sum(got.values()), units))
    return {k: v * step for k, v in got.items()}


def world_to_local(world, chain):
    """World place -> the place in the frame of a node whose ancestors sit at the offsets `chain` (identity rotations, checked by the caller)."""
    return tuple(float(world[a]) - sum(float(c[a]) for c in chain) for a in range(3))


def door_target_paths(top, nums):
    """[Boom? no] -> (front proxies, pathblockers, action nodes) paths of the doors KL_Door_<n> under `top`."""
    base = lambda n: R + top + BS + 'KL_Door_%d' % n + BS
    return ([base(n) + DOOR_CHILD_FRONT for n in nums], [base(n) + DOOR_CHILD_PB for n in nums], [base(n) + DOOR_CHILD_ACTION for n in nums])


def door_targets(sc, top, nums):
    """Resolve the door nodes BY PATH (never by a raw node id): -> dict(front=[k..], pb=[k..], action=[k..]); ValueError unless every path names exactly one node."""
    out = {}
    for lab, paths in zip(('front', 'pb', 'action'), door_target_paths(top, nums)):
        out[lab] = []
        for p in paths:
            hit = sc.resolve(p)
            if len(hit) != 1:
                raise ValueError('%s: %d nodes' % (p, len(hit)))
            out[lab].append(hit[0])
    return out


def timer_lists(top, nums):
    """The two timer lists: Fuse = Boom + proxies + pathblockers; Backstop = proxies + pathblockers only (no second bang)."""
    fr, pb, _a = door_target_paths(top, nums)
    return [R + VAULT + BS + 'Boom'] + fr + pb, fr + pb


def check_input(key, accept, known=KNOWN_INPUTS):
    if key in known:
        return known[key]
    if accept:
        return 'UNKNOWN zips accepted on --accept-input'
    raise ValueError('REFUSED: input zips %s / %s are not a known stage (%s); --accept-input takes them as they are' % (key[0], key[1], ', '.join(known.values())))


def dock_filter(cells, min_z=DOCK_MIN_Z):
    return [c for c in cells if c[2] >= min_z]


# ================================================================ pass 1: the doors (kl_interact_graft virtual hosts)
def free_top(zp):
    import kl_doors_1108 as D
    return D.free_top(zp)


def pass1(src, dst, log):
    import kl_interact_graft as IG
    top, base = free_top(src)
    log('  doors: top group %s, %d kick doors present (new ones %d, %d)' % (top, base, base + 1, base + 2))
    orig = IG.virtual_host
    # monkeypatch: resolve_doors calls virtual_host(hinge, cx) with the default width 120; ours are LEAF_W wide, DOOR_H tall
    IG.virtual_host = lambda hinge, cx, width=LEAF_W, height=DOOR_H: orig(hinge, cx, LEAF_W, DOOR_H)
    try:
        rep = IG.build(src, dst, ext=0, spots=[], doors=list(HOSTS), log=log, top=top, door_base=base, own_leaf=False)
    finally:
        IG.virtual_host = orig
    return top, [base + 1, base + 2]


# ================================================================ pass 2: Vault group, timers, blast, loot
def one(sc, path):
    hit = sc.resolve(path)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (path, len(hit)))
    return hit[0]


def chain_of(sc, k):
    """Ancestors of k (nearest first) with their ZGEOM[2] offsets; refuses a turned ancestor."""
    import kl_fa, kl_prpjoin as J
    out, c = [], sc.parent[k]
    while c > 0:
        lab = J.labels('dd', sc.cls(c))
        v = kl_fa.node_values(sc, c)
        rot = v[lab.index('ZGEOM[1]')]
        if max(abs(a - b) for a, b in zip(rot, (0, 0, 1, 0, 1, 0, 1, 0, 0))) > 1e-4:
            raise ValueError('%s: an ancestor is turned' % sc.path[c])
        out.append(tuple(v[lab.index('ZGEOM[2]')]))
        c = sc.parent[c]
    return out


def world_of(sc, k):
    import kl_fa, kl_prpjoin as J
    lab = J.labels('dd', sc.cls(k))
    p = kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')]
    ch = chain_of(sc, k)
    return tuple(float(p[a]) + sum(float(c[a]) for c in ch) for a in range(3))


def find_piles(B):
    """The 8 big loot piles: CONTAINER money objects (kind 'case': opened by their MoneyBox's Attach01) of >= 500000 -> {node: (amount, world pos, MoneyBox group node)}.
    The MoneyBox group (the visible case with its lids, a sibling of the pile under the same room group) must move with its pile."""
    import kl_fa_bots as KB
    out = {}
    for o in KB.money_objects(B):
        if o['amount'] >= 500000 and o['kind'] == 'case' and o['container']:
            g = B.sc.parent[o['container']]
            if not B.sc.names[g].startswith('PC0500_M03_MoneyBox_'):
                raise ValueError('pile %d: container group %s is not a MoneyBox' % (o['node'], B.sc.path[g]))
            out[o['node']] = (o['amount'], world_of(B.sc, o['node']), g)
    return out


def descendants(sc, k):
    kids = collections.defaultdict(list)
    for c in range(1, len(sc.nodes)):
        kids[sc.parent[c]].append(c)
    out, todo = [], [k]
    while todo:
        c = todo.pop()
        out.append(c)
        todo += kids[c]
    return out


def loot_plan(B, nav, home, log):
    """-> (moves {pile node: world target}, amounts {node: new amount}, groups {pile: MoneyBox group}). The 3 piles at LOOT_MOVE go to dock cells; the rest re-split; the total stays LOOT_TOTAL."""
    import kl_fa_bots as KB
    piles = find_piles(B)
    total = sum(o['amount'] for o in KB.money_objects(B))
    if total != LOOT_TOTAL:
        raise ValueError('map loot total %d, expected %d' % (total, LOOT_TOTAL))
    move = []
    for want in LOOT_MOVE:
        hit = [k for k, v in piles.items() if math.dist(v[1], want) < 2.0]
        if len(hit) != 1:
            raise ValueError('loot pile near %s: %d nodes (piles %s)' % (want, len(hit), {k: tuple(round(x, 1) for x in v[1]) for k, v in piles.items()}))
        move.append(hit[0])
    cells = dock_filter([c for c in nav.around(DOCK_AT, 600.0, home) if abs(c[1] - DOOR_Y) < 15.0])
    spots = nav.spots(cells, len(move), DOCK_SEP, ref=DOCK_AT + (0,), clear=DOCK_CLEAR) if cells else []
    if len(spots) != len(move):
        raise ValueError('only %d dock cells for %d piles' % (len(spots), len(move)))
    spots = sorted(spots, key=lambda c: (c[0], c[2]))
    moves = {k: (c[0], c[1] + LOOT_Y_ABOVE_FLOOR, c[2]) for k, c in zip(move, spots)}
    rest = {k: v[0] for k, v in piles.items() if k not in moves}
    pile_total = sum(v[0] for v in piles.values())
    new_rest = split_amounts(rest, pile_total - LOOT_EACH * len(moves))
    amounts = dict(new_rest)
    amounts.update({k: LOOT_EACH for k in moves})
    if sum(amounts.values()) != pile_total:
        raise ValueError('loot sum changed')
    log('  loot L1: piles %s -> dock %s at %d each; the other %d piles %s' % (
        move, {k: tuple(round(v) for v in p) for k, p in moves.items()}, LOOT_EACH, len(rest), {k: v for k, v in sorted(new_rest.items())}))
    return moves, amounts, {k: piles[k][2] for k in moves}


def apply_loot(B, moves, amounts, groups):
    """Move each pile (world -> local, .prp ZGEOM[2] + entity translation) and its MoneyBox group by the same delta; set the amounts. -> {node: delta} for the
    pile, its group and the group's whole subtree (the .oct boxes of all of them shift by it)."""
    import kl_graft, kl_prpjoin as J, kl_fa_author as AU
    import kl_loot_1025 as L
    sc = B.sc
    delta_of = {}
    for k, wpos in moves.items():
        w0 = world_of(sc, k)
        d = tuple(wpos[a] - w0[a] for a in range(3))
        g = groups[k]
        locs = {k: world_to_local(wpos, chain_of(sc, k))}
        lg = [float(x) for x in kl_graft_values(sc, g)]
        locs[g] = tuple(lg[a] + d[a] for a in range(3))
        for n, loc in locs.items():
            lab = J.labels('dd', sc.cls(n))
            i = lab.index('ZGEOM[2]')
            kl_graft.edit(sc.nodes[n], 'props', lambda us, loc=loc, i=i: AU.setv(sc, us, i, [float(x) for x in loc]))
            e = B.ents[n - 1]
            e.trans = struct.pack('<3f', *loc) + e.trans[12:]
        for n in descendants(sc, g) + [k]:
            delta_of[n] = d
    for k, v in amounts.items():
        L.amount(B, k, v)
    return delta_of


def kl_graft_values(sc, n):
    import kl_fa, kl_prpjoin as J
    lab = J.labels('dd', sc.cls(n))
    return kl_fa.node_values(sc, n)[lab.index('ZGEOM[2]')]


def rebox_loot(octn, moved, slot1, B, delta_of, must=()):
    """After remap_ids: every .oct item of a moved pile gets its box shifted by the pile's world delta; the tree is rebuilt."""
    import kl_octree as O
    ids = {slot1[B.ents[k - 1]] + 2: delta_of[k] for k in delta_of}
    n = 0
    seen = set()
    for room in octn.rooms:
        for ti, t in enumerate(room):
            if t is None or not any(it[0] in ids for it in t.items):
                continue
            its = []
            for it in t.items:
                if it[0] in ids:
                    d = ids[it[0]]
                    seen.add(it[0])
                    lo = t.world(it[1:4])
                    hi = t.world([v + 1 for v in it[4:7]])
                    its.append([it[0]] + O.quantise_box(t.origin, t.scale, tuple(lo[a] + d[a] for a in range(3)), tuple(hi[a] + d[a] for a in range(3))))
                    n += 1
                else:
                    its.append(list(it))
            room[ti] = O.build_tree(its, t.origin, t.scale, quantised=True)
            room[ti].check()
    need = {slot1[B.ents[k - 1]] + 2 for k in must}
    if not need <= seen:
        raise ValueError('moved piles without an .oct item: %d of %d' % (len(need - seen), len(need)))
    return n


def make_vault_nodes(B):
    """KL_Vault!1: Arm (TriggerBox clone), Fuse, Backstop (TriggerDelay2 clones), Boom (box clone, ctrls set later by the Hasta blast dress). Lists/fields are set on the joined scene."""
    import kl_fa_bots as KB, kl_fa_fed as FED, kl_old_waves as KOW
    sc = B.sc
    M = KB.Maker()
    node = lambda path: one(sc, path)
    top = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), VAULT)
    top.ctrls = []
    M.place(top, (0.0, 0.0, 0.0))
    form = node(R + 'Triggers!Respawn_Trigger')
    arm = top.add(FED.clone_built(M, B, form, 'Arm'))
    M.place(arm, ARM_AT)
    M.set(arm, None, {'ZBoxPrimitive[%d]' % a: float(ARM_HALF[a]) for a in range(3)})
    boom = top.add(FED.clone_built(M, B, form, 'Boom'))
    boom.ctrls = []
    M.place(boom, BOOM_AT)
    M.set(boom, None, {'ZBoxPrimitive[%d]' % a: float(BOOM_HALF[a]) for a in range(3)})
    for nm in ('Fuse', 'Backstop'):
        t = top.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), nm))
        M.place(t, (0.0, 0.0, 0.0))
    return M, [top]


def rebuild(src, dst, top, nums, fuse, backstop, log):
    import kl_fa, kl_gms, kl_graft, kl_scene
    import kl_fa_bots as KB
    import kl_fa_author as AU
    import kl_octree as O
    import kl_old_waves as KOW
    import kl_prpjoin as J
    import kl_dm02_assault_1025 as AS
    import kl_hasta_blast_1108 as HBL
    from kl_prp import Prp
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + VAULT):
        raise ValueError('%s already holds %s' % (src, VAULT))
    tg0 = door_targets(sc, top, nums)
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
    a0, s0 = AS.census(sc)
    nav = KB.Nav(A.nav, links=True)
    home = KB.stations(B, nav)['home']
    rep = collections.OrderedDict(census_before=[a0, s0])
    # ---- arm box must stand on the floor (a nav cell)
    if nav.at(ARM_AT[0], DOOR_Y, ARM_AT[2], dy=80.0) is None:
        raise ValueError('the Arm box centre %s is not over a nav cell' % (ARM_AT,))
    # ---- loot
    moves, amounts, groups = loot_plan(B, nav, home, log)
    delta_of = apply_loot(B, moves, amounts, groups)
    rep['loot'] = dict(moves={k: [round(v, 2) for v in p] for k, p in moves.items()}, amounts=amounts, paths={k: sc.path[k] for k in moves}, groups={k: sc.path[g] for k, g in groups.items()})
    # ---- nodes
    M, tops = make_vault_nodes(B)
    q, order = M.scene(tops)
    picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    Jn = J.join(sc, picks, 'dm03vault')
    tg = door_targets(Jn, top, nums)
    fuse_l, back_l = timer_lists(top, nums)
    for nm, delay, lst in (('Fuse', fuse, fuse_l), ('Backstop', backstop, back_l)):
        k = one(Jn, R + VAULT + BS + nm)
        ci = AU.ctrl_of(Jn, k, 'TriggerDelay2')

        def ft(us, delay=delay, lst=lst):
            if len(us) != 5:
                raise ValueError('TriggerDelay2 is not 5 fields')
            AU.setv(Jn, us, 0, float(delay))
            AU.setv(Jn, us, 4, lst)
        kl_fa.edit(Jn, k, ci, ft)
    ka = one(Jn, R + VAULT + BS + 'Arm')
    ci = AU.ctrl_of(Jn, ka, 'TriggerBox')
    fuse_path = R + VAULT + BS + 'Fuse'

    def fa(us):
        AU.setv(Jn, us, 14, 'ECPS_FA_MERCONLY')        # GUESS: mercenaries only, as dd10 vancall
        AU.setv(Jn, us, 10, ARM_REARM)                  # one-shot, see ARM_REARM
        AU.setv(Jn, us, 15, 0)                          # any heister counts
        AU.setv(Jn, us, 17, [fuse_path])
    kl_fa.edit(Jn, ka, ci, fa)
    kb = one(Jn, R + VAULT + BS + 'Boom')
    HBL.dress(Jn, kb, 'AITrigger', log=log)
    for kk in tg['action'] if not KEEP_KICK else ():     # nobody kicks the vault open
        Jn.nodes[kk]['ctrls'] = [(nm, b) for nm, b in Jn.nodes[kk]['ctrls'] if Jn.p.key(nm) != 'KickDoor']
    for kk in tg['front'] if not KEEP_KICK else ():      # no kick sound at the swing: the blast is the sound
        cs = Jn.nodes[kk]['ctrls']
        keep = [(nm, b) for nm, b in cs if Jn.p.key(nm) != 'Audio_PlaySound']
        if [Jn.p.key(nm) for nm, _b in keep] != ['MatPosAnimProxy']:
            raise ValueError('%s controllers %s' % (Jn.path[kk], [Jn.p.key(nm) for nm, _b in cs]))
        Jn.nodes[kk]['ctrls'] = keep
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [R + VAULT + BS + 'Backstop']))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa_, fs_ = AS.census(Jn)
    if (fa_, fs_) != (a0, s0):
        raise ValueError('census changed %d / %d -> %d / %d' % (a0, s0, fa_, fs_))
    rep['census_after'] = [fa_, fs_]
    if sum(o['amount'] for o in KB.money_objects(B)) != LOOT_TOTAL:
        raise ValueError('loot total after the edit is not %d' % LOOT_TOTAL)
    new = dict(B.files)
    new[B.ext['.prp']] = prp
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
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    items = []
    for t in tops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3))
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3))
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    if r3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    rep['oct_items_reboxed'] = rebox_loot(octn, None, slot1, B, delta_of, must=list(moves))
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed = 0
    if move:
        prm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', prm, 0)
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', prm, tt + 16 * i)
            if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', prm, off + 0x1c, move[v]); repointed += 1
        new[B.ext['.prm']] = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    rep.update(entities_added=len(order), slot_ids_moved=sum(1 for a, b in ids.items() if a != b), prm_roots_repointed=repointed)
    work = tempfile.mkdtemp(prefix='dm03vault_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F03_Main.zip'), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        rep['sealed'] = kl_fa_bank.seal(work, log=lambda *_: None)
        probs = kl_fa_bank.reverify(work, log=lambda *_: None)
        if probs:
            log('  reverify notes: %s' % probs[:5])
        rep['reverify'] = probs[:5]
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep['members_changed'] = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    log('  written %s: members changed: %s' % (dst, ' '.join(rep['members_changed'])))
    return rep


def apply(src, dst, fuse, backstop, log=print):
    tmp = tempfile.mkdtemp(prefix='dm03v1_')
    try:
        mid = os.path.join(tmp, os.path.basename(dst))
        top, nums = pass1(src, mid, log)
        rep = rebuild(mid, dst, top, nums, fuse, backstop, log)
        rep.update(top=top, doors=nums)
        return rep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ================================================================ stage + install
def chunks(zp):
    import kl_doors_1108 as D
    return D.chunks(zp)


def patch_entries(path_in, n):
    import kl_doors_1108 as D
    return D.patch_entries(path_in, n)


def make_install(files, tag, game=GAME):
    import kl_doors_1108 as D
    src = D.INSTALL.replace('@MAP@', 'DM03').replace('@GAME@', game).replace('@TAG@', tag).replace('@FILES@', repr(files)).replace('@NEEDS@', ' (the pinned inputs: the live DM03 zips, or the backswat stage when that is installed)').replace('@HINT@', '')
    src = src.replace('OWN-LEAF KICK DOORS 1108 (tools/kl_doors_1108.py)', 'DM03 VAULT DOOR 1110 (tools/kl_dm03vault_1110.py)')
    src = src.replace('<name>.before-doors_1108', '<name>' + tag)
    return src


def stage(in_dir=IN_DIR, out=OUT, accept_input=False, fuse=FUSE_S, backstop=BACKSTOP_S, loot='L1', ini_dir=MAPDIR, log=print):
    if loot != 'L1':
        raise ValueError('--loot %s is not built: only L1 (move 3 piles behind the door); L2 needs loot-object clones' % loot)
    ins = {n: fmd5(os.path.join(in_dir, n)) for n in FILES[:2]}
    log('input: %s (%s)' % (check_input((ins[FILES[0]], ins[FILES[1]]), accept_input), in_dir))
    if open(os.path.join(in_dir, FILES[2])).read().strip() != ins[FILES[0]]:
        raise ValueError('%s: bots.base.md5 is not the plain zip md5' % in_dir)
    in_base = fmd5(os.path.join(in_dir, FILES[2]))
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='dm03vout_', dir=os.path.dirname(out))
    reps = {}
    try:
        for n in FILES[:2]:
            log('== %s' % n)
            reps[n] = apply(os.path.join(in_dir, n), os.path.join(tmp, n), fuse, backstop, log)
        plain = fmd5(os.path.join(tmp, FILES[0]))
        for n in os.listdir(out):
            p = os.path.join(out, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        for n in FILES[:2]:
            shutil.copyfile(os.path.join(tmp, n), os.path.join(out, n))
        open(os.path.join(out, FILES[2]), 'w', newline='\n').write(plain + '\n')
        nchunks = chunks(os.path.join(out, FILES[0]))
        files = [(FILES[0], ins[FILES[0]], plain), (FILES[1], ins[FILES[1]], fmd5(os.path.join(out, FILES[1]))), (FILES[2], in_base, fmd5(os.path.join(out, FILES[2])))]
        for n in INIS:
            data, c = patch_entries(os.path.join(ini_dir, n), nchunks)
            if c != 1:
                raise ValueError('%s: %d Entries= lines' % (n, c))
            open(os.path.join(out, n), 'wb').write(data)
            files.append((n, fmd5(os.path.join(ini_dir, n)), fmd5(os.path.join(out, n))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(make_install(files, TAG))
    for nm, arg in (('INSTALL DM03 vault 1110.bat', ''), ('UNDO DM03 vault 1110.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    ini = os.path.join(GAME, 'KLHook.ini')
    cover = [ln.rstrip('\r\n') for ln in open(ini, encoding='latin1') if ln.split('=')[0].strip() in ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientBuildMaps', 'ClientRewrite', 'ClientRingSync')]
    open(os.path.join(out, 'bench_cover_lines.txt'), 'w').write('\n'.join(cover) + '\n')
    json.dump(dict(files=files, reports=reps, chunks=nchunks, fuse=fuse, backstop=backstop, loot=loot, cover_lines=cover), open(os.path.join(out, 'build_report.json'), 'w'), indent=1, default=str)
    return files


def main(a):
    if not a or a[0] != 'stage':
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    global KEEP_KICK
    KEEP_KICK = '--keep-kick' in a
    for n, o, w in stage(opt('--in-dir', IN_DIR), opt('--out', OUT), '--accept-input' in a, float(opt('--fuse', FUSE_S)), float(opt('--backstop', BACKSTOP_S)), opt('--loot', 'L1')):
        print('%-26s %s -> %s' % (n, o, w))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
