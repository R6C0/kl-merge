import sys, os, collections, json, pickle
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from prp import OPN
ABBR={5:'c',6:'b',7:'i8',8:'i16',9:'i',10:'f',11:'d',12:'s',13:'raw',14:'e',15:'sa',16:'bf',3:'ref'}
def read_value(ops,i):
    p,op,v=ops[i]; b=op&0x7f
    if b==1:
        j=i+1; els=[]
        while ops[j][1]&0x7f!=0x7c:
            s,j=read_value(ops,j); els.append(s)
        u=sorted(set(els))
        if len(u)==1: sig='A%d[%s]'%(v,u[0]) if v<=16 else 'A*[%s]'%u[0]
        elif not u: sig='A0'
        else: sig='A%d(%s)'%(v,','.join(els)) if v<=16 else 'A*{%s}'%('|'.join(u))
        return sig,j+1
    if b==4:
        if i+1<len(ops) and ops[i+1][1]&0x7f==13:
            return 'C:raw',i+2
        j=i+1; els=[]
        for k in range(v):
            s,j=read_value(ops,j); els.append(s)
        u=sorted(set(els))
        return 'C{%s}'%('|'.join(u)),j
    if b==2:
        j=i+1; els=[]
        while ops[j][1]&0x7f!=0x7e:
            s,j=read_value(ops,j); els.append(s)
        return 'O(%s)'%' '.join(els),j+1
    return ABBR.get(b,hex(b)),i+1
def obj_sig(props):
    j=0; els=[]
    while j<len(props):
        s,j=read_value(props,j); els.append(s)
    return ' '.join(els)
def build(paths):
    geom=collections.defaultdict(collections.Counter); ev=collections.defaultdict(collections.Counter)
    gex={}; 
    for base in paths:
        S=Scene(base)
        for n in S.nodes:
            t=0x100021 if n['idx']==0 else S.gms.ents[n['idx']-1]['type']
            sg=obj_sig(n['props']); geom[t][sg]+=1
            for name,evp in n['events']:
                ev[name][obj_sig(evp)]+=1
        print('done',base,file=sys.stderr)
    return geom,ev
if __name__=='__main__':
    out=sys.argv[1]; paths=sys.argv[2:]
    g,e=build(paths)
    pickle.dump((dict(g),dict(e)),open(out,'wb'))
