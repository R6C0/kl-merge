import struct,sys,collections
p=sys.argv[1]
f=open(p,'rb'); d=f.read()
t1,t2,raw,u=struct.unpack_from('<4I',d)
print(p,'t1',hex(t1),'t2',hex(t2),'raw',hex(raw),'u',hex(u),'size',hex(len(d)))
offs=struct.unpack_from('<2048I',d,t1)
nz=[o for o in offs if o]
print('n textures',len(nz),'first idx nonzero', [i for i,o in enumerate(offs) if o][:5])
types=collections.Counter()
for k,o in enumerate(nz[:6]+nz[-3:]):
    print(' entry @',hex(o), d[o:o+64].hex(' ',4))
for o in nz:
    fs,ty,ty2,idx,h,w,mips=struct.unpack_from('<I4s4siHHi',d,o)
    types[(ty,ty2)]+=1
print(types)
