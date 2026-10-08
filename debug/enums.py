"""enums.py [exe] [out.json]   enum value tables in an exe: runs of {value, name*, next*} with values counting up from 0 or 1.
Defaults: kl2.exe -> <temp>/kl_triage/dd_enums.json (tools/dd_enums.json is this output)."""
import json,os,struct,sys
import kl
def extract(path):
    import pefile
    pe=pefile.PE(path,fast_load=True); d=open(path,'rb').read(); B=pe.OPTIONAL_HEADER.ImageBase
    secs=[(B+s.VirtualAddress,B+s.VirtualAddress+s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
    def off(v):
        for a,b,r,n in secs:
            if a<=v<b and v-a<n: return r+v-a
    cache={}
    def cstr(v):
        if v in cache: return cache[v]
        o=off(v); s=None
        if o is not None:
            e=d.find(b'\0',o,o+120)
            t=d[o:e]
            if e>o and all(32<=c<127 for c in t): s=t.decode()
        cache[v]=s; return s
    tables=[]
    for a,b,r,n in secs:
        o=r; end=r+n-12
        i=o
        while i<end:
            run=[]; j=i
            while j<end:
                v,p,x=struct.unpack_from('<III',d,j)
                s=cstr(p) if v<0x10000 else None
                if s is None: break
                run.append((v,s)); j+=12
            if len(run)>=2 and run[0][0] in (0,1) and all(run[k+1][0]==run[k][0]+1 for k in range(len(run)-1)):
                tables.append(run); i=j
            else: i+=4
    return tables
if __name__=='__main__':
    exe=sys.argv[1] if len(sys.argv)>1 else os.path.join(kl.DD,kl.DD_EXE)
    out=sys.argv[2] if len(sys.argv)>2 else os.path.join(kl.TMP,'dd_enums.json')
    t=extract(exe); print(len(t),'tables ->',out)
    json.dump(t,open(out,'w'))
