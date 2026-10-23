#!/usr/bin/env python3
r"""
kl_shop_cards.py - ONE consistent look for all 36 weapon-shop cards, the star tiles and the lock tiles (2026-10-23; re/shop_ui_1023.md). OFFLINE.
NOT RUN IN THE GAME.

The shop (Menu/online.xml, FABuyWeaponsNewWeapon) shows per row a big card FAStatus_WeaponBig#NN (DXT1 512x256, 445x210 shown) and a small
icon FAStatus_WeaponNN#01..04 (DXT5 128x128), plus WeaponShopStar#01..06 and WeaponShopLock#01..08. Before this tool the page was a mix:
stock 3D art on 32 rows, flat chalk silhouettes on the four swapped rows (tools/kl_shop_swap.py, DM01 only).

The look (lead's pick): KEEP the stock 3D gun art, unify it. Per card:
  - the gun is cut out of the stock card (it sits on a coloured backdrop) by its distance from the card's own background colour,
  - placed on ONE clean dark vertical gradient backdrop, scaled so its bounding box fills the same frame on every card (same height class),
    centred, with a crisp 1-2 px light outline and a faint shadow underneath,
  - a subtle chalk edge only: a thin hairline frame and a short chalk underline (no hatching, no dry-brush, no silhouettes),
  - the small icon gets the same cut-out, tight in the stock icon's own box, with the same outline.
The four swapped rows have no stock art (the picture is the carrier's gun): they are drawn from the level's HUD silhouette of the handed gun
(UI_Weapon_01#<name>) shaded to read like the others (light-to-grey vertical ramp, same outline/frame), the best the data allows (GUESS: reads fine).
Same texture ids, sizes and formats: pixels are spliced over the old pixel bytes (tools/kl_shop_swap.patch_pixels). Tiles that another entity
also uses are NOT touched (picture_uses check, as in kl_shop_swap.find_ids).

    python kl_shop_cards.py sheet <archive.zip> <out.png>          contact sheet of the 36 big + 36 small + star + lock tiles (read only)
    python kl_shop_cards.py restyle <archive.zip> <out.zip> [--swap=LINE] [--preview=<png>]
                                                                   rebuilt archive: only the .TEX (and, with --swap, the .LOC) members change
Never writes into the game folder.
"""
import json, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_shop_swap as W

WEAPON_ROWS = tuple(range(36))


def _np():
    import numpy as np
    return np


# ---------------------------------------------------------------- finding every shop picture in a level
def scene_pics(z, stem):
    """-> (by, uses): by[picture entity name] = {texture ids}, uses[texture id] = {picture entity names}. Same walk as kl_shop_swap.find_ids
    (ZWINPIC entity -> .prm sprite chunk -> texture id), but for every picture of the level."""
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
    return by, uses


def shop_tiles(z, stem):
    """-> dict(big={row: tid}, small={row: tid}, star={tid}, lock={tid}, skipped=[(what, why)]). A tile is listed only when the picture
    names of the family are the only users of its texture id."""
    by, uses = scene_pics(z, stem)
    out = dict(big={}, small={}, star=set(), lock=set(), skipped=[])
    for r in WEAPON_ROWS:
        nn = W.pic_nn(r)
        bigname, fam = 'FAStatus_WeaponBig#%02d' % nn, 'FAStatus_Weapon%02d' % nn
        big = by.get(bigname, set())
        small = set().union(*[by.get('%s#%02d' % (fam, k), set()) for k in range(1, 5)])
        if len(big) != 1 or len(small) != 1:
            out['skipped'].append(('row %d' % r, 'picture not found (%s, %s)' % (big, small))); continue
        b, s = next(iter(big)), next(iter(small))
        if uses[b] != {bigname} or not all(u.startswith(fam + '#') for u in uses[s]):
            out['skipped'].append(('row %d' % r, 'texture %d/%d shared with %s / %s' % (b, s, uses[b], uses[s]))); continue
        out['big'][r] = b; out['small'][r] = s
    for key, fam, n in (('star', 'WeaponShopStar', 6), ('lock', 'WeaponShopLock', 8)):
        ids = set().union(*[by.get('%s#%02d' % (fam, k), set()) for k in range(1, n + 1)])
        bad = [t for t in ids if not all(u.startswith(fam + '#') for u in uses[t])]
        if not ids or bad:
            out['skipped'].append((key, 'tiles %s missing or shared (%s)' % (sorted(ids), [uses[t] for t in bad]))); continue
        out[key] = ids
    return out


def decode_tile(tex, tid):
    """-> (RGBA uint8 array, info dict) of texture id `tid` (mip 0)"""
    import kl_gunpics as P
    e = tex.tex[tid].entry
    inf = P.tex_info(e)
    # tex_info's 'w' is the record's FIRST u16, which is the HEIGHT (see kl_shop_swap.patch_pixels): swap for non-square pictures
    return P.decode(dict(inf, w=inf['h'], h=inf['w']), e), dict(inf, w=inf['h'], h=inf['w'])


# ---------------------------------------------------------------- contact sheet
VIS_W, VIS_H = 445, 210                 # the part of the 512x256 big card the game shows


def _over(a, bg):
    """RGBA uint8 -> RGB uint8 over a flat grey background"""
    np = _np()
    al = a[:, :, 3:4].astype(np.float32) / 255.0
    return (a[:, :, :3] * al + bg * (1 - al)).astype(np.uint8)


def sheet(archive, png, cols=4, scale=0.6, log=print):
    """contact sheet of every shop tile of an archive: per row the big card (visible part) and the small icon over dark grey, then the star and
    lock tiles. Reads only."""
    import kl_texmat as T
    from PIL import Image, ImageDraw
    np = _np()
    z = zipfile.ZipFile(archive)
    stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]
    tex = T.read_tex(z.read(stem + '.TEX'))
    t = shop_tiles(z, stem)
    bw, bh = round(VIS_W * scale), round(VIS_H * scale)
    cw, ch = bw + 84 + 12, bh + 18
    n = len(t['big'])
    rows = (n + cols - 1) // cols
    img = Image.new('RGB', (cols * cw, rows * ch + 90), (70, 70, 74))
    dr = ImageDraw.Draw(img)
    for k, r in enumerate(sorted(t['big'])):
        big, _ = decode_tile(tex, t['big'][r]); small, _ = decode_tile(tex, t['small'][r])
        x, y = (k % cols) * cw, (k // cols) * ch
        img.paste(Image.fromarray(_over(big, 40)[:VIS_H, :VIS_W]).resize((bw, bh), Image.LANCZOS), (x + 4, y + 14))
        img.paste(Image.fromarray(_over(small, 40)).resize((76, 76), Image.LANCZOS), (x + bw + 8, y + 14))
        dr.text((x + 4, y + 2), 'row %d' % r, fill=(255, 255, 0))
    y0 = rows * ch + 6
    for k, key in enumerate(('star', 'lock')):
        for tid in sorted(t[key]):
            a, _ = decode_tile(tex, tid)
            img.paste(Image.fromarray(_over(a, 40)).resize((64, 64), Image.NEAREST), (10 + k * 90, y0 + 14))
            dr.text((10 + k * 90, y0), '%s %d' % (key, tid), fill=(255, 255, 0))
    for what, why in t['skipped']:
        log('skipped %s: %s' % (what, why))
    img.save(png)
    log('%s: %d rows, star %s lock %s -> %s' % (archive, n, sorted(t['star']), sorted(t['lock']), png))
    return t


# ---------------------------------------------------------------- image helpers (PIL + numpy only; no scipy / cv2 on this machine)
def _img(a):
    """float 0..1 (H, W) -> PIL 'L'"""
    from PIL import Image
    np = _np()
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'L')


