#!/usr/bin/env python3
"""kl_dm_reverb_test.py - off-game checks of kl_dm_reverb.py: the parameter parsers, the distance and the nearest-effect choice, the kind rule,
the installer text. The heavy part (read-back of a staged DM02 zip) runs only when C:/kl_build_1024/dmreverb_1108 exists, else it is SKIPPED (exit 0)."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm_reverb as R

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


# DM roomeffect (0x70 bytes) parse: build one with known values
b = bytearray(0x70)
struct.pack_into('<i', b, 0x18, 7)
struct.pack_into('<f', b, 0x1c, 12.5)
struct.pack_into('<f', b, 0x20, 0.75)
struct.pack_into('<i', b, 0x24, -1000)
struct.pack_into('<i', b, 0x28, -300)
struct.pack_into('<f', b, 0x30, 1.8)
struct.pack_into('<f', b, 0x34, 0.6)
struct.pack_into('<i', b, 0x3c, -500)
struct.pack_into('<i', b, 0x44, -200)
p = R.dm_params(bytes(b), 0)
check(p['env'] == 7 and abs(p['size'] - 12.5) < 1e-6 and abs(p['diffusion'] - 0.75) < 1e-6, 'dm_params env/size/diffusion')
check(p['room'] == -1000 and p['roomHF'] == -300 and abs(p['decay'] - 1.8) < 1e-5 and p['refl'] == -500 and p['reverb'] == -200, 'dm_params levels')
i = R.ideal_dd(p)
check(abs(i['diffusion'] - 75.0) < 1e-6 and i['room'] == -1000 and i['hfref'] == 5000.0, 'ideal_dd percent + passthrough')

# DD roomeffect (0x50 bytes)
d = bytearray(0x50)
struct.pack_into('<f', d, 0x1c, 80.0)
struct.pack_into('<f', d, 0x24, -900.0)
struct.pack_into('<f', d, 0x2c, 2.5)
struct.pack_into('<f', d, 0x30, 0.7)
q = R.dd_params(bytes(d), 0)
check(q['diffusion'] == 80.0 and q['room'] == -900.0 and abs(q['decay'] - 2.5) < 1e-6 and abs(q['decayHF'] - 0.7) < 1e-6, 'dd_params')

# kind rule
check(R.kind_of('ROOT/x/Roomeffect/Inside/Foo') == 'inside', 'kind inside (stock)')
check(R.kind_of('Roomeffect/outside/Bar') == 'outside', 'kind outside (stock)')
check(R.kind_of('M02_FA_A_Ins_Store') == 'inside' and R.kind_of('M02_FA_A_Out_Lot') == 'outside', 'kind DM room names')
check(R.kind_of('Whatever') is None, 'kind unknown')


def eff(off, name, decay, hf, room, reverb, refl):
    return {'off': off, 'name': name, 'p': dict(decay=decay, decayHF=hf, room=room, reverb=reverb, refl=refl)}


E = [eff(10, 'a/inside/short', 0.5, 0.8, -1000, -500, -600), eff(20, 'a/inside/long', 4.0, 0.5, -500, 0, -300),
     eff(30, 'a/outside/open', 1.0, 0.9, -2000, -1000, -1500)]
dmp = dict(decay=3.8, decayHF=0.5, room=-500, reverb=0, refl=-300)
check(R.distance(dmp, E[1]['p']) < R.distance(dmp, E[0]['p']), 'distance: the similar effect is nearer')
check(R.distance(dmp, dmp) == 0, 'distance to itself is 0')
best, dist = R.choose(dmp, 'M02_FA_A_Ins_Atrium', E)
check(best['off'] == 20, 'choose: nearest inside effect')
best, dist = R.choose(dmp, 'M02_FA_A_Out_Lot', E)
check(best['off'] == 30, 'choose: outside rooms only pick outside effects')
best, dist = R.choose(dmp, 'Unknown', E)
check(best['off'] == 20, 'choose: unknown kind searches all')
check(R.choose(dmp, 'M02_FA_A_Ins_X', E[2:])[0]['off'] == 30, 'choose: empty kind set falls back to all')

# constants and installer text
check(R.GROUP == 'KL_Reverb!' and R.TAG == '.before-1108dmreverb', 'group and tag')
py = R.INSTALL_PY.replace('@FILES@', 'F02').replace('@TAG@', R.TAG)
check('@' not in py.replace('@echo', '').replace('@FILES', ''), 'installer: no unreplaced placeholder')
check(R.TAG in py and '--undo' in py and '--dry' in py, 'installer text has tag, --undo, --dry')
compile(py, 'install.py', 'exec')

# heavy part: read back the staged zips when they exist
stg = 'C:/kl_build_1024/dmreverb_1108'
zp = os.path.join(stg, 'F02_Main.zip')
if os.path.exists(zp):
    base = None
    try:
        import json
        pins = json.load(open(os.path.join(stg, 'pins.json')))
        live = os.path.join(r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', 'KLExpansion', 'Maps', 'DM02', 'F02_Main.zip')
        if os.path.exists(live) and R.md5(live) == pins['files']['F02_Main.zip']['old']:
            base = live
    except Exception as e:
        print('note: pins unreadable: %r' % e)
    out = []
    res = R.check(zp, base, log=out.append)
    check(len(res) > 40 and all(r[0] == 'PASS' for r in res), 'staged zip read-back: %d PASS, %d FAIL' % (sum(r[0] == 'PASS' for r in res), sum(r[0] == 'FAIL' for r in res)))
    if base is None:
        print('note: live DM02 differs from the pinned base (or absent): size comparison skipped')
else:
    print('SKIP: no staged zip at %s (heavy read-back)' % stg)

print('kl_dm_reverb_test: %d checks, %d fail' % (checks, fails))
sys.exit(1 if fails else 0)
