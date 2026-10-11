#!/usr/bin/env python3
r"""
The menu pages and the round-over board in the owner's brush-kit look (2026-10-11, track M; review round the same
day: re\hud_menu.md 'Review round'). NOTHING OF IT HAS RUN IN THE GAME. What can and cannot be done this way, page
by page: re\hud_menu.md.

    python kl_hud_menu.py apply <overlay in> <overlay out> [--look deadmen] [--online-in-patch] [--no-pictures] [--bars kit|hud]
        <overlay in> is a folder with Patch01.zip and Scenes\kaneandlynch.zip (klhook\mkoverlay.py + tools\kl_portraits.py
        + tools\kl_hud.py's menu fonts, e.g. <work>\build\hud_menu\Overlay). Both files are written to <overlay out>;
        the input is only read.
          XML      menu/frontend.xml and menu/ingame.xml (Patch01.zip), Menu/online.xml (the menu scene's copy; with
                   --online-in-patch ALSO as a new member Menu/online.xml of Patch01.zip, for the pages inside a level):
                   colour sets in the kit's colours, money in green, penalties coral, the traitor line orange.
          pictures the menu scene's .TEX: the focus bars (FocusBar_*, MenuFocus_*) repainted as chalk brush strokes, the
                   separator lines (Line_*) as dry-brush lines. No entity, chunk or texture id is added or moved.
          --bars   kit (default) = this file's stroke: solid chalk, edges that wander in runs of 20-40 px, slanted
                   hand-cut ends, a few dry streaks that start at an end; no pinholes, no cuts through the bar.
                   hud = tools\kl_hud.py's own stroke painter (the HUD's picture 111, by import), cut to the bar.
        `apply` adds NO element: --board is refused here (an overlay's online.xml is loaded at the MENU and, in
        Patch01.zip, would reach every level of the game - TABLE below).
    python kl_hud_menu.py level <level archive or build folder> <out folder> [--board] [--bars kit|hud]
        The same pictures and the same Menu/online.xml restyle on ONE level archive (the pages inside a level take
        their bars and lines from the level's own .TEX and their online.xml from the level's archive). Writes
        <out folder>\<name>_Main.zip only; the files beside the archive are not copied.
          --board  ALSO adds the crew (name, fate, score) to the Arcade round-over pages HeistStatus and
                   HeistStatus_EndGame of THAT level. This ADDS 48 elements = it shifts the menu manager's table.
                   Only after live check K0 (re\hud_menu.md 7) has given the level's live count.
    python kl_hud_menu.py check <overlay> [<reference overlay>] [--menu-count N]
        Tag balance of the three XML files, every template / colour set / font / picture a page names, the names
        kl2.exe looks up, the TABLE, the scene archive against the reference. Exit 1 on a FAIL. N = the live count
        of the table at the main menu with the REFERENCE installed (K0's log line): with it a table that grew is
        tested against the budget of 5000.
    python kl_hud_menu.py check-level <level archive> <source archive> [--level-count N]
        The same for one level archive made by `level`: only the .TEX and Menu/online.xml may differ, texture ids
        and sizes as in the source, online.xml's tags, names and table against the source's. N as above, read at
        a round-over page of that level.
    python kl_hud_menu.py diff <overlay a> <overlay b>
        What differs, per file and window (attributes by name), colour sets (each definition of a doubled name),
        repainted textures.
    python kl_hud_menu.py sheet <overlay> <out.png>      the repainted bars and lines on dark grey, to look at
    python kl_hud_menu.py abi <kl2.exe> <overlay>        window / element names of the XML that kl2.exe holds as strings
                                                         with a reference (how KNOWN_* below were made; a LOWER bound:
                                                         a name built or compared another way is not found)

TABLE - the fault class of the menu crash of 2026-10-10 14:24 (READ IN kl2.exe, debug\dasm.py; the dump
<work>\research\crash_1010_1424\KLHook_1.dmp; the menu scene's .prp):
  every <Window>, every created <GuiElement>, every <ColorSet> and <ButtonGraphic> gets the next slot of ONE table of
  5096 {object, kind} pairs in the menu manager [[0xdd265c]+0x824], in file order (kind 0 element 0x7fad5d, 1 window
  0x667e5e, 2 colour set 0x47d641, 3 button graphic 0x53c781; an element keeps its index at +0x5c; overflow = int3
  at 0x7fad8d). ZXMLGUISystem (it holds the same manager at +0x4b4, stored at 0x8a43d8) slot 25 = 0x861720, the
  mouse over a menu picture: takes an id from the object under the cursor (vtable +0x2b0; for a ZBUTTON that is
  0x83d5d0 = [button+0x60]), index = id & 0xffff, fetches table[index] with only a 'below the count' test (0x8d1c10)
  and calls vtable +0x84 on it WITHOUT a kind test. A ZBaseWindow's vtable (0xbaf6c4) has the float 1.0 at +0x84:
  a window there = a call to 0x3f800000.
  THE DANGEROUS INDEX IS 5000: of the 121 ZBUTTONs of the menu scene exactly one carries a non-zero integer
  property, ZWINDOWS\Menu\DefaultFocus = 5000 (the 120 pool / slider buttons carry 0), and the dump has ebx = 0x1388.
  (That this property is what is loaded into [button+0x60] is inferred from the dump, not read in the loader.)
  While the table holds 5000 entries or fewer, entry 5000 does not exist and nothing happens - stock. Past 5000,
  entry 5000 is whatever the XML put there.
  THE RULE: a load set (menu = frontend.xml + online.xml; level = ingame.xml + online.xml) must keep its live
  count <= 5000, or its entry 5000 must be an element. The live counts are NOT KNOWN (live check K0 logs them).
  `apply` changes attribute VALUES and adds attributes only; `check` proves that the sequence of table-making tags
  of every file equals the reference's - then every index and the count are what they were. `level --board`
  breaks that on purpose for the tail of ONE level's online.xml; `check-level` says so (NOTE 'TABLE SHIFT') and,
  given --level-count, tests the budget.

ASSUMPTIONS (none seen in the game):
  - an attribute on the element wins over the same attribute of its template (stock does it with AlignH, X, Y);
    a ColorSet= on a MercsShowInfo* element is taken (stock: IsWeaponAvailable ColorSet="Header").
  - the colour sets 'Debug' (three files), 'DirtyMoneyColorSet', 'WANTED', 'Black' (online.xml) are named by NO XML
    ELEMENT of the three files. That code never asks for them by name is NOT shown (a set name need not stand in
    the exe as a string with a reference: 'White', named by 87 elements, does not). They become GREEN (money),
    ORANGE (traitor) and INK.
  - the reader takes NormalColor / FocusColor / DisableColor (0x8ab978..0x8ab988, the only three names; kl2.exe has
    no string 'DisabledColor'). online.xml's last four sets spell the third 'DisabledColor' = not read: the three
    spare ones get a real DisableColor= added (an attribute, no table entry); the second 'Default' is left as it is.
  - a focus bar may be an 'ABGR' texture where stock has DXT5 (the stock icons and lines are ABGR).
  - Line_* are drawn additively (their draw-mode word differs from the bars' DRAWMODE_OPACITY; stock is one row of
    grey 26 on opaque black): the new line is brighter rows on the same black.
  - Patch01.zip's Menu/online.xml overrides the level archives' copy (--online-in-patch; mount rule of CLAUDE.md, not run).
"""
import os, re, struct, sys, zipfile, hashlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ------------------------------------------------------------------ the look (re\hud_layout.md 'Colours')
CHALK = (0xf3, 0xf0, 0xea)
INK = (0x0c, 0x0c, 0x0d)
CORAL = (0xf0, 0x47, 0x5a)
ORANGE = (0xe8, 0x83, 0x1f)
GREEN_HI = (0x63, 0xa6, 0x5b)
GREEN = (0x4f, 0x8f, 0x49)
DEAD = (0x8c, 0x31, 0x38)
DIM = (0x8d, 0x89, 0x82)                # the draft's #8d8982: labels out of focus, disabled text
LOOKS = ('deadmen',)

