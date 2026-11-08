r"""kl_vehroutes_dm07_1108.py - DM07 (slot F06) escape van that arrives from and leaves to a logical place. 2026-11-08, OFFLINE: reads the live zip, writes a
NEW stage (zip + bots zip + base md5 + install kit); never the live files.

OWNER: "make sure all vehicles actually come from a logic place and leave to a logical place where people can shoot it if they want to".

WHAT WAS WRONG (kl_vehaudit_1108, render triangles; DM07 van seen 87 %): the van's lane is z=10400 through a container yard.
  ARRIVAL: it starts at x=-6000 OUTSIDE the yard and drives through the chain-link fence line x~-4600 (two panels, Chainlink_Fence_4m_01 / _11,
           z 9993..10798) at keys 50..55.
  LEAVING: after the stop (x~-2597, keys 150..180) it drives straight EAST and goes through the 44 m concrete wall SO0300_M07_ConcreteWall_1x44_02/_03
           (x 1108 / 1147, z 8300..12700, y 457..807) at keys 360..364, ending at x=1800 behind it.
FIX (two edits, both marked GUESS where they are):
  1. GATE. The two fence panels in the lane are hidden (gms flags |= 0x400, the stock 'hidden' bit that kl_dm02fix_1108 / kl_dm02door_1108 use; render only:
     their collision stays in the .HVK, GUESS that an invisible 8 m stretch of a boundary fence nobody walks to is harmless). The van now comes through a
     gate in the fence from the open ground outside, and leaves through the same gate.
  2. BACK OUT. The yard is closed on every other side (fence west, the 44 m wall east, walls / fence north and south), so the only logical way out is the
     gate it came in by. Drive-away keys (first .. drive()-1) are re-laid along the ARRIVAL LANE, west from the stop to x=OUT_X (-6000, where it came from):
     the van reverses out (rotation keys untouched, nose stays east). The original SPEED PROFILE is kept (the new arc length is distributed by the old
     cumulative-length fraction), height = the arrival lane's own keys at the same x (that lane is known flat and clear; a forward U-turn in the yard was tried
     and rejected: the yard floor is a mud-heap tile pattern with pits, 388..459 high, see re/vehicle_routes_1108.md).
  The crash-piece keys (>= drive()) keep their order; only x is clamped to <= CRASH_MAX_X so no piece stands in the pillar SO0100_M07_Pillar_F_06 (x 1089).
  The wall is never approached: the van's east-most point is the stop (x -2574), the wall stands at 1108.
Everything else (arrival, stop, boarding, bounds, bot boarding, cameras) is unchanged.
GUESSES: (a) that hiding the panels (flag 0x400) hides them in game and that a hidden panel's collision staying is harmless; (b) the engine reads one
position key per frame with linear interpolation (the keys are per frame in this file: 563 position keys for 796 frames); (c) that a reversing exit reads as
'logical' (DM01B precedent); the alternative is a forward U-turn on the mud heaps (needs wider, bumpier ground than the 600 wide flat lane strip).

usage: python kl_vehroutes_dm07_1108.py stage <live DM07 dir> <out dir>      (also: check <zip>)"""
import hashlib, math, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT_X = -6000.0                       # where the van came from
CRASH_MAX_X = 940.0                   # pillar x 1089 minus hull 130 minus a margin
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


def arrival_y(pos, first):
    """-> f(x): the lane height at x from the arrival keys 0..first (x rises along them), flat-extended at both ends."""
    pts = sorted({(p[0], p[1]) for p in pos[:first + 1]})

    def f(x):
        if x <= pts[0][0]:
            return pts[0][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                return y0 + (y1 - y0) * ((x - x0) / ((x1 - x0) or 1.0))
        return pts[-1][1]
    return f


def relay(old, first, cut):
    """old: key positions [(x, y, z)]. -> {key: x} for keys first..cut-1: the old cumulative-length fraction mapped on the straight way from the stop
    (old[first]) west to OUT_X (monotone, the first key = the stop, the last = OUT_X)."""
    seg = [0.0]
    for i in range(first + 1, cut):
        seg.append(seg[-1] + math.dist(old[i], old[i - 1]))
    tot = seg[-1] or 1.0
    x0 = old[first][0]
    return {i: x0 + (OUT_X - x0) * seg[j] / tot for j, i in enumerate(range(first, cut))}


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
    xs = relay(K.pos, first, cut)
    yf = arrival_y(K.pos, first)
    log('  van keys %d (drive %d), stop key %d at (%d, %d, %d), reverse out to x=%d' % (K.npos, cut, first, *stop, OUT_X))
    head = bytearray(B.scene.head)
    ypos = {}
    for i in range(first + 1, cut):
        ypos[i] = yf(xs[i])
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, xs[i], ypos[i], stop[2])
    clamped = 0
    for i in range(cut, K.npos):                       # crash pieces: keep order, keep out of the pillar
        x, y, z = K.pos[i]
        if x > CRASH_MAX_X:
            struct.pack_into('<3f', head, K.offs[5] + 12 * i, CRASH_MAX_X, y, z)
            clamped += 1
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
    rep = dict(first=first, cut=cut, hidden=hid, clamped=clamped, end=(xs[cut - 1], ypos[cut - 1], stop[2]))
    log('  %d position keys re-laid (end (%d, %d, %d)), %d crash keys clamped, hidden %s' % (cut - 1 - first, *rep['end'], clamped, hid))
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
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 vehroutes 1108.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def check(zp, log=print):
    import kl_vehroutes_1108 as V
    return V.check(zp, log, True)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3:
        stage(a[1], a[2])
    elif a[:1] == ['check'] and len(a) == 2:
        print('close samples:', check(a[1]))
    else:
        print(__doc__)
        sys.exit(2)
