r"""mkoverlay.py <KLHook.ini> <stock Patch01.zip> <out folder>   builds <out>\Overlay\Patch01.zip: the menu of the expansion.

The stock Patch01.zip is only READ. The result goes into <game>\KLExpansion\Overlay\ (copy it there yourself, or give
<game>\KLExpansion as <out>); klslot.c answers the game's open of Patch01.zip with it, so nothing stock is replaced.
It holds the stock members (menu/ingame.xml byte for byte) and a menu/frontend.xml changed in three places only:

 1. Arcade page (window HeistModeMenu): the stock 'Start' button gets  Option="Dummy" OptionValue="1";  one button per
    expansion page is added below the five stock ones:  Window="HeistPlayMenu<N>" Text="%<Title>" Option="Dummy"
    OptionValue="<N>", with a focus bar, an icon and a separator line of its own, and the whole block of rows is moved
    up by one row (34 units) per added button so that the last one clears 'Back' (see LAYOUT).
 2. One window HeistPlayMenu<N> per page: a copy of the stock map page HeistPlayMenu with
      - EVERY ELEMENT NAME SUFFIXED '_P<N>' and every reference to one of them inside the copy rewritten (see NAMES),
      - the headline replaced by the page title,
      - the title of every slot that has a map on the page replaced by literal text (a text that starts with '%' is
        shown as written, re\menus.md 2.6),
      - the picture of such a slot replaced (see PICTURES),
      - the element that prints the STOCK map's briefing for the slot removed,
      - the gamepad's bottom frame taken from a copy of its template whose Accept goes to the page's own selector.
    Everything else - Accept, Back, the option Heist_SelectedLevel - is the stock page's.
 3. One <Template> per page beside the stock BottomFrameHeistBackStartGameButtons (the gamepad layout's Back / Accept).

NAMES (why the first version's page had an empty 'Location:' row, run MP1 2026-10-09). The game finds an element by
name over the WHOLE menu, not inside the window: 0x83faf0 -> 0x4fa730 walks the manager's one table (5096 entries,
all windows and elements in file order) and returns the FIRST element with that name. All 116 direct calls of 0x83faf0 in the
exe are look-ups of this kind (TextReceiver 0x8db616, a toggler's <Graphic> children 0x50f8db, a message's Receiver -
re\menus.md 2.4; which of them serves FocusGraphic was not picked out). A copied page with the stock names therefore sent its level title to the stock page's text block
'HeistChapterData' and lit the stock page's focus bar 'HPMfb#01' - both in a window that is not open. With names of
its own the copy's references stay inside the copy. Names the stock page refers to but does not define (PlayLevel,
HeistIndicator, HelpPlay) are left as they are.
    FOR SCRIPTS (klauto): on page N the selector is 'HeistLevel_P<N>':  sel HeistLevel_P2 0xceceec 0  /
    msg HeistLevel_P2 StartGame.  'HeistLevel' is the stock page's selector, whichever page is open.
    NOT ESTABLISHED: why the row's own label ('Location:') was missing too; expected to come back with the focus bar
    (live check MP2 of re\hook_live.md).

LAYOUT (compared with the stock rows). The five stock buttons stand at Y 220, 254, 288, 322, 356 in the group
`ScreenBaseSize X="130" Y="110"`, each with a focus bar 9 above (Name HMfbl#0k, Graphic FocusBar_short#0k), an icon
(`Type="Graphic" Graphic="Icon_..." Y=<bar> X="250"`) and a line under it (`Template="Line" Graphic="Line_Short_01#0k"
AnimY=<bar+33>`; Anim coordinates are relative to the group: the main menu has the same rows 34 higher in a group 34
lower). The first version added only button and bar at Y 390: no icon element, and 390 + 110 is where the bottom
frame's 'Back' is. Now: icon (Icon_Marketplace, then Icon_Multiplayer, Icon_System_Link, Icon_Options - entities of
the frontend scene that this window does not use yet; an entity can stand in one place only), line
(Line_Short_01#07..#10), and the group's Y lowered by 34 per page, which moves all rows up together.

PICTURES. A picture is an entity of the frontend scene, not a file (re\menus.md 2.7); Dead Men's own menu pictures
are converted but not in that scene (re\expansion.md: the frontend-scene graft is not started). Until it is, the
cheapest result that does not show the WRONG map is a stock picture of another kind: an entry of slot F0k shows the
story-mode picture LevelPicture_L0k (same template LevelPicture_T, used by the stock story page) instead of the Arcade
picture of the stock map whose slot it takes. NOT VIEWED: what each of those eleven pictures shows (no image tool on
this machine) - choose per entry with <slot>.Picture=, or get the old behaviour with Pictures=slot.

'Dummy' is a spare menu option nothing in kl2.exe reads (re\menus.md 3.1). The buttons still set it, but klslot.c no
longer takes the page from it (the options object does not live through the start of a level): the hook reads the page
off the window stack - the window name HeistPlayMenu<N> IS the page - and uses [Redirect.<N>] for a slot from the
moment that slot's archive is opened. Entry k of a page is the engine's slot {F01,F02,F03,F04,F06,F07,F05,F08,F09}[k];
a slot without a map on the page keeps its stock title and loads what [Redirect] or the stock game gives it.

THE HEISTER PAGE (2026-10-09; NOT SEEN IN THE GAME YET). Unless [Character] Enable=0 or Menu=0, the Arcade page gets
one more button, 'Heister', ABOVE the expansion pages' buttons, and a window KLHeister with three rows: Character,
Mask, Outfit. Each row is a stock ToggleText bound to an option the hook answers (klchar.c: KLChar, KLMask, KLOutfit -
names kl2.exe does not know; without the hook's DLL they read 0 and a change is dropped, so the page is harmless but
dead). The rows are the story map page's 'Difficulty' row three times (window PlayMenu: a plain page with two
option rows, values written as they are changed - no Accept / Cancel cache as on the options pages), with focus bars
FocusBar_long#04..#06 and names of their own (KLH_...). Texts are literal ('%...'), English only.
With the Heister button there is room for pages 2..4 only (the Arcade page has four free separator lines).
PICTURES ON THE HEISTER PAGE (--pictures as a fourth argument; NOT SEEN IN THE GAME YET). A picture of the chosen
character (256 x 304) and of the chosen mask (256 x 256) where the map pages show the map picture: one Graphic
element per entry of the two rows (entities KLPic_Char01..16, KLPic_Mask1..8 and three blanks KLPic_None1..3 for
'Game default', 'Game option' and 'No mask') and a ToggleImages per row, which the row's ToggleText names in
ToggleReceivers - the way the map pages' selector drives HeistLevelImageToggler. The ToggleImages also carries the
row's Option so that it starts on the stored value (as LobbyImageToggler does with MP_SelectedLevel).
ASSUMPTIONS: a plain ToggleText passes its steps on to ToggleReceivers as the level selectors do (the attribute is
ZToggle's, re\menus.md 2.3); the two widgets on one option stay in step.
THE ENTITIES ARE NOT IN THE STOCK MENU SCENE: tools\kl_portraits.py 'menu' builds Overlay\Scenes\kaneandlynch.zip
with them. An overlay Patch01.zip built with --pictures must only be installed together with that archive (what a
Graphic= that names no entity does was not tried).

KLHook.ini (the same file the hook reads):
    [Redirect.2]            slot = map folder under KLExpansion\Maps (klslot.c)
    F01=DM03
    F02=DM01
    [Page.2]
    Title=Dead Men maps     button and headline (default: 'Expansion maps <N>')
    Icon=Icon_Marketplace   optional: the button's icon
    Pictures=story          optional: 'story' (default) or 'slot' = the stock Arcade picture of each slot
    F01=Withdrawal          title of the entry (default: the map folder's name)
    F01.Picture=LevelPicture_L09      optional: any LevelPicture_* entity of the frontend scene
Pages 2..5 (four focus bars, icons and lines are free below the stock rows).

SEEN IN THE GAME (run MP1, the first version): the overlay archive's frontend.xml is the one in effect, the sixth
button opens HeistPlayMenu2 with the headline, and the button's OptionValue is stored. NOT SEEN: this version - the
renamed elements, the moved rows, the icon, the story pictures, the gamepad template (no run has used a gamepad), and
the menu system's element limit (5096, re\menus.md 2.5; a page adds about 75 tags).
KNOWN: the lobby title, the briefing and the Steam leaderboard still belong to the stock map of the slot (klslot.c;
klsteam.c blocks the upload).
"""
import configparser, hashlib, os, re, sys, time, zipfile

