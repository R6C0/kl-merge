"""
Spatial files of a level: .oct, .rmi, .rmc (Dead Men and Dog Days alike unless noted).
Read -> model -> write is byte-identical for every stock level of both games (22 Dog Days,
20 Dead Men: 42 .oct, 42 .rmi, 42 .rmc); "N/N" below are counts over those files.

ONE TREE FORMAT (ZOctreeCompiled data; kl2 vtable 0xb8fbf0, Dead Men 0x93bea4)
  +0x00 u32 offset of the leaf items = align16(0x14 + 6 * nodes), the gap filled with 0xCD
  +0x04 3 x f32 origin, +0x10 f32 scale
  +0x14 nodes, 6 bytes: w0 = octant (bits 0-2) | leaf count (bits 3-14) | last sibling (bit 15),
        w1 = index of the first child (0 = none; siblings are consecutive up to the one with
        bit 15), w2 = index of the first leaf item (0 when the node has none)
  then  leaf items, 16 bytes: u32 item, u16 min x,y,z, u16 max x,y,z
  Stock files (67,785 trees): the nodes reachable from node 0 are exactly the stored ones, every
  item belongs to one node, siblings have distinct octants in ascending order, depth <= 14.

How the engine walks it (the only readers of nodes and items):
  quantise   q = trunc((p - origin) * scale + 32768.0)              (0x77a2b0, const 0xb41528)
  cells      the root is centred on 0x8000. A child at depth d (root = 0) is centred on its
             parent's centre -/+ (0x8000 >> d) per axis (octant bit 0 = +x, 1 = +y, 2 = +z) and
             is entered through a LOOSE cell of half size L = 0x10000 >> d around that centre.
  point      0x719850 (slot 9, 0x77a2b0): a node's items are reported when min <= q <= max on
             every axis; a child is entered when centre - L <= q < centre + L.
  box        0x699e00 (slot 7, 0x566ff0: qmin = trunc(min), qmax = trunc(max) + 1): item when
             qmin < max and qmax > min; child when qmin < centre + L and qmax >= centre - L; a
             child whose loose cell lies inside the query has its WHOLE subtree reported with no
             test (0x70f1f0).
  segment    0x65b5b0 (slot 6, 0x5f0140): same cells, tested as boxes against the segment; the
             hit children of one node are sorted in a local array, so a node must not have more
             children than the eight octants.
  all, map   0x70f1f0 (slot 8) reports every item; 0x4f7ef0 (slot 5) rewrites every item u32
             through a callback (the room loader passes the identity, 0x5c6520).
  So a tree is VALID when every item's box lies inside the loose cell of the node that holds it
  (true for all 974,893 stock items) - nothing else is assumed. That is the standard loose
  octree; build_tree() makes such trees. Leaf count is 12 bits, node and item indices 16 bits.

.oct
  16-byte header: four u32 1 (42/42; the loader only tests the first for non-zero, 0x689da3).
  Room trees: FIVE slots per room. Slot = u32 size; size 0 -> 12 zero bytes; else f32 scale,
    3 x f32 origin (copies of the tree's own), 12 zero bytes, the tree (size bytes, always a
    multiple of 16) - ZROOM loader 0x67ec50. Items are entity SLOT ids (see below).
    Room order (312,699 items, 0 exceptions): the scene root first, then the ZROOM-derived
    entities depth first, the children of an entity taken in REVERSE scene order - room_order().
    Membership: an entity is listed by its NEAREST room ancestor (the root when there is none).
    Which tree: 0 = pool category 1 (ZSTDOBJ / ZSHAPE families), 1 = category 2 (lights),
    2 = empty in all 978 sets (ASSUMPTION: category 3), 3 = category 0 (groups),
    4 = rooms (ZROOM-derived children; kl_gms.category gives the category). No entity is in two
    trees. Not every entity is listed: an entity is listed only if its parent is (0 exceptions
    for categories 0 and 1, 35 lights), tree 0 wants a model (27 exceptions) and pool group 0
    (449). What else excludes an entity (in Dog Days 7 % of the remaining category-1 entities,
    26 % of the groups, 55 % of the lights) is NOT established: no .gms record flag decides
    it. Copy membership from the source level instead of deriving it.
    Item bounds are the entity's world box in the tree's frame.
  Records (ZOctreeCompiled objects, loaded in place by 0x8300f0 until a u32 -1):
    +0x00 u32 record size   +0x04 u32 stale vtable (0x01e15844 / Dead Men 0x017136f8; stamped
    at load)   +0x08 origin, +0x14 scale (copies)   +0x18 u32 stale pointer   +0x1c u32 0
    +0x20 the tree. Each record is referenced exactly once by the .prm: a 64-byte chunk of
    type 7 (word at +2) holds (record offset + 4) | 1 at +0x1c (0 when it has no octree) -
    65,518 / 65,518 records. Record order is free; only these offsets matter.
  u32 -1, then the tail: {u32 first triangle, u32 .prm chunk index} pairs (0x4d82f0 keeps
    pointer and count). A record's item u32 is the BYTE offset of a pair (8 * k); every pair
    is used by exactly one item. The chunk is a 64-byte type-8 object (121,951 / 121,951)
    and the pair names its triangles [first, first + 32): for every object the pairs are
    exactly 32 * k for k < ceil(triangles / 32). Tail order is free (items index it).

.rmi / .rmc (room index, queried by point: callbacks 0x927b30 / 0x927c70)
  One tree whose items are file offsets of the box records that follow the items, one item
  per record. Record 0x58 bytes in Dog Days, 0x54 in Dead Men (no last dword):
    +0x00 u32 1 = axis aligned (0: use the matrix)   +0x04 9 x f32 matrix   +0x28 centre
    +0x34 second point   +0x40 half extents
    +0x4c u32 slot id of the room: a ZROOM-derived entity in 2,659 / 2,659 records
    +0x50 u32 optional second slot id: 0, or a ZBOUND (186 records, .rmi only)
    +0x54 u32 0 (Dog Days only; 1,557 records)
  All item bounds lie in 0x4000..0xbfff (84 / 84 files); larger boxes are clamped to it, so a
  point outside that range is in no room. Not every room has a box. Record order is free
  (items carry the offsets). The model keeps items as record indices.

SLOT ids are not the .gms record's +0x30 number. id = 2 + first slot of pool
[category + 8 * pool group] of the parent group's block in the .gms cluster table (blocks and
pools laid out cumulatively) + position among the earlier siblings in that pool; the root is 1.
Any change to the entity table or the cluster table renumbers them: remap_ids().
"""
import math, struct
from collections import deque

