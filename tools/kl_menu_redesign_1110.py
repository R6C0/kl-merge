#!/usr/bin/env python3
"""Menu REDESIGN, stage 2 (2026-11-10, OFFLINE): Dead Men's menu ART in Dog Days' front-end scene.

Why: stage 1 (kl_menu_look_1109.py) only re-fonts and re-colours Dog Days' menu; the owner wanted a full redesign
("i wanted a full redesign on the ui"). The plan is re/menu_redesign_1110.md. This tool is its first, purely
texture-level step: the BACKDROP pictures of Dog Days' menu scene are replaced by Dead Men's pictures of the same name,
tile by tile, in a themed COPY of the overlay scene archive. Nothing in an XML file, the .prp, the .gms or the .prm
changes (so the entity table, the menu manager's slot count and every id stay): only pixels of existing .TEX records.

    python kl_menu_redesign_1110.py inventory [--out DIR]     texture + picture inventory of both menu scenes (json + txt)
    python kl_menu_redesign_1110.py sheet [--out DIR]         PNG contact sheets: DM pictures composed, DD vs DM pairs
    python kl_menu_redesign_1110.py plan                      print the picture mapping (DD picture <- DM picture) and the fit class
    python kl_menu_redesign_1110.py stage [--src ZIP] [--dd DIR] [--dm DIR] [--out DIR] [--only a,b]   build the themed scene archive
    python kl_menu_redesign_1110.py check STAGE_DIR           re-prove the staged archive against its source
    python kl_menu_redesign_1110.py stageb --src LIVE.zip --out DIR [--parts bars,plates,logos,lobby]   stages B/C/F on the live overlay copy
    python kl_menu_redesign_1110.py checkb DIR                re-prove stage B/C/F (only listed .TEX records differ, ids/sizes/names kept)

Reads only. The default output is C:\\kl_build_1024\\menulook_1109\\redesign\\ (never a game folder: --out inside a
game folder is refused). Words: PROVEN = checked by this tool on the real files; GUESS = needs the game.

How a picture is built (PROVEN on both scenes by this tool): a ZWINPIC entity's .prp node ends with three ints
(W, H, chunk); the .prm chunk lists n sprites, each 9 floats (cx, -cy, 0, 0, u, v, 0, tw, th) at 4 + 40k and a sprite
chunk id at 8 + 40n + 4k; the sprite chunk's u32 at +4 is the .TEX id. The tile is drawn as a tw x th rectangle centred at
(cx, -cy) with the top-left (u, v) fraction of the texture -- so a picture's LOOK is its tile textures and its SIZE/PLACE are
fixed by the entity, which is why a swap must keep every tile's pixel size (or re-cut to it).
"""
import collections, json, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ZWINGROUP, ZWINPIC = 0x10002e, 0x200046
WORK = r'C:\kl_build_1024\menulook_1109'
DD_DEF = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
DM_DEF = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
DD_SCENE = ('Scenes/kaneandlynch.zip', 'Scenes/kaneandlynch')       # (path under the game folder, member stem)
DM_SCENE = ('Scenes/KaneAndLynch.zip', 'Scenes/KaneAndLynch')


# ================================================================ texture decoding
def _np():
    import numpy as np
    return np


def _c565(np, c):
    r = ((c >> 11) & 31) * 255 // 31
    g = ((c >> 5) & 63) * 255 // 63
    b = (c & 31) * 255 // 31
    return np.stack([r, g, b], -1).astype(np.int32)


