#!/usr/bin/env python3
"""
kl_arcade_baseline.py - the OFFLINE ARCADE baseline of the AI heisters, per map, from the KLHook.log of the ARC1 bench
(re/bots_online_scorecard_1101.md 'Read this first': no Arcade per-map baseline existed).

    python tools/kl_arcade_baseline.py [--solo <dir of ARC1_<MAP> folders>] [--tag ARC1] [--maps DD01,DD02,...] [--round N]
    python tools/kl_arcade_baseline.py --log <KLHook.log> [--log ...]

Reads the lines [BotFill] ArcadeProbe=1 writes (klhook/klbotfill.c klbf_ap_run), all prefixed 'arcadeprobe:':
    round start: Arcade level L, R crew record(s), A AI (flags&1), clock left C s, van state V
    stacks at +5 s: N armed, M behind a shut door, $S armed in all, K followed
    van state X -> Y at +T s (clock left C s, timer t)
    bot I status X -> 4 ABOARD at +T s ...        bot I status X -> 7 DEAD at +T s ...
    tactics: round summary: N bot(s) (AI crew records), S stack(s) taken, T total (AI record money peak, ...), B boarded, G stack(s) never emptied | van call s V, D dead, ...
Prints one row per map in the column order of the online scorecard table (round 1 by default); a column Arcade
cannot give (the online hook's far-counted boardall credits, get-up orders, trigger FIREs) is '-'.
Round N of a log that has no summary (bench stopped inside the round) is reported from its census / van / bot lines with
'(no summary)'. Reads only. Exit 0 always (a table, not a verdict); 1 when nothing was found.
"""
import argparse, collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MAPS = ['DD01', 'DD02', 'DD03', 'DD04', 'DD05', 'DD06', 'DD07', 'DD08', 'DD09', 'DM01', 'DM06']
COLS = ['Map', 'Bots', 'Armed stacks', 'Stacks taken', '$ carried', 'Van call s (why)', 'Aboard / bots', 'Far-counted',
        'Dead', 'Stack never emptied', 'Get-up down / sent / up s', 'Trigger FIREs']

R_START = re.compile(r'arcadeprobe: round start: Arcade level (\d+), (\d+) crew record\(s\), (\d+) AI \(flags&1\), clock left (-?\d+) s, van state (\d+)')
R_CENSUS = re.compile(r'arcadeprobe: stacks at \+5 s: (\d+) armed, (\d+) behind a shut door, \$(-?\d+) armed in all, (\d+) followed')
R_VAN = re.compile(r'arcadeprobe: van state (\d+) -> (\d+) at \+(\d+) s \(clock left (-?\d+) s')
R_BOT = re.compile(r'arcadeprobe: bot (\d+) status (\d+) -> (\d+)(?: ABOARD| DEAD)? at \+(\d+) s')
R_SUM = re.compile(r'arcadeprobe: tactics: (round|interim) summary: (\d+) bot\(s\) \(AI crew records\), (\d+) stack\(s\) taken, (-?\d+) total .*?, (\d+) boarded, (\d+) stack\(s\) never emptied'
                   r' \| van call s (\d+|none), (\d+) dead')
# the hook's own box fires (klbotfill.c klbf_trig_tick / klbf_trig_other): 'FIRE box ...' = ZTriggerBox, else the class name. DRY lines are not fires.
# NOTE: a FIRE line is counted for the round whose start line (R_START) came before it. A FIRE line BEFORE the first round-start line (or in the gap before
# the next round's start line, which is attributed to the previous round) is NOT counted for the right round / not at all: the Trigger FIREs column can undercount.
R_FIRE = re.compile(r'botfill: trig: FIRE (box|ZTriggerBox2|ZOnlineTriggerBox) ')
R_FATAL = re.compile(r'FATAL|CRASH|assert', re.I)


