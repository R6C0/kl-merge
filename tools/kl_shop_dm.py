#!/usr/bin/env python3
r"""
kl_shop_dm.py - THE WEAPON SHOP, DEAD MEN STYLE (2026-10-24; owner: 'the gun icons and the stuff around the gun shop look nice but the actual
tabs / drop down and stuff looks meh, give the gun more statistics so you can see more info on them when you hover it and just reorganise how
it looks, give it more of a dead men feel in the shop so more gritty'). OFFLINE. NOT RUN IN THE GAME. Never writes into the game folder.

WHAT IT DOES to one installed map archive (default: <DD>\KLExpansion\Maps\DM01\F01_Main.zip, read only; re/shop_plan.md, re/shop_hire.md):

 1. Menu/online.xml, the four shop windows (FABuyWeaponsNew, ...Category, ...Weapon, BuyWeaponDialog): ATTRIBUTE VALUES only, plus three new
    <ColorSet> entries (DMTab, DMRed, DMSteel; NOT a separate table: re/shop_hire.md:182-186 counts colour sets in the one 5096 table; a level load reads 2921 + these 3, 2079 free; every online.xml entry after them shifts by 3; by-name lookup assumed, GUESS). No element, no name,
    no TagName / PlayerIndex / WeaponIndex / Option / Receiver / Window / FocusGraphic / selector attribute changes (`check` proves it):
      - rows / tabs (ColorSet White): DMTab = dim chalk text, INK text when focused, so the focus bar can be a white dry-brush bar (the
        Dead Men signature: focused tab = white bar, black text);
      - headline red (DMRed), money green (the existing DirtyMoneyColorSet), the gun's name in the Header font in red under the card,
        the description in steel with TextWidth 440 (stock 470 ran off the 1024 px screen: 560 + 470 = 1030);
      - the stars and the price move 14 px down, the description starts at y 312 and has room for 7 lines (stock: y 335, 5 lines);
      - the page-2 / page-1 'fake bars' (the dimmed copy of the page before) go from alpha 100 to 40 so their text stays readable on a light bar.
 2. .TEX, only textures that nothing else uses (picture_uses check, same ids / sizes / formats; pixels spliced as kl_shop_swap.patch_pixels):
      1233 + 1234  BackgroundWeaponShop (the panel): near-black grained ground, scratches, square broken-steel boxes with chalk corner brackets,
                   red label ticks, row separators, a frame round the big card, a stats block (hatch + red edge) under it, a strip of tape;
      1202         FocusBar_short (all 20 shop bars; tile 1172 is its empty half): chalk dry-brush stroke (ragged ends, bristle gaps);
      1139         InfoControllerFrame (the BuyWeaponDialog frame): near-black with a thin steel ring.
    NOT TOUCHED: FAStatus_Weapon* icons, FAStatus_WeaponBig* cards, WeaponShopStar (1232), WeaponShopLock (1231), kl_shop_cards.py; and the shared
    Background (1224..), Line_Long (1159, 1196), FocusBar_short_03, ArrowLeft/RightWhite, tile 1172, Icon_Multiplayer (1213, free, left as is).
    All pixels are made from constants and a fixed seed, never from the old pixels: a second run gives the same bytes.
 3. .LOC, every language that has the shop leaves: AllLevels/Menu/Online/WeaponShop/Weapon<row>Desc gets a stat block between the 'Police reg.'
    line and the flavour text (see stat_lines): damage per hit at 10 m, rate of fire, magazine + ammo bought, ranges, with 10-step '|' bars.
    The numbers are READ from the build's weapon templates (the route kl_map_ai.guns uses; formulas of re/balance.md, 0x46ef60) and follow the
    build's [Shop] Swap (KLGuns.ini beside the archive): a swapped row shows the handed-over gun's numbers, the carrier's ammo (shop table).
    A language whose .LOC would go over kl_loc.LOC_CAP (Russian is full) loses the flavour text first; if it still does not fit it is left alone.

    python kl_shop_dm.py apply [--map DM01] [--src ARCHIVE] [--out DIR] [--no-mock]   build + manifest + PNG mock-ups
    python kl_shop_dm.py check [--map DM01] [--src ARCHIVE] [--out DIR]               re-parse the result, compare with the source
    python kl_shop_dm.py mock  [--map DM01] [--out DIR]                               PNG mock-ups of the three pages and the dialog only
    python kl_shop_dm.py stats [--map DM01] [--src ARCHIVE]                           the 36 stat blocks (English)
Idempotent: the XML carries the marker MARK (a second run finds it, adds no colour sets, and changes nothing); texture and .LOC output is a
pure function of constants and the source's stat-free text. Output: <work>\build\shop_dm_1024\<map>\F01_Main.zip (+ manifest.json, mock PNGs).
"""
import argparse, hashlib, json, os, re, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_shop_swap as W
import kl_hud_menu as HM
import kl_hud_shop as HS
import kl_loc as L

MARK = '<!-- kl_shop_dm 1024v2 -->'
MARK_V1 = '<!-- kl_shop_dm 1024 -->'            # v1's marker line: replaced by MARK (the v1 colour sets stay, see restyle_xml)
GAME = W.GAME
WORK_FALLBACK = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools'
OUT_NAME = os.path.join('build', 'shop_dm_1024')
STEM = 'Scenes/Locations/F01/F01_Main'
ONLINE = 'Menu/online.xml'
LOCKEY = HS.KEY                                   # AllLevels/Menu/Online/WeaponShop/Weapon
SHOP_WINDOWS = ('FABuyWeaponsNew', 'FABuyWeaponsNewCategory', 'FABuyWeaponsNewWeapon', 'BuyWeaponDialog')

# palette (tools/kl_shop_cards.py CHALK / GROUND_*, STEEL, RED; re/menus.md colours of the owner's look)
GROUND_TOP, GROUND_BOT = (0x1b, 0x1f, 0x28), (0x0c, 0x0e, 0x13)
CHALK, STEEL, RED_DIRTY, RED_HEAD = (0xf3, 0xf0, 0xea), (0x82, 0x9e, 0xc1), (0xbe, 0x24, 0x22), (0xd7, 0x37, 0x3a)
COLORSETS = (   # new <ColorSet>s, after DirtyMoneyColorSet. A bar = white (chalk) -> the focused text is INK (0c0c0d); unfocused is dim chalk
    ('DMTab',   '0xffbdb8ae', '0xff0c0c0d', '0xff8c3138'),
    ('DMRed',   '0xffd7373a', '0xffd7373a', '0xff8c3138'),
    ('DMSteel', '0xff9fb4d2', '0xff9fb4d2', '0xff6f6c66'),
)

# attribute edits (value changes only). Anything not listed here must be byte-equal in `check`.
ALLOWED_CHANGES = {'ColorSet', 'Y', 'Font', 'TextWidth', 'AlphaMin', 'AlphaMax', 'LineSpace',
                   'FadeInTime', 'FadeInDelay', 'FadeOutTime', 'X', 'GeomSpace'}
FAKE_ALPHA = ('36', '40')

# ---- v2 GRID (g = the 768 x 576 base group; virtual 1280 x 720 = g + (256, 72); the panel texture pixel = (g.x + 127, g.y - 50)).
# Every number below is ABSOLUTE (v2 sets values, it never adds to the old ones), so the pre-v1 archive, the v1 archive and a later archive
# built on v1 all end at the same bytes. One spacing unit: 6 px (box inset), 34 px (row pitch, the code-bound FocusBarDeltaY).
ROW_PITCH = 34
BOX_IN = 6                                         # outline pixel = bar edge -/+ 6: the bar's painted rows are 2..30 of its 32, columns 0..238
CAT_BAR_X, SLOT_BAR_X = 168, -110                  # code-bound bar columns (FocusBarBaseX = 168; page 1's slot bars sit at -110)
TXT_DX, TXT_DY = 15, 7                             # text = bar origin + (15, 7): cell 19 high, bar centre row 16 -> text centre 16.5 (7 + 9.5)
NAME_X, CAT_NAME_Y, LIST_NAME_Y = CAT_BAR_X + TXT_DX, 66 + TXT_DY, 216 + TXT_DY            # 183, 73, 223 (the two 'Name' groups)
SLOT_LABEL_X, SLOT_LABEL_Y = -375, (66 + TXT_DY, 196 + TXT_DY)                              # Primary / Secondary: centre at 384 - 375 = 9 = the bar's centre
GEOM_SPACE = 12                                    # GUESS (top live risk): pitch = glyph line 22 (Text font, READ: record field 11) + GeomSpace
LOCK_X = 369                                       # 32 px lock, right edge 401, 5 px inside the bar's end (406)
CARD_Y = 68                                        # card group (X 432, 445 x 210): 6 px inside the right box (outline y 62)
RIGHT_BOX = (426, 62, 882, 490)                    # right column outline; bottom = the list box's bottom
NAME_X2, NAME_Y2 = 442, 291                        # the gun's name (Header font, cell 24): x = box + 16
STAR_X0, STAR_Y = 662, 287                         # six 32 px stars right-aligned on the name row: 662 + 34 k, last right edge 864
RULE_Y = 321                                       # hairline under the name row
DESC_X, DESC_Y2, DESC_W, DESC_LS = 442, 326, 424, 20   # description block: 7 lines of 20 = 326..466 (+19 cell)
PRICE_X, PRICE_Y = -98, 470                        # right edge 768 + 98 = 866 (= DESC_X + DESC_W); in the strip under the block
FAKE6_Y = 168                                      # stock fake bar #06 had 'Y="169 "'; the real bar is 168
STAR_T = 0.15                                      # animation numbers (see ANIMATIONS in the docstring of restyle_xml)
BAR_IN, BAR_OUT = 0.12, 0.18

