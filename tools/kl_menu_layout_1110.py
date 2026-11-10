#!/usr/bin/env python3
r"""kl_menu_layout_1110.py - MENU REDESIGN stage F: the PAGE LAYOUT of the front-end menus in the Dead Men arrangement (2026-11-10,
cloud, OFFLINE: written without a game file, nothing here has run in the game). Plan + what is already installed: re\menu_redesign_1110.md
("## Stage F layout tool" at its end), design: re\menu_look_1109.md, inventory of the live XML: re\menu_look_inventory_1110.md +
re\menu_inventory_1110\*.md (every number in LAYOUT below was derived from those tables).

    python tools\kl_menu_layout_1110.py plan  [--set <dir>] [--dm <DM Scenes\KaneAndLynch.zip>] [--dm-inventory <md>]
        read-only: per window the elements it will move, old -> new virtual boxes (1280 x 720), the re-pointed pictures, the GUESS list;
        REFUSES (exit 1) a moved element outside its window / the screen, two text elements that would overlap (measured with the scene's
        font advance tables when readable, else an estimate), a selector that finds nothing or several, a Graphic= that names no picture.
    python tools\kl_menu_layout_1110.py stage [--set <dir>] [--out <dir>] [--accept-input] [--dm <zip>] [--dm-inventory <md>] [--no-sheet]
        the plan written: themed copies of Patch01_deadmen.zip, Patch01_rows12_deadmen.zip (when present) and Scenes\kaneandlynch_deadmen.zip
        under <out> (default C:\kl_build_1024\menulook_1109\layout\) with the XML geometry rewritten and, with --dm, the Dead Men art
        (Background_Kane / _Lynch / _KaneOptions / _LynchOptions / _FABag / _HeaderSplat) FILLED INTO the scene's own EMPTY stub pictures
        (see ART below; no entity is added), plus pins.json (--accept-input on the first run), install.py / INSTALL / UNDO .bat (the
        menulook_1109 pattern: pinned live md5s, <name>.before-menulayout_1110 backups, byte-exact undo), build_report.json, plan.txt and
        contact_layout.png (every laid-out window: the boxes BEFORE and AFTER drawn over 1280 x 720, so the owner sees the layout without
        the game; needs Pillow).
    python tools\kl_menu_layout_1110.py check <stage dir> [--set <dir>]
        proofs on a finished stage against the live set: per XML the element count / order / names / Types / Templates are the input's
        (kl_hud_menu.signature + an element-by-element compare), ONLY X Y W H AlignH AlignV Graphic differ and only on planned elements,
        every planned box is inside 0..1280 x 0..720, no zip member other than the XML files (+ the scene's .prp / .prm / .TEX with --dm)
        changed, every stock .TEX record kept (id, name, bytes), the entity list identical (entity delta 0 = no picture was ADDED; the
        stubs were filled), pins present.

WHAT MOVES (data at the top of the file: LAYOUT per window, ROWS rules, ART): MainMenu (Dead Men's arrangement: logo top-left, the
menu column left-centre with its brush bars, Kane / Lynch portraits on the right drawn through the two re-pointed icon elements), the
Arcade pages HeistPlayMenu / 2 / 3 (picture left, its title in the display face right under it, briefing right, HeaderSplat behind the
headline), KLHeister + KLGuns (two-column rows: label left, value centred in the right column, pitch 36, splat behind the headline),
FALobby (picture left, Dead Men's FABag backdrop through the lobby plate's element, the table as it is), OptionsMenu (listed, NOT
moved: its rows are flow-positioned by the game, see the note). Shop pages, pause, round-over live in each LEVEL archive: not here
(stage G, per level). NO element, template or ColorSet is added or removed: the menu manager's table (re\menu_look_inventory_1110.md 2:
no live count exists, static estimate 4793 of 5096) is untouched - the proofs enforce it.

COORDINATE MODEL (GUESS beyond the one proven point): the menu is laid out on a 1280 x 720 virtual screen; a Template ScreenBaseSize
group (768 x 576, Center / Center) therefore starts at (256, 72) [PROVEN: re\shop_hire.md 332, a card at X=432 Y=60 measured at
(688, 132)]. Nested groups ADD their X / Y to the parent's origin after the same alignment rule (GUESS: the main menu's column and the
Heist pages' data column come out where the screenshots show them); AlignH Right = the element's right edge sits at (group right - X);
Center = centre at (group centre + X); same vertically. A text element's width is its string measured with the themed font's advance
table when the scene is readable, else 0.55 x px per character; .LOC keys are measured on the key's last segment (stand-in). Picture
sizes come from the scene (ZWINPIC W x H) when readable, else PIC_SIZES.

HOW THE DEAD MEN ART GETS IN (with --dm; the kl_portraits.py record shapes, PROVEN in the game for KLPic_*): the DD scene already
holds the six Dead Men picture ENTITIES as EMPTY stubs (ZWINPIC with W = H = chunk = 0, PROVEN by the local partner on the .prp
nodes). `stage --dm` composes each Dead Men picture (kl_menu_redesign_1110.Scene.compose), cuts it into power-of-two ABGR tiles
(<= 512 x 512, the stock Background's own layout), appends the tile records to the .TEX (ids after the last stock id), writes one
sprite chunk per tile + one picture chunk per picture to the .prm (kl_prmgraph.new_chunk) and sets the stub's three ints (W, H,
chunk) in the .prp node. Entity count, slot ids, .gms / .buf / .oct / .rmi / .rmc: unchanged (nothing is added, so nothing is
renumbered). GUESS: a stub whose W / H / chunk become valid draws like every other picture (the loader has no special case for the
seven stubs that kl_portraits.check could see). Without --dm the art step is SKIPPED with a log line and the art-dependent
re-points (icons -> portraits, lobby plate -> FABag, headline icon -> splat) are NOT written (an empty stub draws nothing).

GUESSES, every one needs the owner's screenshots (plan prints the list): every number in LAYOUT / ROWS (positions, pitch 36,
portrait x, splat offset); the coordinate model above; that an element's own X / Y wins over its Template's; that a re-pointed
Graphic= is resolved by picture NAME at window open (re\menus.md 2.7: the resolver was not traced); that the 'Kane' / 'Lynch'
template priorities (4) are not needed on the main menu (the icons draw before the text in file order); the stub-fill; that the
8 x 8 blank KLPic_None1 hides an icon; that the ticker / bottom legend keep their place (left alone); text widths.
"""
import hashlib, json, os, re, shutil, struct, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hud_menu as HM
import kl_menu_look_1109 as ML

GAME = ML.GAME
OVERLAY = ML.OVERLAY
OUT = os.path.join(ML.OUT, 'layout')
TAG = '.before-menulayout_1110'
DM_SCENE_DEFAULT = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\Scenes\KaneAndLynch.zip'
PATCH, ROWS12, SCENE = 'Patch01_deadmen.zip', 'Patch01_rows12_deadmen.zip', os.path.join('Scenes', 'kaneandlynch_deadmen.zip')
INPUTS = (PATCH, ROWS12, SCENE)                 # rows12 optional (absent = not staged, logged)
SCENE_STEM = 'Scenes/kaneandlynch'
XML_PATCH = (HM.FRONT,)                         # the XML member of a Patch01*.zip that changes (ingame.xml: nothing laid out there)
GEOM_ATTRS = ('X', 'Y', 'W', 'H', 'AlignH', 'AlignV', 'Graphic')      # the ONLY attributes stage may change
SCREEN = (1280, 720)
SBS = (768, 576)                                # Template ScreenBaseSize
ZWINGROUP, ZWINPIC = 0x10002e, 0x200046
MAX_TILE = 512
EST_ADV = 0.55                                  # GUESS: average advance / px when no font table is readable
LINE_K = 1.2                                    # GUESS: a text line's height / px
LEGEND_Y = 610                                  # the BottomFramePosSize band (768 x 38 at the SBS bottom: y 610..648): a row ending below it is noted
DM_INVENTORY_DEFAULT = os.path.join(HERE, '..', 're', 'menu_inventory_1110', 'dm_frontend.md')

