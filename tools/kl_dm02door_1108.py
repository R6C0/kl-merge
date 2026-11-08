r"""kl_dm02door_1108.py - DM02 (Late Night Opening, slot F02) SECOND door pass, 2026-11-08. OFFLINE: reads a zip, writes a stage; nothing installed.

OWNER (2026-11-08): "why is one of the heist rooms already got their glass blown up with a door to kick down? get rid of the door or make the whole
shop more prettier with a better door to kick down". The first pass (kl_dm02fix_1108.py, part vault) only hid the doubled glass door at D1 / D2. This
pass makes the KICK DOOR ITSELF better. INPUT = the dm02fix_1108 stage (install that first; this kit pins its md5s). Two parts, switchable
(install.py --parts door,remains):

 door     The six KL kick leaves (KL_Interact!1\KL_Door_N\Door, model 0xe404, chunk 58372) all show Metal_F03_Door_01a: the plain WHITE F03 metal slab
          (material 1101, 128 vertices). Dead Men's own glass shop door (model 0x9027, Door_Shatter_Glass_01 Whole04, material 724 =
          Locations/M02/Glass/Glass_01b_Basic_M02_FA, the M02 glass with its reflection) is a thin pane 91 x 209 x 1 cm. This part builds a NEW
          model root from that pane, rotated 180 degrees about Y and scaled into the leaf's own footprint (x -120..0, y 0..240, z +-1), so it hinges
          exactly like the leaf (leaf origin = hinge) and the leaf's collision box (mesh 58365, material _Glacier/Collision) is KEPT as the 2nd object.
          Net look: a glass shop door that shows the shop, instead of a white metal slab.
          The new root is 6 NEW chunks (root, object table, visual mesh, subtable, descriptor, vertex chunk) placed in unreached all-zero 16-byte
          stub chunks of the .prm: chunk count, file size class and Entries= do not change. Shared (not copied): collision mesh 58365, prop 58353,
          glass index chunk 36483, the .oct record (+0x1c) of the leaf. The .MAT ref table gets the delta the new root implies.
          Applied ONLY to the selected leaves (default D1, D2, D5; --doors 1,2,3,4,5,6 chooses): .gms record +0x0c and .prp ZGEOM[4] of that entity.
          NOTHING else changes: no entity hidden / removed / moved, so the 60 KickDoorBehaviourRout nodes, 81 NEXT entries, kick sound events and the
          HVK collision (keyed by REF, same footprint) are untouched. Asserted: the .prp equals the input once those ZGEOM[4] values are put back.
          D5 (ground floor, REF 34495) is the door of the cash-drawer shop behind it: a heist room with the white leaf, so it is in the default.
          GUESSES (comments below): the packed normal / tangent bytes are x,y,z (flipped with 255-b for the 180 degree turn); a root's +0x1c oct
          record shared by two roots is harmless (characters render with empty records; traces still hit the old leaf triangles, same footprint);
          the chunk refcounts of the shared chunks are use counts (+1); the pane stretched 91 -> 120 x 209 -> 240 only stretches the glass texture.
 remains  (OFF by default: install.py --parts door,remains; "(recommended off)") The "already blown up" look. 15 native Remains pieces in the three
          shops (StoreWatch display cases 6, StoreJewel 5, StoreExit 4) stand at the SAME position (< 1 cm) as an intact Whole twin and carry flags
          0x2200e2 (visible); stock Dog Days sets 0x400 on every broken twin at load (kl2 stock F03 218 of 218 Remains carry 0x400, the same pattern
          as this map's other 380). This sets 0x400 on those 15 (.gms flag word, record +28). Remains_box_A/B/C, the Atrium pieces and shard pieces
          with no Whole twin are NOT touched. GUESS: the shatter ('Activate' of HavokShatterGlass, kl2 0x8d1b60) shows a hidden Remains again; not
          proven in kl2.exe here, but all 380 other pairs of this map and all of stock rely on it, so the pieces still appear when the glass breaks.

usage (from tools/):
  python kl_dm02door_1108.py build --parts door,remains --out <dir> [--live <zip>] [--doors 1,2,5]
  python kl_dm02door_1108.py stage [--out C:\kl_build_1024\dm02door_1108] [--live C:\kl_build_1024\dm02fix_1108]
  python kl_dm02door_1108.py check <zip> --live <zip>
"""
import collections, hashlib, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft
import kl_fa_bots as F
import kl_prmgraph as G
import kl_prpjoin as J
import kl_texmat as T
import kl_botsonline
from kl_prp import units

