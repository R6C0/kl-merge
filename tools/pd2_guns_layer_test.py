#!/usr/bin/env python3
"""pd2_guns_layer_test.py - off-game checks of the layer parameterisation of pd2_guns_layer.py (no game files read, nothing baked):
the 1106b defaults, the 1106c layer (keys, tag, base stage, out folder), the installer text per layer and the key tables."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pd2_guns_layer as L
import pd2_guns_multi as M

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


# default = 1106b, as before the parameterisation
check(L.LAYER == '1106b' and L.KEYS == ['C45', 'HRL50', 'HRL51'] and L.TAG == '.before-pd2guns1106b' and L.BASE is None, '1106b defaults')
check(L.src_root() == M.MAPROOT, '1106b is baked on the live maps')
check(os.path.basename(L.default_out()) == 'pd2guns_1106b', '1106b default out')
py_b = L.INSTALL_PY.replace('@TITLE@', L.LAYERS['1106b']['title']).replace('@TAG@', L.TAG)
check("TAG = '.before-pd2guns1106b'" in py_b and '@' not in py_b.replace('@echo', ''), '1106b installer text')

# every layer: keys exist in SPECS, a body detail is known, keys of different layers are disjoint, tags differ
spec_keys = {s['key'] for s in M.SPECS}
seen = set()
for name, lay in L.LAYERS.items():
    check(set(lay['keys']) <= spec_keys, '%s: keys are pd2_guns_multi SPECS' % name)
    check(set(lay['keys']) <= set(L.DETAIL), '%s: a body detail byte per key' % name)
    check(not (set(lay['keys']) & seen), '%s: keys disjoint from the other layers' % name)
    seen |= set(lay['keys'])
check(len({l['tag'] for l in L.LAYERS.values()}) == len(L.LAYERS), 'distinct backup tags')

# switch to 1106c and back
L.configure('1106c')
check(L.KEYS == ['R700', 'GL40', 'GL40GAS', 'GL40FLR'] and L.TAG == '.before-pd2guns1106c', '1106c keys / tag')
check(L.BASE == os.path.join(L.WORK_BUILD, 'pd2guns_1106b') and L.src_root() == L.BASE, '1106c is staged on the 1106b stage')
check(L.default_out().lower().startswith('d:'), '1106c default out is on D:')
py_c = L.INSTALL_PY.replace('@TITLE@', L.LAYERS['1106c']['title']).replace('@TAG@', L.TAG)
check("TAG = '.before-pd2guns1106c'" in py_c and '1106b' not in py_c.split('"""', 2)[2], '1106c installer text')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106b']['keys']), '1106c adds keys, repeats none')
L.configure('1106b')
check(L.KEYS == ['C45', 'HRL50', 'HRL51'] and L.BASE is None, 'configure back to 1106b')


# 1106b installer text is frozen (byte-identical to what was staged and installed on 11-06)
import hashlib
check(hashlib.md5(L.INSTALL_PY.encode()).hexdigest() == '581a74f95ef45261d2d3f0a2d94c231b', '1106b INSTALL_PY text unchanged')
check(L.LAYERS['1106b'].get('backup') is None and L.LAYERS['1106c']['backup'].lower().startswith('d:'), 'only 1106c uses the off-drive backup')

