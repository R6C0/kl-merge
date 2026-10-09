"""
Materials (.MAT) for Dead Men -> Dog Days, and the compiled shader cache (.fxc) container.

The .MAT model, both containers and the canonical writer are in kl_texmat.py (read_mat /
write_mat, byte-identical on every stock archive). convert_mat_full() reads a Dead Men file
into that model, turns every instance into something a stock Dog Days file could hold, and
writes it with the canonical writer (so nothing is appended, no count is stale, and
write_mat(read_mat(out)) == out).

WHAT A DEAD MEN MATERIAL NEEDS (counts: the 21 Dog Days levels and the Dead Men maps M01_FA,
M02_FA, M03_FA, M06_FA, M09_A, M09_B unless said otherwise)

1. Class definition. An instance belongs to a class entry (class name + CLAS{NAME, SUBC{..
   LAYE{PATH, IDEN}}}) that lists, per mesh kind, the effect file and the technique of every
   render pass. Every (class name, CLAS NAME) has ONE tree in all levels of a game, and the two
   games' trees differ: Dead Men's name techniques no Dog Days effect has (PostFilterZPass*,
   ZFill, AmbientSprites*) and lack Dog Days' passes (NormalAndLinearZ, Transparent, ...).
   Each class is therefore replaced by the stock Dog Days tree of the same name, read from the
   installed game (dd_reference). Same name in both games: Old/Bad, Sprites, Standard/Glass,
   Standard/Glow, Standard/SkinCloth, Standard/Standard and the three StaticShadow classes.
   NO Dog Days counterpart (CLASS_MAP, every target a GUESS):
     Standard/Mirror        -> Standard/Standard. Mirror materials are stone FLOORS with a planar
                               reflection; as glass (the old REMAP) they would turn transparent.
                               LOST: the reflection.
     Standard/GlassSurface  -> Standard/Glass. Weapon scope lenses (refraction bubbles).
     ScatterNew/ScatterNew  -> Standard/Standard. Dead Men's scatter objects do not survive the
                               .prm conversion (kl_prm), so these instances end up unused; they
                               only have to be loadable.
   Any other class without a counterpart also falls back to Standard/Standard and is reported.
2. Instance properties (INST/BIND). The engine finds nodes by tag and name (kl2 0x53e610 is
   called with the tag wanted, e.g. 0x826d96 'TXID'), and the lists vary in length inside one
   class, but always in one order. Dog Days lists carry properties Dead Men's lack in EVERY
   instance of the class (Standard/Standard: v4SmearColor, SmoothSmearEnabled, IgnoreDepthFade,
   Shimmer, SSmooth, CensorEnabled, BumpInterpolatedEnabled, StdSamplerState, StdCulling,
   UseDefaultReflectionMap, UsesBoneInstancing). Each instance is rebuilt in the Dog Days
   order of its class: Dead Men's node where it has one, Dog Days' most common node for a
   property every Dog Days instance has, nothing for the optional ones. Properties the Dog Days
   class never has are dropped and reported (gm_vAlphaFade* on Glass, vParallax* / mapParallax
   on SkinCloth, the Mirror / Reflection2D / Refraction2D / Fresnel / Scatter* sets).
   ASSUMPTION: a missing always-present property matters; whether the engine defaults it was
   not read. Node shapes inside a property (RSTA, TEXT, BOOL, ...) and every string value
   (blend mode, culling, tiling) are the same in both games.
3. Entry +0x08 feature flags = 8 * ParallaxEnabled + 16 * BumpEnabled + 64 * BumpInterpolated-
   Enabled, each read from the BOOL of that name (ENAB and VALU set): holds for 12,462 of
   12,462 Dog Days instances. Dead Men only ever sets 8 (12,190 of 12,190). Recomputed.
   ESTABLISHED on the files; what the engine does with the field was not read.
4. Entry +0x18 surface type = row id of the level's surface table (tail of the .buf, .gms
   header +0x30; rows {name, id}, see kl_scene.table_refs). The table is the same in all 21 Dog
   Days levels (24 rows) and in all 20 Dead Men levels (31 rows), and the ids are numbered
   differently: SURFACE_DM / SURFACE_DD below are read from it. Rows of the same name are
   paired by name (ESTABLISHED: 17 pairs, e.g. Concrete 3 -> 4, Metal 9 -> 6, Glass 28 -> 23);
   the 14 Dead Men rows without a namesake use SURFACE_GUESS (GUESS, by meaning).
   That +0x18 is the row id rests on: value range = row count in both games, and material
   folder names agree with row names (Dead Men Concrete/ 3, Stone/ 7, Metal/ 9, Wood/ 13,
   Glass/ 28; Dog Days Concrete/ 4, Stone/ 5, Metal/ 6, Wood/ 11, Glass/ 23).
   THE REMAP IS RIGHT ONLY IF THE LEVEL CARRIES DOG DAYS' SURFACE TABLE (a graft onto a Dog
   Days level does). A level shipped with Dead Men's .buf tail must pass surface=None.
   Counter-evidence kept in view: 5 vehicle materials named alike in both games have Car (27)
   in Dead Men and Metal (6), not Car (2), in Dog Days.
5. Entry +0x0C render group. No table names it; RENDER_GROUP below comes from materials named
   alike in both games (123 names; ESTABLISHED pairs) and from the values the same (class,
   blend mode, alpha test) combination takes in each game (SUPPORTED pairs). Values with
   neither are left as they are and reported. What the engine does with it was not read.
6. Texture stage ids with bit 31 are engine surfaces, not file textures. Dead Men uses
   0x80000000..3 on mapEnvironment, Dog Days only 0x80000000 (2,900 uses). 1..3 are rewritten
   to 0 (ASSUMPTION: they are the level's sampled environment cubes - Dead Men has a ZEnvSampler
   class no Dog Days level uses - so those materials reflect the default map instead).
7. Entry +0x14 (0 Standard, 1 Tweened, 2 Rigid, 3 Weighted; Sprites 1, 3..8) and +0x10 are
   numbered alike in both games and are kept. The ref table (use count per slot) is derived
   from the .prm (kl_texmat.material_refs): pass the CONVERTED .prm so it is recomputed.

.fxc (Dog Days only): [u32 100][u32 count][u32 bytes after header][u32 16] then entries:
0x850-byte header (material class, permutation key, blob size, ..., blob offset at +0x80c,
source shader name at +0x810) followed by a compiled D3D9 effect (fx_2_0) blob.
"""
import collections, hashlib, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FLOAT, STRING, INT, LIST = 0, 1, 2, 3
ENGINE_SLOT = 0x80000000
PARALLAX, BUMP, BUMP_INTERPOLATED = 0x08, 0x10, 0x40
FLAG_BOOLS = (('ParallaxEnabled', PARALLAX), ('BumpEnabled', BUMP), ('BumpInterpolatedEnabled', BUMP_INTERPOLATED))

