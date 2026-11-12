import struct, collections, sys
class MAT:
    def __init__(s, path, rs):
        s.d=d=open(path,'rb').read(); s.rs=rs
        s.h=struct.unpack_from('<4I',d)
        s.sec=[x for x in struct.unpack_from('<32I',d,s.h[0]) if x]
        s.t1=struct.unpack_from('<2048I',d,s.h[1]); s.t2=struct.unpack_from('<2048I',d,s.h[3])
        s.recs={}   # offset -> (tag,val,cnt,typ)
        s.arrays={} # offset -> count
        s.objs={}
        s.stats=collections.Counter()
        for o in s.sec: s.walk_obj(o,'class')
        for i,o in enumerate(s.t1):
            if o: s.walk_obj(o,'inst')
    def rec(s,o):
        d=s.d
        if s.rs==16:
            tag,val,cnt,typ=struct.unpack_from('<4I',d,o)
        else:
            tag,val,cnt,typ=struct.unpack_from('<IIHH',d,o)
        return tag.to_bytes(4,'big').decode('latin1'),val,cnt,typ
    def walk_obj(s,o,kind):
        if o in s.objs: return
        hdr=struct.unpack_from('<12I',s.d,o); s.objs[o]=(kind,hdr)
        s.walk_list(hdr[7],1,kind)
    def walk_list(s,o,n,ctx):
        if o in s.arrays: 
            assert s.arrays[o]==n,(hex(o),n,s.arrays[o]); return
        s.arrays[o]=n
        for i in range(n):
            ro=o+i*s.rs; r=s.rec(ro); s.recs[ro]=r
            tag,val,cnt,typ=r
            s.stats[(tag,typ)]+=1
            if typ==3: s.walk_list(val,cnt,tag)
if __name__=='__main__':
    m=MAT(sys.argv[1],int(sys.argv[2]))
    print('objs',len(m.objs),'arrays',len(m.arrays),'recs',len(m.recs))
    for (t,ty),n in sorted(m.stats.items()): print('  %s type%d: %d'%(t,ty,n))

def cstr(d,o):
    e=d.index(b'\0',o); return d[o:e].decode('latin1')
def dump_tree(m, ro, ind=0, out=None, maxdepth=6):
    tag,val,cnt,typ=m.rec(ro)
    if typ==1: v=repr(cstr(m.d,val))
    elif typ==2: v=str(val)
    elif typ==0: v=str([round(x,3) for x in struct.unpack_from('<%df'%cnt,m.d,val)])
    else: v='[%d]'%cnt
    out.append('  '*ind+'%s %s'%(tag,v))
    if typ==3 and ind<maxdepth:
        for i in range(cnt): dump_tree(m,val+i*m.rs,ind+1,out)
