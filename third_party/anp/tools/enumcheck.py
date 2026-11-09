import sys, os, pickle, collections
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from pval import split_values
def enums_of(ops):
    return [v for p,op,v in ops if op&0x7f==14]
def collect(bases):
    E=collections.defaultdict(collections.Counter)
    for base in bases:
        S=Scene(base)
        for n in S.nodes:
            t=0x100021 if n['idx']==0 else S.gms.ents[n['idx']-1]['type']
            for i,(s,sl) in enumerate(split_values(n['props'])):
                for v in enums_of(sl): E[('g',t,i)][v]+=1
            for name,evp in n['events']:
                for i,(s,sl) in enumerate(split_values(evp)):
                    for v in enums_of(sl): E[('e',name,i)][v]+=1
    return E
if __name__=='__main__':
    if sys.argv[1]=='build':
        E=collect(sys.argv[3:]); pickle.dump({k:dict(v) for k,v in E.items()},open(sys.argv[2],'wb'))
    else:
        DD=pickle.load(open(sys.argv[2],'rb'))
        allvals=collections.Counter()
        for k,v in DD.items(): allvals.update(v)
        E=collect([sys.argv[3]])
        for k,v in sorted(E.items(),key=str):
            dd=DD.get(k)
            for val,n in v.items():
                if dd is None or val not in dd:
                    print('MISSING',k[0],k[1] if isinstance(k[1],str) else hex(k[1]),k[2],repr(val),n,'| DD has:',list(dd)[:6] if dd else None, '| known elsewhere' if val in allvals else '')
