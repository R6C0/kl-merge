#!/usr/bin/env python3
r"""kl_skyline_1108.py - DM05A (Last Call, F01 slot): Dead Men M05_A's BUILDINGS_MIDRANGE put back as a distant skyline (2026-11-08, STAGE ONLY, never installs).

WHY: the owner (11-07): the maps feel empty outside, show more city. Dead Men's M05_A holds one entity ROOT\CutScenes/M05/M05_Call_Retomoto.zip\Rooftops_END\Buildings_MidRange
(node 9286, ZLNKOBJ 0x200002, flags 0x20182, group 0): ONE model, 6 meshes / 156 triangles / 5 materials (NeonSigns, Facade, Buildings_02a/b) / 6 textures, a ring of towers
(local box x -44336..-304, y -4524..20345, z -29644..48749). The graft dropped it with the cutscene layer. This step appends its model closure (.prm / .MAT / .TEX) to the finished live
DM05A build and places ONE static copy far from the pad, in the form kl_fa_ropevis proved drawn (pool group 2, flags 0x264182, in no room tree, ZGEOM[4] = the new model root, light
list borrowed from the nearest ZSTDOBJ that has one) under one new top group KL_Skyline! (listed in root tree 3 like KL_RopeVis! / KL_Traffic!). Its .oct record (+0x1c) is ZEROED:
NO COLLISION, it is scenery.

WHERE (the search is `search`, the numbers `plan`; all cm, world = R . local + T):
  rotation 0 (identity), T = (60000, 1884, -4000): the ring lands on x 15664 .. 59696, z -33644 .. 44749, y -2640 .. 22229, i.e. EAST of the pad (8100, 4600) behind the
  approaching heli as the outro eye (7400, 2500, 2800) sees it (the 2h heli comes from the east along kl_arrival_1107.ROUTE_2H). Conditions the search enforces: every sample at least
  MAP_CLEAR (3000) from any existing render triangle (glow / Distance / skydome meshes excluded), at least ROUTE_CLEAR (9800 = 98 m) from the densified 2h route, no skyline triangle
  between the outro eye and any route sample (the heli stays visible), and every vertex inside Backdrop .rmi box 59 (x/z +-175000).
  GUESS: y offset 1884 (the entity's own height in the cutscene; kept, nothing measured about the real ground there).
  GUESS: rotation 0 and the east side are a taste choice (nearest clear candidate, east biased); the bench shots decide.
  GUESS: box 59 ALONE draws it. A moving entity is drawn only while an .rmi box of a visible room holds it (c9, kl_club_rmi_1106); the Backdrop room has no trees and only box 59.
  c9 saw the heli vanish above the Roof boxes, so a skyline held only by box 59 may not show: the shots decide (then a Roof box would have to be widened, a bigger step).

  python tools/kl_skyline_1108.py plan  [--deg 0 --tx 60000 --tz -4000]      (offline numbers: clearance, line of sight, box 59)
  python tools/kl_skyline_1108.py search                                       (candidate list, nearest first)
  python tools/kl_skyline_1108.py stage [--in-dir <map dir>] [--out <dir>]    (default in-dir: the live DM05A, only READ; out C:\kl_build_1024\skyline_1108)
  python tools/kl_skyline_1108.py check <out> [--in-dir <map dir>]
  python tools/kl_skyline_1108.py plot  <png> [--out <staged dir>]            (top-down picture)

Refuses unless the live plain zip / bots zip / base.md5 are exactly the pinned md5s (the base this was written against). BOTH zips (plain + .bots.zip: same members, only .prp
differs) get the step; F01_Main.bots.base.md5 = md5 of the staged PLAIN zip; KLGuns.ini Entries= follows the new .prm chunk count (only that line changes); KLJoin.ini unchanged.
install.py: chain-installer style, tag .before-skyline1108, all or nothing, --undo, --dry.
"""
import hashlib, json, math, os, shutil, struct, sys, zipfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T, kl_gms
import kl_prpjoin as J
import kl_lastcall_chain_1106 as CH

