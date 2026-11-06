"""Off-game self-test of kl_club_doors_1106 (fast: no game files, no 100 MB zips)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_club_doors_1106 as D

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


with tempfile.TemporaryDirectory() as d:
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
