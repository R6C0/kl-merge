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

    python tools/kl_hud.py preview-board <build dir or zip> <out.png> <board_case.txt>...   # the round-over scoreboard's layout (klhook/klsb_test.exe writes the txt files)

    python tools/kl_hud.py fonts <tree>/Overlay/Scenes/kaneandlynch.zip <out dir> --look deadmen

                                                                  # THE MENUS' lettering: the front-end scene has its own

                                                                  # eight fonts (same format); only they and their pages change

    python tools/kl_hud.py pictures <build dir or zip> <out dir> [--png <dir>]        # restyled HUD plates (see PLATES)

    python tools/kl_hud.py all <build dir or zip> <out dir> [font options]            # fonts + pictures

    python tools/kl_hud.py all <build> <out> --look deadmen       # THE OWNER'S LOOK (2026-10-11): Impact capitals (lower

                                                                  # case drawn as capitals), light chipping, brush-kit bars

                                                                  # + the world markers in the watch look (tools/kl_hud_marks.py;

                                                                  # --markers 0: stock) and the shop's gun names in the HUD's

                                                                  # wording (tools/kl_hud_shop.py; --shopnames 0: stock)

    python tools/kl_hud.py markers <baked build or zip> <out dir> [--shopnames 0]   # ONLY those two, on a level baked before

                                                                  # (no font bake again)

    python tools/kl_hud.py all <build> <out_TEST> --look deadmen --test-bake --mark-slots [52,53,127-160]

                                                                  # TEST ONLY (re/hud_killfeed_plan.md K1): every HUD picture (or the

                                                                  # listed slots) stamped with its slot number; needs both flags and an

                                                                  # output folder named ...TEST...; check says FAIL on purpose



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
    if SHOPNAMES:
        import kl_hud_shop
        kl_hud_shop.apply_level(files, log, guns=os.path.join(os.path.dirname(zp), 'KLGuns.ini'))      # Dead Men looks sold under their names
    os.makedirs(dst, exist_ok=True)

    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):

        raise ValueError('the output folder is the build\'s own')

    apply_marks(files, ext, dst, log)                      # nothing unless --test-bake --mark-slots (after the extras: they get numbers too)
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

        if SHOPNAMES and n.lower().endswith('.loc') and f1[n] != f2.get(n):      # the shop's names (kl_hud_shop): only Weapon<row> / Weapon<row>Desc leaves
            import kl_loc as _L, kl_hud_shop as _S
            a_, b_ = dict(_L.leaves(_L.parse(f1[n]))), dict(_L.leaves(_L.parse(f2[n])))
            if a_.keys() != b_.keys() or any(a_[k].raw != b_[k].raw and not k.startswith(_S.KEY) for k in a_):
                bad.append('%s: more than the shop names changed' % n)
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
            else:                                          # the pixels are the bake of the chosen look: a level baked with the other look (or hand-edited) fails here
                q_ = t.entry.index(bytes(1), 36) + 1; n_ = struct.unpack_from('<I', t.entry, q_)[0]
                if t.entry[q_ + 4:q_ + 4 + n_] != _extra_pixels(kind, w, h):
                    bad.append('extra %s (slot %d): the pixels are not the bake of watch look %d (--watch)' % (kind, slot, WATCH))

    allowed = set(tex_page(t1, max(r[1] for r in parse(p1.chunks[ci])[1]))[0] for ci in fonts.values())

    if pictures:

        allowed |= set(tid for slot, tid in hud_slots(f1, e1).items() if slot in picture_slots())

    if MARK_SLOTS is not None:                             # the test bake stamped (some of) the list's pictures

        allowed |= set(tid for slot, tid in hud_slots(f2, e2).items() if not MARK_SLOTS or slot in MARK_SLOTS)

        bad.append('TEST BAKE with slot numbers stamped: not for the owner\'s tab')

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
SHOPNAMES = False                 # the buy-weapons names in the HUD's wording (tools/kl_hud_shop.py): on with --look deadmen, off with --shopnames 0
MARKERS = False                   # the world markers (loot '$', escape car / chopper / cash) in the watch look: tools/kl_hud_marks.py;
                                  # on with --look deadmen, off with --markers 0


def picture_slots():
    """{slot: kind} of the stock pictures the bake restyles"""
    if not MARKERS:
        return PLATE_SLOTS
    import kl_hud_marks as _M
    d = dict(PLATE_SLOTS); d.update(_M.MARKER_SLOTS)
    return d
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
    slots = picture_slots()
    for slot, tid in sorted(slots_ids.items()):
        kind = slots.get(slot)

        if kind is None or tid not in tex.tex or tid in out:

            continue

        e = tex.tex[tid].entry

        size, f1, _f2, _id, th, tw, mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', e, 0)

        q = e.index(b'\0', 36) + 1

        if kind.startswith(('mk_', 'trk_')):               # a world marker (tools/kl_hud_marks.py); the car / chopper borrow a stock small icon
            import kl_hud_marks as _M
            g = _M.GLYPH_SLOTS.get(kind)
            g = _M.decode(tex.tex[slots_ids[g]].entry) if g in slots_ids and slots_ids[g] in tex.tex else None
            if kind in _M.GLYPH_SLOTS and g is None:
                log('picture slot %3d id %4d %s: the stock icon it borrows (slot %d) is missing: kept stock' % (slot, tid, kind, _M.GLYPH_SLOTS[kind]))
                continue
            px = _M.marker_pixels(kind, tw, th, g)
        else:
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

