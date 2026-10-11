"""gunfit - Dead Men guns seated in Dog Days hands, and every skeleton bound to the right ANM tracks.

Converter output only (prp, prm, ANM): no loader or kl2 code, so no CEG concern. Master switch ANP_GUNFIT (default 1).

WHY (guns research + critique, 11 Oct; FK of the clip data, ICP of the meshes):
  * Both games hold a gun the same way: the gun model's own frame sits on the hand's 'r hand attacher' bone and the
    template Ground is ignored while held. Dog Days' handling clips pitch that attacher's x axis about +9.8 deg in
    aim poses, so every Dog Days gun mesh/skeleton is turned -10 deg in model space and every Dog Days template
    Ground is +9.82 deg (F03: all 51 firearms). Dead Men's meshes have the barrel at -p (p = Dead Men Ground pitch:
    -0.18 most guns, -10.18 Remington 870, -25.18 Rem 700 / Mini-14) and Dead Men's own clips compensate per gun.
    Under Dog Days' clips a converted gun therefore points (9.82 - p) deg high: 10, 20 or 35 deg.
  * Fix (ANP_GUNFIT_TURN): per gun model root, theta = p_DM - p_DD, p_DD = the Ground pitch of the Dog Days (F03)
    template bound to the SAME converted item (9.82 for Dog Days-authored guns, -0.18 for the legacy RPG-7/HK69, so
    those get theta 0 and are left alone). Vertices v' = v*H + s (row vectors, H = turn about model z), packed
    normal/tangent/binormal turned by H, root bounds recomputed. Skeleton: [2] global rest R' = R*H, T' = T*H + s,
    [18] = inverse([2]), and the local rest [3]/[6] of the root bone's children. Every entity drawing the root (the
    templates' Ground/Ground01) gets M' = H^T*M, p' = p - s*H^T*M, so template space (muzzle/eject PosBoxes, Box,
    a gun lying on the floor) does not move.
    s = the Dog Days twin's re-seat (ICP of the meshes) for AK74, Spas12, Minimi, 870, Rem700 (Mini-14 = Rem700);
    every other gun JC's AK re-seat (hand-derived estimates agree to ~2 cm; no better signal in the data).
  * 'l hand attacher' (ANP_GUNFIT_LHA): Dog Days' clips drive the clip-side 'l hand attacher' to a target authored on
    the Dog Days gun's own 'l hand attacher' (stock: 0.1 cm apart). Dead Men's gun lha is in another convention
    (rotated 144.5 deg). The gun's lha global rest is set to that of the F03 template bound to the same item, so any
    left-hand IK onto it is a no-op exactly as in stock Dog Days; fallback when F03 has no such template: the
    measured constant conversion X_LHA (AK/Spas/Minimi twins) plus the AK offset.
  * Bone binding (ANP_GUNFIT_BIND): skeleton slot [9] (u16 per bone) = the bone's index in the ANM bone-name table C,
    slot [8] (1024 bytes) = C -> bone, slot [10] (1024 u16) = C -> bone*12 (both with entries 1022/1023 = 0; 190/190
    stock skeletons of F03, M01A and converted M01 obey [8] = inverse([9]) and [10] = 12*[8]). kl2's pose builder
    (0x853230) maps every track to a bone through [8]. The converter copied Dead Men's tables, but the level ANM is
    F03's library with Dead Men's clips merged in, whose C differs from Dead Men's from index 61 on: in M01 442 of 1339
    bones were bound to the wrong track (faces, muscles, vehicle doors/wheels/seats, gun parts). Rebuilt by bone NAME
    against the merged C; skeleton bone names the merged C lacks are appended to it (append-only: C[0..66], GROUND=57,
    the mirror pair 59/60, stay put). Each unique [8]/[9]/[10] chunk triple is rewritten exactly once.
    Gun part bones (w_bone_*) are bound to their own appended placeholder names, which no clip has, so they stay at
    rest as they did in effect so far (Dog Days' gun clips pose Dog Days' frame, 2-3 cm and 10 deg off a Dead Men
    gun); ANP_GUNFIT_GUNBONES=bind binds them by name instead. ANP_SKELBIND_FACE=0 does the same for fa_* (faces).
  * The M4 is held with the FN SCAR's Rifle_Default clips (prpconv ITEM_MAP, ANP_GUNFIT_M4SCAR): the Type95 bullpup
    clips put the support hand 10 cm behind the M4's foregrip.
"""
import os, sys, math, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _on(name, default='1'):
    return os.environ.get(name, default) == '1'


ENABLED = _on('ANP_GUNFIT')
TEMPLATE_WEAPON = 0x10048d                       # ZFFItemTemplateWeapon (same id in both games' schemas)
FIREARM_WT = {'WT_PISTOL', 'WT_REVOLVER', 'WT_SUBMACHINEGUN', 'WT_MACHINEGUN', 'WT_RIFLE', 'WT_PUMPGUN', 'WT_SHOTGUN',
              'WT_SNIPERRIFLE', 'WT_RIFLETYPE95', 'WT_RIFLETYPE88', 'WT_ROCKETLAUNCHER', 'WT_GRENADELAUNCHER'}
