#!/usr/bin/env python3
"""
Retomoto Tower: what the loot looks like and whether it can be picked up (owner, 2026-10-09 22:00:
'change the props of the money - its bags all around; it should be briefcases for sure in that start
room, and make the ones on the left side from spawn closer to the outer ring since u cant actually
pick the money up; the statue ones - use a good prop replacement for that'). Offline; nothing here
installs anything or starts the game. Spec, evidence, pictures, what only the owner's eyes can
settle: re/retomoto_loot.md.

    python kl_fa_loot.py test <out> [options]             THE BUILD: the whole layer (kl_fa_blast.test =
                                                          kl_fa_author + street + blast, voices on) into
                                                          <out>, the loot dressed, then kl_graft lighten
                                                          and kl_chars wardrobe -> <out>\retomoto_loot,
                                                          every check on that folder (12 minutes)
    python kl_fa_loot.py dress <built folder> <out folder> [options]    only the loot, on a level that
                                                          exists (also one with a wardrobe), as a copy
    python kl_fa_loot.py check <folder>                   every check on a finished folder
    python kl_fa_loot.py survey <archive | stock level>   every loot object: what it shows, where, its
                                                          pick-up reach, where a player can stand for it
    python kl_fa_loot.py sketch <archive> [before archive] top view of the boardroom with the loot
    python kl_fa_loot.py props [out folder]               every case / briefcase / suitcase prop of both
                                                          games, with a picture of each (kl_view; 3 minutes)
    python kl_fa_loot.py picture <archive | level> <out.png> <root> [root ...]    any model roots
    options (also taken by kl_fa_blast.py test):
      --case dm | dd | bag    the boardroom's prop: Dead Men's Fragile Alliance briefcase (default), Dog Days'
                              own (Subway's PC0200_F01_BriefcaseClosed), or the money bags as before
      --case-scale X          size of the case (default: Dead Men's x 1.25 = 45 wide, Dog Days' as it is, 70)
      --statue suit | bag     the samurai cases' loot: the armour itself (default) or a money bag at its feet
      --room-reach R          TriggerBox2 radius of the boardroom's loot (default 125)
      --loot-bags             bags everywhere; only the boardroom's places and reach change

WHAT IT DOES (no new entity, no new controller; 20 new .prm chunks, all in dead chunk indices)
  boardroom   the six stacks on the conference table lie in two rows along its long rims, RIM in from the
              edge of the table top (read off the table's own mesh), on the top (y 21070), radius 125, and
              show a briefcase: a model root appended from Dead Men's M01_FA_A with its three materials and
              five textures (kl_chars.Source's converters, kl_light.fit_shaders).
  statues     each of the 15 stacks at a samurai case shows the ARMOUR of that case - a new model root over
              the case model's own two armour meshes - turned as the case is; the case's model keeps frame,
              glass and hull. What is taken disappears: the armour is gone from its case.
  It works on the WRITTEN level (chunk numbers exist only then): dress(folder). kl_fa_author.FINISH holds
  finish() = dress + check once hook() ran; kl_fa_author.test and kl_fa_blast.test call it (default; --loot-bags
  leaves it out). FOR kl_graft / kl_maps (not my files), so that 'kl_maps.py chain ... --author' builds the same:
      for fn in kl_fa_author.FINISH: fn(<folder the level was written to>, log)       # after the last step
  dress() LIGHTENS FIRST (kl_graft.lighten trim + slim, when the level still has dead model roots): the dead chunk
  indices cannot be handed out before 'slim' has found the removed map's textures by its dead roots. A later
  'kl_graft.py lighten' of that level finds nothing left and changes nothing.

THE PICK-UP, read in kl2.exe (re/retomoto_loot.md 2). A money object's TriggerBox2 (ZTriggerBox2,
vtable 0xbc953c; init = slot 13, 0x750350; update = slot 25, 0x626ec0) asks the game data for the
actors round its node (0x5891f0) and tests each with 0x783e60: with h = the HORIZONTAL distance
between the actor's node (a player's: his feet) and the trigger's node, and R = field 2 + 40 (0xb23668),
        h <= R    and    |actor y - node y| <= 100 + sqrt(R * R - h * h)        (0xb3dde8 = 100)
So a stack with radius 80 is taken from up to 120 away on the floor plan and from any height a
table can have; nothing in the test looks at walls, glass or the way the player faces.
ASSUMPTION: that a money trigger takes this branch. The update takes it when the byte at +0x3d is
set, else it asks the node's own volume (0x68d030); +0x3c / +0x3d are the object's two bools and
both stored bools (fields 1 and 3) are 1 on every money trigger of the level and of stock F02.
What happens AFTER the trigger fires (OnlineMoneyCtrl's own handler, the E prompt) was not read.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence,
not proven. Each is marked where it stands; re/retomoto_loot.md 7 lists them.
"""
import collections, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene, kl_maps, kl_hvk, kl_escape
import kl_prpjoin as J
from kl_prp import units

R = 'ROOT\\'
HIDDEN = 0x400
REACH_PAD = 40.0                        # kl2 0x783e60: the horizontal reach is the TriggerBox2's field 2 + 40 (double at 0xb23668)
REACH_TALL = 100.0                      # ... and the height window 100 + the sphere's chord (double at 0xb3dde8)
BODY = 30.0                             # ASSUMPTION: how near a wall a player's feet get. Run J1 (re/retomoto_fa.md 10.1): pushed
                                        # against the tower car's shut doors he stood at x 2727, the car's box begins at x 2756
MARGIN = 20.0                           # GUESS: what a loot place must have to spare, so that 'in reach' is not a matter of a step
HERO_BITS = 0x28                        # collision flags that stop a player (kl_fa_author.HERO_BITS, same ASSUMPTION)


# ------------------------------------------------------------------ reading a level
class Built:
    """A built level or a stock one: property tree, scene, world positions, collision."""

    def __init__(self, src):
        self.path = src if os.path.isfile(src) else J.level_zip(src)
        self.sc, _snd, _loc = kl_fa.load(src)
        with zipfile.ZipFile(self.path) as z:
            self.ext = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
            self.scene = kl_scene.Scene(kl_gms.unpack(z.read(self.ext['.gms'])), z.read(self.ext['.buf']))
            self.hvk = kl_hvk.Hvk(z.read(self.ext['.hvk']))
        self.ents = list(self.scene.entities())
        self.pos = kl_maps.world(self.scene)
        self.name = {e.ref: e.name.decode('latin1') for e in self.ents}
        self.hidden = {e.ref for e in self.ents if e.flags & HIDDEN}

    def member(self, ext):
        with zipfile.ZipFile(self.path) as z:
            return z.read(self.ext[ext.lower()])

    def at(self, k):
        return self.pos[self.ents[k - 1]]

    def soft(self):
        """REF ids whose collision does not stop a player (no shape of theirs has a player's bits)."""
        hard, every = set(), set()
        for s in self.hvk.shapes:
            fl = 0
            for _su, f, _n in s.sub:
                fl |= f
            for inst in s.inst:
                every.add(kl_hvk.ref(inst))
                if fl & HERO_BITS:
                    hard.add(kl_hvk.ref(inst))
        return every - hard


def values(sc, k, name):
    for nm, body in sc.nodes[k]['ctrls']:
        if sc.p.key(nm) == name:
            return [kl_fa.value(sc, u) for u in units(body[1:-1])]
    return None


def loot(lv):
    """Every money object that is loot (OnlineMoneyCtrl not of a drop pool) -> [dict]: node, name,
    value, type, hidden at load, the pick-up radius (its own TriggerBox2 field 2), model, place."""
    sc, out = lv.sc, []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' in v[2]:
            continue
        tb = values(sc, k, 'TriggerBox2')
        e = lv.ents[k - 1]
        out.append(dict(k=k, path=sc.path[k][5:], name=sc.names[k], value=v[1], type=v[2][16:], hidden=bool(e.flags & HIDDEN),
                        radius=tb[2] if tb else None, how=tb[5] if tb else None, model=e.model, at=lv.at(k), cls=sc.cls(k)))
    return out


