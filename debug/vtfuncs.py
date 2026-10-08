import sys,struct,re,capstone
cls=sys.argv[1].encode(); sys.argv=['x']
exec(open('rtti.py').read().split('for ra in')[0])
# find type descriptor name
o=d.find(b'.?AV'+cls+b'@@\0'); td=B+pe.get_rva_from_offset(o-8)
# COLs referencing td at +12
cols=[]
for i in range(0,len(rd)-20,4):
    if struct.unpack_from('<I',rd,i+12)[0]==td and struct.unpack_from('<I',rd,i)[0]==0: cols.append(rbase+i)
vts=[]
for c in cols:
    pat=struct.pack('<I',c)
    for m in re.finditer(re.escape(pat),rd):
        if m.start()%4==0: vts.append(rbase+m.start()+4)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
img=pe.get_memory_mapped_image()
for vt in vts[:1]:
    print('vtable',hex(vt))
    for k in range(200):
        f=u32(vt+4*k)
        if not f or off(f) is None or not (0x401000<=f<0xb00000): break
        code=img[f-B:f-B+0x600]; txt=[]
        for ins in md.disasm(code,f):
            txt.append(ins.mnemonic+' '+ins.op_str)
            if ins.mnemonic=='ret': break
        j=' ; '.join(txt)
        if '0x74' in j and ('0x7c]' in j or '0x78]' in j): print(k,hex(f),len(txt))
