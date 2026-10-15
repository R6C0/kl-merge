"""kl_rt_window2.py (2026-10-15: + --no-glass = the path blocker only; the owner: the glass may break by gunfire, and w_rt's 1e9 glass kept the blast from opening it) - from kl_rt_window.py - Retomoto (DM09 in slot F06): the boardroom window holds until the blast, for bullets AND for the AI.
(w_rt, 2026-10-14; a NEW step on a finished build, written beside the tools, not in tools/.) OFFLINE: nothing is installed.

    python3 .../x/vmrun.py .../x/w_rt/kl_rt_window.py add   <build folder> <out folder> [--slot F06] [--no-block]
    (--no-block: only the glass, no path blocker - the fallback if live the blocker does not open at the blast)
    python3 .../x/vmrun.py .../x/w_rt/kl_rt_window.py check <build folder> [--slot F06]
    (run from $HOME/mnt/kl-merge/tools)

Owner, 2026-10-14: 'the glass can be broken via gunshot instead of the explosion' and 'ai heisters can walk through into the room'.

1. THE GLASS. The intact window SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00 carries a ZShotActivate (fields
   0..10 = 1, '', 0, on-list, off-list, 350.0, 320.0, 0, eSPRAY_NOTHING, 0, 'ForceTriggerShotActivate'). kl2.exe (vtable 0xba93a4,
   message handler slot 26 = 0x47f130 -> 0x7730f0 -> 0x760780): a hit of damage d counts only when d > [obj+0x54] and then takes
   d off [obj+0x50]; at [obj+0x50] <= 0 the object swaps (on-list shown, off-list hidden; [obj+0x44] = 1). The forced message
   (branch 0x47f2f4: 'ForceTriggerShotActivate' -> [obj+0x4c] = 2, 0x6b32b0) swaps it WITHOUT looking at either float - that is
   the blast timer's AIDWrapper (Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo, at 16.5 s). ASSUMPTION: fields 5 / 6
   are +0x50 / +0x54 (the order of the record). This step writes 1.0e9 into BOTH, so no bullet, grenade or bomb damage can
   reach either test, whichever is which; the forced swap at the blast is unchanged. The cracked panes A / B (hidden until the
   blast) keep their own values: after the blast they break as before.
2. THE AI. The navigation mesh crosses the window: polygon 1912 (the boardroom, x 5545..5875) - 2133 (the sill strip, x 5872..5895,
   z -431..231) - 2134 - 2135 (the balcony), the middle bay; kl_route's AI line from the balcony landing (6090, 21011, 142) to the
   room (5168, 20996, 281) goes straight through it. The intact window does not stop an NPC that follows the mesh: in the owner's
   v66 rounds (KLHook.log 20:51:55, 20:58:53) the bots were inside at 8 s (heist stage 1 at 20:52:03 / 20:59:00; 'stood 6 s at
   (5194, 20990, 131)' at 20:52:11), 8 s before the blast. v66's rappel routs hand each squad on to 010_DefendBehaviour_to_loot the
   moment its bot lands (kl_fa_rappel_bots.py 'THE HAND-OVER'), whose place is in the room; before v66 the squads waited for
   Timer_start_bots (18 s) and the glass was blown by then (20:38:40: they stood on the balcony until 17.7 s).
   This step adds the stock way to shut a mesh crossing until a moment: F07's own Gameplay!010_FirstFight!PF_Blocker form (a
   ZBoxPrimitive with PathBlocker 'eUnblock', 'eBlocking'; F07's 20 s TriggerDelay2 Timer_PFBlocker names it and so opens it;
   Retomoto's lobby glass has four of the same, M09_B ...!PathBlockerGlass). Placed over the sill strip only: centre
   (5884, 21022, -100), half extents (8, 40, 335) - inside polygon 2133 and clear of 1912 (x <= 5875) and 2134 (x >= 5895) - and
   put on the list of the blast timer Gameplay!010_FirstFight!RivalMercVan!Timer (16.5 s), the timer that fires the glass.
   ASSUMPTION (not read in kl2.exe): a blocker shuts the polygons its box touches for the crew and the police; a TriggerDelay2's
   list message makes an 'eUnblock' blocker open (F07 does exactly this).
Everything else of the build is copied as it is (KLJoin.ini, KLTalk.ini, ...). The .gms / .prp / .buf / .oct / .rmi / .rmc are
rewritten for the one new entity (as kl_fa_rappel_bots.add does for its routs; the blocker has no model: no octree item).
"""
import collections, json, os, shutil, struct, sys
sys.path.insert(0, os.getcwd())
import kl_fa_bots as F
import kl_fa
import kl_prpjoin as J
import kl_fa_rappel_bots as RB

