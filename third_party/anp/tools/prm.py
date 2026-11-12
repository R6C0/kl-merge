import struct,sys
class PRM:
    def __init__(s,path):
        s.d=d=open(path,'rb').read()
        s.off,s.cnt,s.off2,z=struct.unpack_from('<4I',d)
        s.desc=[struct.unpack_from('<4I',d,s.off+i*16) for i in range(s.cnt)]
    def chunk(s,i):
        o,sz,k,u=s.desc[i]; return s.d[o:o+sz]
