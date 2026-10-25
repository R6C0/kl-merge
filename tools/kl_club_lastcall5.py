#!/usr/bin/env python3
"""kl_club_lastcall5.py - Last Call (DM05A) pass 1025a: a club of DIFFERENT people, bodyguards inside, a bartender. OFFLINE.

  python tools/kl_club_lastcall5.py build <live F01_Main.zip 858d3371> <out F01_Main.zip> --variant full|lite [--force]
  python tools/kl_club_lastcall5.py check <zip> --variant full|lite
  python tools/kl_club_lastcall5.py stage <live zip> <out folder> --rehearse <scratch> [--variant full,lite] [--no-proc-check]

Builds on the LIVE lastcall4 pack_lite zip (858d3371: 70 civilians, 140 actors / 96 squads). Owner (2026-10-25): "room for more civilians", every
civilian is the same businessman, "more action", more bodyguards inside the club. Reuses kl_club_lastcall3 (roof maker, trim, seal) and kl_chars.put.
  full: 90 civilians (+20, 8 on the upper floor) + 8 bodyguards in 3 squads, the last 18 parked campaign men go -> ~150 actors / 111 squads
  lite: 71 civilians (+1: the bartender)        + 10 bodyguards in 4 squads, 13 parked campaign men go          -> ~138 actors / 95 squads
 1. BODYGUARDS: OldWaves!Guard_G1.. (f3 = 1, Defend rout with Pos# nodes, a Go timer in the AIMonitor START list): make_roof's recipe with its own
    clock. Posts = the posts the campaign designers gave their own guards in this club (identical coordinates in Dead Men's M05_A), snapped to the
    live nav mesh. Which post is bar / booth / stair head was NOT identified (names say only Dance / Surprise / Walkway): GUESS that they are
    sensible club posts. The men are clones of the map's own yakuza (ground) and bodyguard (upper floor) actors, cloned BEFORE the trim.
 2. TRIM: more parked campaign men go (kl_club_lastcall3.trim_pass); gates re-pointed to HunterKillers.
 3. CROWD (full): CR.plan + CV.add; the bartender is placed by hand at Dead Men's Bartender#03 post (-1213, 56, 894), which lies on the live nav mesh.
 4. DANCE: the new civilians dance (KL_Dance4!) except the bartender and a few idle talkers (full: 6) who simply stand.
 5. LOOKS (the point): every civilian gets a look, mixed over the crowd.
      DD models already in the level, no memory: 41803 variants 1-4, 41556 variants 2,3,4,6 (the 'Suitset_Civilians_*' suits). Both 102 bones.
      Dead Men's own club cast, grafted with kl_chars.put (Civilian animation set kept): M05_A 6854 (men, 3 looks), 7265 (woman), 6993 (woman,
      the bartender's model), 7115 (fat man).
GUESSES, said plainly: whether Dead Men's women (skeleton 'Female' in their game) look right under Dog Days' Civilian clips and the Female_Stripper
clip is untested in game; model 41556 on the Civilian set is a guess (same bone table as 41803, never drawn with those clips); the guard posts; the
actor count (full ~150 / 111) is above the stock maximum 148 / 90 only by the squads, memory is the unknown.
"""
import collections
import json
import math
import os
import random
import shutil
import struct
import zipfile
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_club_lastcall3 as L3
import kl_club_dance_1024 as DN
import kl_club_crowd as CR
import kl_fa_civs as CV
import kl_fa_bots as KB
import kl_chars as C
import kl_gms
import kl_prpjoin as J
from kl_prp import units

BS = chr(92)
MD5_LIVE = '858d3371a2f31169dc3b71c08ac4acf2'
MD5_D5F = 'd5f8522bb45c1757e136e999e35d53f5'          # live DM05A after lastcall3b lite + clubmusic: 129 actors / 74 squads, 40 civilians (safe / mid build on it)
SND_MD5 = '498cc81d'
FIRST, SECOND = L3.FIRST, L3.SECOND
REMOVE_LITE = [SECOND + 'Dance#02', FIRST + 'DanceFloor01!On_Dancefloor#02', FIRST + 'DanceFloor02!Dancefloor02a#03', FIRST + 'DanceFloor02!Dancefloor02a#01',
               FIRST + 'DanceFloor02!Dancefloor02a#02', FIRST + 'DanceFloor02!FatBounceronWalkway']          # 13 men / 6 squads
