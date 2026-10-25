#!/usr/bin/env python3
"""kl_club_lastcall7.py - Last Call (DM05A) pass 1025a: fewer PARTICLE EMITTERS and campaign shard pools, on top of lc6. OFFLINE.

  python tools/kl_club_lastcall7.py plan  <lc6 F01_Main.zip 701d082f>
  python tools/kl_club_lastcall7.py build <lc6 F01_Main.zip 701d082f> <out F01_Main.zip> [--force] [--cut-campaign]
  python tools/kl_club_lastcall7.py check <zip> [--live <lc6 zip>]
  python tools/kl_club_lastcall7.py roots <lc6 zip> <lc7 zip> <DM05A folder holding KL{Guns,Wardrobe,Join,Talk}.ini>
  python tools/kl_club_lastcall7.py stage <lc6 zip> <out folder> --rehearse <scratch> [--no-proc-check] [--cut-campaign]

WHY: DM05A (32-bit kl2) still runs out of address space in round 1 after lc6 (28,550 -> 21,033 entities, 10,918 -> 6,323 emitters): of two live runs
one survived (min free VA 202 MB), one died (14 MB). The suspect is a non-kl2 module (the D3D10 driver) growing private 16 MB / halving allocations
with the draw / particle volume. Every ZParticleEmitter is a particle system with its own buffers, so the emitter count is the next lever.
WHAT IT DOES (nothing with a gameplay role is touched; no actor, spawn, loot, escape, bound, squad, wardrobe / gun root, no ZSTDOBJ pane):
 1. STATIC GLASS DECORATION: the Emitter_Glass_{Debris,Dust,Smoke}* LEAVES that sit in a plain ZGROUP under Locations/M05_A/M05A_LOC_Inside
    (RaveBar_GlassA/B/C, Glass_StairsA..F, Booth_A: 760 of the 902 static Inside emitters). Each group is the "particles" half of a glass
    break: a ZShotActivate lists the group (RaveBar, Stairs) or the emitters (Booth lamps, While_Lamp_ON) and fires it when the pane / lamp is
    shot. They are dust, debris and smoke puffs only: the pane, its shards and the break itself stay. The (now empty) groups STAY because the
    shot triggers name them (no trigger loses its target; the Booth lamps' emitter lists are cut and may be empty). The club windows players
    shoot (FX_*_WindowA_Spec*, ZAllocMany pools) are NOT in this set. Pooled templates (ZAllocMany) are NOT touched.
 2. CAMPAIGN-ONLY SHARD POOLS (OFF by default since 1025b; --cut-campaign; UNSAFE: Bottles_A is shared with the dance floor, panes keep '' pools): the ZAllocMany templates under M05A_LOC_Inside of the daughter room
    (GlassA/B/C_DaughterRoom), the wardrobe window (Win_WardrobeA), the lounge sofa table (Sofa_Lounge_TableA) and the shelf bottles (Bottles_A),
    each together with its clone group CloneGroup_Locations/... (so no clone group is orphaned; a template and its group leave as a pair). The
    references to them (the pane's ZHavokShatter[Glass] fields [0] shards / [1] particles) are CUT by trim_pass (an unresolvable path becomes '').
Machinery: kl_club_lastcall3.trim_pass (nested node indices), then kl_fa_bank seal + reverify, exactly as lc6.
GUESSES, said plainly: (a) the engine was NOT run on this. (b) A pane whose ZHavokShatterGlass[0]/[1] is now '' may dereference a NULL pool when
SHOT (the same field is already '' for some stock panes? not established: the empty-field scan of the live scene found no such pane except the
unused slots [3],[4],[6]..). If e8 sees a crash on shooting a daughter-room / wardrobe window / lounge table / bottle, that was the --cut-campaign variant; the default (1025b) keeps those pools.
(c) That the 760 emitters are pure decoration: the only holders are ZSTDOBJ ZShotActivate lists (asserted), never an AI / game-flow node.
(d) The target 'about 4,500 emitters' is NOT reached by these two rules (see the report line of build); the rest sit in shared stock pools
(BulletImpacts 1,611, WeaponsEffects 1,347, car explosions 672) and in the roof / outside window pools: not touched here.
"""
import collections
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_club_lastcall3 as L3
import kl_club_lastcall5 as L5
import kl_club_lastcall6 as L6
import kl_fa_bots as KB
import kl_chars as C
import kl_prpjoin as J
import kl_octree as O
import kl_prmgraph as PG

