#!/usr/bin/env python3
r"""kl_lastcall_chain_1106.py - Last Call (DM05A) 1106 passes re-based on WHATEVER the live files are now. OFFLINE only: reads the live folder, writes stages.

Why: the four c9 passes (doors, spawn2f, outro, helicam) each pin the live zip e6d2f73e. When another session (pd2guns layer, ...) changes the
live DM05A files, every pass is stale. This tool reads the CURRENT md5 of the five live files, stages each pass on them (singly, for separate
benches) or all four as one chain (live -> doors -> spawn2f -> outro -> helicam) with ONE install.py pinning the md5s it read.

  python tools/kl_lastcall_chain_1106.py status [--in-dir <dir>]
  python tools/kl_lastcall_chain_1106.py single doors|spawn2f|outro|helicam [--cam 2a|2b|2c|2d|2e|2f] [--in-dir <dir>] [--root <dir> | --out <dir>]
        -> <root>\<name>_live_<first 8 of the zip md5>   (default root C:\kl_build_1024; name lcdoors / lcspawn2f / lcoutro / lcoutcam2a / lcoutcam2b)
  python tools/kl_lastcall_chain_1106.py chain [--cam 2a|2b|2c|2d|2e|2f|none] [--expect-base <zip md5 prefix[,prefix]>] [--only doors,outro,...] [--doors B01,A02] [--in-dir <dir>] [--pin-dir <dir>] [--tag .before-x] [--root <dir> | --out <dir>] [--keep-steps]
        -> <root>\lcchain_<cam|nocam>_live_<8>   (one stage + install.py; helicam default = the lcoutcam2a set: f5 +700, f6 -500, aim the heli's ShatterGeom)
--in-dir (default: the live DM05A folder) holds the 5 files F01_Main.zip F01_Main.bots.zip F01_Main.bots.base.md5 KLJoin.ini KLGuns.ini.
It is only READ (each pass works on a copy). Nothing is ever written into the game folder (a stage under it is refused).

Each pass accepts the input md5 through its allow= / --allow-md5 parameter, nothing else is loosened. Each pass verifies its own edit on its output
with that tool's own check (doors: kl_club_doors_1106.check live->doors; spawn2f: kl_lc_spawns2f_1106.check; outro: spline point count;
helicam: CCameraBox read-back). If a pass cannot find its edit on a changed zip (node ids shifted, a node renamed, an assert) the run REFUSES with the
pass name and the reason, deletes its partial output, and guesses nothing. Doors recomputes Entries= of KLJoin.ini / KLGuns.ini from the .prm chunk
count of ITS OUTPUT and the ACTUAL input inis (one line changes).

The chain's install.py (tag .before-chain1106, like the per-pass ones): --undo, --dry, --game <dir>, --skip-run-check, --min-free-mb N; every pin is
checked BEFORE anything is written (all or nothing, originals put back on a failure); refuses while kl2.exe runs; never overwrites an existing backup.
"""
import hashlib
import json
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
ROOT = r'C:\kl_build_1024'
FILES5 = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5', 'KLJoin.ini', 'KLGuns.ini')
BIG3 = FILES5[:3]
INIS = FILES5[3:]
PASSES = ('doors', 'spawn2f', 'outro', 'helicam', 'rmi')       # the chain order; 'rmi' (Roof .rmi box 7 enlarged) runs only for --cam 2f
TAG = '.before-chain1106'
ROUTE_CAMS = ('2c', '2d', '2e', '2f')       # the cams that REPLACE the Escaping spline by a 5-point climb: 2c/2d the NE one (kl_club_outro_1106.ROUTE_2C), 2e the north one (ROUTE_2E)


def route_for(cam):
    import kl_club_outro_1106 as O
    return O.ROUTE_2E if cam in ('2e', '2f') else O.ROUTE_2C if cam in ROUTE_CAMS else None
NAMES = {'doors': 'lcdoors', 'spawn2f': 'lcspawn2f', 'outro': 'lcoutro', 'rmi': 'lcrmi'}


class Refused(Exception):
    """A pass cannot be applied to this input: nothing is staged."""


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_live(in_dir=MAPDIR):
    """{name: md5} of the 5 files; a missing one is an error."""
    out = {}
    for n in FILES5:
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p):
            raise Refused('%s is not there' % p)
        out[n] = md5(p)
    return out


