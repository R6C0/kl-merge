#!/usr/bin/env python3
r"""
kl_shop_swap.py - make a swapped weapon-shop row LOOK like the gun it hands over (2026-10-20; re/shop_swap_names.md). OFFLINE. NOT RUN IN THE GAME.

klhook/klshop.c makes a bought shop row hand over another gun ([Shop] Swap=row:item). The shop would still show the carrier's name and
picture. This tool bakes, into the level archive, what the swap needs to be honest:
  - the row's NAME and DESCRIPTION (.LOC, tools/kl_hud_shop.py SWAP_ITEMS),
  - the row's PICTURES: FAStatus_WeaponBig#NN (DXT1 512x256, 445x210 shown) and the 4 copies of FAStatus_WeaponNN (DXT5 128x128), painted as a
    chalk silhouette of the handed-over gun from the level's own HUD silhouette UI_Weapon_01#<name> (so no 3D render is needed; the same
    picture the HUD dial shows), in the chalk-on-ink look of the stage-2a cards (build/claude_stage/agents/shop2).
Price, rank, stars, lock and DLC gate stay the CARRIER row's: the table is hashed (0xbd1f68) and cannot change.

WHERE A MAP DECLARES ITS SWAPS (hook and tools agree): KLGuns.ini beside the archive,
    [Shop]
    Swap=13:52,16:33,32:49,35:47
klshop.c reads it for the map being loaded (klh_level_open -> klshop_level_open); no line = KLHook.ini [Shop] Swap (the default), an empty
line = no swap on that map. Every tool here reads the same line, so the baked names match what the hook hands over.
NOTE: tools\kl_map_guns.py / kl_guns.write_ini REWRITE KLGuns.ini and drop [Shop]: run `set` again after rebuilding a map. kl_buildprint hashes
KLGuns.ini without comments, so a [Shop] line changes the build code of that map.

    python kl_shop_swap.py parse "13:52,16:33"                     the rows, names, carrier price (reads the exe) and the pictures available
    python kl_shop_swap.py set <KLGuns.ini> "13:52,16:33"          write / replace the [Shop] Swap line (CRLF kept, nothing else touched)
    python kl_shop_swap.py bake <map folder> <out folder> [--swap=LINE] [--preview] [--pic=ITEM:alpha.png]
                                                                   <out>/<slot>_Main.zip (+ KLGuns.ini with the line) from the installed map; every
                                                                   zip member but the .TEX and the .LOC files is copied byte for byte
    python kl_shop_swap.py stage <out folder> [--maps=DM01] [--swap=LINE] [--game=<Dog Days folder>]
                                                                   bake each map into <out>\<map>\ + manifest.json + shopswap.ps1 + INSTALL/UNDO .bat
Never writes into the game folder. The stage command only READS the installed maps.
"""
import hashlib, json, os, random, struct, sys, zipfile, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hud_shop as S

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
DEFAULT_SWAP = '13:52,16:33,32:49,35:47'
# eFF2Item -> the HUD silhouette picture's name (UI_Weapon_01#<name>, names read in the DM01 .TEX 2026-10-20). Item 40 has none (GUESS: the
# HUD never shows it), so its picture is left as the carrier's and the report says so.
PIC_OVERRIDE = {}      # item -> path of a 128x128 RGBA PNG whose alpha is the silhouette (a replacement gun whose HUD picture is not the stock one's)
PIC_OF_ITEM = {33: 'Rifle_Type81', 47: 'MG_MiniMi_SPW', 49: 'Sn_Rem700', 50: 'RPG_7V', 52: 'Launcher_HK69A1'}
BIG_BOX = (34, 26, 411, 176)        # where the gun sits on the 445x210 shown part of the 512x256 card (cards.py of the stage-2a cards)