BS = chr(92)
MD5_LC6 = '701d082f89989a6a029dfca32ddd731c'
TAG, STEM = '.before-1025lc7', 'lc7'
VARIANTS = {'lc7': dict(mode='pack', base=MD5_LC6, tag=TAG, stem=STEM, remove=None)}
L3.VARIANTS['lc7'] = VARIANTS['lc7']
INSIDE = 'M05A_LOC_Inside.zip'
GLASS = re.compile(r'^Emitter_Glass_(Debris|Dust|Smoke)')
CAMPAIGN = re.compile(r'(Glass[ABC]_DaughterRoom|Win_WardrobeA|Sofa_Lounge_TableA|Bottles_A)')
KEEP = [False]


def md5(p):
    return L3.md5(p)


def _under_inside(sc, k):
    return sc.path[k].startswith('ROOT' + BS + 'Locations') and INSIDE in sc.path[k]


def _span(sc, roots):
    out = set()
    for t in roots:
        out.update(range(t, sc.end[t]))
    return out


def plan(sc, log=print, campaign=None):
    """-> dict(emitters=[leaf node], pools=[(template, clone group top or None, family)], drop=[nodes to give trim_pass])"""
    campaign = (not KEEP[0]) if campaign is None else campaign
    n = len(sc.nodes)
    holders = collections.defaultdict(set)
    for k, _h, _f, _s, hit in J.references(sc):
        for h in hit or []:
            holders[h].add(k)
    em = [k for k in range(1, n) if sc.cls(k) == 'ZParticleEmitter' and _under_inside(sc, k) and sc.cls(sc.parent[k]) == 'ZGROUP'
          and GLASS.match(sc.names[k]) and 'WindowA_Spec' not in sc.path[k]]
    for k in em:
        bad = {sc.cls(h) for h in holders.get(k, ()) if h >= 0 and sc.cls(h) != 'ZSTDOBJ'} | ({'scene'} if -1 in holders.get(k, ()) else set())
        if bad:
            raise ValueError('%s is named by %s: not pure decoration' % (sc.path[k], bad))
    pools = []
    if campaign:
        tops = {sc.names[t]: t for t in sc.tops()}
        for k in range(1, n):
            if sc.cls(k) != 'ZAllocMany' or sc.path[k].startswith('ROOT' + BS + 'CloneGroup') or not _under_inside(sc, k):
                continue
            m = CAMPAIGN.search(sc.names[k])
            if not m:
                continue
            tgt = sc.p.key(L6._field(sc, k, 'ZAllocMany[3]')[0])[5:]
            t = tops.get(tgt)
            nn = struct.unpack('<H', L6._field(sc, k, 'ZAllocMany[0]')[0][1][:2])[0]
            if t is not None:
                kids = [c for c in range(t + 1, sc.end[t]) if sc.parent[c] == t]
                if sc.cls(t) != 'ZGROUP' or len(kids) != nn or {sc.cls(c) for c in kids} != {'ZAllocMany'}:
                    raise ValueError('%s: clone group is not %d ZAllocMany copies' % (sc.path[k], nn))
            elif tgt:
                raise ValueError('%s: clone group %r not found' % (sc.path[k], tgt))
            pools.append((k, t, m.group(1)))
    # one holder may name several pools (a shared Shards template): every holder is a pane / prop of the same campaign family
    for k, t, fam in pools:
        for h in holders.get(k, ()):
            if h >= 0 and not CAMPAIGN.search(sc.path[h]):
                raise ValueError('%s is named by %s, outside the campaign families' % (sc.path[k], sc.path[h]))
    drop = list(em) + [x for k, t, _f in pools for x in ((k, t) if t is not None else (k,))]
    inpool = _span(sc, [x for k, t, _f in pools for x in ((k, t) if t is not None else (k,))])
    if any(k in inpool for k in em):
        raise ValueError('a static emitter sits inside a campaign pool')
    log('  static glass emitters: %d; campaign pools: %d templates, %d clone groups (%d entities, %d emitters)' % (
        len(em), len(pools), sum(1 for _k, t, _f in pools if t is not None), len(inpool),
        sum(1 for k in inpool if sc.cls(k) == 'ZParticleEmitter')))
    return dict(emitters=em, pools=pools, drop=drop, pool_nodes=inpool)


