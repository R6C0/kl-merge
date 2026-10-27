"""
Navigation mesh of the PF4 pathfinder (Dead Men -> Dog Days).

The mesh is a block inside the unpacked .gms, at the offset in header +0x34: u32 size, then the
data. The scene loader (kl2 0x820300) hands it to 0x538bc0, which builds the PF4::ZData the
database keeps at +0xc. Cover boxes, AI and some 25 other sites use that object without a null
check, so a level without a mesh crashes (kl2 0x5503da, at 73 % of the load).

Both games store 13 arrays, counts first (parsers kaneandlynch 0x4ee810 and kl2 0x63e750; header
+ arrays equals the size in every stock level of both games):
  Dead Men  13 x u16 counts + 2 pad bytes; elements of 16 16 12 24 48 20 20 10 2 8 2 2 4 bytes
  Dog Days  13 x u32 counts + 4 pad bytes; elements of 20 20 12 32 72 28 20 16 4 12 4 4 8 bytes
Dog Days widened the 16-bit indices to 32 bits; floats are unchanged.

WHAT THE ARRAYS ARE (D = Dog Days offset, M = Dead Men offset). "code" = read in both exes,
"structure" = an invariant that holds in all 21 Dog Days and all 20 Dead Men levels when the
fields are paired this way (check() tests every one of them), and would not hold otherwise.
  0   tree over the polygons: two children (>= 0 a node of array 0, < 0 a leaf: -1 - c is a
      polygon, or the polygon count for "none") and three floats.            structure (ranges)
  1   second tree: same record; its leaves index array 2.                    structure (ranges)
  2   three floats per leaf of tree 1. Same size, copied.
  3   polygon: u8 edge count +0, u8 +1 = THE NUMBER OF WAYPOINTS ON THE POLYGON (called 'flags'
      here until 2026-10-11; kl2 0x5ce32c: the path search turns that many records of array 10,
      from 'waypoints before' on, into search nodes; kl_maps.nav_facts tests it on every mesh),
      area M+8 D+8, first edge M+0xa D+0xc (code: both
      parsers), waypoints before this polygon M+0xc D+0x10, a node of tree 1 M+0x10 D+0x18.
      structure: first edge = running sum of the edge counts; area < areas, never decreasing;
      "waypoints before" = number of array-5 records on earlier polygons; M+4, M+0x14, D+4,
      D+0x14, D+0x1c are zero in every level.
  4   area: 12 integers + bounding box (6 floats). [0] waypoints, [2] polygons, [5] first
      waypoint (code: kl2 0x45f8ed reads D+0x14, kaneandlynch 0x4ef9f2 reads M+0xa), [6], [7]
      starts of [1], [2], [9..11] positions in arrays 0, 1, 2; [3], [4], [8] zero.
      structure: every start = running sum of its count; [2] = polygons with that area.
  5   waypoint: position, links M+0xc/+0xe D+0xc/+0x10 = the range [from, to) of its records in
      array 7 (code: kaneandlynch 0x4efcec, kl2 0x5ce01a), polygon M+0x10 D+0x14, a run-time
      word M+0x12 D+0x18 that both parsers clear.
      structure: the ranges chain from 0 to the array-7 count; a waypoint lies on a polygon of
      its area.
  6   five floats (edge vertex and a 2-D normal). Same size, copied.
  7   LINK between two waypoints (ladders, drops, vaults ...), 10 -> 16 bytes. All from code
      (path search kaneandlynch 0x4efd10.., kl2 0x5ce040..; box switch 0x4ef910 / 0x45f810):
        s16 cost            M+0   D+0   (movsx word in both; Dog Days files carry junk in
                                         D+2: 0x03bd in all 192 records, written as 0 here)
        target waypoint     M+2   D+4   number inside the target area
        target area         M+4   D+8   waypoint = area[5] + number
        u8 kind             M+6   D+0xc copied into the path node (+0x1c) the search returns
        u8                  M+7   D+0xd the only byte left on each side (it looks like a
                                         heading: 0, 127, 128, 191, 255 are common)
        u16 switch          M+8   D+0xe run-time flags (or / and-not by the box switch), -1 on disk
      KINDS: Dog Days levels only ever use kind 2 (192 links in 12 levels). Dead Men uses 1
      (195), 2 (203), 3 (34) and 6 (25). What Dog Days' AI does with a path node of another kind
      was NOT read. DECISION: links of a kind no Dog Days level has are dropped by default
      (link_kinds) and the waypoints' ranges are rebuilt. LOST: those shortcuts for the AI -
      M03_FA_A's single link (kind 6), 10 of M09_A's 15 (kinds 6 and 1; the 5 of kind 2 stay).
      ASSUMPTION: kind 2 means the same in both games.
  8, 11, 12   empty in every level of both games (41 of 41), and neither parser touches their
      contents. There is no data to convert or to test on: a mesh that has them is refused.
  9   polygon edge: neighbour polygon (-1 none, < -1: -2 - x) M+0 D+0, vertex (array 6) M+2
      D+4, a link slot both parsers overwrite M+4 D+8.                         code + structure
  10  a permutation of the waypoint numbers, u16 -> u32.                      structure
NOT established: the meaning of area fields [1] / [6] and of the link byte M+7; none is
reinterpreted, they are carried over.

THE FLOATS (2026-10-27, read in kl2.exe, then checked on the 20 stock Dog Days meshes and the
DM11B build with tools/kl_pf4_translate_test.py). Mesh coordinates are world (x, z) with the
height h = world y; a vertex or waypoint record is (x, z, h).
  tree node (arrays 0 and 1, both games' record)   child0, child1, a, b, c:
      next = child1 if a * x + b * z >= c else child0  (a, b are NOT unit: any scale)
      tree 0 (locate, kl2 0x80d600): start at area field [9], children are absolute indices,
          a negative child is a leaf: polygon = -2 - child (child -1 = no polygon). The
          polygon centroid of 27786 of 27800 polygons descends to its own polygon.
      tree 1 (height, kl2 0x55f5a0): start at polygon D+0x18, children are RELATIVE to that
          start node (next = start + child), a negative child is a leaf: array-2 record
          = -1 - child (negative = none, height 0).
  array 2   P, Q, R: the polygon's height plane, h = P * x + Q * z + R (27288 of 27799
      centroids within 1 unit; the rest are non-planar polygons).
  array 6   x, z, h, nx, nz: (nx, nz) is the unit sum of the inward normals of the WALL edges
      (neighbour -1) that meet at the vertex (66592 of 67499 used vertices exact; zero on the
      464 unused vertices); it has no distance term.
  area box  D+0x30 min x, +0x34 min y, +0x38 min z, +0x3c max x, +0x40 max y, +0x44 max z
      (locate tests x and z only; 121711 of 121713 vertices inside their area's box).
A world translation t therefore only touches: node c += a * tx + b * tz; plane R += ty - P * tx
- Q * tz; vertices, waypoints and boxes += t (translate() below). Costs, kinds, headings,
normals and every index stay.
"""
import struct

