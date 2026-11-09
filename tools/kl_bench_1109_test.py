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
        g.ent('V_Van', first)
        g.wait(5)
    g.ent('V_Van', (stop[0], 0, stop[1]) if mut != 'mixrow' else (stop[0], 0, 0))
    if mut == 'mixrow':
        g.ent('V_Van', (stop[0] + 9000, 0, stop[1]), dt=0.02)
    if mut != 'nostate3':
        g.say('BENCH1109 van at state 3', 0.2)
    g.wait(10)
    g.say('BENCH1109 van at state 7 (leaving)')
    for i in range(10):
        g.wait(3)
        if mut != 'nolate':
            g.ent('V_Van', (stop[0] + d * (600 + 900 * i) if mut != 'stuck' else stop[0], 0, stop[1]))
    if k == 'DM07_1109':
        g.say('goto (-1800, 10400) %s in 3000 ms: at (-2100, 550, 10400) heading 90' % ('reached' if mut != 'nocontrol' else 'NOT reached'))
        g.say('goto (-6000, 10400) %s in 15000 ms: at (-4300, 550, 10400) heading 270' % ('NOT reached' if mut != 'walkedout' else 'reached'))
        if mut != 'nopos':
            g.say('pos dm07-after-walk: me #0 (%d, 550, 10400) heading 270' % (-4300 if mut != 'farpos' else -5900))
    return g.done()


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
        if mut != 'nokick':
            g.say('BENCH1109 %s door %s: kicked (E x2, GUESS key)' % (lbl, d['host']))
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
            'DM01B_1109': ['east', 'nostate3', 'nolate', 'stuck', 'mixrow'],
            'DM07_1109': ['fence', 'nolate', 'nocontrol', 'walkedout', 'nopos', 'farpos', 'nostate3', 'stuck'],
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
    # cop actors are not in 'ents': unmoved squad/trigger rows are a WARN on DM03, the cop hits decide
    ok(not fails('DM03_1109', 'nomove'), 'DM03: unmoved ArrivingCops rows are a WARN, not a FAIL')
    # a control goto with the blocked goto missing (walk never ran) must FAIL
    a, dd, ctrl = log_for('DM07_1109')
    a2 = [l for l in a if 'goto (-6000' not in l]
    ok([x for x in M.item_checks('DM07_1109', a2, dd, ctrl)[0] if x[0] == 'FAIL'], 'DM07: missing blocked goto must FAIL')
    # pos parsed by name: the label decides, not the position in the line
    ok(M.pos_of(['01:00:00.000 script 3: pos x-label: me #0 (-4300, 550, 10400) heading 12'], 'x-label') == (-4300, 550, 10400), 'pos_of parses the named x')
    ok(M.pos_of(['01:00:00.000 script 3: pos other: me #0 (1, 2, 3) heading 12'], 'x-label') is None, 'pos_of: other label is None')
    print('RESULT: kl_bench_1109_test %s (%d pass, %d fail)' % ('PASS' if not FAIL else 'FAIL', PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
