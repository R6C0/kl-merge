"""Unattended loader-climb test in M01: teleport Kane to each test spot (scripts/climb_spots.json), hold W, tap E.
Needs an ANP_Loader.asi with the 'tp' hook (loader/climb.inc climb_tp_body) installed in the DD folder.
  smoke_climb.py dry|live [spot ...] [--tp=full] [--opts="warp=dm cam=0"] [--wait-min=30] [--level-s=20]
  spots: names from climb_spots.json (default: every spot without '_alt'; 'all' = every spot).
What it does:
  - takes work/GAME_LOCK ('climb-live <time>'; waits while another agent's lock is < 15 min old, polling 30 s);
  - waits while kl2.exe runs and was not started by us (W may be playing);
  - backs up <DD>/ANP_climb.txt and writes '<mode> trace=1 <opts>' (restored at the end), makes sure
    ANP_autoload.txt says 'M01 1 12' (restored too);
  - launches DD through Steam, waits for the autoload, presses Enter for 'Buffering 100%', waits for 'climb: pos:';
  - per spot: writes ANP_tp.txt (atomic rename), waits 2 s, holds W 1.2 s, taps E while holding W, keeps W 0.5 s,
    waits 5 s; ffmpeg grabs the game window at 2 fps for the whole attempt into <run>/<spot>/;
  - quits through ANP_quit.txt (taskkill only as a last resort), saves the new ANP_log.txt lines to <run>/log.txt and
    a per-spot summary to <run>/summary.json (tp / press / RESULT / START / END lines, positions before and after,
    class, pass/fail against the spot's expectation).
Output: work/smoke/climb_<MMDD_HHMMSS>/. Exit code 0 = ran (see summary), 2 = gave up waiting, 3 = game did not start."""
import ctypes, ctypes.wintypes as wt, glob, hashlib, json, math, os, re, shutil, subprocess, sys, threading, time
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(REPO, 'scripts', 'climb_spots.json')
LOCK = os.path.join(REPO, 'work', 'GAME_LOCK')
LOG = os.path.join(DD, 'ANP_log.txt'); QUIT = os.path.join(DD, 'ANP_quit.txt')
CFG = os.path.join(DD, 'ANP_climb.txt'); AUTO = os.path.join(DD, 'ANP_autoload.txt')
TP = os.path.join(DD, 'ANP_tp.txt'); TPTMP = os.path.join(DD, 'ANP_tp.tmp'); TPDONE = os.path.join(DD, 'ANP_tp.done')

args = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = dict((a[2:].split('=', 1) + [''])[:2] for a in sys.argv[1:] if a.startswith('--'))
if not args or args[0] not in ('dry', 'live'):
    print(__doc__); sys.exit(1)
MODE = args[0]
TPMODE = 'full' if flags.get('tp') == 'full' else ''
OPTS = flags.get('opts', '')
WAIT_MIN = float(flags.get('wait-min', 30))
LEVEL_S = float(flags.get('level-s', 20))
FPS = int(flags.get('fps', 2) or 2)                 # --fps=N: frame grab rate
AFTER = 'after' in flags                            # --after: after the climb, hold S 1 s (control check: steps back off the ledge) and turn the mouse
SPOTS = flags.get('spots') or SPOTS                 # --spots=<json>: another spot file
spec = json.load(open(SPOTS))
allspots = {s['name']: s for s in spec['spots']}
names = args[1:] or [n for n in allspots if not n.endswith('_alt')]
if names == ['all']:
    names = list(allspots)
bad = [n for n in names if n not in allspots]
if bad:
    print('unknown spots: %s (have %s)' % (bad, ', '.join(allspots))); sys.exit(1)