# the shop table's ammunition column (re/shop_plan.md:33-70, read from kl2.exe 0xbd1f68) and star tiers (same table; hashed, mock-up only)
AMMO = (150, 150, 150, 150, 150, 150, 150, 150, 60, 60, 35, 40, 40, 40, 60, 60, 60, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300,
        300, 250, 250, 50, 50, 250, 250, 250)
TIERS = (2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 3, 3, 4, 5, 5, 6, 4, 3, 3, 3, 2, 5, 5, 3, 4, 4, 4, 2, 3, 3, 4, 4, 4, 5, 5)
BAR_N = 10


def work():
    try:
        import kl_port_check
        return kl_port_check.workdir()
    except Exception:
        return WORK_FALLBACK


def default_src(map_name):
    return os.path.join(GAME, 'KLExpansion', 'Maps', map_name, 'F01_Main.zip')


def default_out(map_name):
    return os.path.join(work(), OUT_NAME, map_name)


def md5(b):
    return hashlib.md5(b).hexdigest()


def _np():
    import numpy as np
    return np


# ---------------------------------------------------------------- the numbers
# Weapon / ammo field numbers: re/balance.md 1a, tools/kl_map_ai.py:1268 (W_*, A_DAMAGE). Damage at a distance = 0x46ef60: the ammo's four
# damages lerped over the weapon's four range bands, times weapon field 25, times field 38 (1.0 for a human), times the band factor
# (fields 39..42). Rate = field 27 (rounds per minute, plausible values). Magazine = ammo field 15. Pellets = ammo field 16: GUESS
# (6 on the shotguns, 5 on the Taurus Judge; re/balance.md section 9 says the count was never read). Spread / recoil / reload: NOT shown
# (fields 20 / 53 are a GUESS, no reload time was found).
def item_names():
    en = json.load(open(os.path.join(HERE, '..', 're', 'kl2.json')))['enums']['0xd05e24']['options']
    return {v: k for k, v in en}


def templates(src):
    """{eFF2Item name: {'w': weapon field list, 'a': ammo field list}} of the archive's level (kl_arms.equipment, kl_fa.node_values)."""
    import kl_fa, kl_arms, kl_map_ai as M
    sc = kl_fa.load(src)[0]
    out = {}
    for _n, t in kl_arms.equipment(sc).items():
        k = next(iter(sc.resolve(t['path'])), None)
        v = kl_fa.node_values(sc, k) if k else None
        if not v or len(v) < 43 or not v[18]:
            continue
        a = sc.resolve(M.full(v[18][0]))
        if len(a) != 1:
            continue
        out.setdefault(t['item'], {'w': v, 'a': kl_fa.node_values(sc, a[0])})
    return out


def read_swaps(src):
    """KLGuns.ini beside the archive, [Shop] Swap=row:item,... -> {row: item}; {} without one (kl_shop_swap.set_ini writes it)."""
    ini = os.path.join(os.path.dirname(os.path.abspath(src)), 'KLGuns.ini')
    if not os.path.isfile(ini):
        return {}
    txt = open(ini, encoding='latin1').read()
    m = re.search(r'(?im)^\s*Swap\s*=\s*([0-9:, ]*)$', txt)
    out = {}
    for part in (m.group(1).split(',') if m else []):
        if ':' in part:
            r, i = part.split(':')
            out[int(r)] = int(i)
    return out


def _bullet(r, dd, mult, mp, band, dist):
    def join(i):
        return dd[i] if r[i + 1] <= r[i] else dd[i] + (dd[i + 1] - dd[i]) * (dist - r[i]) / (r[i + 1] - r[i])
    if dist <= r[0]:
        v, b = dd[0], 0
    elif dist <= r[1]:
        v, b = join(0), 0
    elif dist <= r[2]:
        v, b = join(1), 1
    elif dist <= r[3]:
        v, b = join(2), 2
    else:
        v, b = dd[3], 3
    return v * mult * mp * band[b]


def gun_stats(tpl):
    """template {'w','a'} -> dict(dmg, pel, rpm, mag, rng) or None for a gun that is not a plain bullet gun (a range or damage <= 0:
    launchers, the sniper rifle...). dmg = damage per hit at 10 m for a human player, before difficulty / Risk factors."""
    w, a = tpl['w'], tpl['a']
    r, dd, band = [float(x) for x in w[21:25]], [float(x) for x in a[17:21]], [float(x) for x in w[39:43]]
    if min(r) < 0 or min(dd) <= 0 or not w[27] or w[27] <= 0:
        return None
    return dict(dmg=_bullet(r, dd, w[25], w[38], band, 10.0), pel=int(a[16]), rpm=float(w[27]), mag=int(a[15]), rng=r)


def bar(v, scale):
    n = max(1, min(BAR_N, int(round(v / scale))))
    return '|' * n + '.' * (BAR_N - n)


def stat_lines(st, ammo):
    """-> 4 ASCII lines (strings). Bars: DMG hit at 10 m / 20, ROF rpm / 125, MAG rounds / 3, RNG longest band / 10 (10 steps, min 1).
    The font is proportional: '|' / '.' columns line up only roughly (GUESS: both glyphs exist in the shop font, needs one live look)."""
    if st is None:
        return ['DMG  SPECIAL ROUND', 'ROF  --', 'MAG  --   AMMO %d' % ammo, 'RNG  --']
    d = int(round(st['dmg']))
    dm = '%d x%d' % (d, st['pel']) if st['pel'] > 1 else '%d' % d
    r = st['rng']
    return ['DMG  %s  %s' % (bar(st['dmg'], 20.0), dm),
            'ROF  %s  %d RPM' % (bar(st['rpm'], 125.0), int(round(st['rpm']))),
            'MAG  %s  %d   AMMO %d' % (bar(st['mag'], 3.0), st['mag'], ammo),
            'RNG  %s  %s M' % (bar(r[3], 10.0), ' / '.join('%d' % int(round(x)) for x in r))]


def stat_table(src, swaps=None):
    """-> [(row, name, item, [4 lines] )] for the 36 shop rows of this archive."""
    tp, names, sw = templates(src), item_names(), swaps if swaps is not None else read_swaps(src)
    out = []
    for row, (item, name) in enumerate(HS.ROWS):
        it = sw.get(row, item)
        t = tp.get(names[it])
        out.append((row, name, it, stat_lines(gun_stats(t) if t else None, AMMO[row])))
    return out


# ---------------------------------------------------------------- .LOC
FLAV_MAX_EN = 72           # bytes of flavour text kept after the stat block. REVIEW 2026-10-24 (v2): measured with the game's own Text-font advances at
FLAV_MAX_OTHER = 72        # TextWidth 424: 90 bytes wrapped to THREE lines on 5 English / 5 German / 11 Spanish ... rows, i.e. 8 lines (5 header + 3) =
                           # 326..485, over the price strip (470) and the box (490). 72 gives <= 2 lines in all 7 languages (76 still gives 3 on some rows; 73..75 not tried)
                           # (7 lines = 326..466). A v1 source (<= 90 bytes) is re-cut to the same bytes as a pre-v1 source: checked by building both.


def _strip_stats(lines):
    """text lines of a description -> the lines without an earlier stat block of this tool (idempotence)."""
    for i, ln in enumerate(lines):
        if ln.startswith(b'DMG ') and i + 3 < len(lines) and lines[i + 1].startswith(b'ROF ') and lines[i + 3].startswith(b'RNG '):
            return lines[:i] + lines[i + 4:]
    return lines


def _flavour(rest, english):
    """the lines after the 'Police reg.' line -> flavour bytes, cut to length (English at a sentence or word end; another language is
    kept whole or dropped: a cut inside a multi-byte character would break it)."""
    t = b' '.join(x.strip() for x in rest if x.strip())
    if not t:
        return b''
    lim = FLAV_MAX_EN if english else FLAV_MAX_OTHER
    if len(t) <= lim:
        return t
    # unchanged from v1 on purpose: its output is <= FLAV_MAX bytes, so a v1 source passes through the first return above untouched and
    # a pre-v1 source is cut to the very same bytes (the upgrade paths agree).
    cut = t[:lim]                       # cutting at an ASCII space / full stop is safe inside UTF-8 and the 1-byte code pages
    wide = t[:lim + 1]                  # REVIEW v2: the sentence's space may sit AT index lim (a sentence of exactly lim bytes); a v1 source passes such
                                        # a sentence whole, so the pre-v1 path must keep it too (French row 33 differed by one word before)
    k = max(wide.rfind(b'. '), wide.rfind(b'! '), wide.rfind(b'? '))
    if k >= 30:
        return cut[:k + 1]
    k = cut.rfind(b' ')
    return cut[:k].rstrip(b',;:') + b'.' if k > 0 else b''


