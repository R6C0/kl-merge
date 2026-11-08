r"""kl_vehroutes_dm07_1108.py - DM07 (slot F06) escape van that arrives from and leaves to a logical place. 2026-11-08, OFFLINE: reads the live zip, writes a
NEW stage (zip + bots zip + base md5 + install kit); never the live files.

OWNER: "make sure all vehicles actually come from a logic place and leave to a logical place where people can shoot it if they want to"
(and: it should appear from and vanish to somewhere nobody can see or stand).

WHAT WAS WRONG (kl_vehaudit_1108, render triangles; DM07 van seen 87 %): the van's lane is z=10400 through a container yard (x -4600 .. 1100).
  ARRIVAL: it starts at x=-6000 just outside the yard's west chain-link fence and drives through the fence line x~-4600 (two panels,
           Chainlink_Fence_4m_01 / _11, z 9993..10798) at keys 50..55.
  LEAVING: after the stop (x~-2597, keys 150..180) it drives straight EAST and goes through the 44 m concrete wall SO0300_M07_ConcreteWall_1x44_02/_03
           (x 1108 / 1147, z 8300..12700, y 457..807) at keys 360..364, ending at x=1800 behind it.
WHAT IS WEST OF THE FENCE (render + walk flood, this file's check): a mud pocket x -9760 .. -4600, z ~8200 .. 12200 that no player can reach (the flood from the
  stop never gets past the fence), closed by the 2x88 concrete wall SO0300_M07_ConcreteWall_2x88_04 at x=-9759 and low walls north / south. That pocket is the
  only place on this map where a vehicle can stand where nobody can stand.
FIX (three edits, each GUESS marked):
  1. GATE. The two fence panels in the lane are hidden (gms flags |= 0x400, the 'hidden' bit): the van drives in through a gate in the fence.
     0x400 hides the RENDER only: static (.HVK type 1) placements are never looked at for that bit (static reading of kl2.exe, 2026-11-08: the type-1 path
     0x4de4b0 takes the shape record only, no node pointer; stock DD levels author collision on 0x400 objects). So the panels keep their collision:
     players cannot walk out through the gate (nothing is cut on purpose; kl_route's flood from the stop is re-run by check() and must not pass the fence);
     the van is KEY-FRAMED (type 4) and is moved by its keys, so it passes the static panels (GUESS: a key-framed body is not stopped by static collision;
     the original van already drove through both fence panels and through the wall this way). If a 0x400 panel did lose its collision, the KillBox at
     (-5832, 490, 10400) beyond the fence is still there (the map's own answer for stepping off).
  2. FAR START / END. The van now waits at (START_X, z 10400) = the west end of the pocket, 6700 from the stop instead of 3400: the arrival keys are stretched
     to it (x scaled linearly from -6000 .. PIN_X onto START_X .. PIN_X, keys past PIN_X untouched so the stop is exactly where it was), and the van
     leaves the same way (below). Visible from only a few floor cells (check() counts the reachable floor, not the spawn points).
  3. BACK OUT. The yard is closed on every other side (fence west, the 44 m wall east, walls / fence north and south), so the only logical way out is the
     gate it came in by. Drive-away keys (first .. drive()-1) are re-laid along the ARRIVAL LANE, west from the stop to START_X: the van reverses out
     (rotation keys untouched: they stay at 90.9 deg for the whole exit leg, so there is no yaw snap; the 91 -> 35 deg turn belongs to the crash keys
     from frame 500, the wreck tumbling, unchanged). The original SPEED PROFILE is kept (the new arc length is distributed by the old cumulative-length
     fraction); heights = the render floor under the lane + the offset the old keys had over it.
  The crash-piece keys (>= drive()) keep their order; x is clamped to <= CRASH_MAX_X so no piece stands in the pillar SO0100_M07_Pillar_F_06 (x 1089), and a
  piece that sat BELOW the render floor (the stock F07 wreck path, up to 20 low at the east end) is lifted to floor + 3 (GUESS: key origin = wheel level).
  They stay on the yard's flat lane strip (flood floor 389..402), not on a mud heap.
The wall is never approached: the van's east-most point is the stop (x -2574), the wall stands at 1108.
GUESSES: (a) hiding the panels hides them in game and their static collision stays (above); (b) the engine reads one position key per frame with linear
interpolation (the keys are per frame in this file: 563 position keys for 796 frames); (c) a reversing exit reads as 'logical' (DM01B precedent); the
alternative is a forward U-turn on the mud heaps (needs wider, bumpier ground than the 600 wide flat lane strip); (d) the pocket floor is only drawn, it has
no collision (no flood cell there), the van is key-framed so it needs none; (e) the stretched arrival / exit run 1.5 .. 2 times the old speed (peak per
frame printed by the stage).

usage: python kl_vehroutes_dm07_1108.py stage <live DM07 dir> <out dir>      (also: check <zip>)"""
import hashlib, math, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OLD_X = -6000.0                       # where the van used to start
START_X = -9300.0                     # west end of the unreachable mud pocket (wall at -9759, hull 130 + half a van 250 + margin): start AND end
PIN_X = -2700.0                       # arrival keys at x >= this are not touched (the stop stays exactly where it was)
LANE_Z = 10400.0
CRASH_MAX_X = 940.0                   # pillar x 1089 minus hull 130 minus a margin
LIFT = 3.0                            # a crash piece below the floor is put this far above it
HIDE = 0x400
FENCES = ('SO0301_USA_Chainlink_Fence_4m_01', 'SO0301_USA_Chainlink_Fence_4m_11')
SLOT = 'F06'
BUF = 'Scenes/Locations/F06/F06_Main.buf'
LIVE_MD5 = {'F06_Main.zip': 'e0a9e32660a2f59dbbaa733928aa40f6', 'F06_Main.bots.zip': '7e897565ff63319a4ef1a79c17fdbfa6'}


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


