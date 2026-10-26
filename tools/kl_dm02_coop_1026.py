"""kl_dm02_coop_1026.py - DM02 mall (F02 slot) co-op shutter fix: a SOLO "lift shutter" prompt, the six co-op cash drawers back behind their
co-op shutters, and the five dark KL_Shops rooms dressed with furniture and lights cloned from DM02's own upstairs shops.
Written 2026-10-26 (offline only; reads the live zip, writes copies; nothing is installed). Nothing imports it.

WHY (owner: "i see one [co-op shutter] but no button to pull shutter up")  - evidence in the report of the run that wrote this:
  * The prompt of a CoopAirlock (kl2 0x5505c0 -> 0x8e4190 -> predicate 0x8eeae0 -> 0x4c06c0, use-action 0x19) shows only for a PLAYER standing inside
    Box A or Box B: two small INVISIBLE boxes (about 114 x 248 x 124) on the atrium side of the shutter, centred 71 in front of it.
  * The lift needs BOTH boxes occupied by players (bots cannot fill them): a solo or offline player never completes it.
  * The owner's play log has them 40 s at y = 0 below co-op shutter 1, which is on floor 2 (y = 500).
WHAT THIS ADDS (one new top-level group 'KL_Coop!', clones only):
  solo   per co-op shutter a PlayerAction clone of L03 'Fake_EndAlley_Airlock' (the stock use box), text 'CoOpDoors/L03_CoOpDoors/L03_CoOpLift'
         ("{TapUse} Lift Door"), placed at the LOW-lateral end of the shutter opening (lat 80, beside the two co-op boxes, same turn as Box A),
         enabled (field 8 = 1), action list = the CoopAirlock's own completion list [PathBlocker, shutter DeactivateGeom].
  drawers the six KL_Shops cash drawer groups go back to their original places on the counters (the lanes pass had moved them out); loot total unchanged.
  dress  per shop 2..4 kits (wall plaques, display table, shelf wall, desk corner, lounge, ceiling lamp) = rigid copies of DM02's own upstairs props
         + their lights, turned/moved onto the shop's walls; the lights link the shop's structure and props; props go in the root room trees.
GUESSES (each also in a comment): a PlayerAction may activate PathBlocker / DeactivateGeom nodes; the player need not face the box direction; the
  clones render and light from the root room trees; ZLIGHT[2] (baked shadow chunk) emptied on every light clone; cloned props are walk-through
  (no HVK, as the counters before them); shop floor = the shutter's y; a double use (solo + co-op) re-blocks the PathBlocker (eToggle).
usage (from tools/):  python kl_dm02_coop_1026.py patch <live F02_Main.zip 1dd14609> <out folder> [--rehearse <scratch>]   (solo lift re-arm fix, 2 variants)
                      python kl_dm02_coop_1026.py stage <in F02_Main.zip> <out folder> [--rehearse <scratch>]
"""
import collections, json, math, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as F
import kl_fa_cover as C
import kl_octree as O
import kl_prpjoin as J
import kl_dm02_shops_1024 as S
import kl_lanes_stage_1025 as LS
import kl_loot_1025 as LO

SRC_MD5 = '36610fc840823be968d3c537249cbefe'      # the live DM02 zip this was built and checked on (2026-10-26)
GROUP = 'KL_Coop!'
TAG = '.before-1026coop'
TAG_SOLO = '.before-1026solo'   # 03:36: the patch install refused, '.before-1026coop' was taken by the 22:18 coop install
R_ = F.R_
DONOR_USE = ('L03', R_ + 'Special!Coop_doors!EndAlleyHACK!Fake_EndAlley_Airlock')
TEXT_LIFT = 'CoOpDoors/L03_CoOpDoors/L03_CoOpLift'
SOLO_LAT = 80.0                                   # along the shutter span; the co-op boxes stand at lat 261 and 380 (half width 57)
BOX_HALF = (57.0, 124.0, 62.0)                    # the co-op boxes' own half sizes (measured on the live KLCoop nodes)
# the six drawer groups (slot-independent node ids of the live zip) -> their ORIGINAL places (owner1025_build/DM02/stage/build_report.json)
DRAWERS = collections.OrderedDict([
    (23622, ('KLShop01_1_Cashdrawer', (-2577.0, 593.0, 1186.0))), (23630, ('KLShop01_2_Cashdrawer', (-2577.0, 593.0, 1486.0))),
    (23645, ('KLShop02_1_Cashdrawer', (2577.0, 593.0, 1506.0))), (23653, ('KLShop02_2_Cashdrawer', (2577.0, 593.0, 1206.0))),
    (23668, ('KLShop03_1_Cashdrawer', (2577.0, 593.0, -2187.0))), (23676, ('KLShop03_2_Cashdrawer', (2577.0, 593.0, -2487.0)))])
