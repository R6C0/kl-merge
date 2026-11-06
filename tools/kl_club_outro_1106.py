#!/usr/bin/env python3
"""kl_club_outro_1106.py - Last Call (DM05A) pass outro1106: the heli must not fly out of the escape camera's sight. OFFLINE, level data only.

  python tools/kl_club_outro_1106.py stage [--in-dir <dir>] [--out <dir>] [--keep N] [--force]
  python tools/kl_club_outro_1106.py check <zip>

Owner: "grey screen" / "no escape screen" on Last Call. Bench lclive1106 run2 (shots 19-21, 11:30:09-11:30:49): after the heli leaves the
picture is fully BLACK for about 60 s, until the round-over panel (session 0x1f at 11:31:00).

CAUSE (P = proven in log / level data, G = guess)
 P EscCamera01 is eFMM_LookFromPos (kl2 0x447240): the eye is FIXED at CamPos01 (7093, 2181, 2727); the view direction goes to the player
   pivot, and the player rides with the heli (piv398).
 P The Escaping spline (EscapeSetup!EscapeChopper\\Escaping\\Spline, 17 points) flies the heli from the pad (7058, 2271, 3467) to
   (-11691, 5616, -1819), 196 m (units are cm) and 11 degrees up; the heli is 76 m out after 3 s, parked at the end for 5 s, and stays
   there until the round ends. The state machine is timer driven (state 5 = 20 s, then the 40 s 'last vehicle' visit 2), it does not wait
   for the spline end.
 P The fixed eye does not move, so ~45 s of the outro look at one empty direction. G (not provable offline): black because nothing is lit
   there (night sky, no skydome pixels, the chopper model unlit). The waiting heli at 7.5 m is dark but visible (shots 17/18).
FIX (the smallest data change; no entity added or moved, so .oct / .rmi / .rmc / .sgd / .HVK slot ids and placements stay)
 The Escaping spline keeps its first KEEP points (default 6: pad ... (4839, 2760, 4761), 31 m from the eye, 8 m up): the point count at
 raw[4:8] is lowered, the bytes after the points are editor memory and the field keeps its size. The heli still lifts off and slides away
 (it is carried the same way), but it parks about 31 m from the eye, in the same framing as the waiting shots, for the rest of the
 outro instead of 196 m away in black. Vehicle state timers, boarding, the visit-2 call for AI heisters are untouched.
 G: the engine reads only the count (header = tag, count, 1; the same layout kl_map_escape.spline reads); the first live run checks it:
 'heli: ... tick' positions must stop near (4839, 2760, 4761) and the shots 19-21 must show the heli.
Stock Dog Days maps are never touched (this edits one node of the DM05A zip, md5-pinned). Re-runnable on any input: --in-dir holds the
F01_Main.zip + F01_Main.bots.zip + F01_Main.bots.base.md5 to start from (default: the live DM05A folder; or another staging folder
such as C:\\kl_build_1024\\lcdoors_1106 to chain). The bots zip is rebuilt from the final plain zip (kl_botsonline), as the doors pass does.
"""
import hashlib
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT = r'C:\kl_build_1024\lcoutro_1106'
SPLINE = 'EscapeSetup!EscapeChopper\\Escaping\\Spline'
KEEP = 6
KNOWN_IN = ('e6d2f73e', 'a24d7432')        # live DM05A of 2026-11-06 11:30; the doors-1106 stage
TAG = '.before-outro1106'
HDR = 12                                   # raw: tag, point count, 1, then 24 bytes a point
POINT = 24


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def cut_raw(raw, keep):
    """The spline's raw field with the point count lowered to `keep`; same length, same bytes elsewhere. -> (new raw, old count)."""
    n = struct.unpack_from('<I', raw, 4)[0]
    if HDR + POINT * n > len(raw):
        raise ValueError('%d points do not fit %d bytes' % (n, len(raw)))
    if keep < 2:
        raise ValueError('a route needs at least 2 points')
    if keep >= n:
        return raw, n
    return raw[:4] + struct.pack('<I', keep) + raw[8:], n


def count_of(zp):
    import kl_fa
    import kl_fa_bots as F
    import kl_fa_author as A
    import kl_prpjoin as J
    B = F.Built(zp)
    sc = B.sc
    k = A.node_of(sc, SPLINE)
    lab = J.labels('dd', sc.cls(k))
    raw = kl_fa.node_values(sc, k)[lab.index('ZEditorSpline[0]')]
    return B, k, lab, raw, struct.unpack_from('<I', raw, 4)[0]


def check(zp, keep=KEEP, log=print):
    n = count_of(zp)[4]
    log('Escaping spline points: %d' % n)
    ok = n <= keep
    log('RESULT: %s' % ('DONE' if ok else 'NOT DONE'))
    return 0


