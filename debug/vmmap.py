"""vmmap.py <dump> [n]   the address space of a 32-bit process from a minidump's region list.

Needs a dump written with MiniDumpWithFullMemoryInfo (stream 16, MemoryInfoListStream): KLHook's dumps
have it from 2026-10-10 on (klhook.c write_dump), the game's own kl2_490_crash_*.mdmp do not.
Prints what is free (by piece size, and the n largest pieces, default 12), what is in use by kind
(modules, mapped files, private committed, private reserved only) and the n largest allocations of each
private kind, with the module or thread stack they belong to where the dump tells. This answers 'why
did a 26 MB block find no place with 134 MB free' (klhook/klmem.c): which allocations cut the space.
"""
import struct, sys
import kl

MB = 1048576.0
FREE, COMMIT, RESERVE = 0x10000, 0x1000, 0x2000
IMAGE, MAPPED, PRIVATE = 0x1000000, 0x40000, 0x20000


def regions(d):
    """[(base, allocation base, size, state, type)] of stream 16, or None without one."""
    ns, dirrva = struct.unpack_from('<II', d, 8)
    for i in range(ns):
        t, sz, rva = struct.unpack_from('<III', d, dirrva + 12 * i)
        if t == 16:
            hdr, ent, n = struct.unpack_from('<IIQ', d, rva)
            out = []
            for k in range(n):
                base, abase, _, _, size, state, _, typ, _ = struct.unpack_from('<QQIIQIIII', d, rva + hdr + ent * k)
                out.append((base, abase, size, state, typ))
            return out
    return None


def stacks(d):
    """{address inside a thread's stack: thread id} from the thread list (stream 3)."""
    ns, dirrva = struct.unpack_from('<II', d, 8)
    out = {}
    for i in range(ns):
        t, sz, rva = struct.unpack_from('<III', d, dirrva + 12 * i)
        if t == 3:
            for k in range(struct.unpack_from('<I', d, rva)[0]):
                o = rva + 4 + 48 * k
                out[struct.unpack_from('<Q', d, o + 24)[0]] = struct.unpack_from('<I', d, o)[0]
    return out


def main():
    D = kl.Dump(kl.path(sys.argv[1]))
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    reg = regions(D.d)
    if reg is None:
        raise SystemExit('no region list in this dump (written without MiniDumpWithFullMemoryInfo)')
    reg = [r for r in reg if r[0] < 0x7ffe0000]            # the user half; a 64-bit dumper adds the reserved half above it
    st = stacks(D.d)
    free = sorted((r for r in reg if r[3] == FREE), key=lambda r: -r[2])
    print('free: %.0f MB in %d pieces, largest %.1f MB' % (sum(r[2] for r in free) / MB, len(free), free[0][2] / MB if free else 0))
    for lo, hi, name in ((64, 4096, '64 MB+'), (16, 64, '16-64 MB'), (4, 16, '4-16 MB'), (1, 4, '1-4 MB'), (0, 1, 'under 1 MB')):
        g = [r[2] for r in free if lo * MB <= r[2] < hi * MB]
        print('  %-11s %5d pieces %7.1f MB' % (name, len(g), sum(g) / MB))
    print('  largest: ' + ', '.join('%08x %.1f' % (r[0], r[2] / MB) for r in free[:top]))
    kinds = {'modules': 0, 'mapped files': 0, 'private committed': 0, 'private reserved only': 0}
    alloc = {}                                             # allocation base -> [committed, reserved only, type, lowest, highest]
    for base, abase, size, state, typ in reg:
        if state == FREE:
            continue
        k = 'modules' if typ == IMAGE else 'mapped files' if typ == MAPPED else 'private committed' if state == COMMIT else 'private reserved only'
        kinds[k] += size
        a = alloc.setdefault(abase, [0, 0, typ, base, base + size])
        a[0 if state == COMMIT else 1] += size
        a[3], a[4] = min(a[3], base), max(a[4], base + size)
    print('in use: ' + ', '.join('%s %.0f MB' % (k, v / MB) for k, v in kinds.items()) + '; %d allocations' % len(alloc))

    def owner(lo, hi):
        for b, e, n in D.mods:
            if b < hi and lo < e:
                return n
        for a, tid in st.items():
            if lo <= a < hi:
                return 'stack of thread %d' % tid
        return ''
    priv = [(b, a) for b, a in alloc.items() if a[2] == PRIVATE]
    sizes = {}
    for b, a in priv:                                      # how many private allocations of each size (stacks, heap segments ...)
        sizes.setdefault(a[4] - a[3], []).append(a)
    print('private allocations by size (span, count, committed MB, reserved-only MB), the %d that hold most:' % top)
    for span, g in sorted(sizes.items(), key=lambda x: -x[0] * len(x[1]))[:top]:
        print('  %8.2f MB x %4d  committed %7.1f  reserved only %7.1f  %s' % (span / MB, len(g), sum(a[0] for a in g) / MB, sum(a[1] for a in g) / MB,
                                                                              owner(g[0][3], g[0][4])))
    print('the %d largest private allocations:' % top)
    for b, a in sorted(priv, key=lambda x: -(x[1][4] - x[1][3]))[:top]:
        print('  %08x %8.2f MB  committed %7.1f  reserved only %7.1f  %s' % (b, (a[4] - a[3]) / MB, a[0] / MB, a[1] / MB, owner(a[3], a[4])))
    mods = sorted(((e - b, n) for b, e, n in D.mods if b < 0x80000000), reverse=True)
    print('modules: %d, %.0f MB; largest: ' % (len(mods), sum(m[0] for m in mods) / MB) + ', '.join('%s %.0f' % (n, s / MB) for s, n in mods[:top]))


if __name__ == '__main__':
    main()
