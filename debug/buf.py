import struct,sys
exec(open('mem.py').read().split("for a in")[0].replace("sys.argv[1]","sys.argv[1]"))
so=0x1b3b1c4
hdr=read(so,0x14); print([hex(x) for x in struct.unpack('<5I',hdr)])
pos=struct.unpack_from('<I',hdr,12)[0]
buf=read(so+0x14,0x4000) or read(so+0x14,0x2000)
open('/tmp/streambuf2.bin','wb').write(buf); print(hex(pos), buf[pos-48:pos+48].hex(' '))