def build(src, dst, keep=KEEP, log=print):
    """plain zip -> plain zip, only the .prp changes. Idempotent (a zip with <= keep points is copied unchanged)."""
    import kl_fa
    import kl_gms
    import kl_graft
    from kl_prp import Prp
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('the output is the input')
    B, k, lab, raw, n = count_of(src)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if n <= keep:
        shutil.copyfile(src, dst)
        log('already done (%d points): copied unchanged' % n)
        return n
    sc = B.sc
    new, _ = cut_raw(raw, keep)

    def fn(us):
        u = us[lab.index('ZEditorSpline[0]')]
        if u[1][0] != 0x0d or u[1][1][4:] != raw:
            raise ValueError('%s: the raw field is not where it was read' % SPLINE)
        u[1] = (0x0d, u[1][1][:4] + new)
    kl_fa.edit(sc, k, None, fn)
    prp = sc.p.serialize()
    if Prp(prp).serialize() != prp:
        raise ValueError('the new .prp does not round-trip')
    new_files = dict(B.files)
    new_files[B.ext['.prp']] = prp
    kl_graft.write_zip(dst, [(nm, new_files[nm]) for nm in B.order])
    n2 = count_of(dst)[4]
    import zipfile
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list differs')
        diff = [x.filename for x in a.infolist() if a.read(x.filename) != b.read(x.filename)]
    if n2 != keep or len(diff) != 1 or not diff[0].lower().endswith('.prp'):
        raise ValueError('read-back failed: %d points, members that differ %s' % (n2, diff))
    log('spline points %d -> %d; only %s differs' % (n, n2, diff[0]))
    return n


INSTALL = r'''r"""Installs / undoes the Last Call OUTRO pass (2026-11-06) on the live DM05A files: the escape heli's route is cut to its first %(keep)d points
so the fixed escape camera keeps it in view (tools/kl_club_outro_1106.py). Only the .prp inside the zips changes.

  python install.py            install (originals -> <name>.before-outro1106 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals); --skip-run-check for those only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', '.before-outro1106'
LIVE_ZIP_MD5 = %(pin)r      # the precheck: the live plain zip must still be exactly this
FILES = [   # name, live md5 before, staged md5 after
%(files)s]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %%s is not there' %% live); return 1
        cur = md5(live)
        print('%%-26s live %%s' %% (n, cur))
        if n == 'F01_Main.zip' and not undo and cur != LIVE_ZIP_MD5:
            print('REFUSED: the live zip is %%s, not %%s: another pass changed it, re-stage the outro on the new live zip' %% (cur, LIVE_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %%s' %% bak); return 1
            if cur != new:
                print('REFUSED: %%s live md5 %%s is not the installed %%s' %% (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %%s is not md5 %%s' %% (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %%s live md5 %%s is not the pinned %%s (already installed, or another pass changed it: re-stage)' %% (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %%s missing or not md5 %%s' %% (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %%s %%s' %% ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%%s: %%s %%s' %% (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%%s); %%s' %% (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(st, files, keep):
    pin = files['F01_Main.zip'][0]
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = INSTALL % dict(files=fl, keep=keep, pin=pin)
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL last call outro 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call outro 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


def stage(out=OUT, in_dir=MAPDIR, keep=KEEP, force=False, log=print, allow=()):
    import kl_botsonline
    names = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')
    src = os.path.join(in_dir, 'F01_Main.zip')
    h = md5(src)
    if not force and not any(h.startswith(k) for k in tuple(KNOWN_IN) + tuple(a.lower() for a in allow if len(a) >= 8)):
        raise ValueError('refusing: %s md5 %s is not one of %s (use --force after reading what changed)' % (src, h, KNOWN_IN))
    os.makedirs(out, exist_ok=True)
    cp = os.path.join(out, '_in.zip')
    shutil.copyfile(src, cp)                       # the input is only ever READ, through this copy
    if md5(cp) != h:
        raise ValueError('the input changed while it was copied')
    final = os.path.join(out, 'F01_Main.zip')
    n = build(cp, final, keep, log)
    os.remove(cp)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = {nm: (md5(os.path.join(in_dir, nm)), md5(os.path.join(out, nm))) for nm in names}
    write_install(out, files, keep)
    rep = {'in_dir': in_dir, 'in_md5': h, 'points_before': n, 'keep': keep, 'files': files}
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    log('staged %s plain md5 %s' % (out, plain))
    return rep


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if len(a) == 2 and a[0] == 'check':
        return check(a[1])
    if a and a[0] == 'stage':
        stage(opt('--out', OUT), opt('--in-dir', MAPDIR), int(opt('--keep', KEEP)), '--force' in a, allow=[opt('--allow-md5', '')])
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
