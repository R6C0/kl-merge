#!/usr/bin/env python3
r"""kl_cover_dm09_1110.py - DM09 Retomoto: MORE COVER on the street + WRECK COVER (2026-11-10, owner 11-09: "more cover accessible all around ...
make sure you can go into cover from blown up vehicles [CONFIRMED ~15:00: 'yes work as cover when theyre wrecks yes after the explosion']").
OFFLINE: reads the LIVE DM09 files, writes only a stage folder (default C:\kl_build_1024\dm09cover_1110). Starts nothing, installs nothing.
This is a THIN WRAPPER over the existing cover tools: kl_cover_1026.walls (wall tiles), kl_cover_add.sparse / .cars (props, parked cars),
kl_fa_cover.apply / .check / .diff (write + verify), kl_cover_floornav + kl_cover_vet (reachable floor), kl_loot_1025.patch_zip (member-level patch).

    python kl_cover_dm09_1110.py measure [<zip>]                  count the cover boxes / FFCoverList of a zip (default: the live DM09 plain zip)
    python kl_cover_dm09_1110.py plan    [<zip>]                  what would be added, nothing written
    python kl_cover_dm09_1110.py stage   [<out>] [--no-rehearse]  zip + bots zip + base md5 + install.py (+ INSTALL/UNDO .bat, README.txt);
                                                                  rehearses install / 2nd install refused / undo byte-exact in <out>_scratch, then deletes it
    options: --density D (street target, boxes per 100 m2 of street mesh, default 5.5)  --max-walls N (120)  --max-sparse N (60)  --no-wreck  --no-walls  --no-sparse
             --game <DD folder> (read the live files from another root)

WHAT IT ADDS (one new group KL_CoverStreet!, boxes CoverBox{H,M}_KS_nn, ONE group so the cover count stays easy to read):
  1. WRECK COVER = static copies (kl_cover_add.cars) of the stock CoverBox children of every parked vehicle on the street that has no copy yet.
     A vehicle's own cover boxes are children of its key-framed group (they follow it, and go with it if it is deleted / swapped); a copy sits at the place
     the box stood at load and does NOT move, so the spot stays cover when the car is a wreck after the explosion (owner-confirmed wish).
     MEASURED on the live zip (see `measure`): every street vehicle already has copies from KL_CoverMore! (kl_cover_add --cars) except the ones this step lists.
  2. MORE STREET COVER = kl_cover_1026.walls (tiles against solid walls / planters / barriers) + kl_cover_add.sparse (boxes on solid props that have no cover),
     both limited to the STREET mesh (x/z window STREET, ground below STREET_MAX_Y) with a street density target; every box is vetted by kl_fa_cover.check
     (no box in a wall, floor under it, off NoCoverBox / exit boxes / the escape road) and by kl_cover_floornav (reachable floor), plus THIS tool's own
     van-lane and boarding-box exclusion (van_lane_skip).
ONE FFCoverList: no step here adds a controller (a second one asserts at kl2 0x6682c5); `measure` counts it before and after and the stage refuses unless it is 1.
Cover points: the game takes 5,000 boxes (kl_fa_cover.check); this step refuses beyond CAP_TOTAL (4500).

GUESSes (not measured, listed in the report too):
  - STREET window and STREET_MAX_Y: the mesh at the street/forecourt, not the tower rooms or the bus terminal (x < -15000).
  - ESC_LANE band (x -1850 +-350, z 8300..11100) and VAN_PAD: a rough belt round the van's stop (-1567,9300) and boarding box (-1769,79,9030) (re/retomoto_street.md s4; van 01 waits at (-4866,-40,6688); the live exit box otrExitLevel is checked separately by F.in_exit); kl_fa_bots.lane_dist
    (LANE_CLEAR 250 from the van's spline) is applied as well by kl_fa_cover.check, this is the belt to those braces.
  - DENSITY 5.5 per 100 m2: the stock FA median (~5, kl_cover_1026 header).
  - The static copies keep working after the explosion: that the explosion does NOT delete / move the KL_CoverMore!/KL_CoverStreet! boxes (they are plain top-level
    ZSTDOBJ boxes under a top-level group with no controller, nothing in the Retomoto scripts addresses them) is an ASSUMPTION; only a live look proves it.
  - Copies of boxes whose stock child stood IN a wall ledge are kept as the stock stood (exempt from the new-box rules by kl_cover_add's own exemption).
  - No extra 'flank' boxes are laid beside a car: a box next to a car body would stand < 150 (APART) from the car's own box and have no visible object to hide behind.
"""
import collections, hashlib, json, math, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAP, SLOT = 'DM09', 'F06'
FILES = ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5')
TAG_BAK = '.before-dm09cover1110'
OUT = r'C:\kl_build_1024\dm09cover_1110'
GROUP = 'KL_CoverStreet!'
TAG = '_KS_'
CAP_TOTAL = 4500                       # boxes in all (the game takes 5,000)
FREE_KEEP = 3 << 30                    # keep this much free on the stage drive