# ------------------------------------------------------------------ picture sizes (re\menu_inventory_1110\pictures.md) used when the scene is not readable
PIC_SIZES = {
    'Background_Kane': (474, 720), 'Background_Lynch': (410, 720), 'Background_KaneOptions': (474, 720), 'Background_LynchOptions': (410, 720),
    'Background_FABag': (1280, 720), 'Background_HeaderSplat': (365, 267), 'GameLogo': (512, 230), 'GameLogoDemo': (512, 230),
    'GameLogo_big': (512, 348), 'KLPic_None1': (8, 8), 'KLPic_None2': (8, 8), 'KLPic_None3': (8, 8), 'Background': (1280, 720),
    'LobbyBackground': (1024, 462), 'ChapterBackground': (1024, 462), 'DoubleBackground': (1024, 462), 'BlackBandBackground': (1024, 462),
    'BlackBandErrorBackground': (1024, 462), 'BlackBandErrorBackground2': (1024, 462), 'BlackBackground': (32, 32),
}
PIC_PREFIX = (('FocusBar_', (1024, 32)), ('MenuFocus_', (1000, 26)), ('Line_', (1024, 32)), ('LevelPicture_H', (540, 304)), ('LevelPicture_L', (540, 304)),
              ('LevelPicture_DM', (540, 304)), ('LevelPicture_F', (325, 183)), ('LobbyMap_', (325, 183)), ('KLPic_Char', (256, 304)),
              ('KLPic_Mask', (256, 256)), ('Icon_', (32, 32)), ('Infocast', (32, 32)), ('FAStatus_', (18, 18)))
STRIP_FAMILIES = ('FocusBar_', 'MenuFocus_', 'Line_', 'AssignKeyFocus_')     # 1024-wide strips: only their left / top must be on screen
TEXT_TYPES = ('TextBlock', 'ToggleText', 'OpenWindow', 'CloseWindow', 'SendMessage', 'ZOnlyOneController', 'MercsLevelSelectorHeist', 'MercsShowInfo',
              'MercsShowInfoFA', 'MercsShowInfoFAInfocast', 'MercsShowInfoFALobby', 'MercsShowInfoFALobbyFocus', 'MercsHeader', 'SaveOptions',
              'CloseSessionButton', 'GamerCardButton')
ARROW_TEMPLATES = ('OptionsArrowL_T', 'OptionsArrowR_T')          # the < > toggles: a glyph, not a measured string
FONT_PX = {k: v[2] for k, v in ML.MENU_FONTS.items()}
FONT_CAPS = {k: v[4] for k, v in ML.MENU_FONTS.items()}

# ================================================================== THE LAYOUT (DATA; every number a GUESS until a screenshot says otherwise)
# Selectors: 'Name' = every element of the window carrying that own Name (platform copies share one; '?Name' = may be absent); 'pic:<Graphic>' = the element whose own
# Graphic= is that picture (must be unique in the window); '#<i>' = the element index of re\menu_inventory_1110 tables (last resort).
# Values: the XML attributes written (X Y W H AlignH AlignV Graphic). 'art': True = only written when the scene holds that picture with
# pixels (--dm filled it; an empty stub draws nothing, so the stock icon stays otherwise). 'note': shown by plan.
# Windows whose name starts with 'Template:' are template BODIES (instanced where used); plan says which windows use them.
_MM = (402, 240)        # MainMenu group 8 origin by the model: SBS (256,72) + group 5 (16,24) + group 8 (130,144)
_MMX = 150 - _MM[0]     # the column's text x = 150 virtual
_MMY = 300 - _MM[1]     # first row y = 300 virtual
_MMP = 44               # row pitch (stock 34; Dead Men's column is roomier)
_MM_ROWS = ('Button_Play', 'Button_Heist', 'Button_Online', 'Button_Achievements', 'Button_Options', 'Button_Quit')
LAYOUT = {
    'MainMenu': dict(
        note='Dead Men arrangement: logo top-left (template below), menu column at x 150 / y 300.. pitch 44 with the bars 10 px left and 9 px '
             'up (the stock offsets), Kane at x 560 and Lynch at x 870 full height through the two re-pointed icon elements, the other four '
             'icons hidden by the 8 x 8 blank. Ticker, plate and the bottom legend: left where they are.',
        elements=dict(
            **{n: dict(X=_MMX, Y=_MMY + k * _MMP) for k, n in enumerate(_MM_ROWS)},
            **{'MMfb#%02d' % (k + 1): dict(X=_MMX - 10, Y=_MMY + k * _MMP - 9) for k in range(6)},
            **{'pic:Icon_Campaign': dict(Graphic='Background_Kane', X=560 - _MM[0], Y=-_MM[1], art=True),
               'pic:Icon_Heist': dict(Graphic='Background_Lynch', X=870 - _MM[0], Y=-_MM[1], art=True),
               'pic:Icon_Multiplayer': dict(Graphic='KLPic_None1', X=-_MM[0], Y=-_MM[1]),
               'pic:Icon_Achievements': dict(Graphic='KLPic_None1', X=-_MM[0], Y=-_MM[1]),
               'pic:Icon_Options': dict(Graphic='KLPic_None1', X=-_MM[0], Y=-_MM[1]),
               'pic:Icon_Quit': dict(Graphic='KLPic_None1', X=-_MM[0], Y=-_MM[1])})),
    'Template:GameLogoTemplatePCMain': dict(
        note='the PC main-menu logo (512 x 230 tile, Dead Men logo left-aligned in it since stage C) to the top-left corner (64, 40); '
             'used by MainMenu only (plan lists the users).', used_by=('MainMenu',), origin=(272, 96),
        elements={'pic:GameLogo': dict(X=64 - 272, Y=40 - 96), 'pic:GameLogoDemo': dict(X=64 - 272, Y=40 - 96)}),
    'HeistPlayMenu': dict(
        note='Arcade page: picture at (120,130), its title (the level selector) right under it, briefing at (700,130), splat behind the headline.',
        elements={'pic:Icon_Heist': dict(Graphic='Background_HeaderSplat', X=-150, Y=-40, art=True),
                  **{'?H%02d_LevelPicture' % k: dict(X=-136, Y=58) for k in range(1, 10)},
                  'HPMfb#01': dict(X=-146, Y=367), 'HeistLevel': dict(X=-124, Y=376), 'HeistBriefingTextBlock': dict(X=444, Y=58)}),
    'HeistPlayMenu2': dict(
        note='Dead Men maps page: as HeistPlayMenu.',
        elements={'pic:Icon_Heist': dict(Graphic='Background_HeaderSplat', X=-150, Y=-40, art=True),
                  **{'?H%02d_LevelPicture_P2' % k: dict(X=-136, Y=58) for k in range(1, 8)},
                  'HPMfb#01_P2': dict(X=-146, Y=367), 'HeistLevel_P2': dict(X=-124, Y=376)}),
    'HeistPlayMenu3': dict(
        note='Dead Men campaign page: as HeistPlayMenu.',
        elements={'pic:Icon_Heist': dict(Graphic='Background_HeaderSplat', X=-150, Y=-40, art=True),
                  **{'?H%02d_LevelPicture_P3' % k: dict(X=-136, Y=58) for k in range(1, 6)},
                  'HPMfb#01_P3': dict(X=-146, Y=367), 'HeistLevel_P3': dict(X=-124, Y=376)}),
    'KLHeister': dict(
        note='Heister page: label column at x 120, rows pitch 36 (label / bar / value / arrows kept in step), splat behind the headline.',
        elements={'pic:Icon_Heist': dict(Graphic='Background_HeaderSplat', X=-150, Y=-40, art=True)},
        rows=dict(label_template='TextIndentX', data_group='KLH_CenterBox', arrows_group='KLH_CenterBoxArrows', bars='KLHfb#%02d',
                  x=-136, y0=356, pitch=36, dy_bar=-9, dx_bar=-22, dy_data=80, dy_arrow=72)),
    'KLGuns': dict(
        note='Mod settings page: the same two-column rule at the stock pitch (the rows are found by their template, so the rows12 (9) / Patch01 (11) row counts both fit).',
        elements={'pic:Icon_Heist': dict(Graphic='Background_HeaderSplat', X=-150, Y=-40, art=True)},
        rows=dict(label_template='TextIndentX', data_group='KLG_CenterBox', arrows_group='KLG_CenterBoxArrows', bars=None,
                  x=-136, y0=221, pitch=34, dy_bar=-9, dx_bar=-22, dy_data=80, dy_arrow=72)),      # pitch 34 = stock: Patch01's 11 rows must end above the legend band (y 610)
    'FALobby': dict(
        note='FA lobby: picture at (120,130); the settings rows / player table keep their place (the rows12 lobby packs 12 name rows under '
             'them: no room to move). The lobby plate becomes Dead Men\'s FABag backdrop (template below).',
        elements={'?LobbyPictureF%02d' % k: dict(X=-136, Y=58) for k in range(1, 10)}),
    'Template:LobbyBackgroundTemplate': dict(
        note='the lobby plate element -> Background_FABag (1280 x 720) at the screen origin; used by FALobby only.', used_by=('FALobby',), origin=(256, 72),
        elements={'pic:LobbyBackground': dict(Graphic='Background_FABag', X=-256, Y=-72, art=True)}),
    'OptionsMenu': dict(
        note='NOT moved: the left column buttons carry a Y on the first row only (the rest are flow-positioned by the game, MercsPushIndex) '
             'and the right column is the sub-pages\' template body. Two columns already; the chalk rules are textures (stage B).',
        elements={}),
}
# the Dead Men art: (DD stub picture name, DM picture name); filled by stage --dm (see the docstring)
ART = [('Background_Kane', 'Background_Kane'), ('Background_Lynch', 'Background_Lynch'), ('Background_KaneOptions', 'Background_KaneOptions'),
       ('Background_LynchOptions', 'Background_LynchOptions'), ('Background_FABag', 'Background_FABag'), ('Background_HeaderSplat', 'Background_HeaderSplat')]