ORDER = [1, 2, 3, 4, 6, 7, 5, 8, 9]            # menu entry k -> slot number (kl2 0x746570)
MEMBER = 'menu/frontend.xml'
ICONS = ['Icon_Marketplace', 'Icon_Multiplayer', 'Icon_System_Link', 'Icon_Options']      # entities HeistModeMenu does not use (it has Icon_Heist, _Campaign, _Game_Rules, _Game_Stats, _Achievements, _Xbox_Live)
ROW = 34                                       # distance of two rows of the Arcade page
# attributes whose value names another element (comma lists allowed); <Graphic Graphic="..."/> children are handled apart
REFS = ('Receiver', 'TextReceiver', 'ToggleReceivers', 'FocusGraphic', 'FocusParent', 'HelpTextBlock', 'HelpTextBlock2', 'Receivers')
GC_TEMPLATE = 'BottomFrameHeistBackStartGameButtons'


def esc(t):
    """Text for an attribute. Whether the game's XML reader knows entities (&amp; ...) is not established, and the stock
    file uses none inside a literal text: characters that would need one are refused rather than guessed at."""
    bad = [c for c in '&"<>' if c in t] + [c for c in t if ord(c) < 32 or ord(c) > 126]
    if bad:
        raise SystemExit('text %r: the characters %s cannot be used (plain ASCII without & " < > only)' % (t, ' '.join(sorted(set(bad)))))
    return t


def pages(ini):
    """[(n, title, {slot number: (map folder, entry title, picture or None)}, {page keys})] from [Redirect.N] / [Page.N]."""
    cp = configparser.RawConfigParser(strict=False, delimiters=('=',), comment_prefixes=(';', '#'), interpolation=None)
    cp.optionxform = str
    cp.read(ini)
    out = []
    for n in range(2, 6):
        r = 'Redirect.%d' % n
        if not cp.has_section(r):
            continue
        pg = dict(cp.items('Page.%d' % n)) if cp.has_section('Page.%d' % n) else {}
        ent = {}
        for k, v in cp.items(r):
            m = re.fullmatch(r'[Ff]0([1-9])', k)
            if not m:
                print('  [%s] %s: not one of F01..F09 - no menu entry for it' % (r, k)); continue
            ent[int(m.group(1))] = (v.strip(), pg.get(k, v.strip()), pg.get(k + '.Picture'))
        if ent:
            out.append((n, pg.get('Title', 'Expansion maps %d' % n), ent, pg))
    for n in range(6, 10):
        if cp.has_section('Redirect.%d' % n):
            print('  [Redirect.%d]: the hook uses it, but the menu has room for pages 2..5 only - no button for it' % n)
    return out


def one(pattern, text, what, flags=0):
    m = list(re.finditer(pattern, text, flags))
    if len(m) != 1:
        raise SystemExit('frontend.xml is not the one this script knows: %d matches for %s' % (len(m), what))
    return m[0]


def defined(text):
    """Names of the elements a piece of XML defines (comments ignored), in order."""
    plain = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return re.findall(r'<GuiElement\b[^>]*?\bName="([^"]+)"', plain, re.S)


