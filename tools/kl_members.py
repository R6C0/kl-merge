"""
The small level members and the two .buf tables a graft has to carry: .sgd .sgp .hrd .sup .zgf,
the surface-material table (.gms header +0x30) and the bone-dynamics block (.gms header +0x38).

Everything below was read off kl2.exe and checked on all 41 stock levels (21 Dog Days: F01-F09,
L00-L11; 20 Dead Men) on 2026-10-09; `python kl_members.py` repeats the checks. "REF" is the
1-based id at .gms record +0x30. Every format here has the same shape in both games: Dead Men's
files parse to their last byte with the rules read off Dog Days' readers (kaneandlynch.exe's own
readers were not disassembled). What differs is content: material list, ammunition list, REF
ids, .SND offsets.

.sup / .zgf   24 and 17 constant bytes, identical in all 41 levels of both games (SUP, ZGF).

.sgd   Sections {u32 size, u8 header length, name NUL, 0xcd padding to the header length (5 + name
  + NUL rounded up to 16), payload}, ended by u32 -1 and four 0xcd. kl2 0x45ef40 finds a section by
  name (_stricmp); it has exactly three callers:
  - "ExplodableOctree" (0x5e38c0, absent = skipped) and "HavokShatterOctree" (the name is in
    neither exe: nothing reads it, yet all 41 levels carry it). A compiled point octree:
      +0 u32 offset of the leaf area, +4 3 x f32 centre, +0x10 f32 scale (quanta per unit),
      +0x14 nodes of 6 bytes {u16 octant | count << 3 | 0x8000 on the last sibling, u16 index of
      the first child (0 none), u16 first leaf}, 0xcd padding to 16, then 16-byte leaves
      {u32 REF, u16 min[3], u16 max[3]}.
    q = 0x8000 + (p - centre) * scale. In all 21,020 stock leaves max = min + 1, the leaf hangs 14
    levels deep and its path is the top 14 bits of max (octant = x | y << 1 | z << 2); children
    are laid out as one block in ascending octant, depth first (walk: kl2 0x4f7ef0). The loader
    replaces each leaf's REF by table[REF - 1] (0x6af020): every leaf of every level resolves
    (ZSTDOBJ / ZBoxPrimitive / ZHavokRigidBody / ZLNKOBJ). `Octree` rebuilds all 78 stock trees
    byte for byte. Leaf owners: 20,257 under the map's `Locations/...`, 763 under cut-scene,
    AI-vehicle and escape subtrees, none under `AllLevels/...` or a CloneGroup. 72 % of the leaves
    decode to within one quantum of the entity's origin (parent transforms composed naively,
    axes in reverse order); the other 28 % were not explained. MEASURED 2026-10-28 (scheduled
    check-in, kl_sgd_audit.py on the nine stock Dog Days FA levels): every HavokShatterOctree
    leaf lies on its entity's composed origin (worst 0.6 units, so the stored order (z, y, x)
    is a FACT), the unexplained ones are ExplodableOctree leaves of windows, lights and sirens
    that sit 55..525 units from the origin (GUESS: the explodable's own centre, not the
    entity's). The grafts carry STALE leaves: entities moved after the tree was built or
    carried from the other source keep the old point (DM11B 'ShatterGeom' of EscapeSetup 43.6k
    units off, 'Lights_Front_On'/'Lights_Back_On' of Animation/F07 5k..66k off in 8 DM maps,
    DM03A 30 shatter leaves 16k..18k off) - see kl_sgd_audit.py. World translation: the
    centre moves by (tz, ty, tx) (`Octree.translate`, `sgd_translate`); the quantised leaves
    stay.
  - "SecurityZones" (0x448530; L00, M03A, M05A, M09B): 0x40-byte boxes {3x3 f32, centre, half
    extents, u32}. No references.
  - "HavokShatterGlassConnectivity" (0x8aba40, only if the glass manager [0x153ab14] exists;
    Dead Men M01A M02FAA M03A M03FAA M05A M08A M09B, no Dog Days level): u32 n, then
    {u32 count, u32 REF, count x 40 bytes}. Dog Days' reader consumes Dead Men's seven sections
    exactly and all 34 REFs are ZAllocMany shard groups of the map, but nothing here shows the
    40-byte record means the same thing, so `sgd_join` drops the section unless glass=True
    (CLAUDE.md asks for the strip).

.sgp   Sound propagation graph, handed to ZDllSoundWintel (kl2 0x718180 -> 0x70d330, which only
  stores pointer + size). The code that walks it is ZSoundGraph (vtable 0xb9a614; re/campaign_fa_prison.md
  section 4): slot 1 = 0x75ee20 loads the five arrays into this+0x1270 portals / +0x1274 edges /
  +0x1278 rooms / +0x127c routes / +0x1280 portal list (READ 2026-10-28, scheduled check-in). Readers
  of a portal record: the route finder 0x5866a0 (from slot 3 = 0x576b10) takes the squared distance
  listener -> portal +0x14 (0x530e00) and multiplies the two portals' +0x00 (0 = closed: 0x4563dd
  and slot 5 = 0x4da770 test +0x00 against 0); 0x43c030 matches +0x0c / +0x10 against a room; slot 4
  = 0x67c4d0 -> 0x8d6ef0 copies +0x14 centre, +0x20 normal and the four corners +0x2c +0x38 +0x44
  +0x50 (forward or reversed by its side flag) into the caller's vectors. Nothing reads +0x04 / +0x08
  (0 in all 1053 stock + graft portals; +0x00 is 1.0 in all). Edge distance = |centre a - centre b|
  (6218 edges, within 0.003). So a world translation of the level moves centre + corners only:
  `Sgp.translate`. Parsed to the last byte in 41/41:
      5 x u32: portals, edges, rooms, routes, portal-list entries
      portal 0x5c: f32 openness 1.0, f32 0, f32 0, u32 room a, u32 room b, centre xyz, unit normal xyz, 4 corners xyz
      edge   {u32 portal, u32 portal, f32 distance}
      room   {u32 first portal-list entry, u32 route count, u32 first route}
      route  {u16 index, u16 destination room | flag}: flag 0 = index is a portal (each portal
             once: 1280 = 1280), 0x4000 = an edge, 0x8000 = a room to go through; a room only
             lists destinations with a higher index, so ROOM ORDER IS PART OF THE DATA
      portal list: u32 portal indices (-1 fillers occur)
      then per room: scene path without "ROOT\\", NUL, u32 index (0, 1, 2 ...).
  The names are exactly the scene paths of the level's ZROOM-derived entities (set equal in 41/41;
  the order is not scene order), so a graft's .sgp needs BOTH sides' rooms (the systems bring
  DebugRoom and the scope / overlay rooms, with no portals).

.hrd   28-byte records {position xyz in Havok metres (x100 = world units), quaternion}: the rest
  pose of rigid body i of the list at [ZHavok world +0x1106c] (kl2 0x4c1700 -> setPosition, add
  to world). The loop runs over the BODY count and never looks at the file size: a short file is
  read past its end; no file (size < 0) just adds the bodies where the scene has them (static
  reading; no stock level with bodies lacks the file). Records lie on ZHavokRigidBody positions
  (to 0.3 units in 16 of 19 Dog Days levels), but 7 levels have fewer records than bodies and
  the records follow scene order in only about 10 of the 35 files: which bodies register, and
  in what order, is NOT established. Hence `hrd_join`: one level brings all its bodies -> its file unchanged, else no .hrd.
  Every Dog Days FA level and Dead Men FA level keeps all its bodies under `Locations/...`.

Surface table (.buf, from .gms +0x30 to the end; kl2 0x788cc0 -> global 0xea2878): 6 x u32
  {materials, properties, categories, row size, strings, rows} (offsets from the table start).
      materials  u32 n, n x {name id, material id = row + 1}
      properties u32 n, n x {name id, type, offset in the row, category or -1}
                 type 1 int, 2 float, 4 entity REF (-1 none), 5 offset of a record in the .SND
      categories u32 n, n x {name id, offset of {u32 n, n x {name id, index}}}: 0 = the
                 ammunition list "scene:AllLevels/Equipment#/Engine/Objects/Ammo", 1 = Contact (empty)
      rows       per material one row; a cell is a dword, or with a category {u32 4, one dword
                 per member} (accessors 0x8a09f0, 0x4e5040, 0x6d3b80: row = (id - 1) * row size,
                 id 0 answers 0, ids are NOT range checked)
      strings    u32 n, n offsets, the names.
  Materials and properties are looked up BY NAME at run time (0x8f4c70 / 0x7d82b0), so the layout
  is free; Dog Days has 24 materials x 54 ammunition types (row 0x480), Dead Men 31 x 32 (0x248).
  The table is per level only in its REFs and .SND offsets. Its REFs are impact effects, decals
  and blood: in 37 of 41 levels (all nine Dog Days FA levels) every one lies under
  `AllLevels/mainsceneincludes[_multiplayer].zip`; L07, M01FAA, M09B, M13B keep theirs under
  `Locations/`.
  A GRAFT USES THE SYSTEMS LEVEL'S (Dog Days) TABLE, REFs renumbered with the systems side's map:
  the columns are Dog Days' weapons and the cells Dog Days' effects and sounds. Dead Men material
  ids in the map's data must then be rewritten 1..31 -> 1..24 (`material_map`; ids 25..31 would
  read past the last row). Where the ids are stored (.MAT entry +0x18 per CLAUDE.md; .oct / .HVK
  not examined) is not established here.

Bone dynamics (.buf at .gms +0x38, -1 = none; kl2 0x7a68b0, int3 on failure): "FDX", u8 4,
  u16 bone records, u16 vertex records, 8 unread bytes, then per record
      u8 kind (0 bone -> ZBoneExtend, else ZVertexExtend), u8, u16 n,
      kind 0: n x {u16, u16, u16, u16 m, m x u16}, 2 bytes more if the m's sum is odd
      u32 model = chunk index in the .prm (.gms record +0x0c), f32,
      3 x f32 gravity, u16, u16, f32, u16 n1, n2, n3, n4, u32,
      n1 x 24 bytes, n2 x 16, n3 x 8, n4 x 48 (one per instance: n4 equals the number of
      entities using the model in 43/43 records).
  Hanging lamps, blinds, cables, fish: 43 records in 14 levels (F04, L00-L05, seven Dead Men
  levels incl. M01FAA, M02FAA, M06FAA, M09A); all 315 users are ZLNKOBJ under `Locations/`.
  Same version and sizes in both games (Dead Men blocks parse to their end with Dog Days'
  reader); that the fields mean the same is an ASSUMPTION. A graft carries the map's block with
  the model indices renumbered (`fdx_join`). A vertex record (kind != 0) has no array in the
  file (kl2 0x69fee0 only allocates); no stock level has one.
"""
import struct

