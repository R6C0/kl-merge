r"""kl_dm02coop_1109.py - DM02 (Late Night Opening, slot F02): the three co-op SHUTTERS that really block and really open. 2026-11-09. OFFLINE:
reads the live DM02 zips, writes a stage; nothing is installed, the game is not started.

OWNER (2026-11-09, "try it please"): the three Atrium_201a roller shutters (RollerShutterA_03/_02/_01, REF 24710/24711/24712) are open from round
start since 10-26 because their collision was STATIC (a type-1 placement is built into a world list shape at load, nothing can remove it:
re/engine_facts.md, kl_dm02fix_1108 coop VERDICT). This builds the unproven alternative that verdict named: a KEY-FRAMED (type 4) body.

WHAT CHANGES (the three shutter entities in place; NO entity added or removed, so no slot id moves and .oct/.rmi/.rmc/.prm/.MAT/.TEX stay byte for byte):
 1. each shutter ZSTDOBJ becomes a keyed object like the kick-door leaf 'Door' (kl_interact_graft.make_door): flags | 0x200000, a 64-byte raw KEYS block
    (the F07 loading-bay shutter's block, FACT: a MatPosAnim 'OpenShutter' of the stock F07 shutter group rises 0..100 and falls 100..200), its own copy of the
    KEYS tables in the .buf head with the position keys rewritten to THIS shutter (absolute local translation: x, z of the node; y = node y + LIFT * the F07 profile)
    and both rotation keys = the node's own orientation (quaternion, scale 32512, FACT from the F07 camera keys: yaw -90 = (0,-22989,0,22989));
 2. a MatPosAnim controller 'Activate' (the kick-door leaf's, cloned from a live DM02 KL_Door_N\Door) on each shutter node;
 3. the .HVK: one type-4 shape per shutter, bound by REF, a 6.4 x 3.31 m slab 6 cm thick in the node frame (the F03 kick-door leaf shape, vertices from the model box);
    appended behind every existing shape: the static list, its order and its MOPP codes are untouched (static count 2777 asserted, kl_mopp statics equal);
 4. KLCoopN!Open (DeactivateGeom on the shutter) becomes a MatPosAnimProxy frames 0..100 on the shutter leaf (the F03 kick-door proxy's form, cloned from a live one);
 5. KLShops_OpenNow keeps only the two shop frontages (REF 24709, 26082) = kl_dm02fix_1108.part_coop_prp (the SoloLift prompt is enabled there too).

VARIANTS (--variant):
 timer  (DEFAULT, safest) every co-op trigger is cut from the shutters (CoopAirlock field 23 and SoloLift lists emptied, SoloLift prompt off) and a second
        TriggerDelay2 on KLShops_OpenTimer (the node the AIMonitor starts at round start) fires KLCoopN!Pathblocker + KLCoopN!Open after --delay seconds
        (default 90). Needs nothing from the players. A shutter is therefore triggered ONCE (a second trigger would replay frames 0..100 = drop and rise again).
 coop   OpenNow reduced, SoloLift enabled, CoopAirlock lists kept: two players in the boxes (online / Arcade) or one 'Lift Door' (solo) open them. No timer.
Both variants are built; install.py --variant picks one (default timer).

GUESSes (each also marked in the code): see GUESSES below and the README the stage writes. Nothing here has run in the game.

usage (from tools/):
  python kl_dm02coop_1109.py build --variant timer|coop [--delay 90] --out <dir> [--live <F02_Main.zip>]    one zip + bots zip + md5 sidecar
  python kl_dm02coop_1109.py stage [--out C:\kl_build_1024\dm02coop_1109] [--live <Maps\DM02>]               both variants + install.py / UNDO.bat / README.txt
  python kl_dm02coop_1109.py check <zip> [--live <F02_Main.zip>] [--variant timer]                           offline checks of a built zip
"""
import collections, hashlib, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_hvk, kl_mopp
import kl_fa_bots as F
import kl_interact_graft as IG
import kl_map_escape as ME
import kl_botsonline
import kl_dm02fix_1108 as FIX

GAME = FIX.GAME
MAPDIR = FIX.MAPDIR
OUT = r'C:\kl_build_1024\dm02coop_1109'
TAG = '.before-dm02coop1109'
SHUTTER_REFS = FIX.SHUTTER_REFS                      # 24710, 24711, 24712 (Atrium_201a RollerShutterA_03 / _02 / _01)
SHOP_REFS = FIX.SHOP_REFS
LIVE_PIN = 'bd119e9c9fc3320f582daf756f7b26b8'        # live F02_Main.zip 2026-11-09 (dm02fix -> dm02door)
LIVE_BOTS_PIN = 'a5068fa013c78089e751e49add11614f'   # live F02_Main.bots.zip
LIVE_BASE_PIN = 'bd119e9c9fc3320f582daf756f7b26b8'   # F02_Main.bots.base.md5 text
VARIANTS = ('timer', 'coop')
DEFAULT_VARIANT = 'timer'
DEFAULT_DELAY = 90.0                                  # seconds after round start (timer variant); GUESS: the owner's taste, README says how to change it

