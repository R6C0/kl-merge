r"""kl_dm02shop_1110.py - DM02 (Late Night Opening, slot F02): a USE-KEY PROMPT on the three Atrium_201a shutters. 2026-11-10. OFFLINE:
reads the live DM02 zips, writes a stage; nothing is installed, the game is not started.

OWNER (2026-11-10, playing DM02): "no prompt to open shutter". The installed dm02coop_1109 TIMER variant (live zip 43c088c2) lifts the three shutters
(REF 24710/24711/24712) after 90 s with no prompt: every co-op trigger was cut from them. This stage puts the triggers back, on top of that install:
 1. KLCoopN!SoloLift (PlayerAction, the stock 'L03_CoOpLift' prompt '{TapUse} Lift Door', a use box in front of each shutter): field 1 = [KLCoopN!Pathblocker,
    KLCoopN!Open] again and field 8 = 1 (enabled), so pressing the use key plays the keyed shutter (MatPosAnimProxy on KLCoopN!Open) and clears the Pathblocker;
 2. KLCoopN!Controller (CoopAirlock) field 23 = [Pathblocker, Open] again (two heisters in the boxes: Arcade / online, where PlayerAction lists do not run);
 3. the second TriggerDelay2 on KLShops_OpenTimer (the 90 s timer) is REMOVED, so a shutter is triggered once (a retrigger replays frames 0..82 = drop and
    rise again). The timer stays available as the fallback: UNDO this stage (byte exact) = the 90 s timer variant of dm02coop_1109 again.
Nothing else changes: only the .prp member + the bots zip (rebuilt from it). Slots, entities, .oct, HVK, .buf are byte for byte the live ones.

CHAIN: this stage's input is the live zip 43c088c2 / bots bb8f04cb (dm02coop_1109 timer, installed). The door/glass pass of the other agent edits the same zip:
install whichever comes first, then RE-STAGE the other on the new live md5s (install.py refuses a non-pinned live zip: `python tools/kl_dm02shop_1110.py stage`
re-pins to --live after the pins at the top of this file are updated). Undo in reverse order.

usage (from tools/):
  python kl_dm02shop_1110.py build [--out <dir>] [--live <F02_Main.zip>]     one zip + bots zip + md5 sidecar
  python kl_dm02shop_1110.py stage [--out C:\kl_build_1024\dm02shop_1110\prompt] [--live <Maps\DM02>]     + install.py / UNDO bat / README
  python kl_dm02shop_1110.py check <zip> [--live <F02_Main.zip>]
"""
import collections, json, os, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft
import kl_fa_bots as F
import kl_botsonline
import kl_dm02coop_1109 as C

MAPDIR = C.MAPDIR
OUT = r'C:\kl_build_1024\dm02shop_1110\prompt'
TAG = '.before-dm02shop1110'
SHUTTER_REFS = C.SHUTTER_REFS
LIVE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'         # live F02_Main.zip 2026-11-10 (dm02coop_1109 timer installed)
LIVE_BOTS_PIN = 'bb8f04cb6b8460b5f34df021da629c9f'
LIVE_BASE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'
DEFAULT_VARIANT = 'use'

GUESSES = [
    'PlayerAction (the stock Lift Door prompt) with field 1 = [Pathblocker, Open] and field 8 = 1 fires its list on the use key in the solo / host process (it did so for the L03 lift it was cloned from)',
    'the use box (LIFT_HALF from kl_dm02fix_1108) stands where the player meets the shutter: the prompt shows when walking up to the shutter from the street side; if it does not, widen it (bench)',
    'a second press (PlayerAction not one-shot) would replay frames 0..82 = the shutter drops and rises again: the stock lift prompt is single use (GUESS), the bench presses twice',
    'the CoopAirlock field-23 list is the same completion list it had before dm02coop_1109 (copied from the backup zip .before-dm02coop1109, FACT) and runs on both seats',
]


def md5(p):
    return C.md5(p)


