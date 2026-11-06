"""kl_shop_pics.py - own big pictures for the weapon shop's HIRE page and for Page II (route 3: the game's own menu renderer draws them).

WHY: the D3D overlay (klhook/klhirepic.c) can never draw on the owner's PC (Present is not wrapped: FrameLimit off, or the Steam overlay forces
RECURSION CUT). A picture the MENU draws needs no D3D hook: this bakes NEW picture entities, textures and online.xml elements into a level zip.
  * 16 heister cards (HIRE page, rows 0..7 = KLChar 1..8, rows 17..24 = KLChar 9..16): grey/black-and-white 445x210 cards from <work>/build/portraits.
  * Page II gun cards (KLShopPage.ini [Pairs] P0..P19): their OWN white-silhouette card instead of the picture of the borrowed stock row.
WHAT a bake does to a level zip (same pattern as kl_portraits.menu and kl_dm02_shops_1024):
  .gms/.prp  36 new ZWINGROUP+ZWINPIC pairs 'KLPic_Hire01..16' / 'KLPic_Pair00..19' next to FAStatus_WeaponBig#01 (same parent); slot ids move
  .oct .rmi .rmc  renumbered for the moved slot ids (kl_octree.remap_ids), nothing else listed there changes
  .prm       +72 chunks (a sprite and a picture chunk per card)   .TEX  +36 DXT1 512x256 textures, ids 3100..3135 (copy of the stock big card's record)
  Menu/online.xml  after each 'FAStatus_WeaponBig#35' element of each WeaponBig group: 36 GuiElements (PlayerIndex 100..115 heisters, 120..139 pairs)
The elements show nothing by themselves: klhook/klshoppage.c ([Hire] BakedPics=1, [ShopPage] OwnPics=1) gives the one that matches the highlighted
row the shown row as PlayerIndex and hides the stock one (PlayerIndex 99). Constants are shared with klhook/klpicown_logic.h (test cross-checks).
Idempotent: entity names (scene) and the marker comment (xml) say a zip is baked.

  python kl_shop_pics.py check <zip>                 what a bake would do / is it baked
  python kl_shop_pics.py bake <zip> <out zip>        one zip (never over the input)
  python kl_shop_pics.py stage [--out DIR] [--maps ...]   cards + preview + INSTALL/UNDO bats in <work>/build/shop_pics_1105
  python kl_shop_pics.py install|undo [--maps ...]   what the bats run (refuse while kl2.exe runs; install MOVES <zip> to <zip>.before-shoppics)
The [BotGate] sibling <slot>_Main.bots.zip (21 KLExpansion maps; the stock Fxx folders have none) gets the same bake and tag, its
<slot>_Main.bots.base.md5 is rewritten to the new plain md5 and DM11B's Int16Ok.txt to the new sizes (tools/kl_bake_siblings.py; each changed file is
backed up with the tag, a failure restores the whole map, undo restores all). ORDER: after build/pd2guns_1105/install.py and kl_shop_buttons.py; undo in
reverse ('INSTALL ALL 1105.bat' / 'UNDO ALL 1105.bat'). --root DIR = another Dog Days folder (rehearsal); --skip-run-check only with --root.
"""
import argparse, os, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_bake_siblings as BS

# ---- shared with klhook/klpicown_logic.h (klpicown_test.c / kl_shop_pics_test.py compare them)
HIRE_BASE, N_HIRE = 100, 16          # PlayerIndex of the baked heister element n (1..16) = HIRE_BASE + n - 1
PAIR_BASE, N_PAIR = 120, 20          # PlayerIndex of the baked pair element k (0..19) = PAIR_BASE + k
TEX_BASE = 3100                      # first new texture id (stock F01 max id is 1396, 4096 slots)
XML_MARK = 'KLPICS v1'
BAK = '.before-shoppics'
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
GRAPHIC_MODEL = 'FAStatus_WeaponBig#01'
ZWINGROUP, ZWINPIC = 0x10002e, 0x200046
BIG_RE = re.compile(r'^([ \t]*)<GuiElement Template="FAWeaponGraphicBig" PlayerIndex="35" Graphic="FAStatus_WeaponBig#35"[^>\n]*/>[ \t]*\r?\n', re.M)   # review 11-05: DM01's online.xml has FadeInTime/FadeInDelay on these lines (the strict form baked 29 of 30 maps)
WIN_RE = re.compile(r'^([ \t]*)<Window Name="((?:HeistStatus|FAStatus)[A-Za-z_]*)"[^\n]*\n', re.M)

# Page II card source fallbacks (GUESS: names of F01's HUD pictures UI_Weapon_01#<name>; no MG picture exists, the rifle stands in for the Type 88 MGs)
HUD_OF_ITEM = {62: 'HG_M-77B_Human_Shield', 63: 'HG_M9Beretta_Human_Shield', 52: 'Launcher_HK69A1', 53: 'Launcher_HK69A1', 54: 'Launcher_HK69A1',
               50: 'RPG_7V', 51: 'RPG_7V', 40: 'Rifle_Type88', 41: 'Rifle_Type88', 42: 'Rifle_Type88', 43: 'Rifle_Type88', 44: 'Rifle_Type88',
               45: 'MG_MiniMi_SPW', 46: 'MG_MiniMi_SPW', 47: 'MG_MiniMi_SPW', 48: 'MG_MiniMi_SPW', 33: 'Rifle_Type81', 35: 'Rifle_Type88',
               38: 'Rifle_Type95', 49: 'Sn_Rem700'}