class Ground:
    """Render floor of the lane strip: near-horizontal triangles of the zip (kl_arrival_1107.geom), at(x, z, yref) = the highest floor point under
    yref + 120 (None if there is none)."""
    def __init__(self, zp):
        import numpy as np, kl_arrival_1107 as A
        t, o, n = A.geom(zp, region=(np.array([-12000.0, -1000.0, 9500.0]), np.array([1500.0, 2000.0, 11200.0])), log=lambda *a: None)
        t, o = np.asarray(t, np.float64), np.asarray(o)
        bad = [i for i, x in enumerate(n) if any(w in x for w in ('Mist', 'Glow', 'Backdrop', 'Distance', 'Fog', 'Smoke', 'Sky', 'Sands', 'Fence'))]
        t = t[np.isfinite(t).all(axis=(1, 2)) & (np.abs(t).max(axis=(1, 2)) < 1e5) & ~np.isin(o, bad)]
        nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        t = t[np.abs(nr[:, 1]) / (np.linalg.norm(nr, axis=1) + 1e-9) > 0.7]
        self.np, self.a, self.b, self.c = np, t[:, 0], t[:, 1], t[:, 2]

    def at(self, x, z, yref):
        np, a, b, c = self.np, self.a, self.b, self.c
        d = (b[:, 2] - c[:, 2]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 2] - c[:, 2])
        ok = np.abs(d) > 1e-9
        dd = np.where(ok, d, 1.0)
        l1 = ((b[:, 2] - c[:, 2]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z - c[:, 2])) / dd
        l2 = ((c[:, 2] - a[:, 2]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z - c[:, 2])) / dd
        l3 = 1 - l1 - l2
        ys = (l1 * a[:, 1] + l2 * b[:, 1] + l3 * c[:, 1])[ok & (l1 >= 0) & (l2 >= 0) & (l3 >= 0)]
        ys = ys[ys < yref + 120]
        return float(ys.max()) if len(ys) else None


def relay(old, first, cut, out_x=START_X):
    """old: key positions [(x, y, z)]. -> {key: x} for keys first..cut-1: the old cumulative-length fraction mapped on the straight way from the stop
    (old[first]) west to out_x (monotone, the first key = the stop, the last = out_x)."""
    seg = [0.0]
    for i in range(first + 1, cut):
        seg.append(seg[-1] + math.dist(old[i], old[i - 1]))
    tot = seg[-1] or 1.0
    x0 = old[first][0]
    return {i: x0 + (out_x - x0) * seg[j] / tot for j, i in enumerate(range(first, cut))}


def stretch_x(x):
    """Arrival: old x (-6000 .. PIN_X) -> new x (START_X .. PIN_X), linear; x >= PIN_X unchanged."""
    return x if x >= PIN_X else START_X + (x - OLD_X) * (PIN_X - START_X) / (PIN_X - OLD_X)


