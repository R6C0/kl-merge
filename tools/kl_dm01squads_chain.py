import sys, os, shutil, tempfile, subprocess, zipfile, hashlib
sys.path.insert(0,'C:/kl-merge/kl-merge/tools')
import kl_spawns_1024 as SP, kl_interact_graft as IG, kl_graft, kl_dm01squads_1025 as SQ
W='C:/kl_build_1024/dm01fix_1025a/work/'
O='C:/kl_build_1024/dm01squads_1025a/out/'
LIVE='C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days/KLExpansion/Maps/DM01/F01_Main.zip'
pl=IG.PLAN['DM01']
# warehouse doors (stage A): the hall's main door 841 (swung shut along x) and three virtual doors across the west bay (x 1955-2280 at the wall z 19684)
WH_DOORS=[('snap',841,(1.0,0.0,0.0))]+[('at',(float(x),62.0,19684.0),(1.0,0.0,0.0)) for x in (2060,2180,2300)]
SQ.squads(W+'s1_carexit.zip', O+'a_s1.zip', print)
IG.build(O+'a_s1.zip',O+'a_s2.zip',ext=pl['ext'],doors=list(pl['doors'])+WH_DOORS,extra_drop=pl['extra_drop'],spots_near=pl['spots_near'],ext_doors=pl['ext_doors'])
d=tempfile.mkdtemp(prefix='dm01sq_')
os.makedirs(d+'/in'); shutil.copy2(O+'a_s2.zip',d+'/in/F01_Main.zip')
prp,rep=SP.fix_one(d+'/in/F01_Main.zip',d+'/w',print,SP.ACTIVE['DM01'])
print({k:rep[k] for k in ('active','notes','problems') if k in rep})
open(O+'a_spawn.prp','wb').write(prp)
subprocess.check_call([sys.executable,'C:/kl_build_1024/dm01chain_1024r3/work/splice.py',O+'a_s2.zip',O+'a_spawn.prp',O+'a_s3.zip'])
live=zipfile.ZipFile(LIVE); s3=zipfile.ZipFile(O+'a_s3.zip')
order=[i.filename for i in s3.infolist()]
files=[(n, live.read(n) if n=='Menu/online.xml' else s3.read(n)) for n in order]
out=kl_graft.write_zip(O+'DM01_F01_Main.zip', files)
print('written', out, hashlib.md5(open(out,'rb').read()).hexdigest())
