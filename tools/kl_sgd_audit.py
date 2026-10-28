"""Audit (and repair) a level's .sgd point octrees against its scene: which leaves no longer sit
where their entity is. The game asks these trees "which explodables / shatter bodies are near this
point" (kl2 0x5e38c0 reads ExplodableOctree; see the kl_members docstring), so a stale leaf = a
window or canister that a nearby blast does not reach (or a far one does). Stock rule (MEASURED
2026-10-28 on the nine Dog Days FA levels): every HavokShatterOctree leaf is on its entity's
composed origin (worst 0.6 units); ExplodableOctree leaves of windows, lights and sirens sit
55..525 units from the origin (GUESS: the explodable's own centre), so the threshold is per tree.
Leaves under an `Animation/` top-level subtree are reported apart and never repaired: stock F03,
F06 and F07 keep their animated police cars' leaves 1.6k..14k from the rest position.

FOUND 2026-10-28 (second check-in): the 83 stale DM03A vault leaves are stale in Dead Men's own
M03A_Main.sgd (same REFs and distances; x and z swapped, while the .HVK placement agrees with the
.gms), so the source data is wrong, not the graft; the EscapeChopper ShatterGeom of DM11B / DM05A
is ours (the authoring moved the chopper). kl_graft now calls `refresh` on the joined .sgd.

usage: python tools/kl_sgd_audit.py <level.zip | folder-of-members> [...]  [--shatter N] [--explode N]
       python tools/kl_sgd_audit.py <level.zip> --fix <out.zip>      (never in place)
  A folder of members holds <tag>__<slot>_Main.{gms,buf,sgd} sets (several tags). Defaults: shatter 50,
  explode 2000 units. Prints per map the leaves beyond the threshold (REF, distance, entity, top-level
  entity) and exits 1 when any map has one outside Animation/. --fix writes a copy of the one zip
  with the leaves beyond the REPAIR limit (2000 units on both trees, kl_members.STALE; --shatter/--explode
  override it) put back on their entity (kl_members.sgd_refresh). Self-test: --selftest.
"""
import glob, math, os, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_members as MB

LIMIT = {'HavokShatterOctree': 50.0, 'ExplodableOctree': 2000.0}   # REPORT limits (stock F01..F09 pass; explodable
# 'Lights_Back_Off' of F06's police cars sit 1169 off); the REPAIR limit is kl_members.STALE (2000 on both trees): the
# shipped levels keep smaller offsets by convention (DM03FAA panes 85, helicopters 245, M06A While_window 127..726)
ANIM = 'Animation/'


def world_positions(gms, buf, packed=True):
    """{REF: (world xyz, entity name, top-level name)} of a scene (kl_int16_range_check.mul
    composition). gms: the packed member, or the unpacked image with packed=False."""
    import kl_scene, kl_gms
    from kl_int16_range_check import mul
    sc = kl_scene.Scene(kl_gms.unpack(gms) if packed else gms, buf)
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))
    out = {}

    def go(e, par, top):
        rot = struct.unpack('<12f', e.rot)[:12]; tr = struct.unpack('<4f', e.trans)[:3]
        w = mul(par, (tuple(rot), tuple(tr)))
        out[e.ref] = (w[1], e.name.decode('latin1'), top)
        for k in e.kids:
            go(k, w, top)
    for r in sc.roots:
        go(r, ident, r.name.decode('latin1'))
    return out


def audit(gms, buf, sgd, limit=LIMIT, packed=True):
    """[(tree, REF, distance or None, entity, top)] for every leaf beyond the tree's limit (distance
    None: the REF is not in the scene). Leaves under Animation/ are included; `stale` splits them."""
    W = world_positions(gms, buf, packed)
    bad = []
    for name, payload in MB.sgd_read(sgd):
        if 'Octree' not in name:
            continue
        t = MB.Octree(payload)
        for leaf in t.leaves:
            if leaf[0] not in W:
                bad.append((name, leaf[0], None, '?', '?'))
                continue
            p, ename, top = W[leaf[0]]
            d = math.dist(t.world(leaf), p)
            if d > limit.get(name, 0):
                bad.append((name, leaf[0], d, ename, top))
    return bad