# Dead Men (class name, CLAS NAME) with no Dog Days class of that name -> the one used. GUESSES.
CLASS_MAP = {
    ('Standard', 'Mirror'): ('Standard', 'Standard'),
    ('Standard', 'GlassSurface'): ('Standard', 'Glass'),
    ('ScatterNew', 'ScatterNew'): ('Standard', 'Standard'),
}
FALLBACK = ('Standard', 'Standard')

# Row names of the surface table (.buf tail), row id = position + 1; the same in every level.
SURFACE_DM = ('Default', 'Seabed', 'Concrete', 'PlantPink', 'Steam', 'Ceramic', 'Stone', 'StoneReflect', 'Metal',
              'Perforated Metal', 'Perforated Stone', 'Grate', 'Wood', 'Grass', 'Soil', 'Mud', 'Flesh', 'Water',
              'WaterDeep', 'Fabric', 'Plastic', 'Rubber', 'Plaster', 'Plant', 'Paper', 'Gravel', 'Car', 'Glass',
              'GlassFloor', 'CarGlass', 'Bricks')
SURFACE_DD = ('Default', 'Car', 'Ceramic', 'Concrete', 'Stone', 'Metal', 'Metal Water', 'Metal Heavy',
              'Metal Perforated', 'Stone Perforated', 'Wood', 'Soil', 'Puddle', 'Flesh', 'Flesh Hero', 'Fabric',
              'Fabric_Red', 'Fabric_Blue', 'Plastic', 'Plaster', 'Plant', 'Paper', 'Glass', 'Glass Skyscraper')
