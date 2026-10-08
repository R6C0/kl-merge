"""dasm.py <hex address> [hex length]   disassemble kl2.exe with the strings and imports its constants point at.
dasm.py f:<hex address>   starts at the beginning of the function holding the address and marks it."""
import sys
import kl
E=kl.Exe(); a=sys.argv[1]; mark=None
if a.startswith('f:'): mark=int(a[2:],16); a=E.func(mark); n=max(mark-a+0x40,0x100)
else: a=int(a,16); n=0x100
if len(sys.argv)>2: n=int(sys.argv[2],16)
for i in E.dis(a,n): print(hex(i.address),i.mnemonic,i.op_str,E.note(i.op_str),'  <==' if i.address==mark else '')