SUP = bytes.fromhex('00000000180000801800000001000000444c434608000000')
ZGF = bytes.fromhex('0800000011000000015446475a08000000')
NONE = 0xffffffff


# ------------------------------------------------------------------ .sgd
def sgd_read(data):
    """[(name, payload)] of an .sgd."""
    out, o = [], 0
    while struct.unpack_from('<I', data, o)[0] != NONE:
        n, hl = struct.unpack_from('<IB', data, o)
        out.append((data[o + 5:data.index(b'\0', o + 5)].decode('latin1'), data[o + hl:o + hl + n]))
        o += hl + n
    return out


def sgd_write(sections):
    out = b''
    for name, payload in sections:
        hl = (5 + len(name) + 1 + 15) & ~15
        out += struct.pack('<IB', len(payload), hl) + name.encode('latin1') + b'\0'
        out += b'\xcd' * (hl - 6 - len(name)) + payload
    return out + b'\xff' * 4 + b'\xcd' * 4


class Octree:
    """Compiled point octree of an .sgd section. leaves = [(REF, (min xyz), (max xyz))] in file
    order; centre and scale as stored (the stored axis order is the reverse of the .gms
    translation's: decoded leaves match composed entity positions that way round)."""
    DEPTH = 14

    def __init__(self, data=None):
        self.centre, self.scale, self.leaves = (0.0, 0.0, 0.0), 1.0, []
        if data:
            lo = struct.unpack_from('<I', data, 0)[0]
            *c, self.scale = struct.unpack_from('<4f', data, 4)
            self.centre = tuple(c)
            for o in range(lo, len(data), 16):
                v = struct.unpack_from('<I6H', data, o)
                self.leaves.append((v[0], v[1:4], v[4:7]))

    def position(self, leaf):
        """The leaf's point in the STORED axis order: (z, y, x) of the world (docstring, MEASURED)."""
        return tuple(c + (q - 0x8000) / self.scale for c, q in zip(self.centre, leaf[1]))

    def world(self, leaf):
        """The leaf's point as world (x, y, z)."""
        return self.position(leaf)[::-1]

    def translate(self, t):
        """The same tree for the level moved by the world vector t = (tx, ty, tz): only the centre
        moves (stored order, so by (tz, ty, tx)); scale, nodes and the quantised leaves stay.
        Returns a new Octree; the result is exact to one float32 rounding of each centre component."""
        out = Octree()
        out.centre = tuple(struct.unpack('<f', struct.pack('<f', c + d))[0] for c, d in zip(self.centre, (t[2], t[1], t[0])))
        out.scale, out.leaves = self.scale, list(self.leaves)
        return out

    def serialize(self):
        """The section payload; None without leaves (leave the section out: the reader skips it)."""
        if not self.leaves:
            return None
        root = [0, {}, []]                                   # octant, children, leaves
        for leaf in self.leaves:
            node, (x, y, z) = root, leaf[2]
            for lv in range(self.DEPTH):
                s = 15 - lv
                o = (x >> s & 1) | (y >> s & 1) << 1 | (z >> s & 1) << 2
                node = node[1].setdefault(o, [o, {}, []])
            node[2].append(leaf)
        nodes, leaves = [[root, 0, False]], []               # node, first child, last sibling

        def lay(k):
            node = nodes[k][0]
            first = len(leaves) if node[2] else 0
            leaves.extend(node[2])
            kids = [node[1][o] for o in sorted(node[1])]
            if kids:
                nodes[k][1] = base = len(nodes)
                nodes.extend([kid, 0, i == len(kids) - 1] for i, kid in enumerate(kids))
                for i in range(len(kids)):
                    lay(base + i)
            nodes[k].append(first)
        import sys
        sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
        lay(0)
        if len(nodes) > 0xffff or len(leaves) > 0xffff or any(len(n[0][2]) > 0xfff for n in nodes):
            raise ValueError('octree too large for 16-bit node / leaf indices')
        body = b''.join(struct.pack('<3H', n[0][0] | len(n[0][2]) << 3 | (0x8000 if n[2] else 0), n[1], n[3])
                        for n in nodes)
        body += bytes([0xcd]) * (-(0x14 + len(body)) % 16)
        out = struct.pack('<I4f', 0x14 + len(body), *self.centre, self.scale) + body
        return out + b''.join(struct.pack('<I6H', r, *a, *b) for r, a, b in leaves)

    @classmethod
    def join(cls, parts):
        """parts = [(Octree, {old REF: new REF})]. Leaves whose entity is not carried are dropped.
        With one contributing tree its frame and quantised points stay as they are; otherwise the
        points are re-quantised into a common cube (the stock rule for choosing centre and scale
        was not recovered: centre = middle of the points, scale = the smallest of the sources',
        lowered until everything fits in 0x1000..0xefff)."""
        kept = [(t, [(m[l[0]], l[1], l[2]) for l in t.leaves if l[0] in m]) for t, m in parts if t]
        kept = [(t, ls) for t, ls in kept if ls]
        out = cls()
        if len(kept) == 1:
            out.centre, out.scale, out.leaves = kept[0][0].centre, kept[0][0].scale, kept[0][1]
        elif kept:
            pts = [(l[0], t.position(l)) for t, ls in kept for l in ls]
            lo = [min(p[a] for _, p in pts) for a in range(3)]
            hi = [max(p[a] for _, p in pts) for a in range(3)]
            out.centre = tuple((a + b) / 2 for a, b in zip(lo, hi))
            span = max(b - a for a, b in zip(lo, hi)) or 1.0
            out.scale = struct.unpack('<f', struct.pack('<f', min(min(t.scale for t, _ in kept), 0xe000 / span)))[0]
            for ref, p in pts:
                q = tuple(int(round(0x8000 + (v - c) * out.scale)) for v, c in zip(p, out.centre))
                out.leaves.append((ref, q, tuple(v + 1 for v in q)))
        return out


