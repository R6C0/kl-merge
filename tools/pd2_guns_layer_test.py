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
    if name in ('1106s', '1106t'):      # the stock-map layers repeat every key by design (other maps, other base)
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
check('DM05A' in L.LAYERS['1106d']['maps'] and len(L.LAYERS['1106d']['maps']) == 11 and len(set(L.LAYERS['1106d']['maps'])) == 11 and 'DM01' in L.LAYERS['1106d']['maps'], '1106d: 11 maps (the 10 installed + DM05A)')
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
check(sorted(L.KEYS + L.LAYERS['1106f']['keys'] + L.LAYERS['1107r']['keys']) == sorted(s['key'] for s in M.SPECS) and len(L.KEYS) == 19, '1106s keys = every spec except the 1106f re-looks')
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
check(L.LAYERS['1106f']['maps'] == L.LAYERS['1106e']['maps'] and 'DM05A' in L.LAYERS['1106f']['maps'], '1106f: the same 11 maps as 1106e, with DM05A')
sp = {s['key']: s for s in M.SPECS}
check(sp['MG42']['item'] == 42 and sp['PAR40']['item'] == 40 and sp['MG42']['template'] == sp['RPK42']['template'] and sp['PAR40']['template'] == sp['RPK40']['template'],
      '1106f re-looks the templates of RPK42 / RPK40')
check(sp['MG42']['unit'].endswith('wpn_third_lmg_mg42_pts') and sp['PAR40']['unit'].endswith('wpn_third_lmg_par_pts') and len(sp['PAR40']['parts']) == 9, '1106f units / PAR 9 materials')
check(len(M.SPECS) == 23 and 'MINI43' not in sp, 'no minigun spec (fit cost 16.8, rejected)')
check(L.DETAIL['MG42'] == 15 and L.DETAIL['PAR40'] == 15, '1106f body detail 15')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106e']['keys'] + L.LAYERS['1106d']['keys'] + L.LAYERS['1106c']['keys'] + L.LAYERS['1106b']['keys']), '1106f adds keys, repeats none')
py_f = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106f']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106f']['backup'])
check("TAG = '.before-pd2guns1106f'" in py_f and '@' not in py_f.replace('@echo', ''), '1106f installer text')
check(L.LAYERS['1106f']['pic_items'] == [40, 42] and not any(L.LAYERS[k].get('pic_items') for k in ('1106b', '1106c', '1106d', '1106e', '1106s')), '1106f re-pictures cards of items 40 / 42, no other layer does')
# the card step: pairs of the picture items only, cards from <out>/pics/item_NN.png (synthetic pictures, default pair table), the texture replaced in place
import tempfile, kl_shop_pics as P
try:
    from PIL import Image
    td = tempfile.mkdtemp(prefix='pd2layer_pics_')
    for it in (40, 42):
        Image.new('RGBA', (445, 210), (200, 200, 200, 255)).save(os.path.join(td, 'item_%d.png' % it))
    cs = P.cards_of_items([40, 42], td, None, None, lambda x: None)
    check(sorted(cs) == ['KLPic_Pair08', 'KLPic_Pair11'] and all(len(v) == 512 * 256 * 4 for v in cs.values()), 'cards_of_items: item 42 -> Pair08, item 40 -> Pair11, 512x256 RGBA')
    check(P.cards_of_items([99], td, None, None, lambda x: None) == {}, 'cards_of_items: no pair for an unknown item')
    shutil.rmtree(td, ignore_errors=True)
except ImportError:
    pass
L.configure('1106b')