REMOVE_FULL = REMOVE_LITE + [SECOND + 'Dance#01', FIRST + 'Surprise2']                                         # 18 men / 8 squads
BARTENDER = (-1213.0, 56.0, 894.0)                    # Dead Men M05_A AI_Players!Civilians!Bartenders/Bartender#03: on the live nav mesh (measured)
# Posts: where the campaign designers stood their guards (x, y, z) in this club; the live mesh decides the final cell.
POSTS = {'G1': ('yakuza', [(-423, 37, 1355), (-535, 32, 1429)]),
         'G2': ('yakuza', [(1160, 40, 3008), (1256, 40, 3393)]),
         'G3': ('yakuza', [(579, 40, 2554), (889, 40, 2172), (1008, 40, 2148)]),
         'G4': ('bodyguard', [(947, 381, 2740), (634, 371, 2546), (1138, 368, 3066)])}
CENTRE = (0.0, 40.0, 2500.0)
# look: (kind, model or DM source, variant, share). The shares of the non-bartender civilians.
LOOKS = [('dd', 41803, 1, 0.08), ('dd', 41803, 2, 0.06), ('dd', 41803, 3, 0.06), ('dd', 41803, 4, 0.06),
         ('dd', 41556, 2, 0.06), ('dd', 41556, 3, 0.06), ('dd', 41556, 4, 0.06), ('dd', 41556, 6, 0.06),
         ('dm', 6854, 1, 0.07), ('dm', 6854, 2, 0.07), ('dm', 6854, 3, 0.07), ('dm', 7265, 1, 0.16), ('dm', 6993, 1, 0.09), ('dm', 7115, 1, 0.04)]
SEED = 25
# lastcall5safe (2026-10-25): looks sets for the variants pinned on d5f8522b. Cost of the grafted looks measured on d5f8522b with kl_chars.put
# (.TEX growth, MiB; .prm per extra look about +0.5..1.0 MiB, but put also drops ~17 MiB of dead chunks once per build): 6854 men 0.67 for all
# three looks together, 7115 fat man 1.83, 6993 woman 3.58, 7265 woman 6.25. SAFE keeps the cheap ones (6854 x3, bartender 6993), drops 7265 + 7115.
LOOKS_SAFE = [('dd', 41803, 1, 0.09), ('dd', 41803, 2, 0.08), ('dd', 41803, 3, 0.08), ('dd', 41803, 4, 0.08),
              ('dd', 41556, 2, 0.08), ('dd', 41556, 3, 0.08), ('dd', 41556, 4, 0.08), ('dd', 41556, 6, 0.08),
              ('dm', 6854, 1, 0.06), ('dm', 6854, 2, 0.06), ('dm', 6854, 3, 0.06), ('dm', 6993, 1, 0.17)]

VARIANTS = {
    'full': dict(mode='pack', base=MD5_LIVE, tag='.before-1025lastcall5', stem='lastcall5', guards=['G1', 'G3', 'G4'], remove=REMOVE_FULL, add=19, upper=8,
                 idle=6, sep=115.0, spread=0.0, roof='keep', far=600.0, civ_only=True, per=8, dgroup='KL_Dance4!', rout='KLDance4_%02d', doff=23,
                 stagger=0.47, crowd=20, want=90, want_upper=None, men=8, squads=3),
    'lite': dict(mode='pack', base=MD5_LIVE, tag='.before-1025lastcall5', stem='lastcall5', guards=['G1', 'G2', 'G3', 'G4'], remove=REMOVE_LITE, add=0, upper=0,
                 idle=0, sep=115.0, spread=0.0, roof='keep', far=600.0, civ_only=True, per=8, dgroup='KL_Dance4!', rout='KLDance4_%02d', doff=23,
                 stagger=0.47, crowd=1, want=71, want_upper=None, men=10, squads=4),
}
SAFE_BASE = dict(mode='pack', base=MD5_D5F, tag='.before-1025lc5safe', stem='lc5safe', guards=['G1', 'G2', 'G3', 'G4'], remove=REMOVE_LITE, civ_only=True,
                 sep=115.0, spread=0.0, roof='keep', far=600.0, per=8, dgroup='KL_Dance3!', rout='KLDance3_%02d', doff=17, stagger=0.53,
                 men=10, squads=4, min_looks=8)
