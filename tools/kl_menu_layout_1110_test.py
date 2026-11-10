#!/usr/bin/env python3
"""
kl_menu_layout_1110_test.py - self-test of tools/kl_menu_layout_1110.py on SYNTHETIC data: no game file, no GDI, no network.

A fake _deadmen set (Patch01_deadmen.zip + Patch01_rows12_deadmen.zip with menu/frontend.xml + menu/ingame.xml, Scenes/kaneandlynch_deadmen.zip
with Menu/online.xml, a dummy .gms and an untouched binary member) shaped like the live windows of re/menu_inventory_1110/frontend_rows12.md is
written into a temp folder: the parser, the coordinate model, plan / stage / check round trip, the refusals (out of bounds, text overlap, unknown
picture, bad selector, template used elsewhere, pins), stage without --dm (art skipped with a log line), the contact sheet, install.py
(install / undo / second install refused on a fake game folder), the art record shapes and the Dead Men inventory reader.
exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py.
"""
import copy, json, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_layout_1110 as L
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


TEMPLATES = '''
  <ColorSet Name="Default" NormalColor="0xfff3f0ea" FocusColor="0xff0c0c0d" DisableColor="0xff8d8982"/>
  <Template Name="WindowDefault" ScaleToViewPort="True"/>
  <Template Name="ScreenBaseSize" Type="GUIGroup" X="0" Y="0" W="768" H="576" AlignH="Center" AlignV="Center"/>
  <Template Name="MM_Button" Type="OpenWindow" X="300" AlignH="Left" Font="Text"/>
  <Template Name="MM_FocusBar" Type="Graphic" X="290" AlignH="Left" Priority="5"/>
  <Template Name="FocusBar" Type="Graphic" Priority="5"/>
  <Template Name="HeadlineIcon" Type="Graphic" X="-127" Y="0"/>
  <Template Name="HeadlineText" Type="TextBlock" X="-85" Y="6" Font="Header"/>
  <Template Name="LevelPictureGroup_T" Type="GUIGroup" X="0" Y="0" W="384" H="576" AlignH="Left"/>
  <Template Name="LevelPicture_T" Type="Graphic" X="-117" Y="60" AlignH="Left" AlignV="Top" Priority="5"/>
  <Template Name="LobbyLevelPicture_T" Type="Graphic" X="-117" Y="60" AlignH="Left" AlignV="Top" Priority="5"/>
  <Template Name="TextIndentX" Type="ToggleText" AlignV="Left"/>
  <Template Name="OptionsArrowL_T" Type="SendMessage" AlignH="Left"/>
  <Template Name="OptionsArrowR_T" Type="SendMessage" AlignH="Right"/>
  <Template Name="OptionButton" Type="OpenWindow" Font="Text"/>
  <Template Name="Line" Type="MercsGraphic" X="0" Y="0" Priority="3"/>
  <Template Name="PCBackgroundTemplate">
    <GuiElement Template="ScreenBaseSize">
      <GuiElement Type="Graphic" X="-142" Y="308" Priority="1" Graphic="BlackBandErrorBackground2"/>
    </GuiElement>
  </Template>
  <Template Name="GameLogoTemplatePCMain">
    <GuiElement Template="PCBackgroundTemplate"/>
    <ExcludeIn Demo="True">
      <GuiElement Type="Graphic" X="-130" Y="320" Graphic="GameLogo"/>
    </ExcludeIn>
    <ExcludeIn Normal="True">
      <GuiElement Type="Graphic" X="-130" Y="320" Graphic="GameLogoDemo"/>
    </ExcludeIn>
  </Template>
  <Template Name="LobbyBackgroundTemplate">
    <GuiElement Type="Graphic" X="-127" Y="50" Priority="2" Graphic="LobbyBackground"/>
  </Template>
'''


def guns_rows(names):
    rows = ['    <GuiElement Type="GUIGroup" Name="KLG_CenterBox" X="-100" Y="-80" W="384" H="576" AlignH="Right">']
    for k, n in enumerate(names):
        rows.append('      <GuiElement Type="TextBlock" Name="%s_Data" Y="%d" AlignH="Center"/>' % (n, 301 + 34 * k))
    rows.append('    </GuiElement>')
    rows.append('    <GuiElement Type="GUIGroup" Name="KLG_CenterBoxArrows" X="484" Y="-80" W="384" H="576">')
    for k in range(len(names)):
        rows.append('      <GuiElement Template="OptionsArrowL_T" X="0" Y="%d"/>' % (293 + 34 * k))
    for k in range(len(names)):
        rows.append('      <GuiElement Template="OptionsArrowR_T" X="0" Y="%d"/>' % (293 + 34 * k))
    rows.append('    </GuiElement>')
    for k, n in enumerate(names):
        rows.append('    <GuiElement Template="TextIndentX" Name="%s" X="-100" Y="%d" ColorSet="KLFocus" Text="%%Row %s"><Text Text="%%Off"/><Text Text="%%On"/></GuiElement>' % (n, 221 + 34 * k, n))
    return '\n'.join(rows)