def rewrite_loc(data, table, english=False, log=print, tag=''):
    """one .LOC member -> (new bytes, rows changed). Keeps the first line (the 'Police reg.' line), then the stat block, then the flavour
    (if the file stays under kl_loc.LOC_CAP; else without, for all 36 rows of this language)."""
    kids = L.parse(data)
    if kids is None:
        return data, 0
    leaves = dict(L.leaves(kids))
    base = {}
    for row, _n, _it, lines in table:
        d = leaves.get(LOCKEY + '%dDesc' % row)
        if d is None or not d.flags & L.TEXT:
            continue
        txt = L.fields(d)[0] or b''
        parts = _strip_stats(txt.split(b'\n'))
        base[row] = (d, parts[0], _flavour(parts[1:], english), lines)
    if not base:
        return data, 0
    for flav in (True, False):
        for row, (d, head, fl, lines) in base.items():
            body = [head] + [x.encode('ascii') for x in lines] + ([fl] if flav and fl else [])
            e = d.raw.index(b'\0')
            d.raw = b'\n'.join(body) + d.raw[e:]
        out = L.build(kids)
        if len(out) <= L.LOC_CAP:
            assert L.build(L.parse(out)) == out
            if not flav:
                log('  %s: over %d with the flavour text, stat blocks only' % (tag, L.LOC_CAP))
            return out, len(base)
    log('  %s: %d bytes over the cap %d even without flavour: left stock' % (tag, len(out), L.LOC_CAP))
    return data, 0


# ---------------------------------------------------------------- XML
def _ints(v):
    return int(float(v))


def restyle_xml(xml, log=print):
    """online.xml text -> (new text, {what: count}). See the module docstring, item 1.

    v2: EVERY edit sets an absolute value (never 'old + n'), so the result does not depend on whether the source is the pre-v1 archive, the
    v1 archive, or a later archive built on v1: the same attribute set -> the same text. The attributes are set in a fixed order (the order v1
    used first, the v2 ones after), so a v1 source (those attributes already in place) and a pre-v1 source (appended in that order) agree.
    Sources: no marker (pre-v1: three colour sets + MARK are added); MARK_V1 (the marker line is replaced, the v1 colour sets are kept);
    MARK (already v2: left as it is)."""
    cnt = {}
    st = {'row': 0}

    def n(k):
        cnt[k] = cnt.get(k, 0) + 1

    def S(text, **kv):                                   # set_attr in the given order (python keeps keyword order)
        for k, v in kv.items():
            text = HM.set_attr(text, k, str(v))
        return text

    def fn(t, text):
        if t.window not in SHOP_WINDOWS or t.name != 'GuiElement':
            return None
        a = dict(t.attrs)
        tag, new = a.get('TagName'), text
        if a.get('Type') == 'GUIGroup' and a.get('Name') == 'Name':       # the two row groups: first = categories (Y 75), second = the list (Y 225)
            first = a.get('Y', '').strip() in ('75', str(CAT_NAME_Y))
            new = S(new, X=NAME_X, Y=CAT_NAME_Y if first else LIST_NAME_Y, GeomSpace=GEOM_SPACE); n('row group: x/y + pitch'); st['row'] = 0
            return new if new != text else None
        if a.get('Type') == 'GUIGroup' and a.get('W') == '445' and a.get('H') == '210':
            new = S(new, Y=CARD_Y); n('card group y')
            return new if new != text else None
        if a.get('Text') in ('Primary', 'Secondary') and a.get('AlignH') == 'Center':      # slot labels
            k = 0 if a['Text'] == 'Primary' else 1
            new = S(new, X=SLOT_LABEL_X, Y=SLOT_LABEL_Y[k])
            if a.get('ColorSet') == 'White':
                new = S(new, ColorSet='DMTab'); n('row ColorSet White -> DMTab')
            if a.get('Type') == 'OpenWindow':                                                # the focusable ones fade in first
                new = S(new, FadeInTime=0.12, FadeInDelay=round(0.02 + 0.04 * k, 3))
            n('slot labels')
            return new if new != text else None
        if tag in ('OldPrimaryWeapon', 'OldSecondaryWeapon'):
            new = S(new, X=SLOT_LABEL_X); n('slot gun names')
        elif tag in ('PrimaryWeapon', 'SecondaryWeapon') and a.get('Type') == 'MercsGraphicFA':
            new = S(new, X=-355); n('slot icons -5')                                         # GUESS (measured on SHOP5_280s): icon centre 14 -> 9
        elif a.get('Template') == 'FAWeaponText' and 'ButtonGraphic' not in a:
            row = st['row']; st['row'] += 1
            if a.get('ColorSet') == 'White':
                new = S(new, ColorSet='DMTab')
            if a.get('ColorSet') in ('White', 'DMTab'):
                n('row ColorSet White -> DMTab')
            if a.get('Disabled') is None or a.get('Disabled') == 'False':      # live rows: cascade in (the engine fades an element in once, on show)
                new = S(new, FadeInTime=0.12, FadeInDelay=round(0.03 + 0.035 * row, 3)); n('row cascade')
        elif a.get('ColorSet') == 'White' and 'ButtonGraphic' not in a:
            new = S(new, ColorSet='DMTab'); n('row ColorSet White -> DMTab')
        if tag == 'HeadlineText':
            new = S(new, ColorSet='DMRed'); n('headline red')
        elif a.get('Template') == 'FATotal':
            new = S(new, ColorSet='DirtyMoneyColorSet'); n('money green')
        elif tag == 'NewWeapon':
            new = S(new, Y=NAME_Y2, Font='Header', ColorSet='DMRed', X=NAME_X2, FadeInTime=0.18, FadeInDelay=0.06); n('name')
        elif tag == 'NewWeaponDescription':
            new = S(new, Y=DESC_Y2, TextWidth=DESC_W, ColorSet='DMSteel', X=DESC_X, LineSpace=DESC_LS, FadeInTime=0.25, FadeInDelay=0.14); n('description block')
        elif tag == 'WeaponShopStar':
            k = int(a['Graphic'].split('#')[1]) - 1
            new = S(new, Y=STAR_Y, X=STAR_X0 + ROW_PITCH * k, FadeInTime=STAR_T, FadeInDelay=round(0.12 + 0.06 * k, 3)); n('stars on the name row')
        elif tag in ('PackagePrice', 'IsWeaponAvailable'):
            new = S(new, Y=PRICE_Y, X=PRICE_X); n('price strip')
        elif tag == 'WeaponShopLock':
            new = S(new, X=LOCK_X); n('locks inside the bar')
        elif tag == 'WeaponShopFakeBar':
            new = S(new, AlphaMin=FAKE_ALPHA[0], AlphaMax=FAKE_ALPHA[1])
            if a.get('Graphic', '').endswith('#06'):
                new = S(new, Y=FAKE6_Y)
            n('fake bars dimmer')
        elif a.get('Template') == 'FAWeaponGraphicBig':
            new = S(new, FadeInTime=0.22, FadeInDelay=0.04); n('card fade')
        elif a.get('Type') == 'Graphic' and (a.get('IsFocusGraphic') == 'True' or a.get('Name') == 'WeaponBuyFB'):                 # the shop's focus bars
            new = S(new, FadeInTime=BAR_IN, FadeOutTime=BAR_OUT); n('focus bar timing')
        elif a.get('Type') == 'Graphic' and a.get('Graphic') == 'BackgroundWeaponShop':
            new = S(new, FadeInTime=0.15); n('panel fade')
        return new if new != text else None

    if MARK in xml:
        log('  online.xml: v2 marker found (already applied), left as it is')
        return xml, {'already applied': 1}
    v1 = MARK_V1 in xml
    out, _ = HM.rewrite(xml, fn)
    if v1:
        # v1 source: its marker + three colour sets are in place; only the marker line changes (the table does not grow)
        out = out.replace(MARK_V1, MARK, 1)
        cnt['v1 marker replaced'] = 1
        if len(HM.signature(out)) != len(HM.signature(xml)):
            raise SystemExit('online.xml: the table signature changed on a v1 source')
        return out, cnt
    anchor = re.search(r'[ \t]*<ColorSet\s+Name="DirtyMoneyColorSet"[^>]*/>[ \t]*\r?\n', out)
    if not anchor:
        raise SystemExit('online.xml: no DirtyMoneyColorSet line to put the new colour sets after')
    nl = '\r\n' if anchor.group(0).endswith('\r\n') else '\n'
    add = MARK + nl + ''.join('  <ColorSet Name="%s" NormalColor="%s" FocusColor="%s" DisableColor="%s" />%s' % (nm, a, b, c, nl)
                              for nm, a, b, c in COLORSETS)
    out = out[:anchor.end()] + add + out[anchor.end():]
    cnt['colour sets added'] = len(COLORSETS)
    if len(HM.signature(out)) != len(HM.signature(xml)) + len(COLORSETS):
        raise SystemExit('online.xml: the table signature grew by other than the colour sets')
    return out, cnt