def glass_read(payload):
    """HavokShatterGlassConnectivity -> [(REF, [40-byte records])]."""
    out, o = [], 4
    for _ in range(struct.unpack_from('<I', payload, 0)[0]):
        n, ref = struct.unpack_from('<II', payload, o)
        out.append((ref, [payload[o + 8 + 40 * i:o + 48 + 40 * i] for i in range(n)]))
        o += 8 + 40 * n
    if o != len(payload):
        raise ValueError('glass connectivity: %d bytes left' % (len(payload) - o))
    return out


def glass_write(items):
    return struct.pack('<I', len(items)) + b''.join(struct.pack('<II', len(r), ref) + b''.join(r) for ref, r in items)


def sgd_translate(data, t, zones=True):
    """The .sgd of the level moved by the world vector t: both octrees get `Octree.translate`.
    SecurityZones boxes (centre at +0x24, GUESS: stored as world x y z - only L00, M03A, M05A,
    M09B carry the section and none was checked against the scene) move their centre when
    zones=True, else the call raises. HavokShatterGlassConnectivity is refused (its 40-byte
    records are not decoded; no Dog Days level and no DM graft of the FA set carries it)."""
    out = []
    for name, payload in sgd_read(data):
        if name in ('HavokShatterOctree', 'ExplodableOctree'):
            body = Octree(payload).translate(t).serialize()
            if body is None:
                raise ValueError('sgd: %s has no leaves' % name)
            out.append((name, body))
        elif name == 'SecurityZones':
            if not zones:
                raise ValueError('sgd: SecurityZones present (centre axis order is a GUESS)')
            boxes = bytearray(payload)
            for o in range(0, len(boxes), 0x40):
                c = struct.unpack_from('<3f', boxes, o + 0x24)
                struct.pack_into('<3f', boxes, o + 0x24, *[a + b for a, b in zip(c, t)])
            out.append((name, bytes(boxes)))
        elif name == 'HavokShatterGlassConnectivity':
            raise ValueError('sgd: HavokShatterGlassConnectivity is not decoded, cannot translate')
        else:
            raise ValueError('sgd: unknown section %r' % name)
    return sgd_write(out)


