"""Dead Men cover boxes that Dog Days' cover list cannot see -> new Dog Days cover boxes (ANP_COVERS).

  ANP_COVERS=box (default)  add them (below);  ANP_COVERS=off / 0  nothing added, the build is byte-identical.
  Filters on the planned boxes (14 Oct, M02 regression; all three =keep gives the rel5 build byte for byte):
  ANP_COVERS_TILTED=auto (default): a tilted Dead Men box is rebuilt upright only when no other cover box already
      holds >= TILT_SHARE of its footprint, and a rebuilt 'H' box lower than HIGH_MIN cm becomes low. M02: all 11 tipped
      StonewoolBags CoverBoxH_01 lie on a CoverBoxM the designers placed beside them (9 of them >= 100%: dropped; they
      were 113 cm 'high' covers on the same spot as the low box, H_7 at Lynch's scripted LynchCoverLoc). drop = never
      rebuilt; keep = always (rel5).
  ANP_COVERS_DUP=skip (default): no new upright box when >= DUP_SHARE of its footprint lies in an existing list box or
      a kept new one; keep = rel5.
  ANP_COVERS_FLOOR=skip (default): no new box without floor beside it (Dog Days' own cover-point probe, modelled on the
      level .HVK with scripts/hvk_ray.py + kl-merge's kl_hvk; HVK_SRC set by port_level); keep = rel5.

Why (static RE of both exes, work/cover):
  Dog Days CFFCoverList slot 13 (kl2 0x6d6a80) keeps a scene geometry only if its NAME matches '*coverbox*'
  (0x8dfa90, case-insensitive) AND it is a ZSTDOBJ (0x200002); node flag 0x400 skips it; the cap is 5000.
  '*coverboxcar*' / '*coverboxm*' / '*coverboxl*' -> low, '*coverboxh*' -> high (0x603830(obj, high, 1, car)), the
  box = the node box (+0x30 centre, +0x40 half extents) through the node matrix; a box whose world up (m[4]) is
  < 0.717 is rejected (0x603886).
  Dead Men CFFCoverList slot 13 (kaneandlynch 0x66afc0) takes '*coverbox*' / '*covercylinder*' / '*coverarrow*' /
  '*coverspline*' of ANY class and has no tilt test. The converter keeps Dead Men's cover entities as they are, so
  Dog Days loses every Dead Men cover box that is a ZBoxPrimitive (0x2000e1, half extents = the last three props
  floats): 1,345 in the 16 story levels (M02 61, M08 242, M12 252, M13B 474, M14 126 ...), plus the tilted ZSTDOBJ
  prefab boxes (M01 13, M02 11 ...).

What this adds: for every lost box (name *coverbox[lmh]*, not *nocoverbox*; it and its ancestors without record flag
0x400; not inside a ZAllocMany) one NEW ZSTDOBJ 'ANP_CoverBoxH_<n>' (Dead Men H) or 'ANP_CoverBoxM_<n>' (Dead Men
L and M = Dog Days low) under a new ZGROUP 'ANP_Covers', the LAST child of graft's ANP_Tail. Every new entity is a
new node after all existing ones (graft._graft_tail asserts 0 moved; ovlcheck validates the build).
  * transform: the Dead Men box's world transform (relative to ANP_Tail), the box centre at the origin. A box that
    Dog Days would reject as tilted (world up < 0.717) is rebuilt UPRIGHT: y = world up, x = the horizontal part of
    the other box axis with the larger horizontal part, and the half extents ENCLOSE the tilted box (exactly the
    same box for a 90 degree tilt).
  * skipped: boxes whose largest half extent is < ANP_COVERS_MINHALF cm (default 15; 0 = keep all).
  * geometry: per box SIZE (half extents rounded to 0.1 cm) a copy of the mesh, the mesh list and the prim chunk
    (0x70100, bbox floats 8..13 = -half .. +half) of one of the level's own ZSTDOBJ cover boxes (every stock prim has
    its own mesh list and mesh); boxes of one size share the prim; the chunk refcounts are kept as the stock files
    have them (graft_hook's refs). Stock Dog Days cover boxes (L01 843, L03 1192, L07 758) all have ONE mesh of class
    0x80189 with render flags (mesh word 7) 0x800000, record flags 0x302 / 0x200 / 0x272 (0x702/0x600 = 0x400
    hidden) - never the 0x20000 of drawn geometry - and no .HVK collision (L01: 0 of 8323 shape instances are
    cover boxes). The template is picked to match exactly that (prefer flags 0x302, then 0x200, then 0x272), so a
    new box is drawn and collides exactly like a stock Dog Days cover box (not at all). New nodes are not in the
    .HVK / .oct anyway.

API (graft._graft_tail calls graft_hook after the wrapper subtree):
  graft_hook(out, spans, names, g, roff, par, typ, rep, new_chunk, tail_world, prm_next)
    -> None (off / nothing to add) or (recs, ops, refs):
       recs = [(64-byte gms record, name, (matrix offset, pos offset) in g)], one per new box;
       ops  = their prp nodes back to back (props, 0 events, 0 children). _graft_tail wraps them in the ZGROUP
              'ANP_Covers'. tail_world = (stored matrix, pos) of ANP_Tail; prm_next = index of the next new chunk.
       refs = {.prm chunk index: refcount to add} (prmconv.convert_prm_dm_to_dd ref_add; new chunks start at 1).
  Only the tail graft host calls it (ANP_GRAFT_HOST=old: no covers, the build report says so).
  PRM_SRC (module global) = the Dead Men .prm bytes (port_level sets it before graft()).
"""
import os, struct, fnmatch, math

