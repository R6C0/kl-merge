#!/usr/bin/env python3
"""kl_online_vs_arcade_test.py - hand-made fixtures for kl_online_vs_arcade.py (no game files). Exit 0 = all pass."""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_online_vs_arcade as k

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


ARC = """# x
| Map | Bots | Armed stacks | Stacks taken | $ carried | Van call s (why) | Aboard / bots | Far-counted | Dead | Stack never emptied | Get-up down / sent / up s | Trigger FIREs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DD05 | 7 | 6 | 6 | 4.50M | 181 (clock left 189) | 5 / 7 | - | 1 | 0 | - | - |
| DD06 | 7 | 8 | 8 | 5.55M | 186 (clock left 183) | 5 / 7 | - | 1 | 0 | - | - |
| DM06 | 7 | 4 | 4 | 0.00M | 122 (clock left 248) | 6 / 7 | - | 1 | 0 | - | - |
| DD01 | 7 | 0 (+58 behind shut door) | 58 | 7.46M | 204 (clock left 166) | 1 / 7 | - | 6 | 0 | - | - |

other text
"""

LOG_OK = """11:14:44.108 botfill: tactics: round 1 starts (Carry 2, Near 150, Take 2): the host orders the Ally bots itself
11:14:44.200 botfill: tactics: scan: 100 objects, 7 live Ally bot(s), 8 armed stack(s) (+0 behind a shut door) of 9 money object(s), van 0
11:15:08.300 botfill: tactics: bot 0 (actor 2e150020) GRABBED stack 1f6ceb50 = 680000; its tally 680000 after 1 grab(s)
11:17:50.186 botfill: tactics: van state 0 -> 1 (clock left 64.1 s, called 1, +1 s since the call)
11:19:19.285 botfill: tactics: round summary: 6 bot(s) given orders, 2 stack(s) taken, 3130000 total (hook tally, not the game's), 6 boarded, 6 stack(s) given up
11:19:58.835 botfill: tactics: round 2 starts (Carry 2, Near 150, Take 2): the host orders the Ally bots itself
11:20:27.138 botfill: tactics: bot 0 (actor 2e150020) GRABBED stack 1f6ceb50 = 680000; its tally 680000 after 1 grab(s)
""".splitlines()

LOG_NOSUM = """23:58:00.000 botfill: tactics: round 1 starts (Carry 2, Near 150, Take 2): x
23:58:10.000 botfill: tactics: bot 0 (actor 2e150020) GRABBED stack 1f6ceb50 = 1000000; its tally 1000000 after 1 grab(s)
23:58:12.000 botfill: tactics: bot 1 (actor 2e150021) GRABBED stack 1f6ceb51 = 500000; its tally 500000 after 1 grab(s)
00:00:20.500 botfill: tactics: van state 0 -> 2 (clock left 5.0 s, called 1, +1 s since the call)
00:00:30.000 botfill: tactics: bot 0 (actor 2e150020) BOARDED in the escape box (van state 3, inside by 0x1): tally 1000000
""".splitlines()

arc = k.parse_arcade('/nonexistent/none.md')
check(arc == {}, 'missing baseline file -> empty')
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, 'a.md')
    open(p, 'w').write(ARC)
    arc = k.parse_arcade(p)
check(sorted(arc) == ['DD01', 'DD05', 'DD06', 'DM06'], 'four maps parsed, got %s' % sorted(arc))
check(arc['DD06']['loot'] == 5550000 and arc['DD06']['taken'] == 8 and arc['DD06']['boarded'] == 5 and arc['DD06']['van'] == 186, 'DD06 row %s' % arc['DD06'])
check(arc['DM06']['loot'] == 0, 'zero loot kept as 0, got %s' % arc['DM06']['loot'])
check(arc['DD01']['taken'] == 58, 'door-note armed cell does not shift columns')