def part_prp(B, rep):
    """In place on B.sc. -> serialized .prp."""
    sc = B.sc
    node = {sc.names[k]: k for k in range(1, len(sc.names))}
    lists = {}
    for n in (1, 2, 3):
        pb, op = 'KLCoop%d!Pathblocker' % n, 'KLCoop%d!Open' % n
        if sc.names.count(pb) != 1 or sc.names.count(op) != 1:
            raise ValueError('KLCoop%d: want exactly one Pathblocker and one Open node' % n)
        lists[n] = [sc.path[node[pb]], sc.path[node[op]]]
    done = collections.OrderedDict(airlock=[], solo=[])
    for n in (1, 2, 3):
        k = node['KLCoop%d!Controller' % n]
        j = [j for j, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'CoopAirlock']
        if len(j) != 1:
            raise ValueError('KLCoop%d!Controller: %d CoopAirlock' % (n, len(j)))

        def fa(us, n=n):
            if len(us) != 28 or kl_fa.value(sc, us[23]) != []:
                raise ValueError('CoopAirlock field 23 is not the emptied list of the timer variant (wrong live zip?)')
            us[23] = kl_fa._refs(sc, lists[n])
        kl_fa.edit(sc, k, j[0], fa)
        done['airlock'].append(sc.names[k])
        ks = node['KLCoop%d!SoloLift' % n]
        js = [j for j, (nm, _b) in enumerate(sc.nodes[ks]['ctrls']) if sc.p.key(nm) == 'PlayerAction']
        if len(js) != 1:
            raise ValueError('KLCoop%d!SoloLift: %d PlayerAction' % (n, len(js)))

        def fs(us, n=n):
            if len(us) != 21 or kl_fa.value(sc, us[1]) != [] or us[8][0][0] != 6:
                raise ValueError('SoloLift PlayerAction is not the emptied one of the timer variant (wrong live zip?)')
            us[1] = kl_fa._refs(sc, lists[n])
            us[8] = [(6, bytes([1]))]
        kl_fa.edit(sc, ks, js[0], fs)
        done['solo'].append(sc.names[ks])
    # the 90 s timer: the SECOND TriggerDelay2 on KLShops_OpenTimer (first = 1.0 s -> OpenNow) goes away
    kt = node['KLShops_OpenTimer']
    tj = [j for j, (nm, _b) in enumerate(sc.nodes[kt]['ctrls']) if sc.p.key(nm) == 'TriggerDelay2']
    if len(tj) != 2:
        raise ValueError('KLShops_OpenTimer: %d TriggerDelay2 (want 2 = the dm02coop_1109 timer variant)' % len(tj))
    us = [kl_fa.value(sc, u) for u in kl_fa.units(sc.nodes[kt]['ctrls'][tj[1]][1][1:-1])]
    if len(us[4]) != 6 or us[0] < 5.0:
        raise ValueError('the second TriggerDelay2 is not the 6-target timer: %s' % us)
    del sc.nodes[kt]['ctrls'][tj[1]]
    rep['prp'] = collections.OrderedDict(done, timer_removed=us[0])
    prp = sc.p.serialize()
    if F.Prp(prp).serialize() != prp:
        raise ValueError('the patched .prp does not round-trip')
    return prp


def build(live, outdir, log=print):
    B = F.Built(live, 'F02')
    rep = collections.OrderedDict(variant=DEFAULT_VARIANT, live=live, live_md5=md5(live))
    prp = part_prp(B, rep)
    files = dict(B.files)
    files[B.ext['.prp']] = prp
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F02_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    if diff != ['F02_Main.prp']:
        raise ValueError('members changed %s, expected only the .prp' % diff)
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
    with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
    log('dm02shop_1110 prompt -> %s (%s) members %s' % (plain, rep['out_md5'], diff))
    return rep


def check(plain, live, log=print):
    """Read-back of a built zip against the live one -> list of problems."""
    bad = []
    A, N = F.Built(live, 'F02'), F.Built(plain, 'F02')
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    if diff != ['F02_Main.prp']:
        bad.append('members changed: %s' % diff)
    sa, sn = A.scene.slots(), N.scene.slots()
    if [e.name for e in A.ents] != [e.name for e in N.ents] or [sa[e] for e in A.ents] != [sn[e] for e in N.ents]:
        bad.append('entities / slots changed')
    if any((a.flags, a.raw, a.trans, a.rot) != (b.flags, b.raw, b.trans, b.rot) for a, b in zip(A.ents, N.ents)):
        bad.append('an entity changed')
    for m in ('.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.HVK', '.buf', '.gms'):
        if A[m] != N[m]:
            bad.append('%s changed' % m)
    ca, pa = C._ctrl_map(A)
    cb, pb = C._ctrl_map(N)
    if list(ca) != list(cb) or pa != pb:
        bad.append('node list / node properties changed')
    chg = sorted(p for p in ca if ca[p] != cb[p])
    want = sorted(p for p in ca if p.endswith(('!Controller', '!SoloLift')) and '\\KLCoop' in p) + ['ROOT\\KL_Shops!\\KLShops_OpenTimer']
    if chg != sorted(want):
        bad.append('controllers changed on %s' % [p[-30:] for p in chg])
    for n in (1, 2, 3):
        lst = ['ROOT\\KL_Shops!\\KLCoop%d!Pathblocker' % n, 'ROOT\\KL_Shops!\\KLCoop%d!Open' % n]
        for p, cs in cb.items():
            for nm, v in cs:
                if nm == 'CoopAirlock' and p.endswith('KLCoop%d!Controller' % n) and v[23] != lst:
                    bad.append('airlock %d: %s' % (n, v[23]))
                if nm == 'PlayerAction' and p.endswith('KLCoop%d!SoloLift' % n) and (v[1] != lst or v[8] != 1 or v[7] != 'CoOpDoors/L03_CoOpDoors/L03_CoOpLift'):
                    bad.append('solo lift %d: %s %s' % (n, v[1], v[8]))
    tm = [c for c in cb['ROOT\\KL_Shops!\\KLShops_OpenTimer'] if c[0] == 'TriggerDelay2']
    if len(tm) != 1 or tm[0][1][0] != 1.0:
        bad.append('timer: %s' % tm)
    if [c for c in cb['ROOT\\KL_Shops!\\KLShops_OpenNow'] if c[0] == 'DeactivateGeom'] != [c for c in ca['ROOT\\KL_Shops!\\KLShops_OpenNow'] if c[0] == 'DeactivateGeom']:
        bad.append('OpenNow changed')
    mo = lambda X: [(o['node'], o['amount'], o['kind'], o['container']) for o in F.money_objects(X)]
    if mo(A) != mo(N):
        bad.append('bots: the money census changed')
    return bad


