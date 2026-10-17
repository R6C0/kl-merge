#!/usr/bin/env python3
"""
Gun HUD pictures in the black-and-white (silhouette) style, and the picture that matches the gun HELD
(owner 2026-10-17, items 15 and 16 of re/owner_feedback_1017.md). Offline; NOT RUN IN THE GAME YET.

    python kl_gunpics.py sheet <level zip> <out.png>        every gun picture before | after (no output zip)
    python kl_gunpics.py apply <in zip> <out zip>           the level with the new pictures (+ a report)
    python kl_gunpics.py stage <out folder> [--maps=DD01,DM03A,..] [--game=<Dog Days folder>]
                                                            every installed map of KLExpansion\\Maps -> <out>\\Maps\\<map>\\<zip>
                                                            + manifest.json (input md5 -> output md5) for install_guns.ps1

WHAT IT CHANGES
  Each level's .TEX holds one 128 x 128 DXT5 picture per gun, named 'tex:UserInterface/WeaponsPics/UI_Weapon_01#<item>'
  (49 of them: HUD picture indices 58 .. 106; klhud_weapon.c / the stock ZWeaponDisplay pick one by ITEM id through the
  table at [0x154db68 + 4 * item]). Dog Days draws grey shaded renders; Dead Men draws WHITE SILHOUETTES (shape in the
  alpha channel, colour white, the dial tints it). This tool rewrites the pixels of those pictures:
    - every gun picture becomes a white silhouette made from ITS OWN alpha (the shape Dog Days already has), so the
      whole set has the Dead Men style;
    - a gun that WEARS another model (KLGuns.ini beside the archive: Item, Template, Shown, LookN) gets the silhouette of
      the model it shows, because the picture is chosen by item id and the model by the look: the SCAR item wearing the
      SG 552 showed the SCAR picture. Dead Men looks take Dead Men's own silhouette (M01_FA_A .TEX, ids 1358 + n are
      the OSD slots 50 + n = luvsic's DM_ITEM_PIC), scaled so it is as long as the picture it replaces (the Dog Days
      pictures fill the 128 px width, Dead Men's guns fill about 100) and centred on it. A Dog Days look (the AK-74 on
      the Zastava) takes that gun's own silhouette.
  Same size, same format, same ids and names: the .TEX is patched in place (only pixel bytes of those pictures change),
  the archive is rewritten with every other member copied byte for byte (raw), so a map's other pictures, the
  .prm, .gms and sound are untouched. The shop uses other pictures (FAStatus_Weapon*) and is not affected; the
  picture of the pick-up arrow, the ammo pick-up icons (105, 106) and the dial are not touched.

LIMITS (known)
  - The picture is BAKED for the look the archive was built to show (KLGuns.ini 'Shown'). A look switched during a round
    by klgun.c changes the model, not the picture. (A hook that draws another picture needs a spare picture per look:
    not built.)
  - Which item uses which picture is taken from NAMES: the picture '#Rifle_FN_SCAR' is the SCAR item's. luvsic's
    DD_ITEM_SLOT says the same for every gun used here; we did not read the exe's table [0x154db68] ourselves (GUESS
    that it is that table for the six look guns, it is their enum names).
  - The grenade pictures taken from Dead Men (smoke, tear gas, incendiary) keep Dead Men's BLACK markings (colour 0 in
    the holes of the shape), so they are not pure white; the frag grenade and every gun are white.
  - install_guns.ps1 -Undo only restores a zip that is still the staged one (a rebuilt map is left alone).
  - The result is judged by the contact sheet only; how the dial's tint looks on it in the game is not seen.

CREDIT: luvsic, a-newer-perspective (github.com/luvsicccc/a-newer-perspective, tools/dmhud.py): tex_info, decode and
encode_dxt5 below are lifted from it unchanged, and the Dead Men slot -> picture pairing (DM_ITEM_PIC / DM_SLOTS) is his.
"""
import hashlib, json, os, struct, sys, zipfile, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_texmat as T

