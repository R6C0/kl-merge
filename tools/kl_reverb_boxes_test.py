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


DD = R.DD_DEFAULT
KNOWN_UNCOVERED = ('dm06', 'dm06b')
STOCK_TABLE = r'C:\kl_build_1024\roomboxes_1108\KLReverbBoxes.ini'
DM_TABLE = r'C:\kl_build_1024\roomboxes_1108\KLReverbBoxes_dm.ini'


def dm_live_checks():
    """Against the live Dog Days folder (read only; SKIPPED when it is not there): every Dead Men expansion map's boxes, snd offsets inside THAT map's .SND."""
    import struct
    import zipfile
    maps = [(k, z) for k, z in R.expansion_maps(DD) if k.startswith('dm')] if os.path.isdir(DD) else []
    if not maps:
        print('SKIP live Dead Men checks (no Dog Days folder)')
        return
    import kl_snd
    total = 0
    for key, zp in maps:
        boxes = R.dm_collect(zp, log=lambda *_: None)
        with zipfile.ZipFile(zp) as z:
            snd = kl_snd.Snd('dd', z.read(next(m for m in z.namelist() if m.endswith('_Main.SND')))).walk()
        offs = set(snd.tables.get(7, []))
        total += len(boxes)
        check(all(struct.unpack_from('<I', snd.b, b['snd'])[0] == 7 and b['snd'] in offs for b in boxes), '%s: every snd offset is a roomeffect (dword 7) of its own .SND' % key)
        check(all(min(b['h']) >= 1.0 and all(math.isfinite(x) for x in b['c'] + b['h']) for b in boxes), '%s: boxes non-degenerate' % key)
        check(all(30.0 <= b['prio'] <= 100.0 for b in boxes) and len({b['name'] for b in boxes}) == len(boxes), '%s: priorities 30..100, unique names' % key)
        back = R.parse(R.emit([(key, boxes)]))[key]
        check(len(back) == len(boxes) and [b['snd'] for b in back] == [b['snd'] for b in boxes], '%s: emit/parse round trip' % key)
        # an equal-priority overlap of two DIFFERENT effects would fall to the hook's order-dependent tie-break; same effect or disjoint boxes tie harmlessly
        bad = [(a['name'], b['name']) for i, a in enumerate(boxes) for b in boxes[i + 1:]
               if a['prio'] == b['prio'] and a['snd'] != b['snd'] and all(abs(a['c'][k] - b['c'][k]) < a['h'][k] + b['h'][k] for k in range(3))]
        check(not bad, '%s: no equal-priority overlap of different effects %s' % (key, bad[:2]))
        hit, n = R.spawn_coverage(zp, boxes)
        # dm06/dm06b: their only room box (M06FAA_Out_Part_03a) lies outside the graft's play area (0 of 18/63 spawns): known, documented, the engine default plays
        if key in KNOWN_UNCOVERED:
            check(n > 0, '%s: known uncovered map (%d of %d spawns inside a box)' % (key, hit, n))
        else:
            check(n > 0 and hit * 100 >= n * 90, '%s: >= 90%% of spawns inside a box (%d of %d)' % (key, hit, n))
        print('  live %-6s %2d boxes, %d effects, prio %s..%s, spawns covered %d/%d' % (key, len(boxes), len({b['snd'] for b in boxes}),
              min([b['prio'] for b in boxes] or [0]), max([b['prio'] for b in boxes] or [0]), hit, n))
    check(len(maps) == 11, '11 Dead Men expansion maps found (%d)' % len(maps))
    # stock/dd sections must stay byte-identical: the head of the generated _dm table (before the first dm section) equals the committed table's head
    if os.path.isfile(STOCK_TABLE) and os.path.isfile(DM_TABLE):
        def head(p):
            t = open(p, 'rb').read()
            i = t.find(b'[dm01]')
            return t[:i] if i >= 0 else None
        a, b = head(STOCK_TABLE), head(DM_TABLE)
        check(a is not None and a == b, 'stock/dd sections of the _dm table byte-identical to KLReverbBoxes.ini')
    # DM09 grafts two levels: the '+' source detection
    z9 = dict(maps).get('dm09')
    if z9:
        check('+' in R.dm_source(z9), 'dm09 source is a two-level graft (%s)' % R.dm_source(z9))
    check(total > 0, 'boxes emitted: %d' % total)


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

    # dm_prios: smaller volume -> higher priority, inside 30..100, one volume -> top
    pr = R.dm_prios([1000.0, 10.0, 100000.0, 1000.0])
    check(pr[1] > pr[0] > pr[2] and abs(pr[0] - pr[3]) < 0.1 and pr[0] != pr[3], 'prio: nested smaller room above the enclosing one, equal volumes within 0.1 but distinct')
    check(99.9 <= max(pr) <= 100.0 and min(pr) == 30.0, 'prio spans 30..100')
    pd = R.dm_prios([500.0, 400.0, 300.0, 200.0, 100.0])
    check(len(set(pd)) == 5 and pd == sorted(pd), 'prio: distinct volumes get distinct, ordered priorities')
    check(R.dm_prios([5.0, 5.0]) == [100.0, 100.0] and R.dm_prios([]) == [], 'prio: degenerate inputs')
    P = {'boxes': [{'name': 'big', 'center': [0, 0, 0], 'half': [50, 5, 50], 'ref': 100}, {'name': 'small', 'center': [1, 0, 0], 'half': [5, 5, 5], 'ref': 200}]}
    db = R.dm_boxes_from_plan(P)
    check(db[1]['prio'] > db[0]['prio'] and db[0]['snd'] == 100 and db[0]['q'] == [1, 0, 0, 0, 1, 0, 0, 0, 1], 'plan -> boxes: identity q, snd = ref, small wins')
    check(R.inside(db[0], [49, 0, 49]) and not R.inside(db[0], [51, 0, 0]), 'plan box tests like an AABB')
    fl = {'c': [0, 1250, -2500], 'h': [2000, 250, 500], 'q': [1, 0, 0, 0, 1, 0, 0, 0, 1]}   # dm02 KR014: floor at y 1000, as the .rmi room boxes
    check(not R.inside(fl, [1694, 1002, -2967], -30) and R.inside(fl, [1694, 1102, -2967], -30), 'feet on a box floor fail the enter margin, ear height (+100) passes (RB_DM02)')
    dm_live_checks()

    print('%s: %d checks, %d fails' % ('FAIL' if fails else 'PASS', checks, fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
