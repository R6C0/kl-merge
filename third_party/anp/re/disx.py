import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EXES = {'dd': os.environ.get('ANP_DD_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'),
        'dm': os.environ.get('ANP_DM_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men\kaneandlynch.exe')}
import sys

import rtp, capstone
g=sys.argv[1]; f=int(sys.argv[2],0); n=int(sys.argv[3],0) if len(sys.argv)>3 else 0x400
exe=EXES[g]
img=rtp.Img(exe)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
o=img.off(f); k=0
for ins in md.disasm(img.d[o:o+n],f):
    print('%x: %s %s'%(ins.address,ins.mnemonic,ins.op_str))
    if ins.mnemonic=='ret' and len(sys.argv)<=4: break