def rename(text, names, suffix):
    """Give every element in `names` the suffix: its definition (Name=) and every by-name reference in `text`."""
    names = set(names)

    def name(m):
        return '%sName="%s%s"' % (m.group(1), m.group(2), suffix) if m.group(2) in names else m.group(0)

    def ref(m):
        return '%s="%s"' % (m.group(1), ','.join(v + suffix if v.strip() in names else v for v in m.group(2).split(',')))

    def child(m):
        return '<Graphic Graphic="%s%s"' % (m.group(1), suffix) if m.group(1) in names else m.group(0)

    text = re.sub(r'(<GuiElement\b[^>]*?\b)Name="([^"]+)"', name, text, flags=re.S)
    text = re.sub(r'\b(%s)="([^"]*)"' % '|'.join(REFS), ref, text)
    return re.sub(r'<Graphic Graphic="([^"]+)"', child, text)


HEISTER = 'KLHeister'
# THE ENTRY COUNTS ARE THE RANGES of the three options (re\wardrobe.md 5a: a ToggleText shows child [value] and has
# no value above its last child): klchar.c's KLC_NCHAR + 1, KLC_MASKS + 2 and KLC_OUTFITS must be these lengths.
# Dog Days names: the game's own (.LOC FACharacters C1..C8). Dead Men names: its eight Fragile Alliance ranks
# (.LOC Menu/Online/Profile/FragileAllianceRank_01..08; that rank n is the model Hero_0n is an ASSUMPTION for 3..8,
# tools\kl_chars.py DM_NAMES).
CHARACTERS = ['Game default', 'J.C.', 'Tommy', 'Pierre', 'Liam', 'Jean', 'Elwood', 'Bud', 'Mitchel',
              'Kane', 'Lynch', 'Ashkanan (Dead Men)', 'Meldal (Dead Men)', 'Red (Dead Men)', 'Parker (Dead Men)',
              'Standen (Dead Men)', 'Hutchison (Dead Men)']                                   # klchar.c KLChar 0..16
# The masks have no names in the game (one material, Merc_Masks, one shared picture): named here by what
# tools\kl_view.py masks shows (research\v_wardrobe\masks.png), with the heister who wears each in the stock game.
MASK_LOOKS = ['Moustache', 'Black beard', 'Red opera', 'Orange face', 'Skull', 'Porcelain doll', 'Red and white opera', 'Blue opera']
PD2_MASKS = ['Wolf (Payday 2)', 'Dallas (Payday 2)', 'Chains (Payday 2)', 'Hoxton (Payday 2)']       # masks 9..12: tools\kl_pd2mask.py PD2_MASKS order
MASKS = ['Game option', 'No mask'] + ['%s - %s' % (m, c) for m, c in zip(MASK_LOOKS, CHARACTERS[1:9])] + PD2_MASKS      # KLMask 0..13
# The 24 looks of a Dead Men Fragile Alliance hero: armour (0..3) + 4 * shirt (0..1) + 8 * head (0..2), in the order
# of tools\kl_chars.py outfit_name (the same words). A Dog Days body has one outfit and ignores the row.
OUTFIT_ARMOUR = ['Plain clothes', 'Light vest', 'Tactical vest', 'Heavy armour']
OUTFIT_SHIRT = ['', 'black shirt']
OUTFIT_HEAD = ['', 'dark balaclava', 'black balaclava']
OUTFITS = [', '.join(x for x in (a, sh, hd) if x) for hd in OUTFIT_HEAD for sh in OUTFIT_SHIRT for a in OUTFIT_ARMOUR]      # KLOutfit 0..23
HEISTER_ROWS = (('KLH_Char', 'Character', 'KLChar', CHARACTERS), ('KLH_Mask', 'Mask', 'KLMask', MASKS), ('KLH_Outfit', 'Outfit', 'KLOutfit', OUTFITS))
# picture rows: (row name, option, entity of entry k or a blank, X, Y) - tools\kl_portraits.py NAMES
# Y: the character picture (304 high) ends level with the mask picture (84 + 256 = 340); at Y=60 its legs ran ~16 units into the
# Character focus bar (run PV1, 2026-10-09 23:55, picture research\shots\PV1_62s.png).
HEISTER_PICS = (('KLH_Char', 'KLChar', ['KLPic_None1'] + ['KLPic_Char%02d' % n for n in range(1, 17)], -117, 36),
                ('KLH_Mask', 'KLMask', ['KLPic_None2', 'KLPic_None3'] + ['KLPic_Mask%d' % n for n in range(1, len(MASKS) - 1)], 157, 84))
HEISTER_NOTE = 'Arcade Mode. Dead Men bodies, their outfits and the masks of other heisters need a map built with the wardrobe. Outfits are for Dead Men bodies; the balaclava shades show on the six masked men.'