def pic_nn(row):
    """shop row -> the NN of FAStatus_WeaponBig#NN / FAStatus_WeaponNN#01..04 (Menu/online.xml PlayerIndex: 0-5 -> row+1, 6 -> 36, 7-35 -> row)."""
    return row + 1 if row < 6 else 36 if row == 6 else row


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- KLGuns.ini [Shop]
def set_ini(text, line):
    """KLGuns.ini text -> the text with [Shop] Swap=<line>. Only that section changes; the file's line ending is kept."""
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.replace('\r\n', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out, i, done = [], 0, False
    while i < len(lines):
        if lines[i].strip().lower() == '[shop]':
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith('['):
                i += 1                                     # the old section body goes
            continue
        out.append(lines[i]); i += 1
    if line is not None:
        out += ['[Shop]', 'Swap=' + line]
    return nl.join(out) + nl


# ---------------------------------------------------------------- finding the pictures' texture ids
def find_ids(z, stem, rows):
    """{row: (big texture id, small texture id)} from the scene: ZWINPIC entity (named by Menu/online.xml) -> .prm sprite chunk -> texture id.
    The same method as the stage-2a cardbake; every id must belong to that picture alone."""
    import collections
    import kl_hud_menu as HM, kl_scene, kl_prp, kl_prmgraph as G
    sc = kl_scene.read(z, stem); prp = kl_prp.Prp(z.read(stem + '.prp'))
    ents = list(sc.entities()); nodes = prp.nodes(); prm = G.read(z.read(stem + '.prm'), 'dd')
    if len(nodes) != len(ents) + 1:
        raise SystemExit('.prp / .gms do not line up')
    uses = collections.defaultdict(set); by = collections.defaultdict(set)
    for i, e in enumerate(ents):
        if e.tid != HM.ZWINPIC:
            continue
        own = e.name.decode('latin1')
        name = e.parent.name.decode('latin1') if own == 'Box' and e.parent is not None else own
        ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)]
        if len(ints) < 3:
            continue
        c = ints[-1]
        if not 0 < c < len(prm.chunks):
            continue
        d = prm.chunks[c]; n = struct.unpack_from('<I', d, 0)[0]
        if len(d) < 8 + 56 * n or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
            continue
        for s in struct.unpack_from('<%dI' % n, d, 8 + 40 * n):
            if 0 < s < len(prm.chunks) and len(prm.chunks[s]) == 32:
                tid = prm.u32(s, 4); uses[tid].add(name); by[name].add(tid)
    out = {}
    for r in rows:
        nn = pic_nn(r)
        bigname, fam = 'FAStatus_WeaponBig#%02d' % nn, 'FAStatus_Weapon%02d' % nn
        big = by.get(bigname, set())
        small = set().union(*[by.get('%s#%02d' % (fam, k), set()) for k in range(1, 5)])
        if len(big) != 1 or len(small) != 1:
            raise SystemExit('row %d: picture %s / %s not found in the scene (%s, %s)' % (r, bigname, fam, big, small))
        b, s = big.pop(), small.pop()
        if uses[b] != {bigname} or not all(u.startswith(fam + '#') for u in uses[s]):
            raise SystemExit('row %d: texture %d / %d is shared with another picture (%s / %s): not touched' % (r, b, s, uses[b], uses[s]))
        out[r] = (b, s)
    return out


# ---------------------------------------------------------------- painting
def _np():
    import numpy as np
    return np


def _silhouette(tex, item):
    """-> alpha 0..1 float (128, 128) of the HUD picture of that item, or None."""
    import kl_gunpics as P
    if item in PIC_OVERRIDE:
        from PIL import Image
        a = _np().asarray(Image.open(PIC_OVERRIDE[item]).convert('RGBA'))
        assert a.shape == (128, 128, 4), 'override picture must be 128x128'
        return a[:, :, 3].astype(_np().float32) / 255.0
    name = PIC_OF_ITEM.get(item)
    pics = P.pictures(tex)
    if not name or name not in pics:
        return None
    tid, x = pics[name]
    e = x.entry
    return _np().asarray(P.decode(P.tex_info(e), e)[:, :, 3], dtype=_np().float32) / 255.0