KEY_DONOR = 'F07'                                     # stock level whose shutter group carries the lift keys
KEY_NODE = 10013                                      # F07 SO1000_F07_WallB_LoadingBay_Shutter_02 (group, MatPosAnim OpenShutter 0..100)
KEYS_AT = IG.KEYS_AT                                  # 40: the six table offsets in the 64-byte raw block
QSCALE = 32512                                        # identity rotation key = (0, 0, 0, 32512)
LIFT = 300.0                                          # cm the shutter body rises (opening is 331 high; the player is ~180). GUESS: the rest hides in the slab above
OPEN_FRAMES = (0, 82)                                 # the proxy plays 0..peak of the F07 profile (rise only; the keys fall again after 83)
HEIGHT_M, WIDTH_M, THICK_M = 3.31, 6.40, 0.06         # the slab (the model box is x 0..640, y 0..331, z 0 for all four RollerShutterA models, FACT d14 probe)
FLAG_REAL = 0x200000                                  # the engine gives a ZSTDOBJ a runtime object with this flag or raw data (kl_scene)

GUESSES = [
    'a ZSTDOBJ already listed in the .oct trees (the shutter is) that gets raw KEYS + MatPosAnim still draws and rises (the kick-door leaf is unlisted, pool group 2, 0x44000: not copied here)',
    'the type-4 body bound by REF follows the keyed node exactly like the kick-door leaf and the F07 shutter (a key-framed body moves with the node of its entity)',
    'the F07 KEYS tables (bit widths, frame tables) are valid for another node: only the pos keys (12 bytes each) and the 2 rot keys (8 bytes each) are rewritten',
    'MatPosAnim sets the node ABSOLUTELY (local translation + quaternion from the keys): FACT for the F07 camera, the van and the shutter keys equal their entities',
    'a MatPosAnimProxy on KLCoopN!Open reached by the CoopAirlock list / SoloLift PlayerAction / TriggerDelay2 plays the leaf once (the kick doors are reached the same way)',
    'a second TriggerDelay2 controller on KLShops_OpenTimer fires with the first (F07 stock has two MatPosAnim on one node; two TriggerDelay2 on one node: unseen)',
    'a retrigger replays frames 0..100 (the shutter would drop and rise again); the timer variant has a single trigger, the coop variant relies on the airlock being one-shot',
    'LIFT 300 leaves 31 cm of the slab in the top of the 331 cm doorway (above every player); the model rises into the floor slab above and is hidden by it',
    'the Pathblocker of KLCoopN is toggled by the same message as Open (as the airlock list does)',
]


def md5(p):
    return FIX.md5(p)


def quat(R):
    """Quaternion (x, y, z, w) int16 x4, scale QSCALE, of the 3x3 R whose COLUMNS are the node's axes in the parent (kl_fa_bots.frames form). Checked against
    the F07 camera: R columns (0,0,1),(0,1,0),(-1,0,0) = yaw -90 -> (0, -22989, 0, 22989) (= kl_map_escape.VanKeys.yaw convention)."""
    tr = R[0][0] + R[1][1] + R[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (R[2][1] - R[1][2]) / s, (R[0][2] - R[2][0]) / s, (R[1][0] - R[0][1]) / s
    elif R[0][0] > R[1][1] and R[0][0] > R[2][2]:
        s = math.sqrt(1.0 + R[0][0] - R[1][1] - R[2][2]) * 2
        w, x, y, z = (R[2][1] - R[1][2]) / s, 0.25 * s, (R[0][1] + R[1][0]) / s, (R[0][2] + R[2][0]) / s
    elif R[1][1] > R[2][2]:
        s = math.sqrt(1.0 + R[1][1] - R[0][0] - R[2][2]) * 2
        w, x, y, z = (R[0][2] - R[2][0]) / s, (R[0][1] + R[1][0]) / s, 0.25 * s, (R[1][2] + R[2][1]) / s
    else:
        s = math.sqrt(1.0 + R[2][2] - R[0][0] - R[1][1]) * 2
        w, x, y, z = (R[1][0] - R[0][1]) / s, (R[0][2] + R[2][0]) / s, (R[1][2] + R[2][1]) / s, 0.25 * s
    n = math.sqrt(x * x + y * y + z * z + w * w)
    return tuple(max(-32767, min(32767, int(round(c / n * QSCALE)))) for c in (x, y, z, w))


def set_int(u, v):
    """The integer unit u (a list of one token) with the value v, same token type."""
    op = u[0][0]
    fmt = {0x09: '<I', 0x08: '<H', 0x05: '<B', 0x06: '<B', 0x07: '<B'}[op]
    return [(op, struct.pack(fmt, v))]


def shutter_nodes(B):
    out = {}
    for k in range(1, len(B.ents) + 1):
        if B.ents[k - 1].ref in SHUTTER_REFS:
            out[B.ents[k - 1].ref] = k
    if sorted(out) != sorted(SHUTTER_REFS):
        raise ValueError('shutters %s not all found' % sorted(out))
    for r, k in out.items():
        e = B.ents[k - 1]
        Rm, T = B.fr[B.ents[B.sc.parent[k] - 1]] if B.sc.parent[k] else (None, None)
        if e.tid != 0x200002 or e.raw is not None or B.sc.nodes[k]['ctrls']:
            raise ValueError('shutter %d is not a plain ZSTDOBJ without raw or controllers' % r)
        if Rm is None or any(abs(Rm[i][j] - (i == j)) > 1e-6 for i in range(3) for j in range(3)) or any(abs(t) > 1e-3 for t in T):
            raise ValueError('shutter %d: the parent frame is not the identity (keys are absolute local)' % r)
    return out


def key_donor():
    don = IG.Donor.get(KEY_DONOR)
    e = don.ents[KEY_NODE - 1]
    ends = sorted({o for x in don.ents if x.raw for _p, oo in kl_graft.keys_tracks(x.raw) for o in oo} | {len(don.head)})
    K = ME.VanKeys(don.head, e.raw, ends, kl_graft.keys_tracks)
    offs = K.offs
    lo, hi = min(offs), next(x for x in ends if x > max(offs))
    ys = [K.pos[K.f2p[f]][1] for f in range(K.frames)]
    a = 0
    b = max(range(K.frames), key=lambda f: ys[f])         # FACT (probe e7): the F07 profile rises 0..82 to 290 cm, then falls back by ~165 (a bounce)
    if any(ys[i + 1] < ys[i] - 1e-6 for i in range(a, b)) or ys[b] - ys[a] < 100.0 or b != OPEN_FRAMES[1]:
        raise ValueError('F07 keys: frames %d..%d are not a rising lift (%.1f -> %.1f), peak at %d' % (a, OPEN_FRAMES[1], ys[a], ys[OPEN_FRAMES[1]], b))
    return dict(don=don, K=K, raw=bytes(e.raw), offs=offs, lo=lo, hi=hi, rise=ys[b] - ys[a], y0=ys[a])


def put_keys(head, kd, pos, q):
    """Append one copy of the KEYS region to the head (16-aligned): -> (new head, kbase, the raw block). The pos keys of the copy = pos + LIFT * profile,
    both rotation keys = q."""
    head = bytearray(head)
    head += bytes(-len(head) % 16)
    kbase = len(head)
    head += kd['don'].head[kd['lo']:kd['hi']]
    K, offs, lo = kd['K'], kd['offs'], kd['lo']
    for i, p in enumerate(K.pos):
        y = pos[1] + (p[1] - kd['y0']) * (LIFT / kd['rise'])
        struct.pack_into('<3f', head, kbase + offs[5] - lo + 12 * i, pos[0], y, pos[2])
    for i in range(K.nrot):
        struct.pack_into('<4h', head, kbase + offs[2] - lo + 8 * i, *q)
    raw = bytearray(kd['raw'])
    for i, o in enumerate(offs):
        struct.pack_into('<I', raw, KEYS_AT + 4 * i, kbase + o - lo)
    return bytes(head), kbase, bytes(raw)


def templates(B):
    """(MatPosAnim token pair of a live kick-door leaf 'Door', MatPosAnimProxy token pair of a live kick-door proxy)."""
    sc = B.sc
    leaf = proxy = None
    for k in range(1, len(sc.names)):
        for nm, body in sc.nodes[k]['ctrls']:
            key = sc.p.key(nm)
            if key == 'MatPosAnim' and sc.names[k] == 'Door' and leaf is None:
                v = [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])]
                if v[0] == 'Activate' and v[13] == v[14] == 4294967295:
                    leaf = (nm, list(body))
            if key == 'MatPosAnimProxy' and sc.names[k].startswith('KickableDoor_Proxy_Variation01') and proxy is None:
                proxy = (nm, list(body))
    if leaf is None or proxy is None:
        raise ValueError('no kick-door MatPosAnim leaf / MatPosAnimProxy template in this DM02')
    return leaf, proxy