# 1106t: the 1106f change on the 9 stock maps, on the 1106s stage; one map at a time; --cleanup deletes the staged files of a verified map, undo works without them
L.configure('1106t')
check(L.KEYS == ['MG42', 'PAR40'] and L.TAG == '.before-pd2guns1106t' and L.LAYERS['1106t']['pic_items'] == [40, 42], '1106t keys / tag / pic_items')
check(L.BASE == r'D:\kl_stage\pd2guns_1106s' and L.src_root() == L.BASE, '1106t is staged on the 1106s stage')
check(L.default_out() == r'D:\kl_stage\pd2guns_1106t' and L.LAYERS['1106t']['backup'] == r'D:\kl_stage\pd2guns_1106t_backup', '1106t out / backup on D:')
check(L.LAYERS['1106t']['maps'] == L.LAYERS['1106s']['maps'], '1106t: DD01..DD09')
check(L.KEYS == L.LAYERS['1106f']['keys'], '1106t = the 1106f keys')
py_t = L.INSTALL_PY_OFFDRIVE.replace('@TITLE@', L.LAYERS['1106t']['title']).replace('@TAG@', L.TAG).replace('@BACKUP@', L.LAYERS['1106t']['backup'])
check("TAG = '.before-pd2guns1106t'" in py_t and '@' not in py_t.replace('@echo', ''), '1106t installer text')
L.configure('1106c')
tmp = tempfile.mkdtemp(prefix='pd2gl_')
try:
    stage, game, bkp = [os.path.join(tmp, x) for x in ('stage', 'game', 'bk')]
    pins = {}
    for m in ('DMA', 'DMB'):
        pins[m] = {}
        for f in ('F01_Main.zip', 'KLGuns.ini'):
            old, new = (m + f + 'old').encode() * 50, (m + f + 'NEW').encode() * 60
            wr(os.path.join(game, 'KLExpansion', 'Maps', m, f), old); wr(os.path.join(stage, m, f), new)
            pins[m][f] = dict(old=hashlib.md5(old).hexdigest(), new=hashlib.md5(new).hexdigest(), size=len(new))
    json.dump(dict(maps=pins), open(os.path.join(stage, 'pins.json'), 'w'))
    L.write_installer(stage)
    rc, o = run('--maps', 'DMA', '--cleanup')
    check(rc == 0 and is_new('DMA') and is_old('DMB') and 'staged files of DMA deleted' in o and not os.path.exists(os.path.join(stage, 'DMA', 'F01_Main.zip'))
          and os.path.isfile(os.path.join(stage, 'DMB', 'F01_Main.zip')) and os.path.isfile(os.path.join(stage, 'pins.json')), 'cleanup: installed map loses its staged files, the others and pins.json stay')
    rc, o = run('--undo', '--maps', 'DMA')
    check(rc == 0 and is_old('DMA') and 'restored DMA' in o, 'undo works with the staged files deleted (pins.json + backup only)')
    rc, o = run('--undo', '--maps', 'DMA', '--dry'); check(rc == 0, 'dry undo without staged files')
    # --link-from: a twin md5 == pinned old becomes the backup as a hard link (0 bytes on the backup drive); a changed twin is ignored (plain copy)
    twin = os.path.join(tmp, 'twin')
    wr(os.path.join(twin, 'DMB', 'F01_Main.zip'), ('DMB' + 'F01_Main.zip' + 'old').encode() * 50)
    wr(os.path.join(twin, 'DMB', 'KLGuns.ini'), b'not the live file')
    rc, o = run('--maps', 'DMB', '--link-from', twin)
    check(rc == 0 and is_new('DMB') and os.stat(os.path.join(bkp, 'DMB', 'F01_Main.zip')).st_ino == os.stat(os.path.join(twin, 'DMB', 'F01_Main.zip')).st_ino
          and os.stat(os.path.join(bkp, 'DMB', 'KLGuns.ini')).st_ino != os.stat(os.path.join(twin, 'DMB', 'KLGuns.ini')).st_ino
          and 'hard link' in o, 'link-from: an md5-equal twin is hard-linked as the backup, a changed twin is not')
    rc, o = run('--undo', '--maps', 'DMB')
    check(rc == 0 and is_old('DMB') and os.path.isfile(os.path.join(twin, 'DMB', 'F01_Main.zip')), 'undo of a linked backup restores the map and keeps the twin')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
L.configure('1106b')

