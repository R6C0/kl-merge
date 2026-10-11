import struct,re,sys
def define_blocks(d):
    pos=[]
    for m in re.finditer(rb'[A-Z][A-Z0-9_]{2,30}\x00',d):
        s=m.start()
        if d[s+len(m.group()):s+32].strip(b'\0'): continue
        v=d[s+32:s+64]
        if not re.match(rb'[0-9A-Za-z_.]+\x00*$',v): continue
        pos.append((s,m.group()[:-1].decode(),v.split(b'\0')[0].decode()))
    blocks=[]
    for p in pos:
        if blocks and p[0]==blocks[-1][-1][0]+64: blocks[-1].append(p)
        else: blocks.append([p])
    return blocks
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    B=define_blocks(d)
    print(len(B),'blocks')
    for b in B[:int(sys.argv[2]) if len(sys.argv)>2 else 400]:
        s=b[0][0]; pre=struct.unpack_from('<6I',d,s-24)
        print(hex(s),' '.join('%x'%x for x in pre),'|',' '.join('%s=%s'%(n,v) for _,n,v in b))
