#!/usr/bin/env python3
"""
Picture sheets of animation clips without the game: a heister model POSED by a clip's keys (the whole skeleton,
skinned and textured), a row of frames per clip, a number and a legend beside each row. Pure Python (kl_view's
software renderer; the text is drawn by Windows GDI through ctypes). Made for 'which of these is the one you
mean': re/anim_shot.md.

    python kl_animsheet.py list <level> [slot regex]      per slot the clips each character set plays for it
                                                          (default: everything under /Damage and the rises)
    python kl_animsheet.py shot <level> <out folder>      THE SHEETS: every full-body clip a character can play
                                                          when he is hit, wounded, downed, killed or gets up,
                                                          numbered; one page a family + overview.png + legend.txt
    python kl_animsheet.py sheet <level> <out.png> <regex> [...]
                                                          any clips: regex against slot names and clip names
    python kl_animsheet.py check <level>                  the pose reader against the model: a standing clip's
                                                          bone places beside the skeleton's rest places, and three
                                                          clips whose NAME says which way the chest must be
    python kl_animsheet.py trunk <level> <clip regex> [...]
                                                          no picture: per clip the pose by frame ranges (STANDS,
                                                          KNEELS, BELLY, BACK, SIDE, bent - pose_word's limits),
                                                          measured from the keys; the sheets print the same in green

    options: --hero N (1..8, default 1)  --variant V (default 2 = masked)  --lod L (default 2)
             --frames K (default 8)  --view side|quarter|front (default quarter)  --jobs J  --plain (no textures)
             --to F (sheet only: the frames are spread over 0 .. F, to look at a clip's beginning;
                     F below 0: over the last |F| per cent of the clip, to look at its end)
    <level>: a stock Dog Days level name ('F01') or a build folder (kl_chars.Lv).

WHAT IS READ, AND HOW SURE
  clip data (kl_anm docstring 'CLIP DATA'): tracks x {rotation frame table, rotation keys, position frame table,
      position keys, bone}. A frame table is the 'IdxT' block the game reads at kl2 0x6663b0 (bit 34: 4-bit width
      w, bit 38: 16-bit count, bit 54: count x w-bit frame numbers). Rotation keys as kl2 0x834170 reads them:
      byte 0 = bits 0-1 the dropped component, bit 2 'one key', bits 3-7 the width B (31 = raw floats); three
      signed B-bit bases; three 5-bit widths; a record a key = sign bit + three offsets; the dropped component is
      the root of the rest. Position keys are three floats. (Decoder first written for re/player_down.md 10.)
  the pose: every tracked bone's key is its LOCAL rotation and place under its parent (the model's own
      hierarchy, .prm skeleton); world = parent x local, column vectors, the usual quaternion-to-matrix form.
      `check` shows this agrees with the skeleton's rest matrices (same handedness, same axes). Bones a clip has
      no track for (face, attachers, muscle helpers) keep their rest place under their parent; a helper whose rest
      matrix equals a tracked sibling's (the forearm twist bones) follows that sibling. Between two keys the
      rotation is blended linearly and normalised.
  skinning: kl_view's (vertex +12 three weights, +24 four palette bytes, the object's bone runs).
  NOT DRAWN: the weapon (it is another entity on a hand bone), cloth, the ragdoll a clip's event may start, any
      blend with a second clip or an aim layer the game puts on top, the alignment to the floor. What the game
      shows of a clip can therefore be SHORTER than the row (a death clip is cut at its events) - the legend says
      which events a clip carries.
"""
import struct, sys, os, math, re, zlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SETS = ('Kane', 'Lynch', 'Kane_NPC', 'Lynch_NPC')          # the human heisters' two sets, the AI heisters' two
HUMAN, BOT = ('Kane', 'Lynch'), ('Kane_NPC', 'Lynch_NPC')
LIST_RX = r'^/Damage/|^/Movement/Rise/|^/Special_moves/Heal_|^/Movement/(Walk/Forward_Wounded|Stand/Wounded)'

# the families of the `shot` sheets: (page, title, slot regex). A clip goes to the first family that has it.
FAMILIES = [
    ('A_death', 'A. DEATH CLIPS - the death chooser kl2 0x72ab60 (an actor that dies without a ragdoll)',
     r'^/Damage/Death/(Die_|Instant|Standing)'),
    ('B_wounded', "B. THE 'WOUNDED' FAMILY - ZWounded 0x865180 (an NPC killed: thrown down, lies between events 7 and 8) and the human's own death (Hero_Torso_F)",
     r'^/Damage/Wounded/(Running|Crouched|Standing|Hero_Torso|Stand_To|Crouch_To)'),
    ('C_impact', 'C. HIT AND LIVES, full body - ZGeneric 0x4aba20 (/Damage/Impact/FB/...; Running/Front_Torso = down and UP AGAIN)',
     r'^/Damage/(Impact/FB/(Running|Standing|Crouched|Flash)|Hit/)'),
    ('D_down', "D. 'DOWN NOT DEAD' - the human's stock knock-down and an NPC's own (state graph 0x730be0)",
     r'^/Damage/Down_Not_Dead/(Down_Not_Dead$|Down_Not_Dead_Get_|Compact_Down_Not_Dead|On_Spot_|Down_Not_Dead_wounded|Down_Not_Dead_Crawl_Back$|Down_Not_Dead_Crawl_Back_Sprint)'),
    ('E_rise', 'E. CRAWL, DRAG, RISE, HEAL - what else the files hold for a man on the floor',
     r'^/Damage/Wounded/(Crawl|Dragg)|^/Movement/Rise/|^/Special_moves/Heal_|^/Movement/(Walk/Forward_Wounded|Stand/Wounded)'),
    ('F_cover', 'F. FLINCHES AT A COVER, full body (/Damage/Impact/FB/Cover_...): short, he stays where he is',
     r'^/Damage/Impact/FB/Cover_'),
    ('I_upper', 'I. HIT AND LIVES, UPPER BODY ONLY (/Damage/Impact/UB/...) - drawn over the REST legs; the game keeps his own legs',
     r'^/Damage/Impact/UB/'),
]


