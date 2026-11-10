#!/usr/bin/env python3
r"""kl_exitstrip_1110.py - shrink the exit box (Gameplay!EscapeSetup!otrExitLevel, the box that CALLS the escape van) to a strip OFF the van's lane, per map.
Generalises tools/kl_dd10_exitsouth_1110.py (DD10) to DM01B (slot F03), DM06B (F02) and DM07 (F06). Stage built from the LIVE files (2026-11-10, offline,
stage only; nothing is installed, no game is launched).

Why: OnlineExitLevelTrigger (field 2 = the van group) is a 450 x 300 x 450 box and the key-framed van drives (and parks, and reverses out) through its middle: a heister
who waits in the box for the van is run over by the drive-in (DD10 bench dd10call1109: seat at the box centre died ~4 s in, seat in the clear strip lived).
The audit (vanaudit sweep) found the same overlap on DM01B, DM06B, DM07.

Rule for the strip (re-measured from the LIVE zip's van KEYS, not from the audit's numbers): the swept footprint of the van = for every FRAME of the main drive
(keys 0..drive(), the drive-in, the stop, the drive-away or the reverse-out; interpolated every 20 cm), a rectangle centred on the van's origin, heading = the rotation
key (sway included), half width 110 + 40 (capsule) = 150, half length 340 in BOTH directions (so a reverse leg is covered). The new box must be entirely outside that
footprint (checked on a 10 cm grid). The crash legs (keys after drive()) only play when the van is destroyed and are reported, not swept.
Among the valid rectangles inside the OLD box the tool prefers the one that overlaps the bots' AllyEscapeBox most (bots wait there and BotFill walks them to the
centre of otrExitLevel, so a centre in the clear strip also stops the bots standing under the van), then the larger area.

Changes: ONLY that node's .prp ZGEOM[2] (centre) / ZBoxPrimitive[0..2] (half) fields; y is kept. The .gms record is NOT touched (GUESS, as in DD10: the loader reads the .prp's;
if it read the .gms translation instead the box would simply stay as it was). The twin triggers at the same box (POI_TheEscapeArea, ..._OffenseOnlyRespawn = ECPS_CP_OFFENSEONLY,
which never fires in Fragile Alliance, ..._FA_RespawnOnly = ECPS_FA_RESPAWNONLY) only send the escape-area marker (PointOfInterest) and kill nobody: left alone (GUESS: they do
not need to move with the call box; at worst the marker shows while standing in the lane).
Stage per map: <out-root>/exitstrip_1110/<MAP>: plain + bots zip (only .prp differs), bots.base.md5 = md5 of the plain staged zip, install.py (--dry/--undo/--skip-run-check,
live md5 pins, *.before-exitstrip1110 backups), INSTALL.bat/UNDO.bat, README (recommended on).

  python tools/kl_exitstrip_1110.py stage  [MAP ...] [--in-root <Maps dir>] [--out-root C:/kl_build_1024]
  python tools/kl_exitstrip_1110.py check  [MAP ...] [--in-root ...] [--out-root ...] [--no-undo]
  python tools/kl_exitstrip_1110.py lane   [MAP ...] [--in-root ...]     re-measure the swept footprint, free rectangles, ally overlap, KLJoin.ini (reads only)
MAP = DM01B DM06B DM07 (default all). Never installs anything. REFUSES unless the live files are the expected md5s and the box holds the pre-edit values."""
import hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS_DIR = os.path.join(GAME, 'KLExpansion', 'Maps')
OUT_ROOT = 'C:/kl_build_1024'
STAGE = 'exitstrip_1110'
TAG = '.before-exitstrip1110'
TEMPLATES = ['C:/kl_build_1024/dd10doorfix_1109/kit/install.py', 'C:/kl_build_1024/dd10exitsouth_1110/install.py']
R = 'ROOT' + chr(92)
EXIT_BOX = R + 'Gameplay!EscapeSetup!otrExitLevel'
ALLY_BOX = R + 'Gameplay!merc_bot_squad!AllyEscapeBox'
HW = 110.0 + 40.0        # van half width + capsule margin (the brief)
HL = 340.0               # van half length used in BOTH directions (audit sweep: back 340 / front 260)
STEP = 10                # grid cell, cm

