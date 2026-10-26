#!/usr/bin/env python3
r"""
FLOOR + NAV CHECK OF THE COVER BOXES OF A FINISHED MAP (2026-10-26). OFFLINE and READ ONLY: reads map zips, writes only a JSON report when asked.

    python kl_cover_floornav.py scan <zip> [<zip> ...] [--json out.json] [--bad]   per-map counts (--bad: list the failing boxes)
    python kl_cover_floornav.py live [--maps DM05A,DD01,...] [--json out.json] [--bad]
                                    the same for every <DD>\\KLExpansion\\Maps\\<MAP>\\F01_Main.zip (read only)
    (library)  check(L) -> {node: rec}   with L = kl_cover_add.Lite(zip) after kl_cover_add.use_slot(zip)

WHY (DM05A live 4a6799a1, scratch audit 2026-10-26): 25 of 93 KL_CoverSix! boxes were bad although kl_cover_vet (side blocked / raised) passed
them: 23 had NO collision floor near the plan ground at the stand point (box front, where the player stands to take cover), 11 had no nav
mesh in front (the player's tele / cover move snapped onto an overhead poly), 18 more had nav in front but in a nav part no spawn reaches.
kl_cover_vet looks for walls and raised floors AT the box; this tool asks the other question: is there a FLOOR and a WALKABLE MESH there?

PER BOX, per side (the stand point = the side's middle + STAND_OUT outward in the plan, at the box's floor height = the 'ground'):
  floor : a collision floor (an up-facing triangle, kl_fa_cover.Solid.floor) within FLOOR_TOL of the ground at the stand point.
  nav   : a nav poly of the map's mesh within NAV_R (plan distance) of the stand point whose height is within NAV_DY (80) of the ground
          (same floor; sampled on the stand point and rings of radius NAV_R/3, 2NAV_R/3, NAV_R).
  reach : that poly is in a nav part that a ZSpawnPoint of the map stands on (Nav.part with links=True: neighbours and the mesh's drop links; ladders/vaults are not in the mesh).
A box is GOOD when floor + nav + reach hold at its PLAYER SIDE. The zip does not record which side of a KL_CoverSix (tag _K6_) box is its front
(the clone form's local axis for it varies: checked against cover_plan.json, local +z / -x by form and the bb centre does not tell the sign), so the
front comes from the staging plan: `load_plan` finds <MAP>\stage\cover_plan.json (C:\kl_build_1024\cover_1026b, then cover_1026) and a K6 box whose
name AND middle match the plan (2 units) is judged at the side facing the plan's face_normal ('planned'). Any other box (stock, older, K6 with no
matching plan) has no known front (the game takes cover on any side): it is GOOD when at least one of its four sides passes. `all4` counts boxes
whose four sides all pass, `any_side` boxes with at least one passing side.

CALIBRATION (the baseline run on stock boxes, `live`): the tolerances below were set so that the map's own stock cover (tag 'stock' = name without
_K6_ / _KL_ / _KM_) passes nearly always; a stock box failing means the test is too strict, not that the box is bad. Numbers are in the report.
GUESSES: STAND_OUT / FLOOR_TOL / NAV_R / NAV_DY (the cover movement's exact stand place and the mesh's snap range are NOT read from the exe);
a movable crate has no static collision floor but the floor under it is read; a roof over the stand point is not a problem (nearest floor to ground).
"""
import collections, glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F
import kl_fa_cover as C
import kl_cover_vet as V

STAND_OUT = 10.0     # GUESS: how far outside a side the stand point is (the scratch audit used 1 for the K6 plan's own stand point)
FLOOR_TOL = 30.0     # collision floor within this of the ground at the stand point (the scratch audit: 15 for K6; calibrated on stock below)
NAV_R = 60.0         # a nav poly within this plan distance of the stand point (owner/job brief: ~60)
NAV_DY = 80.0        # ... whose height is within this of the ground (same floor). CALIBRATED: Dead Men meshes lie 40..80 UNDER the collision floor (DM09 stock: 180 of 470 boxes), Dog Days' within 20
PLAY_R = 300.0       # a box is IN PLAY when the mesh of a spawn nav part lies within this plan distance of the box middle (200 in height)
CELL = 256.0         # grid of the nav index


