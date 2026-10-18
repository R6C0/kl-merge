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
  --coll-only (walk / test / collonly): instead of taking the two pieces off whole (a hole in the visuals), keep every node and strip ONLY the blocking
      collision triangles from the .HVK (COLL_ONLY below); see the block comment there for what is measured and what is a guess.
  python kl_fa_v2_hc_route2.py collonly <in F01_Main.zip or folder> <out folder>     post-pass: copy the level, patch the .HVK member, write F01_Main.zip
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


# COLL_ONLY (2026-10-18, --coll-only): strip only the BLOCKING COLLISION of the two pieces, keep every node, model and animation.
# MEASURED (built level 8d83b0be, kl_hvk): the warehouse wall is ONE entity (.gms node 8503, REF 28527) that owns BOTH its model (.prm root 40605: 17 meshes, 1600 x 1381, the
# whole wall with a closed door leaf at local x 528..672 y 0..252) and its HVK shape 4071 (STATIC, 60 triangles, one MOPP code). Model and collision are not two nodes, but the
# .HVK shape is separate data: the doorway is shut by 8 triangles (nos. 52..59) of the plane z 17321, x 2745..3054, y 60..1160 -- the rest (frame, panel, ledges) is not on the route.
# The diner door group holds three key-framed shapes (type 4, no MOPP): Dor_attach 4079 (50 triangles, 0x72), Dor_Win_Whole 4081 (16, 0x66) and Dor_Win_Shattered 4080 (hidden twin).
# HOW a triangle is taken out: its three vertices are copied and the copies moved straight down until the piece lies below y -200 (the .HVK header box reaches y -1750), the index
# list keeps its length (the sub-part counts and the MOPP terminal ids stay true). Nothing degenerate, no MOPP rebuild. GUESS: Havok does not mind a triangle that no query can
# reach; nothing was run in the game. The visuals are untouched: with only the collision gone the warehouse shows its closed door and the diner its closed glass door and the bots
# walk through them like ghosts (the owner decides if that is better than a hole). The door's own animation (MatPosAnim 'Activate' on the group) would be the clean answer; what it
# does (open? swing?) is in the .ANM and was not read, so it needs a live look.
COLL_ONLY = (('M01A_Ins_Warehouse_101a\\SI0103_M01_WareHouse_MainWallB_01!SI0103_M01_WareHouse_MainWallB', tuple(range(52, 60))),
             ('M01A_Ins_Diner_101a\\PC0901_M01_Dor_Diner_Anim_01\\Dor_Diner_Anim_Geom_01\\Dor_attach', None),       # None = every triangle of every shape of the node
             ('M01A_Ins_Diner_101a\\PC0901_M01_Dor_Diner_Anim_01\\Dor_Diner_Anim_Geom_01\\Dor_Win_Whole', None),
             ('M01A_Ins_Diner_101a\\PC0901_M01_Dor_Diner_Anim_01\\Dor_Diner_Anim_Geom_01\\Dor_Win_Shattered', None))      # hidden at load (.gms 0x400); sunk too: a hidden body may still collide (GUESS)
SINK_TO = -200.0        # cm: the highest point of a sunk triangle in world y (the floor of the route stands at about 0, the world box ends at -1750)


