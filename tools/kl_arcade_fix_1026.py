"""kl_arcade_fix_1026.py - bring DM03A / DM05A / DM11B / DM09 closer to the stock Arcade standard (2026-10-26, OFFLINE: reads zips, writes only under <root>/<MAP>/stage).

Per map: <root>/<MAP>/in/<zip> (+ the files beside it) -> <root>/<MAP>/stage/{<zip>, install.py, build_report.json}.
Member-level patch of the live zip: only .prp / .gms (and .buf when its bytes differ) are replaced; .prm, .oct, .HVK ... stay byte-identical (asserted).
Every edit keeps the entity count: controllers are added / a ZGEOM is moved, no entity is created or deleted (no slot renumbering).
TOGGLE: map content; the switch is install.py / install.py --undo (backup '<zip>.before-1026arcade').

Pieces
  cover(B, stacks)     an all-AUTO PlayerCoverModifier (cloned from stock F01, key tokens remapped) on the existing *CoverBox* ZSTDOBJ nodes within
                       COVER_R of each loot stack (the audit counts PlayerCoverModifier / CoverStateChanger / RunToCoverPosInfoRout near a stack).
                       All fields AUTO = the engine's default, so it is behaviour-neutral: the cover list is built from the NAME, the controller only overrides sides.
  relocate(B, groups)  soldier groups of a squad moved (group ZGEOM + .gms record) to a spot; the squad script / Defend boxes keep their world targets.
  see the per-map SPEC at the bottom.
usage (from tools/):  python kl_arcade_fix_1026.py stage <root> [MAP ...] [--rehearse <scratch>]
"""
import collections, json, math, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft
import kl_fa_bots as KB
import kl_loot_1025 as LO
import kl_prpjoin as J

TAG = '.before-1026arcade'
GAME = LO.GAME
md5, patch_zip = LO.md5, LO.patch_zip
COVER_R = 1200.0          # GUESS: cover boxes within 12 m (3-D) of a stack get the controller (audit window is 15 m)
COVER_MAX = 4             # per stack


def donor_pcm():
    """(name token, body tokens, source scene) of an all-AUTO PlayerCoverModifier on a ZSTDOBJ of stock F01."""
    sc = J.Scene.load('F01')
    for k, i, v in kl_fa.controllers(sc, 'PlayerCoverModifier'):
        if sc.cls(k) == 'ZSTDOBJ' and all(x == 'AUTO' for x in v if isinstance(x, str)) and len(sc.nodes[k]['ctrls']) == 1:
            nm, body = sc.nodes[k]['ctrls'][i]
            return nm, body, sc
    raise ValueError('no all-AUTO PlayerCoverModifier in F01')


def remap(tok, src, dst):
    op, pl = tok
    if op in (0x0c, 0x0e):
        return (op, struct.pack('<I', dst.p.key_index(src.p.keys[struct.unpack('<I', pl)[0]])))
    if op == 0x0f:      # GUESS: same layout as 0x0c/0x0e (a key index); the donor has none
        raise ValueError('donor holds a 0x0f token')
    return tok


