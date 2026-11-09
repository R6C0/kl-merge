#!/usr/bin/env python3
"""Self-test of tools/kl_bench_1109.py item_checks() on SYNTHETIC host logs (no game, no game files).
1. An empty log must FAIL for every kit (no vacuous PASS).
2. A hand-made good log must have 0 FAIL for every kit.
3. Each mutation of a good log (one fact wrong or missing) must FAIL.
Exit 0 only when all pass (kl_tests.py picks tools/*_test.py up by name)."""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_bench_1109 as M

PASS = FAIL = 0


def ok(cond, text):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print('  FAIL', text)


class Log:
    def __init__(s, k):
        s.k, s.t, s.lines = k, 3600.0 * 3, []
        s.say('BENCH1109 %s host level loaded' % k)

    def stamp(s):
        t = s.t
        return '%02d:%02d:%06.3f' % (int(t // 3600), int(t // 60 % 60), t % 60)

    def raw(s, text, dt=0.1):
        s.t += dt
        s.lines.append('%s %s' % (s.stamp(), text))

    def say(s, text, dt=0.1):
        s.raw('script %d: %s' % (len(s.lines) + 1, text), dt)

    def ent(s, name, pos, hidden=False, slot=1, dt=0.05):
        s.raw("script %d: ents #1 slot %d obj 12345678 name '%s' class ZLNKOBJ ref?(+0x30) 5 en?(!bit10 of +0x3c) %s (flags %08x) pos (%.1f, %.1f, %.1f)"
              % (len(s.lines) + 1, slot, name, '0' if hidden else '1', 0x400 if hidden else 0, pos[0], pos[1], pos[2]), dt)

    def wait(s, secs):
        s.t += secs

    def done(s):
        s.say('BENCH1109 %s host segment done' % s.k)
        return s.lines


def hasta(mut=None):
    g = Log('HASTA1109')
    for i in range(14):
        late = i >= 7
        g.ent('OYCHECK_BEFORE01', (25991.7, 0, 14117.8), hidden=late)
        g.ent('BarricadeB_01', (26409, 800, 14031), hidden=late and mut != 'barricade')
        g.ent('BarricadeB_02', (26400, 800, 14000), hidden=late)
        g.ent('Roadblock_01', (26560.7, 0, 13426.4), hidden=late and mut != 'roadblock')
        g.ent('Roadblock_01', (13721.6, 1050, 4735.6), slot=2)      # the map's second Roadblock_01, far from the wall: never hides, must be ignored
        if mut != 'broken':
            g.ent('Broken01', (26409, 800, 14031), hidden=not late)
        g.ent('OYCHECK_AFTER01', (25937.3, 0, 14117.8), hidden=not late)
        g.say('BENCH1109 hasta sample %d' % i)
        g.wait(9)
    return g.done()


def van(k, mut=None):
    stop = M.STOP_DM01B if k == 'DM01B_1109' else (-4000, 10000)
    d = 1 if k == 'DM01B_1109' else -1                              # DM01B leaves east, DM07 reverses west
    g = Log(k)
    if k == 'DM07_1109':
        for n in ('Chainlink_Fence_4m_01', 'Chainlink_Fence_4m_11', 'Chainlink_Fence_4m_05'):
            g.ent(n, (-9000, 0, 10000), hidden=(n[-2:] != '05' and mut != 'fence'))
    first = (stop[0] - d * 8000 if mut != 'east' else stop[0] + 6000, 0, stop[1] if k == 'DM01B_1109' else 10000)
    for i in range(6):
        g.ent('V_Van_Reflection', (-449, -60000, 0))                       # the map's reflection group: must be ignored
        g.ent('V_Van', first)
        g.wait(5)
    g.ent('V_Van', (stop[0], 0, stop[1]) if mut != 'mixrow' else (stop[0], 0, 0))
    if mut == 'mixrow':
        g.ent('V_Van', (stop[0] + 9000, 0, stop[1]), dt=0.02)
    if mut != 'nostate3':
        g.say('BENCH1109 van at state 3', 0.2)
    g.wait(8)
    if mut != 'nostate5':
        g.say('BENCH1109 van at state 5 (drives out)')
    for i in range(10):
        g.wait(1)
        if mut != 'nolate':
            g.ent('V_Van', (stop[0] + d * (600 + 900 * i) if mut not in ('stuck', 'pop') else stop[0] if mut == 'stuck' or i < 5 else -8000, 0, stop[1]))
    if k == 'DM01B_1109' and mut not in ('stuck', 'pop', 'nolate'):
        g.ent('V_Van', (17365, 0, 31663))                                    # reaches the END pocket, then resets to START: not a pop
        g.wait(1)
        g.ent('V_Van', (M.POCKETS[k][0][0], 0, M.POCKETS[k][0][1]))
    if mut != 'nostate7':
        g.say('BENCH1109 van at state 7 (leaving)')
    for i in range(4):
        g.wait(3)
        g.ent('V_Van', (first[0], 0, first[2]))                             # reset to the start pocket after 7: not a pop
    if k == 'DM07_1109':
        g.say('goto (-1800, 10400) %s in 3000 ms: at (-2100, 550, 10400) heading 90' % ('reached' if mut != 'nocontrol' else 'NOT reached'))
        g.say('goto (-6000, 10400) %s in 15000 ms: at (-4300, 550, 10400) heading 270' % ('NOT reached' if mut != 'walkedout' else 'reached'))
        if mut != 'nopos':
            g.say('pos dm07-after-walk: me #0 (%d, 550, 10400) heading 270' % (-4300 if mut != 'farpos' else -5900))
    return g.done()


def gate(mut=None):
    g = Log('DM07GATE_1109')
    for n in ('Chainlink_Fence_4m_01', 'Chainlink_Fence_4m_11', 'Chainlink_Fence_4m_02'):
        g.ent(n, (-4580, 470, 10000), hidden=(n[-2:] != '02' and mut != 'fence'))
    for lbl, st in M.GATE_WALKS:
        xs = [st[0]] + [max(x, -4560) if lbl != 'gateH' else x for x in M.GATE_XS]
        if mut == 'frozen' and lbl == 'gateB':
            xs = [st[0]] * len(xs)
        if mut in ('deadbefore', 'respawn') and lbl == 'gateA':
            # run 2: died 2 s before gateA-0, A and B then ran on the corpse
            g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
            if mut == 'respawn':
                g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 1 deaths 1 -> lives 2 (drawn)")
        for i, x in enumerate(xs):
            if mut == 'nopos' and lbl == 'gateB' and i == 3:
                continue
            g.say('pos %s-%d: me #0 (%d, 410, %d) heading 270' % (lbl, i, x, st[2]))
            if mut == 'dead' and lbl == 'gateA' and i == 2:
                g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
    return g.done()


def unhide(mut=None):
    """DM07UNHIDE_1109: 4m_01 un-hidden, 4m_11 hidden, 4m_02 visible; H then A. Default = H THROUGH (the gap is the leak), A BLOCKED.
    mut: hblock (H stops at the fence), hfrozen (H never leaves the tele point), hdead (died in H), ahrough (A walks through), hidden01 (4m_01 still hidden), nopos"""
    g = Log('DM07UNHIDE_1109')
    for n in ('Chainlink_Fence_4m_01', 'Chainlink_Fence_4m_11', 'Chainlink_Fence_4m_02'):
        g.ent(n, (-4580, 470, 10000), hidden=(n[-2:] == '11' or (n[-2:] == '01' and mut == 'hidden01')))
    for lbl, st in M.GATE_WALKS_UNHIDE:
        through = (lbl == 'gateH' and mut not in ('hblock', 'hdead')) or (lbl == 'gateA' and mut == 'athrough')
        xs = [st[0]] + [x if through else max(x, -4560) for x in M.GATE_XS]
        if mut == 'hfrozen' and lbl == 'gateH':
            xs = [st[0]] * len(xs)
        for i, x in enumerate(xs):
            if mut == 'nopos' and lbl == 'gateA' and i == 3:
                continue
            g.say('pos %s-%d: me #0 (%d, 410, %d) heading 270' % (lbl, i, x, st[2]))
            if mut == 'hdead' and lbl == 'gateH' and i == 2:
                g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
    return g.done()


def sink(mut=None):
    """DM07SINK_1109: four crossings at the sunk slabs, then the DM07 van round. Default = all BLOCKED (walk up to x -4560), van fine.
    mut: through11a (sink11a walks through), frozen10 (sink10 never leaves the tele point), novan (no van rows)"""
    g = Log('DM07SINK_1109')
    g.t -= 200                                                       # the crossings come before the van log below
    for lbl, st in M.GATE_WALKS_SINK:
        through = mut == 'through11a' and lbl == 'sink11a'
        xs = [st[0]] + [x if through else max(x, -4560) for x in M.GATE_XS]
        if mut == 'frozen10' and lbl == 'sink10':
            xs = [st[0]] * len(xs)
        for i, x in enumerate(xs):
            g.say('pos %s-%d: me #0 (%d, 410, %d) heading 270' % (lbl, i, x, st[2]))
    return g.lines + (van('DM07SINK_1109') if mut != 'novan' else [])


def curtain(mut=None):
    """DM07CURTAIN_1109: controls curA / curB walk up to the fence (BLOCKED), the four gate crossings die in the curtain box (KILLED), then the van round.
    mut: through (cur11a walks through alive), inside (cur11b stops alive inside the box), frozen (cur01 never moves), allvoid (every gate walk frozen),
    policeeast (cur11c dies east of the fence), latedeath (cur11a passes the box, dies at -5000), deadbefore (dead before cur01, no respawn), controlthrough (curA walks through),
    nosample (cur11b-3 missing), novan, nostate7 (van never leaves)"""
    g = Log('DM07CURTAIN_1109')
    g.t -= 400                                                       # the crossings come before the van log below
    kill = lambda: g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
    for lbl, st, exp in M.CURTAIN_WALKS:
        if mut == 'deadbefore' and lbl == 'cur01':
            kill()
        if exp == 'BLOCKED':
            xs = [max(x, -4549) for x in M.GATE_XS] if not (mut == 'controlthrough' and lbl == 'curA') else list(M.GATE_XS)
            dies = None
        else:
            xs = [-4400, -4520, -4600, -4600, -4600]                 # a corpse in the box (-4720..-4560)
            dies = 2
            if mut == 'through' and lbl == 'cur11a':
                xs, dies = list(M.GATE_XS), None
            if mut == 'inside' and lbl == 'cur11b':
                xs, dies = [-4400, -4520, -4620, -4620, -4620], None
            if (mut == 'frozen' and lbl == 'cur01') or mut == 'allvoid':
                xs, dies = [st[0] + 150] * 5, None
            if mut == 'policeeast' and lbl == 'cur11c':
                xs, dies = [-4300, -4300, -4300, -4300, -4300], 1
            if mut == 'latedeath' and lbl == 'cur11a':
                xs, dies = list(M.GATE_XS), 4
        g.say('pos %s-t: me #0 (%d, 410, %d) heading 270' % (lbl, st[0] + 60, st[2]))
        g.say('pos %s-s: me #0 (%d, 410, %d) heading 90' % (lbl, st[0] + 150, st[2]))
        for i, x in enumerate(xs):
            if mut == 'nosample' and lbl == 'cur11b' and i == 2:
                continue
            g.say('pos %s-%d: me #0 (%d, 410, %d) heading 270' % (lbl, i + 1, x, st[2]))
            if dies == i + 1:
                kill()
        g.say('BENCH1109 curtain %s done' % lbl)
        g.wait(12)                                                  # a real walk is ~20 s: the next walk's own death must not fall in this one's window
        if exp == 'KILL' and mut != 'deadbefore':
            g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 1 deaths 1 -> lives 2 (drawn)", 6)   # back as police after the 8 s wait
    return g.lines + (van('DM07CURTAIN_1109', 'nostate7' if mut == 'nostate7' else None) if mut != 'novan' else [])


def doors(k, mut=None):
    dd = [dict(host=176, name='x', hinge=[-3708, 300, -3217], front=[-3772, 300, -3125], back=[-3767, 300, -3316])]
    if k == 'DM02_1109':
        dd.append(dict(host=2, name='y', hinge=[-1440, 500, 1700], front=[-1440, 500, 1830], back=[-1440, 500, 1570]))
    if k == 'DOORS_1109_DM01':
        dd = [dict(host=957, name='x', hinge=[1918, 2, 22042], front=None, back=[2030, 2, 22068]), dict(host=2569, name='y', hinge=[2479, 60, 19851], front=[2369, 60, 19872], back=None)]
    g = Log(k)
    if k == 'DM03_1109':
        for i in range(6):
            g.ent('ArrivingCops_Squad_02_Cop', (0 + 400 * i, 0, 0) if mut != 'nomove' else (0, 0, 0))
            g.ent('ArrivingCops_Car_01', (0 + 900 * i, 0, 0))
            if mut != 'nopolice':
                g.ent('Police_Officer_01', (50, 0, 50))
            g.raw('klbrain: cop->bot factor 5 s: %d cop hits on bots' % (0 if mut == 'nohits' else 3))
            g.wait(15)
        g.raw('botfill: round census: 44 ZFFActor')
    for i, d in enumerate(dd[:1] if k == 'DM03_1109' else dd):
        h = d['hinge']
        lbl = M.door_lbl(k, i)
        if mut != 'noleaf':
            g.ent('KL_Door_Leaf', (h[0] + 5, h[1] + 10, h[2] - 5))
        g.say('BENCH1109 %s door %s: before' % (lbl, d['host']))
        ctrl = lambda when, v: g.raw('script 73: peek 00dd265c+ac4+5c = %08x (at 528f899c)  %s-%s-ctrl7-state' % (v, lbl, when))
        ctrl('stand', 1)
        if mut != 'nokick':
            g.say('BENCH1109 %s door %s: kicked (E x2)' % (lbl, d['host']))
        if mut in ('nostate', 'deadkick'):
            if mut == 'deadkick':
                g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
            ctrl('kicked', 1)
            ctrl('kicked2', 1)
        elif mut == 'second':
            ctrl('kicked', 1)
            ctrl('kicked2', 3)
        else:
            ctrl('kicked', 3)
            ctrl('kicked2', 3)
        if mut != 'noleaf':
            g.ent('KL_Door_Leaf', (h[0] + 5, h[1] + 10, h[2] - 5) if mut == 'static' else (h[0] + 60, h[1] + 10, h[2] - 5))
        b = d['back'] if d['front'] and d['back'] else None
        if b and mut != 'nogoto':
            g.say('goto (%d, %d) reached in 3000 ms: at (%d, %d, %d) heading 90' % (b[0], b[2], b[0], b[1], b[2]))
    return g.done(), dd


def log_for(k, mut=None):
    if k == 'HASTA1109':
        return hasta(mut), [], None
    if k in ('DM01B_1109', 'DM07_1109'):
        return van(k, mut), [], dict(control=[-1800, 10400], length=2100.0)
    if k == 'DM07GATE_1109':
        return gate(mut), [], None
    if k == 'DM07UNHIDE_1109':
        return unhide(mut), [], None
    if k == 'DM07SINK_1109':
        return sink(mut), [], None
    if k == 'DM07CURTAIN_1109':
        return curtain(mut), [], None
    a, dd = doors(k, mut)
    return a, dd, None


def fails(k, mut=None, empty=False):
    a, dd, ctrl = log_for(k, mut)
    r, _ = M.item_checks(k, [] if empty else a, dd, ctrl)
    return [x for x in r if x[0] == 'FAIL']


def main():
    for k in M.ORDER:
        ok(fails(k, empty=True), '%s: empty log must FAIL' % k)
        a, dd, ctrl = log_for(k)
        r, _ = M.item_checks(k, a, dd, ctrl)
        ok(len(r) >= 2 and not [x for x in r if x[0] == 'FAIL'], '%s: good synthetic log must have 0 FAIL, got %s' % (k, [x[1:] for x in r if x[0] == 'FAIL']))
        ok(M.item_checks(k, [], [], None)[0] and all(x[0] != 'PASS' or 'door' not in x[1] for x in M.item_checks(k, [], [], None)[0]), '%s: empty log, no door PASS' % k)
    muts = {'HASTA1109': ['barricade', 'broken', 'roadblock'],
            'DM01B_1109': ['east', 'nostate3', 'nostate5', 'nolate', 'stuck', 'mixrow', 'pop'],
            'DM07_1109': ['fence', 'nolate', 'nocontrol', 'walkedout', 'nopos', 'farpos', 'nostate3', 'stuck'],
            'DM07GATE_1109': ['fence', 'nopos'],
            'DM07UNHIDE_1109': ['hidden01', 'nopos'],
            'DM07CURTAIN_1109': ['through', 'inside', 'allvoid', 'latedeath', 'controlthrough', 'nosample', 'novan', 'nostate7'],
            'DM03_1109': ['nohits', 'nopolice','noleaf', 'nokick', 'static', 'nogoto'],
            'DM02_1109': ['noleaf', 'nokick', 'nogoto'],
            'DOORS_1109_DM01': ['noleaf', 'nokick'],
            'DOORS_1109_DM03A': ['noleaf', 'nokick', 'nogoto']}
    for k, ms in muts.items():
        for m in ms:
            ok(fails(k, m), '%s: mutation %r must FAIL' % (k, m))
    # DM03A door is one-sided in the real kit: a hand-made one-sided door still needs the kick and the leaf samples
    # the 'changed' rule is FAIL on DM03 only: a static leaf on DM02 is a WARN
    ok(not fails('DM02_1109', 'static'), 'DM02: a static leaf is a WARN, not a FAIL')
    # the engine's kick answer: controller 1 -> 3 on either attempt, FAIL when it stays 1, WARN when the host died first
    for k in ('DOORS_1109_DM01', 'DOORS_1109_DM01R', 'DOORS_1109_DM03A'):
        ok(any('1 -> 3' in x[1] for x in fails(k, 'nostate')), '%s: a controller that stays 1 FAILs' % k)
        ok(not fails(k, 'second'), '%s: a kick on the second try passes' % k)
        ok(not any('1 -> 3' in x[1] for x in fails(k, 'deadkick')), '%s: a host death before the kick is a WARN' % k)
    # cop actors are not in 'ents': unmoved squad/trigger rows are a WARN on DM03, the cop hits decide
    ok(not fails('DM03_1109', 'nomove'), 'DM03: unmoved ArrivingCops rows are a WARN, not a FAIL')
    # a control goto with the blocked goto missing (walk never ran) must FAIL
    a, dd, ctrl = log_for('DM07_1109')
    a2 = [l for l in a if 'goto (-6000' not in l]
    ok([x for x in M.item_checks('DM07_1109', a2, dd, ctrl)[0] if x[0] == 'FAIL'], 'DM07: missing blocked goto must FAIL')
    # the gate verdict reads the crossings: visible panels blocked, the hidden one passed
    inf = M.item_checks('DM07GATE_1109', gate(), [], None)[1]
    ok(any('A (visible 4m_02) BLOCKED, B (visible 4m_03) BLOCKED, H (hidden 4m_01) THROUGH' in x for x in inf), 'DM07GATE: verdict line reads the crossings %s' % [x for x in inf if 'verdict' in x])
    # a host death inside a crossing voids its BLOCKED (WARN, verdict DEAD)
    r, inf = M.item_checks('DM07GATE_1109', gate('dead'), [], None)
    ok(any('A (visible 4m_02) DEAD, B (visible 4m_03) DEAD' in x for x in inf) and any(x[0] == 'WARN' and 'death' in x[1] for x in r), 'DM07GATE: a death in crossing A reads DEAD + WARN')
    # run 2: a death BEFORE crossing A (no respawn) voids A and B; a kind-1 row in between keeps them
    inf = M.item_checks('DM07GATE_1109', gate('deadbefore'), [], None)[1]
    ok(any('A (visible 4m_02) DEAD, B (visible 4m_03) DEAD, H (hidden 4m_01) THROUGH' in x for x in inf), 'DM07GATE: a death before A voids A and B')
    inf = M.item_checks('DM07GATE_1109', gate('respawn'), [], None)[1]
    ok(any('A (visible 4m_02) BLOCKED, B (visible 4m_03) BLOCKED' in x for x in inf), 'DM07GATE: a respawn before A keeps the verdicts')
    # never leaving the tele point is FROZEN, not BLOCKED
    r, inf = M.item_checks('DM07GATE_1109', gate('frozen'), [], None)
    ok(any('B (visible 4m_03) FROZEN' in x for x in inf) and any(x[0] == 'WARN' and 'freeze' in x[1] for x in r), 'DM07GATE: a frozen B reads FROZEN + WARN')
    # DM07UNHIDE_1109: both verdicts of the toggle test, a frozen and a dead H, a non-discriminating control
    # the sink fix: any crossing THROUGH FAILs; a freeze is a WARN (no verdict), not a pass of the blocker check's spirit but not a FAIL
    ok(any('sink11a' in x[1] for x in fails('DM07SINK_1109', 'through11a')), 'DM07SINK: a crossing that walks through FAILs')
    ok(not fails('DM07SINK_1109', 'frozen10'), 'DM07SINK: a frozen crossing is a WARN, not a FAIL')
    ok(any('van' in x[1] for x in fails('DM07SINK_1109', 'novan')), 'DM07SINK: no van rows FAIL')
    ok(any('sink verdict' in i_ and 'sink11a BLOCKED' in i_ for i_ in M.item_checks('DM07SINK_1109', sink(), [], None)[1]), 'DM07SINK: the verdict line names every crossing')
    inf = M.item_checks('DM07UNHIDE_1109', unhide(), [], None)[1]
    ok(any('unhide verdict: H (4m_01 UN-hidden) THROUGH, A (visible 4m_02) BLOCKED' in x for x in inf), 'UNHIDE: H THROUGH reads the gap verdict %s' % [x for x in inf if 'verdict' in x])
    r, inf = M.item_checks('DM07UNHIDE_1109', unhide('hblock'), [], None)
    ok(any('unhide verdict: H (4m_01 UN-hidden) BLOCKED, A (visible 4m_02) BLOCKED' in x for x in inf) and not [x for x in r if x[0] != 'PASS'], 'UNHIDE: H BLOCKED reads the collision verdict, no WARN/FAIL %s' % [x for x in r if x[0] != 'PASS'])
    r, inf = M.item_checks('DM07UNHIDE_1109', unhide('hfrozen'), [], None)
    ok(any('H (4m_01 UN-hidden) FROZEN' in x for x in inf) and any(x[0] == 'WARN' and 'freeze' in x[1] for x in r), 'UNHIDE: a frozen H reads FROZEN + WARN, never BLOCKED')
    r, inf = M.item_checks('DM07UNHIDE_1109', unhide('hdead'), [], None)
    ok(any('H (4m_01 UN-hidden) DEAD' in x for x in inf) and any(x[0] == 'WARN' and 'death' in x[1] for x in r), 'UNHIDE: a death in H reads DEAD + WARN')
    r, inf = M.item_checks('DM07UNHIDE_1109', unhide('athrough'), [], None)
    ok(any(x[0] == 'WARN' and 'control A' in x[1] for x in r) and not [x for x in r if x[0] == 'FAIL'], 'UNHIDE: A THROUGH = WARN (control does not discriminate)')
    ok(not any('gateS' in l or 'gateB' in l for l in M.gate_seg('host', M.GATE_WALKS_UNHIDE, south=False))
       and any('gateH' in l for l in M.gate_seg('host', M.GATE_WALKS_UNHIDE, south=False)) and any('gateS' in l for l in M.gate_seg('host')), 'UNHIDE script: H + A only, no south walk; the GATE kit keeps all of it')
    ok(M.K['DM07UNHIDE_1109']['stage'] and M.K['DM07UNHIDE_1109']['tag'] == '.before-dm07unhide1109' and M.K['DM07GATE_1109']['stage'] is None, 'UNHIDE is a stage kit (stage+tag kept by the defaults loop), GATE is not')
    # DM07CURTAIN_1109: KILLED / BLOCKED pass, alive west of the fence FAILs, void walks are WARN, KeepAlive is off, van state 7 is required
    r, inf = M.item_checks('DM07CURTAIN_1109', curtain(), [], None)
    ok(not [x for x in r if x[0] != 'PASS'] and any('curtain verdict: curA BLOCKED, curB BLOCKED, cur01 KILLED, cur11a KILLED, cur11b KILLED, cur11c KILLED' in i_ for i_ in inf),
       'CURTAIN: good log = all PASS, verdict line %s %s' % ([x for x in r if x[0] != 'PASS'], [i_ for i_ in inf if 'verdict' in i_]))
    ok(any('cur11a' in x[1] for x in fails('DM07CURTAIN_1109', 'through')), 'CURTAIN: a gate crossing alive west of -4700 FAILs')
    ok(any('cur11b' in x[1] and 'never alive' in x[1] for x in fails('DM07CURTAIN_1109', 'inside')), 'CURTAIN: alive inside the box (not killed) FAILs')
    ok(any('cur11a' in x[1] for x in fails('DM07CURTAIN_1109', 'latedeath')), 'CURTAIN: a death only after passing the box is THROUGH, FAIL')
    ok(any('curA' in x[1] for x in fails('DM07CURTAIN_1109', 'controlthrough')), 'CURTAIN: a control that walks through FAILs')
    ok(any('van reaches state 7' in x[1] for x in fails('DM07CURTAIN_1109', 'nostate7')), 'CURTAIN: no state 7 FAILs (driver killed?)')
    r, inf = M.item_checks('DM07CURTAIN_1109', curtain('frozen'), [], None)
    ok(not [x for x in r if x[0] == 'FAIL'] and any(x[0] == 'WARN' and 'cur01' in x[1] for x in r) and any('cur01 (z 10334, expect KILL): VOID' in i_ for i_ in inf), 'CURTAIN: a frozen walk is VOID = WARN, not FAIL')
    ok(any('at least 2' in x[1] for x in fails('DM07CURTAIN_1109', 'allvoid')), 'CURTAIN: every gate walk VOID FAILs (no vacuous PASS)')
    r, inf = M.item_checks('DM07CURTAIN_1109', curtain('policeeast'), [], None)
    ok(not [x for x in r if x[0] == 'FAIL'] and any('cur11c (z 10700, expect KILL): DIED-EAST' in i_ for i_ in inf), 'CURTAIN: a death east of the fence is DIED-EAST, WARN')
    r, inf = M.item_checks('DM07CURTAIN_1109', curtain('deadbefore'), [], None)
    ok(any('cur01 (z 10334, expect KILL): DEAD-BEFORE' in i_ for i_ in inf), 'CURTAIN: a corpse at the tele is DEAD-BEFORE')
    ok(any('crossing sampled' in x[1] for x in fails('DM07CURTAIN_1109', 'nosample')), 'CURTAIN: a missing pos line FAILs')
    sc = M.curtain_seg('host')
    ok(sum(1 for l in sc if l.startswith('tele')) == 6 and all(sc[i + 1] == 'wait 2000' and sc[i + 2].startswith('pos ') and sc[i + 3].startswith('goto -3850') for i, l in enumerate(sc) if l.startswith('tele')),
       'CURTAIN script: each walk = tele, wait, pos, settle goto 150 east')
    ok(M.K['DM07CURTAIN_1109']['keepalive'] == 0 and M.K['DM07SINK_1109']['keepalive'] == 1 and M.K['DM07CURTAIN_1109']['tag'] == '.before-dm07curtain1109' and 'DM07CURTAIN_1109' in M.ORDER, 'CURTAIN kit: stage + tag + keepalive 0 only here, in ORDER')
    ok([c[0] for c in M.CURTAIN_WALKS][:2] == ['curA', 'curB'] and [c[1][2] for c in M.CURTAIN_WALKS] == [9800, 10850, 10334, 10420, 10600, 10700], 'CURTAIN walks: controls first, z 9800 10850 10334 10420 10600 10700')
    # pos parsed by name: the label decides, not the position in the line
    ok(M.pos_of(['01:00:00.000 script 3: pos x-label: me #0 (-4300, 550, 10400) heading 12'], 'x-label') == (-4300, 550, 10400), 'pos_of parses the named x')
    ok(M.pos_of(['01:00:00.000 script 3: pos other: me #0 (1, 2, 3) heading 12'], 'x-label') is None, 'pos_of: other label is None')
    print('RESULT: kl_bench_1109_test %s (%d pass, %d fail)' % ('PASS' if not FAIL else 'FAIL', PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
