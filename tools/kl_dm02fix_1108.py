r"""kl_dm02fix_1108.py - ONE combined DM02 (Late Night Opening, slot F02) fix stage, 2026-11-08. OFFLINE: reads the live zip, writes a stage; nothing installed.

OWNER (2026-11-08): "when i got into cover i get stuck inside the pillar still on DM02, wheres the co-op doors and why is one of the heist rooms
already got their glass blown up with a door to kick down? get rid of the door or make the whole shop more prettier with a better door".
Three parts, each switchable (install.py --parts cover,vault[,coop]; coop is OFF by default, see its verdict):

 cover  The atrium columns' own Dead Men cover boxes (AtriumColumnShatter_01..08 CoverBoxH_03 / _04, 3 floors = 48 entities), the VendingMachine_A
        CoverBoxH_02 boxes (4) and CoverBoxH_K6_15 / CoverBoxM_KM_15 stand ON the column / wall collision: kl_cover_vet on the live zip says 1..4 of
        their 4 side stand points are blocked (the column Whole_01 +-100 x 40 is inside the box). The game builds cover from the box alone
        (kl2 0x6d6a80 -> 0x603830: every ZSTDOBJ whose NAME contains 'coverbox'), never from the collision, so a player taking cover there is put in the
        column. FIX = SAME-LENGTH rename 'CoverBox' -> 'CoverBlk' in the .buf name and in every .prp path string of those entities (nothing moves: slot
        ids, .oct/.rmi/.rmc, .gms untouched). The boxes stop being cover; the columns keep their NoCoverBox neighbours. Costs the atrium column cover.
        A name string in the .buf is shared by entities of the same name: it is only renamed when EVERY user of the string is a target.
        GUESS: the finder reads the name from the .buf string (as kl_fa_cover.all_boxes does) and nothing else keys on the old names.
 coop   The three co-op shutters (Atrium_201a RollerShutterA_01/02/03, REF 24712/24711/24710) were opened at round start by the 10-26 'open' patch
        (KLShops_OpenNow lists them) and their static collision plane was cut from the .HVK (kl_dm02_coop_1026.patch2/3). This puts them back:
        (1) KLShops_OpenNow keeps only the two shop frontages (REF 24709, 26082) = the inverse of patch2 'open';
        (2) the KLCoop1..3 SoloLift PlayerActions get patch2 'lift' (enabled, prompt shown, box half 150 x 200 x 330, kl2 0x40ddf0 reach 150);
        (3) the .HVK: the three filler placements the cut left (shape record with 3 copies of REF 20069, static order 1007..1009, between REF 24709
            and 24714; the static list is in REF order) become STATIC placements of the RollerShutterA plane again: shape = the one of REF 24709
            (verts / idx identical to REF 26082's, other model), placement = entity pos * 0.01 + its 3x3 rotation, MOPP code = 24709's code with the
            offset recomputed (world bb min - 0.01; the same formula reproduces the offsets of 24709 and 26082 byte for byte, asserted). The static
            count is unchanged, so the list codes stay valid. Online they open with the co-op boxes (CoopAirlock Controller), solo with the lift.
        VERDICT 2026-11-08 (static reading of kl2.exe): the restored planes are STATIC type-1 placements (REF 24709 / 26082 are type 1, asserted) and
        DeactivateGeom / the 0x400 flag (0x6edd50 -> 0x440290) only change the node flag word and render handles: a static placement is built into the
        world-space list shape + MOPP at load with no node pointer kept, so NOTHING opens it. Opening the shutter would not make it passable: ~1,060,000
        of loot would be locked behind it. No proven route exists, so this part is OFF BY DEFAULT (DEFAULT_PARTS = cover, vault): live keeps the planes
        cut and the shutters open from round start. Only --parts cover,coop,vault builds it, for research. (Unproven alternative: a key-framed type-2/4
        body under the shutter node that the lift hides; never built.) Also unchecked: the three shutter models have the same plane as REF 24709.
 vault  The two WATCH-store corridor doors (KL_Door_1 / _2 at (-1000,500,2560), (-1440,500,1700)) each stand in a frame that already holds a Dead Men
        glass door, Door_Shatter_Glass_01!Whole04 (REF 23182 / 24258, model 0x9027, flags 0x2201e6) within ~40 cm: a doubled, clashing door. Sets flag
        0x400 (hidden / deactivated, as the game's own Remains04 twins carry) on those two Whole04 entities only (.gms flag word; slot ids, .buf and the
        glass .sgd unchanged). The KL kick leaf stays (bots' kick legs for doors 1,2,3,5 depend on it). Doors 5 / 6 (ground floor) are 115 / 170 away
        from their Whole04 = not the same frame: NOT touched. D3 / D4 (jewel store) have no glass door.
        NOT done: a prettier leaf model (needs a look), and any change to the 39 Remains_01 pieces without 0x400 (the "already blown up" glass may be
        those; unproven, needs a screenshot at the jewel east windows first).
        Collision: 0x400 hides the render only (see the coop verdict: static type-1 collision stays), so the two REFs' static placements are ALSO cut
        from the .HVK (kl_escape.cut_collision: a filler placement keeps the static list order and MOPP codes valid); asserted: one static placement each.
        check() proves with kl_doors_clear_1108.hvk_equal that only those two REFs left (every other shape / MOPP / static position identical).

usage (from tools/):
  python kl_dm02fix_1108.py build --parts cover,coop,vault --out <dir> [--live <F02_Main.zip>]   one zip + bots zip + md5 sidecar
  python kl_dm02fix_1108.py stage [--out C:\kl_build_1024\dm02fix_1108] [--live <Maps\DM02>]       the full stage with install.py / UNDO.bat
  python kl_dm02fix_1108.py check <zip>                                                           offline checks of a built zip
"""
import collections, hashlib, json, os, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_hvk, kl_escape
import kl_fa_bots as F
import kl_fa_cover as C
import kl_botsonline

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM02')
OUT = r'C:\kl_build_1024\dm02fix_1108'
TAG = '.before-dm02fix1108'
PARTS = ('cover', 'coop', 'vault')
DEFAULT_PARTS = ('cover', 'vault')                        # coop is OFF by default (module doc, coop: no proven way to drop the shutter collision)
LIVE_PIN = '7adcb2351ba3df043e65f3bed3f71104'            # live F02_Main.zip 2026-11-08 02:31 (PD2 rebase 1107r)
LIVE_BOTS_PIN = '1103c6923a45e015ee1325003b9f69c2'      # live F02_Main.bots.zip (members identical to a kl_botsonline eAllTypes rebuild, asserted)
LIVE_BASE_PIN = '7adcb2351ba3df043e65f3bed3f71104'      # F02_Main.bots.base.md5 holds the md5 of the plain zip