def heister_window(nl, pictures=False):
    """The window KLHeister: three option rows in the layout of the story map page's rows (PlayMenu)."""
    L = ['  <!-- KLExpansion: the heister page (mkoverlay.py; options answered by klchar.c) -->',
         '  <Window Name="%s" LocaleBasePath="AllLevels/Menu/Heist" Template="WindowDefault">' % HEISTER,
         '    <GuiElement Template="BackgroundTemplate"/>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
         '      <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>',
         '      <GuiElement Template="HeadlineText" Text="%Heister"/>',
         '      <GuiElement Template="LongLineTop" />',
         '    </GuiElement>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
         '      <GuiElement Template="ChapterBackgroundTemplate"/>',
         '      <GuiElement Type="TextBlock" Name="KLH_Note" Text="%%%s" Font="Text" LineSpace="26" FadeInDelay="0.10" FadeInTime="0.2" AlphaMax="192" X="450" Y="64" AlignH="Left" TextWidth="430" W="300" H="400" />' % esc(HEISTER_NOTE),
         '      <GuiElement Type="GUIGroup" ShowDebug="True" Name="KLH_CenterBox" AlignH="Right" X="-100" Y="-80" W="384" H="576">']
    if pictures:                                      # before the rows: a <Graphic> child is looked up by name when it is added
        L = L[:-1]
        for name, opt, ents, x, y in HEISTER_PICS:
            if len(ents) != len(dict((r[0], r[3]) for r in HEISTER_ROWS)[name]):
                raise SystemExit('%s: %d pictures for %d entries' % (name, len(ents), len(dict((r[0], r[3]) for r in HEISTER_ROWS)[name])))
            L.append('      <GuiElement Type="GUIGroup" Template="LevelPictureGroup_T">')
            L += ['        <GuiElement Type="Graphic" Name="%sPic%02d" Template="LevelPicture_T" X="%d" Y="%d" Graphic="%s" />' % (name, k, x, y, e) for k, e in enumerate(ents)]
            L.append('      </GuiElement>')
            L.append('      <GuiElement Type="ToggleImages" Text="" Name="%sPics" Option="%s" ActivateButtonUp="NoActivation" ActivateButtonDown="NoActivation" X="0" Y="0" ShowDebug="True" Link="False">' % (name, opt))
            L += ['        <Graphic Graphic="%sPic%02d" />' % (name, k) for k in range(len(ents))]
            L.append('      </GuiElement>')
        L.append('      <GuiElement Type="GUIGroup" ShowDebug="True" Name="KLH_CenterBox" AlignH="Right" X="-100" Y="-80" W="384" H="576">')
    ys = (358, 392, 425)                              # PlayMenu's two rows are at 392 and 425
    for k, (name, label, opt, vals) in enumerate(HEISTER_ROWS):
        L.append('        <GuiElement Type="TextBlock" FadeInDelay="%.2f" FadeInTime="0.2" Text="" Name="%s_Data" Y="%d" AlignH="Center" />' % (0.05 + 0.05 * k, name, ys[k] + 80 + (1 if k == 2 else 0)))
    L += ['      </GuiElement>',
          '      <GuiElement Type="GUIGroup" ShowDebug="True" Name="KLH_CenterBoxArrows" X="484" Y="-80" W="384" H="576" GeomSpace="2">']
    for msg, tpl in (('Decrease', 'OptionsArrowL_T'), ('Increase', 'OptionsArrowR_T')):
        for k, (name, label, opt, vals) in enumerate(HEISTER_ROWS):
            L.append('        <GuiElement Template="%s" X="0" Message="%s" FocusParent="%s" Receiver="%s" Y="%d"/>' % (tpl, msg, name, name, 430 + ROW * k))
    L.append('      </GuiElement>')
    for k, (name, label, opt, vals) in enumerate(HEISTER_ROWS):
        L.append('      <GuiElement Name="KLHfb#%02d" Graphic="FocusBar_long#%02d" Y="%d" X="-122" AlignH="Left" Template="FocusBar" />' % (k + 1, k + 4, 349 + ROW * k))
    for k, (name, label, opt, vals) in enumerate(HEISTER_ROWS):
        L += ['      <GuiElement Type="ToggleText" Text="%%%s" X="-100" Y="%d" Option="%s" FocusGraphic="KLHfb#%02d"' % (esc(label), ys[k], opt, k + 1),
              '          TextReceiver="%s_Data" UseTextReceiverAsFocus="True"%s' % (name, ' ToggleReceivers="%sPics"' % name if pictures and name in [r[0] for r in HEISTER_PICS] else ''),
              '          RecCSFocus="OnFocus" RecCSDefault="Default" FadeInDelay="%.2f" FadeInTime="0.2" Name="%s"' % (0.05 + 0.05 * k, name),
              '          Template="TextIndentX" AlignV="Left" HelpText="/Menu/Generic/UseLRToSelect" HelpTextBlock="HelpPlay" >']
        L += ['        <Text Text="%%%s" />' % esc(v) for v in vals]
        L.append('      </GuiElement>')
    L += ['    </GuiElement>',
          '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
          '      <GuiElement Template="LongLineBottom"/>',
          '      <GuiElement Type="GUIGroup" Navigation="Horizontal" ReverseNavigation="True" Template="BottomFramePosSize" ShowDebug="True">',
          '        <Platform PC_KEYBOARD="True">',
          '          <GuiElement ReceiveAllInput="False" Template="ButtonBack_INV_GT" />',
          '          <GuiElement AlignH="Left" Template="BackButtonNoXPos_PC" HelpTextBlock="HelpPlay" HelpText=" " />',
          '        </Platform>',
          '        <Platform PC_GC="True">',
          '          <GuiElement Template="BottomFrameMenuBackButton"/>',
          '        </Platform>',
          '      </GuiElement>',
          '    </GuiElement>',
          '  </Window>']
    return nl.join(L) + nl


# THE GUNS PAGE (2026-10-09; NOT SEEN IN THE GAME YET): a button 'Guns' under 'Heister' and a window KLGuns with two
# rows, bound to options klhook\klgun.c answers (KLGunStart, KLGunSet). The looks themselves are in a level built by
# tools\kl_guns.py (KLGuns.ini beside its archive); on any other level the rows do nothing. Off with [Guns] Menu=0.
# The entry counts ARE the option ranges (as for the heister rows): klgun.c's klg_upper must agree.
GUNS_WINDOW = 'KLGuns'
GUNS = True
GUN_ROWS = (('KLG_Start', 'Starting rifle', 'KLGunStart', ['Zastava M85', 'MP5 (Dead Men)', 'AK-74']),
            ('KLG_Set', 'Shop guns', 'KLGunSet', ['Dog Days', 'Dead Men looks']))
GUNS_NOTE = ('Looks only: price, rank, stats and sound stay those of the Dog Days gun. Dead Men looks: SG 552 on the FN SCAR, '
             'M4A1 on the AK-47, P90 on the UMP, Steyr TMP on the MAC-10, USP on the M9 Beretta. Everyone who carries that gun shows it. '
             'Needs a map built with the guns.')