OUT = r'C:\kl_build_1024\dm02door_1108'
FIXDIR = r'C:\kl_build_1024\dm02fix_1108'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM02')
TAG = '.before-dm02door_1108'
PARTS = ('door', 'remains')
DEFAULT_PARTS = ('door',)
# the dm02fix_1108 stage (the input of this pass)
FIX_ZIP, FIX_BOTS, FIX_BASE = 'b3dcebd35d1406016f338886d09b2c93', '8f795fcf', 'b89c86c9'
DOOR_REFS = {1: 34403, 2: 34426, 3: 34449, 4: 34472, 5: 34495, 6: 34518}   # KL_Door_N\Door leaf REFs
DEFAULT_DOORS = (1, 2, 5)
LEAF_ROOT, LEAF_COLL, LEAF_PROP = 58372, 58365, 58353
LEAF_MODEL = 0xe404
GLASS_ROOT, GLASS_MESH, GLASS_VTX, GLASS_MODEL = 36903, 36897, 36894, 0x9027
LEAF_W, LEAF_H, PANE_HALF = 120.0, 240.0, 1.0
HIDE = 0x400
TWIN_GROUPS = ('StoreWatch_201a', 'StoreJewel_201a', 'StoreExit_101a')
BS = chr(92)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5b(d):
    return hashlib.md5(d).hexdigest()


def set_prop(sc, k, name, value):
    lab = J.labels('dd', sc.cls(k))
    node = sc.nodes[k]
    us = [list(u) for u in units(node['props'][1:-1])]
    i = lab.index(name)
    old = struct.unpack('<I', us[i][0][1])[0]
    us[i] = [(us[i][0][0], struct.pack('<I', value))]
    node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
    return old


def get_prop(sc, k, name):
    lab = J.labels('dd', sc.cls(k))
    us = units(sc.nodes[k]['props'][1:-1])
    return struct.unpack('<I', us[lab.index(name)][0][1])[0]


# ---------------------------------------------------------------- door
def pane_vertices(p):
    """The glass pane's 24 vertices (40 B each) turned 180 degrees about Y into the leaf footprint -> (bytes, bbox)."""
    c = p.chunks[GLASS_VTX]
    n = len(c) // 40
    if len(c) % 40 or n != 24:
        raise ValueError('door: glass vertex chunk %d has %d bytes' % (GLASS_VTX, len(c)))
    pos = [struct.unpack_from('<3f', c, 40 * i) for i in range(n)]
    lo = [min(v[i] for v in pos) for i in range(3)]
    hi = [max(v[i] for v in pos) for i in range(3)]
    if not (hi[0] - lo[0] > 80 and hi[1] - lo[1] > 200 and hi[2] - lo[2] < 2):
        raise ValueError('door: glass pane bbox %s %s is not the 91 x 209 x 1 pane' % (lo, hi))
    zc = (lo[2] + hi[2]) / 2
    out = bytearray(c)
    for i, v in enumerate(pos):
        x = -(v[0] - lo[0]) / (hi[0] - lo[0]) * LEAF_W
        y = (v[1] - lo[1]) / (hi[1] - lo[1]) * LEAF_H
        z = -(v[2] - zc) * (2 * PANE_HALF) / max(hi[2] - lo[2], 1e-6)
        struct.pack_into('<3f', out, 40 * i, x, y, z)
        for o in (12, 28, 32):             # packed normal / tangent / binormal (GUESS: bytes 0,1,2 = x,y,z; b = n*127.5+127.5): x,z -> -x,-z
            out[40 * i + o] = 255 - out[40 * i + o]
            out[40 * i + o + 2] = 255 - out[40 * i + o + 2]
    pts = [struct.unpack_from('<3f', out, 40 * i) for i in range(n)]
    return bytes(out), ([min(v[i] for v in pts) for i in range(3)], [max(v[i] for v in pts) for i in range(3)])