def _arr(im):
    return _np().asarray(im, _np().float32) / 255.0


def _dil(a, r):
    """grey dilation by a (2r+1) square"""
    from PIL import ImageFilter
    return _arr(_img(a).filter(ImageFilter.MaxFilter(2 * r + 1)))


def _ero(a, r):
    from PIL import ImageFilter
    return _arr(_img(a).filter(ImageFilter.MinFilter(2 * r + 1)))


def _blur(a, r):
    from PIL import ImageFilter
    return _arr(_img(a).filter(ImageFilter.GaussianBlur(r)))


def _components(mask):
    """label the 8-connected true pixels of a bool array -> (labels int32, areas list indexed by label); python flood fill, fine at 1/2 resolution"""
    np = _np()
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32); areas = [0]
    m = mask.tolist(); L = [[0] * w for _ in range(h)]
    n = 0
    for y0 in range(h):
        for x0 in range(w):
            if m[y0][x0] and not L[y0][x0]:
                n += 1; L[y0][x0] = n; st = [(y0, x0)]; cnt = 0
                while st:
                    y, x = st.pop(); cnt += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < h and 0 <= xx < w and m[yy][xx] and not L[yy][xx]:
                                L[yy][xx] = n; st.append((yy, xx))
                areas.append(cnt)
    return np.array(L, np.int32), areas


def _fill_holes(mask):
    """fill every background pocket of a bool mask that does not touch the image border (half resolution flood fill)"""
    np = _np()
    from PIL import Image
    half = mask[::2, ::2]
    lab, areas = _components(~half)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    inner = np.array([i not in border and i != 0 for i in range(len(areas))], bool)[lab]
    full = np.asarray(Image.fromarray((inner * 255).astype(np.uint8), 'L').resize((mask.shape[1], mask.shape[0]), Image.NEAREST)) > 127
    return mask | full


def _clean(fg):
    """close small gaps (highlights on the gun are lighter than the table), fill pockets, keep the main body"""
    np = _np()
    c = _ero(_dil(fg.astype(np.float32), 5), 5) > 0.5
    c = _fill_holes(c)
    c = _dil(_ero(c.astype(np.float32), 4), 4) > 0.5         # open: cut the thin bridges to table shadows, tags and notes
    return _keep_gun(c, 0.6)


def _keep_gun(mask, rel=0.3):
    """keep the largest blob of a bool mask (grown by 3 px first so a scope or a magazine joins the gun) and any blob of at least `rel` of its
    area; everything else (tags, pens, notes, the chalk underline, bokeh) goes. -> bool mask (same size)"""
    np = _np()
    half = mask[::2, ::2]
    grown = _dil(half.astype(np.float32), 3) > 0.5
    lab, areas = _components(grown)
    if len(areas) < 2:
        return mask & False
    big = max(range(1, len(areas)), key=lambda i: areas[i])
    keep = np.zeros(len(areas), bool)
    for i in range(1, len(areas)):
        keep[i] = areas[i] >= rel * areas[big]
    k = keep[lab]
    from PIL import Image
    full = _arr(Image.fromarray((k * 255).astype(np.uint8), 'L').resize((mask.shape[1], mask.shape[0]), Image.NEAREST)) > 0.5
    return mask & _dil(full.astype(np.float32), 3).astype(bool)


# ---------------------------------------------------------------- reading the art of a tile
def classify(rgba):
    """'photo' = stock card (light, lit backdrop, 3D gun photograph); 'flat' = a flat light gun on an ink ground (a stage-2a look card or an
    old swap card); the test is the mean luminance of the four visible corners."""
    np = _np()
    f = rgba[:VIS_H, :VIS_W, :3].astype(np.float32)
    lum = 0.3 * f[:, :, 0] + 0.59 * f[:, :, 1] + 0.11 * f[:, :, 2]
    c = np.mean([lum[:16, :16].mean(), lum[:16, -16:].mean(), lum[-16:, :16].mean(), lum[-16:, -16:].mean()])
    return 'photo' if c > 50 else 'flat'


def _to_full(m_half, shape):
    """bool half-resolution mask -> bool full-resolution (nearest)"""
    np = _np()
    from PIL import Image
    return np.asarray(Image.fromarray((m_half * 255).astype(np.uint8), 'L').resize((shape[1], shape[0]), Image.NEAREST)) > 127


def _fill_pockets(mask, d, small=1500, big=6000, dmin=28):
    """fill the background pockets of a bool mask that do not touch the border: every pocket up to `small` half-resolution px (highlights, grip
    texture, trigger guards of the gun), and bigger ones up to `big` only when they are clearly darker than the table (mean d > dmin). A huge pocket
    of table (the loop of a cable around a gun) stays empty. d = table luminance minus pixel luminance."""
    np = _np()
    half = mask[::2, ::2]; dh = d[::2, ::2]
    lab, areas = _components(~half)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    cnt = np.maximum(np.bincount(lab.ravel(), minlength=len(areas)), 1)
    md = np.bincount(lab.ravel(), weights=dh.ravel(), minlength=len(areas)) / cnt
    ok = np.array([(i not in border and i != 0 and (areas[i] <= small or (areas[i] <= big and md[i] > dmin))) for i in range(len(areas))], bool)[lab]
    return mask | _to_full(ok, mask.shape)


