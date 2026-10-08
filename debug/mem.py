import struct,sys
d=open(sys.argv[1],'rb').read()
ns,dirrva=struct.unpack_from('<II',d,8); streams={}
for i in range(ns):
    t,sz,rva=struct.unpack_from('<III',d,dirrva+12*i); streams[t]=(sz,rva)
mem=[]
if 5 in streams:
    sz,rva=streams[5]; n=struct.unpack_from('<I',d,rva)[0]
    for i in range(n):
        s,dsz,r=struct.unpack_from('<QII',d,rva+4+16*i); mem.append((s,dsz,r))
print('memory ranges',len(mem),'total',sum(m[1] for m in mem))
def read(a,n):
    for s,sz,r in mem:
        if s<=a and a+n<=s+sz: return d[r+a-s:r+a-s+n]
for a in [int(x,16) for x in sys.argv[2:]]:
    b=read(a,0x80); print(hex(a), b.hex(' ') if b else 'not in dump')
