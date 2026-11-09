"""Self-test of kl_dm01b_undoor_1109 (2026-11-09). Pure checks always; the build + proof only when the pre-door DM01B build and the pinned live DM01B files are on this machine
(otherwise one SKIP line, exit 0: kl_tests runs every *_test.py and a missing game file is no verdict)."""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm01b_undoor_1109 as U

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


t('default hosts are D4 and 2D2 (D3 only with a proof)', U.DEFAULT == ['D4', '2D2'] and 'D3' in U.HOSTS)
t('host REF labels and pre-door nodes are distinct', len({h['ref'] for h in U.HOSTS.values()}) == 3 and len({h['k'] for h in U.HOSTS.values()}) == 3)
t('every default host names a group of its top', all(U.HOSTS[n]['grp'].startswith('KL_Door_') and U.HOSTS[n]['top'].startswith('KL_Interact!') for n in U.DEFAULT))
live = [os.path.join(U.LIVE_DIR, n) for n in ('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5')]
if all(os.path.isfile(p) for p in live + [U.REF_ZIP]) and [U.md5(p) for p in live + [U.REF_ZIP]] == [U.PINS[k] for k in ('live', 'bots', 'base', 'ref')]:
    d = tempfile.mkdtemp(prefix='undoor_')
    try:
        rep = U.build(U.LIVE_DIR, d, U.DEFAULT, log=lambda s: None)
        t('build wrote the three files and kept the .prm chunk count (Entries= unchanged)', all(os.path.isfile(os.path.join(d, n)) for n in ('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5')) and not rep['entries_changed'])
        t('bots.base.md5 holds the new plain md5', open(os.path.join(d, 'F03_Main.bots.base.md5')).read().strip() == rep['md5']['plain'])
        bad = U.check(d, U.LIVE_DIR, hosts=U.DEFAULT, log=lambda s: None)
        t('check: the diff against live is exactly the undo (%s)' % bad[:2], not bad)
        try:
            U.build(U.LIVE_DIR, None, ['D9'], log=lambda s: None)
            t('an unknown host is refused', False)
        except ValueError:
            t('an unknown host is refused', True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
else:
    print('SKIP build + proof: the pre-door DM01B build or the pinned live DM01B files are not here (or the kit is installed)')
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