# 1107r game-root ini (KLShopPage.ini re-indexes every pair card): installed only on the run that puts the LAST pinned map on its new files, undone first
L.configure('1107r')
tmp = tempfile.mkdtemp(prefix='pd2gl_')
try:
    stage, game, bkp = [os.path.join(tmp, x) for x in ('stage', 'game', 'bk')]
    pins = {}
    for m in ('DMA', 'DMB'):
        pins[m] = {}
        for f in ('F01_Main.zip', 'KLGuns.ini'):
            old, new = (m + f + 'old').encode() * 50, (m + f + 'NEW').encode() * 60
            wr(os.path.join(game, 'KLExpansion', 'Maps', m, f), old); wr(os.path.join(stage, m, f), new)
            pins[m][f] = dict(old=hashlib.md5(old).hexdigest(), new=hashlib.md5(new).hexdigest(), size=len(new))
    iold, inew = b'[Pairs]\r\nP0=old\r\n', b'[Pairs]\r\nP0=new\r\n'
    wr(os.path.join(game, 'KLShopPage.ini'), iold); wr(os.path.join(stage, 'KLShopPage.ini'), inew)
    root = {'KLShopPage.ini': dict(old=hashlib.md5(iold).hexdigest(), new=hashlib.md5(inew).hexdigest(), size=len(inew))}
    json.dump(dict(maps=pins, root=root), open(os.path.join(stage, 'pins.json'), 'w'))
    L.write_installer(stage)
    ini = lambda: open(os.path.join(game, 'KLShopPage.ini'), 'rb').read()
    rc, o = run('--dry'); check(rc == 0 and ini() == iold and 'game root KLShopPage.ini: old file' in o, 'root dry: reported, nothing written')
    rc, o = run('--maps', 'DMA', '--cleanup')
    check(rc == 0 and is_new('DMA') and is_old('DMB') and ini() == iold and 'NOT installed yet' in o and 'DMB' in o.split('NOT installed yet')[1], 'root: a partial run leaves the ini old and names the maps left')
    check(os.path.isfile(os.path.join(stage, 'KLShopPage.ini')), 'root: --cleanup keeps the staged root ini')
    rc, o = run('--maps', 'DMB')
    check(rc == 0 and is_new('DMB') and ini() == inew and open(os.path.join(bkp, '_root', 'KLShopPage.ini'), 'rb').read() == iold, 'root: the run completing the set installs the ini, backup = old')
    rc, o = run('--maps', 'DMB'); check(ini() == inew and 'installed game root' not in o, 'root: a re-run does not touch the installed ini')
    rc, o = run('--undo', '--maps', 'DMB')
    check(rc == 0 and ini() == iold and is_old('DMB') and is_new('DMA') and not os.path.exists(os.path.join(bkp, '_root')), 'root: any undo restores the ini first, its backup goes')
    wr(os.path.join(game, 'KLShopPage.ini'), b'edited by hand')
    rc, o = run('--maps', 'DMB'); check(rc != 0 and 'changed since staging' in o and is_old('DMB'), 'root: a drifted ini refuses the whole run, no map touched')
    wr(os.path.join(game, 'KLShopPage.ini'), iold)
    rc, o = run('--maps', 'DMB', '--fail-after', '1'); check(rc != 0 and is_old('DMB') and ini() == iold, 'root: a failed map leaves the ini old')
    rc, o = run('--maps', 'DMB'); check(rc == 0 and ini() == inew, 'root: installs after the failed run')
    rc, o = run('--undo'); check(rc == 0 and ini() == iold and is_old('DMA') and is_old('DMB'), 'root: full undo')
    # review 11-07: a drifted ini does not block the maps' undo; a missing live map file gives a NOTE, not a traceback
    for f in pins['DMA']:          # DMA's staged files went with --cleanup above: stage them again
        wr(os.path.join(stage, 'DMA', f), (('DMA' + f + 'NEW').encode()) * 60)
    rc, o = run(); check(rc == 0 and ini() == inew and is_new('DMA') and is_new('DMB'), 'root: reinstall all')
    wr(os.path.join(game, 'KLShopPage.ini'), b'edited by hand')
    rc, o = run('--undo'); check(rc == 0 and is_old('DMA') and is_old('DMB') and ini() == b'edited by hand' and 'left alone' in o, 'root: drifted ini left alone, maps still undone')
    wr(os.path.join(game, 'KLShopPage.ini'), iold); shutil.rmtree(os.path.join(bkp, '_root'), ignore_errors=True)
    os.remove(os.path.join(game, 'KLExpansion', 'Maps', 'DMB', 'KLGuns.ini'))
    rc, o = run('--maps', 'DMA'); check(rc == 0 and is_new('DMA') and ini() == iold and 'NOT installed yet' in o and 'Traceback' not in o, 'root: a missing live map file -> NOTE, no traceback')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
# review 11-07: pin() after the install (live ini == staged) or without the staged ini keeps the recorded root entry
import kl_shop_pics as P
tmp = tempfile.mkdtemp(prefix='pd2gl_')
dd0 = P.DD
try:
    P.DD = os.path.join(tmp, 'dd'); out = os.path.join(tmp, 'out')
    wr(os.path.join(P.DD, 'KLShopPage.ini'), b'old ini'); wr(os.path.join(out, 'KLShopPage.ini'), b'new ini')
    rt = lambda: json.load(open(os.path.join(out, 'pins.json')))['root']
    L.pin(out, [], log=lambda s: None); r1 = rt()
    check(r1['KLShopPage.ini']['old'] == hashlib.md5(b'old ini').hexdigest() and r1['KLShopPage.ini']['new'] == hashlib.md5(b'new ini').hexdigest(), 'pin: root entry old/new')
    wr(os.path.join(P.DD, 'KLShopPage.ini'), b'new ini'); L.pin(out, [], log=lambda s: None)
    check(rt() == r1, 'pin: a re-pin after the install keeps the root entry')
    os.remove(os.path.join(out, 'KLShopPage.ini')); L.pin(out, [], log=lambda s: None)
    check(rt() == r1, 'pin: a re-pin without the staged ini keeps the root entry')
finally:
    P.DD = dd0
    shutil.rmtree(tmp, ignore_errors=True)
L.configure('1106b')

print('pd2_guns_layer_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
