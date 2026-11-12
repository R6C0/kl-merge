import os
import struct, sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
from mat import MAT
def convert_mat_dm_to_dd(data):
    """in-place shrink of 16-byte material records to Dog Days' 12-byte layout"""
    import tempfile; tmp=os.path.join(tempfile.gettempdir(),'_mat_in.bin'); open(tmp,'wb').write(data)
    m=MAT(tmp,16)
    out=bytearray(data)
    for ao,n in m.arrays.items():
        recs=[struct.unpack_from('<4I',data,ao+i*16) for i in range(n)]
        # clear old region then write compact records
        out[ao:ao+16*n]=b'\0'*(16*n)
        for i,(tag,val,cnt,typ) in enumerate(recs):
            assert cnt<0x10000 and typ<0x10000,(hex(ao),i,cnt,typ)
            struct.pack_into('<IIHH',out,ao+i*12,tag,val,cnt,typ)
    # render bucket (instance header word 3 = layer<<4 | blend sub-mode). Dog Days renumbered the layers:
    #   DM 3x static translucent      -> DD 4x
    #   DM 40/41 dynamic opaque/decal -> DD 20/21   (characters, vehicles: DD draws nothing in 40)
    #   DM 4x (x>=2) dynamic alpha    -> DD 5x      (hair, eyes, glasses)
    #   DM 2e/2f sun backdrop          -> DD 13      (additive backdrop)
    global LAST_H3
    LAST_H3=collections.Counter()
    for o in set(x for x in m.t1 if x):
        h3=struct.unpack_from('<I',data,o+12)[0]
        n=map_h3(h3)
        if n!=h3:
            struct.pack_into('<I',out,o+12,n); LAST_H3['%02x->%02x'%(h3,n)]+=1
    # Dog Days material classes render a NormalAndLinearZ (+ToColor) layer that its post-processing reads
    # (linear depth for fog/DOF/SSAO). Dead Men's classes carry PostFilterZPass(+Alpha) in that role, which
    # Dog Days never draws -> depth-based post effects see an empty buffer. Repoint those two layers.
    def cstr(o):
        e=data.index(b'\0',o); return data[o:e].decode('latin1')
    newstr={}
    def addstr(s):
        if s not in newstr:
            while len(out)%4: out.append(0)
            newstr[s]=len(out); out.extend(s.encode('latin1')+b'\0')
        return newstr[s]
    # Dead Men draws sprites (menu/HUD pictures, fonts, prompts, particles) in layer 'Ambient' with techniques
    # AmbientSprites*; Dog Days' Sprite.fx only has TransparentSprites* and kl2 (0x50bbbf..) puts sprites in the
    # 'Transparent' pass. Left as is, no 2D sprite draws at all. Only touch layer arrays whose PATH is Sprite.fx
    # ('Ambient' is a real layer of the Standard classes).
    if os.environ.get('ANP_MAT_SPRITES','1')=='1':
        SPR={'Ambient':'Transparent','AmbientSprites':'TransparentSprites','AmbientSpritesSnow':'TransparentSpritesSnow',
             'AmbientSpritesRain':'TransparentSpritesRain','AmbientSpritesParticle':'TransparentSpritesParticle'}
        for ao,n in m.arrays.items():
            recs=[struct.unpack_from('<4I',data,ao+i*16) for i in range(n)]
            def s_of(val):
                try: return cstr(val)
                except Exception: return None
            if not any(typ==1 and tag==0x50415448 and s_of(val)=='Sprite.fx' for (tag,val,cnt,typ) in recs): continue   # 'PATH'
            for i,(tag,val,cnt,typ) in enumerate(recs):
                if typ==1 and tag in (0x4e414d45,0x4944454e):   # 'NAME','IDEN'
                    s=s_of(val)
                    if s in SPR:
                        struct.pack_into('<IIHH',out,ao+i*12,tag,addstr(SPR[s]),cnt,typ); LAST_H3['sprite layer %s->%s'%(s,SPR[s])]+=1
    if os.environ.get('ANP_MAT_LINZ','1')=='1':
        REN={'PostFilterZPass':'NormalAndLinearZ','PostFilterZPassAlpha':'NormalAndLinearZToColor','PostFilterZPassMPS':'NormalAndLinearZMPS','PostFilterZPassRigid':'NormalAndLinearZ'}
        for ao,n in m.arrays.items():
            for i in range(n):
                tag,val,cnt,typ=struct.unpack_from('<4I',data,ao+i*16)
                if typ==1 and tag in (0x4e414d45,0x4944454e):   # 'NAME','IDEN'
                    try: s=cstr(val)
                    except Exception: continue
                    if s in REN:
                        struct.pack_into('<IIHH',out,ao+i*12,tag,addstr(REN[s]),cnt,typ); LAST_H3['layer %s->%s'%(s,REN[s])]+=1
    # EXPERIMENT (env ANP_EXP_FOG=0): force FENA (fog enable) records to 0
    if os.environ.get('ANP_EXP_FOG')=='0':
        for ao,n in m.arrays.items():
            for i in range(n):
                tag,val,cnt,typ=struct.unpack_from('<4I',data,ao+i*16)
                if tag==0x46454e41 and typ==2 and val:   # 'FENA'
                    struct.pack_into('<IIHH',out,ao+i*12,tag,0,cnt,typ); LAST_H3['EXP fog off']+=1
    # EXPERIMENT (env ANP_EXP_BENA=1): force BENA (blend enable) records to 1
    if os.environ.get('ANP_EXP_BENA')=='1':
        for ao,n in m.arrays.items():
            for i in range(n):
                tag,val,cnt,typ=struct.unpack_from('<4I',data,ao+i*16)
                if tag==0x42454e41 and typ==2 and not val:   # 'BENA'
                    struct.pack_into('<IIHH',out,ao+i*12,tag,1,cnt,typ); LAST_H3['EXP bena on']+=1
    return bytes(out), len(m.arrays), len(m.recs)
def map_h3(v):
    layer,sub=v>>4,v&15
    if layer==3: return 0x40|sub
    if layer==4: return (0x20|sub) if sub in (0,1) else (0x50|sub)
    if layer==2: return 0x13
    return v