def stale(bad):
    """audit() rows -> (the ones to fix, the Animation/ ones that are expected)."""
    return [b for b in bad if not b[4].startswith(ANIM)], [b for b in bad if b[4].startswith(ANIM)]


def refresh(gms, buf, sgd, limit=MB.STALE, packed=True):
    """(new .sgd bytes, [(tree, REF, old distance)]): leaves beyond the REPAIR limit and outside
    Animation/ put back on their entity (kl_members.sgd_refresh). gms as for world_positions."""
    W = world_positions(gms, buf, packed)
    return MB.sgd_refresh(sgd, {r: v[0] for r, v in W.items()}, limit, skip=lambda r: W[r][2].startswith(ANIM))


def sets(arg):
    """[(label, gms, buf, sgd)] from a level zip or a folder of <tag>__<slot>_Main.* members."""
    if os.path.isdir(arg):
        out = []
        for g in sorted(glob.glob(os.path.join(glob.escape(arg), '*.gms'))):
            stem = g[:-4]
            if os.path.isfile(stem + '.buf') and os.path.isfile(stem + '.sgd'):
                out.append((os.path.basename(stem), open(g, 'rb').read(), open(stem + '.buf', 'rb').read(), open(stem + '.sgd', 'rb').read()))
        return out
    with zipfile.ZipFile(arg) as zf:
        mem = {os.path.splitext(n)[1].lower(): n for n in zf.namelist()}
        return [(os.path.basename(arg), zf.read(mem['.gms']), zf.read(mem['.buf']), zf.read(mem['.sgd']))]


def fix_zip(src, dst, limit=MB.STALE):
    """dst = src with its .sgd member refreshed (every other member copied byte for byte, same
    compression and stamps). Refuses dst == src. Returns the moved list."""
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('--fix writes a copy: give another path')
    with zipfile.ZipFile(src) as zi:
        mem = {os.path.splitext(n)[1].lower(): n for n in zi.namelist()}
        new, moved = refresh(zi.read(mem['.gms']), zi.read(mem['.buf']), zi.read(mem['.sgd']), limit)
        with zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
            for info in zi.infolist():
                i2 = zipfile.ZipInfo(info.filename, info.date_time)
                i2.compress_type, i2.external_attr, i2.create_system = info.compress_type, info.external_attr, info.create_system
                data = new if info.filename == mem['.sgd'] else zi.read(info)
                zo.writestr(i2, data, compress_type=info.compress_type)
    return moved


