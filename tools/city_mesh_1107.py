import sys, os, zipfile, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G, kl_scene, kl_texmat as T
z = zipfile.ZipFile(sys.argv[1]); names = {n.rsplit('_Main',1)[1]: n for n in z.namelist() if '_Main' in n}
prm = G.read(z.read(names['.prm']), 'dm'); s = kl_scene.read(z)
mat = T.read_mat(z.read(names['.MAT'])); tex = T.read_tex(z.read(names['.TEX']))
for e in s.entities():
    n = e.name.decode('latin1')
    if n == sys.argv[2] and e.model:
        k, a = G.walk(prm, [e.model])
        slots=set()
        for i, kk in k.items():
            if kk == 'desc':
                c = prm.chunks[i]; cnt = struct.unpack_from('<I', c, 0)[0]; vtx = struct.unpack_from('<I', c, 4)[0]
                v = prm.chunks[vtx]; stride = len(v)//cnt if cnt else 0
                xs=[struct.unpack_from('<3f', v, j*stride) for j in range(cnt)]
                if xs: print('desc',i,'verts',cnt,'stride',stride,'bbox',[ (round(min(p[a] for p in xs)),round(max(p[a] for p in xs))) for a in range(3)])
            if kk == 'mesh': slots.add(prm.u16(i, 0x12))
        print('material slots', sorted(slots))
        ids=T.used_textures(mat, sorted(slots)); print('textures', sorted(ids))
        for t in sorted(ids):
            if t in tex.tex: print('  tex', t, len(tex.tex[t]) if hasattr(tex.tex[t],'__len__') else tex.tex[t])
        for t in sorted(ids):
            if t in tex.tex:
                x = tex.tex[t]; print('  tex', t, x.name, len(x.entry), 'frames', x.frames)
        # skydome
for e in s.entities():
    if e.name == b'M05_Skydome_A':
        k, a = G.walk(prm, [e.model]); mn=[1e9]*3; mx=[-1e9]*3
        for i, kk in k.items():
            if kk == 'desc':
                c = prm.chunks[i]; cnt = struct.unpack_from('<I', c, 0)[0]; vtx = struct.unpack_from('<I', c, 4)[0]; v = prm.chunks[vtx]; st = len(v)//cnt
                for j in range(cnt):
                    p = struct.unpack_from('<3f', v, j*st)
                    for a_ in range(3): mn[a_]=min(mn[a_],p[a_]); mx[a_]=max(mx[a_],p[a_])
        print('skydome bbox', [round(x) for x in mn], [round(x) for x in mx]); break
