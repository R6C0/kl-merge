#!/usr/bin/env python3
"""kl_camlog.py - summarise the camera measurement of klhook/klcam.c ([Camera] Log=1) from a KLHook.log.

Usage: python tools/kl_camlog.py KLHook.log [--from HH:MM:SS] [--to HH:MM:SS] [--csv out.csv] [--selftest]

Reads lines whose text after the 'hh:mm:ss.mmm ' stamp starts with 'cam:', 'camev:' or 'camdump:'. Tokens are
'key value' pairs found by regex; a missing token prints n/a (old logs). Time = T (seconds since start) when present,
else the clock (midnight wrap aware). Plain text output, exit code 0 always. Re: re/camera.md "Round 2".
"""
import re, sys, csv, statistics

STAMP = re.compile(r'^\s*(?:\[)?(\d\d):(\d\d):(\d\d)(?:[.,](\d+))?(?:\])?\s+(.*)$')
KV = re.compile(r'\b([A-Za-z_][\w+]*) (-?\d+(?:\.\d+)?)\b')


def clock(m):
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + (float('0.' + m.group(4)) if m.group(4) else 0.0)


def parse(lines, tfrom=None, tto=None):
    out, day, last = [], 0, None
    for ln in lines:
        m = STAMP.match(ln.rstrip('\r\n'))
        if not m:
            continue
        txt = m.group(5)
        if not txt.startswith(('cam:', 'camev:', 'camdump:')):
            continue
        c = clock(m)
        if last is not None and c < last - 3600:
            day += 1
        last = c
        c += day * 86400
        kind = txt.split(':', 1)[0]
        body = txt.split(':', 1)[1].strip()
        kv = {}
        for k, v in KV.findall(body):
            kv.setdefault(k, float(v))
        t = kv.get('T', None)
        out.append(dict(kind=kind, body=body, clock=c, T=t, kv=kv, stamp='%02d:%02d:%02d' % (int(m.group(1)), int(m.group(2)), int(m.group(3)))))
    def sec(s):
        h, mi, se = (int(x) for x in s.split(':'))
        return h * 3600 + mi * 60 + se
    if tfrom:
        out = [r for r in out if r['clock'] % 86400 >= sec(tfrom)]
    if tto:
        out = [r for r in out if r['clock'] % 86400 <= sec(tto)]
    return out


def when(r):
    return r['T'] if r['T'] is not None else r['clock']


def f(x, p=2):
    return 'n/a' if x is None else ('%.*f' % (p, x))


def med(v):
    return statistics.median(v) if v else None