def free_stubs(B, p):
    """Unreached all-zero 16-byte chunks, lowest first (what G.reuse() would hand out, without shrinking the rest of the file)."""
    raw = kl_gms.unpack(B['.gms'])
    reached = G.closure(p, G.level_roots(B.sc.p, B.sc.tids, raw))
    return [i for i in range(1, len(p.chunks)) if p.chunks[i] == bytes(16) and i not in reached]


def build_model(p, B, rep):
    """New leaf root in 6 stub chunks. -> root index. Mutates p."""
    for i, kind in ((LEAF_ROOT, 'root'), (GLASS_MESH, 'mesh')):
        if p.u16(i, 2) != {'root': 7, 'mesh': 8}[kind]:
            raise ValueError('door: chunk %d is not a %s' % (i, kind))
    root, glass = bytearray(p.chunks[LEAF_ROOT]), bytes(p.chunks[GLASS_MESH])
    objtab = p.u32(LEAF_ROOT, 0x18)
    ot = struct.unpack_from('<2I', p.chunks[objtab])
    if len(root) != 64 or p.u32(LEAF_ROOT, 0x14) != 2 or ot[0] != LEAF_COLL or p.u32(LEAF_ROOT, 0x10) != LEAF_PROP:
        raise ValueError('door: leaf root %d is not [collision %d, visual] with prop %d' % (LEAF_ROOT, LEAF_COLL, LEAF_PROP))
    sub = p.u32(GLASS_MESH, 0x28)
    desc = p.u32(sub, 0)
    if len(p.chunks[sub]) != 16 or len(p.chunks[desc]) != 48 or p.u32(desc, 4) != GLASS_VTX or p.u32(desc, 0) != 24:
        raise ValueError('door: glass subtab %d / desc %d are not the 24-vertex pane' % (sub, desc))
    vtx, bb = pane_vertices(p)
    lo, hi = struct.unpack_from('<3f', p.chunks[LEAF_ROOT], 0x20), struct.unpack_from('<3f', p.chunks[LEAF_ROOT], 0x2c)
    # the root's bounds are the vertex bbox of ALL its meshes: the collision box already spans the footprint; the pane must lie inside
    if any(bb[0][i] < lo[i] - 0.01 or bb[1][i] > hi[i] + 0.01 for i in range(3)):
        raise ValueError('door: new pane %s exceeds the root bounds %s %s' % (bb, lo, hi))
    stubs = free_stubs(B, p)
    if len(stubs) < 6:
        raise ValueError('door: only %d free stubs' % len(stubs))
    p.free = stubs[::-1]
    nv = G.new_chunk(p, vtx, 1)
    nd = bytearray(p.chunks[desc]); struct.pack_into('<I', nd, 4, nv)
    nd = G.new_chunk(p, bytes(nd), 1)
    ns = bytearray(p.chunks[sub]); struct.pack_into('<I', ns, 0, nd)
    ns = G.new_chunk(p, bytes(ns), 1)
    nm = bytearray(glass); struct.pack_into('<I', nm, 0x28, ns)
    nm = G.new_chunk(p, bytes(nm), 1)
    no = G.new_chunk(p, struct.pack('<2I', LEAF_COLL, nm) + bytes(8), 1)
    nr = bytearray(root); struct.pack_into('<I', nr, 0x18, no)
    nr = G.new_chunk(p, bytes(nr), 1)
    for i in (LEAF_COLL, LEAF_PROP, p.u32(desc, 0x18)):
        p.refs[i] += 1               # GUESS: refcount = number of holders; the new root / mesh holds each once more
    rep['door_chunks'] = collections.OrderedDict(root=nr, objtab=no, mesh=nm, subtab=ns, desc=nd, vertices=nv, shared=[LEAF_COLL, LEAF_PROP, p.u32(desc, 0x18)],
                                                 material=p.u16(GLASS_MESH, 0x12), pane_bbox=[[round(x, 2) for x in v] for v in bb])
    return nr


