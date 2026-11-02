#!/usr/bin/env python3
"""
Offline parser for the [CoverDump] lines of KLHook.log (klhook/klcoverdump.c, 2026-10-26). Reads nothing but the log (and a map zip).

    python kl_coverdump_parse.py <KLHook.log>                      counts of the LAST 'coverdump: begin' dump
    python kl_coverdump_parse.py <KLHook.log> --zip <F01_Main.zip> per *coverbox* entity: dumped points inside its footprint + MARGIN
    options: --margin M (default 60)   --yslack Y (default 300: a point counts only if its y is within the box's y range +- Y; 0 = ignore y)
             --list (print every box, default prints only a summary + the boxes WITHOUT points + 12 samples)
    python kl_coverdump_parse.py <host KLHook.log> --compare <client KLHook.log>
             host vs client cover POINT lists of a two-seat run (2026-11-01 scheduled check-in, Q33_DM01 inst2's 29 asserts): the
             LAST COMPLETE dump of each log (with [CoverDump] RoundEnd=1, 11-02, that is the points as the round ended: the load dump
             of a seat can predate its car rings, SN2 DM03 - the 'dumps' lines say which dump of each log was read), the
             BUILT points (pos not 0 0 0) of each side, the common prefix, every index that differs, and the extra points of each
             side with their places. Exit 3 when the lists diverge. Why it matters: ZSoldier's cover index travels host -> client
             by VALUE (ObjDup CallMethod -> 0x581b40 -> 0x656740 sets [soldier+0xe8] = a 16-bit point index); a point the client
             never built has flags +0x68 = 0x400 (neither 0x2 low nor 0x200 high) and the kind readers 0x6567e8 0x845a8b 0x51d049
             0x555900 0x4ede1b hit their int3 (ContinueAsserts steps over it = kind 0; MaxAsserts=200 ends the game).

The box half: kl_fa_cover.all_boxes (every entity whose name contains 'coverbox': its model's box 'bb' in local space, 'mid' in the world).
The footprint is the XZ bounding rectangle of the 8 world corners of that box (an upper bound for a rotated box; GUESS that the cover list's
point coordinates are in the same world frame as B.world, as the COVER8 'pos' lines assume). 'ours' = name contains '_K6_' (KL_CoverSix),
everything else is 'stock' (includes the map's own native boxes).
"""
import collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RE_PT = re.compile(r'coverdump: pt (\d+)\b.*?pos (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) \| \+34 (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)')
RE_REC = re.compile(r'coverdump: rec (\d+)\b')


def read_dumps(path):
    """-> [dict(head=[lines], points=[(i,x,y,z,nx,ny,nz)], recs=[line], near=[line], end=line, kind='load'|'round end')] of EVERY dump
    in the log, in log order ([] when there is none). A dump runs from its 'coverdump: begin' to the next one; 'end' is None when it was
    cut short (the game ended mid-dump). kind 'round end' = the hook's [CoverDump] RoundEnd dump (points only, taken as the round ended)."""
    with open(path, 'r', errors='replace') as f:
        lines = f.read().splitlines()
    out = []
    d = None
    for ln in lines:
        if 'coverdump:' not in ln:
            continue
        if 'coverdump: begin' in ln:
            d = dict(head=[], points=[], recs=[], near=[], end=None, other=[], kind='round end' if 'ROUND END' in ln else 'load')
            out.append(d)
        if d is None:
            continue
        m = RE_PT.search(ln)
        if m:
            d['points'].append((int(m.group(1)),) + tuple(float(m.group(k)) for k in range(2, 8)))
        elif RE_REC.search(ln):
            d['recs'].append(ln)
        elif 'coverdump: near' in ln:
            d['near'].append(ln)
        elif 'coverdump: end' in ln:
            d['end'] = ln
        else:
            d['head'].append(ln)
    return out


def pick_dump(dumps):
    """The dump to read: the LAST COMPLETE one (it has an 'end' line; a round-end dump cut by the game's exit would otherwise show every
    index it never reached as 'unbuilt' = false one-sided points), else the last one, else None."""
    if not dumps:
        return None
    done = [d for d in dumps if d['end']]
    return done[-1] if done else dumps[-1]


def read_dump(path):
    """-> the dump of pick_dump(read_dumps(path)): the last complete dump of the log (None without a 'coverdump: begin' line)."""
    return pick_dump(read_dumps(path))


