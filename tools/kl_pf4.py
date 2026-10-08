"""
Navigation mesh of the PF4 pathfinder (Dead Men -> Dog Days).

The mesh is a block inside the unpacked .gms, at the offset in header +0x34: u32 size, then the
data. The scene loader (kl2 0x820300) hands it to 0x538bc0, which builds the PF4::ZData the
database keeps at +0xc. Cover boxes, AI and some 25 other sites use that object without a null
check, so a level without a mesh crashes (kl2 0x5503da, at 73 % of the load).

Both games store 13 arrays, counts first:
  Dead Men  13 x u16 counts + 2 pad bytes; elements of 16 16 12 24 48 20 20 10 2 8 2 2 4 bytes
  Dog Days  13 x u32 counts + 4 pad bytes; elements of 20 20 12 32 72 28 20 16 4 12 4 4 8 bytes
(parsers kaneandlynch 0x4ee810 and kl2 0x63e750; header + arrays equals the size in every stock
level of both games). Dog Days widened the 16-bit indices to 32 bits.

Established from the two parsers: array 3 (nodes) keeps its u8 edge count at +0 and its first
edge moves from s16 +0xa to i32 +0xc; array 9 (edges) has the neighbour node as s16 -> i32 at +0
and a link slot at +4 -> +8; array 5 has a u16 at +0x12 -> +0x18.
ASSUMPTION: every other field mapping below. It follows the size growth (16-bit -> 32-bit,
floats unchanged) and matching value ranges, not the code that uses each field.
Arrays 7, 8, 11 and 12 are empty in the FA maps except one array-7 record in M03; their
mapping is not known and a level that has them is refused.
"""
import struct

DM_SIZE = (16, 16, 12, 24, 48, 20, 20, 10, 2, 8, 2, 2, 4)
DD_SIZE = (20, 20, 12, 32, 72, 28, 20, 16, 4, 12, 4, 4, 8)


def _wide(v):
    """u16 index -> u32, keeping 'none' and the other negative codes negative."""
    return v - 0x10000 & 0xffffffff if v >= 0x8000 else v


def _a01(r):
    a, b, x, y, z = struct.unpack('<hh3f', r)
    return struct.pack('<ii3f', a, b, x, y, z)

def _a3(r):
    n, flag, pad, zero, area, first, x, y, tail = struct.unpack('<BBHIHHIII', r)
    return struct.pack('<BBHIIIIIII', n, flag, pad, zero, _wide(area), _wide(first), x, 0, y, tail)

def _a4(r):
    v = struct.unpack('<12H6f', r)
    return struct.pack('<12I6f', *([_wide(x) for x in v[:12]] + list(v[12:])))

def _a5(r):
    x, y, z, a, b, idx, _runtime = struct.unpack('<3fHHHH', r)
    return struct.pack('<3fIIIHH', x, y, z, _wide(a), _wide(b), _wide(idx), 0, 0)

def _a9(r):
    node, b, link = struct.unpack('<hHI', r)
    return struct.pack('<iII', node, b, link)

def _a10(r):
    return struct.pack('<I', _wide(struct.unpack('<H', r)[0]))

RECORD = {0: _a01, 1: _a01, 2: bytes, 3: _a3, 4: _a4, 5: _a5, 6: bytes, 9: _a9, 10: _a10}


def counts(block, wide):
    """The 13 array counts of a mesh block (without its size dword)."""
    return struct.unpack_from('<13I' if wide else '<13H', block, 0)


def convert(block):
    """Dead Men mesh data -> Dog Days mesh data (both without the leading size dword)."""
    n = counts(block, False)
    if 28 + sum(c * s for c, s in zip(n, DM_SIZE)) != len(block):
        raise ValueError('navigation mesh does not have Dead Men\'s layout')
    out = [struct.pack('<13I4x', *n)]
    o = 28
    for k, c in enumerate(n):
        if c and k not in RECORD:
            raise ValueError('navigation mesh array %d is not empty: its Dog Days form is unknown' % k)
        for _ in range(c):
            out.append(RECORD[k](block[o:o + DM_SIZE[k]]))
            o += DM_SIZE[k]
    out = b''.join(out)
    if len(out) != 56 + sum(c * s for c, s in zip(n, DD_SIZE)):
        raise ValueError('navigation mesh conversion came out the wrong size')
    return out