def part_door(B, files, rep, doors):
    sc = B.sc
    p = G.read(B['.prm'], 'dd')
    if G.write(p) != B['.prm']:
        raise ValueError('door: the .prm does not round-trip')
    n0 = len(p.chunks)
    mat0 = B['.MAT']
    want0 = T.material_refs(B['.prm'])
    stored0 = T.read_mat(mat0).refs
    nr = build_model(p, B, rep)
    # leaves: the entities REF -> node
    ent = {e.ref: k for k, e in enumerate(B.ents, 1)}
    raw = bytearray(kl_gms.unpack(B['.gms']))
    ents = list(kl_gms.entities(bytes(raw)))
    sel = []
    for d in doors:
        k = ent[DOOR_REFS[d]]
        e = B.ents[k - 1]
        rec = 4 * (ents[k - 1][0] & 0xffffff)
        if e.model != LEAF_MODEL or struct.unpack_from('<I', raw, rec + 0x0c)[0] != LEAF_ROOT or get_prop(sc, k, 'ZGEOM[4]') != LEAF_ROOT:
            raise ValueError('door: D%d (REF %d) is not a leaf of model %#x / chunk %d' % (d, e.ref, LEAF_MODEL, LEAF_ROOT))
        if not sc.path[k].endswith('KL_Door_%d' % d + BS + 'Door'):
            raise ValueError('door: node %d is %r, not KL_Door_%d!Door' % (k, sc.path[k], d))
        struct.pack_into('<I', raw, rec + 0x0c, nr)
        set_prop(sc, k, 'ZGEOM[4]', nr)
        sel.append((d, k))
    # root refcounts: the new root counts one per leaf that uses it. The old root's count (2 although 6 leaves share it: it is not an exact use
    # count) is NOT lowered: an over-count only keeps a chunk alive, an under-count could free it (GUESS: refcount semantics not read in kl2.exe).
    p.refs[nr] = len(sel)
    prm = G.write(p)
    if len(p.chunks) != n0:
        raise ValueError('door: chunk count changed')
    # .MAT: the stored table += (what the new .prm implies - what the old implied); stored table must equal the implied one for the deltas to be exact
    want1 = T.material_refs(prm)
    delta = [b - a for a, b in zip(want0, want1)]
    new_refs = [s + d for s, d in zip(stored0, delta)]
    rt = struct.unpack_from('<I', mat0, 12)[0]
    ninst = len(stored0)
    mat = bytearray(mat0)
    struct.pack_into('<%dI' % ninst, mat, rt, *new_refs)
    if T.read_mat(bytes(mat)).refs != new_refs or bytes(mat[:rt]) != mat0[:rt] or bytes(mat[rt + 4 * ninst:]) != mat0[rt + 4 * ninst:]:
        raise ValueError('door: .MAT ref table patch is not exact')
    files[B.ext['.MAT']] = bytes(mat)
    files[B.ext['.prm']] = prm
    files[B.ext['.gms']] = kl_gms.pack(bytes(raw))
    prp = sc.p.serialize()
    if F.Prp(prp).serialize() != prp:
        raise ValueError('door: the patched .prp does not round-trip')
    # the .prp may differ from the input ONLY in those ZGEOM[4] values
    for d, k in sel:
        set_prop(sc, k, 'ZGEOM[4]', LEAF_ROOT)
    if sc.p.serialize() != B.files[B.ext['.prp']]:
        raise ValueError('door: .prp differs from the input beyond ZGEOM[4]')
    for d, k in sel:
        set_prop(sc, k, 'ZGEOM[4]', nr)
    files[B.ext['.prp']] = sc.p.serialize()
    rep['door'] = collections.OrderedDict(doors=['D%d' % d for d, _k in sel], refs=[DOOR_REFS[d] for d, _k in sel], new_root=nr, chunks=n0,
                                          mat_ref_delta={str(i): d for i, d in enumerate(delta) if d},
                                          mat_table_was_implied=(want0 == stored0))