# DM inventory hooks (--dm-inventory re\menu_inventory_1110\dm_frontend.md, when the local partner has written it): DD element -> (DM window, DM element).
# GUESS: the Dead Men frontend uses the same 1280 x 720 virtual screen; its X / Y replace the LAYOUT value for that element (plan says which).
DM_MAP = {('MainMenu', 'Button_Play'): ('PlayMenu', 'Button_Play'), ('MainMenu', 'Button_Options'): ('PlayMenu', 'Button_Options')}
GUESSES = [
    'every X / Y / pitch in LAYOUT and ROWS (derived from the inventory tables, never seen in the game)',
    'coordinate model: nested groups add their X / Y; Right = right edge at group right - X; Center = centre + X',
    'an own X / Y on the element wins over its Template\'s (the inventory tool assumes the same)',
    'Graphic= is resolved by picture name when the window opens (re/menus.md 2.7: not traced), so a re-point needs no new entity',
    'a filled stub (W / H / chunk set) draws like every other ZWINPIC; the seven stubs have no special case in the loader',
    'the 8 x 8 blank KLPic_None1 hides an icon; the stock Kane / Lynch templates\' priority 4 is not needed (file order)',
    'text widths: themed advance tables (when readable) or 0.55 x px per character; .LOC keys measured on the key tail',
    'the FABag replaces the lobby plate wholesale (the plate\'s grunge alpha is lost under it)',
    'the MercsGraphic Line_* separators (X=0 Y=0 in the XML) are placed by code: GUESS they follow the entries; stray lines at the old '
    'main-menu column in a screenshot = they do not, and the fix is to re-point them at KLPic_None1 (a LAYOUT line, no element)',
    'the Priority of the re-pointed icons stays unset (not a layout attribute): the portraits may draw under the Priority-1 band plate',
]


# ================================================================== XML walk (kl_menu_inventory_1110.parse with the tag offsets kept)
class Elem:
    __slots__ = ('idx', 'depth', 'parent', 'own', 'eff', 'cond', 'texts', 'tag', 'window')

    def __init__(self, idx, depth, parent, own, eff, cond, tag, window):
        self.idx, self.depth, self.parent, self.own, self.eff, self.cond, self.tag, self.window = idx, depth, parent, own, eff, cond, tag, window
        self.texts = []

    @property
    def name(self):
        return self.own.get('Name', '')

    @property
    def type(self):
        return self.eff.get('Type', '')

    def __repr__(self):
        return '%s#%d(%s)' % (self.window, self.idx, self.name or self.own.get('Graphic', self.type))


def parse_windows(xml):
    """-> ({window name: [Elem]}, templates, windows in file order). Template bodies are 'Template:<Name>' pseudo-windows."""
    ts = HM.tags(xml)
    templates = {}
    for t in ts:
        if t.name == 'Template' and not t.close and not t.window:
            a = dict(t.attrs)
            templates[a.get('Name')] = a
            for k, v in t.attrs:
                if k == 'Name' and v != a.get('Name'):
                    templates.setdefault(v, a)

    def effective(own):
        chain, seen, cur = [], set(), own.get('Template')
        while cur and cur in templates and cur not in seen:
            seen.add(cur); chain.append(templates[cur]); cur = templates[cur].get('Template')
        eff = {}
        for tpl in reversed(chain):
            for k, v in tpl.items():
                if k not in ('Name', 'Template'):
                    eff[k] = v
        eff.update(own)
        return eff

    CONT = ('Platform', 'ExcludeIn', 'Locale', 'GameRegion', 'BuildTag', 'MainIniOption')
    wins, order, win, stack, cond, outer = {}, [], None, [], [], []
    for t in ts:
        a = dict(t.attrs)
        if t.name == 'Window':
            if t.close:
                win = None; stack = []; cond = []
            else:
                win = a.get('Name', '?'); wins.setdefault(win, []); order.append(win); stack, cond = [], list(outer)
            continue
        if win is None:
            if t.name in CONT:
                if t.close:
                    if outer:
                        outer.pop()
                elif not t.selfclose:
                    outer.append('%s[%s]' % (t.name, ','.join('%s=%s' % kv for kv in t.attrs)))
            elif t.name == 'Template' and not t.close and not t.selfclose and not t.window:
                win = 'Template:' + a.get('Name', '?'); wins.setdefault(win, []); order.append(win); stack, cond = [], list(outer)
            continue
        if t.name == 'Template' and t.close and win.startswith('Template:'):
            win = None; continue
        if t.name == 'GuiElement':
            if t.close:
                if stack and stack[-1][0] == 'G':
                    stack.pop()
                continue
            depth = sum(1 for s in stack if s[0] == 'G')
            parent = next((s[1] for s in reversed(stack) if s[0] == 'G'), None)
            el = Elem(len(wins[win]), depth, parent, a, effective(a), ' '.join(cond), t, win)
            wins[win].append(el)
            if not t.selfclose:
                stack.append(('G', el))
            continue
        if t.name in CONT:
            if t.close:
                if stack and stack[-1][0] == 'C':
                    stack.pop(); cond.pop()
            elif not t.selfclose:
                stack.append(('C', 0)); cond.append('%s[%s]' % (t.name, ','.join('%s=%s' % kv for kv in t.attrs)))
            continue
        if t.name == 'Text' and not t.close:
            el = next((s[1] for s in reversed(stack) if s[0] == 'G'), None)
            if el is not None:
                el.texts.append(a.get('Text', ''))
    return wins, templates, order


def template_users(wins, tname):
    """Windows (not template bodies) whose elements instance template body `tname` (Template= on an element with no Type)."""
    return sorted({w for w, els in wins.items() if any(e.own.get('Template') == tname and not e.own.get('Type') for e in els)})