R_ = 'ROOT\\'
PRE = R_ + 'Locations/M09_A/M09A_Locations.zip\\Locations/M09_A/M09A_LOC_Inside.zip\\M09_A_Ins_Office_301\\SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00'
TIMER = R_ + 'Gameplay!010_FirstFight!RivalMercVan!Timer'
FORCE = R_ + 'Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo'
DONOR = ('F07', R_ + 'Gameplay!010_FirstFight!PF_Blocker')
NAME = 'KL_WindowNavBlock'
PARENT = R_ + 'KL_Rappel!'                  # kl_fa_rappel.py's top group: stands at the origin unturned (checked)
AT = (5884.0, 21022.0, -100.0)
HALF = (8.0, 40.0, 335.0)
HARD = 1.0e9


def check(folder, slot='F06', log=print, block=True, glass=True):
    B = F.Built(folder, slot); sc = B.sc; out = []
    def say(ok, s):
        out.append(('PASS' if ok else 'FAIL', s)); log('  %s  %s' % out[-1])
    k = sc.resolve(PRE)
    sa = [v for kk, _i, v in kl_fa.controllers(sc, 'ShotActivate') if kk == (k[0] if k else -1)]
    say(len(k) == 1 and len(sa) == 1 and ((sa[0][5] >= HARD and sa[0][6] >= HARD) if glass else (sa[0][5] < HARD and sa[0][6] < HARD)) and sa[0][10] == 'ForceTriggerShotActivate',
        'the intact window: ShotActivate fields 5 / 6 = %s / %s, forced by %r' % (sa[0][5], sa[0][6], sa[0][10]) if sa else 'the intact window: no ShotActivate')
    fo = [v for kk, _i, v in kl_fa.controllers(sc, 'AIDWrapper') if sc.path[kk] == FORCE]
    say(bool(fo) and fo[0][1] == 'ForceTriggerShotActivate' and any(p.lower() == PRE.lower() for p in fo[0][0]), 'the blast\'s AIDWrapper still forces it: %s' % (fo[0][:2] if fo else None))
    bl = sc.resolve(PARENT + '\\' + NAME)
    if not block:
        say(not bl, 'no path blocker (--no-block)')
        return out
    pb = [v for kk, _i, v in kl_fa.controllers(sc, 'PathBlocker') if bl and kk == bl[0]]
    if bl:
        at, box = B.at(bl[0]), B.box(bl[0])
        say(pb and pb[0][:2] == ['eUnblock', 'eBlocking'] and all(abs(at[i] - AT[i]) < 1 for i in range(3)) and all(abs(box[i] - HALF[i]) < 0.01 for i in range(3)),
            'the blocker %s: %s at (%.0f, %.0f, %.0f) half %s' % (NAME, pb[0][:2] if pb else None, at[0], at[1], at[2], box))
        inside = [p for p in ((5883.5, 21022.0, -100.0),) if B.in_box(bl[0], p)]
        say(bool(inside) and not B.in_box(bl[0], (5874.0, 21022.0, -100.0)) and not B.in_box(bl[0], (5896.0, 21020.0, -100.0)),
            'the box holds the middle of the sill strip (polygon 2133) and neither the room\'s (1912, x <= 5875) nor the balcony\'s (2134, x >= 5895) edge')
    else:
        say(False, 'no %s\\%s' % (PARENT, NAME))
    tl = [v for kk, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if sc.path[kk] == TIMER]
    say(bool(tl) and any(p.lower() == (PARENT + '\\' + NAME).lower() for p in tl[0][4]) and abs(tl[0][0] - 16.5) < 0.01,
        'the blast timer (%.1f s) names the blocker: %s' % (tl[0][0], tl[0][4][-2:]) if tl else 'no blast timer')
    return out


