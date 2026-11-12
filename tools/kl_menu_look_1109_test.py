#!/usr/bin/env python3
"""
kl_menu_look_1109_test.py - self-test of tools/kl_menu_look_1109.py on SYNTHETIC data: no game file, no GDI, no network.

A fake overlay (Patch01.zip + Patch01_rows12.zip with menu/frontend.xml + menu/ingame.xml, Scenes/kaneandlynch.zip with Menu/online.xml,
a dummy .gms and an untouched binary member) is written into a temp folder and staged with --no-fonts; the colour mapping table, the chip /
px rule, the colour conversion, the pin logic, the table-signature proof, the widths report, install.py (install / undo / variant round trips
on a fake game folder) and check() are exercised. exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py.
"""
import io, json, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_look_1109 as M
import kl_hud_menu as HM

fails = []
NCHECK = [0]


def check(cond, what):
    NCHECK[0] += 1
    if cond:
        print('  ok   ' + what)
    else:
        print('  FAIL ' + what)
        fails.append(what)


def quiet(*_a, **_k):
    pass


FRONT = '''<Windows>
  <ColorSet Name="Default" NormalColor="0xffffffff" FocusColor="0xa00c0c0d" DisableColor="0xff808080"/>
  <ColorSet Name="White" NormalColor="0xffffffff" FocusColor="0xffffffff" DisableColor="0xff7f7f7f"/>
  <ColorSet Name="Header" NormalColor="0xffd7373a" FocusColor="0xffd7373a" DisableColor="0xff6e1d1f"/>
  <ColorSet Name="Legend" NormalColor="0xffffffff" FocusColor="0xffd00000" DisableColor="0xff808080"/>
  <ColorSet Name="Debug" NormalColor="0x80c0c0c0" FocusColor="0x80c0c0c0" DisableColor="0x80808080"/>
  <ColorSet Name="KLFocus" NormalColor="0xffffffff" FocusColor="0xffd7373a" DisableColor="0xff808080"/>
  <ColorSet Name="OnFocus" NormalColor="0xff000000" FocusColor="0xff000000" DisableColor="0xff888888"/>
  <ColorSet Name="Odd" NormalColor="0xff829ec1" FocusColor="0xffffffff" DisableColor="bogus"/>
  <ColorSet Name="Legend" NormalColor="0xffffffff" FocusColor="0xffd00000" DisableColor="0xff808080"/>
  <Template Name="HelpText_GT" Font="Text" X="1"/>
  <Window Name="MainMenu" Template="WindowDefault">
    <GuiElement Type="TextBlock" Name="A" Text="%Lens glare / cracks (cracks: next start)" Font="Text" ColorSet="Default"/>
    <GuiElement Type="TextBlock" Name="B" Text="%Hot Coffee" Font="Header"/>
    <GuiElement Type="TextBlock" Name="C" Text="%A long paragraph of help text that wraps" TextWidth="600" Font="Text"/>
    <GuiElement Type="ToggleText" Name="D" Text="%Adrenaline" Option="KLSAdren">
      <Text Text="%Stand by him + messages"/>
      <Text Text="%Hold E"/>
    </GuiElement>
  </Window>
</Windows>
'''
INGAME = '''<Windows>
  <ColorSet Name="Default" NormalColor="0xffffffff" FocusColor="0xa00c0c0d" DisableColor="0xff808080"/>
  <ColorSet Name="Debug" NormalColor="0x80c0c0c0" FocusColor="0x80c0c0c0" DisableColor="0x80808080"/>
  <Window Name="IngamePauseFA" Template="WindowDefault">
    <GuiElement Type="TextBlock" Name="P" Text="%Resume" Font="Menu"/>
  </Window>
</Windows>
'''
ONLINE = '''<Windows>
  <ColorSet Name="Default" NormalColor="0xffffffff" FocusColor="0xa00c0c0d" DisableColor="0xff808080"/>
  <ColorSet Name="WANTED" NormalColor="0xffe0e0e0" FocusColor="0xffe0e0e0" DisabledColor="0x00808080"/>
  <ColorSet Name="DirtyMoneyColorSet" NormalColor="0xffffffff" FocusColor="0xffffffff" DisabledColor="0xff808080"/>
  <ColorSet Name="Black" NormalColor="0xff000000" FocusColor="0xff000000" DisabledColor="0xff000000"/>
  <ColorSet Name="Default" NormalColor="0xff829ec1" FocusColor="0xffffffff" DisabledColor="0xff808080"/>
  <Window Name="FALobby" Template="WindowDefault">
    <GuiElement Type="TextBlock" Name="L" Text="%Ready" Font="Menu" ColorSet="Default"/>
  </Window>
</Windows>
'''