def cam_params(cam):
    """--cam -> None (no helicam) or (variant, f5, f6, aim). 2a/2b = the lcoutcam2a / lcoutcam2b stage sets of kl_club_helicam_1106 (commit 150c84ed)."""
    import kl_club_helicam_1106 as H
    if cam == 'none':
        return None
    if cam == '2a':
        return ('A', 700.0, -500.0, H.AIM_B)           # eye f5 +700 / f6 -500, aimed at the heli's ShatterGeom
    if cam == '2b':
        return ('A', -450.0, 100.0, H.AIM_A)           # eye f5 -450 / f6 +100, aimed at EscCameraLAST (hover/rise only)
    if cam == '2c':
        return ('F', None, None, H.AIM_F)              # fixed eye CamPos01 (LookFromPos, in Roof .rmi box 7) + the climb route of the outro pass
    if cam == '2d':
        return ('D', None, None, H.AIM_D)              # stock outside camera (LookFromPosFA): eye = box node moved to the 2c eye, aim = the heli group; 2c's climb route
    if cam == '2e':
        return ('E', None, None, H.AIM_D)              # as 2d (LookFromPosFA, aim the heli group) but the eye is EYE_E (7400,2500,2800) and the route is ROUTE_2E (north climb)
    if cam == '2f':
        return ('E', None, None, H.AIM_D)              # exactly 2e (eye EYE_E, aim the heli group, north route ROUTE_2E) + the 'rmi' pass: Roof .rmi box 7 enlarged upward/eastward
    raise ValueError('--cam must be 2a, 2b, 2c, 2d, 2e, 2f or none')


def out_name(name, cam, live_md5, in_dir, doors=None):
    if name == 'chain' and cam in ('2e', '2f'):
        return 'lcchain_%s_' % cam + live_md5[:8]                     # the folder asked for: C:\kl_build_1024\lcchain_2e_<base8>
    tag = ('live_' if os.path.abspath(in_dir) == os.path.abspath(MAPDIR) else 'in_') + live_md5[:8]
    if name == 'chain':
        return 'lcchain_%s%s_%s' % ('nocam' if cam == 'none' else cam, '_d' + '-'.join(d[0] for d in doors) if doors else '', tag)
    if name == 'helicam':
        return 'lcoutcam%s_%s' % (cam, tag)
    if name == 'outro' and cam in ROUTE_CAMS:
        return 'lcoutro%s_%s' % (cam, tag)                      # never the folder of the plain outro stage
    return '%s_%s' % (NAMES[name], tag)


def guard_out(out):
    a, g = os.path.abspath(out).lower(), os.path.abspath(GAME).lower()
    if a == g or a.startswith(g + os.sep):
        raise Refused('%s is inside the Dog Days folder: stages are never written there' % out)