def add(src, dst, slot='F06', log=print, block=True, glass=True):
    import kl_gms, kl_graft
    import kl_octree as O
    import kl_fa_climb2 as C2
    B = F.Built(src, slot); sc = B.sc; zp = B.zp
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty' % dst)
    lines = []
    def say(s=''):
        log(s); lines.append(s)
    say('kl_rt_window add: %s -> %s' % (zp, dst))
    if sc.resolve(PARENT + '\\' + NAME):
        raise ValueError('the build has %s already' % NAME)
    for p_ in (PRE, TIMER, FORCE, PARENT):
        if len(sc.resolve(p_)) != 1:
            raise ValueError('not one node: %s' % p_)
    par = sc.resolve(PARENT)[0]
    Rm, T = B.fr[B.ents[par - 1]]
    if any(abs(T[i]) > 1e-3 for i in range(3)) or any(abs(Rm[i][j] - (1.0 if i == j else 0.0)) > 1e-5 for i in range(3) for j in range(3)):
        raise ValueError('%s does not stand at the origin unturned: %s %s' % (PARENT, T, Rm))
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0]:
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    M = F.Maker()
    if not block:
        return _glass_only(B, sc, zp, dst, slot, say, lines)
    nd = M.clone(*DONOR, name=NAME)
    if nd.links is not None or nd.model or nd.kids:
        raise ValueError('the donor has a list, a model or children')
    M.place(nd, AT)
    M.set(nd, None, {'ZBoxPrimitive[0]': HALF[0], 'ZBoxPrimitive[1]': HALF[1], 'ZBoxPrimitive[2]': HALF[2]})
    q, order = M.scene([nd])
    qt = q.tops()
    if len(qt) != 1:
        raise ValueError('the made scene has %d tops' % len(qt))
    Jn = RB.join_under(J, sc, {par: [(q, qt[0])]}, 'rt_window')
    # 1. the glass
    k = Jn.resolve(PRE)[0]
    i = next(i for i, (nm, _b) in enumerate(Jn.nodes[k]['ctrls']) if Jn.p.key(nm) == 'ShotActivate')
    was = {}
    def fg(us):
        was['g'] = (struct.unpack('<f', us[5][0][1])[0], struct.unpack('<f', us[6][0][1])[0])
        if us[5][0][0] != 0x0a or us[6][0][0] != 0x0a:
            raise ValueError('ShotActivate fields 5 / 6 are not floats')
        us[5] = [(0x0a, struct.pack('<f', HARD))]; us[6] = [(0x0a, struct.pack('<f', HARD))]
    if glass: kl_fa.edit(Jn, k, i, fg)
    else: was['g'] = (0.0, 0.0)
    if glass: say('  the intact window %s: ShotActivate fields 5 / 6 %.1f / %.1f -> %.0e / %.0e (no damage reaches its tests; the blast\'s forced swap is unchanged)' % (
        PRE.rsplit('\\', 1)[1], was['g'][0], was['g'][1], HARD, HARD))
    # 2. the blocker on the blast timer's list
    tm = Jn.resolve(TIMER)[0]
    ti = next(i for i, (nm, _b) in enumerate(Jn.nodes[tm]['ctrls']) if Jn.p.key(nm) == 'TriggerDelay2')
    def ft(us):
        have = [Jn.p.key(t) for t in us[4][1:]]
        was['t'] = have
        us[4] = kl_fa._refs(Jn, have + [PARENT + '\\' + NAME])
    kl_fa.edit(Jn, tm, ti, ft)
    say('  %s: its list (%d) + %s\\%s' % (TIMER, len(was['t']), PARENT, NAME))
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made = nxt, {}
    ents0 = list(A.entities())
    if ents0[par - 1].name.decode('latin1') != sc.names[par]:
        raise ValueError('the .gms entity of %s is not where the .prp has it' % sc.names[par])
    nxt = C2._write_ent(A, nd, ents0[par - 1], nxt, made)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(nm, new[nm]) for nm in B.order])
    for fx in os.listdir(B.folder):
        pth = os.path.join(B.folder, fx)
        if os.path.isfile(pth) and pth != zp:
            shutil.copyfile(pth, os.path.join(dst, fx))
    say('written %s: 1 entity added (REF id %d); members changed: %s; %d slot ids renumbered' % (out, ref0, ' '.join(changed), moved))
    for e in ('.ANM', '.fxc', '.WAV', '.prm', '.HVK'):
        if e in B.ext and new[B.ext[e]] != B.files[B.ext[e]]:
            raise ValueError('%s changed' % e)
    res = check(dst, slot, log=say, glass=glass)
    rep = collections.OrderedDict(source=B.folder, out=dst, members_changed=changed, check=[list(r) for r in res])
    with open(os.path.join(dst, 'rt_window.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    with open(os.path.join(dst, 'rt_window.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return rep


def _glass_only(B, sc, zp, dst, slot, say, lines):
    import kl_graft
    k = sc.resolve(PRE)[0]
    i = next(i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'ShotActivate')
    def fg(us):
        us[5] = [(0x0a, struct.pack('<f', HARD))]; us[6] = [(0x0a, struct.pack('<f', HARD))]
    kl_fa.edit(sc, k, i, fg)
    prp = sc.p.serialize()
    new = dict(B.files); new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(nm, new[nm]) for nm in B.order])
    for fx in os.listdir(B.folder):
        pth = os.path.join(B.folder, fx)
        if os.path.isfile(pth) and pth != zp:
            shutil.copyfile(pth, os.path.join(dst, fx))
    say('written %s: the glass only (--no-block), .prp changed' % out)
    res = check(dst, slot, log=say, block=False)
    rep = collections.OrderedDict(source=B.folder, out=dst, members_changed=['.prp'], check=[list(r) for r in res])
    with open(os.path.join(dst, 'rt_window.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return rep


def main():
    a = sys.argv[1:]
    slot = 'F06'
    if '--slot' in a:
        i = a.index('--slot'); slot = a[i + 1]; del a[i:i + 2]
    block = '--no-block' not in a
    glass = '--no-glass' not in a
    a = [x for x in a if x not in ('--no-block', '--no-glass')]
    if a and a[0] == 'add' and len(a) == 3:
        rep = add(a[1], a[2], slot, block=block, glass=glass)
        sys.exit(1 if any(r[0] != 'PASS' for r in rep['check']) else 0)
    if a and a[0] == 'check' and len(a) == 2:
        res = check(a[1], slot, block=block, glass=glass)
        sys.exit(1 if any(r[0] != 'PASS' for r in res) else 0)
    print(__doc__); sys.exit(2)


if __name__ == '__main__':
    main()
