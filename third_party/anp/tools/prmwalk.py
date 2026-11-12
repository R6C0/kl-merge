import struct,collections,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
class PRM:
    def __init__(s,d):
        s.d=d
        s.off,s.cnt,_,_=struct.unpack_from('<4I',d)
        s.desc=[struct.unpack_from('<4I',d,s.off+i*16) for i in range(s.cnt)]
    def ch(s,i): o,sz,k,u=s.desc[i]; return s.d[o:o+sz]
    def w(s,i): c=s.ch(i); return struct.unpack_from('<%dI'%(len(c)//4),c)
    def ok(s,h): return 0<h<s.cnt
def walk(P, prims):
    st=dict(prim=collections.Counter(), mesh=collections.Counter(), gd=collections.Counter(), ex={})
    for p in prims:
        if not P.ok(p): continue
        h=P.w(p)
        st['prim'][(h[0],len(P.ch(p)))]+=1
        if h[0]!=0x70100: st['ex'].setdefault(('prim',h[0]),p); continue
        lst=P.w(h[6])
        for m in lst[:h[5]]:
            if not P.ok(m): continue
            mw=P.w(m); key=(mw[0],len(P.ch(m)))
            st['mesh'][key]+=1; st['ex'].setdefault(('mesh',)+key,m)
            if len(mw)>10 and P.ok(mw[10]):
                g=P.w(mw[10])
                for gg in g[:1]:
                    if P.ok(gg):
                        k2=(mw[0],len(P.ch(gg))); st['gd'][k2]+=1; st['ex'].setdefault(('gd',)+k2,gg)
    return st
if __name__=='__main__':
    import zipfile
    from gms import GMS
    from anp_paths import WORK, game_dir, DD_FOLDER, DM_FOLDER
    zips={'dd':(game_dir('ANP_DD_GAME',DD_FOLDER),'L01','Scenes/Locations/L01/L01_Main.prm'),
          'dm':(game_dir('ANP_DM_GAME',DM_FOLDER),'M01_A','Scenes/Locations/M01_A/M01A_Main.prm')}
    for side,n,pk in [('dd','L01_Main','dd'),('dm','M01A_Main','dm')]:
        b=os.path.join(WORK,'scn',side,n); G=GMS(b+'.gms',b+'.buf')
        game,folder,entry=zips[pk]
        P=PRM(zipfile.ZipFile(os.path.join(game,'Scenes','Locations',folder,n+'.zip')).read(entry))
        prims=sorted(set(e['prim'] for e in G.ents if e['prim']))
        st=walk(P,prims)
        print(side,'prims',len(prims))
        for k in ['prim','mesh','gd']:
            print(' ',k,[(hex(a),b,c) for (a,b),c in st[k].most_common()])
        for k,v in sorted(st['ex'].items(),key=str)[:40]:
            print('   ex',k[0],hex(k[1]),k[2:] ,v)
