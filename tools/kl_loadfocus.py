#!/usr/bin/env python3
"""
Shorten level loads: take the game's window out of the foreground while a level loads and put it
back when the level is in.

    python kl_loadfocus.py [hours to keep watching, default 8]

Why (re/loading.md): across 67 kept loads the same archive loads in 11-15 s with the game window
in the background and in 100-200 s with it in front; the loader's message pump nudges the cursor
on every step when the game is the foreground window (kl2 0x6f4220). Not proven that the nudge is
the cost: this script is also the experiment.
How: it reads <DD>/KLHook.log as the hook writes it. 'session: state 0x0 -> 0x12' is a level
load starting from the menu, 'session: state 0x12 -> 0x15' the level being in (both the SHIP and
the TEST hook write these lines). Between the two the desktop shell window is made the foreground
window; afterwards the game's window is. A direct boot (-o DefaultScene) has no such lines and is
left alone. Passive otherwise: no input to the game, nothing written to the game folder.
ASSUMPTION: the game keeps loading and drawing while it is not the foreground window (the kept
background runs did). If the game misbehaves, end this script: nothing else depends on it.
"""
import ctypes, os, subprocess, sys, time
import ctypes.wintypes as wt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, DD_GUESSES, DD_EXE

u, k = ctypes.windll.user32, ctypes.windll.kernel32
HWND = ctypes.c_void_p
u.GetForegroundWindow.restype = HWND
u.GetShellWindow.restype = HWND
u.SetForegroundWindow.argtypes = [HWND]
u.IsWindowVisible.argtypes = [HWND]
u.GetWindowTextW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
u.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(wt.DWORD)]
u.GetWindowThreadProcessId.restype = wt.DWORD
u.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]


COVER = ("import tkinter as t; r = t.Tk(); r.title('KL load helper - closes by itself'); r.geometry('360x60+40+40'); "
         "t.Label(r, text='Kane & Lynch is loading faster in the background...').pack(expand=True); r.after(600000, r.destroy); r.mainloop()")


def game_window():
    found = []

    def each(hwnd, _):
        if u.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(260)
            u.GetWindowTextW(hwnd, buf, 260)
            if buf.value.startswith('Kane & Lynch 2'):
                found.append(hwnd)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, HWND, ctypes.c_void_p)(each), 0)
    return found[0] if found else None


def to_front(hwnd):
    """SetForegroundWindow from a background process: Windows allows it to a thread attached to
    the input of the current foreground thread."""
    if not hwnd:
        return False
    fg = u.GetForegroundWindow()
    if fg == hwnd:
        return True
    me, other = k.GetCurrentThreadId(), u.GetWindowThreadProcessId(fg, None) if fg else 0
    if other and other != me:
        u.AttachThreadInput(me, other, True)
    ok = bool(u.SetForegroundWindow(hwnd))
    if other and other != me:
        u.AttachThreadInput(me, other, False)
    return ok


def main():
    until = time.time() + 3600 * (float(sys.argv[1]) if len(sys.argv) > 1 else 8.0)
    log = os.path.join(find(DD_GUESSES, DD_EXE), 'KLHook.log')
    at = os.path.getsize(log) if os.path.isfile(log) else 0
    loading, t0, cover = False, 0.0, None
    while time.time() < until:
        time.sleep(0.25)
        try:
            size = os.path.getsize(log)
            if size < at:
                at = 0
            if size == at:
                if loading and time.time() - t0 > 420:        # never leave the game in the background for good
                    loading = False
                    if cover:
                        cover.terminate(); cover = None
                    print('%s no end of load after 420 s: game to the front: %s' % (time.strftime('%H:%M:%S'), to_front(game_window())), flush=True)
                continue
            with open(log, 'rb') as f:
                f.seek(at)
                new = f.read().decode('latin1')
            at = size
        except OSError:
            continue
        for line in new.splitlines():
            if 'session: state 0x0 -> 0x12' in line and not loading:
                loading, t0 = True, time.time()
                ok = to_front(u.GetShellWindow())
                if not ok or u.GetForegroundWindow() == game_window():
                    # Windows refuses SetForegroundWindow from a background process (seen 2026-10-09:
                    # False on every load). A window of a process started NOW does get the foreground:
                    # a small helper window is opened for the time of the load and closed afterwards.
                    cover = cover or subprocess.Popen([sys.executable.replace('python.exe', 'pythonw.exe'), '-c', COVER])
                    ok = 'cover window'
                print('%s load starts: game out of the foreground: %s' % (time.strftime('%H:%M:%S'), ok), flush=True)
            elif loading and ('session: state 0x12 -> 0x15' in line or 'KLHook loaded' in line or 'process ended' in line or 'exit:' in line):
                loading = False
                if cover:
                    cover.terminate(); cover = None
                    time.sleep(0.3)
                print('%s load over after %.0f s: game to the front: %s' % (time.strftime('%H:%M:%S'), time.time() - t0, to_front(game_window())), flush=True)


if __name__ == '__main__':
    main()
