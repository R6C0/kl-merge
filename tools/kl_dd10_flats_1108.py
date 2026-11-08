#!/usr/bin/env python3
r"""kl_dd10_flats_1108.py - DD10 'Flat Raid' (Dog Days L05 in the F07 slot): MORE RAIDABLE FLATS, LOOT UPSTAIRS, MORE KICK DOORS, FUEL CANS ON THE FLOOR.
2026-11-08. STAGE ONLY: reads the LIVE DD10 files (read-only), builds C:/kl_build_1024/dd10flats_1108, never installs.

Owner: "more flats you can raid on the map throughout the floors, less loot downstairs more upstairs, kickable doors more of them please and a few more fuel
cans in appropriate spawns not just in the open floating, fix that too".

Parts (--parts a,b,c; default loot,fuel,flats,doors; each part is its own switch):
  loot   three of the eight 500k stacks (the 4 M total is kept, nothing invented) move from the lower floors (y 402 / 802 / 860) into three y 1600 flats
         (z 0 band, one per flat, on the walk mesh with 60 cm margin, y = the collision floor under it). Stack nodes are rigid-less top-level ZSTDOBJ without kids and are
         in no octree tree (checked), so this is the placement only (.prp ZGEOM[2] + .gms translation, kl_fa_author.place). One stack stays downstairs (22128, the stair foot).
  fuel   (a) the two scripted cop-thrown cans (Stairway_PartB_Throw_Can / _PartB3_Throw_Can: 'Group_Gas', static ZSTDOBJ, no animation data) hang 113 / 116 cm in the air
         at rest: the group is lowered onto the floor found by kl_map_escape.Ground.under (GUESS: the throw ANM drives the pose while it plays, so the lowering only
         changes the rest pose; an ANM that adds to the placement would shift the throw by the same 1.1 m);
         (b) FUEL_NEW further Dog Days fuel cans (kl_dm01b_gas_1025.build with its top group renamed KL_Gas!3, no extinguishers) on the floor of flats and corridors on
         every floor, each snapped to walk mesh with a 60 cm margin and >= 900 cm from the start spawns. The two stock KL_Fuel_1/2 of KL_Gas!2 stay where they are
         (moving them needs their .HVK / .hrd records and the octree box of the explosion group: left alone).
  flats  kick doors (own leaf, kl_doors_1108 pipeline) on the ENTRANCE doors of the flats of every floor (FLAT_HOSTS): a flat behind a kickable door is a raidable flat.
         kl_interact_graft.door_hosts is run with h_tol (210, 246): DD10's doors are 220 / 222 cm high, the default 228..246 finds none.
  doors  more kick doors on the other (ring / service) doors (DOOR_HOSTS), same pipeline.
  vanfix NOT BUILT. The owner's report 'cannot escape / van blown up' has no PROVEN cause (the van is called only by entering otrExitLevel (8300,200,1100) half
         (450,300,450); the jump-out-of-the-balcony stuck and the teleport-onto-the-van-lane idea are GUESSES). Selecting it refuses.

Order of the build (slot ids move only in the steps that append nodes): loot + reseat (placement only) -> fuel cans (append KL_Gas!3, .prm/.MAT/.TEX/.oct/.HVK/.hrd)
-> kick doors (append KL_Interact!N). Both the plain zip and the bots zip go through every step; they must differ only in the .prp, as the live pair does.
KLJoin.ini: Entries= = the .prm chunk count of the result (the hook takes the section for that .prm only). No KLGuns.ini for DD10.

  python tools/kl_dd10_flats_1108.py plan  [--in-dir <map dir>]                 the chosen places and doors (writes nothing)
  python tools/kl_dd10_flats_1108.py stage [--in-dir <map dir>] [--out-root C:/kl_build_1024] [--parts loot,fuel,flats,doors] [--keep-tmp]
  python tools/kl_dd10_flats_1108.py check [--out-root C:/kl_build_1024]       census, floors, collision, round trips, install --dry, byte-exact undo in scratch
Never installs anything. REFUSES unless the live files are the pinned md5s."""
import collections, hashlib, json, math, os, re, shutil, struct, subprocess, sys, tempfile, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))

