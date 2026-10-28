#!/usr/bin/env python3
"""
Two kl2.exe on one PC: the solo bench for the online code (re/netsmooth_solo.md; hook part klhook/klsolo.c).

    python kl_solo_test.py --hook <TEST build folder> --tag <name> [--secs 300] [--gap 45]
                           [--base <KLHook.ini>] [--ini1 <extra.ini>] [--ini2 <extra.ini>] [--shots 30-300:30] [--force] [--d3shots]
                           [--n N (3+: more joiners, all with --ini2)] [--gap2 30 (between joiners)]
                           [--netstat SECS] [--relaunch K (3: a failed, hung or ended joiner is started again, before the host's round starts)]
                           [--hang-secs S (90: a joiner whose KLHook.log gains no non-watchdog line for S s is hung: its pid is killed and it is relaunched)]
                           [--owner-away (owner said they are away: no idle gate, no owner abort; the park stays)]
                           [--park 1 (hold the Windows cursor at 0,0 until the host's round starts: a hovered menu row moves the selection)]

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
    for key in ('--hook', '--tag', '--secs', '--gap', '--gap2', '--base', '--ini1', '--ini2', '--shots', '--n', '--netstat', '--relaunch', '--hang-secs', '--park'):
        if key in a:
            i = a.index(key); opt[key] = a[i + 1]; del a[i:i + 2]
    force = '--force' in a
    # 10-28: the GDI desktop grab (at.shot) returned all-zero PNGs all week (monitor off / session locked). --d3shots takes the shots
    # inside the game instead: the hook's kld3 back-buffer shot ([Memory] D3dShot*), KLShot_inst<N>_NN.jpg in the run folder.
    d3shots = '--d3shots' in a
    # 10-28: the owner said 'i didnt use the pc at all' about A1HIRE's 23:03 abort (cursor 1493,445, idle 0 s). With their
    # word that they are away, --owner-away skips the idle gate and the park loop's owner abort (it still parks the cursor).
    away = '--owner-away' in a
    force = force or away
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
        if d3shots and shots:
            # kld3 arms at the first call after From and shoots one interval later, so From = first shot - step (GUESS: Present runs every frame)
            step = (shots[1] - shots[0]) if len(shots) > 1 else 30
            # the shots run inside klfps's Present wrappers: they need [FrameLimit] Enable=1 SwapChain=1 (re/open_work_log.md, 10-26)
            # JPG (Fmt 0), not PNG: the X8R8G8B8 back buffer saves as PNG with alpha 0, which viewers show as a white page (A1LIFT3e 10-28)
            secs_n = merge(secs_n, [('Memory', [('D3dShotEvery', str(max(1, step))), ('D3dShotFrom', str(max(0, shots[0] - step))),
                                                 ('D3dShotMax', str(len(shots))), ('D3dShotFmt', '0'), ('D3dShotDir', root), ('D3dShotTag', 'inst%d' % n)]),
                                    ('FrameLimit', [('Enable', '1'), ('SwapChain', '1')])])
        extra = opt.get('--ini%d' % min(n, 2))
        if extra:
            secs_n = merge(secs_n, read_ini(extra))
        write_ini(os.path.join(d, 'KLHook.ini'), secs_n)
        inst.append(d)
    say('  inis | %d written under %s' % (total, root))      # L9e stopped after the firewall line: this places the next stall
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
        park_on = opt.get('--park', '1') != '0'
        owner = ['']                                         # set by park_loop when the owner's mouse is seen: the run ends

        def park_loop():
            # 10-27 Q27_DM01/DD04: the Windows cursor resting at 320,240 hovered a MainMenu row, so 'tap DOWN' x2 landed on
            # ShowAchievements; DM01H (uncapped, cursor held at 0,0) reached OnlineMenu. Hold it in the windows' top-left
            # corner while the menus are driven (until the host's round starts).
            k, moved = 0, [0]
            while time.time() - t0 < secs:
                k += 1
                if k % 10 == 0:                                  # every 5 s: has the host's round started? (host_started is defined below)
                    try:
                        txt = open(os.path.join(inst[0], 'KLHook.log'), encoding='latin-1').read()
                        if 'SOLO match started' in txt or 'host Ready with' in txt:
                            return
                    except OSError:
                        pass
                # 17:25 Q27_DM06 failed the same way with an 'idle >= 30' gate: the cursor was back at 320,240 (640x480
                # screen centre: a display-mode change re-centres it) and idle had been reset (17:24:56, cause unknown), so
                # the park stood down. Now a cursor at a RESET point (re-centred by a display-mode change or by the game:
                # screen centres, the bench windows' centres) is parked again; anywhere else, or a mouse button down, is
                # the owner's hand (ce 17:30): stop parking and end the bench so the queue frees the lock.
                pt = (ctypes.c_long * 2)()
                ctypes.windll.user32.GetCursorPos(pt)
                sw, sh = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
                reset = {(0, 0), (320, 240), (sw // 2, sh // 2), (480, 270), (1440, 270), (960, 0)}
                btn = any(ctypes.windll.user32.GetAsyncKeyState(v) & 0x8000 for v in (1, 2, 4))
                # Q27_DD09 17:33: the game put the cursor at 960,0 (inst2's window corner) with idle 72 s - a false abort.
                # Game-made moves do not reset idle; a hand does. Off a reset point counts only with input in the last 3 s.
                if not away and k > 1 and (btn or ((pt[0], pt[1]) not in reset and idle_s() < 3)):   # k == 1: where it rested before the bench
                    owner[0] = 'cursor at %d,%d%s (idle %d s)' % (pt[0], pt[1], ', mouse button down' if btn else '', idle_s())
                    say('  park | +%.1f s owner input: %s - bench ended, nothing parked' % (time.time() - t0, owner[0]))
                    return
                if (pt[0], pt[1]) != (0, 0):
                    if moved[0] < 20:
                        say('  park | +%.1f s cursor was at %d,%d (idle %d s): moved back to 0,0' % (time.time() - t0, pt[0], pt[1], idle_s()))
                    moved[0] += 1
                    ctypes.windll.user32.SetCursorPos(0, 0)
                time.sleep(0.5)
        if park_on:
            import threading
            threading.Thread(target=park_loop, daemon=True).start()
            say('  park | cursor held at 0,0 until the host round starts (--park 0: off)')
        for n, d in enumerate(inst, 1):
            if n >= 2:                                     # joiner k starts at gap + (k-2) * gap2 (--gap2, default 30 s): one at a time through the menus
                while time.time() - t0 < gap + (n - 2) * int(opt.get('--gap2', 30)) and not owner[0]:
                    time.sleep(1)
                    netstat_tick(t0)
            if owner[0]:
                break
            env = dict(os.environ, SteamAppId='28000', SteamGameId='28000', KLHOOK_DIR=d)
            p = subprocess.Popen([os.path.join(dd, 'kl2.exe'), '-o', 'DisableSplashScreens'], cwd=dd, env=env)
            procs.append(p)
            say('  start | inst%d pid %d at %+.0f s (%s)' % (n, p.pid, time.time() - t0, d))
        retries = {n: int(opt.get('--relaunch', 3)) for n in range(2, len(inst) + 1)}
        tries = {n: 1 for n in range(1, len(inst) + 1)}          # tries used per instance (1 = first start)
        hang_secs = int(opt.get('--hang-secs', 90))
        last_start = [time.time()]
        prog = {}                                                # n -> (signature of frames/ms/script, time it last changed)
        skipped = set()

        def host_started():
            log = os.path.join(inst[0], 'KLHook.log')
            try:
                txt = open(log, encoding='latin-1').read()
                return 'SOLO match started' in txt or 'host Ready with' in txt
            except OSError:
                return False

        def read_res(d):
            try:
                return ' '.join(open(os.path.join(d, 'KLHook.result'), errors='replace').read().split())
            except OSError:
                return ''

        def save_try(n, k):
            # keep this try's log / result as KLHook.try<k>.log / .result (a copy: the live files stay for the final report)
            d = inst[n - 1]
            for f, g in (('KLHook.log', 'KLHook.try%d.log' % k), ('KLHook.result', 'KLHook.try%d.result' % k)):
                if os.path.isfile(os.path.join(d, f)):
                    shutil.copyfile(os.path.join(d, f), os.path.join(d, g))

        QUIET = ('stall', 'nudge', 'poll gap')               # watchdog lines the hook writes even when the game is frozen

        def hung_for(n, now):
            # seconds the instance's KLHook.log has gained no line besides the watchdog's own (stall / nudge / poll gap).
            # NOT KLHook.result: the hook rewrites it only at start / load / end, so a healthy joiner waiting in the lobby
            # keeps the same frames= ms= script= for many minutes (N9_DM01 inst3 looked 'hung' that way yet reached the
            # lobby). A log that does not exist yet counts as no progress (the hook never loaded).
            try:
                with open(os.path.join(inst[n - 1], 'KLHook.log'), encoding='latin-1', errors='replace') as fh:
                    sig = sum(1 for l in fh if not any(q in l for q in QUIET))
            except OSError:
                sig = -1
            if n not in prog or prog[n][0] != sig:
                prog[n] = (sig, now); return 0
            return now - prog[n][1]

        def relaunch_tick():
            # --relaunch K (default 3): a joiner whose script FAILED, whose log shows no progress for --hang-secs, or whose
            # process ended before the host started the round is started again (its log kept as KLHook.try<k>.log /
            # .result), one at a time, at least 20 s apart. Once the host is in the round nobody is started again
            # (joining a running FA round is not possible: N9_DM01 inst4 lost 4 tries on that).
            now = time.time()
            if procs[0].poll() is not None and not host_started():
                # host (inst1) died before the round: no relaunch can join a dead session (N9_DM01d spent 3 tries per joiner after it died)
                if not getattr(relaunch_tick, 'told', 0):
                    relaunch_tick.told = time.time()
                    say('  relaunch | host (inst1) has ended: no relaunch can join a dead session; run over')
                return
            why = {}
            started = host_started()
            for n in range(2, len(procs) + 1):
                p = procs[n - 1]
                txt = read_res(inst[n - 1])
                hung = hung_for(n, now) if p.poll() is None and not started else 0
                if 'state=FAIL' in txt:
                    why[n] = 'its script failed: ' + txt[:200]
                elif p.poll() is not None:
                    why[n] = 'the process had ended'
                elif hung >= hang_secs:
                    why[n] = 'hung: frames %s unchanged %d s, no log progress' % ((re.search(r'frames=(\S+)', txt) or [0, '?'])[1], hung)
            if not why:
                return
            if started:
                for n in why:
                    if retries[n] > 0 and n not in skipped:
                        skipped.add(n)
                        say('  relaunch | inst%d skipped: host already in round, joining a running FA round is not possible' % n)
                return
            if now - last_start[0] < 20:
                return
            for n, reason in why.items():
                if retries[n] <= 0:
                    continue
                d, p = inst[n - 1], procs[n - 1]
                if p.poll() is None:
                    subprocess.run(['taskkill', '/F', '/PID', str(p.pid)], capture_output=True); time.sleep(2)
                k = tries[n]; retries[n] -= 1; tries[n] += 1
                save_try(n, k)
                for f in ('KLHook.log', 'KLHook.result'):
                    if os.path.isfile(os.path.join(d, f)):
                        os.replace(os.path.join(d, f), os.path.join(d, 'KLHook_try%d%s' % (k, os.path.splitext(f)[1])))
                prog.pop(n, None)
                env = dict(os.environ, SteamAppId='28000', SteamGameId='28000', KLHOOK_DIR=d)
                procs[n - 1] = subprocess.Popen([os.path.join(dd, 'kl2.exe'), '-o', 'DisableSplashScreens'], cwd=dd, env=env)
                last_start[0] = time.time()
                say('  relaunch | inst%d try %d pid %d at %+.0f s (%s) tries=%d' % (n, k + 1, procs[n - 1].pid, time.time() - t0, reason, tries[n]))
                return
        while time.time() - t0 < secs:
            time.sleep(2)
            el = time.time() - t0
            netstat_tick(t0)
            relaunch_tick()
            if getattr(relaunch_tick, 'told', 0) and time.time() - relaunch_tick.told > 30:
                break  # host dead + 30 s grace: free the live slot for the next queue item
            if owner[0]:
                break  # the owner moved the mouse during the menus: end now, the queue frees the lock
            if shots and el >= shots[0] and d3shots:
                shots.pop(0)                         # the hook takes it (KLShot_*), nothing to do here
            elif shots and el >= shots[0]:
                s = shots.pop(0)
                for n, p in enumerate(procs, 1):
                    if p.poll() is None:
                        path = os.path.join(root, 'shot_inst%d_%03ds.png' % (n, s))
                        r = at.shot([p.pid], path)
                        say('  shot | inst%d %ds %s' % (n, s, (path if r != 'black' else 'ALL BLACK (monitor off? use --d3shots): ' + path) if r else 'no window'))
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
            say('  inst%d | exit code %s, %d log lines, tries=%d' % (n, procs[n - 1].returncode if n <= len(procs) else '-', len(lines), tries[n]))
            if tries[n] > 1:                         # every try's reason survives: copy the last one, then list all
                save_try(n, tries[n])
                for k in range(1, tries[n] + 1):
                    say('    try %d | %s' % (k, (read_res(d) if k == tries[n] else
                        ' '.join(open(os.path.join(d, 'KLHook_try%d.result' % k), errors='replace').read().split()) if os.path.isfile(os.path.join(d, 'KLHook_try%d.result' % k)) else 'no result')[:300]))
            for l in [l for l in lines if any(k in l for k in KEEP)][-40:]:
                say('    log | ' + l[:220])
            if d3shots:
                got = sorted(f for f in os.listdir(root) if f.startswith('KLShot_inst%d_' % n))
                bad = [f for f in got if os.path.getsize(os.path.join(root, f)) < 2000]
                say('    d3shots | inst%d %d KLShot files%s%s' % (n, len(got), (', %d under 2 KB (blank?): %s' % (len(bad), bad[:3])) if bad else '',
                    '' if got else ' - NONE: is [FrameLimit] SwapChain on and the TEST dll the one loaded? see the d3count: lines in KLHook.log'))
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
        say('RESULT: ' + ', '.join(verdict) + (' (ABORTED: owner input during the menus, %s - rerun it)' % owner[0] if owner[0] else ''))
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
