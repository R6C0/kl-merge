"""kl_syncdiff.py - line up the 'sync:' probe lists (klhook/klsync.c, [Sync] Probe=1) of several peers and print what differs.

    python kl_syncdiff.py <KLHook.log of the host> <log of client 1> [<log of client 2> ...] [--tol 1.0] [--slots 30] [--max-dt 1500]

Each log holds blocks 'sync: list T=<ms> ...' + 'sync: s=<slot> c=<class> t=<team> p=x,y,z hp=<hp> f=<flag>' + 'sync: list end'.
Slot = entity table slot = the same object on every peer that loaded the same level. The host (first log) is the reference: for every block of
a client the host block with the closest T (within --max-dt ms) is taken. Per client it prints how many objects exist on one side only,
how many sit farther apart than --tol, how many differ in health, and the worst slots. A moving cop differs by speed x dt even when the
games agree: with the default 3 s lists and the peers on one PC (one clock) the stamps differ by well under a second; read d accordingly.
Read-only; no game files."""
import re, sys, math, collections

LIST = re.compile(r'sync: list T=(\d+)')
OBJ = re.compile(r'sync: s=(\d+) c=(\S+) t=(\S+) p=(none|[-\d.]+,[-\d.]+,[-\d.]+) hp=(\S+) f=(\S+)')


def blocks(path):
    out, cur = [], None
    with open(path, errors='replace') as f:
        for ln in f:
            m = LIST.search(ln)
            if m:
                cur = (int(m.group(1)), {})
                out.append(cur)
                continue
            if cur is None:
                continue
            m = OBJ.search(ln)
            if m:
                s, c, t, p, hp, fl = m.groups()
                pos = None if p == 'none' else tuple(float(x) for x in p.split(','))
                cur[1][int(s)] = (c, t, pos, hp, fl)
    return out


def main(argv):
    tol, nshow, maxdt, paths = 1.0, 30, 1500, []
    i = 0
    while i < len(argv):
        if argv[i] == '--tol': tol = float(argv[i + 1]); i += 2
        elif argv[i] == '--slots': nshow = int(argv[i + 1]); i += 2
        elif argv[i] == '--max-dt': maxdt = int(argv[i + 1]); i += 2
        else: paths.append(argv[i]); i += 1
    if len(paths) < 2:
        print(__doc__); return 2
    host = blocks(paths[0])
    print('host %s: %d lists' % (paths[0], len(host)))
    for pth in paths[1:]:
        cl = blocks(pth)
        tot = collections.Counter(); worst = collections.defaultdict(float); kinds = collections.Counter(); used = 0
        for T, objs in cl:
            hb = min(host, key=lambda b: abs(b[0] - T), default=None)
            if hb is None or abs(hb[0] - T) > maxdt:
                continue
            used += 1
            for s in set(objs) | set(hb[1]):
                a, b = hb[1].get(s), objs.get(s)
                if a is None or b is None:
                    tot['one side only'] += 1; kinds[(a or b)[0]] += 1; continue
                tot['compared'] += 1
                if a[2] and b[2]:
                    d = math.dist(a[2], b[2])
                    if d > tol:
                        tot['farther than tol'] += 1; kinds[a[0]] += 1
                    worst[s] = max(worst[s], d)
                elif bool(a[2]) != bool(b[2]):
                    tot['place on one side only'] += 1
                if a[3] != b[3]: tot['health differs'] += 1
        print('\n%s: %d lists, %d matched a host list (<= %d ms)' % (pth, len(cl), used, maxdt))
        for k, v in tot.items(): print('   %-26s %d' % (k, v))
        if kinds: print('   by class:', ', '.join('%s %d' % kv for kv in kinds.most_common(12)))
        for s, d in sorted(worst.items(), key=lambda kv: -kv[1])[:nshow]:
            h = next((b[1][s] for b in host if s in b[1]), None)
            print('   slot %-6d worst d=%-8.1f %s' % (s, d, h[0] if h else '?'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