FRONT, INGAME, ONLINE = 'menu/frontend.xml', 'menu/ingame.xml', 'Menu/online.xml'
SCENE_ZIP, PATCH_ZIP = os.path.join('Scenes', 'kaneandlynch.zip'), 'Patch01.zip'
COLOR_ATTRS = ('NormalColor', 'FocusColor', 'DisableColor')      # what kl2.exe reads (0x8ab978..0x8ab988)
DEAD_ATTR = 'DisabledColor'                                       # online.xml's misspelling: read by nothing, listed only
ZIP_STAMP = (2026, 10, 11, 0, 0, 0)                               # for members this tool adds: the same bytes every build
TABLE_CAP, TABLE_SAFE = 0x13e8, 5000                              # int3 past the first; entry TABLE_SAFE is DefaultFocus's
# spare colour sets -> (normal, focus, disabled) as ARGB. Alpha is ff on purpose (stock 'Debug' has 80 normal, stock
# 'WANTED' 00 disabled): these are data texts now.
# The focus colour stays the bright one: the rows that show money (status, leaderboards) have FAINT focus bars
# (AlphaMax 64; stock gives those rows the set 'White' for that reason), not the bright bar of a menu entry. (The
# draft's dark 'money on a painted row' green has no use here: the shop's price stands under the list, on no bar.)
SPARE = {'Debug': ((0xff,) + GREEN_HI, (0xff,) + GREEN_HI, (0xff,) + GREEN),
         'DirtyMoneyColorSet': ((0xff,) + GREEN_HI, (0xff,) + GREEN_HI, (0xff,) + GREEN),
         'WANTED': ((0xff,) + ORANGE, (0xff,) + ORANGE, (0xff,) + DEAD),
         'Black': ((0xff,) + INK, (0xff,) + INK, (0xff,) + INK)}
GREEN_SET = {FRONT: 'Debug', INGAME: 'Debug', ONLINE: 'DirtyMoneyColorSet'}
ORANGE_SET = {ONLINE: 'WANTED'}
# what a data element shows (TagName; compiled in kl2.exe, re\menus.md 2.4) -> the colour it gets
MONEY_TAGS = {'StatusTotal', 'StatusTotalIngame', 'StatusTotalShifted', 'StatusTeamTotal', 'StatusSplit', 'StatusSplitIngame',
              'StatusRewards', 'StatusRewardsIngame', 'MoneyTotal', 'RoundGrab', 'RoundSplit', 'PackagePrice',
              'HeistLLBTotalMoney', 'HeistLBTotalMoney', 'LBTotalMoney', 'HeistStatusLeaderboardPoints',
              'HeistPointsEscape', 'HeistPointsNPCEscape', 'HeistPointsLoot', 'HeistPointsTime', 'HeistPointsKills',
              'HeistBonusRound', 'HeistPointsRound', 'HeistPointsTotal', 'ProfileBestGrab', 'ProfileLootMoney',
              'ProfileRewardMoney', 'ProfileHeistRoundPoints', 'ProfileHeistSessionPoints'}
PENALTY_TAGS = {'HeistPointsYellow', 'HeistPointsCivilians', 'HeistPenaltyRound', 'HeistPointsDropLoot', 'HeistPointsRogue', 'KilledBy'}
TRAITOR_TAGS = {'HeistPointsTraitor'}
TRAITOR_TEXTS = {'HeistTraitorMalus'}          # a TextBlock's Text= key (the penalty row's label)
MAY_REPLACE = ('Default', 'White')             # an element's own ColorSet= that the money / penalty colour may replace

# --board: the crew on the Arcade round-over pages (positions are GUESSES from the stock page's numbers; nothing seen)
BOARD_WINDOWS = (('HeistStatus', ''), ('HeistStatus_EndGame', '_E'))
BOARD_Y0, BOARD_PITCH = 418, 27                # under the tables' last double line (AnimY 398), above the bottom line (534)
BOARD_NAME_X = (-125, 395)                     # the two columns' left edges = the 'Bonus' / 'Penalty' headings'
BOARD_FATE_DX = 170
BOARD_CASH_RX = (418, -107)                    # right-aligned: frame width 768 - the value columns' right edges (350, 875)
BOARD_NAME_TAG, BOARD_CASH_TAG = 'StatusPlayerName', 'StatusTotal'

# pictures
BAR_RE = re.compile(r'^(FocusBar_|MenuFocus_)')
LINE_RE = re.compile(r'^Line_')
BAR_ALPHA_MIN = 24                             # a stock pixel counts as paint above this alpha
BAR_DARK_SHARE = 0.03                          # a stock bar with this share of dark opaque pixels has a drawing in it: left alone
# the 'kit' stroke (LIGHT: the owner found speckle and breaks overdone twice - none of either here)
BAR_RUN = (20, 40)                             # the top / bottom edge holds its height over runs of this many pixels
BAR_EDGE = (0, 0, 1)                           # ... at one of these insets (pixels); a run differs from its neighbour by 1 at most
BAR_SLANT = (2, 4)                             # a hand-cut end leans by this many pixels over the bar's height
BAR_STREAKS = (2, 3)                           # dry streaks per cut end ...
BAR_STREAK_LEN = (14, 44)                      # ... each one row high, this long, starting AT the end, fading back into the paint
BAR_STREAK_ALPHA = 0.30                        # paint left in a streak at the end (1.0 where it rejoins)
BAR_STYLES = ('kit', 'hud')
LINE_ROWS = 2
LINE_LEVEL = 0.34                              # chalk times this (stock: grey 26 = 0.10)
LINE_GAP_EVERY = 64
ZWINGROUP, ZWINPIC = 0x10002e, 0x200046

# names of the XML that kl2.exe holds as a string with a reference (`abi`, 2026-10-11): renaming or dropping one breaks
# the code that looks it up. A LOWER BOUND: `check` therefore also fails on ANY name of the reference that is gone.
KNOWN_WINDOWS = ('AttractMode AutoSave BuyWeaponDialog CampaignMenu ControllerLossMenu Credits DifficultyScreen EidosPresentsMenu '
                 'FABuyWeaponsNew FACoopLobby FADead FAEscaped FALobby FAPlay FAQuitLobbyConfirm FARespawn FASessionClosingInterlude '
                 'FASessionCreatingInterlude FASessionSearchingInterlude FAStatus FAStatus_HostDisconnect FAWaitForPlayers '
                 'GameplayTrailer GetControllersCoopPC HeistLeaderboard HeistLocalLeaderboard HeistStatus HeistStatusLeaderboard '
                 'HeistStatusLeaderboard_EndGame IOErrorScreen IOErrorScreenOverwriteDamagedSaveGame IOErrorScreenPlay '
                 'IOErrorScreenQuit IOInteractiveMenu IOMissingContentScreen IngameCredits IngameInvite IngamePause '
                 'IngamePauseClient IngamePauseCoopHost IngamePauseFA KL2DogDaysMenu MissionFailedClient MissionFailedReload '
                 'OnlineMenu QuickJoinInterlude QuickJoinInterlude2 QuickPlayerMatch QuitGameMenu ResolutionFallBack SaveError '
                 'SaveInsufficientFreeSpace ShowHeistProfile ShowProfile StatusStyle StatusTeamKills SteamIPCFailure '
                 'SysUIErrorScreen HeistStatus_EndGame FAStatus_Endgame FAStatus_Team HeistHighscore IngamePauseHeist').split()
KNOWN_ELEMENTS = ('CoopLobbyArrowL_1 CoopLobbyArrowL_2 CoopLobbyArrowR_2 CoopLobbyImageToggler CoopLobbyLevelNameToggler '
                  'CoopLobbyLevelWarning EndRound Headbar Headline0 Headline1 Headline2 LoadActiveSaveGame LoadSelectedScene '
                  'LobbyArrowL_1 LobbyArrowL_2 LobbyArrowL_3 LobbyArrowL_4 LobbyArrowR_1 LobbyImageToggler LobbyLevelNameToggler '
                  'MercsFASelectorWeapons Money Name Players QuitGame Ranked SInfoGameType SInfoMaxPlayers SInfoWelcomeMessage '
                  'SaveActiveSaveGame Scenario Style TeamHeadbar0 TeamHeadline0 TeamHeadline1 TeamHeadline2 Time Traitor Trust').split()
TABLE_TAGS = ('Window', 'GuiElement', 'ColorSet', 'ButtonGraphic')      # what takes a slot of the manager's table
REF_ATTRS = ('Receiver', 'TextReceiver', 'ToggleReceivers', 'FocusGraphic', 'FocusParent', 'HelpTextBlock', 'HelpTextBlock2',
             'Receivers', 'FocusBar', 'AlignTo', 'InfoTextReceiver', 'IndexReceiver')


# ------------------------------------------------------------------ XML as the game's reader sees it: tags, no entities
COMMENT = re.compile(r'<!--.*?-->', re.S)
# stock writes four tags with two attributes glued together ('FadeInTime="0.03"Priority="15"', 'X="-75"TakeFocus=..'):
# no white space is asked for between attributes, only after the tag's name
TAG = re.compile(r'<(/?)([A-Za-z][A-Za-z0-9_]*)((?:\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*"[^"]*"(?:\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*"[^"]*")*)?)\s*(/?)>', re.S)
ATTR = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"')
Tag = collections.namedtuple('Tag', 'start end close name attrs selfclose window')