def _keep_gun2(mask, rel=0.05, pad=0.10):
    """keep the largest blob (grown by 4 px first) plus any SOLID blob (area / bbox >= 0.5, so print and wires do not count) of at least `rel` of its
    area whose centre lies inside its bounding box grown by `pad`; a detached silencer or magazine stays, tags and bank notes go. A secondary blob
    that touches the card edge is never kept: that is a neighbouring prop cut by the photo frame (the box and notes beside the Hawk Sawn-off, the
    price tag under the bullpup), not a part of the gun"""
    np = _np()
    half = mask[::2, ::2]
    lab, areas = _components(_dil(half.astype(np.float32), 2) > 0.5)
    if len(areas) < 2:
        return mask & False
    big = max(range(1, len(areas)), key=lambda i: areas[i])
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    ys, xs = np.nonzero(lab == big)
    H, W = half.shape
    x0, x1, y0, y1 = xs.min() - pad * W, xs.max() + pad * W, ys.min() - pad * H, ys.max() + pad * H
    keep = np.zeros(len(areas), bool); keep[big] = True
    for i in range(1, len(areas)):
        if areas[i] < rel * areas[big] or i in edge:
            continue
        yy, xx = np.nonzero(lab == i)
        sol = len(yy) / float((yy.max() - yy.min() + 1) * (xx.max() - xx.min() + 1))
        if sol >= 0.5 and x0 <= xx.mean() <= x1 and y0 <= yy.mean() <= y1:
            keep[i] = True
    return mask & (_dil(_to_full(keep[lab], mask.shape).astype(np.float32), 2) > 0.5)


def table_model(lum, iters=10, deg=4, lam=0.02):
    """the lit table of a stock card as a smooth surface: a ridge-regularised degree-4 polynomial in (x, y) fitted to the UPPER envelope of the
    luminance (iteratively keeping only pixels at most 1.2 sigma below / 2.5 sigma above the fit, so the dark gun, its shadow and the vignette
    corners fall out of the fit but the vignette itself is followed). -> float (H, W) table luminance"""
    np = _np()
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x = (xx / (w - 1)) * 2 - 1; y = (yy / (h - 1)) * 2 - 1
    terms = [(i, j) for i in range(deg + 1) for j in range(deg + 1 - i)]
    A = np.stack([x ** i * y ** j for i, j in terms], -1)
    As = A[::3, ::3].reshape(-1, len(terms)); ls = lum[::3, ::3].reshape(-1)
    ok = ls > np.percentile(ls, 25)
    R = lam * np.eye(len(terms)) * ok.sum() / 100.0
    for _ in range(iters):
        Ao = As[ok]
        co = np.linalg.solve(Ao.T @ Ao + R, Ao.T @ ls[ok])
        res = ls - As @ co
        sg = max(6.0, 1.4826 * np.median(np.abs(res[ok])))
        ok = (res > -1.2 * sg) & (res < 2.5 * sg)
    return (A.reshape(-1, len(terms)) @ co).reshape(h, w)


def _paper_mask(d, thr=-7, min_area=60, hole=600):
    """sheets of paper, sticky notes and boxes are BRIGHTER than the table (d < 0): big bright blobs, print filled. Used only to veto colour-driven
    gun evidence (cream and orange print) so a note is not mistaken for a tan gun."""
    np = _np()
    pm = (_blur((np.clip(d, -60, 60) + 60) / 120.0, 1.2) * 120 - 60) < thr
    pm = _ero(_dil(pm.astype(np.float32), 3), 3) > 0.5
    pm = _dil(_ero(pm.astype(np.float32), 2), 2) > 0.5
    lab, areas = _components(pm[::2, ::2])
    keep = np.array([i != 0 and areas[i] >= min_area for i in range(len(areas))], bool)[lab]
    pm = _dil(_to_full(keep, pm.shape).astype(np.float32), 2) > 0.5
    return _fill_pockets(pm, np.zeros_like(d), small=hole, big=0)


def cut_photo(rgba):
    """stock photo card -> (rgb float (H, W, 3), alpha float (H, W)) of the gun alone over the visible 445x210, or None when no sane gun was found.
    v2 (MARK_VERSION 2): d = table model (table_model) minus pixel luminance.
      core  = very dark (d > 85, or < 50 % of the table where the vignette is dark) or coloured (tan, cyan, orange: chroma + darker than the table,
              not on paper);
      dense = core opened by 2 px (the strokes of print, red ink and wires are 2-4 px, gun parts are not) then blurred > 0.5;
      body  = core near dense, grown 3 px inside the looser 'd > 50' shadow-edge test, closed by 7 px, small pockets filled (_fill_pockets), then
              the largest blob and solid neighbours only (_keep_gun2); the 1-2 px of soft photo halo go with a 1 px erosion."""
    np = _np()
    f = rgba[:VIS_H, :VIS_W, :3].astype(np.float32)
    lum = 0.3 * f[:, :, 0] + 0.59 * f[:, :, 1] + 0.11 * f[:, :, 2]
    bg = table_model(lum); d = bg - lum
    chroma = f.max(2) - f.min(2)
    soft = _blur(np.clip(chroma, 0, 255) / 255.0, 1.5) * 255
    paper = _paper_mask(d)
    col = (((chroma > 40) & (d > 25)) | ((soft > 32) & (d > 6))) & ~paper
    core = (d > 85) | ((lum < 0.5 * bg) & (d > 30)) | col
    loose = (d > 50) | ((lum < 0.6 * bg) & (d > 20)) | (((chroma > 40) & (d > 15)) & ~paper)
    co = _dil(_ero(core.astype(np.float32), 2), 2) > 0.5
    dens = _blur(co.astype(np.float32), 2.5) > 0.5
    rec = core & (_dil(dens.astype(np.float32), 4) > 0.5)
    base = ((_dil(rec.astype(np.float32), 3) > 0.5) & loose) | rec
    base = _ero(_dil(base.astype(np.float32), 7), 7) > 0.5
    base = _fill_pockets(base, d)
    m = _keep_gun2(base)
    m = _ero(m.astype(np.float32), 1) > 0.5
    if m.mean() < 0.02 or m.mean() > 0.55:
        return None
    return f / 255.0, _blur(m.astype(np.float32), 0.8)


def cut_flat(rgba):
    """flat card (light gun on ink) -> (rgb, alpha) with the same contract; the mask is the gun's own silhouette, the underline is dropped"""
    np = _np()
    f = rgba[:VIS_H, :VIS_W, :3].astype(np.float32)
    lum = 0.3 * f[:, :, 0] + 0.59 * f[:, :, 1] + 0.11 * f[:, :, 2]
    fg = _clean(lum > 110)
    if fg.mean() < 0.03 or fg.mean() > 0.6:
        return None
    al = _blur(fg.astype(np.float32), 0.7)
    return None, al                                              # rgb None: the fill is shaded from the mask (shade_flat)


def hud_alpha(tex, item):
    """alpha float (128, 128) of the level's HUD picture of a handed-over gun (kl_shop_swap.PIC_OF_ITEM), or None"""
    return W._silhouette(tex, item)