# shop interior in the shutter frame (measured): walls occupy lat -22..28 and 608..658; depth 10..1010; the entry path stays free
LAT0, LAT1, DEP0, DEP1 = 28.0, 608.0, 10.0, 1010.0
ENTRY = (190.0, 450.0, -1e9, 400.0)               # lat0, lat1, depth0, depth1 - never furnished
PAD = 10.0

# ---- the kits: ids of the live zip (asserted by name), the donor wall normal (world xz, pointing INTO the room), the wall coordinate (n . p),
#      the donor floor y. 'free' kits have no wall (translation only).
KITS = collections.OrderedDict([
    ('plaque2', dict(ids=[897, 899], names=('Wallmontre_06', 'Wallmontre_04'), n=(0.0, -1.0), wall=-2990.0, floor=500.0)),
    ('watchtable', dict(ids=[923, 885], names=('Montre_Large_01', 'IOLight29'), n=(0.0, -1.0), wall=-2990.0, floor=500.0)),
    ('shelfwall', dict(ids=[215, 217, 218, 197, 196, 195, 194, 193, 192, 268, 259, 260],
                       names=('Shelvesystem_A_08', 'Shelvesystem_A_07', 'Shelvesystem_A_06', 'Shelvedrawers_A_07', 'Shelvedrawers_A_08',
                              'Shelvedrawers_A_09', 'Shelvedrawers_A_10', 'Shelvedrawers_A_11', 'Shelvedrawers_A_12', 'Watercooler_A_01',
                              'IOLight03', 'IOLight03_watercooler'), n=(-1.0, 0.0), wall=-2610.0, floor=510.0)),
    ('deskcorner', dict(ids=[277, 276, 278, 261], names=('Desk_A_03', 'OfficeChair_A_03', 'TableLampA_03', 'IOLight02'), n=(0.0, -1.0), wall=-3200.0, floor=510.0)),
    ('lounge', dict(ids=[269, 270], names=('Sofa_A_01', 'Persianrug_A_01'), n=(0.0, 1.0), wall=2634.0, floor=510.0)),
    ('lamp', dict(ids=[1473, 1472], names=('lamp01', 'IOLight18'), free=(500.0, 2500.0), floor=500.0))])
# per shop: (kit, wall, along). wall W0 / W1 = the side walls (along = depth of the kit centre); R = the rear wall (along = lat of the kit centre);
# free kits: along = (lat, depth). Footprints are asserted against the interior, the desks and the entry path at build time.
PLAN = {1: [('plaque2', 'W0', 760.0), ('plaque2', 'W1', 760.0), ('watchtable', 'R', 318.0), ('lamp', None, (318.0, 300.0)), ('lamp', None, (318.0, 760.0))],
        2: [('shelfwall', 'W1', 835.0), ('deskcorner', 'R', 200.0), ('lamp', None, (318.0, 300.0)), ('lamp', None, (318.0, 760.0))],
        3: [('shelfwall', 'W0', 835.0), ('lounge', 'R', 318.0), ('lamp', None, (318.0, 300.0)), ('lamp', None, (318.0, 760.0))],
        4: [('deskcorner', 'R', 318.0), ('plaque2', 'W0', 760.0), ('lamp', None, (318.0, 300.0)), ('lamp', None, (318.0, 760.0))],
        5: [('shelfwall', 'W0', 835.0), ('plaque2', 'W1', 760.0), ('lounge', 'R', 318.0), ('lamp', None, (318.0, 300.0)), ('lamp', None, (318.0, 760.0))]}


def wbox(B, prm, k):
    """World AABB of a node with a model (lo, hi), else the point twice."""
    e = B.ents[k - 1]
    R, T = B.fr[e]
    rt = C._root(prm, e.model) if e.model else None
    if rt is None:
        return tuple(T), tuple(T), False
    v = struct.unpack_from('<6f', rt, 0x20)
    cs = [S.mv(R, [x, y, z]) for x in (v[0], v[3]) for y in (v[1], v[4]) for z in (v[2], v[5])]
    return tuple(T[i] + min(c[i] for c in cs) for i in range(3)), tuple(T[i] + max(c[i] for c in cs) for i in range(3)), True


