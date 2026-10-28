"""Read-only audit of a level's .sgd point octrees against its scene: which leaves no longer sit where
their entity is. The game asks these trees "which explodables / shatter bodies are near this point"
(kl2 0x5e38c0 reads ExplodableOctree; see the kl_members docstring), so a stale leaf = a window or
canister that a nearby blast does not reach (or a far one does). Stock rule (MEASURED 2026-10-28 on
the nine Dog Days FA levels): every HavokShatterOctree leaf is on its entity's composed origin (worst
0.6 units); ExplodableOctree leaves of windows, lights and sirens sit 55..525 units from the origin
(GUESS: the explodable's own centre), so the threshold is per tree.

usage: python tools/kl_sgd_audit.py <level.zip | folder-of-members> [...]  [--shatter N] [--explode N]
  A folder of members holds <tag>__<slot>_Main.{gms,buf,sgd} sets (several tags). Defaults: shatter 50,
  explode 1000 units. Prints per map the leaves beyond the threshold (REF, distance, entity, top-level
  entity) and exits 1 when any map has one. Self-test: --selftest.
"""
import glob, math, os, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_members as MB

LIMIT = {'HavokShatterOctree': 50.0, 'ExplodableOctree': 1000.0}


def world_positions(gms, buf):
    """{REF: (world xyz, entity name, top-level name)} of a scene (kl_int16_range_check.mul composition)."""
    import kl_scene, kl_gms
    from kl_int16_range_check import mul
    sc = kl_scene.Scene(kl_gms.unpack(gms), buf)
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


def audit(gms, buf, sgd, limit=LIMIT):
    """[(tree, REF, distance or None, entity, top)] for every leaf beyond the tree's limit (distance
    None: the REF is not in the scene)."""
    W = world_positions(gms, buf)
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


def selftest():
    """A one-entity scene is not built here (kl_scene needs a .buf); check the geometry helpers."""
    t = MB.Octree()
    t.centre, t.scale = (20000.0, 100.0, 1000.0), 2.0
    q = tuple(int(round(0x8000 + (v - c) * t.scale)) for v, c in zip((20050.0, 120.0, 1100.0), t.centre))
    leaf = (7, q, tuple(v + 1 for v in q))
    assert t.world(leaf) == (1100.0, 120.0, 20050.0), t.world(leaf)
    m = t.translate((-12288.0, 0.0, -16384.0))
    assert m.world(leaf) == (1100.0 - 12288.0, 120.0, 20050.0 - 16384.0), m.world(leaf)
    print('selftest ok')


def main():
    a = sys.argv[1:]
    if '--selftest' in a:
        selftest(); return
    limit = dict(LIMIT)
    for flag, key in (('--shatter', 'HavokShatterOctree'), ('--explode', 'ExplodableOctree')):
        if flag in a:
            i = a.index(flag); limit[key] = float(a[i + 1]); del a[i:i + 2]
    worst = 0
    for arg in a:
        for label, gms, buf, sgd in sets(arg):
            bad = audit(gms, buf, sgd, limit)
            worst = max(worst, len(bad))
            print('%s: %d stale leaves' % (label, len(bad)))
            for name, ref, d, ename, top in sorted(bad, key=lambda b: -(b[2] or 1e9))[:12]:
                print('   %-18s REF %-6d %8s  %s  (%s)' % (name, ref, 'no REF' if d is None else '%.0f' % d, ename[:40], top[:30]))
    sys.exit(1 if worst else 0)


if __name__ == '__main__':
    main()
