#!/usr/bin/env python3
"""
kl_fa_rope.py - the SOUNDS of the climb and the rope for a finished build folder (agent rope, 2026-10-16). OFFLINE.

    python kl_fa_rope.py <build folder> <new folder>
    then: python kl_fa_climb.py apply <new folder> <final folder> --players-only --no-edges   (maps without the climb clips)

1. Dead Men's five climb sequences (M03_FA_A's bank, the source of kl_fa_climb's clips: up_high, up_high_no_weapon, sprint_low,
   sprint_low_no_weapon, sprint_low_pistol = Hand_On_Wall_01/02 + the default footsteps) are appended to the level's .SND by
   kl_snd.merge (6 in-memory records, 14 KB; .WHD / .WAV / _LS.SND rewritten beside the archive). kl_fa_climb.merge(snd=...) then
   keeps every added clip's +0x2C BY NAME (it cleared them before: 'the climb has no foley sound'). Climb clips a build already
   has (+0x2C 0) are given the same records here.
2. Where the .ANM has Dog Days L07's rappel clips (Retomoto, kl_fa_rappel.py build), L07's three rappel sequences are carried too
   (SFX/Animations/Level_Specific/L07/Rappel_01.wav, the sound L07 plays with that very clip) and the clips' +0x2C point at them.
Clip record +0x2C = an offset into the level's own .SND (luvsic; kl_anm.snd_name): played when a player clip starts (ZPlayer
vt+0x620 -> 0x5c8050, READ by luvsic). NOT SEEN LIVE for a clip played by a mini cut or by klfreeclimb's vault action.
"""
import sys, os, shutil, zipfile, struct, collections, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_anm, kl_anmjoin, kl_graft
if len(sys.argv) != 3:
    print(__doc__); sys.exit(2)
src, dst = sys.argv[1], sys.argv[2]
assert not (os.path.isdir(dst) and os.listdir(dst))
zp = [os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith('_main.zip')][0]
stem = os.path.basename(zp)[:-4]
z = zipfile.ZipFile(zp); order = z.namelist(); files = {n: z.read(n) for n in order}
sndn = [n for n in order if n.lower().endswith('.snd') and '_LS' not in n.upper()][0]
anmn = [n for n in order if n.lower().endswith('.anm')][0]
rd = lambda p: open(p, 'rb').read()
ls = rd(os.path.join(src, stem + '_LS.SND'))
whd, wav = rd(os.path.join(src, stem + '.WHD')), rd(os.path.join(src, stem + '.WAV'))
base = kl_snd.Snd('dd', files[sndn], ls).walk()
T0 = base.T
log = []
def say(s): print(s); log.append(s)
CLIMB = [b'audio:animation/resources/movement/soldier/climb/' + x + b'#seq' for x in
         (b'up_high', b'up_high_no_weapon', b'sprint_low', b'sprint_low_no_weapon', b'sprint_low_pistol')]
RAPPEL = [b'audio:animation/resources/level_specific/l07/rappel/l07_repelling_enimies_repelling_0%d#seq' % i for i in (1, 2, 3)]
snd = files[sndn]
has_rp = b'Repilling_01' in files[anmn]
if not has_rp: RAPPEL = []
for lvl, game, names in (('M03_FA_A', 'dm', CLIMB), ('L07', 'dd', RAPPEL)):
    if not names: continue
    s = kl_snd.bank(lvl, game)
    roots = [o for o, t in s.kind.items() if t == 3 and s.name(o) in names]
    assert len(roots) == len(names), (lvl, len(roots))
    b = kl_snd.Snd('dd', snd, ls).walk()
    st = collections.Counter()
    snd2, whd, wav, omap = kl_snd.merge(b, s, whd, wav, kl_snd.read(kl_snd.beside(lvl, '.WHD', game)), kl_snd.read(kl_snd.beside(lvl, '.WAV', game)),
                                        roots, strmap={}, log=say, stats=st)
    say('%s: %d seqs -> %s; %s' % (lvl, len(roots), [hex(omap.get(r, 0)) for r in roots], dict(st)))
    assert all(omap.get(r) for r in roots)
    ls = kl_snd.ls_bank(ls, struct.unpack_from('<I', snd2, 0)[0])
    prob, n = kl_snd.verify(b, snd2, whd, wav, ls, omap)
    assert not prob, prob
    snd = snd2
idx = kl_anm.snd_index(snd)
for nm in CLIMB + RAPPEL: assert nm in idx, nm
# the rappel clips already in the build's .ANM: +0x2C by name
a = kl_anm.Anm(files[anmn])
fixed = []
for i, n in enumerate(a.names):
    for k, tag in ((1, 'Repilling_01'), (2, 'Repelling_02'), (3, 'Repelling_03')):
        if n.endswith('#' + tag):
            v = idx[RAPPEL[k - 1]]
            if struct.unpack_from('<I', a.clips[i], 0x2c)[0] != v:
                c = bytearray(a.clips[i]); struct.pack_into('<I', c, 0x2c, v); a.clips[i] = bytes(c) if isinstance(a.clips[i], bytes) else c
                fixed.append((n, hex(v)))
say('rappel clips +0x2C: %s' % fixed)
srcA = kl_anm.Anm(kl_anmjoin.stock_anm('M03_FA_A', 'dm')); srcS = kl_anmjoin.stock_snd('M03_FA_A', 'dm')
want = {}
for i, n in enumerate(srcA.names):
    if n.startswith('anim:Movement/Soldier/Climb#') and not n.endswith('_NPC'):
        v = struct.unpack_from('<I', srcA.clips[i], 0x2c)[0]
        nm = kl_anm.snd_name(srcS, v) if v else None
        if nm in idx: want[n] = idx[nm]
cl = []
for i, n in enumerate(a.names):
    if n in want and struct.unpack_from('<I', a.clips[i], 0x2c)[0] == 0:
        c = bytearray(a.clips[i]); struct.pack_into('<I', c, 0x2c, want[n]); a.clips[i] = bytes(c) if isinstance(a.clips[i], bytes) else c
        cl.append(n.split('#')[1])
say('climb clips already in the .ANM given their Dead Men foley: %s' % cl)
new_anm = a.save()
bad = kl_anm.clip_snd_bad(kl_anm.Anm(new_anm, 'dd'), snd)
assert not bad, bad[:3]
files[anmn], files[sndn] = new_anm, snd
os.makedirs(dst, exist_ok=True)
kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
for f in os.listdir(src):
    p = os.path.join(src, f)
    if os.path.isfile(p) and p != zp:
        shutil.copyfile(p, os.path.join(dst, f))
open(os.path.join(dst, stem + '.WHD'), 'wb').write(whd)
open(os.path.join(dst, stem + '.WAV'), 'wb').write(wav)
open(os.path.join(dst, stem + '_LS.SND'), 'wb').write(ls)
say('bank T %#x -> %#x; .WHD %d .WAV %d' % (T0, struct.unpack_from('<I', snd, 0)[0], len(whd), len(wav)))
open(os.path.join(dst, 'rope_snd.txt'), 'w').write('\n'.join(log) + '\n')