STREET = (-6500.0, 1500.0, -14500.0, 11500.0)   # GUESS: x0, x1, z0, z1 of the street / forecourt mesh (the bus terminal is x < -15000, the tower rooms are far north/up)
STREET_MAX_Y = 400.0                   # GUESS: polygons above this are tower floors / roofs, not the street
# the escape van: waits (-4866, -40, 6688), stops (-1567, 9300), boarding box (-1769, 79, 9030) (re/retomoto_street.md s4); this band is only a rough belt, the real lane check is kl_fa_cover.check + F.in_exit
ESC_LANE = dict(x=-1850.0, half=350.0, z0=8300.0, z1=11100.0)   # GUESS: the z margins round the wait / stop
VAN_PAD = 200.0                        # a box counts as in the lane when its middle is within this of the band (boxes are up to ~3 m long)
DENSITY = 5.5
MAX_WALLS, MAX_SPARSE = 120, 60
SPREAD = 220.0
COPY_NEAR = 25.0                       # an existing box of the same kind this near a vehicle's child box = the copy is already there


# ------------------------------------------------------------------ pure logic (kl_cover_dm09_1110_test.py)
def in_street(x, y, z, win=STREET, max_y=STREET_MAX_Y):
    return win[0] <= x <= win[1] and win[2] <= z <= win[3] and y < max_y


def in_van_lane(x, z, pad=0.0, lane=None):
    lane = lane or ESC_LANE
    return abs(x - lane['x']) <= lane['half'] + pad and lane['z0'] - pad <= z <= lane['z1'] + pad


def van_lane_skip(mid, exit_hit=None, lane=None, pad=VAN_PAD):
    """Reason string when a box middle (x, y, z) must not get a box: inside the escape van's drive band (+ pad) or the boarding box (exit_hit(point) -> bool)."""
    if in_van_lane(mid[0], mid[2], pad, lane):
        return 'escape van lane'
    if exit_hit is not None and exit_hit((mid[0], mid[1], mid[2])):
        return 'boarding box (otrExitLevel)'
    return None


def street_mask(mids, oks, win=STREET, max_y=STREET_MAX_Y):
    """nav.ok list restricted to the street: mids = [(x, y, z)], oks = [bool]. -> new list (same length)."""
    return [bool(o) and in_street(m[0], m[1], m[2], win, max_y) for m, o in zip(mids, oks)]


def missing_copies(cars, existing, near=COPY_NEAR):
    """cars = [{'mid': (x,y,z), 'kind': k, 'group': g}] (copies kl_cover_add.cars would make); existing = [{'mid','kind','parent'}] of EVERY box of the map.
    A copy is missing when no existing box of the same kind outside the vehicle's own group stands within `near` (x, z) of it."""
    out = []
    for c in cars:
        have = any(e['kind'] == c['kind'] and e['parent'] != c['group'] and math.hypot(e['mid'][0] - c['mid'][0], e['mid'][2] - c['mid'][2]) < near for e in existing)
        if not have:
            out.append(c)
    return out


def ffcover_ok(n):
    """A level may hold exactly ONE FFCoverList (a second asserts at kl2 0x6682c5)."""
    return n == 1