def cover_nodes(B):
    sc = B.sc
    return [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSTDOBJ' and 'coverbox' in sc.names[k].lower()]


def cover(B, stacks, log=print):
    """-> [(box node, stack node, distance)] of the controllers added. Boxes that have a PlayerCoverModifier already are skipped."""
    sc = B.sc
    nm, body, src = donor_pcm()
    name = remap(nm, src, sc)
    toks = [remap(t, src, sc) for t in body]
    boxes = cover_nodes(B)
    have = {k for k, i, v in kl_fa.controllers(sc, 'PlayerCoverModifier')}
    done, taken = [], set()
    for s in stacks:
        p = B.at(s)
        near = sorted((math.dist(p, B.at(k)), k) for k in boxes if k not in have)
        near = [x for x in near if x[0] <= COVER_R][:COVER_MAX]
        for d, k in near:
            if k not in taken:
                sc.nodes[k]['ctrls'].append((name, list(toks)))
                taken.add(k)
            done.append((k, s, round(d / 100.0, 1)))
    log('  cover: %d PlayerCoverModifier added (%d box-stack pairs) for %d stacks' % (len(taken), len(done), len(stacks)))
    return done


# ------------------------------------------------------------------ soldiers away from START
def starts(B):
    sc = B.sc
    return [B.at(k) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and any(x == kl_fa.START for x in kl_fa.node_values(sc, k))]


def nav_start(B, nav):
    for sp in starts(B):
        for dy in (260., 600., 1500.):
            h = nav.at(sp[0], sp[1], sp[2], dy=dy)
            if h:
                return h[0], sp
    raise ValueError('no START on the nav mesh')


def squad_soldiers(B, q):
    """Soldier groups of squad group node q: its ZGROUP children that hold a ZFFActor (the squad logic groups hold none)."""
    sc = B.sc
    return [j for j in range(q + 1, sc.end[q]) if sc.parent[j] == q and sc.cls(j) == 'ZGROUP'
            and any(sc.cls(x) == 'ZFFActor' for x in range(j, sc.end[j]))]


def set_world(B, g, pos):
    """Group g -> world pos: its LOCAL place (the parent's frame, from the .gms chain B.fr) goes into ZGEOM[2] and the .gms record.
    GUESS: the .gms chain is the authority for the world (a few static squad groups keep a stale ZGEOM[2] = 0 in the .prp while the .gms
    holds their pose; their children's world places agree with the vault only under the .gms chain)."""
    sc, e = B.sc, B.ents[g - 1]
    loc = [float(x) for x in B.local(sc.parent[g], pos)]
    lab = J.labels('dd', sc.cls(g))
    i = lab.index('ZGEOM[2]')
    LO.kl_graft.edit(sc.nodes[g], 'props', lambda us: LO.AU.setv(sc, us, i, loc))
    e.trans = struct.pack('<3f', *loc) + e.trans[12:]


def relocate(B, squads, stacks, near_min=4500.0, walk_min=4500.0, reach_max=11000.0, log=print):
    """Soldier groups of the squad nodes `squads` -> nav spots at least near_min straight (every START) and walk_min on foot from START,
    nearest to where each stood (so the squad keeps its part of the map), never within 15 m of a loot stack, 3 m apart.
    The squad's own group, Defend boxes and routs are NOT touched (they hold world targets). -> [(group, old, new, walk m, straight m)]"""
    sc = B.sc
    nav = KB.Nav(B.scene.nav)
    i0, p0 = nav_start(B, nav)
    dm = nav.dist_map(i0, p0)[0]
    ss = starts(B)
    loot = [B.at(s) for s in stacks]
    cands = []
    for i, d in dm.items():
        if not nav.ok[i] or d < walk_min:
            continue
        m = nav.mid[i]
        straight = min(math.hypot(m[0] - s[0], m[2] - s[2]) for s in ss)
        if straight < near_min or straight > reach_max or any(math.hypot(m[0] - l[0], m[2] - l[2]) < 1500.0 for l in loot):
            continue
        cands.append((m[0], m[1], m[2], i))
    if not cands:
        raise ValueError('no candidate spots')
    skipped = []
    every = [j for q in squads for g in squad_soldiers(B, q) if g not in skipped for j in range(g, sc.end[g])]
    stuck = LO.listed_in_oct(B, every)
    if stuck:
        raise ValueError('soldier nodes %s are listed in an .oct room tree' % stuck)
    out, taken = [], []
    for q in squads:
        for g in squad_soldiers(B, q):
            if g in skipped:
                continue
            old = B.at(g)
            free = [c for c in cands if all(math.hypot(c[0] - t[0], c[2] - t[2]) >= 300.0 for t in taken)]
            # GUESS: the squad keeps its logic (Defend boxes are world targets), so the soldier only has to start far: the NEAREST spot (on foot) that is far enough
            free.sort(key=lambda c: (dm[c[3]], abs(c[1] - old[1])))
            got = [c for c in free if nav.clearance(c[0], c[1], c[2]) >= 60.0][:1] or free[:1]
            if not got:
                raise ValueError('no spot for %s' % sc.path[g])
            c = got[0]
            new = (c[0], c[1], c[2])
            set_world(B, g, new)
            taken.append(new)
            out.append((g, [round(v, 1) for v in old], [round(v, 1) for v in new], round(dm[c[3]] / 100.0, 1),
                        round(min(math.hypot(c[0] - s[0], c[2] - s[2]) for s in ss) / 100.0, 1)))
    log('  relocate: %d soldier groups of %d squads moved (walk %.0f..%.0f m from START)' % (len(out), len(squads), min(o[3] for o in out), max(o[3] for o in out)))
    return out, skipped


# ------------------------------------------------------------------ a KillBox under the map (DM11B)
KILL_GAP = 1500.0         # top of the box this far under the lowest walkable polygon (audit: 'nav min y minus 15 m')
KILL_HALF_Y = 1000.0
KILL_MARGIN = 3000.0


def donor_kill():
    """(name token, body tokens, source scene) of the KillBox controller of stock F08 (its only one: a big box under the level)."""
    sc = J.Scene.load('F08')
    ks = kl_fa.controllers(sc, 'KillBox')
    if len(ks) != 1:
        raise ValueError('F08 has %d KillBox controllers' % len(ks))
    k, i, _v = ks[0]
    nm, body = sc.nodes[k]['ctrls'][i]
    return nm, body, sc


def killbox(B, log=print):
    """A KillBox spanning the nav mesh, TOP_GAP under its lowest polygon. NO entity is added (that would renumber every slot id): an inert leftover
    box of the map is used - a top-level ZBoxPrimitive named '*NoCover*' with no controller that nothing names and no .oct room tree lists (the
    NoCoverBox controllers of those 34 boxes were stripped by the cover pass). It is moved, resized, turned to the identity and given the F08 KillBox
    controller (CheckInsideEnter, FA_DieFromSelf). GUESS: ZSTDOBJ[1] (1 on the leftover, 0 on every stock KillBox) is set to the stock value."""
    sc = B.sc
    if kl_fa.controllers(sc, 'KillBox'):
        log('  killbox: the map has one already, nothing added')
        return None
    nav = KB.Nav(B.scene.nav)
    xs = [v[0] for vs in nav.pv for v in vs]
    zs = [v[2] for vs in nav.pv for v in vs]
    ys = [m[1] for i, m in enumerate(nav.mid) if nav.ok[i]]
    ymin = min(ys)
    named = set()
    for _kk, _h, _f, _s, g in KB.J.references(sc):
        named.update(g or ())
    cands = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZBoxPrimitive' and sc.parent[k] == 0 and not sc.nodes[k]['ctrls']
             and k not in named and 'nocover' in sc.path[k].lower()]
    cands = [k for k in cands if sc.end[k] == k + 1 and k not in LO.listed_in_oct(B, [k])]
    if not cands:
        raise ValueError('no inert box to use as the KillBox')
    k = cands[0]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    half = ((max(xs) - min(xs)) / 2 + KILL_MARGIN, KILL_HALF_Y, (max(zs) - min(zs)) / 2 + KILL_MARGIN)
    pos = (cx, ymin - KILL_GAP - KILL_HALF_Y, cz)
    lab = J.labels('dd', sc.cls(k))
    ident = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

    def fn(us):
        LO.AU.setv(sc, us, lab.index('ZGEOM[1]'), ident)
        LO.AU.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
        for i, v in enumerate(half):
            LO.AU.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
        LO.AU.setv(sc, us, lab.index('ZSTDOBJ[1]'), 0)
    LO.kl_graft.edit(sc.nodes[k], 'props', fn)
    e = B.ents[k - 1]
    e.rot = struct.pack('<9f', *ident) + bytes(12)
    e.trans = struct.pack('<3f', *[float(x) for x in pos]) + bytes(4)
    nm, body, src = donor_kill()
    sc.nodes[k]['ctrls'].append((remap(nm, src, sc), [remap(t, src, sc) for t in body]))
    log('  killbox: node %d (%s) -> centre (%.0f, %.0f, %.0f), half (%.0f, %.0f, %.0f); nav y min %.0f, box top %.0f' % (
        k, sc.names[k], *pos, *half, ymin, pos[1] + KILL_HALF_Y))
    return dict(node=k, name=sc.names[k], centre=[round(v, 1) for v in pos], half=[round(v, 1) for v in half], nav_ymin=round(ymin, 1), top=round(pos[1] + KILL_HALF_Y, 1),
                spare_boxes=len(cands) - 1)