MAPDIR = CH.MAPDIR
OUT = r'C:\kl_build_1024\skyline_1108'
TAG = '.before-skyline1108'
SLOT = 'F01'
Z, BZ = 'F01_Main.zip', 'F01_Main.bots.zip'
LIVE_ZIP_MD5 = '651a749259f54211c20eb67eff90ee65'        # the live DM05A plain zip this was staged on (11-08, 2h arrival + club music)
LIVE_BOTS_MD5 = 'ba98c0a6e723a45b4cc58345ee2433b4'
LIVE_BASE_MD5 = '1d89ea850b3baac1cabe3c50bc2eecfe'
FILES = (Z, BZ, 'F01_Main.bots.base.md5', 'KLGuns.ini')
GROUP = 'KL_Skyline!'
NAME = 'KL_Skyline_MidRange'
LEVEL = 'M05_A'
STOCK = 'M05_A_conv'
SRC_PATH = 'ROOT\\CutScenes/M05/M05_Call_Retomoto.zip\\Rooftops_END\\Buildings_MidRange'
VIS_FLAGS = 0x264182
BOX_ROOM = 59                                  # Backdrop .rmi box (room slot id 2 = kl_scene slot 0 + 2)
DEG, TX, TY, TZ = 0, 60000.0, 1884.0, -4000.0  # see WHERE above
PAD = (8100.0, 1400.0, 4600.0)
EYE = (7400.0, 2500.0, 2800.0)
MAP_CLEAR, ROUTE_CLEAR = 3000.0, 9800.0
LOCAL = r'C:\kl_build_1024\skyline_local_tris.npy'
WIDE = r'C:\kl_build_1024\skyline_wide_render_1108.npz'
md5 = lambda b: hashlib.md5(b).hexdigest()


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ geometry (numpy only)
def rot(P, deg):
    """world = rot(local): turn about Y by deg (multiples of 90); the matching ZGEOM[1] is F.rot9(sin, cos)."""
    c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg)))
    return np.stack([c * P[:, 0] + s * P[:, 2], P[:, 1], -s * P[:, 0] + c * P[:, 2]], 1)


def local_tris(M):
    """The (n,3,3) local triangles of Buildings_MidRange (every mesh of the model closure), cached at LOCAL."""
    src = M.ents[M.prp.resolve(SRC_PATH)[0] - 1]
    p7 = G.read(M['.prm'], 'dd')
    kinds, _a = G.walk(p7, [src.model])
    out = []
    for m, kd in sorted(kinds.items()):
        if kd != 'mesh':
            continue
        d = p7.u32(p7.u32(m, 0x28), 0)
        nv, v = p7.u32(d, 0), p7.chunks[p7.u32(d, 4)]
        pos = np.array([struct.unpack_from('<3f', v, 40 * k) for k in range(nv)], float)    # stride 40, position first (static, no skinning: measured)
        ix = p7.chunks[p7.u32(d, 0x18)]
        n = struct.unpack_from('<H', ix, 2)[0]
        ii = struct.unpack_from('<%dH' % n, ix, 4)
        out.append(pos[np.array([(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)])])
    return np.concatenate(out), src


def sample(tris, step):
    """Points on the triangles, at most `step` apart."""
    out = []
    for t in tris:
        e = max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[1]), np.linalg.norm(t[0] - t[2]))
        n = max(1, min(60, int(math.ceil(e / step))))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                out.append(t[0] * (1 - u - v) + t[1] * u + t[2] * v)
    return np.array(out)


def route_path():
    import kl_arrival_1107 as A
    R = np.array(A.ROUTE_2H, float)
    pts = []
    for a, b in zip(R, R[1:]):
        k = max(1, int(np.linalg.norm(b - a) / 100))
        pts += [a + (b - a) * i / k for i in range(k)]
    pts.append(R[-1])
    return np.array(pts)


def route_dist(P, path):
    best = 1e18
    for k in range(0, len(path), 20):
        q = path[k:k + 20]
        for i in range(0, len(P), 4000):
            best = min(best, float(((P[i:i + 4000, None, :] - q[None, :, :]) ** 2).sum(2).min()))
    return math.sqrt(best)


def seg_hits(p0, ends, tris):
    """Moeller-Trumbore: how many of the segments p0 -> ends[i] cross a triangle of `tris`."""
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    s = p0 - tris[:, 0]
    q = np.cross(s, e1)
    n = 0
    for d in ends - p0:
        h = np.cross(d, e2)
        a = (e1 * h).sum(1)
        ok = np.abs(a) > 1e-9
        f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
        u, v, t = f * (s * h).sum(1), f * (q * d).sum(1), f * (e2 * q).sum(1)
        n += bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)).any())
    return n


