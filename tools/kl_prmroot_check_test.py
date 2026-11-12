r"""kl_prmroot_check_test.py - off-game checks of kl_prmroot_check.py. Run: python kl_prmroot_check_test.py
Synthetic .prm (hand-built chunk table) + a synthetic zip without .oct (skip); the real-.oct part runs on a live
<DD>\KLExpansion\Maps zip when present (stale root made in memory) and SKIPs otherwise."""
import glob
import io
import os
import struct
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_octree as O              # noqa: E402
import kl_prmgraph as G            # noqa: E402
import kl_prmroot_check as R       # noqa: E402

fails = 0


def check(ok, what):
    global fails
    print(('  ok   ' if ok else '  FAIL ') + what)
    if not ok:
        fails += 1


def root(off):
    c = bytearray(64)
    c[:4] = b'\0\1\7\0'
    struct.pack_into('<I', c, 0x1c, off)
    return bytes(c)


def prm(chunks):
    return G.write(G.Prm('dd', [None] + list(chunks), [1] * (len(chunks) + 1)))


# synthetic: refs {101, 205}; roots 101, 205 good, 0 ignored, a 32-byte chunk and a non-root 64-byte chunk ignored
good = prm([root(101), root(205), root(0), b'\0\1\7\0' + bytes(28), bytes(64)])
check(R.check_prm(good, {101, 205}) == (2, 0), 'good: 2 roots, 0 stale')
bad = prm([root(101), root(206), root(999)])
check(R.check_prm(bad, {101, 205}) == (3, 2), 'stale: 3 roots, 2 stale')
check(R.check_prm(prm([]), set()) == (0, 0), 'empty table: 0 roots')

# zips: no .oct -> skip; a path through main() prints RESULT
d = tempfile.mkdtemp()
p = os.path.join(d, 'F01_Main.zip')
with zipfile.ZipFile(p, 'w') as z:
    z.writestr('F01_Main.prm', good)
check(R.check_zip(p)[0] == 'skip', 'zip without .oct: skip')
check(R.main([p]) == 0, 'skip alone does not fail')
check(R.main([os.path.join(d, 'nothing')]) == 1, 'unreadable path fails')

# real .oct: refs of a live zip; roots = its own good ones, then one shifted by 4
live = sorted(glob.glob(os.path.join(os.environ.get('KL_DD', r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'),
                                     'KLExpansion', 'Maps', '*', 'F0?_Main.zip')))
src = None
for lp in live:
    try:
        with zipfile.ZipFile(lp) as z:
            nm = R._members(z)
            if 'oct' in nm and 'prm' in nm:
                src = z.read(nm['oct'])
                break
    except Exception:
        pass
if src is None:
    print('  SKIP real-.oct part: no live zip with .oct/.prm')
else:
    refs = O.Oct.parse(src).record_refs()
    pg = prm([root(refs[0]), root(refs[-1])])
    pb = prm([root(refs[0]), root(refs[-1] + 4)])
    check(R.check_zip_bytes(src, pg) == (2, 0), 'real .oct, good roots: PASS')
    check(R.check_zip_bytes(src, pb) == (2, 1), 'real .oct, one stale root: FAIL')
    for nm_, prmb, want in (('good', pg, 0), ('stale', pb, 1)):
        zp = os.path.join(d, nm_ + '_Main.zip')
        with zipfile.ZipFile(zp, 'w') as z:
            z.writestr('F01_Main.oct', src)
            z.writestr('F01_Main.prm', prmb)
        check(R.check_zip(zp)[0] == ('BAD' if want else 'ok'), 'zip %s -> %s' % (nm_, 'BAD' if want else 'ok'))
    check(R.main([os.path.join(d, 'stale_Main.zip')]) == 1, 'main exits 1 on a stale zip')
    check(R.main([os.path.join(d, 'good_Main.zip')]) == 0, 'main exits 0 on a good zip')

print('FAIL %d' % fails if fails else 'PASS')
sys.exit(1 if fails else 0)