OLD, NEW = b'CoverBox', b'CoverBlk'                      # same length; 'coverbox' no longer a substring
SHUTTER_REFS = (24710, 24711, 24712)                     # Atrium_201a RollerShutterA_03 / _02 / _01 (kl_dm02_coop_1026.SHUTTER_REFS)
SHOP_REFS = (24709, 26082)                               # the two always-open shop frontages (stay in KLShops_OpenNow)
DONOR_REF = 24709                                        # its static plane is the template (verts / idx identical to REF 26082's)
FILLER_REF = 20069
LIFT_HALF = (150.0, 200.0, 330.0)                        # kl_dm02_coop_1026.LIFT_HALF (GUESS: kl2 0x40ddf0 reach 150)
GLASS_DOORS = {23182: (-1000.0, 2560.0), 24258: (-1440.0, 1700.0)}   # Whole04 REF -> KL_Door hinge (x, z) of D1 / D2
GLASS_MAX_DIST = 60.0                                    # a Whole04 further from the hinge is another frame (D5 115, D6 170: skipped)
HIDE = 0x400


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5b(d):
    return hashlib.md5(d).hexdigest()


# ---------------------------------------------------------------- cover
def cover_targets(B):
    """-> (nodes, skipped): ZSTDOBJ nodes named *coverbox* of the column / vending / K6_15 / KM_15 families."""
    sc = B.sc
    pat = re.compile(r'(AtriumColumnShatter_0\d!CoverBoxH_0[34]$|VendingMachine_A_0\d!CoverBoxH_02$|^CoverBoxH_K6_15$|^CoverBoxM_KM_15$)')
    hit = [k for k in range(1, len(sc.names)) if sc.cls(k) == 'ZSTDOBJ' and 'coverbox' in sc.names[k].lower() and pat.search(sc.names[k])]
    return hit


def gms_name_offsets(B):
    """{entity node k: .buf offset of its name string} (the .gms record's first word, as F.Built reads it)."""
    raw = kl_gms.unpack(B['.gms'])
    return {k: struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0] for k, (decl, _t, _p) in enumerate(kl_gms.entities(raw), 1)}


