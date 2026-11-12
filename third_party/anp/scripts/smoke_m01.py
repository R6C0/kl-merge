"""Unattended M01 smoke test through ANP_Loader's autoload (no test hook needed).
Launches DD via Steam, waits for kl2.exe, presses Enter for 'Buffering 100%', then: pause menu + highlight moves
(the 11 Oct settings crash), one dry W+E climb press, and quits through ANP_quit.txt. Frames every 2 s go to
work/smoke/<run>/, the new ANP_log.txt lines to work/smoke/<run>/log.txt.
Rules: refuses to start if kl2.exe already runs; always removes ANP_quit.txt; kills kl2.exe only as a last resort.
usage: smoke_m01.py [seconds_in_level=60]"""
import ctypes, ctypes.wintypes as wt, os, sys, time, subprocess, glob, threading
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = time.strftime('%m%d_%H%M%S'); OUT = os.path.join(REPO, 'work', 'smoke', RUN); os.makedirs(OUT, exist_ok=True)
FF = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))[0]
LOG = os.path.join(DD, 'ANP_log.txt'); QUIT = os.path.join(DD, 'ANP_quit.txt')
inlevel = float(sys.argv[1]) if len(sys.argv) > 1 else 60
u = ctypes.windll.user32; k32 = ctypes.windll.kernel32; u.SetProcessDPIAware()
t0 = time.time()
def say(s):
    line = '%7.1fs %s' % (time.time() - t0, s); print(line, flush=True)
    open(os.path.join(OUT, 'steps.txt'), 'a').write(line + '\n')
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
                if os.path.basename(b.value).lower() == 'kl2.exe': found.append(h)
        return True
    u.EnumWindows(cb, 0); return found[0] if found else None
SC = {'enter': 0x1C, 'esc': 0x01, 'up': 0xC8, 'down': 0xD0, 'w': 0x11, 'e': 0x12}   # DirectInput scan codes (0xE0 xx = extended)
def key(name, hold=0.08):
    sc = SC[name]; ext = 1 if sc & 0x80 else 0; sc &= 0x7F
    flags = 0x0008 | (0x0001 if ext else 0)          # KEYEVENTF_SCANCODE | EXTENDEDKEY
    u.keybd_event(0, sc, flags, 0); time.sleep(hold); u.keybd_event(0, sc, flags | 0x0002, 0)
def keydown(name):
    sc = SC[name]; u.keybd_event(0, sc & 0x7F, 0x0008 | (1 if sc & 0x80 else 0), 0)
def keyup(name):
    sc = SC[name]; u.keybd_event(0, sc & 0x7F, 0x0008 | 0x0002 | (1 if sc & 0x80 else 0), 0)
def front():
    h = kl2_hwnd()
    if h and u.GetForegroundWindow() != h:
        u.keybd_event(0x12, 0, 0, 0); u.SetForegroundWindow(h); u.keybd_event(0x12, 0, 2, 0); time.sleep(0.3)
    return h and u.GetForegroundWindow() == h
stop = threading.Event()
def grabber():
    n = 0
    while not stop.is_set():
        h = kl2_hwnd()
        if h:
            r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
            x, y = max(r.left, 0), max(r.top, 0); w, hh = r.right - x, r.bottom - y
            if w >= 320 and hh >= 200:
                subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-offset_x', str(x), '-offset_y', str(y),
                                '-video_size', '%dx%d' % (w - w % 2, hh - hh % 2), '-i', 'desktop', '-frames:v', '1', '-vf', 'scale=640:-2',
                                '-q:v', '5', os.path.join(OUT, '%04d_%05.1fs.jpg' % (n, time.time() - t0))], capture_output=True, timeout=20)
                n += 1
        stop.wait(2.0)
def newlog():
    try:
        d = open(LOG, 'rb').read()
        # the loader may start a fresh log on launch: if the first bytes changed, the whole file is new
        fresh = len(d) < log0 or d[:len(head0)] != head0
        return d.decode('latin1', 'replace') if fresh else d[log0:].decode('latin1', 'replace')
    except OSError: return ''
if running('kl2.exe'): print('kl2.exe already running - W may be playing; not touching anything'); sys.exit(2)
if os.path.exists(QUIT): os.remove(QUIT)
log0 = os.path.getsize(LOG) if os.path.exists(LOG) else 0
head0 = open(LOG, 'rb').read(256) if log0 else b''
g = threading.Thread(target=grabber, daemon=True); g.start()
try:
    say('launching steam://rungameid/28000'); os.startfile('steam://rungameid/28000')
    for _ in range(90):
        if running(): break
        time.sleep(1)
    else:
        say('kl2.exe did not start within 90 s (Steam sign-in window?)'); sys.exit(3)
    say('kl2.exe running')
    # wait for the level: autoload line then a quiet period; press Enter for 'Buffering 100%'
    for _ in range(120):
        if 'autoload' in newlog().lower(): break
        time.sleep(1)
    say('autoload seen in log' if 'autoload' in newlog().lower() else 'no autoload line after 120 s')
    time.sleep(15)
    for i in range(6):
        if not running(): break
        front(); key('enter'); time.sleep(4)
    say('Enter presses done; in level for %.0f s' % inlevel)
    time.sleep(inlevel / 2)
    if running():
        say('pause menu + highlight moves'); front(); key('esc'); time.sleep(2.5)
        for k_ in ['down', 'down', 'down', 'up', 'down', 'up', 'up']: key(k_); time.sleep(0.7)
        time.sleep(2); key('esc'); time.sleep(2)
        say('still running after menu test: %s' % running())
    if running():
        say('dry climb press: hold W, tap E'); front(); keydown('w'); time.sleep(1.2); key('e', 0.15); time.sleep(0.6); keyup('w')
        time.sleep(inlevel / 2)
finally:
    if running():
        open(QUIT, 'w').write('quit'); say('ANP_quit.txt written')
        for _ in range(30):
            if not running(): break
            time.sleep(1)
        if running(): say('still running after 30 s: taskkill'); subprocess.run(['taskkill', '/IM', 'kl2.exe', '/F'], capture_output=True)
    time.sleep(2)
    if os.path.exists(QUIT): os.remove(QUIT); say('ANP_quit.txt removed')
    stop.set(); g.join(timeout=25)
    lg = newlog(); open(os.path.join(OUT, 'log.txt'), 'w', encoding='utf-8').write(lg)
    for pat in ['EXCEPTION', 'guard', 'climb', 'frame hook', 'autoload', 'watchdog']:
        hits = [l for l in lg.splitlines() if pat.lower() in l.lower()]
        say('log %-10s %3d  %s' % (pat, len(hits), (hits[-1][:160] if hits else '')))
    say('done -> %s' % OUT)
