"""Off-game self-test of the pure parts of kl_vehroutes_dm07_1108 (no game files)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_vehroutes_dm07_1108 as V

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


old = [(-6000 + 40 * i, 400.0 + i, 10400.0) for i in range(6)] + [(-5800 + 100 * j, 405.0, 10400.0) for j in range(1, 6)]
first, cut = 5, 11
xs = V.relay(old, first, cut)
t('relay: first key stays at the stop, last at OUT_X', xs[first] == old[first][0] and abs(xs[cut - 1] - V.OUT_X) < 1e-6)
t('relay: monotone west', all(xs[i + 1] < xs[i] for i in range(first, cut - 1)))
t('relay: speed profile kept (equal old steps -> equal new steps)', abs((xs[6] - xs[5]) - (xs[10] - xs[9])) < 1e-6)
f = V.arrival_y(old, first)
t('arrival_y interpolates and flat-extends', f(-6100) == 400.0 and f(-6000) == 400.0 and abs(f(-5980) - 400.5) < 1e-6 and f(0) == old[first][1])
t('crash clamp stays clear of the pillar at 1089 (hull 130)', V.CRASH_MAX_X + 130 < 1089)
t('hide flag is 0x400 and two panels named', V.HIDE == 0x400 and len(V.FENCES) == 2)
print('RESULT: %d fail' % len(fails))
sys.exit(1 if fails else 0)