BS = chr(92)
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DD10')
OUT_ROOT = 'C:/kl_build_1024'
MAP, SLOT = 'DD10', 'F07'
NAME, TAG, TITLE = 'dd10flats_1108', '.before-dd10flats1108', 'DD10FLATS1108'
TEMPLATE = 'C:/kl_build_1024/citylights_1108/install.py'
ZIP, BOTS, BASE, JOIN = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5', 'KLJoin.ini'
LIVE_MD5 = {ZIP: '5d76d91ae2c84607e7d635678c5d8a98', BOTS: '069f440219307e17a66a237531be8e15', BASE: '3dcfc1d349492fda2d9fdf2376560212', JOIN: '481520e72914cc285ea0f11cf16640b5'}
PARTS_ALL = ('loot', 'fuel', 'flats', 'doors')
CHANGED_OK = ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.HVK', '.hrd')

# ---- loot: node -> (target x, target z, floor level y). 500k each, REF labels untouched. 22128 (11394,402,150, the foot of the stairway) stays downstairs.
# The y 1600 band z 100..500 (collision floor 1603) is walk mesh the whole way along x 10600..13000; the flats' entrance doors stand at z ~ 18 (x 10951 / 11751 / 12551).
LOOT_MOVES = {22134: (11300.0, 300.0, 1603.0),     # was (9550, 402, 810)  y 402
              22133: (12100.0, 300.0, 1603.0),     # was (10330, 802, 50)  y 802
              22132: (12850.0, 300.0, 1603.0)}     # was (11800, 860, 1800) y 860
# ---- fuel: the floating scripted cans (group node of 'Group_Gas', the can node that stands in the air)
FLOATERS = {11654: 11676, 11625: 11650}
# new fuel cans: (x, z, floor y) anchors, wall side of the flats / corridors, one or two per floor; snapped to walk mesh with a 60 cm margin
FUEL_NEW = [(11200.0, 470.0, 1603.0), (12150.0, 470.0, 1603.0), (11700.0, 1750.0, 1603.0),
            (11700.0, 300.0, 1203.0), (12100.0, 300.0, 803.0), (11300.0, 300.0, 403.0)]
FUEL_TOP = 'KL_Gas!3'
# ---- doors: candidate hosts (live .prp node numbers from the 11-08 scan with h_tol 210..246); every host passes safety (spawn / exit distance) and the clearance walk
# (kl_doors_clear_1108.check_map), a host that fails is DROPPED and printed.
# FINDING (11-08 scan): of DD10's 129 door leaves (h_tol 210..246) NONE can take an OWN-LEAF kick door: 51 'PC1201_L05_Door_NN' leaves are centred on their origin
# (bb x -61..61) and 78 are wide along local z (kl_interact_graft.own_host refuses both), so every door here gets the Dog Days white kick leaf (own=False) in place of the map's.
# Flat entrances ('ApartmentMetalDoor_*', the flats' own doors, every floor; interleaved by floor so the cap keeps all floors) and the corridor / stairway leaves
# ('PC1201_L05_Door_*' in the Stairway groups):
FLAT_HOSTS = [1827, 3448, 2487, 5490, 2062, 3032, 2515, 5506, 1828, 3445, 2488, 5519, 1826, 3153, 2655, 5656, 1854, 3139, 2686, 5661, 6996, 5487]
DOOR_HOSTS = [2059, 3449, 2509, 5501, 2064, 3457, 2517, 5517]
MAX_DOORS = 26
FLOOR_TOL = 5.0                                   # cm: a placed object must stand within this of the collision floor
START_MIN = 900.0


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def need_live(in_dir):
    for n, want in LIVE_MD5.items():
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != want:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DD10 changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', want))
    if open(os.path.join(in_dir, BASE)).read().strip() != fmd5(os.path.join(in_dir, ZIP)):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')


def _import():
    global F, A, J, SK, ME, GAS, IG, DOORS, DC, kl_gms, kl_graft
    import kl_fa_bots as F, kl_fa_author as A, kl_prpjoin as J, kl_skyline_1108 as SK, kl_map_escape as ME
    import kl_dm01b_gas_1025 as GAS, kl_interact_graft as IG, kl_doors_1108 as DOORS, kl_doors_clear_1108 as DC
    import kl_gms, kl_graft


# ------------------------------------------------------------------ the plan
def floor_at(G, x, y, z):
    """Collision floor y of the highest walkable triangle not more than 120 above y (None: no floor)."""
    fl = [h for h in G.hits(x, z) if h[1] > 0.7 and h[0] <= y + 120.0]
    return fl[-1][0] if fl else None