def tags(xml):
    """Every tag outside comments, in file order, with the window it stands in ('' = the templates part)."""
    plain = COMMENT.sub(lambda m: ' ' * len(m.group(0)), xml)
    out, win = [], ''
    for m in TAG.finditer(plain):
        close, name = bool(m.group(1)), m.group(2)
        attrs = ATTR.findall(m.group(3))
        if name == 'Window' and not close:
            win = dict(attrs).get('Name', '?')
        out.append(Tag(m.start(), m.end(), close, name, attrs, bool(m.group(4)), win))
        if name == 'Window' and close:
            win = ''
    return out


def anomalies(xml):
    """What a strict reader would trip over: text between tags that holds '<' or '>', and tags that do not nest."""
    plain = COMMENT.sub(lambda m: ' ' * len(m.group(0)), xml)
    bad, pos, stack = [], 0, []
    for m in TAG.finditer(plain):
        gap = plain[pos:m.start()]
        if '<' in gap or '>' in gap:
            bad.append('stray text %r' % gap.strip()[:50])
        pos = m.end()
        if m.group(1):
            if not stack or stack[-1] != m.group(2):
                bad.append('</%s> closes %s' % (m.group(2), stack[-1] if stack else 'nothing'))
                if m.group(2) in stack:
                    while stack.pop() != m.group(2):
                        pass
            else:
                stack.pop()
        elif not m.group(4):
            stack.append(m.group(2))
    gap = plain[pos:]
    if '<' in gap or '>' in gap:
        bad.append('stray text %r' % gap.strip()[:50])
    bad += ['<%s> is never closed' % s for s in stack]
    return bad


def signature(xml):
    """The sequence that decides the menu manager's table (and what instancing a template adds to it)."""
    out = []
    for t in tags(xml):
        if t.close:
            if t.name in TABLE_TAGS or t.name in ('Template', 'Platform', 'ExcludeIn', 'Locale', 'GameRegion', 'BuildTag', 'MainIniOption'):
                out.append('/' + t.name)
            continue
        a = dict(t.attrs)
        if t.name in TABLE_TAGS or t.name == 'Template':
            out.append('%s|%s|%s|%s%s' % (t.name, a.get('Name', ''), a.get('Type', ''), a.get('Template', ''), '/' if t.selfclose else ''))
        elif t.name in ('Platform', 'ExcludeIn', 'Locale', 'GameRegion', 'BuildTag', 'MainIniOption'):
            out.append('%s|%s%s' % (t.name, ','.join('%s=%s' % kv for kv in t.attrs), '/' if t.selfclose else ''))
        elif t.name in ('Text', 'Graphic', 'GraphicElement'):
            out.append(t.name)
    return out


def set_attr(text, name, value):
    """A tag's text with attribute name=value: the first one replaced, or a new one put before the closing bracket."""
    m = re.search(r'(?<![A-Za-z0-9_])%s\s*=\s*"[^"]*"' % re.escape(name), text)
    if m:
        return text[:m.start()] + '%s="%s"' % (name, value) + text[m.end():]
    e = re.search(r'\s*/?>$', text)
    return text[:e.start()] + ' %s="%s"' % (name, value) + text[e.start():]


def rewrite(xml, fn):
    """fn(Tag, tag text) -> new tag text or None; applied to every opening tag outside comments."""
    out, pos, n = [], 0, 0
    for t in tags(xml):
        if t.close:
            continue
        new = fn(t, xml[t.start:t.end])
        if new is not None and new != xml[t.start:t.end]:
            out.append(xml[pos:t.start]); out.append(new); pos = t.end; n += 1
    out.append(xml[pos:])
    return ''.join(out), n


# ------------------------------------------------------------------ colours
def _role(argb):
    """A stock colour -> the kit's colour of the same role (alpha kept), or None to leave it alone."""
    a, r, g, b = argb
    if abs(r - g) <= 6 and abs(g - b) <= 6:
        return (a,) + (CHALK if r >= 0xd0 else INK if r <= 0x10 else DIM)
    if r >= g + 0x40 and r >= b + 0x40:
        return (a,) + (CORAL if r >= 0xc0 else DEAD)
    return None


def _hex(v):
    m = re.fullmatch(r'0[xX]([0-9a-fA-F]{8})', v.strip())       # the stock files hold two malformed values: left alone
    return tuple(bytes.fromhex(m.group(1))) if m else None


def restyle_colorsets(xml):
    def fn(t, text):
        if t.name != 'ColorSet':
            return None
        name = dict(t.attrs).get('Name', '')
        if name in SPARE:                                   # all three, DisableColor ADDED where the file misspells it
            for an, new in zip(COLOR_ATTRS, SPARE[name]):
                text = set_attr(text, an, '0x%02x%02x%02x%02x' % new)
            return text
        for an, av in t.attrs:                              # 'DisabledColor' (read by nothing) is left as it stands
            if an in COLOR_ATTRS:
                old = _hex(av)
                new = _role(old) if old else None
                if new:
                    text = set_attr(text, an, '0x%02x%02x%02x%02x' % new)
        return text
    return rewrite(xml, fn)


def colorsets(xml):
    """{name: colours} - for the NAMES; a name defined twice shows its last definition (colorset_list has both)."""
    return collections.OrderedDict((dict(t.attrs).get('Name', ''), [v for k, v in t.attrs if k in COLOR_ATTRS])
                                   for t in tags(xml) if t.name == 'ColorSet' and not t.close)


def colorset_list(xml):
    """[((name, occurrence), 'Attr=value ...')] in file order: online.xml defines 'Default' twice, every file 'Legend'."""
    seen, out = collections.Counter(), []
    for t in tags(xml):
        if t.name == 'ColorSet' and not t.close:
            n = dict(t.attrs).get('Name', ''); seen[n] += 1
            out.append(((n, seen[n]), ' '.join('%s=%s' % (k.replace('Color', ''), v) for k, v in t.attrs if k in COLOR_ATTRS or k == DEAD_ATTR)))
    return out


def restyle_data(xml, member):
    """Money green, penalties coral, the traitor line orange - by the ColorSet attribute of the element itself."""
    have = set(colorsets(xml))
    green = GREEN_SET.get(member); orange = ORANGE_SET.get(member)
    count = collections.Counter()

    def fn(t, text):
        if t.name != 'GuiElement':
            return None
        a = dict(t.attrs); tag = a.get('TagName'); want = None
        if tag in MONEY_TAGS:
            want = green
        elif tag in PENALTY_TAGS:
            want = 'Header'
        elif tag in TRAITOR_TAGS or (a.get('Type') == 'TextBlock' and a.get('Text') in TRAITOR_TEXTS):
            want = orange
        if not want or want not in have or a.get('ColorSet', 'Default') not in MAY_REPLACE:
            return None
        count[want] += 1
        return set_attr(text, 'ColorSet', want)
    xml, n = rewrite(xml, fn)
    return xml, count