def counts(zp):
    c = L6.counts(zp)
    B = KB.Built(zp)
    c['prm_chunks'] = struct.unpack_from('<II', B['.prm'], 0)[1]
    return c


# ------------------------------------------------------------------ build
def build_lc7(src, dst, force, log):
    h = md5(src)
    if h != MD5_LC6 and not force:
        raise SystemExit('refusing: %s md5 %s is not lc6 %s (use --force)' % (src, h, MD5_LC6))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    W = os.path.join(os.path.dirname(os.path.abspath(dst)), '_lc7_work')
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(W)
    sc = KB.Built(src).sc
    pl = plan(sc, log)
    before = counts(src)
    t1 = os.path.join(W, 't1.zip')
    rep = collections.OrderedDict(source=src, source_md5=h, plan=dict(
        emitters=len(pl['emitters']), pools=[(sc.path[k].split(BS)[-1], fam) for k, _t, fam in pl['pools']], campaign=not KEEP[0],
        pool_entities=len(pl['pool_nodes'])))
    rep['trim'] = L3.trim_pass(src, t1, pl['drop'], log, room_items=True)
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


def check_lc7(zp, log=print, live=None):
    live = live or os.environ.get('KL_DM05A_LC6', os.path.join(L3.SIBLINGS, 'F01_Main.zip'))
    fails = []
    if md5(live) != MD5_LC6:
        raise SystemExit('check needs lc6 701d082f as the reference; %s is %s' % (live, md5(live)[:8]))
    B0, B1 = KB.Built(live), KB.Built(zp)
    s0, s1 = B0.sc, B1.sc
    pl = plan(s0, lambda *_: None)
    c0, c1 = counts(live), counts(zp)
    for k in ('entities', 'emitters', 'alloc', 'actors', 'squads', 'civilians', 'looks', 'prm_chunks'):
        log('%-10s %6d -> %6d' % (k, c0[k], c1[k]))
    gone_set = _span(s0, pl['drop'])
    p0 = collections.Counter(s0.path[k] for k in range(1, len(s0.nodes)))
    p1 = collections.Counter(s1.path[k] for k in range(1, len(s1.nodes)))
    if p1 - p0:
        fails.append('%d paths in the new scene are not in lc6, e.g. %s' % (sum((p1 - p0).values()), next(iter(p1 - p0))))
    want = collections.Counter(s0.path[k] for k in gone_set)
    if p0 - p1 != want:
        fails.append('removed paths differ from the plan: %d gone, %d planned' % (sum((p0 - p1).values()), sum(want.values())))
    lost = collections.Counter(s0.cls(k) for k in gone_set)
    for bad in ('ZFFActor', 'ZFFPlayer', 'ZSquadScript', 'ZBOUND', 'ZSNDOBJ', 'ZOMNILIGHT', 'ZROOM'):
        if lost[bad]:
            fails.append('%d %s among the removed nodes' % (lost[bad], bad))
    stray = [s0.path[k] for k in gone_set if s0.cls(k) == 'ZSTDOBJ' and k not in pl['pool_nodes']]
    if stray:
        fails.append('%d ZSTDOBJ removed outside the shard pools, e.g. %s' % (len(stray), stray[0]))     # shard objects of the pools only, never a pane
    log('removed classes: %s' % dict(lost))
    if c1['emitters'] != c0['emitters'] - lost['ZParticleEmitter']:
        fails.append('emitters %d -> %d, plan says -%d' % (c0['emitters'], c1['emitters'], lost['ZParticleEmitter']))
    if c1['prm_chunks'] != c0['prm_chunks']:
        fails.append('.prm chunk count %d -> %d (KLJoin [FedBody] Entries=54305 depends on it!)' % (c0['prm_chunks'], c1['prm_chunks']))
    if c1['actors'] != c0['actors'] or c1['squads'] != c0['squads'] or c1['civilians'] != c0['civilians']:
        fails.append('actors / squads / civilians changed')
    for name in ('Spawn', 'Loot', 'Escape', 'Bound', 'START', 'Wardrobe', 'Guns', 'OldWaves!Wave_', 'Roof_R', 'merc_bot_squad', 'WindowA_Spec'):
        n0 = sum(1 for k in range(1, len(s0.nodes)) if name.lower() in s0.names[k].lower())
        n1 = sum(1 for k in range(1, len(s1.nodes)) if name.lower() in s1.names[k].lower())
        if n0 != n1:    # counted over ALL lc6 nodes: a protected name among the removed ones fails too
            fails.append('nodes named *%s*: %d -> %d' % (name, n0, n1))
    # the club windows keep every emitter and pool
    ww0 = sum(1 for k in range(1, len(s0.nodes)) if 'WindowA_Spec' in s0.path[k] and s0.cls(k) == 'ZParticleEmitter')
    ww1 = sum(1 for k in range(1, len(s1.nodes)) if 'WindowA_Spec' in s1.path[k] and s1.cls(k) == 'ZParticleEmitter')
    if ww0 != ww1:
        fails.append('WindowA_Spec emitters %d -> %d' % (ww0, ww1))
    if {s1.path[t] for t in J.orphan_clone_groups(s1)} != {s0.path[t] for t in J.orphan_clone_groups(s0)}:
        fails.append('orphan clone groups differ from lc6')
    d0, d1 = J.dangling(s0), J.dangling(s1)
    if len(d1[0]) > len(d0[0]) or len(d1[1]) > len(d0[1]):
        fails.append('new dangling references: %d paths, %d names' % (len(d1[0]) - len(d0[0]), len(d1[1]) - len(d0[1])))
    log('orphan clone groups: as lc6, dangling %d/%d -> %d/%d' % (len(d0[0]), len(d0[1]), len(d1[0]), len(d1[1])))
    # no clone group left whose template is gone, no template whose group is gone
    left = {p for p in p1}
    for k, t, _f in pl['pools']:
        if (s0.path[k] in left) or (t is not None and s0.path[t] in left):
            fails.append('pool %s: template / clone group not removed as a pair' % s0.path[k].split(BS)[-1])
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
            if n.lower().endswith('.snd') and hashlib.md5(z1.read(n)).hexdigest()[:8] != L6.SND_MD5:
                fails.append('SND member changed: %s' % n)
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