# ------------------------------------------------------------------ boarding cameras of the parked vans (DM09)
def cameras(B, log=print):
    """Retomoto's vans 02 and 03 are parked under the map on purpose (kl_fa_street.place_escape, re/open_work_log 2026-10-11: their FakeTargets crashed the
    vision grid), so the 'eye under the map' faults of their CamPos01 are by design and the cameras never fire. The eye node of each parked van's camera
    is nevertheless put on van 01's, which stands on the road (365 over the street at the exit), so no camera of the map can show the void.
    GUESS: the engine reads the eye from the node's own place (eFMM_LookFromPos, field 9 - the audit's reading of kl2.exe 0x447240)."""
    import kl_map_escape as E
    sc = B.sc
    eyes = {}
    for k in range(1, len(sc.nodes)):
        if sc.names[k] == 'CamPos01' and sc.cls(k) in ('ZSTDOBJ', 'ZBoxPrimitive', 'ZGROUP'):
            top = sc.path[k].split(chr(92))[1]
            eyes[top] = k
    tops = sorted(eyes)
    if len(tops) < 2:
        raise ValueError('expected 3 CamPos01, found %s' % tops)
    ref = eyes[tops[0]]
    target = B.at(ref)
    if target[1] < 0:
        raise ValueError('the reference eye %s is under the ground' % sc.path[ref])
    done = []
    for t in tops[1:]:
        k = eyes[t]
        old = B.at(k)
        if old[1] > -1000.0:
            continue
        if LO.listed_in_oct(B, [k]):
            raise ValueError('eye node %d is listed in an .oct room tree' % k)
        set_world(B, k, target)
        done.append(dict(node=k, name=sc.path[k][-60:], old=[round(v, 1) for v in old], new=[round(v, 1) for v in target]))
    log('  cameras: %d parked-van eye nodes put on the eye of van 01: %s' % (len(done), [round(v) for v in target]))
    return done


