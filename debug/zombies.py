r"""zombies.py [name=kl2.exe] [--count]   "kl2.exe" entries that linger with 0 threads, and who keeps them.
WHAT THEY ARE (found 2026-10-09, 21 of them): not ended game processes. Each is a child of a game process that CRASHED,
created in the very second Windows logged an 'Application Error' for KL2.exe, with 0 threads, 0 handles and 0 CPU time: the
process snapshot (a copy-on-write clone of the address space) that Windows Error Reporting takes of a faulting process.
Being a copy of the address space it keeps every DLL of the game mapped - which is why <Dog Days>\dinput8.dll cannot be
replaced while one made with that file exists (rename the locked file aside and copy the new one in; that works).
It cannot be opened or killed ('Access denied': it never had a thread) and goes when the last handle to it is closed.
Reproduced with a 16 KB test program: an unhandled fault left to Windows leaves one, the same fault ended by the hook
(klhook.c, [KLHook] EndOnFatal=1) leaves none.
WHO HOLDS THEM: this script cannot open them either, so it works indirectly: of all process handles in the system
(NtQuerySystemInformation 64) it sets aside those whose object some openable process identifies as a live or ended
process; what is left is grouped by the set of processes holding each object. The group whose size follows the number of
lingering entries is the holder. On the owner's machine two services hold such a group, warp-svc.exe (25) and
rsEngineSvc.exe (22, a security product's engine; access SYNCHRONIZE | QUERY_LIMITED = waiting for an end that a
thread-less process never signals). When the test program added one entry, rsEngineSvc's group grew by one and
warp-svc's did not: rsEngineSvc.exe it is (inferred from counts, not from the objects' identity). steam.exe holds ONE
process handle, to its own web helper: restarting Steam clears nothing. Restarting the holding service or a reboot does.
(MedalEncoder.exe separately keeps handles to ~65 ENDED game runs; those are not listed by Windows and lock no file.)
--count prints only the number: tools\kl_autotest.py can compare it before and after a run (one more = that run ended in a
Windows error report) and must not take an entry with 0 threads for a running game."""
import collections,ctypes,datetime,struct,sys
from ctypes import wintypes as w
k=ctypes.WinDLL('kernel32',use_last_error=True); nt=ctypes.WinDLL('ntdll')
class HE(ctypes.Structure): _fields_=[('obj',ctypes.c_void_p),('pid',ctypes.c_size_t),('h',ctypes.c_size_t),('acc',w.DWORD),('bt',w.USHORT),('ti',w.USHORT),('attr',w.DWORD),('res',w.DWORD)]
k.OpenProcess.restype=w.HANDLE; k.GetCurrentProcess.restype=w.HANDLE; k.CloseHandle.argtypes=[w.HANDLE]
k.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]
k.GetProcessId.argtypes=[w.HANDLE]; k.GetProcessId.restype=w.DWORD
def query(cls,size=1<<22):
    n=w.ULONG(size)
    while True:
        b=ctypes.create_string_buffer(n.value); r=nt.NtQuerySystemInformation(cls,b,n,ctypes.byref(n))&0xffffffff
        if r==0xc0000004: n=w.ULONG(n.value+(1<<20)); continue
        if r: raise OSError('NtQuerySystemInformation(%d) %#x'%(cls,r))
        return b
