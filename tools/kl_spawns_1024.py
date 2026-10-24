"""kl_spawns_1024.py - DATA pass of the 'enemies must not plop in' request (owner 2026-10-24: 'dont make it so they just plop in, they
need to spawn in from vehicles or from a door or somewhere logical or already spawned in'). Written 2026-10-24 (offline only).

WHAT IT DOES: reads the LIVE Dead Men map zips, runs kl_map_ai's spawn audit (re/retomoto_spawns.md: ZSquadScript field 3 = 0 hides the
men until the squad is handed a goal; PLOP = they are then SHOWN in sight, within 40 m of a place inside the waking box) and, for every
squad the audit calls PLOP, sets field 3 = 1: the men stand in the world from the load ('already spawned in', the third of the owner's
three allowed answers). That is exactly kl_map_ai.spawnfix with {'auto': True, 'posts': False}; this file only wraps it so that it
  - takes a LIVE zip (any chain of earlier passes) and gives a zip,
  - is idempotent (a zip with no PLOP squad left is reported 'nothing to change', nothing is written),
  - refuses an input whose md5 is not the one this was built and checked on (unless --force),
  - stages an md5-chained INSTALL/UNDO like kl_blowup.py (only the .prp member is replaced; no entity added/removed; .gms/.buf unchanged).
NOT DONE ON PURPOSE: DM05A (club) and DM11B (Hasta) are other jobs; DM11B has 2 PLOP squads (documented in re/spawns_1024.md).
Door / vehicle ARRIVALS are not grafted: Dog Days' arrivals are animated cutscene vans (.ANM baked in DD coordinates, never copied) and
KickDoor routs; Dead Men's own car squads already drive in. A squad that must come from somewhere gets a different answer only when a
hidden cell exists (kl_map_ai spawnfix 'posts' for Retomoto's street) - not generalisable offline.
Usage (from tools/):  python kl_spawns_1024.py [--game <DD>] [--out <folder>] [--maps DM01B,DM09] [--force] [--rehearse <scratch>]
"""
import os, sys, json, hashlib, shutil, subprocess, zipfile, tempfile, gc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_blowup as BL
import kl_map_ai as MA

DD = BL.DD
TAG = '.before-1024spawns'
# map -> (zip name, md5 of the live zip this pass was built and checked on 2026-10-24)
MAPS = {'DM01B': ('F03_Main.zip', 'badc0bee911aed73f1ff3f7c9a16277f'),
        'DM09': ('F06_Main.zip', 'fa9ecf84e98e4ff28633d23cd5670a6d')}
md5 = BL.md5
# the blowup installer, re-labelled (same code path: one member replaced in a COPY, checked, swapped; backup = <zip><TAG>)
PS1 = (BL.PS1.replace('blowup.json', 'spawns.json').replace('blowup.ps1', 'spawns.ps1').replace('.before-1024blowup', TAG)
       .replace('not the blowup build', 'not the spawns build')
       .replace('escape vehicles can blow up again (tools/kl_blowup.py, 2026-10-24)', 'enemies stand in the world from the load instead of plopping in (tools/kl_spawns_1024.py, 2026-10-24)'))
BAT = BL.BAT.replace('blowup.ps1', 'spawns.ps1')


def prp_name(zpath):
    with zipfile.ZipFile(zpath) as z:
        return [n for n in z.namelist() if n.lower().endswith('_main.prp')][0]


def fix_one(live, work, log=print):
    """-> (prp bytes, report) or (None, report) when no squad is PLOP. work: scratch folder."""
    src = os.path.join(work, 'src'); dst = os.path.join(work, 'dst')
    os.makedirs(src, exist_ok=True)
    shutil.copy2(live, src)
    ini = os.path.join(os.path.dirname(live), 'KLJoin.ini')
    if os.path.isfile(ini):
        shutil.copy2(ini, src)
    rep = MA.spawnfix(src, dst, {'auto': True, 'posts': False}, log=lambda *_a: None)
    if rep['problems']:
        raise ValueError('spawnfix read-back problems: %s' % rep['problems'])
    if not rep['active']:
        return None, rep
    if rep['members_changed'] != ['.prp']:
        raise ValueError('members changed %s, expected only .prp' % rep['members_changed'])
    out = os.path.join(dst, os.path.basename(live))
    with zipfile.ZipFile(out) as z:
        return z.read(prp_name(out)), rep