SURFACE_SAME = {'Perforated Metal': 'Metal Perforated', 'Perforated Stone': 'Stone Perforated'}   # same words
SURFACE_GUESS = {                                # Dead Men rows with no Dog Days row of that name: GUESSES
    'Seabed': 'Soil', 'PlantPink': 'Plant', 'Steam': 'Default', 'StoneReflect': 'Stone', 'Grate': 'Metal Perforated',
    'Grass': 'Plant', 'Mud': 'Soil', 'Water': 'Puddle', 'WaterDeep': 'Puddle', 'Rubber': 'Plastic', 'Gravel': 'Soil',
    'GlassFloor': 'Glass', 'CarGlass': 'Glass', 'Bricks': 'Stone',
}

# Entry +0x0C. 'E' = a material of the same name has this pair in both games (number of names),
# 'S' = supported by the values of the same (class, blend mode, alpha test) in both games.
RENDER_GROUP = {
    0: (0, 'E 30'), 7: (7, 'E 1'), 105: (105, 'E 1'), 108: (108, 'E 9'), 110: (110, 'E 8'), 111: (111, 'E 16'),
    119: (119, 'E 1'),
    49: (65, 'E 41'), 52: (68, 'E 8'), 54: (70, 'E 2'), 65: (33, 'E 4'),
    # Dead Men 0x30..0x37 -> + 0x10 (the "on opaque" and alpha-test modes)
    48: (64, 'S'), 50: (66, 'S MUL_ON_OPAQUE'), 51: (67, 'S ADD_ON_OPAQUE'), 53: (69, 'S'), 55: (71, 'S'),
    # Dead Men 0x29..0x2f -> + 0x10
    41: (57, 'S'), 44: (60, 'S TRANS'), 46: (62, 'S SCREEN'), 47: (63, 'S ADD'),
    # Dead Men 0x40 -> 0x20 (opaque skin and cloth: 531 instances at 64 there, 482 at 32 here)
    64: (32, 'S SkinCloth opaque'),
    # Dead Men 0x46 / 0x47 -> 0x56 / 0x57 (alpha-tested hair: 153 at 70 there, 82 at 86 here)
    70: (86, 'S SkinCloth TRANS + alpha test'), 71: (87, 'S'),
    # the same value serves the same blend mode in both games
    1: (1, 'S'), 16: (16, 'S'), 17: (17, 'S'), 19: (19, 'S'), 89: (89, 'S'), 92: (92, 'S'), 95: (95, 'S'),
    103: (103, 'S'), 109: (109, 'S MUL'),
}


# ---------------------------------------------------------------- fxc
FXC_HDR = 0x850
FX_MAGIC = b'\x01\x09\xff\xfe'


def read_fxc(data):
    ver, count, size, hdr = struct.unpack_from('<4I', data, 0)
    o, out = 16, []
    for _ in range(count):
        bs = struct.unpack_from('<I', data, o + 8)[0]
        head = data[o:o + FXC_HDR]
        blob = data[o + FXC_HDR:o + FXC_HDR + bs]
        if blob[:4] != FX_MAGIC:
            raise ValueError('fxc entry without effect blob at %#x' % o)
        out.append((head, blob))
        o += FXC_HDR + bs
    if o != len(data):
        raise ValueError('fxc size mismatch')
    return ver, out


def entry_key(head, blob):
    h = bytearray(head)
    h[0x80c:0x810] = b'\0\0\0\0'                 # absolute offset differs per file
    return hashlib.md5(bytes(h) + blob).hexdigest()