def part_prp(B, variant, delay, rep):
    """Everything in the .prp. In place on B.sc."""
    sc = B.sc
    ent = shutter_nodes(B)
    leaf_t, proxy_t = templates(B)
    node = {n: k for k in range(1, len(sc.names)) for n in [sc.names[k]]}
    # 1. KLShops_OpenNow -> 2 frontages; SoloLift prompt on (a no-op for the timer variant, undone below)
    FIX.part_coop_prp(B, rep)
    opens = [k for k in range(1, len(sc.names)) if sc.names[k].startswith('KLCoop') and sc.names[k].endswith('!Open')]
    pbl = {sc.names[k][:7]: k for k in range(1, len(sc.names)) if sc.names[k].startswith('KLCoop') and sc.names[k].endswith('!Pathblocker')}
    # 2. the Open nodes: DeactivateGeom -> MatPosAnimProxy on the shutter leaf
    shut_of = {}
    for k in opens:
        i = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'DeactivateGeom']
        if len(i) != 1 or len(sc.nodes[k]['ctrls']) != 1:
            raise ValueError('%s: want exactly one DeactivateGeom' % sc.names[k])
        tg = kl_fa.value(sc, kl_fa.units(sc.nodes[k]['ctrls'][i[0]][1][1:-1])[1])
        if len(tg) != 1:
            raise ValueError('%s: %d targets' % (sc.names[k], len(tg)))
        shut_of[k] = tg[0]
        body = list(proxy_t[1])

        def fp(us, tg=tg):
            if len(us) != 8:
                raise ValueError('MatPosAnimProxy has %d fields (want 8)' % len(us))
            us[1] = set_int(us[1], OPEN_FRAMES[0])
            us[2] = set_int(us[2], OPEN_FRAMES[1])
            us[3] = kl_fa._refs(sc, tg)
            us[5] = kl_fa._refs(sc, [])
        sc.nodes[k]['ctrls'][i[0]] = (proxy_t[0], body)
        kl_fa.edit(sc, k, i[0], fp)
    if sorted(sc.path[ent[r]] for r in SHUTTER_REFS) != sorted(shut_of.values()):
        raise ValueError('the Open nodes do not name the three shutters')
    # 3. the MatPosAnim on each shutter node
    for r in SHUTTER_REFS:
        sc.nodes[ent[r]]['ctrls'].append((leaf_t[0], list(leaf_t[1])))
    rep['prp'] = collections.OrderedDict(open_nodes=[sc.names[k] for k in opens], proxy_frames=list(OPEN_FRAMES), shutters_keyed=sorted(SHUTTER_REFS))
    # 4. variant
    ls = [(k, i) for k in range(1, len(sc.names)) for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'CoopAirlock']
    hits = [k for k in range(1, len(sc.names)) if sc.names[k].endswith('!SoloLift')]
    if variant == 'timer':
        for k, i in ls:                                   # field 23 = completion list [Pathblocker, Open] -> nothing
            def fa(us):
                if len(us) != 28 or len(us[23]) != 3:
                    raise ValueError('CoopAirlock: field 23 is not [Pathblocker, Open]')
                us[23] = kl_fa._refs(sc, [])
            kl_fa.edit(sc, k, i, fa)
        for k in hits:
            j = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'PlayerAction'][0]

            def fs(us):
                us[1] = kl_fa._refs(sc, [])
                us[8] = [(6, bytes([0]))]                 # prompt off again
            kl_fa.edit(sc, k, j, fs)
        k = node['KLShops_OpenTimer']
        j = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'TriggerDelay2']
        if len(j) != 1:
            raise ValueError('KLShops_OpenTimer: %d TriggerDelay2' % len(j))
        sc.nodes[k]['ctrls'].append((sc.nodes[k]['ctrls'][j[0]][0], list(sc.nodes[k]['ctrls'][j[0]][1])))

        def ft(us):
            if len(us) != 5 or kl_fa.value(sc, us[0]) != 1.0:
                raise ValueError('KLShops_OpenTimer is not [1.0, 0, -1, 0, list]')
            us[0] = [(0x0a, struct.pack('<f', delay))]
            us[4] = kl_fa._refs(sc, [sc.path[x] for n in (1, 2, 3) for x in (pbl['KLCoop%d' % n], next(o for o in opens if sc.names[o].startswith('KLCoop%d' % n)))])
        kl_fa.edit(sc, k, len(sc.nodes[k]['ctrls']) - 1, ft)
        rep['variant_prp'] = 'timer: %.0f s, CoopAirlock field 23 and SoloLift lists emptied, SoloLift prompt off' % delay
    else:
        rep['variant_prp'] = 'coop: CoopAirlock lists kept, SoloLift prompt on, no timer'
    prp = sc.p.serialize()
    if F.Prp(prp).serialize() != prp:
        raise ValueError('the patched .prp does not round-trip')
    return prp, ent


