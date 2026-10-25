#!/usr/bin/env python3
"""kl_l05_build_1025.py - the whole offline build chain of DD10 The Flat Raid (Dog Days L05 on F07's Fragile Alliance systems), reproducible from one place.

    python tools/kl_l05_build_1025.py <work dir> [--plan <van.json>] [--from <step>] [--stage <stage out dir>] [--rehearse <scratch game dir>]

Steps, each into its own folder under <work dir> (a step whose folder already holds its zip is NOT redone; delete the folder to redo it):
    b3   kl_l05_layer.py test      F07 + L05 with the layer, finish (briefcases, hidden props, CoopAirLock path blockers inert), nav bridges, bots + dyn, check()
    c1   kl_l05_layer.py cover     the extra cover boxes
    d1   kl_dmlines.py --fed       Dead Men voice lines (GameEnds, Shoot_Off_Money, fed respawn / kill)
    e1   kl_gunpics.py apply       gun silhouettes, ONCE (it is not idempotent)
    f3   kl_dm_overhaul_1025.py    build DD10 (extinguishers + fuel cans)
    f4   kl_fa_fedbody.py apply    KLJoin.ini [FedBody] AFTER the last .prm change (every other file hard-linked)
    install\\KLExpansion\\{Maps,BuildInfo}\\DD10   the tree kl_l05_stage_1025.py stages (F01_* files renamed F07_*)
then the passes: kl_fa_fedbody check, debug/check_passes.py (A / B / C1 / C2 / C3), debug/check.py, klt_audit, kl_prpjoin.dangling, kl_l05_layer check.
Every step is a subprocess of an existing tool; nothing is installed, the game is never touched. --stage / --rehearse then run kl_l05_stage_1025.py.
Needs a plan of the van: the default is the van.json of C:/kl_build_1024/l05fa_1025a/f4 (the same measured plan).
"""
import hashlib, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
PLAN = 'C:/kl_build_1024/l05fa_1025a/f4/van.json'
SLOT = 'F07'                                    # the host slot; the build folders name their archive F01_Main (the test slot), the install tree F07_Main
MIN_FREE_GB = 6.0


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def run(args, log, cwd=ROOT, ok=(0,)):
    log('$ ' + ' '.join(args))
    r = subprocess.run([PY, '-u'] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    log(r.stdout.rstrip())
    log('exit %d' % r.returncode)
    if r.returncode not in ok:
        raise SystemExit('step failed (exit %d): %s' % (r.returncode, ' '.join(args)))
    return r.stdout


def carry(src, dst):
    """Every file of src that dst lacks, hard-linked (copied when the link fails)."""
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        s, d = os.path.join(src, f), os.path.join(dst, f)
        if os.path.isfile(s) and not os.path.exists(d):
            try:
                os.link(s, d)
            except OSError:
                shutil.copy2(s, d)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    w = os.path.abspath(a[0]).replace('\\', '/')
    plan = a[a.index('--plan') + 1] if '--plan' in a else PLAN
    free = shutil.disk_usage(os.path.splitdrive(w)[0] + '/').free / 1e9
    if free < MIN_FREE_GB:
        sys.exit('only %.1f GB free, %.0f needed' % (free, MIN_FREE_GB))
    os.makedirs(w, exist_ok=True)
    lf = open(os.path.join(w, 'chain.log'), 'a', encoding='utf-8')
    def log(s):
        print(s, flush=True)
        lf.write(s + '\n'); lf.flush()
    T = lambda n: os.path.join(HERE, n)
    zipname = lambda d: os.path.join(d, 'F01_Main.zip')
    b3 = w + '/b3/F07+L05'
    if not os.path.isfile(zipname(b3)):
        # --keep: test() deletes the archive when check() fails; exit 1 (check FAILs) is logged and the chain goes on so the failures are reported with the build
        run([T('kl_l05_layer.py'), 'test', w + '/b3', '--plan', plan, '--keep'], log, ok=(0, 1))
    c1 = w + '/c1'
    if not os.path.isfile(zipname(c1)):
        run([T('kl_l05_layer.py'), 'cover', zipname(b3), c1], log)
        carry(b3, c1)
    d1 = w + '/d1'
    if not os.path.isfile(zipname(d1)):
        run([T('kl_dmlines.py'), c1, d1, '--fed'], log)
        carry(c1, d1)
    e1 = w + '/e1'
    if not os.path.isfile(zipname(e1)):
        os.makedirs(e1, exist_ok=True)
        run([T('kl_gunpics.py'), 'apply', zipname(d1), zipname(e1)], log)
        carry(d1, e1)
    f3 = w + '/f3'
    if not os.path.isfile(zipname(f3)):
        os.makedirs(f3, exist_ok=True)
        run([T('kl_dm_overhaul_1025.py'), 'build', 'DD10', zipname(e1), zipname(f3)], log)
        carry(e1, f3)
    f4 = w + '/f4'
    if not os.path.isfile(os.path.join(f4, 'KLJoin.ini')):
        run([T('kl_fa_fedbody.py'), 'apply', f3, f4, '--link'], log)
    log('zip %s md5 %s  %d bytes; KLJoin.ini md5 %s' % (zipname(f4), md5(zipname(f4)), os.path.getsize(zipname(f4)), md5(f4 + '/KLJoin.ini')))
    # ---- the install tree (what the stage tool wants): F01_* -> F07_*; the Build* files beside it as BuildInfo
    inst = w + '/install/KLExpansion'
    maps, info = inst + '/Maps/DD10', inst + '/BuildInfo/DD10'
    os.makedirs(maps, exist_ok=True); os.makedirs(info, exist_ok=True)
    for f in sorted(os.listdir(f4)):
        s = os.path.join(f4, f)
        if not os.path.isfile(s):
            continue
        game = f.startswith('F01_Main') or f == 'KLJoin.ini' or f in ('KLTalk.ini', 'KLGuns.ini')
        d = os.path.join(maps if game else info, f.replace('F01_Main', SLOT + '_Main'))
        if not os.path.exists(d):
            try:
                os.link(s, d)
            except OSError:
                shutil.copy2(s, d)
    # ---- the passes
    log('=== passes')
    run([T('kl_fa_fedbody.py'), 'check', f4], log)
    out = run([os.path.join(ROOT, 'debug', 'check_passes.py'), zipname(f4)], log)
    run([os.path.join(ROOT, 'debug', 'check.py'), zipname(f4)], log)
    run([T('klt_audit.py'), inst], log)
    run(['-c', "import sys; sys.path.insert(0, %r); import kl_prpjoin as J; s = J.Scene.from_zip(%r, 'dd', 'DD10'); p, n = J.dangling(s); print('dangling: %%d paths, %%d names' %% (len(p), len(n))); sys.exit(1 if p or n else 0)" % (HERE, zipname(f4))], log)
    run([T('kl_l05_layer.py'), 'check', f4], log, ok=(0, 1))
    if '--stage' in a:
        st = a[a.index('--stage') + 1]
        cmd = [T('kl_l05_stage_1025.py'), 'stage', w + '/install', st]
        if '--rehearse' in a:
            cmd += ['--rehearse', a[a.index('--rehearse') + 1]]
        run(cmd, log)
    log('DONE ' + time.strftime('%Y-%m-%d %H:%M'))


if __name__ == '__main__':
    main()
