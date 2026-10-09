#!/usr/bin/env python3
"""
Every map through the graft, offline: build S + M into a folder of its own, verify, run the
Fragile Alliance check and measure the result. Nothing is installed and the game is not started;
kl_graft's own output folder (<work>/build/install, what the live tests install from) is never
written: kl_graft.out_dir is replaced for the length of a build. Spec and results: re/maps.md.

    python kl_maps.py one  <out> F07 M02_FA_A [options]   one build -> <out>/F07+M02_FA_A/
    python kl_maps.py maps <out> [-j N]                   F07 + each Dead Men FA map
    python kl_maps.py hosts <out> [M03_FA_A] [-j N]       every stock F level as S against one map
    python kl_maps.py m09  <out> [-j N]                   F07 + M09_A, F07 + M09_B, raw and with the
                                                          campaign pre-pass (story levels)
    python kl_maps.py chain <out> F07 M09_B M09_A         THREE sources: S + M1, then that + M2
    python kl_maps.py table <out>                         the table of everything built in <out>
    python kl_maps.py what M06_FA_A                       what a level is: title, rooms, extent, names
    python kl_maps.py sides M09_A                         how kl_graft splits a level's subtrees and
                                                          what the campaign pre-pass drops
    python kl_maps.py hostfacts [M03_FA_A]                what differs between the stock hosts
    python kl_maps.py clash M09_A M09_B                   top-level names two maps share
    python kl_maps.py navtest                             the rules nav_join rests on, on every
                                                          stock mesh, and three trial joins
  options of 'one':  --keep        leave the archive and the files beside it (default: measured,
                                   then deleted - a build is 0.3 .. 0.4 GB)
                     --campaign    the campaign pre-pass (campaign_drop) for a story level
                     --heroes      S's Heroes! groups at the level's HERO_AT markers
                     kl_graft's own: --silent --no-loc --no-fa --stock-anm --light X
                     --m-drop A,B  --m-add A,B

Each build runs in a process of its own (a failure is a row of the table, not the end of the
run). <out>/<S>+<M>/result.json holds the numbers, log.txt what kl_graft printed.

WHAT IS MEASURED (from the written files, not from kl_graft's log)
  archive MB, beside MB (.WHD .WAV .hti and the _LS bank), entities (.gms), textures of 4096 and
  materials of 2048 (kl_texmat), sounds / waves (kl_snd type tables 1 / 4; the largest stock bank
  has 4,806 / 4,568), rooms, .prm chunks, problems (kl_graft.verify), FA findings by severity
  (kl_fa.check on the written archive), every scene path that names nothing ('dangling';
  verify() shows the first ten).

CAMPAIGN PRE-PASS (--campaign; a story level has no Fragile Alliance layer)
  kl_prpjoin.sides() knows two sides, and everything that is not a systems subtree is 'map': in
  M09_A that makes 'map' of 88 AI_Players! squads, 35 Characters!, 97 Markup!, the cut scenes,
  the music triggers, the co-op airlocks, the rappel. campaign_drop() names what must not come:
  every top-level map subtree that is not geometry (Locations/*, CloneGroup_Locations, a
  backdrop), not the level's ambience (Locations/<L>/<L>_Audio.zip!*), not an effect template
  (Effects/*) and not a passive marker (PASSIVE: cover and level-bound boxes without a script).
  Clone groups follow their template (kl_graft.picks_of). The names go to Select(m_drop=...).

THREE SOURCES (chain): kl_graft.build takes one S and one M. Two maps go through it as
  S + M1 -> a level 'R09' in <out>/chain/, then R09 as S (every subtree of it counted as systems:
  nothing of it leaves, nothing of it is renumbered) + M2. For that the stock-file lookups of
  kl_prpjoin / kl_snd / kl_graft are redirected for the name R09 (PSEUDO). What the second step
  loses because build() has a single map in mind is listed in re/maps.md (FDX, scene block,
  .hrd). The navigation mesh is not lost: nav_join() puts both meshes into one (EXPERIMENT).
"""
import collections, json, os, struct, subprocess, sys, time, traceback, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LIMITS = {'textures': 4096, 'materials': 2048}
DM_FA = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A']
DD_FA = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']
SLOT = 'F01'
# Dead Men's own names (AllLevels/Menu/Online/Scenarios/TitleNN + BriefingNN of its .LOC; the
# order is the order of the level folders - Briefing03 speaks of the Japanese Gardens and a
# chopper, and M06_FA_A is the one map with ZHeli escape vehicles and 299 'DopeBag' loot objects)
TITLES = {'M01_FA_A': ('Title00', 'Briefing00'), 'M02_FA_A': ('Title01', 'Briefing01'),
          'M03_FA_A': ('Title02', 'Briefing02'), 'M06_FA_A': ('Title03', 'Briefing03')}
