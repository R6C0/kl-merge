"""dump.py <dump>   what faulted, registers, code before the fault, kl2.exe return addresses on the stack."""
import re,struct,sys
import kl
def summary(D,E):
    r=D.reg; at=D.addr; w=D.which(at) or '?'
    acc=' (%s address %#x)'%('writing' if D.info[0] else 'reading',D.info[1]) if D.code==0xc0000005 and len(D.info)>1 else ''
    print('code %#x at %#x %s%s'%(D.code,at,w,acc))
    print(' '.join('%s=%08x'%(k,r[k]) for k in 'eip esp ebp eax ebx ecx edx esi edi'.split()))
    if kl.SITES.get(at): print('site:',kl.explain(at,r,D))
    n=D.u32(0xe0ff14)                                   # node loader 0x46fe20 counts the nodes it enters here; entity total at 0xe0ff18
    if n: print('node loader counter: %d of %d nodes entered -> node index %d if a level load is in progress'%(n,D.u32(0xe0ff18)+1,n-1))
def frames(D,E,depth=0x2000):
    """kl2.exe return addresses on the stack: each must follow a call (rel32 into .text, or through a register/memory)."""
    st=D.read(D.reg['esp'],min(depth,D.have(D.reg['esp']))//4*4) or b''; out=[]; i=E.img
    for v, in struct.iter_unpack('<I',st):
        if E.code(v):
            o=v-E.B
            if (i[o-5]==0xe8 and E.code(v+struct.unpack_from('<i',i,o-4)[0])) or any(i[o-n]==0xff and (i[o-n+1]>>3)&7==2 for n in (2,3,6,7)): out.append(v)
    return out
def chain(fr): return ' < '.join('%#x%s'%(c,' ('+kl.CALLERS[c]+')' if c in kl.CALLERS else '') for c in fr)
if __name__=='__main__':
    D=kl.Dump(kl.path(sys.argv[1])); E=kl.Exe(); summary(D,E); at=D.addr
    if E.code(at):
        f=E.func(at); a=max(f,at-0x60) if f else at-0x40
        if f: print('function %#x'%f)
        for i in E.dis(a,at-a+0x10): print('   %#x %s %s%s%s'%(i.address,i.mnemonic,i.op_str,E.note(i.op_str),'   <==' if i.address==at else ''))
    fr=frames(D,E); print('stack: %d kl2.exe return addresses'%len(fr))
    for v in fr[:14]:
        strs=[t for i in E.dis(v-0x400,0x400) for m in re.findall(r'0x[0-9a-f]{6,8}',i.op_str) for t in [E.cstr(int(m,16))] if t]
        print('  %#x in %#x %s %s'%(v,E.func(v) or 0,kl.CALLERS.get(v,''),strs[-4:]))
