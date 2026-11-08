#!/usr/bin/env python3
"""kl_fallback_guns_test.py - off-game checks of tools/kl_fallback_guns.py (the no-PD2 Page II set made of Dead Men guns): the SPECS_FALLBACK table (no heli, own class,
items = the live [Pairs]), the pure helpers (LOD detail, report check, restore plan, KLShopPage.ini text) on small synthetic cases, and, ONLY when a bake-set output exists
(C:\\kl_build_1024\\nopd2_spike\\out_set), its report.json / KLShopPage.ini / zip pin. No game file is written; the live KLShopPage.ini is only read (skipped when absent)."""
import hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fallback_guns as F
import pd2_guns_multi as M

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


# ---- the table
check(F.table_problems() == [], 'table_problems: %s' % F.table_problems())
S = F.SPECS_FALLBACK
check([s['pair'] for s in S] == list(range(len(S))) and len(S) == 13, '13 pairs in order')
check(len({s['item'] for s in S}) == 13, 'one pair per item')
check(all(s['item'] in M.POOL_ITEMS for s in S), 'every item is in POOL_ITEMS')
check(not any(s['item'] in (42, 43, 44, 45, 46, 48, 51) for s in S), 'no heli item')
check(not any(M.HELI_RE.search(s['host']) for s in S), 'no heli / hind / player host template')
for s in S:
    hc = {M.spec_class(x) for x in M.SPECS if x['item'] == s['item'] and x['template'] == s['host']}
    check(hc == {s['cls']}, 'item %d host %s class %s == %s' % (s['item'], s['host'], hc, s['cls']))
    check(s['dm'] is None or F.DM_CLASS.get(s['dm']) == s['cls'], 'item %d DM %s is the pair class' % (s['item'], s['dm']))
    check(s['dm'] is not None or bool(s['why']), 'item %d: a stock pair says why' % s['item'])
    check(s['cls'] in F.CLASS_RULES, 'item %d: class %s has a rule' % (s['item'], s['cls']))
check(all(r['hold'] in ('house', 'same') for r in F.CLASS_RULES.values()), 'class rules name a hold')
check(F.CLASS_RULES['grenade']['hold'] == 'same' and F.CLASS_RULES['rocket']['hold'] == 'same', 'launchers only build on the host\'s own space')
check(sum(1 for s in S if s['dm']) == 11 and [s['item'] for s in S if not s['dm']] == [63, 41], 'dm / stock split (11 / items 63 41)')
check([s['name'] for s in S if s['dm']] == ['USP', 'HK69 FLARE', 'HK69 GAS', 'HK69', 'RPG-7', 'PKM', 'MINIMI', 'SG 552', 'M4A1', 'AK-74', 'REM 700'], 'display names')
# an invalid table is caught: a heli host, a class mismatch
_keep = [dict(s) for s in S]
S[0]['host'] = 'MG_GP_Type88_L09_Heli'
check(any('heli' in b for b in F.table_problems()), 'a heli host is refused')
S[0].update(_keep[0]); S[1]['cls'] = 'mg'
check(any('class' in b for b in F.table_problems()), 'a class mismatch is refused')
S[1].update(_keep[1])
check(F.table_problems() == [], 'table restored after the negative checks')

# ---- the live structure (read only)
LIVE = F.LIVE_INI
if os.path.isfile(LIVE):
    txt = open(LIVE, encoding='latin-1').read()
    live_items = [int(m.group(1)) for m in re.finditer(r'(?m)^P\d+=\d+\|(\d+)\|', txt)]
    check(live_items == [s['item'] for s in S], 'items = the live [Pairs] items %s' % live_items)
    modes = {s['item']: ('dm' if s['dm'] else 'stock') for s in S}
    new = F.shop_ini_text(txt, S, modes)
    new_items = [int(m.group(1)) for m in re.finditer(r'(?m)^P\d+=\d+\|(\d+)\|', new)]
    check(new_items == live_items, 'shop_ini_text keeps items and order')
    check([re.match(r'P\d+=(\d+)\|\d+\|(\d+)\|', l).groups() for l in new.split('\r\n') if re.match(r'P\d+=', l)] ==
          [re.match(r'P\d+=(\d+)\|\d+\|(\d+)\|', l).groups() for l in txt.split('\n') if re.match(r'P\d+=', l)], 'rows and picture rows unchanged')
    check('Payday' not in new, 'no Payday 2 text left in the set')
else:
    print('  (live KLShopPage.ini not found: live-structure checks skipped)')

