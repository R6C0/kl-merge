"""kl_cover_stage_1026.py - stage the player-cover pass (tools/kl_cover_1026.py) for the expansion maps (2026-10-26).
OFFLINE: reads the LIVE zips, writes only under <root>/<MAP>/{in,mid,stage}. Nothing is installed.

Per map: the live zip is copied to <root>/<MAP>/in/, kl_cover_1026.build() runs on it (kl_fa_cover.apply + check + diff), the 7 members
it changes (.buf .gms .oct .prm .prp .rmc .rmi) are patched INTO THE LIVE ZIP BYTES (member-level, every other member and the zip
layout untouched, kl_loot_1025.patch_zip) -> <root>/<MAP>/stage/{<zip>, install.py, build_report.json}. install.py pins the live md5
(refuses when it moved), refuses while kl2.exe runs, moves the original to '<zip>.before-1026cover'; --undo puts it back.
The pass is idempotent (a zip that already has the KL_CoverSix! group is left alone: 'nothing to add').
REPLACE (2026-10-26, --replace): the live zip already holds a KL_CoverSix! group whose boxes failed the floor + nav check (tools/kl_cover_floornav.py: DM05A live 4a6799a1,
25+ of 93 boxes on no floor / no mesh). The group is TAKEN OUT of a copy of the live zip (kl_cover_strip_1026: the inverse of the add, member level, 7 members), a new group is
planned on that base with the floor + nav filter (kl_cover_1026 FLOORNAV, --no-floornav turns it off), and the members that differ from the LIVE zip are patched into the live bytes.
install.py pins the live md5 and keeps the original as '<zip>.before-1026cover2' (the first cover's '.before-1026cover' stays untouched); --undo puts it back.
RE-STAGE after another step changed a zip:   python kl_cover_stage_1026.py stage C:/kl_build_1024/cover_1026 [DM01 DM02 ...] [--rehearse <scratch>] [--no-safety] [--no-floornav] [--replace]
(it always starts from whatever is live at that moment, and the md5 pin of install.py is that zip).
"""
import collections, glob, json, os, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loot_1025 as LO
import kl_cover_1026 as K
import kl_cover_add as A
import kl_cover_strip_1026 as S

GAME = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
TAG = '.before-1026cover'
TAG2 = '.before-1026cover2'      # --replace: the first cover's backup file keeps its name
REPLACE = False
TIERS_ALL = None             # --tiers a|b|ab: override of the box-model forms for every staged map (2026-10-26 COVER8: 'a' = clone only stock-proven form a boxes)
TAG_OVERRIDE = None          # --tag .before-xxx: the backup name install.py uses (COVER8: '.before-1026coverfix')
FREE_KEEP = 6 << 30             # keep this much free on the stage drive (job brief: 6 GB)
MAPS = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B', 'DD10']
OPT = {'max': K.MAX_NEW, 'density': K.DENSITY, 'spread': K.SPREAD, 'safety': K.SAFETY, 'floornav': K.FLOORNAV}   # safety = kl_cover_1026 filter rules (recommended on); stage ... --no-safety turns them off
TIERS = {'DM07': 'ab'}    # maps with no hidden form-b box model (DM07: 'box models: []'): clone form a boxes too (kl_cover_1026 --tiers ab; GUESS: a form a
                          # clone, with the collision record of its model listed in tree 0, is a harmless cover box - proven only on the Dig's pass)
INSTALL_PY = LO.INSTALL_PY.replace('loot-placement', 'player-cover (KL_CoverSix! boxes)').replace('tools/kl_loot_1025.py', 'tools/kl_cover_stage_1026.py')


FROM = None      # --from <root>: take <root>/<MAP>/stage/*_Main.zip (another agent's staged, not yet installed zip) as the input when there is one


def live_zip(name):
    if FROM:
        g = glob.glob('%s/%s/stage/*_Main.zip' % (FROM, name))
        if g:
            return g[0]
    return glob.glob('%s/KLExpansion/Maps/%s/*_Main.zip' % (GAME, name))[0]


def counts(zp):
    """(cover boxes, NoCoverBox, mesh m2) of a zip, by kl_cover_add.Lite."""
    A.use_slot(zp)
    L = A.Lite(zp)
    area = sum(K._area(L.nav.pv[i]) for i in range(len(L.nav.pv)) if L.nav.ok[i]) / 1e4
    return len([b for b in L.boxes if b['kind']]), len(L.nocover), round(area)


