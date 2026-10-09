"""
Kane & Lynch .prm as a graph of chunks: read / write, walk, extract, append (both games).

CONTAINER (41/41 stock levels, 21 Dog Days + 20 Dead Men, rewrite byte-identical): chunk 0 is the
16-byte header [table ofs][count][table ofs][0]; chunks follow in index order, every size a
multiple of 16, no gaps; the table (count x [ofs, size, refcount, 0]) ends the file. Every
"pointer" in the file is a chunk index, 0 = none; the engine keeps a pointer per index in a
global table (kl2 0xeac7b0, 429 code sites, e.g. 0x6ad0db), so nothing is fixed up at load and
a chunk can be moved if every index naming it is rewritten.
The table's refcount is NOT the number of references in the file (it also counts copies the
build tool merged; a root used by 20 entities has 1): it is kept per chunk and never recomputed.

WHO POINTS INTO THE FILE (the roots; none of them is found by size)
  .gms record +0x0c            lType 7 model root, lType 2 sprite (ZParticleTemplate) or lType 12
                               light. Equal to the .prp ZGEOM field below in 378,122/378,122
                               non-zero cases, so both must be renumbered together.
  .prp fields (PRP_FIELDS)     ZGEOM 4 (= the .gms field), ZWINPIC 2, ZTTFONT 0, ZCloth 15 (Dead
                               Men 14), ZPlant 2, ZPostFilterEvent 0, ZPostFilterSetEvent 4,
                               ZParticleTemplate 25, ZParticleBox 5, ZCutSequencePostFilter-
                               CollectionEvent 0. Record numbers are positions in the owner
                               class's own list (kl_rtp field key). Found by taking every integer
                               field of every object of the 41 levels and keeping those whose
                               non-zero values are all chunks of one kind (100% each).
  .prp scene block             PostFilterPalettes, PostFilterBoxes (one chunk index each).
  .oct tail {a, b} pairs       b = index of a mesh chunk the walk reaches, in 656,821/656,821
                               pairs of the 41 levels (a is a multiple of 32, not a chunk).
The .gms roots alone reach 92.8% of the Dog Days chunks (517,107 of 557,085) and 93.5% of the
Dead Men ones (529,365 of 566,046); with the .prp roots 99.991% (all but 50) and 99.16% (all
but 4,766). Every chunk left over is a dead model root or hangs under one: see orphans().

CHUNK KINDS (kind: size; fields; references. c = chunk index u32, m = material u16,
t = texture id u32, o = .oct reference)
  root     64   lType 7 at +2 (header 00 01 07 00); +0x0c flags (bit 0 = has skeleton),
                +0x10 c prop, +0x14 object count, +0x18 c objtab, +0x1c o = (offset of an
                octree record in the .oct + 4) | 1 or 0 (kl2 0x6ad0f9: type 7 -> +0x1c, bit 0 ->
                add the .oct base). The 29,845 + 35,495 octree records of the 41 levels are each
                named by exactly one reached root and no root names anything else. +0x20 bounds, +0x38 c rootx (32 bytes, two 4-float rows),
                +0x3c c inst (per-instance vertex colours; the build clones the root for it)
  prop     16   4 slots: [1] c skel, [2] c prop2 (Dead Men, 5 chunks); [0] and [3] never set
  skel     80   20 dwords: [0] bone count, [1..11], [13], [18], [19] c (bone definitions 64 B
                per bone, bind matrices 48 B per bone, ...), [12], [14..17] numbers.
                [11] c face (32 B: +0 c, +4 c, +0xc c; characters only)
  objtab        root.count x c object
  mesh     64 / 128 (static shadow)  lType 8; +0x0c subtype, +0x12 m, +0x1c draw mode,
                +0x28 c subtab, +0x38 / +0x3c copy bones: subtype 3 -> count and c bones,
                subtype 2 -> a bone number (not a chunk)
  subtab        c desc ..., 0-terminated (always one entry in stock levels)
  desc     Dog Days 48: [0] vertex count, [1] c vtx, [5] a number, [6] c idx, rest 0
           Dead Men 32: [0] vertex count, [1] c vtx, [2] a number, [3] c idx,
                        [4] c lit (8 bytes per vertex), [5] c lit5 (16 bytes, shared), rest 0
           The number is not the index count and not a chunk (24 vertices, 36 indices -> 15;
           larger than the chunk count in 12 Dead Men descriptors); meaning not established.
  scatter  lType 9. Dead Men 256: +0x12 m, +0xd0, +0xe4, +0xe8 c.
           Dog Days 144: +0x12 m, +0x5c u16 instance count; the instances (28 bytes each) are
           the NEXT chunk (index + 1) in 44/44 objects and nothing in the level archive holds
           that index. ASSUMPTION: the engine takes "object index + 1" (not located in kl2.exe),
           so the pair is kept adjacent: see GLUE.
  water    lType 11, 176 (Dead Men, 5 chunks): +0x12 m, otherwise opaque
  sprite   32   lType 2; +0x04 t (occupied slot of the level's .TEX table 1 in 50,701/50,742,
                the rest 0)
  light    48 / 64 / 80  lType 12; no references
  winpic        u32 n, n x 40 bytes, u32 n, n x c sprite, n x 12 bytes (64/128/176/240/352 B)
  font          +0x10 glyph count, glyphs from +0x28, 32 bytes each (Dead Men 20): +0 character,
                +4 texture id + number of .TEX slots (4096 Dog Days, 2048 Dead Men) for text
                glyphs, the plain texture id for characters from 0xe000 (button pictures); an
                occupied .TEX slot in 88,818/88,818 glyphs of the 268 fonts
  pflist        u32 n, n x c pf (0 allowed)
  pfboxes       88-byte records, +0x30 c pf
  pf       176  post-filter set. Its u16 values at +0x64.. index the scene's PostFilterPalettes
                blob (not decoded): sets of two levels cannot share one palette blob
  pfpal, cloth, plant, vtx, idx, lit, lit5, bones, inst, rootx, prop2, skelN, faceN, scatN:
                no chunk index found inside (tests: values pointing at chunks nothing else
                reaches, and values within 200 below the chunk's own index, over all 41 levels).
                cloth, plant and pfpal are opaque blobs.
MATERIAL id = slot in the .MAT instance table (header +4, 2048 slots): occupied for every one of
the 199,856 reached objects of the 41 levels. The .MAT table at header +0xc holds a use count
per slot: equal to the number of reached objects in 20,074 of 24,652 occupied slots, greater in
the rest (never smaller), so it counts more than this file shows; a join should add the two
levels' counts. No chunk holds an entity REF id.

DEAD MEN vs DOG DAYS: desc 32 vs 48 bytes (Dog Days [5] = Dead Men [2]); Dead Men lit meshes
(desc [4] and [5] set together, 26,705 descriptors; their mesh has draw-mode bit 0x01000000 in
26,718/26,718 cases, a bit no Dog Days mesh has) are reached by the walk like any other desc -
it finds all 91,960, kl_prm.find_descriptors 65,255; scatter 256 vs 144 bytes with unrelated
content; font glyphs 20 vs 32 bytes and texture bias 2048 vs 4096; prop slot 2 and water
objects only in Dead Men. append() refuses to mix the games: convert first.

THE NUMBER OF CHUNKS IS LIMITED (re/prm_limit.md; kl_impact.chunk_limit): the pointer table at kl2
0xeac7b0 has 0x12000 = 73,728 four-byte slots, shared with the chunks the game makes while it
runs, and no loader tests the count. So a joined level must not simply grow at the end:
  reuse(p, live, keep)   every chunk no live root reaches (S's removed map: 27,000 of 65,000 in a
                         grafted level) becomes a 16-byte stub and its INDEX is handed out again by
                         new_chunk() / append() before any index is added at the end. Nothing that
                         is live moves, so no reference outside the new sub-graphs changes.
  compact(p, live)       the file renumbered with the dead chunks dropped (= extract of the live
                         closure): every holder of a chunk index must then be rewritten - see
                         kl_chars.compact_level, which does it for the holders this file knows.
"live" is what the level's own files name: level_roots() (the same set as kl_graft.live_roots,
without kl_graft's build machinery) plus the model roots NO entity names - the wardrobe's, listed
in KLWardrobe.ini beside the archive (kl_chars.wardrobe_roots).
"""
import struct

