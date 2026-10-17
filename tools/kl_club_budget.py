#!/usr/bin/env python3
"""
Last Call (DM05A), the BOTS' TIME BUDGET: let the AI heisters skip the gate waits that cost the most time so that
somebody reaches the exit box inside the 360 s round. OFFLINE; reads a finished build folder, writes a new one.
Nothing is installed or started. Data only: the .prp changes (one list value per wait node), no entity is added.

    python kl_club_budget.py budget <folder>                   the time budget of the plan, from the .prp itself
    python kl_club_budget.py build  <folder> <out> --skip-gates walkway,floor2,third [--round-s 360]
    python kl_club_budget.py check  <folder> <out>             only the allowed wait nodes differ, and only in field 0

WITHOUT --skip-gates `build` writes a byte-identical copy of the folder (proved by `check` and by md5 of the zip).

WHY (re/club_campaign.md 2026-10-18; owner 2026-10-17: the bots never reach the roof, veh1dc stayed 0 all round)
  Each gate of the bot plan ends in a TriggerActorsDead (squad step 03N_TriggerActorsDead_<gate>) that holds the
  squad until the named guards are dead. READ IN kl2.exe (this session, capstone, the same bytes as
  re/retomoto_bots_rooms_review.md):
    0x4afb80 (message 'AITrigger'): arms the node once and writes deadline = [[0xdd2640]+0x48] + 0x7800 into +0x44.
        0x7800 is an IMMEDIATE in the code: 30.0 s (1/1024 s ticks). It is NOT a level value, so the wait cannot be
        shortened by data - only removed.
    0x8def80 (per tick, session state 0x19): bl = 1; loops the list at +0x3c asking 0x5f4470 per entry (any entry
        that is not dead sets bl = 0); 0x8defcc 'jle' with a count of 0 skips the loop, so an EMPTY list leaves bl = 1;
        0x8df00b/0x8df010: fires when now > deadline OR bl != 0. So an EMPTY guard list fires on the first tick.
  The plan's own timetable (bots.txt): quickest crew at the seal hold 162 s, slowest 463 s, against a 360 s round. The
  walk is 40330 units (~134 s at 300 u/s) + loot 18 s + start delay 10 s = 162 s; seven gates at up to 30 s each add
  up to 210 s -> up to 372 s + the 10 s seal hold. So a crew that has to wait out every gate is over the round.
  THE GUESS HOLDS AS ARITHMETIC (the 30 s is fixed, the sum exceeds 360 s); that it is the only reason the live bots
  never reached the exit box is NOT proven (no live log with the stage times of every gate).

WHAT IS CHANGED (only with --skip-gates)
  Field 0 (the guard list) of the named gates' TriggerActorsDead, in every squad, becomes EMPTY: the squad goes on to
  the next step at once. The gate's DefendBehaviour hold and the 'wakes' lists (field 2) are untouched, so the guards
  of a skipped gate still wake as before; the bots just do not wait for them to die.
  Default gates to skip: walkway, floor2, third (the three that WAKE NOBODY per bots.txt, so no fight is cut short;
  worst case then 162 + 4*30 + 10 = 292 s, 68 s of slack).
GUESS: that the 360 s is the round length the bots race against (the HUD clock runs ~10 s ahead of the end timer,
  re/club_campaign.md AA step 7); that 300 u/s is the bots' walking speed (the plan's own figure); that a bot walking
  on past live guards of a skipped gate is not shot down before the next hold (the men that wake at a gate are the
  ones listed in its field 2, those still wake); that the empty list is accepted by the loader as a count of 0
  (the same token form kl_fa_bots writes for other empty lists; round-trip is checked here, the loader is not).
  NOT RUN IN THE GAME.
"""
import os, shutil, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_graft

GATES = ['walkway', 'floor2', 'floor1n', 'floor1s', 'stairs', 'lounge', 'third']   # the plan's order (bots.txt)
SKIP_DEFAULT = ['walkway', 'floor2', 'third']       # the gates that wake nobody
WAIT_S = 30.0               # 0x7800 ticks at 1/1024 s (kl2 0x4afbbd)
WALK_S = 134.0              # GUESS: 40330 units at 300 u/s (bots.txt)
LOOT_S, START_S, SEAL_S = 18.0, 10.0, 10.0
GUARD_LIST = 0              # ZTriggerActorsDead field 0: the actor groups it waits for