FILL = 0xcd
MAXDEPTH = 14                       # deepest node in any stock tree
NODE_MAX = 0xfff                    # 12-bit leaf count
VTABLE = {'dd': 0x01e15844, 'dm': 0x017136f8}
BOX = {'dd': 0x58, 'dm': 0x54}


def _align(n):
    return (n + 15) & ~15


class Tree:
    """origin (3 floats), scale, nodes [[w0, w1, w2]], items [[item, x0, y0, z0, x1, y1, z1]]
    (bounds quantised). `fill` is the gap between nodes and items as found in the file."""

    def __init__(self, origin, scale, nodes, items, fill=None):
        self.origin, self.scale, self.nodes, self.items = tuple(origin), scale, nodes, items
        self.fill = fill if fill is not None else bytes([FILL]) * (_align(0x14 + 6 * len(nodes)) - 0x14 - 6 * len(nodes))

    @classmethod
    def parse(cls, data, off, size=None, count=None):
        """The tree at `off`: `size` bytes in all, or `count` items."""
        ioff, ox, oy, oz, sc = struct.unpack_from('<I4f', data, off)
        if count is None:
            if ioff > size or (size - ioff) % 16:
                raise ValueError('octree at %#x: bad item offset' % off)
            count = (size - ioff) // 16
        room = (ioff - 0x14) // 6
        nodes, todo = {}, [0]
        while todo:                                     # the nodes the engine can reach
            i = todo.pop()
            while True:
                if i >= room or i in nodes:
                    raise ValueError('octree at %#x: bad node index %d' % (off, i))
                nodes[i] = list(struct.unpack_from('<3H', data, off + 0x14 + 6 * i))
                if nodes[i][1]:
                    todo.append(nodes[i][1])
                if i == 0 or nodes[i][0] & 0x8000:
                    break
                i += 1
        n = len(nodes)
        if sorted(nodes) != list(range(n)):
            raise ValueError('octree at %#x: unreachable nodes' % off)
        items = [list(struct.unpack_from('<I6H', data, off + ioff + 16 * k)) for k in range(count)]
        for w0, w1, w2 in nodes.values():
            if w2 + ((w0 >> 3) & NODE_MAX) > count:
                raise ValueError('octree at %#x: node items out of range' % off)
        return cls((ox, oy, oz), sc, [nodes[i] for i in range(n)], items,
                   bytes(data[off + 0x14 + 6 * n:off + ioff]))

    def item_offset(self):
        return 0x14 + 6 * len(self.nodes) + len(self.fill)

    def pack(self):
        out = struct.pack('<I4f', self.item_offset(), *self.origin, self.scale)
        out += b''.join(struct.pack('<3H', *n) for n in self.nodes) + self.fill
        return out + b''.join(struct.pack('<I6H', *i) for i in self.items)

    # --- the engine's walks -------------------------------------------------------------
    def quantise(self, p):
        """World point -> the engine's integer coordinates (0x77a2b0)."""
        return tuple(int((p[a] - self.origin[a]) * self.scale + 32768.0) for a in range(3))

    def world(self, q):
        return tuple((q[a] - 32768.0) / self.scale + self.origin[a] for a in range(3))

    def _children(self, i, c, depth):
        """(node, centre) of the children of node i, which is at `depth` with centre c."""
        j, h = self.nodes[i][1], 0x8000 >> (depth + 1)
        while j:
            o = self.nodes[j][0]
            yield j, tuple(c[a] + (h if o >> a & 1 else -h) for a in range(3))
            if o & 0x8000:
                break
            j += 1

    def _own(self, i):
        w0, _w1, w2 = self.nodes[i]
        return self.items[w2:w2 + ((w0 >> 3) & NODE_MAX)]

    def cells(self):
        """(node, depth, centre, loose half size) of every node, root first."""
        todo = [(0, 0, (0x8000,) * 3)]
        while todo:
            i, d, c = todo.pop()
            yield i, d, c, 0x10000 >> d
            todo += [(j, d + 1, cc) for j, cc in self._children(i, c, d)]

    def point(self, q):
        """Items reported for the quantised point q, in the engine's order (0x719850)."""
        out, todo = [], [(0, 0, (0x8000,) * 3)]
        while todo:
            i, d, c = todo.pop()
            out += [it[0] for it in self._own(i) if all(it[1 + a] <= q[a] <= it[4 + a] for a in range(3))]
            L = 0x10000 >> (d + 1)
            kids = [(j, d + 1, cc) for j, cc in self._children(i, c, d)
                    if all(cc[a] - L <= q[a] < cc[a] + L for a in range(3))]
            todo += reversed(kids)
        return out

    def box(self, lo, hi):
        """Items reported for the quantised box lo..hi (0x699e00; the caller 0x566ff0 passes
        trunc(min) and trunc(max) + 1)."""
        out, todo = [], [(0, 0, (0x8000,) * 3, False)]
        while todo:
            i, d, c, whole = todo.pop()
            out += [it[0] for it in self._own(i)
                    if whole or all(lo[a] < it[4 + a] and hi[a] > it[1 + a] for a in range(3))]
            L = 0x10000 >> (d + 1)
            for j, cc in self._children(i, c, d):
                if whole:
                    todo.append((j, d + 1, cc, True))
                elif all(lo[a] < cc[a] + L and hi[a] >= cc[a] - L for a in range(3)):
                    todo.append((j, d + 1, cc, all(lo[a] <= cc[a] - L and hi[a] >= cc[a] + L for a in range(3))))
        return out

    def check(self):
        """Raises unless the tree is one the engine walks correctly (module docstring)."""
        seen = [0] * len(self.items)
        for i, d, c, L in self.cells():
            if d > 16:
                raise ValueError('octree deeper than the 16-bit coordinates')
            if d == 0:
                L = 0x8000
            kids = [self.nodes[j][0] & 7 for j, _ in self._children(i, c, d)]
            if len(set(kids)) != len(kids):
                raise ValueError('node %d: two children in one octant' % i)
            w2 = self.nodes[i][2]
            for k, it in enumerate(self._own(i)):
                seen[w2 + k] += 1
                if not all(c[a] - L <= it[1 + a] <= it[4 + a] <= c[a] + L - 1 for a in range(3)):
                    raise ValueError('item %#x lies outside the cell of node %d' % (it[0], i))
        if any(s != 1 for s in seen):
            raise ValueError('octree items not owned by exactly one node')
        return self