def report(recs):
    L = []
    cams = [r for r in recs if r['kind'] == 'cam' and r['body'].startswith('f ')]
    evs = [r for r in recs if r['kind'] == 'camev']
    L.append('1. RUN')
    if not recs:
        L.append('  no cam:/camev: lines (is [Camera] Log=1 set, and is the test dll the one running?)')
        return L
    on = [r for r in recs if r['body'].startswith('on:')]
    if on:
        L.append('  ini: ' + on[0]['body'][3:].strip()[:300])
    L.append('  %s .. %s, %d cam: samples, %d camev: events' % (recs[0]['stamp'], recs[-1]['stamp'], len(cams), len(evs)))
    fr = [(r['kv'].get('f'), r['T']) for r in cams if r['T'] is not None and 'f' in r['kv']]
    if len(fr) > 1 and fr[-1][1] > fr[0][1]:
        L.append('  frame rate estimate (game frames per second): %.1f' % ((fr[-1][0] - fr[0][0]) / (fr[-1][1] - fr[0][1])))
    hit = sorted(((r['kv'].get('rdt', 0), r) for r in evs if r['body'].startswith('HITCH')), key=lambda x: x[0])
    L.append('  HITCH events (frame time > 0.1 s): %d; worst: %s' % (len(hit), ', '.join('%.2f s at %s' % (h, r['stamp']) for h, r in hit[-10:][::-1]) or 'none'))
    gaps = [r for r in evs if r['body'].startswith('GAP')]
    L.append('  GAP events (wall time between ticks > 0.25 s): %d%s' % (len(gaps), ' (worst %.2f s)' % max(r['kv'].get('wall', 0) for r in gaps) if gaps else ''))
    skips = {}
    for r in evs:
        m = re.match(r'SKIP (\S+) ends after ([\d.]+)', r['body'])
        if m:
            s = skips.setdefault(m.group(1), [0, 0.0]); s[0] += 1; s[1] += float(m.group(2))
    L.append('  SKIP reasons: ' + (', '.join('%s x%d %.1f s' % (k, v[0], v[1]) for k, v in skips.items()) or 'none'))

    L.append('2. STUCK / LAG')
    eps, cur = [], {}
    for r in evs:
        b = r['body']
        for nm in ('STUCK2', 'LAG2'):
            if b.startswith(nm + ' begins'):
                cur[nm] = r
            elif b.startswith(nm + ' ends') and nm in cur:
                s = cur.pop(nm)
                fz = re.search(r'frozen=(\S*)', b) or re.search(r'frozen=(\S*)', s['body'])
                eps.append(dict(nm=nm, start=s, end=r, dur=r['kv'].get('after', 0), frozen=fz.group(1) if fz else '', ch=(b.split('changed:', 1) + [''])[1].strip()))
    for nm, s in cur.items():
        eps.append(dict(nm=nm, start=s, end=None, dur=None, frozen='', ch='(open at the end of the log)'))
    marks = [r for r in evs if r['body'].startswith('MARK')]
    if not eps:
        L.append('  no STUCK2 / LAG2 episode')
    for e in eps:
        s = e['start']; t0 = when(s)
        near = [h for h, r in hit if 0 <= t0 - when(r) <= 1.0]
        L.append('  %s at %s T %s lasts %s s frozen=%s %s%s' % (e['nm'], s['stamp'], f(s['T']), f(e['dur']), e['frozen'] or '-', ('changed:' + e['ch']) if e['ch'] else '',
                 ' [a hitch %.2f s lay within 1 s before]' % max(near) if near else ''))
        mv = re.search(r'mv (-?\d+)', s['body'])
        if mv:
            L.append('      mv %s%s' % (mv.group(1), ' ' + re.search(r'blk.*', s['body']).group(0)[:100] if re.search(r'blk.*', s['body']) else ''))
    causes = {}
    for e in eps:
        if e['nm'] == 'STUCK2':
            causes[e['frozen']] = causes.get(e['frozen'], 0) + 1
    if causes:
        L.append('  cause table (STUCK2 by frozen field set): ' + ', '.join('%s x%d' % (k or '-', v) for k, v in sorted(causes.items(), key=lambda kv: -kv[1])))
    for mk in marks:
        t0 = when(mk)
        best = min(eps, key=lambda e: abs(when(e['start']) - t0), default=None)
        L.append('  F9 %s at %s: nearest episode %s' % (mk['body'].split('|')[0].strip(), mk['stamp'],
                 'none' if not best else '%s %.1f s away' % (best['nm'], abs(when(best['start']) - t0))))

    L.append('3. CHASE')
    byprof = {}
    for r in cams:
        pm = re.search(r'prof ([0-9a-f]{8})', r['body'])
        if not pm:
            continue
        kv = r['kv']
        if kv.get('vE', 0) > 5 and kv.get('dPiv') is not None:
            byprof.setdefault(pm.group(1), []).append((kv['dPiv'] / kv['vE'], kv.get('k590'), kv.get('k594'), kv.get('slow')))
    if not byprof:
        L.append('  no moving samples')
    for p, v in byprof.items():
        L.append('  profile %s: tau median %s max %s s (%d samples); k590 median %s k594 median %s slow median %s' % (p, f(med([x[0] for x in v]), 3), f(max(x[0] for x in v), 3), len(v),
                 f(med([x[1] for x in v if x[1] is not None]), 3), f(med([x[2] for x in v if x[2] is not None]), 3), f(med([x[3] for x in v if x[3] is not None]), 3)))
    bl = [r['kv'].get('end') for r in evs if r['body'].startswith('BLEND end')]
    bl = [r['kv'].get('after') for r in evs if r['body'].startswith('BLEND end')]
    L.append('  BLEND achieved: %d, median %s s, max %s s' % (len(bl), f(med(bl)), f(max(bl) if bl else None)))

    L.append('4. SHOULDER / COVER')
    sh = [r for r in evs if re.match(r'(KEY X|shoulder|SWAP|LEAN|COVER|SIDEBLEND|KEY X gates)', r['body'])]
    if not sh:
        L.append('  no shoulder / cover events')
    for r in sh:
        L.append('  %s %s' % (r['stamp'], r['body'][:230]))
    nokey = sum(1 for r in evs if r['body'].startswith('shoulder key in cover: the side bit did not change'))
    leanfail = sum(1 for r in evs if r['body'].startswith('LEAN FAILED') or r['body'].startswith('LEAN did not follow'))
    L.append('  swaps with no change: %d; lean write did not follow: %d' % (nokey, leanfail))

    L.append('5. AIM')
    keys = [r for r in evs if re.match(r'KEY RMB', r['body'])]
    fov = [r for r in evs if r['body'].startswith('FOV')]
    ey = [r for r in evs if r['body'].startswith('EYE settled')]
    L.append('  RMB edges %d, FOV settle events %d (median %s s), EYE settle events %d (median %s s)' % (
        len(keys), len(fov), f(med([r['kv'].get('after') for r in fov if r['kv'].get('after') is not None])),
        len(ey), f(med([r['kv'].get('after') for r in ey if r['kv'].get('after') is not None]))))
    for r in fov[:20]:
        L.append('  %s %s' % (r['stamp'], r['body'][:200]))

    L.append('6. VERDICT')
    n_st = sum(1 for e in eps if e['nm'] == 'STUCK2')
    if n_st:
        top = max(causes.items(), key=lambda kv: kv[1])
        L.append('  %d stuck episode(s); most are frozen=%s (%d)' % (n_st, top[0] or '-', top[1]))
        if 'EYE' in top[0] and 'PIV' not in top[0]:
            L.append('  -> the eye is frozen while the pivot moves: check the tick gate / owner pointer (camev: GATE / TARGET lines) and the filter substep (FILTER lines)')
        if 'PIV' in top[0]:
            L.append('  -> the pivot itself is frozen: upstream of the chase (target / cut), not the filter')
    else:
        L.append('  no stuck episode logged')
    if marks:
        near_h = sum(1 for mk in marks if any(0 <= when(mk) - when(r) <= 3 for h, r in hit))
        L.append('  hitches explain %d of %d F9 marks (hitch within 3 s before)' % (near_h, len(marks)))
    if gaps or hit:
        L.append('  %d hitch(es) and %d gap(s): a freeze that coincides is a frame-time problem (UnstickFilter), not a camera field' % (len(hit), len(gaps)))
    return L


