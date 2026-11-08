#!/usr/bin/env python3
r"""kl_dd10_vancall_1108.py - Flat Raid (DD10 = Dog Days L05 in the F07 slot): the escape van is shown on APPROACH, the escape marker is lit from the alarm, and the
secret ledge route lands clear of the van. Stage built from the LIVE files (2026-11-08, offline, stage only; nothing is installed, no game is launched).

OWNER (quoted): "for flat raid u can jump out the balcony n u get stuck and i specifically said to make it a secret route to get to the van too, and the van spawns
at the spawn right? it still blown up and yeah cant escape".

CHAIN, READ FROM THE LIVE SCENE (MEASURED, not run): the van group EscapeVehicle_Animation_F07 (node 21786) is hidden from the load (ZGEOM[3] = 1, .gms 0x3200400; stock
F07 never hides it: 0x3200000). Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT (ActivateGeom, node 21983) is the ONLY show, fired by the van timer
(RivalMercs!DisableVisionBlocker!Timer, 8 s) which the flats' floor box (tb_RIGHT_TheySpotYou) and the backstop (RivalMercVan!Timer, 165 s) start. So the van is on
screen 8 s after the alarm, parked at its wait key, whether or not anybody is near. The CALL is Gameplay!EscapeSetup!otrExitLevel (OnlineExitLevelTrigger, box 450 x 300 x 450
at (8300, 200, 1100), field 2 = the group): a heister inside it calls the van. Box FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn (node 22127) has the SAME box,
ECPS_CP_OFFENSEONLY, which never counts anybody in Fragile Alliance (re/triggerbox.md): DEAD in this mode.

PARTS (--parts, default hide,cue,landing):
  hide     the van timer no longer shows the van (21983 off its list). Node 22127 is REPURPOSED as the approach box: centre (8300, 200, 1100) kept, half 800 x 300 x 450
           (x 7500..9100, z 650..1550 = the street, z extent = the exit box so it holds the exit box), ECPS_FA_MERCONLY, f10 = 0 (fires on every enter edge: round 2 works, the reset DeactivateGeom hides the van again),
           f17 = [GeomActivator_TearGas_LEFT]. Its old list (tutorial check, loot-area deactivator, escape POI) goes: that box never fired. The van therefore appears when
           the first heister walks into the street from the west gate (x 7500, ~800 cm before the stop), or lands on it by the ledge route.
           GUESS 1: the van's drive-in animation runs while the group is hidden (ZGEOM[3] = 1 hides RENDER only, the layer's hidden-but-live evidence), so a call that
           comes the same frame as the show (the landing is inside both boxes) still drives in; at worst the first frames of the drive-in are not drawn.
           GUESS 2: ActivateGeom 'AITrigger' sets the group visible on every fire (it is how the layer shows it today).
  cue      the escape POI (POI_TheEscapeArea, plus CheckMPTutorialOption#02 as the van timer sends it) is also fired by the floor box and the backstop, i.e. from the ALARM
           instead of alarm + 8 s: with the van hidden until approach, the marker is the player's only pointer. GUESS: firing PointOfInterest twice (the van timer still
           fires it, and it is already reached by both the floor box and the backstop) is idempotent (stock already sends it twice in the unfixed chain).
  callback NOT BUILT (REFUSED if asked). The task wanted the backstop to call the van "ONLY if provable". OnlineExitLevelTrigger has no output list, slot 34 (0x6c3d50)
           needs an activator body and calls the rules' slot 44 only when the vehicle state is 0; an 'AITrigger' message from a timer has no body, so a call without a heister in
           the box is UNPROVEN. Left out on purpose: the van is still only called by a heister in the exit box.
  landing  KLJoin.ini [Join.3] Target 8300 0 1100 -> 8500 0 1180. The old target is inside the stopped van (stop x 8640, z 1030 after the lane fix, collision box z ~930..1130,
           x 8300..8900): the ledge-route heister landed in the van's body and was stuck. MEASURED on the collision (kl_map_escape.Ground): floor y 0 at the target, no
           solid between 30 and 260 above it within 40 cm; it is 50 cm from the van's side (half width 100). The target is inside the exit and the approach
           boxes, so the landing shows and calls the van. GUESS: Tolerance 8 and Slack 150 of [Join.3] are unchanged and still fit the new place.

Changes ONLY F07_Main.prp of the plain AND the bots zip (hide, cue) and KLJoin.ini (landing); the .gms / .buf / .HVK are byte-equal (no node moves, no flag changes).
F07_Main.bots.base.md5 = md5 of the plain staged zip.

  python tools/kl_dd10_vancall_1108.py stage [--parts hide,cue,landing] [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_dd10_vancall_1108.py check [--parts ...] [--in-dir ...] [--out-root ...] [--no-undo]
Never installs anything. REFUSES unless the live files are the expected md5s and the nodes hold the pre-edit values."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))
import kl_fa
import kl_fa_bots as F
import kl_fa_author as A
import kl_gms
import kl_map_escape as ME
import kl_prpjoin as J
import kl_skyline_1108 as SK

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DD10')
OUT_ROOT = 'C:/kl_build_1024'
MAP, SLOT = 'DD10', 'F07'
NAME, TAG, TITLE = 'dd10vancall_1108', '.before-dd10vancall1108', 'DD10VANCALL1108'
TEMPLATE = 'C:/kl_build_1024/citylights_1108/install.py'
ZIP, BOTS, BASE, JOIN = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5', 'KLJoin.ini'
LIVE_MD5 = {ZIP: '13bc6388855ade7b31cb5c3bd47bf9d3', BOTS: '488872aa72b4a2fcbeeda20bc81a49a3', BASE: '2d73022b814a68aa8ba6bc314eb48217',
            JOIN: '30482fec0845857a0abb80e7d22066c9'}
PARTS_ALL = ('hide', 'cue', 'landing')
BS = chr(92)
R = 'ROOT' + BS

VAN_ON = R + 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT'            # ActivateGeom -> the van group (node 21983)
VAN_GROUP = R + 'Animation/F07/F07_Escape_Vehicle_01.zip' + BS + 'EscapeVehicle_Animation_F07'
VAN_TIMER = R + 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!Timer'
FLOOR_BOX = R + 'Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou'
BACKSTOP = R + 'Gameplay!010_FirstFight!RivalMercVan!Timer'
DEAD_BOX = R + 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn'          # node 22127, ECPS_CP_OFFENSEONLY = never in FA
EXIT_BOX = R + 'Gameplay!EscapeSetup!otrExitLevel'
POI = R + 'FASpecials!POI!POI_TheEscapeArea'
POI_CHECK = R + 'FASpecials!POI!CheckMPTutorialOption#02'
DEAD_OLD = [POI_CHECK, R + 'FASpecials!POI!GeomDeactivator_TheLootArea', POI]
APPROACH_HALF = (800.0, 300.0, 450.0)
APPROACH_AT = (8300.0, 200.0, 1100.0)
OLD_TARGET, NEW_TARGET = '8300 0 1100', '8500 0 1180'
STOP = (8640.0, 1030.0)                  # the van's stop (origin) after the lane fix (kl_dd10_vanlane_1108)
VAN_HALF_W = 100.0


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ the scene edits
def values(sc, cname, node_name):
    k = A.node_of(sc, node_name)
    for kk, i, v in kl_fa.controllers(sc, cname):
        if kk == k:
            return k, i, v
    raise SystemExit('REFUSED: %s has no %s' % (node_name, cname))


def setf(sc, k, cname, fields):
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, cname), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])


def pre_check(sc, parts):
    """REFUSES unless this is the pre-edit state."""
    if values(sc, 'ActivateGeom', VAN_ON)[2][1] != [VAN_GROUP]:
        raise SystemExit('REFUSED: the van-on ActivateGeom does not hold the van group')
    vt = values(sc, 'TriggerDelay2', VAN_TIMER)[2]
    if VAN_ON not in vt[4] or POI not in vt[4]:
        raise SystemExit('REFUSED: the van timer list is not the pre-edit one: %r' % (vt[4],))
    if 'hide' in parts:
        vb = values(sc, 'TriggerBox', DEAD_BOX)[2]
        if vb[14] != 'ECPS_CP_OFFENSEONLY' or vb[17] != DEAD_OLD:
            raise SystemExit('REFUSED: the dead box is not the pre-edit one: %r %r' % (vb[14], vb[17]))
    if 'cue' in parts and POI in values(sc, 'TriggerBox', FLOOR_BOX)[2][17]:
        raise SystemExit('REFUSED: the floor box already fires the POI')


def edit_scene(B, parts, log=print):
    sc = B.sc
    pre_check(sc, parts)
    if 'hide' in parts:
        k, _i, vt = values(sc, 'TriggerDelay2', VAN_TIMER)
        setf(sc, k, 'TriggerDelay2', {'f4': [x for x in vt[4] if x != VAN_ON]})
        kb = A.node_of(sc, DEAD_BOX)
        A.place(types.SimpleNamespace(prp=sc, ents=B.ents), kb, APPROACH_AT, half=APPROACH_HALF)
        setf(sc, kb, 'TriggerBox', {'f10': 0, 'f14': 'ECPS_FA_MERCONLY', 'f15': 0, 'f17': [VAN_ON]})   # f15 0 = ANY heister counts (kept 1 = local human only: a bot / remote / dedicated host would never show the van; review fix 2026-11-08)
        log('  hide: van timer list minus the van show; node %d = approach box half %s, FA_MERCONLY, every edge -> van on' % (kb, APPROACH_HALF))
    if 'cue' in parts:
        add = [POI_CHECK, POI]
        k, _i, vf = values(sc, 'TriggerBox', FLOOR_BOX)
        setf(sc, k, 'TriggerBox', {'f17': list(vf[17]) + add})
        k, _i, vs = values(sc, 'TriggerDelay2', BACKSTOP)
        setf(sc, k, 'TriggerDelay2', {'f4': list(vs[4]) + add})
        log('  cue: floor box and backstop also fire the escape POI (+ tutorial check)')


def patch_zip(src, dst, parts, log=print):
    B = F.Built(src)
    edit_scene(B, parts, log)
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))


# ------------------------------------------------------------------ KLJoin.ini
def patch_join(src_bytes):
    t = src_bytes.decode('latin1')
    m = re.search(r'(?ms)^\[Join\.3\]\r?\n(.*?)(?=^\[|\Z)', t)
    if not m or m.group(1).count('Target=' + OLD_TARGET) != 1 or 'Name=06_Exit' not in m.group(1):
        raise SystemExit('REFUSED: [Join.3] is not the 06_Exit join with Target=%s' % OLD_TARGET)
    nl = '\r\n' if '\r\n' in t else '\n'
    body = m.group(1).replace('Target=' + OLD_TARGET, 'Target=' + NEW_TARGET)
    body = ("; 2026-11-08 vancall: landing moved out of the van's body (8300 0 1100) to 8500 0 1180 (kl_dd10_vancall_1108.py; GUESS: Tolerance / Slack still fit)." + nl) + body
    return (t[:m.start(1)] + body + t[m.end(1):]).encode('latin1')


# ------------------------------------------------------------------ install
def parts_zip(parts):
    return bool({'hide', 'cue'} & set(parts))


def staged_files(parts):
    return ([ZIP, BOTS, BASE] if parts_zip(parts) else []) + ([JOIN] if 'landing' in parts else [])


def make_install(out, stage_md5, files):
    t = open(TEMPLATE, encoding='utf-8').read()
    rows = ["    ('%s', '%s', '%s')," % (n, LIVE_MD5[n], stage_md5[n]) for n in files]
    t, k = re.subn(r"FILES = \[.*?\n\]\n", lambda m: "FILES = [   # name, live md5 before, staged md5 after\n" + '\n'.join(rows) + "\n]\n", t, flags=re.S)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES block')
    t, k = re.subn(r"MAP, TAG = 'DM05A', '\.before-[a-z0-9]+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5[ZIP], t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single LIVE_ZIP_MD5 line')
    t = t.replace("DM05A CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)", "DD10 %s (tools/kl_dd10_vancall_1108.py)" % TITLE)
    t = t.replace('F01_Main', 'F07_Main').replace('.before-skyline1108', TAG)
    t = t.replace('DM05A', MAP)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for nm, arg in (('INSTALL DD10 vancall 1108.bat', ''), ('UNDO DD10 vancall 1108.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')


def need_live(in_dir, parts):
    for n in staged_files(parts) + ([BASE] if False else []):
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != LIVE_MD5[n]:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DD10 changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', LIVE_MD5[n]))
    if parts_zip(parts) and open(os.path.join(in_dir, BASE)).read().strip() != fmd5(os.path.join(in_dir, ZIP)):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')


def stage(in_dir, out_root, parts, log=print):
    if 'callback' in parts:
        raise SystemExit('REFUSED: callback is not built: an AITrigger message cannot call OnlineExitLevelTrigger without an activator body (see the docstring)')
    bad = [p for p in parts if p not in PARTS_ALL]
    if bad or not parts:
        raise SystemExit('REFUSED: parts %s (built: %s)' % (bad or parts, ','.join(PARTS_ALL)))
    need_live(in_dir, parts)
    out = os.path.join(out_root, NAME)
    os.makedirs(out, exist_ok=True)
    for old in (ZIP, BOTS, BASE, JOIN):
        if os.path.exists(os.path.join(out, old)):
            os.remove(os.path.join(out, old))
    log('stage -> %s (parts %s)' % (out, ','.join(parts)))
    if parts_zip(parts):
        for n in (ZIP, BOTS):
            log(n)
            patch_zip(os.path.join(in_dir, n), os.path.join(out, n), parts, log)
        with open(os.path.join(out, BASE), 'w', newline='\n') as f:
            f.write(fmd5(os.path.join(out, ZIP)) + '\n')
    if 'landing' in parts:
        open(os.path.join(out, JOIN), 'wb').write(patch_join(open(os.path.join(in_dir, JOIN), 'rb').read()))
    files = staged_files(parts)
    sm = {n: fmd5(os.path.join(out, n)) for n in files}
    make_install(out, sm, files)
    ini = os.path.join(GAME, 'KLHook.ini')
    cover = [ln.rstrip('\r\n') for ln in open(ini, encoding='latin1') if ln.split('=')[0].strip() in ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientBuildMaps', 'ClientRewrite', 'ClientRingSync')]
    open(os.path.join(out, 'bench_cover_lines.txt'), 'w').write('\n'.join(cover) + '\n')
    json.dump(dict(parts=list(parts), md5=sm, live=LIVE_MD5, tag=TAG), open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):
        log('  %-32s %s' % (n, fmd5(os.path.join(out, n))))
    return out


# ------------------------------------------------------------------ the checks
def node_diff(a, b):
    if len(a.nodes) != len(b.nodes):
        return [('node count', len(a.nodes), len(b.nodes))]
    out = []
    for k in range(1, len(a.nodes)):
        na, nb = a.nodes[k], b.nodes[k]
        if na['props'] != nb['props'] or len(na['ctrls']) != len(nb['ctrls']) or any(x != y for x, y in zip(na['ctrls'], nb['ctrls'])):
            out.append(k)
    return out


def landing_report(zp):
    """-> (ok, text): the new landing against the collision and the stopped van."""
    G = ME.Ground(ME.Level(zp))
    x, y, z = [float(v) for v in NEW_TARGET.split()]
    fl = [h[0] for h in G.hits(x, z) if -50 < h[0] < 30]
    solid = []
    for dx in (-40, -20, 0, 20, 40):
        for dz in (-40, -20, 0, 20, 40):
            solid += [(dx, dz, round(h[0])) for h in G.hits(x + dx, z + dz) if 30 < h[0] < 260]
    side = z - (STOP[1] + VAN_HALF_W)
    ok = bool(fl) and abs(fl[0] - y) <= 3 and not solid and side >= 40
    return ok, 'landing (%g, %g, %g): floor %s, solids 30..260 within 40 cm %s, %.0f cm from the van side (z %.0f)' % (x, y, z, [round(v) for v in fl], solid[:4], side, STOP[1] + VAN_HALF_W)


def check(in_dir, out_root, parts, log=print, undo_rehearsal=True):
    out = os.path.join(out_root, NAME)
    rep = json.load(open(os.path.join(out, 'build_report.json')))
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    need(rep['parts'] == list(parts), 'staged parts %s' % rep['parts'])
    files = staged_files(parts)
    if parts_zip(parts):
        for n in (ZIP, BOTS):
            base, stg = os.path.join(in_dir, n), os.path.join(out, n)
            with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
                need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
                changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
                need(changed == ['.prp'], '%s: only .prp differs (changed: %s): .gms .buf .HVK byte-equal' % (n, changed))
            Bb, Bs = F.Built(base), F.Built(stg)
            sc = Bs.sc
            need(sc.p.serialize() == Bs['.prp'] and kl_gms.pack(Bs.scene.write()[0]) == Bs['.gms'], '%s: .prp and .gms round-trip' % n)
            need(F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip (F.Prp)' % n)
            want = set()
            for nm in ((VAN_TIMER, DEAD_BOX) if 'hide' in parts else ()) + ((FLOOR_BOX, BACKSTOP) if 'cue' in parts else ()):
                want.add(A.node_of(Bb.sc, nm))
            need(set(node_diff(Bb.sc, sc)) == want, '%s: .prp: exactly these nodes differ %s' % (n, sorted(want)))
            if 'hide' in parts:
                vt = values(sc, 'TriggerDelay2', VAN_TIMER)[2]
                vt0 = values(Bb.sc, 'TriggerDelay2', VAN_TIMER)[2]
                need(VAN_ON not in vt[4] and POI in vt[4] and vt[4] == [x for x in vt0[4] if x != VAN_ON], '%s: van timer no longer shows the van, still fires the POI (%d targets)' % (n, len(vt[4])))
                vb = values(sc, 'TriggerBox', DEAD_BOX)[2]
                need(vb[14] == 'ECPS_FA_MERCONLY' and vb[10] == 0 and vb[15] == 0 and vb[17] == [VAN_ON] and vb[0] == 1 and vb[1] == 1 and vb[2] == 1, '%s: approach box: FA_MERCONLY, every edge, enter, list = van on' % n)
                kb = A.node_of(sc, DEAD_BOX)
                lab = J.labels('dd', sc.cls(kb))
                vv = kl_fa.node_values(sc, kb)
                need([vv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3)] == list(APPROACH_HALF) and vv[lab.index('ZGEOM[2]')] == list(APPROACH_AT), '%s: approach box half %s at %s' % (n, APPROACH_HALF, APPROACH_AT))
                need(Bs.ents[kb - 1].trans == Bb.ents[kb - 1].trans and Bs.ents[kb - 1].flags == Bb.ents[kb - 1].flags, '%s: its .gms record unchanged' % n)
                ke = A.node_of(sc, EXIT_BOX)
                le = J.labels('dd', sc.cls(ke))
                ve = kl_fa.node_values(sc, ke)
                eh = [ve[le.index('ZBoxPrimitive[%d]' % i)] for i in range(3)]
                ec = ve[le.index('ZGEOM[2]')]
                need(all(abs(ec[i] - APPROACH_AT[i]) + eh[i] <= APPROACH_HALF[i] + 1e-3 for i in (0, 2)), '%s: the exit box %s at %s lies inside the approach box in x and z' % (n, eh, ec))
                need(values(sc, 'OnlineExitLevelTrigger', EXIT_BOX)[2][2] == VAN_GROUP, '%s: the exit trigger (the call) is untouched and names the van group' % n)
                need(values(sc, 'ActivateGeom', VAN_ON)[2][1] == [VAN_GROUP], '%s: van-on ActivateGeom untouched' % n)
            if 'cue' in parts:
                vf, vf0 = values(sc, 'TriggerBox', FLOOR_BOX)[2], values(Bb.sc, 'TriggerBox', FLOOR_BOX)[2]
                need(vf[17] == list(vf0[17]) + [POI_CHECK, POI], '%s: floor box list + POI' % n)
                vs, vs0 = values(sc, 'TriggerDelay2', BACKSTOP)[2], values(Bb.sc, 'TriggerDelay2', BACKSTOP)[2]
                need(vs[4] == list(vs0[4]) + [POI_CHECK, POI], '%s: backstop list + POI' % n)
        need(open(os.path.join(out, BASE)).read().strip() == fmd5(os.path.join(out, ZIP)), 'bots.base.md5 = md5 of the plain staged zip')
        with zipfile.ZipFile(os.path.join(in_dir, ZIP)) as a, zipfile.ZipFile(os.path.join(in_dir, BOTS)) as b, zipfile.ZipFile(os.path.join(out, ZIP)) as c, zipfile.ZipFile(os.path.join(out, BOTS)) as d:
            ld = [m for m in a.namelist() if a.read(m) != b.read(m)]
            sd = [m for m in c.namelist() if c.read(m) != d.read(m)]
            need(ld == sd, 'plain and bots zips differ only in %s (live %s)' % (sd, ld))
    if 'landing' in parts:
        old = open(os.path.join(in_dir, JOIN), 'rb').read().decode('latin1').splitlines()
        new = open(os.path.join(out, JOIN), 'rb').read().decode('latin1').splitlines()
        dl = [ln for ln in new if ln not in old]
        need(len(new) == len(old) + 1 and len(dl) == 2 and 'Target=' + NEW_TARGET in dl, 'KLJoin.ini: one Target line changed + one comment added (%s)' % [d[:50] for d in dl])
        ok, txt = landing_report(os.path.join(in_dir, ZIP))
        need(ok, txt)
        ent = lambda p: re.search(r'(?m)^Entries\s*=\s*(\d+)', open(p, encoding='latin1').read()).group(1)
        need(ent(os.path.join(out, JOIN)) == ent(os.path.join(in_dir, JOIN)), 'KLJoin.ini Entries= unchanged (%s)' % ent(os.path.join(out, JOIN)))
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in files:
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    if undo_rehearsal:
        sg = tempfile.mkdtemp(prefix='vancallgame_', dir=out)
        try:
            d = os.path.join(sg, 'KLExpansion', 'Maps', MAP)
            os.makedirs(d)
            for n in LIVE_MD5:
                shutil.copyfile(os.path.join(in_dir, n), os.path.join(d, n))
            before = {n: fmd5(os.path.join(d, n)) for n in LIVE_MD5}
            run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', sg, '--skip-run-check', '--min-free-mb', '0'] + list(a), capture_output=True, text=True)
            r = run('--dry')
            need(r.returncode == 0, 'install.py --dry rc %d %s' % (r.returncode, (r.stdout + r.stderr).strip()[-120:]))
            r = run()
            need(r.returncode == 0 and all(fmd5(os.path.join(d, n)) == (fmd5(os.path.join(out, n)) if n in files else before[n]) for n in LIVE_MD5), 'scratch install lands the staged md5s (others untouched)')
            r = run('--undo')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in LIVE_MD5} == before, 'scratch undo restores every file byte for byte')
        finally:
            shutil.rmtree(sg, ignore_errors=True)
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check'):
        print(__doc__)
        return 2
    in_dir, out_root = opt('--in-dir', LIVE), opt('--out-root', OUT_ROOT)
    parts = [p for p in opt('--parts', ','.join(PARTS_ALL)).split(',') if p]
    if a[0] == 'stage':
        stage(in_dir, out_root, parts)
    return 0 if check(in_dir, out_root, parts, undo_rehearsal='--no-undo' not in a) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