# ---- shop_ini_text on a synthetic ini
SYN = ('; header\r\n[Pairs]\r\nCount=3\r\nP0=0|62|0|CHIMANO 88 SHIELD\r\nP1=10|63|2|BERNETTI 9 SHIELD\r\nP2=28|33|30|AK.762\r\n[Desc]\r\n'
       'D0=Police reg.: 2062-II62\\nHand gun. Payday 2 sidearm. Page II: sold in the M-77B row, same price, same rank.\r\n'
       'D1=Police reg.: 2063-II63\\nHand gun. Payday 2 sidearm. Page II: sold in the TAURUS JUDGE row, same price, same rank.\r\n'
       'D2=Police reg.: 2033-II33\\nAssault rifle. Payday 2 rifle. Page II: sold in the ZASTAVA M85 row, same price, same rank.\r\n')
t = F.shop_ini_text(SYN, S, {62: 'dm', 63: 'stock', 33: 'dm'})
check('P0=0|62|0|USP' in t and 'P2=28|33|30|SG 552' in t, 'dm names on dm pairs')
check('P1=10|63|2|M9 SHIELD' in t, 'the stock name on a stock pair (kl_shop_sets.ITEMS)')
check('Name=dm' in t and '[Set]' in t and 'ignores [Set]' in t, '[Set] Name=dm with the comment')
check('sold in the M-77B row, same price, same rank.' in t and 'sold in the TAURUS JUDGE row' in t, 'the sold-in row text is kept')
check('Payday' not in t, 'no Payday text in a dm / stock ini')
check(t.count('\\n') == 3 and 'Police reg.: 2062-II62\\nHand gun. Dead Men gun: the USP' in t, 'description: literal \\n, Dead Men text')
check('Origin: Italian' in t, 'a stock pair gets the stock description')

# ---- lod_detail (pure) on a fake chunk store
class FakeP:
    def __init__(self, details):
        self.chunks = {i: bytes(0x0e) + bytes([d]) + bytes(49) for i, d in enumerate(details)}


p = FakeP([255, 3, 252, 1, 14])
check(F.lod_detail(p, [0], 31, True) == {0: 239}, 'the box bit 16 is dropped when the host keeps its box')
check(F.lod_detail(p, [0], 31, False) == {0: 255}, 'the box bit stays when the host has none')
d = F.lod_detail(p, [1, 3], 15, True)
check(d == {1: 3 | 12, 3: 1 | 12}, 'a missing LOD bit is added to the full-detail part: %s' % d)
d = F.lod_detail(p, [1, 2], 31, True)
check(d[1] == 3 | 0 and d[2] == 252 & 0xEF, 'covered LODs add nothing: %s' % d)
d = F.lod_detail(p, [4], 3, True)
check(d == {4: 14 | 1}, 'a part with no bit 1 takes the missing bit when it is the only part: %s' % d)

# ---- report_problems / restore_plan
good = dict(base='stock', source_md5='0' * 32, guns={'DM33': dict(template='Rifle_Type81', previous_root=4623, root=39200, item=33)},
            pairs=[dict(pair=9, item=33, mode='dm', template='Rifle_Type81'), dict(pair=8, item=41, mode='stock', template='MG_GP_Type88_L09_NPC', reason='x')])
check(F.report_problems(good) == [], 'a good report: %s' % F.report_problems(good))
check(any('classified' in b for b in F.report_problems(dict(good, base=None))), 'an unclassified base is refused')
check(any('md5' in b for b in F.report_problems(dict(good, source_md5=None))), 'an unpinned source is refused')
g2 = json.loads(json.dumps(good)); del g2['guns']['DM33']['previous_root']
check(any('previous_root' in b for b in F.report_problems(g2)), 'a baked gun without previous_root is refused')
g3 = json.loads(json.dumps(good)); g3['pairs'][1]['reason'] = ''
check(any('reason' in b for b in F.report_problems(g3)), 'a stock pair without a reason is refused')
g4 = json.loads(json.dumps(good)); g4['pairs'][0]['template'] = 'Other'
check(any('no baked gun' in b for b in F.report_problems(g4)), 'a dm pair without a baked gun is refused')
check(F.restore_plan(good) == [('Rifle_Type81', 4623, 39200)], 'restore_plan: template, previous root, baked root')
try:
    F.restore_plan(g2); check(False, 'restore_plan needs previous_root')
except ValueError:
    check(True, 'restore_plan refuses a report without previous_root')

# ---- same-space / refuse (no .prm needed: the Refuse path of an unknown class)
try:
    F.place(None, 1, 'x', 'y', 0, 'tank'); check(False, 'unknown class refused')
