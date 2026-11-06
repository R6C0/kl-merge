#!/usr/bin/env python3
"""
pd2_guns_layer.py - stage the NEW pd2_guns_multi specs (batch 3 C45 / item 62, batch 4 HRL50 / HRL51 = items 50 / 51) as a layer ON TOP of the
live Dead Men maps (2026-11-06, offline; writes only the stage folder, never the game).

    python tools/pd2_guns_layer.py build  [--layer 1106b|1106c] [--out <dir>] [--maps DM01,DM02]   default out <work>/build/pd2guns_1106b (1106c: D:\\kl_stage\\pd2guns_1106c, on the 1106b stage)
    python tools/pd2_guns_layer.py verify [--out <dir>] [--maps ...]         per-map table (needs the live zips to be the ones staged on)
    python tools/pd2_guns_layer.py pin    [--out <dir>]                      redo the ini Entries fix + pins.json of a baked stage (no re-bake)
    python tools/pd2_guns_layer.py install-py [--out <dir>]                  rewrite install.py / INSTALL.bat / UNDO.bat from pins.json
    python tools/pd2_guns_layer.py all    [--out <dir>]                      build + verify + pics

Why not tools/pd2_guns_stage.py: that bakes EVERY spec on the live zip and rebuilds the bots sibling from the plain result. The live zips already hold
batch 1 + 2 (pd2guns_1106) and layers above it (shop buttons, shop pics, c9 glass), so this layer
  * bakes ONLY KEYS (pd2_guns_multi.stage_map(only=...)), fits frozen from fits.json (seeded from pd2guns_1106 + the pd2b4 scratch), so the shifts are
    identical on every map and on the plain and bots zip;
  * bakes the bots sibling by the SAME bake on the LIVE bots zip (as kl_shop_pics does), NOT convert(plain): the live bots zip carries layers
    (and a squad conversion) the plain result would lose;
  * moves nothing else: members outside .prm .MAT .TEX .oct .gms .prp stay byte-equal; the .ini files get Entries= the new chunk count;
    <slot>_Main.bots.base.md5 is restaged (md5 of the new plain + LF) only when the live one matched the live plain zip (kl_bake_siblings rule);
    DM11B's Int16Ok.txt zip= / bots= take the new sizes (kl_bake_siblings._fix_i16).
Undo order: this layer FIRST (install.py --undo refuses a map whose live files are no longer the ones it wrote, i.e. when buttons / pics /
glass went on top; undo those first).
"""
import hashlib, json, os, shutil, struct, sys, time, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pd2_guns_multi as M

# A layer = which SPECS keys it bakes, the backup tag, the folder it is staged on (BASE: None = the live map folders, else a folder of per-map
# folders = an earlier layer's STAGE, so a later layer goes on top of an earlier one that is not installed yet), and the default out folder.
# Select with `--layer NAME` (default 1106b, behaving exactly as before); configure() sets the module globals the functions below read.
WORK_BUILD = os.path.join(M.work(), 'build')
LAYERS = {
    '1106b': dict(keys=['C45', 'HRL50', 'HRL51'], tag='.before-pd2guns1106b', base=None, out=os.path.join(WORK_BUILD, 'pd2guns_1106b'),
                  title='1106b (items 62 C45 pistol, 50 / 51 HRL-7 launchers: the specs C45, HRL50, HRL51)', short='C45 / HRL-7',
                  seeds=[]),
    '1106c': dict(keys=['R700', 'GL40', 'GL40GAS', 'GL40FLR'], tag='.before-pd2guns1106c', base=os.path.join(WORK_BUILD, 'pd2guns_1106b'),
                  out=r'D:\kl_stage\pd2guns_1106c', backup=r'D:\kl_stage\pd2guns_1106c_backup',      # backup = off-drive installer (C: is full)
                  title='1106c (items 49 R700 sniper, 52 / 53 / 54 GL40 grenade launchers: the specs R700, GL40, GL40GAS, GL40FLR), staged on top of layer 1106b',
                  short='R700 / GL40', seeds=[os.path.join(WORK_BUILD, 'pd2b5_scratch', 'r700_out', 'fits.json'),
                                              os.path.join(WORK_BUILD, 'pd2b6_scratch', 'fits.json')]),
}
KEYS = LAYERS['1106b']['keys']
TAG = LAYERS['1106b']['tag']
BASE = LAYERS['1106b']['base']
LAYER = '1106b'
ALLOWED = {'.prm', '.MAT', '.TEX', '.oct', '.gms', '.prp'}
FITS_SEEDS = [r'C:\Users\Henri\AppData\Local\Temp\claude\c--kl-merge-kl-merge\e2de9ad7-9c8b-45d5-9019-f852ea50154f\scratchpad\pd2b4\fits.json']
DETAIL = {'C45': 31, 'HRL50': 255, 'HRL51': 255,      # body detail byte (see build_level GUESS notes)
          'R700': 31, 'GL40': 191, 'GL40GAS': 191, 'GL40FLR': 191}      # R700 7|28 = 31, GL40 1|190 = 191 (pd2_guns_multi batch 5/6 commits)


