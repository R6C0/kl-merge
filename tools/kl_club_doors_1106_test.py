"""Off-game self-test of kl_club_doors_1106 (fast: no game files, no 100 MB zips)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_club_doors_1106 as D

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


# --doors subset: default = all four, names pick in DOORS order, bad picks are refused
t('select() default is all four doors', D.select() is D.DOORS and D.select('') is D.DOORS and len(D.DOORS) == 4)
t('select() subset keeps DOORS order', [x[0] for x in D.select('A02,B01')] == ['B01', 'A02'] and [x[0] for x in D.select(['F02'])] == ['F02'])
for bad in ('X9', 'B01,B01', 'B01,Z', ',', 'b01'):
    try:
        D.select(bad)
        t('select refuses %r' % bad, False)
    except ValueError:
        t('select refuses %r' % bad, True)
with tempfile.TemporaryDirectory() as d:
    # a bad --doors is refused before the live zip is read
    try:
        D.stage(os.path.join(d, 'o2'), os.path.join(d, 'nolive'), doors='X9')
        t('stage refuses a bad doors pick first', False)
    except ValueError as e:
        t('stage refuses a bad doors pick first', '--doors' in str(e))
    # patch_entries: exactly one line replaced, nothing else changed
    ini = os.path.join(d, 'a.ini')
    open(ini, 'wb').write(b'[FedBody]\r\n; Entries = text\r\nEntries=54354\r\nRoot=0\r\n')
    new, c = D.patch_entries(ini, 54446)
    t('patch_entries replaces one line', c == 1 and new == b'[FedBody]\r\n; Entries = text\r\nEntries=54446\r\nRoot=0\r\n')
    # pin: any other zip is refused before anything is read or written
    os.makedirs(os.path.join(d, 'live'))
    open(os.path.join(d, 'live', 'F01_Main.zip'), 'wb').write(b'not the live zip')
    try:
        D.stage(os.path.join(d, 'out'), os.path.join(d, 'live'))
        t('stage refuses a zip with another md5', False)
    except ValueError as e:
        t('stage refuses a zip with another md5', 'refusing' in str(e) and not os.path.exists(os.path.join(d, 'out', 'F01_Main.zip')))
    # the generated installer compiles and carries the md5 precheck + tag
    st = os.path.join(d, 'st'); os.makedirs(st)
    D.write_install(st, {'F01_Main.zip': ('a' * 32, 'b' * 32), 'KLJoin.ini': ('c' * 32, 'c' * 32)}, 54446)
    src = open(os.path.join(st, 'install.py')).read()
    t('install.py has tag, pin and --undo', "'.before-doors1106'" in src and D.LIVE_PIN in src and '--undo' in src and "('KLJoin.ini'" not in src)
    r = subprocess.run([sys.executable, os.path.join(st, 'install.py'), '--dry', '--game', os.path.join(d, 'nogame')], capture_output=True, text=True)
    t('install.py --dry refuses a missing game folder', r.returncode == 1 and 'REFUSED' in r.stdout)
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