def sgd_join(parts, glass=False):
    """parts = [(sgd bytes, {old REF: new REF})], one per source level; a REF missing from the map
    means the entity is not in the joined level. Also the Dead Men -> Dog Days conversion (one
    part): the formats are the same, only the glass section goes unless glass=True."""
    secs = [(dict(sgd_read(d)), m) for d, m in parts]
    out = []
    zones = b''.join(s.get('SecurityZones', b'') for s, _ in secs)
    if zones:
        out.append(('SecurityZones', zones))
    if glass:
        items = [(m[ref], recs) for s, m in secs if 'HavokShatterGlassConnectivity' in s
                 for ref, recs in glass_read(s['HavokShatterGlassConnectivity']) if ref in m]
        if items:
            out.append(('HavokShatterGlassConnectivity', glass_write(items)))
    for name in ('HavokShatterOctree', 'ExplodableOctree'):
        body = Octree.join([(Octree(s[name]), m) for s, m in secs if name in s]).serialize()
        if body:
            out.append((name, body))
    return sgd_write(out)


# ------------------------------------------------------------------ .sgp
class Sgp:
    """Sound propagation graph. portals: 0x5c-byte records (rooms at +0x0c / +0x10); edges
    (portal, portal, distance); rooms [name, portal-list slice, routes]; routes (index, word)."""
    P, E, R = 0, 0x4000, 0x8000

    def __init__(self, data=None):
        self.portals, self.edges, self.rooms = [], [], []
        if not data:
            return
        a, b, nr, nd, ne = struct.unpack_from('<5I', data, 0)
        o = 0x14
        self.portals = [bytearray(data[o + 0x5c * i:o + 0x5c * i + 0x5c]) for i in range(a)]
        o += 0x5c * a
        self.edges = [struct.unpack_from('<IIf', data, o + 12 * i) for i in range(b)]
        o += 12 * b
        recs = [struct.unpack_from('<3I', data, o + 12 * i) for i in range(nr)]
        o += 12 * nr
        routes = [struct.unpack_from('<HH', data, o + 4 * i) for i in range(nd)]
        o += 4 * nd
        plist = struct.unpack_from('<%dI' % ne, data, o)
        o += 4 * ne
        for i, (first, count, froute) in enumerate(recs):
            e = data.index(b'\0', o)
            if struct.unpack_from('<I', data, e + 1)[0] != i:
                raise ValueError('sgp: room names are not numbered in order')
            end = recs[i + 1][0] if i + 1 < nr else ne
            self.rooms.append([data[o:e].decode('latin1'), list(plist[first:end]), routes[froute:froute + count]])
            o = e + 5
        if o != len(data) or sum(len(r[2]) for r in self.rooms) != nd:
            raise ValueError('sgp: layout not understood')

    def serialize(self):
        plist = [p for r in self.rooms for p in r[1]]
        routes = [x for r in self.rooms for x in r[2]]
        out = struct.pack('<5I', len(self.portals), len(self.edges), len(self.rooms), len(routes), len(plist))
        out += b''.join(bytes(p) for p in self.portals) + b''.join(struct.pack('<IIf', *e) for e in self.edges)
        ep = er = 0
        for name, pl, rt in self.rooms:
            out += struct.pack('<3I', ep, len(rt), er)
            ep += len(pl)
            er += len(rt)
        out += b''.join(struct.pack('<HH', *x) for x in routes) + struct.pack('<%dI' % len(plist), *plist)
        return out + b''.join(r[0].encode('latin1') + b'\0' + struct.pack('<I', i) for i, r in enumerate(self.rooms))

    CENTRE, NORMAL, CORNERS = 0x14, 0x20, (0x2c, 0x38, 0x44, 0x50)

    def points(self, k):
        """Portal k's absolute points: [centre, corner, corner, corner, corner] as (x, y, z)."""
        p = self.portals[k]
        return [struct.unpack_from('<3f', p, o) for o in (self.CENTRE,) + self.CORNERS]

    def translate(self, t):
        """The graph of the level moved by the world vector t = (tx, ty, tz): every portal's
        centre and four corners move by t; openness, rooms, normal, edges (distance between the
        centres: unchanged by a translation), rooms, routes and the portal list are copied.
        Returns a new Sgp. Each moved float is rounded once to float32 (exact for the integer
        part when t is a multiple of 4096 and |x| < 2^22; translate back is not bit-identical)."""
        out = Sgp()
        for p in self.portals:
            q = bytearray(p)
            for o in (self.CENTRE,) + self.CORNERS:
                struct.pack_into('<3f', q, o, *[v + d for v, d in zip(struct.unpack_from('<3f', q, o), t)])
            out.portals.append(q)
        out.edges = list(self.edges)
        out.rooms = [[name, list(pl), list(rt)] for name, pl, rt in self.rooms]
        return out

    @classmethod
    def join(cls, parts, rooms=None):
        """parts = [(Sgp, keep)]: keep(room path) says whether that room is in the joined level
        (e.g. lambda p: p.split('\\\\')[0] in kept_top_level_names). Kept rooms keep their relative
        order (routes only run from lower to higher index). A portal goes when both its rooms go
        (and its edges with it); one between a kept and a dropped room, or a kept room routed
        through a dropped one, is an error: the kept rooms must be a closed part of the graph.
        Rooms of different parts are not connected (no portal joins them): sound will not carry
        between two maps joined this way. `rooms`, if given, is every ZROOM path of the joined
        level: missing ones are appended as isolated rooms and anything else is an error."""
        out = cls()
        for g, keep in parts:
            new, pmap, emap = {}, {}, {}
            for i, r in enumerate(g.rooms):
                if keep(r[0]):
                    new[i] = len(out.rooms) + len(new)
            for k, p in enumerate(g.portals):
                a, b = struct.unpack_from('<II', p, 0x0c)
                if (a in new) != (b in new):
                    raise ValueError('sgp: portal %d joins a kept and a dropped room' % k)
                if a in new:
                    q = bytearray(p)
                    struct.pack_into('<II', q, 0x0c, new[a], new[b])
                    pmap[k] = len(out.portals)
                    out.portals.append(q)
            for k, (i, j, d) in enumerate(g.edges):
                if i in pmap and j in pmap:
                    emap[k] = len(out.edges)
                    out.edges.append((pmap[i], pmap[j], d))
            for i, (name, pl, rt) in enumerate(g.rooms):
                if i not in new:
                    continue
                fixed = []
                for idx, w in rt:
                    f, dest = w & 0xc000, w & 0x3fff
                    via = pmap if f == cls.P else emap if f == cls.E else new
                    if f == 0xc000 or idx not in via or dest not in new or via[idx] > 0xffff or new[dest] > 0x3fff:
                        raise ValueError('sgp: room %r is routed through something that is dropped' % name)
                    fixed.append((via[idx], f | new[dest]))
                out.rooms.append([name, [p if p == NONE else pmap[p] for p in pl], fixed])
        have = [r[0] for r in out.rooms]
        if len(set(have)) != len(have):
            raise ValueError('sgp: the same room path comes from two parts')
        if rooms is not None:
            extra = set(have) - set(rooms)
            if extra:
                raise ValueError('sgp: rooms not in the joined level: %s' % sorted(extra)[:3])
            out.rooms += [[p, [], []] for p in rooms if p not in set(have)]
        return out


