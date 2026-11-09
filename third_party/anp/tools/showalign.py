import sys; sys.path.insert(0,'tools')
from prpconv import Conv, fam
from scene import Scene
from pval import split_values, gen
C=Conv('dd_db.pkl')
S=Scene(sys.argv[1])
want=set(sys.argv[2:])
done=set()
def show(kind,key,props):
    vals=split_values(props)
    if kind=='g': vals=vals[:5]+[('b',[(0,6,0)])]+vals[5:]
    dmt=[('e',fam(v[1][0][2])) if v[0]=='e' else gen(v[0]) for v in vals]
    sig=C.choose_sig(kind,key,dmt)
    ddt=C.ddtoks(kind,key,sig)
    cost,path=C.align(dmt,ddt)
    line=[]
    for st in path:
        if st[0]=='m':
            v=vals[st[1]][1]; vv=v[0][2] if len(v)==1 else ('['+str(len(v))+']')
            line.append('%s=%s'%(dmt[st[1]][0] if isinstance(dmt[st[1]],tuple) else dmt[st[1]],str(vv)[:14]))
        elif st[0]=='i':
            d=C.default_for(kind,key,sig,st[1],sig[st[1]])
            line.append('+%s(%s)'%(sig[st[1]], str(d[0][2])[:14] if d and len(d)==1 else '..'))
        else:
            v=vals[st[1]][1]; vv=v[0][2] if len(v)==1 else '..'
            line.append('-%s(%s)'%(vals[st[1]][0],str(vv)[:14]))
    print('== %s %s cost %.1f'%(kind,key if isinstance(key,str) else hex(key),cost))
    print('   '+' '.join(line))
for n in S.nodes:
    t=0x100021 if n['idx']==0 else S.gms.ents[n['idx']-1]['type']
    if hex(t) in want and hex(t) not in done: done.add(hex(t)); show('g',t,n['props'])
    for name,evp in n['events']:
        if name in want and name not in done: done.add(name); show('e',name,evp)
