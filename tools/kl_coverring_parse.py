#!/usr/bin/env python3
"""
Offline grader for the [CoverRing] lines of KLHook.log (klhook/klcoverring.c, 2026-11-01). Reads nothing but the logs.
Written for the CR1 bench (host + client poll, DM01 / DM03) and the CR2 bench (ClientBuild) of the DM01/DM03 online
CLIENT cover asserts (re/dm_car_cover_1101.md). 2026-11-01 scheduled check-in.

    python kl_coverring_parse.py <KLHook.log>                        one seat: the LAST load's count timeline and ring table
    python kl_coverring_parse.py <host KLHook.log> --compare <client KLHook.log>
                                                                     host vs client: which cars rang on each seat, in which ORDER,
                                                                     with which indices; the host's order as a ready list; exit 3
                                                                     when the seats differ (set, order or indices), 0 when equal
    options: --load N   grade load N of the log (0 = first; default = the last one)
             --all      print every car sample, not only the first and the ring-flip ones

WHY THE ORDER IS KNOWN EXACTLY: the ring writer 0x81b6f0 takes its 8 indices from 0x558350 (eax = [L+0x68]++), so a car's
first index idx[0] IS its place in the seat's assignment order; sorting the ringed cars by idx[0] gives the host's order
without any timing guess (the poll only sees a flip within its sample period). A gap between one car's last index + 1 and
the next car's idx[0] means something ELSE took indices in between: 0x558350's only other caller is ZCreateActorCover
(0x795f22, ONE point per call), so the gap size counts runtime actor covers. Those too must come out equal on both seats
or every replicated index after them points at the wrong point on the client: the parser reports them per seat.

LINES READ (prefix 'coverring:', klcoverring.c):
  load gd=.. state=..                                        a level load (the grading unit)
  poll t+<ms>ms state=<x> L=.. real-count[+68]=<n> ... cars=<c> ring-ran=<r> ...
  poll count <a> -> <b> (delta <d>)
  car #<i> t+<ms>ms slot <s> '<name>' car=.. vt=.. script=.. n[+1c4]=<n> done[+1e8]=<d> rsv[+1e9]=<r> idx[+1c8]=[..] car+8c0=.. car+a28=..
  clientbuild GO ... / clientbuild car #<i> slot <s> '<name>' ... called 0x81b6f0: count <a> -> <b> (delta <d>) ... idx[+1c8]=[..]
  clientbuild car ... - SKIPPED / clientbuild END ... / clientbuild t+..: <gate text>
A car is keyed by its entity-table slot + name (the slot id is the same on both seats of one map zip; names can repeat,
slots cannot). 'rang' = done or rsv set in any sample of the load, or a clientbuild 'called' line.
"""
import re, sys

RE_STAMP = re.compile(r'^(\d\d):(\d\d):(\d\d)\.(\d\d\d) ')
RE_LOAD = re.compile(r'coverring: load gd=([0-9a-f]+) state=([0-9a-f]+)')
RE_POLL = re.compile(r'coverring: poll t\+(\d+)ms state=([0-9a-f]+) L=([0-9a-f]+) real-count\[\+68\]=(\d+)(.*?) points\(vec (\d+)\) cars=(\d+) ring-ran=(\d+)')
RE_POLLCNT = re.compile(r'coverring: poll count (\d+) -> (\d+) \(delta (-?\d+)\)')
RE_CAR = re.compile(r"coverring: car #(\d+) t\+(\d+)ms slot (\d+) '([^']*)' car=([0-9a-f]+) vt=([0-9a-f]+) script=([0-9a-f]+) n\[\+1c4\]=(\d+) done\[\+1e8\]=(\d+) rsv\[\+1e9\]=(\d+) idx\[\+1c8\]=\[([^\]]*)\]")
RE_CB_CALLED = re.compile(r"coverring: clientbuild car #(\d+) slot (\d+) '([^']*)' car=([0-9a-f]+) script=([0-9a-f]+) called 0x81b6f0: count (\d+) -> (\d+) \(delta (-?\d+)\) n\[\+1c4\]=(\d+) done\[\+1e8\]=(\d+) rsv\[\+1e9\]=(\d+) idx\[\+1c8\]=\[([^\]]*)\]")
RE_CB_SKIP = re.compile(r"coverring: clientbuild car #(\d+) slot (\d+) '([^']*)' .* - SKIPPED")
RE_CB_GO = re.compile(r"coverring: clientbuild GO t\+(\d+)ms slot '([^']*)' state=([0-9a-f]+) L=([0-9a-f]+) real-count\[\+68\]=(\d+) cars=(\d+)")
RE_CB_END = re.compile(r'coverring: clientbuild END cars=(\d+) eligible=(\d+) called=(\d+) real-count (\d+) -> (\d+)')
RE_CB_FAULT = re.compile(r'coverring: clientbuild car #(\d+) .*FAULT in 0x81b6f0')
RE_CB_GATE = re.compile(r'coverring: clientbuild t\+(\d+)ms state=([0-9a-f]+): (.*)$')


