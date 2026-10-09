"""Shared by the triage scripts: game folders (tools/kl_port_check), temp dir, minidump reader,
kl2.exe image (strings, RTTI, function starts) and the kl2.exe sites decoded so far."""
import bisect,glob,os,re,struct,sys,tempfile
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(os.path.dirname(HERE),'tools'))
from kl_port_check import find,DM_GUESSES,DD_GUESSES,DM_EXE,DD_EXE
DM=find(DM_GUESSES,DM_EXE); DD=find(DD_GUESSES,DD_EXE)
if not DD: sys.exit('Dog Days not found: add its folder to DD_GUESSES in tools/kl_port_check.py')
TMP=os.path.join(tempfile.gettempdir(),'kl_triage'); os.makedirs(TMP,exist_ok=True)

def path(a):
    """A dump argument: a file, or a name inside the Dog Days folder (KLHook_3.dmp)."""
    return a if os.path.isfile(a) else os.path.join(DD,a)
def dumps():
    """The hook's dumps in the game folder: the numbered ones in order, then the named ones (KLHook_stall.dmp,
    KLHook_stackoverflow.dmp, KLHook_crt.dmp) by age."""
    def key(p):
        m=re.search(r'_(\d+)\.dmp$',p)
        return (0,int(m.group(1))) if m else (1,os.path.getmtime(p))
    return sorted(glob.glob(os.path.join(glob.escape(DD),'KLHook_*.dmp')),key=key)
def game_dumps(since=None):
    """The game's own Steam minidumps (kl2_<build>_crash_<date>.mdmp), oldest first; since = a time stamp or datetime:
    only those written at or after it. They hold the fault record of ANY module (the ship hook's log has it for kl2.exe
    only) but no memory besides the stacks."""
    t=since.timestamp() if hasattr(since,'timestamp') else since
    return [p for p in sorted(glob.glob(os.path.join(glob.escape(DD),'kl2_*crash*.mdmp')),key=os.path.getmtime) if t is None or os.path.getmtime(p)>=t-2]

class Dump:
    """Minidump: exception record, x86 context of the faulting thread, modules, captured memory."""
    def __init__(s,p):
        s.path=p; s.d=d=open(p,'rb').read()
        if d[:4]!=b'MDMP': raise ValueError('not a minidump: '+p)
        ns,dirrva=struct.unpack_from('<II',d,8); st={}
        for i in range(ns):
            t,sz,rva=struct.unpack_from('<III',d,dirrva+12*i)
            if t: st[t]=rva
        mem=[]
        if 5 in st:                                     # MemoryListStream
            n=struct.unpack_from('<I',d,st[5])[0]
            mem+=[struct.unpack_from('<QII',d,st[5]+4+16*i) for i in range(n)]
        if 9 in st:                                     # Memory64ListStream (full-memory dumps)
            n,r=struct.unpack_from('<QQ',d,st[9])
            for i in range(n):
                a,sz=struct.unpack_from('<QQ',d,st[9]+16+16*i); mem.append((a,sz,r)); r+=sz
        s.mem=[]; end=0                                 # sorted, overlaps removed, so lookups can bisect
        for a,sz,r in sorted(mem):
            if a+sz>end:
                k=max(end-a,0); s.mem.append((a+k,sz-k,r+k)); end=a+sz
        s.starts=[m[0] for m in s.mem]; s.mods=[]
        if 4 in st:
            for i in range(struct.unpack_from('<I',d,st[4])[0]):
                o=st[4]+4+108*i; base,size=struct.unpack_from('<QI',d,o); nr=struct.unpack_from('<I',d,o+20)[0]
                L=struct.unpack_from('<I',d,nr)[0]; s.mods.append((base,base+size,d[nr+4:nr+4+L].decode('utf-16le').split('\\')[-1]))
        s.code=s.addr=s.tid=None; s.info=(); s.reg={}; s.threads=[]
        ctx=lambda crva: dict(zip('edi esi ebx edx ecx eax ebp eip cs efl esp ss'.split(),struct.unpack_from('<12I',d,crva+156)))
        if 3 in st:                                     # ThreadListStream: (thread id, registers) in the dump's order
            for i in range(struct.unpack_from('<I',d,st[3])[0]):
                o=st[3]+4+48*i; tid=struct.unpack_from('<I',d,o)[0]; csz,crva=struct.unpack_from('<II',d,o+40)
                if csz>=204: s.threads.append((tid,ctx(crva)))
        if 6 in st:
            s.tid,_,s.code,_,_,s.addr,n,_=struct.unpack_from('<IIIIQQII',d,st[6]); s.info=struct.unpack_from('<15Q',d,st[6]+40)[:n]
            crva=struct.unpack_from('<I',d,st[6]+164)[0]
            s.reg=ctx(crva)
        elif s.threads:                                 # no exception record (the hook's watchdog dumps: stall, stack overflow,
            s.tid,s.reg=s.threads[0]                    # C runtime): the first thread listed is the process's first = the main thread
    def read(s,a,n):
        """n bytes at address a, or None if any of them is missing from the dump."""
        out=b''
        while n>0:
            i=bisect.bisect_right(s.starts,a)-1
            if i<0 or a>=s.mem[i][0]+s.mem[i][1]: return None
            b,sz,r=s.mem[i]; k=min(n,b+sz-a); out+=s.d[r+a-b:r+a-b+k]; a+=k; n-=k
        return out
    def have(s,a):
        """How many bytes the dump holds from address a on."""
        i=bisect.bisect_right(s.starts,a)-1
        return max(s.mem[i][0]+s.mem[i][1]-a,0) if i>=0 else 0
    def u32(s,a):
        b=s.read(a,4); return struct.unpack('<I',b)[0] if b else None
    def which(s,a):
        for b,e,nm in s.mods:
            if b<=a<e: return '%s+0x%x'%(nm,a-b)