EXTRAS_OLD = (            # slot, name, width, height (watch look 0 = the look of 2026-10-12 morning)

    (111, 'stroke', 256, 32),     # a solid painted bar, hand-cut edge, small breaks: row blocks, pop-up bars, rules

    (112, 'dry', 256, 32),        # the same, streaked: strike-through, bar tails

    (113, 'dab', 32, 32),         # one round brush dab (ink 0.9 of the picture): the moving end of a ring stroke, the watch's hand

    (114, 'disc', 128, 128),      # a filled disc with a rough rim: dial backs

    (115, 'ring', 128, 128),      # a thin UNBROKEN track ring at the arcs' centre-line radius (0.40 of the square; 128 px, 1.5-3 texel line: drawn at most 2.3x smaller, review M2): under a dial's stroke, the loot ring's inner circle

    (116, 'dollar', 128, 128),    # '$' dragged sideways with streaks rubbed out: the loot ring

    (117, 'frame', 256, 32),      # a thin outlined bar: magazine, loot taken, vehicle bars (fill = 'stroke' over it)

    (118, 'box', 256, 64),        # an outlined box: the traitor pop-up

    (123, 'arcA0', 128, 128),     # ring family A (stroke 0.23 of the radius: watch, escape dial, loot ring), slice 0..2 of 3

    (124, 'arcA1', 128, 128),

    (125, 'arcA2', 128, 128),

    (126, 'arcB0', 256, 256),     # family B (0.12: weapon dial)

    (185, 'arcB1', 256, 256),

    (190, 'arcB2', 256, 256),     # slots 123..126, 185, 190: 0 in the two 200-entry lists of every stock level (checked 2026-10-12)

)

# THE WATCH LOOK (2026-10-12, re/hud_hook.md section 14): 112 / 114 / 115 become wear / worn dial / bezel (all 128 x 128, tools/kl_hud_watch.py);
# the others are the same. A level carries ONE of the two sets: kl_hud.py all --look deadmen --watch 0|1 (default 1) and the hook's [HUD] WatchStyle
# must agree. Slot 112's old users (strike-through, bar tails, rules) draw slot 111 thinner under the new look.
WATCH = 1
EXTRAS_NEW = tuple(((112, 'wear', 128, 128) if e[0] == 112 else (114, 'disc', 128, 128) if e[0] == 114 else (115, 'bezel', 128, 128) if e[0] == 115
                   else (117, 'mfill', 256, 32) if e[0] == 117 else e) for e in EXTRAS_OLD)      # 117: the money bar's painted fill (cloud 2026-10-12; the old 'frame' was drawn by nobody)
EXTRAS = EXTRAS_NEW


def set_watch(w):
    """choose the look (1 = the watch look, 0 = the old one) for everything below: EXTRAS, ARC_FAM and the pixels"""
    global WATCH, EXTRAS, ARC_FAM
    WATCH = 1 if w else 0
    EXTRAS = EXTRAS_NEW if WATCH else EXTRAS_OLD
    ARC_FAM = ARC_FAM_NEW if WATCH else ARC_FAM_OLD






# ---- painted rings as arc pictures (2026-10-12; the owner: 'i dont want the circles to have that circle circle')
# A ring that empties was a string of round dabs and read as beads. It is now ONE stroke: a ring is cut into ARC_N slices of
# 360 / ARC_N degrees (clockwise from the top), each baked as a square texture that holds the whole ring's bounding square with
# only that slice painted, so the slices drawn at the ring's square join into a ring. The slice that holds the moving end of
# the stroke is made of tightly overlapping round dabs (picture 113, spacing <= 1.5 px) so its end can stand anywhere.
# Two families (stroke width / centre-line radius): A (watch, escape dial, loot ring) and B (weapon dial). klhud.c klu_arc mirrors
# every number here (ARC_*). Round caps only at 0 degrees (slice 0 start) and 360 degrees (last slice end).
ARC_N = 3
ARC_KR = 0.40                      # centre-line radius / the square's side
ARC_FAM_OLD = {'A': (128, 0.23, 123, 124, 125), 'B': (256, 0.12, 126, 185, 190)}
ARC_FAM_NEW = {'A': (128, 0.13, 123, 124, 125, 0.6), 'B': (256, 0.10, 126, 185, 190, 0.9)}      # the watch look (re/hud_hook.md 14): thinner strokes; side, ratio, slots, overlap in degrees
ARC_FAM = ARC_FAM_NEW      # texture side, stroke / centre-line radius, slots
RING_STROKE = 0.021                # the thin track ring (slot 115), stroke / the square's side


