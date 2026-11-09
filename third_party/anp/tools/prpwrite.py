import struct
def write_prp(tokens, flags, is_raw, nobjects, ops, hdr13=b'\0\0\0\0'):
    tok=list(tokens); idx={t:i for i,t in enumerate(tok)}
    def ti(s):
        if s not in idx: idx[s]=len(tok); tok.append(s)
        return idx[s]
    body=bytearray()
    for p,op,v in ops:
        b=op&0x7f; body.append(op)
        if b in (1,4): body+=struct.pack('<I',v)
        elif b in (2,3,0x7c,0x7d,0x7e,0x7f): pass
        elif b in (5,6,7): body.append(v&0xff)
        elif b==8: body+=struct.pack('<h',v)
        elif b in (9,16): body+=struct.pack('<i',v)
        elif b==10: body+=struct.pack('<f',v)
        elif b==11: body+=struct.pack('<d',v)
        elif b in (12,14):
            if b==14 and not (flags&4): body+=struct.pack('<I',v)
            elif flags&8: body+=struct.pack('<I',ti(v))
            else:
                e=v.encode('latin1'); body+=struct.pack('<I',len(e))+e
        elif b==13: body+=struct.pack('<I',len(v))+bytes(v)
        elif b==15:
            body+=struct.pack('<I',len(v))
            for s in v: body+=struct.pack('<I',ti(s))
        else: raise Exception('op %x'%op)
    tt=b''.join(t.encode('latin1')+b'\0' for t in tok)
    hdr=b'IOPacked v0.1\0'+bytes([is_raw])+struct.pack('<I',flags)+hdr13+struct.pack('<II',len(tok)-1,len(tt))
    assert len(hdr)==0x1f
    return hdr+tt+struct.pack('<I',nobjects)+bytes(body)
