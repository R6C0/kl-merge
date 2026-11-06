"""HavokShatterGlassConnectivity of an .sgd: decode, recompute from the level's shard meshes, insert.

WHY (2026-11-06, re/open_work_log.md): a Dead Men map ported into a Dog Days slot has its .sgd section
HavokShatterGlassConnectivity stripped (kl_members.sgd_join), so the first time a pane is touched the engine
computes every neighbour table itself. That is quadratic in shards and in vertices and froze the main thread
21-29 s per seat on Last Call (DM05A) in the round-2 reset.

WHAT THE ENGINE DOES (kl2.exe, READ from the disassembly 2026-11-06; every address below is a kl2 VA)
  0x4dfd60   pane object (this = ebx; [+0x48] = piece count, [+0x84] = the table, [+0x88] = ENTITY ID of the pane's shard
             group). First asks the glass manager [0x153ab14] (0x4eccd0) for a PRECOMPUTED table with that id; if it has one
             ([this+0x84] <- copy of its n * 40 bytes) it returns at once. Else:
               1. pieces = the shard group's children, in chain order ([group+0x40] first, then the u16 at +0x5e);
               2. per piece 0x754d90 collects the vertices of its meshes (lType 8 objects of the piece's model; if any object
                  has flag bits 0x3c at object +0x14 the flagged ones are left out), transformed to WORLD space;
               3. for every ordered pair (i, j), i != j: 0x4a45a0 counts vertex pairs (a of i, b of j) whose distance
                  (0x6499b0, euclidean, float32) is STRICTLY below [0xb89a20] = 2.5 (float32 constant, read from the exe);
                  a count > 0 appends j to piece i's record unless that record already holds 16: record at
                  i * 40 : [+0] u8 count, [+1] u8 mask (|= 1 << count, an 8-bit shift: only the first 8 neighbours set a bit),
                  [+8 + 2 * count] u16 j. j runs 0..n-1, so a record lists its neighbours in ascending order, at most 16.
  0x8aba40   (.sgd section loader, only when the glass manager exists): u32 n, then n x {u32 count, u32 ID, count x 40 bytes};
             each becomes one cache entry keyed by ID. The key is compared with [pane + 0x88]; the Dead Men files prove it is
             the shard group's REF label (kl_scene Entity.ref), NOT its slot: all 10 keys of M05A_Main.sgd are lType 0x1000ca
             groups by REF, and the live DM05A has the same groups under other REFs.
  Dog Days' own 21 stock .sgd files carry NO such section (measured: only SecurityZones + the two octrees), so Dog Days
  stock panes are computed on first use too (few shards, ~0.01 s); the section exists in Dead Men levels only. Therefore the
  validation reference is Dead Men's shipped data (M05A: 10 panes, 691 records), not a Dog Days file.
  Unused bytes of a record: [+2..+3] = 0xcd 0xcd, [+4..+7] = 0, [+8 + 2 * count ..] = 0xff (all measured on the shipped data).

CLI
  python tools/kl_glass_conn.py check <level.zip> [more.zip ...]
  python tools/kl_glass_conn.py build <in.zip> <out.zip> [--sgd-from <dead men level.zip>] [--force]
      computes the section for every shard group of the level and inserts it into the .sgd; every other member is copied
      byte-identical (stored compression and order as in <in>). --sgd-from: use a Dead Men level's SHIPPED records for the
      groups it has (matched by scene path, REF renumbered) and compute only the rest.
  python tools/kl_glass_conn.py compare <dead men level.zip>   recompute that level's own shipped section and print the match rate
"""
import math, os, struct, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_members as MB
import kl_scene
import kl_prmgraph

SECTION = 'HavokShatterGlassConnectivity'
GROUP, SHARD = 0x1000ca, 0x200002          # ZAllocMany group, its children (both from the .gms type ids)
THRESHOLD = 2.5                            # float32 at kl2 0xb89a20 (read from the exe)
MAXN = 16
FLAGS = 0x3c                               # mesh object +0x14 bits that 0x754d90 leaves out when any object has them


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