def decode_dxt(data, w, h, kind):
    """kind '1', '3' or '5' -> RGBA uint8 array (h, w, 4). First mip. Vectorised over blocks."""
    np = _np()
    bw, bh = (w + 3) // 4, (h + 3) // 4
    step = 8 if kind == '1' else 16
    raw = np.frombuffer(bytes(data[:bw * bh * step]), np.uint8).reshape(bh * bw, step)
    cb = raw[:, step - 8:].copy()
    c0 = cb[:, 0].astype(np.int32) | (cb[:, 1].astype(np.int32) << 8)
    c1 = cb[:, 2].astype(np.int32) | (cb[:, 3].astype(np.int32) << 8)
    bits = (cb[:, 4].astype(np.uint32) | (cb[:, 5].astype(np.uint32) << 8) | (cb[:, 6].astype(np.uint32) << 16) | (cb[:, 7].astype(np.uint32) << 24))
    p, q = _c565(np, c0), _c565(np, c1)
    pal = np.zeros((len(raw), 4, 4), np.int32)
    pal[:, 0, :3], pal[:, 1, :3] = p, q
    four = (c0 > c1)[:, None]
    pal[:, 2, :3] = np.where(four, (2 * p + q) // 3, (p + q) // 2)
    pal[:, 3, :3] = np.where(four, (p + 2 * q) // 3, 0)
    pal[:, :, 3] = 255
    if kind == '1':
        pal[:, 3, 3] = np.where(four[:, 0], 255, 0)               # 3-colour mode: index 3 = transparent
    idx = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))[None, :]) & 3
    px = np.take_along_axis(pal, idx[:, :, None].astype(np.int64).repeat(4, 2), 1)   # (blocks, 16, 4)
    if kind == '3':
        a = raw[:, :8].astype(np.uint32)
        a64 = np.zeros(len(raw), np.uint64)
        for i in range(8):
            a64 |= raw[:, i].astype(np.uint64) << np.uint64(8 * i)
        al = ((a64[:, None] >> (4 * np.arange(16, dtype=np.uint64))[None, :]) & np.uint64(15)).astype(np.int32) * 17
        px[:, :, 3] = al
    elif kind == '5':
        a0, a1 = raw[:, 0].astype(np.int32), raw[:, 1].astype(np.int32)
        a48 = np.zeros(len(raw), np.uint64)
        for i in range(6):
            a48 |= raw[:, 2 + i].astype(np.uint64) << np.uint64(8 * i)
        ai = ((a48[:, None] >> (3 * np.arange(16, dtype=np.uint64))[None, :]) & np.uint64(7)).astype(np.int32)
        tab = np.zeros((len(raw), 8), np.int32)
        tab[:, 0], tab[:, 1] = a0, a1
        gt = (a0 > a1)[:, None]
        for i in range(1, 7):
            tab[:, i + 1] = np.where(gt[:, 0], ((7 - i) * a0 + i * a1) // 7, np.where(i <= 4, ((5 - i) * a0 + i * a1) // 5, 0))
        tab[:, 6] = np.where(gt[:, 0], tab[:, 6], 0)
        tab[:, 7] = np.where(gt[:, 0], tab[:, 7], 255)
        px[:, :, 3] = np.take_along_axis(tab, ai, 1)
    img = px.reshape(bh, bw, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(bh * 4, bw * 4, 4)
    return img[:h, :w].astype(np.uint8)


def tex_rgba(entry):
    """A .TEX record -> RGBA uint8 (h, w, 4) of mip 0, or None for a format not read (8V8U, 0A61, cube faces)."""
    np = _np()
    _size, f1, _f2, _id, th, tw, _mips, _fl = struct.unpack_from('<I4s4sIHHII', entry, 0)
    q = entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', entry, q)[0]
    d = entry[q + 4:q + 4 + n]
    if f1 in (b'1TXD', b'3TXD', b'5TXD'):
        return decode_dxt(d, tw, th, f1[:1].decode())
    if f1 == b'ABGR' and n >= 4 * tw * th:
        return np.frombuffer(bytes(d[:4 * tw * th]), np.uint8).reshape(th, tw, 4).copy()
    return None


def tex_info(entry):
    _size, f1, _f2, tid, th, tw, mips, fl = struct.unpack_from('<I4s4sIHHII', entry, 0)
    return dict(id=tid, w=tw, h=th, fmt=f1.decode('latin1'), mips=mips, flags=fl)


# ================================================================ scene pictures
class Scene:
    """One menu scene archive: its pictures {name: [Pic]} and its .TEX."""

    def __init__(self, path, stem, game):
        import kl_scene, kl_prp, kl_prmgraph as G, kl_texmat as T
        self.path, self.stem, self.game = path, stem, game
        z = zipfile.ZipFile(path)
        self.zip = z
        self.tex = T.read_tex(z.read(stem + '.TEX'))
        sc = kl_scene.read(z, stem)
        prp = kl_prp.Prp(z.read(stem + '.prp'))
        ents = list(sc.entities())
        nodes = prp.nodes()
        if len(nodes) != len(ents) + 1:
            raise SystemExit('%s: .prp nodes and .gms entities do not line up' % path)
        prm = G.read(z.read(stem + '.prm'), game)
        self.pics = collections.OrderedDict()
        for i, e in enumerate(ents):
            if e.tid != ZWINPIC:
                continue
            own = e.name.decode('latin1')
            name = e.parent.name.decode('latin1') if own == 'Box' and e.parent is not None else own
            ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)]
            if len(ints) < 3:
                continue
            W, H, c = ints[-3:]
            if not 0 < c < len(prm.chunks):
                continue
            d = prm.chunks[c]
            n = struct.unpack_from('<I', d, 0)[0]
            if len(d) < 8 + 56 * n or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
                continue
            sp = []
            for k, s in enumerate(struct.unpack_from('<%dI' % n, d, 8 + 40 * n)):
                if not 0 < s < len(prm.chunks) or len(prm.chunks[s]) != 32:
                    continue
                f = struct.unpack_from('<9f', d, 4 + 40 * k)
                sp.append(dict(cx=f[0], cy=-f[1], u=f[4], v=f[5], tw=f[7], th=f[8], tex=prm.u32(s, 4)))
            self.pics.setdefault(name, []).append(dict(W=W, H=H, sprites=sp, entity=i))

    def family(self):
        f = collections.OrderedDict()
        for n, v in self.pics.items():
            f.setdefault(re.sub(r'#\d+$', '', n), []).append(n)
        return f

    def compose(self, name, bg=None):
        """The picture drawn from its tiles -> PIL RGBA image of W x H (alpha kept; bg = (r,g,b) to flatten)."""
        from PIL import Image
        p = self.pics[name][0]
        im = Image.new('RGBA', (int(p['W']), int(p['H'])), (0, 0, 0, 0))
        for s in p['sprites']:
            t = self.tex.tex.get(s['tex'])
            a = tex_rgba(t.entry) if t is not None else None
            if a is None:
                continue
            h, w = a.shape[:2]
            tile = Image.fromarray(a, 'RGBA').crop((0, 0, max(1, round(w * min(s['u'], 1.0))), max(1, round(h * min(s['v'], 1.0)))))
            tile = tile.resize((max(1, round(s['tw'])), max(1, round(s['th']))), Image.BILINEAR)
            x, y = round(s['cx'] - s['tw'] / 2), round(s['cy'] - s['th'] / 2)
            im.alpha_composite(tile, (max(x, 0), max(y, 0))) if x >= 0 and y >= 0 else im.paste(tile, (x, y), tile)
        if bg is not None:
            flat = Image.new('RGBA', im.size, bg + (255,))
            flat.alpha_composite(im)
            return flat
        return im