def _arc_pixels(fam, idx):
    import math
    S, ratio = ARC_FAM[fam][:2]
    rc = ARC_KR * S; hw0 = 0.5 * ratio * rc
    a = bytearray(S * S)
    TAU = 2 * math.pi
    th0, th1 = TAU * idx / ARC_N, TAU * (idx + 1) / ARC_N
    ovl = math.radians(ARC_FAM[fam][5] if len(ARC_FAM[fam]) > 5 else 0.7)
    hs = (th1 - th0) / 2 + (0 if idx == 0 else ovl) / 2; he = (th1 - th0) / 2 + (0 if idx == ARC_N - 1 else ovl) / 2
    # the stroke's wobble: a function of the GLOBAL angle so that neighbouring slices meet exactly; subtle (about 4 % of the width)
    def hwo(t, ph):
        return hw0 * (1 + 0.035 * math.sin(5 * t + ph) + 0.025 * math.sin(13 * t + ph * 1.7) + 0.012 * math.sin(31 * t + ph * 0.6))
    # a few small nicks on the edges ('light breaks only'): (angle, side, radius as a part of the half width)
    nicks = [(0.55, 1, 0.20), (1.90, -1, 0.17), (2.75, 1, 0.22), (3.65, -1, 0.15), (4.55, 1, 0.19), (5.60, -1, 0.16)]
    cxy = (S - 0.0) / 2.0
    cap0 = (idx == 0); cap1 = (idx == ARC_N - 1)
    p0 = (0.0, -rc)
    lim = hw0 * 1.12 + 2
    for y in range(S):
        dy = y + 0.5 - cxy
        for x in range(S):
            dx = x + 0.5 - cxy
            r = math.hypot(dx, dy)
            if abs(r - rc) > lim and not ((cap0 or cap1) and math.hypot(dx - p0[0], dy - p0[1]) < lim):
                continue
            t = math.atan2(dx, -dy)
            if t < 0: t += TAU
            ri = rc - hwo(t, 1.1); ro = rc + hwo(t, 3.3)
            sd = min(r - ri, ro - r)
            phi = t - (th0 + th1) / 2
            if phi > math.pi: phi -= TAU
            if phi < -math.pi: phi += TAU
            sa = min(r * (phi + hs), r * (he - phi))
            sdb = min(sd, sa)
            if cap0 or cap1:                                              # the round cap at 0 / 360 degrees (the same point)
                sdb = max(sdb, hw0 * 0.95 - math.hypot(dx - p0[0], dy - p0[1]))
            for (nt, side, nr) in nicks:
                nd = math.hypot(dx - (rc + side * hw0) * math.sin(nt), dy + (rc + side * hw0) * math.cos(nt)) - nr * hw0
                if nd < sdb: sdb = nd
            v = int(255 * max(0.0, min(1.0, sdb + 0.5)))
            if v: a[y * S + x] = v
    return a


def _track_pixels(S):
    import math
    rc = ARC_KR * S; hw = max(1.0, 0.5 * RING_STROKE * S)
    a = bytearray(S * S); cxy = S / 2.0; TAU = 2 * math.pi
    nicks = [(0.4, 0.5), (1.35, 0.4), (2.2, 0.5), (3.3, 0.4), (4.1, 0.5), (5.2, 0.4)]
    for y in range(S):
        dy = y + 0.5 - cxy
        for x in range(S):
            dx = x + 0.5 - cxy
            r = math.hypot(dx, dy)
            if abs(r - rc) > hw + 2: continue
            sd = hw - abs(r - rc)                                      # one clean unbroken line (the owner: no 'circle circle'; review M2)
            v = int(255 * max(0.0, min(1.0, sd + 0.5)))
            if v: a[y * S + x] = v
    return a


def _dab_pixels(w):
    import math
    a = bytearray(w * w); c = w / 2.0; R = w * 0.45
    for y in range(w):
        for x in range(w):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            r = R * (1 + 0.025 * math.sin(math.atan2(y + 0.5 - c, x + 0.5 - c) * 3 + 0.8))
            v = int(255 * max(0.0, min(1.0, r - d + 0.5)))
            if v: a[y * w + x] = v
    return a


def _white_alpha(a):
    px = bytearray(b'\xff\xff\xff\0' * len(a))
    px[3::4] = a
    return px


_PX_CACHE = {}


def _extra_pixels(kind, w, h):
    k = (WATCH, kind, w, h)
    if k not in _PX_CACHE:
        _PX_CACHE[k] = bytes(_extra_pixels_raw(kind, w, h))
    return _PX_CACHE[k]


def _extra_pixels_raw(kind, w, h):
    if WATCH and kind in ('disc', 'wear', 'bezel', 'mfill'):
        import kl_hud_watch as _W
        return _W.pixels(kind, w, h)

    if kind.startswith('arc'):
        return _white_alpha(_arc_pixels(kind[3], int(kind[4:])))
    if kind == 'ring':
        return _white_alpha(_track_pixels(w))
    if kind == 'dab':
        return _white_alpha(_dab_pixels(w))

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

    apply_marks(files, ext, dst, log)                      # nothing unless --test-bake --mark-slots

    import kl_graft

    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])

    for f in os.listdir(os.path.dirname(zp)):

        q = os.path.join(os.path.dirname(zp), f)

        if os.path.isfile(q) and not os.path.samefile(q, zp):

            shutil.copyfile(q, os.path.join(dst, f))

    log('wrote %s (%d pictures)' % (out, len(new)))

    return out





