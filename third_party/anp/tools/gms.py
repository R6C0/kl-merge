import struct, zlib, sys, collections
def load_gms(path):
    d=open(path,'rb').read()
    usz,fsz=struct.unpack_from('<II',d); flag=d[8]
    return d[9:] if flag else zlib.decompressobj(-15).decompress(d[9:])
class GMS:
    def __init__(s,gmspath,bufpath):
        s.g=g=load_gms(gmspath); s.b=open(bufpath,'rb').read()
        s.hdr=struct.unpack_from('<20I',g,0)
        tab=s.hdr[0]; n=struct.unpack_from('<I',g,tab)[0]
        s.ents=[]
        for i in range(n):
            decl,u4=struct.unpack_from('<II',g,tab+4+i*8)
            off=4*(decl&0xFFFFFF)
            f=struct.unpack_from('<16I',g,off)
            nameoff=f[0]
            e=s.b.index(b'\0',nameoff); name=s.b[nameoff:e].decode('latin1')
            s.ents.append(dict(i=i,decl=decl,u4=u4,off=off,name=name,f=f,type=f[5],prim=f[3],inst=f[12]))
    def depth_tree(s):
        path=[-1]; 
        for e in s.ents:
            rd=e['decl']>>25
            path=path[:len(path)-rd] if rd else path
            e['parent']=path[-1]; e['depth']=len(path)-1
            if e['decl']&0x1000000: path=path+[e['i']]
if __name__=='__main__':
    G=GMS(sys.argv[1],sys.argv[2]); G.depth_tree()
    print('hdr',[hex(x) for x in G.hdr]); print('n',len(G.ents))
    c=collections.Counter(e['type'] for e in G.ents)
    for t,n in c.most_common(): 
        ex=[e['name'] for e in G.ents if e['type']==t][:3]
        print(hex(t),n,ex)
