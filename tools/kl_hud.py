"""

HUD data for Dog Days builds: new typefaces for the ZTTFONT glyph atlases (and, later, the 200 HUD pictures).

Spec: re/hud_data.md. Nothing here touches the game folder.



A ZTTFONT chunk (see re/hud_data.md 3) is a 48-byte header, 32-byte glyph records and a tail (kerning pairs).

Page 0 of a font (a 512 x 512 ABGR texture, RGB white, alpha = coverage) holds the ordinary characters; page 1

(256 x 256, coloured) holds the button / skull / '$' pictures of the private-use characters. This module

re-rasterizes page 0 with a Windows-installed face through GDI (ctypes, no PIL) and rewrites the page-0 records;

page 1, its records, the header and the tail stay as the stock ones (ASSUMPTION: the tail is kerning for the

stock face; it is kept, so a few pairs may kern slightly wrong for the new face).



    python tools/kl_hud.py fonts <build dir or _Main.zip> <out dir> [--face "Bahnschrift SemiCondensed"]

                           [--weight 600] [--scale 1.0] [--only H1,H2,H3,...]

    python tools/kl_hud.py preview <build dir or zip> <font name> "text" <out.png>   # how a line looks

    python tools/kl_hud.py dump <build dir or zip>                                   # the fonts a level has

    python tools/kl_hud.py fonts <tree>/Overlay/Scenes/kaneandlynch.zip <out dir> --look deadmen

                                                                  # THE MENUS' lettering: the front-end scene has its own

                                                                  # eight fonts (same format); only they and their pages change

    python tools/kl_hud.py pictures <build dir or zip> <out dir> [--png <dir>]        # restyled HUD plates (see PLATES)

    python tools/kl_hud.py all <build dir or zip> <out dir> [font options]            # fonts + pictures

    python tools/kl_hud.py all <build> <out> --look deadmen       # THE OWNER'S LOOK (2026-10-11): Impact capitals (lower

                                                                  # case drawn as capitals), light chipping, brush-kit bars



PLATES: the stock plates (re/hud_data.md 2: slot 107/108 Weapon_BG 256x128, 169 Meter_BG 256x64, 161..164 GameplayTracker

256x64, 109/193 the AmmoCount tick 32x32, 0/1 the borders 128x32) are light grey rounded boxes the code draws with its own

tint / alpha (NOT established how: re/hud.md). The restyle writes dark plates with 2 px corners, a 1 px top highlight and

the alpha baked in, as uncompressed ABGR records of the same size under the same ids; `--png` also writes them as PNGs.

ASSUMPTION: the code's tint is light (white-ish), so a dark picture comes out dark; if it comes out black, lighten PLATE_RGB.



Record fields (established on F07, proven by `preview` of the stock H1): char (u32), atlas ref (u32: 4096 + id

for page 0, the bare id for page 1), x0 y0 x1 y1 (u16, page pixels), w h (i16), xoff yoff (i16: pen-relative ink

box, yoff negative = above the baseline), advance (u16), size (u16, the font's pixel size), 0, 0xcdcd.

The header is 40 bytes: 1, 8, pixel size, 1.0f, glyph count, line height, kerning pair count, 2, 3, ascent offset;

the tail is kerning pairs {u16 a, u16 b, i32 adjust} x pair count.

"""

import sys, os, struct, zipfile, ctypes, ctypes.wintypes as W, zlib, shutil



sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kl_prmgraph as G

import kl_texmat as T

import kl_gms

from kl_prp import Prp, units



REC = '<II4H4h2H2H'

PAGE = 512

PAD = 1

FONT_NAMES = ('Button', 'Text', 'DebugText', 'Menu', 'Header', 'H3', 'H2', 'H1')





# ------------------------------------------------------------------ GDI rasterizer