def selftest():
    """Geometry helpers, the stock frame rule and sgd_refresh on hand-made trees (a one-entity
    scene is not built here: kl_scene needs a .buf)."""
    t = MB.Octree()
    t.centre, t.scale = (20000.0, 100.0, 1000.0), 2.0
    q = tuple(int(round(0x8000 + (v - c) * t.scale)) for v, c in zip((20050.0, 120.0, 1100.0), t.centre))
    leaf = (7, q, tuple(v + 1 for v in q))
    assert t.world(leaf) == (1100.0, 120.0, 20050.0), t.world(leaf)
    m = t.translate((-12288.0, 0.0, -16384.0))
    assert m.world(leaf) == (1100.0 - 12288.0, 120.0, 20050.0 - 16384.0), m.world(leaf)
    # stock frame: min corner, 32000 / largest span
    pts = [(1, (10.0, 0.0, -5.0)), (2, (110.0, 50.0, 95.0)), (3, (60.0, 20.0, 20.0))]
    b = MB.Octree.build(pts)
    assert b.centre == (10.0, 0.0, -5.0) and abs(b.scale - 320.0) < 1e-3, (b.centre, b.scale)
    assert b.leaves[0][1] == (0x8000, 0x8000, 0x8000) and b.leaves[1][1] == (0xfd00, 0x8000 + 16000, 0xfd00), b.leaves
    assert b.serialize() and sorted(MB.Octree(b.serialize()).leaves) == sorted(b.leaves)   # the file order is the tree walk's
    # replace inside the frame: only that leaf changes; outside: rebuilt, the others keep their points
    r = b.replace({3: (60.0, 20.0, 40.0)})
    assert r.leaves[0] == b.leaves[0] and r.leaves[1] == b.leaves[1] and r.position(r.leaves[2]) == (60.0, 20.0, 40.0), r.leaves
    r = b.replace({3: (500.0, 20.0, 40.0)})
    assert r.centre == b.centre and r.leaves[2][1][0] == 0xfd00 and r.position(r.leaves[0]) == (10.0, 0.0, -5.0), (r.centre, r.leaves)
    # sgd_refresh: world is (x, y, z), stored order (z, y, x); REF 2 is 3000 units off -> moved (frame rebuilt); REF 1 stays
    data = MB.sgd_write([('HavokShatterOctree', b.serialize()), ('SecurityZones', b'\0' * 0x40)])
    world = {1: (-5.0, 0.0, 10.0), 2: (95.0, 50.0, 3110.0), 3: (20.0, 20.0, 60.0)}
    new, moved = MB.sgd_refresh(data, world)
    assert [(n, r) for n, r, _ in moved] == [('HavokShatterOctree', 2)] and abs(moved[0][2] - 3000.0) < 1e-6, moved
    secs = dict(MB.sgd_read(new))
    t2 = MB.Octree(secs['HavokShatterOctree'])
    got = {l[0]: t2.world(l) for l in t2.leaves}
    assert set(got) == set(world) and all(math.dist(got[r], world[r]) < 0.1 for r in world), got   # rebuilt frame: one quantum
    assert secs['SecurityZones'] == b'\0' * 0x40
    assert MB.sgd_refresh(data, world, skip=lambda r: r == 2) == (data, [])
    assert MB.sgd_refresh(data, {1: world[1]}) == (data, [])
    assert MB.sgd_refresh(data, {2: (95.0, 50.0, 410.0)}) == (data, [])          # 300 off: below the repair limit, kept
    print('selftest ok')


def main():
    a = sys.argv[1:]
    if '--selftest' in a:
        selftest(); return
    over = {}
    for flag, key in (('--shatter', 'HavokShatterOctree'), ('--explode', 'ExplodableOctree')):
        if flag in a:
            i = a.index(flag); over[key] = float(a[i + 1]); del a[i:i + 2]
    if '--fix' in a:
        i = a.index('--fix'); dst = a[i + 1]; del a[i:i + 2]
        if len(a) != 1 or os.path.isdir(a[0]):
            sys.exit('--fix takes exactly one level zip')
        moved = fix_zip(a[0], dst, dict(MB.STALE, **over))
        print('%s -> %s: %d leaves put back on their entity' % (a[0], dst, len(moved)))
        for name, ref, d in sorted(moved, key=lambda m: -m[2])[:12]:
            print('   %-18s REF %-6d was %8.0f off' % (name, ref, d))
        return
    worst = 0
    for arg in a:
        for label, gms, buf, sgd in sets(arg):
            bad, anim = stale(audit(gms, buf, sgd, dict(LIMIT, **over)))
            worst = max(worst, len(bad))
            print('%s: %d stale leaves%s' % (label, len(bad), ' (+%d under %s, expected)' % (len(anim), ANIM) if anim else ''))
            for name, ref, d, ename, top in sorted(bad, key=lambda b: -(b[2] or 1e9))[:12]:
                print('   %-18s REF %-6d %8s  %s  (%s)' % (name, ref, 'no REF' if d is None else '%.0f' % d, ename[:40], top[:30]))
    sys.exit(1 if worst else 0)


if __name__ == '__main__':
    main()
