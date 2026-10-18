#!/usr/bin/env python3
"""
Last Call (DM05A), the ROOF MARKER: show the escape marker from the moment the escape opens, not only when a
player already stands on the roof pad. OFFLINE; reads a finished build folder, writes a new one. Nothing is
installed or started. Data only: the .prp changes (list values and one float), no entity is added, so no other
member moves and no seal pass is needed.

    python kl_club_roof.py build <folder> <out> [--hide-within N] [--timer 'van timer'|'van timer b'] [--no-hide-change] [--marker-at-start]
    python kl_club_roof.py check <folder>        what the escape marker is wired to, and from where it can be shown
    python kl_club_roof.py diff  <folder> <out>  only the .prp differs, and only in the allowed nodes

WHY (owner 2026-10-17: 'cant get to the roof idk where it is for that mission'; re/club_campaign.md, re/heli_call.md)
  FASpecials!POI!POI_TheEscapeArea (ZSTDOBJ + ZPointOfInterest + ZActivateGameplayTrackerDisplay) is wired as in stock
  F07: its ONLY sender is FASpecials!POI!Trigger_POI_TheEscapeArea, the box at the roof pad (half 700, 250, 500). So the
  marker shows once the player already stands there. Nothing shows the way before.
  The tracker float (field 3 of the ActivateGameplayTrackerDisplay, 2500 in F07) was read in kl2.exe (2026-10-18,
  the HUD's ZGameplayTrackerDisplay at HUD +0x10f8, 5 entries of 0x110 bytes, drawn by 0x8e2060): for a non-vehicle
  entry it is a HIDE-WITHIN radius (the marker is not drawn while the player is nearer than it), NOT a visibility
  distance as the notes said; the float after it (0.0) is a maximum distance, 0 = unlimited. So the radius only hides
  the marker near the pad; it is not why the roof is not shown.

WHAT IS CHANGED
  1. the target list (field 4) of the TriggerDelay2 `--timer` (default 'van timer b', ...!DisableVisionBlocker!TimerInputAI;'van timer' fails kl_fa_club.check, which wants it to name 'van on' alone,
     started 30 s after every round start, the one that shows the chopper) gets FASpecials!POI!POI_TheEscapeArea:
     the marker comes with the chopper, every round (the POI is activated by an 'AITrigger' list message like the loot
     marker's own timer Timer_POI_TheLootArea does it in stock).
  2. the hide-within radius (ZActivateGameplayTrackerDisplay field 3) 2500 -> N (default 800, GUESS: 8 m is the
     length of the last stretch from the roof door, 580 from the pad centre, so the marker stays on during the walk
     over the roof but is not on top of the player at the pad). `--no-hide-change` leaves 2500.
  The pad box's own message still arrives later and is harmless (the marker is already active).
GUESS: that the marker is in the chain of 'van timer' in a round (it is a timer the heli build already relies on);
  the unit of the radius (world units, 100 = 1 m: the same unit as every other position in the file); that a second
  activation by the pad box does not hide or reset the marker. NOT RUN IN THE GAME.
"""
import os, shutil, sys, json, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_graft

