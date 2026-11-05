"""Slim DD10 (F07) TEX: selective mip drop. Usage: mk_slim.py IN.zip OUT.zip [--tier 1|2|3]"""
import sys,os,re,zipfile,collections
sys.path.insert(0,'C:/kl-merge/kl-merge/tools')
import kl_texmat as T, kl_texmip as M
NONDIFF=re.compile(r'#(Normal|Bump|Specular|Illumination|normal|specular|mask|Mask)', re.I)
def rule(nm, mx, tier):
    """None = keep, else reason. Only world surface textures: tex:Levels/, tex:_Test/, tex:Vehicles/."""
    lv = nm.startswith('tex:Levels/') or nm.startswith('tex:_Test/')
    ve = nm.startswith('tex:Vehicles/')
    if not (lv or ve): return None
    if mx >= 2048: return 'T1 >=2048'
    if tier >= 2 and lv and mx >= 1024 and NONDIFF.search(nm) and 'Diffuse' not in nm: return 'T2 level 1024 non-diffuse'
    if tier >= 3 and lv and mx >= 1024: return 'T3 level 1024 diffuse'
    return None
def run(src,dst,tier):
    zin=zipfile.ZipFile(src)
    mem=M.tex_member(zin)[0]
    old=zin.read(mem); t=T.read_tex(old)
    listed=set()
    for x in t.tex.values():
        if x.frames: listed.update(x.frames)
    saved=collections.Counter(); cnt=collections.Counter(); rows=[]
    for i in sorted(t.tex):
        x=t.tex[i]
        try: d=M.parse(x.entry)
        except Exception: continue
        mx=max(d['w'],d['h'])
        why=rule(d['name'],mx,tier)
        if not why: continue
        if d['flags']&(T.CUBE|T.ANIMATED) or x.cube is not None or x.faces or x.frames is not None or i in listed: continue
        if d['mips']<=1 or min(d['w'],d['h'])<128: continue
        if M.chain_ok(d): continue
        if d['fc'] in M.BLOCK and min(d['w'],d['h'])>>1<4: continue
        if d['w']%2 or d['h']%2: continue
        new,cut=M.drop(x.entry,d,1); x.entry=new
        saved[why]+=cut; cnt[why]+=1; rows.append((i,d['name'],d['fc'],d['w'],d['h'],why,cut))
    newtex=T.write_tex(t)
    # verify: reparse, same ids, every dropped record parses
    b=T.read_tex(newtex); assert set(b.tex)==set(t.tex)
    for i,x in b.tex.items():
        try: M.parse(x.entry)
        except Exception as e: raise SystemExit('reparse fail %d %s'%(i,e))
    print('tier',tier,dict(cnt),{k:round(v/1e6,1) for k,v in saved.items()},'total MB',round(sum(saved.values())/1e6,1),'TEX',len(old),'->',len(newtex))
    with zipfile.ZipFile(dst,'w') as zo:
        for zi in zin.infolist():
            zo.writestr(zi, newtex if zi.filename==mem else zin.read(zi.filename), compress_type=zi.compress_type, compresslevel=6)
    with open(dst+'.texlist.txt','w') as f:
        for r in rows: f.write('%d\t%s\t%s\t%dx%d\t%s\t%d\n'%(r[0],r[1],r[2].decode(),r[3],r[4],r[5],r[6]))
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],int(sys.argv[sys.argv.index('--tier')+1]) if '--tier' in sys.argv else 2)
