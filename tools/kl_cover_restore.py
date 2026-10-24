#!/usr/bin/env python3
"""
PUT BACK THE NoCoverBox CONTROLLERS THAT WERE HAZARD MARKERS (2026-10-24 17:10). OFFLINE: reads zips, writes a staging folder.

    python kl_cover_restore.py plan    <live zip> <donor zip>                  which stripped boxes would come back, and why
    python kl_cover_restore.py restore <live zip> <donor zip> <out folder> [--all] [--none-but PATTERN ...]
                                                                               the live zip with those controllers back on
    <donor zip> = the same map BEFORE kl_cover_pass.strip (the installed '<zip>.before-1024cover' file).

WHY. kl_cover_pass.strip (rev_1024 / rev2_1024) took the NoCoverBox controller off EVERY box of 11 Dead Men maps so that
the C key works everywhere (owner: 'withdrawal dont let you go into cover'). The boxes are Dead Men's own 'not here' marks
(ZFFPlayerMovementStandCover slot 14, 0x71f050, answers 0 inside one - re/lean_m02.md). Some are zones of taste (benches,
shop fronts), but the map authors also left REPAIR markers: 'NoCover_BugFix', 'NoCoverBugFix_nn', 'RemoveHeroCover#nn',
'NoHeroCover#nn', 'Parking_NoCover', 'Respawn_HallWay_NoCover', 'Escalator...' - places where taking cover broke in Dead
Men itself. With the controller gone the player can press C inside them and the cover movement puts him where the author
had made that impossible. The owner (16:50): 'sometimes going into cover it puts me inside the object and im stuck for
the round'. This tool brings back the controller on the boxes whose path says BAD, and leaves the zones of taste stripped
(--all = every box back = the pre-rev behaviour).

WHICH (HAZARD, matched on the box's path, case-insensitive; a GUESS about the authors' intent, the names are the evidence):
bug, remove, nohero, herocover, escal, stair, lift, elev, ladder, spawn, respawn, door, gate, roof, ramp, step, exit, garage.

HOW. The donor is read for its NoCoverBox nodes (kl_fix_lean.boxes); the live zip's node with the same PATH gets the same
controller back (key-ref to 'NoCoverBox' + an empty body, the form of every stock box: one `{ }`). Proved on the result:
the .prp is the only member that differs, the .prp re-serialises byte for byte before the change, kl_prpjoin.check finds no
more bad objects, and every restored node's controller list equals the donor's (token for token, key index aside).
"""
import json, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft
import kl_fix_lean as L
import kl_prpjoin as J

HAZARD = ('bug', 'remove', 'nohero', 'herocover', 'escal', 'stair', 'lift', 'elev', 'ladder', 'spawn', 'door', 'gate', 'roof',
          'ramp', 'step', 'exit', 'garage')


def hazard(path, extra=()):
    low = path.lower().replace('\\', '/').split('/')
    low = '/'.join(low[-3:])
    return next((t for t in tuple(HAZARD) + tuple(extra) if t in low), None)


def donor_boxes(dz):
    order, files, ext, sc, _l, _h = kl_graft.open_built(dz)
    out = {}
    for k in L.boxes(sc):
        c = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) == L.CTRL]
        out[sc.path[k]] = c[0]
    return out


def plan(lz, dz, only=None, every=False, log=print):
    don = donor_boxes(dz)
    order, files, ext, sc, _l, _h = kl_graft.open_built(lz)
    cur = {sc.path[k]: k for k in range(1, len(sc.nodes))}
    now = set(sc.path[k] for k in L.boxes(sc))
    todo, miss, keep = [], [], []
    for p, c in don.items():
        why = 'all' if every else hazard(p, only or ())
        if p in now:
            continue                                  # (it still has the controller)
        if p not in cur:
            miss.append(p)
        elif why:
            todo.append((p, why))
        else:
            keep.append(p)
    log('%s: donor has %d NoCoverBox, live has %d; back: %d, left stripped: %d, not found in live: %d'
        % (os.path.basename(os.path.dirname(lz)) or lz, len(don), len(now), len(todo), len(keep), len(miss)))
    return don, todo, keep, miss


def restore(lz, dz, outdir, only=None, every=False, log=print):
    don, todo, keep, miss = plan(lz, dz, only, every, log)
    if not todo:
        log('%s: nothing to restore' % lz)
        return None
    order, files, ext, sc, _l, _h = kl_graft.open_built(lz)
    if sc.p.serialize() != files[ext['.prp']]:
        raise ValueError('the .prp does not re-serialise byte for byte: not changed')
    data0, bad0, _p, _n = J.check(sc, log=lambda *_a: None)
    cur = {sc.path[k]: k for k in range(1, len(sc.nodes))}
    kidx = sc.p.key_index(L.CTRL)
    for p, _why in todo:
        k = cur[p]
        d = don[p]
        sc.nodes[k]['ctrls'].append(((d[0][0], struct.pack('<I', kidx)), list(d[1])))
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0):
        raise ValueError('%d objects do not fit their class after the change (%d before)' % (len(bad), len(bad0)))
    if len(L.boxes(sc)) < len(todo):
        raise ValueError('the controllers did not take')
    files[ext['.prp']] = data
    os.makedirs(outdir, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(outdir, os.path.basename(lz)), [(n, files[n]) for n in order])
    with zipfile.ZipFile(lz) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != ['.prp']:
        raise ValueError('more than the .prp differs: %s' % diff)
    # read it back: every restored node carries the controller, the donor's body
    _o, _f, _e, sc2, _l2, _h2 = kl_graft.open_built(out)
    back = {sc2.path[k] for k in L.boxes(sc2)}
    for p, _why in todo:
        if p not in back:
            raise ValueError('read-back: %s has no NoCoverBox' % p)
        c = [c for c in sc2.nodes[{sc2.path[k]: k for k in range(1, len(sc2.nodes))}[p]]['ctrls'] if sc2.p.key(c[0]) == L.CTRL][0]
        if c[1] != don[p][1] or c[0][0] != don[p][0][0]:
            raise ValueError('read-back: %s: controller body differs from the donor\'s' % p)
    log('%s: NoCoverBox back on %d boxes (%d stay stripped); only %s differs' % (os.path.basename(lz), len(todo), len(keep), diff))
    with open(out + '.restore.json', 'w') as fh:
        json.dump({'live': lz, 'donor': dz, 'restored': [{'path': p, 'because': w} for p, w in todo], 'left_stripped': keep, 'not_found': miss}, fh, indent=1)
    return out


def main():
    a = sys.argv[1:]
    every = '--all' in a
    if every:
        a.remove('--all')
    only = []
    while '--none-but' in a:
        i = a.index('--none-but'); only.append(a[i + 1]); del a[i:i + 2]
    if len(a) == 3 and a[0] == 'plan':
        don, todo, keep, miss = plan(a[1], a[2], only, every)
        for p, w in todo:
            print('  BACK  [%s] %s' % (w, p))
        for p in keep:
            print('  stays stripped  %s' % p)
    elif len(a) == 4 and a[0] == 'restore':
        restore(a[1], a[2], a[3], only, every)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
