#!/usr/bin/env python3
"""
DM02 rear stops behind the cut shutters (2026-10-26, offline; NOT committed).

PROBLEM: hvk3 cut the static HVK shutter planes REF 24710 / 24711 / 24712 (slots 1007..1009, list chunk 1; now copies of the
filler REF 20069) so the co-op shops can be walked into. Behind each shutter the shop floor ends in the open at |x| = 30 m
(site 1: x -30, z 10..17; sites 2/3: x +30), so a player walks off and falls out of the world.

HOW (option b of the brief): a list code is a MOPP over ONE chunk of 510 static placements, addressed by position, and it returns
a child only inside that child's old box. So a placement MOVED inside its old chunk is never found. Instead:
  1. the live file's static run (3797 placements = 7 * 510 + 227) is padded to a multiple of 510 with copies of the live filler
     (REF 20069) - the way kl_hvk.join pads between two maps (those copies are never returned by any list code);
  2. the three ORIGINAL shutter planes (4 vertices, 2 triangles, flags 0x72, surface 0) are appended as a NEW chunk of three static
     placements, each translated by dx = -10 m (site 1) / +10 m (sites 2, 3) along x ONLY. The placement position and the per-placement
     MOPP offset (x) move by the same amount; the code bytes stay, because a MOPP code is relative to its own offset. Their z/y extent
     is the old shutter's (z 10.32..16.72, y 5.00..8.10), x = -29.90 / +29.90 (10 cm inside the floor edge);
  3. the new chunk gets one list code of its own, built here: 'return all three children' = a split with maxLeft 0xff / minRight 0x00
     (everything goes both ways, the form the stock codes use: '10 ff 00 01 31 30'), left child inline, right child behind the jump.
     Bytes: 10 ff 00 01 30 | 10 ff 00 01 31 32.
Everything else in the file (every shape record, placement, MOPP code and the 8 list codes) is byte-for-byte the live one.

GUESSES (marked GUESS below): header offset / scale of the new list code are not read by a code that has no cut op; the REF of the
new placements is the shop's own side wall (WallA_10mDor) so the 'Open' DeactivateGeom on the shutter REF can never touch it; the
engine takes a 9th list shape and a 3-child last chunk (the stock last chunk is partial too: 227 here).
"""
import hashlib
import os
import shutil
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hvk
import kl_escape
import kl_graft

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
DM02 = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM02')
LIVE = os.path.join(DM02, 'F02_Main.zip')
LIVE_MD5 = '6d380f5d2d16a8ffa99c87cdb17cbb2e'            # hvk3
PRE = os.path.join(DM02, 'F02_Main.zip.before-1026solo3')  # the file hvk3 was cut from (shutter planes still in it)
PRE_MD5 = '505735d2d466c5a0e025ddb1e2ef3dbf'
OUT = r'C:\kl_build_1024\dm02_rearwall_1026'
TAG = '.before-1026rear'
FILLER_REF = 20069
# shutter REF -> (dx in metres, REF the new placement carries, site label). The new placements carry the filler REF 20069:
# it is already duplicated in the live file (hvk3 + join padding), while a real wall REF (23256/23241/23248) would appear twice
# among the statics, which no stock map does (review wmmy6foln: the REF-indexed handle table may then point at the plane).
SITES = {24710: (-10.0, FILLER_REF, 'site 1 (x -30, z 10..17)'),
         24711: (+10.0, FILLER_REF, 'site 2 (x +30, z 10..17)'),
         24712: (+10.0, FILLER_REF, 'site 3 (x +30, z -27..-20)')}
