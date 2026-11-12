import sys,os,struct; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gms import load_gms
from anp_paths import WORK
DD_SZ=[20,20,12,32,72,28,20,16,4,12,4,4,8]
DM_SZ=[16,16,12,24,48,20,20,10,2,8,2,2,4]
def arrays(g, dm):
    h=struct.unpack_from('<20I',g); o=h[13]; size=struct.unpack_from('<I',g,o)[0]
    if dm:
        cnt=list(struct.unpack_from('<14h',g,o+4))[:13]; p=o+4+28; sz=DM_SZ
    else:
        cnt=list(struct.unpack_from('<14i',g,o+4))[:13]; p=o+4+56; sz=DD_SZ
    arrs=[]
    for c,s in zip(cnt,sz):
        arrs.append((p,c,s)); p+=c*s
    assert p==o+4+size,(p,o+4+size)
    return cnt,arrs
if __name__=='__main__':
    which=int(sys.argv[1]); n=int(sys.argv[2]) if len(sys.argv)>2 else 4
    for side,nm,dm in [('dd','F01_Main',0),('dm','M01A_Main',1)]:
        g=load_gms(os.path.join(WORK,'scn',side,nm+'.gms')); cnt,arrs=arrays(g,dm)
        p,c,s=arrs[which]
        print(side,'A%d'%which,'count',c,'size',s)
        for i in range(min(n,c)):
            r=g[p+i*s:p+(i+1)*s]
            print('   ',r.hex(' ',2))
