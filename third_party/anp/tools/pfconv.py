"""Dead Men -> Dog Days pathfinder (PF4::ZData, GMS header slot 13) conversion.

Blob = u32 size, 13 counts (+1 pad), then 13 arrays back to back.  Dead Men stores
counts and indices as int16; Dog Days widened them to int32 (floats unchanged).
Record layouts (DM -> DD), worked out from PF4::ZData::Load in both executables
(kl1 0x4ee810, kl2 0x63e750) and the level data:
 A0  tree nodes      [h a,h b,3f]                     -> [i,i,3f]               16->20
 A1  tree nodes      [h a,h b,3f]                     -> [i,i,3f]               16->20
 A2  points          [3f]                             -> same                   12
 A3  polygons        [B n,B fl,H 0,i rt, 8h]          -> [B,B,H,i, 6i]          24->32
 A4  ?               [12h, 6f]                        -> [12i, 6f]              48->72
 A5  ?               [3f, h,h, h poly, H rt]          -> [3f, i,i, i, H rt, H]  20->28
 A6  cover/edges     [5f]                             -> same                   20
 A7  ?               [H,H,H,B,B,h]                    -> [H,H, i,i, B,B,h]      10->16
 A8  int list        h                                -> i                      2->4
 A9  poly edges      [h nb,h v,i link]                -> [i,i,i]                8->12
 A10 int list        h                                -> i                      2->4
 A11 int list        h                                -> i                      2->4
 A12 ?               4 bytes                          -> 8 bytes (unsupported, count must be 0)
"""
import struct
DM_SZ=[16,16,12,24,48,20,20,10,2,8,2,2,4]
DD_SZ=[20,20,12,32,72,28,20,16,4,12,4,4,8]
def convert_pf_dm_to_dd(blob):
    """blob: bytes starting at the u32 size word. Returns DD blob (with size word)."""
    size=struct.unpack_from('<I',blob)[0]
    cnt=list(struct.unpack_from('<14h',blob,4))
    p=4+28; arrs=[]
    for c,s in zip(cnt[:13],DM_SZ):
        assert c>=0
        arrs.append(blob[p:p+c*s]); p+=c*s
    assert p==4+size,(p,size)
    assert cnt[12]==0,'A12 records not supported yet'
    out=[]
    def conv(i, f_in, f_out, fn):
        a=arrs[i]; s=struct.calcsize(f_in); assert s==DM_SZ[i] and struct.calcsize(f_out)==DD_SZ[i]
        r=bytearray()
        for k in range(cnt[i]):
            r+=struct.pack(f_out,*fn(struct.unpack_from(f_in,a,k*s)))
        out.append(bytes(r))
    ident=lambda t:t
    conv(0,'<2h3f','<2i3f',ident)
    conv(1,'<2h3f','<2i3f',ident)
    out.append(arrs[2])
    conv(3,'<BBHi8h','<BBHi6i',lambda t:t[:4]+t[4:10])
    conv(4,'<12h6f','<12i6f',ident)
    conv(5,'<3f3hH','<3f3iHH',lambda t:t[:6]+(0,0))
    out.append(arrs[6])
    conv(7,'<3HBBh','<2H2iBBh',lambda t:(t[0],0,t[1],t[2],t[3],0,t[5]))
    conv(8,'<h','<i',ident)
    conv(9,'<2hi','<3i',ident)
    conv(10,'<h','<i',ident)
    conv(11,'<h','<i',ident)
    out.append(b'')
    body=struct.pack('<14i',*(cnt[:13]+[0]))+b''.join(out)
    return struct.pack('<I',len(body))+body

def check_dd_blob(b):
    size=struct.unpack_from('<I',b)[0]; cnt=struct.unpack_from('<14i',b,4)
    tot=56+sum(c*s for c,s in zip(cnt[:13],DD_SZ))
    return size==tot, size, tot
if __name__=='__main__':
    import sys
    sys.path.insert(0,__file__.rsplit('/',1)[0])
    from gms import load_gms
    g=load_gms(sys.argv[1]); h=struct.unpack_from('<20I',g)
    o=h[13]; sz=struct.unpack_from('<I',g,o)[0]
    nb=convert_pf_dm_to_dd(g[o:o+4+sz])
    print('dm',sz,'-> dd',len(nb)-4, check_dd_blob(nb))