class Occupancy:
    """Voxel (1000 cm) occupancy of the live map's render geometry: vertices, centroids and edge midpoints of every triangle, without glow / Distance / skydome."""
    CS = 1000.0

    def __init__(self, tris, owner, names):
        bad = np.array(['glow' in n.lower() or 'distance' in n.lower() or 'skydome' in n.lower() for n in names])
        t = tris.astype(float)[~bad[owner]]
        pts = [t.reshape(-1, 3), t.mean(1)] + [(t[:, i] + t[:, j]) / 2 for i, j in ((0, 1), (1, 2), (0, 2))]
        pts = np.concatenate(pts)
        self.mn = np.floor(pts.min(0) / self.CS).astype(int) - 40
        mx = np.ceil(pts.max(0) / self.CS).astype(int) + 40
        g = np.zeros(mx - self.mn + 1, np.int32)
        k = np.floor(pts / self.CS).astype(int) - self.mn
        g[k[:, 0], k[:, 1], k[:, 2]] = 1
        self.shape = np.array(g.shape)
        self.c = np.pad(g.cumsum(0).cumsum(1).cumsum(2), ((1, 0), (1, 0), (1, 0)))

    def hits(self, P, margin):
        """How many of the points P have existing geometry within a +-margin cube."""
        a = np.clip(np.floor((P - margin) / self.CS).astype(int) - self.mn, 0, self.shape)
        b = np.clip(np.floor((P + margin) / self.CS).astype(int) - self.mn + 1, 0, self.shape)
        c = self.c
        s = (c[b[:, 0], b[:, 1], b[:, 2]] - c[a[:, 0], b[:, 1], b[:, 2]] - c[b[:, 0], a[:, 1], b[:, 2]] - c[b[:, 0], b[:, 1], a[:, 2]]
             + c[a[:, 0], a[:, 1], b[:, 2]] + c[a[:, 0], b[:, 1], a[:, 2]] + c[b[:, 0], a[:, 1], a[:, 2]] - c[a[:, 0], a[:, 1], a[:, 2]])
        return int((s > 0).sum())


def wide_render(zp, log=print):
    """Render triangles of the map and its far backdrop (x/z +-120000), cached at WIDE together with the zip md5."""
    import kl_arrival_1107 as A
    want = fmd5(zp)
    if os.path.isfile(WIDE):
        d = np.load(WIDE)
        if 'zip_md5' in d.files and str(d['zip_md5']) == want:
            return d['tris'], d['owner'], [str(n) for n in d['names']]
    tris, owner, names = A.geom(zp, region=(np.array([-120000, -30000, -120000]), np.array([120000, 60000, 120000])), log=log)
    np.savez_compressed(WIDE, tris=tris, owner=owner, names=np.array(names), zip_md5=np.array(want))
    return tris, owner, names


def rmi_box(rmi, i):
    f = struct.unpack_from('<19f', rmi.boxes[i].raw, 0)
    return np.array(f[10:13]), np.array(f[16:19])


def world_tris(L, deg=DEG, t=(TX, TY, TZ)):
    return (rot(L.reshape(-1, 3), deg) + np.array(t)).reshape(-1, 3, 3)


def plan(deg=DEG, t=(TX, TY, TZ), zp=os.path.join(MAPDIR, Z), log=print, L=None, occ=None):
    """The offline numbers of one placement -> dict (all cm)."""
    import kl_graft
    if L is None:
        L = np.load(LOCAL) if os.path.isfile(LOCAL) else local_tris(kl_graft.DeadMen(LEVEL, log=lambda *a: None))[0]
    W = world_tris(L, deg, t)
    S = sample(W, 400.0)
    path = route_path()
    occ = occ or Occupancy(*wide_render(zp, log))
    lo, hi = W.reshape(-1, 3).min(0), W.reshape(-1, 3).max(0)
    clear = 0
    for m in (1000, 2000, 3000, 5000, 8000, 12000, 20000):          # the largest margin with no existing geometry inside
        if occ.hits(S, float(m)):
            break
        clear = m
    res = dict(deg=deg, T=list(t), box_lo=lo.round().tolist(), box_hi=hi.round().tolist(), samples=len(S),
               map_clear_ge=clear, route_clear=round(route_dist(S, path)),
               eye_los_hits=seg_hits(np.array(EYE), path[::5], W), eye_inside=bool((EYE >= lo).all() and (EYE <= hi).all()),
               centre=W.reshape(-1, 3).mean(0).round().tolist())
    c = res['centre']
    res['bearing_from_eye_deg'] = round(math.degrees(math.atan2(c[2] - EYE[2], c[0] - EYE[0])))
    res['dist_from_pad'] = round(math.hypot(c[0] - PAD[0], c[2] - PAD[2]))
    return res