def parse(lines):
    """-> list of rounds, each a dict (keys: bots, level, armed, door, taken, total, van_call, why, boarded, dead, never, summary, faults)."""
    rounds, cur = [], None
    faults = sum(1 for l in lines if R_FATAL.search(l) and 'arcadeprobe' not in l)
    for l in lines:
        m = R_START.search(l)
        if m:
            if cur is not None:
                rounds.append(cur)
            cur = dict(level=int(m.group(1)), bots=int(m.group(3)), armed=None, door=None, taken=None, total=None, van_call=None,
                       why='', boarded=set(), dead=set(), never=None, summary=False, clock=int(m.group(4)), fires=collections.Counter())
            continue
        m = R_FIRE.search(l)
        if m and cur is not None:
            cur['fires'][{'box': 'TriggerBox'}.get(m.group(1), m.group(1)[1:])] += 1
            continue
        if cur is None:
            continue
        m = R_CENSUS.search(l)
        if m:
            cur['armed'], cur['door'] = int(m.group(1)), int(m.group(2))
            continue
        m = R_VAN.search(l)
        if m:
            if cur['van_call'] is None and 1 <= int(m.group(2)) <= 4:
                cur['van_call'] = int(m.group(3))
                cur['why'] = 'clock left %s' % m.group(4)
            continue
        m = R_BOT.search(l)
        if m:
            if m.group(3) == '4':
                cur['boarded'].add(int(m.group(1)))
            elif m.group(3) == '7':
                cur['dead'].add(int(m.group(1)))
            continue
        m = R_SUM.search(l)
        if m:
            final = m.group(1) == 'round'
            cur.update(bots=int(m.group(2)), taken=int(m.group(3)), total=int(m.group(4)), never=int(m.group(6)), summary=final)
            cur['boarded_n'] = int(m.group(5))
            cur['dead_n'] = int(m.group(8))
            if m.group(7) != 'none':
                cur['van_call'] = int(m.group(7))
                if not cur['why']:
                    cur['why'] = 'from summary'
            if final:
                rounds.append(cur)
                cur = None
    if cur is not None:
        rounds.append(cur)
    for r in rounds:
        r['faults'] = faults
        r.setdefault('boarded_n', len(r['boarded']))
        r.setdefault('dead_n', len(r['dead']))
    return rounds


def money(v):
    return '-' if v is None else ('0' if v == 0 else '%.2fM' % (v / 1e6))


def fires_cell(r):
    """Trigger FIREs of a round: the hook's 'trig: FIRE' lines. OFFLINE Arcade the game's own census fires the boxes (0x7f6850 counts the Ally bots)
    and the hook's OnlineTriggers stays idle (host-only), so the log holds none: 0 here is 'the game fires, not counted', NOT 'no box fired'."""
    f = r.get('fires')
    if not f:
        return '0 (Arcade: game fires, not logged)'
    return '%d (%s)' % (sum(f.values()), ', '.join('%s %d' % kv for kv in sorted(f.items())))


def row(name, r):
    if r is None:
        return [name, 'no ArcadeProbe round'] + ['-'] * (len(COLS) - 2)
    armed = '-' if r['armed'] is None else ('%d (+%d behind shut door)' % (r['armed'], r['door']) if r['door'] else '%d' % r['armed'])
    van = 'none' if r['van_call'] is None else '%d%s' % (r['van_call'], ' (%s)' % r['why'] if r['why'] else '')
    taken = '-' if r['taken'] is None else str(r['taken'])
    if not r['summary']:
        taken += ' (no summary)'
    return [name, str(r['bots']), armed, taken, money(r['total']), van, '%d / %d' % (r['boarded_n'], r['bots']),
            '-', str(r['dead_n']), '-' if r['never'] is None else str(r['never']), '-', fires_cell(r)]


def table(rows):
    out = ['| ' + ' | '.join(COLS) + ' |', '|' + '---|' * len(COLS)]
    for r in rows:
        out.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(out)


def read_log(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    except OSError:
        return None


def default_solo():
    try:
        from kl_port_check import workdir
        return os.path.join(workdir(), 'build', 'klhook', 'solo')
    except Exception:
        return os.path.join('G:\\', 'SteamLibrary', 'steamapps', 'common', 'Kane and Lynch Dead Men', 'KL_PortTools', 'build', 'klhook', 'solo')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo')
    ap.add_argument('--tag', default='ARC1')
    ap.add_argument('--maps', default=','.join(MAPS))
    ap.add_argument('--round', type=int, default=1, help='1-based round to report (default 1)')
    ap.add_argument('--log', action='append', default=[])
    a = ap.parse_args(argv)
    rows, found = [], 0
    if a.log:
        for p in a.log:
            ls = read_log(p)
            rs = parse(ls) if ls is not None else []
            r = rs[a.round - 1] if len(rs) >= a.round else None
            found += r is not None
            rows.append(row(os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(p)))) or p, r))
    else:
        solo = a.solo or default_solo()
        for m in a.maps.split(','):
            p = os.path.join(solo, '%s_%s' % (a.tag, m), 'inst1', 'KLHook.log')
            ls = read_log(p)
            rs = parse(ls) if ls is not None else []
            r = rs[a.round - 1] if len(rs) >= a.round else None
            found += r is not None
            rows.append(row(m if ls is not None else m + ' (no log)', r))
    print(table(rows))
    print('\nArcade baseline, round %d, offline one seat, game record fields (not a hook tally). Aboard = crew records with status 4 (ABOARD); $ carried = '
          'sum of each AI record\'s highest money field; Stacks never emptied = followed armed stacks still not at 0 at the round end; Trigger FIREs = the hook\'s own "trig: FIRE" lines in the round (an online log has them; an Arcade log cannot, the game fires there).' % a.round)
    print('RESULT: %s (%d of %d map(s) with an ArcadeProbe round)' % ('OK' if found else 'NONE', found, len(rows)))
    return 0 if found else 1


if __name__ == '__main__':
    sys.exit(main())