def peak(pos, a, b):
    return max(math.dist(pos[i], pos[i - 1]) for i in range(a + 1, b))


def build(src, log=print):
    """live zip -> (members {name: bytes} changed, report dict)."""
    import kl_fa_bots as F, kl_gms, kl_graft, kl_map_escape as ME
    B = F.Built(src, SLOT)
    sc = B.sc
    van = next(k for k in range(1, len(B.ents) + 1) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    R_, T_ = ME.Level(src).frame(sc.parent[van])
    if any(abs(T_[i]) > 1e-3 for i in range(3)) or any(abs(R_[i][j] - (i == j)) > 1e-4 for i in range(3) for j in range(3)):
        raise ValueError('the van\'s parent frame is not identity (keys are local): %r %r' % (R_, T_))
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    K = ME.VanKeys(B.scene.head, B.ents[van - 1].raw, ends, kl_graft.keys_tracks)
    cut = K.drive()
    first = max(i for i in range(150, cut) if K.pos[i][0] <= K.pos[150][0] + 40)      # the last key of the creep plateau (the stop)
    stop = K.pos[first]
    G = Ground(src)
    xs = relay(K.pos, first, cut)
    offs_ = [K.pos[i][1] - G.at(K.pos[i][0], stop[2], K.pos[i][1]) for i in range(0, first) if OLD_X <= K.pos[i][0] < PIN_X and G.at(K.pos[i][0], stop[2], K.pos[i][1]) is not None]
    off = sorted(offs_)[len(offs_) // 2]            # the height the old arrival keys had over the render floor (median)
    gy = lambda x: (G.at(x, stop[2], stop[1] + 40.0) or stop[1]) + off
    log('  van keys %d (drive %d), stop key %d at (%d, %d, %d), start/end x=%d, height over the render floor %.1f' % (K.npos, cut, first, *stop, START_X, off))
    old_peak = (peak(K.pos, 0, first), peak(K.pos, first, cut))
    head = bytearray(B.scene.head)
    keep = list(K.pos)
    n_arr = 0
    for i in range(0, first):                       # arrival: stretched back to the pocket's west end
        x = K.pos[i][0]
        if x < PIN_X:
            keep[i] = (stretch_x(x), gy(stretch_x(x)), stop[2])
            struct.pack_into('<3f', head, K.offs[5] + 12 * i, *keep[i])
            n_arr += 1
    ypos = {}
    for i in range(first + 1, cut):                 # drive-away: back out along the lane to the pocket
        ypos[i] = gy(xs[i])
        keep[i] = (xs[i], ypos[i], stop[2])
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *keep[i])
    clamped = lifted = 0
    for i in range(cut, K.npos):                    # crash pieces: keep order, keep out of the pillar, keep on the floor
        x, y, z = K.pos[i]
        nx = min(x, CRASH_MAX_X)
        g = G.at(nx, z, y)
        ny = max(y, g + LIFT) if g is not None and y < g else y
        clamped += nx != x
        lifted += ny != y
        if (nx, ny) != (x, y):
            struct.pack_into('<3f', head, K.offs[5] + 12 * i, nx, ny, z)
    new_peak = (peak(keep, 0, first), peak(keep, first, cut))
    log('  arrival keys stretched %d, per-frame peak speed arrival %.0f -> %.0f, drive-away %.0f -> %.0f' % (n_arr, old_peak[0], new_peak[0], old_peak[1], new_peak[1]))
    nrot = 0                                           # rotation keys untouched: the nose stays east, the van reverses
    # the gate: two fence panels hidden
    zf = zipfile.ZipFile(src)
    gms_name = next(n for n in zf.namelist() if n.lower().endswith('_main.gms'))
    raw = bytearray(kl_gms.unpack(zf.read(gms_name)))
    if B.scene.write()[0] != bytes(raw):
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    ents = list(kl_gms.entities(bytes(raw)))
    hid = []
    for k in range(1, len(B.ents) + 1):
        if sc.names[k] in FENCES:
            e = B.ents[k - 1]
            rec = 4 * (ents[k - 1][0] & 0xffffff)
            if struct.unpack_from('<I', raw, rec + 28)[0] != e.flags:
                raise ValueError('flags word of %s is not at record +28' % sc.names[k])
            struct.pack_into('<I', raw, rec + 28, e.flags | HIDE)
            hid.append((sc.names[k], e.ref, hex(e.flags)))
    if len(hid) != 2:
        raise ValueError('want 2 fence panels, found %d' % len(hid))
    buf = zf.read(BUF)
    if buf[:len(B.scene.head)] != B.scene.head:
        raise ValueError('the .buf head is not the scene head')
    members = {gms_name: kl_gms.pack(bytes(raw)), BUF: bytes(head) + buf[len(head):]}
    rep = dict(first=first, cut=cut, hidden=hid, clamped=clamped, lifted=lifted, start=keep[0], end=(xs[cut - 1], ypos[cut - 1], stop[2]), peak_old=old_peak, peak_new=new_peak)
    log('  %d position keys re-laid (end (%d, %d, %d)), %d crash keys clamped in x, %d lifted onto the floor, hidden %s' % (cut - 1 - first, *rep['end'], clamped, lifted, hid))
    return members, rep


def stage(live_dir, out, log=print):
    import kl_graft, kl_botsonline
    src = os.path.join(live_dir, 'F06_Main.zip')
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    base_old = md5(os.path.join(live_dir, 'F06_Main.bots.base.md5'))
    members, rep = build(src, log)
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, 'F06_Main.zip')
    zin = zipfile.ZipFile(src)
    kl_graft.write_zip(final, [(n, members[n] if n in members else zin.read(n)) for n in zin.namelist()])
    with zipfile.ZipFile(final) as a:
        if a.namelist() != zin.namelist():
            raise ValueError('member list changed')
        diff = sorted(n for n in a.namelist() if a.read(n) != zin.read(n))
    if sorted(diff) != sorted(members):
        raise ValueError('members changed %s, expected %s' % (diff, sorted(members)))
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F06_Main.bots.zip'), 'eAllTypes', SLOT, log=lambda *a: None)
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(plain + '\n')
    files = [('F06_Main.zip', LIVE_MD5['F06_Main.zip'], plain), ('F06_Main.bots.zip', LIVE_MD5['F06_Main.bots.zip'], md5(os.path.join(out, 'F06_Main.bots.zip'))),
             ('F06_Main.bots.base.md5', base_old, md5(os.path.join(out, 'F06_Main.bots.base.md5')))]
    write_kit(out, files)
    for f in files:
        log('  %-24s %s -> %s' % f)
    return files, rep