def procs():
    """{pid: (name, threads, parent pid, created, handles)} of every process Windows lists (no process is opened)."""
    b=query(5); raw=b.raw; o=0; out={}; P=ctypes.sizeof(ctypes.c_void_p)      # b stays alive: the name pointers point into it
    while True:
        nxt,nth=struct.unpack_from('<II',raw,o); ct=struct.unpack_from('<q',raw,o+0x20)[0]; nl=struct.unpack_from('<H',raw,o+0x38)[0]
        if P==8: nptr=struct.unpack_from('<Q',raw,o+0x40)[0]; pid,pp=struct.unpack_from('<QQ',raw,o+0x50); hc=struct.unpack_from('<I',raw,o+0x60)[0]
        else: nptr=struct.unpack_from('<I',raw,o+0x3c)[0]; pid,pp=struct.unpack_from('<II',raw,o+0x44); hc=struct.unpack_from('<I',raw,o+0x4c)[0]
        out[pid]=(ctypes.wstring_at(nptr,nl//2) if nptr else '',nth,pp,ct,hc)
        if not nxt: return out
        o+=nxt
def lingering(name='kl2.exe',P=None):
    """-> {pid: (parent pid, created)} of processes of that name with no thread left."""
    return {p:(v[2],v[3]) for p,v in (P or procs()).items() if v[0].lower()==name.lower() and v[1]==0}
def when(ft): return datetime.datetime.fromtimestamp(ft/1e7-11644473600).strftime('%m-%d %H:%M:%S') if ft else '?'      # FILETIME -> local time
def handles():
    b=query(64,1<<24); c=ctypes.c_size_t.from_buffer(b).value
    return (HE*c).from_buffer(b,2*ctypes.sizeof(ctypes.c_size_t)),b
def holders(P):
    """-> ({frozenset(holder pids): number of process objects nobody can identify}, {pid: access masks}); see the docstring."""
    me=k.GetCurrentProcessId(); mine={}
    for p in P:
        h=k.OpenProcess(0x1000,False,p)                 # PROCESS_QUERY_LIMITED_INFORMATION
        if h: mine[h]=p
    H,keep=handles(); known=set(); pt=None; src={}
    for e in H:
        if e.pid==me and e.h in mine: known.add(e.obj); pt=e.ti
    if pt is None or not any(known): return None,None   # no object addresses for this caller
    for e in H:                                         # ended processes somebody still holds: identify through the holder's handle
        if e.ti!=pt or e.pid==me or e.obj in known: continue
        if e.pid not in src: src[e.pid]=k.OpenProcess(0x40,False,e.pid)        # PROCESS_DUP_HANDLE
        d=w.HANDLE()
        if src[e.pid] and k.DuplicateHandle(src[e.pid],e.h,k.GetCurrentProcess(),ctypes.byref(d),0,False,2):
            if k.GetProcessId(d): known.add(e.obj)
            k.CloseHandle(d)
    hold=collections.defaultdict(set); acc=collections.defaultdict(set)
    for e in H:
        if e.ti==pt and e.pid!=me and e.obj not in known: hold[e.obj].add(e.pid); acc[e.pid].add(e.acc)
    for h in list(mine)+[x for x in src.values() if x]: k.CloseHandle(h)
    return collections.Counter(frozenset(v) for v in hold.values()),acc
def report(name='kl2.exe'):
    P=procs(); Z=lingering(name,P)
    print('%d %s with no thread left (of %d listed)'%(len(Z),name,sum(1 for v in P.values() if v[0].lower()==name.lower())))
    for p,(pp,ct) in sorted(Z.items(),key=lambda x:x[1][1]):
        print('  pid %-6d created %s  parent %d (%s)  handles %d'%(p,when(ct),pp,P[pp][0]+' - still running' if pp in P else 'gone',P[p][4]))
    if not Z: return
    print('each is created in the second of an \'Application Error\' event for the program (Event Viewer > Windows Logs > Application, id 1000)')
    G,acc=holders(P)
    if G is None: print('this process gets no object addresses from the system (needs Windows 10, medium integrity): holders not listed'); return
    print('process objects that no openable process identifies, by who holds them (the %d above are among these):'%len(Z))
    for s,c in G.most_common():
        if len(s)==1 and c>=max(len(Z)-1,1):
            q=next(iter(s)); print('  %3d held ONLY by pid %d %s (access %s)%s'%(c,q,P.get(q,('?',))[0],', '.join('%#x'%a for a in sorted(acc[q])),'   <== size fits' if c<=len(Z)+4 else ''))
    st=[p for p,v in P.items() if v[0].lower()=='steam.exe']
    for q in st: print('  steam.exe pid %d holds %d of them'%(q,sum(c for s,c in G.items() if q in s)))
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if not x.startswith('--')]; name=a[0] if a else 'kl2.exe'
    if '--count' in sys.argv: print(len(lingering(name)))
    else: report(name)
