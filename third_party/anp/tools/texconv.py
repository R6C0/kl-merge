import struct
def convert_tex_dm_to_dd(d, outpath, extra=()):
    t1,t2,raw,u=struct.unpack_from('<4I',d)
    o1=struct.unpack_from('<2048I',d,t1); o2=struct.unpack_from('<2048I',d,t2)
    tab0=[0]*4096; tab1=[0]*4096
    out=open(outpath,'wb'); out.write(b'\0'*0xc020)
    pos=0xc020; stats={'tex':0,'cube':0,'anim':0}
    def entry(i, zero_idx=False):
        o=o1[i]; fs=struct.unpack_from('<I',d,o)[0]; assert fs<0x2000000
        e=bytearray(d[o:o+fs])
        if zero_idx: struct.pack_into('<i',e,12,0)
        return bytes(e)+b'\0'*((-fs)&15)
    def lst(i):
        if not o2[i]: return None
        lo=o2[i]; n=struct.unpack_from('<I',d,lo)[0]; return list(struct.unpack_from('<%dI'%n,d,lo+4))
    for s in range(2048):
        if not o1[s]: continue
        fl=struct.unpack_from('<I',d,o1[s]+24)[0]
        tab0[s]=pos
        if fl & 0x400:
            L=lst(s) or [s]*6
            blob=entry(s, zero_idx=True)
            flags=[1 if (k<len(L) and L[k]!=L[k-1]) else 0 for k in range(1,6)]
            blob+=struct.pack('<8I',s,*flags,0,0)
            for k in range(1,6):
                if flags[k-1]: blob+=entry(L[k], zero_idx=True)
            stats['cube']+=1
        else:
            blob=entry(s)
            if fl & 0x100:
                L=lst(s) or [s]
                blk=struct.pack('<I',len(L))+struct.pack('<%dI'%len(L),*L)
                blob+=blk+b'\0'*((-len(blk))&15); tab1[s]=len(L); stats['anim']+=1
        out.write(blob); pos+=len(blob); stats['tex']+=1
    for slot,blob in extra:                     # grafted Dog Days entries (already DD layout, index patched)
        assert not tab0[slot], slot
        tab0[slot]=pos; out.write(blob); pos+=len(blob); stats['tex']+=1; stats['grafted']=stats.get('grafted',0)+1
    out.seek(0)
    out.write(struct.pack('<8I',0x20,0x4020,0,0,0,0,0,0))
    out.write(struct.pack('<4096I',*tab0)); out.write(struct.pack('<4096I',*tab1)); out.write(b'\0'*0x4000)
    out.close(); stats['size']=pos
    return stats
