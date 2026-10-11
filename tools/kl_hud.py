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
        self.hf = g.CreateFontW(-px, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, ANTIALIASED_QUALITY, 0, face)
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
        self.ascent, self.descent = tm.tmAscent, tm.tmDescent
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
        g.TextOutW(ctypes.c_void_p(self.mdc), ox, oy, ch, 1)
        g.GdiFlush()
        px = ctypes.string_at(self.bits, self.w * self.h * 4)
        W_, H_ = self.w, self.h
        rows = [px[4 * y * W_: 4 * (y + 1) * W_: 4] for y in range(H_)]       # blue channel = coverage
        ys = [y for y in range(H_) if any(rows[y])]
        if not ys:
            return abc.a + abc.b + abc.c, 0, 0, 0, 0, []
        xs0 = min(next(x for x in range(W_) if rows[y][x]) for y in ys)
        xs1 = max(max(x for x in range(W_) if rows[y][x]) for y in ys)
        y0, y1 = ys[0], ys[-1]
        ink = [rows[y][xs0:xs1 + 1] for y in range(y0, y1 + 1)]
        return abc.a + abc.b + abc.c, xs0 - ox, y0 - (oy + self.ascent), xs1 - xs0 + 1, y1 - y0 + 1, ink

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
def build_font(chunk, tex, face, weight=600, scale=1.0, log=print):
    """-> (new chunk, {texture id: new entry}, report). Page-0 records are re-rasterized with `face`; page-1
    records (private characters) are kept."""
    h, recs, tail = parse(chunk)
    px = max(1, int(round(h[2] * scale)))
    page0 = max(r[1] for r in recs)                      # the 4096 + id ref
    keep = [r for r in recs if r[1] != page0]
    todo = [r for r in recs if r[1] == page0]
    tid, tw, th, _px, entry = tex_page(tex, page0)
    gd = _Gdi().font(face, px, weight)
    glyphs = []
    for r in todo:
        ch = chr(r[0])
        adv, xo, yo, w, hh, ink = gd.glyph(ch)
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
    rgba = bytearray(b'\xff\xff\xff\0' * (tw * th))
    rgba[3::4] = atlas
    recs2 = []
    it = iter(new)
    for r in recs:                                       # stock order kept (page-1 records in place)
        recs2.append(r if r[1] != page0 else next(it))
    rep = {'face': face, 'px': px, 'glyphs': len(todo), 'kept': len(keep), 'page rows used': y + shelf + PAD,
           'ascent': gd.ascent, 'descent': gd.descent}
    return pack(h, recs2, tail), {tid: tex_replace(entry, rgba)}, rep


def apply(src, dst, face='Bahnschrift SemiCondensed', weight=600, scale=1.0, only=None, log=print):
    """A build (folder or zip) -> folder `dst` with the fonts replaced. Files beside the archive are copied."""
    zp, order, files, ext = open_level(src)
    fonts = fonts_of(files, ext)
    p = G.read(files[ext['.prm']], 'dd')
    tex = T.read_tex(files[ext['.TEX']])
    reps = {}
    for name, ci in sorted(fonts.items(), key=lambda kv: kv[1]):
        if only and name not in only:
            continue
        chunk, entries, rep = build_font(p.chunks[ci], tex, face, weight, scale, log)
        p.chunks[ci] = chunk
        for tid, e in entries.items():
            tex.tex[tid] = T.Texture(e, tex.tex[tid].faces, tex.tex[tid].cube, tex.tex[tid].frames, tex.tex[tid].group)
        reps[name] = rep
        log('font %-10s chunk %d: %s %d px, %d glyphs on page 0 (%d rows), ascent %d' % (name, ci, rep['face'], rep['px'], rep['glyphs'], rep['page rows used'], rep['ascent']))
    files[ext['.prm']] = G.write(p)
    files[ext['.TEX']] = T.write_tex(tex)
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


def check(src, dst, log=print):
    """The two builds differ only in the font chunks and their page-0 textures; every record's rectangle lies
    on its page, every char is still there. -> list of problems."""
    _z, o1, f1, e1 = open_level(src); _z2, o2, f2, e2 = open_level(dst)
    bad = []
    if o1 != o2:
        bad.append('member order differs')
    for n in o1:
        if n not in (e1['.prm'], e1['.TEX']) and f1[n] != f2.get(n):
            bad.append('member %s changed' % n)
    p1, p2 = G.read(f1[e1['.prm']], 'dd'), G.read(f2[e2['.prm']], 'dd')
    if len(p1.chunks) != len(p2.chunks) or p1.refs != p2.refs:
        bad.append('chunk table differs')
    fonts = fonts_of(f1, e1)
    changed = [i for i in range(1, len(p1.chunks)) if p1.chunks[i] != p2.chunks[i]]
    if set(changed) - set(fonts.values()):
        bad.append('chunks other than fonts changed: %s' % sorted(set(changed) - set(fonts.values()))[:5])
    t2 = T.read_tex(f2[e2['.TEX']])
    for name, ci in fonts.items():
        h1, r1, tl1 = parse(p1.chunks[ci]); h2, r2, tl2 = parse(p2.chunks[ci])
        if h1 != h2 or tl1 != tl2 or len(r1) != len(r2):
            bad.append('%s: header / tail / count changed' % name)
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
    elif cmd == 'fonts':
        kw = {}
        rest = a[3:]
        while rest:
            k = rest.pop(0)
            if k == '--face': kw['face'] = rest.pop(0)
            elif k == '--weight': kw['weight'] = int(rest.pop(0))
            elif k == '--scale': kw['scale'] = float(rest.pop(0))
            elif k == '--only': kw['only'] = rest.pop(0).split(',')
            else: raise SystemExit('unknown option ' + k)
        apply(a[1], a[2], **kw)
        bad = check(a[1], a[2])
        print('check:', 'PASS' if not bad else 'FAIL ' + '; '.join(bad))
    else:
        raise SystemExit('unknown command ' + cmd)


if __name__ == '__main__':
    main()