# --- building ---------------------------------------------------------------------------

def quantise_box(origin, scale, lo, hi):
    """World box -> quantised bounds as the point walk needs them (every point of the box maps
    inside), clamped to the 16-bit range like the stock catch-all boxes."""
    q = [math.floor((p[a] - origin[a]) * scale + 32768.0) for p in (lo, hi) for a in range(3)]
    return [min(max(v, 0), 0xffff) for v in q]


def build_tree(items, origin, scale, quantised=False, leaf=8):
    """items: [(item, (min x, y, z), (max x, y, z))] in world space (or [(item, x0, y0, z0, x1,
    y1, z1)] already quantised) -> Tree. Loose octree: an item goes down into the child its centre
    lies in for as long as its box fits that child's loose cell and the node has more than
    `leaf` items. A node that would keep more than 4095 items first hands the surplus to any
    other child whose cell holds them, then to its parent (whose cell contains its own). Only
    the root cannot pass items on: OverflowError (use a smaller scale - with everything inside
    0x4000..0xbfff every item fits a child of the root)."""
    if quantised:
        its = [list(i) for i in items]
    else:
        its = [[i] + quantise_box(origin, scale, lo, hi) for i, lo, hi in items]

    def place(d, c, mine):
        """-> (items kept here, [(octant, subtree)], surplus for the parent)"""
        stay, kids = mine, {}
        if len(mine) > leaf and d < MAXDEPTH:
            stay, h, L = [], 0x8000 >> (d + 1), 0x10000 >> (d + 1)
            centre = lambda o: tuple(c[a] + (h if o >> a & 1 else -h) for a in range(3))
            fits = lambda it, cc: all(cc[a] - L <= it[1 + a] and it[4 + a] <= cc[a] + L - 1 for a in range(3))
            for it in mine:
                o = sum((it[1 + a] + it[4 + a] + 1 >= 2 * c[a]) << a for a in range(3))
                (kids.setdefault(o, []) if fits(it, centre(o)) else stay).append(it)
            if len(stay) > NODE_MAX:                    # more large items than one node can hold
                keep = []
                for it in stay:
                    o = next((o for o in range(8) if fits(it, centre(o))), None)
                    (keep if o is None else kids.setdefault(o, [])).append(it)
                stay = keep
            subs = []
            for o in sorted(kids):
                sub = place(d + 1, centre(o), kids[o])
                stay += sub[2]
                subs.append((o, sub))
            kids = subs
        return stay[:NODE_MAX], kids or [], stay[NODE_MAX:]

    root = place(0, (0x8000,) * 3, its)
    if root[2]:
        raise OverflowError('octree root would hold %d items (limit 4095)' % (NODE_MAX + len(root[2])))
    nodes, out, todo = [[0, 0, 0]], [], deque([(0, root)])
    while todo:                                         # breadth first: siblings are consecutive
        ni, (stay, kids, _) = todo.popleft()
        if stay:
            if len(out) > 0xffff:
                raise OverflowError('octree: the first item index of a node does not fit 16 bits')
            nodes[ni][0] |= len(stay) << 3
            nodes[ni][2] = len(out)
            out += stay
        if kids:
            nodes[ni][1] = len(nodes)
            for o, sub in kids:
                todo.append((len(nodes), sub))
                nodes.append([o, 0, 0])
            nodes[-1][0] |= 0x8000
            if len(nodes) > 0xffff:
                raise OverflowError('octree with more than 65535 nodes')
    return Tree(origin, scale, nodes, out)


