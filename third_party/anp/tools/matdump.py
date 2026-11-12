import sys,struct
sys.path.insert(0,__file__.rsplit('/',1)[0])
from mat import MAT, cstr
def fmt(m,ro,ind,out,maxd):
    tag,val,cnt,typ=m.rec(ro)
    if typ==1: v=repr(cstr(m.d,val))
    elif typ==2: v=str(val)
    elif typ==0:
        if cnt<=1: v=str(round(struct.unpack('<f',struct.pack('<I',val))[0],3))
        else: v=str([round(x,3) for x in struct.unpack_from('<%df'%cnt,m.d,val)])
    else: v='[%d]'%cnt
    out.append('  '*ind+'%s %s'%(tag,v))
    if typ==3 and ind<maxd:
        for i in range(cnt): fmt(m,val+i*m.rs,ind+1,out,maxd)
def inst(m,idx,maxd=5):
    o=m.t1[idx]; kind,hdr=m.objs[o]; out=[]
    fmt(m,hdr[7],0,out,maxd); return out
if __name__=='__main__':
    m=MAT(sys.argv[1],int(sys.argv[2]))
    for a in sys.argv[3:]:
        print('== inst',a); print('\n'.join(inst(m,int(a,0))))
