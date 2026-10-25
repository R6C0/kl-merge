#!/usr/bin/env python3
"""kl_club_lastcall6.py - Last Call (DM05A) pass 1025a: a LEANER scene, same game. OFFLINE.

  python tools/kl_club_lastcall6.py plan  <live F01_Main.zip d5f8522b>
  python tools/kl_club_lastcall6.py build <live F01_Main.zip d5f8522b> <out F01_Main.zip> [--force]
  python tools/kl_club_lastcall6.py check <zip> [--live <live zip>]
  python tools/kl_club_lastcall6.py stage <live zip> <out folder> --rehearse <scratch> [--no-proc-check]

WHY: DM05A crashes kl2 (32-bit) ~20-120 s into round 1 because the ADDRESS SPACE runs out (free VA 1728 MB before the load -> 14-17 MB;
private committed 299 MB at the menu -> 1209 MB at round 1 + 35 s; lc5 SAFE died on a HeapAlloc NULL). The textures, Havok, animation and sound
of DM05A are NOT outliers (census of 2026-10-25, C:/kl_build_1024/lastcall6_1025a/census*.py); the SCENE is: 28,550 entities (stable maps 16k-24k),
10,918 ZParticleEmitter (4.3k-6.6k), 2,573 ZAllocMany (1.0k-1.5k). d5f already has 40 civilians with ONE look, so "fewer looks" is not the lever.
THE FINDING (this tool, measured on d5f8522b): the biggest block is ZAllocMany POOLS. A glass-break effect is a template ZAllocMany (field
ZAllocMany[0] = pool size N, [3] = its clone group) plus a clone group CloneGroup_Locations/... = a ZGROUP holding N full COPIES of the effect
(each copy is a ZAllocMany with its emitters). 247 templates, pool sizes 20 (70 of them!), 5, 7 ... The 60 roof windows (FX0001_M05_RoofGlas_A_01..48,
B_01..12) have N = 20 where every other map prop has 2..5: 9,350 entities (32.7% of the scene, 5,040 emitters) for panes that break ONCE each.
WHAT IT DOES (nothing gameplay-visible is removed; every window, prop, trigger, sound stays):
 1. POOL SHRINK: every per-prop effect template under Locations/M05_A/M05A_LOC_* with pool N > K is shrunk to K: copies K+1..N of its clone group are
    taken out (the clone group then has exactly the shape of a stock group with a pool of K), and ZAllocMany[0] = K on the template and on the
    kept copies (they carry a copy of the template's fields). K = 2 for a template that ONE holder names (the pane / prop that breaks once);
    K = min(N, 6) for a template that SEVERAL holders share (the 48 A panes share one Shards_16 pool, the 12 B panes one Shards_14 pool).
    Template and clone group stay together, so no orphan clone group arises (kl_prpjoin.orphan_clone_groups is compared with the live build's own).
 2. PARKED CAMPAIGN MEN: the 13 men / 6 squads of kl_club_lastcall5.REMOVE_LITE (dance-floor guards, fat bouncer; the exact trim lc5 SAFE used).
    KEPT: HunterKillers, Bodyguards_First_Floor, YokoGuards, Rave#01/02, Lounge#01/02 (the bots' stage gates point at them), the 6 OldWaves police
    squads (30) + 3 roof squads (12) + 7 merc bots, the 40 civilians and their dance routs, every spawn / loot / escape / bound / wardrobe / gun root.
 Civilians are NOT touched: 40 (<= 50) with ONE look (<= 6): they cost 8 scene entities each, look count is no outlier in the census.
Machinery: kl_club_lastcall3.trim_pass (.prp via kl_prpjoin.join(skip=), .gms / .buf, .oct / .rmi / .rmc remap, .prm roots, references INTO the cut
nodes cut, bots' gates re-pointed), extended 2026-10-25 to take node indices (nested subtrees) as well as top-group names and a `post` hook for field
edits on the joined scene; then kl_fa_bank seal + reverify.
GUESSES, said plainly: (a) that kl2 reads a pool of K from a clone group holding exactly K copies (true of the 247 stock groups: every one has
len(copies) == N, asserted); the engine was NOT run on this. (b) that K = 2 / 6 is enough: a pane breaks once, but two panes of a shared pool breaking
within the effect's lifetime beyond 6 would show no debris for the 7th (unmeasured). (c) the memory saved per entity: offline there is no meter. The A/B
e8 can run: this zip vs d5f, k48 line 'free VA' at the menu and in round 1.
"""
import collections
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_club_lastcall3 as L3
import kl_club_lastcall5 as L5
import kl_club_dance_1024 as DN
import kl_fa_bots as KB
import kl_chars as C
import kl_prpjoin as J
import kl_fa
import struct