def fit_mask(alpha, box, size, up=1.25):
    """crop to the bounding box, scale into box (aspect kept, at most `up` times larger than the source, centred in x, centred in y) on a
    size (W, H) canvas -> (placed array, scale)"""
    np = _np()
    from PIL import Image
    ys, xs = np.nonzero(alpha > 0.4)
    if not len(xs):
        return None, 1.0
    return (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1), 1.0


def place(rgb, alpha, box, size, up=1.25, left=False):
    """crop the art to its bounding box and scale it into box (x0, y0, x1, y1) on a canvas of size (W, H); rgb may be None (flat). Premultiplied
    resampling so the edge keeps no fringe. -> (rgb or None, alpha) float canvas arrays"""
    np = _np()
    from PIL import Image
    ys, xs = np.nonzero(alpha > 0.4)
    if not len(xs):
        return None, np.zeros((size[1], size[0]), np.float32)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    ca = alpha[y0:y1, x0:x1]
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / ca.shape[1], bh / ca.shape[0], up)
    w, h = max(1, round(ca.shape[1] * s)), max(1, round(ca.shape[0] * s))
    a2 = _arr(Image.fromarray((np.clip(ca, 0, 1) * 255).astype(np.uint8), 'L').resize((w, h), Image.LANCZOS))
    a2 = np.clip((a2 - 0.5) * 1.6 + 0.5, 0, 1) if s > 1.05 else a2          # an enlarged mask is soft: pull its edge back in
    px = box[0] if left else box[0] + (bw - w) // 2
    py = box[1] + (bh - h) // 2
    A = np.zeros((size[1], size[0]), np.float32); A[py:py + h, px:px + w] = a2
    if rgb is None:
        return None, A
    C = np.zeros((size[1], size[0], 3), np.float32)
    pm = rgb[y0:y1, x0:x1] * ca[:, :, None]
    for k in range(3):
        c = _arr(Image.fromarray((np.clip(pm[:, :, k], 0, 1) * 255).astype(np.uint8), 'L').resize((w, h), Image.LANCZOS))
        C[py:py + h, px:px + w, k] = c / np.maximum(a2, 1e-3) if False else c
    out = np.zeros_like(C)
    nz = A > 1e-3
    sc = np.zeros_like(A); sc[py:py + h, px:px + w] = _arr(Image.fromarray((np.clip(ca, 0, 1) * 255).astype(np.uint8), 'L').resize((w, h), Image.LANCZOS))
    out[nz] = C[nz] / np.maximum(sc[nz], 1e-3)[:, None]
    return np.clip(out, 0, 1), A


# ---------------------------------------------------------------- the look
CHALK = (0xf3, 0xf0, 0xea)               # the project's chalk white (tools/kl_hud_menu.CHALK)
OUTLINE = (238, 236, 230)
BACK_TOP, BACK_BOT = (54, 57, 63), (27, 29, 33)
BIG_BOX = (24, 20, 421, 172)             # where the gun sits on the 445x210 shown part: same frame on every card
SMALL_BOX = (2, 38, 126, 86)             # the band the stock small icons use (x 0..127, y 37..86 measured on the 36 stock icons)
UP_BIG, UP_SMALL = 1.2, 1.5
MARK_VERSION = 2          # 2 = the v2 cut-out (table_model segmentation); a v1 card counts as stale but is never re-cut from its own restyled art


def lift(rgb, alpha, target):
    """gain so the 95th percentile luminance of the gun reaches `target` (0..255): black plastic reads as dark grey, a light gun is not
    brightened further; 15 % of the colour is taken out"""
    np = _np()
    m = alpha > 0.6
    lum = (0.3 * rgb[:, :, 0] + 0.59 * rgb[:, :, 1] + 0.11 * rgb[:, :, 2])[m] * 255
    p95 = float(np.percentile(lum, 95)) if len(lum) else target
    g = float(np.clip(target / max(p95, 8.0), 0.75, 2.4))
    grey = (0.3 * rgb[:, :, 0] + 0.59 * rgb[:, :, 1] + 0.11 * rgb[:, :, 2])[:, :, None]
    c = rgb * 0.85 + grey * 0.15
    return np.clip(c * g, 0, 1)


def shade_flat(alpha, tone=(206, 209, 215)):
    """fill for a gun known only by its silhouette: a vertical light ramp (lighter on top) and a bright inner rim, so it reads as metal"""
    np = _np()
    ys, xs = np.nonzero(alpha > 0.5)
    y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, 1)
    yy = np.arange(alpha.shape[0], dtype=np.float32)[:, None]
    ramp = 0.95 - 0.42 * np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    rim = np.clip(alpha - _ero(alpha, 2), 0, 1) * 0.20
    top = np.clip(alpha - np.roll(alpha, 3, axis=0), 0, 1) * 0.25     # a lit upper edge
    t = np.clip(ramp + rim + top, 0, 1)[:, :, None]
    return np.clip(t * np.array(tone, np.float32)[None, None, :] / 255.0, 0, 1)


def backdrop(w, h, vis_w, vis_h):
    """the card's own ground: a clean dark vertical gradient over the shown part, its edge colour continued over the unseen padding"""
    np = _np()
    t = np.clip(np.arange(h, dtype=np.float32) / (vis_h - 1), 0, 1)[:, None, None]
    top, bot = np.array(BACK_TOP, np.float32), np.array(BACK_BOT, np.float32)
    return np.broadcast_to(top * (1 - t) + bot * t, (h, w, 3)).copy()


def paint_card(rgb, alpha, size, vis, hairline=True, underline=True):
    """gun art on the unified ground -> RGB float (H, W, 3) 0..255. rgb None = flat (already shaded by the caller via shade_flat)."""
    np = _np()
    W_, H_ = size
    out = backdrop(W_, H_, vis[0], vis[1])
    sh = _blur(np.roll(np.roll(alpha, 4, axis=1), 7, axis=0), 5) * 0.55          # soft contact shadow, down and right
    out *= (1 - sh)[:, :, None]
    out = out * (1 - alpha[:, :, None]) + rgb * 255.0 * alpha[:, :, None]
    ring = np.clip(_dil(alpha, 2) - alpha, 0, 1)                                  # crisp outline, 2 px, outside the gun
    ring = np.clip(_blur(ring, 0.5) * 1.5, 0, 1) * 0.9 * (1 - alpha)
    out = out * (1 - ring[:, :, None]) + np.array(OUTLINE, np.float32)[None, None, :] * ring[:, :, None]
    if hairline:                                                                   # the chalk edge: one faint line, inset
        c = np.array(CHALK, np.float32)
        x0, y0, x1, y1 = 5, 5, vis[0] - 6, vis[1] - 6
        for (ys, xs) in ((slice(y0, y0 + 1), slice(x0, x1 + 1)), (slice(y1, y1 + 1), slice(x0, x1 + 1)),
                         (slice(y0, y1 + 1), slice(x0, x0 + 1)), (slice(y0, y1 + 1), slice(x1, x1 + 1))):
            out[ys, xs] = out[ys, xs] * 0.82 + c * 0.18
    if underline:
        c = np.array(CHALK, np.float32)
        ux0, ux1, uy = (vis[0] - 160) // 2, (vis[0] + 160) // 2, vis[1] - 22
        for x in range(ux0, ux1):
            e = min(x - ux0, ux1 - 1 - x) / 14.0
            a = 0.30 * min(1.0, e)
            for dy in (0, 1):
                out[uy + dy, x] = out[uy + dy, x] * (1 - a) + c * a
    return out


