#!/usr/bin/env python3
"""
Payday 2 (Diesel engine) .model and .texture reader, pure Python (3.14, no numpy / PIL). Everything
below was measured on the 661 mask / character .model files extracted with tools/pd2_crate.py from
Steam build 25506656 (2026-10-10); re/pd2_model.md has the numbers and the pictures' descriptions.

    python tools/pd2_model.py info <file.model>                 sections, object tree, meshes, skin, bounds
    python tools/pd2_model.py obj  <file.model> <out.obj>       Wavefront OBJ, world (root) space, 'o' per model,
                                                                normals, uvs, 'usemtl' per render atom
    python tools/pd2_model.py png  <file.model> <out.png> [--tex <df.texture|.dds> | --tex g_body=<f>;g_hands=<f>]
                                   [--objs g_body,g_hands] [--size 300] [--up y|z]
                                                                front / side / top, textured with the top DXT mip
    python tools/pd2_model.py onhead <body.model> <mask.model> <out.png> [--head g_head_dallas] [--tex ...]
                                                                the character's head mesh with the mask placed at
                                                                its Head object (identity), front / side / top
    python tools/pd2_model.py tex  <file.texture> <out.dds> [--png <out.png>]
    python tools/pd2_model.py scan <folder>                     every .model under it: parsed / failed / unknown
                                                                section types, stream codes, model sizes
    python tools/pd2_model.py head <body.model> <mask.model>    the Head object's rest frame of a character and
                                                                where the mask lands when placed at it
    python tools/pd2_model.py holes <file.model> [--min 4]      boundary loops (eye holes, rim) in root space

FILE  = 'DODB' u32 1  u32 file size  u32 section count, then sections {u32 type, u32 id, u32 size, body}
        back to back to the file end (every file: count and sizes add up exactly).  Public Diesel tools
        describe an older header (u32 -1, size, count) for the bundle-era files; the crate-era files
        have this 16-byte one.  Section ids are 1-based, unique per file, and are what other sections
        refer to.  Names are u64 little-endian Jenkins lookup8 hash64 (pd2_crate.hash64) of the name:
        hash64(b'rp_wolf_mask') = 03a3b6d53742e6fa is stored as bytes fa e6 42 37 d5 b6 a3 03.  The exe
        ships no hashlist for object names; this module hashes candidate names (bone names, the words of
        the unit's .object / .unit / .material_config XML next to the model, a built-in list) and shows
        '?<hash>' for the rest.

SECTION TYPES (count over the 661 files):
  5dc011b8  661  file header: u64 hash c62ff7a7a32c724d, u32 x2 (0x3d088988 in masks, 0 in the body), u32 0.
  7623c465  661  Author: u64 hash, then NUL-separated strings: e-mail, source .mb/.ma path, 5 empty.
  29276b1d 1551  MaterialGroup: u32 count, u32 Material ids.
  3c54609c 1590  Material: u64 name hash, then 52 bytes (u32 0 x5, f 1, 0,0,0, f 1, 0,0,0): all identical.
  0ffcd100  879  Object3D: u64 name hash, u32 controller count, {u32 controller id, u32 0, u32 0} x count
                 (12 bytes each: 116-byte objects have 2), float[16] matrix (ROW-vector convention:
                 world = local x parent; the translation is floats 12..14), float[3] position (repeats the
                 translation), u32 parent id (0 = root).
  62212d88 1074  Model: the Object3D fields, then u32 version.  version 6 (7 files: c_sphere_head and such
                 collision models): float[6] box min / max, float radius, u32 0.  version 3: u32 PassthroughGP
                 id, u32 TopologyIP id, u32 atom count, atoms {u32 base vertex, u32 triangle count, u32 base
                 index, u32 vertex count, u32 material index into the group} x count, u32 MaterialGroup id,
                 u32 lightset (0), u32 properties (3), float[3] box min, float[3] box max, float radius,
                 u32 (6 in every file read), u32 SkinBones id (0 = rigid).  Sizes 176 / 196 / 216 / 256 =
                 1 / 2 / 3 / 5 atoms.
  7ab072d3 1067  Geometry: u32 vertex count, u32 stream count, {u32 size code, u32 stream type} x count,
                 the streams one after another (NOT interleaved), 8 bytes tail (a hash; 6 distinct values
                 over 1067 geometries = the vertex layout's name, ASSUMPTION).  Size codes and bytes per
                 item (proved by section size = 8 + 8n + vertices x sum + 8 in all 1067): 3 = 12 (3 floats),
                 9 = 4 (2 halfs), 8 = 4 (4 x u8), 7 = 8 (4 x u16), 2 = 8 (2 floats), 5 = 4 (4 x u8).
                 Stream types: 1 position 3f (cm), 7 uv0 half2, 8 uv1 half2, 2 normal, 22 tangent,
                 23 binormal (each 4 x u8: x = byte 2, y = byte 1, z = byte 0, w = byte 3, value
                 b / 255 * 2 - 1: mean dot with the face normals 0.83 for that byte order, 0.02 for the
                 others; lengths 0.99..1.01), 17 bone indices 4 x u16 (into the SkinBones id list),
                 19 bone weights 3f (the fourth is the rest), 5 colour 4 x u8 (3 files).  v of the uvs is
                 negative (0 .. -1) and counts from the BOTTOM of the picture: DDS row from the top = 1 + v
                 (wolf / dallas: chin vertices -v 0.09, eye holes 0.43 / 0.46, brow 0.5 .. 0.8, and the DDS
                 has the chin at the bottom, the eyes at row 0.53).  OBJ vt = -v.
  4c507a13 1067  Topology: u32 3, u32 index count, u16 indices (triangle list), u32 count + bytes
                 (0 in every file), u64 name hash.
  e3a3b1ca 1067  PassthroughGP: u32 Geometry id, u32 Topology id.
  03b634bd 1067  TopologyIP: u32 Topology id.
  65cc1825   45  SkinBones: u32 list count (2 in every file read), lists {u32 count, u32 bone slot} x
                 count (ASSUMPTION: per-atom bone subsets), u32 root object id (Hips), u32 bone count,
                 u32 object ids, float[16] per bone (inverse bind: Head's is -1 0 0 / 0 0 1 / 0 1 0 with
                 translation (0, -166.76, -5.33) = the inverse of Head's rest), float[16] global skin
                 transform (= Hips' matrix).
  26a5128c   22  animation controller, position keys: u64 hash, u32 0, f, f end time, u32 n, {f time,
  648a206c   22  float[3]} x n;  rotation keys: the same head, {f time, float[4] quaternion} x n.
                 Only msk_fps_back_straps and fps_temp_dallas have them (ASSUMPTION on the key layout).
  Unknown types are kept raw and reported by `scan`.

UNITS AND AXES: centimetres, Z up, +Y forward (the criminal body's Head object sits at world (0, 5.33,
166.76), the nose of its head mesh points +y, a child point 15 cm along the Head's local z = world +y).
A bone's local Y is the bone direction; the Hips matrix maps local (x, y, z) to world (-x, z, y), and
Head inherits that frame: Head local x = world -x, y = world up, z = world forward.  Skinned vertices are
stored in root space (the g_* models hang under Hips with the inverse of Hips' transform), rigid ones in
the Model's own space.

TEXTURE: a plain DDS file ('DDS ', header size 124, fourCC DXT5 for every mask map read, 512 x 512 x 10 mips
for the crew masks, 1024 for the fps ones; the _nm maps carry the 'A2D5' swizzle tag in the pixel format
(flag 0x80000000): x in alpha, y in green, z rebuilt).  `tex` copies the file as .dds and decodes the top mip
to PNG.  A MASK FILE'S ROOT SPACE IS THE HEAD FRAME (y up, z forward, x the character's left): the mask is
placed at the body's Head object with identity (its box then lies exactly in front of the head meshes).
"""
import struct, sys, os, math, json, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