SLOTS = {'dd': 4096, 'dm': 2048}                     # .TEX table size = font texture bias
GLYPH = {'dd': 32, 'dm': 20}
SKEL = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 18, 19)
BY_TYPE = {7: 'root', 2: 'sprite', 12: 'light'}      # what a .gms / ZGEOM index may name
OBJECT = {8: 'mesh', 9: 'scatter', 11: 'water'}
GLUE = {('dd', 'scatter'): 'scatinst'}               # kinds whose next chunk belongs to them
# kinds that hold references; every other kind is plain data, and one data chunk may serve two
# purposes (a one-bone skeleton uses the same matrix chunk as skel2 and skel3)
STRUCT = {'root', 'prop', 'skel', 'face', 'objtab', 'mesh', 'subtab', 'desc', 'scatter', 'water',
          'sprite', 'winpic', 'font', 'pflist', 'pfboxes'}
# .prp fields holding a chunk index: owner class, record number in its own list -> kind
PRP_FIELDS = {('ZGEOM', 4): None, ('ZWINPIC', 2): 'winpic', ('ZTTFONT', 0): 'font',
              ('ZPlant', 2): 'plant', ('ZPostFilterEvent', 0): 'pf', ('ZPostFilterSetEvent', 4): 'pf',
              ('ZParticleTemplate', 25): 'sprite', ('ZParticleBox', 5): 'sprite',
              ('ZCutSequencePostFilterCollectionEvent', 0): 'pflist'}