def to_rgba_big(out, size, vis, mark):
    """RGB float canvas -> RGBA bytes with the padding (unseen) filled from the edge, a faint ordered dither against banding, and the signature
    patches (item key, version) in the unseen bottom-right corner"""
    np = _np()
    W_, H_ = size
    out = out.copy()
    out[:, vis[0]:] = out[:, vis[0] - 1:vis[0]]
    out[vis[1]:, :] = out[vis[1] - 1:vis[1], :]
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 - 0.5
    d = np.tile(bayer, (H_ // 4, W_ // 4))[:, :, None] * 2.0
    out = np.clip(out + d, 0, 255)
    px = np.zeros((H_, W_, 4), np.uint8)
    px[:, :, :3] = (out + 0.5).astype(np.uint8); px[:, :, 3] = 255
    for k, v in enumerate(mark):                         # 16x12 solid patches: exact in DXT1 (two equal endpoints)
        c = W._un565(v)
        px[H_ - 12:, W_ - 16 * (k + 1):W_ - 16 * k, :3] = c
    return px


def marks(item, version=None):
    """two 16-bit colour values written into the unseen corner of a restyled big card: [version, item key]"""
    v = MARK_VERSION if version is None else version
    return [0x07E0 ^ (v * 0x0101) & 0xFFFF, (0x1357 + 0x0421 * (item + 1)) & 0xFFFF]


def marked(rgba):
    """the item key (int) of a card already restyled by THIS version of the tool, else None"""
    r = marked_any(rgba)
    return r[1] if r and r[0] == MARK_VERSION else None


def marked_any(rgba):
    """(version, item key) of a card restyled by any known version of this tool, else None"""
    np = _np()
    H_, W_ = rgba.shape[:2]
    p = rgba[H_ - 12:, W_ - 16:, :3].reshape(-1, 3)
    ver = None
    for v in range(1, MARK_VERSION + 1):
        if (p == np.array(W._un565(marks(0, v)[0]), np.uint8)).all():
            ver = v
    if ver is None:
        return None
    q = rgba[H_ - 12:, W_ - 32:W_ - 16, :3].reshape(-1, 3)
    if not (q == q[0]).all():
        return None
    for item in range(0, 64):
        if tuple(int(v) for v in q[0]) == tuple(W._un565(marks(item, ver)[1])):
            return ver, item
    return None


def card_big(rgb, alpha, item, flat, up=UP_BIG):
    """(art rgb / None, alpha, item key) cut from a card -> RGBA (256, 512, 4) uint8"""
    np = _np()
    size, vis = (512, 256), (VIS_W, VIS_H)
    if flat:
        _c, A = place(None, alpha, BIG_BOX, size, up)
        C = shade_flat(A)
    else:
        C, A = place(lift(rgb, alpha, 150), alpha, BIG_BOX, size, UP_BIG)
    return to_rgba_big(paint_card(C, A, size, vis), size, vis, marks(item))


def card_small(rgb, alpha, flat, up=UP_SMALL):
    """-> RGBA (128, 128, 4) uint8: the gun lit like a stock icon (light), a chalk outline, transparent ground"""
    np = _np()
    size = (128, 128)
    if flat:
        _c, A = place(None, alpha, SMALL_BOX, size, up, left=True)
        C = shade_flat(A)
    else:
        C, A = place(lift(rgb, alpha, 205), alpha, SMALL_BOX, size, UP_SMALL, left=True)
    ring = np.clip(_dil(A, 1) - A, 0, 1)
    ring = np.clip(ring * 1.4, 0, 1) * 0.9
    a_out = np.clip(A + ring * (1 - A), 0, 1)
    col = C * 255.0 * A[:, :, None] + np.array(OUTLINE, np.float32)[None, None, :] * (ring * (1 - A))[:, :, None]
    col = col / np.maximum(a_out, 1e-3)[:, :, None]
    px = np.zeros((128, 128, 4), np.uint8)
    px[:, :, :3] = np.clip(col + 0.5, 0, 255).astype(np.uint8)
    px[:, :, 3] = (a_out * 255 + 0.5).astype(np.uint8)
    return px


# ---------------------------------------------------------------- star and lock
def glyph_star(size=32, ss=8):
    """a crisp white five-point star, same bounding box centre / width as the stock tile, with a thin dark halo (reads on light and dark bars)"""
    import math
    from PIL import Image, ImageDraw
    n = size * ss
    cx, cy = n / 2, n / 2 + 0.5 * ss
    R = 11.5 * ss / 1.0
    pts = []
    for k in range(10):
        r = R if k % 2 == 0 else R * 0.42
        ang = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    im = Image.new('L', (n, n), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return _glyph(im, size, ss)


def glyph_lock(size=32, ss=8):
    from PIL import Image, ImageDraw
    n = size * ss
    im = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(im)
    s = ss
    d.rounded_rectangle((8.5 * s, 14.5 * s, 23.5 * s, 26.5 * s), radius=1.5 * s, fill=255)            # body
    d.arc((10.5 * s, 5.5 * s, 21.5 * s, 22.5 * s), 180, 360, fill=255, width=int(2.4 * s))          # shackle
    d.rectangle((10.5 * s, 12 * s, 12.9 * s, 15 * s), fill=255); d.rectangle((19.1 * s, 12 * s, 21.5 * s, 15 * s), fill=255)
    d.ellipse((14.4 * s, 17.4 * s, 17.6 * s, 20.6 * s), fill=0); d.polygon([(15.2 * s, 19.8 * s), (16.8 * s, 19.8 * s), (17.2 * s, 23.5 * s), (14.8 * s, 23.5 * s)], fill=0)   # keyhole
    return _glyph(im, size, ss)


def _glyph(im, size, ss):
    """supersampled mask (L) -> RGBA (size, size, 4): white inside, dark halo of 1 px outside (DXT5 alpha carries both)"""
    np = _np()
    from PIL import Image
    a = _arr(im.resize((size, size), Image.LANCZOS))
    halo = np.clip(_dil(a, 1) - a, 0, 1) * 0.6
    ao = np.clip(a + halo * (1 - a), 0, 1)
    col = (255.0 * a + 24.0 * halo * (1 - a)) / np.maximum(ao, 1e-3)
    px = np.zeros((size, size, 4), np.uint8)
    px[:, :, :3] = np.clip(col, 0, 255).astype(np.uint8)[:, :, None]
    px[:, :, 3] = (ao * 255 + 0.5).astype(np.uint8)
    return px


# ---------------------------------------------------------------- restyle one archive
def restyle_tex(tex_bytes, tiles, swaps, texobj=None, log=print):
    """-> (new .TEX bytes or the old ones, report dict). tiles = shop_tiles(); swaps = {row: item}. Idempotent: a big card carrying this tool's
    signature for the same item is left as it is."""
    data, expect, rep = bake_tiles(tex_bytes, tiles, swaps, texobj, log)
    if not data:
        return tex_bytes, rep
    return W.patch_pixels(tex_bytes, data, expect), rep


def bake_tiles(tex_bytes, tiles, swaps, texobj=None, log=print, glyphs=True):
    """-> (data {texture id: encoded pixels}, expect {id: (fourcc, w, h)}, report). The pixel work of restyle_tex, without patching anything."""
    import kl_texmat as T
    np = _np()
    tex = texobj or T.read_tex(tex_bytes)
    data, expect, rep = {}, {}, dict(rows={}, kept=[], failed=[])
    for r in sorted(tiles['big']):
        item = swaps.get(r, 0)
        bigid, smallid = tiles['big'][r], tiles['small'][r]
        big, _ = decode_tile(tex, bigid)
        ma = marked_any(big)
        if ma is not None:
            ver, mk = ma
            if mk == item and ver == MARK_VERSION:
                rep['kept'].append(r); continue
            if not item:
                rep['failed'].append((r, 'restyled card (v%d) carries item %d but the swap line has none: the stock art is gone, start from an archive before the restyle' % (ver, mk))); continue
        if item:
            alpha_hud = hud_alpha(tex, item)
            if alpha_hud is None:
                rep['failed'].append((r, 'item %d has no HUD silhouette: card left as it was' % item)); continue
            art = (None, alpha_hud); flat = True; how = 'hud silhouette of item %d' % item
        else:
            kind = classify(big)
            cut = cut_photo(big) if kind == 'photo' else cut_flat(big)
            if cut is None:
                rep['failed'].append((r, 'no gun found in the %s card: left as it was' % kind)); continue
            art = cut; flat = kind == 'flat'; how = kind
        rgb, A = art
        data[bigid] = W.encode_dxt1(card_big(rgb, A, item, flat, 4.0 if item else UP_BIG).tobytes(), 512, 256); expect[bigid] = ('DXT1', 512, 256)
        sp = card_small(rgb, A, flat, 4.0 if item else UP_SMALL)
        import kl_gunpics as P
        data[smallid] = P.encode_dxt5(sp); expect[smallid] = ('DXT5', 128, 128)
        rep['rows'][r] = how
    for key, fn in (('star', glyph_star), ('lock', glyph_lock)):
        for tid in (sorted(tiles[key]) if glyphs else []):
            import kl_gunpics as P
            cur, inf = decode_tile(tex, tid)
            if (inf['fourcc'], inf['w'], inf['h']) != ('DXT5', 32, 32):
                rep['failed'].append((key, 'tile %d is %s %dx%d, not DXT5 32x32: left' % (tid, inf['fourcc'], inf['w'], inf['h']))); continue
            g = fn()
            enc = P.encode_dxt5(g)
            data[tid] = enc; expect[tid] = ('DXT5', 32, 32)
            rep['rows'][key + str(tid)] = 'glyph'
    return data, expect, rep


def blank_tiles(archive_or_zip):
    """regression check: every shop tile the archive's scene shows (36 big cards, 36 small icons, star, lock) must be found, readable, and not a
    uniform picture. -> list of problem strings (empty = fine)"""
    import kl_texmat as T
    np = _np()
    z = archive_or_zip if isinstance(archive_or_zip, zipfile.ZipFile) else zipfile.ZipFile(archive_or_zip)
    stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]
    tex = T.read_tex(z.read(stem + '.TEX'))
    t = shop_tiles(z, stem)
    bad = ['%s: %s' % x for x in t['skipped']]
    if len(t['big']) != 36:
        bad.append('only %d of 36 shop rows found' % len(t['big']))
    items = [('big row %d' % r, tid) for r, tid in sorted(t['big'].items())] + [('small row %d' % r, tid) for r, tid in sorted(t['small'].items())] \
        + [('star', tid) for tid in sorted(t['star'])] + [('lock', tid) for tid in sorted(t['lock'])]
    for what, tid in items:
        try:
            a, _ = decode_tile(tex, tid)
        except Exception as e:
            bad.append('%s (texture %d): not readable (%s)' % (what, tid, e)); continue
        vis = a[:VIS_H, :VIS_W] if a.shape[0] == 256 else a
        rgb, al = vis[:, :, :3].astype(np.float32), vis[:, :, 3]
        if al.max() < 20:
            bad.append('%s (texture %d): fully transparent' % (what, tid)); continue
        sel = al > 20
        if rgb[sel].std(axis=0).max() < 6.0:
            bad.append('%s (texture %d): one flat colour (blank tile)' % (what, tid))
    return bad


def restyle(src, dst, swap_text=None, preview=None, log=print):
    """archive -> ({member: new bytes}, report, tiles); only .TEX changes (names are bake_map's)"""
    import kl_texmat as T
    z = zipfile.ZipFile(src)
    stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]; texm = stem + '.TEX'
    old = z.read(texm)
    tiles = shop_tiles(z, stem)
    for what, why in tiles['skipped']:
        log('  skipped %s: %s' % (what, why))
    swaps = {r: i for r, i in __import__('kl_hud_shop').parse_swap(swap_text, log).items()} if swap_text else {}
    new_tex, rep = restyle_tex(old, tiles, swaps, log=log)
    new = {}
    if new_tex != old:
        new[texm] = new_tex
    return new, rep, tiles


def bake_map(mapdir, outdir, swap_text, log=print):
    """installed map folder -> outdir/<slot>_Main.zip: shop cards restyled (.TEX) and, for the swapped rows, names + descriptions (.LOC).
    The swaps are the map's own KLGuns.ini [Shop] Swap line if it has one, else swap_text (the order klshop.c uses). Every other zip member is
    copied byte for byte (kl_shop_swap.rezip_raw_multi). -> report dict with the per-member proof"""
    import kl_hud_shop as S
    zp = next(os.path.join(mapdir, f) for f in sorted(os.listdir(mapdir)) if f.lower().endswith('_main.zip'))
    ini = os.path.join(mapdir, 'KLGuns.ini')
    swaps, src = S.read_swaps(ini, swap_text, log)
    z = zipfile.ZipFile(zp)
    stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]; texm = stem + '.TEX'
    old = z.read(texm)
    tiles = shop_tiles(z, stem)
    for what, why in tiles['skipped']:
        log('  skipped %s: %s' % (what, why))
    new_tex, rep = restyle_tex(old, tiles, swaps, log=log)
    new = {}
    if new_tex != old:
        new[texm] = new_tex
    files = {i.filename: z.read(i.filename) for i in z.infolist() if i.filename.lower().endswith('.loc')}
    changed = S.apply_level(files, log, guns=ini if os.path.isfile(ini) else None, swaps=swaps)
    for m in changed:
        new[m] = files[m]
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, os.path.basename(zp))
    if os.path.exists(dst):
        os.remove(dst)
    if not new:
        return dict(archive=os.path.basename(zp), unchanged=True, swaps=swaps, swap_source=src, rows=rep['rows'], kept=rep['kept'], failed=rep['failed'])
    W.rezip_raw_multi(zp, dst, new)
    b = zipfile.ZipFile(dst)
    # proof: member by member, CRC + size; only .TEX / .LOC may differ, and only those named in `new`
    diff = [i.filename for i in z.infolist() if (b.getinfo(i.filename).CRC, b.getinfo(i.filename).file_size) != (i.CRC, i.file_size)]
    assert [i.filename for i in z.infolist()] == [i.filename for i in b.infolist()], 'member list changed'
    assert sorted(diff) == sorted(new), 'members that differ %s != changed %s' % (diff, sorted(new))
    assert all(d.lower().endswith(('.tex', '.loc')) for d in diff), diff
    # a second pass changes nothing
    t2 = shop_tiles(b, stem)
    again, rep2 = restyle_tex(b.read(texm), t2, swaps, log=lambda s: None)
    assert again == b.read(texm), 'second restyle pass changed %d bytes (rows %s)' % (sum(x != y for x, y in zip(again, b.read(texm))), sorted(rep2['rows'], key=str)[:6])
    assert not [r for r in rep2['rows'] if isinstance(r, int)], 'second pass repainted cards %s' % sorted(r for r in rep2['rows'] if isinstance(r, int))
    f2 = {n: b.read(n) for n in files}
    assert S.apply_level(f2, lambda s: None, guns=ini if os.path.isfile(ini) else None, swaps=swaps) == [], 'second name pass not idempotent'
    bad = blank_tiles(b)
    return dict(archive=os.path.basename(zp), swaps={str(r): i for r, i in sorted(swaps.items())}, swap_source=src, changed=sorted(new),
                old_md5=W.md5(zp), new_md5=W.md5(dst), old_size=os.path.getsize(zp), new_size=os.path.getsize(dst),
                members=len(z.infolist()), members_identical=len(z.infolist()) - len(diff), members_changed=diff,
                rows=len(rep['rows']), kept=rep['kept'], failed=rep['failed'], blank_tiles=bad,
                tiles_skipped=[[str(y) for y in x] for x in tiles['skipped']])