def _fit(alpha, box, size):
    """crop the silhouette to its bounding box, scale it into box (aspect kept, centred) on a size (W, H) canvas -> float coverage array (H, W)"""
    np = _np()
    from PIL import Image
    ys, xs = np.nonzero(alpha > 0.15)
    if not len(xs):
        return np.zeros((size[1], size[0]), np.float32)
    crop = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / crop.shape[1], bh / crop.shape[0])
    w, h = max(1, round(crop.shape[1] * s)), max(1, round(crop.shape[0] * s))
    im = Image.fromarray((crop * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    a = np.clip((a - 0.5) * 2.2 + 0.5, 0, 1)               # a 128 px shape scaled up is soft: pull the edge back in
    out = np.zeros((size[1], size[0]), np.float32)
    x0 = box[0] + (bw - w) // 2; y0 = box[1] + (bh - h) // 2
    out[y0:y0 + h, x0:x0 + w] = a
    return out


def big_card(alpha, seed):
    """512x256 RGBA bytes: ink ground with chalk dust, the gun in chalk (light on top, hatched in the shadow, dry-brush edge), a chalk underline.
    Only 445x210 of it is shown by the game (UV 0.869 x 0.82)."""
    import kl_hud_menu as HM
    np = _np()
    CH, IN = HM.CHALK, HM.INK
    W, H = 512, 256
    cov = _fit(alpha, BIG_BOX, (W, H))
    rnd = random.Random(seed)
    px = bytearray(4 * W * H)
    ys, xs = np.nonzero(cov > 0.05)
    y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, 1)
    edge_on = True; run = 0
    for y in range(H):
        for x in range(W):
            i = 4 * (y * W + x)
            if x >= 445 or y >= 210:
                px[i:i + 4] = bytes(IN) + b'\xff'; continue
            dust = 0.03 + (0.06 if rnd.random() > 0.985 else 0)
            c = [IN[k] + (CH[k] - IN[k]) * dust for k in range(3)]
            a = float(cov[y, x])
            if a > 0.01:
                if run <= 0:
                    edge_on = rnd.random() < 0.55; run = rnd.randint(2, 10)
                run -= 1
                if a < 0.9 and not edge_on:
                    a *= 0.1 + 0.4 * rnd.random()                      # dry brush: the chalk breaks up at the edge
                lv = (0.97 - 0.42 * (y - y0) / max(1, y1 - y0)) * (0.92 + 0.08 * rnd.random())
                if lv < 0.78 and (x + y) % 5 == 0:
                    lv *= 0.82                                         # hatching on the shadow side
                g = [CH[k] * lv for k in range(3)]
                c = [c[k] * (1 - a) + g[k] * a for k in range(3)]
            px[i:i + 3] = bytes(max(0, min(255, int(v))) for v in c); px[i + 3] = 255
    bw, bh = 300, 6
    st = HM._stroke_kit(bw, bh, True, True, rnd)
    ox, oy = (445 - bw) // 2, 190
    for y in range(bh):
        for x in range(bw):
            a = st[y * bw + x] / 255 * 0.5
            if a:
                i = 4 * ((oy + y) * W + ox + x)
                for k in range(3):
                    px[i + k] = int(px[i + k] * (1 - a) + CH[k] * a)
    return bytes(px)


def small_icon(alpha, box):
    """128x128 RGBA bytes: a chalk silhouette inside the stock icon's own box"""
    import kl_hud_menu as HM
    np = _np()
    CH = HM.CHALK
    cov = _fit(alpha, box, (128, 128))
    ys, xs = np.nonzero(cov > 0.05)
    y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, 1)
    px = bytearray(4 * 128 * 128)
    for y in range(128):
        for x in range(128):
            a = float(cov[y, x])
            if a > 0:
                lv = 0.97 - 0.42 * (y - y0) / max(1, y1 - y0)
                i = 4 * (y * 128 + x)
                px[i:i + 3] = bytes(int(CH[k] * lv) for k in range(3)); px[i + 3] = int(255 * min(1.0, a))
    return bytes(px)