BS = chr(92)
MD5_D5F = L5.MD5_D5F
SND_MD5 = L5.SND_MD5
TAG, STEM = '.before-1025lc6', 'lc6'
VARIANTS = {'lc6': dict(mode='pack', base=MD5_D5F, tag=TAG, stem=STEM, remove=None)}
L3.VARIANTS['lc6'] = VARIANTS['lc6']


def md5(p):
    return L3.md5(p)


POOL_K_ONE, POOL_K_SHARED = 2, 6


def _field(sc, k, label):
    return next(u for _h, f, u in J.fields(sc, k) if f == label)


def _tpl_nodes(sc):
    """ZAllocMany templates of the map's own locations: AllocMany nodes outside every clone group, under Locations/M05_A/M05A_LOC_*
    (the shared Effects/AllocMany pools - bullets, muzzle flashes, cars - are not touched)."""
    return [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZAllocMany' and not sc.path[k].startswith('ROOT' + BS + 'CloneGroup')
            and 'M05A_LOC_' in sc.path[k] and '\\Effects/' not in sc.path[k]]


def _span(sc, roots):
    out = set()
    for t in roots:
        out.update(range(t, sc.end[t]))
    return out


def plan(sc, log=print):
    """-> dict(shrink=[(template node, clone group top, N, K, [copy roots kept], [copy roots dropped])], drop=[node indices], skipped=[...]).
    Asserts the shape every template must have: the clone group is a ZGROUP whose direct children are exactly N ZAllocMany copies of one size."""
    tops = {sc.names[t]: t for t in sc.tops()}
    holders = collections.defaultdict(set)                  # target node -> distinct holder nodes
    for k, _h, _f, _s, hit in J.references(sc):
        for h in hit or []:
            holders[h].add(k)
    shrink, skipped = [], []
    for k in _tpl_nodes(sc):
        n = struct.unpack('<H', _field(sc, k, 'ZAllocMany[0]')[0][1][:2])[0]
        tgt = sc.p.key(_field(sc, k, 'ZAllocMany[3]')[0])[5:]
        t = tops.get(tgt)
        if t is None:
            skipped.append((sc.path[k], 'no clone group'))
            continue
        kids = [c for c in range(t + 1, sc.end[t]) if sc.parent[c] == t]
        if sc.cls(t) != 'ZGROUP' or len(kids) != n or len({sc.end[c] - c for c in kids}) != 1 or {sc.cls(c) for c in kids} != {'ZAllocMany'}:
            skipped.append((sc.path[k], 'clone group is not %d equal ZAllocMany copies' % n))
            continue
        own = _span(sc, [k, t])
        outside = {h for h in holders.get(k, ()) if h not in own}
        kk = POOL_K_ONE if len(outside) <= 1 else min(n, POOL_K_SHARED)
        if n <= kk:
            continue
        shrink.append((k, t, n, kk, kids[:kk], kids[kk:]))
    drop = [c for _k, _t, _n, _kk, _keep, gone in shrink for c in gone]
    log('  pools shrunk: %d templates (pool %s), %d copies out, %d entities; left alone: %s' % (
        len(shrink), dict(collections.Counter(n for _k, _t, n, _kk, _a, _b in shrink)), len(drop), len(_span(sc, drop)), skipped[:3]))
    return dict(shrink=shrink, drop=drop, skipped=skipped)


def _set_counts(sc, pl):
    """post hook for trim_pass: ZAllocMany[0] = K on every shrunk template and on its kept copies (nodes of `sc` -> nodes of the joined scene)."""
    def hook(Jn):
        where = {sk: jk for jk, (_s, sk) in enumerate(Jn.origin)}      # trim_pass reads the same file: node indices agree
        lab = J.labels('dd', 'ZAllocMany').index('ZAllocMany[0]')
        done = 0
        for k, _t, _n, kk, keep, _gone in pl['shrink']:
            for node in [k] + keep:
                def fn(us, kk=kk):
                    if us[lab][0][0] != 0x08 or len(us[lab]) != 1:
                        raise ValueError('ZAllocMany[0] is not a plain u16')
                    us[lab] = [(0x08, struct.pack('<H', kk))]
                kl_fa.edit(Jn, where[node], None, fn)
                done += 1
        hook.done = done
    return hook


def counts(zp):
    B = KB.Built(zp)
    sc = B.sc
    cl = collections.Counter(sc.cls(k) for k in range(1, len(sc.nodes)))
    a, s = L3.L2.census(sc)
    civ = L5.civ_actors(sc)
    looks = collections.Counter(C.person(sc, k)[:2] for k in civ)
    sizes = {}
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            sizes[os.path.splitext(i.filename)[1].lower()] = sizes.get(os.path.splitext(i.filename)[1].lower(), 0) + i.file_size
        sizes['zip'] = os.path.getsize(zp)
    return dict(entities=len(sc.nodes) - 1, emitters=cl['ZParticleEmitter'], alloc=cl['ZAllocMany'], stdobj=cl['ZSTDOBJ'], actors=a, squads=s,
                civilians=len(civ), looks=len(looks), look_set={'%s v%s' % k: n for k, n in looks.items()}, sizes=sizes)


