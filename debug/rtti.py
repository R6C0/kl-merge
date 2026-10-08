import pefile,struct,sys,re
pe=pefile.PE('kl2.exe',fast_load=True); d=open('kl2.exe','rb').read(); B=pe.OPTIONAL_HEADER.ImageBase
def off(v):
    try: return pe.get_offset_from_rva(v-B)
    except: return None
def u32(v):
    o=off(v); return struct.unpack_from('<I',d,o)[0] if o is not None else None
def func_start(va):
    o=off(va); s=d.rfind(b'\xcc\xcc',o-0x2000,o)
    # skip padding
    while d[s]==0xcc: s+=1
    return B+pe.get_rva_from_offset(s)
# index all dwords in .rdata pointing into .text, for vtable lookups
rdata=[s for s in pe.sections if s.Name.startswith(b'.rdata')][0]
rbase=B+rdata.VirtualAddress; rd=d[rdata.PointerToRawData:rdata.PointerToRawData+rdata.SizeOfRawData]
def vtables_with(fn):
    out=[]
    pat=struct.pack('<I',fn)
    for m in re.finditer(re.escape(pat),rd):
        if m.start()%4: continue
        out.append(rbase+m.start())
    return out
def class_of_vtable_slot(addr):
    # walk back to vtable start: entry before start is COL pointer
    a=addr
    for _ in range(400):
        col=u32(a-4)
        if col and off(col) is not None:
            sig=u32(col)
            if sig==0:
                td=u32(col+12)
                if td and off(td) is not None:
                    o=off(td)+8; e=d.find(b'\0',o,o+200); name=d[o:e]
                    if name.startswith(b'.?A'): return name.decode(),(addr-a)//4
        a-=4
    return None,None
for ra in [int(x,16) for x in sys.argv[1:]]:
    fs=func_start(ra); vt=vtables_with(fs)
    print(hex(ra),'func',hex(fs),[class_of_vtable_slot(v) for v in vt][:4])