def requantise(tree, origin, scale):
    """The tree's items with their bounds moved into another frame (never shrinking a box)."""
    if (tuple(origin), scale) == (tree.origin, tree.scale):
        return [list(i) for i in tree.items]
    out = []
    for it in tree.items:
        lo, hi = tree.world(it[1:4]), tree.world([v + 1 for v in it[4:7]])
        a = [math.floor((lo[k] - origin[k]) * scale + 32768.0 + 1e-6) for k in range(3)]
        b = [math.ceil((hi[k] - origin[k]) * scale + 32768.0 - 1e-6) - 1 for k in range(3)]
        out.append([it[0]] + [min(max(v, 0), 0xffff) for v in a + b])
    return out


def _f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def _fits(tree, origin, scale):
    for it in tree.items:
        lo, hi = tree.world(it[1:4]), tree.world([v + 1 for v in it[4:7]])
        for k in range(3):
            if (lo[k] - origin[k]) * scale + 32768.0 < -1e-6 or (hi[k] - origin[k]) * scale + 32768.0 > 65536 + 1e-6:
                return False
    return True


def join_trees(a, b, leaf=8):
    """Two trees (either may be None) -> one tree holding the items of both. The frame is the
    finer of the two that holds the other's items in its 16-bit range, else a new one that puts
    the union of both in the middle half of the range (the stock .rmi layout). Bounds moved to
    another frame are rounded outwards, so a walk of the result reports at least what the two
    trees reported. The result is rebuilt with build_tree."""
    if a is None or b is None:
        t = a or b
        return t and Tree(t.origin, t.scale, [list(n) for n in t.nodes], [list(i) for i in t.items], t.fill)
    frames = [(t.origin, t.scale) for t, other in ((a, b), (b, a)) if _fits(other, t.origin, t.scale)]
    frames.sort(key=lambda f: -f[1])                    # the finer of the two first
    boxes = [(t.world(it[1:4]), t.world([v + 1 for v in it[4:7]])) for t in (a, b) for it in t.items]
    if boxes:
        lo = [min(x[0][k] for x in boxes) for k in range(3)]
        hi = [max(x[1][k] for x in boxes) for k in range(3)]
        half = max(max(hi[k] - lo[k] for k in range(3)) / 2.0, 1e-3)
        for shrink in (1, 2, 4, 8):                     # each step frees room below the root
            frames.append((tuple(_f32((lo[k] + hi[k]) / 2.0) for k in range(3)), _f32(16000.0 / half / shrink)))
    err = None
    for origin, scale in frames:
        try:
            return build_tree(requantise(a, origin, scale) + requantise(b, origin, scale), origin, scale, True, leaf)
        except OverflowError as e:
            err = e
    raise err or OverflowError('no frame')


