"""Dog Days per-level effect permutation library (.fxc)
header: u32 ver(100), u32 count, u32 dataSize(=file-16), u32 firstOff(16)
record: u32 kind, u32 ?, u32 codeSize, defines[32] x (name[32], value[32]), u32 codeOff (file-relative, rebased by loader), char name[64], code[codeSize]"""
import struct,sys
def parse(d):
    ver,cnt,dsz,off=struct.unpack_from('<4I',d)
    recs=[]
    for i in range(cnt):
        kind,x,cs=struct.unpack_from('<3I',d,off)
        defs=[]
        for k in range(32):
            n=d[off+12+64*k:off+12+64*k+32].split(b'\0')[0].decode()
            if not n: break
            v=d[off+12+64*k+32:off+12+64*k+64].split(b'\0')[0].decode()
            defs.append((n,v))
        name=d[off+0x810:off+0x850].split(b'\0')[0].decode('latin1')
        end=off+0x850+cs
        recs.append(dict(off=off,kind=kind,x=x,size=cs,defs=defs,name=name,raw=d[off:end]))
        off=end
    assert off==len(d),(hex(off),len(d))
    return ver,recs
def build(ver,recs):
    body=b''.join(r['raw'] for r in recs)
    return struct.pack('<4I',ver,len(recs),len(body),16)+body
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); ver,R=parse(d)
    for r in R: print(hex(r['off']),r['kind'],hex(r['x']),r['name'],' '.join(n for n,v in r['defs']))
