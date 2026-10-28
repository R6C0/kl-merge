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
def sgd_stale(src):
    """Octree leaves of the .sgd that are not where their entity is (kl_sgd_audit; the graft repairs the ones beyond
    kl_members.STALE, so a build fresh from kl_graft prints 0 here; a later layout tool that moved entities shows up)."""
    if not src.lower().endswith('.zip'): return
    try:
        import kl_sgd_audit as SA, kl_members as MB
        for label,gms,buf,sgd in SA.sets(src):
            bad,anim=SA.stale(SA.audit(gms,buf,sgd,MB.STALE))
            print('%s: %d octree leaves over %d units from their entity (grenades miss them; kl_sgd_audit.py --fix)%s'%(
                os.path.basename(label),len(bad),int(MB.STALE['HavokShatterOctree']),' - %d under Animation/ (expected)'%len(anim) if anim else ''))
            for name,ref,d,ename,top in sorted(bad,key=lambda b:-(b[2] or 1e9))[:5]:
                print('   %-18s REF %-6d %8s  %s  (%s)'%(name,ref,'no REF' if d is None else '%.0f'%d,ename[:40],top[:30]))
    except Exception as e:
        print('sgd audit skipped: %r'%e)
if __name__=='__main__':
    src=sys.argv[1] if len(sys.argv)>1 else os.path.join(kl.DD,'Scenes','Locations','F01','F01_Main.zip')
    loc_sizes(src)
    sgd_stale(src)
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
