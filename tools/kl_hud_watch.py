"""
kl_hud_watch.py - THE WATCH LOOK of the HUD (2026-10-12; owner: 'clock needs a rehaul and the circle on the gun', 'make the clock more
like a watch like rolex hands and a bit more wear n tear', 'black bar bottom right to make gun name more pronounced and a / to
distinguish between gun name and ammo reserve').  Design = re/hud_hook.md section 14.

Two things live here and are used by tools/kl_hud.py:

  1. THE BAKED TEXTURES of the new look (alpha only, white; tinted at draw time):
        114 disc   a worn dial: hand-cut rim, low-frequency mottling, hairline scratches, specks, three rim bites   128 x 128
        112 wear   light scratches, one arc scuff, dust, a very soft glare wedge (drawn in chalk at alpha 0.30)     128 x 128
        115 bezel  60 minute pips (every 5th long, 4 shortened, 2 missing), a triangle at 12 on the bezel,
                   12 baton markers (one nicked) and a triangle at 12 on the face                                  128 x 128
     plus the ring families' new stroke widths (A 0.13, B 0.10 of the centre-line radius; overlaps 0.6 / 0.9 degrees).
     `pixels(kind, w, h)` -> RGBA bytes or None (not one of ours).  Geometry is in fractions of the picture's side so that the
     hook's constants (klhud.c KLW_*) and the preview agree: DISC_K = the disc's radius, BEZ_* = the bezel's.

  2. THE DRAWING of the watch, the escape dial, the weapon circle and the label bar as a LIST OF PICTURES, number for number the
     same as klhud.c klu_dials / klhud_weapon.c (the hook is C, this is the model it was written from and the preview draws).
     `draw_*` take a canvas `cv` with  cv.pic(slot, x, y, w, h, argb)  and  cv.text(...)  and return nothing; the canvas counts.

NOTHING OF IT HAS RUN IN THE GAME.  Guesses are marked GUESS.
"""
import math, random

# ---- geometry shared with the hook (all in the picture's own side, 1.0 = the side) -----------------------------------------
DISC_K = 60.0 / 128.0           # the disc's radius in a 128 texture (w / 2 - 4)
DAB_INK = 0.90                  # a dab's ink (diameter) as a part of its picture (kl_hud._dab_pixels: R = 0.45 w)
# bezel texture, centre = side / 2
BEZ_OUT = 0.470                 # outer end of every pip
BEZ_SHORT = 0.035               # a short pip's length
BEZ_LONG = 0.065                # every fifth
BEZ_TRI = (0.395, 0.490, 0.050) # the triangle on the bezel at 12: inner apex radius, outer radius, half width at the outer edge
BAT_IN, BAT_OUT = 0.245, 0.305  # the batons' radial span
FTRI = (0.225, 0.305, 0.032)    # the triangle on the face at 12: apex radius (inner), outer radius, half width at the outer edge

# ---- the look in screen pixels (virtual 1280 x 720) ----------------------------------------------------------------------------
WATCH_R_CASE = 36.2
WATCH_R_FACE = 34.0
WATCH_R_BEZEL = 33.0            # the pips' outer edge -> the bezel picture is drawn 2 * 33 / (2 * 0.47) = 70.2 px
WATCH_R_STROKE = 26.0           # the time-left stroke's centre line: inside the pips' band (24.3 .. 27.7 for family A's 0.13)
ESC_SCALE = 22.5 / 33.0         # the escape dial is the watch at this scale (50 px across)
WEAP_D = 107.0                  # the weapon circle (= 141 * 0.76)
WEAP_S = 0.76
WEAP_RING_R = 62.0 * WEAP_S     # 47.1
CASE_RGB, FACE_RGB = 0x07080A, 0x14161A
C_CHALK, C_CORAL, C_RED, C_ORANGE, C_BEZEL = 0xe9e6df, 0xf0475a, 0xe8303f, 0xff8a2a, 0x9a9a97
C_CASE_A, C_FACE_A = 0xe8, 0xdc          # GUESS: the case 0.91, the face 0.86 (the draft's disc was 0.61 over a bright scene: too see-through for a face)
C_WEAR_A = 0x4d                          # 0.30
C_PIPS_A = 0xb2                          # 0.70 (the watch; the escape dial 0.5)
C_PIPS_ESC_A = 0x80
C_DIM = 0x2b2c2e                         # the dim full ring under the weapon stroke (GUESS)


