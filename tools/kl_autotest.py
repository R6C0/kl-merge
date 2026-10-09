#!/usr/bin/env python3
"""
Run one unattended load test of the level installed in a Dog Days slot.

    python kl_autotest.py [seconds to wait, default 420] [--shots 70,100,150,200-400:10] [--tag name]
                          [--hook <dinput8.dll or its folder>] [--ini <KLHook.ini>]
        --shots: at these seconds after the start, save a picture of the game's own window
        (only its rectangle) as <work folder>/research/shots/<tag>_<seconds>s.png
        --hook / --ini: put this hook DLL and / or this KLHook.ini into the game folder for the
        run, keep the ini, the hook's KLHook.result and this tool's output as
        <work folder>/build/klhook/live/<tag>.{ini,result,txt}, and afterwards put the ORIGINAL
        pair back from <work folder>/build/klhook/direct_boot (sha1 printed).
    With --tag the run's part of KLHook.log is kept as <work folder>/build/klhook/live/<tag>.log.

Needs the Steam launch options of Dog Days to boot straight into the level and quit by itself:
    -o DefaultScene=Locations/F01/F01_Main.gms -o AutoExit=120
(kl2.exe reads no ini; "-o Key=Value" lines override its built-in configuration.)

Starts the game through Steam, waits until kl2.exe has gone or the time is up (then ends it),
and reports what the run left behind: the events our dinput8.dll proxy wrote to KLHook.log, and
any crash dump the game wrote itself (those catch faults in other modules, which the old proxy
did not log). Prints one line starting with RESULT:
    RESULT: crash kl2.exe+0x2a1ff7 ...     a fault inside kl2.exe (address as in the log)
    RESULT: crash <module>+0x...           a fault elsewhere (the hook's FATAL line, or the game's dump)
    RESULT: assert ...                     the engine hit one of its int3 checks first
    RESULT: integrity exit ...             the game's code-integrity check ended it (re/antitamper.md)
    RESULT: clean exit after N s           no fault recorded: the level loaded and AutoExit fired
    RESULT: hung                           still running at the deadline and nothing was logged
Exit code 0 for a clean exit, 1 otherwise. Nothing in the game folder is changed (without
--hook / --ini), except that the hook's own KLHook.result of an earlier scripted run
(klhook/klauto.c) is deleted before the start; the new one is printed. A scripted run through the
menu needs a longer wait (1200).

LINGERING ENTRIES (debug/zombies.py): a game run that ends in a Windows error report leaves a
'kl2.exe' entry with no thread, which cannot be opened or ended and keeps the run's dinput8.dll
mapped. So: a process counts as running only while it has a thread (never by its memory size,
and a thread-less entry is never given to taskkill); the number of such entries is printed before
and after the run (one more = this run ended in a Windows error report: the hook did not end the
process itself); and a hook DLL that cannot be overwritten is renamed aside (`put`).
"""
import glob, hashlib, os, re, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, DD_GUESSES, DD_EXE

PROBE = 0xa8e3cb                      # Steam DRM's deliberate write to 0: the old hook logged it as CRASH, harmless
APP = 28000
ORIGINAL = {'dinput8.dll': '7e806e6c1f8669779d7a5481b1a5300defcaec96',      # the pair the owner plays with:
            'KLHook.ini': '2ced8e5f2b2399ad3c151557ef636004f93d2e81'}       # <work>/build/klhook/direct_boot

try:                                  # the repo's debug/ folder; the work-folder copy of tools/ has none
    sys.path.insert(1, os.path.join(os.path.dirname(HERE), 'debug'))
    import zombies
except Exception:                     # ImportError, or no ntdll (not Windows)
    zombies = None


