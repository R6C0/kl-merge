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

MARK = '<!-- kl_shop_dm 1024 -->'
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
ALLOWED_CHANGES = {'ColorSet', 'Y', 'Font', 'TextWidth', 'AlphaMin', 'AlphaMax'}
DESC_Y, NAME_Y, STAR_DY, PRICE_DY, DESC_W = 312, 272, 14, 8, 440
FAKE_ALPHA = ('36', '40')

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
FLAV_MAX_EN = 90           # bytes of flavour text kept after the stat block: 2 wrapped lines (GUESS: ~46 characters per line at 440 px). Review 2026-10-24:
FLAV_MAX_OTHER = 90        # 100/110 bytes could wrap to 3 lines = 8 lines in all: 312 + 8*22 = 488, under the stars (y 474) and the price (y 478)


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
    cut = t[:lim]                       # cutting at an ASCII space / full stop is safe inside UTF-8 and the 1-byte code pages
    k = max(cut.rfind(b'. '), cut.rfind(b'! '), cut.rfind(b'? '))
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
    """online.xml text -> (new text, {what: count}). See the module docstring, item 1."""
    cnt = {}

    def n(k):
        cnt[k] = cnt.get(k, 0) + 1

    def fn(t, text):
        if t.window not in SHOP_WINDOWS or t.name != 'GuiElement':
            return None
        a = dict(t.attrs)
        tag, new = a.get('TagName'), text
        if a.get('ColorSet') == 'White' and 'ButtonGraphic' not in a:
            new = HM.set_attr(new, 'ColorSet', 'DMTab'); n('row ColorSet White -> DMTab')
        if tag == 'HeadlineText':
            new = HM.set_attr(new, 'ColorSet', 'DMRed'); n('headline red')
        elif a.get('Template') == 'FATotal':
            new = HM.set_attr(new, 'ColorSet', 'DirtyMoneyColorSet'); n('money green')
        elif tag == 'NewWeapon':
            new = HM.set_attr(HM.set_attr(HM.set_attr(new, 'Y', str(NAME_Y)), 'Font', 'Header'), 'ColorSet', 'DMRed'); n('name under the card')
        elif tag == 'NewWeaponDescription':
            new = HM.set_attr(HM.set_attr(HM.set_attr(new, 'Y', str(DESC_Y)), 'TextWidth', str(DESC_W)), 'ColorSet', 'DMSteel'); n('description block')
        elif tag == 'WeaponShopStar':
            new = HM.set_attr(new, 'Y', str(_ints(a['Y']) + STAR_DY)) if 'MARKSTAR' not in text else new; n('stars down')
        elif tag in ('PackagePrice', 'IsWeaponAvailable'):
            new = HM.set_attr(new, 'Y', str(_ints(a['Y']) + PRICE_DY)); n('price down')
        elif tag == 'WeaponShopFakeBar':
            new = HM.set_attr(HM.set_attr(new, 'AlphaMin', FAKE_ALPHA[0]), 'AlphaMax', FAKE_ALPHA[1]); n('fake bars dimmer')
        return new if new != text else None

    if MARK in xml:                                   # applied before: the edits above are absolute for the colours / alphas but relative
        log('  online.xml: marker found (already applied), left as it is')    # for stars / price (+14 / +8): never apply twice
        return xml, {'already applied': 1}
    out, _ = HM.rewrite(xml, fn)
    anchor = re.search(r'[ \t]*<ColorSet\s+Name="DirtyMoneyColorSet"[^>]*/>[ \t]*\r?\n', out)
    if not anchor:
        raise SystemExit('online.xml: no DirtyMoneyColorSet line to put the new colour sets after')
    nl = '\r\n' if anchor.group(0).endswith('\r\n') else '\n'
    add = MARK + nl + ''.join('  <ColorSet Name="%s" NormalColor="%s" FocusColor="%s" DisableColor="%s" />%s' % (nm, a, b, c, nl)
                              for nm, a, b, c in COLORSETS)
    out = out[:anchor.end()] + add + out[anchor.end():]
    cnt['colour sets added'] = len(COLORSETS)
    if HM.signature(out)[:0] != [] or len(HM.signature(out)) != len(HM.signature(xml)) + len(COLORSETS):
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


