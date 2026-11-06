#!/usr/bin/env python3
"""Off-game self-test of tools/kl_n9_1106.py: ini building, map order/exclusions, estimate, run refusals. Never launches the game."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_n9_1106 as k

fails = []


def chk(name, cond, detail=''):
    print('  %s %s %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond:
        fails.append(name)


TPL_H = """[Expansion]
Page=2
Log=1
[Auto]
Enable=1
CmdAdd=-o AutoExit=580
[Lobby]
MinPlayers=2
[Auto]
CmdAdd=-o AutoExit=2400
MaxRunMs=2390000
[Script]
; c
1=waitwin CampaignMenu 180000
2=log SOLO host lobby
3=tap RIGHT
4=wait 900
5=log MAPS9 old
6=windows
7=waitpeers 9 900000 30000
8=tap RETURN
9=wait 300000
10=pass 3000
11=label bail
12=fail x
"""
TPL_J = """[Expansion]
Page=2
[Script]
1=waitwin CampaignMenu 180000
2=pass 3000
"""
ml = k.map_list(set())
names = [m for m, *_ in ml]
chk('17 maps', len(ml) == 17, str(len(ml)))
chk('Last Call and slot F07 excluded', not ({'DM05A', 'DD07', 'DM03A', 'DD10'} & set(names)))
ml2 = k.map_list({'DD01', 'DM01'})
n2 = [m for m, *_ in ml2]
chk('ran-at-9 maps go last', n2[-2:] == ['DD01', 'DM01'] and all(r for *_, r in ml2[-2:]) and not any(r for *_, r in ml2[:-2]), str(n2[-3:]))
h = k.build(TPL_H, 'host', 'DD09', 'F09', 0)
sc = [l.split('=', 1)[1] for l in h.split('[Script]')[1].strip().splitlines()]
chk('8 RIGHT taps for F09', sc.count('tap RIGHT') == 8, str(sc.count('tap RIGHT')))
chk('old MAPS9 block replaced', sum(1 for c in sc if c.startswith('log MAPS9')) == 1 and 'old' not in h)
chk('Page retargeted', 'Page=0' in h and 'Page=2' not in h)
chk('one [Auto], last-wins budget', h.count('[Auto]') == 1 and 'AutoExit=%d' % k.AUTO_EXIT in h and 'AutoExit=2400' not in h)
chk('waitpeers 9 540000 30000', 'waitpeers 9 540000 30000' in sc)
chk('observation wait set', 'wait %d' % k.OBS_MS in sc)
chk('FrameLimit 30 added', 'Fps=30' in h and 'StallMs=120000' in h)
chk('numbering contiguous', [l.split('=')[0] for l in h.split('[Script]')[1].strip().splitlines()] == [str(i + 1) for i in range(len(sc))])
h0 = k.build(TPL_H, 'host', 'DD01', 'F01', 0)
chk('F01 has no RIGHT taps', 'tap RIGHT' not in h0)
j = k.build(TPL_J, 'join', 'DD09', 'F09', 0)
chk('joiner: Page=0 and script kept', 'Page=0' in j and 'pass 3000' in j and j.count('[Script]') == 1)
a = k.arc_ini()
chk('arc ref: one pass, page 0, known ops', 'pass 1000' in a and 'Page=0' in a and all(c.split()[0] in k.OPS for c in k.script_lines(a.split('[Script]')[1].splitlines())))
typ, worst = k.estimate(17)
chk('estimate', 4 * 3600 < typ < 7 * 3600 and worst > typ and 'h' in k.hm(typ), '%s / %s' % (k.hm(typ), k.hm(worst)))
# run refuses (nothing launched) when the live dll is not an accepted SHIP, and when kl2.exe runs
calls = []
k.subprocess.run = lambda *a, **kw: calls.append(a) or type('R', (), {'stdout': '', 'returncode': 0})()
k.validate = lambda *a, **kw: 0
k.live_state = lambda: {'dll': 'b6a69772' + '0' * 24, 'ini': 'x'}
k.meta_of = lambda: {'order': [{'map': 'DD02', 'slot': 'F02', 'page': 0, 'ran_at_9': False}], 'zips': {'DD02': {}}}
rc = k.run(['DD02', '--owner-away'])
chk('run refuses a non-SHIP live dll, no launch', rc == 1 and not calls)
k.live_state = lambda: {'dll': '288fb016' + '0' * 24, 'ini': 'x'}
k.kl2_running = lambda: 2
rc = k.run(['DD02', '--owner-away'])
chk('run refuses while kl2.exe runs, no launch', rc == 1 and not calls)
print('RESULT: kl_n9_1106_test %s (%d FAIL)' % ('PASS' if not fails else 'FAIL', len(fails)))
sys.exit(1 if fails else 0)
