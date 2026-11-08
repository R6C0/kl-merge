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
# true peak AFTER the ADPCM encode: every record of the pipeline (body -> drive_raw -> encode) decodes at <= -0.3 dBFS
import hashlib, json, shutil, subprocess, tempfile
import kl_gunsnd as G


class W:                                                # minimal record: what encode_for / ima_decode read
    codec = 0x11; name = 'synthetic'
    f = dict(rate=R, ch=1, block=0x400, spb=(0x400 - 4) * 2 + 1)
    def get(self, k): return self.f[k]


lim = 10 ** (P.LIMIT_DB / 20)
for cls in ('pistol', 'rifle', 'smg', 'mg', 'shotgun', 'distant', 'silenced'):
    for seed_tail in (0.2, 0.8):
        y = P.punch_body(shot(seed_tail), cls, False)
        z = P.punch_drive_raw(y, -3.15, 19.8)[0]
        data, ns, _ = G.encode_for(W(), z[:, None], R, rail=True)
        d = G.ima_decode(data, 1, 0x400, W.f['spb'], ns)
        check(np.abs(d.astype(np.int32)).max() / 32768.0 <= lim, '%s decoded peak %.3f dBFS <= -0.3' % (cls, P.peak_db(d)))
# an adversarial full-scale square wave (ADPCM overshoots a hard edge) must also come back under the limit
sq = np.where((np.arange(R // 2) // 40) % 2 == 0, 1.0, -1.0)
data, ns, _ = G.encode_for(W(), sq[:, None], R, rail=False)
check(np.abs(G.ima_decode(data, 1, 0x400, W.f['spb'], ns).astype(np.int32)).max() / 32768.0 <= lim, 'full-scale square wave limited after the encode')

# installer: all-or-nothing on a scratch 'game folder' with 4 fake banks (no real file read or written)
md5 = lambda b: hashlib.md5(b).hexdigest()
tmp = tempfile.mkdtemp(prefix='gpt_')
try:
    kit = os.path.join(tmp, 'kit'); game = os.path.join(tmp, 'game'); os.makedirs(os.path.join(kit, 'Banks', 'maps')); os.makedirs(game)
    shutil.copyfile(os.path.join(HERE, 'kl_gunpunch_install.py'), os.path.join(kit, 'install.py'))
    man = {}; olds = {}
    for i in range(4):
        old = bytes([i + 1]) * 4096; new = bytearray(old); new[100:300] = b'\xee' * 200; new[2000:2100] = b'\xdd' * 100; new = bytes(new)
        rel = 'b%d.WAV' % i; open(os.path.join(game, rel), 'wb').write(old); olds[rel] = old
        open(os.path.join(kit, 'Banks', 'maps', 'k%d.new' % i), 'wb').write(new[100:300] + new[2000:2100])
        open(os.path.join(kit, 'Banks', 'maps', 'k%d.old' % i), 'wb').write(old[100:300] + old[2000:2100])
        man['k%d' % i] = dict(file=rel, group='maps', id='k%d' % i, spans=[100, 200, 2000, 100], input_md5=md5(old), output_md5=md5(new))
    json.dump(dict(tag='t', banks=man), open(os.path.join(kit, 'manifest.json'), 'w'))
    run = lambda *a: subprocess.run([sys.executable, os.path.join(kit, 'install.py'), '--root', game] + list(a), capture_output=True, text=True)
    cur = lambda: {r: open(os.path.join(game, r), 'rb').read() for r in olds}
    r = run('--check'); check(r.returncode == 0 and cur() == olds, 'check is read-only and passes')
    # (a) write error on bank 3 (read-only file) after 0..2 were written: everything back
    import stat
    os.chmod(os.path.join(game, 'b2.WAV'), stat.S_IREAD)
    r = run(); check(r.returncode == 5 and 'rolled back' in r.stdout, 'write error rolls back (rc %d)' % r.returncode)
    check(cur() == olds, 'write error: every bank byte-identical to before')
    os.chmod(os.path.join(game, 'b2.WAV'), stat.S_IREAD | stat.S_IWRITE)
    # (b) corrupt span file of bank 3: md5 mismatch after the write: rolled back
    good = open(os.path.join(kit, 'Banks', 'maps', 'k3.new'), 'rb').read()
    open(os.path.join(kit, 'Banks', 'maps', 'k3.new'), 'wb').write(b'\x00' * len(good))
    r = run(); check(r.returncode == 5 and cur() == olds, 'md5 mismatch rolls back all (rc %d)' % r.returncode)
    open(os.path.join(kit, 'Banks', 'maps', 'k3.new'), 'wb').write(good)
    # (c) clean install, then undo is byte-exact; a second install is a no-op
    r = run(); check(r.returncode == 0 and all(md5(v) == man['k%d' % i]['output_md5'] for i, v in enumerate(cur().values())), 'clean install')
    check(run().returncode == 0, 'second install is a no-op')
    r = run('--undo'); check(r.returncode == 0 and cur() == olds, 'undo byte-exact')
    # (d) a bank that is neither input nor output: refused, nothing written
    open(os.path.join(game, 'b1.WAV'), 'ab').write(b'x'); before = cur()
    r = run(); check(r.returncode == 3 and cur() == before, 'foreign bank refused, nothing written')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('kl_gunpunch_test: %d checks, %d fail' % (checks, fails))
sys.exit(1 if fails else 0)