def is_light(B, k):
    return kl_gms.category(B.sc.tids[k]) == 2


def room_structure(B, prm, probe):
    """The ZSTDOBJ children (with a model) of the 'Corridore' ZROOM whose children's union box holds the world point probe -> [node]."""
    sc = B.sc
    best = None
    for k in range(1, len(sc.names)):
        p = sc.path[k]
        if sc.cls(k) != 'ZROOM' or not p or 'Corridore_' not in p.rsplit('\\', 1)[-1]:
            continue
        kids = [j for j in S.kids_of(B, k) if sc.cls(j) == 'ZSTDOBJ' and B.ents[j - 1].model]
        if not kids:
            continue
        bx = [wbox(B, prm, j)[:2] for j in kids]
        lo = [min(b[0][i] for b in bx) for i in range(3)]
        hi = [max(b[1][i] for b in bx) for i in range(3)]
        if all(lo[i] - 1 <= probe[i] <= hi[i] + 1 for i in range(3)):
            if best is not None:
                raise ValueError('two corridor rooms hold %s' % (probe,))
            best = (k, kids)
    if best is None:
        raise ValueError('no corridor room holds %s' % (probe,))
    return best


def g_matrix(nd, nt):
    """Vertical-axis rotation G (3x3) that turns the xz direction nd onto nt."""
    c = nd[0] * nt[0] + nd[1] * nt[1]
    s = nd[0] * nt[1] - nd[1] * nt[0]
    return [[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]]


