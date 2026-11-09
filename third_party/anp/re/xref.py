import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EXES = {'dd': os.environ.get('ANP_DD_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'),
        'dm': os.environ.get('ANP_DM_EXE', r'C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men\kaneandlynch.exe')}
import sys, struct; 
import rtp
g=sys.argv[1]; s=sys.argv[2].encode()
exe=EXES[g]
img=rtp.Img(exe); d=img.d
def va_of(off):
    for a,n,r,nm in img.secs:
        if r<=off<r+n: return a+off-r
i=-1
while True:
    i=d.find(s+b'\0',i+1)
    if i<0: break
    if d[i-1]!=0: continue
    va=va_of(i); print('string at',hex(va))
    pat=struct.pack('<I',va); j=-1; n=0
    while True:
        j=d.find(pat,j+1)
        if j<0 or n>20: break
        print('   ref at',hex(va_of(j)), d[j-1:j].hex()); n+=1