# off-drive installer: synthetic rehearsal (tiny files, scratch game + backup + stage folders, no real game file touched)
import json, shutil, subprocess, tempfile
L.configure('1106c')
tmp = tempfile.mkdtemp(prefix='pd2gl_')
try:
    stage, game, bkp = [os.path.join(tmp, x) for x in ('stage', 'game', 'bk')]
    def wr(p, data):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
    pins = {}
    for m in ('DMA', 'DMB'):
        pins[m] = {}
        for f in ('F01_Main.zip', 'KLGuns.ini'):
            old, new = (m + f + 'old').encode() * 50, (m + f + 'NEW').encode() * 60
            wr(os.path.join(game, 'KLExpansion', 'Maps', m, f), old); wr(os.path.join(stage, m, f), new)
            pins[m][f] = dict(old=hashlib.md5(old).hexdigest(), new=hashlib.md5(new).hexdigest(), size=len(new))
    json.dump(dict(maps=pins), open(os.path.join(stage, 'pins.json'), 'w'))
    L.write_installer(stage)
    inst = open(os.path.join(stage, 'install.py'), encoding='utf-8').read()
    check('@' not in inst.replace('@echo', '') and compile(inst, 'install.py', 'exec') is not None, 'offdrive installer text: no placeholder left, compiles')
    check(r"BACKUP = r'D:\kl_stage\pd2guns_1106c_backup'" in inst and 'os.rename' not in inst, 'offdrive installer: backup on D:, no in-place rename')
    check(os.path.isfile(os.path.join(stage, 'README.txt')) and 'OFF the game drive' in open(os.path.join(stage, 'README.txt')).read(), 'README names the backup place')
    def run(*a):
        r = subprocess.run([sys.executable, os.path.join(stage, 'install.py'), '--skip-run-check', '--game', game, '--backup', bkp, '--spare-mb', '0'] + list(a),
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    def live(m, f): return open(os.path.join(game, 'KLExpansion', 'Maps', m, f), 'rb').read()
    def is_new(m): return all(hashlib.md5(live(m, f)).hexdigest() == pins[m][f]['new'] for f in pins[m])
    def is_old(m): return all(hashlib.md5(live(m, f)).hexdigest() == pins[m][f]['old'] for f in pins[m])
    rc, o = run('--dry'); check(rc == 0 and is_old('DMA') and not os.path.exists(bkp) and 'net' in o, 'dry: nothing written')
    rc, o = run('--maps', 'DMA'); check(rc == 0 and is_new('DMA') and is_old('DMB'), 'install DMA only')
    check(all(hashlib.md5(open(os.path.join(bkp, 'DMA', f), 'rb').read()).hexdigest() == pins['DMA'][f]['old'] for f in pins['DMA']), 'backups on the scratch backup drive = pinned old')
    check(not any(n.endswith(('.new', '.before-pd2guns1106c')) for _, _, fs in os.walk(game) for n in fs), 'no .new / renamed backup left beside live files')
    rc, o = run('--maps', 'DMA'); check('backup exists' in o and is_new('DMA'), 'second install refused (backup exists)')
    wr(os.path.join(game, 'KLExpansion', 'Maps', 'DMB', 'KLGuns.ini'), b'drifted')
    rc, o = run('--maps', 'DMB'); check('changed since staging' in o and not os.path.exists(os.path.join(bkp, 'DMB')), 'drift refused, no backup made')
    wr(os.path.join(game, 'KLExpansion', 'Maps', 'DMB', 'KLGuns.ini'), (('DMB' + 'KLGuns.ini' + 'old').encode()) * 50)
    rc, o = run('--maps', 'DMB', '--fail-after', '1')
    check(rc != 0 and 'forced failure' in o and 'rolled back' in o and is_old('DMB') and not os.path.exists(os.path.join(bkp, 'DMB')), 'forced mid-map failure: rolled back from backups, backups dropped')
    check(not any(n.endswith('.new') for _, _, fs in os.walk(game) for n in fs), 'rollback leaves no .new')
    rc, o = run('--maps', 'DMB'); check(rc == 0 and is_new('DMB'), 'DMB installs after the rollback')
    wr(os.path.join(game, 'KLExpansion', 'Maps', 'DMB', 'KLGuns.ini'), b'someone else')
    rc, o = run('--undo', '--maps', 'DMB'); check('neither the staged nor the original' in o and os.path.isdir(os.path.join(bkp, 'DMB')), 'undo refuses a drifted live file, backups kept')
    wr(os.path.join(game, 'KLExpansion', 'Maps', 'DMB', 'KLGuns.ini'), live('DMA', 'KLGuns.ini')[:0] + (('DMB' + 'KLGuns.ini' + 'NEW').encode()) * 60)
    rc, o = run('--undo'); check(rc == 0 and is_old('DMA') and is_old('DMB') and not os.path.exists(bkp) or (rc == 0 and is_old('DMA') and is_old('DMB') and not os.listdir(bkp)), 'undo restores both maps, backups deleted after verify')
    rc, o = run('--undo'); check('SKIP' in o and is_old('DMA'), 'second undo: skipped (backups gone), nothing touched')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
L.configure('1106b')

print('pd2_guns_layer_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
