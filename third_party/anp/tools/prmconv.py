"""Dead Men -> Dog Days .PRM (geometry chunk store) conversion.

File = chunk 0 (header: tableOff, count, tableOff, 0) + contiguous 16-aligned chunks + table of
(offset, size, refcount, 0) per chunk.  Objects reference chunks by index.

Prim  (0x70100, 64B):  ... [5]=#meshes [6]=mesh list chunk
Mesh  (0x8xxxx, 64/128B): ... [10]=geometry-descriptor list chunk (16B: up to 4 descriptor handles)
Geometry descriptor:
   Dead Men  32B: nVerts, vbChunk, n2, ibChunk, litStream, litInfo, 0, 0
   Dog Days  48B: nVerts, vbChunk, 0,0,0, n2, ibChunk, 0,0,0,0,0
Vertex / index buffers are byte-identical between the games.
"""
import struct,collections
def convert_prm_dm_to_dd(d, rep=None, extra_chunks=(), ref_add=None):
    """ref_add = {chunk index: n}: n added to that chunk's refcount (table word 2; grafted chunks start at 1)"""
    rep=rep if rep is not None else collections.Counter()
    off,cnt,off2,_=struct.unpack_from('<4I',d)
    desc=[struct.unpack_from('<4I',d,off+i*16) for i in range(cnt)]
    chunks=[bytearray(d[o:o+s]) for (o,s,k,u) in desc]
    def w(i):
        c=chunks[i]; return struct.unpack_from('<%dI'%(len(c)//4),c)
    ok=lambda h: 0<h<cnt
    meshes=set()
    for i,c in enumerate(chunks):
        if len(c)==64 and struct.unpack_from('<I',c)[0]==0x70100:
            p=w(i)
            if ok(p[6]):
                lst=w(p[6])
                for m in lst[:p[5]]:
                    if ok(m): meshes.add(m)
    gds=set()
    for m in meshes:
        mw=w(m); cls=mw[0]>>16
        rep['mesh type %x/%d'%(mw[0],len(chunks[m]))]+=1
        if cls!=8: continue
        if not ok(mw[10]): continue
        for g in w(mw[10]):
            if ok(g): gds.add(g)
    for g in sorted(gds):
        c=chunks[g]
        if len(c)==32:
            x=struct.unpack_from('<8I',c)
            # DM words 4/5 = baked per-vertex lighting stream + its info chunk; Dog Days has no slot
            # for it in L01 data (words 2-4 always 0) -> dropped for now (lighting comes from DD's renderer)
            if x[4] or x[5]: rep['gd baked-lighting stream dropped']+=1
            if x[6] or x[7]: rep['gd unknown tail words']+=1
            chunks[g]=bytearray(struct.pack('<12I',x[0],x[1],0,0,0,x[2],x[3],0,0,0,0,0))
            rep['gd converted']+=1
        elif len(c)==48: rep['gd already 48']+=1
        else: rep['gd odd size %d'%len(c)]+=1
    # EXPERIMENT (env ANP_EXP_MAT=prim:mat): force all meshes of a prim to one material
    import os as _os
    exp=_os.environ.get('ANP_EXP_MAT')
    if exp:
        ep,em=[int(x) for x in exp.split(':')]
        pw=w(ep)
        for m in w(pw[6])[:pw[5]]:
            c=chunks[m]; x=struct.unpack_from('<I',c,16)[0]
            struct.pack_into('<I',c,16,(em<<16)|(x&0xffff)); rep['EXP material forced']+=1
    # EXPERIMENT (env ANP_EXP_FLAG=hex): OR this value into word7 (render flags) of every 0x80089 mesh with flags 0x880
    fx=_os.environ.get('ANP_EXP_FLAG')
    if fx:
        fv=int(fx,16)
        for m in meshes:
            c=chunks[m]
            if struct.unpack_from('<I',c,0)[0]==0x80089 and struct.unpack_from('<I',c,28)[0]==0x880:
                struct.pack_into('<I',c,28,0x880|fv); rep['EXP flag set']+=1
    # rebuild
    out=bytearray(16); table=[]
    table.append((0,16,desc[0][2],0))
    for i in range(1,cnt):
        c=chunks[i]
        assert len(c)%16==0
        table.append((len(out),len(c),desc[i][2],desc[i][3])); out+=c
    for c in extra_chunks:                      # grafted chunks get indices cnt, cnt+1, ...
        c=bytes(c)+b'\0'*((-len(c))&15)
        table.append((len(out),len(c),1,0)); out+=c
    cnt+=len(extra_chunks)
    if extra_chunks: rep['prm grafted chunks']+=len(extra_chunks)
    for i,n in sorted((ref_add or {}).items()):
        assert 0<i<cnt and table[i][2]+n>=1, ('prm ref_add', i, n)
        o_,s_,r_,u_=table[i]; table[i]=(o_,s_,r_+n,u_)
    if ref_add: rep['prm refcounts raised on %d chunks (ANP_COVERS)'%sum(1 for n in ref_add.values() if n)]+=1
    toff=len(out)
    struct.pack_into('<4I',out,0,toff,cnt,toff,0)
    for t in table: out+=struct.pack('<4I',*t)
    return bytes(out), rep
if __name__=='__main__':
    import sys
    o,rep=convert_prm_dm_to_dd(open(sys.argv[1],'rb').read())
    open(sys.argv[2],'wb').write(o)
    for k,v in sorted(rep.items()): print(k,v)