# ---------------------------------------------------------------- textures
def _noise(rng, shape, cell):
    """smooth value noise 0..1 of `shape` (h, w), cell px"""
    np = _np()
    from PIL import Image
    h, w = shape
    g = rng.random_sample((h // cell + 2, w // cell + 2)).astype('float32')
    im = Image.fromarray((g * 255).astype('uint8')).resize((w + cell, h + cell), Image.BICUBIC)
    return np.asarray(im, dtype='float32')[:h, :w] / 255.0


def _broken(draw, x0, y0, x1, y1, col, rng, gap=0.3, width=1):
    """a hand-cut rectangle outline: each side in segments, some missing, +-1 px wobble"""
    def side(p, q, horiz):
        t = p
        while t < q:
            ln = int(rng.randint(24, 90))
            e = min(q, t + ln)
            if rng.random_sample() > gap:
                j = int(rng.randint(-1, 2))
                if horiz:
                    draw.line([(t, y_fixed + j), (e, y_fixed + j)], fill=col, width=width)
                else:
                    draw.line([(x_fixed + j, t), (x_fixed + j, e)], fill=col, width=width)
            t = e + int(rng.randint(2, 8))
    for y_fixed in (y0, y1):
        side(x0, x1, True)
    for x_fixed in (x0, x1):
        side(y0, y1, False)


def _brackets(draw, x0, y0, x1, y1, col, ln=14, w=2):
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        draw.line([(x, y), (x + dx * ln, y)], fill=col, width=w)
        draw.line([(x, y), (x, y + dy * ln)], fill=col, width=w)


def panel_px(x, y):
    """g coordinate -> pixel of the panel texture (the Graphic sits at g (-127, 50))."""
    return x + 127, y - 50


def boxes():
    """the five outline boxes in g coordinates (x0, y0, x1, y1 = outline pixels), each exactly 6 px outside the painted rows / columns of its bars"""
    sb, cb = SLOT_BAR_X, CAT_BAR_X
    return {
        'slot1': (sb - BOX_IN, 62, sb + 238 + BOX_IN, 186),
        'slot2': (sb - BOX_IN, 192, sb + 238 + BOX_IN, 316),
        'cat': (cb - BOX_IN, 66 + 2 - BOX_IN, cb + 238 + BOX_IN, 66 + 3 * ROW_PITCH + 30 + BOX_IN),          # 162, 62, 412, 204
        'list': (cb - BOX_IN, 216 + 2 - BOX_IN, cb + 238 + BOX_IN, 216 + 7 * ROW_PITCH + 30 + BOX_IN),      # 162, 212, 412, 490
        'right': RIGHT_BOX,
    }


def paint_panel(seed=1024):
    """-> RGBA uint8 (462, 1024, 4): the BackgroundWeaponShop picture, v2 'engineered' grid. All geometry is in g coordinates through
    panel_px(); every frame is drawn ON the outline pixels of boxes() (no wobble, no gaps), the corner brackets sit on the same pixels,
    ticks / separators / index marks are computed from the row pitch (34) and the bar origin, so frame, bars and text line up."""
    np = _np()
    from PIL import Image, ImageDraw
    W_, H_ = 1024, 462
    rng = np.random.RandomState(seed)
    t = np.linspace(0, 1, H_, dtype='float32')[:, None, None]
    top, bot = np.array(GROUND_TOP, 'float32'), np.array(GROUND_BOT, 'float32')
    rgb = top * (1 - t) + bot * t
    rgb = np.broadcast_to(rgb, (H_, W_, 3)).copy()
    blot = _noise(rng, (H_, W_), 48) * 14 - 7
    grain = rng.normal(0, 3.2, (H_, W_)).astype('float32')
    rgb += (blot + grain)[..., None]
    vig = np.minimum(np.minimum(np.arange(W_)[None, :], W_ - 1 - np.arange(W_)[None, :]), np.minimum(np.arange(H_)[:, None], H_ - 1 - np.arange(H_)[:, None]))
    vig = np.clip(vig / 40.0, 0, 1)
    rgb *= (0.78 + 0.22 * vig)[..., None]
    alpha = (205 + 25 * t[..., 0] + 8 * (1 - vig)).astype('float32')
    alpha = np.broadcast_to(alpha, (H_, W_)).copy()
    alpha += rng.normal(0, 4, (H_, W_))
    base = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)]).astype('uint8'), 'RGBA')

    ov = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for _ in range(60):                                                   # a few long faint scratches (fewer than v1: the grid is the star now)
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); ln = int(rng.randint(30, 190)); ang = rng.uniform(-0.45, 0.45)
        d.line([(x, y), (x + ln * np.cos(ang), y + ln * np.sin(ang))], fill=(205, 210, 222, int(rng.randint(6, 18))), width=1)
    for _ in range(420):
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); d.point((x, y), fill=(CHALK[0], CHALK[1], CHALK[2], int(rng.randint(20, 60))))
    for _ in range(18):
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); r = int(rng.randint(2, 6)); d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 0, 0, int(rng.randint(30, 60))))

    def px(x, y):
        return panel_px(x, y)

    def rect(x0, y0, x1, y1, fill):                                     # g coordinates, inclusive pixels
        a, b = px(x0, y0); c, e = px(x1, y1)
        d.rectangle([a, b, c, e], fill=fill)

    steel_a, steel_b, steel_c = STEEL + (150,), STEEL + (90,), STEEL + (60,)
    # ruler down the left edge of the panel: ticks every 10 px (3 long), every 50 px (6 long), from the top of the boxes to their bottom
    for y in range(62, 491, 10):
        ln = 6 if (y - 62) % 50 == 0 else 3
        rect(-122, y, -122 + ln, y, STEEL + (70,))
    rect(-122, 62, -122, 490, STEEL + (40,))
    for name, (x0, y0, x1, y1) in boxes().items():
        ln = 22 if name == 'right' else 14
        rect(x0, y0, x1, y0, steel_a); rect(x0, y1, x1, y1, steel_a); rect(x0, y0, x0, y1, steel_a); rect(x1, y0, x1, y1, steel_a)
        for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):          # brackets: 2 px, flush on the outline
            hx = (cx, cy, cx + dx * ln, cy + dy)
            rect(min(hx[0], hx[2]), min(hx[1], hx[3]), max(hx[0], hx[2]), max(hx[1], hx[3]), CHALK + (205,))
            vx = (cx, cy, cx + dx, cy + dy * ln)
            rect(min(vx[0], vx[2]), min(vx[1], vx[3]), max(vx[0], vx[2]), max(vx[1], vx[3]), CHALK + (205,))
        rect(x0 + 18, y0 - 1, x0 + 58, y0 + 1, RED_DIRTY + (230,))                                           # red label tab: 40 x 3 centred on the outline
        for x in range(x0 + ln + 4, x1 - ln - 3, 10):                                                         # top ruler inside the box
            long_ = (x - x0) % 50 < 10
            rect(x, y0 + 2, x, y0 + (5 if long_ else 3), STEEL + (80 if long_ else 55,))
    # rows: separators between rows (dotted 6 on / 2 off), index marks left of every bar
    def rows(bar_x, y0, n):
        for k in range(n):
            y = y0 + ROW_PITCH * k
            rect(bar_x - 5, y + 15, bar_x - 3, y + 17, CHALK + (170,))                                       # index mark: 3 x 3, centred on the bar's centre row 16
            if k < n - 1:
                for xs in range(bar_x, bar_x + 239, 8):
                    rect(xs, y + 33, min(bar_x + 238, xs + 5), y + 33, steel_b)
    rows(SLOT_BAR_X, 66, 1); rows(SLOT_BAR_X, 196, 1)
    rows(CAT_BAR_X, 66, 4); rows(CAT_BAR_X, 216, 8)
    # right column: card brackets 3 px outside the card, the name rule, the star sockets, the stats block, the price strip
    cx0, cy0, cx1, cy1 = 432 - 3, CARD_Y - 3, 432 + 444 + 3, CARD_Y + 209 + 3
    for (cx, cy, dx, dy) in ((cx0, cy0, 1, 1), (cx1, cy0, -1, 1), (cx0, cy1, 1, -1), (cx1, cy1, -1, -1)):
        rect(min(cx, cx + dx * 12), min(cy, cy + dy), max(cx, cx + dx * 12), max(cy, cy + dy), CHALK + (200,))
        rect(min(cx, cx + dx), min(cy, cy + dy * 12), max(cx, cx + dx), max(cy, cy + dy * 12), CHALK + (200,))
    rect(NAME_X2, RULE_Y, DESC_X + DESC_W, RULE_Y, STEEL + (115,))
    rect(NAME_X2, RULE_Y - 1, NAME_X2 + 80, RULE_Y + 1, RED_HEAD + (235,))
    for k in range(6):                                                                                       # star sockets: 34 px pitch, 1 px gap
        sx = STAR_X0 + ROW_PITCH * k
        for (a, b, c, e) in ((sx - 1, STAR_Y - 1, sx + 32, STAR_Y - 1), (sx - 1, STAR_Y + 32, sx + 32, STAR_Y + 32), (sx - 1, STAR_Y - 1, sx - 1, STAR_Y + 32), (sx + 32, STAR_Y - 1, sx + 32, STAR_Y + 32)):
            rect(a, b, c, e, STEEL + (46,))
    bx0, by0, bx1, by1 = NAME_X2 - 6, DESC_Y2 - 2, DESC_X + DESC_W + 6, 466
    a, b = px(bx0, by0); c, e = px(bx1, by1)
    d.rectangle([a, b, c, e], fill=(6, 7, 10, 105))
    for k in range(-(e - b), c - a, 9):
        d.line([(a + k, e), (a + k + (e - b), b)], fill=STEEL + (11,), width=1)
    rect(bx0, by0, bx0 + 2, by1, RED_DIRTY + (215,))
    rect(bx0, by1 + 1, bx1, by1 + 1, steel_b)
    rect(DESC_X + DESC_W - 60, RIGHT_BOX[3] - 1, DESC_X + DESC_W, RIGHT_BOX[3] + 1, RED_DIRTY + (225,))      # red tab on the box's bottom edge, flush right with the text
    for dx, dy, r in ((-14, -9, 3), (-3, -17, 2), (-24, -3, 2), (-9, -2, 1), (-31, -14, 1)):
        a, b = px(RIGHT_BOX[2] + dx, RIGHT_BOX[3] + dy)
        d.ellipse([a - r, b - r, a + r, b + r], fill=RED_DIRTY + (70,))
    out = Image.alpha_composite(base, ov)
    tape = Image.new('RGBA', (52, 15), CHALK + (78,)); td = ImageDraw.Draw(tape)
    for k in range(0, 52, 3):
        td.line([(k, 0), (k, 14)], fill=CHALK + (int(rng.randint(40, 100)),))
    tape = tape.rotate(8, expand=True, resample=Image.BICUBIC)
    a, b = px(RIGHT_BOX[0], RIGHT_BOX[1])
    out.alpha_composite(tape, (a - 22, b - 10))
    return np.asarray(out, 'uint8').copy()


