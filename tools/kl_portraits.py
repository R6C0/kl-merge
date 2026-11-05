#!/usr/bin/env python3
r"""
Pictures for the Heister page: the wardrobe's characters and masks as menu pictures (2026-10-09).

    python kl_portraits.py render <wardrobe build folder> <pictures folder>
        Draws the sixteen characters (face, outfit 0) and the eight masks of a `kl_chars.py wardrobe` build with
        tools\kl_view.py (software renderer: flat light, no alpha - hair cards and glasses are solid sheets) into
        <pictures folder>\char_01..16.png, mask_1..8.png and sheet.png (all of them, to look at).
        A picture with the same name that is already there is KEPT unless --force: a better one (a screenshot
        from the game, cut out) can simply be put in its place. Any PNG of the right size works (8-bit RGB / RGBA).
    python kl_portraits.py menu <pictures folder> <stock Scenes\kaneandlynch.zip> <out folder>
        Writes <out folder>\Overlay\Scenes\kaneandlynch.zip: the stock menu scene plus one picture entity per PNG.
        The stock archive is only READ; klslot.c's Overlay answers the game's open of Scenes\kaneandlynch.zip
        with the copy (give <game>\KLExpansion as <out folder>, or copy it there).
        klhook\mkoverlay.py puts the pictures on the page (it must be run with --pictures, see there).
    python kl_portraits.py gray <pictures folder> [<out folder>]
        The black and white heister cards of the hire page (hook, [Hire] PagePics=1): <pictures folder>\char_01..16.png ->
        <out folder>\kmi\char_01..16.kmi (KMI1, 445 x 210 = the big picture box, klmappool_ov.c's image file) and <out folder>\cards.png
        (contact sheet). The look of the white gun cards (kl_shop_cards.paint_white: dark ground, steel ring, hairline frame, red corner
        bracket), the heister in grey with the contrast pulled up, the name in white. <out folder> defaults to <pictures folder>.
        Needs numpy and Pillow (like kl_shop_cards.py).
    python kl_portraits.py check <a menu scene zip> [<stock zip>]
        Reads a built archive back: every picture entity -> picture chunk -> sprite -> texture, and that
        nothing of the stock scene moved except what has to (slot ids).

WHAT A MENU PICTURE IS (read from the stock menu scene; LevelPicture_H01, LevelPicture_F01, Icon_Heist)
  XML   <GuiElement Type="Graphic" Graphic="N">  names a scene ENTITY N (re\menus.md 2.7).
  .gms  N = ZWINGROUP (0x10002e, flags 0x3000000) under ROOT\LocalResources\Graphic, one child 'Box' = ZWINPIC
        (0x200046). Neither has a model, raw data or a list.
  .prp  ZWINPIC: ... ALIGNMENT_Top_Left DRAWMODE_OPACITY TYPE_Background, then three ints: width, height and the
        index of a picture chunk in the .prm (kl_prmgraph PRP_FIELDS ('ZWINPIC', 2)).
  .prm  picture chunk: u32 n, n x 40 bytes, u32 n, n x u32 sprite chunk, n x 12 bytes, padded to 16.
        A 40-byte tile = 10 x f32: centre x, -centre y, 0, 0, u extent, v extent, 0, width, height, and 0xffffffff
        (LevelPicture_H01 is 540 x 304 in six tiles: 512 + 28 wide, the 28 from a 32-wide texture with u extent
        0.875). The 12 bytes are {1, 0xcdcdcdcd, tile number}.
        sprite chunk (32 bytes): 01 01 02 00, u32 texture id, 0, 5, 00 c2 07 00, zeros - the same in every stock
        menu sprite but for the id.
  .TEX  one record per tile (kl_texmat): 1 mip, flags 0, scale 1.0, no name; DXT5 for the Arcade map pictures,
        'ABGR' (32 bits a pixel) for the lobby pictures and the icons.
Here: ONE tile per picture and an 'ABGR' texture whose size is the next powers of two (the tile's u / v extents
cut the picture out of it, as the stock 28-of-32 tiles do).
ASSUMPTIONS, none seen in the game yet:
  - 'ABGR' bytes are B, G, R, A in the file (D3DFMT_A8R8G8B8); if the pictures come out with red and blue
    swapped, set BGRA = False.
  - DRAWMODE_OPACITY blends with the texture's alpha (the stock icons are ABGR with this mode).
  - Graphic= finds an entity anywhere under LocalResources\Graphic by name (the resolver was not traced).
  - the scene's heap budget (header +0x1c) needs no raise for 2 x 27 more entities.
SLOT IDS: new entities under LocalResources stand before the menu's 3D room in the loader's slot order, so the
room's slot id changes; .oct trees, .rmi and .rmc are renumbered (kl_octree.remap_ids) as kl_graft does.
"""
import os, struct, sys, zlib, zipfile, time, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CHAR_SIZE = (256, 304)            # width, height on the page (the stock map picture is 540 x 304)
MASK_SIZE = (256, 256)
NCHAR, NMASK = 16, 12             # 8 heister masks + 4 Payday 2 plates (kl_chars.MASKS); a build with fewer masks renders what it has
BLANKS = ['KLPic_None1', 'KLPic_None2', 'KLPic_None3']      # one per use: an entity is one thing on the page
NAMES = BLANKS + ['KLPic_Char%02d' % n for n in range(1, NCHAR + 1)] + ['KLPic_Mask%d' % n for n in range(1, NMASK + 1)]
PARENT = ('LocalResources', 'Graphic')
MODEL = 'LevelPicture_H01'        # the entity pair that is copied
ZWINGROUP, ZWINPIC = 0x10002e, 0x200046
BGRA = False                      # the 'ABGR' record wants the bytes R, G, B, A: with the swap on, Lynch's skin was BLUE in the game (run PV1, 2026-10-09 23:55)
SS = 2                            # the renderer draws this many times larger and averages (edges, alpha)
CHAR_BOX = (72.0, 190.0)          # model units shown, bottom to top: waist to above the head
MASK_BOX = (146.0, 188.0)
ARMS = {'RIGHT_UPPER_ARM': ('z', 62), 'LEFT_UPPER_ARM': ('z', -62)}


