import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EXES = {'dd': os.environ.get('ANP_DD_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'),
        'dm': os.environ.get('ANP_DM_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men\kaneandlynch.exe')}
import rtp, capstone, struct, sys
exe=EXES['dd']
img=rtp.Img(exe); vts=rtp.vtable_by_class(img)
cls=sys.argv[1]; lo,hi=int(sys.argv[2],0),int(sys.argv[3],0)
vt=vts[cls]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False
text=img.sec('.text')
def funcbytes(va,n=0x600):
    o=img.off(va); return img.d[o:o+n]
for k in range(80):
    f=img.u32(vt+4*k)
    if not f or not (text[0]<=f<text[0]+text[1]): break
    hits=[]
    for ins in md.disasm(funcbytes(f),f):
        op=ins.op_str
        import re
        for m in re.finditer(r'\[(e\w\w) \+ (0x[0-9a-f]+)\]',op):
            off=int(m.group(2),16)
            if lo<=off<=hi: hits.append('%x: %s %s'%(ins.address,ins.mnemonic,op))
        if ins.mnemonic=='ret' : break
    if hits: print('slot',k,hex(f)); [print('   ',h) for h in hits[:20]]
