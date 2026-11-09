import struct, sys
OPN={1:'Array',2:'BeginObject',3:'Reference',4:'Container',5:'Char',6:'Bool',7:'Int8',8:'Int16',9:'Int32',10:'Float32',11:'Float64',12:'String',13:'RawData',14:'StrOrArrE',15:'StringArray',16:'Bitfield',0x7C:'EndArray',0x7D:'SkipMark',0x7E:'EndObject',0x7F:'EndOfStream'}
class PRP:
    def __init__(s,data):
        s.d=d=data
        assert d[:14]==b'IOPacked v0.1\0', d[:16]
        s.is_raw=d[14]; s.flags=struct.unpack_from('<I',d,15)[0]
        s.nkeys,s.dataoff=struct.unpack_from('<II',d,0x17)
        p=0x1F; s.tokens=[]
        if s.flags&8:
            for i in range(s.nkeys+1):
                e=d.index(b'\0',p); s.tokens.append(d[p:e].decode('latin1')); p=e+1
        s.objstart=0x1F+s.dataoff
        s.nobjects=struct.unpack_from('<I',d,s.objstart)[0]
        s.defs_off=s.objstart+4
    def str_(s,p):
        if s.flags&8:
            i=struct.unpack_from('<I',s.d,p)[0]; return s.tokens[i],p+4
        n=struct.unpack_from('<I',s.d,p)[0]; return s.d[p+4:p+4+n].decode('latin1'),p+4+n
    def instrs(s,start=None):
        d=s.d; p=s.defs_off if start is None else start
        while p<len(d):
            op=d[p]; base=op&0x7F; named=op&0x80 and op not in (0x80,)
            q=p+1
            if base in (1,4): v=struct.unpack_from('<I',d,q)[0]; q+=4
            elif base in (2,0x7C,0x7D,0x7E,0x7F,3): v=None
            elif base in (5,6,7): v=d[q]; q+=1
            elif base==8: v=struct.unpack_from('<h',d,q)[0]; q+=2
            elif base in (9,16): v=struct.unpack_from('<i',d,q)[0]; q+=4
            elif base==10: v=struct.unpack_from('<f',d,q)[0]; q+=4
            elif base==11: v=struct.unpack_from('<d',d,q)[0]; q+=8
            elif base in (12,14):
                if base==14 and not (s.flags&4): v=struct.unpack_from('<I',d,q)[0]; q+=4
                else: v,q=s.str_(q)
            elif base==13:
                n=struct.unpack_from('<I',d,q)[0]; v=d[q+4:q+4+n]; q+=4+n
            elif base==15:
                n=struct.unpack_from('<I',d,q)[0]; q+=4; v=[]
                for i in range(n):
                    x,q=s.str_(q); v.append(x)
            else:
                raise Exception('bad op %x at %x'%(op,p))
            yield p,op,v
            p=q
            if base==0x7F: break
if __name__=='__main__':
    pr=PRP(open(sys.argv[1],'rb').read())
    print('raw',pr.is_raw,'flags',hex(pr.flags),'nkeys',pr.nkeys,'dataoff',hex(pr.dataoff),'nobjects',pr.nobjects)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 200
    for i,(p,op,v) in enumerate(pr.instrs()):
        if i>=n: break
        print(hex(p), ('N' if op&0x80 else ' ')+OPN.get(op&0x7f,hex(op)), repr(v)[:80])