def guns_window(nl):
    """The window KLGuns: the heister page's row pattern (PlayMenu's two rows, at their stock places 392 and 425)."""
    ys = (392, 425)
    L = ['  <!-- KLExpansion: the guns page (mkoverlay.py; options answered by klgun.c) -->',
         '  <Window Name="%s" LocaleBasePath="AllLevels/Menu/Heist" Template="WindowDefault">' % GUNS_WINDOW,
         '    <GuiElement Template="BackgroundTemplate"/>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
         '      <GuiElement Template="HeadlineIcon" Graphic="Icon_Heist"/>',
         '      <GuiElement Template="HeadlineText" Text="%Guns"/>',
         '      <GuiElement Template="LongLineTop" />',
         '    </GuiElement>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
         '      <GuiElement Template="ChapterBackgroundTemplate"/>',
         '      <GuiElement Type="TextBlock" Name="KLG_Note" Text="%%%s" Font="Text" LineSpace="26" FadeInDelay="0.10" FadeInTime="0.2" AlphaMax="192" X="450" Y="64" AlignH="Left" TextWidth="430" W="300" H="400" />' % esc(GUNS_NOTE),
         '      <GuiElement Type="GUIGroup" ShowDebug="True" Name="KLG_CenterBox" AlignH="Right" X="-100" Y="-80" W="384" H="576">']
    for k, (name, label, opt, vals) in enumerate(GUN_ROWS):
        L.append('        <GuiElement Type="TextBlock" FadeInDelay="%.2f" FadeInTime="0.2" Text="" Name="%s_Data" Y="%d" AlignH="Center" />' % (0.05 + 0.05 * k, name, (472, 506)[k]))
    L += ['      </GuiElement>',
          '      <GuiElement Type="GUIGroup" ShowDebug="True" Name="KLG_CenterBoxArrows" X="484" Y="-80" W="384" H="576" GeomSpace="2">']
    for msg, tpl in (('Decrease', 'OptionsArrowL_T'), ('Increase', 'OptionsArrowR_T')):
        for k, (name, label, opt, vals) in enumerate(GUN_ROWS):
            L.append('        <GuiElement Template="%s" X="0" Message="%s" FocusParent="%s" Receiver="%s" Y="%d"/>' % (tpl, msg, name, name, 464 + ROW * k))
    L.append('      </GuiElement>')
    for k, (name, label, opt, vals) in enumerate(GUN_ROWS):
        L.append('      <GuiElement Name="KLGfb#%02d" Graphic="FocusBar_long#%02d" Y="%d" X="-122" AlignH="Left" Template="FocusBar" />' % (k + 1, k + 7, 383 + ROW * k))
    for k, (name, label, opt, vals) in enumerate(GUN_ROWS):
        L += ['      <GuiElement Type="ToggleText" Text="%%%s" X="-100" Y="%d" Option="%s" FocusGraphic="KLGfb#%02d"' % (esc(label), ys[k], opt, k + 1),
              '          TextReceiver="%s_Data" UseTextReceiverAsFocus="True"' % name,
              '          RecCSFocus="OnFocus" RecCSDefault="Default" FadeInDelay="%.2f" FadeInTime="0.2" Name="%s"' % (0.05 + 0.05 * k, name),
              '          Template="TextIndentX" AlignV="Left" HelpText="/Menu/Generic/UseLRToSelect" HelpTextBlock="HelpPlay" >']
        L += ['        <Text Text="%%%s" />' % esc(v) for v in vals]
        L.append('      </GuiElement>')
    L += ['    </GuiElement>',
          '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
          '      <GuiElement Template="LongLineBottom"/>',
          '      <GuiElement Type="GUIGroup" Navigation="Horizontal" ReverseNavigation="True" Template="BottomFramePosSize" ShowDebug="True">',
          '        <Platform PC_KEYBOARD="True">',
          '          <GuiElement ReceiveAllInput="False" Template="ButtonBack_INV_GT" />',
          '          <GuiElement AlignH="Left" Template="BackButtonNoXPos_PC" HelpTextBlock="HelpPlay" HelpText=" " />',
          '        </Platform>',
          '        <Platform PC_GC="True">',
          '          <GuiElement Template="BottomFrameMenuBackButton"/>',
          '        </Platform>',
          '      </GuiElement>',
          '    </GuiElement>',
          '  </Window>']
    return nl.join(L) + nl