def plan(zp, log=print):
    _import()
    B = F.Built(zp)
    nav = F.Nav(B.scene.nav)
    L = ME.Level(zp)
    G = ME.Ground(L)
    sc = B.sc
    starts = [B.at(k) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and 'Start' in sc.names[k]]
    P = dict(loot={}, float={}, fuel=[])
    for k, (x, z, fy) in LOOT_MOVES.items():
        sx, sy, sz = GAS.snap(nav, x, z, y=fy, reach=250.0)
        y = floor_at(G, sx, fy, sz)
        if y is None or abs(y - fy) > 40:
            raise SystemExit('REFUSED: no collision floor near y %s at loot place (%s, %s)' % (fy, sx, sz))
        near = min(math.hypot(sx - p[0], sz - p[2]) for p in starts if abs(p[1] - y) < 300) if any(abs(p[1] - y) < 300 for p in starts) else 1e9
        if near < 400:
            raise SystemExit('REFUSED: loot place %s is %.0f cm from a start spawn (LOOT_CLEAR 400)' % ((sx, sz), near))
        P['loot'][k] = (sx, y, sz, B.at(k))
        log('  loot %d: %s -> (%.0f, %.1f, %.0f)' % (k, [round(v) for v in B.at(k)], sx, y, sz))
    for g, can in FLOATERS.items():
        cx, cy, cz = B.at(can)
        r = G.under(cx, cy, cz)
        if r is None:
            raise SystemExit('REFUSED: no floor under can node %d at %s' % (can, (cx, cy, cz)))
        gy = B.at(g)
        P['float'][g] = (gy[0], gy[1] + (r[0] - cy), gy[2], (cx, cy, cz), r[0])
        log('  floating can %d (group %d): world y %.1f, floor %.1f -> group y %.1f' % (can, g, cy, r[0], P['float'][g][1]))
    for (x, z, fy) in FUEL_NEW:
        P['fuel'].append((x, z, fy))
    return P


# ------------------------------------------------------------------ step 1: placement only (loot + reseat)
def move_zip(src, dst, P, parts, log=print):
    B = F.Built(src)
    sc = B.sc
    shim = types.SimpleNamespace(prp=sc, ents=B.ents)
    moved = []
    if 'loot' in parts:
        for k, (x, y, z, old) in P['loot'].items():
            A.place(shim, k, (x, y, z))
            moved.append((k, tuple(round(v) for v in old), (round(x), round(y, 1), round(z))))
    if 'fuel' in parts:
        for g, (x, y, z, _c, _f) in P['float'].items():
            A.place(shim, g, (x, y, z))
            moved.append((g, None, (round(x), round(y, 1), round(z))))
    if not moved:
        shutil.copyfile(src, dst)
        return moved
    prp = sc.p.serialize()
    gms, buf = B.scene.write()
    if buf != B.files[B.ext['.buf']]:
        raise SystemExit('REFUSED: scene.write() does not reproduce the .buf (placement-only step would be wrong)')
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']] = prp, kl_gms.pack(gms)
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))
    log('  moved %d nodes %s' % (len(moved), moved))
    return moved


# ------------------------------------------------------------------ step 2: more fuel cans (kl_dm01b_gas_1025.build, adapted)
def fuel_spots3(B, nav):
    """kl_dm01b_gas_1025.fuel_spots with the start-spawn distance taken on the SAME floor only (the start spawns of DD10 are on the ground floor, the cans upstairs: the
    original 2-D rule would refuse every flat that lies above the start)."""
    starts = [B.at(k) for k in range(1, len(B.sc.nodes)) if B.sc.cls(k) == 'ZSpawnPoint' and 'Start' in B.sc.names[k]]
    out = []
    for anc in GAS.FUEL_ANCHORS:
        s = GAS.snap(nav, anc[0], anc[1], y=anc[2])
        same = [p for p in starts if abs(p[1] - s[1]) < 300.0]
        near = min([math.hypot(s[0] - p[0], s[2] - p[2]) for p in same] or [1e9])
        if near < START_MIN:
            raise ValueError('fuel can at %s is only %.0f cm from a start spawn on its floor' % (s, near))
        out.append(s)
    return out