class _Gdi:

    def __init__(self):

        self.gdi, self.user = ctypes.windll.gdi32, ctypes.windll.user32

        g = self.gdi

        for f in ('CreateCompatibleDC', 'CreateDIBSection', 'SelectObject', 'CreateFontW'):

            getattr(g, f).restype = ctypes.c_void_p

        self.user.GetDC.restype = ctypes.c_void_p

        g.SelectObject.argtypes = (ctypes.c_void_p, ctypes.c_void_p)

        g.CreateCompatibleDC.argtypes = (ctypes.c_void_p,)

        g.DeleteObject.argtypes = (ctypes.c_void_p,)

        g.DeleteDC.argtypes = (ctypes.c_void_p,)

        for f in ('SetBkColor', 'SetTextColor', 'GetTextMetricsW', 'GetTextFaceW', 'TextOutW', 'GetCharABCWidthsW',

                  'GetTextExtentPoint32W', 'SetBkMode', 'PatBlt'):

            getattr(g, f).argtypes = None

        # the draft's own faces (Anton, Montserrat: open licence) are taken from <work>/fonts/*.ttf WITHOUT installing them:

        # AddFontResourceExW(FR_PRIVATE) makes them visible to this process only. Absent files = the installed stand-ins.

        try:

            import glob, kl_port_check

            for f in glob.glob(os.path.join(kl_port_check.workdir(), 'fonts', '*.ttf')):

                g.AddFontResourceExW(f, 0x10, None)

        except Exception:

            pass



    def has(self, face):

        try:

            self.font(face, 16, 400); return True

        except ValueError:

            return False



    def font(self, face, px, weight):

        """A DC with the face selected at `px` pixels (cell height = px; GDI's negative height = character

        height, which matches how the stock atlases were sized: the 28 px font has 20 px capitals)."""

        g = self.gdi

        self.hdc = self.user.GetDC(0)

        self.mdc = g.CreateCompatibleDC(self.hdc)

        self.w = self.h = 4 * px + 32

        class BIH(ctypes.Structure):

            _fields_ = [('biSize', W.DWORD), ('biWidth', W.LONG), ('biHeight', W.LONG), ('biPlanes', W.WORD),

                        ('biBitCount', W.WORD), ('biCompression', W.DWORD), ('biSizeImage', W.DWORD),

                        ('biXPelsPerMeter', W.LONG), ('biYPelsPerMeter', W.LONG), ('biClrUsed', W.DWORD), ('biClrImportant', W.DWORD)]

        class BI(ctypes.Structure):

            _fields_ = [('bmiHeader', BIH), ('bmiColors', W.DWORD * 3)]

        bi = BI(); bi.bmiHeader.biSize = ctypes.sizeof(BIH); bi.bmiHeader.biWidth = self.w

        bi.bmiHeader.biHeight = -self.h; bi.bmiHeader.biPlanes = 1; bi.bmiHeader.biBitCount = 32

        self.bits = ctypes.c_void_p()

        self.hbm = g.CreateDIBSection(ctypes.c_void_p(self.mdc), ctypes.byref(bi), 0, ctypes.byref(self.bits), None, 0)

        g.SelectObject(self.mdc, self.hbm)

        ANTIALIASED_QUALITY = 4

        self.ss = 4                                                            # supersampling: GDI's own AA left stair-steps live (F1)

        self.w = self.h = self.ss * (4 * px + 32)

        bi.bmiHeader.biWidth = self.w; bi.bmiHeader.biHeight = -self.h

        self.hbm = g.CreateDIBSection(ctypes.c_void_p(self.mdc), ctypes.byref(bi), 0, ctypes.byref(self.bits), None, 0)

        g.SelectObject(self.mdc, self.hbm)

        self.hf = g.CreateFontW(-px * self.ss, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, ANTIALIASED_QUALITY, 0, face)

        g.SelectObject(self.mdc, self.hf)

        buf = ctypes.create_unicode_buffer(64); g.GetTextFaceW(ctypes.c_void_p(self.mdc), 64, buf)

        if buf.value.lower() != face.lower():

            raise ValueError('GDI has no face %r (it gave %r)' % (face, buf.value))

        class TM(ctypes.Structure):

            _fields_ = [('tmHeight', W.LONG), ('tmAscent', W.LONG), ('tmDescent', W.LONG), ('tmInternalLeading', W.LONG),

                        ('tmExternalLeading', W.LONG), ('tmAveCharWidth', W.LONG), ('tmMaxCharWidth', W.LONG), ('tmWeight', W.LONG),

                        ('tmOverhang', W.LONG), ('tmDigitizedAspectX', W.LONG), ('tmDigitizedAspectY', W.LONG),

                        ('tmFirstChar', W.WCHAR), ('tmLastChar', W.WCHAR), ('tmDefaultChar', W.WCHAR), ('tmBreakChar', W.WCHAR),

                        ('tmItalic', ctypes.c_byte), ('tmUnderlined', ctypes.c_byte), ('tmStruckOut', ctypes.c_byte),

                        ('tmPitchAndFamily', ctypes.c_byte), ('tmCharSet', ctypes.c_byte)]

        tm = TM(); g.GetTextMetricsW(ctypes.c_void_p(self.mdc), ctypes.byref(tm))

        self.ascent, self.descent = (tm.tmAscent + self.ss // 2) // self.ss, (tm.tmDescent + self.ss // 2) // self.ss

        self.ascent_ss = tm.tmAscent

        g.SetBkColor(ctypes.c_void_p(self.mdc), 0x000000); g.SetTextColor(ctypes.c_void_p(self.mdc), 0xffffff)

        return self



    def glyph(self, ch):

        """-> (advance, xoff, yoff, w, h, rows of coverage bytes) with the ink box found in the rendering."""

        g = self.gdi

        g.PatBlt(ctypes.c_void_p(self.mdc), 0, 0, self.w, self.h, 0x00000042)   # BLACKNESS

        class ABC(ctypes.Structure):

            _fields_ = [('a', W.INT), ('b', W.UINT), ('c', W.INT)]

        abc = ABC()

        ox, oy = self.w // 3, self.h // 4                                        # pen origin (cell top-left)

        if not g.GetCharABCWidthsW(ctypes.c_void_p(self.mdc), ord(ch), ord(ch), ctypes.byref(abc)):

            sz = W.SIZE(); g.GetTextExtentPoint32W(ctypes.c_void_p(self.mdc), ch, 1, ctypes.byref(sz))

            abc.a, abc.b, abc.c = 0, sz.cx, 0

        ss = self.ss

        ox, oy = (ox // ss) * ss, (oy // ss) * ss                                # pen on a whole output pixel

        g.TextOutW(ctypes.c_void_p(self.mdc), ox, oy, ch, 1)

        g.GdiFlush()

        big = ctypes.string_at(self.bits, self.w * self.h * 4)

        BW = self.w

        brow = [big[4 * y * BW: 4 * (y + 1) * BW: 4] for y in range(self.h)]  # blue channel = coverage, supersampled

        bys = [y for y in range(self.h) if brow[y].strip(b'\0')]

        adv = (abc.a + abc.b + abc.c + ss // 2) // ss

        if not bys:

            return adv, 0, 0, 0, 0, []

        bx0 = min(len(brow[y]) - len(brow[y].lstrip(b'\0')) for y in bys)

        bx1 = max(len(brow[y].rstrip(b'\0')) - 1 for y in bys)

        x0, x1 = bx0 // ss, bx1 // ss; y0, y1 = bys[0] // ss, bys[-1] // ss  # output-pixel box

        ink = []

        for y in range(y0, y1 + 1):

            row = bytearray(x1 - x0 + 1)

            for x in range(x0, x1 + 1):

                t = 0

                for yy in range(ss):

                    t += sum(brow[y * ss + yy][x * ss: x * ss + ss])

                row[x - x0] = (t + ss * ss // 2) // (ss * ss)

            ink.append(row)

        return adv, x0 - ox // ss, y0 - (oy // ss + self.ascent), x1 - x0 + 1, y1 - y0 + 1, ink



    def close(self):

        g = self.gdi

        g.DeleteObject(self.hf); g.DeleteObject(self.hbm); g.DeleteDC(self.mdc)

        self.user.ReleaseDC(0, ctypes.c_void_p(self.hdc))





# ------------------------------------------------------------------ level access

def open_level(path):

    """A build folder or archive -> (zip path, member order, {name: bytes}, {'.prm': member ...})."""

    zp = path if path.lower().endswith('.zip') else next(os.path.join(path, f) for f in sorted(os.listdir(path)) if f.lower().endswith('_main.zip'))

    with zipfile.ZipFile(zp) as z:

        order = z.namelist()

        files = {n: z.read(n) for n in order}

    ext = {n.rsplit('_Main', 1)[1]: n for n in order if '_Main' in n}

    if '.gms' not in ext:                                  # the menu scene (Scenes/kaneandlynch.*): members by their stem

        stem = next(n for n in order if n.lower().endswith('.gms'))[:-4]

        ext = {n[len(stem):]: n for n in order if n.startswith(stem)}

    return zp, order, files, ext





def fonts_of(files, ext):

    """{font name: chunk index} from the ZTTFONT entities (name -> ZTTFONT[0])."""

    raw = kl_gms.unpack(files[ext['.gms']]); buf = files[ext['.buf']]

    import kl_rtp

    names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]

    for decl, tid, _prio in kl_gms.entities(raw):

        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]

        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)

    import kl_prpjoin as J

    sc = J.Scene(Prp(files[ext['.prp']]), names, tids, 'dd')

    out = {}

    for k in range(1, len(sc.nodes)):

        if sc.cls(k) == 'ZTTFONT':

            for _h, lab, u in J.fields(sc, k):

                if lab == 'ZTTFONT[0]':

                    out[sc.names[k]] = struct.unpack('<I', u[0][1])[0]

    return out





def parse(chunk):

    """-> (header tuple of 12, [records], tail bytes). Records: tuples in REC order."""

    h = struct.unpack_from('<IIIfIIIIii', chunk, 0)

    n = h[4]

    recs = [struct.unpack_from(REC, chunk, 0x28 + 32 * k) for k in range(n)]

    return h, recs, chunk[0x28 + 32 * n:]





def pack(h, recs, tail):

    out = bytearray(struct.pack('<IIIfIIIIii', *h[:4], len(recs), *h[5:]))

    for r in recs:

        out += struct.pack(REC, *r)

    out += tail

    return bytes(out)





def tex_page(tex, ref):

    """The .TEX record of an atlas ref -> (id, w, h, rgba bytes, entry)."""

    tid = ref & 0xfff

    e = tex.tex[tid].entry

    size, f1, _f2, _id, th, tw, mips, fl = struct.unpack_from('<I4s4sIHHII', e, 0)

    q = e.index(b'\0', 36) + 1

    n = struct.unpack_from('<I', e, q)[0]

    return tid, tw, th, e[q + 4:q + 4 + n], e





def tex_replace(entry, rgba):

    """The same record with new pixels (ABGR, same size)."""

    q = entry.index(b'\0', 36) + 1

    n = struct.unpack_from('<I', entry, q)[0]

    if n != len(rgba):

        raise ValueError('page size differs')

    body = entry[4:q] + struct.pack('<I', n) + bytes(rgba)

    return struct.pack('<I', len(body) + 4) + body





# ------------------------------------------------------------------ build a font

def _chip(ink, w, h, seed, px, amount):

    """Light damage on one glyph, after the Dead Men title lettering: at most two small nicks bitten out of the

    OUTLINE and, on large sizes only, rarely one hairline crack. Deterministic per character. amount 0..1 scales

    how often. LIVE 2026-10-11 (the owner's bank round): the first version chipped anywhere in the ink with a radius

    up to 1.1 px at 18 px, which closed the bowl of every 'R' ('HOUND SCORE') and cut the capital 'I' into an 'i'.

    So: narrow glyphs are left whole, a nick sits on an edge pixel, is small against the stem, and all nicks

    together may not take more than 3 % of the glyph's ink."""

    import random

    if w < 6 or h < 8 or amount <= 0:

        return ink

    rnd = random.Random(seed * 7919 + px * 31)

    rows = [bytearray(r) for r in ink]



    def at(x, y):

        return rows[y][x] if 0 <= x < w and 0 <= y < h else 0

    edge = [(x, y) for y in range(h) for x in range(w)

            if rows[y][x] > 160 and min(at(x - 1, y), at(x + 1, y), at(x, y - 1), at(x, y + 1)) < 60]

    total = sum(sum(r) for r in rows)

    if len(edge) < 12 or not total:

        return ink

    roll = rnd.random()

    chips = 2 if roll < .08 * amount else 1 if roll < .42 * amount else 0

    for _ in range(chips):

        cx, cy = rnd.choice(edge)

        rad = .35 + rnd.random() * min(.55, px / 60.0)

        trial = [bytearray(r) for r in rows]

        for y in range(max(0, int(cy - rad - 1)), min(h, int(cy + rad + 2))):

            for x in range(max(0, int(cx - rad - 1)), min(w, int(cx + rad + 2))):

                d = ((x - cx) ** 2 + (y - cy) ** 2) ** .5

                if d < rad + .5:

                    trial[y][x] = int(trial[y][x] * max(0.0, min(1.0, d - rad + .5)))

        if total - sum(sum(r) for r in trial) <= .03 * total:

            rows = trial

    if px >= 24 and rnd.random() < .07 * amount and h >= 14:   # a hairline crack, two or three pixels, large sizes only

        x, y = rnd.choice(edge); dx = rnd.choice((-1, 1)) * .5

        for k in range(rnd.randint(2, 3)):

            xi, yi = int(x + dx * k), y + k

            if 0 <= xi < w and 0 <= yi < h:

                rows[yi][xi] = rows[yi][xi] // 2

    return rows





def build_font(chunk, tex, face, weight=600, scale=1.0, log=print, caps=False, chip=0.0, px=None, track=0.0, baseline=False):

    """-> (new chunk, {texture id: new entry}, report). Page-0 records are re-rasterized with `face`; page-1

    records (private characters) are kept."""

    h, recs, tail = parse(chunk)

    px = max(1, int(px)) if px else max(1, int(round(h[2] * scale)))

    page0 = max(r[1] for r in recs)                      # the 4096 + id ref

    keep = [r for r in recs if r[1] != page0]

    todo = [r for r in recs if r[1] == page0]

    tid, tw, th, _px, entry = tex_page(tex, page0)

    gd = _Gdi().font(face, px, weight)

    glyphs = []

    for r in todo:

        ch = chr(r[0])

        if caps and ch.islower() and len(ch.upper()) == 1 and ord(ch.upper()) < 0x530:

            ch = ch.upper()                              # the game's own strings stay; lower case is DRAWN as capitals

        adv, xo, yo, w, hh, ink = gd.glyph(ch)

        if track and r[0] > 32:

            adv += int(round(track))                      # letter-spacing: extra pen advance after every glyph

        if chip and ink:

            ink = _chip(ink, w, hh, r[0], px, chip)

        glyphs.append((r, adv, xo, yo, w, hh, ink))

    gd.close()

    # shelf packing, tallest first

    order = sorted(range(len(glyphs)), key=lambda i: -glyphs[i][5])

    atlas = bytearray(tw * th)

    x = y = shelf = PAD

    place = {}

    for i in order:

        _r, _adv, _xo, _yo, w, hh, ink = glyphs[i]

        if w == 0:

            place[i] = (0, 0); continue

        if x + w + PAD > tw:

            x = PAD; y += shelf + PAD; shelf = 0

        if y + hh + PAD > th:

            raise ValueError('%s at %d px does not fit the %dx%d page' % (face, px, tw, th))

        for yy, row in enumerate(ink):

            atlas[(y + yy) * tw + x: (y + yy) * tw + x + w] = row

        place[i] = (x, y)

        x += w + PAD; shelf = max(shelf, hh)

    new = []

    for i, (r, adv, xo, yo, w, hh, _ink) in enumerate(glyphs):

        x0, y0 = place[i]

        new.append((r[0], r[1], x0, y0, x0 + w, y0 + hh, w, hh, xo, yo, adv, r[11], r[12], r[13]))

    cap = 0

    if baseline:                                         # centring (2026-10-11): the cap height of THIS bake; the header's ascent offset becomes -cap,

        for (r, adv, xo, yo, w, hh, _ink) in glyphs:     # so the capitals' top lies at the y given to Draw (the baseline is at y - header[9]: seen live, own row of V3)

            if r[0] == ord('H'):

                cap = hh

        if cap:

            h = h[:5] + (int(round(cap * 1.3)) + 2,) + h[6:9] + (-cap,)

    rgba = bytearray(b'\xff\xff\xff\0' * (tw * th))

    rgba[3::4] = atlas

    recs2 = []

    it = iter(new)

    for r in recs:                                       # stock order kept (page-1 records in place)

        recs2.append(r if r[1] != page0 else next(it))

    rep = {'face': face, 'px': px, 'cap': cap, 'track': track, 'glyphs': len(todo), 'kept': len(keep), 'page rows used': y + shelf + PAD,

           'ascent': gd.ascent, 'descent': gd.descent}

    return pack(h, recs2, tail), {tid: tex_replace(entry, rgba)}, rep





# THE DRAFT'S TYPE (2026-10-11, hud_mockup.html): --display Anton (Dead Men's heavy capitals, NOT installed here -> Impact, the

# closest installed face), --label Montserrat 800 spaced caps (NOT installed -> Segoe UI Black). Sizes are the draft's px at

# 1280 wide (1 cqw = 12.8 px) times 0.9 (the draft's Anton and Impact differ in cap height; the 0.9 was already the look's scale).

# A text takes ONE font object by SetFont and the HUD can reach four of them ([osd+0xd48/50/54/58], klhud.c); which slot

# name sits at which offset is ASSUMED from the elements' registrations (re/hud.md 2.2: d50 = the headline / ammo font = H1,

# d54 = the FA list / names = H2, d58 = tracker / text display = H3, d48 = the fourth = DebugText) - klhud.c's [HUD] Font*

# keys can re-point a role without a rebuild. face, weight, px, tracking px, chips, role (what klhud.c draws with it)

DRAFT_SPECS_ANTON = {

    # THE DRAFT'S OWN FACES at the draft's own sizes (1 cqw = 12.8 px): used when <work>/fonts holds Anton-Regular.ttf and Montserrat

    # (the variable file; GDI picks the weight). Same slots / roles as DRAFT_SPECS below.

    # SIZES, 2026-10-11 (owner: 'the smaller text versions are looking perfect ... the scoreboard text should be smaller than the Dead Men one ... so its not all in your face'):

    # the heavy Anton texts come DOWN to the label's height (label cap = 10): names / loot values / on-gun count cap 11, cash / off-gun count / count cap 10,

    # the total AND the pop-up bar cap 15 (before: 19 / 15 / 30). Below ~16 px the light chips are OFF (a nick of 0.5 px eats a 6 px stem). Labels unchanged.

    'H2':        ('Anton', 400, 12, 1, False, 'names, loot / rewards values, on-gun count  (before 21 px, cap 19; now cap 11). Stock: name tags over heads, the clock (small now)'),

    'DebugText': ('Montserrat', 800, 12, 4, False, 'LABELS  (draft Montserrat 800 .9cqw = 11.5 px, .32em)'),

    'H3':        ('Anton', 400, 11, 0, False, 'cash, count, off-gun count; stock: subtitles, tracker  (before 16 px, cap 15; now cap 10)'),

    'H1':        ('Anton', 400, 17, 1, True,  'the total AND the pop-up bar  (before 33 px, cap 30 for the total, the bar used H2 at cap 19; now cap 15 for both). Stock: other pop-ups'),

    'Button':    ('Anton', 400, 17, 0, False, 'stock: button prompts'),

    'Text':      ('Anton', 400, 21, 1, True,  'stock: general text'),

    'Menu':      ('Anton', 400, 21, 1, True,  'stock: menus in the level'),

    'Header':    ('Anton', 400, 27, 0, True,  'stock: headers'),

}



DRAFT_SPECS = {

    # 1:1 round (2026-10-11). The hook reaches four fonts: H1 = osd+0xd50, H2 = +0xd54, H3 = +0xd58, DebugText = +0xd5c (the property

    # order of re/hud_data.md: [0] template +0xd4c, [1..4] H1 H2 H3 DebugText; +0xd5c as DebugText is read from that order, NOT seen live).

    # DebugText is drawn by nothing stock, so it carries the LABEL face (Segoe UI Black standing in for Montserrat 800, tracked) without

    # side effects; H3 (stock: subtitles, the tracker's distance) becomes a small DISPLAY face so those stay readable; H2 serves names,

    # money rows, the weapon dial's count AND (hook SetFont) the pop-up bar; H1 the total. Sizes: draft px x ~0.9 (Impact is wider and

    # heavier than Anton, which is NOT installed: a GUESS). Letter-spacing of the draft (.03-.06em) as 1 px of track on the big ones.

    'H2':        ('Impact', 400, 13, 1, False, 'names, crew rows, loot values, on-gun count  (before 19 px, cap 16; now cap 11)'),

    'DebugText': ('Segoe UI Black', 400, 13, 3, False, 'LABELS: DEAD MEN, ROUND, TOTAL, LOOT, gun name  (draft Montserrat 800 .9cqw = 11.5 px, .32em)'),

    'H3':        ('Impact', 400, 12, 0, False, 'cash, count, off-gun count; stock: subtitles, tracker distance  (before 15 px, cap 13; now cap 10)'),

    'H1':        ('Impact', 400, 18, 1, True,  'the total AND the pop-up bar  (before 30 px, cap 24; now cap 15)'),

    'Button':    ('Impact', 400, 16, 0, False, 'stock: button prompts'),

    'Text':      ('Impact', 400, 19, 1, True,  'stock: general text'),

    'Menu':      ('Impact', 400, 19, 1, True,  'stock: menus in the level'),

    'Header':    ('Impact', 400, 25, 0, True,  'stock: headers'),

}





def apply(src, dst, face='Bahnschrift SemiCondensed', weight=600, scale=1.0, only=None, log=print, pictures=False, caps=False, chip=0.0, extras=False, specs=None):

    """A build (folder or zip) -> folder `dst` with the fonts replaced. Files beside the archive are copied."""

    zp, order, files, ext = open_level(src)

    fonts = fonts_of(files, ext)

    p = G.read(files[ext['.prm']], 'dd')

    tex = T.read_tex(files[ext['.TEX']])

    reps = {}

    for name, ci in sorted(fonts.items(), key=lambda kv: kv[1]):

        if only and name not in only:

            continue

        if specs and name in specs:

            f_, w_, px_, tr_, ch_, _role = specs[name]

            chunk, entries, rep = build_font(p.chunks[ci], tex, f_, w_, 1.0, log, True, chip if ch_ else 0.0, px=px_, track=tr_, baseline=True)

        else:

            chunk, entries, rep = build_font(p.chunks[ci], tex, face, weight, scale, log, caps, chip)

        p.chunks[ci] = chunk

        for tid, e in entries.items():

            tex.tex[tid] = T.Texture(e, tex.tex[tid].faces, tex.tex[tid].cube, tex.tex[tid].frames, tex.tex[tid].group)

        reps[name] = rep

        log('font %-10s chunk %d: %s %d px, track %s, cap %s, %d glyphs on page 0 (%d rows), ascent %d' % (name, ci, rep['face'], rep['px'], rep['track'], rep['cap'], rep['glyphs'], rep['page rows used'], rep['ascent']))

    files[ext['.prm']] = G.write(p)

    files[ext['.TEX']] = T.write_tex(tex)

    if pictures:

        apply_pictures(None, None, None, log, _files=(zp, order, files, ext))

    if extras:

        add_extras(files, ext, log)

    os.makedirs(dst, exist_ok=True)

    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):

        raise ValueError('the output folder is the build\'s own')

    import kl_graft

    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])

    for f in os.listdir(os.path.dirname(zp)):

        q = os.path.join(os.path.dirname(zp), f)

        if os.path.isfile(q) and not os.path.samefile(q, zp):

            shutil.copyfile(q, os.path.join(dst, f))

    log('wrote %s' % out)

    return out, reps





