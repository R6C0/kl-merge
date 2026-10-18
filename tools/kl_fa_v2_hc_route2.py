"""kl_fa_v2_hc_route2.py - Hot Coffee II (DM01B): find the campaign's still-closed pieces on the way START rows -> van, and (opt-in) open them.

WHY (kl-merge-e5, 2026-10-18): kl_fa_v2_hotcoffee.ROUTE_OPEN holds the pieces found by kl_walk2d (STEP 65, 40-unit cells) up to the second steel door;
its comment says the flood then reaches z 23,000 of 30,800 and "stops at cells the 40-unit grid cannot judge; not walked further". This module walks
the REST, on the finished level, with a finer grid, and says which collision entities stand at the frontier.

This file does NOT edit kl_fa_v2_hotcoffee.py (kl-merge-3f's). Everything here is opt-in:
  python kl_fa_v2_hc_route2.py walk <finished folder or F01_Main.zip> [--cell 20] [--step 65] [--drop <path substring> ...] [--extra] [--near 400] [--nocam]
      read-only: floods from the START rows with the blast + ROUTE_OPEN pieces dropped (read from the level's own wiring), prints the extent and the
      steep pieces that wall each frontier cell (top-level subtree / entity), grouped. --extra also drops EXTRA_OPEN below; --nocam ignores camera-only collision (flag 0x40).
  python kl_fa_v2_hc_route2.py test <out> [--keep] [--str PC_Def.str]      the SAME build as 'kl_fa_v2_hotcoffee.py test' with ROUTE_OPEN + EXTRA_OPEN (default build unchanged:
      this runs in-process and sets kl_fa_v2_hotcoffee.ROUTE_OPEN before the build; nothing is written to the module)
EXTRA_OPEN holds the pieces a walk has named so far (each a GUESS until a walk with --extra reaches the van and a live run agrees).
"""
import collections, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

START_XZ = (-400.0, 4200.0)             # the START rows' middle (kl_fa_v2_hotcoffee.START)
VAN_XZ = (2000.0, 30800.0)              # the van's stop
# Paths relative to a campaign tile, as ROUTE_OPEN is ('<tile>\\<node>'). GUESS: empty until a walk finds the blockers.
# MEASURED (2026-10-18, civs5_dm01b_1018/DM01B F03_Main.zip, kl_walk2d at cell 20 and 40, STEP 65, blast + ROUTE_OPEN already dropped): the flood from the START rows
# ends at z 17310, in the second steel door's gap, because the warehouse's main wall B stands across it at z 17321: three triangles (2745..3054 wide, y 60..862,
# normal 0) fill the whole door opening. With that node dropped the flood reaches z 23,050 (the warehouse's north wall at x 5930 .. 8010, y -10 .. 396), which is
# the 'z 23,000' the kl_fa_v2_hotcoffee comment names. GUESS: that this node is what the campaign's script removes (it is a 'name!remains' destructible; its sibling
# '...MainWallB_01!ColiObj_CamColli_01' is camera collision and stays). GUESS: a DeactivateGeom also hides the wall's MESH, so the warehouse would show a 310 x 800
# hole in its south wall for the whole round (the alley wall and the door leaves of ROUTE_OPEN do the same); a live look decides.
# MEASURED (2026-10-18, same level, walk --extra, cell 20, STEP 65): past MainWallB the flood fills the warehouse + the diner (x -30 .. 8010, z up to 23,050 / 23,070) and stops at
# the diner's FRONT: Entrance_01 (x 5897..6300, z 23080..23100, y 0..320) is a 36-triangle wall piece whose doorway holds the diner's animated glass door,
# 'PC0901_M01_Dor_Diner_Anim_01' (ZGROUP: MatPosAnim + RelayMessageList; leaves Dor_attach x 6040..6160 y 0..252 [key-framed shape, filter 0x72], Dor_Win_Whole /
# Dor_Win_Shattered [ShotActivate, 0x66]). It is the door the campaign OPENS (its own animation), so no clean-up of level geometry is needed. WHY dropping it alone 'changed nothing':
# 'ColiObj_camerablocker_01' (x 4723..6690, z 23078, y -10..396, 2 triangles) closes the whole diner front in the model, but its .HVK filter flags are 0x40, the
# same word as the 'ColiObj_CAM_Boothcollision*' shapes (their twins 'ColiObj_Hero_Boothcollision*' are 0x108) = camera-only collision. GUESS (names + twin pairs, not the
# engine's filter table): 0x40 does not stop a player. Walk with --nocam (ignores shapes whose every flag is 0x40) + this door: the flood reaches the van cell
# (z 31,470 max; van floor y -15). Without --nocam the walk needs --drop ColiObj_camerablocker_01 as well. GUESS: DeactivateGeom also hides the door's mesh and glass, so the
# diner front shows an open doorway for the whole round (the same cost as the warehouse wall B); a live look decides. Outside the door: Street_02a facade pieces
# (FacShop_A_0n, GlassA/B_Diner, pillars) did not stop the flood.
EXTRA_OPEN = ('M01A_Ins_Warehouse_101a\\SI0103_M01_WareHouse_MainWallB_01!SI0103_M01_WareHouse_MainWallB',
              'M01A_Ins_Diner_101a\\PC0901_M01_Dor_Diner_Anim_01')


