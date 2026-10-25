import pefile,capstone,sys
p=pefile.PE(r"C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days/kl2.exe")
b=p.get_memory_mapped_image();base=p.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for a,n in [(0x87bda0,0x60),(0x5a06a0,0x40)]:
    print(hex(a))
    for i in md.disasm(b[a-base:a-base+n],a): print(hex(i.address),i.mnemonic,i.op_str)