class Exe:
    """kl2.exe mapped at its image base."""
    def __init__(s,p=None):
        import pefile,capstone
        s.pe=pefile.PE(p or os.path.join(DD,DD_EXE),fast_load=True); s.B=s.pe.OPTIONAL_HEADER.ImageBase
        s.img=s.pe.get_memory_mapped_image(); s.md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
        s.sec={x.Name.rstrip(b'\0').decode():(s.B+x.VirtualAddress,s.B+x.VirtualAddress+x.Misc_VirtualSize) for x in s.pe.sections}
        s._f=s._imp=None
    def u32(s,v):
        o=v-s.B; return struct.unpack_from('<I',s.img,o)[0] if 0<=o<=len(s.img)-4 else None
    def code(s,v):
        a,b=s.sec['.text']; return a<=v<b
    def cstr(s,v):
        """Printable text at a data address (4+ chars, or 3 and a terminator: file extensions), else ''."""
        o=v-s.B; m=re.match(rb'[\x20-\x7e]{4,}|[\x21-\x7e]{3}(?=\0)',s.img[o:o+160]) if 0<o<len(s.img) and not s.code(v) else None
        return m.group().decode() if m else ''
    def imp(s,v):
        """'DLL.Function' if v is an import slot."""
        if s._imp is None:
            import pefile
            s.pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
            s._imp={i.address:'%s.%s'%(e.dll.decode()[:-4],i.name.decode() if i.name else i.ordinal) for e in s.pe.DIRECTORY_ENTRY_IMPORT for i in e.imports}
        return s._imp.get(v,'')
    def dis(s,a,n):
        return s.md.disasm(s.img[a-s.B:a-s.B+n],a)
    def note(s,op):
        """Strings and imports behind the constants of an operand string."""
        out=''
        for v in re.findall(r'0x[0-9a-f]{6,}',op):
            t=s.cstr(int(v,16)); out+=' "%s"'%t if t else ''
            t=s.imp(int(v,16)); out+=' <%s>'%t if t else ''
        return out
    def funcs(s):
        """Sorted function starts (heuristic): 16-aligned call targets, plus call targets and code pointers in .rdata
        (vtable slots) that follow padding, a ret or a jmp."""
        if s._f is None:
            a,b=s.sec['.text']; i=s.img; o=a-s.B; e=b-s.B; f=set()
            after=lambda v: i[v-s.B-1] in (0xcc,0xc3,0x90) or i[v-s.B-3]==0xc2 or i[v-s.B-5]==0xe9 or i[v-s.B-2]==0xeb
            while (o:=i.find(b'\xe8',o,e-5))>=0:
                v=s.B+o+5+struct.unpack_from('<i',i,o+1)[0]; o+=1
                if a<v<b and (v%16==0 or after(v)): f.add(v)
            ra,rb=s.sec['.rdata']
            f.update(v for v, in struct.iter_unpack('<I',i[ra-s.B:ra-s.B+(rb-ra)//4*4]) if a<v<b and after(v))
            s._f=sorted(f)
        return s._f
    def func(s,va):
        f=s.funcs(); i=bisect.bisect_right(f,va)-1; return f[i] if i>=0 else None
    def rtti(s,vt):
        """Class name of the vtable at vt (MSVC RTTI), or None."""
        col=s.u32(vt-4); td=s.u32(col+12) if col and s.u32(col)==0 else None
        o=(td or 0)+8-s.B; m=re.match(rb'\.\?A[VU]([\x21-\x7e]+?)@@\0',s.img[o:o+200]) if td and 0<o<len(s.img) else None
        return m.group(1).decode() if m else None
    def vtables(s,cls):
        """Primary vtables of a class, through its RTTI type descriptor and complete-object locators."""
        o=s.img.find(b'.?AV'+cls.encode()+b'@@\0'); out=[]
        if o<0: return out
        td=struct.pack('<I',s.B+o-8); a,b=s.sec['.rdata']; r=s.img[a-s.B:b-s.B]; i=-1
        while (i:=r.find(td,i+1))>=0:
            if i%4==0 and i>=12 and r[i-12:i-4]==b'\0'*8:          # locator: signature 0, offset 0, cdOffset, type descriptor
                col=struct.pack('<I',a+i-12); j=-1
                while (j:=r.find(col,j+1))>=0:
                    if j%4==0: out.append(a+j+4)
        return out

# .prp markers. kl2 0x45ed90 maps a property type index to the marker its reader expects:
# 0:0d 1:05 2:06 3,4:07 5,6:08 7,8:09 9:0a 10:0b 11:0c 12:0e 13:0f 14:02 15:03 16:04 (same table as Blood Money).
MARK={0x01:'array[',0x02:'object{',0x03:'type15',0x04:'count',0x05:'char',0x06:'bool',0x07:'u8',0x08:'u16',0x09:'u32',0x0a:'f32',
      0x0b:'f64',0x0c:'string',0x0d:'raw',0x0e:'enum',0x0f:'keylist',0x7c:']array',0x7d:'skip',0x7e:'}object',0x7f:'end'}
def mark(b): return '%02x %s'%(b,MARK.get(b,'not a marker'))

# Exception addresses understood so far (all read off the disassembly; see `dasm.py <address>`).
SITES={
 0x8c1625:'ZPackedInput::ExchangeFooter(14) read a byte that is not 7e: the record holds MORE fields than the class reads (or the reader desynced earlier)',
 0x64a856:'ZPackedInput::ExchangeHeader: marker read (ecx) is not the marker of the expected type (eax)',
 0x64a819:'ZPackedInput::ExchangeHeader, dictionary path: marker read (ecx) is not the expected one (eax)',
 0x5cf526:'SkipObject visitor was handed a value at depth 0 (ebx = its marker): the record to skip did not start with 02',
 0x5b4bd0:'ZPackedInput skip (0x5b4880) read a byte that is no marker (ebx)',
 0x4f9828:'SkipObject: the reader could not step over a token (follows 0x5b4bd0)',
 0x8f47c7:'controller-class lookup by name: the name pointer (edi) is null',
 0xa8e3cb:'NOT A CRASH: Steam DRM anti-debug probe, a deliberate write to 0 that its own SEH handler (0xb0fd20) resumes',
}
# Return addresses inside the recursive node loader 0x46fe20 (Blood Money: ZEngineDataBase::LoadPropertiesRecursive).
CALLERS={0x46fecc:'node record footer',0x46ff33:'controller count',0x46ffa6:'controller name',0x46ffd1:'create controller by name',
         0x47001a:'skip unknown controller',0x470079:'child node',0x8ade95:'scene root',0x7f8e33:'count header'}

def explain(at,reg,D=None):
    """One line on what a known site means, with the values in the registers."""
    t=SITES.get(at,'')
    if at in (0x64a856,0x64a819): t+=' -> expected %s, read %s'%(mark(reg['eax']&255),mark(reg['ecx']&255))
    if at in (0x5cf526,0x5b4bd0): t+=' -> marker %s'%mark(reg['ebx']&255)
    b=D.read(reg['esp']+4,1) if D and at==0x8c1625 else None
    if b: t+=' -> read %s'%mark(b[0])
    return t
