#!/usr/bin/env python3
"""
kl_kit_summary.py - one-screen summary of a live bench kit (read-only, 2026-11-02).

usage: python tools/kl_kit_summary.py KITDIR [--solo DIR] [--grep REGEX]... [--control TAG_MAP]...
  KITDIR holds maps_*.txt (lines tag|map|slot|page|secs). Logs: <solo>/<TAG>_<MAP>/inst1/KLHook.log (host), inst2 (client).
Per run dir and seat: log exists, last RESULT line (200 chars), asserts / faults (parsed from the RESULT line when it has
them, else counted), 'is dead or gone' count, last 'round summary:' money + boarded, every round clock (left[+4c]=) at state 25.
Lines with 'netsmooth' or 'heli:' are ignored. Always exits 0.

Batch gate (2026-11-02 scheduled, for the 21-map passes Q28..Q35):
  python tools/kl_kit_summary.py --batch Q35_ [KITDIR] [--solo DIR] [--gate]
  One line per <solo>/<PREFIX>* run dir from the two seats' KLHook.result files (state, asserts, faults, soft_asserts,
  level_loaded, scene) plus the run.txt RESULT line; a run is CLEAN when both seats say state=PASS, level_loaded=1 and
  asserts = faults = soft_asserts = 0 (a missing result file or seat = NOT clean). With KITDIR the scene's Fxx is checked
  against the slot of the maps_*.txt line of that tag (a wrong slot = NOT clean). The last line is the verdict:
  'BATCH Q35_: 21 run(s), 21 clean -> CLEARED' or the list of the runs that are not. --gate exits 1 unless every run is
  clean (for a ship script); without it the exit code stays 0.
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


RE_SLOT = re.compile(r'Locations[\\/](F\d\d)[\\/]', re.I)


def read_result(path):
    """KLHook.result (key=value lines) -> dict, or None when the file is missing. Values stay strings."""
    if not os.path.isfile(path):
        return None
    r = {}
    with open(path, errors='replace') as f:
        for ln in f:
            if '=' in ln:
                k, v = ln.rstrip('\r\n').split('=', 1)
                r[k.strip()] = v.strip()
    return r


def read_kit_slots(kit):
    """maps_*.txt -> {'TAG_MAP': 'Fxx'} (the slot column, upper case); {} when there is no kit."""
    slots = {}
    if not kit:
        return slots
    for p in sorted(glob.glob(os.path.join(kit, 'maps_*.txt'))):
        with open(p, errors='replace') as f:
            for ln in f:
                a = ln.strip().split('|')
                if len(a) >= 3 and not a[0].startswith('#'):
                    slots[a[0] + '_' + a[1]] = a[2].strip().upper()
    return slots


def seat_clean(r):
    """(clean?, why) for one seat's result dict: PASS, level loaded, 0 asserts / faults / soft asserts (soft_asserts is
    absent in older hooks: then not counted)."""
    if r is None:
        return False, 'no result file'
    why = []
    if r.get('state') != 'PASS':
        why.append('state=%s' % r.get('state', '?'))
    if r.get('level_loaded') != '1':
        why.append('level_loaded=%s' % r.get('level_loaded', '?'))
    for k in ('asserts', 'faults', 'soft_asserts'):
        if k in r and r[k] != '0':
            why.append('%s=%s' % (k, r[k]))
    return not why, ', '.join(why)


def run_txt_result(d):
    """The last RESULT line of run.txt (the launcher's verdict), '' when none."""
    p, last = os.path.join(d, 'run.txt'), ''
    if os.path.isfile(p):
        with open(p, errors='replace') as f:
            for ln in f:
                s = ln.strip()
                if s.startswith('RESULT'):
                    last = s
    return last


def batch(solo, prefix, slots):
    """[(name, clean?, line)] for every <solo>/<prefix>* run dir, sorted by name."""
    rows = []
    for d in sorted(glob.glob(os.path.join(solo, prefix + '*'))):
        if not os.path.isdir(d):
            continue
        name, parts, clean, scene = os.path.basename(d), [], True, ''
        for seat, inst in (('host', 'inst1'), ('client', 'inst2')):
            r = read_result(os.path.join(d, inst, 'KLHook.result'))
            ok, why = seat_clean(r)
            clean = clean and ok
            if r and not scene:
                m = RE_SLOT.search(r.get('scene', ''))
                scene = m.group(1).upper() if m else r.get('scene', '')[:30]
            parts.append('%s %s' % (seat, 'clean' if ok else 'NOT clean (%s)' % why))
        want = slots.get(name)
        if want and scene and scene != want:
            clean = False
            parts.append('SLOT %s, kit says %s' % (scene, want))
        rt = run_txt_result(d)
        rows.append((name, clean, '%-11s %-4s %s | %s' % (name, scene or '?', '; '.join(parts), rt or 'run.txt: no RESULT line')))
    return rows


def verdict(prefix, rows):
    n, bad = len(rows), [r[0] for r in rows if not r[1]]
    if not n:
        return 'BATCH %s: no run dir -> NOT CLEARED' % prefix, False
    if bad:
        return 'BATCH %s: %d run(s), %d clean, NOT CLEARED: %s' % (prefix, n, n - len(bad), ' '.join(bad)), False
    return 'BATCH %s: %d run(s), %d clean -> CLEARED' % (prefix, n, n), True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('kit', nargs='?')
    ap.add_argument('--solo', default=SOLO)
    ap.add_argument('--grep', action='append', default=[])
    ap.add_argument('--control', action='append', default=[])
    ap.add_argument('--batch', metavar='PREFIX', help="gate every <solo>/<PREFIX>* run dir from its KLHook.result files")
    ap.add_argument('--gate', action='store_true', help='with --batch: exit 1 unless every run is clean')
    a = ap.parse_args()
    if a.batch:
        rows = batch(a.solo, a.batch, read_kit_slots(a.kit))
        for _, _, line in rows:
            print(line)
        text, ok = verdict(a.batch, rows)
        print(text)
        raise SystemExit(1 if a.gate and not ok else 0)
    if not a.kit:
        ap.error('KITDIR is needed without --batch')
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
