"""Deterministic virtual-PCM mapping for Dead Men IMA-ADPCM stream entries (shared with ANP_Loader).
Dog Days streams only Ogg/PCM, so the loader serves each ADPCM entry as 16-bit PCM at a virtual
file offset >= VBASE; WHD streamed records are rewritten to point there."""
import struct,os,pickle
VBASE=0x60000000
def dm_adpcm_entries(path):
    f=open(path,'rb'); h=f.read(0x38)
    assert h[:12]==b'IOISNDSTREAM'
    tbl,cnt=struct.unpack_from('<II',h,0x18)
    f.seek(tbl); idx=f.read(cnt*72)
    E=[]
    for i in range(cnt):
        doff,size,moff=struct.unpack_from('<QQQ',idx,i*72+8)
        hsz=struct.unpack_from('<I',idx,i*72+32)[0]
        f.seek(moff); m=f.read(hsz)
        if len(m)>=36 and struct.unpack_from('<I',m)[0]==3:
            w=struct.unpack_from('<9I',m)
            E.append(dict(i=i,doff=doff,size=size,moff=moff,hsz=hsz,samples=w[1],ch=w[2],rate=w[3],balign=w[7],spb=w[8]))
    E.sort(key=lambda e:(e['doff'],e['i']))
    v=VBASE
    for e in E:
        e['pcm']=e['samples']*e['ch']*2; e['voff']=v; v+=(e['pcm']+0xFFF)&~0xFFF
    return E
def mapping(path, cache_dir=None):
    if cache_dir:
        cp=os.path.join(cache_dir,'strvirt_%d.pkl'%os.path.getsize(path))
        if os.path.exists(cp): return pickle.load(open(cp,'rb'))
    E=dm_adpcm_entries(path); M={e['doff']:e for e in E}
    if cache_dir: pickle.dump(M,open(cp,'wb'))
    return M