def write_kit(out, files):
    """install.py = the DM01B kit's with this map's folder, names and pins."""
    ref = r'C:\kl_build_1024\vehroutes_1108\DM01B\install.py'
    t = open(ref, encoding='utf-8').read()
    nl = chr(10)
    i, j = t.index('FILES = ['), t.index(nl + ']' + nl) + 3
    t = t[:i] + 'FILES = [   # name, live md5 before, staged md5 after' + nl + nl.join('    (%r, %r, %r),' % f for f in files) + nl + ']' + nl + t[j:]
    t = t.replace("MAP, TAG = 'DM01B', '.before-vehroutes1108'", "MAP, TAG = 'DM07', '.before-vehroutes1108dm07'")
    t = t.replace("LIVE_ZIP_MD5 = '74d3723323dc1aa03d3166b522ae5448'", 'LIVE_ZIP_MD5 = %r' % LIVE_MD5['F06_Main.zip'])
    t = t.replace("n == 'F03_Main.zip'", "n == 'F06_Main.zip'")
    t = t.replace('DM01B VAN DRIVE-AWAY 1108 (tools/kl_vehroutes_1108.py)', 'DM07 VAN GATE + REVERSE OUT 1108 (tools/kl_vehroutes_dm07_1108.py)')
    t = t.replace('F03_Main.', 'F06_Main.')
    t = t.replace('on the live DM01B files', 'on the live DM07 files')                 # docstring: this kit's map and backup tag, not DM01B's
    t = t.replace('<name>.before-vehroutes1108 NEXT', '<name>.before-vehroutes1108dm07 NEXT')
    if 'DM01B' in t or 'F03' in t:
        raise ValueError('install.py still names DM01B / F03')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 vehroutes 1108.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


VIEW_R = 7000.0