def part_scene(B, ent, kd, rep):
    """The .gms / .buf: flags + raw + the three key copies. -> (gms, buf)."""
    A = B.scene
    slot0 = A.slots()
    info = []
    for r in SHUTTER_REFS:
        e = B.ents[ent[r] - 1]
        R, T = B.fr[e]
        q = quat(R)
        A.head, kbase, raw = put_keys(A.head, kd, T, q)
        e.flags |= FLAG_REAL
        e.raw = raw
        info.append(dict(ref=r, node=ent[r], at=[round(v, 3) for v in T], quat=list(q), kbase=kbase))
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    gms, buf = A.write()
    if A.slots() != slot0 or [e.name for e in A.entities()] != [e.name for e in B.ents]:
        raise ValueError('slot ids / entity order changed')
    rep['keys'] = info
    return kl_gms.pack(gms), buf


def part_hvk(B, ent, rep):
    h = kl_hvk.Hvk(B['.HVK'])
    n0, order0 = h.static_count(), [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]
    if any(kl_hvk.ref(i) in SHUTTER_REFS for s in h.shapes for i in s.inst):
        raise ValueError('a shutter REF is in the .HVK already')
    dd = IG.Donor.get(IG.DOOR_DONOR)
    ds = dd.hvk.shapes[IG.DOOR_SHAPE]
    leaf = dd.ent(IG.DOOR_LEAF)
    di = next(i for i in ds.inst if kl_hvk.ref(i) == leaf.ref)
    if ds.type != kl_hvk.KEYFRAMED or len(ds.verts) // 12 != 8:
        raise ValueError('the donor door shape is not the 8-vertex type-4 slab')
    x0, x1, y0, y1, zp, zm = 0.0, WIDTH_M, 0.0, HEIGHT_M, THICK_M / 2, -THICK_M / 2
    vv = []                                              # the donor slab's vertex ORDER (as kl_interact_graft own-leaf)
    for xx, yy, zz in ((x1, y1, zp), (x0, y1, zp), (x0, y1, zm), (x1, y1, zm), (x1, y0, zp), (x1, y0, zm), (x0, y0, zm), (x0, y0, zp)):
        vv += [xx, yy, zz]
    for r in sorted(SHUTTER_REFS):
        e = B.ents[ent[r] - 1]
        R, T = B.fr[e]
        i = bytearray(di)
        struct.pack_into('<3f', i, 0, *(c / 100.0 for c in T))
        struct.pack_into('<9f', i, 12, *(R[a][b] for a in range(3) for b in range(3)))      # row-major, columns = the node's axes (as make_door)
        struct.pack_into('<I', i, 0x30, r)
        sh = ds.clone([bytes(i)], [])
        sh.verts = struct.pack('<24f', *vv)
        h.shapes.append(sh)
    data = h.serialize()
    h2 = kl_hvk.Hvk(data)
    if h2.serialize() != data or h2.static_count() != n0 or kl_mopp.statics(h2) != order0:
        raise ValueError('.HVK read-back differs')
    rep['hvk'] = collections.OrderedDict(static=n0, added_type4=sorted(SHUTTER_REFS), bytes=(len(B['.HVK']), len(data)))
    return data