def argb(rgb, a=0xff):
    return (a << 24) | rgb


# ---- textures ---------------------------------------------------------------------------------------------------------------
def _line(a, w, x0, y0, x1, y1, val, half=0.55):
    """a hairline (alpha `val`) from (x0, y0) to (x1, y1), antialiased, max-merged"""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1.0
    for y in range(max(0, int(min(y0, y1) - 2)), min(w, int(max(y0, y1) + 3))):
        for x in range(max(0, int(min(x0, x1) - 2)), min(w, int(max(x0, x1) + 3))):
            t = max(0.0, min(1.0, ((x + .5 - x0) * dx + (y + .5 - y0) * dy) / L2))
            d = math.hypot(x + .5 - (x0 + t * dx), y + .5 - (y0 + t * dy))
            v = int(val * max(0.0, min(1.0, half + 0.5 - d)))
            if v > a[y * w + x]:
                a[y * w + x] = v


def disc_pixels(w):
    """114: the worn dial.  Alpha ~ 250 with mottling dips (low frequency, to ~225), ~15 hairline scratches and ~26 specks
    that are more transparent (a lighter trace over the dark face), 3 bites out of the rim, a hand-cut rim."""
    rnd = random.Random(1141)
    R = w / 2.0 - 4.0
    c = w / 2.0
    a = bytearray(w * w)
    bites = [(0.7, 2.6), (2.35, 2.2), (4.4, 2.4)]          # (angle, radius of the bite); centre on the rim
    ph = [rnd.uniform(0, 6.28) for _ in range(6)]
    for y in range(w):
        for x in range(w):
            dx, dy = x + .5 - c, y + .5 - c
            d = math.hypot(dx, dy)
            if d > R + 3:
                continue
            ang = math.atan2(dy, dx)
            rr = R + .28 * math.sin(ang * 5 + .4) + .2 * math.sin(ang * 11 + 1.9) + .12 * math.sin(ang * 23)
            sd = rr - d
            for (ba, br) in bites:
                bd = math.hypot(dx - R * math.cos(ba), dy - R * math.sin(ba)) - br
                if bd < sd:
                    sd = bd
            cov = max(0.0, min(1.0, sd + 0.5))
            if not cov:
                continue
            m = (math.sin(x * .071 + ph[0]) * math.sin(y * .058 + ph[1]) + math.sin((x + y) * .043 + ph[2]) * .7 + math.sin((x - 1.6 * y) * .035 + ph[3]) * .5) / 2.2
            v = 248 - 20 * (0.5 + 0.5 * m)
            a[y * w + x] = int(v * cov)
    # the scratches / specks are carved after the body: they LOWER the alpha
    hold = bytearray(w * w)
    for _ in range(15):
        ang = rnd.uniform(0, 6.283); rad = rnd.uniform(0.0, 0.8) * R
        x0, y0 = c + rad * math.cos(ang), c + rad * math.sin(ang)
        th = rnd.uniform(0, 3.1416); ln = rnd.uniform(5, 17)
        _line(hold, w, x0, y0, x0 + ln * math.cos(th), y0 + ln * math.sin(th), rnd.choice((36, 48, 62)))
    for _ in range(26):
        ang = rnd.uniform(0, 6.283); rad = math.sqrt(rnd.uniform(0, 1)) * R * 0.92
        x0, y0 = c + rad * math.cos(ang), c + rad * math.sin(ang); r = rnd.uniform(.7, 1.4)
        for y in range(int(y0 - 3), int(y0 + 4)):
            for x in range(int(x0 - 3), int(x0 + 4)):
                if 0 <= x < w and 0 <= y < w:
                    v = int(rnd.choice((50, 70, 90)) * max(0.0, min(1.0, r + .5 - math.hypot(x + .5 - x0, y + .5 - y0))))
                    if v > hold[y * w + x]:
                        hold[y * w + x] = v
    for i in range(w * w):
        if a[i] and hold[i]:
            a[i] = max(0, a[i] - hold[i])
    return a


