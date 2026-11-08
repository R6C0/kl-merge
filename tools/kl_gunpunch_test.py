#!/usr/bin/env python3
"""kl_gunpunch_test.py - off-game checks of tools/kl_gunpunch.py on synthetic shots (no game file is read or written): the punchy body keeps the clip
length, stays finite and under full scale; the tail duck lowers a long tail to its class target and leaves a dry clip alone; every class has a profile."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunpunch as P, kl_gunsnd_match as M, kl_gunsnd_all as A

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1; print('FAIL: ' + msg)


R = M.R
rng = np.random.default_rng(7)


def shot(tail_s, n_s=1.0):
    n = int(n_s * R); t = np.arange(n) / R
    x = rng.standard_normal(n) * np.exp(-t / 0.03) + 0.15 * rng.standard_normal(n) * np.exp(-t / tail_s)
    x = np.concatenate([np.zeros(int(0.01 * R)), x])[:n]
    return x / np.abs(x).max()


P.install()
check(set(P.PUNCH) >= {'pistol', 'shotgun', 'rifle', 'smg', 'mg', 'distant', 'silenced'}, 'profile classes')
check(all(c in P.PUNCH for c in set(A.gun_class(n) for n in ('/HG_X/a_Shot_01.wav', '/Shotgun_Y/a.wav', '/Rifle_Z/a.wav', '/SMG_A/a.wav', '/MG_B/a.wav', 'Distant_Shot_1', 'x_Silenced'))), 'gun_class results have profiles')
for cls in ('pistol', 'rifle', 'smg', 'mg', 'shotgun'):
    x = shot(0.5)
    y = P.punch_body(x, cls, False)
    check(len(y) == len(x) and np.isfinite(y).all() and np.abs(y).max() <= 1.0, cls + ' body keeps length, finite, no clip')
    z, d, h, fl = P.punch_drive_raw(y, -3.15, 19.8)
    check(len(z) == len(x) and np.isfinite(z).all() and np.abs(z).max() <= 1.0, cls + ' drive_raw keeps length, finite, no clip')
    check(abs(h - M.head_db(z)) < 1e-6, cls + ' reported head = measured head')
# the duck: a long loud tail goes down to about the class target, never below the floor; a dry clip is untouched
P.FLOOR_ON = False; y = P.punch_body(shot(1.0), 'rifle'); z0 = P.punch_drive_raw(y, -3.15, 19.8)[0]
P.FLOOR_ON = True; y = P.punch_body(shot(1.0), 'rifle'); z1 = P.punch_drive_raw(y, -3.15, 19.8)[0]
t0, t1 = P.tail_db(z0), P.tail_db(z1)
check(t1 <= t0 + 1e-6, 'duck never raises the tail (%.1f -> %.1f)' % (t0, t1))
check(t0 < P.PUNCH['rifle']['tgt'] or t1 >= t0 + P.PUNCH['rifle']['floor'] - 0.5, 'duck limited by the floor')
env = P.duck_env(R, 0, P.PUNCH['pistol'], -6.0)
check(env[0] == 1.0 and abs(env[-1] - 10 ** (-6 / 20)) < 1e-9 and (np.diff(env) <= 1e-12).all(), 'duck envelope monotone 1 -> floor')
short = shot(0.05, 0.3); check(P.tail_db(short) == -99.0, 'short clip has no tail window (not ducked)')
print('kl_gunpunch_test: %d checks, %d fail' % (checks, fails))
sys.exit(1 if fails else 0)