def join_room_trees(a, b, leaf=8):
    """Two sets of five room trees (the root's of level A and of level B, ids already in the
    joined level's numbering) -> the merged set."""
    return [join_trees(x, y, leaf) for x, y in zip(a, b)]


def room_order(parents, is_room):
    """Order of the five-tree sets in the .oct. parents[i] = scene index of entity i's parent
    (-1 = scene root), is_room[i] = ZROOM-derived. -> [-1 (root), entity index, ...]."""
    kids = {}
    for i, p in enumerate(parents):
        kids.setdefault(p, []).append(i)
    out, todo = [-1], list(kids.get(-1, ()))
    while todo:
        i = todo.pop()                                  # last child first
        if is_room[i]:
            out.append(i)
        todo += kids.get(i, ())
    return out


# --- .oct -----------------------------------------------------------------------------------

class Record:
    """One ZOctreeCompiled record: stale vtable and pointer dwords (overwritten at load) + tree."""
    def __init__(self, vtable, pointer, tree):
        self.vtable, self.pointer, self.tree = vtable, pointer, tree

    def pack(self):
        t = self.tree.pack()
        return struct.pack('<II4fII', 0x20 + len(t), self.vtable, *self.tree.origin, self.tree.scale,
                           self.pointer, 0) + t


class Oct:
    """header (4 u32), rooms [[Tree or None] * 5] in room_order(), records [Record],
    tail [[first triangle, .prm chunk index]]. Record items are tail INDICES in the model
    (the file stores 8 * index)."""

    def __init__(self, header, rooms, records, tail):
        self.header, self.rooms, self.records, self.tail = header, rooms, records, tail

    @classmethod
    def parse(cls, data):
        header, o, rooms = struct.unpack_from('<4I', data, 0), 0x10, []
        while True:
            size = struct.unpack_from('<I', data, o)[0]
            # a record has its scale at +0x14, a room tree zeros (1,337 + 846 trees)
            if size == 0xffffffff or (size and struct.unpack_from('<I', data, o + 0x14)[0]):
                break
            room = []
            for _ in range(5):
                size = struct.unpack_from('<I', data, o)[0]
                if not size:
                    if any(data[o + 4:o + 16]):
                        raise ValueError('.oct: empty room tree at %#x is not empty' % o)
                    room.append(None)
                    o += 16
                    continue
                t = Tree.parse(data, o + 0x20, size)
                if data[o + 4:o + 8] != data[o + 0x30:o + 0x34] or data[o + 8:o + 0x14] != data[o + 0x24:o + 0x30] \
                        or any(data[o + 0x14:o + 0x20]) or size % 16:
                    raise ValueError('.oct: room tree header at %#x' % o)
                room.append(t)
                o += 0x20 + size
            rooms.append(room)
        records = []
        while struct.unpack_from('<I', data, o)[0] != 0xffffffff:
            size, vt = struct.unpack_from('<II', data, o)
            ptr, zero = struct.unpack_from('<II', data, o + 0x18)
            t = Tree.parse(data, o + 0x20, size - 0x20)
            if zero or data[o + 8:o + 0x18] != data[o + 0x24:o + 0x34]:
                raise ValueError('.oct: record header at %#x' % o)
            for it in t.items:
                if it[0] % 8:
                    raise ValueError('.oct: record item is not a tail offset')
                it[0] //= 8
            records.append(Record(vt, ptr, t))
            o += size
        if (len(data) - o - 4) % 8:
            raise ValueError('.oct: tail is not made of pairs')
        tail = [list(struct.unpack_from('<II', data, k)) for k in range(o + 4, len(data), 8)]
        if any(it[0] >= len(tail) for r in records for it in r.tree.items):
            raise ValueError('.oct: record item beyond the tail')
        return cls(header, rooms, records, tail)

    def _parts(self):
        out = [struct.pack('<4I', *self.header)]
        for room in self.rooms:
            for t in room:
                if t is None:
                    out.append(bytes(16))
                else:
                    b = t.pack()
                    b += bytes(-len(b) % 16)
                    out.append(struct.pack('<If3f', len(b), t.scale, *t.origin) + bytes(12) + b)
        return out

    def record_refs(self):
        """What the .prm stores at +0x1c of the type-7 chunk owning each record, in order."""
        o, out = sum(len(p) for p in self._parts()), []
        for r in self.records:
            out.append((o + 4) | 1)
            o += 0x20 + r.tree.item_offset() + 16 * len(r.tree.items)
        return out

    def pack(self):
        out = self._parts()
        for r in self.records:
            for it in r.tree.items:
                it[0] *= 8
            out.append(r.pack())
            for it in r.tree.items:
                it[0] //= 8
        out.append(b'\xff\xff\xff\xff')
        out += [struct.pack('<II', *p) for p in self.tail]
        return b''.join(out)


