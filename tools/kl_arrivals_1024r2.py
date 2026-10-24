"""kl_arrivals_1024r2.py - 'enemies must not plop in' round 2 (owner 2026-10-24). Offline only. Two rerunnable passes, each an
input zip -> output zip (only the .prp member changes), md5-pinned input (unless --force), idempotent, staged with an md5-chained
INSTALL/UNDO built from kl_spawns_1024's installer (backup <zip>.before-1024<name>, never overwritten).

  plop     DM11B (Hasta): the audit (kl_map_ai.spawn_rows) calls 2 squads PLOP (RebelSideBarricade_Guard / _01, 8 men): ZSquadScript
           field 3 = 1 so they stand in the world from the load. Input = the live zip after hasta_1024n (323c13f3).
           Same code path as kl_spawns_1024 (kl_map_ai.spawnfix auto), so DM01B / DM09 are already covered by spawns_1024n.
  carexit  DM01 (FrontMall_01 / _02: 4 cops in 2 parked Bentleys): kl_convert drops the VehicleExitBehaviourRout controller because
           kl_rtp has no field kind for its field 2 (type handler 54, a flag set over EBoneType; kl_rtp kind None -> conv.object
           returns None -> 'ctrl_removed'). kl_map_ai.cars(restore=True) teaches kind 'k' in memory and puts Dead Men's two
           controllers back (tokens copied from M01_FA_A, ref keys re-indexed to the build's pool). Check: J.check 0 misfits, 0
           unresolved paths, faults() empty. NO stock Dog Days level stores this controller: whether DD's ZVehicleExitBehaviourRout
           runs (cops get out) is UNPROVEN, hence its own opt-in pack.
NOT DONE (proved not available offline): timer-wave squads through doors. Probe over all 'by a timer' squads of DM01 / DM03A / DM06B /
DM09 / DM11B: no named door/gate/shutter node within 25 m of a wave position that is not already a DoorCtrl or a decor leaf; the only
offline-proven door mechanism (DeactivateGeom list, kl_hc2_garagedoor.py) makes a door vanish, it cannot open for a spawn.
Usage (from tools/):  python kl_arrivals_1024r2.py plop|carexit [--game <DD>] [--out <folder>] [--force] [--rehearse <scratch>]
"""
import os, sys, json, hashlib, shutil, subprocess, zipfile, tempfile, gc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_blowup as BL
import kl_spawns_1024 as SP

DD = BL.DD
md5 = BL.md5
PASSES = {
    'plop': {'m': 'DM11B', 'f': 'F04_Main.zip', 'md5': '323c13f3f76095941db9eecbe0f82bdb', 'tag': '.before-1024arrivals',
             'out': r'C:\kl_build_1024\arrivals_1024r2',
             'what': 'Hasta squads stand in the world from the load instead of plopping in'},
    'carexit': {'m': 'DM01', 'f': 'F01_Main.zip', 'md5': '5522ebcf5df8b5fe7cef99adef13fc7a', 'tag': '.before-1024carexit',
                'out': r'C:\kl_build_1024\carexit_1024r2',
                'what': 'DM01 cops get out of the parked Bentleys (VehicleExit routs put back; UNPROVEN in game)'},
}


def installer(name, tag, what):
    ps1 = (SP.PS1.replace('spawns.json', name + '.json').replace('spawns.ps1', name + '.ps1').replace(SP.TAG, tag)
           .replace('not the spawns build', 'not the %s build' % name)
           .replace('enemies stand in the world from the load instead of plopping in (tools/kl_spawns_1024.py, 2026-10-24)',
                    '%s (tools/kl_arrivals_1024r2.py, 2026-10-24)' % what))
    return ps1, SP.BAT.replace('spawns.ps1', name + '.ps1')


def carexit_prp(live):
    import kl_map_ai as MA, kl_graft, kl_prpjoin as J
    order, files, ext, sc, _l, _h = kl_graft.open_built(live)
    d0, bad0, p0, _ = J.check(sc, log=lambda *_a: None)
    if d0 != files[ext['.prp']]:
        raise ValueError('the .prp does not re-serialise byte for byte')
    lost = MA.lost_exits(sc, 'M01_FA_A')
    if not lost:
        return None, {'restored': []}
    rep = MA.cars(sc, 'M01_FA_A', restore=True, log=lambda *_a: None)
    d, bad, p, _ = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0) or len(p) > len(p0):
        raise ValueError('after the change %d misfits (%d before), %d unresolved paths (%d before)' % (len(bad), len(bad0), len(p), len(p0)))
    f = MA.faults(sc)
    if f:
        raise ValueError('reference lists at fault: %s' % f[:5])
    if MA.lost_exits(sc, 'M01_FA_A'):
        raise ValueError('exit routs still missing after the restore')
    return d, {'restored': rep, 'prp_bytes': [len(files[ext['.prp']]), len(d)]}