# ------------------------------------------------------------------ .hrd
def hrd_records(data):
    return [struct.unpack_from('<7f', data, o) for o in range(0, len(data) - 27, 28)]


def hrd_join(parts):
    """parts = [(hrd bytes or None, ZHavokRigidBody entities in that level, how many of them are
    carried)]. Returns the member when exactly one level brings rigid bodies and brings all of
    them (ASSUMPTION: their registration order survives the graft, as nothing else registers),
    else None = ship no .hrd (see the docstring: record i belongs to rigid body i in an order
    that was not recovered, and a file shorter than the body list is read past its end)."""
    live = [(d, total, kept) for d, total, kept in parts if kept]
    return live[0][0] if len(live) == 1 and live[0][0] and live[0][1] == live[0][2] else None


# ------------------------------------------------------------------ surface table
INT, FLOAT, ENTITY, SOUND = 1, 2, 4, 5

# Dead Men material -> Dog Days material where the name differs. ASSUMPTION throughout: chosen by
# meaning; any Dog Days name is safe, it only picks the decal, debris and sound of a hit.
MATERIAL_ALIAS = {
    'Perforated Metal': 'Metal Perforated', 'Perforated Stone': 'Stone Perforated', 'Grate': 'Metal Perforated',
    'StoneReflect': 'Stone', 'Bricks': 'Stone', 'Gravel': 'Soil', 'Seabed': 'Soil', 'Mud': 'Soil', 'Grass': 'Soil',
    'PlantPink': 'Plant', 'Water': 'Puddle', 'WaterDeep': 'Puddle', 'Rubber': 'Plastic', 'Steam': 'Default',
    'GlassFloor': 'Glass', 'CarGlass': 'Glass',
}


