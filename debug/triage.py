"""triage.py [dump ...] [--level <prp | zip>] [--keep]   start here after a crash.
No dump given: decodes the last session of <Dog Days>/KLHook.log (log.py: unknown lines are skipped) and goes through
 - the dumps that session's lines name: KLHook_N.dmp and the watchdog's KLHook_stall / _stackoverflow / _crt.dmp
   (the hook restarts at KLHook_1.dmp on every run of the game and overwrites: dumps left from an older run are skipped),
 - the game's own kl2_<build>_crash_*.mdmp written since that session began. It is the only record of a fault OUTSIDE
   kl2.exe when the ship hook is installed (that one logs kl2.exe faults only), so it is always read when there is one;
   without a log at all, the newest one.
Each dump: what faulted, and why if the site is known. The FIRST dump that holds a .prp reader is located in the level it
was reading - node, name, class, record, field (locate.py) - and compared with the layouts Dog Days' own levels store for
that class or controller (layouts.py). Later ones are usually fallout. A dump that cannot be read is reported and skipped.
The located level's .prp/.gms/.buf are copied to <temp>/kl_triage; --keep also copies the log and the dumps there, which
is the only way they survive the next run of the game.
Other tools here: check.py (pre-flight of a built level, run it BEFORE installing), layouts.py, log.py, dump.py, buf.py,
locate.py, mem.py, dasm.py, rtti.py, vtfuncs.py, enums.py, zombies.py (lingering kl2.exe entries and who holds them);
kl.py is what they share. Each prints its usage as docstring."""
import os,shutil,sys,time
import kl,dump,buf,log
a=sys.argv[1:]; level=None; keep='--keep' in a
if keep: a.remove('--keep')
if '--level' in a: i=a.index('--level'); level=a[i+1]; del a[i:i+2]
every=bool(a)                                           # dumps named on the command line are all located
if not a:
    lg=os.path.join(kl.DD,'KLHook.log'); since=None
    if os.path.isfile(lg):
        try: ev=log.report(lg)
        except Exception as x: ev=[]; print('KLHook.log could not be decoded (%s: %s) - going on with the dump files'%(type(x).__name__,x))
        names=[n for e in ev for n in e['dumps']]; print()
        a=[os.path.join(kl.DD,n) for n in dict.fromkeys(names) if os.path.isfile(os.path.join(kl.DD,n))]
        for n in dict.fromkeys(names):
            if names.count(n)>1: print('note: %s was written %d times this session; the file holds the last event'%(n,names.count(n)))
            if not os.path.isfile(os.path.join(kl.DD,n)): print('note: %s is named in the log but no longer in the game folder'%n)
        for p in kl.dumps():
            if p not in a: print('note: %s is left from an earlier run of the game - skipped'%os.path.basename(p))
        since=log.started(lg,log.events(lg)[0])
        own=kl.game_dumps(since) if since else []
        if own:
            print('note: the game wrote its own dump this session: %s'%', '.join(os.path.basename(p) for p in own)); a+=own[-1:]
        elif any(e['kind']=='FAULT' and e['module'].lower()!='kl2.exe' and e['text'].startswith('FATAL') for e in ev):
            print('note: a fatal fault outside kl2.exe is logged but the game wrote no dump of its own this session')
    else: a=kl.game_dumps()[-1:]
    if not a: print('no dump to look at: this session wrote none (a clean run, or an end the hook does not see - check KLHook.result and the Windows event log)')
    if keep and a:
        d=os.path.join(kl.TMP,time.strftime('%Y%m%d_%H%M%S',time.localtime(os.path.getmtime(a[0])))); os.makedirs(d,exist_ok=True)
        for p in a+[lg]:
            if os.path.isfile(p): shutil.copy2(p,d)
        print('kept the log and %d dumps in %s'%(len(a),d))
if not a: sys.exit(0)
import locate,layouts
E=kl.Exe(); done=False
for p in a:
    print('=== '+os.path.basename(p))
    try: D=kl.Dump(kl.path(p))
    except Exception as x: print('cannot be read as a minidump (%s: %s)\n'%(type(x).__name__,x)); continue
    dump.summary(D,E)
    if not D.reg: print(); continue
    print('callers: '+dump.chain(dump.frames(D,E)[:8]))
    if dump.wants_foreign(D,E): print(dump.foreign_line(D,E))
    for t in dump.who(D,E): print(t)                             # which thread, and the overlays / recorders in the process
    if D.code is None or D.addr==0xa8e3cb: print(); continue     # a watchdog dump, or the DRM probe: no reader to locate
    try: g=buf.get(D,E)
    except Exception as x: g=None; print('.prp reader not looked for (%s: %s)'%(type(x).__name__,x))
    if not g: print(); continue
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