R = A.R if hasattr(A, 'R') else 'ROOT\\'
POI = 'FASpecials!POI!POI_TheEscapeArea'
TIMERS = {'van timer': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!Timer',
          'van timer b': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!TimerInputAI'}
HIDE_DEFAULT = 800.0            # GUESS (see the docstring)
TRACKER_HIDE = 3                # ZActivateGameplayTrackerDisplay field: hide-within radius (kl2 0x8e2060)
DELAY_LIST = 4                  # ZTriggerDelay2 field 4: the objects it names


def _vals(sc, k, cls):
    for kk, _i, v in kl_fa.controllers(sc, cls):
        if kk == k:
            return v
    raise KeyError('%s has no %s' % (sc.path[k], cls))


def wiring(B):
    sc = B.sc
    out = {}
    k = A.node_of(sc, POI)
    out['poi'] = k
    out['tracker'] = list(_vals(sc, k, 'ActivateGameplayTrackerDisplay'))
    out['senders'] = []
    for cls in ('TriggerBox', 'TriggerDelay2', 'RelayMessageList', 'TriggerCounter'):
        for kk, _i, v in kl_fa.controllers(sc, cls):
            for x in v:
                if isinstance(x, list) and any(isinstance(s, str) and s.endswith(POI) for s in x):
                    out['senders'].append((sc.path[kk], cls))
    return out


def check(folder, slot='F01', log=print):
    B = F.Built(folder, slot)
    w = wiring(B)
    log('POI node %d, tracker fields %s' % (w['poi'], w['tracker']))
    for p, c in w['senders']:
        log('  sent by %s (%s)' % (p, c))
    return w


def build(src, dst, timer='van timer b', hide=HIDE_DEFAULT, slot='F01', log=print, at_start=False):
    B = F.Built(src, slot)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    poi = A.node_of(sc, POI)
    tr = _vals(sc, poi, 'ActivateGameplayTrackerDisplay')
    A_ctrl = lambda k, name: A.ctrl_of(sc, k, name)
    # --marker-at-start (new, default off): ALSO name the marker in the 30 s round-start timer 'van timer' (sent by
    # AIMonitor at every round start), so the roof is shown without the player first entering tb_LEFT_TheySpotYou
    # (the only sender of 'van timer b'). A timer that already names the marker is left alone in this mode.
    names = [timer] + (['van timer'] if at_start and timer != 'van timer' else [])
    old = []
    for nm in names:
        t = A.node_of(sc, TIMERS[nm])
        tv = _vals(sc, t, 'TriggerDelay2')
        if not isinstance(tv[DELAY_LIST], list):
            raise ValueError('%s field %d is not a list: %r' % (nm, DELAY_LIST, tv[DELAY_LIST]))
        cur = list(tv[DELAY_LIST])
        if R + POI in cur:
            if at_start:
                log('%s already names the marker: left alone' % nm)
                continue
            raise ValueError('%s already names the marker' % nm)
        old = cur
        kl_fa.edit(sc, t, A_ctrl(t, 'TriggerDelay2'), lambda us, cur=cur: A.setv(sc, us, DELAY_LIST, cur + [R + POI]))
    if hide is not None and abs(tr[TRACKER_HIDE] - hide) > 1e-6:
        kl_fa.edit(sc, poi, A_ctrl(poi, 'ActivateGameplayTrackerDisplay'), lambda us: A.setv(sc, us, TRACKER_HIDE, float(hide)))
    prp = sc.p.serialize()
    import kl_prp
    back = kl_prp.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'civs.')):
            shutil.copyfile(p, os.path.join(dst, f))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['roof'] = ['.prp']
        st['same'] = [e for e in st.get('same', []) if e != '.prp']
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_club_roof: %s names %s (was %d targets%s); hide-within %s -> %s; from %s\n'
                % (timer, POI, len(old), ', + van timer at round start (marker-at-start)' if at_start else '', tr[TRACKER_HIDE], hide, B.folder))
    log('written %s: %s now names the escape marker; hide-within %s -> %s' % (dst, timer, tr[TRACKER_HIDE], hide))
    return dst


def diff(src, dst, slot='F01', log=print):
    a, b = F.Built(src, slot), F.Built(dst, slot)
    bad = []
    if a.order != b.order:
        bad.append('member order differs')
    for n in a.order:
        if a.files[n] != b.files.get(n) and not n.endswith('.prp'):
            bad.append('member %s differs' % n)
    la, lb = a.sc, b.sc
    if len(la.nodes) != len(lb.nodes):
        bad.append('node count differs')
    else:
        ok = {A.node_of(lb, TIMERS['van timer']), A.node_of(lb, TIMERS['van timer b']), A.node_of(lb, POI)}
        for k in range(len(la.nodes)):
            if (la.nodes[k]['props'], la.nodes[k]['ctrls']) != (lb.nodes[k]['props'], lb.nodes[k]['ctrls']) and k not in ok:
                bad.append('node %d (%s) differs' % (k, la.path[k]))
    return bad


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    cmd = a.pop(0)
    def opt(flag, default, conv=str):
        if flag in a:
            i = a.index(flag); v = conv(a[i + 1]); del a[i:i + 2]; return v
        return default
    if cmd == 'check':
        check(a[0]); return 0
    if cmd == 'diff':
        bad = diff(a[0], a[1])
        for x in bad:
            print('FAIL', x)
        print('diff: %d FAIL' % len(bad)); return 1 if bad else 0
    if cmd == 'build':
        timer = opt('--timer', 'van timer b')
        hide = None if '--no-hide-change' in a else opt('--hide-within', HIDE_DEFAULT, float)
        at_start = '--marker-at-start' in a
        a = [x for x in a if x not in ('--no-hide-change', '--marker-at-start')]
        build(a[0], a[1], timer, hide, at_start=at_start)
        bad = diff(a[0], a[1])
        for x in bad:
            print('FAIL', x)
        return 1 if bad else 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