def select_records(oct, keep, chunk_map=None):
    """A copy of `oct` with only the records whose index is in `keep` (in that order) and only
    the tail pairs they use; chunk_map (dict or None) renumbers the pairs' .prm chunk indices.
    -> (Oct, {old .prm reference: new .prm reference})."""
    old, records, tail = oct.record_refs(), [], []
    for k in keep:
        r = oct.records[k]
        items = []
        for it in r.tree.items:
            first, chunk = oct.tail[it[0]]
            tail.append([first, chunk if chunk_map is None else chunk_map[chunk]])
            items.append([len(tail) - 1] + it[1:])
        t = r.tree
        records.append(Record(r.vtable, r.pointer, Tree(t.origin, t.scale, [list(n) for n in t.nodes], items, t.fill)))
    new = Oct(oct.header, oct.rooms, records, tail)
    return new, dict(zip((old[k] for k in keep), new.record_refs()))


def append_records(a, b, chunk_map=None, keep=None):
    """Level A's .oct plus the records of level B (all, or the indices in `keep`), B's tail
    merged behind A's. chunk_map: B's .prm chunk index -> its index in the joined .prm.
    -> (Oct, refs_a, refs_b): {old reference: new reference} for the type-7 chunks of A's and
    of B's .prm (+0x1c). A's references change only if its room trees were changed before."""
    part, _ = select_records(b, range(len(b.records)) if keep is None else keep, chunk_map)
    n = len(a.tail)
    for r in part.records:
        for it in r.tree.items:
            it[0] += n
    out = Oct(a.header, a.rooms, a.records + part.records, a.tail + part.tail)
    new, old_b = out.record_refs(), b.record_refs()
    keep = range(len(b.records)) if keep is None else keep
    return (out, dict(zip(a.record_refs(), new)),
            dict(zip((old_b[k] for k in keep), new[len(a.records):])))