# ------------------------------------------------------------------ one pass on one input dir
def run_pass(name, in_dir, out, cam='2a', log=print, doors=None):
    """Stage pass `name` from the files in in_dir into out and verify it with the pass tool's own check. -> {file: md5} of out (the files that pass writes).
    Any failure, or a failed check, becomes Refused (out is deleted by the caller)."""
    h = md5(os.path.join(in_dir, 'F01_Main.zip'))
    allow = [h]
    try:
        if name == 'doors':
            import kl_club_doors_1106 as D
            D.stage(out, in_dir, True, log, allow=allow, doors=doors)
            bad, _ = D.check(out, in_dir, log, allow=allow, doors=doors)
            if bad:
                raise ValueError('doors self-check: %d faults: %s' % (len(bad), '; '.join(bad[:3])))
            files = FILES5
        elif name == 'spawn2f':
            import kl_lc_spawns2f_1106 as S
            S.stage(out, os.path.join(in_dir, 'F01_Main.zip'), h, log)
            bad, _ = S.check(out, os.path.join(in_dir, 'F01_Main.zip'), h, log)
            if bad:
                raise ValueError('spawn2f self-check: %d faults: %s' % (len(bad), '; '.join(map(str, bad[:3]))))
            files = BIG3
        elif name == 'outro':
            import kl_club_outro_1106 as O
            O.stage(out, in_dir, O.KEEP, False, log, allow=allow, route=route_for(cam))
            n = O.count_of(os.path.join(out, 'F01_Main.zip'))[4]
            if n > O.KEEP:
                raise ValueError('outro self-check: the Escaping spline has %d points, want <= %d' % (n, O.KEEP))
            files = BIG3
        elif name == 'helicam':
            import kl_club_helicam_1106 as H
            cp = cam_params(cam)
            if cp is None:
                raise ValueError('helicam needs --cam 2a, 2b or 2c')
            variant, f5, f6, aim = cp
            H.stage(out, in_dir, variant, f5, f6, aim, log, allow=allow)
            v = H.state(os.path.join(out, 'F01_Main.zip'))[3]
            fl, ai = H.wanted(variant, f5, f6, aim)
            if not H.done_state(v, fl, ai, H.MODES[variant]) or not H.eye_done(*H.state(os.path.join(out, 'F01_Main.zip'))[:2], variant):
                raise ValueError('helicam self-check: the camera box reads back as %r' % (v,))
            files = BIG3
        elif name == 'rmi':
            import kl_club_rmi_1106 as R
            R.stage(out, in_dir, log, allow=allow)
            bad = R.check(os.path.join(out, 'F01_Main.zip'), os.path.join(in_dir, 'F01_Main.zip'))
            if bad:
                raise ValueError('rmi self-check: %d faults: %s' % (len(bad), '; '.join(bad[:3])))
            files = BIG3
        else:
            raise ValueError('unknown pass %r' % name)
    except Refused:
        raise
    except Exception as e:              # a node/key not found on a changed zip, an assert in a tool: never guess past it
        raise Refused('pass %s cannot be applied to the input (zip md5 %s): %s: %s. REFUSING; nothing staged, nothing guessed.' % (
            name, h, type(e).__name__, e))
    return {n: md5(os.path.join(out, n)) for n in files}


def drop_big(d):
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        try:
            os.remove(os.path.join(d, n))
        except OSError:
            pass