T_HEADER, T_AUTHOR, T_MATGROUP, T_MATERIAL = 0x5dc011b8, 0x7623c465, 0x29276b1d, 0x3c54609c
T_OBJECT3D, T_MODEL, T_GEOMETRY, T_TOPOLOGY = 0x0ffcd100, 0x62212d88, 0x7ab072d3, 0x4c507a13
T_PASSGP, T_TOPOIP, T_SKINBONES, T_BONES = 0xe3a3b1ca, 0x03b634bd, 0x65cc1825, 0x2eb43c77
T_CTRL_POS, T_CTRL_ROT, T_TOOLHASHES = 0x26a5128c, 0x648a206c, 0x7c7844fd
TYPE_NAMES = {T_HEADER: 'FileHeader', T_AUTHOR: 'Author', T_MATGROUP: 'MaterialGroup', T_MATERIAL: 'Material',
              T_OBJECT3D: 'Object3D', T_MODEL: 'Model', T_GEOMETRY: 'Geometry', T_TOPOLOGY: 'Topology',
              T_PASSGP: 'PassthroughGP', T_TOPOIP: 'TopologyIP', T_SKINBONES: 'SkinBones', T_BONES: 'Bones',
              T_CTRL_POS: 'PositionController', T_CTRL_ROT: 'RotationController', T_TOOLHASHES: 'ModelToolHashes'}
STREAM_BYTES = {1: 4, 2: 8, 3: 12, 4: 16, 5: 4, 6: 8, 7: 8, 8: 4, 9: 4}
STREAM_NAMES = {1: 'position', 2: 'normal', 5: 'colour', 7: 'uv0', 8: 'uv1', 17: 'bone_indices', 19: 'bone_weights',
                20: 'tangent?', 21: 'binormal?', 22: 'tangent', 23: 'binormal'}

COMMON_NAMES = ('root_point Hips Spine Spine1 Spine2 Neck Head HeadEnd Head_end LeftShoulder LeftArm LeftForeArm '
                'LeftForeArmRoll LeftHand RightShoulder RightArm RightForeArm RightForeArmRoll RightHand LeftUpLeg '
                'LeftLeg LeftFoot LeftToeBase RightUpLeg RightLeg RightFoot RightToeBase LeftHandThumb1 LeftHandThumb2 '
                'LeftHandThumb3 LeftHandIndex1 LeftHandIndex2 LeftHandIndex3 LeftHandMiddle1 LeftHandMiddle2 '
                'LeftHandMiddle3 LeftHandRing1 LeftHandRing2 LeftHandRing3 LeftHandPinky1 LeftHandPinky2 '
                'LeftHandPinky3 RightHandThumb1 RightHandThumb2 RightHandThumb3 RightHandIndex1 RightHandIndex2 '
                'RightHandIndex3 RightHandMiddle1 RightHandMiddle2 RightHandMiddle3 RightHandRing1 RightHandRing2 '
                'RightHandRing3 RightHandPinky1 RightHandPinky2 RightHandPinky3 a_weapon_right a_weapon_left '
                'a_weapon_right_front a_weapon_left_front a_equipment a_head Head_look Head_Eye Head_eye e_taser '
                'shadow_caster rp_mask rp_wolf_mask rp_dallas_mask rp_chains_mask rp_hoxton_mask g_wolf g_dallas '
                'g_chains g_hoxton g_mask g_glow g_mask_glow g_straps g_fps_straps s_body c_capsule_body c_sphere_head '
                'g_body g_hands g_head mtr_mask mtr_glow mtr_straps default Camera camera').split()


# ------------------------------------------------------------------ hashing / names
def hash64(k, level=0):
    from pd2_crate import hash64 as h
    return h(k, level)


class Names:
    """hash -> name for every candidate string this can collect; unknown hashes print as ?<hex>."""
    def __init__(self, near=None, extra=()):
        self.map = {}
        self.add(COMMON_NAMES)
        self.add(extra)
        if near:
            self.harvest(near)

    def add(self, names):
        for n in names:
            if n:
                self.map[hash64(n.encode('utf-8'))] = n

    def harvest(self, path):
        """Words and quoted strings of the text / xml files in the model's folder (and its unit's)."""
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        seen = set()
        for root, _ds, fs in os.walk(folder):
            for f in fs:
                if f.endswith(('.xml', '.unit', '.object', '.material_config', '.txt', '.sequence_manager')):
                    p = os.path.join(root, f)
                    try:
                        t = open(p, 'r', encoding='utf-8', errors='replace').read()
                    except OSError:
                        continue
                    for m in re.findall(r'[A-Za-z_][A-Za-z0-9_\-\.]*', t):
                        seen.add(m)
                    for m in re.findall(r'"([^"]*)"', t):
                        seen.add(m)
                        seen.add(m.rsplit('/', 1)[-1])
        self.add(seen)

    def of(self, h):
        return self.map.get(h, '?%016x' % h)


