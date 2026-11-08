#!/usr/bin/env python3
"""kl_reverb_boxes_test.py - pure-python checks of tools/kl_reverb_boxes.py on a synthetic table (no game files). RESULT line like the other tool tests."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_reverb_boxes as R

fails = checks = 0


def check(c, what):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL', what)


def rot_y(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]            # a node frame R: world = R * local + T


def main():
    # a frame turned 90 degrees about y: local x -> world -z... derive Q = R^T and test with the same arithmetic the game side does
    Rm = rot_y(90)
    Q, err = R.q_from_frame(Rm)
    check(err < 1e-9, 'unit axes: no scale warning')
    check(all(abs(Q[3 * i + j] - Rm[j][i]) < 1e-12 for i in range(3) for j in range(3)), 'Q is the transpose of R')
    b = {'name': 'long box along local x', 'c': [1000.0, 50.0, -2000.0], 'h': [300.0, 40.0, 60.0], 'q': Q, 'snd': 438992, 'prio': 60.0}
    T = b['c']
    def world(l):
        return [T[i] + sum(Rm[i][j] * l[j] for j in range(3)) for i in range(3)]
    check(R.inside(b, world([290, 0, 0])), 'local (290,0,0) is inside')
    check(not R.inside(b, world([310, 0, 0])), 'local x 310 > half 300 is outside')
    check(not R.inside(b, world([0, 0, 70])), 'local z 70 > half 60 is outside')
    check(R.inside(b, world([0, 39, 59])), 'local corner region inside')
    # the long axis really is turned: a point 290 along WORLD x from the centre is NOT inside (the box runs along world z)
    check(not R.inside(b, [T[0] + 290, T[1], T[2]]), 'the rotation matters: 290 along world x is outside')
    check(R.inside(b, [T[0], T[1], T[2] + 290]) or R.inside(b, [T[0], T[1], T[2] - 290]), '290 along world z is inside')
    check(R.inside(b, world([305, 0, 0]), 10.0) and not R.inside(b, world([295, 0, 0]), -10.0), 'margin widens / shrinks')
    # scale warning
    Q2, err2 = R.q_from_frame([[2, 0, 0], [0, 1, 0], [0, 0, 1]])
    check(err2 > 0.9, 'a scaled frame is reported')

    # emit / parse round trip, section order, case, a known-empty map, names with odd characters
    boxes = [b, {'name': 'second;with semicolon', 'c': [-5.5, 0.0, 12.25], 'h': [1.0, 2.0, 3.0], 'q': [1, 0, 0, 0, 1, 0, 0, 0, 1], 'snd': 7, 'prio': 30.5}]
    text = R.emit([('F01\\F01_Main', boxes), ('DM02', []), ('dd05', boxes[1:])])
    back = R.parse(text)
    check(list(back) == ['f01\\f01_main', 'dm02', 'dd05'], 'sections in order, lower case')
    check(len(back['f01\\f01_main']) == 2 and back['dm02'] == [] and len(back['dd05']) == 1, 'box counts survive')
    r0 = back['f01\\f01_main'][0]
    check(all(abs(x - y) < 1e-3 for x, y in zip(r0['c'] + r0['h'], b['c'] + b['h'])), 'centre and half extents survive')
    check(all(abs(x - y) < 1e-5 for x, y in zip(r0['q'], b['q'])), 'rotation survives to 1e-5')
    check(r0['snd'] == 438992 and r0['prio'] == 60.0, 'snd and priority survive')
    check(back['f01\\f01_main'][1]['name'].startswith('second'), 'name survives (cut at a semicolon is harmless: the reader ignores it)')
    check(R.inside(r0, world([290, 0, 0])) and not R.inside(r0, world([310, 0, 0])), 'a parsed box tests like the original')
    check(R.emit(back.items(), header=False) == R.emit([(k, v) for k, v in back.items()], header=False), 'emit is stable')
    # re-emit of a parsed table parses to the same thing
    again = R.parse(R.emit(back.items()))
    check(list(again) == list(back) and all(len(again[k]) == len(back[k]) for k in back), 'second round trip')

    # reader strictness
    try:
        R.parse('[a]\nbox 1 2 3\n')
        check(False, 'short box line must raise')
    except ValueError:
        check(True, 'short box line raises')
    try:
        R.parse('[a]\nbox 0 0 0 -1 1 1 1 0 0 0 1 0 0 0 1 5 5\n')
        check(False, 'negative half extent must raise')
    except ValueError:
        check(True, 'negative half extent raises')
    check(R.parse('; c\n# c\n\n[x]\r\nbox 0 0 0 1 1 1 1 0 0 0 1 0 0 0 1 5 5\r\n') == {'x': [{'name': '', 'c': [0, 0, 0], 'h': [1, 1, 1], 'q': [1, 0, 0, 0, 1, 0, 0, 0, 1], 'snd': 5, 'prio': 5.0}]}, 'comments, blank lines, CRLF')
    check(R.fmt(-0.00001) == '0' and R.fmt(2.50) == '2.5' and R.fmt(-3.0) == '-3', 'number format')

    print('%s: %d checks, %d fails' % ('FAIL' if fails else 'PASS', checks, fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