def configure(name):
    global KEYS, TAG, BASE, LAYER
    L = LAYERS[name]
    KEYS, TAG, BASE, LAYER = list(L['keys']), L['tag'], L['base'], name


def src_root():
    """Folder holding the per-map folders this layer is baked on: the base stage, else the live maps."""
    return BASE or M.MAPROOT


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def default_out():
    return LAYERS[LAYER]['out']


def seed_fits(out):
    """fits.json = pd2guns_1106's + the scratch fits of the new keys (frozen shifts)."""
    fp = os.path.join(out, 'fits.json')
    if os.path.isfile(fp):
        return fp
    d = {}
    for src in [os.path.join(M.work(), 'build', 'pd2guns_1106', 'fits.json')] + FITS_SEEDS + LAYERS[LAYER]['seeds']:
        if os.path.isfile(src):
            d.update(json.load(open(src)))
    miss = [k for k in KEYS if k not in d]
    if miss:
        raise SystemExit('no fit for %s in the seeds' % miss)
    json.dump(d, open(fp, 'w'), indent=1)
    return fp


def stage(out, maps, log=print):
    import kl_chars as C
    import kl_bake_siblings as BS
    os.makedirs(out, exist_ok=True)
    seed_fits(out)
    pins = {}
    t0 = time.time()
    for m in maps:
        live = os.path.join(src_root(), m)
        rep = M.stage_map(m, out, only=KEYS, log=log, src=live)
        slot, d = rep['slot'], os.path.join(out, m)
        lp = BS.paths(os.path.join(live, slot + '_Main.zip'))
        # bots sibling: the same bake on the live (or base-stage) bots zip (scratch folder = bots zip as the folder's only *_Main.zip + the live inis)
        bots_new = None
        if os.path.isfile(lp['bots']):
            scr = os.path.join(out, '_botsrc')
            shutil.rmtree(scr, ignore_errors=True); os.makedirs(scr)
            shutil.copyfile(lp['bots'], os.path.join(scr, slot + '_Main.zip'))
            for f in os.listdir(live):
                if f.lower().endswith('.ini'):
                    shutil.copyfile(os.path.join(live, f), os.path.join(scr, f))
            brep = M.stage_map(m, out, src=scr, dirname='_botsout', only=KEYS, log=log)
            shutil.rmtree(scr, ignore_errors=True)
            if brep['chunks_after'] != rep['chunks_after'] or brep['chunks_before'] != rep['chunks_before']:
                raise SystemExit('%s: bots prm chunks %d -> %d differ from plain %d -> %d' % (
                    m, brep['chunks_before'], brep['chunks_after'], rep['chunks_before'], rep['chunks_after']))
            for k in KEYS:
                if rep['guns'].get(k, {}).get('root') != brep['guns'].get(k, {}).get('root'):
                    raise SystemExit('%s: %s root differs plain/bots' % (m, k))
            bots_new = os.path.join(out, '_botsout', slot + '_Main.zip')
            os.replace(bots_new, os.path.join(d, slot + '_Main.bots.zip'))
            shutil.rmtree(os.path.join(out, '_botsout'), ignore_errors=True)
        newp, newb = os.path.join(d, slot + '_Main.zip'), os.path.join(d, slot + '_Main.bots.zip')
        if os.path.isfile(lp['md5']):
            cur = open(lp['md5']).read().strip()
            if cur == md5(lp['plain']):
                with open(os.path.join(d, slot + '_Main.bots.base.md5'), 'w', newline='') as f:
                    f.write(md5(newp) + '\n')
            else:
                log('  WARNING %s: live bots.base.md5 (%s) is not the live plain md5 (%s): not restaged (already drifted)' % (m, cur[:8], md5(lp['plain'])[:8]))
        if os.path.isfile(lp['i16']):
            raw = open(lp['i16'], 'rb').read()
            fixed = BS._fix_i16(raw, os.path.getsize(lp['plain']), os.path.getsize(newp),
                                os.path.getsize(lp['bots']) if os.path.isfile(lp['bots']) else None,
                                os.path.getsize(newb) if os.path.isfile(newb) else None, log)
            if fixed != raw:
                open(os.path.join(d, 'Int16Ok.txt'), 'wb').write(fixed)
        log('%s baked (%.0f s)' % (m, time.time() - t0))
    return pin(out, maps, log)


