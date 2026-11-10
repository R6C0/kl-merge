#!/usr/bin/env python3
"""kl_smartcops_1110.py - "smart cops" for a Dead Men map in Dog Days (owner 2026-11-10: 'idk why theyre not as good as they were in retomoto tower').

Port of the Retomoto recipe (re/dm01_ai_cover_1025.md section 11 wins): the enemies take COVER before they defend. Two parts, each a --parts toggle:

  cover     (recommended on)  hidden cover boxes (CoverBox{H,M}_KC_nn, group KL_CoverSmart!) on real props / walls NEXT TO the enemy Defend posts that
                              have fewer than NEED boxes within NEAR cm (the 'weak posts'). Same box models, rules and checks as the other cover passes
                              (kl_fa_cover.apply/check/diff, kl_cover_add.sparse, kl_cover_1026.walls, kl_cover_floornav reachable-side prune).
  runcover  (recommended on)  one RunToCoverBehaviourRout ('05_RunToCover', a last child of the squad top) per enemy squad that defends, with one
                              RunToCoverPosInfoRout kid per ACTOR (at the actor's own post); its NEXT is the squad's old Defend rout and every starter
                              (timer / trigger list entry) that named the Defend rout now names the RunToCover rout. No new actor or squad is made
                              (budget 99 / 55 untouched). Forms cloned from Dog Days' own F04 RunToCover (kl_bots_kick_1025 does the same for kicks).

Not done here (open, see the kit README): RandomTrigger lane splits and Hunt/Flank timers (they need a bench to tune), moving the weak posts.

  python tools/kl_smartcops_1110.py measure [zip]                  weak-post table of a zip (default: the live map)
  python tools/kl_smartcops_1110.py plan [zip]                     cover plan only
  python tools/kl_smartcops_1110.py stage [outdir] [--map DM01] [--parts cover,runcover] [--no-rehearse]
Nothing is installed, the game is never started, nothing is written under the Dog Days folder (the live files are only READ and md5-pinned)."""
import collections, hashlib, json, math, os, re, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BS = chr(92)
R = 'ROOT' + BS
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TAG_BAK = '.before-smartcops1110'
OUT_ROOT = r'C:\kl_build_1024\smartcops_1110'
GROUP = 'KL_CoverSmart!'
TAG = '_KC_'
CAP_TOTAL = 4500                       # boxes in all (the game takes 5,000)
FREE_KEEP = 3 << 30
NEAR = 500.0                           # cm: a post is covered when a box stands within this (the DefendCover tactic searches 500)
NEED = 2                               # boxes within NEAR a post must reach this or the post is 'weak' (spec section 11: cover on every post)
REACH = 1100.0                          # cm: new boxes may be put on mesh within this of a weak post (GUESS: a 5 m search plus the box length)
DY = 300.0                             # cm: a box counts for a post when within this in height
DENSITY, SPREAD = 12.0, 150.0
MAX_WALLS, MAX_SPARSE = 40, 30
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55
PARTS = ('cover', 'runcover')
RC_NAME = '05_RunToCover'
RC_SRC = ('F04', 'Gameplay!merc_bot_squad!Squad#08' + BS + '010_RunToCover_first_big_fight')   # form donor (RunToCoverBehaviourRout + RunToPosInfo#08 kid)

MAPS = collections.OrderedDict([
    ('DM01', dict(slot='F01', files=('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'),
                  # the enemy squads that have a DefendBehaviourRout started by a timer / trigger (kl_old_waves, KL_Hold, KL_WH, AI_Enemies): scene path after ROOT\
                  squads=('OldWaves!Wave_1', 'OldWaves!Wave_2', 'OldWaves!Wave_3', 'KL_Hold!Shop', 'KL_WH!Floor', 'KL_WH!Top',
                          'AI_Enemies!CheckFront', 'AI_Enemies!KitchenBoy', 'AI_Enemies!CornerShop'),
                  enemy=('AI_Enemies!', 'OldWaves!', 'KL_Hold!', 'KL_WH!', 'KL_Kick!'))),
    # DM03 Withdrawal (live slot F03): the cops of kl_dm03cops_1108, started together by KL_Squads!Clock\Go (one list holding both Defend routs: rc_targets swaps each entry)
    ('DM03', dict(slot='F03', files=('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5'),
                  squads=('KL_Garage!Back', 'KL_Ramp!Wave'),
                  enemy=('KL_Garage!', 'KL_Ramp!'))),
])


# ------------------------------------------------------------------ pure logic (kl_smartcops_1110_test.py)
def near_count(pos, mids, r=NEAR, dy=DY):
    """Boxes (mids = [(x, y, z)]) within r cm in the plane and dy in height of pos."""
    return sum(1 for m in mids if math.hypot(m[0] - pos[0], m[2] - pos[2]) < r and abs(m[1] - pos[1]) < dy)


def weak_posts(posts, mids, need=NEED, r=NEAR):
    """posts [dict(pos=...)] -> those with fewer than `need` boxes in reach."""
    return [p for p in posts if near_count(p['pos'], mids, r) < need]


