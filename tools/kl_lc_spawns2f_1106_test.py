"""Off-game self-test of kl_lc_spawns2f_1106 (fast: no game files, no 100 MB zips)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_lc_spawns2f_1106 as S

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


pl = S.plan()
names = [p[1] for p in pl]
t('plan: 31 unique nodes', len(pl) == 31 and len(set(names)) == 31)
t('plan: every point is on floor 2 at the same height', all(abs(p[2][1] - S.FLOOR_Y) < 1e-6 for p in pl))

with tempfile.TemporaryDirectory() as d:
    # pin: any other zip is refused before anything is written
    src = os.path.join(d, 'x.zip')
    open(src, 'wb').write(b'not the live zip')
    try:
        S.take_copy(src, S.LIVE_PIN, os.path.join(d, 'out'))
        t('take_copy refuses a zip with another md5', False)
    except ValueError as e:
        t('take_copy refuses a zip with another md5', 'refusing' in str(e) and not os.path.exists(os.path.join(d, 'out', '_in', 'F01_Main.zip')))
    try:
        S.take_copy(src, 'abc', os.path.join(d, 'out'))
        t('take_copy refuses a short pin', False)
    except ValueError:
        t('take_copy refuses a short pin', True)
    # the generated installer compiles and carries the md5 precheck + tag
    st = os.path.join(d, 'st'); os.makedirs(st)
    S.write_install(st, {'F01_Main.zip': ('a' * 32, 'b' * 32), 'KLJoin.ini': ('c' * 32, 'c' * 32)}, S.LIVE_PIN)
    txt = open(os.path.join(st, 'install.py')).read()
    t('install.py has tag, pin and --undo', S.TAG in txt and S.LIVE_PIN in txt and '--undo' in txt and "('KLJoin.ini'" not in txt)
    r = subprocess.run([sys.executable, os.path.join(st, 'install.py'), '--dry', '--game', os.path.join(d, 'nogame')], capture_output=True, text=True)
    t('install.py --dry refuses a missing game folder', r.returncode == 1 and 'REFUSED' in r.stdout)
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