def _opened(L, extra):
    """Full paths of the nodes the finished level's blast list takes off (campaign pieces + brick wall + ROUTE_OPEN), read from the level's wiring."""
    import kl_fa_v2_hotcoffee as H, kl_fa_bank as BK, kl_fa_author as A
    sc = L.sc
    k = A.node_of(sc, H.BLAST['out'])
    paths = []
    for s in BK.values(sc, k, 'DeactivateGeom')[1]:
        for j in (sc.resolve(s) or ()):
            paths.append(sc.path[j])
    for tail in tuple(H.ROUTE_OPEN) + tuple(extra):
        hit = [sc.path[j] for j in range(1, len(sc.names)) if sc.path[j] and sc.path[j].endswith('\\' + tail)]
        if len(hit) != 1:
            raise ValueError('kl_fa_v2_hc_route2: ROUTE_OPEN/EXTRA_OPEN %s: %d nodes' % (tail, len(hit)))
        paths += hit
    return sorted(set(paths))      # ROUTE_OPEN is added even when the level predates it (older builds); the set drops duplicates


def _camera_only_ground():
    """Make kl_walk2d's Ground leave out the shapes whose every .HVK collision flag is 0x40 (camera-only: see EXTRA_OPEN; GUESS)."""
    import kl_map_escape as ESC, kl_hvk

    Base = ESC.Ground

    class Ground(Base):
        def __init__(self, L):
            Base.__init__(self, L)
            cam = set(kl_hvk.ref(i) for s in L.hvk.shapes if s.sub and all(x[1] == 0x40 for x in s.sub) for i in s.inst)
            self.tris = [t for t in self.tris if t[3] not in cam]
            self.boxes = [b for b in self.boxes if b[1] not in cam]
            self.camera_only = len(cam)
    ESC.Ground = Ground


