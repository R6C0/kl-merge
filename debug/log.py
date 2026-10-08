"""log.py [KLHook.log]   the last session of the hook's log, with every known site and node-loader caller spelled out."""
import os,re,sys
import kl
def events(path):
    """-> (session header, [event dict]) of the last '==== KLHook loaded' session."""
    head=''; out=[]
    for line in open(path,errors='replace'):
        if '==== KLHook loaded' in line: head=line.strip(); out=[]; continue
        m=re.match(r'(\S+) (ASSERT|CRASH \w+) at kl2\.exe\+\w+ \((\w+)\)',line)
        if m: out.append(dict(time=m.group(1),kind=m.group(2),at=int(m.group(3),16),reg={},callers=[],dump='',acc='')); continue
        if not out: continue
        e=out[-1]
        if 'eax=' in line: e['reg']={k:int(v,16) for k,v in re.findall(r'(e\w\w)=(\w+)',line)}
        elif 'callers:' in line: e['callers']=[int(x,16) for x in line.split('callers:')[1].split()]
        elif 'address' in line: e['acc']=' '.join(line.split()[1:])
        elif 'dump written' in line: e['dump']=re.findall(r'KLHook_\d+\.dmp',line)[0]
    return head,out
def report(path=None):
    head,ev=events(path or os.path.join(kl.DD,'KLHook.log')); print(head)
    for e in ev:
        print('%s %s %#x %s %s'%(e['time'],e['kind'],e['at'],e['acc'],('['+e['dump']+']') if e['dump'] else ''))
        t=kl.explain(e['at'],e['reg']) if e['reg'] else kl.SITES.get(e['at'],'')
        if t: print('      '+t)
        print('      callers: '+' < '.join('%#x%s'%(c,' ('+kl.CALLERS[c]+')' if c in kl.CALLERS else '') for c in e['callers']))
    return ev
if __name__=='__main__': report(sys.argv[1] if len(sys.argv)>1 else None)