DM_SIZE = (16, 16, 12, 24, 48, 20, 20, 10, 2, 8, 2, 2, 4)
DD_SIZE = (20, 20, 12, 32, 72, 28, 20, 16, 4, 12, 4, 4, 8)
DD_LINK_KINDS = (2,)                            # array-7 kinds stock Dog Days levels use
EMPTY = (8, 11, 12)


def _wide(v):
    """u16 index -> u32, keeping 'none' and the other negative codes negative."""
    return v - 0x10000 & 0xffffffff if v >= 0x8000 else v


def _a01(r):
    a, b, x, y, z = struct.unpack('<hh3f', r)
    return struct.pack('<ii3f', a, b, x, y, z)

def _a3(r):
    n, flag, pad, zero, area, first, before, node, tail = struct.unpack('<BBHIHHIII', r)
    return struct.pack('<BBHIIIIIII', n, flag, pad, zero, _wide(area), _wide(first), before, 0, node, tail)

def _a4(r):
    v = struct.unpack('<12H6f', r)
    return struct.pack('<12I6f', *([_wide(x) for x in v[:12]] + list(v[12:])))

def _a5(r):
    x, y, z, a, b, poly, _runtime = struct.unpack('<3fHHHH', r)
    return struct.pack('<3fIIIHH', x, y, z, _wide(a), _wide(b), _wide(poly), 0, 0)