# --- .rmi / .rmc ------------------------------------------------------------------------------

class Box:
    """One room box record, kept as bytes; room / second are the two slot ids."""
    def __init__(self, raw):
        self.raw = bytearray(raw)
    room = property(lambda s: struct.unpack_from('<I', s.raw, 0x4c)[0],
                    lambda s, v: struct.pack_into('<I', s.raw, 0x4c, v))
    second = property(lambda s: struct.unpack_from('<I', s.raw, 0x50)[0],
                      lambda s, v: struct.pack_into('<I', s.raw, 0x50, v))

    def sized(self, size):
        """The record in the other game's size (Dog Days adds one zero dword)."""
        return Box(bytes(self.raw[:size]) + bytes(max(size - len(self.raw), 0)))


class RoomIndex:
    """tree (items are indices into boxes), boxes [Box], size of a record."""

    def __init__(self, tree, boxes, size):
        self.tree, self.boxes, self.size = tree, boxes, size

    @classmethod
    def parse(cls, data):
        ioff = struct.unpack_from('<I', data, 0)[0]
        n, first = 0, len(data)
        while ioff + 16 * n < first:                   # items run up to the first record
            first = min(first, struct.unpack_from('<I', data, ioff + 16 * n)[0])
            n += 1
        if first != ioff + 16 * n or not n or (len(data) - first) % n or (len(data) - first) // n not in BOX.values():
            raise ValueError('room index: items and records do not add up')
        size = (len(data) - first) // n
        tree = Tree.parse(data, 0, count=n)
        for it in tree.items:
            if (it[0] - first) % size or not first <= it[0] < len(data):
                raise ValueError('room index: item does not point at a record')
            it[0] = (it[0] - first) // size
        return cls(tree, [Box(data[first + size * k:first + size * (k + 1)]) for k in range(n)], size)

    def pack(self):
        t = self.tree
        first = t.item_offset() + 16 * len(t.items)
        moved = Tree(t.origin, t.scale, t.nodes, [[first + self.size * it[0]] + it[1:] for it in t.items], t.fill)
        return moved.pack() + b''.join(bytes(b.raw) for b in self.boxes)