def search(zp=os.path.join(MAPDIR, Z), log=print, top=12):
    """Candidate list: rotations 0/90/180/270 over a 2000 cm (T x, T z) grid, y fixed; nearest clear candidate first. Conditions: see the module doc."""
    import kl_graft
    L = np.load(LOCAL) if os.path.isfile(LOCAL) else local_tris(kl_graft.DeadMen(LEVEL, log=lambda *a: None))[0]
    occ = Occupancy(*wide_render(zp, log))
    S = sample(L, 1500.0)
    path = route_path()
    cand = []
    lim = 175000.0 - 2000.0
    for deg in (0, 90, 180, 270):
        R = rot(S, deg)
        for tx in range(-120000, 120001, 2000):
            for tz in range(-120000, 120001, 2000):
                P = R + np.array([tx, TY, tz])
                if np.abs(P[:, 0]).max() > lim or np.abs(P[:, 2]).max() > lim or abs(tx) > lim or abs(tz) > lim:
                    continue
                if occ.hits(P, MAP_CLEAR):
                    continue
                c = P.mean(0)
                cand.append((math.hypot(c[0] - PAD[0], c[2] - PAD[2]), deg, tx, tz))
    cand.sort()
    out = []
    for dist, deg, tx, tz in cand:
        r = plan(deg, (tx, TY, tz), zp, log, L, occ)
        if r['route_clear'] >= ROUTE_CLEAR and not r['eye_los_hits'] and not r['eye_inside']:
            out.append(r)
            log('%s' % r)
            if len(out) >= top:
                break
    return out


# ------------------------------------------------------------------ staging
TEX_LEVEL = None


def tex_level(zp):
    """The deflate level the live zip's .TEX was packed at: the one whose recompression matches the member's compressed size (MEASURED, not assumed)."""
    import zlib
    with zipfile.ZipFile(zp) as z:
        i = next(i for i in z.infolist() if i.filename.endswith('.TEX'))
        raw = z.read(i.filename)
    for lvl in (6, 1, 9):
        c = zlib.compressobj(lvl, zlib.DEFLATED, -15)
        n = len(c.compress(raw)) + len(c.flush())
        if abs(n - i.compress_size) <= i.compress_size * 0.001:
            return lvl
    return 6


def write_zip(path, members, texlvl):
    """kl_graft.write_zip (same stamp, attrs, order) with the live level per member: .TEX at the measured level, the rest as load_options() says."""
    import kl_graft
    opt = kl_graft.load_options()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=opt['level']) as z:
        for name, data in members:
            zi = zipfile.ZipInfo(name, kl_graft.STAMP)
            zi.external_attr = 0o600 << 16
            z.writestr(zi, data, zipfile.ZIP_DEFLATED, texlvl if name.endswith('.TEX') else opt['level'])
    return path