def _idx(s):
    s = s.strip()
    return [int(v) for v in s.split(',')] if s else []


def _stamp(ln):
    m = RE_STAMP.match(ln)
    return ln[:12] if m else ''


def read_log(path):
    """-> list of loads, oldest first. Each load = dict(gd, state, stamp, polls=[...], cars={(slot,name): [samples]}, cb=dict(...))."""
    with open(path, 'r', errors='replace') as f:
        lines = f.read().splitlines()
    loads = []
    cur = None
    for ln in lines:
        if 'coverring:' not in ln:
            continue
        m = RE_LOAD.search(ln)
        if m:
            cur = dict(gd=m.group(1), state=m.group(2), stamp=_stamp(ln), polls=[], cars={}, order=[],
                       cb=dict(go=None, called=[], skipped=[], end=None, fault=None, gates=[]), budget=False)
            loads.append(cur)
            continue
        if cur is None:
            # a ClientBuild-only run (Enable=0) logs no 'load' line: open an anonymous load on the first line
            cur = dict(gd='?', state='?', stamp=_stamp(ln), polls=[], cars={}, order=[],
                       cb=dict(go=None, called=[], skipped=[], end=None, fault=None, gates=[]), budget=False)
            loads.append(cur)
        m = RE_POLL.search(ln)
        if m:
            cur['polls'].append(dict(t=int(m.group(1)), state=m.group(2), L=m.group(3), cnt=int(m.group(4)), kind=m.group(5).strip(),
                                     vec=int(m.group(6)), cars=int(m.group(7)), ran=int(m.group(8)), stamp=_stamp(ln)))
            continue
        m = RE_CAR.search(ln)
        if m:
            key = (int(m.group(3)), m.group(4))
            if key not in cur['cars']:
                cur['cars'][key] = []
                cur['order'].append(key)
            cur['cars'][key].append(dict(t=int(m.group(2)), i=int(m.group(1)), car=m.group(5), vt=m.group(6), script=m.group(7),
                                         n=int(m.group(8)), done=int(m.group(9)), rsv=int(m.group(10)), idx=_idx(m.group(11)), stamp=_stamp(ln)))
            continue
        m = RE_CB_CALLED.search(ln)
        if m:
            cur['cb']['called'].append(dict(i=int(m.group(1)), slot=int(m.group(2)), name=m.group(3), car=m.group(4), script=m.group(5),
                                            c0=int(m.group(6)), c1=int(m.group(7)), delta=int(m.group(8)), n=int(m.group(9)),
                                            done=int(m.group(10)), rsv=int(m.group(11)), idx=_idx(m.group(12)), stamp=_stamp(ln)))
            continue
        m = RE_CB_SKIP.search(ln)
        if m:
            cur['cb']['skipped'].append(dict(i=int(m.group(1)), slot=int(m.group(2)), name=m.group(3), line=ln))
            continue
        m = RE_CB_GO.search(ln)
        if m:
            cur['cb']['go'] = dict(t=int(m.group(1)), slotkey=m.group(2), state=m.group(3), L=m.group(4), cnt=int(m.group(5)), cars=int(m.group(6)), stamp=_stamp(ln))
            continue
        m = RE_CB_END.search(ln)
        if m:
            cur['cb']['end'] = dict(cars=int(m.group(1)), eligible=int(m.group(2)), called=int(m.group(3)), c0=int(m.group(4)), c1=int(m.group(5)))
            continue
        m = RE_CB_FAULT.search(ln)
        if m:
            cur['cb']['fault'] = ln
            continue
        m = RE_CB_GATE.search(ln)
        if m:
            cur['cb']['gates'].append((int(m.group(1)), m.group(3)))
            continue
        if 'poll budget' in ln:
            cur['budget'] = True
    return loads


