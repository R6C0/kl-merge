import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!='-' else None)
def show(e, d, maxd):
    n = sum(1 for _ in e.walk())
    print('  '*d + '%s %#x n=%d' % (e.name.decode('latin1')[:70], e.tid, n))
    if d < maxd:
        for k in e.kids:
            if k.kids: show(k, d+1, maxd)
for r in s.roots:
    nm = r.name.decode('latin1')
    if nm.startswith(sys.argv[3]): show(r, 0, int(sys.argv[4]))
