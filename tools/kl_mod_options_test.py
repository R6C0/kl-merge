"""
kl_mod_options_test.py - self-test of kl_mod_options.py's two consistency checks on a SYNTHETIC ini (no game files):
own_key (the key that tells a row from the others), ini_rec (the '(recommended on|off)' marker on a key's line or in the
comment lines above it that name the key; 'until' / 'after' forms count as off for now) and check_rec (rows vs markers,
proven keys without a row), scan_keys / ini_mentions / check_ini (the keys the sources read vs the keys the ini names).
Then the real repo ini: every row must agree with klhook\\KLHook.ini, and every row key must be mentioned there.

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
        # a proven key the ini only carries commented out (the page II online keys of 10-27 were ';OnlineSend=0 ; (recommended on; benched ...)')
        open(p, 'w').write(INI.replace('Rows12=1', 'Rows12=1\n;OnlineNewThing=0   ; (recommended on; benched X27_ABC 10-27) 1 = ...\n;OnlineNewThing=0   ; a repeat'))
        bad, norow, nocheck = M.check_rec(p)
        check(sum('OnlineNewThing' in x for x in norow) == 1, 'a commented-out proven key without a row is listed once: %s' % norow)
        open(p, 'w').write(INI.replace('Rows12=1', 'Rows12=1\n; a comment that says OnlineNewThing=1 is (recommended on) proven live: X1, not a key line'))
        bad, norow, nocheck = M.check_rec(p)
        check(not any('OnlineNewThing' in x for x in norow), 'a comment sentence naming Key=value is not a commented-out key')

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

    # describe_writes (2026-11-01): a prerequisite write over the same value is told apart from a real change and from a new key
    d = dict(M.describe_writes(lines, [('HUD', 'Online', 1), ('HUD', 'OnlineTagStyle', 1), ('Grades', 'OnlineTags', 1), ('Input', 'PumpNoBlock', 1), ('Nowhere', 'Key', 1)]))
    check(d.get('[HUD] Online = 1  (already 1)') is False, 'describe_writes: a write of the value the ini has is no change: %s' % list(d))
    check(d.get('[HUD] OnlineTagStyle = 1  (was 0)') is True, 'describe_writes: 0 -> 1 is a change')
    check(d.get('[Grades] OnlineTags = 1  (was 0)') is True, 'describe_writes: the section is told apart ([Grades] OnlineTags, not [HUD])')
    check(d.get('[Input] PumpNoBlock = 1  (new key; the DLL default was 0)') is True, 'describe_writes: an absent row key names the DLL default and counts as a change')
    check(d.get('[Nowhere] Key = 1  (new key; the DLL default was ?)') is True, 'describe_writes: an absent key no row carries is still a change')
    check(M.writes_summary(M.describe_writes(lines, [('HUD', 'Online', 1), ('HUD', 'OnlineTagStyle', 1)])) == '1 value change(s), 1 write(s) that keep the value the ini already has', 'writes_summary counts both kinds')
    nd = M.describe_writes(lines, [('Input', 'PumpNoBlock', 0)])
    check(nd[0] == ('[Input] PumpNoBlock = 0  (new key; the DLL default was 0)', False), 'describe_writes: a new key written to its own DLL default is no change: %s' % nd)

    # a key the ini only carries commented out still gives its marker (2026-10-27: ';PumpNoBlock=0 ... (recommended off until benched)')
    lines3 = M.split_lines(INI + '\n[Input]\n; the pump\n;MouseMoveMs=0\n;PumpNoBlock=0   ; never waits (recommended off until benched: C27_PNB1)\n')
    check(M.find_commented_key(lines3, 'Input', 'PumpNoBlock') is not None, 'find_commented_key finds ;PumpNoBlock=0')
    check(M.ini_rec(lines3, 'Input', 'PumpNoBlock')[0] == 'off', 'marker on a commented key line: off until benched')
    check(M.ini_rec(lines3, 'Input', 'MouseMoveMs')[0] is None, 'commented key without a marker -> None')
    check(M.ini_mentions(lines3, 'Input', 'PumpNoBlock') and M.ini_mentions(lines3, 'Input', 'MouseMoveMs'), 'ini_mentions: commented keys count')
    check(M.ini_mentions(lines3, 'HUD', 'OnlineTagStyle') and M.ini_mentions(lines3, 'HUD', 'Online'), 'ini_mentions: active keys count')
    check(not M.ini_mentions(lines3, 'HUD', 'Nowhere') and not M.ini_mentions(lines3, 'Nope', 'Online'), 'ini_mentions: absent key / section -> False')

    # scan_keys + check_ini on a synthetic source folder: direct Int / String calls, an Int helper, a String helper, other ini files
    src = tempfile.mkdtemp()
    with open(os.path.join(src, 'klx.c'), 'w') as fh:
        fh.write('static int klx_inii(const char *key, int def) { return GetPrivateProfileIntA("X", key, def, klh_ini); }\n'
                 'static float klx_inif(const char *key, const char *def) { char t[32]; GetPrivateProfileStringA("X", key, def, t, sizeof t, klh_ini); return (float)atof(t); }\n'
                 'void klx_init(void) { int a = GetPrivateProfileIntA("Input", "PumpNoBlock", 0, klh_ini) != 0; char b[8];\n'
                 '  GetPrivateProfileStringA("Expansion", "MountFirst", "", b, sizeof b, klh_ini); int c = GetPrivateProfileIntA("Auto", "Hooks", 1, kla_ini);\n'
                 '  int d = klx_inii("Rows", 3); float e = klx_inif("Near", "30");\n'
                 '  GetPrivateProfileStringA("X", "Meter", "3", b, sizeof b, klh_ini); GetPrivateProfileStringA("X", "Cap", "DM05A:60", b, sizeof b, klh_ini); }\n')
    seen, where = M.scan_keys(src)
    check(seen.get(('Input', 'PumpNoBlock')) == {0} and seen.get(('X', 'Rows')) == {3}, 'scan_keys: direct and helper Int defaults: %s' % seen)
    check(seen.get(('X', 'Meter')) == {3} and ('X', 'Cap') not in seen and ('X', 'Cap') in where, 'scan_keys: a whole-number String default counts, a text one is only read: %s' % seen)
    check(('X', 'Near') in where and ('Expansion', 'MountFirst') in where, 'scan_keys: String helper and direct String keys are read: %s' % sorted(where))
    check(('Auto', 'Hooks') not in where, 'scan_keys: a key read from another ini (kla_ini) is not a KLHook.ini key')
    ini3 = os.path.join(src, 'k.ini')
    with open(ini3, 'w') as fh:
        fh.write('[Input]\n;PumpNoBlock=0\n[X]\n; Rows=3 = the rows\n')
    rowless, un = M.check_ini(src, ini3)
    check(rowless == [], 'check_ini: the pumpnoblock row key is mentioned: %s' % rowless)
    check(sorted(un) == ['[Expansion] MountFirst (klx.c)', '[X] Cap (klx.c)', '[X] Meter (klx.c)', '[X] Near (klx.c)'], 'check_ini: unmentioned = the four keys no line names: %s' % un)
    with open(ini3, 'w') as fh:
        fh.write('[Input]\n; nothing here\n')
    rowless, un = M.check_ini(src, ini3)
    check(rowless == ['pumpnoblock: [Input] PumpNoBlock (klx.c)'], 'check_ini: a row key the ini leaves out is reported: %s' % rowless)

    # Recommended leaves the owner's own choices alone (2026-11-01, triage Finding 2: it wrote OnlineSet 9 -> 0, Glare 0 -> 1, ...)
    own = M.split_lines('[Expansion]\nOnlineSet=9   ; 1026 owner: random stock + Dead Men map\n[Graphics]\nGlare=0\nAA=1\n'
                        '[Hire]\nEnable=1   ; owner 10-27 evening: try buying characters\n[FrameLimit]\nEnable=0   ; stutter A/B (owner): off again\n'
                        '[Grenade]\nThrow=1   ; the session installed it\n')
    wants, kept = M.rec_wants(own)
    kept = dict(kept)
    check('onlinerandom' in kept and 'onlinerandom' not in wants, 'Recommended keeps a key with a "1026 owner:" note: %s' % kept.get('onlinerandom'))
    check('glare' in kept and 'aa' in kept, 'Recommended keeps the keys the game\'s Mod settings menu writes when the ini has them')
    check('hire' in kept and 'fps60' in kept, 'Recommended keeps "owner 10-27" and "(owner)" notes, the fps rows by [FrameLimit] Enable')
    check(wants.get('grenade') is False, 'Recommended still sets a row whose key has no owner note (grenade -> off)')
    check('onlinevanbots' in kept and 'onlinevanbots' not in wants, 'Recommended keeps a row marked keep=')

    # Recommended must not fight itself (2026-11-01, scheduled check-in): onlineguardliveonly (on) wrote OnlineGuardMode=1 as its
    # prerequisite while onlineguardmode (then off) wrote it 0 -> the key flip-flopped with every press. Rule: a key a recommended-on row
    # needs is never the own key of a recommended-off row; and pressing Recommended twice writes nothing the second time.
    need, off = {}, {}
    for f in M.F:
        if f['rec'] == 'on':
            for sec, key, onv, offv, dflt in f['keys'][1:]:
                need.setdefault((sec.lower(), key.lower()), []).append(f['id'])
        else:
            sec, key = f['keys'][0][:2]
            off.setdefault((sec.lower(), key.lower()), []).append(f['id'])
    fight = [(k, off[k], need[k]) for k in need if k in off and not any(M.BY_ID[i].get('exact') or M.BY_ID[i].get('excl') for i in off[k])]
    check(not fight, 'no recommended-on row needs a key a recommended-off row switches off: %s' % fight)

    # Taking loot online without banking it loses the money (11-01 scheduled check-in): OnlineTacticsTake=2 depletes the stack through the
    # game's 0x4e3f40, and online the game cannot bank for a bot (no seat), so only the hook's ledger + OnlineBankCredit bring it to the
    # team. Rule: the take row writes the two bank keys with it, and the two rows are recommended the same way.
    take, bank = M.BY_ID['onlinetacticstake'], M.BY_ID['onlinebank']
    tk = {(s.lower(), k.lower()): v for s, k, v, _o, _d in take['keys'][1:]}
    check(tk.get(('botfill', 'onlinebank')) == 1 and tk.get(('botfill', 'onlinebankcredit')) == 1, 'the loot-taking row writes OnlineBank=1 + OnlineBankCredit=1 with it')
    check(take['rec'] == bank['rec'], 'the loot-taking and the bank rows are recommended the same way (%s / %s)' % (take['rec'], bank['rec']))
    ls = M.split_lines(INI + '\n[BotFill]\nOnlineHost=1\nOnlineTactics=1\nOnlineTacticsTake=0\n')
    w = M.plan(ls, {'onlinetacticstake': True})
    check(('BotFill', 'OnlineBank', 1) in w and ('BotFill', 'OnlineBankCredit', 1) in w and ('BotFill', 'OnlineTacticsTake', 2) in w, 'ticking the loot-taking row alone also switches the bank on: %s' % w)

    def twice(text):
        ls = M.split_lines(text)
        for sec, key, val in M.plan(ls, M.rec_wants(ls)[0]):
            M.set_key(ls, sec, key, val)
        return M.plan(ls, M.rec_wants(ls)[0])
    again = twice(INI)
    check(again == [], 'Recommended pressed twice on the synthetic ini writes nothing the second time: %s' % again)
    again = twice(INI + '\n[BotFill]\nOnlineGuardMode=1\nOnlineGuardLiveOnly=1\n')
    check(again == [], 'Recommended pressed twice with the guard keys on writes nothing the second time (the 11-01 flip-flop): %s' % again)

    # the repo ini itself
    repo =os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'klhook', 'KLHook.ini')
    if os.path.isfile(repo):
        bad, norow, nocheck = M.check_rec(repo)
        check(not bad, 'repo klhook/KLHook.ini: every row agrees with its marker (%s)' % bad)
        check(not norow, 'repo klhook/KLHook.ini: every proven recommended-on key has a row (%s)' % norow)
        rowless, un = M.check_ini(os.path.dirname(repo), repo)
        check(not rowless, 'repo klhook/KLHook.ini mentions every row key (%s)' % rowless)
        again = twice(M.read_ini(repo))
        check(again == [], 'Recommended pressed twice on the repo ini writes nothing the second time: %s' % again)
    print('RESULT: %s (%d checks, %d failed)' % ('PASS' if not FAILS else 'FAIL', 58 + 4 * os.path.isfile(repo), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