def build(xml, pgs, heister=True, pictures=False):
    nl = '\r\n' if '\r\n' in xml else '\n'
    # the stock map page, whole
    w = one(r'[ \t]*<Window Name="HeistPlayMenu" [^>]*>.*?</Window>[ \t]*\r?\n', xml, 'the window HeistPlayMenu', re.S)
    page = w.group(0)
    gt = one(r'[ \t]*<Template Name="%s">.*?</Template>[ \t]*\r?\n' % GC_TEMPLATE, xml, 'the template ' + GC_TEMPLATE, re.S)
    taken = set(re.findall(r'\bName="([^"]+)"', xml))
    new = tpl = ''
    for n, title, ent, pg in pgs:
        suffix = '_P%d' % n
        mode = pg.get('Pictures', 'story').strip().lower()
        if mode not in ('story', 'slot'):
            raise SystemExit('[Page.%d] Pictures=%s: story or slot' % (n, pg.get('Pictures')))
        p = page.replace('<Window Name="HeistPlayMenu" ', '<Window Name="HeistPlayMenu%d" ' % n, 1)
        h = one(r'(<GuiElement Template="HeadlineText" Text=)"HeistTitle"', p, 'the headline')
        p = p[:h.start()] + h.group(1) + '"%%%s"' % esc(title) + p[h.end():]
        b = one(r'[ \t]*<GuiElement Type="MercsShowInfo" TagName="HeistBriefing"[^>]*/>[ \t]*\r?\n', p, 'the briefing element')
        p = p[:b.start()] + p[b.end():]
        for slot, (folder, name, pic) in sorted(ent.items()):
            t = one(r'<Text Text="/Menu/Online/Scenarios/Title%02d" />' % slot, p, 'the title of slot %d' % slot)
            p = p[:t.start()] + '<Text Text="%%%s" />' % esc(name) + p[t.end():]
            pic = pic or ('LevelPicture_L%02d' % slot if mode == 'story' else None)
            if pic:
                g = one(r'(Name="H%02d_LevelPicture" Template="LevelPicture_T" Graphic=)"LevelPicture_H%02d"' % (slot, slot), p, 'the picture of slot %d' % slot)
                p = p[:g.start()] + g.group(1) + '"%s"' % esc(pic) + p[g.end():]
        # the gamepad layout's Back / Accept: the page's own copy of the template (its Accept names the selector)
        u = one(r'<GuiElement Template="%s"\s*/>' % GC_TEMPLATE, p, 'the gamepad bottom frame')
        p = p[:u.start()] + '<GuiElement Template="%s%s"/>' % (GC_TEMPLATE, suffix) + p[u.end():]
        t = gt.group(0).replace('<Template Name="%s">' % GC_TEMPLATE, '<Template Name="%s%s">' % (GC_TEMPLATE, suffix), 1)
        # names of their own, references inside the copy rewritten
        names = defined(p)
        if len(set(names)) != len(names):
            raise SystemExit('the stock map page defines a name twice: %s' % sorted(x for x in set(names) if names.count(x) > 1))
        tnames = defined(t)
        clash = sorted(x + suffix for x in set(names) | set(tnames) if x + suffix in taken)
        if clash or '%s%s' % (GC_TEMPLATE, suffix) in taken:
            raise SystemExit('names already in frontend.xml: %s' % clash)
        p = rename(p, names, suffix)
        t = rename(t, set(names) | set(tnames), suffix)
        if 'Receiver="HeistLevel%s"' % suffix not in t or 'Name="HeistLevel%s"' % suffix not in p:
            raise SystemExit('the selector HeistLevel was not found where this script expects it')
        taken |= {x + suffix for x in set(names) | set(tnames)}
        new += nl + '  <!-- KLExpansion page %d: a copy of HeistPlayMenu with names of its own (mkoverlay.py) -->' % n + nl + p
        tpl += nl + '\t<!-- KLExpansion page %d: the gamepad bottom frame of HeistPlayMenu%d (mkoverlay.py) -->' % (n, n) + nl + t
    if heister:
        if HEISTER in taken or any(x.startswith('KLH') for x in taken):
            raise SystemExit('names already in frontend.xml: KLH...')
        new += nl + heister_window(nl, pictures)
    if GUNS:
        if GUNS_WINDOW in taken or any(x.startswith('KLG') for x in taken):
            raise SystemExit('names already in frontend.xml: KLG...')
        new += nl + guns_window(nl)
    xml = xml[:w.end()] + new + xml[w.end():]          # the window stands behind the template in the file
    xml = xml[:gt.end()] + tpl + xml[gt.end():]
    # the Arcade page: option on the stock button; per page a button, focus bar, icon and line; all rows moved up
    a = one(r'[ \t]*<Window Name="HeistModeMenu" [^>]*>.*?</Window>', xml, 'the window HeistModeMenu', re.S)
    arc = a.group(0)
    s = one(r'(<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu" Text="Button_StartHeist"\s+FocusGraphic="HMfbl#01" FadeInDelay="0\.15" Y="220")(/>)', arc, 'the Start button')
    arc = arc[:s.start()] + s.group(1) + ' Option="Dummy" OptionValue="1"' + s.group(2) + arc[s.end():]
    g = one(r'(<GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y=)"110"(>)', arc, 'the group of the rows')
    rows = ([(HEISTER, 'Heister', None, None)] if heister else []) + ([(GUNS_WINDOW, 'Guns', None, None)] if GUNS else []) + [('HeistPlayMenu%d' % n, title, pg.get('Icon'), n) for n, title, ent, pg in pgs]
    if len(rows) > len(ICONS):
        raise SystemExit('%d added buttons: the Arcade page has room for %d (with the Heister button: pages 2..4)' % (len(rows), len(ICONS)))
    arc = arc[:g.start()] + g.group(1) + '"%d"' % (110 - ROW * len(rows)) + g.group(2) + arc[g.end():]
    f1 = one(r'([ \t]*)<GuiElement Name="HMfbl#01" Y="211" [^>]*/>', arc, 'the first focus bar')
    f5 = one(r'[ \t]*<GuiElement Name="HMfbl#05" Y="347" [^>]*/>[ \t]*\r?\n', arc, 'the fifth focus bar')
    i5 = one(r'([ \t]*)<GuiElement Type="Graphic" Graphic="Icon_Xbox_Live" Y="347" X="250" ([^>]*)/>[ \t]*\r?\n', arc, 'the fifth icon')
    l5 = one(r'([ \t]*)<GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#06" AnimY="380" />[ \t]*\r?\n', arc, 'the fifth line')
    ind = f1.group(1); btn = bars = icons = lines = ''
    for i, (win, title, icon, n) in enumerate(rows):
        k = 6 + i; y = 390 + ROW * i; icon = (icon or ICONS[i]).strip()
        btn += (ind + '<GuiElement Type="OpenWindow" Template="HM_Button" Window="%s" Text="%%%s"' % (win, esc(title)) + nl +
                ind + '            FocusGraphic="HMfbl#%02d" FadeInDelay="0.15" Y="%d"%s/>' % (k, y, ' Option="Dummy" OptionValue="%d"' % n if n else '') + nl + nl)
        bars += ind + '<GuiElement Name="HMfbl#%02d" Y="%d" Graphic="FocusBar_short#%02d" Template="HM_FocusBar" MouseFocusW="239" />' % (k, y - 9, k) + nl
        icons += i5.group(1) + '<GuiElement Type="Graphic" Graphic="%s" Y="%d" X="250" %s/>' % (esc(icon), y - 9, i5.group(2)) + nl
        lines += l5.group(1) + '<GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#%02d" AnimY="%d" />' % (k + 1, y + 24) + nl
    # insert from the back of the window to the front, so that the earlier matches keep their offsets
    for m, text in sorted(((f5, bars), (l5, lines), (i5, icons)), key=lambda x: -x[0].end()):
        arc = arc[:m.end()] + text + arc[m.end():]
    f1 = one(r'([ \t]*)<GuiElement Name="HMfbl#01" Y="211" [^>]*/>', arc, 'the first focus bar')
    arc = arc[:f1.start()] + ind + '<!-- KLExpansion: one button per expansion page (mkoverlay.py) -->' + nl + btn + arc[f1.start():]
    return xml[:a.start()] + arc + xml[a.end():]


