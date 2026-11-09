"""Unattended sound test (copy of smoke_m01.py): loads the autoload level, records the default speaker's output
through WASAPI loopback (soundcard) from launch to quit, and writes audio.wav plus rms.csv (dBFS per second) to
work/smoke/<run>_<tag>/. No pause menu or climb presses: the level just runs.
Rules: refuses to start if kl2.exe already runs; always removes ANP_quit.txt; kills kl2.exe only as a last resort.
usage: smoke_sound.py [seconds_in_level=90] [tag=snd]"""
import ctypes, ctypes.wintypes as wt, os, sys, time, subprocess, glob, threading, wave, math
import numpy as np, soundcard as scd
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = sys.argv[2] if len(sys.argv) > 2 else 'snd'
RUN = time.strftime('%m%d_%H%M%S') + '_' + TAG; OUT = os.path.join(REPO, 'work', 'smoke', RUN); os.makedirs(OUT, exist_ok=True)
SR = 48000
def recorder():
    """loopback of the default speaker, 1 s blocks until stop; WAV int16 stereo + per-second RMS"""
    mic = scd.get_microphone(id=str(scd.default_speaker().name), include_loopback=True)
    w = wave.open(os.path.join(OUT, 'audio.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    # nonfinite = NaN/Inf samples in that second (counted separately: they used to be logged as -180 dB / written as 0)
    csv = open(os.path.join(OUT, 'rms.csv'), 'w'); csv.write('t_s,rms_dbfs,peak_dbfs,nonfinite\n')
    with mic.recorder(samplerate=SR, channels=2) as r:
        while not stop.is_set():
            d = r.record(numframes=SR); ts = time.time() - t0
            bad = int(d.size - np.isfinite(d).sum()) if d.size else 0
            if bad: d = np.nan_to_num(d, nan=0.0, posinf=1.0, neginf=-1.0)
            w.writeframes((np.clip(d, -1, 1) * 32767).astype('<i2').tobytes())
            rms = float(np.sqrt(np.mean(d ** 2))) if d.size else 0.0; pk = float(np.max(np.abs(d))) if d.size else 0.0
            db = lambda v: 20 * math.log10(v) if v > 1e-9 else -180.0
            csv.write('%.1f,%.1f,%.1f,%d\n' % (ts, db(rms), db(pk), bad)); csv.flush()
    w.close(); csv.close()
FF = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))[0]
LOG = os.path.join(DD, 'ANP_log.txt'); QUIT = os.path.join(DD, 'ANP_quit.txt')
inlevel = float(sys.argv[1]) if len(sys.argv) > 1 else 90
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
rec = threading.Thread(target=recorder, daemon=True); rec.start()
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
    for _ in range(int(inlevel)):
        if not running(): say('kl2.exe gone while in level'); break
        time.sleep(1)
finally:
    if running():
        open(QUIT, 'w').write('quit'); say('ANP_quit.txt written')
        for _ in range(30):
            if not running(): break
            time.sleep(1)
        if running(): say('still running after 30 s: taskkill'); subprocess.run(['taskkill', '/IM', 'kl2.exe', '/F'], capture_output=True)
    time.sleep(2)
    if os.path.exists(QUIT): os.remove(QUIT); say('ANP_quit.txt removed')
    stop.set(); g.join(timeout=25); rec.join(timeout=5)
    lg = newlog(); open(os.path.join(OUT, 'log.txt'), 'w', encoding='utf-8').write(lg)
    for pat in ['EXCEPTION', 'guard', 'climb', 'frame hook', 'autoload', 'watchdog']:
        hits = [l for l in lg.splitlines() if pat.lower() in l.lower()]
        say('log %-10s %3d  %s' % (pat, len(hits), (hits[-1][:160] if hits else '')))
    say('done -> %s' % OUT)
