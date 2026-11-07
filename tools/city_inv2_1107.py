import sys, os, zipfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_scene
z = zipfile.ZipFile(sys.argv[1]); s = kl_scene.read(z, sys.argv[2] if len(sys.argv)>2 else None)
pat = re.compile(sys.argv[3] if len(sys.argv)>3 else r'backdrop|sky|distance|glow|city|traffic|car|billboard|neon|light|fog|cloud|moon|far|building|street|skyline', re.I)
top = []
for r in s.roots:
    n = sum(1 for _ in r.walk()); top.append((r.name.decode('latin1'), r.tid, n))
print('ROOTS', len(top))
for n,t,c in top:
    if not re.match(r'(Characters|AI_Players|Doors|Specials)!', n): print('  %-60s %#x %d' % (n,t,c))
