"""Off-game self-test of kl_club_outro_1106 (fast: no game files, no 100 MB zips)."""
import os, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_club_outro_1106 as O

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


raw = b'1PW1' + struct.pack('<II', 17, 1) + bytes(range(256)) * 4
raw = raw[:12] + b''.join(struct.pack('<6f', i, i, i, 0, 10, 0) + b'\xcd' * 0 for i in range(17)) + b'\xcd' * 556
new, n = O.cut_raw(raw, 6)
t('cut_raw lowers only the count', n == 17 and len(new) == len(raw) and new[:4] == raw[:4] and struct.unpack_from('<I', new, 4)[0] == 6 and new[8:] == raw[8:])
t('cut_raw is idempotent', O.cut_raw(new, 6) == (new, 6))
t('cut_raw keeps a shorter route', O.cut_raw(new, 9)[0] == new)
for bad in (1, 0):
    try:
        O.cut_raw(raw, bad); t('cut_raw refuses keep=%d' % bad, False)
    except ValueError:
        t('cut_raw refuses keep=%d' % bad, True)
try:
    O.cut_raw(raw[:100], 6); t('cut_raw refuses a count that does not fit', False)
except ValueError:
    t('cut_raw refuses a count that does not fit', True)
# route replacement (candidate 2c): the frame of the real spline node, a rotation about y by 0.4 rad plus an offset, and 17 old points
import math
c, sn = math.cos(0.4), math.sin(0.4)
R = [[c, 0.0, -sn], [0.0, 1.0, 0.0], [sn, 0.0, c]]
T = (15871.5, 4699.5, -18602.9)
rr = b'1PW1' + struct.pack('<II', 17, 1) + b''.join(struct.pack('<3f', i, i, i) + struct.pack('<ff', 1.5 + i, 10.0) + b'\xcd' * 4 for i in range(17)) + b'\xcd' * 556
nr, n0 = O.route_raw(rr, O.ROUTE_2C, R, T)
t('route_raw: count 5, length and the bytes after the points kept', n0 == 17 and len(nr) == len(rr) and struct.unpack_from('<I', nr, 4)[0] == 5 and nr[12 + 24 * 17:] == rr[12 + 24 * 17:])
t('route_raw: world points read back to the route', O.route_done(O.world_points(nr, R, T), O.ROUTE_2C, 0.5))
t('route_raw: angle/10.0/cd bytes of point i kept', all(nr[12 + 24 * i + 12:12 + 24 * i + 24] == rr[12 + 24 * i + 12:12 + 24 * i + 24] for i in range(5)))
t('route_raw is idempotent', O.route_raw(nr, O.ROUTE_2C, R, T)[0] == nr)
t('route_done false for another route', not O.route_done(O.world_points(nr, R, T), O.ROUTE_2C[:4]) and not O.route_done(O.world_points(rr, R, T), O.ROUTE_2C))
for nm, rt, RR in (('one point', O.ROUTE_2C[:1], R), ('more than the field', O.ROUTE_2C * 4, R), ('a non-rotation frame', O.ROUTE_2C, [[2, 0, 0], [0, 1, 0], [0, 0, 1]])):
    try:
        O.route_raw(rr, rt, RR, T); t('route_raw refuses %s' % nm, False)
    except ValueError:
        t('route_raw refuses %s' % nm, True)
t('ROUTE_2C starts at the pad point and climbs north-east', O.ROUTE_2C[0] == (7058.0, 2271.0, 3467.0) and all(a[1] < b[1] and a[0] < b[0] for a, b in zip(O.ROUTE_2C, O.ROUTE_2C[1:])))
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, 'in'))
    open(os.path.join(d, 'in', 'F01_Main.zip'), 'wb').write(b'not the live zip')
    try:
        O.stage(os.path.join(d, 'out'), os.path.join(d, 'in'))
        t('stage refuses a zip with another md5', False)
    except ValueError as e:
        t('stage refuses a zip with another md5', 'refusing' in str(e) and not os.path.exists(os.path.join(d, 'out', 'F01_Main.zip')))
    st = os.path.join(d, 'st'); os.makedirs(st)
    O.write_install(st, {'F01_Main.zip': ('a' * 32, 'b' * 32), 'F01_Main.bots.base.md5': ('c' * 32, 'c' * 32)}, 6)
    src = open(os.path.join(st, 'install.py')).read()
    t('install.py has tag, pin and --undo', "'.before-outro1106'" in src and "LIVE_ZIP_MD5 = '" + 'a' * 32 in src and '--undo' in src)
    r = subprocess.run([sys.executable, os.path.join(st, 'install.py'), '--dry', '--game', os.path.join(d, 'nogame')], capture_output=True, text=True)
    t('install.py --dry refuses a missing game folder', r.returncode == 1 and 'REFUSED' in r.stdout)
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
