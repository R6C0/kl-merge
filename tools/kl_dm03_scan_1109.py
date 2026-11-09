#!/usr/bin/env python3
r"""kl_dm03_scan_1109.py - READ-ONLY scanner for the DM03 (Withdrawal, slot F03) vault-door / loot-room design (re/dm03_vault_swat_1109.md). 2026-11-09.
Nothing is written but the report files named on the command line. Runs on any built F0x_Main.zip (the DM03 defaults are only names).

  python tools/kl_dm03_scan_1109.py <F03_Main.zip> [--out <report.json>] [--near <x,y,z>] [--radius 2500]
      dumps (stdout + JSON): every door-like leaf (ZSTDOBJ with a model whose name says door / dor / vault / gate / shutter; frames 'Wall_Door' /
      'Garage_Wall' too): node k, path, REF, model chunk, model box, world place and frame, extents, hidden / animated flags, whether
      kl_interact_graft.door_hosts takes it as a kick host (and its hinge), the walk mesh on both sides (polygon, part), its .HVK placements
      (type, world box in cm); PAIRS of leaves standing within PAIR_DIST of each other on one floor (double-door candidates, the owner's "two doors");
      the bank triggers / markers (ExitBank*, EnterBank*, Respawn*, MapIcon*, SpawnPoint*, Boarding*, ExitTrigger*: class, place); every loot object
      (kl_fa_bots.money_objects: node, name, place, amount, kind, container) and, per leaf, the loot within --radius; the escape van's wait / stop /
      board / end (kl_fa_bots.van_drives); the KL_* groups already grafted (KL_Interact!N doors with their hinges, KL_Garage!Back ...); census.
      --near x,y,z restricts the leaf / frame / trigger tables to --radius round that point (default: everything).
Built on kl_fa_bots.Built / Nav, kl_interact_graft.door_hosts, kl_hvk, kl_prmgraph the way kl_doors_1108 reads hosts. The pure helpers (classify,
pair_leaves, world_box, within) have an off-game self-test: tools/kl_dm03_scan_1109_test.py.
"""
import collections, json, math, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BS = chr(92)
PAIR_DIST = 400.0           # two leaves whose hinges / middles lie within this (plan) and DY in height are a double door candidate
PAIR_DY = 150.0
TRIGGER_RE = re.compile(r'exitbank|enterbank|respawn|mapicon|spawnpoint|boarding|exittrigger|escape|vault', re.I)
LEAF_RE = re.compile(r'door|dor\b|dor_|vault|gate|shutter', re.I)
FRAME_RE = re.compile(r'wall_door|garage_wall|door_4m|doorframe|frame', re.I)
GROUP_PREFIX = 'KL_'


def classify(name):
    """Last path element -> 'leaf' (a door-like object name), 'frame' (a wall piece with a door opening), or None."""
    last = name.rsplit(BS, 1)[-1]
    if FRAME_RE.search(last):
        return 'frame'
    if LEAF_RE.search(last):
        return 'leaf'
    return None


def within(p, c, r):
    """Plan distance of p from c at most r (None c = always)."""
    return c is None or math.hypot(p[0] - c[0], p[2] - c[2]) <= r


def pair_leaves(leaves, dist=PAIR_DIST, dy=PAIR_DY):
    """leaves = [dict(k, pos)] -> [(k1, k2, plan distance)] of every pair within dist on one floor, k1 < k2, nearest first."""
    out = []
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            d = math.hypot(a['pos'][0] - b['pos'][0], a['pos'][2] - b['pos'][2])
            if d <= dist and abs(a['pos'][1] - b['pos'][1]) <= dy:
                out.append((min(a['k'], b['k']), max(a['k'], b['k']), round(d)))
    return sorted(out, key=lambda t: (t[2], t[0]))


def world_box(inst, shape):
    """World bounding box in cm of a .HVK placement (pos * 100 + R * v over the shape's vertices; kl_dm07plane_1109.world_box)."""
    f = struct.unpack_from('<12f', inst)
    p, R = f[:3], [f[3:6], f[6:9], f[9:12]]
    lo, hi = [1e30] * 3, [-1e30] * 3
    n = len(shape.verts) // shape.vstride if shape.vstride else 0
    for j in range(n):
        v = struct.unpack_from('<3f', shape.verts, j * shape.vstride)
        for i in range(3):
            w = (p[i] + sum(R[i][t] * v[t] for t in range(3))) * 100.0
            lo[i], hi[i] = min(lo[i], w), max(hi[i], w)
    return [round(x) for x in lo], [round(x) for x in hi]


