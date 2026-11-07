"""city_inv_1107.py - read-only inventory of what each level draws outside the play space. python city_inv_1107.py <zip> [depth]"""
import sys, os, zipfile, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
def walk(e, d, maxd, out, path=''):
    n = sum(1 for _ in e.walk())
    out.append((d, e.name.decode('latin1'), e.tid, n))
    if d < maxd:
        for k in e.kids:
            if k.kids: walk(k, d+1, maxd, out)
            else: pass
if __name__ == '__main__':
    z = zipfile.ZipFile(sys.argv[1]); md = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    stem = sys.argv[3] if len(sys.argv) > 3 else None
    s = kl_scene.read(z, stem)
    ents = list(s.entities()); print('entities', len(ents))
    out = []
    for r in s.roots: walk(r, 0, md, out)
    for d, n, t, c in out: print('  '*d + '%s tid=%#x n=%d' % (n, t, c))
    c = collections.Counter(e.tid for e in ents); print(sorted(c.items(), key=lambda x: -x[1])[:40])