# ------------------------------------------------------------------ the build
def build(src, dst, solo=True, drawers=True, dress=True, force=False, log=print):
    have = S.md5(src)
    if have != SRC_MD5 and not force:
        raise ValueError('%s: md5 %s is not the DM02 zip this was checked on (%s)' % (src, have, SRC_MD5))
    B = F.Built(src, 'F02')
    sc = B.sc
    if any(sc.names[t] == GROUP for t in sc.tops()):
        log('%s already holds %s: nothing to do' % (src, GROUP))
        return None
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']
    n_before = len(B.ents)

    # ---- (c) drawers back: the .prp ZGEOM[2] and the .gms record of each group (kl_lanes_stage_1025.move_group), asserted against the lanes places
    moved = []
    if drawers:
        for g, (nm, pos) in DRAWERS.items():
            if sc.names[g] != nm:
                raise ValueError('node %d is %s, not %s (not the DM02 zip of the lanes pass)' % (g, sc.names[g], nm))
            cur = [round(float(v), 1) for v in B.at(g)]
            if cur != [round(float(v), 1) for v in LS.DM02_MOVES[g]]:
                raise ValueError('%s stands at %s, not at the lanes place %s' % (nm, cur, LS.DM02_MOVES[g]))
        stuck = LO.listed_in_oct(B, [j for g in DRAWERS for j in range(g, sc.end[g])])
        if stuck:
            raise ValueError('drawer nodes %s are listed in an .oct room tree' % stuck)
        for g, (nm, pos) in DRAWERS.items():
            LS.move_group(B, g, pos)
            moved.append(collections.OrderedDict(group=g, name=nm, was=list(LS.DM02_MOVES[g]), now=list(pos)))

    M = F.Maker()
    gk = C.group_form(B)
    grp = C._node(M, B, gk, GROUP)
    M.place(grp, (0.0, 0.0, 0.0))
    base = R_ + GROUP + '\\'
    pts, props, lights = [], [], []                  # props / lights: (Node, lo, hi)
    wl = {}                                          # id(Node) -> [(Node | structure Entity, bits)] wanted links
    back = collections.defaultdict(list)             # id(structure Entity) -> (Entity, [(Node light, bits)])
    sites = []
    wanted = []                                      # Entity -> [(light Node, 0)] receivers outside the new group

    for si, spec in enumerate(S.SHOPS, 1):
        sk = S.shutter_at(B, spec['at'])
        o, xs, zs = S.shutter_frame(B, sk)
        site = {'shop': si, 'at': list(spec['at']), 'coop': spec['coop'], 'solo': None, 'dress': []}
        sites.append(site)
        W = lambda lat, dep, up=0.0, o=o, xs=xs, zs=zs: [o[i] + xs[i] * lat + zs[i] * dep + (up if i == 1 else 0.0) for i in range(3)]
        # ---- (b) the solo prompt
        if solo and spec['coop'] and True:
            bx = S.find(B, 'KLCoop%d!Box_A' % si)
            Rb, Tb = B.fr[B.ents[bx - 1]]
            P = [Tb[i] + xs[i] * (SOLO_LAT - 380.0) for i in range(3)]
            us = grp.add(M.clone(DONOR_USE[0], DONOR_USE[1], 'KLCoop%d!SoloLift' % si))
            if us.links is not None or us.model:
                raise ValueError('the L03 use donor is not model/list free')
            M.place(us, P, S.stored(Rb))
            M.set(us, None, {'ZBoxPrimitive[0]': BOX_HALF[0], 'ZBoxPrimitive[1]': BOX_HALF[1], 'ZBoxPrimitive[2]': BOX_HALF[2]})
            pb = base[:-len(GROUP) - 1] + 'KL_Shops!\\KLCoop%d!Pathblocker' % si
            op = base[:-len(GROUP) - 1] + 'KL_Shops!\\KLCoop%d!Open' % si
            for q in (pb, op):
                if len(sc.resolve(q)) != 1:
                    raise ValueError('no node at ' + q)
            # GUESS: a PlayerAction may start a PathBlocker (eToggle) and a DeactivateGeom node: the same list the CoopAirlock runs on completion.
            M.set(us, 'PlayerAction', {1: [pb, op], 8: 1})
            M.set(us, 'PlayerAction', {7: TEXT_LIFT})
            site['solo'] = dict(name=us.name, at=[round(v, 1) for v in P], text=TEXT_LIFT, actions=[pb, op])
            pts += [tuple(P[i] - 130 for i in range(3)), tuple(P[i] + 130 for i in range(3))]
        if not dress:
            continue
        # ---- (c) the dressing
        floor_t = o[1]
        probe = W(320.0, 500.0, 100.0)
        rk, struct_ks = room_structure(B, prm, probe)
        keep = [(ENTRY[0], ENTRY[1], ENTRY[2], ENTRY[3])]
        for dn in range(1, 3):
            nm_ = 'KLShop%02d_%d_Montre_Desk' % (si, dn)
            hit = [k for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].endswith('\\' + nm_)]
            if hit:
                lo, hi, _m = wbox(B, prm, hit[0])
                pc = [(sum((p[i] - o[i]) * xs[i] for i in range(3)), sum((p[i] - o[i]) * zs[i] for i in range(3)))
                      for p in [[(lo, hi)[(m >> j) & 1][j] for j in range(3)] for m in range(8)]]
                keep.append((min(a for a, _b in pc) - PAD, max(a for a, _b in pc) + PAD, min(b for _a, b in pc) - PAD, max(b for _a, b in pc) + PAD))
        shop_lights, shop_props = [], []
        for kn, wallsel, along in PLAN[si]:
            kit = KITS[kn]
            for k, nm in zip(kit['ids'], kit['names']):
                if not sc.path[k] or not sc.path[k].rsplit('\\', 1)[-1].endswith(nm):
                    raise ValueError('kit %s: node %d is %s, not %s' % (kn, k, sc.path[k], nm))
                if sc.nodes[k]['ctrls']:
                    raise ValueError('kit %s: %s carries a controller' % (kn, nm))
            if 'free' in kit:
                G = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
                Ad = [kit['free'][0], 0.0, kit['free'][1]]
                At = W(along[0], along[1])
            else:
                nd = kit['n']
                td = (-nd[1], nd[0])
                bb = [wbox(B, prm, k) for k in kit['ids'] if not is_light(B, k)]
                pcs = [(lo, hi) for lo, hi, m in bb if m]
                ss = [td[0] * p[0] + td[1] * p[2] for lo, hi in pcs for p in (lo, hi)]
                s_mid = (min(ss) + max(ss)) / 2.0
                Ad = [nd[0] * kit['wall'] + td[0] * s_mid, 0.0, nd[1] * kit['wall'] + td[1] * s_mid]       # n . Ad = the donor wall coordinate
                if wallsel == 'W0':
                    nt3 = [xs[0], 0.0, xs[2]]
                    At = W(LAT0, along)
                elif wallsel == 'W1':
                    nt3 = [-xs[0], 0.0, -xs[2]]
                    At = W(LAT1, along)
                else:
                    nt3 = [-zs[0], 0.0, -zs[2]]
                    At = W(along, DEP1)
                G = g_matrix(nd, (nt3[0], nt3[2]))
            made = {}
            for k, nm in zip(kit['ids'], kit['names']):
                e = B.ents[k - 1]
                Rd, Pd = B.fr[e]
                name = 'KLDress%d_%s_%s_%02d' % (si, kn, nm, len(site['dress']))
                nd_ = S.own(M, B, k, name, with_ctrls=False)
                Rn = S.mm(G, Rd)
                Pn = [At[0] + sum(G[0][j] * (Pd[j] - Ad[j]) for j in range(3)), Pd[1] + (floor_t - kit['floor']),
                      At[2] + sum(G[2][j] * (Pd[j] - Ad[j]) for j in range(3))]
                if kit.get('free'):
                    Pn[0] = At[0] + (Pd[0] - Ad[0]); Pn[2] = At[2] + (Pd[2] - Ad[2])
                M.place(nd_, Pn, S.stored(Rn))
                lo_, hi_, has = None, None, False
                if is_light(B, k):
                    # GUESS: ZLIGHT[2] is the baked shadow-mesh chunk of the DONOR room: not valid for a clone, emptied (other lights have it empty).
                    try:
                        M.set(nd_, None, {'ZLIGHT[2]': []})
                    except (StopIteration, ValueError, KeyError):
                        pass
                    lo_, hi_ = tuple(Pn[i] - 300 for i in range(3)), tuple(Pn[i] + 300 for i in range(3))
                    lights.append((nd_, lo_, hi_)); shop_lights.append(nd_)
                else:
                    rt = C._root(prm, e.model) if e.model else None
                    v = struct.unpack_from('<6f', rt, 0x20)
                    cs = [S.mv(Rn, [x, y, z]) for x in (v[0], v[3]) for y in (v[1], v[4]) for z in (v[2], v[5])]
                    lo_ = tuple(Pn[i] + min(c[i] for c in cs) for i in range(3)); hi_ = tuple(Pn[i] + max(c[i] for c in cs) for i in range(3))
                    props.append((nd_, lo_, hi_)); shop_props.append(nd_)
                    pc = [(sum((p[i] - o[i]) * xs[i] for i in range(3)), sum((p[i] - o[i]) * zs[i] for i in range(3)))
                          for p in [[(lo_, hi_)[(m >> j) & 1][j] for j in range(3)] for m in range(8)]]
                    la0, la1 = min(a for a, _b in pc), max(a for a, _b in pc)
                    de0, de1 = min(b for _a, b in pc), max(b for _a, b in pc)
                    if la0 < LAT0 - 3 or la1 > LAT1 + 3 or de0 < DEP0 - 3 or de1 > DEP1 + 3:
                        raise ValueError('shop %d kit %s %s leaves the interior: lat %.0f..%.0f depth %.0f..%.0f' % (si, kn, nm, la0, la1, de0, de1))
                    low = lo_[1] - floor_t < 250 and hi_[1] - floor_t > 0
                    if low:
                        for k0, k1, d0, d1 in keep:
                            if la0 < k1 and la1 > k0 and de0 < d1 and de1 > d0:
                                raise ValueError('shop %d kit %s %s (lat %.0f..%.0f depth %.0f..%.0f) hits a keep-out %s' % (si, kn, nm, la0, la1, de0, de1, (k0, k1, d0, d1)))
                made[k] = nd_
                grp.add(nd_)
                pts += [lo_, hi_]
                site['dress'].append(dict(kit=kn, node=nm, at=[round(v, 1) for v in Pn]))
            # kit-internal links as in the donor (light <-> prop pairs that are both in the kit)
            for k, nd_ in made.items():
                e = B.ents[k - 1]
                if e.links is not None:
                    wl[id(nd_)] = [(made[t_k], b) for t, b in e.links for t_k in [B.ents.index(t) + 1 if t is not None else None] if t_k in made]
        # the shop's lights light the shop: every light <-> every prop of the shop (bits 0) and the corridor's structure (ceiling 2, else 0)
        for lt in shop_lights:
            have_l = {id(t) for t, _b in wl.get(id(lt), [])}
            wl.setdefault(id(lt), [])
            for pr in shop_props:
                if id(pr) not in have_l:
                    wl[id(lt)].append((pr, 0))
                    wl.setdefault(id(pr), []).append((lt, 0))
            for sk_ in struct_ks:
                wl[id(lt)].append((B.ents[sk_ - 1], 2 if 'Ceiling' in sc.path[sk_] else 0))
                back[id(B.ents[sk_ - 1])].append((B.ents[sk_ - 1], lt))
        site['room_node'] = rk
        site['structure'] = [sc.path[j].rsplit('\\', 1)[-1] for j in struct_ks]

    if not grp.kids:
        if not moved:
            raise ValueError('nothing to do')
        # drawers only: no entity is added, so no slot id moves - a member-level patch of .prp / .gms / .buf (as kl_lanes_stage_1025.build_loot)
        gms, buf = B.scene.write()
        repl = {n: b for n, b in {B.ext['.prp']: sc.p.serialize(), B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf}.items() if b != B.files[n]}
        LS.patch_zip(src, dst, repl)
        Bn = F.Built(dst, 'F02')
        bad = []
        for g, (nm, pos) in DRAWERS.items():
            if any(abs(Bn.at(g)[i] - pos[i]) > 0.01 for i in range(3)) or Bn.sc.names[g] != nm:
                bad.append('drawer %s not at %s' % (nm, pos))
            for j in range(g, sc.end[g]):
                if any(abs((Bn.at(j)[i] - Bn.at(g)[i]) - (B.at(j)[i] - B.at(g)[i])) > 0.01 for i in range(3)):
                    bad.append('part %s moved against its group' % sc.path[j])
        for n in Bn.files:
            if n not in repl and Bn.files[n] != B.files[n]:
                bad.append('member %s changed' % n)
        if len(Bn.ents) != n_before or bad:
            raise ValueError('read-back: %s' % (bad or 'entity count'))
        rep = collections.OrderedDict(solo=solo, drawers=drawers, dress=dress, source=src, source_md5=have, out=dst, out_md5=S.md5(dst),
                                      members_changed=sorted(repl), entities_before=n_before, entities_after=n_before, entities_added=0,
                                      moved_drawers=moved, sites=sites)
        log('kl_dm02_coop_1026 drawers only: members %s -> %s (%s)' % (' '.join(rep['members_changed']), dst, rep['out_md5']))
        return rep
    q, order = M.scene([grp])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'coop')
    data = Jn.p.serialize()
    back_p = F.Prp(data)
    if back_p.serialize() != data or len(back_p.nodes()) != len(Jn.nodes):
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
    # links (entities exist now). New light/prop lists; the corridor's structure entities get the way back (light, 0) behind their stored list.
    nlinks = 0
    for n in grp.walk():
        if id(n) in wl:
            e = made_e[id(n)]
            e.links = [((made_e[id(t)] if not isinstance(t, kl_scene.Entity) else t), b) for t, b in wl[id(n)]]
            nlinks += len(e.links)
    for key, lst in back.items():
        for se, lt in lst:
            se.links = list(se.links or []) + [(made_e[id(lt)], 0)]
            nlinks += 1
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
    nmoved = sum(1 for a, b in ids.items() if a != b)
    root0, root1, root3 = octn.rooms[0][0], octn.rooms[0][1], octn.rooms[0][3]
    if root0 is None or root3 is None or (lights and root1 is None):
        raise ValueError('the root has no tree 0 / 1 / 3')
    # GUESS (as kl_dm02_shops_1024): props in the root's tree 0 (where the shop counters are listed), lights in its tree 1, the group in its tree 3.
    if props:
        octn.rooms[0][0] = O.join_trees(root0, C._tree([(slot1[made_e[id(n)]] + 2, lo, hi) for n, lo, hi in props]))
        octn.rooms[0][0].check()
    if lights:
        octn.rooms[0][1] = O.join_trees(root1, C._tree([(slot1[made_e[id(n)]] + 2, lo, hi) for n, lo, hi in lights]))
        octn.rooms[0][1].check()
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
    # ---- read back: a fresh load must show the drawers where they belong and every new node where it was placed
    Bn = F.Built(dst, 'F02')
    bad = []
    for g, (nm, pos) in (DRAWERS.items() if drawers else ()):
        gn = [k for k in range(1, len(Bn.sc.names)) if Bn.sc.names[k] == nm]
        if len(gn) != 1 or any(abs(Bn.at(gn[0])[i] - pos[i]) > 0.01 for i in range(3)):
            bad.append('drawer %s not at %s' % (nm, pos))
        else:
            for j in range(gn[0], Bn.sc.end[gn[0]]):
                d0 = [Bn.at(j)[i] - Bn.at(gn[0])[i] for i in range(3)]
                jo = [k for k in range(1, len(sc.names)) if sc.names[k] == Bn.sc.names[j] and sc.path[k].endswith(Bn.sc.path[j].split('KL_Shops!')[-1])]
                if len(jo) == 1:
                    d1 = [B.at(jo[0])[i] - B.at(g)[i] for i in range(3)]
                    if any(abs(d0[i] - d1[i]) > 0.01 for i in range(3)):
                        bad.append('drawer part %s moved against its group' % Bn.sc.path[j])
    if len(Bn.ents) != n_before + len(order):
        bad.append('entity count %d != %d' % (len(Bn.ents), n_before + len(order)))
    if bad:
        raise ValueError('read-back: ' + '; '.join(bad))
    rep = collections.OrderedDict(
        solo=solo, drawers=drawers, dress=dress, source=src, source_md5=have, out=dst, out_md5=S.md5(dst), members_changed=changed,
        entities_before=n_before, entities_after=len(ents), entities_added=len(order),
        added_props=len(props), added_lights=len(lights), added_solo=sum(1 for s_ in sites if s_['solo']), links_written=nlinks,
        ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=nmoved, prm_model_roots_repointed=repointed,
        slot_id_faults_before=pre, slot_id_faults_after=post, moved_drawers=moved, sites=sites)
    log('kl_dm02_coop_1026 solo=%s drawers=%s dress=%s: %d entities added (%d props, %d lights, %d links) %d -> %d, members %s, %d slot ids moved -> %s (%s)'
        % (solo, drawers, dress, len(order), len(props), len(lights), nlinks, n_before, len(ents), ' '.join(changed), nmoved, dst, rep['out_md5']))
    return rep