def fix_inis(out, m, rep, log=print):
    """KLGuns.ini / KLJoin.ini: Entries= must be the chunk count of the NEW .prm (klgun.c G1 refuses a file whose count differs, so the guns of the
    level would be left at what was built in). On 11-06 the live files carried the count of BEFORE the shop pics bake (+72 chunks on every map;
    re-synced by tools/kl_entries_fix.py, after which `pin` must be re-run so the pins hold the fixed inis); stage_map only rewrites a value that equals the live chunk count, so it wrote nothing. A file with exactly ONE Entries
    line gets the new count whatever it held (the stale case is logged); with several lines only those equal to the live chunk count change."""
    import re
    live, d = os.path.join(src_root(), m), os.path.join(out, m)
    for f in sorted(os.listdir(live)):
        if not f.lower().endswith('.ini'):
            continue
        txt = open(os.path.join(live, f), encoding='latin-1', newline='').read()
        vals = re.findall(r'(?m)^Entries\s*=\s*(\d+)\s*$', txt)
        if not vals:
            continue
        pat = r'(?m)^(Entries\s*=\s*)(\d+)(\s*)$'
        if len(vals) == 1:
            new = re.sub(pat, lambda x: x.group(1) + str(rep['chunks_after']) + x.group(3), txt)
            if int(vals[0]) != rep['chunks_before']:
                log('  %s %s: Entries=%s was STALE (live .prm has %d chunks); now %d' % (m, f, vals[0], rep['chunks_before'], rep['chunks_after']))
        else:
            new = re.sub(pat, lambda x: x.group(1) + (str(rep['chunks_after']) if int(x.group(2)) == rep['chunks_before'] else x.group(2)) + x.group(3), txt)
            log('  WARNING %s %s: %d Entries lines %s, only those equal to %d changed' % (m, f, len(vals), vals, rep['chunks_before']))
        if new != txt:
            open(os.path.join(d, f), 'w', encoding='latin-1', newline='').write(new)


def pin(out, maps, log=print):
    """ini fixes + pins.json {map: {file: {old, new, size}}} for every staged file against the live one ('old')."""
    pins = {}
    for m in maps:
        d = os.path.join(out, m)
        fix_inis(out, m, json.load(open(os.path.join(d, 'report.json'))), log)
        pins[m] = {}
        for f in sorted(os.listdir(d)):
            if f == 'report.json':
                continue
            lf = os.path.join(src_root(), m, f)
            if not os.path.isfile(lf):
                raise SystemExit('%s: no %s %s to pin' % (m, 'base-stage' if BASE else 'live', f))
            pins[m][f] = dict(old=md5(lf), new=md5(os.path.join(d, f)), size=os.path.getsize(os.path.join(d, f)))
            if BASE:           # old = what the base layer installs = its pinned 'new' (the base stage file itself must still be that)
                bp = json.load(open(os.path.join(BASE, 'pins.json')))['maps'][m].get(f)
                if bp and bp['new'] != pins[m][f]['old']:
                    raise SystemExit('%s: base stage %s md5 %s != base pins.json new %s' % (m, f, pins[m][f]['old'], bp['new']))
    pp = os.path.join(out, 'pins.json')
    allp = json.load(open(pp))['maps'] if os.path.isfile(pp) else {}
    allp.update(pins)
    json.dump(dict(maps=allp, tag=TAG, keys=KEYS, base=BASE), open(pp, 'w'), indent=1)
    return pins