def build(live, outdir, variant=DEFAULT_VARIANT, delay=DEFAULT_DELAY, log=print):
    if variant not in VARIANTS:
        raise ValueError('variant %s' % variant)
    B = F.Built(live, 'F02')
    kd = key_donor()
    rep = collections.OrderedDict(variant=variant, delay=delay, live=live, live_md5=md5(live))
    prp, ent = part_prp(B, variant, delay, rep)
    gms, buf = part_scene(B, ent, kd, rep)
    hvk = part_hvk(B, ent, rep)
    files = dict(B.files)
    files[B.ext['.prp']], files[B.ext['.gms']], files[B.ext['.buf']], files[B.ext['.HVK']] = prp, gms, buf, hvk
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F02_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    want = {'F02_Main.prp', 'F02_Main.gms', 'F02_Main.buf', 'F02_Main.HVK'}
    if set(diff) != want:
        raise ValueError('members changed %s, expected %s' % (diff, sorted(want)))
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
    with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
    log('dm02coop_1109 %s -> %s (%s) members %s' % (variant, plain, rep['out_md5'], diff))
    return rep


# ---------------------------------------------------------------- checks
def _ctrl_map(B):
    """{node path: [(controller key, values)]} for every node, plus {node path: node values}."""
    sc = B.sc
    c, p = {}, {}
    for k in range(1, len(sc.names)):
        c[sc.path[k]] = [(sc.p.key(nm), [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])]) for nm, body in sc.nodes[k]['ctrls']]
        p[sc.path[k]] = kl_fa.node_values(sc, k)
    return c, p


def hvk_added_only(zp_in, zp_out, added_refs):
    """Shape-by-shape: every shape record of the old .HVK is identical and in place (static list, order, MOPP codes, instances), the new one has only
    `added_refs` more, each a single type-4 placement; box equal. -> problems."""
    def load(zp):
        with zipfile.ZipFile(zp) as z:
            return kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))
    a, b = load(zp_in), load(zp_out)
    bad = []
    sg = lambda s: (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub), tuple(bytes(i) for i in s.inst), tuple(s.mopp))
    n = len(a.shapes)
    if len(b.shapes) != n + len(added_refs):
        bad.append('shape count %d -> %d' % (n, len(b.shapes)))
    elif [sg(s) for s in a.shapes] != [sg(s) for s in b.shapes[:n]]:
        bad.append('an old shape record changed')
    new = b.shapes[n:]
    if sorted(kl_hvk.ref(i) for s in new for i in s.inst) != sorted(added_refs) or any(s.type != kl_hvk.KEYFRAMED or len(s.inst) != 1 for s in new):
        bad.append('the added shapes are not one type-4 placement per ref %s' % sorted(added_refs))
    if a.box != b.box or a.static_count() != b.static_count() or kl_mopp.statics(a) != kl_mopp.statics(b) or a.lists != b.lists or a.tail != b.tail:
        bad.append('box / static count / static order / list codes / tail changed')
    return bad


