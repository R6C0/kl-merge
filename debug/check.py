"""check.py [level zip | prp]   pre-flight: every node and controller record of a level (default: the installed F01) against
the layouts Dog Days' own levels store for that class / controller name (layouts.py; classes as the level's .gms has them).
Independent of the converter and of the exe schemas. A layout no shipped level uses is what made the reader assert on
2026-10-08 (ZROOM-shaped records on nodes the .gms called ZGROUP). Classes and controllers no shipped level stores cannot
be judged this way and are listed apart. Array lengths and values are not compared."""
import collections,os,sys
import kl,locate,layouts
from kl_prp import Prp
import kl_convert as K,kl_gms
from kl_port_check import exe_classes
def problems(rd):
    """-> ({(what, our layout, comparable): [count, first node index, its name]}, node count); rd as in locate.sources."""
    dd=collections.defaultdict(set)
    for L,zp in layouts.levels():
        for kind,who,sg in layouts.survey(zp): dd[kind,who].add(sg)
    names=exe_classes(os.path.join(kl.DD,kl.DD_EXE))[0]; p=Prp(rd('prp')); ent=locate.entities(kl_gms.unpack(rd('gms')),rd('buf')); out={}
    for k,n in enumerate(p.nodes()):
        tid,name=ent[k]
        for kind,who,label,obj in [('c',tid,'node '+('ROOT' if k==0 else names.get(tid,('%#x'%tid,))[0]),n['props'])]+[('k',p.key(a),'controller '+p.key(a),b) for a,b in n['ctrls']]:
            sg=K.csig(obj)
            if sg not in dd[kind,who]: out.setdefault((label,sg,bool(dd[kind,who])),[0,k,name])[0]+=1
    return out,len(ent)
LOC_MAX=612634   # = kl_loc.LOC_CAP: kl2 0x7fef36 copies the selected language's level .LOC into a static 600,000-byte buffer at 0xe100b8, unchecked; 612,634 (stock Russian) is the largest size proven safe (crash 0x526b40 at 639,672, V1_DM01)
def loc_sizes(src):
    import zipfile
    if not src.lower().endswith('.zip'): return
    with zipfile.ZipFile(src) as z:
        for n in z.namelist():
            if n.upper().endswith('.LOC'):          # every language: the player's selected one is the one copied
                s=z.getinfo(n).file_size
                print('%s: %d bytes%s'%(n,s,' - OVER the %d-byte cap: the level will crash in that language'%LOC_MAX if s>LOC_MAX else ''))
if __name__=='__main__':
    src=sys.argv[1] if len(sys.argv)>1 else os.path.join(kl.DD,'Scenes','Locations','F01','F01_Main.zip')
    loc_sizes(src)
    for label,rd in locate.sources(src):
        if not rd('gms'): sys.exit(label+': no .gms beside it - the classes come from there')
        bad,n=problems(rd); rows=sorted(bad.items(),key=lambda x:x[1][1])
        print('%s: %d nodes'%(label,n))
        print('%d records with a layout Dog Days never stores for that class/controller'%sum(v[0] for (_,_,cmp),v in rows if cmp))
        for (what,sg,cmp),(c,k,name) in rows:
            if cmp: print('%6d %s %s   first: node %d %r'%(c,what,sg,k,name))
        print('%d records of classes/controllers no shipped level stores (not comparable here)'%sum(v[0] for (_,_,cmp),v in rows if not cmp))
        for (what,sg,cmp),(c,k,name) in rows:
            if not cmp: print('%6d %s %s   first: node %d %r'%(c,what,sg,k,name))
