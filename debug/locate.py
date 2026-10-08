"""locate.py <dump> [prp | level zip]   which node, record and field of which level the .prp reader stood in.
The reader's 16 KB buffer (from the dump) is searched in the .prp: with no file given, in every level archive under
<Dog Days>/Scenes. A level rebuilt since the crash no longer holds those bytes and is reported as not found.
Node k is .gms entity k-1 (node 0 = ROOT); the class is the type id in the .gms as installed, i.e. what the engine created."""
import bisect,glob,os,struct,sys,zipfile
import kl,buf as B
from kl_prp import Prp
import kl_convert as K,kl_gms
from kl_port_check import exe_classes

def sources(src=None):
    """(label, read) per .prp to try; read(ext) returns the sibling file with that extension or None."""
    if src and not src.lower().endswith('.zip'):
        def rd(ext,stem=src[:-3]):
            for e in (ext,ext.upper()):
                if os.path.isfile(stem+e): return open(stem+e,'rb').read()
        yield src,rd; return
    for zp in [src] if src else sorted(glob.glob(os.path.join(glob.escape(kl.DD),'Scenes','**','*.zip'),recursive=True)):
        z=zipfile.ZipFile(zp); low={n.lower():n for n in z.namelist()}
        for n in low:
            if n.endswith('.prp'): yield zp+'!'+low[n],(lambda ext,z=z,low=low,n=n: z.read(low[n[:-3]+ext]) if n[:-3]+ext in low else None)
def find(sb,src=None):
    """The .prp that holds the stream buffer exactly once -> (label, read, file offset of the buffer)."""
    for label,rd in sources(src):
        d=rd('prp'); i=d.find(sb)
        if sb and i>=0 and d.find(sb,i+1)<0: return label,rd,i
def entities(raw,names):
    """[(type id, name)] per node: record +0x14 is the class, +0x00 the offset of the name in the .buf."""
    t=struct.unpack_from('<I',raw,0)[0]; out=[(None,'ROOT')]
    for i in range(struct.unpack_from('<I',raw,t)[0]):
        rec=4*(struct.unpack_from('<I',raw,t+4+8*i)[0]&0xffffff); no=struct.unpack_from('<I',raw,rec)[0]
        e=names.find(b'\0',no) if names and no<len(names) else -1
        out.append((struct.unpack_from('<I',raw,rec+0x14)[0],names[no:e].decode('latin1') if e>=0 else '?'))
    return out
def show(p,tok):
    op,pl=tok
    if op in (0x0c,0x0e): return '%02x %s'%(op,p.key(tok))
    if op==0x0a: return '0a %g'%struct.unpack('<f',pl)[0]
    if op in (0x01,0x04,0x09): return '%02x %d'%(op,struct.unpack('<I',pl)[0])
    return '%02x %s'%(op,'raw[%d]'%(len(pl)-4) if op==0x0d else pl.hex())
def where(p,t):
    """Token index -> (node index, part of the node, that object's tokens or None, index of its first token, controller name)."""
    idx=len(p.settings)
    if t<idx: return None,'scene settings',None,0,None
    for ni,n in enumerate(p.nodes()):
        if t<idx+len(n['props']): return ni,'node properties',n['props'],idx,None
        idx+=len(n['props'])
        if t==idx: return ni,'controller count',None,idx,None
        idx+=1
        for ci,(name,body) in enumerate(n['ctrls']):
            if t==idx: return ni,'name of controller %d'%ci,None,idx,p.key(name)
            if t<=idx+len(body): return ni,'controller %d %s'%(ci,p.key(name)),body,idx+1,p.key(name)
            idx+=1+len(body)
        if t==idx: return ni,'child count',None,idx,None
        idx+=1
    return None,'after the scene tree',None,idx,None
def parents(p):
    par=[]; st=[(p.root,-1)]
    while st:
        n,pa=st.pop(); k=len(par); par.append(pa); st.extend((c,k) for c in reversed(n['children']))
    return par
def report(label,rd,base,pos):
    """Print where the reader stood; -> dict(node, cls, ctrl, csig, field) for the caller."""
    d=rd('prp'); p=Prp(d); q=0x1f+len(p.keyblob)+4; offs=[]
    for op,pl in p.tokens: offs.append(q); q+=1+len(pl)
    at=base+pos; t=bisect.bisect_right(offs,at-1)-1          # the token holding the last byte read
    print('level  '+label); print('buffer at file %#x, reader at %#x: last byte read %#x = %02x'%(base,at,at-1,d[at-1]))
    ni,part,obj,first,ctrl=where(p,t); gms=rd('gms'); r=dict(node=ni,cls=None,ctrl=ctrl,csig=None,field=None)
    ent=entities(kl_gms.unpack(gms),rd('buf')) if gms else []
    if ni is None: print(part)
    else:
        tid,name=ent[ni] if ni<len(ent) else (None,'?'); cls=exe_classes(os.path.join(kl.DD,kl.DD_EXE))[0]; par=parents(p); chain=[]; k=ni
        while k>=0: chain.append(ent[k][1] if k<len(ent) else str(k)); k=par[k]
        r['cls']='ROOT' if ni==0 else cls.get(tid,('?',))[0]
        print('NODE %d %r class %s %s | %s'%(ni,name,'%#x'%tid if tid else '',r['cls'],part))
        print('path   '+' > '.join(reversed(chain)))
        nd=p.nodes()[ni]; print('node   %s, %d controllers %s, %d children'%(K.csig(nd['props']),len(nd['ctrls']),[p.key(n) for n,_ in nd['ctrls']],len(nd['children'])))
    if obj:
        us=K.units(K.body(obj)); k=first+1; r['csig']=K.csig(obj); print('record %s: %d fields; reader is in token %d of %d'%(r['csig'],len(us),t-first,len(obj)))
        for i,u in enumerate(us):
            here=k<=t<k+len(u); k+=len(u)
            if here: r['field']=i
            print('  field %2d %-6s %s%s'%(i,K.unit_sig(u),' '.join(show(p,x) for x in u)[:110],'   <== last read' if here else ''))
    print('tokens:')
    for j in range(max(0,t-8),min(len(p.tokens),t+9)): print('  %s %d @%#x: %s'%('>>' if j==t else '  ',j,offs[j],show(p,p.tokens[j])[:100]))
    return r
if __name__=='__main__':
    D=kl.Dump(kl.path(sys.argv[1])); g=B.get(D,kl.Exe())
    if not g: sys.exit('no .prp reader in this dump')
    so,pos,size,buf=g; f=find(buf[:size],sys.argv[2] if len(sys.argv)>2 else None)
    if not f: sys.exit('the reader\'s buffer (%#x bytes) is in no .prp tried: the level was rebuilt since the crash, or pass the .prp/.zip the game read'%size)
    report(*f,pos)
