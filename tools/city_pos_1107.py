import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene, kl_maps
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if sys.argv[2]!='-' else None)
pos = kl_maps.world(s)
pat = re.compile(sys.argv[3], re.I)
room=None
cur={}
def walk(e, room):
    n=e.name.decode('latin1')
    if e.tid in (0x100021,0x10003f) and not n.startswith('CloneGroup'): room=n
    if e.tid==0x200002 and pat.search(n) and not n.startswith('CloneGroup'):
        p=pos[e]; print('%-30s %-60s model=%#x flags=%#x (%d,%d,%d)'%(room,n[:60],e.model,e.flags,*p))
    for k in e.kids: walk(k, room)
for r in s.roots: walk(r, None)