def recut(mapdir, outdir, swap_text=None, source_suffix='.before-1023shop', log=print, rows=None):
    """v2 cut-out for an installed map: the cards are re-cut from the pre-restyle archive (<zip><source_suffix>, the stock photos) and ONLY the big
    card + small icon tiles of the installed .TEX are replaced (star, lock, FocusBar tiles, every other member stay byte for byte as installed).
    rows: only these shop rows are replaced (the v2 cut is not better on every card: DD01 judged by eye 2026-10-23, re/shop_ui_1023.md);
    the others keep their installed (v1) card, which the stale-art guard in bake_tiles then refuses to re-bake.
    -> report dict with the per-member and per-texture proof. Writes outdir/<zip name>; never touches mapdir."""
    import kl_hud_shop as S, kl_texmat as T
    np = _np()
    zp = next(os.path.join(mapdir, f) for f in sorted(os.listdir(mapdir)) if f.lower().endswith('_main.zip'))
    srcp = zp + source_suffix
    assert os.path.isfile(srcp), 'no source archive %s' % srcp
    ini = os.path.join(mapdir, 'KLGuns.ini')
    swaps, src = S.read_swaps(ini, swap_text or W.DEFAULT_SWAP, log)
    zi, zs = zipfile.ZipFile(zp), zipfile.ZipFile(srcp)
    stem = [n for n in zi.namelist() if n.endswith('.prm')][0][:-4]; texm = stem + '.TEX'
    ti, ts = shop_tiles(zi, stem), shop_tiles(zs, stem)
    assert ti['big'] == ts['big'] and ti['small'] == ts['small'], 'tile ids differ between installed and source'
    if rows is not None:
        ts = dict(ts, big={r: t for r, t in ts['big'].items() if r in rows}, small={r: t for r, t in ts['small'].items() if r in rows})
    data, expect, rep = bake_tiles(zs.read(texm), ts, swaps, log=log, glyphs=False)
    assert not rep['failed'], rep['failed']
    inst_tex = zi.read(texm)
    new_tex = W.patch_pixels(inst_tex, data, expect)
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, os.path.basename(zp))
    if os.path.exists(dst):
        os.remove(dst)
    W.rezip_raw_multi(zp, dst, {texm: new_tex})
    b = zipfile.ZipFile(dst)
    diff = [i.filename for i in zi.infolist() if (b.getinfo(i.filename).CRC, b.getinfo(i.filename).file_size) != (i.CRC, i.file_size)]
    assert [i.filename for i in zi.infolist()] == [i.filename for i in b.infolist()], 'member list changed'
    assert diff == [texm], 'members that differ %s' % diff
    for i in zi.infolist():                       # CRC32 + size is strong, but the named members get a byte compare as well
        if i.filename != texm and (i.filename.lower().endswith(('.loc', '.xml')) or 'focusbar' in i.filename.lower()):
            assert b.read(i.filename) == zi.read(i.filename), i.filename
    assert b.read(texm) == new_tex
    # texture by texture: exactly the card / icon tiles we meant to replace may differ (and every one of those did), nothing else
    texi, texn = T.read_tex(inst_tex), T.read_tex(new_tex)
    assert len(texi.tex) == len(texn.tex)
    assert sorted(texi.tex) == sorted(texn.tex)
    diff_t = [tid for tid in sorted(texi.tex) if bytes(texi.tex[tid].entry) != bytes(texn.tex[tid].entry)]
    assert set(diff_t) <= set(data), 'textures changed beyond the shop tiles: %s' % sorted(set(diff_t) - set(data))
    assert len(new_tex) == len(inst_tex)
    return dict(archive=os.path.basename(zp), dst=dst, source=os.path.basename(srcp), swaps={str(r): i for r, i in sorted(swaps.items())},
                members=len(zi.infolist()), members_changed=diff, rows=len([r for r in rep['rows']]), kept=rep['kept'],
                textures_total=len(texi.tex), textures_changed=len(diff_t), textures_planned=len(data),
                new_md5=W.md5(dst), old_md5=W.md5(zp), rowinfo=rep['rows'])


