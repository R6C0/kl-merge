# value-tree helpers over PRP op lists
from prp import OPN
ABBR={5:'c',6:'b',7:'i8',8:'i16',9:'i',10:'f',11:'d',12:'s',13:'raw',14:'e',15:'sa',16:'bf',3:'ref'}
def read_value(ops,i):
    """returns (sig, j) where ops[i:j] is the value"""
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
        if i+1<len(ops) and ops[i+1][1]&0x7f==13: return 'C:raw',i+2
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
def split_values(ops):
    """split an object's prop ops into top-level values: list of (sig, opslice)"""
    out=[]; j=0
    while j<len(ops):
        s,k=read_value(ops,j); out.append((s,ops[j:k])); j=k
    return out
def gen(sig):
    """generalised token for matching"""
    if sig.startswith('C'): return 'C'
    if sig.startswith('A*'): return 'A*'
    return sig
