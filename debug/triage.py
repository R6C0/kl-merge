"""triage.py [dump ...] [--level <prp | zip>] [--keep]   start here after a crash.
No dump given: decodes the last session of <Dog Days>/KLHook.log and goes through the KLHook_N.dmp that session wrote
(the hook restarts at KLHook_1.dmp on every run of the game and overwrites: dumps left from an older run are skipped;
without a log, the game's own newest kl2_*_crash_*.mdmp). Each dump: what faulted, and why if the site is known. The FIRST
dump that holds a .prp reader is located in the level it was reading - node, name, class, record, field (locate.py) - and
compared with the layouts Dog Days' own levels store for that class or controller (layouts.py). Later ones are usually fallout.
The located level's .prp/.gms/.buf are copied to <temp>/kl_triage; --keep also copies the log and the dumps there, which
is the only way they survive the next run of the game.
Other tools here: check.py (pre-flight of a built level, run it BEFORE installing), layouts.py, log.py, dump.py, buf.py,
locate.py, mem.py, dasm.py, rtti.py, vtfuncs.py, enums.py; kl.py is what they share. Each prints its usage as docstring."""
import glob,os,re,shutil,sys,time
import kl,dump,buf,locate,log,layouts
a=sys.argv[1:]; level=None; keep='--keep' in a
if keep: a.remove('--keep')
if '--level' in a: i=a.index('--level'); level=a[i+1]; del a[i:i+2]
every=bool(a)                                           # dumps named on the command line are all located
if not a:
    lg=os.path.join(kl.DD,'KLHook.log')
    if os.path.isfile(lg):
        ev=log.report(lg); names=[e['dump'] for e in ev if e['dump']]; print()
        a=[os.path.join(kl.DD,n) for n in dict.fromkeys(names) if os.path.isfile(os.path.join(kl.DD,n))]
        for n in set(names):
            if names.count(n)>1: print('note: %s was written %d times this session; the file holds the last event'%(n,names.count(n)))
        for p in kl.dumps():
            if p not in a: print('note: %s is left from an earlier run of the game - skipped'%os.path.basename(p))
    else: a=sorted(glob.glob(os.path.join(glob.escape(kl.DD),'kl2_*crash*.mdmp')),key=os.path.getmtime)[-1:]
    if keep and a:
        d=os.path.join(kl.TMP,time.strftime('%Y%m%d_%H%M%S',time.localtime(os.path.getmtime(a[0])))); os.makedirs(d,exist_ok=True)
        for p in a+[lg]:
            if os.path.isfile(p): shutil.copy2(p,d)
        print('kept the log and %d dumps in %s'%(len(a),d))
E=kl.Exe(); done=False
for p in a:
    D=kl.Dump(kl.path(p)); print('=== '+os.path.basename(p)); dump.summary(D,E)
    print('callers: '+dump.chain(dump.frames(D,E)[:8]))
    g=buf.get(D,E)
    if not g or D.addr==0xa8e3cb: print(); continue     # no reader, or the DRM probe
    so,pos,size,b=g; print('.prp reader: stream %#x pos %#x of %#x'%(so,pos,size))
    if every or not done:
        f=locate.find(b[:size],level)
        if not f: print('  its buffer is in no .prp tried: level rebuilt since the crash? pass --level <the .prp or .zip the game read>')
        else:
            r=locate.report(*f,pos); done=True; stem=os.path.join(kl.TMP,os.path.basename(p))
            for ext in ('prp','gms','buf'):
                x=f[1](ext)
                if x: open(stem+'.'+ext,'wb').write(x)
            print('level files kept as '+stem+'.prp/.gms/.buf')
            who=r['ctrl'] if r['ctrl'] and r['csig'] else r['cls']
            if who and who!='?':
                tot=layouts.layouts(who); print('Dog Days\' own levels store %s as:'%who)
                for (kind,sg),(c,ls,eg) in sorted(tot.items(),key=lambda x:-x[1][0])[:6]: print('%8d %s   %d levels, e.g. %s node %d'%(c,sg,len(ls),*eg))
                if not tot: print('   (never: no shipped level has one)')
                if r['csig']: print('this record  %s   %s'%(r['csig'],'is one of them' if any(sg==r['csig'] for _,sg in tot) else '<== NOT a layout Dog Days stores for it'))
    print()
