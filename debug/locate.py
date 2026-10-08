import struct,bisect,sys
sys.path.insert(0,'/home/claude/KL_PortTools')
from kl_prp import Prp
import kl_convert as K
d=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); pos=int(sys.argv[3],16)
base=None
for s in range(0,len(b)-64,0x100):
    i=d.find(b[s:s+64])
    if i>=0 and d.find(b[s:s+64],i+1)<0: base=i-s; break
target=base+pos; print('buffer base',hex(base),'file off',hex(target))
p=Prp(d)
off=struct.unpack_from('<I',d,0x1b)[0]; q=0x1f+off+4; offs=[]
for op,pl in p.tokens: offs.append(q); q+=1+len(pl)
t=bisect.bisect_right(offs,target)-1; print('token',t,p.tokens[t])
def show(o): return [(hex(op),p.key((op,pl)) if op in(12,14) else pl.hex()[:40]) for op,pl in o]
idx=len(p.settings)
for ni,n in enumerate(p.nodes()):
    s=idx; idx+=len(n['props'])
    if s<=t<idx: print('NODE',ni,'props tok',t-s, K.csig(n['props'])); print(show(n['props'])[:80]); break
    idx+=1; hit=False
    for name,body in n['ctrls']:
        cs=idx; idx+=1+len(body)
        if cs<=t<idx: print('NODE',ni,'ctrl',p.key(name),'tok',t-cs,K.csig(body)); print(show(body)[:80]); hit=True
    if hit: break
    idx+=1
