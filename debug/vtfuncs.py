"""vtfuncs.py <Class> [text ...]   vtable slots of a class: slot, function, instruction count.
With texts, only the functions whose disassembly (up to the first ret) contains all of them, e.g.  vtfuncs.py ZROOM 0x74"""
import sys
import kl
def slots(E,vt):
    k=0
    while E.code(E.u32(vt+4*k) or 0) and not (k and E.rtti(vt+4*k)): yield k,E.u32(vt+4*k); k+=1
if __name__=='__main__':
    E=kl.Exe(); want=sys.argv[2:]
    for vt in E.vtables(sys.argv[1])[:1]:
        print('vtable',hex(vt))
        for k,f in slots(E,vt):
            txt=[]
            for ins in E.dis(f,0x600):
                txt.append(ins.mnemonic+' '+ins.op_str)
                if ins.mnemonic=='ret': break
            if all(w in ' ; '.join(txt) for w in want): print(k,hex(f),len(txt),txt[0] if len(txt)<3 else '')