def check(plain, live, variant, log=print):
    """Offline read-back of a built zip -> list of problems (empty = ok)."""
    bad = []
    A, N = F.Built(live, 'F02'), F.Built(plain, 'F02')
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    if diff != ['F02_Main.HVK', 'F02_Main.buf', 'F02_Main.gms', 'F02_Main.prp']:
        bad.append('members changed: %s' % diff)
    # entities: same list, same slots, only the three shutters differ (flags | 0x200000, raw)
    if [e.name for e in A.ents] != [e.name for e in N.ents]:
        bad.append('entity names differ')
    sa, sn = A.scene.slots(), N.scene.slots()
    if [sa[e] for e in A.ents] != [sn[e] for e in N.ents]:
        bad.append('slot ids changed')
    ch = []
    for k, (a, b) in enumerate(zip(A.ents, N.ents), 1):
        same = (a.tid, a.model, a.rot, a.trans, a.aux, a.ref, a.group, a.links is None) == (b.tid, b.model, b.rot, b.trans, b.aux, b.ref, b.group, b.links is None)
        if not same:
            bad.append('entity %d changed beyond flags/raw' % k)
        if a.flags != b.flags or a.raw != b.raw:
            ch.append(b.ref)
            if b.flags != a.flags | FLAG_REAL or a.raw is not None or b.raw is None or len(b.raw) != 64:
                bad.append('shutter %d: flags %#x -> %#x, raw %s' % (b.ref, a.flags, b.flags, None if b.raw is None else len(b.raw)))
    if sorted(ch) != sorted(SHUTTER_REFS):
        bad.append('entities changed: %s' % sorted(ch))
    for m in ('.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX'):
        if A[m] != N[m]:
            bad.append('%s changed' % m)
    # the keys of each shutter decode to the intended motion
    kd = key_donor()
    ends = sorted({o for x in N.ents if x.raw for _p, oo in kl_graft.keys_tracks(x.raw) for o in oo} | {len(N.scene.head)})
    for r in SHUTTER_REFS:
        e = next(x for x in N.ents if x.ref == r)
        K = ME.VanKeys(N.scene.head, e.raw, ends, kl_graft.keys_tracks)
        R, T = N.fr[e]
        q = quat(R)
        p0, p1 = K.pos[K.f2p[OPEN_FRAMES[0]]], K.pos[K.f2p[OPEN_FRAMES[1]]]
        if K.frames != kd['K'].frames or K.f2p != kd['K'].f2p or K.f2r != kd['K'].f2r:
            bad.append('shutter %d: frame tables differ from the F07 ones' % r)
        if any(abs(p0[i] - T[i]) > 1e-3 for i in range(3)) or abs(p1[1] - T[1] - LIFT) > 0.5 or abs(p1[0] - T[0]) > 1e-3 or abs(p1[2] - T[2]) > 1e-3:
            bad.append('shutter %d: keys %s -> %s, node %s' % (r, p0, p1, T))
        if any(tuple(k) != q for k in K.rot):
            bad.append('shutter %d: rotation keys %s != %s' % (r, K.rot, q))
        ys = [K.pos[K.f2p[f]][1] for f in range(OPEN_FRAMES[0], OPEN_FRAMES[1] + 1)]
        if any(ys[i + 1] < ys[i] - 1e-3 for i in range(len(ys) - 1)):
            bad.append('shutter %d: the lift is not monotonic' % r)
        # the orientation of the quaternion = the node's +Z heading
        hz = math.degrees(math.atan2(R[0][2], R[2][2]))
        kh = math.degrees(2 * math.atan2(K.rot[0][1], K.rot[0][3]))       # heading of the (0, y, 0, w) key
        if abs(kh - hz) > 0.5 and abs(abs(kh - hz) - 360) > 0.5:
            bad.append('shutter %d: key heading %.1f vs node %.1f' % (r, kh, hz))
    # .prp: only the intended nodes change
    ca, pa = _ctrl_map(A)
    cb, pb = _ctrl_map(N)
    if list(ca) != list(cb) or [p for p in pa if pa[p] != pb[p] and not p.endswith('!SoloLift')]:
        bad.append('node list / node properties changed (only the SoloLift trigger box size may, kl_dm02fix_1108.part_coop_prp)')
    sc = N.sc
    sp = {sc.path[N.ents.index(next(x for x in N.ents if x.ref == r)) + 1] for r in SHUTTER_REFS}
    allowed = set(sp) | {p for p in ca if p.endswith('!Open') and '\\KLCoop' in p}
    allowed |= {p for p in ca if p.endswith('KLShops_OpenNow') or p.endswith('!SoloLift') or p.endswith('KLShops_OpenTimer')}
    if variant == 'timer':
        allowed |= {p for p in ca if p.endswith('!Controller') and '\\KLCoop' in p}
    chg = {p for p in ca if ca[p] != cb[p]}
    if not chg <= allowed:
        bad.append('controllers changed on %s' % sorted(chg - allowed)[:4])
    for p in sp:
        if [c[0] for c in cb[p]] != ['MatPosAnim']:
            bad.append('%s: controllers %s' % (p[-30:], [c[0] for c in cb[p]]))
    for p in [p for p in cb if p.endswith('!Open') and '\\KLCoop' in p]:
        if [c[0] for c in cb[p]] != ['MatPosAnimProxy'] or cb[p][0][1][1:3] != list(OPEN_FRAMES) or cb[p][0][1][3] not in ([s] for s in sp):
            bad.append('%s: %s' % (p[-30:], cb[p]))
    on = [c for c in cb['ROOT\\KL_Shops!\\KLShops_OpenNow'] if c[0] == 'DeactivateGeom']
    if len(on) != 1 or any(not any(('Atrium_101a' in t or 'Atrium_201a' in t) and t.endswith(('RollerShutterA_03', 'RollerShutterA_04')) for t in [x]) for x in on[0][1][1]) or len(on[0][1][1]) != 2:
        bad.append('KLShops_OpenNow: %s' % on)
    tm = [c for c in cb['ROOT\\KL_Shops!\\KLShops_OpenTimer'] if c[0] == 'TriggerDelay2']
    if variant == 'timer':
        if len(tm) != 2 or tm[1][1][0] not in (DEFAULT_DELAY,) and tm[1][1][0] <= 1.0 or len(tm[1][1][4]) != 6:
            bad.append('timer: %s' % tm)
        for p, cs in cb.items():
            for nm, v in cs:
                if nm == 'CoopAirlock' and v[23] != []:
                    bad.append('timer: %s still lists %s' % (p[-30:], v[23]))
                if nm == 'PlayerAction' and p.endswith('!SoloLift') and (v[1] != [] or v[8] != 0):
                    bad.append('timer: SoloLift %s %s %s' % (p[-30:], v[1], v[8]))
    else:
        if len(tm) != 1:
            bad.append('coop: %d TriggerDelay2 on OpenTimer' % len(tm))
        for p, cs in cb.items():
            for nm, v in cs:
                if nm == 'PlayerAction' and p.endswith('!SoloLift') and (v[8] != 1 or len(v[1]) != 2):
                    bad.append('coop: SoloLift %s' % p[-30:])
    # the .HVK
    bad += ['hvk: ' + x for x in hvk_added_only(live, plain, SHUTTER_REFS)]
    # bots: the loot census does not move, and the bots zip is the plain one + the squad edit
    mo = lambda X: [(o['node'], o['amount'], o['kind'], o['container']) for o in F.money_objects(X)]
    if mo(A) != mo(N):
        bad.append('bots: the money census changed')
    return bad


def VANY(q):
    return ME.VanKeys.yaw(q)