# Per-map table. new_at / new_half: the strip (y kept). All edges are multiples of 10 and inside the old box.
#   DM01B: lane z 31907 +-150 = 31757..32057 (x 3668..4568 of the box all on it); north strip z 32070..32350 (the south one z 31460..31740 does not touch the AllyEscapeBox z 32002..32702)
#   DM07 : lane z 10400 +-150 = 10250..10550; south strip z 9950..10230 (AllyEscapeBox z 9615..10315); the north strip 10560..10850 misses it
#   DM06B: diagonal lane NW->SE: the free ground is the south-west corner; best (ally overlap) x -3020..-2400, z -8380..-8170 (AllyEscapeBox x -3082..-2382, z -8684..-7984, its centre -2732/-8334 is inside it)
MAPS = {
    'DM01B': dict(slot='F03', live={'F03_Main.zip': '5eab5eccdda1c9d945bcf767db05271d', 'F03_Main.bots.zip': 'cadfb74e6e62408fbd43540938406b79', 'F03_Main.bots.base.md5': '4db9726f51dd4eaefc9642c03caa8c17'},
                  old_at=[4118.0, 185.0, 31907.0], old_half=[450.0, 300.0, 450.0], new_at=[4118.0, 185.0, 32210.0], new_half=[450.0, 300.0, 140.0]),
    'DM06B': dict(slot='F02', live={'F02_Main.zip': '7cee043dda5d62eeb6c48329b40fcda8', 'F02_Main.bots.zip': 'ec42c5e4ec454196380292286ca7e081', 'F02_Main.bots.base.md5': '171f7443261ec0f3bc9d5a049702994e'},
                  old_at=[-2573.800048828125, 2704.0, -7939.0], old_half=[450.0, 300.0, 450.0], new_at=[-2710.0, 2704.0, -8275.0], new_half=[310.0, 300.0, 105.0]),
    'DM07': dict(slot='F06', live={'F06_Main.zip': 'f35e4133af2e9d3ebec0ec4647e1233f', 'F06_Main.bots.zip': '1f514d51d06b3dcb29e6e210b9a711ac', 'F06_Main.bots.base.md5': '08478b6eb1a226cceca594237e524f52'},
                 old_at=[-2937.0, 602.0, 10400.0], old_half=[450.0, 300.0, 450.0], new_at=[-2937.0, 602.0, 10090.0], new_half=[450.0, 300.0, 140.0]),
}
for _m, _c in MAPS.items():
    _c['zip'], _c['bots'], _c['base'] = ['%s_Main%s' % (_c['slot'], s) for s in ('.zip', '.bots.zip', '.bots.base.md5')]


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _mods():
    global kl_fa, F, A, J, SK, ME, kl_graft, np
    import numpy as np
    import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_prpjoin as J, kl_skyline_1108 as SK, kl_map_escape as ME, kl_graft


def box_values(sc, k):
    lab = J.labels('dd', sc.cls(k))
    vv = kl_fa.node_values(sc, k)
    return [vv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3)], vv[lab.index('ZGEOM[2]')]


def rect_of(at, half):
    return (at[0] - half[0], at[0] + half[0], at[2] - half[2], at[2] + half[2])


# ---------------------------------------------------------------- the van's swept footprint (from the zip's KEYS)