def paint_panel(seed=1024):
    """-> RGBA uint8 (462, 1024, 4): the BackgroundWeaponShop picture (1024 x 462 drawn at screen (1, 50); tiles = left / right 512 columns).
    Screen coordinates below; the panel's own = screen - (1, 50). The boxes sit where the stock panel's did (the bars and rows stay)."""
    np = _np()
    from PIL import Image, ImageDraw
    W_, H_ = 1024, 462
    rng = np.random.RandomState(seed)
    ox, oy = 1, 50
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

    def P(x, y):
        return (x - ox, y - oy)

    # long faint scratches
    for _ in range(90):
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); ln = int(rng.randint(30, 190)); ang = rng.uniform(-0.45, 0.45)
        d.line([(x, y), (x + ln * np.cos(ang), y + ln * np.sin(ang))], fill=(205, 210, 222, int(rng.randint(7, 24))), width=1)
    # dirt specks and a few darker blots
    for _ in range(520):
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); d.point((x, y), fill=(CHALK[0], CHALK[1], CHALK[2], int(rng.randint(20, 70))))
    for _ in range(26):
        x, y = int(rng.randint(0, W_)), int(rng.randint(0, H_)); r = int(rng.randint(2, 6)); d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 0, 0, int(rng.randint(30, 70))))

    steel_a, steel_b = STEEL + (150,), STEEL + (80,)
    # (1) the two weapon-slot boxes (page 1) and the category / list boxes (pages 2, 3): square, broken steel line, chalk brackets, red label tick
    boxes = ((11, 60, 261, 182), (11, 190, 261, 313), (291, 58, 541, 200), (291, 210, 541, 487))
    for (a, b, c, e) in boxes:
        x0, y0 = P(a, b); x1, y1 = P(c, e)
        _broken(d, x0, y0, x1, y1, steel_a, rng)
        _brackets(d, x0, y0, x1, y1, CHALK + (205,))
        d.rectangle([x0 + 14, y0 - 1, x0 + 54, y0 + 2], fill=RED_DIRTY + (225,))
    # (2) row separators: 3 in the category box (rows y 66 + 34k), 7 in the list box (rows y 216 + 34k): broken steel
    for k in range(3):
        y = 95 + 34 * k; _broken(d, *P(296, y), *P(536, y + 1), steel_b, rng, gap=0.35) if False else None
        x0, yy = P(296, y); x1, _ = P(536, y)
        for xs in range(x0, x1, 40):
            if rng.random_sample() > 0.25:
                d.line([(xs, yy), (min(x1, xs + int(rng.randint(18, 40))), yy)], fill=steel_b, width=1)
    for k in range(7):
        y = 246 + 34 * k; x0, yy = P(296, y); x1, _ = P(536, y)
        for xs in range(x0, x1, 40):
            if rng.random_sample() > 0.25:
                d.line([(xs, yy), (min(x1, xs + int(rng.randint(18, 40))), yy)], fill=steel_b, width=1)
    # (3) the frame round the big card (445 x 210 at screen (560, 60)): corner brackets + a red tab, a strip of tape over the top-left corner
    x0, y0 = P(555, 55); x1, y1 = P(1010, 275)
    _brackets(d, x0, y0, x1, y1, CHALK + (215,), ln=22, w=2)
    _broken(d, x0, y0, x1, y1, steel_b, rng, gap=0.45)
    d.rectangle([x1 - 90, y1 - 1, x1 - 30, y1 + 3], fill=RED_DIRTY + (225,))
    # (4) the name rule under the card and the stats block ('file' feel: dark, diagonal hatch, red edge strip)
    a0, b0 = P(560, 306); a1, _ = P(1005, 306)
    d.line([(a0, b0), (a1, b0)], fill=STEEL + (110,), width=1)
    d.rectangle([a0, b0 - 1, a0 + 80, b0 + 2], fill=RED_HEAD + (235,))
    sx0, sy0 = P(556, 310); sx1, sy1 = P(1010, 470)
    d.rectangle([sx0, sy0, sx1, sy1], fill=(6, 7, 10, 105))
    for k in range(-(sy1 - sy0), sx1 - sx0, 9):
        d.line([(sx0 + k, sy1), (sx0 + k + (sy1 - sy0), sy0)], fill=STEEL + (11,), width=1)
    d.rectangle([sx0, sy0, sx0 + 2, sy1], fill=RED_DIRTY + (215,))
    d.line([(sx0, sy1), (sx1, sy1)], fill=STEEL + (90,), width=1)
    # (5) the star row: a hairline above it
    a0, b0 = P(560, 472); a1, _ = P(1005, 472)
    d.line([(a0, b0), (a1, b0)], fill=STEEL + (70,), width=1)
    # (6) a few red splashes at the bottom-right of the card frame (subtle)
    for dx, dy, r in ((-14, -9, 3), (-3, -17, 2), (-24, -3, 2), (-9, -2, 1), (-31, -14, 1)):
        d.ellipse([x1 + dx - r, y1 + dy - r, x1 + dx + r, y1 + dy + r], fill=RED_DIRTY + (70,))
    out = Image.alpha_composite(base, ov)
    # tape: translucent strip, rotated, over the card frame's top-left corner
    tape = Image.new('RGBA', (52, 15), CHALK + (78,)); td = ImageDraw.Draw(tape)
    for k in range(0, 52, 3):
        td.line([(k, 0), (k, 14)], fill=CHALK + (int(rng.randint(40, 100)),))
    tape = tape.rotate(8, expand=True, resample=Image.BICUBIC)
    out.alpha_composite(tape, (x0 - 22, y0 - 10))
    a = np.asarray(out, 'uint8').copy()
    return a


