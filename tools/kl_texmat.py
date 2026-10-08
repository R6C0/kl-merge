#!/usr/bin/env python3
"""
Surfaces of a level: textures (.TEX), materials (.MAT) and the compiled shader cache (.fxc),
read into models, written back byte for byte, and joined with renumbering.

    python kl_texmat.py            round trip of every stock archive of both games + join test
    python kl_texmat.py rt | join  one of the two

Counts below are over the 21 Dog Days levels (F01 from KL_PortBackup) and the 20 Dead Men
levels unless a kl2.exe address is given. The round trip also covers the other archives under
Scenes: 44 Dog Days and 59 Dead Men archives, every .TEX / .MAT / .fxc byte-identical.

REFERENCE CHAIN (what a join has to renumber)
  .prm object (+0x12 u16 material id)        -> .MAT instance slot          [other module]
  .prm sprite prim (lType 2, +0x04 u16)      -> .TEX id (1229 in F01, all resolve) [other module]
  .prp ZOnScreenDisplay2 field 0xd0ba88:7    -> 200 x .TEX id (HUD pictures; 7686 of 7686
        non-zero values resolve, 21 levels). Other .prp carriers were NOT found by value
        statistics; about 24 UI/font textures per level have no known referrer.
  .MAT instance entry +0x04                  -> .MAT class slot (same file)
  .MAT instance INST/BIND/TEXT/TXID          -> .TEX id; 0 = none; bit 31 set = engine surface
        slot, not a file texture (Dog Days only uses 0x80000000, Dead Men 0x80000000..3).
        Every other TXID resolves: 32,738 of 32,738 (DD), 28,062 of 28,062 (DM). No other
        integer in a .MAT tree is an id (all int tags listed under MAT below).
  .MAT ref table [instance slot]             <- derived from the .prm: sum over model roots of
        root chunk refcounts per mesh object using the material (see material_refs).
  .TEX animated texture (flag 0x100)         -> frame list of .TEX ids
  .TEX cube map (flag 0x400)                 -> DM: list of 6 .TEX ids; DD: faces stored inline
  .MAT class CLAS/SUBC/LAYE PATH, IDEN       -> effect file and technique name (by name, no ids)
  .fxc entry                                 <- (defines, effect file); nothing refers to an
        entry by index, so a union needs no renumbering.

TEX
  record (both games): u32 size, fourcc x2, u32 id, u16 h, u16 w, u32 mips, u32 flags,
      f32 scale, u32 +0x20 (opaque; 5 distinct non-zero values in DD), name\\0, mips x (u32 n, data)
  Dead Men: header [T1 ofs][T2 ofs][0][4]; records from 0x10, every item 16-byte aligned, in id
      order; T1 (2048 x u32 record offset) and T2 (2048 x u32 list offset) at the end.
      A list is u32 n + n ids, stored behind some later record (usually its highest member).
      Cube maps (263) have a 6-id list whose first id is the owner; animated textures (24) a
      frame list; 278 of these 287 sit behind their highest member, 9 further on. 43 more
      lists are in the file but in no table (a second
      cube sharing face 0 with an earlier one). Tex.lists keeps where each list is stored.
  Dog Days: header [0x20][0x4020][0 x6]; three 4096-entry tables at 0x20 / 0x4020 / 0x8020;
      records from 0xc020 in id order, 16-byte aligned, file padded to 16.
      table 0: record offset.   table 1: frame COUNT of an animated texture (not an offset);
      the list (u32 n + n ids) follows the record inline (7 textures, story levels only;
      loader kl2 0x5d2701..0x5d2776).   table 2: a word copied to the texture object
      (kl2 0x5d27b0); zero in F01-F09/L00/L09. ASSUMPTION: a streaming-section bit mask
      (values such as 0x111, 0x711, 0x700; equal for the maps of one material), not an id.
      Cube map (248): record with id field 0, then a 32-byte block [id, 5 x face present, 0, 0],
      then the present faces inline (id 0, flag 0x400). 247 have 5 faces, one has 3.
  Ids start at 128 and are contiguous in all 41 levels (max used: DD 1953 in L05, DM 1610).
  The id limit is the table size: 4096 (kl2 0x5d220b cmp eax,0x1000), 2048 in Dead Men.

MAT (both games; the layout rules in write_mat reproduce every stock file)
  header [class table ofs][instance table ofs][0][ref table ofs]; the tables are the LAST thing
  in the file: 32 class slots, 2048 instance slots, 2048 ref counts (same sizes in every file;
  ASSUMPTION that the engine's arrays are that size too, the loader was not read). Slot 0 is
  never used; slots are filled 1..n without holes.
  entry (0x30 bytes): +0x00 class name string, +0x04 class slot (0 in a class entry),
      +0x08 feature flags, +0x0C render group, +0x10 (8, or 2 for Sprites), +0x14 (0..8),
      +0x18 surface type, +0x1C root node, +0x20 root child count, +0x24..+0x2F zero.
      Class entries have all of +0x04..+0x18 zero.
  node: tag (fourcc stored reversed), value, count, type; 16 bytes in Dead Men (count, type
      u32), 12 in Dog Days (u16). type 0 float, 1 string (count = length + 1), 2 int, 3 list;
      value is inline for a single int/float, else a file offset.
  trees:  CLAS{NAME, SUBC{NAME, OTYP, STYP, VALI{BIND, VALU}?, LAYE{NAME,TYPE,PATH,IDEN,VALI}*}*}
          INST{NAME, BIND{ RSTA{..} TEXT{NAME,ENAB,TXID?,TILU?,TILV?,TILW?} COLO FLTV BOOL SCRL
          SPRI }}.  Int tags: ENAB, VALU (0/1), TXID, and RSTA's BENA ATST AREF FENA ZBIA.

FXC (Dog Days only; Dead Men ships .fx sources instead)
  [u32 100][u32 count][u32 bytes after the header][u32 16], then per entry a 0x850-byte head:
  +0 u32 profile (3 for the *30.fx effects, else 1), +4 u32 key, +8 u32 blob size,
  +0x0C 32 x {name[32], value[32]} defines (first = mesh class: MESH_STANDARD / _RIGID /
  _WEIGHTED / _TWEENED / SPRITES; the rest upper-cased material BOOL names, value "1"),
  +0x80C blob offset in the file, +0x810 effect file name; then the D3D9 effect blob.
  key = byte sum of the effect file name + 412 + for each define (95 + byte sum of its name
  without a trailing "ENABLED"): 2069 of 2069 entries, 242 distinct (fxc_key). 20 of the 21
  define names are upper-cased BOOL names; BLENDENABLED is RSTA/BENA. How the engine looks an
  entry up was not read; no two entries of a file share (profile, defines, effect file).
  A material reaches an entry through its class: SUBC chosen by mesh kind (STYP) and VALI
  conditions, LAYE PATH = effect ("Standard" -> Standard30.fx), IDEN = technique in it.
"""
import hashlib, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_mat import read_fxc, write_fxc, entry_key, FXC_HDR