# ------------------------------------------------------------------ --board
def board(xml, log=print):
    """The crew on the Arcade round-over pages: two columns of four rows, name / fate / score. The fate blocks are
    EMPTY text blocks with names (KLB_Fate<k>): what a heister's fate is no data tag tells - hook code would fill them.
    PlayerIndex k is a ROW, not a record number (READ, kl2 0x5bb49b / 0x5bb8bb): in Arcade both tags turn the row
    into a record by the rules' slot 0x188 = ZGameRulesHeist 0x5a0fa0: record = byte [[rules+0x368]+k] when
    [rules+0x1d4] != 0 and k < [rules+0x35c], else 0xff (record 0 for EVERY row while [rules+0x1d4] is 0). So name
    row k and score row k are the same heister, and whoever fills KLB_Fate<k> must read that byte table, not use k."""
    nl = '\r\n' if '\r\n' in xml else '\n'
    have = set(colorsets(xml)); added = 0
    for win, sfx in BOARD_WINDOWS:
        m = re.search(r'<Window Name="%s" [^>]*>.*?</Window>' % re.escape(win), xml, re.S)
        if not m:
            log('  --board: no window %s' % win); continue
        body = m.group(0)
        anchors = [t for t in tags(body) if t.name == 'GuiElement' and not t.close and dict(t.attrs).get('Template') == 'LongLineBottom']
        if len(anchors) != 1:
            log('  --board: %s has %d bottom lines, not 1: left alone' % (win, len(anchors))); continue
        if 'KLB_Name0' + sfx in body:
            log('  --board: %s already has the crew' % win); continue
        at = anchors[0].start
        ind = body[body.rfind('\n', 0, at) + 1:at]
        L = ['<!-- kl_hud_menu.py --board: the crew (name, fate, score) -->']
        for k in range(8):
            c, r = divmod(k, 4); y = BOARD_Y0 + BOARD_PITCH * r; d = 0.20 + 0.03 * k
            L.append('<GuiElement Type="MercsShowInfoFA" Name="KLB_Name%d%s" TagName="%s" PlayerIndex="%d" Font="Text" AlignH="Left" X="%d" Y="%d" FadeInTime="0.2" FadeInDelay="%.2f"/>'
                     % (k, sfx, BOARD_NAME_TAG, k, BOARD_NAME_X[c], y, d))
            L.append('<GuiElement Type="TextBlock" Name="KLB_Fate%d%s" Text="" Font="Text" ColorSet="Header" AlignH="Left" X="%d" Y="%d" FadeInTime="0.2" FadeInDelay="%.2f"/>'
                     % (k, sfx, BOARD_NAME_X[c] + BOARD_FATE_DX, y, d))
            L.append('<GuiElement Type="MercsShowInfoFA" Name="KLB_Cash%d%s" TagName="%s" PlayerIndex="%d" Font="Text"%s AlignH="Right" X="%d" Y="%d" FadeInTime="0.2" FadeInDelay="%.2f"/>'
                     % (k, sfx, BOARD_CASH_TAG, k, ' ColorSet="%s"' % GREEN_SET[ONLINE] if GREEN_SET[ONLINE] in have else '', BOARD_CASH_RX[c], y, d))
        body = body[:at] + (nl + ind).join(L) + nl + ind + body[at:]
        xml = xml[:m.start()] + body + xml[m.end():]
        added += len(L) - 1
        log('  --board: %s + %d elements (KLB_Name / KLB_Fate / KLB_Cash 0..7%s)' % (win, len(L) - 1, sfx))
    return xml, added


def restyle_xml(xml, member, do_board=False, log=print):
    xml, n1 = restyle_colorsets(xml)
    xml, cnt = restyle_data(xml, member)
    nb = 0
    if do_board and member == ONLINE:
        xml, nb = board(xml, log)
    log('  %s: %d colour sets, elements recoloured: %s%s' % (member, n1, ', '.join('%d %s' % (v, k) for k, v in sorted(cnt.items())) or 'none',
                                                             ', %d board elements' % nb if nb else ''))
    return xml


