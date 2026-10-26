#!/usr/bin/env python3
"""
Two kl2.exe on one PC: the solo bench for the online code (re/netsmooth_solo.md; hook part klhook/klsolo.c).

    python kl_solo_test.py --hook <TEST build folder> --tag <name> [--secs 300] [--gap 45]
                           [--base <KLHook.ini>] [--ini1 <extra.ini>] [--ini2 <extra.ini>] [--shots 30-300:30] [--force]
                           [--n N (3+: more joiners, all with --ini2)] [--gap2 30 (between joiners)]
                           [--netstat SECS] [--relaunch K (3: a failed joiner is started again, before the host's Ready)]

- Puts the TEST dinput8.dll into the game folder for the run and puts the one that was there back afterwards
  (kl_autotest.snapshot / restore_original). The game folder's KLHook.ini is not touched: each instance reads
  its own <work>/build/klhook/solo/<tag>/inst<N>/KLHook.ini (env KLHOOK_DIR, TEST builds only) and writes its
  KLHook.log / KLHook.result / dumps there.
- Instance ini = --base (default: the game folder's KLHook.ini) + [Solo] Enable=1 X/Y/W/H (side by side) +
  [Net] Log=1 + [NetSmooth] Enable=1 Log=1 Probe=1 + [Load] NudgeMs=86400000 (no game-made mouse input), then the sections of --ini1 / --ini2 on top (key by key;
  a [Script] section there replaces the base's whole [Script]).
- Starts kl2.exe directly (no steam://, so the Steam launch options are NOT used) with env SteamAppId=SteamGameId=28000
  and '-o DisableSplashScreens'; instance 2 --gap seconds after instance 1. Ends both after --secs.
- Refuses while a kl2.exe runs, or while the owner gave input in the last 300 s (--force skips that check).
- --netstat SECS: for the first SECS seconds samples 'netstat -ano -p UDP' every 2 s, keeps the rows of the kl2 pids and
  writes every CHANGE (a socket opened / closed, with the second since the start) into run.txt as 'netstat | ...' lines.
  A control for the System Link discovery question (re/netsmooth_camyaw.md): does the host hold UDP 9100 / 9103 before the
  client searches, and which port does the client's search socket use. Both processes' sockets are on one PC, so the
  rows say who bound what, not whether a broadcast was heard.
Prints per instance: alive at the end?, the solo / net / netsmooth lines of its log, KLHook.result, and a RESULT line.
"""
import ctypes, os, re, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_autotest as at
from kl_port_check import find, DD_GUESSES, DD_EXE, workdir

KEEP = ('solo:', 'net:', 'netsmooth', 'FATAL', 'CRASH', 'assert', 'exit:', 'auto:', 'script', 'tick: driven')


def idle_s():
    class L(ctypes.Structure):
        _fields_ = [('s', ctypes.c_uint), ('t', ctypes.c_uint)]
    l = L(8, 0)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(l))
    return ((ctypes.windll.kernel32.GetTickCount() - l.t) & 0xffffffff) // 1000


def firewall_ok(exe):
    """What kl2's System Link check (0x8945d0) will see: firewall off, or the exe enabled in AuthorizedApplications. Read-only."""
    ps = ("$p=(New-Object -ComObject HNetCfg.FwMgr).LocalPolicy.CurrentProfile; if(-not $p.FirewallEnabled){'off'} "
          "else { $a=$p.AuthorizedApplications | ?{ $_.ProcessImageFileName -eq '%s' -and $_.Enabled }; if($a){'allowed'}else{'blocked'} }" % exe.replace("'", "''"))
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True)
    return (r.stdout.strip() or 'unknown: ' + r.stderr.strip()[:100])


def netstat_rows(pids):
    """-> {(pid, proto, local address)} of 'netstat -ano -p UDP' for those pids ('*:*' foreign column of UDP rows ignored)."""
    r = subprocess.run(['netstat', '-ano', '-p', 'UDP'], capture_output=True, text=True)
    rows = set()
    for l in r.stdout.splitlines():
        f = l.split()
        if len(f) >= 4 and f[0] == 'UDP' and f[-1].isdigit() and int(f[-1]) in pids:
            rows.add((int(f[-1]), f[0], f[1]))
    return rows