def _ini_roots(folder):
    roots = []
    for nm in ('KLGuns.ini', 'KLWardrobe.ini', 'KLJoin.ini', 'KLTalk.ini'):
        p = os.path.join(folder, nm)
        if os.path.isfile(p):
            for line in open(p, encoding='utf-8', errors='replace'):
                m = re.match(r'\s*Root\s*=\s*(\d+)', line)
                if m and int(m.group(1)):
                    roots.append((nm, int(m.group(1))))
    return roots


def check_roots(old_zip, new_zip, folder, log=print):
    """kl_prmgraph.walk closure of every Root= chunk of the .ini files: identical in both .prm; the only byte difference allowed is the +0x1c .oct
    offset of a model root, and then the .oct record it points to must be byte-identical (Record.pack)."""
    A, B = KB.Built(old_zip), KB.Built(new_zip)
    p0, p1 = PG.read(A['.prm']), PG.read(B['.prm'])
    o0, o1 = O.Oct.parse(A['.oct']), O.Oct.parse(B['.oct'])
    r0, r1 = o0.record_refs(), o1.record_refs()
    fails, seen = [], set()
    roots = _ini_roots(folder)
    if len(p0.chunks) != len(p1.chunks):
        fails.append('chunk count %d != %d' % (len(p0.chunks), len(p1.chunks)))
    n_oct = 0
    for nm, r in roots:
        if r in seen:
            continue
        seen.add(r)
        k0, a0 = PG.walk(p0, [r])
        k1, a1 = PG.walk(p1, [r])
        if k0 != k1 or a0 != a1:
            fails.append('%s Root=%d: closure differs' % (nm, r))
            continue
        for i in sorted(k0):
            c0, c1 = p0.chunks[i], p1.chunks[i]
            if c0 == c1:
                continue
            if len(c0) == 64 and c0[:4] == b'\0\1\7\0' and len(c1) == 64 and c0[:0x1c] + c0[0x20:] == c1[:0x1c] + c1[0x20:]:
                v0, v1 = struct.unpack_from('<I', c0, 0x1c)[0], struct.unpack_from('<I', c1, 0x1c)[0]
                if v0 in r0 and v1 in r1 and o0.records[r0.index(v0)].pack() == o1.records[r1.index(v1)].pack():
                    n_oct += 1
                    continue
                fails.append('%s Root=%d chunk %d: +0x1c %#x -> %#x, the .oct record differs or is not found' % (nm, r, i, v0, v1))
            else:
                fails.append('%s Root=%d chunk %d differs beyond +0x1c' % (nm, r, i))
    log('roots checked: %d (%s), closure chunks identical; %d chunks differ only in the .oct offset (record byte-identical)' % (
        len(seen), ', '.join(sorted({n for n, _r in roots})), n_oct))
    for f in fails:
        log('FAIL: ' + f)
    return fails