# ================================================================== the coordinate model
def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class Model:
    """Virtual boxes of elements. pic_size(name) -> (w, h) or None; measure(text, font) -> px."""

    def __init__(self, pic_sizes=None, adv_tables=None):
        self.pics = dict(PIC_SIZES); self.pics.update(pic_sizes or {})
        self.adv = adv_tables or {}
        self.estimated = not adv_tables

    def pic_size(self, name):
        if name in self.pics:
            return self.pics[name]
        fam = re.sub(r'#\d+$', '', name)
        if fam in self.pics:
            return self.pics[fam]
        for pre, wh in PIC_PREFIX:
            if fam.startswith(pre):
                return wh
        return None

    def measure(self, text, font):
        px = FONT_PX.get(font, FONT_PX['Text'])
        if font in self.adv:
            return ML.text_width(self.adv[font], text, FONT_CAPS.get(font, True)), px
        return EST_ADV * px * len(text), px

    @staticmethod
    def _place(px_, pw, X, W, align):
        if align == 'Right':
            return px_ + pw - W - X
        if align == 'Center':
            return px_ + (pw - W) / 2.0 + X
        return px_ + X

    def group_box(self, els, el, root=None):
        """(x, y, w, h) of a GUIGroup element; root = the box a template body is instanced in (None = the screen)."""
        if el is None:
            return root or (0.0, 0.0, float(SCREEN[0]), float(SCREEN[1]))
        p = self.group_box(els, el.parent, root)
        e = el.eff
        W = _num(e.get('W'), p[2]); H = _num(e.get('H'), p[3])
        X = _num(e.get('X'), 0.0); Y = _num(e.get('Y'), 0.0)
        return (self._place(p[0], p[2], X, W, e.get('AlignH', 'Left')), self._place(p[1], p[3], Y, H, e.get('AlignV', 'Top')), W, H)

    def elem_text(self, el):
        """The longest string the element shows (literal or key tail) and how sure that is ('lit' | 'key' | '')."""
        cands = [s for s in [el.eff.get('Text', '')] + el.texts if s]
        if not cands:
            return '', ''
        best = max(cands, key=lambda s: len(s.lstrip('%').split('/')[-1]))
        if best.startswith('%'):
            return best[1:], 'lit'
        return best.split('/')[-1].replace('_', ' '), 'key'

    def elem_box(self, els, el, override=None, root=None):
        """(x, y, w, h, kind, sure) of an element with the attribute overrides applied; None when it has no position (flow)."""
        e = dict(el.eff); e.update(override or {})
        X, Y = _num(e.get('X')), _num(e.get('Y'))
        if X is None and Y is None:
            return None                                     # flow-positioned (the game places it after its predecessor: MercsPushIndex)
        X, Y = X or 0.0, Y or 0.0                           # GUESS: one missing coordinate reads as 0 (the _Data cells carry only Y)
        typ = e.get('Type', '')
        g = self.group_box(els, el.parent, root)
        sure = 'ok'
        if el.own.get('Template') in ARROW_TEMPLATES:
            w, h, kind = 20.0, 20.0, 'arrow'
        elif typ == 'GUIGroup':
            w, h, kind = _num(e.get('W'), g[2]), _num(e.get('H'), g[3]), 'group'
        elif e.get('Graphic'):
            wh = self.pic_size(e['Graphic'])
            if wh is None:
                wh, sure = (32, 32), 'nopic'
            w, h, kind = float(wh[0]), float(wh[1]), 'pic'
        elif typ in TEXT_TYPES or e.get('Font') or e.get('Text') or el.texts:
            s, how = self.elem_text(el)
            tw = _num(e.get('TextWidth'))
            w, px = self.measure(s, e.get('Font', 'Text'))
            if tw:
                w = min(w, tw) if s else tw
            h, kind = px * LINE_K, 'text'
            if not s:
                w = 12.0 * EST_ADV * px; sure = 'nostr'          # a Mercs* value filled at run time: a 12-character stand-in
            elif how == 'key' or self.estimated:
                sure = 'est'
        else:
            return None
        return (self._place(g[0], g[2], X, w, e.get('AlignH', 'Left')), self._place(g[1], g[3], Y, h, e.get('AlignV', 'Top')), w, h, kind, sure)


def is_strip(name):
    return any(name.startswith(p) for p in STRIP_FAMILIES)


def inside(box, name=''):
    x, y, w, h = box[:4]
    if is_strip(name):
        return 0 <= x < SCREEN[0] and 0 <= y < SCREEN[1]
    return x >= -0.5 and y >= -0.5 and x + w <= SCREEN[0] + 0.5 and y + h <= SCREEN[1] + 0.5


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


# ================================================================== selectors and rows
def select(els, sel):
    """-> [Elem] for a selector (see LAYOUT). Raises ValueError when nothing / several (pic:, #) match; a leading '?' makes a missing
    name a no-op (a picture slot a page does not have)."""
    if sel.startswith('?'):
        return [e for e in els if e.name == sel[1:]]
    if sel.startswith('pic:'):
        hit = [e for e in els if e.own.get('Graphic') == sel[4:]]
        if len(hit) != 1:
            raise ValueError('selector %s: %d elements carry that Graphic=' % (sel, len(hit)))
        return hit
    if sel.startswith('#'):
        i = int(sel[1:])
        if i >= len(els):
            raise ValueError('selector %s: the window has %d elements' % (sel, len(els)))
        return [els[i]]
    hit = [e for e in els if e.name == sel]
    if not hit:
        raise ValueError('selector %s: no element of that name' % sel)
    return hit


def row_changes(els, spec):
    """The ROWS rule -> {Elem: {attr: value}}: labels (ToggleText with the label template, top-level order), the data TextBlocks of the data
    group, the L / R arrows of the arrows group and the bars (name pattern) all re-pitched together; counts must agree."""
    labels = [e for e in els if e.type == 'ToggleText' and e.own.get('Template') == spec['label_template']]
    n = len(labels)
    if n == 0:
        raise ValueError('rows: no ToggleText with Template %s' % spec['label_template'])
    grp = {e.name: e for e in els if e.name}
    dg = grp.get(spec['data_group']); ag = grp.get(spec['arrows_group'])
    if dg is None or ag is None:
        raise ValueError('rows: group %s / %s not found' % (spec['data_group'], spec['arrows_group']))
    data = [e for e in els if e.parent is dg and e.type == 'TextBlock']
    arl = [e for e in els if e.parent is ag and e.own.get('Template') == 'OptionsArrowL_T']
    arr = [e for e in els if e.parent is ag and e.own.get('Template') == 'OptionsArrowR_T']
    if not (len(data) == len(arl) == len(arr) == n):
        raise ValueError('rows: %d labels, %d data, %d left / %d right arrows: not one per row' % (n, len(data), len(arl), len(arr)))
    out = {}
    for k in range(n):
        y = spec['y0'] + k * spec['pitch']
        out[labels[k]] = dict(X=spec['x'], Y=y)
        out[data[k]] = dict(Y=y + spec['dy_data'])
        out[arl[k]] = dict(Y=y + spec['dy_arrow']); out[arr[k]] = dict(Y=y + spec['dy_arrow'])
        if spec.get('bars'):
            for b in select(els, spec['bars'] % (k + 1)):
                out[b] = dict(X=spec['x'] + spec['dx_bar'], Y=y + spec['dy_bar'])
    return out


# ================================================================== the plan
class Change:
    __slots__ = ('el', 'attrs', 'old_box', 'new_box', 'art')

    def __init__(self, el, attrs, old_box, new_box, art):
        self.el, self.attrs, self.old_box, self.new_box, self.art = el, attrs, old_box, new_box, art