def open_scene(which, dd=DD_DEF, dm=DM_DEF, path=None):
    if which == 'dm':
        return Scene(path or os.path.join(dm, *DM_SCENE[0].split('/')), DM_SCENE[1], 'dm')
    return Scene(path or os.path.join(dd, *DD_SCENE[0].split('/')), DD_SCENE[1], 'dd')


# ================================================================ mapping
# DD picture family -> DM picture family. Same NAME in both menu scenes (the Dog Days scene is a descendant of the Dead
# Men one); the fit class says what the swap needs (PROVEN by `plan` on the real files, the looks are GUESS until seen):
#   tiles   = every tile has the same pixel size and the same picture size -> copy the DM pixels into the DD record
#   recut   = picture size differs -> the DM picture is composed, scaled to the DD picture's size and cut to the DD tiles
#   bar     = long focus bar / line family: handled by stage 1's --bars (kl_hud_menu.repaint), not here
MAP = [
    # (DD family, DM family, note)
    ('Background', 'Background', 'full-screen backdrop of the stock pages'),
    ('Background_Tape', 'Background_Tape', 'full-screen tape / dirt overlay'),
    ('Background_Dirt01', 'Background_Dirt01', 'small dirt overlay'),
    ('Background_Dirt02', 'Background_Dirt02', 'dirt overlay'),
    ('MainLogo', 'MainLogo', 'title-screen logo'),
    ('GameLogoFA', 'GameLogoFA', 'Fragile Alliance logo (276x229 in both)'),
    ('GameLogo', 'GameLogo', 'main-menu logo: DM 276x229 vs DD 512x230'),
    ('GameLogo_big', 'GameLogo_big', 'lobby / big logo: DM 448x349 vs DD 512x348'),
    ('LegalText', 'LegalText', 'legal line (text; left alone by default)'),
    ('LegalText_US', 'LegalText', 'legal line (US)'),
    ('LegalText_EU', 'LegalText', 'legal line (EU)'),
    ('PlatformVersion', 'PlatformVersion', 'platform watermark'),
    ('DebugGridOverlay', 'DebugGridOverlay', 'debug grid (never visible)'),
]