def part_cover(B, files, prp, rep):
    sc = B.sc
    hit = set(cover_targets(B))
    if not hit:
        raise ValueError('cover: no target boxes found')
    off = gms_name_offsets(B)
    users = collections.defaultdict(list)
    for k, o in off.items():
        users[o].append(k)
    buf = bytearray(files[B.ext['.buf']])
    renamed, shared = set(), []
    for o in sorted({off[k] for k in hit}):
        if any(u not in hit for u in users[o]):
            shared.append(sc.names[users[o][0]])
            continue
        e = buf.index(b'\0', o)
        s = bytes(buf[o:e])
        if s.count(OLD) != 1:
            raise ValueError('cover: name %r at %d has %d x %s' % (s, o, s.count(OLD), OLD))
        buf[o:e] = s.replace(OLD, NEW)
        renamed.update(users[o])
    if shared:
        rep['cover_shared_skipped'] = shared
    n_prp = 0
    for k in sorted(renamed):
        p = sc.path[k].encode('latin1')
        if p.count(OLD) != 1:
            raise ValueError('cover: path %r' % p)
        c = prp.count(p)
        if c < 1:     # the vending / K6_15 / KM_15 paths are not strings of the .prp at all (checked: no leaf name either); only the .buf name exists
            if prp.count(sc.names[k].encode('latin1')):
                raise ValueError('cover: node %d name is in the .prp but not its path' % k)
            continue
        prp = prp.replace(p, p.replace(OLD, NEW))
        n_prp += c
    files[B.ext['.buf']] = bytes(buf)
    rep['cover'] = collections.OrderedDict(targets=len(hit), renamed=len(renamed), buf_strings=len({off[k] for k in renamed}), prp_strings=n_prp,
                                           names=sorted({sc.names[k].rsplit('!', 1)[-1] for k in renamed}))
    return prp


# ---------------------------------------------------------------- coop
def part_coop_prp(B, rep):
    """In place on B.sc (the live scene); returns nothing. See the module doc, coop (1) and (2)."""
    sc = B.sc
    hits = [k for k in range(1, len(sc.names)) if sc.names[k].endswith('!SoloLift')]
    opens = [k for k in range(1, len(sc.names)) if sc.names[k].startswith('KLCoop') and sc.names[k].endswith('!Open')]
    now = [k for k in range(1, len(sc.names)) if sc.names[k] == 'KLShops_OpenNow']
    if len(hits) != 3 or len(opens) != 3 or len(now) != 1:
        raise ValueError('coop: %d SoloLift, %d Open, %d OpenNow' % (len(hits), len(opens), len(now)))
    tg = []
    for k in opens:
        for nm, body in sc.nodes[k]['ctrls']:
            if sc.p.key(nm) == 'DeactivateGeom':
                tg += kl_fa.value(sc, kl_fa.units(body[1:-1])[1])
    want = {B.ents[k - 1].ref for k in range(1, len(sc.names)) if sc.path[k] in tg}
    if want != set(SHUTTER_REFS) or len(tg) != 3:
        raise ValueError('coop: Open targets %s differ from %s' % (sorted(want), SHUTTER_REFS))
    ci = [j for j, (nm, _b) in enumerate(sc.nodes[now[0]]['ctrls']) if sc.p.key(nm) == 'DeactivateGeom']
    if len(ci) != 1:
        raise ValueError('coop: OpenNow has %d DeactivateGeom' % len(ci))

    def fo(us):
        cur = kl_fa.value(sc, us[1])
        keep = [t for t in cur if t not in tg]
        if len(cur) != 5 or len(keep) != 2 or any(t not in cur for t in tg):
            raise ValueError('coop: OpenNow has %d targets (want 5 = 2 frontages + 3 co-op shutters)' % len(cur))
        us[1] = kl_fa._refs(sc, keep)
    kl_fa.edit(sc, now[0], ci[0], fo)
    for k in hits:
        i = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'PlayerAction']
        if len(i) != 1:
            raise ValueError('coop: %s has %d PlayerActions' % (sc.names[k], len(i)))

        def fn(us):
            if len(us) != 21 or us[12][0][0] != 6 or us[13][0][0] != 6 or us[8][0][0] != 6:
                raise ValueError('coop: PlayerAction is not the clone of the L03 use box')
            us[8] = [(6, bytes([1]))]       # enabled
            us[12] = [(6, bytes([1]))]
            us[13] = [(6, bytes([0]))]      # 13 = 1 hides the prompt (kl2 0x550992)
        kl_fa.edit(sc, k, i[0], fn)

        def fb(us):
            if len(us) != 11 or any(us[j][0][0] != 0x0a for j in (8, 9, 10)):
                raise ValueError('coop: box node layout is not 11 fields with floats at 8..10')   # GUESS (as patch2): props 8..10 = half sizes
            for j, h in zip((8, 9, 10), LIFT_HALF):
                us[j] = [(0x0a, struct.pack('<f', h))]
        kl_fa.edit(sc, k, None, fb)
    rep['coop_prp'] = collections.OrderedDict(opennow_before=5, opennow_after=2, solo_lift_nodes=len(hits), box_half=list(LIFT_HALF))