def pick_load(loads, which=None):
    if not loads:
        return None
    if which is None:
        return loads[-1]
    return loads[which] if 0 <= which < len(loads) else None


def rings(load):
    """-> list of dict(slot, name, first=idx[0], idx=[..], n, t_seen, how) sorted by first index: the seat's ring ASSIGNMENT ORDER.
    A car rang when any poll sample shows done or rsv set, or when a clientbuild 'called' line names it. Cars with a flag but
    no index (n == 0 and an empty idx list) are listed last with first = None (seen as rung, indices unreadable)."""
    out = []
    for key in load['order']:
        slot, name = key
        best = None
        for s in load['cars'][key]:
            if s['done'] or s['rsv']:
                if best is None:
                    best = dict(slot=slot, name=name, idx=list(s['idx']), n=s['n'], t_seen=s['t'], how='poll', done=s['done'], rsv=s['rsv'])
                elif not best['idx'] and s['idx']:
                    best['idx'] = list(s['idx']); best['n'] = s['n']
        if best is not None:
            out.append(best)
    seen = set((r['slot'], r['name']) for r in out)
    for c in load['cb']['called']:
        if (c['slot'], c['name']) in seen:
            continue
        out.append(dict(slot=c['slot'], name=c['name'], idx=list(c['idx']), n=c['n'], t_seen=None, how='clientbuild', done=c['done'], rsv=c['rsv']))
        seen.add((c['slot'], c['name']))
    for r in out:
        r['first'] = min(r['idx']) if r['idx'] else None
        r['last'] = max(r['idx']) if r['idx'] else None
    out.sort(key=lambda r: (r['first'] is None, r['first'] if r['first'] is not None else 0, r['slot']))
    return out


def base_count(load):
    """the real count at the first poll of the load (before any ring of this load), or None"""
    return load['polls'][0]['cnt'] if load['polls'] else None


def final_count(load):
    if load['cb']['end']:
        return load['cb']['end']['c1']
    return load['polls'][-1]['cnt'] if load['polls'] else None


def gaps(ringlist, base):
    """indices taken between the rings by something else (ZCreateActorCover, 1 point per call): [(after_slot_or_None, from_idx, count)].
    base = the count before the first ring (None = unknown: the first gap is not judged)."""
    out = []
    prev_end = base - 1 if base is not None else None
    prev_key = None
    for r in ringlist:
        if r['first'] is None:
            break
        if prev_end is not None and r['first'] > prev_end + 1:
            out.append((prev_key, prev_end + 1, r['first'] - prev_end - 1))
        if prev_end is not None and r['first'] <= prev_end:
            out.append((prev_key, r['first'], -(prev_end + 1 - r['first'])))      # overlap: indices shared = a misread or a re-run
        prev_end = r['last']
        prev_key = (r['slot'], r['name'])
    return out


def contiguous(r):
    """a ring's 8 indices come out consecutive from 0x558350 (nothing else runs between the 8 bumps): 1 when so"""
    if not r['idx']:
        return 0
    s = sorted(r['idx'])
    return int(s == list(range(s[0], s[0] + len(s))))