class SurfaceTable:
    """The table at .gms +0x30 (pass buf[offset:], it runs to the end of the .buf). Kept as bytes
    and patched in place, so an untouched table serialises unchanged."""

    def __init__(self, data):
        self.d = d = bytearray(data)
        u = lambda o: struct.unpack_from('<I', d, o)[0]
        self.h = h = struct.unpack_from('<6I', d, 0)
        self.strings = []
        for i in range(u(h[4])):
            o = u(h[4] + 4 + 4 * i)
            self.strings.append(d[o:d.index(b'\0', o)].decode('latin1'))
        self.materials = [self.strings[u(h[0] + 4 + 8 * i)] for i in range(u(h[0]))]
        if [u(h[0] + 8 + 8 * i) for i in range(len(self.materials))] != list(range(1, len(self.materials) + 1)):
            raise ValueError('surface table: material ids are not 1..n')
        self.props = [struct.unpack_from('<IIIi', d, h[1] + 4 + 16 * i) for i in range(u(h[1]))]
        self.categories = []
        for i in range(u(h[2])):
            name, o = struct.unpack_from('<II', d, h[2] + 4 + 8 * i)
            self.categories.append((self.strings[name], [self.strings[u(o + 4 + 8 * k)] for k in range(u(o))]))
        if h[5] + len(self.materials) * h[3] > len(d):
            raise ValueError('surface table: rows run past the end')

    def material_id(self, name):
        """1-based id as the engine's name lookup (kl2 0x8f4c70) returns it."""
        return self.materials.index(name) + 1

    def cells(self, *types):
        """(material name, property name, category member or None, offset of the dword)."""
        for m, mat in enumerate(self.materials):
            for name, typ, off, cat in self.props:
                if types and typ not in types:
                    continue
                base = self.h[5] + m * self.h[3] + off
                if cat < 0:
                    yield mat, self.strings[name], None, base
                else:
                    for k, member in enumerate(self.categories[cat][1]):
                        yield mat, self.strings[name], member, base + 4 + 4 * k

    def get(self, off):
        return struct.unpack_from('<I', self.d, off)[0]

    def refs(self):
        return {self.get(o) for *_, o in self.cells(ENTITY)} - {NONE}

    def sounds(self):
        return {self.get(o) for *_, o in self.cells(SOUND)} - {0}

    def remap(self, refs=None, sounds=None, missing=None):
        """Renumber entity REFs (dict old -> new) and / or .SND record offsets (dict). A REF
        without a new id becomes `missing` (-1 = no effect) or raises when missing is None;
        an unknown sound offset always raises. Returns how many cells changed."""
        n = 0
        if refs is not None:
            for mat, prop, member, o in self.cells(ENTITY):
                v = self.get(o)
                if v == NONE:
                    continue
                if v not in refs and missing is None:
                    raise KeyError('surface table: %s / %s uses REF %d, which is not carried' % (mat, prop, v))
                struct.pack_into('<I', self.d, o, refs.get(v, missing))
                n += refs.get(v, missing) != v
        if sounds is not None:
            for mat, prop, member, o in self.cells(SOUND):
                v = self.get(o)
                if v:
                    struct.pack_into('<I', self.d, o, sounds[v])
                    n += sounds[v] != v
        return n

    def serialize(self):
        return bytes(self.d)


