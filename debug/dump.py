import struct,sys,re,pefile,capstone
dmp=sys.argv[1]; exe='/mnt/user-data/uploads/Kane & Lynch 2 - Dog Days/kl2.exe'
d=open(dmp,'rb').read()
ns,dirrva=struct.unpack_from('<II',d,8); streams={}
for i in range(ns):
    t,sz,rva=struct.unpack_from('<III',d,dirrva+12*i); streams[t]=(sz,rva)
sz,rva=streams[6]
code,flags,rec,addr,np=struct.unpack_from('<IIQQI',d,rva+8)
info=struct.unpack_from('<2Q',d,rva+8+24+4+4)  # approx
ctx_sz,ctx_rva=struct.unpack_from('<II',d,rva+8+152); c=d[ctx_rva:ctx_rva+ctx_sz]
off=156; edi,esi,ebx,edx,ecx,eax=struct.unpack_from('<6I',c,off); ebp,eip,cs,efl,esp,ss=struct.unpack_from('<6I',c,off+24)
mem=[]
sz,rva2=streams[5]; n=struct.unpack_from('<I',d,rva2)[0]
for i in range(n):
    start,dsz,drva=struct.unpack_from('<QII',d,rva2+4+16*i); mem.append((start,dsz,drva))
def read(a,n):
    for s,sz_,r in mem:
        if s<=a and a+n<=s+sz_: return d[r+a-s:r+a-s+n]
sz,rva=streams[4]; n=struct.unpack_from('<I',d,rva)[0]; mods=[]
for i in range(n):
    base,size=struct.unpack_from('<QI',d,rva+4+108*i); nr=struct.unpack_from('<I',d,rva+4+108*i+20)[0]
    L=struct.unpack_from('<I',d,nr)[0]; mods.append((base,base+size,d[nr+4:nr+4+L].decode('utf-16le').split('\\')[-1]))
def which(a):
    for b,e,nm in mods:
        if b<=a<e: return '%s+0x%x'%(nm,a-b)
print('code',hex(code),'at',hex(addr),which(addr))
print(dict(eip=hex(eip),esp=hex(esp),ebp=hex(ebp),eax=hex(eax),ebx=hex(ebx),ecx=hex(ecx),edx=hex(edx),esi=hex(esi),edi=hex(edi)))
pe=pefile.PE(exe,fast_load=True); x=open(exe,'rb').read(); B=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def cs(v):
    try:
        o=pe.get_offset_from_rva(v-B); e=x.find(b'\0',o,o+100); t=x[o:e]
        return t.decode() if e>o and all(32<=q<127 for q in t) else ''
    except: return ''
if which(addr) and 'kl2.exe' in which(addr):
    o=pe.get_offset_from_rva(addr-B)
    for i in md.disasm(x[o-0x40:o+0x10],addr-0x40): print('   ',hex(i.address),i.mnemonic,i.op_str,'<==' if i.address==addr else '')
st=read(esp,0x1000) or read(esp,0x800) or b''
print('stack',len(st))
frames=[]
for i in range(0,len(st)-3,4):
    v=struct.unpack_from('<I',st,i)[0]; w=which(v)
    if w and 'kl2.exe' in w:
        # validate it's a return address (preceded by call)
        try:
            o=pe.get_offset_from_rva(v-B)
            if x[o-5]==0xe8 or x[o-2]==0xff or x[o-3]==0xff or x[o-6]==0xff: frames.append(v)
        except: pass
for v in frames[:14]:
    o=pe.get_offset_from_rva(v-B); win=x[o-0x400:o]
    strs=[]
    for i in md.disasm(win,v-0x400):
        for m in re.findall(r'0x([0-9a-f]{6,8})',i.op_str):
            t=cs(int(m,16))
            if len(t)>3: strs.append(t)
    print(hex(v),which(v),strs[-6:])
