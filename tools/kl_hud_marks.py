"""
kl_hud_marks.py - THE WORLD MARKERS in the HUD's watch look (2026-10-13; the owner, with a picture of the grey '$' over a dropped bag:
'new icon needed'; and of the van: 'for when u escape / in the van should be an icon', 'fix the van symbol ... it looks broken').

The stock markers are grey plastic buttons (slot 53 UI_KL_Communications_01#Loot: a rounded grey box with a dark '$', 128; 54 #Money:
a grey map pin with a '$', 128; 170 / 171 / 172 UI_KL2_Icons_01 BoardingCar / BoardingChopper / Money: small grey boxes, 64; read from
DM01 F01_Main.TEX on 2026-10-13 - NOTE re/hud_data.md's table is one slot early for 52..56: 53 is Loot, 54 Money). They are restyled as
the HUD's own pieces: an ink disc with the watch dial's worn rim (kl_hud_watch.disc_pixels), a broken chalk ring, and the glyph painted
on it - the loot ring's dragged green '$' (picture 116) for money, the stock small icons' car / chopper silhouettes (173 / 174) in chalk
for the escape markers. 54 keeps its pin shape (a point under the disc), so a marker still points at the bag on the floor.

Used by kl_hud.build_pictures under the owner's look (kl_hud.py all --look deadmen; --markers 0 leaves them stock). Same ids, same sizes,
written as uncompressed ABGR with one mip like the plates. Colour is baked: the stock pictures are drawn untinted (they are grey in the
file and grey on screen - GUESS from the owner's picture, so a tint would show here as a dimmer marker).
NOT LOADED IN THE GAME YET. Which of 53 / 54 is the dropped-bag marker is NOT established (re/hud_killfeed_plan.md K1); both are done.
"""
import math, random, struct

MARKER_SLOTS = {53: 'mk_loot', 54: 'mk_pin', 170: 'mk_car', 171: 'mk_chopper', 172: 'mk_cash'}
# 2026-10-14 (the owner, a picture of the escape vehicle's marker: 'the van icon on the van ... looks weird with the bar n stuff'): the vehicle
# marker in the world (ZGameplayTrackerDisplay, osd+0x10f8: icon + time + a progress bar) draws the GameplayTracker bars 161..164 and the
# Meter_BG frame 169, which the plate restyle (kl_hud.PLATE_SLOTS) had made outlined boxes with a chalk fill. Under the markers they become
# a quiet thin line: no frame, a faint full-length track and a 3 px chalk fill of 4/4 .. 1/4 of the width.
MARKER_SLOTS.update({169: 'trk_meter', 161: 'trk_bar0', 162: 'trk_bar1', 163: 'trk_bar2', 164: 'trk_bar3'})
GLYPH_SLOTS = {'mk_car': 173, 'mk_chopper': 174}          # stock 32 x 32 white silhouettes the escape markers borrow

INK = (12, 12, 13)
CHALK = (233, 230, 223)
GREEN_HI = (99, 166, 91)


