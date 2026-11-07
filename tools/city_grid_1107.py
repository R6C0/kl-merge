import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene, kl_maps
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if sys.argv[2]!='-' else None)
pos = kl_maps.world(s)
CELL=int(sys.argv[3]) if len(sys.argv)>3 else 2500
g=collections.Counter(); ymax=collections.defaultdict(float)
def walk(e, room):
    n=e.name.decode('latin1')
    if e.tid in (0x100021,0x10003f) and not n.startswith('CloneGroup'): room=n
    if e.tid==0x200002 and room and 'Outside' in room and (e.flags & 0x20000) and re.search(r'Build|Facade|Billboard|Glow|Tower|Sign',n):
        p=pos[e]; k=(int(p[0]//CELL), int(p[2]//CELL)); g[k]+=1; ymax[k]=max(ymax[k],p[1])
    for k in e.kids: walk(k, room)
for r in s.roots: walk(r, None)
xs=range(-6,16); zs=range(-8,6)
print('x cells %d..%d (cell %d cm), rows = z descending; digit = count (cap 9), . = none; PAD at x=%d z=%d'%(xs[0],xs[-1],CELL,8100//CELL,4600//CELL))
for zz in reversed(zs):
    print('z%6d '%(zz*CELL)+''.join(('P' if (xx==8100//CELL and zz==4600//CELL) else (str(min(9,g[(xx,zz)])) if g[(xx,zz)] else '.')) for xx in xs))