PRP_GAME = {'dd': {('ZCloth', 15): 'cloth'}, 'dm': {('ZCloth', 14): 'cloth'}}
PRP_SCENE = {'PostFilterPalettes': 'pfpal', 'PostFilterBoxes': 'pfboxes'}


class Prm:
    """chunks[i] = bytes of chunk i (chunks[0] is None: the header), refs[i] = its refcount."""

    def __init__(self, game, chunks, refs):
        self.game, self.chunks, self.refs = game, chunks, refs
        self.free = []                                # indices new_chunk() may fill: set by reuse()

    def u32(self, i, o):
        return struct.unpack_from('<I', self.chunks[i], o)[0]

    def u16(self, i, o):
        return struct.unpack_from('<H', self.chunks[i], o)[0]


def read(data, game=None):
    """game: 'dd' or 'dm'; None = decided by the first mesh descriptor the table holds a
    48- or 32-byte candidate for (only the font and scatter rules depend on it)."""
    t, n, t2, z = struct.unpack_from('<4I', data, 0)
    if t != t2 or z or t + 16 * n != len(data):
        raise ValueError('not a .prm chunk table')
    table = [struct.unpack_from('<4I', data, t + 16 * i) for i in range(n)]
    if table[0][:2] != (0, 16) or any(e[3] for e in table):
        raise ValueError('unexpected .prm table entry')
    p = Prm(game, [None] + [data[o:o + s] for o, s, _r, _z in table[1:]], [e[2] for e in table])
    if game is None:
        p.game = _guess(p)
    return p


def _guess(p):
    for i in range(1, len(p.chunks)):                 # first model root -> its first descriptor
        c = p.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and 0 < p.u32(i, 0x18) < len(p.chunks):
            o = p.u32(p.u32(i, 0x18), 0)
            if 0 < o < len(p.chunks) and p.u16(o, 2) == 8:
                return 'dm' if len(p.chunks[p.u32(p.u32(o, 0x28), 0)]) == 32 else 'dd'
    return 'dd'


def write(p):
    body, table = bytearray(16), [(0, 16, p.refs[0], 0)]
    for c, r in zip(p.chunks[1:], p.refs[1:]):
        if len(c) % 16:
            raise ValueError('chunk size %d is not a multiple of 16' % len(c))
        table.append((len(body), len(c), r, 0))
        body += c
    struct.pack_into('<4I', body, 0, len(body), len(table), len(body), 0)
    return bytes(body) + b''.join(struct.pack('<4I', *e) for e in table)


