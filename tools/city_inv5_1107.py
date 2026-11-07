import sys, os, zipfile, collections, re, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if sys.argv[2]!='-' else None)
want = sys.argv[3].split(',')
for e in s.entities():
    nm = e.name.decode('latin1')
    if nm in want:
        print('==', nm, hex(e.tid), 'kids', len(e.kids))
        for k in e.walk():
            t = struct.unpack_from('<12f', k.rot)[9:12] if False else struct.unpack_from('<4f', k.trans)
            print('   %-60s %#x model=%#x flags=%#x pos=(%.0f,%.0f,%.0f)' % (k.name.decode('latin1')[:60], k.tid, k.model, k.flags, *t[:3]))