def bar_geometry():
    """(first row, last row, first col, last col at the top, last col at the bottom): the painted part of the 32 x 512 bar tile"""
    return 2, 30, 0, 238, 232


def paint_bar(seed=77):
    """-> RGBA uint8 (32, 512, 4): the focus bar: a chalk bar on rows 2..30 (centre row 16), cols 0..238 with a straight left end, a 3 px red
    stripe at the left, a right end cut at a slant (6 px over the height), a dark bevel on the last two rows and a row of ink ticks near
    the right end. Dry-brush streaks are kept faint so the ink text stays readable."""
    np = _np()
    h, w = 32, 512
    rng = np.random.RandomState(seed)
    rgb = np.zeros((h, w, 3), 'float32'); al = np.zeros((h, w), 'float32')
    r0, r1, c0, c1, c2 = bar_geometry()
    fine = _noise(rng, (h, w), 5) * 0.5 + _noise(rng, (h, w), 14) * 0.5
    streak = np.clip(0.93 + 0.10 * _noise(rng, (h, 1), 1)[:, 0] + rng.normal(0, 0.025, h), 0.82, 1.03)
    for y in range(r0, r1 + 1):
        xr = c1 - int(round((c1 - c2) * (y - r0) / float(r1 - r0)))
        for x in range(c0, xr + 1):
            a = 248 * streak[y] * (0.90 + 0.12 * fine[y, x])
            c = 240 - 16 * (1 - fine[y, x]) + rng.normal(0, 2)
            col = (c + 5, c + 2, c - 5)
            if y >= r1 - 1:
                col = tuple(v * 0.80 for v in col)
            if x <= c0 + 2:
                col = RED_HEAD; a = 255
            al[y, x] = a
            rgb[y, x] = col
    for k in range(7):                                                                  # ink ticks: 2 x 3 px, 6 px apart, rows 6..8, right of the text area
        x = 206 + 6 * k
        for y in range(6, 9):
            xr = c1 - int(round((c1 - c2) * (y - r0) / float(r1 - r0)))
            if x + 1 <= xr - 6:
                rgb[y, x:x + 2] = (12, 12, 13); al[y, x:x + 2] = 210
    return np.dstack([np.clip(rgb, 0, 255), np.clip(al, 0, 255)]).astype('uint8')


def paint_frame(size=32):
    """-> RGBA (32, 32, 4): the BuyWeaponDialog frame (a 9-slice of unknown margins: a uniform ring survives any): near-black fill, thin steel ring."""
    np = _np()
    a = np.zeros((size, size, 4), 'uint8'); a[...] = (10, 11, 15, 238)
    a[0, :] = a[-1, :] = a[:, 0] = a[:, -1] = STEEL + (215,)
    a[1, 1:-1] = a[-2, 1:-1] = a[1:-1, 1] = a[1:-1, -2] = (CHALK[0] // 2, CHALK[1] // 2, CHALK[2] // 2, 120)
    return a


def bake_tex(tex_bytes, z, log=print):
    """-> (new .TEX bytes, [texture ids]). Verifies that nothing else draws the textures first (kl_shop_cards.scene_pics / kl_hud_menu.picture_uses)."""
    import kl_texmat as T, kl_shop_cards as C, kl_gunpics as P
    np = _np()
    by, uses = C.scene_pics(z, STEM)
    panel_t, frame_t = sorted(by['BackgroundWeaponShop']), sorted(by['InfoControllerFrame'])
    for tid, name in ((panel_t[0], 'BackgroundWeaponShop'), (panel_t[1], 'BackgroundWeaponShop'), (frame_t[0], 'InfoControllerFrame')):
        if uses[tid] != {name}:
            raise SystemExit('texture %d is shared (%s): not touched' % (tid, sorted(uses[tid])))
    bars = [tid for tid, us in HM.picture_uses(z, STEM).items() if {f for f, _l, _r in us} == {'FocusBar_short'}]
    if len(bars) != 1:
        raise SystemExit('expected one FocusBar_short-only texture, found %s' % bars)
    bar_t = bars[0]
    tex = T.read_tex(tex_bytes)
    w, h, _px = HM.tex_pixels(tex.tex[bar_t].entry)
    if (w, h) != (512, 32):
        raise SystemExit('bar tile %d is %dx%d, not 512x32' % (bar_t, w, h))
    bar = paint_bar()
    tex.tex[bar_t] = T.Texture(HM.tex_abgr(tex.tex[bar_t].entry, bar.tobytes()))
    data = T.write_tex(tex)
    pan = paint_panel()
    full = np.zeros((512, 1024, 4), 'uint8'); full[:pan.shape[0]] = pan
    ids = {panel_t[0]: P.encode_dxt5(np.ascontiguousarray(full[:, :512])), panel_t[1]: P.encode_dxt5(np.ascontiguousarray(full[:, 512:])),
           frame_t[0]: P.encode_dxt5(paint_frame())}
    expect = {panel_t[0]: ('DXT5', 512, 512), panel_t[1]: ('DXT5', 512, 512), frame_t[0]: ('DXT5', 32, 32)}
    data = W.patch_pixels(data, ids, expect)
    log('  textures: panel %s, bar %d, dialog frame %d' % (panel_t, bar_t, frame_t[0]))
    return data, panel_t + [bar_t] + frame_t


# ---------------------------------------------------------------- archive
def members(z):
    return {i.filename.lower(): i.filename for i in z.infolist()}


def apply(src, out_dir, log=print, mock=True):
    """source archive (read only) -> out_dir\\F01_Main.zip + manifest.json (+ mock PNGs). Returns the manifest."""
    if os.path.abspath(out_dir).lower().startswith(os.path.abspath(GAME).lower()):
        raise SystemExit('refusing to write into the game folder: %s' % out_dir)
    z = zipfile.ZipFile(src)
    mem = members(z)
    new, man = {}, dict(tool='tools/kl_shop_dm.py', src=src, src_md5=md5(open(src, 'rb').read()), loc={}, xml={}, tex=[])
    xml_name = mem[ONLINE.lower()]
    xml, cnt = restyle_xml(z.read(xml_name).decode('latin-1'), log)
    new[xml_name] = xml.encode('latin-1'); man['xml'] = cnt
    log('online.xml: %s' % cnt)
    tex_name = next(n for n in z.namelist() if n.lower() == (STEM + '.tex').lower())
    new[tex_name], man['tex'] = bake_tex(z.read(tex_name), z, log)
    table = stat_table(src)
    for n in z.namelist():
        m = re.search(r'F01_Main(\w+)\.LOC$', n)
        if not m:
            continue
        out, k = rewrite_loc(z.read(n), table, m.group(1) == 'English', log, m.group(1))
        if k:
            new[n] = out
        man['loc'][m.group(1)] = dict(rows=k, size=len(out), room=L.LOC_CAP - len(out))
        log('%-9s %2d rows, %d bytes (room %d)' % (m.group(1), k, len(out), L.LOC_CAP - len(out)))
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, 'F01_Main.zip')
    W.rezip_raw_multi(src, dst, new)
    man['out'] = dst; man['out_md5'] = md5(open(dst, 'rb').read()); man['out_bytes'] = os.path.getsize(dst)
    json.dump(man, open(os.path.join(out_dir, 'manifest.json'), 'w'), indent=1)
    log('wrote %s (%d bytes, md5 %s)' % (dst, man['out_bytes'], man['out_md5'][:8]))
    if mock:
        mock_all(dst, out_dir, log)
    return man