PIC = 'UserInterface/WeaponsPics/UI_Weapon_01#'
SKIP = ('AmmoPickup', 'AmmoNoPickup')                    # the ammo pick-up icons are not guns
DM_FIRST_ID, DM_FIRST_SLOT = 1358, 50                    # M01_FA_A.TEX: id = 1358 + (OSD slot - 50)  (checked on the contact sheet)
# look label (KLGuns.ini) -> ('dm', DM OSD slot) or ('dd', Dog Days picture name). Slot names: luvsic's DM_SLOTS.
LOOK_PIC = {
    'MP5': ('dm', 56),          # MP5_A3
    'SG 552': ('dm', 60),       # SG_552
    'M4A1': ('dm', 58),         # M4A1_Carbine
    'P90': ('dm', 57),          # FN_P90
    'Steyr TMP': ('dm', 55),    # Smg_SteyrTMP
    'USP': ('dm', 52),          # HK_USP
    'AK-74': ('dd', 'Rifle_AK74'),
    'AK-74 (DM)': ('dm', 59),   # for a look of Dead Men's own AK (Rifle_AK74_01, textured AK-47): not in any build yet
    'AK-47': ('dm', 59),        # same, if such a look is labelled so (GUESS at the label)
}
# pictures whose Dead Men silhouette is better than the own-alpha one (the grenades keep their markings as holes in the shape)
STYLE_DM = {'Grenade_Smoke': 68, 'Grenade_TearGas': 69, 'Grenade': 70, 'Grenade_Incendiary': 71}
DM_ALPHA_MIN = 24                                        # bounding box of the Dead Men shape: texels this opaque


# ---------------------------------------------------------------- luvsic's helpers (dmhud.py, unchanged)
def _np():
    import numpy as np
    return np


def tex_info(blob, off=0):
    """.TEX entry: +0 size, +4/+8 fourcc ('5TXD' = DXT5), +12 index, +16 u16 w,h, +20 mips, +24 flags, +28 f32,
    +32 0, +36 name\\0, then per mip: u32 size + data"""
    sz = struct.unpack_from('<I', blob, off)[0]
    w, h = struct.unpack_from('<HH', blob, off + 16); mips, fl = struct.unpack_from('<II', blob, off + 20)
    e = blob.index(b'\0', off + 36)
    return dict(size=sz, fourcc=bytes(blob[off + 4:off + 8])[::-1].decode('latin1'), w=w, h=h, mips=mips, flags=fl,
                name=bytes(blob[off + 36:e]).decode('latin1'), mip0=e + 1 - off)   # mip0: relative to the entry


