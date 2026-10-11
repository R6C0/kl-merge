"""Build a level .fxc: union of Dog Days permutations + alias entries for keys Dead Men materials need."""
import struct,pickle,sys,os
sys.path.insert(0,os.path.dirname(__file__))
IGN={'STDSAMPLERSTATE','USEDEFAULTREFLECTIONMAP'}
def load_keys(path):
    K=[]
    for l in open(path):
        l=l.strip()
        if not l: continue
        a,b=l.split(' : ') if ' : ' in l else (l.rstrip(' :'),'')
        kind,name=a.split(' ',1)
        K.append((int(kind),name.strip(),tuple(b.split())))
    return K
def score(want,have):
    if want[0]!=have[0] or want[1]!=have[1]: return None
    W,H=want[2],have[2]
    if not W or not H or W[0]!=H[0]: return None          # mesh type must match
    w=set(W[1:]); h=set(H[1:])
    if ('BLENDENABLED' in w)!=('BLENDENABLED' in h): return None
    missing=w-h; extra=(h-w)-IGN
    s=len(missing)*10+len(extra)*4
    if 'REFLECTIONENABLED' in missing and 'REFLECTIONENABLED' not in h: s+=5
    if 'STDSAMPLERSTATE' not in h: s+=1
    return s
def alias_record(raw,defs):
    r=bytearray(raw)
    r[12:12+0x800]=bytes(0x800)
    for i,n in enumerate(defs):
        r[12+64*i:12+64*i+len(n)]=n.encode(); r[12+64*i+32]=ord('1')
    return bytes(r)
def build(union,keys,log=print,base=None):
    recs=dict(base if base is not None else union); out=[]
    for k in keys:
        if k in recs: continue
        best=None
        for hk in union:
            sc=score(k,hk)
            if sc is not None and (best is None or sc<best[0]): best=(sc,hk)
        if best is None: log('NO DONOR %s'%(k,)); continue
        recs[k]=alias_record(union[best[1]],k[2]); log('alias %s <- %s (score %d)'%(' '.join((str(k[0]),k[1])+k[2]),' '.join(best[1][2]),best[0]))
    return assemble(list(recs.values())), len(recs)
def assemble(raws):
    out=bytearray(struct.pack('<4I',100,len(raws),0,16))
    for raw in raws:
        r=bytearray(raw); off=len(out)
        struct.pack_into('<I',r,0x80c,off+0x850)   # code offset (relative to file start; loader rebases)
        assert len(r)==0x850+struct.unpack_from('<I',r,8)[0]
        out+=r
    struct.pack_into('<I',out,8,len(out)-16)
    return bytes(out)
if __name__=='__main__':
    U=pickle.load(open(sys.argv[1],'rb')); K=load_keys(sys.argv[2])
    base=None
    if len(sys.argv)>4:
        from fxclib import parse
        ver,R=parse(open(sys.argv[4],'rb').read())
        base={(r['kind'],r['name'],tuple(x for x,_ in r['defs'])):r['raw'] for r in R}
    d,n=build(U,K,base=base); open(sys.argv[3],'wb').write(d); print('records',n,'bytes',len(d))