def walk(src, cell=20.0, step=65.0, drop=(), extra=(), near=None, log=print, nocam=False):
    """-> dict(reached, extent, van_reached, frontier: [(top-level name, entity name, count)]). nocam: ignore camera-only (flag 0x40) shapes."""
    import kl_walk2d as W
    if nocam:
        _camera_only_ground()
    W.CELL, W.STEP = float(cell), float(step)
    import kl_map_escape as ESC
    L = ESC.Level(src)
    drops = _opened(L, extra) + list(drop)
    log('  dropping %d node(s) the blast / route lists take off%s' % (len(drops), ' (+%d extra)' % len(extra) if extra else ''))
    box = (-3000.0, 8000.0, 3000.0, 32000.0)
    w = W.Walk(src, box, drops)
    reach = w.flood(START_XZ)
    zs = [w.xz(c)[1] for c in reach]
    xs = [w.xz(c)[0] for c in reach]
    van = (w._ix(VAN_XZ[0]), w._iz(VAN_XZ[1])) in reach
    log('  reached cells %d, extent x %d .. %d z %d .. %d, van cell reached: %s' % (len(reach), min(xs), max(xs), min(zs), max(zs), van))
    # frontier: an unreached cell next to a reached one that holds a floor and a steep piece spanning body height
    # near: keep only reached cells within `near` of the farthest z (the walls at the END of the flood, not the side walls of the whole level)
    zmax = max(zs)
    seen, cnt = set(), collections.Counter()
    node_of = {e.ref: i + 1 for i, e in enumerate(L.ents)}
    sc = L.sc
    # pieces the walk itself dropped (a path under a dropped path) must not be named as walls
    gone = {ref for ref, k in node_of.items() if any(sc.path[k].startswith(d) for d in drops)}
    cand = []
    for (i, j), y in reach.items():
        if near is not None and w.xz((i, j))[1] < zmax - near:
            continue
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if (a, b) in reach or not (0 <= a < w.nx and 0 <= b < w.nz) or (a, b) in seen:
                continue
            seen.add((a, b))
            if w.floors[a][b] and w.walls[a][b]:
                cand.append((a, b, y))
    # name the pieces: steep triangles / boxes near each candidate cell centre
    cells = {(a, b): w.xz((a, b)) for a, b, _y in cand}
    ys = {(a, b): y for a, b, y in cand}
    for (typ, ref, lo, hi) in w.g.boxes:
        if ref in gone:
            continue
        for c, (x, z) in cells.items():
            if lo[0] - cell <= x <= hi[0] + cell and lo[2] - cell <= z <= hi[2] + cell and lo[1] < ys[c] + W.BODY[1] and hi[1] > ys[c] + W.BODY[0]:
                cnt[ref] += 1
    for (a, b, c_, ref, ny) in w.g.tris:
        if ny >= 0.45 or ref in gone:
            continue
        xs_, zs_ = (a[0], b[0], c_[0]), (a[2], b[2], c_[2])
        bx0, bx1, bz0, bz1 = min(xs_) - cell, max(xs_) + cell, min(zs_) - cell, max(zs_) + cell
        ylo, yhi = min(a[1], b[1], c_[1]), max(a[1], b[1], c_[1])
        for c, (x, z) in cells.items():
            if bx0 <= x <= bx1 and bz0 <= z <= bz1 and ylo < ys[c] + W.BODY[1] and yhi > ys[c] + W.BODY[0]:
                cnt[ref] += 1
                break
    out = []
    for ref, n in cnt.most_common(25):
        k = node_of.get(ref)
        if ref in gone:
            continue
        out.append((sc.names[sc.top[k]] if k else '?', sc.path[k] if k else 'REF %d' % ref, n))
    for t in out:
        log('   frontier piece (%4d cells)  %s   <- %s' % (t[2], t[1], t[0]))
    return dict(reached=len(reach), extent=(min(xs), max(xs), min(zs), max(zs)), van_reached=van, frontier=out, candidates=len(cand))


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'walk':
        cell = float(a[a.index('--cell') + 1]) if '--cell' in a else 20.0
        step = float(a[a.index('--step') + 1]) if '--step' in a else 65.0
        drop = [a[i + 1] for i, v in enumerate(a) if v == '--drop']
        near = float(a[a.index('--near') + 1]) if '--near' in a else None
        r = walk(a[1], cell, step, drop, EXTRA_OPEN if '--extra' in a else (), near, nocam='--nocam' in a)
        sys.exit(0 if r['van_reached'] else 1)
    elif len(a) >= 2 and a[0] == 'test':
        import kl_fa_v2_hotcoffee as H
        H.ROUTE_OPEN = tuple(H.ROUTE_OPEN) + tuple(t for t in EXTRA_OPEN if t not in H.ROUTE_OPEN)
        if '--str' in a:                # as kl_fa_v2_hotcoffee.py test --str
            import kl_fa_bank as BK
            H.STREAM = os.path.abspath(a[a.index('--str') + 1])
            BK.use_stream(H.STREAM)
        sys.exit(H.test(a[1], '--keep' in a))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