# ------------------------------------------------------------------ the pick-up test and the walk test
def in_reach(node, feet, radius):
    """kl2 0x783e60, as read (module docstring)."""
    r = radius + REACH_PAD
    h = math.hypot(feet[0] - node[0], feet[2] - node[2])
    return h <= r and abs(feet[1] - node[1]) <= REACH_TALL + math.sqrt(r * r - h * h)


class Floors:
    """kl_escape.Walk's grid with a flood that keeps every floor of a cell apart (a gallery over a
    hall: Walk.flood has one floor per cell). Same rules: steps of UP up / DOWN down, blocked by
    anything LO..HI above the floor stepped on."""

    def __init__(self, hvk, box, skip=()):
        self.w = kl_escape.Walk(hvk, box, skip=skip)

    def flood(self, starts, snap=60.0):
        """starts: [(x, y, z)] (a start counts when a floor lies within `snap` of its height)
        -> {cell: [floor y ...]} reached, {REF id: cells it blocked}."""
        w = self.w
        seen, block, q = collections.defaultdict(list), collections.defaultdict(set), collections.deque()
        for s in starts:
            c, y = w.floor(*s)
            if y is not None and abs(y - s[1]) < snap and not any(abs(y - v) < 30 for v in seen[c]):
                seen[c].append(y); q.append((c, y))
        while q:
            c, y = q.popleft()
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + d[0], c[1] + d[1])
                g = w.grid.get(n)
                if not g:
                    continue
                cand = [yy for yy, f, _r in g if f and -w.DOWN <= yy - y <= w.UP]
                if not cand:
                    continue
                ny = max(cand)
                if any(abs(ny - v) < 30 for v in seen[n]):
                    continue
                bl = [r for yy, _f, r in g if ny + w.LO < yy < ny + w.HI]
                if bl:
                    for r in bl:
                        block[r].add(n)
                    continue
                seen[n].append(ny); q.append((n, ny))
        return {c: v for c, v in seen.items() if v}, block

    def clear(self, seen, c, y, body=BODY):
        """True if a body of radius `body` fits at cell c on floor y: every cell within it is reached there."""
        n = int(math.ceil(body / self.w.CELL))
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                if math.hypot(i, j) * self.w.CELL <= body + 1e-6:
                    if not any(abs(v - y) < 60 for v in seen.get((c[0] + i, c[1] + j), ())):
                        return False
        return True

    def stand(self, seen, node, radius, body=BODY):
        """Where a player can stand for a pick-up at `node` -> (best place (x, y, z) or None, its
        horizontal distance, number of places in reach). Best = the one with most reach to spare."""
        w, r = self.w, radius + REACH_PAD
        c0, n = w.cell(node[0], node[2]), int(r // w.CELL) + 1
        best, count = None, 0
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                c = (c0[0] + i, c0[1] + j)
                x, z = w.centre(c)
                for y in seen.get(c, ()):
                    if in_reach(node, (x, y, z), radius) and self.clear(seen, c, y, body):
                        count += 1
                        h = math.hypot(x - node[0], z - node[2])
                        if best is None or h < best[1]:
                            best = ((x, y, z), h)
        return (best[0], best[1], count) if best else (None, None, 0)

    def under(self, lv, node):
        """What the collision has at a place: [(y, floor?, entity name)] of the node's cell, lowest first."""
        g = self.w.grid.get(self.w.cell(node[0], node[2]), ())
        return sorted((round(y), f, lv.name.get(r, '?').split('!')[-1]) for y, f, r in g)


def blast_state(lv):
    """REF ids switched (off, on) by the round-start blast: what the layer's blast timer names with
    an ActivateGeom / DeactivateGeom, and the window's own forced ShotActivate. Whole subtrees."""
    import kl_fa_author as au
    sc, off, on = lv.sc, set(), set()
    def refs(paths):
        out = set()
        for p in paths:
            for k in sc.resolve(p):
                out.update(lv.ents[j - 1].ref for j in range(k, sc.end[k]))
        return out
    if not sc.resolve(R + au.ROLE['blast timer']):
        return off, on
    todo = list(values(sc, au.node_of(sc, au.ROLE['blast timer']), 'TriggerDelay2')[4])
    for p in todo:
        for k in sc.resolve(p):
            a, d = values(sc, k, 'ActivateGeom'), values(sc, k, 'DeactivateGeom')
            if a:
                on |= refs(a[1])
            if d:
                off |= refs(d[1])
    for k in sc.resolve(au.WINDOW_PRE):                 # the window's ShotActivate: Dog Days field 3 on / 4 off
        v = values(sc, k, 'ShotActivate')
        if v:
            on |= refs(v[3]); off |= refs(v[4])
    return off, on


TOWER = (-3200.0, 6300.0, -2700.0, 2700.0)             # the walk test's box: boardroom, reception, atrium, elevator lobby
# Places a player has stood on in the game, beyond the boardroom's door (run RT3, re/retomoto_fa.md 9.3: 'every way
# point reached'). The walk test needs them as further starts: the door's leaves (D1 / D2, after the blast D03 / D04)
# are key-framed shapes that fill the doorway in the .HVK and do NOT stop a player in the game (x 3690 -> 3422 in
# 0.5 s in runs RT3 / RT4, and every round the owner has played) - the test has no way to know that.
WALKED = [(3132.0, 20996.0, -1063.0), (2497.0, 19601.0, 1063.0)]


def walk(lv, box=TOWER, starts=None, log=print):
    """The walk test of the tower after the blast -> (Floors, reached, blockers)."""
    import kl_fa_author as au
    off, on = blast_state(lv)
    skip = (lv.soft() | lv.hidden | off) - on
    f = Floors(lv.hvk, box, skip=skip)
    starts = starts or [(p[0], p[1], p[2]) for p in au.START] + WALKED
    seen, block = f.flood(starts)
    ys = [y for v in seen.values() for y in v]
    log('walk test (collision with a player\'s bits, hidden entities out, blast switched: %d off, %d on) from %s: %d cells of 20 x 20, floors y %d..%d' % (
        len(off), len(on), tuple(int(v) for v in starts[0]), sum(len(v) for v in seen.values()), min(ys), max(ys)))
    return f, seen, block


def survey(src, log=print, starts=None, box=None):
    """Every loot object of a level against the pick-up test and the walk test -> [dict]."""
    lv = Built(src)
    rows = loot(lv)
    stock = not os.path.isfile(src)
    if stock:                                           # a stock level, as a control of the test itself: a LOCAL walk, started
        own = [r for r in rows if r['radius'] is not None]      # on the floors round each loot object (stock F02's heisters start
        starts = starts or [(r['at'][0] + dx, r['at'][1], r['at'][2] + dz) for r in own       # in a train that static collision
                            for dx in (-150, 0, 150) for dz in (-150, 0, 150)]              # does not join to the loot's wagon)
        xs, zs = [s[0] for s in starts], [s[2] for s in starts]
        box = box or (min(xs) - 600, max(xs) + 600, min(zs) - 600, max(zs) + 600)
        f = Floors(lv.hvk, box, skip=lv.soft() | lv.hidden)
        seen, _block = f.flood(starts, snap=200.0)
        log('walk test, local (from the floors within 150 of each loot object): %d cells' % sum(len(v) for v in seen.values()))
    else:
        f, seen, _block = walk(lv, box or TOWER, starts, log)
    log('%-58s %-8s %9s %-7s %5s %6s  %-22s %s' % ('loot object', 'class', 'value', 'state', 'model', 'radius', 'at', 'pick-up'))
    for r in rows:
        if r['radius'] is None:
            r['stand'], r['why'] = None, 'no TriggerBox2 of its own (a container\'s loot)'
        else:
            place, h, n = f.stand(seen, r['at'], r['radius'])
            r['stand'], r['h'], r['places'] = place, h, n
            if place is None:
                near, _h, _n = f.stand(seen, r['at'], r['radius'] + 400.0)
                under = [u for u in f.under(lv, r['at']) if abs(u[0] - r['at'][1]) < 150]
                r['why'] = 'OUT OF REACH: nearest standing place %s, reach %d%s' % (
                    '%d away at (%d, %d, %d)' % (math.hypot(near[0] - r['at'][0], near[2] - r['at'][2]), *near) if near else 'more than %d away' % (r['radius'] + 440),
                    r['radius'] + REACH_PAD, '; it lies on / in %s' % ', '.join(sorted({u[2] for u in under})) if under else '')
            else:
                spare = r['radius'] + REACH_PAD - h
                r['why'] = 'ok: stand at (%d, %d, %d), %d away, reach %d (%d to spare%s), %d places' % (
                    *place, h, r['radius'] + REACH_PAD, spare, '' if spare >= MARGIN else ' - TIGHT', n)
        log('%-58s %-8s %9d %-7s %5d %6s  (%6d %6d %6d) %s' % (r['path'][-58:], r['cls'], r['value'], 'hidden' if r['hidden'] else 'shown', r['model'],
                                                               '%g' % r['radius'] if r['radius'] is not None else '-', *r['at'], r['why']))
    bad = [r for r in rows if r['radius'] is not None and r['stand'] is None]
    log('%d loot objects, %d; %d out of reach' % (len(rows), sum(r['value'] for r in rows), len(bad)))
    return rows


# ------------------------------------------------------------------ models: reading and pictures
VSTRIDE = 40                            # a static mesh's vertex: +0 position (3 floats), +12 normal (4 bytes), +16 colour,
                                        # +20 texture coordinate (2 floats), +28 / +32 tangent frame, +36 unused (read off 14 models)
NOT_DRAWN = ('_Glacier/', 'Shadow')     # material names of what is no picture: collision hulls, blob shadows


class Assets:
    """The .prm / .MAT / .TEX of a built level, a stock Dog Days level or a Dead Men level (that one
    through kl_dmassets.convert_level: Dog Days form, Dead Men's own chunk numbers)."""
    _cache = {}

    def __init__(self, src):
        import kl_prmgraph as G, kl_texmat as T
        self.src = src
        if os.path.isfile(src) or not src.startswith('M'):
            path = src if os.path.isfile(src) else J.level_zip(src)
            with zipfile.ZipFile(path) as z:
                m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
                prm, mat, tex = z.read(m['.prm']), z.read(m['.mat']), z.read(m['.tex'])
        else:
            import kl_dmassets
            out, _rep, _src = kl_dmassets.convert_level(src)
            prm, mat, tex = out['prm'], out['MAT'], out['TEX']
        self.raw = {'prm': prm, 'mat': mat, 'tex': tex}
        self.p, self.mat, self.tex = G.read(prm, 'dd'), T.read_mat(mat), T.read_tex(tex)

    @classmethod
    def of(cls, src):
        if src not in cls._cache:
            cls._cache[src] = cls(src)
        return cls._cache[src]

    def material(self, o):
        m = self.p.u16(o, 0x12)
        return self.mat.insts[m].name if m in self.mat.insts else '?'

    def meshes(self, root, drawn=True):
        """Mesh objects (lType 8) of a model root -> [chunk index]; drawn: without hulls and shadows."""
        p, out = self.p, []
        c = p.chunks[root]
        if len(c) != 64 or c[:4] != b'\0\1\7\0':
            raise ValueError('%s: chunk %d is not a model root' % (self.src, root))
        for j in range(p.u32(root, 0x14)):
            o = p.u32(p.u32(root, 0x18), 4 * j)
            if p.chunks[o][2] == 8 and not (drawn and any(w in self.material(o) for w in NOT_DRAWN)):
                out.append(o)
        return out

    def geometry(self, o):
        """(positions, texture coordinates, triangles) of a mesh object."""
        p = self.p
        d = p.u32(p.u32(o, 0x28), 0)
        nv, v = p.u32(d, 0), p.chunks[p.u32(d, 4)]
        if len(v) < VSTRIDE * nv:
            return [], [], []                           # a stub (kl_graft's emptied dead chunks)
        pos = [struct.unpack_from('<3f', v, VSTRIDE * k) for k in range(nv)]
        uv = [struct.unpack_from('<2f', v, VSTRIDE * k + 20) for k in range(nv)]
        ix = p.chunks[p.u32(d, 0x18)]
        n = struct.unpack_from('<H', ix, 2)[0]
        ii = struct.unpack_from('<%dH' % n, ix, 4)
        return pos, uv, [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)]

    def bounds(self, root, drawn=True):
        pts = [q for o in self.meshes(root, drawn) for q in self.geometry(o)[0]]
        if not pts:
            return None
        return tuple(min(q[a] for q in pts) for a in range(3)), tuple(max(q[a] for q in pts) for a in range(3))

    def describe(self, root):
        b = self.bounds(root)
        return '%d meshes (%s), %s' % (len(self.meshes(root)), ', '.join(sorted({self.material(o).split('/')[-1] for o in self.meshes(root)})),
                                       'x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]) if b else 'no geometry')


def _turn(q, yaw, pitch):
    """A point turned about Y by yaw, then about X by pitch (degrees): the camera of the pictures."""
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    x, y, z = q[0] * cy + q[2] * sy, q[1], -q[0] * sy + q[2] * cy
    return x, y * cp - z * sp, y * sp + z * cp


def panels(parts, views=((0, 0), (35, 25), (90, 0), (0, 90))):
    """kl_view panels of one object. parts: [(Assets, root, (dx, dy, dz) or None)] - several roots
    drawn together (a case and its lid); a 4th member = the mesh objects to draw (default: all
    but hulls and shadows). Views: (yaw, pitch); the last default one is from above."""
    import kl_view
    out = []
    for yaw, pitch in views:
        items, pts = [], []
        for a, root, shift, *only in parts:
            tx = kl_view.Textures(a.mat, a.tex)
            for o in (only[0] if only else a.meshes(root)):
                pos, uv, tris = a.geometry(o)
                if not pos:
                    continue
                if shift:
                    pos = [(q[0] + shift[0], q[1] + shift[1], q[2] + shift[2]) for q in pos]
                pos = [_turn(q, yaw, pitch) for q in pos]
                pts += pos
                items.append((pos, tris, kl_view.PALETTE[len(items) % len(kl_view.PALETTE)], uv, tx.of(a.p.u16(o, 0x12))))
        if not pts:
            continue
        lo, hi = [min(q[a] for q in pts) for a in range(2)], [max(q[a] for q in pts) for a in range(2)]
        half = max(hi[0] - lo[0], hi[1] - lo[1]) * 0.55 + 1
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        out.append(('front', (cx - half, cx + half, cy - half, cy + half), items))
    return out


def picture(path, rows, size=220):
    """One PNG: a row of four views per object. rows: [parts] (see panels)."""
    import kl_view
    ps = [p for parts in rows for p in panels(parts)]
    kl_view.sheet(path, ps, size, size, cols=4)
    return path


# ------------------------------------------------------------------ the props
# THE BRIEFCASE (boardroom). Dead Men's own Fragile Alliance money case: M01_FA_A 'DropMoney!KillDrop!Suitcase'
# (the same model as M06_FA_A 'Money!KillDrop!Briefcase', and the materials - Briefcase_Side_01a / _Brass_01a - of
# the Retomoto briefcase the campaign's M09 is about, 'CutScenes/M09/M09B_Bus_Station_Exit.zip\...\Briefcase_*').
# One model root, black leather with silver clasps, lying flat, x -18..18, y 0..9, z -20..14 (the handle at -z).
# 'dd' = stock Dog Days' own closed briefcase, Subway's 'DL10_Platform\PC0200_F01_BriefcaseClosed' (black, brass
# locks, 70 x 60: nearly twice the size; its geometry lies off its origin, x -47..23, z 32..92).
CASES = {'dm': ('M01_FA_A', 6380, 'DropMoney!KillDrop!Suitcase'),
         'dd': ('F01', 5646, 'PC0200_F01_BriefcaseClosed')}
CASE = 'dm'                             # None ('--case bag'): the boardroom keeps the money bags
CASE_SCALES = {'dm': 1.25,              # GUESS: Dead Men's model is 36 wide; x 1.25 = 45, a real attache case. 1.0 = as Dead Men has it.
               'dd': 1.0}               # Dog Days' own is 70 wide as it is
CASE_SCALE = None                       # '--case-scale X': another size than CASE_SCALES has for the case
                                        # (No stock entity of F02 / F07 has a scaled matrix, so the size is written into the copy's vertices.)
CASE_YAW = (8.0, -6.0, 11.0)            # GUESS: degrees off square, per column: three cases put down by hand, not ruled
# THE TABLE. Read off the built level by table(): PC0200_M09_ConferenceTable_A_01 at (4931, 20990, -100), not turned;
# its top is the mesh Wood_Black_02a_M09, y 21070, boat-shaped: z -257..29 in the middle, -237..9 at the ends,
# x 4474..5388; its collision hull reaches 7 further out. The six stacks of kl_fa_author stood at z -120 and z 20:
# 134 and 9 in from the rim. Seen from the balcony (looking -x) the row at z -120 is the LEFT one - turning right
# raises atan2(x, z) (klhook\klauto.c: mouse counts and heading, run PX3), so facing -x the left hand is -z - and it
# is the one no player can take: 190 from the nearest place to stand, reach 120 (survey).
TABLE = 'PC0200_M09_ConferenceTable_A_01'
RIM = 33.0                              # GUESS: the case's origin this far in from the table top's rim: its handle side 8 from the edge
                                        # (at CASE_SCALES['dm']; another size moves the origin in proportion, so the edge distance stays)
RIM_BAG = 50.0                          # ... and a money bag's (it is 82 long across the table)
ROOM_REACH = 125.0                      # TriggerBox2 radius of the boardroom's loot: the value of all 117 stock OnlineMoneyContainer
                                        # triggers (re/escape.md 4.1). kl_fa_author had 80 (stock F02's bags, which lie on the floor)
# THE STATUES. A samurai case is '...Montre_SamuraiSuit' with two models: '_Whole' (frame, glass, the armour: mesh
# Fabric_Samurai_01a_M09 and its dark lining Textureless_01_2sided) and '_Remain' (the bare wooden stand, shown when the
# glass is shot). 'suit': the loot IS the armour - the stack at the case shows the two armour meshes, turned as the case
# is, and the case's own model stops listing them. Taken = the armour is gone from its case.
STATUE = 'suit'                         # None ('--statue bag'): money bags at the armour's feet, as before
CASE_NODE, CASE_WHOLE, CASE_REMAIN = 'Montre_SamuraiSuit', '_Whole', '_Remain'
SUIT = ('Fabric_Samurai', 'Textureless')   # material names of the armour in the case's model


def frames(scene):
    """{entity: (R as rows, (x, y, z))} world frame of every entity (kl_maps.world's rule, with the matrix)."""
    out = {}
    def go(e, R, T):
        r = struct.unpack('<9f', e.rot[:36]); t = struct.unpack('<3f', e.trans[:12])
        m = [r[6:9], r[3:6], r[0:3]]
        m = [[m[j][i] for j in range(3)] for i in range(3)]
        p = tuple(T[i] + sum(R[i][j] * t[j] for j in range(3)) for i in range(3))
        R2 = [[sum(R[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        out[e] = (R2, p)
        for c in e.kids:
            go(c, R2, p)
    for e in scene.roots:
        go(e, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], (0.0, 0.0, 0.0))
    return out


def m9_of(Rm):
    """ZGEOM[1] / .gms record form of a matrix given as rows: [third column, second column, first column]."""
    return [Rm[i][c] for c in (2, 1, 0) for i in range(3)]


def yaw9(deg):
    """ZGEOM[1] of a turn about Y by deg (0 = not turned; 180 = local -z looks along +z)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return m9_of([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


class Edit:
    """A built level open for editing: kl_chars.Lv (the members), property tree, scene, .prm."""

    def __init__(self, folder):
        import kl_chars as C, kl_prmgraph as G, kl_texmat as T, kl_octree as O
        self.lv = C.Lv(folder)
        self.sc, self.raw = self.lv.scene()
        self.scene = kl_scene.Scene(kl_gms.unpack(self.lv['.gms']), self.lv['.buf'])
        self.ents = list(self.scene.entities())
        if [e.name.decode('latin1') for e in self.ents] != self.sc.names[1:]:
            raise ValueError('%s: .gms and .prp disagree on the entities' % folder)
        self.frame = frames(self.scene)
        self.p = G.read(self.lv['.prm'], 'dd')
        self.mat, self.tex = T.read_mat(self.lv['.MAT']), T.read_tex(self.lv['.TEX'])
        self.oct = O.Oct.parse(self.lv['.oct'])
        self.extra = C.wardrobe_roots(self.lv)

    def at(self, k):
        return self.frame[self.ents[k - 1]][1]

    def mname(self, o):
        m = self.p.u16(o, 0x12)
        return self.mat.insts[m].name if m in self.mat.insts else '?'

    def objects(self, root):
        return list(struct.unpack_from('<%dI' % self.p.u32(root, 0x14), self.p.chunks[self.p.u32(root, 0x18)]))

    def node(self, name):
        hit = [k for k in range(1, len(self.sc.nodes)) if self.sc.names[k] == name]
        if len(hit) != 1:
            raise KeyError('%d nodes named %s' % (len(hit), name))
        return hit[0]

    def put(self, k, pos=None, m9=None, model=None):
        """Node k: place, turn, model - .prp ZGEOM[2] / [1] / [4] and the .gms record, kept equal as in stock."""
        import kl_graft, kl_fa_author as au
        sc, e = self.sc, self.ents[k - 1]
        lab = J.labels('dd', sc.cls(k))
        def fn(us):
            if m9 is not None:
                au.setv(sc, us, lab.index('ZGEOM[1]'), [float(x) for x in m9])
            if pos is not None:
                au.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
            if model is not None:
                if us[lab.index('ZGEOM[4]')][0][0] != 0x09:
                    raise ValueError('%s: ZGEOM[4] is not a number' % sc.path[k])
                au.setv(sc, us, lab.index('ZGEOM[4]'), model)
        kl_graft.edit(sc.nodes[k], 'props', fn)
        if m9 is not None:
            e.rot = struct.pack('<9f', *m9) + e.rot[36:]
        if pos is not None:
            e.trans = struct.pack('<3f', *pos) + e.trans[12:]
        if model is not None:
            e.model = model

    def save(self, dst=None, log=print):
        """Write the members back: into the build's own archive (dst None) or as a copy in folder dst."""
        import kl_graft, kl_prmgraph as G, kl_texmat as T, shutil
        lv = self.lv
        prm = G.write(self.p)
        self.mat.refs = T.material_refs(prm)
        gms, buf = self.scene.write()
        lv['.prm'], lv['.MAT'], lv['.TEX'] = prm, T.write_mat(self.mat), T.write_tex(self.tex)
        lv['.gms'], lv['.buf'], lv['.prp'] = kl_gms.pack(gms), buf, self.sc.p.serialize()
        src = os.path.dirname(lv.src)
        if dst is None or os.path.abspath(dst) == os.path.abspath(src):
            tmp = lv.src + '.tmp'
            kl_graft.write_zip(tmp, [(n, lv.files[n]) for n in lv.order])
            os.replace(tmp, lv.src)
            return lv.src
        os.makedirs(dst, exist_ok=True)
        out = kl_graft.write_zip(os.path.join(dst, os.path.basename(lv.src)), [(n, lv.files[n]) for n in lv.order])
        for f in os.listdir(src):
            q = os.path.join(src, f)
            if os.path.isfile(q) and q != lv.src:
                shutil.copyfile(q, os.path.join(dst, f))
        return out


def _assets(E, src='level'):
    """Assets' readers on an open level."""
    a = Assets.__new__(Assets)
    a.p, a.mat, a.tex, a.src = E.p, E.mat, E.tex, src
    return a


def table(E):
    """The conference table of a level -> dict: node, world origin, top height, rim(x) = (z of the
    top's -z edge, of its +z edge) at world x or None beside the table, x range of the top."""
    k = E.node(TABLE)
    Rm, T = E.frame[E.ents[k - 1]]
    if [[round(v, 3) for v in r] for r in Rm] != [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
        raise ValueError('the table is turned: rim() reads its top in world axes')
    a = _assets(E)
    best = None
    for o in a.meshes(E.ents[k - 1].model):
        pos, _uv, tris = a.geometry(o)
        if not pos:
            continue
        hi = max(q[1] for q in pos)
        flat = [t for t in tris if min(pos[i][1] for i in t) > hi - 0.6]
        area = sum(abs((pos[b][0] - pos[a_][0]) * (pos[c][2] - pos[a_][2]) - (pos[c][0] - pos[a_][0]) * (pos[b][2] - pos[a_][2])) / 2 for a_, b, c in flat)
        if best is None or (hi > best[0] + 0.6) or (abs(hi - best[0]) <= 0.6 and area > best[1]):
            best = (hi, area, o, pos, flat)
    hi, _area, o, pos, flat = best
    def rim(x):
        lo, up = None, None
        for t in flat:
            P = [pos[i] for i in t]
            for i in range(3):
                p0, p1 = P[i], P[(i + 1) % 3]
                if (p0[0] + T[0] - x) * (p1[0] + T[0] - x) <= 0 and p0[0] != p1[0]:
                    z = p0[2] + (x - T[0] - p0[0]) / (p1[0] - p0[0]) * (p1[2] - p0[2]) + T[2]
                    lo, up = z if lo is None else min(lo, z), z if up is None else max(up, z)
        return None if lo is None else (lo, up)
    xs = [q[0] + T[0] for t in flat for q in (pos[i] for i in t)]
    return dict(k=k, at=T, top=T[1] + hi, rim=rim, x=(min(xs), max(xs)), mesh=o, material=E.mname(o))


def statues(E):
    """The samurai cases -> [dict: node of the '_Whole' model, its entity, world frame, model root]."""
    sc, out = E.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.names[k].endswith(CASE_WHOLE) and CASE_NODE in sc.names[sc.parent[k]]:
            e = E.ents[k - 1]
            out.append(dict(k=k, e=e, R=E.frame[e][0], at=E.frame[e][1], root=e.model))
    return out


def loot_nodes(E):
    """The layer's loot (top-level money objects that are not a drop pool) -> (the table, on the
    table [node], at a case [(node, case)], elsewhere [node]), by where they stand."""
    sc = E.sc
    tab, cases = table(E), statues(E)
    on, at, other = [], [], []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' in v[2] or sc.parent[k] != 0:
            continue
        p = E.at(k)
        r = tab['rim'](p[0])
        near = [c for c in cases if math.hypot(c['at'][0] - p[0], c['at'][2] - p[2]) < 60 and abs(c['at'][1] - p[1]) < 60]
        if r and r[0] - 80 <= p[2] <= r[1] + 80 and abs(p[1] - tab['top']) < 60:
            on.append(k)
        elif near:
            at.append((k, near[0]))
        else:
            other.append(k)
    return tab, on, at, other


def case_model(E, which, scale, log=print):
    """The briefcase joins the level's .prm (into dead chunk indices), .MAT and .TEX -> (model root,
    its bounds after scaling, the new material slots). A Dead Men model goes through the converters
    (kl_chars.Source = kl_prm / kl_mat / kl_tex, as kl_graft.DeadMen); its octree record is left
    behind (root +0x1c = 0: 597 drawn ZSTDOBJ of stock F07 have none, e.g. PC400_F07_Trash_G_03) -
    a bullet finds nothing to mark on the case."""
    import kl_chars as C, kl_prmgraph as G, kl_texmat as T
    level, root, _name = CASES[which]
    if level.startswith('M'):
        src = C.Source.get(level, log)
        sp, smat, stex = src.prm, src.mat, src.tex
    else:
        a = Assets.of(level)
        sp, smat, stex = a.p, a.mat, a.tex
    ex, cmap = G.extract(sp, [root])
    r = cmap[root]
    kinds, _args = G.walk(ex, [r])
    done = set()
    for i, kind in kinds.items():                       # the size goes into the copy's own vertices
        if kind == 'desc' and scale != 1.0:
            nv, vtx = ex.u32(i, 0), ex.u32(i, 4)
            if vtx in done or len(ex.chunks[vtx]) < VSTRIDE * nv:
                continue
            done.add(vtx)
            v = bytearray(ex.chunks[vtx])
            for j in range(nv):
                struct.pack_into('<3f', v, VSTRIDE * j, *(c * scale for c in struct.unpack_from('<3f', v, VSTRIDE * j)))
            ex.chunks[vtx] = bytes(v)
    c = bytearray(ex.chunks[r])
    struct.pack_into('<6f', c, 0x20, *(x * scale for x in struct.unpack_from('<6f', c, 0x20)))
    struct.pack_into('<I', c, 0x1c, 0)
    ex.chunks[r] = bytes(c)
    slots = {ex.u16(i, 0x12) for i, kind in kinds.items() if kind == 'mesh'}
    E.tex, tmap = T.merge_tex(E.tex, stex, set(T.used_textures(smat, slots)))
    before = set(E.mat.insts)
    E.mat, mmap = T.merge_mat(E.mat, smat, slots, tmap)
    n0 = len(E.p.chunks)
    E.p, cmap3 = G.append(E.p, ex, [r], mmap, None, tmap)
    new = cmap3[r]
    log('  kl_fa_loot: briefcase %s root %d (%s) -> chunk %d: %d chunks into dead indices, %d at the end; materials %s; size x %.2f' % (
        level, root, CASES[which][2], new, sum(v < n0 for v in cmap3.values()), sum(v >= n0 for v in cmap3.values()),
        sorted(E.mat.insts[mmap[s]].name.split('/')[-1] for s in slots), scale))
    return new, struct.unpack_from('<6f', E.p.chunks[new], 0x20), sorted(set(E.mat.insts) - before)


def suit_models(E, cases, log=print):
    """Per case model: a new root listing the armour's meshes (the chunks themselves are shared),
    and the case's own object table without them -> {case root: armour root}. Two new chunks per
    distinct case model, taken from the dead indices."""
    import kl_prmgraph as G
    p, out = E.p, {}
    remain = {}
    for c in cases:                                     # the bare stand's root: the form of a plain prop of this very object
        par = E.sc.parent[c['k']]
        k = next((j for j in range(par + 1, E.sc.end[par]) if E.sc.names[j].endswith(CASE_REMAIN)), None)
        remain[c['root']] = E.ents[k - 1].model if k else None
    for root in sorted({c['root'] for c in cases}):
        objs = E.objects(root)
        suit = [o for o in objs if any(w in E.mname(o) for w in SUIT)]
        rest = [o for o in objs if o not in suit]
        if not suit or not rest:
            raise ValueError('case model %d: armour meshes %r, others %r' % (root, suit, rest))
        tab = p.u32(root, 0x18)
        users = [i for i, ch in enumerate(p.chunks) if ch and len(ch) == 64 and ch[:4] == b'\0\1\7\0' and p.u32(i, 0x18) == tab]
        if users != [root]:
            raise ValueError('case model %d shares its object table with %r' % (root, users))
        pts = []
        for o in suit:
            d = p.u32(p.u32(o, 0x28), 0)
            v = p.chunks[p.u32(d, 4)]
            pts += [struct.unpack_from('<3f', v, VSTRIDE * j) for j in range(p.u32(d, 0))]
        base = remain[root] or root
        new_tab = G.new_chunk(p, struct.pack('<%dI' % len(suit), *suit) + bytes(-4 * len(suit) % 16))
        c = bytearray(p.chunks[base])                   # flags, prop chunk: those of the case's own '_Remain' (a plain prop)
        struct.pack_into('<II', c, 0x14, len(suit), new_tab)
        struct.pack_into('<I', c, 0x1c, 0)              # no octree record (as case_model)
        struct.pack_into('<6f', c, 0x20, *([min(q[a] for q in pts) for a in range(3)] + [max(q[a] for q in pts) for a in range(3)]))
        struct.pack_into('<II', c, 0x38, 0, 0)
        new = G.new_chunk(p, bytes(c))
        p.chunks[tab] = struct.pack('<%dI' % len(rest), *rest) + bytes(-4 * len(rest) % 16)
        c = bytearray(p.chunks[root]); struct.pack_into('<I', c, 0x14, len(rest)); p.chunks[root] = bytes(c)
        out[root] = new
        log('  kl_fa_loot: case model %d keeps %d objects (frame, glass, hull); the armour (%s, %d vertices) is model %d' % (
            root, len(rest), ', '.join(sorted({E.mname(o).split('/')[-1] for o in suit})), len(pts), new))
    return out


def lighten_first(E, log=print):
    """kl_graft's 'lighten' (trim, slim) on the open level, when it still has dead model roots.
    It has to come BEFORE the dead chunk indices are handed out: G.reuse() turns every dead chunk
    into a stub, and 'slim' finds the textures only the removed map shows by walking its dead model
    roots (kl_prmgraph.reuse's own warning). Seen: a level dressed first came out of 'lighten' with
    '0 dead model roots ... 0 shrunk' and a 337 MB archive instead of 212. A level lightened before
    has no dead root left and is not touched. -> lighten()'s report or None."""
    import kl_graft, kl_prmgraph as G, kl_texmat as T
    live = kl_graft.live_roots(E.sc, G.gms_roots(E.raw)) + [(r, 'root') for r in E.extra]
    if not kl_graft.dead_assets(E.p, E.mat, E.tex, live, kl_graft.hud_textures(E.sc))['roots']:
        return None
    prm, tex, r = kl_graft.lighten(E.lv['.prm'], E.lv['.TEX'], E.lv['.MAT'], live, kl_graft.hud_textures(E.sc),
                                   kl_graft.load_options('trim,slim'), log)
    E.lv['.prm'], E.lv['.TEX'] = prm, tex
    E.p, E.tex = G.read(prm, 'dd'), T.read_tex(tex)
    return r


def dress(folder, dst=None, log=print):
    """The loot's props and places on a built level (a folder with <slot>_Main.zip; written in place
    or as a copy in dst) -> report dict. A level dressed before is left as it is. The level is
    lightened first if it has not been (lighten_first)."""
    import kl_chars as C, kl_light, kl_texmat as T, kl_fa_author as au
    from kl_port_check import workdir
    E = Edit(folder)
    sc = E.sc
    tab, on, at, other = loot_nodes(E)
    bag = {E.ents[k - 1].model for k in on + [k for k, _c in at]}
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    if not bag <= pool:
        log('  kl_fa_loot: %s: the loot already shows models of its own (%s): nothing done' % (folder, sorted(bag - pool)))
        return dict(done=False)
    n0 = len(E.p.chunks)
    light = lighten_first(E, log)
    C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
    rep = dict(done=True, table=[], statues=[], chunks=(n0, n0), other=[sc.names[k] for k in other], lightened=light)
    # ---- the boardroom: six on the table, a row along each long rim, a case each
    new_slots, case_root, box = [], None, None
    if CASE:
        scale = CASE_SCALE if CASE_SCALE is not None else CASE_SCALES[CASE]
        case_root, _box, new_slots = case_model(E, CASE, scale, log)
        lo3, hi3 = _assets(E).bounds(case_root)         # of what is drawn (Dog Days' root box is wider than its one mesh)
        box = lo3 + hi3
    inset = (RIM * scale / CASE_SCALES['dm'] if CASE == 'dm' else RIM) if CASE else RIM_BAG
    cols = collections.defaultdict(list)
    for k in on:
        cols[round(E.at(k)[0])].append(k)
    for ci, x in enumerate(sorted(cols)):
        ks = sorted(cols[x], key=lambda k: E.at(k)[2])
        if len(ks) != 2:
            raise ValueError('the table has %d stacks at x %d, not one for each side' % (len(ks), x))
        lo, up = tab['rim'](x)
        for side, k in ((-1, ks[0]), (1, ks[1])):       # -1: the -z rim, the left one from the balcony
            yaw = (0.0 if side < 0 else 180.0) + side * CASE_YAW[ci % len(CASE_YAW)] if CASE else None
            z = (lo + inset) if side < 0 else (up - inset)
            was = E.at(k)
            if CASE == 'dd':                            # its geometry lies off its origin: the node goes where the case's middle
                cx, cz = (box[0] + box[3]) / 2, (box[2] + box[5]) / 2      # then is `inset + half its depth` in from the rim
                c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
                zc = (lo + inset + (box[5] - box[2]) / 2) if side < 0 else (up - inset - (box[5] - box[2]) / 2)
                pos = (x - (cx * c + cz * s), tab['top'] - box[1], zc - (-cx * s + cz * c))    # and its underside on the top
            else:
                pos = (float(x), tab['top'], z)
            E.put(k, pos, yaw9(yaw) if CASE else None, case_root)
            kl_fa.edit(sc, k, au.ctrl_of(sc, k, 'TriggerBox2'), lambda us: au.setv(sc, us, 2, ROOM_REACH))
            rep['table'].append(dict(name=sc.names[k], was=[round(v) for v in was], now=[round(v, 1) for v in pos], side='left' if side < 0 else 'right',
                                     rim=round(lo if side < 0 else up, 1), yaw=yaw, model=case_root or E.ents[k - 1].model))
    # ---- the statues: the armour itself
    if STATUE == 'suit' and at:
        suits = suit_models(E, [c for _k, c in at], log)
        for k, c in at:
            E.put(k, c['at'], m9_of(c['R']), suits[c['root']])
            rep['statues'].append(dict(name=sc.names[k], at=[round(v) for v in c['at']], model=suits[c['root']], case=sc.path[c['k']][5:]))
    rep['chunks'] = (n0, len(E.p.chunks))
    if len(E.p.chunks) != n0:
        raise ValueError('the chunk table grew from %d to %d: not enough dead indices' % (n0, len(E.p.chunks)))
    if new_slots:                                       # a material without a compiled shader is not drawn
        fxc = E.lv['.fxc']
        upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
        if os.path.isfile(upath):
            fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
        fit = kl_light.fit_shaders(E.mat, fxc, slots=new_slots, log=log)
        E.lv['.fxc'] = fxc
        rep['shaders_fitted'] = {E.mat.insts[s].name: v[1] for s, v in fit['fixed'].items()}
        rep['shaders_missing'] = [v[0] for v in fit['unresolved'].values()]
        if rep['shaders_missing']:
            raise ValueError('no compiled shader for %s' % rep['shaders_missing'])
    path = E.save(dst, log)
    log('  kl_fa_loot: %s: %d on the table (%s, radius %g, %d from the rim), %d at the samurai cases (%s); chunk table %d entries, as before' % (
        path, len(rep['table']), 'briefcases' if CASE else 'bags', ROOM_REACH, inset, len(at),
        'the armour itself' if STATUE == 'suit' else 'bags', n0))
    return rep


# ------------------------------------------------------------------ reading a dressed level back
def check(folder, log=print):
    """A built level's loot against what it must be -> [problems]. Every loot object: its model is
    a model root with vertex data, the .gms record and the .prp agree on it, every material of it
    has a compiled shader; a stack on the table lies on the table top inside its rim; the armour
    is drawn once (by the loot or by the case, not both) and stands in its case; every stack can
    be taken (survey: the read pick-up test from a place the walk test reaches, with MARGIN to
    spare); the chunk table is inside kl_impact's limit."""
    import kl_light, kl_impact
    E = Edit(folder)
    sc, bad = E.sc, []
    tab, on, at, other = loot_nodes(E)
    lab = lambda k: J.labels('dd', sc.cls(k))
    A = _assets(E, folder)
    slots = set()
    for k in on + [k for k, _c in at] + other:
        e = E.ents[k - 1]
        v = kl_fa.node_values(sc, k)
        if v[lab(k).index('ZGEOM[4]')] != e.model:
            bad.append('%s: .prp model %s, .gms model %d' % (sc.names[k], v[lab(k).index('ZGEOM[4]')], e.model))
        c = E.p.chunks[e.model] if 0 < e.model < len(E.p.chunks) else b''
        if len(c) != 64 or c[:4] != b'\0\1\7\0':
            bad.append('%s: model %d is not a model root' % (sc.names[k], e.model)); continue
        ms = A.meshes(e.model)
        if not ms or any(not A.geometry(o)[0] for o in ms):
            bad.append('%s: model %d has a mesh without vertex data' % (sc.names[k], e.model))
        slots |= {E.p.u16(o, 0x12) for o in ms}
        if [round(a, 3) for a in struct.unpack('<9f', e.rot[:36])] != [round(a, 3) for a in v[lab(k).index('ZGEOM[1]')]] or \
                [round(a, 2) for a in struct.unpack('<3f', e.trans[:12])] != [round(a, 2) for a in v[lab(k).index('ZGEOM[2]')]]:
            bad.append('%s: .prp and .gms disagree on its place' % sc.names[k])
    lack = kl_light.missing_shaders(E.mat, E.lv['.fxc'], sorted(slots))
    for s, l in lack.items():
        bad.append('material %s of a loot model has no compiled shader (%s)' % (E.mat.insts[s].name, l[:2]))
    for k in on:                                        # on the table: the model's footprint inside the top
        e, p = E.ents[k - 1], E.at(k)
        Rm = E.frame[e][0]
        b = A.bounds(e.model)
        for cx, cz in ((b[0][0], b[0][2]), (b[0][0], b[1][2]), (b[1][0], b[0][2]), (b[1][0], b[1][2])):
            wx, wz = p[0] + Rm[0][0] * cx + Rm[0][2] * cz, p[2] + Rm[2][0] * cx + Rm[2][2] * cz
            r = tab['rim'](wx)
            if not r or not r[0] <= wz <= r[1]:
                bad.append('%s: a corner of its model at (%d, %d) is off the table top%s' % (sc.names[k], wx, wz, ' (z %d..%d there)' % r if r else '')); break
        if abs(p[1] + b[0][1] - tab['top']) > 3:
            bad.append('%s: its underside is at y %.1f, the table top at %.1f' % (sc.names[k], p[1] + b[0][1], tab['top']))
    for k, c in at:
        suit_here = [o for o in E.objects(c['root']) if any(w in E.mname(o) for w in SUIT)]
        mine = [o for o in E.objects(E.ents[k - 1].model) if any(w in E.mname(o) for w in SUIT)]
        if mine and suit_here:
            bad.append('%s: the armour is drawn twice (loot model %d and case model %d)' % (sc.names[k], E.ents[k - 1].model, c['root']))
        if mine and math.dist(E.at(k), c['at']) > 1:
            bad.append('%s: the armour stands %d from its case' % (sc.names[k], math.dist(E.at(k), c['at'])))
    for c in statues(E):                                # a case without its armour and without loot that shows it
        if not any(o for o in E.objects(c['root']) if any(w in E.mname(o) for w in SUIT)) and not any(cc is c or cc['k'] == c['k'] for _k, cc in at):
            bad.append('%s: its model has no armour and no loot stands in it' % sc.path[c['k']][5:])
    if other:
        bad.append('loot that is neither on the table nor at a case: %s' % [sc.names[k] for k in other])
    bad += kl_impact.chunk_limit(E.lv['.prm'])
    for r in survey(E.lv.src, lambda *_a: None):
        if r['radius'] is not None and (r['stand'] is None or r['radius'] + REACH_PAD - r['h'] < MARGIN):
            bad.append('%s: %s' % (r['name'], r['why']))
    log('kl_fa_loot.check %s: %d on the table, %d at cases; problems: %d' % (folder, len(on), len(at), len(bad)))
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


def sketch(src, before=None, log=print):
    """Top view of the boardroom as the heisters see it from the balcony: the balcony below the
    page, looking up it (-x), so left on the page is left in the game (-z). One cell = 40 x 40.
    # table top, . a place a player can stand (walk test, a body's width from anything),
    capital letters = loot of `src`, small ones = of `before` (where it stood)."""
    lv = Built(src)
    inroom = lambda r: 4300 < r['at'][0] < 5600 and -500 < r['at'][2] < 300 and 20900 < r['at'][1] < 21300
    rows = sorted([r for r in loot(lv) if inroom(r)], key=lambda r: (r['at'][0], r['at'][2]))
    old = sorted([r for r in loot(Built(before)) if inroom(r)], key=lambda r: (r['at'][0], r['at'][2])) if before else []
    f, seen, _b = walk(lv, (4200.0, 6300.0, -1200.0, 1000.0), log=lambda *_a: None)
    tab = table(Edit(os.path.dirname(lv.path)))
    C_ = 40
    zs = list(range(-480, 280, C_))
    log('boardroom from the balcony (the balcony is below this picture; up = -x, into the room; LEFT = -z, as in the game)')
    log('         z %d%s%d' % (zs[0], ' ' * (len(zs) - 9), zs[-1] + C_))
    marks = {}
    for i, r in enumerate(old):
        marks[int(r['at'][0] // C_), int(r['at'][2] // C_)] = 'abcdefghij'[i]
    for i, r in enumerate(rows):
        marks[int(r['at'][0] // C_), int(r['at'][2] // C_)] = 'ABCDEFGHIJ'[i]
    for x in range(4400, 5480, C_):
        line = ''
        for z in zs:
            cx, cz = x + C_ / 2, z + C_ / 2
            r = tab['rim'](cx)
            ch = marks.get((x // C_, z // C_))
            if not ch:
                if r and r[0] <= cz <= r[1]:
                    ch = '#'
                elif any(f.clear(seen, f.w.cell(cx + dx, cz + dz), y) for dx in (-10, 10) for dz in (-10, 10) for y in seen.get(f.w.cell(cx + dx, cz + dz), ())):
                    ch = '.'
                else:
                    ch = ' '
            line += ch
        log('  x %5d  %s' % (x, line))
    log('                    [ window x 5850, balcony, spawn x 6000 ]')
    for title, rs, names in (('now   ', rows, 'ABCDEFGHIJ'), ('before', old, 'abcdefghij')):
        for i, r in enumerate(rs):
            s = ''
            if title.startswith('now'):
                place, h, _n = f.stand(seen, r['at'], r['radius'])
                s = ': stand at (%d, %d), %d away, reach %d' % (place[0], place[2], h, r['radius'] + REACH_PAD) if place else ': OUT OF REACH'
            log('  %s %s %-18s (%5d %5d %5d) radius %g, model %d%s' % (names[i], title, r['name'][-18:], *r['at'], r['radius'], r['model'], s))


# ------------------------------------------------------------------ every case prop of both games
CASE_WORDS = r'briefcase|suitcase|alu_case|attache'


def props(out=None, log=print):
    """Every case / briefcase / suitcase model of both games' levels (entity names matching
    CASE_WORDS, with a model) -> [(game, model name, [levels], level and root of the picture)];
    with `out` one PNG per prop (four views) in that folder."""
    import glob, re
    found = collections.OrderedDict()
    for game, base in (('dd', J.find(J.DD_GUESSES, J.DD_EXE)), ('dm', J.find(J.DM_GUESSES, J.DM_EXE))):
        levels = sorted({os.path.basename(os.path.dirname(q)) for root in (base, os.path.join(base, 'KL_PortBackup'))
                         for q in glob.glob(os.path.join(root, 'Scenes', 'Locations', '*', '*_Main.zip'))})
        for lv in levels:
            with zipfile.ZipFile(J.level_zip(lv, game)) as z:
                m = {n.rsplit('ain', 1)[1].lower(): n for n in z.namelist() if 'ain.' in n}
                scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
            for e in scene.entities():
                name = e.name.decode('latin1')
                if e.model and re.search(CASE_WORDS, name, re.I) or (e.model and e.parent is not None and re.search(r'alu_case|^briefcase', e.parent.name.decode('latin1'), re.I)):
                    key = (game, re.sub(r'(_\d+|#\d+)+$', '', name.split('!')[-1]))
                    found.setdefault(key, [[], lv, e.model, name])[0].append(lv)
    rows = []
    for (game, name), (lvs, lv, root, full) in found.items():
        rows.append((game, name, sorted(set(lvs)), lv, root))
        a = Assets.of(lv)
        try:
            what = a.describe(root)
        except ValueError:
            continue
        log('%s %-34s %-28s %s root %d: %s' % (game, name, ' '.join('%s x%d' % (l, lvs.count(l)) for l in sorted(set(lvs))), lv, root, what))
        if out and a.bounds(root):
            os.makedirs(out, exist_ok=True)
            picture(os.path.join(out, '%s_%s_%s.png' % (game, lv, re.sub(r'\W+', '_', name))), [[(a, root, None)]], 240)
    return rows


# ------------------------------------------------------------------ in the build
def finish(folder, log=print):
    """What kl_fa_author / kl_fa_blast call on the written level (au.FINISH): dress it in place and
    read it back -> [problems]."""
    dress(folder, None, log)
    return check(folder, log)


def hook():
    """Put this layer into kl_fa_author's builds, once: after the level is written, finish()."""
    import kl_fa_author as au
    if finish not in au.FINISH:
        au.FINISH.append(finish)


def test(out, log=print, wardrobe=True):
    """The level the owner plays, with the loot's props: the full layer (kl_fa_blast.test: author +
    street + blast, and this file through au.FINISH) built into <out>, with the voices on as the
    play builds had them (kl_snd.VOICE); then kl_graft's 'lighten' into <out>\\light and kl_chars'
    wardrobe into <out>\\retomoto_loot; every check on the final folder. -> 0 or 1.
    ('lighten' finds nothing left to do: dress() has to lighten before it takes dead chunk indices.
    The step stays so that the order of the play builds is the order here.)"""
    import glob, shutil, subprocess, kl_snd, kl_graft
    import kl_fa_blast as bl
    kl_snd.VOICE = True
    hook()
    rc = bl.test(out, True, log)
    built = glob.glob(os.path.join(out, 'R09+M09_A*'))
    if rc or len(built) != 1:
        log('kl_fa_loot: the build failed (%s)' % rc)
        return 1
    join = os.path.join(os.path.dirname(HERE), 'klhook', 'KLJoin.retomoto.ini')     # the hook's box for the tower's car:
    if os.path.isfile(join) and not os.path.isfile(os.path.join(built[0], 'KLJoin.ini')):   # it travels beside the archive
        shutil.copyfile(join, os.path.join(built[0], 'KLJoin.ini'))
    light, final = os.path.join(out, 'light'), os.path.join(out, 'retomoto_loot')
    kl_graft.relight(built[0], light, kl_graft.load_options('trim,slim'), log)
    if wardrobe:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'kl_chars.py'), 'wardrobe', light, final], capture_output=True, text=True)
        log(r.stdout[-3000:] + r.stderr[-2000:])
        if r.returncode:
            log('kl_fa_loot: kl_chars wardrobe: exit %d' % r.returncode)
            return 1
    else:
        final = light
    return 1 if final_checks(final, log) else 0


def final_checks(final, log=print):
    """Every check there is on a finished folder -> number of problems."""
    import subprocess, kl_impact, kl_chars
    archive = os.path.join(final, 'F01_Main.zip')
    bad = check(final, log)
    fa = [f for f in kl_fa.check(*kl_fa.load(archive)) if f.sev <= kl_fa.BROKEN]
    log('kl_fa.check: %d CRASH / BROKEN' % len(fa))
    for f in fa:
        log('  ' + str(f)[:240])
    imp = kl_impact.check(archive)
    log('kl_impact.check (bones, chunk limit, surfaces): problems: %d' % len(imp))
    for b in imp:
        log('  ' + b[:240])
    und = kl_chars.undrawn(kl_chars.Lv(final))
    log('kl_chars.undrawn: %d' % len(und))
    for b in und:
        log('  ' + b[:240])
    r = subprocess.run([sys.executable, os.path.join(HERE, 'kl_arms.py'), 'check', archive], capture_output=True, text=True)
    log('kl_arms check: exit %d; %s' % (r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]))
    for f in ('KLJoin.ini', 'KLWardrobe.ini'):
        log('%s: %s' % (f, 'there' if os.path.isfile(os.path.join(final, f)) else 'MISSING'))
    n = len(bad) + len(fa) + len(imp) + len(und) + (1 if r.returncode else 0)
    log('RESULT: %s (%s)' % ('PASS' if not n else 'FAIL', final))
    return n


def options(a):
    """The knobs from a command line (removed from it): --case dm|dd|bag, --case-scale X,
    --statue suit|bag, --room-reach R, --loot-bags (everything as it was but the places)."""
    global CASE, CASE_SCALE, STATUE, ROOM_REACH
    def take(name):
        if name in a:
            i = a.index(name)
            v = a[i + 1]
            del a[i:i + 2]
            return v
    v = take('--case')
    if v is not None:
        CASE = None if v == 'bag' else v
    v = take('--case-scale')
    if v is not None:
        CASE_SCALE = float(v)
    v = take('--statue')
    if v is not None:
        STATUE = None if v == 'bag' else v
    v = take('--room-reach')
    if v is not None:
        ROOM_REACH = float(v)
    if '--loot-bags' in a:
        a.remove('--loot-bags')
        CASE = STATUE = None
    if CASE not in (None,) + tuple(CASES) or STATUE not in (None, 'suit'):
        raise SystemExit('--case dm | dd | bag, --statue suit | bag')
    return a


def main():
    a = options(sys.argv[1:])
    if len(a) == 2 and a[0] == 'survey':
        survey(a[1])
    elif len(a) in (2, 3) and a[0] == 'sketch':
        sketch(*a[1:])
    elif len(a) in (1, 2) and a[0] == 'props':
        props(*a[1:])
    elif len(a) >= 4 and a[0] == 'picture':
        A = Assets.of(a[1])
        for r in a[3:]:
            print('%s root %s: %s' % (a[1], r, A.describe(int(r))))
        print(picture(a[2], [[(A, int(r), None)] for r in a[3:]]))
    elif len(a) == 3 and a[0] == 'dress':
        dress(a[1], a[2])
        sys.exit(1 if check(a[2]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if final_checks(a[1]) else 0)
    elif len(a) >= 2 and a[0] == 'test':
        sys.exit(test(a[1], wardrobe='--no-wardrobe' not in a))
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_loot                   # one module: kl_fa_author's FINISH holds this module's finish()
    kl_fa_loot.main()