# ------------------------------------------------------------------ the install.py of a chain stage
INSTALL = r'''r"""Installs / undoes the LAST CALL CHAIN @@PASSES@@ (2026-11-06, tools/kl_lastcall_chain_1106.py) on the live DM05A files, which were read at stage time:
every pin below is the md5 of a live file as it was then.

  python install.py            install (originals -> <name>.before-chain1106 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
  --min-free-mb N              free space wanted on the game drive besides the files (default 1024)
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Never touches KL_PortBackup or any other file."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', @@TAG@@
LIVE_ZIP_MD5 = @@PIN@@      # the precheck: the live plain zip must still be exactly this
FILES = [   # name, live md5 before, staged md5 after
@@FILES@@]


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
    min_free = (int(a[a.index('--min-free-mb') + 1]) if '--min-free-mb' in a else 1024) << 20
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if n == 'F01_Main.zip' and not undo and cur != LIVE_ZIP_MD5:
            print('REFUSED: the live zip is %s, not %s: another pass changed it, re-stage the chain on the new live files' % (cur, LIVE_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + min_free
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + %d MB free on the game drive' % (min_free >> 20)); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
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
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(st, files, passes, tag=TAG):
    """files {name: (live md5, staged md5)}; only the names whose md5 changes are installed. The zip is always pinned."""
    if 'F01_Main.zip' not in files:
        raise ValueError('the zip must be in files')
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = INSTALL.replace('@@FILES@@', fl).replace('@@PIN@@', repr(files['F01_Main.zip'][0])).replace('@@PASSES@@', '+'.join(passes)).replace('@@TAG@@', repr(tag))
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL last call chain 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call chain 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


# ------------------------------------------------------------------ stage
def stage_single(name, in_dir=MAPDIR, out=None, root=ROOT, cam='2a', log=print):
    """One pass on the files of in_dir -> out (default <root>\\<name>_live_<8>), with that pass tool's own install.py (pins = the in_dir files)."""
    live = read_live(in_dir)
    out = out or os.path.join(root, out_name(name, cam, live['F01_Main.zip'], in_dir))
    guard_out(out)
    shutil.rmtree(out, ignore_errors=True)
    try:
        got = run_pass(name, in_dir, out, cam, log)
        if read_live(in_dir) != live:
            raise Refused('the input files changed while the pass was staged: re-run')
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    log('single %s staged in %s: %s' % (name, out, ' '.join('%s=%s' % (k, v[:8]) for k, v in got.items())))
    return out, live, got


def stage_chain(in_dir=MAPDIR, out=None, root=ROOT, cam='2a', only=None, keep_steps=False, log=print, doors=None, pin_dir=None, tag=TAG, expect=None):
    """live -> doors -> spawn2f -> outro -> helicam as ONE stage in out whose install.py pins the md5s of in_dir's files read first.
    pin_dir (default in_dir): the folder whose 5 files are pinned as the install's "before" (e.g. the LIVE folder when in_dir is the pre-chain base of an
    earlier candidate, so the new stage installs directly over it); tag: the backup suffix of that install (default .before-chain1106)."""
    import kl_club_doors_1106 as D
    try:
        sel = D.select(doors) if doors else None                   # None = all four doors (the default, unchanged)
    except ValueError as e:
        raise Refused(str(e))
    if sel and only and 'doors' not in only:
        raise Refused('--doors given but the doors pass is not in --only')
    live = read_live(in_dir)
    if expect and not any(live['F01_Main.zip'].startswith(e) for e in expect):
        raise Refused('--expect-base: the zip of %s is %s, not one of %s: build on the live base you meant (or change --expect-base)' % (in_dir, live['F01_Main.zip'], ', '.join(expect)))
    todo = [p for p in PASSES if (only is None or p in only) and not (p == 'helicam' and cam == 'none') and not (p == 'rmi' and cam != '2f')]
    if not todo:
        raise Refused('nothing to do')
    if only:
        bad = [p for p in only if p not in PASSES]
        if bad:
            raise Refused('unknown pass %s' % bad)
    out = out or os.path.join(root, out_name('chain', cam, live['F01_Main.zip'], in_dir, sel))
    guard_out(out)
    shutil.rmtree(out, ignore_errors=True)
    steps = os.path.join(out, '_steps')
    os.makedirs(steps)
    cur, prev, report = in_dir, None, {'in_dir': in_dir, 'pin_dir': pin_dir, 'tag': tag, 'live': live, 'cam': cam, 'passes': todo, 'steps': []}
    inis = {n: os.path.join(in_dir, n) for n in INIS}
    try:
        for i, p in enumerate(todo):
            d = os.path.join(steps, '%d_%s' % (i + 1, p))
            log('=== step %d/%d: %s on %s (zip %s)' % (i + 1, len(todo), p, cur, md5(os.path.join(cur, 'F01_Main.zip'))[:8]))
            got = run_pass(p, cur, d, cam, log, [x[0] for x in sel] if sel else None)
            report['steps'].append({'pass': p, 'out': d, 'files': got})
            if p == 'doors':                                    # the only pass that changes the inis (Entries=, recomputed from the actual input inis)
                for n in INIS:
                    keep = os.path.join(steps, 'inis_' + n)
                    shutil.copyfile(os.path.join(d, n), keep)
                    inis[n] = keep
            if prev:
                shutil.rmtree(prev, ignore_errors=True)          # the earlier step's two ~115 MB zips are no longer needed
            cur = prev = d
        final = {n: os.path.join(cur, n) for n in BIG3}
        final.update(inis)
        for n, src in final.items():
            shutil.copyfile(src, os.path.join(out, n))
        if read_live(in_dir) != live:
            raise Refused('the input files changed while the chain was staged: re-run')
        problems = verify_final(out, todo, cam, log)
        if problems:
            raise Refused('chain self-check failed: ' + '; '.join(problems))
        pins = read_live(pin_dir) if pin_dir else live
        files = {n: (pins[n], md5(os.path.join(out, n))) for n in FILES5}
        report['files'] = files
        write_install(out, files, todo + (['cam' + cam] if 'helicam' in todo else []), tag)
        with open(os.path.join(out, 'build_report.json'), 'w') as fh:
            json.dump(report, fh, indent=1, default=str)
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    if not keep_steps:
        shutil.rmtree(steps, ignore_errors=True)
    log('chain staged in %s' % out)
    for n, (o, w) in files.items():
        log('  %-26s live %s -> %s%s' % (n, o[:8], w[:8], '' if o != w else '  (unchanged, not installed)'))
    return out, live, files


def verify_final(out, todo, cam, log=print):
    """Cheap whole-chain checks on the finished stage (each pass was already checked on its own output). -> list of problems."""
    bad = []
    zp = os.path.join(out, 'F01_Main.zip')
    if 'outro' in todo:
        import kl_club_outro_1106 as O
        n = O.count_of(zp)[4]
        log('  final: Escaping spline points %d' % n)
        if n > O.KEEP:
            bad.append('outro edit gone in the final zip (%d points)' % n)
        if cam in ROUTE_CAMS:
            B, k, _l, raw, _n = O.count_of(zp)
            R, T = O.frame_of(zp, k)
            if not O.route_done(O.world_points(raw, R, T), route_for(cam), 1.0):
                bad.append('%s climb route gone in the final zip: %r' % (cam, O.world_points(raw, R, T),))
            else:
                log('  final: Escaping spline is the %s climb route (%d points)' % (cam, n))
    if 'helicam' in todo:
        import kl_club_helicam_1106 as H
        variant, f5, f6, aim = cam_params(cam)
        v = H.state(zp)[3]
        B = H.state(zp)[0]
        if not H.done_state(v, *H.wanted(variant, f5, f6, aim), H.MODES[variant]) or not H.eye_done(B, H.state(zp)[1], variant):
            bad.append('helicam edit gone in the final zip: %r' % (v,))
        else:
            log('  final: EscCamera01 %s f5/f6 %s,%s aim %s' % (v[11], v[5], v[6], v[9]))
    if 'rmi' in todo:
        import kl_club_rmi_1106 as R
        b = R.check(zp)
        bad += ['rmi check: %s' % x for x in b]
        log('  final: Roof .rmi box 7 enlarged: %s' % ('PASS' if not b else 'FAIL'))
    if 'spawn2f' in todo:
        import kl_lc_spawns2f_1106 as S
        b, _rows = S.points(zp)
        bad += ['spawn point check: %s' % x for x in b]
        log('  final: spawn points check %s' % ('PASS' if not b else 'FAIL'))
    bz = os.path.join(out, 'F01_Main.bots.zip')
    with zipfile.ZipFile(zp) as a, zipfile.ZipFile(bz) as b:
        if a.namelist() != b.namelist():
            bad.append('bots zip member list differs from the plain zip')
        else:
            dd = [n for n in a.namelist() if a.read(n) != b.read(n)]
            if [n.rsplit('_Main', 1)[-1] for n in dd] != ['.prp']:
                bad.append('bots zip differs from the plain zip in %s (want only .prp)' % dd)
    if open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip() != md5(zp):
        bad.append('bots.base.md5 is not the md5 of the plain zip')
    return bad


# ------------------------------------------------------------------ cli
def main(a):
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('status', 'single', 'chain'):
        print(__doc__)
        return 2
    in_dir, root, out, cam = opt('--in-dir', MAPDIR), opt('--root', ROOT), opt('--out'), opt('--cam', '2a')
    try:
        cam_params(cam)
        if a[0] == 'status':
            for n, h in read_live(in_dir).items():
                print('%-26s %s' % (n, h))
            return 0
        if a[0] == 'single':
            if len(a) < 2 or a[1] not in PASSES:
                print('single needs one of %s' % ', '.join(PASSES))
                return 2
            stage_single(a[1], in_dir, out, root, cam)
        else:
            only = opt('--only')
            stage_chain(in_dir, out, root, cam, only.split(',') if only else None, '--keep-steps' in a, doors=opt('--doors'),
                        pin_dir=opt('--pin-dir'), tag=opt('--tag', TAG),
                        expect=[x for x in opt('--expect-base', '').split(',') if x] or None)
    except Refused as e:
        print('REFUSED: %s' % e)
        return 1
    except ValueError as e:
        print('REFUSED: %s' % e)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