def stage_zip(zp, out_zp, M, log, texlvl):
    """One zip: the skyline added -> report dict."""
    import kl_fa_bots as F, kl_fa_cover as CV, kl_fa_climb2 as C2, kl_light
    import kl_octree as O
    B = F.Built(zp, SLOT)
    sc = B.sc
    if sc.resolve(F.R_ + GROUP):
        raise ValueError('the build already has %s' % GROUP)
    say = log
    mk = F.Maker()
    nd = mk.clone(STOCK, SRC_PATH)
    sc7, ents7 = F.Maker.level(STOCK)
    root = ents7[sc7.resolve(SRC_PATH)[0] - 1].model
    p7 = G.read(M['.prm'], 'dd')
    mat7, tex7 = T.read_mat(M['.MAT']), T.read_tex(M['.TEX'])
    pos = (TX, TY, TZ)
    c, s = round(math.cos(math.radians(DEG))), round(math.sin(math.radians(DEG)))
    rot9 = F.rot9(s, c)                                    # local +Z -> (sin, cos): identity for 0 deg (matches rot() above)
    # ---- .prm / .MAT / .TEX
    pD, matD, texD = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    kinds, args = G.walk(p7, [root])
    slots = {p7.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(mat7, slots))
    tex, tmap = T.merge_tex(texD, tex7, want)
    mat, mmap = T.merge_mat(matD, mat7, slots, tmap)
    prm, cmap = G.append(pD, p7, [root], mmap, None, tmap)
    zeroed = 0
    for old in kinds:                                     # NO COLLISION: every model root's .oct record reference (+0x1c) -> 0
        cc = prm.chunks[cmap[old]]
        if len(cc) == 64 and cc[:4] == b'\0\1\7\0' and struct.unpack_from('<I', cc, 0x1c)[0]:
            cc = bytearray(cc); struct.pack_into('<I', cc, 0x1c, 0); prm.chunks[cmap[old]] = bytes(cc); zeroed += 1
    say('  .prm: %d chunks appended (root %d -> %d), %d .oct record refs zeroed; materials %d, textures %d' % (len(kinds), root, cmap[root], zeroed, len(slots), len(want)))
    # SHADER FIT: a material without a compiled shader is NOT drawn (kl_fa_loot.dress); static meshes, so no twin_on / glow twin is needed
    new_slots = sorted(mmap[x] for x in slots)
    fit = kl_light.fit_shaders(mat, B['.fxc'], slots=new_slots, log=say)
    if fit['unresolved']:
        raise ValueError('no compiled shader for %s' % [v[0] for v in fit['unresolved'].values()])
    lack = kl_light.missing_shaders(mat, B['.fxc'], new_slots)
    if lack:
        raise ValueError('shaders still missing after fit_shaders: %s' % lack)
    say('  shaders: every one of the %d skyline materials resolves to a compiled shader (fixed: %s)' % (len(new_slots), {k: v for k, v in fit['fixed'].items()} or 'none'))
    # ---- nodes
    gk = CV.group_form(B)
    topg = CV._node(mk, B, gk, GROUP)
    mk.place(topg, (0.0, 0.0, 0.0))
    nd.name = NAME if isinstance(nd.name, str) else NAME.encode()
    topg.add(nd)
    mk.place(nd, pos, rot9)
    nd.model, nd.flags, nd.group = cmap[root], VIS_FLAGS, 2
    mk.set(nd, None, {'ZGEOM[4]': cmap[root]})
    best = None
    for e in B.ents:                                      # GUESS (as the rope / traffic): the light list of the nearest ZSTDOBJ that has one
        if e.tid == 0x200002 and e.links:
            P = B.fr[e][1]
            dd = sum((P[i] - pos[i]) ** 2 for i in range(3))
            if best is None or dd < best[0]:
                best = (dd, e)
    nd.links = list(best[1].links) if best else []
    say('  %s at (%.0f, %.0f, %.0f) rot %d; light list of %s (%d, %.0f away)' % (NAME, pos[0], pos[1], pos[2], DEG, best[1].name.decode('latin1')[-30:] if best else '-',
                                                                              len(nd.links), math.sqrt(best[0]) if best else 0))
    q, order = mk.scene([topg])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'skyline1108')
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    misfit = J.misfits(Jn) if hasattr(J, 'misfits') else []
    if misfit:
        raise ValueError('schema misfits: %s' % (misfit[:3],))
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    A = B.scene
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    nxt = C2._write_ent(A, topg, None, nxt, made)
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
    L = np.load(LOCAL) if os.path.isfile(LOCAL) else local_tris(M)[0]
    Wt = world_tris(L).reshape(-1, 3)
    lo = tuple(float(v) - 600.0 for v in Wt.min(0)); hi = tuple(float(v) + 600.0 for v in Wt.max(0))
    root3 = octn.rooms[0][3]
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree([(slot1[made[id(topg)]] + 2, lo, hi)], root3.origin, root3.scale))
        octn.rooms[0][3].check()
    move = {x: y for x, y in zip(octx.record_refs(), octn.record_refs()) if x != y}
    pm = bytearray(G.write(prm))
    repointed = 0
    if move:
        t, n = struct.unpack_from('<II', pm, 0)
        for i in range(1, n):
            o, size = struct.unpack_from('<II', pm, t + 16 * i)
            if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    prm_bytes = bytes(pm)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    lost = T.used_textures(T.read_mat(new[B.ext['.MAT']])) - set(T.read_tex(new[B.ext['.TEX']]).tex)
    if lost:
        raise ValueError('materials name textures the .TEX lacks: %s' % sorted(lost)[:5])
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    write_zip(out_zp, [(nm, new[nm]) for nm in B.order], texlvl)
    say('written %s: %d entities added, members changed: %s; %d .prm roots re-pointed; chunks %d -> %d' % (out_zp, len(order), ' '.join(changed), repointed, len(pD.chunks), len(p2.chunks)))
    return dict(changed=changed, chunks=len(p2.chunks), root=cmap[root], pos=list(pos), deg=DEG, order=B.order,
                shaders_fixed={str(k): [v[0], [str(x) for x in v[1]]] for k, v in fit['fixed'].items()})


