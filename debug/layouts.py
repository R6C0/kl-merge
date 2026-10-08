"""layouts.py <Class | Controller | ROOT> [level ...]   the record layouts Dog Days' own levels store for an entity class
or a controller, with counts - what our converted record has to look like. Classes come from each level's .gms as shipped
(no retyping); a level we replaced is read from KL_PortBackup. First run reads every level (~40 s), then it is cached."""
import collections,glob,os,pickle,sys
import kl,locate
from kl_prp import Prp
import kl_convert as K,kl_gms
from kl_port_check import exe_classes
def levels(names=()):
    for zp in sorted(glob.glob(os.path.join(glob.escape(kl.DD),'Scenes','Locations','*','*_Main.zip'))):
        L=os.path.basename(os.path.dirname(zp)); bak=os.path.join(kl.DD,'KL_PortBackup',os.path.relpath(zp,kl.DD))
        if not names or L in names: yield L,(bak if os.path.isfile(bak) else zp)
def survey(zp):
    """{('c',type id,layout) | ('k',controller,layout): [count, first node index]} of one level archive."""
    st=os.stat(zp); f=os.path.join(kl.TMP,'layouts_%s_%d_%d.pkl'%(os.path.basename(zp),st.st_mtime,st.st_size))
    if os.path.isfile(f): return pickle.load(open(f,'rb'))
    out={}
    for label,rd in locate.sources(zp):
        p=Prp(rd('prp')); ent=locate.entities(kl_gms.unpack(rd('gms')),None)
        for k,n in enumerate(p.nodes()):
            for key in [('c',ent[k][0],K.csig(n['props']))]+[('k',p.key(a),K.csig(b)) for a,b in n['ctrls']]:
                out.setdefault(key,[0,k])[0]+=1
    pickle.dump(out,open(f,'wb')); return out
def layouts(name,names=()):
    """{(kind, layout): [count, levels, (level, node index) example]} for a class or controller name."""
    tids={t for t,(n,_) in exe_classes(os.path.join(kl.DD,kl.DD_EXE))[0].items() if n==name}|({None} if name=='ROOT' else set())
    tot=collections.defaultdict(lambda:[0,set(),None])
    for L,zp in levels(names):
        for (kind,who,sg),(c,first) in survey(zp).items():
            if who in tids if kind=='c' else who==name:
                t=tot[(kind,sg)]; t[0]+=c; t[1].add(L); t[2]=t[2] or (L,first)
    return tot
if __name__=='__main__':
    tot=layouts(sys.argv[1],sys.argv[2:])
    if not tot: print('no Dog Days level stores a class or controller named',sys.argv[1])
    for (kind,sg),(c,ls,eg) in sorted(tot.items(),key=lambda x:-x[1][0]):
        print('%7d %s %s   %d levels, e.g. %s node %d'%(c,'class     ' if kind=='c' else 'controller',sg,len(ls),*eg))