def plan_xml(xml, model, pictures, art_pics, dm_pos=None, log=print):
    """-> (changes per window {window: [Change]}, problems [str], notes [str]) for one frontend.xml.
    pictures: set of picture names the scene has (None = not readable: Graphic= targets checked against PIC_SIZES only);
    art_pics: set of ART pictures that HAVE pixels in the scene (art-dependent entries are skipped otherwise)."""
    wins, _tpl, _order = parse_windows(xml)
    changes, problems, notes = {}, [], []
    for wname, spec in LAYOUT.items():
        els = wins.get(wname)
        if els is None:
            notes.append('%s: not in this file (skipped)' % wname); continue
        if wname.startswith('Template:'):
            users = template_users(wins, wname[9:])
            extra = [u for u in users if u not in spec.get('used_by', ())]
            if extra:
                problems.append('%s is also used by %s: refused (the LAYOUT lists %s)' % (wname, extra, spec.get('used_by')))
                continue
            notes.append('%s: used by %s' % (wname, ', '.join(users) or 'nobody'))
        root = spec.get('origin')
        root = (float(root[0]), float(root[1]), float(SBS[0]), float(SBS[1])) if root else None
        wanted = {}
        for sel, attrs in spec.get('elements', {}).items():
            try:
                hit = select(els, sel)
            except ValueError as e:
                problems.append('%s: %s' % (wname, e)); continue
            for el in hit:
                a = dict(attrs); art = a.pop('art', False)
                if dm_pos and (wname, el.name) in DM_MAP and DM_MAP[(wname, el.name)] in dm_pos:
                    dx, dy = dm_pos[DM_MAP[(wname, el.name)]]
                    a['X'], a['Y'] = dx, dy
                    notes.append('%s %s: X / Y from the Dead Men inventory (%s)' % (wname, el.name, DM_MAP[(wname, el.name)]))
                if art and a.get('Graphic') not in art_pics:
                    notes.append('%s %r: art-dependent (%s has no pixels in the scene): NOT written' % (wname, el, a.get('Graphic')))
                    continue
                wanted[el] = (a, art)
        if spec.get('rows'):
            try:
                for el, a in row_changes(els, spec['rows']).items():
                    wanted[el] = (a, False)
            except ValueError as e:
                problems.append('%s: %s' % (wname, e))
        out = []
        for el, (a, art) in wanted.items():
            bad = [k for k in a if k not in GEOM_ATTRS]
            if bad:
                problems.append('%s %r: attribute(s) %s are not layout attributes' % (wname, el, bad)); continue
            g = a.get('Graphic')
            if g and pictures is not None and g not in pictures:
                problems.append('%s %r: Graphic=%s names no picture of the scene' % (wname, el, g)); continue
            if g and pictures is None and model.pic_size(g) is None:
                problems.append('%s %r: Graphic=%s is unknown here (scene not readable, not in PIC_SIZES)' % (wname, el, g)); continue
            same = all(str(el.own.get(k)) == str(v) for k, v in a.items())
            if same:
                continue
            ob = model.elem_box(els, el, None, root); nb = model.elem_box(els, el, a, root)
            if nb is None:
                problems.append('%s %r: no position after the change (X / Y missing)' % (wname, el)); continue
            name = a.get('Graphic') or el.own.get('Graphic') or el.eff.get('Graphic', '')
            if not inside(nb, name):
                problems.append('%s %r: new box %s leaves the screen' % (wname, el, _fmt(nb))); continue
            if nb[4] == 'text' and nb[1] + nb[3] > LEGEND_Y:
                notes.append('%s %r: box %s reaches into the bottom legend band (y >= %d)' % (wname, el, _fmt(nb), LEGEND_Y))
            out.append(Change(el, a, ob, nb, art))
        # text vs text overlap involving a moved element (platform copies of each other excluded)
        moved = {c.el: c for c in out}
        boxes = {}
        for el in els:
            c = moved.get(el)
            b = c.new_box if c else model.elem_box(els, el, None, root)
            if b is not None and b[4] == 'text':
                boxes[el] = (b, c.old_box if c else b)
        for c in out:
            if c.new_box[4] != 'text':
                continue
            for el, (b, b0) in boxes.items():
                if el is c.el or el.cond != c.el.cond or (el.name and el.name == c.el.name):
                    continue
                if overlap(c.new_box, b):
                    if c.old_box is not None and b0 is not None and overlap(c.old_box, b0):
                        notes.append('%s %r (%s) overlaps %r (%s) as it did before the move (stock overlap: the two show in different states)' % (wname, c.el, _fmt(c.new_box), el, _fmt(b)))
                    else:
                        problems.append('%s %r (%s) would overlap %r (%s)' % (wname, c.el, _fmt(c.new_box), el, _fmt(b)))
        changes[wname] = out
    return changes, problems, notes


def _fmt(b):
    return '(%d,%d %dx%d)' % (round(b[0]), round(b[1]), round(b[2]), round(b[3])) if b else '(flow)'


def apply_changes(xml, changes):
    """The XML with every Change's attributes written on its element's tag (only GEOM_ATTRS; nothing else in the text moves)."""
    by_start = {c.el.tag.start: c for cs in changes.values() for c in cs}

    def fn(t, text):
        c = by_start.get(t.start)
        if c is None:
            return None
        for k, v in c.attrs.items():
            text = HM.set_attr(text, k, str(v))
        return text
    out, n = HM.rewrite(xml, fn)
    if n != len(by_start):
        raise ValueError('apply: %d tags rewritten for %d changes' % (n, len(by_start)))
    return out


def element_diff(old, new):
    """Per element of two XML files: [(window, idx, attr, old, new)] of differing own attributes; raises when the element lists differ."""
    wo, _t, oo = parse_windows(old); wn, _t2, on = parse_windows(new)
    if oo != on:
        raise ValueError('window order differs')
    out = []
    for w in oo:
        a, b = wo[w], wn[w]
        if len(a) != len(b):
            raise ValueError('%s: %d vs %d elements' % (w, len(a), len(b)))
        for x, y in zip(a, b):
            if (x.name, x.own.get('Type'), x.own.get('Template'), x.depth, x.cond, x.texts) != (y.name, y.own.get('Type'), y.own.get('Template'), y.depth, y.cond, y.texts):
                raise ValueError('%s #%d: element identity differs' % (w, x.idx))
            for k in sorted(set(x.own) | set(y.own)):
                if x.own.get(k) != y.own.get(k):
                    out.append((w, x.idx, k, x.own.get(k), y.own.get(k)))
    return out


# ================================================================== the scene: pictures, fonts, the stub fill
def scene_pictures(zpath, log=print):
    """-> (pictures {name: (W, H)} incl. empty stubs with (0, 0), adv tables {font: {char: adv}}) or (None, None) when the scene cannot be read
    (a synthetic archive, a missing reader). Never raises."""
    try:
        import kl_menu_redesign_1110 as R, kl_scene, kl_prp
        sc = R.Scene(zpath, SCENE_STEM, 'dd')
        pics = {n: (int(v[0]['W']), int(v[0]['H'])) for n, v in sc.pics.items()}
        z = sc.zip
        s = kl_scene.read(z, SCENE_STEM); prp = kl_prp.Prp(z.read(SCENE_STEM + '.prp'))
        ents = list(s.entities()); nodes = prp.nodes()
        for i, e in enumerate(ents):
            if e.tid == ZWINPIC and e.parent is not None and e.name == b'Box':
                nm = e.parent.name.decode('latin1')
                if nm not in pics:
                    pics[nm] = (0, 0)
        adv = {}
        try:
            import kl_hud, kl_prmgraph as G
            p0 = G.read(z.read(SCENE_STEM + '.prm'), 'dd')
            for name, ci in HM.font_chunks(z, SCENE_STEM).items():
                _h, recs, _t = kl_hud.parse(p0.chunks[ci])
                adv[name] = {r[0]: r[10] for r in recs}
        except Exception as e:                          # fonts are a convenience for the widths
            log('  fonts not read (%s): widths estimated' % e)
        return pics, adv
    except Exception as e:
        log('  scene not readable (%s): picture sizes from PIC_SIZES, widths estimated, Graphic= targets not proven against the scene' % e)
        return None, None