def write_fxc(entries, ver=100):
    out = bytearray(struct.pack('<4I', ver, len(entries), 0, 16))
    for head, blob in entries:
        h = bytearray(head)
        struct.pack_into('<I', h, 0x80c, len(out) + FXC_HDR)
        out += h + blob
    struct.pack_into('<I', out, 8, len(out) - 16)
    return bytes(out)


def entry_info(head):
    kind, key, bs = struct.unpack_from('<3I', head, 0)
    cls = head[12:12 + 64].split(b'\0')[0].decode('latin1')
    shader = head[0x810:0x850].split(b'\0')[0].decode('latin1')
    return cls, key, shader


# ---------------------------------------------------------------- .MAT model helpers
def _name(node, tag='NAME'):
    return next((c[3].decode('latin1') for c in node[3] if c[0] == tag), None)


def _child(node, tag):
    return next((c for c in node[3] if c[0] == tag), None)


def _freeze(node):
    return (node[0], node[1], node[2], tuple(_freeze(x) for x in node[3]) if node[1] == LIST else node[3])


def _thaw(f):
    return [f[0], f[1], f[2], [_thaw(x) for x in f[3]] if f[1] == LIST else f[3]]


def class_key(mat, entry):
    """(class name, CLAS NAME) of a class entry or of an instance's class."""
    c = entry if not entry.f[1] else mat.classes[entry.f[1]]
    return c.cls.decode('latin1'), _name(c.root)


def _bind(entry):
    b = [c for c in entry.root[3] if c[0] == 'BIND']
    if len(b) != 1 or [c[0] for c in entry.root[3]] != ['NAME', 'BIND']:
        raise ValueError('material instance %r is not INST{NAME, BIND}' % entry.name)
    return b[0]


def _keys(bind):
    """[(key, node)] of a BIND list; key = (tag, NAME, occurrence), a property's identity."""
    seen, out = collections.Counter(), []
    for n in bind[3]:
        k = (n[0], _name(n) if n[1] == LIST else None)
        out.append((k + (seen[k],), n)); seen[k] += 1
    return out


def _flag(props, name):
    n = props.get(('BOOL', name, 0))
    if n is None:
        return False
    e, v = _child(n, 'ENAB'), _child(n, 'VALU')
    return bool(e and e[3] and v and v[3])


def feature_flags(entry):
    """Entry +0x08 as the instance's BOOLs imply it (see the docstring, point 3)."""
    props = dict(_keys(_bind(entry)))
    return sum(bit for name, bit in FLAG_BOOLS if _flag(props, name))


def surface_rows(gms_raw, buf):
    """Row names of a level's surface table, row id = position + 1 (unpacked .gms, .buf)."""
    off = struct.unpack_from('<I', gms_raw, 0x30)[0]
    rows, _cols, _arrs, _size, strings, _data = struct.unpack_from('<6I', buf, off)
    n = struct.unpack_from('<I', buf, off + strings)[0]
    names = [buf[off + o:buf.index(b'\0', off + o)].decode('latin1') for o in struct.unpack_from('<%dI' % n, buf, off + strings + 4)]
    out = {}
    for k in range(struct.unpack_from('<I', buf, off + rows)[0]):
        name, ident = struct.unpack_from('<II', buf, off + rows + 4 + 8 * k)
        out[ident] = names[name]
    if sorted(out) != list(range(1, len(out) + 1)):
        raise ValueError('surface table ids are not 1..n')
    return tuple(out[i] for i in range(1, len(out) + 1))


def surface_map(dm_rows=SURFACE_DM, dd_rows=SURFACE_DD):
    """{Dead Men surface id: (Dog Days surface id, 'E' same row name | 'G' guess)}."""
    dd = {name: i for i, name in enumerate(dd_rows, 1)}
    out = {}
    for i, name in enumerate(dm_rows, 1):
        same = SURFACE_SAME.get(name, name)
        if same in dd:
            out[i] = (dd[same], 'E')
        else:
            out[i] = (dd[SURFACE_GUESS.get(name, 'Default')], 'G')
    return out


