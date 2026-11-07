import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
pat = re.compile(r'building|skydome|backdrop|traffic|car_|_car|vehicle|distance|billboard|skyline|city|midrange|far|horizon|helicopter|moon|cloud|streetglow|sign|neon_|tower|bentley|taxi|bus', re.I)
def load(p, stem=None):
    s = kl_scene.read(zipfile.ZipFile(p), stem); return s
def rows(s):
    out = collections.Counter()
    for e in s.entities():
        n = e.name.decode('latin1')
        if n.startswith('CloneGroup') or 'Particl' in n or 'Shard' in n or 'Glow' in n and 'Cone' in n: continue
        if pat.search(n): out[(n, e.tid)] += 1
    return out
a = rows(load(sys.argv[1])); b = rows(load(sys.argv[2]))
print('source-only (dropped or renamed):')
for k, v in sorted(a.items()):
    if k not in b: print('  ', k, v)
print('both:', sum(1 for k in a if k in b), ' live-only:', sum(1 for k in b if k not in a))