def apply_markers(src, dst, shop=True, log=print):
    """An already baked level (folder or zip) -> folder `dst` with ONLY the world markers restyled (tools/kl_hud_marks.py) and, with
    shop, the shop's names (tools/kl_hud_shop.py): the upgrade of a level baked before 2026-10-13 without baking its fonts again."""
    global MARKERS
    import kl_hud_marks as _M
    zp, order, files, ext = open_level(src)
    tex = T.read_tex(files[ext['.TEX']])
    slots = hud_slots(files, ext)
    old, MARKERS = MARKERS, True
    try:
        new = build_pictures(tex, {k: v for k, v in slots.items() if k in _M.MARKER_SLOTS or k in _M.GLYPH_SLOTS.values()}, log)
    finally:
        MARKERS = old
    for tid, (e, kind, tw, th, px) in new.items():
        t = tex.tex[tid]
        tex.tex[tid] = T.Texture(e, t.faces, t.cube, t.frames, t.group)
    files[ext['.TEX']] = T.write_tex(tex)
    changed = []
    if shop:
        import kl_hud_shop
        changed = kl_hud_shop.apply_level(files, log, guns=os.path.join(os.path.dirname(zp), 'KLGuns.ini'))
    os.makedirs(dst, exist_ok=True)
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError("the output folder is the build's own")
    import kl_graft
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for f in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), f)
        if os.path.isfile(q) and not os.path.samefile(q, zp):
            shutil.copyfile(q, os.path.join(dst, f))
    log('wrote %s (%d marker pictures, %d .LOC member(s) with the shop names)' % (out, len(new), len(changed)))
    return out


# ------------------------------------------------------------------ TEST BAKE: the slot number stamped on every HUD picture
# re/hud_killfeed_plan.md step 0 (K1): which of the 200 picture slots is the kill line's skull and which the grey '$' over loot is
# NOT established, and the code that draws them has not been read. So a test archive stamps each picture with ITS SLOT NUMBER and one
# run with a kill and a loot pick-up reads the numbers off the screenshots. No hook change.
# Never for the owner's tab: `--mark-slots` works only with `--test-bake`, and the output folder's name must contain TEST (apply()
# refuses otherwise, so a library caller such as kl_graft cannot turn it on by accident: MARK_SLOTS is None unless main() set it).
MARK_SLOTS = None                 # None = off; a set of slot numbers to stamp; an empty set = every slot of the list
MARK_INK, MARK_CHALK, MARK_EDGE = (12, 12, 13), (243, 240, 234), (240, 71, 90)
_DIGITS = {                       # 3 x 5 bitmap digits, rows top to bottom
    '0': ('111', '101', '101', '101', '111'), '1': ('010', '110', '010', '010', '111'), '2': ('111', '001', '111', '100', '111'),
    '3': ('111', '001', '111', '001', '111'), '4': ('101', '101', '111', '001', '001'), '5': ('111', '100', '111', '001', '111'),
    '6': ('111', '100', '111', '101', '111'), '7': ('111', '001', '010', '010', '010'), '8': ('111', '101', '111', '101', '111'),
    '9': ('111', '101', '111', '001', '111')}


def parse_slots(s):
    """'52,53,127-160' -> {52, 53, 127, ..., 160}; '' or 'all' -> set() (= every slot)"""
    out = set()
    for part in (s or '').split(','):
        part = part.strip()
        if not part or part == 'all':
            continue
        a, _, b = part.partition('-')
        out.update(range(int(a), int(b or a) + 1))
    if any(not 0 <= k < 200 for k in out):
        raise ValueError('HUD picture slots are 0..199: %s' % s)
    return out


