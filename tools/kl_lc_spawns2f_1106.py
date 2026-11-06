#!/usr/bin/env python3
r"""kl_lc_spawns2f_1106.py - Last Call (DM05A, slot F01): the crew starts on the 2nd floor. Written 2026-11-06 (item 4 of re/lastcall_content_plan_1106.md).
OFFLINE only: nothing here is run in the game and nothing writes into the game folder (install.py does, run by the owner).

WHAT MOVES (31 nodes, position and rotation only; no node added, no REF label, slot id, list, .oct/.rmi/.rmc/.prm touched):
  Heroes!Hero_01..08                       the eight player groups (a direct boot, e.g. DefaultScene=..., puts the player at Hero_01)
  FASpecials!SpawnPoint!SpawnPoint_Start_08 the one START spawn point (stock: exactly on Hero_02)
  FASpecials!SpawnPoint!UCC!SpawnPoint_Start_01..08                  UCC start set (stock: Hero_n + (60, 20))
  FASpecials!SpawnPoint!SpawnPoint_Start_Traitor_01..04              TRAITOR set
  FASpecials!SpawnPoint!UCC!SpawnPoint_Start_Traitor_01..04          UCC_TRAITOR set (stock: beside the TRAITOR set, 45 away)
  FASpecials!SpawnPoint!TeamMode!SpawnPoint_TEAM_Merc#01..06         TEAM_MERC set
STAYS: the police sets (TEAM_POLICE, UCC_POLICE 'Dead'), Heroes!Henchmen_*, the zone sets TEAM_010/020/030 (MERC1/2/3), every other node.

WHERE: the far WEST END of floor 2 (y 460), x -4860..-4500, z 540..1230 (the dance floor's west bay and the pocket south of it). Why there and not nearer the stairs: every other
patch of floor 2 lies under 15 m from a guard post of F2_Hold / F2_Shot / SurpriseStairs / HunterKillers (the stairs top is the middle of them), so a
spawn there would be inside a wake radius. The west end is >= 15 m (1500 units) from every enemy actor AND every node of an enemy squad (posts, cover, chain),
the nearest being F2_Flank (-3146, 460, -299) at about 19 m. TRADE-OFF (stated, not hidden): the crew starts about 50 m of walk from the stairs top and has
to fight its way EAST; the F2_Flank squad comes from the south-east, the crowd civilians stand east of x -1000 so nobody is near the spawn.
FACING: east (+x) for all, toward the stairs and the guards. ZSpawnPoint looks along local +Z (rot9), a player group along local -Z (look9), as
kl_fa_author documents; `check` reads the facing back from the written file.

REF labels stay as they are: the nodes are edited by name (.prp ZGEOM[1] / ZGEOM[2] and the .gms record, kept equal as a build does).

usage (from tools/):
  python kl_lc_spawns2f_1106.py stage [--src <zip>] [--pin <md5 or prefix>] [--out <dir>]   build the stage (default: the live zip, e6d2f73e..., C:\kl_build_1024\lcspawn2f_1106)
  python kl_lc_spawns2f_1106.py check [--src <zip>] [--pin <md5>] [--out <dir>]              offline self-check of the stage against --src
  python kl_lc_spawns2f_1106.py points [--src <zip>]                                          design aid: the facts of every planned point on --src (writes nothing)
--src is only ever READ (through a scratch copy under <out>\_in). To stack this pass on a later pass (the kick doors), give --src <that stage's F01_Main.zip>
and --pin <its md5>: the bots sibling and base.md5 next to --src give install.py its 'old' pins.
"""
import collections, hashlib, json, math, os, re, shutil, struct, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT = r'C:\kl_build_1024\lcspawn2f_1106'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
LIVE_PIN = 'e6d2f73ef0c51bfdbaec56c9534a4c9a'      # the live plain zip (2026-11-06 10:19)
TAG = '.before-spawn2f1106'
BS = chr(92)
R = 'ROOT' + BS
FLOOR_Y = 462.0                                    # floor 2: the collision floor is 460 or 462 (tile height); a spawn stands ON the floor (stock: y 30 on the street slab at y 30)
FACE = (1.0, 0.0)                                  # east: toward the stairs and the guards
MIN_ENEMY = 1500.0                                 # 15 m from every enemy actor and squad node
MIN_CIV = 300.0
MIN_CLEAR = 80.0                                   # nav wall clearance (a player capsule is about 40 wide; the wall edges include the pillars' rims)
MIN_EDGE = 250.0                                   # to the nearest drop-off (the fall assert 0x5e4a22 is for falling forever, this keeps it far from any ledge)
MIN_GAP = 50.0                                     # two points of one set
SP = 'FASpecials!SpawnPoint!'
SET = {'hero': 'player group', 'start': 'START', 'ucc': 'UCC', 'traitor': 'TRAITOR', 'ucc_traitor': 'UCC_TRAITOR', 'merc': 'TEAM_MERC'}
TYPE = {'start': 'eSPAWN_TYPE_FRAGILE_ALLIANCE_START', 'ucc': 'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC', 'traitor': 'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR',
        'ucc_traitor': 'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR', 'merc': 'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC'}