def wear_pixels(w):
    """112: chalk wear drawn at alpha 0.30 over the face: 14 light scratches, one arc scuff, dust, a very soft glare wedge in the upper left."""
    rnd = random.Random(1121)
    c = w / 2.0
    a = bytearray(w * w)
    Rm = 0.455 * w
    for _ in range(14):
        ang = rnd.uniform(0, 6.283); rad = rnd.uniform(0.05, 0.85) * Rm
        x0, y0 = c + rad * math.cos(ang), c + rad * math.sin(ang)
        th = rnd.uniform(0, 3.1416); ln = rnd.uniform(6, 20)
        x1, y1 = x0 + ln * math.cos(th), y0 + ln * math.sin(th)
        if math.hypot(x1 - c, y1 - c) > Rm:
            continue
        _line(a, w, x0, y0, x1, y1, rnd.choice((90, 120, 150)), 0.6)
    # the arc scuff: a partial ring at 0.30 of the side, 36 degrees, ragged ends
    r0 = 0.30 * w
    for y in range(w):
        for x in range(w):
            dx, dy = x + .5 - c, y + .5 - c
            d = math.hypot(dx, dy)
            if abs(d - r0) > 2.4:
                continue
            t = (math.degrees(math.atan2(dx, -dy)) + 360) % 360          # clockwise from 12
            if 205 < t < 241:
                edge = min(t - 205, 241 - t) / 6.0
                v = int(120 * max(0.0, min(1.0, 1.4 - abs(d - r0) / 1.2)) * min(1.0, edge))
                if v > a[y * w + x]:
                    a[y * w + x] = v
    for _ in range(70):                                          # dust
        ang = rnd.uniform(0, 6.283); rad = math.sqrt(rnd.uniform(0, 1)) * Rm
        x, y = int(c + rad * math.cos(ang)), int(c + rad * math.sin(ang))
        v = rnd.choice((50, 70, 95))
        if 0 <= x < w and 0 <= y < w and v > a[y * w + x]:
            a[y * w + x] = v
    for y in range(w):                                           # the glare wedge: 292 .. 346 degrees, out to the rim, quadratic ramps
        for x in range(w):
            dx, dy = x + .5 - c, y + .5 - c
            d = math.hypot(dx, dy)
            if d > Rm or d < 3:
                continue
            t = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
            if 292 < t < 346:
                u = (t - 292) / 54.0
                f = math.sin(u * math.pi) ** 2 * (d / Rm) ** 1.5
                v = int(85 * f)
                if v > a[y * w + x]:
                    a[y * w + x] = v
    return a