# closer looks of the `shot` run, with the SAME numbers: (page, title, clip-name regexes, frames, view, last frame or 0)
ZOOMS = [
    ('G_zoom_belly', 'G. CLOSER, from the side, 12 frames: the clips that put him FLAT ON THE BELLY and bring him up over a knee',
     [r'Wounded#Hero_Torso_Back$', r'Wounded#(Merc_)?Run_Torso_(Front|Back)_03$', r'Wounded#Run_Torso_Back_02$', r'Impact_02#Running_', r'Impact_02#Run_Torso_Impact$',
      r'Get_Up_From_Stomach$', r'Die#Die_Forward$', r'Wounded#Crawl_Forward_0[14]$'], 12, 'side', 0),
    ('H_zoom_thrown', 'H. CLOSER, the FIRST 1.8 s only (frames 0 .. 44): the clips that throw a standing man',
     [r'Die#Die_Backwards$', r'Wounded#Stand_Torso_', r'HeadShot#Stand_Front_02$', r'Wounded#Hero_Torso_Front$', r'Wounded#Hero_Torso_Back$',
      r'Impact_02#Front_(Chest|Stomach|Left_Shoulder|Right_Shoulder)$', r'Down_Not_Dead#Down_Not_Dead_Get_Down$',
      r'Impact_02#(Shoot_Pose_Impact|Stand_impact)_\w+_UB$'], 12, 'quarter', 44),
    ('J_zoom_knee', 'J. CLOSER, from the side, THE RISE ONLY (the last 45 % of each clip, 12 frames): where is he UP ON A KNEE, and for how long',
     [r'Get_Up_From_Stomach$', r'Wounded#Hero_Torso_Back$', r'Wounded#Run_Torso_Back_02$', r'Impact_02#Running_torso_Front_3$', r'Wounded#Merc_Run_Torso_Back_03$',
      r'Wounded#Hero_Die_End$', r'Down_Not_Dead#Down_Not_Dead_Get_Up$'], 12, 'side', -45),
]


# ------------------------------------------------------------------ the clip reader
def _bits(buf, at, n):
    return int.from_bytes(buf[at >> 3:(at >> 3) + 8], 'little') >> (at & 7) & ((1 << n) - 1)


def _sbits(buf, at, n):
    v = _bits(buf, at, n)
    return v - (1 << n) if v >> (n - 1) else v


def frame_table(d, p):
    """The frame numbers of a track's keys ('IdxT', kl2 0x6663b0); None when the block is not one."""
    if d[p:p + 4] != b'IdxT':
        return None
    w, n = _bits(d, 8 * p + 34, 4), _bits(d, 8 * p + 38, 16)
    return [_bits(d, 8 * p + 54 + w * k, w) for k in range(n)]


def rotation_keys(d, p, n):
    """n quaternions (x, y, z, w) as kl2 0x834170 unpacks them."""
    h = d[p]; drop = h & 3; single = h >> 2 & 1; B = h >> 3 & 0x1f
    if B == 0x1f:
        return [struct.unpack_from('<4f', d, p + 4 + 16 * k) for k in range(n)]
    scale = 1.0 / ((1 << (B - 1)) - 1)
    base = [_sbits(d, 8 * p + 8 + B * i, B) for i in range(3)]
    at = 8 * p + 8 + 3 * B
    if single:
        vals, sgs = [[b * scale for b in base]] * n, [_bits(d, at, 1)] * n
    else:
        w = [_bits(d, at + 5 * i, 5) for i in range(3)]; at += 15
        rec = sum(w) + 1; vals, sgs = [], []
        for k in range(n):
            a = at + rec * k; sgs.append(_bits(d, a, 1)); a += 1; v = []
            for i in range(3):
                v.append((base[i] + (_bits(d, a, w[i]) if w[i] else 0)) * scale); a += w[i]
            vals.append(v)
    out = []
    for v, sg in zip(vals, sgs):
        q = [0.0] * 4
        for i, x in zip([i for i in range(4) if i != drop], v):
            q[i] = x
        q[drop] = math.sqrt(max(0.0, 1.0 - sum(x * x for x in v))) * (-1.0 if sg else 1.0)
        out.append(tuple(q))
    return out


class Clip:
    """One clip of a kl_anm.Anm: frames, fps, events [(id, frame)], tracks {BONE NAME (upper): (rot frames, quats,
    pos frames, places)}. ci = clip index; own = kl_anm.owners(a)."""

    def __init__(self, a, own, ci):
        r = a.clips[ci]
        self.ci, self.name = ci, a.names[ci]
        self.frames, self.fps = struct.unpack_from('<hh', r, 2)
        self.off = struct.unpack_from('<i', r, 0xc)[0]
        self.root_vec = struct.unpack_from('<3f', r, 0x18)
        self.upper_only = bool(struct.unpack_from('<I', r, 0x28)[0] & 0x10)
        blk, nev = own[self.off]
        d, o = a.data, blk[0] + 8 * nev
        self.events = [struct.unpack_from('<IH', d, blk[0] + 8 * k) for k in range(nev)]
        self.tracks = {}
        for k in range(struct.unpack_from('<i', d, o + 0x1c)[0]):
            r0, r1, p0, p1, bone = struct.unpack_from('<5i', d, o + 0x24 + 0x14 * k)
            name = a.bones[bone].upper() if 0 <= bone < len(a.bones) else '#%d' % bone
            rf = frame_table(d, o + r0) or [0]
            pf = frame_table(d, o + p0) or [0]
            self.tracks[name] = (rf, rotation_keys(d, o + r1, len(rf)), pf,
                                 [struct.unpack_from('<3f', d, o + p1 + 12 * i) for i in range(len(pf))])

    def local(self, bone, f):
        """(quaternion, place) of a tracked bone at frame f (a float), or None."""
        t = self.tracks.get(bone)
        if t is None:
            return None
        rf, rq, pf, pp = t
        k, u = _span(rf, f)
        a, b = rq[k], rq[min(k + 1, len(rq) - 1)]
        if a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3] < 0:
            b = (-b[0], -b[1], -b[2], -b[3])
        q = [a[i] + (b[i] - a[i]) * u for i in range(4)]
        n = math.sqrt(sum(x * x for x in q)) or 1.0
        k2, u2 = _span(pf, f)
        a, b = pp[k2], pp[min(k2 + 1, len(pp) - 1)]
        return tuple(x / n for x in q), tuple(a[i] + (b[i] - a[i]) * u2 for i in range(3))

    def root_travel(self):
        """(forward, right, up) of the GROUND bone from the first to the last frame; forward is -z."""
        a, b = self.local('GROUND', 0), self.local('GROUND', self.frames - 1)
        if not a or not b:
            return None
        return (-(b[1][2] - a[1][2]), b[1][0] - a[1][0], b[1][1] - a[1][1])


