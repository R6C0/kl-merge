#!/usr/bin/env python3
"""
kl_interact_graft.py - Dog Days' INTERACTIVE props grafted onto a Dead Men map (agent, 2026-10-24, re/interactivity.md step 3/4).

    python kl_interact_graft.py spots <in.zip>                      the extinguisher spots chosen for the map (nothing written)
    python kl_interact_graft.py build <in.zip> <out.zip> [--ext N] [--doors K,K,..] [--md5 HEX] [--force] [--keep-door-leaf]
        --ext N       number of fire extinguishers (default: the map's plan in PLAN, else 4)
        --doors K,..  .prp node numbers of the static door leaves to replace with a KICK DOOR (default: the map's plan)
        --md5 HEX     refuse an input whose md5 is not this (PLAN pins the live md5 of each map); --force skips the pin

WHAT IT DOES (one pass, idempotent: an input that already holds the KL_Interact! group is written out unchanged)
  Both templates are Dog Days stock nodes (F04 FX0900_ALL_FireExtinguisher_01!*, F03 PC0800_ALL_KickableDoor_*).
  The graft puts ONE top group KL_Interact!1 at the origin into the map; under it one group per instance (KL_Ext_n, KL_Door_n).
  - The nodes of a template are cloned out of the stock .prp with every scene path rewritten (kl_prpjoin._intern(rename=)) from the
    template's parent path to the instance group's; the lists that named dropped nodes are filtered (see EXT_DROP).
  - Models: the closure of each model root in the donor .prm is appended (kl_prmgraph.append) with its materials / textures
    (kl_texmat) and its .oct records (kl_octree.append_records); the map's own roots are re-pointed at the moved records.
  - Slot ids: the .gms is rewritten by kl_scene, every slot id of .oct / .rmi / .rmc is sent through old slot -> new slot, the new
    top group is listed in the root group tree (room 0, tree 3) and the room sets are compared before and after.
  - Collision: a Havok placement per instance with a fresh REF label (extinguisher = type 2 rigid body, one shape record for all
    of them + one .hrd record each; door = type 4 key-framed body). The door's static leaf in the map loses its collision
    (kl_escape.cut_collision) and its entity is removed.
Everything the offline checks cannot prove (what the engine does with a grafted can or door) is listed in re/interactivity.md.
"""
import collections, hashlib, json, math, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T, kl_gms, kl_scene, kl_hvk
import kl_prpjoin as J
import kl_octree as O

TOP = 'KL_Interact!1'
EXT_DONOR, EXT_PARENT = 'F04', 'ROOT\\Locations/F04/F04_Locations.zip\\Locations/F04/F04_LOC_Outside.zip\\F04_Outside_MazeMarketsRightPath'
EXT_CAN = 5270                                         # F04 node numbers (.prp), see re/interactivity.md
EXT_KEEP = [5270, 5269, 5271] + list(range(5124, 5134)) + [5136, 5137, 5138]
EXT_DROP = ('FX0900_ALL_FireExtinguisher_01!ShatterTrigger', 'FX0900_ALL_FireExtinguisher_01!Shards')   # the glass-pane splinters
EXT_PREFIX = 'FX0900_ALL_FireExtinguisher_01!'
EXT_TREE0 = [5125, 5129]       # the template nodes the F04 .oct lists in tree 0 of its room 16 (read with a probe, 2026-10-24): static, pool group 0

