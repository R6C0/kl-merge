#!/usr/bin/env python3
r"""
Payday 2 masks into the Kane & Lynch wardrobe (2026-10-10). The Kane & Lynch HALF: everything that turns a
rigid mesh (positions, normals, uvs, triangles, in HEAD-bone space) plus a diffuse / normal DDS into chunks,
a material and textures of a Dog Days level. The Payday 2 half (reading .model / .texture, tools\pd2_model.py)
feeds `Plate` objects into `add_mask`. Facts come from re\pd2_klside.md (measured on stock F01 and the owner's
wardrobe build); nothing here was run in the game yet.

    python kl_pd2mask.py selftest [<build folder>]      round trip J.C.'s stock mask through the builders (byte-equal
                                                        vertex / index / descriptor / runs chunks), clone Merc_Masks dry

HEAD space (re\pd2_klside.md 3): HEAD = bone 7 in all 16 wardrobe skeletons; rest rotation byte-identical:
    model = R . h + t,  R columns = HEAD axes in model space:  X = model +y (up), Y = model +z (BACK: the face is -Y),
    Z = model -x (the character's RIGHT); t = (0, 162.69 .. 162.88, -1.91).
A rigid mask is stored in MODEL space (bind pose) like every vertex, weighted 1.0 to HEAD: weights (1, 0, 0),
palette bytes (0, 0, 0, 0), one bone run {12 x 1, 12 x 7}. The game moves it with HEAD.

VERTEX (52 bytes, mesh subtype 3): +0 f32x3 position, +12 f32x3 weights (4th = 1 - sum), +24 u8x4 = 3 x palette
entry, +28 normal packed B,G,R,0 = ((b2-128)/127, (b1-128)/127, (b0-128)/127), +32 D3DCOLOR 0xffffffff,
+36 f32x2 uv (v down), +44 tangent (+dP/du) and +48 binormal (+dP/dv), packed like the normal.
INDEX chunk: u16 1 (segments), u16 count, count x u16; triangle LIST; the stored order (a, b, c) has its outward
normal = (c - a) x (b - a) (clockwise from outside). DESCRIPTOR: 12 dwords [vertex count, vertex chunk, 0, 0, 0,
dword5 (0 accepted), index chunk, 0 x5]. SUBTAB: [descriptor, 0, 0, 0]. MESH OBJECT: 64 bytes copied from a stock
Merc_Masks object with +0x0e LOD, +0x0f variant, +0x12 material, +0x28 subtab, +0x38 run count, +0x3c runs.
BOUNDS: only the model root's six floats at +0x20 (union box) - widened when a plate sticks out.
MATERIAL: a clone of Merc_Masks (class SkinCloth, flags 0x10, normal + specular stages) with new TXIDs; the .TEX
record for a DDS payload: 'u32 size | fourcc reversed x2 | u32 id | u16 h | u16 w | u32 mips | u32 flags | f32 scale
| u32 0 | name\0 | mips x (u32 n, data)', DXT5 normal maps carry flags 0x40 and scale 251/255 (ASSUMPTION from the
193 such records of F01, Merc_Masks' own normal map among them).
"""
import math, os, struct, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T

HEAD_BONE = 7
MERC_MASKS = 'Merc_Masks'
NORMAL_FLAGS, NORMAL_SCALE = 0x40, 251 / 255.0


# ------------------------------------------------------------------ packing
def pack_dir(v):
    """(x, y, z) unit vector -> the 4 bytes B,G,R,0 the vertex uses (re/pd2_klside.md 1)."""
    q = lambda c: max(0, min(255, int(round(c * 127 + 128))))
    return bytes((q(v[2]), q(v[1]), q(v[0]), 0))


def unpack_dir(b):
    return ((b[2] - 128) / 127.0, (b[1] - 128) / 127.0, (b[0] - 128) / 127.0)


