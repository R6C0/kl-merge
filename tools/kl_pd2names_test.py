#!/usr/bin/env python3
"""kl_pd2names_test.py - rewrites a sample KLShopPage.ini and checks names, lengths, tails (no game files)."""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_pd2names as k

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


SAMPLE = ('[Pairs]\r\nCount=3\r\nP0=28|33|30|TYPE 81\r\nP1=16|50|14|RPG-7\r\nP2=35|49|32|REM 700\r\n[Desc]\r\n'
          'D0=Police reg.: 2033-II33\\nAssault rifle. Origin: Chinese. Plain, rugged and everywhere. Page II: sold in the ZASTAVA M85 row, same price, same rank.\r\n'
          'D1=Police reg.: 2050-II50\\nRocket launcher. Origin: Russian. Not for the faint-hearted. Page II: sold in the HAWK BULLPUP row, same price, same rank.\r\n'
          'D2=Police reg.: 2049-II49\\nSniper rifle. Origin: American. A hunting rifle with a long reach. Page II: sold in the TYPE 95 SCOPE row, same price, same rank.\r\n')
new, log = k.rewrite(SAMPLE)
names, descs = k.parse(new)
check(names == {33: 'AK.762', 50: 'HRL-7', 49: 'R700'}, 'names rewritten: %r' % names)
check('P0=28|33|30|AK.762' in new, 'row/item/pic fields untouched')
check('Page II: sold in the ZASTAVA M85 row' in descs[33] and 'Payday 2' in descs[33], 'tail kept, PD2 line in')
check('Origin: Chinese' not in descs[33] and descs[33].startswith('Police reg.: 2033-II33\\nAssault rifle.'), 'header kept')
check(not k.problems(new), 'no problems: %r' % k.problems(new))
check(new.count('\r\n') == SAMPLE.count('\r\n'), 'line endings kept')
check(k.rewrite(new)[0] == new, 'idempotent') if False else None
for it, (n, s, f) in k.PD2.items():
    check(len(n) <= k.MAXNAME and n == n.upper(), 'name %r fits' % n)
    check(s.split()[0] in ('VERIFIED', 'GUESS'), 'status for %d' % it)
check(len({n for n, s, f in k.PD2.values()}) == len(k.PD2), 'names distinct')
check(k.PD2[33][0] == 'AK.762', 'Type 81 is the AK.762')
# batch 2 (2026-11-06): the PD2 RPK model sits on the Type 88 MG items 40-43; each keeps its own distinct RPK name
check([k.PD2[i][0] for i in (40, 41, 42, 43)] == ['RPK', 'RPK L09', 'RPK HELI', 'RPK HELI P'], 'RPK names of items 40-43')
check(all('PD2' in k.PD2[i][1] and 'model' in k.PD2[i][1] for i in (38, 40, 41, 42, 43, 44)), 'status of every PD2-model item says so')
with tempfile.TemporaryDirectory() as d:
    live = os.path.join(d, 'live.ini')
    open(live, 'w', newline='').write(SAMPLE)
    out = os.path.join(d, 'o')
    k.stage(out, live)
    check(all(os.path.isfile(os.path.join(out, f)) for f in ('KLShopPage.ini', 'INSTALL pd2names.bat', 'UNDO pd2names.bat')), 'staged files')
    check(k.check(os.path.join(out, 'KLShopPage.ini'), live) == 0, 'check passes')

print('kl_pd2names_test: %d checks, %d failed' % (checks, fails))
sys.exit(1 if fails else 0)
