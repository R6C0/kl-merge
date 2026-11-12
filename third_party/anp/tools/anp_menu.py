"""ANP main menu: builds ANP_Patch01.zip, the patch archive the loader serves in place of the game's own.

    py -I tools\\anp_menu.py [--out work\\out_menu\\ANP\\ANP_Patch01.zip] [--enable-all] [--check-only] [--intro auto|on|off]

--intro (default auto = on when <DD>\\Movies\\ANP\\M00_Intro.bik is installed, see tools/anp_movie.py): New game and
New saga open a window that plays Dead Men's intro; the loader (campaign.inc IntroMovie) starts M01 / DGNW when it ends
or is skipped. Off: both rows load at once, as before.

What it does (reads the player's own files only, writes only --out, <out dir>\\menu\\frontend.xml (the same XML as a
loose file: the loader serves it straight to the menu reader, MenuXml in campaign.inc) and a review copy):
  * Base = the archive the game mounts: KL2FixPatch01.zip when KL2Fix.asi is in the Dog Days folder and that zip
    exists, else Patch01.zip. Every member is copied byte for byte except menu/frontend.xml.
  * frontend.xml:
      - lines added for ANP tests (HelpText="%ANP test ...", e.g. the X07 button in AllLevels) are dropped;
      - MainMenu's button list becomes 8 rows: Dead Men / Dog Days (the stock Button_Play -> CampaignMenu) /
        Dead Dogs / Arcade / Online / Achievements / Settings / Quit (group moved up 68 px so the last row stays put);
      - three windows are inserted before <Window Name="MainMenu">: ANP_DeadMen (Continue = LoadScene DMCN,
        New game = LoadScene M01, Chapters, Difficulty), ANP_DeadMenChapters (16 LoadScene buttons, titles from
        Dead Men's own LOC in <Locale> blocks) and ANP_DeadDogs (Continue = DGCN, New saga = DGNW, Difficulty).
        DMCN / DGCN / DGNW are pseudo scene ids that the loader maps (loader/campaign.inc).
        --dm-difficulty on (default): the Dead Men page's Difficulty row shows Dead Men's own names from its LOC
        (Aspirin / Codeine / Morphine, per language in <Locale> blocks) and 'Morphine+' for Dog Days' 4th value.
  * Checks (the build fails on any): every added fragment is well-formed XML; every Graphic= name exists in the
    frontend scene (Scenes\\kaneandlynch.zip) or as an element Name; FocusGraphic / TextReceiver / HelpTextBlock
    names exist in the same window; Template= and Window= targets exist; every <Locale> group covers all nine
    languages kl2 knows exactly once; the output equals the input outside the replaced MainMenu list and the
    inserted block; window names are new.

The loader (ANP_Loader.asi, campaign.inc) answers the game's CreateFileA of Patch01.zip / KL2FixPatch01.zip with
<DD>\\ANP\\ANP_Patch01.zip when that file exists. Installing = copying --out there (game closed); removing it
restores the stock menu. Nothing in the game folder is changed by this script.
"""
import argparse, json, os, re, sys, unicodedata, xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anp_paths, locconv
from zipraw import read_zip, read_entry, entry_from_bytes, write_zip

# ANP scene id (folder under Scenes\Locations; at most 4 characters: kl2 copies 4 bytes, SetId 0x869d00) -> DM key
CHAPTERS = [('M01', 'M01A'), ('M02', 'M02A'), ('M03', 'M03A'), ('M03B', 'M03B'), ('M05', 'M05A'), ('M06', 'M06A'),
            ('M07', 'M07A'), ('M08', 'M08A'), ('M09', 'M09A'), ('M09B', 'M09B'), ('M11', 'M11A'), ('M11B', 'M11B'),
            ('M12', 'M12A'), ('M13', 'M13A'), ('M13B', 'M13B'), ('M14', 'M14A')]
# kl2's <Locale> language names (table at 0xcd8dcc): every Locale group must name each exactly once
KL2_LANGS = ['English', 'German', 'French', 'Spanish', 'Italian', 'Dutch', 'Russian', 'Polish', 'Japanese']
DM_LANGS = ['English', 'German', 'French', 'Spanish', 'Italian']           # Dead Men's own LOC languages
OTHER_LANGS = [l for l in KL2_LANGS if l not in DM_LANGS]                  # shown with the English titles
WINDOWS = ('ANP_DeadMen', 'ANP_DeadMenChapters', 'ANP_DeadDogs')
# --intro: New game / New saga play Dead Men's intro first (tools/anp_movie.py -> <DD>\Movies\ANP\M00_Intro.bik).
# kl2's MoviePlayer looks up the front end's IntroSequence entity and plays Movie00 + '.bik' as a LOOSE file (BinkOpen
# opens it itself; a missing file counts as finished at once, a file only inside a zip crashes at 0x4df0b8, so never
# pack it). No GUI element starts a scene when a movie ends, so the loader does (campaign.inc IntroMovie: BinkOpen /
# BinkClose import hooks). The two pages name the same file in different letter case so the loader can tell them
# apart (kl2 keeps the case, turns '\' into '/'; Windows opens either). The *Go windows (OpenWindowOnFinish) hold a
# LoadScene button that fades in after 1.5 s: only seen when the loader did not act.
INTRO_FILE = os.path.join('Movies', 'ANP', 'M00_Intro.bik')                 # under the Dog Days folder
INTRO_MOVIE_DM = 'Movies/ANP/M00_Intro'
INTRO_MOVIE_DG = 'Movies/ANP/M00_INTRO'
INTRO_WINDOWS = ('ANP_DMIntro', 'ANP_DMIntroGo', 'ANP_DGIntro', 'ANP_DGIntroGo')
NL = '\r\n'                                                                 # the stock XML uses CRLF