def check(src, dst, log=print, pictures=False, extras=False, draft=False):

    """The two builds differ only in the font chunks and their page-0 textures; every record's rectangle lies

    on its page, every char is still there. -> list of problems."""

    _z, o1, f1, e1 = open_level(src); _z2, o2, f2, e2 = open_level(dst)

    bad = []

    if o1 != o2:

        bad.append('member order differs')

    for n in o1:

        if extras and n == e1['.prp']:

            a, b = Prp(f1[n]), Prp(f2[n])

            d = [i for i, (x, y) in enumerate(zip(a.tokens, b.tokens)) if x != y]

            if len(a.tokens) != len(b.tokens) or a.keys != b.keys or len(d) > 2 * len(EXTRAS):

                bad.append('.prp: more than the HUD picture slots changed (%d tokens)' % len(d))

            continue

        if n not in (e1['.prm'], e1['.TEX']) and f1[n] != f2.get(n):

            bad.append('member %s changed' % n)

    p1, p2 = G.read(f1[e1['.prm']], 'dd'), G.read(f2[e2['.prm']], 'dd')

    if len(p1.chunks) != len(p2.chunks) or p1.refs != p2.refs:

        bad.append('chunk table differs')

    fonts = fonts_of(f1, e1)

    changed = [i for i in range(1, len(p1.chunks)) if p1.chunks[i] != p2.chunks[i]]

    if set(changed) - set(fonts.values()):

        bad.append('chunks other than fonts changed: %s' % sorted(set(changed) - set(fonts.values()))[:5])

    t1, t2 = T.read_tex(f1[e1['.TEX']]), T.read_tex(f2[e2['.TEX']])

    new_ids = set(range(EXTRA_ID, EXTRA_ID + len(EXTRAS))) if extras else set()

    if set(t1.tex) | new_ids != set(t2.tex):

        bad.append('texture ids differ')

    if extras:                                           # the way the game looks them up (re/hud_extras.md): 0x5e3810 walks the

        have = hud_slots(f2, e2)                         # 200 ids at osd+0xd68; a non-zero id is loaded as a texture

        for k, (slot, kind, w, h) in enumerate(EXTRAS):  # (id, flags|0x10, type 5, 1) and the handle goes to osd+0x3ec+12*slot

            tid = EXTRA_ID + k

            if have.get(slot) != tid:

                bad.append('extra %s: slot %d holds %s in the written .prp, not %d (the game would load nothing)' % (kind, slot, have.get(slot), tid))

            t = t2.tex.get(tid)

            if t is None:

                bad.append('extra %s: texture %d is not in the .TEX' % (kind, tid)); continue

            if tid >= 4096:

                bad.append('extra %s: texture id %d is over the 4096 limit' % (kind, tid))

            sz, f1_, f2_, hid, th_, tw_, mips = struct.unpack_from('<I4s4sIHHI', t.entry, 0)

            if hid != tid or (tw_, th_) != (w, h) or sz != len(t.entry):

                bad.append('extra %s: the .TEX record header (id %d, %dx%d, size %d) does not match' % (kind, hid, tw_, th_, sz))

    allowed = set(tex_page(t1, max(r[1] for r in parse(p1.chunks[ci])[1]))[0] for ci in fonts.values())

    if pictures:

        allowed |= set(tid for slot, tid in hud_slots(f1, e1).items() if slot in PLATE_SLOTS)

    other = [i for i in t1.tex if i in t2.tex and t1.tex[i].entry != t2.tex[i].entry and i not in allowed and i not in new_ids]

    if other:

        bad.append('textures other than the fonts / plates changed: %s' % other[:5])

    for name, ci in fonts.items():

        h1, r1, tl1 = parse(p1.chunks[ci]); h2, r2, tl2 = parse(p2.chunks[ci])

        if h1[:5] != h2[:5] or h1[6:9] != h2[6:9] or tl1 != tl2 or len(r1) != len(r2):      # line height [5] and ascent offset [9] are the baked ones

            bad.append('%s: header / tail / count changed' % name)

        if draft and name in DRAFT_SPECS:                  # baked with baseline=True: ascent offset = -cap, line height = round(1.3 cap) + 2 (the hook's Cap0..3 rely on it)

            cap_ = -h2[9]

            if not (4 <= cap_ <= 60) or h2[5] != int(round(cap_ * 1.3)) + 2:

                bad.append('%s: header[9] %d / line height %d are not the draft bake:  (-cap, round(1.3 cap) + 2)' % (name, h2[9], h2[5]))

        for a, b in zip(r1, r2):

            if a[:2] != b[:2] or a[11:] != b[11:]:

                bad.append('%s: record for char %d changed identity' % (name, a[0])); break

            if b[1] < 4096:                              # page 1 (its rectangles are in 512-space: kept as stock)

                if a != b:

                    bad.append('%s: page-1 record for char %d changed' % (name, a[0])); break

                continue

            _tid, tw, th, _px, _e = tex_page(t2, b[1])

            if not (0 <= b[2] <= b[4] <= tw and 0 <= b[3] <= b[5] <= th and b[4] - b[2] == b[6] and b[5] - b[3] == b[7]):

                bad.append('%s: char %d rectangle %s off its page' % (name, b[0], b[2:8])); break

    return bad





