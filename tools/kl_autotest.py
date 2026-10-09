#!/usr/bin/env python3
"""
Run one unattended load test of the level installed in a Dog Days slot.

    python kl_autotest.py [seconds to wait, default 420]

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
Exit code 0 for a clean exit, 1 otherwise. Nothing in the game folder is changed.
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


def last_session(log):
    """Lines of the newest KLHook session, or [] if the log has none."""
    try:
        lines = open(log, errors='replace').read().splitlines()
    except OSError:
        return []
    starts = [i for i, l in enumerate(lines) if 'KLHook loaded' in l]
    return lines[starts[-1]:] if starts else []


def main():
    wait = int(sys.argv[1]) if len(sys.argv) > 1 else 420
    dd = find(DD_GUESSES, DD_EXE)
    if not dd:
        raise SystemExit('Dog Days not found')
    if running():
        raise SystemExit('RESULT: not started - kl2.exe is already running')
    log = os.path.join(dd, 'KLHook.log')
    size0 = os.path.getsize(log) if os.path.isfile(log) else 0
    dumps0 = set(glob.glob(os.path.join(glob.escape(dd), 'kl2_*crash*.mdmp')))
    t0 = time.time()
    os.startfile('steam://rungameid/%d' % APP)
    started = False
    while time.time() - t0 < wait:
        time.sleep(2)
        if running():
            started = True
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
