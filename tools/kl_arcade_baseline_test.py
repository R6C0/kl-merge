"""
kl_arcade_baseline_test.py - self-test of tools/kl_arcade_baseline.py on a SYNTHETIC KLHook.log (no game files).

    python tools/kl_arcade_baseline_test.py          -> RESULT: PASS / FAIL
"""
import os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_arcade_baseline as B

FAILS = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


P = '2026-11-01 12:00:00.000 [1234] '
LOG1 = [
    P + 'KLHook starting',
    P + 'arcadeprobe: round start: Arcade level 3, 8 crew record(s), 7 AI (flags&1), clock left 250 s, van state 0',
    P + 'arcadeprobe: stacks at +5 s: 12 armed, 3 behind a shut door, $4200000 armed in all, 15 followed',
    P + 'arcadeprobe: stack 0a1b2c3d 300000 -> 0 (type 0 state 2 armed 0) at +20 s, nearest AI crew member within 8 m: 2',
    P + 'arcadeprobe: bot 2 money 0 -> 300000 (+300000) at +21 s, stage 1, status 0',
    P + 'arcadeprobe: van state 0 -> 1 at +100 s (clock left 150 s, timer 0.0)',
    P + 'arcadeprobe: van state 1 -> 3 at +120 s (clock left 130 s, timer 20.0)',
    P + 'arcadeprobe: bot 2 status 0 -> 4 ABOARD at +130 s (stage 3, money 300000)',
    P + 'arcadeprobe: bot 5 status 0 -> 7 DEAD at +60 s (stage 1, money 0)',
    P + 'arcadeprobe: tactics: round summary: 7 bot(s) (AI crew records), 5 stack(s) taken, 1250000 total (AI record money peak, the game\'s own field), 4 boarded, 10 stack(s) never emptied | van call s 100, 1 dead, 6 drain step(s), 2 type-1 drop(s), first take +20 s, last take +90 s, round lasted 250 s (left the round state or no Arcade session)',
    P + 'arcadeprobe: round start: Arcade level 3, 8 crew record(s), 7 AI (flags&1), clock left 250 s, van state 0',
    P + 'arcadeprobe: van state 0 -> 2 at +50 s (clock left 200 s, timer 0.0)',
]
LOG3 = [
    P + 'arcadeprobe: round start: Arcade level 1, 8 crew record(s), 7 AI (flags&1), clock left 250 s, van state 0',
    P + 'arcadeprobe: tactics: interim summary: 7 bot(s) (AI crew records), 3 stack(s) taken, 900000 total (AI record money peak, the game own field), 0 boarded, 12 stack(s) never emptied | van call s 80, 0 dead, 4 drain step(s), 1 type-1 drop(s), first take +20 s, last take +60 s, round lasted 90 s (interim)',
    P + 'arcadeprobe: tactics: interim summary: 7 bot(s) (AI crew records), 6 stack(s) taken, 1500000 total (AI record money peak, the game own field), 2 boarded, 9 stack(s) never emptied | van call s 80, 1 dead, 8 drain step(s), 1 type-1 drop(s), first take +20 s, last take +120 s, round lasted 120 s (interim)',
]
LOG2 = [P + 'nothing here']


def main():
    rs = B.parse(LOG1)
    check(len(rs) == 2, 'two rounds found (one with a summary, one cut off)')
    r = rs[0]
    check(r['summary'] and r['bots'] == 7 and r['taken'] == 5 and r['total'] == 1250000, 'summary: bots 7, taken 5, total 1.25M')
    check(r['boarded_n'] == 4 and r['dead_n'] == 1 and r['never'] == 10, 'summary: boarded 4, dead 1, never emptied 10')
    check(r['armed'] == 12 and r['door'] == 3, 'census: 12 armed, 3 behind a shut door')
    check(r['van_call'] == 100 and r['why'] == 'clock left 150', 'van call at +100 s (first state 1..4), clock left 150')
    check(not rs[1]['summary'] and rs[1]['van_call'] == 50 and rs[1]['taken'] is None, 'cut-off round: no summary, van call 50, taken unknown')
    r3 = B.parse(LOG3)
    check(len(r3) == 1 and not r3[0]['summary'] and r3[0]['taken'] == 6 and r3[0]['total'] == 1500000, 'killed round: the latest interim summary fills the row, still (no summary)')
    check(r3[0]['boarded_n'] == 2 and r3[0]['dead_n'] == 1 and r3[0]['van_call'] == 80 and r3[0]['never'] == 9, 'interim: boarded, dead, van call, never emptied')
    row = B.row('DD03', r)
    check(len(row) == len(B.COLS), 'row has the scorecard column count (%d)' % len(B.COLS))
    check(row[0] == 'DD03' and row[1] == '7' and row[2] == '12 (+3 behind shut door)' and row[3] == '5' and row[4] == '1.25M', 'row cells: bots/armed/taken/$')
    check(row[5] == '100 (clock left 150)' and row[6] == '4 / 7' and row[8] == '1', 'row cells: van, aboard, dead')
    row2 = B.row('DD04', rs[1])
    check('(no summary)' in row2[3], 'cut-off round row says (no summary)')
    check(B.row('DM01', None)[1] == 'no ArcadeProbe round', 'missing round row')
    check(B.parse(LOG2) == [], 'a log without ArcadeProbe lines gives no round')
    tab = B.table([row, row2])
    check(tab.splitlines()[0].startswith('| Map | Bots | Armed stacks | Stacks taken |') and tab.count('\n') == 3, 'table: header, rule, two rows')
    d = tempfile.mkdtemp()
    for tag, log in (('DD03', LOG1), ('DD04', LOG2)):
        os.makedirs(os.path.join(d, 'ARC1_' + tag, 'inst1'))
        open(os.path.join(d, 'ARC1_' + tag, 'inst1', 'KLHook.log'), 'w').write('\n'.join(log))
    check(B.main(['--solo', d, '--maps', 'DD03,DD04,DD05']) == 0, 'main over a folder: exit 0 when one map has a round')
    check(B.main(['--solo', d, '--maps', 'DD04,DD05']) == 1, 'main: exit 1 when none has')
    print('RESULT: %s' % ('FAIL (%d)' % len(FAILS) if FAILS else 'PASS'))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