def material_map(src, dst, alias=MATERIAL_ALIAS):
    """{material id in table `src`: id in table `dst`} by name, then by `alias`; 0 stays 0 (the
    accessors answer 0 for it). Raises if a material has no counterpart."""
    out = {0: 0}
    for i, name in enumerate(src.materials):
        out[i + 1] = dst.material_id(name if name in dst.materials else alias[name])
    return out


def surface_join(systems_table, refs, sounds=None, missing=None):
    """The table of a grafted level: the systems level's, with its REFs (and, if the .SND was
    rebuilt, its sound offsets) renumbered. The map's own table is not used at all."""
    t = SurfaceTable(systems_table)
    t.remap(refs, sounds, missing)
    return t.serialize()


# ------------------------------------------------------------------ bone dynamics (.gms +0x38)
def fdx_read(buf, off):
    """((header 16 bytes), [record], size). A record is a dict of raw byte fields plus 'model'."""
    if buf[off:off + 4] != b'FDX\x04':
        raise ValueError('no FDX v4 block at %#x' % off)
    na, nb = struct.unpack_from('<HH', buf, off + 4)
    o, recs = off + 16, []
    for _ in range(na + nb):
        s, kind, n = o, buf[o], struct.unpack_from('<H', buf, o + 2)[0]
        o += 4
        if kind == 0:
            tot = 0
            for _ in range(n):
                m = struct.unpack_from('<H', buf, o + 6)[0]
                o += 8 + 2 * m
                tot += m
            o += 2 * (tot & 1)
        head, model, o = buf[s:o], struct.unpack_from('<I', buf, o)[0], o + 4
        n1, n2, n3, n4 = struct.unpack_from('<4H', buf, o + 4 + 0x14)
        e = o + 4 + 0x20 + 24 * n1 + 16 * n2 + 8 * n3 + 48 * n4
        recs.append({'kind': kind, 'head': head, 'model': model, 'tail': buf[o:e], 'instances': n4})
        o = e
    return buf[off:off + 16], recs, o - off


def fdx_write(header, recs):
    na = sum(r['kind'] == 0 for r in recs)
    out = header[:4] + struct.pack('<HH', na, len(recs) - na) + header[8:16]
    for r in sorted(recs, key=lambda r: r['kind'] != 0):       # stable: bone records first, as the counts imply
        out += r['head'] + struct.pack('<I', r['model']) + r['tail']
    return out