DD_PITCH = 9.82                                   # Dog Days Ground pitch of a Dog Days-authored firearm (F03: all)
LEGACY_PITCH = -0.18                              # RPG-7 / HK69 (Dog Days kept Dead Men's mesh and clips)
LEGACY_WT = {'WT_ROCKETLAUNCHER', 'WT_GRENADELAUNCHER'}
# re-seat shift (model space after the turn), by Dead Men template name prefix (ICP of the Dog Days twins)
SHIFTS = (('rifle_ak74', (1.04, 1.41, -0.14)), ('rifle_spas12', (0.02, 4.20, 0.19)),
          ('mg_minimi_spw', (0.68, 1.59, -2.52)), ('shotgun_remington_870', (2.81, 4.35, 0.46)),
          ('sn_rem700', (1.37, 3.26, 0.05)), ('rifle_rugermini14', (1.37, 3.26, 0.05)))
SHIFT_DEFAULT = (1.04, 1.41, -0.14)               # JC's AK re-seat (kl-merge re/map_guns.md)
# Dead Men -> Dog Days 'l hand attacher' convention (fallback only): R = X_LHA * R_dm(turned), p += LHA_OFS
X_LHA = ((0.229, -0.917, -0.327), (-0.405, -0.395, 0.825), (-0.885, -0.056, -0.462))
LHA_OFS = (-0.08, -1.91, -8.88)
STRIDE = {0: 40, 2: 40, 3: 52}                    # mesh subtype -> vertex size
VECS = {40: (12, 28, 32), 52: (28, 44, 48)}       # packed B,G,R,x normal / tangent / binormal
LHA = 'l hand attacher'
UNBOUND_TAG = '~anp_static'                       # placeholder C names: '<bone name>~anp_static'
C_RESERVED = 1022                                 # [8]/[10] entries 1022/1023 are fixed (0) in every stock skeleton


# ---------------------------------------------------------------- small linear algebra (row vectors, 3x3 lists)
def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vm(v, m):
    return [sum(v[k] * m[k][j] for k in range(3)) for j in range(3)]


def tr(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def turn(theta):
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return [[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]]


def stored_to_rows(f9):
    """stored rows are the images of z, y, x -> [x, y, z] rows"""
    return [list(f9[6:9]), list(f9[3:6]), list(f9[0:3])]


def rows_to_stored(M):
    return list(M[2]) + list(M[1]) + list(M[0])


def pitch_of(f9):
    """pitch (deg) of the model x axis in the parent frame, from a stored 9-float matrix"""
    x = f9[6:9]
    return math.degrees(math.atan2(x[1], math.hypot(x[0], x[2])))


def qmat(q):
    """quaternion (x, y, z, w) -> row-vector matrix (the skeleton [6] convention: chaining [6] reproduces [2])"""
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
            [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
            [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)]]


def mquat(M, near=None):
    """inverse of qmat (qmat(q) is the transpose of the usual column-vector matrix)"""
    R = tr(M)
    t = R[0][0] + R[1][1] + R[2][2]
    if t > 0:
        S = math.sqrt(t + 1.0) * 2; w = 0.25 * S
        x = (R[2][1] - R[1][2]) / S; y = (R[0][2] - R[2][0]) / S; z = (R[1][0] - R[0][1]) / S
    elif R[0][0] > R[1][1] and R[0][0] > R[2][2]:
        S = math.sqrt(1.0 + R[0][0] - R[1][1] - R[2][2]) * 2; x = 0.25 * S
        w = (R[2][1] - R[1][2]) / S; y = (R[0][1] + R[1][0]) / S; z = (R[0][2] + R[2][0]) / S
    elif R[1][1] > R[2][2]:
        S = math.sqrt(1.0 + R[1][1] - R[0][0] - R[2][2]) * 2; y = 0.25 * S
        w = (R[0][2] - R[2][0]) / S; x = (R[0][1] + R[1][0]) / S; z = (R[1][2] + R[2][1]) / S
    else:
        S = math.sqrt(1.0 + R[2][2] - R[0][0] - R[1][1]) * 2; z = 0.25 * S
        w = (R[1][0] - R[0][1]) / S; x = (R[0][2] + R[2][0]) / S; y = (R[1][2] + R[2][1]) / S
    q = [x, y, z, w]
    n = math.sqrt(sum(a * a for a in q)); q = [a / n for a in q]
    if near is not None and sum(a * b for a, b in zip(q, near)) < 0:
        q = [-a for a in q]
    return q