RUN = time.strftime('%m%d_%H%M%S'); OUT = os.path.join(REPO, 'work', 'smoke', 'climb_' + RUN); os.makedirs(OUT, exist_ok=True)
FF = (glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe')) or [shutil.which('ffmpeg')])[0]
u = ctypes.windll.user32; k32 = ctypes.windll.kernel32; u.SetProcessDPIAware()
t0 = time.time()


def say(s):
    line = '%7.1fs %s' % (time.time() - t0, s); print(line, flush=True)
    with open(os.path.join(OUT, 'steps.txt'), 'a') as f:
        f.write(line + '\n')


def running(exe='kl2.exe'):
    return exe in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + exe, '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout.lower()


def kl2_hwnd():
    found = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(h, _):
        pid = wt.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if u.IsWindowVisible(h):
            hp = k32.OpenProcess(0x1000, False, pid.value)
            if hp:
                b = ctypes.create_unicode_buffer(260); n = wt.DWORD(260)
                k32.QueryFullProcessImageNameW(hp, 0, b, ctypes.byref(n)); k32.CloseHandle(hp)
                if os.path.basename(b.value).lower() == 'kl2.exe':
                    found.append(h)
        return True
    u.EnumWindows(cb, 0)
    return found[0] if found else None


SC = {'enter': 0x1C, 'esc': 0x01, 'w': 0x11, 'e': 0x12, 's': 0x1F}       # DirectInput scan codes


def keydown(name):
    u.keybd_event(0, SC[name] & 0x7F, 0x0008 | (1 if SC[name] & 0x80 else 0), 0)


def keyup(name):
    u.keybd_event(0, SC[name] & 0x7F, 0x0008 | 0x0002 | (1 if SC[name] & 0x80 else 0), 0)


def key(name, hold=0.08):
    keydown(name); time.sleep(hold); keyup(name)


def front():
    h = kl2_hwnd()
    if h and u.GetForegroundWindow() != h:
        u.keybd_event(0x12, 0, 0, 0); u.SetForegroundWindow(h); u.keybd_event(0x12, 0, 2, 0); time.sleep(0.3)
    return bool(h and u.GetForegroundWindow() == h)


def grab_cmd(dur, pattern):
    """ffmpeg recording the game window at 2 fps for dur seconds -> Popen or None."""
    h = kl2_hwnd()
    if not h or not FF:
        return None
    r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
    x, y = max(r.left, 0), max(r.top, 0); w, hh = r.right - x, r.bottom - y
    if w < 320 or hh < 200:
        return None
    return subprocess.Popen([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-framerate', str(FPS),
                             '-offset_x', str(x), '-offset_y', str(y), '-video_size', '%dx%d' % (w - w % 2, hh - hh % 2),
                             '-i', 'desktop', '-t', '%.1f' % dur, '-vf', 'scale=640:-2', '-q:v', '5', pattern],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def shot(name):
    p = grab_cmd(0.6, os.path.join(OUT, name + '_%02d.jpg'))
    if p:
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()


def logsize():
    try:
        return os.path.getsize(LOG)
    except OSError:
        return 0


def logfrom(off):
    try:
        with open(LOG, 'rb') as f:
            d = f.read()
    except OSError:
        return ''
    return (d[off:] if len(d) >= off else d).decode('latin1', 'replace')


def md5(p):
    try:
        return hashlib.md5(open(p, 'rb').read()).hexdigest()
    except OSError:
        return None


# ---------------------------------------------------------------- lock and waiting
LOCKTXT = 'climb-live %s pid=%d' % (time.strftime('%Y-%m-%d %H:%M:%S'), os.getpid())
have_lock = False


def take_lock():
    global have_lock
    deadline = time.time() + WAIT_MIN * 60
    while True:
        try:
            age = time.time() - os.path.getmtime(LOCK); txt = open(LOCK).read().strip()
        except OSError:
            age, txt = None, ''
        if age is None or age >= 15 * 60 or txt == LOCKTXT:
            if age is not None and txt != LOCKTXT:
                say('GAME_LOCK is stale (%.0f min, "%s"): taking it' % (age / 60, txt))
            with open(LOCK, 'w') as f:
                f.write(LOCKTXT)
            time.sleep(0.5)
            if open(LOCK).read().strip() == LOCKTXT:
                have_lock = True; return True
        if time.time() > deadline:
            return False
        say('GAME_LOCK held: "%s" (%.0f s old) - waiting' % (txt, age or 0)); time.sleep(30)


def touch_lock():
    if have_lock:
        try:
            os.utime(LOCK, None)
        except OSError:
            pass


def drop_lock():
    try:
        if have_lock and open(LOCK).read().strip() == LOCKTXT:
            os.remove(LOCK)
    except OSError:
        pass


# ---------------------------------------------------------------- per-spot log parsing
RX = {k: re.compile(v) for k, v in dict(
    tp=r'climb: tp: (?!settled)(.*)', settled=r'climb: tp: settled (.*)', press=r'climb: press (.*)',
    ignored=r'climb: press ignored (.*)', result=r'climb: RESULT (.*)', start=r'climb: START (.*)',
    end=r'climb: END (.*)', pos=r'climb: pos: (\S+) (\S+) (\S+) (\S+)', fault=r'climb: (FAULT|DISABLED).*',
    snap=r'climb: SNAP (.*)', other=r'climb: (start failed|CreateAction|clip ).*').items()}
FEET = re.compile(r'feet=\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\)')


def first(lines, k):
    for l in lines:
        m = RX[k].search(l)
        if m:
            return l.split('] ', 1)[-1]
    return None


def summarize(spot, text):
    lines = [l for l in text.splitlines() if 'climb:' in l]
    res = first(lines, 'result')
    s = dict(name=spot['name'], expect=spot['expect'], target=spot.get('target'), tp=first(lines, 'tp'),
             settled=first(lines, 'settled'), press=first(lines, 'press') or first(lines, 'ignored'), result=res,
             start=first(lines, 'start'), end=first(lines, 'end'), snap=first(lines, 'snap'),
             faults=[l.split('] ', 1)[-1] for l in lines if RX['fault'].search(l)],
             other=[l.split('] ', 1)[-1] for l in lines if RX['other'].search(l)][:6],
             rays=[l.split('] ', 1)[-1] for l in lines if 'climb: ray ' in l or 'climb: cand ' in l][:12])
    m = re.search(r'RESULT (OK class=(\w+)|abort:([\w ]+?)|none: ([\w ]+?)) h=(-?[\d.]+)', res or '')
    s['class'] = m.group(2) if m and m.group(2) else None
    s['outcome'] = ('OK ' + m.group(2)) if m and m.group(2) else ('abort:' + m.group(3)) if m and m.group(3) else ('none:' + m.group(4)) if m and m.group(4) else None
    s['h'] = float(m.group(5)) if m else None
    pos = [tuple(float(v) for v in RX['pos'].search(l).groups()) for l in lines if RX['pos'].search(l)]
    tpf = FEET.search(s['settled'] or s['tp'] or '')
    s['pos_before'] = [float(v) for v in tpf.groups()] if tpf else (list(pos[0][:3]) if pos else None)
    y = re.search(r'yaw=(-?[\d.]+)', s['settled'] or (s['tp'] or '').split('->')[-1])
    s['yaw_before'] = float(y.group(1)) if y else None
    pr = re.search(r'P=\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\) F=\((-?[\d.]+),(-?[\d.]+)\)', s['press'] or '')
    s['pos_press'] = [float(pr.group(i)) for i in (1, 2, 3)] if pr else None
    s['yaw_press'] = round(math.degrees(math.atan2(float(pr.group(4)), float(pr.group(5)))) % 360, 1) if pr else None
    s['pos_after'] = list(pos[-1][:3]) if pos else None
    s['yaw_after'] = pos[-1][3] if pos else None
    want = [spot['x'], spot['y'], spot['z']]
    if s['pos_before']:
        s['tp_off'] = round(math.dist(s['pos_before'], want), 1)
    if s['pos_press'] and s['pos_before']:
        d = [s['pos_press'][0] - s['pos_before'][0], s['pos_press'][2] - s['pos_before'][2]]
        s['walked_cm'] = round(math.hypot(*d), 1)
        s['walk_dir'] = round(math.degrees(math.atan2(d[0], d[1])) % 360, 1) if math.hypot(*d) > 5 else None
    if s['pos_after'] and s['pos_before']:
        s['rise'] = round(s['pos_after'][1] - s['pos_before'][1], 1)
    exp = spot['expect']
    ok_dry = (s['outcome'] == 'abort:too high') if exp == 'too high' else (s['outcome'] == 'OK ' + exp)
    s['pass_probe'] = bool(ok_dry)
    if MODE == 'live' and exp != 'too high':
        endr = re.search(r'reason=(\S+)', s['end'] or '')
        s['end_reason'] = endr.group(1) if endr else None
        s['pass_live'] = bool(ok_dry and s['start'] and s['end_reason'] in ('animend', 'clip', 'clip end') and
                              s.get('rise') is not None and s['h'] and s['rise'] > 0.6 * s['h'] and not s['faults'])
    s['pass'] = s.get('pass_live', s['pass_probe']) and not s['faults']
    return s


# ---------------------------------------------------------------- main
backup = {}
started_by_us = False
summary = dict(run=RUN, mode=MODE, tp=TPMODE or '0x82cc40', opts=OPTS, spots=[], loader_installed_md5=md5(os.path.join(DD, 'ANP_Loader.asi')),
               loader_build_md5=md5(os.path.join(REPO, 'build', 'ANP_Loader.asi')))
log0 = 0
try:
    if not take_lock():
        say('GAME_LOCK still held after %.0f min - giving up' % WAIT_MIN); sys.exit(2)
    say('lock taken: %s' % LOCKTXT)
    deadline = time.time() + WAIT_MIN * 60
    while running():
        if time.time() > deadline:
            say('kl2.exe still running (not ours) after %.0f min - giving up' % WAIT_MIN); sys.exit(2)
        say('kl2.exe is running and we did not start it (W playing?) - waiting'); touch_lock(); time.sleep(30)
    if 'install' in flags:      # --install: back up the installed loader, then copy build/ANP_Loader.asi (game not running, lock held)
        inst, bld = os.path.join(DD, 'ANP_Loader.asi'), os.path.join(REPO, 'build', 'ANP_Loader.asi')
        if md5(inst) != md5(bld):
            bdir = os.path.join(REPO, 'work', 'backup', 'loader_' + time.strftime('%m%d_%H%M%S')); os.makedirs(bdir, exist_ok=True)
            if os.path.exists(inst):
                shutil.copy2(inst, os.path.join(bdir, 'ANP_Loader.asi'))
            shutil.copy2(bld, inst)
            say('installed build/ANP_Loader.asi (old one backed up to %s)' % bdir)
        else:
            say('installed loader already matches the build')
        summary['loader_installed_md5'] = md5(inst)
    for p in (CFG, AUTO):
        backup[p] = open(p, 'rb').read() if os.path.exists(p) else None
        if backup[p] is not None:
            shutil.copy2(p, os.path.join(OUT, os.path.basename(p) + '.bak'))
    with open(CFG, 'w') as f:
        f.write(('%s trace=1 %s' % (MODE, OPTS)).strip() + '\n')
    if (backup[AUTO] or b'').split()[:1] != [b'M01']:
        with open(AUTO, 'w') as f:
            f.write('M01 1 12')
    for p in (QUIT, TP, TPTMP, TPDONE):
        if os.path.exists(p):
            os.remove(p)
    say('ANP_climb.txt = "%s"; spots: %s; tp %s' % (open(CFG).read().strip(), ', '.join(names), TPMODE or '0x82cc40'))
    if summary['loader_installed_md5'] != summary['loader_build_md5']:
        say('NOTE: installed ANP_Loader.asi differs from build/ANP_Loader.asi')
    log0 = logsize()
    say('launching steam://rungameid/28000'); os.startfile('steam://rungameid/28000'); started_by_us = True
    for _ in range(90):
        if running():
            break
        time.sleep(1)
    else:
        say('kl2.exe did not start within 90 s (Steam sign-in window?)'); sys.exit(3)
    say('kl2.exe running')
    for _ in range(120):
        if 0 < logsize() < log0:
            log0 = 0                          # the loader started a fresh ANP_log.txt
        if 'autoload' in logfrom(log0).lower():
            break
        time.sleep(1)
    say('autoload seen in log' if 'autoload' in logfrom(log0).lower() else 'no autoload line after 120 s')
    time.sleep(15); touch_lock()
    for i in range(6):
        if not running():
            break
        front(); key('enter'); time.sleep(4)
    for _ in range(60):
        if 'climb: pos:' in logfrom(log0) or not running():
            break
        time.sleep(1)
    say('in level (pos lines seen)' if 'climb: pos:' in logfrom(log0) else 'NO pos lines - is trace on / the player there?')
    # since 11 Oct 12:28 M01 opens with DM's intro cutscenes (~80 s; the player is cutscene-controlled, teleports and
    # climbs are ignored). Enter is kl2's cutscene skip: tap it every 3 s for 45 s so both intro cutscenes are skipped.
    t_skip = time.time()
    while time.time() - t_skip < float(os.environ.get('CLIMB_SKIP_S', '45')) and running():
        front(); key('enter'); time.sleep(3); touch_lock()
    say('cutscene skip done')
    time.sleep(LEVEL_S / 2); shot('level')
    for n in names:
        if not running():
            say('kl2.exe is gone - stopping'); break
        touch_lock()
        sp = allspots[n]; d = os.path.join(OUT, n); os.makedirs(d, exist_ok=True)
        off = logsize()
        say('spot %s: tp to (%.1f, %.1f, %.1f) yaw %.1f, expect %s' % (n, sp['x'], sp['y'], sp['z'], sp['yaw'], sp['expect']))
        rec = grab_cmd(11.5 + (5.5 if AFTER else 0), os.path.join(d, 'f_%03d.jpg'))
        with open(TPTMP, 'w') as f:
            f.write('%.1f %.1f %.1f %.1f %s\n' % (sp['x'], sp['y'], sp['z'], sp['yaw'], TPMODE))
        os.replace(TPTMP, TP)
        for _ in range(20):
            if not os.path.exists(TP):
                break
            time.sleep(0.25)
        if os.path.exists(TP):
            say('  ANP_tp.txt not consumed in 5 s (loader without tp, game paused or not in level?) - skipping the rest')
            os.remove(TP)
            if rec:
                rec.kill()
            summary['spots'].append(summarize(sp, logfrom(off)) | {'error': 'tp not consumed'})
            break
        time.sleep(2.0)
        front(); keydown('w'); time.sleep(1.2); key('e', 0.15); time.sleep(0.5); keyup('w')
        time.sleep(5.0)
        off2 = logsize()
        if AFTER:          # control check: walk 1 s, then sweep the camera with the mouse
            front(); keydown('s'); time.sleep(1.0); keyup('s'); time.sleep(1.2)   # walk BACK: steps off the ledge the way he came
            for i in range(40):
                u.mouse_event(0x0001, 12 if i < 20 else -12, 0, 0, 0); time.sleep(0.03)
            time.sleep(1.5)
        if rec:
            try:
                rec.wait(timeout=15)
            except subprocess.TimeoutExpired:
                rec.kill()
        s = summarize(sp, logfrom(off)[:max(off2 - off, 0)]); s['frames'] = d
        if AFTER:
            pa = [tuple(float(v) for v in RX['pos'].search(l).groups()) for l in logfrom(off2).splitlines() if RX['pos'].search(l)]
            if s.get('pos_after') and len(pa) >= 2:
                s['pos_after_climb'] = list(pa[0][:3])
                s['pos_after_walk'] = list(pa[-1][:3])
                s['after_walk_cm'] = round(math.dist(pa[0][:3], pa[-1][:3]), 1)
                s['after_walk_dy'] = round(pa[-1][1] - pa[0][1], 1)
        summary['spots'].append(s)
        say('  %s: %s | %s | %s' % ('PASS' if s['pass'] else 'FAIL', s['result'], s['start'] and 'START' or '-', s['end'] or '-'))
        with open(os.path.join(OUT, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=1)
finally:
    keyup('w'); keyup('s')
    if started_by_us and running():
        with open(QUIT, 'w') as f:
            f.write('quit')
        say('ANP_quit.txt written')
        for _ in range(30):
            if not running():
                break
            time.sleep(1)
        if running():
            say('still running after 30 s: taskkill'); subprocess.run(['taskkill', '/IM', 'kl2.exe', '/F'], capture_output=True)
        time.sleep(2)
    for p in (QUIT, TP, TPTMP):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    for p, data in backup.items():
        try:
            if data is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                with open(p, 'wb') as f:
                    f.write(data)
        except OSError as e:
            say('could not restore %s: %s' % (p, e))
    if backup:
        say('ANP_climb.txt / ANP_autoload.txt restored')
    if started_by_us:
        lg = logfrom(log0)
        with open(os.path.join(OUT, 'log.txt'), 'w', encoding='utf-8') as f:
            f.write(lg)
        summary['faults'] = [l for l in lg.splitlines() if 'EXCEPTION' in l or 'climb: FAULT' in l or 'DISABLED' in l][:20]
        summary['passed'] = sum(1 for s in summary['spots'] if s.get('pass'))
        with open(os.path.join(OUT, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=1)
        say('%d/%d spots passed; faults %d' % (summary['passed'], len(summary['spots']), len(summary['faults'])))
    drop_lock()
    say('done -> %s' % OUT)