def write_csv(recs, path):
    cams = [r for r in recs if r['kind'] == 'cam' and r['body'].startswith('f ')]
    cols = []
    for r in cams:
        for k in r['kv']:
            if k not in cols:
                cols.append(k)
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['stamp'] + cols)
        for r in cams:
            w.writerow([r['stamp']] + [r['kv'].get(k, '') for k in cols])


SELF = """\
10:00:00.000 cam: on: Blend 0 Unstick 0 Log 1
10:00:01.000 cam: f 100 dt 0.0160 | P 1 2 3 vP 300 | eye 1 2 3 vE 250 node 1 2 3 | piv398 1 2 3 dPiv 50.0 | blend 0.00 | prof 0154b810 t 1/2/3 fov 1.0 | T 1.00 rdt 0.0160 mv 2 k590 0.5 k594 0.4 slow 1.0
10:00:02.000 camev: HITCH rdt 1.800 s | f 120 T 2.00
10:00:03.000 camev: STUCK2 begins frozen=EYE | f 130 T 3.00 rdt 0.0160 | P 1 2 3 mv 2 kind 02 a54 0000 | blk 0
10:00:04.500 camev: STUCK2 ends after 1.50 s frozen=EYE | f 200 T 4.50 | changed: tick
10:00:05.000 camev: MARK 1 | f 210 T 5.00 | x
10:00:06.000 camev: KEY X down | f 220 T 6.00 | cs 1
10:00:06.500 camev: shoulder swapped in cover: side bit 0 -> 1
10:00:07.000 camev: SKIP GATE4CD8 begins | T 7.00 a 00000001 b 0
10:00:08.000 camev: SKIP GATE4CD8 ends after 1.00 s | T 8.00
10:00:09.000 camev: BLEND end after 0.80 s (prof 0154b810(default)) | f 300 T 9.00
10:00:10.000 camev: FOV 1.000 -> 0.800 settled after 0.30 s since RMB down | f 310 T 10.00
10:00:11.000 camev: GAP wall 0.400 s since the last tick | T 11.00
"""


def selftest():
    recs = parse(SELF.splitlines())
    assert len(recs) == 13, len(recs)
    txt = '\n'.join(report(recs))
    assert 'HITCH events (frame time > 0.1 s): 1' in txt, txt
    assert 'STUCK2 at 10:00:03' in txt and 'frozen=EYE' in txt, txt
    assert 'GATE4CD8 x1 1.0 s' in txt, txt
    assert 'hitches explain 0 of 1' in txt or 'hitches explain 1 of 1' in txt, txt
    assert 'GAP events (wall time between ticks > 0.25 s): 1' in txt, txt
    assert parse(['garbage', '10:00:00 other: x']) == []
    print('selftest ok')


def main(argv):
    if '--selftest' in argv:
        selftest(); return 0
    args = [a for a in argv if not a.startswith('--')]
    opt = lambda n: argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else None
    for n in ('--from', '--to', '--csv'):
        v = opt(n)
        if v in args:
            args.remove(v)
    if not args:
        print(__doc__); return 0
    with open(args[0], encoding='cp1252', errors='replace') as fh:
        recs = parse(fh, opt('--from'), opt('--to'))
    print('\n'.join(report(recs)))
    if opt('--csv'):
        write_csv(recs, opt('--csv'))
        print('csv written: ' + opt('--csv'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