ANIMATED, CUBE = 0x100, 0x400
ENGINE_SLOT = 0x80000000
FLOAT, STRING, INT, LIST = 0, 1, 2, 3


def _pad(b):
    b.extend(b'\0' * (-len(b) % 16))


# ================================================================ TEX
class Texture:
    """entry: the record (face 0 of a Dog Days cube). faces/cube: Dog Days cube map (inline
    face records, the 7 dwords after the id in its block). frames: id list (Dog Days: animated
    frames; Dead Men: table-2 list = cube faces or frames). group: Dog Days table-2 word."""
    __slots__ = ('entry', 'faces', 'cube', 'frames', 'group')

    def __init__(self, entry, faces=None, cube=None, frames=None, group=0):
        self.entry, self.faces, self.cube, self.frames, self.group = entry, faces, cube, frames, group

    flags = property(lambda s: struct.unpack_from('<I', s.entry, 24)[0])
    name = property(lambda s: s.entry[36:s.entry.index(b'\0', 36)].decode('latin1'))

    def key(self):
        """Identity of the picture: everything but its own id (None when it names other ids)."""
        if self.frames is not None:
            return None
        e = bytearray(self.entry); e[12:16] = b'\0\0\0\0'
        h = hashlib.md5(bytes(e))
        for f in self.faces or ():
            h.update(f)
        h.update(repr((self.cube, self.group)).encode())
        return h.digest()

    def renumbered(self, old, new, idmap):
        e = bytearray(self.entry)
        if struct.unpack_from('<I', e, 12)[0] == old:           # Dog Days cube records carry 0
            struct.pack_into('<I', e, 12, new)
        fr = None if self.frames is None else tuple(idmap[i] for i in self.frames)
        return Texture(bytes(e), self.faces, self.cube, fr, self.group)