# ------------------------------------------------------------------ small matrix helpers (row-vector)
def mat_mul(a, b):
    """a x b for 4x4 row-major float[16] (row vectors: p' = p x M)."""
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]


def mat_apply(m, p):
    x, y, z = p
    return (x * m[0] + y * m[4] + z * m[8] + m[12], x * m[1] + y * m[5] + z * m[9] + m[13],
            x * m[2] + y * m[6] + z * m[10] + m[14])


def mat_apply_dir(m, p):
    x, y, z = p
    return (x * m[0] + y * m[4] + z * m[8], x * m[1] + y * m[5] + z * m[9], x * m[2] + y * m[6] + z * m[10])


def mat_inverse_rigid(m):
    """Inverse of a rotation + translation matrix (transpose the 3x3, rotate the translation back)."""
    r = [m[0], m[4], m[8], 0, m[1], m[5], m[9], 0, m[2], m[6], m[10], 0, 0, 0, 0, 1]
    t = mat_apply_dir(r, (m[12], m[13], m[14]))
    r[12], r[13], r[14] = -t[0], -t[1], -t[2]
    return r


IDENTITY = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]


def half(h):
    s, e, m = (h >> 15) & 1, (h >> 10) & 31, h & 1023
    if e == 0:
        v = m / 1024.0 * 2.0 ** -14
    elif e == 31:
        v = float('inf') if m == 0 else float('nan')
    else:
        v = (1 + m / 1024.0) * 2.0 ** (e - 15)
    return -v if s else v


# ------------------------------------------------------------------ the file
class Section:
    __slots__ = ('type', 'id', 'data', 'offset')

    def __init__(self, t, i, d, o):
        self.type, self.id, self.data, self.offset = t, i, d, o


class Object3D:
    def __init__(self, sec, names):
        b = sec.data
        self.id, self.section = sec.id, sec
        self.hash = struct.unpack_from('<Q', b, 0)[0]
        self.name = names.of(self.hash)
        n = struct.unpack_from('<I', b, 8)[0]
        self.controllers = [struct.unpack_from('<3I', b, 12 + 12 * k) for k in range(n)]
        o = 12 + 12 * n
        self.local = list(struct.unpack_from('<16f', b, o))
        self.position = struct.unpack_from('<3f', b, o + 64)
        self.parent = struct.unpack_from('<I', b, o + 76)[0]
        self.body_offset = o + 80
        self.world = None
        self.children = []
        self.model = None             # Model data when this is a Model section


class ModelData:
    pass


class Geometry:
    def __init__(self, sec):
        b = sec.data
        self.id = sec.id
        self.count, nh = struct.unpack_from('<II', b, 0)
        self.headers = [struct.unpack_from('<II', b, 8 + 8 * k) for k in range(nh)]
        o = 8 + 8 * nh
        self.streams = {}
        for code, typ in self.headers:
            size = STREAM_BYTES.get(code)
            if size is None:
                raise ValueError('unknown stream size code %d (type %d)' % (code, typ))
            self.streams[typ] = (code, size, o)
            o += size * self.count
        self.tail = b[o:]
        if len(self.tail) != 8:
            raise ValueError('geometry tail %d bytes, expected 8' % len(self.tail))
        self.data = b
        self._cache = {}

    def _floats(self, typ, n):
        code, size, o = self.streams[typ]
        return [struct.unpack_from('<%df' % n, self.data, o + size * k) for k in range(self.count)]

    def positions(self):
        if 'pos' not in self._cache:
            self._cache['pos'] = self._floats(1, 3)
        return self._cache['pos']

    def uvs(self, typ=7):
        if typ not in self.streams:
            return None
        code, size, o = self.streams[typ]
        if code == 9:
            return [tuple(half(x) for x in struct.unpack_from('<2H', self.data, o + 4 * k)) for k in range(self.count)]
        return self._floats(typ, 2)

    def packed_dirs(self, typ):
        """Normal (2) / tangent (22) / binormal (23): 4 x u8, bytes (z, y, x, w)."""
        if typ not in self.streams:
            return None
        code, size, o = self.streams[typ]
        if code != 8:
            return self._floats(typ, 3)
        d = self.data
        return [((d[o + 4 * k + 2] / 255.0) * 2 - 1, (d[o + 4 * k + 1] / 255.0) * 2 - 1, (d[o + 4 * k] / 255.0) * 2 - 1)
                for k in range(self.count)]

    def bone_indices(self):
        if 17 not in self.streams:
            return None
        code, size, o = self.streams[17]
        if code == 7:
            return [struct.unpack_from('<4H', self.data, o + 8 * k) for k in range(self.count)]
        return [tuple(self.data[o + 4 * k:o + 4 * k + 4]) for k in range(self.count)]

    def bone_weights(self):
        if 19 not in self.streams:
            return None
        code, size, o = self.streams[19]
        n = size // 4
        out = []
        for k in range(self.count):
            w = list(struct.unpack_from('<%df' % n, self.data, o + size * k))
            w.append(max(0.0, 1.0 - sum(w)))
            out.append(tuple(w))
        return out


class Topology:
    def __init__(self, sec, names):
        b = sec.data
        self.id = sec.id
        self.kind, n = struct.unpack_from('<II', b, 0)
        self.indices = struct.unpack_from('<%dH' % n, b, 8)
        o = 8 + 2 * n
        cnt = struct.unpack_from('<I', b, o)[0]
        self.extra = b[o + 4:o + 4 + cnt]
        o += 4 + cnt
        self.hash = struct.unpack_from('<Q', b, o)[0]
        self.name = names.of(self.hash)
        if o + 8 != len(b):
            raise ValueError('topology: %d bytes left' % (len(b) - o - 8))

    def triangles(self):
        ii = self.indices
        return [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, len(ii) - 2, 3)]


