"""Draws dmr.ico (the launcher exe's icon) with Pillow and the Windows Impact font: chalk 'KL' over a coral
brush bar on ink, the launcher's palette (INK #0C0C0D, CHALK #F3F0EA, CORAL #F0475A). No game art.
python make_icon.py -> dmr.ico (16..256) + dmr_preview.png"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
INK, CHALK, CORAL = (12, 12, 13, 255), (243, 240, 234, 255), (240, 71, 90, 255)
FONT = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'impact.ttf')


def draw(n=1024):
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, n - 1, n - 1), radius=n // 7, fill=INK)
    rnd = random.Random(1109)
    # torn brush bar under the letters: a slanted band with ragged ends
    y0, y1 = int(n * 0.64), int(n * 0.80)
    pts = [(int(n * 0.10), y0 + int(n * 0.03))]
    for i in range(1, 12):
        pts.append((int(n * (0.10 + 0.08 * i)), y0 - int(n * 0.012 * i) + rnd.randint(-n // 90, n // 90)))
    pts.append((int(n * 0.93), y0 - int(n * 0.12)))
    for i in range(11, 0, -1):
        pts.append((int(n * (0.10 + 0.08 * i)), y1 - int(n * 0.012 * i) + rnd.randint(-n // 90, n // 90)))
    pts.append((int(n * 0.08), y1 + int(n * 0.02)))
    d.polygon(pts, fill=CORAL)
    f = ImageFont.truetype(FONT, int(n * 0.66))
    box = d.textbbox((0, 0), 'KL', font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((n - w) // 2 - box[0], int(n * 0.10) - box[1]), 'KL', font=f, fill=CHALK)
    # light chipping on the letters (ink nicks), like the launcher's lettering
    for _ in range(14):
        x, y, r = rnd.randint(int(n * .15), int(n * .85)), rnd.randint(int(n * .1), int(n * .62)), rnd.randint(n // 220, n // 120)
        d.ellipse((x - r, y - r, x + r, y + r), fill=INK)
    return im


def main():
    big = draw()
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, 'dmr.ico'), sizes=[(s, s) for s in sizes])
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, 'dmr_preview.png'))
    print('wrote dmr.ico')


if __name__ == '__main__':
    main()