class Tex:
    def __init__(self, game, tex=None, lists=None):
        self.game, self.slots = game, 4096 if game == 'dd' else 2048
        self.tex = tex or {}                # id -> Texture
        self.lists = lists or []            # Dead Men file layout: (stored behind record id,
                                            # owner id or None if in no table, ids)


def read_tex(data):
    if struct.unpack_from('<I', data, 0)[0] == 0x20:            # Dog Days
        if struct.unpack_from('<8I', data, 0) != (0x20, 0x4020, 0, 0, 0, 0, 0, 0):
            raise ValueError('unexpected Dog Days .TEX header')
        T = [struct.unpack_from('<4096I', data, 0x20 + 0x4000 * k) for k in range(3)]
        t = Tex('dd')
        for i, o in enumerate(T[0]):
            if not o:
                if T[1][i] or T[2][i]:
                    raise ValueError('table entry for the missing texture %d' % i)
                continue
            size, flags = struct.unpack_from('<I', data, o)[0], struct.unpack_from('<I', data, o + 24)[0]
            x = Texture(data[o:o + size], group=T[2][i])
            p = o + size + (-size % 16)
            if flags & CUBE:
                blk = struct.unpack_from('<8I', data, p); p += 32
                if blk[0] != i or any(b > 1 for b in blk[1:6]):
                    raise ValueError('cube block of texture %d' % i)
                x.cube, x.faces = blk[1:], []
                for present in blk[1:6]:
                    if present:
                        fs = struct.unpack_from('<I', data, p)[0]
                        x.faces.append(data[p:p + fs]); p += fs + (-fs % 16)
            if bool(flags & ANIMATED) != bool(T[1][i]):
                raise ValueError('animation flag and frame count disagree at %d' % i)
            if T[1][i]:
                n = struct.unpack_from('<I', data, p)[0]
                if n != T[1][i]:
                    raise ValueError('frame list of texture %d' % i)
                x.frames = struct.unpack_from('<%dI' % n, data, p + 4)
            t.tex[i] = x
        return t
    t1, t2, z, v = struct.unpack_from('<4I', data, 0)           # Dead Men
    if (z, v) != (0, 4) or t2 - t1 != 0x2000 or len(data) - t2 != 0x2000:
        raise ValueError('unexpected Dead Men .TEX header')
    T1, T2 = struct.unpack_from('<2048I', data, t1), struct.unpack_from('<2048I', data, t2)
    t = Tex('dm')
    owner = {o: i for i, o in enumerate(T2) if o}
    recs = sorted((o, i) for i, o in enumerate(T1) if o)
    for k, (o, i) in enumerate(recs):
        size = struct.unpack_from('<I', data, o)[0]
        t.tex[i] = Texture(data[o:o + size])
        p = o + size + (-size % 16)                             # lists stored behind this record
        end = recs[k + 1][0] if k + 1 < len(recs) else t1
        while p + 4 <= end and struct.unpack_from('<I', data, p)[0]:
            n = struct.unpack_from('<I', data, p)[0]
            ids = struct.unpack_from('<%dI' % n, data, p + 4)
            t.lists.append((i, owner.pop(p, None), ids))
            if t.lists[-1][1] is not None:
                t.tex[t.lists[-1][1]].frames = ids
            p += 4 + 4 * n + (-(4 + 4 * n) % 16)
    if owner:
        raise ValueError('id list outside the record stream')
    return t