def gas_zip(src, dst, anchors, log=print):
    GAS.fuel_spots = fuel_spots3
    GAS.TOP = FUEL_TOP
    GAS.FUEL_ANCHORS = [(x, z, fy) for x, z, fy in anchors]
    GAS.EXT_WALL = []
    GAS.START_Z = (0.0, 0.0)
    GAS.FUEL_MIN_START = START_MIN
    return GAS.build(src, dst, pin=None, log=log)


# ------------------------------------------------------------------ step 3: kick doors
def _hvk_equal_packed(zp_in, zp_out, new_refs=(), gone_refs=()):
    """kl_doors_clear_1108.hvk_equal assumes ONE new key-framed shape per new door slab (true on maps that already hold kick doors). DD10 has none yet: the graft packs all
    slabs of one size into ONE new shape with many instances, which that check reports as '1 non-static shapes are new, N new refs'. Same proof, that message accepted when every
    instance of every new non-static shape is a NEW ref (so nothing existing moved) and the shapes are key-framed (type 4)."""
    import kl_hvk
    bad = DC._hvk_equal_orig(zp_in, zp_out, new_refs, gone_refs)
    rest = [m for m in bad if not re.match(r'\d+ non-static shapes are new, \d+ new refs', m)]
    if len(rest) == len(bad):
        return bad

    def load(zp):
        with zipfile.ZipFile(zp) as z:
            return kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))
    a, b = load(zp_in), load(zp_out)
    old = {kl_hvk.ref(i) for s in a.shapes for i in s.inst}
    sig = lambda s: (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub))
    oldn = [(s.type, sig(s), tuple(bytes(i) for i in s.inst)) for s in a.shapes if s.type != 1]
    for s in b.shapes:
        if s.type == 1 or (s.type, sig(s), tuple(bytes(i) for i in s.inst)) in oldn:
            continue
        if s.type != 4 or any(kl_hvk.ref(i) in old for i in s.inst):
            rest.append('new non-static shape (type %d) holds an existing REF' % s.type)
    return rest


def doors_zip_patch():
    if not hasattr(DC, '_hvk_equal_orig'):
        DC._hvk_equal_orig = DC.hvk_equal
    DC.hvk_equal = _hvk_equal_packed
    DOORS.INIS = ('KLJoin.ini',)               # DD10 has no KLGuns.ini; the Entries= patch of KLJoin.ini is redone by stage() on the final zip


def doors_zip(in_dir, hosts, tmp, log=print):
    """-> (zip, bots zip, hosts kept, report). Hosts that fail safety or the clearance walk are dropped (printed), then the pass is rebuilt on the rest."""
    doors_zip_patch()
    h_orig = IG.door_hosts
    IG.door_hosts = lambda B, nav, **kw: h_orig(B, nav, h_tol=(210.0, 246.0), **kw)
    try:
        zn = os.path.join(in_dir, ZIP)
        top, base = DOORS.free_top(zn)
        B0 = F.Built(zn)
        nav = F.Nav(B0.scene.nav)
        allh = {h['k']: h for h in IG.door_hosts(B0, nav)}
        keep = []
        for k in hosts:
            if k not in allh:
                log('  host %d dropped: not a door host with h_tol 210..246 on this map' % k)
                continue
            try:
                DOORS.safety(zn, [k], lambda s: None)
            except ValueError as e:
                log('  host %d dropped (safety): %s' % (k, e))
                continue
            keep.append(k)
        keep = keep[:MAX_DOORS + 8]
        pins = tuple(fmd5(os.path.join(in_dir, n)) for n in (ZIP, BOTS, BASE))
        for rnd in range(3):
            DOORS.MAPS[MAP] = dict(slot=SLOT, dir=in_dir, ini_dir=LIVE, top=top, base=base, pins=pins, hosts=list(keep))
            out = os.path.join(tmp, 'doors%d' % rnd)
            os.makedirs(out, exist_ok=True)
            try:
                DOORS.stage_map(MAP, out, in_dir=in_dir, own=False, log=log, hosts=keep, clear=False)
            except ValueError as e:
                raise SystemExit('REFUSED: doors graft: %s' % e)
            res = os.path.join(out, MAP, ZIP)
            cc = DC.check_map(zn, res, keep, top, base, log=lambda s: None)
            bad = {k: v['problems'] for k, v in cc.items() if v['problems']}
            for k, p in bad.items():
                log('  host %d dropped (clearance): %s' % (k, p[0][:160]))
            if len(keep) - len(bad) > MAX_DOORS:
                extra = [k for k in keep if k not in bad][MAX_DOORS:]
                for k in extra:
                    log('  host %d dropped (over the %d door cap)' % (k, MAX_DOORS))
                bad.update({k: ['cap'] for k in extra})
            if not bad:
                return res, os.path.join(out, MAP, BOTS), keep, dict(top=top, base=base)
            keep = [k for k in keep if k not in bad]
            shutil.rmtree(out, ignore_errors=True)
        raise SystemExit('REFUSED: door selection did not settle')
    finally:
        IG.door_hosts = h_orig


