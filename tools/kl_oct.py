"""
.oct room trees (Dead Men -> Dog Days).

File: 16-byte header (4 x u32 1), then for every room of the scene, in scene order with the
scene root first, FIVE trees; then other records up to a u32 -1 and a tail. A tree is
  u32 size; size == 0: 12 more bytes
            size != 0: f32, 24 bytes of bounds, then the tree data padded to 16 bytes
(Dog Days ZROOM method at kl2 0x67ec50, called for each ZROOM by ZEngineDataBase 0x689d90; the
same five-per-room layout parses every stock level of both games.)

The rooms eat their trees one after another, so a room that is retyped to a plain group
(kl_gms.RETYPE) must lose its five trees as well: otherwise Dog Days reads the leftover trees
as the records that follow them and crashes (the 69 % load crash at kl2 0x689ec4).

ASSUMPTION: the scene root is the first room in the file. Dead Men and Dog Days levels parse
either way; with only the root left as a room, a wrong guess gives it another room's trees.
"""
import struct

TREES = 5


def room_trees(data, rooms):
    """[(start, end)] of each room's five trees. Raises if the file does not hold that many."""
    out, o = [], 0x10
    for _ in range(rooms):
        start = o
        for _ in range(TREES):
            size = struct.unpack_from('<I', data, o)[0]
            o += 4 + (4 + 0x18 + ((size + 15) & ~15) if size else 0xc)
            if o + 8 > len(data):
                raise ValueError('.oct ends inside the room trees')
        out.append((start, o))
    return out


def convert(data, keep):
    """keep: one bool per room in scene order, root first. Trees of rooms not kept are removed."""
    spans = room_trees(data, len(keep))
    end = spans[-1][1] if spans else 0x10
    if b'\xff\xff\xff\xff' not in data[end:]:
        raise ValueError('.oct: no terminator after the room trees (room count wrong?)')
    out = data[:0x10] + b''.join(data[a:b] for (a, b), k in zip(spans, keep) if k) + data[end:]
    if len(room_trees(out, sum(keep))) != sum(keep):
        raise ValueError('.oct did not parse back')
    return out
