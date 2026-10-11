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
                                                          (--author: with kl_fa_author's FA layer = Retomoto Tower;
                                                          --author <module>: with that module's, see 'one')
    python kl_maps.py table <out>                         the table of everything built in <out>
    python kl_maps.py what M06_FA_A                       what a level is: title, rooms, extent, names
    python kl_maps.py sides M09_A                         how kl_graft splits a level's subtrees and
                                                          what the campaign pre-pass drops
    python kl_maps.py hostfacts [M03_FA_A]                what differs between the stock hosts
    python kl_maps.py clash M09_A M09_B                   top-level names two maps share
    python kl_maps.py navtest                             the rules nav_join rests on, on every
                                                          stock mesh, and three trial joins
    python kl_maps.py first M02_FA_A                      classes / controllers of a Dead Men map that
                                                          no map which ran live has (PROVEN)
    python kl_maps.py preflight <out>/F07+M02_FA_A        every offline check on a KEPT build and the
                                                          predicted risks (re/maps.md section 9);
                                                          exit code 1 on a CRASH finding
    python kl_maps.py deliver <out> [-j N]                the kept builds for the first live runs of
                                                          M02_FA_A and M06_FA_A + their preflight
    python kl_maps.py ready <out> [M01 M03 ...] [-j 2]    THE FOUR FA MAPS READY TO INSTALL (re/maps.md 14): each
                                                          built with every fix and the voices on, lightened,
                                                          the wardrobe on top, every checker -> <out>/<M01|..>/
    python kl_maps.py audit <folder>                      every checker and the numbers on a finished folder
    python kl_maps.py readytable <out>                    the table of section 14 from the audits
    python kl_maps.py bots [F07 ...]                      a stock level's AI heister squad: nodes, route, what it names
    python kl_maps.py stations <folder> ...               a built map's round stations on its navigation mesh (14.5)
    python kl_maps.py stage <out>/F07+M02_FA_A            LIVE SIDE ONLY: copy a kept build into
                                                          <work>/build/install (then kl_graft.py install)
  options of 'one':  --keep        leave the archive and the files beside it (default: measured,
                                   then deleted - a build is 0.3 .. 0.4 GB)
                     --campaign    the campaign pre-pass (campaign_drop) for a story level
                     --heroes      S's Heroes! groups at the level's HERO_AT markers
                     --author [module]   an authored Fragile Alliance layer (kl_graft.build's `author`, where
                                   the module's interface is written down): alone = kl_fa_author (Retomoto
                                   Tower), with a name = that module of tools/, e.g. 'one <out> F07 M03_A
                                   --campaign --author kl_fa_bank --keep'. With --campaign the module's
                                   campaign_names() stay out of the pre-pass. The name follows the option directly
                     --flat ZEnvSampler   load that Dead Men class as its base class (FLAT)
                     kl_graft's own: --silent --no-loc --no-fa --stock-anm --light X
                     --m-drop A,B  --m-add A,B

Each build runs in a process of its own (a failure is a row of the table, not the end of the
run). <out>/<S>+<M>/result.json holds the numbers, log.txt what kl_graft printed.

BEFORE A FIRST LIVE RUN (preflight; re/maps.md sections 9 and 10)
  On a kept build: kl_fa.check, kl_light.check / missing_shaders, torn stream groups, and the
  crashes the diner and the bank hit looked for by their cause - events that delete themselves at
  init (OnlineSpeakTrigger, OnlineMoneyContainer, PhysicsLinkage), KEYS chunks keys_tracks does
  not find, controllers on a node outside their class - then what the map has that no map in
  PROVEN has (first_timers), with the checks read off kl2.exe for those: ZEnvSampler slots,
  SoundSpline's sound, squad behaviours under a squad, filter sets inside S's palette, the .sgd
  sections every stock level has. Nothing is changed; the fix that is a pre-pass is --flat.

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
  (Effects/*) and not a passive marker (PASSIVE: cover and level-bound boxes without a script,
  and the level's cover list where it sits in a campaign subtree).
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
# Dead Men's own names (AllLevels/Menu/Online/Scenarios/TitleNN + BriefingNN of its .LOC). The
# order is the exe's: kaneandlynch.exe 0x6415a3 builds the array M01_FA_A, M02_FA_A, M03_FA_A,
# M06_FA_A and the titles are fetched as 'Title%02d' (re/maps.md section 2); content agrees -
# Briefing03 speaks of the Japanese Gardens and a chopper, and M06_FA_A is the one map with ZHeli
# escape vehicles and 299 'DopeBag' loot objects
TITLES = {'M01_FA_A': ('Title00', 'Briefing00'), 'M02_FA_A': ('Title01', 'Briefing01'),
          'M03_FA_A': ('Title02', 'Briefing02'), 'M06_FA_A': ('Title03', 'Briefing03')}
# controllers that only mark a place (cover, bounds): a campaign subtree made of them stays.
# FFCoverList is the level's cover list itself (one ZLIST node, no field, names nothing; the game makes
# a cover of every '*coverbox*' object through it at load). Most levels have it as the top-level
# 'CoverList', which is never a candidate here; M03_A (Special!CoverList), M06_A, M12_A, M13_B
# (Specials!CoverPoints!CoverControl) and M07_A (Special!CoverPoints!CoverControl) keep it in a campaign
# subtree, and without this entry the pre-pass dropped their ONLY list: M03_A's 118 and M06_A's 225
# kept cover boxes were covers for nobody (re/campaign_fa_tooling.md 5.5; nothing else changes on any
# of the 20 levels: re/bank_campaign.md T1.2). A layer that keeps the host's Specials! must drop the
# host's list then (kl_fa_author.DROP): a second FFCoverList is an assert, and verify() counts them.
PASSIVE = {'PlayerCoverCollision', 'NoCoverBox', 'LevelBound', 'FFCoverList'}
# Where S's Heroes! groups go when a story level is the map (--heroes; a direct boot puts the
# player at a Heroes! group). The markers are the campaign's own checkpoint positions:
# M09_A CP_02 = inside the boardroom (re/retomoto.md 3.1), M09_B CP_01 = see 'sides M09_B'.
# M03_A (the bank the campaign way): the secure yard the round starts in. The yard holds ONE
# top-level marker of the level, the developers' jump point behind the rappel, (-313, 205, -4398):
# on the yard's part of the navigation mesh (4 above its polygon), 6 m west of the study's START
# place (300, 200, -4350) (re/campaign_fa_bank.md 1.3, 4.3; re/bank_campaign.md T1.3). one() takes
# its JumpPoint controller off with the retyping. The yard is shut by the dock's roller door: a bare
# direct boot stands locked in there until that door is opened. No second marker: Hero_02 stays at F07's place.
# ASSUMPTION: these are places a player can stand; nobody has stood there in Dog Days yet.
HERO_AT = {'M09_A': {'Markup!CP_02_PosP1': 'Heroes!Hero_01', 'Markup!CP_02_PosP2': 'Heroes!Hero_02'},
           'M09_B': {'Checkpoints!CP_01_PosP1': 'Heroes!Hero_01', 'Checkpoints!CP_01_PosP2': 'Heroes!Hero_02'},
           'M03_A': {'Special!JumpPoints!Jump#060': 'Heroes!Hero_01'}}
PSEUDO = {}                             # level name -> folder with <name>_Main.zip and the files beside it
# Dead Men maps that have run live under F07 (kl_graft's run log: B-4 / M01c, and F1 .. RN6 with a
# whole Arcade round). What a map has beyond these the game meets for the first time: first_timers.
PROVEN = ('M01_FA_A', 'M03_FA_A')
# the largest of each in a Dead Men build that ran live (F07 + M03_FA_A; the mesh is M03's)
LIVE = {'entities': 19827, 'rooms': 20, 'sounds': 4918, 'waves': 4782, 'nav_bytes': 186672}
SQUADS = ('ZSquadScript', 'ZMercSquad', 'ZFusionSquad', 'ZProxySquad')    # what kl2 0x4aff50 looks for on the parent
# owner mismatches whose init was read: ZGatePath (kl2 0x449120) asks its PARENT for a 'GateGroup'
# controller and its own node only for a list; nothing treats the node as a ZGROUP there
OWNER_READ = ('GatePath (registered for ZGROUP) on ZBoxPrimitive',)
# --flat: Dead Men classes loaded as their base for one build (an entry of kl_gms.RETYPE for the
# length of the build, the bisect its comment describes). ZEnvSampler -> ZSTDOBJ keeps the game
# from building ZRenderEntryEnvSamplerD3D objects, which no stock Dog Days level has (re/maps.md 9.3).
FLAT = {'ZEnvSampler': (0x20010f, 0x200002)}


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
    is a permutation inside each area's own waypoint range. So no array spans two areas.
    Tree 1 (20-byte nodes) is one tree per polygon (root = polygon[8]) with RELATIVE children."""
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
    # tree 1: one tree per polygon, children relative to its root; the trees share no node and
    # cover the array (F07 940 trees / 1624 nodes; read absolute, 340 of them overlap or leave it)
    cover, clean = set(), True
    for root in sorted({p[8] for p in polys}):
        seen, todo = set(), [0]
        while todo and clean:
            i = todo.pop() + root
            clean = i not in seen and i not in cover and 0 <= i < n[1]
            if clean:
                seen.add(i)
                todo += [ch for ch in t1[i] if ch >= 0]
        cover |= seen
    rule('tree 1: per polygon, children relative to its root, no node shared, all covered', clean and len(cover) == n[1])
    # polygon byte +1 = how many waypoints name the polygon, and array 10 from 'waypoints before' on names exactly
    # them: what the path search's polygon step reads (kl2 0x5ce320..0x5ce3a7). Found 2026-10-11 through a
    # hand-written link no AI took (kl_fa_bots.add_drop left the byte at 0; re/bots_bank.md 1).
    own = collections.defaultdict(list)
    for wi, r in enumerate(A[5]):
        own[struct.unpack_from('<I', r, 0x14)[0]].append(wi)
    for i, p in enumerate(polys):
        rule('polygon: byte +1 = the waypoints that name it', p[1] == len(own.get(i, ())))
        if own.get(i):
            rule('polygon: array 10 from its \'waypoints before\' names its waypoints', sorted(perm[p[6]:p[6] + p[1]]) == own[i])
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
    # tree 1 is one small tree PER POLYGON and a child >= 0 is RELATIVE to the polygon's root
    # (polygon[8]): kl2 0x55f5c7 'add edx, edi' with edi = [polygon + 0x18]. Only the leaves
    # (-1 - c = array-2 record, absolute) move. The first join shifted the children too and the
    # height lookup of the first actor never came back (run RT1b / RT1c: stuck at Buffering 69 %,
    # main thread in 0x55f5a0 from ZActor slot 82).
    out[1] += [tree(r, 0, na[2], ()) for r in B[1]]
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


def one(out, s_name, m_name, keep=False, campaign=False, heroes=False, slot=SLOT, tag='', nav_base=None, flat=(), **opt):
    """Build S + M into <out>/<S>+<M><tag>/ and write result.json. -> the result dict.
    opt: kl_graft.build's own arguments. author (True = kl_fa_author, a module's name, or a module:
    kl_graft.author_module) is also asked here which campaign subtrees the pre-pass must leave in."""
    import kl_graft, kl_gms, kl_prpjoin as J
    redirect()
    folder = os.path.join(out, '%s+%s%s' % (s_name, m_name, tag))
    os.makedirs(folder, exist_ok=True)
    lines, t0 = [], time.time()
    def log(s=''):
        lines.append(str(s)); print(s, flush=True)
    res = {'S': s_name, 'M': m_name, 'ok': False, 'options': {k: (list(v) if isinstance(v, tuple) else v) for k, v in opt.items()},
           'campaign': campaign, 'heroes': heroes, 'tag': tag, 'flat': list(flat)}
    if 'author' in opt:                                 # a module handed in goes into result.json by its name
        res['options']['author'] = getattr(opt['author'], '__name__', opt['author'])
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
        def __init__(self, name, log=print, *a, **k):   # *a: kl_graft.DeadMen's later arguments (ao)
            super().__init__(name, log, *a, **k)
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
        for c in flat:                                  # pre-pass: these Dead Men classes load as their base
            kl_gms.RETYPE[FLAT[c][0]] = FLAT[c][1]
            log('kl_maps: --flat %s: %#x is loaded as %#x in this build' % (c, *FLAT[c]))
        m_drop = tuple(opt.pop('m_drop', ()))
        if campaign:
            names, gone, stay = campaign_drop(m_name)
            au = kl_graft.author_module(opt.get('author'))
            if au:                                      # the authored layer keeps squads and helpers of the campaign
                import glob
                leave = {glob.escape(n) for n in au.campaign_names(m_name)}
                names = [n for n in names if n not in leave]
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
        for c in flat:
            kl_gms.RETYPE.pop(FLAT[c][0], None)
    res['seconds'] = round(time.time() - t0)
    if flat and res['ok']:
        with open(os.path.join(folder, 'graft.txt'), 'a') as f:
            f.write('kl_maps pre-pass: --flat %s (loaded as the base class)\n' % ','.join(flat))
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


# ------------------------------------------------------------------ before a map's first live run
def map_side(sc):
    """kl_prpjoin.sides as kl_graft.DeadMen corrects it (Dead Men's CoverList counts as map)."""
    import kl_prpjoin as J
    side = J.sides(sc)
    if sc.game == 'dm':
        for k in range(1, len(sc.nodes)):
            if sc.names[sc.top[k]] == 'CoverList':
                side[k] = 'map'
    return side


def census(level, game=None):
    """What a stock level's map side stores: ({class: n}, {controller: n}, {(controller, class): n})."""
    import kl_prpjoin as J
    sc = J.Scene.load(level, game or ('dm' if level.startswith('M') else 'dd'))
    side = map_side(sc)
    cls, ctrl, pair = collections.Counter(), collections.Counter(), collections.Counter()
    for k in range(1, len(sc.nodes)):
        if side[k] == 'map':
            cls[sc.cls(k)] += 1
            for nm, _b in sc.nodes[k]['ctrls']:
                ctrl[sc.p.key(nm)] += 1; pair[sc.p.key(nm), sc.cls(k)] += 1
    return cls, ctrl, pair


def stock_use():
    """{'c:<class>' | 'k:<controller>': [objects, [levels]]} over the whole of every stock Dog Days
    level (systems included). Cached in the temp folder: the stock levels do not change."""
    import tempfile
    import kl_prpjoin as J
    cache = os.path.join(tempfile.gettempdir(), 'kl_maps_stock_use.json')
    if os.path.isfile(cache):
        return json.load(open(cache))
    out = {}
    for lv in DD_FA + ['L%02d' % i for i in range(12)]:
        try:
            sc = J.Scene.load(lv)
        except FileNotFoundError:
            continue
        seen = collections.Counter()
        for k in range(1, len(sc.nodes)):
            seen['c:%s' % sc.cls(k)] += 1
            for nm, _b in sc.nodes[k]['ctrls']:
                seen['k:' + sc.p.key(nm)] += 1
        for name, n in seen.items():
            e = out.setdefault(name, [0, []])
            e[0] += n; e[1].append(lv)
    with open(cache, 'w') as f:
        json.dump(out, f)
    return out


def first_timers(level, log=None):
    """Classes and controllers on a Dead Men map's map side that no map in PROVEN has: what the
    game meets for the first time when this map loads. -> [(kind 'c' | 'k', name, count, on
    classes, Dog Days class or [registrations], stock Dog Days objects, stock levels)]."""
    import kl_prpjoin as J, kl_gms
    dm, dd, use = J.schema('dm'), J.schema('dd'), stock_use()
    base_c, base_k = set(), set()
    for p in PROVEN:
        c, k, _p = census(p)
        base_c |= set(c); base_k |= set(k)
    cls, ctrl, pair = census(level)
    rows = []
    for c, n in cls.most_common():
        if c not in base_c:
            tid = next(t for t, x in dm.geoms.items() if x == c)
            d = dd.geoms.get(kl_gms.RETYPE.get(tid, tid))
            rows.append(('c', c, n, [], d, *use.get('c:%s' % d, [0, []])))
    for c, n in ctrl.most_common():
        if c not in base_k:
            rows.append(('k', c, n, sorted(x for (kk, x) in pair if kk == c), dd.controllers.get(c), *use.get('k:' + c, [0, []])))
    if log:
        log('%s: on its map side and on that of none of %s' % (level, ', '.join(PROVEN)))
        for kind, name, n, on, d, objs, lvs in rows:
            what = ('class -> Dog Days %s' % d) if kind == 'c' else (
                'controller on %s -> %s' % (', '.join(on), d[0][1] if d else 'NOT REGISTERED (the converter drops it)'))
            log('  %-24s %4d  %-58s stock Dog Days: %d in %s' % (name, n, what, objs, ' '.join(lvs) if lvs else 'NO LEVEL'))
    return rows


def stock_values(classes):
    """{class: {field index: {value text}}} of the switch-like fields (bool, enum, flags) of every
    object of `classes` (implementing classes) in the stock Dog Days levels that have one."""
    import kl_graft, kl_prpjoin as J
    from kl_prp import units
    sch, use, out = J.schema('dd'), stock_use(), {c: collections.defaultdict(set) for c in classes}
    names = {c: ['c:' + c] + ['k:' + n for n, es in sch.controllers.items() if any(e[1] == c for e in es)] for c in classes}
    levels = sorted({lv for c in classes for n in names[c] for lv in use.get(n, [0, []])[1]})
    for lv in levels:
        sc = J.Scene.load(lv)
        for k in range(1, len(sc.nodes)):
            for cls, holder, key in kl_graft.objects(sc, k):
                if cls in out:
                    for i, (f, u) in enumerate(zip(sch.fields(cls), units(kl_graft.get_obj(holder, key)[1:-1]))):
                        if f.kind in ('b', 'e', 'k'):
                            out[cls][i].add(repr(J.text(sc, u)))
    return out


def preflight(folder, slot=SLOT, log=print):
    """Every offline check there is on a KEPT build (<folder> = <out>/<S>+<M>...; result.json says
    which levels), and the predictions of re/maps.md section 9: what the crashes M01_FA_A and
    M03_FA_A hit would look like here, and what this map has that no map which ran live had.
    -> [(severity, code, text)]; severity CRASH (do not install), RISK (a path of the game no
    live run has taken: the first place to look when it faults), NOTE, ok. Written to
    <folder>/preflight.json."""
    import kl_graft, kl_prpjoin as J, kl_fa, kl_gms, kl_scene, kl_texmat as T, kl_light, kl_snd, kl_prmgraph as G
    import kl_pf4, kl_members as MB, kl_dmassets
    from kl_prp import units
    res = json.load(open(os.path.join(folder, 'result.json')))
    s_name, m_name = res['S'], res['M']
    zp = os.path.join(folder, slot + '_Main.zip')
    out = []
    def say(sev, code, text):
        out.append((sev, code, text)); log('%-5s %-12s %s' % (sev, code, text))
    sc, snd, loc = kl_fa.load(zp)
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        f = {e: z.read(m[e]) for e in ('.gms', '.buf', '.prp', '.prm', '.MAT', '.fxc', '.sgd')}
    scene = kl_scene.Scene(kl_gms.unpack(f['.gms']), f['.buf'])
    ents, sch = list(scene.entities()), J.schema('dd')
    game = 'dm' if m_name.startswith('M') else 'dd'
    src = J.Scene.load(m_name, game)
    side = map_side(src)
    m_tops = {src.names[t] for t in src.tops() if side[t] == 'map'}
    mine = [k for k in range(1, len(sc.nodes)) if sc.names[sc.top[k]] in m_tops]      # the nodes that came from M
    ctrls = lambda k: [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
    notes = res.get('notes', [])
    log('%s: %s systems + %s map%s; %d nodes, %d of them the map\'s; build problems: %d' % (
        zp, s_name, m_name, ' (flat: %s)' % ','.join(res['flat']) if res.get('flat') else '', len(sc.nodes) - 1, len(mine), len(res.get('problems', []))))
    if res.get('problems'):
        say('CRASH', 'verify', 'kl_graft.verify reported %d problems (result.json)' % len(res['problems']))

    # -- crash 1 of M01: an event that deletes itself after it was entered in the save-state table
    mute = [sc.path[k] for k in range(1, len(sc.nodes)) for c in sc.nodes[k]['ctrls'] if kl_graft.mute_speech(sc, c, snd)]
    if mute:
        say('CRASH', 'self-delete', '%d OnlineSpeakTrigger without their line in the .SND (kl2 0x4eae60), e.g. %s' % (len(mute), mute[0]))
    first = next(i for i, x in enumerate(sch.fields('ZOnlineMoneyContainer')) if x.owner == 'ZOnlineMoneyContainer')
    cont = bad = 0
    for k in range(1, len(sc.nodes)):
        for nm, body in sc.nodes[k]['ctrls']:
            if sc.p.key(nm) == 'OnlineMoneyContainer':
                refs = J.strings(sc, units(body[1:-1])[first])
                cont += 1
                if not refs or not sc.resolve(refs[0]):
                    bad += 1
                    say('CRASH', 'self-delete', '%s: OnlineMoneyContainer whose first reference names nothing deletes itself '
                        '(kl2 0x837000 -> [vtbl+0x78])' % sc.path[k])
    # ZPhysicsLinkage init (slot 14, kl2 0x80bd20 -> 0x78cd90): its first reference must resolve to a
    # ZLNKOBJ (class id [0x15355a0]), else it deletes itself. Whether it is in the save-state table
    # by then was NOT read; stock levels always pass (L01's lamps: a ZLNKOBJ and a bone name).
    link = unlinked = 0
    for k in range(1, len(sc.nodes)):
        for nm, body in sc.nodes[k]['ctrls']:
            if sc.p.key(nm) == 'PhysicsLinkage':
                refs = J.strings(sc, units(body[1:-1])[next(i for i, x in enumerate(sch.fields('ZPhysicsLinkage')) if x.owner == 'ZPhysicsLinkage')])
                link += 1
                if not refs or not any('ZLNKOBJ' in sch.bases(sc.cls(x)) for x in sc.resolve(refs[0])):
                    unlinked += 1
                    say('CRASH', 'self-delete', '%s: PhysicsLinkage whose target is no ZLNKOBJ deletes itself (kl2 0x80bd20 -> [vtbl+0x78])' % sc.path[k])
    say('ok', 'self-delete', 'speech triggers cut by the build: %s; %d OnlineMoneyContainer, the first reference of %d resolves; '
        '%d PhysicsLinkage, the target of %d is a ZLNKOBJ' % (
            '; '.join(n.split(': ', 1)[1] for n in notes if 'OnlineSpeakTrigger' in n) or 'none', cont, cont - bad, link, link - unlinked))

    # -- crash 2 of M01: KEYS chunks in raw data blocks
    tags = found = stray = 0
    for e in ents:
        if e.raw is not None:
            ks = kl_graft.keys_tracks(e.raw)
            tags += e.raw.count(b'SYEK'); found += len(ks)
            stray += sum(not 16 <= v < len(scene.head) for _p, ko in ks for v in ko)
    other = collections.Counter(e.raw[p:p + 4] for e in ents if e.raw is not None for p in range(0, len(e.raw) - 3, 4)
                                if e.raw[p:p + 4].isalpha() and e.raw[p:p + 4].isupper() and e.raw[p:p + 4] != b'SYEK')
    if tags != found or stray:
        say('CRASH', 'KEYS', '%d \'SYEK\' tags in raw data blocks, kl_graft.keys_tracks finds %d; %d track offsets outside the .buf head' % (tags, found, stray))
    else:
        say('ok', 'KEYS', '%d KEYS chunks, every one found by keys_tracks, every offset inside the head; other four-letter tags in raw blocks: %s' % (
            found, {k.decode(): v for k, v in other.items()} or 'none'))

    # -- crash 3 of M01 / M03: a controller on a node that is no longer (or never was) its class
    odd, geoms = collections.Counter(), set(sch.geoms.values())
    for k in mine:
        chain = sch.bases(sc.cls(k))
        for c in ctrls(k):
            owners = {e[0] for e in sch.controllers.get(c, [])}
            if owners and owners <= geoms and not owners & set(chain):   # an owner that is no entity class binds nothing
                odd['%s (registered for %s) on %s' % (c, '/'.join(sorted(owners)), sc.cls(k))] += 1
    retyped = [k for k in range(1, len(src.nodes)) if side[k] == 'map' and src.tids[k] in kl_gms.RETYPE] if game == 'dm' else []
    unread = [o for o in odd if o not in OWNER_READ]
    say('RISK' if unread else 'NOTE' if odd else 'ok', 'owner', 'controllers on a node outside the class they are registered for: %s%s; '
        '%d map nodes retyped by kl_gms.RETYPE (%s)' % (dict(odd) or 'none', ' - init read, does not use the node as that class' if odd and not unread else '',
                                                       len(retyped), dict(collections.Counter(src.cls(k) for k in retyped)) or 'none'))

    # -- the sound-thread fault of the bank: interleaved stream groups
    whd = open(os.path.join(folder, slot + '_Main.WHD'), 'rb').read()
    import kl_whd                                       # (kl_graft.broken_groups moved there)
    torn = set(kl_whd.torn_groups("dd", whd))
    named = sum(off in torn for _w, _i, off in kl_snd.Snd('dd', snd).walk().waves())
    if named:
        say('CRASH', 'streams', '%d wave references name a record of a torn interleaved stream group (divide fault kl2 0x44668b)' % named)
    else:
        say('ok', 'streams', '%d torn records left in the .WHD, none named by a wave' % len(torn))
    if res.get('stream_clips_missing'):
        say('NOTE', 'streams', '%d stream clips are not in the merged PC_Def.str: silent' % len(res['stream_clips_missing']))

    # -- the other offline checks that exist
    for x in kl_fa.check(sc, snd, loc):
        say('CRASH' if x.sev == kl_fa.CRASH else 'RISK' if x.sev == kl_fa.BROKEN else 'NOTE', 'fa:' + x.code, x.text)
    prm = G.read(f['.prm'], 'dd')
    lights = kl_light.check(sc, scene, prm, nodes=set(mine)) if game == 'dm' else []
    for x in lights:
        say('RISK', 'lights', x)
    if not lights:
        say('ok', 'lights', 'kl_light.check: nothing')
    logf = os.path.join(folder, 'log.txt')
    for line in open(logf, encoding='utf-8', errors='replace') if os.path.isfile(logf) else ():
        if 'environments in no stock form: ' in line and not line.rstrip().endswith('none'):
            say('NOTE', 'lights', 'environments in no stock form (a matter of look, re/lighting.md): ' + line.rsplit('stock form: ', 1)[1].strip())
    mat = T.read_mat(f['.MAT'])
    lack = kl_light.missing_shaders(mat, f['.fxc'])
    say('NOTE' if lack else 'ok', 'shaders', '%d of %d materials have no compiled shader in the level\'s .fxc: their meshes are not drawn '
        '(the bank ran live with 35 such: no fault)%s' % (len(lack), len(mat.insts), ''.join('\n' + ' ' * 19 + n for n in notes if 'compiled shader' in n)))
    for n in notes:
        if n.startswith('.ANM') or 'dynamic lists' in n or '.hrd' in n:
            say('NOTE', 'build', n)

    # -- what this map has that no map which ran live had
    if game == 'dm':
        rows = first_timers(m_name)
        have_c, have_k = collections.Counter(sc.cls(k) for k in mine), collections.Counter(c for k in mine for c in ctrls(k))
        for kind, name, n, on, d, objs, lvs in rows:
            now = have_c.get(d, 0) if kind == 'c' else have_k.get(name, 0)
            if kind == 'k' and not d:
                say('NOTE', 'first', 'controller %s x%d: Dog Days does not register it, the converter drops it (in the build: %d)' % (name, n, now))
            else:
                say('RISK' if not objs and now else 'NOTE', 'first', '%s %s x%d (in the build: %d)%s; stock Dog Days: %d in %s' % (
                    'class' if kind == 'c' else 'controller', name, n, now, '' if kind == 'c' else ' on ' + ', '.join(on),
                    objs, ' '.join(lvs) if lvs else 'NO LEVEL - code no stock level runs'))
        # values of those objects that Dog Days' own levels never store in the field
        impl = {d for kind, name, n, on, d, objs, lvs in rows if kind == 'c' and d} | \
               {e[1] for kind, name, n, on, d, objs, lvs in rows if kind == 'k' and d for e in d}
        stock = stock_values(impl)
        unseen = collections.Counter()
        for k in mine:
            for cls, holder, key in kl_graft.objects(sc, k):
                if cls in impl:
                    fs = sch.fields(cls)
                    for i, (fl, u) in enumerate(zip(fs, units(kl_graft.get_obj(holder, key)[1:-1]))):
                        own = i - next(j for j, x in enumerate(fs) if x.owner == fl.owner)
                        if stock[cls].get(i) and repr(J.text(sc, u)) not in stock[cls][i] and fl.owner not in ('ZGEOM', 'ZSTDOBJ', 'ZEventBase'):
                            unseen['%s: %s[%d] (%s) = %s; stock has only %s' % (cls, fl.owner, own, fl.kind, J.text(sc, u), sorted(stock[cls][i])[:4])] += 1
        for t, n in unseen.most_common(12):
            say('RISK', 'value', 'x%d %s' % (n, t))

    # -- ZEnvSampler: a render entry of its own, built for no stock Dog Days level
    slots = collections.Counter()
    for k in mine:
        if sc.cls(k) == 'ZEnvSampler':
            lab = kl_graft.labels('ZEnvSampler')
            slots[kl_graft.u32(units(sc.nodes[k]['props'][1:-1])[lab.index('ZEnvSampler[0]')][0])] += 1
    if any(s > 3 for s in slots):
        say('CRASH', 'envsampler', 'ZEnvSampler slot %d: ZRenderEntryEnvSamplerD3D (kl2 0x7ee5ba) indexes a table of 4 x 16 at 0x138c718 without a test' % max(slots))
    elif slots:
        say('RISK', 'envsampler', '%d ZEnvSampler (slots %s): each gets a ZRenderEntryEnvSamplerD3D (kl2 0x718f20 -> 0x7ee4b0) whose render function '
            '0x61b5a0 no stock Dog Days level ever reaches. --flat ZEnvSampler loads them as plain ZSTDOBJ' % (sum(slots.values()), dict(sorted(slots.items()))))
    else:
        say('ok', 'envsampler', 'no ZEnvSampler in the build')

    # -- ZSoundSpline (kl2 slot 15 0x61e690, slot 16 0x544e60) uses the sound instance of its node
    # (0x6c6ab0 -> 0x659370, by the node's handle) without a null test; its spline reference may
    # be empty or name anything (three tests in slot 16). ASSUMPTION: a ZSNDOBJ with a sound has one.
    mute_spline = [sc.path[k] for k in mine if 'SoundSpline' in ctrls(k) and not any(
        fl.type in kl_graft.SOUND_TYPES and fl.kind == 'I' and kl_graft.u32(u[0])
        for fl, u in zip(sch.fields(sc.cls(k)), units(sc.nodes[k]['props'][1:-1])))]
    nsp = sum('SoundSpline' in ctrls(k) for k in mine)
    if mute_spline:
        say('RISK', 'soundspline', '%d of %d SoundSpline sit on a node without a sound (kl2 0x61e733 / 0x544ea1 use its sound instance untested), e.g. %s' % (
            len(mute_spline), nsp, mute_spline[0]))
    elif nsp:
        say('ok', 'soundspline', '%d SoundSpline, each on a node with a sound of the merged bank' % nsp)

    # -- squad behaviours: PatrolBehaviourRout with its start flag set calls into the squad at init
    lone = [sc.path[k] for k in mine for c in ctrls(k) if (c.endswith('BehaviourRout') or c in ('SquadModifierBehaviour', 'IdleWalkPathRout'))
            and not set(ctrls(sc.parent[k])) & set(SQUADS)]
    nb = sum(c.endswith('BehaviourRout') for k in mine for c in ctrls(k))
    if lone:
        say('CRASH', 'behaviour', '%d squad behaviours whose parent has no squad controller (kl2 0x4aff50 leaves the squad 0; 0x59a0e0 calls through it), e.g. %s' % (len(lone), lone[0]))
    else:
        say('ok', 'behaviour', '%d squad behaviours, each under a node with one of %s' % (nb, ' / '.join(SQUADS)))

    # -- post filter: M's sets index S's palette
    kinds, _a = G.walk(prm, kl_dmassets.prm_roots(f['.gms'], f['.prp'], 'dd'))
    pal = [i for i, k in kinds.items() if k == 'pfpal']
    sets = [i for i, k in kinds.items() if k == 'pf']
    if len(pal) == 1:
        n = len(kl_light.palette_entries(prm.chunks[pal[0]]))
        over = [i for i in sets if any(c != kl_light.PF_NONE and c >= n for c in kl_light.set_curves(prm.chunks[i]))]
        boxes = sum('PostFilterBox' in c for k in mine for c in ctrls(k))
        say('RISK' if over else 'ok', 'postfilter', '%d filter sets, palette of %d curves (%s\'s); %d sets name a curve past the palette; '
            '%d PostFilterBox controllers of the map; scene block has PostFilterBoxes: %s' % (
                len(sets), n, s_name, len(over), boxes, 'PostFilterBoxes' in dict(J.block(sc))))
    else:
        say('RISK', 'postfilter', '%d palettes reachable in the .prm' % len(pal))

    # -- shapes: rooms, gates, navigation mesh, .sgd, FDX, sizes
    rooms = [k for k in range(1, len(sc.nodes)) if kl_graft.is_room(sc.tids[k])]
    lab, own = kl_graft.labels('ZROOM'), set(mine)
    ng = [kl_graft.u32(units(sc.nodes[k]['props'][1:-1])[lab.index('ZROOM[0]')][0]) for k in rooms]
    nl = [units(sc.nodes[k]['props'][1:-1])[lab.index('ZROOM[1]')][0][1][0] for k in rooms]
    say('ok', 'rooms', '%d rooms (%d the map\'s), %d gates (most in one room: %d), %d neighbour lists; verify() followed every gate, list, tree and box' % (
        len(rooms), sum(k in own for k in rooms), sum(ng), max(ng or [0]), sum(nl)))
    if scene.nav is None:
        say('CRASH', 'nav', 'no navigation mesh (kl2 0x5503da)')
    else:
        kl_pf4.check(scene.nav)
        n, rep = kl_pf4.counts(scene.nav, True), {}
        if game == 'dm':
            with zipfile.ZipFile(J.level_zip(m_name, 'dm')) as z:
                g = [x for x in z.namelist() if x.endswith('_Main.gms')][0]
                kl_pf4.convert(kl_scene.Scene(kl_gms.unpack(z.read(g)), z.read(g[:-4] + '.buf')).nav, report=rep)
        say('NOTE' if rep.get('dropped') else 'ok', 'nav', 'kl_pf4.check passes: %d areas, %d polygons, %d waypoints, %d links; '
            'Dead Men links dropped by kind: %s' % (n[4], n[3], n[5], n[7], rep.get('dropped') or 'none'))
    secs = dict(MB.sgd_read(f['.sgd']))
    lacks = [x for x in ('HavokShatterOctree', 'ExplodableOctree') if x not in secs]      # 21 of 21 stock levels have both
    say('NOTE' if lacks else 'ok', 'sgd', 'sections: %s%s' % (', '.join('%s %d B' % (name, len(p)) for name, p in secs.items()),
        '; NO %s, which every stock Dog Days level has (ExplodableOctree: the loader kl2 0x5e38c0 skips a missing section and both '
        'users of game data +0x814, 0x60b426 and 0x82e5a9, test it for 0)' % ' / '.join(lacks) if lacks else ''))
    if scene.fdx is not None:
        recs = MB.fdx_read(f['.buf'], scene.fdx)[1]
        say('ok', 'FDX', '%d records (%d with bones), %d instances' % (len(recs), sum(r['kind'] == 0 for r in recs), sum(r['instances'] for r in recs)))
    else:
        say('ok', 'FDX', 'no block')
    over = ['%s %d (ran live: %d)' % (k, res.get(k, 0), v) for k, v in LIVE.items() if res.get(k, 0) > v]
    say('NOTE' if over else 'ok', 'size', 'larger than any Dead Men build that ran live: %s' % (', '.join(over) or 'nothing'))
    count = collections.Counter(s for s, _c, _t in out)
    log('preflight: CRASH %d, RISK %d, NOTE %d' % (count['CRASH'], count['RISK'], count['NOTE']))
    with open(os.path.join(folder, 'preflight.json'), 'w') as fh:
        json.dump({'S': s_name, 'M': m_name, 'findings': out}, fh, indent=1)
    return out


def stage(folder, slot=SLOT, log=print):
    """FOR THE LIVE SIDE: copy a kept build into kl_graft's own output folder
    (<work>/build/install/Scenes/Locations/<slot>), so that 'python kl_graft.py install' and
    kl_autotest.py take it. Whatever build was there is replaced. Refuses a build with problems."""
    import shutil
    import kl_graft
    res = json.load(open(os.path.join(folder, 'result.json')))
    if not res.get('ok') or res.get('problems'):
        raise SystemExit('%s: not a build with 0 problems' % folder)
    files = sorted(x for x in os.listdir(folder) if x.startswith(slot + '_Main'))
    if slot + '_Main.zip' not in files:
        raise SystemExit('%s holds no %s_Main.zip (built without --keep?)' % (folder, slot))
    d = kl_graft.out_dir(slot)
    for x in os.listdir(d):
        if x.startswith(slot + '_Main') or x == 'graft.txt':
            os.remove(os.path.join(d, x))
    for x in files + ['graft.txt']:
        shutil.copyfile(os.path.join(folder, x), os.path.join(d, x))
    log('staged %s systems + %s map (%d files%s) in %s' % (res['S'], res['M'], len(files) + 1,
                                                          ', flat ' + ','.join(res['flat']) if res.get('flat') else '', d))


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


# ------------------------------------------------------------------ the four FA maps, ready to install
# Each Dead Men Fragile Alliance map to the standard of the Retomoto build the owner plays (re/maps.md 14):
# the build with every fix that is a default of kl_graft today and the voices on, then 'lighten', then the
# wardrobe - the order re/prm_limit.md gives (lighten FIRST: after the wardrobe took the dead chunk indices
# lighten finds no dead material left). (folder under <out>, level, Dead Men's own title, kl_maps.one options)
READY_S = 'F07'                                 # the only systems level a Dead Men map has run under (sections 3, 10)
READY = [('M01', 'M01_FA_A', 'Hot Coffee', {}), ('M02', 'M02_FA_A', 'Late Night Opening', {}),
         ('M03', 'M03_FA_A', 'Withdrawal', {}), ('M06', 'M06_FA_A', 'A Walk in the Park', {})]
READY_LOAD = 'trim,slim'                        # kl_graft.load_options: what the played Retomoto build has


def round_facts(sc):
    """What a Fragile Alliance round needs, counted on a built scene (kl_fa's readers) -> dict."""
    import kl_fa
    _ctrl, cls = kl_fa.census(sc)
    n = lambda name: len(kl_fa.controllers(sc, name))
    money = [v[1] for _k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if len(v) > 1 and isinstance(v[1], (int, float))]
    veh = ['%s %s' % (sc.cls(k), sc.path[k].split('\\', 1)[-1]) for k, _i, _v in kl_fa.controllers(sc, 'OnlineEscVehicleController')]
    points = collections.Counter()
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint':
            points[next((x for x in kl_fa.node_values(sc, k) if isinstance(x, str) and 'SPAWN' in x.upper()), '?')] += 1
    return collections.OrderedDict((
        ('money objects (OnlineMoneyCtrl)', len(money)), ('their amounts added up (field 1)', int(sum(money))),
        ('money containers (OnlineMoneyContainer)', n('OnlineMoneyContainer')),
        ('enter / exit loot-area triggers (OnlineGamePlayTrigger)', n('OnlineGamePlayTrigger')),
        ('level exit (OnlineExitLevelTrigger)', n('OnlineExitLevelTrigger')), ('escape monitor (OnlineEscVehicleMonitor)', n('OnlineEscVehicleMonitor')),
        ('escape vehicles (OnlineEscVehicleController on)', veh),
        ('squads (ZSquadScript)', n('ZSquadScript')), ('bot squads (TriggerLootDepleted)', n('TriggerLootDepleted')),
        ('actors (ZFFActor)', cls['ZFFActor']), ('players (ZFFPlayer)', cls['ZFFPlayer']), ('spawn points', dict(points)),
        ('HUD markers (PointOfInterest)', n('PointOfInterest'))))


# ------------------------------------------------------------------ the AI heisters ('no bot squads')
# kl_fa.check on every Dead Men map: 'no bot squads'. What a stock level's squad is and what a map offers it,
# measured; nothing is built from it (re/maps.md 14.5: it is authoring per map, not a switch).
def bot_facts(level=READY_S, log=print):
    """The AI heister squad of a stock Fragile Alliance level, read from its .prp -> dict: top-level subtrees
    ('Gameplay!merc_bot_squad!*'), nodes, squads and the fields of their ZSquadScript, controllers, the plain
    position boxes its DefendBehaviourRout steps walk to, the actors' places against the START points, every
    reference out of it by field and target side, and who outside starts it."""
    import kl_fa, kl_prpjoin as J, kl_gms, kl_scene
    sc, _snd, _loc = kl_fa.load(level)
    with zipfile.ZipFile(J.level_zip(level, 'dd')) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    ents = list(scene.entities()); pos = world(scene)
    at = lambda k: tuple(round(v) for v in pos[ents[k - 1]])
    side = J.sides(sc)
    tops = [t for t in sc.tops() if 'merc_bot' in sc.names[t].lower()]
    mine = {k for t in tops for k in range(t, sc.end[t])}
    ctrl = collections.Counter(sc.p.key(nm) for k in mine for nm, _b in sc.nodes[k]['ctrls'])
    out_refs, into = collections.Counter(), collections.Counter()
    for k, _holder, field, _st, hit in J.references(sc):
        if k in mine and hit and not all(h in mine for h in hit):
            out_refs['%s -> %s %s' % (field, side[hit[0]], sc.cls(hit[0]))] += 1
        elif k not in mine and hit and any(h in mine for h in hit):
            into['%s %s' % (sc.names[sc.top[k]] if k > 0 else 'scene block', field)] += 1
    squads = [t for t in tops if kl_fa.has(sc, t, 'ZSquadScript')]
    boxes = sorted(k for k in mine if sc.cls(k) == 'ZBoxPrimitive' and not sc.nodes[k]['ctrls'])
    starts = [at(k) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and any(
        isinstance(x, str) and x.endswith('_START') for x in kl_fa.node_values(sc, k))]
    actors = [at(k) for k in sorted(mine) if sc.cls(k) == 'ZFFActor']
    mid = lambda ps: tuple(round(sum(p[i] for p in ps) / len(ps)) for i in range(3)) if ps else None
    ps = [at(k) for k in boxes]
    r = collections.OrderedDict((
        ('level', level), ('top-level subtrees', len(tops)), ('nodes', len(mine)), ('squads', len(squads)),
        ('ZSquadScript fields 0..3', next(([kl_fa.value(sc, u) for u in units_of(b)][:4] for nm, b in sc.nodes[squads[0]]['ctrls']
                                           if sc.p.key(nm) == 'ZSquadScript'), None) if squads else None),
        ('controllers', dict(ctrl.most_common())), ('route steps (DefendBehaviourRout)', ctrl['DefendBehaviourRout']),
        ('position boxes', len(boxes)),
        ('position boxes: extent x, y, z', [(min(p[i] for p in ps), max(p[i] for p in ps)) for i in range(3)] if ps else None),
        ('actors stand around', mid(actors)), ('START points around', mid(starts)),
        ('references into the level outside the squad', dict(out_refs.most_common())), ('started from outside by', dict(into))))
    for k, v in r.items():
        log('  %-46s %s' % (k, v))
    return r


def units_of(body):
    from kl_prp import units
    return units(body[1:-1])


class NavParts:
    """A Dog Days-form navigation mesh as polygons with neighbours (kl_pf4: array 3 polygons, 9 edges, 6 vertices
    stored x, z, y - as tools/kl_fa_street.py's Nav reads them) and its connected parts. `joined`: besides the edges'
    neighbour fields, two waypoints of different polygons at one place (within 60) join their polygons - the
    ASSUMPTION of re/fa_round.md 6.1 that every scripted walk bore out; part ids are given for both readings."""
    def __init__(self, block):
        import math, kl_pf4
        _n, A = kl_pf4.split(block, True)
        polys = [struct.unpack('<BBHIIIIIII', r) for r in A[3]]
        edges = [struct.unpack('<iII', r) for r in A[9]]
        verts = [struct.unpack('<5f', r) for r in A[6]]
        self.pv = [[(verts[edges[e][1]][0], verts[edges[e][1]][2], verts[edges[e][1]][1]) for e in range(p[5], p[5] + p[0])] for p in polys]
        nb = collections.defaultdict(set)
        for i, p in enumerate(polys):
            for e in range(p[5], p[5] + p[0]):
                j = edges[e][0]
                j = -2 - j if j < -1 else j
                if 0 <= j < len(polys) and j != i:
                    nb[i].add(j); nb[j].add(i)
        self.links = sum(1 for _r in A[7])
        wj = collections.defaultdict(set)
        wps = [struct.unpack('<3fIIIHH', r) for r in A[5]]
        grid = collections.defaultdict(list)
        for w in wps:
            grid[int(w[0] // 100), int(w[1] // 100)].append(w)
        for w in wps:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for v in grid.get((int(w[0] // 100) + dx, int(w[1] // 100) + dz), ()):
                        if v[5] != w[5] and math.dist(w[:3], v[:3]) < 60 and max(v[5], w[5]) < len(polys):
                            wj[w[5]].add(v[5]); wj[v[5]].add(w[5])
        self.part, self.joined = self._parts(nb, {}), self._parts(nb, wj)
        self.box = [(min(v[0] for v in vs), max(v[0] for v in vs), min(v[2] for v in vs), max(v[2] for v in vs),
                     sum(v[1] for v in vs) / len(vs)) if len(vs) >= 3 else None for vs in self.pv]

    def _parts(self, nb, more):
        part, n = [-1] * len(self.pv), 0
        for s in range(len(self.pv)):
            if part[s] >= 0:
                continue
            part[s], st = n, [s]
            while st:
                i = st.pop()
                for j in nb.get(i, set()) | more.get(i, set()):
                    if part[j] < 0:
                        part[j] = n; st.append(j)
            n += 1
        return part

    def inside(self, i, x, z):
        vs, sign = self.pv[i], 0
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            c = (b[0] - a[0]) * (z - a[2]) - (b[2] - a[2]) * (x - a[0])
            if abs(c) < 1e-6:
                continue
            if sign and (c > 0) != (sign > 0):
                return False
            sign = c
        return True

    def at(self, x, y, z):
        """(polygon, horizontal distance to it, height difference): the polygon under the point whose height is
        nearest to y, else the polygon whose centre is nearest (distance > 0: the point is off the mesh)."""
        import math
        under = [i for i, b in enumerate(self.box) if b and b[0] <= x <= b[1] and b[2] <= z <= b[3] and self.inside(i, x, z)]
        if under:
            i = min(under, key=lambda i: abs(self.box[i][4] - y))
            return i, 0.0, self.box[i][4] - y
        i = min((i for i, b in enumerate(self.box) if b), key=lambda i: math.dist(
            ((self.box[i][0] + self.box[i][1]) / 2, self.box[i][4], (self.box[i][2] + self.box[i][3]) / 2), (x, y, z)))
        b = self.box[i]
        return i, math.hypot((b[0] + b[1]) / 2 - x, (b[2] + b[3]) / 2 - z), b[4] - y


def stations(folder, slot=SLOT, log=print):
    """Where a Fragile Alliance round happens on a built map, and whether an AI could walk it: the START row, the
    loot-area triggers, the level exit, the boarding action and the escape vehicle (world places, kl_scene), each
    looked up on the level's navigation mesh (NavParts). -> dict. Read only; for re/maps.md 14.5."""
    import kl_fa, kl_gms, kl_scene
    zp = os.path.join(folder, slot + '_Main.zip')
    sc, _snd, _loc = kl_fa.load(zp)
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    ents = list(scene.entities()); pos = world(scene)
    at = lambda k: pos[ents[k - 1]]
    nav = NavParts(scene.nav)
    mid = lambda ps: tuple(sum(p[i] for p in ps) / len(ps) for i in range(3))
    st = collections.OrderedDict()
    kinds = collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint':
            kind = next((x for x in kl_fa.node_values(sc, k) if isinstance(x, str) and 'SPAWN' in x.upper()), '?')
            kinds[kind.rsplit('ALLIANCE_', 1)[-1]].append(at(k))
    for kind in ('START', 'AFTER_DEATH', 'TRAITOR'):
        if kinds.get(kind):
            st['%s points (%d), their middle' % (kind, len(kinds[kind]))] = mid(kinds[kind])
    for k, _i, v in kl_fa.controllers(sc, 'OnlineGamePlayTrigger'):
        what_ = next((x for x in v if isinstance(x, str) and x.startswith('eOGPT_')), '?')
        st['%s  %s' % (what_.replace('eOGPT_PLAYER_', ''), sc.path[k][5:])] = at(k)
    for k, _i, v in kl_fa.controllers(sc, 'OnlineExitLevelTrigger'):
        st['level exit  %s' % sc.path[k][5:]] = at(k)
    for k, _i, v in kl_fa.controllers(sc, 'PlayerAction'):
        if 'EnterVehicle' in v:
            st['boarding  %s' % sc.path[k][5:]] = at(k)
    for k, _i, v in kl_fa.controllers(sc, 'OnlineEscVehicleController'):
        st['escape vehicle (%s)  %s' % (next((sc.cls(j) for j in range(k + 1, sc.end[k]) if sc.cls(j) in ('ZHavokCar', 'ZHeli', 'ZAnimatedVehicle')), sc.cls(k)),
                                        sc.path[k][5:])] = at(k)
    boxes = [at(k) for k, _i, _v in kl_fa.controllers(sc, 'OnlineMoneyContainer')]
    if boxes:
        st['money containers (%d), their middle' % len(boxes)] = mid(boxes)
    sizes, sizes_j = collections.Counter(nav.part), collections.Counter(nav.joined)
    out = collections.OrderedDict(folder=folder, polygons=len(nav.pv), links=nav.links,
                                  parts_by_edges=len(sizes), parts_with_waypoint_joins=len(sizes_j),
                                  largest_parts=[n for _p, n in sizes_j.most_common(6)], stations=[])
    log('%s: navigation mesh %d polygons, %d links; %d connected parts by the edges\' neighbour fields, %d when waypoints at one place join '
        '(largest: %s polygons)' % (folder, len(nav.pv), nav.links, len(sizes), len(sizes_j), ', '.join(str(n) for _p, n in sizes_j.most_common(6))))
    home = None
    for name, p in st.items():
        i, d, dy = nav.at(*p)
        part = nav.joined[i]
        home = part if home is None else home
        out['stations'].append({'what': name, 'at': [round(v) for v in p], 'polygon': i, 'off_mesh_by': round(d), 'height_off': round(dy),
                                'part': part, 'part_polygons': sizes_j[part], 'with_start': part == home})
        log('  %-74s (%6d %6d %6d)  part %3d of %4d polygons%s%s' % (
            name[:74], *[round(v) for v in p], part, sizes_j[part], '' if part == home else '   NOT the part of the START row',
            '' if d == 0 else '   [%d off the mesh: nearest polygon]' % round(d)))
    return out


def boarding(sc, scene):
    """Where each escape vehicle's boarding action stands against where the vehicle stops: for every
    OnlineEscHavokCar (Dead Men's form: a car or helicopter on a spline; field 0 = its incoming route, field 2 = the
    box with PlayerAction 'EnterVehicle') -> [(box path, box place, last point of the incoming spline, horizontal
    distance)]. Places through the entities' own matrices (world()'s convention), so a rotated spline node is
    read too (M06_FA_A's). Dead Men's own boxes: 288 (M03), 364 (M01), 305 (M06) - and 9,534 in M02_FA_A, whose
    box has the bank's coordinates (kl_escape.board_box moves it; re/maps.md 14.4)."""
    import math, kl_fa, kl_prpjoin as J
    ents, pos = list(scene.entities()), world(scene)
    out = []
    for _k, _i, v in kl_fa.controllers(sc, 'OnlineEscHavokCar'):
        if len(v) < 3 or not isinstance(v[0], str) or not isinstance(v[2], str):
            continue
        inc, box = sc.resolve(v[0]), sc.resolve(v[2])
        sp = next((j for h in inc for j in range(h, sc.end[h]) if sc.cls(j) == 'ZEditorSpline'), None)
        if sp is None or len(box) != 1:
            continue
        raw = kl_fa.node_values(sc, sp)[J.labels(sc.game, 'ZEditorSpline').index('ZEditorSpline[0]')]
        last = None
        for o in range(12, len(raw) - 23, 24):          # 12 bytes, then 24-byte records (x, y, z, three floats)
            p = struct.unpack_from('<3f', raw, o)
            if max(abs(x) for x in p) > 1e6:
                break
            last = p
        chain, j = [], sp
        while j > 0:
            chain.append(ents[j - 1]); j = sc.parent[j]
        R, T = [[1, 0, 0], [0, 1, 0], [0, 0, 1]], (0.0, 0.0, 0.0)
        for e in reversed(chain):                       # as world(): rows reversed, then transposed
            r, t = struct.unpack('<9f', e.rot[:36]), struct.unpack('<3f', e.trans[:12])
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[b][a] for b in range(3)] for a in range(3)]
            T = tuple(T[i] + sum(R[i][b] * t[b] for b in range(3)) for i in range(3))
            R = [[sum(R[i][c] * m[c][b] for c in range(3)) for b in range(3)] for i in range(3)]
        end = tuple(T[i] + sum(R[i][b] * last[b] for b in range(3)) for i in range(3))
        at = pos[ents[box[0] - 1]]
        out.append((sc.path[box[0]][5:], tuple(round(x) for x in at), tuple(round(x) for x in end), round(math.hypot(at[0] - end[0], at[2] - end[2]))))
    return out


def member_ids(folder, slot=SLOT):
    """{member extension: [CRC, size]} of a build folder's archive and {file beside it: sha1} -> (members, beside)
    as lists (JSON form), to tell which members a step changed without keeping 0.3 GB per step."""
    import hashlib
    with zipfile.ZipFile(os.path.join(folder, slot + '_Main.zip')) as z:
        mem = sorted([n.rsplit('_Main', 1)[1], i.CRC, i.file_size] for n, i in ((i.filename, i) for i in z.infolist()) if '_Main' in n)
    side = []
    for f in sorted(os.listdir(folder)):
        if f.startswith(slot + '_Main') and f != slot + '_Main.zip':
            h = hashlib.sha1()
            with open(os.path.join(folder, f), 'rb') as fh:
                for b in iter(lambda: fh.read(1 << 22), b''):
                    h.update(b)
            side.append([f, h.hexdigest()])
    return [mem, side]


def audit(folder, slot=SLOT, log=print):
    """Every checker there is on a FINISHED folder (archive + the files beside it, with or without a wardrobe), and
    the numbers of the table in re/maps.md 14, read back from the written files. Nothing is changed but
    <folder>/audit.json and audit.txt. -> dict; ['bad'] = the findings that must be 0 before an install,
    ['known'] = findings that are listed and accepted: a material of the MAP without a compiled shader (it is not
    drawn in that pass; kl_light.TWIN_CLASSES says why a glow is not rebuilt; M02c / M06a / the bank ran live with
    such) - a PERSON such a material leaves undrawn is in 'bad' through kl_chars.undrawn.
    (kl_graft.verify needs the joined scene's origin, so its verdict is the build's: result.json. A CRASH finding
    of <folder>/preflight.json - kl_maps.preflight, run before this by ready_one - counts as bad.)"""
    import kl_fa, kl_impact, kl_chars, kl_arms, kl_light, kl_snd, kl_voice, kl_whd, kl_texmat as T
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    zp = os.path.join(folder, slot + '_Main.zip')
    rj = os.path.join(folder, 'result.json')
    res = json.load(open(rj)) if os.path.isfile(rj) else {}
    out = collections.OrderedDict(folder=folder, S=res.get('S'), M=res.get('M'), bad=[], known=[])
    bad, known = out['bad'], out['known']
    out['tag'], out['title'] = next(((r[0], r[2]) for r in READY if r[1] == res.get('M')), (None, None))
    out['seconds'] = res.get('seconds')
    out['build'] = {k: res.get(k) for k in ('entities', 'rooms', 'nav_bytes', 'fdx', 'notes', 'dangling_templates', 'options')}
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        size = {e: z.getinfo(n).file_size for e, n in m.items()}
        f = {e: z.read(m[e]) for e in ('.prm', '.MAT', '.fxc', '.SND', '.TEX', '.ANM', '.gms', '.buf')}
    out['archive_mb'] = round(os.path.getsize(zp) / 1e6, 1)
    out['beside_mb'] = round(sum(os.path.getsize(os.path.join(folder, x)) for x in os.listdir(folder)
                                 if x.startswith(slot + '_Main') and x != slot + '_Main.zip') / 1e6, 1)
    out['prm_mb'], out['tex_mb'] = round(size['.prm'] / 1e6, 1), round(size['.TEX'] / 1e6, 1)
    out['prm_entries'] = struct.unpack_from('<I', f['.prm'], 4)[0]          # the header's count: what the game's table takes
    out['textures'], out['materials'] = len(T.read_tex(f['.TEX']).tex), len(T.read_mat(f['.MAT']).insts)
    say('%s: archive %.1f MB (+ %.1f MB beside it), .prm %.1f MB with %d table entries (the tools\' limit %d, the game\'s %d), '
        '.TEX %.1f MB' % (folder, out['archive_mb'], out['beside_mb'], out['prm_mb'], out['prm_entries'], kl_impact.CHUNK_SAFE,
                          0x12000, out['tex_mb']))
    # one number for 'the same build': the wardrobe step stamps the archive's members with the time of the build, so
    # the zip's own sha1 differs from run to run while every member is the same (seen: M06 built twice, 2026-10-10)
    import hashlib
    out['content_id'] = hashlib.sha1(json.dumps(member_ids(folder, slot)).encode()).hexdigest()
    say('content id %s (members by CRC and size + sha1 of the files beside the archive; not the zip\'s sha1)' % out['content_id'])
    # -- the build's own verify
    out['verify'] = res.get('problems')
    say('kl_graft.verify (at the build): %s' % ('problems: %d' % len(res['problems']) if isinstance(res.get('problems'), list)
                                                else 'NOT KNOWN (no result.json)'))
    for x in res.get('problems') or ():
        say('  ' + str(x)[:300]); bad.append('verify: ' + str(x))
    sj = os.path.join(folder, 'steps.json')             # ready_one: what the steps after verify changed
    if os.path.isfile(sj):
        st = json.load(open(sj))
        now = member_ids(folder, slot)
        out['steps'] = dict(st, folder_is_the_one_measured=now == st.get('final'))
        say('  since that verify: lighten changed %s; the wardrobe changed %s; %d of %d members and %d of %d files beside the archive are '
            'the verified build\'s, byte for byte%s' % (
                ' '.join(st['lighten']) or 'nothing', ' '.join(st['wardrobe']) or 'nothing', len(st['same']), st['members'],
                st['beside_same'], st['beside'], '' if now == st.get('final') else ' - BUT THE FOLDER IS NO LONGER THE ONE THAT WAS MEASURED'))
        if st.get('bots'):                              # kl_fa_bots.apply: one more step after the verify
            say('  then the AI heister squad (kl_fa_bots) changed %s' % ' '.join(st['bots']))
        if now != st.get('final'):
            bad.append('steps: the archive or a file beside it changed after the steps were recorded')
    # -- Fragile Alliance
    sc, snd, loc = kl_fa.load(zp)
    fs = kl_fa.check(sc, snd, loc, f['.ANM'])
    out['fa'] = dict(collections.Counter(kl_fa.SEV[x.sev] for x in fs))
    out['fa_findings'] = [str(x) for x in fs]
    say('kl_fa.check: %s' % (out['fa'] or 'nothing'))
    for x in fs:
        say('  ' + str(x)[:260])
        if x.sev <= kl_fa.BROKEN:
            bad.append('fa: ' + str(x))
    out['round'], out['nodes'] = round_facts(sc), len(sc.nodes)
    for k, v in out['round'].items():
        say('  %-58s %s' % (k, v))
    import kl_escape, kl_gms, kl_scene
    out['boarding'] = boarding(sc, kl_scene.Scene(kl_gms.unpack(f['.gms']), f['.buf']))
    for path, at, end, d in out['boarding']:
        say('  boarding action %s at %s: %d from where its vehicle stops %s%s' % (path, at, d, end, '' if d <= kl_escape.BOARD_FAR else
                                                                                '  - TOO FAR: the action is not at the vehicle'))
        if d > kl_escape.BOARD_FAR:
            bad.append('boarding: %s stands %d from the end of its vehicle\'s incoming route (kl_escape.board_box)' % (path, d))
    # -- impacts: bone ids, chunk table, surface rows
    imp = kl_impact.check(zp)
    out['impact'] = imp
    say('kl_impact.check (bone ids, chunk limit, surface table): problems: %d' % len(imp))
    for x in imp:
        say('  ' + x[:300]); bad.append('impact: ' + x)
    # -- weapons
    arms = kl_arms.check(sc, f['.ANM'])
    out['arms'] = ['%s %s %s' % (('', 'BROKEN', 'DEGRADED')[s], c, t) for s, c, t in arms]
    tot, by = collections.Counter(), collections.OrderedDict()
    for squad, c in kl_arms.table(sc).items():
        tot.update(c)
        by[squad] = dict(c)
    out['weapons'], out['weapons_by_squad'] = collections.OrderedDict(tot.most_common()), by
    say('kl_arms.check: %d findings; carried: %s' % (len(arms), ', '.join('%s %d' % x for x in tot.most_common())))
    for x in out['arms']:
        say('  ' + x[:300])
    bad += ['arms: ' + x for (s, _c, _t), x in zip(arms, out['arms']) if s == 1]
    # -- people: who would not be drawn; the wardrobe's models
    lv = kl_chars.Lv(folder)
    rows = kl_chars.people(lv)
    und = ['%s %s: %s' % (sev, r['path'], text) for r in rows for sev, text in r['faults'] if sev != 'NOTE']
    out['people'], out['undrawn'] = len(rows), und
    out['people_by_class'] = dict(collections.Counter(r['cls'] for r in rows))
    say('kl_chars.undrawn: %d of %d people (%s)' % (len(und), len(rows), out['people_by_class']))
    for x in und:
        say('  ' + x[:300]); bad.append('people: ' + x)
    extra = kl_chars.wardrobe_roots(lv)
    out['wardrobe_roots'] = len(extra)
    cb = kl_chars.check(lv, extra=extra, log=lambda *_a: None)
    out['chars_check'] = [str(x) for x in cb]
    say('kl_chars.check (wardrobe roots no entity names: %d): problems: %d' % (len(extra), len(cb)))
    for x in cb:
        mine = 'asks for a shader the .fxc lacks' in str(x)
        say('  %s%s' % ('known: ' if mine else '', str(x)[:300]))
        (known if mine else bad).append('chars: ' + str(x))
    say('KLWardrobe.ini: %s' % ('there' if os.path.isfile(os.path.join(folder, 'KLWardrobe.ini')) else 'none (no wardrobe on this build)'))
    # -- shaders (a material without a compiled shader is not drawn in that pass; a look, not a fault: the bank ran with 35)
    mat = T.read_mat(f['.MAT'])
    lack = kl_light.missing_shaders(mat, f['.fxc'])
    out['missing_shaders'] = {str(s): [str(x) for x in v][:3] for s, v in lack.items()}
    say('kl_light.missing_shaders: %d of %d materials ask for an effect the level\'s .fxc lacks' % (len(lack), len(mat.insts)))
    for s in list(lack)[:12]:
        say('  slot %d: %s' % (s, [str(x) for x in lack[s]][:2]))
    # -- sound bank
    rd = lambda suffix: open(os.path.join(folder, slot + '_Main' + suffix), 'rb').read()
    whd, ls = rd('.WHD'), rd('_LS.SND')
    sb, counts = kl_snd.verify(kl_snd.bank(res.get('S') or READY_S), f['.SND'], whd, rd('.WAV'), ls)
    torn = set(kl_whd.torn_groups('dd', whd))
    walked = kl_snd.Snd('dd', f['.SND'], ls).walk()
    named = sum(off in torn for _w, _i, off in walked.waves())
    if named:
        sb.append('%d wave references name a record of a torn interleaved stream group (divide fault kl2 0x44668b)' % named)
    out['snd'], out['sounds'], out['waves'] = sb, len(walked.tables.get(1, ())), len(walked.tables.get(4, ()))
    say('kl_snd.verify: problems: %d; %d sounds, %d waves (largest stock bank 4,806 / 4,568), %d .WHD records, %d torn records named by a wave'
        % (len(sb), out['sounds'], out['waves'], counts['.WHD records'], named))
    for x in sb:
        say('  ' + x[:300]); bad.append('sound: ' + x)
    # -- voices
    try:
        c = kl_voice.census(zp)
        out['voice'] = {k: c[k] for k in ('characters', 'line fields', 'speak triggers', 'bank', 'clips by format')}
        out['voice']['voice sets in use'] = {k: v['characters'] for k, v in c['voice sets in use'].items()}
        out['voice']['silent lines'] = len(c['silent lines'])
        say('kl_voice.census:')
        kl_voice.show(c, say)
    except Exception as x:                              # a report: readiness does not hang on it
        out['voice'] = {'error': '%s: %s' % (type(x).__name__, x)}
        say('kl_voice.census did not run: %s' % out['voice']['error'])
    pj = os.path.join(folder, 'preflight.json')
    if os.path.isfile(pj):
        pre = json.load(open(pj))['findings']
        out['preflight'] = dict(collections.Counter(x[0] for x in pre))
        out['preflight_risks'] = ['%s %s' % (x[1], x[2]) for x in pre if x[0] in ('CRASH', 'RISK')]
        say('kl_maps.preflight: %s' % out['preflight'])
        for x in pre:
            if x[0] in ('CRASH', 'RISK'):
                say('  %-5s %s %s' % (x[0], x[1], x[2][:260]))
        bad += ['preflight: %s %s' % (x[1], x[2]) for x in pre if x[0] == 'CRASH']
    say('RESULT: %s (%d findings that must be 0, %d known and accepted)' % ('PASS' if not bad else 'FAIL', len(bad), len(known)))
    with open(os.path.join(folder, 'audit.json'), 'w') as fh:
        json.dump(out, fh, indent=1, default=str)
    with open(os.path.join(folder, 'audit.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out


def ready_one(out, tag, wardrobe=True, log=print):
    """One map of READY: <out>/_work/<tag>/ (the build, then its lightened copy) -> <out>/<tag>/ = the archive, the
    files beside it, KLWardrobe.ini, graft.txt, log.txt, result.json, wardrobe.txt, preflight.*, audit.*. The
    archives of the two intermediate steps are removed when the final folder passed.
    -> audit dict (or {'error': ..., 'bad': [...]})."""
    import shutil, kl_snd, kl_graft
    tag, m_name, title, opt = next(r for r in READY if tag in r[:2])
    work, final = os.path.join(out, '_work', tag), os.path.join(out, tag)
    kl_snd.VOICE = True                                 # the speech repairs of re/voice.md, as the played builds have them
    try:
        r = one(work, READY_S, m_name, keep=True, **dict(opt))
    finally:
        kl_snd.VOICE = None
    built = os.path.join(work, '%s+%s' % (READY_S, m_name))
    if not r.get('ok'):
        log('%s: build failed: %s at %s' % (tag, r.get('error'), r.get('where')))
        return {'error': r.get('error'), 'bad': ['build failed']}
    with open(os.path.join(built, 'graft.txt'), 'a') as f:
        f.write('kl_maps ready: voices on (kl_snd.VOICE = True), then kl_graft lighten (%s)%s\n' % (
            READY_LOAD, ', then kl_chars wardrobe' if wardrobe else ''))
    light, new = os.path.join(work, 'light'), os.path.join(work, 'new')
    shutil.rmtree(light, ignore_errors=True)
    shutil.rmtree(new, ignore_errors=True)              # the folder of an earlier run stays until this one has its archive
    kl_graft.relight(built, light, kl_graft.load_options(READY_LOAD), log)
    if wardrobe:
        w = subprocess.run([sys.executable, os.path.join(HERE, 'kl_chars.py'), 'wardrobe', light, new], capture_output=True, text=True)
        log(w.stdout[-4000:] + w.stderr[-2000:])
        if w.returncode or not os.path.isfile(os.path.join(new, SLOT + '_Main.zip')):
            log('%s: kl_chars wardrobe: exit %d' % (tag, w.returncode))
            return {'error': 'wardrobe exit %d' % w.returncode, 'bad': ['wardrobe failed']}
        with open(os.path.join(new, 'wardrobe.txt'), 'w', encoding='utf-8') as f:
            f.write(w.stdout + w.stderr)
    else:
        shutil.copytree(light, new)
    shutil.rmtree(final, ignore_errors=True)
    os.replace(new, final)
    # kl_graft.verify ran on the build; lighten and the wardrobe came after it. Which members each of them changed
    # (the rest is the verified build byte for byte) is recorded before the two intermediate archives are removed.
    ids = [member_ids(d) for d in (built, light, final)]
    diff = lambda a, b: [e for (e, *x), (_e, *y) in zip(a[0], b[0]) if x != y] if [m[0] for m in a[0]] == [m[0] for m in b[0]] else ['(member list)']
    with open(os.path.join(final, 'steps.json'), 'w') as f:
        json.dump({'lighten': diff(ids[0], ids[1]), 'wardrobe': diff(ids[1], ids[2]), 'members': len(ids[2][0]),
                   'same': [m[0] for m, n in zip(ids[0][0], ids[2][0]) if m == n], 'beside': len(ids[2][1]),
                   'beside_same': sum(a == b for a, b in zip(ids[0][1], ids[2][1])) if len(ids[0][1]) == len(ids[2][1]) else 0,
                   'final': ids[2]}, f, indent=1)
    with open(os.path.join(final, 'preflight.txt'), 'w', encoding='utf-8') as fh:
        preflight(final, log=lambda t: fh.write(str(t) + '\n'))
    a = audit(final, log=log)
    if not a['bad']:
        for d in (built, light):                        # 0.5 GB a map; log.txt / result.json of the build stay
            for x in os.listdir(d):
                if x.startswith(SLOT + '_Main'):
                    os.remove(os.path.join(d, x))
    log('%s %s: %s' % (tag, title, 'READY in ' + final if not a['bad'] else 'NOT READY: ' + '; '.join(a['bad'])[:600]))
    return a


def ready(out, tags=None, par=2, log=print):
    """READY's maps, each in a process of its own -> number of maps that are not ready."""
    tags = list(tags or [r[0] for r in READY])
    os.makedirs(out, exist_ok=True)
    live, bad = [], 0
    while tags or live:
        while tags and len(live) < par:
            t = tags.pop(0)
            fh = open(os.path.join(out, t + '.ready.log'), 'w', encoding='utf-8')
            live.append((t, fh, subprocess.Popen([sys.executable, os.path.abspath(__file__), 'ready1', out, t], stdout=fh, stderr=subprocess.STDOUT)))
        time.sleep(2)
        for j in [j for j in live if j[2].poll() is not None]:
            live.remove(j); j[1].close()
            bad += j[2].returncode != 0
            log('%s: %s (log %s)' % (j[0], 'ready' if not j[2].returncode else 'NOT READY, exit %d' % j[2].returncode, os.path.join(out, j[0] + '.ready.log')))
    ready_table(out, log)
    return bad


def ready_table(out, log=print):
    """The table of re/maps.md 14 from the audit.json of every finished folder under <out>."""
    rows = []
    for tag, m_name, title, _o in READY:
        p = os.path.join(out, tag, 'audit.json')
        if os.path.isfile(p):
            rows.append((tag, m_name, title, json.load(open(p))))
    log('| folder | map | archive MB | beside MB | .prm MB | chunk-table entries | .TEX MB | nodes | people (actors / players) | sounds / waves '
        '| verify | FA | impact | arms | undrawn | chars | sound | boarding action from the vehicle\'s stop | known: map materials without a shader '
        '| content id | result |')
    log('|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|')
    for tag, m_name, title, a in rows:
        pc = a.get('people_by_class', {})
        log('| `%s` | %s "%s" | %s | %s | %s | %s | %s | %s | %s (%s / %s) | %s / %s | %s | %s | %d | %d | %d | %d | %d | %s | %d | `%s` | %s |' % (
            tag, m_name, title, a['archive_mb'], a['beside_mb'], a['prm_mb'], '{:,}'.format(a['prm_entries']), a['tex_mb'], '{:,}'.format(a['nodes']),
            a['people'], pc.get('ZFFActor', 0), pc.get('ZFFPlayer', 0), '{:,}'.format(a['sounds']), '{:,}'.format(a['waves']),
            len(a['verify']) if isinstance(a.get('verify'), list) else '?',
            ', '.join('%d %s' % (v, k) for k, v in a['fa'].items()) or '-', len(a['impact']), len(a['arms']), len(a['undrawn']),
            len(a['chars_check']) - len(a.get('known', ())), len(a['snd']), ', '.join(str(b[3]) for b in a.get('boarding', ())) or '-',
            len(a.get('known', ())), a.get('content_id', '')[:10], 'READY' if not a['bad'] else 'NOT READY (%d)' % len(a['bad'])))
    return rows


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
        if '--author' in a:                             # alone: kl_fa_author (True); '--author kl_fa_bank': that module
            import kl_graft
            opt['author'] = kl_graft.author_arg(a)
        if '--flat' in a:
            i = a.index('--flat'); opt['flat'] = tuple(a[i + 1].split(',')); del a[i:i + 2]
        keep, campaign, heroes = flag('--keep'), flag('--campaign'), flag('--heroes')
        if a[0] == 'chain':
            r = chain(a[1], a[2], a[3], a[4], heroes=heroes, keep=keep, **opt)
        else:
            r = one(a[1], a[2], a[3], keep=keep, campaign=campaign, heroes=heroes,
                    tag=(' campaign' if campaign else '') + (' flat' if opt.get('flat') else ''), **opt)
        sys.exit(0 if r['ok'] and not r['problems'] else 1)
    elif len(a) >= 2 and a[0] == 'maps':
        run_many(a[1], [('F07', m, []) for m in DM_FA], par)
    elif len(a) >= 2 and a[0] == 'hosts':
        m = a[2] if len(a) > 2 else 'M03_FA_A'
        run_many(a[1], [(s, m, []) for s in DD_FA], par)
    elif len(a) >= 2 and a[0] == 'm09':
        run_many(a[1], [('F07', m, o) for m in ('M09_A', 'M09_B') for o in ([], ['--campaign', '--heroes'])], par)
    elif len(a) >= 2 and a[0] == 'first':
        first_timers(a[1], print)
    elif len(a) >= 2 and a[0] == 'preflight':
        sys.exit(1 if any(x[0] == 'CRASH' for x in preflight(a[1], *a[2:3])) else 0)
    elif len(a) >= 2 and a[0] == 'stage':
        stage(a[1], *a[2:3])
    elif len(a) >= 2 and a[0] == 'deliver':
        # the builds for a first live run, kept, each with its preflight (re/maps.md section 10)
        jobs = [('F07', 'M02_FA_A', ['--keep', '--flat', 'ZEnvSampler']), ('F07', 'M02_FA_A', ['--keep']),
                ('F07', 'M06_FA_A', ['--keep']), ('F08', 'M06_FA_A', ['--keep'])]
        run_many(a[1], jobs, par)
        bad = 0
        for s_, m_, o in jobs:
            d = os.path.join(a[1], '%s+%s%s' % (s_, m_, ' flat' if '--flat' in o else ''))
            with open(os.path.join(d, 'preflight.txt'), 'w') as fh:
                bad += any(x[0] == 'CRASH' for x in preflight(d, log=lambda t: (print(t, flush=True), fh.write(str(t) + '\n'))))
        sys.exit(1 if bad else 0)
    elif len(a) >= 2 and a[0] == 'ready':
        sys.exit(1 if ready(a[1], a[2:] or None, min(par, 2)) else 0)
    elif len(a) >= 3 and a[0] == 'ready1':              # one map, in this process (ready() starts these)
        sys.exit(1 if ready_one(a[1], a[2], wardrobe='--no-wardrobe' not in a).get('bad') else 0)
    elif len(a) >= 2 and a[0] == 'audit':
        sys.exit(1 if audit(a[1], *a[2:3])['bad'] else 0)
    elif len(a) >= 2 and a[0] == 'readytable':
        ready_table(a[1])
    elif a and a[0] == 'bots':
        for lv in a[1:] or [READY_S]:
            print('AI heister squad of stock %s:' % lv)
            bot_facts(lv)
    elif len(a) >= 2 and a[0] == 'stations':
        for d in a[1:]:
            stations(d)
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
