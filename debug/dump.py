"""dump.py <dump> [--threads]   what faulted, registers, code before the fault, kl2.exe return addresses on the stack.
A dump without an exception record (KLHook_stall.dmp, KLHook_stackoverflow.dmp, KLHook_crt.dmp: written by the hook's
watchdog, not by a fault handler) is read from its first thread, the game's main thread; --threads lists every thread.
For a fault outside kl2.exe, a stack overflow and a watchdog dump the other modules on the stack are listed too."""
import collections,re,struct,sys
import kl
def summary(D,E):
    r=D.reg
    if D.code is None:
        if not r: print('no exception record and no thread list in this dump'); return
        print('no exception record (a dump the hook wrote from its watchdog): thread %d, the first of %d, stands at %#x %s'%(D.tid,len(D.threads),r['eip'],D.which(r['eip']) or '?'))
    else:
        at=D.addr; w=D.which(at) or '?'
        acc=' (%s address %#x)'%('writing' if D.info[0] else 'reading',D.info[1]) if D.code==0xc0000005 and len(D.info)>1 else ''
        print('code %#x at %#x %s%s'%(D.code,at,w,acc))
    print(' '.join('%s=%08x'%(k,r[k]) for k in 'eip esp ebp eax ebx ecx edx esi edi'.split()))
    if D.code is not None and kl.SITES.get(D.addr): print('site:',kl.explain(D.addr,r,D))
    n=D.u32(0xe0ff14)                                   # node loader 0x46fe20 counts the nodes it enters here; entity total at 0xe0ff18
    if n: print('node loader counter: %d of %d nodes entered -> node index %d if a level load is in progress'%(n,(D.u32(0xe0ff18) or 0)+1,n-1))
def frames(D,E,depth=0x2000,reg=None):
    """kl2.exe return addresses on the stack: each must follow a call (rel32 into .text, or through a register/memory)."""
    reg=reg or D.reg
    if not reg: return []
    st=D.read(reg['esp'],min(depth,D.have(reg['esp']))//4*4) or b''; out=[]; i=E.img
    for v, in struct.iter_unpack('<I',st):
        if E.code(v):
            o=v-E.B
            if (i[o-5]==0xe8 and E.code(v+struct.unpack_from('<i',i,o-4)[0])) or any(i[o-n]==0xff and (i[o-n+1]>>3)&7==2 for n in (2,3,6,7)): out.append(v)
    return out
def chain(fr): return ' < '.join('%#x%s'%(c,' ('+kl.CALLERS[c]+')' if c in kl.CALLERS else '') for c in fr) or '(no kl2.exe return address on the captured stack)'
def foreign(D,depth=0x4000,reg=None):
    """Values on the stack that point into other modules, in order of first appearance, repeats counted:
    [(module+offset, times)]. For a fault outside kl2.exe; in a stack overflow the group seen thousands of times is the loop."""
    reg=reg or D.reg
    if not reg: return []
    st=D.read(reg['esp'],min(depth,D.have(reg['esp']))//4*4) or b''; c=collections.Counter(); order=[]
    for v, in struct.iter_unpack('<I',st):
        w=D.which(v)
        if w and not w.lower().startswith('kl2.exe'):
            if w not in c: order.append(w)
            c[w]+=1
    return [(w,c[w]) for w in order]
def wants_foreign(D,E):
    at=D.addr if D.code is not None else D.reg.get('eip')
    return D.code is None or D.code==0xc00000fd or not (at and E.code(at))
def foreign_line(D,E):
    deep=D.code is None or D.code==0xc00000fd
    fo=foreign(D,0x400000 if deep else 0x4000)
    if deep: fo=sorted(fo,key=lambda x:-x[1])
    return 'other modules on the stack (%s): '%('most frequent first' if deep else 'in stack order')+(', '.join('%s x%d'%x for x in fo[:16]) or 'none')
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if not x.startswith('--')]
    D=kl.Dump(kl.path(a[0])); E=kl.Exe(); summary(D,E); at=D.addr if D.code is not None else D.reg.get('eip')
    if at and E.code(at):
        f=E.func(at); a0=max(f,at-0x60) if f else at-0x40
        if f: print('function %#x'%f)
        for i in E.dis(a0,at-a0+0x10): print('   %#x %s %s%s%s'%(i.address,i.mnemonic,i.op_str,E.note(i.op_str),'   <==' if i.address==at else ''))
    fr=frames(D,E); print('stack: %d kl2.exe return addresses'%len(fr))
    for v in fr[:14]:
        strs=[t for i in E.dis(v-0x400,0x400) for m in re.findall(r'0x[0-9a-f]{6,8}',i.op_str) for t in [E.cstr(int(m,16))] if t]
        print('  %#x in %#x %s %s'%(v,E.func(v) or 0,kl.CALLERS.get(v,''),strs[-4:]))
    if wants_foreign(D,E): print(foreign_line(D,E))
    if '--threads' in sys.argv:
        for tid,r in D.threads: print('thread %6d eip %08x %-28s esp %08x  kl2: %s'%(tid,r['eip'],D.which(r['eip']) or '?',r['esp'],chain(frames(D,E,0x400,r)[:4])))