# ------------------------------------------------------------------ scene side
def _mul(par, loc):
    """(rot9, trans3) composed like kl_int16_range_check.mul (row vectors: p' = p * R + t)."""
    pr, pt = par
    lr, lt = loc
    t = tuple(pt[i] + sum(lt[j] * pr[j * 3 + i] for j in range(3)) for i in range(3))
    r = tuple(sum(lr[a * 3 + k] * pr[k * 3 + c] for k in range(3)) for a in range(3) for c in range(3))
    return r, t


AXES = (2, 1, 0)   # the .gms stores translation and rotation in (z, y, x) order against the vertices' (x, y, z): MEASURED, with
# the .gms order unchanged 0 of 691 shipped records match, reversed 691 of 691 (kl_members: the octree's stored order is (z, y, x) too)


def worlds(scene):
    """{entity: (rot9, trans3)} composed down the tree, in the vertex axis order (AXES applied to every translation / rotation)."""
    out = {}
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))
    stack = [(r, ident) for r in scene.roots]
    while stack:
        e, par = stack.pop()
        r, t = struct.unpack('<12f', e.rot)[:9], struct.unpack('<4f', e.trans)[:3]
        w = _mul(par, (tuple(r[AXES[a] * 3 + AXES[b]] for a in range(3) for b in range(3)), tuple(t[AXES[i]] for i in range(3))))
        out[e] = w
        stack.extend((k, w) for k in e.kids)
    return out


def local_vertices(prm, model):
    """Positions (model space) of the vertices 0x754d90 takes from a model root (lType 7), [] when it has none."""
    if not model or model >= len(prm.chunks) or prm.chunks[model] is None or prm.u16(model, 2) != 7:
        return []
    n, tab = prm.u32(model, 0x14), prm.u32(model, 0x18)
    objs = [prm.u32(tab, 4 * i) for i in range(n)]
    objs = [o for o in objs if o and prm.u16(o, 2) == 8]
    if any(prm.u32(o, 0x14) & FLAGS for o in objs):
        objs = [o for o in objs if not prm.u32(o, 0x14) & FLAGS]      # GUESS: the second pass of 0x754d90 tests 0x3e, here 0x3c
    out = []
    for o in objs:
        sub = prm.u32(o, 0x28)
        k = 0
        while sub and prm.u32(sub, 4 * k):
            d = prm.u32(sub, 4 * k)
            cnt, vtx = prm.u32(d, 0), prm.u32(d, 4)
            data = prm.chunks[vtx]
            # chunks are padded to 16 bytes, so len // cnt is wrong (5 x 40 = 200 -> 208); every shard mesh of the 21 Dead Men
            # and the Last Call levels has 40-byte vertices (position first): 40 first, then other 4-multiples that fit
            stride = next((st for st in (40,) + tuple(range(12, 100, 4)) if cnt and 0 <= len(data) - st * cnt < 16), 0)
            if stride:
                out.extend(struct.unpack_from('<3f', data, stride * v) for v in range(cnt))
            k += 1
    return out


def world_vertices(prm, shard, w):
    rot, t = w
    out = []
    for x, y, z in local_vertices(prm, shard.model):
        out.append(tuple(f32(t[i] + x * rot[i] + y * rot[3 + i] + z * rot[6 + i]) for i in range(3)))
    return out


def groups(scene):
    """[ZAllocMany shard group entities]: lType 0x1000ca with children, all lType 0x200002."""
    return [e for e in scene.entities() if e.tid == GROUP and e.kids and all(k.tid == SHARD for k in e.kids)]


def path(e):
    p = []
    while e:
        p.append(e.name.decode('latin1'))
        e = e.parent
    return '/'.join(reversed(p))