def gate_nodes(sc):
    """{gate: [node, ...]} over every squad: nodes named <squad>\\03N_TriggerActorsDead_<gate>."""
    out = {g: [] for g in GATES}
    for k, _i, _v in kl_fa.controllers(sc, 'TriggerActorsDead'):
        p = sc.path[k]
        leaf = p.split('\\')[-1]
        if '!Squad#' in p and '_TriggerActorsDead_' in leaf:
            g = leaf.split('_TriggerActorsDead_')[-1]
            if g in out:
                out[g].append(k)
    return out


def _vals(sc, k):
    for kk, _i, v in kl_fa.controllers(sc, 'TriggerActorsDead'):
        if kk == k:
            return v
    raise KeyError(sc.path[k])


def budget(folder, skip=(), round_s=360.0, slot='F01', log=print):
    B = F.Built(folder, slot)
    gn = gate_nodes(B.sc)
    waits = [g for g in GATES if gn[g] and g not in skip and _vals(B.sc, gn[g][0])[GUARD_LIST]]
    worst = WALK_S + LOOT_S + START_S + WAIT_S * len(waits) + SEAL_S
    log('gates found: %s' % ', '.join('%s x%d' % (g, len(gn[g])) for g in GATES))
    log('waiting gates: %d (%s); worst case %.0f s of %.0f s round, slack %.0f s'
        % (len(waits), ','.join(waits), worst, round_s, round_s - worst))
    return worst


def build(src, dst, skip=(), slot='F01', log=print):
    B = F.Built(src, slot)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    for g in skip:
        if g not in GATES:
            raise ValueError('unknown gate %s (have %s)' % (g, ','.join(GATES)))
    gn = gate_nodes(sc)
    changed = []
    for g in skip:
        if not gn[g]:
            raise ValueError('gate %s has no wait node in %s' % (g, src))
        for k in gn[g]:
            if not _vals(sc, k)[GUARD_LIST]:
                continue                                    # already empty
            kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'TriggerActorsDead'), lambda us: A.setv(sc, us, GUARD_LIST, []))
            changed.append(k)
    new = dict(B.files)
    if changed:
        prp = sc.p.serialize()
        import kl_prp
        back = kl_prp.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
            raise ValueError('the new .prp does not round-trip')
        new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    if changed:
        kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    else:
        shutil.copyfile(B.zp, os.path.join(dst, os.path.basename(B.zp)))   # byte-identical default
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'civs.')):
            shutil.copyfile(p, os.path.join(dst, f))
    if changed:
        sj = os.path.join(dst, 'steps.json')
        if os.path.isfile(sj):
            import kl_maps
            st = json.load(open(sj))
            st['budget'] = ['.prp']
            st['same'] = [e for e in st.get('same', []) if e != '.prp']
            st['final'] = kl_maps.member_ids(dst)
            with open(sj, 'w') as f:
                json.dump(st, f, indent=1)
        with open(os.path.join(dst, 'graft.txt'), 'a') as f:
            f.write('kl_club_budget: guard lists of %d wait node(s) emptied (gates %s); from %s\n'
                    % (len(changed), ','.join(skip), B.folder))
    log('written %s: %d wait node(s) emptied (%s)' % (dst, len(changed), ','.join(skip) or 'none'))
    return dst


def diff(src, dst, skip=(), slot='F01', log=print):
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
        return bad
    ok = {k for g in skip for k in gate_nodes(lb)[g]}
    for k in range(len(la.nodes)):
        if (la.nodes[k]['props'], la.nodes[k]['ctrls']) != (lb.nodes[k]['props'], lb.nodes[k]['ctrls']):
            if k not in ok:
                bad.append('node %d (%s) differs' % (k, la.path[k]))
            else:
                v = _vals(lb, k)
                w = _vals(la, k)
                if v[GUARD_LIST] or v[1:] != w[1:]:
                    bad.append('node %d (%s): more than field 0 changed' % (k, la.path[k]))
    if not skip and a.files != b.files:
        bad.append('no flag, but the members differ')
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
    skip = opt('--skip-gates', '', str)
    skip = [x for x in skip.split(',') if x]
    rs = opt('--round-s', 360.0, float)
    if skip == ['default']:
        skip = list(SKIP_DEFAULT)
    if cmd == 'budget':
        budget(a[0], skip, rs); return 0
    if cmd == 'build':
        build(a[0], a[1], skip)
        bad = diff(a[0], a[1], skip)
        for x in bad:
            print('FAIL', x)
        budget(a[1], (), rs)
        return 1 if bad else 0
    if cmd == 'check':
        bad = diff(a[0], a[1], skip)
        for x in bad:
            print('FAIL', x)
        print('check: %d FAIL' % len(bad)); return 1 if bad else 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
