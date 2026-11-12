import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
from evdump import fmt
base=sys.argv[1]; pats=sys.argv[2].split(','); depth=int(sys.argv[3]) if len(sys.argv)>3 else 1
S=Scene(base)
def show(idx,d):
    e=S.gms.ents[idx-1]; node=S.nodes[idx]
    print('  '*d+'%d %s %s | %s'%(idx,hex(e['type']),e['name'],fmt(node['props'])[:300]))
    for name,ev in node['events']: print('  '*d+'    ev %s %s'%(name,fmt(ev)[:400]))
    if d<depth:
        for c in node['children']: show(c,d+1)
for node in S.nodes[1:]:
    e=S.gms.ents[node['idx']-1]
    if any(p in e['name'] for p in pats): show(node['idx'],0)
