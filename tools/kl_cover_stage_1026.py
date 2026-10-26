"""kl_cover_stage_1026.py - stage the player-cover pass (tools/kl_cover_1026.py) for the expansion maps (2026-10-26).
OFFLINE: reads the LIVE zips, writes only under <root>/<MAP>/{in,mid,stage}. Nothing is installed.

Per map: the live zip is copied to <root>/<MAP>/in/, kl_cover_1026.build() runs on it (kl_fa_cover.apply + check + diff), the 7 members
it changes (.buf .gms .oct .prm .prp .rmc .rmi) are patched INTO THE LIVE ZIP BYTES (member-level, every other member and the zip
layout untouched, kl_loot_1025.patch_zip) -> <root>/<MAP>/stage/{<zip>, install.py, build_report.json}. install.py pins the live md5
(refuses when it moved), refuses while kl2.exe runs, moves the original to '<zip>.before-1026cover'; --undo puts it back.
The pass is idempotent (a zip that already has the KL_CoverSix! group is left alone: 'nothing to add').
RE-STAGE after another step changed a zip:   python kl_cover_stage_1026.py stage C:/kl_build_1024/cover_1026 [DM01 DM02 ...] [--rehearse <scratch>] [--no-safety]
(it always starts from whatever is live at that moment, and the md5 pin of install.py is that zip).
"""
import collections, glob, json, os, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loot_1025 as LO
import kl_cover_1026 as K
import kl_cover_add as A

GAME = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
TAG = '.before-1026cover'
MAPS = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B', 'DD10']
OPT = {'max': K.MAX_NEW, 'density': K.DENSITY, 'spread': K.SPREAD, 'safety': K.SAFETY}   # safety = kl_cover_1026 filter rules (recommended on); stage ... --no-safety turns them off
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
    src = os.path.join(d, 'in', zn)
    shutil.copyfile(live, src)
    for f in os.listdir(os.path.dirname(live)):                    # the small files beside it (the checkers read the .ini)
        if f.lower().endswith('.ini'):
            shutil.copyfile(os.path.join(os.path.dirname(live), f), os.path.join(d, 'in', f))
    h = LO.md5(src)
    log('== %s (%s) md5 %s ==' % (name, zn, h))
    n0, nc0, area = counts(src)
    mid = os.path.join(d, 'mid')
    L, rep, out, bad = K.build(src, mid, dict(OPT, tiers=TIERS.get(name, K.TIERS)), log)
    if rep is None:
        log('  nothing to add (already has the group, or no model fits)')
        return None
    fails = [t for s, t in out if s == 'FAIL']
    if fails or bad:
        raise SystemExit('%s: check FAIL %s / diff %s' % (name, fails[:3], bad))
    new_zip = os.path.join(mid, zn)
    with zipfile.ZipFile(new_zip) as z, zipfile.ZipFile(src) as a:
        repl = {i.filename: z.read(i.filename) for i in a.infolist() if z.read(i.filename) != a.read(i.filename)}
    final = os.path.join(d, 'stage', zn)
    LO.patch_zip(src, final, repl)
    h2 = LO.md5(final)
    n1, nc1, _a = counts(final)
    rep2 = collections.OrderedDict(map=name, zip=zn, md5_in=h, md5_out=h2, members_changed=sorted(n.rsplit('_Main', 1)[-1] for n in repl),
                                   boxes_before=n0, boxes_after=n1, added=n1 - n0, nocover_before=nc0, nocover_after=nc1, mesh_m2=area,
                                   per100_before=round(n0 / area * 100, 2), per100_after=round(n1 / area * 100, 2),
                                   kinds_added=dict(collections.Counter(b['kind'] for b in rep['plan']['boxes'])),
                                   check_lines=len(out), options=dict(OPT, tiers=TIERS.get(name, K.TIERS)),
                                   tier_a_added=sum(1 for b in rep['plan']['boxes'] if b['tier'] == 'a'))
    if nc1 != nc0:
        raise SystemExit('%s: NoCoverBox count changed %d -> %d' % (name, nc0, nc1))
    with open(os.path.join(d, 'stage', 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=h, new=h2))
    with open(os.path.join(d, 'stage', 'build_report.json'), 'w') as fh:
        json.dump(rep2, fh, indent=1, default=str)
    with open(os.path.join(d, 'stage', 'cover_plan.json'), 'w') as fh:        # the boxes (spot list for the live test)
        json.dump(rep['plan']['boxes'], fh, indent=0, default=str)
    LO.rmtree(mid)
    log('  %s: boxes %d -> %d (%.2f -> %.2f per 100 m2 of %d m2); members %s; md5 %s -> %s' % (name, n0, n1, rep2['per100_before'], rep2['per100_after'], area, rep2['members_changed'], h[:8], h2[:8]))
    if scratch:
        LO.MAPS[name] = dict(slot=os.path.basename(zn).split('_Main')[0], zip=zn)
        LO.TAG = TAG
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
    names = [x for x in a[2:] if x in MAPS] or MAPS
    res = {}
    for n in names:
        res[n] = stage_map(a[1], n, scratch)
    with open(os.path.join(a[1], 'summary.json'), 'w') as fh:
        json.dump(res, fh, indent=1, default=str)
    return 0


if __name__ == '__main__':
    sys.exit(main())
