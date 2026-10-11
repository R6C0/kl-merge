"""Dead Men -> Dog Days .SND (sound definition database) conversion.

Layout (both games):  u32 dirOff, u32 fileSize, u32 3, u32 4, then 16-byte language
stream-name records ("PC_Def.str", ...), sound records ..., and at dirOff a directory:
  [0] u32 ?
  [1..N] u32 offsets of the language stream names   (DM: N=6, DD: N=10)
  then  0xcdcdcdcd, stamp(2 u32), u32, counts[25], offsets[25], (count,offset) pairs ...
Dog Days code reads counts at dir+0x3c and offsets at dir+0xa0, i.e. it expects 10
language slots.  All other offsets in the file are file-relative, so we only append
the extra language names and rebuild the directory at the end of the file.
"""
import struct
DD_LANGS=['Def','Eng','Ger','Fre','Spa','Ita','Dut','Rus','Pol','Jap']
CDCD=0xcdcdcdcd

def convert_snd_dm_to_dd(d, stream_dir=None, fallback='Eng', hide_types=()):
    """stream_dir: if given (e.g. '..\\\\Kane and Lynch Dead Men\\\\'), stream names are rewritten
    to point at the Dead Men .str files there (they hold DM's streamed dialogue)."""
    h0,size,a,b=struct.unpack_from('<4I',d,0)
    assert size==len(d) and (a,b)==(3,4), (size,len(d),a,b)
    nw=(len(d)-h0)//4
    w=list(struct.unpack_from('<%dI'%nw,d,h0))
    nl=w.index(CDCD)-1
    if nl==10: return d, 'already DD'
    assert nl==6, nl
    names=[]
    for i in range(nl):
        o=w[1+i]; e=d.index(b'\0',o); names.append(d[o:e].decode('latin1'))
    have={n[3:6]:n for n in names}            # 'PC_Eng.str' -> 'Eng'
    body=bytearray(d[:h0])
    def add_name(s):
        while len(body)%16: body.append(0)
        off=len(body); body.extend(s.encode('latin1')+b'\0')
        return off
    offs=[]
    for L in DD_LANGS:
        src=have.get(L) or have.get(fallback)
        if stream_dir is not None:
            offs.append(add_name(stream_dir+src))
        elif L in have:
            offs.append(w[1+DD_LANGS.index(L)] if DD_LANGS.index(L)<nl else add_name(src))
        else:
            offs.append(add_name(src))
    while len(body)%16: body.append(0)
    newdir=[w[0]]+offs+w[1+nl:]
    # hide record types from the directory (count 0) - e.g. 0x12 dialogue banks whose DM stream
    # records DD misreads (until the record conversion exists)
    c0=1+10+4
    for t in hide_types: newdir[c0+t]=0
    newh0=len(body)
    out=body+struct.pack('<%dI'%len(newdir),*newdir)
    struct.pack_into('<II',out,0,newh0,len(out))
    return bytes(out), 'langs %d->10'%nl

if __name__=='__main__':
    import sys
    d=open(sys.argv[1],'rb').read()
    # in-game stream folder, must end in '\'. Windows argument parsing turns a quoted trailing backslash into '"'.
    sd=sys.argv[3].rstrip('"\\')+'\\' if len(sys.argv)>3 else None
    o,msg=convert_snd_dm_to_dd(d, sd)
    open(sys.argv[2],'wb').write(o); print(msg,len(d),'->',len(o))

def convert_ls_snd(d, main_snd_converted):
    """*_LS.SND (loading-screen overlay): header word 0 mirrors the main SND directory offset."""
    h0,size,a,b=struct.unpack_from('<4I',d,0)
    assert size==len(d) and (a,b)==(3,4)
    newh0=struct.unpack_from('<I',main_snd_converted,0)[0]
    out=bytearray(d); struct.pack_into('<I',out,0,newh0)
    return bytes(out), 'ls dir %d->%d'%(h0,newh0)