def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _norm(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def tangents(pos, uv, tris):
    """Per-vertex (tangent, binormal) = +dP/du, +dP/dv, area-weighted over the triangles (re/pd2_klside.md 1)."""
    t = [(0.0, 0.0, 0.0)] * len(pos); b = list(t)
    for a, c, d in tris:
        e1, e2 = _sub(pos[c], pos[a]), _sub(pos[d], pos[a])
        du1, dv1 = uv[c][0] - uv[a][0], uv[c][1] - uv[a][1]
        du2, dv2 = uv[d][0] - uv[a][0], uv[d][1] - uv[a][1]
        det = du1 * dv2 - du2 * dv1
        if abs(det) < 1e-12:
            continue
        r = 1.0 / det
        tt = tuple((e1[k] * dv2 - e2[k] * dv1) * r for k in range(3))
        bb = tuple((e2[k] * du1 - e1[k] * du2) * r for k in range(3))
        for i in (a, c, d):
            t[i] = tuple(t[i][k] + tt[k] for k in range(3)); b[i] = tuple(b[i][k] + bb[k] for k in range(3))
    return [_norm(x) for x in t], [_norm(x) for x in b]


class Plate:
    """A rigid mesh in MODEL space: pos / nrm / uv lists (same length), tris [(a, b, c)] with outward normal
    (b - a) x (c - a) (the usual counter-clockwise convention; the writer flips to the file's order)."""

    def __init__(self, pos, nrm, uv, tris, name='plate'):
        self.pos, self.nrm, self.uv, self.tris, self.name = pos, nrm, uv, tris, name
        if not (len(pos) == len(nrm) == len(uv)):
            raise ValueError('%s: %d positions, %d normals, %d uvs' % (name, len(pos), len(nrm), len(uv)))
        if len(pos) > 65535:
            raise ValueError('%s: %d vertices do not fit u16 indices' % (name, len(pos)))

    def box(self):
        xs, ys, zs = zip(*self.pos)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def vertex_chunk(plate, flip=True):
    """The 52-byte vertex stream of a plate weighted to one bone (palette entry 0)."""
    tris = [(a, c, b) for a, b, c in plate.tris] if flip else plate.tris
    tan, bin_ = tangents(plate.pos, plate.uv, tris)
    out = bytearray()
    for k in range(len(plate.pos)):
        out += struct.pack('<3f3f', *plate.pos[k], 1.0, 0.0, 0.0)
        out += b'\0\0\0\0' + pack_dir(plate.nrm[k]) + b'\xff\xff\xff\xff'
        out += struct.pack('<2f', *plate.uv[k]) + pack_dir(tan[k]) + pack_dir(bin_[k])
    return bytes(out) + bytes(-len(out) % 16)


def index_chunk(tris, flip=True):
    ii = [i for a, b, c in tris for i in ((a, c, b) if flip else (a, b, c))]
    out = struct.pack('<HH', 1, len(ii)) + struct.pack('<%dH' % len(ii), *ii)
    return out + bytes(-len(out) % 16)


def runs_chunk(bone=HEAD_BONE):
    return struct.pack('<II', 12, 12 * bone) + bytes(8)


def descriptor(nv, vchunk, ichunk, dword5=0):
    return struct.pack('<12I', nv, vchunk, 0, 0, 0, dword5, ichunk, 0, 0, 0, 0, 0)


def subtab(desc):
    return struct.pack('<4I', desc, 0, 0, 0)


def mesh_object(template, lod, variant, material, sub, runs, nruns=1):
    """A 64-byte mesh object from a stock Merc_Masks one (its +0x14 / +0x18 / +0x1c are copied)."""
    c = bytearray(template)
    if len(c) != 64 or c[0x0c] != 3:
        raise ValueError('the template is not a weighted mesh object')
    c[0x0e], c[0x0f] = lod, variant
    struct.pack_into('<H', c, 0x12, material)
    struct.pack_into('<I', c, 0x28, sub)
    struct.pack_into('<II', c, 0x38, nruns, runs)
    return bytes(c)


# ------------------------------------------------------------------ into a level's .prm
class Geometry:
    """The shared chunks of one plate in a .prm (vertex, index, descriptor, subtab, runs): made once, then
    `objects()` stamps a 64-byte mesh object per (lod, variant, material)."""

    def __init__(self, p, plate, template, flip=True):
        self.p, self.plate, self.template = p, plate, template
        self.v = G.new_chunk(p, vertex_chunk(plate, flip))
        self.i = G.new_chunk(p, index_chunk(plate.tris, flip))
        self.d = G.new_chunk(p, descriptor(len(plate.pos), self.v, self.i))
        self.s = G.new_chunk(p, subtab(self.d))
        self.r = G.new_chunk(p, runs_chunk())

    def object(self, lod, variant, material):
        return G.new_chunk(self.p, mesh_object(self.template, lod, variant, material, self.s, self.r))


def widen_root(p, root, box):
    """Grow the model root's union box (+0x20 six floats) to hold `box` = ((min), (max))."""
    lo = list(struct.unpack_from('<3f', p.chunks[root], 0x20)); hi = list(struct.unpack_from('<3f', p.chunks[root], 0x2c))
    for k in range(3):
        lo[k] = min(lo[k], box[0][k]); hi[k] = max(hi[k], box[1][k])
    c = bytearray(p.chunks[root]); struct.pack_into('<6f', c, 0x20, *lo, *hi); p.chunks[root] = bytes(c)


def stock_mask_template(p, mat):
    """A stock Merc_Masks mesh object of the file (the 64-byte template) and its material slot."""
    slot = next(s for s, e in mat.insts.items() if e.name and e.name.endswith('/' + MERC_MASKS))
    for i, c in enumerate(p.chunks):
        if c and len(c) == 64 and c[:4] == b'\x89\x00\x08\x00' and c[0x0c] == 3 and struct.unpack_from('<H', c, 0x12)[0] == slot:
            return c, slot
    raise ValueError('no Merc_Masks mesh object in this .prm')


# ------------------------------------------------------------------ textures and the material
def dds_mips(data):
    """A DDS file -> (fourcc b'DXT1' | b'DXT5', width, height, [mip bytes ...])."""
    if data[:4] != b'DDS ' or struct.unpack_from('<I', data, 4)[0] != 124:
        raise ValueError('not a DDS file')
    h, w, mips = struct.unpack_from('<II', data, 12)[0], struct.unpack_from('<I', data, 16)[0], struct.unpack_from('<I', data, 28)[0] or 1
    fourcc = data[84:88]
    if fourcc not in (b'DXT1', b'DXT5', b'DXT3'):
        raise ValueError('DDS format %r: only DXT1 / DXT3 / DXT5 are wrapped' % fourcc)
    block = 8 if fourcc == b'DXT1' else 16
    out, q = [], 128
    for m in range(mips):
        mw, mh = max(w >> m, 1), max(h >> m, 1)
        n = max(1, (mw + 3) // 4) * max(1, (mh + 3) // 4) * block
        out.append(data[q:q + n]); q += n
    if q > len(data):
        raise ValueError('DDS is %d bytes short of its mip chain' % (q - len(data)))
    return fourcc, w, h, out


def tex_record(tid, name, fourcc, w, h, mips, normal_map=False):
    """A Dog Days .TEX record (kl_texmat docstring) from a DDS mip chain."""
    rev = {b'DXT1': b'1TXD', b'DXT3': b'3TXD', b'DXT5': b'5TXD'}[fourcc]
    body = rev + rev + struct.pack('<IHHIIfI', tid, h, w, len(mips), NORMAL_FLAGS if normal_map else 0,
                                   NORMAL_SCALE if normal_map else 1.0, 0)
    body += name.encode('latin1') + b'\0'
    for m in mips:
        body += struct.pack('<I', len(m)) + m
    return struct.pack('<I', len(body) + 4) + body


def add_texture(tex, name, dds_bytes, normal_map=False, group=None):
    """-> the new texture id."""
    fourcc, w, h, mips = dds_mips(dds_bytes)
    tid = next(i for i in range(128, tex.slots) if i not in tex.tex)
    tex.tex[tid] = T.Texture(tex_record(tid, name, fourcc, w, h, mips, normal_map), group=group or 0)
    return tid


def clone_material(mat, name, diffuse, normal=None, specular=None):
    """A copy of Merc_Masks under `name` with the given .TEX ids (None keeps Merc_Masks' own). -> new slot."""
    src = mat.insts[next(s for s, e in mat.insts.items() if e.name and e.name.endswith('/' + MERC_MASKS))]
    clone = T.Entry(src.cls, list(src.f), T._copy(src.root))
    for stage, node in T.texture_stages(clone):
        if stage == 'mapDiffuse':
            node[3] = diffuse
        elif stage == 'mapNormal' and normal is not None:
            node[3] = normal
        elif stage == 'mapSpecularMask' and specular is not None:
            node[3] = specular
    nm = next(n for n in clone.root[3] if n[0] == 'NAME')
    nm[3] = name.encode('latin1')
    slot = max(mat.insts) + 1
    if slot >= mat.ninst:
        raise ValueError('the .MAT has no free instance slot')
    mat.insts[slot] = clone
    return slot


# ------------------------------------------------------------------ self test
def _stock_plate(p, o):
    """J.C.'s stock mask object read back as a Plate (positions, normals, uvs; triangles in the FILE order)."""
    d = p.u32(p.u32(o, 0x28), 0); nv = p.u32(d, 0); v = p.chunks[p.u32(d, 4)]
    pos = [struct.unpack_from('<3f', v, 52 * k) for k in range(nv)]
    nrm = [unpack_dir(v[52 * k + 28:52 * k + 32]) for k in range(nv)]
    uv = [struct.unpack_from('<2f', v, 52 * k + 36) for k in range(nv)]
    ix = p.chunks[p.u32(d, 0x18)]; n = struct.unpack_from('<H', ix, 2)[0]
    ii = struct.unpack_from('<%dH' % n, ix, 4)
    tris = [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)]
    return Plate(pos, nrm, uv, tris, 'stock'), v, ix, d


def selftest(build=None, log=print):
    import kl_chars as C
    lv = C.Lv(build if build and os.path.isdir(build) else 'F01')          # 'F01' = the stock level (KL_PortBackup)
    p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    tpl, slot = stock_mask_template(p, mat)
    o = next(i for i, c in enumerate(p.chunks) if c == tpl)
    plate, v, ix, d = _stock_plate(p, o)
    ok = True
    # 1. the index chunk round-trips (file order in, flip off)
    ic = index_chunk(plate.tris, flip=False)
    log('  index chunk: %s (%d vs %d bytes)' % ('same' if ic == bytes(ix) else 'DIFFERENT', len(ic), len(ix)))
    ok &= ic == bytes(ix)
    # 2. the vertex chunk: positions, normals, uvs and the packed tangent frame against the stock bytes
    vc = vertex_chunk(Plate(plate.pos, plate.nrm, plate.uv, plate.tris, 'rt'), flip=False)
    nv = len(plate.pos)
    pos_ok = all(vc[52 * k:52 * k + 12] == v[52 * k:52 * k + 12] for k in range(nv))
    nrm_ok = sum(1 for k in range(nv) if max(abs(a - b) for a, b in zip(vc[52 * k + 28:52 * k + 32], v[52 * k + 28:52 * k + 32])) <= 1)
    uv_ok = all(vc[52 * k + 36:52 * k + 44] == v[52 * k + 36:52 * k + 44] for k in range(nv))
    agree = lambda off: sum(1 for k in range(nv) if _dot(unpack_dir(vc[52 * k + off:52 * k + off + 4]), unpack_dir(v[52 * k + off:52 * k + off + 4])) > 0.7)
    log('  vertex chunk: positions %s, normals within 1/127 on %d / %d, uvs %s, tangent agrees on %d, binormal on %d (weights / palette differ by design: the stock mask uses 7 bones)' % (
        'same' if pos_ok else 'DIFFERENT', nrm_ok, nv, 'same' if uv_ok else 'DIFFERENT', agree(44), agree(48)))
    ok &= pos_ok and uv_ok and nrm_ok == nv and agree(44) > 0.95 * nv and agree(48) > 0.95 * nv
    # 3. descriptor / subtab / object shapes
    dd = descriptor(nv, p.u32(d, 4), p.u32(d, 0x18), p.u32(d, 0x14))
    log('  descriptor: %s' % ('same' if dd == bytes(p.chunks[d]) else 'DIFFERENT'))
    ok &= dd == bytes(p.chunks[d])
    mo = mesh_object(tpl, tpl[0x0e], tpl[0x0f], slot, p.u32(o, 0x28), p.u32(o, 0x3c), p.u32(o, 0x38))
    log('  mesh object: %s' % ('same' if mo == bytes(tpl) else 'DIFFERENT'))
    ok &= mo == bytes(tpl)
    # 4. material clone + texture wrap, in memory: Merc_Masks' own diffuse re-wrapped from its record
    e = tex.tex[next(n[3] for s, n in T.texture_stages(mat.insts[slot]) if s == 'mapDiffuse')].entry
    size, f1, _f2, _id, th, tw, mips, fl, sc = struct.unpack_from('<I4s4sIHHIIf', e, 0)
    q = e.index(b'\0', 36) + 1; chain = []
    for _m in range(mips):
        n = struct.unpack_from('<I', e, q)[0]; chain.append(e[q + 4:q + 4 + n]); q += 4 + n
    rec = tex_record(_id, e[36:e.index(b'\0', 36)].decode('latin1'), {b'1TXD': b'DXT1', b'5TXD': b'DXT5'}[f1], tw, th, chain)
    log('  .TEX record re-wrap of Merc_Masks diffuse: %s (%d bytes)' % ('same' if rec == bytes(e) else 'DIFFERENT', len(rec)))
    ok &= rec == bytes(e)
    before = (len(mat.insts), len(tex.tex))
    new_slot = clone_material(mat, 'Characters/_MultiPlayer/_All_Levels/PD2_Mask_Test', diffuse=_id)
    T.write_mat(mat); T.write_tex(tex)
    log('  clone: slot %d (%d -> %d instances, %d textures); .MAT / .TEX write back' % (new_slot, before[0], len(mat.insts), before[1]))
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'selftest':
        sys.exit(0 if selftest(a[1] if len(a) > 1 else None) else 1)
    print(__doc__)