# ---------------------------------------------------------------- install.py / stage
INSTALL_PY = r'''r"""Installs / undoes the DM02 CO-OP SHUTTERS 1109 (key-framed shutter bodies that open).
  python install.py                      install the default variant (%(default)s) from the staged files (originals -> <name>%(tag)s; an existing backup is NEVER overwritten)
  python install.py --variant coop|timer pick the variant (timer: opens by itself after the delay; coop: two players in the boxes / the solo Lift Door)
  python install.py --undo               put the originals back byte for byte (only when each live file is exactly what an install wrote)
  python install.py --dry                read-only: print every pin and what would happen (also with --undo)
  --game <dir>  other Dog Days folder (rehearsals); --skip-run-check for those only
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s (re-stage if another layer changed them).
Nothing is written while a kl2.exe with threads runs. Never touches KL_PortBackup or any other file. Undo this layer BEFORE any layer installed earlier on DM02."""
import hashlib, json, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '%(tag)s'
NAMES = ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')
OLD = {'F02_Main.zip': '%(live)s', 'F02_Main.bots.zip': '%(bots)s'}
OLD_BASE_TEXT = '%(base)s'
DEFAULT = '%(default)s'
STAGED = %(staged)s      # variant -> {name: md5}
STATE = os.path.join(HERE, 'installed.json')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-Process kl2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Threads.Count } | Measure-Object -Sum).Sum"],
                             capture_output=True, text=True).stdout.strip()
        return bool(out) and int(float(out)) > 0
    except (OSError, ValueError):
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    variant = a[a.index('--variant') + 1] if '--variant' in a else DEFAULT
    if variant not in STAGED:
        print('REFUSED: --variant takes %%s' %% ', '.join(sorted(STAGED))); return 1
    d = os.path.join(game, 'KLExpansion', 'Maps', 'DM02')
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    live = {n: os.path.join(d, n) for n in NAMES}
    bak = {n: live[n] + TAG for n in NAMES}
    for n in NAMES:
        if not os.path.isfile(live[n]):
            print('REFUSED: %%s is not there' %% live[n]); return 1
    if undo:
        if not os.path.isfile(STATE):
            print('REFUSED: no installed.json here (nothing was installed from this folder)'); return 1
        st = json.load(open(STATE))
        for n in NAMES:
            cur = md5(live[n])
            print('%%-26s live %%s' %% (n, cur))
            if cur != st['new'][n]:
                print('REFUSED: %%s live md5 %%s is not the installed %%s (another layer changed it: undo that one first)' %% (n, cur, st['new'][n])); return 1
            if not os.path.isfile(bak[n]) or md5(bak[n]) != st['old'][n]:
                print('REFUSED: backup %%s missing or not %%s' %% (bak[n], st['old'][n])); return 1
        if dry:
            print('would restore', ', '.join(NAMES)); return 0
        for n in NAMES:
            shutil.copyfile(bak[n], live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n]); os.remove(bak[n])
            print('%%s: restored %%s' %% (n, md5(live[n])))
        os.remove(STATE)
        return 0
    cur = {n: md5(live[n]) for n in NAMES}
    for n in NAMES:
        print('%%-26s live %%s' %% (n, cur[n]))
    if os.path.exists(STATE):
        print('REFUSED: installed.json exists: this folder was installed already (use --undo first)'); return 1
    if cur['F02_Main.zip'] != OLD['F02_Main.zip'] or cur['F02_Main.bots.zip'] != OLD['F02_Main.bots.zip'] or open(live['F02_Main.bots.base.md5']).read().strip() != OLD_BASE_TEXT:
        print('REFUSED: a live DM02 file is not the pinned one (%%s / %%s / base %%s): another layer changed it: re-stage on the live files' %% (
            OLD['F02_Main.zip'], OLD['F02_Main.bots.zip'], OLD_BASE_TEXT)); return 1
    for n in NAMES:
        if os.path.exists(bak[n]):
            print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak[n]); return 1
    src = os.path.join(HERE, 'variant_' + variant)
    new = {n: (md5(os.path.join(src, n)) if os.path.isfile(os.path.join(src, n)) else None) for n in NAMES}
    if None in new.values() or any(new[n] != STAGED[variant][n] for n in NAMES):
        print('REFUSED: staged files in %%s are missing or not the md5 the stage recorded' %% src); return 1
    if open(os.path.join(src, 'F02_Main.bots.base.md5')).read().strip() != new['F02_Main.zip']:
        print('REFUSED: base sidecar is not the md5 of the staged zip'); return 1
    need = sum(os.path.getsize(os.path.join(src, n)) + os.path.getsize(live[n]) for n in NAMES) + (1 << 30)
    if shutil.disk_usage(d).free < need:
        print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        print('would install variant', variant, 'from', src); return 0
    done = []
    try:
        for n in NAMES:
            shutil.copyfile(live[n], bak[n]); done.append(n)
            shutil.copyfile(os.path.join(src, n), live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n])
            print('%%s: installed %%s' %% (n, md5(live[n])))
    except OSError as e:
        for n in reversed(done):
            shutil.copyfile(bak[n], live[n]); os.remove(bak[n])
        print('FAILED (%%s); originals put back' %% e); return 2
    json.dump({'variant': variant, 'old': {n: md5(bak[n]) for n in NAMES}, 'new': {n: md5(live[n]) for n in NAMES}}, open(STATE, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''

README = r'''DM02 CO-OP SHUTTERS 1109 (Late Night Opening, slot F02)       built OFFLINE, NOT installed, NOT run in the game
================================================================================================================
What it does: the three Atrium_201a roller shutters (REF 24710 / 24711 / 24712) block the shops again with a body that can MOVE
(key-framed type-4 slab bound to each shutter, rising 300 cm on the shutter's own MatPosAnim keys) instead of the static plane that could
never be removed. Variants (install.py --variant ...):
  timer (default, safest)  the shops open by themselves %(delay)s s after the round starts (second TriggerDelay2 on KLShops_OpenTimer), the co-op
                           triggers are cut from the shutters so nothing can retrigger the lift.
  coop                     two players in the co-op boxes (Arcade / online) or the solo 'Lift Door' prompt open them; no timer.
KLShops_OpenNow no longer opens the three (it keeps the two shop frontages).  Undo: UNDO dm02 coop 1109.bat (byte exact), BEFORE any
layer installed earlier on DM02 (the live md5 must be the one this wrote).

Install (game closed):  INSTALL dm02 coop 1109.bat           or   python install.py [--variant coop] [--dry] [--game <dir> --skip-run-check]
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s.   Backups: <name>%(tag)s next to the live files.
Staged: timer zip %(tzip)s bots %(tbots)s | coop zip %(czip)s bots %(cbots)s

Proven offline (tools/kl_dm02coop_1109.py check + tools/kl_dm02coop_1109_test.py): only the .prp / .gms / .buf / .HVK members change; the 27,522 entity
slots and names are identical, only the three shutters differ (flags | 0x200000, 64-byte raw KEYS); their key tables decode to node position at
frame 0, + 300 cm at frame 100, monotonic, rotation keys = the node's orientation; the .HVK keeps every old shape record byte for byte (static count,
order, MOPP list codes, kl_mopp statics) and gains exactly three type-4 slabs; .prp: only the Open nodes, the three shutter nodes, OpenNow and (variant)
the co-op / timer nodes changed; the money census of the bots does not move; check.py and check_passes.py pass; scratch install / 2nd install refused / undo
byte exact.