def esc(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def ascii_text(b):
    """Dead Men LOC text (UTF-8, cp1252 punctuation as C1 controls) -> plain ASCII (the stock XML is pure ASCII)"""
    s = b.decode('utf-8', 'replace')
    s = ''.join(locconv.C1_MAP.get(c, c) for c in s)
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('–', '-').replace('—', '-').replace('…', '...')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', s).strip()


def dm_titles(dm_dir):
    """{(language, key): title} from Dead Men's Scenes/KaneAndLynch.zip (AllLevels/Menu/Play/<key>_ChapterTitle)"""
    zp = os.path.join(dm_dir, 'Scenes', 'KaneAndLynch.zip')
    ents = {e.name.lower(): e for e in read_zip(zp)}
    out = {}
    for L in DM_LANGS:
        e = ents.get('scenes/kaneandlynch%s.loc' % L.lower())
        tree = locconv.parse(read_entry(e)) if e else []

        def find(nodes, path):
            for n in nodes:
                if n[0].decode('latin1').lower() == path[0].lower():
                    if len(path) == 1: return n
                    return find(n[2], path[1:]) if n[1] == 0x10 else None
            return None
        for _, key in CHAPTERS:
            n = find(tree, ['AllLevels', 'Menu', 'Play', key + '_ChapterTitle'])
            t = ascii_text(n[2]) if n is not None and n[1] != 0x10 and n[2] else ''
            if t: out[(L, key)] = t
    for _, key in CHAPTERS:                                   # missing language -> English -> the key itself
        for L in DM_LANGS:
            out.setdefault((L, key), out.get(('English', key), key))
    return out


DIFF_KEYS = ('Difficulty_Easy', 'Difficulty_Medium', 'Difficulty_Hard')


def dm_difficulty(dm_dir):
    """{(language, key): name} for Dead Men's three difficulties (AllLevels/Menu/Play/Difficulty_Easy/Medium/Hard in
    Dead Men's own front-end LOC: Aspirin / Codeine / Morphine in English), plus (language, 'Difficulty_Extreme') =
    the Hard name + '+': Dog Days' 4th difficulty has no Dead Men name, and every stock difficulty toggle lists all four
    values (option values 0..3; a 3-entry ToggleText with the profile at 3 is untested), so it is labelled, not hidden"""
    zp = os.path.join(dm_dir, 'Scenes', 'KaneAndLynch.zip')
    ents = {e.name.lower(): e for e in read_zip(zp)}
    out = {}
    for L in DM_LANGS:
        e = ents.get('scenes/kaneandlynch%s.loc' % L.lower())
        tree = locconv.parse(read_entry(e)) if e else []
        for key in DIFF_KEYS:
            n = locconv.find(tree, ['AllLevels', 'Menu', 'Play', key]) if tree else None
            t = ascii_text(n[2]) if n is not None and n[1] != 0x10 and n[2] else ''
            if t: out[(L, key)] = t
    for key in DIFF_KEYS:                                     # missing language -> English
        if ('English', key) not in out: raise SystemExit('Dead Men front-end LOC has no English %s' % key)
        for L in DM_LANGS: out.setdefault((L, key), out[('English', key)])
    for L in DM_LANGS: out[(L, 'Difficulty_Extreme')] = out[(L, 'Difficulty_Hard')] + '+'
    return out


def localized(make, titles, key):
    """one <Locale> block per Dead Men language; kl2's other languages get the English block"""
    parts = []
    for L in DM_LANGS:
        langs = [L] + (OTHER_LANGS if L == 'English' else [])
        parts.append('<Locale %s>%s</Locale>' % (' '.join('%s="True"' % x for x in langs), make(titles[(L, key)])))
    return NL.join(parts)


MAIN_GROUP = '''<GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="76">
  <GuiElement Type="Graphic" Graphic="Icon_Campaign" Y="177" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Resume" Y="211" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_System_Link" Y="245" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Heist" Y="279" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Multiplayer" Y="313" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Achievements" Y="347" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Options" Y="381" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement Type="Graphic" Graphic="Icon_Quit" Y="415" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#01" AnimY="210" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#02" AnimY="244" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#03" AnimY="278" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#04" AnimY="312" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#05" AnimY="346" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#06" AnimY="380" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#07" AnimY="414" />
  <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#08" AnimY="448" />

  <GuiElement Type="OpenWindow" Text="%Dead Men" Name="ANP_Button_DeadMen" Window="ANP_DeadMen" FocusGraphic="MMfb#01"
              HelpText="%Kane &amp; Lynch: Dead Men (2007)" FadeInDelay="0.05" Template="MM_Button" Y="186" ColorSet="Default"
              Option="MP_MultiPlayerMenu" OptionValue="0" />
  <GuiElement Type="OpenWindow" Text="%Dog Days" Name="Button_Play" Window="CampaignMenu" FocusGraphic="MMfb#02"
              HelpText="Button_Play_Help" FadeInDelay="0.05" Template="MM_Button" Y="220" ColorSet="Default"
              Option="MP_MultiPlayerMenu" OptionValue="0" />
  <GuiElement Type="OpenWindow" Text="%Dead Dogs" Name="ANP_Button_DeadDogs" Window="ANP_DeadDogs" FocusGraphic="MMfb#03"
              HelpText="%The full story: Dead Men, then Dog Days" FadeInDelay="0.05" Template="MM_Button" Y="254" ColorSet="Default"
              Option="MP_MultiPlayerMenu" OptionValue="0" />
  <GuiElement Type="OpenWindow" Text="Button_HeistMode" Name="Button_Heist" Window="HeistModeMenu" FocusGraphic="MMfb#04"
              HelpText="Button_Play_Help" FadeInDelay="0.10" Template="MM_Button" Y="288" ColorSet="Default"
              Option="MP_MultiPlayerMenu" OptionValue="0" Disabled="False" DisableInDemo="True" DisableInHiddenDemo="False" />
  <GuiElement Type="OpenWindow" Text="Button_Online" Name="Button_Online" Window="OnlineMenu" FocusGraphic="MMfb#05"
              HelpText="Button_Online_Help" FadeInDelay="0.15" Template="MM_Button" Y="322"
              Option="MP_MultiPlayerMenu" OptionValue="1" RulesWindow="FAShowRules" FirstGameWindow="FAFirstGame" DisableInGermanSKU="True" />
  <GuiElement Type="ZOnlyOneController" Text="Button_Achievements_pc" Name="Button_Achievements" Window="ShowAchievements"
              FocusGraphic="MMfb#06" HelpText="Button_Achievements_Help_pc" FadeInDelay="0.20" Template="MM_Button" Y="356"
              Option="MP_MultiPlayerMenu" OptionValue="0" Disabled="false" DisableInDemo="True" DisableInPreviewBuild="True"/>
  <GuiElement Type="OpenWindow" Text="Button_Settings" Name="Button_Options" Window="OptionsMenu" FocusGraphic="MMfb#07"
              HelpText="Button_Settings_Help" FadeInDelay="0.25" Template="MM_Button" Y="390" Option="MP_MultiPlayerMenu" OptionValue="0" />
  <GuiElement Type="OpenWindow" Text="Button_QuitGame" Name="Button_Quit" Window="QuitGameMenu" FocusGraphic="MMfb#08"
              HelpText="Button_QuitGame_Help" FadeInDelay="0.30" Template="MM_Button" Y="424" ColorSet="Default"
              Option="MP_MultiPlayerMenu" OptionValue="0" />

  <GuiElement Name="MMfb#01" Y="177" Graphic="FocusBar_short#01" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#02" Y="211" Graphic="FocusBar_short#02" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#03" Y="245" Graphic="FocusBar_short#03" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#04" Y="279" Graphic="FocusBar_short#04" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#05" Y="313" Graphic="FocusBar_short#05" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#06" Y="347" Graphic="FocusBar_short#06" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#07" Y="381" Graphic="FocusBar_short#07" Template="MM_FocusBar" MouseFocusW="239" />
  <GuiElement Name="MMfb#08" Y="415" Graphic="FocusBar_short#08" Template="MM_FocusBar" MouseFocusW="239" />
</GuiElement>'''


def bottom(help_name):
    return '''<GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Type="GUIGroup" Template="BottomFramePosSize" ShowDebug="True">
      <Platform PC_GC="True"><GuiElement Template="BottomFrameMenuBackButton"/></Platform>
      <Platform PC_KEYBOARD="True">
        <GuiElement Template="ButtonBack_INV_GT" />
        <GuiElement Template="BackButtonNoXPos_PC" AlignH="Right" X="0" HelpTextBlock="%s" HelpText=" "/>
      </Platform>
      <GuiElement Name="%s" Template="HelpText_GT" />
    </GuiElement>
  </GuiElement>''' % (help_name, help_name)


def hub(name, title, icon, rows):
    """a CampaignMenu-like page; each row is XML with @Y (row y), @FB (its focus bar) and @H (help block)"""
    help_name = name + '_Help'
    r, fb = [], []
    for i, row in enumerate(rows):
        y = 186 + 34 * i
        r.append(row.replace('@Y', str(y)).replace('@FB', '%s_fb#%02d' % (name, i + 1)).replace('@H', help_name))
        fb.append('<GuiElement Name="%s_fb#%02d" Y="%d" Graphic="FocusBar_short#%02d" Template="ANP_CM_FocusBar" MouseFocusW="239" />'
                  % (name, i + 1, y - 9, i + 1))
    return '''<Window Name="%s" LocaleBasePath="AllLevels/Menu/Play" Template="WindowDefault" RollBackMark="True">
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Template="HeadlineIcon" Graphic="%s"/>
    <GuiElement Template="HeadlineText" Text="%%%s" Shadow="true"/>
  </GuiElement>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="16" Y="24">
    <GuiElement Template="GameLogoTemplate" />
    <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="144">
      %s
      %s
    </GuiElement>
  </GuiElement>
  %s
</Window>''' % (name, icon, title, '\n      '.join(r), '\n      '.join(fb), bottom(help_name))


DIFF_ROW = '''<GuiElement Type="ToggleText" Text="Difficulty" Option="Difficulty" Name="@N_Diff" Template="ANP_CM_Button" Y="@Y"
                FocusGraphic="@FB" TextReceiver="@N_DiffData" UseTextReceiverAsFocus="True" RecCSFocus="OnFocus" RecCSDefault="Default"
                FadeInDelay="0.20" HelpText="/Menu/Generic/UseLRToSelect" HelpTextBlock="@H">
        <Text Text="Difficulty_Easy" /><Text Text="Difficulty_Medium" /><Text Text="Difficulty_Hard" /><Text Text="Difficulty_Extreme" />
      </GuiElement>
      <GuiElement Type="TextBlock" Text="" Name="@N_DiffData" X="560" Y="@Y" AlignH="Left" FadeInDelay="0.20" FadeInTime="0.2" />'''


def dm_diff_row(diff):
    """DIFF_ROW with Dead Men's names (dm_difficulty): the toggle once per Dead Men language in <Locale> blocks (kl2's
    other languages get the English one), each <Text> a literal ('%' prefix, as the chapter titles), so the frontend LOC
    needs no new keys. Same option (Difficulty, values 0..3) as Dog Days' rows."""
    head, tail = DIFF_ROW.split('\n        <Text', 1)
    tail, data = ('<Text' + tail).split('\n      </GuiElement>', 1)
    parts = []
    for L in DM_LANGS:
        langs = [L] + (OTHER_LANGS if L == 'English' else [])
        texts = ''.join('<Text Text="%%%s" />' % esc(diff[(L, k)]) for k in DIFF_KEYS + ('Difficulty_Extreme',))
        parts.append('<Locale %s>%s\n        %s\n      </GuiElement></Locale>'
                     % (' '.join('%s="True"' % x for x in langs), head, texts))
    return NL.join(parts) + data


def chapters_page(titles, enabled):
    help_name = 'ANP_DeadMenChapters_Help'
    rows = []
    for i, (sid, key) in enumerate(CHAPTERS):
        col, k = divmod(i, 8)
        pos = ' X="%d" Y="%d"' % (col * 330, 120 + 34 * k)      # every row placed, 34 px apart like the hub pages
        dis = '' if sid in enabled else ' Disabled="True"'
        rows.append(localized(lambda t, sid=sid, i=i, pos=pos, dis=dis:
                              '<GuiElement Type="LoadScene" Name="ANP_DM_%s" Scene="%s" Text="%%%d. %s" Template="ANP_DM_LT"'
                              ' HelpText="%%Dead Men, chapter %d" FocusGraphic="ANP_DMC_fb#%02d" FadeInDelay="%.2f"%s%s/>'
                              % (sid, sid, i + 1, esc(t), i + 1, i + 1, 0.05 + 0.02 * i, pos, dis), titles, key))
    fbars = '\n    '.join('<GuiElement Name="ANP_DMC_fb#%02d" X="%d" Y="%d" Graphic="FocusBar_short#%02d" Template="ANP_DM_FocusBar" MouseFocusW="239" />'
                           % (i + 1, (i // 8) * 330 - 10, 120 + 34 * (i % 8) - 9, i + 1) for i in range(len(CHAPTERS)))   # bar = row y - 9, as hub()
    return '''<Template Name="ANP_DM_LT" Type="LoadScene" Font="Text" FadeInTime="0.3" AlignH="Left" HelpTextBlock="%s"/>
<Template Name="ANP_DM_FocusBar" Type="Graphic" IsFocusGraphic="True" Priority="5" AlignH="Left" AlphaMin="0" AlphaMax="255" FadeInDelay="0.05" FadeInTime="0.1" FadeOutTime="0.01" />
<Window Name="ANP_DeadMenChapters" LocaleBasePath="AllLevels/Menu/Play" Template="WindowDefault">
  <GuiElement Template="BackgroundTemplate"/>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Template="HeadlineIcon" Graphic="Icon_Campaign"/>
    <GuiElement Template="HeadlineText" Text="%%Dead Men - Chapters"/>
    <GuiElement Template="LongLineTop" />
    <GuiElement Type="GUIGroup" Name="ANP_DMChapterList" Navigation="Free" GeomSpace="34" X="40" Y="0" W="700" H="500" AlignH="Left" ShowDebug="True">
    %s
    </GuiElement>
    %s
  </GuiElement>
  %s
</Window>''' % (help_name, '\n    '.join(rows), fbars, bottom(help_name))


CM_TEMPLATES = (
    '<Template Name="ANP_CM_Button" X="300" FadeInTime="0.2" AlignH="Left" HelpTextBlock="HelpCampaign"/>\n'
    '<Template Name="ANP_CM_FocusBar" Type="Graphic" IsFocusGraphic="True" Priority="5" X="290" AlignH="Left" AlphaMin="0"'
    ' AlphaMax="255" FadeInDelay="0.05" FadeInTime="0.1" FadeOutTime="0.01" />')


def movie_window(name, movie, go):
    return '''<Window Name="%s" PopOnBack="False" LocaleBasePath="AllLevels/Menu/Splash" Template="WindowDefault">
  <GuiElement Template="BackgroundTemplate"/>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Type="MoviePlayer" TimeOut="0" Loop="false" MoviePlayerDefine="IntroSequence" Movie00="%s" OpenWindowOnFinish="%s" Link="False"/>
  </GuiElement>
</Window>''' % (name, movie, go)


def go_window(name, scene, text, help_text):
    """after the movie: normally the loader has already started the scene; else one button (fades in after 1.5 s)"""
    return '''<Window Name="%s" PopOnBack="False" LocaleBasePath="AllLevels/Menu/Play" Template="WindowDefault">
  <GuiElement Template="BackgroundTemplate"/>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="16" Y="24">
    <GuiElement Template="GameLogoTemplate" />
    <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="144">
      <GuiElement Type="LoadScene" Name="%s_Start" Scene="%s" Text="%%%s" Template="ANP_CM_Button" Y="186" FocusGraphic="%s_fb#01" FadeInDelay="1.50" HelpText="%%%s" HelpTextBlock="%s_Help"/>
      <GuiElement Name="%s_fb#01" Y="177" Graphic="FocusBar_short#01" Template="ANP_CM_FocusBar" MouseFocusW="239" />
    </GuiElement>
  </GuiElement>
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize">
    <GuiElement Type="GUIGroup" Template="BottomFramePosSize" ShowDebug="True">
      <GuiElement Name="%s_Help" Template="HelpText_GT" />
    </GuiElement>
  </GuiElement>
</Window>''' % (name, name, scene, text, name, help_text, name, name, name)


def intro_pages():
    return '\n'.join([movie_window('ANP_DMIntro', INTRO_MOVIE_DM, 'ANP_DMIntroGo'),
                      go_window('ANP_DMIntroGo', 'M01', 'Start chapter 1', 'Dead Men, chapter 1'),
                      movie_window('ANP_DGIntro', INTRO_MOVIE_DG, 'ANP_DGIntroGo'),
                      go_window('ANP_DGIntroGo', 'DGNW', 'Start the saga', 'Dead Men, then Dog Days')])


def anp_block(titles, enabled, intro=False, diff=None):
    if intro:
        dm_new = '<GuiElement Type="OpenWindow" Name="ANP_DM_New" Window="ANP_DMIntro" Text="%New game" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.10" HelpText="%Start Dead Men from chapter 1 (any key skips the intro)" HelpTextBlock="@H"/>'
        dg_new = '<GuiElement Type="OpenWindow" Name="ANP_DG_New" Window="ANP_DGIntro" Text="%New saga" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.10" HelpText="%Dead Men, then Dog Days, as one campaign (any key skips the intro)" HelpTextBlock="@H"/>'
    else:
        dm_new = '<GuiElement Type="LoadScene" Name="ANP_DM_New" Scene="M01" Text="%New game" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.10" HelpText="%Start Dead Men from chapter 1" HelpTextBlock="@H"/>'
        dg_new = '<GuiElement Type="LoadScene" Name="ANP_DG_New" Scene="DGNW" Text="%New saga" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.10" HelpText="%Dead Men, then Dog Days, as one campaign" HelpTextBlock="@H"/>'
    dm_rows = [
        '<GuiElement Type="LoadScene" Name="ANP_DM_Continue" Scene="DMCN" Text="%Continue" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.05" HelpText="%Restart the last Dead Men chapter you reached" HelpTextBlock="@H"/>',
        dm_new,
        '<GuiElement Type="OpenWindow" Name="ANP_DM_Chapters" Window="ANP_DeadMenChapters" Text="%Chapters" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.15" Option="MercsGameMode" OptionValue="0" HelpTextBlock="@H" HelpText="%Pick any Dead Men chapter"/>',
        (dm_diff_row(diff) if diff else DIFF_ROW).replace('@N', 'ANP_DM'),
    ]
    dg_rows = [
        '<GuiElement Type="LoadScene" Name="ANP_DG_Continue" Scene="DGCN" Text="%Continue" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.05" HelpText="%Continue the saga" HelpTextBlock="@H"/>',
        dg_new,
        DIFF_ROW.replace('@N', 'ANP_DG'),
    ]
    return '\n'.join([
        '<!-- ===== A Newer Perspective: added pages (built by tools/anp_menu.py from your own game files) ===== -->',
        # copies of the stock CampaignMenu templates: CM_Button / CM_FocusBar are defined further down the file and kl2
        # resolves Template= while it parses, so using them here put the rows at X=0 (behind the logo) and left the
        # focus bars without IsFocusGraphic (arrow keys did not move the focus)
        CM_TEMPLATES,
        hub('ANP_DeadMen', 'Dead Men', 'Icon_Campaign', dm_rows),
        chapters_page(titles, enabled),
        hub('ANP_DeadDogs', 'Dead Dogs', 'Icon_System_Link', dg_rows)]
        + ([intro_pages()] if intro else []) +
        ['<!-- ===== end of ANP pages ===== -->', '']).replace('\r\n', '\n').replace('\n', NL)


MAIN_START = '<GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="144">'


def strip_test_lines(src):
    """drop the lines ANP added for tests (HelpText="%ANP test ...")"""
    out, dropped = [], []
    for line in src.splitlines(keepends=True):
        if re.search(r'HelpText="%ANP test', line): dropped.append(line.strip()); continue
        out.append(line)
    return ''.join(out), dropped


# KL2Fix with DebugMenu=1 (W's setup) opens CheatMenu instead of MainMenu after the splash, and Back there closes every
# window. So the three campaign rows also go into CheatMenu, as a fourth column, plus 'Play Dog Days' -> the stock main
# menu. Same element pattern as the stock CheatMenu rows.
# The focused row's text is drawn in the focus colour, which is invisible on CheatMenu's black background (11 Oct 14:01:
# 'Play Dead Men' had the initial focus and could not be seen). So it gets a focus bar like the hub pages (dark text on
# the grey bar). Attributes inline: our templates are defined after CheatMenu now (the ANP block is at the file's end).
CHEAT_FB = ('\t\t\t<GuiElement Name="ANP_CheatFB" Type="Graphic" Graphic="FocusBar_short#01" IsFocusGraphic="True" Priority="5"'
            ' AlignH="Left" AlphaMin="0" AlphaMax="255" FadeInDelay="0.05" FadeInTime="0.1" FadeOutTime="0.01"'
            ' MouseFocusW="239" X="615" Y="161" />\n')
CHEAT_ROWS = (
    '\t\t\t<GuiElement Type="OpenWindow" Text="%Play Dead Men"\tWindow="ANP_DeadMen"\tFont="Text" FadeInTime="0.2" FadeInDelay="0.10" HelpText="Kane &amp; Lynch: Dead Men" HelpTextBlock="HelpMainMenu" X="625" Y="170" FocusGraphic="ANP_CheatFB" />\n'
    '\t\t\t<GuiElement Type="OpenWindow" Text="%Play Dog Days"\tWindow="MainMenu"\tFont="Text" FadeInTime="0.2" FadeInDelay="0.20" HelpText="Kane &amp; Lynch 2: Dog Days" HelpTextBlock="HelpMainMenu"/>\n'
    '\t\t\t<GuiElement Type="OpenWindow" Text="%Play Dead Dogs"\tWindow="ANP_DeadDogs"\tFont="Text" FadeInTime="0.2" FadeInDelay="0.30" HelpText="Dead Men, then Dog Days" HelpTextBlock="HelpMainMenu"/>\n')
CHEAT_ANCHOR = 'Text="%XMLtest"'


def add_cheat_rows(out):
    """insert before CheatMenu's first row, so 'Play Dead Men' has the initial focus (the menu is driven by keys/pad;
    kl2 reads the mouse through DirectInput, so it has no Windows cursor to hover with)"""
    c0 = out.index('<Window Name="CheatMenu"'); c1 = out.index('</Window>', c0)
    a = out.index(CHEAT_ANCHOR, c0)
    if a > c1: raise SystemExit('CheatMenu first row not found')
    at = out.rfind('\n', c0, a) + 1
    rows = (CHEAT_FB + CHEAT_ROWS).replace('\n', NL)
    return out[:at] + rows + out[at:], rows


def build(src, titles, enabled, intro=False, diff=None):
    main = MAIN_GROUP.replace('\r\n', '\n').replace('\n', NL)
    block = anp_block(titles, enabled, intro, diff)
    for w in WINDOWS + INTRO_WINDOWS:
        if 'Name="%s"' % w in src: raise SystemExit('base frontend.xml already has %s: is it already an ANP archive?' % w)
    m0 = src.index('<Window Name="MainMenu"')
    g0 = src.index(MAIN_START, m0)
    g1 = src.index('<GuiElement Name="MMfb#06"', g0)
    g1 = src.index('</GuiElement>', g1) + len('</GuiElement>')
    if g1 > src.index('</Window>', m0): raise SystemExit('MainMenu list group not found where expected')
    out = src[:g0] + main + src[g1:]
    # insert after every stock window, just before </Windows>. Inserted before MainMenu (the old spot), the game booted
    # straight onto ANP_DeadMen instead of CheatMenu/MainMenu: the boot window depends on window order (the first
    # RollBackMark window, or an index), so no stock window may move
    at = out.rindex('</Windows>')
    at = out.rfind('\n', 0, at) + 1
    out = out[:at] + block + out[at:]
    if '<Window Name="CheatMenu"' in out:
        out, cheat = add_cheat_rows(out)
        block_all = (block, cheat)
    else:
        block_all = (block, '')
    return out, (g0, g1, main), (at, block_all)


# ---------------------------------------------------------------- checks
def scene_names_blob(dd_dir):
    ents = {e.name.lower(): e for e in read_zip(os.path.join(dd_dir, 'Scenes', 'kaneandlynch.zip'))}
    blob = b''
    for n in ('scenes/kaneandlynch.gms', 'scenes/kaneandlynch.buf', 'scenes/kaneandlynch.prp'):
        if n in ents: blob += read_entry(ents[n]) + b'\0'
    if not blob: raise SystemExit('frontend scene not readable (Scenes\\kaneandlynch.zip)')
    return blob


def windows_of(text):
    """{window name: its XML text} (also commented-out ones are skipped)"""
    t = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return {m.group(1): m.group(0) for m in re.finditer(r'<Window Name="([^"]+)".*?</Window>', t, re.S)}


def check(src, out, g0, g1, main, block, scene_blob, intro=False, dd_dir=None):
    errs, notes = [], []
    block, cheat = block
    windows = WINDOWS + (INTRO_WINDOWS if intro else ())
    for nm, frag in (('MainMenu list', main), ('ANP pages', block), ('CheatMenu rows', cheat)):
        try: xml.dom.minidom.parseString('<r>' + frag + '</r>')
        except Exception as e: errs.append('%s not well-formed: %s' % (nm, e))
    # outside the three edits the file is unchanged
    a = src[:g0] + src[g1:]
    b = out.replace(block, '', 1).replace(main, '', 1)
    if cheat: b = b.replace(cheat, '', 1)
    if a != b: errs.append('output differs from the input outside the MainMenu list, the CheatMenu rows and the ANP block')
    if cheat: notes.append('CheatMenu: 3 campaign rows added (KL2Fix DebugMenu opens it first)')
    added = main + block + cheat
    nocomment = re.sub(r'<!--.*?-->', '', out, flags=re.S)
    names = set(re.findall(r'\bName="([^"]+)"', nocomment))
    templates = set(re.findall(r'<Template Name="([^"]+)"', nocomment))
    wins = windows_of(out)
    for g in sorted(set(re.findall(r'(?<![A-Za-z])Graphic="([^"]+)"', added))):
        if g.encode('latin1') + b'\0' not in scene_blob and g not in names:
            errs.append('Graphic "%s" is neither in the frontend scene nor an element name' % g)
    for w in windows + ('MainMenu',):
        if w not in wins: errs.append('window %s missing from the output' % w); continue
        wt = wins[w]
        wnames = set(re.findall(r'\bName="([^"]+)"', wt))
        for attr in ('FocusGraphic', 'TextReceiver', 'HelpTextBlock', 'Receiver'):
            for v in set(re.findall(r'\b%s="([^"]+)"' % attr, wt)):
                if w == 'MainMenu' and attr == 'HelpTextBlock': continue      # stock templates' blocks
                if v not in wnames and v not in templates:
                    # stock template-defined help blocks (e.g. HelpMainMenu) are checked against the whole file
                    if v not in names: errs.append('%s: %s="%s" names no element' % (w, attr, v))
    for t in sorted(set(re.findall(r'\bTemplate="([^"]+)"', added))):
        if t not in templates: errs.append('Template "%s" not defined' % t); continue
        d = out.find('<Template Name="%s"' % t)                 # kl2 resolves templates while parsing
        uses = [out.find(f) + f.find('Template="%s"' % t) for f in (main, block, cheat)
                if f and 'Template="%s"' % t in f and f in out]
        if uses and d > min(uses): errs.append('Template "%s" is used before it is defined' % t)
    for t in sorted(set(re.findall(r'\b(?:Window|OpenWindowOnFinish)="([^"]+)"', added))):
        if t not in wins: errs.append('Window "%s" not defined' % t)
    # intro movie pages: MoviePlayer needs the front end's IntroSequence define and a LOOSE .bik (never a zip entry)
    movies = re.findall(r'<GuiElement Type="MoviePlayer"[^>]*>', added)
    if intro:
        if len(movies) != 2: errs.append('intro: %d MoviePlayer elements (want 2)' % len(movies))
        for mv in movies:
            d = dict(re.findall(r'(\w+)="([^"]*)"', mv))
            if d.get('MoviePlayerDefine') != 'IntroSequence' or d.get('Loop', '').lower() != 'false' or d.get('TimeOut') != '0':
                errs.append('intro: MoviePlayer attributes %s' % d)
            if d.get('OpenWindowOnFinish') not in INTRO_WINDOWS: errs.append('intro: OpenWindowOnFinish %s' % d.get('OpenWindowOnFinish'))
            if d.get('Movie00', '').replace('\\', '/').lower() != INTRO_MOVIE_DM.lower(): errs.append('intro: Movie00 %s' % d.get('Movie00'))
        if sorted(re.findall(r'Movie00="([^"]+)"', added)) != sorted([INTRO_MOVIE_DM, INTRO_MOVIE_DG]) or INTRO_MOVIE_DM == INTRO_MOVIE_DG:
            errs.append('intro: the two pages must name the movie in different letter case (the loader tells them apart)')
        if b'IntroSequence\0' not in scene_blob: errs.append('intro: the frontend scene has no IntroSequence define')
        if dd_dir:
            mp = os.path.join(dd_dir, INTRO_FILE)
            if os.path.isfile(mp):
                with open(mp, 'rb') as f: hd = f.read(4)
                if hd[:3] != b'BIK': errs.append('intro: %s is not a Bink file (kl2 would crash at 0x4df0b8)' % mp)
                else: notes.append('intro: %s installed (%s, %d bytes)' % (mp, hd.decode('latin1'), os.path.getsize(mp)))
            else: notes.append('intro: %s NOT installed yet: until it is, New game / New saga show only the fallback button' % mp)
        for w in INTRO_WINDOWS:
            if out.count('<Window Name="%s"' % w) != 1: errs.append('window %s defined %d times' % (w, out.count('<Window Name="%s"' % w)))
        notes.append('intro: New game -> ANP_DMIntro (%s), New saga -> ANP_DGIntro (%s); loader IntroMovie starts M01 / DGNW'
                     % (INTRO_MOVIE_DM, INTRO_MOVIE_DG))
    elif movies: errs.append('MoviePlayer in the added XML without --intro')
    groups = {}                                   # element name -> languages of the Locale blocks holding it
    for m in re.finditer(r'<Locale ([^>]*)>(.*?)</Locale>', block, re.S):
        for nm in re.findall(r'\bName="([^"]+)"', m.group(2)):
            groups.setdefault(nm, []).extend(re.findall(r'(\w+)="True"', m.group(1)))
    for nm, langs in groups.items():
        if sorted(langs) != sorted(KL2_LANGS): errs.append('Locale group of %s covers %s' % (nm, ','.join(langs)))
    if groups: notes.append('Locale groups: %d elements x %d languages' % (len(groups), len(KL2_LANGS)))
    for w in WINDOWS:
        if out.count('<Window Name="%s"' % w) != 1: errs.append('window %s defined %d times' % (w, out.count('<Window Name="%s"' % w)))
    if any(ord(c) > 126 for c in added): errs.append('non-ASCII text in the added XML')
    notes.append('added elements: %d GuiElement/Window/Template tags (each chapter once per language block)'
                 % len(re.findall(r'<(?:GuiElement|Window|Template)\b', added)))
    return errs, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=os.path.join(anp_paths.WORK, 'out_menu', 'ANP', 'ANP_Patch01.zip'))
    ap.add_argument('--dd'); ap.add_argument('--dm')
    ap.add_argument('--base', help='patch archive to start from (default: what the game mounts)')
    ap.add_argument('--enable-all', action='store_true', help='enable every chapter button even if not installed')
    ap.add_argument('--check-only', action='store_true', help='build and check, write nothing')
    ap.add_argument('--intro', choices=('auto', 'on', 'off'), default='auto',
                    help='New game / New saga play Dead Men\'s intro first (auto = when <DD>\\%s is installed)' % INTRO_FILE)
    ap.add_argument('--dm-difficulty', choices=('on', 'off'), default='on',
                    help='Dead Men page difficulty row with Dead Men\'s names (Aspirin / Codeine / Morphine / Morphine+, '
                         'per language); off = Dog Days\' names as before. The Dead Dogs page keeps Dog Days\' names')
    a = ap.parse_args()
    dd = a.dd or anp_paths.game_dir('ANP_DD_GAME', anp_paths.DD_FOLDER)
    dm = a.dm or anp_paths.game_dir('ANP_DM_GAME', anp_paths.DM_FOLDER)
    if a.base: base = a.base
    else:
        k = os.path.join(dd, 'KL2FixPatch01.zip')
        base = k if os.path.exists(os.path.join(dd, 'KL2Fix.asi')) and os.path.exists(k) else os.path.join(dd, 'Patch01.zip')
    out_abs = os.path.abspath(a.out)
    if out_abs.lower().startswith(os.path.abspath(dd).lower() + os.sep) and not a.check_only:
        raise SystemExit('refusing to write into the game folder (%s); build into work and copy it' % out_abs)
    ents = read_zip(base)
    fe = [e for e in ents if e.name.lower() == 'menu/frontend.xml']
    if len(fe) != 1: raise SystemExit('%s has no menu/frontend.xml' % base)
    src0 = read_entry(fe[0]).decode('latin1')
    src, dropped = strip_test_lines(src0)
    installed = {sid for sid, _ in CHAPTERS if os.path.exists(os.path.join(dd, 'Scenes', 'Locations', sid, '%s_Main.zip' % sid))}
    enabled = {sid for sid, _ in CHAPTERS} if a.enable_all else installed
    titles = dm_titles(dm)
    diff = dm_difficulty(dm) if a.dm_difficulty == 'on' else None
    intro = a.intro == 'on' or (a.intro == 'auto' and os.path.isfile(os.path.join(dd, INTRO_FILE)))
    out, (g0, g1, mtxt), (at, block) = build(src, titles, enabled, intro, diff)
    errs, notes = check(src, out, g0, g1, mtxt, block, scene_names_blob(dd), intro, dd)
    if diff:
        if block[0].count('Name="ANP_DM_Diff"') != len(DM_LANGS): errs.append('Dead Men difficulty toggle: %d copies (want %d)'
                                                                           % (block[0].count('Name="ANP_DM_Diff"'), len(DM_LANGS)))
        if block[0].count('Name="ANP_DG_Diff"') != 1 or block[0].count('Name="ANP_DM_DiffData"') != 1:
            errs.append('difficulty rows: the Dead Dogs toggle / the Dead Men text receiver must stay single')
    rep = {'base': base, 'dropped_test_lines': dropped, 'frontend_bytes': [len(src0), len(out)],
           'intro': '%s (--intro %s)' % ('on' if intro else 'off', a.intro),
           'dm_difficulty': ([diff[(L, k)] for L in DM_LANGS for k in DIFF_KEYS + ('Difficulty_Extreme',)]
                             if diff else 'off (Dog Days names)'),
           'chapters_installed': sorted(installed, key=[s for s, _ in CHAPTERS].index),
           'chapters_enabled': len(enabled), 'english_titles': [titles[('English', k)] for _, k in CHAPTERS],
           'notes': notes, 'errors': errs, 'out': None}
    if errs:
        print(json.dumps(rep, indent=1)); raise SystemExit('menu check FAILED (%d errors)' % len(errs))
    if not a.check_only:
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        new = []
        for e in ents:
            if e is fe[0]:
                ne = entry_from_bytes(e.name, out.encode('latin1'), like=e); ne.flags = e.flags; ne.ver = e.ver
                new.append(ne)
            else: new.append(e)                      # copied byte for byte (compressed data as is)
        tmp = out_abs + '.tmp'
        write_zip(tmp, new); os.replace(tmp, out_abs)
        # read back: every member decompresses and matches
        back = {e.name: read_entry(e) for e in read_zip(out_abs)}
        for e in ents:
            want = out.encode('latin1') if e is fe[0] else read_entry(e)
            if back.get(e.name) != want: raise SystemExit('read-back mismatch in %s' % e.name)
        # loose copy the loader serves directly (campaign.inc MenuXml: <DD>\ANP\menu\frontend.xml), same bytes
        loose = os.path.join(os.path.dirname(out_abs), 'menu', 'frontend.xml')
        os.makedirs(os.path.dirname(loose), exist_ok=True)
        with open(loose + '.tmp', 'wb') as f: f.write(out.encode('latin1'))
        os.replace(loose + '.tmp', loose)
        rep['loose_xml'] = loose
        rd = os.path.dirname(out_abs)                 # review copy next to the ANP folder, not inside it
        if os.path.basename(rd).lower() == 'anp': rd = os.path.dirname(rd)
        rep['review_copy'] = os.path.join(rd, 'ANP_Patch01.frontend.xml')
        with open(rep['review_copy'], 'w', encoding='latin1', newline='') as f:
            f.write(out)
        rep['out'] = out_abs
    print(json.dumps(rep, indent=1))
    if not installed and not a.enable_all:
        print('note: no ANP chapter is installed in %s, so every chapter button is disabled (use --enable-all)' % dd)


if __name__ == '__main__':
    main()
