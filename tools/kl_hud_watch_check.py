#!/usr/bin/env python3
r"""
kl_hud_watch_check.py - checks the WATCH LOOK of the hook against its model, offline (2026-10-12, cloud session). NOT the game.

    python kl_hud_watch_check.py compare <watch_c.txt>             every picture klhud.c queued (klhook/klwatch_test.c's dump) against
                                                                   tools/kl_hud_watch.py's draw_watch / draw_escape: slot, place, size,
                                                                   tint and layer; exit 1 on any difference
    python kl_hud_watch_check.py render <watch_c.txt> <out folder>  the hook's picture lists drawn with the BAKED textures of kl_hud.py
                                                                   (--watch 1): sheet.png (1x and 2x, dark and light ground) and one 6x
                                                                   close-up. Bilinear, no mips, plain alpha blending, call order inside a
                                                                   layer: an approximation of the game's renderer (GUESS), not a picture of it.
                                                                   Stock pictures (car icon 170) are drawn as stand-ins.
Dump: tools/run_harness_linux.sh klwatch_test > watch_c.txt  (or cl klwatch_test.c on Windows).
The ring painter (klhud.c klu_arc / klu_dabs, watch-look ratios) is ported here because the model leaves arcs to the canvas
(tools/kl_hud_wprev.py, which is NOT in the repository).
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RATIO_W = {0: 0.13, 1: 0.10}; SLOTS = {0: (123, 124, 125), 1: (126, 185, 190)}
class Cv:
    """records pictures as (slot, x, y, w, h, argb, layer); arc = the C ring painter"""
    def __init__(s): s.p = []
    def pic(s, n, x, y, w, h, argb, layer=13): s.p.append((n, x, y, w, h, argb & 0xffffffff, layer))
    def _dabs(s, cx, cy, r, ta, tb, stroke, argb, layer):           # port of klhud.c klu_dabs
        size = stroke / 0.90 * 0.97; ln = r * 6.2831853 * (tb - ta); step = min(stroke * 0.4, 2.5)
        ln = max(ln, 0); n = int(ln / step) + 1
        for k in range(n + 1):
            a = 6.2831853 * (ta + (tb - ta) * k / n)
            s.pic(113, cx + r * math.sin(a) - size / 2, cy - r * math.cos(a) - size / 2, size, size, argb, layer)
    def arc(s, cx, cy, r, fam, t0, t1, argb, layer):                 # port of klhud.c klu_arc (watch look)
        D = r / 0.40; stroke = RATIO_W[fam] * r; t0 = max(t0, 0); t1 = min(t1, 1.0)
        if not t1 > t0: return
        cur = t0
        for j in range(3):
            a, b = j / 3, (j + 1) / 3
            if t0 <= a + 1e-4 and t1 >= b - 1e-4:
                if cur < a - 1e-4: s._dabs(cx, cy, r, cur, a, stroke, argb, layer)
                s.pic(SLOTS[fam][j], cx - D / 2, cy - D / 2, D, D, argb, layer); cur = b
        if cur < t1 - 1e-4: s._dabs(cx, cy, r, cur, t1, stroke, argb, layer)
    def text(s, *a, **k): pass
    def gun(s, pic, x, y, size, argb, layer): s.pic(pic, x - size / 2, y - size / 2, size, size, argb, layer)


def load(path):
    cases = {}; cur = None
    for line in open(path):
        f = line.split()
        if not f: continue
        if f[0] == 'CASE': cur = (f[1], int(f[2]), float(f[3])); cases[cur] = []
        elif f[0] == 'P': cases[cur].append((int(f[1]), *map(float, f[2:6]), int(f[6], 16), int(f[7])))
    return cases


def model(kind, sec, val):
    import kl_hud_watch as W
    cv = Cv()
    if kind == 'watch': W.draw_watch(cv, 1212.0, 66.0, val, 13, seconds=bool(sec))
    else: W.draw_escape(cv, 1150.0, 66.0, val, 13, 170)
    return cv.p


def compare(path):
    bad = 0; cases = load(path)
    for (kind, sec, val), cp in cases.items():
        pp = model(kind, sec, val); diffs = []
        if len(pp) != len(cp): diffs.append('count: C %d, model %d' % (len(cp), len(pp)))
        for i, (a, b) in enumerate(zip(cp, pp)):
            if a[0] != b[0] or a[5] != b[5] or a[6] != b[6] or max(abs(a[k] - b[k]) for k in (1, 2, 3, 4)) > 0.02:
                diffs.append('#%d C %s model %s' % (i, a, tuple(round(v, 3) if isinstance(v, float) else v for v in b)))
                if len(diffs) > 4: break
        print('%-6s seconds=%d %7.2f: %s' % (kind, sec, val, 'MATCH (%d pictures)' % len(cp) if not diffs else 'DIFF'))
        for d in diffs: print('    ', d)
        bad += bool(diffs)
    print('RESULT: %s (%d of %d cases differ)' % ('PASS' if not bad else 'FAIL', bad, len(cases)))
    return 1 if bad else 0


def render_all(path, out):
    from PIL import Image, ImageDraw
    import kl_hud as H
    H.set_watch(1)
    tex = {}
    for slot, kind, w, h in H.EXTRAS:
        if kind in ('dab', 'disc', 'wear', 'bezel', 'stroke') or kind.startswith('arc'):      # 'dollar' needs Windows GDI: not used by the dials
            tex[slot] = Image.frombytes('RGBA', (w, h), bytes(H._extra_pixels(kind, w, h)))

    def standin():
        im = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((8, 22, 56, 44), 6, outline=(255, 255, 255, 255), width=4)
        d.ellipse((14, 38, 24, 48), fill=(255, 255, 255, 255)); d.ellipse((40, 38, 50, 48), fill=(255, 255, 255, 255))
        return im

    def render(pics, box, scale, bg):
        x0, y0, x1, y1 = box
        img = Image.new('RGBA', (int((x1 - x0) * scale), int((y1 - y0) * scale)), bg)
        for i in sorted(range(len(pics)), key=lambda i: (pics[i][6], i)):
            n, x, y, w, h, argb, layer = pics[i]
            sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
            s = (tex.get(n) or standin()).resize((sw, sh), Image.BILINEAR)
            a = (argb >> 24) & 255
            t = Image.new('RGBA', (sw, sh), ((argb >> 16) & 255, (argb >> 8) & 255, argb & 255, 0))
            t.putalpha(s.split()[3].point(lambda v: v * a // 255))
            img.alpha_composite(t, (round((x - x0) * scale), round((y - y0) * scale)))
        return img

    os.makedirs(out, exist_ok=True)
    cases = load(path)
    keys = [k for k in cases if k[0] == 'watch' and k[1] == 0] + [k for k in cases if k[0] == 'escape'][1:2]
    tiles = []
    for k in keys:
        box = (1170, 24, 1254, 108) if k[0] == 'watch' else (1108, 24, 1192, 108)
        for bg in ((52, 58, 66, 255), (196, 190, 178, 255)):
            tiles.append((render(cases[k], box, 1, bg).resize((168, 168), Image.NEAREST), render(cases[k], box, 2, bg)))
    sheet = Image.new('RGB', (168 * len(tiles), 342), (0, 0, 0))
    for i, (a, b) in enumerate(tiles):
        sheet.paste(a.convert('RGB'), (i * 168, 0)); sheet.paste(b.convert('RGB'), (i * 168, 174))
    sheet.save(os.path.join(out, 'sheet.png'))
    k = next((k for k in cases if k[0] == 'watch' and k[1] == 0 and abs(k[2] - 219) < 0.01), keys[0])
    render(cases[k], (1170, 24, 1254, 108), 6, (52, 58, 66, 255)).convert('RGB').save(os.path.join(out, 'watch_x6.png'))
    print('wrote', os.path.join(out, 'sheet.png'), '(top: 1x shown 2x; bottom: 2x; times', ', '.join('%.1f' % k[2] for k in keys), ')')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'compare': sys.exit(compare(a[1]))
    elif len(a) == 3 and a[0] == 'render': render_all(a[1], a[2])
    else: print(__doc__); sys.exit(2)
