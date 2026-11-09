import struct,sys,collections
p=sys.argv[1]
d=open(p,'rb').read()
off,cnt,off2,z=struct.unpack_from('<4I',d)
print(p,'chunkOff',hex(off),'count',cnt,'off2',hex(off2),'zero',z,'size',len(d))
kinds=collections.Counter(); sizes=collections.defaultdict(list)
descs=[]
for i in range(cnt):
    o,s,k,u=struct.unpack_from('<4I',d,off+i*16)
    descs.append((o,s,k,u)); kinds[(k,u)]+=1; sizes[(k,u)].append(s)
for k,v in sorted(kinds.items()): print(' kind',k,'unk',hex(k[1]) if False else k[1],'n',v,'sizes',sorted(set(sizes[k]))[:8])
print('first descs', descs[:12])