def disc_mask(mids, oks, centres, r=REACH):
    """nav polygon mids / ok flags -> flags that stay True only within r (plane) of a centre."""
    return [bool(ok) and any(math.hypot(m[0] - c[0], m[2] - c[2]) <= r and abs(m[1] - c[1]) < 400.0 for c in centres) for m, ok in zip(mids, oks)]


def assign_posts(n_actors, posts):
    """Actor i -> post (i mod n posts): every actor gets its own RunToPosInfo place; None when the squad has no post."""
    return [posts[i % len(posts)] if posts else None for i in range(n_actors)]


def swap_entry(entries, old, new):
    """Reference list entries with the one that names `old` (case-insensitive) now naming `new` -> (list, n replaced)."""
    out, n = [], 0
    for e in entries:
        if e.lower() == old.lower():
            out.append(new)
            n += 1
        else:
            out.append(e)
    return out, n


def parse_holder(holder, field):
    """('ZBoxPrimitive + TriggerDelay2 (ZTriggerDelay2)', 'ZTriggerDelay2[4]') -> ('TriggerDelay2', 4); None when it does not parse."""
    m, f = re.search(r'\+ (\w+) \(', holder), re.search(r'\[(\d+)\]$', field)
    return (m.group(1), int(f.group(1))) if m and f else None


def budget_ok(actors, squads, add_a=0, add_s=0):
    return actors + add_a <= ENGINE_ACTORS and squads + add_s <= ENGINE_SQUADS


def ffcover_ok(n):
    return n == 1


def cap_ok(total, cap=CAP_TOTAL):
    return total <= cap


def parts_ok(s):
    p = [x for x in s.split(',') if x]
    bad = [x for x in p if x not in PARTS]
    if bad or not p:
        raise SystemExit('--parts: %s is not one of %s' % (bad or '(empty)', ','.join(PARTS)))
    return p


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ install.py written next to the stage
INSTALL = r'''"""Installs / undoes SMART COPS 1110 for @MAP@ (tools/kl_smartcops_1110.py): the enemies take cover first (recommended on).

  python install.py            install (originals -> <name>.before-smartcops1110 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --root <dir> (or --game <dir>)  a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing: plain zip, bots zip, bots.base.md5); nothing is written while kl2.exe runs.
Never touches KL_PortBackup. Needs the LIVE files to be exactly the ones this was staged from (re-stage after another @MAP@ step)."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = '@MAP@', '@TAG@'
FILES = @FILES@      # (name, pinned live md5, staged md5)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def opt(a, *names):
    for n in names:
        if n in a:
            return a[a.index(n) + 1]
    return None


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = opt(a, '--root', '--game') or GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (@SPACE@)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + the reserve free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def render_install(files, game=GAME, space='1 << 30', map_='DM01'):
    return INSTALL.replace('@GAME@', game).replace('@TAG@', TAG_BAK).replace('@FILES@', repr(list(files))).replace('@SPACE@', space).replace('@MAP@', map_)


README = '''SMART COPS 1110 for %(map)s  (recommended on)  parts: %(parts)s
=========================================================
Why: the owner finds the cops here "not as good as in Retomoto". Retomoto's enemies take cover, hide and defend from behind props; this map's
enemies only stand on their Defend posts (0 RunToCover routs, %(weak0)d of %(nposts)d posts with no or one cover box within 5 m).

What it changes (%(map)s only: %(files)s):
  cover     (recommended on)  +%(n_cover)d hidden cover boxes (group %(group)s) on real props / walls next to the weak enemy posts, on reachable floor only,
                              never in the escape lane or the boarding box. Posts with fewer than %(need)d boxes within 5 m: %(weak0)d -> %(weak1)d (of %(nposts)d);
                              with none: %(none0)d -> %(none1)d. Cover boxes on the map: %(b0)d -> %(b1)d. One FFCoverList before and after.
  runcover  (recommended on)  %(n_rc)d enemy squads (%(n_pi)d actors) get a RunToCover step before their Defend rout: the men run to cover at their post, then defend.
                              No new actor or squad (census %(census)s, cap %(cap)s).

Install:  INSTALL.bat  (or: python install.py)     Undo: UNDO.bat  (or: python install.py --undo)     Check only: python install.py --dry
Close the game first. Pinned live md5s: %(pins)s
If another %(map)s step changed the files since, install.py REFUSES (re-stage: python tools/kl_smartcops_1110.py stage --map %(map)s).
Choose the parts at staging (--parts cover | runcover | cover,runcover): two zip pairs of the same names cannot be installed together, so a different choice = re-stage.