# ------------------------------------------------------------------ one map
MAPS = collections.OrderedDict([
    ('DM03A', dict(slot='F07', zip='F07_Main.zip', pin='1acb434a82d64ca6fd32acf91ecd1c94')),
    ('DM05A', dict(slot='F01', zip='F01_Main.zip', pin='9cdd6dee29f9a0a349589bf842b6e995')),
    ('DM11B', dict(slot='F04', zip='F04_Main.zip', pin='e6ab53474cc0423b6dc24298b6b203dc')),
    ('DM09', dict(slot='F06', zip='F06_Main.zip', pin='5c31e9017f60d24c8a4ea7df4805df36'))])

# DM05A: the owner's staged loot moves (C:/kl_build_1024/owner1025_build/DM05A/stage, 2026-10-25), re-applied here on the live zip.
DM05A_MOVES = collections.OrderedDict([(18903, (3050.0, 340.0, 2490.0)), (18904, (2950.0, 340.0, 2520.0)), (18806, (290.0, 127.0, -1150.0))])

SPEC = collections.OrderedDict([
    ('DM03A', dict(relocate=True, cover=True)),
    ('DM05A', dict(relocate=True, cover=True, moves=DM05A_MOVES)),
    ('DM11B', dict(cover=True, killbox=True)),
    ('DM09', dict(cover=True, cameras=True))])