def plop_prp(live):
    work = tempfile.mkdtemp(prefix='arr1024_')
    try:
        return SP.fix_one(live, work)
    finally:
        gc.collect(); shutil.rmtree(work, ignore_errors=True)


def build(kind, game, out=None, force=False, src=None, log=print):
    P = PASSES[kind]; out = out or P['out']; name = 'arrivals' if kind == 'plop' else 'carexit'
    live = src or os.path.join(game, 'KLExpansion', 'Maps', P['m'], P['f'])
    have = md5(live)
    if have != P['md5'] and not force:
        log('%s: input md5 %s is not the one this pass was checked on (%s): SKIPPED (use --force)' % (P['m'], have, P['md5']))
        return None
    prp, rep = (plop_prp if kind == 'plop' else carexit_prp)(live)
    if prp is None:
        log('%s: nothing to change' % P['m']); return None
    os.makedirs(os.path.join(out, P['m']), exist_ok=True)
    pf = P['f'].replace('_Main.zip', '_Main.prp')
    open(os.path.join(out, P['m'], pf), 'wb').write(prp)
    json.dump(rep, open(os.path.join(out, P['m'], name + '_report.json'), 'w'), indent=1, default=str)
    man = {'maps': [{'m': P['m'], 'f': P['f'], 'member': SP.prp_name(live), 'prp_file': pf, 'old': have,
                     'prp_md5': hashlib.md5(prp).hexdigest(), 'new': ''}]}
    json.dump(man, open(os.path.join(out, name + '.json'), 'w'), indent=1)
    ps1, bat = installer(name, P['tag'], P['what'])
    open(os.path.join(out, name + '.ps1'), 'w', newline='\r\n').write(ps1)
    for nm, arg in (('INSTALL %s.bat' % name, ''), ('UNDO %s.bat' % name, '-Undo')):
        open(os.path.join(out, nm), 'w', newline='').write(bat.format(arg=arg))
    log('%s: %s -> %s (prp md5 %s)' % (P['m'], kind, out, man['maps'][0]['prp_md5']))
    return man


def rehearse(kind, out, game, scratch, log=print):
    """Same as kl_spawns_1024.rehearse, on scratch copies only; asserts every path is inside scratch first."""
    name = 'arrivals' if kind == 'plop' else 'carexit'; tag = PASSES[kind]['tag']
    g = os.path.join(scratch, 'game')
    assert os.path.abspath(g).lower().startswith(os.path.abspath(scratch).lower()) and os.path.abspath(g).lower() != os.path.abspath(game).lower()
    log('rehearsal target: %s (inside scratch: ok)' % g)
    mp = os.path.join(out, name + '.json'); man = json.load(open(mp)); x = man['maps'][0]
    d = os.path.join(g, 'KLExpansion', 'Maps', x['m']); os.makedirs(d, exist_ok=True)
    shutil.copy2(os.path.join(game, 'KLExpansion', 'Maps', x['m'], x['f']), d)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    live = os.path.join(d, x['f'])
    assert os.path.abspath(live).lower().startswith(os.path.abspath(scratch).lower())
    run = lambda undo=False: subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(out, name + '.ps1'),
                                             '-Game', g] + (['-Undo'] if undo else []), capture_output=True, text=True)
    r = run(); log(r.stdout + r.stderr)
    new = md5(live)
    with zipfile.ZipFile(live) as z:
        assert z.testzip() is None and hashlib.md5(z.read(x['member'])).hexdigest() == x['prp_md5']
    r = run(True); log(r.stdout + r.stderr)
    assert md5(live) == x['old'] and not os.path.exists(live + tag), 'undo not byte identical'
    log('UNDO byte identical: ok')
    run(); assert md5(live) == new, 'not deterministic'
    x['new'] = new; json.dump(man, open(mp, 'w'), indent=1)
    run(); run(True); assert md5(live) == x['old']
    log('re-install deterministic, final UNDO byte identical: ok  (installed md5 %s)' % new)
    open(live, 'ab').write(b'x'); t = run(); t = t.stdout + t.stderr
    assert 'SKIP, live md5' in t, t
    log('wrong live md5 refused: ok')
    gc.collect(); shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    if not a or a[0] not in PASSES:
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    game = opt('--game', DD); out = opt('--out') or PASSES[a[0]]['out']
    man = build(a[0], game, out, '--force' in a, opt('--src'))
    if man and opt('--rehearse'):
        rehearse(a[0], out, game, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