def check(stock, res, pgs, heister=True):
    """What must hold for the result, whatever the game does with it. -> list of faults."""
    bad = []
    plain = re.sub(r'<!--.*?-->', '', res, flags=re.S)
    wins = {m.group(1): m.group(0) for m in re.finditer(r'<Window Name="([^"]+)"[^>]*>.*?</Window>', plain, re.S)}
    first = {}
    for m in re.finditer(r'<Window Name="([^"]+)"[^>]*>.*?</Window>', plain, re.S):
        for nm in defined(m.group(0)):
            first.setdefault(nm, m.group(1))                 # the window the game's look-up finds for a name
    for n, title, ent, pg in pgs:
        w = wins.get('HeistPlayMenu%d' % n)
        if not w:
            bad.append('window HeistPlayMenu%d is missing' % n); continue
        own = set(defined(w))
        for nm in own:
            if first[nm] != 'HeistPlayMenu%d' % n:
                bad.append('HeistPlayMenu%d: the name %s is found in window %s first' % (n, nm, first[nm]))
        refs = [v.strip() for a in REFS for x in re.findall(r'\b%s="([^"]*)"' % a, w) for v in x.split(',') if v.strip()] + re.findall(r'<Graphic Graphic="([^"]+)"', w)
        for r in sorted(set(refs)):
            if r not in own and r in first and first[r] == 'HeistPlayMenu':
                bad.append('HeistPlayMenu%d refers to %s, an element of the stock map page' % (n, r))
        if len(re.findall(r'<Text Text=', one(r'<GuiElement Type="MercsLevelSelectorHeist".*?</GuiElement>', w, 'the selector of page %d' % n, re.S).group(0))) != 9:
            bad.append('HeistPlayMenu%d: the selector does not have nine entries' % n)
    if wins.get('HeistPlayMenu') != {m.group(1): m.group(0) for m in re.finditer(r'<Window Name="([^"]+)"[^>]*>.*?</Window>', re.sub(r'<!--.*?-->', '', stock, flags=re.S), re.S)}.get('HeistPlayMenu'):
        bad.append('the stock map page changed')
    arc = wins['HeistModeMenu']
    nrows = len(pgs) + (1 if heister else 0) + (1 if GUNS else 0)
    if GUNS:
        w = wins.get(GUNS_WINDOW)
        if not w:
            bad.append('window %s is missing' % GUNS_WINDOW)
        else:
            own = defined(w)
            for nm in own:
                if first[nm] != GUNS_WINDOW or own.count(nm) != 1:
                    bad.append('%s: the name %s is defined twice or found in window %s first' % (GUNS_WINDOW, nm, first[nm]))
            for r in sorted({v.strip() for a in REFS for x in re.findall(r'\b%s="([^"]*)"' % a, w) for v in x.split(',') if v.strip()}):
                if r not in own and r != 'HelpPlay':
                    bad.append('%s refers to %s, which the page does not define' % (GUNS_WINDOW, r))
            for name, label, opt, vals in GUN_ROWS:
                t = re.search(r'<GuiElement Type="ToggleText"[^>]*Option="%s"[^>]*>(.*?)</GuiElement>' % opt, w, re.S)
                if not t or len(re.findall(r'<Text Text=', t.group(1))) != len(vals):
                    bad.append('%s: the row of option %s does not have %d entries' % (GUNS_WINDOW, opt, len(vals)))
            bars = re.findall(r'Graphic="(FocusBar_long#\d+)"', w) + re.findall(r'Graphic="(FocusBar_long#\d+)"', wins.get(HEISTER, ''))
            if len(set(bars)) != len(bars):
                bad.append('%s and %s use one focus bar entity twice: %s' % (GUNS_WINDOW, HEISTER, bars))
    if heister:
        w = wins.get(HEISTER)
        if not w:
            bad.append('window %s is missing' % HEISTER)
        else:
            own = defined(w)
            for nm in own:
                if first[nm] != HEISTER or own.count(nm) != 1:
                    bad.append('%s: the name %s is defined twice or found in window %s first' % (HEISTER, nm, first[nm]))
            refs = [v.strip() for a in REFS for x in re.findall(r'\b%s="([^"]*)"' % a, w) for v in x.split(',') if v.strip()]
            for r in sorted(set(refs)):
                if r not in own and r != 'HelpPlay':         # HelpPlay: named by the stock pages too, defined by none
                    bad.append('%s refers to %s, which the page does not define' % (HEISTER, r))
            for name, label, opt, vals in HEISTER_ROWS:
                t = re.search(r'<GuiElement Type="ToggleText"[^>]*Option="%s"[^>]*>(.*?)</GuiElement>' % opt, w, re.S)
                if not t or len(re.findall(r'<Text Text=', t.group(1))) != len(vals):
                    bad.append('%s: the row of option %s does not have %d entries' % (HEISTER, opt, len(vals)))
            tpl = set(re.findall(r'\bTemplate="([^"]+)"', w)) - set(re.findall(r'<Template Name="([^"]+)"', plain))
            if tpl:
                bad.append('%s uses templates frontend.xml does not define: %s' % (HEISTER, sorted(tpl)))
    ys = re.findall(r'Template="HM_Button"[^>]*?\bY="(\d+)"', arc, re.S)     # stock has several per row (<Platform> alternatives)
    if len(set(ys)) != 5 + nrows or any(ys.count(str(390 + ROW * i)) != 1 for i in range(nrows)):
        bad.append('HeistModeMenu: buttons at Y %s' % ys)
    used = re.findall(r'Type="Graphic" Graphic="([^"]+)"', arc) + re.findall(r'Template="HeadlineIcon" Graphic="([^"]+)"', arc)
    if len(set(used)) != len(used):
        bad.append('HeistModeMenu: an icon entity is used twice: %s' % sorted(x for x in set(used) if used.count(x) > 1))
    for what, pat in (('focus bar', r'Graphic="(FocusBar_short#\d+)"'), ('line', r'Graphic="(Line_Short_01#\d+)"')):
        v = re.findall(pat, arc)
        if len(set(v)) != len(v):
            bad.append('HeistModeMenu: a %s entity is used twice: %s' % (what, v))
    return bad