def read_ini(path):
    """-> [(section, [(key, value) or (None, raw line)])] in file order; keys keep their case."""
    out, cur = [], None
    for raw in open(path, encoding='latin-1').read().splitlines():
        m = re.match(r'\s*\[([^\]]+)\]', raw)
        if m:
            cur = (m.group(1), []); out.append(cur); continue
        if cur is None:
            cur = ('', []); out.append(cur)
        k, eq, v = raw.partition('=')
        cur[1].append((k.strip(), v.strip()) if eq and not raw.lstrip().startswith(';') else (None, raw))
    return out


def merge(base, over):
    """over's keys win; a [Script] in over replaces base's [Script] entirely."""
    secs = {s.lower(): (s, items) for s, items in base}
    order = [s for s, _ in base]
    for s, items in over:
        if s.lower() == 'script' or s.lower() not in secs:
            if s.lower() not in secs:
                order.append(s)
            secs[s.lower()] = (s, list(items)); continue
        _, have = secs[s.lower()]
        for k, v in items:
            if k is None:
                continue
            for i, (k2, _) in enumerate(have):
                if k2 is not None and k2.lower() == k.lower():
                    have[i] = (k, v); break
            else:
                have.append((k, v))
    return [secs[s.lower()] for s in order]


def write_ini(path, secs):
    lines = []
    for s, items in secs:
        if s:
            lines.append('[%s]' % s)
        lines += [v if k is None else '%s=%s' % (k, v) for k, v in items]      # (None, raw line) keeps the line
    open(path, 'w', encoding='latin-1').write('\n'.join(lines) + '\n')


