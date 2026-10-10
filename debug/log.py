"""log.py [KLHook.log] [--all]   the last session of the hook's log: every assert, fault, watchdog and end-of-run line with
the known sites and node-loader callers spelled out. Lines it does not know are skipped, never an error (the log also holds
script, position and expansion lines). --all prints every session's one-line summary first.
Also shown: what the Steam write guard did ('steam:' - blocked and passed writes, the level's verdict, NOT GUARDED), the end
of a session ('session: ... SESSION END', the moment the game uploads) and every jump box that fired or failed ('join:');
a run of more than four 'steam:' lines is folded.
Last: how the session went and ended (course): its session states, the stretches the game window was not in front (the game
runs no frame then), and - for a run without any fault line - that the log simply stops, with what was overdue at that moment.
--all marks every session that has no end line."""
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
 ('EXIT',  re.compile(r'(process exit|INTEGRITY EXIT|exit: ExitProcess|exit: _?exit)(.*)')),
 ('REFUSED',re.compile(r'patch REFUSED (\w+) (.*)')),          # the hook's patch guard said no (klhook.c)
 ('RESULT',re.compile(r'RESULT (\w+) \((.*)\) exit code (-?\d+)')),
 ('STEAM', re.compile(r'steam: (NOT GUARDED|BLOCKED |passed on |level .|at exit|Patch01\.zip .* not a menu file)')),      # klsteam.c
 ('SESSION',re.compile(r'session: .*SESSION END')),
 ('JOIN',  re.compile(r'join: (player \d+ |box \d+ NOT usable|level .* jump list is EMPTY)')),                              # kljoin.c
 ('PAGE',  re.compile(r'expansion: (menu page \d+ (latched|dropped|forced)|slot \w+: menu page \d+ from now on|the menu.s window system)')),   # klslot.c: which map page a load belongs to
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
STATE=re.compile(r'session: state 0x(\w+) -> 0x(\w+)')
NUDGE=re.compile(r'nudge: ([\d.]+) s: (\d+) calls \((\d+) /s\), \d+ passed on, game window in front at the last one: (\w+)')
ENDS=re.compile(r'exit: |process exit|process ended here|RESULT |INTEGRITY EXIT|steam: at exit')
def secs(t): h,m,s=t.split(':'); return int(h)*3600+int(m)*60+float(s)
def raw(path):
    """[[(time, text), ...]]: the lines of every session, its '==== KLHook loaded' header first."""
    ses=[]
    for ln in open(path,errors='replace'):
        m=HEAD.match(ln.rstrip('\r\n'))
        if not m: continue
        if m.group(2).startswith('==== KLHook') and 'loaded' in m.group(2): ses.append([])
        if ses: ses[-1].append(m.groups())
    return ses
def course(lines):
    """How a session went and how it ended - for the runs that leave NO fault line: a hang, a kill, the machine going down
    (the owner's freeze of 2026-10-09 22:23, re/freeze_1009.md). -> dict:
    states [(time, from, to)]; ended = an exit / RESULT / 'process ended' line exists; last = (time, text) of the last line;
    away [(from, to, seconds)] = stretches the 'nudge:' lines report the game window as not in front: the main loop then runs
    no frame and polls no input (kl2 0x87a963, unless an online session runs), it only pumps messages some 15,000 times a second;
    quiet = seconds from the last nudge line to the last line when one was overdue (they come every 10 s while the message
    pump 0x82dfb0 is called); notes = what is unusual, in words."""
    st=[(t,int(m.group(1),16),int(m.group(2),16)) for t,r in lines for m in [STATE.search(r)] if m]
    nu=[(t,float(m.group(1)),int(m.group(3)),m.group(4)) for t,r in lines for m in [NUDGE.search(r)] if m]
    ended=any(ENDS.search(r) for t,r in lines); last=lines[-1]; away=[]; notes=[]; cur=None
    for t,dt,rate,front in nu:
        if front=='no': cur=[cur[0] if cur else (secs(t)-dt)%86400,secs(t)]
        elif cur: away.append(cur); cur=None
    if cur: away.append(cur)
    away=[(a,b,(b-a)%86400) for a,b in away]
    quiet=(secs(last[0])-secs(nu[-1][0]))%86400 if nu else 0
    if quiet<=10.5: quiet=0
    for t,a,b in st:
        if b==0x2e and a not in (0x28,0): notes.append('%s session closing (0x2e) entered from %#x, not from the session end 0x28: no upload, no stats - the quit on the page between two rounds, or an error close'%(t,a))
    if st and st[-1][2]==0x2e and st[-1][1]!=0: notes.append('the session never left 0x2e: 0x0 normally follows within 25 ms, BEFORE the level is unloaded')
    if away: notes.append('game window not in front for %.0f s in %d stretch(es) (%s): no frames, no input polls there'%(sum(x[2] for x in away),len(away),
        ', '.join('%s-%s'%tuple('%02d:%02d:%02d'%(v//3600,v%3600//60,v%60) for v in x[:2]) for x in away[:4])+(' ...' if len(away)>4 else '')))
    if quiet: notes.append('no nudge line in the last %.1f s of the log: the main thread did not reach its message pump (it waits for the render thread without a timeout at kl2 0x459b1a, or stands in a call)'%quiet)
    if not ended: notes.append('NO END LINE: the log stops at %s ("%s"). The process hung or was killed, the machine went down - or the game is still running'%(last[0],last[1][:60]))
    return dict(states=st,ended=ended,last=last,away=away,quiet=quiet,notes=notes)
def line(e):
    if e['kind'] in ('ASSERT','CRASH'): return '%s %s %#x %s'%(e['time'],e['kind'] if e['kind']=='ASSERT' else 'CRASH %08x'%e['code'],e['at'],e['acc'])
    if e['kind']=='FAULT':
        return '%s %s %08x at %s %#x %s'%(e['time'],'FATAL' if e['text'].startswith('FATAL') else 'fault, first chance (may have been handled)',e['code'],e['module'],e['at'],e['acc'])
    return '%s %s'%(e['time'],e['text'])
def report(path=None,every=False):
    path=path or os.path.join(kl.DD,'KLHook.log')
    rs=raw(path)
    if every:
        al=events(path,True)
        for n,(h,ev) in enumerate(al):
            c={}
            for e in ev: c[e['kind']]=c.get(e['kind'],0)+1
            noend=len(rs)==len(al) and not any(ENDS.search(r) for t,r in rs[n])      # a hang, a kill - or the running game
            print(h[:60],' '.join('%s %d'%x for x in sorted(c.items())),'|',next((e['text'] for e in reversed(ev) if e['kind']=='RESULT'),'NO END LINE, stops at '+rs[n][-1][0] if noend else ''))
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
    if rs:
        c=course(rs[-1])
        if c['states']: print('session states: '+' '.join('%#x'%s[2] for s in c['states'][-12:])+'   (last change %s %#x -> %#x)'%c['states'][-1])
        for t in c['notes']: print('note: '+t)
    return ev
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if x!='--all']; report(a[0] if a else None,'--all' in sys.argv)
