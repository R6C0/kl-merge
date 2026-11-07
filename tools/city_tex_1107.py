import zipfile, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_texmat as T
p = sys.argv[1]; z = zipfile.ZipFile(p); nm = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
tex = T.read_tex(z.read(nm['.TEX']))
names = sorted((i, t.name, len(t.entry)) for i, t in tex.tex.items() if any(w in t.name for w in sys.argv[2].split(',')))
print(len(tex.tex), len(names))
for x in names[:60]: print('  ', x)
