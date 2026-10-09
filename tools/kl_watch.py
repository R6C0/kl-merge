#!/usr/bin/env python3
"""
Watch the owner play: pictures of the game's own window while kl2.exe runs, taken with ffmpeg.

    python kl_watch.py [seconds between pictures, default 5] [hours to keep watching, default 6]

Passive: it never starts or ends the game, sends no input and touches nothing in the game folder.
Only the screen under the game's own window is grabbed, and only while that window is in front
(ffmpeg gdigrab on that rectangle); never the rest of the desktop, a camera or a microphone. Each run of the game gets a folder
    <work>/research/watch/<date>_<time>/NNNN_<seconds since the start>s.jpg
together with a copy of the KLHook.log lines written during that run (watch.log), so that a
picture can be matched to what the hook logged at that moment. Pictures are 1280 wide JPEGs.
ASSUMPTION: gdigrab sees the game's picture; in exclusive full screen it may return black frames
(kl_autotest.shot has the same limit and retries). Black frames are dropped by size.
"""
import ctypes, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, workdir, DD_GUESSES, DD_EXE

user32 = ctypes.windll.user32
HWND = ctypes.c_void_p                # 64-bit Python: a window handle does not fit the default int
user32.IsWindowVisible.argtypes = [HWND]
user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(ctypes.c_ulong)]
user32.GetWindowTextW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetForegroundWindow.restype = HWND
user32.SetProcessDPIAware()
SMALL = 12000                         # bytes: a 1280-wide JPEG of a black frame is smaller


def game_window():
    """(hwnd, title) of kl2.exe's visible top-level window, or None."""
    found = []
    pid = ctypes.c_ulong()

    def each(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            buf = ctypes.create_unicode_buffer(260)
            user32.GetWindowTextW(hwnd, buf, 260)
            if buf.value.startswith('Kane & Lynch 2'):
                found.append((hwnd, buf.value))
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(each), 0)
    return found[0] if found else None


def grab(hwnd, path):
    """One picture of the screen under the game's window, only while that window is the
    foreground one (so nothing else of the desktop can end up in a picture). ffmpeg's
    'title=' grab returned nothing for the game on 2026-10-09 (full screen), the screen region
    is what kl_autotest.shot reads too."""
    import ctypes.wintypes as wt
    if user32.GetForegroundWindow() != hwnd:
        return False
    r = wt.RECT()
    user32.GetWindowRect(HWND(hwnd), ctypes.byref(r))
    x, y, cx, cy = max(r.left, 0), max(r.top, 0), r.right - max(r.left, 0), r.bottom - max(r.top, 0)
    if cx < 320 or cy < 200:
        return False
    q = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-framerate', '1',
                        '-offset_x', str(x), '-offset_y', str(y), '-video_size', '%dx%d' % (cx - cx % 2, cy - cy % 2),
                        '-i', 'desktop', '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '4', path],
                       capture_output=True, text=True, timeout=30)
    return q.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > SMALL


def main():
    every = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    until = time.time() + 3600 * (float(sys.argv[2]) if len(sys.argv) > 2 else 6.0)
    dd = find(DD_GUESSES, DD_EXE)
    log = os.path.join(dd, 'KLHook.log')
    root = os.path.join(workdir(), 'research', 'watch')
    run = None
    while time.time() < until:
        w = game_window()
        if not w:
            if run:
                print('game window gone: %d pictures in %s' % (run['n'], run['dir']), flush=True)
                run = None
            time.sleep(3)
            continue
        if not run:
            d = os.path.join(root, time.strftime('%Y%m%d_%H%M%S'))
            os.makedirs(d, exist_ok=True)
            run = {'dir': d, 't0': time.time(), 'n': 0, 'at': os.path.getsize(log) if os.path.isfile(log) else 0}
            print('game window seen: %s' % d, flush=True)
        name = os.path.join(run['dir'], '%04d_%ds.jpg' % (run['n'], time.time() - run['t0']))
        try:
            if grab(w[0], name):
                run['n'] += 1
            elif os.path.isfile(name):
                os.remove(name)
        except (subprocess.TimeoutExpired, OSError):
            pass
        try:                                              # the hook's lines of this run, as they come
            with open(log, 'rb') as f:
                f.seek(run['at'])
                new = f.read()
            if new:
                run['at'] += len(new)
                with open(os.path.join(run['dir'], 'watch.log'), 'ab') as f:
                    f.write(new)
        except OSError:
            pass
        time.sleep(every)


if __name__ == '__main__':
    main()