PATCH_INI = ("; KLHook.shop.patch.ini - merge into <Dog Days>\\KLHook.ini by hand (this tool never touches the game folder).\r\n"
             "; The cards and names baked by 'INSTALL shop 1023.bat' say the guns below; the hook hands them over only with these lines.\r\n"
             "; A map whose KLGuns.ini has its own [Shop] Swap line keeps that line (the bake read the same one).\r\n"
             "[Shop]\r\nEnable=1\r\nSwap=%s\r\nReserveClips=2\r\n")


def stage_all(out, game=W.GAME, swap_text=W.DEFAULT_SWAP, maps=None, log=print, keep_going=True):
    import datetime
    maproot = os.path.join(game, 'KLExpansion', 'Maps')
    names = maps or sorted(d for d in os.listdir(maproot) if os.path.isdir(os.path.join(maproot, d)))
    os.makedirs(out, exist_ok=True)
    manifest = dict(swap=swap_text, game=game, maps=[])
    rows, table = [], []
    for m in names:
        log('== %s' % m)
        try:
            res = bake_map(os.path.join(maproot, m), os.path.join(out, m), swap_text, log)
        except Exception as e:
            if not keep_going:
                raise
            log('  FAILED %s: %s' % (m, e)); res = dict(error=str(e))
        res['map'] = m
        manifest['maps'].append(res)
        if 'new_md5' in res:
            rows.append("  @{ m = '%s'; f = '%s'; old = '%s'; new = '%s' }" % (m, res['archive'], res['old_md5'], res['new_md5']))
            table.append('#     %s\\%s  %s -> %s  (%d -> %d bytes)' % (m, res['archive'], res['old_md5'][:8], res['new_md5'][:8], res['old_size'], res['new_size']))
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    write_scripts(out, manifest, rows, table)
    return manifest


