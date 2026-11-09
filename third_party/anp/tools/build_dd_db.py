import sys, os, pickle, collections
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from pval import split_values, gen
def key_ops(opslice):
    return tuple((op,v if not isinstance(v,list) else tuple(v)) for p,op,v in opslice)
geom=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(collections.Counter)))
ev=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(collections.Counter)))
sigc_g=collections.defaultdict(collections.Counter); sigc_e=collections.defaultdict(collections.Counter)
for base in sys.argv[2:]:
    S=Scene(base)
    for n in S.nodes:
        t=0x100021 if n['idx']==0 else S.gms.ents[n['idx']-1]['type']
        vals=split_values(n['props']); sig=tuple(s for s,_ in vals)
        sigc_g[t][sig]+=1
        for i,(s,sl) in enumerate(vals):
            if len(sl)<=40: geom[t][sig][i][key_ops(sl)]+=1
        for name,evp in n['events']:
            vals=split_values(evp); sig=tuple(s for s,_ in vals)
            sigc_e[name][sig]+=1
            for i,(s,sl) in enumerate(vals):
                if len(sl)<=40: ev[name][sig][i][key_ops(sl)]+=1
    print('db',base,file=sys.stderr)
def freeze(d):
    return {k:{s:{i:c.most_common(3) for i,c in pos.items()} for s,pos in v.items()} for k,v in d.items()}
pickle.dump(dict(geom=freeze(geom),ev=freeze(ev),sigg={k:dict(v) for k,v in sigc_g.items()},sige={k:dict(v) for k,v in sigc_e.items()}),open(sys.argv[1],'wb'))