# ------------------------------------------------------------------ verify
def check_zip(live_zip, new_zip, rep):
    """-> (row dict, ok). One plain or bots zip against the live zip it was staged from."""
    import tempfile
    import kl_chars as C, kl_guns, kl_prmgraph as G
    a, b = zipfile.ZipFile(live_zip), zipfile.ZipFile(new_zip)
    same_list = a.namelist() == b.namelist()
    changed = sorted(n.rsplit('_Main', 1)[-1] if '_Main' in n else n for n in a.namelist() if a.read(n) != b.read(n))
    ok = same_list and set(changed) <= ALLOWED
    row = dict(members=','.join(changed), list_same=same_list)

    def lv_of(zp):
        d = tempfile.mkdtemp(prefix='lvchk_', dir=os.path.dirname(new_zip))
        try:
            shutil.copyfile(zp, os.path.join(d, rep['slot'] + '_Main.zip'))
            lv = C.Lv(d); lv.beside, lv.side = {}, {}
        finally:
            shutil.rmtree(d, ignore_errors=True)
        return lv
    lv0, lv1 = lv_of(live_zip), lv_of(new_zip)
    sc0, _ = lv0.scene(); sc1, _ = lv1.scene()
    p0, p1 = G.read(lv0['.prm'], 'dd'), G.read(lv1['.prm'], 'dd')
    tpl = {rep['guns'][k]['template']: k for k in KEYS if k in rep['guns']}
    row['specs'] = ','.join(sorted(tpl.values()))
    changed_nodes, same_nodes = [], 0
    for k in range(1, len(sc1.nodes)):
        pa = sc1.path[k]
        if pa.endswith('\\Ground') and '\\Weapon\\' in pa:
            t = pa.split('\\')[-2]
            try:
                r1, r0 = C.person(sc1, k)[0], C.person(sc0, k)[0]
            except Exception:
                continue
            if r1 != r0:
                changed_nodes.append(t)
            else:
                same_nodes += 1
    ok &= sorted(changed_nodes) == sorted(tpl)
    row['retargeted'] = len(changed_nodes); row['others_same'] = same_nodes
    det = {}
    for t, key in tpl.items():
        det[key] = p1.chunks[rep['guns'][key]['body_object']][0x0e]
        ok &= det[key] == DETAIL[key]
    row['detail'] = ' '.join('%s=%d' % kv for kv in sorted(det.items()))
    # every pre-existing chunk byte-equal (the new roots / objects are appended), so the batch 1-2 roots, objects and vertices are untouched
    n0 = len(p0.chunks)
    diff = [i for i in range(n0) if p0.chunks[i] != p1.chunks[i]]
    row['old_chunks_diff'] = len(diff)
    ok &= not diff and len(p1.chunks) == rep['chunks_after'] and n0 == rep['chunks_before']
    old_roots = 0                      # batch 1-2 roots explicitly (also by node: same root id, same bytes, same objects)
    for s in M.SPECS:
        if s['key'] in KEYS:
            continue
        try:
            k = kl_guns.gun_node(sc1, s['template'])
        except Exception:
            continue
        r1, r0 = C.person(sc1, k)[0], C.person(sc0, k)[0]
        ok &= r1 == r0 and p1.chunks[r1] == p0.chunks[r0] and all(p1.chunks[o] == p0.chunks[o] for o in C.objects(p0, r0))
        old_roots += 1
    row['b12_roots_checked'] = old_roots
    return row, bool(ok)


def verify(out, maps, log=print):
    import kl_bake_siblings as BS
    allok = True
    for m in maps:
        d = os.path.join(out, m)
        rep = json.load(open(os.path.join(d, 'report.json')))
        slot = rep['slot']
        lp = BS.paths(os.path.join(src_root(), m, slot + '_Main.zip'))
        for kind, lz, nz in (('plain', lp['plain'], os.path.join(d, slot + '_Main.zip')), ('bots', lp['bots'], os.path.join(d, slot + '_Main.bots.zip'))):
            if not os.path.isfile(lz):
                log('%-6s %-5s no such live file' % (m, kind)); continue
            row, ok = check_zip(lz, nz, rep)
            allok &= ok
            log('%-6s %-5s %-4s members[%s] list_same=%s specs[%s] retargeted=%d others_unchanged=%d detail[%s] old_chunks_diff=%d b12_roots=%d' % (
                m, kind, 'ok' if ok else 'FAIL', row['members'], row['list_same'], row['specs'], row['retargeted'], row['others_same'],
                row['detail'], row['old_chunks_diff'], row['b12_roots_checked']))
            missing = sorted(set(KEYS) - set(row['specs'].split(',')))
            if missing:
                log('       NOTE: %s has no template for %s (skipped on this map)' % (m, missing))
    allok &= M.verify(out, log=lambda s: log('  [pd2_guns_multi.verify] ' + s), live_root=BASE)      # base verifier on the plain zips (also scans every <dir>/report.json)
    log('LAYER RESULT: %s' % ('PASS' if allok else 'FAIL'))
    return allok