def stamp_pixels(px, w, h, numbers):
    """Stamp the slot number(s) into the top-left corner of an RGBA picture of w x h, in place; -> (box width, box height).
    An ink box with a coral edge and chalk digits, one number per row. The stroke is 2 px on a 32 or 64 px icon (a three-
    digit number is then 26 x 13 px: most of a 32 px icon's width, as the skull candidates 173..179 are 32 px and the number
    must read at 1:1), 4 on 128, 9 on 256 (under half the width) so the number reads in a 1280 x 720 screenshot of a picture
    drawn near its own size; a picture drawn much smaller than it is (the 12 px lives skulls) will not be readable."""
    s = max(2 if min(w, h) >= 32 else 1, min(w // 26, h // 13))
    rows = [str(int(n)) for n in numbers]
    bw = 2 * s + max(len(r) for r in rows) * 4 * s - s
    bh = 2 * s + len(rows) * 6 * s - s
    bw, bh = min(bw, w), min(bh, h)
    for y in range(bh):
        for x in range(bw):
            i = 4 * (y * w + x)
            edge = x == 0 or y == 0 or x == bw - 1 or y == bh - 1
            px[i:i + 4] = bytes(MARK_EDGE if edge else MARK_INK) + b'\xff'
    for r, text in enumerate(rows):
        for c, ch in enumerate(text):
            for gy, row in enumerate(_DIGITS[ch]):
                for gx, bit in enumerate(row):
                    if bit != '1':
                        continue
                    for dy in range(s):
                        for dx in range(s):
                            x = s + c * 4 * s + gx * s + dx
                            y = s + r * 6 * s + gy * s + dy
                            if x < bw - 1 and y < bh - 1:
                                i = 4 * (y * w + x)
                                px[i:i + 4] = bytes(MARK_CHALK) + b'\xff'
    return bw, bh


def mark_slots(tex, slots_ids, which=None, log=print):
    """{slot: texture id} -> {id: (new entry, slot list)}: every listed picture decoded (kl_hud_marks.decode: DXT1 / 3 / 5 or
    ABGR, first mip), its slot number(s) stamped, written back as an ABGR record of the same size under the same id (the
    plate bake's record shape). which: the slots to stamp (empty / None = all). A texture in several slots gets every number."""
    import kl_hud_marks as _M
    by_id = {}
    for slot, tid in sorted(slots_ids.items()):
        if which and slot not in which:
            continue
        by_id.setdefault(tid, []).append(slot)
    out = {}
    for tid, slots in sorted(by_id.items()):
        if tid not in tex.tex:
            log('mark slot %s: texture %d is not in the .TEX: skipped' % (slots, tid))
            continue
        e = tex.tex[tid].entry
        _size, f1, _f2, _id, th, tw, _mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', e, 0)
        q = e.index(b'\0', 36) + 1
        try:
            w, h, px = _M.decode(e)
        except Exception as ex:                                # a format decode() has no reader for: left as it is
            log('mark slot %s: texture %d (%s) not decoded (%s): skipped' % (slots, tid, f1[::-1].decode('latin1'), ex))
            continue
        stamp_pixels(px, w, h, slots)
        body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', _id, th, tw, 1, fl & ~0x100, sc, x20) + e[36:q] + struct.pack('<I', len(px)) + bytes(px)
        out[tid] = (struct.pack('<I', len(body) + 4) + body, slots)
        log('mark slot %-12s id %4d %dx%d %s -> ABGR  %s' % (','.join(map(str, slots)), tid, tw, th, f1[::-1].decode('latin1'), tex.tex[tid].name))
    return out


def apply_marks(files, ext, dst, log=print):
    """The test-bake step of apply() / apply_pictures(): a no-op (files untouched) unless MARK_SLOTS is set. Edits files in
    place and writes <dst>/TEST_BAKE_mark_slots.txt (slot -> id -> stock name) for the run's notes. -> {id: slots}"""
    if MARK_SLOTS is None:
        return {}
    if 'TEST' not in os.path.basename(os.path.abspath(dst)):
        raise ValueError('a bake with the slot numbers stamped (--mark-slots) goes only into a folder whose name contains TEST')
    tex = T.read_tex(files[ext['.TEX']])
    slots = hud_slots(files, ext)
    names = {tid: tex.tex[tid].name for tid in slots.values() if tid in tex.tex}
    new = mark_slots(tex, slots, MARK_SLOTS, log)
    for tid, (e, _s) in new.items():
        t = tex.tex[tid]
        tex.tex[tid] = T.Texture(e, t.faces, t.cube, t.frames, t.group)
    files[ext['.TEX']] = T.write_tex(tex)
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, 'TEST_BAKE_mark_slots.txt'), 'w') as f:
        f.write('TEST BAKE: every HUD picture carries its slot number (kl_hud.py --test-bake --mark-slots). NOT for the owner\'s tab.\n')
        f.write('K1 (re/hud_killfeed_plan.md 6): read the number on the kill line\'s skull and on the grey $ over loot.\n')
        for slot in sorted(slots):
            tid = slots[slot]
            f.write('%3d  id %4d  %s%s\n' % (slot, tid, names.get(tid, '?'), '' if tid in new else '  (not stamped)'))
    log('TEST BAKE: %d pictures stamped with their slot numbers (%d slots in the list); not for the owner\'s tab' % (len(new), len(slots)))
    return {tid: s for tid, (_e, s) in new.items()}


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

    # the REAL baked arc pictures (2026-10-12): the level's own textures 3000.. sampled the way the game's sprite draw would (area
    # average), and klhud.c's klu_arc / klu_dabs / klu_track mirrored number for number
    def texa(tid):
        e = tex.tex[tid].entry; q = e.index(b'\0', 36) + 1
        _s, _a, _b, _i, th, tw = struct.unpack_from('<I4s4sIHH', e, 0)
        n = struct.unpack_from('<I', e, q)[0]
        return tw, th, e[q + 4:q + 4 + n]
    TA = {}
    def pic(slot, x0, y0, dw, dh, col, a=1.0):
        tid = EXTRA_ID + [s for s, *_ in EXTRAS].index(slot)
        if tid not in TA: TA[tid] = texa(tid)
        tw, th, px = TA[tid]
        ss = max(1, int(tw / max(dw, 1.0) + 0.999)); ss = min(ss, 8)
        for y in range(max(0, int(y0)), min(H_, int(y0 + dh) + 1)):
            for x in range(max(0, int(x0)), min(W_, int(x0 + dw) + 1)):
                acc = 0.0
                for j in range(2):
                    for i in range(2):
                        u = ((x + (i + .5) / 2 - x0) / dw) * tw; v = ((y + (j + .5) / 2 - y0) / dh) * th
                        if 0 <= u < tw and 0 <= v < th:
                            acc += px[4 * (int(v) * tw + int(u)) + 3]
                al = acc / 4 / 255.0 * a
                if al > 0:
                    q = 3 * (y * W_ + x)
                    for k in range(3):
                        img[q + k] = int(col[k] * al + img[q + k] * (1 - al))
    SLOTS = ((123, 124, 125), (126, 185, 190)); RATIO = (ARC_FAM['A'][1], ARC_FAM['B'][1])
    def dabs(cx_, cy_, r, ta, tb, stroke, col):
        size = stroke / 0.9 * 0.97; step = min(2.5, stroke * .4); ln = max(0.0, r * 2 * math.pi * (tb - ta)); n = int(ln / step) + 1
        for k in range(n + 1):
            a = 2 * math.pi * (ta + (tb - ta) * k / n)
            pic(113, cx_ + r * math.sin(a) - size / 2, cy_ - r * math.cos(a) - size / 2, size, size, col)
    def arc(cx_, cy_, r, fam, t0, t1, col):
        D = r / ARC_KR; stroke = RATIO[fam] * r; cur = t0
        if t1 <= t0: return
        for j in range(ARC_N):
            a, b = j / ARC_N, (j + 1) / ARC_N
            if t0 <= a + 1e-4 and t1 >= b - 1e-4:
                if cur < a - 1e-4: dabs(cx_, cy_, r, cur, a, stroke, col)
                pic(SLOTS[fam][j], cx_ - D / 2, cy_ - D / 2, D, D, col); cur = b
        if cur < t1 - 1e-4: dabs(cx_, cy_, r, cur, t1, stroke, col)
    def track(cx_, cy_, r, col):
        D = r / ARC_KR; pic(115, cx_ - D / 2, cy_ - D / 2, D, D, col)
    TRACKC = (74, 72, 68)
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

    if WATCH:
        import kl_hud_wprev as _P, kl_hud_watch as _WM
        _cv = _P.Canvas(sys.modules[__name__], src, W_, H_, 1, img=img)
        _WM.draw_watch(_cv, 1212, 66, 219.0, 13); log('watch: %d pictures' % _cv.count); _c0 = _cv.count
        _WM.draw_escape(_cv, 1150, 66, .35, 13, 170); log('escape dial: %d pictures' % (_cv.count - _c0))
    else:
        wcx, wcy = 1212, 66
        left = .6; a_ = 2 * math.pi * (1 - left)
        disc(wcx, wcy, 34.5, (8, 8, 9), .61); track(wcx, wcy, 29, TRACKC); arc(wcx, wcy, 29, 0, 1 - left, 1.0, CHALKc)
        hs = 3.9 / .9
        for k in range(1, int(21 / 1.1) + 1): pic(113, wcx + math.sin(a_) * 1.1 * k - hs / 2, wcy - math.cos(a_) * 1.1 * k - hs / 2, hs, hs, CHALKc)
        pic(113, wcx - 4.3, wcy - 4.3, 8.6, 8.6, CHALKc)
        ex, ey = wcx - 75, wcy + 5
        disc(ex, ey, 27.5, (8, 8, 9), .61); track(ex, ey, 23, TRACKC); arc(ex, ey, 23, 0, 1 - .65, 1.0, ORANGE); rect(ex - 9, ey - 5, 18, 10, CHALKc)         # a car, as a block
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

    if WATCH:
        _WM.draw_weapon(_cv, 1199, 598, 0.8, 24, 9, 90, 65, 13)
        _WM.draw_label(_cv, 'ZASTAVA M85', '222', _WM.LABEL_CW)
    else:
        wx, wy = 1177, 598; S85 = 0.85                                            # klhud_weapon.c KLWD_S: the whole circle x 0.76 about its centre
        disc(wx, wy, 70.5 * S85, (8, 8, 9), .61); track(wx, wy, 62 * S85, TRACKC); arc(wx, wy, 62 * S85, 1, 0.0, .7, CHALKc)
        rect(wx - 43.5 * S85, wy + 2 * S85, 87 * S85, 2, CHALKc, .29)                                 # the divider
        text('H2', '30', wx - 7 * S85, leg(wy - 36 * S85, 'H2'), CHALKc, 'r'); text(SM, '150', wx - 5 * S85, leg(wy + 18 * S85, SM), (169, 165, 157), 'r')
        text(LAB, 'ZASTAVA M85 . 270', wx + TRK / 2.0, leg(wy + 88 * S85, LAB), CORALc, 'c')
    # the loot ring (a third of it filled) and the pop-up bar + the traitor box

    lx, ly = 640, 470
    disc(lx, ly, 17, (15, 16, 15)); (arc(lx, ly, 17, 0, 0.0, 1.0, (74, 72, 68)) if WATCH else track(lx, ly, 17, (141, 137, 130))); arc(lx, ly, 22, 0, 0.0, .34, CHALKc)      # the watch look: the track is a dim full ring of the stroke's family (115 is the bezel)
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





