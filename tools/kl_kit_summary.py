#!/usr/bin/env python3
"""
kl_kit_summary.py - one-screen summary of a live bench kit (read-only, 2026-11-02).

usage: python tools/kl_kit_summary.py KITDIR [--solo DIR] [--grep REGEX]... [--control TAG_MAP]...
  KITDIR holds maps_*.txt (lines tag|map|slot|page|secs). Logs: <solo>/<TAG>_<MAP>/inst1/KLHook.log (host), inst2 (client).
Per run dir and seat: log exists, last RESULT line (200 chars), asserts / faults (parsed from the RESULT line when it has
them, else counted), 'is dead or gone' count, last 'round summary:' money + boarded, every round clock (left[+4c]=) at state 25.
Lines with 'netsmooth' or 'heli:' are ignored. Always exits 0.
"""
import argparse
import glob
import os
import re

SOLO = r'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'
SKIP = ('netsmooth', 'heli:')
RE_ASSERT = re.compile(r'(?<!soft )\basserts? (\d+)', re.I)
RE_FAULT = re.compile(r'\bfaults? (\d+)', re.I)
RE_MONEY = re.compile(r'(\d+) total')
RE_BOARD = re.compile(r'(\d+) boarded')
RE_CLOCK = re.compile(r'left\[\+4c\]=(-?[\d.]+)')


def read_kit(kit):
    runs = []
    for p in sorted(glob.glob(os.path.join(kit, 'maps_*.txt'))):
        with open(p, errors='replace') as f:
            for ln in f:
                ln = ln.strip()
                if ln and not ln.startswith('#'):
                    a = ln.split('|')
                    if len(a) >= 2:
                        runs.append(a[0] + '_' + a[1])
    return runs


def summarize(log, greps):
    s = {'exists': os.path.isfile(log), 'result': None, 'assert': 0, 'fault': 0, 'dead': 0,
         'money': None, 'boarded': None, 'clocks': [], 'grep': [[0, []] for _ in greps]}
    if not s['exists']:
        return s
    with open(log, errors='replace') as f:
        for ln in f:
            low = ln.lower()
            if any(k in low for k in SKIP):
                continue
            ln = ln.rstrip('\r\n')
            if 'RESULT' in ln:
                s['result'] = ln
            if 'assert' in low:
                s['assert'] += 1
            if 'fault' in low:
                s['fault'] += 1
            if 'is dead or gone' in ln:
                s['dead'] += 1
            if 'round summary:' in ln:
                m, b = RE_MONEY.search(ln), RE_BOARD.search(ln)
                s['money'] = int(m.group(1)) if m else None
                s['boarded'] = int(b.group(1)) if b else None
            if 'round clock at state 25' in ln:
                m = RE_CLOCK.search(ln)
                if m:
                    s['clocks'].append(m.group(1))
            for i, rx in enumerate(greps):
                if rx.search(ln):
                    s['grep'][i][0] += 1
                    s['grep'][i][1] = (s['grep'][i][1] + [ln[:200]])[-2:]
    r = s['result']
    if r:   # the game's own counts beat our line counts (a line can mention 'assert' without being one)
        m, f = RE_ASSERT.search(r), RE_FAULT.search(r)
        if m:
            s['assert'] = int(m.group(1))
        if f:
            s['fault'] = int(f.group(1))
    return s


def show(name, seat, s, greps_src):
    print('  %s %s' % (name, seat))
    if not s['exists']:
        print('    log: MISSING')
        return
    print('    result: %s' % ((s['result'] or 'none')[:200]))
    print('    asserts %d  faults %d  dead-or-gone %d' % (s['assert'], s['fault'], s['dead']))
    print('    round summary: money %s  boarded %s' % (s['money'], s['boarded']))
    print('    round clock left[+4c]: %s' % (', '.join(s['clocks']) or 'none'))
    for src, (n, last) in zip(greps_src, s['grep']):
        print('    grep %r: %d' % (src, n))
        for ln in last:
            print('      ' + ln)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('kit')
    ap.add_argument('--solo', default=SOLO)
    ap.add_argument('--grep', action='append', default=[])
    ap.add_argument('--control', action='append', default=[])
    a = ap.parse_args()
    greps = [re.compile(g) for g in a.grep]
    runs = read_kit(a.kit)
    print('kit %s: %d run(s)' % (a.kit, len(runs)))
    for label, names in (('', runs), ('control ', a.control)):
        for name in names:
            print('%s%s' % (label, name))
            for seat, inst in (('host', 'inst1'), ('client', 'inst2')):
                log = os.path.join(a.solo, name, inst, 'KLHook.log')
                show(name, seat, summarize(log, greps), a.grep)


if __name__ == '__main__':
    main()