# ---------------------------------------------------------------- check
BOUND = ('Name', 'TagName', 'PlayerIndex', 'WeaponIndex', 'SelectionState', 'PageSize', 'FocusBar', 'FocusBarBaseX', 'FocusBarBaseY',
         'FocusBarDeltaX', 'FocusBarDeltaY', 'InfoTextReceiver', 'Message', 'Receiver', 'Window', 'Option', 'FocusGraphic', 'Graphic',
         'ButtonGraphic', 'Type', 'Template', 'CheckFocusIndex', 'TakeFocus', 'Link', 'ActivateButton', 'Disabled', 'ReceiveAllInput',
         'X', 'W', 'H', 'AlignH', 'AlignV', 'GeomSpace', 'Text')


def _shop_elements(xml):
    out = []
    for t in HM.tags(xml):
        if t.window in SHOP_WINDOWS and not t.close:
            out.append((t.window, t.name, [kv for kv in t.attrs]))
    return out


X_TAGS = ('WeaponShopStar', 'WeaponShopLock', 'NewWeapon', 'NewWeaponDescription', 'PackagePrice', 'IsWeaponAvailable', 'OldPrimaryWeapon',
          'OldSecondaryWeapon', 'PrimaryWeapon', 'SecondaryWeapon')


def _allowed(k, d):
    """X and GeomSpace are code-bound for most elements; v2 moves them on the listed ones only (the row groups, text / icon / star / lock /
    price elements, the slot labels). Everything else must keep its X / W / H / GeomSpace."""
    if k == 'X':
        return d.get('TagName') in X_TAGS or d.get('Name') == 'Name' or d.get('Text') in ('Primary', 'Secondary')
    if k == 'GeomSpace':
        return d.get('Name') == 'Name'
    if k in ('Y', 'FadeInTime', 'FadeInDelay', 'FadeOutTime', 'LineSpace'):
        return True
    return True


def check(src, out_dir, log=print):
    """-> list of failures ([] = PASS). Re-parses the produced archive and compares it with the source."""
    dst = os.path.join(out_dir, 'F01_Main.zip')
    fails, zs, zd = [], zipfile.ZipFile(src), zipfile.ZipFile(dst)
    if zd.testzip():
        fails.append('zip: bad member %s' % zd.testzip())
    if sorted(zs.namelist()) != sorted(zd.namelist()):
        fails.append('member lists differ')
    changed = [n for n in zs.namelist() if n in zd.namelist() and zs.read(n) != zd.read(n)]
    log('members changed: %s' % ', '.join(os.path.basename(n) for n in changed))
    for n in changed:
        if not (n.lower().endswith(('.loc', '.tex')) or n.lower() == ONLINE.lower()):
            fails.append('unexpected member changed: %s' % n)
    xs, xd = zs.read(ONLINE).decode('latin-1'), zd.read(ONLINE).decode('latin-1')
    marked_src = MARK in xs or MARK_V1 in xs
    if HM.anomalies(xd):
        fails.append('XML does not parse cleanly: %s' % HM.anomalies(xd)[:3])
    # element count and table signature
    ss, sd = HM.signature(xs), HM.signature(xd)
    cs = lambda s: sum(1 for x in s if x.startswith('GuiElement'))
    ncs = lambda s: sum(1 for x in s if x.startswith('ColorSet'))
    log('GuiElement entries: source %d, result %d; Window %d / %d; ColorSet %d / %d; ButtonGraphic %d / %d' % (
        cs(ss), cs(sd), sum(x.startswith('Window') for x in ss), sum(x.startswith('Window') for x in sd), ncs(ss), ncs(sd),
        sum(x.startswith('ButtonGraphic') for x in ss), sum(x.startswith('ButtonGraphic') for x in sd)))
    if cs(ss) != cs(sd):
        fails.append('GuiElement count changed %d -> %d' % (cs(ss), cs(sd)))
    if sd != ss and not (ncs(sd) - ncs(ss) in (0, len(COLORSETS))):
        fails.append('table signature differs by more than the colour sets')
    if not marked_src:
        sd2 = [x for x in sd if not any(x.startswith('ColorSet|%s|' % c[0]) for c in COLORSETS)]
        if sd2 != ss:
            fails.append('table signature differs beyond the %d new colour sets' % len(COLORSETS))
    if MARK not in xd:
        fails.append('marker missing')
    for c in COLORSETS:
        if 'Name="%s"' % c[0] not in xd:
            fails.append('colour set %s missing' % c[0])
    # every bound attribute identical, only ALLOWED_CHANGES differ
    es, ed = _shop_elements(xs), _shop_elements(xd)
    if len(es) != len(ed):
        fails.append('shop element count %d -> %d' % (len(es), len(ed)))
    diff = {}
    for (w1, n1, a1), (w2, n2, a2) in zip(es, ed):
        d1, d2 = dict(a1), dict(a2)
        if (w1, n1) != (w2, n2):
            fails.append('element order differs near %s/%s' % (w1, n1)); break
        for k in set(d1) | set(d2):
            if d1.get(k) != d2.get(k):
                if k in ALLOWED_CHANGES and _allowed(k, d1):
                    key = '%s.%s' % (d1.get('TagName') or d1.get('Template') or n1, k) if k != 'ColorSet' else k
                    diff.setdefault(key, set()).add((d1.get(k), d2.get(k)))
                else:
                    fails.append('%s: attribute %s changed %r -> %r (%s)' % (w1, k, d1.get(k), d2.get(k), d1.get('Name') or d1.get('TagName') or ''))
    for k, v in sorted(diff.items()):
        log('  changed %-34s %d distinct: %s' % (k, len(v), '; '.join('%s->%s' % x for x in sorted(v, key=str)[:3])))
    # code-bound names: every Name / TagName / Window / Receiver of the shop windows still exists, and the selector attributes are the same
    names = lambda e: sorted((w, d.get(k)) for w, _n, a in e for d in (dict(a),) for k in ('Name', 'TagName', 'Window', 'Receiver', 'FocusGraphic', 'InfoTextReceiver') if d.get(k))
    if names(es) != names(ed):
        fails.append('a name / TagName / Receiver / FocusGraphic of the shop windows changed')
    else:
        log('code-bound names: %d of the shop windows (Name, TagName, Window, Receiver, FocusGraphic, InfoTextReceiver) all present and equal' % len(names(es)))
    for nm in sorted(set(x for x in HM.KNOWN_WINDOWS if x in SHOP_WINDOWS)):
        if 'Window Name="%s"' % nm not in xd:
            fails.append('window %s missing' % nm)
    # the textures: ids, sizes and formats as before; the peer's textures byte-equal
    import kl_texmat as T, kl_shop_cards as C
    ts, td = T.read_tex(zs.read(STEM + '.TEX')), T.read_tex(zd.read(STEM + '.TEX'))
    by, _u = C.scene_pics(zd, STEM)
    peer = set()
    for nm, ids in by.items():
        if re.match(r'FAStatus_Weapon(Big)?\d+#?\d*$', nm) or nm.startswith(('WeaponShopStar', 'WeaponShopLock', 'FAStatus_Weapon')):
            peer |= ids
    bad = [t for t in peer if ts.tex[t].entry != td.tex[t].entry]
    log('peer textures (icons, cards, stars, locks): %d ids, %s' % (len(peer), 'all byte-equal' if not bad else 'CHANGED %s' % bad))
    if bad:
        fails.append('peer textures changed: %s' % bad)
    diff_t = [t for t in ts.tex if t in td.tex and ts.tex[t].entry != td.tex[t].entry]
    if sorted(ts.tex) != sorted(td.tex):
        fails.append('texture id set differs')
    log('textures changed: %s' % diff_t)
    for t in diff_t:
        a, b = HM.tex_pixels(ts.tex[t].entry)[:2], HM.tex_pixels(td.tex[t].entry)[:2]
        if a != b or len(ts.tex[t].entry) != len(td.tex[t].entry):
            log('  texture %d: size %s -> %s, record %d -> %d bytes' % (t, a, b, len(ts.tex[t].entry), len(td.tex[t].entry)))
    if set(diff_t) - {1233, 1234, 1202, 1139} and not set(by.get('BackgroundWeaponShop', ())) | {1202, 1139} >= set(diff_t):
        fails.append('unexpected textures changed: %s' % diff_t)
    # .LOC: every language that has the keys: stats present, size under the cap, the first line kept
    table = None
    for n in zd.namelist():
        m = re.search(r'F01_Main(\w+)\.LOC$', n)
        if not m:
            continue
        ds, dd = zs.read(n), zd.read(n)
        kd = L.parse(dd)
        if kd is None:
            log('  %-9s no shop leaves (stub), same bytes: %s' % (m.group(1), ds == dd)); continue
        lv_s, lv_d = dict(L.leaves(L.parse(ds))), dict(L.leaves(kd))
        k_stat, k_first = 0, 0
        for r in range(36):
            ds_, dd_ = lv_s.get(LOCKEY + '%dDesc' % r), lv_d.get(LOCKEY + '%dDesc' % r)
            if dd_ is None:
                continue
            t_d = (L.fields(dd_)[0] or b'').split(b'\n'); t_s = (L.fields(ds_)[0] or b'').split(b'\n')
            k_stat += any(x.startswith(b'DMG ') for x in t_d)
            k_first += t_d[0] == t_s[0]
            # flavour is one long line (the engine wraps at TextWidth); only the 4 stat lines must be short
            if max([len(x) for x in t_d if x[:4] in (b'DMG ', b'ROF ', b'MAG ', b'RNG ')] or [0]) > 48:
                fails.append('%s row %d: a stat line over 48 bytes' % (m.group(1), r))
        others = [k for k in lv_s if k.startswith(LOCKEY) and not k.endswith('Desc') or k.startswith(LOCKEY) and k.endswith('Desc') and False]
        same = all(L.fields(lv_s[k])[0] == L.fields(lv_d[k])[0] for k in others if k in lv_d)
        log('  %-9s stat blocks %2d / 36, first line kept %2d, size %d (room %d), names untouched: %s' % (m.group(1), k_stat, k_first, len(dd), L.LOC_CAP - len(dd), same))
        if len(dd) > L.LOC_CAP:
            fails.append('%s over the cap' % m.group(1))
        if k_stat not in (0, 36) or (k_stat and k_first != 36 and marked_src is False):
            fails.append('%s: %d stat blocks, first line kept %d' % (m.group(1), k_stat, k_first))
        if not same:
            fails.append('%s: a name leaf changed' % m.group(1))
    log('check: %s (%d failure(s))' % ('PASS' if not fails else 'FAIL', len(fails)))
    for f in fails:
        log('  FAIL ' + f)
    return fails


