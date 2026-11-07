import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!='-' else None)
# rooms: tid 0x100021 and 0x10003f
for e in s.entities():
    if e.tid in (0x100021, 0x10003f) or (e.tid&0x100000 and re.search(r'Outside|Street|Roof|Backdrop|Sky|Distance|Far|City', e.name.decode('latin1'))):
        if e.name.decode('latin1').startswith('CloneGroup'): continue
        kids = collections.Counter(k.tid for k in e.walk())
        print('%-70s %#x total=%d  %s' % (e.name.decode('latin1')[:70], e.tid, sum(kids.values()), dict((hex(k),v) for k,v in kids.most_common(5))))
