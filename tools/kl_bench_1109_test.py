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


def plane(k='DM07PLANE_1109', mut=None):
    """DM07PLANE*_1109: controls plA (BLOCKED at the visible fence, x -4549) and plF (free east), ten gate crossings and two crouched ones that stop at the plane (BLOCKED), then
    the van round. mut: through (pl10334 walks out west), throughcrouch (plC10394 walks out), killed (pl10420 passes, then dies west), frozen (pl9995 never moves),
    freestuck (plF never moves), controlthrough (plA walks through), diedeast (pl10600 dies at x -4300), allvoid (every gate walk frozen), deadbefore (corpse before pl9995),
    nosample (pl10700-3 missing), unhidden (panel 4m_11 visible), novan, nostate7"""
    g = Log(k)
    g.t -= 500                                                       # the crossings come before the van log below
    for n in ('Chainlink_Fence_4m_01', 'Chainlink_Fence_4m_11'):
        g.ent(n, (-4579, 471, 10200), hidden=not (mut == 'unhidden' and n.endswith('11')))
    kill = lambda: g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 3 deaths 1 -> lives 2 (drawn)")
    for lbl, st, kind in M.PLANE_WALKS:
        if mut == 'deadbefore' and lbl == 'pl9995':
            kill()
        dies = None
        if kind == 'FREE':
            xs = [st[0] + 150 + 200 * (i + 1) for i in range(5)] if mut != 'freestuck' else [st[0] + 150] * 5
        elif kind == 'CTRL':
            xs = [max(x, -4549) for x in M.GATE_XS] if mut != 'controlthrough' else list(M.GATE_XS)
        else:
            xs = [max(x, -4545) for x in M.GATE_XS]                  # the capsule stops east of the plane (x -4578)
            if (mut == 'through' and lbl == 'pl10334') or (mut == 'throughcrouch' and lbl == 'plC10394'):
                xs = list(M.GATE_XS)
            if mut == 'killed' and lbl == 'pl10420':
                xs, dies = list(M.GATE_XS), 4
            if (mut == 'frozen' and lbl == 'pl9995') or mut == 'allvoid':
                xs = [st[0] + 150] * 5
            if mut == 'diedeast' and lbl == 'pl10600':
                xs, dies = [-4300] * 5, 1
        g.say('pos %s-t: me #0 (%d, 410, %d) heading 270' % (lbl, st[0] + 60, st[2]))
        g.say('pos %s-s: me #0 (%d, 410, %d) heading 90' % (lbl, st[0] + 150, st[2]))
        for i, x in enumerate(xs):
            if mut == 'nosample' and lbl == 'pl10700' and i == 2:
                continue
            g.say('pos %s-%d: me #0 (%d, 410, %d) heading 270' % (lbl, i + 1, x, st[2]))
            if dies == i + 1:
                kill()
        g.say('BENCH1109 plane %s done' % lbl)
        g.wait(4)
        if dies:
            g.raw("hud: ONLINE skulls state: row 0 'R5 J.C.' kind 1 deaths 1 -> lives 2 (drawn)", 6)
    return g.lines + (van(k, 'nostate7' if mut == 'nostate7' else None) if mut != 'novan' else [])


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