# ------------------------------------------------------------------ plates (pictures)

PLATE_RGB = (22, 22, 26)          # the plate fill

PLATE_A = 0xb4                    # its alpha (0xb4 = 70 %)

EDGE_RGB = (255, 255, 255)        # 1 px top highlight

AMBER = (224, 150, 46)

PLATE_SLOTS = {107: 'plate', 108: 'plate', 169: 'meter', 161: 'bar0', 162: 'bar1', 163: 'bar2', 164: 'bar3',

               109: 'tick', 193: 'tick', 0: 'border', 1: 'border_red'}





CHALK = (243, 240, 234)           # the kit's brush white

CORAL = (240, 71, 90)             # the kit's red





def _plate_pixels(kind, w, h):

    """ABGR pixels of a HUD picture of w x h in the owner's brush-kit look (2026-10-11: solid chalk strokes with a

    hand-cut edge and small breaks, thin outlined bars with a painted fill), stored R G B A (run F1_DM03)."""

    import random

    rnd = random.Random(w * 1009 + h * 17 + sum(map(ord, kind)))

    px = bytearray(4 * w * h)



    def put(x, y, rgb, a):

        if 0 <= x < w and 0 <= y < h:

            i = 4 * (y * w + x); px[i], px[i + 1], px[i + 2], px[i + 3] = rgb[0], rgb[1], rgb[2], a



    def stroke(x0, y0, x1, y1, rgb, a=0xff, breaks=True):

        """A solid painted bar: each row's ends and each column's top / bottom wander by a pixel or two; a few

        one-pixel vertical breaks and chips in the paint."""

        top = [y0 + rnd.choice((0, 0, 0, 1)) for _ in range(x1 - x0)]

        bot = [y1 - rnd.choice((0, 0, 0, 1)) for _ in range(x1 - x0)]

        gaps = set()

        if breaks:

            for _ in range(max(1, (x1 - x0) // 38)):

                gaps.add(rnd.randrange(x0 + 2, max(x0 + 3, x1 - 2)))

        for y in range(y0, y1):

            lo = x0 + rnd.choice((0, 0, 1, 2)); hi = x1 - rnd.choice((0, 0, 1, 2))

            for x in range(lo, hi):

                if x in gaps and rnd.random() < .8:

                    continue

                if top[x - x0] <= y < bot[x - x0]:

                    put(x, y, rgb, a if rnd.random() > .012 else a // 4)



    def frame(x0, y0, x1, y1, rgb=CHALK, a=0xe6):

        for x in range(x0, x1):

            put(x, y0, rgb, a); put(x, y1 - 1, rgb, a)

        for y in range(y0, y1):

            put(x0, y, rgb, a); put(x1 - 1, y, rgb, a)



    if kind == 'plate':                                    # behind the stock weapon panel: a torn dark smear, no box

        for y in range(8, h - 8):

            lo = 8 + rnd.choice((0, 1, 2, 3, 4)); hi = w - 8 - rnd.choice((0, 1, 2, 3, 4))

            for x in range(lo, hi):

                put(x, y, (8, 8, 9), 0x8c)

        frame(33, h // 2 - 3, w - 34, h // 2 + 12)         # the thin outlined bar the magazine ticks are painted into

    elif kind == 'meter':

        frame(4, 16, w - 4, h - 16)

    elif kind.startswith('bar'):                           # tracker bar: outlined bar, painted fill at 4/4 .. 1/4

        k = int(kind[3])

        frame(4, 20, w - 4, h - 20)

        stroke(4, 18, 4 + (w - 8) * (4 - k) // 4, h - 18, CHALK)

    elif kind == 'tick':                                   # one magazine tick: the code scales the whole cell to one thin bar

        for y in range(h):

            for x in range(w):

                put(x, y, CHALK, 0xff if rnd.random() > .03 else 0x60)

    elif kind.startswith('border'):

        frame(0, 0, w, h, CORAL if kind == 'border_red' else CHALK, 0xff)

    return px





def build_pictures(tex, slots_ids, log=print):

    """slots_ids: {slot: texture id} -> {id: (new entry, kind, w, h, pixels)} for the slots in PLATE_SLOTS. The

    record keeps the stock words except fourcc (ABGR), mips (1), the animated flag, size and pixels."""

    out = {}

    for slot, tid in sorted(slots_ids.items()):

        kind = PLATE_SLOTS.get(slot)

        if kind is None or tid not in tex.tex or tid in out:

            continue

        e = tex.tex[tid].entry

        size, f1, _f2, _id, th, tw, mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', e, 0)

        q = e.index(b'\0', 36) + 1

        px = _plate_pixels(kind, tw, th)

        body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', _id, th, tw, 1, fl & ~0x100, sc, x20) + e[36:q] + struct.pack('<I', len(px)) + bytes(px)

        out[tid] = (struct.pack('<I', len(body) + 4) + body, kind, tw, th, px)

        log('picture slot %3d id %4d %-10s %dx%d %s -> ABGR' % (slot, tid, kind, tw, th, f1[::-1].decode('latin1')))

    return out





# ------------------------------------------------------------------ extra pictures for the hook's HUD (klhud.c klu_pic)

# The owner's draft (2026-10-11) needs shapes no stock HUD picture has. They go into picture slots every stock FA

# level leaves 0 (re/hud_data.md 2: 111..118), as NEW textures (ids from EXTRA_ID up; the .TEX holds 4096). All are

# WHITE with the shape in the alpha channel, so klu_pic's record colour paints them (chalk, coral, orange, green, black).

# NOT LOADED IN THE GAME: that the loader makes a sprite for a slot the stock list has 0 in is ASSUMED (it does for

# every non-zero id); klhud.c's [HUD] PicTest is the check.

EXTRA_ID = 3000

EXTRAS = (            # slot, name, width, height

    (111, 'stroke', 256, 32),     # a solid painted bar, hand-cut edge, small breaks: row blocks, pop-up bars, rules

    (112, 'dry', 256, 32),        # the same, streaked: strike-through, bar tails

    (113, 'dab', 32, 32),         # one brush dab: rings are drawn as dabs on a circle and empty dab by dab

    (114, 'disc', 128, 128),      # a filled disc with a rough rim: dial backs

    (115, 'ring', 128, 128),      # a thin broken ring: the loot ring's inner circle, dial rims

    (116, 'dollar', 128, 128),    # '$' dragged sideways with streaks rubbed out: the loot ring

    (117, 'frame', 256, 32),      # a thin outlined bar: magazine, loot taken, vehicle bars (fill = 'stroke' over it)

    (118, 'box', 256, 64),        # an outlined box: the traitor pop-up

)





def _extra_pixels(kind, w, h):

    import random, math

    rnd = random.Random(w * 7 + h * 131 + sum(map(ord, kind)) * 17)

    a = bytearray(w * h)                                   # alpha only; colour is white



    def put(x, y, v):

        if 0 <= x < w and 0 <= y < h:

            a[y * w + x] = max(a[y * w + x], v)



    def bar(x0, y0, x1, y1, streak):

        top = [y0 + rnd.choice((0, 0, 0, 1, 1, 2)) for _ in range(w)]

        bot = [y1 - rnd.choice((0, 0, 0, 1, 1, 2)) for _ in range(w)]

        gaps = {rnd.randrange(x0 + 3, x1 - 3) for _ in range((x1 - x0) // (20 if streak else 42))}

        rows = {rnd.randrange(y0 + 2, y1 - 2) for _ in range((y1 - y0) // 3)} if streak else set()

        for y in range(y0, y1):

            lo = x0 + rnd.choice((0, 0, 1, 2, 3)); hi = x1 - rnd.choice((0, 0, 1, 2, 3))

            for x in range(lo, hi):

                if x in gaps and rnd.random() < .85:

                    continue

                if y in rows and rnd.random() < .7 and (x // 23 + y) % 3:

                    continue

                if top[x] <= y < bot[x]:

                    put(x, y, 255 if rnd.random() > .015 else 70)



    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0

    if kind == 'stroke':

        bar(2, 3, w - 2, h - 3, False)

    elif kind == 'dry':

        bar(2, 6, w - 2, h - 6, True)

    elif kind == 'frame':

        for x in range(2, w - 2):

            for t in (0, 1):

                if rnd.random() > .03: put(x, 6 + t, 235)

                if rnd.random() > .03: put(x, h - 8 + t, 235)

        for y in range(6, h - 6):

            for t in (0, 1):

                put(2 + t, y, 235); put(w - 4 + t, y, 235)

    elif kind == 'box':

        for x in range(3, w - 3):

            for t in (0, 1, 2):

                if rnd.random() > .04: put(x, 3 + t, 240)

                if rnd.random() > .04: put(x, h - 6 + t, 240)

        for y in range(3, h - 3):

            for t in (0, 1, 2):

                put(3 + t, y, 240); put(w - 6 + t, y, 240)

    elif kind == 'dab':

        for y in range(h):

            for x in range(w):

                d = math.hypot((x - cx) / 1.0, (y - cy) / 1.25)

                r = 9.5 + .55 * math.sin(math.atan2(y - cy, x - cx) * 2 + 1.3)

                if d < r:

                    put(x, y, 255 if rnd.random() > .03 else 90)

                elif d < r + 1:

                    put(x, y, int(255 * (r + 1 - d)))

    elif kind in ('disc', 'ring'):

        R = w / 2.0 - 4

        for y in range(h):

            for x in range(w):

                ang = math.atan2(y - cy, x - cx)

                d = math.hypot(x - cx, y - cy)

                rr = R + .45 * math.sin(ang * 7 + .4) + .3 * math.sin(ang * 17)

                if kind == 'disc':

                    if d < rr: put(x, y, 255)

                    elif d < rr + 1: put(x, y, int(255 * (rr + 1 - d)))

                else:

                    if rr - 3.2 < d < rr and (int((ang + math.pi) * 9) % 11 or rnd.random() < .35) and rnd.random() > .04:

                        put(x, y, 255)

    elif kind == 'dollar':

        gd = _Gdi().font('Impact', 96, 400)

        _adv, _xo, _yo, gw, gh, ink = gd.glyph('$')

        gd.close()

        ox, oy = int(cx - gw / 2), int(cy - gh / 2)

        rub = {rnd.randrange(0, h) for _ in range(h // 4)}

        for yy, row in enumerate(ink):

            y = oy + yy

            for xx, v in enumerate(row):

                if not v:

                    continue

                if y in rub and (xx // 9 + yy) % 4 != 0:

                    v = v // 6

                if rnd.random() < .05:

                    v = v // 3

                for dx in range(0, 7):                     # dragged to the right, fading

                    put(ox + xx + dx, y, v if dx == 0 else int(v * .32 * (1 - dx / 7.0)))

    px = bytearray(b'\xff\xff\xff\0' * (w * h))

    px[3::4] = a

    return px





def add_extras(files, ext, log=print, png=None):

    """New textures + their ids in the spare slots of every ZOnScreenDisplay2's 200-entry list. Edits files in place.

    -> {slot: texture id}. A level that already has them (ids at EXTRA_ID..) gets the pictures re-made in place."""

    tex = T.read_tex(files[ext['.TEX']])

    proto = None

    for tid in sorted(tex.tex):                            # header words of a small stock HUD picture

        n = tex.tex[tid].name

        if 'UI_KL2_Small_Icons_01' in n:

            proto = tex.tex[tid].entry; break

    if proto is None:

        raise ValueError('no stock HUD icon to model the new records on')

    _size, _f1, _f2, _id, _th, _tw, _mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', proto, 0)

    out = {}

    for k, (slot, kind, w, h) in enumerate(EXTRAS):

        tid = EXTRA_ID + k

        if tid in tex.tex and 'KLMerge' not in tex.tex[tid].name:

            raise ValueError('texture id %d is taken by %s' % (tid, tex.tex[tid].name))

        px = _extra_pixels(kind, w, h)

        name = ('tex:UserInterface/KLMerge_HUD_01#%s' % kind).encode('latin1') + b'\0'

        body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', tid, h, w, 1, fl & ~0x100, sc, 0) + name + struct.pack('<I', len(px)) + bytes(px)

        tex.tex[tid] = T.Texture(struct.pack('<I', len(body) + 4) + body)

        out[slot] = tid

        if png:

            os.makedirs(png, exist_ok=True)

            _png_rgba(os.path.join(png, 'extra_%d_%s.png' % (slot, kind)), w, h, px)

    files[ext['.TEX']] = T.write_tex(tex)

    # the 200-entry lists in the .prp: an array-begin token of 200 followed by 200 integer tokens. THE EDIT MUST GO INTO THE

    # NODES' prop lists: Prp.serialize() rebuilds the stream from nodes (Prp.tokens is a read-only flat copy of them; the

    # first version of this function edited it, wrote nothing, and 'extras: ... 2 HUD list(s) updated' lied - slots 111..118

    # stayed 0 in the game, so the hook found no extra picture; re/hud_extras.md).

    p = Prp(files[ext['.prp']])

    done = 0

    for node in p.nodes():

        toks = node['props']

        for i, (op, pl) in enumerate(toks):

            if op == 0x01 and len(pl) == 4 and struct.unpack('<I', pl)[0] == 200 and i + 200 < len(toks):

                run = toks[i + 1:i + 201]

                if any(t[0] not in (0x04, 0x09) for t in run):

                    continue

                vals = [struct.unpack('<I', t[1])[0] for t in run]

                if sum(1 for v in vals if v) < 100 or max(vals) >= 4096:

                    continue                                   # not a HUD picture list

                for slot, tid in out.items():

                    if vals[slot] not in (0, tid):

                        raise ValueError('HUD picture slot %d holds %d' % (slot, vals[slot]))

                    toks[i + 1 + slot] = (run[slot][0], struct.pack('<I', tid))

                done += 1

    if not done:

        raise ValueError('no 200-entry HUD picture list found in the .prp')

    files[ext['.prp']] = p.serialize()

    log('extras: %d pictures in slots %s (texture ids %d..%d), %d HUD list(s) updated' % (len(out), ', '.join(str(k) for k in sorted(out)), EXTRA_ID, EXTRA_ID + len(EXTRAS) - 1, done))

    return out





def hud_slots(files, ext):

    """{slot: texture id} of the first ZOnScreenDisplay2's 200-entry list."""

    import kl_prpjoin as J, kl_rtp

    raw = kl_gms.unpack(files[ext['.gms']]); buf = files[ext['.buf']]

    names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]

    for decl, tid, _prio in kl_gms.entities(raw):

        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]

        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)

    sc = J.Scene(Prp(files[ext['.prp']]), names, tids, 'dd')

    for k in range(1, len(sc.nodes)):

        if sc.cls(k) == 'ZOnScreenDisplay2':

            for _h, lab, u in J.fields(sc, k):

                if lab == 'ZOnScreenDisplay2[7]':

                    v = [struct.unpack('<I', t[1])[0] for t in u if t[0] in (0x04, 0x09)]

                    ids = v[1:] if v[0] == len(v) - 1 else v

                    return {i: t for i, t in enumerate(ids) if t}

    return {}





def _png_rgba(path, w, h, rgba):

    raw = b''.join(b'\0' + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))



    def ch(t, d):

        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))





def apply_pictures(src, dst, png=None, log=print, _files=None):

    """A build -> folder `dst` with the plate pictures restyled (fonts untouched). png: also write PNGs there.

    _files: (zp, order, files, ext) of a build already open -> edits files in place and returns the new entries."""

    zp, order, files, ext = open_level(src) if _files is None else _files

    tex = T.read_tex(files[ext['.TEX']])

    new = build_pictures(tex, hud_slots(files, ext), log)

    for tid, (e, kind, tw, th, px) in new.items():

        t = tex.tex[tid]

        tex.tex[tid] = T.Texture(e, t.faces, t.cube, t.frames, t.group)

        if png:

            os.makedirs(png, exist_ok=True)

            rgba = bytearray(px)

            _png_rgba(os.path.join(png, '%d_%s.png' % (tid, kind)), tw, th, rgba)

    files[ext['.TEX']] = T.write_tex(tex)

    if _files is not None:

        return new

    os.makedirs(dst, exist_ok=True)

    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):

        raise ValueError("the output folder is the build's own")

    import kl_graft

    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])

    for f in os.listdir(os.path.dirname(zp)):

        q = os.path.join(os.path.dirname(zp), f)

        if os.path.isfile(q) and not os.path.samefile(q, zp):

            shutil.copyfile(q, os.path.join(dst, f))

    log('wrote %s (%d pictures)' % (out, len(new)))

    return out





# ------------------------------------------------------------------ preview

def _png(path, w, h, rgb):

    raw = b''.join(b'\0' + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def ch(t, d):

        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))





def preview(src, font, text, out, log=print):

    """Draw `text` with a level's font the way the records say (pen at x += advance, ink at pen + offsets,

    baseline at 2 * size), 3x enlarged, into out.png."""

    _zp, _o, files, ext = open_level(src)

    fonts = fonts_of(files, ext)

    p = G.read(files[ext['.prm']], 'dd'); tex = T.read_tex(files[ext['.TEX']])

    h, recs, _tail = parse(p.chunks[fonts[font]])

    by = {r[0]: r for r in recs}

    pages = {}

    W_, H_ = 24 + sum(by[ord(c)][10] for c in text if ord(c) in by) + 24, 4 * h[2]

    img = bytearray(bytes((28, 30, 34)) * (W_ * H_))

    pen, base = 12, int(2.2 * h[2])

    for c in text:

        r = by.get(ord(c))

        if r is None:

            continue

        if r[1] not in pages:

            pages[r[1]] = tex_page(tex, r[1])

        _tid, tw, th, px, _e = pages[r[1]]

        tint = r[1] >= 4096

        sc = 1 if tint else tw / PAGE                     # page-1 rectangles are in 512-space

        for yy in range(r[7]):

            for xx in range(r[6]):

                sx, sy = int((r[2] + xx) * sc), int((r[3] + yy) * sc)

                i = 4 * (sy * tw + sx); a = px[i + 3] / 255

                X, Y = pen + r[8] + xx, base + r[9] + yy

                if 0 <= X < W_ and 0 <= Y < H_:

                    q = 3 * (Y * W_ + X)

                    col = (236, 232, 223) if tint else (px[i], px[i + 1], px[i + 2])

                    for k in range(3):

                        img[q + k] = int(col[k] * a + img[q + k] * (1 - a))

        pen += r[10]

    # 3x

    S = 3

    big = bytearray(W_ * S * H_ * S * 3)

    for y in range(H_ * S):

        row = img[3 * (y // S) * W_: 3 * (y // S + 1) * W_]

        big[3 * y * W_ * S: 3 * (y + 1) * W_ * S] = b''.join(bytes(row[3 * (x // S): 3 * (x // S) + 3]) for x in range(W_ * S))

    _png(out, W_ * S, H_ * S, big)

    log('wrote %s (%dx%d, font %s %d px)' % (out, W_ * S, H_ * S, font, h[2]))





def preview_hud(src, out, log=print):

    """A quick offline look (2026-10-11): the crew list, round line, money box and weapon-dial texts drawn with a baked level's own

    atlases at the HOOK'S layout (klhud.c with [HUD] Draft=1 Fonts=1: crew 33, 38, 211 wide, 30 px rows, block 28 high from y - 5; money box

    right edge 1247; weapon dial middle 1177, 598) on a dark 1280 x 720 background, 1:1 pixels. The pen's baseline lies at y - header[9]

    (the game's rule, seen live), exactly what the hook relies on. Roles: names = H2, big = H1, labels = DebugText, small = H3.

    Pictures other than the own row's block, the strike and three skull dots are NOT drawn."""

    _zp, _o, files, ext = open_level(src)

    fonts = fonts_of(files, ext)

    p = G.read(files[ext['.prm']], 'dd'); tex = T.read_tex(files[ext['.TEX']])

    W_, H_ = 1280, 720

    img = bytearray(W_ * H_ * 3)

    for y in range(H_):

        c = int(36 - 22 * y / H_)

        img[3 * y * W_: 3 * (y + 1) * W_] = bytes((c, c + 1, c + 3)) * W_

    def rect(x0, y0, w, h, col, a=1.0):

        for y in range(max(0, int(y0)), min(H_, int(y0 + h))):

            for x in range(max(0, int(x0)), min(W_, int(x0 + w))):

                q = 3 * (y * W_ + x)

                for k in range(3):

                    img[q + k] = int(col[k] * a + img[q + k] * (1 - a))

    cache = {}

    def font(name):

        if name not in cache:

            h, recs, _t = parse(p.chunks[fonts[name]])

            pg = {}

            for r in recs:

                if r[1] not in pg: pg[r[1]] = tex_page(tex, r[1])

            cache[name] = (h, {r[0]: r for r in recs}, pg)

        return cache[name]

    def width(name, text):

        h, by, _pg = font(name); return sum(by[ord(c)][10] for c in text if ord(c) in by)

    def text(name, s, x, ytop, col, align='l', centre=False):

        """ytop = the y given to Draw. align l / r / c."""

        h, by, pg = font(name)

        wid = width(name, s)

        pen = x if align == 'l' else x - wid if align == 'r' else x - wid / 2.0

        base = ytop - h[9]

        for ch in s:

            r = by.get(ord(ch))

            if r is None: continue

            _tid, tw, th, px, _e = pg[r[1]]

            for yy in range(r[7]):

                for xx in range(r[6]):

                    i = 4 * ((r[3] + yy) * tw + r[2] + xx); a = px[i + 3] / 255.0

                    X, Y = int(pen + r[8] + xx), int(base + r[9] + yy)

                    if a and 0 <= X < W_ and 0 <= Y < H_:

                        q = 3 * (Y * W_ + X)

                        for k in range(3):

                            img[q + k] = int(col[k] * a + img[q + k] * (1 - a))

            pen += r[10]

    CAP = {n: -font(n)[0][9] for n in ('H1', 'H2', 'H3', 'DebugText')}      # header[9] = -cap (the hook's Cap0..3)

    LAB, SM = 'DebugText', 'H3'                                              # labels = DebugText (+0xd5c), small figures = H3 (+0xd58)

    TRK = 3                                                                  # the hook adds the label font's tracking back for right / centre alignment

    import math

    def cen(c, name): return math.floor(c - CAP[name] / 2.0 + .5)

    def leg(y, name): return y + 13 - CAP[name]

    CHALKc, CORALc, GREEN, GREENHI, INK, ORANGE, DEAD = (243, 240, 234), (240, 71, 90), (79, 143, 73), (99, 166, 91), (12, 12, 13), (232, 131, 31), (140, 49, 56)

    # THE QUIET ROUND (klhud.c KLU_D_*; before -> after): row pitch 30 -> 21, block 28 -> 19, name inset 8 -> 6, rule 5 -> 3 high, strike 4 -> 2,

    # money lines +0 / +40 / +64 -> +0 / +34 / +52, bar 8 -> 6 high at +26 -> +22, pop-up bar 47.7 -> 38 high, rings and the loot ring a fifth smaller.

    ROW, YOFF, BUP, BH, PADX = 21, 28, 4, 19, 6

    def disc(cx_, cy_, r, col, a=1.0):

        for y in range(int(cy_ - r) - 1, int(cy_ + r) + 2):

            for x in range(int(cx_ - r) - 1, int(cx_ + r) + 2):

                d = ((x + .5 - cx_) ** 2 + (y + .5 - cy_) ** 2) ** .5

                if d <= r and 0 <= x < W_ and 0 <= y < H_:

                    q = 3 * (y * W_ + x)

                    for k in range(3): img[q + k] = int(col[k] * a + img[q + k] * (1 - a))

    def ring(cx_, cy_, r, n, left, dw, dh, col):

        """the dabs of the part that is LEFT (the empty part begins at the top, clockwise); a dab's ink is 0.59 x 0.74 of its picture"""

        first = int((1.0 - left) * n + .5)

        for k in range(first, n):

            a = 2 * math.pi * k / n

            rect(cx_ + r * math.sin(a) - dw * .3, cy_ - r * math.cos(a) - dh * .37, dw * .59, dh * .74, col)

    def frame(x0, y0, w, h, col):

        rect(x0, y0, w, 1, col); rect(x0, y0 + h - 1, w, 1, col); rect(x0, y0, 1, h, col); rect(x0 + w - 1, y0, 1, h, col)

    cx, cy, cw = 33, 38, 211

    text(LAB, 'DEAD MEN', cx, leg(cy, LAB), CORALc); text(SM, '6 / 8', cx + cw, leg(cy, SM), CHALKc, 'r')

    rect(cx, cy + 17.5, cw, 3, CHALKc)                                        # the painted rule

    rows = [('R6KXO', '$550K', 'you'), ('TOMMY', '$100K', ''), ('PIERRE', '$0', 'traitor'), ('LIAM', '$20K', ''), ('JEAN', '$0', ''), ('ELWOOD', '$0', 'dead'), ('BUD', '$0', ''), ('MITCHEL', '$0', 'dead')]

    for i, (nm, cash, kind) in enumerate(rows):

        y = cy + YOFF + ROW * i; rc = y + BH * .5 - BUP

        if kind in ('you', 'traitor'): rect(cx - 4, y - BUP, cw + 8, BH, CHALKc if kind == 'you' else ORANGE)

        col = INK if kind in ('you', 'traitor') else DEAD if kind == 'dead' else CHALKc

        text('H2', nm + ('  TRAITOR' if kind == 'traitor' else ''), cx + PADX, cen(rc, 'H2'), col)

        text(SM, cash, cx + cw - PADX, cen(rc, SM), (31, 74, 29) if kind == 'you' else INK if kind == 'traitor' else (95, 42, 47) if kind == 'dead' else GREENHI, 'r')

        if kind == 'dead': rect(cx + 2, rc - 1, width('H2', nm) + 8, 2, DEAD)

        if kind == 'you':

            sx = cx + 12 + width('H2', nm) - 6 + 6          # KLUV_SKULL_LEAD 12 + the name's width

            for k in range(3): rect(sx + 12.5 * k, rc - 5.5, 11, 11, INK, 1.0 if k < 2 else .3)

    # round watch + escape dial (klu_dials): rings of dabs

    wcx, wcy = 1212, 66

    disc(wcx, wcy, 34.5, (8, 8, 9), .61); ring(wcx, wcy, 29, 40, .6, 11, 9, CHALKc)

    a_ = 2 * math.pi * .4

    for i in range(1, 6): rect(wcx + 4.4 * i * math.sin(a_) - 2.5, wcy - 4.4 * i * math.cos(a_) - 2.5, 5, 5, CHALKc)

    disc(wcx, wcy, 4, CHALKc)

    ex, ey = wcx - 75, wcy + 5

    disc(ex, ey, 27.5, (8, 8, 9), .61); ring(ex, ey, 23, 32, .65, 10, 8.5, ORANGE); rect(ex - 9, ey - 5, 18, 10, CHALKc)         # a car, as a block

    mx = 1247

    text(LAB, 'ROUND 1 OF 10', mx + TRK, leg(108, LAB), CHALKc, 'r')

    my = 36 + 99

    bx, by_ = mx - 211, my + 22

    frame(bx, by_, 211, 6, CHALKc); rect(bx - 2, by_ - 2, 211 * .16, 10, CHALKc)         # the framed bar under TOTAL

    for k, (lab, val) in enumerate((('TOTAL', '$550,000'), ('LOOT', '$550,000'), ('REWARDS', '$0'))):

        y = my + (0 if k == 0 else 34 + 18 * (k - 1))

        text(LAB, lab, mx - 211, leg(y, LAB), CORALc)

        f = 'H1' if k == 0 else 'H2'

        text(f, val, mx, leg(y, f), GREENHI if k == 0 else GREEN, 'r')

    wx, wy = 1177, 598

    disc(wx, wy, 70.5, (8, 8, 9), .61); ring(wx, wy, 62, 64, .7, 12, 10, CHALKc)

    rect(wx - 43, wy + 2, 87, 2, CHALKc, .29)                                 # the divider

    text('H2', '30', wx - 7, leg(wy - 36, 'H2'), CHALKc, 'r'); text(SM, '150', wx - 5, leg(wy + 18, SM), (169, 165, 157), 'r')

    text(LAB, 'ZASTAVA M85 . 270', wx + TRK / 2.0, leg(wy + 88, LAB), CORALc, 'c')

    # the loot ring (a third of it filled) and the pop-up bar + the traitor box

    lx, ly = 640, 470

    disc(lx, ly, 17, (15, 16, 15)); ring(lx, ly, 22, 32, 1.0, 8, 7, CHALKc) if False else None

    for k in range(11):

        a = 2 * math.pi * k / 32; rect(lx + 22 * math.sin(a) - 2.4, ly - 22 * math.cos(a) - 2.6, 4.7, 5.2, CHALKc)

    text(SM, '$', lx - 3, cen(ly, SM), GREENHI)

    msg = 'YOU BAGGED $50,000'; bw = width('H1', msg) + 48; bh = 38; byc = 523

    rect(640 - bw / 2, byc - bh / 2, bw, bh, CHALKc); text('H1', msg, 640 - width('H1', msg) / 2, cen(byc, 'H1'), INK)

    msg = 'YOU ARE A TRAITOR'; bw = width('H1', msg) + 48; byc = 600

    rect(640 - bw / 2, byc - bh / 2, bw, bh, (12, 12, 13), .9); frame(640 - bw / 2 - 5, byc - bh / 2 - 5, bw + 10, bh + 10, ORANGE)

    frame(640 - bw / 2 - 4, byc - bh / 2 - 4, bw + 8, bh + 8, ORANGE); text('H1', msg, 640 - width('H1', msg) / 2, cen(byc, 'H1'), ORANGE)

    _png(out, W_, H_, img)

    log('wrote %s (1280x720, 1:1)' % out)





def dump(src, log=print):

    _zp, _o, files, ext = open_level(src)

    fonts = fonts_of(files, ext)

    p = G.read(files[ext['.prm']], 'dd'); tex = T.read_tex(files[ext['.TEX']])

    for name, ci in sorted(fonts.items(), key=lambda kv: kv[1]):

        h, recs, tail = parse(p.chunks[ci])

        pages = sorted(set(r[1] for r in recs))

        names = [tex.tex[r & 0xfff].name for r in pages]

        log('%-10s chunk %-6d size %2d line %2d glyphs %3d tail %4d pages %s' % (name, ci, h[2], h[5], len(recs), len(tail), names))





def main():

    a = sys.argv[1:]

    if not a:

        print(__doc__); return

    cmd = a[0]

    if cmd == 'dump':

        dump(a[1])

    elif cmd == 'preview':

        preview(a[1], a[2], a[3], a[4])

    elif cmd == 'preview-hud':

        preview_hud(a[1], a[2])

    elif cmd == 'pictures':

        png = a[a.index('--png') + 1] if '--png' in a else None

        apply_pictures(a[1], a[2], png)

    elif cmd == 'all':

        kw = {}

        rest = a[3:]

        while rest:

            k = rest.pop(0)

            if k == '--face': kw['face'] = rest.pop(0)

            elif k == '--weight': kw['weight'] = int(rest.pop(0))

            elif k == '--scale': kw['scale'] = float(rest.pop(0))

            elif k == '--caps': kw['caps'] = True

            elif k == '--chip': kw['chip'] = float(rest.pop(0))

            elif k == '--look' and rest.pop(0) == 'deadmen':      # the owner's look of 2026-10-11

                _g = _Gdi(); _own = _g.has('Anton') and _g.has('Montserrat')

                print('faces:', 'the draft own faces (Anton, Montserrat from <work>/fonts)' if _own else 'stand-ins (Impact, Segoe UI Black): put Anton-Regular.ttf and Montserrat into <work>/fonts for the draft own faces')

                kw.update(face='Anton' if _own else 'Impact', weight=400, scale=.9, caps=True, chip=.6, extras=True, specs=DRAFT_SPECS_ANTON if _own else DRAFT_SPECS)

            else: raise SystemExit('unknown option ' + k)

        _out, _reps = apply(a[1], a[2], pictures=True, **kw)

        if kw.get('specs'):

            print('hook roles (osd+0xd54 names, +0xd50 big, +0xd5c labels, +0xd58 small): [HUD] Cap0=%s Cap1=%s Cap2=%s Cap3=%s (klhud.c default)' % tuple(_reps[n]['cap'] for n in ('H2', 'H1', 'DebugText', 'H3')))

        bad = check(a[1], a[2], pictures=True, extras=kw.get('extras', False), draft=bool(kw.get('specs')))

        print('check:', 'PASS' if not bad else 'FAIL ' + '; '.join(bad))

    elif cmd == 'extras':                                   # only the extra pictures, as PNGs to look at

        zp, order, files, ext = open_level(a[1])

        print(add_extras(files, ext, png=a[2]))

    elif cmd == 'fonts':

        kw = {}

        rest = a[3:]

        while rest:

            k = rest.pop(0)

            if k == '--face': kw['face'] = rest.pop(0)

            elif k == '--weight': kw['weight'] = int(rest.pop(0))

            elif k == '--scale': kw['scale'] = float(rest.pop(0))

            elif k == '--only': kw['only'] = rest.pop(0).split(',')

            elif k == '--look' and rest.pop(0) == 'deadmen':      # the lettering alone (the menu scene has no HUD pictures)

                kw.update(face='Impact', weight=400, scale=.9, caps=True, chip=.6)

            else: raise SystemExit('unknown option ' + k)

        out, _reps = apply(a[1], a[2], **kw)

        bad = check(a[1], out)

        print('check:', 'PASS' if not bad else 'FAIL ' + '; '.join(bad))

    else:

        raise SystemExit('unknown command ' + cmd)





if __name__ == '__main__':

    main()