def write_scripts(out, manifest, rows=None, table=None):
    """INSTALL / UNDO .bat, shop1023.ps1 and KLHook.shop.patch.ini from a manifest (also: `python kl_shop_cards.py scripts <out>`)"""
    import datetime
    swap_text = manifest['swap']
    if rows is None:
        rows, table = [], []
        for res in manifest['maps']:
            if 'new_md5' in res:
                rows.append("  @{ m = '%s'; f = '%s'; old = '%s'; new = '%s' }" % (res['map'], res['archive'], res['old_md5'], res['new_md5']))
                table.append('#     %s\\%s  %s -> %s  (%d -> %d bytes)' % (res['map'], res['archive'], res['old_md5'][:8], res['new_md5'][:8], res['old_size'], res['new_size']))
    ps = W.PS1.replace('__FILES__', ',\r\n'.join(rows)).replace('__TABLE__', '\r\n'.join(table)).replace('__SWAP__', swap_text) \
        .replace('__DATE__', datetime.date.today().isoformat()).replace('.before-shopswap', '.before-1023shop') \
        .replace('shopswap.ps1', 'shop1023.ps1').replace('(tools/kl_shop_swap.py,', '(tools/kl_shop_cards.py,') \
        .replace('re/shop_swap_names.md', 're/shop_ui_1023.md') \
        .replace("and\n#   KLGuns.ini (gains a [Shop] Swap= line, which is what the hook reads for that map). Swap line:", "(all 36 shop cards + star / lock restyled).\n#   KLGuns.ini is NOT touched: merge KLHook.shop.patch.ini into KLHook.ini by hand. Swap line:") \
        .replace('the .TEX pixels of the swapped rows\' shop pictures', 'the .TEX pixels of the shop pictures')
    open(os.path.join(out, 'shop1023.ps1'), 'w', encoding='latin1', newline='').write(ps.replace('\r\n', '\n').replace('\n', '\r\n'))
    bat = W.BAT.replace('shopswap.ps1', 'shop1023.ps1').replace('tools\\kl_shop_swap.py', 'tools\\kl_shop_cards.py')
    open(os.path.join(out, 'INSTALL shop 1023.bat'), 'w', newline='').write(bat.format(what='INSTALL shop 1023', arg=''))
    open(os.path.join(out, 'UNDO shop 1023.bat'), 'w', newline='').write(bat.format(what='UNDO shop 1023', arg='-Undo'))
    open(os.path.join(out, 'KLHook.shop.patch.ini'), 'w', newline='').write(PATCH_INI % swap_text)


def main(a):
    pos = [k for k in a if not k.startswith('--')]
    opts = {k[2:].split('=')[0]: (k.split('=', 1)[1] if '=' in k else True) for k in a if k.startswith('--')}
    if len(pos) == 3 and pos[0] == 'sheet':
        sheet(pos[1], pos[2]); return 0
    if len(pos) == 3 and pos[0] == 'bake':
        r = bake_map(pos[1], pos[2], opts.get('swap', W.DEFAULT_SWAP)); print(json.dumps(r, indent=1)); return 0
    if len(pos) == 2 and pos[0] == 'stage':
        m = stage_all(pos[1], swap_text=opts.get('swap', W.DEFAULT_SWAP), maps=opts['maps'].split(',') if 'maps' in opts else None)
        bad = [x['map'] for x in m['maps'] if 'error' in x or x.get('failed') or x.get('blank_tiles')]
        print('staged %d maps; maps with problems: %s' % (len(m['maps']), bad or 'none')); return 1 if bad else 0
    if len(pos) == 3 and pos[0] == 'recut':
        rows = {int(x) for x in opts['rows'].split(',')} if 'rows' in opts else None
        r = recut(pos[1], pos[2], opts.get('swap'), rows=rows); print(json.dumps(r, indent=1)); return 0
    if len(pos) == 2 and pos[0] == 'scripts':
        write_scripts(pos[1], json.load(open(os.path.join(pos[1], 'manifest.json')))); print('scripts rewritten'); return 0
    if len(pos) == 2 and pos[0] == 'check':
        bad = blank_tiles(pos[1])
        print('\n'.join(bad) if bad else 'OK: 36 big + 36 small + star + lock tiles all present and non-uniform')
        return 1 if bad else 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
