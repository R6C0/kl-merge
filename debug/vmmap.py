"""vmmap.py <dump or map> [n]        the address space of the 32-bit game process: what is free, who holds the rest
vmmap.py <map A> <map B> [n]      ... and what is in B that was not in A (two level loads of one process)

Inputs:
  KLHook_map_<n>.txt  written by the hook (klhook/klmem.c) at every level's largest block, beside KLHook.log:
                      one line per region - base, allocation base, size, state F/C/R, type I/M/P, protection, module.
  a minidump with the region list (MiniDumpWithFullMemoryInfo, stream 16): KLHook's dumps from 2026-10-10 on.
                      The game's own kl2_490_crash_*.mdmp have none.
Why: a level's large blocks (klmem.c) failed with 134 MB free because the largest free piece was 14 MB; the free
space is cut smaller with every level PLAYED. Two maps of one process, taken at the same point of two loads, show
which allocations came in between (by size and kind) and where they sit.
n = how many rows of each list (default 12).
"""
import os, struct, sys

MB = 1048576.0
TOP = 0x7ffe0000                                           # the user half; a 64-bit dumper adds the reserved half above it


def read_map(path):
    """-> (title, [(base, allocation base, size, state 'F'/'C'/'R', type 'I'/'M'/'P'/'-', module name)])."""
    title, out = '', []
    for line in open(path, encoding='latin1'):
        w = line.split()
        if line.startswith('#'):
            title = line[1:].strip()
        elif len(w) >= 6:
            out.append((int(w[0], 16), int(w[1], 16), int(w[2], 16), w[3], w[4], ' '.join(w[6:])))
    return title, out


