"""
.gms scene file (Dead Men -> Dog Days).

File: u32 uncompressed size, u32 file size, u8 0, raw deflate stream.
Header of the uncompressed data (16 x u32) is the same in both games except:
  +0x34  offset of the sound-occlusion geometry list. Dog Days reads each block as a
         13-count header + arrays; Dead Men uses an older layout, which crashes Dog Days.
         0 = "none" (the loader skips it).
  +0x38  optional offset; Dog Days levels use -1 here.
"""
import struct, zlib


def unpack(f):
    raw_len, file_len = struct.unpack_from('<II', f, 0)
    raw = zlib.decompressobj(-15).decompress(f[9:])
    if len(raw) != raw_len:
        raise ValueError('gms size mismatch')
    return raw


def pack(raw):
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    z = c.compress(raw) + c.flush()
    return struct.pack('<II', len(raw), 9 + len(z)) + b'\0' + z


# Dead Men classes Dog Days doesn't register -> Dog Days class with the same layout
RETYPE = {
    0x100486: 0x100001,     # ZIngameMapGroup -> ZGROUP (as a ZROOM its record has no portal data and Dog Days' room linking crashes)
    # classes Dog Days still has but never saves in a level (layout unknown). Targets keep
    # the "group" bit (0x100000) so the cluster table keeps the same number of blocks.
    # ZROOM stays ZROOM: each room (and ROOT) owns one section of the level's .oct octree, same
    # format in both games. Retyping rooms left their sections unread and Dog Days' octree walk
    # (ZEngineDataBase 0x689d90) ran off the end - the 69% crash on 2026-10-08.
    0x100490: 0x100001,     # ZFFItemTemplateMultistage -> ZGROUP
    0x200110: 0x200002,     # ZSHADOWMESHOBJ  -> ZSTDOBJ
    0x2000fd: 0x200002,     # ZPlant          -> ZSTDOBJ
    0x20010f: 0x200002,     # ZEnvSampler     -> ZSTDOBJ
    0x2000d4: 0x200002,     # ZHavokCar       -> ZSTDOBJ (static car)
    0x800011e: 0x200002,    # ZAMBIENTOCCLUSION -> ZSTDOBJ
}
GROUP = 0x100000


def retype(raw, old, new):
    """Change entity records of type `old` to `new` and merge the type-table counts."""
    h = struct.unpack_from('<16I', raw, 0)
    tab = h[4]
    n = struct.unpack_from('<I', raw, tab)[0]
    ents = [list(struct.unpack_from('<3I', raw, tab + 4 + 12 * i)) for i in range(n)]
    ids = [e[0] for e in ents]
    if old not in ids:
        return 0
    cnt = ents[ids.index(old)][1]
    # entity records: type id at +0x14, node id at +0x30 (record starts 16-aligned)
    done = 0
    for p in range(0, tab, 16):
        if struct.unpack_from('<I', raw, p + 0x14)[0] == old and struct.unpack_from('<I', raw, p)[0] < len(raw):
            struct.pack_into('<I', raw, p + 0x14, new); done += 1
    if done != cnt:
        raise ValueError('expected %d %#x records, found %d' % (cnt, old, done))
    i = ids.index(old)
    if new in ids:
        ents[ids.index(new)][1] += cnt
        ents[i] = ents[-1]; ents.pop()               # drop the old entry
    else:
        ents[i][0] = new
    struct.pack_into('<I', raw, tab, len(ents))
    for k, e in enumerate(ents):
        struct.pack_into('<3I', raw, tab + 4 + 12 * k, *e)
    struct.pack_into('<3I', raw, tab + 4 + 12 * len(ents), 0, 0, 0) if len(ents) < n else None
    return done


def entities(raw):
    t = struct.unpack_from('<I', raw, 0)[0]
    n = struct.unpack_from('<I', raw, t)[0]
    out = []
    for i in range(n):
        decl = struct.unpack_from('<I', raw, t + 4 + 8 * i)[0]
        rec = 4 * (decl & 0xffffff)
        out.append((decl, struct.unpack_from('<I', raw, rec + 0x14)[0], raw[rec + 0x35]))
    return out


def category(tid):
    """Pool category of a class, as kl2 0x829b10 computes it from the class's bases (the same rule
    in Dead Men, 0x42a2c0): ZGROUP family 0; ZSTDOBJ and ZSHAPE families 1, except ZBOUND and
    ZSNDOBJ 3; lights 2; everything else 3. It reproduces every cell of the cluster table of
    every stock level of both games."""
    if tid in (0x200012, 0x20001c):                 # ZBOUND, ZSNDOBJ
        return 3
    return {0x100000: 0, 0x800000: 2, 0x200000: 1, 0x4000000: 1}.get(tid & 0x7ff00000, 3)


def rebuild_clusters(raw):
    """Recompute the cluster table the way Dog Days' entity loader (kl2 0x8ad7c0) consumes it: one
    block of 24 pool counts per group-type entity (plus ROOT's block 0); each entity takes a
    128-byte slot from pool [category + 8 * pool group] of its parent group's block. A pool
    with count 0 gets no memory and the loader dereferences it (crash at 0x8adbba)."""
    ents = entities(raw)
    ctab = struct.unpack_from('<I', raw, 0x14)[0]
    nblocks = struct.unpack_from('<I', raw, ctab)[0]
    blocks = [[0] * 24 for _ in range(nblocks)]
    stack, nxt, pending = [0], 1, None
    for decl, tid, prio in ents:
        for _ in range(decl >> 25):
            stack.pop()
        if pending is not None:
            stack.append(pending); pending = None
        if prio > 2:
            raise ValueError('entity pool group %d out of range' % prio)
        blocks[stack[-1]][category(tid) + 8 * prio] += 1
        blk = None
        if tid & GROUP:
            blk = nxt; nxt += 1
        if decl & 0x1000000:
            if blk is None:
                raise ValueError('non-group entity %#x has children' % tid)
            pending = blk
    if nxt != nblocks:
        raise ValueError('cluster table has %d blocks, entities need %d' % (nblocks, nxt))
    for k, b in enumerate(blocks):
        struct.pack_into('<24I', raw, ctab + 4 + 96 * k, *b)
    return nblocks


def convert(f):
    raw = bytearray(unpack(f))
    for old, new in RETYPE.items():
        retype(raw, old, new)
    rebuild_clusters(raw)
    struct.pack_into('<I', raw, 0x34, 0)
    struct.pack_into('<I', raw, 0x38, 0xffffffff)
    out = pack(bytes(raw))
    if unpack(out) != bytes(raw):
        raise ValueError('gms repack failed')
    return out