def fields(p, i, kind, arg=0):
    """Every reference chunk i holds, given its kind: [(offset, type, kind of the target)].
    type 'c' chunk index (u32), 'm' material id (u16), 't' texture id (u32), 'T' texture id,
    with or without the .TEX slot count added (u32), 'o' .oct reference (u32, (offset + 4) | 1)."""
    c, out = p.chunks[i], []
    n32 = len(c) // 4
    if kind == 'root':
        if c[2:4] != b'\7\0':
            raise ValueError('chunk %d is used as a model root but is not lType 7' % i)
        out = [(0x10, 'c', 'prop'), (0x18, 'c', ('objtab', p.u32(i, 0x14))), (0x38, 'c', 'rootx'), (0x3c, 'c', 'inst')]
        if p.u32(i, 0x1c):
            out.append((0x1c, 'o', None))
    elif kind == 'prop':
        out = [(4, 'c', 'skel'), (8, 'c', 'prop2')]
    elif kind == 'skel':
        out = [(4 * s, 'c', 'face' if s == 11 else 'skel%d' % s) for s in SKEL]
    elif kind == 'face':
        out = [(0, 'c', 'face0'), (4, 'c', 'face1'), (12, 'c', 'face3')]
    elif kind == 'objtab':
        for k in range(arg):
            t = p.u16(p.u32(i, 4 * k), 2)
            if t not in OBJECT:
                raise ValueError('object table %d: entry %d has unknown lType %d' % (i, k, t))
            out.append((4 * k, 'c', OBJECT[t]))
    elif kind == 'mesh':
        out = [(0x12, 'm', None), (0x28, 'c', 'subtab')]
        if len(c) == 64 and c[0x0c] == 3:
            out.append((0x3c, 'c', 'bones'))
    elif kind == 'subtab':
        for k in range(n32):
            if not p.u32(i, 4 * k):
                break
            out.append((4 * k, 'c', 'desc'))
    elif kind == 'desc':
        if len(c) == 48:
            out = [(4, 'c', 'vtx'), (0x18, 'c', 'idx')]
        elif len(c) == 32:
            out = [(4, 'c', 'vtx'), (0x0c, 'c', 'idx'), (0x10, 'c', 'lit'), (0x14, 'c', 'lit5')]
        else:
            raise ValueError('mesh descriptor %d is %d bytes' % (i, len(c)))
    elif kind == 'scatter':
        out = [(0x12, 'm', None)]
        if len(c) == 256:
            out += [(0xd0, 'c', 'scat0'), (0xe4, 'c', 'scat1'), (0xe8, 'c', 'scat2')]
        elif len(c) != 144:
            raise ValueError('scatter object %d is %d bytes' % (i, len(c)))
    elif kind == 'water':
        out = [(0x12, 'm', None)]
    elif kind == 'sprite':
        if c[2:4] != b'\2\0':
            raise ValueError('chunk %d is used as a sprite but is not lType 2' % i)
        out = [(4, 't', None)]
    elif kind == 'winpic':
        n = p.u32(i, 0)
        out = [(8 + 40 * n + 4 * k, 'c', 'sprite') for k in range(n)]
    elif kind == 'font':
        g = GLYPH[p.game]
        out = [(0x2c + g * k, 'T', None) for k in range(p.u32(i, 0x10)) if p.u32(i, 0x2c + g * k)]
    elif kind == 'pflist':
        out = [(4 + 4 * k, 'c', 'pf') for k in range(p.u32(i, 0))]
    elif kind == 'pfboxes':
        out = [(48 + 88 * k, 'c', 'pf') for k in range(len(c) // 88)]
    return [f for f in out if f[1] != 'c' or p.u32(i, f[0])]


def _roots(p, roots):
    for r in roots:
        i, kind = (r, None) if isinstance(r, int) else (r[0], r[1])
        if not 0 < i < len(p.chunks):
            if i:
                raise ValueError('root %d is not a chunk' % i)
            continue
        if kind is None:
            kind = BY_TYPE.get(p.u16(i, 2))
            if kind is None:
                raise ValueError('root %d: lType %d is not a model, sprite or light' % (i, p.u16(i, 2)))
        yield i, kind


def walk(p, roots):
    """roots: chunk indices (.gms / ZGEOM: kind from the lType word) or (index, kind) pairs
    (prp_roots). Returns ({chunk: kind}, {chunk: argument}) for everything reachable; a chunk
    reached as two different kinds is an error unless both are plain data (the first name is
    kept). An object table's argument is its entry count."""
    kinds, args, todo = {}, {}, []

    def reach(i, kind):
        kind, arg = kind if isinstance(kind, tuple) else (kind, 0)
        if not 0 < i < len(p.chunks):
            raise ValueError('reference to chunk %d (%s) outside the file' % (i, kind))
        if i in kinds:
            if (kinds[i] != kind or args.get(i, 0) != arg) and (kind in STRUCT or kinds[i] in STRUCT):
                raise ValueError('chunk %d is reached as %s and as %s' % (i, kinds[i], kind))
            return
        kinds[i] = kind
        if arg:
            args[i] = arg
        todo.append(i)

    for i, kind in _roots(p, roots):
        reach(i, kind)
    while todo:
        i = todo.pop()
        for off, typ, kind in fields(p, i, kinds[i], args.get(i, 0)):
            if typ == 'c':
                reach(p.u32(i, off), kind)
        glue = GLUE.get((p.game, kinds[i]))
        if glue:
            reach(i + 1, glue)
    return kinds, args


def closure(p, roots):
    """Set of chunks reachable from the roots."""
    return set(walk(p, roots)[0])


def orphans(p, kinds):
    """Chunks the roots do not reach, explained where possible: {chunk: label}.
    'dead root': an unreached chunk shaped like a model root (64 bytes, 00 01 07 00, a valid
    object table) and 'dead:<kind>' what only it reaches. 44 of the 45 in Dog Days and 482 of
    the 787 in Dead Men are the original of a root the build cloned to hang per-instance colours
    on (same bytes up to +0x38, content shared with the clone); the other 306 own a whole model
    (Dog Days F08 1; Dead Men story levels M03_B, M05_A, M08_A, M09_B, M11_B, M13_A; no FA map).
    None has an .oct reference and no consistent field of .gms / .prp / .buf names them.
    ASSUMPTION: they are dead data. This is a shape test, used for reporting only; in all 41
    levels it labels every unreached chunk (no 'unknown')."""
    out, n = {}, len(p.chunks)
    dead = [i for i in range(1, n) if i not in kinds and len(p.chunks[i]) == 64 and p.chunks[i][:4] == b'\0\1\7\0'
            and 0 < p.u32(i, 0x18) < n and len(p.chunks[p.u32(i, 0x18)]) >= 4 * p.u32(i, 0x14)]
    try:
        k2 = walk(p, [(i, 'root') for i in dead])[0]
    except ValueError:
        k2 = {i: 'root' for i in dead}
    for i in range(1, n):
        if i not in kinds:
            out[i] = ('dead root' if k2[i] == 'root' else 'dead:' + k2[i]) if i in k2 else 'unknown'
    return out


def _pack(c, off, fmt, v):
    return c[:off] + struct.pack(fmt, v) + c[off + struct.calcsize(fmt):]


def _lookup(m, v, what):
    if m is None:
        return v
    r = m(v) if callable(m) else m.get(v)
    if r is None:
        raise KeyError('%s %d has no entry in the map' % (what, v))
    return r


def remap(p, kinds, args, cmap, material_map=None, oct_offset_map=None, texture_map=None):
    """Chunks of `cmap` (old index -> new index) with every reference rewritten; returns
    {old index: new bytes}. The maps (dict or function, None = unchanged): material id -> id,
    texture id -> id, .oct octree record offset -> offset."""
    out, bias = {}, SLOTS[p.game]
    for i in cmap:
        c = p.chunks[i]
        for off, typ, _k in fields(p, i, kinds[i], args.get(i, 0)):
            if typ == 'c':
                c = _pack(c, off, '<I', cmap[p.u32(i, off)])
            elif typ == 'm':
                c = _pack(c, off, '<H', _lookup(material_map, p.u16(i, off), 'material'))
            elif typ == 't' and p.u32(i, off):
                c = _pack(c, off, '<I', _lookup(texture_map, p.u32(i, off), 'texture'))
            elif typ == 'T':
                v = p.u32(i, off)
                c = _pack(c, off, '<I', _lookup(texture_map, v % bias, 'texture') + v - v % bias)
            elif typ == 'o':
                v = p.u32(i, off)
                if not v & 1:
                    raise ValueError('root %d: .oct reference %#x without the offset bit' % (i, v))
                c = _pack(c, off, '<I', (_lookup(oct_offset_map, (v & ~1) - 4, '.oct record') + 4) | 1)
        out[i] = c
    return out


def extract(p, roots, order=None):
    """A self-contained file holding the closure of the roots.
    order: the closure's chunks in the order wanted (default: ascending, the original order).
    A glued chunk (GLUE) must directly follow its owner. Returns (Prm, {old index: new index});
    external references (materials, textures, .oct offsets) are left as they are."""
    kinds, args = walk(p, roots)
    order = sorted(kinds) if order is None else list(order)
    if set(order) != set(kinds) or len(order) != len(kinds):
        raise ValueError('order is not a permutation of the closure')
    cmap = {old: new for new, old in enumerate(order, 1)}
    for i, k in kinds.items():
        if GLUE.get((p.game, k)) and cmap[i + 1] != cmap[i] + 1:
            raise ValueError('chunk %d must directly follow its %s %d' % (i + 1, k, i))
    new = remap(p, kinds, args, cmap)
    return Prm(p.game, [None] + [new[i] for i in order], [p.refs[0]] + [p.refs[i] for i in order]), cmap


def append(a, b, b_roots, material_map=None, oct_offset_map=None, texture_map=None):
    """a + the closure of b_roots in b (original order), every chunk index of the appended part
    renumbered and its materials / textures / .oct offsets sent through the maps. Returns
    (Prm, {index in b: index in the result}); look the old roots up in it. Nothing is merged
    with equal chunks of a. Both files must be of the same game.
    The new chunks take a's free indices first (a.free, see reuse(); lowest first, in b's order)
    and only then new indices at the end; a chunk glued to its neighbour (GLUE) always goes to
    the end, with it. Nothing of a moves. The result carries the free indices left over."""
    if a.game != b.game:
        raise ValueError('cannot append a %s file to a %s file: convert it first' % (b.game, a.game))
    kinds, args = walk(b, b_roots)
    order = sorted(kinds)
    glued = {j for i, k in kinds.items() if GLUE.get((b.game, k)) for j in (i, i + 1)}
    free, cmap, end = list(a.free), {}, len(a.chunks)
    for old in order:
        if free and old not in glued:
            cmap[old] = free.pop()
        else:
            cmap[old] = end; end += 1
    new = remap(b, kinds, args, cmap, material_map, oct_offset_map, texture_map)
    chunks, refs = a.chunks + [None] * (end - len(a.chunks)), a.refs + [0] * (end - len(a.chunks))
    for old in order:
        chunks[cmap[old]], refs[cmap[old]] = new[old], b.refs[old]
    out = Prm(a.game, chunks, refs)
    out.free = free
    return out, cmap


def new_chunk(p, data, ref=1):
    """Index of a new chunk holding `data`: the lowest free index (reuse()) when there is one,
    else a new one at the end. Every writer of a new chunk goes through here (kl_chars, kl_impact)."""
    data = bytes(data)
    if len(data) % 16:
        raise ValueError('chunk size %d is not a multiple of 16' % len(data))
    if p.free:
        i = p.free.pop()
        p.chunks[i], p.refs[i] = data, ref
        return i
    p.chunks.append(data); p.refs.append(ref)
    return len(p.chunks) - 1


def reuse(p, live, keep=()):
    """Make the indices of the dead chunks available: every chunk that no root of `live` reaches
    and `keep` does not hold becomes a 16-byte stub (its refcount stays), and p.free lists them for
    new_chunk() / append(), lowest first. keep: indices something else names - the chunks of the
    .oct tail pairs (kl_graft keeps the removed map's collision records, and its verify() wants
    every pair on a 64-byte mesh). A kept dead mesh then points at stubs or at re-used chunks:
    nothing reads it (kl2 has no loop over the chunk table: its count 0xeac7a4 is read only by
    the loaders, by 0x638c90 'is this a file chunk' and by 0x45f260; every other use is an index
    taken from a live holder). A chunk a dead root reaches and a live root also reaches is live.
    Returns (number of free indices, bytes the stubs saved). Run trim / slim (kl_graft lighten)
    BEFORE this: afterwards no dead root is left for it to find the dead materials by."""
    reached = closure(p, live)
    keep = set(keep)
    free = [i for i in range(1, len(p.chunks)) if i not in reached and i not in keep]
    saved = 0
    for i in free:
        saved += len(p.chunks[i]) - 16
        p.chunks[i] = bytes(16)
    p.free = free[::-1]                                # pop() gives the lowest
    return len(free), saved


def compact(p, live):
    """The file with only what the live roots reach, renumbered in the old order (extract()).
    -> (Prm, {old index: new index}). EVERY holder of a chunk index has to be rewritten with the
    map: .gms record +0x0c, the .prp fields of prp_roots(), the .oct tail pairs (a pair on a
    dropped chunk has to go, with its record), KLWardrobe.ini. kl_chars.compact_level does that."""
    return extract(p, live)


def level_roots(prp, tids, raw, extra=(), game='dd', schema=None):
    """Every chunk the level's own files name, as walk() takes it: the .prp fields and scene
    block (prp_roots) and the .gms records (unpacked .gms `raw`), plus `extra` - model roots no
    entity names (the wardrobe's: kl_chars.wardrobe_roots). The same set as kl_graft.live_roots."""
    if schema is None:
        import kl_prpjoin
        schema = kl_prpjoin.schema(game)
    return ([(c, k) if k else c for _w, c, k in prp_roots(prp, tids, schema, game)] +
            [m for m in gms_roots(raw) if m] + [(r, 'root') for r in extra])


def gms_roots(raw):
    """Chunk index (+0x0c) of every record of an unpacked .gms, in entity-table order (0 = none)."""
    t = struct.unpack_from('<I', raw, 0)[0]
    u32 = lambda o: struct.unpack_from('<I', raw, o)[0]
    return [u32(4 * (u32(t + 4 + 8 * k) & 0xffffff) + 0x0c) for k in range(u32(t))]


def prp_roots(prp, tids, schema, game):
    """Every chunk index a .prp holds. prp: kl_prp.Prp; tids: type id per node (ROOT's 0x100021
    first, then the .gms entity table); schema: kl_rtp.Schema of the game.
    Returns [(where, chunk, kind)], where = (node number, controller number or None, field
    number in the object) or ('scene', name). kind None = decided by the lType word."""
    from kl_prp import units
    table, out = {**PRP_FIELDS, **PRP_GAME[game]}, []
    val = lambda tok: struct.unpack('<I', tok[1])[0]

    def obj(cls, toks, node, ctrl):
        fs = schema.fields(cls)
        if not fs or not any((f.owner, int(f.key.split(':')[1])) in table for f in fs):
            return
        us = units(toks[1:-1])
        if len(us) != len(fs):
            raise ValueError('node %d: object does not fit class %s' % (node, cls))
        for k, (f, u) in enumerate(zip(fs, us)):
            key = (f.owner, int(f.key.split(':')[1]))
            if key in table and val(u[0]):
                out.append(((node, ctrl, k), val(u[0]), table[key]))

    for n, (tid, node) in enumerate(zip(tids, prp.nodes())):
        cls = schema.geoms.get(tid)
        if cls is None:
            continue
        obj(cls, node['props'], n, None)
        for k, (name, toks) in enumerate(node['ctrls']):
            impl = schema.controller(prp.key(name), cls)
            if impl:
                obj(impl, toks, n, k)
    s = prp.settings                                   # scene block: name, type, count, [ value ]
    for k, tok in enumerate(s):
        if tok[0] == 0x0c and prp.key(tok) in PRP_SCENE:
            out.append((('scene', prp.key(tok)), val(s[k + 4]), PRP_SCENE[prp.key(tok)]))
    return out
