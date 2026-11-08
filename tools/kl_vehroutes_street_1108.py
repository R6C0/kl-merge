r"""kl_vehroutes_street_1108.py - DM01B (Hot Coffee II, slot F03): the escape van where Dead Men has it, on the MAIN STREET north of the planter strip.
Written 2026-11-08, OFFLINE: reads the live DM01B zip, writes NEW files (never the live ones). The alternative stage is kl_vehroutes_1108.py (the van backs out
of the alley); only one of the two can be installed (both pin the same live md5).

OWNER (2026-11-08): "hot coffee 2 the car just goes through a building, put it on the other side on the wall where it normally is in dead men".

DEAD MEN SOURCE (read from M01A_Main.zip, node 05_EscapeVehicle's ZEditorSpline, raw field ZSTDOBJ[1]): the campaign car arrives from the WEST along the main
street, points (-4998,31412) (-4322,31981) (-1668,31933) (4458,31907) and STOPS at x=4458, z=31907 (it waits at (-5262,-14,30767)); TB_EscapeBox (4399,86,31396),
SceneChangerExitPoint (4533,17.5,31188), Van_Horn_Sound (4642,-4,31739). Dead Men's world frame = Hot Coffee II's (the live positions match). The spline ends at the
stop: where the campaign car goes after it is NOT in the data (no departure path), the departure below is ours.

WHAT THIS DOES (a RIGID TURN of the van's whole old drive, no re-timing, no key added or dropped):
  map (x, z) -> (CX - x, CZ - z), heading + 180 degrees. CX = 4458 + 1660 (the Dead Men stop x + the old stop plateau x), CZ = 31907 + 30800 (the Dead Men stop z +
  the old lane z). The old drive ARRIVED from the east along z=30800 to x=1660 and LEFT west; the turned drive ARRIVES from the WEST along z=31907 (x 758 -> 4458,
  as Dead Men) and LEAVES EAST along the street (to x=7518; the street's ground tiles end at x~7600). Crash-piece keys (the shot-to-pieces variants) are turned
  too and clamped to z >= 31907 (the south side holds the planter bushes). Ground is y=-20 in both the alley and the street (no y change).
  Everything that is the stop is turned with it: the van node (= key 0), PathBlockerVan, TriggerBox_RearDoors_Open, CameraTrigger01, CameraTrigger_InVan,
  EscCamera01_01, CamPos01, CamPos_InVan_FocusPoint, Gameplay!EscapeSetup!otrExitLevel, the three Trigger_POI_TheEscapeArea boxes, the POI_TheEscapeArea marker,
  Specials!JumpPoints!06_Exit, Gameplay!merc_bot_squad!AllyEscapeBox and every merc squad '051_DefendBehaviour_out*' position (the bots' escape-side posts).
  BoardingTrigger rides on the van. The .HVK key-framed placements of the van parts are turned from the old waiting pose to the new one (kl_map_escape.van_hvk).
  The bots zip is re-derived (kl_botsonline.convert, eAllTypes) and the base md5 written.
NOT TOUCHED: .oct / .rmi / .rmc (no slot id changes; .rmi boxes 29 (room 1070) and 46 (Backdrop) cover the whole new lane and the old one alike: checked), the
police spawn cameras (they watch the fight, not the van), loose parked van pieces (y -60000), every hook / ini value (nothing there names the stop: grep).
GUESSES: (1) the game moves a key-framed Havok body with its entity (the .HVK is turned either way, see van_hvk); (2) the drive-away to x=7518 reads as a
logical exit (the street is a dead end of the map there); (3) the bots' pathing around the new stop (nav mesh) is only checked offline by kl_route.
usage: python kl_vehroutes_street_1108.py stage <live DM01B dir> <out dir>      python kl_vehroutes_street_1108.py check <F03_Main.zip>"""
import hashlib, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F, kl_graft, kl_gms, kl_hvk, kl_map_escape as ME, kl_prpjoin as J, kl_fa_author as A

