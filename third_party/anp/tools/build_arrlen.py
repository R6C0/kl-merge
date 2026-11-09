import sys, os, pickle, collections
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from pval import split_values
L=collections.defaultdict(collections.Counter)
for base in sys.argv[2:]:
    S=Scene(base)
    for n in S.nodes:
        t=0x100021 if n['idx']==0 else S.gms.ents[n['idx']-1]['type']
        vals=split_values(n['props']); sig=tuple(s for s,_ in vals)
        for i,(s,sl) in enumerate(vals):
            if sl[0][1]&0x7f==1 and s.startswith('A*'): L[('g',t,sig,i)][sl[0][2]]+=1
        for name,evp in n['events']:
            vals=split_values(evp); sig=tuple(s for s,_ in vals)
            for i,(s,sl) in enumerate(vals):
                if sl[0][1]&0x7f==1 and s.startswith('A*'): L[('e',name,sig,i)][sl[0][2]]+=1
pickle.dump({k:dict(v) for k,v in L.items()},open(sys.argv[1],'wb'))
for k,v in L.items():
    if len(v)==1: print(k[0],k[1] if isinstance(k[1],str) else hex(k[1]),k[3],dict(v))