# ------------------------------------------------------------------ installer
INSTALL_PY = r'''"""PD2 guns @TITLE@ as a layer ON TOP of the live Dead Men maps.
Per map: <slot>_Main.zip, <slot>_Main.bots.zip, <slot>_Main.bots.base.md5, KLGuns.ini, KLJoin.ini (and DM11B's Int16Ok.txt) are RENAMED to <name>@TAG@
(never written through, never deleted) and the staged file copied in. Every live file's md5 is pinned (pins.json, taken when this was staged): a map whose
live file changed since (any other layer installed or undone) is refused, the others still install. --undo only restores a map whose live files are exactly
the ones this installer wrote and whose backups are the pinned originals (undo the layers above first: glass, shop pics, shop buttons).
usage: python install.py [--dry] [--maps DM01,DM02] [--skip-run-check] | --undo [--maps ...] [--dry]     (run with the game closed)"""
import hashlib, json, os, subprocess, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = os.path.join(GAME, 'KLExpansion', 'Maps')
TAG = '@TAG@'
pins = json.load(open(os.path.join(HERE, 'pins.json')))['maps']


def _md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


_MD5 = {}


def md5(p):
    k = (p, os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else p
    if k not in _MD5:
        _MD5[k] = _md5(p)
    return _MD5[k]


def arg(name):
    return sys.argv[sys.argv.index(name) + 1].split(',') if name in sys.argv else None


if '--skip-run-check' not in sys.argv and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    sys.exit('kl2.exe is running')
if arg('--game'):                       # test-only: rehearse on a scratch copy of a Dog Days folder
    GAME = arg('--game')[0]; MAPS = os.path.join(GAME, 'KLExpansion', 'Maps')
want = arg('--maps') or list(pins)
undo, dry = '--undo' in sys.argv, '--dry' in sys.argv
jobs = []          # (map, live path, staged path, old md5, new md5)
for m in want:
    for f, p in pins[m].items():
        jobs.append((m, os.path.join(MAPS, m, f), os.path.join(HERE, m, f), p['old'], p['new']))
bad = set()
for m, live, new, o, n in jobs:
    if not os.path.exists(live):
        print('SKIP %s: live %s missing' % (m, os.path.basename(live))); bad.add(m)
    elif undo:
        if not os.path.exists(live + TAG) or md5(live + TAG) != o:
            print('SKIP %s: backup %s missing or changed' % (m, os.path.basename(live + TAG))); bad.add(m)
        elif md5(live) != n:
            print('SKIP %s: live %s is not the staged file (%s)' % (m, os.path.basename(live), md5(live)[:8])); bad.add(m)
    else:
        if os.path.exists(live + TAG):
            print('SKIP %s: backup exists %s' % (m, live + TAG)); bad.add(m)
        elif md5(live) != o:
            print('SKIP %s: live %s changed since staging (md5 %s, pinned %s)' % (m, os.path.basename(live), md5(live)[:8], o[:8])); bad.add(m)
        elif not os.path.exists(new) or md5(new) != n:
            print('SKIP %s: staged %s missing or md5 != pinned' % (m, os.path.basename(new))); bad.add(m)
todo = [j for j in jobs if j[0] not in bad]
print('%s %d files of %s (skipped: %s)' % ('dry:' if dry else ('undo' if undo else 'install'), len(todo), sorted({j[0] for j in todo}, key=want.index), sorted(bad) or 'none'))
if not undo:
    need = sum(os.path.getsize(j[2]) for j in todo)      # renames cost nothing, each staged file is copied in full
    free = shutil.disk_usage(MAPS).free
    print('disk: copies need %d MB, %d MB free on %s' % (need >> 20, free >> 20, os.path.splitdrive(MAPS)[0]))
    if not dry and free < need + (512 << 20):
        sys.exit('not enough space (want %d MB + 512 MB spare); free space or install with --maps for fewer maps' % (need >> 20))
if dry:
    sys.exit()


def retry(fn, *a):
    """A just-read zip can stay locked a few seconds by another process (WinError 32 on 11-06, likely a scanner, GUESS): retry up to ~60 s."""
    import time
    for i in range(30):
        try:
            return fn(*a)
        except PermissionError:
            if i == 29:
                raise
            time.sleep(2)


def roll_back(done):
    """Put a map's already-swapped files back (reverse order) so a failed map is left exactly as before."""
    for live in reversed(done):
        if os.path.exists(live):
            retry(os.remove, live)
        retry(os.rename, live + TAG, live)
        print('  rolled back', os.path.basename(live))


failed = []
for mm in sorted({j[0] for j in todo}, key=want.index):
    done = []
    try:
        for m, live, new, o, n in [j for j in todo if j[0] == mm]:
            if undo:
                retry(os.remove, live); retry(os.rename, live + TAG, live)
                print('restored', m, os.path.basename(live), _md5(live)[:8])
            else:
                retry(os.rename, live, live + TAG)
                done.append(live)
                shutil.copyfile(new, live)
                assert _md5(live) == n
                print('installed', m, os.path.basename(live), n[:8], '| backup', o[:8])
    except Exception as e:
        print('FAILED %s: %s' % (mm, e)); failed.append(mm)
        if not undo:
            roll_back(done)
if failed:
    sys.exit('failed (left as before): %s' % ' '.join(failed))
'''