def frontend(rows12):
    guns = ['KLS_Look', 'KLS_Cam', 'KLS_Glare'] + ([] if rows12 else ['KLS_More'])
    return '<Windows>' + TEMPLATES + '''
  <Window Name="MainMenu" Template="WindowDefault">
    <GuiElement Template="ScreenBaseSize" X="2" Y="5">
      <GuiElement Type="Graphic" Name="InfocastGfxLeft1" X="-130" Y="42" Graphic="InfocastLeft"/>
      <GuiElement Type="MercsShowInfoFAInfocast" X="-119" Y="50" AlignH="Left" Font="Text"/>
    </GuiElement>
    <GuiElement Template="ScreenBaseSize" X="16" Y="24">
      <Platform PC="True">
        <GuiElement Template="GameLogoTemplatePCMain"/>
      </Platform>
      <GuiElement Template="ScreenBaseSize" X="130" Y="144">
        <GuiElement Type="Graphic" X="250" Y="177" Graphic="Icon_Campaign"/>
        <GuiElement Type="Graphic" X="250" Y="211" Graphic="Icon_Heist"/>
        <GuiElement Type="Graphic" X="250" Y="245" Graphic="Icon_Multiplayer"/>
        <GuiElement Type="Graphic" X="250" Y="279" Graphic="Icon_Achievements"/>
        <GuiElement Type="Graphic" X="250" Y="313" Graphic="Icon_Options"/>
        <GuiElement Template="Line" Graphic="Line_Short_01#01"/>
        <Platform PC="True">
          <GuiElement Type="Graphic" X="250" Y="344" Graphic="Icon_Quit"/>
        </Platform>
        <GuiElement Template="MM_Button" Name="Button_Play" Y="186" ColorSet="Default" Text="Button_Play" FocusGraphic="MMfb#01"/>
        <GuiElement Template="MM_Button" Name="Button_Heist" Y="220" Text="Button_HeistMode" FocusGraphic="MMfb#02"/>
        <GuiElement Template="MM_Button" Name="Button_Online" Y="254" Text="Button_Online" FocusGraphic="MMfb#03"/>
        <Platform PC="True">
          <GuiElement Template="MM_Button" Type="ZOnlyOneController" Name="Button_Achievements" Y="288" Text="Button_Achievements_pc" FocusGraphic="MMfb#04"/>
        </Platform>
        <Platform XENON="True">
          <GuiElement Template="MM_Button" Type="ZOnlyOneController" Name="Button_Achievements" Y="288" Text="Button_Achievements" FocusGraphic="MMfb#04"/>
        </Platform>
        <GuiElement Template="MM_Button" Name="Button_Options" Y="322" Text="Button_Settings" FocusGraphic="MMfb#05"/>
        <Platform PC="True">
          <GuiElement Template="MM_Button" Name="Button_Quit" Y="356" ColorSet="Default" Text="Button_QuitGame" FocusGraphic="MMfb#06"/>
        </Platform>
        <GuiElement Template="MM_FocusBar" Name="MMfb#01" Y="177" Graphic="FocusBar_short#01"/>
        <GuiElement Template="MM_FocusBar" Name="MMfb#02" Y="211" Graphic="FocusBar_short#02"/>
        <GuiElement Template="MM_FocusBar" Name="MMfb#03" Y="245" Graphic="FocusBar_short#03"/>
        <GuiElement Template="MM_FocusBar" Name="MMfb#04" Y="279" Graphic="FocusBar_short#04"/>
        <GuiElement Template="MM_FocusBar" Name="MMfb#05" Y="313" Graphic="FocusBar_short#05"/>
        <GuiElement Template="MM_FocusBar" Name="MMfb#06" Y="347" Graphic="FocusBar_short#06"/>
      </GuiElement>
    </GuiElement>
  </Window>
  <Window Name="HeistPlayMenu" Template="WindowDefault">
    <GuiElement Template="ScreenBaseSize">
      <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>
      <GuiElement Template="HeadlineText" Name="PMHeadline" Text="HeistTitle"/>
      <GuiElement Template="LevelPictureGroup_T">
        <GuiElement Template="LevelPicture_T" Name="H01_LevelPicture" Graphic="LevelPicture_H01"/>
        <GuiElement Template="LevelPicture_T" Name="H02_LevelPicture" Graphic="LevelPicture_H02"/>
      </GuiElement>
      <GuiElement Type="TextBlock" Name="HeistBriefingTextBlock" X="450" Y="64" W="300" H="400" AlignH="Left" Font="Text"/>
      <GuiElement Type="Graphic" X="445" Y="268" AlignH="Left" Priority="5" Graphic="FocusBar_medium_05#02"/>
      <GuiElement Type="TextBlock" X="460" Y="276" ColorSet="OnFocus" Text="/Menu/Online/Leaderboard/CriminalName"/>
      <GuiElement Template="FocusBar" Name="HPMfb#01" X="-122" Y="383" AlignH="Left" Graphic="FocusBar_long#01"/>
      <GuiElement Type="MercsLevelSelectorHeist" Name="HeistLevel" X="-100" Y="392" AlignV="Left" Text="HeistLevel" FocusGraphic="HPMfb#01"><Text Text="%Subway"/><Text Text="%A Walk in the Park II"/></GuiElement>
      <GuiElement Type="MercsShowInfoFA" X="0" Y="450" AlignH="Center" ColorSet="Header"/>
    </GuiElement>
  </Window>
  <Window Name="KLGuns" Template="WindowDefault">
    <GuiElement Template="ScreenBaseSize">
    <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>
    <GuiElement Template="HeadlineText" Text="%Mod settings"/>
''' + guns_rows(guns) + '''
    </GuiElement>
  </Window>
  <Window Name="OptionsMenu" Template="OptionsWindowDefault">
    <GuiElement Template="ScreenBaseSize">
      <GuiElement Template="OptionButton" X="-110" Y="122" Text="Button_GameSetting"/>
      <GuiElement Template="OptionButton" X="-110" Text="Button_Video"/>
    </GuiElement>
  </Window>
  <Window Name="FALobby" Template="WindowDefault">
    <GuiElement Template="ScreenBaseSize">
      <GuiElement Template="LobbyBackgroundTemplate"/>
      <GuiElement Template="LevelPictureGroup_T">
        <GuiElement Template="LobbyLevelPicture_T" Name="LobbyPictureF01" Graphic="LobbyMap_DM01"/>
        <GuiElement Template="LobbyLevelPicture_T" Name="LobbyPictureF02" Graphic="LobbyMap_DM02"/>
      </GuiElement>
      <GuiElement Type="Graphic" Name="LobbyOptionsFB#01" X="218" Y="56" AlignH="Left" Priority="5" Graphic="FocusBar_Medium_03#01"/>
      <GuiElement Type="TextBlock" Name="Headline0" X="-60" Y="268" ColorSet="OnFocus" Text="/Menu/Online/Profile/GamerTag"/>
    </GuiElement>
  </Window>
  <Window Name="TooManyPlayersSignedIn" Template="WindowDefault">
    <GuiElement Template="Kane"/>
  </Window>
</Windows>
'''