def cap_ok(total_boxes, cap=CAP_TOTAL):
    return total_boxes <= cap


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ install.py written next to the stage
INSTALL = r'''"""Installs / undoes DM09 COVER 1110 (tools/kl_cover_dm09_1110.py): more street cover + wreck cover boxes (recommended on).

  python install.py            install (originals -> <name>.before-dm09cover1110 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --root <dir> (or --game <dir>)  a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing: plain zip, bots zip, bots.base.md5); nothing is written while kl2.exe runs.
Never touches KL_PortBackup. Needs the LIVE files to be exactly the ones this was staged from (re-stage after another DM09 step)."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM09', '@TAG@'
FILES = @FILES@      # (name, pinned live md5, staged md5)


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


def opt(a, *names):
    for n in names:
        if n in a:
            return a[a.index(n) + 1]
    return None


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = opt(a, '--root', '--game') or GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (@SPACE@)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + the reserve free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
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
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def render_install(files, game=GAME, space='1 << 30'):
    return INSTALL.replace('@GAME@', game).replace('@TAG@', TAG_BAK).replace('@FILES@', repr(list(files))).replace('@SPACE@', space)


README = '''DM09 Retomoto COVER 1110  (recommended on)
==========================================
More cover on the street of Retomoto (DM09) and cover from the parked police cars / trucks / SWAT vans / buses that stays when they are wrecks.
Optional: undo puts the three original files back byte for byte.

What it changes (DM09 only: F06_Main.zip, F06_Main.bots.zip, F06_Main.bots.base.md5):
  - a new top-level group KL_CoverStreet! with %(n)d invisible cover boxes (%(n_wreck)d static copies of vehicle boxes that had none, %(n_wall)d at walls/planters/barriers,
    %(n_sparse)d on solid props), only on the street mesh, never in the escape van's lane or the boarding box.
  - cover boxes on the map: %(before)d -> %(after)d. One FFCoverList before and after (a second one would crash the level).

