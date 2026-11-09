"""Off-game self-test of kl_doors_clear_1108 (pure geometry, no game files). Also pins the MAPS host decisions of kl_doors_1108 (review 2026-11-08)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_doors_clear_1108 as C

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


h = dict(hinge=(0.0, 0.0, 0.0), mid=(50.0, 0.0, 0.0), width=100.0)
t('leaf_dir is the unit hinge -> mid vector', C.leaf_dir(h) == (1.0, 0.0))
fp = C.footprints(h)
t('footprints: shut + 2 swings x 2 directions', [f[0] for f in fp] == ['shut', '+90', '-90', '+120', '-120'])
t('shut leaf runs along +x for the leaf width', fp[0][2] == (100.0, 0.0))
e90 = dict((f[0], f[2]) for f in fp)
t('+90 swings the free end to (0, +-100)', abs(e90['+90'][0]) < 1e-9 and abs(abs(e90['+90'][1]) - 100.0) < 1e-9 and e90['+90'][1] == -e90['-90'][1])
t('+120 free end is 100 cm from the hinge', abs(math.hypot(*e90['+120']) - 100.0) < 1e-9)
t('seg_dist: point beside, before and past a segment', abs(C.seg_dist(50, 30, (0, 0), (100, 0)) - 30) < 1e-9 and abs(C.seg_dist(-30, 40, (0, 0), (100, 0)) - 50) < 1e-9 and abs(C.seg_dist(130, 40, (0, 0), (100, 0)) - 50) < 1e-9)
I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
t('seg_hits_box: a leaf through a box hits, one 200 cm away does not', C.seg_hits_box((0, 0), (100, 0), (50, 0, 0), (10, 10, 10), I) and not C.seg_hits_box((0, 300), (100, 300), (50, 0, 0), (10, 10, 10), I))
t('seg_hits_box grows by the body half width', C.seg_hits_box((0, 35), (100, 35), (50, 0, 0), (10, 10, 10), I) and not C.seg_hits_box((0, 60), (100, 60), (50, 0, 0), (10, 10, 10), I))
t('a 3-cell pocket is a nook (< MIN_CUT), a 42-cell room is not', 3 < C.MIN_CUT <= 42)
t('escape names include the exit icon and the van boarding box', 'mapiconexit' in C.ESCAPE_NAMES and 'boardingtrigger' in C.ESCAPE_NAMES)
try:
    import kl_doors_1108 as D
    t('DM03 default hosts exclude 1076 (cuts a corridor off) and the one-sided 546/1255, keep 176/64', D.MAPS['DM03']['hosts'] == [176, 64])
    t('DM03A default hosts exclude 6770 (cuts a room off)', D.MAPS['DM03A']['hosts'] == [6516] and D.MAPS['DM03A']['top'] == 'KL_Interact!3')
except ImportError as e:
    t('kl_doors_1108 imports (%s)' % e, False)
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