o = k.parse_online(LOG_OK, 1)
check(o['summary'] and o['loot'] == 3130000 and o['taken'] == 2 and o['boarded'] == 6, 'round 1 summary %s' % o)
check(o['van'] == 186, 'van call 186 s after the round start, got %s' % o['van'])
check(o['armed'] == 8, 'armed stacks from the scan')
o2 = k.parse_online(LOG_OK, 2)
check(o2 is not None and not o2['summary'] and o2['taken'] == 1 and o2['loot'] == 680000, 'round 2 has no summary: GRABBED fallback %s' % o2)
check(k.parse_online(LOG_OK, 3) is None, 'round 3 never started')
o3 = k.parse_online(LOG_NOSUM, 1)
check(o3['loot'] == 1500000 and o3['taken'] == 2 and o3['boarded'] == 1, 'fallback counts %s' % o3)
check(o3['van'] == 140, 'van time across midnight, got %s' % o3['van'])

v, r = k.verdict(arc['DD06'], o, 0.60)
check(v == 'BELOW' and abs(r - 3130000 / 5550000.0) < 1e-9, 'DD06 56%% is BELOW 60%%: %s %s' % (v, r))
v, r = k.verdict(arc['DD06'], o, 0.50)
check(v == 'PASS', 'DD06 passes at a 50 pct threshold')
v, r = k.verdict(arc['DD06'], dict(loot=3330000), 0.60)
check(v == 'PASS', 'exactly 60 pct passes (>=): %s' % v)
v, r = k.verdict(arc['DM06'], dict(loot=0), 0.60)
check(v == 'ARC-ZERO' and r is None, 'Arcade 0 loot: no ratio, no tautological PASS, got %s' % v)
dt, gp = k.deltas(arc['DD06'], o)
check(dt == '-6 / +1 / +0' and gp == ['STACKS'], 'DD06 deltas %s %s' % (dt, gp))
dt, gp = k.deltas(arc['DD06'], dict(taken=8, boarded=2, van=None))
check(gp == ['BOARDED', 'VAN'], 'boarded gap and missing van flagged: %s' % gp)
rows_, cnt_ = k.build(arc, [('DD06', LOG_OK), ('DM99', LOG_OK)], 1, 0.60)
check(cnt_['nobase_maps'] == ['DM99'] and cnt_['GAPS'] == 1, 'no-baseline map listed %s %s' % (cnt_['nobase_maps'], cnt_['GAPS']))
check(k.verdict(None, o, 0.6)[0] == 'NO-BASELINE', 'no Arcade row')
check(k.verdict(arc['DD05'], None, 0.6)[0] == 'NO-ROUND', 'no online round')

rows, cnt = k.build(arc, [('DD05', None), ('DD06', LOG_OK), ('DM99', LOG_OK), ('DD01', ['nothing'])], 1, 0.60)
check([r[-1] for r in rows] == ['NO-LOG', 'BELOW', 'NO-BASELINE', 'NO-ROUND'], 'verdict column %s' % [r[-1] for r in rows])
check(cnt['BELOW'] == 1 and cnt['NOLOG'] == 1 and cnt['NOBASE'] == 1 and cnt['NOROUND'] == 1 and cnt['PASS'] == 0, 'counts %s' % cnt)
check(rows[1][3] == '56%', 'ratio cell %s' % rows[1][3])
check(all(len(r) == len(k.COLS) for r in rows), 'every row has one cell per column')
check(k.table(rows).count('\n') == len(rows) + 1, 'table lines')

with tempfile.TemporaryDirectory() as d:
    ap_ = os.path.join(d, 'a.md')
    open(ap_, 'w').write(ARC)
    lp = os.path.join(d, 'KLHook.log')
    open(lp, 'w').write('\n'.join(LOG_OK))
    check(k.main(['--arcade', ap_, '--arcade', ap_, '--log', 'DD06=' + lp]) == 0, 'main with a log exits 0')
    check(k.main(['--arcade', ap_, '--log', 'DD06=' + os.path.join(d, 'none.log')]) == 1, 'main with no log exits 1')

print('kl_online_vs_arcade_test: %d checks, %d fail' % (checks, fails))
sys.exit(1 if fails else 0)