GUESSes (not provable offline - the bench decides):
%(guesses)s

BENCH PLAN (later, owner not playing; one bench at a time; tools/kl_bench_1106.py or kl_solo_test on the TEST dll, never the SHIP one):
 0. df C: and the game drive; python install.py --dry; install the variant (INSTALL bat). Bench kit: copy the DM05A/DM02 kit's ini, KLShopPage.ini staged,
    [Script] edited in place. Needs the ClientBuild* / ClientRewrite / ClientRingSync / AssertSoft lines of the live DM02 cover kit.
 1. SOLO, DM02, timer variant:  load the round, walk to the shop frontage of Atrium_201a (x -1990, y 500, z 1032 / 1660 / -2033); shot 1 shutter CLOSED and
    DRAWN (GUESS 1); try to walk through: blocked (GUESS 2). Wait %(delay)s s (+2): shot 2 shutter risen 300 cm (draw + body), walk in: free.
    Log: 0 asserts / faults / dumps; the shutter does not drop back (GUESS 7) over 60 s more.
 2. SOLO, coop variant: stand at the 'Lift Door' prompt (box at lat 80 of the shutter, half 150 x 200 x 330), hold E: shutter rises, Pathblocker toggled; walk in.
 3. 2 SEATS (Arcade / online FA), coop variant: both seats in KLCoopN Box_A / Box_B (arrows): the airlock plays, shutter rises on BOTH seats (the keys play on
    the client too: GUESS 5); then timer variant on 2 seats: both see the rise at the same time +-1 s.
 4. Bots: online FA with bots: they must not clump at a closed shutter for the whole delay: in the timer variant (Pathblocker blocking until the timer) they
    route elsewhere / wait; after the open they enter. If they jam: lower the delay (install.py is re-run with --delay via the tool) or use the coop variant.
 5. Round 2: the shutters are closed again (scene reload), the timer runs again.
 If the shutter is not DRAWN or not BLOCKING, undo and use the old behaviour (shops open, kl_dm02fix_1108 coop verdict); if it blocks but does not rise: the body
 moves with the node only if GUESS 2 holds - read DD's loading-bay (F07) shutter run for the same symptom.

Change the delay: python tools/kl_dm02coop_1109.py stage --delay 60   (re-stages both variants on the CURRENT live files, repins).
'''


def stage(live_dir, out, delay=DEFAULT_DELAY, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    bots = os.path.join(live_dir, 'F02_Main.bots.zip')
    if md5(live) != LIVE_PIN or md5(bots) != LIVE_BOTS_PIN:
        raise SystemExit('live DM02 zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin on the live md5s)' % (LIVE_PIN, LIVE_BOTS_PIN))
    base = open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip()
    if base != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is %s, not %s' % (base, LIVE_BASE_PIN))
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    reps, staged = {}, {}
    for v in VARIANTS:
        d = os.path.join(out, 'variant_' + v)
        reps[v] = build(live, d, v, delay, log)
        bad = check(os.path.join(d, 'F02_Main.zip'), live, v, log)
        if bad:
            raise SystemExit('check failed (%s): %s' % (v, bad))
        staged[v] = {n: md5(os.path.join(d, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}
        reps[v]['check'] = 'ok'
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(tag=TAG, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, staged=repr(staged), default=DEFAULT_VARIANT))
    for nm, arg in (('INSTALL dm02 coop 1109', ''), ('UNDO dm02 coop 1109', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as fh:
        fh.write(README % dict(delay='%.0f' % delay, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, tag=TAG,
                               tzip=staged['timer']['F02_Main.zip'], tbots=staged['timer']['F02_Main.bots.zip'],
                               czip=staged['coop']['F02_Main.zip'], cbots=staged['coop']['F02_Main.bots.zip'],
                               guesses='\n'.join(' %d. GUESS: %s' % (i + 1, g) for i, g in enumerate(GUESSES))))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(dict(reports=reps, staged=staged), fh, indent=1, default=str)
    log(json.dumps(staged, indent=1))
    return reps, staged


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    live = opt('--live', os.path.join(MAPDIR, 'F02_Main.zip'))
    if a and a[0] == 'build':
        out = opt('--out', OUT)
        rep = build(live, out, opt('--variant', DEFAULT_VARIANT), float(opt('--delay', DEFAULT_DELAY)))
        bad = check(os.path.join(out, 'F02_Main.zip'), live, rep['variant'])
        if bad:
            print('check failed:', *bad, sep='\n'); return 1
        return 0
    if a and a[0] == 'stage':
        stage(opt('--live', MAPDIR), opt('--out', OUT), float(opt('--delay', DEFAULT_DELAY)))
        return 0
    if len(a) >= 2 and a[0] == 'check':
        bad = check(a[1], live, opt('--variant', DEFAULT_VARIANT))
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