LIVE_MD5 = {'F03_Main.zip': '74d3723323dc1aa03d3166b522ae5448', 'F03_Main.bots.zip': '73583df1aa6b251d3c4aca7d86cebaa6',
            'F03_Main.bots.base.md5': 'c3535e34052721460900c50dae9e0811'}
DM_STOP_X, DM_STOP_Z = 4458.0, 31907.0      # Dead Men: the end of 05_EscapeVehicle's spline (read from M01A_Main.zip)
OLD_STOP_X, OLD_LANE_Z = 1660.0, 30800.0    # the live key plateau and lane
CX, CZ = DM_STOP_X + OLD_STOP_X, DM_STOP_Z + OLD_LANE_Z
CRASH_MIN_Z = DM_STOP_Z                      # crash pieces stay on the north side (the planter bushes are south)
HULL = 130.0
SLOT = 'F03'
VAN_ZIP = 'F07_Escape_Vehicle_01.zip'
# world-placed van children (names unique below the van zip's node); BoardingTrigger rides on the van
VAN_NODES = ('V_Van_00', 'PathBlockerVan', 'TriggerBox_RearDoors_Open', 'CameraTrigger01', 'CameraTrigger_InVan', 'EscCamera01_01', 'CamPos01',
             'CamPos_InVan_FocusPoint')
# FA-layer nodes that stand at the old stop: exact path tails
STOP_TAILS = ('Gameplay!EscapeSetup!otrExitLevel', 'FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly', 'FASpecials!POI!POI_TheEscapeArea', 'Specials!JumpPoints!06_Exit',
              'Gameplay!merc_bot_squad!AllyEscapeBox')
OUT_POSTS = '051_DefendBehaviour_out'        # merc squads' escape-side posts (Pos#nn below 051_DefendBehaviour_out and _out_b)
BUF = 'Scenes/Locations/F03/F03_Main.buf'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def turn_pos(p):
    return (CX - p[0], p[1], CZ - p[2])


def turn_m9(r):
    """ZGEOM[1] (stored as the 3rd, 2nd, 1st column of the frame matrix) of the same node turned 180 degrees about world Y (frame := diag(-1,1,-1) . frame)."""
    cols = [r[6:9], r[3:6], r[0:3]]                   # frame columns 0, 1, 2
    cols = [(-c[0], c[1], -c[2]) for c in cols]
    return list(cols[2]) + list(cols[1]) + list(cols[0])


def nodes_of(B):
    """-> (van top node, {van child name: node}, [stop nodes], [post nodes]) by name; raises unless every one is found exactly once."""
    sc = B.sc
    n = len(sc.names)
    top = [k for k in range(1, n) if sc.names[k].endswith(VAN_ZIP)]
    if len(top) != 1:
        raise ValueError('want one %s node, found %d' % (VAN_ZIP, len(top)))
    top = top[0]
    kids = {}
    for k in range(top, sc.end[top]):
        if sc.names[k] in VAN_NODES and 'Reflection' not in sc.path[k]:
            if sc.names[k] in kids:
                raise ValueError('%s appears twice below the van' % sc.names[k])
            kids[sc.names[k]] = k
    miss = [v for v in VAN_NODES if v not in kids]
    if miss:
        raise ValueError('van nodes missing: %r' % miss)
    stop = []
    for t in STOP_TAILS:
        hit = [k for k in range(1, n) if sc.path[k].endswith(t)]
        if len(hit) != 1:
            raise ValueError('%s: %d nodes' % (t, len(hit)))
        stop += hit
    posts = [k for k in range(1, n) if OUT_POSTS in sc.path[k] and sc.names[k].startswith('Pos#') and 'merc_bot_squad' in sc.path[k]]
    if len(posts) < 6:
        raise ValueError('only %d merc escape posts found' % len(posts))
    return top, kids, stop, posts


def van_keys(B):
    sc = B.sc
    k = next(k for k in range(1, len(B.ents) + 1) if sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k])
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    return k, ME.VanKeys(B.scene.head, B.ents[k - 1].raw, ends, kl_graft.keys_tracks)