def main():
    pictures = '--pictures' in sys.argv[1:]
    if len(sys.argv) - pictures != 4:
        raise SystemExit(__doc__)
    ini, stock, out = [a for a in sys.argv[1:] if a != '--pictures']
    pgs = pages(ini)
    cp = configparser.RawConfigParser(strict=False, delimiters=('=',), comment_prefixes=(';', '#'), interpolation=None)
    cp.read(ini)
    heister = not cp.has_section('Character') or (cp.get('Character', 'Enable', fallback='1').strip() != '0' and cp.get('Character', 'Menu', fallback='1').strip() != '0')
    global GUNS
    GUNS = not cp.has_section('Guns') or (cp.get('Guns', 'Enable', fallback='1').strip() != '0' and cp.get('Guns', 'Menu', fallback='1').strip() != '0')
    if not pgs and not heister:
        raise SystemExit('no [Redirect.2] .. [Redirect.5] section with F01..F09 lines in %s and the heister page is off: nothing to build' % ini)
    z = zipfile.ZipFile(stock)
    names = {i.filename.lower(): i for i in z.infolist()}
    if MEMBER not in names:
        raise SystemExit('%s has no %s' % (stock, MEMBER))
    raw = z.read(names[MEMBER]); xml = raw.decode('latin-1')
    new = build(xml, pgs, heister, pictures)
    bad = check(xml, new, pgs, heister)
    if bad:
        raise SystemExit('the result breaks its own rules, nothing written:\n  ' + '\n  '.join(bad))
    res = new.encode('latin-1')
    dst = os.path.join(out, 'Overlay'); os.makedirs(dst, exist_ok=True); path = os.path.join(dst, 'Patch01.zip')
    if os.path.exists(path) and os.path.samefile(path, stock):
        raise SystemExit('refusing to write over the stock archive')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():                       # same members, same order, same names
            if i.filename.lower() == MEMBER:
                n = zipfile.ZipInfo(i.filename, time.localtime()[:6]); n.compress_type = zipfile.ZIP_DEFLATED; n.external_attr = i.external_attr
                o.writestr(n, res)
            else:
                n = zipfile.ZipInfo(i.filename, i.date_time); n.compress_type = i.compress_type; n.external_attr = i.external_attr
                o.writestr(n, z.read(i))
    # read back and say what is in it
    c = zipfile.ZipFile(path); back = c.read(names[MEMBER].filename)
    assert back == res and all(c.read(i.filename) == z.read(i.filename) for i in z.infolist() if i.filename.lower() != MEMBER)
    print('%s: %d members, %s %d -> %d bytes (stock sha1 %s)' % (path, len(c.namelist()), MEMBER, len(raw), len(res), hashlib.sha1(raw).hexdigest()[:12]))
    h = (1 if heister else 0) + (1 if GUNS else 0)
    if GUNS:
        print('  guns page: Arcade button %d (icon %s) -> window %s; rows %s' % (6 + (1 if heister else 0), ICONS[1 if heister else 0], GUNS_WINDOW, ', '.join('%s (%s, %d entries)' % (r[1], r[2], len(r[3])) for r in GUN_ROWS)))
    if heister:
        if pictures:
            print(r'  heister page: WITH PICTURES - needs Overlay\Scenes\kaneandlynch.zip of tools\kl_portraits.py beside it (%s)' % ', '.join('%d for %s' % (len(r[2]), r[1]) for r in HEISTER_PICS))
        print('  heister page: Arcade button 6 (icon %s) -> window %s; rows %s' % (ICONS[0], HEISTER, ', '.join('%s (%s, %d entries)' % (r[1], r[2], len(r[3])) for r in HEISTER_ROWS)))
    for k, (n, title, ent, pg) in enumerate(pgs):
        mode = pg.get('Pictures', 'story').strip().lower()
        print('  page %d "%s": Arcade button %d (icon %s) -> window HeistPlayMenu%d; selector HeistLevel_P%d; Dummy = %d' % (n, title, 6 + h + k, pg.get('Icon', ICONS[h + k]).strip(), n, n, n))
        for e, slot in enumerate(ORDER):
            if slot in ent:
                pic = ent[slot][2] or ('LevelPicture_L%02d' % slot if mode == 'story' else 'LevelPicture_H%02d' % slot)
                print('     entry %d = slot F%02d: "%s" from Maps\\%s, picture %s' % (e, slot, ent[slot][1], ent[slot][0], pic))
    print('  Arcade page: rows moved up by %d (group Y %d)' % (ROW * (len(pgs) + h), 110 - ROW * (len(pgs) + h)))
    print('  windows %d -> %d, elements <GuiElement %d -> %d' % (xml.count('<Window '), res.count(b'<Window '), xml.count('<GuiElement'), res.count(b'<GuiElement')))


if __name__ == '__main__':
    main()