def mute_snd_from_dm(d, stream_dir=None):
    """Valid Dog Days SND directory with no sound records (all counts 0).
    Used until the per-record conversion (type 1 sample records changed layout in DD) is done:
    every sound lookup then fails cleanly instead of feeding DM records to DD's player/streamer."""
    conv,_=convert_snd_dm_to_dd(d, stream_dir)
    h0=struct.unpack_from('<I',conv,0)[0]
    nw=(len(conv)-h0)//4
    w=list(struct.unpack_from('<%dI'%nw,conv,h0))
    nl=10
    langs=w[1:1+nl]
    # keep header bytes up to the first language name end, rebuild a compact body
    body=bytearray(conv[:16])
    newl=[]
    for o in langs:
        e=conv.index(b'\0',o); s=conv[o:e]+b'\0'
        while len(body)%16: body.append(0)
        newl.append(len(body)); body+=s
    while len(body)%16: body.append(0)
    c0=1+nl+4
    hdr=w[1+nl:c0]                      # cdcd, stamp lo, stamp hi, x
    rest=[0]*(nw-(c0+50))
    if rest: rest[-1]=w[-1]
    nd=[16]+newl+hdr+[0]*25+[0]*25+rest
    newh0=len(body)
    out=body+struct.pack('<%dI'%len(nd),*nd)
    struct.pack_into('<II',out,0,newh0,len(out))
    return bytes(out),'muted (no records)'


# ---------------------------------------------------------------------------------------------
# Streamed-sound fixes that need the original Dead Men .WHD (11 Oct, sound workflow).
#
# 1. Layered streams.  A layered stream is one interleaved data block described by a head record
#    (layer byte = 0x80|n) followed by n-1 layer records (layer byte = k).  Every record has the same
#    data offset.  Dog Days reads the layers at a 0x48 stride from the head (kl2 0x4b20e8, 0x4b2388,
#    0x4b23e0: rate +0xc, bits +0x10, size +0x14, +0x18, channels +0x1c, LIP word +0x34) and a layer
#    record referenced on its own goes back to its head as record - k*0x48.  Dead Men records are 15
#    words (0x3c) and its layers sit at a 0x3c stride, so Dog Days read neighbouring bytes as layers
#    (M02: divide by zero 0x4b240e then int3 0x522acb; M08: 18.7 MB read).  Clearing the layer byte
#    (whdconv default since 11 Oct) avoids the garbage but plays the interleaved block as one plain
#    stream (noise), and the SND still references the Dead Men layer records (head+0x3c*k, layer
#    byte k) whose 'head' then lands 0xc bytes before the real one.
#    Fix: every Dead Men group is rewritten in Dog Days layout (18-word records, 0x48 stride) after
#    the last record (before the empty directory), and the SND type-4 items that point at the old
#    head/layer offsets are pointed at the new ones.  89983 two-layer groups and 13 3/4-layer music
#    groups over the 16 levels; Dog Days' own L05 music uses the same layered PCM form.
# 2. LIP flag.  Record word 13 (Dog Days; Dead Men word 12) low half == 4 exactly when the stream data
#    starts with a 'LIP ' lip-sync chunk (checked on every streamed record of both games: DD 30387/0
#    exceptions, DM 35134/0).  whdconv set 4 on every ADPCM stream it points at the loader's virtual
#    PCM, so Dog Days parsed PCM samples as a LIP chunk header on the 445 streams that have none
#    (M01's first streamed sound, Propane_Tank_Anim_01, is one).  Fix: 4 only where Dead Men's
#    stream has the chunk, else 0.  Dead Men keeps the chunk in ADPCM block 0 (blocks 1.. are audio);
#    the loader serves that block as the LIP chunk + silence (it used to decode it as ADPCM).
# Switches: ANP_SND_LAYERS=dd (default) | off ; ANP_SND_LIPFLAG=1 (default) | 0
# ---------------------------------------------------------------------------------------------
import os
SND_LAYERS=os.environ.get('ANP_SND_LAYERS','dd')
SND_LIPFLAG=os.environ.get('ANP_SND_LIPFLAG','1')=='1'
DM_REC=0x3c; DD_REC=0x48

def _dm_heads(dm_whd):
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from whdconv import find_records
    return find_records(dm_whd)