def build(game, out, maps=None, force=False, log=print):
    os.makedirs(out, exist_ok=True)
    man = {'maps': []}
    for m in (maps or list(MAPS)):
        f, want = MAPS[m]
        live = os.path.join(game, 'KLExpansion', 'Maps', m, f)
        have = md5(live)
        if have != want and not force:
            log('%s: live md5 %s is not the one this pass was checked on (%s): SKIPPED (use --force)' % (m, have, want))
            continue
        work = tempfile.mkdtemp(prefix='spawns1024_')
        try:
            prp, rep = fix_one(live, work, log)
            gc.collect()
        finally:
            shutil.rmtree(work, ignore_errors=True)
        if prp is None:
            log('%s: nothing to change (no PLOP squad)' % m)
            continue
        d = os.path.join(out, m)
        os.makedirs(d, exist_ok=True)
        pf = f.replace('_Main.zip', '_Main.prp')
        with open(os.path.join(d, pf), 'wb') as fh:
            fh.write(prp)
        with open(os.path.join(d, 'spawnfix.json'), 'w') as fh:
            json.dump(rep, fh, indent=1)
        man['maps'].append({'m': m, 'f': f, 'member': prp_name(live), 'prp_file': pf, 'old': have,
                            'prp_md5': hashlib.md5(prp).hexdigest(), 'new': '', 'squads': rep['active']})
        log('%s: %d squad(s) now in the world from the load: %s' % (m, len(rep['active']), ', '.join(rep['active'])))
    with open(os.path.join(out, 'spawns.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'spawns.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL spawns.bat', ''), ('UNDO spawns.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    return man


def ps(out, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(out, 'spawns.ps1'), '-Game', game]
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def rehearse(out, game, scratch, log=print):
    """INSTALL + UNDO on COPIES in <scratch>\\game; records the installed md5s into spawns.json. Never touches the real game."""
    g = os.path.join(scratch, 'game')
    mp = os.path.join(out, 'spawns.json')
    man = json.load(open(mp))
    for x in man['maps']:
        d = os.path.join(g, 'KLExpansion', 'Maps', x['m'])
        os.makedirs(d, exist_ok=True)
        shutil.copy2(os.path.join(game, 'KLExpansion', 'Maps', x['m'], x['f']), d)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    log(ps(out, g))
    new = {}
    for x in man['maps']:
        live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
        new[x['m']] = md5(live)
        with zipfile.ZipFile(live) as z:
            assert z.testzip() is None, live
            assert hashlib.md5(z.read(x['member'])).hexdigest() == x['prp_md5']
    log(ps(out, g, undo=True))
    for x in man['maps']:
        live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
        assert md5(live) == x['old'] and not os.path.exists(live + TAG), 'undo not byte identical ' + x['m']
    log('UNDO byte identical: ok')
    log(ps(out, g))
    for x in man['maps']:
        assert md5(os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])) == new[x['m']], 'not deterministic ' + x['m']
        x['new'] = new[x['m']]
    json.dump(man, open(mp, 'w'), indent=1)
    log('second install same md5s: ok')
    log(ps(out, g))                      # now chained: 'already installed'
    log(ps(out, g, undo=True))
    for x in man['maps']:
        assert md5(os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])) == x['old']
    log('final UNDO byte identical: ok')
    # a wrong live file must be refused
    x = man['maps'][0]
    live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = ps(out, g)
    assert 'SKIP, live md5' in t, t
    log('wrong live md5 refused: ok')
    gc.collect()
    shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    game = opt('--game', DD)
    out = opt('--out') or r'C:\kl_build_1024\spawns_1024n'
    maps = opt('--maps')
    man = build(game, out, maps.split(',') if maps else None, force='--force' in a)
    print('kl_spawns_1024: %d map(s) -> %s' % (len(man['maps']), out))
    if '--rehearse' in a and man['maps']:
        rehearse(out, game, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