VARIANTS = collections.OrderedDict([('coop_only', dict(solo=False, drawers=True, dress=False)),
                                    ('coop_solo', dict(solo=True, drawers=True, dress=True)),          # recommended
                                    ('dress_only', dict(solo=False, drawers=False, dress=True))])


LIVE_MD5 = '1dd1460913ee039f6e28f7c071c04be6'      # the live DM02 zip that already holds KL_Coop! (2026-10-26 02:20); patch() works on this one


def patch(src, dst, auto=False, force=False, log=print):
    """2026-10-26 (solo lift did not open the shutter live; cause not provable offline): rewrite the three KLCoop<N>!SoloLift PlayerActions in a zip that
    already holds KL_Coop!. Only the .prp changes (no node added or moved; .gms/.buf/.oct/.rmi/.rmc/.prm byte-identical).
      field 12 = 1  re-enable after use (the donor has 0: ONE use ever, so a try that was spent on a missed press never comes back).
      auto: field 13 = 1  fires WITHOUT the key as soon as a player stands in the box (hedge for a use-key edge the script or player misses).
    GUESS: both fields behave as the ZPlayerAction map in re/engine_facts.md says (12 -> +0x5e copied to +0x54/+0x7c by 0x8c8b50; 13 -> +0x5f).
    The action list [PathBlocker, shutter DeactivateGeom] is NOT touched: it is the CoopAirlock's own completion list."""
    have = S.md5(src)
    if have != LIVE_MD5 and not force:
        raise ValueError('%s: md5 %s is not the live DM02 zip (%s)' % (src, have, LIVE_MD5))
    B = F.Built(src, 'F02')
    sc = B.sc
    hits = [k for k in range(1, len(sc.names)) if sc.names[k].endswith('!SoloLift')]
    if len(hits) != 3:
        raise ValueError('%d SoloLift nodes, not 3' % len(hits))
    for k in hits:
        i = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'PlayerAction']
        if len(i) != 1:
            raise ValueError('%s: %d PlayerActions' % (sc.names[k], len(i)))
        def fn(us):
            if len(us) != 21 or us[12][0][0] != 6 or us[13][0][0] != 6 or len(us[1]) != 3:
                raise ValueError('PlayerAction is not the clone of the L03 use box')
            us[12] = [(6, bytes([1]))]
            if auto:
                us[13] = [(6, bytes([1]))]
        kl_fa.edit(sc, k, i[0], fn)
    data = sc.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(sc.p.nodes()):
        raise ValueError('the patched .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = data
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    Bn = F.Built(dst, 'F02')
    got = []
    for k in hits:
        for nm, body in Bn.sc.nodes[k]['ctrls']:
            if Bn.sc.p.key(nm) == 'PlayerAction':
                v = [kl_fa.value(Bn.sc, u) for u in kl_fa.units(body[1:-1])]
                got.append((v[1], v[8], v[12], v[13]))
                if v[12] != 1 or v[13] != int(auto) or v[8] != 1:
                    raise ValueError('read-back %s' % (v,))
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        diff = sorted(n for n in a.namelist() if a.read(n) != b.read(n))
    if diff != [B.ext['.prp']]:
        raise ValueError('members changed: %s' % diff)
    rep = collections.OrderedDict(mode='patch', auto=auto, source=src, source_md5=have, out=dst, out_md5=S.md5(dst), members_changed=diff,
                                  solo=[h[0] for h in got], fields_12_13=[(h[2], h[3]) for h in got], md5_in=have)
    log('kl_dm02_coop_1026 patch auto=%s: %d SoloLift PlayerActions (field 12=1, 13=%d) -> %s (%s)' % (auto, len(hits), int(auto), dst, rep['out_md5']))
    return rep


def stage_patch(src, out, scratch=None, log=print):
    h = S.md5(src)
    if h != LIVE_MD5:
        raise SystemExit('input md5 %s is not the live %s' % (h, LIVE_MD5))
    LO.MAPS['DM02'] = dict(slot='F02', zip='F02_Main.zip')
    LO.TAG = TAG_SOLO
    install = LS.INSTALL_PY.replace('van-lane + loot', 'co-op solo lift fix').replace('tools/kl_lanes_stage_1025.py', 'tools/kl_dm02_coop_1026.py').replace('2026-10-25', '2026-10-26')
    reps = {}
    for name, auto in (('coop_solo', False), ('coop_solo_auto', True)):
        d = os.path.join(out, name)
        LO.rmtree(d)
        os.makedirs(d)
        rep = patch(src, os.path.join(d, 'F02_Main.zip'), auto=auto, log=log)
        with open(os.path.join(d, 'install.py'), 'w', newline='\n') as fh:
            fh.write(install % dict(map='DM02', zip='F02_Main.zip', tag=TAG_SOLO, game=LS.GAME, old=h, new=rep['out_md5']))
        with open(os.path.join(d, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        if scratch:
            LO.rehearse(d, 'DM02', src, rep['out_md5'], h, scratch, log)
        reps[name] = rep
    return reps


def stage(src, out, scratch=None, log=print):
    h = S.md5(src)
    if h != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (h, SRC_MD5))
    LO.MAPS['DM02'] = dict(slot='F02', zip='F02_Main.zip')
    LO.TAG = TAG
    install = LS.INSTALL_PY.replace('van-lane + loot', 'co-op shutter + shop dressing').replace('tools/kl_lanes_stage_1025.py', 'tools/kl_dm02_coop_1026.py').replace('2026-10-25', '2026-10-26')
    reps = {}
    for name, opt in VARIANTS.items():
        d = os.path.join(out, name)
        LO.rmtree(d)
        os.makedirs(d)
        z = os.path.join(d, 'F02_Main.zip')
        rep = build(src, z, log=log, **opt)
        rep['variant'] = name
        rep['md5_in'] = h
        with open(os.path.join(d, 'install.py'), 'w', newline='\n') as fh:
            fh.write(install % dict(map='DM02', zip='F02_Main.zip', tag=TAG, game=LS.GAME, old=h, new=rep['out_md5']))
        with open(os.path.join(d, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        if scratch:
            LO.rehearse(d, 'DM02', src, rep['out_md5'], h, scratch, log)
        reps[name] = rep
    return reps


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'patch':
        stage_patch(a[1], a[2], a[a.index('--rehearse') + 1] if '--rehearse' in a else None)
        return 0
    if len(a) < 3 or a[0] != 'stage':
        print(__doc__)
        return 2
    stage(a[1], a[2], a[a.index('--rehearse') + 1] if '--rehearse' in a else None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
