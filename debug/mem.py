"""mem.py <dump> <hex address> ...   0x80 bytes at each address, if the dump holds them."""
import sys
import kl
D=kl.Dump(kl.path(sys.argv[1]))
print('memory ranges',len(D.mem),'total',sum(m[1] for m in D.mem))
for a in [int(x,16) for x in sys.argv[2:]]:
    b=D.read(a,min(0x80,D.have(a))); print(hex(a), b.hex(' ') if b else 'not in dump')