def stage_map(root, name, scratch=None, log=print):
    live = os.path.normpath(live_zip(name))
    zn = os.path.basename(live)
    d = os.path.join(root, name)
    LO.rmtree(os.path.join(d, 'in')); LO.rmtree(os.path.join(d, 'mid')); LO.rmtree(os.path.join(d, 'stage'))
    os.makedirs(os.path.join(d, 'in')); os.makedirs(os.path.join(d, 'stage'))
    need = 5 * os.path.getsize(live) + FREE_KEEP            # in + strip + mid + stage + the rehearsal's copy
    if shutil.disk_usage(root).free < need:
        raise SystemExit('REFUSED: %s: less than %d MB free on the stage drive (5 zips + 6 GB kept)' % (name, need >> 20))
    src = os.path.join(d, 'in', zn)
    shutil.copyfile(live, src)
    for f in os.listdir(os.path.dirname(live)):                    # the small files beside it (the checkers read the .ini)
        if f.lower().endswith('.ini'):
            shutil.copyfile(os.path.join(os.path.dirname(live), f), os.path.join(d, 'in', f))
    h = LO.md5(src)
    log('== %s (%s) md5 %s ==' % (name, zn, h))
    n0, nc0, area = counts(src)
    mid = os.path.join(d, 'mid')
    base, strip_rep = src, None
    if REPLACE:
        repl0, strip_rep = S.strip(src, log)
        if repl0 is not None:
            LO.rmtree(os.path.join(d, 'strip'))
            os.makedirs(os.path.join(d, 'strip'))
            for f in os.listdir(os.path.join(d, 'in')):
                if f.lower().endswith('.ini'):
                    shutil.copyfile(os.path.join(d, 'in', f), os.path.join(d, 'strip', f))
            base = os.path.join(d, 'strip', zn)
            LO.patch_zip(src, base, repl0)
            nb, ncb, _a = counts(base)
            if ncb != nc0 or nb != n0 - strip_rep['removed'] + 1:
                raise SystemExit('%s: stripped base has %d boxes / %d NoCoverBox (live %d / %d, group %d entities)' % (name, nb, ncb, n0, nc0, strip_rep['removed']))
            log('  base without the old group: %d cover boxes (live %d)' % (nb, n0))
    tag = TAG_OVERRIDE or (TAG2 if REPLACE else TAG)
    L, rep, out, bad = K.build(base, mid, dict(OPT, tiers=TIERS_ALL or TIERS.get(name, K.TIERS)), log)
    if rep is None:
        log('  nothing to add (already has the group, or no model fits)')
        return None
    fails = [t for s, t in out if s == 'FAIL']
    if fails or bad:
        raise SystemExit('%s: check FAIL %s / diff %s' % (name, fails[:3], bad))
    new_zip = os.path.join(mid, zn)
    with zipfile.ZipFile(new_zip) as z, zipfile.ZipFile(src) as a:
        repl = {i.filename: z.read(i.filename) for i in a.infolist() if z.read(i.filename) != a.read(i.filename)}
    if REPLACE and not {n.rsplit('_Main', 1)[-1] for n in repl} <= {'.buf', '.gms', '.oct', '.prm', '.prp', '.rmc', '.rmi'}:    # (a member the new group leaves as the live one was, e.g. .prm, is not patched)
        raise SystemExit('%s: members to patch into the live zip: %s' % (name, sorted(repl)))
    final = os.path.join(d, 'stage', zn)
    LO.patch_zip(src, final, repl)
    h2 = LO.md5(final)
    n1, nc1, _a = counts(final)
    rep2 = collections.OrderedDict(map=name, zip=zn, md5_in=h, md5_out=h2, members_changed=sorted(n.rsplit('_Main', 1)[-1] for n in repl),
                                   boxes_before=n0, boxes_after=n1, added=n1 - n0, nocover_before=nc0, nocover_after=nc1, mesh_m2=area,
                                   per100_before=round(n0 / area * 100, 2), per100_after=round(n1 / area * 100, 2),
                                   kinds_added=dict(collections.Counter(b['kind'] for b in rep['plan']['boxes'])),
                                   replaced=strip_rep, tag=tag, check_lines=len(out), options=dict(OPT, tiers=TIERS_ALL or TIERS.get(name, K.TIERS)),
                                   tier_a_added=sum(1 for b in rep['plan']['boxes'] if b['tier'] == 'a'))
    if nc1 != nc0:
        raise SystemExit('%s: NoCoverBox count changed %d -> %d' % (name, nc0, nc1))
    with open(os.path.join(d, 'stage', 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=zn, tag=tag, game=GAME, old=h, new=h2))
    with open(os.path.join(d, 'stage', 'build_report.json'), 'w') as fh:
        json.dump(rep2, fh, indent=1, default=str)
    with open(os.path.join(d, 'stage', 'cover_plan.json'), 'w') as fh:        # the boxes (spot list for the live test)
        json.dump(rep['plan']['boxes'], fh, indent=0, default=str)
    LO.rmtree(mid)
    LO.rmtree(os.path.join(d, 'strip'))
    import kl_cover_floornav as FN                                  # the new group against the floor + nav check (reads the cover_plan.json just written)
    _r, rows = FN.scan(final, name=name, log=log)
    rep2['floornav_after'] = rows
    with open(os.path.join(d, 'stage', 'build_report.json'), 'w') as fh:
        json.dump(rep2, fh, indent=1, default=str)
    log('  %s: boxes %d -> %d (%.2f -> %.2f per 100 m2 of %d m2); members %s; md5 %s -> %s' % (name, n0, n1, rep2['per100_before'], rep2['per100_after'], area, rep2['members_changed'], h[:8], h2[:8]))
    if scratch:
        LO.MAPS[name] = dict(slot=os.path.basename(zn).split('_Main')[0], zip=zn)
        LO.TAG = tag
        LO.rehearse(os.path.join(d, 'stage'), name, src, h2, h, scratch, log)
    LO.rmtree(os.path.join(d, 'in'))                                # (disk: the stage keeps the zip; `stage` rebuilds `in`)
    return rep2


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__)
        return 2
    global FROM
    scratch = a[a.index('--rehearse') + 1] if '--rehearse' in a else None
    FROM = a[a.index('--from') + 1] if '--from' in a else None
    if '--no-safety' in a:
        OPT['safety'] = False
    if '--no-floornav' in a:
        OPT['floornav'] = False
    global REPLACE, TIERS_ALL, TAG_OVERRIDE
    TIERS_ALL = a[a.index('--tiers') + 1] if '--tiers' in a else None
    TAG_OVERRIDE = a[a.index('--tag') + 1] if '--tag' in a else None
    REPLACE = '--replace' in a
    names = [x for x in a[2:] if x in MAPS] or MAPS   # (--tiers / --tag values are not map names)
    res = {}
    for n in names:
        res[n] = stage_map(a[1], n, scratch)
    with open(os.path.join(a[1], 'summary.json'), 'w') as fh:
        json.dump(res, fh, indent=1, default=str)
    return 0


if __name__ == '__main__':
    sys.exit(main())