# ---------------------------------------------------------------- Dog Days reference
class Reference:
    """What stock Dog Days materials look like. classes: {(class name, CLAS NAME): frozen CLAS
    tree}; order: {class: [key ...]} the one order all its instances' properties follow;
    always: {class: {key: frozen node}} properties every instance of the class has, with their
    most common node; groups / surfaces: the +0x0C / +0x18 values that occur; strings:
    {(property tag, child tag): values}."""

    def __init__(self):
        self.classes, self.order, self.always, self.count = {}, {}, {}, collections.Counter()
        self.groups, self.surfaces, self.strings = set(), set(), collections.defaultdict(set)
        self.subtypes = collections.defaultdict(set)
        self._seqs = collections.defaultdict(collections.Counter)
        self._nodes = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))

    def add(self, mat):
        if mat.wide:
            raise ValueError('a Dead Men .MAT cannot serve as Dog Days reference')
        for e in mat.classes.values():
            k = class_key(mat, e)
            f = _freeze(e.root)
            if self.classes.setdefault(k, f) != f:
                raise ValueError('Dog Days class %s/%s has two different trees' % k)
        for e in mat.insts.values():
            k = class_key(mat, e)
            self.count[k] += 1
            self.groups.add(e.f[3]); self.surfaces.add(e.f[6]); self.subtypes[k].add(e.f[5])
            ks = _keys(_bind(e))
            self._seqs[k][tuple(key for key, _n in ks)] += 1
            for key, n in ks:
                self._nodes[k][key][_freeze(n)] += 1
                if n[1] == LIST:
                    for c in n[3]:
                        if c[1] == STRING and c[0] != 'NAME':
                            self.strings[(n[0], c[0])].add(c[3])

    def finish(self):
        for k, seqs in self._seqs.items():
            # one total order: every sequence must be a subsequence of it
            after, keys = collections.defaultdict(set), []
            for seq, _c in seqs.most_common():
                for a, b in zip(seq, seq[1:]):
                    after[a].add(b)
                keys += [x for x in seq if x not in keys]
            order, left = [], list(keys)
            while left:
                free = [x for x in left if not any(x in after[y] for y in left if y != x)]
                if not free:
                    raise ValueError('Dog Days %s/%s instances do not agree on a property order' % k)
                order.append(free[0]); left.remove(free[0])
            pos = {x: i for i, x in enumerate(order)}
            if any(list(seq) != sorted(seq, key=pos.get) for seq in seqs):
                raise ValueError('Dog Days %s/%s: a property list is out of order' % k)
            self.order[k] = order
            self.always[k] = {key: nodes.most_common(1)[0][0] for key, nodes in self._nodes[k].items()
                              if sum(nodes.values()) == self.count[k]}
        return self


_REFERENCE = {}


def dd_reference(dd=None):
    """Reference built from every stock Dog Days level under `dd` (default: the installed game;
    KL_PortBackup originals are preferred over a slot we installed into). About 20 s."""
    import zipfile
    import kl_texmat as TM
    from kl_port_check import find, level_zips, DD_GUESSES, DD_EXE
    dd = dd or find(DD_GUESSES, DD_EXE)
    if dd not in _REFERENCE:
        ref = Reference()
        for z in sorted(level_zips(dd)):
            if not z.endswith('_Main.zip'):
                continue
            with zipfile.ZipFile(z) as zf:
                for n in zf.namelist():
                    if n.lower().endswith('_main.mat'):
                        ref.add(TM.read_mat(zf.read(n)))
        if not ref.classes:
            raise ValueError('no stock Dog Days .MAT found under %r' % dd)
        _REFERENCE[dd] = ref.finish()
    return _REFERENCE[dd]


