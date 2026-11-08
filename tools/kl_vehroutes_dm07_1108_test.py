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
t('relay: first key stays at the stop, last at START_X', xs[first] == old[first][0] and abs(xs[cut - 1] - V.START_X) < 1e-6)
t('relay: monotone west', all(xs[i + 1] < xs[i] for i in range(first, cut - 1)))
t('relay: speed profile kept (equal old steps -> equal new steps)', abs((xs[6] - xs[5]) - (xs[10] - xs[9])) < 1e-6)
t('stretch_x: start maps to START_X, PIN_X and beyond untouched, monotone', abs(V.stretch_x(V.OLD_X) - V.START_X) < 1e-6 and V.stretch_x(V.PIN_X) == V.PIN_X and V.stretch_x(V.PIN_X + 50) == V.PIN_X + 50 and V.stretch_x(-5000) > V.stretch_x(-5500))
t('start x is west of the fence (-4600) and east of the pocket wall (-9759) with margin', -9759 + 130 + 250 < V.START_X < -4600)
t('crash clamp stays clear of the pillar at 1089 (hull 130)', V.CRASH_MAX_X + 130 < 1089)
t('hide flag is 0x400 and two panels named', V.HIDE == 0x400 and len(V.FENCES) == 2)
print('RESULT: %d fail' % len(fails))
sys.exit(1 if fails else 0)
