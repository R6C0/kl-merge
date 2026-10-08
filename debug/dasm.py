import pefile,capstone,sys,re
exe='/mnt/user-data/uploads/Kane & Lynch 2 - Dog Days/kl2.exe'
pe=pefile.PE(exe,fast_load=True); B=pe.OPTIONAL_HEADER.ImageBase; img=pe.get_memory_mapped_image()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
a=int(sys.argv[1],16); n=int(sys.argv[2],16) if len(sys.argv)>2 else 0x100
def s(v):
    try:
        o=v-B
        if 0<o<len(img):
            m=re.match(rb'[\x20-\x7e]{4,}',img[o:o+120]); return m.group().decode() if m else ''
    except: pass
    return ''
for i in md.disasm(img[a-B:a-B+n],a):
    ex=''
    for v in re.findall(r'0x[0-9a-f]{6,}',i.op_str):
        t=s(int(v,16)); ex+=(' "'+t+'"') if t else ''
    print(hex(i.address),i.mnemonic,i.op_str,ex)
