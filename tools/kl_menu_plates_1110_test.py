#!/usr/bin/env python3
"""
kl_menu_plates_1110_test.py - self-test of tools/kl_menu_plates_1110.py on SYNTHETIC archives: no game file.

A fake <game>\\KLExpansion\\Overlay with the three `_deadmen` siblings (pale OnFocus as the 11-09 stage1 wrote it, an untouched binary
member each) and a stock-coloured Patch01.zip (OnFocus already ink: must be skipped) is staged; the XML edit (alpha kept, malformed /
absent attributes left alone, other sets untouched, table signature equal), the member-equality proof, the pins, check(), and install.py
(dry / install / refused re-install / undo byte-exact / refused re-undo, on the fake game folder) are exercised.
exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py.
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_plates_1110 as M
import kl_hud_menu as HM

fails = []
NCHECK = [0]


def check(cond, what):
    NCHECK[0] += 1
    print(('  ok   ' if cond else '  FAIL ') + what)
    if not cond:
        fails.append(what)


def quiet(*_a, **_k):
    pass


PALE = '''<Windows>
  <ColorSet Name="Default" NormalColor="0xfff3f0ea" FocusColor="0xa00c0c0d" DisableColor="0xff8d8982"/>
  <ColorSet Name="OnFocus" NormalColor="0xfff3f0ea" FocusColor="0xff0c0c0d" DisableColor="0xff8d8982"/>
  <ColorSet Name="Header" NormalColor="0xfff0475a" FocusColor="0xfff0475a" DisableColor="0xff8c3138"/>
  <Template Name="HelpText_GT" Font="Text" X="1"/>
  <Window Name="FALobby" Template="WindowDefault">
    <GuiElement Type="TextBlock" Name="Headline0" Text="/Menu/Online/Profile/GamerTag" Font="Text" ColorSet="OnFocus"/>
    <GuiElement Type="ToggleText" Name="D" Text="%%Location" RecCSFocus="OnFocus" RecCSDefault="Default">
      <Text Text="%%Hot Coffee"/>
    </GuiElement>
  </Window>
</Windows>
'''
# online.xml: the set twice (as online.xml defines Default twice), one with alpha 80, a malformed and an absent attribute
ONLINE = '''<Windows>
  <ColorSet Name="Default" NormalColor="0xa0f3f0ea" FocusColor="0xa00c0c0d" DisableColor="0xff8d8982"/>
  <ColorSet Name="OnFocus" NormalColor="0x80f3f0ea" FocusColor="0xff0c0c0d" DisableColor="bogus"/>
  <ColorSet Name="OnFocus" NormalColor="0xfff3f0ea" FocusColor="0xffffffff"/>
  <ColorSet Name="Black" NormalColor="0xff0c0c0d" FocusColor="0xff0c0c0d" DisableColor="0xff0c0c0d"/>
  <Window Name="HeistStatus" Template="WindowDefault">
    <GuiElement Type="TextBlock" Name="HB" Text="Heist_Bonus" Font="Text" ColorSet="OnFocus"/>
  </Window>
</Windows>
'''
STOCK = PALE.replace('Name="OnFocus" NormalColor="0xfff3f0ea" FocusColor="0xff0c0c0d" DisableColor="0xff8d8982"',
                     'Name="OnFocus" NormalColor="0xff000000" FocusColor="0xff000000" DisableColor="0xff888888"')   # the stock values
BIN = bytes(range(256)) * 40


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def mkzip(path, members):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in members:
            z.writestr(zipfile.ZipInfo(n, (2026, 11, 9, 0, 0, 0)), d)


def main():
    print('== fix_xml')
    x2, rows = M.fix_xml(PALE)
    d = dict(HM.colorset_list(x2))
    check(d[('OnFocus', 1)] == 'Normal=0xff0c0c0d Focus=0xff0c0c0d Disable=0xff8d8982', 'OnFocus -> ink / ink / dim: %s' % d[('OnFocus', 1)])
    check(d[('Default', 1)] == 'Normal=0xfff3f0ea Focus=0xa00c0c0d Disable=0xff8d8982', 'Default untouched')
    check(d[('Header', 1)] == 'Normal=0xfff0475a Focus=0xfff0475a Disable=0xff8c3138', 'Header untouched')
    check([r[4] for r in rows] == ['ink', 'already', 'already'], 'rows: normal changed, focus + disable already: %s' % [r[4] for r in rows])
    check(HM.signature(PALE) == HM.signature(x2) and len(HM.tags(PALE)) == len(HM.tags(x2)), 'table signature + tag count unchanged')
    check('RecCSFocus="OnFocus"' in x2 and 'ColorSet="OnFocus"' in x2, 'element references untouched')
    o2, orows = M.fix_xml(ONLINE)
    d = dict(HM.colorset_list(o2))
    check(d[('OnFocus', 1)] == 'Normal=0x800c0c0d Focus=0xff0c0c0d Disable=bogus', 'alpha 80 kept, malformed left: %s' % d[('OnFocus', 1)])
    check(d[('OnFocus', 2)].startswith('Normal=0xff0c0c0d Focus=0xff0c0c0d'), 'second definition fixed too: %s' % d[('OnFocus', 2)])
    check('DisableColor' not in o2.split('\n')[3], 'absent attribute NOT added (no new attribute)')
    hows = sorted(set(r[4] for r in orows))
    check(hows == ['absent', 'already', 'ink', 'malformed'], 'every outcome named: %s' % hows)
    x3, rows3 = M.fix_xml(x2)
    check(x3 == x2 and all(r[4] == 'already' for r in rows3), 'idempotent: a fixed file is all already')
    s2, srows = M.fix_xml(STOCK)
    check(s2 == STOCK and [r[4] for r in srows] == ['already'] * 3, 'stock black / black / 888888 = the same role: already, untouched')
    x4, rows4 = M.fix_xml('<Windows><Window Name="A"/></Windows>')
    check(rows4 == [], 'no OnFocus set -> no rows')

    print('== fake overlay + stage')
    tmp = tempfile.mkdtemp(prefix='klplates_')
    try:
        game = os.path.join(tmp, 'DD')
        ov = os.path.join(game, 'KLExpansion', 'Overlay')
        mkzip(os.path.join(ov, 'Patch01_deadmen.zip'), [('menu/frontend.xml', PALE), ('menu/ingame.xml', PALE), ('menu/bin.dat', BIN)])
        mkzip(os.path.join(ov, 'Patch01_rows12_deadmen.zip'), [('menu/frontend.xml', PALE.replace('FALobby', 'FALobby12')), ('Menu/Ingame.xml', PALE), ('x.bin', BIN)])
        mkzip(os.path.join(ov, 'Scenes', 'kaneandlynch_deadmen.zip'), [('Scenes/kaneandlynch.TEX', BIN), ('Menu/online.xml', ONLINE), ('menu/frontend.xml', PALE), ('menu/ingame.xml', PALE)])
        mkzip(os.path.join(ov, 'Patch01.zip'), [('menu/frontend.xml', STOCK), ('menu/ingame.xml', STOCK)])
        before = {n: md5(os.path.join(ov, n)) for n in ('Patch01_deadmen.zip', 'Patch01_rows12_deadmen.zip', os.path.join('Scenes', 'kaneandlynch_deadmen.zip'), 'Patch01.zip')}
        out = os.path.join(tmp, 'kit')
        files = M.stage(ov, out, accept=True, game=game, log=quiet)
        names = [f[0] for f in files]
        check(names == ['Patch01_deadmen.zip', 'Patch01_rows12_deadmen.zip', os.path.join('Scenes', 'kaneandlynch_deadmen.zip')], 'the three pale files staged, stock Patch01.zip skipped: %s' % names)
        check(all(f[1] == before[f[0]] for f in files), 'pins = the live md5s')
        check(all(md5(os.path.join(out, f[0])) == f[2] for f in files), 'staged md5s match')
        check(not os.path.exists(os.path.join(out, 'Patch01.zip')), 'no stage file for the already-ink one')
        pins = json.load(open(os.path.join(out, 'pins.json')))
        check(pins == before, 'pins.json holds every present file, the skipped one too')
        rep = json.load(open(os.path.join(out, 'build_report.json')))
        check(rep['want'] == ['0c0c0d', '0c0c0d', '8d8982'] and len(rep['files']) == 3, 'build_report: want + files')
        for n, members in dict(M.CANDIDATES).items():
            if n in names:
                M.verify_pair(os.path.join(ov, n), os.path.join(out, n), members)
        check(True, 'verify_pair passes on every staged file')
        with zipfile.ZipFile(os.path.join(out, 'Patch01_deadmen.zip')) as z:
            check(z.read('menu/bin.dat') == BIN and z.namelist() == ['menu/frontend.xml', 'menu/ingame.xml', 'menu/bin.dat'], 'binary member + order untouched')
            check(dict(HM.colorset_list(z.read('menu/ingame.xml').decode('latin-1')))[('OnFocus', 1)].startswith('Normal=0xff0c0c0d'), 'ingame.xml fixed too')
        with zipfile.ZipFile(os.path.join(out, 'Patch01_rows12_deadmen.zip')) as z:
            check('FALobby12' in z.read('menu/frontend.xml').decode('latin-1') and z.read('Menu/Ingame.xml') != PALE.encode('latin-1'), 'rows12: its own frontend, case-insensitive member name fixed')
        with zipfile.ZipFile(os.path.join(out, 'Scenes', 'kaneandlynch_deadmen.zip')) as z:
            check(z.read('menu/frontend.xml') == PALE.encode('latin-1') and z.read('menu/ingame.xml') == PALE.encode('latin-1'), 'scene: its frontend / ingame copies (shadowed by Patch01) left alone')
            check(dict(HM.colorset_list(z.read('Menu/online.xml').decode('latin-1')))[('OnFocus', 1)].startswith('Normal=0x800c0c0d'), 'scene: online.xml fixed')
        check(M.members_for(os.path.join(ov, 'Scenes', 'kaneandlynch_deadmen.zip')) == (HM.ONLINE,) and M.members_for(os.path.join(ov, 'Patch01.zip')) == (HM.FRONT, HM.INGAME), 'members_for by candidate name')
        check(M.check(out, ov, log=quiet), 'check() PASS on the fresh stage')
        # a tampered stage: another member differs -> verify_pair refuses
        bad = os.path.join(tmp, 'bad.zip')
        mkzip(bad, [('menu/frontend.xml', M.fix_xml(PALE)[0]), ('menu/ingame.xml', M.fix_xml(PALE)[0]), ('menu/bin.dat', BIN[::-1])])
        try:
            M.verify_pair(os.path.join(ov, 'Patch01_deadmen.zip'), bad, (HM.FRONT, HM.INGAME)); check(False, 'tampered member refused')
        except ValueError as e:
            check('differs' in str(e), 'tampered member refused: %s' % e)
        bad2 = os.path.join(tmp, 'bad2.zip')
        mkzip(bad2, [('menu/frontend.xml', M.fix_xml(PALE)[0].replace('0xff8d8982"/>\n  <ColorSet Name="Header"', '0xff000000"/>\n  <ColorSet Name="Header"', 1)), ('menu/ingame.xml', M.fix_xml(PALE)[0]), ('menu/bin.dat', BIN)])
        try:
            M.verify_pair(os.path.join(ov, 'Patch01_deadmen.zip'), bad2, (HM.FRONT, HM.INGAME)); check(False, 'an XML edit beyond OnFocus refused')
        except ValueError as e:
            check('only the OnFocus set' in str(e), 'an XML edit beyond OnFocus refused: %s' % e)
        check(M.fix_zip(os.path.join(ov, 'Patch01.zip'), os.path.join(tmp, 'nope.zip'), (HM.FRONT, HM.INGAME), log=quiet) is None and not os.path.exists(os.path.join(tmp, 'nope.zip')), 'fix_zip on an ink file -> None, nothing written')
        try:
            M.fix_zip(os.path.join(ov, 'Patch01.zip'), os.path.join(tmp, 'nope.zip'), (HM.ONLINE,), log=quiet); check(False, 'missing member refused')
        except ValueError as e:
            check('has no' in str(e), 'missing member refused')
        for p in (os.path.join(game, 'KL_PortBackup', 'Patch01.zip'), os.path.join(game, 'Patch01.zip'), os.path.join(game, 'Scenes', 'kaneandlynch.zip')):
            try:
                M.guard(p); check(False, 'guard refuses %s' % p)
            except SystemExit:
                check(True, 'guard refuses %s' % os.path.relpath(p, game))
        M.guard(os.path.join(ov, 'Scenes', 'kaneandlynch_deadmen.zip')); check(True, 'guard passes the overlay')
        # pins: a moved live file is refused without --accept-input
        mkzip(os.path.join(ov, 'Patch01_deadmen.zip'), [('menu/frontend.xml', PALE), ('menu/ingame.xml', PALE), ('menu/bin.dat', BIN + b'x')])
        try:
            M.stage(ov, out, accept=False, game=game, log=quiet); check(False, 'moved live file refused')
        except SystemExit as e:
            check('moved' in str(e), 'moved live file refused without --accept-input')
        mkzip(os.path.join(ov, 'Patch01_deadmen.zip'), [('menu/frontend.xml', PALE), ('menu/ingame.xml', PALE), ('menu/bin.dat', BIN)])
        files = M.stage(ov, out, accept=False, game=game, log=quiet)
        check(len(files) == 3, 're-stage on unchanged live files OK')

        print('== install.py round trip on the fake game folder')
        inst = os.path.join(out, 'install.py')
        run = lambda *a: subprocess.run([sys.executable, inst, '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
        r = run('--dry')
        check(r.returncode == 0 and r.stdout.count('would install') == 3, 'dry run lists 3 installs')
        check(all(md5(os.path.join(ov, n)) == before[n] for n in before), 'dry run wrote nothing')
        r = run()
        check(r.returncode == 0 and r.stdout.count('installed') == 3, 'install exit 0: %s' % r.stdout.strip().splitlines()[-1:])
        check(all(md5(os.path.join(ov, f[0])) == f[2] for f in files), 'live files are the staged ones')
        check(all(os.path.isfile(os.path.join(ov, f[0] + M.TAG)) and md5(os.path.join(ov, f[0] + M.TAG)) == f[1] for f in files), 'backups next to each file, byte-exact')
        check(md5(os.path.join(ov, 'Patch01.zip')) == before['Patch01.zip'] and not os.path.exists(os.path.join(ov, 'Patch01.zip' + M.TAG)), 'the skipped file untouched, no backup')
        r = run()
        check(r.returncode == 1 and 'REFUSED' in r.stdout and 'not the pinned' in r.stdout, 'second install refused (pin)')
        check(M.check(out, ov, log=quiet), 'check() on an installed stage: skip lines, PASS')
        r = run('--undo')
        check(r.returncode == 0 and r.stdout.count('restored') == 3, 'undo exit 0')
        check(all(md5(os.path.join(ov, n)) == before[n] for n in before), 'undo byte-exact on every file')
        check(not any(os.path.exists(os.path.join(ov, f[0] + M.TAG)) for f in files), 'backups gone after undo')
        r = run('--undo')
        check(r.returncode == 1 and 'no backup' in r.stdout, 'second undo refused')
        # stage after the fix went in: nothing pale -> no installer left behind
        for f in files:
            shutil.copyfile(os.path.join(out, f[0]), os.path.join(ov, f[0]))
        files2 = M.stage(ov, out, accept=True, game=game, log=quiet)
        check(files2 == [] and not os.path.exists(inst), 'a stage with every set ink stages nothing and removes the old install.py')
        # show: read-only
        vals = M.show(os.path.join(ov, 'Patch01_deadmen.zip'), log=quiet)
        check(set(vals) == {HM.FRONT, HM.INGAME} and all(r[3] == 'already' for rows in vals.values() for r in rows), 'show reads both members, all already')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\n%d checks, %d FAIL' % (NCHECK[0], len(fails)))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