def fit_class(dd, dm, ddf, dmf):
    a, b = dd.pics[dd.family()[ddf][0]][0], dm.pics[dm.family()[dmf][0]][0]
    ta = [(round(s['tw']), round(s['th']), round(s['cx']), round(s['cy']), tex_info(dd.tex.tex[s['tex']].entry)['fmt'] if s['tex'] in dd.tex.tex else None) for s in a['sprites']]
    tb = [(round(s['tw']), round(s['th']), round(s['cx']), round(s['cy']), tex_info(dm.tex.tex[s['tex']].entry)['fmt'] if s['tex'] in dm.tex.tex else None) for s in b['sprites']]
    if (a['W'], a['H']) == (b['W'], b['H']) and [t[:4] for t in ta] == [t[:4] for t in tb]:
        return 'tiles'
    return 'recut'


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['inventory', 'sheet', 'plan', 'stage', 'check', 'stageb', 'checkb'])
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--dd', default=DD_DEF)
    ap.add_argument('--dm', default=DM_DEF)
    ap.add_argument('--src')
    ap.add_argument('--out', default=os.path.join(WORK, 'redesign'))
    ap.add_argument('--only')
    ap.add_argument('--parts', default=','.join(PARTS_B))
    a = ap.parse_args(argv)
    for g in (a.dd, a.dm):
        if os.path.abspath(a.out).lower().startswith(os.path.abspath(g).lower() + os.sep):
            raise SystemExit('refusing: --out is inside a game folder')
    os.makedirs(a.out, exist_ok=True)
    if a.cmd == 'inventory':
        return cmd_inventory(a)
    if a.cmd == 'sheet':
        return cmd_sheet(a)
    if a.cmd == 'plan':
        return cmd_plan(a)
    if a.cmd == 'stage':
        return cmd_stage(a)
    if a.cmd == 'stageb':
        return cmd_stageb(a)
    if a.cmd == 'checkb':
        return cmd_checkb(a)
    return cmd_check(a)


def cmd_inventory(a):
    out = {}
    for g in ('dm', 'dd'):
        s = open_scene(g, a.dd, a.dm)
        tex = [dict(tex_info(t.entry), name=t.name) for _i, t in sorted(s.tex.tex.items())]
        pics = {n: [dict(W=p['W'], H=p['H'], tiles=[(round(q['tw']), round(q['th']), q['tex']) for q in p['sprites']]) for p in v] for n, v in s.pics.items()}
        out[g] = dict(textures=tex, pictures=pics, formats=collections.Counter(t['fmt'] for t in tex))
        print(g, len(tex), 'textures', len(pics), 'pictures', dict(out[g]['formats']))
    json.dump(out, open(os.path.join(a.out, 'inventory.json'), 'w'), indent=1)


def cmd_plan(a):
    dd, dm = open_scene('dd', a.dd, a.dm), open_scene('dm', a.dd, a.dm)
    for ddf, dmf, note in MAP:
        if ddf not in dd.family() or dmf not in dm.family():
            print('%-20s <- %-20s MISSING (%s / %s)' % (ddf, dmf, ddf in dd.family(), dmf in dm.family()))
            continue
        print('%-20s <- %-20s %-6s %s' % (ddf, dmf, fit_class(dd, dm, ddf, dmf), note))


DEFAULT_ONLY = ['Background', 'Background_Tape', 'Background_Dirt01', 'Background_Dirt02', 'MainLogo', 'GameLogoFA']