def layer_plan(dm_whd):
    """Dead Men layered groups -> new Dog Days positions after the record area.
    Returns {'base': h0, 'groups': [(old_head, n, new_head)], 'map': {old_off: new_off}, 'skipped': [...]}"""
    h0=struct.unpack_from('<I',dm_whd,0)[0]
    plan={'base':h0,'groups':[],'map':{},'skipped':[]}
    if SND_LAYERS!='dd' or h0==0: return plan
    pos=(h0+15)&~15
    for o in sorted(_dm_heads(dm_whd)):
        w=struct.unpack_from('<15I',dm_whd,o); lay=w[2]>>24
        if not (lay&0x80): continue
        n=lay&0x7f; ok=n>=2
        for k in range(1,n):
            q=o+DM_REC*k
            if q+DM_REC>h0: ok=False; break
            l=struct.unpack_from('<15I',dm_whd,q)
            if l[0]!=0 or (l[2]>>24)!=k or (l[2]&0xffff)!=(w[2]&0xffff) or l[8]!=w[8]: ok=False; break
        if not ok: plan['skipped'].append(o); continue
        plan['groups'].append((o,n,pos))
        for k in range(n): plan['map'][o+DM_REC*k]=pos+DD_REC*k
        pos+=(DD_REC*n+15)&~15
    return plan

def _dd_record(w15, lay):
    """Dead Men 15-word record -> Dog Days 18-word record (data offset widened to 64 bits)."""
    w=list(w15)
    w[2]=(w[2]&0x00ffffff)|(lay<<24)
    return w[0:9]+[0]+w[9:13]+[0,0,0,0]

