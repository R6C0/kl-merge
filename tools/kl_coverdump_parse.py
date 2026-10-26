#!/usr/bin/env python3
"""
Offline parser for the [CoverDump] lines of KLHook.log (klhook/klcoverdump.c, 2026-10-26). Reads nothing but the log (and a map zip).

    python kl_coverdump_parse.py <KLHook.log>                      counts of the LAST 'coverdump: begin' dump
    python kl_coverdump_parse.py <KLHook.log> --zip <F01_Main.zip> per *coverbox* entity: dumped points inside its footprint + MARGIN
    options: --margin M (default 60)   --yslack Y (default 300: a point counts only if its y is within the box's y range +- Y; 0 = ignore y)
             --list (print every box, default prints only a summary + the boxes WITHOUT points + 12 samples)

The box half: kl_fa_cover.all_boxes (every entity whose name contains 'coverbox': its model's box 'bb' in local space, 'mid' in the world).
The footprint is the XZ bounding rectangle of the 8 world corners of that box (an upper bound for a rotated box; GUESS that the cover list's
point coordinates are in the same world frame as B.world, as the COVER8 'pos' lines assume). 'ours' = name contains '_K6_' (KL_CoverSix),
everything else is 'stock' (includes the map's own native boxes).
"""
import collections, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RE_PT = re.compile(r'coverdump: pt (\d+)\b.*?pos (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) \| \+34 (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)')
RE_REC = re.compile(r'coverdump: rec (\d+)\b')


def read_dump(path):
    """-> dict(head=[lines], points=[(i,x,y,z,nx,ny,nz)], recs=[line], near=[line], end=line) of the last dump."""
    with open(path, 'r', errors='replace') as f:
        lines = f.read().splitlines()
    start = None
    for i, ln in enumerate(lines):
        if 'coverdump: begin' in ln:
            start = i
    if start is None:
        return None
    d = dict(head=[], points=[], recs=[], near=[], end=None, other=[])
    for ln in lines[start:]:
        if 'coverdump:' not in ln:
            continue
        if 'coverdump: begin' in ln and ln is not lines[start]:
            break
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
    return d


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


def main(argv):
    a = [x for x in argv if not x.startswith('--')]
    opt = {}
    k = 0
    args = list(argv)
    zp = None
    margin, yslack, full = 60.0, 300.0, '--list' in args
    for i, x in enumerate(args):
        if x == '--zip' and i + 1 < len(args):
            zp = args[i + 1]
        if x == '--margin' and i + 1 < len(args):
            margin = float(args[i + 1])
        if x == '--yslack' and i + 1 < len(args):
            yslack = float(args[i + 1])
    pos = [x for i, x in enumerate(args) if not x.startswith('--') and not (i and args[i - 1] in ('--zip', '--margin', '--yslack'))]
    if not pos:
        print(__doc__)
        return 2
    d = read_dump(pos[0])
    if d is None:
        print('no "coverdump: begin" line in %s' % pos[0])
        return 1
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