VARIANTS['safe'] = dict(SAFE_BASE, add=0, upper=0, idle=0, crowd=1, want=41, want_upper=None, looks=LOOKS_SAFE, max_actors=129, max_squads=74)
VARIANTS['mid'] = dict(SAFE_BASE, remove=REMOVE_FULL, add=13, upper=5, idle=3, crowd=14, want=54, want_upper=None, looks=None, max_actors=135, max_squads=85)
for _k, _v in VARIANTS.items():
    L3.VARIANTS[_k if _k in ('safe', 'mid') else 'lc5_' + _k] = _v


def md5(p):
    return L3.md5(p)


# ------------------------------------------------------------------ bodyguards
def guard_plan(src, names, log):
    B = KB.Built(src)
    nav = KB.Nav(B.scene.nav, links=True)
    home = KB.stations(B, nav)['home']
    plan = []
    for n in names:
        kind, posts = POSTS[n]
        men = []
        for p in posts:
            hit = nav.at(p[0], p[1], p[2], 120.0, home)
            cell = (p[0], hit[1], p[2]) if hit else None
            if cell is None or nav.clearance(*cell) < 25.0:
                near = [c for c in nav.around(p, 160.0, home, step=40.0, dy=120.0) if nav.clearance(c[0], c[1], c[2]) >= 25.0]
                near.sort(key=lambda c: math.hypot(c[0] - p[0], c[2] - p[2]))
                cell = near[0][:3] if near else None
            if cell is None:
                log('  guard post %s of %s is off the mesh: dropped' % (p, n))
                continue
            men.append(cell)
        if not men:
            raise ValueError('guard squad %s has no post on the mesh' % n)
        plan.append(dict(name=n, kind=kind, men=men, target=CENTRE if men[0][1] < 200 else (800.0, men[0][1], 2800.0)))
        log('  guard squad %s (%s): %s' % (n, kind, [[round(v) for v in c] for c in men]))
    return plan


# ------------------------------------------------------------------ looks
def civ_actors(sc):
    return [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and sc.names[sc.top[k]].startswith(L3.CIV_PREFIX)]


def assign(paths, n_bar, seed=SEED, looks=None):
    """{actor path: look} - the shares of LOOKS over the non-bartender civilians (largest remainder), shuffled over the crowd."""
    looks = looks or LOOKS
    rng = random.Random(seed)
    rest = list(paths)
    rng.shuffle(rest)
    n = len(rest)
    raw = [s * n for _k, _m, _v, s in looks]
    cnt = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - cnt[i], reverse=True)[:n - sum(cnt)]:
        cnt[i] += 1
    out, i = {}, 0
    for look, c in zip(looks, cnt):
        for _ in range(c):
            out[rest[i]] = look[:3]
            i += 1
    return out


def set_prop(sc, k, name, value):
    lab = J.labels('dd', sc.cls(k))
    node = sc.nodes[k]
    us = [list(u) for u in units(node['props'][1:-1])]
    i = lab.index(name)
    us[i] = [(us[i][0][0], struct.pack('<I', value))]
    node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]


