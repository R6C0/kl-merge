"""Shared helpers for the unattended campaign smoke tests (smoke_menu.py, smoke_saves.py).

Game-side rules (as the other smoke scripts): never start while kl2.exe runs; take work/GAME_LOCK (owner text
'campaigns ...', waits while someone else's lock is younger than 15 min); quit through ANP_quit.txt, taskkill only as
a last resort; every file put into the Dog Days folder is removed or restored afterwards."""
import ctypes, ctypes.wintypes as wt, glob, hashlib, os, re, shutil, subprocess, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import anp_paths

REPO = anp_paths.REPO
DD = anp_paths.game_dir('ANP_DD_GAME', anp_paths.DD_FOLDER)
LOG = os.path.join(DD, 'ANP_log.txt')
LOCK = os.path.join(anp_paths.WORK, 'GAME_LOCK')
DOCS_SAVE = os.path.join(os.path.expanduser('~'), 'Documents', 'Square Enix', 'Kane & Lynch 2 - Dog Days')
APPDATA = os.path.join(os.environ.get('LOCALAPPDATA', os.path.join(DD, 'ANP', 'appdata')), 'A Newer Perspective')
HOOKS = ['ANP_quit.txt', 'ANP_load.txt', 'ANP_endlevel.txt', 'ANP_cstate.txt', 'ANP_guinames.txt', 'ANP_gui.txt',
         'ANP_shot.txt', 'ANP_nodes.txt', 'ANP_where.txt']
FF = (glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))
      or [shutil.which('ffmpeg')])[0]
u = ctypes.windll.user32; k32 = ctypes.windll.kernel32; u.SetProcessDPIAware()
SC = {'enter': 0x1C, 'esc': 0x01, 'up': 0xC8, 'down': 0xD0, 'left': 0xCB, 'right': 0xCD}   # DirectInput scan codes


