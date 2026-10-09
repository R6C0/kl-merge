"""
Kane & Lynch .TEX texture library converter (Dead Men -> Dog Days).

The file model and both containers are in kl_texmat.py (read_tex / write_tex, byte-identical on
every stock archive of both games); this module turns a Dead Men file into a Dog Days one and
checks a Dog Days file the way the game's loader walks it.

A texture record is the same in both games:
  u32 size, fourcc, fourcc, u32 id, u16 height, u16 width, u32 mips, u32 flags, f32 scale,
  u32 (+0x20), name\\0, then per mip: u32 size + pixel data
What differs is the container and how a record names other textures:
  Dead Men  header [table 1 ofs][table 2 ofs][0][4]; records from 0x10; two 2048-entry tables at
            the end: record offset, and offset of an id list (u32 n + n ids).
            cube map (flag 0x400): 6-id list, first id = the owner, the faces are textures of
            their own.   animated (flag 0x100): frame list, first id = the owner.
  Dog Days  header [0x20][0x4020][0 x6]; three 4096-entry tables at 0x20 / 0x4020 / 0x8020;
            records from 0xc020.   table 0: record offset.   table 1: frame COUNT of an animated
            texture; its list (u32 n + n ids) follows the record inline.   table 2: a word the
            loader copies into the texture object (zero in every Fragile Alliance level).
            cube map: record with id field 0, a 32-byte block [id, 5 x face present, 0, 0], then
            the faces inline (id field 0, flag 0x400).

Dog Days' loader (kl2 0x5d2113..0x5d27c4, read in the disassembly):
  - reads the three tables in one go from header[0]; header[1] is not used;
  - walks slots 0..4095 and, for each non-zero table-0 entry, reads the NEXT record in the
    file (0x505970: u32 size, int3 above 0x2000000; position += size rounded up to 16). The
    table-0 value itself is only tested for non-zero;
  - 0x70e4f0 switches on the fourcc at +4: DXT1 DXT3 DXT5 RGBA I8 U8V8 A8 16A0 16A1 16A4 PALN
    PALO; anything else is an int3;
  - flag 0x400: reads 0x18 bytes [id, 5 x present], position += 0x20, the id becomes the
    texture's id (vtable +0x54), then one record per present face;
  - the texture is stored at this + 4 + id * 0x44 (0x5d26e5), id taken from the record;
  - flag 0x100: n = table 1 [id]; copies 4 + 4 n bytes and skips them rounded up to 16
    (0x5d2711..0x5d2756). A flagged record without a list would make it eat the next record.

What the conversion keeps and loses:
  - every texture keeps its id, so nothing that names a texture needs rewriting;
  - animated textures stay animated (stock Dog Days has 7, all in story levels). A frame may be
    animated itself in both games (nested lists are kept as they are);
  - cube maps get their five faces inline. The face textures also stay as textures of their own
    (Dead Men materials name a few of them directly): 31-45 ids per map that Dog Days would not
    have spent;
  - Dead Men lists that are in no table (a second list for an owner that already has one,
    1-8 per map) cannot be reached by either game and are dropped.
NOT established: the meaning of flags 0x2, 0x40, 0x1000, 0x4000 and of the dword at +0x20 (copied
with the record; every flag value a Dead Men map carries also occurs in stock Dog Days files).
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DD_SLOTS = 4096
DD_T1, DD_T2, DD_T3, DD_DATA = 0x20, 0x4020, 0x8020, 0xc020
CUBE, ANIMATED = 0x400, 0x100
MAX_RECORD = 0x2000000                           # kl2 0x5059c0
FORMATS = (b'DXT1', b'DXT3', b'DXT5', b'RGBA', b'I8  ', b'U8V8', b'A8  ', b'16A0', b'16A1', b'16A4',
           b'PALN', b'PALO')                     # kl2 0x70e4f0 (stored reversed in the file)


def check_entry(e):
    """Walk a record's mips; returns (fourcc, width, height, mips, name) or raises."""
    size, f1, _f2, _id, h, w, mips = struct.unpack_from('<I4s4sIHHI', e, 0)
    end = e.index(b'\0', 36)
    p = end + 1
    for _ in range(mips):
        p += 4 + struct.unpack_from('<I', e, p)[0]
    if p != size or size != len(e):
        raise ValueError('texture entry size mismatch')
    return f1[::-1], w, h, mips, e[36:end].decode('latin1')


def _with(entry, ident=None, set_flags=0, clear_flags=0):
    e = bytearray(entry)
    if ident is not None:
        struct.pack_into('<I', e, 12, ident)
    struct.pack_into('<I', e, 24, (struct.unpack_from('<I', e, 24)[0] | set_flags) & ~clear_flags)
    return bytes(e)