def tile_plan(w, h, max_tile=MAX_TILE):
    """[(x0, y0, tw, th, tex w, tex h)]: the stock Background's way, <= max_tile columns / rows, power-of-two records."""
    def cuts(n):
        out, p = [], 0
        while p < n:
            t = min(max_tile, n - p); out.append((p, t)); p += t
        return out
    def pow2(n):
        k = 8
        while k < n:
            k *= 2
        return k
    return [(x, y, tw, th, pow2(tw), pow2(th)) for y, th in cuts(h) for x, tw in cuts(w)]


def tex_record(tid, tw, th, rgba_tile, w, h):
    """An ABGR record tw x th holding the w x h tile (top-left), the rest transparent (kl_portraits.tex_record's layout)."""
    px = bytearray(tw * th * 4)
    for y in range(h):
        px[y * tw * 4:y * tw * 4 + w * 4] = rgba_tile[y * w * 4:(y + 1) * w * 4]
    body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', tid, th, tw, 1, 0, 1.0, 0) + b'\0' + struct.pack('<I', len(px)) + bytes(px)
    return struct.pack('<I', len(body) + 4) + body


def sprite_chunk(tid):
    return bytes.fromhex('01010200') + struct.pack('<I', tid) + bytes.fromhex('00000000' '05000000' '00c20700') + bytes(12)


def pic_chunk(tiles, sprites):
    """tiles: [(x0, y0, tw, th, texw, texh)], sprites: their sprite chunk ids -> the picture chunk (kl_portraits.pic_chunk for n tiles)."""
    n = len(tiles)
    c = struct.pack('<I', n)
    for x0, y0, tw, th, texw, texh in tiles:
        c += struct.pack('<9f', x0 + tw / 2.0, -(y0 + th / 2.0), 0, 0, tw / float(texw), th / float(texh), 0, tw, th) + b'\xff\xff\xff\xff'
    c += struct.pack('<I', n) + struct.pack('<%dI' % n, *sprites)
    for k in range(n):
        c += struct.pack('<III', 1, 0xcdcdcdcd, k)
    return c + bytes(-len(c) % 16)