# ---------------------------------------------------------------- conversion
def convert_mat_full(data, ref=None, prm=None, surface='dd', texture_ids=None):
    """Dead Men .MAT -> Dog Days .MAT; instance slots keep their numbers.
    ref: Reference (default dd_reference()). prm: the CONVERTED .prm of the level; with it the
    ref table is recomputed, and an instance of a class dropped for want of a counterpart
    must then be unused or it is reported in `misused`. surface: 'dd' = renumber +0x18 for a
    level that carries Dog Days' surface table, None = leave Dead Men's numbers.
    texture_ids: ids the level's .TEX has; a TXID outside it raises.
    Returns (bytes, report); report: instances, classes {Dead Men class: Dog Days class},
    no_counterpart [Dead Men classes mapped by guess], added / dropped {(class, property): n},
    bump (instances that gained the bump bit), surface / surface_guess / group / group_unmapped
    {(old, new): n}, group_not_in_dd {value: n} (render groups written that no stock Dog Days
    material has), engine_slots {old: n}, misused [slots], refs_changed."""
    import kl_texmat as TM
    src = TM.read_mat(data)
    if not src.wide:
        raise ValueError('not a Dead Men .MAT (12-byte nodes)')
    ref = ref or dd_reference()
    smap = surface_map() if surface == 'dd' else None
    out = TM.Mat(False, src.ncls, src.ninst)
    rep = dict(instances=len(src.insts), classes={}, no_counterpart=[], added=collections.Counter(),
               dropped=collections.Counter(), bump=0, surface=collections.Counter(), surface_guess=collections.Counter(),
               group=collections.Counter(), group_unmapped=collections.Counter(), group_not_in_dd=collections.Counter(),
               engine_slots=collections.Counter(),
               misused=[], refs_changed=0)
    slot_of, guessed = {}, set()
    for slot in sorted(src.insts):
        e = src.insts[slot]
        old = class_key(src, e)
        new = old if old in ref.classes else CLASS_MAP.get(old, FALLBACK)
        if new not in ref.classes:
            raise ValueError('Dog Days reference has no class %s/%s' % new)
        if old not in ref.classes:
            guessed.add(slot)
            if old not in rep['no_counterpart']:
                rep['no_counterpart'].append(old)
        rep['classes']['%s/%s' % old] = '%s/%s' % new
        if new not in slot_of:
            slot_of[new] = len(slot_of) + 1
            out.classes[slot_of[new]] = TM.Entry(new[0].encode('latin1'), [0] * 12, _thaw(ref.classes[new]))
        # properties in Dog Days' order
        have = dict(_keys(_bind(e)))
        bind = []
        for key in ref.order[new]:
            if key in have:
                bind.append(_thaw(_freeze(have.pop(key))))
            elif key in ref.always[new]:
                bind.append(_thaw(ref.always[new][key])); rep['added'][(new[1], key[1])] += 1
        for key in have:
            rep['dropped'][(old[1], key[1] or key[0])] += 1
        for n in bind:
            if n[1] != LIST:
                continue
            for c in n[3]:
                if c[0] == 'TXID':
                    if c[3] & ENGINE_SLOT:
                        if c[3] != ENGINE_SLOT:
                            rep['engine_slots'][c[3]] += 1; c[3] = ENGINE_SLOT
                    elif c[3] and texture_ids is not None and c[3] not in texture_ids:
                        raise ValueError('material %d (%s): texture %d is not in the .TEX' % (slot, e.name, c[3]))
                elif c[1] == STRING and c[0] != 'NAME' and c[3] not in ref.strings[(n[0], c[0])]:
                    raise ValueError('material %d (%s): %s/%s value %r never occurs in Dog Days' % (slot, e.name, n[0], c[0], c[3]))
        f = list(e.f)
        f[1] = slot_of[new]
        x = TM.Entry(new[0].encode('latin1'), f, [e.root[0], LIST, 2, [_thaw(_freeze(_child(e.root, 'NAME'))), ['BIND', LIST, len(bind), bind]]])
        flags = feature_flags(x)
        if f[2] & ~(PARALLAX | BUMP | BUMP_INTERPOLATED) or (f[2] & PARALLAX) != (flags & PARALLAX):
            raise ValueError('material %d (%s): feature flags %#x do not follow its switches' % (slot, e.name, f[2]))
        rep['bump'] += bool(flags & BUMP) and not f[2] & BUMP
        f[2] = flags
        if f[3] in RENDER_GROUP:
            g = RENDER_GROUP[f[3]][0]
            if g != f[3]:
                rep['group'][(f[3], g)] += 1
            f[3] = g
        else:
            rep['group_unmapped'][(f[3], f[3])] += 1
        if f[3] not in ref.groups:
            rep['group_not_in_dd'][f[3]] += 1
        if smap is not None:
            if f[6] not in smap:
                raise ValueError('material %d (%s): surface type %d is not a row of Dead Men\'s table' % (slot, e.name, f[6]))
            s, how = smap[f[6]]
            rep['surface' if how == 'E' else 'surface_guess'][(f[6], s)] += 1
            f[6] = s
        if f[5] not in ref.subtypes[new]:
            raise ValueError('material %d (%s): mesh kind %d never occurs with class %s/%s' % ((slot, e.name, f[5]) + new))
        out.insts[slot] = x
    out.refs = list(src.refs)
    if prm is not None:
        out.refs = TM.material_refs(prm, out.ninst)
        rep['refs_changed'] = sum(a != b for a, b in zip(out.refs, src.refs))
        rep['misused'] = [s for s in sorted(guessed) if out.refs[s] and class_key(src, src.insts[s]) == ('ScatterNew', 'ScatterNew')]
        used = [s for s, n in enumerate(out.refs) if n and s not in out.insts]
        if used:
            raise ValueError('the .prm uses material slots the .MAT does not have: %r' % used[:8])
    result = TM.write_mat(out)
    check(result, ref)
    return result, rep


