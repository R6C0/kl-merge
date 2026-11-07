import sys, os, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_graft as KG, kl_prmgraph as G
p = sys.argv[1]
order, files, ext, sc, live, hud = KG.open_built(p)
prm = G.read(files[ext['.prm']], 'dd')
reached, args = G.walk(prm, live)
orph = G.orphans(prm, reached)
dead = [i for i, l in orph.items() if l == 'dead root']
tot = sum(len(c) for c in prm.chunks if c)
print('chunks', len(prm.chunks), 'bytes', tot, 'reached', len(reached), 'dead roots', len(dead))
try:
    dk, da = G.walk(prm, [(i, 'root') for i in dead])
except ValueError as e:
    print('dead walk failed', e); dk = {}
dk = {i: k for i, k in dk.items() if i not in reached}
big = sorted(((len(prm.chunks[i] or b""), i, k) for i, k in dk.items() if k in ('vtx', 'idx')), reverse=True)
print('dead data chunks', len(big), 'bytes', sum(b[0] for b in big), 'non-empty(>16)', sum(1 for b in big if b[0] > 16))
print(big[:10])
