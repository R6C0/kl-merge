#!/usr/bin/env python3
"""kl_club_helicam_1106.py - Last Call (DM05A) pass helicam1106: the escape camera rides WITH the heli and looks back at the tower. OFFLINE, level data only.

  python tools/kl_club_helicam_1106.py stage [--in-dir <dir>] [--out <dir>] [--variant A|B|D|F] [--f5 N] [--f6 N] [--aim <path>] [--pin-live] [--tag .before-x]
  python tools/kl_club_helicam_1106.py check <zip> [--variant A|B|D|F]
(no --force: the input md5 must be a pinned one or --allow-md5 <8+ hex digits>; chain with --in-dir on another stage, e.g. C:\\kl_build_1024\\lcoutro_1106)

Plan and reasoning: re/lastcall_helicam_plan_1106.md. Problem: EscCamera01 is eFMM_LookFromPos, a FIXED eye at CamPos01 (7093, 2181, 2727); once the
heli leaves, the view toward it is unlit (all-black frame), also with the heli parked 17.8 m away (bench lcoutro1106), so distance is not the cause.
Stock Dog Days F06 rides in the vehicle instead (CameraInVan_01: eFMM_LookAtPos, floats 0 -270 -270 80 0 -170, a focus sibling of the heli).

FIX (node 11576 edited in place; NO entity added, so no SLOT renumbering: .oct/.rmi/.rmc/.HVK untouched; only the .prp changes, the key table
grows by the new key strings):
  CCameraBox mode (field 11) eFMM_LookAtPos, field 9 -> the aim node, f5/f6 = the eye offset. Message-only flag (field 12) stays 1, so the
  CameraTrigger01 -> EscCamera01 chain is unchanged.
  Variant A (default, "tower behind"): aim ROOT\\EscCameraSetup!EscCameraLAST (7800, 2271, 3500, the lit tower side), f5 -900, f6 +200;
    f1..f4 keep their stored values.
  Variant B (stock-faithful): floats 0 -270 -270 80 0 -170, aim ROOT\\EscapeSetup!EscapeChopper\\Escape_Chopper\\ShatterGeom (a heli sibling).
GUESS (nothing here is proven offline; the bench checks it, see the plan):
  1. sign and axis of f5/f6: eye = player place + (f5, f6) in world x,y (taken from the plan's reading of the F06 camera, not re-verified).
  2. the 'player place' of LookAtPos is the heli pivot (piv398) during the outro.
  3. the tower view is lit enough not to be black.
  4. variant B: the meaning of f1..f4 (stock values copied unchanged); eye may sit inside the hull.
  5. variant A: f1..f4 stay at the LookFromPos-era stored values (0, 99999, 99999, 40); GUESS that LookAtPos ignores or tolerates them
     (stock F06 uses 0 -270 -270 80). If the bench frame is wrong/black, try variant B's floats with --f5/--f6 first.
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
OUT = r'C:\kl_build_1024\lchelicam_1106'
CAMBOX = 'EscCameraSetup!EscCamera01'
LOOK_AT = 'eFMM_LookAtPos'
LOOK_FROM = 'eFMM_LookFromPos'
AIM_A = 'ROOT\\EscCameraSetup!EscCameraLAST'
AIM_B = 'ROOT\\EscapeSetup!EscapeChopper\\Escape_Chopper\\ShatterGeom'
F5_A, F6_A = -900.0, 200.0                            # GUESS (sign/axis); plan range f5 -750..-1000, f6 +150..+300
STOCK_B = (0.0, -270.0, -270.0, 80.0, 0.0, -170.0)    # F06 CameraInVan_01 f1..f6; GUESS on the meaning of f1..f4
# Variant F (candidate 2c, re/lastcall diagnosis 11-06 "room culling"): a FIXED eye again (stock mode), the eye node CamPos01 (7093, 2181, 2727) lies inside the
# Roof room's .rmi box 7 so the frame starts from the Roof room; the stock LookFromPos floats of F04/F05/F07/F09 (0, 99999, 99999, 40, 0, 50). It needs the
# climb route of kl_club_outro_1106.ROUTE_2C so the heli stays over open air, in view. f4 = 40 is probably a field of view (GUESS).
AIM_F = 'ROOT\\EscCameraSetup!CamPos01'
FLOATS_F = (0.0, 99999.0, 99999.0, 40.0, 0.0, 50.0)
# Variant D (candidate 2d, 11-06): the stock outside-camera of F02/F03/F06/F08 (kl2.exe 0x4471a1, mode eFMM_LookFromPosFA): eye = the camera box's OWN node,
# aim = field 9 re-read every frame, so the eye stays fixed in Roof .rmi box 7 while the view follows the heli group. Node 11576 (parent 0 = a world place) moves
# from (7800, 2271, 3500) to the 2c eye; prp ZGEOM[2] and the .gms trans change together (like kl_club_heli_1105 does for CamPos01); no entity is added.
LOOK_FROM_FA = 'eFMM_LookFromPosFA'
AIM_D = 'ROOT\\EscapeSetup!EscapeChopper\\Escape_Chopper'    # the heli group (ZGROUP with OnlineEscHavokCar), the analogue of stock F08 node 767
FLOATS_D = (0.0, -270.0, -270.0, 80.0, 0.0, 0.0)               # the stock F02/F03/F08 outside cameras; GUESS: mode 4 ignores f1..f6 (kl2 0x447190 reads positions only)
EYE_D = (7093.0, 2181.0, 2727.0)                               # = the 2c eye CamPos01, inside Roof .rmi box 7 (an eye outside every box gives a grey frame)
MODES = {'A': LOOK_AT, 'B': LOOK_AT, 'F': LOOK_FROM, 'D': LOOK_FROM_FA}
EYES = {'D': EYE_D}                                            # variants that also move the camera box node to this world place
# live DM05A of 2026-11-06 (e6d2f73e), doors-1106 (a24d7432), outro-1106 (77a42f74), spawn2f-1106 (88e23dd5)
KNOWN_IN = ('e6d2f73e', 'a24d7432', '77a42f74', '88e23dd5')
TAG = '.before-helicam1106'
# --pin-live: the install.py "before" pins are the LIVE files (e6d2f73e), not the --in-dir stage (e.g. lcoutro_1106), so one install = in-dir changes + camera
LIVE_PINS = {'F01_Main.zip': 'e6d2f73ef0c51bfdbaec56c9534a4c9a', 'F01_Main.bots.zip': '54cb9e269b7b38a24525ab5e671c400a',
             'F01_Main.bots.base.md5': 'aa0e1580a147ed73134a71e03e6d597a'}
NAMES = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def wanted(variant, f5=None, f6=None, aim=None):
    """-> (f1..f6, aim path). Variant A only sets f5/f6 (f1..f4 entries are None = keep); B sets all six."""
    if variant == 'A':
        fl, aim = [None] * 4 + [F5_A, F6_A], aim or AIM_A
    elif variant == 'B':
        fl, aim = list(STOCK_B), aim or AIM_B
    elif variant == 'F':
        fl, aim = list(FLOATS_F), aim or AIM_F
    elif variant == 'D':
        fl, aim = list(FLOATS_D), aim or AIM_D
    else:
        raise ValueError('variant must be A, B, D or F')
    if f5 is not None:
        fl[4] = float(f5)
    if f6 is not None:
        fl[5] = float(f6)
    return fl, aim


def state(zp):
    import kl_fa
    import kl_fa_bots as F
    import kl_fa_author as A
    B = F.Built(zp)
    sc = B.sc
    k = A.node_of(sc, CAMBOX)
    ci = [i for i, (n, b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(n) == 'CCameraBox'][0]
    v = [kl_fa.value(sc, u) for u in kl_fa.units(sc.nodes[k]['ctrls'][ci][1][1:-1])]
    return B, k, ci, v


def done_state(v, fl, aim, mode=LOOK_AT):
    return (v[11] == mode and v[9] == aim and v[12] == 1
            and all(fl[i] is None or abs(float(v[1 + i]) - fl[i]) < 1e-3 for i in range(6)))


def eye_of(B, k):
    """-> (prp ZGEOM[2] of the camera box node, .gms trans xyz) as float tuples."""
    import kl_fa
    import kl_prpjoin as J
    lab = J.labels('dd', B.sc.cls(k))
    z = tuple(float(x) for x in kl_fa.node_values(B.sc, k)[lab.index('ZGEOM[2]')])
    return z, struct.unpack('<3f', B.ents[k - 1].trans[:12])


def eye_done(B, k, variant):
    """True when the variant moves no eye, or the box node (prp and .gms) sits at EYES[variant]."""
    if variant not in EYES:
        return True
    z, t = eye_of(B, k)
    return all(abs(z[i] - EYES[variant][i]) < 0.5 and abs(t[i] - EYES[variant][i]) < 0.5 for i in range(3))


def check(zp, variant='A', log=print):
    B, k, ci, v = state(zp)
    log('%s (node %d): mode %s, field 9 %s, f1..f6 %s, message-only %s' % (CAMBOX, k, v[11], v[9], v[1:7], v[12]))
    fl, aim = wanted(variant)
    ok = done_state(v, fl, aim, MODES[variant]) and eye_done(B, k, variant)
    if variant in EYES:
        log('box node place: prp %s, gms %s (want %s)' % (eye_of(B, k) + (EYES[variant],)))
    log('RESULT: %s' % ('DONE' if ok else 'NOT DONE'))
    return 0


def build(src, dst, variant='A', f5=None, f6=None, aim=None, log=print):
    """plain zip -> plain zip, only the .prp changes. Idempotent. -> the camera's field values before."""
    import kl_fa
    import kl_graft
    from kl_prp import Prp
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('the output is the input')
    B, k, ci, v = state(src)
    sc = B.sc
    fl, aim = wanted(variant, f5, f6, aim)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    mode = MODES[variant]
    vals_done, eye_ok = done_state(v, fl, aim, mode), eye_done(B, k, variant)
    if vals_done and eye_ok:
        shutil.copyfile(src, dst)
        log('already done: copied unchanged')
        return v
    if v[12] != 1:
        raise ValueError('%s is not message-only (field 12 = %r): refusing, the trigger chain would change' % (CAMBOX, v[12]))
    if len(sc.resolve(aim)) != 1:
        raise ValueError('aim node %s is not one node' % aim)

    def fn(us):
        if us[11][0][0] != 0x0e or us[9][0][0] != 0x0c:
            raise ValueError('CCameraBox field 9/11 are not a string/enum')
        for i in range(1, 7):
            if fl[i - 1] is None:
                continue
            if us[i][0][0] != 0x0a:
                raise ValueError('CCameraBox field %d is not a float' % i)
            us[i] = [(0x0a, struct.pack('<f', fl[i - 1]))]
        us[9] = [(0x0c, struct.pack('<I', sc.p.key_index(aim)))]
        us[11] = [(0x0e, struct.pack('<I', sc.p.key_index(mode)))]
    if not vals_done:
        kl_fa.edit(sc, k, ci, fn)
    if not eye_ok:
        if sc.parent[k] > 0:
            raise ValueError('%s has a parent node: a world position is not its place (refusing)' % CAMBOX)
        import kl_gms
        import kl_prpjoin as J
        import kl_fa_author as A
        lab = J.labels('dd', sc.cls(k))
        kl_fa.edit(sc, k, None, lambda us: A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in EYES[variant]]))
        e = B.ents[k - 1]
        e.trans = struct.pack('<3f', *EYES[variant]) + e.trans[12:]
        log('%s: place %s -> %s' % (CAMBOX, eye_of(B, k)[0], EYES[variant]))
    prp = sc.p.serialize()
    if Prp(prp).serialize() != prp:
        raise ValueError('the new .prp does not round-trip')
    new_files = dict(B.files)
    new_files[B.ext['.prp']] = prp
    if not eye_ok:
        gms, buf = B.scene.write()
        new_files[B.ext['.gms']], new_files[B.ext['.buf']] = kl_gms.pack(gms), buf
    kl_graft.write_zip(dst, [(nm, new_files[nm]) for nm in B.order])
    B2, k2, _c2, v2 = state(dst)
    import zipfile
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list differs')
        diff = [x.filename for x in a.infolist() if a.read(x.filename) != b.read(x.filename)]
    okd = (len(diff) == 1 and diff[0].lower().endswith('.prp')) or (not eye_ok and len(diff) <= 3 and all(
        d.lower().rsplit('.', 1)[-1] in ('prp', 'gms', 'buf') for d in diff) and any(d.lower().endswith('.prp') for d in diff))
    if not done_state(v2, fl, aim, mode) or not eye_done(B2, k2, variant) or not okd:
        raise ValueError('read-back failed: %r, members that differ %s' % (v2, diff))
    log('%s: mode %s -> %s, field 9 %s -> %s, f5/f6 %s,%s -> %s,%s; differs: %s' % (
        CAMBOX, v[11], v2[11], v[9], v2[9], v[5], v[6], v2[5], v2[6], ', '.join(diff)))
    return v


