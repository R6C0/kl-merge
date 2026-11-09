import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from prp import OPN
T={6:'b',7:'i8',8:'i16',9:'i',10:'f',12:'s',14:'e',3:'ref',16:'bf'}
def fmt(props):
    out=[]
    for p,op,v in props:
        b=op&0x7f
        if b==1: out.append('[%d:'%v)
        elif b==0x7c: out.append(']')
        elif b==4: out.append('C%d'%v)
        elif b==10: out.append('f%.4g'%v)
        elif b in (12,14): out.append(T[b]+repr(v)[:40])
        else: out.append(T.get(b,OPN.get(b,'?'))+str(v))
    return ' '.join(out)
if __name__=="__main__":
    base=sys.argv[1]; evname=sys.argv[2]; lim=int(sys.argv[3]) if len(sys.argv)>3 else 10
    S=Scene(base)
    seen=collections.Counter(); n=0
    for node in S.nodes[1:]:
        for name,ev in node['events']:
            if name!=evname: continue
            s=fmt(ev); seen[s]+=1
    for s,c in seen.most_common(lim): print(c,'|',s)
