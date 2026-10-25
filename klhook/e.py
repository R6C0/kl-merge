import pefile,capstone
p=pefile.PE(r"C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days/kl2.exe")
b=p.get_memory_mapped_image();base=p.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
import sys
a=int(sys.argv[1],16);n=int(sys.argv[2],16)
for i in md.disasm(b[a-base:a-base+n],a):
    print(hex(i.address),i.mnemonic,i.op_str)
