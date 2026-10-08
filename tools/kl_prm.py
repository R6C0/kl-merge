"""
Kane & Lynch .prm geometry converter (Dead Men -> Dog Days).

Container (both games): chunk 0 is the 16-byte header [table ofs][count][table ofs][0];
chunks are 16-byte aligned and the chunk table (count x [ofs, size, refs, 0]) is at the end.

Model graph (both games):  model (64 B) -> object list -> object (64 B, +0x28 -> ptr chunk)
                            -> ptr chunk [desc] -> mesh descriptor -> vertex / index chunks
Vertex layouts (0x10, 0x24, 0x28, 0x34 stride) and index chunks are identical.

The one structural change is the mesh descriptor:
  Dead Men  32 B: nverts, vertex chunk, n (multiple of 3, unused by Dog Days), index chunk, 0 x4
  Dog Days  48 B: nverts, vertex chunk, 0, 0, 0, lighting record (optional), index chunk, 0 x5
"""
import struct


def read(data):
    t, n, t2, z = struct.unpack_from('<IIII', data, 0)
    table = [list(struct.unpack_from('<4I', data, t + 16 * i)) for i in range(n)]
    chunks = [data[o:o + s] for o, s, _r, _z in table]
    return table, chunks


def _is_index(chunks, i):
    c = chunks[i]
    if len(c) < 8:
        return False
    a, cnt = struct.unpack_from('<HH', c, 0)
    return a == 1 and 4 + 2 * cnt <= len(c)


def find_descriptors(chunks, size):
    n = len(chunks)
    out = []
    for i, c in enumerate(chunks):
        if i == 0 or len(c) != size:
            continue
        u = struct.unpack_from('<%dI' % (size // 4), c)
        if size == 32:
            nv, vc, ic, tail = u[0], u[1], u[3], u[4:]
        else:
            nv, vc, ic, tail = u[0], u[1], u[6], (u[2], u[3], u[4]) + u[7:]
        if nv > 0 and 0 < vc < n and 0 < ic < n and _is_index(chunks, ic) and not any(tail) \
                and len(chunks[vc]) >= nv * 16:
            out.append(i)
    return out


def write(table, chunks):
    n = len(chunks)
    body = bytearray(16)                       # chunk 0 = header, filled in last
    offs = [0] * n
    for i in range(1, n):
        body.extend(b'\0' * ((-len(body)) % 16))
        offs[i] = len(body)
        body += chunks[i]
    body.extend(b'\0' * ((-len(body)) % 16))
    tpos = len(body)
    for i in range(n):
        size = 16 if i == 0 else len(chunks[i])
        body += struct.pack('<4I', offs[i], size, table[i][2], 0)
    struct.pack_into('<4I', body, 0, tpos, n, tpos, 0)
    return bytes(body)


def convert(dm_data):
    table, chunks = read(dm_data)
    descs = find_descriptors(chunks, 32)
    for i in descs:
        u = struct.unpack_from('<8I', chunks[i])
        chunks[i] = struct.pack('<12I', u[0], u[1], 0, 0, 0, 0, u[3], 0, 0, 0, 0, 0)
    out = write(table, chunks)
    # verify: same chunk count, every descriptor now in Dog Days form, everything else byte-identical
    t2, c2 = read(out)
    if len(c2) != len(chunks):
        raise ValueError('chunk count changed')
    if sorted(find_descriptors(c2, 48)) != sorted(descs):
        raise ValueError('descriptor conversion check failed')
    _, orig = read(dm_data)
    ds = set(descs)
    if any(c2[i] != orig[i] for i in range(1, len(orig)) if i not in ds):
        raise ValueError('non-descriptor chunk changed')
    return out, len(descs)