def paint_bar(seed=77):
    """-> RGBA uint8 (32, 512, 4): the focus bar stroke in the stock bar's place (x 0..238, y 1..30; the rest empty): a chalk dry-brush
    with ragged ends, bristle gaps and the odd darker streak. Opaque enough for ink text; the same tile for all 20 shop bars."""
    np = _np()
    h, w = 32, 512
    rng = np.random.RandomState(seed)
    rgb = np.zeros((h, w, 3), 'float32'); al = np.zeros((h, w), 'float32')
    streak = np.clip(0.80 + 0.35 * _noise(rng, (h, 1), 1)[:, 0] + rng.normal(0, 0.07, h), 0.45, 1.05)     # per row strength
    fine = _noise(rng, (h, w), 5) * 0.5 + _noise(rng, (h, w), 14) * 0.5
    for y in range(1, 31):
        xl = int(rng.randint(0, 7)); xr = 232 + int(rng.randint(0, 7))
        edge = 1.0 if 4 <= y <= 27 else 0.55
        for x in range(xl, xr):
            a = 246 * streak[y] * edge * (0.78 + 0.34 * fine[y, x])
            if x < xl + 5:
                a *= 0.55 + 0.09 * (x - xl)                                      # soft start
            if x > xr - 34:                                                     # bristles run out: gaps get likelier
                p = (x - (xr - 34)) / 34.0
                if rng.random_sample() < 0.5 * p * p + 0.25 * p * (1 - fine[y, x]):
                    a *= 0.15
                a *= 1.0 - 0.45 * p
            al[y, x] = a
            c = 238 - 22 * (1 - fine[y, x]) + rng.normal(0, 3)
            rgb[y, x] = (c + 5, c + 2, c - 5)
    for y in rng.randint(3, 28, 5):                                              # a few darker bristle lines
        x0 = int(rng.randint(0, 120)); x1 = x0 + int(rng.randint(60, 150))
        rgb[y, x0:x1] *= 0.80
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
    marked_src = MARK in xs
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
                if k in ALLOWED_CHANGES:
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
    """PNG mock-ups of the three pages + the dialog, drawn from the XML coordinates (x = 128 + X for AlignH Left: the 768 px screen
    base group centred on 1024; AlignH Center: 512 + X) and the produced textures, with stock cards and icons. Fonts are stand-ins
    (Impact / Arial): the real FOUNMB glyphs are narrower or wider, so wraps and the bar columns are APPROXIMATE."""
    np = _np()
    from PIL import Image, ImageDraw
    import kl_texmat as T, kl_shop_cards as C
    z = zipfile.ZipFile(arc)
    xml = z.read(ONLINE).decode('latin-1')
    tex = T.read_tex(z.read(STEM + '.TEX'))
    by, _u = C.scene_pics(z, STEM)

    def tile(tid):
        w, h, px = HM.tex_pixels(tex.tex[tid].entry)
        if px is None:
            a, _i = C.decode_tile(tex, tid)
            return Image.fromarray(np.asarray(a, 'uint8'), 'RGBA')
        return Image.fromarray(np.frombuffer(bytes(px), np.uint8).reshape(h, w, 4).copy(), 'RGBA')

    bg = Image.new('RGBA', (1024, 576), (22, 23, 27, 255))
    rng = np.random.RandomState(5)
    noise = (rng.normal(0, 3, (576, 1024)) + 24).clip(0, 255).astype('uint8')
    bg = Image.fromarray(np.dstack([noise, noise, noise + 2, np.full_like(noise, 255)]), 'RGBA')
    pl, pr = sorted(by['BackgroundWeaponShop'])
    panel = Image.new('RGBA', (1024, 462)); panel.paste(tile(pl).crop((0, 0, 512, 462)), (0, 0)); panel.paste(tile(pr).crop((0, 0, 512, 462)), (512, 0))
    bartile = tile(next(t for t, us in HM.picture_uses(z, STEM).items() if {f for f, _l, _r in us} == {'FocusBar_short'})).crop((0, 0, 240, 32))
    star = tile(next(iter(by['WeaponShopStar#01']))); lock = tile(next(iter(by['WeaponShopLock#01'])))
    fonts = dict(h=_font('impact.ttf', 24), t=_font('impact.ttf', 17), s=_font('arialbd.ttf', 13), b=_font('arialbd.ttf', 12), hl=_font('impact.ttf', 25))
    CS = {'DMTab': ((0xbd, 0xb8, 0xae), (0x0c, 0x0c, 0x0d)), 'DMRed': ((0xd7, 0x37, 0x3a),) * 2, 'DMSteel': ((0x9f, 0xb4, 0xd2),) * 2}
    en = None
    for n in z.namelist():
        if n.endswith('MainEnglish.LOC'):
            en = dict(L.leaves(L.parse(z.read(n))))

    def desc(row):
        t = L.fields(en[LOCKEY + '%dDesc' % row])[0] or b''
        return t.decode('latin1').split('\n')

    def page(window, focus_row=None, focus_cat=None, slots=False, row0=0):
        im = bg.copy(); im.alpha_composite(panel, (1, 50)); d = ImageDraw.Draw(im)
        hl = _el(xml, window, TagName='HeadlineText')
        d.text((128 - 90, 5), {'FABuyWeaponsNew': 'BUY WEAPONS', 'FABuyWeaponsNewCategory': 'BUY WEAPONS', 'FABuyWeaponsNewWeapon': 'BUY WEAPONS'}[window], font=fonts['hl'], fill=CS['DMRed'][0])
        d.text((896 - 130, 15), '$ 142,500', font=fonts['t'], fill=(0x63, 0xa6, 0x5b), anchor='ra')
        d.line([(0, 33), (1024, 33)], fill=(120, 130, 150, 70)); d.line([(0, 534), (1024, 534)], fill=(120, 130, 150, 70))

        def row_text(x, y, text, focused, col='DMTab'):
            if focused:
                im.alpha_composite(bartile, (x - 17, y - 9))
            d.text((x, y), text, font=fonts['t'], fill=CS[col][1] if focused else CS[col][0])

        fake = int(re.search(r'TagName="WeaponShopFakeBar"[^>]*AlphaMax="(\d+)"', xml).group(1))
        # slots (page 1 focus; pages 2, 3 dimmed fake bars)
        for k, (nm, gun) in enumerate((('PRIMARY', 'ZASTAVA M85'), ('SECONDARY', 'M9 BERETTA'))):
            y = 66 + 130 * k
            foc = slots and k == 0
            tmp = bartile.copy()
            if not slots:
                tmp.putalpha(tmp.getchannel('A').point(lambda v: v * fake // 255)); im.alpha_composite(tmp, (18, y))
            elif foc:
                im.alpha_composite(bartile, (18, y))
            tw = d.textlength(nm, font=fonts['t']); d.text((132 - tw / 2, y + 9), nm, font=fonts['t'], fill=CS['DMTab'][1] if foc else CS['DMTab'][0])
            d.text((132, y + 90), gun, font=fonts['s'], fill=CS['DMSteel'][0], anchor='ma')
            ico = tile(next(iter(by['FAStatus_Weapon%02d#01' % W.pic_nn(28 if k == 0 else 2)])))
            im.alpha_composite(ico.resize((64, 64), Image.LANCZOS), (162 - 32 + 0, y + 26 - 8)) if False else None
        # categories
        cats = ('PISTOLS', 'SHOTGUNS', 'SUBMACHINE GUNS', 'ASSAULT RIFLES')
        for k, c in enumerate(cats):
            foc = window == 'FABuyWeaponsNewCategory' and k == (focus_cat or 0)
            if window == 'FABuyWeaponsNewWeapon':
                tmp = bartile.copy(); tmp.putalpha(tmp.getchannel('A').point(lambda v: v * fake // 255)); im.alpha_composite(tmp, (296, 66 + 34 * k))
            row_text(313, 75 + 34 * k - 8 + 8, c, foc)
        names = [HS.ROWS[r][1] for r in range(row0, row0 + 8)]
        for k, nm in enumerate(names):
            foc = window == 'FABuyWeaponsNewWeapon' and (row0 + k) == focus_row
            if window == 'FABuyWeaponsNewWeapon':
                row_text(313, 225 + 34 * k - 2, nm, foc)
                if row0 + k in (1, 3, 5):
                    im.alpha_composite(lock, (505, 216 + 34 * k))
            else:
                d.text((313, 225 + 34 * k - 2), nm, font=fonts['t'], fill=CS['DMTab'][0] + (0,) if False else (0x6f, 0x6c, 0x66))
        if window != 'FABuyWeaponsNew':
            r = focus_row if focus_row is not None else row0
            card, _i = C.decode_tile(tex, next(iter(by['FAStatus_WeaponBig#%02d' % W.pic_nn(r)])))
            im.alpha_composite(Image.fromarray(np.asarray(card, 'uint8'), 'RGBA').crop((0, 0, 445, 210)), (560, 60))
        if window == 'FABuyWeaponsNewWeapon':
            r = focus_row
            nm = _el(xml, window, TagName='NewWeapon'); ds = _el(xml, window, TagName='NewWeaponDescription')
            d.text((560, int(nm['Y'])), HS.ROWS[r][1], font=fonts['h'], fill=CS['DMRed'][0])
            d.text((1005, int(nm['Y']) + 6), '$ %s' % '{:,}'.format((2, 4, 6, 8, 10, 13, 15, 18)[r % 8] * 1000), font=fonts['t'], fill=(0x63, 0xa6, 0x5b), anchor='ra')
            y = int(ds['Y']); wid = int(ds['TextWidth'])
            for ln in desc(r):
                words, cur = ln.split(' '), ''
                for wd in words:
                    if d.textlength(cur + ' ' + wd, font=fonts['s']) > wid and cur:
                        d.text((560, y), cur, font=fonts['s'], fill=CS['DMSteel'][0]); y += int(ds['LineSpace']); cur = wd
                    else:
                        cur = (cur + ' ' + wd).strip()
                d.text((560, y), cur, font=fonts['s'], fill=CS['DMSteel'][0]); y += int(ds['LineSpace'])
            sy = int(_el(xml, window, TagName='WeaponShopStar', PlayerIndex='0')['Y'])
            for k in range(TIERS[r]):
                im.alpha_composite(star, (551 + 34 * k, sy))
        d.text((128 - 130, 534 - 28), 'NEXT ROUND 4', font=fonts['b'], fill=(0xbd, 0xb8, 0xae)); d.text((896, 534 - 28), 'BACK', font=fonts['b'], fill=(0xf3, 0xf0, 0xea), anchor='ra')
        return im.convert('RGB')

    pages = [('shop_dm_page1_slots.png', page('FABuyWeaponsNew', slots=True)),
             ('shop_dm_page2_category.png', page('FABuyWeaponsNewCategory', focus_cat=2, focus_row=18)),
             ('shop_dm_page3_weapon.png', page('FABuyWeaponsNewWeapon', focus_row=6, row0=0)),
             ('shop_dm_page3_weapon_smg.png', page('FABuyWeaponsNewWeapon', focus_row=18, row0=17))]
    # the dialog
    im = bg.copy(); d = ImageDraw.Draw(im)
    fr = tile(next(iter(by['InfoControllerFrame'])))
    im.alpha_composite(fr.resize((700, 200), Image.NEAREST), (162, 190))
    d.text((512, 240), 'Are you sure you want to purchase this weapon?', font=fonts['t'], fill=(0xf3, 0xf0, 0xea), anchor='ma')
    im.alpha_composite(bartile, (300, 320)); d.text((330, 327), 'YES', font=fonts['t'], fill=CS['DMTab'][1]); d.text((600, 327), 'NO', font=fonts['t'], fill=CS['DMTab'][0])
    pages.append(('shop_dm_dialog.png', im.convert('RGB')))
    os.makedirs(out_dir, exist_ok=True)
    for name, im in pages:
        im.save(os.path.join(out_dir, name))
    sheet = Image.new('RGB', (2048, 1152 + 0))
    for k, (_n, im) in enumerate(pages[:4]):
        sheet.paste(im, ((k % 2) * 1024, (k // 2) * 576))
    sheet.save(os.path.join(out_dir, 'shop_dm_mock.png'))
    log('mock-ups: %s' % ', '.join(n for n, _ in pages) + ', shop_dm_mock.png')


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