# per map: the live md5 the plan was made against (CLAUDE.md chain), extinguishers, kick-door leaves (.prp node numbers)
PLAN = {
    # DM01 (Hot Coffee), second pass 1025: built on the shop-v2 + carexit zip (the graft is idempotent, so it starts from the zip WITHOUT
    # KL_Interact!1). Three doors where a Dog Days designer puts them: the diner's BACK EXIT to the alley (the FA authors' own leaf 2433, swung
    # shut), the STAFF CORRIDOR door between the two diner halves (an empty 130 cm doorway: virtual host), the SHOP's back door (leaf 961,
    # swung shut). The sunlight cards 1174 / 942 that painted light through the open leaves are dropped. Extinguishers: beside those doors
    # and at the counter / east fight (spots_near targets, see DM01_SPOTS).
    'DM01':  dict(slot='F01', md5='02d2a481a921fb7a0b0cbd4c7f16485c', ext=5,
                  doors=[('snap', 2433, (1.0, 0.0, 0.0), 21909.5), ('at', (4700.0, 0.0, 22160.0), (0.0, 0.0, 1.0)), ('snap', 961, (1.0, 0.0, 0.0), 21914.0)],
                  extra_drop=[1174, 942],
                  spots_near=[(6300.0, 22930.0), (4235.0, 21960.0), (4645.0, 22230.0), (3035.0, 21965.0), (6620.0, 22420.0)]),
    'DM01B': dict(slot='F03', md5='0a34b035c089c5e3b656a658398c5348', ext=4, doors=[1373, 7169, 8844, 7166, 7167]),
    'DM03A': dict(slot='F07', md5='89256d16986513d06f81d7609abbf6aa', ext=4, doors=[6521, 3594, 3647, 3737, 3790]),
    'DM06':  dict(slot='F04', md5='2faf474222bb71e22483cf9e116984f7', ext=4, doors=[]),
    'DM09':  dict(slot='F06', md5='e2c7d5bda12d7d97651c04496bc8f05e', ext=4, doors=[]),
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def sget(M, tok):
    return M.p.keys[struct.unpack('<I', tok[1])[0]]


# ------------------------------------------------------------------ donors
class Donor:
    """A stock Dog Days level: its zip members, .prm / .MAT / .TEX / .oct / .HVK / .hrd, the scene and the entities."""
    _cache = {}

    def __init__(self, level):
        import kl_fa_bots as F
        self.level = level
        self.sc, self.ents = F.Maker.level(level)
        with zipfile.ZipFile(J.level_zip(level, 'dd')) as z:
            m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
            self.files = {e: z.read(n) for e, n in m.items()}
        self.prm = G.read(self.files['.prm'], 'dd')
        self.mat, self.tex = T.read_mat(self.files['.MAT']), T.read_tex(self.files['.TEX'])
        self.oct = O.Oct.parse(self.files['.oct'])
        self.hvk = kl_hvk.Hvk(self.files['.HVK'])
        self.head = kl_scene.Scene(kl_gms.unpack(self.files['.gms']), self.files['.buf']).head        # the .buf head the KEYS offsets address

    @classmethod
    def get(cls, level):
        if level not in cls._cache:
            cls._cache[level] = cls(level)
        return cls._cache[level]

    def ent(self, k):
        return self.ents[k - 1]


# ------------------------------------------------------------------ cloning with a path rewrite
def clone(M, don, k, name, rename):
    """The donor node k as a new Node, every scene path rewritten by `rename`."""
    import kl_fa_bots as F
    sc = don.sc
    n = sc.nodes[k]
    props = J._intern(n['props'], sc.p.keys, M.p.ix, M.p.keys, rename)
    ctrls = [(J._intern([nm], sc.p.keys, M.p.ix, M.p.keys)[0], J._intern(body, sc.p.keys, M.p.ix, M.p.keys, rename)) for nm, body in n['ctrls']]
    node = F.Node(name, sc.tids[k], props, ctrls, don.ent(k))
    node.model = don.ent(k).model
    node.donor = k
    return node


def list_filter(M, node, ctrl, field, keep):
    """Drop the strings of a reference-list field for which keep(string) is false."""
    import kl_fa_bots as F
    if ctrl is None:
        obj, lab = node.props, J.labels('dd', J.schema('dd').geoms.get(node.tid))
        j = lab.index(field) if isinstance(field, str) else field
    else:
        i = next(i for i, (nm, _b) in enumerate(node.ctrls) if M.p.key(nm) == ctrl)
        obj, j = node.ctrls[i][1], field
    us = [list(u) for u in F.units(obj[1:-1])]
    u = us[j]
    if u[0][0] != 0x04:
        raise ValueError('%s field %s is not a list' % (node.name, field))
    strs = [M.p.keys[struct.unpack('<I', t[1])[0]] for t in u[1:]]
    kept = [s for s in strs if keep(s)]
    if len(kept) != len(strs):
        M.set(node, ctrl, {field: kept})
    return len(strs) - len(kept)


def shift(M, node, d):
    """Move a node's place by d (ZGEOM[2] and the entity's translation), keeping its rotation."""
    p = struct.unpack_from('<3f', node.trans)
    new = tuple(p[i] + d[i] for i in range(3))
    M.set(node, None, {'ZGEOM[2]': list(new)})
    node.trans = struct.pack('<3f', *new) + node.trans[12:]
    node.pos = new


# ------------------------------------------------------------------ the extinguisher
def make_extinguisher(M, B, don, n, at, tmpl_ok):
    """One instance -> (group Node, can Node, [model-bearing nodes]). `at` = world place of the can's origin."""
    import kl_fa_cover as CV, kl_fa_bots as F
    gk = CV.group_form(B)
    grp = CV._node(M, B, gk, 'KL_Ext_%d' % n)
    M.place(grp, (0.0, 0.0, 0.0))
    newp = TOP_PATH + '\\' + grp.name + '\\'
    old = EXT_PARENT + '\\'
    rn = lambda s: (newp + s[len(old):]) if s.lower().startswith(old.lower()) else s
    can0 = struct.unpack_from('<3f', don.ent(EXT_CAN).trans)
    d = tuple(at[i] - can0[i] for i in range(3))
    byk, kids = {}, []
    for k in EXT_KEEP:
        nd = clone(M, don, k, don.sc.names[k], rn)
        byk[k] = nd
        par = don.sc.parent[k]
        (byk[par] if par in byk else grp).add(nd)
        if don.sc.parent[k] not in byk:           # a top-level node of the template: its place is a world place
            shift(M, nd, d)
    dropped = lambda s: any(x.lower() in s.lower() for x in EXT_DROP)
    can = byk[EXT_CAN]
    cuts = list_filter(M, can, None, 'ZHavokRigidBody[13]', lambda s: not dropped(s))
    cuts += list_filter(M, byk[5269], 'ActivateGeom', 1, lambda s: not dropped(s))
    # ASSUMPTION (guess): ZHavokRigidBody[14] (a u32, 0x00068690 in the stock can) is left as the stock value.
    # emitters whose template the target lacks are dropped
    gone = []
    for k in list(byk):
        nd = byk[k]
        if nd.tid == 0x2000ff:
            tpl = [sget(M, t) for t in nd.props if t[0] == 0x0c]
            nm = _emitter_template(M, nd)
            if nm and nm.lower() not in tmpl_ok:
                gone.append(nd)
    for nd in gone:
        for k, v in list(byk.items()):
            if v is nd:
                del byk[k]
        for v in grp.walk():
            if nd in v.kids:
                v.kids.remove(nd)
    return grp, can, byk, [g.name for g in gone], cuts


def _emitter_template(M, nd):
    import kl_fa_bots as F
    lab = J.labels('dd', J.schema('dd').geoms.get(nd.tid))
    j = lab.index('ZParticleEmitter[34]')
    us = list(F.units(nd.props[1:-1]))
    u = us[j]
    return M.p.keys[struct.unpack('<I', u[0][1])[0]] if u[0][0] in (0x0c, 0x0e) else None


TOP_PATH = 'ROOT\\' + TOP


# ------------------------------------------------------------------ spots
def ext_spots(B, nav, n, apart=2500.0, near=800.0, wall_dist=45.0):
    """n places for extinguishers: a short way inside the walls of the walk mesh, near the guards' defend places (the fights).
    -> [(x, y, z, wall length)] deterministic."""
    import re
    sc = B.sc
    fights = []
    for k in range(1, len(sc.nodes)):
        if re.search(r'Pos#\d+$', sc.path[k]):
            x, y, z = B.at(k)
            if nav.at(x, y, z, dy=120.0):
                fights.append((x, y, z))
    big = collections.Counter(nav.part[i] for i in range(len(nav.pv)) if nav.ok[i]).most_common(1)[0][0]
    cands = []
    for i, vs in enumerate(nav.pv):
        if not nav.ok[i] or nav.part[i] != big:
            continue
        cx, cz = nav.mid[i][0], nav.mid[i][2]
        for e, j in enumerate(nav.en[i]):
            if j >= 0:
                continue
            a, b = vs[e], vs[(e + 1) % len(vs)]
            L = math.hypot(b[0] - a[0], b[2] - a[2])
            if L < 150.0:
                continue
            mx, mz = (a[0] + b[0]) / 2, (a[2] + b[2]) / 2
            nx, nz = -(b[2] - a[2]) / L, (b[0] - a[0]) / L
            if nx * (cx - mx) + nz * (cz - mz) < 0:
                nx, nz = -nx, -nz
            x, z = mx + nx * wall_dist, mz + nz * wall_dist
            if not nav.inside(i, x, z):
                continue
            y = nav.height(i, x, z)
            # the fights within reach on the same floor
            score = sum(1 for f in fights if abs(f[1] - y) < 250 and math.hypot(f[0] - x, f[2] - z) < near)
            if score:
                cands.append((-score, -L, round(x, 1), round(z, 1), round(y, 1)))
    cands.sort()
    out = []
    for s, nL, x, z, y in cands:
        if all(math.hypot(x - o[0], z - o[2]) > apart or abs(y - o[1]) > 250 for o in out):
            out.append((x, y, z, -nL))
        if len(out) >= n:
            break
    return out


def wall_cands(B, nav, wall_dist=45.0, min_len=150.0):
    """Every free wall edge (no neighbour polygon) of the walk mesh that is >= min_len long -> [(x, y, z, length)], a point wall_dist inside
    the mesh from the edge's middle (the same candidates ext_spots ranks by fights)."""
    out = []
    big = collections.Counter(nav.part[i] for i in range(len(nav.pv)) if nav.ok[i]).most_common(1)[0][0]
    for i, vs in enumerate(nav.pv):
        if not nav.ok[i] or nav.part[i] != big:
            continue
        cx, cz = nav.mid[i][0], nav.mid[i][2]
        for e, j in enumerate(nav.en[i]):
            if j >= 0:
                continue
            a, b = vs[e], vs[(e + 1) % len(vs)]
            L = math.hypot(b[0] - a[0], b[2] - a[2])
            if L < min_len:
                continue
            mx, mz = (a[0] + b[0]) / 2, (a[2] + b[2]) / 2
            nx, nz = -(b[2] - a[2]) / L, (b[0] - a[0]) / L
            if nx * (cx - mx) + nz * (cz - mz) < 0:
                nx, nz = -nx, -nz
            x, z = mx + nx * wall_dist, mz + nz * wall_dist
            if nav.inside(i, x, z):
                out.append((round(x, 1), round(nav.height(i, x, z), 1), round(z, 1), L))
    return out


def spot_near(B, nav, targets, keep_off=(), off=130.0, r=600.0, apart=300.0):
    """One extinguisher spot per (x, z) target: the wall_cands point nearest the target within r that is at least `off` from every
    keep_off point (the door hinges: the can must not stand in a door's swing) and `apart` from the spots already chosen. Deterministic.
    A target with no candidate raises (the plan then needs another target rather than a silent drop)."""
    cands = wall_cands(B, nav)
    out = []
    for tx, tz in targets:
        best = None
        for c in cands:
            d = math.hypot(c[0] - tx, c[2] - tz)
            if d > r or any(math.hypot(c[0] - k[0], c[2] - k[2]) < off for k in keep_off):
                continue
            if any(math.hypot(c[0] - o[0], c[2] - o[2]) < apart and abs(c[1] - o[1]) < 250 for o in out):
                continue
            if best is None or (d, c) < best[0]:
                best = ((d, c), c)
        if best is None:
            raise ValueError('no wall spot within %d cm of target (%d, %d)' % (r, tx, tz))
        out.append(best[1])
    return out


# ------------------------------------------------------------------ door hosts
BS = chr(92)
DOOR_H = 220.0                      # the donor leaf's height (F03 model 13862, box y 0..220) and width
DOOR_W = 120.0


def _mat_vec(R, v):
    return tuple(sum(R[i][j] * v[j] for j in range(3)) for i in range(3))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def door_hosts(B, nav, w_tol=(110.0, 126.0), h_tol=(228.0, 246.0), max_thick=40.0):
    """The static door leaves of a map that a kick door could replace -> [dict(k, name, R, p, bb, hinge, ...)].
    A leaf: ZSTDOBJ with a model, no raw data (nothing animates it), a name with 'door' / 'dor', a model box about as wide
    as the donor leaf (110..126), 228..246 tall, thinner than 40, and walk-mesh on AT LEAST ONE side of it (120 cm out along its
    thickness axis, within 150 cm of its base height: a closed door has mesh only where the heisters come from).
    hinge = the end of the width axis whose distance from the entity's own origin is smaller (the stock leaves hinge at
    their origin; GUESS for the others), c_x = world direction FROM the free end TO the hinge."""
    prm = G.read(B['.prm'], 'dd')
    out = []
    for k, e in enumerate(B.ents, 1):
        if not e.model or e.tid != 0x200002 or e.raw or e.kids:
            continue
        last = B.sc.path[k].rsplit(BS, 1)[-1].lower()
        if 'door' not in last and 'dor' not in last:
            continue
        c = prm.chunks[e.model] if e.model < len(prm.chunks) else b''
        if len(c) < 0x38:
            continue
        bb = struct.unpack_from('<6f', c, 0x20)
        ext = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]
        if not (h_tol[0] <= ext[1] <= h_tol[1]):
            continue
        ax = 0 if w_tol[0] <= ext[0] <= w_tol[1] and ext[2] <= max_thick else 2 if w_tol[0] <= ext[2] <= w_tol[1] and ext[0] <= max_thick else None
        if ax is None:
            continue
        th = 2 - ax
        R, P = B.fr[e]
        lo, hi = bb[ax], bb[ax + 3]
        end = hi if abs(hi) <= abs(lo) else lo
        sign = 1.0 if end == hi else -1.0                  # c_x = sign * (width axis): points from the free end to the hinge
        axis_l = [0.0, 0.0, 0.0]; axis_l[ax] = sign
        thick_l = [0.0, 0.0, 0.0]; thick_l[th] = 1.0
        cx = _mat_vec(R, axis_l)
        cy = _mat_vec(R, (0.0, 1.0, 0.0))
        cz = _cross(cx, cy)
        org_l = [0.0, bb[1], 0.0]; org_l[ax] = end; org_l[th] = (bb[th] + bb[th + 3]) / 2
        hinge = tuple(P[i] + _mat_vec(R, org_l)[i] for i in range(3))
        mid_l = [(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2]
        mid = tuple(P[i] + _mat_vec(R, mid_l)[i] for i in range(3))
        n = _mat_vec(R, thick_l)
        sides = []
        for sgn in (1.0, -1.0):
            x, z = mid[0] + sgn * 120.0 * n[0], mid[2] + sgn * 120.0 * n[2]
            sides.append(nav.at(x, hinge[1], z, dy=150.0))
        if not any(sides):                  # a closed door has walk-mesh only on the side the heisters come from: ONE side is enough
            continue
        out.append(dict(k=k, name=B.sc.path[k].split(BS, 1)[-1], ref=e.ref, model=e.model, R=(cx, cy, cz), hinge=hinge, mid=mid,
                        height=ext[1], width=ext[ax], thick=ext[th], bb=bb))
    return out


def stored_rot(cx, cy, cz):
    """The 9 floats of ZGEOM[1] for a frame whose local axes in the world are cx, cy, cz: rows are local Z, Y, X (kl_fa_bots.frames)."""
    return list(cz) + list(cy) + list(cx)


def pick_doors(B, nav, n=5, apart=1300.0, near=1500.0, hosts=None):
    """n door hosts, deterministic: the most guard places (Pos#NN) within `near` on the same floor first, at least `apart` apart;
    only hosts of the map's commonest height class (the one door model is scaled to one height per map)."""
    import re
    hosts = hosts if hosts is not None else door_hosts(B, nav)
    if not hosts:
        return []
    fights = []
    for k in range(1, len(B.sc.nodes)):
        if re.search(r'Pos#\d+$', B.sc.path[k]):
            fights.append(B.at(k))
    cls = collections.Counter(round(h['height']) for h in hosts).most_common(1)[0][0]
    hosts = [h for h in hosts if abs(h['height'] - cls) <= 3.0]
    for h in hosts:
        h['score'] = sum(1 for f in fights if abs(f[1] - h['hinge'][1]) < 250 and math.hypot(f[0] - h['hinge'][0], f[2] - h['hinge'][2]) < near)
    hosts.sort(key=lambda h: (-h['score'], h['k']))
    out = []
    for h in hosts:
        if all(math.hypot(h['hinge'][0] - o['hinge'][0], h['hinge'][2] - o['hinge'][2]) > apart or abs(h['hinge'][1] - o['hinge'][1]) > 250 for o in out):
            out.append(h)
        if len(out) >= n:
            break
    return out


def virtual_host(hinge, cx, width=DOOR_W, height=240.0):
    """A kick door for an EMPTY doorway (no static leaf to replace): k = ref = None. hinge = the leaf's hinge point (the jamb end, base,
    thickness middle), cx = world direction FROM the free end TO the hinge (the leaf lies along -cx from the hinge). The frame is y up."""
    cx = tuple(float(v) for v in cx)
    cy = (0.0, 1.0, 0.0)
    return dict(k=None, name='(doorway)', ref=None, model=None, R=(cx, cy, _cross(cx, cy)), hinge=tuple(hinge), mid=tuple(hinge),
                height=height, width=width, thick=5.0, bb=None, virtual=True)


def snap_host(h, cx, hinge_z=None):
    """The host leaf swung SHUT: the same hinge point (a swing does not move it), the frame turned so that the leaf lies along the
    doorway (cx as given, y up). Dead Men's FA leaves 2433 / 961 stand open in the data (rotated about 120 / 180 degrees)."""
    cx = tuple(float(v) for v in cx)
    cy = (0.0, 1.0, 0.0)
    hinge = h['hinge'] if hinge_z is None else (h['hinge'][0], h['hinge'][1], float(hinge_z))     # hinge_z: the wall's middle (read off the wall model's thin face), a guess of a few cm
    return dict(h, R=(cx, cy, _cross(cx, cy)), hinge=hinge, snapped=True)


def resolve_doors(B, nav, doors):
    """The PLAN / --doors entries -> host dicts. An int = that static leaf as it stands; ('snap', k, cx) = that leaf swung shut along cx;
    ('snap', k, cx, hinge_z) also sets the hinge's z; ('at', (x, y, z), cx) = a virtual host at that hinge point (an empty doorway)."""
    allh = {h['k']: h for h in door_hosts(B, nav)}
    out = []
    for d in doors:
        if isinstance(d, int):
            d = ('leaf', d)
        if d[0] in ('leaf', 'snap'):
            if d[1] not in allh:
                raise ValueError('not a door leaf of this map: %s' % (d[1],))
            out.append(snap_host(allh[d[1]], d[2], d[3] if len(d) > 3 else None) if d[0] == 'snap' else allh[d[1]])
        elif d[0] == 'at':
            out.append(virtual_host(d[1], d[2]))
        else:
            raise ValueError('door spec %r' % (d,))
    return out


# ------------------------------------------------------------------ the kick door
DOOR_DONOR = 'F03'
DOOR_PARENT = BS.join(['ROOT', 'Locations/F03/F03_Locations.zip', 'Locations/F03/F03_LOC_Inside.zip', 'F03_Office_B_Low', 'PC0800_ALL_KickableDoor_E_01'])
DOOR_GRP = 4167                         # F03 node numbers (.prp): the group, its 22 kids (4168 .. 4189), and the leaf (4189)
DOOR_KIDS = list(range(4168, 4190))
DOOR_LEAF = 4189
DOOR_SHAPE = 234                        # F03 .HVK shape of the leaf (type 4 key-framed, 8 vertices in metres: x -1.2 .. 0, y 0 .. 2.2, z +-0.02)
DOOR_VTX = (13857, 13852)               # the leaf model's two vertex chunks (128 + 24 vertices of 40 bytes, position first)
KEYS_AT = 40                            # position of the six KEYS offsets in the leaf's 64-byte raw block (kl_graft.keys_tracks)


def door_keys(don):
    """(first offset, end offset) of the .buf head region the stock leaf's KEYS tracks use: the six offsets in the leaf's raw block and
    the tracks tile that region (480 + 160 + 64 + 720 bytes in F03); a track ends where the next larger offset of ANY entity begins."""
    import kl_graft
    raw = don.ent(DOOR_LEAF).raw
    (_p, offs), = kl_graft.keys_tracks(raw)
    every = sorted({o for e in don.ents if e.raw for _p2, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(don.head)})
    lo = min(offs)
    hi = next(x for x in every if x > max(offs))
    return offs, lo, hi


def scaled_door_prm(don, sx, sy):
    """A copy of the donor .prm whose leaf model (root box, both vertex chunks) is scaled by (sx, sy, 1) about its origin (the hinge
    end, base): the stock leaf is 120 wide (x -120 .. 0) and 220 high; Dead Men's door leaves are 110 .. 126 by 228 .. 246.
    GUESS: the model's .oct record (the tree over the triangle ranges) keeps its stock box; it is at most ~8% off."""
    p = G.Prm(don.prm.game, list(don.prm.chunks), list(don.prm.refs))
    p.free = list(don.prm.free)
    root = bytearray(p.chunks[13862])
    for off, f in ((0x20, sx), (0x24, sy), (0x2c, sx), (0x30, sy)):
        struct.pack_into('<f', root, off, struct.unpack_from('<f', root, off)[0] * f)
    p.chunks[13862] = bytes(root)
    for v in DOOR_VTX:
        c = bytearray(p.chunks[v])
        nv = {13857: 128, 13852: 24}[v]
        for i in range(nv):
            x, y = struct.unpack_from('<2f', c, 40 * i)
            struct.pack_into('<2f', c, 40 * i, x * sx, y * sy)
        p.chunks[v] = bytes(c)
    return p


def make_door(M, B, don, n, host, tmpl_ok):
    """One kick door -> (group Node, {donor node number: Node}, names of the dropped nodes). The group stands at the host leaf's hinge with
    its frame (local x from the free end to the hinge, as the stock group's: the leaf extends along local -x); the stock kids keep their
    local places. Emitters whose particle template the map lacks are dropped (the lists naming them are filtered later: drop_names)."""
    import kl_fa_cover as CV
    gk = CV.group_form(B)
    grp = CV._node(M, B, gk, 'KL_Door_%d' % n)
    M.place(grp, host['hinge'], stored_rot(*host['R']))
    newp = TOP_PATH + BS + grp.name + BS
    old = DOOR_PARENT + BS
    rn = lambda s: (newp + s[len(old):]) if s.lower().startswith(old.lower()) else s
    byk = {}
    for k in DOOR_KIDS:
        nd = clone(M, don, k, don.sc.names[k], rn)
        byk[k] = nd
        par = don.sc.parent[k]
        (byk[par] if par in byk else grp).add(nd)
    gone = []
    for k in list(byk):
        nd = byk[k]
        if nd.tid == 0x2000ff:
            nm = _emitter_template(M, nd)
            if nm and nm.lower() not in tmpl_ok:
                gone.append((k, nd))
    for k, nd in gone:
        del byk[k]
        for v in grp.walk():
            if nd in v.kids:
                v.kids.remove(nd)
    return grp, byk, [don.sc.path[k][len(DOOR_PARENT) + 1:] for k, nd in gone], newp


def drop_names(M, grp, newp, dropped):
    """Take the scene paths of the dropped nodes (list entries only) out of every list field of the group's nodes. -> number removed."""
    import kl_fa_bots as F
    gone = {(newp + n).lower() for n in dropped}
    cut = 0
    for nd in grp.walk():
        for ctrl, obj in [(None, nd.props)] + [(M.p.key(nm), body) for nm, body in nd.ctrls]:
            for j, u in enumerate([list(u) for u in F.units(obj[1:-1])]):
                if u and u[0][0] == 0x04:
                    strs = [M.p.keys[struct.unpack('<I', t[1])[0]] for t in u[1:]]
                    kept = [s for s in strs if s.lower() not in gone]
                    if len(kept) != len(strs):
                        M.set(nd, ctrl, {j: kept}); cut += len(strs) - len(kept)
                        obj = nd.props if ctrl is None else next(b for nm, b in nd.ctrls if M.p.key(nm) == ctrl)
    return cut


# ------------------------------------------------------------------ build
def build(src_zip, dst_zip, ext=4, doors=(), pin=None, log=print, spots=None, extra_drop=(), spots_near=None):
    import statistics
    import kl_fa_bots as F, kl_fa_cover as CV, kl_fa_climb2 as C2, kl_graft, kl_light, kl_escape
    data = open(src_zip, 'rb').read()
    if pin and md5(data) != pin:
        raise ValueError('%s: md5 %s is not the pinned %s (use --force)' % (src_zip, md5(data), pin))
    B = F.Built(src_zip)
    sc = B.sc
    if sc.resolve(F.R_ + TOP):
        log('already grafted (%s present): written unchanged' % TOP)
        open(dst_zip, 'wb').write(data)
        return dict(unchanged=True)
    lines = []

    def say(s=''):
        log(s); lines.append(s)
    say('kl_interact_graft: %s (%s) -> %s' % (src_zip, md5(data), dst_zip))
    nav = F.Nav(B.scene.nav)
    hosts = resolve_doors(B, nav, doors) if doors else []
    if spots is None and spots_near:
        spots = spot_near(B, nav, spots_near, keep_off=[h['hinge'] for h in hosts])
    spots = spots if spots is not None else ext_spots(B, nav, ext)
    say('  extinguisher spots: %s' % [(round(s[0]), round(s[1]), round(s[2])) for s in spots])
    real = [h for h in hosts if h['k']]                 # static leaves that are replaced (a virtual host has none)
    gone_k = sorted({h['k'] for h in real} | set(extra_drop))
    if extra_drop:
        for k in extra_drop:
            if not B.ents[k - 1].model or B.ents[k - 1].kids or B.ents[k - 1].raw:
                raise ValueError('extra_drop %d is not a plain static model' % k)
    if hosts or extra_drop:
        tgt = set(gone_k)
        named = sorted({(B.sc.names[k], B.sc.names[x]) for k, _h, _f, _s, hit in J.references(B.sc) for x in (hit or []) if x in tgt and k != x})
        if named:
            raise ValueError('door leaves named by other nodes: %s' % named[:5])
    if hosts:
        sx = round(statistics.median(h['width'] for h in hosts) / DOOR_W, 4)
        sy = round(statistics.median(h['height'] for h in hosts) / DOOR_H, 4)
        say('  kick doors on leaves %s; leaf model scaled x %.4f, y %.4f (stock 120 x 220)' % ([(h['k'], h['name'][-40:], round(h['width']), round(h['height'])) for h in hosts], sx, sy))
        say('  doors swung shut (frame set, hinge kept): %s; virtual doorways: %s; extra nodes dropped: %s' % (
            [h['k'] for h in hosts if h.get('snapped')], [tuple(round(v) for v in h['hinge']) for h in hosts if h.get('virtual')], list(extra_drop)))
    don = Donor.get(EXT_DONOR)
    tmpl_ok = {sc.names[k].lower() for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZParticleTemplate'}
    M = F.Maker()
    gk = CV.group_form(B)
    topg = CV._node(M, B, gk, TOP)
    M.place(topg, (0.0, 0.0, 0.0))
    insts = []
    can0 = don.ent(EXT_CAN)
    cbox = struct.unpack_from('<6f', don.prm.chunks[can0.model], 0x20)
    for n, (x, y, z, _L) in enumerate(spots, 1):
        # the can's origin: its model box bottom (cbox[1]) on the floor, 1 cm up; ASSUMPTION: the model's own y axis is up
        at = (x, y - cbox[1] + 1.0, z)
        grp, can, byk, gone, cuts = make_extinguisher(M, B, don, n, at, tmpl_ok)
        topg.add(grp)
        insts.append(dict(group=grp, can=can, byk=byk, at=at))
        say('  KL_Ext_%d at %s: %d nodes, %d list entries dropped, emitters without template dropped: %s' % (n, tuple(round(v) for v in at), len(list(grp.walk())) - 1, cuts, gone))
    # ---- the kick doors
    dinsts, dd = [], None
    if hosts:
        dd = Donor.get(DOOR_DONOR)
        for n, h in enumerate(hosts, 1):
            grp, byk, gone, newp = make_door(M, B, dd, n, h, tmpl_ok)
            cut = drop_names(M, grp, newp, gone)
            topg.add(grp)
            dinsts.append(dict(group=grp, byk=byk, at=h['hinge'], host=h, door=byk[DOOR_LEAF]))
            say('  KL_Door_%d at %s on host leaf %s (%s): %d nodes, dropped %s, %d list entries cut' % (
                n, tuple(round(v) for v in h['hinge']), h['k'], h['name'][-40:], len(list(grp.walk())) - 1, gone, cut))
    # ---- models: roots of every cloned node that has one; one leg per donor level, in order (the numbering of a leg
    # depends on the .prm the legs before it made: a dry run per leg here, the real appends below)
    pS, matS, texS = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    legs = []
    todo = [(don, don.prm, insts)] + ([(dd, scaled_door_prm(dd, sx, sy), dinsts)] if dinsts else [])
    for dn, dprm, its in todo:
        if not its:
            continue
        roots = sorted({nd.model for it in its for nd in it['group'].walk() if nd.model and getattr(nd, 'donor', None)})
        kinds, args = G.walk(dprm, roots)
        slots = {dprm.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
        want = set(T.used_textures(dn.mat, slots))
        for i, k in kinds.items():
            for off, typ, _k in G.fields(dprm, i, k, args.get(i, 0)):
                if typ in 'tT' and dprm.u32(i, off):
                    want.add(dprm.u32(i, off) % G.SLOTS['dd'])
        tex, tmap = T.merge_tex(texS, dn.tex, want)
        mat, mmap = T.merge_mat(matS, dn.mat, slots, tmap)
        pS, cmap = G.append(pS, dprm, roots, mmap, None, tmap)         # a dry run: the numbering only
        lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
        say('  .prm: %d chunks of %s appended; materials %s; shaders missing in the map .fxc: %s' % (len(kinds), dn.level, sorted(mmap[s] for s in slots), lack or 'none'))
        if lack:
            raise ValueError('%s: shaders missing in the map .fxc: %s' % (dn.level, lack))
        legs.append(dict(don=dn, prm=dprm, roots=roots, kinds=kinds, mmap=mmap, tmap=tmap, cmap=cmap))
        texS, matS = tex, mat
        for it in its:
            for nd in it['group'].walk():
                if getattr(nd, 'donor', None) and nd.model:
                    nd.model = cmap[nd.model]
                    M.set(nd, None, {'ZGEOM[4]': nd.model})
    mat, tex = matS, texS
    # ---- light lists (a ZSTDOBJ with a list in the donor gets the nearest map object's)
    slotx = B.scene.slots()
    lit = [e for e in B.ents if e.tid == 0x200002 and e.links]
    for it in insts + dinsts:
        for nd in it['group'].walk():
            if nd.links is not None and getattr(nd, 'donor', None):
                P = it['at']
                best = min(lit, key=lambda e: sum((B.fr[e][1][i] - P[i]) ** 2 for i in range(3)))
                nd.links = list(best.links)
    # ---- the scene
    q, order = M.scene([topg])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'interact', skip=set(gone_k))
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    gone_ents = [B.ents[k - 1] for k in gone_k]
    for e in gone_ents:                                   # the static leaves the kick doors replace (no kids: door_hosts) + extra_drop
        A.remove(e)
    made = {}
    nxt = C2._write_ent(A, topg, None, nxt, made)
    A.ref_slots = nxt
    keys = None
    if dinsts:                                            # the stock leaf's KEYS tracks: their .buf head region once, every leaf points at it
        offs, klo, khi = door_keys(dd)
        A.head += bytes(-len(A.head) % 16)
        kbase = len(A.head)
        A.head += dd.head[klo:khi]
        for it in dinsts:
            raw = bytearray(dd.ent(DOOR_LEAF).raw)
            for i, o in enumerate(offs):
                struct.pack_into('<I', raw, KEYS_AT + 4 * i, kbase + o - klo)
            made[id(it['door'])].raw = bytes(raw)
        keys = (kbase, khi - klo)
        say('  KEYS: %d bytes of the .buf head of %s (%#x..%#x) copied to %#x of the map' % (khi - klo, DOOR_DONOR, klo, khi, kbase))
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    drop = {slot0[e] + 2 for e in gone_ents}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, drop), O.remap_ids(rmi, ids, drop), O.remap_ids(rmc, ids, drop)
    allit = insts + dinsts
    lo = tuple(min(it['at'][i] for it in allit) - 400.0 for i in range(3)); hi = tuple(max(it['at'][i] for it in allit) + 400.0 for i in range(3))
    root3 = octn.rooms[0][3]
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree([(slot1[made[id(topg)]] + 2, lo, hi)], root3.origin, root3.scale))
        octn.rooms[0][3].check()
    t0 = octn.rooms[0][0]
    if t0 is not None:
        # GUESS (cosmetic): the explosion's two group-0 meshes are listed in the root room's tree 0 with a 3 m box round the can;
        # a pool-group-0 mesh that no tree lists is not drawn (ropevis T29), which room the engine draws it from is untested
        items = []
        for it in insts:
            for k in EXT_TREE0:
                nd = it['byk'].get(k)
                if nd is not None:
                    items.append((slot1[made[id(nd)]] + 2, tuple(it['at'][i] - 300.0 for i in range(3)), tuple(it['at'][i] + 300.0 for i in range(3))))
        octn.rooms[0][0] = O.join_trees(t0, O.build_tree(items, t0.origin, t0.scale))
        octn.rooms[0][0].check()
        say('  %d explosion meshes listed in tree 0 of the root room (%d -> %d items)' % (len(items), len(t0.items), len(octn.rooms[0][0].items)))
    else:
        say('  the root room has no tree 0: the explosion group-0 meshes stay unlisted')
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    # ---- .oct records of the donor models, then the .prm for real, one leg per donor: the references the chunks hold now are
    # `held` (the original .oct's for the map's own roots); after a leg every root chunk that held one is sent to the new .oct's
    unref = lambda v: (v & ~1) - 4
    octj, held, pcur, moved = octn, octx.record_refs(), G.read(B['.prm'], 'dd'), 0
    for lg in legs:
        dn = lg['don']
        rec_d = {v: n for n, v in enumerate(dn.oct.record_refs())}
        keep = sorted({rec_d[lg['prm'].u32(i, 0x1c)] for i, k in lg['kinds'].items() if k == 'root' and lg['prm'].u32(i, 0x1c)})
        octk, _same, refs_b = O.append_records(octj, dn.oct, lg['cmap'], keep)
        refs_a = dict(zip(held, octk.record_refs()))
        pnew, cmap2 = G.append(pcur, lg['prm'], lg['roots'], lg['mmap'], {unref(a): unref(b) for a, b in refs_b.items()}, lg['tmap'])
        if cmap2 != lg['cmap']:
            raise ValueError('kl_prmgraph.append numbers chunks differently on the second run (%s)' % dn.level)
        for i in range(1, len(pcur.chunks)):
            c = pnew.chunks[i]
            if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
                v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
                if v != struct.unpack_from('<I', c, 0x1c)[0]:
                    pnew.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]; moved += 1
        held, octj, pcur = octk.record_refs(), octk, pnew
    prm = pcur
    prm_bytes = G.write(prm)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    # ---- Havok: the cans: one type-2 shape record; the doors: one type-4 shape record (the stock leaf's slab scaled like the model)
    hvk = kl_hvk.Hvk(B['.HVK'])
    if real:
        kl_escape.cut_collision(hvk, {h['ref'] for h in real}, log=say)
    news, hrd_new = [], []
    if insts:
        dh = don.hvk
        dshape = next(s for s in dh.shapes if any(kl_hvk.ref(i) == can0.ref for i in s.inst))
        dinst = next(i for i in dshape.inst if kl_hvk.ref(i) == can0.ref)
        d_hrd = don.files['.hrd']
        t2 = [i for s in dh.shapes if s.type == kl_hvk.RIGID for i in s.inst]
        drec = d_hrd[28 * t2.index(dinst):28 * t2.index(dinst) + 28]
        for it in insts:
            i = bytearray(dinst)
            struct.pack_into('<3f', i, 0, *(v / 100.0 for v in it['at']))
            struct.pack_into('<I', i, 0x30, made[id(it['can'])].ref)
            news.append(bytes(i))
            rec = bytearray(drec)
            struct.pack_into('<3f', rec, 0, *(v / 100.0 for v in it['at']))
            hrd_new.append(bytes(rec))
        hvk.shapes.append(dshape.clone(news, []))
    if dinsts:
        ds = dd.hvk.shapes[DOOR_SHAPE]
        leaf = dd.ent(DOOR_LEAF)
        di = next(i for i in ds.inst if kl_hvk.ref(i) == leaf.ref)
        v = list(struct.unpack('<%df' % (len(ds.verts) // 4), ds.verts))
        for j in range(0, len(v), 3):
            v[j] *= sx; v[j + 1] *= sy
        dnews = []
        for it in dinsts:
            cx, cy, cz = it['host']['R']
            i = bytearray(di)
            struct.pack_into('<3f', i, 0, *(c / 100.0 for c in it['at']))
            struct.pack_into('<9f', i, 12, *(col[r] for r in range(3) for col in (cx, cy, cz)))      # row-major, columns = the leaf's axes
            struct.pack_into('<I', i, 0x30, made[id(it['door'])].ref)
            dnews.append(bytes(i))
        sh = ds.clone(dnews, [])
        sh.verts = struct.pack('<%df' % len(v), *v)
        hvk.shapes.append(sh)
    hvk_bytes = hvk.serialize()
    if kl_hvk.Hvk(hvk_bytes).serialize() != hvk_bytes:
        raise ValueError('.HVK does not round-trip')
    hrd = B.files[B.ext['.hrd']] + b''.join(hrd_new) if '.hrd' in B.ext else None
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octj.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    new[B.ext['.HVK']] = hvk_bytes
    if hrd is not None:
        new[B.ext['.hrd']] = hrd
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    out = kl_graft.write_zip(dst_zip, [(nm, new[nm]) for nm in B.order])
    say('written %s md5 %s; members changed: %s; %d map .prm roots re-pointed' % (out, md5(open(out, 'rb').read()), ' '.join(changed), moved))
    return dict(out=out, changed=changed, spots=spots, lines=lines)


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('spots', 'build'):
        print(__doc__); return 2
    import kl_fa_bots as F
    if a[0] == 'spots':
        B = F.Built(a[1])
        for s in ext_spots(B, F.Nav(B.scene.nav), 6):
            print(s)
        return 0
    kw = {}
    if '--ext' in a:
        i = a.index('--ext'); kw['ext'] = int(a[i + 1]); del a[i:i + 2]
    if '--doors' in a:
        i = a.index('--doors'); kw['doors'] = [int(x) for x in a[i + 1].split(',') if x]; del a[i:i + 2]
    force = '--force' in a
    if force:
        a.remove('--force')
    if '--map' in a:                       # PLAN entry: ext count, doors and the md5 pin (unless --force)
        i = a.index('--map'); pl = PLAN[a[i + 1]]; del a[i:i + 2]
        kw.setdefault('ext', pl['ext']); kw.setdefault('doors', pl['doors'])
        if pl.get('extra_drop'):
            kw.setdefault('extra_drop', pl['extra_drop'])
        if pl.get('spots_near'):
            kw.setdefault('spots_near', pl['spots_near'])
        if not force:
            kw['pin'] = pl['md5']
    if '--md5' in a:
        i = a.index('--md5'); kw['pin'] = a[i + 1]; del a[i:i + 2]
        if force:
            kw.pop('pin')
    build(a[1], a[2], **kw)
    return 0


if __name__ == '__main__':
    sys.exit(main())