def mopp_offset(inst, shape):
    """The 16-byte MOPP offset of a placement: world bb min - 0.01 (xyz, float32) + the code's own 4th float (kept by the caller)."""
    f = struct.unpack_from('<12f', inst)
    p, R = f[:3], [f[3:6], f[6:9], f[9:12]]
    mn = [1e30] * 3
    for j in range(len(shape.verts) // 12):
        v = struct.unpack_from('<3f', shape.verts, j * 12)
        for i in range(3):
            mn[i] = min(mn[i], p[i] + sum(R[i][t] * v[t] for t in range(3)))
    return struct.pack('<3f', *[m - 0.01 for m in mn])


def placement(B, k, ref):
    """0x38-byte placement: pos * 0.01 (Havok scale), the entity's 3x3 rotation rows, REF, flag 0 (checked against REF 24709 / 24714 / 24716)."""
    Rm, T = B.fr[B.ents[k - 1]]
    return struct.pack('<12f', *[t * 0.01 for t in T], *[Rm[i][j] for i in range(3) for j in range(3)]) + struct.pack('<II', ref, 0)


def part_coop_hvk(B, files, rep):
    sc = B.sc
    ent = {B.ents[k - 1].ref: k for k in range(1, len(sc.names))}
    h = kl_hvk.Hvk(files[B.ext['.HVK']])
    n0 = h.static_count()
    stat = [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]
    refs = [kl_hvk.ref(h.shapes[si].inst[i]) for si, i in stat]
    if any(r in refs for r in SHUTTER_REFS):
        raise ValueError('coop hvk: a shutter REF is placed already (the cut is not live: nothing to restore)')
    donor = [(si, i) for si, i in stat if kl_hvk.ref(h.shapes[si].inst[i]) == DONOR_REF]
    if len(donor) != 1:
        raise ValueError('coop hvk: donor REF %d placed %d times' % (DONOR_REF, len(donor)))
    ds = h.shapes[donor[0][0]]
    if len(ds.inst) != 1 or len(ds.verts) // ds.vstride != 4 or ds.convex:
        raise ValueError('coop hvk: donor is not the single 4-vertex plane')
    # self-test of the two formulas on the donor and on REF 26082 (a second RollerShutterA): byte-exact
    for r in (DONOR_REF, 26082):
        s = [h.shapes[si] for si, i in stat if kl_hvk.ref(h.shapes[si].inst[i]) == r][0]
        if s.verts != ds.verts or s.idx != ds.idx or s.sub != ds.sub:
            raise ValueError('coop hvk: REF %d plane differs from the donor' % r)
        # placement byte-exact; the offset to float32 rounding (REF 26082 differs by 1 ulp in y: the game's tool used another summation order)
        o1, o2 = struct.unpack('<3f', mopp_offset(s.inst[0], s)), struct.unpack('<3f', s.mopp[0][0][:12])
        if placement(B, ent[r], r) != s.inst[0] or any(abs(x - y) > 1e-6 for x, y in zip(o1, o2)):
            raise ValueError('coop hvk: placement / offset formula does not reproduce REF %d' % r)
    # the cut slots: ONE filler shape record with exactly 3 copies of REF FILLER_REF, between REF 24709 and the next kept REF 24714 in static order
    pos = {r: n for n, r in enumerate(refs)}
    a = pos[DONOR_REF]
    nxt = refs[a + 4]
    if refs[a + 1:a + 4] != [FILLER_REF] * 3 or nxt in (FILLER_REF,) or not DONOR_REF < nxt:
        raise ValueError('coop hvk: static order around REF %d is %s' % (DONOR_REF, refs[a:a + 6]))
    if any(not (DONOR_REF < r < nxt) for r in SHUTTER_REFS):
        raise ValueError('coop hvk: shutter REFs are not between %d and %d' % (DONOR_REF, nxt))
    fsi = stat[a + 1][0]
    fs = h.shapes[fsi]
    if len(fs.inst) != 3 or [stat[a + 1 + n][0] for n in range(3)] != [fsi] * 3:
        raise ValueError('coop hvk: the 3 fillers are not one shape record')
    new = []
    for r in sorted(SHUTTER_REFS):
        inst = placement(B, ent[r], r)
        off = mopp_offset(inst, ds)
        new.append(ds.clone([inst], [(off + ds.mopp[0][0][12:], ds.mopp[0][1])]))
    h.shapes[fsi:fsi + 1] = new
    if h.static_count() != n0:
        raise ValueError('coop hvk: static count changed')
    data = h.serialize()
    h2 = kl_hvk.Hvk(data)
    got = [kl_hvk.ref(i) for s in h2.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    if got[a + 1:a + 4] != sorted(SHUTTER_REFS) or h2.static_count() != n0:
        raise ValueError('coop hvk: read-back %s' % got[a:a + 6])
    files[B.ext['.HVK']] = data
    rep['coop_hvk'] = collections.OrderedDict(static=n0, slots=[a + 1, a + 2, a + 3], refs=sorted(SHUTTER_REFS), bytes=(len(h.serialize()), len(data)))


# ---------------------------------------------------------------- vault
def part_vault(B, files, rep):
    raw = bytearray(kl_gms.unpack(B['.gms']))
    ents = list(kl_gms.entities(bytes(raw)))
    done = []
    for k, e in enumerate(B.ents, 1):
        if e.ref not in GLASS_DOORS:
            continue
        nm = B.sc.names[k]
        if not nm.endswith('!Whole04') or 'Door_Shatter_Glass' not in nm or e.model != 0x9027 or e.flags != 0x2201e6:
            raise ValueError('vault: REF %d is %r model %#x flags %#x, not the intact Whole04 glass door' % (e.ref, nm, e.model, e.flags))
        x, z = B.at(k)[0], B.at(k)[2]
        hx, hz = GLASS_DOORS[e.ref]
        d = ((x - hx) ** 2 + (z - hz) ** 2) ** 0.5
        if d > GLASS_MAX_DIST:
            raise ValueError('vault: REF %d is %.0f from the hinge (> %.0f)' % (e.ref, d, GLASS_MAX_DIST))
        rec = 4 * (ents[k - 1][0] & 0xffffff)
        if struct.unpack_from('<I', raw, rec + 28)[0] != e.flags:
            raise ValueError('vault: flags word of node %d is not at record +28' % k)
        struct.pack_into('<I', raw, rec + 28, e.flags | HIDE)
        done.append((e.ref, round(d, 1)))
    if len(done) != len(GLASS_DOORS):
        raise ValueError('vault: %d of %d glass doors found' % (len(done), len(GLASS_DOORS)))
    files[B.ext['.gms']] = kl_gms.pack(bytes(raw))
    # 0x400 only hides the render (static type-1 placements keep their collision: kl2 0x6edd50 -> 0x440290 touch the node flag word and render handles
    # only; the static list shape + MOPP are built at load with no node pointer): so the REF's placement is cut out of the .HVK as well.
    h = kl_hvk.Hvk(files[B.ext['.HVK']])
    for r in GLASS_DOORS:
        got = [s.type for s in h.shapes for i in s.inst if kl_hvk.ref(i) == r]
        if got != [kl_hvk.STATIC]:
            raise ValueError('vault: REF %d has placements of types %s in the .HVK (want exactly one static)' % (r, got))
    kl_escape.cut_collision(h, set(GLASS_DOORS), lambda *a: None)
    left = [r for r in GLASS_DOORS if any(kl_hvk.ref(i) == r for s in h.shapes for i in s.inst)]
    if left:
        raise ValueError('vault: REF %s still placed after the cut' % left)
    files[B.ext['.HVK']] = h.serialize()
    rep['vault'] = collections.OrderedDict(hidden_whole04=done, hvk_cut=sorted(GLASS_DOORS))


# ---------------------------------------------------------------- build
def build(live, outdir, parts, log=print):
    """live zip -> outdir/F02_Main.zip + F02_Main.bots.zip + F02_Main.bots.base.md5. -> report dict."""
    parts = [p for p in PARTS if p in parts]
    if not parts:
        raise ValueError('no parts')
    B = F.Built(live, 'F02')
    files = dict(B.files)
    rep = collections.OrderedDict(parts=parts, live=live, live_md5=md5(live))
    prp = B.files[B.ext['.prp']]
    if 'coop' in parts:
        part_coop_prp(B, rep)
        prp = B.sc.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp:
            raise ValueError('the patched .prp does not round-trip')
        part_coop_hvk(B, files, rep)
    if 'cover' in parts:
        prp = part_cover(B, files, prp, rep)
    if 'vault' in parts:
        part_vault(B, files, rep)
    files[B.ext['.prp']] = prp
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F02_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
    want = {'cover': {'F02_Main.buf', 'F02_Main.prp'}, 'coop': {'F02_Main.prp', 'F02_Main.HVK'}, 'vault': {'F02_Main.gms', 'F02_Main.HVK'}}
    allowed = set().union(*[want[p] for p in parts])
    if not set(diff) <= allowed:
        raise ValueError('members changed %s outside %s' % (diff, sorted(allowed)))
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
    with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
    log('dm02fix_1108 parts=%s -> %s (%s) members %s' % (','.join(parts), plain, rep['out_md5'], diff))
    return rep


def hvk_only_gone(zp_in, zp_out, gone_refs):
    """Shape-by-shape proof that the .HVK differs only by `gone_refs` having left: every other REF keeps its placements, shape records and MOPP code
    (the filler REF, here 20069 which the earlier cuts already use with several variants, may only GAIN len(gone) copies of a variant it already has),
    static positions keep their place, non-static shapes and the box are identical. (kl_doors_clear_1108.hvk_equal wants ONE filler variant: not true of this live.) -> problems."""
    def load(zp):
        with zipfile.ZipFile(zp) as z:
            return kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))

    def sig(s):
        return (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub))

    def pl(h):
        d = collections.defaultdict(list)
        for s in h.shapes:
            for j, i in enumerate(s.inst):
                d[kl_hvk.ref(i)].append((s.type, sig(s), bytes(i), s.mopp[j][1] if s.mopp else None))
        return d
    a, b = load(zp_in), load(zp_out)
    pa, pb = pl(a), pl(b)
    bad = []
    if set(pa) - set(pb) != set(gone_refs) or set(pb) - set(pa):
        bad.append('refs gone %s / new %s, expected only %s gone' % (sorted(set(pa) - set(pb)), sorted(set(pb) - set(pa)), sorted(gone_refs)))
    diff = [r for r in pa if r in pb and pa[r] != pb[r]]
    for r in diff:
        ca, cb = collections.Counter(pa[r]), collections.Counter(pb[r])
        extra = cb - ca
        if ca - cb or sum(extra.values()) != len(gone_refs) or len(extra) != 1 or next(iter(extra)) not in ca or any(x[0] != 1 for x in pa[r]):
            bad.append('REF %d changed beyond gaining %d filler copies of an existing variant' % (r, len(gone_refs)))
    if len(diff) > 1:
        bad.append('more than one ref changed: %s' % diff)
    if a.static_count() != b.static_count():
        bad.append('static count %d -> %d' % (a.static_count(), b.static_count()))
    gset = set(gone_refs)
    sa = [kl_hvk.ref(i) for s in a.shapes if s.type == 1 for i in s.inst]
    sb = [kl_hvk.ref(i) for s in b.shapes if s.type == 1 for i in s.inst]
    if len(sa) != len(sb) or any(x != y and not (x in gset and y in diff) for x, y in zip(sa, sb)):
        bad.append('static list order changed')
    ns = lambda h: [(s.type, sig(s), tuple(bytes(i) for i in s.inst)) for s in h.shapes if s.type != 1]
    if ns(a) != ns(b):
        bad.append('a non-static shape changed')
    if a.box != b.box:
        bad.append('the .HVK box changed')
    return bad


