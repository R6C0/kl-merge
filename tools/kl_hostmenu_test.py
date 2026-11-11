"""
kl_hostmenu_test.py - the Host rows of the Mod settings window (mkoverlay.py HOST_ROWS) agree with klhostopt.c / klset.c (no game files).
Map-set row: option KLSHMap, one value per klho_maps[] entry (OnlineSet 0 / 2 / 3 / 9) with a label that names the set; options row: KLSHOpt,
8 values (bit0 AI, bit1 Solo, bit2 PD2); klset.c answers both names.

    python tools/kl_hostmenu_test.py          -> RESULT: PASS / FAIL
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KLH = os.path.join(os.path.dirname(HERE), 'klhook')
sys.path.insert(0, KLH)
import mkoverlay as M

FAILS = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


c = open(os.path.join(KLH, 'klhostopt.c'), encoding='latin-1').read()
maps = [int(x) for x in re.search(r'klho_maps\[4\]\s*=\s*\{([^}]*)\}', c).group(1).split(',')]
check(maps == [0, 2, 3, 9], 'klhostopt.c klho_maps = %s (Classic 0, Dead Men 2, DLC 3, Random 9)' % maps)
rows = {r[2]: r for r in M.HOST_ROWS}
check(set(rows) == {'KLSHMap', 'KLSHOpt'}, 'HOST_ROWS options %s' % sorted(rows))
vals = rows['KLSHMap'][3]
check(len(vals) == len(maps), 'KLSHMap has %d values, klho_maps has %d' % (len(vals), len(maps)))
for v, want in zip(vals, ('classic', 'dead men', 'dlc', 'random')):
    check(want in v.lower(), 'KLSHMap value "%s" names "%s"' % (v, want))
check(len(rows['KLSHOpt'][3]) == 8, 'KLSHOpt has 8 values (3 bits)')
k = open(os.path.join(KLH, 'klset.c'), encoding='latin-1').read()
for n in rows:
    check('"%s"' % n in k, 'klset.c kset_which answers %s' % n)
check('klho_get(0)' in k and 'klho_put(0, value)' in k, 'klset.c routes KLSHMap to klho_get/put(0)')
print('RESULT: ' + ('FAIL' if FAILS else 'PASS'))
sys.exit(1 if FAILS else 0)