DEFAULT_PAIRS_RAW = [(0, 62, 0, 'M-77B SHIELD'), (10, 63, 2, 'M9 SHIELD'), (11, 54, 14, 'HK69 FLARE'), (12, 53, 14, 'HK69 GAS'), (13, 52, 14, 'HK69'),
                 (15, 51, 14, 'RPG-7 HIND'), (16, 50, 14, 'RPG-7'), (17, 45, 32, 'MINIMI HELI P'), (18, 42, 31, 'TYPE 88 MG HELI'),
                 (19, 43, 31, 'TYPE 88 MG HELI P'), (21, 41, 31, 'TYPE 88 MG L09'), (22, 40, 31, 'TYPE 88 MG'), (23, 47, 32, 'MINIMI'),
                 (24, 44, 31, 'TYPE 88 MG L10'), (25, 46, 32, 'MINIMI L10'), (27, 48, 32, 'MINIMI HELI'), (28, 33, 30, 'TYPE 81'),
                 (31, 35, 31, 'TYPE 88 L09'), (32, 38, 34, 'TYPE 95 L09'), (35, 49, 32, 'REM 700')]    # = the live KLShopPage.ini of 2026-11-05


def hire_name(n):
    return 'KLPic_Hire%02d' % n


def pair_name(k):
    return 'KLPic_Pair%02d' % k


def all_names():
    return [hire_name(n) for n in range(1, N_HIRE + 1)] + [pair_name(k) for k in range(N_PAIR)]


def player_index(name):
    if name.startswith('KLPic_Hire'):
        return HIRE_BASE + int(name[10:]) - 1
    return PAIR_BASE + int(name[10:])


def _np():
    import numpy as np
    return np


