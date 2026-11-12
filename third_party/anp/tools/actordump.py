import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from prp import OPN
def fmt(props):
    out=[]; i=0
    for p,op,v in props:
        b=op&0x7f
        if b==1: out.append('[%d:'%v)
        elif b==0x7c: out.append(']')
        elif b==3: out.append('ref')
        elif b==10: out.append('%.3g'%v)
        elif b in (12,14): out.append(repr(v))
        elif b==4: out.append('C%d'%v)
        else: out.append(str(v))
    return ' '.join(out)
base=sys.argv[1]; tid=int(sys.argv[2],0); lim=int(sys.argv[3]) if len(sys.argv)>3 else 10
S=Scene(base)
n=0
for node in S.nodes[1:]:
    e=S.gms.ents[node['idx']-1]
    if e['type']!=tid: continue
    print(e['name'],'|',fmt(node['props']))
    for name,ev in node['events'][:12]: print('    ev',name, fmt(ev)[:200])
    n+=1
    if n>=lim: break