# ------------------------------------------------------------------ the computation
def neighbours(pieces, thr=THRESHOLD):
    """pieces = [[(x, y, z) world vertices]] -> [[j, ...]] per piece, ascending, at most 16 (0x4dfd60 + 0x4a45a0).
    A pair is a neighbour when ANY vertex of one lies strictly closer than thr to ANY vertex of the other."""
    cell = thr
    grid = {}
    for i, vs in enumerate(pieces):
        for v in vs:
            if not all(map(math.isfinite, v)):
                continue                      # a NaN compares unordered: the engine's test (ah & 0x41) skips the pair, so it never counts
            grid.setdefault((math.floor(v[0] / cell), math.floor(v[1] / cell), math.floor(v[2] / cell)), []).append((i, v))
    near = [set() for _ in pieces]
    t2 = thr * thr
    for (cx, cy, cz), items in grid.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    other = grid.get((cx + dx, cy + dy, cz + dz))
                    if not other:
                        continue
                    for i, a in items:
                        for j, b in other:
                            if j != i and j not in near[i]:
                                d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
                                if d < t2 and f32(math.sqrt(d)) < thr:
                                    near[i].add(j)
    return [sorted(s)[:MAXN] for s in near]


def encode(nb):
    """One neighbour list -> the 40-byte record."""
    r = bytearray(b'\xff' * 40)
    r[0], r[1] = len(nb), sum(1 << k for k in range(min(len(nb), 8)))
    r[2:4] = b'\xcd\xcd'
    r[4:8] = bytes(4)
    for k, j in enumerate(nb):
        struct.pack_into('<H', r, 8 + 2 * k, j)
    return bytes(r)


def decode(rec):
    """40-byte record -> (count, mask, [neighbours])."""
    return rec[0], rec[1], [struct.unpack_from('<H', rec, 8 + 2 * k)[0] for k in range(rec[0])]


def compute(scene, prm, grp):
    """[40-byte records] of one shard group, kids in scene order (VALIDATED against Dead Men's shipped data: see compare())."""
    W = worlds(scene)
    return [encode(nb) for nb in neighbours([world_vertices(prm, k, W[k]) for k in grp.kids])]


# ------------------------------------------------------------------ archives
def _member(zf, ext):
    m = [n for n in zf.namelist() if n.lower().endswith(ext)]
    return m[0] if len(m) == 1 else None


def load(zf):
    """(scene, prm or None, sgd member name or None)."""
    sc = kl_scene.read(zf)
    pm = _member(zf, '.prm')
    prm = kl_prmgraph.read(zf.read(pm)) if pm else None
    return sc, prm, _member(zf, '.sgd')


def section_of(zf, sgd):
    """[(REF, [records])] of the level's section, or None."""
    return next((MB.glass_read(p) for n, p in MB.sgd_read(zf.read(sgd)) if n == SECTION), None)


def check(zpath):
    """Rows of text describing the level; returns (text, panes, with_section)."""
    with zipfile.ZipFile(zpath) as zf:
        sc, prm, sgd = load(zf)
        if sgd is None:
            return ['no .sgd'], 0, 0
        gs = groups(sc)
        have = section_of(zf, sgd)
        W = worlds(sc)
        rows, shards, verts, work = [], 0, 0, 0
        for g in gs:
            vs = [world_vertices(prm, k, W[k]) for k in g.kids]
            shards += len(vs)
            verts += sum(map(len, vs))
            work += sum(map(len, vs)) ** 2
        refs = {r for r, _ in have} if have else set()
        rows.append('%s: %d shard groups, %d shards, %d vertices (O(n^2) vertex pairs the engine would test: %.1f M), section %s'
                    % (os.path.basename(zpath), len(gs), shards, verts, work / 1e6,
                       'PRESENT: %d panes, %d records' % (len(have), sum(len(r) for _, r in have)) if have else 'ABSENT'))
        if have:
            ids = {g.ref for g in gs}
            rows.append('  section keys that are shard groups of this scene: %d of %d; shard groups without an entry: %d'
                        % (len(refs & ids), len(refs), len(ids - refs)))
        return rows, len(gs), len(have or [])


def compare(zpath, report=None):
    """Recompute the level's own shipped section; returns (panes, records_total, records_equal, panes_equal, differing list)."""
    with zipfile.ZipFile(zpath) as zf:
        sc, prm, sgd = load(zf)
        have = section_of(zf, sgd)
        if not have:
            return 0, 0, 0, 0, []
        byref = {g.ref: g for g in groups(sc)}
        W = worlds(sc)
        tot = eq = peq = 0
        bad = []
        for ref, recs in have:
            g = byref[ref]
            mine = [encode(nb) for nb in neighbours([world_vertices(prm, k, W[k]) for k in g.kids])]
            e = sum(a == b for a, b in zip(mine, recs)) if len(mine) == len(recs) else 0
            tot += len(recs)
            eq += e
            peq += e == len(recs)
            if e != len(recs):
                bad.append((ref, path(g), len(recs), len(mine), e))
        return len(have), tot, eq, peq, bad