def write_tex(t):
    ids = sorted(t.tex)
    if ids and ids[-1] >= t.slots:
        raise ValueError('texture id %d does not fit the %d-entry table' % (ids[-1], t.slots))
    if t.game == 'dd':
        T = [[0] * 4096 for _ in range(3)]
        out = bytearray(struct.pack('<8I', 0x20, 0x4020, 0, 0, 0, 0, 0, 0)) + bytes(0xc000)
        for i in ids:
            x = t.tex[i]
            _pad(out); T[0][i] = len(out); T[2][i] = x.group
            out += x.entry
            if x.flags & CUBE:
                _pad(out); out += struct.pack('<8I', i, *x.cube)
                for f in x.faces:
                    _pad(out); out += f
            if x.frames is not None:
                _pad(out); T[1][i] = len(x.frames)
                out += struct.pack('<%dI' % (len(x.frames) + 1), len(x.frames), *x.frames)
        _pad(out)
        for k in range(3):
            struct.pack_into('<4096I', out, 0x20 + 0x4000 * k, *T[k])
        return bytes(out)
    T1, T2 = [0] * 2048, [0] * 2048
    out = bytearray(16)
    after, placed = {}, set()               # record id -> lists stored behind it
    for at, owner, fr in t.lists:
        if owner is None:
            after.setdefault(at, []).append((None, fr))
        elif owner in t.tex and t.tex[owner].frames is not None and owner not in placed:
            after.setdefault(at, []).append((owner, t.tex[owner].frames)); placed.add(owner)
    for i in ids:                           # a list that is new: behind its highest member
        if t.tex[i].frames is not None and i not in placed:
            after.setdefault(max(t.tex[i].frames), []).append((i, t.tex[i].frames))
    for i in ids:
        _pad(out); T1[i] = len(out); out += t.tex[i].entry
        for owner, fr in after.get(i, ()):
            _pad(out)
            if owner is not None:
                T2[owner] = len(out)
            out += struct.pack('<%dI' % (len(fr) + 1), len(fr), *fr)
    _pad(out)
    struct.pack_into('<4I', out, 0, len(out), len(out) + 0x2000, 0, 4)
    return bytes(out) + struct.pack('<2048I', *T1) + struct.pack('<2048I', *T2)


def texture_closure(t, ids):
    """ids plus every texture their frame / face lists name."""
    out, todo = set(), list(ids)
    while todo:
        i = todo.pop()
        if i not in out:
            if i not in t.tex:
                raise KeyError('texture %d is not in the file' % i)
            out.add(i); todo.extend(t.tex[i].frames or ())
    return out


def merge_tex(a, b, wanted_ids_b, dedupe=True):
    """Add b's textures `wanted_ids_b` (and what their lists name) to a. a's ids do not change.
    With dedupe, a b texture whose record, faces and group word equal an a texture's maps to it.
    Returns (new Tex, {b id: id in the result})."""
    if a.game != b.game:
        raise ValueError('cannot join a %s with a %s texture file' % (a.game, b.game))
    out = Tex(a.game, dict(a.tex), list(a.lists))
    have = {}
    if dedupe:
        for i in sorted(a.tex):
            have.setdefault(a.tex[i].key(), i)
    idmap, new = {}, []
    free = max(list(a.tex) + [127]) + 1
    for i in sorted(texture_closure(b, wanted_ids_b)):
        k = b.tex[i].key()
        if dedupe and k is not None and k in have:
            idmap[i] = have[k]
            continue
        if free >= out.slots:
            raise ValueError('out of texture ids (%d-entry table)' % out.slots)
        idmap[i] = free; new.append(i); free += 1
        if k is not None:
            have[k] = idmap[i]
    for i in new:
        out.tex[idmap[i]] = b.tex[i].renumbered(i, idmap[i], idmap)
    return out, idmap


# ================================================================ MAT
class Entry:
    """cls: class name. f: the 12 dwords of the entry ([0], [7], [8] are rewritten on write).
    root: node [tag, type, count, value]; value is a list of nodes (LIST), bytes without the
    terminator (STRING), the raw dwords (count > 1) or the inline dword."""
    __slots__ = ('cls', 'f', 'root')

    def __init__(self, cls, f, root):
        self.cls, self.f, self.root = cls, f, root

    class_slot = property(lambda s: s.f[1])
    name = property(lambda s: next((n[3].decode('latin1') for n in s.root[3] if n[0] == 'NAME'), None))


class Mat:
    def __init__(self, wide, ncls=32, ninst=2048):
        self.wide = wide                    # True: Dead Men 16-byte nodes
        self.classes, self.insts = {}, {}   # slot -> Entry
        self.ncls, self.ninst = ncls, ninst
        self.refs = [0] * ninst


