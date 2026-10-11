"""Dead Men -> Dog Days .WHD (wave header bank) conversion, in place.

WHD = [dirOff, size, 3, 4] + (name, 64-byte wave record)* + empty dir.  Records are referenced by
offset from SND type-4 records, so they are converted in place (same size, same offsets).
 record words: 0:0  1:nameOff  2:fmtTag|flags<<16  3:rate  4:bits  5:dataSize  6:?  7:channels  8:dataOff
   Dead Men  9:samples 10:blockAlign 11:samplesPerBlock 12:extra 13-15:pad
   Dog Days  9:dataOff hi (0) 10:samples 11:blockAlign 12:samplesPerBlock 13:extra 14-15:pad
"""
import struct, os
FMTS=(0x1,0x2,0x11,0x55,0x1000)
KEEP_LAYERS=os.environ.get('ANP_WHD_KEEP_LAYERS','0')=='1'   # 1 = old behaviour (copy Dead Men's layer byte)
def find_records(d):
    h0,hsz=struct.unpack_from('<II',d,0)
    if h0==0: h0=hsz                                # LS banks: no directory, header holds the size
    out=[]
    for o in range(16,h0-63+16,16):
        w=struct.unpack_from('<9I',d,o)
        if o==16 and w[0]==0 and w[1]==0 and (w[2]&0xffff) in FMTS and 4000<=w[3]<=96000 and w[7] in (1,2,4,6):
            out.append(o); continue                 # LS banks: single unnamed record
        if w[0]!=0 or not (16<=w[1]<o): continue
        if (w[2]&0xffff) not in FMTS or not (4000<=w[3]<=96000) or w[7] not in (1,2,4,6): continue
        e=d.find(b'\0',w[1],o)
        if e<0 or not d[w[1]:e].lower().endswith(b'.wav'): continue
        out.append(o)
    return out
def convert_whd_dm_to_dd(d, refs=None, stream_map=None, lang_maps=None):
    """stream_map: strvirt.mapping(PC_Def.str) -> streamed (non-localised) IMA-ADPCM records are pointed at
    the loader's virtual 16-bit PCM copy (Dog Days streams Ogg/PCM only).
    lang_maps: {record offset: strvirt.mapping(PC_<Lang>.str)} for records in a language stream file (flag 0x400000;
    sndconv.whd_lang_records says which file) -> the same, from that file (ANP_SND_LANGS)."""
    d=bytearray(d); recs=find_records(d); nv=0; nl=0; nlv=0
    if refs is not None:
        missing=[r for r in refs if r not in set(recs)]
    else: missing=[]
    n=0
    for o in recs:
        w=list(struct.unpack_from('<16I',d,o))
        fmt=w[2]&0xffff
        nw=w[0:9]+[0]+w[9:13]+w[13:15]
        if fmt==1 and nw[11]==0: nw[11]=w[7]*(w[4]//8)
        fl=w[2]>>16
        sm=stream_map if not (fl&0x40) else (lang_maps.get(o) if lang_maps else None)
        if sm is not None and fmt==0x11 and (fl&0x80) and w[8] in sm:
            e=sm[w[8]]
            if fl&0x40: nlv+=1
            nw[2]=(fl<<16)|1; nw[4]=16; nw[5]=e['pcm']; nw[6]=e['pcm']; nw[7]=e['ch']
            nw[8]=e['voff']&0xffffffff; nw[9]=e['voff']>>32; nw[10]=e['samples']*e['ch']
            nw[11]=2*e['ch']; nw[12]=0; nw[13]=4; nv+=1
        # Byte 3 of word 2 (record+0xb) is Dog Days' layered-stream grouping (kl2 0x4b20e8): bit7 = group head,
        # low 7 bits = layer count; otherwise the index back to the head. kl2 then walks that many records at a
        # 0x48 stride from the head. Dead Men sets 0x82/0x83/0x84 on its layered streams (two-layer dialogue,
        # layered music) but has no follow-on layer records, so kl2 read neighbouring bytes as layers: divide by
        # zero at 0x4b240e and an int3 at 0x522acb (M02), an 18.7 MB read and an int3 at 0x458819 (M08).
        # Clear it: each record plays as one plain stream.
        if (nw[2]>>24) and not KEEP_LAYERS: nw[2]&=0x00ffffff; nl+=1
        struct.pack_into('<16I',d,o,*nw); n+=1
    st={'whd records converted':n, 'whd refs not found':len(missing), 'whd adpcm streams -> virtual pcm':nv,
        'whd DM layer byte cleared':nl}
    if lang_maps is not None: st['whd language-file adpcm streams -> virtual pcm (incl. above)']=nlv
    return bytes(d), st
def snd_whd_refs(snd, nl=10):
    """WHD offsets referenced by type-4 records of a (DD-layout directory) SND."""
    h0=struct.unpack_from('<I',snd,0)[0]
    w=struct.unpack_from('<%dI'%((len(snd)-h0)//4),snd,h0)
    c0=1+nl+4; cnt=w[c0+4]; off=w[c0+25+4]
    refs=[]
    for i in range(cnt):
        r=struct.unpack_from('<I',snd,off+4*i)[0]
        if r+24<=len(snd) and struct.unpack_from('<I',snd,r)[0]==4: refs.append(struct.unpack_from('<I',snd,r+20)[0])
    return refs