CHANGED_OK = ('.prp', '.gms', '.buf')              # the only members that may differ from --src


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ the plan
def plan():
    """[(set, node name below ROOT, (x, y, z), (face dx, dz))] for the 31 nodes. Two patches of the west end (measured with `points`, see the module doc):
    the BAY (x -4860..-4500, z 980..1230: between the two pillars at z 800 and z 1400, 15 m from every post) holds the crew sets, three columns that look east;
    the SOUTH POCKET (x -4860..-4530, z 540..650, 4 m behind the pillar line) holds the traitor sets and TEAM_MERC. The sets are ALTERNATIVES (one is
    used per game mode), so they may overlap each other; within a set every point is >= 60 from the next."""
    y, out = FLOOR_Y, []
    col = {1: -4800.0, 2: -4700.0, 3: -4600.0}
    hero = {1: (1, 1000.0), 2: (1, 1090.0), 3: (1, 1180.0), 4: (2, 1045.0), 5: (2, 1135.0), 6: (2, 1210.0), 7: (3, 1045.0), 8: (3, 1135.0)}
    pos = {n: (col[c], y, z) for n, (c, z) in hero.items()}
    for n, p in pos.items():
        out.append(('hero', 'Heroes!Hero_%02d' % n, p, FACE))
    out.append(('start', SP + 'SpawnPoint_Start_08', pos[2], FACE))                           # stock: START_08 stands exactly on Hero_02
    for n, p in pos.items():                                                                  # stock: UCC_n = Hero_n + (60, 20); here (35, -35) keeps it inside the bay
        out.append(('ucc', SP + 'UCC!SpawnPoint_Start_%02d' % n, (p[0] + 35.0, y, p[2] - 35.0), FACE))
    for n in range(4):
        x = -4800.0 + 60 * n
        out.append(('traitor', SP + 'SpawnPoint_Start_Traitor_%02d' % (n + 1), (x, y, 585.0), FACE))
        out.append(('ucc_traitor', SP + 'UCC!SpawnPoint_Start_Traitor_%02d' % (n + 1), (x, y, 545.0), FACE))   # stock: beside the TRAITOR row, 45 away
    for n in range(6):
        out.append(('merc', SP + 'TeamMode!SpawnPoint_TEAM_Merc#%02d' % (n + 1), (-4830.0 + 60 * n, y, 625.0), FACE))
    return out


def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


