import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scene import Scene
def local_xf(node):
    vals=[v for p,op,v in node['props']]
    # props: e bounding, [9 floats], [3 floats], ...
    ops=node['props']; i=0
    # find first array of 9 and following array of 3
    arrs=[]; cur=None
    for p,op,v in ops:
        b=op&0x7f
        if b==1: cur=[]; continue
        if b==0x7c: arrs.append(cur); cur=None; continue
        if cur is not None: cur.append(v)
        if len(arrs)>=2: break
    return arrs[0], arrs[1]
def mmul(a,b):  # 3x3 row-major
    return [sum(a[r*3+k]*b[k*3+c] for k in range(3)) for r in range(3) for c in range(3)]
def mv(m,v): return [sum(m[r*3+k]*v[k] for k in range(3)) for r in range(3)]
def world(S, idx, conv):
    chain=[]; i=idx
    while i is not None and i>0:
        chain.append(i); i=S.nodes[i]['parent']
    M=[1,0,0,0,1,0,0,0,1]; T=[0,0,0]
    for i in reversed(chain):
        R,P=local_xf(S.nodes[i])
        if conv=='rowvec':   # world = local * parent : p_w = p_l*M_parent + T_parent
            T=[T[k]+sum(P[j]*M[j*3+k] for j in range(3)) for k in range(3)]
            M=mmul(R,M)
        else:                # column vectors: p_w = M_parent*p_l + T_parent
            T=[T[k]+mv(M,P)[k] for k in range(3)]
            M=mmul(M,R)
    return M,T
if __name__=='__main__':
    S=Scene(sys.argv[1]); pats=sys.argv[2].split(','); conv=sys.argv[3] if len(sys.argv)>3 else 'col'
    for node in S.nodes[1:]:
        e=S.gms.ents[node['idx']-1]
        if any(p in e['name'] for p in pats):
            M,T=world(S,node['idx'],conv)
            print(node['idx'],e['name'],'pos',[round(x,1) for x in T],'rot',[round(x,3) for x in M])