def make_zip(path, members):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(zipfile.ZipInfo(n, (2026, 11, 9, 0, 0, 0)), data)


def make_overlay(root, rows12=True):
    ov = os.path.join(root, 'KLExpansion', 'Overlay')
    patch = {'menu/frontend.xml': FRONT.encode('latin-1'), 'menu/ingame.xml': INGAME.encode('latin-1'), 'other.bin': b'\x01\x02\x03stock'}
    make_zip(os.path.join(ov, M.PATCH), patch)
    if rows12:
        p2 = dict(patch); p2['menu/frontend.xml'] = FRONT.replace('MainMenu', 'MainMenu').encode('latin-1')
        make_zip(os.path.join(ov, M.ROWS12), p2)
        os.utime(os.path.join(ov, M.ROWS12), None)
    make_zip(os.path.join(ov, M.SCENE), {'Scenes/kaneandlynch.gms': b'GMS', 'Menu/online.xml': ONLINE.encode('latin-1'), 'Scenes/kaneandlynch.oct': b'OCT'})
    return ov


def read_member(zp, name):
    with zipfile.ZipFile(zp) as z:
        return z.read(HM._member(z, name)).decode('latin-1')


def main():
    print('== colour conversion / mapping')
    check(M.argb('0xffd7373a') == (0xff, 0xd7, 0x37, 0x3a), 'argb parses 0xAARRGGBB')
    check(M.argb('bogus') is None and M.argb('0xffd7373') is None, 'malformed values parse to None')
    check(M.hexa((0xa0, 0x0c, 0x0c, 0x0d)) == '0xa00c0c0d', 'hexa writes 0xAARRGGBB lower case')
    new, how = M.color_for('Default', 1, 'FocusColor', (0xa0, 0x0c, 0x0c, 0x0d))
    check(new == (0xa0,) + M.COLORS['INK'] and how == 'name', 'Default #1 focus -> INK, alpha a0 kept, by name')
    new, how = M.color_for('Default', 2, 'NormalColor', (0xff, 0x82, 0x9e, 0xc1))
    check(new is None and how == 'kept', 'Default #2 (bluish) is LEFT ALONE')
    new, how = M.color_for('Header', 1, 'NormalColor', (0xff, 0xd7, 0x37, 0x3a))
    check(new == (0xff,) + M.COLORS['CORAL'] and how == 'name', 'Header -> CORAL by name')
    new, how = M.color_for('Odd', 1, 'FocusColor', (0xff, 0xff, 0xff, 0xff))
    check(new == (0xff,) + M.COLORS['CHALK'] and how == 'role', 'unknown set, white -> CHALK by role')
    new, how = M.color_for('Odd', 1, 'NormalColor', (0xff, 0x82, 0x9e, 0xc1))
    check(new is None and how == 'kept', 'unknown set, bluish -> left alone')
    new, how = M.color_for('Odd', 1, 'DisableColor', None)
    check(new is None and how == 'malformed', 'malformed value -> left alone, said so')
    new, how = M.color_for('Debug', 1, 'NormalColor', (0x80, 0xc0, 0xc0, 0xc0))
    check(new == (0xff,) + M.COLORS['GREEN_HI'], 'spare set Debug -> GREEN_HI with alpha ff on purpose')
    new, how = M.color_for('WANTED', 1, 'DisableColor', (0xff, 0, 0, 0))
    check(new == (0xff,) + M.COLORS['DEAD'], 'WANTED disable -> DEAD')
    for k, v in M.COLORSETS.items():
        check(all(c in M.COLORS for c in v['colors']) and v['alpha'] in ('keep', 'ff'), 'COLORSETS[%s] names palette colours' % k)
    check(set(M.COLORS) >= {'CHALK', 'CORAL', 'INK', 'AMBER', 'GREEN', 'DEAD', 'DIM'}, 'palette has the kit tokens')
    check(M.COLORS['CHALK'] == HM.CHALK and M.COLORS['INK'] == HM.INK and M.COLORS['CORAL'] == HM.CORAL, 'palette equals kl_hud_menu tokens')

    print('== restyle_colorsets on the synthetic XML')
    x2, rows = M.restyle_colorsets(FRONT)
    check(HM.signature(FRONT) == HM.signature(x2), 'frontend: table signature unchanged')
    check(len(HM.tags(FRONT)) == len(HM.tags(x2)), 'frontend: tag count unchanged')
    sets = HM.colorset_list(x2)
    d = dict(sets)
    check('Normal=0xfff3f0ea Focus=0xa00c0c0d Disable=0xff8d8982' == d[('Default', 1)], 'Default #1 = chalk / ink(a0) / dim: %s' % d[('Default', 1)])
    check('Normal=0xfff0475a Focus=0xfff0475a Disable=0xff8c3138' == d[('Header', 1)], 'Header = coral / coral / dead')
    check(d[('Legend', 2)] == d[('Legend', 1)] == 'Normal=0xfff3f0ea Focus=0xfff0475a Disable=0xff8d8982', 'both Legend definitions mapped alike')
    check('Normal=0xff63a65b Focus=0xff63a65b Disable=0xff4f8f49' == d[('Debug', 1)], 'Debug = green, alpha ff')
    check('Normal=0xff0c0c0d Focus=0xff0c0c0d Disable=0xff8d8982' == d[('OnFocus', 1)], 'OnFocus = ink / ink / dim (text ON a light plate; 11-10 pale-plate bug): %s' % d[('OnFocus', 1)])
    check(d[('Odd', 1)] == 'Normal=0xff829ec1 Focus=0xfff3f0ea Disable=bogus', 'Odd: bluish kept, white -> chalk, bogus kept: %s' % d[('Odd', 1)])
    hows = {r[5] for r in rows}
    check(hows == {'name', 'role', 'kept', 'malformed'}, 'every how occurs once at least: %s' % sorted(hows))
    o2, orows = M.restyle_colorsets(ONLINE)
    check(HM.signature(ONLINE) == HM.signature(o2), 'online: table signature unchanged')
    od = dict(HM.colorset_list(o2))
    check(od[('Default', 2)] == 'Normal=0xff829ec1 Focus=0xffffffff Disabled=0xff808080', 'online second Default untouched')
    w = od[('WANTED', 1)].split()
    check('Normal=0xffe8831f' in w and 'Focus=0xffe8831f' in w and 'Disable=0xff8c3138' in w, 'WANTED amber + a REAL DisableColor added: %s' % od[('WANTED', 1)])
    check('Disabled=0x00808080' in w, 'the misspelt DisabledColor is left as it stands')
    check(od[('Black', 1)].split().count('Normal=0xff0c0c0d') == 1 and 'Focus=0xff0c0c0d' in od[('Black', 1)].split() and 'Disable=0xff0c0c0d' in od[('Black', 1)].split(), 'Black = ink x3')
    check(x2.count('<ColorSet') == FRONT.count('<ColorSet') and o2.count('<ColorSet') == ONLINE.count('<ColorSet'), 'no ColorSet tag added or removed')

    print('== chip / px rule and font specs')
    check(M.chip_for(15, 0.5) == 0.0 and M.chip_for(16, 0.5) == 0.5 and M.chip_for(28, 0.3) == 0.3, 'chip_for: none under %d px' % M.CHIP_FLOOR)
    sp = M.font_specs('impact', have=lambda f: True)
    check(sp['Header'][0] == 'Impact' and sp['Header'][4] is True and sp['Header'][5] == 0.5, 'Header = Impact caps chip 0.5')
    check(sp['H3'][0] == 'Segoe UI Black' and sp['H3'][4] is False, 'H3 = body face, mixed case')
    check(sp['DebugText'][5] == 0.0 and sp['DebugText'][2] == 15, 'DebugText 15 px gets no chip (floor)')
    sp2 = M.font_specs('anton', have=lambda f: f in ('Anton', 'Montserrat'))
    check(sp2['Text'][0] == 'Anton' and sp2['H3'][0] == 'Montserrat', 'anton specs use the draft faces when installed')
    sp3 = M.font_specs('anton', have=lambda f: False)
    check(sp3['Text'][0] == 'Impact' and sp3['H3'][0] == 'Segoe UI Black', 'anton specs fall back to the stand-ins')
    try:
        M.font_specs('comic', have=lambda f: True); check(False, 'unknown face refused')
    except ValueError:
        check(True, 'unknown face refused')
    for slot, (_f, _w, px, _t, caps, chip) in sp.items():
        cap_stock = M.STOCK_CAP.get(slot, 0)
        check(px >= cap_stock, '%s: %d px >= stock capital %d (menus are not shrunk)' % (slot, px, cap_stock))
    check(all(sp[s][4] for s in ('Header', 'Menu', 'Text', 'Button')), 'display slots draw capitals')
    check(set(sp) == set(HM.MENU_SPECS), 'the eight slots are kl_hud_menu\'s eight')

    print('== widths report (advance tables faked)')
    adv_old = {ord(c): 8 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}; adv_old.update({ord(c): 6 for c in 'abcdefghijklmnopqrstuvwxyz'}); adv_old[32] = 4
    adv_new = {ord(c): 11 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}; adv_new[32] = 5
    check(M.text_width(adv_old, 'Ab c', False) == 8 + 6 + 4 + 6, 'text_width sums advances')
    check(M.text_width(adv_new, 'Ab c', True) == 11 + 11 + 5 + 11, 'text_width draws lower case as capitals when caps')
    saved = M.advance_table
    M.advance_table = lambda chunk: chunk
    try:
        lines = M.widths_report([FRONT], {'Text': adv_old, 'Header': adv_old}, {'Text': adv_new, 'Header': adv_new}, sp)
    finally:
        M.advance_table = saved
    check(lines[0].startswith('#') and len(lines) > 3, 'widths.txt has a header and rows')
    check('Lens glare' in '\n'.join(lines) and 'Stand by him' in '\n'.join(lines), 'the longest literals (element and <Text> child) are listed')
    body = [l for l in lines if not l.startswith('#')]
    pcs = [float(l.split('(')[1].split('%')[0]) for l in body]
    check(pcs == sorted(pcs, reverse=True), 'rows sorted by growth, worst first')
    lits = M.literals(FRONT)
    check(('Header', 'Hot Coffee') in lits and ('Text', 'Hold E') in lits, 'literals() carries the Font slot (default Text)')

    print('== stage on a synthetic overlay (no fonts)')
    root = tempfile.mkdtemp(prefix='menulook_test_')
    try:
        ov = make_overlay(root)
        out = os.path.join(root, 'build')
        try:
            M.stage(ov, out, accept=False, fonts=False, log=quiet); check(False, 'first stage without --accept-input refused')
        except ValueError as e:
            check('accept-input' in str(e), 'first stage without --accept-input refused: %s' % str(e)[:60])
        files = M.stage(ov, out, accept=True, fonts=False, log=quiet)
        sd = os.path.join(out, M.STAGE)
        check(sorted(n for n, _o, _w in files) == sorted([M.PATCH, M.ROWS12, M.SCENE]), 'three files staged (rows12 included)')
        check(os.path.isfile(os.path.join(sd, 'pins.json')) and os.path.isfile(os.path.join(sd, 'install.py')) and os.path.isfile(os.path.join(sd, 'build_report.json')), 'pins.json, install.py, build_report.json written')
        pins = json.load(open(os.path.join(sd, 'pins.json')))
        check(pins[M.PATCH] == M.fmd5(os.path.join(ov, M.PATCH)), 'pins.json holds the input md5s')
        check(all(o != w for _n, o, w in files), 'every staged file differs from its input')
        fx = read_member(os.path.join(sd, M.PATCH), HM.FRONT)
        check(HM.signature(fx) == HM.signature(FRONT), 'staged frontend.xml keeps the table signature')
        check('ColorSet Name="Header" NormalColor="0xfff0475a"' in fx, 'staged frontend.xml has coral Header')
        check('Name="HelpText_GT" Font="H3"' in fx and 'Name="C" Text="%A long paragraph of help text that wraps" TextWidth="600" Font="H3"' in fx, 'body re-point: template + wide TextBlock -> H3')
        check('Name="A" Text="%Lens glare / cracks (cracks: next start)" Font="Text"' in fx, 'short row keeps Font=Text')
        ix = read_member(os.path.join(sd, M.PATCH), HM.INGAME)
        check('Font="H3"' not in ix and 'NormalColor="0xff63a65b"' in ix, 'ingame.xml: colours only, no H3 (level HUD font)')
        with zipfile.ZipFile(os.path.join(sd, M.PATCH)) as z:
            check(z.read('other.bin') == b'\x01\x02\x03stock', 'untouched member byte-identical')
        sx = read_member(os.path.join(sd, M.SCENE), HM.ONLINE)
        check('Name="Default" NormalColor="0xff829ec1"' in sx and 'Name="Default" NormalColor="0xfff3f0ea"' in sx, 'scene online.xml: first Default chalk, second kept')
        check(not M.check(sd, ov, log=quiet), 'check() PASS on the fresh stage')
        # second run without --accept-input: pins match
        M.stage(ov, out, accept=False, fonts=False, log=quiet)
        check(True, 'second stage without --accept-input accepted (pins match)')
        # the input changes -> refused
        make_zip(os.path.join(ov, M.PATCH), {'menu/frontend.xml': FRONT.replace('Hot Coffee', 'Hot Coffee II').encode('latin-1'), 'menu/ingame.xml': INGAME.encode('latin-1'), 'other.bin': b'x'})
        try:
            M.stage(ov, out, accept=False, fonts=False, log=quiet); check(False, 'changed input refused')
        except ValueError as e:
            check('pinned' in str(e), 'changed input refused without --accept-input')
        bad = M.check(sd, ov, log=quiet)
        check(any('not the pin' in b for b in bad), 'check() FAILs on a changed input: %s' % bad[:1])
        make_overlay(root)                                # back to the original inputs (same bytes: same stamps)
        check(not M.check(sd, ov, log=quiet), 'check() PASS again with the inputs restored')
        # a tampered stage (an element added) fails the signature proof
        tam = os.path.join(root, 'tamper.zip')
        with zipfile.ZipFile(os.path.join(sd, M.PATCH)) as z, zipfile.ZipFile(tam, 'w') as o:
            for i in z.infolist():
                data = z.read(i)
                if i.filename == 'menu/frontend.xml':
                    data = data.replace(b'</Window>', b'<GuiElement Type="TextBlock" Name="X" Text="%x"/></Window>')
                o.writestr(i, data)
        shutil.copyfile(os.path.join(sd, M.PATCH), os.path.join(root, 'good.zip'))
        shutil.copyfile(tam, os.path.join(sd, M.PATCH))
        bad = M.check(sd, ov, log=quiet)
        check(any('signature' in b for b in bad), 'check() FAILs on a table shift: %s' % bad[:1])
        shutil.copyfile(os.path.join(root, 'good.zip'), os.path.join(sd, M.PATCH))
        # rows12 older than Patch01 -> warned by check
        os.utime(os.path.join(ov, M.ROWS12), (1000000000, 1000000000))
        bad = M.check(sd, ov, log=quiet)
        check(any('older' in b for b in bad), 'check() names a rows12 older than Patch01.zip')
        check(M.rows12_ok(ov) is False, 'rows12_ok False when older')
        os.utime(os.path.join(ov, M.ROWS12), None)
        check(M.rows12_ok(ov), 'rows12_ok True when newer')
        # an overlay without rows12 stages two files
        root2 = tempfile.mkdtemp(prefix='menulook_test2_')
        try:
            ov2 = make_overlay(root2, rows12=False)
            f2 = M.stage(ov2, os.path.join(root2, 'build'), accept=True, fonts=False, log=quiet)
            check(sorted(n for n, _o, _w in f2) == sorted([M.PATCH, M.SCENE]), 'without rows12: two files staged')
            check(M.rows12_ok(ov2), 'rows12_ok True when absent')
        finally:
            shutil.rmtree(root2, ignore_errors=True)
        # members_ok refuses a changed member outside the allowed set
        try:
            M.members_ok(os.path.join(ov, M.PATCH), os.path.join(root, 'tamper2.zip') if False else os.path.join(ov, M.PATCH))
            check(True, 'members_ok: identical archives -> no change')
        except ValueError:
            check(False, 'members_ok: identical archives -> no change')
        with zipfile.ZipFile(os.path.join(root, 'bad.zip'), 'w') as o, zipfile.ZipFile(os.path.join(ov, M.PATCH)) as z:
            for i in z.infolist():
                o.writestr(i, b'changed' if i.filename == 'other.bin' else z.read(i))
        try:
            M.members_ok(os.path.join(ov, M.PATCH), os.path.join(root, 'bad.zip')); check(False, 'members_ok refuses a changed binary member')
        except ValueError:
            check(True, 'members_ok refuses a changed binary member')
        # inventory runs (log captured)
        buf = []
        M.inventory(ov, log=buf.append)
        txt = '\n'.join(buf)
        check('Default' in txt and 'kept' in txt and 'colour sets' in txt, 'inventory lists the sets and their fate')

        print('== install.py round trips on the fake game folder')
        inst = os.path.join(sd, 'install.py')
        run = lambda *args: subprocess.run([sys.executable, inst, '--game', root, '--skip-run-check'] + list(args), capture_output=True, text=True)
        r = run('--dry')
        check(r.returncode == 0 and 'would install' in r.stdout, '--dry prints the plan: %s' % r.stdout.strip().splitlines()[-1][:70])
        before = {n: M.fmd5(os.path.join(ov, n)) for n, _o, _w in files}
        r = run()
        check(r.returncode == 0, 'install exit 0: %s' % r.stdout.strip().splitlines()[-1][:70])
        for n, o, w in files:
            check(M.fmd5(os.path.join(ov, n)) == w and os.path.isfile(os.path.join(ov, n + M.TAG)) and M.fmd5(os.path.join(ov, n + M.TAG)) == o, '%s installed, backup = original' % n)
        check(os.path.getmtime(os.path.join(ov, M.ROWS12)) >= os.path.getmtime(os.path.join(ov, M.PATCH)), 'rows12 written after Patch01.zip (not older)')
        r = run()
        check(r.returncode == 1 and 'REFUSED' in r.stdout, 'second install refused (already installed)')
        r = run('--undo')
        check(r.returncode == 0, 'undo exit 0')
        for n, o, w in files:
            check(M.fmd5(os.path.join(ov, n)) == before[n] and not os.path.exists(os.path.join(ov, n + M.TAG)), '%s restored byte-exact, backup gone' % n)
        r = run('--undo')
        check(r.returncode == 1 and 'REFUSED' in r.stdout, 'undo without an install refused')
        # a live file that is not the pin -> refused, nothing written
        shutil.copyfile(os.path.join(root, 'bad.zip'), os.path.join(ov, M.PATCH))
        r = run()
        check(r.returncode == 1 and 'REFUSED' in r.stdout and not os.path.exists(os.path.join(ov, M.SCENE + M.TAG)), 'wrong live md5: refused, no backup made')
        make_overlay(root)
        # variant mode
        r = run('--variant')
        var = os.path.join(ov, 'Patch01' + M.VARIANT + '.zip')
        check(r.returncode == 0 and os.path.isfile(var) and M.fmd5(var) == dict((n, w) for n, _o, w in files)[M.PATCH], '--variant writes Patch01_deadmen.zip beside the live file')
        check(os.path.isfile(os.path.join(ov, 'Scenes', 'kaneandlynch' + M.VARIANT + '.zip')) and os.path.isfile(os.path.join(ov, 'Patch01_rows12' + M.VARIANT + '.zip')), 'variants for rows12 and the scene too')
        check(M.fmd5(os.path.join(ov, M.PATCH)) == before[M.PATCH], '--variant leaves the live file alone')
        r = run('--variant')
        check(r.returncode == 1, 'a second --variant refuses (exists)')
        r = run('--variant', '--undo')
        check(r.returncode == 0 and not os.path.exists(var), '--variant --undo removes the variants')
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print('\n%d checks, %d FAIL' % (NCHECK[0], len(fails)))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