def _c565(c):
    r, g, b = (max(0, min(255, int(v))) for v in c)
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def _un565(c):
    return ((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)


def encode_dxt1(px, w, h):
    """RGBA bytes -> DXT1 (4-colour blocks, c0 > c1; the card is opaque). The stage-2a cards' own encoder."""
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            idx = [4 * ((by + k // 4) * w + bx + k % 4) for k in range(16)]
            blk = [tuple(px[i:i + 3]) for i in idx]
            lum = [0.3 * r + 0.59 * g + 0.11 * b for r, g, b in blk]
            c0, c1 = _c565(blk[lum.index(max(lum))]), _c565(blk[lum.index(min(lum))])
            if c0 < c1:
                c0, c1 = c1, c0
            if c0 == c1:
                out += struct.pack('<HHI', c0, c1, 0); continue
            p, q = _un565(c0), _un565(c1)
            pal = [p, q, tuple((2 * x + y) // 3 for x, y in zip(p, q)), tuple((x + 2 * y) // 3 for x, y in zip(p, q))]
            bits = 0
            for k, c in enumerate(blk):
                d = [sum((a - b) ** 2 for a, b in zip(c, pc)) for pc in pal]
                bits |= d.index(min(d)) << (2 * k)
            out += struct.pack('<HHI', c0, c1, bits)
    return bytes(out)


# ---------------------------------------------------------------- the .TEX
def patch_pixels(tex_bytes, ids_data, expect):
    """splice new mip-0 data over the old pixel bytes of those texture ids; same length, same header. expect = {id: (fourcc, w, h)}"""
    import kl_gunpics as P
    out = bytearray(tex_bytes)
    for tid, data in ids_data.items():
        o = struct.unpack_from('<I', out, 0x20 + 4 * tid)[0]
        inf = P.tex_info(bytes(out[o:o + struct.unpack_from('<I', out, o)[0]]))
        # kl_gunpics.tex_info's 'w' is the record's FIRST u16, which is the HEIGHT (stage-2a cardbake: 'th, tw'); square pictures hide it
        if (inf['fourcc'], inf['h'], inf['w'], inf['mips']) != expect[tid] + (1,):
            raise SystemExit('texture %d is %s %dx%d x%d mips, not the expected %s' % ((tid, inf['fourcc'], inf['h'], inf['w'], inf['mips']) + (expect[tid],)))
        p = o + inf['mip0']
        n = struct.unpack_from('<I', out, p)[0]
        if n != len(data):
            raise SystemExit('texture %d: mip size %d != %d' % (tid, n, len(data)))
        out[p + 4:p + 4 + n] = data
    return bytes(out)


# ---------------------------------------------------------------- the archive
def rezip_raw_multi(src, dst, new):
    """archive src -> dst with the members in `new` ({name: bytes}) re-deflated; every other member copied byte for byte (local header +
    compressed data), same order, dates, attributes. Verified member by member."""
    if os.path.exists(dst) and os.path.samefile(src, dst):
        raise SystemExit('refusing to write over the input: %s' % dst)
    z = zipfile.ZipFile(src); il = z.infolist()
    f = open(src, 'rb'); f.seek(z.start_dir); cdraw = f.read()
    p, cents = 0, []
    for i in il:
        assert cdraw[p:p + 4] == b'PK\x01\x02' and i.flag_bits & ~0x800 == 0 and i.compress_type in (0, 8), i.filename
        nl, el, cl = struct.unpack('<HHH', cdraw[p + 28:p + 34])
        cents.append(bytearray(cdraw[p:p + 46 + nl + el + cl])); p += 46 + nl + el + cl
    eocd = cdraw[p:]
    assert eocd[:4] == b'PK\x05\x06', 'no plain EOCD (zip64?)'
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    tmp = dst + '.part'
    o = open(tmp, 'wb')
    for k, i in enumerate(il):
        f.seek(i.header_offset); lh = bytearray(f.read(30)); assert lh[:4] == b'PK\x03\x04'
        nl, el = struct.unpack('<HH', lh[26:30]); ne = f.read(nl + el); newoff = o.tell()
        if i.filename in new:
            assert i.compress_type == zipfile.ZIP_DEFLATED, i.filename
            data = new[i.filename]
            c = zlib.compressobj(6, zlib.DEFLATED, -15); comp = c.compress(data) + c.flush()
            crc = zlib.crc32(data) & 0xffffffff
            struct.pack_into('<III', lh, 14, crc, len(comp), len(data))
            o.write(lh); o.write(ne); o.write(comp)
            struct.pack_into('<III', cents[k], 16, crc, len(comp), len(data))
        else:
            o.write(lh); o.write(ne); left = i.compress_size
            while left:
                b = f.read(min(left, 8 << 20)); assert b; o.write(b); left -= len(b)
        struct.pack_into('<I', cents[k], 42, newoff)
    cdoff = o.tell()
    for c in cents:
        o.write(c)
    e = bytearray(eocd); struct.pack_into('<II', e, 12, o.tell() - cdoff, cdoff); o.write(e)
    o.close(); f.close()
    os.replace(tmp, dst)
    a, b = zipfile.ZipFile(src), zipfile.ZipFile(dst)
    ia, ib = a.infolist(), b.infolist()
    assert [x.filename for x in ia] == [x.filename for x in ib], 'member order/names differ'
    fa, fb = open(src, 'rb'), open(dst, 'rb')

    def raw(fh, i):
        fh.seek(i.header_offset + 26); nl, el = struct.unpack('<HH', fh.read(4)); fh.seek(i.header_offset)
        return fh.read(30 + nl + el + i.compress_size)
    for x, y in zip(ia, ib):
        for fld in ('date_time', 'compress_type', 'external_attr', 'create_system', 'flag_bits', 'extra', 'comment'):
            assert getattr(x, fld) == getattr(y, fld), (x.filename, fld)
        if x.filename in new:
            assert b.read(y.filename) == new[x.filename]
        else:
            assert x.CRC == y.CRC and x.compress_size == y.compress_size and raw(fa, x) == raw(fb, y), 'raw entry differs: ' + x.filename
    fa.close(); fb.close()
    assert b.testzip() is None


# ---------------------------------------------------------------- bake
def bake(mapdir, outdir, swap_text=None, preview=False, log=print):
    """installed map folder -> outdir/<slot>_Main.zip (+ KLGuns.ini with [Shop] Swap when the map had none). -> report dict"""
    import kl_texmat as T, kl_gunpics as P
    zp = next(os.path.join(mapdir, f) for f in sorted(os.listdir(mapdir)) if f.lower().endswith('_main.zip'))
    ini_in = os.path.join(mapdir, 'KLGuns.ini')
    swaps, src = S.read_swaps(ini_in, swap_text, log)
    if swap_text is not None and src == 'default':
        pass                                             # the map has no [Shop] line: the given line is both the hook's default and the bake
    if not swaps:
        raise SystemExit('no swap for %s (KLGuns.ini has no [Shop] Swap and --swap is empty)' % mapdir)
    z = zipfile.ZipFile(zp)
    stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]; texm = stem + '.TEX'
    old = z.read(texm); tex = T.read_tex(old)
    ids = find_ids(z, stem, sorted(swaps))
    try:
        mused = T.used_textures(T.read_mat(z.read(stem + '.MAT')))
        clash = [t for r in ids for t in ids[r] if t in mused]
        assert not clash, 'texture used by a material too: %s' % clash
    except AssertionError:
        raise
    except Exception as e:
        log('  (material texture use not read: %s)' % e)
    data, expect, rep = {}, {}, []
    os.makedirs(outdir, exist_ok=True)
    for r, item in sorted(swaps.items()):
        sil = _silhouette(tex, item)
        if sil is None:
            rep.append(dict(row=r, item=item, picture='left as the carrier row\'s (no HUD silhouette for item %d)' % item)); continue
        bigid, smallid = ids[r]
        e = tex.tex[smallid].entry
        stock_alpha = _np().asarray(P.decode(P.tex_info(e), e)[:, :, 3])
        ys, xs = _np().nonzero(stock_alpha > 40)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        bp = big_card(sil, 1000 * r + item)
        data[bigid] = encode_dxt1(bp, 512, 256); expect[bigid] = ('DXT1', 512, 256)
        sp = small_icon(sil, box)
        data[smallid] = P.encode_dxt5(_np().frombuffer(sp, _np().uint8).reshape(128, 128, 4)); expect[smallid] = ('DXT5', 128, 128)
        rep.append(dict(row=r, item=item, big=bigid, small=smallid, picture='UI_Weapon_01#' + PIC_OF_ITEM[item]))
        if preview:
            import kl_gunpics as G
            both = _np().zeros((256, 512 + 128 + 8, 3), _np().uint8) + 0x30
            both[:, :512] = _np().frombuffer(bp, _np().uint8).reshape(256, 512, 4)[:, :, :3]
            sa = _np().frombuffer(sp, _np().uint8).reshape(128, 128, 4).astype(_np().float32)
            both[:128, 520:] = (sa[:, :, :3] * sa[:, :, 3:] / 255 + 0x30 * (1 - sa[:, :, 3:] / 255)).astype(_np().uint8)
            G.write_png(os.path.join(outdir, 'card_row%02d_item%02d.png' % (r, item)), both)
    new = {}
    if data:
        new[texm] = patch_pixels(old, data, expect)
        t2 = T.read_tex(new[texm])
        assert sorted(t2.tex) == sorted(tex.tex) and len(new[texm]) == len(old)
    locs = {i.filename: z.read(i.filename) for i in z.infolist() if i.filename.lower().endswith('.loc')}
    files = dict(locs)
    changed = S.apply_level(files, log, guns=ini_in if os.path.isfile(ini_in) else None, swaps=swaps)
    for m in changed:
        new[m] = files[m]
    if not new:
        raise SystemExit('NOTHING CHANGED (already baked?)')
    dst = os.path.join(outdir, os.path.basename(zp))
    rezip_raw_multi(zp, dst, new)
    b = zipfile.ZipFile(dst)
    again = {n: b.read(n) for n in locs}
    assert S.apply_level(again, lambda s: None, guns=ini_in if os.path.isfile(ini_in) else None, swaps=swaps) == [], 'second name pass not idempotent'
    res = dict(archive=os.path.basename(zp), swaps={str(r): i for r, i in sorted(swaps.items())}, swap_source=src, changed=sorted(new),
               old_md5=md5(zp), new_md5=md5(dst), old_size=os.path.getsize(zp), new_size=os.path.getsize(dst), cards=rep)
    if src == 'default' and os.path.isfile(ini_in):
        txt = open(ini_in, encoding='latin1', newline='').read()
        line = ','.join('%d:%d' % x for x in sorted(swaps.items()))
        outini = os.path.join(outdir, 'KLGuns.ini')
        open(outini, 'w', encoding='latin1', newline='').write(set_ini(txt, line))
        res['klguns'] = dict(old_md5=md5(ini_in), new_md5=md5(outini), swap=line)
    return res


PS1 = r'''# shopswap.ps1 - the weapon shop names / pictures of swapped rows (tools/kl_shop_swap.py, __DATE__; re/shop_swap_names.md).
#   powershell -ExecutionPolicy Bypass -File shopswap.ps1 [-Undo] [-DryRun]
# WHY: klhook/klshop.c ([Shop] Enable=1, Swap=) makes a bought row hand over another gun; the shop must say which one.
# WHAT: replaces, per map, the level zip (only the .TEX pixels of the swapped rows' shop pictures and the language .LOC members differ) and
#   KLGuns.ini (gains a [Shop] Swap= line, which is what the hook reads for that map). Swap line: __SWAP__
__TABLE__
# SAFETY: refuses while a kl2.exe WITH THREADS runs (a zombie with none is ignored); each file is skipped unless the live one is exactly the
#   expected old one (or already the new one); the source is md5-checked; the live file is RENAMED to <name>.before-shopswap (never deleted);
#   read-back md5 after the copy, on failure the original is put back. -Undo puts each backup back if the live file is still the new one.
# Not touched: KL_PortBackup, stock files, KLHook.ini (set [Shop] Enable=1 there yourself to make the rows hand the guns over), dinput8.dll.
param([switch]$Undo, [switch]$DryRun,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-shopswap'
$files = @(
__FILES__
)
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
$run = @(Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 })
if ($run.Count -gt 0) {
  if ($DryRun) { 'WARNING: kl2.exe is running; a real install would refuse. Dry run only reads, going on.' }
  else { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
}
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$bad = 0
foreach ($x in $files) {
  $dst = Join-Path $Game ('KLExpansion\Maps\' + $x.m + '\' + $x.f)
  $bak = "$dst$tag"
  $src = Join-Path $PSScriptRoot ($x.m + '\' + $x.f)
  $name = $x.m + '\' + $x.f
  if (-not (Test-Path -LiteralPath $dst)) { "$name : SKIP, not installed"; $bad++; continue }
  $cur = md5 $dst
  if ($Undo) {
    if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $x.old) { "$name : already undone" } else { "$name : SKIP, no backup and live is $cur"; $bad++ }; continue }
    if ($cur -ne $x.new) { "$name : SKIP, live is $cur, not the shopswap build (changed since?). Backup left in place."; $bad++; continue }
    if ((md5 $bak) -ne $x.old) { "$name : SKIP, backup is not the expected original"; $bad++; continue }
    if ($DryRun) { "$name : would restore the original (dry run)"; continue }
    Remove-Item -LiteralPath $dst -Force
    Rename-Item -LiteralPath $bak -NewName $x.f
    if ((md5 $dst) -ne $x.old) { "$name : FAILED, restored file does not read back right!"; $bad++; continue }
    "$name : original restored, read back ok"
    continue
  }
  if ($cur -eq $x.new) { "$name : already installed"; continue }
  if ($cur -ne $x.old) { "$name : SKIP, live md5 is $cur, expected $($x.old). Another install in between? Not changed."; $bad++; continue }
  if (Test-Path -LiteralPath $bak) { "$name : SKIP, $bak already exists. Not changed."; $bad++; continue }
  if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $x.new) { "$name : SKIP, build file $src missing or changed"; $bad++; continue }
  if ($DryRun) { "$name : would install $($x.new.Substring(0,8)) (dry run)"; continue }
  Rename-Item -LiteralPath $dst -NewName ($x.f + $tag)
  $ok = $false
  try { Copy-Item -LiteralPath $src -Destination $dst; $ok = ((md5 $dst) -eq $x.new) } catch { $ok = $false }
  if (-not $ok) {
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    Rename-Item -LiteralPath $bak -NewName $x.f
    "$name : FAILED copy, original put back"; $bad++; continue
  }
  "$name : installed $($x.new.Substring(0,8)), read back ok (original kept as $($x.f)$tag)"
}
if ($bad) { "done with $bad problem(s), see above."; exit 4 }
'done.'
'''

BAT = '@echo off\r\nrem {what} - see shopswap.ps1 (stages from tools\\kl_shop_swap.py). Close the game first.\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0shopswap.ps1" {arg}\r\npause\r\n'


def stage(out, maps=('DM01',), swap_text=DEFAULT_SWAP, game=GAME, log=print):
    import datetime
    os.makedirs(out, exist_ok=True)
    manifest = dict(swap=swap_text, game=game, maps=[])
    rows, table = [], []
    for m in maps:
        mapdir = os.path.join(game, 'KLExpansion', 'Maps', m)
        od = os.path.join(out, m)
        log('== %s' % m)
        res = bake(mapdir, od, swap_text, True, log)
        res['map'] = m
        manifest['maps'].append(res)
        rows.append("  @{ m = '%s'; f = '%s'; old = '%s'; new = '%s' }" % (m, res['archive'], res['old_md5'], res['new_md5']))
        table.append('#     %s\\%s  %s -> %s' % (m, res['archive'], res['old_md5'][:8], res['new_md5'][:8]))
        if 'klguns' in res:
            k = res['klguns']
            rows.append("  @{ m = '%s'; f = 'KLGuns.ini'; old = '%s'; new = '%s' }" % (m, k['old_md5'], k['new_md5']))
            table.append('#     %s\\KLGuns.ini  %s -> %s' % (m, k['old_md5'][:8], k['new_md5'][:8]))
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    ps = PS1.replace('__FILES__', ',\r\n'.join(rows)).replace('__TABLE__', '\r\n'.join(table)).replace('__SWAP__', swap_text).replace('__DATE__', datetime.date.today().isoformat())
    open(os.path.join(out, 'shopswap.ps1'), 'w', encoding='latin1', newline='').write(ps.replace('\r\n', '\n').replace('\n', '\r\n'))
    open(os.path.join(out, 'INSTALL shopswap.bat'), 'w', newline='').write(BAT.format(what='INSTALL shopswap', arg=''))
    open(os.path.join(out, 'UNDO shopswap.bat'), 'w', newline='').write(BAT.format(what='UNDO shopswap', arg='-Undo'))
    return manifest


def main(a):
    if len(a) >= 2 and a[0] == 'parse':
        sw = S.parse_swap(a[1])
        try:
            import kl_shop_extra as X
            rows = X.rows()
        except Exception as e:
            rows = None; print('(carrier prices not read: %s)' % e)
        for r, it in sorted(sw.items()):
            price = '%7d' % rows[r][2] if rows else '?'
            print('row %2d %-16s price %s rank %s -> item %2d %-10s picture: %s' % (
                r, S.ROWS[r][1], price, rows[r][3] if rows else '?', it, S.SWAP_ITEMS.get(it, ('?',))[0], PIC_OF_ITEM.get(it, 'none (carrier picture stays)')))
        return 0
    if len(a) == 3 and a[0] == 'set':
        txt = open(a[1], encoding='latin1', newline='').read()
        S.parse_swap(a[2])
        open(a[1], 'w', encoding='latin1', newline='').write(set_ini(txt, a[2]))
        print('%s: [Shop] Swap=%s' % (a[1], a[2])); return 0
    opts = {k[2:].split('=')[0]: (k.split('=', 1)[1] if '=' in k else True) for k in a if k.startswith('--')}
    pos = [k for k in a if not k.startswith('--')]
    for k in a:
        if k.startswith('--pic='):
            it, png = k[6:].split(':', 1); PIC_OVERRIDE[int(it)] = png
    if len(pos) == 3 and pos[0] == 'bake':
        res = bake(pos[1], pos[2], opts.get('swap', DEFAULT_SWAP) if 'swap' in opts else None, bool(opts.get('preview')))
        print(json.dumps(res, indent=1)); return 0
    if len(pos) == 2 and pos[0] == 'stage':
        m = stage(pos[1], tuple(str(opts.get('maps', 'DM01')).split(',')), opts.get('swap', DEFAULT_SWAP), opts.get('game', GAME))
        for r in m['maps']:
            print(r['map'], r['archive'], r['old_md5'], '->', r['new_md5'], 'changed:', len(r['changed']), 'members')
        return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