NOT run in the game (the owner is playing). GUESSes to bench: (1) the RunToCover rout hands over to its NEXT (the Defend rout) once the man is in cover
(the stock F07 forms have an empty NEXT, the F04 ones a trigger); if it does not, the squads would stay in cover instead of walking to their posts;
(2) a RunToPosInfo at the post picks the cover box nearest to it; (3) KL_Kick! door squads are left alone. Bench: the first minute of round 1, look for
the Wave_1/2/3 and shop men going to the new boxes. Open: RandomTrigger lane splits (eDMS_Run Defend chains) and moving the remaining weak posts.
'''


# ------------------------------------------------------------------ pipeline
def _imports():
    import kl_fa, kl_fa_bots as F, kl_fa_cover as C, kl_cover_add as A, kl_cover_1026 as K, kl_loot_1025 as LO
    return kl_fa, F, C, A, K, LO


def live_dir(map_, game=GAME):
    return os.path.join(game, 'KLExpansion', 'Maps', map_)


def posts_of(B, cfg):
    """Every enemy DefendBehaviourRout Pos: [dict(squad, rout, name, pos)] (kl_fa.controllers: field 0 + field 1 are the place references)."""
    import kl_fa
    sc, out = B.sc, []
    for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout'):
        p = sc.path[k].replace(R, '')
        if not p.startswith(cfg['enemy']):
            continue
        tg = ([v[0]] if v[0] else []) + list(v[1])
        for s in tg:
            for j in (sc.resolve(s) if isinstance(s, str) else []):
                out.append(dict(squad=p.split(BS)[0], rout=p.split(BS)[-1], name=sc.names[j], pos=tuple(B.at(j))))
    return out


def measure(zp, cfg, log=print):
    """-> (L, report): box counts and the weak-post table."""
    kl_fa, F, C, A, K, LO = _imports()
    A.use_slot(zp)
    L = A.Lite(zp)
    sc = L.B.sc
    kinded = [b for b in L.boxes if b['kind']]
    mids = [b['mid'] for b in kinded]
    posts = posts_of(L.B, cfg)
    for p in posts:
        p['n'] = near_count(p['pos'], mids)
    by = collections.OrderedDict()
    for p in posts:
        s = by.setdefault(p['squad'], dict(posts=0, none=0, weak=0))
        s['posts'] += 1
        s['none'] += p['n'] == 0
        s['weak'] += p['n'] < NEED
    r = collections.OrderedDict(entities=len(L.B.ents), boxes=len(kinded), high=sum(1 for b in kinded if b['kind'] == 'high'), low=sum(1 for b in kinded if b['kind'] == 'low'),
                                records=len(L.boxes), nocover=len(L.nocover), ffcoverlist=len(kl_fa.controllers(sc, 'FFCoverList')),
                                posts=len(posts), none=sum(1 for p in posts if p['n'] == 0), weak=sum(1 for p in posts if p['n'] < NEED),
                                by_squad=by, weak_list=[dict(p, pos=[round(v) for v in p['pos']]) for p in posts if p['n'] < NEED],
                                rc_rouths=len(kl_fa.controllers(sc, 'RunToCoverBehaviourRout')))
    log('measure %s: %d boxes, %d enemy posts, %d with no box within %d cm, %d with fewer than %d, %d RunToCover routs' % (
        os.path.basename(zp), r['boxes'], r['posts'], r['none'], NEAR, r['weak'], NEED, r['rc_rouths']))
    return L, r


def plan_cover(zp, cfg, o, log=print):
    """-> (L, P, report). P = {'boxes': [...]} for kl_fa_cover.apply."""
    kl_fa, F, C, A, K, LO = _imports()
    A.use_slot(zp)
    C.GROUP, C.TAG = GROUP, TAG
    L, before = measure(zp, cfg, log)
    if not ffcover_ok(before['ffcoverlist']):
        raise SystemExit('REFUSED: the live zip has %d FFCoverList (the stage keeps exactly one)' % before['ffcoverlist'])
    if any(L.B.sc.names[k] == GROUP for k in range(1, len(L.B.sc.nodes))):
        log('the %s group is already in this zip: nothing to add (idempotent)' % GROUP)
        return L, dict(boxes=[]), dict(before=before, added=0)
    weak = before['weak_list']
    if not weak:
        return L, dict(boxes=[]), dict(before=before, added=0)
    fs = C.forms(L.B, L.boxes, 'b', True)
    log('box models a new box may take: %s' % sorted('%dx%dx%d' % tuple(f['size']) for f in fs))
    ok0 = list(L.nav.ok)
    L.nav.ok[:] = disc_mask(L.nav.mid, ok0, [w['pos'] for w in weak], o['reach'])      # walls() / sparse() pick their places only near a weak post
    log('mesh polygons kept near the %d weak posts: %d of %d' % (len(weak), sum(L.nav.ok), sum(ok0)))
    import kl_cover_floornav as FN
    sf0, gr0 = K.safety_features, FN.Ground

    def unmasked(fn):                  # spawn / loot stations and the reachable-floor grid need the WHOLE mesh
        def w(*a, **k):
            m = list(L.nav.ok)
            L.nav.ok[:] = ok0
            try:
                return fn(*a, **k)
            finally:
                L.nav.ok[:] = m
        return w
    K.safety_features, FN.Ground = unmasked(sf0), unmasked(gr0)
    new = []
    try:
        if fs:
            K.walls(L, fs, new, o['max_walls'], o['density'], o['spread'], log, True, True)
            A.sparse(L, fs, new, len(new) + o['max_sparse'], o['spread'], log)
    finally:
        K.safety_features, FN.Ground = sf0, gr0
        L.nav.ok[:] = ok0
    keep = []
    dropped = collections.Counter()
    for b in new:
        if L.exits and F.in_exit(L.B, L.exits, b['mid']):
            dropped['boarding box'] += 1
            continue
        keep.append(b)
    if not cap_ok(before['boxes'] + len(keep)):
        raise SystemExit('REFUSED: %d boxes + %d new is over the cap %d' % (before['boxes'], len(keep), CAP_TOTAL))
    cnt = collections.Counter()
    for c in keep:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', TAG, cnt[c['kind']])
    P = collections.OrderedDict(folder=L.folder, options=dict(o), boxes=keep)
    rep = collections.OrderedDict(before=before, added=len(keep), wall=sum(1 for b in keep if b['via'] == 'wall'), sparse=sum(1 for b in keep if b['via'] == 'sparse'),
                                  dropped=dict(dropped))
    log('PLAN: %d boxes (%d low, %d high): %d wall, %d sparse; dropped: %s' % (len(keep), cnt['low'], cnt['high'], rep['wall'], rep['sparse'], dict(dropped)))
    return L, P, rep


def build_cover(zp, slot, work, P, log=print):
    """Write P into a copy of `zp` (as <work>/in/<slot>_Main.zip: the checkers open <slot>_Main.zip) -> (member-patched zip, report)."""
    kl_fa, F, C, A, K, LO = _imports()
    src = os.path.join(work, 'in', slot + '_Main.zip')
    os.makedirs(os.path.dirname(src), exist_ok=True)
    shutil.copyfile(zp, src)
    mid = os.path.join(work, 'mid')
    LO.rmtree(mid)
    os.makedirs(mid)
    A.use_slot(src)
    C.GROUP, C.TAG = GROUP, TAG
    L = A.Lite(src)
    rep = C.apply(L, P, mid, log)
    rep['plan'] = P
    with open(os.path.join(mid, 'cover.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out = C.check(mid, log)
    fails = [t for s, t in out if s == 'FAIL']
    bad = C.diff(L.folder, mid, log)
    if fails or bad:
        raise SystemExit('check FAIL %s / diff %s' % (fails[:4], bad))
    new_zip = os.path.join(mid, slot + '_Main.zip')
    with zipfile.ZipFile(new_zip) as z, zipfile.ZipFile(src) as a:
        repl = {i.filename: z.read(i.filename) for i in a.infolist() if z.read(i.filename) != a.read(i.filename)}
    final = os.path.join(work, 'final.zip')
    LO.patch_zip(src, final, repl)
    members = sorted(n.rsplit('_Main', 1)[-1] for n in repl)
    LO.rmtree(mid)
    os.remove(src)
    return final, dict(members_changed=members, check_lines=len(out), check_notes=sum(1 for s, _t in out if s == 'NOTE'))


def prune_unreachable(zp, slot, work, P, log=print):
    """Build P once, run kl_cover_floornav.check and drop every new box with no usable side. -> (P filtered and renamed, dropped)."""
    kl_fa, F, C, A, K, LO = _imports()
    import kl_cover_floornav as FN
    pw = os.path.join(work, 'prune')
    fin, _r = build_cover(zp, slot, pw, json.loads(json.dumps(P, default=str)), log)
    chk = os.path.join(pw, 'chk')
    os.makedirs(chk, exist_ok=True)
    z = os.path.join(chk, slot + '_Main.zip')
    shutil.copyfile(fin, z)
    A.use_slot(z)
    rep = FN.check(A.Lite(z), {}, lambda *a: None)
    bad = []
    for r in rep['boxes'].values():
        if TAG not in r['name'] or r['any']:
            continue
        for b in P['boxes']:
            if abs(b['mid'][0] - r['mid'][0]) < 2 and abs(b['mid'][2] - r['mid'][2]) < 2:
                bad.append(b)
    A.use_slot(zp)
    LO.rmtree(pw)
    if not bad:
        return P, []
    ids = {id(b) for b in bad}
    P = collections.OrderedDict(P)
    P['boxes'] = [b for b in P['boxes'] if id(b) not in ids]
    cnt = collections.Counter()
    for c in P['boxes']:
        cnt[c['kind']] += 1
        c['name'] = 'CoverBox%s%s%02d' % ('H' if c['kind'] == 'high' else 'M', TAG, cnt[c['kind']])
    for b in bad:
        log('PRUNED (no reachable side): %s at %s via %s' % (b.get('name'), [round(v) for v in b['mid']], b.get('via')))
    return P, bad


# ------------------------------------------------------------------ runcover
def rc_targets(B, cfg, log=print):
    """-> [dict(top, defend, actors [group node], posts [node], starters [(holder node, ctrl, field)])] for the squads that can take a RunToCover step."""
    import kl_fa, kl_prpjoin as J
    sc = B.sc
    refs = collections.defaultdict(list)
    for k, holder, field, s, _hit in J.references(sc):
        if k >= 0:
            refs[s.lower()].append((k, holder, field))
    ctl = lambda k: [sc.p.key(c[0]) for c in sc.nodes[k]['ctrls']]
    out = []
    for name in cfg['squads']:
        tt = sc.resolve(R + name)
        if len(tt) != 1:
            log('  skip %s: %d nodes' % (name, len(tt)))
            continue
        t = tt[0]
        kids = [j for j in range(t + 1, sc.end[t]) if sc.parent[j] == t]
        if any(sc.names[j] == RC_NAME for j in kids):
            log('  skip %s: has %s already' % (name, RC_NAME))
            continue
        d = [j for j in kids if 'DefendBehaviourRout' in ctl(j)]
        if len(d) != 1:
            log('  skip %s: %d Defend routs' % (name, len(d)))
            continue
        d = d[0]
        grp = [j for j in kids if any(sc.names[c] == 'Ground' and sc.parent[c] == j for c in range(j + 1, sc.end[j]))]
        v = next(v for k2, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout') if k2 == d)
        posts = [j for s in (([v[0]] if v[0] else []) + list(v[1])) for j in (sc.resolve(s) if isinstance(s, str) else [])]
        starters = []
        for k, holder, field in refs.get(sc.path[d].lower(), []):
            ph = parse_holder(holder, field)
            if ph is None:
                log('  skip %s: unparsed reference holder %r %r' % (name, holder, field))
                starters = None
                break
            starters.append((k, ph[0], ph[1]))
        if not grp or not posts or not starters:
            log('  skip %s: %d actor groups, %d posts, starters %s' % (name, len(grp), len(posts), starters))
            continue
        if any(abs(c) > 0.5 for c in B.at(t)[:3]):
            log('  skip %s: the squad top is not at the origin (%s)' % (name, B.at(t)))
            continue
        out.append(dict(name=name, top=t, defend=d, actors=grp, posts=posts, starters=starters))
    return out


def build_runcover(src, slot, dst, cfg, log=print):
    """src zip -> dst zip with the RunToCover steps -> report. Nothing to do -> md5_out None, nothing written."""
    import kl_fa, kl_gms, kl_graft, kl_scene, kl_fa_bank
    import kl_fa_bots as KB, kl_fa_author as AU, kl_octree as O, kl_prpjoin as J
    import kl_dm02_assault_1025 as AS
    from kl_prp import Prp
    import kl_bots_kick_1025 as KK
    B = KB.Built(src, slot)
    sc = B.sc
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    nav = KB.Nav(A.nav, links=True)
    a0, s0 = AS.census(sc)
    T = rc_targets(B, cfg, log)
    if not T:
        log('  no squad to change')
        return collections.OrderedDict(md5_in=fmd5(src), md5_out=None, squads=[])
    # ---- the nodes: one RunToCover group per squad, one PosInfo kid per actor at its own post
    M = KB.Maker()
    tops, per, specs = [], collections.OrderedDict(), []
    for tg in T:
        posts = [dict(node=j, pos=tuple(B.at(j))) for j in tg['posts']]
        pick = assign_posts(len(tg['actors']), posts)
        g = M.clone(RC_SRC[0], R + RC_SRC[1], RC_NAME)
        M.place(g, (0.0, 0.0, 0.0))
        M.set(g, 'RunToCoverBehaviourRout', {0: [sc.path[tg['defend']]]})
        infos = []
        for i, (ag, ps) in enumerate(zip(tg['actors'], pick)):
            pi = g.add(M.clone(RC_SRC[0], R + RC_SRC[1] + BS + 'RunToPosInfo#08', 'RunToPosInfo#%02d' % (i + 1)))
            M.place(pi, ps['pos'])
            M.set(pi, 'RunToCoverPosInfoRout', {5: sc.path[ag]})
            infos.append((sc.names[ag], sc.names[ps['node']], [round(v) for v in ps['pos']]))
        tops.append(g)
        per[tg['top']] = [len(tops) - 1]
        specs.append(dict(name=tg['name'], infos=infos, starters=tg['starters']))
    n_pi = sum(len(s['infos']) for s in specs)
    if not budget_ok(a0, s0):
        raise ValueError('budget %d / %d' % (a0, s0))
    q, order = M.scene(tops)
    qt = q.tops()
    if len(qt) != len(tops):
        raise ValueError('scene: %d tops for %d nodes' % (len(qt), len(tops)))
    adopt = {t: [(q, qt[i]) for i in idx] for t, idx in per.items()}
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'smartcops', adopt=adopt)
    # ---- every starter of the Defend rout now names the RunToCover rout
    swapped = 0
    for tg in T:
        old, new = sc.path[tg['defend']], R + sc.names[tg['top']] + BS + RC_NAME
        for k, cn, f in tg['starters']:
            kh = Jn.resolve(sc.path[k])
            if len(kh) != 1:
                raise ValueError('%s: %d nodes in the joined tree' % (sc.path[k], len(kh)))
            kh = kh[0]
            ci = AU.ctrl_of(Jn, kh, cn)
            cnt = [0]

            def fn(us, f=f, old=old, new=new, cnt=cnt):
                u = us[f]
                if u[0][0] == 0x04:
                    ks, n = swap_entry([Jn.p.key(x) for x in u[1:]], old, new)
                    us[f] = kl_fa._refs(Jn, ks)
                elif u[0][0] == 0x0c:
                    ks, n = swap_entry([Jn.p.key(u[0])], old, new)
                    us[f] = kl_fa._refs(Jn, ks)[1:] if False else [(0x0c, struct.pack('<I', Jn.p.key_index(ks[0])))]
                else:
                    n = 0
                cnt[0] += n
            kl_fa.edit(Jn, kh, ci, fn)
            if cnt[0] != 1:
                raise ValueError('%s %s[%d] names %s %d times (expected 1)' % (sc.path[k], cn, f, old, cnt[0]))
            swapped += 1
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if (fa, fs) != (a0, s0):
        raise ValueError('census changed %d / %d -> %d / %d' % (a0, s0, fa, fs))
    log('  %d RunToCover groups (+ %d PosInfo kids), %d starter entries swapped, census %d / %d unchanged' % (len(tops), n_pi, swapped, a0, s0))
    # ---- .gms / .buf: the new entities are the last kids of their squad tops
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
        e.ref = nxt
        nxt += 1
        e.parent = parent
        e.kids = []
        parent.kids.append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t, idx in per.items():
        for i in idx:
            ent(tops[i], B.ents[t - 1])
    A.ref_slots = max(A.ref_slots, nxt)
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    # the squad's step groups are listed in the root's group tree 3 when the Defend rout is (kl_fa_bots.apply): ours join them, box = the PosInfo kids +- 10
    r3 = octx.rooms[0][3]
    in3 = {it[0] for it in (r3.items if r3 is not None else [])}
    items = []
    for tg, nd in zip(T, tops):
        if (slot0[B.ents[tg['defend'] - 1]] + 2) in in3:
            pts = [k.pos for k in nd.kids]
            items.append((slot1[made[id(nd)]] + 2, tuple(min(p[a] for p in pts) - 10.0 for a in range(3)), tuple(max(p[a] for p in pts) + 10.0 for a in range(3))))
    repointed, new_prm = 0, None
    if items:
        r3n = octn.rooms[0][3]
        octn.rooms[0][3] = O.join_trees(r3n, O.build_tree(items, r3n.origin, r3n.scale))
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(B['.prm'])
            tt, nn = struct.unpack_from('<II', prm, 0)
            old = set(octx.record_refs())
            for i in range(1, nn):
                off, size = struct.unpack_from('<II', prm, tt + 16 * i)
                if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, off + 0x1c, move[v])
                        repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('room sets after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    repl = {B.ext[e]: new[B.ext[e]] for e in changed}
    work = tempfile.mkdtemp(prefix='smartcops_')
    try:
        wz = os.path.join(work, slot + '_Main.zip')
        KK.patch_zip(src, wz, repl)
        counts = []
        for zsrc in (src, wz):                                  # seal on throwaway COPIES: the stray room-list entries it moves must be the input's own
            tmpd = tempfile.mkdtemp(prefix='smartcops_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, slot + '_Main.zip'))
                counts.append(kl_fa_bank.seal(tmpd, log=lambda *_: None))
            finally:
                KK.rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        problems = kl_fa_bank.reverify(work, log=lambda *_: None)
        wi = tempfile.mkdtemp(prefix='smartcops_in_')
        try:
            shutil.copyfile(src, os.path.join(wi, slot + '_Main.zip'))
            base_problems = kl_fa_bank.reverify(wi, log=lambda *_: None)
        finally:
            KK.rmtree(wi)
        problems = [x for x in problems if x not in base_problems]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(wz, dst)
    finally:
        KK.rmtree(work)
    log('  members changed: %s; %d entities added, %d slot ids renumbered, %d tree-3 items, %d .prm roots re-pointed' % (' '.join(changed), len(order), moved, len(items), repointed))
    return collections.OrderedDict(md5_in=fmd5(src), md5_out=fmd5(dst), members_changed=changed, entities_before=len(B.ents), entities=len(allents), added=len(order),
                                   squads=specs, swapped=swapped, slot_ids_moved=moved, tree3_items=len(items), prm_roots_repointed=repointed, census=[a0, s0], pi=n_pi)


# ------------------------------------------------------------------ stage
def checks(zp, slot, log=print):
    """debug/check.py (0 bad) and debug/check_passes.py (no FAIL) on a staged zip (read only) -> dict."""
    out = collections.OrderedDict()
    dbg = os.path.join(os.path.dirname(HERE), 'debug')
    for nm in ('check.py', 'check_passes.py'):
        t = subprocess.run([sys.executable, os.path.join(dbg, nm), zp], capture_output=True, text=True, cwd=dbg)
        txt = (t.stdout or '') + (t.stderr or '')
        out[nm] = dict(rc=t.returncode, tail=txt.strip().splitlines()[-6:])
        log('  %s rc=%d: %s' % (nm, t.returncode, out[nm]['tail'][-1] if out[nm]['tail'] else ''))
    return out


def stage(out, map_, parts, game=GAME, rehearse=True, log=print):
    kl_fa, F, C, A, K, LO = _imports()
    cfg = MAPS[map_]
    slot, FILES = cfg['slot'], cfg['files']
    d = live_dir(map_, game)
    live = {n: os.path.join(d, n) for n in FILES}
    pins = {n: fmd5(p) for n, p in live.items()}
    if open(live[FILES[2]]).read().strip() != pins[FILES[0]]:
        raise SystemExit('REFUSED: the live bots.base.md5 is not the live plain zip md5')
    need = 8 * os.path.getsize(live[FILES[0]]) + FREE_KEEP
    os.makedirs(out, exist_ok=True)
    if shutil.disk_usage(out).free < need:
        raise SystemExit('REFUSED: less than %d MB free on the stage drive' % (need >> 20))
    work = os.path.join(out, 'work')
    LO.rmtree(work)
    os.makedirs(work)
    for f in os.listdir(out):
        p = os.path.join(out, f)
        if p != work and os.path.isfile(p):
            os.remove(p)
    log('live pins: %s' % pins)
    for f in os.listdir(d):                                         # the small files beside the zip (the checkers read the .ini)
        if f.lower().endswith('.ini') and os.path.isfile(os.path.join(d, f)):
            os.makedirs(os.path.join(work, 'in'), exist_ok=True)
            shutil.copyfile(os.path.join(d, f), os.path.join(work, 'in', f))
    o = dict(density=DENSITY, max_walls=MAX_WALLS, max_sparse=MAX_SPARSE, spread=SPREAD, reach=REACH)
    _L0, m0 = measure(live[FILES[0]], cfg, log)
    P0, rep_c, cur = None, dict(added=0, before=m0), {n: live[n] for n in FILES[:2]}
    if 'cover' in parts:
        L, P, rep_c = plan_cover(live[FILES[0]], cfg, o, log)
        if P['boxes']:
            P, pruned = prune_unreachable(live[FILES[0]], slot, work, P, log)
            rep_c['pruned_unreachable'] = [dict(name=b.get('name'), mid=b['mid'], via=b.get('via')) for b in pruned]
            rep_c['added'] = len(P['boxes'])
            rep_c['sparse'] -= sum(1 for b in pruned if b.get('via') == 'sparse')
            rep_c['wall'] -= sum(1 for b in pruned if b.get('via') == 'wall')
        P0 = json.loads(json.dumps(P, default=str))
        for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
            if not P0['boxes']:
                break
            log('== cover %s' % name)
            P1 = json.loads(json.dumps(P0))
            for b in P1['boxes']:
                b['mid'] = list(b['mid'])
            fin, r = build_cover(live[name], slot, os.path.join(work, 'c_' + key), P1, log)
            cur[name] = os.path.join(work, 'cover_' + name)
            shutil.move(fin, cur[name])
            rep_c.setdefault('built', {})[key] = r
    res_rc = {}
    finals = {}
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        dst = os.path.join(out, name)
        if 'runcover' in parts:
            log('== runcover %s' % name)
            sdir = os.path.join(work, 'rc_' + key)
            os.makedirs(sdir, exist_ok=True)
            srcz = os.path.join(sdir, slot + '_Main.zip')            # Built wants the <slot>_Main name next to the .ini files
            shutil.copyfile(cur[name], srcz)
            r = build_runcover(srcz, slot, dst, cfg, log)
            if r['md5_out'] is None:
                raise SystemExit('runcover: nothing to change in %s' % name)
            res_rc[key] = r
        else:
            shutil.copyfile(cur[name], dst)
        finals[name] = dst
    base = fmd5(finals[FILES[0]])
    open(os.path.join(out, FILES[2]), 'w', newline='\n').write(base + '\n')
    after, ck = {}, {}
    for key, name in (('plain', FILES[0]), ('bots', FILES[1])):
        _L, m = measure(finals[name], cfg, log)
        after[key] = m
        if not ffcover_ok(m['ffcoverlist']):
            raise SystemExit('REFUSED: %s has %d FFCoverList after' % (name, m['ffcoverlist']))
        if not cap_ok(m['boxes']):
            raise SystemExit('REFUSED: %s has %d boxes after' % (name, m['boxes']))
        want = m0['boxes'] + (rep_c['added'] if 'cover' in parts else 0)
        if m['boxes'] != want or m['nocover'] != m0['nocover']:
            raise SystemExit('REFUSED: %s: %d boxes after, expected %d; NoCoverBox %d -> %d' % (name, m['boxes'], want, m0['nocover'], m['nocover']))
        if 'runcover' in parts and m['rc_rouths'] != m0['rc_rouths'] + len(res_rc[key]['squads']):
            raise SystemExit('REFUSED: %s: %d RunToCover routs after, expected %d' % (name, m['rc_rouths'], m0['rc_rouths'] + len(res_rc[key]['squads'])))
        ck[name] = checks(finals[name], slot, log)
    files = [(FILES[0], pins[FILES[0]], base), (FILES[1], pins[FILES[1]], fmd5(finals[FILES[1]])), (FILES[2], pins[FILES[2]], fmd5(os.path.join(out, FILES[2])))]
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(render_install(files, game, map_=map_))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    a = after['plain']
    rc = res_rc.get('plain', dict(squads=[], pi=0, census=['-', '-']))
    open(os.path.join(out, 'README.txt'), 'w', newline='\n').write(README % dict(
        map=map_, parts=','.join(parts), files=' '.join(FILES), group=GROUP, need=NEED, nposts=m0['posts'], weak0=m0['weak'], weak1=a['weak'], none0=m0['none'], none1=a['none'],
        n_cover=rep_c['added'] if 'cover' in parts else 0, b0=m0['boxes'], b1=a['boxes'], n_rc=len(rc['squads']), n_pi=rc['pi'],
        census='%s / %s' % tuple(rc['census']), cap='%d / %d' % (ENGINE_ACTORS, ENGINE_SQUADS), pins=', '.join('%s %s' % (n, h[:8]) for n, h in pins.items())))
    report = collections.OrderedDict(map=map_, parts=parts, pins=pins, files=files, before=m0, after=after, cover=rep_c, runcover=res_rc, checks=ck, options=o)
    with open(os.path.join(out, 'build_report.json'), 'w') as f:
        json.dump(report, f, indent=1, default=str)
    if P0:
        with open(os.path.join(out, 'cover_plan.json'), 'w') as f:
            json.dump(P0['boxes'], f, indent=0, default=str)
    LO.rmtree(work)
    if rehearse:
        rehearsal(out, files, map_, game, log)
    for n, o_, w in files:
        log('%-26s %s -> %s' % (n, o_, w))
    return report


def rehearsal(out, files, map_, game, log=print):
    """Install, 2nd install refused, --dry, undo byte-exact, 2nd undo refused - on a COPY of the live files in <out>_scratch; deleted afterwards."""
    kl_fa, F, C, A, K, LO = _imports()
    scratch = os.path.abspath(out) + '_scratch'
    assert os.path.abspath(scratch).lower() != os.path.abspath(game).lower()
    LO.rmtree(scratch)
    g = os.path.join(scratch, 'game')
    d = os.path.join(g, 'KLExpansion', 'Maps', map_)
    os.makedirs(d)
    try:
        for n, old, _new in files:
            shutil.copyfile(os.path.join(live_dir(map_, game), n), os.path.join(d, n))
        run = lambda *x: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--root', g, '--skip-run-check'] + list(x), capture_output=True, text=True)
        steps = []
        t = run('--dry'); steps.append(('dry', t.returncode == 0 and 'would install' in t.stdout and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files)))
        t = run(); steps.append(('install', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == w for n, _o, w in files) and all(fmd5(os.path.join(d, n + TAG_BAK)) == o for n, o, _w in files)))
        t = run(); steps.append(('2nd install refused', t.returncode == 1 and 'REFUSED' in t.stdout and all(fmd5(os.path.join(d, n)) == w for n, _o, w in files)))
        t = run('--undo', '--dry'); steps.append(('undo dry', t.returncode == 0 and 'would restore' in t.stdout))
        t = run('--undo'); steps.append(('undo byte-exact', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files) and not any(os.path.exists(os.path.join(d, n + TAG_BAK)) for n, _o, _w in files)))
        t = run('--undo'); steps.append(('2nd undo refused', t.returncode == 1 and 'REFUSED' in t.stdout))
        t = run(); steps.append(('reinstall after undo', t.returncode == 0))
        t = run('--undo'); steps.append(('final undo byte-exact', t.returncode == 0 and all(fmd5(os.path.join(d, n)) == o for n, o, _w in files)))
        for s, ok in steps:
            log('  rehearsal %-24s %s' % (s, 'PASS' if ok else 'FAIL'))
        if not all(ok for _s, ok in steps):
            raise SystemExit('rehearsal FAILED')
    finally:
        LO.rmtree(scratch)
        log('  scratch %s %s' % (scratch, 'deleted' if not os.path.exists(scratch) else 'STILL THERE'))


def main(argv):
    if not argv or argv[0] not in ('measure', 'plan', 'stage'):
        print(__doc__)
        return 2
    a, map_, parts, rehearse, rest, game = list(argv[1:]), 'DM01', list(PARTS), True, [], GAME
    while a:
        x = a.pop(0)
        if x == '--map': map_ = a.pop(0)
        elif x == '--parts': parts = parts_ok(a.pop(0))
        elif x == '--game': game = a.pop(0)
        elif x == '--no-rehearse': rehearse = False
        else: rest.append(x)
    if map_ not in MAPS:
        raise SystemExit('--map %s: configured maps are %s' % (map_, ', '.join(MAPS)))
    cfg = MAPS[map_]
    live = os.path.join(live_dir(map_, game), cfg['files'][0])
    if argv[0] == 'measure':
        _L, r = measure(rest[0] if rest else live, cfg)
        print(json.dumps(r, indent=1, default=str))
    elif argv[0] == 'plan':
        o = dict(density=DENSITY, max_walls=MAX_WALLS, max_sparse=MAX_SPARSE, spread=SPREAD, reach=REACH)
        _L, P, rep = plan_cover(rest[0] if rest else live, cfg, o)
        print(json.dumps(dict(rep, boxes=[{k: b[k] for k in ('name', 'kind', 'via', 'mid', 'object') if k in b} for b in P['boxes']]), indent=1, default=str))
    else:
        stage(rest[0] if rest else os.path.join(OUT_ROOT, map_), map_, parts, game, rehearse)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