def squads_near_start(src, B):
    import kl_map_ai as M
    byname = {B.sc.path[k]: k for k in range(1, len(B.sc.nodes))}
    return [byname['ROOT' + chr(92) + q['name']] for q in M.measure(src)['squads'] if q['far'] is not None and q['far'] < 30 and q['people']]


def build(name, src, dst, log=print):
    m, sp = MAPS[name], SPEC[name]
    B = KB.Built(src, m['slot'])
    sc = B.sc
    stacks = [o['node'] for o in KB.money_objects(B)]
    total0 = sum(o['amount'] for o in KB.money_objects(B))
    rep = collections.OrderedDict()
    for k, p in (sp.get('moves') or {}).items():
        if LO.listed_in_oct(B, [k]):
            raise ValueError('loot node %d is listed in an .oct room tree' % k)
        LO.move(B, k, p)
    rep['loot_moved'] = [[k, [round(v, 2) for v in p]] for k, p in (sp.get('moves') or {}).items()]
    if sp.get('relocate'):
        sq = squads_near_start(src, B)
        out, skipped = relocate(B, sq, stacks, log=log)
        rep['relocated'] = out
        rep['relocate_skipped'] = skipped
    if sp.get('cover'):
        rep['cover'] = cover(B, stacks, log)
    if sp.get('killbox'):
        rep['killbox'] = killbox(B, log)
    if sp.get('cameras'):
        rep['cameras'] = cameras(B, log)
    prp = sc.p.serialize()
    gms, buf = B.scene.write()
    new = {B.ext['.prp']: prp, B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf}
    repl = {n: b for n, b in new.items() if b != B.files[n]}
    patch_zip(src, dst, repl)
    A = KB.Built(dst, m['slot'])
    bad = []
    for n in A.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if A.files[B.ext['.prm']] != B.files[B.ext['.prm']]:
        bad.append('.prm changed')
    if len(A.sc.names) != len(sc.names) or A.sc.names != sc.names:
        bad.append('node list changed')
    after = {o['node']: o['amount'] for o in KB.money_objects(A)}
    if set(after) != set(stacks) or sum(after.values()) != total0:
        bad.append('loot set / values changed')
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep['members_changed'] = sorted(repl)
    rep['loot_total'] = total0
    return rep


def stage_map(root, name, scratch=None, log=print):
    m = MAPS[name]
    d = os.path.join(root, name)
    src = os.path.join(d, 'in', m['zip'])
    h = md5(src)
    if h != m['pin']:
        raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, m['pin']))
    out = os.path.join(d, 'stage')
    LO.rmtree(out)
    os.makedirs(out)
    log('== %s (%s) ==' % (name, m['zip']))
    final = os.path.join(out, m['zip'])
    rep = build(name, src, final, log)
    rep.update(md5_in=h, md5_out=md5(final))
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(final) as b:
        assert a.namelist() == b.namelist()
        diff = sorted(n for n in a.namelist() if a.read(n) != b.read(n))
        assert diff == rep['members_changed'], (diff, rep['members_changed'])
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=m['zip'], tag=TAG, game=GAME, old=h, new=rep['md5_out']))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    if scratch:
        LO.MAPS[name] = dict(slot=m['slot'], zip=m['zip'])
        LO.TAG = TAG
        LO.rehearse(out, name, src, rep['md5_out'], h, scratch, log)
    return rep


INSTALL_PY = LO.INSTALL_PY.replace('loot-placement', 'Arcade-standard fix').replace('tools/kl_loot_1025.py', 'tools/kl_arcade_fix_1026.py').replace('2026-10-25', '2026-10-26')


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__)
        return 2
    for n in [x for x in a[2:] if x in SPEC] or list(SPEC):
        stage_map(a[1], n, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
