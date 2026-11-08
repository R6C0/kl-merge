"""Off-game self-test of the pure parts of kl_vehaudit_1108 (no game files)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_vehaudit_1108 as V

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


d = V.densify([(0, 0, 0), (300, 0, 0)], 100)
t('densify keeps both ends and steps <= 100', d[0] == (0, 0, 0) and d[-1] == (300, 0, 0) and len(d) == 4)
t('heading is a unit vector along x', V.heading((0, 5, 0), (10, 9, 0)) == (1.0, 0.0))
segs = V.body_lines('CAR', (0, 0, 0), (1.0, 0.0))
t('car body: 3 lateral lines x (3 heights + 1 column)', len(segs) == 12 and segs[0][0][1] == 73.0 and segs[3][1][1] == 263.0)
t('heli body: 3 centre points + 4 spokes x 3 heights', len(V.body_lines('HELI', (0, 0, 0), (1.0, 0.0))) == 15)
pts = [(0, 0, 0)] * 2 + [(500, 0, 0)] + [(1000, 0, 0)] * 5
t('stop_of finds the far plateau', V.stop_of(pts) == (1000, 0, 0) and V.stop_of([(0, 0, 0), (500, 0, 0)]) is None)
print('RESULT: %d fail' % len(fails))
sys.exit(1 if fails else 0)
