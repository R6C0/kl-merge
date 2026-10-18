#!/usr/bin/env python3
"""
kl_fa_hasta_police.py - Hasta (DM11B), heli escape: hold back the plaza police so the chopper is not shot down. OFFLINE post-pass, opt-in.

    python kl_fa_hasta_police.py <finished map folder> <out folder> [--keep <substr>[,<substr>...]] [--keep-none]
    python kl_fa_hasta_police.py check <folder>            # prints what each GatePath lists and each squad's active flag

WHY (re/open_work_log.md 2026-10-18 07:34 / 07:50 / 08:22, kl-merge-3f live runs L44-L49): the chopper survives its landing only when most of the
plaza squad is dead at boarding (good L9, L36, L47, L48; heli destroyed 0.9-4.9 s after lift-off in L44-L46, L49 with ~10 police alive). The squad is the
four F07 police squads of kl_fa_hasta_layer.ARRIVE_XZ (3 + 2 + 3 + 2 = 10 men, 16 .. 29 m from the pad (27500, 0, 22800)). They are started by the two
GatePath nodes of Gameplay!RunToEscape!RunToEscapeGate (Way#01 / Way#02, field 0 = the four '10_RunToCover' entries), which the stair's box and the
backstop timer fire. The hook-side answer (refuse the heli call while more than 2 plaza police live) is the owner's call and not built; this is the
level-side equivalent: only the squads named by --keep still get that start entry, so at most their men ever fight (default: 'ExitStreet_Left', 2 men).

Only the .prp member of <slot>_Main.zip changes (two GatePath lists); every other member and every side file is copied as it was. The default build
(kl_fa_hasta_layer / kl_fa_hasta) is untouched, so nothing changes unless this step is run.

GUESS (not run in the game):
  * a squad whose start entry is never fired stays idle (its ZSquadScript active flag is already 0 in the finished level) - the men stand on the
    square dormant, as they do before the alarm today; they may still react when shot at or when they see a heister.
  * 2 live police are too few to bring the chopper down (the observed good runs had 0 .. 4 alive); that the police shoot the chopper at all is itself a GUESS
    of the 07:34 note (no hit lines).
  * the round's "police arrive" pressure drops by 8 of 10 men; the ending (all crew dead / escape) is not otherwise touched.
"""
import os, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_hasta_layer as L, kl_prpjoin as J

KEEP_DEFAULT = ('ExitStreet_Left',)         # GUESS: the squad farthest from the pad (x 25,200, 23 m west) with the fewest men (2)


def gate_nodes(sc):
    out = []
    for w in L.GATE_WAYS:
        ks = sc.resolve(L.R + L.ROLE['gate'] + '\\' + w)
        if len(ks) != 1 or not kl_fa.has(sc, ks[0], 'GatePath'):
            raise SystemExit('%s: not one GatePath node' % w)
        out.append(ks[0])
    return out


def arrive_entries():
    return [L.R + n + '\\' + L.ARRIVE_START for n in L.ARRIVE_XZ]


def keep_list(keep):
    """-> the ARRIVE_START entries that stay. A substring that names no squad is an error (a typo must not silently keep nothing)."""
    ent = arrive_entries()
    out = []
    for s in keep:
        hit = [e for e in ent if s in e]
        if not hit:
            raise SystemExit('--keep %r names none of %s' % (s, [n.split('!')[-1] for n in L.ARRIVE_XZ]))
        out += [e for e in hit if e not in out]
    return [e for e in ent if e in out]     # the original order


def check(sc, log=print):
    bad = []
    ent = arrive_entries()
    for k in gate_nodes(sc):
        lst = L.values(sc, k, 'GatePath')[0]
        log('  node %d GatePath f0: %s' % (k, [e.split('\\')[-2].split('!')[-1] for e in lst]))
        if any(e not in ent for e in lst):
            bad.append('node %d names an entry that is not an arriving police squad' % k)
        if any(not sc.resolve(e) for e in lst):
            bad.append('node %d: dangling entry' % k)
    for n in L.ARRIVE_XZ:
        k = L.A.node_of(sc, n)
        a = L.values(sc, k, 'ZSquadScript')[L.SQUAD_ACTIVE]
        log('  %s: active flag %r' % (n.split('!')[-1], a))
        if a != 0:
            bad.append('%s: active flag %r (a dormant squad is wanted)' % (n, a))
    return bad


def run(folder, out, keep=KEEP_DEFAULT, log=print):
    folder, out = os.path.abspath(folder), os.path.abspath(out)
    zn = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    zp = os.path.join(folder, zn)
    sc, _snd, _loc = kl_fa.load(zp)
    kept = keep_list(keep)
    was = {}
    for k in gate_nodes(sc):
        lst = L.values(sc, k, 'GatePath')[0]
        if sorted(lst) != sorted(arrive_entries()):
            raise SystemExit('node %d GatePath is not the four arriving squads (already edited?): %s' % (k, lst))
        was[k] = lst
        i = L.A.ctrl_of(sc, k, 'GatePath')
        kl_fa.edit(sc, k, i, lambda us: L.A.setv(sc, us, 0, list(kept)))
    data, bad, _paths, _n = J.check(sc, log=lambda *_a: None)
    if bad:
        raise SystemExit('%d objects do not fit after the edit' % len(bad))
    problems = check(sc, log=lambda *_a: None)
    if problems:
        raise SystemExit('check: ' + '; '.join(problems))
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(folder):
        if f != zn and os.path.isfile(os.path.join(folder, f)):
            shutil.copyfile(os.path.join(folder, f), os.path.join(out, f))
    with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(os.path.join(out, zn), 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as zo:
        for zi in zin.infolist():
            d = data if zi.filename.lower().endswith('_main.prp') else zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, zi.date_time)
            ni.compress_type, ni.external_attr = zi.compress_type, zi.external_attr
            zo.writestr(ni, d)
    men = {n: m for n, (_a, m, _c, _d) in L.ARRIVE_XZ.items()}
    left = sum(len(m) for n, m in men.items() if (L.R + n + '\\' + L.ARRIVE_START) in kept)
    log('hasta police: GatePath Way#01/#02 f0 %d -> %d entries (%s); %d of %d men can still be started' % (
        len(arrive_entries()), len(kept), ', '.join(e.split('\\')[-2].split('!')[-1] for e in kept) or 'none', left, sum(len(m) for m in men.values())))
    return kept


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'check':
        zp = a[1] if a[1].lower().endswith('.zip') else os.path.join(a[1], [f for f in os.listdir(a[1]) if f.lower().endswith('_main.zip')][0])
        sc, _s, _l = kl_fa.load(zp)
        b = check(sc)
        print('PASS' if not b else 'FAIL: ' + '; '.join(b))
        sys.exit(1 if b else 0)
    if len(a) < 2 or a[0].startswith('--'):
        print(__doc__); sys.exit(2)
    keep = KEEP_DEFAULT
    if '--keep-none' in a:
        keep = ()
    elif '--keep' in a:
        keep = tuple(a[a.index('--keep') + 1].split(','))
    run(a[0], a[1], keep)