def fill_stubs(src, dm_zip, dst, log=print):
    """Scenes\\kaneandlynch_deadmen.zip with the ART stubs filled from the Dead Men scene. -> report dict. Refuses when a stub is not empty,
    a DM picture is missing, or the stock part would not come back byte for byte."""
    import kl_menu_redesign_1110 as R, kl_scene, kl_prp, kl_texmat as T, kl_prmgraph as G
    dm = R.Scene(dm_zip, R.DM_SCENE[1], 'dm')
    z = zipfile.ZipFile(src)
    sc = kl_scene.read(z, SCENE_STEM); prp = kl_prp.Prp(z.read(SCENE_STEM + '.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        raise ValueError('%s: .prp nodes and .gms entities do not line up' % src)
    tex = T.read_tex(z.read(SCENE_STEM + '.TEX')); prm = G.read(z.read(SCENE_STEM + '.prm'), 'dd')
    n_chunks0, tex_ids0 = len(prm.chunks), set(tex.tex)
    tid = max(tex.tex) + 1
    rep = {'filled': {}, 'tex_ids': [], 'chunks': []}
    for ddn, dmn in ART:
        i = next((k for k, e in enumerate(ents) if e.tid == ZWINPIC and e.name == b'Box' and e.parent is not None and e.parent.name.decode('latin1') == ddn), None)
        if i is None:
            raise ValueError('%s: no ZWINPIC Box under %s' % (src, ddn))
        node = nodes[i + 1]
        ints = [k for k, (op, _pl) in enumerate(node['props']) if op in (4, 9)]
        if len(ints) < 3 or [struct.unpack('<I', node['props'][k][1])[0] for k in ints[-3:]] != [0, 0, 0]:
            raise ValueError('%s: %s is not an empty stub (W, H, chunk = %s)' % (src, ddn, [struct.unpack('<I', node['props'][k][1])[0] for k in ints[-3:]]))
        inst = dm.family().get(dmn, [dmn])[0]                 # the family's first instance ('Name' or 'Name#01')
        if inst not in dm.pics:
            raise ValueError('the Dead Men scene has no picture %s' % dmn)
        img = dm.compose(inst)
        w, h = img.size
        tiles = tile_plan(w, h)
        sprites = []
        for x0, y0, tw, th, texw, texh in tiles:
            part = img.crop((x0, y0, x0 + tw, y0 + th)).tobytes()
            tex.tex[tid] = T.Texture(tex_record(tid, texw, texh, part, tw, th))
            sprites.append(G.new_chunk(prm, sprite_chunk(tid)))
            rep['tex_ids'].append(tid); tid += 1
        pc = G.new_chunk(prm, pic_chunk(tiles, sprites))
        rep['chunks'] += sprites + [pc]
        for k, v in zip(ints[-3:], (w, h, pc)):
            node['props'][k] = (node['props'][k][0], struct.pack('<I', v))
        rep['filled'][ddn] = dict(dm=dmn, w=w, h=h, tiles=len(tiles), chunk=pc)
        log('  art %s <- DM %s: %d x %d, %d tile(s), picture chunk %d' % (ddn, dmn, w, h, len(tiles), pc))
    if prm.chunks[:n_chunks0] != G.read(z.read(SCENE_STEM + '.prm'), 'dd').chunks:
        raise ValueError('a stock .prm chunk changed')
    new = {(SCENE_STEM + '.prp').lower(): prp.serialize(), (SCENE_STEM + '.TEX').lower(): T.write_tex(tex), (SCENE_STEM + '.prm').lower(): G.write(prm)}
    HM._rezip(src, dst, new)
    # proofs on the written file
    z2 = zipfile.ZipFile(dst)
    t2 = T.read_tex(z2.read(SCENE_STEM + '.TEX'))
    if any(t2.tex[k].entry != tex.tex[k].entry for k in tex_ids0) or set(t2.tex) != tex_ids0 | set(rep['tex_ids']):
        raise ValueError('the written .TEX does not hold the stock records unchanged + the new ones')
    s2 = kl_scene.read(z2, SCENE_STEM)
    if [(e.name, e.tid, e.ref) for e in s2.entities()] != [(e.name, e.tid, e.ref) for e in ents]:
        raise ValueError('the entity list changed')
    rep['entities'] = len(ents)
    return rep


# ================================================================== the DM inventory (optional)
def dm_positions(path):
    """{(window, name): (X, Y)} of the named elements of a kl_menu_inventory_1110 table (own values only, '~' = inherited skipped)."""
    out, win = {}, None
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'## Window `([^`]+)`', line)
        if m:
            win = m.group(1); continue
        if win is None or not line.startswith('| ') or line.startswith('| i |') or line.startswith('|---'):
            continue
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(c) < 9 or not c[3]:
            continue
        X, Y = c[6], c[7]
        if X.endswith('~') or Y.endswith('~'):
            continue
        x, y = _num(X), _num(Y)
        if x is not None and y is not None:
            out[(win, c[3])] = (int(x), int(y))
    return out


# ================================================================== contact sheet
def contact_sheet(sheets, path, model, log=print):
    """sheets: [(window, [(label, kind, old box, new box, moved)])] -> one PNG: per window BEFORE | AFTER at half size."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        log('  contact_layout.png not written (no Pillow)'); return False
    S = 0.5
    PW, PH, GAP, HEAD = int(SCREEN[0] * S), int(SCREEN[1] * S), 16, 18
    im = Image.new('RGB', (2 * PW + 3 * GAP, len(sheets) * (PH + HEAD + GAP) + GAP), (28, 28, 30))
    d = ImageDraw.Draw(im)
    COL = {'text': (243, 240, 234), 'pic': (120, 120, 128), 'group': (70, 70, 80), 'moved': (240, 71, 90), 'art': (224, 150, 46)}
    for r, (wname, rows) in enumerate(sheets):
        top = GAP + r * (PH + HEAD + GAP)
        for col, which in enumerate(('BEFORE', 'AFTER')):
            x0 = GAP + col * (PW + GAP)
            d.text((x0, top), '%s %s' % (wname, which), fill=(243, 240, 234))
            d.rectangle((x0, top + HEAD, x0 + PW - 1, top + HEAD + PH - 1), fill=(12, 12, 13), outline=(60, 60, 64))
            for label, kind, ob, nb, moved, art in rows:
                b = ob if col == 0 else nb
                if b is None:
                    continue
                bx, by, bw, bh = (b[0] * S, b[1] * S, max(1, b[2] * S), max(1, b[3] * S))
                bx, by = x0 + max(bx, 0), top + HEAD + max(by, 0)
                bw = min(bw, x0 + PW - bx); bh = min(bh, top + HEAD + PH - by)
                if bw <= 0 or bh <= 0:
                    continue
                colr = COL['art'] if (art and col == 1) else COL['moved'] if (moved and col == 1) else COL.get(kind, COL['text'])
                if kind == 'pic':
                    d.rectangle((bx, by, bx + bw, by + bh), fill=(44, 44, 48), outline=colr)
                else:
                    d.rectangle((bx, by, bx + bw, by + bh), outline=colr)
                if moved or kind == 'pic':
                    d.text((bx + 2, by + 1), label[:24], fill=colr)
    im.save(path)
    log('  %s written (%d windows)' % (path, len(sheets)))
    return True


def sheet_rows(xml, changes, model):
    wins, _t, _o = parse_windows(xml)
    out = []
    for wname in LAYOUT:
        els = wins.get(wname)
        if els is None:
            continue
        moved = {(c.el.window, c.el.idx): c for c in changes.get(wname, [])}      # keyed by place: the changes come from another parse
        root = LAYOUT[wname].get('origin')
        root = (float(root[0]), float(root[1]), float(SBS[0]), float(SBS[1])) if root else None
        rows = []
        for el in els:
            c = moved.get((el.window, el.idx))
            ob = model.elem_box(els, el, None, root)
            nb = c.new_box if c else ob
            if ob is None and nb is None:
                continue
            label = el.name or (c.attrs.get('Graphic') if c else None) or el.own.get('Graphic', '') or el.type
            kind = (nb or ob)[4]
            rows.append((label, kind, ob, nb, c is not None, bool(c and c.art)))
        out.append((wname, rows))
    return out


# ================================================================== archives, pins, install
def inputs_present(set_dir):
    out = []
    for n in INPUTS:
        p = os.path.join(set_dir, n)
        if os.path.isfile(p):
            out.append((n, p))
        elif n != ROWS12:
            raise ValueError('REFUSED: %s is not there (the set needs %s and %s: stage 1 + the redesign stages first)' % (p, PATCH, SCENE))
    return out


INSTALL = r'''r"""Installs / undoes the MENU LAYOUT stage (tools/kl_menu_layout_1110.py) on the live _deadmen menu files.

  python install.py            install: each live file -> <name>@TAG@ NEXT TO it (an existing backup is NEVER overwritten: refuses), then
                               the staged copy in its place. Order: Patch01_deadmen.zip FIRST, then Patch01_rows12_deadmen.zip, then the scene.
  python install.py --undo     every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: every pin and what would happen
  --game <dir>                 another Dog Days folder (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches a stock file
(<DD>\Patch01.zip, <DD>\Scenes\...), the un-themed overlay files or KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '@TAG@'
FILES = @FILES@          # (relative name under KLExpansion\Overlay, live md5 pinned at stage time, md5 of the staged copy)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    ov = os.path.join(game, 'KLExpansion', 'Overlay')
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(ov, n), os.path.join(ov, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-32s live %s' % (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or the set changed: re-stage with --accept-input)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) for p in plan) * 2 + (256 << 20)
        if shutil.disk_usage(ov).free < need:
            print('REFUSED: less than the files x2 + 256 MB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s (backup %s)' % ('restore' if undo else 'install', p[1], p[2]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(stage_dir, files, log):
    src = INSTALL.replace('@GAME@', GAME).replace('@TAG@', TAG).replace('@FILES@', repr(files))
    open(os.path.join(stage_dir, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL menu layout 1110.bat', ''), ('UNDO menu layout 1110.bat', ' --undo')):
        open(os.path.join(stage_dir, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    log('  install.py + bats written (%d files)' % len(files))


def _xml_of(zpath, member):
    z = zipfile.ZipFile(zpath)
    i = HM._member(z, member)
    if i is None:
        raise ValueError('%s has no %s' % (zpath, member))
    return z.read(i).decode('latin-1'), i.filename


def _model_for(scene_path, log):
    pics, adv = scene_pictures(scene_path, log)
    model = Model(pics, adv)
    names = set(pics) if pics is not None else None
    art = {n for n, wh in (pics or {}).items() if n in dict(ART) and wh != (0, 0)}
    return model, names, art


# ================================================================== commands
def plan(set_dir=OVERLAY, dm=None, dm_inv=None, log=print):
    """-> (per-file changes {name: changes}, problems, notes, model). Prints the plan."""
    present = inputs_present(set_dir)
    scene_path = os.path.join(set_dir, SCENE)
    model, names, art = _model_for(scene_path, log)
    dmp = None
    if dm_inv and os.path.isfile(dm_inv):
        dmp = dm_positions(dm_inv); log('  Dead Men inventory %s: %d named positions' % (dm_inv, len(dmp)))
    if dm:
        log('  --dm %s: the ART stubs would be filled by stage (the art-dependent re-points are planned as if filled)' % dm)
        art = set(dict(ART))
    allc, allp, alln = {}, [], []
    for n, p in present:
        if n == SCENE:
            continue
        xml, _m = _xml_of(p, HM.FRONT)
        ch, pr, nt = plan_xml(xml, model, names, art, dmp, log)
        allc[n] = ch; allp += ['%s: %s' % (n, x) for x in pr]; alln += ['%s: %s' % (n, x) for x in nt]
        log('== %s %s' % (n, HM.FRONT))
        for w, cs in ch.items():
            log('  %s: %d element(s) moved - %s' % (w, len(cs), LAYOUT[w].get('note', '')))
            for c in cs:
                log('    %-34s %s -> %s  %s%s' % (repr(c.el)[:34], _fmt(c.old_box), _fmt(c.new_box), ' '.join('%s=%s' % kv for kv in c.attrs.items()),
                                                 ' [art]' if c.art else '', ))
    for x in alln:
        log('  note: ' + x)
    log('  GUESS list: ' + '; '.join(GUESSES))
    for x in allp:
        log('  REFUSED: ' + x)
    log('plan: %s (%d problem(s))' % ('OK' if not allp else 'REFUSED', len(allp)))
    return allc, allp, alln, model


def stage(set_dir=OVERLAY, out=OUT, accept=False, dm=None, dm_inv=None, sheet=True, log=print):
    present = inputs_present(set_dir)
    os.makedirs(out, exist_ok=True)
    pins = ML.check_pins(present, out, accept, log)
    lines = []
    allc, allp, alln, model = plan(set_dir, dm, dm_inv, lambda s: (lines.append(s), log(s)))
    if allp:
        raise ValueError('REFUSED: the plan has %d problem(s); nothing staged' % len(allp))
    tmp = tempfile.mkdtemp(prefix='menulayout_', dir=out)
    report = dict(set=set_dir, pins=pins, dm=dm, dm_inventory=dm_inv, changes={}, art=None, guesses=GUESSES, notes=alln)
    files, sheets = [], []
    try:
        for n, p in present:
            dst = os.path.join(tmp, n)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if n == SCENE:
                if dm:
                    try:
                        report['art'] = fill_stubs(p, dm, dst, log)
                    except Exception as e:
                        raise ValueError('REFUSED: Dead Men art not staged (%s: %s); nothing written' % (type(e).__name__, e))
                else:
                    log('  %s: Dead Men art SKIPPED (no --dm): the scene is copied unchanged, the stubs stay empty' % n)
                    shutil.copyfile(p, dst)
                continue
            xml, member = _xml_of(p, HM.FRONT)
            new = apply_changes(xml, allc[n])
            if HM.signature(xml) != HM.signature(new):
                raise ValueError('%s: the table signature moved - refused' % n)
            diff = element_diff(xml, new)
            planned = {(c.el.window, c.el.idx): c.attrs for cs in allc[n].values() for c in cs}
            for w, i, k, o, v in diff:
                if k not in GEOM_ATTRS or (w, i) not in planned or str(planned[(w, i)].get(k)) != str(v):
                    raise ValueError('%s: unplanned attribute change %s #%d %s %r -> %r' % (n, w, i, k, o, v))
            HM._rezip(p, dst, {member.lower(): new.encode('latin-1')})
            report['changes'][n] = [dict(window=w, idx=i, attr=k, old=o, new=v) for w, i, k, o, v in diff]
            log('  %s: %d attribute(s) rewritten on %d element(s)' % (n, len(diff), len(planned)))
            if not sheets:
                sheets = sheet_rows(xml, allc[n], model)
        for n, p in present:
            final = os.path.join(out, n)
            os.makedirs(os.path.dirname(final), exist_ok=True)
            shutil.move(os.path.join(tmp, n), final)
            files.append((n, pins[n], ML.fmd5(final)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(pins, open(os.path.join(out, 'pins.json'), 'w'), indent=1)
    open(os.path.join(out, 'plan.txt'), 'w').write('\n'.join(lines) + '\n')
    if sheet and sheets:
        contact_sheet(sheets, os.path.join(out, 'contact_layout.png'), model, log)
    write_install(out, files, log)
    report['files'] = files
    json.dump(report, open(os.path.join(out, 'build_report.json'), 'w'), indent=1, default=str)
    for n, o, w in files:
        log('%-32s %s -> %s' % (n, o, w))
    return files


def check(stage_dir, set_dir=OVERLAY, log=print):
    """A finished stage against the live set. -> [problems]."""
    bad = []
    rp = os.path.join(stage_dir, 'build_report.json'); pp = os.path.join(stage_dir, 'pins.json')
    if not os.path.isfile(rp) or not os.path.isfile(pp):
        return ['no build_report.json / pins.json in %s' % stage_dir]
    report, pins = json.load(open(rp)), json.load(open(pp))
    for n, p in inputs_present(set_dir):
        s = os.path.join(stage_dir, n)
        if not os.path.isfile(s):
            bad.append('%s not staged' % n); continue
        if pins.get(n) != ML.fmd5(p):
            bad.append('%s: live md5 %s is not the pin %s' % (n, ML.fmd5(p), pins.get(n)))
        with zipfile.ZipFile(p) as a, zipfile.ZipFile(s) as b:
            if a.namelist() != b.namelist():
                bad.append('%s: member list differs' % n); continue
            changed = [m for m in a.namelist() if a.read(m) != b.read(m)]
        if n == SCENE:
            allowed = {(SCENE_STEM + e).lower() for e in ('.prp', '.prm', '.TEX')} if report.get('art') else set()
            extra = [m for m in changed if m.lower() not in allowed]
            if extra:
                bad.append('%s: members changed outside the allowed set: %s' % (n, extra))
            if report.get('art'):
                try:
                    import kl_texmat as T, kl_scene, kl_prmgraph as G
                    with zipfile.ZipFile(p) as a, zipfile.ZipFile(s) as b:
                        t0, t1 = T.read_tex(a.read(SCENE_STEM + '.TEX')), T.read_tex(b.read(SCENE_STEM + '.TEX'))
                        if any(t0.tex[k].entry != t1.tex[k].entry or t0.tex[k].name != t1.tex[k].name for k in t0.tex):
                            bad.append('%s: a stock .TEX record changed' % n)
                        if set(t1.tex) - set(t0.tex) != set(report['art']['tex_ids']):
                            bad.append('%s: new .TEX ids are not the reported ones' % n)
                        p0, p1 = G.read(a.read(SCENE_STEM + '.prm'), 'dd'), G.read(b.read(SCENE_STEM + '.prm'), 'dd')
                        if p1.chunks[:len(p0.chunks)] != p0.chunks:
                            bad.append('%s: a stock .prm chunk changed' % n)
                        e0 = [(e.name, e.tid, e.ref) for e in kl_scene.read(a, SCENE_STEM).entities()]
                        e1 = [(e.name, e.tid, e.ref) for e in kl_scene.read(b, SCENE_STEM).entities()]
                        if e0 != e1:
                            bad.append('%s: entity list differs (delta %d, expected 0)' % (n, len(e1) - len(e0)))
                        else:
                            log('  %s: entity delta 0 (%d entities), %d stubs filled, %d new textures' % (n, len(e1), len(report['art']['filled']), len(report['art']['tex_ids'])))
                except Exception as e:
                    bad.append('%s: scene proofs not run (%s)' % (n, e))
            else:
                log('  %s: unchanged (no art)' % n)
            continue
        extra = [m for m in changed if m.lower() != HM.FRONT.lower()]
        if extra:
            bad.append('%s: members changed outside %s: %s' % (n, HM.FRONT, extra))
        old, _m = _xml_of(p, HM.FRONT); new, _m2 = _xml_of(s, HM.FRONT)
        if HM.signature(old) != HM.signature(new):
            bad.append('%s: table signature differs' % n); continue
        try:
            diff = element_diff(old, new)
        except ValueError as e:
            bad.append('%s: %s' % (n, e)); continue
        planned = {(d['window'], d['idx'], d['attr']): d['new'] for d in report['changes'].get(n, [])}
        for w, i, k, o, v in diff:
            if k not in GEOM_ATTRS:
                bad.append('%s: %s #%d: attribute %s changed (not a layout attribute)' % (n, w, i, k))
            elif planned.get((w, i, k)) != v:
                bad.append('%s: %s #%d %s=%r is not in the build report' % (n, w, i, k, v))
        # every changed element's box inside the screen (the model of the staged file; pictures from the scene when readable)
        model, names, _art = _model_for(os.path.join(stage_dir, SCENE), lambda s: None)
        wins, _t, _o = parse_windows(new)
        for (w, i) in sorted({(d[0], d[1]) for d in diff}):
            el = wins[w][i]
            root = LAYOUT.get(w, {}).get('origin')
            root = (float(root[0]), float(root[1]), float(SBS[0]), float(SBS[1])) if root else None
            b = model.elem_box(wins[w], el, None, root)
            if b is not None and not inside(b, el.own.get('Graphic', '')):
                bad.append('%s: %s %r box %s leaves the screen' % (n, w, el, _fmt(b)))
            g = el.own.get('Graphic')
            if g and names is not None and g not in names:
                bad.append('%s: %s %r Graphic=%s names no picture of the staged scene' % (n, w, el, g))
        log('  %s: ok (%d attributes on %d elements, signature = input)' % (n, len(diff), len({(d[0], d[1]) for d in diff})))
    if not os.path.isfile(os.path.join(stage_dir, 'install.py')):
        bad.append('no install.py')
    log('check: %s' % ('PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


def main(a):
    if not a or a[0] not in ('plan', 'stage', 'check'):
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    set_dir = opt('--set', OVERLAY)
    dm_inv = opt('--dm-inventory', DM_INVENTORY_DEFAULT if os.path.isfile(DM_INVENTORY_DEFAULT) else None)
    if a[0] == 'plan':
        _c, problems, _n, _m = plan(set_dir, opt('--dm'), dm_inv)
        return 1 if problems else 0
    if a[0] == 'check':
        return 1 if check(a[1], set_dir) else 0
    stage(set_dir, opt('--out', OUT), accept='--accept-input' in a, dm=opt('--dm'), dm_inv=dm_inv, sheet='--no-sheet' not in a)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as e:
        print(e); sys.exit(1)
