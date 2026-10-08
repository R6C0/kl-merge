"""
Scene model: the .gms entity file and the .buf it points into (Dead Men and Dog Days alike).

Read both into a tree of entities, write them back byte for byte, remove or add top-level
subtrees and get every table regenerated. Checked on all 103 stock scenes (44 Dog Days, 59 Dead
Men .gms/.buf pairs: levels, menus, loader screens; 60 of them distinct): read -> write is
byte-identical, and no table is read back from the place it is written to except the list pool
and the room pairs, which are what the slot rule below is proved on.

UNPACKED .gms, in file order (hdr = 16 x u32; all blocks 16-aligned, zero padded)
  0x00 header   +0x00 entity table  +0x10 type table  +0x14 cluster table  +0x18 list pool
                +0x1c heap budget   +0x20 tag block   +0x24 dynamic list   +0x28 room pairs
                +0x30 .buf offset of the surface table (start of the .buf tail)
                +0x34 navigation mesh (kl_pf4)        +0x38 .buf offset of an 'FDX' block or -1
                +0x3c REF slot count (above every REF id; highest id + 1 in 46 of 60 scenes)
                +0x04 +0x08 +0x2c = 0, +0x0c = 4 in every scene
  0x40 16 bytes, one constant per game (GAMES[..]['magic']); tells the games apart
  0x50 records  per entity, in scene order: [translation 16 B][rotation 48 B][record 64 B].
                A translation / rotation is written only the first time its bytes occur; later
                entities point at that copy (exact in 103/103: no other sharing, no gaps).
       record   +0x00 name (.buf)  +0x04 rotation, +0x08 translation (.gms offsets)
                +0x0c model: chunk index in the .prm (lights: their light record). For class
                      0x20011b (loader scenes only) it is a BYTE offset in the .prm instead:
                      the loader script text (kl2 0x55a9b0)
                +0x14 class id  +0x1c flags  +0x20 raw data (.buf) or 0  +0x28 aux
                +0x30 REF id  +0x35 pool group (0..2); everything else 0
  cluster table u32 blocks, then 24 x u32 per block: block 0 = children of the scene root, then
                one block per entity whose class has bit 0x100000, in scene order. Cell
                [kl_gms.category(class) + 8 * pool group] counts that block's children.
  list pool     u32 size, then dwords: A, B, C, -1, the lists, C + B dwords of 0xcdcdcdcd.
                A = dwords up to the end of the lists, C = 20000 (Dead Men 16000),
                B = max(40960, 2 * A - 8). A list is [0][elements], an element is
                slot * SLOT + 0x10 | bits; bit 0 ends the list, a bare 1 is an empty list.
  room pairs    u32 n, n x {room slot * SLOT, environment light slot * SLOT}; the scene root is
                slot -1. 797 pairs: ZROOM / ZBackdrop / ZIngameMapGroup -> class 0x80000d.
  entity table  u32 n, n x {u32 decl, u32 list}: decl = record offset / 4 | 0x1000000 if it has
                children | levels to go up << 25; list = dword index of the entity's list in
                the pool, 0 = none (goes to slot +0x54 & 0xffffff, kl2 0x8adc83 / 0x41f2e0).
  dynamic list  u32 n, n x {class id, count}: objects the game creates at run time.
  tag block     u32 n, n x {fourcc, first, count}: ranges of the dynamic list ('ITEM', 'ZCOB').
                Both are copied as they are by kl2 0x9262b0.
  type table    u32 n, n x {class id, count, plain}, sorted by class id. count = entities of the
                class + its dynamic-list count; plain = entities the loader gives no object:
                class 0x200002 with flags & 0x200000 == 0 and no raw data (kl2 0x8adb82), 0 for
                every other class. kl2 0x545e50 sizes the slot and object heaps from it.

TWO ID SPACES - the point of the whole exercise
  REF id (record +0x30) is a LABEL. The loader keeps a table of hdr+0x3c + 1 handles on its stack
  and stores each entity at [REF - 1] (kl2 0x8addb7). Everything outside the .gms names entities
  by REF id and is resolved through that table: room gates and neighbour lists in the .buf
  (0x48e910), the surface table (0x8d1210), the .HVK (0x6204b0 is handed the table; fields not
  decoded here), .rmi/.rmc (kl_rooms). An id no entity has resolves to nothing, and stock
  neighbour lists hold such ids (1,268 of 13,685 over all levels; gates and surface table: 0).
  The ids follow no rule (not dense, not in scene or cluster order: holes in every level), so
  removing entities changes no REF id and added entities simply take unused ones.
  Slot index is the entity's place in the loader's memory: every block of the cluster table is
  taken from the slot heap when the first child of its group is loaded, its 24 pools laid out
  one after another (kl2 0x8ada3e..0x8adb71). An entity's slot follows from scene order and the
  cluster table alone, and changes for every later entity when one is removed. Slots are stored
  ONLY inside the .gms: list pool and room pairs. SLOT = 0x80 bytes in Dog Days, 0x70 in Dead Men.
  Proof of the slot rule: with it every one of the 627,807 list elements (Dog Days 511,036,
  Dead Men 116,771) joins a light to a non-light, and all 797 pairs join a room to an
  environment light. What a list means beyond "these two touch" is not decoded (bit 1 of an
  element is set on 54,523 of them).

.buf
  [head][names][tail]. names = for every entity in scene order its name (zero terminated) and
  its raw data block (u32, u32 size | flags << 30, ...), each written only the first time its
  bytes occur, each padded to 16: regenerated here (byte-identical 103/103). tail = the surface
  table, always the last thing in the file (0x7770 bytes in Dog Days, 0x4fe0 in Dead Men):
  six u32 {rows, columns, arrays, row size, strings, data} and typed cells; cells of type 4 are
  REF ids or -1 (90,634 ids over all scenes, every one an entity of its level): table_refs().
  head = 16 bytes '0123456789abcdef', then data the .prp addresses by offset (ZROOM gate arrays
  and neighbour lists: room_refs(); ZHFlow, ZGeomBuffer and others not decoded) and the FDX
  block. It is kept as it is and never moves, so offsets into it stay valid.

NOT DECODED (kept as stored): aux (+0x28), heap budget (+0x1c), FDX block, most of the .buf
head.
  aux is non-zero on 78,367 entities, all of group classes; clones of one object share a value
  and values run in sequences (an index into something per level). The Dog Days loader reads
  neither aux nor rotation / translation / model from a record: 0x8ad7c0 touches +0x00 +0x14
  +0x18 +0x1c +0x20 +0x2c +0x30 +0x35 only, and the one other function found that walks the
  entity table (0x55a9b0) reads +0x0c of class 0x20011b. The .prp carries the same values
  (ZGEOM fields 1, 2, 4): model equal on 857,784 of 857,784 entities, rotation on 852,908,
  position on 846,696. So a join must renumber the model index in BOTH files.
  heap budget: kl2 0x8ad862 adds 0x57800 and sizes a heap with it (0x541ae0, at least
  0x340000). ASSUMPTION: adding the budgets of two scenes is enough for their join.
"""
import struct
import kl_gms