def _patch():
    L3.build_pack = lambda src, dst, force, log, variant: build_lc7(src, dst, force, log)
    L3.check = lambda zp, log=print, variant='lc7': check_lc7(zp, log)
    orig = L3.configure

    def configure(variant):
        orig(variant)
        L3.CFG.update(VARIANTS['lc7'])
        L3.CFG['variant'] = variant
    L3.configure = configure


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('plan', 'build', 'check', 'stage', 'roots'):
        print(__doc__)
        return 2
    _patch()
    L3.NOPROC[0] = '--no-proc-check' in a
    KEEP[0] = '--cut-campaign' not in a      # 1025b: campaign pools are KEPT by default (verifiers: 21 panes would lose their pool, Bottles_A pool is shared with the dance floor)
    if a[0] == 'plan':
        sc = KB.Built(a[1]).sc
        p = plan(sc)
        print('nodes out: %d of %d' % (len(_span(sc, p['drop'])), len(sc.nodes) - 1))
        for k, t, fam in p['pools']:
            print('  pool', fam, sc.path[k].split(BS)[-2], sc.names[k], 'group' if t else 'no group')
        return 0
    if a[0] == 'check':
        return 1 if check_lc7(a[1], live=opt('--live')) else 0
    if a[0] == 'roots':
        return 1 if check_roots(a[1], a[2], a[3]) else 0
    if a[0] == 'build':
        r = build_lc7(a[1], a[2], '--force' in a, print)
        return r or (1 if check_lc7(a[2], live=a[1]) else 0)
    return L3.stage(a[1], a[2], opt('--rehearse'), variants=('lc7',))


if __name__ == '__main__':
    sys.exit(main())
