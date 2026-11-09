import sys, struct, collections
sys.path.insert(0,'tools')
from gms import load_gms
def read_ents(g, buf=None):
    h=struct.unpack_from('<20I',g); tab=h[0]; n=struct.unpack_from('<I',g,tab)[0]
    ents=[]
    for i in range(n):
        decl,u4=struct.unpack_from('<II',g,tab+4+i*8); off=4*(decl&0xFFFFFF)
        f=struct.unpack_from('<16I',g,off)
        ents.append(dict(decl=decl,off=off,type=f[5],prio=g[off+0x35]))
    return h,ents
def basetype_guess(t):
    if t & 0x100000: return 0
    if t in (0x20001c,0x200012): return 3
    if t & 0x800000 and not t&0x8000000: return 2
    if t & 0x200000 or t & 0x4000000: return 1
    return 3
def compute_blocks(ents, bt):
    # returns list of 24-int blocks: block0 = ROOT
    blocks=[[0]*24]; stack=[0]   # stack of block indices (current parent)
    for e in ents:
        rd=e['decl']>>25
        if rd: stack=stack[:len(stack)-rd]
        b=stack[-1]
        blocks[b][e['prio']*8+bt(e['type'])]+=1
        myblock=None
        if e['type'] & 0x100000:
            blocks.append([0]*24); myblock=len(blocks)-1
        if e['decl'] & 0x1000000:
            stack.append(myblock if myblock is not None else -999)
    return blocks
def read_blocks(g,h):
    n=struct.unpack_from('<I',g,h[5])[0]
    return [list(struct.unpack_from('<24I',g,h[5]+4+i*96)) for i in range(n)]
if __name__=='__main__':
    for p in sys.argv[1:]:
        g=load_gms(p); h,ents=read_ents(g)
        real=read_blocks(g,h); mine=compute_blocks(ents,basetype_guess)
        bad=sum(1 for a,b in zip(real,mine) if a!=b)
        print(p,'blocks real',len(real),'mine',len(mine),'mismatch',bad)
        if bad:
            for i,(a,b) in enumerate(zip(real,mine)):
                if a!=b: print('  first bad',i,a,b); break
def node_order(ents, bt=basetype_guess):
    """static node index per entity (runtime node table, verified on M01): node 0 = ROOT, then
    block-major (blocks numbered in preorder of group-type entities, block 0 = ROOT), then
    slot = prio*8 + basetype, then entity order."""
    stack=[0]; nb=1; key=[]
    for i,e in enumerate(ents):
        rd=e['decl']>>25
        if rd: stack=stack[:len(stack)-rd]
        key.append((stack[-1], e['prio']*8+bt(e['type']), i))
        my=None
        if e['type'] & 0x100000: my=nb; nb+=1
        if e['decl'] & 0x1000000: stack.append(my if my is not None else -999)
    order=sorted(range(len(ents)), key=lambda i: key[i])
    node=[0]*len(ents)
    for r,i in enumerate(order): node[i]=r+1
    return node
