#!/usr/bin/env python3
r"""
Dead Men names and pictures in the ONLINE lobby (Private Match / System Link), 2026-10-25. Offline build, nothing is installed here.

    python kl_lobbynames.py build [<out folder>]      default C:\kl_build_1024\lobbynames_1025
    python kl_lobbynames.py check <out folder>        re-reads every built archive

WHAT IT BUILDS (one folder per online set: set2, set3, rand; notes in re\lobby_map_names.md section 5)
  <out>\<set>\Overlay\Scenes\kaneandlynch.zip   the LIVE overlay menu scene (read only) + 18 new picture entities (see below)
                                                + the six Title0k leaves of every language's .LOC rewritten to the set's map names
  <out>\<set>\Overlay\Patch01.zip               the LIVE overlay Patch01 + frontend.xml with LobbyPictureF0k re-pointed at the new
                                                entities, and the three ARCADE lists that read Title0k from the LOC (HeistLevel,
                                                HeistLeaderboardScreen, HeistLocalLeaderboardScreen) turned into literal stock names
                                                (otherwise the Arcade page 1 would show Dead Men names too)
  <out>\preview\*.png                           what the lobby will show (never committed)
  <out>\manifest.json                           md5 of base and variants, read by install.py
Where the name comes from: the lobby tag LobbyLevelName builds the key Title%02i (slot + 1) and asks the frontend LOC, so the
LOC leaf is the whole story (re\lobby_map_names.md section 1). Where the picture comes from: frontend scene entities
LevelPicture_F0k (325 x 183), shown by LobbyPictureF0k + LobbyImageToggler.
New entities: LobbyMap_<folder> (12 maps, 325 x 183, the Arcade pictures of the live scene scaled down; The Dig and Flat Raid have
none, so a drawn title card) and LobbyRand_F0k (6 slots: a 2 x 2 collage of the slot's pool = the stock map picture + the picture of
the slot's map on every page of KLHook.ini, the fourth cell a "RANDOM" card when the pool has three).
The pool is read from KLHook.ini [Redirect.N] / [Page.N]; it must be the pool klslot.c's OnlineSet=9 draws from.
Pixels: tex_record layout of kl_portraits (ABGR record, bytes R G B A, picture top left, one tile).
"""
import hashlib, json, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_portraits as P

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'C:\kl_build_1024\lobbynames_1025'
BASE_SCENE = DD + r'\KLExpansion\Overlay\Scenes\kaneandlynch.zip'
BASE_PATCH = DD + r'\KLExpansion\Overlay\Patch01.zip'
INI = DD + r'\KLHook.ini'
STEM = 'Scenes/kaneandlynch'
LW, LH = 325, 183                       # the lobby picture
MODEL = 'LevelPicture_F01'
SLOTS = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']     # LobbyPictureF0k = slot k; the key Title0k = slot k
ARCADE_LISTS = ('HeistLevel', 'HeistLeaderboardScreen', 'HeistLocalLeaderboardScreen')


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ the ini: which map is in which slot on which page
def read_ini(path=INI):
    """-> (redirect {page: {slot: folder}}, titles {page: {slot: title}}); only the block of kl_expansion, pages 2..8."""
    sect, red, tit = None, {}, {}
    for line in open(path, 'rb').read().decode('latin-1').splitlines():
        line = line.split(';')[0].strip()
        m = re.match(r'\[(Redirect|Page)\.(\d)\]$', line)
        if m:
            sect = (m.group(1), int(m.group(2))); continue
        if line.startswith('['):
            sect = None; continue
        if sect and '=' in line:
            k, v = [x.strip() for x in line.split('=', 1)]
            if re.match(r'F0\d$', k):
                (red if sect[0] == 'Redirect' else tit).setdefault(sect[1], {})[k] = v
    return red, tit