def join_index(a, b, leaf=8):
    """Room index of level A + the boxes of level B (ids already in the joined numbering; drop
    B's catch-all box first with remap_ids if its room is not kept). Record size is A's."""
    n = len(a.boxes)
    shifted = Tree(b.tree.origin, b.tree.scale, b.tree.nodes, [[it[0] + n] + it[1:] for it in b.tree.items], b.tree.fill)
    return RoomIndex(join_trees(a.tree, shifted, leaf), a.boxes + [x.sized(a.size) for x in b.boxes], a.size)


# --- renumbering ------------------------------------------------------------------------------

def _filter(tree, keep):
    """The tree without the items keep(item) rejects; `keep` returns the new item or None.
    Nodes and item order stay as they are (an emptied node is legal), so every walk returns what
    it did before minus the removed items."""
    new = [keep(it) for it in tree.items]
    before = [0]
    for v in new:
        before.append(before[-1] + (v is not None))
    nodes = []
    for w0, w1, w2 in tree.nodes:
        n = before[w2 + ((w0 >> 3) & NODE_MAX)] - before[w2]
        nodes.append([(w0 & 0x8007) | n << 3, w1, before[w2] if n else 0])
    return Tree(tree.origin, tree.scale, nodes, [v for v in new if v is not None], tree.fill)


def remap_tree(tree, ids, drop=()):
    """Item ids through `ids` (dict old -> new); items whose id is in `drop` are removed. An id
    in neither raises KeyError: a stale id makes the engine call room methods on another class."""
    return _filter(tree, lambda it: None if it[0] in drop else [ids[it[0]]] + it[1:])


def remap_ids(obj, ids, drop=()):
    """Oct or RoomIndex -> the same structure with slot ids renumbered through `ids` and the
    entities in `drop` removed.
    Oct: the room trees' items (records and tail hold no entity ids). The five-tree SETS are not
    touched: dropping or reordering rooms is a list operation on .rooms (see room_order).
    RoomIndex: boxes of a dropped room are removed with their items; a dropped second id is
    cleared to 0."""
    if isinstance(obj, Oct):
        rooms = [[t and remap_tree(t, ids, drop) for t in room] for room in obj.rooms]
        return Oct(obj.header, rooms, obj.records, obj.tail)
    new, boxes = {}, []
    for k, b in enumerate(obj.boxes):
        if b.room in drop:
            continue
        new[k] = len(boxes)
        b = Box(b.raw)
        b.room = ids[b.room]
        if b.second:
            b.second = 0 if b.second in drop else ids[b.second]
        boxes.append(b)
    tree = _filter(obj.tree, lambda it: [new[it[0]]] + it[1:] if it[0] in new else None)
    return RoomIndex(tree, boxes, obj.size)


def read(path):
    """A level zip -> (Oct, RoomIndex of the .rmi, RoomIndex of the .rmc)."""
    import zipfile
    z = zipfile.ZipFile(path)
    member = {n.rsplit('.', 1)[-1].lower(): n for n in z.namelist()}
    return (Oct.parse(z.read(member['oct'])), RoomIndex.parse(z.read(member['rmi'])),
            RoomIndex.parse(z.read(member['rmc'])))