class SkinBones:
    def __init__(self, sec):
        b = sec.data
        self.id = sec.id
        nl = struct.unpack_from('<I', b, 0)[0]
        o = 4
        self.lists = []
        for _ in range(nl):
            c = struct.unpack_from('<I', b, o)[0]
            self.lists.append(struct.unpack_from('<%dI' % c, b, o + 4))
            o += 4 + 4 * c
        self.root, nb = struct.unpack_from('<2I', b, o)
        o += 8
        self.objects = struct.unpack_from('<%dI' % nb, b, o)
        o += 4 * nb
        self.matrices = [list(struct.unpack_from('<16f', b, o + 64 * k)) for k in range(nb)]
        o += 64 * nb
        self.global_transform = list(struct.unpack_from('<16f', b, o))
        o += 64
        if o != len(b):
            raise ValueError('skinbones: %d bytes left' % (len(b) - o))


class Model:
    """A parsed .model: sections, objects (tree), meshes, materials."""

    def __init__(self, path, names=None):
        self.path = path
        d = open(path, 'rb').read()
        self.size = len(d)
        magic, ver, fsize, n = struct.unpack_from('<4sIII', d, 0)
        if magic != b'DODB' or fsize != len(d):
            raise ValueError('not a DODB model (magic %r, size %d of %d)' % (magic, fsize, len(d)))
        self.version = ver
        self.sections = []
        p = 16
        for _ in range(n):
            t, sid, sz = struct.unpack_from('<III', d, p)
            self.sections.append(Section(t, sid, d[p + 12:p + 12 + sz], p))
            p += 12 + sz
        if p != len(d):
            raise ValueError('sections end at %d of %d' % (p, len(d)))
        self.by_id = {s.id: s for s in self.sections}
        self.unknown = sorted(set(s.type for s in self.sections if s.type not in TYPE_NAMES))
        self.names = names or Names(path)
        self.author = None
        for s in self.sections:
            if s.type == T_AUTHOR:
                self.author = [x.decode('utf-8', 'replace') for x in s.data[8:].split(b'\0')]
            if s.type == T_TOOLHASHES:
                cnt = struct.unpack_from('<I', s.data, 0)[0]
                o, strs = 4, []
                for _ in range(cnt):
                    ln = struct.unpack_from('<I', s.data, o)[0]
                    strs.append(s.data[o + 4:o + 4 + ln].decode('utf-8', 'replace'))
                    o += 4 + ln
                self.names.add(strs)
        self.materials = {s.id: self.names.of(struct.unpack_from('<Q', s.data, 0)[0]) for s in self.sections if s.type == T_MATERIAL}
        self.material_groups = {}
        for s in self.sections:
            if s.type == T_MATGROUP:
                c = struct.unpack_from('<I', s.data, 0)[0]
                self.material_groups[s.id] = struct.unpack_from('<%dI' % c, s.data, 4)
        self.geometries = {s.id: Geometry(s) for s in self.sections if s.type == T_GEOMETRY}
        self.topologies = {s.id: Topology(s, self.names) for s in self.sections if s.type == T_TOPOLOGY}
        self.passgp = {s.id: struct.unpack_from('<2I', s.data, 0) for s in self.sections if s.type == T_PASSGP}
        self.topoip = {s.id: struct.unpack_from('<I', s.data, 0)[0] for s in self.sections if s.type == T_TOPOIP}
        self.skins = {s.id: SkinBones(s) for s in self.sections if s.type == T_SKINBONES}
        self.objects = {}
        for s in self.sections:
            if s.type in (T_OBJECT3D, T_MODEL):
                o = Object3D(s, self.names)
                if s.type == T_MODEL:
                    o.model = self._model_body(s.data, o.body_offset)
                self.objects[o.id] = o
        self.roots = []
        for o in self.objects.values():
            if o.parent and o.parent in self.objects:
                self.objects[o.parent].children.append(o)
            else:
                self.roots.append(o)
        for r in self.roots:
            self._world(r, IDENTITY)

    def _world(self, o, parent_world):
        o.world = mat_mul(o.local, parent_world)
        for c in o.children:
            self._world(c, o.world)

    def _model_body(self, b, o):
        m = ModelData()
        m.version = struct.unpack_from('<I', b, o)[0]
        o += 4
        if m.version == 6:
            m.bounds = struct.unpack_from('<6f', b, o)
            m.radius = struct.unpack_from('<f', b, o + 24)[0]
            m.unknown = struct.unpack_from('<I', b, o + 28)[0]
            m.passgp = m.topoip = None
            m.atoms = []
            m.material_group = m.skin = 0
            m.rest = b[o + 32:]
            return m
        m.passgp, m.topoip, na = struct.unpack_from('<3I', b, o)
        o += 12
        m.atoms = [struct.unpack_from('<5I', b, o + 20 * k) for k in range(na)]
        o += 20 * na
        m.material_group, m.lightset, m.properties = struct.unpack_from('<3I', b, o)
        o += 12
        m.bounds = struct.unpack_from('<6f', b, o)
        m.radius = struct.unpack_from('<f', b, o + 24)[0]
        m.unknown, m.skin = struct.unpack_from('<2I', b, o + 28)
        m.rest = b[o + 36:]
        return m

    # -- meshes --------------------------------------------------------------------------------
    def mesh(self, obj):
        """(geometry, topology) of a Model object with a mesh, or None."""
        m = obj.model
        if not m or m.version == 6 or m.passgp not in self.passgp:
            return None
        g, t = self.passgp[m.passgp]
        return self.geometries.get(g), self.topologies.get(t)

    def mesh_objects(self):
        return [o for o in self.objects.values() if o.model and self.mesh(o)]

    def atom_materials(self, obj):
        grp = self.material_groups.get(obj.model.material_group, ())
        out = []
        for a in obj.model.atoms:
            mid = grp[a[4]] if a[4] < len(grp) else None
            out.append(self.materials.get(mid, '?'))
        return out

    def world_mesh(self, obj, pose=None):
        """positions / normals / uvs / triangles of a Model in root space (rigid: by its world matrix;
        skinned: the stored root-space positions, or linear blend skinning with pose = {object id: matrix}).
        Returns dict(pos, nrm, uv, tris, atoms)."""
        geo, top = self.mesh(obj)
        pos = geo.positions()
        nrm = geo.packed_dirs(2)
        skin = self.skins.get(obj.model.skin) if obj.model.skin else None
        if skin and pose:
            bi, bw = geo.bone_indices(), geo.bone_weights()
            mats = []
            for k, oid in enumerate(skin.objects):
                mats.append(mat_mul(skin.matrices[k], pose.get(oid, self.objects[oid].world)))
            out = []
            for k in range(geo.count):
                acc = [0.0, 0.0, 0.0]
                for j in range(4):
                    w = bw[k][j]
                    if w <= 0:
                        continue
                    q = mat_apply(mats[bi[k][j]], pos[k])
                    acc[0] += w * q[0]; acc[1] += w * q[1]; acc[2] += w * q[2]
                out.append(tuple(acc))
            wpos = out
            wnrm = nrm
        else:
            wpos = [mat_apply(obj.world, p) for p in pos]
            wnrm = [mat_apply_dir(obj.world, n) for n in nrm] if nrm else None
        return {'pos': wpos, 'nrm': wnrm, 'uv': geo.uvs(7), 'tris': top.triangles(), 'atoms': obj.model.atoms,
                'materials': self.atom_materials(obj)}

    def bounds(self, objs=None):
        lo, hi = [1e30] * 3, [-1e30] * 3
        for o in objs or self.mesh_objects():
            for p in self.world_mesh(o)['pos']:
                for i in range(3):
                    lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
        return lo, hi

    # -- reports -------------------------------------------------------------------------------
    def tree_lines(self):
        out = []

        def walk(o, depth):
            kind = 'MODEL' if o.model else 'OBJ'
            extra = ''
            if o.model:
                m = o.model
                if m.version == 6:
                    extra = '  v6 box %s r %.2f' % (['%.2f' % x for x in m.bounds], m.radius)
                else:
                    mesh = self.mesh(o)
                    nv = mesh[0].count if mesh else 0
                    nt = len(mesh[1].indices) // 3 if mesh else 0
                    extra = '  %d verts %d tris atoms %s mats %s box %s skin %s' % (
                        nv, nt, [a[:4] for a in m.atoms], self.atom_materials(o), ['%.2f' % x for x in m.bounds],
                        m.skin or '-')
            rot = 'I' if all(abs(o.local[i] - (1 if i % 5 == 0 else 0)) < 1e-4 for i in range(12)) else \
                '[%s]' % ' '.join('%.3f' % x for x in o.local[:11] if True)
            out.append('%s%-5s %3d %-24s pos (%.2f %.2f %.2f) rot %s%s' % ('  ' * depth, kind, o.id, o.name, *o.position, rot, extra))
            for c in o.children:
                walk(c, depth + 1)
        for r in self.roots:
            walk(r, 0)
        return out

    def info(self):
        L = ['%s: %d bytes, %d sections, version %d' % (self.path, self.size, len(self.sections), self.version)]
        cnt = collections.Counter(TYPE_NAMES.get(s.type, '?%08x' % s.type) for s in self.sections)
        L.append('sections: ' + ', '.join('%s x%d' % kv for kv in sorted(cnt.items())))
        if self.author:
            L.append('author: ' + ' | '.join(x for x in self.author if x))
        L.append('materials: ' + ', '.join('%d=%s' % kv for kv in sorted(self.materials.items())))
        L += self.tree_lines()
        for g in self.geometries.values():
            L.append('geometry %d: %d vertices, streams %s, tail %s' % (
                g.id, g.count, ' '.join('%s(code %d)' % (STREAM_NAMES.get(t, 'type%d' % t), c) for c, t in g.headers), g.tail.hex()))
        for s in self.skins.values():
            L.append('skinbones %d: root %d (%s), %d bones: %s; lists %s' % (
                s.id, s.root, self.names.of(self.objects[s.root].hash) if s.root in self.objects else '?',
                len(s.objects), ' '.join(self.objects[i].name if i in self.objects else str(i) for i in s.objects),
                [len(x) for x in s.lists]))
        if self.mesh_objects():
            lo, hi = self.bounds()
            L.append('bounds (root space, all meshes): %s .. %s' % (['%.2f' % x for x in lo], ['%.2f' % x for x in hi]))
        if self.unknown:
            L.append('UNKNOWN section types: ' + ' '.join('%08x' % t for t in self.unknown))
        return '\n'.join(L)