# controllers that only mark a place (cover, bounds): a campaign subtree made of them stays
PASSIVE = {'PlayerCoverCollision', 'NoCoverBox', 'LevelBound'}
# Where S's Heroes! groups go when a story level is the map (--heroes; a direct boot puts the
# player at a Heroes! group). The markers are the campaign's own checkpoint positions:
# M09_A CP_02 = inside the boardroom (re/retomoto.md 3.1), M09_B CP_01 = see 'sides M09_B'.
# ASSUMPTION: these are places a player can stand; nobody has stood there in Dog Days yet.
HERO_AT = {'M09_A': {'Markup!CP_02_PosP1': 'Heroes!Hero_01', 'Markup!CP_02_PosP2': 'Heroes!Hero_02'},
           'M09_B': {'Checkpoints!CP_01_PosP1': 'Heroes!Hero_01', 'Checkpoints!CP_01_PosP2': 'Heroes!Hero_02'}}
PSEUDO = {}                             # level name -> folder with <name>_Main.zip and the files beside it


# ------------------------------------------------------------------ story levels
def campaign_drop(level):
    """Top-level subtrees of a Dead Men story level that are campaign scripting -> (names to drop,
    {family: nodes} of what is dropped, the same of what stays)."""
    import glob
    import kl_prpjoin as J, kl_graft
    sc = J.Scene.load(level, 'dm')
    side, tpl = J.sides(sc), J.templates(sc)
    drop, gone, stay = [], collections.Counter(), collections.Counter()
    ctrls = lambda t: {sc.p.key(nm) for k in range(t, sc.end[t]) for nm, _b in sc.nodes[k]['ctrls']}
    cand = [t for t in sc.tops() if side[t] == 'map' and not sc.names[t].startswith('CloneGroup_')]   # a clone group follows its template
    keep = {t for t in cand if kl_graft.geometry(sc.names[t]) or sc.names[t].startswith(('Locations/', 'Effects/'))}
    passive = {t for t in cand if t not in keep and ctrls(t) and ctrls(t) <= PASSIVE}
    by_name = {sc.names[t].lower(): t for t in cand}
    for t in sorted(passive):
        # what a marker names: a script-free box (M09_B's LevelBound -> Warn01 / Warn02) comes
        # along; a marker that names anything scripted stays out with it
        named = {by_name.get(s[5:].split('\\')[0].lower()) for k in range(t, sc.end[t]) for _h, _f, u in J.fields(sc, k)
                 for s in J.strings(sc, u) if s[:5].upper() == 'ROOT\\'}
        if all(n is not None and (n in keep or n in passive or not ctrls(n)) for n in named):
            keep |= {t} | named
    for t in cand:
        name = sc.names[t]
        (stay if t in keep else gone)[J.family(name)] += sc.end[t] - t
        if t not in keep:
            drop.append(glob.escape(name))              # Select matches with fnmatch
    for t in sc.tops():                                 # clone groups, for the count only
        if side[t] == 'map' and sc.names[t].startswith('CloneGroup_'):
            top = sc.names[sc.top[tpl[t]]] if t in tpl else None
            fam = 'clone groups of dropped templates' if top and glob.escape(top) in drop else \
                  'clone groups of kept templates' if top else 'clone groups without a template'
            (gone if fam.endswith('dropped templates') else stay)[fam] += sc.end[t] - t
    return drop, dict(gone), dict(stay)


def redirect():
    """Stock-file lookups also find the levels in PSEUDO (a build of ours used as S), and such a
    level is all 'systems'. Process-wide; this file is the only caller."""
    import kl_prpjoin as J, kl_snd, kl_graft
    if getattr(J, '_kl_maps', False):
        return
    J._kl_maps = True
    r_zip, r_szip, r_beside, r_ls, r_stock, r_sides = J.level_zip, kl_snd.level_zip, kl_snd.beside, kl_snd.ls_files, kl_graft.stock_beside, J.sides
    at = lambda level, suffix: os.path.join(PSEUDO[level], level + '_Main' + suffix)
    J.level_zip = lambda level, game=None: at(level, '.zip') if level in PSEUDO else r_zip(level, game)
    kl_snd.level_zip = lambda level, game=None: at(level, '.zip') if level in PSEUDO else r_szip(level, game)
    kl_snd.beside = lambda level, suffix, game=None: ((at(level, suffix) if os.path.isfile(at(level, suffix)) else None)
                                                      if level in PSEUDO else r_beside(level, suffix, game))
    kl_snd.ls_files = lambda level, game=None: ({f[len(level) + 5:]: os.path.join(PSEUDO[level], f) for f in os.listdir(PSEUDO[level])
                                                 if f.startswith(level + '_Main_LS')} if level in PSEUDO else r_ls(level, game))
    kl_graft.stock_beside = lambda level, ext: at(level, ext) if level in PSEUDO else r_stock(level, ext)
    J.sides = lambda sc: (['root'] + ['systems'] * (len(sc.nodes) - 1)) if sc.label in PSEUDO else r_sides(sc)