def solo_secs(n, total=2):
    # 2 instances: side by side 960x540; more: a grid of ceil(sqrt(total)) columns across 1920 px (9 -> 3x3 of 640x360)
    cols = 2 if total <= 2 else int(-(-total ** 0.5 // 1))
    w = 960 if total <= 2 else 1920 // cols
    h = w * 9 // 16
    x, y = ((n - 1) % cols) * w, ((n - 1) // cols) * h
    return [('Solo', [('Enable', '1'), ('Windowed', '1'), ('Focus', '1'), ('X', str(x)), ('Y', str(y)), ('W', str(w)), ('H', str(h))]),
            ('Net', [('Log', '1')]),
            ('NetSmooth', [('Enable', '1'), ('Log', '1'), ('Probe', '1')]),
            # The game calls mouse_event(MOVE,0,0) (0x6f4220, klnudge.c) while its window is in front; each one passed on resets
            # GetLastInputInfo, so the owner-idle check above read the bench's own nudge as owner input (E0a: 04:37:43 / 04:38:43).
            # 24 h = none passed on during a run: the idle check then sees only real input (needs klnudge.c from 1022c on:
            # before it, values over 60000 counted as 0 = the slot not wrapped, the game nudging every frame - E0b).
            ('Load', [('NudgeMs', '86400000')])]


def main():
    a, opt = sys.argv[1:], {}
    for key in ('--hook', '--tag', '--secs', '--gap', '--gap2', '--base', '--ini1', '--ini2', '--shots', '--n', '--netstat', '--relaunch'):
        if key in a:
            i = a.index(key); opt[key] = a[i + 1]; del a[i:i + 2]
    force = '--force' in a
    tag, secs, gap = opt.get('--tag', time.strftime('solo_%H%M%S')), int(opt.get('--secs', 300)), int(opt.get('--gap', 45))
    shots = []
    for x in opt.get('--shots', '30-%d:30' % secs).split(','):
        r, _, st = x.partition(':'); lo, _, hi = r.partition('-')
        shots += range(int(lo), int(hi or lo) + 1, int(st or 30))
    shots = sorted(set(shots))
    dd = find(DD_GUESSES, DD_EXE)
    if not dd or '--hook' not in opt:
        raise SystemExit('usage: --hook <TEST build> (and Dog Days must be found)')
    if at.running():
        raise SystemExit('RESULT: not started - kl2.exe is already running')
    if not force and idle_s() < 300:
        raise SystemExit('RESULT: not started - owner input %d s ago' % idle_s())
    fw = firewall_ok(os.path.join(dd, 'kl2.exe'))
    print('  firewall | %s (System Link opens only if off / allowed)' % fw, flush=True)
    if fw == 'blocked' and '--any-firewall' not in a:
        raise SystemExit('RESULT: not started - kl2.exe is not allowed by Windows Firewall; System Link would stop at '
                         'Online/BlockedByFirewall (the owner allows it; --any-firewall runs anyway)')
    root = os.path.join(workdir(), 'build', 'klhook', 'solo', tag)
    out = []

    def say(t):
        print(t, flush=True); out.append(t)
    base = read_ini(opt.get('--base', os.path.join(dd, 'KLHook.ini')))
    inst = []
    total = int(opt.get('--n', 2))
    for n in range(1, total + 1):                             # --n 1: one instance (control runs); 3+: instances 3.. take --ini2 (more joiners)
        d = os.path.join(root, 'inst%d' % n)
        os.makedirs(d, exist_ok=True)
        for f in ('KLHook.log', 'KLHook.result'):
            if os.path.isfile(os.path.join(d, f)):
                os.remove(os.path.join(d, f))
        secs_n = merge(base, solo_secs(n, total))
        extra = opt.get('--ini%d' % min(n, 2))
        if extra:
            secs_n = merge(secs_n, read_ini(extra))
        write_ini(os.path.join(d, 'KLHook.ini'), secs_n)
        inst.append(d)
    was = at.snapshot(dd, say)
    procs, code = [], 1
    ns_secs, ns_prev, ns_t = int(opt.get('--netstat', 0)), set(), [0.0]

    def netstat_tick(t0):
        # every 2 s while inside the first --netstat seconds: log what the kl2 pids bound / let go (changes only)
        nonlocal ns_prev
        el = time.time() - t0
        if not ns_secs or el > ns_secs or el - ns_t[0] < 2 or not procs:
            return
        ns_t[0] = el
        cur = netstat_rows({p.pid for p in procs})
        names = {p.pid: 'inst%d' % (i + 1) for i, p in enumerate(procs)}
        for pid, proto, addr in sorted(cur - ns_prev):
            say('  netstat | %+.0f s %s pid %d %s %s OPEN' % (el, names[pid], pid, proto, addr))
        for pid, proto, addr in sorted(ns_prev - cur):
            say('  netstat | %+.0f s %s pid %d %s %s CLOSED' % (el, names[pid], pid, proto, addr))
        ns_prev = cur
    try:
        src = opt['--hook']; src = os.path.join(src, 'dinput8.dll') if os.path.isdir(src) else src
        note = at.put(src, os.path.join(dd, 'dinput8.dll'))
        say('  hook | %s (sha1 %s)%s' % (src, at.sha1(src)[:8], ' - ' + note if note else ''))
        t0 = time.time()
        for n, d in enumerate(inst, 1):
            if n >= 2:                                     # joiner k starts at gap + (k-2) * gap2 (--gap2, default 30 s): one at a time through the menus
                while time.time() - t0 < gap + (n - 2) * int(opt.get('--gap2', 30)):
                    time.sleep(1)
                    netstat_tick(t0)
            env = dict(os.environ, SteamAppId='28000', SteamGameId='28000', KLHOOK_DIR=d)
            p = subprocess.Popen([os.path.join(dd, 'kl2.exe'), '-o', 'DisableSplashScreens'], cwd=dd, env=env)
            procs.append(p)
            say('  start | inst%d pid %d at %+.0f s (%s)' % (n, p.pid, time.time() - t0, d))
        retries = {n: int(opt.get('--relaunch', 3)) for n in range(2, len(inst) + 1)}
        last_start = [time.time()]

        def host_started():
            log = os.path.join(inst[0], 'KLHook.log')
            try:
                return 'SOLO match started' in open(log, encoding='latin-1').read() or 'host Ready with' in open(log, encoding='latin-1').read()
            except OSError:
                return False

        def relaunch_tick():
            # --relaunch K (default 3): a joiner whose script FAILED or whose process ended before the host started the
            # round is started again (its log kept as KLHook_try<k>.log), one at a time, at least 20 s apart
            if time.time() - last_start[0] < 20 or host_started():
                return
            for n in range(2, len(procs) + 1):
                d, p = inst[n - 1], procs[n - 1]
                res = os.path.join(d, 'KLHook.result')
                try:
                    failed = 'state=FAIL' in open(res, errors='replace').read()
                except OSError:
                    failed = False
                if not (failed or p.poll() is not None) or retries[n] <= 0:
                    continue
                if p.poll() is None:
                    subprocess.run(['taskkill', '/F', '/PID', str(p.pid)], capture_output=True); time.sleep(2)
                k = int(opt.get('--relaunch', 3)) - retries[n] + 1; retries[n] -= 1
                for f, g in (('KLHook.log', 'KLHook_try%d.log' % k), ('KLHook.result', 'KLHook_try%d.result' % k)):
                    if os.path.isfile(os.path.join(d, f)):
                        os.replace(os.path.join(d, f), os.path.join(d, g))
                env = dict(os.environ, SteamAppId='28000', SteamGameId='28000', KLHOOK_DIR=d)
                procs[n - 1] = subprocess.Popen([os.path.join(dd, 'kl2.exe'), '-o', 'DisableSplashScreens'], cwd=dd, env=env)
                last_start[0] = time.time()
                say('  relaunch | inst%d try %d pid %d at %+.0f s (%s)' % (n, k + 1, procs[n - 1].pid, time.time() - t0,
                                                                         'its script failed' if failed else 'the process had ended'))
                return
        while time.time() - t0 < secs:
            time.sleep(2)
            el = time.time() - t0
            netstat_tick(t0)
            relaunch_tick()
            if shots and el >= shots[0]:
                s = shots.pop(0)
                for n, p in enumerate(procs, 1):
                    if p.poll() is None:
                        path = os.path.join(root, 'shot_inst%d_%03ds.png' % (n, s))
                        r = at.shot([p.pid], path)
                        say('  shot | inst%d %ds %s' % (n, s, path if r else 'no window'))
            alive = at.running()
            if procs and not alive and el > gap + 20:
                break
        say('  end | %+.0f s; alive: %s; all kl2 pids now: %s' % (time.time() - t0, ['inst%d' % (n + 1) for n, p in enumerate(procs) if p.poll() is None], at.running()))
        for p in procs:
            if p.poll() is None:
                subprocess.run(['taskkill', '/F', '/PID', str(p.pid)], capture_output=True)
        for pid in at.running():                     # a Steam relaunch would have another pid
            say('  end | other kl2.exe pid %d (Steam relaunch?) ended' % pid)
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
        time.sleep(3)
        verdict = []
        for n, d in enumerate(inst, 1):
            log = os.path.join(d, 'KLHook.log')
            lines = open(log, encoding='latin-1').read().splitlines() if os.path.isfile(log) else []
            say('  inst%d | exit code %s, %d log lines' % (n, procs[n - 1].returncode if n <= len(procs) else '-', len(lines)))
            for l in [l for l in lines if any(k in l for k in KEEP)][-40:]:
                say('    log | ' + l[:220])
            res = os.path.join(d, 'KLHook.result')
            if os.path.isfile(res):
                say('    KLHook.result | ' + ' '.join(open(res, errors='replace').read().split())[:400])
            failed = os.path.isfile(res) and 'state=FAIL' in open(res, errors='replace').read()
            if not lines:
                v = 'NO LOG'
            elif any('SOLO match started' in l for l in lines):
                v = 'IN ROUND'
            else:
                v = 'FAILED' if failed else 'not in round'
            verdict.append('inst%d %s' % (n, v))
        say('RESULT: ' + ', '.join(verdict))
        code = 0
    finally:
        for p in procs:
            if p.poll() is None:
                subprocess.run(['taskkill', '/F', '/PID', str(p.pid)], capture_output=True)
        time.sleep(2)
        if not at.restore_original(dd, say, was):
            code = 1
        os.makedirs(root, exist_ok=True)
        open(os.path.join(root, 'run.txt'), 'w').write('\n'.join(out) + '\n')
    return code


if __name__ == '__main__':
    sys.exit(main())