def check(plain, live, parts, log=print):
    """Offline read-back of a built zip: -> list of problems (empty = ok)."""
    bad = []
    A, Bn = F.Built(live, 'F02'), F.Built(plain, 'F02')
    n0 = len(C.all_boxes(A))
    n1 = len(C.all_boxes(Bn))
    tg = cover_targets(A)
    if 'cover' in parts:
        if n0 - n1 != len(tg) or cover_targets(Bn):
            bad.append('cover: boxes %d -> %d, targets %d, targets left %d' % (n0, n1, len(tg), len(cover_targets(Bn))))
        pz = zipfile.ZipFile(plain).read(Bn.ext['.prp'])
        if any(sc_p.encode('latin1') in pz for sc_p in (A.sc.path[k] for k in tg)):
            bad.append('cover: an old path is still in the .prp')
        if [Bn.sc.names[k].replace('CoverBlk', 'CoverBox') for k in tg] != [A.sc.names[k] for k in tg] and len(tg) != len([1 for k in tg]):
            bad.append('cover: names')
    elif n0 != n1:
        bad.append('cover off but boxes %d -> %d' % (n0, n1))
    if 'coop' in parts:
        sc = Bn.sc
        now = [k for k in range(1, len(sc.names)) if sc.names[k] == 'KLShops_OpenNow'][0]
        ons = []
        for nm, body in sc.nodes[now]['ctrls']:
            if sc.p.key(nm) == 'DeactivateGeom':
                ons = [t.rsplit('\\', 1)[-1] for t in kl_fa.value(sc, kl_fa.units(body[1:-1])[1])]
        if len(ons) != 2 or any('RollerShutterA_0' not in t for t in ons):
            bad.append('coop: OpenNow %s' % ons)
        for k in [k for k in range(1, len(sc.names)) if sc.names[k].endswith('!SoloLift')]:
            for nm, body in sc.nodes[k]['ctrls']:
                if sc.p.key(nm) == 'PlayerAction':
                    v = [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])]
                    if v[8] != 1 or v[12] != 1 or v[13] != 0:
                        bad.append('coop: SoloLift %s fields %s' % (sc.names[k], (v[8], v[12], v[13])))
            if kl_fa.node_values(sc, k)[8:11] != list(LIFT_HALF):
                bad.append('coop: lift box half of %s' % sc.names[k])
        h = kl_hvk.Hvk(Bn['.HVK'])
        got = {kl_hvk.ref(i) for s in h.shapes if s.type == kl_hvk.STATIC for i in s.inst}
        if not set(SHUTTER_REFS) <= got:
            bad.append('coop: HVK shutters not placed')
    if 'vault' in parts:
        for k, e in enumerate(Bn.ents, 1):
            if e.ref in GLASS_DOORS and not e.flags & HIDE:
                bad.append('vault: REF %d not hidden' % e.ref)
        diff = [k for k, (a, b) in enumerate(zip(A.ents, Bn.ents)) if a.flags != b.flags]
        if sorted(Bn.ents[k].ref for k in diff) != sorted(GLASS_DOORS):
            bad.append('vault: flags changed on %s' % [Bn.ents[k].ref for k in diff])
        if 'coop' not in parts:        # shape-by-shape: only the two glass placements left (static order kept, filler copies only)
            bad += ['vault hvk: ' + x for x in hvk_only_gone(live, plain, sorted(GLASS_DOORS))]
        else:
            h = kl_hvk.Hvk(Bn['.HVK'])
            if any(kl_hvk.ref(i) in GLASS_DOORS for s in h.shapes for i in s.inst):
                bad.append('vault: glass door collision still in the .HVK')
    else:
        if any(a.flags != b.flags for a, b in zip(A.ents, Bn.ents)):
            bad.append('vault off but flags changed')
    return bad