def swap_plan(dd, dm, only):
    """-> {dd tex id: (dm tex id, family)} for every 'tiles' family in `only` whose DD tile textures are not shared
    with another picture and match the DM tile's pixel size. Recut families are reported, not swapped (this revision)."""
    users = collections.defaultdict(set)
    for n, v in dd.pics.items():
        for p in v:
            for s in p['sprites']:
                users[s['tex']].add(re.sub(r'#\d+$', '', n))
    plan, skipped = {}, []
    for ddf, dmf, _n in MAP:
        if ddf not in only or ddf not in dd.family() or dmf not in dm.family():
            continue
        if fit_class(dd, dm, ddf, dmf) != 'tiles':
            skipped.append((ddf, 'recut'))
            continue
        a, b = dd.pics[dd.family()[ddf][0]][0], dm.pics[dm.family()[dmf][0]][0]
        for sa, sb in zip(a['sprites'], b['sprites']):
            ia, ib = tex_info(dd.tex.tex[sa['tex']].entry), tex_info(dm.tex.tex[sb['tex']].entry)
            if users[sa['tex']] != {ddf} or (ia['w'], ia['h']) != (ib['w'], ib['h']) or tex_rgba(dm.tex.tex[sb['tex']].entry) is None:
                skipped.append((ddf, 'tile %d shared or size/format differs' % sa['tex']))
                continue
            plan[sa['tex']] = (sb['tex'], ddf)
    return plan, skipped