def van_frames(zp):
    """([(x, z, heading_rad)] per frame of the MAIN drive, [crash-leg (x, z)] ) of V_Van_00, world frame."""
    B = F.Built(zp)
    L = ME.Level(zp)
    sc = B.sc
    ends = sorted({o for e in B.ents if e.raw for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(B.scene.head)})
    for k in range(1, len(B.ents) + 1):
        if sc.names[k] != 'V_Van_00' or 'Reflection' in sc.path[k] or 'EscapeVehicle' not in sc.path[k] or not kl_graft.keys_tracks(B.ents[k - 1].raw):
            continue
        K = ME.VanKeys(B.scene.head, B.ents[k - 1].raw, ends, kl_graft.keys_tracks)
        Rm, T = L.frame(sc.parent[k])
        w = lambda q: tuple(T[i] + sum(Rm[i][j] * q[j] for j in range(3)) for i in range(3))
        n = K.drive()
        out, crash = [], []
        for f in range(K.frames):
            ip, ir = K.f2p[f], K.f2r[f]
            q = K.pos[ip]
            if q == (0.0, 0.0, 0.0):
                continue
            x, _y, z = w(q)
            if ip >= n:
                crash.append((x, z))
                continue
            psi = math.radians(K.yaw(K.rot[ir]))
            fx, _fy, fz = [w((math.sin(psi), 0.0, math.cos(psi)))[i] - w((0, 0, 0))[i] for i in range(3)]
            out.append((x, z, math.atan2(fx, fz)))
        return out, crash
    raise SystemExit('REFUSED: no key-framed V_Van_00 under an EscapeVehicle node in %s' % zp)


def dense(fr):
    out = []
    for a, b in zip(fr, fr[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / 20))
        dy = (b[2] - a[2] + math.pi) % (2 * math.pi) - math.pi
        for t in range(n):
            f = t / n
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + dy * f))
    out.append(fr[-1])
    return out


def grid(rect):
    xs = np.arange(rect[0], rect[1] + 1, STEP, dtype=float)
    zs = np.arange(rect[2], rect[3] + 1, STEP, dtype=float)
    return xs, zs


def swept(fr, rect, hw=HW):
    """Boolean mask [len(zs), len(xs)] of the grid cells of `rect` inside the van's footprint at any frame."""
    xs, zs = grid(rect)
    X, Z = np.meshgrid(xs, zs)
    cov = np.zeros(X.shape, bool)
    for x, z, y in dense(fr):
        if x < rect[0] - HL - hw or x > rect[1] + HL + hw or z < rect[2] - HL - hw or z > rect[3] + HL + hw:
            continue
        f = (math.sin(y), math.cos(y))
        dx, dz = X - x, Z - z
        cov |= (np.abs(dx * f[0] + dz * f[1]) <= HL) & (np.abs(dx * f[1] - dz * f[0]) <= hw)
    return xs, zs, cov


def choose(fr, rect, ally, minside=200):
    """Best free axis-aligned rectangles inside `rect`: [(ally overlap area, area, x0, x1, z0, z1)] best first."""
    xs, zs, cov = swept(fr, rect)
    nz, nx = cov.shape
    out = []
    for z0 in range(nz):
        run = np.ones(nx, bool)
        for z1 in range(z0, nz):
            run &= ~cov[z1]
            if not run.any():
                break
            if zs[z1] - zs[z0] < minside:
                continue
            j = 0
            while j < nx:
                if run[j]:
                    k = j
                    while k + 1 < nx and run[k + 1]:
                        k += 1
                    if xs[k] - xs[j] >= minside:
                        ov = max(0.0, min(xs[k], ally[1]) - max(xs[j], ally[0])) * max(0.0, min(zs[z1], ally[3]) - max(zs[z0], ally[2]))
                        out.append((ov, (xs[k] - xs[j]) * (zs[z1] - zs[z0]), xs[j], xs[k], zs[z0], zs[z1]))
                    j = k + 1
                else:
                    j += 1
    out.sort(reverse=True)
    return out


def clear_of_lane(fr, rect, hw=HW):
    """(True, 0) when no grid cell of `rect` (the strip, edges inclusive) is inside the footprint; else (False, cells)."""
    xs, zs, cov = swept(fr, rect, hw)
    return (not cov.any()), int(cov.sum())


# ---------------------------------------------------------------- stage

def edit_scene(B, cfg, log=print):
    sc = B.sc
    k = A.node_of(sc, EXIT_BOX)
    if k not in [c[0] for c in kl_fa.controllers(sc, 'OnlineExitLevelTrigger')]:
        raise SystemExit('REFUSED: %s has no OnlineExitLevelTrigger controller' % EXIT_BOX)
    half, at = box_values(sc, k)
    if [float(x) for x in half] != cfg['old_half'] or [float(x) for x in at] != cfg['old_at']:
        raise SystemExit('REFUSED: the exit box is not the pre-edit one: half %r at %r' % (half, at))
    lab = J.labels('dd', sc.cls(k))

    def fn(us):
        A.setv(sc, us, lab.index('ZGEOM[2]'), list(cfg['new_at']))
        for i in range(3):
            A.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), cfg['new_half'][i])
    kl_graft.edit(sc.nodes[k], 'props', fn)         # .prp only
    log('  exit box node %d: centre %s -> %s, half %s -> %s' % (k, cfg['old_at'], cfg['new_at'], cfg['old_half'], cfg['new_half']))
    return k