# ------------------------------------------------------------------ two navigation meshes in one
def nav_facts(block):
    """Which indices of a Dog Days mesh are absolute: {rule: (holds, of)}. Every rule holds in
    all 21 stock Dog Days meshes (python kl_maps.py navtest); nav_join rests on them.
    NEW against kl_pf4's notes: tree 0 is one BSP PER AREA (root = area[9], its nodes run to
    the next area's root; leaf -1 = nothing, leaf c <= -2 = polygon -2 - c, a polygon of that
    area); area[1] / area[6] = count / first record of the area's vertices in array 6; array 10
    is a permutation inside each area's own waypoint range. So no array spans two areas."""
    import kl_pf4
    n, A = kl_pf4.split(block, True)
    areas = [struct.unpack('<12I', r[:48]) for r in A[4]]
    t0 = [struct.unpack('<ii', r[:8]) for r in A[0]]
    t1 = [struct.unpack('<ii', r[:8]) for r in A[1]]
    polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
    edges = [struct.unpack('<iII', r) for r in A[9]]
    perm = struct.unpack('<%dI' % n[10], b''.join(A[10]))
    c = collections.Counter()
    def rule(name, ok):
        c[name, 'of'] += 1; c[name, 'ok'] += bool(ok)
    for i, a in enumerate(areas):
        end = areas[i + 1][9] if i + 1 < len(areas) else n[0]
        rule('area: tree-0 root follows the last area\'s nodes', a[9] <= end)
        for j in range(a[9], end):
            for ch in t0[j]:
                if ch >= 0:
                    rule('tree 0: a child node lies in its area\'s node range', a[9] <= ch < end)
                elif ch < -1:
                    rule('tree 0: leaf -2 - c is a polygon of its area', a[7] <= -2 - ch < a[7] + a[2])
        rule('area: [6] = vertices of the areas before', a[6] == sum(x[1] for x in areas[:i]))
        rule('array 10: a permutation of the area\'s own waypoints', sorted(perm[a[5]:a[5] + a[0]]) == list(range(a[5], a[5] + a[0])))
        for p in polys[a[7]:a[7] + a[2]]:
            rule('polygon: its edges name vertices of its area', all(a[6] <= e[1] < a[6] + a[1] for e in edges[p[5]:p[5] + p[0]]))
            rule('polygon: tree-1 node not above area[10]', p[8] <= a[10])
    rule('areas: vertex counts add up to array 6', sum(a[1] for a in areas) == n[6])
    rule('tree 1: -1 - c of the leaves covers array 2 to its last record',
         max([-1 - ch for r in t1 for ch in r if ch < 0] or [-1]) == n[2] - 1)
    return {k: (c[k, 'ok'], c[k, 'of']) for k, _x in c if _x == 'of'}


def nav_join(a, b):
    """Two Dog Days mesh blocks (no size dword) -> one: b's areas behind a's, every absolute
    index of b moved by a's counts (nav_facts says which are absolute). EXPERIMENT, not loaded
    by the game yet. ASSUMPTIONS: the game finds the area of a point from the area records
    alone (their boxes) - nothing in the file spans areas, arrays 8 / 11 / 12 are empty; and
    the order of areas carries no meaning beyond the running sums kl_pf4.check tests.
    No link joins the two parts: an AI cannot walk from one to the other (for Retomoto that is
    the design: the parts are 190 m apart in height)."""
    import kl_pf4
    na, A = kl_pf4.split(a, True)
    nb, B = kl_pf4.split(b, True)
    P = struct.pack
    def tree(r, node, leaf, none):
        c1, c2 = struct.unpack_from('<ii', r)
        mv = lambda c: c + node if c >= 0 else c if c in none else c - leaf
        return P('<ii', mv(c1), mv(c2)) + r[8:]
    out = [list(x) for x in A]
    out[0] += [tree(r, na[0], na[3], (-1,)) for r in B[0]]          # leaf -2 - c = polygon, -1 = nothing
    out[1] += [tree(r, na[1], na[2], ()) for r in B[1]]             # leaf -1 - c = array-2 record
    out[2] += B[2]
    for r in B[3]:
        v = list(struct.unpack('<BBHIIIIIII', r))
        v[4] += na[4]; v[5] += na[9]; v[6] += na[5]; v[8] += na[1]
        out[3].append(P('<BBHIIIIIII', *v))
    for r in B[4]:
        v = list(struct.unpack('<12I', r[:48]))
        for k, arr in ((5, 5), (6, 6), (7, 3), (9, 0), (10, 1), (11, 2)):
            v[k] += na[arr]
        out[4].append(P('<12I', *v) + r[48:])
    for r in B[5]:
        lo, hi, poly = struct.unpack_from('<III', r, 12)
        out[5].append(r[:12] + P('<III', lo + na[7], hi + na[7], poly + na[3]) + r[24:])
    out[6] += B[6]
    for r in B[7]:
        cost, junk, number, area, kind, heading, switch = struct.unpack('<hHiiBBH', r)
        out[7].append(P('<hHiiBBH', cost, junk, number, area + na[4], kind, heading, switch))
    for r in B[9]:
        nbr, vertex, link = struct.unpack('<iII', r)
        out[9].append(P('<iII', nbr + na[3] if nbr >= 0 else nbr if nbr == -1 else nbr - na[3], vertex + na[6], link))
    out[10] += [P('<I', struct.unpack('<I', r)[0] + na[5]) for r in B[10]]
    data = kl_pf4.join(out)
    kl_pf4.check(data)
    bad = {k: v for k, v in nav_facts(data).items() if v[0] != v[1]}
    if bad:
        raise ValueError('joined navigation mesh breaks %s' % bad)
    return data