def new_keys(K):
    """-> (positions, rotations): the whole drive and the crash keys turned (zero keys = unused, kept)."""
    cut = K.drive()
    pos = []
    for i, p in enumerate(K.pos):
        if p == (0.0, 0.0, 0.0):
            pos.append(p)
            continue
        if i < cut:
            pos.append(turn_pos(p))
        else:   # crash pieces: x turned about CX, the offset from the lane kept in sign, clamped to the north side (GUESS: debris, the spin does not matter)
            pos.append((CX - p[0], p[1], max(CRASH_MIN_Z, DM_STOP_Z + (p[2] - OLD_LANE_Z))))
    rot = [K.turned(q, 180.0) for q in K.rot]
    return pos, rot


def put(B, k, pos=None, m9=None):
    """The place() of kl_fa_author for a node of a Built: .prp ZGEOM[1] / [2] and the .gms record; the node's parents must be identity."""
    sc, e = B.sc, B.ents[k - 1]
    lab = J.labels('dd', sc.cls(k))

    def fn(us):
        if m9 is not None:
            A.setv(sc, us, lab.index('ZGEOM[1]'), [float(x) for x in m9])
        if pos is not None:
            A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
    kl_graft.edit(sc.nodes[k], 'props', fn)
    if m9 is not None:
        e.rot = struct.pack('<9f', *m9) + bytes(12)
    if pos is not None:
        e.trans = struct.pack('<3f', *pos) + bytes(4)


def turn_node(B, k, moved):
    sc, e = B.sc, B.ents[k - 1]
    t, r = struct.unpack('<3f', e.trans[:12]), struct.unpack('<9f', e.rot[:36])
    w = B.at(k)
    if any(abs(w[i] - t[i]) > 0.5 for i in range(3)):
        raise ValueError('%s: its parents are not identity at the origin (local %r, world %r)' % (sc.path[k], t, w))
    put(B, k, turn_pos(t), turn_m9(r))
    moved.append((sc.names[k], tuple(round(x) for x in t), tuple(round(x) for x in turn_pos(t))))


def build(src, log=print):
    """live zip -> {member: bytes} of the changed members + a report."""
    B = F.Built(src)
    zf = zipfile.ZipFile(src)
    orig_gms = kl_gms.unpack(zf.read([n for n in zf.namelist() if n.lower().endswith('_main.gms')][0]))
    if B.scene.write()[0] != orig_gms:
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    prp_name = next(n for n in zf.namelist() if n.lower().endswith('_main.prp'))
    if B.sc.p.serialize() != zf.read(prp_name):
        raise ValueError('the .prp does not round-trip (stop: nothing was written)')
    top, kids, stop, posts = nodes_of(B)
    vk, K = van_keys(B)
    pos, rot = new_keys(K)
    head = bytearray(B.scene.head)
    for i, p in enumerate(pos):
        struct.pack_into('<3f', head, K.offs[5] + 12 * i, *p)
    for i, q in enumerate(rot):
        struct.pack_into('<4h', head, K.offs[2] + 8 * i, *q)
    old_pose = (K.pos[K.f2p[0]], K.yaw(K.rot[K.f2r[0]]))
    new_pose = (pos[K.f2p[0]], K.yaw(rot[K.f2r[0]]))
    moved = []
    for n in VAN_NODES:
        k = kids[n]
        if n == 'V_Van_00':                                  # the node's own place = the key of frame 0
            r = struct.unpack('<9f', B.ents[k - 1].rot[:36])
            put(B, k, pos[K.f2p[0]], turn_m9(r))
            moved.append((n, tuple(round(x) for x in K.pos[K.f2p[0]]), tuple(round(x) for x in pos[K.f2p[0]])))
        else:
            turn_node(B, k, moved)
    for k in stop + posts:
        turn_node(B, k, moved)
    refs = lambda k: {B.ents[j - 1].ref for j in range(k, B.sc.end[k])}
    rep = dict(hvk=dict(static=[], van=sorted(refs(kids['V_Van_00'])), old=[list(old_pose[0]), old_pose[1]], new=[list(new_pose[0]), new_pose[1]]))
    gms, _buf = B.scene.write()
    out = {}
    out[prp_name] = B.sc.p.serialize()
    out[prp_name[:-4] + '.gms'] = kl_gms.pack(gms)
    buf = zf.read(BUF)
    if buf[:len(B.scene.head)] != B.scene.head:
        raise ValueError('the .buf head is not the scene head')
    out[BUF] = bytes(head) + buf[len(head):]
    hn = next(n for n in zf.namelist() if n.lower().endswith('.hvk'))
    hv = kl_hvk.Hvk(zf.read(hn))
    if hv.serialize() != zf.read(hn):
        log('  note: the .HVK does not round-trip byte for byte; its van placements are NOT rewritten (stop and look)')
        raise ValueError('the .HVK does not round-trip')
    ME.van_hvk(hv, rep, log)
    out[hn] = hv.serialize()
    log('kl_vehroutes_street_1108: %d keys turned (%d drive), %d nodes moved, van now waits at (%d, %d, %d) and stops at x=%d' % (
        K.npos, K.drive(), len(moved), *pos[K.f2p[0]], DM_STOP_X))
    return out, moved, rep