def looks_pass(lv, bartender, log, looks=None):
    """lv: the C.Lv of the finished scene. Returns the report."""
    sc, _raw = lv.scene()
    acts = civ_actors(sc)
    path = {k: sc.path[k].replace('ROOT' + BS, '', 1) for k in acts}
    bar = [k for k in acts if bartender and sc.names[sc.top[k]] == bartender]
    rest = [path[k] for k in acts if k not in bar]
    plan = assign(rest, len(bar), looks=looks)
    for k in bar:
        plan[path[k]] = ('dm', 6993, 1)
    # Dead Men's cast: one pick per (model, variant)
    groups = collections.OrderedDict()
    for p, (kind, m, v) in plan.items():
        if kind == 'dm':
            groups.setdefault((m, v), []).append(p)
    picks = [C.Pick(ps, 'M05_A', str(m), {1: v, 2: v}) for (m, v), ps in groups.items()]
    t0 = len(lv['.TEX'])
    rep = C.put(lv, picks, log=lambda *_: None)
    rep['tex_bytes'] = (t0, len(lv['.TEX']))
    # verifier fix 2026-10-25: C.put merges build/shared/union.fxc (242 entries, 17.8 MB) into the cache; the 13 new materials need none
    # of it (the live 130-entry, 9.2 MB cache already holds every effect they ask for). The cache is read whole into ONE heap block at
    # load (re/open_work_log.md 'five large blocks'), so +8.5 MB there is a crash risk for nothing. slim_cache keeps exactly what the
    # materials ask for (measured: result == the live .fxc byte for byte).
    import kl_light
    lv['.fxc'], frep = kl_light.slim_cache(C.T.read_mat(lv['.MAT']), lv['.fxc'], log=lambda *_: None)
    rep['fxc'] = frep
    # Dog Days' own models/variants: ZGEOM[4] (+ .gms) and ZLNKOBJ[0]
    sc, raw = lv.scene()
    raw = bytearray(raw)
    models = C.gms_models(raw)
    byp = {sc.path[k].replace('ROOT' + BS, '', 1): k for k in range(1, len(sc.nodes))}
    done = collections.Counter()
    for p, (kind, m, v) in plan.items():
        k = byp[p]
        if kind == 'dd':
            struct.pack_into('<I', raw, models[k - 1][0], m)
            set_prop(sc, k, 'ZGEOM[4]', m)
        set_prop(sc, k, 'ZLNKOBJ[0]', v if kind == 'dd' else C.person(sc, k)[1])
        done[(kind, m, v)] += 1
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    rep['looks'] = {'%s %s v%s' % k: n for k, n in sorted(done.items())}
    rep['women'] = sum(n for (kd, m, v), n in done.items() if m in (7265, 6993))
    rep['picks_n'] = len(picks)
    log('  looks: %s' % rep['looks'])
    return rep