# ------------------------------------------------------------------ textures
def dxt1(rgba, w, h):
    """RGBA bytes -> DXT1 blocks (4-colour mode, c0 > c1, endpoints = brightest / darkest pixel of the block). Same result as
    kl_shop_swap.encode_dxt1 (the stage-2a cards' encoder), vectorised."""
    np = _np()
    a = np.frombuffer(bytes(rgba), np.uint8).reshape(h, w, 4)[:, :, :3].astype(np.int64)
    blk = a.reshape(h // 4, 4, w // 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 3)
    n = blk.shape[0]
    lum = blk[:, :, 0] * 0.3 + blk[:, :, 1] * 0.59 + blk[:, :, 2] * 0.11
    ar = np.arange(n)
    hi, lo = blk[ar, lum.argmax(1)], blk[ar, lum.argmin(1)]

    def c565(c):
        return (((c[:, 0] * 31 + 127) // 255) << 11) | (((c[:, 1] * 63 + 127) // 255) << 5) | ((c[:, 2] * 31 + 127) // 255)

    def un565(v):
        r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
        return np.stack([r * 255 // 31, g * 255 // 63, b * 255 // 31], 1)
    c0, c1 = c565(hi), c565(lo)
    sw = c0 < c1
    c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
    p, q = un565(c0), un565(c1)
    pal = np.stack([p, q, (2 * p + q) // 3, (p + 2 * q) // 3], 1)                       # (n, 4, 3)
    d = ((blk[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(3)                          # (n, 16, 4)
    idx = d.argmin(2).astype(np.uint64)
    bits = (idx << (2 * np.arange(16, dtype=np.uint64))[None, :]).sum(1)
    bits = np.where(c0 == c1, 0, bits)
    out = np.zeros(n, dtype=[('a', '<u2'), ('b', '<u2'), ('c', '<u4')])
    out['a'], out['b'], out['c'] = c0, c1, bits.astype(np.uint32)
    return out.tobytes()


def card_record(template_entry, tid, dxt):
    """a texture record: the stock big card's record with a new id (+12), a card-specific name and its mip 0 replaced (same length)."""
    import kl_gunpics as P
    inf = P.tex_info(template_entry)
    if inf['fourcc'] != 'DXT1' or (inf['h'], inf['w']) != (512, 256) or inf['mips'] != 1:
        raise ValueError('the stock big card is %s %dx%d x%d mips, not DXT1 512x256 x1' % (inf['fourcc'], inf['h'], inf['w'], inf['mips']))
    e = bytearray(template_entry)
    p = inf['mip0']
    n = struct.unpack_from('<I', e, p)[0]
    if n != len(dxt) or inf['size'] != len(e):
        raise ValueError('stock record: mip %d bytes / record %d, card has %d' % (n, inf['size'], len(dxt)))
    struct.pack_into('<I', e, 12, tid)
    e[p + 4:p + 4 + n] = dxt
    return bytes(e)


# ------------------------------------------------------------------ cards (RGBA 512 x 256; the game shows the top left 445 x 210)
def pad_card(rgba445, size=(445, 210)):
    np = _np()
    a = np.frombuffer(bytes(rgba445), np.uint8).reshape(size[1], size[0], 4)
    out = np.pad(a, ((0, 256 - size[1]), (0, 512 - size[0]), (0, 0)), mode='edge')
    return bytes(np.ascontiguousarray(out).tobytes())


def heister_card(n, portraits):
    import kl_portraits as K
    path = os.path.join(portraits, 'char_%02d.png' % n)
    if not os.path.isfile(path):
        return None
    return pad_card(K.gray_card(n, K.png_read(path)))


def pair_source(tex, pair, pd2_dir=None):
    """-> (shade or None, alpha float (H, W), how) of one Page II pair (slot, item, picRow, name), or None.
    Order: PD2 render (pd2guns_1106/pics, else pd2guns_1105/pics: item_NN.png, its alpha = the shape) > model silhouette of the item > HUD picture of the item
    (HUD_OF_ITEM, GUESS names) > the silhouette of the picRow's own gun (a look-alike, the same picture Page II showed before)."""
    np = _np()
    import kl_shop_cards as C
    slot, item, row, name = pair
    if pd2_dir:
        f = os.path.join(pd2_dir, 'item_%02d.png' % item)
        if os.path.isfile(f):
            from PIL import Image
            a = np.asarray(Image.open(f).convert('RGBA'), np.float32) / 255.0
            return a[:, :, 0], a[:, :, 3], 'pd2 ' + os.path.basename(f)
    if item in C.ITEM_TPL:
        m = C.load_model(C.ITEM_TPL[item])
        if m is not None:
            return m[0], m[1], 'model ' + C.ITEM_TPL[item]
    if tex is not None and item in HUD_OF_ITEM:
        import kl_gunpics as P
        pics = P.pictures(tex)
        hit = next((k for k in pics if k.lower() == HUD_OF_ITEM[item].lower()), None)
        if hit:
            e = pics[hit][1].entry
            al = np.asarray(P.decode(P.tex_info(e), e)[:, :, 3], np.float32) / 255.0
            return None, al, 'hud ' + hit
    m = C.load_model(C.row_template(row, 0))
    if m is not None:
        return m[0], m[1], 'look-alike model ' + C.row_template(row, 0)
    return None


def pair_card(tex, pair, pd2_dir=None):
    import kl_shop_cards as C
    src = pair_source(tex, pair, pd2_dir)
    if src is None:
        return None, 'no source'
    shade, alpha, how = src
    return bytes(C.card_big_white(shade, alpha, pair[1], pair[0]).tobytes()), how


def _default_pairs():
    return [(i, it, pr, nm) for i, (_row, it, pr, nm) in enumerate(DEFAULT_PAIRS_RAW)]


def read_pairs(ini_path):
    """KLShopPage.ini [Pairs] -> [(slot, item, picRow, name)] with slot = the P<i> index (row|item|picrow|name)"""
    out = []
    if not ini_path or not os.path.isfile(ini_path):
        return _default_pairs()
    sec = None
    for ln in open(ini_path, encoding='latin1'):
        ln = ln.strip()
        if ln.startswith('['):
            sec = ln.lower(); continue
        m = re.match(r'P(\d+)\s*=\s*(\d+)\|(\d+)\|(\d+)\|(.*)$', ln)
        if sec == '[pairs]' and m:
            out.append((int(m.group(1)), int(m.group(3)), int(m.group(4)), m.group(5).strip()))
    # (slot, item, picRow, name): the ini is row|item|pic|name, the first field (row) is not needed for the card
    return out or _default_pairs()


def build_cards(portraits, tex=None, ini=None, pd2_dir=None, log=print):
    """-> ({entity name: RGBA 512x256 bytes}, {entity name: how}). Missing sources are skipped (logged), never faked."""
    cards, how = {}, {}
    for n in range(1, N_HIRE + 1):
        c = heister_card(n, portraits)
        if c is None:
            log('  no portrait for heister %d: no card' % n); continue
        cards[hire_name(n)] = c; how[hire_name(n)] = 'portrait char_%02d' % n
    for pair in read_pairs(ini):
        pair = (pair[0], pair[1], pair[2], pair[3])
        k = pair[0]
        if not 0 <= k < N_PAIR:
            continue
        # read_pairs returns (P index, item, picRow, name); pair_source wants (_, item, picRow, name)
        c, h = pair_card(tex, (k, pair[1], pair[2], pair[3]), pd2_dir)
        if c is None:
            log('  no picture source for pair %d (item %d): no card' % (k, pair[1])); continue
        cards[pair_name(k)] = c; how[pair_name(k)] = h
    return cards, how


# ------------------------------------------------------------------ online.xml
def bake_xml(xml):
    """bytes -> (bytes, report). One element per card after each FAStatus_WeaponBig#35 element."""
    if XML_MARK.encode() in xml:
        return xml, ['already baked']
    nl = '\r\n' if b'\r\n' in xml else '\n'
    t = xml.decode('latin-1')
    groups = list(BIG_RE.finditer(t))
    if not groups:
        raise ValueError('online.xml has no FAWeaponGraphicBig element for FAStatus_WeaponBig#35')
    out, pos = [], 0
    for m in groups:
        ind = m.group(1)
        out.append(t[pos:m.end()])
        for name in all_names():
            out.append('%s<GuiElement Template="FAWeaponGraphicBig" PlayerIndex="%d" Graphic="%s" />%s' % (ind, player_index(name), name, nl))
        pos = m.end()
    out.append(t[pos:])
    s = ''.join(out)
    w = WIN_RE.search(s)
    i = w.start() if w else 0
    s = s[:i] + '  <!-- %s (tools/kl_shop_pics.py) -->%s' % (XML_MARK, nl) + s[i:]
    return s.encode('latin-1'), ['%d big groups, +%d elements each' % (len(groups), len(all_names()))]


def xml_names(xml):
    return re.findall(rb'Graphic="(KLPic_[A-Za-z]+\d+)"', xml)


# ------------------------------------------------------------------ the zip
def _members(z):
    names = {i.filename.lower(): i.filename for i in z.infolist()}
    prm = [n for n in names if n.endswith('.prm')]
    if len(prm) != 1:
        raise ValueError('expected one .prm, found %d' % len(prm))
    stem = names[prm[0]][:-4]
    return names, stem


def _find(sc, name):
    hit = [e for e in sc.entities() if e.name.decode('latin1') == name]
    return hit


def baked_state(zpath):
    """-> (scene baked, xml baked): both False for a stock zip. Reads only the .prp-less cheap bits (.gms names) and online.xml."""
    import kl_scene
    z = zipfile.ZipFile(zpath)
    names, stem = _members(z)
    sc = kl_scene.read(z, stem)
    sb = any(e.name.startswith(b'KLPic_') for e in sc.entities())
    xb = XML_MARK.encode() in z.read(names['menu/online.xml'])
    return sb, xb


def bake_zip(src, dst, cards, log=print):
    """level zip + {entity name: RGBA 512x256} -> dst. Returns a report dict, or None when src is already fully baked (nothing written)."""
    import kl_scene, kl_prp, kl_gms, kl_texmat as T, kl_prmgraph as G, kl_octree as O
    import kl_portraits as K
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('refusing to write over the input')
    z = zipfile.ZipFile(src)
    names, stem = _members(z)
    rd = lambda ext: z.read(names[(stem + ext).lower()])
    xml_member = names['menu/online.xml']
    sc = kl_scene.read(z, stem)
    ents = list(sc.entities())
    sbaked = any(e.name.startswith(b'KLPic_') for e in ents)
    new_xml, rep = bake_xml(z.read(xml_member))
    xbaked = rep == ['already baked']
    if sbaked and xbaked:
        return None
    if sbaked != xbaked:
        raise ValueError('%s is half baked (scene %s, online.xml %s): bake from the original' % (src, sbaked, xbaked))
    todo = [n for n in all_names() if n in cards]
    if not todo:
        raise ValueError('no cards to bake')
    if len(todo) != len(all_names()):
        log('  note: %d of %d cards missing (their elements are still added, the stock card is shown for them)' % (len(all_names()) - len(todo), len(all_names())))
    prp = kl_prp.Prp(rd('.prp')); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        raise ValueError('.prp nodes and .gms entities do not line up')
    node_of = {id(e): nodes[i + 1] for i, e in enumerate(ents)}
    slot0 = sc.slots()
    models = _find(sc, GRAPHIC_MODEL)
    if len(models) != 1:
        raise ValueError('%d entities named %s' % (len(models), GRAPHIC_MODEL))
    model = models[0]
    parent = model.parent
    if parent is None or [k.tid for k in model.walk()] != [ZWINGROUP, ZWINPIC]:
        raise ValueError('%s is not a ZWINGROUP with one ZWINPIC' % GRAPHIC_MODEL)
    mnode = node_of[id(model)]
    bnode = mnode['children'][0]
    if mnode['ctrls'] or bnode['ctrls']:
        raise ValueError('%s has controllers: not copied' % GRAPHIC_MODEL)
    box_ints = [k for k, (op, _pl) in enumerate(bnode['props']) if op in (4, 9)][-3:]
    sw, sh, sc_chunk = [struct.unpack('<I', bnode['props'][k][1])[0] for k in box_ints]

    tex = T.read_tex(rd('.TEX')); prm = G.read(rd('.prm'), 'dd')
    d = prm.chunks[sc_chunk]; n = struct.unpack_from('<I', d, 0)[0]
    if n != 1 or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
        raise ValueError('the stock big card chunk %d is not a one-tile picture chunk' % sc_chunk)
    sprite0 = struct.unpack_from('<I', d, 8 + 40 * n)[0]
    sd = prm.chunks[sprite0]
    if len(sd) != 32 or sd[:4] != b'\1\1\2\0':
        raise ValueError('the stock big card sprite is not a sprite chunk')
    tex0 = struct.unpack_from('<I', sd, 4)[0]
    tpl = tex.tex[tex0].entry
    tid = TEX_BASE
    if any(t >= TEX_BASE for t in tex.tex) or TEX_BASE + len(todo) > 4096:
        raise ValueError('texture ids %d.. are not free' % TEX_BASE)
    pnode = node_of[id(parent)]
    for name in all_names():
        top = sc.graft(sc, model, parent, models=True)['top']
        top.name = name.encode('latin1')
        if name in cards:
            tex.tex[tid] = T.Texture(card_record(tpl, tid, dxt1(cards[name], 512, 256)))
            sp = G.new_chunk(prm, sd[:4] + struct.pack('<I', tid) + sd[8:], prm.refs[sprite0])
            pc = G.new_chunk(prm, d[:8 + 40 * n] + struct.pack('<I', sp) + d[12 + 40 * n:], prm.refs[sc_chunk])
            tid += 1
        else:
            pc = sc_chunk                                          # no card: the element shows the stock card (the hook hides it, it has no own picture)
        box = dict(bnode, props=list(bnode['props']), ctrls=[], children=[])
        box['props'][box_ints[2]] = (bnode['props'][box_ints[2]][0], struct.pack('<I', pc))
        pnode['children'].append({'props': list(mnode['props']), 'ctrls': [], 'children': [box]})

    faults = sc.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    slot1 = sc.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}; ids[1] = 1
    moved = sum(1 for a, b in ids.items() if a != b)
    pieces = {}
    same = {1: 1}; same.update({v: v for v in ids})
    for ext, cls in (('.oct', O.Oct), ('.rmi', O.RoomIndex), ('.rmc', O.RoomIndex)):
        raw = rd(ext)
        if ext != '.oct' and len(raw) == 32:
            continue
        obj = cls.parse(raw)
        if O.remap_ids(cls.parse(raw), same).pack() != raw:
            raise ValueError('%s does not come back byte for byte from kl_octree: not renumbered' % ext)
        pieces[ext] = O.remap_ids(obj, ids).pack()
    gms, buf = sc.write()
    old_gms = rd('.gms')
    pieces['.gms'] = kl_gms.pack(gms) if K._packed(old_gms) else gms
    pieces['.buf'] = buf
    pieces['.prp'] = prp.serialize()
    pieces['.TEX'] = T.write_tex(tex)
    pieces['.prm'] = G.write(prm)
    new = {names[(stem + e).lower()]: v for e, v in pieces.items()}
    new[xml_member] = new_xml
    _write_zip(src, dst, new)
    res = dict(src=src, dst=dst, cards=len(todo), entities_added=len(all_names()), slots_moved=moved, textures=len(tex.tex), chunks=len(prm.chunks) - 1,
               members=sorted(new))
    log('  %s: +%d entities, +%d textures, %d slot ids renumbered' % (os.path.basename(dst), len(all_names()), len(todo), moved))
    bad = check(dst, src, cards=todo, log=log)
    if bad:
        raise ValueError('the result fails its own check:\n  ' + '\n  '.join(bad))
    return res


def _write_zip(src, dst, new):
    import kl_shop_swap as W
    try:
        W.rezip_raw_multi(src, dst, new)
        return
    except AssertionError as e:                       # a stored member / zip64 / a flag the raw copier does not take: the plain way
        print('  (raw copy refused: %s; rewriting with zipfile)' % e)
    tmp = dst + '.tmp'
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            if info.filename in new:
                zo.writestr(info, new[info.filename], compress_type=info.compress_type)
            else:
                with zi.open(info) as f, zo.open(info, 'w') as g:
                    shutil.copyfileobj(f, g, 1 << 20)
    os.replace(tmp, dst)


def check(path, stock=None, cards=None, log=print):
    """Problems of a baked level zip ([] = none): entities, picture chunks, sprites, textures, online.xml, stock content kept."""
    import kl_scene, kl_prp, kl_texmat as T, kl_prmgraph as G, kl_octree as O, kl_gunpics as P
    bad = []
    z = zipfile.ZipFile(path)
    names, stem = _members(z)
    rd = lambda ext: z.read(names[(stem + ext).lower()])
    sc = kl_scene.read(z, stem); prp = kl_prp.Prp(rd('.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        return ['%d .prp nodes for %d entities' % (len(nodes), len(ents))]
    bad += ['scene: ' + x for x in sc.check()]
    tex = T.read_tex(rd('.TEX')); prm = G.read(rd('.prm'), 'dd')
    seen = {}
    for i, e in enumerate(ents):
        if e.tid != ZWINPIC or not e.parent or not e.parent.name.startswith(b'KLPic_'):
            continue
        nm = e.parent.name.decode('latin1')
        ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)]
        w, h, c = ints[-3:]
        if not 0 < c < len(prm.chunks):
            bad.append('%s: picture chunk %d is not in the .prm' % (nm, c)); continue
        d = prm.chunks[c]; n = struct.unpack_from('<I', d, 0)[0]
        if n != 1 or len(d) < 8 + 56 * n or struct.unpack_from('<I', d, 4 + 40 * n)[0] != n:
            bad.append('%s: chunk %d is not a picture chunk' % (nm, c)); continue
        s = struct.unpack_from('<I', d, 8 + 40 * n)[0]
        if not 0 < s < len(prm.chunks) or len(prm.chunks[s]) != 32 or prm.chunks[s][:4] != b'\1\1\2\0':
            bad.append('%s: sprite %d is not a sprite chunk' % (nm, s)); continue
        t = prm.u32(s, 4)
        if t not in tex.tex:
            bad.append('%s: texture %d is not in the .TEX' % (nm, t)); continue
        if t >= TEX_BASE:
            inf = P.tex_info(tex.tex[t].entry)
            if (inf['fourcc'], inf['h'], inf['w']) != ('DXT1', 512, 256) or struct.unpack_from('<I', tex.tex[t].entry, 12)[0] != t:
                bad.append('%s: texture %d is not a DXT1 512x256 record with its own id' % (nm, t))
        seen[nm] = (w, h, c, t)
    want = list(cards) if cards is not None else all_names()
    miss = [n for n in want if n not in seen]
    if miss:
        bad.append('no entity for %s' % ', '.join(miss))
    dup = [n for n in all_names() if sum(1 for e in ents if e.name.decode('latin1') == n) > 1]
    if dup:
        bad.append('named twice: ' + ', '.join(dup))
    own = {t for (_w, _h, _c, t) in seen.values() if t >= TEX_BASE}
    if len(own) != len([1 for v in seen.values() if v[3] >= TEX_BASE]):
        bad.append('two cards share a texture')
    xml = rd_xml = z.read(names['menu/online.xml'])
    if XML_MARK.encode() not in xml:
        bad.append('online.xml has no marker')
    found = xml_names(xml)
    groups = len(BIG_RE.findall(xml.decode('latin-1')))
    if len(found) != groups * len(all_names()) or set(found) != {n.encode() for n in all_names()}:
        bad.append('online.xml holds %d KLPic elements, %d expected' % (len(found), groups * len(all_names())))
    if stock:
        s = zipfile.ZipFile(stock)
        changed = {'.gms', '.buf', '.prp', '.tex', '.prm', '.oct', '.rmi', '.rmc'}
        for i in s.infolist():
            ext = os.path.splitext(i.filename)[1].lower()
            if i.filename.lower() == 'menu/online.xml' or (ext in changed and i.filename.lower().startswith(stem.lower() + '.')):
                continue
            if z.read(i.filename) != s.read(i.filename):
                bad.append('%s differs from the stock member' % i.filename)
        ssc = kl_scene.read(s, stem)
        keep = [e for e in ents if not e.name.startswith(b'KLPic_') and not (e.parent and e.parent.name.startswith(b'KLPic_'))]
        s0, s1 = ssc.slots(), sc.slots()
        if len(keep) == len(s0):
            ids = {s0[a_] + 2: s1[b_] + 2 for a_, b_ in zip(ssc.entities(), keep)}
            for ext in ('.rmi', '.rmc'):                   # the rooms the stock indexes name, renumbered, are the rooms the baked ones name
                if len(rd(ext)) != 32:
                    r0 = {ids.get(b.room, b.room) for b in O.RoomIndex.parse(s.read(names[(stem + ext).lower()])).boxes}
                    r1 = {b.room for b in O.RoomIndex.parse(rd(ext)).boxes}
                    if r0 != r1:
                        bad.append('%s: room ids %s are not the stock rooms renumbered' % (ext, sorted(r0 ^ r1)[:4]))
        old = [(e.name, e.tid, e.ref, e.model) for e in ssc.entities()]
        now = [(e.name, e.tid, e.ref, e.model) for e in ents if not e.name.startswith(b'KLPic_') and not (e.parent and e.parent.name.startswith(b'KLPic_'))]
        if old != now:
            bad.append('the stock entities are not all there in their order')
        st = T.read_tex(s.read(names[(stem + '.TEX').lower()])); sp = G.read(s.read(names[(stem + '.prm').lower()]), 'dd')
        if any(tex.tex[k].entry != v.entry for k, v in st.tex.items()):
            bad.append('a stock texture changed')
        if prm.chunks[:len(sp.chunks)] != sp.chunks:
            bad.append('a stock .prm chunk changed')
        so = s.read(xml_member_name(s)).decode('latin-1'); sn = rd_xml.decode('latin-1')
        if re.sub(r'(?m)^[ \t]*<GuiElement Template="FAWeaponGraphicBig" PlayerIndex="\d+" Graphic="KLPic_[^\n]*\n', '', sn).replace('  <!-- %s (tools/kl_shop_pics.py) -->\r\n' % XML_MARK, '').replace('  <!-- %s (tools/kl_shop_pics.py) -->\n' % XML_MARK, '') != so:
            bad.append('online.xml differs from the stock one by more than the KLPic elements')
    log('  check: %d of %d cards found, %d problems' % (len(seen), len(want), len(bad)))
    return bad


def xml_member_name(z):
    return next(i.filename for i in z.infolist() if i.filename.lower() == 'menu/online.xml')


# ------------------------------------------------------------------ targets, stage, install, undo
def zip_in(d):
    for f in sorted(os.listdir(d)):
        if f.lower().endswith('_main.zip'):
            return os.path.join(d, f)
    return None


def targets(names, dd=DD):
    import kl_shop_buttons as B
    t = {}
    for n in B.STOCK_MAPS:
        d = os.path.join(dd, 'Scenes', 'Locations', n)
        z = zip_in(d) if os.path.isdir(d) else None
        if z:
            t[n] = z
    maps = os.path.join(dd, 'KLExpansion', 'Maps')
    if os.path.isdir(maps):
        for n in sorted(os.listdir(maps)):
            z = zip_in(os.path.join(maps, n)) if os.path.isdir(os.path.join(maps, n)) else None
            if z:
                t[n] = z
    return {k: v for k, v in t.items() if not names or k in names}


def kl2_running():
    import kl_shop_buttons as B
    return B.kl2_running()


def work():
    import kl_port_check
    return kl_port_check.workdir()


def cards_for(zpath, outdir, log=print, dd=None):
    """cards for a stage: built once from the first stock-like zip's HUD pictures (the cards do not depend on the map)"""
    import kl_texmat as T
    w = work()
    portraits = os.path.join(w, 'build', 'portraits')
    pd2 = next((q for q in (os.path.join(w, 'build', 'pd2guns_1106', 'pics'), os.path.join(w, 'build', 'pd2guns_1105', 'pics')) if os.path.isdir(q)),
               os.path.join(w, 'build', 'pd2guns_1105', 'pics'))      # batch 2 (1106) first, the batch 1 stage as the fallback
    z = zipfile.ZipFile(zpath)
    names, stem = _members(z)
    tex = T.read_tex(z.read(names[(stem + '.TEX').lower()]))
    return build_cards(portraits, tex, os.path.join(dd or DD, 'KLShopPage.ini'), pd2 if os.path.isdir(pd2) else None, log)


def write_cards_png(cards, outdir):
    from PIL import Image
    np = _np()
    os.makedirs(outdir, exist_ok=True)
    for name, c in cards.items():
        Image.fromarray(np.frombuffer(c, np.uint8).reshape(256, 512, 4)[:210, :445, :3], 'RGB').save(os.path.join(outdir, name + '.png'))


def preview(cards, how, path):
    """an offline mock of the two pages: the hire page (list left, highlighted heister's card right) and one Page II row"""
    from PIL import Image, ImageDraw
    import kl_portraits as K
    np = _np()
    W_, H_ = 1000, 780
    im = Image.new('RGB', (W_, H_), (22, 24, 30))
    d = ImageDraw.Draw(im)
    f, fs = K._font(22), K._font(15)
    d.text((20, 10), 'HIRE page (mock, not the game): row 3 highlighted', font=fs, fill=(200, 200, 200))
    for i, nm in enumerate(K.CARD_NAMES[:8]):
        y = 40 + i * 34
        if i == 2:
            d.rectangle((20, y - 2, 330, y + 28), fill=(70, 74, 86))
        d.text((30, y), '%d  %s' % (i + 1, nm.upper()), font=f, fill=(235, 235, 235))
    c = cards.get(hire_name(3))
    if c:
        im.paste(Image.fromarray(np.frombuffer(c, np.uint8).reshape(256, 512, 4)[:210, :445, :3], 'RGB'), (400, 40))
    d.text((20, 400), 'Page II row (mock): the pair card replaces the borrowed stock picture', font=fs, fill=(200, 200, 200))
    for i, k in enumerate((4, 16)):
        c = cards.get(pair_name(k))
        if c:
            im.paste(Image.fromarray(np.frombuffer(c, np.uint8).reshape(256, 512, 4)[:210, :445, :3], 'RGB'), (20 + i * 470, 430))
            d.text((20 + i * 470, 650), '%s: %s' % (pair_name(k), how.get(pair_name(k), '')), font=fs, fill=(200, 200, 200))
    im.save(path)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['check', 'bake', 'stage', 'install', 'undo'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--maps', nargs='+', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--root', default=None, help='a Dog Days folder other than the default (rehearsal on copies)')
    ap.add_argument('--skip-run-check', action='store_true', help='with --root only: do not refuse while kl2.exe runs')
    a = ap.parse_args(argv)
    if a.mode == 'check':
        if len(a.paths) != 1:
            print('usage: check <zip>'); return 2
        sb, xb = baked_state(a.paths[0])
        print('scene baked: %s, online.xml baked: %s' % (sb, xb))
        if sb and xb:
            return 1 if check(a.paths[0]) else 0
        return 0
    if a.mode == 'bake':
        if len(a.paths) != 2:
            print('usage: bake <zip> <out zip>'); return 2
        cards, how = cards_for(a.paths[0], None)
        r = bake_zip(a.paths[0], a.paths[1], cards)
        print('already baked' if r is None else 'wrote %s' % a.paths[1])
        return 0
    if a.mode in ('install', 'undo') and kl2_running() and not (a.skip_run_check and a.root):
        print('kl2.exe is running: close the game first (nothing changed)'); return 2
    tg = targets(a.maps, a.root or DD)
    out = a.out or os.path.join(work(), 'build', 'shop_pics_1105')
    bad, lines, cards, how = 0, [], None, {}
    for name, zp in tg.items():
        if a.mode == 'undo':
            try:
                n = BS.undo_map(zp, BAK, lambda m: print('%-6s%s' % (name, m)))
            except OSError as e:
                print('%-6s FAIL undo (map restored to its state before the undo): %s' % (name, e)); bad += 1; continue
            if not n:
                print('%-6s no backup %s' % (name, zp + BAK))
            continue
        try:
            if cards is None:
                cards, how = cards_for(zp, out, dd=a.root)
            sb, xb = baked_state(zp)
            sib = BS.paths(zp)['bots']
            sib_todo = os.path.isfile(sib) and baked_state(sib) != (True, True)
            if sb and xb and not (sib_todo and a.mode == 'install'):
                print('%-6s already baked' % name); lines.append('%s already baked' % name); continue
            if a.mode == 'stage':
                os.makedirs(os.path.join(out, name), exist_ok=True)
                tmp = os.path.join(out, name, os.path.basename(zp))
                r = bake_zip(zp, tmp, cards)
                lines.append('%s ok: %d cards, %d slot ids moved%s' % (name, r['cards'], r['slots_moved'], '; bots sibling too' if os.path.isfile(sib) else ''))
                print(lines[-1])
                if xb is False and not os.path.exists(os.path.join(out, 'preview.png')):
                    write_cards_png(cards, os.path.join(out, 'cards')); preview(cards, how, os.path.join(out, 'preview.png'))
                os.remove(tmp)                                                         # the stage holds the cards and the tool, the bats bake from the LIVE zip
            else:
                def bake_one(src, dst):                                                # plain zip and bots sibling: the same bake, the same cards
                    if baked_state(src) == (True, True):
                        return False
                    return bake_zip(src, dst, cards) is not None
                r = BS.install_map(zp, BAK, bake_one, lambda m: print('%-6s%s' % (name, m)))
                print('%-6s %s %s%s' % (name, r, zp, ' (original: %s)' % os.path.basename(zp + BAK) if r == 'installed' else ''))
        except (ValueError, KeyError, OSError, zipfile.BadZipFile, SystemExit) as e:
            print('%-6s FAIL %s%s' % (name, e, ' (every file of the map restored)' if a.mode == 'install' else '')); bad += 1; lines.append('%s FAIL %s' % (name, e))
    if a.mode == 'stage':
        os.makedirs(out, exist_ok=True)
        if cards:
            write_cards_png(cards, os.path.join(out, 'cards'))
            if not os.path.exists(os.path.join(out, 'preview.png')):
                preview(cards, how, os.path.join(out, 'preview.png'))
        open(os.path.join(out, 'report.txt'), 'w').write('\n'.join(lines + ['%s: %s' % (k, v) for k, v in sorted(how.items())]) + '\n')
        write_bats(out, list(tg))
    return 1 if bad else 0


def modules():
    """the .py files a stage folder needs (closure of the imports of this tool)"""
    return ['kl_shop_pics.py', 'kl_shop_buttons.py', 'kl_menu_count.py', 'kl_portraits.py', 'kl_shop_cards.py', 'kl_shop_swap.py', 'kl_scene.py',
            'kl_prp.py', 'kl_gms.py', 'kl_texmat.py', 'kl_prmgraph.py', 'kl_octree.py', 'kl_gunpics.py', 'kl_hud_shop.py', 'kl_hud_menu.py',
            'kl_port_check.py', 'kl_mat.py', 'kl_loc.py', 'kl_bake_siblings.py']   # review 11-05: kl_texmat imports kl_mat, kl_port_check imports kl_loc: the staged bats died with ModuleNotFoundError (found by running the staged copy alone)


def write_bats(out, maps):
    for f in modules():
        p = os.path.join(HERE, f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(out, f))
    ml = ' '.join(maps)
    for nm, mode, txt in (('INSTALL shop pics.bat', 'install', 'Moves each live map zip to <zip>%s and writes the baked zip (16 heister cards + 20 Page II gun cards) in its place. An existing backup is never overwritten.' % BAK),
                          ('UNDO shop pics.bat', 'undo', 'Moves the *%s files back.' % BAK)):
        with open(os.path.join(out, nm), 'w', newline='\r\n') as f:
            f.write('@echo off\nrem %s\nrem Needs python on the PATH (with numpy and pillow). Bakes from the live zips, so the shop buttons bake and other map edits are kept.\n' % txt)
            f.write('rem Also set [Hire] BakedPics=1 and [ShopPage] OwnPics=1 in KLHook.ini (both default 0).\n')
            f.write('tasklist /fi "imagename eq kl2.exe" 2>nul | find /i "kl2.exe" >nul && (echo Kane and Lynch 2 is running: close it first. Nothing changed. & pause & exit /b 1)\n')
            f.write('python "%%~dp0kl_shop_pics.py" %s --maps %s\npause\n' % (mode, ml))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