# ---------------------------------------------------------------- mock-up (PIL, from the produced archive's XML and TEX)
def _font(name, size):
    from PIL import ImageFont
    for p in (r'C:\Windows\Fonts\%s' % name, r'C:\Windows\Fonts\arialbd.ttf'):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _el(xml, window, **want):
    for t in HM.tags(xml):
        if t.window == window and not t.close:
            a = dict(t.attrs)
            if all(a.get(k) == v for k, v in want.items()):
                return a
    raise KeyError((window, want))


def mock_all(arc, out_dir, log=print):
    """PNG mock-ups, alignment-faithful (v2): a 1280 x 720 virtual screen, the 768 x 576 base group at (256, 72), every element placed from
    the produced online.xml (bars, text, card, stars, locks) and drawn with the game's own baked Text / Header glyphs (record: cell
    x0 y0 x1 y1, w, h, bearing, advance 10, line 11), so the columns, wraps and the bar-to-text fit are the real ones.
    GUESS inside the mock: a glyph's top = the element's Y + font ascent + record[9] (small glyphs such as '.' and '-' sit low) (it matches the measured bar/text centring: bar centre 82, text
    centre 82.5); the row pitch is read from the XML GeomSpace + the font line. Also writes frame strips of the three animations:
    shop_dm_anim_focus.png, shop_dm_anim_info.png, shop_dm_anim_open.png (the engine's own fade attributes, drawn as linear alpha)."""
    np = _np()
    from PIL import Image, ImageDraw
    import kl_texmat as T, kl_shop_cards as C, kl_hud as H
    z = zipfile.ZipFile(arc)
    xml = z.read(ONLINE).decode('latin-1')
    tex = T.read_tex(z.read(STEM + '.TEX'))
    by, _u = C.scene_pics(z, STEM)
    OX, OY = 256, 72

    def tile(tid):
        w, h, px = HM.tex_pixels(tex.tex[tid].entry)
        if px is None:
            a, _i = C.decode_tile(tex, tid)
            return Image.fromarray(np.asarray(a, 'uint8'), 'RGBA')
        return Image.fromarray(np.frombuffer(bytes(px), np.uint8).reshape(h, w, 4).copy(), 'RGBA')

    # ---- the game's own fonts
    _zp, _order, files, ext = H.open_level(arc)
    fo = H.fonts_of(files, ext)
    prm = H.G.read(files[ext['.prm']], 'dd')
    gl, asc = {}, {}
    for name in ('Text', 'Header'):
        _h, recs, _t = H.parse(prm.chunks[fo[name]])
        asc[name] = -_h[9]                              # the line's ascent (19 Text, 24 Header); a glyph's top = Y + ascent + record[9]
        pages, d = {}, {}
        for r in recs:
            if r[1] not in pages:
                _tid, tw, th, raw, _e = H.tex_page(tex, r[1])
                pages[r[1]] = np.frombuffer(raw, np.uint8).reshape(th, tw, 4)
            a = pages[r[1]][r[3]:r[5], r[2]:r[4], 3] if r[4] > r[2] else None
            d[r[0]] = (a, r)
        gl[name] = d

    def advance(font, s):
        return sum(gl[font].get(ord(c), gl[font][32])[1][10] for c in s)

    def hexrgb(s):
        v = int(s, 16)
        return ((v >> 16) & 255, (v >> 8) & 255, v & 255)

    CS = {nm: (hexrgb(a[4:]), hexrgb(b[4:])) for nm, a, b, _c in COLORSETS}
    GREEN = (0x63, 0xa6, 0x5b)

    def text(im, x, y, s, col, font='Text', align='l', alpha=1.0):
        """x, y in g units; the glyph cell's top sits at y; align l / c / r on x."""
        w = advance(font, s)
        px = x - (w if align == 'r' else w / 2.0 if align == 'c' else 0) + OX
        for ch in s:
            a, r = gl[font].get(ord(ch), gl[font][32])
            if a is not None and a.size:
                lay = np.zeros(a.shape + (4,), 'uint8'); lay[..., 0], lay[..., 1], lay[..., 2] = col
                lay[..., 3] = (a.astype('float32') * alpha).astype('uint8')
                im.alpha_composite(Image.fromarray(lay, 'RGBA'), (int(round(px)) + r[8], int(round(y + OY)) + asc[font] + r[9]))
            px += r[10]
        return w

    def wrap(s, width, font='Text'):
        out, cur = [], ''
        for wd in s.split(' '):
            t = (cur + ' ' + wd).strip()
            if advance(font, t) > width and cur:
                out.append(cur); cur = wd
            else:
                cur = t
        return out + [cur]

    bartile = tile(next(t for t, us in HM.picture_uses(z, STEM).items() if {f for f, _l, _r in us} == {'FocusBar_short'})).crop((0, 0, 240, 32))
    star = tile(next(iter(by['WeaponShopStar#01']))); lock = tile(next(iter(by['WeaponShopLock#01'])))
    panel_l, panel_r = sorted(by['BackgroundWeaponShop'])
    panel = Image.new('RGBA', (1024, 462)); panel.paste(tile(panel_l).crop((0, 0, 512, 462)), (0, 0)); panel.paste(tile(panel_r).crop((0, 0, 512, 462)), (512, 0))
    rng = np.random.RandomState(5)
    noise = (rng.normal(0, 3, (720, 1280)) + 24).clip(0, 255).astype('uint8')
    bg = Image.fromarray(np.dstack([noise, noise, noise + 2, np.full_like(noise, 255)]), 'RGBA')
    en = None
    for n in z.namelist():
        if n.endswith('MainEnglish.LOC'):
            en = dict(L.leaves(L.parse(z.read(n))))

    def desc(row):
        t = L.fields(en[LOCKEY + '%dDesc' % row])[0] or b''
        lines = t.decode('latin1').split('\n')
        return lines[0], lines[1:]

    def A(t, delay, dur):                                # the engine's fade-in: linear 0 -> 1 from the delay over the time
        if t is None:
            return 1.0
        return max(0.0, min(1.0, (t - delay) / dur)) if dur > 0 else float(t >= delay)

    def put(im, spr, gx, gy, alpha=1.0):
        if alpha <= 0:
            return
        if alpha < 1:
            spr = spr.copy(); spr.putalpha(spr.getchannel('A').point(lambda v: int(v * alpha)))
        im.alpha_composite(spr, (int(gx + OX), int(gy + OY)))

    def num(window, **want):
        return _el(xml, window, **want)

    CATS = ('PISTOLS', 'SHOTGUNS', 'SUBMACHINE GUNS', 'ASSAULT RIFLES')
    LIVE = {'FABuyWeaponsNew': 'BUY WEAPONS', 'FABuyWeaponsNewCategory': 'BUY WEAPONS', 'FABuyWeaponsNewWeapon': 'BUY WEAPONS'}

    def page(window, focus_row=None, focus_cat=None, slots=False, row0=0, t=None, bar_a=None):
        """t = seconds since the page opened (None = fully shown); bar_a = {row: alpha} overrides for the list focus bars."""
        im = bg.copy()
        put(im, panel, -127, 50, A(t, 0, 0.15))
        text(im, -90, 5, LIVE[window], CS['DMRed'][0], 'Header')
        text(im, 768 - 130, 15, '$ 142,500', GREEN, 'Text', 'r')
        d = ImageDraw.Draw(im)
        fake = int(num('FABuyWeaponsNewWeapon', TagName='WeaponShopFakeBar')['AlphaMax']) / 255.0
        # slots
        for k, (nm, gun) in enumerate((('PRIMARY', 'ZASTAVA M85'), ('SECONDARY', 'M9 BERETTA'))):
            y = 66 + 130 * k
            foc = slots and k == 0
            if not slots:
                put(im, bartile, SLOT_BAR_X, y, fake)
            elif foc:
                put(im, bartile, SLOT_BAR_X, y, A(t, 0, BAR_IN))
            text(im, SLOT_LABEL_X + 384, SLOT_LABEL_Y[k], nm, CS['DMTab'][1] if foc else CS['DMTab'][0], 'Text', 'c', A(t, 0.02 + 0.04 * k, 0.12))
            text(im, SLOT_LABEL_X + 384, 155 + 130 * k, gun, CS['DMSteel'][0], 'Text', 'c')
        # categories + list
        gs = GEOM_SPACE + 22
        for k, c in enumerate(CATS):
            foc = window == 'FABuyWeaponsNewCategory' and k == (focus_cat or 0)
            if window == 'FABuyWeaponsNew':
                continue
            if window == 'FABuyWeaponsNewWeapon':
                put(im, bartile, CAT_BAR_X, 66 + ROW_PITCH * k, fake)
            elif foc:
                put(im, bartile, CAT_BAR_X, 66 + ROW_PITCH * k, A(t, 0, BAR_IN))
            text(im, NAME_X, CAT_NAME_Y + gs * k, c, CS['DMTab'][1] if foc else CS['DMTab'][0])
        if window != 'FABuyWeaponsNew':
            for k in range(8):
                r = row0 + k
                foc = window == 'FABuyWeaponsNewWeapon' and r == focus_row
                if window == 'FABuyWeaponsNewWeapon':
                    ba = (bar_a or {}).get(r, 1.0 if foc else 0.0)
                    put(im, bartile, CAT_BAR_X, 216 + ROW_PITCH * k, ba)
                    ta = A(t, 0.03 + 0.035 * k, 0.12)
                    text(im, NAME_X, LIST_NAME_Y + gs * k, HS.ROWS[r][1], CS['DMTab'][1] if (foc and ba > 0.5) else CS['DMTab'][0], 'Text', 'l', ta)
                    if r in (1, 3, 5):
                        put(im, lock, LOCK_X, 216 + ROW_PITCH * k)
                else:
                    text(im, NAME_X, LIST_NAME_Y + gs * k, HS.ROWS[r][1], (0x6f, 0x6c, 0x66))
            r = focus_row if focus_row is not None else row0
            card, _i = C.decode_tile(tex, next(iter(by['FAStatus_WeaponBig#%02d' % W.pic_nn(r)])))
            put(im, Image.fromarray(np.asarray(card, 'uint8'), 'RGBA').crop((0, 0, 445, 210)), 432, CARD_Y, A(t, 0.04, 0.22))
        if window == 'FABuyWeaponsNewWeapon':
            r = focus_row
            text(im, NAME_X2, NAME_Y2, HS.ROWS[r][1], CS['DMRed'][0], 'Header', 'l', A(t, 0.06, 0.18))
            first, rest = desc(r)
            y = DESC_Y2
            body = [first] + rest
            for ln in body:
                for w2 in wrap(ln, DESC_W):
                    text(im, DESC_X, y, w2, CS['DMSteel'][0], 'Text', 'l', A(t, 0.14, 0.25)); y += DESC_LS
            for k in range(TIERS[r]):
                put(im, star, STAR_X0 + ROW_PITCH * k, STAR_Y, A(t, 0.12 + 0.06 * k, STAR_T))
            text(im, 768 - PRICE_X, PRICE_Y, '$ {:,}'.format((2, 4, 6, 8, 10, 13, 15, 18)[r % 8] * 1000), GREEN, 'Text', 'r')
        text(im, -2, 506, 'NEXT ROUND 4', (0xbd, 0xb8, 0xae)); text(im, 768, 506, 'BACK', (0xf3, 0xf0, 0xea), 'Text', 'r')
        d.rectangle([OX, OY, OX + 767, OY + 575], outline=(60, 70, 90, 255))        # the 768 x 576 base group, for the eye
        return im.convert('RGB')

    pages = [('shop_dm_page1_slots.png', page('FABuyWeaponsNew', slots=True)),
             ('shop_dm_page2_category.png', page('FABuyWeaponsNewCategory', focus_cat=2, focus_row=18, row0=17)),
             ('shop_dm_page3_weapon.png', page('FABuyWeaponsNewWeapon', focus_row=6, row0=0)),
             ('shop_dm_page3_weapon_smg.png', page('FABuyWeaponsNewWeapon', focus_row=18, row0=17))]
    im = bg.copy(); d = ImageDraw.Draw(im)
    fr = tile(next(iter(by['InfoControllerFrame'])))
    im.alpha_composite(fr.resize((700, 200), Image.NEAREST), (290, 260))
    text(im, 384, 215, 'Are you sure you want to purchase this weapon?', (0xf3, 0xf0, 0xea), 'Text', 'c')
    put(im, bartile, 90, 300); text(im, 105, 307, 'YES', CS['DMTab'][1]); text(im, 480, 307, 'NO', CS['DMTab'][0])
    pages.append(('shop_dm_dialog.png', im.convert('RGB')))
    os.makedirs(out_dir, exist_ok=True)
    for name, pim in pages:
        pim.save(os.path.join(out_dir, name))
    sheet = Image.new('RGB', (2560, 1440))
    for k, (_n, pim) in enumerate(pages[:4]):
        sheet.paste(pim, ((k % 2) * 1280, (k // 2) * 720))
    sheet.save(os.path.join(out_dir, 'shop_dm_mock.png'))

    # ---- frame strips (crop g x 150..890, y 56..500; scaled to 50 %)
    def strip(name, frames):
        crops = []
        for lab, fim in frames:
            c = fim.crop((150 + OX, 56 + OY, 890 + OX, 500 + OY)).resize((370, 222), Image.LANCZOS)
            ImageDraw.Draw(c).text((6, 4), lab, fill=(255, 255, 90))
            crops.append(c)
        sh = Image.new('RGB', (370 * 3 + 8, 222 * ((len(crops) + 2) // 3) + 4 * ((len(crops) + 2) // 3 - 1)), (10, 10, 12))
        for k, c in enumerate(crops):
            sh.paste(c, ((k % 3) * 374, (k // 3) * 226))
        sh.save(os.path.join(out_dir, name))

    W_ = 'FABuyWeaponsNewWeapon'
    # focus moving row 3 -> 4: the old bar fades out over FadeOutTime, the new bar fades in over FadeInTime (the text colour switches at once)
    fr_focus = []
    for tt in (0.0, 0.04, 0.08, 0.12, 0.18, 0.24):
        fr_focus.append(('t=%.2fs' % tt, page(W_, focus_row=4, row0=0, bar_a={3: max(0.0, 1 - tt / BAR_OUT), 4: min(1.0, tt / BAR_IN)})))
    strip('shop_dm_anim_focus.png', fr_focus)
    # focus lands on another weapon: card / name / description / stars re-fade (the same FadeIn attributes, drawn as t after the move)
    strip('shop_dm_anim_info.png', [('t=%.2fs' % tt, page(W_, focus_row=6, row0=0, t=tt, bar_a={6: 1.0})) for tt in (0.04, 0.10, 0.16, 0.24, 0.34, 0.5)])
    # page open: panel, rows cascade, card, name, description, stars
    strip('shop_dm_anim_open.png', [('t=%.2fs' % tt, page(W_, focus_row=2, row0=0, t=tt, bar_a={2: A(tt, 0.0, BAR_IN)})) for tt in (0.05, 0.10, 0.16, 0.24, 0.34, 0.5)])
    log('mock-ups: %s, shop_dm_mock.png, shop_dm_anim_focus.png, shop_dm_anim_info.png, shop_dm_anim_open.png' % ', '.join(n for n, _ in pages))


# ---------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=('apply', 'check', 'mock', 'stats'))
    ap.add_argument('--map', default='DM01')
    ap.add_argument('--src', default=None, help='source archive (default: the installed map archive, read only)')
    ap.add_argument('--out', default=None, help='output folder (default: <work>\\build\\shop_dm_1024\\<map>)')
    ap.add_argument('--no-mock', action='store_true')
    a = ap.parse_args(argv)
    src = a.src or default_src(a.map)
    out = a.out or default_out(a.map)
    if a.cmd == 'apply':
        apply(src, out, mock=not a.no_mock)
    elif a.cmd == 'check':
        sys.exit(1 if check(src, out) else 0)
    elif a.cmd == 'mock':
        mock_all(os.path.join(out, 'F01_Main.zip'), out)
    else:
        for row, name, it, lines in stat_table(src):
            print('%2d %-16s item %-3d | %s' % (row, name, it, ' | '.join(lines)))


if __name__ == '__main__':
    main()
