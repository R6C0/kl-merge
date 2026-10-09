#!/usr/bin/env python3
"""
Run one unattended load test of the level installed in a Dog Days slot.

    python kl_autotest.py [seconds to wait, default 420] [--shots 70,100,150,200-400:10] [--tag name]
        --shots: at these seconds after the start, save a picture of the game's own window
        (only its rectangle) as <work folder>/research/shots/<tag>_<seconds>s.png

Needs the Steam launch options of Dog Days to boot straight into the level and quit by itself:
    -o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120
(kl2.exe reads no ini; "-o Key=Value" lines override its built-in configuration.)

Starts the game through Steam, waits until kl2.exe has gone or the time is up (then ends it),
and reports what the run left behind: the events our dinput8.dll proxy wrote to KLHook.log, and
any crash dump the game wrote itself (those catch faults in other modules, which the proxy does
not log). Prints one line starting with RESULT:
    RESULT: crash kl2.exe+0x2a1ff7 ...     a fault inside kl2.exe (address as in the log)
    RESULT: crash <module>+0x...           a fault elsewhere, from the game's own dump
    RESULT: assert ...                     the engine hit one of its int3 checks first
    RESULT: clean exit after N s           no fault recorded: the level loaded and AutoExit fired
    RESULT: hung                           still running at the deadline and nothing was logged
Exit code 0 for a clean exit, 1 otherwise. Nothing in the game folder is changed, except that
the hook's own KLHook.result of an earlier scripted run (klhook/klauto.c) is deleted before the
start; the new one is printed. A scripted run through the menu needs a longer wait (1200).
"""
import glob, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, DD_GUESSES, DD_EXE

PROBE = 0xa8e3cb                      # Steam DRM's deliberate write to 0: logged as CRASH, harmless
APP = 28000


def running():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True).stdout
    live = []
    for line in out.splitlines():
        m = re.match(r'"kl2\.exe","(\d+)","[^"]*","[^"]*","([\d,\.]+) K"', line)
        if m and int(re.sub(r'\D', '', m.group(2))) > 5000:      # exited shells linger at ~100 K
            live.append(int(m.group(1)))
    return live


def window_of(pids):
    """(handle, x, y, width, height) of the largest visible top-level window of the processes."""
    import ctypes
    from ctypes import wintypes
    u, best = ctypes.windll.user32, [None, 0]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]

    def each(h, _l):
        pid, r = wintypes.DWORD(), wintypes.RECT()
        u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u.IsWindowVisible(h):
            u.GetWindowRect(h, ctypes.byref(r))
            area = (r.right - r.left) * (r.bottom - r.top)
            if area > best[1]:
                best[:] = [(h, r.left, r.top, r.right - r.left, r.bottom - r.top), area]
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(each), 0)
    return best[0]


