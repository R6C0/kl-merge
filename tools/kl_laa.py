#!/usr/bin/env python3
r"""kl_laa.py <kl2.exe> <out exe>      a COPY of kl2.exe with the 'large address aware' flag set (4 GB instead of 2 GB
                                    of address space on 64-bit Windows). The original is only read.
    kl_laa.py <exe>                 print the flag

One bit: IMAGE_FILE_LARGE_ADDRESS_AWARE (0x20) in the PE file header's Characteristics (+22 from 'PE\0\0').
Why it may be safe: the game's integrity checks (Valve CEG, re/antitamper.md 2.1) hash .text, .rdata and .version
in memory; the header page 0x400000-0x401000 is in none of the 626 range sets read. NOT TRIED IN THE GAME
(2026-10-10). Unknowns: whether Steam verifies the file on launch (it re-downloads on 'verify files' only), and
whether the game's own code survives pointers above 2 GB (signed compares, tagged pointers).
The optional-header CheckSum is left as it is (Windows checks it for drivers only).
"""
import struct, sys, hashlib


def flag(d):
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    if d[pe:pe + 4] != b'PE\0\0':
        raise SystemExit('not a PE file')
    return pe + 22, struct.unpack_from('<H', d, pe + 22)[0]


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) not in (1, 2):
        raise SystemExit(__doc__)
    d = bytearray(open(a[0], 'rb').read())
    off, ch = flag(d)
    print('%s: Characteristics %04x, large address aware: %s, sha1 %s' % (a[0], ch, bool(ch & 0x20), hashlib.sha1(d).hexdigest()))
    if len(a) == 2:
        struct.pack_into('<H', d, off, ch | 0x20)
        open(a[1], 'wb').write(d)
        print('%s: written with the flag set (1 byte differs at file offset 0x%x), sha1 %s' % (a[1], off, hashlib.sha1(d).hexdigest()))