def merr(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def orthonormal(M):
    """Gram-Schmidt on the rows (the X_LHA fallback constant is only 3 decimals)"""
    x = M[0]; n = math.sqrt(sum(a * a for a in x)); x = [a / n for a in x]
    y = M[1]; d = sum(a * b for a, b in zip(x, y)); y = [a - d * b for a, b in zip(y, x)]
    n = math.sqrt(sum(a * a for a in y)); y = [a / n for a in y]
    z = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
    return [x, y, z]


# ---------------------------------------------------------------- prm access (Dog Days layout, edited in place)
class _Prm:
    def __init__(self, d):
        self.d = d
        off, cnt = struct.unpack_from('<II', d, 0)
        self.n = cnt
        self.T = [struct.unpack_from('<2I', d, off + 16 * i) for i in range(cnt)]

    def u32(self, i, o):
        return struct.unpack_from('<I', self.d, self.T[i][0] + o)[0]

    def size(self, i):
        return self.T[i][1]

    def chunk(self, i):
        o, s = self.T[i]; return self.d[o:o + s]

    def is_root(self, r):
        return 0 < r < self.n and self.T[r][1] == 64 and struct.unpack_from('<H', self.d, self.T[r][0] + 2)[0] == 7

    def skeleton(self, r):
        if not self.is_root(r) or not self.d[self.T[r][0] + 0x0c] & 1:
            return 0
        p = self.u32(r, 0x10)
        if not (0 < p < self.n) or self.size(p) < 8:
            return 0
        sk = self.u32(p, 4)
        return sk if (0 < sk < self.n and self.size(sk) >= 80) else 0

    def words(self, sk):
        return struct.unpack_from('<20I', self.d, self.T[sk][0])

    def bone_names(self, h):
        n = h[0]; defs = self.chunk(h[1])
        return [bytes(defs[64 * b + 0x1c:64 * b + 64]).split(b'\0')[0].decode('latin1') for b in range(n)]

    def bone_parents(self, h):
        defs = self.chunk(h[1])
        return [struct.unpack_from('<i', defs, 64 * b + 0x0c)[0] for b in range(h[0])]

    def objects(self, r):
        n = self.u32(r, 0x14); lst = self.u32(r, 0x18)
        return list(struct.unpack_from('<%dI' % n, self.d, self.T[lst][0])) if n and 0 < lst < self.n else []

    def descriptors(self, o):
        st = self.u32(o, 0x28)
        if not (0 < st < self.n):
            return []
        out = []
        for x in struct.unpack_from('<%dI' % (self.size(st) // 4), self.d, self.T[st][0]):
            if not x:
                break
            out.append(x)
        return out


def _skeletons(P):
    """{skeleton chunk: [model roots]} over the whole prm"""
    res = collections.defaultdict(list)
    for r in range(1, P.n):
        if P.T[r][1] == 64 and P.is_root(r):
            try:
                sk = P.skeleton(r)
            except struct.error:
                continue
            if sk:
                res[sk].append(r)
    return res


# ---------------------------------------------------------------- Dog Days reference guns (F03, the ANM donor)
def _scene_templates(ops, names, parent, types, prims, k=None):
    """weapon templates of a converted/stock prp op list -> [dict(node, name, ih, wt, item, grounds=[(node, prim, m9,
    p3, span)])]; node = preorder index (= entity index + 1)"""
    from graft import node_spans
    if k is None:
        k = next(i for i, (p, op, v) in enumerate(ops) if op & 0x7f == 2)
    spans, _ = node_spans(ops, k)
    kids = collections.defaultdict(list)
    for e, p in enumerate(parent):
        kids[p + 1 if p >= 0 else 0].append(e + 1)
    res = []
    for e, t in enumerate(types):
        node = e + 1
        if t != TEMPLATE_WEAPON:
            continue
        s0, s1 = spans[node]
        pe = _obj_end(ops, s0)
        ens = [v for (p, op, v) in ops[s0:pe] if op & 0x7f == 14 and isinstance(v, str)]
        ih = next((v for v in ens if v.startswith('IH_')), None)
        wt = next((v for v in ens if v.startswith('WT_')), None)
        item = None
        j = pe
        assert ops[j][1] & 0x7f == 4
        nev = ops[j][2]; j += 1
        for _ in range(nev):
            nm = ops[j][2]; j += 1
            je = _obj_end(ops, j)
            if nm == 'InventoryBinding':
                it = [v for (p, op, v) in ops[j:je] if op & 0x7f == 14 and isinstance(v, str)
                      and v.startswith('eFF2Item') and not v.startswith('eFF2ItemType')]
                if it:
                    item = it[0]
            j = je
        grounds = []
        for c in kids[node]:
            if names[c - 1].split('#')[0] in ('Ground', 'Ground01'):      # M12 also has 'Ground#03'
                g0 = spans[c][0]
                m9, p3 = _get_arrays(ops, g0, _obj_end(ops, g0))
                grounds.append(dict(node=c, prim=prims[c], m9=m9, p3=p3, span=(g0, _obj_end(ops, g0))))
        res.append(dict(node=node, name=names[e], ih=ih, wt=wt, item=item, grounds=grounds))
    return res


def _obj_end(ops, j):
    d = 0
    while True:
        b = ops[j][1] & 0x7f
        if b == 2:
            d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0:
                return j + 1
        j += 1


def _get_arrays(ops, s, e):
    """first 9-float array and the first 3-float array after it inside ops[s:e] (climbs._set_arrays layout)"""
    m9 = p3 = None; j = s
    while j < e:
        op = ops[j]
        if op[1] & 0x7f == 1 and op[2] == 9 and m9 is None:
            m9 = [float(ops[j + 1 + q][2]) for q in range(9)]; j += 10; continue
        if op[1] & 0x7f == 1 and op[2] == 3 and m9 is not None:
            p3 = [float(ops[j + 1 + q][2]) for q in range(3)]; break
        j += 1
    return m9, p3


def _set_arrays(ops, s, e, m9, p3):
    j = s; done9 = False
    while j < e:
        op = ops[j]
        if op[1] & 0x7f == 1 and op[2] == 9 and not done9:
            for q in range(9):
                o = ops[j + 1 + q]; ops[j + 1 + q] = (o[0], o[1], float(m9[q]))
            done9 = True; j += 10; continue
        if op[1] & 0x7f == 1 and op[2] == 3 and done9:
            for q in range(3):
                o = ops[j + 1 + q]; ops[j + 1 + q] = (o[0], o[1], float(p3[q]))
            return
        j += 1
    raise AssertionError('Ground arrays not found')


_REF = None


def reference(work, dd_root, donor='F03'):
    """{item: dict(tpl, pitch, root, lha=[12 stored floats] or None)} from the Dog Days donor level's own weapon
    templates (read from the player's install; cached in <work>/cache, never committed)"""
    global _REF
    if _REF is not None:
        return _REF
    zp = os.path.join(dd_root, donor, donor + '_Main.zip')
    base = os.path.join(work, 'scn', 'dd', donor + '_Main')
    key = [os.path.getsize(zp), int(os.path.getmtime(zp))] + [os.path.getsize(base + x) for x in ('.prp', '.gms', '.buf')]
    cpath = os.path.join(work, 'cache', 'gunfit_ref_%s.json' % donor)
    try:
        c = json.load(open(cpath))
        if c.get('key') == key and c.get('v') == 1:
            _REF = c['ref']; return _REF
    except (OSError, ValueError):
        pass
    from prp import PRP
    from gms import GMS
    from zipraw import read_zip, read_entry
    ops = list(PRP(open(base + '.prp', 'rb').read()).instrs())
    G = GMS(base + '.gms', base + '.buf'); G.depth_tree()
    names = [e['name'] for e in G.ents]; parent = [e['parent'] for e in G.ents]
    types = [e['type'] for e in G.ents]; prims = [0] + [e['prim'] for e in G.ents]
    tpls = _scene_templates(ops, names, parent, types, prims)
    ze = next(e for e in read_zip(zp) if e.name.lower().endswith(('/%s_Main.prm' % donor).lower()))
    P = _Prm(read_entry(ze))
    ref = {}
    for t in tpls:
        if not t['item'] or t['item'] in ref or not t['grounds']:
            continue
        g = t['grounds'][0]
        lha = None
        sk = P.skeleton(g['prim'])
        if sk:
            h = P.words(sk); nm = P.bone_names(h)
            if LHA in nm:
                b = nm.index(LHA)
                lha = list(struct.unpack_from('<12f', P.d, P.T[h[2]][0] + 48 * b))
        ref[t['item']] = dict(tpl=t['name'], pitch=round(pitch_of(g['m9']), 4), root=g['prim'], lha=lha)
    os.makedirs(os.path.dirname(cpath), exist_ok=True)
    json.dump(dict(v=1, key=key, ref=ref), open(cpath, 'w'), indent=0)
    _REF = ref
    return ref


# ---------------------------------------------------------------- step 1: plan + Ground compensation (prp ops)
def _shift_for(name):
    low = name.lower()
    for pre, s in SHIFTS:
        if low.startswith(pre):
            return s, pre
    return SHIFT_DEFAULT, 'default'


def fix_prp(ops, names, parent, types, prims, ref, rep):
    """Plan the turn per gun model root from the level's weapon templates and compensate every Ground that draws a
    turned root. ops: the converted op list (edited in place); names/parent/types: per gms entity (0-based, parent
    -1 = ROOT); prims: per node (0 = ROOT). Returns {root: dict(theta, shift, item, tpl)}."""
    if not (ENABLED and _on('ANP_GUNFIT_TURN')):
        return {}
    tpls = _scene_templates(ops, names, parent, types, prims)
    users = collections.defaultdict(list)                 # root -> [(template, ground)]
    for t in tpls:
        for g in t['grounds']:
            users[g['prim']].append((t, g))
    plan = {}
    for root, lst in sorted(users.items()):
        cands = []
        for t, g in lst:
            if t['ih'] in (None, 'IH_NONE') or t['wt'] not in FIREARM_WT or g['m9'] is None:
                continue
            if t['item'] == 'eFF2ItemNoItem':
                continue
            if t['item'] and t['item'] in ref:
                target, why = ref[t['item']]['pitch'], 'F03 %s' % ref[t['item']]['tpl']
            elif t['item'] is None:
                # binding dropped as a duplicate of another template's item (Light/Carry/Silenced variants)
                target, why = (LEGACY_PITCH if t['wt'] in LEGACY_WT else DD_PITCH), 'no item (%s)' % t['wt']
            else:
                target, why = (LEGACY_PITCH if t['wt'] in LEGACY_WT else DD_PITCH), 'item not in F03'
            # the hand-held template decides (its item's F03 reference gives the lha); vehicle/heli copies come last
            veh = any(x in t['name'].lower() for x in ('heli', 'hind', 'mounted'))
            cands.append(((0 if t['item'] else 2) + (1 if veh else 0), t, g, round(pitch_of(g['m9']) - target, 3), why))
        if not cands:
            continue
        cands.sort(key=lambda c: c[0])
        _, t, g, theta, why = cands[0]
        others = sorted(set(c[3] for c in cands if c[0] < 2 and abs(c[3] - theta) > 0.05))
        if others:
            rep['gunfit root %d (%s): templates disagree on the turn %.2f vs %s - first kept' % (root, t['name'], theta, others)] += 1
        if abs(theta) < 0.05:
            rep['gunfit root %d %s: no turn (%s)' % (root, t['name'], why)] += 1
            continue
        s, spre = _shift_for(t['name'])
        plan[root] = dict(theta=theta, shift=list(s), item=t['item'], tpl=t['name'])
        rep['gunfit root %d %-24s item %s theta %.2f (%s) shift %s %s; drawn by %s' % (
            root, t['name'], t['item'], theta, why, spre, s, ', '.join(sorted(set(u[0]['name'] for u in lst))))] += 1
    # Ground compensation: every entity drawing a planned root (template Grounds; any other user is logged)
    pr = {}
    for e in range(len(names)):
        if prims[e + 1] in plan:
            pr.setdefault(prims[e + 1], []).append(e + 1)
    from graft import node_spans
    k = next(i for i, (p, op, v) in enumerate(ops) if op & 0x7f == 2)
    spans, _ = node_spans(ops, k)
    gnodes = set(g['node'] for t in tpls for g in t['grounds'])
    for root, nodes in pr.items():
        H = turn(plan[root]['theta']); Ht = tr(H); s = plan[root]['shift']
        for nd in nodes:
            if nd not in gnodes:
                rep['gunfit: non-Ground user of root %d: %s (compensated too)' % (root, names[nd - 1])] += 1
            s0 = spans[nd][0]; s1 = _obj_end(ops, s0)
            m9, p3 = _get_arrays(ops, s0, s1)
            if m9 is None or p3 is None:
                raise SystemExit('gunfit: %s (root %d) has no transform arrays' % (names[nd - 1], root))
            M = stored_to_rows(m9)
            M2 = mm(Ht, M)
            p2 = [a - b for a, b in zip(p3, vm(vm(s, Ht), M))]
            _set_arrays(ops, s0, s1, rows_to_stored(M2), p2)
            rep['gunfit Grounds compensated'] += 1
            plan[root].setdefault('grounds', []).append((names[nd - 1], round(pitch_of(m9), 2), round(pitch_of(rows_to_stored(M2)), 2)))
    return plan


# ---------------------------------------------------------------- step 2: ANM bone table (append-only)
def _walk_anm(b):
    """top-level (type, offset, size) of an ANM file"""
    n = struct.unpack_from('<I', b, 12)[0]; o = 16; out = []
    for _ in range(n):
        t = struct.unpack_from('<I', b, o)[0]; sz = struct.unpack_from('<I', b, o + 4)[0] & 0x3fffffff
        out.append((t, o, sz)); o += sz
    return out


def anm_bones(b):
    import anm_lib as L
    t, o, sz = next(x for x in _walk_anm(b) if x[0] == 4)
    a, tot = L.AnimData.parse(b, o)
    return a, o, tot


def anm_append_bones(b, new_names):
    """append bone names to the type-4 chunk's C table; everything else keeps its bytes"""
    import anm_lib as L
    a, o, tot = anm_bones(b)
    a.C.extend(n.encode('latin1') for n in new_names)
    nb = a.build()
    out = bytearray(b[:o]) + nb + b[o + tot:]
    struct.pack_into('<II', out, 4, (struct.unpack_from('<I', b, 4)[0] & 0xc0000000) | len(out), len(out))
    return bytes(out), [c.decode('latin1') for c in a.C]


def _unbound(name):
    low = name.lower()
    if low.startswith('w_bone_') and os.environ.get('ANP_GUNFIT_GUNBONES', 'static') != 'bind':
        return True
    if low.startswith('fa_') and not _on('ANP_SKELBIND_FACE'):
        return True
    return False


def prepare_anm(merged, dm_anm, dm_prm, rep):
    """Append to the merged ANM's bone table every skeleton bone name it lacks (and the placeholder names of the
    unbound bones). Returns (anm bytes, bind info for apply_prm) or (merged, None) when ANP_GUNFIT_BIND=0."""
    if not (ENABLED and _on('ANP_GUNFIT_BIND')):
        return merged, None
    a_dm, _, _ = anm_bones(dm_anm)
    C_dm = [c.decode('latin1') for c in a_dm.C]
    a_out, _, _ = anm_bones(merged)
    C_out = [c.decode('latin1') for c in a_out.C]
    low = set(c.lower() for c in C_out)
    P = _Prm(dm_prm)
    seen = {}
    for sk in _skeletons(P):
        h = P.words(sk)
        if not h[9]:
            continue
        for nm in P.bone_names(h):
            seen.setdefault(nm.lower(), nm)
    add = []
    for lnm, nm in sorted(seen.items()):
        want = (nm + UNBOUND_TAG) if _unbound(nm) else nm
        if want.lower() not in low:
            add.append(want); low.add(want.lower())
    if len(C_out) + len(add) >= C_RESERVED:
        raise SystemExit('gunfit: bone table would reach %d names (limit %d)' % (len(C_out) + len(add), C_RESERVED))
    if add:
        merged, C_new = anm_append_bones(merged, add)
        assert C_new[:len(C_out)] == C_out
        C_out = C_new
    rep['gunfit ANM bone names appended %d (now %d): %s' % (len(add), len(C_out), ', '.join(add))] += 1
    return merged, dict(C_dm=C_dm, C_out=C_out)


# ---------------------------------------------------------------- step 3: prm (binding, turn, l hand attacher)
def _rebind(P, bind, rep):
    d = P.d
    C_dm, C_out = bind['C_dm'], bind['C_out']
    idx = {}
    for i, c in enumerate(C_out):
        idx.setdefault(c.lower(), i)
    sks = _skeletons(P)
    groups = collections.defaultdict(list)             # (h8, h9, h10) -> skeletons
    for sk in sks:
        h = P.words(sk)
        if h[9] and h[8] and h[10]:
            groups[(h[8], h[9], h[10])].append(sk)
    owner = {}
    for tri in groups:
        for k_, c in zip((8, 9, 10), tri):
            if owner.setdefault((k_, c), tri) != tri:
                raise SystemExit('gunfit: skeleton slot [%d] chunk %d paired with different tables' % (k_, c))
    st = collections.Counter()
    for (c8, c9, c10), lst in sorted(groups.items()):
        h = P.words(lst[0]); n = h[0]
        nm = P.bone_names(h)
        if any([x.lower() for x in P.bone_names(P.words(s))] != [x.lower() for x in nm] for s in lst[1:]):
            rep['gunfit bind: shared table %d used by skeletons with different bones - left alone' % c9] += 1; continue
        if P.size(c8) != 1024 or P.size(c10) != 2048 or P.size(c9) < 2 * n:
            rep['gunfit bind: table sizes %d/%d/%d unexpected - left alone' % (P.size(c8), P.size(c9), P.size(c10))] += 1; continue
        old = struct.unpack_from('<%dH' % n, d, P.T[c9][0])
        keys = [(x + UNBOUND_TAG).lower() if _unbound(x) else x.lower() for x in nm]
        miss = [x for x, k_ in zip(nm, keys) if k_ not in idx]
        if miss:                                        # e.g. a skeleton grafted from the Dog Days donor
            rep['gunfit bind: skeleton %d bones not in the ANM bone table (%s) - left alone' % (lst[0], ', '.join(miss[:5]))] += 1
            continue
        new = [idx[k_] for k_ in keys]
        for b in range(n):
            if old[b] < len(C_dm) and C_dm[old[b]].lower() == nm[b].lower():
                st['bones that held the Dead Men index'] += 1
            else:
                st['bones that did NOT hold the Dead Men index'] += 1
        dup = [c for c, k_ in collections.Counter(new).items() if k_ > 1]
        if dup:
            rep['gunfit bind: skeleton %d has bones sharing a name (%s): first wins' % (lst[0], ', '.join(C_out[c] for c in dup))] += 1
        st['bones moved'] += sum(1 for a, b in zip(old, new) if a != b)
        st['bones unbound (placeholder)'] += sum(1 for x in nm if _unbound(x))
        struct.pack_into('<%dH' % n, d, P.T[c9][0], *new)
        o8, o10 = P.T[c8][0], P.T[c10][0]
        d[o8:o8 + C_RESERVED] = b'\xff' * C_RESERVED
        struct.pack_into('<%dH' % C_RESERVED, d, o10, *([0xffff] * C_RESERVED))
        for b in reversed(range(n)):                    # first bone of a name wins
            d[o8 + new[b]] = b
            struct.pack_into('<H', d, o10 + 2 * new[b], 12 * b)
        st['tables rewritten'] += 1
        st['skeletons'] += len(lst)
    for k_, v in sorted(st.items()):
        rep['gunfit bind: %s' % k_] += v


def _turn_root(P, root, pl, ref, done_vc, done_sk, vc_roots, sk_slot_users, rep):
    d = P.d
    th = pl['theta']; H = turn(th); s = pl['shift']
    key = (th, tuple(s))
    lo, hi = [1e30] * 3, [-1e30] * 3
    nv_tot = nch = 0
    for o in P.objects(root):
        sub = d[P.T[o][0] + 0x0c]
        if sub not in STRIDE:
            rep['gunfit root %d: object %d subtype %d skipped' % (root, o, sub)] += 1; continue
        w = STRIDE[sub]
        for dc in P.descriptors(o):
            nv, vc = P.u32(dc, 0), P.u32(dc, 4)
            if not (0 < vc < P.n) or not (nv * w <= P.size(vc) < nv * w + 16):
                rep['gunfit root %d: vertex chunk %d size %d vs %d x %d - skipped' % (root, vc, P.size(vc), nv, w)] += 1; continue
            base = P.T[vc][0]
            other = vc_roots.get(vc, set()) - pl['roots_same']
            if other:
                raise SystemExit('gunfit: vertex chunk %d of gun root %d is also drawn by roots %s' % (vc, root, sorted(other)[:5]))
            if vc in done_vc:
                if done_vc[vc] != key:
                    raise SystemExit('gunfit: vertex chunk %d shared by roots with different turns' % vc)
            else:
                for i in range(nv):
                    a = base + w * i
                    p = struct.unpack_from('<3f', d, a)
                    struct.pack_into('<3f', d, a, *[x + y for x, y in zip(vm(p, H), s)])
                    for k_ in VECS[w]:
                        b4 = d[a + k_:a + k_ + 4]
                        v = ((b4[2] - 128) / 127.0, (b4[1] - 128) / 127.0, (b4[0] - 128) / 127.0)
                        q = [max(0, min(255, int(round(x * 127.0 + 128)))) for x in vm(v, H)]
                        d[a + k_:a + k_ + 3] = bytes((q[2], q[1], q[0]))
                done_vc[vc] = key; nch += 1; nv_tot += nv
            for i in range(nv):
                p = struct.unpack_from('<3f', d, base + w * i)
                lo = [min(x, y) for x, y in zip(lo, p)]; hi = [max(x, y) for x, y in zip(hi, p)]
    if lo[0] < 1e30:
        struct.pack_into('<6f', d, P.T[root][0] + 0x20, *(lo + hi))
    rep['gunfit vertices turned'] += nv_tot
    rep['gunfit vertex chunks turned'] += nch
    # skeleton
    sk = P.skeleton(root)
    if not sk:
        rep['gunfit root %d: no skeleton' % root] += 1; return
    h = P.words(sk); n = h[0]
    # slot chunks can be shared by skeletons of different roots (M01: USP and USP_S share [2]/[3]/[6]/[18]):
    # each chunk is turned exactly once
    state = [done_sk.get(h[k_]) for k_ in (2, 3, 6, 18)]
    if any(x is not None for x in state):
        if state != [key] * 4:
            raise SystemExit('gunfit: skeleton %d slot chunks already turned differently %s' % (sk, state))
        rep['gunfit skeletons sharing an already turned rest'] += 1
        return
    for k_ in (2, 3, 6, 18):
        other = sk_slot_users.get((k_, h[k_]), set()) - pl['sk_same']
        if other:
            rep['gunfit root %d: skeleton slot [%d] shared with skeletons %s - skeleton left alone' % (root, k_, sorted(other)[:4])] += 1
            return
    names = P.bone_names(h); par = P.bone_parents(h)
    o2, o3, o6, o18 = P.T[h[2]][0], P.T[h[3]][0], P.T[h[6]][0], P.T[h[18]][0]
    G = [(stored_to_rows(struct.unpack_from('<12f', d, o2 + 48 * b)), list(struct.unpack_from('<3f', d, o2 + 48 * b + 36)))
         for b in range(n)]
    # the convention check on the original data: root-bone children have [3] == [2] and qmat([6]) == [3]
    roots_b = [b for b in range(n) if par[b] < 0]
    for b in range(n):
        if par[b] in roots_b:
            L3 = stored_to_rows(struct.unpack_from('<12f', d, o3 + 48 * b))
            q = struct.unpack_from('<4f', d, o6 + 28 * b)
            if merr(qmat(q), L3) > 2e-3 or merr(L3, mm(G[b][0], tr(G[par[b]][0]))) > 2e-3:
                rep['gunfit root %d: skeleton convention check failed on bone %s - skeleton left alone' % (root, names[b])] += 1
                return
    G2 = []
    for b in range(n):
        R, t = G[b]
        if par[b] < 0:
            G2.append((R, t)); continue                 # GROUND: the model frame itself
        G2.append((mm(R, H), [x + y for x, y in zip(vm(t, H), s)]))
    if LHA in names and _on('ANP_GUNFIT_LHA'):
        b = names.index(LHA)
        if any(p == b for p in par):
            rep['gunfit root %d: l hand attacher has children - left as turned' % root] += 1
        else:
            r_ = ref.get(pl['item']) if pl['item'] else None
            if r_ and r_.get('lha'):
                f = r_['lha']
                G2[b] = (stored_to_rows(f[:9]), list(f[9:12]))
                rep['gunfit lha <- F03 %s' % r_['tpl']] += 1
            else:
                R, t = G2[b]
                G2[b] = (orthonormal(mm([list(r) for r in X_LHA], R)), [x + y for x, y in zip(t, LHA_OFS)])
                rep['gunfit lha <- X_LHA fallback (%s: no F03 template for %s)' % (pl['tpl'], pl['item'])] += 1
            pl['lha_moved'] = round(math.sqrt(sum((x - y) ** 2 for x, y in zip(G[b][1], G2[b][1]))), 2)
    recompute = set(b for b in range(n) if par[b] in roots_b or names[b] == LHA)
    for b in range(n):
        R, t = G2[b]
        struct.pack_into('<12f', d, o2 + 48 * b, *(rows_to_stored(R) + list(t)))
        Ri = tr(R)
        struct.pack_into('<12f', d, o18 + 48 * b, *(rows_to_stored(Ri) + [-x for x in vm(t, Ri)]))
        if b in recompute and par[b] >= 0:
            PR, PT = G2[par[b]]
            LR = mm(R, tr(PR)); Lt = vm([x - y for x, y in zip(t, PT)], tr(PR))
            struct.pack_into('<12f', d, o3 + 48 * b, *(rows_to_stored(LR) + Lt))
            q = mquat(LR, near=struct.unpack_from('<4f', d, o6 + 28 * b))
            assert merr(qmat(q), LR) < 1e-5, (root, names[b])
            struct.pack_into('<7f', d, o6 + 28 * b, *(q + Lt))
    for k_ in (2, 3, 6, 18):
        done_sk[h[k_]] = key
    rep['gunfit skeletons turned'] += 1


def apply_prm(prm, plan, bind, ref, rep):
    if not ENABLED or (not plan and not bind):
        return prm
    P = _Prm(bytearray(prm))
    if bind:
        _rebind(P, bind, rep)
    if plan:
        # who draws which vertex chunk / owns which skeleton slot chunk (sharing checks)
        vc_roots = collections.defaultdict(set)
        sk_of = {}
        for r in range(1, P.n):
            if P.T[r][1] != 64 or not P.is_root(r):
                continue
            try:
                for o in P.objects(r):
                    if not (0 < o < P.n) or P.size(o) not in (64, 128) or P.u32(o, 0) >> 16 != 8:
                        continue                         # mesh objects only (prmconv: class 8)
                    for dc in P.descriptors(o):
                        if 0 < dc < P.n and P.size(dc) == 48:
                            vc_roots[P.u32(dc, 4)].add(r)
                sk_of[r] = P.skeleton(r)
            except struct.error:
                continue
        sk_slot_users = collections.defaultdict(set)
        for r, sk in sk_of.items():
            if sk:
                h = P.words(sk)
                for k_ in (2, 3, 6, 18):
                    sk_slot_users[(k_, h[k_])].add(sk)
        done_vc, done_sk = {}, {}
        for root, pl in sorted(plan.items()):
            same = set(r for r, q in plan.items() if (q['theta'], tuple(q['shift'])) == (pl['theta'], tuple(pl['shift'])))
            pl['roots_same'] = same
            pl['sk_same'] = set(sk_of.get(r) for r in same)
            _turn_root(P, root, pl, ref, done_vc, done_sk, vc_roots, sk_slot_users, rep)
            del pl['roots_same'], pl['sk_same']
    return bytes(P.d)


# ---------------------------------------------------------------- offline verification (tools/verify_guns.py uses it)
def check_skeletons(prm, C=None, roots=None):
    """invariants: [8] = inverse([9]), [10] = 12*[8], every bone bound by name (or to its placeholder), [18] =
    inverse([2]), root-bone children [3] == [2] and qmat([6]) == [3]. Returns a Counter."""
    P = _Prm(prm); st = collections.Counter()
    idx = {}
    if C:
        for i, c in enumerate(C):
            idx.setdefault(c.lower(), i)
    for sk, rs in _skeletons(P).items():
        h = P.words(sk); n = h[0]
        if roots is not None and not set(rs) & set(roots):
            continue
        st['skeletons'] += 1
        nm = P.bone_names(h); par = P.bone_parents(h)
        if h[9] and h[8] and h[10] and P.size(h[8]) == 1024:
            s9 = struct.unpack_from('<%dH' % n, P.d, P.T[h[9]][0]); s8 = P.chunk(h[8])
            s10 = struct.unpack_from('<1024H', P.d, P.T[h[10]][0])
            st['[8] inverse of [9]' if all(s8[s9[b]] == b for b in range(n)) else '[8] NOT inverse of [9]'] += 1
            st['[10] = 12*[8]' if all((s8[c] == 0xff and s10[c] == 0xffff) or s10[c] == 12 * s8[c] for c in range(C_RESERVED))
               else '[10] != 12*[8]'] += 1
            if C:
                for b in range(n):
                    want = idx.get((nm[b] + UNBOUND_TAG).lower() if _unbound(nm[b]) else nm[b].lower())
                    st['bones bound by name' if s9[b] == want else 'bones NOT bound by name'] += 1
        o2, o3, o6, o18 = (P.T[h[k]][0] for k in (2, 3, 6, 18))
        G = [(stored_to_rows(struct.unpack_from('<12f', P.d, o2 + 48 * b)), struct.unpack_from('<3f', P.d, o2 + 48 * b + 36)) for b in range(n)]
        e18 = e3 = e6 = 0.0
        for b in range(n):
            R, t = G[b]
            f = struct.unpack_from('<12f', P.d, o18 + 48 * b)
            Ri = tr(R)
            e18 = max(e18, merr(stored_to_rows(f[:9]), Ri), max(abs(x + y) for x, y in zip(f[9:], vm(t, Ri))))
            if par[b] >= 0:
                PR, PT = G[par[b]]
                L3 = struct.unpack_from('<12f', P.d, o3 + 48 * b)
                LR = mm(R, tr(PR)); Lt = vm([x - y for x, y in zip(t, PT)], tr(PR))
                q = struct.unpack_from('<7f', P.d, o6 + 28 * b)
                e3 = max(e3, merr(stored_to_rows(L3[:9]), LR), max(abs(x - y) for x, y in zip(L3[9:], Lt)))
                e6 = max(e6, merr(qmat(q[:4]), LR), max(abs(x - y) for x, y in zip(q[4:], Lt)))
        st['max |[18] - inverse([2])| x1e4'] = max(st['max |[18] - inverse([2])| x1e4'], int(e18 * 1e4))
        st['max |[3] - local([2])| x1e4'] = max(st['max |[3] - local([2])| x1e4'], int(e3 * 1e4))
        st['max |qmat([6]) - local([2])| x1e4'] = max(st['max |qmat([6]) - local([2])| x1e4'], int(e6 * 1e4))
    return st