def surplus(load, ringlist):
    """final count - base - 8 * rings with indices: 0 when the rings explain the whole growth; None when unknown"""
    b, f = base_count(load), final_count(load)
    if b is None or f is None:
        return None
    return f - b - 8 * sum(1 for r in ringlist if r['first'] is not None)


def describe(load, label, every=False):
    print('%s: load gd=%s state=%s at %s: %d poll line(s), %d car(s) seen%s' % (
        label, load['gd'], load['state'], load['stamp'] or '?', len(load['polls']), len(load['cars']), ', poll budget used up' if load['budget'] else ''))
    if load['polls']:
        p0, p1 = load['polls'][0], load['polls'][-1]
        print('  count: %d at t+%dms -> %d at t+%dms (%d change(s) logged)' % (p0['cnt'], p0['t'], p1['cnt'], p1['t'], max(0, len(load['polls']) - 1)))
        if every or len(load['polls']) <= 12:
            for p in load['polls']:
                print('    t+%7dms state=%s count=%d cars=%d ring-ran=%d %s' % (p['t'], p['state'], p['cnt'], p['cars'], p['ran'], p['kind']))
    rl = rings(load)
    b = base_count(load)
    print('  rings (sorted by first index = assignment order): %d' % len(rl))
    for k, r in enumerate(rl):
        print('    %2d. slot %-5d %-40s idx %s%s%s' % (k + 1, r['slot'], "'%s'" % r['name'], r['idx'] if r['idx'] else '(none read)',
                                                      '' if contiguous(r) or not r['idx'] else '  NOT CONTIGUOUS',
                                                      '' if r['how'] == 'poll' else '  (clientbuild call)'))
    for after, frm, n in gaps(rl, b):
        if n > 0:
            print('  between rings: %d index(es) from %d taken by something else (ZCreateActorCover, 1 point each)%s' % (n, frm, '' if after is None else ' after slot %d' % after[0]))
        else:
            print('  OVERLAP: ring at %d reuses %d index(es) of the previous ring (misread or re-run)' % (frm, -n))
    sp = surplus(load, rl)
    if sp is not None:
        print('  surplus = final - base - 8 x rings = %d%s' % (sp, '' if sp == 0 else '  (indices the rings do not explain)'))
    cb = load['cb']
    if cb['go'] or cb['called'] or cb['gates'] or cb['fault']:
        print('  clientbuild: GO %s, %d called, %d skipped, END %s%s' % (
            't+%dms count %d cars %d' % (cb['go']['t'], cb['go']['cnt'], cb['go']['cars']) if cb['go'] else 'never',
            len(cb['called']), len(cb['skipped']),
            'count %d -> %d' % (cb['end']['c0'], cb['end']['c1']) if cb['end'] else 'missing', '  FAULT: ' + cb['fault'] if cb['fault'] else ''))
        for c in cb['called']:
            print("    called slot %-5d %-40s count %d -> %d (delta %d) idx %s" % (c['slot'], "'%s'" % c['name'], c['c0'], c['c1'], c['delta'], c['idx']))
        if cb['gates']:
            print('    gate: ' + '; '.join('t+%dms %s' % g for g in cb['gates'][-6:]))
    if every:
        for key in load['order']:
            for s in load['cars'][key]:
                print("    car slot %d '%s' t+%dms n=%d done=%d rsv=%d idx=%s" % (key[0], key[1], s['t'], s['n'], s['done'], s['rsv'], s['idx']))
    return rl