INSTALL_PY_OFFDRIVE = r'''"""PD2 guns @TITLE@ as a layer ON TOP of the live Dead Men maps - OFF-DRIVE BACKUP mode.
The game drive is nearly full, so nothing is kept beside the live files. Per map and file (<slot>_Main.zip, <slot>_Main.bots.zip, <slot>_Main.bots.base.md5,
KLGuns.ini, KLJoin.ini, DM11B's Int16Ok.txt): the live file is COPIED to <backup>/<map>/<file> (md5 must be the pinned old one), then the staged file is
copied to <live>.new beside it (md5 must be the pinned new one) and os.replace'd over the live file. Any failure rolls the whole map back from the backup
copies (md5-checked) and removes them, so the map is left as it was. A map that already has a backup file on the backup drive is refused ('backup exists').
Backups live in the BACKUP folder set below (override: --backup DIR). Every live md5 is pinned (pins.json): a map whose live file drifted is refused, the others still install.
Disk: the game drive needs only the largest staged file + 512 MB spare per map (the new file replaces the old one), the backup drive the old files of the maps installed.
--undo restores a file only when live md5 == pinned new and the backup md5 == pinned old; a map's backup files are DELETED only after every file of that map
is restored and its md5 verified (they are then redundant and would make a re-install refuse with 'backup exists'; deleting after the check frees the D: space).
usage: python install.py [--dry] [--maps DM01,DM02] [--skip-run-check] [--backup DIR] [--game DIR] | --undo [same options]   (run with the game closed)"""
import hashlib, json, os, subprocess, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
BACKUP = r'@BACKUP@'
TAG = '@TAG@'                              # the in-place rename tag of the older installer; unused here, kept so layer tags stay greppable
SPARE = 512 << 20                          # transient headroom kept free on the game drive
pins = json.load(open(os.path.join(HERE, 'pins.json')))['maps']


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def arg(name):
    return sys.argv[sys.argv.index(name) + 1].split(',') if name in sys.argv else None


if '--skip-run-check' not in sys.argv and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    sys.exit('kl2.exe is running')
if arg('--game'):                          # rehearsal on a scratch copy of a Dog Days folder
    GAME = arg('--game')[0]
if arg('--backup'):
    BACKUP = arg('--backup')[0]
if arg('--spare-mb'):                      # test only
    SPARE = int(arg('--spare-mb')[0]) << 20
FAIL_AFTER = int(arg('--fail-after')[0]) if arg('--fail-after') else None      # test only: raise after N files of a map were swapped in
MAPS = os.path.join(GAME, 'KLExpansion', 'Maps')
want = arg('--maps') or list(pins)
undo, dry = '--undo' in sys.argv, '--dry' in sys.argv
mb = lambda n: '%d MB' % (n >> 20)


def retry(fn, *a):
    """A just-read zip can stay locked a few seconds by another process (WinError 32 on 11-06, likely a scanner, GUESS): retry up to ~60 s."""
    for i in range(30):
        try:
            return fn(*a)
        except PermissionError:
            if i == 29:
                raise
            time.sleep(2)


def bk(m, f):
    return os.path.join(BACKUP, m, f)


def swap_in(src, live, want_md5):
    """src -> <live>.new (same drive) -> os.replace over live; md5 checked on the .new and on the result."""
    tmp = live + '.new'
    try:
        retry(shutil.copyfile, src, tmp)
        if md5(tmp) != want_md5:
            raise IOError('md5 of %s after copy is not %s' % (os.path.basename(tmp), want_md5[:8]))
        retry(os.replace, tmp, live)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    if md5(live) != want_md5:
        raise IOError('md5 of %s after replace is not %s' % (os.path.basename(live), want_md5[:8]))


jobs = {}          # map -> [(file, live path, staged path, old md5, new md5)]
for m in want:
    jobs[m] = [(f, os.path.join(MAPS, m, f), os.path.join(HERE, m, f), p['old'], p['new']) for f, p in pins[m].items()]
bad = {}
for m, js in jobs.items():
    for f, live, new, o, n in js:
        why = None
        if not os.path.exists(live):
            why = 'live %s missing' % f
        elif undo:
            if not os.path.exists(bk(m, f)) or md5(bk(m, f)) != o:
                why = 'backup %s missing or changed' % bk(m, f)
            elif md5(live) not in (n, o):
                why = 'live %s is neither the staged nor the original file (%s)' % (f, md5(live)[:8])
        else:
            if os.path.exists(bk(m, f)):
                why = 'backup exists %s' % bk(m, f)
            elif md5(live) != o:
                why = 'live %s changed since staging (md5 %s, pinned %s)' % (f, md5(live)[:8], o[:8])
            elif not os.path.exists(new) or md5(new) != n:
                why = 'staged %s missing or md5 != pinned' % f
        if why:
            print('SKIP %s: %s' % (m, why)); bad[m] = why
            break
todo = [m for m in want if m not in bad]
print('%s maps %s (skipped: %s)' % ('dry:' if dry else ('undo' if undo else 'install'), todo, sorted(bad) or 'none'))
for m in todo:
    big = max(os.path.getsize(j[1]) if undo else os.path.getsize(j[2]) for j in jobs[m])
    delta = sum(os.path.getsize(j[2]) - os.path.getsize(j[1]) for j in jobs[m]) * (-1 if undo else 1)
    print('  %-6s game drive: %s transient (largest file + spare), net %+d MB%s' % (m, mb(big + SPARE), delta >> 20,
          '' if undo else ', backup drive: %s' % mb(sum(os.path.getsize(j[1]) for j in jobs[m]))))
if not undo and todo:
    need = sum(os.path.getsize(j[1]) for m in todo for j in jobs[m])
    probe = BACKUP
    while not os.path.isdir(probe) and os.path.dirname(probe) != probe:
        probe = os.path.dirname(probe)
    free = shutil.disk_usage(probe).free
    print('backup drive: %s needed, %s free on %s' % (mb(need), mb(free), os.path.splitdrive(os.path.abspath(BACKUP))[0]))
    if not dry and free < need + SPARE:
        sys.exit('not enough space on the backup drive (want %s + %s spare); install with --maps for fewer maps' % (mb(need), mb(SPARE)))
if dry:
    sys.exit()


def drop_backups(m):
    for f, live, new, o, n in jobs[m]:
        if os.path.exists(bk(m, f)):
            retry(os.remove, bk(m, f))
    d = os.path.join(BACKUP, m)
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)


def roll_back(m):
    """Put every file of the map whose live md5 != pinned old back from its backup copy (md5-verified; covers a failure after the replace too),
    then drop the map's backups. True when the map is exactly as before."""
    ok = True
    for f, live, new, o, n in reversed(jobs[m]):
        if not os.path.exists(bk(m, f)) or md5(live) == o:
            continue
        try:
            swap_in(bk(m, f), live, o)
            print('  rolled back', f, o[:8])
        except Exception as e:
            print('  ROLLBACK FAILED %s: %s (backup kept in %s)' % (f, e, bk(m, f))); ok = False
    if ok:
        drop_backups(m)
    return ok


failed = []
for m in todo:
    swapped = 0
    try:
        big = max(os.path.getsize(j[1]) if undo else os.path.getsize(j[2]) for j in jobs[m])
        free = shutil.disk_usage(MAPS).free
        if free < big + SPARE:
            raise IOError('game drive has %s free, want %s (largest file + spare)' % (mb(free), mb(big + SPARE)))
        if undo:
            for f, live, new, o, n in jobs[m]:
                if md5(live) == n:
                    swap_in(bk(m, f), live, o)
                print('restored', m, f, md5(live)[:8])
            for f, live, new, o, n in jobs[m]:
                assert md5(live) == o, f
            drop_backups(m)               # every file of the map is restored and md5-verified
            print('  backups of %s deleted (verified restored)' % m)
        else:
            os.makedirs(os.path.join(BACKUP, m), exist_ok=True)
            for f, live, new, o, n in jobs[m]:          # 1: copy every live file off the drive, md5 = pinned old
                retry(shutil.copyfile, live, bk(m, f))
                if md5(bk(m, f)) != o:
                    raise IOError('backup copy of %s md5 != pinned old' % f)
            for f, live, new, o, n in jobs[m]:          # 2: staged -> <live>.new -> replace
                swap_in(new, live, n)
                swapped += 1
                print('installed', m, f, n[:8], '| backup', o[:8], 'in', bk(m, f))
                if FAIL_AFTER is not None and swapped >= FAIL_AFTER:
                    raise IOError('forced failure (test)')
    except Exception as e:
        print('FAILED %s: %s' % (m, e)); failed.append(m)
        if not undo and not roll_back(m):
            failed.append(m + '(ROLLBACK INCOMPLETE, backups kept)')
if failed:
    sys.exit('failed: %s' % ' '.join(failed))
'''