def dump_label(d):
    """'load 17:38:11 1371 pts' / 'round end 17:40:00 1371 pts (CUT SHORT)' for the dumps line of --compare."""
    s = dump_secs(d)
    t = '%02d:%02d:%02d' % (int(s) // 3600, int(s) % 3600 // 60, int(s) % 60) if s is not None else '??:??:??'
    return '%s %s %d pts%s' % (d['kind'], t, len(d['points']), '' if d['end'] else ' (CUT SHORT)')


def dumps_line(name, dumps, used):
    """One line per log for --compare: every dump with its kind and time, and which one is compared."""
    return '%s: %d dump(s): %s -> compared the %s' % (name, len(dumps), '; '.join(dump_label(d) for d in dumps),
                                                         dump_label(used) if used is not None else 'none')


def boxes_of(zp):
    import kl_fa_bots as F
    import kl_fa_cover as C
    B = F.Built(os.path.normpath(os.path.abspath(zp)))
    out = []
    for b in C.all_boxes(B):
        if b['bb']:
            bb = b['bb']
            cs = [B.world(b['node'], (x, y, z)) for x in (bb[0], bb[3]) for y in (bb[1], bb[4]) for z in (bb[2], bb[5])]
        else:
            m = b['mid']
            cs = [(m[0] - 50, m[1] - 50, m[2] - 50), (m[0] + 50, m[1] + 50, m[2] + 50)]
        out.append(dict(name=b['name'], kind=b['kind'], flags=b['flags'], mid=tuple(b['mid']), has_bb=bool(b['bb']),
                        x0=min(c[0] for c in cs), x1=max(c[0] for c in cs), y0=min(c[1] for c in cs), y1=max(c[1] for c in cs),
                        z0=min(c[2] for c in cs), z1=max(c[2] for c in cs), ours='_K6_' in b['name']))
    return out


def count(boxes, points, margin, yslack):
    for b in boxes:
        b['pts'] = []
    for p in points:
        _, x, y, z = p[:4]
        for b in boxes:
            if b['x0'] - margin <= x <= b['x1'] + margin and b['z0'] - margin <= z <= b['z1'] + margin \
                    and (not yslack or b['y0'] - yslack <= y <= b['y1'] + yslack):
                b['pts'].append(p[0])
    return boxes


BLANK = (0.0, 0.0, 0.0)          # an unbuilt point: pos 0 0 0 (its +0x68 flags are 0x400 alone, +0x34 holds the array's fill pattern)


def built_points(d):
    """{index: (x, y, z)} of the points whose pos is not 0 0 0 (the ones the engine built on that machine)."""
    return {p[0]: p[1:4] for p in d['points'] if p[1:4] != BLANK}


TOL = 1.0                        # CR5 11-02: a parked car's ring points settle 0.1 unit apart on the two seats (physics jitter); the dump prints 1 decimal


def _near(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def compare(host, client, tol=TOL):
    """Compare two read_dump() results (host, client) -> dict(host_built, client_built, prefix, differ, host_extra,
    client_extra, diverge, jitter) where differ = sorted indices whose pos differs by more than tol on an axis (a missing side
    counts as blank), jitter = indices built on both within tol but not equal, prefix = the number of leading indices that
    agree (built or blank on both), *_extra = the indices built on one side only."""
    h, c = built_points(host), built_points(client)
    n = max([p[0] for p in host['points']] + [p[0] for p in client['points']] + [-1]) + 1
    neq = [i for i in range(n) if h.get(i, BLANK) != c.get(i, BLANK)]
    jitter = [i for i in neq if i in h and i in c and _near(h[i], c[i], tol)]
    differ = [i for i in neq if i not in set(jitter)]
    prefix = differ[0] if differ else n
    return dict(host_built=len(h), client_built=len(c), prefix=prefix, differ=differ, n=n, jitter=jitter,
                host_extra=sorted(i for i in h if i not in c), client_extra=sorted(i for i in c if i not in h),
                h=h, c=c, diverge=bool(differ))


def print_compare(r, host_name='host', client_name='client'):
    print('cover points: %s built %d, %s built %d (of %d dumped), lists agree for indices 0..%d' % (
        host_name, r['host_built'], client_name, r['client_built'], r['n'], r['prefix'] - 1))
    if not r['diverge']:
        j = r.get('jitter') or []
        print('RESULT: cover point lists IDENTICAL' + (' (%d point(s) within %.1f unit: %s)' % (len(j), TOL, j[:16]) if j else ''))
        return
    print('%d index(es) differ: %s%s' % (len(r['differ']), r['differ'][:24], ' ...' if len(r['differ']) > 24 else ''))
    for label, idx, pts in ((host_name + ' only', r['host_extra'], r['h']), (client_name + ' only', r['client_extra'], r['c'])):
        if idx:
            print('  built on %s (%d): %s' % (label, len(idx), ' '.join('#%d (%.0f %.0f %.0f)' % ((i,) + pts[i]) for i in idx[:16])))
    both = [i for i in r['differ'] if i in r['h'] and i in r['c']]
    if both:
        print('  built on both but at different places (%d): %s' % (len(both), both[:16]))
    lo = min(r['host_built'], r['client_built'])
    print('RESULT: cover point lists DIVERGE at index %d - a replicated ZSoldier cover index >= %d is an int3 on the side that lacks it '
          '(0x6567e8 / 0x845a8b / 0x51d049 / 0x555900 / 0x4ede1b; ContinueAsserts steps over, MaxAsserts=200 ends the game)' % (r['prefix'], lo))
    # CR9 11-02: the int3 needs an index the host built and the client did not; client-only or moved points only give a
    # different cover place (the dump has no flags, so usable vs spare is in the 'ringsync' lines, not here)
    print(safety_line(r, host_name, client_name))


def safety_line(r, host_name='host', client_name='client'):
    if r['host_extra']:
        return 'UNSAFE: %d index(es) built on %s only: %s' % (len(r['host_extra']), host_name, r['host_extra'][:16])
    return 'SAFE: no index built on %s only (%s-only %d, moved %d)' % (
        host_name, client_name, len(r['client_extra']), len([i for i in r['differ'] if i in r['h'] and i in r['c']]))


SKEW_S = 60                      # SN2 11-02: host dumped at 11:08:32 (car #0 ring not built yet), client at 11:13:48 -> a DIVERGE that was only time


def dump_secs(d):
    """Seconds of day of the dump's 'coverdump: begin' line (its HH:MM:SS.mmm stamp), or None."""
    m = re.match(r'\s*(\d\d):(\d\d):(\d\d(?:\.\d+)?)', d['head'][0] if d['head'] else '')
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def skew_line(d1, d2, limit=SKEW_S):
    """A warning when the two dumps were taken more than limit seconds apart (a car ring can be built between them), else None."""
    t1, t2 = dump_secs(d1), dump_secs(d2)
    if t1 is None or t2 is None or abs(t1 - t2) <= limit:
        return None
    return 'SKEW: the dumps are %.0f s apart (more than %d s): points built in between show as one-sided; compare dumps of the same moment' % (abs(t1 - t2), limit)


def main(argv):
    args = list(argv)
    zp = None
    cmp_log = None
    margin, yslack, full = 60.0, 300.0, '--list' in args
    for i, x in enumerate(args):
        if x == '--zip' and i + 1 < len(args):
            zp = args[i + 1]
        if x == '--compare' and i + 1 < len(args):
            cmp_log = args[i + 1]
        if x == '--margin' and i + 1 < len(args):
            margin = float(args[i + 1])
        if x == '--yslack' and i + 1 < len(args):
            yslack = float(args[i + 1])
    pos = [x for i, x in enumerate(args) if not x.startswith('--') and not (i and args[i - 1] in ('--zip', '--compare', '--margin', '--yslack'))]
    if not pos:
        print(__doc__)
        return 2
    d = read_dump(pos[0])
    if d is None:
        print('no "coverdump: begin" line in %s' % pos[0])
        return 1
    if cmp_log:
        ds1, ds2 = read_dumps(pos[0]), read_dumps(cmp_log)
        d, d2 = pick_dump(ds1), pick_dump(ds2)
        if d2 is None:
            print('no "coverdump: begin" line in %s' % cmp_log)
            return 1
        for name, dd, ds in ((pos[0], d, ds1), (cmp_log, d2, ds2)):
            print(dumps_line(name, ds, dd))
            print('%s: %s' % (name, dd['end'] or 'NO "coverdump: end" line (dump cut short?)'))
        if d['kind'] != d2['kind']:
            print('NOTE: a %s dump is compared with a %s dump: a seat whose round-end dump is missing (game ended mid-dump, RoundEnd off) is read at its load dump, which can predate the car rings' % (d['kind'], d2['kind']))
        r = compare(d, d2)
        print_compare(r)
        sk = skew_line(d, d2)
        if sk:
            print(sk)
        return 3 if r['diverge'] else 0
    for ln in d['head']:
        print(ln)
    print('records dumped: %d   points dumped: %d   near lines: %d' % (len(d['recs']), len(d['points']), len(d['near'])))
    print(d['end'] or 'NO "coverdump: end" line (dump cut short?)')
    for ln in d['near']:
        print(ln)
    if not zp:
        return 0
    boxes = count(boxes_of(zp), d['points'], margin, yslack)
    print('\n== boxes vs points (footprint + %g, y slack %g): %d coverbox entities, %d points ==' % (margin, yslack, len(boxes), len(d['points'])))
    for label, sel in (('ours (KL_CoverSix, _K6_)', [b for b in boxes if b['ours']]), ('stock / native', [b for b in boxes if not b['ours']])):
        withp = [b for b in sel if b['pts']]
        print('%-26s boxes %4d   with >=1 point %4d   without %4d   points total (a point may count for several boxes) %d'
              % (label, len(sel), len(withp), len(sel) - len(withp), sum(len(b['pts']) for b in sel)))
    claimed = {i for b in boxes for i in b['pts']}
    print('points inside NO box footprint: %d of %d' % (len(d['points']) - len(claimed), len(d['points'])))
    print('\nboxes WITHOUT points:')
    for b in boxes:
        if not b['pts']:
            print('  %-40s %s mid (%.0f %.0f %.0f) flags %#x%s' % (b['name'], 'OURS ' if b['ours'] else 'stock', *b['mid'], b['flags'] or 0, '' if b['has_bb'] else ' (no box model)'))
    print('\nboxes WITH points%s:' % ('' if full else ' (first 12 per group; --list for all)'))
    shown = collections.Counter()
    for b in boxes:
        if b['pts'] and (full or shown[b['ours']] < 12):
            shown[b['ours']] += 1
            print('  %-40s %s %3d points  e.g. %s' % (b['name'], 'OURS ' if b['ours'] else 'stock', len(b['pts']), b['pts'][:6]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