# ---- reading a stock picture -------------------------------------------------------------------------------------------------
def _c565(c):
    return (((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)


def decode(entry):
    """a .TEX record -> (w, h, RGBA bytearray) of its first mip; DXT5, DXT1 and the uncompressed ABGR / RGBA records"""
    size, f1, _f2, _id, th, tw = struct.unpack_from('<I4s4sIHH', entry, 0)
    q = entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', entry, q)[0]
    b = entry[q + 4:q + 4 + n]
    fmt = f1[::-1]
    px = bytearray(4 * tw * th)
    if fmt in (b'ABGR', b'RGBA') or f1 in (b'ABGR', b'RGBA'):
        px[:] = b[:4 * tw * th]
        return tw, th, px
    dxt5 = fmt == b'DXT5' or f1 == b'DXT5'
    bs = 16 if dxt5 else 8
    o = 0
    for by in range(0, th, 4):
        for bx in range(0, tw, 4):
            if dxt5:
                a0, a1 = b[o], b[o + 1]
                ab = int.from_bytes(b[o + 2:o + 8], 'little')
                if a0 > a1:
                    al = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
                else:
                    al = [a0, a1] + [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]
                c0, c1, bits = struct.unpack_from('<HHI', b, o + 8)
            else:
                al, ab = None, 0
                c0, c1, bits = struct.unpack_from('<HHI', b, o)
            C0, C1 = _c565(c0), _c565(c1)
            if dxt5 or c0 > c1:
                cs = [C0, C1, tuple((2 * x + y) // 3 for x, y in zip(C0, C1)), tuple((x + 2 * y) // 3 for x, y in zip(C0, C1))]
            else:
                cs = [C0, C1, tuple((x + y) // 2 for x, y in zip(C0, C1)), (0, 0, 0)]
            for i in range(16):
                x, y = bx + i % 4, by + i // 4
                if x < tw and y < th:
                    k = (bits >> 2 * i) & 3
                    a = al[(ab >> 3 * i) & 7] if dxt5 else (0 if (not c0 > c1 and k == 3) else 255)
                    j = 4 * (y * tw + x)
                    px[j:j + 4] = bytes(cs[k]) + bytes((a,))
            o += bs
    return tw, th, px


# ---- alpha maps --------------------------------------------------------------------------------------------------------------
class Alpha:
    """an alpha map with bilinear sampling in [0, 1] x [0, 1]"""
    def __init__(self, w, h, a):
        self.w, self.h, self.a = w, h, a

    def at(self, u, v):
        x = u * self.w - 0.5; y = v * self.h - 0.5
        x0, y0 = int(math.floor(x)), int(math.floor(y)); fx, fy = x - x0, y - y0
        def g(i, j):
            return self.a[j * self.w + i] if 0 <= i < self.w and 0 <= j < self.h else 0
        return ((g(x0, y0) * (1 - fx) + g(x0 + 1, y0) * fx) * (1 - fy) + (g(x0, y0 + 1) * (1 - fx) + g(x0 + 1, y0 + 1) * fx) * fy) / 255.0


def _alpha_of(rgba, w, h):
    return Alpha(w, h, bytes(rgba[3::4]))


def _glyph_bbox(al):
    xs = [i % al.w for i, v in enumerate(al.a) if v > 40]; ys = [i // al.w for i, v in enumerate(al.a) if v > 40]
    if not xs:
        return 0.0, 0.0, 1.0, 1.0
    return min(xs) / al.w, min(ys) / al.h, (max(xs) + 1) / al.w, (max(ys) + 1) / al.h


# ---- the markers -------------------------------------------------------------------------------------------------------------
def tracker_pixels(kind, w, h):
    """RGBA of the vehicle marker's bar pictures: 'trk_meter' empty; 'trk_barK' a thin chalk line, (4 - K) / 4 of the width"""
    px = bytearray(4 * w * h)
    if kind == 'trk_meter':
        return px
    k = int(kind[-1]); cy = h // 2; x1 = int((w - 8) * (4 - k) / 4.0) + 4
    for y in range(cy - 2, cy + 3):
        for x in range(4, w - 4):
            j = 4 * (y * w + x)
            if cy - 1 <= y <= cy + 1 and x < x1:
                px[j:j + 4] = bytes((CHALK[0], CHALK[1], CHALK[2], 0xf0))
            elif y == cy + 2 and x < x1:
                px[j:j + 4] = bytes((INK[0], INK[1], INK[2], 0x90))
            elif y == cy:
                px[j:j + 4] = bytes((CHALK[0], CHALK[1], CHALK[2], 0x40))
    return px


def marker_pixels(kind, w, h, glyph=None, dollar=None):
    """RGBA bytes of marker `kind` (MARKER_SLOTS) at w x h. glyph: (w, h, RGBA) of the borrowed stock silhouette (car / chopper).
    dollar: RGBA of picture 116 (128 x 128); default = kl_hud's own bake of it (GDI: Windows only)."""
    if kind.startswith('trk_'):
        return tracker_pixels(kind, w, h)
    import kl_hud_watch as W
    import kl_hud as H
    S = min(w, h)
    disc_side = 128
    disc = Alpha(disc_side, disc_side, bytes(W.disc_pixels(disc_side)))       # the worn dial: alpha only
    pin = kind == 'mk_pin'
    # the disc's square (in pixels): a pin puts the disc at the top and the point under it
    dr = S * (0.40 if pin else 0.47)
    dcx, dcy = w / 2.0, (S * 0.43 if pin else h / 2.0)
    if kind in ('mk_loot', 'mk_pin', 'mk_cash'):
        d = dollar if dollar is not None else H._extra_pixels('dollar', 128, 128)
        ga = _alpha_of(d, 128, 128); gcol = GREEN_HI; gscale = 0.70 if pin else 0.78
    else:
        gw, gh, gpx = glyph
        ga = _alpha_of(gpx, gw, gh); gcol = CHALK; gscale = 0.66
    bx0, by0, bx1, by1 = _glyph_bbox(ga)
    gsz = max(bx1 - bx0, by1 - by0) or 1.0
    gside = 2 * dr * gscale                                          # the glyph's longer side in pixels
    rnd = random.Random(sum(map(ord, kind)) * 31 + w)
    bites = [(rnd.uniform(0, 6.28), rnd.uniform(0.10, 0.22)) for _ in range(3)]   # where the chalk ring is broken (angle, half width)
    px = bytearray(4 * w * h)
    SS = 3
    for y in range(h):
        for x in range(w):
            ink = chalk = gl = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    X = x + (sx + 0.5) / SS; Y = y + (sy + 0.5) / SS
                    u = (X - dcx) / (2 * dr) + 0.5; v = (Y - dcy) / (2 * dr) + 0.5
                    i_ = disc.at(u * (disc_side - 8) / disc_side + 4.0 / disc_side, v * (disc_side - 8) / disc_side + 4.0 / disc_side)
                    if pin:                                       # the point: a triangle from the disc's lower half to the bottom
                        ty = (Y - dcy) / (h - 1 - dcy)
                        if 0 < ty <= 1:
                            half = dr * 0.62 * (1 - ty)
                            i_ = max(i_, max(0.0, min(1.0, half - abs(X - dcx) + 0.5)))
                    ink += i_
                    r = math.hypot(X - dcx, Y - dcy); ang = math.atan2(X - dcx, -(Y - dcy)) % (2 * math.pi)
                    rw = max(1.0, S * 0.022)
                    c_ = max(0.0, min(1.0, rw - abs(r - dr * 0.86) + 0.5))
                    for a0, hw in bites:
                        da = abs((ang - a0 + math.pi) % (2 * math.pi) - math.pi)
                        if da < hw:
                            c_ *= max(0.0, da / hw * 1.6 - 0.6)
                    chalk += c_
                    gu = (X - dcx) / gside * gsz + (bx0 + bx1) / 2; gv = (Y - dcy) / gside * gsz + (by0 + by1) / 2
                    gl += ga.at(gu, gv)
            n = SS * SS
            ink, chalk, gl = ink / n, chalk / n * 0.80, gl / n
            # composite: ink (alpha 0.88), chalk ring over it, glyph over both
            a = ink * 0.88
            col = [c * a for c in INK]
            for layer_a, layer_c in ((chalk * (1 if ink > 0.05 else 0), CHALK), (gl, gcol)):
                col = [c * (1 - layer_a) + lc * layer_a for c, lc in zip(col, layer_c)]
                a = a * (1 - layer_a) + layer_a
            j = 4 * (y * w + x)
            if a > 0.002:
                px[j:j + 4] = bytes((min(255, int(col[0] / a + .5)), min(255, int(col[1] / a + .5)), min(255, int(col[2] / a + .5)), min(255, int(a * 255 + .5))))
    return px
