import sys,os,zipfile,collections,time,pickle
sys.path.insert(0,'.')
import kl_convert as K
from kl_prp import Prp
DM=os.path.expanduser('~/mnt/Kane and Lynch Dead Men'); DD=os.path.expanduser('~/mnt/Kane & Lynch 2 - Dog Days')
t=time.time(); ref=K.DDReference(DD); print('reference %.0fs'%(time.time()-t))
lvls=sys.argv[1:] or ['M01_FA_A','M02_FA_A','M03_FA_A','M06_FA_A']
for lv in lvls:
    base=lv.replace('_','')
    zf=zipfile.ZipFile(DM+'/Scenes/Locations/%s/%s_Main.zip'%(lv,base)); n='Scenes/Locations/%s/%s_Main.prp'%(lv,base)
    types=K.node_types(zf,n); log=collections.defaultdict(collections.Counter)
    out,st=K.convert_level(zf.read(n),ref,log,types)
    open('converted/%s/%s_Main.prp'%(lv,base),'wb').write(out)
    p=Prp(out); bad=collections.Counter(); prob=collections.Counter()
    def check(key,o,known):
        sg=K.csig(o)
        if sg not in known: prob['layout '+str(key)[:40]]+=1; return
        for i,u in enumerate(K.units(K.body(o))):
            if u[0][0]==0x0e and len(u)==1:
                v=ref.enums.get((key,sg,i))
                if v is not None and not K.enum_ok(p.key(u[0]),v): prob['enum '+str(key)[:40]]+=1
            elif u[0][0]==0x01:
                L=ref.alen.get((key,sg,i))
                import struct as S
                if L and len(L)==1 and S.unpack('<I',u[0][1])[0] not in L: prob['array-length '+str(key)[:40]]+=1
            elif u[0][0]==0x04:
                sl,si=ref.lists.get((key,sg,i),(0,0))
                if K.is_list(u) and not sl: prob['list-where-int '+str(key)[:40]]+=1
                if not K.is_list(u) and u[0][1]!=b'\0\0\0\0' and not si: prob['int-where-list '+str(key)[:40]]+=1
    for tid,nd in zip(types,p.nodes()):
        if tid in ref.cls: check(('<class>',tid),nd['props'],ref.cls[tid])
        for nm,o in nd['ctrls']:
            check(p.key(nm),o,ref.ctrl.get(p.key(nm),{}))
    items=collections.Counter()
    for nd in p.nodes():
        for nm,o in nd['ctrls']:
            if p.key(nm)=='InventoryBinding':
                e=[p.key(t) for t in o if t[0]==0x0e][0]
                if e!='eFF2ItemNoItem': items[e]+=1
    dup={k:v for k,v in items.items() if v>1}
    if dup: prob['duplicate item bindings '+str(dup)]+=1
    unk=[k for k in items if k not in K.DD_ENUMS]
    if unk: prob['items not in Dog Days '+str(unk)]+=1
    print(lv,dict(st)); print('  problems:',sum(prob.values()),prob.most_common(12),'| %.0fs'%(time.time()-t))
