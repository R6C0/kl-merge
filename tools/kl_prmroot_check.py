"""kl_prmroot_check.py - every type-7 .prm model root of a level zip must point at a record start of the SAME zip's .oct.

Crash class (2026-11-10, DM01B): a tool edited the .oct, 3640 type-7 roots (64-byte chunks b'\0\1\7\0', u32 at +0x1c = the
offset of a record in the .oct, the value kl_octree Oct.record_refs() lists) kept the OLD offsets; kl2.exe died at load
(c0000005 at 0x6ad1d9 via ZCollisionBase vtable slot 34). A root with +0x1c == 0 has no .oct record and is not checked.

usage: python tools/kl_prmroot_check.py [--live] [PATH ...]
  PATH = a *_Main.zip / *_Main.bots.zip, or a folder (its *_Main*.zip are checked, not recursive).
  --live = every <DD>/KLExpansion/Maps/*/F0?_Main*.zip.
One line per zip, then 'RESULT: PASS' or 'RESULT: FAIL n' (n = zips with stale roots); exit 1 on FAIL.
A zip without .oct or .prm is 'skip'. Importable: check_zip_bytes(oct_bytes, prm_bytes) -> (roots, stale)."""
import glob
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_octree as O          # noqa: E402
import kl_prmgraph as G        # noqa: E402


def check_prm(prm_bytes, refs):
    """-> (roots, stale): type-7 roots with a non-zero +0x1c, and how many of those are not in refs."""
    pr = G.read(prm_bytes, 'dd')
    roots = [struct.unpack_from('<I', c, 0x1c)[0] for c in pr.chunks      # chunks[0] is None (the header)
             if c is not None and len(c) == 64 and c[:4] == b'\0\1\7\0']
    roots = [r for r in roots if r]
    return len(roots), sum(1 for r in roots if r not in refs)


def check_zip_bytes(oct_bytes, prm_bytes):
    """-> (roots, stale) for one level's .oct and .prm."""
    return check_prm(prm_bytes, set(O.Oct.parse(oct_bytes).record_refs()))


def _members(z):
    nm = {}
    for n in z.namelist():
        e = n.rsplit('.', 1)[-1].lower()
        if e in ('oct', 'prm'):
            nm.setdefault(e, n)
    return nm


def check_zip(path):
    """-> ('skip'|'ok'|'BAD', roots, stale)."""
    with zipfile.ZipFile(path) as z:
        nm = _members(z)
        if 'oct' not in nm or 'prm' not in nm:
            return 'skip', 0, 0
        roots, stale = check_zip_bytes(z.read(nm['oct']), z.read(nm['prm']))
    return ('BAD' if stale else 'ok'), roots, stale


def dd_dir():
    import kl_port_check as P
    return P.find(P.DD_GUESSES, P.DD_EXE)


def collect(args, live):
    out = []
    if live:
        out += sorted(glob.glob(os.path.join(dd_dir(), 'KLExpansion', 'Maps', '*', 'F0?_Main*.zip')))
    for a in args:
        out += sorted(glob.glob(os.path.join(a, '*_Main*.zip'))) if os.path.isdir(a) else [a]
    return out


def main(argv):
    live = '--live' in argv
    paths = collect([a for a in argv if a != '--live'], live)
    if not paths:
        print('nothing to check (give zips/folders or --live)')
        return 1
    bad = 0
    for p in paths:
        try:
            st, roots, stale = check_zip(p)
        except Exception as e:      # unreadable zip / unparsable member = a failure, never a silent pass
            st, roots, stale = 'BAD', 0, 0
            print('%s: ERROR %r' % (p, e))
        bad += st == 'BAD'
        print('%-5s roots %5d stale %4d  %s' % (st, roots, stale, p))
    print('RESULT: %s' % ('FAIL %d' % bad if bad else 'PASS'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
