import sys, struct, collections
sys.path.insert(0, __import__('os').path.dirname(__file__))
from prp import PRP, OPN
from gms import GMS
def sig_of(ops):
    out=[]
    for p,op,v in ops:
        b=op&0x7f
        n=OPN.get(b,hex(b))
        if b in (1,4): out.append('%s%d'%(n[0],v) if b==1 else 'C')
        else: out.append(n)
    return ' '.join(out)
class Scene:
    def __init__(s, base):
        s.base=base
        s.prp=PRP(open(base+'.prp','rb').read())
        s.gms=GMS(base+'.gms', base+'.buf'); s.gms.depth_tree()
        s.ops=list(s.prp.instrs())
        # skip defines: find index of first BeginObject
        s.k=next(i for i,(p,op,v) in enumerate(s.ops) if op&0x7f==2)
        s.nodes=[]
        s.pos=s.k
        s.root=s.parse_node(None)
    def take_obj(s):
        ops=s.ops; i=s.pos
        assert ops[i][1]&0x7f==2, ('expected BeginObject', hex(ops[i][0]), ops[i])
        depth=0; j=i
        while True:
            b=ops[j][1]&0x7f
            if b==2: depth+=1
            elif b==0x7e:
                depth-=1
                if depth==0: break
            j+=1
        s.pos=j+1
        return ops[i+1:j]
    def take(s, base):
        p,op,v=s.ops[s.pos]
        assert op&0x7f==base, ('expected',OPN[base],'got',hex(p),OPN.get(op&0x7f),v)
        s.pos+=1; return v
    def parse_node(s, parent):
        start=s.ops[s.pos][0]
        props=s.take_obj()
        nev=s.take(4); events=[]
        for e in range(nev):
            name=s.take(12)
            ev=s.take_obj()
            events.append((name,ev))
        node=dict(props=props,events=events,parent=parent,start=start,children=[])
        idx=len(s.nodes); s.nodes.append(node)
        node['idx']=idx
        # children container present only for groups -> peek
        if True:
            nch=s.take(4)
            for c in range(nch):
                node['children'].append(s.parse_node(idx))
        return idx
    def is_group(s, idx):
        e=s.gms.ents[idx-1]
        return bool(e['decl']&0x1000000)
if __name__=='__main__':
    S=Scene(sys.argv[1])
    print('nodes',len(S.nodes),'gms ents',len(S.gms.ents),'pos',S.pos,'of',len(S.ops), S.ops[S.pos] if S.pos<len(S.ops) else None)