def write_installer(out):
    L = LAYERS[LAYER]
    if L.get('backup'):            # off-drive backup mode: the live drive keeps no backup files
        py = INSTALL_PY_OFFDRIVE.replace('@TITLE@', L['title']).replace('@TAG@', TAG).replace('@BACKUP@', L['backup'])
        open(os.path.join(out, 'README.txt'), 'w', encoding='utf-8', newline='').write(
            'PD2 guns %s: install.py keeps its backups OFF the game drive, in %s/<map>/<file> (copied and md5-checked before the live file is replaced;\r\n'
            'deleted by --undo only after the restored files are md5-verified). Nothing is renamed beside the live files.\r\n' % (LAYER, L['backup']))
    else:
        py = INSTALL_PY.replace('@TITLE@', L['title']).replace('@TAG@', TAG)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='').write(py.replace('\n', '\r\n'))
    open(os.path.join(out, 'INSTALL.bat'), 'w', encoding='utf-8', newline='').write(
        '@echo off\r\nrem PD2 guns ' + LAYER + ' (' + LAYERS[LAYER]['short'] + '): install ON TOP of the live maps (game closed). Add --dry to only check, --maps DM01,DM02 for some maps.\r\n'
        'python "%~dp0install.py" %*\r\npause\r\n')
    open(os.path.join(out, 'UNDO.bat'), 'w', encoding='utf-8', newline='').write(
        '@echo off\r\nrem PD2 guns ' + LAYER + ': undo. Layers installed ABOVE this one (glass, shop pics, shop buttons) must be undone BEFORE this.\r\n'
        'python "%~dp0install.py" --undo %*\r\npause\r\n')