def nav_of(level):
    """Dog Days mesh block of a stock Dog Days level or a level in PSEUDO, or None."""
    import kl_prpjoin as J, kl_gms, kl_scene
    redirect()
    with zipfile.ZipFile(J.level_zip(level)) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        return kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf'])).nav


def navtest(log=print):
    """nav_facts on every stock Dog Days mesh, then nav_join of two of them (F07 + F09) and of
    each with itself: kl_pf4.check and nav_facts must hold on the result. -> rules broken."""
    import kl_pf4
    levels = DD_FA + ['L%02d' % i for i in range(12)]
    tot, navs = collections.Counter(), {}
    for lv in levels:
        try:
            navs[lv] = nav_of(lv)
        except FileNotFoundError:
            continue
        for k, (ok, of) in nav_facts(navs[lv]).items():
            tot[k, 'ok'] += ok; tot[k, 'of'] += of
    log('%d stock meshes' % len(navs))
    broken = 0
    for k in sorted({k for k, _x in tot}):
        log('  %-58s %7d of %7d' % (k, tot[k, 'ok'], tot[k, 'of']))
        broken += tot[k, 'ok'] != tot[k, 'of']
    for x, y in (('F07', 'F09'), ('F09', 'F07'), ('F04', 'F04')):
        j = nav_join(navs[x], navs[y])
        n = kl_pf4.counts(j, True)
        log('  join %s + %s: check passes; %d areas, %d polygons, %d waypoints, %d links, %d bytes' % (x, y, n[4], n[3], n[5], n[7], len(j)))
    return broken


# ------------------------------------------------------------------ one build
def measure(folder, slot=SLOT):
    """The numbers of a built level, read back from its files."""
    import kl_gms, kl_scene, kl_texmat as T, kl_snd, kl_fa, kl_prmgraph as G, kl_graft
    zp = os.path.join(folder, slot + '_Main.zip')
    out = {'archive_mb': round(os.path.getsize(zp) / 1e6, 1)}
    out['beside_mb'] = round(sum(os.path.getsize(os.path.join(folder, f)) for f in os.listdir(folder)
                                 if f.startswith(slot + '_Main') and f != slot + '_Main.zip') / 1e6, 1)
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        rd = lambda e: z.read(m[e])
        out['member_mb'] = {e: round(z.getinfo(n).file_size / 1e6, 1) for e, n in m.items() if z.getinfo(n).file_size > 1e6}
        sc = kl_scene.Scene(kl_gms.unpack(rd('.gms')), rd('.buf'))
        ents = list(sc.entities())
        out['entities'] = len(ents)
        out['rooms'] = sum(kl_graft.is_room(e.tid) for e in ents)
        out['ref_slots'] = sc.ref_slots
        out['nav_bytes'] = len(sc.nav) if sc.nav is not None else 0
        out['fdx'] = sc.fdx is not None
        out['textures'] = len(T.read_tex(rd('.TEX')).tex)
        out['materials'] = len(T.read_mat(rd('.MAT')).insts)
        out['prm_chunks'] = len(G.read(rd('.prm'), 'dd').chunks) - 1
        snd = kl_snd.Snd('dd', rd('.SND')).walk()
        out['sounds'], out['waves'] = len(snd.tables.get(1, ())), len(snd.tables.get(4, ()))
    s, snd, loc = kl_fa.load(zp)
    fs = kl_fa.check(s, snd, loc)
    ctrl, cls = kl_fa.census(s)
    out['fa'] = dict(collections.Counter(kl_fa.SEV[f.sev] for f in fs))
    out['fa_findings'] = [str(f) for f in fs]
    out['escape'] = {k: v for c in (ctrl, cls) for k, v in c.items()
                     if k and any(w in k for w in ('OnlineEsc', 'OnlineExit', 'OnSpline', 'ZHeli', 'ZHavokCar', 'ZAnimatedVehicle', 'AllyEscape'))}
    return out