def encode_dxt5(img):
    """RGBA uint8 (h, w, 4) -> DXT5 blocks (bounding-box colour endpoints, min/max 8-level alpha)"""
    np = _np()
    h, w, _ = img.shape
    H4, W4 = max(4, (h + 3) // 4 * 4), max(4, (w + 3) // 4 * 4)
    if (H4, W4) != (h, w):
        img = np.pad(img, ((0, H4 - h), (0, W4 - w), (0, 0)), mode='edge')
    bh, bw = H4 // 4, W4 // 4
    blk = img.reshape(bh, 4, bw, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 4).astype(np.int64)
    nb = blk.shape[0]
    A = blk[:, :, 3]; a0 = A.max(1); a1 = A.min(1)
    k = np.arange(2, 8)
    palA = np.concatenate([a0[:, None], a1[:, None], ((8 - k)[None] * a0[:, None] + (k - 1)[None] * a1[:, None]) // 7], 1)
    ai = np.abs(A[:, :, None] - palA[:, None, :]).argmin(2)
    ai[a0 == a1] = 0
    abits = np.zeros(nb, np.uint64)
    for p in range(16): abits |= ai[:, p].astype(np.uint64) << np.uint64(3 * p)
    C = blk[:, :, :3]; m = (A > 0)[:, :, None]
    m = np.where(m.any(1, keepdims=True), m, True)
    cmax = np.where(m, C, 0).max(1); cmin = np.where(m, C, 255).min(1)
    def q(c): return ((c[:, 0] * 31 + 127) // 255) << 11 | ((c[:, 1] * 63 + 127) // 255) << 5 | ((c[:, 2] * 31 + 127) // 255)
    c0, c1 = q(cmax), q(cmin)
    sw = c0 < c1; c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
    def dq(c): return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], 1)
    k0, k1 = dq(c0), dq(c1)
    pal = np.stack([k0, k1, (2 * k0 + k1) // 3, (k0 + 2 * k1) // 3], 1)
    ci = ((C[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(3).argmin(2)
    ci[c0 == c1] = 0
    cbits = np.zeros(nb, np.uint64)
    for p in range(16): cbits |= ci[:, p].astype(np.uint64) << np.uint64(2 * p)
    out = np.zeros((nb, 16), np.uint8)
    out[:, 0] = a0; out[:, 1] = a1
    for qq in range(6): out[:, 2 + qq] = ((abits >> np.uint64(8 * qq)) & np.uint64(255)).astype(np.uint8)
    out[:, 8] = c0 & 255; out[:, 9] = c0 >> 8; out[:, 10] = c1 & 255; out[:, 11] = c1 >> 8
    for qq in range(4): out[:, 12 + qq] = ((cbits >> np.uint64(8 * qq)) & np.uint64(255)).astype(np.uint8)
    return out.tobytes()


def decode(info, blob):
    """mip 0 -> RGBA uint8 array (h, w, 4)"""
    np = _np()
    w, h, fc = info['w'], info['h'], info['fourcc']
    o = info['mip0']; n = struct.unpack_from('<I', blob, o)[0]; data = blob[o + 4:o + 4 + n]
    bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4); nb = bw * bh
    bs = 8 if fc == 'DXT1' else 16
    a = np.frombuffer(data[:nb * bs], np.uint8).reshape(nb, bs)
    cb = a[:, bs - 8:].astype(np.uint32)
    c0 = cb[:, 0] | cb[:, 1] << 8; c1 = cb[:, 2] | cb[:, 3] << 8
    def rgb(c): return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], 1).astype(np.float32)
    k0, k1 = rgb(c0), rgb(c1)
    four = (c0 > c1) | (fc != 'DXT1')
    k2 = np.where(four[:, None], (2 * k0 + k1) / 3, (k0 + k1) / 2)
    k3 = np.where(four[:, None], (k0 + 2 * k1) / 3, 0)
    pal = np.stack([k0, k1, k2, k3], 1)
    bits = cb[:, 4] | cb[:, 5] << 8 | cb[:, 6] << 16 | cb[:, 7] << 24
    idx = np.stack([(bits >> (2 * p)) & 3 for p in range(16)], 1)
    col = np.take_along_axis(pal, idx[:, :, None].repeat(3, 2).astype(np.int64), 1)
    if fc == 'DXT1':
        al = np.where((~four[:, None]) & (idx == 3), 0, 255)
    elif fc == 'DXT3':
        ab = a[:, :8].astype(np.uint64); v = np.zeros(nb, np.uint64)
        for q in range(8): v |= ab[:, q] << np.uint64(8 * q)
        al = np.stack([((v >> np.uint64(4 * p)) & np.uint64(15)).astype(np.int64) * 17 for p in range(16)], 1)
    else:
        a0 = a[:, 0].astype(np.int64); a1 = a[:, 1].astype(np.int64)
        v = np.zeros(nb, np.uint64)
        for q in range(6): v |= a[:, 2 + q].astype(np.uint64) << np.uint64(8 * q)
        ai = np.stack([((v >> np.uint64(3 * p)) & np.uint64(7)).astype(np.int64) for p in range(16)], 1)
        big = (a0 > a1)[:, None]
        palA = []
        for i in range(8):
            if i == 0: pa = a0[:, None].repeat(1, 1)
            elif i == 1: pa = a1[:, None]
            else:
                p8 = ((8 - i) * a0 + (i - 1) * a1) // 7
                p6 = ((6 - i) * a0 + (i - 1) * a1) // 5 if i < 6 else (np.zeros_like(a0) if i == 6 else np.full_like(a0, 255))
                pa = np.where(big[:, 0], p8, p6)[:, None]
            palA.append(pa)
        palA = np.concatenate(palA, 1)
        al = np.take_along_axis(palA, ai, 1)
    px = np.concatenate([col, al[:, :, None].astype(np.float32)], 2)
    img = px.reshape(bh, bw, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(bh * 4, bw * 4, 4)
    return np.clip(img[:h, :w], 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- level files
def tex_member(z):
    return next(i for i in z.infolist() if i.filename.lower().endswith('.tex'))


def pictures(tex):
    """{picture name: (texture id, Texture)} of the gun pictures (UI_Weapon_01#...), the ammo icons left out."""
    out = {}
    for i, x in tex.tex.items():
        n = x.name.split('#')[-1] if PIC in x.name else None
        if n and n not in SKIP:
            out[n] = (i, x)
    return out


def read_looks(ini_text):
    """KLGuns.ini -> [(Template, Item, Shown, label of the shown look or None)]"""
    out, cur = [], None
    for line in ini_text.splitlines():
        line = line.strip()
        if line.startswith('[Gun.'):
            cur = {}; out.append(cur)
        elif cur is not None and '=' in line:
            k, v = line.split('=', 1); cur[k.strip()] = v.strip()
    res = []
    for g in out:
        n = int(g.get('Shown', '0') or 0)
        res.append((g.get('Template', ''), int(g.get('Item', '-1')), n, g.get('Look%d' % n) if n else None))
    return res


_dm_cache = {}


def dm_silhouettes(dm_zip=None):
    """{OSD slot: RGBA (128, 128, 4) uint8} of Dead Men's gun pictures, from M01_FA_A.TEX."""
    if _dm_cache:
        return _dm_cache
    if dm_zip is None:
        import kl_prpjoin as J
        dm_zip = J.level_zip('M01_FA_A')
    z = zipfile.ZipFile(dm_zip)
    t = T.read_tex(z.read(tex_member(z)))
    for slot in range(50, 73):
        x = t.tex[DM_FIRST_ID + slot - DM_FIRST_SLOT]
        if not x.name.endswith('UserInterface/WeaponsPics/UI_Weapon_01'):
            raise ValueError('Dead Men texture %d is %s, not a weapon picture' % (DM_FIRST_ID + slot - 50, x.name))
        _dm_cache[slot] = decode(tex_info(x.entry), x.entry)
    return _dm_cache


def _bbox(a, lo):
    np = _np()
    ys, xs = np.nonzero(a >= lo)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def fit_to(dm_rgba, dd_a):
    """Dead Men's alpha (128 x 128) scaled to the width of the Dog Days picture's shape and centred on it."""
    np = _np()
    from PIL import Image
    dm_a = dm_rgba[:, :, 3]
    x0, y0, x1, y1 = _bbox(dm_a, DM_ALPHA_MIN)
    X0, Y0, X1, Y1 = _bbox(dd_a[:, :, 3], DM_ALPHA_MIN)
    crop = dm_rgba[y0:y1, x0:x1]
    s = min((X1 - X0) / crop.shape[1], 124.0 / crop.shape[0], 124.0 / crop.shape[1])
    nw, nh = max(1, int(round(crop.shape[1] * s))), max(1, int(round(crop.shape[0] * s)))
    im = np.asarray(Image.fromarray(crop).resize((nw, nh), Image.LANCZOS))
    out = np.zeros((128, 128, 4), np.uint8)
    cx, cy = (X0 + X1) // 2, (Y0 + Y1) // 2
    ox = min(max(cx - nw // 2, 0), 128 - nw); oy = min(max(cy - nh // 2, 0), 128 - nh)
    out[oy:oy + nh, ox:ox + nw] = im
    out[out[:, :, 3] == 0, :3] = 255                      # texels with no shape: white (clean DXT blocks)
    return out


def _white(a):
    np = _np()
    return np.dstack([np.full(a.shape + (3,), 255, np.uint8), a[:, :, None]])


def plan(tex, looks, dm=None):
    """{texture id: new RGBA (128 x 128 x 4)} and a report list for one level's .TEX (+ its KLGuns.ini looks)."""
    pics = pictures(tex)
    low = {n.lower(): n for n in pics}
    new, rep = {}, []
    own = {}
    for n, (i, x) in pics.items():
        e = x.entry; inf = tex_info(e)
        if (inf['w'], inf['h'], inf['fourcc']) != (128, 128, 'DXT5') or inf['mips'] != 1:
            rep.append('SKIP %s: %s %dx%d mips %d' % (n, inf['fourcc'], inf['w'], inf['h'], inf['mips'])); continue
        own[n] = _white(decode(inf, e)[:, :, 3])
        new[i] = own[n]; rep.append('style  %-28s own silhouette' % n)
    for n, slot in STYLE_DM.items():
        if n in own:
            new[pics[n][0]] = fit_to(dm_silhouettes()[slot] if dm is None else dm[slot], own[n])
            rep.append('style  %-28s Dead Men picture slot %d' % (n, slot))
    for tpl, item, shown, label in looks:
        if not shown:
            continue
        n = low.get(tpl.lower())
        if n is None or pics[n][0] not in new:
            rep.append('WARN look of %s (item %d): no picture of that name' % (tpl, item)); continue
        src = LOOK_PIC.get(label)
        if src is None:
            rep.append('WARN look %r of %s: no picture known (left as its own)' % (label, tpl)); continue
        if src[0] == 'dm':
            new[pics[n][0]] = fit_to(dm_silhouettes()[src[1]] if dm is None else dm[src[1]], own[n])
            rep.append('look   %-28s item %2d wears %-10s -> Dead Men picture slot %d' % (n, item, label, src[1]))
        else:
            m = low.get(src[1].lower())
            if m is None or pics[m][0] not in new:
                rep.append('WARN look %r of %s: no Dog Days picture %s' % (label, tpl, src[1])); continue
            new[pics[n][0]] = own[m]
            rep.append('look   %-28s item %2d wears %-10s -> Dog Days picture %s' % (n, item, label, m))
    return new, rep


def patch_tex(data, new):
    """The .TEX bytes with the pixels of those ids replaced (same length; DXT5, 128 x 128, one mip)."""
    np = _np()
    out = bytearray(data)
    if struct.unpack_from('<I', out, 0)[0] != 0x20:
        raise ValueError('not a Dog Days .TEX')
    for i, a in new.items():
        assert a.shape == (128, 128, 4) and a.dtype == np.uint8
        o = struct.unpack_from('<I', out, 0x20 + 4 * i)[0]
        inf = tex_info(bytes(out[o:o + struct.unpack_from('<I', out, o)[0]]))
        blk = encode_dxt5(a)
        p = o + inf['mip0']
        if struct.unpack_from('<I', out, p)[0] != len(blk):
            raise ValueError('picture %d: mip size %d != %d' % (i, struct.unpack_from('<I', out, p)[0], len(blk)))
        out[p + 4:p + 4 + len(blk)] = blk
    return bytes(out)


# ---------------------------------------------------------------- archive (raw rewrite: only one member changes)
def rezip_raw(src, dst, member, data):
    """A copy of archive src with `member` (deflated) replaced by data; every other member copied byte for byte."""
    if os.path.exists(dst) and os.path.samefile(src, dst):
        raise SystemExit('refusing to write over the input: %s' % dst)
    z = zipfile.ZipFile(src); il = z.infolist()
    f = open(src, 'rb'); f.seek(z.start_dir); cdraw = f.read()
    p, cents = 0, []
    for i in il:
        assert cdraw[p:p + 4] == b'PK\x01\x02'
        nl, el, cl = struct.unpack('<HHH', cdraw[p + 28:p + 34])
        cents.append(bytearray(cdraw[p:p + 46 + nl + el + cl])); p += 46 + nl + el + cl
    eocd = cdraw[p:]
    assert eocd[:4] == b'PK\x05\x06', 'no plain EOCD (zip64?)'
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    tmp = dst + '.part'
    o = open(tmp, 'wb')
    for k, i in enumerate(il):
        f.seek(i.header_offset); lh = bytearray(f.read(30))
        assert lh[:4] == b'PK\x03\x04'
        nl, el = struct.unpack('<HH', lh[26:30])
        name_extra = f.read(nl + el)
        newoff = o.tell()
        if i.filename == member:
            assert i.compress_type == zipfile.ZIP_DEFLATED and not (i.flag_bits & 8)
            c = zlib.compressobj(6, zlib.DEFLATED, -15); comp = c.compress(data) + c.flush()
            crc = zlib.crc32(data) & 0xffffffff
            struct.pack_into('<III', lh, 14, crc, len(comp), len(data))
            o.write(lh); o.write(name_extra); o.write(comp)
            struct.pack_into('<III', cents[k], 16, crc, len(comp), len(data))
        else:
            o.write(lh); o.write(name_extra)
            left = i.compress_size
            while left:
                b = f.read(min(left, 8 << 20)); assert b; o.write(b); left -= len(b)
        struct.pack_into('<I', cents[k], 42, newoff)
    cdoff = o.tell()
    for c in cents: o.write(c)
    cdsize = o.tell() - cdoff
    e = bytearray(eocd); struct.pack_into('<II', e, 12, cdsize, cdoff); o.write(e)
    o.close(); f.close()
    os.replace(tmp, dst)
    # verify: same members, unchanged ones raw-identical, the new one reads back (CRC-checked)
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
        if x.filename == member:
            assert b.read(y.filename) == data
        else:
            assert x.CRC == y.CRC and x.compress_size == y.compress_size and raw(fa, x) == raw(fb, y), 'raw entry differs: ' + x.filename
    fa.close(); fb.close()


def apply_zip(src, dst, log=print):
    """-> report dict. The archive's KLGuns.ini (beside the archive) gives the looks; none = style only."""
    ini = os.path.join(os.path.dirname(os.path.abspath(src)), 'KLGuns.ini')
    looks = read_looks(open(ini, encoding='latin-1').read()) if os.path.isfile(ini) else []
    z = zipfile.ZipFile(src); m = tex_member(z)
    data = z.read(m)
    new, rep = plan(T.read_tex(data), looks)
    out = patch_tex(data, new)
    # the patched file must still be the same file but for those pixels
    t_old, t_new = T.read_tex(data), T.read_tex(out)
    assert sorted(t_old.tex) == sorted(t_new.tex)
    changed = [i for i in t_old.tex if t_old.tex[i].entry != t_new.tex[i].entry]
    assert set(changed) <= set(new), 'a picture changed that was not planned'
    assert len(out) == len(data)
    rezip_raw(src, dst, m.filename, out)
    for r in rep:
        log('   ' + r)
    return dict(pictures=len(new), changed=len(changed), looks=[r for r in rep if r.startswith('look')], warnings=[r for r in rep if r.startswith(('WARN', 'SKIP'))])


# ---------------------------------------------------------------- sheet
def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = b''.join(b'\0' + rgb[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def sheet(zip_path, png, only=None):
    np = _np()
    ini = os.path.join(os.path.dirname(os.path.abspath(zip_path)), 'KLGuns.ini')
    looks = read_looks(open(ini, encoding='latin-1').read()) if os.path.isfile(ini) else []
    z = zipfile.ZipFile(zip_path); data = z.read(tex_member(z)); t = T.read_tex(data)
    new, _ = plan(t, looks)
    pics = pictures(t)
    names = [n for n in pics if pics[n][0] in new and (only is None or n in only)]
    def tile(a, tint=None):
        al = a[:, :, 3:4] / 255.0
        return (a[:, :, :3] * tint * al + 60.0 * (1 - al)).astype(np.uint8)
    cols = 8
    rows = []
    for k in range(0, len(names), cols):
        row = []
        for n in names[k:k + cols]:
            i, x = pics[n]
            old = decode(tex_info(x.entry), x.entry)
            oldt = (old[:, :, :3] * (old[:, :, 3:4] / 255.0) + 60.0 * (1 - old[:, :, 3:4] / 255.0)).astype(np.uint8)
            row.append(np.concatenate([oldt, tile(new[i], 0.92)], 0))
        while len(row) < cols:
            row.append(np.zeros((256, 128, 3), np.uint8))
        rows.append(np.concatenate(row, 1))
    write_png(png, np.concatenate(rows, 0))
    print('%d pictures: %s' % (len(names), png))
    for n in names:
        print('   %s' % n)


# ---------------------------------------------------------------- stage
def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def stage(out, maps=None, game=None):
    game = game or r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
    root = os.path.join(game, 'KLExpansion', 'Maps')
    names = maps or sorted(os.listdir(root))
    man = dict(tool='tools/kl_gunpics.py', credit='luvsic, a-newer-perspective (tex_info / decode / encode_dxt5, Dead Men picture slots)', maps={})
    for n in names:
        d = os.path.join(root, n)
        zs = [f for f in os.listdir(d) if f.lower().endswith('_main.zip')]
        if len(zs) != 1:
            print('SKIP %s: %d archives' % (n, len(zs))); continue
        src = os.path.join(d, zs[0]); dst = os.path.join(out, 'Maps', n, zs[0])
        free = __import__('shutil').disk_usage(os.path.dirname(os.path.abspath(out)) if not os.path.isdir(out) else out).free
        if free < os.path.getsize(src) + (700 << 20):
            raise SystemExit('stopping: only %d MB free where the output goes' % (free >> 20))
        print('== %s/%s' % (n, zs[0]))
        r = apply_zip(src, dst, log=lambda s: None)
        for w in r['warnings']:
            print('   ' + w)
        for l in r['looks']:
            print('   ' + l)
        man['maps'][n] = dict(file=zs[0], input_md5=md5(src), output_md5=md5(dst), pictures=r['pictures'], looks=len(r['looks']))
        print('   %d pictures, %d looks; %s -> %s' % (r['pictures'], len(r['looks']), man['maps'][n]['input_md5'][:8], man['maps'][n]['output_md5'][:8]))
        json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    return man


def main(a):
    if len(a) >= 3 and a[0] == 'sheet':
        return sheet(a[1], a[2])
    if len(a) >= 3 and a[0] == 'apply':
        r = apply_zip(a[1], a[2], log=print); print(r); return
    if len(a) >= 2 and a[0] == 'stage':
        kw = dict(x.lstrip('-').split('=', 1) for x in a[2:])
        stage(a[1], kw['maps'].split(',') if 'maps' in kw else None, kw.get('game')); return
    print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