except F.Refuse as e:
    check('no rule' in str(e), 'an unknown class is refused before anything is read')

# ---- shop ini: the same-model mode keeps the DM name, a pair absent from `modes` is stock
t = F.shop_ini_text(SYN, S, {62: 'stock-same-model', 33: 'dm'})
check('P0=0|62|0|USP' in t and 'Dog Days already ships this very model' in t, 'stock-same-model shows the DM name and says so')
check('P1=10|63|2|M9 SHIELD' in t, 'an item missing from modes is stock (one-pair bake)')
check('Looks=62:same:HG_HK_USP_01,33:dm:Rifle_SG552_01' in t.replace('\r\n', '\n'), 'Looks lists same: and dm:')

# ---- guard_fit (strict guards, pure)
okfit = dict(grip=1.0, hand=[0.5, 0.5], hand_len=0.7, mag=[1.0, 0.0], mag_len=1.0, base={})
check(F.guard_fit(okfit, 'rifle') is None, 'a good fit passes')
check('grip gap' in (F.guard_fit(dict(okfit, grip=F.GRIP_MAX + 0.1), 'rifle') or ''), 'grip over the limit is refused')
check('support hand' in (F.guard_fit(dict(okfit, hand_len=F.HAND_MAX + 0.1), 'rifle') or ''), 'hand over the limit is refused')
check(F.HAND_MAX <= 4.0 and F.GRIP_MAX <= 3.0 and F.MAG_MAX <= 4.0, 'strict guard values (no looser global hand limit)')
check('magazine' in (F.guard_fit(dict(okfit, mag_len=F.MAG_MAX + 0.1), 'rifle') or ''), 'magazine over the limit is refused')
check(F.guard_fit(dict(okfit, mag=None, mag_len=None), 'rifle') is None, 'no clip bone on a side: the magazine guard does not apply')
check('two-handed' in (F.guard_fit(dict(okfit, hand=None, hand_len=None), 'rifle') or ''), 'a two-handed class with no hand measurement is refused')
check(F.guard_fit(dict(okfit, hand=None, hand_len=None), 'pistol') is None, 'a pistol is exempt from the support hand')
check('too few' in (F.guard_fit(dict(okfit, grip=None), 'pistol') or ''), 'no grip measurement is refused')

# ---- fit_hold / hold_eval on synthetic shapes (numpy)
import math
import kl_map_guns as MG