def compare(host, client):
    """-> (verdict, lines). verdict 0 = equal (same cars, same order, same indices, same base), 3 = divergent."""
    hr, cr = rings(host), rings(client)
    lines = []
    bad = 0
    hb, cb_ = base_count(host), base_count(client)
    if hb is not None and cb_ is not None and hb != cb_:
        lines.append('BASE COUNT differs before any ring: host %d, client %d (the compiled lists are not the same: nothing after can match)' % (hb, cb_))
        bad = 1
    hk = [(r['slot'], r['name']) for r in hr]
    ck = [(r['slot'], r['name']) for r in cr]
    hs, cs = set(hk), set(ck)
    for key in hk:
        if key not in cs:
            lines.append("HOST-ONLY ring: slot %d '%s' idx %s (the client never ran the writer for it = the client's int3 at 0x6567e8 for these indices)" % (key[0], key[1], dict(zip(hk, hr))[key]['idx']))
            bad = 1
    for key in ck:
        if key not in hs:
            lines.append("CLIENT-ONLY ring: slot %d '%s' idx %s (the host never rang it: these client indices shadow whatever the host put there)" % (key[0], key[1], dict(zip(ck, cr))[key]['idx']))
            bad = 1
    common = [k for k in hk if k in cs]
    corder = [k for k in ck if k in hs]
    if common != corder:
        lines.append('ORDER differs on the common cars: host %s, client %s' % (['%d' % k[0] for k in common], ['%d' % k[0] for k in corder]))
        bad = 1
    hd, cd = dict(zip(hk, hr)), dict(zip(ck, cr))
    for key in common:
        if hd[key]['idx'] != cd[key]['idx']:
            lines.append("INDICES differ for slot %d '%s': host %s, client %s" % (key[0], key[1], hd[key]['idx'], cd[key]['idx']))
            bad = 1
    hg, cg = gaps(hr, hb), gaps(cr, cb_)
    if [(g[1], g[2]) for g in hg] != [(g[1], g[2]) for g in cg]:
        lines.append('ACTOR-COVER GAPS differ (indices taken between rings by ZCreateActorCover): host %s, client %s' % (
            [(g[1], g[2]) for g in hg], [(g[1], g[2]) for g in cg]))
        bad = 1
    hf, cf = final_count(host), final_count(client)
    if hf is not None and cf is not None and hf != cf:
        lines.append('FINAL COUNT differs: host %d, client %d (delta %d)' % (hf, cf, hf - cf))
        bad = 1
    if not bad:
        lines.append('IDENTICAL: %d ring(s) in the same order with the same indices on both seats%s' % (
            len(hr), '' if hf is None else ', final count %d' % hf))
    if hr:
        lines.append("host order (for a per-map car list, entity-table slots in the host's assignment order): " + ','.join('%d' % r['slot'] for r in hr)
                     + '   names: ' + ' | '.join(r['name'] or '?' for r in hr))
    return (3 if bad else 0), lines


def main(argv):
    if len(argv) < 2 or argv[1] in ('-h', '--help'):
        print(__doc__)
        return 2
    path = argv[1]
    other = None
    which = None
    every = False
    i = 2
    while i < len(argv):
        a = argv[i]
        if a == '--compare':
            other = argv[i + 1]; i += 1
        elif a == '--load':
            which = int(argv[i + 1]); i += 1
        elif a == '--all':
            every = True
        else:
            print('unknown option %s' % a)
            return 2
        i += 1
    loads = read_log(path)
    load = pick_load(loads, which)
    if load is None:
        print('%s: no coverring lines (is [CoverRing] Enable=1 / ClientBuild=1 in that seat\'s ini, TEST dll?)' % path)
        return 2
    print('%s: %d load(s) with coverring lines; grading %s' % (path, len(loads), 'the last' if which is None else 'load %d' % which))
    describe(load, 'HOST' if other else 'SEAT', every)
    if not other:
        return 0
    oloads = read_log(other)
    oload = pick_load(oloads, which)
    if oload is None:
        print('%s: no coverring lines' % other)
        return 2
    print('%s: %d load(s) with coverring lines' % (other, len(oloads)))
    describe(oload, 'CLIENT', every)
    code, lines = compare(load, oload)
    print('COMPARE host vs client:')
    for ln in lines:
        print('  ' + ln)
    print('RESULT: %s' % ('IDENTICAL' if code == 0 else 'DIVERGENT (exit 3)'))
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