GAMES = {
    'dd': dict(slot=0x80, spare=20000, magic=bytes.fromhex('cbdc9401ffffffff0000000000000000')),
    'dm': dict(slot=0x70, spare=16000, magic=bytes.fromhex('ffffffff9b603d010000000000000000')),
}
GROUP, STDOBJ = 0x100000, 0x200002
FILL = 0xcdcdcdcd


def _pad(b):
    b += bytes(-len(b) % 16)


class Entity:
    """name: bytes. rot: 48 bytes, trans: 16 bytes. raw: bytes or None. links: None (no list) or
    [(Entity or None, bits)] - the light <-> geometry list. kids: child entities."""
    __slots__ = ('name', 'tid', 'flags', 'group', 'model', 'rot', 'trans', 'raw', 'aux', 'ref',
                 'links', 'lkey', 'kids', 'parent')

    def walk(self):
        """This entity and everything below it, in scene order."""
        st = [self]
        while st:
            e = st.pop()
            yield e
            st.extend(reversed(e.kids))

    def __repr__(self):
        return '<%s %#x ref %d>' % (self.name.decode('latin1'), self.tid, self.ref)


class Scene:
    def __init__(self, gms, buf):
        """gms: unpacked image (kl_gms.unpack). buf: the level's .buf member."""
        h = struct.unpack_from('<16I', gms, 0)
        self.game = next((g for g, v in GAMES.items() if gms[0x40:0x50] == v['magic']), None)
        if self.game is None or (h[1], h[2], h[3], h[11]) != (0, 0, 4, 0):
            raise ValueError('not a scene image this module knows')
        S = GAMES[self.game]['slot']
        self.budget, self.ref_slots = h[7], h[15]
        self.fdx = None if h[14] == 0xffffffff else h[14]            # lies in the .buf head
        tab, n = h[0], struct.unpack_from('<I', gms, h[0])[0]
        # entities
        self.roots, order, stack, lists = [], [], [], []
        for i in range(n):
            decl, lst = struct.unpack_from('<II', gms, tab + 4 + 8 * i)
            r = struct.unpack_from('<16I', gms, 4 * (decl & 0xffffff))
            if r[4] or r[6] or r[9] or r[11] or r[13] & 0xffff00ff or r[14] or r[15]:
                raise ValueError('entity %d: a record field that is 0 in every stock scene is set' % i)
            e = Entity()
            e.name = buf[r[0]:buf.index(b'\0', r[0])]
            e.rot, e.trans = gms[r[1]:r[1] + 48], gms[r[2]:r[2] + 16]
            e.model, e.tid, e.flags, e.aux, e.ref, e.group = r[3], r[5], r[7], r[10], r[12], r[13] >> 8
            e.raw = buf[r[8]:r[8] + (struct.unpack_from('<I', buf, r[8] + 4)[0] & 0x3fffffff)] if r[8] else None
            e.links, e.lkey, e.kids = None, lst, []
            del stack[len(stack) - (decl >> 25):]
            e.parent = stack[-1] if stack else None
            (e.parent.kids if e.parent else self.roots).append(e)
            if decl & 0x1000000:
                stack.append(e)
            order.append(e); lists.append(lst)
            if i == 0:
                self.head = buf[:r[0]]
        if not n:
            self.head = buf[:h[12]]
        self.tail, self._head0, self._tail0 = buf[h[12]:], len(self.head), h[12]
        if self.fdx is not None and self.fdx >= self._head0:
            raise ValueError('FDX block is not in the .buf head')
        # slots as the loader hands them out, then everything stored by slot
        at = {s: e for e, s in self.slots().items()}
        o = h[6]
        d = struct.unpack_from('<%dI' % (struct.unpack_from('<I', gms, o)[0] // 4), gms, o + 4)
        for e, p in zip(order, lists):
            if p:
                e.links = []
                while True:
                    p += 1
                    v = d[p]
                    e.links.append((at[(v & ~7) // S] if v & ~7 else None, v & 6))
                    if v & 1:
                        break
                if e.links == [(None, 0)]:
                    e.links = []
        o = h[10]
        self.pairs = []
        for k in range(struct.unpack_from('<I', gms, o)[0]):
            a, b = struct.unpack_from('<ii', gms, o + 4 + 8 * k)
            self.pairs.append((None if a == -S else at[a // S], at[b // S]))
        self.nav = gms[h[13] + 4:h[13] + 4 + struct.unpack_from('<I', gms, h[13])[0]] if h[13] else None
        self.dyn = self.tags = None
        if h[9]:
            self.dyn = [struct.unpack_from('<II', gms, h[9] + 4 + 8 * k)
                        for k in range(struct.unpack_from('<I', gms, h[9])[0])]
        if h[8]:
            self.tags = [struct.unpack_from('<4sII', gms, h[8] + 4 + 12 * k)
                         for k in range(struct.unpack_from('<I', gms, h[8])[0])]

    # -- reading the model
    def entities(self):
        """Every entity in scene order: the order of the .prp nodes after ROOT."""
        for r in self.roots:
            yield from r.walk()

    def _blocks(self):
        """(cluster table, {entity: slot}) the way kl2 0x8ad7c0 consumes the table."""
        blocks, slot, index = [[0] * 24], {}, {}
        for e in self.entities():                          # block numbers: scene order
            if e.tid & GROUP:
                index[e] = len(blocks); blocks.append([0] * 24)
            elif e.kids:
                raise ValueError('%r has children but is not a group class' % e)
            if e.group > 2:
                raise ValueError('%r: pool group %d' % (e, e.group))
            blocks[index[e.parent] if e.parent else 0][kl_gms.category(e.tid) + 8 * e.group] += 1
        base = [0]
        # a group's block is allocated when its first child is reached, i.e. in scene order of
        # the groups that have children; the children then fill its pools in scene order
        def place(parent):
            pool = []
            for c in blocks[index[parent] if parent else 0]:
                pool.append(base[0]); base[0] += c
            return pool
        stack = [(iter(self.roots), place(None))] if self.roots else []
        while stack:
            it, pool = stack[-1]
            e = next(it, None)
            if e is None:
                stack.pop(); continue
            k = kl_gms.category(e.tid) + 8 * e.group
            slot[e] = pool[k]; pool[k] += 1
            if e.kids:
                stack.append((iter(e.kids), place(e)))
        return blocks, slot

    def slots(self):
        """{entity: slot index}. The scene root itself is slot -1."""
        return self._blocks()[1]

    def check(self):
        """Problems that would make the loader misbehave; [] for every stock scene."""
        out, refs, ents = [], {}, set(self.entities())
        for e in ents:
            if not 0 < e.ref <= self.ref_slots:
                out.append('%r: REF id outside 1..%d' % (e, self.ref_slots))
            if refs.setdefault(e.ref, e) is not e:
                out.append('%r and %r share a REF id' % (e, refs[e.ref]))
            if len(e.rot) != 48 or len(e.trans) != 16 or b'\0' in e.name:
                out.append('%r: bad matrix or name' % e)
            if e.raw is not None and (len(e.raw) < 8 or struct.unpack_from('<I', e.raw, 4)[0] & 0x3fffffff != len(e.raw)):
                out.append('%r: raw data does not carry its own size' % e)
            light = kl_gms.category(e.tid) == 2
            for t, _bits in e.links or ():
                if t is not None and t not in ents:
                    out.append('%r is linked to an entity that is not in the scene' % e)
                elif t is not None and (kl_gms.category(t.tid) == 2) == light:
                    out.append('%r: list joins two lights or two non-lights' % e)
        for a, b in self.pairs:
            if (a is not None and a not in ents) or b not in ents:
                out.append('room pair names an entity that is not in the scene')
        try:
            blocks, slot = self._blocks()
            if sum(map(sum, blocks)) != len(ents) or sorted(slot.values()) != list(range(len(ents))):
                out.append('cluster table does not add up')
        except ValueError as x:
            out.append(str(x))
        if self.dyn is not None and self.tags is not None and sum(t[2] for t in self.tags) != len(self.dyn):
            out.append('tag block does not cover the dynamic list')
        return out

    # -- writing
    def _names(self, ents):
        """([(name offset, raw data offset or 0)] per entity, the names part of the .buf)."""
        names, where, base, offs = bytearray(), {}, len(self.head), []
        def put(key, data):
            if key not in where:
                where[key] = base + len(names)
                names.extend(data); _pad(names)
            return where[key]
        for e in ents:
            a = put((0, e.name), e.name + b'\0')
            offs.append((a, put((1, e.raw), e.raw) if e.raw is not None else 0))
        return offs, bytes(names)

    def write(self):
        """(unpacked .gms, .buf). Pack the first with kl_gms.pack."""
        S, G = GAMES[self.game]['slot'], GAMES[self.game]
        ents = list(self.entities())
        blocks, slot = self._blocks()
        offs, names = self._names(ents)
        tail = len(self.head) + len(names)
        buf = self.head + names + self.tail
        # records
        out = bytearray(0x40) + G['magic']
        mats, recs = {}, []
        for e, (name, raw) in zip(ents, offs):
            for m in (e.trans, e.rot):
                if m not in mats:
                    mats[m] = len(out); out += m
            recs.append(len(out))
            out += struct.pack('<16I', name, mats[e.rot], mats[e.trans], e.model, 0, e.tid, 0, e.flags,
                               raw, 0, e.aux, 0, e.ref, e.group << 8, 0, 0)
        h = [0] * 16
        h[3], h[7], h[12] = 4, self.budget, tail
        h[14] = 0xffffffff if self.fdx is None else self.fdx
        h[15] = max([self.ref_slots] + [e.ref + 1 for e in ents])
        h[5] = len(out)
        out += struct.pack('<I', len(blocks)) + b''.join(struct.pack('<24I', *b) for b in blocks); _pad(out)
        # list pool: lists keep their stored order, new ones go behind
        d, lst = [0, 0, 0, 0xffffffff], {}
        for e in sorted((e for e in ents if e.links is not None), key=lambda e: e.lkey or 1 << 30):
            lst[e] = len(d)
            d.append(0)
            el = e.links or [(None, 0)]
            for k, (t, bits) in enumerate(el):
                d.append((slot[t] * S + 0x10 if t is not None else 0) | bits | (k == len(el) - 1))
        d[0], d[1], d[2] = len(d), max(40960, 2 * len(d) - 8), G['spare']
        d += [FILL] * (d[1] + d[2])
        h[6] = len(out)
        out += struct.pack('<I%dI' % len(d), 4 * len(d), *d); _pad(out)
        h[10] = len(out)
        out += struct.pack('<I', len(self.pairs))
        for a, b in self.pairs:
            out += struct.pack('<iI', -S if a is None else slot[a] * S, slot[b] * S)
        _pad(out)
        h[0] = len(out)
        out += struct.pack('<I', len(ents))
        level = 0
        depth = {None: -1}
        for e, r in zip(ents, recs):
            depth[e] = dp = depth[e.parent] + 1
            out += struct.pack('<II', r // 4 | (0x1000000 if e.kids else 0) | (level - dp) << 25, lst.get(e, 0))
            level = dp + bool(e.kids)
        _pad(out)
        if self.nav is not None:
            h[13] = len(out)
            out += struct.pack('<I', len(self.nav)) + self.nav; _pad(out)
        if self.dyn is not None:
            h[9] = len(out)
            out += struct.pack('<I', len(self.dyn)) + b''.join(struct.pack('<II', *x) for x in self.dyn); _pad(out)
        if self.tags is not None:
            h[8] = len(out)
            out += struct.pack('<I', len(self.tags)) + b''.join(struct.pack('<4sII', *x) for x in self.tags); _pad(out)
        count, plain = dict(self.dyn or ()), 0
        for e in ents:
            count[e.tid] = count.get(e.tid, 0) + 1
            plain += e.tid == STDOBJ and not e.flags & 0x200000 and e.raw is None
        h[4] = len(out)
        out += struct.pack('<I', len(count))
        for t in sorted(count):
            out += struct.pack('<3I', t, count[t], plain if t == STDOBJ else 0)
        _pad(out)
        out[:0x40] = struct.pack('<16I', *h)
        return bytes(out), buf

    def buf_offset(self, off):
        """Where a .buf offset of the scene as it was READ lies in the .buf write() returns now:
        the head does not move, the tail moves as one block. None for the names / raw data
        part, which only the .gms records address."""
        if off < self._head0:
            return off
        if off < self._tail0:
            return None
        return off - self._tail0 + len(self.head) + len(self._names(list(self.entities()))[1])

    # -- editing
    def remove(self, top):
        """Take a subtree out. Lists and room pairs that named one of its entities lose that
        entry. REF ids of the remaining entities do not change (they are labels); their slots
        do, and write() renumbers every stored slot. Returns
        {'refs': REF ids that left, 'links': list entries dropped, 'pairs': pairs dropped}."""
        gone = set(top.walk())
        (top.parent.kids if top.parent else self.roots).remove(top)
        top.parent = None
        cut = 0
        for e in self.entities():
            if e.links:
                keep = [x for x in e.links if x[0] not in gone]
                cut += len(e.links) - len(keep)
                e.links = keep
        pairs = [p for p in self.pairs if p[0] in gone or p[1] in gone]
        self.pairs = [p for p in self.pairs if p not in pairs]
        return {'refs': sorted(e.ref for e in gone), 'links': cut, 'pairs': len(pairs)}

    def graft(self, src, top, parent=None, models=True, head=False):
        """Append a copy of subtree `top` of scene `src` (same game) under `parent` (None: the
        scene root). Copies take unused REF ids from ref_slots up. Lists and pairs are kept
        where both ends are inside the subtree; the others are dropped and counted.
        models=False sets every model index to 0 (entities only).
        head=True also appends src's .buf head (once per src) so that offsets the .prp of src
        holds (room gates, neighbour lists ...) stay addressable at offset + 'buf'.
        Returns {'refs': {REF id in src: REF id here}, 'buf': shift of src's head offsets or
        None, 'links': dropped, 'pairs': dropped, 'top': the new subtree}.
        Dynamic list, tag block, navigation mesh, surface table and heap budget stay this
        scene's own: add src.budget to budget when in doubt (see the report)."""
        if src.game != self.game:
            raise ValueError('grafting between games needs the converters first')
        copy, cut = {}, 0
        nxt = max([self.ref_slots] + [e.ref + 1 for e in self.entities()])
        for e in top.walk():
            c = Entity()
            for a in ('name', 'tid', 'flags', 'group', 'rot', 'trans', 'raw', 'aux'):
                setattr(c, a, getattr(e, a))
            c.model = e.model if models else 0
            c.ref, c.lkey, c.kids, c.links = nxt, 0, [], None
            c.parent = copy.get(e.parent, parent) if e is not top else parent
            (c.parent.kids if c.parent else self.roots).append(c)
            copy[e] = c; nxt += 1
        self.ref_slots = nxt
        for e, c in copy.items():
            if e.links is not None:
                c.links = [(copy[t] if t is not None else None, b) for t, b in e.links if t is None or t in copy]
                cut += len(e.links) - len(c.links)
        new = [(copy.get(a), copy[b]) for a, b in src.pairs if a in copy and b in copy]
        lost = sum(1 for a, b in src.pairs if (a in copy) != (b in copy))
        self.pairs += new
        shift = None
        if head:
            shifts = self.__dict__.setdefault('_heads', {})
            if id(src) not in shifts:
                self.head += bytes(-len(self.head) % 16)
                shifts[id(src)] = len(self.head)
                self.head += src.head
            shift = shifts[id(src)]
        return {'refs': {e.ref: c.ref for e, c in copy.items()}, 'buf': shift, 'links': cut,
                'pairs': lost, 'top': copy[top]}

    def compact_refs(self):
        """Optional: renumber REF ids 1..n in scene order and return {old: new}. Every other
        member that stores REF ids must then be remapped with the result (see table_refs,
        room_refs and the report). Nothing requires it; it only keeps the id table small."""
        m = {}
        for k, e in enumerate(self.entities()):
            m[e.ref] = e.ref = k + 1
        self.ref_slots = len(m) + 1
        return m


# -- REF ids stored in the .buf ---------------------------------------------------------------
def table_refs(buf, off):
    """Offsets (in buf) of the REF id cells of the surface table that starts at `off`
    (gms header +0x30). A cell holds a REF id or -1. Layout as kl2 0x788cc0 / 0x8d1210 read it:
    rows {name, id}, columns {name, type, offset, array or -1}, arrays {name, offset of the
    count}; an array cell is u32 stride, then count elements of that stride."""
    rows, cols, arrs, size, _strings, data = struct.unpack_from('<6I', buf, off)
    ids = [struct.unpack_from('<I', buf, off + rows + 8 + 8 * i)[0] for i in range(struct.unpack_from('<I', buf, off + rows)[0])]
    out = []
    for k in range(struct.unpack_from('<I', buf, off + cols)[0]):
        _name, typ, at, arr = struct.unpack_from('<4I', buf, off + cols + 4 + 16 * k)
        if typ != 4:
            continue
        for i in ids:
            cell = off + data + (i - 1) * size + at
            if arr == 0xffffffff:
                out.append(cell)
            else:
                n = struct.unpack_from('<I', buf, off + struct.unpack_from('<I', buf, off + arrs + 8 + 8 * arr)[0])[0]
                stride = struct.unpack_from('<I', buf, cell)[0]
                out += [cell + 4 + stride * j for j in range(n)]
    return out


def room_refs(buf, game, gates, ngates, lists, nlists):
    """Offsets (in buf) of the REF ids one ZROOM's data holds. gates / lists are the room's two
    .buf offsets, ngates / nlists its two counts (.prp, see kl_rooms). A gate names its
    neighbour at +0x30 when +0x36 has bit 2; a neighbour list is {REF id, n, offset from
    `lists`} followed by n REF ids (kl2 0x48e910)."""
    stride = 0x74 if game == 'dd' else 0x38
    out = [gates + stride * k + 0x30 for k in range(ngates) if buf[gates + stride * k + 0x36] & 2]
    for k in range(nlists):
        _room, n, at = struct.unpack_from('<3I', buf, lists + 12 * k)
        out.append(lists + 12 * k)
        out += [lists + at + 4 * j for j in range(n)]
    return out


def remap_refs(buf, offsets, refs, missing=None):
    """buf with the REF ids at `offsets` replaced through {old: new}; 0 and -1 stay.
    Stock levels hold a few ids that name no entity (Dead Men M06_FA_A: 6707 in a room's
    data); the loader's table has 0 there, so they resolve to nothing. After a renumbering such
    an id could hit a real entity: pass missing = an id no entity has (Scene.ref_slots after
    write() is always free) to send them there; with missing=None they raise KeyError."""
    buf = bytearray(buf)
    for o in offsets:
        v = struct.unpack_from('<I', buf, o)[0]
        if v not in (0, 0xffffffff):
            struct.pack_into('<I', buf, o, refs[v] if missing is None else refs.get(v, missing))
    return bytes(buf)


def read(zf, stem=None):
    """Scene of a level archive (zipfile.ZipFile). stem: member name without extension when
    the archive holds more than one scene."""
    names = {n.lower(): n for n in zf.namelist()}
    gms = [n for n in names if n.endswith('.gms') and (stem is None or n == stem.lower() + '.gms')]
    if len(gms) != 1:
        raise ValueError('expected one .gms, found %d' % len(gms))
    return Scene(kl_gms.unpack(zf.read(names[gms[0]])), zf.read(names[gms[0][:-4] + '.buf']))
