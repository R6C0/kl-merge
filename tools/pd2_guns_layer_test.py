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
    if name == '1106s':      # the stock-map layer repeats every key by design (other maps, other base)
        continue
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

# 1106d: four RPK keys on the Minimi items, staged on the 1106c stage, 10 maps without DM05A, off-drive backup, body detail 63 (62|7)
L.configure('1106d')
check(L.KEYS == ['RPK45', 'RPK46', 'RPK47', 'RPK48'] and L.TAG == '.before-pd2guns1106d', '1106d keys / tag')
check(L.BASE == r'D:\kl_stage\pd2guns_1106c' and L.src_root() == L.BASE, '1106d is staged on the 1106c stage')
check(L.default_out() == r'D:\kl_stage\pd2guns_1106d' and L.LAYERS['1106d']['backup'] == r'D:\kl_stage\pd2guns_1106d_backup', '1106d out / backup on D:')
check('DM05A' not in L.LAYERS['1106d']['maps'] and len(L.LAYERS['1106d']['maps']) == 10, '1106d: 10 maps, not DM05A')
check(all(L.DETAIL[k] == 63 for k in L.KEYS), '1106d body detail 62|7 = 63')
sp = {s['key']: s for s in M.SPECS}
check([sp[k]['item'] for k in L.KEYS] == [45, 46, 47, 48] and all(sp[k]['unit'].endswith('wpn_npc_rpk') for k in L.KEYS), '1106d specs = items 45-48 on the PD2 RPK')
check(sp['RPK47']['template'] == 'Mg_Minimi_SPW' and sp['RPK45']['template'].endswith('Heli_Player'), '1106d Minimi templates')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106c']['keys']) and set(L.KEYS).isdisjoint(L.LAYERS['1106b']['keys']), '1106d adds keys, repeats none')
py_d = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106d']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106d']['backup'])
check("TAG = '.before-pd2guns1106d'" in py_d and '@' not in py_d.replace('@echo', ''), '1106d installer text')
L.configure('1106b')

# 1106e: the Deagle on item 63, staged on the 1106d stage, same 10 maps, off-drive backup, pistol body detail 31
L.configure('1106e')
check(L.KEYS == ['DEAG63'] and L.TAG == '.before-pd2guns1106e', '1106e keys / tag')
check(L.BASE == r'D:\kl_stage\pd2guns_1106d' and L.src_root() == L.BASE, '1106e is staged on the 1106d stage')
check(L.default_out() == r'D:\kl_stage\pd2guns_1106e' and L.LAYERS['1106e']['backup'] == r'D:\kl_stage\pd2guns_1106e_backup', '1106e out / backup on D:')
check(L.LAYERS['1106e']['maps'] == L.LAYERS['1106d']['maps'] and L.DETAIL['DEAG63'] == 31, '1106e: same 10 maps as 1106d, pistol detail 31')
sp = {s['key']: s for s in M.SPECS}
check(sp['DEAG63']['item'] == 63 and sp['DEAG63']['template'] == 'HG_M9Beretta_Human_Shield' and sp['DEAG63']['unit'].endswith('wpn_npc_deagle'), '1106e spec = item 63 on the PD2 Deagle')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106d']['keys'] + L.LAYERS['1106c']['keys'] + L.LAYERS['1106b']['keys']), '1106e adds keys, repeats none')
py_e = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106e']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106e']['backup'])
check("TAG = '.before-pd2guns1106e'" in py_e and '@' not in py_e.replace('@echo', ''), '1106e installer text')
L.configure('1106b')

# 1106s: all 19 keys on the 9 stock DD maps, live zips as base, off-drive backup, no DD10 / Scenes
L.configure('1106s')
check(L.BASE is None and L.src_root() == M.MAPROOT and L.TAG == '.before-pd2guns1106s', '1106s is baked on the live zips')
check(sorted(L.KEYS + L.LAYERS['1106f']['keys']) == sorted(s['key'] for s in M.SPECS) and len(L.KEYS) == 19, '1106s keys = every spec except the 1106f re-looks')
check(L.LAYERS['1106s']['maps'] == ['DD0%d' % i for i in range(1, 10)], '1106s: DD01..DD09, not DD10')
check(L.default_out() == r'D:\kl_stage\pd2guns_1106s' and L.LAYERS['1106s']['backup'] == r'D:\kl_stage\pd2guns_1106s_backup', '1106s out / backup on D:')
check(all(k in L.DETAIL for k in L.KEYS), '1106s: a DETAIL entry for every key')
py_s = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106s']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106s']['backup'])
check("TAG = '.before-pd2guns1106s'" in py_s and '@' not in py_s.replace('@echo', ''), '1106s installer text')
L.configure('1106b')

# 1106f: PD2 MG42 (item 42) and PAR (item 40) re-look two RPK duplicates, staged on the 1106e stage, same 10 maps, off-drive backup, detail 15 (RPK root keeps its hidden box)
L.configure('1106f')
check(L.KEYS == ['MG42', 'PAR40'] and L.TAG == '.before-pd2guns1106f', '1106f keys / tag')
check(L.BASE == r'D:\kl_stage\pd2guns_1106e' and L.src_root() == L.BASE, '1106f is staged on the 1106e stage')
check(L.default_out() == r'D:\kl_stage\pd2guns_1106f' and L.LAYERS['1106f']['backup'] == r'D:\kl_stage\pd2guns_1106f_backup', '1106f out / backup on D:')
check(L.LAYERS['1106f']['maps'] == L.LAYERS['1106e']['maps'] and 'DM05A' not in L.LAYERS['1106f']['maps'], '1106f: the same 10 maps, not DM05A')
sp = {s['key']: s for s in M.SPECS}
check(sp['MG42']['item'] == 42 and sp['PAR40']['item'] == 40 and sp['MG42']['template'] == sp['RPK42']['template'] and sp['PAR40']['template'] == sp['RPK40']['template'],
      '1106f re-looks the templates of RPK42 / RPK40')
check(sp['MG42']['unit'].endswith('wpn_third_lmg_mg42_pts') and sp['PAR40']['unit'].endswith('wpn_third_lmg_par_pts') and len(sp['PAR40']['parts']) == 9, '1106f units / PAR 9 materials')
check(len(M.SPECS) == 21 and 'MINI43' not in sp, 'no minigun spec (fit cost 16.8, rejected)')
check(L.DETAIL['MG42'] == 15 and L.DETAIL['PAR40'] == 15, '1106f body detail 15')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106e']['keys'] + L.LAYERS['1106d']['keys'] + L.LAYERS['1106c']['keys'] + L.LAYERS['1106b']['keys']), '1106f adds keys, repeats none')
py_f = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106f']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106f']['backup'])
check("TAG = '.before-pd2guns1106f'" in py_f and '@' not in py_f.replace('@echo', ''), '1106f installer text')
L.configure('1106b')

print('pd2_guns_layer_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