def shot(pids, path):
    """Copy the screen under the game's own window (nothing else of the desktop) to a PNG.
    -> False (no window), True, or 'black' when every try came back all black.
    The game runs full screen: a BitBlt of the screen now and then returns a black frame although
    the game is drawing (run RN6: black and good pictures alternate while the round timer runs).
    So a black frame is taken again, up to 8 times 0.2 s apart, then once through PrintWindow
    (PW_RENDERFULLCONTENT). A picture that is still black is most likely what the game shows
    (the fade at a load, AutoExit)."""
    import ctypes, struct, zlib
    ctypes.windll.user32.SetProcessDPIAware()
    w = window_of(pids)
    if not w or w[3] < 320 or w[4] < 200:               # a splash or helper window, not the game's
        return False
    h, x, y, cx, cy = w
    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    info = struct.pack('<IiiHHIIiiII', 40, cx, -cy, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(cx * cy * 4)
    black = True
    for attempt in range(9):
        scr = u.GetDC(0)
        mem = g.CreateCompatibleDC(scr)
        bmp = g.CreateCompatibleBitmap(scr, cx, cy)
        g.SelectObject(mem, bmp)
        if attempt < 8:
            g.BitBlt(mem, 0, 0, cx, cy, scr, x, y, 0x00CC0020)
        else:
            u.PrintWindow(ctypes.c_void_p(h), ctypes.c_void_p(mem), 2)
        g.GetDIBits(mem, bmp, 0, cy, buf, info, 0)
        g.DeleteObject(bmp); g.DeleteDC(mem); u.ReleaseDC(0, scr)
        px = bytearray(buf.raw)                                 # whole-image slices: 0.3 s instead of 8 s a picture
        del px[3::4]                                            # BGRX -> BGR
        black = px.count(0) == len(px)
        if not black:
            break
        time.sleep(0.2)
    px[0::3], px[2::3] = px[2::3], px[0::3]                     # BGR -> RGB
    raw = b''.join(bytes(1) + px[r * cx * 3:(r + 1) * cx * 3] for r in range(cy))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(bytes([0x89, 0x50, 0x4e, 0x47, 13, 10, 26, 10]) + chunk(b'IHDR', struct.pack('>IIBBBBB', cx, cy, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 1)) + chunk(b'IEND', b''))
    return 'black' if black else True


def last_session(log):
    """Lines of the newest KLHook session, or [] if the log has none."""
    try:
        lines = open(log, errors='replace').read().splitlines()
    except OSError:
        return []
    starts = [i for i, l in enumerate(lines) if 'KLHook loaded' in l]
    return lines[starts[-1]:] if starts else []


def main():
    a = sys.argv[1:]
    shots, tag = [], time.strftime('%H%M%S')
    if '--shots' in a:
        i = a.index('--shots')
        for x in a[i + 1].split(','):                       # 70 | 30-90:5 (from-to:step)
            if '-' in x:
                r, _, st = x.partition(':'); lo, hi = r.split('-')
                shots += range(int(lo), int(hi) + 1, int(st or 5))
            else:
                shots.append(int(x))
        shots = sorted(set(shots)); del a[i:i + 2]
    if '--tag' in a:
        i = a.index('--tag'); tag = a[i + 1]; del a[i:i + 2]
    wait = int(a[0]) if a else 420
    dd = find(DD_GUESSES, DD_EXE)
    if not dd:
        raise SystemExit('Dog Days not found')
    if running():
        raise SystemExit('RESULT: not started - kl2.exe is already running')
    log = os.path.join(dd, 'KLHook.log')
    size0 = os.path.getsize(log) if os.path.isfile(log) else 0
    dumps0 = set(glob.glob(os.path.join(glob.escape(dd), 'kl2_*crash*.mdmp')))
    result = os.path.join(dd, 'KLHook.result')          # written by a dinput8.dll built from klhook/klauto.c
    if os.path.isfile(result):
        os.remove(result)
    t0 = time.time()
    os.startfile('steam://rungameid/%d' % APP)
    started = False
    while time.time() - t0 < wait:
        time.sleep(2)
        live = running()
        if live:
            started = True
            if shots and time.time() - t0 >= shots[0]:
                from kl_port_check import workdir
                path = os.path.join(workdir(), 'research', 'shots', '%s_%ds.png' % (tag, shots.pop(0)))
                r = shot(live, path)
                print('  shot | %s%s' % (path if r else 'no window', ' (black after 9 tries)' if r == 'black' else ''), flush=True)
        elif started or time.time() - t0 > 60:
            break
    took = time.time() - t0
    left = running()
    for pid in left:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
    if not started:
        print('RESULT: not started - no kl2.exe within 60 s (is Steam running?)')
        return 1
    grew = os.path.isfile(log) and os.path.getsize(log) > size0
    events = []
    for l in (last_session(log) if grew else []):
        m = re.search(r'(CRASH \w+|ASSERT) at kl2\.exe\+(\w+) \((\w+)\)', l)
        if m and int(m.group(3), 16) != PROBE:
            events.append((m.group(1).split()[0].lower(), 'kl2.exe+0x' + m.group(2).lstrip('0'), l.strip()))
    new = sorted(set(glob.glob(os.path.join(glob.escape(dd), 'kl2_*crash*.mdmp'))) - dumps0, key=os.path.getmtime)
    for l in (last_session(log) if grew else [])[-14:]:
        print('  log |', l[:200])
    if new:
        print('  game dump:', os.path.basename(new[-1]))
    if os.path.isfile(result):                          # a scripted run (re/fa_round.md): state=PASS / FAIL / EXIT / RUNNING
        print('  KLHook.result | ' + ' '.join(open(result, errors='replace').read().split()))
    if events:
        kind, where, line = events[0]
        print('RESULT: %s %s after %.0f s (%d events)' % (kind, where, took, len(events)))
    elif new:
        print('RESULT: crash outside kl2.exe after %.0f s - decode with: python debug/dump.py "%s"' % (took, new[-1]))
    elif left:
        print('RESULT: hung - still running after %.0f s, nothing logged' % took)
    else:
        print('RESULT: clean exit after %.0f s' % took)
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