def _a7(r):
    cost, number, area, kind, heading, switch = struct.unpack('<hhhBBH', r)
    return struct.pack('<hHiiBBH', cost, 0, number, area, kind, heading, switch)

def _a9(r):
    node, vertex, link = struct.unpack('<hHI', r)
    return struct.pack('<iII', node, vertex, link)

def _a10(r):
    return struct.pack('<I', _wide(struct.unpack('<H', r)[0]))

RECORD = {0: _a01, 1: _a01, 2: bytes, 3: _a3, 4: _a4, 5: _a5, 6: bytes, 7: _a7, 9: _a9, 10: _a10}


def counts(block, wide):
    """The 13 array counts of a mesh block (without its size dword)."""
    return struct.unpack_from('<13I' if wide else '<13H', block, 0)


def split(block, wide):
    """(counts, [list of records per array]) of a mesh block of either game."""
    n, sizes = counts(block, wide), DD_SIZE if wide else DM_SIZE
    o = 56 if wide else 28
    if o + sum(c * s for c, s in zip(n, sizes)) != len(block):
        raise ValueError('navigation mesh does not have %s layout' % ('Dog Days\'' if wide else 'Dead Men\'s'))
    out = []
    for c, s in zip(n, sizes):
        out.append([block[o + s * i:o + s * i + s] for i in range(c)]); o += c * s
    return n, out


def join(arrays):
    """Dog Days mesh block from 13 lists of Dog Days records."""
    return struct.pack('<13I4x', *[len(a) for a in arrays]) + b''.join(b''.join(a) for a in arrays)


def convert(block, link_kinds=DD_LINK_KINDS, report=None):
    """Dead Men mesh data -> Dog Days mesh data (both without the leading size dword).
    link_kinds: array-7 kinds to keep (None = all). report: a dict that receives links,
    links_kept and dropped {kind: n}."""
    n, src = split(block, False)
    for k in EMPTY:
        if n[k]:
            raise ValueError('navigation mesh array %d is not empty: no level of either game has one' % k)
    out = [[RECORD[k](r) for r in src[k]] for k in range(13)]
    dropped = {}
    if n[7]:
        kinds = [r[6] for r in src[7]]
        keep = [link_kinds is None or k in link_kinds for k in kinds]
        for k, ok in zip(kinds, keep):
            if not ok:
                dropped[k] = dropped.get(k, 0) + 1
        new = [0]                                   # new index of each old link boundary
        for ok in keep:
            new.append(new[-1] + ok)
        out[7] = [r for r, ok in zip(out[7], keep) if ok]
        for i, r in enumerate(out[5]):
            a, b = struct.unpack_from('<II', r, 12)
            if not a <= b <= n[7]:
                raise ValueError('waypoint %d: link range %d..%d outside array 7' % (i, a, b))
            out[5][i] = r[:12] + struct.pack('<II', new[a], new[b]) + r[20:]
    if report is not None:
        report.update(links=n[7], links_kept=len(out[7]), dropped=dropped)
    data = join(out)
    check(data, link_kinds)
    return data