def preview_board(src, out, dumps, log=print):
    """THE ROUND-OVER SCOREBOARD offline (2026-10-12; klhook/klhud_board2.c): draws the layout the C code composed - klhook/klsb_test.exe <folder> writes
    board_<case>.txt, one line a text ("T idx x y fnt align colour 'text'") and one a picture ("P slot x y w h argb layer") - with the level's own baked
    fonts and extra pictures (3000..) on a faux street, 1280 x 720, 1:1. The pen's baseline lies at y - header[9] (the game's rule, seen live), the label
    font's tracking is added back for right / centre alignment as the hook does. Pictures: slots 111 .. 125 are the level's real textures sampled by area;
    181 (UI_White) is a flat rectangle; 178 (the stock skull) is a stand-in drawn by hand (NOT the game's picture). NOT the game's renderer: the file's
    order is the draw order (no layer sort), no real world behind the plate.
    out = the main file (the first dump); every other case goes beside it as <out>_<case>.png and a side-by-side sheet of the plates as <out>_sheet.png."""
    import re
    _zp, _o, files, ext = open_level(src)
    fonts = fonts_of(files, ext)
    p = G.read(files[ext['.prm']], 'dd'); tex = T.read_tex(files[ext['.TEX']])
    W_, H_ = 1280, 720
    cache = {}; TA = {}

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

    def texa(tid):
        e = tex.tex[tid].entry; q = e.index(b'\0', 36) + 1
        _s, _a, _b, _i, th, tw = struct.unpack_from('<I4s4sIHH', e, 0)
        n = struct.unpack_from('<I', e, q)[0]
        return tw, th, e[q + 4:q + 4 + n]

    ROLE = {0: 'H2', 1: 'H1', 2: 'DebugText', 3: 'H3'}          # klhud.c: names / big / labels / small
    TRK = 3.0

    def argb(v): return ((v >> 16) & 255, (v >> 8) & 255, v & 255), (v >> 24) / 255.0

    def render(path):
        img = bytearray(W_ * H_ * 3)
        for y in range(H_):                                         # a faux street: sky, buildings, road
            if y < 250: c = (60 + y // 6, 70 + y // 6, 80 + y // 8)
            elif y < 420: c = (88, 84, 78)
            else: c = (50 + (y - 420) // 10, 52 + (y - 420) // 10, 54 + (y - 420) // 12)
            img[3 * y * W_: 3 * (y + 1) * W_] = bytes(c) * W_
        for x0, y0, w, h, c in ((60, 180, 180, 250, (120, 110, 96)), (980, 140, 220, 290, (70, 78, 90)), (250, 300, 90, 130, (150, 140, 120)), (820, 380, 330, 40, (190, 170, 60))):
            for y in range(y0, y0 + h):
                img[3 * (y * W_ + x0): 3 * (y * W_ + x0 + w)] = bytes(c) * w

        def blend(X, Y, col, a):
            if 0 <= X < W_ and 0 <= Y < H_ and a > 0:
                q = 3 * (Y * W_ + X)
                for k in range(3): img[q + k] = int(col[k] * a + img[q + k] * (1 - a))

        def rect(x0, y0, w, h, col, a=1.0):
            for y in range(max(0, int(y0)), min(H_, int(y0 + h))):
                for x in range(max(0, int(x0)), min(W_, int(x0 + w))): blend(x, y, col, a)

        def pic(slot, x0, y0, dw, dh, col, a):
            if slot == 181: rect(x0, y0, dw, dh, col, a); return
            if slot == 178:                                         # a stand-in skull
                rect(x0 + dw * .1, y0, dw * .8, dh * .7, col, a); rect(x0 + dw * .25, y0 + dh * .7, dw * .5, dh * .3, col, a)
                rect(x0 + dw * .22, y0 + dh * .3, dw * .2, dh * .2, (12, 12, 13), a); rect(x0 + dw * .58, y0 + dh * .3, dw * .2, dh * .2, (12, 12, 13), a); return
            tid = EXTRA_ID + [e[0] for e in EXTRAS].index(slot)
            if tid not in TA: TA[tid] = texa(tid)
            tw, th, px = TA[tid]
            for y in range(max(0, int(y0)), min(H_, int(y0 + dh) + 1)):
                for x in range(max(0, int(x0)), min(W_, int(x0 + dw) + 1)):
                    acc = 0.0
                    for j in range(2):
                        for i in range(2):
                            u = ((x + (i + .5) / 2 - x0) / dw) * tw; v = ((y + (j + .5) / 2 - y0) / dh) * th
                            if 0 <= u < tw and 0 <= v < th: acc += px[4 * (int(v) * tw + int(u)) + 3]
                    blend(x, y, col, acc / 4 / 255.0 * a)

        def text(fnt, align, s_, x, ytop, col):
            name = ROLE[fnt]; h, by, pg = font(name)
            if fnt == 2: x += TRK if align == 1 else TRK * .5 if align == 2 else 0
            wid = width(name, s_); pen = x if align == 0 else x - wid if align == 1 else x - wid / 2.0; base = ytop - h[9]
            for ch in s_:
                r = by.get(ord(ch))
                if r is None: continue
                _tid, tw, th, px, _e = pg[r[1]]
                for yy in range(r[7]):
                    for xx in range(r[6]):
                        i = 4 * ((r[3] + yy) * tw + r[2] + xx); a = px[i + 3] / 255.0
                        if a: blend(int(pen + r[8] + xx), int(base + r[9] + yy), col, a)
                pen += r[10]

        lines = open(path, encoding='utf-8').read().splitlines()
        for line in lines:
            m = re.match(r"P (\d+) (\S+) (\S+) (\S+) (\S+) ([0-9a-f]{8}) (\d+)", line)
            if m:
                col, a = argb(int(m.group(6), 16)); pic(int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), col, a)
        for line in lines:                                          # texts last (the hook draws the pictures first, the texts over them)
            m = re.match(r"T (\d+) (\S+) (\S+) (\d) (\d) ([0-9a-f]{8}) '(.*)'", line)
            if m:
                col, a = argb(int(m.group(6), 16)); text(int(m.group(4)), int(m.group(5)), m.group(7), float(m.group(2)), float(m.group(3)), col)
        return img

    base, ext_ = os.path.splitext(out); crops = []
    for i, (name, path) in enumerate(dumps):
        img = render(path); o = out if i == 0 else '%s_%s%s' % (base, name, ext_)
        _png(o, W_, H_, img); log('wrote %s (%s, 1280x720)' % (o, name))
        crops.append(bytes(b''.join(bytes(img[3 * (y * W_ + 300): 3 * (y * W_ + 980)]) for y in range(130, 560))))
    if len(crops) > 1:
        cw, ch = 680, 430; sheet = bytearray()
        for y in range(ch): sheet += b''.join(c[3 * y * cw: 3 * (y + 1) * cw] for c in crops)
        _png('%s_sheet%s' % (base, ext_), cw * len(crops), ch, sheet); log('wrote %s_sheet%s' % (base, ext_))



def _test_bake_options(a, out):
    """Takes `--test-bake` and `--mark-slots [list]` out of the option list `a` (in place) and sets MARK_SLOTS. Both flags
    and an output folder named ...TEST... are required together: a slot-numbered archive must not reach the owner's tab."""
    global MARK_SLOTS
    test = mark = None
    while '--test-bake' in a:
        a.remove('--test-bake'); test = True
    while '--mark-slots' in a:
        i = a.index('--mark-slots'); del a[i]
        mark = a.pop(i) if i < len(a) and not a[i].startswith('--') else 'all'
    if mark is None and test is None:
        return
    if mark is None or test is None:
        raise SystemExit('--mark-slots and --test-bake go together (a test archive with the slot numbers stamped on the HUD pictures)')
    if 'TEST' not in os.path.basename(os.path.abspath(out)):
        raise SystemExit('--mark-slots: the output folder name must contain TEST (got %r)' % os.path.basename(os.path.abspath(out)))
    MARK_SLOTS = parse_slots(mark)
    print('TEST BAKE: slot numbers stamped on %s HUD picture(s); the archive is for re/hud_killfeed_plan.md K1 only' % ('every' if not MARK_SLOTS else len(MARK_SLOTS)))


def main():
    global MARKERS, SHOPNAMES
    a = sys.argv[1:]

    if not a:

        print(__doc__); return

    cmd = a[0]

    if cmd in ('all', 'pictures') and len(a) > 2:
        _test_bake_options(a, a[2])

    if cmd == 'dump':

        dump(a[1])

    elif cmd == 'preview':

        preview(a[1], a[2], a[3], a[4])

    elif cmd == 'preview-hud':

        preview_hud(a[1], a[2])

    elif cmd == 'preview-dials':                          # the watch look's dial board at 1x / 2x / 4x with the picture count of every element (tools/kl_hud_wprev.py)
        import kl_hud_wprev
        kl_hud_wprev.preview_dials(sys.modules[__name__], a[1], a[2])
    elif cmd == 'preview-board':

        preview_board(a[1], a[2], [(os.path.basename(x)[6:-4], x) for x in a[3:]])

    elif cmd == 'pictures':

        png = a[a.index('--png') + 1] if '--png' in a else None

        apply_pictures(a[1], a[2], png)

    elif cmd == 'all':
        kw = {}
        _mk = _sn = None

        rest = a[3:]

        while rest:

            k = rest.pop(0)

            if k == '--face': kw['face'] = rest.pop(0)

            elif k == '--weight': kw['weight'] = int(rest.pop(0))

            elif k == '--scale': kw['scale'] = float(rest.pop(0))

            elif k == '--caps': kw['caps'] = True
            elif k == '--watch': set_watch(int(rest.pop(0)))      # 1 (default) = the watch look, 0 = the look before 2026-10-12 noon

            elif k == '--chip': kw['chip'] = float(rest.pop(0))

            elif k == '--markers': _mk = int(rest.pop(0))           # 0 = keep the stock world markers under --look deadmen
            elif k == '--shopnames': _sn = int(rest.pop(0))         # 0 = keep the shop's stock names under --look deadmen
            elif k == '--look' and rest.pop(0) == 'deadmen':      # the owner's look of 2026-10-11
                MARKERS = SHOPNAMES = True

                _g = _Gdi(); _own = _g.has('Anton') and _g.has('Montserrat')

                print('faces:', 'the draft own faces (Anton, Montserrat from <work>/fonts)' if _own else 'stand-ins (Impact, Segoe UI Black): put Anton-Regular.ttf and Montserrat into <work>/fonts for the draft own faces')

                kw.update(face='Anton' if _own else 'Impact', weight=400, scale=.9, caps=True, chip=.6, extras=True, specs=DRAFT_SPECS_ANTON if _own else DRAFT_SPECS)

            else: raise SystemExit('unknown option ' + k)
        if _mk == 0:
            MARKERS = False
        if _sn == 0:
            SHOPNAMES = False
        _out, _reps = apply(a[1], a[2], pictures=True, **kw)

        if kw.get('specs'):

            print('hook roles (osd+0xd54 names, +0xd50 big, +0xd5c labels, +0xd58 small): [HUD] Cap0=%s Cap1=%s Cap2=%s Cap3=%s (klhud.c default)' % tuple(_reps[n]['cap'] for n in ('H2', 'H1', 'DebugText', 'H3')))

        bad = check(a[1], a[2], pictures=True, extras=kw.get('extras', False), draft=bool(kw.get('specs')))

        print('check:', 'PASS' if not bad else 'FAIL ' + '; '.join(bad))

    elif cmd == 'markers':                                  # an already baked level: only the world markers (+ the shop names unless --shopnames 0)
        apply_markers(a[1], a[2], shop=not ('--shopnames' in a and a[a.index('--shopnames') + 1] == '0'))
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