# ------------------------------------------------------------------ build
def build_lc5(src, dst, force, log, variant):
    cfg = VARIANTS[variant.replace('lc5_', '')]
    L3.CFG.clear(); L3.CFG.update(cfg)
    h = md5(src)
    if h != cfg['base'] and not force:
        raise SystemExit('refusing: %s md5 %s is not the live DM05A %s (use --force)' % (src, h, cfg['base']))
    W = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc5_work_' + variant)
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(os.path.join(W, 'src'))
    for f in os.listdir(L3.SIBLINGS):
        p_ = os.path.join(L3.SIBLINGS, f)
        if os.path.isfile(p_) and '.before-' not in f and not f.startswith(('audit.', 'civs.')) and not f.endswith(('.bak', '.old', '.zip')):
            shutil.copyfile(p_, os.path.join(W, 'src', f))
    shutil.copyfile(src, os.path.join(W, 'src', 'F01_Main.zip'))
    rep = collections.OrderedDict(source=src, source_md5=h, variant=variant, cfg={k: v for k, v in cfg.items() if k != 'remove'})
    # 1. bodyguards (before the trim: the pools are the campaign men)
    plan = guard_plan(src, cfg['guards'], log)
    L3.CFG['guards'] = plan
    g1 = os.path.join(W, 'g1.zip')
    rep['guards'] = L3.roof_pass(src, g1, False, log)
    L3.CFG['guards'] = None
    # 2. trim
    os.makedirs(os.path.join(W, 'src2'))
    for f in os.listdir(os.path.join(W, 'src')):
        if f != 'F01_Main.zip':
            shutil.copyfile(os.path.join(W, 'src', f), os.path.join(W, 'src2', f))
    rep['trim'] = L3.trim_pass(g1, os.path.join(W, 'src2', 'F01_Main.zip'), cfg['remove'], log)
    # 3. crowd
    B0 = KB.Built(os.path.join(W, 'src2'), 'F01')
    before = {n for _k, _g, n in DN.dancers(B0)}
    civs = []
    if cfg['add']:
        CR.GROUND_SEP = CR.UPPER_SEP = cfg['sep']
        civs, _play = CR.plan(B0, cfg['add'], cfg['upper'], L3.ALERT, L3.SEED)
        log('crowd: %d of %d places found' % (len(civs), cfg['add']))
        if len(civs) < cfg['add']:
            raise ValueError('only %d of %d civilian places' % (len(civs), cfg['add']))
    nav = KB.Nav(B0.scene.nav)
    hit = nav.at(BARTENDER[0], BARTENDER[1], BARTENDER[2], 150.0, None)
    if not hit:
        raise ValueError('the bartender post %s is off the mesh' % (BARTENDER,))
    pos = (BARTENDER[0], hit[1], BARTENDER[2])
    fl = CV.flee_points(nav, pos, 2, away=None, rng=random.Random(5))
    if not fl:                                            # the bar pocket is tighter than F.CLEAR: run from the nearest open cell instead
        open_ = sorted((c for c in nav.around(pos, 600.0, None, step=40.0, dy=150.0) if nav.clearance(c[0], c[1], c[2]) >= CV.F.CLEAR),
                       key=lambda c: math.hypot(c[0] - pos[0], c[2] - pos[2]))
        fl = CV.flee_points(nav, open_[0][:3], 2, away=None, rng=random.Random(5)) if open_ else []
    if not fl:
        raise ValueError('the bartender has nowhere to flee')
    civs.append(dict(pos=pos, face=(0.0, -1.0), flee=fl))
    nci = len(civs)
    CV.add(os.path.join(W, 'src2'), os.path.join(W, 'civ'), civs, 'F01', 'auto', L3.ALERT, True, play=None, log=lambda *_: None)
    fails, _ = CV.check(os.path.join(W, 'civ'), 'F01', play=False)
    if fails:
        raise ValueError('kl_fa_civs.check: %s' % fails[:5])
    mid = os.path.join(W, 'mid.zip')
    L3.CFG.update(civ_only=True)
    rep['civ_pass'] = L3.roof_pass(os.path.join(W, 'civ', 'F01_Main.zip'), mid, False, log)
    # 4. dance (not the bartender, not the idle talkers)
    Bm = KB.Built(mid)
    new = sorted({n for _k, _g, n in DN.dancers(Bm)} - before)
    barname = new[-1]                                     # the bartender was the last civilian added (highest number)
    idle = set(random.Random(SEED).sample(new[:-1], min(cfg['idle'], len(new) - 1))) if cfg['idle'] else set()
    dancing = set(new) - {barname} - idle
    log('dance: %d new civilians, %d dance, bartender %s, idle %s' % (len(new), len(dancing), barname, sorted(idle)))
    d1 = os.path.join(W, 'd1.zip')
    drep = DN.build(mid, d1, per=cfg['per'], force=True, log=log, group=cfg['dgroup'], only=dancing, prefix=cfg['rout'], offset=cfg['doff'], stagger=cfg['stagger']) if dancing else None
    if drep is None:
        shutil.copyfile(mid, d1)
    rep['dance'] = dict(new_civilians=len(new), dancing=len(dancing), idle=sorted(idle), bartender=barname, routs=(drep or {}).get('routs'))
    L3.seal_verify(d1, log)
    # 5. looks
    os.makedirs(os.path.join(W, 'lv'))
    for f in os.listdir(os.path.join(W, 'src')):
        if f != 'F01_Main.zip':
            shutil.copyfile(os.path.join(W, 'src', f), os.path.join(W, 'lv', f))
    shutil.copyfile(d1, os.path.join(W, 'lv', 'F01_Main.zip'))
    lv = C.Lv(os.path.join(W, 'lv'))
    sc0, _ = lv.scene()
    bt = [sc0.names[sc0.top[k]] for k in civ_actors(sc0) if sc0.path[k].split(BS)[-2] == barname]
    rep['looks'] = looks_pass(lv, bt[0] if bt else None, log, cfg.get('looks'))
    out = lv.write(os.path.join(W, 'out'))
    shutil.copyfile(out, dst)
    rep['out_md5'] = md5(dst)
    with open(os.path.splitext(dst)[0] + '.' + cfg['stem'] + '.json', 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    shutil.rmtree(W, ignore_errors=True)
    log('written %s md5 %s' % (dst, rep['out_md5']))
    return 0


def check_lc5(zp, log=print, variant='full'):
    cfg = VARIANTS[variant.replace('lc5_', '')]
    fails = []
    B = KB.Built(zp)
    sc = B.sc
    a, s = L3.L2.census(sc)
    log('census: %d actors / %d squads' % (a, s))
    cv = [k for k, g, n in DN.dancers(B)]
    log('civilians: %d (want %d)' % (len(cv), cfg['want']))
    if len(cv) != cfg['want']:
        fails.append('civilians %d, wanted %d' % (len(cv), cfg['want']))
    guards = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and sc.names[sc.top[k]].startswith('OldWaves!Guard_')]
    log('bodyguards: %d men in %d squads (want %d / %d)' % (len(guards), len({sc.top[k] for k in guards}), cfg['men'], cfg['squads']))
    if len(guards) != cfg['men'] or len({sc.top[k] for k in guards}) != cfg['squads']:
        fails.append('bodyguard count')
    if cfg['guards'] and not any('Guard_' in x for x in KB.Built(zp).sc.names):
        fails.append('no guard squads')
    # looks
    cnt = collections.Counter()
    for k in civ_actors(sc):
        m, v, _s = C.person(sc, k)
        cnt[(m, v)] += 1
    log('looks (model, variant): %s' % dict(cnt))
    if len(cnt) < cfg.get('min_looks', 8):
        fails.append('fewer than %d distinct looks' % cfg.get('min_looks', 8))
    if cfg.get('max_actors') and (a > cfg['max_actors'] or s > cfg['max_squads']):
        fails.append('census %d/%d over the cap %d/%d' % (a, s, cfg['max_actors'], cfg['max_squads']))
    # the sound member is untouched
    import zipfile, hashlib
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.lower().endswith('.snd'):
                if hashlib.md5(z.read(n)).hexdigest()[:8] != SND_MD5:
                    fails.append('SND member changed: %s' % n)
    # kl_chars.check on the zip against the live zip: only problems the live one does not have already count (4 M05 glow30 shaders do)
    import tempfile
    def probs(z):
        with tempfile.TemporaryDirectory() as t:
            shutil.copy(z, os.path.join(t, 'F01_Main.zip'))
            return C.check(C.Lv(t), log=lambda *_: None)
    live = os.environ.get('KL_DM05A_LIVE', os.path.join(L3.SIBLINGS, 'F01_Main.zip'))
    if os.path.isfile(live):
        base = set(probs(live))
        new = [p for p in probs(zp) if p not in base]
        log('kl_chars.check: %d new problems' % len(new))
        fails += ['kl_chars.check: ' + p for p in new]
    if os.path.isfile(live):
        with zipfile.ZipFile(zp) as z1, zipfile.ZipFile(live) as z0:
            f1 = [n for n in z1.namelist() if n.lower().endswith('.fxc')][0]
            s1, s0 = z1.getinfo(f1).file_size, z0.getinfo(f1).file_size
        log('.fxc: %d bytes (live %d)' % (s1, s0))
        if s1 > s0:
            fails.append('.fxc grew %d -> %d: one heap block at load, slim it (kl_light.slim_cache)' % (s0, s1))
    for f in fails:
        log('FAIL: ' + f)
    return fails


def _patch():
    L3.build_pack = lambda src, dst, force, log, variant: build_lc5(src, dst, force, log, variant)
    L3.check = lambda zp, log=print, variant='full': check_lc5(zp, log, variant)
    orig = L3.configure

    def configure(variant):
        orig(variant)
        L3.CFG.update(VARIANTS[variant.replace('lc5_', '')])
        L3.CFG['variant'] = variant
    L3.configure = configure


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('build', 'check', 'stage'):
        print(__doc__)
        return 2
    _patch()
    variant = opt('--variant', 'full')
    L3.NOPROC[0] = '--no-proc-check' in a
    vs = tuple(v if v in ('safe', 'mid') else 'lc5_' + v for v in variant.split(','))
    if a[0] == 'check':
        return 1 if check_lc5(a[1], variant=vs[0]) else 0
    if a[0] == 'build':
        r = build_lc5(a[1], a[2], '--force' in a, print, vs[0])
        return r or (1 if check_lc5(a[2], variant=vs[0]) else 0)
    return L3.stage(a[1], a[2], opt('--rehearse'), variants=vs)


if __name__ == '__main__':
    sys.exit(main())