# ---------------------------------------------------------------- remains
def remains_targets(B):
    """-> [(node k, twin node)]: Remains pieces of the three shops with an intact (visible) twin at the same spot."""
    sc = B.sc
    bygrp = collections.defaultdict(list)
    for k in range(1, len(sc.names)):
        bygrp[sc.path[k].rsplit(BS, 1)[0]].append(k)
    out = []
    for k, e in enumerate(B.ents, 1):
        nm = sc.names[k].rsplit('!', 1)[-1]
        g = sc.path[k].rsplit(BS, 1)[0]
        if 'Remains' not in nm or e.flags & HIDE or not any(t in g for t in TWIN_GROUPS) or 'box' in nm.lower():
            continue
        a = B.at(k)
        for j in bygrp[g]:
            if j == k or j > len(B.ents):
                continue
            m = sc.names[j].rsplit('!', 1)[-1]
            f = B.ents[j - 1].flags
            if f & HIDE or f == 0x3200000 or 'Remains' in m:
                continue
            if ('Whole' in m or m.startswith('Glassmontre_big') or m.startswith('Glassmontre_Small_0')) and \
                    sum((x - y) ** 2 for x, y in zip(a, B.at(j))) ** 0.5 < 1.0:
                out.append((k, j))
                break
    return out


def part_remains(B, files, rep):
    tg = remains_targets(B)
    if len(tg) != 15:
        raise ValueError('remains: %d targets, expected 15' % len(tg))
    raw = bytearray(kl_gms.unpack(files[B.ext['.gms']]))
    ents = list(kl_gms.entities(bytes(raw)))
    for k, _j in tg:
        rec = 4 * (ents[k - 1][0] & 0xffffff)
        if struct.unpack_from('<I', raw, rec + 28)[0] != B.ents[k - 1].flags:
            raise ValueError('remains: flags word of node %d is not at record +28' % k)
        struct.pack_into('<I', raw, rec + 28, B.ents[k - 1].flags | HIDE)
    files[B.ext['.gms']] = kl_gms.pack(bytes(raw))
    rep['remains'] = collections.OrderedDict(hidden=[B.ents[k - 1].ref for k, _j in tg])


# ---------------------------------------------------------------- build / check
def build(live, outdir, parts, doors=DEFAULT_DOORS, log=print):
    parts = [p for p in PARTS if p in parts]
    if not parts:
        raise ValueError('no parts')
    B = F.Built(live, 'F02')
    files = dict(B.files)
    rep = collections.OrderedDict(parts=parts, live=live, live_md5=md5(live))
    if 'door' in parts:
        part_door(B, files, rep, doors)
    if 'remains' in parts:
        part_remains(B, files, rep)
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F02_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
    want = {'door': {'F02_Main.prm', 'F02_Main.MAT', 'F02_Main.gms', 'F02_Main.prp'}, 'remains': {'F02_Main.gms'}}
    allowed = set().union(*[want[p] for p in parts])
    if not set(diff) <= allowed:
        raise ValueError('members changed %s outside %s' % (diff, sorted(allowed)))
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
    with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
    log('dm02door_1108 parts=%s -> %s (%s) members %s' % (','.join(parts), plain, rep['out_md5'], diff))
    return rep