Install:  INSTALL.bat  (or: python install.py)     Undo: UNDO.bat  (or: python install.py --undo)     Check only: python install.py --dry
Close the game first. Pinned live md5s: %(pins)s
If another DM09 step changed the files since, install.py REFUSES (re-stage with: python tools/kl_cover_dm09_1110.py stage).
Not run in the game yet (owner on the PC): whether the AI and the player use the new boxes, and that the explosion leaves the copies alone, are GUESSes.
'''


# ------------------------------------------------------------------ the pipeline
def _imports():
    import kl_fa, kl_fa_bots as F, kl_fa_cover as C, kl_cover_add as A, kl_cover_1026 as K, kl_loot_1025 as LO
    return kl_fa, F, C, A, K, LO


def live_dir(game=GAME):
    return os.path.join(game, 'KLExpansion', 'Maps', MAP)


def measure(zp, log=print):
    """{'boxes': kind-ed cover boxes, 'high', 'low', 'records': all box records, 'nocover', 'ffcoverlist', 'by_tag', 'street': (boxes, mesh m2, per100)}"""
    kl_fa, F, C, A, K, LO = _imports()
    A.use_slot(zp)
    L = A.Lite(zp)
    sc = L.B.sc
    kinded = [b for b in L.boxes if b['kind']]
    tags = collections.Counter()
    for b in kinded:
        nm = b['name']
        tags['KS' if TAG in nm else 'KM' if '_KM_' in nm else 'K6' if '_K6_' in nm else 'KL' if '_KL_' in nm else 'stock/other'] += 1
    area = sum(K._area(L.nav.pv[i]) for i in range(len(L.nav.pv)) if L.nav.ok[i] and in_street(*L.nav.mid[i])) / 1e4
    st = sum(1 for b in kinded if in_street(b['mid'][0], b['mid'][1], b['mid'][2]))
    r = collections.OrderedDict(entities=len(L.B.ents), boxes=len(kinded), high=sum(1 for b in kinded if b['kind'] == 'high'), low=sum(1 for b in kinded if b['kind'] == 'low'),
                                records=len(L.boxes), nocover=len(L.nocover), ffcoverlist=len(kl_fa.controllers(sc, 'FFCoverList')), by_tag=dict(tags),
                                street_boxes=st, street_mesh_m2=round(area), street_per100=round(st / area * 100, 2) if area else 0)
    log('measure %s: %s' % (zp, json.dumps(r)))
    return L, r


def wreck_copies(L, log=print):
    """Static copies of the stock CoverBox children of parked vehicles that have none yet (kl_cover_add.cars filtered by missing_copies)."""
    kl_fa, F, C, A, K, LO = _imports()
    sc = L.B.sc
    cars = A.cars(L, log)
    for c in cars:
        c['mid'] = [c['origin'][0], c['origin'][1], c['origin'][2]]
        c['group'] = sc.parent[c['form_node']]
    # the copy's real box middle (A.cars' origin is the child's place; its box middle is the stock child's mid)
    child = {b['node']: b for b in L.boxes}
    for c in cars:
        b = child.get(c['form_node'])
        if b is not None:
            c['mid'] = [b['mid'][0], b['mid'][1], b['mid'][2]]
    existing = [dict(mid=b['mid'], kind=b['kind'], parent=sc.parent[b['node']]) for b in L.boxes if b['kind']]
    miss = missing_copies([dict(c) for c in cars], existing)
    keep = [c for c in cars if any(m['mid'] == c['mid'] and m['group'] == c['group'] and m['kind'] == c['kind'] for m in miss)]
    out, why = [], collections.Counter()
    for c in keep:
        if not in_street(c['mid'][0], c['mid'][1], c['mid'][2]):       # measured: the 3 copies outside lie in the bus terminal's NoCoverBoxes (AI never uses them)
            why['off the street window'] += 1
            continue
        if any(L.B.in_box(k, (c['mid'][0], c['mid'][1] + dy, c['mid'][2])) for k in L.nocover for dy in (-150.0, -100.0, -50.0, 0.0)):   # (kl_fa_cover.check tests corners at foot + 50)
            why['inside a NoCoverBox'] += 1
            continue
        r = van_lane_skip(c['mid'], lambda p: bool(L.exits) and F.in_exit(L.B, L.exits, p))
        if r:
            why[r] += 1
            continue
        c['object'] = sc.path[c['group']].rsplit(A.SEP, 1)[-1]
        out.append(c)
    log('wreck: %d vehicle boxes without a copy, kept %d (dropped: %s)' % (len(keep), len(out), dict(why)))
    return out, [dict(object=sc.path[c['group']].rsplit(A.SEP, 1)[-1], kind=c['kind'], mid=[round(v, 1) for v in c['mid']]) for c in keep]


def vehicle_table(L):
    """Every parked vehicle group of the street with its stock child boxes and the copies standing beside them (the verification the brief asks for)."""
    kl_fa, F, C, A, K, LO = _imports()
    sc = L.B.sc
    ctl = lambda k: [sc.p.key(c[0]) for c in sc.nodes[k]['ctrls']]
    by = {b['node']: b for b in L.boxes}
    rows = []
    for g in range(1, len(sc.nodes)):
        if sc.cls(g) != 'ZGROUP' or 'VehicleEffects' not in ctl(g):
            continue
        p = L.B.at(g)
        if not in_street(p[0], p[1] + 1, p[2]) and not (STREET[0] <= p[0] <= STREET[1] and STREET[2] <= p[2] <= STREET[3] + 4000):
            continue
        kids = [j for j in range(1, len(sc.nodes)) if sc.parent[j] == g and 'coverbox' in sc.names[j].lower() and j in by and by[j]['kind']]
        copies = 0
        for j in kids:
            copies += any(b['kind'] == by[j]['kind'] and sc.parent[b['node']] != g and math.hypot(b['mid'][0] - by[j]['mid'][0], b['mid'][2] - by[j]['mid'][2]) < COPY_NEAR
                          for b in L.boxes if b['kind'])
        rows.append(dict(vehicle=sc.path[g].rsplit(A.SEP, 1)[-1], at=[round(p[0]), round(p[1]), round(p[2])], stock_boxes=len(kids), copies=copies,
                         in_lane=in_van_lane(p[0], p[2], 0.0)))
    return rows


def plan(zp, o, log=print):
    """-> (L, P, report). P = {'boxes': [...]} for kl_fa_cover.apply."""
    kl_fa, F, C, A, K, LO = _imports()
    A.use_slot(zp)
    C.GROUP, C.TAG = GROUP, TAG
    L, before = measure(zp, log)
    if not ffcover_ok(before['ffcoverlist']):
        raise SystemExit('REFUSED: the live zip has %d FFCoverList (the stage keeps exactly one)' % before['ffcoverlist'])
    if any(L.B.sc.names[k] == GROUP for k in range(1, len(L.B.sc.nodes))):
        log('the %s group is already in this zip: nothing to add (idempotent)' % GROUP)
        return L, dict(boxes=[]), dict(before=before)
    fs = C.forms(L.B, L.boxes, 'b', True)
    log('box models a new box may take: %s' % sorted('%dx%dx%d' % tuple(f['size']) for f in fs))
    ok0 = list(L.nav.ok)
    L.nav.ok[:] = street_mask(L.nav.mid, ok0)             # walls() / sparse() pick their places only on the street mesh
    new = []
    import kl_cover_floornav as FN
    sf0, gr0 = K.safety_features, FN.Ground

    def unmasked(fn):                  # spawn / loot stations and the reachable-floor grid need the WHOLE mesh (no START point stands on the street mask)
        def w(*a, **k):
            m = list(L.nav.ok)
            L.nav.ok[:] = ok0
            try:
                return fn(*a, **k)
            finally:
                L.nav.ok[:] = m
        return w
    K.safety_features, FN.Ground = unmasked(sf0), unmasked(gr0)
    try:
        if fs and o['walls']:
            K.walls(L, fs, new, o['max_walls'], o['density'], o['spread'], log, True, True)
        if fs and o['sparse']:
            A.sparse(L, fs, new, len(new) + o['max_sparse'], o['spread'], log)
    finally:
        K.safety_features, FN.Ground = sf0, gr0
        L.nav.ok[:] = ok0
    dropped = collections.Counter()
    keep = []
    for b in new:
        r = van_lane_skip(b['mid'], lambda p: bool(L.exits) and F.in_exit(L.B, L.exits, p))
        if r:
            dropped[r] += 1
            continue
        keep.append(b)
    n_wall = sum(1 for b in keep if b['via'] == 'wall')
    n_sparse = sum(1 for b in keep if b['via'] == 'sparse')
    wreck, wreck_all = ([], [])
    if o['wreck']:
        wreck, wreck_all = wreck_copies(L, log)
    boxes = keep + wreck
    if not cap_ok(before['boxes'] + before['records'] - before['boxes'] + len(boxes) + 0, CAP_TOTAL) or not cap_ok(before['boxes'] + len(boxes)):
        raise SystemExit('REFUSED: %d boxes + %d new is over the cap %d' % (before['boxes'], len(boxes), CAP_TOTAL))
    cnt = collections.Counter()
    for c in boxes:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', TAG, cnt[c['kind']])
    P = collections.OrderedDict(folder=L.folder, options=dict(o), boxes=boxes)
    rep = collections.OrderedDict(before=before, added=len(boxes), wall=n_wall, sparse=n_sparse, wreck=len(wreck), wreck_candidates=wreck_all,
                                  dropped_van_lane_or_exit=dict(dropped), vehicles=vehicle_table(L))
    log('PLAN: %d boxes (%d low, %d high): %d wall, %d sparse, %d wreck copies; dropped by the van-lane/boarding rule: %s' % (len(boxes), cnt['low'], cnt['high'], n_wall, n_sparse, len(wreck), dict(dropped)))
    return L, P, rep


def build_one(zp, work, P, log=print):
    """Write P into a copy of `zp` (copied as <work>/in/F06_Main.zip because the checkers open <slot>_Main.zip) -> (path of the member-patched zip, report)."""
    kl_fa, F, C, A, K, LO = _imports()
    src = os.path.join(work, 'in', 'F06_Main.zip')
    os.makedirs(os.path.dirname(src), exist_ok=True)
    shutil.copyfile(zp, src)
    mid = os.path.join(work, 'mid')
    LO.rmtree(mid)
    os.makedirs(mid)
    A.use_slot(src)
    C.GROUP, C.TAG = GROUP, TAG
    L = A.Lite(src)
    rep = C.apply(L, P, mid, log)
    rep['plan'] = P
    with open(os.path.join(mid, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out = C.check(mid, log)
    cn = tuple(c['name'] for c in P['boxes'] if c.get('via') == 'car')
    # the copies of a parked car's boxes stand where a stock box already stood: the new-box rules (APART, a plan height, static collision under a car) do not apply (kl_cover_add.build)
    out = [('NOTE', 'car copy: ' + t) if s == 'FAIL' and cn and t.startswith(cn) else (s, t) for s, t in out]
    fails = [t for s, t in out if s == 'FAIL']
    bad = C.diff(L.folder, mid, log)
    if fails or bad:
        raise SystemExit('check FAIL %s / diff %s' % (fails[:4], bad))
    new_zip = os.path.join(mid, 'F06_Main.zip')
    with zipfile.ZipFile(new_zip) as z, zipfile.ZipFile(src) as a:
        repl = {i.filename: z.read(i.filename) for i in a.infolist() if z.read(i.filename) != a.read(i.filename)}
    final = os.path.join(work, 'final.zip')
    LO.patch_zip(src, final, repl)
    members = sorted(n.rsplit('_Main', 1)[-1] for n in repl)
    LO.rmtree(mid)
    os.remove(src)
    return final, dict(members_changed=members, check_lines=len(out), check_notes=sum(1 for s, _t in out if s == 'NOTE'))


def prune_unreachable(zp, work, P, log=print):
    """Build P once, run kl_cover_floornav.check on the result and drop every new box with no usable side (review 1110: the prop box KS_09 had none).
    -> (P filtered and renamed, list of dropped boxes). Car copies stand where a stock box stood and are kept."""
    kl_fa, F, C, A, K, LO = _imports()
    import kl_cover_floornav as FN
    pw = os.path.join(work, 'prune')
    fin, _r = build_one(zp, pw, json.loads(json.dumps(P, default=str)), log)
    chk = os.path.join(pw, 'chk')
    os.makedirs(chk, exist_ok=True)
    z = os.path.join(chk, 'F06_Main.zip')
    shutil.copyfile(fin, z)
    A.use_slot(z)
    rep = FN.check(A.Lite(z), {}, lambda *a: None)
    bad = []
    for r in rep['boxes'].values():
        if TAG not in r['name'] or r['any']:
            continue
        for b in P['boxes']:
            if b.get('via') != 'car' and abs(b['mid'][0] - r['mid'][0]) < 2 and abs(b['mid'][2] - r['mid'][2]) < 2:
                bad.append(b)
    A.use_slot(zp)
    LO.rmtree(pw)
    if not bad:
        return P, []
    ids = {id(b) for b in bad}
    P = collections.OrderedDict(P)
    P['boxes'] = [b for b in P['boxes'] if id(b) not in ids]
    cnt = collections.Counter()
    for c in P['boxes']:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', TAG, cnt[c['kind']])
    for b in bad:
        log('PRUNED (no reachable side): %s at %s via %s' % (b.get('name'), [round(v) for v in b['mid']], b.get('via')))
    return P, bad


def stage(out, o, game=GAME, rehearse=True, log=print):
    kl_fa, F, C, A, K, LO = _imports()
    d = live_dir(game)
    live = {n: os.path.join(d, n) for n in FILES}
    pins = {n: fmd5(p) for n, p in live.items()}
    if open(live[FILES[2]]).read().strip() != pins[FILES[0]]:
        raise SystemExit('REFUSED: the live bots.base.md5 is not the live plain zip md5')
    need = 6 * os.path.getsize(live[FILES[0]]) + FREE_KEEP
    os.makedirs(out, exist_ok=True)
    if shutil.disk_usage(out).free < need:
        raise SystemExit('REFUSED: less than %d MB free on the stage drive' % (need >> 20))
    work = os.path.join(out, 'work')
    LO.rmtree(work)
    os.makedirs(work)
    for f in os.listdir(out):
        p = os.path.join(out, f)
        if p != work and os.path.isfile(p):
            os.remove(p)
    log('live pins: %s' % pins)
    for f in os.listdir(d):                                         # the small files beside the zip (the checkers read the .ini)
        if f.lower().endswith('.ini') and os.path.isfile(os.path.join(d, f)):
            os.makedirs(os.path.join(work, 'in'), exist_ok=True)
            shutil.copyfile(os.path.join(d, f), os.path.join(work, 'in', f))
    L, P, rep = plan(live[FILES[0]], o, log)
    if not P['boxes']:
        raise SystemExit('nothing to add')
    P, pruned = prune_unreachable(live[FILES[0]], work, P, log)
    rep['pruned_unreachable'] = [dict(name=b.get('name'), mid=b['mid'], via=b.get('via')) for b in pruned]
    rep['added'] = len(P['boxes'])
    rep['sparse'] -= sum(1 for b in pruned if b.get('via') == 'sparse')
    rep['wall'] -= sum(1 for b in pruned if b.get('via') == 'wall')
    if not P['boxes']:
        raise SystemExit('nothing to add')
    P0 = json.loads(json.dumps(P, default=str))                    # the plan before apply adds 'bb'
    res = {}
    finals = {}
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        log('== %s' % name)
        if key == 'bots':
            P = json.loads(json.dumps(P0))
            for b in P['boxes']:
                b['mid'] = list(b['mid'])
        fin, r = build_one(live[name], os.path.join(work, key), P, log)
        shutil.copyfile(fin, os.path.join(out, name))
        os.remove(fin)
        finals[name] = os.path.join(out, name)
        res[key] = r
    base = fmd5(finals[FILES[0]])
    open(os.path.join(out, FILES[2]), 'w', newline='\n').write(base + '\n')
    # counts after, from the staged files themselves
    after = {}
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        _L, m = measure(finals[name], log)
        after[key] = m
        if not ffcover_ok(m['ffcoverlist']):
            raise SystemExit('REFUSED: %s has %d FFCoverList after' % (name, m['ffcoverlist']))
        if not cap_ok(m['boxes']):
            raise SystemExit('REFUSED: %s has %d boxes after' % (name, m['boxes']))
        if m['boxes'] != rep['before']['boxes'] + len(P0['boxes']) or m['nocover'] != rep['before']['nocover']:
            raise SystemExit('REFUSED: %s: %d boxes after, expected %d; NoCoverBox %d -> %d' % (name, m['boxes'], rep['before']['boxes'] + len(P0['boxes']), rep['before']['nocover'], m['nocover']))
    files = [(FILES[0], pins[FILES[0]], base), (FILES[1], pins[FILES[1]], fmd5(finals[FILES[1]])), (FILES[2], pins[FILES[2]], fmd5(os.path.join(out, FILES[2])))]
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(render_install(files, game))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    open(os.path.join(out, 'README.txt'), 'w', newline='\n').write(README % dict(n=len(P0['boxes']), n_wreck=rep['wreck'], n_wall=rep['wall'], n_sparse=rep['sparse'],
                                                                                     before=rep['before']['boxes'], after=after['plain']['boxes'],
                                                                                     pins=', '.join('%s %s' % (n, h[:8]) for n, h in pins.items())))
    with open(os.path.join(out, 'cover_plan.json'), 'w') as f:
        json.dump(P0['boxes'], f, indent=0, default=str)
    report = collections.OrderedDict(pins=pins, files=files, plan=rep, after=after, built=res, options=dict(o))
    with open(os.path.join(out, 'build_report.json'), 'w') as f:
        json.dump(report, f, indent=1, default=str)
    LO.rmtree(work)
    if rehearse:
        rehearsal(out, files, game, log)
    for n, o_, w in files:
        log('%-26s %s -> %s' % (n, o_, w))
    return report


def rehearsal(out, files, game, log=print):
    """Install, 2nd install refused, --dry, undo byte-exact, 2nd undo refused - on a COPY of the three live DM09 files in <out>_scratch; the scratch is deleted afterwards."""
    kl_fa, F, C, A, K, LO = _imports()
    scratch = os.path.abspath(out) + '_scratch'
    assert os.path.abspath(scratch).lower() != os.path.abspath(game).lower()
    LO.rmtree(scratch)
    g = os.path.join(scratch, 'game')
    d = os.path.join(g, 'KLExpansion', 'Maps', MAP)
    os.makedirs(d)
    try:
        for n, old, _new in files:
            shutil.copyfile(os.path.join(live_dir(game), n), os.path.join(d, n))
        run = lambda *x: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--root', g, '--skip-run-check'] + list(x), capture_output=True, text=True)
        steps = []
        t = run('--dry'); steps.append(('dry', t.returncode == 0 and 'would install' in t.stdout and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files)))
        t = run(); steps.append(('install', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == w for n, _o, w in files) and all(fmd5(os.path.join(d, n + TAG_BAK)) == o for n, o, _w in files)))
        t = run(); steps.append(('2nd install refused', t.returncode == 1 and 'REFUSED' in t.stdout and all(fmd5(os.path.join(d, n)) == w for n, _o, w in files)))
        t = run('--undo'); steps.append(('undo byte-exact', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files) and not any(os.path.exists(os.path.join(d, n + TAG_BAK)) for n, _o, _w in files)))
        t = run('--undo'); steps.append(('2nd undo refused', t.returncode == 1 and 'REFUSED' in t.stdout))
        t = run(); steps.append(('reinstall after undo', t.returncode == 0))
        t = run('--undo'); steps.append(('final undo byte-exact', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files)))
        for s, ok in steps:
            log('  rehearsal %-24s %s' % (s, 'PASS' if ok else 'FAIL'))
        if not all(ok for _s, ok in steps):
            raise SystemExit('rehearsal FAILED')
    finally:
        LO.rmtree(scratch)
        log('  scratch %s %s' % (scratch, 'deleted' if not os.path.exists(scratch) else 'STILL THERE'))


def options(a):
    o = dict(density=DENSITY, max_walls=MAX_WALLS, max_sparse=MAX_SPARSE, spread=SPREAD, wreck=True, walls=True, sparse=True)
    a = list(a)
    game = GAME
    rest = []
    while a:
        x = a.pop(0)
        if x == '--density': o['density'] = float(a.pop(0))
        elif x == '--max-walls': o['max_walls'] = int(a.pop(0))
        elif x == '--max-sparse': o['max_sparse'] = int(a.pop(0))
        elif x == '--game': game = a.pop(0)
        elif x == '--no-wreck': o['wreck'] = False
        elif x == '--no-walls': o['walls'] = False
        elif x == '--no-sparse': o['sparse'] = False
        else: rest.append(x)
    return o, game, rest


def main(argv):
    if not argv or argv[0] not in ('measure', 'plan', 'stage'):
        print(__doc__)
        return 2
    o, game, rest = options(argv[1:])
    rehearse = '--no-rehearse' not in rest
    rest = [x for x in rest if x != '--no-rehearse']
    live = os.path.join(live_dir(game), FILES[0])
    if argv[0] == 'measure':
        _L, r = measure(rest[0] if rest else live)
        print(json.dumps(r, indent=1))
    elif argv[0] == 'plan':
        _L, P, rep = plan(rest[0] if rest else live, o)
        print(json.dumps(dict(rep, boxes=[{k: b[k] for k in ('name', 'kind', 'via', 'mid', 'object') if k in b} for b in P['boxes']]), indent=1, default=str))
    else:
        stage(rest[0] if rest else OUT, o, game, rehearse)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