def processes(name='kl2.exe'):
    """-> (pids with at least one thread, pids with none) of that image name.
    Without debug/zombies.py: tasklist, and the old guess that a thread-less entry is one under
    5000 K of working set (true of every entry seen; a starting game is briefly below it too)."""
    live, dead = [], []
    if zombies:
        for pid, v in zombies.procs().items():
            if v[0].lower() == name.lower():
                (live if v[1] else dead).append(pid)
        return live, dead
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + name, '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.match(r'"[^"]+","(\d+)","[^"]*","[^"]*","([\d,\.]+) K"', line)
        if m:
            (live if int(re.sub(r'\D', '', m.group(2))) > 5000 else dead).append(int(m.group(1)))
    return live, dead


def running():
    """pids of kl2.exe processes that have a thread: a game that runs (lingering entries excluded)."""
    return processes()[0]


def lingering():
    """number of thread-less kl2.exe entries (see the docstring)."""
    return len(processes()[1])


def sha1(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()


def put(src, dst):
    """Copy src over dst. A DLL that a lingering entry keeps mapped cannot be written or deleted,
    but it can be renamed: it is moved aside (same volume: the temp folder if that is on the
    game's drive, else beside it as <name>.aside_N) and a fresh file takes its place.
    -> '' or a note saying where the locked file went. Files moved aside earlier are deleted
    when that has become possible (after a reboot)."""
    folder, name = os.path.split(os.path.abspath(dst))
    aside = os.path.join(tempfile.gettempdir(), 'kl_autotest_aside')
    if os.path.splitdrive(aside)[0].lower() != os.path.splitdrive(folder)[0].lower():
        aside = folder
    for old in glob.glob(os.path.join(glob.escape(aside), glob.escape(name) + '.aside_*')):
        try:
            os.remove(old)
        except OSError:
            pass
    try:
        shutil.copyfile(src, dst)
        return ''
    except PermissionError:
        os.makedirs(aside, exist_ok=True)
        k = 0
        while os.path.exists(os.path.join(aside, '%s.aside_%d' % (name, k))):
            k += 1
        os.replace(dst, os.path.join(aside, '%s.aside_%d' % (name, k)))
        shutil.copyfile(src, dst)
        return '%s was locked (mapped by a lingering entry): moved to %s' % (name, os.path.join(aside, '%s.aside_%d' % (name, k)))


def restore_original(dd, say=print):
    """Put the owner's dinput8.dll and KLHook.ini back; -> True when both sha1 sums are right."""
    from kl_port_check import workdir
    ok = True
    for name, want in ORIGINAL.items():
        src = os.path.join(workdir(), 'build', 'klhook', 'direct_boot', name)
        if not os.path.isfile(src) or sha1(src) != want:
            say('  restore | reference %s is missing or not the original' % src)
            ok = False
            continue
        dst = os.path.join(dd, name)
        if not os.path.isfile(dst) or sha1(dst) != want:
            note = put(src, dst)
            if note:
                say('  restore | ' + note)
        good = sha1(dst) == want
        say('  restore | %s %s' % (name, 'original (sha1 ok)' if good else 'WRONG ' + sha1(dst)))
        ok &= good
    return ok


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


def last_session(log, size0=0):
    """Lines of the newest KLHook session, or [] if the log has none; size0: only what was
    written after the log had that size."""
    try:
        with open(log, 'rb') as f:
            f.seek(size0)
            lines = f.read().decode('latin-1').splitlines()
    except OSError:
        return []
    starts = [i for i, l in enumerate(lines) if 'KLHook loaded' in l]
    return lines[starts[-1]:] if starts else []


EVENTS = [      # (kind, pattern); the hook's lines are those of klhook/klhook.c, as debug/log.py reads them
    ('assert', re.compile(r'ASSERT at (kl2\.exe)\+(\w+) \((\w+)\)')),
    ('crash', re.compile(r'CRASH \w+ at (kl2\.exe)\+(\w+) \((\w+)\)')),
    # the rewritten hook (2026-10-09): a fatal fault in ANY module, which the hook then ends itself
    ('crash', re.compile(r'FATAL (?:unhandled exception|stack overflow) \w+ at (.+?)\+0x(\w+) \((\w+)\)')),
]
NOTES = ('WATCHDOG:', 'process ended here', 'left to Windows', 'exit: ', 'patch REFUSED', 'process exit',
         "Steam's probe",
         # klsteam.c / kljoin.c (re/hook_live.md): the guard is absent (then no scripted session may end), a session
         # ended (the game uploads and commits stats there), a jump box moved a player, a box that cannot work
         'steam: NOT GUARDED', 'SESSION END', 'join: player', 'NOT usable on this level')


def read_events(lines):
    """-> ([(kind, where, line)], [other lines worth showing]) of one session's lines.
    The Steam probe is no event: the old hook wrote a CRASH line for it, the rewritten one writes
    a single 'Steam's probe ... not dumped' line. A repeated assert ('(again)') counts once."""
    events, notes = [], []
    for l in lines:
        for kind, pat in EVENTS:
            m = pat.search(l)
            if m:
                mod = 'kl2.exe' if m.group(1).lower() == 'kl2.exe' else m.group(1)
                where = '%s+0x%s' % (mod, m.group(2).lstrip('0'))
                if int(m.group(3), 16) != PROBE and '(again)' not in l and not (
                        'FATAL' in l and events and events[-1][1] == where):     # CRASH (first chance) + FATAL = one fault
                    events.append((kind, where, l.strip()))
                break
        else:
            if 'FATAL C runtime' in l:
                events.append(('crash', 'the C runtime', l.strip()))
            elif 'INTEGRITY EXIT' in l:
                events.append(('integrity exit', '(ExitProcess 0x8000dead)', l.strip()))
            elif any(n in l for n in NOTES):
                notes.append(l.strip())
    return events, notes


def main():
    a = sys.argv[1:]
    shots, opt = [], {}
    if '--shots' in a:
        i = a.index('--shots')
        for x in a[i + 1].split(','):                       # 70 | 30-90:5 (from-to:step)
            if '-' in x:
                r, _, st = x.partition(':'); lo, hi = r.split('-')
                shots += range(int(lo), int(hi) + 1, int(st or 5))
            elif x:
                shots.append(int(x))
        shots = sorted(set(shots)); del a[i:i + 2]
    for key in ('--tag', '--hook', '--ini'):
        if key in a:
            i = a.index(key); opt[key] = a[i + 1]; del a[i:i + 2]
    tag = opt.get('--tag', time.strftime('%H%M%S'))
    wait = int(a[0]) if a else 420
    dd = find(DD_GUESSES, DD_EXE)
    if not dd:
        raise SystemExit('Dog Days not found')
    if running():
        raise SystemExit('RESULT: not started - kl2.exe is already running')
    out = []

    def say(text):
        print(text, flush=True)
        out.append(text)
    swap = '--hook' in opt or '--ini' in opt
    code = 1
    try:
        if '--hook' in opt:
            src = opt['--hook']
            src = os.path.join(src, 'dinput8.dll') if os.path.isdir(src) else src
            note = put(src, os.path.join(dd, 'dinput8.dll'))
            say('  hook | %s (sha1 %s)%s' % (src, sha1(src)[:8], ' - ' + note if note else ''))
        if '--ini' in opt:
            put(opt['--ini'], os.path.join(dd, 'KLHook.ini'))
            say('  ini  | %s' % opt['--ini'])
        code = run(dd, wait, shots, tag, say, keep_log='--tag' in opt or swap)
    finally:
        if swap:
            from kl_port_check import workdir
            live = os.path.join(workdir(), 'build', 'klhook', 'live')
            os.makedirs(live, exist_ok=True)
            if '--ini' in opt:
                shutil.copyfile(opt['--ini'], os.path.join(live, tag + '.ini'))
            if os.path.isfile(os.path.join(dd, 'KLHook.result')):
                shutil.copyfile(os.path.join(dd, 'KLHook.result'), os.path.join(live, tag + '.result'))
            if not restore_original(dd, say):
                code = code or 1
            open(os.path.join(live, tag + '.txt'), 'w').write('\n'.join(out) + '\n')
    return code


def run(dd, wait, shots, tag, say=print, keep_log=False):
    """One start through Steam; -> exit code (0 = clean exit). See the module docstring."""
    from kl_port_check import workdir
    log = os.path.join(dd, 'KLHook.log')
    size0 = os.path.getsize(log) if os.path.isfile(log) else 0
    dumps0 = set(glob.glob(os.path.join(glob.escape(dd), 'kl2_*crash*.mdmp')))
    result = os.path.join(dd, 'KLHook.result')          # written by a dinput8.dll built from klhook/klauto.c
    if os.path.isfile(result):
        os.remove(result)
    linger0 = lingering()
    t0 = time.time()
    os.startfile('steam://rungameid/%d' % APP)
    started = False
    while time.time() - t0 < wait:
        time.sleep(2)
        live = running()
        if live:
            started = True
            if shots and time.time() - t0 >= shots[0]:
                path = os.path.join(workdir(), 'research', 'shots', '%s_%ds.png' % (tag, shots.pop(0)))
                r = shot(live, path)
                say('  shot | %s%s' % (path if r else 'no window', ' (black after 9 tries)' if r == 'black' else ''))
        elif started or time.time() - t0 > 60:
            break
    took = time.time() - t0
    left = running()                                    # only processes with a thread: a lingering entry cannot be ended
    for pid in left:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
    for _ in range(10):                                 # Windows makes its error-report entry within a second or two
        if not running():
            break
        time.sleep(1)
    time.sleep(2)
    linger1 = lingering()
    say('  lingering kl2.exe entries (no thread): %d before, %d after%s' % (
        linger0, linger1, ' - THIS RUN ENDED IN A WINDOWS ERROR REPORT (the hook did not end the process itself)' if linger1 > linger0 else ''))
    if not started:
        say('RESULT: not started - no kl2.exe within 60 s (is Steam running?)')
        return 1
    grew = os.path.isfile(log) and os.path.getsize(log) > size0
    session = last_session(log, size0) if grew else []
    if grew and keep_log:
        keep = os.path.join(workdir(), 'build', 'klhook', 'live')
        os.makedirs(keep, exist_ok=True)
        with open(log, 'rb') as f:
            f.seek(size0)
            open(os.path.join(keep, tag + '.log'), 'wb').write(f.read())
    events, notes = read_events(session)
    new = sorted(set(glob.glob(os.path.join(glob.escape(dd), 'kl2_*crash*.mdmp'))) - dumps0, key=os.path.getmtime)
    for l in session[-14:]:
        say('  log | ' + l[:200])
    for l in notes[:8]:
        if l not in [x.strip() for x in session[-14:]]:
            say('  log | ' + l[:200])
    if new:
        say('  game dump: ' + os.path.basename(new[-1]))
    if os.path.isfile(result):                          # a scripted run (re/fa_round.md): state=PASS / FAIL / EXIT / RUNNING
        say('  KLHook.result | ' + ' '.join(open(result, errors='replace').read().split()))
    if events:
        kind, where, line = events[0]
        fatal = [e for e in events[1:] if 'FATAL' in e[2] and e[1] != where]
        say('RESULT: %s %s after %.0f s (%d events)%s' % (kind, where, took, len(events),
                                                          '; fatal fault at ' + fatal[0][1] if fatal else ''))
    elif new:
        say('RESULT: crash outside kl2.exe after %.0f s - decode with: python debug/dump.py "%s"' % (took, new[-1]))
    elif linger1 > linger0:
        say('RESULT: crash - ended in a Windows error report after %.0f s, nothing logged' % took)
    elif left:
        say('RESULT: hung - still running after %.0f s, nothing logged' % took)
    else:
        say('RESULT: clean exit after %.0f s' % took)
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
