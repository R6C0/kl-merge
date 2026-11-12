"""Merc down-not-dead A/B test (helper, 11 Oct). Optionally installs <build>\\<L> over Scenes\\Locations\\<L> (backup first,
under GAME_LOCK), then runs work/helper/scratch/longplay.py <L> <secs> with ANP_god.txt='1' (player safe) and the empty
ANP_cutdiag.txt (fire/move bursts every 30 s, D3D shots every 5 s, loopback audio), then counts from the log:
  - merc downs/deaths: per SQUAD stat member, transitions able=1 -> able=0 (and back = got up)
  - scene reloads: n644 increments (each = a game-state transition back to InGame; in M09 = mission fail -> reload)
  - mission-fail signs: lines with 'MF_' / 'MissionFailed' / 'mission fail'
  - shots taken within 10 s after each down (paths)
Writes <run>/dnd_result.txt and prints it. --restore puts the backup back after the run.
usage: py scripts\\smoke_dnd.py <L> [--build work\\out_xxx] [--secs 300] [--restore] [--tag A]"""
import os, sys, re, time, glob, shutil, hashlib, subprocess, argparse
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(REPO, 'work', 'helper', 'scratch'); sys.path.insert(0, SCR); import gamelock
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
PY = sys.executable
ap = argparse.ArgumentParser(); ap.add_argument('level'); ap.add_argument('--build'); ap.add_argument('--secs', default='300')
ap.add_argument('--restore', action='store_true'); ap.add_argument('--tag', default='')
a = ap.parse_args(); L = a.level
sha = lambda p: hashlib.sha1(open(p, 'rb').read()).hexdigest()
dst = os.path.join(DD, 'Scenes', 'Locations', L); bk = None

if a.build:
    bk = os.path.join(REPO, 'work', 'backup', 'dnd_%s_%s' % (L, time.strftime('%m%d_%H%M%S')))
    gamelock.wait_free(); gamelock.acquire('smoke_dnd install %s %s' % (L, a.build))
    try:
        if gamelock.running(): sys.exit('kl2.exe running')
        if os.path.isdir(dst): shutil.copytree(dst, bk)
        src = os.path.join(REPO, a.build, L) if not os.path.isabs(a.build) else os.path.join(a.build, L)
        bad = 0
        for f in os.listdir(src):
            s, d = os.path.join(src, f), os.path.join(dst, f); os.makedirs(dst, exist_ok=True); shutil.copy2(s, d); bad += sha(s) != sha(d)
        print('installed %s -> %s (mismatches %d), backup %s' % (src, dst, bad, bk), flush=True)
    finally:
        gamelock.release()

gamelock.wait_free()
before = set(glob.glob(os.path.join(REPO, 'work', 'smoke', 'long_%s_*' % L)))
subprocess.run([PY, os.path.join(SCR, 'longplay.py'), L, a.secs], env=dict(os.environ, LONG_GOD='1', LONG_CUT='1'))
run = sorted(set(glob.glob(os.path.join(REPO, 'work', 'smoke', 'long_%s_*' % L))) - before)
run = run[-1] if run else None

out = []
if run:
    lg = open(os.path.join(run, 'log.txt'), encoding='utf-8', errors='replace').read().splitlines()
    ts = lambda l: (lambda m: int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None)(re.match(r'\[(\d+):(\d+):([\d.]+)\]', l))
    t0 = next((ts(l) for l in lg if ts(l) is not None), 0)
    last, downs, ups = {}, [], 0
    for l in lg:
        if 'SQUAD stat' not in l: continue
        for m in re.finditer(r"\[(\d+)\]\*? m=(\d+) '([^']*)' ctl=(\d) able=(\d)", l):
            key = m.group(2); able = m.group(5)
            if last.get(key) == '1' and able == '0': downs.append((ts(l) - t0, key, m.group(3)))
            if last.get(key) == '0' and able == '1': ups += 1
            last[key] = able
    n644 = [int(v) for v in re.findall(r'n644=(\d+)', '\n'.join(lg))]
    reloads = (max(n644) - 1) if n644 else 0
    fails = [l[:160] for l in lg if re.search(r'MF_|MissionFailed|mission fail', l, re.I)]
    exc = [l[:160] for l in lg if 'EXCEPTION' in l and 'a8e3cb' not in l.lower()]
    shots = sorted(glob.glob(os.path.join(run, '*.jpg')))
    def shots_after(t):
        res = []
        for s in shots:
            m = re.search(r'_t(\d+)\.jpg$', s)
            if m and 0 <= int(m.group(1)) - t <= 25: res.append(os.path.basename(s))
        return res[:3]
    out.append('level %s %s build %s run %s' % (L, a.tag, a.build or '(installed)', run))
    out.append('merc downs (able 1->0): %d   got up again (0->1): %d' % (len(downs), ups))
    for t, k, nm in downs: out.append('  t=%.0fs merc m=%s %s  shots: %s' % (t, k, nm, ' '.join(shots_after(t + 20))))
    out.append('scene reloads (n644 steps beyond the first): %d' % reloads)
    out.append('mission-fail lines: %d %s' % (len(fails), fails[0] if fails else ''))
    out.append('exceptions: %d %s' % (len(exc), exc[0] if exc else ''))
    open(os.path.join(run, 'dnd_result.txt'), 'w').write('\n'.join(out) + '\n')
else:
    out.append('no run folder (the run did not start?)')
print('\n'.join(out))

if a.restore and bk:
    gamelock.wait_free(grace=20); gamelock.acquire('smoke_dnd restore %s' % L)
    try:
        if gamelock.running(): print('kl2.exe running: NOT restored; backup', bk)
        else: shutil.rmtree(dst); shutil.copytree(bk, dst); print('restored', dst, 'from', bk)
    finally:
        gamelock.release()
