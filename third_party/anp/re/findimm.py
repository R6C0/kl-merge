import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EXES = {'dd': os.environ.get('ANP_DD_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'),
        'dm': os.environ.get('ANP_DM_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men\kaneandlynch.exe')}
import sys, struct; 
import rtp, capstone
g=sys.argv[1]; vals=[int(x,0) for x in sys.argv[2:]]
exe=EXES[g]
img=rtp.Img(exe); d=img.d
a,n,r=img.sec('.text')
for v in vals:
    pat=struct.pack('<I',v); j=r
    while True:
        j=d.find(pat,j+1,r+n)
        if j<0: break
        va=a+j-r
        print(hex(v),'at',hex(va), d[j-3:j].hex())