INGAME = '<Windows>\n  <ColorSet Name="Default" NormalColor="0xffffffff" FocusColor="0xa00c0c0d" DisableColor="0xff808080"/>\n  <Window Name="IngamePauseFA" Template="WindowDefault">\n    <GuiElement Type="TextBlock" Name="P" Text="%Resume" Font="Menu"/>\n  </Window>\n</Windows>\n'
ONLINE = '<Windows>\n  <ColorSet Name="Default" NormalColor="0xffffffff" FocusColor="0xa00c0c0d" DisableColor="0xff808080"/>\n  <Window Name="FAWaitForPlayers" Template="WindowDefault">\n    <GuiElement Type="TextBlock" Name="W" Text="%Waiting" Font="Text"/>\n  </Window>\n</Windows>\n'


def write_set(d):
    os.makedirs(os.path.join(d, 'Scenes'), exist_ok=True)
    for name, rows12 in ((L.PATCH, False), (L.ROWS12, True)):
        with zipfile.ZipFile(os.path.join(d, name), 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('menu/frontend.xml', frontend(rows12).encode('latin-1'))
            z.writestr('menu/ingame.xml', INGAME.encode('latin-1'))
            z.writestr('menu/blob.bin', b'\x00\x01\x02binary' * 50)
    with zipfile.ZipFile(os.path.join(d, L.SCENE), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('Scenes/kaneandlynch.gms', b'NOT A SCENE' * 10)
        z.writestr('Menu/online.xml', ONLINE.encode('latin-1'))
        z.writestr('menu/frontend.xml', frontend(False).encode('latin-1'))
        z.writestr('Scenes/kaneandlynch.TEX', b'\x00' * 64)
    os.utime(os.path.join(d, L.PATCH), (1700000000, 1700000000))


def md5(p):
    import hashlib
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    tmp = tempfile.mkdtemp(prefix='kl_menu_layout_test_')
    try:
        run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('%s: %d checks, %d FAIL' % ('PASS' if not fails else 'FAIL', NCHECK[0], len(fails)))
    for f in fails:
        print('  - ' + f)
    return 1 if fails else 0


def run(tmp):
    xml = frontend(True)
    # ---- parser: the inventory's numbering (document order, nested counted, template bodies as pseudo-windows)
    wins, tpls, order = L.parse_windows(xml)
    print('-- parser')
    check('MainMenu' in wins and 'Template:GameLogoTemplatePCMain' in wins and 'Template:LobbyBackgroundTemplate' in wins, 'windows and template bodies found')
    mm = wins['MainMenu']
    play = [e for e in mm if e.name == 'Button_Play'][0]
    check(play.eff.get('X') == '300' and play.own.get('Y') == '186' and play.type == 'OpenWindow', 'template chain resolved (MM_Button X 300, own Y)')
    check(play.parent is not None and play.parent.own.get('X') == '130' and play.parent.parent.own.get('X') == '16', 'parents: group 8 inside group 5')
    ach = [e for e in mm if e.name == 'Button_Achievements']
    check(len(ach) == 2 and ach[0].cond != ach[1].cond, 'platform copies carry their cond')
    check(L.template_users(wins, 'GameLogoTemplatePCMain') == ['MainMenu'], 'template users: GameLogoTemplatePCMain <- MainMenu')
    check(L.template_users(wins, 'LobbyBackgroundTemplate') == ['FALobby'], 'template users: LobbyBackgroundTemplate <- FALobby')

    # ---- the coordinate model
    print('-- model')
    model = L.Model()
    sbs = [e for e in wins['HeistPlayMenu'] if e.own.get('Template') == 'ScreenBaseSize'][0]
    check(model.group_box(wins['HeistPlayMenu'], sbs)[:2] == (256.0, 72.0), 'ScreenBaseSize group at (256, 72)')
    g8 = play.parent
    check(model.group_box(mm, g8)[:2] == (402.0, 240.0), 'nested groups add their X / Y: group 8 at (402, 240)')
    b = model.elem_box(mm, play)
    check(b is not None and round(b[0]) == 702 and round(b[1]) == 426 and b[4] == 'text', 'Button_Play box (702, 426) text: %s' % L._fmt(b))
    kg = wins['KLGuns']
    cb = [e for e in kg if e.name == 'KLG_CenterBox'][0]
    check(model.group_box(kg, cb)[:2] == (740.0, -8.0), 'AlignH Right: CenterBox X=-100 W=384 -> x 740')
    bar = [e for e in mm if e.name == 'MMfb#01'][0]
    bb = model.elem_box(mm, bar)
    check(bb is not None and bb[4] == 'pic' and bb[2] == 1024 and L.inside(bb, 'FocusBar_short#01') and not L.inside(bb, 'LevelPicture_H01'), 'a 1024-wide strip counts by its left / top only')
    check(model.pic_size('LobbyMap_DM02') == (325, 183) and model.pic_size('Background_Kane') == (474, 720) and model.pic_size('Nope') is None, 'picture sizes by name / prefix')
    w, px = model.measure('Hot Coffee', 'Header')
    check(px == 28 and abs(w - 0.55 * 28 * 10) < 1e-6, 'estimated width without a font table')
    opt = wins['OptionsMenu']
    check(model.elem_box(opt, opt[2]) is not None and model.elem_box(opt, opt[2])[1] == 72.0, 'an element with X only reads Y as 0 (the _Data cells carry only Y)')
    nox = [e for e in wins['FALobby'] if e.own.get('Template') == 'LobbyBackgroundTemplate'][0]
    check(model.elem_box(wins['FALobby'], nox) is None, 'an element with neither X nor Y has no box')
    check(L.overlap((0, 0, 10, 10), (5, 5, 10, 10)) and not L.overlap((0, 0, 10, 10), (10, 0, 10, 10)), 'overlap rule')

    # ---- the plan on the fake set
    print('-- plan')
    sd = os.path.join(tmp, 'set'); write_set(sd)
    lines = []
    allc, allp, alln, _m = L.plan(sd, None, None, lines.append)
    check(not allp, 'plan OK on the synthetic set (%s)' % allp[:2])
    ch = allc[L.PATCH]
    names = {repr(c.el).split('(')[1][:-1] for c in ch['MainMenu']}
    check({'Button_Play', 'Button_Quit', 'MMfb#01', 'Icon_Multiplayer'} <= names and 'Icon_Campaign' not in names, 'MainMenu: rows + bars + blanked icons planned, portraits art-dependent and skipped: %s' % sorted(names))
    play_c = [c for c in ch['MainMenu'] if c.el is [e for e in wins['MainMenu'] if e.name == 'Button_Play'][0] or c.el.name == 'Button_Play'][0]
    check(round(play_c.new_box[0]) == 150 and round(play_c.new_box[1]) == 300, 'Button_Play lands at (150, 300): %s' % L._fmt(play_c.new_box))
    check(any('NOT written' in n and 'Background_Kane' in n for n in alln), 'art-dependent entries noted as not written without the art')
    check(any('Template:GameLogoTemplatePCMain: used by MainMenu' in n for n in alln), 'template users listed')
    logo = [c for c in ch['Template:GameLogoTemplatePCMain']]
    check(len(logo) == 2 and all(round(c.new_box[0]) == 64 and round(c.new_box[1]) == 40 for c in logo), 'logo at (64, 40) through the template-body origin')
    kgc = ch['KLGuns']
    check(len(kgc) == 4 and all(c.attrs == dict(X=-136, Y=221 + 34 * k) for k, c in enumerate(kgc)), 'KLGuns at the stock pitch 34: only the 4 labels move (X): %d changes' % len(kgc))
    check(len(allc[L.ROWS12]['KLGuns']) == 3, 'rows rule follows each file\'s own row count (rows12: 3 rows)')
    saved = copy.deepcopy(L.LAYOUT)
    try:
        L.LAYOUT['KLGuns']['rows']['pitch'] = 36
        c36, p36, _n, _m = L.plan(sd, None, None, quiet)
        k36 = c36[L.PATCH]['KLGuns']
        # row 0 keeps its y (y0 = the stock 221): its data cell and arrows do not change; every label moves (X)
        check(not p36 and len(k36) == 4 * 4 - 3, 'pitch 36: 4 rows x (label, data, 2 arrows) - 3 unchanged = %d changes' % len(k36))
        lab = [c for c in k36 if c.el.name == 'KLS_More'][0]
        check(lab.attrs == dict(X=-136, Y=221 + 3 * 36), '4th row at y0 + 3 x pitch')
        dat = [c for c in k36 if c.el.name == 'KLS_More_Data'][0]
        check(dat.attrs == dict(Y=221 + 3 * 36 + 80) and dat.new_box[4] == 'text' and round(dat.new_box[0] + dat.new_box[2] / 2) == 932, 'its data cell 80 below, centred in the right column (x 932)')
        arr = [c for c in k36 if c.el.own.get('Template') == 'OptionsArrowR_T']
        check(len(arr) == 3 and all(c.new_box[4] == 'arrow' for c in arr), 'arrows re-pitched, not measured as text')
    finally:
        L.LAYOUT = saved
    check(not ch['OptionsMenu'], 'OptionsMenu: nothing moved')
    check(any('GUESS list' in s for s in lines) and any('REFUSED' not in s for s in lines), 'plan prints the GUESS list')
    allc_dm, allp_dm, alln_dm, _m = L.plan(sd, 'fake.zip', None, quiet)
    check(not allp_dm and any(c.art and c.attrs.get('Graphic') == 'Background_Kane' for c in allc_dm[L.PATCH]['MainMenu']), 'with --dm the portrait re-points are planned')
    check(any(c.attrs.get('Graphic') == 'Background_FABag' for c in allc_dm[L.PATCH]['Template:LobbyBackgroundTemplate']), 'with --dm the lobby plate -> FABag')

    # ---- refusals (LAYOUT patched, then restored)
    print('-- refusals')
    saved = copy.deepcopy(L.LAYOUT)
    try:
        L.LAYOUT['MainMenu']['elements']['Button_Play'] = dict(X=2000, Y=10)
        _c, p1, _n, _m = L.plan(sd, None, None, quiet)
        check(any('leaves the screen' in x for x in p1), 'out of bounds refused: %s' % p1[:1])
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['MainMenu']['elements']['Button_Play'] = dict(X=L._MMX, Y=L._MMY + 44)   # onto Button_Heist's row
        _c, p2, _n, _m = L.plan(sd, None, None, quiet)
        check(any('would overlap' in x and 'Button_Play' in x for x in p2), 'text overlap refused: %s' % p2[:1])
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['MainMenu']['elements']['pic:Icon_Options'] = dict(Graphic='NoSuchPicture', X=0, Y=0)
        _c, p3, _n, _m = L.plan(sd, None, None, quiet)
        check(any('NoSuchPicture' in x for x in p3), 'unknown Graphic= refused')
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['MainMenu']['elements']['pic:Icon_Heist'] = dict(Priority=9, X=0, Y=0)
        _c, p4, _n, _m = L.plan(sd, None, None, quiet)
        check(any('not layout attributes' in x for x in p4), 'a non-layout attribute refused')
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['MainMenu']['elements']['NoSuchName'] = dict(X=0, Y=0)
        L.LAYOUT['MainMenu']['elements']['pic:FocusBar_short#01'] = dict(X=0, Y=0)
        _c, p5, _n, _m = L.plan(sd, None, None, quiet)
        check(any('no element of that name' in x for x in p5), 'unknown name selector refused')
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['Template:GameLogoTemplatePCMain']['used_by'] = ('Credits',)
        _c, p6, _n, _m = L.plan(sd, None, None, quiet)
        check(any('is also used by' in x for x in p6), 'a template body used by an unlisted window refused')
        L.LAYOUT = copy.deepcopy(saved)
        L.LAYOUT['KLGuns']['rows']['data_group'] = 'Nope'
        _c, p7, _n, _m = L.plan(sd, None, None, quiet)
        check(any('rows: group' in x for x in p7), 'rows rule with a missing group refused')
    finally:
        L.LAYOUT = saved
    _c, p0, _n, _m = L.plan(sd, None, None, quiet)
    check(not p0, 'LAYOUT restored')

    # ---- stage
    print('-- stage')
    out = os.path.join(tmp, 'layout')
    try:
        L.stage(sd, out, accept=False, log=quiet); check(False, 'stage without pins refused')
    except ValueError as e:
        check('accept-input' in str(e), 'stage without pins refused: %s' % str(e)[:60])
    lines = []
    files = L.stage(sd, out, accept=True, log=lines.append)
    check(len(files) == 3 and all(os.path.isfile(os.path.join(out, n)) for n, _o, _w in files), 'three files staged')
    check(any('Dead Men art SKIPPED (no --dm)' in s for s in lines), 'without --dm the art step logs its skip')
    check(os.path.isfile(os.path.join(out, 'contact_layout.png')) and os.path.getsize(os.path.join(out, 'contact_layout.png')) > 1000, 'contact_layout.png written')
    try:
        from PIL import Image
        im = Image.open(os.path.join(out, 'contact_layout.png')).convert('RGB')
        PW = 640
        before = im.crop((16, 0, 16 + PW, im.height)); after = im.crop((32 + PW, 0, 32 + 2 * PW, im.height))
        coral = sum(1 for px in after.tobytes()[0::3][0:0]) + after.tobytes().count(bytes((240, 71, 90))); coral0 = before.tobytes().count(bytes((240, 71, 90)))
        check(coral > 200 and coral0 == 0, 'the AFTER panels draw the moved boxes in coral (%d px), BEFORE none (%d)' % (coral, coral0))
    except ImportError:
        pass
    for f in ('pins.json', 'install.py', 'build_report.json', 'plan.txt', 'INSTALL menu layout 1110.bat', 'UNDO menu layout 1110.bat'):
        check(os.path.isfile(os.path.join(out, f)), f + ' written')
    rep = json.load(open(os.path.join(out, 'build_report.json')))
    check(rep['art'] is None and set(rep['changes']) == {L.PATCH, L.ROWS12} and rep['guesses'], 'build report: no art, changes per patch, guesses')
    check(md5(os.path.join(out, L.SCENE)) == md5(os.path.join(sd, L.SCENE)), 'the scene is copied unchanged without --dm')
    with zipfile.ZipFile(os.path.join(out, L.PATCH)) as z, zipfile.ZipFile(os.path.join(sd, L.PATCH)) as z0:
        check(z.namelist() == z0.namelist() and z.read('menu/blob.bin') == z0.read('menu/blob.bin') and z.read('menu/ingame.xml') == z0.read('menu/ingame.xml'), 'other members byte-identical')
        new = z.read('menu/frontend.xml').decode('latin-1'); old = z0.read('menu/frontend.xml').decode('latin-1')
    check(HM.signature(old) == HM.signature(new), 'table signature kept')
    diff = L.element_diff(old, new)
    check(diff and all(d[2] in L.GEOM_ATTRS for d in diff), 'only X Y W H AlignH AlignV Graphic differ (%d attributes)' % len(diff))
    check(any(d[0] == 'MainMenu' and d[2] == 'Graphic' and d[4] == 'KLPic_None1' for d in diff), 'icons re-pointed at the blank')
    check(not any(d[4] in ('Background_Kane', 'Background_Lynch', 'Background_FABag', 'Background_HeaderSplat') for d in diff), 'no art-dependent re-point without the art')
    wn, _t, _o = L.parse_windows(new)
    pl = [e for e in wn['MainMenu'] if e.name == 'Button_Play'][0]
    check(pl.own.get('X') == str(L._MMX) and pl.own.get('Y') == str(L._MMY), 'Button_Play carries its own X / Y now')
    # a Priority attribute added by hand -> element_diff flags it, check fails
    tampered = HM.set_attr(new[pl.tag.start:pl.tag.end], 'Priority', '7')
    bad_xml = new[:pl.tag.start] + tampered + new[pl.tag.end:]
    check(any(d[2] == 'Priority' for d in L.element_diff(old, bad_xml)), 'element_diff sees a foreign attribute')

    # ---- check
    print('-- check')
    lines = []
    bad = L.check(out, sd, lines.append)
    check(not bad, 'check PASS on the stage: %s' % bad[:2])
    # tamper the staged file -> check FAIL
    tp = os.path.join(out, L.PATCH)
    keep = open(tp, 'rb').read()
    with zipfile.ZipFile(tp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('menu/frontend.xml', bad_xml.encode('latin-1')); z.writestr('menu/ingame.xml', INGAME.encode('latin-1')); z.writestr('menu/blob.bin', b'\x00\x01\x02binary' * 50)
    bad = L.check(out, sd, quiet)
    check(any('Priority' in x for x in bad), 'check FAILs a tampered stage (Priority): %s' % bad[:1])
    open(tp, 'wb').write(keep)
    check(not L.check(out, sd, quiet), 'check PASS again')
    # the live set changes -> pins refuse
    sd2 = os.path.join(tmp, 'set2'); write_set(sd2)
    with zipfile.ZipFile(os.path.join(sd2, L.PATCH), 'a') as z:
        z.writestr('menu/extra.txt', b'x')
    try:
        L.stage(sd2, out, accept=False, log=quiet); check(False, 'a changed input is refused by the pins')
    except ValueError as e:
        check('pinned' in str(e), 'a changed input is refused by the pins: %s' % str(e)[:50])
    check(any('not the pin' in x for x in L.check(out, sd2, quiet)), 'check against a changed set says so')
    # stage --dm on a fake scene refuses, nothing written
    out2 = os.path.join(tmp, 'layout_dm')
    try:
        L.stage(sd, out2, accept=True, dm=os.path.join(sd, L.PATCH), log=quiet); check(False, '--dm on an unreadable scene refused')
    except ValueError as e:
        check('Dead Men art not staged' in str(e) and not os.path.isfile(os.path.join(out2, 'install.py')), '--dm on an unreadable scene refused, nothing staged: %s' % str(e)[:60])

    # ---- install.py round trip on a fake game folder
    print('-- install')
    game = os.path.join(tmp, 'game'); ov = os.path.join(game, 'KLExpansion', 'Overlay')
    os.makedirs(os.path.join(ov, 'Scenes'))
    for n, _o, _w in files:
        shutil.copyfile(os.path.join(sd, n), os.path.join(ov, n))
    before = {n: md5(os.path.join(ov, n)) for n, _o, _w in files}
    cmd = [sys.executable, os.path.join(out, 'install.py'), '--game', game, '--skip-run-check']
    r = subprocess.run(cmd + ['--dry'], capture_output=True, text=True)
    check(r.returncode == 0 and 'would install' in r.stdout, 'install --dry')
    check(before == {n: md5(os.path.join(ov, n)) for n, _o, _w in files}, 'dry run wrote nothing')
    r = subprocess.run(cmd, capture_output=True, text=True)
    check(r.returncode == 0 and all(md5(os.path.join(ov, n)) == w for n, _o, w in files), 'install: live files = staged md5s (%s)' % r.stdout.strip().splitlines()[-1:])
    check(all(os.path.isfile(os.path.join(ov, n + L.TAG)) for n, _o, _w in files), 'backups next to the files')
    r = subprocess.run(cmd, capture_output=True, text=True)
    check(r.returncode != 0 and 'REFUSED' in r.stdout, 'second install refused')
    r = subprocess.run(cmd + ['--undo'], capture_output=True, text=True)
    check(r.returncode == 0 and before == {n: md5(os.path.join(ov, n)) for n, _o, _w in files}, 'undo byte-exact')
    check(not any(os.path.exists(os.path.join(ov, n + L.TAG)) for n, _o, _w in files), 'backups removed by undo')
    r = subprocess.run(cmd + ['--undo'], capture_output=True, text=True)
    check(r.returncode != 0, 'second undo refused')

    # ---- the art record shapes (the kl_portraits layout; no scene to fill here)
    print('-- art')
    tp = L.tile_plan(1280, 720)
    check(len(tp) == 6 and tp[0] == (0, 0, 512, 512, 512, 512) and tp[2] == (1024, 0, 256, 512, 256, 512) and tp[5] == (1024, 512, 256, 208, 256, 256), 'tile plan 1280x720 = the stock Background\'s six tiles')
    check(L.tile_plan(474, 720) == [(0, 0, 474, 512, 512, 512), (0, 512, 474, 208, 512, 256)], 'tile plan 474x720 (Kane)')
    rec = L.tex_record(3001, 16, 8, bytes(range(256)) * 0 + bytes(10 * 4 * 3), 10, 3)
    import struct
    check(len(rec) == 4 + 4 + 4 + 4 + 2 + 2 + 4 + 4 + 4 + 4 + 1 + 4 + 16 * 8 * 4 and struct.unpack_from('<I4s4sIHH', rec, 0)[1:] == (b'ABGR', b'ABGR', 3001, 8, 16), 'tex record header + size')
    sp = L.sprite_chunk(3001)
    check(len(sp) == 32 and sp[:4] == b'\x01\x01\x02\x00' and struct.unpack_from('<I', sp, 4)[0] == 3001, 'sprite chunk')
    pc = L.pic_chunk(tp, list(range(10, 16)))
    n = struct.unpack_from('<I', pc, 0)[0]
    check(n == 6 and len(pc) % 16 == 0 and struct.unpack_from('<I', pc, 4 + 40 * 6)[0] == 6 and struct.unpack_from('<6I', pc, 8 + 40 * 6) == tuple(range(10, 16)), 'picture chunk: n tiles, n sprites, padded')
    f = struct.unpack_from('<9f', pc, 4 + 40 * 5)
    check(abs(f[0] - 1152) < 1e-3 and abs(f[1] + 616) < 1e-3 and abs(f[4] - 1.0) < 1e-6 and abs(f[5] - 208 / 256.0) < 1e-6 and f[7] == 256 and f[8] == 208, 'last tile: centre, u / v extents')

    # ---- the Dead Men inventory reader
    print('-- dm inventory')
    md = os.path.join(tmp, 'dm_frontend.md')
    open(md, 'w').write('# dm\n\n## Window `PlayMenu` (3 elements)\nWindow attrs: x\n\n| i | par | d | name | Type | Template | X | Y | W | H | AlignH |\n|---|---|---|---|---|---|---|---|---|---|---|\n'
                        '| 0 |  | 0 | Button_Play | OpenWindow | MM | -200 | 230 |  |  | Left |\n| 1 |  | 0 | Button_Options | OpenWindow | MM | -200~ | 300 |  |  | Left |\n| 2 |  | 0 |  | Graphic |  | 1 | 2 |  |  |  |\n')
    pos = L.dm_positions(md)
    check(pos == {('PlayMenu', 'Button_Play'): (-200, 230)}, 'dm_positions: own X / Y of named elements only: %s' % pos)
    c, p, nts, _m = L.plan(sd, None, md, quiet)
    pc_ = [x for x in c[L.PATCH]['MainMenu'] if x.el.name == 'Button_Play'][0]
    check(pc_.attrs == dict(X=-200, Y=230) and any('from the Dead Men inventory' in x for x in nts), 'a mapped element takes the Dead Men position')


if __name__ == '__main__':
    sys.exit(main())