def _inv(shift, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda q: (c * (q[0] - shift[0]) + s * (q[1] - shift[1]), -s * (q[0] - shift[0]) + c * (q[1] - shift[1]), q[2] - shift[2])


def synth(dx=0.0, dy=0.0, clip_dx=0.0):
    """host in Dog Days space; look = the host seen through house() backwards (so house(look) == host), then moved by (dx, dy)."""
    inv = _inv(MG.HOUSE_SHIFT, MG.HOUSE_DEG)
    grid = [(x * 1.0, y * 1.0, z * 1.0) for x in range(-3, 18) for y in range(-10, 8) for z in (-1, 0, 1)]
    clip = [(10.0 + i * 0.5, -6.0 + j * 0.5, 0.0) for i in range(6) for j in range(10)]
    lh = [0.0] * 9 + [40.0, 0.3, 0.4]
    q = inv((lh[9] - MG.LHAND_CONV[0], lh[10] - MG.LHAND_CONV[1], 0.0))
    host = dict(bones={'l hand attacher': lh}, parts=[('w_bone_body', grid), ('w_bone_clip', clip)])
    look = dict(bones={'l hand attacher': [0.0] * 9 + [q[0] + dx, q[1] + dy, q[2]]},
                parts=[('w_bone_body', [(inv(v)[0] + dx, inv(v)[1] + dy, inv(v)[2]) for v in grid]),
                       ('w_bone_clip', [(inv(v)[0] + dx + clip_dx, inv(v)[1] + dy, inv(v)[2]) for v in clip])])
    return look, host


lk, ho = synth()
ctx = F.HoldCtx(lk, ho)
e0 = F.hold_eval(ctx, MG.HOUSE_SHIFT, MG.HOUSE_DEG)
check(e0['grip'] is not None and e0['grip'] < 0.05 and math.hypot(*e0['hand']) < 0.05 and e0['mag'] is not None and math.hypot(*e0['mag']) < 0.05, 'hold_eval: the identity case has zero residuals %s' % e0)
m = MG.measure(lk, ho, 'dm')
check(abs(m['grip'][1] - e0['grip']) < 1e-6 and abs(m['hand'][1][0] - e0['hand'][0]) < 1e-6 and abs(m['mag'][0] - e0['mag'][0]) < 1e-6, 'hold_eval = kl_map_guns.measure at the house hold (grip, hand, mag)')
lk2, ho2 = synth(dx=1.5, dy=-2.0)
b = F.hold_eval(F.HoldCtx(lk2, ho2), MG.HOUSE_SHIFT, MG.HOUSE_DEG)
ft = F.fit_hold(lk2, ho2)
check(ft['cost'] < b['cost'] * 0.5 and ft['base']['cost'] > 1.0, 'fit_hold lowers the cost of a displaced gun (%.2f -> %.2f)' % (ft['base']['cost'], ft['cost']))
check(abs(ft['shift'][0] - (MG.HOUSE_SHIFT[0] - 1.5)) < 0.6 and abs(ft['shift'][1] - (MG.HOUSE_SHIFT[1] + 2.0)) < 0.6, 'fit_hold recovers the displacement %s' % ft['shift'])
check(abs(ft['shift'][0] - MG.HOUSE_SHIFT[0]) <= F.FIT_SHIFT_MAX + 1e-9 and abs(ft['deg'] - MG.HOUSE_DEG) <= F.FIT_DEG_MAX + 1e-9, 'fit_hold stays inside its bounds')
lk3, ho3 = synth(dx=30.0, dy=0.0)
ft3 = F.fit_hold(lk3, ho3)
check(F.guard_fit(ft3, 'rifle') is not None, 'a gun 30 cm off cannot be fitted inside the strict guards (%s)' % F.guard_fit(ft3, 'rifle'))
lk4, ho4 = synth(clip_dx=9.0)
ft4 = F.fit_hold(lk4, ho4)
check(ft4['mag_len'] is not None and ft4['mag_len'] > 0.5, 'the magazine offset is measured and recorded (%.1f cm)' % (ft4['mag_len'] or -1))
check({'shift', 'deg', 'grip', 'hand', 'hand_len', 'mag', 'mag_len', 'cost', 'base', 'evals'} <= set(ft), 'fit record has shift, turn, the residuals and the house baseline')

# ---- pinned fit, extent guard, turn tie-break
hs, hd = MG.HOUSE_SHIFT, MG.HOUSE_DEG
check(F.pinned_axis(dict(shift=list(hs), deg=hd)) is None, 'pinned_axis: the house hold is not pinned')
check(F.pinned_axis(dict(shift=[hs[0] + F.FIT_SHIFT_MAX, hs[1], hs[2]], deg=hd)) == 'shift x', 'pinned_axis: x on its bound')
check(F.pinned_axis(dict(shift=[hs[0], hs[1] - F.FIT_SHIFT_MAX + 0.0005, hs[2]], deg=hd)) == 'shift y', 'pinned_axis: y within 1e-3 of its bound')
check(F.pinned_axis(dict(shift=[hs[0], hs[1], hs[2] - F.FIT_Z_MAX], deg=hd)) == 'shift z', 'pinned_axis: z on its bound')
check(F.pinned_axis(dict(shift=list(hs), deg=hd + F.FIT_DEG_MAX)) == 'turn', 'pinned_axis: turn on its bound')
check(F.pinned_axis(dict(shift=[hs[0] + F.FIT_SHIFT_MAX - 0.01, hs[1], hs[2]], deg=hd)) is None, 'pinned_axis: 0.01 inside the bound is free')
check('pinned to bound turn' in (F.guard_fit(dict(okfit, shift=list(hs), deg=hd - F.FIT_DEG_MAX), 'rifle') or ''), 'guard_fit refuses a fit pinned to a bound')
check(F.guard_fit(dict(okfit, shift=list(hs), deg=hd), 'rifle') is None, 'guard_fit passes an interior fit')
okext = dict(rear=1.0, front=-2.0, below=3.0, box=4.0)
check(F.extent_problem(okext) is None, 'extent: a fit inside the limits passes')
check('rear' in (F.extent_problem(dict(okext, rear=F.EXT_REAR_MAX + 0.1)) or ''), 'extent: rear overhang refused')
check('muzzle' in (F.extent_problem(dict(okext, front=F.EXT_FRONT_MAX + 0.1)) or '') and 'muzzle' in (F.extent_problem(dict(okext, front=-F.EXT_FRONT_MAX - 0.1)) or ''), 'extent: muzzle off either way refused')
check('below' in (F.extent_problem(dict(okext, below=F.EXT_BELOW_MAX + 0.1)) or ''), 'extent: geometry below the host refused')
check('root box' in (F.extent_problem(dict(okext, box=F.EXT_BOX_MAX + 0.1)) or ''), 'extent: root-box overhang refused')
check('rear' in (F.guard_fit(dict(okfit, extent=dict(okext, rear=9.0)), 'rifle') or ''), 'guard_fit applies the extent guard')
lkx, hox = synth()
ex = F.extent_of(lkx, hox, MG.HOUSE_SHIFT, MG.HOUSE_DEG)
check(max(abs(ex['rear']), abs(ex['front']), abs(ex['below'])) < 0.05, 'extent_of: the identity case overhangs nothing %s' % ex)
ex2 = F.extent_of(lkx, hox, (MG.HOUSE_SHIFT[0] - 5.0, MG.HOUSE_SHIFT[1], MG.HOUSE_SHIFT[2]), MG.HOUSE_DEG)
check(abs(ex2['rear'] - 5.0) < 0.05 and abs(ex2['front'] + 5.0) < 0.05, 'extent_of: a 5 cm shift back is rear +5 front -5 %s' % ex2)
check(ft['extent'] is not None and 'turn_penalty' in ft, 'fit record carries extent and turn_penalty')
ftf = F.fit_hold(lkx, hox)
check(abs(ftf['deg'] - MG.HOUSE_DEG) <= 0.3, 'tie-break: a perfect-at-house gun settles at the house turn (%.3f)' % ftf['deg'])
# a flat valley (no sensitivity to the turn: two points of grip) still lands near the house turn
check(F.TURN_PENALTY > 0 and F.TURN_PENALTY <= 0.25, 'the turn penalty is light')

# ---- ini_problems on a synthetic out
SP4 = os.path.join(os.path.dirname(F.OUT_DEFAULT), 'test_tmp4')
shutil.rmtree(SP4, ignore_errors=True)
os.makedirs(os.path.join(SP4, 'MAP'))
json.dump(dict(pairs=[dict(item=62, mode='dm'), dict(item=63, mode='stock'), dict(item=52, mode='stock-same-model')]), open(os.path.join(SP4, 'MAP', 'report.json'), 'w'))
check(any('missing' in b for b in F.ini_problems(SP4, ['MAP'])), 'ini_problems: a missing ini is a problem')
open(os.path.join(SP4, 'KLShopPage.ini'), 'w').write(SYN.replace('P2=28|33|30|AK.762', 'P2=28|52|30|HK69').replace('CHIMANO 88 SHIELD', 'USP'))
b4 = F.ini_problems(SP4, ['MAP'])
check(any('item 63' in b for b in b4) and not any('item 62' in b for b in b4), 'ini_problems: a wrong stock name is caught, a dm name passes: %s' % b4)
open(os.path.join(SP4, 'KLShopPage.ini'), 'w').write(SYN.replace('CHIMANO 88 SHIELD', 'WRONG'))
check(any('item 62' in b for b in F.ini_problems(SP4, ['MAP'])), 'ini_problems: a dm item with another name is caught')
shutil.rmtree(SP4, ignore_errors=True)

# ---- out_conflicts / restore inside staged / rounds=0
SP2 = r'C:\kl_build_1024\nopd2_spike\test_tmp2'
shutil.rmtree(SP2, ignore_errors=True)
os.makedirs(os.path.join(SP2, 'OLD'))
json.dump(dict(pairs=[dict(item=33, mode='dm'), dict(item=62, mode='stock')]), open(os.path.join(SP2, 'OLD', 'report.json'), 'w'))
try:
    F.out_conflicts(SP2, ['NEW'], {33: 'stock', 62: 'stock'}); check(False, 'out_conflicts must refuse differing modes')
except F.Unsafe as e:
    check('fresh out' in str(e) and 'OLD' in str(e), 'out_conflicts refuses an out whose other map has other modes')
check(F.out_conflicts(SP2, ['NEW'], {33: 'dm', 62: 'stock'}) is None, 'out_conflicts: same modes is fine')
check(F.out_conflicts(SP2, ['OLD'], {33: 'stock'}) is None, 'out_conflicts: the maps of this run are replaced, not compared')
shutil.rmtree(SP2, ignore_errors=True)
try:
    F.bake_maps(['DD05'], r'C:\kl_build_1024\nopd2_spike\test_tmp3', rounds=0); check(False, 'rounds=0 must be refused')
except ValueError:
    check(True, 'bake_maps rounds=0 is a ValueError (not a NameError)')
shutil.rmtree(r'C:\kl_build_1024\nopd2_spike\test_tmp3', ignore_errors=True)

# ---- mesh_signature / same_mesh on a fake prm (monkeypatched kl_chars / kl_map_guns readers)
import struct, hashlib
import kl_chars as C


class FakeMesh:
    """object chunk = 64 bytes (detail +0x0e, bone +0x3c); descriptor chunk = nv, vertex chunk index; vertex chunk = nv*40 bytes."""

    def __init__(self):
        self.chunks, self.desc = {}, {}

    def add(self, bone, detail, verts):
        v = len(self.chunks); self.chunks[v] = b''.join(struct.pack('<10f', *x) for x in verts)
        d = v + 1; self.chunks[d] = struct.pack('<II', len(verts), v)
        o = v + 2; c = bytearray(64); c[0x0e] = detail; struct.pack_into('<I', c, 0x3c, bone); self.chunks[o] = bytes(c); self.desc[o] = [d]
        return o

    def u32(self, i, off):
        return struct.unpack_from('<I', self.chunks[i], off)[0]


_keep = (C.skeleton, C.bone_names, C._rest, MG._descriptors)
C.skeleton = lambda p, root: root
C.bone_names = lambda p, sk: ['w_bone_frame', 'w_bone_body', 'w_bone_clip']
C._rest = lambda p, sk: [[float(i)] * 12 for i in range(3)]
MG._descriptors = lambda p, o: p.desc[o]
try:
    fm = FakeMesh()
    va = [tuple(float(i + j) for j in range(10)) for i in range(5)]
    a1, a2 = fm.add(1, 255, va), fm.add(1, 239, va)
    b1 = fm.add(2, 255, va)
    c1 = fm.add(1, 255, va[:-1] + [tuple(9.0 for _ in range(10))])
    check(F.same_mesh(fm, 0, [a1], 0, [a2]), 'same_mesh: equal vertex buffers, bone and detail (box bit 16 ignored)')
    check(not F.same_mesh(fm, 0, [a1], 0, [b1]), 'same_mesh: another bone is another mesh')
    check(not F.same_mesh(fm, 0, [a1], 0, [c1]), 'same_mesh: one changed vertex is another mesh')
    d1 = fm.add(1, 3, va)
    check(not F.same_mesh(fm, 0, [a1], 0, [d1]), 'same_mesh: another LOD detail is another mesh')
    check(not F.same_mesh(fm, 0, [a1], 0, [a1, a2]), 'same_mesh: another part count is another mesh')
finally:
    C.skeleton, C.bone_names, C._rest, MG._descriptors = _keep

# ---- combine_decisions: one mode per pair on every map
pm = {'A': {1: dict(mode='dm', reason=None), 2: dict(mode='stock', reason='x'), 3: dict(mode='stock-same-model', reason='y')},
      'B': {1: dict(mode='stock', reason='hand 5 cm'), 2: dict(mode='stock', reason='x'), 3: dict(mode='stock-same-model', reason='y')}}
cd = F.combine_decisions(pm)
check(cd[1]['mode'] == 'stock' and 'maps disagree' in cd[1]['reason'] and 'A dm' in cd[1]['reason'] and 'B stock' in cd[1]['reason'], 'maps that disagree: stock on all, reason names both')
check(cd[2]['mode'] == 'stock' and cd[3]['mode'] == 'stock-same-model', 'maps that agree keep the mode')
check(F.combine_decisions(pm, {3: 'because'})[3] == dict(mode='stock', reason='because'), 'force makes a pair stock')
check(all(d['mode'] == 'stock' for d in F.combine_decisions({'A': {1: dict(mode='dm', reason=None)}, 'B': {1: dict(mode='stock-same-model', reason='z')}}).values()), 'dm vs same-model disagree: stock')

# ---- report_problems: strict limits, folded count, mismatch, same-model
sm = dict(good, pairs=good['pairs'] + [dict(pair=3, item=52, mode='stock-same-model', template='Launcher_HK69A1_01', reason='same mesh')])
check(F.report_problems(sm) == [], 'stock-same-model with a reason is a good pair: %s' % F.report_problems(sm))
check(any('without a reason' in b for b in F.report_problems(dict(good, pairs=good['pairs'] + [dict(pair=3, item=52, mode='stock-same-model', template='L')]))), 'stock-same-model without a reason is refused')
bg = json.loads(json.dumps(good)); bg['guns']['DM33'].update(same_space=False, folded_bones=0, fit=dict(grip=1.0, hand_len=2.0, mag_len=9.0))
check(any('magazine' in b for b in F.report_problems(bg)), 'a baked gun with a magazine over MAG_MAX is a problem')
bg['guns']['DM33']['fit'] = dict(grip=1.0, hand_len=5.0, mag_len=1.0)
check(any('support hand' in b for b in F.report_problems(bg)), 'a baked gun with a hand over HAND_MAX is a problem')
bg['guns']['DM33'].update(fit=dict(grip=1.0, hand_len=1.0, mag_len=1.0), folded_bones=None)
check(any('folded' in b for b in F.report_problems(bg)), 'a baked gun without a folded-bone count is a problem')
check(any('another mode' in b for b in F.report_problems(dict(good, mismatch=[33]))), 'a residual mismatch is a problem')

# ---- write guards: game folders, KL_PortBackup, dest == staged, report pin
import shutil
check(F.out_problem(os.path.join(F.DD, 'KLExpansion', 'Maps', 'X')) is not None, 'out inside the Dog Days folder is refused')
check(F.out_problem(F.DD) is not None, 'out == the Dog Days folder is refused')
check(F.out_problem(os.path.join(F.DM_DIR, 'x')) is not None, 'out inside the Dead Men folder is refused')
check(F.out_problem(os.path.join(F.DD, 'KL_PortBackup')) is not None and F.out_problem(r'D:\anywhere\KL_PortBackup\x') is not None, 'KL_PortBackup is refused anywhere')
check(F.out_problem(os.path.join(F.DM_DIR, 'KL_PortTools', 'build', 'scratch')) is None, 'the DM KL_PortTools\\build scratch is allowed')
check(F.out_problem(F.OUT_DEFAULT) is None and F.out_problem(r'C:\kl_build_1024\nopd2_spike\other') is None, 'the spike folder is allowed')
for fn, args in ((F.bake_set, ('DD05', os.path.join(F.DD, 'oops'))), (F.bake, ('DD05', os.path.join(F.DD, 'oops'), 33, 'Rifle_Type81', 'Rifle_SG552_01', 'M01_FA_A')),
                 (F.bake_maps, (['DD05'], os.path.join(F.DM_DIR, 'oops'))), (F.write_shop_ini, (os.path.join(F.DD, 'oops'), S, {}))):
    try:
        fn(*args); check(False, '%s into a game folder must be refused' % fn.__name__)
    except F.Unsafe:
        check(True, '%s refuses a game folder out' % fn.__name__)
SPIKE_TMP = r'C:\kl_build_1024\nopd2_spike\test_tmp'
shutil.rmtree(SPIKE_TMP, ignore_errors=True)
stg = os.path.join(SPIKE_TMP, 'staged'); os.makedirs(stg)
open(os.path.join(stg, 'X_Main.zip'), 'wb').write(b'zipbytes')
pin = hashlib.md5(b'zipbytes').hexdigest()
json.dump(dict(slot='X', md5={'X_Main.zip': pin}, guns={}, ini_entries={}), open(os.path.join(stg, 'report.json'), 'w'))
for dest, what in ((stg, 'dest == staged'), (os.path.join(F.DD, 'KLExpansion', 'Maps', 'X'), 'dest in Dog Days'), (r'D:\x\KL_PortBackup\X', 'dest in KL_PortBackup'),
                   (os.path.join(F.DM_DIR, 'y'), 'dest in Dead Men')):
    try:
        F.restore(stg, dest); check(False, 'restore must refuse ' + what)
    except F.Unsafe:
        check(True, 'restore refuses ' + what)
try:
    F.restore(stg, os.path.join(stg, 'sub')); check(False, 'restore must refuse dest inside staged')
except F.Unsafe as e:
    check('inside the staged' in str(e), 'restore refuses dest inside the staged folder')
open(os.path.join(stg, 'X_Main.zip'), 'wb').write(b'tampered')
try:
    F.restore(stg, os.path.join(SPIKE_TMP, 'dest')); check(False, 'restore must refuse a zip that differs from its pin')
except F.Unsafe as e:
    check('md5' in str(e), 'restore refuses a staged zip that differs from the report md5 pin')
check(not os.path.exists(os.path.join(SPIKE_TMP, 'dest')), 'a refused restore wrote nothing')

# ---- bake() (single pair) writes KLShopPage.ini beside the map folder (bake_set stubbed: no game data touched)
_bs = F.bake_set
F.bake_set = lambda name, out, specs, src, base_ok, log, **k: dict(pairs=[dict(pair=0, item=33, mode='dm', template='Rifle_Type81', dm_template='Rifle_SG552_01', reason=None)])
try:
    if os.path.isfile(LIVE):
        F.bake('DD05', os.path.join(SPIKE_TMP, 'one'), 33, 'Rifle_Type81', 'Rifle_SG552_01', 'M01_FA_A', log=lambda *_a: None)
        ipath = os.path.join(SPIKE_TMP, 'one', 'KLShopPage.ini')
        check(os.path.isfile(ipath), 'bake (single pair) writes KLShopPage.ini')
        if os.path.isfile(ipath):
            it = open(ipath, encoding='latin-1').read()
            check('|Rifle_SG552_01' in it, 'single pair ini names the DM gun on its row')
            check('P10=31|35|31|TYPE 88 L09' in it.replace('\r', '') or 'M4A1' not in it.split('[Desc]')[0], 'every other pair of the single-pair ini is stock')
finally:
    F.bake_set = _bs
shutil.rmtree(SPIKE_TMP, ignore_errors=True)

# ---- end to end, only when a bake-set output exists
OUT = F.OUT_DEFAULT
rp = os.path.join(OUT, 'DD05', 'report.json')
if os.path.isfile(rp):
    rep = json.load(open(rp))
    check(F.report_problems(rep) == [], 'out_set report: %s' % F.report_problems(rep))
    check(rep['set'] == 'dm' and rep['base'] in ('stock', 'pd2-restored'), 'out_set base %s' % rep['base'])
    check(len(rep['pairs']) == 13 and [pr['item'] for pr in rep['pairs']] == [s['item'] for s in S], 'out_set pairs = the table items')
    check(all(pr['mode'] == 'stock' for pr in rep['pairs'] if pr['item'] in (63, 41)), 'items 63 and 41 are stock')
    check(not any(M.HELI_RE.search(g['template']) for g in rep['guns'].values()), 'no baked gun on a heli template')
    sm_items = [pr['item'] for pr in rep['pairs'] if pr['mode'] == 'stock-same-model']
    check(set(sm_items) <= {50, 52, 53, 54}, 'only launchers are stock-same-model: %s' % sm_items)
    check(not any(g['item'] in sm_items for g in rep['guns'].values()), 'a same-model pair bakes nothing')
    check(rep['mismatch'] == [], 'no residual mismatch')
    check(all(pr['mode'] in ('dm', 'stock', 'stock-same-model') for pr in rep['pairs']), 'pair modes')
    for k, g in rep['guns'].items():
        fl = g['fit']
        check(g['folded_bones'] is not None, '%s folded-bone count recorded' % k)
        if not g['same_space']:
            check(fl['grip'] <= F.GRIP_MAX and (fl['hand_len'] is None or fl['hand_len'] <= F.HAND_MAX) and (fl['mag_len'] is None or fl['mag_len'] <= F.MAG_MAX),
                  '%s residuals inside the strict guards %s' % (k, fl))
            check(fl['base'] is not None and len(fl['shift']) == 3, '%s fitted shift and house baseline recorded' % k)
    for k, g in rep['guns'].items():
        if not g['same_space']:
            check(F.pinned_axis(g['fit']) is None and F.extent_problem(g['fit']['extent']) is None, '%s not pinned, extent inside the limits %s' % (k, g['fit'].get('extent')))
    check(F.ini_problems(OUT, [n for n in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, n, 'report.json'))]) == [], 'out_set ini names match the modes')
    ev = rep.get('stock_root_evidence') or {}
    if rep['base'] == 'pd2-restored':
        check('Rifle_Type81' in ev and ev['Rifle_Type81']['root_chunk_equal'] and ev['Rifle_Type81']['objects_equal'], 'Rifle_Type81 stock root evidence recorded (pre-PD2 copy)')
        check(all(v['verdict'].startswith('confirmed') or v['verdict'].startswith('GUESS') for v in ev.values()), 'no contradicted stock root')
    zp = os.path.join(OUT, 'DD05', rep['slot'] + '_Main.zip')
    check(os.path.isfile(zp) and F.md5(zp) == rep['md5'][os.path.basename(zp)], 'the staged zip matches its pinned md5')
    check(os.path.getsize(zp) < 600 << 20, 'zip size under 600 MB (%d MB)' % (os.path.getsize(zp) >> 20))
    ip = os.path.join(OUT, 'KLShopPage.ini')
    check(os.path.isfile(ip), 'out_set KLShopPage.ini written')
    if os.path.isfile(ip):
        it = open(ip, encoding='latin-1').read()
        check('Name=dm' in it and 'Payday' not in it, 'out_set ini: Name=dm, no Payday text')
    if os.environ.get('KL_FALLBACK_FULL'):
        check(F.verify(OUT, log=lambda *_a: None), 'out_set verify (KL_FALLBACK_FULL)')
else:
    print('  (no out_set bake: end-to-end checks skipped)')

print('kl_fallback_guns_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