def read_mat(data):
    ct, it, h8, rt = struct.unpack_from('<4I', data, 0)
    if h8 or not 16 <= ct <= it <= rt <= len(data):
        raise ValueError('unexpected .MAT header')
    first = next(o for o in struct.unpack_from('<%dI' % ((rt - ct) // 4), data, ct) if o)
    wide = struct.unpack_from('<H', data, struct.unpack_from('<I', data, first + 0x1c)[0] + 10)[0] != LIST
    size, fmt = (16, '<III') if wide else (12, '<IHH')
    m = Mat(wide, (it - ct) // 4, (rt - it) // 4)
    m.refs = list(struct.unpack_from('<%dI' % m.ninst, data, rt))     # one per instance slot; the file
                                            # ends here (kl_mat.convert_mat appends strings after it)

    def nodes(p, n):
        out = []
        for q in range(p, p + size * n, size):
            v, c, ty = struct.unpack_from(fmt, data, q + 4)
            if ty == LIST:
                v = nodes(v, c)
            elif ty == STRING:
                v = data[v:data.index(b'\0', v)]    # count = length + 1 in every stock file
                                                    # (kl_mat.convert_mat keeps the old count)
            elif ty in (FLOAT, INT):
                if c > 1:
                    v = data[v:v + 4 * c]
            else:
                raise ValueError('node type %d at %#x' % (ty, q))
            out.append([data[q:q + 4][::-1].decode('latin1'), ty, c, v])
        return out

    for table, tab, n in ((m.classes, ct, m.ncls), (m.insts, it, m.ninst)):
        for slot, o in enumerate(struct.unpack_from('<%dI' % n, data, tab)):
            if o:
                f = list(struct.unpack_from('<12I', data, o))
                table[slot] = Entry(data[f[0]:data.index(b'\0', f[0])], f, nodes(f[7], 1)[0])
    return m


def write_mat(m):
    """The layout every stock file has (103 of 103 archives reproduced):
    - everything is 16-byte aligned; data starts at 0x10; the three tables come last;
    - instances are written in slot order, each class right before its first instance;
    - an entry is written depth first: a node's children's data, then the node array; then the
      class name, the root node and the 0x30-byte entry;
    - identical blobs (strings, value arrays, node arrays) are stored once in the whole file;
      a class entry's name is pooled only with other class entries' names; entries never."""
    fmt = '<4sIII' if m.wide else '<4sIHH'
    out, pool, cnames = bytearray(16), {}, {}

    def put(b, share=pool):
        if share is not None and b in share:
            return share[b]
        _pad(out)
        p = len(out); out.extend(b)
        if share is not None:
            share[b] = p
        return p

    def emit(ns):
        recs = []
        for tag, ty, c, v in ns:
            if ty == LIST:
                c, v = len(v), put(b''.join(emit(v)))
            elif ty == STRING:
                c, v = len(v) + 1, put(v + b'\0')
            elif c > 1:
                v = put(v)
            recs.append(struct.pack(fmt, tag.encode('latin1')[::-1], v, c, ty))
        return recs

    tabs = ([0] * m.ncls, [0] * m.ninst)
    def entry(kind, slot, e):
        if not 0 < slot < len(tabs[kind]):
            raise ValueError('material %s slot %d out of range' % ('instance' if kind else 'class', slot))
        rec = emit([e.root])[0]
        f = list(e.f)
        f[0] = put(e.cls + b'\0', pool if kind else cnames)
        f[7], f[8] = put(rec), len(e.root[3])
        tabs[kind][slot] = put(struct.pack('<12I', *f), None)

    done = set()
    for slot in sorted(m.insts):
        c = m.insts[slot].f[1]
        if c not in done:
            done.add(c); entry(0, c, m.classes[c])
        entry(1, slot, m.insts[slot])
    for c in sorted(set(m.classes) - done):                     # never happens in stock files
        entry(0, c, m.classes[c])
    _pad(out)
    ct = len(out); it = ct + 4 * m.ncls; rt = it + 4 * m.ninst
    out += struct.pack('<%dI' % m.ncls, *tabs[0]) + struct.pack('<%dI' % m.ninst, *tabs[1])
    out += struct.pack('<%dI' % len(m.refs), *m.refs)
    struct.pack_into('<4I', out, 0, ct, it, 0, rt)
    return bytes(out)


def walk(node, path=''):
    """Yield (path, node) for every node below and including `node`."""
    yield path + node[0], node
    if node[1] == LIST:
        for c in node[3]:
            yield from walk(c, path + node[0] + '/')


def texture_stages(entry):
    """[(stage name, TXID node)] of an instance: the nodes a join rewrites."""
    out = []
    for path, n in walk(entry.root):
        if path == 'INST/BIND/TEXT':
            name = next((c[3].decode('latin1') for c in n[3] if c[0] == 'NAME'), None)
            out += [(name, c) for c in n[3] if c[0] == 'TXID']
    return out


def used_textures(mat, material_ids=None):
    """.TEX ids the given instance slots (default: all) name. Engine slots and 0 are left out."""
    out = set()
    for slot in (mat.insts if material_ids is None else material_ids):
        for _name, n in texture_stages(mat.insts[slot]):
            if n[3] and not n[3] & ENGINE_SLOT:
                out.add(n[3])
    return out


def _copy(node, txmap=None):
    tag, ty, c, v = node
    if ty == LIST:
        v = [_copy(x, txmap) for x in v]
    elif txmap is not None and tag == 'TXID' and v and not v & ENGINE_SLOT:
        if v not in txmap:
            raise KeyError('texture %d has no new id' % v)
        v = txmap[v]
    return [tag, ty, c, v]


def _frozen(node):
    return (node[0], node[1], node[2], tuple(_frozen(x) for x in node[3]) if node[1] == LIST else node[3])


def merge_mat(a, b, wanted_b, texture_id_map, dedupe=True):
    """Add b's instance slots `wanted_b` to a, with their classes and with TXIDs rewritten through
    `texture_id_map` (from merge_tex). a's slots do not change. A b class equal to an a class
    (name and whole tree) shares its slot; with dedupe, so does an instance equal to an a
    instance after rewriting (its ref count is added). Other new slots take b's ref count: the
    caller should overwrite `refs` with material_refs() of the joined .prm.
    Returns (new Mat, {b instance slot: slot in the result})."""
    if a.wide != b.wide:
        raise ValueError('cannot join materials of different games (node size differs)')
    out = Mat(a.wide, a.ncls, a.ninst)
    out.classes, out.insts, out.refs = dict(a.classes), dict(a.insts), list(a.refs)
    ckey = lambda e: (e.cls, _frozen(e.root))
    ikey = lambda e: (e.cls, tuple(e.f[1:7]), tuple(e.f[9:]), _frozen(e.root))
    chave = {}
    for s in sorted(out.classes):
        chave.setdefault(ckey(out.classes[s]), s)
    ihave = {}
    if dedupe:
        for s in sorted(out.insts):
            ihave.setdefault(ikey(out.insts[s]), s)
    cmap, idmap = {}, {}
    for slot in sorted(set(wanted_b)):
        src = b.insts[slot]
        c = src.f[1]
        if c not in cmap:
            k = ckey(b.classes[c])
            if k not in chave:
                n = max(list(out.classes) + [0]) + 1
                if n >= out.ncls:
                    raise ValueError('out of material class slots (%d)' % out.ncls)
                out.classes[n] = Entry(b.classes[c].cls, list(b.classes[c].f), _copy(b.classes[c].root))
                chave[k] = n
            cmap[c] = chave[k]
        f = list(src.f); f[1] = cmap[c]
        e = Entry(src.cls, f, _copy(src.root, texture_id_map))
        k = ikey(e)
        if dedupe and k in ihave:
            idmap[slot] = ihave[k]
            out.refs[ihave[k]] += b.refs[slot]
            continue
        n = max(list(out.insts) + [0]) + 1
        if n >= out.ninst or n > 0xffff:
            raise ValueError('out of material slots (%d)' % out.ninst)
        out.insts[n] = e; out.refs[n] = b.refs[slot]; idmap[slot] = n
        if dedupe:
            ihave[k] = n
    return out, idmap


def material_refs(prm, ninst=2048):
    """The .MAT ref table as the .prm implies it. A model root is a chunk with lType 7 (+0x02),
    +0x14 object count, +0x18 object table chunk; an object names its material at +0x12 (u16).
    Each mesh object (lType 8) adds its root chunk's refcount, once per root listing it; a
    scatter object (lType 9) adds 1 however many roots list it. Equal to the stored table in
    every stock archive of both games (see round_trip). Roots are found by shape, as in the
    Blood Money reference; what the engine does with the table was not read."""
    t, n = struct.unpack_from('<II', prm, 0)
    tab = [struct.unpack_from('<4I', prm, t + 16 * i) for i in range(n)]
    refs, scatter = [0] * ninst, set()
    for o, size, rc, _z in tab[1:]:
        if size < 0x1c or struct.unpack_from('<H', prm, o + 2)[0] != 7 or prm[o] >= 16:
            continue
        nobj, ot = struct.unpack_from('<II', prm, o + 0x14)
        if not (nobj and 0 < ot < n and tab[ot][1] >= 4 * nobj):
            continue
        for oi in struct.unpack_from('<%dI' % nobj, prm, tab[ot][0]):
            if 0 < oi < n and tab[oi][1] >= 0x14:
                kind, mid = struct.unpack_from('<H', prm, tab[oi][0] + 2)[0], struct.unpack_from('<H', prm, tab[oi][0] + 0x12)[0]
                if mid >= ninst or (kind == 9 and oi in scatter):
                    continue
                scatter.add(oi)
                refs[mid] += 1 if kind == 9 else rc
    return refs


# ================================================================ FXC
def fxc_defines(head):
    out = []
    for i in range(32):
        r = head[12 + 64 * i:76 + 64 * i]
        if r[0]:
            out.append((r[:32].split(b'\0')[0].decode('latin1'), r[32:].split(b'\0')[0].decode('latin1')))
    return out


def fxc_info(head):
    """(profile, key, [(define, value)], effect file name)"""
    profile, key = struct.unpack_from('<II', head, 0)
    return profile, key, fxc_defines(head), head[0x810:0x850].split(b'\0')[0].decode('latin1')


def fxc_key(defines, fx):
    """The key stored at +4 (see the docstring; holds for all 242 distinct stock entries)."""
    cut = lambda n: n[:-7] if n.endswith('ENABLED') else n
    return sum(fx.encode('latin1')) + 412 + sum(95 + sum(cut(n).encode('latin1')) for n, _v in defines)


def merge_fxc(a, b):
    """Union of two .fxc files (bytes in, bytes out): a's entries in order, then b's entries that
    a lacks. Entries are compared in full (head without its file offset, and blob)."""
    va, ea = read_fxc(a)
    vb, eb = read_fxc(b)
    if va != vb:
        raise ValueError('fxc versions differ')
    seen = set(entry_key(h, bl) for h, bl in ea)
    out = list(ea)
    for h, bl in eb:
        k = entry_key(h, bl)
        if k not in seen:
            seen.add(k); out.append((h, bl))
    return write_fxc(out, va)


# ================================================================ self test
def _members(game):
    import zipfile
    from kl_port_check import level_zips
    for z in sorted(level_zips(game)):
        with zipfile.ZipFile(z) as zf:
            got = {}
            for n in zf.namelist():
                ext = n.lower().rsplit('.', 1)[-1]
                if ext in ('tex', 'mat', 'fxc', 'prm') and ext not in got:
                    got[ext] = n
            if 'tex' in got or 'mat' in got:
                yield os.path.basename(z), zf, got


def round_trip(log=print):
    from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE
    bad = 0
    for label, game in (('Dog Days', find(DD_GUESSES, DD_EXE)), ('Dead Men', find(DM_GUESSES, DM_EXE))):
        n = dict(tex=[0, 0], mat=[0, 0], fxc=[0, 0], refs=[0, 0], key=[0, 0])
        for name, zf, got in _members(game):
            for ext, fn in (('tex', lambda d: write_tex(read_tex(d))), ('mat', lambda d: write_mat(read_mat(d))),
                            ('fxc', lambda d: write_fxc(read_fxc(d)[1], read_fxc(d)[0]))):
                if ext in got:
                    d = zf.read(got[ext])
                    ok = fn(d) == d
                    n[ext][0] += ok; n[ext][1] += 1
                    if not ok:
                        log('  DIFFERENT: %s %s' % (name, got[ext]))
                    if ext == 'fxc':
                        for h, _b in read_fxc(d)[1]:
                            p, key, defs, fx = fxc_info(h)
                            n['key'][0] += fxc_key(defs, fx) == key; n['key'][1] += 1
            if 'mat' in got and 'prm' in got:
                m = read_mat(zf.read(got['mat']))
                n['refs'][0] += material_refs(zf.read(got['prm']), m.ninst) == m.refs; n['refs'][1] += 1
        log('%s: byte-identical .TEX %d/%d, .MAT %d/%d, .fxc %d/%d; ref table = material_refs(.prm) '
            '%d/%d; fxc keys %d/%d' % (label, *n['tex'], *n['mat'], *n['fxc'], *n['refs'], *n['key']))
        bad += sum(v[1] - v[0] for v in n.values())
    return bad


def join_test(pairs=(('F01', 'F02'), ('F05', 'F08')), log=print):
    """Merge B's textures and materials into A; every B material must still resolve to the same
    pictures, and A must be untouched. Also reports the id space two levels need."""
    import zipfile
    from kl_port_check import find, level_zips, DD_GUESSES, DD_EXE
    zips = {os.path.basename(z)[:3]: z for z in level_zips(find(DD_GUESSES, DD_EXE)) if z.endswith('_Main.zip')}
    def load(l):
        with zipfile.ZipFile(zips[l]) as zf:
            g = {n.lower().rsplit('.', 1)[-1]: n for n in zf.namelist()}
            return read_tex(zf.read(g['tex'])), read_mat(zf.read(g['mat'])), zf.read(g['fxc'])
    def pictures(tex, mat, slot):                                # what a material shows
        out = []
        for name, n in texture_stages(mat.insts[slot]):
            v = n[3]
            if not v or v & ENGINE_SLOT:
                out.append((name, v)); continue
            x = tex.tex[v]
            fr = None if x.frames is None else tuple(tex.tex[i].key() for i in x.frames)
            e = bytearray(x.entry); e[12:16] = b'\0\0\0\0'
            out.append((name, bytes(e), tuple(x.faces or ()), x.cube, x.group, fr))
        e = mat.insts[slot]
        c = mat.classes[e.f[1]]
        return out, e.cls, e.f[2:7], _frozen(c.root), [(p, n[3]) for p, n in walk(e.root) if n[0] != 'TXID' and n[1] != LIST]
    bad = 0
    for la, lb in pairs:
        (ta, ma, fa), (tb, mb, fb) = load(la), load(lb)
        for dedupe in (False, True):
            wanted = sorted(mb.insts)
            tex, tmap = merge_tex(ta, tb, used_textures(mb, wanted), dedupe)
            mat, mmap = merge_mat(ma, mb, wanted, tmap, dedupe)
            tex2, mat2 = read_tex(write_tex(tex)), read_mat(write_mat(mat))          # through the file
            errs = sum(pictures(tb, mb, s) != pictures(tex2, mat2, mmap[s]) for s in wanted)
            errs += sum(pictures(ta, ma, s) != pictures(tex2, mat2, s) for s in ma.insts)
            errs += sum(tex2.tex[i].entry != ta.tex[i].entry or tex2.tex[i].faces != ta.tex[i].faces for i in ta.tex)
            errs += sum(_frozen(mat2.classes[s].root) != _frozen(ma.classes[s].root) for s in ma.classes)
            if not dedupe:
                errs += mat2.refs[:len(ma.insts) + 1] != ma.refs[:len(ma.insts) + 1]
                errs += [mat2.refs[mmap[s]] for s in wanted] != [mb.refs[s] for s in wanted]
            bad += errs
            log('%s + %s (dedupe %s): textures %d + %d used of %d -> %d (max id %d of 4095); materials %d + %d '
                '-> %d (of 2047); classes %d + %d -> %d (of 31); B materials checked %d, A %d, errors %d'
                % (la, lb, 'on' if dedupe else 'off', len(ta.tex), len(tmap), len(tb.tex), len(tex2.tex), max(tex2.tex),
                   len(ma.insts), len(wanted), len(mat2.insts), len(ma.classes), len(mb.classes), len(mat2.classes),
                   len(wanted), len(ma.insts), errs))
        # whole of B, the way a graft of all of B's .prp/.prm would need it
        tex, tmap = merge_tex(ta, tb, list(tb.tex), False)
        u = merge_fxc(fa, fb)
        n = len(read_fxc(u)[1])
        ok = merge_fxc(u, fb) == u and merge_fxc(u, fa) == u and u[:len(fa)][16:] == fa[16:]
        bad += not ok
        log('%s + %s: all textures without sharing %d (max id %d); fxc %d + %d -> %d entries, union stable: %s'
            % (la, lb, len(tex.tex), max(tex.tex), len(read_fxc(fa)[1]), len(read_fxc(fb)[1]), n, ok))
    return bad


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    bad = 0
    if what in ('all', 'rt'):
        bad += round_trip()
    if what in ('all', 'join'):
        bad += join_test()
    print('problems: %d' % bad)
    sys.exit(1 if bad else 0)