def convert(dm_data):
    """Dead Men .TEX -> Dog Days .TEX. Returns (bytes, counts); counts: textures, cubes,
    animated, frames (ids named by frame lists), dropped_lists (lists in no table),
    unflagged (animation flags cleared because the texture had no list)."""
    import kl_texmat as TM
    src = TM.read_tex(dm_data)
    if src.game != 'dm':
        raise ValueError('not a Dead Men .TEX')
    out = TM.Tex('dd')
    n = dict(textures=len(src.tex), cubes=0, animated=0, frames=0, unflagged=0,
             dropped_lists=sum(1 for _at, owner, _ids in src.lists if owner is None))
    for i, x in sorted(src.tex.items()):
        fmt = check_entry(x.entry)[0]
        if fmt not in FORMATS:
            raise ValueError('texture %d: format %r is not one Dog Days reads' % (i, fmt))
        if struct.unpack_from('<I', x.entry, 12)[0] != i:
            raise ValueError('texture %d carries id %d' % (i, struct.unpack_from('<I', x.entry, 12)[0]))
        f, ids = x.flags, x.frames
        if ids is not None and (ids[0] != i or any(j not in src.tex for j in ids)):
            raise ValueError('texture %d: unexpected id list %r' % (i, ids))
        if f & CUBE:
            if f & ANIMATED or ids is None or len(ids) != 6:
                raise ValueError('cube map %d without a 6-face list' % i)
            if any(src.tex[j].flags & (CUBE | ANIMATED) for j in ids[1:]):
                raise ValueError('cube map %d: a face is a cube or animated itself' % i)
            # stock: record id 0 (the block carries the id), faces id 0 and flagged 0x400
            out.tex[i] = TM.Texture(_with(x.entry, 0), [_with(src.tex[j].entry, 0, CUBE) for j in ids[1:]],
                                    (1, 1, 1, 1, 1, 0, 0))
            n['cubes'] += 1
        elif f & ANIMATED:
            if ids is None:
                # the loader would read a count of 0 and still skip 16 bytes: clear the flag
                out.tex[i] = TM.Texture(_with(x.entry, clear_flags=ANIMATED)); n['unflagged'] += 1
            else:
                out.tex[i] = TM.Texture(x.entry, frames=tuple(ids))
                n['animated'] += 1; n['frames'] += len(ids)
        elif ids is not None:
            raise ValueError('texture %d has an id list but neither the cube nor the animation flag' % i)
        else:
            out.tex[i] = TM.Texture(x.entry)
    data = TM.write_tex(out)
    got = simulate_dd_loader(data)
    back = TM.read_tex(data)
    if got != (n['textures'], n['cubes'], n['animated']) or sorted(back.tex) != sorted(src.tex) or \
            any(back.tex[i].frames != out.tex[i].frames or back.tex[i].entry != out.tex[i].entry for i in out.tex):
        raise ValueError('converted .TEX does not read back as written')
    return data, n


def simulate_dd_loader(data, strict=True):
    """Walk a .TEX the way Dog Days' loader does (see the docstring). Returns (textures, cubes,
    animated) or raises with the first problem. Everything the loader would trip over is
    checked always; with `strict` also what every stock file satisfies but the loader does not
    test: table-0 values are the real record offsets, a texture's id is its slot, a frame list's
    own count equals table 1, frame ids exist, table entries only for present textures, and the
    walk ends at the end of the file."""
    if len(data) < DD_DATA:
        raise ValueError('file shorter than the three tables')
    t1off = struct.unpack_from('<I', data, 0)[0]
    T = [struct.unpack_from('<%dI' % DD_SLOTS, data, t1off + 4 * DD_SLOTS * k) for k in range(3)]
    pos = t1off + 12 * DD_SLOTS
    seen, lists = {}, []
    n = cubes = anims = 0

    def record(what):
        nonlocal pos
        if pos + 36 > len(data):
            raise ValueError('%s: record at %#x is past the end of the file' % (what, pos))
        size = struct.unpack_from('<I', data, pos)[0]
        if size > MAX_RECORD or pos + size > len(data):
            raise ValueError('%s: bad record size %d at %#x' % (what, size, pos))
        e = data[pos:pos + size]
        if check_entry(e)[0] not in FORMATS:
            raise ValueError('%s: format %r is an int3 in the loader' % (what, e[4:8][::-1]))
        pos += (size + 15) & ~15
        return e

    for slot in range(DD_SLOTS):
        if not T[0][slot]:
            if strict and (T[1][slot] or T[2][slot]):
                raise ValueError('slot %d: table entry for a missing texture' % slot)
            continue
        if strict and pos != T[0][slot]:
            raise ValueError('slot %d: loader at %#x but table says %#x' % (slot, pos, T[0][slot]))
        e = record('slot %d' % slot)
        ident, flags = struct.unpack_from('<I', e, 12)[0], struct.unpack_from('<I', e, 24)[0]
        if flags & CUBE:
            blk = struct.unpack_from('<6I', data, pos)
            pos += 0x20
            ident = blk[0]
            for k, present in enumerate(blk[1:]):
                if present:
                    record('slot %d face %d' % (slot, k + 1))
            cubes += 1
        if ident >= DD_SLOTS:
            raise ValueError('slot %d: texture id %d is outside the loader\'s table' % (slot, ident))
        if ident in seen:
            raise ValueError('slot %d: texture id %d is already used by slot %d' % (slot, ident, seen[ident]))
        if strict and ident != slot:
            raise ValueError('slot %d: record carries id %d' % (slot, ident))
        seen[ident] = slot
        n += 1
        if flags & ANIMATED:
            cnt = T[1][ident]
            if pos + 4 + 4 * cnt > len(data):
                raise ValueError('slot %d: frame list runs past the end of the file' % slot)
            own = struct.unpack_from('<I', data, pos)[0]
            if strict and (own != cnt or not cnt):
                raise ValueError('slot %d: frame list says %d frames, table 1 says %d' % (slot, own, cnt))
            lists.append((slot, struct.unpack_from('<%dI' % cnt, data, pos + 4)))
            pos += (4 + 4 * cnt + 15) & ~15
            anims += 1
        elif strict and T[1][ident]:
            raise ValueError('slot %d: frame count without the animation flag' % slot)
    if strict:
        for slot, ids in lists:
            if any(i not in seen for i in ids):
                raise ValueError('slot %d: a frame names a texture the file does not have' % slot)
        if pos != len(data):
            raise ValueError('loader ends at %#x, file is %#x bytes' % (pos, len(data)))
    return n, cubes, anims
