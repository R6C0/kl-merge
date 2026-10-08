"""
Kane & Lynch .TEX texture library converter (Dead Men -> Dog Days).

Both games store each texture the same way:
  u32 entry size, fourcc, fourcc, u32 id, u16 w, u16 h, u32 mips, u32, u32, f32, u32,
  name\\0, then per mip: u32 size + pixel data      (DXT1/3/5, ABGR, V8U8, I8)
Only the container differs:
  Dead Men : data from 0x10; header = [table1 ofs][table2 ofs][0][4]; tables (2048 x u32) at the end
  Dog Days : header = [0x20][0x4020][0][0]; table1 (4096 x u32) at 0x20, table2 at 0x4020,
             data from 0xc020
table1 maps texture id -> entry, table2 maps id -> animated-texture list (u32 n + n ids).
"""
import struct

DD_SLOTS = 4096
DD_T1, DD_T2, DD_DATA = 0x20, 0x4020, 0xc020


def read_dm(data):
    t1, t2, _z, _v = struct.unpack_from('<IIII', data, 0)
    n = (t2 - t1) // 4
    entries, anims = {}, {}
    for slot, o in enumerate(struct.unpack_from('<%dI' % n, data, t1)):
        if o:
            size = struct.unpack_from('<I', data, o)[0]
            entries[slot] = data[o:o + size]
    n2 = (len(data) - t2) // 4
    for slot, o in enumerate(struct.unpack_from('<%dI' % n2, data, t2)):
        if o:
            cnt = struct.unpack_from('<I', data, o)[0]
            anims[slot] = data[o:o + 4 + 4 * cnt]
    return entries, anims


def read_dd(data):
    t1, t2 = struct.unpack_from('<II', data, 0)
    entries, anims = {}, {}
    for slot, o in enumerate(struct.unpack_from('<%dI' % DD_SLOTS, data, t1)):
        if o:
            entries[slot] = data[o:o + struct.unpack_from('<I', data, o)[0]]   # face 0 only for cubes
    for slot, o in enumerate(struct.unpack_from('<%dI' % DD_SLOTS, data, t2)):
        if o:
            cnt = struct.unpack_from('<I', data, o)[0]
            anims[slot] = data[o:o + 4 + 4 * cnt]
    return entries, anims


def check_entry(e):
    """Walk an entry's mips; returns (fourcc, w, h, mips, name) or raises."""
    size, f1, _f2, _id, w, h, mips = struct.unpack_from('<I4s4sIHHI', e, 0)
    end = e.index(b'\0', 36)
    p = end + 1
    for _ in range(mips):
        p += 4 + struct.unpack_from('<I', e, p)[0]
    if p != size or size != len(e):
        raise ValueError('texture entry size mismatch')
    return f1, w, h, mips, e[36:end].decode('latin1')


def write_dd(entries, anims):
    t1 = [0] * DD_SLOTS
    t2 = [0] * DD_SLOTS
    body = bytearray()
    def pad():                                   # Dog Days keeps entries 16-byte aligned
        body.extend(b'\0' * ((-len(body)) % 16))
    for slot in sorted(entries):
        t1[slot] = DD_DATA + len(body); body += entries[slot]; pad()
    for slot in sorted(anims):
        t2[slot] = DD_DATA + len(body); body += anims[slot]; pad()
    head = struct.pack('<IIII', DD_T1, DD_T2, 0, 0).ljust(DD_T1, b'\0')
    out = head + struct.pack('<%dI' % DD_SLOTS, *t1) + struct.pack('<%dI' % DD_SLOTS, *t2)
    out = out.ljust(DD_DATA, b'\0')
    return bytes(out) + bytes(body)


CUBE = 0x400
ANIMATED = 0x100


