import sys, os, zipfile, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G, kl_scene
z = zipfile.ZipFile(sys.argv[1]); names = {n.rsplit('_Main',1)[1]: n for n in z.namelist() if '_Main' in n}
prm = G.read(z.read(names['.prm']), 'dm'); s = kl_scene.read(z)
want = set(sys.argv[2].split(','))
for e in s.entities():
    n = e.name.decode('latin1')
    if n in want and e.model:
        try:
            k, a = G.walk(prm, [e.model])
        except Exception as ex:
            print(n, 'walk fail', ex); continue
        b = sum(len(prm.chunks[i] or b'') for i in k)
        kinds = {}
        for i, kk in k.items(): kinds[kk] = kinds.get(kk, 0) + 1
        print('%-34s model=%#x chunks=%d bytes=%d %s' % (n, e.model, len(k), b, kinds))