LIP_BLOCK=4096
def whd_postfix(dm_whd, conv_whd, plan=None, stream_map=None, lang_maps=None):
    """Apply the layered-group relayout and the LIP fixes to a whdconv output.  conv_whd must be
    the in-place conversion of dm_whd (same size).  lang_maps: as for whdconv (records in a language stream file).
    Returns (bytes, stats)."""
    st={'whd layered groups relaid':0,'whd layered groups skipped':0,'whd virtual pcm LIP flag fixed':0,
        'whd virtual pcm with LIP block resized':0}
    out=bytearray(conv_whd)
    h0=struct.unpack_from('<I',dm_whd,0)[0]
    if h0==0 or len(conv_whd)!=len(dm_whd): return bytes(out),st
    if SND_LIPFLAG:
        # Virtual PCM (loader): LIP word 4 (one 4 KB LIP block) when Dead Men's stream starts with one, else 0.
        # The high half stays 0: Dead Men's ADPCM data holds a single LIP chunk whatever its high half says,
        # and kl2 0x4b221d sizes ceil(size/(hi KB)) extra LIP blocks from it.
        # Dead Men's LIP block is 4 KB = ADPCM blocks 0-3 (audio from block 4; the meta sample count includes
        # the 4 blocks).  The loader (lip=1) serves [4 KB LIP block verbatim][PCM of blocks 4..], so the record
        # gets size 4096 + (samples - 4*spb)*ch*2 and that many samples.
        for o in _dm_heads(dm_whd):
            dw=struct.unpack_from('<15I',dm_whd,o); cw=list(struct.unpack_from('<16I',out,o))
            if (dw[2]&0xffff)!=0x11 or (cw[2]&0xffff)!=1: continue
            lip=bool(dw[12]&0xffff)
            want=4 if lip else 0
            if cw[13]!=want: cw[13]=want; st['whd virtual pcm LIP flag fixed']+=1
            sm=stream_map
            if (dw[2]>>16)&0x40: sm=lang_maps.get(o) if lang_maps else None    # language file record (ANP_SND_LANGS)
            e=sm.get(dw[8]) if sm else None
            if lip and e and LIP_BLOCK%e['balign']==0:
                aud=max(0,e['samples']-(LIP_BLOCK//e['balign'])*e['spb'])
                cw[5]=cw[6]=LIP_BLOCK+aud*e['ch']*2; cw[10]=aud*e['ch']
                st['whd virtual pcm with LIP block resized']+=1
            struct.pack_into('<16I',out,o,*cw)
    if plan and plan['groups']:
        tail=bytes(out[h0:])                          # empty directory
        out=out[:h0]
        for o,n,new in plan['groups']:
            while len(out)<new: out.append(0)
            for k in range(n):
                w=struct.unpack_from('<15I',dm_whd,o+DM_REC*k)
                out+=struct.pack('<18I',*_dd_record(w,(0x80|n) if k==0 else k))
            st['whd layered groups relaid']+=1
        while len(out)%16: out.append(0)
        newh0=len(out); out+=tail
        struct.pack_into('<II',out,0,newh0,len(out))
        st['whd layered groups skipped']=len(plan['skipped'])
    return bytes(out),st

# ---------------------------------------------------------------------------------------------
# Sound definition records (11 Oct, sound round 2).  The SND conversion above only rebuilt the directory and
# kept Dead Men's records byte for byte, but three record layouts differ between the games:
#
# Type 1 (sound, parsed by kl2 0x7a1200).  Dead Men 0x30 bytes, Dog Days 0x40:
#   DM  [1,cdcd,name,cdcd000N,props,wave, f6,       w7,  w8, w9, w10(+0x28 b0,vol,b2,b3), w11 cdcdcdLL]  then the next item
#   DD  [1,cdcd,name,cdcd000N,props,wave, f6, f7,   w7,  w8, w9, w10(+0x2c b0,vol,b2,b3), w12 cd0000LL, 0,0,0]
#   kl2 reads +0x18 f6, +0x1c f7 (obj+0xc8), +0x20..+0x2b the three DM words, +0x2c priority-ish byte (obj+0x130),
#   +0x2d volume % (signed, clamped 0..100 -> obj+0x13c; final gain = x * vol% * obj+0xf8, 0x8c5e50), +0x2e bit0 loop,
#   +0x2f byte, +0x30 loop count (obj+0x13b, >1 sets flag 0x400000, 0x8d1ed0), +0x31/+0x32 bools.
#   Unconverted, kl2 read the volume from Dead Men's 0xcd padding (-51 -> 0 %): every Dead Men sound played at gain 0
#   (M01 digital silence while its streams kept being read), and the loop count from the next item's name ('a' = 97).
#   DM's w11 low byte is DD's +0x30 loop count (both: 1 exactly on the looping sounds, checked on DM M01 / DD L01).
#   Fix (ANP_SND_T1=dd): rewrite +0x1c..+0x2f in place as [f7=0.0 (DD's commonest), w7, w8, w9, w10]; the 16 bytes at
#   +0x30 belong to the next item, which is nearly always a name string referenced only by record name fields: that
#   string is copied to the end of the record area, its references are re-pointed, and the DD tail [LL,0,0,cd, 0*12]
#   is written in its place.  Followers that cannot be moved are left (stats: 'type-1 tail not movable').
#   ANP_SND_T1=inplace = only the +0x1c..+0x2f rewrite; off = untouched (silent, the old behaviour).
#   ANP_SND_T1_B0=keep (default) | zero: Dead Men's +0x28 byte (4/6/10 occur; Dog Days only uses 0/2/5/8).
# Type 7 (EAX-style reverb preset, kl2 0x5fff30 feeds rec+0x1c.. to alEffectf AL_REVERB_*):
#   DM  w6 env, w7 size, w8 diffusion 0..1, w9 room mB (int), w10 roomHF (int), w11 roomLF, w12 decay, w13 HF ratio,
#       w14 LF ratio, w15 reflections (int), w16 refl delay, w17 reverb (int), w18 reverb delay, ..., w24 HF reference
#   DD  w6 env, w7 density %, w8 diffusion %, w9 gain mB, w10 gainHF mB, w11 decay, w12 HF ratio, w13 refl mB,
#       w14 refl delay, w15 late mB, w16 late delay, w17 HF reference, w18 0, w19 0   (all floats)
#   ANP_SND_REVERB=dd (default) | off.  Rewritten in place (DM records are >= 0x70 bytes).
# *_LS.SND (loading-screen overlay): header + an array of type-1 records, 0x30 stride in DM, 0x40 in DD.
#   ANP_SND_LS=dd (default) | off.  Names in it point into the main .SND, so moved names are re-pointed there too.
# ---------------------------------------------------------------------------------------------
SND_T1=os.environ.get('ANP_SND_T1','dd')
SND_T1_B0=os.environ.get('ANP_SND_T1_B0','keep')
SND_REVERB=os.environ.get('ANP_SND_REVERB','dd')
SND_LS=os.environ.get('ANP_SND_LS','dd')

def _is_dm_t1(w):
    """w = 12+ words of a type-1 record in Dead Men layout"""
    return (w[0]==1 and w[1]==CDCD and (w[3]>>16)==0xcdcd and (w[11]&0xffffff00)==0xcdcdcd00
            and (w[11]&0xff)<=0x40)

def _t1_mid(w):
    """Dead Men w7..w10 -> Dog Days +0x1c..+0x2f (5 words)"""
    w10=w[10]
    if SND_T1_B0=='zero': w10&=0xffffff00
    return [0,w[7],w[8],w[9],w10]          # f7 = 0.0f

def _dir(snd, nl=10):
    h0=struct.unpack_from('<I',snd,0)[0]
    w=struct.unpack_from('<%dI'%((len(snd)-h0)//4),snd,h0)
    c0=1+nl+4
    return h0,w[c0:c0+25],w[c0+25:c0+50]

def snd_fix_records(snd, nl=10):
    """Type-1 and type-7 records of a converted (Dog Days directory) SND -> Dog Days layout.
    Returns (bytes, stats, name_map {old string offset: new})."""
    st={'snd type-1 records converted':0,'snd type-1 tail written':0,'snd type-1 tail not movable':0,
        'snd type-1 tail already right':0,'snd names moved':0,'snd type-7 reverb converted':0}
    if SND_T1=='off' and SND_REVERB!='dd': return snd,st,{}
    out=bytearray(snd)
    h0,counts,offs=_dir(out,nl)
    listed={}
    for t in range(25):
        for i in range(counts[t]):
            r=struct.unpack_from('<I',out,offs[t]+4*i)[0]
            if r<h0: listed.setdefault(r,t)
    W=list(struct.unpack_from('<%dI'%(h0//4),out,0))
    # reverb presets
    if SND_REVERB=='dd':
        for r,t in listed.items():
            if t!=7 or r+0x70>h0: continue
            w=W[r//4:r//4+28]
            if w[0]!=7 or w[1]!=CDCD or w[5]!=2: continue
            f=lambda i: struct.unpack('<f',struct.pack('<I',w[i]))[0]
            si=lambda i: struct.unpack('<i',struct.pack('<I',w[i]))[0]
            if not all(-10000<=si(i)<=2000 for i in (9,10,15,17)): continue        # already floats (Dog Days)
            size=f(7); dens=100.0*min(1.0,max(0.0,size)**3/16.0)
            vals=[dens, 100.0*min(1.0,max(0.0,f(8))), float(si(9)), float(si(10)), f(12), f(13),
                  float(si(15)), f(16), float(si(17)), f(18), f(24) if 1000<=f(24)<=20000 else 5000.0, 0.0, 0.0]
            struct.pack_into('<13f',out,r+0x1c,*vals)
            for k,v in enumerate(vals): W[r//4+7+k]=struct.unpack('<I',struct.pack('<f',v))[0]
            st['snd type-7 reverb converted']+=1
    if SND_T1=='off': return bytes(out),st,{}
    t1=[r for r,t in listed.items() if t==1 and r+0x30<=h0 and _is_dm_t1(W[r//4:r//4+12])]
    # reference classes: record name fields (+8; type-4 lists also name their wave at item+4) and type-4 WHD offsets
    namepos=set(); whdpos=set()
    for r,t in listed.items():
        if r+12>h0: continue
        if W[r//4]==t and t: namepos.add(r+8)
        if t==4:
            if W[r//4]==4: whdpos.add(r+0x14); continue
            par=W[r//4+2]; k=r+4
            while k+28<=h0 and W[k//4]==0 and W[k//4+1]==par:
                namepos.add(k+4); whdpos.add(k+16); k+=28
    want={r+0x30 for r in t1}
    refs={}
    for i,v in enumerate(W):
        if v in want: refs.setdefault(v,[]).append(4*i)
    body=bytearray(out[:h0]); tail=bytes(out[h0:])
    name_map={}; stuck=[]
    for r in sorted(t1):
        w=W[r//4:r//4+12]
        loop=w[11]&0xff
        struct.pack_into('<5I',body,r+0x1c,*_t1_mid(w))
        st['snd type-1 records converted']+=1
        if SND_T1!='dd': continue
        x=r+0x30
        ddtail=bytes([loop,0,0,0xcd])+bytes(12)
        if body[x:x+3]==ddtail[:3] and x not in refs:
            st['snd type-1 tail already right']+=1; continue
        e=body.find(b'\0',x,min(h0,x+512))
        isstr=e>x and all(32<=c<127 for c in body[x:e])
        rf=refs.get(x,[])
        ok=isstr and rf and all(p in namepos or p in whdpos for p in rf) and any(p in namepos for p in rf)
        if not ok:
            st['snd type-1 tail not movable']+=1; stuck.append(r); continue
        end=e+1
        while end%16 and end<h0 and body[end]==0: end+=1
        room=end-x
        if room<3: st['snd type-1 tail not movable']+=1; continue
        s=bytes(body[x:e+1])
        while len(body)%16: body.append(0)
        new=len(body); body+=s
        for p in rf:
            if p in namepos: struct.pack_into('<I',body,p,new)
        name_map[x]=new; st['snd names moved']+=1
        n=min(16,room); body[x:x+n]=ddtail[:n]
        st['snd type-1 tail written']+=1
    if stuck:
        # The item after these records is a child pointer array, a type-3 record, ...: append a full 0x40 Dog Days
        # copy of the record instead and re-point directory list 1 and the type-2/3 child arrays at it (sound ids are
        # plain .SND offsets, kl2 0x54dca0).  References elsewhere keep the in-place record (right volume, wrong tail).
        sref={}
        for i in range(counts[1]): sref.setdefault(W[(offs[1]+4*i)//4],[]).append(offs[1]+4*i)
        for r,t in listed.items():
            # types 2 (random), 3 (sequence), 5 (sound list): [t, cdcd, name, cdcd0000, x, list, n|n<<16, ...]
            if t in (2,3,5) and r+0x1c<=h0 and W[r//4]==t:
                p=W[r//4+5]; n=W[r//4+6]&0xffff
                if p and p%4==0 and p+4*n<=h0:
                    for k in range(n): sref.setdefault(W[p//4+k],[]).append(p+4*k)
        allref={}
        S=set(stuck)
        for i,v in enumerate(W):
            if v in S: allref[v]=allref.get(v,0)+1
        for r in stuck:
            w=list(struct.unpack_from('<12I',body,r))          # +0x1c.. already rewritten in place
            while len(body)%16: body.append(0)
            new=len(body)
            body+=struct.pack('<16I',*(w[0:7]+list(struct.unpack_from('<5I',body,r+0x1c))+[0xcd000000|(W[r//4+11]&0xff),0,0,0]))
            ps=sref.get(r,[])
            for p in ps: struct.pack_into('<I',body,p,new)
            st['snd type-1 records relocated (0x40 copy)']=st.get('snd type-1 records relocated (0x40 copy)',0)+1
            st['snd type-1 relocated refs re-pointed']=st.get('snd type-1 relocated refs re-pointed',0)+len(ps)
            st['snd type-1 relocated refs left (other/coincidence)']=st.get('snd type-1 relocated refs left (other/coincidence)',0)+allref.get(r,0)-len(ps)
    while len(body)%16: body.append(0)
    newh0=len(body); res=body+tail
    struct.pack_into('<II',res,0,newh0,len(res))
    return bytes(res),st,name_map

def convert_ls_snd_dd(d, main_snd_converted, name_map=None):
    """*_LS.SND: header [main dir offset, size, 3, 4] + Dead Men type-1 records (0x30) -> Dog Days records (0x40)."""
    h0,size,a,b=struct.unpack_from('<4I',d,0)
    assert size==len(d) and (a,b)==(3,4)
    newh0=struct.unpack_from('<I',main_snd_converted,0)[0]
    n=(len(d)-16)//0x30
    if SND_LS!='dd' or n==0 or (len(d)-16)%0x30: return convert_ls_snd(d, main_snd_converted)
    recs=[struct.unpack_from('<12I',d,16+0x30*i) for i in range(n)]
    if not all(_is_dm_t1(w) for w in recs): return convert_ls_snd(d, main_snd_converted)
    out=bytearray(struct.pack('<4I',newh0,0,3,4)); moved=0
    for w in recs:
        w=list(w)
        if name_map and w[2] in name_map: w[2]=name_map[w[2]]; moved+=1
        mid=_t1_mid(w); mid[0]=0x3f800000        # f7 = 1.0f like Dog Days' own LS record
        out+=struct.pack('<16I',*(w[0:7]+mid+[0xcd000000|(w[11]&0xff),0,0,0]))
    struct.pack_into('<I',out,4,len(out))
    return bytes(out),'ls %d type-1 records -> DD layout (names re-pointed %d), dir %d->%d'%(n,moved,h0,newh0)

# ---------------------------------------------------------------------------------------------
# Dialogue languages (ANP_SND_LANGS, 11 Oct).
#   Localized wave (type-4 table entry whose first dword is 0 and +0xc is 0xb): u32 0, then one 7-word item per language
#   [0, name*, flags (0xb on the first, 3 on the rest), 0, .WHD record offset, f32 seconds, 0], languages in stream-name
#   order without PC_Def.  Dead Men has 5 items (Eng Ger Fre Spa Ita; all 2,385-2,657 per level, no empty item, the
#   Ger..Ita items always point at records flagged 0x400000 = 'in the language stream file' PC_Ger/Fre/Spa/Ita.str),
#   Dog Days reads 9 (Eng Ger Fre Spa Ita Dut Rus Pol Jap = language id 0..8, [0xdda79c]).
#   kl2 0x8207a4 stores the language at sound+0x6908 and 0x4d3de0 opens stream name [language+1] as the language file
#   (falling back to language 0 only when that file does not exist).  So unconverted, Dutch/Russian/Polish/Japanese read
#   items 5..8 out of the type-1 sound object that follows each wave (garbage .WHD offsets), and German..Italian found the
#   right items but their IMA-ADPCM records (~30 % of the lines) were never pointed at the loader's virtual PCM.
#   Fix: every localized wave is appended in Dog Days layout (items 0-4 = Dead Men's, 5-8 = a copy of the English item)
#   and the type-4 table and every type-1 sound's wave pointer (+0x14) are re-pointed at it; the old object stays in place
#   unused.  whdconv/whd_postfix point each language file's ADPCM records at that file's virtual PCM (lang_stream_maps).
#   ANP_SND_LANGS=0: the old output, byte for byte.
# ---------------------------------------------------------------------------------------------
SND_LANGS=os.environ.get('ANP_SND_LANGS','1')=='1'
DD_ITEM_FROM_DM=[0,1,2,3,4,0,0,0,0]       # Dog Days item (language id) <- Dead Men item; DM lacks Dut Rus Pol Jap -> English
LOC_ITEM=0x1c

def _loc_items(W, r, h0, maxn=16):
    """items of the localized wave at r (W = dwords of the record area)"""
    par=W[r//4+2]; k=r+4; items=[]
    while k+LOC_ITEM<=h0 and len(items)<maxn:
        it=W[k//4:k//4+7]
        if it[0]!=0 or it[1]!=par: break
        items.append(list(it)); k+=LOC_ITEM
    return items

def _loc_waves(snd, nl):
    """{offset: items} of the localized waves listed in the type-4 table"""
    h0,counts,offs=_dir(snd,nl)
    W=struct.unpack_from('<%dI'%(h0//4),snd,0)
    res={}
    for i in range(counts[4]):
        r=struct.unpack_from('<I',snd,offs[4]+4*i)[0]
        if r+0x20>h0 or r in res: continue
        if W[r//4]==0 and W[r//4+3]==0xb: res[r]=_loc_items(W,r,h0)
    return res

def whd_lang_records(dm_snd):
    """Dead Men .SND (6 stream names) -> {.WHD record offset: stream file name} for the records its localized waves use
    in languages 1..4 (German, French, Spanish, Italian; these live in PC_<Lang>.str)."""
    h0=struct.unpack_from('<I',dm_snd,0)[0]
    w=struct.unpack_from('<%dI'%((len(dm_snd)-h0)//4),dm_snd,h0)
    nl=w.index(CDCD)-1
    names=[dm_snd[o:dm_snd.index(b'\0',o)].decode('latin1') for o in w[1:1+nl]]
    out={}
    for r,items in _loc_waves(dm_snd,nl).items():
        for li,it in enumerate(items[1:nl-1],1):
            if it[4]: out.setdefault(it[4],names[li+1])
    return out

def snd_expand_langs(snd, nl=10):
    """Localized waves of a converted (Dog Days directory) SND: Dead Men's 5 language items -> Dog Days' 9
    (DD_ITEM_FROM_DM).  Returns (bytes, stats)."""
    st={'snd localized waves -> 9 languages':0,'snd localized waves already 9':0,'snd localized waves odd item count':0,
        'snd type-4 table entries re-pointed':0,'snd type-1 wave pointers re-pointed':0}
    if not SND_LANGS: return snd,st
    h0,counts,offs=_dir(snd,nl)
    loc=_loc_waves(snd,nl)
    body=bytearray(snd[:h0]); tail=bytes(snd[h0:])
    newoff={}
    for r in sorted(loc):
        items=loc[r]
        if len(items)==len(DD_ITEM_FROM_DM): st['snd localized waves already 9']+=1; continue
        if len(items)!=5: st['snd localized waves odd item count']+=1; continue
        rest=items[1][2]                                     # flags word of the further items (3)
        out=[]
        for k,src in enumerate(DD_ITEM_FROM_DM):
            it=list(items[src])
            if k: it[2]=rest if src==0 else items[src][2]
            out+=it
        while len(body)%16: body.append(0)
        new=len(body)
        body+=struct.pack('<I',0)+struct.pack('<%dI'%len(out),*out)
        newoff[r]=new; st['snd localized waves -> 9 languages']+=1
    if not newoff: return snd,st
    # references: the type-4 table, and the wave pointer (+0x14) of every type-1 sound (listed, or left in place by
    # snd_fix_records); any other dword equal to such an offset is a number (checked on Dead Men M01-M14: .WHD offsets in
    # wave items, a type-1 flags word)
    for i in range(counts[4]):
        p=offs[4]+4*i
        if p+4<=h0:
            v=struct.unpack_from('<I',body,p)[0]
            if v in newoff: struct.pack_into('<I',body,p,newoff[v]); st['snd type-4 table entries re-pointed']+=1
    W=struct.unpack_from('<%dI'%(len(body)//4),body,0)
    for i in range(4,len(W)-6):
        if W[i]==1 and W[i+1]==CDCD and (W[i+3]>>16)==0xcdcd and W[i+5] in newoff:
            struct.pack_into('<I',body,4*i+0x14,newoff[W[i+5]]); st['snd type-1 wave pointers re-pointed']+=1
    while len(body)%16: body.append(0)
    newh0=len(body); res=body+tail
    struct.pack_into('<II',res,0,newh0,len(res))
    return bytes(res),st

def snd_remap_whd(snd, plan, nl=10):
    """Point SND type-4 items (record = u32 0 + items of 7 u32 [0, parent, flags, 0, whdOff, gain, 0];
    one item per language) at the relaid layered records.  snd must have the Dog Days directory."""
    if not plan or not plan['map']: return snd,{'snd type-4 refs remapped':0}
    out=bytearray(snd); M=plan['map']
    h0=struct.unpack_from('<I',out,0)[0]
    w=struct.unpack_from('<%dI'%((len(out)-h0)//4),out,h0)
    c0=1+nl+4
    starts=set()
    for t in range(25):
        for i in range(w[c0+t]):
            r=struct.unpack_from('<I',out,w[c0+25+t]+4*i)[0]
            if r<h0: starts.add(r)
    starts=sorted(starts)
    import bisect
    n=0; items=0
    for i in range(w[c0+4]):
        r=struct.unpack_from('<I',out,w[c0+25+4]+4*i)[0]
        if r+32>h0: continue
        if struct.unpack_from('<I',out,r)[0]==4:
            # single-wave record [4, x, name, 0, 0, whdOff, gain, 0] (round 2: these were skipped before)
            items+=1; wo=struct.unpack_from('<I',out,r+0x14)[0]
            if wo in M: struct.pack_into('<I',out,r+0x14,M[wo]); n+=1
            continue
        j=bisect.bisect_right(starts,r); end=starts[j] if j<len(starts) else h0
        parent=struct.unpack_from('<I',out,r+8)[0]
        k=r+4
        while k+28<=end:
            it=struct.unpack_from('<7I',out,k)
            if it[0]!=0 or it[1]!=parent: break
            items+=1
            if it[4] in M: struct.pack_into('<I',out,k+16,M[it[4]]); n+=1
            k+=28
    return bytes(out),{'snd type-4 refs remapped':n,'snd type-4 items seen':items}