def check(block, link_kinds=None):
    """Every structural rule the 21 stock Dog Days meshes obey (see the docstring), applied to
    a Dog Days mesh block; raises on the first one broken, returns the counts. With
    link_kinds also: every link is of one of these kinds."""
    n, A = split(block, True)
    if block[52:56] != bytes(4):
        raise ValueError('header padding is not zero')
    def bad(what, *a):
        raise ValueError('navigation mesh: ' + what % a)
    for k in EMPTY:
        if n[k]:
            bad('array %d is not empty', k)
    for k, leaves in ((0, n[3] + 1), (1, n[2])):
        for i, r in enumerate(A[k]):
            for c in struct.unpack_from('<ii', r):
                if not (c < n[k] if c >= 0 else -1 - c < leaves):
                    bad('tree %d node %d: child %d out of range', k, i, c)
    polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
    areas = [struct.unpack('<12I', r[:48]) for r in A[4]]
    ways = [struct.unpack('<III', r[12:24]) for r in A[5]]
    edges, on = 0, [0] * (n[3] + 1)
    for i, w in enumerate(ways):
        if w[2] >= n[3]:
            bad('waypoint %d: polygon %d', i, w[2])
        on[w[2] + 1] += 1                           # (the word at +0x18 is junk on disk: the parser clears it)
    before = 0
    for i, (cnt, _flag, pad, zero, area, first, ways_before, z1, node, z2) in enumerate(polys):
        before += on[i]
        if pad or zero or z1 or z2:
            bad('polygon %d: a zero field is set', i)
        if first != edges or area >= n[4] or (i and area < polys[i - 1][4]):
            bad('polygon %d: first edge %d (expected %d) or area %d', i, first, edges, area)
        if ways_before != before or node >= n[1]:
            bad('polygon %d: %d waypoints before it (expected %d) or tree node %d', i, ways_before, before, node)
        edges += cnt
    if edges != n[9]:
        bad('polygons own %d edges, array 9 has %d', edges, n[9])
    start = [0, 0, 0]
    for i, a in enumerate(areas):
        if list(a[5:8]) != start or a[3] or a[4] or a[8]:
            bad('area %d: starts %r, expected %r', i, a[5:8], start)
        if a[2] != sum(1 for p in polys[a[7]:a[7] + a[2]] if p[4] == i) or a[9] > n[0] or a[10] > n[1] or a[11] > n[2]:
            bad('area %d: polygon run or tree positions', i)
        if any(polys[w[2]][4] != i for w in ways[a[5]:a[5] + a[0]]):
            bad('area %d: a waypoint lies on a polygon of another area', i)
        if i and any(a[k] < areas[i - 1][k] for k in (9, 10, 11)):
            bad('area %d: tree positions go backwards', i)
        box = struct.unpack_from('<6f', A[4][i], 48)
        if any(box[k] > box[k + 3] for k in range(3)):
            bad('area %d: empty bounding box', i)
        start = [start[k] + a[k] for k in range(3)]
    if start[0] != n[5] or start[2] != n[3]:
        bad('areas own %d waypoints and %d polygons of %d and %d', start[0], start[2], n[5], n[3])
    at = 0
    for i, w in enumerate(ways):
        if w[0] != at or w[1] < w[0]:
            bad('waypoint %d: link range %d..%d does not follow %d', i, w[0], w[1], at)
        at = w[1]
    if at != n[7]:
        bad('waypoints own %d links, array 7 has %d', at, n[7])
    for i, r in enumerate(A[7]):
        cost, _junk, number, area, kind, _heading, _switch = struct.unpack('<hHiiBBH', r)
        if cost <= 0 or not 0 <= area < n[4] or not 0 <= number < areas[area][0]:
            bad('link %d: cost %d, target %d of area %d', i, cost, number, area)
        if link_kinds is not None and kind not in link_kinds:
            bad('link %d is of kind %d', i, kind)
    for i, r in enumerate(A[9]):
        nb, vertex, link = struct.unpack('<iII', r)
        if not (nb == -1 or 0 <= (nb if nb >= 0 else -2 - nb) < n[3]) or vertex >= n[6] or link:
            bad('edge %d: neighbour %d, vertex %d, link %d', i, nb, vertex, link)
    if n[10] != n[5] or sorted(struct.unpack('<%dI' % n[10], b''.join(A[10]))) != list(range(n[5])):
        bad('array 10 is not a permutation of the waypoints')
    return n