def _sink(hvk, ref, tris, ents_world):
    """Move triangles `tris` (None = all) of every shape that has a placement for `ref` straight down; -> triangles changed."""
    import struct, kl_hvk
    done = 0
    for s in hvk.shapes:
        for inst in s.inst:
            if kl_hvk.ref(inst) != ref or s.convex:
                continue
            nv = len(s.verts) // s.vstride
            idx = list(struct.unpack('<%dH' % (len(s.idx) // 2), s.idx))
            vs = [list(struct.unpack_from('<3f', s.verts, i * s.vstride)) for i in range(nv)]
            M = struct.unpack_from('<9f', inst, 12)
            py = struct.unpack_from('<3f', inst, 0)[1]
            want = range(len(idx) // 3) if tris is None else tris
            used = sorted(set(idx[3 * t + c] for t in want for c in range(3)))
            top = max(100.0 * (py + M[3] * vs[i][0] + M[4] * vs[i][1] + M[5] * vs[i][2]) for i in used)       # world y in cm of the highest vertex
            d = (0.0, (SINK_TO - top) / 100.0, 0.0)                                                          # the move, world metres
            loc = [M[0] * d[0] + M[3] * d[1] + M[6] * d[2], M[1] * d[0] + M[4] * d[1] + M[7] * d[2], M[2] * d[0] + M[5] * d[1] + M[8] * d[2]]   # M^T d (M orthonormal)
            wset = set(want)
            shared = set(idx[3 * t + c] for t in range(len(idx) // 3) if t not in wset for c in range(3))
            newv, remap = bytearray(), {}
            for i in used:
                if i in shared:                                   # a vertex a kept triangle also uses: copy it, move the copy
                    remap[i] = nv + len(remap)
                    raw = bytearray(s.verts[i * s.vstride:(i + 1) * s.vstride])
                    struct.pack_into('<3f', raw, 0, *(vs[i][a] + loc[a] for a in range(3)))
                    newv += raw
                else:                                             # only moved triangles use it: move it in place
                    v = bytearray(s.verts[i * s.vstride:(i + 1) * s.vstride])
                    struct.pack_into('<3f', v, 0, *(vs[i][a] + loc[a] for a in range(3)))
                    s.verts = s.verts[:i * s.vstride] + bytes(v) + s.verts[(i + 1) * s.vstride:]
            for t in want:
                for c in range(3):
                    if idx[3 * t + c] in remap:
                        idx[3 * t + c] = remap[idx[3 * t + c]]
            s.verts += bytes(newv)
            s.idx = struct.pack('<%dH' % len(idx), *idx)
            done += len(want)
    return done


def coll_only_patch(L, log=print):
    """Patch L.hvk (kl_hvk.Hvk, in memory) as COLL_ONLY says. -> triangles moved."""
    n = 0
    node = {}
    for k in range(1, len(L.sc.names)):
        node.setdefault(L.sc.path[k], k)
    for tail, tris in COLL_ONLY:
        hit = [k for k in range(1, len(L.sc.names)) if L.sc.path[k] and L.sc.path[k].endswith('\\' + tail)]
        if len(hit) != 1:
            raise ValueError('kl_fa_v2_hc_route2: COLL_ONLY %s: %d nodes' % (tail, len(hit)))
        c = _sink(L.hvk, L.ents[hit[0] - 1].ref, tris, None)
        if not c:
            raise ValueError('kl_fa_v2_hc_route2: COLL_ONLY %s: no triangles' % tail)
        log('  coll-only: %s: %d triangles sunk' % (tail.split('\\')[-1], c))
        n += c
    return n


def _coll_only_level():
    """Make kl_map_escape.Level patch its .HVK in memory (the walk then sees the stripped collision)."""
    import kl_map_escape as ESC
    Base = ESC.Level

    class Level(Base):
        def __init__(self, src):
            Base.__init__(self, src)
            coll_only_patch(self, lambda *a: None)
    ESC.Level = Level


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


def walk(src, cell=20.0, step=65.0, drop=(), extra=(), near=None, log=print, nocam=False, coll_only=False, skip_extra=False):
    """-> dict(reached, extent, van_reached, frontier: [(top-level name, entity name, count)]). nocam: ignore camera-only (flag 0x40) shapes."""
    import kl_walk2d as W
    if coll_only:
        _coll_only_level()
    if nocam:
        _camera_only_ground()
    W.CELL, W.STEP = float(cell), float(step)
    import kl_map_escape as ESC
    L = ESC.Level(src)
    drops = _opened(L, extra) + list(drop)
    if skip_extra:                  # a level built WITH EXTRA_OPEN in its lists (8d83b0be): do not drop those two (used with --coll-only)
        gone_x = [p for p in drops if any(p.endswith('\\' + t) for t in EXTRA_OPEN)]
        drops = [p for p in drops if p not in gone_x]
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


def collonly(src, out=None, log=print):
    """Post-pass: write the level `src` (a finished folder or its F01_Main.zip) with the COLL_ONLY triangles sunk in its .HVK member; every other member is copied
    as it is (same compression, same bytes). out = the new folder (siblings of the archive are copied), None = in place. -> path of the archive."""
    import shutil, zipfile, kl_map_escape as ESC
    zp = src if src.lower().endswith('.zip') else os.path.join(src, ESC.SLOT + '_Main.zip')
    L = ESC.Level(zp)
    name = L.ext['.hvk']
    with zipfile.ZipFile(zp) as z:
        raw = z.read(name)
    if L.hvk.serialize() != raw:
        raise ValueError('kl_fa_v2_hc_route2: the .HVK does not round-trip; nothing written')
    coll_only_patch(L, log)
    new = L.hvk.serialize()
    folder = os.path.dirname(zp)
    dest_folder = folder if out is None else os.path.abspath(out)
    if out is not None:
        os.makedirs(dest_folder, exist_ok=True)
        for f in os.listdir(folder):
            if os.path.join(folder, f) != zp and os.path.isfile(os.path.join(folder, f)):
                shutil.copy2(os.path.join(folder, f), dest_folder)
    dest = os.path.join(dest_folder, os.path.basename(zp))
    tmp = dest + '.tmp'
    with zipfile.ZipFile(zp) as zi, zipfile.ZipFile(tmp, 'w') as zo:
        for info in zi.infolist():
            zo.writestr(info, new if info.filename == name else zi.read(info.filename), compress_type=info.compress_type)
    os.replace(tmp, dest)
    log('  coll-only: %s written (%d -> %d bytes .HVK)' % (dest, len(raw), len(new)))
    return dest


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'walk':
        cell = float(a[a.index('--cell') + 1]) if '--cell' in a else 20.0
        step = float(a[a.index('--step') + 1]) if '--step' in a else 65.0
        drop = [a[i + 1] for i, v in enumerate(a) if v == '--drop']
        near = float(a[a.index('--near') + 1]) if '--near' in a else None
        r = walk(a[1], cell, step, drop, EXTRA_OPEN if '--extra' in a else (), near, nocam='--nocam' in a, coll_only='--coll-only' in a, skip_extra='--skip-extra' in a)
        sys.exit(0 if r['van_reached'] else 1)
    elif len(a) >= 2 and a[0] == 'test':
        import kl_fa_v2_hotcoffee as H
        if '--coll-only' not in a:         # --coll-only: ROUTE_OPEN stays as it is, the two pieces stay in the level and their collision is sunk after the build
            H.ROUTE_OPEN = tuple(H.ROUTE_OPEN) + tuple(t for t in EXTRA_OPEN if t not in H.ROUTE_OPEN)
        if '--str' in a:                # as kl_fa_v2_hotcoffee.py test --str
            import kl_fa_bank as BK
            H.STREAM = os.path.abspath(a[a.index('--str') + 1])
            BK.use_stream(H.STREAM)
        if '--coll-only' in a:
            rc = H.test(a[1], True)
            if rc == 0:
                zs = [os.path.join(r, f) for r, _d, fs in os.walk(a[1]) for f in fs if f.endswith('_Main.zip')]
                for z in zs:
                    collonly(z)
                if '--keep' not in a:
                    pass            # --coll-only needs the archive for the checks: it is always kept
            sys.exit(rc)
        sys.exit(H.test(a[1], '--keep' in a))
    elif len(a) >= 2 and a[0] == 'collonly':
        collonly(a[1], a[2] if len(a) > 2 else None)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