# ------------------------------------------------------------------ OBJ
def write_obj(model, out, objs=None):
    vbase = 1
    with open(out, 'w') as f:
        f.write('# %s\n' % model.path)
        for o in objs or model.mesh_objects():
            m = model.world_mesh(o)
            f.write('o %s\n' % o.name)
            for p in m['pos']:
                f.write('v %.5f %.5f %.5f\n' % p)
            if m['uv']:
                for u, v in m['uv']:
                    f.write('vt %.5f %.5f\n' % (u, -v))
            if m['nrm']:
                for n in m['nrm']:
                    f.write('vn %.5f %.5f %.5f\n' % n)
            tris = m['tris']
            for a, mat in zip(m['atoms'], m['materials']):
                f.write('usemtl %s\n' % mat)
                for k in range(a[2] // 3, (a[2] + 3 * a[1]) // 3):
                    if k >= len(tris):
                        break
                    t = tris[k]
                    f.write('f ' + ' '.join('%d/%d/%d' % (vbase + i, vbase + i, vbase + i) for i in t) + '\n')
            vbase += len(m['pos'])


# ------------------------------------------------------------------ DDS
def _565(c):
    return ((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)


def dds_info(d):
    if d[:4] != b'DDS ':
        return None
    h, flags, height, width, pitch, depth, mips = struct.unpack_from('<7I', d, 4)
    fourcc = d[84:88]
    pf_flags = struct.unpack_from('<I', d, 80)[0]
    swizzle = d[88:92]
    return {'width': width, 'height': height, 'mips': mips, 'fourcc': fourcc.decode('latin-1'), 'pf_flags': pf_flags,
            'swizzle': swizzle.decode('latin-1') if pf_flags & 0x80000000 else '', 'writer': d[76:80].decode('latin-1')}


def dds_decode(d, want=512, normal=False):
    """Top mip not wider than `want` of a DXT1 / DXT5 DDS -> (w, h, rgb bytearray). normal=True reads a
    DXT5 'A2D5' map as (x = alpha, y = green, z from the two) into rgb."""
    i = dds_info(d)
    if not i or i['fourcc'] not in ('DXT1', 'DXT5', 'DXT3'):
        return None
    w, h = i['width'], i['height']
    blk = 8 if i['fourcc'] == 'DXT1' else 16
    o = 128
    for m in range(max(i['mips'], 1)):
        if w <= want or m == i['mips'] - 1:
            break
        o += ((w + 3) // 4) * ((h + 3) // 4) * blk
        w, h = max(w // 2, 1), max(h // 2, 1)
    out = bytearray(3 * w * h)
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            if o + blk > len(d):
                break
            if blk == 16:
                a0, a1 = d[o], d[o + 1]
                abits = int.from_bytes(d[o + 2:o + 8], 'little')
                c0, c1, bits = struct.unpack_from('<HHI', d, o + 8)
            else:
                c0, c1, bits = struct.unpack_from('<HHI', d, o)
            o += blk
            a, b = _565(c0), _565(c1)
            if c0 > c1 or blk == 16:
                c = (a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b)))
            else:
                c = (a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0))
            for k in range(16):
                y, x = by + k // 4, bx + k % 4
                if y >= h or x >= w:
                    continue
                col = c[(bits >> (2 * k)) & 3]
                if normal and blk == 16:
                    ai = (abits >> (3 * k)) & 7
                    if ai == 0: al = a0
                    elif ai == 1: al = a1
                    elif a0 > a1: al = ((8 - ai) * a0 + (ai - 1) * a1) // 7
                    elif ai == 6: al = 0
                    elif ai == 7: al = 255
                    else: al = ((6 - ai) * a0 + (ai - 1) * a1) // 5
                    nx, ny = al / 255.0 * 2 - 1, col[1] / 255.0 * 2 - 1
                    nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
                    col = (al, col[1], int((nz + 1) * 127.5))
                p = 3 * (y * w + x)
                out[p], out[p + 1], out[p + 2] = col
    return w, h, out


# ------------------------------------------------------------------ pictures
def view_space(p, up='z'):
    """Model frame -> kl_view's (x right, y up, z toward the viewer; its 'front' view shows the -z side).
    up='z': the Diesel world frame (x right, y forward, z up) of a character file; up='y': the Head frame
    (x left, y up, z forward) that a mask file's root space is in.  'front' then shows the face."""
    return (p[0], p[2], -p[1]) if up == 'z' else (p[0], p[1], -p[2])


def guess_up(model):
    """'z' when the file has a skeleton root (a character), else 'y' (a mask: its root space is the Head frame)."""
    return 'z' if any(o.name in ('root_point', 'Hips') for o in model.objects.values()) else 'y'


def render_items(out, items, size=300):
    """items: [(positions in view space, triangles, uv or None, texture or None)] -> front / side / top sheet."""
    import kl_view
    meshes, lo, hi = [], [1e30] * 3, [-1e30] * 3
    for pos, tris, uv, tex in items:
        for p in pos:
            for i in range(3):
                lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
        meshes.append((pos, tris, kl_view.PALETTE[len(meshes) % len(kl_view.PALETTE)], uv, tex))
    span = max(hi[i] - lo[i] for i in range(3)) * 1.1 or 1
    cx = [(lo[i] + hi[i]) / 2 for i in range(3)]
    sq = lambda a, b: (a - span / 2, a + span / 2, b - span / 2, b + span / 2)
    # side: kl_view u = z, d = x: seen from +x; top: looked down the up axis, the face toward the picture's top
    top = [([(p[0], -p[2], -p[1]) for p in pos], tris, col, uv, t) for pos, tris, col, uv, t in meshes]
    panels = [('front', sq(cx[0], cx[1]), meshes), ('side', sq(cx[2], cx[1]), meshes), ('front', sq(cx[0], -cx[2]), top)]
    kl_view.sheet(out, panels, w=size, h=size)
    return lo, hi


def mesh_item(model, o, tex, up, xform=None, pose=None):
    m = model.world_mesh(o, pose)
    pos = m['pos'] if xform is None else [mat_apply(xform, p) for p in m['pos']]
    uv = [(u, 1 + v) for u, v in m['uv']] if m['uv'] else None      # row from the top = 1 + v (v is 0 .. -1)
    t = tex.get(o.name) if isinstance(tex, dict) else tex
    return ([view_space(p, up) for p in pos], m['tris'], uv, t if uv else None)


def render(model, out, tex=None, size=300, objs=None, pose=None, up=None):
    """tex: one decoded texture for everything, or {object name: texture}."""
    up = up or guess_up(model)
    return render_items(out, [mesh_item(model, o, tex, up, pose=pose) for o in objs or model.mesh_objects()], size)


def render_on_head(body, mask, out, head_objs, tex=None, size=300, head_name='Head'):
    """The character's head meshes and the mask's meshes placed at the Head object with identity, world frame."""
    head = [o for o in body.objects.values() if o.name == head_name][0]
    items = [mesh_item(body, o, tex, 'z') for o in body.mesh_objects() if o.name in head_objs]
    items += [mesh_item(mask, o, tex, 'z', xform=head.world) for o in mask.mesh_objects()]
    return render_items(out, items, size)


def load_texture(path, normal=False):
    d = open(path, 'rb').read()
    return dds_decode(d, want=512, normal=normal)


# ------------------------------------------------------------------ scan
def scan(folder):
    files = sorted(os.path.join(r, f) for r, _ds, fs in os.walk(folder) for f in fs if f.endswith('.model'))
    ok, failed, unknown = 0, [], collections.Counter()
    codes, model_sizes, streams = collections.Counter(), collections.Counter(), collections.Counter()
    names = Names()
    for fn in files:
        try:
            m = Model(fn, names)
        except Exception as e:                      # noqa: report, do not stop
            failed.append((fn, str(e)))
            continue
        ok += 1
        for t in m.unknown:
            unknown[t] += 1
        for g in m.geometries.values():
            for c, t in g.headers:
                codes[(c, t)] += 1
            streams[tuple(t for c, t in g.headers)] += 1
        for s in m.sections:
            if s.type == T_MODEL:
                model_sizes[len(s.data)] += 1
    return {'files': len(files), 'parsed': ok, 'failed': failed, 'unknown_types': {'%08x' % k: v for k, v in unknown.items()},
            'stream_codes': {'%d/%s' % (c, STREAM_NAMES.get(t, t)): n for (c, t), n in sorted(codes.items())},
            'stream_layouts': {' '.join(STREAM_NAMES.get(t, str(t)) for t in k): n for k, n in streams.most_common()},
            'model_section_sizes': dict(sorted(model_sizes.items()))}


# ------------------------------------------------------------------ holes (eye holes, rim)
def boundary_loops(model, obj, merge=0.01):
    """Closed loops of boundary edges (edges used by exactly one triangle) of a Model's mesh, in root space.
    Vertices are merged by position (UV seams duplicate them).  Returns [(loop positions)] largest first."""
    m = model.world_mesh(obj)
    pos = m['pos']
    key = {}
    canon = []
    for k, p in enumerate(pos):
        q = (round(p[0] / merge), round(p[1] / merge), round(p[2] / merge))
        canon.append(key.setdefault(q, k))
    edges = collections.Counter()
    for a, b, c in m['tris']:
        a, b, c = canon[a], canon[b], canon[c]
        for u, v in ((a, b), (b, c), (c, a)):
            if u != v:
                edges[(min(u, v), max(u, v))] += 1
    nxt = collections.defaultdict(list)
    for (u, v), n in edges.items():
        if n == 1:
            nxt[u].append(v); nxt[v].append(u)
    seen, loops = set(), []
    for s in list(nxt):
        if s in seen:
            continue
        loop, cur, prev = [], s, None
        while cur is not None and cur not in seen:
            seen.add(cur); loop.append(pos[cur])
            cand = [v for v in nxt[cur] if v != prev and v not in seen]
            prev, cur = cur, (cand[0] if cand else None)
        loops.append(loop)
    loops.sort(key=len, reverse=True)
    return loops


def holes_report(model, min_len=4):
    L = []
    for o in model.mesh_objects():
        loops = boundary_loops(model, o)
        L.append('%s: %d boundary loops' % (o.name, len(loops)))
        for lp in loops:
            if len(lp) < min_len:
                continue
            n = len(lp)
            c = tuple(sum(p[i] for p in lp) / n for i in range(3))
            lo = tuple(min(p[i] for p in lp) for i in range(3))
            hi = tuple(max(p[i] for p in lp) for i in range(3))
            L.append('  %4d verts  centre (%6.2f %6.2f %6.2f)  size (%5.2f %5.2f %5.2f)' % (
                n, *c, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    return '\n'.join(L)


# ------------------------------------------------------------------ head frame
def head_report(body_path, mask_path, head_name='Head'):
    body = Model(body_path)
    mask = Model(mask_path)
    head = [o for o in body.objects.values() if o.name == head_name]
    if not head:
        return 'no object named %s' % head_name
    head = head[0]
    inv = mat_inverse_rigid(head.world)
    L = ['body %s: %d objects, %d meshes' % (body_path, len(body.objects), len(body.mesh_objects()))]
    chain = []
    o = head
    while o:
        chain.append(o)
        o = body.objects.get(o.parent)
    L.append('chain: ' + ' <- '.join('%s(%s)' % (o.name, ' '.join('%.2f' % x for x in o.position)) for o in chain))
    L.append('Head world matrix rows: %s | pos %s' % (
        ' / '.join('(%s)' % ' '.join('%.3f' % head.world[4 * r + c] for c in range(3)) for r in range(3)),
        ' '.join('%.2f' % x for x in head.world[12:15])))
    for ax, v in (('x', (1, 0, 0)), ('y', (0, 1, 0)), ('z', (0, 0, 1))):
        L.append('  Head local %s in world: %s' % (ax, ' '.join('%.3f' % c for c in mat_apply_dir(head.world, v))))
    lo, hi = body.bounds()
    L.append('body bounds (root space): %s .. %s -> height %.1f' % (['%.1f' % x for x in lo], ['%.1f' % x for x in hi], hi[2] - lo[2]))
    # head meshes: vertices whose dominant bone is Head
    for o in body.mesh_objects():
        if 'head' not in o.name.lower():
            continue
        geo, top = body.mesh(o)
        skin = body.skins.get(o.model.skin)
        bi, bw = geo.bone_indices(), geo.bone_weights()
        pos = geo.positions()
        hl, hh = [1e30] * 3, [-1e30] * 3
        n = 0
        for k in range(geo.count):
            if skin and bi:
                j = max(range(4), key=lambda i: bw[k][i])
                if skin.objects[bi[k][j]] != head.id:
                    continue
            q = mat_apply(inv, pos[k])
            n += 1
            for i in range(3):
                hl[i] = min(hl[i], q[i]); hh[i] = max(hh[i], q[i])
        wl, wh = body.bounds([o])
        L.append('%s: %d of %d vertices on Head; Head-space box %s .. %s; root-space box %s .. %s' % (
            o.name, n, geo.count, ['%.2f' % x for x in hl], ['%.2f' % x for x in hh], ['%.2f' % x for x in wl], ['%.2f' % x for x in wh]))
    # the mask at Head with identity
    L.append('mask %s: roots %s' % (mask_path, [r.name for r in mask.roots]))
    ml, mh = mask.bounds()
    L.append('  mask bounds in its own root space: %s .. %s (size %s)' % (
        ['%.2f' % x for x in ml], ['%.2f' % x for x in mh], ['%.2f' % (mh[i] - ml[i]) for i in range(3)]))
    for o in mask.mesh_objects():
        L.append('  model %s local pos %s, model-space box %s' % (o.name, ' '.join('%.2f' % x for x in o.position), ['%.2f' % x for x in o.model.bounds]))
    wl, wh = [1e30] * 3, [-1e30] * 3
    for o in mask.mesh_objects():
        for p in mask.world_mesh(o)['pos']:
            q = mat_apply(head.world, p)
            for i in range(3):
                wl[i] = min(wl[i], q[i]); wh[i] = max(wh[i], q[i])
    L.append('  placed at Head with identity: world box %s .. %s (Head at %s; up = z)' % (
        ['%.2f' % x for x in wl], ['%.2f' % x for x in wh], ' '.join('%.2f' % x for x in head.world[12:15])))
    L += fit_lines(mask, ml, mh)
    return '\n'.join(L)


# Kane & Lynch 2 HEAD frame (re/pd2_klside.md section 3): X up, Y back (the face is -Y), Z the character's right.
# Payday 2 Head frame (a mask file's root space): x the character's left, y up, z forward.
# So  X = y,  Y = -z,  Z = -x.  Targets: eye centres HEAD (6.5, -11.5, +-3.3), whole-head mask box
# (-14.7, -17.0, -10.2) .. (20.9, 10.8, 10.4).
KL_EYE = (6.5, -11.5, 3.3)
KL_BOX = ((-14.7, -17.0, -10.2), (20.9, 10.8, 10.4))


def to_kl(p):
    return (p[1], -p[2], -p[0])


def eye_holes(mask):
    """The two smallest symmetric boundary loops (>= 8 vertices, |x| > 1.5) of the mask's meshes -> their centres
    in the mask's root space, or None."""
    cands = []
    for o in mask.mesh_objects():
        for lp in boundary_loops(mask, o):
            if len(lp) < 8:
                continue
            c = tuple(sum(p[i] for p in lp) / len(lp) for i in range(3))
            if abs(c[0]) > 1.5:
                cands.append((len(lp), c))
    cands.sort()
    left = [c for n, c in cands if c[0] > 0]
    right = [c for n, c in cands if c[0] < 0]
    if not left or not right:
        return None
    return left[0], right[0]


def fit_lines(mask, ml, mh):
    L = []
    kl_lo = tuple(min(a, b) for a, b in zip(to_kl(ml), to_kl(mh)))
    kl_hi = tuple(max(a, b) for a, b in zip(to_kl(ml), to_kl(mh)))
    L.append('  in K&L HEAD axes (X up, Y back, Z right; X = y, Y = -z, Z = -x): box %s .. %s; target box %s .. %s' % (
        ['%.2f' % x for x in kl_lo], ['%.2f' % x for x in kl_hi], list(KL_BOX[0]), list(KL_BOX[1])))
    eh = eye_holes(mask)
    if not eh:
        L.append('  no eye holes found (no two symmetric small boundary loops)')
        return L
    a, b = (to_kl(c) for c in eh)
    sep = abs(a[2] - b[2])
    mid = tuple((a[i] + b[i]) / 2 for i in range(3))
    L.append('  eye holes in K&L axes: %s and %s, %.2f apart (K&L eyes: X %.1f Y %.1f Z +-%.1f, %.1f apart)' % (
        ['%.2f' % x for x in a], ['%.2f' % x for x in b], sep, KL_EYE[0], KL_EYE[1], KL_EYE[2], 2 * KL_EYE[2]))
    L.append('  PROPOSAL scale 1.0 (head tops agree: Payday 2 +21.0, K&L +20.9 above the head joint); translation in'
             ' HEAD space (%.2f, %.2f, %.2f) puts the eye-hole centres on the K&L eye line; mask front then at Y %.2f'
             ' (K&L mask box front %.1f); eye-separation scale would be %.2f (not advised: K&L heads are wider)' % (
                 KL_EYE[0] - mid[0], KL_EYE[1] - mid[1], 0.0, kl_lo[1] + (KL_EYE[1] - mid[1]), KL_BOX[0][1], 2 * KL_EYE[2] / sep))
    return L


# ------------------------------------------------------------------ CLI
def pick_objects(model, spec):
    """--objs a,b,c -> those mesh objects (in file order); None -> every mesh object."""
    if not spec:
        return model.mesh_objects()
    want = spec.split(',')
    out = [o for o in model.mesh_objects() if o.name in want]
    missing = set(want) - set(o.name for o in out)
    if missing:
        raise SystemExit('no mesh object named %s (have %s)' % (sorted(missing), [o.name for o in model.mesh_objects()]))
    return out


def textures_opt(spec):
    """--tex <file>  or  --tex g_body=<file>;g_hands=<file>  (.texture / .dds; the top 512 mip is decoded)."""
    if not spec:
        return None
    if '=' not in spec:
        return load_texture(spec)
    return {k: load_texture(v) for k, v in (kv.split('=', 1) for kv in spec.split(';'))}


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    opts = {}
    rest = []
    k = 0
    while k < len(args):
        if args[k].startswith('--'):
            opts[args[k][2:]] = args[k + 1] if k + 1 < len(args) else True
            k += 2
        else:
            rest.append(args[k]); k += 1
    if cmd == 'info':
        print(Model(rest[0]).info())
    elif cmd == 'obj':
        m = Model(rest[0])
        objs = pick_objects(m, opts.get('objs'))
        write_obj(m, rest[1], objs)
        print('%s: %d meshes -> %s' % (rest[0], len(objs), rest[1]))
    elif cmd == 'png':
        m = Model(rest[0])
        lo, hi = render(m, rest[1], textures_opt(opts.get('tex')), int(opts.get('size', 300)), pick_objects(m, opts.get('objs')),
                        up=opts.get('up'))
        print('%s -> %s (view-space box %s .. %s)' % (rest[0], rest[1], ['%.1f' % x for x in lo], ['%.1f' % x for x in hi]))
    elif cmd == 'onhead':
        body, mask = Model(rest[0]), Model(rest[1])
        heads = opts.get('head', 'g_head_dallas').split(',')
        lo, hi = render_on_head(body, mask, rest[2], heads, textures_opt(opts.get('tex')), int(opts.get('size', 300)))
        print('%s + %s on %s -> %s (world box %s .. %s)' % (rest[1], heads, rest[0], rest[2], ['%.1f' % x for x in lo], ['%.1f' % x for x in hi]))
    elif cmd == 'tex':
        d = open(rest[0], 'rb').read()
        i = dds_info(d)
        print('%s: %s' % (rest[0], i))
        if len(rest) > 1:
            open(rest[1], 'wb').write(d)
        if 'png' in opts:
            import kl_view
            r = dds_decode(d, normal=(opts.get('normal') is not None) or (i and i['swizzle'] == 'A2D5'))
            if r:
                kl_view.png(opts['png'], r[0], r[1], r[2])
                print('top mip %dx%d -> %s' % (r[0], r[1], opts['png']))
            else:
                print('format %s not decoded' % (i and i['fourcc']))
    elif cmd == 'scan':
        r = scan(rest[0])
        print(json.dumps(r, indent=1))
    elif cmd == 'head':
        print(head_report(rest[0], rest[1], opts.get('bone', 'Head')))
    elif cmd == 'holes':
        print(holes_report(Model(rest[0]), int(opts.get('min', 4))))
    else:
        print('unknown command', cmd)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