def build_section(sc, prm, shipped=None):
    """[(REF, records)] for every shard group; shipped = {scene path tail: records} wins over the computation."""
    out, W, gs = [], worlds(sc), groups(sc)
    refs = [g.ref for g in gs]
    if len(set(refs)) != len(refs):
        raise SystemExit('duplicate shard group REFs: the section is keyed by REF, refusing to build')
    big = [path(g) for g in gs if len(g.kids) > 255]
    if big:
        raise SystemExit('shard groups over 255 pieces (u8 neighbour ids would overflow): %s' % big[:3])
    tails = [path(g).split('/', 3)[-1] for g in gs]
    for g, tail in zip(gs, tails):
        # a tail that names two groups here could take the other group's records: those are always computed
        recs = shipped.get(tail) if shipped and tails.count(tail) == 1 else None
        if recs is None or len(recs) != len(g.kids):
            recs = [encode(nb) for nb in neighbours([world_vertices(prm, k, W[k]) for k in g.kids])]
        out.append((g.ref, recs))
    return out


def insert(in_zip, out_zip, shipped=None, force=False):
    """Copy in_zip -> out_zip with the section added to the .sgd (every other member byte-identical, same order and compression)."""
    with zipfile.ZipFile(in_zip) as zi:
        sc, prm, sgd = load(zi)
        secs = MB.sgd_read(zi.read(sgd))
        if any(n == SECTION for n, _ in secs) and not force:
            raise SystemExit('the .sgd has the section already (--force replaces it)')
        items = build_section(sc, prm, shipped)
        secs = [(n, p) for n, p in secs if n != SECTION]
        # same order as Dead Men's files: SecurityZones, glass, then the octrees
        pos = 1 if secs and secs[0][0] == 'SecurityZones' else 0
        secs.insert(pos, (SECTION, MB.glass_write(items)))
        new = MB.sgd_write(secs)
        tmp = out_zip + '.tmp'
        with zipfile.ZipFile(tmp, 'w') as zo:
            for info in zi.infolist():
                data = new if info.filename == sgd else zi.read(info.filename)
                zo.writestr(info, data, compress_type=info.compress_type)
        os.replace(tmp, out_zip)
    return items


def shipped_by_path(dm_zip):
    """{scene path tail: records} of a Dead Men level's shipped section."""
    with zipfile.ZipFile(dm_zip) as zf:
        sc, prm, sgd = load(zf)
        have = section_of(zf, sgd) or []
        byref = {g.ref: g for g in groups(sc)}
        tails = [path(byref[r]).split('/', 3)[-1] for r, _ in have if r in byref]
        # path tails are not unique (M05_A has several): a tail shipped twice is dropped, so those groups are computed
        return {t: recs for t, (r, recs) in zip(tails, [h for h in have if h[0] in byref]) if tails.count(t) == 1}


def main(a):
    if len(a) >= 2 and a[0] == 'check':
        for z in a[1:]:
            for row in check(z)[0]:
                print(row)
        return 0
    if len(a) >= 2 and a[0] == 'compare':
        n, tot, eq, peq, bad = compare(a[1])
        print('%d panes, %d records: %d byte-equal (%.2f %%), %d panes fully equal' % (n, tot, eq, 100.0 * eq / max(tot, 1), peq))
        for b in bad:
            print('  differs: REF %d %s shipped %d mine %d equal %d' % b)
        return 0 if tot == eq else 1
    if len(a) >= 3 and a[0] == 'build':
        shipped = shipped_by_path(a[a.index('--sgd-from') + 1]) if '--sgd-from' in a else None
        items = insert(a[1], a[2], shipped, '--force' in a)
        print('wrote %s: %d panes, %d records' % (a[2], len(items), sum(len(r) for _, r in items)))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