class Run:
    def __init__(self, tag):
        self.id = time.strftime('%m%d_%H%M%S')
        self.out = os.path.join(anp_paths.WORK, 'smoke', '%s_%s' % (tag, self.id)); os.makedirs(self.out, exist_ok=True)
        self.t0 = time.time(); self.have_lock = False; self.lock_txt = 'campaigns %s %s pid=%d' % (tag, time.strftime('%Y-%m-%d %H:%M:%S'), os.getpid())
        self.log0 = 0; self.head0 = b''; self.moved = []

    def say(self, s):
        line = '%7.1fs %s' % (time.time() - self.t0, s); print(line, flush=True)
        with open(os.path.join(self.out, 'steps.txt'), 'a', encoding='utf-8') as f: f.write(line + '\n')

    # ---------------------------------------------------------------- lock
    def take_lock(self, wait_min=30):
        deadline = time.time() + wait_min * 60
        while True:
            try: age = time.time() - os.path.getmtime(LOCK); txt = open(LOCK).read().strip()
            except OSError: age, txt = None, ''
            if age is None or age >= 15 * 60 or txt == self.lock_txt:
                if age is not None and txt != self.lock_txt: self.say('GAME_LOCK is stale (%.0f min, "%s"): taking it' % (age / 60, txt))
                with open(LOCK, 'w') as f: f.write(self.lock_txt)
                time.sleep(0.5)
                if open(LOCK).read().strip() == self.lock_txt: self.have_lock = True; return True
            if time.time() > deadline: return False
            self.say('GAME_LOCK held: "%s" (%.0f s old) - waiting' % (txt, age or 0)); time.sleep(30)

    def touch_lock(self):
        if self.have_lock:
            try: os.utime(LOCK, None)
            except OSError: pass

    def release_lock(self):
        try:
            if self.have_lock and open(LOCK).read().strip() == self.lock_txt: os.remove(LOCK)
        except OSError: pass
        self.have_lock = False

    # ---------------------------------------------------------------- files in the game folder
    def move_aside(self, name):
        """rename <DD>/name to name.smoke_<run> for the run (restored by restore_moved)"""
        p = os.path.join(DD, name)
        if os.path.exists(p):
            q = p + '.smoke_' + self.id; os.replace(p, q); self.moved.append((q, p)); self.say('moved aside: %s' % name)

    def restore_moved(self):
        for q, p in reversed(self.moved):
            try:
                if os.path.exists(p): os.remove(p)
                os.replace(q, p); self.say('restored: %s' % os.path.basename(p))
            except OSError as e: self.say('could not restore %s: %s' % (p, e))
        self.moved = []

    def clear_hooks(self):
        for h in HOOKS:
            p = os.path.join(DD, h)
            if os.path.exists(p):
                try: os.remove(p)
                except OSError: pass

    def hook(self, name, text=''):
        with open(os.path.join(DD, name), 'w') as f: f.write(text)
        self.say('%s = %s' % (name, text or '(empty)'))

    # ---------------------------------------------------------------- game process
    def running(self, exe='kl2.exe'):
        return exe in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + exe, '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout.lower()

    def mark_log(self):
        self.log0 = os.path.getsize(LOG) if os.path.exists(LOG) else 0
        self.head0 = open(LOG, 'rb').read(256) if self.log0 else b''

    def log(self):
        """this session's ANP_log.txt text (the loader starts a fresh log at every launch)"""
        try: d = open(LOG, 'rb').read()
        except OSError: return ''
        fresh = len(d) < self.log0 or d[:len(self.head0)] != self.head0
        return (d if fresh else d[self.log0:]).decode('latin1', 'replace')

    def launch(self):
        self.mark_log()
        self.say('launching steam://rungameid/28000'); os.startfile('steam://rungameid/28000')
        for _ in range(90):
            if self.running(): break
            time.sleep(1)
        else:
            self.say('kl2.exe did not start within 90 s (Steam sign-in window?)'); return False
        self.say('kl2.exe running')
        return True

    def quit(self):
        if self.running():
            self.hook('ANP_quit.txt', 'quit')
            for _ in range(30):
                if not self.running(): break
                time.sleep(1)
            if self.running(): self.say('still running after 30 s: taskkill'); subprocess.run(['taskkill', '/IM', 'kl2.exe', '/F'], capture_output=True)
        time.sleep(2)
        self.clear_hooks()

    def wait_for(self, pred, timeout, step=1.0):
        end = time.time() + timeout
        while time.time() < end:
            v = pred()
            if v: return v
            if not self.running(): return None
            self.touch_lock(); time.sleep(step)
        return pred()

    def wait_log(self, pattern, timeout, since=0):
        rx = re.compile(pattern, re.I)
        def f():
            m = rx.search(self.log()[since:])
            return m.group(0) if m else None
        return self.wait_for(f, timeout)

    # ---------------------------------------------------------------- input, pictures
    def hwnd(self):
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
        u.EnumWindows(cb, 0)
        return found[0] if found else None

    def front(self):
        h = self.hwnd()
        if h and u.GetForegroundWindow() != h:
            u.keybd_event(0x12, 0, 0, 0); u.SetForegroundWindow(h); u.keybd_event(0x12, 0, 2, 0); time.sleep(0.3)
        return bool(h and u.GetForegroundWindow() == h)

    def park_mouse(self):
        """cursor to the window's top-right corner, away from every menu row (mouse focus would move the highlight)"""
        h = self.hwnd()
        if h:
            r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r)); u.SetCursorPos(r.right - 8, r.top + 40)

    def click(self, fx, fy, gap=1.0):
        """left click at a fraction (fx, fy) of the game window's client area (hover first so mouse focus moves)"""
        self.front(); h = self.hwnd()
        if not h: return False
        r = wt.RECT(); u.GetClientRect(h, ctypes.byref(r))
        p = wt.POINT(int(r.right * fx), int(r.bottom * fy)); u.ClientToScreen(h, ctypes.byref(p))
        u.SetCursorPos(p.x, p.y); time.sleep(0.4)
        u.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.08); u.mouse_event(0x0004, 0, 0, 0, 0)
        self.say('click (%.3f, %.3f) -> screen (%d, %d)' % (fx, fy, p.x, p.y)); time.sleep(gap)
        return True

    def key(self, name, hold=0.08, gap=0.9):
        self.front()
        sc = SC[name]; ext = 1 if sc & 0x80 else 0; sc &= 0x7F
        flags = 0x0008 | (0x0001 if ext else 0)
        u.keybd_event(0, sc, flags, 0); time.sleep(hold); u.keybd_event(0, sc, flags | 0x0002, 0)
        self.say('key %s' % name); time.sleep(gap)

    def shot(self, name):
        h = self.hwnd()
        if not h or not FF: self.say('screenshot %s: no window' % name); return None
        r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
        x, y = max(r.left, 0), max(r.top, 0); w, hh = r.right - x, r.bottom - y
        if w < 320 or hh < 200: return None
        fn = os.path.join(self.out, name + '.jpg')
        subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-offset_x', str(x), '-offset_y', str(y),
                        '-video_size', '%dx%d' % (w - w % 2, hh - hh % 2), '-i', 'desktop', '-frames:v', '1', '-vf', 'scale=960:-2',
                        '-q:v', '4', fn], capture_output=True, timeout=20)
        ok = os.path.exists(fn); self.say('screenshot %s %s' % (os.path.basename(fn), 'ok' if ok else 'FAILED'))
        return fn if ok else None

    def save_log(self):
        lg = self.log()
        with open(os.path.join(self.out, 'log.txt'), 'w', encoding='utf-8') as f: f.write(lg)
        return lg


def sha1(p):
    try:
        with open(p, 'rb') as f: return hashlib.sha1(f.read()).hexdigest().upper()
    except OSError: return None


def lines(text, *pats):
    rx = re.compile('|'.join(pats), re.I)
    return [l for l in text.splitlines() if rx.search(l)]


def preflight(r, need_menu=True):
    """common checks before a campaign smoke run; returns a list of problems"""
    bad = []
    if r.running(): bad.append('kl2.exe already running - W may be playing; not touching anything')
    if not os.path.exists(os.path.join(DD, 'ANP_Loader.asi')): bad.append('ANP_Loader.asi is not installed in the Dog Days folder')
    if need_menu and not os.path.exists(os.path.join(DD, 'ANP', 'ANP_Patch01.zip')):
        bad.append(r'<DD>\ANP\ANP_Patch01.zip missing: run tools\anp_menu.py and copy work\out_menu\ANP\ANP_Patch01.zip there')
    return bad
