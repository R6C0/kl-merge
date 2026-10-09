"""log.py [KLHook.log] [--all]   the last session of the hook's log: every assert, fault, watchdog and end-of-run line with
the known sites and node-loader callers spelled out. Lines it does not know are skipped, never an error (the log also holds
script, position and expansion lines). --all prints every session's one-line summary first.
Also shown: what the Steam write guard did ('steam:' - blocked and passed writes, the level's verdict, NOT GUARDED), the end
of a session ('session: ... SESSION END', the moment the game uploads) and every jump box that fired or failed ('join:');
a run of more than four 'steam:' lines is folded."""
import datetime,os,re,sys
import kl
HEAD=re.compile(r'(\d\d:\d\d:\d\d\.\d+) (.*)')
KINDS=[                                                 # (kind, pattern on the text behind the time stamp)
 ('ASSERT',re.compile(r'ASSERT at kl2\.exe\+\w+ \((\w+)\)')),
 ('CRASH', re.compile(r'CRASH (\w+) at kl2\.exe\+\w+ \((\w+)\)')),
 ('FAULT', re.compile(r'(?:FAULT \(first chance[^)]*\)|FATAL unhandled exception|FATAL stack overflow) (\w+) at (.+?)\+0x(\w+) \((\w+)\)')),
 ('FATAL', re.compile(r'FATAL (C runtime: .*)')),
 ('WATCHDOG',re.compile(r'WATCHDOG: (.*)')),
 ('END',   re.compile(r'END (\w+\(\d+\)) called from kl2 (\w+)')),
 ('EXIT',  re.compile(r'(process exit|INTEGRITY EXIT|exit: ExitProcess)(.*)')),
 ('REFUSED',re.compile(r'patch REFUSED (\w+) (.*)')),          # the hook's patch guard said no (klhook.c)
 ('RESULT',re.compile(r'RESULT (\w+) \((.*)\) exit code (-?\d+)')),
 ('STEAM', re.compile(r'steam: (NOT GUARDED|BLOCKED |passed on |level .|at exit|Patch01\.zip .* not a menu file)')),      # klsteam.c
 ('SESSION',re.compile(r'session: .*SESSION END')),
 ('JOIN',  re.compile(r'join: (player \d+ |box \d+ NOT usable)')),                                                    # kljoin.c
]
def events(path,every=False):
    """-> (session header, [event dict]) of the last '==== KLHook loaded' session; every=True -> [(header, events)] of all.
    An event: time, kind (ASSERT CRASH FAULT FATAL WATCHDOG END EXIT RESULT), text, at (address or None), module, code,
    reg, callers, acc, where, dumps (every dump file named in its lines), dump (the first, '' if none)."""
    ses=[('',[])]; e=None
    for line in open(path,errors='replace'):
        m=HEAD.match(line.rstrip('\r\n'))
        if not m: continue
        t,rest=m.groups()
        if rest.startswith('==== KLHook') and 'loaded' in rest: ses.append((line.strip(),[])); e=None; continue
        if rest.startswith('  ') and e is not None:      # indented = belongs to the event above it
            r=rest.strip()
            if r.startswith('eax='): e['reg']={k:int(v,16) for k,v in re.findall(r'\b(e\w\w)=([0-9a-fA-F]+)',r)}
            elif r.startswith('callers:'): e['callers']=[int(x,16) for x in re.findall(r'\b[0-9a-fA-F]{8}\b',r[8:])]
            elif re.match(r'(reading|writing) address',r): e['acc']=r
            elif r.startswith('where:'): e['where'].append(r[7:])
            elif r.startswith('dump written'):
                e['dumps']+=re.findall(r'[\w.-]+\.m?dmp',r); e['dump']=e['dumps'][0] if e['dumps'] else ''
            continue
        if rest.startswith('AT kl2.exe+'): continue      # klauto's heading for the 'where:' lines printed BEFORE the event
        e=None
        for kind,pat in KINDS:
            g=pat.match(rest)
            if not g: continue
            e=dict(time=t,kind=kind,text=rest,at=None,module='',code=None,reg={},callers=[],acc='',where=[],dumps=[],dump='')
            if kind=='ASSERT': e['at']=int(g.group(1),16); e['module']='kl2.exe'; e['code']=0x80000003
            elif kind=='CRASH': e['code']=int(g.group(1),16); e['at']=int(g.group(2),16); e['module']='kl2.exe'
            elif kind=='FAULT': e['code']=int(g.group(1),16); e['module']=g.group(2); e['at']=int(g.group(4),16)
            ses[-1][1].append(e); break
    return ses[1:] if every and len(ses)>1 else ses if every else ses[-1]
def started(path,head):
    """When the session began: the header's time of day on the last date that is not after the log's own time stamp."""
    m=HEAD.match(head)
    if not m: return None
    end=datetime.datetime.fromtimestamp(os.path.getmtime(path)); h,mi,s=m.group(1).split(':')
    t=end.replace(hour=int(h),minute=int(mi),second=int(float(s)),microsecond=0)
    return t if t<=end+datetime.timedelta(seconds=2) else t-datetime.timedelta(days=1)
def line(e):
    if e['kind'] in ('ASSERT','CRASH'): return '%s %s %#x %s'%(e['time'],e['kind'] if e['kind']=='ASSERT' else 'CRASH %08x'%e['code'],e['at'],e['acc'])
    if e['kind']=='FAULT':
        return '%s %s %08x at %s %#x %s'%(e['time'],'FATAL' if e['text'].startswith('FATAL') else 'fault, first chance (may have been handled)',e['code'],e['module'],e['at'],e['acc'])
    return '%s %s'%(e['time'],e['text'])
def report(path=None,every=False):
    path=path or os.path.join(kl.DD,'KLHook.log')
    if every:
        for h,ev in events(path,True):
            c={}
            for e in ev: c[e['kind']]=c.get(e['kind'],0)+1
            print(h[:60],' '.join('%s %d'%x for x in sorted(c.items())),'|',next((e['text'] for e in reversed(ev) if e['kind']=='RESULT'),''))
        print()
    head,ev=events(path); print(head)
    for i,e in enumerate(ev):
        if e['kind']=='STEAM':                          # fold a run: the first two, a count, the last
            j=i
            while j>0 and ev[j-1]['kind']=='STEAM': j-=1
            k=i
            while k+1<len(ev) and ev[k+1]['kind']=='STEAM': k+=1
            if k-j+1>4 and j+1<i<k:
                if i==j+2: print('%s ... %d more steam: lines'%(e['time'],k-j-2))
                continue
        print(line(e)+(' ['+', '.join(e['dumps'])+']' if e['dumps'] else ''))
        if e['at'] is not None and e['module']=='kl2.exe':
            t=kl.explain(e['at'],e['reg']) if e['reg'] else kl.SITES.get(e['at'],'')
            if t: print('      '+t)
        for w in e['where']: print('      where: '+w)
        if e['callers']: print('      callers: '+' < '.join('%#x%s'%(c,' ('+kl.CALLERS[c]+')' if c in kl.CALLERS else '') for c in e['callers']))
    return ev
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if x!='--all']; report(a[0] if a else None,'--all' in sys.argv)
