"""buf.py <dump>   the .prp reader's stream at the moment of the dump: position and the 16 KB it was reading.
ZPackedInput keeps its ZInputStream at +0x28; the stream is [vtbl][byte swap][source][pos][size] + 0x4000 buffer
(kl2 0x8f8460 refills the buffer 0x4000 at a time and copies out of it). pos is the NEXT byte; the last one read is pos-1."""
import os,struct,sys
import kl
def stream(D,E):
    """Address of the ZInputStream: a register holding the reader or the stream itself, else the first one on the stack."""
    vr=E.vtables('ZPackedInput'); vs=E.vtables('ZInputStream'); r=D.reg
    st=D.read(r['esp'],D.have(r['esp'])//4*4) or b''
    for a in [r[k] for k in 'esi ecx edi ebx eax edx ebp'.split()]+list(struct.unpack('<%dI'%(len(st)//4),st)):
        v=D.u32(a)
        if v in vr: a=D.u32(a+0x28); v=D.u32(a)
        if v in vs: return a
def get(D,E):
    """-> (stream address, pos, size, buffer) or None when the dump holds no reader."""
    so=stream(D,E)
    if so is None: return None
    pos,size=struct.unpack('<II',D.read(so+0xc,8)); return so,pos,size,D.read(so+0x14,min(0x4000,D.have(so+0x14)))
if __name__=='__main__':
    D=kl.Dump(kl.path(sys.argv[1])); g=get(D,kl.Exe())
    if not g: sys.exit('no ZPackedInput/ZInputStream in the registers or on the stack of this dump')
    so,pos,size,buf=g; out=os.path.join(kl.TMP,'streambuf.bin'); open(out,'wb').write(buf)
    print('stream %#x pos %#x size %#x, %d buffer bytes -> %s'%(so,pos,size,len(buf),out))
    print('last read %s | next %s'%(buf[max(pos-48,0):pos].hex(' '),buf[pos:pos+48].hex(' ')))