# ------------------------------------------------------------------ the edit
def move_nodes(src, dst, log=print):
    """src zip -> dst zip with the plan's nodes moved. Returns a report dict. Only .prp, .gms, .buf members may differ; slot ids stay."""
    import kl_fa, kl_gms, kl_scene
    import kl_fa_bots as KB
    import kl_fa_author as AU
    import kl_fa_bank as BK
    import kl_octree as O
    import kl_prpjoin as J
    import kl_bots_kick_1025 as KK
    from kl_prp import Prp
    B = KB.Built(src)
    sc, A = B.sc, B.scene
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    if not all(a is b for a, b in zip(B.ents, A.entities())):
        raise ValueError('Built.ents are not the scene\'s entities')
    slot0 = A.slots()
    base_prp = same.p.serialize()       # the joined tree before any edit: kl_prpjoin re-encodes ~158 kB of cross-references (same meaning), so the edit is applied as a byte patch to the ORIGINAL .prp
    pl = plan()
    moves = []
    for kind, name, pos, face in pl:
        ks = one(sc, name)
        kj = same.resolve(R + name)
        if len(kj) != 1:
            raise ValueError('%s: %d nodes in the joined tree' % (name, len(kj)))
        kj = kj[0]
        lab = J.labels('dd', same.cls(kj))
        if kind != 'hero':
            tv = kl_fa.node_values(same, kj)[8]                  # field 8 of a ZSpawnPoint is its eSPAWN_TYPE_* string (read off the live file)
            if tv != TYPE[kind]:
                raise ValueError('%s: spawn type %s, the plan says %s (%s)' % (name, tv, TYPE[kind], kind))
        if sc.parent[ks] != 0:
            raise ValueError('%s: not a top node (the plan writes world values)' % name)
        old = tuple(float(x) for x in kl_fa.node_values(same, kj)[lab.index('ZGEOM[2]')])
        ent = B.ents[ks - 1]
        eo = struct.unpack_from('<3f', ent.trans, 0)
        if max(abs(eo[i] - old[i]) for i in range(3)) > 0.5:
            raise ValueError('%s: .prp place %s and .gms place %s differ' % (name, old, eo))
        m9 = AU.look9(face) if kind == 'hero' else AU.rot9(face)
        new = tuple(float(x) for x in pos)

        def fn(us, lab=lab, m9=m9, new=new, same=same):
            AU.setv(same, us, lab.index('ZGEOM[1]'), [float(x) for x in m9])
            AU.setv(same, us, lab.index('ZGEOM[2]'), list(new))
        kl_fa.edit(same, kj, None, fn)
        ent.rot = struct.pack('<9f', *m9) + ent.rot[36:]
        ent.trans = struct.pack('<3f', *new) + ent.trans[12:]
        moves.append(dict(kind=kind, node=name, ref=ent.ref, old=[round(v) for v in old], new=[round(v) for v in new]))
    edited = same.p.serialize()
    orig_prp = B['.prp']
    if not (len(edited) == len(base_prp) == len(orig_prp)):
        raise ValueError('the edit changed the .prp length: it must only overwrite floats')
    prp_b = bytearray(orig_prp)
    n_patch = 0
    for i in range(len(edited)):
        if edited[i] != base_prp[i]:
            prp_b[i] = edited[i]
            n_patch += 1
    prp = bytes(prp_b)
    log('.prp: %d bytes patched in place (the rest of the original file is untouched)' % n_patch)
    back = Prp(prp)
    if len(back.nodes()) != len(same.nodes):
        raise ValueError('the patched .prp has a different node count')
    gms, buf = A.write()
    if A.slots() != slot0:
        raise ValueError('the slot ids moved: a move must not renumber anything')
    newf = dict(B.files)
    newf[B.ext['.prp']], newf[B.ext['.gms']], newf[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    # the trees are keyed by slot id and by box: a spawn point is not in a tree, which room_sets_check proves (same result, files not rewritten)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    repl = {B.ext[e]: newf[B.ext[e]] for e in CHANGED_OK if newf[B.ext[e]] != B.files[B.ext[e]]}
    work = tempfile.mkdtemp(prefix='spawn2f_')
    try:
        wz = os.path.join(work, os.path.basename(dst))
        KK.patch_zip(src, wz, repl)
        counts = []
        for zsrc in (src, wz):
            tmpd = tempfile.mkdtemp(prefix='spawn2f_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, os.path.basename(dst)))
                counts.append(BK.seal(tmpd, log=lambda *_: None))
            finally:
                KK.rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        problems = BK.reverify(work, log=lambda *_: None)
        wi = tempfile.mkdtemp(prefix='spawn2f_in_')
        try:
            shutil.copyfile(src, os.path.join(wi, os.path.basename(dst)))
            base_problems = BK.reverify(wi, log=lambda *_: None)
        finally:
            KK.rmtree(wi)
        problems = [x for x in problems if x not in base_problems]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(wz, dst)
    finally:
        KK.rmtree(work)
    log('moved %d nodes; members changed: %s' % (len(moves), sorted(e for e in CHANGED_OK if B.ext[e] in repl)))
    return dict(moves=moves, changed=sorted(repl), seal_moved=counts[1], reverify_new_problems=len(problems))


# ------------------------------------------------------------------ the point tests
class World:
    """What the point tests need, read once from a zip: the property tree + frames, the nav mesh, the collision grid."""

    def __init__(self, zp, log=print):
        import kl_fa, kl_fa_bots as KB, kl_route
        self.zp = zp
        self.B = KB.Built(zp)
        self.sc = self.B.sc
        self.nav = KB.Nav(self.B.scene.nav, links=True)
        log('  reading the collision of %s ...' % os.path.basename(zp))
        self.lv = kl_route.load(zp)
        self.g = kl_route.Grid(self.lv)
        sc, B = self.sc, self.B
        self.enemy, self.civ, self.post = [], [], []
        tops = set(sc.tops())
        top_of = {}
        for k in range(1, len(sc.nodes)):
            t = k
            while sc.parent[t] != 0:
                t = sc.parent[t]
            top_of[k] = t
        squads = set()
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZFFActor':
                kind = B.values(k)['ZFFActor[0]']
                p = B.at(k)
                if kind == 'Enemy':
                    self.enemy.append((sc.path[k], p))
                    squads.add(top_of[k])
                elif kind == 'Neutral':
                    self.civ.append((sc.path[k], p))
        # a squad's own nodes: posts, covers, the Defend chain's places (everything below its top that has a position and is not a geometry stub)
        for k in range(1, len(sc.nodes)):
            if top_of[k] in squads and sc.cls(k) in ('ZSTDOBJ', 'ZGROUP', 'ZBoxPrimitive'):
                p = B.at(k)
                if any(abs(v) > 0.5 for v in p):
                    self.post.append((sc.path[k], p))
        import kl_fa as KF
        self.kill, self.bound, self.trig = [], [], []
        for k, _i, v in KF.controllers(sc, 'KillBox'):
            self.kill.append(k)
        for k, _i, v in KF.controllers(sc, 'LevelBound'):
            for j in [k] + [j for lst in v[0:2] for s in lst for j in sc.resolve(s)]:
                self.bound.append(j)
        seen = set(self.kill) | set(self.bound)
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZBoxPrimitive' and sc.nodes[k]['ctrls'] and k not in seen:
                names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
                if not all(n in ('ZCoverBox', 'CoverBox') for n in names):
                    self.trig.append((k, names))

    def facts(self, p, log=None):
        """Every test of one standing point p = (x, y, z) -> dict."""
        sc, B, g, nav = self.sc, self.B, self.g, self.nav
        f = collections.OrderedDict(at=tuple(p))
        i, j = g.cell(p[0], p[2])
        fl = sorted(y for y, _ in g.floors(i, j) if abs(y - p[1]) <= 30)
        f['floor'] = fl[-1] if fl else None
        f['free'] = bool(fl) and not g.hit(i, j, fl[-1])
        above = sorted(y for y, _ in g.floors(i, j) if y > p[1] + 20)
        f['head'] = round(above[0] - p[1]) if above else 9999
        a = nav.at(p[0], p[1], p[2])
        f['nav'] = a is not None
        f['nav_part'] = nav.part[a[0]] if a else None
        f['clear'] = round(nav.clearance(p[0], p[1], p[2]))
        f['edge'] = self.edge(p)
        for key, rows, flat in (('enemy', self.enemy, False), ('post', self.post, False), ('civ', self.civ, False)):
            ds = [math.hypot(p[0] - q[0], p[2] - q[2]) for _n, q in rows if abs(q[1] - p[1]) < 250]            # same storey: the next one is 400 up
            f['d_' + key] = round(min(ds)) if ds else 99999
        hits = []
        for what, nodes in (('kill', self.kill), ('bound', self.bound)):
            for k in nodes:
                if any(B.in_box(k, (p[0], p[1] + dy, p[2])) for dy in (0.0, 90.0, 180.0)):
                    hits.append('%s %s' % (what, sc.names[k]))
        f['boxes'] = hits
        info = []
        for k, names in self.trig:
            if any(B.in_box(k, (p[0], p[1] + dy, p[2])) for dy in (0.0, 90.0, 180.0)):
                info.append('%s [%s]' % (sc.names[k][-50:], ','.join(names)))
        f['triggers'] = info
        return f

    def edge(self, p, rmax=600.0):
        """Distance to the nearest drop-off: 16 rays, a cell with no floor at the spawn's height and nothing solid in its body column is a drop,
        a wall (a solid) ends the ray safely. rmax when none is nearer."""
        g, best = self.g, rmax
        for a in range(16):
            dx, dz = math.cos(a * math.pi / 8), math.sin(a * math.pi / 8)
            r = 40.0
            while r <= rmax:
                x, z = p[0] + dx * r, p[2] + dz * r
                i, j = g.cell(x, z)
                near = [y for y, _ in g.floors(i, j) if abs(y - p[1]) <= 45]
                if near:
                    if g.hit(i, j, near[-1]):
                        break
                else:
                    if g.hit(i, j, p[1]):
                        break
                    best = min(best, r)
                    break
                r += 20.0
        return round(best)


def verdict(f, label):
    """The faults of one point's facts."""
    bad = []
    if f['floor'] is None:
        bad.append('no collision floor within 30 of the point')
    elif not f['free']:
        bad.append('the body column is blocked (furniture / pillar)')
    if f['head'] < 200:
        bad.append('only %d units of headroom' % f['head'])
    if not f['nav']:
        bad.append('off the navigation mesh')
    if f['clear'] < MIN_CLEAR:
        bad.append('nav wall clearance %d < %d' % (f['clear'], MIN_CLEAR))
    if f['edge'] < MIN_EDGE:
        bad.append('a drop-off %d away (< %d)' % (f['edge'], MIN_EDGE))
    if f['d_enemy'] < MIN_ENEMY:
        bad.append('an enemy actor %d away (< %d)' % (f['d_enemy'], MIN_ENEMY))
    if f['d_post'] < MIN_ENEMY:
        bad.append('a squad post/node %d away (< %d)' % (f['d_post'], MIN_ENEMY))
    if f['d_civ'] < MIN_CIV:
        bad.append('a civilian %d away (< %d)' % (f['d_civ'], MIN_CIV))
    for b in f['boxes']:
        bad.append('inside ' + b)
    return ['%s: %s' % (label, b) for b in bad]


def spacing(pts):
    """Smallest horizontal gap between two points of the same set, and between any two points."""
    sets = collections.defaultdict(list)
    for kind, _n, p, _f in pts:
        sets[kind].append(p)
    within = min((math.hypot(a[0] - b[0], a[2] - b[2]) for ps in sets.values() for n, a in enumerate(ps) for b in ps[n + 1:]), default=1e9)
    allp = [p for _k, _n, p, _f in pts]
    every = min(math.hypot(a[0] - b[0], a[2] - b[2]) for n, a in enumerate(allp) for b in allp[n + 1:])
    return within, every


def points(zp, log=print):
    """Design aid: the plan's points tested on zp. -> (faults, per-point facts)."""
    W = World(zp, log)
    bad, rows = [], []
    for kind, name, pos, face in plan():
        f = W.facts(pos)
        rows.append((kind, name, f))
        bad += verdict(f, name)
        log('%-9s %-62s %s' % (kind, name[-62:], ' '.join('%s=%s' % (k, f[k]) for k in ('floor', 'free', 'head', 'nav', 'nav_part', 'clear', 'edge', 'd_enemy', 'd_post', 'd_civ'))))
        if f['triggers']:
            log('          trigger boxes around: %s' % f['triggers'])
    w, e = spacing(plan())
    if w < MIN_GAP:
        bad.append('two points of one set are %d apart (< %d)' % (w, MIN_GAP))
    log('spacing: within a set %d, any two %d' % (w, e))
    return bad, rows


# ------------------------------------------------------------------ install.py
INSTALL = r'''r"""Installs / undoes the Last Call 2ND-FLOOR SPAWNS pass (2026-11-06): the crew's start sets move to the far west end of floor 2 (tools/kl_lc_spawns2f_1106.py).
Position and rotation of 31 nodes only; the plain zip md5 must be exactly the pinned one (%(pin8)s...), so a later pass over the live zip refuses it (re-stage on top).

  python install.py            install (originals -> <name>.before-spawn2f1106 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also usable with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a scratch copy); --skip-run-check for those only
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Never touches KL_PortBackup or any other file."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', '.before-spawn2f1106'
IN_ZIP_MD5 = '%(pin)s'      # the precheck: the live plain zip must still be exactly this
FILES = [   # name, live md5 before, staged md5 after
%(files)s]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %%s is not there' %% live); return 1
        cur = md5(live)
        print('%%-26s live %%s' %% (n, cur))
        if n == 'F01_Main.zip' and not undo and cur != IN_ZIP_MD5:
            print('REFUSED: the live zip is %%s, not %%s: another pass changed it, re-stage the spawns on the new live zip' %% (cur, IN_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %%s' %% bak); return 1
            if cur != new:
                print('REFUSED: %%s live md5 %%s is not the installed %%s' %% (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %%s is not md5 %%s' %% (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %%s live md5 %%s is not the pinned %%s (already installed, or another pass changed it: re-stage)' %% (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %%s missing or not md5 %%s' %% (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %%s %%s' %% ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%%s: %%s %%s' %% (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%%s); %%s' %% (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(st, files, pin):
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = INSTALL % dict(files=fl, pin=pin, pin8=pin[:8])
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL last call spawns 2f 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call spawns 2f 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


# ------------------------------------------------------------------ stage
def take_copy(src, pin, out, name='_in'):
    """src (only ever read) -> <out>\\_in\\F01_Main.zip, md5-checked against pin (a prefix of >= 8 hex digits is enough)."""
    if len(pin) < 8:
        raise ValueError('--pin: give at least 8 hex digits of the expected md5')
    inp = os.path.join(out, name)
    shutil.rmtree(inp, ignore_errors=True)
    os.makedirs(inp)
    dst = os.path.join(inp, 'F01_Main.zip')
    shutil.copyfile(src, dst)
    h = md5(dst)
    if not h.startswith(pin.lower()):
        shutil.rmtree(inp, ignore_errors=True)
        raise ValueError('%s md5 %s is not the pin %s: refusing (re-pin after the new pass is understood)' % (src, h, pin))
    return dst, h


def stage(out, src=None, pin=LIVE_PIN, log=print):
    import kl_botsonline
    src = src or os.path.join(MAPDIR, 'F01_Main.zip')
    old_dir = os.path.dirname(os.path.abspath(src))
    if not all(os.path.isfile(os.path.join(old_dir, n)) for n in ('F01_Main.bots.zip', 'F01_Main.bots.base.md5')):
        old_dir = MAPDIR   # src is a bare copy: the live slot's sibling files are the old pins (only read)
    for n in ('F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        if not os.path.isfile(os.path.join(old_dir, n)):
            raise ValueError('%s: no %s beside the input (install.py pins the bots files from there)' % (old_dir, n))
    os.makedirs(out, exist_ok=True)
    cp, h_in = take_copy(src, pin, out)
    rep = {'src': src, 'src_md5': h_in}
    final = os.path.join(out, 'F01_Main.zip')
    try:
        rep.update(move_nodes(cp, final, log))
        rep['md5_plain'] = md5(final)
        kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
        open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(rep['md5_plain'] + '\n')
        files = {}
        for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
            files[n] = (md5(os.path.join(old_dir, n)), md5(os.path.join(out, n)))
        rep['files'] = files
        write_install(out, files, h_in)
        with open(os.path.join(out, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
    finally:
        shutil.rmtree(os.path.join(out, '_in'), ignore_errors=True)       # the scratch copy of the input (~115 MB)
    log('staged %s  plain md5 %s' % (out, rep['md5_plain']))
    return rep


# ------------------------------------------------------------------ the offline self-check
def rp(o):
    """repr with object addresses removed: parsed nodes hold objects without __eq__, so == is identity there; repr of the bytes/ints/labels is exact."""
    return re.sub(r' at 0x[0-9a-fA-F]+', '', repr(o))


def check(out, src=None, pin=LIVE_PIN, log=print):
    """Diff --src against the staged zip and test every new point. Returns (faults, facts). Reads --src through a scratch copy in <out>\\_chk."""
    import kl_fa, kl_gms
    import kl_fa_bots as KB
    import kl_prpjoin as J
    src = src or os.path.join(MAPDIR, 'F01_Main.zip')
    bad, facts = [], collections.OrderedDict()

    def fail(s):
        bad.append(s)
        log('FAIL ' + s)

    def ok(k, v):
        facts[k] = v
        log('  ok  %s: %s' % (k, v))
    sz = os.path.join(out, 'F01_Main.zip')
    try:
        lz, h_in = take_copy(src, pin, out, '_chk')
    except ValueError as e:
        fail(str(e))
        return bad, facts
    try:
        ok('input md5', h_in)
        ok('staged md5', md5(sz))
        zl, zs = zipfile.ZipFile(lz), zipfile.ZipFile(sz)
        if zl.namelist() != zs.namelist():
            fail('member list/order differs')
        differ = []
        for a, b in zip(zl.infolist(), zs.infolist()):
            if (a.CRC, a.file_size) != (b.CRC, b.file_size):
                differ.append(a.filename)
        ext = {n.rsplit('_Main', 1)[1]: n for n in zl.namelist() if '_Main' in n}
        bad_mem = [n for n in differ if not any(n == ext[e] for e in CHANGED_OK)]
        if bad_mem:
            fail('members changed that must stay byte-identical: %s' % bad_mem[:5])
        # CRC equal is not byte equal: compare the bytes of every member that is not meant to change
        same = 0
        for n in zl.namelist():
            if n in differ:
                continue
            with zl.open(n) as fa, zs.open(n) as fb:
                while True:
                    ca, cb = fa.read(1 << 22), fb.read(1 << 22)
                    if ca != cb:
                        fail('member %s differs in content with equal CRC' % n)
                        break
                    if not ca:
                        break
            same += 1
        ok('members', '%d, %d byte-identical, changed: %s' % (len(zl.namelist()), same, [n.rsplit('_Main', 1)[1] for n in differ]))
        # the trees: .prp node by node, .gms entity by entity
        A, Bn = KB.Built(lz), KB.Built(sz)
        a, b = A.sc, Bn.sc
        if (a.names, a.tids, a.parent) != (b.names, b.tids, b.parent):
            fail('node names / classes / parents differ')
        target = {}
        for kind, name, pos, face in plan():
            target[one(a, name)] = (kind, name, pos, face)
        n_node = 0
        for k in range(1, len(a.nodes)):
            na, nb = a.nodes[k], b.nodes[k]
            if k in target:
                if rp(na['ctrls']) != rp(nb['ctrls']):
                    fail('%s: controllers changed' % a.names[k])
                lab = J.labels('dd', a.cls(k))
                va, vb = kl_fa.node_values(a, k), kl_fa.node_values(b, k)
                diff = [lab[i] for i in range(len(va)) if va[i] != vb[i]]
                if not set(diff) <= {'ZGEOM[1]', 'ZGEOM[2]'}:
                    fail('%s: fields other than the place changed: %s' % (a.names[k], diff))
                n_node += 1
            elif rp(na) != rp(nb):
                fail('%s: a node that must not change differs' % a.names[k])
        ok('.prp', '%d nodes, only the %d planned nodes differ and only in ZGEOM[1] / ZGEOM[2]' % (len(a.nodes) - 1, n_node))
        if len(target) != 31:
            fail('the plan names %d nodes, not 31' % len(target))
        ea, eb = A.ents, Bn.ents
        if len(ea) != len(eb):
            fail('entity counts differ')
        n_ent = 0
        for k, (x, y) in enumerate(zip(ea, eb), 1):
            if (x.ref, x.name, x.tid, x.flags, x.group, x.model, x.aux, rp(x.links), x.raw, x.parent and x.parent.ref) != \
                    (y.ref, y.name, y.tid, y.flags, y.group, y.model, y.aux, rp(y.links), y.raw, y.parent and y.parent.ref):
                fail('entity %s (REF %s): more than the place changed' % (x.name, x.ref))
            moved = (x.rot, x.trans) != (y.rot, y.trans)
            if moved != (k in target):
                fail('entity %s (REF %s): %s' % (x.name, x.ref, 'moved but not planned' if moved else 'planned but not moved'))
            if k in target:
                n_ent += 1
        sla, slb = A.scene.slots(), Bn.scene.slots()
        if {e.ref: sla[e] for e in A.ents} != {e.ref: slb[e] for e in Bn.ents}:
            fail('the slot ids differ')
        ok('.gms', '%d entities, REF labels and slot ids equal; %d moved' % (len(ea), n_ent))
        # prp and gms agree on the place, and the facing reads back
        for k, (kind, name, pos, face) in target.items():
            p = Bn.at(k)
            if max(abs(p[i] - pos[i]) for i in range(3)) > 0.01:
                fail('%s: written at %s, planned %s' % (name, p, pos))
            v = kl_fa.node_values(b, k)
            lab = J.labels('dd', b.cls(k))
            g2 = v[lab.index('ZGEOM[2]')]
            if max(abs(g2[i] - pos[i]) for i in range(3)) > 0.01:
                fail('%s: .prp place %s differs from planned %s' % (name, g2, pos))
            Rm = Bn.fr[Bn.ents[k - 1]][0]
            fwd = (Rm[0][2], Rm[2][2])
            if kind == 'hero':
                fwd = (-fwd[0], -fwd[1])
            if math.hypot(fwd[0] - face[0], fwd[1] - face[1]) > 1e-3:
                fail('%s: faces %s, planned %s' % (name, fwd, face))
        ok('facing', 'all 31 read back facing %s (spawn points along local +Z, player groups along local -Z)' % (FACE,))
        # the point tests on the STAGED zip, positions read from the file
        W = World(sz, log)
        ppl = [(kind, name, tuple(Bn.at(k)), face) for k, (kind, name, _p, face) in target.items()]
        rows = []
        for kind, name, p, face in ppl:
            f = W.facts(p)
            rows.append((name, f))
            for s in verdict(f, name):
                fail(s)
        w, e = spacing(ppl)
        if w < MIN_GAP:
            fail('two points of one set are %d apart (< %d)' % (w, MIN_GAP))
        ok('spacing', 'smallest gap within a set %d, between any two points %d' % (w, e))
        ok('floor/free/nav', 'all %d: collision floor within 30 of y %d, body column free, headroom >= %d, on the nav mesh part(s) %s, wall clearance >= %d' % (
            len(rows), FLOOR_Y, min(f['head'] for _n, f in rows), sorted({f['nav_part'] for _n, f in rows}), min(f['clear'] for _n, f in rows)))
        ok('drop-offs', 'nearest drop-off from any point %d (limit %d)' % (min(f['edge'] for _n, f in rows), MIN_EDGE))
        ok('guards', 'nearest enemy actor %d, nearest squad node %d (limit %d); nearest civilian %d (limit %d)' % (
            min(f['d_enemy'] for _n, f in rows), min(f['d_post'] for _n, f in rows), MIN_ENEMY, min(f['d_civ'] for _n, f in rows), MIN_CIV))
        ok('boxes', '%d kill boxes, %d level-bound/warn boxes tested at feet/knee/head: %d points inside one' % (
            len(W.kill), len(W.bound), sum(1 for _n, f in rows if f['boxes'])))
        trig = collections.Counter(t for _n, f in rows for t in f['triggers'])
        ok('other trigger boxes holding a point', dict(trig) if trig else 'none')
        # the walk from the old street start
        import kl_route
        old_start = (280.0, 30.0, -2740.0)
        st = kl_route.stations(W.lv, [old_start] + [p for _k, _n, p, _f in ppl], near=30)
        part = st[0]['part']
        off = [(n, r) for (_k, n, _p, _f), r in zip(ppl, st[1:]) if not (r['mesh'] and r['part'] == part and r['reached'])]
        for n, r in off:
            fail('%s: not reached on foot from the old street start (mesh %s, part %s vs %s, reached %s, gap %s)' % (n, r['mesh'], r['part'], part, r['reached'], r.get('gap')))
        lens = [r['length'] for r in st[1:] if r['length'] is not None]
        ok('walk from the street', 'every point on the street start\'s mesh part %s and reached; %s..%s m of walking' % (part, min(lens) if lens else '?', max(lens) if lens else '?'))
        facts['points'] = [(n, dict(f)) for n, f in rows]
        # the bots sibling follows the plain zip
        bz = os.path.join(out, 'F01_Main.bots.zip')
        if os.path.isfile(bz):
            Bs = KB.Built(bz)
            for k, (kind, name, pos, face) in target.items():
                p = Bs.at(k)
                if max(abs(p[i] - pos[i]) for i in range(3)) > 0.01:
                    fail('bots sibling: %s at %s, planned %s' % (name, p, pos))
            bm = open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip()
            if bm != md5(sz):
                fail('bots.base.md5 %s is not the plain zip\'s %s' % (bm, md5(sz)))
            ok('bots sibling', 'holds the same places; base.md5 = the plain zip')
        else:
            fail('no F01_Main.bots.zip in the stage')
    finally:
        shutil.rmtree(os.path.join(out, '_chk'), ignore_errors=True)
    log('RESULT: %s' % ('FAIL %d' % len(bad) if bad else 'PASS'))
    return bad, facts


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('stage', 'check', 'points'):
        print(__doc__)
        return 2

    def opt(name, default):
        return a[a.index(name) + 1] if name in a else default
    out, src, pin = opt('--out', OUT), opt('--src', None), opt('--pin', LIVE_PIN)
    if a[0] == 'points':
        s = src or os.path.join(MAPDIR, 'F01_Main.zip')
        os.makedirs(out, exist_ok=True)
        cp, _h = take_copy(s, pin, out)
        try:
            bad, _rows = points(cp)
        finally:
            shutil.rmtree(os.path.join(out, '_in'), ignore_errors=True)
        for b in bad:
            print('FAULT', b)
        print('RESULT: %s' % ('FAIL %d' % len(bad) if bad else 'PASS'))
        return 1 if bad else 0
    if a[0] == 'stage':
        stage(out, src, pin)
    bad, _f = check(out, src, pin)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