def viewers(zp):
    """-> (viewers, cells): one standing point (+0 height, the eye is added later) per 400 x 400 x 150 block of EVERY floor cell kl_route's walker reaches from the
    stop (the walkable flood: players move, so not only the spawn points), and the reached cells."""
    import kl_route as R
    run = R._Run(zp, mesh=False)
    g = run.g
    cost, _p, _e, _ed = R._search(g, g.feet((-2597.0, 397.0, 10400.0), frozenset()), None, None, frozenset(), None)
    seen = {}
    for i, j, y in cost:
        x, z = (i + .5) * R.CELL, (j + .5) * R.CELL
        seen.setdefault((int(x // 400), int(z // 400), int(y // 150)), (x, float(y), z))
    return list(seen.values()), cost


def seen_by(zp, vs, pts, log=print):
    """For each point: how many of the viewers within VIEW_R have a clear line to it (eye 170, point +100), with (a) the fence panels as walls,
    (b) the fence see-through (chain link: GUESS the engine draws it with alpha), (c) the gate open (the two hidden panels removed, the rest of the fence a wall)."""
    import numpy as np, kl_arrival_1107 as A
    t, o, n = A.geom(zp, region=(np.array([-12500.0, -1000.0, 5500.0]), np.array([3500.0, 4000.0, 15000.0])), log=lambda *a: None)
    t, o = np.asarray(t, np.float64), np.asarray(o)
    bad = [i for i, x in enumerate(n) if any(w in x for w in ('Mist', 'Glow', 'Backdrop', 'Distance', 'Fog', 'Smoke', 'Sky'))]
    ok = np.isfinite(t).all(axis=(1, 2)) & (np.abs(t).max(axis=(1, 2)) < 2e4) & ~np.isin(o, bad)
    t, o = t[ok], o[ok]

    def mesh(drop):
        ex = [k for k, x in enumerate(n) if any(w in x for w in drop)]
        m = ~np.isin(o, ex)
        return A.Mesh(t[m].astype(np.float32), o[m], n)
    var = [('fence solid', mesh(())), ('fence see-through', mesh(('Chainlink_Fence',))), ('gate open', mesh(FENCES_SHORT))]
    out = []
    for p in pts:
        q = (p[0], p[1] + 100.0, p[2])
        near = [v for v in vs if math.dist(v, q) < VIEW_R]
        row = [len(near)]
        for _nm, M in var:
            row.append(sum(1 for v in near if not A.seg_hits(M, (v[0], v[1] + 170.0, v[2]), q)))
        out.append((p, row))
        log('  view %-22s within %d: %s' % (tuple(int(c) for c in p), row[0], ', '.join('%s %d' % (nm, c) for (nm, _M), c in zip(var, row[1:]))))
    return out


FENCES_SHORT = ('Chainlink_Fence_4m_01', 'Chainlink_Fence_4m_11')


def check(zp, log=print, full=True):
    """Offline proofs on a staged zip; -> list of problems ([] = all pass). 1 render hull check of the drive (0 close samples), 2 the walk flood from the stop
    does not pass the fence (the hidden panels keep their static collision, GUESS above), 3 viewer counts (every reachable floor cell) at the start / end
    and at the stop for comparison (reported, not a pass / fail: the pocket is visible through the fence from some cells)."""
    import kl_vehroutes_1108 as V
    bad = []
    n = V.check(zp, log, True)
    log('  1 render check of the drive: %d close samples' % n)
    if n:
        bad.append('%d close samples' % n)
    if full:
        vs, cost = viewers(zp)
        import kl_route as R
        out = [(i, j) for i, j, y in cost if -9700 < (i + .5) * R.CELL < -4620 and abs((j + .5) * R.CELL - LANE_Z) < 1900]      # the pocket (the walkable ground west of the wall at -9759 is another region)
        log('  2 walk flood from the stop: %d cells, %d inside the pocket west of the fence (x -9700 .. -4620, lane +-1900)' % (len(cost), len(out)))
        if out:
            bad.append('the flood passes the fence (%d cells): the gate is open for players' % len(out))
        import numpy as np, kl_arrival_1107 as A
        B, K = V.van_keys(zp)
        pts = [tuple(K.pos[0]), tuple(K.pos[K.drive() - 1]), (-2597.0, 397.0, LANE_Z)]
        log('  3 who can see the start, the end and (for comparison) the stop; viewers = the reachable floor, one per 400 block:')
        seen_by(zp, vs, pts, log)
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3:
        stage(a[1], a[2])
    elif a[:1] == ['check'] and len(a) == 2:
        bad = check(a[1])
        print('PROBLEMS:' if bad else 'check: ok', bad)
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)
        sys.exit(2)