def hvk_by_ref(hvk):
    """{REF: [(type, shape index, placement index)]}."""
    d = collections.defaultdict(list)
    import kl_hvk
    for si, s in enumerate(hvk.shapes):
        for j, i in enumerate(s.inst):
            d[kl_hvk.ref(i)].append((s.type, si, j))
    return d


def scan(zp, near=None, radius=2500.0, log=print):
    import kl_fa_bots as F, kl_interact_graft as IG, kl_prmgraph as G, kl_hvk
    B = F.Built(zp)
    sc = B.sc
    nav = F.Nav(B.scene.nav)
    main = IG.main_part(nav)
    prm = G.read(B['.prm'], 'dd')
    hvk = kl_hvk.Hvk(B['.HVK'])
    byref = hvk_by_ref(hvk)
    hosts = {h['k']: h for h in IG.door_hosts(B, nav)}
    rep = collections.OrderedDict(zip=os.path.basename(zp), nodes=len(sc.nodes) - 1, main_part=main, near=near, radius=radius)
    leaves, frames = [], []
    for k, e in enumerate(B.ents, 1):
        kind = classify(sc.path[k])
        if kind is None or e.tid != 0x200002:
            continue
        R, P = B.fr[e]
        if not within(P, near, radius):
            continue
        row = collections.OrderedDict(k=k, path=sc.path[k][5:], ref=e.ref, model=e.model, pos=[round(v) for v in P],
                                      hidden=bool(e.flags & 0x400), animated=bool(e.raw), kids=len(e.kids), group=e.group, flags='%#x' % e.flags)
        c = prm.chunks[e.model] if e.model and e.model < len(prm.chunks) else b''
        if len(c) >= 0x38:
            bb = struct.unpack_from('<6f', c, 0x20)
            row['bb'] = [round(v) for v in bb]
            row['ext'] = [round(bb[3] - bb[0]), round(bb[4] - bb[1]), round(bb[5] - bb[2])]
            # the two sides along the thinnest horizontal axis, 120 out from the box middle, at the base height (door_hosts' rule)
            ext = row['ext']
            th = 0 if ext[0] <= ext[2] else 2
            mid_l = [(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2]
            mid = [P[i] + sum(R[i][j] * mid_l[j] for j in range(3)) for i in range(3)]
            n = [R[i][th] for i in range(3)]
            base = P[1] + sum(R[1][j] * [0.0, bb[1], 0.0][j] for j in range(3))
            sides = []
            for sg in (1.0, -1.0):
                x, z = mid[0] + sg * 120.0 * n[0], mid[2] + sg * 120.0 * n[2]
                a = nav.at(x, base, z, dy=150.0)
                sides.append(None if a is None else [a[0], nav.part[a[0]], nav.part[a[0]] == main])
            row['mid'] = [round(v) for v in mid]
            row['sides'] = sides
        if k in hosts:
            h = hosts[k]
            row['kick_host'] = dict(hinge=[round(v) for v in h['hinge']], width=round(h['width']), height=round(h['height']), thick=round(h['thick']))
        row['hvk'] = [[t, list(world_box(hvk.shapes[si].inst[j], hvk.shapes[si]))] for t, si, j in byref.get(e.ref, [])]
        (leaves if kind == 'leaf' else frames).append(row)
    rep['leaves'], rep['frames'] = leaves, frames
    rep['pairs'] = [dict(a=a, b=b, dist=d, names=[sc.path[a][5:].rsplit(BS, 1)[-1], sc.path[b][5:].rsplit(BS, 1)[-1]]) for a, b, d in pair_leaves(leaves)]
    trig = []
    for k in range(1, len(sc.nodes)):
        last = sc.path[k].rsplit(BS, 1)[-1]
        if TRIGGER_RE.search(last) and sc.cls(k) in ('ZBoxPrimitive', 'ZSpawnPoint', 'ZSTDOBJ', 'ZGROUP', 'ZLNKOBJ'):
            P = B.at(k)
            if within(P, near, radius):
                row = dict(k=k, path=sc.path[k][5:], cls=sc.cls(k), pos=[round(v) for v in P])
                if sc.cls(k) == 'ZBoxPrimitive':
                    row['half'] = [round(v) for v in B.box(k)]
                trig.append(row)
    rep['triggers'] = trig
    loot = []
    for o in F.money_objects(B):
        loot.append(dict(node=o['node'], name=sc.path[o['node']][5:], pos=[round(v) for v in o['at']], amount=o['amount'], kind=o['kind'], type=o['type'],
                         container=o['container'], radius=o['radius']))
    rep['loot'] = loot
    rep['loot_total'] = sum(o['amount'] for o in loot)
    for row in leaves:
        row['loot_near'] = [o['node'] for o in loot if math.hypot(o['pos'][0] - row['pos'][0], o['pos'][2] - row['pos'][2]) <= radius and abs(o['pos'][1] - row['pos'][1]) <= 400]
    try:
        rep['vans'] = [dict(name=d['name'], wait=[round(v) for v in d['wait']], stop=[round(v) for v in d['stop']], board=[round(v) for v in d['board']],
                            end=[round(v) for v in d['end']], seconds=d['seconds']) for d in F.van_drives(B)]
    except Exception as ex:          # a van that cannot be read is reported, not fatal
        rep['vans'] = 'unreadable: %s' % ex
    groups = collections.OrderedDict()
    for k in range(1, len(sc.nodes)):
        p = sc.path[k][5:]
        if p.startswith(GROUP_PREFIX) and sc.parent[k] == 0:
            groups[p] = dict(k=k, kids=sc.end[k] - k - 1)
        if p.startswith('KL_Interact!') and sc.names[k].startswith('KL_Door_') and sc.parent[sc.parent[k]] == 0:
            groups[p] = dict(k=k, hinge=[round(v) for v in B.at(k)])
    rep['kl_groups'] = groups
    try:
        import kl_dm02_assault_1025 as AS
        rep['census'] = list(AS.census(sc))
    except Exception as ex:
        rep['census'] = 'n/a: %s' % ex
    # ---- text
    log('%s: %d nodes, main part %d, %d door-like leaves, %d frames, %d pairs, %d triggers, %d loot objects (%d), van %s' % (
        rep['zip'], rep['nodes'], main, len(leaves), len(frames), len(rep['pairs']), len(trig), len(loot), rep['loot_total'],
        rep['vans'] if isinstance(rep['vans'], str) else ['%s stop %s' % (v['name'][-30:], v['stop']) for v in rep['vans']]))
    for row in leaves:
        log('  leaf %5d ref %6d model %6d %-44s at %s ext %s hidden %s anim %s host %s sides %s hvk %s loot %s' % (
            row['k'], row['ref'], row['model'], row['path'][-44:], row['pos'], row.get('ext'), int(row['hidden']), int(row['animated']),
            row['kick_host']['hinge'] if 'kick_host' in row else '-', row.get('sides'), [(t, b[0], b[1]) for t, b in row['hvk']][:2], row['loot_near'][:6]))
    for pr in rep['pairs']:
        log('  PAIR %d + %d (%d cm): %s' % (pr['a'], pr['b'], pr['dist'], ' | '.join(pr['names'])))
    for row in frames:
        log('  frame %5d ref %6d %-44s at %s ext %s hvk %d' % (row['k'], row['ref'], row['path'][-44:], row['pos'], row.get('ext'), len(row['hvk'])))
    for row in trig:
        log('  trig %5d %-16s %-50s at %s %s' % (row['k'], row['cls'], row['path'][-50:], row['pos'], row.get('half', '')))
    for o in loot:
        log('  loot %5d %-50s at %s %8d %s' % (o['node'], o['name'][-50:], o['pos'], o['amount'], o['kind']))
    for p, g in groups.items():
        log('  group %-40s %s' % (p, g))
    log('  census %s' % (rep['census'],))
    return rep


def main(a):
    if not a or a[0].startswith('-'):
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    near = tuple(float(x) for x in opt('--near').split(',')) if '--near' in a else None
    rep = scan(a[0], near, float(opt('--radius', 2500.0)))
    out = opt('--out')
    if out:
        json.dump(rep, open(out, 'w'), indent=1, default=str)
        print('written %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