def fdx_join(parts):
    """parts = [(buf, offset from .gms +0x38 or -1, {old .prm chunk index: new})]. Returns the
    block for the joined level's .buf (put it at an offset divisible by 16, as stock, and store
    that at .gms +0x38) or None = write -1. A record whose model is not carried is dropped."""
    header, recs = None, []
    for buf, off, models in parts:
        if off in (-1, NONE):
            continue
        h, rs, _ = fdx_read(buf, off)
        header = header or h
        recs += [dict(r, model=models[r['model']]) for r in rs if r['model'] in models]
    return fdx_write(header, recs) if recs else None


# ------------------------------------------------------------------ checks on the stock levels
def _levels():
    import glob, os
    from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE
    dd, dm = find(DD_GUESSES, DD_EXE), find(DM_GUESSES, DM_EXE)
    out = [('dd', os.path.join(dd, 'KL_PortBackup', 'Scenes', 'Locations', 'F01', 'F01_Main.zip'))]
    out += [('dd', p) for p in sorted(glob.glob(os.path.join(glob.escape(dd), 'Scenes', 'Locations', '*', '*_Main.zip')))
            if os.sep + 'F01' + os.sep not in p]              # the F01 under Scenes is our build
    return out + [('dm', p) for p in sorted(glob.glob(os.path.join(glob.escape(dm), 'Scenes', 'Locations', '*', '*_Main.zip')))]


def selftest():
    import collections, os, zipfile
    import kl_gms
    c, tables = collections.Counter(), {}
    for game, path in _levels():
        zf = zipfile.ZipFile(path)
        mem = {os.path.splitext(n)[1].lower(): n for n in zf.namelist()}
        read = lambda ext: zf.read(mem[ext]) if ext in mem else None
        raw, buf = kl_gms.unpack(read('.gms')), read('.buf')
        refs, models = set(), set()
        for decl, _tid, _pg in kl_gms.entities(raw):
            rec = 4 * (decl & 0xffffff)
            refs.add(struct.unpack_from('<I', raw, rec + 0x30)[0])
            models.add(struct.unpack_from('<I', raw, rec + 0x0c)[0])
        ident = {r: r for r in refs}
        c['levels'] += 1
        c['sup/zgf constant'] += read('.sup') == SUP and read('.zgf') == ZGF
        # .sgd: container, every tree rebuilt, every REF known, identity join
        sgd = read('.sgd')
        secs = sgd_read(sgd)
        c['sgd container round trip'] += sgd_write(secs) == sgd
        for name, body in secs:
            if 'Octree' in name:
                t = Octree(body)
                c['octrees'] += 1
                c['octree rebuilt byte-identical'] += t.serialize() == body
                c['octree leaves'] += len(t.leaves)
                c['octree leaves with unknown REF'] += sum(l[0] not in refs for l in t.leaves)
            elif name == 'HavokShatterGlassConnectivity':
                g = glass_read(body)
                c['glass sections round trip'] += glass_write(g) == body
                c['glass REFs unknown'] += sum(r not in refs for r, _ in g)
            elif name == 'SecurityZones':
                c['security zone sections'] += len(body) % 64 == 0
        c['sgd identity join'] += sgd_join([(sgd, ident)], glass=True) == sgd
        # .sgp
        sgp = read('.sgp')
        g = Sgp(sgp)
        c['sgp round trip'] += g.serialize() == sgp
        c['sgp identity join'] += Sgp.join([(g, lambda p: True)], [r[0] for r in g.rooms]).serialize() == sgp
        # .hrd
        hrd = read('.hrd')
        if hrd is not None:
            c['hrd files'] += 1
            c['hrd size is a multiple of 28'] += len(hrd) % 28 == 0
            c['hrd join rule'] += hrd_join([(hrd, 5, 5), (hrd, 9, 0)]) == hrd and hrd_join([(hrd, 5, 4)]) is None
        # surface table
        off = struct.unpack_from('<I', raw, 0x30)[0]
        t = SurfaceTable(buf[off:])
        tables.setdefault(game, t)
        c['surface table round trip'] += t.serialize() == buf[off:] and surface_join(buf[off:], ident) == buf[off:]
        c['surface REFs unknown'] += len(t.refs() - refs)
        c['surface layout as %s' % game] += (t.materials, t.props, t.categories) == \
            (tables[game].materials, tables[game].props, tables[game].categories)
        # bone dynamics
        off = struct.unpack_from('<I', raw, 0x38)[0]
        if off != NONE:
            h, recs, size = fdx_read(buf, off)
            c['fdx blocks'] += 1
            c['fdx records'] += len(recs)
            c['fdx round trip'] += fdx_write(h, recs) == buf[off:off + size] == fdx_join([(buf, off, {m: m for m in models})])
            c['fdx models unknown'] += sum(r['model'] not in models for r in recs)
    for k, v in c.items():
        print('%-36s %d' % (k, v))
    mm = material_map(tables['dm'], tables['dd'])
    print('Dead Men -> Dog Days material ids:', ' '.join('%d>%d' % kv for kv in sorted(mm.items())))
    return c


if __name__ == '__main__':
    selftest()
