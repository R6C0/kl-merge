#!/usr/bin/env python3
"""Self-test of the pure logic in kl_cover_dm09_1110.py (no game files needed): lane / boarding-box exclusion, street mask, missing wreck copies, FFCoverList / cap rules, install.py render."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_cover_dm09_1110 as M

n = bad = 0


def chk(name, cond):
    global n, bad
    n += 1
    if not cond:
        bad += 1
        print('FAIL', name)


# van lane: x -1850 +-350, z 8300..11100, pad 200
chk('lane centre', M.in_van_lane(-1850, 9000, 0))
chk('lane edge in', M.in_van_lane(-1500, 9000, 0))
chk('lane just out', not M.in_van_lane(-1400, 9000, 0))
chk('lane pad catches', M.in_van_lane(-1400, 9000, 200))
chk('lane z start', M.in_van_lane(-1850, 8300, 0) and not M.in_van_lane(-1850, 8200, 0))
chk('lane z end pad', M.in_van_lane(-1850, 11250, 200) and not M.in_van_lane(-1850, 11400, 200))
chk('far street not lane', not M.in_van_lane(-4900, 5700, 200))
chk('skip lane', M.van_lane_skip((-1850, 0, 9500)) == 'escape van lane')
chk('skip boarding box', M.van_lane_skip((-3000, 0, 4000), lambda p: True) == 'boarding box (otrExitLevel)')
chk('skip none', M.van_lane_skip((-3000, 0, 4000), lambda p: False) is None)
# street window
chk('street in', M.in_street(-3000, 0, 5000))
chk('tower floor out', not M.in_street(-3000, 900, 5000))
chk('terminal out', not M.in_street(-19000, 0, 12000))
chk('mask', M.street_mask([(-3000, 0, 5000), (-19000, 0, 5000), (-3000, 0, 5000)], [True, True, False]) == [True, False, False])
# wreck copies
cars = [dict(mid=(100, 0, 100), kind='high', group=7), dict(mid=(500, 0, 500), kind='low', group=7)]
ex = [dict(mid=(110, 0, 100), kind='high', parent=3), dict(mid=(500, 0, 500), kind='low', parent=7), dict(mid=(900, 0, 900), kind='high', parent=2)]
mc = M.missing_copies(cars, ex)
chk('copy present -> not missing', all(c['mid'] != (100, 0, 100) for c in mc))
chk('own-group box is not a copy', any(c['mid'] == (500, 0, 500) for c in mc))
chk('far box is not a copy', len(M.missing_copies([dict(mid=(0, 0, 0), kind='high', group=1)], ex)) == 1)
chk('other kind is not a copy', len(M.missing_copies([dict(mid=(110, 0, 100), kind='low', group=1)], ex)) == 1)
# one FFCoverList, cap
chk('ff 1', M.ffcover_ok(1))
chk('ff 0', not M.ffcover_ok(0))
chk('ff 2', not M.ffcover_ok(2))
chk('cap', M.cap_ok(4500) and not M.cap_ok(4501))
chk('group/tag distinct from earlier passes', M.GROUP not in ('KL_CoverMore!', 'KL_CoverSix!') and M.TAG not in ('_KM_', '_K6_'))
# install.py renders and compiles; pins are in it
src = M.render_install([('a.zip', 'a' * 32, 'b' * 32)], r'C:\x')
compile(src, 'install.py', 'exec')
chk('install pins', 'a' * 32 in src and 'b' * 32 in src and M.TAG_BAK in src and '@' not in src.replace('@echo', ''))
print('kl_cover_dm09_1110_test: %d checks, %d FAIL' % (n, bad))
sys.exit(1 if bad else 0)