def dd_cube(main, faces):
    """Dog Days cube map: face 0 entry, 32-byte block [slot id, 1 x5, 0, 0], faces 1-5 inline
    (each with id 0 and the cube flag), all 16-byte aligned."""
    def pad(b):
        return b + b'\0' * ((-len(b)) % 16)
    slot = struct.unpack_from('<I', main, 12)[0]
    out = pad(main) + struct.pack('<8I', slot, 1, 1, 1, 1, 1, 0, 0)
    for i, f in enumerate(faces):
        f = bytearray(f)
        struct.pack_into('<I', f, 12, 0)
        struct.pack_into('<I', f, 24, struct.unpack_from('<I', f, 24)[0] | CUBE)
        out += bytes(f) if i == len(faces) - 1 else pad(bytes(f))
    return out


def convert(dm_data):
    """Dead Men keeps cube maps as 6 separate textures plus a face list in table 2;
    Dog Days stores the faces inline after the first one (see dd_cube)."""
    entries, lists = read_dm(dm_data)
    data_flags = dict(entries)
    if max(list(entries) + list(lists) + [0]) >= DD_SLOTS:
        raise ValueError('texture id out of range for Dog Days')
    for e in entries.values():
        check_entry(e)
    out_entries = {}
    for slot, e in entries.items():                 # drop the animation flag everywhere
        f = struct.unpack_from('<I', e, 24)[0]
        if f & ANIMATED:
            e = bytearray(e); struct.pack_into('<I', e, 24, f & ~ANIMATED); e = bytes(e)
        out_entries[slot] = e
    entries = dict(out_entries)
    cubes = 0
    animated = 0
    for slot, blob in lists.items():
        n = struct.unpack_from('<I', blob, 0)[0]
        ids = struct.unpack_from('<%dI' % n, blob, 4)
        flags = struct.unpack_from('<I', data_flags[slot], 24)[0]
        if flags & ANIMATED and not flags & CUBE:
            # animated texture (frame list): Dog Days stores these differently, so keep the
            # first frame as a static texture
            animated += 1
            continue
        if n != 6 or ids[0] != slot or not (struct.unpack_from('<I', entries[slot], 24)[0] & CUBE):
            raise ValueError('unexpected cube map layout at slot %d' % slot)
        out_entries[slot] = dd_cube(entries[slot], [entries[i] for i in ids[1:]])
        cubes += 1
    # any other texture carrying the cube flag would make Dog Days expect inline faces
    for slot, e in entries.items():
        if slot not in lists and struct.unpack_from('<I', e, 24)[0] & CUBE:
            raise ValueError('cube-flagged texture %d without faces' % slot)
    out = write_dd(out_entries, {})
    e2, a2 = read_dd(out)
    if any(e2[k] != out_entries[k][:len(e2[k])] for k in entries) or a2:
        raise ValueError('texture round-trip mismatch')
    simulate_dd_loader(out)
    return out, len(entries), cubes


def simulate_dd_loader(data):
    """Walk a .TEX exactly the way Dog Days' loader does (sequential, slot order, inline
    cube faces). Returns (textures, cubes) or raises with the first problem found."""
    t1off = struct.unpack_from('<I', data, 0)[0]
    t1 = struct.unpack_from('<%dI' % DD_SLOTS, data, t1off)
    pos = DD_DATA
    n = cubes = 0
    for slot in range(DD_SLOTS):
        if not t1[slot]:
            continue
        if pos != t1[slot]:
            raise ValueError('slot %d: loader at %#x but table says %#x' % (slot, pos, t1[slot]))
        size = struct.unpack_from('<I', data, pos)[0]
        if size > 0x2000000 or pos + size > len(data):
            raise ValueError('slot %d: bad entry size %d' % (slot, size))
        check_entry(data[pos:pos + size])
        flags = struct.unpack_from('<I', data, pos + 24)[0]
        pos += (size + 15) & ~15
        n += 1
        if flags & CUBE:
            blk = struct.unpack_from('<6I', data, pos)
            if blk[0] != slot:
                raise ValueError('slot %d: cube block names slot %d' % (slot, blk[0]))
            pos += 0x20
            for f in blk[1:]:
                if f:
                    fs = struct.unpack_from('<I', data, pos)[0]
                    if fs > 0x2000000:
                        raise ValueError('slot %d: bad cube face size' % slot)
                    check_entry(data[pos:pos + fs])
                    pos += (fs + 15) & ~15
            cubes += 1
    return n, cubes