def read_dump(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kl
    D = kl.Dump(kl.path(path))
    d = D.d
    ns, dirrva = struct.unpack_from('<II', d, 8)
    reg, stacks = None, {}
    for i in range(ns):
        t, _sz, rva = struct.unpack_from('<III', d, dirrva + 12 * i)
        if t == 16:
            hdr, ent, n = struct.unpack_from('<IIQ', d, rva)
            reg = [struct.unpack_from('<QQIIQIIII', d, rva + hdr + ent * k) for k in range(n)]
        elif t == 3:                                       # thread list: where each stack is
            for k in range(struct.unpack_from('<I', d, rva)[0]):
                o = rva + 4 + 48 * k
                stacks[struct.unpack_from('<Q', d, o + 24)[0]] = struct.unpack_from('<I', d, o)[0]
    if reg is None:
        raise SystemExit('no region list in this dump (written without MiniDumpWithFullMemoryInfo)')
    out = []
    for base, abase, _ap, _a1, size, state, _prot, typ, _a2 in reg:
        st = 'F' if state == 0x10000 else 'C' if state == 0x1000 else 'R'
        ty = '-' if st == 'F' else 'I' if typ == 0x1000000 else 'M' if typ == 0x40000 else 'P'
        name = next((n for b, e, n in D.mods if b <= base < e), '') if ty == 'I' else ''
        if ty == 'P':
            name = next(('stack of thread %d' % tid for a, tid in stacks.items() if base <= a < base + size), '')
        out.append((base, abase, size, st, ty, name))
    return os.path.basename(path), out


def load(path):
    title, reg = read_map(path) if open(path, 'rb').read(4) != b'MDMP' else read_dump(path)
    return title, [r for r in reg if r[0] < TOP]


def allocations(reg):
    """{allocation base: [type, lowest, highest, committed, reserved only, name]}"""
    out = {}
    for base, abase, size, st, ty, name in reg:
        if st == 'F':
            continue
        a = out.setdefault(abase, [ty, base, base + size, 0, 0, ''])
        a[1], a[2] = min(a[1], base), max(a[2], base + size)
        a[3 if st == 'C' else 4] += size
        a[5] = a[5] or name
    return out


KIND = {'I': 'module', 'M': 'mapped file', 'P': 'private'}


def summary(title, reg, top):
    free = sorted((r for r in reg if r[3] == 'F'), key=lambda r: -r[2])
    print('%s' % title)
    print('  free: %.0f MB in %d pieces, largest %.1f MB' % (sum(r[2] for r in free) / MB, len(free), free[0][2] / MB if free else 0))
    for lo, hi, name in ((64, 4096, '64 MB+'), (16, 64, '16-64 MB'), (4, 16, '4-16 MB'), (1, 4, '1-4 MB'), (0, 1, 'under 1 MB')):
        g = [r[2] for r in free if lo * MB <= r[2] < hi * MB]
        print('    %-11s %5d pieces %7.1f MB' % (name, len(g), sum(g) / MB))
    print('    largest: ' + ', '.join('%08x %.1f' % (r[0], r[2] / MB) for r in free[:top]))
    al = allocations(reg)
    use = {}
    for a in al.values():
        k = KIND[a[0]] + 's' if a[0] != 'P' else 'private'
        u = use.setdefault(k, [0, 0, 0]); u[0] += 1; u[1] += a[3]; u[2] += a[4]
    print('  in use: ' + '; '.join('%s %d = %.0f MB committed + %.0f reserved only' % (k, u[0], u[1] / MB, u[2] / MB) for k, u in sorted(use.items())))
    return al


def by_span(al, keys, top, head):
    """Private allocations grouped by their span (thread stacks, heap segments ... have typical sizes)."""
    g = {}
    for b in keys:
        a = al[b]
        if a[0] == 'P':
            g.setdefault(a[2] - a[1], []).append((b, a))
    if not g:
        return
    print(head)
    for span, l in sorted(g.items(), key=lambda x: -x[0] * len(x[1]))[:top]:
        names = sorted(set(a[5] for _b, a in l if a[5]))
        print('    %8.2f MB x %4d = %7.1f MB  committed %7.1f  reserved only %7.1f  at %s%s%s' % (
            span / MB, len(l), span * len(l) / MB, sum(a[3] for _b, a in l) / MB, sum(a[4] for _b, a in l) / MB,
            ' '.join('%08x' % b for b, _a in sorted(l)[:4]), ' ...' if len(l) > 4 else '', '  (%s)' % ', '.join(names[:2]) if names else ''))


def main():
    arg = sys.argv[1:]
    top = int(arg.pop()) if arg and arg[-1].isdigit() else 12
    if not arg:
        raise SystemExit(__doc__)
    ta, ra = load(arg[0])
    aa = summary(ta, ra, top)
    if len(arg) == 1:
        by_span(aa, aa, top, '  private allocations by size, the %d that hold most:' % top)
        mods = sorted(((a[2] - a[1], a[5]) for a in aa.values() if a[0] == 'I'), reverse=True)
        print('  modules: %d, %.0f MB; largest: ' % (len(mods), sum(m[0] for m in mods) / MB) + ', '.join('%s %.0f' % (n, s / MB) for s, n in mods[:top]))
        return
    tb, rb = load(arg[1])
    ab = summary(tb, rb, top)
    new, gone = [b for b in ab if b not in aa], [b for b in aa if b not in ab]
    grown = [(b, (ab[b][2] - ab[b][1]) - (aa[b][2] - aa[b][1])) for b in ab if b in aa and ab[b][2] - ab[b][1] != aa[b][2] - aa[b][1]]
    span = lambda al, keys: sum(al[b][2] - al[b][1] for b in keys) / MB
    print('B against A: %d allocations are new (%.0f MB of address space), %d are gone (%.0f MB), %d changed size (%+.0f MB)' % (
        len(new), span(ab, new), len(gone), span(aa, gone), len(grown), sum(g for _b, g in grown) / MB))
    for ty in 'IM':
        l = sorted((b for b in new if ab[b][0] == ty), key=lambda b: -(ab[b][2] - ab[b][1]))
        if l:
            print('  new %ss: %d, %.0f MB: ' % (KIND[ty], len(l), span(ab, l)) + ', '.join('%s %.1f' % (ab[b][5] or '%08x' % b, (ab[b][2] - ab[b][1]) / MB) for b in l[:top]))
    by_span(ab, new, top, '  new private allocations by size:')
    by_span(aa, gone, top, '  private allocations that are gone, by size:')
    # where the new ones sit: how many of A's large free pieces each new allocation cut
    big = [(r[0], r[0] + r[2]) for r in ra if r[3] == 'F' and r[2] >= 16 * MB]
    cut = {}
    for b in new:
        for lo, hi in big:
            if lo <= ab[b][1] < hi:
                cut.setdefault((lo, hi), []).append(b)
    if cut:
        print('  A\'s free pieces of 16 MB or more that new allocations now sit in:')
        for (lo, hi), l in sorted(cut.items(), key=lambda x: -(x[0][1] - x[0][0]))[:top]:
            left = max((r[2] for r in rb if r[3] == 'F' and lo <= r[0] < hi), default=0)
            print('    %08x %6.1f MB: %3d new allocations, %.1f MB of them; largest free piece left in it %.1f MB (%s)' % (
                lo, (hi - lo) / MB, len(l), span(ab, l), left / MB, ', '.join(sorted(set(KIND[ab[b][0]] + ' %.2f' % ((ab[b][2] - ab[b][1]) / MB) for b in l))[:4])))


if __name__ == '__main__':
    main()