class NavIndex:
    """Grid over a kl_fa_bots.Nav: polys by bbox cell, so a lookup does not scan the whole mesh."""

    def __init__(self, nav, part=None):
        self.nav = nav
        self.part = part or nav.part
        self.g = collections.defaultdict(list)
        for i, b in enumerate(nav.box):
            if not nav.ok[i]:
                continue
            for cx in range(int(b[0] // CELL), int(b[1] // CELL) + 1):
                for cz in range(int(b[2] // CELL), int(b[3] // CELL) + 1):
                    self.g[cx, cz].append(i)

    def at(self, x, y, z, dy, parts=None):
        """(poly, height) under (x, z) nearest to y within dy, like Nav.at; of the nav `parts` only when given."""
        nav, best = self.nav, None
        for i in self.g.get((int(x // CELL), int(z // CELL)), ()):
            b = nav.box[i]
            if b[0] <= x <= b[1] and b[2] <= z <= b[3] and (parts is None or self.part[i] in parts) and nav.inside(i, x, z):
                h = nav.height(i, x, z)
                if abs(h - y) <= dy and (best is None or abs(h - y) < abs(best[1] - y)):
                    best = (i, h)
        return best


    def near_play(self, mid, parts):
        """True when the mesh of one of `parts` lies under a sample within PLAY_R of the box middle (rings of 100; the box is in the area the players walk)."""
        for r in (0.0, 100.0, 200.0, PLAY_R):
            for a in range(1 if r == 0 else 8):
                t = a * math.pi / 4
                res = self.at(mid[0] + r * math.cos(t), mid[1], mid[2] + r * math.sin(t), 200.0, parts)
                if res is not None:
                    return True
        return False


def spawn_parts(L, NI):
    """({nav part: spawn count}, n spawn points, n off the mesh). A spawn is put on the poly nearest its height within 80, else the nearest poly middle within 250."""
    sc, nav = L.B.sc, L.nav
    parts, n, off = collections.Counter(), 0, 0
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZSpawnPoint':
            continue
        p = L.B.at(k)
        n += 1
        r = NI.at(p[0], p[1], p[2], 120.0)
        if r is None:
            best = None
            for i in range(len(nav.pv)):
                if nav.ok[i] and abs(nav.mid[i][1] - p[1]) < 150:
                    d = math.hypot(nav.mid[i][0] - p[0], nav.mid[i][2] - p[2])
                    if d < 250 and (best is None or d < best[0]):
                        best = (d, i)
            if best is None:
                off += 1
                continue
            r = (best[1], 0)
        parts[NI.part[r[0]]] += 1
    return parts, n, off


def _stand_nav(NI, p, g):
    """The nav poly (poly, height) near the stand point p = (x, z): the one on the stand point or the nearest sample within NAV_R at the ground g, or None."""
    pts = [(0.0, p)]
    for r in (NAV_R / 3, 2 * NAV_R / 3, NAV_R):
        for a in range(8):
            t = a * math.pi / 4
            pts.append((r, (p[0] + r * math.cos(t), p[1] + r * math.sin(t))))
    for r, q in pts:                                   # nearest ring first (pts are ordered by radius)
        res = NI.at(q[0], g, q[1], NAV_DY)
        if res is not None:
            return res
    return None


def side_test(L, NI, mid_y, sd, parts):
    """sd = (side name, side middle xz, outward unit xz) -> {'floor': delta or None, 'nav': delta or None, 'part': nav part or None, 'ok': bool, 'why': [..]}."""
    nm, m, d = sd
    p = (m[0] + d[0] * STAND_OUT, m[1] + d[1] * STAND_OUT)
    f = L.solid.floor(p[0], mid_y, p[1], reach=FLOOR_TOL)
    nv = _stand_nav(NI, p, mid_y)
    why = []
    if f is None:
        why.append('nofloor')
    if nv is None:
        why.append('nonav')
    elif parts and NI.part[nv[0]] not in parts:
        why.append('unreach')
    return {'side': nm, 'stand': [round(p[0], 1), round(mid_y, 1), round(p[1], 1)], 'floor': None if f is None else round(f - mid_y, 1),
            'nav': None if nv is None else round(nv[1] - mid_y, 1), 'part': None if nv is None else NI.part[nv[0]], 'ok': not why, 'why': why}


STOCK_PART_MIN = 3   # GUESS: a nav part no ZSpawnPoint stands on still counts as walked when at least this many of the map's own stock cover boxes stand in it


class Ground:
    """The floor + nav test of ONE planned cover tile, for the placement filter in kl_cover_1026 (same tolerances as check(): STAND_OUT / FLOOR_TOL / NAV_R / NAV_DY, all GUESSes above).
    L = kl_cover_add.Lite of the map WITHOUT its KL_CoverSix! group. The reach rule: a tile whose nav part is in none that a spawn stands on is DROPPED,
    unless the map's own stock boxes (tag 'stock') stand in that part too (>= STOCK_PART_MIN of them: the part is walked in the original game's cover design)."""

    def __init__(self, L, log=print):
        lk = F.Nav(L.B.scene.nav, links=True)
        self.L, self.NI = L, NavIndex(L.nav, lk.part)
        sp, n_sp, off = spawn_parts(L, self.NI)
        self.reach = set(sp)
        self.stock = collections.Counter()
        for b in L.boxes:
            if b.get('kind') is None or b.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ' or tag_of(b['name']) != 'stock':
                continue
            sd = V.sides(L.B, b)
            if sd is None:
                continue
            mid, ss, _size = sd
            for s in ss:                                  # the box counts once, in the part of its first side with floor + nav (reach not asked)
                r = side_test(L, self.NI, mid[1], s, None)
                if r['ok']:
                    self.stock[r['part']] += 1
                    break
        self.kept = collections.Counter()
        log('floornav: %d spawns (off the mesh %d) on nav parts %s; stock boxes per part %s' % (n_sp, off, sorted(self.reach), dict(self.stock)))

    def tile_bad(self, side_mid, n, y):
        """Reason string when the stand point in front of the tile's face (side middle + STAND_OUT along n, at the ground y) has no collision floor, no nav, or
        a nav part nobody reaches (and no stock cover in it), else None."""
        r = side_test(self.L, self.NI, y, ('front', side_mid, n), None)
        if r['floor'] is None:
            return 'no collision floor at the stand point'
        if r['nav'] is None:
            return 'no nav mesh in front'
        p = r['part']
        if self.reach and p not in self.reach:
            if self.stock[p] < STOCK_PART_MIN:
                return 'nav part no spawn reaches (%d stock boxes there)' % self.stock[p]
            self.kept['unreach kept: %d stock boxes in the part' % self.stock[p]] += 1
        return None


def load_plan(map_name, zp=None):
    """{box name: [plan entries]} of the staged cover_plan.json files for the map, newest root first (cover_1026b, then cover_1026); {} when none.
    A list per name: a restaged map reuses the names K6_01.. with other middles, and the old live boxes must still find their own entry (the middle decides)."""
    out = {}
    for root in (r'C:\kl_build_1024\cover_1026b', r'C:\kl_build_1024\cover_1026'):
        f = os.path.join(root, map_name, 'stage', 'cover_plan.json')
        if os.path.isfile(f):
            with open(f) as fh:
                for p in json.load(fh):
                    if p.get('name'):
                        out.setdefault(p['name'], []).append(p)
    return out


def tag_of(name):
    return 'K6' if '_K6_' in name else 'KL' if '_KL_' in name else 'KM' if '_KM_' in name else 'stock'


def check(L, plan=None, log=print):
    """plan = {box name: [cover_plan.json entries]} (load_plan) -> {'boxes': {node: rec}, 'spawn_parts': {...}, 'n_spawns': n}. rec: name, tag, mid, ground, ok (player side / best side), all4, sides {name: side_test}."""
    B = L.B
    plan = plan or {}
    # reachability by the mesh's neighbours AND its drop links (Nav links=True: a one-way drop joins two parts for this labelling, like Nav.part does)
    lk = F.Nav(L.B.scene.nav, links=True)
    NI = NavIndex(L.nav, lk.part)
    sp, n_sp, off = spawn_parts(L, NI)
    big = {p for p, _c in sp.items()}
    log('  spawns %d (off the mesh %d) on nav parts %s' % (n_sp, off, {p: (c, lk.part_size[p]) for p, c in sp.items()}))
    out = {}
    for b in L.boxes:
        if b.get('kind') is None or b.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ':
            continue
        sd = V.sides(B, b)
        if sd is None:
            continue
        mid, ss, size = sd
        g = mid[1]                                   # the box floor in the world (V.sides puts the middle on the model box's floor)
        res = {s[0]: side_test(L, NI, g, s, big) for s in ss}
        tag = tag_of(b['name'])
        front = None
        pl = next((q for q in plan.get(b['name'], ()) if abs(q['mid'][0] - b['mid'][0]) < 2 and abs(q['mid'][2] - b['mid'][2]) < 2), None)
        if tag == 'K6' and pl:
            n = pl['face_normal']                      # the planned free side: the side facing along the plan's face normal
            front = next((s[0] for s in ss if s[2][0] * n[0] + s[2][1] * n[1] > 0.9), None)
        if front is not None:
            ok = res[front]['ok']
        else:                                          # stock / older box / K6 without a matching plan: any side
            front = next((n for n, r in res.items() if r['ok']), None)
            ok = front is not None
        out[b['node']] = {'name': b['name'], 'tag': tag, 'mid': [round(v, 1) for v in mid], 'ground': round(g, 1), 'play': NI.near_play(mid, big), 'ok': ok, 'side': front, 'planned': front is not None and tag == 'K6' and pl is not None,
                          'all4': all(r['ok'] for r in res.values()), 'any': any(r['ok'] for r in res.values()), 'sides': res}
    return {'boxes': out, 'spawn_parts': {str(k): v for k, v in sp.items()}, 'n_spawns': n_sp}


def _failside(r):
    """The side that explains a failing box: its front when it has one, else the side with the fewest failed tests."""
    if r.get('side') and r['side'] in r['sides']:
        return r['sides'][r['side']]
    return min(r['sides'].values(), key=lambda v: len(v['why']))


def summary(rep, label='', log=print):
    """One line per tag: boxes, good, and why the rest fail (first failing reason at the player side / best side)."""
    rows = {}
    for tag in ('stock', 'KL', 'KM', 'K6'):
        bs = [r for r in rep['boxes'].values() if r['tag'] == tag]
        if not bs:
            continue
        why = collections.Counter()
        for r in bs:
            if not r['ok']:
                s = _failside(r)
                for w in s['why']:
                    why[w] += 1
        pl = [r for r in bs if r['play']]
        rows[tag] = {'boxes': len(bs), 'good': sum(r['ok'] for r in bs), 'play': len(pl), 'good_play': sum(r['ok'] for r in pl), 'all4': sum(r['all4'] for r in bs), 'planned': sum(r.get('planned', False) for r in bs), 'any_side': sum(r['any'] for r in bs),
                     'nofloor': why['nofloor'], 'nonav': why['nonav'], 'unreach': why['unreach']}
        r = rows[tag]
        log('  %-5s %4d boxes  good %4d (%5.1f%%)  | in play %4d  good %4d (%5.1f%%)  | any-side %4d  all-4 %4d  planned %3d | fail: nofloor %d  nonav %d  unreach %d' % (
            tag, r['boxes'], r['good'], 100.0 * r['good'] / r['boxes'], r['play'], r['good_play'], 100.0 * r['good_play'] / max(1, r['play']), r['any_side'], r['all4'], r['planned'], r['nofloor'], r['nonav'], r['unreach']))
    return rows


def scan(zp, bad=False, name=None, log=print):
    import kl_cover_add as A
    A.use_slot(zp)
    L = A.Lite(zp)
    log('%s' % zp)
    rep = check(L, load_plan(name or ''), log)
    rows = summary(rep, log=log)
    if bad:
        for k, r in sorted(rep['boxes'].items()):
            if not r['ok'] and r['tag'] in ('K6', 'KL', 'KM'):
                s = _failside(r)
                log('    BAD %s mid %s ground %s side %s stand %s floor %s nav %s %s' % (r['name'], r['mid'], r['ground'], s['side'], s['stand'], s['floor'], s['nav'], s['why']))
    return rep, rows


def live_maps(only=None):
    base = None
    for c in (r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', os.environ.get('KL_DD', '')):
        if c and os.path.isdir(os.path.join(c, 'KLExpansion', 'Maps')):
            base = os.path.join(c, 'KLExpansion', 'Maps')
            break
    if base is None:
        sys.exit('no <DD>\\KLExpansion\\Maps found')
    zs = sorted(glob.glob(os.path.join(base, '*', 'F??_Main.zip')))
    return [(os.path.basename(os.path.dirname(z)), z) for z in zs if not only or os.path.basename(os.path.dirname(z)) in only]


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('scan', 'live'):
        sys.exit(__doc__)
    out = {}
    pairs = []
    if a[0] == 'scan':
        pairs = [(os.path.basename(os.path.dirname(z)) or z, z) for z in a[1:] if not z.startswith('--') and z.lower().endswith('.zip')]
    else:
        only = a[a.index('--maps') + 1].split(',') if '--maps' in a else None
        pairs = live_maps(only)
    for name, zp in pairs:
        try:
            rep, rows = scan(zp, bad='--bad' in a, name=name)
            out[name] = {'rows': rows, 'spawn_parts': rep['spawn_parts'], 'n_spawns': rep['n_spawns'], 'boxes': rep['boxes']}
        except Exception as e:
            print('  %s FAILED: %r' % (name, e))
            out[name] = {'error': repr(e)}
    if '--json' in a:
        with open(a[a.index('--json') + 1], 'w') as fh:
            json.dump(out, fh, indent=1)


if __name__ == '__main__':
    main()