# ---------------------------------------------------------------- world translation
def translate(block, t):
    """A Dog Days mesh block moved by the world vector t = (tx, ty, tz): the mesh of the same
    level built t further along. Only the absolute floats change (docstring: THE FLOATS); every
    index, count, cost and normal is copied. Values are computed in double and rounded once to
    float32, so a moved mesh is exact to half a float32 ulp of each result (about 0.001 units at
    |x| < 16384): translate(translate(b, t), -t) is NOT bit-identical to b, see check_translate."""
    tx, ty, tz = (float(v) for v in t)
    n, A = split(block, True)
    out = list(A)
    def node(r):
        c0, c1, a, b, c = struct.unpack('<ii3f', r)
        return struct.pack('<ii3f', c0, c1, a, b, c + a * tx + b * tz)
    out[0] = [node(r) for r in A[0]]
    out[1] = [node(r) for r in A[1]]
    out[2] = [struct.pack('<3f', p, q, s + ty - p * tx - q * tz) for p, q, s in (struct.unpack('<3f', r) for r in A[2])]
    out[4] = [r[:48] + struct.pack('<6f', *[v + d for v, d in zip(struct.unpack_from('<6f', r, 48), (tx, ty, tz) * 2)]) for r in A[4]]
    out[5] = [struct.pack('<3f', x + tx, z + tz, h + ty) + r[12:] for r in A[5] for x, z, h in (struct.unpack_from('<3f', r),)]
    out[6] = [struct.pack('<5f', x + tx, z + tz, h + ty, nx, nz) for r in A[6] for x, z, h, nx, nz in (struct.unpack('<5f', r),)]
    return join(out)


def locate(mesh, x, z):
    """(polygon, height) of the world point (x, z) the way kl2 0x55e6e0 starts: the first area
    whose box holds (x, z) and whose tree 0 names a polygon, then that polygon's height plane;
    (-1, None) when no area does. mesh = split(block, True). The game then prefers, over all
    areas, the polygon nearest in height to the point's y; this helper stops at the first hit
    (enough for a same-mesh comparison)."""
    n, A = mesh
    for r in A[4]:
        f = struct.unpack('<12I6f', r)
        if not (f[12] <= x <= f[15] and f[14] <= z <= f[17]) or f[9] == 0xffffffff:
            continue
        leaf = _descend(A[0], f[9], x, z, 0)
        if leaf is None:
            continue
        p = -2 - leaf
        if 0 <= p < n[3]:
            return p, height(mesh, p, x, z)
    return -1, None


def height(mesh, poly, x, z):
    """Height of the mesh under (x, z) on polygon poly (kl2 0x55f5a0): tree 1 from the
    polygon's node, children relative to it, the leaf's plane. 0.0 with no plane."""
    n, A = mesh
    start = struct.unpack_from('<I', A[3][poly], 0x18)[0]
    if start >= n[1]:
        return 0.0
    leaf = _descend(A[1], start, x, z, start)
    if leaf is None or leaf >= 0:
        return 0.0
    leaf = -1 - leaf
    if leaf >= n[2]:
        return 0.0
    p, q, r = struct.unpack('<3f', A[2][leaf])
    return p * x + q * z + r


def _descend(nodes, node, x, z, rel):
    """Walk a tree from node: the negative child the point ends at, None on a cycle."""
    for _ in range(len(nodes) + 1):
        c0, c1, a, b, c = struct.unpack('<ii3f', nodes[node])
        nxt = c1 if a * x + b * z >= c else c0
        if nxt < 0:
            return nxt
        node = nxt + rel
        if node >= len(nodes):
            return None
    return None
