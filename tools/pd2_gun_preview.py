#!/usr/bin/env python3
"""pd2_gun_preview.py - side-view pictures of a staged PD2 gun over the stock Type 81, both in Dog Days gun space (centimetres).
Offline helper of pd2_gun.py (1025d). x runs along the barrel, y is up; every triangle is drawn translucent, so the overlap shows."""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def part_mesh(p, o):
    """([(x, y, z)], [(a, b, c)]) of one rigid mesh object of a .prm (the first descriptor)."""
    import kl_map_guns as MG
    d = MG._descriptors(p, o)[0]
    nv, v, ix = p.u32(d, 0), p.chunks[p.u32(d, 4)], p.chunks[p.u32(d, 0x18)]
    n = struct.unpack_from('<H', ix, 2)[0]
    ii = struct.unpack_from('<%dH' % n, ix, 4)
    return ([struct.unpack_from('<3f', v, 40 * k) for k in range(nv)], [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)])


def side(layers, box, out, scale=9.0, marks=(), zone=None, title=''):
    """layers: [(pos, tris, (r, g, b), alpha)]; box = (x0, x1, y0, y1) cm; marks: [(x, y, label, (r,g,b))]; zone = (x0, x1, y0, y1)."""
    from PIL import Image, ImageDraw
    W, H = int((box[1] - box[0]) * scale), int((box[3] - box[2]) * scale)
    px = lambda x, y: ((x - box[0]) * scale, (box[3] - y) * scale)
    im = Image.new('RGBA', (W, H), (22, 22, 26, 255))
    d = ImageDraw.Draw(im)
    for gx in range(int(box[0] // 10) * 10, int(box[1]) + 1, 10):
        d.line([px(gx, box[2]), px(gx, box[3])], fill=(48, 48, 56, 255)); d.text(px(gx, box[2] + 1.2), str(gx), fill=(120, 120, 130, 255))
    for gy in range(int(box[2] // 10) * 10, int(box[3]) + 1, 10):
        d.line([px(box[0], gy), px(box[1], gy)], fill=(48, 48, 56, 255))
    if zone:
        a, b = px(zone[0], zone[3]), px(zone[1], zone[2])
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle([a, b], outline=(255, 255, 0, 255), fill=(255, 255, 0, 30))
        im = Image.alpha_composite(im, ov)
    for pos, tris, col, al in layers:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for a, b, c in tris:
            pts = [px(pos[k][0], pos[k][1]) for k in (a, b, c)]
            od.polygon(pts, fill=col + (al,), outline=col + (min(255, al * 2),))
        im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    for x, y, label, col in marks:
        q = px(x, y); d.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], outline=col + (255,), width=2); d.text((q[0] + 8, q[1] - 6), label, fill=col + (255,))
    if title:
        d.text((8, 6), title, fill=(230, 230, 230, 255))
    im.convert('RGB').save(out)
    return out


def _top(layers, box, out, scale=9.0, title=''):
    """x along the barrel (horizontal), z on the vertical axis: the same layers seen from above."""
    swapped = [([(q[0], q[2], q[1]) for q in pos], tris, col, al) for pos, tris, col, al in layers]
    return side(swapped, box, out, scale, title=title)


def stock_layers(live_dir, alpha=36):
    """Layers + marks of the stock Type 81 (blue body, orange sight, red magazine, green slide, grey hidden box) from a slot folder."""
    import kl_chars as C, kl_guns, kl_prmgraph as G, kl_map_guns as MG
    lv = C.Lv(live_dir); lv.beside, lv.side = {}, {}
    sc, _raw = lv.scene(); p = G.read(lv['.prm'], 'dd')
    root = C.person(sc, kl_guns.gun_node(sc, 'Rifle_Type81'))[0]
    sh = MG.shape(p, root)
    colour = {1: (70, 150, 255), 3: (255, 80, 60), 4: (80, 230, 110)}
    out = []
    for o in C.objects(p, root):
        pos, t = part_mesh(p, o)
        col = (130, 130, 130) if p.chunks[o][0x0e] == 16 else colour.get(p.u32(o, 0x3c), (255, 170, 60))
        out.append((pos, t, col, alpha))
    return out, sh['bones']['l hand attacher'][9:12], sh['bones']['w_bone_clip'][9:12]


def previews(live_dir, build_dir, outdir, log=print):
    """Side view of the staged AKM (yellow body, magenta magazine) over the stock Type 81, the grip zone, the left-hand attacher and the
    magazine bone; the AKM alone; the same from above. -> [paths]"""
    import kl_chars as C, kl_guns, kl_prmgraph as G, kl_map_guns as MG
    stock, lh, clip = stock_layers(live_dir)
    lv = C.Lv(build_dir); lv.beside, lv.side = {}, {}
    sc, _raw = lv.scene(); p = G.read(lv['.prm'], 'dd')
    root = C.person(sc, kl_guns.gun_node(sc, 'Rifle_Type81'))[0]
    new = []
    for o in C.objects(p, root):
        if p.chunks[o][0x0e] == 16:
            continue
        pos, t = part_mesh(p, o)
        new.append((pos, t, (255, 215, 60) if p.u32(o, 0x3c) == 1 else (255, 60, 220), 70))
    marks = [(lh[0], lh[1], 'l hand attacher', (255, 255, 255)), (clip[0], clip[1], 'w_bone_clip', (255, 120, 120)), (0, 0, 'origin', (160, 160, 160))]
    box = (-34, 82, -22, 22)
    ps = [side(stock + new, box, os.path.join(outdir, 'preview_side_over_type81.png'), marks=marks, zone=MG.GRIP_ZONE,
               title='blue = stock Type 81 body, red = its magazine (bone 3), grey = hidden box; yellow = PD2 AKM body, magenta = AKM magazine (bone 3); yellow frame = GRIP_ZONE'),
          side(new, box, os.path.join(outdir, 'preview_side_akm.png'), marks=marks, zone=MG.GRIP_ZONE, title='PD2 AKM alone (Dog Days gun space, cm)'),
          _top(stock + new, (-34, 82, -14, 14), os.path.join(outdir, 'preview_top_over_type81.png'), scale=9.0, title='from above (x along the barrel, z across)')]
    for x in ps:
        log('  wrote ' + x)
    return ps


if __name__ == '__main__':
    previews(sys.argv[1], sys.argv[2], sys.argv[3])
