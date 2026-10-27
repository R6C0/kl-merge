"""
kl_mod_options_test.py - self-test of kl_mod_options.py's two consistency checks on a SYNTHETIC ini (no game files):
own_key (the key that tells a row from the others), ini_rec (the '(recommended on|off)' marker on a key's line or in the
comment lines above it that name the key; 'until' / 'after' forms count as off for now) and check_rec (rows vs markers,
proven keys without a row). Then the real repo ini: every row must agree with klhook\\KLHook.ini.

    python tools/kl_mod_options_test.py          -> RESULT: PASS / FAIL
"""
import os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_mod_options as M

FAILS = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


INI = """; header
[HUD]
Online=1   ; (recommended on) master of the Online* HUD keys
; OnlineTagHold=1 (needs OnlineTags=1; (recommended on), benched CE27_ALL2G): a tag is not drawn until ...
OnlineTagHold=1
; OnlineTagStyle=0|1|2 (needs OnlineTags=1; recommended off until benched): 0 full name
OnlineTagStyle=0
OnlineTags=1   ; (recommended on) proven live: DD01ce4
OnlineShopNames=1   ; (recommended on) proven live: CE27_ALL2D..G
Rows12=1
; a comment with no key name (recommended off)
Plain=1

[HostOpts]
Enable=1   ; (recommended on) master switch
Menu=0     ; (recommended on after the live test) the two host rows

[Grades]
Enable=1   ; (recommended on) Arcade rotation clean
OnlineTags=0
Badge=1   ; (recommended on)
"""


def main():
    lines = M.split_lines(INI)
    r = lambda sec, key: M.ini_rec(lines, sec, key)[0]
    check(r('HUD', 'Online') == 'on', 'marker on the key line')
    check(r('HUD', 'OnlineTagHold') == 'on', 'marker in the comment above, "((recommended on), benched" form')
    check(r('HUD', 'OnlineTagStyle') == 'off', '"recommended off until benched" = off')
    check(r('HostOpts', 'Menu') == 'off', '"recommended on after the live test" = off for now')
    check(r('HUD', 'Plain') is None, 'a comment above that does not name the key is not its marker')
    check(r('HUD', 'Rows12') is None, 'no marker -> None')
    check(r('Grades', 'OnlineTags') is None, 'same key name in another section: that section only')
    check(r('HUD', 'Missing') == (None), 'absent key -> None')
    check(M.ini_rec(lines, 'HUD', 'Missing') == (None, None), 'absent key -> (None, None)')

    # own_key on the real table: a shared master key never wins over the row's own key
    ok = M.own_key(M.BY_ID['gradesbadge'])
    check(ok == ('Grades', 'Badge'), 'own_key gradesbadge = Badge (Enable is shared), got %r' % (ok,))
    ok = M.own_key(M.BY_ID['onlinetagstyle'])
    check(ok == ('HUD', 'OnlineTagStyle'), 'own_key onlinetagstyle = OnlineTagStyle, got %r' % (ok,))
    ok = M.own_key(M.BY_ID['gradesonlinetags'])
    check(ok == ('Grades', 'OnlineTags'), 'own_key gradesonlinetags = [Grades] OnlineTags, got %r' % (ok,))
    ok = M.own_key(M.BY_ID['hudonline'])
    check(ok == ('HUD', 'Online'), 'own_key hudonline = its master key, got %r' % (ok,))

    # check_rec on the synthetic ini, with the real table: rows whose own key is in it
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'KLHook.ini')
        open(p, 'w').write(INI)
        bad, norow, nocheck = M.check_rec(p)
        check(not bad, 'synthetic ini agrees with the table (%s)' % bad)
        check(any('OnlineShopNames' in x for x in norow) is False, 'OnlineShopNames has a row now (not in the no-row list)')
        check(all('proven' in x or 'benched' in x for x in norow), 'no-row list only holds proven keys: %s' % norow)
        ids = [x.split(':')[0] for x in nocheck]
        check('hudonline' not in ids and 'onlinetaghold' not in ids and 'fps240' in ids, 'rows whose own key is not in the synthetic ini are "not checked", the others are (%d unchecked)' % len(nocheck))
        # flip one marker: the check must name the row
        open(p, 'w').write(INI.replace('OnlineTagHold=1 (needs OnlineTags=1; (recommended on), benched', 'OnlineTagHold=1 (needs OnlineTags=1; recommended off until benched'))
        bad, norow, nocheck = M.check_rec(p)
        check(len(bad) == 1 and bad[0].startswith('onlinetaghold: row says on, the ini says off'), 'a flipped marker is reported on its row: %s' % bad)
        # a proven key the table does not offer
        open(p, 'w').write(INI.replace('Rows12=1', 'Rows12=1\nOnlineNewThing=1   ; (recommended on) proven live: X1'))
        bad, norow, nocheck = M.check_rec(p)
        check(any('OnlineNewThing' in x for x in norow), 'a proven recommended-on key without a row is listed: %s' % norow)
        open(p, 'w').write(INI.replace('Rows12=1', 'Rows12=1\nOnlineNewThing=1   ; (recommended on) not yet benched'))
        bad, norow, nocheck = M.check_rec(p)
        check(not any('OnlineNewThing' in x for x in norow), 'a recommended-on key without a proof word is not listed')

    # table shape: a prerequisite another row owns is never written off by this row (it comes after the own key, off value None)
    masters = {}
    for f in M.F:
        masters.setdefault(tuple(f['keys'][0][:2]), []).append(f['id'])
    shared = [(k, ids) for k, ids in masters.items() if len(ids) > 1 and not all(M.BY_ID[i].get('exact') or M.BY_ID[i].get('excl') or 'preset' in M.BY_ID[i] for i in ids)]
    check(not shared, 'no two plain rows share a master key: %s' % shared)
    clobber = [(f['id'], sec, key) for f in M.F for sec, key, onv, offv, dflt in f['keys'][1:] if (sec, key) in masters and offv is not None]
    check(not clobber, 'no row writes another row\'s master key when turned off: %s' % clobber)
    # plan(): gradesonlinetags off leaves [HUD] OnlineTags and [Grades] Enable alone; on writes the prerequisites too
    lines2 = M.split_lines(INI.replace('OnlineTags=0', 'OnlineTags=1'))
    w = M.plan(lines2, {'gradesonlinetags': False})
    check(w == [('Grades', 'OnlineTags', 0)], 'gradesonlinetags off writes only its own key: %s' % w)
    w = M.plan(lines, {'gradesonlinetags': True})
    check(('Grades', 'OnlineTags', 1) in w and ('Grades', 'Enable', 1) in w and ('HUD', 'OnlineTags', 1) in w, 'gradesonlinetags on writes the prerequisites too: %s' % w)
    w = M.plan(lines, {'onlinetagstyle': False, 'onlinetags': True})
    check(w == [], 'onlinetagstyle is read from OnlineTagStyle (0 = already off), not from OnlineTags: %s' % w)

    # the repo ini itself
    repo = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'klhook', 'KLHook.ini')
    if os.path.isfile(repo):
        bad, norow, nocheck = M.check_rec(repo)
        check(not bad, 'repo klhook/KLHook.ini: every row agrees with its marker (%s)' % bad)
        check(not norow, 'repo klhook/KLHook.ini: every proven recommended-on key has a row (%s)' % norow)
    print('RESULT: %s (%d checks, %d failed)' % ('PASS' if not FAILS else 'FAIL', 30 + 2 * os.path.isfile(repo), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