def write(src, dst, log=print):
    out, moved, rep = build(src, log)
    zin = zipfile.ZipFile(src)
    members = [(n, out[n] if n in out else zin.read(n)) for n in zin.namelist()]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    return moved, rep


def check(zp, log=print, summary=True):
    """The drive turned, against RENDER triangles (kl_vehroutes_1108.check, 0 wanted), and: the stop inside the street, the drive within the street's ground."""
    import kl_vehroutes_1108 as V
    bad = V.check(zp, log, summary)
    B = F.Built(zp)
    _k, K = van_keys(B)
    pts = [p for p in K.pos if p != (0.0, 0.0, 0.0)]
    lo, hi = min(p[0] for p in pts[:K.drive()]), max(p[0] for p in pts[:K.drive()])
    log('  drive x %d..%d at z %d (street ground x 200..7600, z 31600..33600)' % (lo, hi, pts[0][2]))
    return bad


def stage(live_dir, out, log=print):
    import kl_botsonline
    src = os.path.join(live_dir, 'F03_Main.zip')
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, 'F03_Main.zip')
    write(src, final, log)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F03_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F03_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = [(n, LIVE_MD5[n], md5(os.path.join(out, n))) for n in LIVE_MD5]
    ref = r'C:\kl_build_1024\vehroutes_1108\DM01B\install.py'
    t = open(ref, encoding='utf-8').read()
    nl = chr(10)
    i, j = t.index('FILES = ['), t.index(nl + ']' + nl) + 3
    t = t[:i] + 'FILES = [   # name, live md5 before, staged md5 after' + nl + nl.join('    (%r, %r, %r),' % f for f in files) + nl + ']' + nl + t[j:]
    t = t.replace('.before-vehroutes1108', '.before-vehroutes1108street').replace('DM01B VAN DRIVE-AWAY 1108 (tools/kl_vehroutes_1108.py)',
                                                                                    'DM01B VAN ON THE MAIN STREET 1108 (tools/kl_vehroutes_street_1108.py; the alternative of tools/kl_vehroutes_1108.py: install ONE)')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    open(os.path.join(out, 'INSTALL DM01B vehroutes street 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + cr + nl + 'pause' + cr + nl)
    open(os.path.join(out, 'UNDO DM01B vehroutes street 1108.bat'), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py" --undo' + cr + nl + 'pause' + cr + nl)
    for f in files:
        log('  %-24s %s -> %s' % f)
    return files


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3:
        stage(a[1], a[2])
    elif a[:1] == ['check'] and len(a) == 2:
        print('close samples:', check(a[1]))
    else:
        print(__doc__)
        sys.exit(2)
