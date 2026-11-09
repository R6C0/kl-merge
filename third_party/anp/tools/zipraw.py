import struct, zlib, os, binascii
class Entry:
    def __init__(s, name, method, crc, csize, usize, src=None, off=0, data=None, dostime=0, dosdate=0, flags=0, ver=20):
        s.name=name; s.method=method; s.crc=crc; s.csize=csize; s.usize=usize
        s.src=src; s.off=off; s.data=data; s.dostime=dostime; s.dosdate=dosdate; s.flags=flags; s.ver=ver
def read_zip(path):
    f=open(path,'rb'); f.seek(0,2); size=f.tell()
    f.seek(max(0,size-65557)); tail=f.read(); i=tail.rfind(b'PK\x05\x06')
    eocd=tail[i:]; n=struct.unpack_from('<H',eocd,10)[0]; cdsize,cdoff=struct.unpack_from('<II',eocd,12)
    f.seek(cdoff); cd=f.read(cdsize); p=0; ents=[]
    for k in range(n):
        (sig,vm,vn,fl,meth,t,dt,crc,cs,us,nl,el,cl,dn,ia,ea,lho)=struct.unpack_from('<IHHHHHHIIIHHHHHII',cd,p)
        name=cd[p+46:p+46+nl].decode('latin1'); p+=46+nl+el+cl
        f.seek(lho); lh=f.read(30); lnl,lel=struct.unpack_from('<HH',lh,26)
        ents.append(Entry(name,meth,crc,cs,us,src=path,off=lho+30+lnl+lel,dostime=t,dosdate=dt,flags=fl&~8,ver=vn))
    return ents
def entry_from_bytes(name, data, compress=True, level=6, like=None):
    crc=binascii.crc32(data)&0xffffffff
    if compress:
        c=zlib.compressobj(level,zlib.DEFLATED,-15); cd=c.compress(data)+c.flush(); m=8
    else: cd=data; m=0
    e=Entry(name,m,crc,len(cd),len(data),data=cd)
    if like: e.dostime,e.dosdate=like.dostime,like.dosdate
    return e
def entry_from_file(name, path, compress=True, level=6, like=None):
    return entry_from_bytes(name, open(path,'rb').read(), compress, level, like)
def read_entry(e):
    if e.data is not None: raw=e.data
    else:
        with open(e.src,'rb') as f: f.seek(e.off); raw=f.read(e.csize)
    return zlib.decompress(raw,-15) if e.method==8 else raw
def write_zip(path, ents):
    out=open(path,'wb'); cd=[]
    for e in ents:
        lho=out.tell(); nb=e.name.encode('latin1')
        out.write(struct.pack('<IHHHHHIIIHH',0x04034b50,e.ver,e.flags,e.method,e.dostime,e.dosdate,e.crc,e.csize,e.usize,len(nb),0)+nb)
        if e.data is not None: out.write(e.data)
        else:
            with open(e.src,'rb') as f:
                f.seek(e.off); left=e.csize
                while left:
                    b=f.read(min(left,1<<22)); out.write(b); left-=len(b)
        cd.append(struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,e.ver,e.ver,e.flags,e.method,e.dostime,e.dosdate,e.crc,e.csize,e.usize,len(nb),0,0,0,0,0x20,lho)+nb)
    cdoff=out.tell(); cdb=b''.join(cd); out.write(cdb)
    out.write(struct.pack('<IHHHHIIH',0x06054b50,0,0,len(ents),len(ents),len(cdb),cdoff,0))
    out.close()
