"""
Room data that lives outside the scene files (Dead Men -> Dog Days).

Gates. A ZROOM's own properties are, in order: u32 gate count, u8 list count, u32, three enums,
a container, two bools, u32 gate-array offset, u32 list-array offset, a string, (Dog Days: one
more u32), float[3]. Both offsets are byte offsets into the level's .buf. A gate record is
  +0x00 four corners (12 floats)   +0x30 u32 REF id of the neighbour room
  +0x34 u16   +0x36 u8 flags (2 = has a neighbour)   +0x37 u8
which is all of Dead Men's 0x38 bytes. Dog Days records are 0x74 bytes and add
  +0x38 centre   +0x44 half extents   +0x50 3x3 frame
The post-load room fix-up walks the array with the game's own stride (kl2 0x48e910, Dead Men
0x50ad00), so Dead Men gates must be re-emitted. The added floats follow from the corners; the
rule below reproduces all 1569 gates of Dog Days' own levels.

Room index (.rmi, .rmc). An octree header, 16-byte leaf items {u32 offset of a record, 6 x u16
bounds}, then one record per item: a room's box, with the room's REF id at +0x4c. Records are
0x54 bytes in Dead Men and 0x58 in Dog Days (one more u32, always 0).

Both files refer to rooms by REF id. Ids follow the .gms cluster table, so they stay valid only
while kl_gms leaves that table as Dead Men had it, and the entity they name must still be a room
in Dog Days (the engine calls ZROOM-only virtuals on it: the crash at kl2 0x719884).
"""
import math, struct
from kl_prp import Prp, units

DM_GATE, DD_GATE = 0x38, 0x74
DM_BOX, DD_BOX = 0x54, 0x58


def _sub(a, b): return [a[i] - b[i] for i in range(3)]
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def _unit(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return [x / n for x in a]


def gate_frame(c):
    """Four corners -> (centre, half extents, three rows) as Dog Days stores them."""
    centre = [sum(p[i] for p in c) / 4.0 for i in range(3)]
    row0 = _unit(_cross(_sub(c[1], c[0]), _sub(c[2], c[1])))          # the gate's normal
    up = _sub([0.0, 1.0, 0.0], [row0[1] * x for x in row0])            # world up, in the gate's plane
    row1 = _unit(up) if _dot(up, up) > 1e-6 else [1.0, 0.0, 0.0]       # a horizontal gate uses +X
    row2 = _cross(row1, row0)
    def half(axis):
        pr = [_dot(_sub(q, centre), axis) for q in c]
        return (max(pr) - min(pr)) / 2.0
    return centre, [half(row2), half(row1), half(row0)], [row0, row1, row2]


def dd_gate(rec):
    """One Dead Men gate record -> the Dog Days record."""
    f = struct.unpack_from('<12f', rec)
    centre, ext, rows = gate_frame([f[0:3], f[3:6], f[6:9], f[9:12]])
    return rec[:DM_GATE] + struct.pack('<15f', *(centre + ext + rows[0] + rows[1] + rows[2]))


def convert_gates(prp, classes, dd, buf):
    """prp: converted .prp bytes; classes: Dog Days class name of each node; buf: the level's .buf.
    Appends every room's gates to the .buf in Dog Days' form and points the room at them.
    Returns (prp bytes, buf bytes, number of gates)."""
    p = Prp(prp)
    buf = bytearray(buf)
    total = 0
    for node, cls in zip(p.nodes(), classes):
        if 'ZROOM' not in dd.bases(cls):
            continue
        own = [i for i, f in enumerate(dd.fields(cls)) if f.owner == 'ZROOM']
        us = [list(u) for u in units(node['props'][1:-1])]
        n = struct.unpack('<I', us[own[0]][0][1])[0]
        off = struct.unpack('<I', us[own[9]][0][1])[0]
        # Dog Days stores 0 here in every room; Dead Men a non-zero value in rooms that have
        # neighbour lists. Meaning unknown: following Dog Days is an ASSUMPTION.
        us[own[2]] = [(0x09, b'\0\0\0\0')]
        if n:
            if off + n * DM_GATE > len(buf):
                raise ValueError('room gates lie outside the .buf')
            buf += b'\0' * (-len(buf) % 16)
            us[own[9]] = [(0x09, struct.pack('<I', len(buf)))]
            for k in range(n):
                buf += dd_gate(bytes(buf[off + k * DM_GATE:off + (k + 1) * DM_GATE]))
            total += n
        node['props'] = [(0x02, b'')] + [t for u in us for t in u] + [(0x7e, b'')]
    return p.serialize(), bytes(buf), total


def _items(data):
    """(offset of the leaf items, offset of the first record): items run up to the lowest offset
    any of them names."""
    ioff = struct.unpack_from('<I', data, 0)[0]
    o, rec0 = ioff, len(data)
    while o < rec0:
        rec0 = min(rec0, struct.unpack_from('<I', data, o)[0])
        o += 16
    return ioff, rec0


def convert_index(data):
    """.rmi / .rmc: room boxes 0x54 -> 0x58 bytes, leaf items repointed."""
    ioff, rec0 = _items(data)
    n = (rec0 - ioff) // 16
    if rec0 != ioff + 16 * n or len(data) - rec0 != DM_BOX * n:
        raise ValueError('room index does not have Dead Men\'s layout')
    out = bytearray(data[:rec0])
    for o in range(ioff, rec0, 16):
        v = struct.unpack_from('<I', out, o)[0]
        if (v - rec0) % DM_BOX:
            raise ValueError('room index item does not point at a record')
        struct.pack_into('<I', out, o, rec0 + DD_BOX * ((v - rec0) // DM_BOX))
    for k in range(n):
        out += data[rec0 + k * DM_BOX:rec0 + (k + 1) * DM_BOX] + b'\0\0\0\0'
    return bytes(out)


def box_rooms(data, size):
    """REF ids of the rooms an index names (first id of each record)."""
    ioff, rec0 = _items(data)
    return [struct.unpack_from('<I', data, o + 0x4c)[0] for o in range(rec0, len(data), size)]