def _poly(a, w, pts, val=255):
    """a filled convex polygon, antialiased by 3 x 3 supersampling"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    n = len(pts)

    def inside(px, py):
        s = 0
        for i in range(n):
            x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
            cr = (x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)
            s |= 1 if cr > 0 else 2
        return s != 3
    for y in range(max(0, int(min(ys)) - 1), min(w, int(max(ys)) + 2)):
        for x in range(max(0, int(min(xs)) - 1), min(w, int(max(xs)) + 2)):
            k = sum(inside(x + (i + .5) / 3, y + (j + .5) / 3) for i in range(3) for j in range(3))
            v = int(val * k / 9)
            if v > a[y * w + x]:
                a[y * w + x] = v


def _rad(c, w, ang_deg, r):
    t = math.radians(ang_deg)
    return (c + r * w * math.sin(t), c - r * w * math.cos(t))


def _bar(a, w, ang, r0, r1, wd, val=255, nick=False):
    """a radial bar from radius r0 to r1 (fractions of the side), width wd px, at angle ang (degrees clockwise from 12)"""
    c = w / 2.0
    p0, p1 = _rad(c, w, ang, r0), _rad(c, w, ang, r1)
    t = math.radians(ang)
    nx, ny = math.cos(t) * wd / 2, math.sin(t) * wd / 2
    _poly(a, w, [(p0[0] - nx, p0[1] - ny), (p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny)], val)
    if nick:                                                      # a bite out of one baton's edge
        mx, my = (p0[0] + p1[0]) / 2 + nx * .8, (p0[1] + p1[1]) / 2 + ny * .8
        for y in range(int(my - 3), int(my + 4)):
            for x in range(int(mx - 3), int(mx + 4)):
                if 0 <= x < w and 0 <= y < w:
                    d = math.hypot(x + .5 - mx, y + .5 - my)
                    if d < 1.7:
                        a[y * w + x] = int(a[y * w + x] * max(0.0, d - 1.0) / 0.7) if d > 1.0 else 0


def bezel_pixels(w):
    """115: 60 minute pips (every 5th long; 4 shortened; 2 missing), a triangle at 12 on the bezel, 12 batons on the face
    (one nicked), a triangle at 12 on the face"""
    a = bytearray(w * w)
    c = w / 2.0
    shortened = (13, 27, 38, 52); missing = (22, 47)
    for i in range(60):
        if i == 0 or i in missing:
            continue
        long_ = i % 5 == 0
        ln = BEZ_LONG if long_ else BEZ_SHORT
        if i in shortened:
            ln *= 0.62
        _bar(a, w, i * 6.0, BEZ_OUT - ln, BEZ_OUT, 3.6 if long_ else 2.2)
    ri, ro, hw = BEZ_TRI                                          # the bezel triangle: base on the outside, apex inward (a pointer to 12)
    _poly(a, w, [(c - hw * w, c - ro * w), (c + hw * w, c - ro * w), (c, c - ri * w)])
    for k in range(1, 12):
        _bar(a, w, k * 30.0, BAT_IN, BAT_OUT, 4.4 if k % 3 == 0 else 3.6, 255, nick=(k == 8))
    ai, ao, hw2 = FTRI                                            # the face triangle at 12: apex pointing outward? no - base inward, apex out like a dive watch's
    _poly(a, w, [(c - hw2 * w, c - ai * w), (c + hw2 * w, c - ai * w), (c, c - ao * w)])
    return a


def pixels(kind, w, h):
    """-> RGBA bytes for the textures of the new look, or None (kl_hud's own generators handle the rest)"""
    if kind == 'disc':
        a = disc_pixels(w)
    elif kind == 'wear':
        a = wear_pixels(w)
    elif kind == 'bezel':
        a = bezel_pixels(w)
    else:
        return None
    px = bytearray(b'\xff\xff\xff\0' * (w * h))
    px[3::4] = a
    return px


# ---- the drawing (mirrors klhud.c) ------------------------------------------------------------------------------------------
def disc(cv, cx, cy, r, rgb, a, layer):
    s = r / DISC_K
    cv.pic(114, cx - s / 2, cy - s / 2, s, s, argb(rgb, a), layer)


def dab(cv, x, y, ink, col, layer):
    s = ink / DAB_INK
    cv.pic(113, x - s / 2, y - s / 2, s, s, col, layer)


def hand(cv, cx, cy, deg, length, tail, prof, step, col, layer):
    """a hand as a run of dabs from -tail to length along the direction `deg` (clockwise from 12); prof(s) -> ink width"""
    t = math.radians(deg); dx, dy = math.sin(t), -math.cos(t)
    n = int((length + tail) / step + 0.5)
    for k in range(n + 1):
        s = -tail + (length + tail) * k / n
        dab(cv, cx + dx * s, cy + dy * s, prof(s), col, layer)


def hour_hand(cv, cx, cy, deg, col, face_col, layer):
    L, T = 19.0, 3.6
    cv_ring = 0.62 * L

    def prof(s):
        if s < 0:
            return 2.6
        return 3.0 if s <= 0.8 * L else 3.0 + (0.8 - 3.0) * (s - 0.8 * L) / (0.2 * L)
    hand(cv, cx, cy, deg, L, T, prof, 1.0, col, layer)
    t = math.radians(deg)
    x, y = cx + math.sin(t) * cv_ring, cy - math.cos(t) * cv_ring
    dab(cv, x, y, 7.0, col, layer)                                 # the Mercedes ring: a chalk dab ...
    dab(cv, x, y, 3.7, face_col, layer)                            # ... and the dial's colour over it


def sword_hand(cv, cx, cy, deg, col, layer):
    L, T = 29.0, 5.0

    def prof(s):
        if s < 0:
            return 2.2
        if s <= 0.55 * L:
            return 2.2 + (3.4 - 2.2) * s / (0.55 * L)
        return 3.4 + (1.4 - 3.4) * (s - 0.55 * L) / (0.45 * L)
    hand(cv, cx, cy, deg, L, T, prof, 1.2, col, layer)


def sec_hand(cv, cx, cy, deg, col, layer):
    hand(cv, cx, cy, deg, 30.4, 6.0, lambda s: 1.1, 1.1, col, layer)


def hub(cv, cx, cy, face_col, col, layer):
    dab(cv, cx, cy, 5.6, col, layer)
    dab(cv, cx, cy, 2.2, face_col, layer)


def watch_angles(left):
    """-> (hour hand degrees, sword hand degrees) for `left` seconds of the round"""
    sl = int(math.floor(left))
    if left > 60.0:
        sl %= 60
    return (360.0 - left / 60.0 * 30.0) % 360.0, ((60 - sl) * 6.0) % 360.0   # both run CLOCKWISE (review 2026-10-12)


def stroke_start(left):
    """fraction (clockwise from 12) where the time-left stroke begins; it runs to 12.  > 60 s: from the hour tip; last minute: from the sword tip"""
    if left <= 60.0:
        return (60 - int(math.floor(left))) * 6.0 / 360.0
    return max(0.0, 1.0 - left / 60.0 * 30.0 / 360.0)


def draw_dial_base(cv, cx, cy, k, layer, wear=True, pips_a=C_PIPS_A):
    """case, face, wear, bezel pips of a dial at scale k (1 = the watch)"""
    disc(cv, cx, cy, WATCH_R_CASE * k, CASE_RGB, C_CASE_A, layer - 4)
    disc(cv, cx, cy, WATCH_R_FACE * k, FACE_RGB, C_FACE_A, layer - 3)
    if wear:
        s = WATCH_R_FACE * k / DISC_K
        cv.pic(112, cx - s / 2, cy - s / 2, s, s, argb(C_CHALK, C_WEAR_A), layer - 3)
    sb = WATCH_R_BEZEL * k / BEZ_OUT
    cv.pic(115, cx - sb / 2, cy - sb / 2, sb, sb, argb(C_CHALK, pips_a), layer - 2)


def draw_watch(cv, cx, cy, left, layer, seconds=False, wear=True):
    """the round watch with `left` seconds on it.  `arc(cx, cy, r, fam, t0, t1, argb, layer)` is the canvas's (klu_arc)."""
    draw_dial_base(cv, cx, cy, 1.0, layer, wear)
    hdeg, sdeg = watch_angles(left)
    red = left <= 60.0
    sc = argb(C_RED if red else C_BEZEL)
    cv.arc(cx, cy, WATCH_R_STROKE, 0, stroke_start(left), 1.0, sc, layer - 1)
    hand_col = argb(C_CHALK)
    hour_hand(cv, cx, cy, hdeg, hand_col, argb(FACE_RGB), layer)
    sword_hand(cv, cx, cy, sdeg, argb(C_RED if red else C_CHALK), layer)
    if seconds:
        sec_hand(cv, cx, cy, (360.0 - (left % 60.0) * 6.0) % 360.0, argb(C_CORAL), layer)
    hub(cv, cx, cy, argb(FACE_RGB), hand_col, layer)


def draw_escape(cv, cx, cy, left, layer, icon, wear=True):
    """the escape dial: left = the part of the wait that is left (0..1); icon = the car / helicopter picture slot"""
    k = ESC_SCALE
    draw_dial_base(cv, cx, cy, k, layer, wear, C_PIPS_ESC_A)
    cv.arc(cx, cy, WATCH_R_STROKE * k, 0, 1.0 - left, 1.0, argb(C_ORANGE), layer - 1)
    cv.pic(icon, cx - 13.0, cy - 13.0, 26.0, 26.0, argb(C_CHALK), layer)


def draw_weapon(cv, cx, cy, frac, rounds, other_total, pic_act, pic_oth, layer, low=False, wear=True, gun_low=False):
    """the weapon circle (C's): case, face, wear, a dim full ring, the magazine as a stroke, the big count upper left, a hairline,
    the other gun below.  pic_* are the gun pictures (the canvas draws stand-ins)."""
    S = WEAP_S
    disc(cv, cx, cy, WEAP_D / 2.0, CASE_RGB, C_CASE_A, layer - 4)
    disc(cv, cx, cy, WEAP_D / 2.0 - 2.3, FACE_RGB, C_FACE_A, layer - 3)
    if wear:
        s = (WEAP_D / 2.0 - 2.3) / DISC_K
        cv.pic(112, cx - s / 2, cy - s / 2, s, s, argb(C_CHALK, C_WEAR_A), layer - 3)
    cv.arc(cx, cy, WEAP_RING_R, 1, 0.0, 1.0, argb(C_DIM), layer - 2)
    col = argb(C_CORAL if low else C_CHALK)
    f = max(0.0, min(1.0, frac))
    if f < 0.012 and rounds > 0:
        f = 0.012
    if f > 0:
        cv.arc(cx, cy, WEAP_RING_R, 1, 0.0, f, col, layer - 1)
    cv.gun(pic_act, cx + 28 * S, cy - 26 * S, 64 * S, argb(C_CORAL if gun_low else C_CHALK), layer)
    cv.text('H2', '%d' % rounds, cx - 7 * S, cy - 36 * S, col, 'r', False)
    cv.pic(181, cx - 87 * S / 2, cy + 2 * S - 0.5, 87 * S, 1.0, 0x49f3f0ea, layer - 1)           # the hairline across the middle (181 = the game's own white: a 1 px line must be clean; 111 breaks up at 1 px)
    cv.gun(pic_oth, cx + 21 * S, cy + 24 * S, 36 * S, argb(0x6f6c66), layer)
    cv.text('H3', '%d' % other_total, cx - 5 * S, cy + 18 * S, argb(0x6f6c66), 'r', False)


LABEL_RIGHT = 1247.0
LABEL_Y0, LABEL_Y1 = 654.0, 675.0
LABEL_PAD = 8.0
LABEL_BAR_A = 0xe6                # 0.90
LABEL_BAR_RGB = 0x070707
LABEL_NAME = 0xe9e6df
LABEL_CW = 11.6                   # the hook's [HUD] LabelCharW default: an ESTIMATED advance per character of the baked label font (measured by the preview)
LABEL_RES = 0xc9c5bd


def label_layout(name, reserve, cw, slash=True):
    """-> dict: bar x0, the right edges of the reserve / slash / name texts, using an estimated advance `cw` for a character (the
    hook has no text metrics; GUESS, the preview prints the real widths against it)"""
    rw = len(reserve) * cw * 0.93                                  # digits are narrower than the capitals (measured: 10.7 against 11.9 a character)
    res_r = LABEL_RIGHT - LABEL_PAD
    slash_r = res_r - rw - cw * 0.43
    slash_l = slash_r - cw * 0.78                                  # the slash glyph is 9 px with its tracking
    name_r = slash_l - cw * 0.43
    x0 = name_r - len(name) * cw - LABEL_PAD
    return dict(x0=x0, res_r=res_r, slash_r=slash_r, name_r=name_r)


def draw_label(cv, name, reserve, cw, low=False, slash=True, bar=True, layer=13, bar_slot=111):
    """the black bar with 'NAME / reserve'.  reserve = '' -> the name alone."""
    if reserve == '':
        x0 = LABEL_RIGHT - LABEL_PAD - len(name) * cw - LABEL_PAD
        if bar:
            cv.pic(bar_slot, x0, LABEL_Y0, LABEL_RIGHT - x0, LABEL_Y1 - LABEL_Y0, argb(LABEL_BAR_RGB, LABEL_BAR_A), layer - 1)
        cv.text('DebugText', name, LABEL_RIGHT - LABEL_PAD, (LABEL_Y0 + LABEL_Y1) / 2, argb(LABEL_NAME), 'r', True)
        return
    L = label_layout(name, reserve, cw, slash)
    if bar:
        cv.pic(bar_slot, L['x0'], LABEL_Y0, LABEL_RIGHT - L['x0'], LABEL_Y1 - LABEL_Y0, argb(LABEL_BAR_RGB, LABEL_BAR_A), layer - 1)
    cy = (LABEL_Y0 + LABEL_Y1) / 2
    cv.text('DebugText', reserve, L['res_r'], cy, argb(C_CORAL if low else LABEL_RES), 'r', True)
    cv.text('DebugText', '/' if slash else ' ', L['slash_r'], cy, argb(C_CORAL), 'r', True)
    cv.text('DebugText', name, L['name_r'], cy, argb(LABEL_NAME), 'r', True)
