#!/usr/bin/env python3
"""
kl_online_vs_arcade.py - ONE per-map table: the Arcade baseline (ARC1 table of re/arcade_baseline_1101.md) next to the ONLINE bots of a bench prefix
(the host log <solo>/<PREFIX>_<MAP>/inst1/KLHook.log of the Q31 / Q32 ... runs), with a pass threshold (2026-11-01, wk-botscore-1101, week-plan T3).

    python tools/kl_online_vs_arcade.py [--prefix Q31] [--solo <dir of <PREFIX>_<MAP> folders>] [--arcade <baseline .md>]
                                        [--maps DD01,DD02,...] [--threshold 0.6] [--round 1]
    python tools/kl_online_vs_arcade.py --log MAP=<KLHook.log> [--log ...]

Columns: loot ($ carried), stacks taken, boarded, van call s (seconds after 'round N starts' of the first van state 1..4), each Arcade | Online, then the loot ratio
and PASS / BELOW / NO-BASELINE / NO-LOG / NO-ROUND.
PASS = online loot >= THRESHOLD x Arcade loot.  THRESHOLD 0.60 is a JUDGEMENT CALL (not measured): Arcade itself spreads a lot between runs (stacks are shot
away, bots die), so 60 % of one Arcade round is "in the same league", not "equal". Change it with --threshold.
Online numbers are the HOST's HOOK tally ('round summary: B bot(s) given orders, S stack(s) taken, T total (hook tally ...), X boarded'); the Arcade ones are the game's
own crew records (kl_arcade_baseline.py). A round without a summary (bench stopped inside it) falls back to the GRABBED / BOARDED lines and is marked '(no summary)'.
Reads only. Exit 0 whenever a table was printed, 1 when no map had any data.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
THRESHOLD = 0.60      # JUDGEMENT CALL, see the module docstring
DEFAULT_ARCADE = os.path.join(ROOT, 're', 'arcade_baseline_1101.md')

COLS = ['Map', 'Loot Arcade', 'Loot Online', 'Ratio', 'Stacks Arcade', 'Stacks Online', 'Boarded Arcade', 'Boarded Online',
        'Van s Arcade', 'Van s Online', 'Verdict']

R_TS = re.compile(r'^(\d\d):(\d\d):(\d\d)\.(\d\d\d) ')
R_START = re.compile(r'botfill: tactics: round (\d+) starts')
R_SCAN = re.compile(r'botfill: tactics: scan: \d+ objects, \d+ live Ally bot\(s\), (\d+) armed stack\(s\)')
R_SUM = re.compile(r'botfill: tactics: round summary: (\d+) bot\(s\) given orders, (\d+) stack\(s\) taken, (-?\d+) total .*?, (\d+) boarded, (\d+) stack\(s\) given up')
R_VAN = re.compile(r'botfill: tactics: van state (\d+) -> (\d+) ')
R_GRAB = re.compile(r'botfill: tactics: bot \d+ \(actor [0-9a-f]+\) GRABBED stack [0-9a-f]+ = (\d+)')
R_BOARD = re.compile(r'botfill: tactics: bot (\d+) \(actor [0-9a-f]+\) BOARDED ')


def secs(line):
    m = R_TS.match(line)
    return None if not m else int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000.0


def money(v):
    return '-' if v is None else ('0' if v == 0 else '%.2fM' % (v / 1e6))


def parse_money(s):
    s = s.strip()
    m = re.match(r'^(-?\d+(?:\.\d+)?)M$', s)
    if m:
        return int(round(float(m.group(1)) * 1e6))
    return 0 if s == '0' else None


def parse_arcade(path):
    """-> {map: dict(loot, taken, boarded, van)} from the markdown table of the ARC1 baseline note (header names found by text, not by position)."""
    try:
        lines = open(path, 'r', encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        return {}
    head, out = None, {}
    for l in lines:
        if not l.startswith('|'):
            if head is not None and out:
                break
            continue
        cells = [c.strip() for c in l.strip().strip('|').split('|')]
        if cells and cells[0] == 'Map':
            head = {c: i for i, c in enumerate(cells)}
            continue
        if head is None or set(cells[0]) <= set('-: ') or not re.match(r'^D[DM]\d\d[A-Z]?$', cells[0]):
            continue

        def cell(name):
            i = head.get(name)
            return cells[i] if i is not None and i < len(cells) else ''
        ab = re.match(r'^(\d+)\s*/\s*(\d+)', cell('Aboard / bots'))
        van = re.match(r'^(\d+)', cell('Van call s (why)'))
        taken = re.match(r'^(\d+)', cell('Stacks taken'))
        out[cells[0]] = dict(loot=parse_money(cell('$ carried')), taken=int(taken.group(1)) if taken else None,
                             boarded=int(ab.group(1)) if ab else None, van=int(van.group(1)) if van else None)
    return out


def parse_online(lines, rnd=1):
    """Round `rnd` (1-based) of a host KLHook.log -> dict(loot, taken, boarded, van, armed, summary) or None when that round never started."""
    cur, ts0, prev = 0, None, None
    r = None
    for l in lines:
        t = secs(l)
        if t is not None:
            if prev is not None and t < prev - 3600:
                t += 86400      # past midnight
            prev = t
        m = R_START.search(l)
        if m:
            cur = int(m.group(1))
            if cur == rnd:
                r = dict(loot=None, taken=None, boarded=None, van=None, armed=None, summary=False, grab_n=0, grab_sum=0, board=set())
                ts0 = t
            continue
        if cur != rnd or r is None:
            continue
        m = R_SCAN.search(l)
        if m and r['armed'] is None:
            r['armed'] = int(m.group(1))
            continue
        m = R_SUM.search(l)
        if m and not r['summary']:
            r.update(taken=int(m.group(2)), loot=int(m.group(3)), boarded=int(m.group(4)), summary=True)
            continue
        m = R_VAN.search(l)
        if m and r['van'] is None and 1 <= int(m.group(2)) <= 4 and t is not None and ts0 is not None:
            r['van'] = int(round(t - ts0))
            continue
        m = R_GRAB.search(l)
        if m:
            r['grab_n'] += 1
            r['grab_sum'] += int(m.group(1))
            continue
        m = R_BOARD.search(l)
        if m:
            r['board'].add(int(m.group(1)))
    if r is None:
        return None
    if not r['summary']:
        r['taken'], r['loot'], r['boarded'] = r['grab_n'], r['grab_sum'], len(r['board'])
    return r


def verdict(arc, onl, threshold):
    """-> (text, ratio or None)"""
    if arc is None or arc.get('loot') is None:
        return 'NO-BASELINE', None
    if onl is None:
        return 'NO-ROUND', None
    if arc['loot'] <= 0:
        return ('PASS' if (onl['loot'] or 0) >= 0 else 'BELOW'), None      # Arcade took nothing: nothing to fall behind
    ratio = (onl['loot'] or 0) / float(arc['loot'])
    return ('PASS' if ratio >= threshold else 'BELOW'), ratio


def row(name, arc, onl, log_found, threshold):
    if not log_found:
        v, ratio = 'NO-LOG', None
    else:
        v, ratio = verdict(arc, onl, threshold)
    a = arc or {}
    o = onl or {}
    note = '' if (onl is None or onl.get('summary')) else ' (no summary)'

    def n(x):
        return '-' if x is None else str(x)
    return [name, money(a.get('loot')), money(o.get('loot')), '-' if ratio is None else '%d%%' % round(ratio * 100),
            n(a.get('taken')), n(o.get('taken')) + (note if onl else ''), n(a.get('boarded')), n(o.get('boarded')),
            n(a.get('van')), n(o.get('van')), v]


def table(rows):
    out = ['| ' + ' | '.join(COLS) + ' |', '|' + '---|' * len(COLS)]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows]
    return '\n'.join(out)


def read_log(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    except OSError:
        return None


def build(arcade, logs, rnd, threshold):
    """logs: list of (map, lines or None) -> (rows, counts dict)"""
    rows, cnt = [], dict(PASS=0, BELOW=0, NOBASE=0, NOLOG=0, NOROUND=0)
    for m, ls in logs:
        onl = parse_online(ls, rnd) if ls is not None else None
        r = row(m, arcade.get(m), onl, ls is not None, threshold)
        rows.append(r)
        key = {'PASS': 'PASS', 'BELOW': 'BELOW', 'NO-BASELINE': 'NOBASE', 'NO-LOG': 'NOLOG', 'NO-ROUND': 'NOROUND'}[r[-1]]
        cnt[key] += 1
    return rows, cnt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--prefix', default='Q31')
    ap.add_argument('--solo')
    ap.add_argument('--arcade', action='append', default=[], help='baseline note(s) with the ARC table; repeat to merge ARC1 + ARC2 notes (default %s)' % os.path.basename(DEFAULT_ARCADE))
    ap.add_argument('--maps')
    ap.add_argument('--threshold', type=float, default=THRESHOLD, help='online loot / Arcade loot needed to pass (default %.2f, a judgement call)' % THRESHOLD)
    ap.add_argument('--round', type=int, default=1)
    ap.add_argument('--log', action='append', default=[], help='MAP=path of a host KLHook.log')
    a = ap.parse_args(argv)
    paths = a.arcade or [DEFAULT_ARCADE]
    arcade = {}
    for pth in paths:
        arcade.update(parse_arcade(pth))
    logs = []
    if a.log:
        for item in a.log:
            m, _, p = item.partition('=')
            logs.append((m, read_log(p)))
    else:
        solo = a.solo
        if not solo:
            from kl_arcade_baseline import default_solo
            solo = default_solo()
        maps = a.maps.split(',') if a.maps else sorted(arcade)
        for m in maps:
            logs.append((m, read_log(os.path.join(solo, '%s_%s' % (a.prefix, m), 'inst1', 'KLHook.log'))))
    rows, cnt = build(arcade, logs, a.round, a.threshold)
    print(table(rows))
    print('\nOnline = host hook tally of round %d (prefix %s); Arcade = ARC1 game records (%s, %d map(s)). PASS = online loot >= %d%% of Arcade loot '
          '(JUDGEMENT CALL, not measured). Van s = seconds after the round start to the first van state 1..4.' % (a.round, a.prefix, ', '.join(os.path.basename(x) for x in paths), len(arcade), round(a.threshold * 100)))
    found = len(rows) - cnt['NOLOG']
    print('RESULT: %s (%d PASS, %d BELOW, %d no baseline, %d no log, %d no round)' % ('OK' if found else 'NONE', cnt['PASS'], cnt['BELOW'], cnt['NOBASE'], cnt['NOLOG'], cnt['NOROUND']))
    return 0 if found else 1


if __name__ == '__main__':
    sys.exit(main())