# ------------------------------------------------------------------ PNG
def png_write(path, w, h, rgba):
    raw = b''.join(b'\0' + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    def ch(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))


def png_read(path):
    """-> (w, h, bytearray RGBA). 8-bit RGB or RGBA, not interlaced (what png_write and most tools write)."""
    d = open(path, 'rb').read()
    if d[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('%s is not a PNG' % path)
    o, idat, w = 8, b'', None
    while o < len(d):
        n, t = struct.unpack_from('>I4s', d, o)
        body = d[o + 8:o + 8 + n]; o += 12 + n
        if t == b'IHDR':
            w, h, depth, ctype, _c, _f, lace = struct.unpack('>IIBBBBB', body)
            if depth != 8 or ctype not in (2, 6) or lace:
                raise ValueError('%s: only 8-bit RGB / RGBA PNGs without interlace are read' % path)
        elif t == b'IDAT':
            idat += body
    bpp = 4 if ctype == 6 else 3
    raw = zlib.decompress(idat); stride = w * bpp
    out = bytearray(w * h * 4); prev = bytearray(stride); q = 0
    for y in range(h):
        f = raw[q]; line = bytearray(raw[q + 1:q + 1 + stride]); q += 1 + stride
        if f == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride): line[i] = (line[i] + ((line[i - bpp] if i >= bpp else 0) + prev[i]) // 2) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        elif f:
            raise ValueError('%s: PNG filter %d' % (path, f))
        if bpp == 4:
            out[y * w * 4:(y + 1) * w * 4] = line
        else:
            for x in range(w):
                out[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes(line[3 * x:3 * x + 3]) + b'\xff'
        prev = line
    return w, h, out


# ------------------------------------------------------------------ render
def _shot(V, p, mat, tx, root, variant, size, vbox, pose):
    """One look, front view -> RGBA bytearray of `size`, transparent where nothing was drawn."""
    w, h = size; W, H = w * SS, h * SS
    half = (vbox[1] - vbox[0]) * w / h / 2
    v = V.View(W, H, (-half, half, vbox[0], vbox[1]), 'front', bg=(0, 0, 0))
    for it in V.posed(p, mat, root, variant, pose, textures=tx):
        v.draw(*it)
    out = bytearray(w * h * 4); n2 = SS * SS
    for y in range(h):
        for x in range(w):
            r = g = b = a = 0
            for sy in range(SS):
                k = (y * SS + sy) * W + x * SS
                for sx in range(SS):
                    if v.z[k + sx] > -1e29:
                        a += 1; r += v.rgb[3 * (k + sx)]; g += v.rgb[3 * (k + sx) + 1]; b += v.rgb[3 * (k + sx) + 2]
            if a:
                out[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes((r // a, g // a, b // a, 255 * a // n2))
    return out


def render(build, out, force=False, log=print):
    import json
    import kl_view as V, kl_chars as C, kl_prmgraph as G, kl_texmat as T

    class Sharp(V.Textures):                          # kl_view decodes a 128-wide mip; here the 512 one
        def of(self, slot):
            if slot not in self.cache:
                t = None
                for name, val in T.texture_stages(self.mat.insts[slot]):
                    if name == 'mapDiffuse' and val[-1] in self.tex.tex:
                        t = V.decode(self.tex.tex[val[-1]].entry, 512)
                self.cache[slot] = t
            return self.cache[slot]

    os.makedirs(out, exist_ok=True)
    lv = C.Lv(build); p = G.read(lv['.prm'], 'dd'); mat = T.read_mat(lv['.MAT'])
    tx = Sharp(mat, T.read_tex(lv['.TEX']))
    rep = json.load(open(os.path.join(build, 'chars.json')))
    chars = rep['characters']
    if len(chars) != NCHAR:
        raise SystemExit('%s has %d characters, the page has %d' % (build, len(chars), NCHAR))
    jobs = [('char_%02d' % (i + 1), c['root'], C.variant_of(0, 0), CHAR_SIZE, CHAR_BOX, ARMS, c['name']) for i, c in enumerate(chars)]
    jobs += [('mask_%d' % m, chars[0]['root'], C.variant_of(0, m), MASK_SIZE, MASK_BOX, V.REST, 'mask %d' % m) for m in range(1, NMASK + 1)]
    for name, root, variant, size, vbox, pose, what in jobs:
        path = os.path.join(out, name + '.png')
        if os.path.exists(path) and not force:
            log('  %s: kept (already there)' % name); continue
        t0 = time.time()
        png_write(path, size[0], size[1], _shot(V, p, mat, tx, root, variant, size, vbox, pose))
        log('  %s: %s, %d x %d, %.0f s' % (name, what, size[0], size[1], time.time() - t0))
    sheet(out)


def sheet(folder, bg=(40, 44, 52)):
    """sheet.png: every picture of the folder on the menu's dark grey, to look at."""
    pics = [(n, png_read(os.path.join(folder, n + '.png'))) for n in _files() if os.path.exists(os.path.join(folder, n + '.png'))]
    if not pics:
        return
    cw, chh = CHAR_SIZE; cols = 8; rows = (len(pics) + cols - 1) // cols
    W, H = cw * cols, chh * rows; out = bytearray(bytes(bg + (255,)) * (W * H))
    for k, (n, (w, h, px)) in enumerate(pics):
        ox, oy = (k % cols) * cw, (k // cols) * chh
        for y in range(min(h, chh)):
            for x in range(min(w, cw)):
                r, g, b, a = px[(y * w + x) * 4:(y * w + x) * 4 + 4]
                o = ((oy + y) * W + ox + x) * 4
                out[o:o + 3] = bytes(((r * a + bg[0] * (255 - a)) // 255, (g * a + bg[1] * (255 - a)) // 255, (b * a + bg[2] * (255 - a)) // 255))
    png_write(os.path.join(folder, 'sheet.png'), W, H, out)


def _files():
    return ['char_%02d' % n for n in range(1, NCHAR + 1)] + ['mask_%d' % n for n in range(1, NMASK + 1)]


# ------------------------------------------------------------------ the menu scene
def _pow2(n):
    k = 8
    while k < n: k *= 2
    return k


def tex_record(tid, w, h, rgba):
    """An 'ABGR' texture record of the powers of two that hold w x h; the picture in its top left corner, the
    rest transparent. Layout from the stock 32 x 32 icons (record size 41 + 4 * w * h)."""
    tw, th = _pow2(w), _pow2(h)
    px = bytearray(tw * th * 4)
    for y in range(h):
        row = rgba[y * w * 4:(y + 1) * w * 4]
        if BGRA:
            row = bytearray(row); row[0::4], row[2::4] = row[2::4], row[0::4]
        px[y * tw * 4:y * tw * 4 + w * 4] = row
    body = struct.pack('<4s4sIHHIIfI', b'ABGR', b'ABGR', tid, th, tw, 1, 0, 1.0, 0) + b'\0' + struct.pack('<I', len(px)) + bytes(px)
    return struct.pack('<I', len(body) + 4) + body, tw, th


def sprite_chunk(tid):
    return bytes.fromhex('01010200') + struct.pack('<I', tid) + bytes.fromhex('00000000' '05000000' '00c20700') + bytes(12)


def pic_chunk(sprite, w, h, tw, th):
    c = struct.pack('<I', 1) + struct.pack('<9f', w / 2, -h / 2, 0, 0, w / tw, h / th, 0, w, h) + b'\xff\xff\xff\xff'
    c += struct.pack('<II', 1, sprite) + struct.pack('<III', 1, 0xcdcdcdcd, 0)
    return c + bytes(-len(c) % 16)


def _find(roots, path):
    kids = roots
    for name in path:
        e = next((k for k in kids if k.name.decode('latin1') == name), None)
        if e is None:
            raise SystemExit('the scene has no %s' % '\\'.join(path))
        kids = e.kids
    return e


def menu(pics_dir, stock, out, log=print):
    import kl_scene, kl_prp, kl_gms, kl_texmat as T, kl_prmgraph as G, kl_octree as O
    z = zipfile.ZipFile(stock)
    names = {i.filename.lower(): i for i in z.infolist()}
    stem = 'scenes/kaneandlynch'
    rd = lambda ext: z.read(names[stem + ext.lower()])
    pics = [(n, (8, 8, bytearray(8 * 8 * 4))) for n in BLANKS]
    for n, f in zip(NAMES[len(BLANKS):], _files()):
        path = os.path.join(pics_dir, f + '.png')
        if not os.path.exists(path):
            raise SystemExit('no %s: run "render" first' % path)
        w, h, px = png_read(path)
        want = CHAR_SIZE if f.startswith('char') else MASK_SIZE
        if (w, h) != want:
            raise SystemExit('%s is %d x %d, the page wants %d x %d' % (path, w, h, want[0], want[1]))
        pics.append((n, (w, h, px)))

    sc = kl_scene.read(z, 'Scenes/kaneandlynch')
    prp = kl_prp.Prp(rd('.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        raise SystemExit('.prp nodes and .gms entities do not line up')
    node_of = {id(e): nodes[i + 1] for i, e in enumerate(ents)}
    if any(e.name.decode('latin1') in NAMES for e in ents):
        raise SystemExit('%s already holds KLPic entities: give the STOCK archive' % stock)
    slot0 = sc.slots()
    parent = _find(sc.roots, PARENT); model = _find(sc.roots, PARENT + (MODEL,))
    if [k.tid for k in model.walk()] != [ZWINGROUP, ZWINPIC]:
        raise SystemExit('%s is not a ZWINGROUP with one ZWINPIC' % MODEL)
    mnode = node_of[id(model)]
    box_ints = [k for k, (op, _pl) in enumerate(mnode['children'][0]['props']) if op in (4, 9)]
    if [struct.unpack('<I', mnode['children'][0]['props'][k][1])[0] for k in box_ints[-3:]][:2] != [540, 304]:
        raise SystemExit('the ZWINPIC of %s does not end in width 540, height 304, chunk' % MODEL)

    tex = T.read_tex(rd('.TEX')); prm = G.read(rd('.prm'), 'dd')
    tid = max(tex.tex) + 1
    pnode = node_of[id(parent)]
    for name, (w, h, px) in pics:
        rec, tw, th = tex_record(tid, w, h, px)
        tex.tex[tid] = T.Texture(rec)
        sp = G.new_chunk(prm, sprite_chunk(tid)); pc = G.new_chunk(prm, pic_chunk(sp, w, h, tw, th))
        top = sc.graft(sc, model, parent, models=True)['top']
        top.name = name.encode('latin1')
        box = [dict(mnode['children'][0], props=list(mnode['children'][0]['props']), ctrls=[], children=[])][0]
        for k, v in zip(box_ints[-3:], (w, h, pc)):
            box['props'][k] = (box['props'][k][0], struct.pack('<I', v))
        pnode['children'].append({'props': list(mnode['props']), 'ctrls': [], 'children': [box]})
        tid += 1
    if mnode['ctrls'] or mnode['children'][0]['ctrls']:
        raise SystemExit('%s has controllers: not copied' % MODEL)

    slot1 = sc.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in ents}; ids[1] = 1
    moved = sum(1 for a, b in ids.items() if a != b)
    new = {'.gms': None, '.buf': None, '.prp': prp.serialize(), '.TEX': T.write_tex(tex), '.prm': G.write(prm),
           '.oct': O.remap_ids(O.Oct.parse(rd('.oct')), ids).pack(),
           '.rmc': O.remap_ids(O.RoomIndex.parse(rd('.rmc')), ids).pack()}
    if len(rd('.rmi')) != 32:                         # the menu's .rmi is an empty index (header only): no ids in it
        new['.rmi'] = O.remap_ids(O.RoomIndex.parse(rd('.rmi')), ids).pack()
    same = {1: 1}; same.update({v: v for v in ids})
    if O.remap_ids(O.Oct.parse(rd('.oct')), same).pack() != rd('.oct') or O.remap_ids(O.RoomIndex.parse(rd('.rmc')), same).pack() != rd('.rmc'):
        raise SystemExit('.oct / .rmc do not come back byte for byte from kl_octree: not renumbered')
    gms, buf = sc.write()
    new['.gms'], new['.buf'] = kl_gms.pack(gms) if _packed(rd('.gms')) else gms, buf

    dst = os.path.join(out, 'Overlay', 'Scenes'); os.makedirs(dst, exist_ok=True); path = os.path.join(dst, 'kaneandlynch.zip')
    if os.path.exists(path) and os.path.samefile(path, stock):
        raise SystemExit('refusing to write over the stock archive')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():                        # same members, same order, same names
            ext = os.path.splitext(i.filename)[1]
            data = new[ext] if i.filename.lower() == stem + ext.lower() and ext in new else z.read(i)
            n = zipfile.ZipInfo(i.filename, i.date_time); n.compress_type = i.compress_type; n.external_attr = i.external_attr
            o.writestr(n, data)
    log('%s: %d pictures added (%d entities -> %d, textures -> %d, chunks -> %d); %d slot ids renumbered' %
        (path, len(pics), len(ents), len(ents) + 2 * len(pics), len(tex.tex), len(prm.chunks) - 1, moved))
    bad = check(path, stock, log)
    if bad:
        raise SystemExit('the result fails its own check:\n  ' + '\n  '.join(bad))
    return path


def _packed(gms):
    import kl_gms
    try:
        return kl_gms.unpack(gms) != gms
    except Exception:
        return False


def check(path, stock=None, log=print):
    """Problems of a built menu scene ([] = none)."""
    import kl_scene, kl_prp, kl_texmat as T, kl_prmgraph as G, kl_octree as O
    bad = []
    z = zipfile.ZipFile(path); stem = 'Scenes/kaneandlynch'
    sc = kl_scene.read(z, stem); prp = kl_prp.Prp(z.read(stem + '.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    tex = T.read_tex(z.read(stem + '.TEX')); prm = G.read(z.read(stem + '.prm'), 'dd')
    if len(nodes) != len(ents) + 1:
        return ['%d .prp nodes for %d entities' % (len(nodes), len(ents))]
    bad += ['scene: ' + x for x in sc.check()]
    seen = {}
    for i, e in enumerate(ents):
        if e.tid != ZWINPIC:
            continue
        ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)]
        w, h, c = ints[-3:]
        nm = e.parent.name.decode('latin1')
        if not c and nm not in NAMES:                 # seven stock pictures have no chunk (Background_Kane ...)
            continue
        if not 0 < c < len(prm.chunks):
            bad.append('%s: picture chunk %d is not in the .prm' % (nm, c)); continue
        d = prm.chunks[c]; n = struct.unpack_from('<I', d, 0)[0]
        if len(d) < 8 + 56 * n or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
            bad.append('%s: chunk %d is not a picture chunk' % (nm, c)); continue
        for s in struct.unpack_from('<%dI' % n, d, 8 + 40 * n):
            if not 0 < s < len(prm.chunks) or len(prm.chunks[s]) != 32 or prm.chunks[s][:4] != b'\1\1\2\0':
                bad.append('%s: sprite %d is not a sprite chunk' % (nm, s)); continue
            t = prm.u32(s, 4)
            if t not in tex.tex:
                bad.append('%s: texture %d is not in the .TEX' % (nm, t))
        if nm in NAMES:
            seen[nm] = (w, h, c)
    missing = [n for n in NAMES if n not in seen]
    if missing:
        bad.append('no entity for %s' % ', '.join(missing))
    nk = [n for n in NAMES if sum(1 for e in ents if e.name.decode('latin1') == n) > 1]
    if nk:
        bad.append('named twice: %s' % ', '.join(nk))
    rooms = {s + 2 for e, s in sc.slots().items() if e in {a for a, _b in sc.pairs if a is not None}}
    for ext in ('.rmi', '.rmc'):
        if len(z.read(stem + ext)) == 32:
            continue
        for b in O.RoomIndex.parse(z.read(stem + ext)).boxes:
            if b.room not in rooms:
                bad.append('%s names slot id %d, which is not a room' % (ext, b.room))
    if stock:
        s = zipfile.ZipFile(stock)
        same = {'.gms', '.buf', '.prp', '.tex', '.prm', '.oct', '.rmi', '.rmc'}
        for i in s.infolist():
            if os.path.splitext(i.filename)[1].lower() in same and i.filename.lower().startswith('scenes/kaneandlynch.'):
                continue
            if z.read(i.filename) != s.read(i.filename):
                bad.append('%s differs from the stock member' % i.filename)
        ssc = kl_scene.read(s, stem); st = T.read_tex(s.read(stem + '.TEX')); sp = G.read(s.read(stem + '.prm'), 'dd')
        if any(tex.tex[k].entry != v.entry for k, v in st.tex.items()):
            bad.append('a stock texture changed')
        if prm.chunks[:len(sp.chunks)] != sp.chunks:
            bad.append('a stock .prm chunk changed')
        old = [(e.name, e.tid, e.ref, e.model) for e in ssc.entities()]
        now = [(e.name, e.tid, e.ref, e.model) for e in ents if e.name.decode('latin1') not in NAMES and not (e.parent and e.parent.name.decode('latin1') in NAMES)]
        if old != now:
            bad.append('the stock entities are not all there in their order')
    log('  check: %d of %d pictures found, %d problems' % (len(seen), len(NAMES), len(bad)))
    return bad

# ---------------------------------------------------------------- the hire page's black and white cards (hook klhirepic.c)
CARD = (445, 210)                 # the big picture box of the weapon / hire page, virtual pixels (klhirepic.h KHP_BW x KHP_BH)
CARD_NAMES = ('J.C.', 'Tommy', 'Pierre', 'Liam', 'Jean', 'Elwood', 'Bud', 'Mitchel',            # KLChar 1..8, kl_chars.DD_NAMES
              'Kane', 'Lynch', 'Ashkanan', 'Meldal', 'Red', 'Parker', 'Standen', 'Hutchison')   # KLChar 9..16, kl_chars.DM_NAMES (rank n = Hero_0n, see re/shop_hire.md section 11)


def _font(px):
    from PIL import ImageFont
    for f in ('C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(f, px)
        except Exception:
            pass
    return ImageFont.load_default()


def gray_card(n, png):
    """-> RGBA bytes of one card, CARD size. png = (w, h, RGBA bytearray) of the heister's picture (kl_portraits.render)."""
    import numpy as np
    from PIL import Image, ImageDraw
    import kl_shop_cards as C
    W_, H_ = CARD
    w, h, px = png
    a = np.frombuffer(bytes(px), np.uint8).reshape(h, w, 4).astype(np.float32)
    lum = (a[:, :, 0] * 0.30 + a[:, :, 1] * 0.59 + a[:, :, 2] * 0.11) / 255.0
    alpha = a[:, :, 3] / 255.0
    ys, xs = np.nonzero(alpha > 0.5)
    if len(xs):                                                           # crop to the figure, then fit its height into the card
        lum, alpha = lum[ys.min():ys.max() + 1, xs.min():xs.max() + 1], alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    lo, hi = np.percentile(lum[alpha > 0.5], (4, 96)) if (alpha > 0.5).any() else (0.0, 1.0)
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1) ** 0.9           # contrast pulled up, then to 55..100 % grey (reads as white-ish on the dark ground)
    grey = 0.40 + 0.60 * lum
    th = H_ - 18; tw = max(1, int(round(lum.shape[1] * th / float(lum.shape[0]))))
    g = np.asarray(Image.fromarray((grey * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS), np.float32)
    al = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS), np.float32) / 255.0
    out = C.ground_white((W_, H_), (W_, H_), 300 + n)                     # dark ground, smudges, dirty edges, specks (the gun cards' ground)
    steel = np.array(C.STEEL, np.float32)
    cx, cy = W_ * 0.64, H_ * 0.5
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    rr = np.sqrt(((xx - cx) * 0.62) ** 2 + (yy - cy) ** 2)                # the thin ring behind the figure
    for R, k in ((92.0, 0.26), (118.0, 0.10)):
        ring = np.clip(1.15 - np.abs(rr - R), 0, 1)
        out = out * (1 - ring * k)[:, :, None] + steel * (ring * k)[:, :, None]
    x0, y0 = int(round(cx - tw / 2.0)), 9
    sx0, sx1 = max(0, x0), min(W_, x0 + tw)
    A = np.zeros((H_, W_), np.float32); G = np.zeros((H_, W_), np.float32)
    A[y0:y0 + th, sx0:sx1] = al[:, sx0 - x0:sx1 - x0]; G[y0:y0 + th, sx0:sx1] = g[:, sx0 - x0:sx1 - x0]
    glow = C._blur(A, 7) * 0.16                                          # a faint bloom round the figure
    out = out * (1 - glow)[:, :, None] + steel * (glow * 0.9)[:, :, None]
    out = out * (1 - A[:, :, None]) + G[:, :, None] * A[:, :, None]
    x1, y1 = W_ - 5, H_ - 5                                               # the hairline frame and the red corner bracket (paint_white)
    for ys_, xs_ in ((slice(4, 5), slice(4, x1 + 1)), (slice(y1, y1 + 1), slice(4, x1 + 1)), (slice(4, y1 + 1), slice(4, 5)), (slice(4, y1 + 1), slice(x1, x1 + 1))):
        out[ys_, xs_] = out[ys_, xs_] * 0.5 + steel * 0.5
    red = np.array(C.RED, np.float32)
    out[4:7, 4:30] = out[4:7, 4:30] * 0.12 + red * 0.88
    out[4:26, 4:7] = out[4:26, 4:7] * 0.12 + red * 0.88
    im = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).convert('RGB')
    d = ImageDraw.Draw(im)
    name = CARD_NAMES[n - 1].upper()
    f = _font(30)
    d.text((22, H_ - 52), name, font=f, fill=tuple(C.WHITE_FILL))
    d.rectangle((22, H_ - 18, 22 + min(150, 12 * len(name)), H_ - 16), fill=tuple(C.RED))
    rgba = np.dstack([np.asarray(im), np.full((H_, W_), 255, np.uint8)])
    return bytes(rgba.tobytes())


def gray(pics, out=None, log=print):
    """pictures folder -> <out>/kmi/char_01..16.kmi + <out>/cards.png. A missing char_NN.png is skipped (logged)."""
    import kl_mappool
    out = out or pics
    kd = os.path.join(out, 'kmi'); os.makedirs(kd, exist_ok=True)
    W_, H_ = CARD; made = []
    for n in range(1, NCHAR + 1):
        src = os.path.join(pics, 'char_%02d.png' % n)
        if not os.path.exists(src):
            log('  char_%02d.png missing: skipped' % n); continue
        rgba = gray_card(n, png_read(src))
        open(os.path.join(kd, 'char_%02d.kmi' % n), 'wb').write(kl_mappool.kmi_bytes(W_, H_, rgba))
        made.append(rgba)
    cols = 4; rows = (len(made) + cols - 1) // cols
    if made:
        SW = W_ * cols; sh = bytearray(SW * H_ * rows * 4)
        for k, rg in enumerate(made):
            ox, oy = (k % cols) * W_, (k // cols) * H_
            for y in range(H_):
                o = ((oy + y) * SW + ox) * 4
                sh[o:o + W_ * 4] = rg[y * W_ * 4:(y + 1) * W_ * 4]
        png_write(os.path.join(out, 'cards.png'), SW, H_ * rows, sh)
    log('gray: %d cards -> %s (+ cards.png)' % (len(made), kd))
    return len(made)



if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) == 3 and a[0] == 'render':
        render(a[1], a[2], force='--force' in sys.argv)
    elif len(a) == 4 and a[0] == 'menu':
        menu(a[1], a[2], a[3])
    elif len(a) in (2, 3) and a[0] == 'gray':
        gray(a[1], a[2] if len(a) == 3 else None)
    elif len(a) in (2, 3) and a[0] == 'check':
        for b in check(a[1], a[2] if len(a) == 3 else None):
            print('  ' + b)
    else:
        print(__doc__); sys.exit(1)