# ------------------------------------------------------------------ pictures
def _dxt5(data, w, h):
    out = bytearray(4 * w * h); o = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            a0, a1 = data[o], data[o + 1]; ab = int.from_bytes(data[o + 2:o + 8], 'little')
            c0, c1, bits = struct.unpack_from('<HHI', data, o + 8); o += 16
            al = [a0, a1] + ([((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)] if a0 > a1 else [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255])
            p = ((c0 >> 11) * 255 // 31, ((c0 >> 5) & 63) * 255 // 63, (c0 & 31) * 255 // 31)
            q = ((c1 >> 11) * 255 // 31, ((c1 >> 5) & 63) * 255 // 63, (c1 & 31) * 255 // 31)
            cs = (p, q, tuple((2 * x + y) // 3 for x, y in zip(p, q)), tuple((x + 2 * y) // 3 for x, y in zip(p, q)))
            for k in range(16):
                y, x = by + k // 4, bx + k % 4
                if y < h and x < w:
                    i = 4 * (y * w + x); out[i:i + 3] = bytes(cs[(bits >> (2 * k)) & 3]); out[i + 3] = al[(ab >> (3 * k)) & 7]
    return out


def tex_pixels(entry):
    """A .TEX record -> (w, h, RGBA bytearray or None for a format not read here). First mip."""
    _size, f1, _f2, _id, th, tw, _mips, _fl = struct.unpack_from('<I4s4sIHHII', entry, 0)
    q = entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', entry, q)[0]; d = entry[q + 4:q + 4 + n]
    if f1 == b'5TXD' and n >= tw * th:
        return tw, th, _dxt5(d, tw, th)
    if f1 == b'ABGR' and n == 4 * tw * th:
        return tw, th, bytearray(d)
    return tw, th, None


def tex_abgr(entry, px):
    """The record as a one-mip 'ABGR' texture of the same id, size and name (as kl_hud.build_pictures writes them)."""
    _size, _f1, _f2, _id, th, tw, _mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', entry, 0)
    q = entry.index(b'\0', 36) + 1
    body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', _id, th, tw, 1, fl & ~0x100, sc, x20) + entry[36:q] + struct.pack('<I', len(px)) + bytes(px)
    return struct.pack('<I', len(body) + 4) + body


def _edge(rnd, n):
    """n insets for one long edge: held over runs of BAR_RUN pixels, a run one step from its neighbour at most."""
    out, cur = [], rnd.choice(BAR_EDGE)
    while len(out) < n:
        out += [cur] * rnd.randint(*BAR_RUN)
        nxt = rnd.choice(BAR_EDGE)
        cur += (nxt > cur) - (nxt < cur)
    return out[:n]


def _stroke_kit(bw, bh, cut_left, cut_right, rnd):
    """Coverage 0..255 of one bar of bw x bh: solid, wandering long edges, slanted hand-cut ends, dry streaks at them."""
    a = bytearray(bw * bh)
    top, bot = _edge(rnd, bw), _edge(rnd, bw)
    ends = []
    for cut in (cut_left, cut_right):
        if not cut or bw < 24:
            ends.append([0] * bh); continue
        lean = rnd.randint(*BAR_SLANT) * rnd.choice((-1, 1)); jit, row = 0, []
        for y in range(bh):
            if y % 4 == 0:
                jit = rnd.choice((0, 0, 1))                 # the cut is not ruled: a step every few rows
            t = y * lean // max(1, bh - 1)
            row.append((t if lean > 0 else t - lean) + jit)
        ends.append(row)
    for y in range(bh):
        lo, hi = ends[0][y], bw - ends[1][y]
        for x in range(lo, hi):
            if top[x] <= y < bh - bot[x]:
                a[y * bw + x] = 255
    for side, cut in ((0, cut_left), (1, cut_right)):       # the brush runs dry toward a cut end, never across the bar
        if not cut or bw < 3 * BAR_STREAK_LEN[1] or bh < 10:
            continue
        for y in rnd.sample(range(3, bh - 3), min(rnd.randint(*BAR_STREAKS), bh - 6)):
            n = rnd.randint(*BAR_STREAK_LEN)
            for k in range(n):
                x = k if side == 0 else bw - 1 - k
                if a[y * bw + x]:
                    a[y * bw + x] = int(255 * (BAR_STREAK_ALPHA + (1 - BAR_STREAK_ALPHA) * (k / float(n)) ** 2))
    return a


def _stroke_hud(bw, bh, cut_left, cut_right):
    """The same from tools\\kl_hud.py's stroke painter (HUD picture 111 'stroke'), by import: painted larger by its own
    margins, and by 8 pixels past an end that is not a cut, then cropped to the bar."""
    import kl_hud
    ml, mr = (0 if cut_left else 8), (0 if cut_right else 8)
    W, H = bw + 4 + ml + mr, bh + 6
    px = kl_hud._extra_pixels('stroke', W, H)
    a = bytearray(bw * bh)
    for y in range(bh):
        o = 4 * ((y + 3) * W + 2 + ml)
        a[y * bw:(y + 1) * bw] = px[o + 3:o + 3 + 4 * bw:4]
    return a


def paint_bar(px, w, h, tid, rough_left, rough_right, style='kit'):
    """A stock focus bar -> the same extent as a chalk brush stroke (alpha = the stock bar's mean). None = no bar."""
    import random
    xs = [x for x in range(w) if any(px[4 * (y * w + x) + 3] > BAR_ALPHA_MIN for y in range(h))]
    ys = [y for y in range(h) if any(px[4 * (y * w + x) + 3] > BAR_ALPHA_MIN for x in range(0, w, 3))]
    if not xs or not ys:
        return None
    x0, x1, y0, y1 = xs[0], xs[-1] + 1, ys[0], ys[-1] + 1
    dark = sum(1 for y in range(y0, y1) for x in range(x0, x1, 2) if px[4 * (y * w + x) + 3] > 128 and max(px[4 * (y * w + x):4 * (y * w + x) + 3]) < 80)
    if dark > BAR_DARK_SHARE * (y1 - y0) * ((x1 - x0 + 1) // 2):
        return False                                       # FocusBar_medium_02: a bar with a dark groove drawn into it
    al = [px[4 * (y * w + x) + 3] for y in range(y0, y1) for x in range(x0, x1, 5)]
    alpha = max(200, sum(al) // len(al))
    bw, bh = x1 - x0, y1 - y0
    cut_l, cut_r = bool(rough_left or x0 > 0), bool(rough_right or x1 < w)   # the bar ENDS in this tile on that side
    if style == 'hud' and bw >= 16 and bh >= 8:
        cov = _stroke_hud(bw, bh, cut_l, cut_r)
    else:
        cov = _stroke_kit(bw, bh, cut_l, cut_r, random.Random(tid * 7919 + w * 31 + h))
    out = bytearray(4 * w * h)
    for y in range(bh):
        for x in range(bw):
            c = cov[y * bw + x]
            if c:
                i = 4 * ((y0 + y) * w + x0 + x)
                out[i], out[i + 1], out[i + 2] = CHALK
                out[i + 3] = alpha * c // 255
    return out


def paint_line(px, w, h, tid):
    """A stock separator line (grey on opaque black) -> a dry-brush line of LINE_ROWS rows over the same span."""
    import random
    rows = [y for y in range(h) if any(max(px[4 * (y * w + x):4 * (y * w + x) + 3]) > 12 for x in range(0, w, 2))]
    if not rows:
        return None
    y0 = rows[0]
    xs = [x for x in range(w) if max(px[4 * (y0 * w + x):4 * (y0 * w + x) + 3]) > 12]
    x0, x1 = xs[0], xs[-1] + 1
    rnd = random.Random(tid * 104729 + w)
    out = bytearray(b'\0\0\0\xff' * (w * h))
    gaps = {}
    for _ in range(max(1, (x1 - x0) // LINE_GAP_EVERY)):
        g = rnd.randrange(x0, x1); gaps[g] = rnd.randrange(2, 7)
    for r in range(LINE_ROWS):
        y = y0 + r
        if y >= h:
            break
        x = x0
        while x < x1:
            if x in gaps:
                x += gaps[x]; continue
            lvl = LINE_LEVEL * (1.0 if r == 0 else .55) * (1.0 if rnd.random() > .06 else .4)
            if r and (x // 37 + r) % 4 == 0:
                lvl *= .3
            i = 4 * (y * w + x)
            out[i], out[i + 1], out[i + 2] = (int(c * lvl) for c in CHALK)
            x += 1
    return out


def picture_uses(z, stem):
    """{texture id: [(family, tile is the picture's left edge, right edge)]} over every ZWINPIC of a scene."""
    import kl_scene, kl_prp, kl_prmgraph as G
    sc = kl_scene.read(z, stem); prp = kl_prp.Prp(z.read(stem + '.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        raise SystemExit('%s: .prp nodes and .gms entities do not line up' % stem)
    prm = G.read(z.read(stem + '.prm'), 'dd')
    uses = collections.defaultdict(list)
    for i, e in enumerate(ents):
        if e.tid != ZWINPIC:
            continue
        own = e.name.decode('latin1')
        name = e.parent.name.decode('latin1') if own == 'Box' and e.parent is not None else own
        fam = re.sub(r'#\d+$', '', name)
        if not (BAR_RE.match(fam) or LINE_RE.match(fam)):
            continue
        ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)]
        if len(ints) < 3:
            continue
        W, _H, c = ints[-3:]
        if not 0 < c < len(prm.chunks):
            continue
        d = prm.chunks[c]; n = struct.unpack_from('<I', d, 0)[0]
        if len(d) < 8 + 56 * n or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
            continue
        for k, s in enumerate(struct.unpack_from('<%dI' % n, d, 8 + 40 * n)):
            if not 0 < s < len(prm.chunks) or len(prm.chunks[s]) != 32:
                continue
            cx, _cy, _a, _b, _u, _v, _c, tw, _th = struct.unpack_from('<9f', d, 4 + 40 * k)
            uses[prm.u32(s, 4)].append((fam, cx - tw / 2 <= 0.5, cx + tw / 2 >= W - 0.5))
    return uses


def repaint(z, stem, log=print, bars='kit'):
    """-> (new .TEX bytes, {texture id: (kind, w, h)}). Only pixels of existing textures change."""
    import kl_texmat as T
    tex = T.read_tex(z.read(stem + '.TEX'))
    done = {}
    for tid, us in sorted(picture_uses(z, stem).items()):
        if tid not in tex.tex:
            continue
        kinds = {'bar' if BAR_RE.match(f) else 'line' for f, _l, _r in us}
        if len(kinds) != 1:
            log('  texture %d is used by bars and lines: left alone' % tid); continue
        kind = kinds.pop()
        w, h, px = tex_pixels(tex.tex[tid].entry)
        if px is None:
            log('  texture %d (%s): a format not read here, left alone' % (tid, us[0][0])); continue
        new = paint_bar(px, w, h, tid, all(l for _f, l, _r in us), all(r for _f, _l, r in us), bars) if kind == 'bar' else paint_line(px, w, h, tid)
        if new is None:
            continue                                       # an empty half of a two-tile picture
        if new is False:
            log('  texture %d (%s): a bar with a drawing in it, left alone' % (tid, us[0][0])); continue
        tex.tex[tid] = T.Texture(tex_abgr(tex.tex[tid].entry, new))
        done[tid] = (kind, w, h, sorted({f for f, _l, _r in us}))
    return T.write_tex(tex), done


# ------------------------------------------------------------------ archives
def _member(z, name):
    return next((i for i in z.infolist() if i.filename.lower() == name.lower()), None)


def _rezip(src, dst, new, extra=None):
    """A copy of archive `src` with the members in `new` ({lower-case name: bytes}) replaced and `extra` appended."""
    if os.path.exists(dst) and os.path.exists(src) and os.path.samefile(src, dst):
        raise SystemExit('refusing to write over the input: %s' % dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    z = zipfile.ZipFile(src); seen = set()
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():
            key = i.filename.lower()
            n = zipfile.ZipInfo(i.filename, i.date_time)                 # the member's own stamp: the same bytes every build
            n.compress_type = i.compress_type; n.external_attr = i.external_attr
            o.writestr(n, new[key] if key in new else z.read(i)); seen.add(key)
        for name, data in (extra or {}).items():
            if name.lower() in seen:
                continue
            n = zipfile.ZipInfo(name, ZIP_STAMP); n.compress_type = zipfile.ZIP_DEFLATED
            o.writestr(n, data)
    back = zipfile.ZipFile(dst)
    for i in z.infolist():
        if back.read(i.filename) != (new.get(i.filename.lower()) if i.filename.lower() in new else z.read(i)):
            raise SystemExit('%s: member %s did not come back as written' % (dst, i.filename))


def _sha(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:8]


def apply(src, dst, look='deadmen', do_board=False, online_in_patch=False, pictures=True, log=print, bars='kit'):
    if do_board:
        raise SystemExit('--board is refused on an overlay: its online.xml is loaded at the MENU, and from Patch01.zip in every level '
                         'of the game; 48 more table entries there with the live count unknown (budget 5000) = the 14:24 crash class. '
                         'Use `level --board` on ONE of our level archives, after live check K0.')
    if bars not in BAR_STYLES:
        raise SystemExit('--bars %s: only %s' % (bars, ', '.join(BAR_STYLES)))
    if look not in LOOKS:
        raise SystemExit('--look %s: only %s' % (look, ', '.join(LOOKS)))
    ps, ss = os.path.join(src, PATCH_ZIP), os.path.join(src, SCENE_ZIP)
    for p in (ps, ss):
        if not os.path.exists(p):
            raise SystemExit('no %s (an overlay needs both files)' % p)
    zp, zs = zipfile.ZipFile(ps), zipfile.ZipFile(ss)
    new_p = {}
    for member in (FRONT, INGAME):
        i = _member(zp, member)
        if i is None:
            raise SystemExit('%s has no %s' % (ps, member))
        new_p[i.filename.lower()] = restyle_xml(zp.read(i).decode('latin-1'), member, do_board, log).encode('latin-1')
    i = _member(zs, ONLINE)
    if i is None:
        raise SystemExit('%s has no %s' % (ss, ONLINE))
    online = restyle_xml(zs.read(i).decode('latin-1'), ONLINE, do_board, log).encode('latin-1')
    new_s = {i.filename.lower(): online}
    if pictures:
        stem = next(n for n in zs.namelist() if n.lower().endswith('.gms'))[:-4]
        data, done = repaint(zs, stem, log, bars)
        new_s[(stem + '.TEX').lower()] = data
        log('  pictures: %d textures repainted (%d bars, %d lines)' % (len(done), sum(1 for v in done.values() if v[0] == 'bar'), sum(1 for v in done.values() if v[0] == 'line')))
    extra = {}
    j = _member(zp, ONLINE)
    if j is not None:
        new_p[j.filename.lower()] = online
    elif online_in_patch:
        extra[ONLINE] = online
    _rezip(ps, os.path.join(dst, PATCH_ZIP), new_p, extra)
    _rezip(ss, os.path.join(dst, SCENE_ZIP), new_s)
    for f in (PATCH_ZIP, SCENE_ZIP):
        log('  %s  %d bytes  sha1 %s' % (os.path.join(dst, f), os.path.getsize(os.path.join(dst, f)), _sha(os.path.join(dst, f))))


def level(src, out, do_board=False, log=print, bars='kit'):
    zp = src if src.lower().endswith('.zip') else next(os.path.join(src, f) for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip'))
    z = zipfile.ZipFile(zp)
    stem = next(n for n in z.namelist() if n.lower().endswith('_main.gms'))[:-4]
    new = {}
    i = _member(z, ONLINE)
    if i is not None:
        new[i.filename.lower()] = restyle_xml(z.read(i).decode('latin-1'), ONLINE, do_board, log).encode('latin-1')
    else:
        log('  %s has no %s: pictures only' % (zp, ONLINE))
    data, done = repaint(z, stem, log, bars)
    new[(stem + '.TEX').lower()] = data
    dst = os.path.join(out, os.path.basename(zp))
    _rezip(zp, dst, new)
    log('  %s: %d textures repainted, %d bytes, sha1 %s' % (dst, len(done), os.path.getsize(dst), _sha(dst)))


# ------------------------------------------------------------------ check / diff
def _xmls(folder):
    """{member: text} of an overlay: frontend / ingame from Patch01.zip, online from the scene (and Patch01 if there)."""
    zp, zs = zipfile.ZipFile(os.path.join(folder, PATCH_ZIP)), zipfile.ZipFile(os.path.join(folder, SCENE_ZIP))
    out = {}
    for member, z in ((FRONT, zp), (INGAME, zp), (ONLINE, zs)):
        i = _member(z, member)
        out[member] = z.read(i).decode('latin-1') if i is not None else None
    j = _member(zp, ONLINE)
    out['patch:' + ONLINE] = zp.read(j).decode('latin-1') if j is not None else None
    return out


def _scene_names(folder):
    """Names of the menu scene's entities (what Graphic= may name) - from the .buf's strings, no scene parse needed."""
    z = zipfile.ZipFile(os.path.join(folder, SCENE_ZIP))
    buf = z.read(next(n for n in z.namelist() if n.lower().endswith('.buf')))
    return {s.decode('latin-1') for s in re.findall(rb'[\x20-\x7e]{2,80}', buf)}


def _names(xml, tag):
    """Names of the tags of one kind. The FIRST Name= counts: a template may carry two ('one for template, one for
    instantiation', the stock file's own comment)."""
    return [n for n in (next((v for k, v in t.attrs if k == 'Name'), None) for t in tags(xml) if t.name == tag and not t.close) if n]


def check(folder, ref=None, log=print, count=None):
    fails, notes = [], []
    grown = 0                                               # table-making tags more than the reference, frontend.xml + online.xml
    for f in (PATCH_ZIP, SCENE_ZIP):
        if not os.path.exists(os.path.join(folder, f)):
            return ['%s is missing: an overlay is BOTH files' % f], notes
    X = _xmls(folder); R = _xmls(ref) if ref else None
    if X['patch:' + ONLINE] is not None and X['patch:' + ONLINE] != X[ONLINE]:
        fails.append("Patch01.zip's Menu/online.xml is not the menu scene's")
    ents = _scene_names(folder)
    fonts_seen = set()
    for member in (FRONT, INGAME, ONLINE):
        xml = X[member]
        if xml is None:
            fails.append('%s is missing' % member); continue
        rx = R[member] if R else None
        mate = X[ONLINE] if member != ONLINE else None             # online.xml is loaded behind frontend.xml / ingame.xml
        # 1. shape
        an = anomalies(xml)
        if rx is not None:
            if an != anomalies(rx):
                fails.append('%s: the tags do not nest as in the reference: %s' % (member, [a for a in an if a not in anomalies(rx)][:4]))
        elif an:
            notes.append('%s: %d oddities a strict XML reader would refuse (no reference to compare): %s' % (member, len(an), an[:3]))
        ts = [t for t in tags(xml) if not t.close]
        for t in ts:
            for k, v in t.attrs:
                if any(c in v for c in '<>&') or any(ord(c) < 32 and c not in '\t\r\n' for c in v):
                    fails.append('%s: %s %s="%s": a character the stock files never have in a value' % (member, t.name, k, v[:30]))
            if len({k for k, _v in t.attrs}) != len(t.attrs) and rx is None:
                pass                                                # stock has doubled attributes (Name, AnimDelay): no fault
        # 2. names a page refers to
        tdef = set(_names(xml, 'Template'))
        cdef = set(colorsets(xml)) | (set(colorsets(mate)) if mate else set()) | ({n for m2 in (FRONT, INGAME) if X[m2] for n in colorsets(X[m2])} if member == ONLINE else set())
        el = set(_names(xml, 'GuiElement'))
        rts = [t for t in tags(rx) if not t.close] if rx is not None else []
        used = lambda tl, key: {v2.strip() for t in tl for k, v in t.attrs if k == key for v2 in v.split(',') if v2.strip()}
        for what, key, defined in (('template', 'Template', tdef), ('colour set', 'ColorSet', cdef), ('colour set', 'RecCSFocus', cdef),
                                   ('colour set', 'RecCSDefault', cdef), ('colour set', 'ColorSetValue', cdef), ('colour set', 'ColorSetBackground', cdef)):
            miss = sorted(used(ts, key) - defined)
            if rx is not None:
                miss = [m2 for m2 in miss if m2 not in used(rts, key) or (key == 'Template' and m2 in set(_names(rx, 'Template')))]
            if miss:
                (fails if rx is not None else notes).append('%s: %s not defined: %s' % (member, what, miss[:8]))
        f_new = used(ts, 'Font') - (used(rts, 'Font') if rx is not None else used(ts, 'Font'))
        if f_new:
            fails.append('%s: fonts the reference does not use: %s' % (member, sorted(f_new)))
        fonts_seen |= used(ts, 'Font')
        gr = {v for t in ts if t.name in ('GuiElement', 'Template', 'Graphic') for k, v in t.attrs if k == 'Graphic'}
        low = {e.lower() for e in ents} | {e.lower() for e in el}       # stock writes FocusBar_Long#01 for FocusBar_long#01
        g_new = sorted(g for g in gr - ({v for t in rts for k, v in t.attrs if k == 'Graphic'} if rx is not None else set()) if g.lower() not in low)
        if g_new:
            (fails if rx is not None else notes).append('%s: Graphic= names nothing in the menu scene or the file: %s%s' %
                                                        (member, g_new[:8], '' if rx is not None else ' (in-level art and console art are not in the menu scene)'))
        if rx is not None:
            r_new = sorted((used(ts, 'Receiver') | used(ts, 'TextReceiver') | used(ts, 'FocusGraphic')) -
                           (used(rts, 'Receiver') | used(rts, 'TextReceiver') | used(rts, 'FocusGraphic')) - el)
            if r_new:
                fails.append('%s: new references to elements the file does not define: %s' % (member, r_new[:8]))
        # 3. the names kl2.exe looks up
        wn, en = _names(xml, 'Window'), _names(xml, 'GuiElement')
        if rx is not None:
            rw, re_ = _names(rx, 'Window'), _names(rx, 'GuiElement')
            gone = sorted((set(rw) - set(wn)) | {n for n in set(re_) - set(en)})
            if gone:
                fails.append('%s: names of the reference are gone: %s' % (member, gone[:8]))
            kind = lambda x: {(dict(t.attrs).get('Name'), t.name, dict(t.attrs).get('Type', '')) for t in tags(x) if not t.close and dict(t.attrs).get('Name') in set(KNOWN_WINDOWS) | set(KNOWN_ELEMENTS)}
            if kind(xml) - kind(rx) or kind(rx) - kind(xml):
                fails.append('%s: a name kl2.exe looks up changed its kind: %s' % (member, sorted(kind(xml) ^ kind(rx))[:6]))
        dup = sorted(n for n in set(wn) if wn.count(n) > 1)
        if dup and rx is None:
            notes.append('%s: a window name twice (stock has <Platform> alternatives): %s' % (member, dup))
        elif dup and dup != sorted(n for n in set(_names(rx, 'Window')) if _names(rx, 'Window').count(n) > 1):
            fails.append('%s: a window name twice: %s' % (member, dup))
        for t in ts:                                                # the fault class itself: a window that is not a plain page tag
            if t.name == 'Window' and dict(t.attrs).get('Type'):
                fails.append('%s: <Window Name="%s"> carries Type=: a window must be made by the window factory' % (member, dict(t.attrs).get('Name')))
        # 4. the table
        sig = signature(xml); n_tab = sum(1 for s in sig if s.split('|')[0] in TABLE_TAGS)
        if rx is not None:
            rs = signature(rx)
            if sig == rs:
                log('  %s: table layout identical to the reference (%d table-making tags)' % (member, n_tab))
            else:
                k = next((i for i, (a, b) in enumerate(zip(sig, rs)) if a != b), min(len(sig), len(rs)))
                extra = [s for s in sig if s.startswith('GuiElement|KLB_')]
                rest = [s for s in sig if not s.startswith('GuiElement|KLB_')]
                msg = '%s: TABLE SHIFT - %d table-making tags against %d; first difference at tag %d (%s)' % (
                    member, n_tab, sum(1 for s in rs if s.split('|')[0] in TABLE_TAGS), k, sig[k] if k < len(sig) else 'end')
                if member in (FRONT, ONLINE):
                    grown += n_tab - sum(1 for s in rs if s.split('|')[0] in TABLE_TAGS)
                if rest == rs:
                    notes.append(msg + '; only the %d --board elements were added: every index behind them moves' % len(extra))
                else:
                    fails.append(msg)
        else:
            notes.append('%s: %d table-making tags (no reference: the table cannot be compared)' % (member, n_tab))
    msg = _budget('the menu (frontend.xml + online.xml)', grown, count, '--menu-count')
    if msg:
        (fails if msg.startswith('OVER') or count is None else notes).append(msg)
    # 5. the scene archive
    if ref:
        za, zb = zipfile.ZipFile(os.path.join(folder, SCENE_ZIP)), zipfile.ZipFile(os.path.join(ref, SCENE_ZIP))
        if za.namelist() != zb.namelist():
            fails.append('scene archive: the member list differs from the reference')
        else:
            import kl_texmat as T
            for n in za.namelist():
                if n.lower() == ONLINE.lower() or za.read(n) == zb.read(n):
                    continue
                if not n.lower().endswith('.tex'):
                    fails.append('scene archive: %s differs from the reference' % n); continue
                ta, tb = T.read_tex(za.read(n)), T.read_tex(zb.read(n))
                if sorted(ta.tex) != sorted(tb.tex):
                    fails.append('scene archive: the texture ids differ from the reference'); continue
                ch = [t for t in ta.tex if ta.tex[t].entry != tb.tex[t].entry]
                for t in ch:
                    wa, ha, pa = tex_pixels(ta.tex[t].entry); wb, hb, _pb = tex_pixels(tb.tex[t].entry)
                    if (wa, ha) != (wb, hb) or pa is None:
                        fails.append('scene archive: texture %d changed size or is not readable' % t)
                log('  scene archive: %d textures differ from the reference, same ids and sizes; every other member identical' % len(ch))
        pa, pb = zipfile.ZipFile(os.path.join(folder, PATCH_ZIP)), zipfile.ZipFile(os.path.join(ref, PATCH_ZIP))
        more = [n for n in pa.namelist() if n not in pb.namelist()]
        if [n for n in pb.namelist() if n not in pa.namelist()]:
            fails.append('Patch01.zip lost members of the reference')
        if more:
            notes.append('Patch01.zip has members the reference does not: %s (that the game takes Menu/online.xml from it is ASSUMED)' % more)
    try:
        import kl_portraits
        z = zipfile.ZipFile(os.path.join(folder, SCENE_ZIP))
        if any(b'KLPic_Char01' in z.read(n) for n in z.namelist() if n.lower().endswith('.buf')):
            import kl_scene
            bad = kl_scene.read(z, next(n for n in z.namelist() if n.lower().endswith('.gms'))[:-4]).check()
            if bad:
                fails += ['scene: ' + b for b in bad[:6]]
    except Exception as e:                                          # a helper of another session changed: say so, do not hide it
        notes.append('scene self-check not run: %s' % e)
    return fails, notes


def _budget(what, grown, count, opt):
    """The rule of the TABLE note for one load set: live count <= TABLE_SAFE (entry 5000 must not exist) - an added
    tag makes an entry unless a <Platform> block drops it, so `grown` is an upper bound. None = nothing grew."""
    if grown <= 0:
        return None
    if count is None:
        return ('TABLE BUDGET NOT TESTED: %s gains up to %d entries and its live count is not given (%s N, from live check K0). '
                'Past %d entries the cursor over the menu background calls into entry %d: do not run this build before K0'
                % (what, grown, opt, TABLE_SAFE, TABLE_SAFE))
    if count + grown > TABLE_SAFE:
        return 'OVER THE TABLE BUDGET: %s has %d live entries + %d new = %d, over %d (entry %d would exist: the 14:24 crash class)' % (
            what, count, grown, count + grown, TABLE_SAFE, TABLE_SAFE)
    return 'table budget: %s %d live + %d new = %d of %d safe (cap %d)' % (what, count, grown, count + grown, TABLE_SAFE, TABLE_CAP)


def check_level(arc, src, log=print, count=None):
    """One level archive made by `level` against the archive it was made from."""
    import kl_texmat as T
    fails, notes = [], []
    za, zb = zipfile.ZipFile(arc), zipfile.ZipFile(src)
    if za.namelist() != zb.namelist():
        return ['the member list differs from the source archive'], notes
    changed = [n for n in za.namelist() if za.read(n) != zb.read(n)]
    for n in changed:
        low = n.lower()
        if low.endswith('_main.tex'):
            ta, tb = T.read_tex(za.read(n)), T.read_tex(zb.read(n))
            if sorted(ta.tex) != sorted(tb.tex):
                fails.append('%s: the texture ids differ from the source' % n); continue
            ch = [t for t in ta.tex if ta.tex[t].entry != tb.tex[t].entry]
            for t in ch:
                wa, ha, pa = tex_pixels(ta.tex[t].entry); wb, hb, _pb = tex_pixels(tb.tex[t].entry)
                if (wa, ha) != (wb, hb) or pa is None:
                    fails.append('%s: texture %d changed size or is not readable' % (n, t))
            log('  %s: %d textures differ from the source, same ids and sizes' % (n, len(ch)))
        elif low == ONLINE.lower():
            xml, rx = za.read(n).decode('latin-1'), zb.read(n).decode('latin-1')
            if anomalies(xml) != anomalies(rx):
                fails.append('%s: the tags do not nest as in the source: %s' % (n, [a for a in anomalies(xml) if a not in anomalies(rx)][:4]))
            ts = [t for t in tags(xml) if not t.close]; rts = [t for t in tags(rx) if not t.close]
            for t in ts:
                for k, v in t.attrs:
                    if any(c in v for c in '<>&') or any(ord(c) < 32 and c not in '\t\r\n' for c in v):
                        fails.append('%s: %s %s="%s": a character the stock files never have in a value' % (n, t.name, k, v[:30]))
                if t.name == 'Window' and dict(t.attrs).get('Type'):
                    fails.append('%s: <Window Name="%s"> carries Type=' % (n, dict(t.attrs).get('Name')))
            used = lambda tl, key: {v2.strip() for t in tl for k, v in t.attrs if k == key for v2 in v.split(',') if v2.strip()}
            for key in ('Template', 'ColorSet', 'Font', 'Graphic', 'RecCSFocus', 'RecCSDefault', 'TagName', 'Type'):
                own = set(colorsets(xml)) if key in ('ColorSet', 'RecCSFocus', 'RecCSDefault') else set(_names(xml, 'Template')) if key == 'Template' else set()
                new = sorted(used(ts, key) - used(rts, key) - own)   # a level's online.xml leans on ingame.xml: only NEW names can be judged
                if new:
                    fails.append('%s: %s= values the source never uses: %s' % (n, key, new[:8]))
            gone = sorted((set(_names(rx, 'Window')) - set(_names(xml, 'Window'))) | (set(_names(rx, 'GuiElement')) - set(_names(xml, 'GuiElement'))))
            if gone:
                fails.append('%s: names of the source are gone: %s' % (n, gone[:8]))
            wn = _names(xml, 'Window'); rw = _names(rx, 'Window')
            if sorted(x for x in set(wn) if wn.count(x) > 1) != sorted(x for x in set(rw) if rw.count(x) > 1):
                fails.append('%s: a window name twice' % n)
            sig, rs = signature(xml), signature(rx)
            n_tab = sum(1 for s in sig if s.split('|')[0] in TABLE_TAGS); r_tab = sum(1 for s in rs if s.split('|')[0] in TABLE_TAGS)
            if sig == rs:
                log('  %s: table layout identical to the source (%d table-making tags)' % (n, n_tab))
            elif [s for s in sig if not s.startswith('GuiElement|KLB_')] != rs:
                fails.append('%s: TABLE SHIFT that is not the --board elements alone (%d tags against %d)' % (n, n_tab, r_tab))
            else:
                notes.append('%s: TABLE SHIFT - the %d --board elements; every index behind HeistStatus moves in THIS level' % (n, n_tab - r_tab))
                msg = _budget('this level (ingame.xml + online.xml)', n_tab - r_tab, count, '--level-count')
                (fails if msg.startswith('OVER') or count is None else notes).append(msg)
        else:
            fails.append('%s differs from the source: `level` changes the .TEX and Menu/online.xml only' % n)
    if not changed:
        notes.append('identical to the source')
    return fails, notes


def diff(a, b, log=print):
    A, B = _xmls(a), _xmls(b)
    for member in (FRONT, INGAME, ONLINE, 'patch:' + ONLINE):
        xa, xb = A[member], B[member]
        if xa is None or xb is None:
            if xa is not xb:
                log('%s: only in %s' % (member, a if xb is None else b))
            continue
        if xa == xb:
            log('%s: identical' % member); continue
        ca, cb = dict(colorset_list(xa)), colorset_list(xb)
        for key, val in cb:                                 # by (name, occurrence): both definitions of a doubled name
            if ca.get(key) != val:
                log('%s: colour set %-22s %s -> %s' % (member, key[0] + ('' if key[1] == 1 else ' (definition %d)' % key[1]), ca.get(key, '-'), val))
        ta, tb = [t for t in tags(xa) if not t.close], [t for t in tags(xb) if not t.close]
        per = collections.OrderedDict()
        if len(ta) == len(tb):
            for p, q in zip(ta, tb):
                if p.name == 'ColorSet' or p.attrs == q.attrs:
                    continue
                da, db = dict(p.attrs), dict(q.attrs)
                for k in sorted(set(da) | set(db)):
                    if da.get(k) != db.get(k):
                        per.setdefault(q.window or '(templates)', collections.Counter())['%s %s -> %s' % (k, da.get(k, '-'), db.get(k, '-'))] += 1
        else:
            na, nb = collections.Counter(t.window for t in ta), collections.Counter(t.window for t in tb)
            for w in nb:
                if na.get(w, 0) != nb[w]:
                    per.setdefault(w or '(templates)', collections.Counter())['tags %d -> %d' % (na.get(w, 0), nb[w])] += 1
            added = [dict(t.attrs).get('Name') for t in tb if dict(t.attrs).get('Name', '').startswith('KLB_')]
            if added:
                log('%s: %d elements added: %s .. %s' % (member, len(added), added[0], added[-1]))
        for w, c in per.items():
            log('%s: %-32s %s' % (member, w, '; '.join('%d x %s' % (v, k) for k, v in c.most_common())))
    import kl_texmat as T
    za, zb = zipfile.ZipFile(os.path.join(a, SCENE_ZIP)), zipfile.ZipFile(os.path.join(b, SCENE_ZIP))
    for n in zb.namelist():
        if n.lower().endswith('.tex') and n in za.namelist() and za.read(n) != zb.read(n):
            ta, tb = T.read_tex(za.read(n)), T.read_tex(zb.read(n))
            ch = sorted(t for t in tb.tex if t not in ta.tex or ta.tex[t].entry != tb.tex[t].entry)
            log('%s: %d textures differ: %s' % (n, len(ch), ' '.join(map(str, ch))))
        elif n in za.namelist() and za.read(n) != zb.read(n) and n.lower() != ONLINE.lower():
            log('%s: differs' % n)


def sheet(folder, out, log=print):
    """Every repainted bar / line texture of the overlay's menu scene, stacked on the menu's dark grey."""
    import kl_texmat as T
    from kl_portraits import png_write
    z = zipfile.ZipFile(os.path.join(folder, SCENE_ZIP))
    stem = next(n for n in z.namelist() if n.lower().endswith('.gms'))[:-4]
    tex = T.read_tex(z.read(stem + '.TEX'))
    rows = []
    for tid, us in sorted(picture_uses(z, stem).items()):
        w, h, px = tex_pixels(tex.tex[tid].entry)
        if px is not None:
            rows.append((tid, w, h, px, 'line' if LINE_RE.match(us[0][0]) else 'bar'))
    W = max(r[1] for r in rows); H = sum(r[2] + 4 for r in rows)
    bg = (40, 44, 52); img = bytearray(bytes(bg + (255,)) * (W * H)); y0 = 0
    for tid, w, h, px, kind in rows:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[4 * (y * w + x):4 * (y * w + x) + 4]
                o = 4 * ((y0 + y) * W + x)
                if kind == 'line':                                  # additive
                    img[o:o + 3] = bytes((min(255, bg[0] + r), min(255, bg[1] + g), min(255, bg[2] + b)))
                else:
                    img[o:o + 3] = bytes(((r * a + bg[0] * (255 - a)) // 255, (g * a + bg[1] * (255 - a)) // 255, (b * a + bg[2] * (255 - a)) // 255))
        y0 += h + 4
    png_write(out, W, H, img)
    log('%s: %d textures (%s)' % (out, len(rows), ' '.join(str(r[0]) for r in rows)))


def abi(exe, folder, log=print):
    import kl_exe
    E = kl_exe.Exe(exe); d = E.d
    X = _xmls(folder)
    for tag in ('Window', 'GuiElement'):
        known = []
        for n in sorted({n for m in (FRONT, INGAME, ONLINE) if X[m] for n in _names(X[m], tag)}):
            b = n.encode('latin-1') + b'\0'; i = d.find(b'\0' + b); hit = False
            while i >= 0 and not hit:
                try:
                    hit = d.find(struct.pack('<I', E.va_of(i + 1))) >= 0
                except Exception:
                    pass
                i = d.find(b'\0' + b, i + 1)
            if hit:
                known.append(n)
        log('%s names kl2.exe refers to (%d): %s' % (tag, len(known), ' '.join(known)))


def main():
    argv = sys.argv[1:]; val = {}
    for name in ('--look', '--bars', '--menu-count', '--level-count'):      # options with a value
        if name in argv:
            i = argv.index(name)
            if i + 1 >= len(argv):
                raise SystemExit('%s needs a value' % name)
            val[name] = argv[i + 1]; del argv[i:i + 2]
    a = [x for x in argv if not x.startswith('--')]
    opt = [x for x in argv if x.startswith('--')]
    look, bars = val.get('--look', 'deadmen'), val.get('--bars', 'kit')
    num = lambda k: int(val[k], 0) if k in val else None
    if len(a) == 3 and a[0] == 'apply':
        apply(a[1], a[2], look, '--board' in opt, '--online-in-patch' in opt, '--no-pictures' not in opt, bars=bars)
    elif len(a) == 3 and a[0] == 'level':
        level(a[1], a[2], '--board' in opt, bars=bars)
    elif (len(a) in (2, 3) and a[0] == 'check') or (len(a) == 3 and a[0] == 'check-level'):
        if a[0] == 'check':
            fails, notes = check(a[1], a[2] if len(a) == 3 else None, count=num('--menu-count'))
        else:
            fails, notes = check_level(a[1], a[2], count=num('--level-count'))
        for n in notes:
            print('  NOTE ' + n)
        for f in fails:
            print('  FAIL ' + f)
        print('RESULT: %s (%d fails, %d notes)' % ('FAIL' if fails else 'PASS', len(fails), len(notes)))
        sys.exit(1 if fails else 0)
    elif len(a) == 3 and a[0] == 'diff':
        diff(a[1], a[2])
    elif len(a) == 3 and a[0] == 'sheet':
        sheet(a[1], a[2])
    elif len(a) == 3 and a[0] == 'abi':
        abi(a[1], a[2])
    else:
        print(__doc__); sys.exit(1)


if __name__ == '__main__':
    main()