INSTALL = r'''r"""Installs / undoes the Last Call HELICAM pass (2026-11-06) on the live DM05A files: the escape camera EscCamera01 rides with the heli
(eFMM_LookAtPos, tools/kl_club_helicam_1106.py). Only the .prp inside the zips changes.

  python install.py            install (originals -> <name>.before-helicam1106 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals); --skip-run-check skips the kl2.exe check (zombie process)
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', %(tag)r
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
            print('REFUSED: the live zip is %%s, not %%s: another pass changed it, re-stage the helicam on the new live zip' %% (cur, LIVE_ZIP_MD5)); return 1
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


def write_install(st, files, tag=TAG):
    pin = files['F01_Main.zip'][0]
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = INSTALL % dict(files=fl, pin=pin, tag=tag)
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL last call helicam 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call helicam 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


def stage(out=OUT, in_dir=MAPDIR, variant='A', f5=None, f6=None, aim=None, log=print, pin_live=False, tag=TAG, allow=()):
    import kl_botsonline
    src = os.path.join(in_dir, 'F01_Main.zip')
    h = md5(src)
    if not any(h.startswith(k) for k in tuple(KNOWN_IN) + tuple(a.lower() for a in allow if len(a) >= 8)):
        raise ValueError('refusing: %s md5 %s is not one of %s' % (src, h, KNOWN_IN))
    os.makedirs(out, exist_ok=True)
    cp = os.path.join(out, '_in.zip')
    shutil.copyfile(src, cp)                       # the input is only ever READ, through this copy
    if md5(cp) != h:
        raise ValueError('the input changed while it was copied')
    final = os.path.join(out, 'F01_Main.zip')
    old = build(cp, final, variant, f5, f6, aim, log)
    os.remove(cp)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    files = {nm: (LIVE_PINS[nm] if pin_live else md5(os.path.join(in_dir, nm)), md5(os.path.join(out, nm))) for nm in NAMES}
    write_install(out, files, tag)
    rep = {'in_dir': in_dir, 'in_md5': h, 'variant': variant, 'before': [str(x) for x in old[1:13]], 'files': files}
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    log('staged %s plain md5 %s' % (out, plain))
    return rep


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if len(a) >= 2 and a[0] == 'check':
        return check(a[1], opt('--variant', 'A'))
    if a and a[0] == 'stage':
        f = lambda k: float(opt(k, None)) if k in a else None
        stage(opt('--out', OUT), opt('--in-dir', MAPDIR), opt('--variant', 'A'), f('--f5'), f('--f6'), opt('--aim', None),
              pin_live='--pin-live' in a, tag=opt('--tag', TAG), allow=[opt('--allow-md5', '')])
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
