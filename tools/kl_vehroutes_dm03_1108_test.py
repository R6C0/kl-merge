"""Off-game self-test of the pure parts of kl_vehroutes_dm03_1108 (no game files)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_vehroutes_dm03_1108 as V

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


t('hide y is modest: below the floor, nowhere near the -60000 octree crash', -20000 < V.HIDE_Y < -1000)
t('both spellings of the template group are matched', 'Traffic!Cars!Ground_USA_Bentley_00'.startswith(V.PREFIXES) and 'Trafiic!Cars!Ground_USA_Bentley_00'.startswith(V.PREFIXES))
t('traffic routes are not templates', not 'Traffic!WestTrafficNorthBound'.startswith(V.PREFIXES))
t('pins are three md5s and the slot is F03', len(V.PINS) == 3 and all(len(h) == 32 for h in V.PINS.values()) and V.SLOT == 'F03')
print('RESULT: %d fail' % len(fails))
sys.exit(1 if fails else 0)