# ------------------------------------------------------------------ the stage
def make_install(out, stage_md5):
    t = open(TEMPLATE, encoding='utf-8').read()
    rows = ["    ('%s', '%s', '%s')," % (n, LIVE_MD5[n], stage_md5[n]) for n in (ZIP, BOTS, BASE, JOIN)]
    t, k = re.subn(r"FILES = \[.*?\n\]\n", lambda m: "FILES = [   # name, live md5 before, staged md5 after\n" + '\n'.join(rows) + "\n]\n", t, flags=re.S)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES block')
    t, k = re.subn(r"MAP, TAG = 'DM05A', '\.before-[a-z0-9]+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5[ZIP], t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single LIVE_ZIP_MD5 line')
    t = t.replace("DM05A CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)", "DD10 %s (tools/kl_dd10_flats_1108.py)" % TITLE)
    t = t.replace('F01_Main', 'F07_Main').replace('.before-skyline1108', TAG)
    t = t.replace('DM05A', MAP)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for nm, arg in (('INSTALL DD10 flats 1108.bat', ''), ('UNDO DD10 flats 1108.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')


def census(zp):
    B = F.Built(zp)
    c = collections.Counter(B.sc.cls(k) for k in range(1, len(B.sc.nodes)))
    return len(B.ents), dict(c), B


def stage(in_dir, out_root, parts, log=print, keep_tmp=False):
    _import()
    need_live(in_dir)
    bad = [p for p in parts if p not in PARTS_ALL]
    if bad:
        raise SystemExit('REFUSED: part %s not built (parts: %s; vanfix is not built, see the docstring)' % (bad, ','.join(PARTS_ALL)))
    out = os.path.join(out_root, NAME)
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='flats_', dir=out)
    rep = dict(parts=list(parts))
    try:
        zl = os.path.join(in_dir, ZIP)
        P = plan(zl, log)
        cur = {ZIP: zl, BOTS: os.path.join(in_dir, BOTS)}
        # 1 placement
        if 'loot' in parts or 'fuel' in parts:
            d = os.path.join(tmp, 's1'); os.makedirs(d)
            for n in (ZIP, BOTS):
                log('== placement %s' % n)
                rep['moved'] = move_zip(cur[n], os.path.join(d, n), P, parts, log)
                cur[n] = os.path.join(d, n)
        # 2 cans
        if 'fuel' in parts:
            d = os.path.join(tmp, 's2'); os.makedirs(d)
            for n in (ZIP, BOTS):
                log('== fuel cans %s' % n)
                r = gas_zip(cur[n], os.path.join(d, n), P['fuel'], log)
                cur[n] = os.path.join(d, n)
                if n == ZIP:
                    rep['fuel'] = dict(spots=[tuple(round(v, 1) for v in s) for s in r.get('fuel', [])], changed=r.get('changed'))
        # 3 doors
        hosts = (FLAT_HOSTS if 'flats' in parts else []) + (DOOR_HOSTS if 'doors' in parts else [])
        if hosts:
            d = os.path.join(tmp, 's3in'); os.makedirs(d)
            for n in (ZIP, BOTS):
                os.replace(cur[n], os.path.join(d, n)) if os.path.dirname(cur[n]).startswith(tmp) else shutil.copyfile(cur[n], os.path.join(d, n))
                cur[n] = os.path.join(d, n)
            open(os.path.join(d, BASE), 'w', newline='\n').write(fmd5(cur[ZIP]) + '\n')
            log('== kick doors (%d candidates)' % len(hosts))
            res, resb, kept, drep = doors_zip(d, hosts, tmp, log)
            cur[ZIP], cur[BOTS] = res, resb
            rep['doors'] = dict(kept=kept, **drep)
        if cur[ZIP] == zl:
            raise SystemExit('REFUSED: nothing selected')
        # plain / bots differ only in the .prp
        with zipfile.ZipFile(cur[ZIP]) as a, zipfile.ZipFile(cur[BOTS]) as b, zipfile.ZipFile(zl) as la, zipfile.ZipFile(os.path.join(in_dir, BOTS)) as lb:
            ldiff = [m for m in la.namelist() if m in lb.namelist() and la.read(m) != lb.read(m)]
            diff = [m for m in a.namelist() if m in b.namelist() and a.read(m) != b.read(m)]
            if sorted(diff) != sorted(ldiff):
                raise SystemExit('REFUSED: plain and bots zips differ in %s, the live pair differs in %s' % (diff, ldiff))
            bad = [m for m in a.namelist() if m in la.namelist() and a.read(m) != la.read(m) and not m.endswith(CHANGED_OK)]
            if bad or a.namelist() != la.namelist():
                raise SystemExit('REFUSED: members changed outside the allowed set: %s' % bad)
        for n in (ZIP, BOTS):
            shutil.move(cur[n], os.path.join(out, n))
    finally:
        if not keep_tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    plain = fmd5(os.path.join(out, ZIP))
    open(os.path.join(out, BASE), 'w', newline='\n').write(plain + '\n')
    chunks = DOORS.chunks(os.path.join(out, ZIP))
    data, c = DOORS.patch_entries(os.path.join(in_dir, JOIN), chunks)
    if c != 1:
        raise SystemExit('REFUSED: %d Entries= lines in KLJoin.ini' % c)
    open(os.path.join(out, JOIN), 'wb').write(data)
    sm = {n: fmd5(os.path.join(out, n)) for n in (ZIP, BOTS, BASE, JOIN)}
    make_install(out, sm)
    ini = os.path.join(GAME, 'KLHook.ini')
    cover = [ln.rstrip('\r\n') for ln in open(ini, encoding='latin1') if ln.split('=')[0].strip() in ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientBuildMaps', 'ClientRewrite', 'ClientRingSync')]
    open(os.path.join(out, 'bench_cover_lines.txt'), 'w').write('\n'.join(cover) + '\n')
    rep.update(md5=sm, chunks=chunks)
    json.dump(rep, open(os.path.join(out, 'build_report.json'), 'w'), indent=1, default=str)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):    # --keep-tmp leaves a directory here
        log('  %-30s %s' % (n, fmd5(os.path.join(out, n))))
    return out


# ------------------------------------------------------------------ the checks
def check(in_dir, out_root, log=print, undo_rehearsal=True):
    _import()
    out = os.path.join(out_root, NAME)
    rep = json.load(open(os.path.join(out, 'build_report.json')))
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    zl, zn = os.path.join(in_dir, ZIP), os.path.join(out, ZIP)
    n0, c0, B0 = census(zl)
    n1, c1, B1 = census(zn)
    log('census entities %d -> %d' % (n0, n1))
    for cl in sorted(set(c0) | set(c1)):
        if c0.get(cl, 0) != c1.get(cl, 0):
            log('   %-22s %6d -> %6d' % (cl, c0.get(cl, 0), c1.get(cl, 0)))
    prp = B1['.prp']
    need(F.Prp(prp).serialize() == prp, '.prp round trip (F.Prp serialize == bytes)')
    need(B1.sc.p.serialize() == prp, '.prp round trip (Built scene)')
    need(not B1.scene.check(), 'kl_scene.check clean')
    L = ME.Level(zn)
    G = ME.Ground(L)
    # every moved / added object: z within FLOOR_TOL above the floor, nothing solid in its way
    sc = B1.sc
    # rep['moved'] ids are LIVE node numbers; the kick-door pass removes the leaves it replaces, so every later node moves down (21 here): map by node PATH
    # (review 2026-11-08: the first version looked the live numbers up in the staged scene and read OnScreenMSG / POI nodes instead of the stacks)
    p1 = {pth: i for i, pth in enumerate(B1.sc.path) if pth}
    n1 = lambda k0: p1[B0.sc.path[k0]]
    objs = []
    for k0 in [m[0] for m in rep.get('moved', [])]:
        k = n1(k0)
        objs.append((k, B1.at(k)))
    for k in range(1, len(sc.nodes)):
        if sc.path[k].startswith('ROOT' + BS + FUEL_TOP + BS) and sc.cls(k) == 'ZHavokRigidBody':
            objs.append((k, B1.at(k)))
    for k, p in objs:
        fl = floor_at(G, p[0], p[1], p[2])
        solid = [h for h in G.hits(p[0], p[2]) if fl is not None and fl + 3.0 < h[0] < fl + 60.0]
        isfl = B1.sc.path[k] in {B0.sc.path[g] for g in FLOATERS}
        if isfl:
            can = n1(FLOATERS[next(g for g in FLOATERS if B0.sc.path[g] == B1.sc.path[k])])
            cp = B1.at(can)
            fl = floor_at(G, cp[0], cp[1], cp[2])
            need(fl is not None and -FLOOR_TOL <= cp[1] - fl <= FLOOR_TOL, 'floating can %d: %.1f cm above the collision floor %.1f' % (can, cp[1] - fl if fl is not None else 1e9, fl or 0))
        else:
            need(fl is not None and -FLOOR_TOL <= p[1] - fl <= FLOOR_TOL + 60, 'node %d %s: %.1f cm above the collision floor' % (k, sc.names[k][:30], (p[1] - fl) if fl is not None else 1e9))
            need(not solid, 'node %d: no collision triangle in the 60 cm above it at %s' % (k, [round(h[0]) for h in solid]))
    if 'doors' in rep:
        need(DOORS.free_top(zn)[1] >= DOORS.free_top(zl)[1] + len(rep['doors']['kept']), 'kick doors %d -> %d (+%d hosts)' % (DOORS.free_top(zl)[1], DOORS.free_top(zn)[1], len(rep['doors']['kept'])))
    # money: the same eight stacks, the same 4M
    m0, m1 = F.money_objects(B0), F.money_objects(B1)
    need(len(m0) == len(m1) and sum(m['amount'] for m in m0) == sum(m['amount'] for m in m1), 'money stacks %d / %d total %d -> %d' % (len(m0), len(m1), sum(m['amount'] for m in m0), sum(m['amount'] for m in m1)))
    log('  money by floor before %s after %s' % (sorted(collections.Counter(round(m['at'][1] / 400) * 400 for m in m0).items()), sorted(collections.Counter(round(m['at'][1] / 400) * 400 for m in m1).items())))
    need(open(os.path.join(out, BASE)).read().strip() == fmd5(zn), 'bots.base.md5 = md5 of the plain zip')
    ent = int(re.search(r'(?m)^Entries\s*=\s*(\d+)', open(os.path.join(out, JOIN)).read()).group(1))
    need(ent == DOORS.chunks(zn), 'KLJoin.ini Entries=%d = .prm chunks %d' % (ent, DOORS.chunks(zn)))
    # install --dry on a scratch game folder, then install + undo byte for byte
    if undo_rehearsal:
        sg = tempfile.mkdtemp(prefix='flatsgame_', dir=out)
        try:
            d = os.path.join(sg, 'KLExpansion', 'Maps', MAP)
            os.makedirs(d)
            for n in LIVE_MD5:
                shutil.copyfile(os.path.join(in_dir, n), os.path.join(d, n))
            before = {n: fmd5(os.path.join(d, n)) for n in LIVE_MD5}
            run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', sg, '--skip-run-check'] + list(a), capture_output=True, text=True)
            r = run('--dry')
            need(r.returncode == 0, 'install.py --dry rc %d' % r.returncode)
            r = run()
            need(r.returncode == 0 and all(fmd5(os.path.join(d, n)) == json.load(open(os.path.join(out, 'build_report.json')))['md5'][n] for n in LIVE_MD5), 'scratch install lands the staged md5s')
            r = run('--undo')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in LIVE_MD5} == before, 'scratch undo restores every file byte for byte')
        finally:
            shutil.rmtree(sg, ignore_errors=True)
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('plan', 'stage', 'check'):
        print(__doc__); return 2
    in_dir = opt('--in-dir', LIVE)
    parts = [p for p in opt('--parts', ','.join(PARTS_ALL)).split(',') if p]
    if a[0] == 'plan':
        need_live(in_dir)
        P = plan(os.path.join(in_dir, ZIP))
        print('fuel anchors', P['fuel'])
        return 0
    if a[0] == 'stage':
        stage(in_dir, opt('--out-root', OUT_ROOT), parts, keep_tmp='--keep-tmp' in a)
        return 0
    return 0 if check(in_dir, opt('--out-root', OUT_ROOT), undo_rehearsal='--no-undo' not in a) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