def patch_zip(src, dst, cfg, log=print):
    B = F.Built(src)
    edit_scene(B, cfg, log)
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))


def template_text():
    for p in [os.environ.get('KL_EXITSTRIP_TEMPLATE')] + TEMPLATES:
        if p and os.path.isfile(p):
            return open(p, encoding='utf-8').read()
    raise SystemExit('REFUSED: no install.py template found (%s)' % TEMPLATES)


def make_install(m, cfg, stage_md5, text=None):
    t = text if text is not None else template_text()
    rows = ", ".join("('%s', '%s', '%s')" % (n, cfg['live'][n], stage_md5[n]) for n in (cfg['zip'], cfg['bots'], cfg['base']))
    t, k = re.subn(r"^FILES = \[.*?\]\n", lambda mm: "FILES = [" + rows + "]\n", t, flags=re.S | re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES line')
    t, k = re.subn(r"^MAP, TAG = '[A-Za-z0-9]+', '[^']+'", "MAP, TAG = '%s', '%s'" % (m, TAG), t, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r'^r?"""Installs / undoes[^\n]*\n', lambda mm: 'r"""Installs / undoes EXIT STRIP 1110 on the live %s files: the van-call exit box shrinks to a strip off the van lane (tools/kl_exitstrip_1110.py).\n' % m, t, count=1, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no docstring head')
    t = re.sub(r'<name>\.before-[a-z0-9]+', '<name>' + TAG, t)
    return t


README = """EXIT STRIP 1110 - %(m)s (slot %(slot)s) - staged, NOT installed. (recommended on)
Tool: tools/kl_exitstrip_1110.py (+ _test.py).
Live now (pinned): %(zip)s %(lz)s, bots %(lb)s, bots.base.md5 %(lm)s.
Staged:            %(zip)s %(sz)s, bots %(sb)s, bots.base.md5 %(sm)s.

What changes: the exit box Gameplay!EscapeSetup!otrExitLevel (the box that calls the van) goes from x %(ox0)g..%(ox1)g, z %(oz0)g..%(oz1)g to x %(nx0)g..%(nx1)g, z %(nz0)g..%(nz1)g (y unchanged).
Why: the key-framed van drives in (and parks, and leaves) through the old box; a heister waiting in it for the van is run over. The new strip is outside the van's swept
footprint (half width 110 + 40 capsule margin, all frames of the drive, both directions) and %(ally)s.
Nothing else changes (van, twin POI triggers, loot, KLJoin.ini). Only the .prp of the plain and the bots zip differ (bytes inside this one entity).
Install: python install.py (game closed; backups *%(tag)s next to the files).   Undo: UNDO.bat  (python install.py --undo), byte exact.
GUESS: the .gms record of the box keeps its old translation (the loader reads the .prp); the strip floor is walkable (the AllyEscapeBox overlap suggests so). Not benched:
walk into the strip (van called), wait through the drive-in, board; bots should now wait in the strip.
"""


def stage(m, in_root, out_root, log=print):
    cfg = MAPS[m]
    in_dir = os.path.join(in_root, m)
    for n in (cfg['zip'], cfg['bots'], cfg['base']):
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != cfg['live'][n]:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live %s changed: re-stage)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', cfg['live'][n], m))
    if open(os.path.join(in_dir, cfg['base'])).read().strip() != fmd5(os.path.join(in_dir, cfg['zip'])):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')
    out = os.path.join(out_root, STAGE, m)
    os.makedirs(out, exist_ok=True)
    for old in (cfg['zip'], cfg['bots'], cfg['base']):
        if os.path.exists(os.path.join(out, old)):
            os.remove(os.path.join(out, old))
    log('stage %s -> %s' % (m, out))
    for n in (cfg['zip'], cfg['bots']):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), cfg, log)
    with open(os.path.join(out, cfg['base']), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, cfg['zip'])) + '\n')
    sm = {n: fmd5(os.path.join(out, n)) for n in (cfg['zip'], cfg['bots'], cfg['base'])}
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(make_install(m, cfg, sm))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    o, n_ = rect_of(cfg['old_at'], cfg['old_half']), rect_of(cfg['new_at'], cfg['new_half'])
    ally = 'overlaps the bots\' AllyEscapeBox (they still wait in the call box)' if ally_overlap(m, in_dir, n_) else 'does not overlap the bots\' AllyEscapeBox'
    open(os.path.join(out, 'README.txt'), 'w', newline='\n').write(README % dict(
        m=m, slot=cfg['slot'], zip=cfg['zip'], tag=TAG, ally=ally,
        lz=cfg['live'][cfg['zip']][:8], lb=cfg['live'][cfg['bots']][:8], lm=cfg['live'][cfg['base']][:8],
        sz=sm[cfg['zip']][:8], sb=sm[cfg['bots']][:8], sm=sm[cfg['base']][:8],
        ox0=o[0], ox1=o[1], oz0=o[2], oz1=o[3], nx0=n_[0], nx1=n_[1], nz0=n_[2], nz1=n_[3]))
    json.dump(dict(map=m, md5=sm, live=cfg['live'], tag=TAG, old=o, new=n_), open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def ally_rect(in_dir, cfg):
    sc = F.Built(os.path.join(in_dir, cfg['zip'])).sc
    k = A.node_of(sc, ALLY_BOX)
    half, at = box_values(sc, k)
    return rect_of([float(v) for v in at], [float(v) for v in half])


def ally_overlap(m, in_dir, r):
    a = ally_rect(in_dir, MAPS[m])
    return max(0.0, min(r[1], a[1]) - max(r[0], a[0])) * max(0.0, min(r[3], a[3]) - max(r[2], a[2]))


def check(m, in_root, out_root, log=print, undo_rehearsal=True):
    cfg = MAPS[m]
    in_dir = os.path.join(in_root, m)
    out = os.path.join(out_root, STAGE, m)
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    log('CHECK %s' % m)
    o, n_ = rect_of(cfg['old_at'], cfg['old_half']), rect_of(cfg['new_at'], cfg['new_half'])
    need(o[0] <= n_[0] and n_[1] <= o[1] and o[2] <= n_[2] and n_[3] <= o[3], 'new box x %g..%g z %g..%g lies inside the old one' % (n_[0], n_[1], n_[2], n_[3]))
    need(cfg['new_at'][1] == cfg['old_at'][1] and cfg['new_half'][1] == cfg['old_half'][1], 'y unchanged')
    fr, crash = van_frames(os.path.join(in_dir, cfg['zip']))
    ok, cells = clear_of_lane(fr, n_)
    need(ok, 'new box wholly outside the van footprint (half width %g, half length %g, %d frames, 10 cm grid; %d cells inside)' % (HW, HL, len(fr), cells))
    ok2, cells2 = clear_of_lane(fr, o)
    need(not ok2, 'the OLD box does overlap the lane (%d cells)' % cells2)
    for n in (cfg['zip'], cfg['bots']):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = sorted(mm.rsplit('_Main', 1)[1] for mm in zb.namelist() if zb.read(mm) != zs.read(mm))
            need(changed == ['.prp'], '%s: only .prp differs (changed: %s)' % (n, changed))
            pa, pb = zb.read([mm for mm in zb.namelist() if mm.endswith('.prp')][0]), zs.read([mm for mm in zs.namelist() if mm.endswith('.prp')][0])
            need(len(pa) == len(pb), '%s: .prp same length (%d)' % (n, len(pa)))
            diff = [i for i in range(min(len(pa), len(pb))) if pa[i] != pb[i]]
            need(0 < len(diff) <= 24 and diff[-1] - diff[0] < 300, '%s: .prp %d bytes differ, span %s (one entity)' % (n, len(diff), (diff[0], diff[-1]) if diff else None))
        Bb, Bs = F.Built(base), F.Built(stg)
        need(F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip' % n)
        k = A.node_of(Bs.sc, EXIT_BOX)
        h, at = box_values(Bs.sc, k)
        need([float(x) for x in h] == cfg['new_half'] and [float(x) for x in at] == cfg['new_at'], '%s: exit box half %s at %s' % (n, h, at))
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or len(Bb.sc.nodes[j]['ctrls']) != len(Bs.sc.nodes[j]['ctrls'])
                 or any(x != y for x, y in zip(Bb.sc.nodes[j]['ctrls'], Bs.sc.nodes[j]['ctrls']))]
        need(diffn == [k], '%s: exactly node %d differs' % (n, k))
    need(open(os.path.join(out, cfg['base'])).read().strip() == fmd5(os.path.join(out, cfg['zip'])), 'bots.base.md5 = md5 of the plain staged zip')
    with zipfile.ZipFile(os.path.join(in_dir, cfg['zip'])) as a, zipfile.ZipFile(os.path.join(in_dir, cfg['bots'])) as b, zipfile.ZipFile(os.path.join(out, cfg['zip'])) as c, zipfile.ZipFile(os.path.join(out, cfg['bots'])) as d:
        ld = [mm for mm in a.namelist() if a.read(mm) != b.read(mm)]
        sd = [mm for mm in c.namelist() if c.read(mm) != d.read(mm)]
        need(ld == sd, 'plain and bots zips differ only in %s (live %s)' % (sd, ld))
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in (cfg['zip'], cfg['bots'], cfg['base']):
        need(("'%s', '%s', '%s')" % (n, cfg['live'][n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, cfg['live'][n][:8], fmd5(os.path.join(out, n))[:8]))
    if undo_rehearsal:
        sg = tempfile.mkdtemp(prefix='exitstripgame_', dir=out)
        try:
            d = os.path.join(sg, 'KLExpansion', 'Maps', m)
            os.makedirs(d)
            names = [x for x in os.listdir(in_dir) if x in cfg['live'] or x == 'KLJoin.ini']
            for n in names:
                shutil.copyfile(os.path.join(in_dir, n), os.path.join(d, n))
            before = {n: fmd5(os.path.join(d, n)) for n in names}
            run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', sg, '--skip-run-check'] + list(a), capture_output=True, text=True)
            r = run('--dry')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in names} == before, 'install.py --dry rc %d, writes nothing' % r.returncode)
            r = run()
            need(r.returncode == 0 and all(fmd5(os.path.join(d, n)) == (fmd5(os.path.join(out, n)) if n in cfg['live'] else before[n]) for n in names) and all(os.path.isfile(os.path.join(d, n + TAG)) for n in cfg['live']), 'scratch install lands the staged md5s, backups *%s made, other files untouched' % TAG)
            r2 = run()
            need(r2.returncode != 0, 'a second install is refused')
            r = run('--undo')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in names} == before and not any(os.path.exists(os.path.join(d, n + TAG)) for n in cfg['live']), 'scratch undo restores every file byte for byte')
        finally:
            shutil.rmtree(sg, ignore_errors=True)
    log('CHECK %s %s (%d failures)' % (m, 'PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def join_lines(in_dir):
    p = os.path.join(in_dir, 'KLJoin.ini')
    if not os.path.isfile(p):
        return None
    out, sec = [], ''
    for ln in open(p, encoding='utf-8', errors='replace'):
        s = ln.strip()
        if s.startswith('['):
            sec = s
        elif sec.lower().startswith('[join') and re.match(r'(Land|Target|Tolerance|Slack)\s*=', s, re.I):
            out.append('%s %s' % (sec, s))
    return out


def report(m, in_root, log=print):
    cfg = MAPS[m]
    in_dir = os.path.join(in_root, m)
    zp = os.path.join(in_dir, cfg['zip'])
    fr, crash = van_frames(zp)
    o, n_ = rect_of(cfg['old_at'], cfg['old_half']), rect_of(cfg['new_at'], cfg['new_half'])
    xs = [f[0] for f in fr]
    zs = [f[1] for f in fr]
    log('== %s  van frames %d, x %.0f..%.0f z %.0f..%.0f, crash-leg keys %d (x %.0f..%.0f z %.0f..%.0f)' % (
        m, len(fr), min(xs), max(xs), min(zs), max(zs), len(crash), min([c[0] for c in crash] or [0]), max([c[0] for c in crash] or [0]), min([c[1] for c in crash] or [0]), max([c[1] for c in crash] or [0])))
    ins = [f for f in dense(fr) if o[0] - 1 <= f[0] <= o[1] + 1 and o[2] - 1 <= f[1] <= o[3] + 1]
    if ins:
        log('  inside the old box: z %.0f..%.0f (centre line), x %.0f..%.0f' % (min(f[1] for f in ins), max(f[1] for f in ins), min(f[0] for f in ins), max(f[0] for f in ins)))
    sp = [(i, math.hypot(fr[i + 1][0] - fr[i][0], fr[i + 1][1] - fr[i][1])) for i in range(len(fr) - 1)]
    still = [i for i, d in sp if d < 3 and o[0] <= fr[i][0] <= o[1] and o[2] <= fr[i][1] <= o[3]]
    if still:
        log('  parked inside the old box: frames %d..%d at x %.0f z %.0f' % (still[0], still[-1], fr[still[0]][0], fr[still[0]][1]))
    ar = ally_rect(in_dir, cfg)
    log('  AllyEscapeBox x %g..%g z %g..%g; overlaps old box %.0f m2, new strip %.0f m2' % (ar[0], ar[1], ar[2], ar[3], ally_overlap(m, in_dir, o) / 1e4, ally_overlap(m, in_dir, n_) / 1e4))
    xs_, zs_, cov = swept(fr, ar)
    log('  AllyEscapeBox itself overlaps the lane: %s (%.0f of %.0f m2 inside the footprint)' % (bool(cov.any()), cov.sum() * STEP * STEP / 1e4, cov.size * STEP * STEP / 1e4))
    ok, cells = clear_of_lane(fr, n_)
    log('  new strip x %g..%g z %g..%g: clear of the lane %s' % (n_[0], n_[1], n_[2], n_[3], ok))
    best = choose(fr, o, ar)[:3]
    for b in best:
        log('  best free rectangle: ally overlap %.0f m2, area %.0f m2, x %g..%g z %g..%g' % (b[0] / 1e4, b[1] / 1e4, b[2], b[3], b[4], b[5]))
    jl = join_lines(in_dir)
    log('  KLJoin.ini: %s' % ('absent' if jl is None else (jl or 'present, no [Join*] Land/Target (only [FedBody])')))
    sc = F.Built(zp).sc
    for k in range(1, len(sc.nodes)):
        p = sc.path[k]
        if 'FASpecials!POI!Trigger_POI_TheEscapeArea' in p or 'TriggerBox_RearDoors' in p:
            hh, at = box_values(sc, k)
            log('  twin %-62s at %s half %s%s' % (p[-62:], [round(float(v)) for v in at], [round(float(v)) for v in hh], '  (same box as otrExitLevel)' if [float(v) for v in at] == cfg['old_at'] and [float(v) for v in hh] == cfg['old_half'] else ''))


def main(a):
    if not a or a[0] not in ('stage', 'check', 'lane'):
        print(__doc__)
        return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    skip = {opt('--in-root'), opt('--out-root')}
    maps = [x for x in a[1:] if x in MAPS] or list(MAPS)
    unknown = [x for x in a[1:] if not x.startswith('-') and x not in MAPS and x not in skip]
    if unknown:
        print('unknown map(s): %s' % unknown)
        return 2
    _mods()
    in_root, out_root = opt('--in-root', MAPS_DIR), opt('--out-root', OUT_ROOT)
    bad = 0
    for m in maps:
        if a[0] == 'lane':
            report(m, in_root)
            continue
        if a[0] == 'stage':
            stage(m, in_root, out_root)
        bad += 0 if check(m, in_root, out_root, undo_rehearsal='--no-undo' not in a) else 1
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