ZSTDOBJ = 0x200002
ZBOXPRIM = 0x2000e1
ALLOC_T = 0x1000ca
PRM_MAX = 73728          # the engine's PRM chunk table holds at most this many entries
COVER_CAP = 5000         # kl2's cover list cap
UP_MIN = 0.717           # kl2 0x603886
PRM_SRC = None
HVK_SRC = None           # the Dead Men .HVK bytes (copied to the build as is): ANP_COVERS_FLOOR (port_level sets it)
DUP_SHARE = 0.9          # ANP_COVERS_DUP: an upright box is a duplicate when >= 90% of its footprint lies in another box
TILT_SHARE = 0.5         # ... a tilted rebuild when >= half of it does (Dead Men's replacement box beside it)
DUP_DY = 60.0            # ... whose centre is within this many cm in height
HIGH_MIN = 150.0         # ANP_COVERS_TILTED=auto: a rebuilt tilted 'H' box lower than this (cm) is classed low
IDENT9 =(0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
TEMPLATE_FLAGS = (0x302, 0x200, 0x272)   # stock Dog Days cover-box record flags, most common first
COVER_MESH = (0x80189, 0x800000)         # stock Dog Days cover-box mesh: class, render flags (word 7)
SIZE_ROUND = 1           # half extents are rounded to 0.1 cm; boxes of one rounded size share one prim


def mode():
    return os.environ.get('ANP_COVERS', 'box').strip().lower()


def enabled():
    return mode() not in ('0', 'off', 'none', '')


def _opt(name, default, allowed):
    v = os.environ.get(name, default).strip().lower()
    if v not in allowed: raise SystemExit('%s=%s: use %s' % (name, v, ' or '.join(allowed)))
    return v


def dup_mode():
    """ANP_COVERS_DUP: skip (default) = no new upright box where >= DUP_SHARE of its footprint already lies in a cover
    box Dog Days takes (or in a new box kept before it; same height band); keep = add it anyway (rel5)"""
    return _opt('ANP_COVERS_DUP', 'skip', ('skip', 'keep'))


def tilted_mode():
    """ANP_COVERS_TILTED: auto (default) = a tilted Dead Men box is rebuilt upright only when it is not a duplicate
    (checked even with ANP_COVERS_DUP=keep); drop = never rebuilt; keep = always rebuilt (rel5)"""
    return _opt('ANP_COVERS_TILTED', 'auto', ('auto', 'drop', 'keep'))


def zbox_mode():
    """ANP_COVERS_ZBOX: skip (default) = no copy of an UPRIGHT Dead Men ZBoxPrimitive cover box: Dog Days already lists
    it (ZBoxPrimitive derives from ZSTDOBJ - RTTI; kl2 0x6d6a80 tests the ZSTDOBJ class mask [0x150c8a0]/[0x150c89c],
    which subclasses pass; stock DD levels hold 291 ZBoxPrimitive cover boxes, L02 73, L11 157; runtime covers= =
    ZSTDOBJ + ZBoxPrimitive in M02/M05/M06/M07/M08/M12/M13B/M14); a TILTED one is still rebuilt (kind tilted).
    keep = copy every one (rel5: each listed twice)"""
    return _opt('ANP_COVERS_ZBOX', 'skip', ('skip', 'keep'))


def _zbox_half(out, spans, i):
    s0, pe = _props(out, spans, i)
    fl = [o[2] for o in out[s0:pe] if o[1] & 0x7f == 10][-3:]
    return tuple(fl) if len(fl) == 3 and min(fl) > 0 else None


def floor_mode():
    """ANP_COVERS_FLOOR: skip (default) = no new box without a floor beside it (Dog Days' own rule for cover points,
    kl2 0x71fc30 -> 0x4a2710, modelled on the level's .HVK); keep = add it anyway (rel5)"""
    return _opt('ANP_COVERS_FLOOR', 'keep', ('skip', 'keep'))

def _m(n, p):
    return fnmatch.fnmatch(n.lower(), p)


def dm_class(name):
    """Dead Men list box class of a name -> 'H' / 'M' (Dog Days class: L and M are both low) or None"""
    if _m(name, '*nocoverbox*'): return None
    if _m(name, '*coverboxh*'): return 'H'
    if _m(name, '*coverboxm*') or _m(name, '*coverboxl*'): return 'M'
    return None


# kl2 0x6be1c0: w = v.x*(m6,m7,m8) + v.y*(m3,m4,m5) + v.z*(m0,m1,m2)  (stored identity = [0,0,1,0,1,0,1,0,0])
def _rot(m, v):
    return [v[0] * m[6] + v[1] * m[3] + v[2] * m[0], v[0] * m[7] + v[1] * m[4] + v[2] * m[1],
            v[0] * m[8] + v[1] * m[5] + v[2] * m[2]]


def _cols(m):   # images of the local x, y, z axes
    return [m[6], m[7], m[8]], [m[3], m[4], m[5]], [m[0], m[1], m[2]]


def _stored(ex, ey, ez):
    return (ez[0], ez[1], ez[2], ey[0], ey[1], ey[2], ex[0], ex[1], ex[2])


def _mul(a, b):   # (a*b)(v) = a(b(v))
    ex, ey, ez = _cols(b)
    return _stored(_rot(a, ex), _rot(a, ey), _rot(a, ez))


def _tf(g, off):
    m_off, p_off = struct.unpack_from('<II', g, off + 4)
    return struct.unpack_from('<9f', g, m_off), struct.unpack_from('<3f', g, p_off)


def world(g, roff, par, i):
    """(stored matrix, position) of entity i in world space (parent chain of the gms record transforms)"""
    M, P = IDENT9, (0.0, 0.0, 0.0)
    chain = []
    while i != -1:
        chain.append(i); i = par[i]
    for q in reversed(chain):
        m, p = _tf(g, roff[q])
        r = _rot(M, p); P = (P[0] + r[0], P[1] + r[1], P[2] + r[2]); M = _mul(M, m)
    return M, P


def _inv(M, P):
    """inverse of a rigid stored transform"""
    ex, ey, ez = _cols(M)
    Mi = _stored([ex[0], ey[0], ez[0]], [ex[1], ey[1], ez[1]], [ex[2], ey[2], ez[2]])
    r = _rot(Mi, P)
    return Mi, (-r[0], -r[1], -r[2])


def _norm(v):
    l = math.sqrt(sum(x * x for x in v)); return [x / l for x in v] if l > 1e-9 else None


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def upright(M, half):
    """tilted box (stored M, half extents) -> (upright stored matrix, half extents along its x, y, z): x = the
    horizontal part of the box axis (not the one closest to world y) with the larger horizontal part, y = world up,
    z = x cross y; the new box ENCLOSES the old one (half'_j = sum_k |E[k].axis_j| * half[k]), so a 90 degree tilt
    gives the same box and an oblique one (a tipped rock) the smallest upright box around it with that yaw"""
    E = _cols(M)
    a = max(range(3), key=lambda k: abs(E[k][1]))           # the axis closest to world y = the height
    rest = sorted((k for k in range(3) if k != a), key=lambda k: -math.hypot(E[k][0], E[k][2]))
    b, c = rest
    x = _norm([E[b][0], 0.0, E[b][2]])
    if x is None: x = [1.0, 0.0, 0.0]
    y = [0.0, 1.0, 0.0]
    z = _cross(x, y)
    h = tuple(sum(abs(E[k][0] * ax[0] + E[k][1] * ax[1] + E[k][2] * ax[2]) * half[k] for k in range(3))
              for ax in (x, y, z))
    return _stored(x, y, z), h


def _props(out, spans, i):
    """(begin, end) op indices of entity i's props object: out[s0] = BeginObject, out[pe] = the event count"""
    s0 = spans[i + 1][0]; d = 0; j = s0
    while True:
        b = out[j][1] & 0x7f
        if b == 2: d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0: return s0, j + 1
        j += 1


def _arrays(ops):
    """op indices of the first [9] and [3] arrays and of the model int (first Int32 after them)"""
    a9 = a3 = mi = None; j = 0
    while j < len(ops):
        b = ops[j][1] & 0x7f
        if b == 1 and ops[j][2] == 9 and a9 is None: a9 = j; j += 10; continue
        if b == 1 and ops[j][2] == 3 and a9 is not None and a3 is None: a3 = j; j += 4; continue
        if b == 9 and a3 is not None and mi is None: mi = j
        j += 1
    return a9, a3, mi


def _prm_chunk(idx):
    off, cnt, _, _ = struct.unpack_from('<4I', PRM_SRC)
    if not 0 < idx < cnt: return None
    o, s, _, _ = struct.unpack_from('<4I', PRM_SRC, off + 16 * idx)
    return PRM_SRC[o:o + s]


def _prim_bbox(idx):
    c = _prm_chunk(idx)
    if c is None or len(c) != 64 or struct.unpack_from('<I', c)[0] != 0x70100: return None
    f = struct.unpack_from('<6f', c, 32)
    return f[:3], f[3:]


def _cover_mesh_ok(idx):
    """the prim has exactly one mesh, of the stock Dog Days cover-box kind (COVER_MESH)"""
    c = _prm_chunk(idx)
    if c is None or len(c) != 64 or struct.unpack_from('<I', c)[0] != 0x70100: return False
    w = struct.unpack_from('<16I', c)
    if w[5] != 1: return False
    ml = _prm_chunk(w[6])
    if not ml: return False
    m = _prm_chunk(struct.unpack_from('<I', ml)[0])
    return bool(m) and len(m) >= 32 and (struct.unpack_from('<I', m)[0], struct.unpack_from('<I', m, 28)[0]) == COVER_MESH


def min_half():
    """ANP_COVERS_MINHALF (cm, default 15): boxes whose largest half extent is smaller are skipped (Dead Men's
    10 x 10 x 10 marker boxes, e.g. M02 Special!CoverBoxes!CoverBoxH/M at y ~1003, give no cover); 0 = keep all"""
    try: return float(os.environ.get('ANP_COVERS_MINHALF', '15'))
    except ValueError: raise SystemExit('ANP_COVERS_MINHALF=%r: give a number of cm' % os.environ['ANP_COVERS_MINHALF'])


def _flag(g, roff, i):
    return struct.unpack_from('<I', g, roff[i] + 0x1c)[0]


def plan(out, spans, names, g, roff, par, typ, rep):
    """-> [dict(src, name, cls, M, P, half, kind)] (world space, box centred at P) for every lost Dead Men box"""
    res = []
    hidden = {}
    mh = min_half()
    def anc_bad(i):
        if i in hidden: return hidden[i]
        r = None
        if _flag(g, roff, i) & 0x400: r = 'hidden (flag 0x400)'
        elif typ[i] == ALLOC_T: r = 'inside a ZAllocMany'
        elif par[i] != -1: r = anc_bad(par[i])
        hidden[i] = r; return r
    for i, nm in enumerate(names):
        cls = dm_class(nm)
        if not cls: continue
        if typ[i] == ZBOXPRIM:
            s0, pe = _props(out, spans, i)
            fl = [o[2] for o in out[s0:pe] if o[1] & 0x7f == 10][-3:]
            if len(fl) != 3 or min(fl) <= 0:
                rep['covers: skipped ZBoxPrimitive without half extents'] += 1; continue
            centre, half, kind = (0.0, 0.0, 0.0), tuple(fl), 'box'
            if zbox_mode() == 'skip':
                if world(g, roff, par, i)[0][4] >= UP_MIN:
                    rep["covers: ZBoxPrimitive already in Dog Days' list, not copied (ANP_COVERS_ZBOX=skip)"] += 1; continue
                kind = 'tilted'
        elif typ[i] == ZSTDOBJ:
            M, _ = world(g, roff, par, i)
            if M[4] >= UP_MIN: continue                         # Dog Days takes it as it is
            bb = _prim_bbox(struct.unpack_from('<I', g, roff[i] + 0x0c)[0])
            if bb is None:
                rep['covers: skipped tilted ZSTDOBJ without a prim'] += 1; continue
            lo, hi = bb
            centre = tuple((lo[k] + hi[k]) / 2 for k in range(3)); half = tuple((hi[k] - lo[k]) / 2 for k in range(3))
            if min(half) <= 0:
                rep['covers: skipped tilted ZSTDOBJ with an empty bbox'] += 1; continue
            kind = 'tilted'
        else:
            rep['covers: skipped class %x (%s)' % (typ[i], nm[-40:])] += 1; continue
        why = anc_bad(i)
        if why:
            rep['covers: skipped %s' % why] += 1; continue
        if max(half) < mh:
            rep['covers: skipped degenerate box, largest half extent < %g cm (ANP_COVERS_MINHALF)' % mh] += 1; continue
        M, P = world(g, roff, par, i)
        c = _rot(M, centre); P = (P[0] + c[0], P[1] + c[1], P[2] + c[2])
        if M[4] < UP_MIN:
            h0 = half; up = max(abs(e[1]) for e in _cols(M))
            M, half = upright(M, half); rep['covers: rebuilt upright (%s)' % kind] += 1
            if up < 0.999:      # not a 90 degree tilt: the upright box encloses the tilted one
                rep['covers: rebuilt upright, oblique (%s): enclosing box' % kind] += 1
                rep['covers: oblique %s half (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f), axis up %.3f' % (
                    nm[-45:], h0[0], h0[1], h0[2], half[0], half[1], half[2], up)] += 1
            # ANP_COVERS_TILTED=auto: a tipped-over high box is as tall as it now stands (M02's StonewoolBags
            # CoverBoxH_01 lying on its side: 113 cm); Dog Days' high boxes are >= 198 cm (L01: 282 boxes, 198..274),
            # Dead Men's >= 150 -> below HIGH_MIN it becomes a low box
            if cls == 'H' and 2 * half[1] < HIGH_MIN and tilted_mode() == 'auto':
                cls = 'M'; rep['covers: tilted high box now %.0f cm tall -> low (ANP_COVERS_TILTED=auto)' % (2 * half[1])] += 1
        res.append(dict(src=i, name=nm, cls=cls, M=tuple(M), P=P, half=tuple(half), kind=kind))
    return _filter(res, existing_boxes(names, g, roff, par, typ, out, spans), rep)


def existing_boxes(names, g, roff, par, typ, out=None, spans=None):
    """the boxes Dog Days' list takes already (ZSTDOBJ *coverbox*, no 0x400 on it or above, upright; with
    ANP_COVERS_ZBOX=skip also the upright ZBoxPrimitive ones, not *nocoverbox*), world space, centred:
    [dict(name, M, P, half)]; a box without a readable prim bbox / half extents is left out"""
    res = []
    for i, nm in enumerate(names):
        if typ[i] == ZBOXPRIM and out is not None and zbox_mode() == 'skip' and _m(nm, '*coverbox*')                 and not _m(nm, '*nocoverbox*'):
            M, P = world(g, roff, par, i); hz = _zbox_half(out, spans, i)
            if M[4] >= UP_MIN and hz: res.append(dict(name=nm, M=tuple(M), P=tuple(P), half=hz))
            continue
        if typ[i] != ZSTDOBJ or not _m(nm, '*coverbox*'): continue
        q = i; bad = False
        while q != -1:
            if _flag(g, roff, q) & 0x400: bad = True; break
            q = par[q]
        if bad: continue
        M, P = world(g, roff, par, i)
        if M[4] < UP_MIN: continue
        bb = _prim_bbox(struct.unpack_from('<I', g, roff[i] + 0x0c)[0])
        if bb is None: continue
        lo, hi = bb
        c = _rot(M, tuple((lo[k] + hi[k]) / 2 for k in range(3)))
        res.append(dict(name=nm, M=tuple(M), P=(P[0] + c[0], P[1] + c[1], P[2] + c[2]),
                        half=tuple((hi[k] - lo[k]) / 2 for k in range(3))))
    return res


def _inside(pt, c, pad_y=0.0):
    ax = _cols(c['M']); d = [pt[k] - c['P'][k] for k in range(3)]
    return all(abs(sum(d[k] * ax[j][k] for k in range(3))) <= c['half'][j] + (pad_y if j == 1 else 0.0) + 1e-3
               for j in range(3))


def _overlap(a, b, n=6):
    """share of a's footprint (n x n grid at a's centre height) inside b"""
    ex, ey, ez = _cols(a['M']); h = a['half']; P = a['P']; k = 0
    for i in range(n):
        for j in range(n):
            u = -1 + 2 * (i + .5) / n; w = -1 + 2 * (j + .5) / n
            pt = (P[0] + u * h[0] * ex[0] + w * h[2] * ez[0], P[1] + u * h[0] * ex[1] + w * h[2] * ez[1],
                  P[2] + u * h[0] * ex[2] + w * h[2] * ez[2])
            k += _inside(pt, b, DUP_DY)
    return k / float(n * n)


_COLL = None


def _collision(rep):
    """the level's .HVK as a ray caster (scripts/hvk_ray.py on kl-merge's kl_hvk), or None (reported)"""
    global _COLL
    if _COLL is not None: return _COLL or None
    _COLL = False
    if HVK_SRC is None:
        rep['covers: WARNING ANP_COVERS_FLOOR: no .HVK, floor check skipped'] += 1; return None
    try:
        import sys, struct as _st
        import anp_paths
        for p in (os.path.join(anp_paths.KLMERGE, 'tools'), os.path.join(anp_paths.REPO, 'scripts')):
            if p not in sys.path: sys.path.insert(0, p)
        import kl_hvk, hvk_ray
        C = hvk_ray.Collision.__new__(hvk_ray.Collision)
        C.conv = 'col'; C.hvk = kl_hvk.Hvk(HVK_SRC); C.ents = {}; C.insts = []
        for s in C.hvk.shapes:          # = hvk_ray.Collision.__init__ without the scene (names are not needed)
            s.lverts = [_st.unpack_from('<3f', s.verts, k * s.vstride) for k in range(len(s.verts) // s.vstride)]
            if s.convex:
                s.lplanes = [_st.unpack_from('<4f', s.planes, 16 * k) for k in range(len(s.planes) // 16)]
            else:
                s.ltris = _st.unpack('<%dH' % (len(s.idx) // 2), s.idx)
                fl = []
                for _su, f, n in s.sub: fl += [f] * n
                s.triflags = fl
            for raw in s.inst:
                i = hvk_ray.Inst(); i.shape = s; i.ref = kl_hvk.ref(raw)
                i.P = _st.unpack_from('<3f', raw, 0); i.R = _st.unpack_from('<9f', raw, 12)
                w = [C.to_world(i, v) for v in s.lverts]
                i.wverts = w; i.tris = None
                i.lo = tuple(min(v[a] for v in w) for a in range(3)); i.hi = tuple(max(v[a] for v in w) for a in range(3))
                C.insts.append(i)
        C.grid = {}
        for k, i in enumerate(C.insts):
            for cx in range(int(i.lo[0] // C.CELL), int(i.hi[0] // C.CELL) + 1):
                for cz in range(int(i.lo[2] // C.CELL), int(i.hi[2] // C.CELL) + 1):
                    C.grid.setdefault((cx, cz), []).append(k)
        _COLL = C
        return C
    except Exception as e:      # kl-merge missing / unreadable HVK: no floor check, said in the report
        rep['covers: WARNING ANP_COVERS_FLOOR: .HVK ray caster unavailable (%s), floor check skipped' % str(e)[:80]] += 1
        return None


def floor_ok(C, c):
    """Dog Days' cover-point floor probe (kl2 0x71fc30 -> 0x4a2710, read statically): beside each bottom edge, 100 cm
    out, a downward ray over [bottom - h/2, bottom + h/2] with h = half height + 50 (0x603830) must hit solid (mask
    0x20 here; the game's probe uses 0x23); modelled at each edge's middle -> True when at least one side has floor"""
    ex, ey, ez = _cols(c['M']); h = c['half']; P = c['P']
    bot = P[1] - h[1]; hh = (h[1] + 50.0) / 2
    for ax, hw in ((ex, h[0]), (ez, h[2])):
        for s in (1, -1):
            o = (P[0] + s * ax[0] * (hw + 100.0), bot + hh, P[2] + s * ax[2] * (hw + 100.0))
            if C.ray(o, (0.0, -2 * hh, 0.0), 0x20): return True
    return False


def _filter(cands, existing, rep):
    """ANP_COVERS_DUP / _TILTED / _FLOOR on the planned boxes (entity order kept): upright boxes first, then the tilted
    rebuilds, so a tilted box gives way to the upright box Dead Men placed beside it (M02: every tipped
    StonewoolBags CoverBoxH_01 has a CoverBoxM next to it)"""
    dm, tm, fm = dup_mode(), tilted_mode(), floor_mode()
    if dm == 'keep' and tm == 'keep' and fm == 'keep': return cands
    C = _collision(rep) if fm == 'skip' else None
    kept = []
    for c in [c for c in cands if c['kind'] != 'tilted'] + [c for c in cands if c['kind'] == 'tilted']:
        nm = c['name'][-45:]
        if c['kind'] == 'tilted' and tm == 'drop':
            rep['covers: skipped tilted box (ANP_COVERS_TILTED=drop)'] += 1; continue
        if dm == 'skip' or (c['kind'] == 'tilted' and tm == 'auto'):
            best = max(((_overlap(c, o), o['name']) for o in existing + kept if abs(o['P'][1] - c['P'][1]) < DUP_DY),
                       default=(0.0, ''))
            if best[0] >= (TILT_SHARE if c['kind'] == 'tilted' else DUP_SHARE):
                rep['covers: skipped duplicate (ANP_COVERS_DUP), %s box' % c['kind']] += 1
                rep['covers: duplicate %s = %.0f%% in %s' % (nm, 100 * best[0], best[1][-40:])] += 1
                continue
        if C is not None and not floor_ok(C, c):
            rep['covers: skipped, no floor beside it (ANP_COVERS_FLOOR)'] += 1
            rep['covers: no floor %s at (%.0f, %.0f, %.0f)' % (nm, c['P'][0], c['P'][1], c['P'][2])] += 1
            continue
        kept.append(c)
    ids = set(id(c) for c in kept)
    return [c for c in cands if id(c) in ids]


def dd_list_count(names, g, roff, par, typ):
    """existing entities Dog Days' list takes (estimate: ZSTDOBJ or ZBoxPrimitive *coverbox*, not *nocoverbox* for
    ZBoxPrimitive, no 0x400 on it or above, upright; matches the runtime covers= count of rel5 M02 169, M08 598,
    M13B 950, M14 712)"""
    n = 0
    for i, nm in enumerate(names):
        if not _m(nm, '*coverbox*'): continue
        if typ[i] == ZBOXPRIM:
            if _m(nm, '*nocoverbox*'): continue
        elif typ[i] != ZSTDOBJ: continue
        q = i; bad = False
        while q != -1:
            if _flag(g, roff, q) & 0x400: bad = True; break
            q = par[q]
        if not bad and world(g, roff, par, i)[0][4] >= UP_MIN: n += 1
    return n


def template(out, spans, names, g, roff, typ):
    """a ZSTDOBJ cover box of this level shaped like a stock Dog Days one (module doc):
    -> (entity, gms record bytes, props op list (inside Begin/End), prim index) or None"""
    best = None
    for i, nm in enumerate(names):
        if typ[i] != ZSTDOBJ or not dm_class(nm): continue
        fl = _flag(g, roff, i)
        if fl not in TEMPLATE_FLAGS: continue
        prim = struct.unpack_from('<I', g, roff[i] + 0x0c)[0]
        if not _cover_mesh_ok(prim): continue
        s0, pe = _props(out, spans, i)
        ops = list(out[s0 + 1:pe - 1])
        a9, a3, mi = _arrays(ops)
        if None in (a9, a3, mi) or ops[mi][2] != prim: continue
        rank = TEMPLATE_FLAGS.index(fl)
        if best is None or rank < best[0]:
            best = (rank, (i, bytes(g[roff[i]:roff[i] + 64]), ops, prim))
            if rank == 0: break
    return best[1] if best else None


def prim_chunk(idx, half):
    c = bytearray(_prm_chunk(idx))
    assert len(c) == 64 and struct.unpack_from('<I', c)[0] == 0x70100, (idx, len(c))
    struct.pack_into('<6f', c, 32, -half[0], -half[1], -half[2], half[0], half[1], half[2])
    return bytes(c)


LAST = None     # the last plan (port_level / tests read it: new box name -> source, class, world transform)


def graft_hook(out, spans, names, g, roff, par, typ, rep, new_chunk, tail_world, prm_next):
    global LAST
    LAST = None
    if not enabled(): return None
    if PRM_SRC is None:
        rep['covers: no PRM_SRC, skipped'] += 1; return None
    P_ = plan(out, spans, names, g, roff, par, typ, rep)
    if not P_:
        rep['covers: no lost Dead Men cover boxes'] += 1; return None
    T = template(out, spans, names, g, roff, typ)
    if T is None:
        rep['covers: no stock-like ZSTDOBJ cover box to copy, %d boxes NOT added' % len(P_)] += 1; return None
    # one prim per box SIZE (half extents rounded to SIZE_ROUND cm): each new size gets its own mesh (copy of the
    # template's, same geometry descriptor list), mesh list (16 B -> that mesh) and prim (mesh list, bbox), the 1:1:1
    # prim : mesh list : mesh pairing of every stock Dog Days and Dead Men prim; boxes of one size share that prim
    for c in P_: c['half'] = tuple(round(h, SIZE_ROUND) for h in c['half'])
    sizes = []
    for c in P_:
        if c['half'] not in sizes: sizes.append(c['half'])
    room = (PRM_MAX - prm_next) // 3
    if len(sizes) > room:
        keep = set(sizes[:max(room, 0)]); n0 = len(P_)
        P_ = [c for c in P_ if c['half'] in keep]; sizes = sizes[:max(room, 0)]
        rep['covers: PRM table full, %d of %d boxes NOT added' % (n0 - len(P_), n0)] += 1
        if not P_: return None
    have = dd_list_count(names, g, roff, par, typ)
    if have + len(P_) > COVER_CAP:
        rep['covers: WARNING cover list %d + %d > cap %d (kl2 keeps the first %d)' % (have, len(P_), COVER_CAP, COVER_CAP)] += 1
    ti, trec, tops, tprim = T
    a9, a3, mi = _arrays(tops)
    # chunk refcounts (.prm table word 2) = the users summed down the chain in every stock file: prim = its entities,
    # mesh list and mesh = their prim's, geometry descriptor list / descriptors / vertex and index buffers = the sum
    # over their meshes -> refs = {chunk index: refcount to ADD} (new chunks are appended with refcount 1)
    tw = struct.unpack_from('<16I', _prm_chunk(tprim))
    tmesh = struct.unpack_from('<I', _prm_chunk(tw[6]))[0]
    mesh_b = _prm_chunk(tmesh); mw = struct.unpack_from('<16I', mesh_b)
    shared = [mw[10]]
    # prim word 4: a 16-byte zero chunk shared by every prim; its refcount = the sum of its prims' refcounts in stock
    # files (L01 3028 = 3028, DM M02 3242 = 3242) -> the new prims count too (review 13 Oct)
    if tw[4] and _prm_chunk(tw[4]) is not None: shared.append(tw[4])
    for gd in struct.unpack_from('<4I', _prm_chunk(mw[10]))[:mw[11]]:
        gw = _prm_chunk(gd)
        if gw is None: continue
        shared.append(gd)
        vb, ib = struct.unpack_from('<I', gw, 4)[0], struct.unpack_from('<I', gw, 24 if len(gw) == 48 else 12)[0]
        shared += [b for b in (vb, ib) if _prm_chunk(b) is not None]
    use = {}
    for c in P_: use[c['half']] = use.get(c['half'], 0) + 1
    refs = {}
    for q in shared: refs[q] = refs.get(q, 0) + len(P_)
    pk = {}; first_k = None
    for hf in sizes:
        km = new_chunk(mesh_b)
        kl = new_chunk(struct.pack('<4I', km, 0, 0, 0))
        pc = bytearray(prim_chunk(tprim, hf)); struct.pack_into('<I', pc, 24, kl)
        kp = new_chunk(bytes(pc)); pk[hf] = kp
        if first_k is None: first_k = km
        for q in (km, kl, kp): refs[q] = use[hf] - 1
    Ti = _inv(*tail_world)                           # the boxes sit under ANP_Tail\ANP_Covers (identity)
    recs = []; ops = []; n = {'H': 0, 'M': 0}; plan_out = []
    for c in P_:
        M = _mul(Ti[0], c['M']); r = _rot(Ti[0], c['P']); P = (r[0] + Ti[1][0], r[1] + Ti[1][1], r[2] + Ti[1][2])
        k = pk[c['half']]
        while len(g) % 16: g.append(0)
        m_off = len(g); g.extend(struct.pack('<9f', *M) + b'\0' * 12)
        p_off = len(g); g.extend(struct.pack('<3f', *P) + b'\0' * 4)
        rec = bytearray(trec); struct.pack_into('<I', rec, 0x0c, k)
        struct.pack_into('<I', rec, 0x1c, struct.unpack_from('<I', rec, 0x1c)[0] & ~0x400)
        nm = 'ANP_CoverBox%s_%d' % (c['cls'], n[c['cls']]); n[c['cls']] += 1
        recs.append((bytes(rec), nm, (m_off, p_off)))
        po = [list(o) for o in tops]
        for q in range(9): po[a9 + 1 + q][2] = M[q]
        for q in range(3): po[a3 + 1 + q][2] = P[q]
        if po[a3 + 4][1] & 0x7f == 0x7c and po[a3 + 5][1] & 0x7f == 6: po[a3 + 5][2] = 0   # ZGEOM[3] (hidden) off
        po[mi][2] = k
        ops += [(0, 2, None)] + [tuple(o) for o in po] + [(0, 0x7e, None), (0, 4, 0), (0, 4, 0)]
        plan_out.append(dict(c, new=nm, prim=k))
    kinds = {}
    for c in P_: kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
    rep['covers: ANP_Covers %d high + %d low (%s), template %s (flags %#x, prim %d), %d sizes = %d prim/mesh list/mesh '
        'chunks %d..%d, cover list %d -> %d' % (n['H'], n['M'], ', '.join('%s %d' % kv for kv in sorted(kinds.items())),
                                               names[ti][-40:], _flag(g, roff, ti), tprim, len(sizes), 3 * len(sizes),
                                               first_k, first_k + 3 * len(sizes) - 1, have, have + len(P_))] += 1
    rep['covers: refcounts +%d on the shared geometry chunks %s' % (len(P_), shared)] += 1
    for c in plan_out[:3]:
        rep['covers: e.g. %s <- %s at (%.1f, %.1f, %.1f) half (%.1f, %.1f, %.1f)' % (
            c['new'], c['name'][-45:], c['P'][0], c['P'][1], c['P'][2], c['half'][0], c['half'][1], c['half'][2])] += 1
    LAST = plan_out
    return recs, ops, refs