def stage(in_dir=MAPDIR, out=OUT, log=print):
    import kl_graft, kl_fa_bots as F
    zp, bp = os.path.join(in_dir, Z), os.path.join(in_dir, BZ)
    live = {n: fmd5(os.path.join(in_dir, n)) for n in FILES}
    if live[Z] != LIVE_ZIP_MD5:
        raise ValueError('REFUSED: the live DM05A plain zip is %s, not the pinned %s: re-pin after checking what changed it' % (live[Z], LIVE_ZIP_MD5))
    if live[BZ] != LIVE_BOTS_MD5:
        raise ValueError('REFUSED: the live DM05A bots zip is %s, not the pinned %s' % (live[BZ], LIVE_BOTS_MD5))
    if live['F01_Main.bots.base.md5'] != LIVE_BASE_MD5:
        raise ValueError('REFUSED: the live F01_Main.bots.base.md5 is %s, not the pinned %s' % (live['F01_Main.bots.base.md5'], LIVE_BASE_MD5))
    free = shutil.disk_usage(os.path.dirname(out) or '.').free
    if free < 4 << 30:
        raise ValueError('REFUSED: %d MB free on the build drive, want 4096' % (free >> 20))
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    M = kl_graft.DeadMen(LEVEL, log=lambda *a: None)
    if not os.path.isfile(LOCAL):
        np.save(LOCAL, local_tris(M)[0])
    F.Maker._stock[STOCK] = (M.prp, M.ents)
    texlvl = tex_level(zp)
    log('.TEX deflate level of the live zip (measured): %d' % texlvl)
    reps = {}
    for name, src in ((Z, zp), (BZ, bp)):
        log('== %s' % name)
        reps[name] = stage_zip(src, os.path.join(out, name), M, log, texlvl)
    if reps[Z]['order'] != reps[BZ]['order']:
        raise ValueError('member order differs between the zips')
    plain = fmd5(os.path.join(out, Z))
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    n = reps[Z]['chunks']
    if reps[BZ]['chunks'] != n:
        raise ValueError('.prm chunk count differs between the zips')
    import kl_club_doors_1106 as D
    ini, c = D.patch_entries(os.path.join(in_dir, 'KLGuns.ini'), n)
    if c != 1:
        raise ValueError('KLGuns.ini: %d Entries= lines' % c)
    open(os.path.join(out, 'KLGuns.ini'), 'wb').write(ini)
    files = {nm: (live[nm], fmd5(os.path.join(out, nm))) for nm in FILES}
    write_install(out, files)
    json.dump(dict(in_dir=in_dir, files=files, plan=plan(zp=zp, log=log), reports={k: {a: b for a, b in v.items() if a != 'order'} for k, v in reps.items()}),
              open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    bad = check(out, in_dir, log)
    for nm, (o, w) in files.items():
        log('  %-26s live %s -> %s%s' % (nm, o[:8], w[:8], '' if o != w else '  (unchanged, not installed)'))
    log('CHECK: %s' % ('PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


def check(out, in_dir=MAPDIR, log=print):
    import kl_fa_bots as F, kl_octree as O, kl_light, kl_fa_loot as L
    bad = []
    pl = None
    for name in (Z, BZ):
        a, b = zipfile.ZipFile(os.path.join(in_dir, name)), zipfile.ZipFile(os.path.join(out, name))
        if [i.filename for i in a.infolist()] != [i.filename for i in b.infolist()]:
            bad.append('%s: member list/order differs' % name)
            continue
        ch = sorted(i.filename.rsplit('_Main', 1)[1] for i in a.infolist()
                    if (b.getinfo(i.filename).CRC, b.getinfo(i.filename).file_size) != (i.CRC, i.file_size))
        want = ['.MAT', '.TEX', '.buf', '.gms', '.oct', '.prm', '.prp', '.rmc', '.rmi']
        if ch != sorted(want):
            bad.append('%s: members changed %s, expected %s' % (name, ch, sorted(want)))
        zo = os.path.join(out, name)
        B = F.Built(zo, SLOT)
        if len(B.sc.resolve(F.R_ + GROUP)) != 1:
            bad.append('%s: not exactly one %s node' % (name, GROUP)); continue
        p = G.read(B['.prm'], 'dd')
        mat, tex = T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
        es = [e for e in B.ents if e.name.decode('latin1') == NAME]
        if len(es) != 1:
            bad.append('%s: %d %s entities' % (name, len(es), NAME)); continue
        e = es[0]
        kinds, _a = G.walk(p, [e.model])
        sl = {p.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
        if not sl or any(s not in mat.insts for s in sl):
            bad.append('%s: material slot unresolved' % name)
        nolack = kl_light.missing_shaders(mat, kl_light.shader_cache(B['.fxc']), sorted(sl))
        if nolack:
            bad.append('%s: materials without a compiled shader: %s' % (name, nolack))
        if T.used_textures(mat, sl) - set(tex.tex):
            bad.append('%s: texture missing' % name)
        c = p.chunks[e.model]
        if len(c) == 64 and struct.unpack_from('<I', c, 0x1c)[0]:
            bad.append('%s: keeps an .oct record ref' % name)
        if e.group != 2 or e.flags != VIS_FLAGS:
            bad.append('%s: form group %s flags %#x' % (name, e.group, e.flags))
        # world triangles as the staged build draws them (kl_fa_loot frames + Assets, the way kl_arrival_1107.geom reads a map) against the plan
        Bl, As = L.Built(zo), L.Assets(zo)
        Rm, Tt = L.frames(Bl.scene)[next(x for x in Bl.ents if x.name.decode('latin1') == NAME)]
        R, Tt = np.array(Rm, float), np.array(Tt, float)
        tris = []
        for o in As.meshes(e.model):
            pos, _uv, ii = As.geometry(o)
            if len(pos):
                tris.append((np.array(pos, float) @ R.T + Tt)[np.array(ii)])
        W = np.concatenate(tris)
        planned = world_tris(np.load(LOCAL))
        if W.shape != planned.shape or np.abs(np.sort(W.reshape(-1, 3), axis=0) - np.sort(planned.reshape(-1, 3), axis=0)).max() > 1.0:
            bad.append('%s: the staged world triangles are not the planned ones (max diff %s)' % (name, np.abs(np.sort(W.reshape(-1, 3), axis=0) - np.sort(planned.reshape(-1, 3), axis=0)).max()
                                                                                              if W.shape == planned.shape else 'shape %s vs %s' % (W.shape, planned.shape)))
        rmi = O.RoomIndex.parse(B['.rmi'])
        ctr, half = rmi_box(rmi, BOX_ROOM)
        lo, hi = W.reshape(-1, 3).min(0), W.reshape(-1, 3).max(0)
        inside = bool((lo >= ctr - half).all() and (hi <= ctr + half).all()) and bool((np.array(B.fr[e][1]) >= ctr - half).all() and (np.array(B.fr[e][1]) <= ctr + half).all())
        log('  %s %s: world box %s .. %s; Backdrop .rmi box %d holds all of it (AABB, rotation ignored): %s' % (name, NAME, lo.round().astype(int).tolist(), hi.round().astype(int).tolist(), BOX_ROOM, inside))
        if not inside:
            bad.append('%s: the skyline is not inside Backdrop .rmi box %d (would not be drawn)' % (name, BOX_ROOM))
        # the box must belong to the Backdrop room (slot id 2) and the room must still have no tree that lists the entity
        if pl is None:
            pl = plan(zp=os.path.join(in_dir, Z), log=log)
            log('  plan: %s' % pl)
            if pl['route_clear'] < ROUTE_CLEAR or pl['eye_los_hits'] or pl['eye_inside'] or pl['map_clear_ge'] < MAP_CLEAR:
                bad.append('plan: clearance conditions not met: %s' % pl)
    if open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip() != fmd5(os.path.join(out, Z)):
        bad.append('base.md5 is not the plain zip md5')
    a = open(os.path.join(in_dir, 'KLGuns.ini'), 'rb').read().decode('latin-1').splitlines()
    b = open(os.path.join(out, 'KLGuns.ini'), 'rb').read().decode('latin-1').splitlines()
    d = [(x, y) for x, y in zip(a, b) if x != y]
    if len(a) != len(b) or len(d) > 1 or any(not x.lower().startswith('entries') for x, y in d):
        bad.append('KLGuns.ini: more than the Entries= line differs')
    return bad


# ------------------------------------------------------------------ install.py (the chain installer, retargeted: header, tag, bat names)
def write_install(st, files):
    txt = CH.INSTALL
    for a, b in (('LAST CALL CHAIN @@PASSES@@ (2026-11-06, tools/kl_lastcall_chain_1106.py) on the live DM05A files',
                  'DM05A SKYLINE 1108 (tools/kl_skyline_1108.py) on the live DM05A files'),
                 ('<name>.before-chain1106', '<name>' + TAG)):
        if a not in txt:
            raise ValueError('install template changed: %r not found' % a)
        txt = txt.replace(a, b)
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = txt.replace('@@FILES@@', fl).replace('@@PIN@@', repr(files[Z][0])).replace('@@TAG@@', repr(TAG))
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL DM05A skyline 1108.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO DM05A skyline 1108.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


# ------------------------------------------------------------------ top-down picture (PIL: matplotlib is not installed)
def plot(png, out=OUT, in_dir=MAPDIR, log=print):
    from PIL import Image, ImageDraw
    zp = os.path.join(in_dir, Z)
    tris, owner, names = wide_render(zp, log)
    L = np.load(LOCAL)
    W = world_tris(L)
    path = route_path()
    x0, x1, z0, z1 = -50000.0, 70000.0, -40000.0, 50000.0
    sc = 0.01                                              # px per cm: 1 px = 1 m
    w, h = int((x1 - x0) * sc), int((z1 - z0) * sc)
    im = Image.new('RGB', (w, h), (18, 20, 26))
    d = ImageDraw.Draw(im)
    px = lambda x, z: ((x - x0) * sc, h - (z - z0) * sc)
    for gx in range(-40000, 70001, 10000):
        d.line([px(gx, z0), px(gx, z1)], fill=(40, 44, 54))
    for gz in range(-40000, 50001, 10000):
        d.line([px(x0, gz), px(x1, gz)], fill=(40, 44, 54))
    t = tris.astype(float)
    keep = ~((t[:, :, 0].max(1) < x0) | (t[:, :, 0].min(1) > x1) | (t[:, :, 2].max(1) < z0) | (t[:, :, 2].min(1) > z1))
    for tr in t[keep][::3]:
        d.polygon([px(v[0], v[2]) for v in tr], fill=(90, 96, 108))
    for tr in W:
        d.polygon([px(v[0], v[2]) for v in tr], fill=(214, 140, 40), outline=(255, 190, 90))
    d.line([px(v[0], v[2]) for v in path], fill=(80, 200, 255), width=2)
    for v, col in ((PAD, (255, 80, 80)), (EYE, (120, 255, 120))):
        x, y = px(v[0], v[2])
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col)
    d.text((8, 8), 'DM05A skyline 1108, top-down, 1 px = 1 m (x right, z up). grey = live map + backdrop, orange = new Buildings_MidRange,', fill=(230, 230, 230))
    d.text((8, 22), 'blue = 2h heli route, red = pad (8100,4600), green = outro eye (7400,2500,2800). T=(%d, %d, %d) rot %d' % (TX, TY, TZ, DEG), fill=(230, 230, 230))
    os.makedirs(os.path.dirname(png), exist_ok=True)
    im.save(png)
    log('wrote %s (%dx%d)' % (png, w, h))


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if a[:1] == ['stage']:
        return 1 if stage(opt('--in-dir', MAPDIR), opt('--out', OUT)) else 0
    if a[:1] == ['check'] and len(a) >= 2:
        bad = check(a[1], opt('--in-dir', MAPDIR))
        print('CHECK:', 'PASS' if not bad else bad)
        return 1 if bad else 0
    if a[:1] == ['plan']:
        print(json.dumps(plan(int(opt('--deg', DEG)), (float(opt('--tx', TX)), TY, float(opt('--tz', TZ)))), indent=1))
        return 0
    if a[:1] == ['search']:
        search()
        return 0
    if a[:1] == ['plot'] and len(a) >= 2:
        plot(a[1], opt('--out', OUT), opt('--in-dir', MAPDIR))
        return 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