# ------------------------------------------------------------------ pixels
def tile_image(prm, tex, chunk):
    """The picture chunk of a ZWINPIC -> (w, h, bytearray RGBA), tiles laid out by their centres, ABGR texture bytes as R G B A."""
    d = prm.chunks[chunk]; n = struct.unpack_from('<I', d, 0)[0]
    sprites = struct.unpack_from('<%dI' % n, d, 8 + 40 * n)
    tiles = [struct.unpack_from('<9f', d, 4 + 40 * i) for i in range(n)]
    W = int(round(max(t[0] + t[7] / 2 for t in tiles))); H = int(round(max(-t[1] + t[8] / 2 for t in tiles)))
    out = bytearray(W * H * 4)
    for t, s in zip(tiles, sprites):
        cx, ncy, _a, _b, _u, _v, _c, w, h = t; w, h = int(round(w)), int(round(h))
        e = tex.tex[prm.u32(s, 4)].entry
        if e[4:8] != b'ABGR':
            raise SystemExit('texture %d is %r, only ABGR is read' % (prm.u32(s, 4), e[4:8]))
        th, tw = struct.unpack_from('<HH', e, 16)
        x0 = int(round(cx - w / 2)); y0 = int(round(-ncy - h / 2))
        for y in range(h):
            if 0 <= y0 + y < H:
                src = 41 + y * tw * 4
                out[((y0 + y) * W + x0) * 4:((y0 + y) * W + x0 + w) * 4] = e[src:src + w * 4]
    return W, H, out