README = r'''DM02 SHUTTER PROMPT 1110 (Late Night Opening, slot F02)       built OFFLINE, NOT installed, NOT run in the game
================================================================================================================
Owner: "no prompt to open shutter". On top of the installed dm02coop_1109 TIMER variant (live zip %(live)s) this gives the three Atrium_201a shutters the
stock use-key prompt '{TapUse} Lift Door' (a use box in front of each) again, restores the two-heister CoopAirlock lists, and removes the 90 s timer so each
shutter plays once. Only the .prp changes (+ the bots zip rebuilt from it).
Undo (UNDO dm02 shop 1110 prompt.bat, byte exact) = the 90 s timer variant of dm02coop_1109 back (the fallback).
Install (game closed): INSTALL dm02 shop 1110 prompt.bat  or  python install.py [--dry] [--game <dir> --skip-run-check]
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s. Backups: <name>%(tag)s. Staged: zip %(zip)s bots %(botsn)s.
CHAIN: the other agent's door/glass pass edits the same zip: install one, then re-stage the other on the new live md5 (install.py refuses a foreign live zip).
Undo in reverse order.

GUESSes (the bench decides):
%(guesses)s

BENCH: solo DM02, walk to the first shutter (x -1990, z 1032 ...): the prompt shows; press use: the shutter rises (draw + body), walk in; press again: nothing
should drop; 2 seats: both in the KLCoopN boxes (airlock) = it rises on both seats; round 2: closed again. 0 asserts / faults.
'''


def stage(live_dir, out, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    bots = os.path.join(live_dir, 'F02_Main.bots.zip')
    if md5(live) != LIVE_PIN or md5(bots) != LIVE_BOTS_PIN:
        raise SystemExit('live DM02 zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin)' % (LIVE_PIN, LIVE_BOTS_PIN))
    if open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip() != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is not %s' % LIVE_BASE_PIN)
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    d = os.path.join(out, 'variant_use')
    rep = build(live, d, log)
    bad = check(os.path.join(d, 'F02_Main.zip'), live, log)
    if bad:
        raise SystemExit('check failed: %s' % bad)
    rep['check'] = 'ok'
    staged = {'use': {n: md5(os.path.join(d, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}}
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(C.INSTALL_PY % dict(tag=TAG, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, staged=repr(staged), default=DEFAULT_VARIANT))
    for nm, arg in (('INSTALL dm02 shop 1110 prompt', ''), ('UNDO dm02 shop 1110 prompt', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as fh:
        fh.write(README % dict(live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, tag=TAG, zip=staged['use']['F02_Main.zip'],
                               botsn=staged['use']['F02_Main.bots.zip'], guesses='\n'.join(' %d. GUESS: %s' % (i + 1, g) for i, g in enumerate(GUESSES))))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(dict(report=rep, staged=staged), fh, indent=1, default=str)
    log(json.dumps(staged, indent=1))
    return rep, staged


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    live = opt('--live', os.path.join(MAPDIR, 'F02_Main.zip'))
    if a and a[0] == 'build':
        out = opt('--out', OUT)
        build(live, os.path.join(out, 'variant_use'))
        bad = check(os.path.join(out, 'variant_use', 'F02_Main.zip'), live)
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    if a and a[0] == 'stage':
        stage(opt('--live', MAPDIR), opt('--out', OUT))
        return 0
    if len(a) >= 2 and a[0] == 'check':
        bad = check(a[1], live)
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
