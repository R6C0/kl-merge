"""rtti.py <hex code address> ...   the function around each address and the classes whose vtables hold it (class, slot)."""
import re,struct,sys
import kl
def owners(E,fn):
    """[(class, slot)] for every vtable entry pointing at fn."""
    a,b=E.sec['.rdata']; r=E.img[a-E.B:b-E.B]; out=[]
    for m in re.finditer(re.escape(struct.pack('<I',fn)),r):
        if m.start()%4: continue
        v=a+m.start()
        for k in range(400):                            # walk back over code pointers to the vtable start: an RTTI locator precedes it
            c=E.rtti(v-4*k)
            if c: out.append((c,k)); break
            if not E.code(E.u32(v-4*k-4) or 0): break   # not inside a vtable
    return out
if __name__=='__main__':
    E=kl.Exe()
    for ra in [int(x,16) for x in sys.argv[1:]]:
        f=E.func(ra); o=owners(E,f) if f else []
        print(hex(ra),'func',hex(f) if f else None,kl.CALLERS.get(ra,''),o[:6],'(+%d more)'%(len(o)-6) if len(o)>6 else '')