def check(dd_data, ref=None):
    """A converted .MAT must be canonical and hold nothing stock Dog Days files do not: the
    file is what the canonical writer makes of it, every class tree is a stock tree, every
    instance's properties are properties of its class in the class's order with every
    always-present one there, +0x08 follows the switches, strings are known values and no engine
    texture slot but 0 is named. Returns (instances, classes)."""
    import kl_texmat as TM
    ref = ref or dd_reference()
    m = TM.read_mat(dd_data)
    if m.wide or TM.write_mat(m) != dd_data:
        raise ValueError('.MAT is not in canonical Dog Days form')
    if len(dd_data) != struct.unpack_from('<I', dd_data, 12)[0] + 4 * m.ninst:
        raise ValueError('.MAT does not end with its ref table')
    for s, e in m.classes.items():
        k = class_key(m, e)
        if ref.classes.get(k) != _freeze(e.root):
            raise ValueError('class slot %d (%s/%s) is not a stock Dog Days class tree' % ((s,) + k))
    for s, e in m.insts.items():
        k = class_key(m, e)
        if e.cls.decode('latin1') != k[0]:
            raise ValueError('material %d: class name differs from its class entry' % s)
        keys = [key for key, _n in _keys(_bind(e))]
        pos = {x: i for i, x in enumerate(ref.order[k])}
        if any(x not in pos for x in keys) or keys != sorted(keys, key=pos.get) or any(x not in keys for x in ref.always[k]):
            raise ValueError('material %d (%s): property list does not fit Dog Days class %s/%s' % ((s, e.name) + k))
        if e.f[2] != feature_flags(e):
            raise ValueError('material %d (%s): feature flags' % (s, e.name))
        for n in _bind(e)[3]:
            for c in (n[3] if n[1] == LIST else ()):
                if c[0] == 'TXID' and c[3] & ENGINE_SLOT and c[3] != ENGINE_SLOT:
                    raise ValueError('material %d (%s): engine texture slot %#x' % (s, e.name, c[3]))
                if c[1] == STRING and c[0] != 'NAME' and c[3] not in ref.strings[(n[0], c[0])]:
                    raise ValueError('material %d (%s): %s/%s value %r' % (s, e.name, n[0], c[0], c[3]))
    return len(m.insts), len(m.classes)