def _span(frames, f):
    if f <= frames[0]:
        return 0, 0.0
    for k in range(len(frames) - 1):
        if frames[k] <= f <= frames[k + 1]:
            return k, (f - frames[k]) / float(frames[k + 1] - frames[k] or 1)
    return len(frames) - 1, 0.0


# ------------------------------------------------------------------ matrices (3x3 as 9 floats by rows, column vectors)
def _qmat(q):
    x, y, z, w = q
    return (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
            2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
            2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y))


def _mm(a, b):
    return (a[0] * b[0] + a[1] * b[3] + a[2] * b[6], a[0] * b[1] + a[1] * b[4] + a[2] * b[7], a[0] * b[2] + a[1] * b[5] + a[2] * b[8],
            a[3] * b[0] + a[4] * b[3] + a[5] * b[6], a[3] * b[1] + a[4] * b[4] + a[5] * b[7], a[3] * b[2] + a[4] * b[5] + a[5] * b[8],
            a[6] * b[0] + a[7] * b[3] + a[8] * b[6], a[6] * b[1] + a[7] * b[4] + a[8] * b[7], a[6] * b[2] + a[7] * b[5] + a[8] * b[8])


def _mv(a, v):
    return (a[0] * v[0] + a[1] * v[1] + a[2] * v[2], a[3] * v[0] + a[4] * v[1] + a[5] * v[2], a[6] * v[0] + a[7] * v[1] + a[8] * v[2])


def _mt(a):
    return (a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8])


def _roty(deg):
    t = math.radians(deg); s, c = math.sin(t), math.cos(t)
    return (c, 0, s, 0, 1, 0, -s, 0, c)


def _rotx(deg):
    t = math.radians(deg); s, c = math.sin(t), math.cos(t)
    return (1, 0, 0, 0, c, -s, 0, s, c)