def cmd_stage(a):
    import kl_texmat as T, kl_hud_menu as H
    src = a.src or os.path.join(WORK, 'stage1', 'Scenes', 'kaneandlynch.zip')
    if not os.path.exists(src):
        src = os.path.join(a.dd, *DD_SCENE[0].split('/'))
    only = a.only.split(',') if a.only else DEFAULT_ONLY
    dd, dm = open_scene('dd', a.dd, a.dm, src), open_scene('dm', a.dd, a.dm)
    plan, skipped = swap_plan(dd, dm, only)
    for k, (ib, f) in plan.items():
        px = tex_rgba(dm.tex.tex[ib].entry)
        dd.tex.tex[k].entry = H.tex_abgr(dd.tex.tex[k].entry, px.tobytes())
    dst = os.path.join(a.out, 'stage', 'Scenes')
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, 'kaneandlynch_deadmen.zip')
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = T.write_tex(dd.tex) if it.filename == DD_SCENE[1] + '.TEX' else zi.read(it.filename)
            zo.writestr(it, data)
    rep = dict(src=src, out=out, swapped=len(plan), families=sorted(set(f for _, f in plan.values())), skipped=skipped)
    json.dump(rep, open(os.path.join(a.out, 'stage', 'report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def cmd_check(a):
    rep = json.load(open(os.path.join(a.arg or os.path.join(a.out, 'stage'), 'report.json')))
    new, old = zipfile.ZipFile(rep['out']), zipfile.ZipFile(rep['src'])
    bad = [n for n in old.namelist() if not n.endswith('.TEX') and old.read(n) != new.read(n)]
    import kl_texmat as T
    t0, t1 = T.read_tex(old.read(DD_SCENE[1] + '.TEX')), T.read_tex(new.read(DD_SCENE[1] + '.TEX'))
    chg = [i for i in t0.tex if t0.tex[i].entry != t1.tex[i].entry]
    ok = not bad and sorted(t0.tex) == sorted(t1.tex) and len(chg) <= rep["swapped"] and all(
        tex_info(t0.tex[i].entry)['w'] == tex_info(t1.tex[i].entry)['w'] and t0.tex[i].name == t1.tex[i].name for i in chg)
    print('check', 'PASS' if ok else 'FAIL', 'changed textures', len(chg), 'other members changed', bad)
    return 0 if ok else 1


def cmd_sheet(a):
    from PIL import Image, ImageDraw
    dm, dd = open_scene('dm', a.dd, a.dm), open_scene('dd', a.dd, a.dm)
    dst = os.path.join(a.out, 'sheets')
    os.makedirs(dst, exist_ok=True)

    def sheet(scene, names, path, cell=(320, 200), cols=4, bg=(40, 40, 44)):
        rows = (len(names) + cols - 1) // cols
        S = Image.new('RGB', (cols * cell[0], rows * (cell[1] + 14)), (20, 20, 22))
        d = ImageDraw.Draw(S)
        for k, n in enumerate(names):
            try:
                im = scene.compose(n, bg)
            except Exception as e:
                continue
            im.thumbnail((cell[0] - 6, cell[1] - 6))
            x, y = (k % cols) * cell[0], (k // cols) * (cell[1] + 14)
            S.paste(im.convert('RGB'), (x + 3, y + 14))
            d.text((x + 3, y + 1), '%s %dx%d' % (n, scene.pics[n][0]['W'], scene.pics[n][0]['H']), fill=(240, 240, 230))
        S.save(path)
        print('wrote', path)

    big = [n for n, v in dm.pics.items() if v[0]['W'] >= 100 and v[0]['H'] >= 40 and not re.search(r'#\d+$', n) or re.search(r'#01$', n)]
    sheet(dm, big[:48], os.path.join(dst, 'dm_pictures_1.png'))
    sheet(dm, big[48:], os.path.join(dst, 'dm_pictures_2.png'))
    pairs = []
    for ddf, dmf, _n in MAP:
        if ddf in dd.family() and dmf in dm.family():
            pairs.append((ddf, dmf))
    cell = (360, 220)
    S = Image.new('RGB', (2 * cell[0], len(pairs) * (cell[1] + 14)), (20, 20, 22))
    d = ImageDraw.Draw(S)
    for k, (ddf, dmf) in enumerate(pairs):
        for j, (sc, f) in enumerate(((dd, ddf), (dm, dmf))):
            im = sc.compose(sc.family()[f][0], (40, 40, 44))
            im.thumbnail((cell[0] - 6, cell[1] - 6))
            S.paste(im.convert('RGB'), (j * cell[0] + 3, k * (cell[1] + 14) + 14))
            d.text((j * cell[0] + 3, k * (cell[1] + 14) + 1), '%s %s' % ('DD' if j == 0 else 'DM', f), fill=(240, 240, 230))
    S.save(os.path.join(dst, 'pairs_dd_vs_dm.png'))
    print('wrote pairs sheet')


# ================================================================ stages B (bars, plates), C (logos), F (lobby picture)
PARTS_B = ['bars', 'plates', 'logos', 'lobby']
PLATES = ['LobbyBackground', 'BackgroundWeaponShop', 'ChapterBackground', 'DoubleBackground', 'BlackBandBackground',
          'BlackBandErrorBackground', 'BlackBandErrorBackground2']
LOGOS = [('GameLogo', 'GameLogo'), ('GameLogo_big', 'GameLogo_big')]       # (DD family, DM family): recut, left-aligned
LOBBY = [('LobbyMap_DM07', 'LevelPicture_M07')]                            # DD picture <- DM picture (DD had a text card)


def _set_px(dd, tid, px):
    import kl_hud_menu as H
    e = dd.tex.tex[tid].entry
    i = tex_info(e)
    if px.shape[:2] != (i['h'], i['w']):
        raise SystemExit('texture %d: %s pixels for a %dx%d record' % (tid, px.shape[:2], i['w'], i['h']))
    dd.tex.tex[tid].entry = H.tex_abgr(e, px.tobytes())


def _cut_to_tiles(img, pic, dd):
    """Write the RGBA PIL image (picture size W x H) into the picture's own tile textures, tile by tile: a tile at centre
    (cx, cy) of size tw x th shows the top-left u x v fraction of its texture, so the texture's top-left tw x th pixels
    get the picture rows/cols that tile covers; the rest of the record stays transparent."""
    np = _np()
    done = []
    for s in pic['sprites']:
        i = tex_info(dd.tex.tex[s['tex']].entry)
        x0, y0 = round(s['cx'] - s['tw'] / 2), round(s['cy'] - s['th'] / 2)
        tw, th = round(s['tw']), round(s['th'])
        out = np.zeros((i['h'], i['w'], 4), np.uint8)
        part = img.crop((x0, y0, x0 + tw, y0 + th))
        out[:th, :tw] = np.asarray(part)
        _set_px(dd, s['tex'], out)
        done.append(s['tex'])
    return done


def _opaque_rgb(img):
    """Transparent pixels get the RGB of the nearest drawn ones (no dark halo when the tile is filtered)."""
    np = _np()
    from PIL import Image, ImageFilter
    a = np.asarray(img).copy()
    al = a[..., 3]
    if not (al > 0).any():
        return img
    rgb = Image.fromarray(np.where((al > 0)[..., None], a[..., :3], 0).astype(np.uint8), 'RGB')
    msk = Image.fromarray(((al > 0) * 255).astype(np.uint8), 'L')
    blur_c = np.asarray(rgb.filter(ImageFilter.BoxBlur(3))).astype(np.float32)
    blur_m = np.asarray(msk.filter(ImageFilter.BoxBlur(3))).astype(np.float32)[..., None] / 255.0
    fill = np.where(blur_m > 0.01, blur_c / np.maximum(blur_m, 0.01), 0).clip(0, 255).astype(np.uint8)
    a[..., :3] = np.where((al > 0)[..., None], a[..., :3], fill)
    return Image.fromarray(a, 'RGBA')


def part_logos(dd, dm, log):
    from PIL import Image
    changed = []
    for ddf, dmf in LOGOS:
        dp = dd.pics[dd.family()[ddf][0]][0]
        src = dm.compose(dm.family()[dmf][0])
        W, H = int(dp['W']), int(dp['H'])
        k = min(1.0, W / src.width, H / src.height)
        if k < 1.0:
            src = src.resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
        canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        canvas.paste(src, (0, (H - src.height) // 2), src)       # left-aligned like the Dog Days logo (GUESS: the menu anchors it left)
        canvas = _opaque_rgb(canvas)
        ids = _cut_to_tiles(canvas, dp, dd)
        log('  logo %s <- DM %s: %dx%d into %dx%d, textures %s' % (ddf, dmf, src.width, src.height, W, H, ids))
        changed += ids
    return changed


def part_lobby(dd, dm, log):
    from PIL import Image
    np = _np()
    changed = []
    for ddn, dmn in LOBBY:
        dp = dd.pics[ddn][0]
        src = dm.compose(dmn)
        a = np.asarray(src)[..., 3]
        ys, xs = np.where(a > 128)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        mx, my = int((x1 - x0) * 0.05), int((y1 - y0) * 0.06)          # inside the torn frame
        x0, y0, x1, y1 = x0 + mx, y0 + my, x1 - mx, y1 - my
        want = dp['W'] / dp['H']
        if (x1 - x0) / (y1 - y0) > want:                               # centre-crop to the card's 16:9 (no stretch)
            d = int((x1 - x0) - (y1 - y0) * want) // 2
            x0, x1 = x0 + d, x1 - d
        else:
            d = int((y1 - y0) - (x1 - x0) / want) // 2
            y0, y1 = y0 + d, y1 - d
        crop = src.crop((x0, y0, x1, y1))
        bg = Image.new('RGBA', crop.size, (20, 22, 26, 255))
        bg.alpha_composite(crop)
        W, H = int(dp['W']), int(dp['H'])
        img = bg.resize((W, H), Image.LANCZOS)
        ids = _cut_to_tiles(img, dp, dd)
        log('  lobby %s <- DM %s: frame %s -> %dx%d, textures %s' % (ddn, dmn, crop.size, W, H, ids))
        changed += ids
    return changed


def part_plates(dd, dm, log):
    """Grunge on the dark page plates: alpha x (0.55 .. 1.35) by a luminance map of Dead Men's Background (the near-black
    grunge page), RGB untouched, hard zeros stay zero and no alpha rises above the plate's own maximum."""
    np = _np()
    from PIL import Image
    bgm = dm.compose(dm.family()['Background'][0], (0, 0, 0)).convert('L')
    changed = []
    for fam in PLATES:
        pic = dd.pics[dd.family()[fam][0]][0]
        W, H = int(pic['W']), int(pic['H'])
        lum = np.asarray(bgm.resize((W, H), Image.BILINEAR)).astype(np.float32)
        lum = (lum - lum.mean()) / (lum.std() + 1e-3)
        gain = (1.0 + 0.28 * lum).clip(0.55, 1.35)
        for s in pic['sprites']:
            e = dd.tex.tex[s['tex']].entry
            i = tex_info(e)
            px = tex_rgba(e)
            if px is None or i['w'] != 512:
                continue
            x0, y0 = round(s['cx'] - s['tw'] / 2), round(s['cy'] - s['th'] / 2)
            tw, th = round(s['tw']), round(s['th'])
            g = np.ones((i['h'], i['w']), np.float32)
            g[:th, :tw] = gain[y0:y0 + th, x0:x0 + tw]
            amax = int(px[..., 3].max())
            px = px.copy()
            px[..., 3] = np.minimum(px[..., 3].astype(np.float32) * g, amax).round().astype(np.uint8)
            _set_px(dd, s['tex'], px)
            changed.append(s['tex'])
        log('  plate %s: %d tile(s)' % (fam, len(pic['sprites'])))
    return changed


def part_bars(src_zip, dd, log):
    """Chalk brush focus bars and lines (kl_hud_menu.repaint, the stage-2 painter of menu_look_1109). Reads the CURRENT .TEX
    of `dd` through a temporary archive so earlier parts survive."""
    import kl_hud_menu as H, kl_texmat as T, io
    buf = io.BytesIO()
    with zipfile.ZipFile(src_zip) as zi, zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zo:
        for it in zi.infolist():
            zo.writestr(it, T.write_tex(dd.tex) if it.filename == DD_SCENE[1] + '.TEX' else zi.read(it.filename))
    buf.seek(0)
    z = zipfile.ZipFile(buf)
    data, done = H.repaint(z, DD_SCENE[1], log=log)
    new = T.read_tex(data)
    for k in done:
        dd.tex.tex[k] = new.tex[k]
    log('  bars/lines: %d texture(s) repainted' % len(done))
    return sorted(done)


def cmd_stageb(a):
    import kl_texmat as T
    src = a.src or os.path.join(a.dd, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch_deadmen.zip')
    parts = [p for p in a.parts.split(',') if p]
    dd, dm = open_scene('dd', a.dd, a.dm, src), open_scene('dm', a.dd, a.dm)
    log = print
    changed = collections.OrderedDict()
    for p in parts:
        log('part', p)
        if p == 'bars':
            changed[p] = part_bars(src, dd, log)
        elif p == 'plates':
            changed[p] = part_plates(dd, dm, log)
        elif p == 'logos':
            changed[p] = part_logos(dd, dm, log)
        elif p == 'lobby':
            changed[p] = part_lobby(dd, dm, log)
        else:
            raise SystemExit('unknown part ' + p)
    dst = os.path.join(a.out, 'stage', 'Scenes')
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, 'kaneandlynch_deadmen.zip')
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = T.write_tex(dd.tex) if it.filename == DD_SCENE[1] + '.TEX' else zi.read(it.filename)
            zo.writestr(it, data)
    rep = dict(src=src, out=out, parts=parts, changed={k: v for k, v in changed.items()})
    json.dump(rep, open(os.path.join(a.out, 'stage', 'report.json'), 'w'), indent=1)
    print('staged', out, 'changed', {k: len(v) for k, v in changed.items()})
    return cmd_checkb(a)


def cmd_checkb(a):
    """PROOF: every member except the .TEX is byte-identical; the .TEX has the same ids, names, sizes (w,h) and record
    count; only the listed ids differ; each changed record is a one-mip ABGR of the same id (header intact)."""
    import kl_texmat as T
    rep = json.load(open(os.path.join(a.arg or os.path.join(a.out, 'stage'), 'report.json')))
    new, old = zipfile.ZipFile(rep['out']), zipfile.ZipFile(rep['src'])
    bad = [n for n in old.namelist() if not n.endswith('.TEX') and old.read(n) != new.read(n)]
    t0, t1 = T.read_tex(old.read(DD_SCENE[1] + '.TEX')), T.read_tex(new.read(DD_SCENE[1] + '.TEX'))
    listed = set(i for v in rep['changed'].values() for i in v)
    chg = [i for i in t0.tex if t0.tex[i].entry != t1.tex[i].entry]
    ok = not bad and sorted(t0.tex) == sorted(t1.tex) and set(chg) <= listed and old.namelist() == new.namelist()
    for i in chg:
        x, y = tex_info(t0.tex[i].entry), tex_info(t1.tex[i].entry)
        ok = ok and (x['w'], x['h'], x['id']) == (y['w'], y['h'], y['id']) and t0.tex[i].name == t1.tex[i].name and y['fmt'] == 'ABGR' and y['mips'] == 1
    print('checkb', 'PASS' if ok else 'FAIL', 'changed textures', len(chg), 'listed', len(listed), 'other members changed', bad)
    return 0 if ok else 1



if __name__ == '__main__':
    main()