# ------------------------------------------------------------------ build
def build_lc6(src, dst, force, log):
    h = md5(src)
    if h != MD5_D5F and not force:
        raise SystemExit('refusing: %s md5 %s is not the live DM05A %s (use --force)' % (src, h, MD5_D5F))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    W = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc6_work')
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(W)
    B = KB.Built(src)
    sc = B.sc
    pl = plan(sc, log)
    ents = len(_span(sc, pl['drop']))
    log('  taking %d entities out of %d' % (ents, len(sc.nodes) - 1))
    before = counts(src)
    t1 = os.path.join(W, 't1.zip')
    hook = _set_counts(sc, pl)
    rep = collections.OrderedDict(source=src, source_md5=h, plan=dict(templates=len(pl['shrink']), copies_out=len(pl['drop']), entities_out=ents,
                                                                      skipped=pl['skipped'], guards=L5.REMOVE_LITE, K=[POOL_K_ONE, POOL_K_SHARED]))
    rep['trim'] = L3.trim_pass(src, t1, L5.REMOVE_LITE + pl['drop'], log, post=hook, room_items=True)
    if hook.done != sum(1 + len(x[4]) for x in pl['shrink']):
        raise ValueError('pool counts set on %d nodes' % hook.done)
    rep['trim'].pop('removed', None)
    L3.seal_verify(t1, log)
    shutil.copyfile(t1, dst)
    rep['before'], rep['after'] = before, counts(dst)
    rep['out_md5'] = md5(dst)
    with open(os.path.splitext(dst)[0] + '.' + STEM + '.json', 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    shutil.rmtree(W, ignore_errors=True)
    log('written %s md5 %s' % (dst, rep['out_md5']))
    return 0


def check_lc6(zp, log=print, live=None):
    live = live or os.environ.get('KL_DM05A_LIVE', os.path.join(L3.SIBLINGS, 'F01_Main.zip'))
    fails = []
    if md5(live) != MD5_D5F:
        raise SystemExit('check needs the live d5f8522b as the reference; %s is %s' % (live, md5(live)[:8]))
    B0, B1 = KB.Built(live), KB.Built(zp)
    s0, s1 = B0.sc, B1.sc
    pl = plan(s0, lambda *_: None)
    c0, c1 = counts(live), counts(zp)
    for k in ('entities', 'emitters', 'alloc', 'actors', 'squads', 'civilians', 'looks'):
        log('%-10s %6d -> %6d' % (k, c0[k], c1[k]))
    # exactly the planned nodes (and the guard groups) are gone, nothing else
    p0, p1 = collections.Counter(s0.path[k] for k in range(1, len(s0.nodes))), collections.Counter(s1.path[k] for k in range(1, len(s1.nodes)))
    gone = p0 - p1
    if p1 - p0:
        fails.append('%d paths in the new scene are not in the live one, e.g. %s' % (sum((p1 - p0).values()), next(iter(p1 - p0))))
    guard_t = [t for t in s0.tops() if s0.names[t] in L5.REMOVE_LITE]
    want = collections.Counter(s0.path[k] for k in _span(s0, pl['drop'] + guard_t))
    if gone != want:
        fails.append('removed paths differ from the plan: %d gone, %d planned' % (sum(gone.values()), sum(want.values())))
    # every shrunk pool: template + kept copies say K, the clone group holds exactly K copies, still the stock shape
    for k, t, n, kk, keep, _gone in pl['shrink']:
        tk = [x for x in range(1, len(s1.nodes)) if s1.path[x] == s0.path[k]]
        gt = [x for x in s1.tops() if s1.names[x] == s0.names[t]]
        if len(tk) != 1 or len(gt) != 1:
            fails.append('pool %s: template/clone group not found once' % s0.path[k].split(BS)[-1])
            continue
        kids = [c for c in range(gt[0] + 1, s1.end[gt[0]]) if s1.parent[c] == gt[0]]
        cnt = [struct.unpack('<H', _field(s1, x, 'ZAllocMany[0]')[0][1][:2])[0] for x in tk + kids]
        if len(kids) != kk or set(cnt) != {kk}:
            fails.append('pool %s: %d copies, counts %s (want %d)' % (s0.path[k].split(BS)[-1], len(kids), sorted(set(cnt)), kk))
    # protected classes: nothing but the 13 parked men and their squads may leave
    lostc = collections.Counter(s0.cls(k) for k in _span(s0, pl['drop']))
    for bad in ('ZFFActor', 'ZFFPlayer', 'ZSquadScript', 'ZBOUND'):
        if lostc[bad]:
            fails.append('%d %s in the pool copies taken out' % (lostc[bad], bad))
    if c1['civilians'] != c0['civilians'] or c1['looks'] > 6 or c1['civilians'] > 50:
        fails.append('civilians %d / looks %d (want %d, <= 6, <= 50)' % (c1['civilians'], c1['looks'], c0['civilians']))
    if c0['actors'] - c1['actors'] != 13 or c0['squads'] - c1['squads'] != 6:
        fails.append('actors %d -> %d, squads %d -> %d (the guard trim is 13 / 6)' % (c0['actors'], c1['actors'], c0['squads'], c1['squads']))
    gone0 = _span(s0, pl['drop'])
    for name in ('Spawn', 'Loot', 'Escape', 'Bound', 'START', 'Wardrobe', 'Guns', 'OldWaves!Wave_', 'Roof_R', 'merc_bot_squad'):
        n0 = sum(1 for k in range(1, len(s0.nodes)) if k not in gone0 and name.lower() in s0.names[k].lower())
        n1 = sum(1 for k in range(1, len(s1.nodes)) if name.lower() in s1.names[k].lower())
        if n0 != n1:
            fails.append('nodes named *%s*: %d -> %d' % (name, n0, n1))
    if {s1.path[t] for t in J.orphan_clone_groups(s1)} != {s0.path[t] for t in J.orphan_clone_groups(s0)}:
        fails.append('orphan clone groups differ from the live ones')
    d0, d1 = J.dangling(s0), J.dangling(s1)
    if len(d1[0]) > len(d0[0]) or len(d1[1]) > len(d0[1]):
        fails.append('new dangling references: %d paths, %d names' % (len(d1[0]) - len(d0[0]), len(d1[1]) - len(d0[1])))
    log('orphan clone groups: as live, dangling %d/%d -> %d/%d' % (len(d0[0]), len(d0[1]), len(d1[0]), len(d1[1])))
    # members: sound untouched, .fxc / .TEX / .ANM / .HVK / .MAT / .zgf byte-identical, only the scene members change
    with zipfile.ZipFile(zp) as z1, zipfile.ZipFile(live) as z0:
        n0, n1 = z0.namelist(), z1.namelist()
        if n0 != n1:
            fails.append('member list differs')
        diff = [n for n in n0 if n in n1 and hashlib.md5(z0.read(n)).digest() != hashlib.md5(z1.read(n)).digest()]
        log('members changed: %s' % sorted(os.path.splitext(n)[1].lower() for n in diff))
        for n in diff:
            if os.path.splitext(n)[1].lower() not in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm'):
                fails.append('unexpected member changed: %s' % n)
        for n in n1:
            if n.lower().endswith('.snd') and hashlib.md5(z1.read(n)).hexdigest()[:8] != SND_MD5:
                fails.append('SND member changed: %s' % n)
    # the shared problem check, only NEW problems count
    import tempfile

    def probs(z):
        with tempfile.TemporaryDirectory() as t:
            shutil.copy(z, os.path.join(t, 'F01_Main.zip'))
            return C.check(C.Lv(t), log=lambda *_: None)
    base = set(probs(live))
    new = [p for p in probs(zp) if p not in base]
    log('kl_chars.check: %d new problems' % len(new))
    fails += ['kl_chars.check: ' + p for p in new]
    for f in fails:
        log('FAIL: ' + f)
    return fails


def _patch():
    L3.build_pack = lambda src, dst, force, log, variant: build_lc6(src, dst, force, log)
    L3.check = lambda zp, log=print, variant='lc6': check_lc6(zp, log)
    orig = L3.configure

    def configure(variant):
        orig(variant)
        L3.CFG.update(VARIANTS['lc6'])
        L3.CFG['variant'] = variant
    L3.configure = configure


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('plan', 'build', 'check', 'stage'):
        print(__doc__)
        return 2
    _patch()
    L3.NOPROC[0] = '--no-proc-check' in a
    if a[0] == 'plan':
        sc = KB.Built(a[1]).sc
        p = plan(sc)
        print('entities out: %d of %d' % (len(_span(sc, p['drop'])), len(sc.nodes) - 1))
        return 0
    if a[0] == 'check':
        return 1 if check_lc6(a[1], live=opt('--live')) else 0
    if a[0] == 'build':
        r = build_lc6(a[1], a[2], '--force' in a, print)
        return r or (1 if check_lc6(a[2], live=a[1]) else 0)
    return L3.stage(a[1], a[2], opt('--rehearse'), variants=('lc6',))


if __name__ == '__main__':
    sys.exit(main())