STOP_X = {24710: -29.90, 24711: +29.90, 24712: +29.90}


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def hvk_name(z):
    n = [x for x in z.namelist() if x.endswith('.HVK')]
    if len(n) != 1:
        raise ValueError('HVK members %s' % n)
    return n[0]


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def world_verts(s, inst):
    f = struct.unpack_from('<12f', inst, 0)
    p, R = f[:3], f[3:]
    out = []
    for j in range(len(s.verts) // s.vstride):
        v = struct.unpack_from('<3f', s.verts, s.vstride * j)
        out.append(tuple(p[c] + sum(v[r] * R[c * 3 + r] for r in range(3)) for c in range(3)))
    return out


def tris(s):
    return [struct.unpack_from('<3H', s.idx, 6 * k) for k in range(len(s.idx) // 6)]


def move(inst, mopp, dx):
    """The placement and its MOPP record moved by dx metres along x. The code bytes are not touched (relative to the offset)."""
    x, y, z = struct.unpack_from('<3f', inst, 0)
    inst2 = struct.pack('<3f', f32(x + dx), y, z) + inst[12:]
    ox, oy, oz, sc = struct.unpack('<4f', mopp[0])
    return inst2, (struct.pack('<4f', f32(ox + dx), oy, oz, sc), mopp[1])


def list_code_all(n):
    """List code returning children 0..n-1 for ANY query: n-1 nested splits (maxLeft 0xff, minRight 0x00, jump = left length)."""
    if n < 1 or n > 31:
        raise ValueError(n)
    if n == 1:
        return bytes([0x30])
    if n == 2:
        return bytes([0x10, 0xff, 0x00, 0x01, 0x30, 0x31])
    rest = list_code_all_from(1, n)
    return bytes([0x10, 0xff, 0x00, 0x01, 0x30]) + rest


def list_code_all_from(a, n):
    if a == n - 1:
        return bytes([0x30 + a])
    if a == n - 2:
        return bytes([0x10, 0xff, 0x00, 0x01, 0x30 + a, 0x30 + a + 1])
    return bytes([0x10, 0xff, 0x00, 0x01, 0x30 + a]) + list_code_all_from(a + 1, n)


def build(log=print):
    if md5(LIVE) != LIVE_MD5:
        raise SystemExit('live %s md5 %s is not the pinned %s' % (LIVE, md5(LIVE), LIVE_MD5))
    if md5(PRE) != PRE_MD5:
        raise SystemExit('%s md5 %s is not the pinned %s' % (PRE, md5(PRE), PRE_MD5))
    zl, zp = zipfile.ZipFile(LIVE), zipfile.ZipFile(PRE)
    hl = kl_hvk.Hvk(zl.read(hvk_name(zl)))
    hp = kl_hvk.Hvk(zp.read(hvk_name(zp)))
    n0 = hl.static_count()
    if n0 % kl_hvk.CHUNK != 227 or len(hl.lists) != 8:
        raise ValueError('unexpected live layout: %d statics, %d lists' % (n0, len(hl.lists)))
    for r in SITES:   # the cut slots are fillers now, the shutter planes are gone
        if any(kl_hvk.ref(i) == r for s in hl.shapes for i in s.inst):
            raise ValueError('REF %d is still in the live file' % r)
    # the originals, from the pre-cut file
    src = {}
    for s in hp.shapes:
        if s.type != kl_hvk.STATIC:
            continue
        for i, m in zip(s.inst, s.mopp):
            if kl_hvk.ref(i) in SITES:
                if len(s.inst) != 1 or kl_hvk.ref(i) in src:
                    raise ValueError('REF %d: shape has %d placements' % (kl_hvk.ref(i), len(s.inst)))
                src[kl_hvk.ref(i)] = (s, i, m)
    if set(src) != set(SITES):
        raise ValueError('shutter planes found %s' % sorted(src))
    refs_live = {kl_hvk.ref(i) for s in hl.shapes for i in s.inst}
    for r, (dx, wall, lab) in SITES.items():
        if wall not in refs_live:
            raise ValueError('wall REF %d is not in the live file' % wall)
    fill = kl_escape.smallest_static(hl.shapes, {FILLER_REF: FILLER_REF})
    if not fill:
        raise ValueError('no filler REF %d' % FILLER_REF)
    pad = -n0 % kl_hvk.CHUNK
    out = kl_hvk.Hvk.__new__(kl_hvk.Hvk)
    out.box, out.tail = hl.box, hl.tail
    out.shapes = [s for s in hl.shapes]
    out.lists = list(hl.lists)
    if pad:
        out.shapes.append(fill[0].clone([fill[1]] * pad, [fill[2]] * pad))
    new_world = []
    for r in sorted(SITES):
        dx, wall, lab = SITES[r]
        s, i, m = src[r]
        i2, m2 = move(i, m, dx)
        i2 = i2[:0x30] + struct.pack('<I', wall) + i2[0x34:]
        out.shapes.append(s.clone([i2], [m2]))
        w = world_verts(s, i2)
        lo = [min(v[c] for v in w) for c in range(3)]
        hi = [max(v[c] for v in w) for c in range(3)]
        # invariant of re/havok.md: MOPP offset = world minimum - 0.01 (to 1e-3)
        off = struct.unpack('<3f', m2[0][:12])
        if max(abs(off[c] - (lo[c] - 0.01)) for c in range(3)) > 2e-3:
            raise ValueError('REF %d: offset %s vs world min %s' % (r, off, lo))
        new_world.append((r, lo, hi))
        log('  %s: REF %d plane -> x %.3f, y %.2f..%.2f, z %.2f..%.2f  (carries REF %d)' % (lab, r, lo[0], lo[1], hi[1], lo[2], hi[2], wall))
    # GUESS: header offset / scale of the new list code are never read (no cut op in it); the union box minus 0.01 and the
    # scale of the shutter's own code are plausible values of the same kind.
    off = [min(w[1][c] for w in new_world) - 0.01 for c in range(3)]
    scale = struct.unpack('<f', src[24710][2][0][12:])[0]
    out.lists.append((struct.pack('<4f', *off, scale), list_code_all(3)))
    data = out.serialize()
    again = kl_hvk.Hvk(data)
    if again.serialize() != data or again.static_count() != n0 + pad + 3 or len(again.lists) != 9:
        raise ValueError('round trip / counts')
    log('  statics %d -> %d (pad %d + 3), list codes 8 -> 9, .HVK %d -> %d bytes' % (n0, again.static_count(), pad, len(zl.read(hvk_name(zl))), len(data)))
    name = hvk_name(zl)
    members = [(n, data if n == name else zl.read(n)) for n in zl.namelist()]
    dst = os.path.join(OUT, 'stage', 'F02_Main.zip')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    kl_graft.write_zip(dst, members)
    return dst


# ---------------------------------------------------------------- self-check

def vm(code, lo=None, hi=None):
    """Tiny MOPP walk over the ops this tool writes (and the stock split ops): splits 0x10-0x12 [maxLeft][minRight][jump] with
    the query clamped to 0..255 (the query box is given in code units; None = whole range), cuts 0x26-0x28 [lo][hi], terms 0x30..0x4f.
    -> set of child ids. Raises on any other op (so it is never silently wrong)."""
    q = {0: (0, 255), 1: (0, 255), 2: (0, 255)} if lo is None else {a: (lo[a], hi[a]) for a in range(3)}
    res = set()

    def walk(pc, q):
        while True:
            op = code[pc]
            if 0x30 <= op <= 0x4f:
                res.add(op - 0x30)
                return
            if 0x10 <= op <= 0x12:
                a = op - 0x10
                ml, mr, jmp = code[pc + 1], code[pc + 2], code[pc + 3]
                if q[a][0] <= ml:
                    walk(pc + 4, q)
                if q[a][1] >= mr:
                    pc = pc + 4 + jmp
                    continue
                return
            if 0x26 <= op <= 0x28:
                a = op - 0x26
                if q[a][1] < code[pc + 1] or q[a][0] > code[pc + 2]:
                    return
                pc += 3
                continue
            raise ValueError('op %#x at %d not handled' % (op, pc))
    walk(0, q)
    return res


def seg_tri(p0, p1, a, b, c):
    """Moller-Trumbore on the segment p0->p1, two-sided; -> t in [0,1] or None."""
    d = [p1[k] - p0[k] for k in range(3)]
    e1 = [b[k] - a[k] for k in range(3)]
    e2 = [c[k] - a[k] for k in range(3)]

    def cr(u, v):
        return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]

    def dt(u, v):
        return sum(u[k] * v[k] for k in range(3))
    pv = cr(d, e2)
    det = dt(e1, pv)
    if abs(det) < 1e-12:
        return None
    inv = 1.0 / det
    tv = [p0[k] - a[k] for k in range(3)]
    u = dt(tv, pv) * inv
    if u < -1e-9 or u > 1 + 1e-9:
        return None
    qv = cr(tv, e1)
    v = dt(d, qv) * inv
    if v < -1e-9 or u + v > 1 + 1e-9:
        return None
    t = dt(e2, qv) * inv
    return t if -1e-9 <= t <= 1 + 1e-9 else None


def selfcheck(dst, log=print):
    bad = []
    zl, zn, zp = zipfile.ZipFile(LIVE), zipfile.ZipFile(dst), zipfile.ZipFile(PRE)
    name = hvk_name(zl)
    # 1. only the HVK member differs
    diff = [n for n in zl.namelist() if zl.read(n) != zn.read(n)]
    if diff != [name] or zl.namelist() != zn.namelist():
        bad.append('members differ: %s' % diff)
    hl, hn, hp = kl_hvk.Hvk(zl.read(name)), kl_hvk.Hvk(zn.read(name)), kl_hvk.Hvk(zp.read(hvk_name(zp)))
    # 2. everything that was there is unchanged
    old = hl.shapes
    if len(hn.shapes) != len(old) + 1 + 3 or hn.box != hl.box or hn.tail != hl.tail:
        bad.append('shape count / box / tail: %d vs %d' % (len(hn.shapes), len(old)))
    for k, s in enumerate(old):
        t = hn.shapes[k]
        if (s.type, s.flags, s.convex, s.verts, s.sub, s.inst, s.mopp) != (t.type, t.flags, t.convex, t.verts, t.sub, t.inst, t.mopp) \
                or (s.planes if s.convex else s.idx) != (t.planes if t.convex else t.idx):
            bad.append('old shape record %d changed' % k)
            break
    if hn.lists[:8] != hl.lists:
        bad.append('old list codes changed')
    log('check 1/2: only %s differs; %d old shape records, 8 old list codes byte-equal' % (name, len(old)))
    # 3. static order: chunk of every old REF unchanged
    def order(h):
        return [kl_hvk.ref(i) for s in h.shapes if s.type == 1 for i in s.inst]
    ol, on = order(hl), order(hn)
    if on[:len(ol)] != ol:
        bad.append('static order of old placements changed')
    padn = (-len(ol)) % 510
    if on[len(ol):len(ol) + padn] != [FILLER_REF] * padn or len(on) != len(ol) + padn + 3 or (len(ol) + padn) % 510:
        bad.append('pad / new chunk layout')
    chunk = (len(ol) + padn) // 510
    log('check 3: old statics %d keep their positions; %d fillers pad chunk %d; new chunk %d = statics %d..%d (REFs %s)' % (
        len(ol), padn, chunk - 1, chunk, len(ol) + padn, len(on) - 1, on[-3:]))
    # 4. the new chunk: list code -> children -> triangles -> ray hits
    code = hn.lists[chunk][1]
    kids = vm(code)
    if kids != {0, 1, 2}:
        bad.append('list code returns %s' % kids)
    # a query anywhere in a coarse range also returns all three (spot-check with boxes)
    for lo, hi in (((0, 0, 0), (0, 0, 0)), ((255, 255, 255), (255, 255, 255)), ((100, 20, 3), (101, 90, 4))):
        if vm(code, lo, hi) != {0, 1, 2}:
            bad.append('list code misses for %s' % (lo,))
    new_statics = [(s, i, m) for s in hn.shapes[-3:] for i, m in zip(s.inst, s.mopp)]
    pre_src = {}
    for s in hp.shapes:
        for i, m in zip(s.inst, s.mopp):
            if kl_hvk.ref(i) in SITES and s.type == 1:
                pre_src[kl_hvk.ref(i)] = (s, i, m)
    results = []
    for (s, i, m), r in zip(new_statics, sorted(SITES)):
        ps, pi, pm = pre_src[r]
        if m[1] != pm[1] or s.verts != ps.verts or s.idx != ps.idx or s.sub != ps.sub:
            bad.append('REF %d: code / shape differs from the original shutter' % r)
        w = world_verts(s, i)
        T = tris(s)
        px = STOP_X[r]
        wo = world_verts(ps, pi)
        # the original plane: same y/z, x moved by exactly dx
        if any(abs(a[1] - b[1]) > 1e-5 or abs(a[2] - b[2]) > 1e-5 or abs(a[0] - b[0] - SITES[r][0]) > 1e-4 for a, b in zip(w, wo)):
            bad.append('REF %d: plane is not the shutter shifted along x' % r)
        zlo, zhi = min(v[2] for v in w), max(v[2] for v in w)
        ylo, yhi = min(v[1] for v in w), max(v[1] for v in w)
        # rays: from inside the shop (towards the rear) along +-x, a grid over the opening
        sgn = 1 if px > 0 else -1
        hit = miss = 0
        xs = []
        for gy in range(1, 10):
            for gz in range(1, 10):
                y = ylo + (yhi - ylo) * gy / 10.0
                z = zlo + (zhi - zlo) * gz / 10.0
                p0, p1 = (px - sgn * 3.0, y, z), (px + sgn * 3.0, y, z)
                got = [seg_tri(p0, p1, w[a], w[b], w[c]) for a, b, c in T]
                got = [t for t in got if t is not None]
                if got:
                    hit += 1
                    xs.append(p0[0] + (p1[0] - p0[0]) * min(got))
                else:
                    miss += 1
        if miss or max(abs(x - px) for x in xs) > 1e-3:
            bad.append('REF %d: rays hit %d miss %d, x %s' % (r, hit, miss, xs[:3]))
        # the floor edge of the shop is at |x| = 30: the stop is inside it
        results.append('%s: plane x=%.3f y %.2f..%.2f z %.2f..%.2f; 81/81 rays from the shop side hit at x=%.3f' % (
            SITES[r][2], px, ylo, yhi, zlo, zhi, sum(xs) / len(xs)))
    for line in results:
        log('check 4: ' + line)
    # 5. the floor is untouched: the live floor placements are the same bytes (covered by 2) and none of their codes were edited
    floors = {23255: -30.0, 23239: 30.0, 23247: 30.0}
    for r, edge in floors.items():
        got = [(s, i) for s in hn.shapes for i in s.inst if kl_hvk.ref(i) == r]
        if len(got) != 1:
            bad.append('floor REF %d: %d placements' % (r, len(got)))
            continue
        w = world_verts(*got[0])
        ext = (min(v[0] for v in w), max(v[0] for v in w))
        log('check 5: floor REF %d x %.2f..%.2f (unchanged record); rear stop %.2f is inside' % (r, ext[0], ext[1], STOP_X[{23255: 24710, 23239: 24711, 23247: 24712}[r]]))
    return bad


INSTALL_NOTE = '2026-10-26 rear stops'


def write_install(dst, md5_new):
    import kl_loot_1025 as LO
    txt = LO.INSTALL_PY.replace('loot-placement', 'DM02 rear stops behind the shutters').replace('tools/kl_loot_1025.py', 'tools/kl_dm02_rearwall_1026.py').replace('2026-10-25', '2026-10-26')
    p = os.path.join(os.path.dirname(dst), 'install.py')
    with open(p, 'w', newline='\n') as fh:
        fh.write(txt % dict(map='DM02', zip='F02_Main.zip', tag=TAG, game=GAME, old=LIVE_MD5, new=md5_new))
    return p


def main():
    if sys.argv[1:] and sys.argv[1] != 'stage':
        print(__doc__)
        return 2
    dst = build()
    bad = selfcheck(dst)
    m = md5(dst)
    p = write_install(dst, m)
    print('staged %s md5 %s (%d bytes)\ninstall %s\nselfcheck problems: %d %s' % (dst, m, os.path.getsize(dst), p, len(bad), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