def dd10gate(mut=None):
    """DD10GATE_1109 host log. mut: through (walks out west), stuck (never moves, control too), dead (a death row in every walk)"""
    xs, cx = {'through': ((8050, 7950, 7850, 7700, 7500), 8400), 'stuck': ((8150,) * 5, 8160)}.get(mut, ((8100, 8060, 8058, 8058, 8058), 8400))
    a, t = ['01:00:00.000 BENCH1109 DD10GATE_1109 host level loaded', '01:00:00.500 BENCH1109 dd10gate van parked'], 1
    for lbl, st in M.DD10_GATE_WALKS:
        for n, x in [('t', 8150)] + [(str(i + 1), x) for i, x in enumerate(xs)] + [('ct', 8150), ('c', cx)]:
            a.append('01:00:%06.3f script 3: pos %s-%s: me #0 (%d, 60, %d) heading 90' % (t, lbl, n, x, st[2]))
            t += 1
            if mut == 'dead' and n == '2':
                a.append('01:00:%06.3f hud: ONLINE skulls state: row 0 kind 3 deaths 1' % (t - 0.5))
    return a + ['01:00:59.000 BENCH1109 DD10GATE_1109 host segment done']


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
    if k in M.PLANE_KITS:
        return plane(k, mut), [], None
    if k == 'DD10GATE_1109':
        return dd10gate(mut), [], None
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
            'DM07PLANE_1109': ['through', 'killed', 'nosample', 'novan', 'nostate7', 'unhidden'],
            'DM07PLANE72_1109': ['through', 'nostate7'],
            'DD10GATE_1109': ['through', 'stuck'],
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
    # DM07PLANE*_1109: BLOCKED passes, alive west of the plane FAILs (also a crouched one, also dead-after-passing), VOID / DIED are WARN, the free path must PASS, van state 7 required
    for pk_ in M.PLANE_KITS:
        r, inf = M.item_checks(pk_, plane(pk_), [], None)
        ok(not [x for x in r if x[0] != 'PASS'] and any('plane verdict: plA BLOCKED, plF PASSED, pl9995 BLOCKED' in i_ and 'plC10790 BLOCKED' in i_ for i_ in inf),
           '%s: good log = all PASS, verdict line %s %s' % (pk_, [x for x in r if x[0] != 'PASS'], [i_ for i_ in inf if 'verdict' in i_]))
    K_ = 'DM07PLANE_1109'
    ok(any('pl10334' in x[1] for x in fails(K_, 'through')), 'PLANE: a gate crossing alive west of -4600 FAILs')
    ok(any('plC10394' in x[1] and 'crouched' in x[1] for x in fails(K_, 'throughcrouch')), 'PLANE: a crouched crossing alive west FAILs')
    r, inf = M.item_checks(K_, plane(K_, 'killed'), [], None)
    ok(any(x[0] == 'FAIL' and 'pl10420' in x[1] for x in r) and any('pl10420 (z 10420, GATE): KILLED' in i_ for i_ in inf), 'PLANE: passed the plane then died = KILLED, FAIL')
    r, inf = M.item_checks(K_, plane(K_, 'frozen'), [], None)
    ok(not [x for x in r if x[0] == 'FAIL'] and any(x[0] == 'WARN' and 'pl9995' in x[1] for x in r) and any('pl9995 (z 9995, GATE): VOID' in i_ for i_ in inf), 'PLANE: a frozen walk is VOID = WARN, not FAIL')
    r, inf = M.item_checks(K_, plane(K_, 'freestuck'), [], None)
    ok(not [x for x in r if x[0] == 'FAIL'] and any(x[0] == 'WARN' and 'plF' in x[1] for x in r), 'PLANE: a stuck free path is VOID = WARN')
    ok(any('plA' in x[1] for x in fails(K_, 'controlthrough')), 'PLANE: a control that walks through FAILs')
    r, inf = M.item_checks(K_, plane(K_, 'diedeast'), [], None)
    ok(not [x for x in r if x[0] == 'FAIL'] and any('pl10600 (z 10600, GATE): DIED' in i_ for i_ in inf), 'PLANE: a death east of the plane is DIED, WARN')
    r, inf = M.item_checks(K_, plane(K_, 'deadbefore'), [], None)
    ok(any('pl9995 (z 9995, GATE): DEAD-BEFORE' in i_ for i_ in inf), 'PLANE: a corpse at the tele is DEAD-BEFORE')
    ok(any('at least' in x[1] for x in fails(K_, 'allvoid')), 'PLANE: every gate walk VOID FAILs (no vacuous PASS)')
    ok(any('crossing sampled' in x[1] for x in fails(K_, 'nosample')), 'PLANE: a missing pos line FAILs')
    ok(any('van reaches state 7' in x[1] for x in fails(K_, 'nostate7')) and any('van' in x[1] for x in fails(K_, 'novan')), 'PLANE: no van state 7 / no van rows FAIL')
    ok(any('still hidden' in x[1] for x in fails(K_, 'unhidden')), 'PLANE: a visible panel FAILs (the van must drive through hidden ones)')
    sc = M.plane_seg('host')
    ok(sum(1 for l in sc if l.startswith('tele')) == len(M.PLANE_WALKS) == 14 and all(sc[i + 1] == 'wait 2000' and sc[i + 2].startswith('pos ') for i, l in enumerate(sc) if l.startswith('tele')),
       'PLANE script: 14 walks, each = tele, wait, pos')
    ok(sc.count('tap LCONTROL') == 4 and [x[1][2] for x in M.PLANE_WALKS if x[2] == 'GATE'] == [9995, 10100, 10200, 10334, 10394, 10420, 10600, 10700, 10790, 10850]
       and [x[0] for x in M.PLANE_WALKS][:2] == ['plA', 'plF'], 'PLANE walks: controls first, the ten gate z values, 2 crouch walks (4 stance taps)')
    ok(all(M.K[k_]['tag'] == '.before-dm07plane1109' and M.K[k_]['stage'] and k_ in M.ORDER and M.K[k_]['keepalive'] == 1 for k_ in M.PLANE_KITS)
       and M.K['DM07PLANE_1109']['stage'] != M.K['DM07PLANE72_1109']['stage'], 'PLANE kits: two stage kits (separate stage dirs), same tag, in ORDER')
    # pos parsed by name: the label decides, not the position in the line
    ok(M.pos_of(['01:00:00.000 script 3: pos x-label: me #0 (-4300, 550, 10400) heading 12'], 'x-label') == (-4300, 550, 10400), 'pos_of parses the named x')
    ok(M.pos_of(['01:00:00.000 script 3: pos other: me #0 (1, 2, 3) heading 12'], 'x-label') is None, 'pos_of: other label is None')
    r, inf = M.item_checks('DD10GATE_1109', dd10gate())
    ok(not [x for x in r if x[0] != 'PASS'] and any('BLOCKED' in i_ for i_ in inf), 'DD10GATE: stopped east of the gate = PASS')
    ok(any('stops the player' in x[1] for x in fails('DD10GATE_1109', 'through')), 'DD10GATE: alive west of the gate FAILs')
    r, _ = M.item_checks('DD10GATE_1109', dd10gate('stuck'))
    ok(any(x[0] == 'WARN' for x in r) and any(x[0] == 'FAIL' and 'at least 2' in x[1] for x in r), 'DD10GATE: a stuck start is VOID (WARN), all VOID FAILs')
    r, inf = M.item_checks('DD10GATE_1109', dd10gate('dead'))
    ok(any('DIED' in i_ for i_ in inf), 'DD10GATE: a death in the walk is DIED')
    ok('DD10GATE_1109' in M.ORDER and M.K['DD10GATE_1109']['stage'] is None and M.dd10gate_seg('host').index('waitvan 3 60000') < M.dd10gate_seg('host').index('tele 8150 60 900'),
       'DD10GATE kit: live, in ORDER, van parked before the walks')
    print('RESULT: kl_bench_1109_test %s (%d pass, %d fail)' % ('PASS' if not FAIL else 'FAIL', PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