def resize(px, w, h, nw, nh):
    """Area average (box filter), alpha is carried along."""
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        y0, y1 = y * h // nh, max((y + 1) * h // nh, y * h // nh + 1)
        for x in range(nw):
            x0, x1 = x * w // nw, max((x + 1) * w // nw, x * w // nw + 1)
            s = [0, 0, 0, 0]; c = (y1 - y0) * (x1 - x0)
            for yy in range(y0, y1):
                row = px[(yy * w + x0) * 4:(yy * w + x1) * 4]
                for k in range(4):
                    s[k] += sum(row[k::4])
            out[(y * nw + x) * 4:(y * nw + x) * 4 + 4] = bytes(v // c for v in s)
    return out


FONT = {   # 5 x 7, rows top to bottom; only the letters of the cards. Unknown characters draw a filled block.
    'A': '01110 10001 10001 11111 10001 10001 10001', 'D': '11110 10001 10001 10001 10001 10001 11110',
    'E': '11111 10000 10000 11110 10000 10000 11111', 'F': '11111 10000 10000 11110 10000 10000 10000',
    'G': '01110 10001 10000 10111 10001 10001 01111', 'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110', 'L': '10000 10000 10000 10000 10000 10000 11111',
    'M': '10001 11011 10101 10101 10001 10001 10001', 'N': '10001 11001 10101 10011 10001 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110', 'P': '11110 10001 10001 11110 10000 10000 10000',
    'R': '11110 10001 10001 11110 10100 10010 10001', 'T': '11111 00100 00100 00100 00100 00100 00100',
    '?': '01110 10001 00001 00010 00100 00000 00100',
}


def card(w, h, lines, scale):
    """A dark card with centred block-letter lines (title card for a map that has no picture, the RANDOM cell)."""
    px = bytearray(w * h * 4)
    for y in range(h):                                  # vertical blue-grey gradient
        g = 34 + 26 * y // max(h - 1, 1)
        px[y * w * 4:(y + 1) * w * 4] = bytes((g - 6, g, g + 10, 255)) * w
    lh = 7 * scale + 2 * scale; top = (h - lh * len(lines) + 2 * scale) // 2
    for li, text in enumerate(lines):
        tw = len(text) * 6 * scale - scale; x = (w - tw) // 2; y = top + li * lh
        for ch in text.upper():
            rows = FONT.get(ch)
            if ch != ' ':
                for r in range(7):
                    for c in range(5):
                        if rows is None or rows.split()[r][c] == '1':
                            for dy in range(scale):
                                for dx in range(scale):
                                    o = ((y + r * scale + dy) * w + x + c * scale + dx) * 4
                                    if 0 <= o < len(px) - 3 and 0 <= x + c * scale + dx < w:
                                        px[o:o + 4] = bytes((236, 236, 228, 255))
            x += 6 * scale
    return px


def collage(cells, w=LW, h=LH, gap=2):
    """2 x 2 grid of (cw, ch, rgba) pictures, each scaled to its cell."""
    px = bytearray(bytes((20, 20, 24, 255)) * (w * h))
    cw, chh = (w - gap) // 2, (h - gap) // 2
    for i, (sw, sh, spx) in enumerate(cells[:4]):
        small = resize(spx, sw, sh, cw, chh)
        ox, oy = (i % 2) * (cw + gap), (i // 2) * (chh + gap)
        for y in range(chh):
            px[((oy + y) * w + ox) * 4:((oy + y) * w + ox + cw) * 4] = small[y * cw * 4:(y + 1) * cw * 4]
    return px


# ------------------------------------------------------------------ the scene
def _find(roots, path):
    kids = roots
    for name in path:
        e = next((k for k in kids if k.name.decode('latin1') == name), None)
        if e is None:
            raise SystemExit('the scene has no %s' % '\\'.join(path))
        kids = e.kids
    return e


def scene_members(base, pics):
    """base = the live overlay menu scene zip; pics = [(entity name, w, h, rgba)] -> {extension: bytes} of the rebuilt scene (+ names check)."""
    import kl_scene, kl_prp, kl_gms, kl_texmat as T, kl_prmgraph as G, kl_octree as O
    z = zipfile.ZipFile(base)
    names = {i.filename.lower(): i for i in z.infolist()}
    rd = lambda ext: z.read(names[(STEM + ext).lower()])
    sc = kl_scene.read(z, STEM); prp = kl_prp.Prp(rd('.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    if len(nodes) != len(ents) + 1:
        raise SystemExit('.prp nodes and .gms entities do not line up')
    node_of = {id(e): nodes[i + 1] for i, e in enumerate(ents)}
    have = {e.name.decode('latin1') for e in ents}
    for n, *_ in pics:
        if n in have:
            raise SystemExit('%s is already in %s' % (n, base))
    slot0 = sc.slots()
    parent = _find(sc.roots, P.PARENT); model = _find(sc.roots, P.PARENT + (MODEL,))
    if [k.tid for k in model.walk()] != [P.ZWINGROUP, P.ZWINPIC]:
        raise SystemExit('%s is not a ZWINGROUP with one ZWINPIC' % MODEL)
    mnode = node_of[id(model)]
    box_ints = [k for k, (op, _pl) in enumerate(mnode['children'][0]['props']) if op in (4, 9)]
    if [struct.unpack('<I', mnode['children'][0]['props'][k][1])[0] for k in box_ints[-3:]][:2] != [LW, LH]:
        raise SystemExit('the ZWINPIC of %s does not end in width %d, height %d, chunk' % (MODEL, LW, LH))
    if mnode['ctrls'] or mnode['children'][0]['ctrls']:
        raise SystemExit('%s has controllers: not copied' % MODEL)
    tex = T.read_tex(rd('.TEX')); prm = G.read(rd('.prm'), 'dd')
    tid = max(tex.tex) + 1; pnode = node_of[id(parent)]
    for name, w, h, px in pics:
        rec, tw, th = P.tex_record(tid, w, h, px)
        tex.tex[tid] = T.Texture(rec)
        sp = G.new_chunk(prm, P.sprite_chunk(tid)); pc = G.new_chunk(prm, P.pic_chunk(sp, w, h, tw, th))
        top = sc.graft(sc, model, parent, models=True)['top']
        top.name = name.encode('latin1')
        box = dict(mnode['children'][0], props=list(mnode['children'][0]['props']), ctrls=[], children=[])
        for k, v in zip(box_ints[-3:], (w, h, pc)):
            box['props'][k] = (box['props'][k][0], struct.pack('<I', v))
        pnode['children'].append({'props': list(mnode['props']), 'ctrls': [], 'children': [box]})
        tid += 1
    slot1 = sc.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in ents}; ids[1] = 1
    new = {'.prp': prp.serialize(), '.TEX': T.write_tex(tex), '.prm': G.write(prm),
           '.oct': O.remap_ids(O.Oct.parse(rd('.oct')), ids).pack(),
           '.rmc': O.remap_ids(O.RoomIndex.parse(rd('.rmc')), ids).pack()}
    if len(rd('.rmi')) != 32:
        new['.rmi'] = O.remap_ids(O.RoomIndex.parse(rd('.rmi')), ids).pack()
    same = {1: 1}; same.update({v: v for v in ids})
    if O.remap_ids(O.Oct.parse(rd('.oct')), same).pack() != rd('.oct') or O.remap_ids(O.RoomIndex.parse(rd('.rmc')), same).pack() != rd('.rmc'):
        raise SystemExit('.oct / .rmc do not come back byte for byte from kl_octree: not renumbered')
    gms, buf = sc.write()
    new['.gms'], new['.buf'] = kl_gms.pack(gms) if P._packed(rd('.gms')) else gms, buf
    return new


def stock_picture(z, entity):
    """-> (w, h, rgba) of the ZWINPIC under the entity named so, from an open menu scene zip."""
    import kl_scene, kl_prp, kl_texmat as T, kl_prmgraph as G
    sc = kl_scene.read(z, STEM); prp = kl_prp.Prp(z.read(STEM + '.prp'))
    ents = list(sc.entities()); nodes = prp.nodes()
    prm = G.read(z.read(STEM + '.prm'), 'dd'); tex = T.read_tex(z.read(STEM + '.TEX'))
    for i, e in enumerate(ents):
        if e.tid == P.ZWINPIC and e.parent is not None and e.parent.name.decode('latin1') == entity:
            ints = [struct.unpack('<I', pl)[0] for op, pl in nodes[i + 1]['props'] if op in (4, 9)][-3:]
            return tile_image(prm, tex, ints[2])
    raise SystemExit('the scene has no picture %s' % entity)


# ------------------------------------------------------------------ names (LOC) and the page (XML)
def loc_set(data, titles):
    """The six Title0k leaves of a .LOC -> the same file with the given texts; titles {'01': 'Hot Coffee'}. Language-neutral."""
    import kl_loc
    kids = kl_loc.parse(data)
    if kids is None:
        return data
    n = 0
    for key, nd in kl_loc.leaves(kids):
        m = re.match(r'AllLevels/Menu/Online/Scenarios/Title(\d\d)$', key)
        if m and m.group(1) in titles:
            old = nd.raw.index(b'\0'); nd.raw = titles[m.group(1)].encode('latin1') + nd.raw[old:]; n += 1
    if n != len(titles):
        raise SystemExit('found %d of %d Title leaves' % (n, len(titles)))
    out = kl_loc.build(kids); kl_loc.check_cap('LOC', len(out))
    return out


def loc_titles(data):
    import kl_loc
    out = {}
    for key, nd in kl_loc.leaves(kl_loc.parse(data)):
        m = re.match(r'AllLevels/Menu/Online/Scenarios/Title(\d\d)$', key)
        if m:
            out[m.group(1)] = nd.raw[:nd.raw.index(b'\0')].decode('latin1')
    return out


def frontend_set(xml, pictures, stock):
    """pictures {'F01': entity}; stock {'01': 'Subway'}: re-point the lobby pictures, literalise the Arcade lists."""
    for slot, ent in pictures.items():
        pat = r'(Name="LobbyPicture%s"[^>]*Graphic=")LevelPicture_%s(")' % (slot, slot)
        xml, n = re.subn(pat, r'\g<1>' + ent + r'\2', xml)
        if n != 1:
            raise SystemExit('LobbyPicture%s: %d matches' % (slot, n))
    lines = xml.split('\n'); inside = 0; lit = 0
    for i, ln in enumerate(lines):
        if any(('Name="%s"' % nm) in ln for nm in ARCADE_LISTS) and '<GuiElement' in ln:
            inside = 1
        if inside:
            def sub(m):
                return '%' + stock[m.group(1)]
            lines[i], k = re.subn(r'(?<=Text=")/Menu/Online/Scenarios/Title(\d\d)', lambda m: '%' + stock[m.group(1)], ln)
            lit += k
            if '</GuiElement>' in ln:
                inside = 0
    if lit != 9 * 3 - 0 and lit < 24:
        raise SystemExit('only %d Arcade list entries literalised' % lit)
    return '\n'.join(lines), lit


def write_zip(src, dst, repl):
    z = zipfile.ZipFile(src)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    low = {k.lower(): v for k, v in repl.items()}
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():
            data = low.get(i.filename.lower(), z.read(i))
            n = zipfile.ZipInfo(i.filename, i.date_time); n.compress_type = i.compress_type; n.external_attr = i.external_attr
            o.writestr(n, data)


# ------------------------------------------------------------------ build
def build(out=OUT, log=print):
    os.makedirs(out, exist_ok=True)
    red, tit = read_ini()
    z = zipfile.ZipFile(BASE_SCENE)
    zp = zipfile.ZipFile(BASE_PATCH)
    # 1. the pictures: the live Arcade pictures per map (540 x 304) -> 325 x 183; stock lobby pictures; cards for maps without one
    stockpic = {s: stock_picture(z, 'LevelPicture_' + s) for s in SLOTS}
    maps = sorted({m for p in (2, 3) for m in red[p].values()})
    mappic, fake = {}, {}
    for m in maps:
        try:
            w, h, px = stock_picture(z, 'LevelPicture_' + m)
            mappic[m] = (LW, LH, resize(px, w, h, LW, LH))
        except SystemExit:
            name = next(t for p in tit for s, t in tit[p].items() if red.get(p, {}).get(s) == m)
            words = name.upper().split()
            mappic[m] = (LW, LH, card(LW, LH, words, 6 if max(len(x) for x in words) <= 5 else 4)); fake[m] = name
    pics = [('LobbyMap_' + m, *mappic[m]) for m in maps]
    # 2. the random collages: per slot the stock map + the slot's map of every page; the fourth cell a RANDOM card
    pool = {}
    for s in SLOTS:
        ms = [m for p in sorted(red) if p >= 2 for k, m in red[p].items() if k == s]
        if ms:
            pool[s] = ms
            cells = [stockpic[s]] + [mappic[m] for m in ms]
            cells = cells[:4]
            if len(cells) < 4:
                cells.append((LW // 2, LH // 2, card(LW // 2, LH // 2, ['RANDOM', '?'], 3)))
            pics.append(('LobbyRand_' + s, LW, LH, collage(cells)))
    log('pictures: %d new entities (%s); cards drawn for %s; random pools %s' % (len(pics), ', '.join(n for n, *_ in pics), fake or 'none', pool))
    new = scene_members(BASE_SCENE, pics)
    # 3. names
    stock_titles = loc_titles(z.read('Scenes/kaneandlynchEnglish.LOC'))
    names = {'set2': {s[1:]: tit[2][s] for s in tit[2]}, 'set3': {s[1:]: tit[3][s] for s in tit[3]},
             'rand': {s[1:]: 'Random Map' for s in pool}}
    pict = {'set2': {s: 'LobbyMap_' + red[2][s] for s in red[2]}, 'set3': {s: 'LobbyMap_' + red[3][s] for s in red[3]},
            'rand': {s: 'LobbyRand_' + s for s in pool}}
    xml0 = zp.read('menu/frontend.xml').decode('latin-1')
    man = {'base_scene': md5(BASE_SCENE), 'base_patch': md5(BASE_PATCH), 'sets': {}}
    for sname in ('set2', 'set3', 'rand'):
        repl = {STEM + ext: data for ext, data in new.items()}
        for i in z.infolist():
            if re.match(r'Scenes/kaneandlynch\w+\.LOC$', i.filename):
                repl[i.filename] = loc_set(z.read(i), names[sname])
        sz = os.path.join(out, sname, 'Overlay', 'Scenes', 'kaneandlynch.zip')
        write_zip(BASE_SCENE, sz, repl)
        xml, lit = frontend_set(xml0, pict[sname], stock_titles)
        pz = os.path.join(out, sname, 'Overlay', 'Patch01.zip')
        write_zip(BASE_PATCH, pz, {'menu/frontend.xml': xml.encode('latin-1')})
        man['sets'][sname] = {'scene': md5(sz), 'patch': md5(pz), 'names': names[sname], 'pictures': pict[sname]}
        log('%s: names %s | %d Arcade list entries literal | %s %.1f MB' % (sname, names[sname], lit, sz, os.path.getsize(sz) / 1e6))
    # 4. previews (to look at, not committed)
    os.makedirs(os.path.join(out, 'preview'), exist_ok=True)
    for n, w, h, px in pics:
        P.png_write(os.path.join(out, 'preview', n + '.png'), w, h, px)
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    bad = check(out, log)
    if bad:
        raise SystemExit('check failed:\n  ' + '\n  '.join(bad))
    return man


def check(out=OUT, log=print):
    """Problems ([] = none): every built archive parses, every named picture/entity exists, stock strings are unchanged."""
    man = json.load(open(os.path.join(out, 'manifest.json')))
    bad = []
    if md5(BASE_SCENE) != man['base_scene'] or md5(BASE_PATCH) != man['base_patch']:
        bad.append('the live overlay files changed since the build')
    base = zipfile.ZipFile(BASE_SCENE)
    stock_names = loc_titles(base.read('Scenes/kaneandlynchEnglish.LOC'))
    for sname, info in man['sets'].items():
        sz = os.path.join(out, sname, 'Overlay', 'Scenes', 'kaneandlynch.zip'); pz = os.path.join(out, sname, 'Overlay', 'Patch01.zip')
        z = zipfile.ZipFile(sz); p = zipfile.ZipFile(pz)
        if z.testzip() or p.testzip():
            bad.append(sname + ': zip crc')
        P.NAMES = ['LobbyMap_' + m for m in sorted({v[9:] for v in info['pictures'].values() if v.startswith('LobbyMap_')})] + \
                  [v for v in info['pictures'].values() if v.startswith('LobbyRand_')]
        P.NAMES = sorted(set(P.NAMES))
        bad += [sname + ': ' + b for b in P.check(sz, BASE_SCENE, lambda *_: None) if 'stock entities' not in b and '.LOC' not in b]
        xml = p.read('menu/frontend.xml').decode('latin-1')
        for slot, ent in info['pictures'].items():
            if 'Name="LobbyPicture%s"' % slot not in xml or ('Graphic="%s"' % ent) not in xml:
                bad.append('%s: LobbyPicture%s does not name %s' % (sname, slot, ent))
        for i in z.infolist():
            if re.match(r'Scenes/kaneandlynch\w+\.LOC$', i.filename) and i.file_size > 9:
                t = loc_titles(z.read(i))
                own = loc_titles(base.read(i.filename))            # this language's stock text
                for k in own:
                    want = info['names'].get(k, own[k])                # not renamed: the stock text
                    if t.get(k) != want:
                        bad.append('%s %s Title%s is %r, wanted %r' % (sname, i.filename, k, t.get(k), want))
                if len(z.read(i)) > 612634:
                    bad.append(i.filename + ' over the LOC cap')
        # stock strings for OnlineSet=0 are the base files: the unchanged originals
        for i in base.infolist():
            if re.match(r'Scenes/kaneandlynch\w+\.LOC$', i.filename) and i.file_size > 9 and i.filename not in z.namelist():
                bad.append('missing ' + i.filename)
        # the Arcade lists read literals now, the lobby entities exist, and the stock page 1 cannot see a Dead Men name
        hl = re.search(r'Name="HeistLevel" .*?</GuiElement>', xml, re.S)
        if not hl or 'Scenarios/Title' in hl.group(0):
            bad.append(sname + ': HeistLevel still reads the LOC')
    log('check: %d problems' % len(bad))
    return bad


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if a and a[0] == 'build':
        build(a[1] if len(a) > 1 else OUT)
    elif a and a[0] == 'check':
        for b in check(a[1] if len(a) > 1 else OUT):
            print('  ' + b)
    else:
        print(__doc__); sys.exit(1)
