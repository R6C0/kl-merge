"""
kl_hud_wprev.py - the offline PREVIEW of the watch look (tools/kl_hud_watch.py's picture lists drawn with a baked level's REAL textures
and fonts).  Used by kl_hud.py:  preview-hud (the whole HUD at 1280 x 720, 1:1) and  preview-dials <level> <out dir>  (the dial board at
1x / 2x / 4x with the picture count of every element).

The model of the game's draw: one picture = a texture stretched to w x h at a top-left place, tinted by one ARGB, BILINEAR sampled at the pixel
centre, NO mips (GUESS: the live look W1 decides), drawn in call order (the hook queues in the same order and the layers never decrease).
`H` is the kl_hud module (passed in, because it may be __main__).
"""
import math
import kl_hud_watch as W

DAB_INK = W.DAB_INK


class Canvas:
    def __init__(self, H, src, w, ht, k=1, img=None):
        import struct
        self.H, self.W, self.Ht, self.k = H, w, ht, k
        _zp, _o, files, ext = H.open_level(src)
        self.fonts = H.fonts_of(files, ext)
        self.p = H.G.read(files[ext['.prm']], 'dd')
        self.tex = H.T.read_tex(files[ext['.TEX']])
        self.img = img if img is not None else bytearray(w * k * ht * k * 3)
        self.ox = self.oy = 0.0
        self.count = 0
        self._ta, self._fc = {}, {}
        self.struct = struct
        self.TRK = 3.0                          # klhud.c KLU_TRACK: the label font's baked tracking, added back for right / centre alignment
        self.CAP = {n: -self._font(n)[0][9] for n in ('H1', 'H2', 'H3', 'DebugText')}

    def background(self):
        w, ht, k = self.W * self.k, self.Ht * self.k, self.k
        for y in range(ht):
            row = bytearray()
            for x in range(w):
                u = x / w
                v = y / ht
                c = 70 + 55 * u - 40 * v + 18 * math.sin(x / (9.0 * k)) * math.sin(y / (7.0 * k))
                if 0.45 < v < 0.52:
                    c += 70
                row += bytes((max(0, min(255, int(c))), max(0, min(255, int(c + 4))), max(0, min(255, int(c + 9)))))
            self.img[3 * y * w:3 * (y + 1) * w] = row

    def fill(self, rgb):
        self.img[:] = bytes(((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)) * (self.W * self.k * self.Ht * self.k)

    def _blend(self, X, Y, col, a):
        if 0 <= X < self.W * self.k and 0 <= Y < self.Ht * self.k and a > 0:
            q = 3 * (Y * self.W * self.k + X)
            im = self.img
            im[q] = int(col[0] * a + im[q] * (1 - a))
            im[q + 1] = int(col[1] * a + im[q + 1] * (1 - a))
            im[q + 2] = int(col[2] * a + im[q + 2] * (1 - a))

    def rect(self, x, y, w, h, rgb, a=1.0):
        k = self.k
        x += self.ox
        y += self.oy
        col = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
        for Y in range(int(y * k), int((y + h) * k + 0.999)):
            for X in range(int(x * k), int((x + w) * k + 0.999)):
                self._blend(X, Y, col, a)

    def _texa(self, slot):
        if slot not in self._ta:
            H = self.H
            tid = H.EXTRA_ID + [s for s, *_ in H.EXTRAS].index(slot)
            e = self.tex.tex[tid].entry
            q = e.index(bytes(1), 36) + 1
            _s, _a, _b, _i, th, tw = self.struct.unpack_from('<I4s4sIHH', e, 0)
            n = self.struct.unpack_from('<I', e, q)[0]
            self._ta[slot] = (tw, th, e[q + 4:q + 4 + n][3::4])
        return self._ta[slot]

    def pic(self, slot, x, y, w, h, argb_, layer=0):
        self.count += 1
        if w <= 0 or h <= 0:
            return
        k = self.k
        if slot == 181:                                       # UI_White: a plain rectangle
            self.rect(x, y, w, h, argb_ & 0xffffff, (argb_ >> 24) / 255.0)
            return
        if slot not in [s for s, *_ in self.H.EXTRAS]:       # the game's own pictures (icons): a stand-in block
            self.rect(x + w * .15, y + h * .32, w * .7, h * .36, argb_ & 0xffffff, (argb_ >> 24) / 255.0)
            return
        tw, th, al = self._texa(slot)
        a0 = (argb_ >> 24) / 255.0
        col = ((argb_ >> 16) & 255, (argb_ >> 8) & 255, argb_ & 255)
        x += self.ox
        y += self.oy
        X0, X1 = int(math.floor(x * k)), int(math.ceil((x + w) * k))
        Y0, Y1 = int(math.floor(y * k)), int(math.ceil((y + h) * k))
        for Y in range(max(0, Y0), min(self.Ht * k, Y1)):
            v = ((Y + .5) / k - y) / h * th - .5
            vi = int(math.floor(v))
            fv = v - vi
            for X in range(max(0, X0), min(self.W * k, X1)):
                u = ((X + .5) / k - x) / w * tw - .5
                ui = int(math.floor(u))
                fu = u - ui
                s = 0.0
                for dy, wy in ((0, 1 - fv), (1, fv)):
                    yy = vi + dy
                    if not 0 <= yy < th:
                        continue
                    for dx, wx in ((0, 1 - fu), (1, fu)):
                        xx = ui + dx
                        if 0 <= xx < tw:
                            s += al[yy * tw + xx] * wx * wy
                if s > 0:
                    self._blend(X, Y, col, s / 255.0 * a0)

    # rings: klhud.c klu_arc / klu_dabs, number for number
    def _dabs(self, cx, cy, r, ta, tb, stroke, argb_, layer):
        size = stroke / DAB_INK * 0.97
        step = min(2.5, stroke * .4)
        ln = max(0.0, r * 2 * math.pi * (tb - ta))
        n = int(ln / step) + 1
        for j in range(n + 1):
            a = 2 * math.pi * (ta + (tb - ta) * j / n)
            self.pic(113, cx + r * math.sin(a) - size / 2, cy - r * math.cos(a) - size / 2, size, size, argb_, layer)

    def arc(self, cx, cy, r, fam, t0, t1, argb_, layer=0):
        H = self.H
        F = H.ARC_FAM['AB'[fam]]
        D = r / H.ARC_KR
        stroke = F[1] * r
        t0 = max(0.0, t0)
        t1 = min(1.0, t1)
        if not t1 > t0:
            return
        cur = t0
        for j in range(H.ARC_N):
            a, b = j / H.ARC_N, (j + 1) / H.ARC_N
            if t0 <= a + 1e-4 and t1 >= b - 1e-4:
                if cur < a - 1e-4:
                    self._dabs(cx, cy, r, cur, a, stroke, argb_, layer)
                self.pic(F[2 + j], cx - D / 2, cy - D / 2, D, D, argb_, layer)
                cur = b
        if cur < t1 - 1e-4:
            self._dabs(cx, cy, r, cur, t1, stroke, argb_, layer)

    def gun(self, slot, x, y, size, argb_, layer=0):
        """stand-in for a type-6 gun picture (the real icons are the game's): a silhouette with a grip"""
        self.count += 1
        a = (argb_ >> 24) / 255.0
        rgb = argb_ & 0xffffff
        self.rect(x - size * .46, y - size * .13, size * .92, size * .2, rgb, a * .75)
        self.rect(x - size * .08, y + size * .02, size * .16, size * .3, rgb, a * .75)

    # text: the hook's baseline rule (the pen's baseline lies at y - header[9]); right / centre alignment add the tracking back
    def _font(self, name):
        if name not in self._fc:
            H = self.H
            h, recs, _t = H.parse(self.p.chunks[self.fonts[name]])
            pg = {}
            for r in recs:
                if r[1] not in pg:
                    pg[r[1]] = H.tex_page(self.tex, r[1])
            self._fc[name] = (h, {r[0]: r for r in recs}, pg)
        return self._fc[name]

    def width(self, name, s):
        h, by, _pg = self._font(name)
        return sum(by[ord(c)][10] for c in s if ord(c) in by)

    def text(self, name, s, x, y, argb_, align='l', cen=False):
        h, by, pg = self._font(name)
        wid = self.width(name, s)
        if name == 'DebugText' and align == 'r':
            x += self.TRK
        pen = x if align == 'l' else x - wid if align == 'r' else x - wid / 2.0
        pen += self.ox
        ytop = (math.floor(y - self.CAP[name] / 2.0 + .5) if cen else y + 13 - self.CAP[name]) + self.oy
        base = ytop - h[9]
        k = self.k
        a0 = (argb_ >> 24) / 255.0
        col = ((argb_ >> 16) & 255, (argb_ >> 8) & 255, argb_ & 255)
        for ch in s:
            r = by.get(ord(ch))
            if r is None:
                continue
            _tid, tw, th, px, _e = pg[r[1]]
            for yy in range(r[7]):
                for xx in range(r[6]):
                    a = px[4 * ((r[3] + yy) * tw + r[2] + xx) + 3] / 255.0 * a0
                    if a:
                        X, Y = int((pen + r[8] + xx) * k), int((base + r[9] + yy) * k)
                        for j in range(k):
                            for i in range(k):
                                self._blend(X + i, Y + j, col, a)
            pen += r[10]

    def save(self, path, crop=None):
        w, k = self.W * self.k, self.k
        if crop:
            x0, y0, x1, y1 = [int(v * k) for v in crop]
            rows = b''.join(bytes(self.img[3 * (y * w + x0):3 * (y * w + x1)]) for y in range(y0, y1))
            self.H._png(path, x1 - x0, y1 - y0, rows)
        else:
            self.H._png(path, w, self.Ht * k, bytes(self.img))


def avg_advance(cv, name='DebugText'):
    """the real average advance of the label font's capitals + digits (what the hook's LabelCharW estimates)"""
    h, by, _pg = cv._font(name)
    cs = [by[ord(c)][10] for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' if ord(c) in by]
    return sum(cs) / len(cs)


def board(cv, cw):
    """the dial board: three watches, the escape dial twice, a watch with the seconds hand, one without wear, three weapon circles with
    their label bars.  -> {element: pictures}"""
    L = 13
    cv.background()
    counts = {}

    def n_of(name, f):
        c0 = cv.count
        f()
        counts[name] = cv.count - c0
    for i, left in enumerate((330.0, 130.0, 40.0)):
        cv.ox = 60 + 90 * i - 1212.0
        cv.oy = 0.0
        n_of('watch %d:%02d' % (left // 60, left % 60), lambda l=left: W.draw_watch(cv, 1212, 50, l, L))
    cv.ox = 330 - 1137.0
    n_of('escape 65%', lambda: W.draw_escape(cv, 1137, 50, 0.65, L, 170))
    cv.ox = 395 - 1137.0
    n_of('escape 20%', lambda: W.draw_escape(cv, 1137, 50, 0.20, L, 171))
    cv.ox = 480 - 1212.0
    n_of('watch 2:10 + seconds hand', lambda: W.draw_watch(cv, 1212, 50, 130.0, L, seconds=True))
    cv.ox = 570 - 1212.0
    n_of('watch 2:10 no wear', lambda: W.draw_watch(cv, 1212, 50, 130.0, L, wear=False))
    cases = [(30, 30, 'ZASTAVA M85', '222', False, 30), (15, 30, 'AK-47', '183', False, 24), (3, 30, 'M9 BERETTA', '12', True, 9)]
    for i, (rounds, size, name, res, low, oth) in enumerate(cases):
        cv.ox = 100 + 205 * i - 1199.0
        cv.oy = 170 - 598.0

        def one(r=rounds, s=size, nm=name, rs=res, lo=low, o=oth):
            W.draw_weapon(cv, 1199, 598, r / float(s), r, o, 90, 65, L, low=lo or r / float(s) <= 0.25, gun_low=lo)
            W.draw_label(cv, nm, rs, cw, low=lo, layer=L)
        n_of('weapon %d/%d + label' % (rounds, size), one)
    return counts


def preview_dials(H, src, outdir, log=print):
    import os
    os.makedirs(outdir, exist_ok=True)
    k0 = Canvas(H, src, 640, 250, 1)
    cw = W.LABEL_CW
    log('label font: average advance %.2f px (capitals + digits); the hook estimates %.1f ([HUD] LabelCharW)' % (avg_advance(k0), cw))
    counts = None
    for k in (1, 2, 4):
        cv = Canvas(H, src, 640, 250, k)
        counts = board(cv, cw)
        cv.save(os.path.join(outdir, 'dials_%dx.png' % k))
        if k == 4:
            cv.save(os.path.join(outdir, 'dials.png'))
        log('wrote dials_%dx.png' % k)
    tot = 0
    for name, n in counts.items():
        log('  %-28s %3d pictures' % (name, n))
        tot += n
    # the label's real width against the estimate
    cv = Canvas(H, src, 8, 8, 1)
    for nm, rs in (('ZASTAVA M85', '222'), ('AK-47', '183'), ('M9 BERETTA', '12'), ('POLICE REVOLVER', '9')):
        L = W.label_layout(nm, rs, cw)
        real = cv.width('DebugText', nm) + cv.width('DebugText', rs) + cv.width('DebugText', '/')
        log('  label %-16s estimated bar %.0f px, text %.0f px (estimate %.0f)' % (nm + ' / ' + rs, W.LABEL_RIGHT - L['x0'], real, (len(nm) + len(rs) + 1) * cw))
    return counts