def one(out, s_name, m_name, keep=False, campaign=False, heroes=False, slot=SLOT, tag='', nav_base=None, **opt):
    """Build S + M into <out>/<S>+<M><tag>/ and write result.json. -> the result dict."""
    import kl_graft, kl_prpjoin as J
    redirect()
    folder = os.path.join(out, '%s+%s%s' % (s_name, m_name, tag))
    os.makedirs(folder, exist_ok=True)
    lines, t0 = [], time.time()
    def log(s=''):
        lines.append(str(s)); print(s, flush=True)
    res = {'S': s_name, 'M': m_name, 'ok': False, 'options': {k: (list(v) if isinstance(v, tuple) else v) for k, v in opt.items()},
           'campaign': campaign, 'heroes': heroes, 'tag': tag}
    real_out, real_verify, real_dm = kl_graft.out_dir, kl_graft.verify, kl_graft.DeadMen
    kl_graft.out_dir = lambda _slot: folder             # never <work>/build/install

    def verify(o, Jn, *a, **k):                         # the whole list; verify() shows the first ten
        bad = real_verify(o, Jn, *a, **k)
        _d, _misfits, paths, names = J.check(Jn, log=lambda *_a: None)
        res['dangling'] = sorted('%s: %s %s -> %s' % (Jn.path[kk], h, f, t) for kk, h, f, t in paths)
        res['dangling_templates'] = len(names)
        M = a[1]                                        # verify(out, Jn, S, M, ...)
        stock = {s.lower() for _k, _h, _f, s in J.dangling(M.prp)[1]}
        res['dangling_templates_new'] = dict(collections.Counter(
            '%s (emitter under %s)' % (s, Jn.names[Jn.top[kk]]) for kk, _h, _f, s in names if s.lower() not in stock))
        res['tops'] = len(Jn.tops())
        return bad

    class Story(real_dm):
        """The level's HERO_AT markers under the names (and class) of S's Heroes! groups: picks_of
        then puts S's group in the marker's place and build() gives it the marker's rotation and
        position, exactly as it does for a Fragile Alliance map's own Heroes! groups."""
        def __init__(self, name, log=print):
            super().__init__(name, log)
            from kl_prp import units
            group = next(t for t, c in J.schema('dd').geoms.items() if c == 'ZGROUP')
            lab = kl_graft.labels('ZGROUP')
            # the marker becomes a plain ZGROUP (properties of a model-less group of this level
            # with the marker's rotation and position): build() wants S's class on M's node
            like = next(k for k in self.prp.tops() if self.prp.tids[k] == group and not self.ents[k - 1].model)
            for src, dst in (HERO_AT.get(name, {}) if heroes else {}).items():
                t = next(t for t in self.prp.tops() if self.prp.names[t] == src)
                mine, us = units(self.prp.nodes[t]['props'][1:-1]), [list(u) for u in units(self.prp.nodes[like]['props'][1:-1])]
                for l in ('ZGEOM[1]', 'ZGEOM[2]'):
                    us[lab.index(l)] = list(mine[lab.index(l)])
                p = self.prp.nodes[like]['props']
                self.prp.nodes[t]['props'] = [p[0]] + [x for u in us for x in u] + [p[-1]]
                self.prp.nodes[t]['ctrls'] = []
                self.prp.names[t], self.prp.tids[t] = dst, group
                log('  kl_maps: %s stands at %s %s' % (dst, src, tuple(round(v) for v in struct.unpack('<3f', self.ents[t - 1].trans[:12]))))
            if nav_base is not None and self.scene.nav is not None:
                # build() gives the level M's mesh ('A.nav = B.nav'): hand it both
                n0 = len(self.scene.nav)
                self.scene.nav = nav_join(nav_base, self.scene.nav)
                log('  kl_maps: navigation mesh = that of %s (%d bytes) + that of %s (%d bytes), nav_join (EXPERIMENT)' % (s_name, len(nav_base), name, n0))

    import kl_snd, kl_whd as W
    real_merge = kl_snd.merge

    def merge(base, src, base_whd, base_wav, src_whd, src_wav, roots, *a, **k):
        """kl_snd.merge counts the stream clips the merged PC_Def.str lacks; this names them
        (the waves that came along and whose streamed record has no place in the stream map)."""
        r = real_merge(base, src, base_whd, base_wav, src_whd, src_wav, roots, *a, **k)
        count = (k.get('stats') or {}).get('stream clips not in the merged stream file', 0)
        if src.game != base.game and count:             # kl_snd's count decides; the names are a reconstruction
            recs, strmap, lost = W.records(src.game, src_whd), kl_snd.stream_map(), set()
            for o, _i, off in src.waves():
                f = recs.get(off)
                if o in r[3] and f and f['fmt'] & W.STREAMED and (f['fmt'] & W.LANGFILE or f['off'] not in strmap):
                    lost.add(kl_snd.cs(src_whd, f['name']).decode('latin1'))
            res['stream_clips_missing'] = sorted(lost)
            res['stream_clips_missing_count'] = count   # equal to len() in both M09 parts
        return r

    kl_graft.verify, kl_graft.DeadMen, kl_snd.merge = verify, Story, merge
    try:
        m_drop = tuple(opt.pop('m_drop', ()))
        if campaign:
            names, gone, stay = campaign_drop(m_name)
            m_drop += tuple(names)
            res['campaign_dropped'], res['campaign_kept'] = gone, stay
            log('campaign pre-pass: %d subtrees dropped %s; kept %s' % (len(names), gone, stay))
        sel = kl_graft.Select(opt.pop('geometry', False), m_add=opt.pop('m_add', ()), m_drop=m_drop)
        _path, problems = kl_graft.build(s_name, m_name, slot, log=log, sel=sel, **opt)
        res.update(ok=True, problems=problems, **measure(folder, slot))
        res['notes'] = [l.strip()[6:] for l in lines if l.strip().startswith('note: ')]
    except Exception as x:
        log(traceback.format_exc())
        frames = traceback.extract_tb(x.__traceback__)
        res.update(error='%s: %s' % (type(x).__name__, x),
                   where=['%s:%d %s' % (os.path.basename(f.filename), f.lineno, f.name) for f in frames[-4:]])
    finally:
        kl_graft.out_dir, kl_graft.verify, kl_graft.DeadMen, kl_snd.merge = real_out, real_verify, real_dm, real_merge
    res['seconds'] = round(time.time() - t0)
    if not keep:
        for f in os.listdir(folder):
            if f.startswith(slot + '_Main'):
                os.remove(os.path.join(folder, f))
    with open(os.path.join(folder, 'log.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    with open(os.path.join(folder, 'result.json'), 'w') as f:
        json.dump(res, f, indent=1)
    return res


def chain(out, s_name, m1, m2, campaign=True, heroes=False, keep=False, **opt):
    """Three sources: S + M1 -> <out>/chain/ as level R09 (kept: it is the S of the second step),
    then R09 + M2 -> <out>/R09+<M2> (R09 = <S>+<M1>)/."""
    mid = os.path.join(out, 'chain')
    r1 = one(mid, s_name, m1, keep=True, campaign=campaign, slot='R09', **dict(opt))
    if not r1['ok']:
        return r1
    PSEUDO['R09'] = os.path.join(mid, '%s+%s' % (s_name, m1))
    tag = ' (R09 = %s+%s)' % (s_name, m1)
    r2 = one(out, 'R09', m2, keep=keep, campaign=campaign, heroes=heroes, tag=tag, nav_base=nav_of('R09'), **dict(opt))
    r2['first'] = {k: r1.get(k) for k in ('problems', 'entities', 'textures', 'materials', 'sounds', 'waves', 'archive_mb', 'nav_bytes', 'fdx')}
    with open(os.path.join(out, 'R09+%s%s' % (m2, tag), 'result.json'), 'w') as f:
        json.dump(r2, f, indent=1)
    return r2


# ------------------------------------------------------------------ many builds, the table
def run_many(out, jobs, par=3):
    """jobs: [(S, M, [options])]; each in a process of its own, `par` at a time."""
    os.makedirs(out, exist_ok=True)
    todo, live = list(jobs), []
    while todo or live:
        while todo and len(live) < par:
            s, m, o = todo.pop(0)
            f = open(os.path.join(out, 'stdout %s+%s%s.txt' % (s, m, ''.join(' ' + x.strip('-') for x in o))), 'w')
            live.append((s, m, f, subprocess.Popen([sys.executable, os.path.abspath(__file__), 'one', out, s, m] + list(o),
                                                   stdout=f, stderr=subprocess.STDOUT)))
        time.sleep(2)
        for j in [j for j in live if j[3].poll() is not None]:
            live.remove(j); j[2].close()
            print('%s + %s: exit %d' % (j[0], j[1], j[3].returncode), flush=True)
    table(out)


def results(out):
    rs = []
    for d in sorted(os.listdir(out)):
        p = os.path.join(out, d, 'result.json')
        if os.path.isfile(p):
            rs.append(json.load(open(p)))
    return rs


def table(out, log=print):
    """One markdown table of everything built in <out>."""
    log('| S + M | problems | FA crash/broken/degraded/note | archive MB | beside MB | entities | rooms | textures /4096 | materials /2048 | sounds | waves | s |')
    log('|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    title = lambda r: '%s + %s%s' % (r['S'], r['M'], r.get('tag', ''))
    for r in results(out):
        if not r['ok']:
            log('| %s | FAILED | %s at %s | | | | | | | | | %d |' % (title(r), r['error'][:110], r['where'][-1], r['seconds']))
            continue
        fa = r['fa']
        log('| %s | %d | %d / %d / %d / %d | %.0f | %.0f | %d | %d | %d | %d | %d | %d | %d |' % (
            title(r), len(r['problems']), fa.get('CRASH', 0), fa.get('BROKEN', 0), fa.get('DEGRADED', 0), fa.get('NOTE', 0),
            r['archive_mb'], r['beside_mb'], r['entities'], r['rooms'], r['textures'], r['materials'], r['sounds'], r['waves'], r['seconds']))
    for r in results(out):
        for p, n in collections.Counter(x if len(x) < 170 else x[:170] + ' ...' for x in r.get('problems', [])).items():
            log('  %s PROBLEM%s: %s' % (title(r), ' x%d' % n if n > 1 else '', p))


# ------------------------------------------------------------------ looking at levels
def world(scene):
    """{entity: (x, y, z)} world position, composed down the tree. Rotation = record +4, nine
    floats, used as rows (hbm-editor gms/placements.ts reverses and transposes them: the same
    matrix); checked on M09_A against re/retomoto.md (boardroom window at x 5850, y 21000)."""
    pos = {}
    def go(e, R, T):
        r = struct.unpack('<9f', e.rot[:36]); t = struct.unpack('<3f', e.trans[:12])
        m = [r[6:9], r[3:6], r[0:3]]                    # rows reversed ...
        m = [[m[j][i] for j in range(3)] for i in range(3)]   # ... then transposed
        p = tuple(T[i] + sum(R[i][j] * t[j] for j in range(3)) for i in range(3))
        R2 = [[sum(R[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        pos[e] = p
        for c in e.kids:
            go(c, R2, p)
    for e in scene.roots:
        go(e, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], (0.0, 0.0, 0.0))
    return pos


def what(level, log=print):
    """What a level is, from its own data: Dead Men's menu title and briefing, rooms with the
    extent of the entities under them, escape vehicles, loot, and the words its map names use."""
    import re
    import kl_prpjoin as J, kl_gms, kl_scene, kl_loc
    game = 'dm' if level.startswith('M') else 'dd'
    sc = J.Scene.load(level, game)
    with zipfile.ZipFile(J.level_zip(level, game)) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
        if level in TITLES:
            want = {'AllLevels/Menu/Online/Scenarios/' + x for x in TITLES[level]}
            for p, k in kl_loc.leaves(kl_loc.parse(z.read(kl_loc.members(z)['English']))):
                if p in want:
                    log('%s: %s' % (p.rsplit('/', 1)[1], (kl_loc.fields(k)[0] or b'').decode('latin1')))
    ents, side = list(scene.entities()), J.sides(sc)
    pos = world(scene)
    log('%s: %d entities' % (level, len(ents)))
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) in ('ZROOM', 'ZBackdrop') and side[k] == 'map':
            ps = [pos[ents[j - 1]] for j in range(k, sc.end[k]) if ents[j - 1].model]
            box = ' x %d..%d y %d..%d z %d..%d' % tuple(round(f(p[i] for p in ps)) for i in range(3) for f in (min, max)) if ps else ''
            log('  room %-34s %5d entities%s' % (sc.names[k], sc.end[k] - k, box))
    ctrl = collections.Counter(sc.p.key(nm) for k in range(1, len(sc.nodes)) if side[k] == 'map' for nm, _b in sc.nodes[k]['ctrls'])
    cls = collections.Counter(sc.cls(k) for k in range(1, len(sc.nodes)) if side[k] == 'map')
    log('  escape / loot: %s' % {k: v for c in (ctrl, cls) for k, v in c.items() if k and any(
        w in k for w in ('OnlineEsc', 'OnlineExit', 'OnSpline', 'ZHeli', 'ZHavokCar', 'ZAnimatedVehicle', 'OnlineMoney', 'Spawnpoint', 'SpawnPoint'))})
    words = collections.Counter(w for k in range(1, len(sc.nodes)) if side[k] == 'map' and sc.parent[k] and not sc.names[sc.top[k]].startswith('CloneGroup_')
                                for w in re.findall(r'[A-Za-z]{4,}', sc.names[k]))
    log('  words: ' + ', '.join('%s %d' % x for x in words.most_common(70)))


def sides(level, log=print):
    """kl_prpjoin.sides() on a level, per family; for a story level also what campaign_drop does."""
    import kl_prpjoin as J
    game = 'dm' if level.startswith('M') else 'dd'
    sc = J.Scene.load(level, game)
    side = J.sides(sc)
    fam = collections.Counter()
    for t in sc.tops():
        fam[side[t], J.family(sc.names[t])] += sc.end[t] - t
    log('%s: %d entities; kl_prpjoin.sides:' % (level, len(sc.nodes) - 1))
    for (s, f), n in sorted(fam.items(), key=lambda x: (x[0][0], -x[1])):
        log('  %-8s %6d  %s' % (s, n, f))
    if game == 'dm':
        names, gone, stay = campaign_drop(level)
        log('campaign pre-pass: %d subtrees dropped, %d nodes; %d nodes stay' % (len(names), sum(gone.values()), sum(stay.values())))
        log('  dropped: %s' % sorted(gone.items(), key=lambda x: -x[1]))
        log('  kept:    %s' % sorted(stay.items(), key=lambda x: -x[1]))


def clash(a, b, log=print):
    """Top-level names both maps would bring (after the campaign pre-pass)."""
    import glob
    import kl_prpjoin as J
    keep = {}
    for lv in (a, b):
        sc = J.Scene.load(lv, 'dm')
        side, tpl = J.sides(sc), J.templates(sc)
        drop = set(campaign_drop(lv)[0])
        keep[lv] = {}
        for t in sc.tops():
            own = sc.names[sc.top[tpl[t]]] if t in tpl else sc.names[t]
            if side[t] == 'map' and glob.escape(own) not in drop:
                keep[lv][sc.names[t]] = (sc.end[t] - t, sc.cls(t), 'template in ' + own.split('\\')[0] if t in tpl else '')
    both = sorted(set(keep[a]) & set(keep[b]))
    log('%s keeps %d top-level subtrees, %s %d; %d names in both:' % (a, len(keep[a]), b, len(keep[b]), len(both)))
    for n in both:
        log('  %-70s %s %s | %s %s' % (n, keep[a][n][0], keep[a][n][2], keep[b][n][0], keep[b][n][2]))
    return both


def hostfacts(m_name='M03_FA_A', log=print):
    """What differs between the stock Fragile Alliance levels as S (kl_graft.pairs covers two
    Dog Days levels; this adds what matters under a Dead Men map)."""
    import kl_graft, kl_prpjoin as J, kl_anm, kl_fa, kl_prmgraph as G
    used = None
    if m_name:
        sc = J.Scene.load(m_name)
        side = J.sides(sc)
        used = {sc.p.keys[kl_graft.u32(t)] for k in range(1, len(sc.nodes)) if side[k] == 'map'
                for toks in [sc.nodes[k]['props']] + [b for _n, b in sc.nodes[k]['ctrls']]
                for t in toks if t[0] == 0x0c and sc.p.keys[kl_graft.u32(t)].startswith(kl_anm.PREFIX)}
        log('%s map names animation sets: %s' % (m_name, sorted(x[len(kl_anm.PREFIX):] for x in used)))
    pal = {}
    for L in DD_FA:
        lv = kl_graft.Level(L)
        blk = dict(J.block(lv.prp))
        prm = G.read(lv['.prm'], 'dd')
        pal[L] = prm.chunks[[kl_graft.u32(t) for t in blk['PostFilterPalettes'] if t[0] == 9][-1]]
        cols = {c.name for c in kl_anm.Anm(lv['.ANM'], 'dd').cols}
        ctrl, cls = kl_fa.census(lv.prp)
        dang = J.dangling(lv.prp)
        sysn = sum(1 for k in range(1, len(lv.prp.nodes)) if lv.side[k] == 'systems')
        log('%s: systems %d nodes; palette = %s; FDX %s; vehicle %s; kept by kl_fa %d (monitor %s); .ANM lacks %s' % (
            L, sysn, next(k for k in DD_FA if pal.get(k) == pal[L]), lv.scene.fdx is not None,
            'ZHeli + OnlineEscHavokCar' if cls.get('ZHeli') else 'ZAnimatedVehicle',
            len(kl_fa.host_keep(lv.prp)), any('onitor' in n and 'AIMonitor' not in n for n in kl_fa.host_keep(lv.prp)),
            sorted(x[len(kl_anm.PREFIX):] for x in (used or set()) - cols)))


def main():
    a = sys.argv[1:]
    par = 3
    if '-j' in a:
        i = a.index('-j'); par = int(a[i + 1]); del a[i:i + 2]
    if (len(a) >= 4 and a[0] == 'one') or (len(a) >= 5 and a[0] == 'chain'):
        opt = {}
        for o in ('--m-add', '--m-drop'):
            while o in a:
                i = a.index(o); opt[o[2:].replace('-', '_')] = tuple(opt.get(o[2:].replace('-', '_'), ())) + tuple(a[i + 1].split(',')); del a[i:i + 2]
        if '--light' in a:
            i = a.index('--light'); opt['light'] = None if a[i + 1] == 'off' else a[i + 1]; del a[i:i + 2]
        flag = lambda f: (f in a, a.remove(f) if f in a else None)[0]
        if flag('--silent'): opt['sound'] = False
        if flag('--no-loc'): opt['loc'] = False
        if flag('--no-fa'): opt['fa'] = False
        if flag('--stock-anm'): opt['anim'] = False
        if flag('--geometry'): opt['geometry'] = True
        keep, campaign, heroes = flag('--keep'), flag('--campaign'), flag('--heroes')
        if a[0] == 'chain':
            r = chain(a[1], a[2], a[3], a[4], heroes=heroes, keep=keep, **opt)
        else:
            r = one(a[1], a[2], a[3], keep=keep, campaign=campaign, heroes=heroes, tag=' campaign' if campaign else '', **opt)
        sys.exit(0 if r['ok'] and not r['problems'] else 1)
    elif len(a) >= 2 and a[0] == 'maps':
        run_many(a[1], [('F07', m, []) for m in DM_FA], par)
    elif len(a) >= 2 and a[0] == 'hosts':
        m = a[2] if len(a) > 2 else 'M03_FA_A'
        run_many(a[1], [(s, m, []) for s in DD_FA], par)
    elif len(a) >= 2 and a[0] == 'm09':
        run_many(a[1], [('F07', m, o) for m in ('M09_A', 'M09_B') for o in ([], ['--campaign', '--heroes'])], par)
    elif a and a[0] == 'navtest':
        sys.exit(1 if navtest() else 0)
    elif len(a) >= 2 and a[0] == 'table':
        table(a[1])
    elif len(a) >= 2 and a[0] == 'what':
        what(a[1])
    elif len(a) >= 2 and a[0] == 'sides':
        sides(a[1])
    elif len(a) >= 3 and a[0] == 'clash':
        clash(a[1], a[2])
    elif a and a[0] == 'hostfacts':
        hostfacts(*a[1:2])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