# ------------------------------------------------------------------ the model
class Model:
    """A character model ready to pose: skeleton (names upper-case, parents, rest matrices and places, rest LOCAL
    transforms, 'follow' for untracked helpers) and its mesh objects of one variant / lod."""

    def __init__(self, lv, hero=1, variant=2, lod=2, plain=False, root=None):
        import kl_chars as C, kl_prmgraph as G, kl_texmat as T, kl_view as V
        p = G.read(lv['.prm'], 'dd'); mat = T.read_mat(lv['.MAT'])
        if root is None:
            sc, _ = lv.scene()
            root = C.person(sc, C.find_node(sc, C.HERO % hero))[0]
        self.root = root
        sk = C.skeleton(p, root)
        self.names = [s.upper() for s in C.bone_names(p, sk)]
        self.par = C.bone_parents(p, sk)
        rest = C._rest(p, sk)
        self.rest_r = [tuple(r[:9]) for r in rest]
        self.rest_t = [tuple(r[9:12]) for r in rest]
        self.rest_local = []
        for b, pa in enumerate(self.par):
            if pa < 0:
                self.rest_local.append((self.rest_r[b], self.rest_t[b]))
            else:
                inv = _mt(self.rest_r[pa])
                d = tuple(self.rest_t[b][i] - self.rest_t[pa][i] for i in range(3))
                self.rest_local.append((_mm(inv, self.rest_r[b]), _mv(inv, d)))
        tx = None if plain else V.Textures(mat, T.read_tex(lv['.TEX']))
        self.objects = []
        for o in C.objects(p, root):
            ch = p.chunks[o]
            if ch[0x0f] != variant or ch[0x0e] != lod:
                continue
            nm = mat.insts[p.u16(o, 0x12)].name.split('/')[-1]
            if 'eye_Outer' in nm or 'Eyelash' in nm or 'Glass' in nm:
                continue
            pal = C._palette(p, o)
            d = p.u32(p.u32(o, 0x28), 0); v = p.chunks[p.u32(d, 4)]
            verts, uv = [], []
            for k in range(p.u32(d, 0)):
                q = struct.unpack_from('<3f', v, 52 * k); w = list(struct.unpack_from('<3f', v, 52 * k + 12)); w.append(1 - sum(w))
                uv.append(struct.unpack_from('<2f', v, 52 * k + 36))
                verts.append((q, [(pal[v[52 * k + 24 + j] // 3], w[j]) for j in range(4) if w[j] > 1e-3]))
            col = (200, 60, 60) if 'Mask' in nm else (90, 150, 90) if 'MoneyBag' in nm else (190, 170, 150)
            self.objects.append((verts, V.mesh(p, o)[1], col, uv, tx.of(p.u16(o, 0x12)) if tx else None))
        if not self.objects:
            raise ValueError('model %d has no mesh of variant %d, lod %d' % (root, variant, lod))

    def follow(self, clip):
        """{untracked bone: tracked sibling with the same rest matrix} (the forearm twist bones)."""
        out = {}
        for b, n in enumerate(self.names):
            if n in clip.tracks or self.par[b] < 0:
                continue
            for s, m in enumerate(self.names):
                if s != b and self.par[s] == self.par[b] and m in clip.tracks and \
                        max(abs(x - y) for x, y in zip(self.rest_r[s] + self.rest_t[s], self.rest_r[b] + self.rest_t[b])) < 1e-3:
                    out[b] = s
                    break
        return out

    def world(self, clip, f, follow=None):
        """[(rotation, place)] of every bone at frame f."""
        follow = self.follow(clip) if follow is None else follow
        W = [None] * len(self.names)
        for b, n in enumerate(self.names):                 # parents come before their children in the file
            if b in follow:
                W[b] = W[follow[b]] if W[follow[b]] else None
                if W[b]:
                    continue
            loc = clip.local(n, f)
            r, t = (_qmat(loc[0]), loc[1]) if loc else self.rest_local[b]
            pa = self.par[b]
            if pa < 0 or W[pa] is None:
                W[b] = (r, t)
            else:
                pr, pt = W[pa]
                d = _mv(pr, t)
                W[b] = (_mm(pr, r), (pt[0] + d[0], pt[1] + d[1], pt[2] + d[2]))
        return W

    def posed(self, clip, f, follow=None):
        """[(positions, triangles, colour, uv, texture)] at frame f, in the clip's own space, + the bone list."""
        W = self.world(clip, f, follow)
        S = []
        for b in range(len(W)):
            m = _mm(W[b][0], _mt(self.rest_r[b]))
            d = _mv(m, self.rest_t[b])
            S.append((m, (W[b][1][0] - d[0], W[b][1][1] - d[1], W[b][1][2] - d[2])))
        out = []
        for verts, tris, col, uv, tex in self.objects:
            pos = []
            for q, ws in verts:
                x = y = z = 0.0
                for b, w in ws:
                    m, o = S[b]
                    x += w * (m[0] * q[0] + m[1] * q[1] + m[2] * q[2] + o[0])
                    y += w * (m[3] * q[0] + m[4] * q[1] + m[5] * q[2] + o[1])
                    z += w * (m[6] * q[0] + m[7] * q[1] + m[8] * q[2] + o[2])
                pos.append((x, y, z))
            out.append((pos, tris, col, uv, tex))
        return out, W

    def bone(self, name):
        return self.names.index(name)

    # ---- the body's attitude, from the keys alone (no renderer): what `phases`, `trunk` and `check` use
    def _shoulders(self):
        for l, r in (('LEFT_UPPERARM', 'RIGHT_UPPERARM'), ('LEFT_CLAVICLE', 'RIGHT_CLAVICLE')):
            if l in self.names and r in self.names:
                return self.bone(l), self.bone(r)
        raise KeyError('no shoulder bones')

    def _chest(self, P):
        ls, rs = self._shoulders()
        up = _unit(_sub(P[self.bone('HEAD')], P[self.bone('PELVIS')]))
        return _unit(_cross(_sub(P[rs], P[ls]), up)), up

    def attitude(self, clip, f, follow=None):
        """{up: y of the pelvis->head line (1 = upright, 0 = flat), chest: y of the chest's normal (-1 = chest
        down, +1 = chest up; its sign is fixed by the toes of the rest pose), pelvis / head / knee: heights over
        the GROUND bone (knee = the lower of the two calf bones' origins)}."""
        if not hasattr(self, '_sgn'):
            toe = _unit(_sub(self.rest_t[self.bone('LEFT_TOE')], self.rest_t[self.bone('LEFT_FOOT')]))
            self._sgn = 1.0 if _dot(self._chest(self.rest_t)[0], toe) > 0 else -1.0
        P = [w[1] for w in self.world(clip, f, follow)]
        g = P[0][1]
        cn, up = self._chest(P)
        return {'up': up[1], 'chest': self._sgn * cn[1], 'pelvis': P[self.bone('PELVIS')][1] - g, 'head': P[self.bone('HEAD')][1] - g,
                'knee': min(P[self.bone('LEFT_CALF')][1], P[self.bone('RIGHT_CALF')][1]) - g}


def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def pose_word(at):
    """One word for an attitude. The limits are this tool's own (the review's, re/anim_shot_review.md M1):
    STANDS = trunk up over 0.8 with the pelvis over 65; KNEELS = trunk up over 0.8, pelvis under 65, a knee under
    22 (an UPRIGHT kneel or deep crouch); lying = trunk under 0.5 with the head under 60: BELLY / BACK / SIDE by
    the chest's normal; everything else (bent over, on all fours, falling) is 'bent'."""
    if at['up'] > 0.8:
        return 'STANDS' if at['pelvis'] > 65 else 'KNEELS' if at['knee'] < 22 else 'crouch'
    if abs(at['up']) < 0.5 and at['head'] < 60:
        return 'BELLY' if at['chest'] < -0.5 else 'BACK' if at['chest'] > 0.5 else 'SIDE'
    return 'bent'


def phases(model, clip):
    """[(word, first frame, last frame)] over the whole clip; [] for an upper-body clip (its legs are not its own)."""
    if clip.upper_only or 'PELVIS' not in clip.tracks:
        return []
    fol, out = model.follow(clip), []
    for f in range(clip.frames):
        w = pose_word(model.attitude(clip, f, fol))
        if out and out[-1][0] == w:
            out[-1][2] = f
        else:
            out.append([w, f, f])
    return [tuple(x) for x in out]


def phase_text(ph, least=4):
    """'STANDS 0-12, bent 13-38, BELLY 39-98, ...' - runs shorter than `least` frames are folded into 'bent'."""
    out = []
    for w, a, b in ph:
        if b - a + 1 < least:
            w = 'bent'
        if out and out[-1][0] == w:
            out[-1][2] = b
        else:
            out.append([w, a, b])
    return ', '.join('%s %d-%d' % tuple(x) if x[1] != x[2] else '%s %d' % (x[0], x[1]) for x in out)


# ------------------------------------------------------------------ pictures
VIEWS = {'side': (180, 0), 'quarter': (145, 12), 'front': (90, 0)}      # (turn about y, tilt down), then seen along +x


def render_row(model, clip, k=8, w=200, h=180, view='quarter', frames=None, to=0):
    """K panels of one clip -> (list of frame numbers, bytearray rgb of size (k*w) x h)."""
    import kl_view as V
    yaw, tilt = VIEWS[view]
    cam = _mm(_rotx(tilt), _roty(yaw))
    n = min(clip.frames, to + 1) if to > 0 else clip.frames
    first = round((n - 1) * (1 + to / 100.0)) if to < 0 else 0     # to < 0: only the last |to| per cent of the clip
    fs = frames or ([0] if n <= 1 else [round(first + i * (n - 1 - first) / float(k - 1)) for i in range(k)])
    follow = model.follow(clip)
    out = bytearray(w * len(fs) * h * 3)
    span = 225.0                                           # model units across a panel: a lying man is ~185 long
    vh = span * h / w
    pel = model.bone('PELVIS')
    for i, f in enumerate(fs):
        items, W = model.posed(clip, f, follow)
        g = W[0][1]                                        # the GROUND bone: the floor under him
        c = _mv(cam, W[pel][1]); gy = _mv(cam, (W[pel][1][0], g[1], W[pel][1][2]))
        box = (c[2] - span / 2, c[2] + span / 2, gy[1] - 0.08 * vh, gy[1] + 0.92 * vh)
        v = V.View(w, h, box, 'side', bg=(46, 50, 58))
        # the floor: a line at his ground height
        fy = int((box[3] - gy[1]) / (box[3] - box[2]) * h)
        if 0 <= fy < h:
            for x in range(w):
                v.rgb[3 * (fy * w + x):3 * (fy * w + x) + 3] = b'\x70\x74\x7c'
        for pos, tris, col, uv, tex in items:
            v.draw([_mv(cam, q) for q in pos], tris, col, uv, tex)
        for y in range(h):
            out[(y * w * len(fs) + i * w) * 3:(y * w * len(fs) + i * w + w) * 3] = v.rgb[y * w * 3:(y + 1) * w * 3]
    return fs, out


class Canvas:
    def __init__(self, w, h, bg=(24, 26, 30)):
        self.w, self.h = w, h
        self.rgb = bytearray(bytes(bg) * (w * h))

    def blit(self, x, y, w, h, rgb):
        for r in range(h):
            if 0 <= y + r < self.h:
                n = min(w, self.w - x)
                self.rgb[((y + r) * self.w + x) * 3:((y + r) * self.w + x + n) * 3] = rgb[r * w * 3:(r * w + n) * 3]

    def save(self, path):
        raw = b''.join(b'\0' + bytes(self.rgb[y * self.w * 3:(y + 1) * self.w * 3]) for y in range(self.h))

        def ch(t, d):
            return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0))
                               + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))


def text_block(w, h, lines, bg=(24, 26, 30), face='Segoe UI'):
    """A w x h rgb block with text drawn by GDI. lines: [(x, y, size, bold, (r, g, b), string)]."""
    import ctypes
    g, u = ctypes.windll.gdi32, ctypes.windll.user32
    P = ctypes.c_void_p
    for f in ('CreateCompatibleDC', 'CreateDIBSection', 'CreateFontW', 'SelectObject'):
        getattr(g, f).restype = P
    g.CreateCompatibleDC.argtypes = (P,)
    g.SelectObject.argtypes = (P, P)
    g.DeleteObject.argtypes = (P,)
    g.DeleteDC.argtypes = (P,)
    g.TextOutW.argtypes = (P, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int)
    g.SetTextColor.argtypes = (P, ctypes.c_uint)
    g.SetBkMode.argtypes = (P, ctypes.c_int)
    g.CreateFontW.argtypes = (ctypes.c_int,) * 5 + (ctypes.c_uint,) * 8 + (ctypes.c_wchar_p,)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', ctypes.c_uint), ('biWidth', ctypes.c_int), ('biHeight', ctypes.c_int), ('biPlanes', ctypes.c_ushort),
                    ('biBitCount', ctypes.c_ushort), ('biCompression', ctypes.c_uint), ('biSizeImage', ctypes.c_uint),
                    ('a', ctypes.c_int), ('b', ctypes.c_int), ('c', ctypes.c_uint), ('d', ctypes.c_uint)]
    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    g.CreateDIBSection.argtypes = (P, ctypes.POINTER(BIH), ctypes.c_uint, ctypes.POINTER(P), P, ctypes.c_uint)
    dc = g.CreateCompatibleDC(None)
    bits = P()
    bm = g.CreateDIBSection(dc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
    old = g.SelectObject(dc, bm)
    fill = bytes((bg[2], bg[1], bg[0], 0)) * (w * h)
    ctypes.memmove(bits, fill, len(fill))
    g.SetBkMode(dc, 1)
    fonts = {}
    for x, y, size, bold, col, s in lines:
        key = (size, bold)
        if key not in fonts:
            fonts[key] = g.CreateFontW(-size, 0, 0, 0, 700 if bold else 400, 0, 0, 0, 0, 0, 0, 4, 0, face)
        g.SelectObject(dc, fonts[key])
        g.SetTextColor(dc, col[0] | col[1] << 8 | col[2] << 16)
        g.TextOutW(dc, x, y, s, len(s))
    g.GdiFlush()
    raw = ctypes.string_at(bits, w * h * 4)
    out = bytearray(w * h * 3)
    out[0::3], out[1::3], out[2::3] = raw[2::4], raw[1::4], raw[0::4]
    g.SelectObject(dc, old)
    for f in fonts.values():
        g.DeleteObject(f)
    g.DeleteObject(bm); g.DeleteDC(dc)
    return out


# ------------------------------------------------------------------ what a level's sets play
def load_anm(lv):
    import kl_anm
    a = kl_anm.Anm(lv['.ANM'], 'dd')
    return a, kl_anm.owners(a)


def slot_census(a, rx, sets=SETS):
    """[(slot id, slot name, {set: [(condition word, clip index)] or None})] for the slots matching rx."""
    L = {s: a.col(s).lists() for s in sets if any(c.short == s for c in a.cols)}
    out = []
    for sid in sorted(range(len(a.slots)), key=lambda i: a.slots[i]):
        if rx.search(a.slots[sid]) and any(sid in L[s] for s in L):
            out.append((sid, a.slots[sid], {s: L[s].get(sid) for s in L}))
    return out


def weights(pairs):
    """The share of each pair of a slot's list in the game's draw (kl2 0x7c6750: bits 0-2 of the condition word are
    weights - 1.0; bit 2 -> 0.1; bit 1 x 0.33; bit 0 x 0.5 -, bits 3.. conditions: those pairs are left out here)."""
    ws = []
    for f, _ in pairs:
        if f >> 3:
            ws.append(None); continue
        w = 0.1 if f & 4 else 1.0
        if f & 2: w *= 0.33
        if f & 1: w *= 0.5
        ws.append(w)
    tot = sum(w for w in ws if w is not None) or 1.0
    return [None if w is None else w / tot for w in ws]


def candidates(a, own, families=FAMILIES):
    """The numbered clips of the `shot` sheets: [(number, family index, Clip, [slot names], {set names})],
    one entry per clip DATA (aliases of one data block are one clip)."""
    off = lambda ci: struct.unpack_from('<i', a.clips[ci], 0xc)[0]
    seen, out = {}, []
    for fi, (_, _, pat) in enumerate(families):
        for sid, name, per in slot_census(a, re.compile(pat)):
            for s, pairs in per.items():
                for f, ci in pairs or ():
                    o = off(ci)
                    if o not in own:
                        continue
                    if o not in seen:
                        seen[o] = len(out)
                        out.append([0, fi, ci, [], set()])
                    e = out[seen[o]]
                    if e[1] == fi and name not in e[3]:
                        e[3].append(name)
                    e[4].add(s)
    out.sort(key=lambda e: (e[1], a.slots.index(e[3][0]) if e[3] else 0))
    res = []
    for n, e in enumerate(out):
        res.append((n + 1, e[1], Clip(a, own, e[2]), e[3], e[4]))
    return res


def who(sets):
    h, b = bool(sets & set(HUMAN)), bool(sets & set(BOT))
    return 'human + AI heister sets' if h and b else 'AI heister (NPC) sets ONLY' if b else 'human sets ONLY'


EVENT_NOTE = {2: 'may be cut', 5: 'align', 6: 'aligned', 7: 'LANDS', 8: 'RISES / end of lying', 31: 'weapon', 36: 'RAGDOLL', 0: '?',
              22: '?', 23: '?', 10: 'weapon item: the action ACTS on it', 2000: 'hit'}


def _wrap(s, width=54, indent='    '):
    out = []
    while s:                                               # wrapped at a comma
        cut = len(s) if len(s) <= width else s.rfind(', ', 0, width) + 1 or len(s)
        out.append(s[:cut].strip()); s = (indent + s[cut:].strip()) if s[cut:].strip() else ''
    return out


def legend_lines(num, clip, slots, sets, pose=''):
    tr = clip.root_travel()
    ev = ', '.join('%d at %d%s' % (e, f, ' (%s)' % EVENT_NOTE[e] if EVENT_NOTE.get(e, '?') != '?' else '') for e, f in clip.events) or 'none'
    short = clip.name.split(':', 1)[-1]
    lines = ['%s' % short.replace('Dammage/', '').replace('Special_Moves/', ''),
             '%d frames = %.1f s at %d a second' % (clip.frames, (clip.frames - 1) / float(clip.fps or 25), clip.fps or 25),
             'root: %s' % ('%+.2f m forward, %+.2f m to his right' % (tr[0] / 100.0, tr[1] / 100.0) if tr else 'no root track')]
    if clip.upper_only:
        lines[2] = 'an UPPER-BODY clip: the legs shown are the rest pose'
    lines += _wrap('events: ' + ev)
    lines.append(who(sets))
    if pose:                                               # measured from the keys (pose_word), frame ranges
        lines += _wrap('pose: ' + pose)
    room = max(1, 11 - len(lines))                         # a row holds 11 lines
    for s in slots[:room]:
        lines.append(s)
    if len(slots) > room:
        lines[-1] = '%s  (+ %d more)' % (lines[-1][:40], len(slots) - room)
    return lines


# ------------------------------------------------------------------ the sheets
_G = {}


def _init(level, hero, variant, lod, plain):
    import kl_chars as C
    lv = C.Lv(level)
    _G['a'], _G['own'] = load_anm(lv)
    _G['m'] = Model(lv, hero, variant, lod, plain)


def _row(job):
    ci, k, w, h, view = job[:5]
    clip = Clip(_G['a'], _G['own'], ci)
    fs, rgb = render_row(_G['m'], clip, k, w, h, view, to=job[5] if len(job) > 5 else 0)
    return ci, fs, bytes(rgb), phase_text(phases(_G['m'], clip))


LABEL_W = 380


def compose(path, title, rows, k, w, h, cols=1, note=None):
    """rows: [(number, legend lines, frame numbers, rgb of the row)]."""
    rw = LABEL_W + k * w
    rh = h + 18
    per = (len(rows) + cols - 1) // cols
    head = 34 + (18 if note else 0)
    cv = Canvas(cols * rw + (cols - 1) * 12, head + per * rh)
    lines = [(8, 6, 20, True, (240, 240, 240), title)]
    if note:
        lines.append((8, 32, 13, False, (170, 175, 185), note))
    cv.blit(0, 0, cv.w, head, text_block(cv.w, head, lines))
    for i, (num, leg, fs, rgb) in enumerate(rows):
        x0, y0 = (i // per) * (rw + 12), head + (i % per) * rh
        tl = [(6, 2, 34 if num < 100 else 26, True, (255, 190, 60), '%d' % num)]
        green = False
        for j, s in enumerate(leg):
            green = s.startswith('pose:') or (green and s.startswith('    '))
            tl.append((64, 2 + 17 * j, 15 if j == 0 else 13, j == 0, (235, 235, 235) if j == 0 else (255, 150, 120) if 'ONLY' in s else
                       (150, 220, 150) if green else (170, 175, 185), s))
        cv.blit(x0, y0, LABEL_W, rh, text_block(LABEL_W, rh, tl))
        cv.blit(x0 + LABEL_W, y0, k * w, h, rgb)
        fl = [(j * w + 4, 1, 12, False, (150, 200, 255), 'frame %d  (%.1f s)' % (f, f / 25.0)) for j, f in enumerate(fs)]
        cv.blit(x0 + LABEL_W, y0 + h, k * w, 18, text_block(k * w, 18, fl))
    cv.save(path)


def run_rows(level, jobs, opt):
    import multiprocessing as mp
    args = (level, opt['hero'], opt['variant'], opt['lod'], opt['plain'])
    if opt['jobs'] <= 1:
        _init(*args)
        return dict((ci, (fs, rgb, ph)) for ci, fs, rgb, ph in map(_row, jobs))
    with mp.Pool(opt['jobs'], _init, args) as pool:
        return dict((ci, (fs, rgb, ph)) for ci, fs, rgb, ph in pool.imap_unordered(_row, jobs))


def cmd_shot(level, out, opt):
    import kl_chars as C
    lv = C.Lv(level)
    a, own = load_anm(lv)
    cand = candidates(a, own)
    k, w, h = opt['frames'], 200, 180
    done = run_rows(level, [(c.ci, k, w, h, opt['view']) for _, _, c, _, _ in cand], opt)
    os.makedirs(out, exist_ok=True)
    rows_all, legend = [], []
    for fi, (page, title, _) in enumerate(FAMILIES):
        rows = []
        for num, f, c, slots, sets in cand:
            if f != fi:
                continue
            leg = legend_lines(num, c, slots, sets, done[c.ci][2])
            rows.append((num, leg, done[c.ci][0], done[c.ci][1]))
            legend.append('%3d  %-6s %-52s %3d fr  ev %-44s root %-18s %s | %s' % (
                num, page[0], c.name.split(':', 1)[-1], c.frames, ','.join('%d@%d' % e for e in c.events) or '-',
                ('%+.0f fwd %+.0f right' % c.root_travel()[:2]) if c.root_travel() else '-', who(sets), ' ; '.join(slots)))
            if done[c.ci][2]:
                legend.append('       pose: ' + done[c.ci][2])
        if rows:
            compose(os.path.join(out, page + '.png'), title, rows, k, w, h,
                    note='stock %s, heister %d masked; frames evenly spread over the clip; the grey line is his floor; no weapon is drawn; he faces right at frame 0' % (level, opt['hero']))
            print('%s: %d clip(s), numbers %d .. %d' % (os.path.join(out, page + '.png'), len(rows), rows[0][0], rows[-1][0]))
        rows_all += rows
    for page, title, pats, zk, zview, zto in ZOOMS:
        pick = [e for e in cand if any(re.search(x, e[2].name) for x in pats)]
        zd = run_rows(level, [(c.ci, zk, w, h, zview, zto) for _, _, c, _, _ in pick], opt)
        compose(os.path.join(out, page + '.png'), title, [(num, legend_lines(num, c, slots, sets, zd[c.ci][2]), zd[c.ci][0], zd[c.ci][1]) for num, _, c, slots, sets in pick],
                zk, w, h, note="the numbers are the overview's")
        print('%s: %d clip(s)' % (os.path.join(out, page + '.png'), len(pick)))
    compose(os.path.join(out, 'overview.png'), "EVERY CLIP A HEISTER CAN PLAY WHEN HE IS SHOT - point at a number (the families' pages A .. F and I show the same rows; G, H, J are closer looks)",
            rows_all, k, w, h, cols=2,
            note='stock %s; rows 1 .. %d; orange = a clip only ONE side\'s sets have (all others: human AND AI heister sets); green = his pose by frame, measured from the keys' % (level, len(rows_all)))
    open(os.path.join(out, 'legend.txt'), 'w').write('\n'.join(legend) + '\n')
    print('%s: %d clips' % (os.path.join(out, 'overview.png'), len(rows_all)))


def cmd_sheet(level, out, pats, opt):
    import kl_chars as C
    lv = C.Lv(level)
    a, own = load_anm(lv)
    rx = [re.compile(x, re.I) for x in pats]
    fam = [('x', 'x', x) for x in pats]
    cand = candidates(a, own, fam)
    have = {c.off for _, _, c, _, _ in cand}
    off = lambda ci: struct.unpack_from('<i', a.clips[ci], 0xc)[0]
    n = len(cand)
    for ci, nm in enumerate(a.names):                      # clips by NAME that no heister slot of the patterns has
        if any(r.search(nm) for r in rx) and off(ci) in own and off(ci) not in have:
            have.add(off(ci)); n += 1
            cand.append((n, 0, Clip(a, own, ci), [], set()))
    k, w, h = opt['frames'], 200, 180
    done = run_rows(level, [(c.ci, k, w, h, opt['view'], opt['to']) for _, _, c, _, _ in cand], opt)
    rows = [(num, legend_lines(num, c, slots, sets, done[c.ci][2]) if sets else legend_lines(num, c, slots, sets, done[c.ci][2]) + ['(by clip name: in no slot asked for)'],
             done[c.ci][0], done[c.ci][1]) for num, _, c, slots, sets in cand]
    compose(out, ' | '.join(pats), rows, k, w, h, cols=2 if len(rows) > 12 else 1)
    print('%s: %d clip(s)' % (out, len(rows)))


def cmd_list(level, pat):
    import kl_chars as C
    a, own = load_anm(C.Lv(level))
    off = lambda ci: struct.unpack_from('<i', a.clips[ci], 0xc)[0]
    print('%s: %d sets (%s ...), %d slots, %d clips' % (level, len(a.cols), ', '.join(c.short for c in a.cols[:8]), len(a.slots), len(a.clips)))
    differ = 0
    for sid, name, per in slot_census(a, re.compile(pat)):
        kinds = collections.OrderedDict()
        for s, pairs in per.items():
            kinds.setdefault(None if pairs is None else tuple((f, off(ci)) for f, ci in pairs), [pairs, []])[1].append(s)
        differ += len(kinds) > 1
        print('%4d %s' % (sid, name))
        for key, (pairs, ss) in kinds.items():
            if len(kinds) > 1:
                print('      [%s]' % ', '.join(ss))
            if pairs is None:
                print('          (no list)'); continue
            for (f, ci), wt in zip(pairs, weights(pairs)):
                c = Clip(a, own, ci) if off(ci) in own else None
                tr = c.root_travel() if c else None
                print('          %-9s cond %-2x clip %5d %-50s %3d fr  ev %-34s %s%s' % (
                    'CONDITION' if wt is None else '%3.0f %%' % (100 * wt), f, ci, a.names[ci].split(':', 1)[-1], struct.unpack_from('<h', a.clips[ci], 2)[0],
                    ','.join('%d@%d' % e for e in c.events) if c and c.events else '-',
                    'root %+.0f fwd' % tr[0] if tr else '', '  UPPER BODY' if c and c.upper_only else ''))
    print('slots where the four sets do not agree: %d' % differ)


def cmd_check(level, opt):
    import kl_chars as C
    lv = C.Lv(level)
    a, own = load_anm(lv)
    m = Model(lv, opt['hero'], opt['variant'], opt['lod'], True)
    ci = next(i for i, nm in enumerate(a.names) if 'Soldier/Stand#' in nm and struct.unpack_from('<i', a.clips[i], 0xc)[0] in own)
    c = Clip(a, own, ci)
    W = m.world(c, 0)
    print('%s: model %d, %d bones, %d with a track in %s' % (level, m.root, len(m.names), sum(n in c.tracks for n in m.names), c.name))
    worst = 0.0
    for n in ('PELVIS', 'SPINE_2', 'HEAD', 'LEFT_HAND', 'RIGHT_HAND', 'LEFT_CALF', 'RIGHT_CALF', 'LEFT_FOOT', 'RIGHT_FOOT', 'LEFT_TOE'):
        b = m.bone(n)
        d = math.sqrt(sum((W[b][1][i] - m.rest_t[b][i]) ** 2 for i in range(3)))
        if 'HAND' not in n:
            worst = max(worst, d)
        print('   %-12s posed (%6.1f %6.1f %6.1f)  rest (%6.1f %6.1f %6.1f)  apart %5.1f' % ((n,) + W[b][1] + m.rest_t[b] + (d,)))
    ok = worst < 40
    print('%s: a standing clip puts trunk, head and legs within %.0f of the rest pose (a wide stance; the arms hold a gun)' % ('ok' if ok else 'FAIL', worst))
    # two proofs by the clips' NAMES (the review's): which way is the chest
    for pat, f_of, want, say in ((r'#Get_Up_From_Stomach$', lambda c: 0, -1, 'starts chest DOWN'), (r'Die#Die_Backwards$', lambda c: c.frames - 1, 1, 'ends chest UP'),
                                 (r'Die#Die_Forward$', lambda c: c.frames - 1, -1, 'ends chest DOWN')):
        ci = next((i for i, nm in enumerate(a.names) if re.search(pat, nm) and struct.unpack_from('<i', a.clips[i], 0xc)[0] in own), None)
        if ci is None:
            print('   (no clip %s in this level: not proven here)' % pat); continue
        c = Clip(a, own, ci); f = f_of(c)
        at = m.attitude(c, f)
        good = at['chest'] * want > 0.5 and abs(at['up']) < 0.5
        ok = ok and good
        print('   %s: %s frame %d: trunk up %+.2f, chest normal y %+.2f, head %.0f over the floor = %s (%s)' % (
            'ok' if good else 'FAIL', c.name.split(':', 1)[-1], f, at['up'], at['chest'], at['head'], pose_word(at), say))
    print('PASS: the pose reader fits this skeleton (standing clip within %.0f of the rest pose; from-stomach starts chest down, backwards ends chest up, forward ends chest down)' % worst
          if ok else 'FAIL: the pose reader does not fit this skeleton')


def cmd_trunk(level, pats, opt):
    """Per clip: the pose word by frame ranges, and the numbers behind it at 16 frames."""
    import kl_chars as C
    lv = C.Lv(level)
    a, own = load_anm(lv)
    m = Model(lv, opt['hero'], opt['variant'], opt['lod'], True)
    off = lambda ci: struct.unpack_from('<i', a.clips[ci], 0xc)[0]
    seen = set()
    for ci, nm in enumerate(a.names):
        if off(ci) not in own or off(ci) in seen or not any(re.search(p, nm) for p in pats):
            continue
        seen.add(off(ci))
        c = Clip(a, own, ci)
        ph = phases(m, c)
        print('%5d %s (%d frames)\n      %s' % (ci, nm.split(':', 1)[-1], c.frames, phase_text(ph, 1) or 'an upper-body clip'))
        kn = [(x[1], x[2]) for x in ph if x[0] == 'KNEELS']
        print('      upright kneel: %s' % (', '.join('%d-%d = %.1f s' % (p, q, (q - p + 1) / float(c.fps or 25)) for p, q in kn) or 'NONE'))
        if ph:
            fol = m.follow(c)
            for f in sorted(set(round(i * (c.frames - 1) / 15.0) for i in range(16))):
                at = m.attitude(c, f, fol)
                print('        f %3d  up %+.2f chest %+.2f pelvis %4.0f head %4.0f knee %3.0f  %s' % (f, at['up'], at['chest'], at['pelvis'], at['head'], at['knee'], pose_word(at)))


def main():
    argv = sys.argv[1:]
    opt = {'hero': 1, 'variant': 2, 'lod': 2, 'frames': 8, 'view': 'quarter', 'jobs': max(1, (os.cpu_count() or 2) - 2), 'plain': False, 'to': 0}
    a = []
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == '--plain':
            opt['plain'] = True
        elif x.startswith('--') and x[2:] in opt:
            opt[x[2:]] = argv[i + 1] if x == '--view' else int(argv[i + 1]); i += 1
        else:
            a.append(x)
        i += 1
    if len(a) >= 2 and a[0] == 'list':
        cmd_list(a[1], a[2] if len(a) > 2 else LIST_RX)
    elif len(a) == 3 and a[0] == 'shot':
        cmd_shot(a[1], a[2], opt)
    elif len(a) >= 4 and a[0] == 'sheet':
        cmd_sheet(a[1], a[2], a[3:], opt)
    elif len(a) == 2 and a[0] == 'check':
        cmd_check(a[1], opt)
    elif len(a) >= 3 and a[0] == 'trunk':
        cmd_trunk(a[1], a[2:], opt)
    else:
        print(__doc__); sys.exit(1)


if __name__ == '__main__':
    main()