# ---------------------------------------------------------------- install.py / stage
INSTALL_PY = r'''r"""Installs / undoes the DM02 FIX 1108 (cover boxes off the atrium columns, co-op shutters back, doubled watch-store glass door hidden).
  python install.py                    install the DEFAULT parts (cover, vault; coop is OFF, see below) from the staged files (originals -> <name>%(tag)s; an existing backup is NEVER overwritten)
  python install.py --parts cover,vault,coop build the chosen parts first (needs the repo tools: %(tool)s) from the LIVE zip, then install those
  python install.py --undo             put the originals back byte for byte (only when each live file is exactly what an install wrote)
  python install.py --dry              read-only: print every pin and what would happen (also with --undo)
  --game <dir>  other Dog Days folder (rehearsals); --skip-run-check for those only
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s (re-stage on --base live if another layer changed them).
Nothing is written while a kl2.exe with threads runs. Never touches KL_PortBackup or any other file. Undo order: this layer's UNDO.bat BEFORE any layer
that was installed earlier on DM02 (the UNDO ALL 1105.bat steps); out of order refuses (the live md5 is then not the one this wrote)."""
import hashlib, json, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '%(tag)s'
TOOL = r'%(tool)s'
NAMES = ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')
OLD = {'F02_Main.zip': '%(live)s', 'F02_Main.bots.zip': '%(bots)s', 'F02_Main.bots.base.md5': ''}   # base: md5 of its CONTENT is checked below
OLD_BASE_TEXT = '%(base)s'
STAGED = %(staged)s      # parts tuple -> {name: md5}; 'all' is staged here, subsets are built at install time into HERE/parts_<list>
STATE = os.path.join(HERE, 'installed.json')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    """True when a kl2.exe WITH THREADS runs (zombie kl2.exe with 0 threads do not count)."""
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-Process kl2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Threads.Count } | Measure-Object -Sum).Sum"],
                             capture_output=True, text=True).stdout.strip()
        return bool(out) and int(float(out)) > 0
    except (OSError, ValueError):
        return True


def base_text(p):
    return open(p).read().strip()


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    parts = a[a.index('--parts') + 1].split(',') if '--parts' in a else ['cover', 'vault']
    if any(p not in ('cover', 'coop', 'vault') for p in parts):
        print('REFUSED: --parts takes cover, coop, vault'); return 1
    parts = [p for p in ('cover', 'coop', 'vault') if p in parts]
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
    if cur['F02_Main.zip'] != OLD['F02_Main.zip'] or cur['F02_Main.bots.zip'] != OLD['F02_Main.bots.zip'] or base_text(live['F02_Main.bots.base.md5']) != OLD_BASE_TEXT:
        print('REFUSED: a live DM02 file is not the pinned one (%%s / %%s / base %%s): another layer changed it: re-stage on --base live' %% (
            OLD['F02_Main.zip'], OLD['F02_Main.bots.zip'], OLD_BASE_TEXT)); return 1
    for n in NAMES:
        if os.path.exists(bak[n]):
            print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak[n]); return 1
    src = HERE
    if parts != ['cover', 'vault']:
        src = os.path.join(HERE, 'parts_' + '_'.join(parts))
        if dry:
            print('would build parts %%s into %%s with %%s' %% (parts, src, TOOL))
        else:
            r = subprocess.run([sys.executable, TOOL, 'build', '--parts', ','.join(parts), '--out', src, '--live', live['F02_Main.zip']])
            if r.returncode:
                print('REFUSED: building the subset failed'); return 1
    new = {n: (md5(os.path.join(src, n)) if os.path.isfile(os.path.join(src, n)) else None) for n in NAMES}
    if not dry:
        if None in new.values():
            print('REFUSED: staged file missing in %%s' %% src); return 1
        if src == HERE and any(new[n] != STAGED[n] for n in NAMES):
            print('REFUSED: staged files are not the md5 the stage recorded'); return 1
        if base_text(os.path.join(src, 'F02_Main.bots.base.md5')) != new['F02_Main.zip']:
            print('REFUSED: base sidecar is not the md5 of the staged zip'); return 1
        need = sum(os.path.getsize(os.path.join(src, n)) + os.path.getsize(live[n]) for n in NAMES) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    else:
        print('would install parts', ','.join(parts), 'from', src); return 0
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
    json.dump({'parts': parts, 'old': {n: md5(bak[n]) for n in NAMES}, 'new': {n: md5(live[n]) for n in NAMES}}, open(STATE, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def stage(live_dir, out, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    if md5(live) != LIVE_PIN or md5(os.path.join(live_dir, 'F02_Main.bots.zip')) != LIVE_BOTS_PIN:
        raise SystemExit('live DM02 zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin on the live md5s)' % (LIVE_PIN, LIVE_BOTS_PIN))
    base = open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip()
    if base != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is %s, not %s' % (base, LIVE_BASE_PIN))
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        if n != 'work':
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    rep = build(live, out, DEFAULT_PARTS, log)
    bad = check(os.path.join(out, 'F02_Main.zip'), live, DEFAULT_PARTS, log)
    if bad:
        raise SystemExit('check failed: %s' % bad)
    staged = {n: md5(os.path.join(out, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}
    tool = os.path.join(HERE, 'kl_dm02fix_1108.py')
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(tag=TAG, tool=tool, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, staged=repr(staged)))
    for nm, arg in (('INSTALL dm02 fix 1108', ''), ('UNDO dm02 fix 1108', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    rep['staged'] = staged
    rep['check'] = 'ok'
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    log(json.dumps(rep, indent=1, default=str))
    return rep


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    if a and a[0] == 'build':
        parts = opt('--parts', ','.join(DEFAULT_PARTS)).split(',')
        rep = build(opt('--live', os.path.join(MAPDIR, 'F02_Main.zip')), opt('--out', OUT), parts)
        bad = check(os.path.join(opt('--out', OUT), 'F02_Main.zip'), opt('--live', os.path.join(MAPDIR, 'F02_Main.zip')), rep['parts'])
        if bad:
            print('check failed:', bad); return 1
        return 0
    if a and a[0] == 'stage':
        stage(opt('--live', MAPDIR), opt('--out', OUT))
        return 0
    if len(a) >= 2 and a[0] == 'check':
        bad = check(a[1], opt('--live', os.path.join(MAPDIR, 'F02_Main.zip')), opt('--parts', ','.join(DEFAULT_PARTS)).split(','))
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