def check(plain, live, parts, doors=DEFAULT_DOORS, log=print):
    """Offline read-back of a built zip against its input: -> list of problems (empty = ok)."""
    bad = []
    A, Bn = F.Built(live, 'F02'), F.Built(plain, 'F02')
    if len(A.ents) != len(Bn.ents) or A.sc.names != Bn.sc.names or A.sc.path != Bn.sc.path:
        bad.append('entity list / names / paths changed')
    pa, pb = G.read(A['.prm'], 'dd'), G.read(Bn['.prm'], 'dd')
    if len(pa.chunks) != len(pb.chunks):
        bad.append('chunk count %d -> %d' % (len(pa.chunks), len(pb.chunks)))
    changed = [i for i in range(1, min(len(pa.chunks), len(pb.chunks))) if pa.chunks[i] != pb.chunks[i]]
    if 'door' in parts:
        if len(changed) > 12:
            bad.append('door: %d chunks changed' % len(changed))
        for i in changed:
            if pa.chunks[i] != bytes(16):
                bad.append('door: chunk %d was not a stub before' % i)
        if G.write(pb) != Bn['.prm']:
            bad.append('door: .prm does not round-trip')
        ra = G.closure(pa, G.level_roots(A.sc.p, A.sc.tids, kl_gms.unpack(A['.gms'])))
        for i in changed:
            if i in ra:
                bad.append('door: reached chunk %d changed' % i)
        mb = T.read_mat(Bn['.MAT'])
        if mb.refs != [s + d for s, d in zip(T.read_mat(A['.MAT']).refs, [x - y for x, y in zip(T.material_refs(Bn['.prm']), T.material_refs(A['.prm']))])]:
            bad.append('door: .MAT refs')
        raw = kl_gms.unpack(Bn['.gms'])
        rawa = kl_gms.unpack(A['.gms'])
        roots = [m for m in G.gms_roots(raw)]
        rootsa = G.gms_roots(rawa)
        sel = {DOOR_REFS[d] for d in doors}
        for k, (x, y) in enumerate(zip(rootsa, roots), 1):
            if (x != y) != (Bn.ents[k - 1].ref in sel):
                bad.append('door: .gms root of node %d changed unexpectedly' % k)
            if x != y and get_prop(Bn.sc, k, 'ZGEOM[4]') != y:
                bad.append('door: .prp ZGEOM[4] of node %d is not the .gms root' % k)
        nroots = {y for x, y in zip(rootsa, roots) if x != y}
        if len(nroots) != 1:
            bad.append('door: %d new roots' % len(nroots))
        else:
            r = nroots.pop()
            ob = pb.u32(r, 0x18)
            objs = struct.unpack_from('<2I', pb.chunks[ob])
            mats = [pb.u16(o, 0x12) for o in objs]
            if mats != [109, 724] or pb.u32(r, 0x1c) != pa.u32(LEAF_ROOT, 0x1c) or pb.chunks[r][0x20:0x38] != pa.chunks[LEAF_ROOT][0x20:0x38]:
                bad.append('door: new root objects %s / oct / bounds' % mats)
            v = pb.chunks[pb.u32(pb.u32(pb.u32(objs[1], 0x28), 0), 4)]
            pts = [struct.unpack_from('<3f', v, 40 * i) for i in range(len(v) // 40)]
            lo = struct.unpack_from('<3f', pb.chunks[r], 0x20)
            hi = struct.unpack_from('<3f', pb.chunks[r], 0x2c)
            if any(min(q[i] for q in pts) < lo[i] - 0.01 or max(q[i] for q in pts) > hi[i] + 0.01 for i in range(3)):
                bad.append('door: pane outside the root bounds')
            if pb.u32(pb.u32(pb.u32(objs[1], 0x28), 0), 0x18) != pa.u32(pa.u32(pa.u32(GLASS_MESH, 0x28), 0), 0x18):
                bad.append('door: index chunk differs from the glass pane')
    else:
        if pa.chunks != pb.chunks:
            bad.append('door off but .prm changed')
    if 'remains' in parts:
        n = [k for k, (a, b) in enumerate(zip(A.ents, Bn.ents), 1) if a.flags != b.flags]
        if sorted(Bn.ents[k - 1].ref for k in n) != sorted(Bn.ents[k - 1].ref for k, _j in remains_targets(A)):
            bad.append('remains: flags changed on %s' % [Bn.ents[k - 1].ref for k in n])
        if any(not Bn.ents[k - 1].flags & HIDE or Bn.ents[k - 1].flags & ~HIDE != A.ents[k - 1].flags for k in n):
            bad.append('remains: flag word is not old | 0x400')
    elif any(a.flags != b.flags for a, b in zip(A.ents, Bn.ents)):
        bad.append('remains off but flags changed')
    return bad


# ---------------------------------------------------------------- install.py / stage
import kl_dm02fix_1108 as _fix


def _kit_template():
    """The dm02fix_1108 install.py template (same pins / undo / refusal logic) with this pass's parts, doors and backup tag."""
    t = _fix.INSTALL_PY
    rep = [
        ('Installs / undoes the DM02 FIX 1108 (cover boxes off the atrium columns, co-op shutters back, doubled watch-store glass door hidden).',
         'Installs / undoes the DM02 DOOR pass 1108 (glass kick doors in place of the white metal leaves; optional: hide the 15 shattered-glass twins).\nNeeds the dm02fix_1108 layer installed FIRST (this pins its files).'),
        ('python install.py --parts cover,coop build the chosen parts first', 'python install.py --parts door,remains --doors 1,2,5 build the chosen parts first'),
        ("parts = a[a.index('--parts') + 1].split(',') if '--parts' in a else ['cover', 'coop', 'vault']",
         "parts = a[a.index('--parts') + 1].split(',') if '--parts' in a else ['door']\n    doors = a[a.index('--doors') + 1] if '--doors' in a else '1,2,5'"),
        ("if any(p not in ('cover', 'coop', 'vault') for p in parts):", "if any(p not in ('door', 'remains') for p in parts) or any(x not in '123456,' for x in doors):"),
        ("--parts takes cover, coop, vault", "--parts takes door, remains; --doors a list of 1..6"),
        ("parts = [p for p in ('cover', 'coop', 'vault') if p in parts]", "parts = [p for p in ('door', 'remains') if p in parts]"),
        ("if parts != ['cover', 'coop', 'vault']:\n        src = os.path.join(HERE, 'parts_' + '_'.join(parts))",
         "if parts != ['door'] or doors != '1,2,5':\n        src = os.path.join(HERE, 'parts_' + '_'.join(parts) + '_d' + doors.replace(',', ''))"),
        ("'--parts', ','.join(parts), '--out', src,", "'--parts', ','.join(parts), '--doors', doors, '--out', src,"),
        ("another layer changed it: re-stage on --base live", "install dm02fix_1108 first, or re-stage on --base live"),
    ]
    for a, b in rep:
        if a not in t:
            raise ValueError('install template: %r not found' % a[:60])
        t = t.replace(a, b)
    return t


def stage(live_dir, out, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    pins = (md5(live), md5(os.path.join(live_dir, 'F02_Main.bots.zip')), open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip())
    if not (pins[0] == FIX_ZIP and pins[1].startswith(FIX_BOTS) and pins[2] == FIX_ZIP and md5(os.path.join(live_dir, 'F02_Main.bots.base.md5')).startswith(FIX_BASE)):
        raise SystemExit('input is not the dm02fix_1108 stage (%s / %s / %s)' % pins)
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        if n != 'work':
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    rep = build(live, out, DEFAULT_PARTS)
    bad = check(os.path.join(out, 'F02_Main.zip'), live, DEFAULT_PARTS)
    if bad:
        raise SystemExit('check failed: %s' % bad)
    staged = {n: md5(os.path.join(out, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(_kit_template() % dict(tag=TAG, tool=os.path.join(HERE, 'kl_dm02door_1108.py'), live=pins[0], bots=pins[1], base=pins[2], staged=repr(staged)))
    for nm, arg in (('INSTALL dm02 door 1108', ''), ('UNDO dm02 door 1108', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    rep['staged'], rep['check'], rep['input_pins'] = staged, 'ok', pins
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    log(json.dumps(rep['staged'], indent=1))
    return rep


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    doors = tuple(int(x) for x in opt('--doors', ','.join(map(str, DEFAULT_DOORS))).split(','))
    if a and a[0] == 'build':
        live = opt('--live', os.path.join(FIXDIR, 'F02_Main.zip'))
        rep = build(live, opt('--out', OUT), opt('--parts', ','.join(DEFAULT_PARTS)).split(','), doors)
        bad = check(os.path.join(opt('--out', OUT), 'F02_Main.zip'), live, rep['parts'], doors)
        if bad:
            print('check failed:', bad); return 1
        return 0
    if a and a[0] == 'stage':
        stage(opt('--live', FIXDIR), opt('--out', OUT))
        return 0
    if len(a) >= 2 and a[0] == 'check':
        bad = check(a[1], opt('--live', os.path.join(FIXDIR, 'F02_Main.zip')), opt('--parts', ','.join(DEFAULT_PARTS)).split(','), doors)
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