def main(a):
    if '--layer' in a:
        configure(a[a.index('--layer') + 1]); del a[a.index('--layer'):a.index('--layer') + 2]
    out = default_out()
    if '--out' in a:
        out = a[a.index('--out') + 1]; del a[a.index('--out'):a.index('--out') + 2]
    maps = list(M.MAPS)
    if LAYER == '1106c':       # DM02 first: the fits of a new key are taken on the first baked map (the notes fit on DM02)
        maps.sort(key=lambda m: m != 'DM02')
    if '--maps' in a:
        maps = a[a.index('--maps') + 1].split(','); del a[a.index('--maps'):a.index('--maps') + 2]
    cmd = (a[:1] or [''])[0]
    if cmd in ('build', 'all'):
        os.makedirs(out, exist_ok=True)
        need = len(maps) * 460 << 20
        if shutil.disk_usage(out).free < need + (2 << 30):
            sys.exit('disk: want %d MB + 2 GB spare on the stage drive' % (need >> 20))
        stage(out, maps)
    if cmd == 'pin':             # ini Entries + pins of an already baked stage
        pin(out, maps)
    if cmd in ('verify', 'all'):
        if not verify(out, maps):
            sys.exit(1)
    if cmd in ('install-py', 'build', 'all', 'pin'):
        write_installer(out)
    if cmd in ('pics', 'all'):
        M.write_pics(out, only=KEYS)
    if cmd not in ('build', 'verify', 'install-py', 'all', 'pin', 'pics'):
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
