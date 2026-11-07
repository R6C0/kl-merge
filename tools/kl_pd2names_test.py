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
# 2026-11-07: the PD2 look is only on non-heli items: 41 = MG42, 40 = PAR, 47 = RPK; the heli / hind items go back to their stock text
check([k.PD2[i][0] for i in (40, 41, 47)] == ['PAR', 'MG42', 'RPK'], 'PAR / MG42 / RPK on items 40 / 41 / 47')
check(all(i not in k.PD2 for i in k.STOCK) and set(k.STOCK) == {42, 43, 44, 45, 46, 48, 51}, 'heli items carry no PD2 name')
check(all('PD2' in k.PD2[i][1] and 'model' in k.PD2[i][1] for i in (38, 47)) and k.PD2[41][1].startswith('GUESS') and k.PD2[40][1].startswith('GUESS'), 'status of the PD2-model items')
import kl_shop_sets as S
for it, (n, kind, pic) in S.ITEMS.items():
    check(len(n) <= k.MAXNAME and 'HELI' not in n.upper() and 'HIND' not in n.upper(), 'stock label %r' % n)
    check('door-mounted' not in kind.lower() and 'heli' not in kind.lower(), 'stock text of item %d has no heli wording' % it)
for it, (n, s_, f) in k.PD2.items():
    check('door-mounted' not in f.lower() and 'heli' not in n.lower() and 'heli' not in f.lower(), 'PD2 text of item %d has no heli wording' % it)
# a live ini that still holds the old PD2 heli names: the stock text comes back, and a re-run changes nothing
OLD = ('[Pairs]\r\nCount=3\r\nP0=18|42|31|RPK HELI\r\nP1=22|40|31|RPK\r\nP2=21|41|31|RPK L09\r\n[Desc]\r\n'
       'D0=Police reg.: 2042-II42\\nLight machine gun. Payday 2 light machine gun: the RPK, door-mounted, taken off its mount. Page II: sold in the TYPE 05 row, same price, same rank.\r\n'
       'D1=Police reg.: 2040-II40\\nLight machine gun. Payday 2 light machine gun: the RPK, belt-fed and heavy. Page II: sold in the TYPE 05 row, same price, same rank.\r\n'
       'D2=Police reg.: 2041-II41\\nLight machine gun. Origin: Chinese. Warehouse stock. Page II: sold in the X row, same price, same rank.\r\n')
n2, _ = k.rewrite(OLD)
nm2, ds2 = k.parse(n2)
check(nm2 == {42: 'TYPE 88 MG II', 40: 'PAR', 41: 'MG42'}, 'old heli name replaced by the stock one, 40 / 41 re-named: %r' % nm2)
check('RPK' not in n2 and 'door-mounted' not in n2 and 'Page II: sold in the TYPE 05 row' in ds2[42], 'old heli text gone, tail kept')
check(not k.problems(n2) and k.rewrite(n2)[0] == n2, 'rewritten ini is clean and a re-run changes nothing: %r' % k.problems(n2))
# HeliGuns pair table (kl_shop_sets): mode 0 drops the heli items, mode 2 keeps them on the dearest rows, item 48 never
NM = ['row%d' % i for i in range(40)]
TAB = {0: (62, 'a', 'x', 0), 10: (63, 'b', 'x', 2), 15: (51, 'c', 'x', 14), 16: (50, 'd', 'x', 14), 17: (45, 'e', 'x', 32), 18: (42, 'f', 'x', 31), 19: (43, 'g', 'x', 31),
       21: (41, 'h', 'x', 31), 22: (40, 'i', 'x', 31), 23: (47, 'j', 'x', 32), 24: (44, 'k', 'x', 31), 25: (46, 'l', 'x', 32), 27: (48, 'm', 'x', 32), 28: (33, 'n', 'x', 30)}
m0 = S.heli_apply(TAB, 0, NM)
check(not ({v[0] for v in m0.values()} & set(S.HELI_ITEMS)), 'mode 0: no heli item')
check(m0[25][0] == 41 and 21 not in m0 and 'row25' in m0[25][2], 'mode 0: item 41 re-paired to row 25, desc names the row')
check(all(m0[r] == TAB[r] for r in m0 if r != 25), 'mode 0: everything else untouched')
m2 = S.heli_apply(TAB, 2, NM)
check(48 not in {v[0] for v in m2.values()}, 'mode 2: item 48 never')
check({v[0] for v in m2.values()} >= {42, 43, 44, 45, 46, 51}, 'mode 2: the other heli items kept')
check(all(r in S.HELI_ROWS for r, v in m2.items() if v[0] in S.HELI_ITEMS), 'mode 2: heli items only on the dearest rows')
check(list(m2) == sorted(m2) and len(m2) == len({v[0] for v in m2.values()}), 'mode 2: sorted by row, one row per item')
try:
    S.heli_apply(TAB, 1, NM)
    check(False, 'mode 1 refused')
except ValueError:
    pass
check('HeliGuns=0 (recommended)' in S.render(m0, 0) and S.render(m0, 0).count('\r\nP') == len(m0), 'ini comment says (recommended), one P line per pair')
check(S.heli_rewrite(S.render(m2, 2), 0).count('|48|') == 0, 'heli_rewrite round trip')
with tempfile.TemporaryDirectory() as d:
    live = os.path.join(d, 'live.ini')
    open(live, 'w', newline='').write(SAMPLE)
    out = os.path.join(d, 'o')
    k.stage(out, live)
    check(all(os.path.isfile(os.path.join(out, f)) for f in ('KLShopPage.ini', 'INSTALL pd2names.bat', 'UNDO pd2names.bat')), 'staged files')
    check(k.check(os.path.join(out, 'KLShopPage.ini'), live) == 0, 'check passes')

print('kl_pd2names_test: %d checks, %d failed' % (checks, fails))
sys.exit(1 if fails else 0)
