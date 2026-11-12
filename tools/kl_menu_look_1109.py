#!/usr/bin/env python3
r"""kl_menu_look_1109.py - THE IN-GAME MENUS IN THE DEAD MEN LOOK, stage 1 (fonts + colour sets), 2026-11-09. STAGE ONLY: reads the LIVE overlay
menu pair, writes themed COPIES into C:\kl_build_1024\menulook_1109\stage1\ with install.py / UNDO, never installs, never opens a stock file for
writing. Plan, inventory, benches: re\menu_look_1109.md (track T9: owner 11-09 "overhaul the whole in game menu UI to make it feel more like dead
men too, even the menu button sounds; ... a button for the mod ... default on").

    python tools\kl_menu_look_1109.py inventory [--overlay <dir>]
        read-only: every <ColorSet> of the three menu XML files (name, occurrence, values, what this tool would make of it), the eight
        font chunks (face px per slot), the archives' md5s, and whether Patch01_rows12.zip is there and newer than Patch01.zip.
    python tools\kl_menu_look_1109.py stage [--overlay <dir>] [--out <dir>] [--accept-input] [--no-fonts] [--no-body] [--bars] [--face impact|anton]
        themed copies of Patch01.zip, Patch01_rows12.zip (when present: it is the file the game opens while [Lobby] Rows12=1) and
        Scenes\kaneandlynch.zip. Inputs are PINNED: the first run on the owner's PC needs --accept-input (writes pins.json with the md5s it
        read); a later run refuses when an input differs from pins.json (re-stage with --accept-input after an overlay rebuild).
          colours  <ColorSet> attribute VALUES (NormalColor FocusColor DisableColor, 0xAARRGGBB; the three names kl2.exe reads,
                   0x8ab978..0x8ab988) -> the kit's palette by NAME (COLORSETS) first, by ROLE second (kl_hud_menu._role: greys -> chalk /
                   ink / dim, reds -> coral / dead, alpha kept), anything else LEFT ALONE and logged. No tag is added or removed.
          fonts    the menu scene's eight ZTTFONT chunks re-rasterized (kl_hud.build_font: page 0 + records rebuilt, header / page 1 /
                   kerning tail kept, baseline NOT moved) with MENU_FONTS: Impact capitals (lower case drawn as capitals), light chips
                   on sizes >= CHIP_FLOOR px, none under it; H3 = the mixed-case body face, and the paragraph templates / wide text
                   blocks of frontend.xml + the scene's online.xml re-pointed at it (kl_hud_menu.repoint_body; --no-body keeps them).
                   GDI (Windows) only: --no-fonts stages colours alone (what the Linux self-test runs).
          --bars   stage 2: the scene's focus bars / lines repainted as chalk brush strokes (kl_hud_menu.repaint, 'kit' painter). Off by default.
        Writes: the themed files under their live names, pins.json, install.py (+ INSTALL / UNDO .bat), build_report.json, widths.txt (the
        longest literal row texts per font, stock vs new advance sums: overflow candidates first) and fontsheet.png (Windows, with fonts).
        PROVES before writing: the table signature of every XML file (kl_hud_menu.signature: the sequence of Window / GuiElement / ColorSet /
        ButtonGraphic / Template tags and the conditional blocks) is the input's, the member lists are the input's, and only the allowed
        members changed (the XML files, the scene's .prm / .TEX).
    python tools\kl_menu_look_1109.py check <stage dir> [--overlay <dir>]
        the same proofs on a finished stage against the live overlay, plus pins.json present and the rows12 mtime rule.

install.py (written into the stage; the kl_doors_1108 / kl_dm03cops_1108 pattern): refuses unless every live file's md5 is its pin, backs each
up as <name>.before-menulook_1109 NEXT TO it (never overwrites a backup), all or nothing, refuses while kl2.exe runs, --dry, --undo byte-exact
only when each live file is exactly what it wrote. Order: Patch01.zip FIRST, then Patch01_rows12.zip (klslot.c 981: a rows12 file OLDER than
Overlay\Patch01.zip is not used), then the scene. --variant writes <stem>_deadmen.<ext> BESIDE the live files instead (for the klslot.c
[MenuLook] variant step of re\menu_look_1109.md 4.2, not built yet) and touches nothing else.

GUESSES (nothing here has run in the game; each is in re\menu_look_1109.md 2 and 5.1): the COLORSETS values where the stock hex is not in
re\ (the roles are READ, the hex is not); chip 0 on the 19 px row font (readability of prices); that an attribute on the element wins over
its template's; the Impact stand-in (Anton when <work>\fonts has it); the widths.txt rule (advance sums are the game's widths); that the
rows12 file wants the same restyle as Patch01.zip (it is the same frontend.xml with the FALobby rows changed).
"""
import hashlib, json, os, re, shutil, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hud_menu as HM

BS = chr(92)
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OVERLAY = os.path.join(GAME, 'KLExpansion', 'Overlay')
OUT = r'C:\kl_build_1024\menulook_1109'
STAGE = 'stage1'
TAG = '.before-menulook_1109'
VARIANT = '_deadmen'
PATCH, ROWS12, SCENE = 'Patch01.zip', 'Patch01_rows12.zip', os.path.join('Scenes', 'kaneandlynch.zip')
INPUTS = (PATCH, ROWS12, SCENE)                         # rows12 is optional (absent = not staged, logged)
XML_PATCH = (HM.FRONT, HM.INGAME)                       # members of a Patch01*.zip that change
CHANGED_OK = ('.xml', '.prm', '.tex')                   # members that may differ between input and stage (lower-case endings)

# ------------------------------------------------------------------ the kit's palette (tools/kl_hud.py 1032-1040, kl_hud_menu.py, design_mock_1109.html :root)
COLORS = {
    'CHALK': (0xf3, 0xf0, 0xea), 'INK': (0x0c, 0x0c, 0x0d), 'CORAL': (0xf0, 0x47, 0x5a), 'AMBER': (0xe8, 0x83, 0x1f),
    'GREEN_HI': (0x63, 0xa6, 0x5b), 'GREEN': (0x4f, 0x8f, 0x49), 'DEAD': (0x8c, 0x31, 0x38), 'DIM': (0x8d, 0x89, 0x82),
}
# Colour sets BY NAME: (normal, focus, disable) as palette names; None = keep that attribute's value by ROLE (or as it is).
# alpha: 'keep' = the stock alpha byte stays; 'ff' = opaque on purpose (the four spare sets, re\hud_menu.md 2).
# GUESS (every row): the stock hex values are not in re\; the ROLES are (re\hud_menu.md 1.2 / 2, 2026-10-23 shop note: the first
# 'Default' has focus INK a00c0c0d; 'Header' red d7373a; the PC legend focus d00000; online.xml's second 'Default' bluish 829EC1).
COLORSETS = {
    'Default':            dict(colors=('CHALK', 'INK', 'DIM'), alpha='keep', occurrence=1),   # the FIRST definition only (online.xml defines it twice)
    'White':              dict(colors=('CHALK', 'CHALK', 'DIM'), alpha='keep'),
    'Header':             dict(colors=('CORAL', 'CORAL', 'DEAD'), alpha='keep'),
    'OnFocus':            dict(colors=('INK', 'INK', 'DIM'), alpha='keep'),                # text ON a light plate, always (stock ff000000 x2 / ff888888;
                                                                                          # RecCSFocus receivers, lobby headers, Bonus / Penalty). 11-10 02:55
                                                                                          # shots: the earlier CHALK normal was PALE on the plate = unreadable.
                                                                                          # Live files built before this fix: tools/kl_menu_plates_1110.py.
    'Legend':             dict(colors=('CHALK', 'CORAL', 'DIM'), alpha='keep'),
    'AssignKeys':         dict(colors=('CHALK', 'INK', 'DIM'), alpha='keep'),
    'KLFocus':            dict(colors=('CHALK', 'CORAL', 'DIM'), alpha='keep'),              # mkoverlay.py: the Mod settings rows show focus by COLOUR (no bar)
    'Debug':              dict(colors=('GREEN_HI', 'GREEN_HI', 'GREEN'), alpha='ff'),       # spare: money columns (kl_hud_menu GREEN_SET)
    'DirtyMoneyColorSet': dict(colors=('GREEN_HI', 'GREEN_HI', 'GREEN'), alpha='ff'),
    'WANTED':             dict(colors=('AMBER', 'AMBER', 'DEAD'), alpha='ff'),               # the traitor line
    'Black':              dict(colors=('INK', 'INK', 'INK'), alpha='ff'),
}
LEFT_ALONE = {('Default', 2)}                            # online.xml's bluish second Default: which definition wins is NOT established (re\hud_menu.md risk 2)
COLOR_ATTRS = HM.COLOR_ATTRS                             # NormalColor FocusColor DisableColor

# ------------------------------------------------------------------ fonts (re\hud_menu.md 11.1 sizes; the owner's look = Impact capitals, light chips)
CHIP_FLOOR = 16                                          # px: no chips under it (kl_hud.py DRAFT_SPECS_ANTON note: a 0.5 px nick eats a 6 px stem)
STOCK_CAP = HM.STOCK_CAP                                 # READ: the capital 'H' height of the stock menu fonts
# slot: (display face?, weight, px, track px, caps, chip amount)   display face = Impact (Anton with <work>\fonts), body face = Segoe UI Black (Montserrat)
MENU_FONTS = {
    'Header':    ('display', 400, 28, 1, True, 0.5),
    'H1':        ('display', 400, 28, 1, True, 0.5),
    'Menu':      ('display', 400, 20, 1, True, 0.3),
    'Text':      ('display', 400, 19, 1, True, 0.0),    # GUESS: no chips on the row font (prices, names) although 19 >= CHIP_FLOOR
    'H2':        ('display', 400, 19, 1, True, 0.0),
    'Button':    ('display', 400, 17, 1, True, 0.0),
    'DebugText': ('body', 800, 15, 3, True, 0.0),
    'H3':        ('body', 600, 17, 0, False, 0.0),      # the paragraph face (mixed case): kl_hud_menu.repoint_body points tips / help / legal at it
}
FACES = {'impact': {'display': 'Impact', 'body': 'Segoe UI Black'},
         'anton':  {'display': 'Anton', 'body': 'Montserrat'}}
STANDIN = {'Anton': 'Impact', 'Montserrat': 'Segoe UI Black'}
WIDTH_FONT_DEFAULT = 'Text'                              # an element without Font= draws with the Text slot (GUESS: the common case in the files)
WIDTH_TOP = 12                                           # longest literals per font listed in widths.txt


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ colours
def argb(v):
    """'0xAARRGGBB' -> (a, r, g, b) or None (the stock files hold two malformed values: left alone)."""
    return HM._hex(v)


def hexa(t):
    return '0x%02x%02x%02x%02x' % tuple(t)


def chip_for(px, chip):
    """The chip amount a slot gets: none under CHIP_FLOOR px whatever the table says."""
    return 0.0 if px < CHIP_FLOOR else float(chip)


def color_for(name, occurrence, attr, old):
    """-> (new argb, how) for one colour attribute of a <ColorSet>; new None = left alone. how: 'name' | 'role' | 'kept' | 'malformed'."""
    if old is None:
        return None, 'malformed'
    if (name, occurrence) in LEFT_ALONE:
        return None, 'kept'
    spec = COLORSETS.get(name)
    if spec and spec.get('occurrence', occurrence) == occurrence:
        rgb = COLORS[spec['colors'][COLOR_ATTRS.index(attr)]]
        a = 0xff if spec['alpha'] == 'ff' else old[0]
        return (a,) + rgb, 'name'
    new = HM._role(old)
    return (new, 'role') if new else (None, 'kept')


def restyle_colorsets(xml):
    """-> (xml, rows): every <ColorSet> attribute decided; rows = [(name, occurrence, attr, old text, new text or '-', how)]."""
    seen, rows = {}, []

    def fn(t, text):
        if t.name != 'ColorSet':
            return None
        name = dict(t.attrs).get('Name', '')
        seen[name] = seen.get(name, 0) + 1
        occ = seen[name]
        spec = COLORSETS.get(name)
        attrs = dict(t.attrs)
        # the four spare sets get a REAL DisableColor= added where the file only has the misspelt one (an attribute, no table entry)
        want = list(COLOR_ATTRS) if (spec and spec['alpha'] == 'ff') else [a for a in COLOR_ATTRS if a in attrs]
        for an in want:
            old_txt = attrs.get(an)
            old = argb(old_txt) if old_txt is not None else (0xff, 0, 0, 0)      # an added attribute: alpha ff
            new, how = color_for(name, occ, an, old)
            if new is not None:
                text = HM.set_attr(text, an, hexa(new))
            rows.append((name, occ, an, old_txt if old_txt is not None else '(absent)', hexa(new) if new else '-', how))
        return text
    xml, _n = HM.rewrite(xml, fn)
    return xml, rows


# ------------------------------------------------------------------ fonts
def font_specs(face='impact', have=None):
    """MENU_FONTS resolved to real faces: {slot: (face, weight, px, track, caps, chip)}. have(face) -> bool says which faces are installed
    (GDI on Windows; the test passes its own); a missing draft face falls back to its STANDIN."""
    if face not in FACES:
        raise ValueError('--face %s: impact or anton' % face)
    if have is None:
        try:
            import kl_hud
            g = kl_hud._Gdi()
            have = g.has
        except Exception:                                 # no GDI here (Linux): stand-ins
            have = lambda f: f in ('Impact', 'Segoe UI Black')
    out = {}
    for slot, (kind, weight, px, track, caps, chip) in MENU_FONTS.items():
        f = FACES[face][kind]
        if not have(f):
            f = STANDIN.get(f, f)
        out[slot] = (f, weight, px, track, caps, chip_for(px, chip))
    return out


def bake_fonts(zs, stem, tex_bytes, specs, log=print):
    """-> (new .prm, new .TEX, {slot: report}): the eight menu fonts rebuilt with `specs` (kl_hud.build_font, baseline kept)."""
    import kl_hud, kl_prmgraph as G, kl_texmat as T
    fonts = HM.font_chunks(zs, stem)
    p = G.read(zs.read(stem + '.prm'), 'dd'); tex = T.read_tex(tex_bytes)
    reps = {}
    for name, ci in sorted(fonts.items(), key=lambda kv: kv[1]):
        face, weight, px, track, caps, chip = specs[name]
        chunk, entries, rep = kl_hud.build_font(p.chunks[ci], tex, face, weight, 1.0, log, caps, chip, px=px, track=track, baseline=False)
        p.chunks[ci] = chunk
        for tid, e in entries.items():
            tex.tex[tid] = T.Texture(e, tex.tex[tid].faces, tex.tex[tid].cube, tex.tex[tid].frames, tex.tex[tid].group)
        _h, recs, _t = kl_hud.parse(chunk)
        rep['cap'] = next((r[7] for r in recs if r[0] == ord('H')), 0)
        rep['chip'] = chip
        reps[name] = rep
        log('  font %-9s chunk %d: %s %d px w%d, track %s, chip %.1f, capitals %s px (stock %s), %d glyphs (%d kept)'
            % (name, ci, rep['face'], rep['px'], weight, rep['track'], chip, rep['cap'], STOCK_CAP.get(name, '?'), rep['glyphs'], rep['kept']))
    return G.write(p), T.write_tex(tex), reps


# ------------------------------------------------------------------ widths (overflow candidates)
LITERAL = re.compile(r'\bText\s*=\s*"%([^"]+)"')


def literals(xml):
    """[(font slot, literal text)] of every Text="%..." in the file (the literal strings the pages show as written), with the element's
    Font= (else WIDTH_FONT_DEFAULT). Localised keys (.LOC) are not resolvable here: NEEDS FILE for those rows."""
    out = []
    for t in HM.tags(xml):
        if t.close:
            continue
        a = dict(t.attrs)
        s = a.get('Text', '')
        if s.startswith('%') and len(s) > 1:
            out.append((a.get('Font', WIDTH_FONT_DEFAULT), s[1:]))
    return out


def advance_table(chunk):
    """{char: advance px} of one ZTTFONT chunk (kl_hud.parse record field 10)."""
    import kl_hud
    _h, recs, _t = kl_hud.parse(chunk)
    return {r[0]: r[10] for r in recs}


def text_width(adv, s, caps):
    w = 0
    for ch in s:
        c = ch.upper() if caps and ch.islower() else ch
        w += adv.get(ord(c), adv.get(ord(ch), adv.get(ord('M'), 0)))
    return w


def widths_report(xmls, old_chunks, new_chunks, specs, top=WIDTH_TOP):
    """-> lines for widths.txt: per font the longest literals, stock vs new width, sorted by growth (worst first)."""
    rows = []
    per_font = {}
    for xml in xmls:
        for slot, s in literals(xml):
            per_font.setdefault(slot, set()).add(s)
    for slot, texts in sorted(per_font.items()):
        if slot not in old_chunks or slot not in new_chunks:
            continue
        ao, an = advance_table(old_chunks[slot]), advance_table(new_chunks[slot])
        caps = specs[slot][4]
        for s in sorted(texts, key=len, reverse=True)[:top * 3]:
            wo, wn = text_width(ao, s, False), text_width(an, s, caps)
            rows.append((slot, s, wo, wn, (wn - wo) * 100.0 / wo if wo else 0.0))
    rows.sort(key=lambda r: -r[4])
    lines = ['# widths of the longest literal texts per font: stock advance sum -> new (percent); > 15 % = look at that row in ML1 first',
             '# literal Text="%..." only; .LOC keys (most rows) are NEEDS FILE - see re/menu_look_1109.md 2.1']
    for slot, s, wo, wn, pc in rows[:top * len(per_font) or top]:
        lines.append('%-9s %4d -> %4d px (%+5.1f %%)  %s' % (slot, wo, wn, pc, s[:60]))
    return lines


# ------------------------------------------------------------------ archives
def inputs_present(overlay):
    """[(relative name, absolute path)] of the inputs that exist; rows12 may be absent; the other two must be there."""
    out = []
    for n in INPUTS:
        p = os.path.join(overlay, n)
        if os.path.isfile(p):
            out.append((n, p))
        elif n != ROWS12:
            raise ValueError('REFUSED: %s is not there (an overlay needs %s and %s)' % (p, PATCH, SCENE))
    return out


def rows12_ok(overlay):
    """True when Patch01_rows12.zip is absent or not older than Patch01.zip (klslot.c 981: else the game ignores it)."""
    r, p = os.path.join(overlay, ROWS12), os.path.join(overlay, PATCH)
    return (not os.path.isfile(r)) or (not os.path.isfile(p)) or os.path.getmtime(r) >= os.path.getmtime(p)


def check_pins(present, out_dir, accept, log=print):
    """pins.json rule: --accept-input writes the md5s read; otherwise every input must equal its pin. -> {name: md5}."""
    pins_path = os.path.join(out_dir, 'pins.json')
    got = {n: fmd5(p) for n, p in present}
    if accept:
        return got
    if not os.path.isfile(pins_path):
        raise ValueError('REFUSED: no %s yet: the first stage on this PC needs --accept-input (it records the input md5s as the pins)' % pins_path)
    pins = json.load(open(pins_path))
    for n, m in got.items():
        if pins.get(n) != m:
            raise ValueError('REFUSED: %s is md5 %s, pinned %s (the overlay changed: re-stage with --accept-input)' % (n, m, pins.get(n)))
    return got


def theme_patch(src, dst, body, log):
    """A Patch01*.zip: frontend.xml + ingame.xml colour sets (and the body font re-point on frontend.xml). -> {member: rows}."""
    zp = zipfile.ZipFile(src); new = {}; report = {}
    for member in XML_PATCH:
        i = HM._member(zp, member)
        if i is None:
            raise ValueError('%s has no %s' % (src, member))
        xml = zp.read(i).decode('latin-1')
        xml2, rows = restyle_colorsets(xml)
        if body:
            xml2, _n = HM.repoint_body(xml2, member, log)        # a no-op on ingame.xml (BODY_FILES)
        if HM.signature(xml) != HM.signature(xml2):
            raise ValueError('%s %s: the table signature moved - refused' % (src, member))
        new[i.filename.lower()] = xml2.encode('latin-1')
        report[member] = rows
        log('  %s %s: %d colour attributes decided (%s)' % (os.path.basename(src), member, len(rows), summary(rows)))
    HM._rezip(src, dst, new)
    return report


def theme_scene(src, dst, body, fonts, bars, specs, log):
    """Scenes\\kaneandlynch.zip: online.xml colour sets (+ body re-point), the eight fonts, optionally the bars. -> (rows, font reports, old/new chunks)."""
    zs = zipfile.ZipFile(src); new = {}
    i = HM._member(zs, HM.ONLINE)
    if i is None:
        raise ValueError('%s has no %s' % (src, HM.ONLINE))
    xml = zs.read(i).decode('latin-1')
    xml2, rows = restyle_colorsets(xml)
    if body:
        xml2, _n = HM.repoint_body(xml2, HM.ONLINE, log)
    if HM.signature(xml) != HM.signature(xml2):
        raise ValueError('%s %s: the table signature moved - refused' % (src, HM.ONLINE))
    new[i.filename.lower()] = xml2.encode('latin-1')
    log('  %s %s: %d colour attributes decided (%s)' % (os.path.basename(src), HM.ONLINE, len(rows), summary(rows)))
    stem = next(n for n in zs.namelist() if n.lower().endswith('.gms'))[:-4]
    reps, old_chunks, new_chunks = {}, {}, {}
    tex_bytes = None
    if bars:
        tex_bytes, done = HM.repaint(zs, stem, log, 'kit')
        new[(stem + '.TEX').lower()] = tex_bytes
        log('  pictures: %d textures repainted (%d bars, %d lines)' % (len(done), sum(1 for v in done.values() if v[0] == 'bar'), sum(1 for v in done.values() if v[0] == 'line')))
    if fonts:
        import kl_prmgraph as G
        p0 = G.read(zs.read(stem + '.prm'), 'dd')
        chunks0 = HM.font_chunks(zs, stem)
        old_chunks = {n: p0.chunks[ci] for n, ci in chunks0.items()}
        prm, tex2, reps = bake_fonts(zs, stem, tex_bytes or zs.read(stem + '.TEX'), specs, log)
        new[(stem + '.prm').lower()] = prm
        new[(stem + '.TEX').lower()] = tex2
        p1 = G.read(prm, 'dd')
        new_chunks = {n: p1.chunks[ci] for n, ci in chunks0.items()}
    else:
        log('  fonts: SKIPPED (--no-fonts): colours only; the scene .prm / .TEX are the input\'s')
    HM._rezip(src, dst, new)
    return rows, reps, old_chunks, new_chunks, xml2


def summary(rows):
    c = {}
    for r in rows:
        c[r[5]] = c.get(r[5], 0) + 1
    return ', '.join('%d by %s' % (v, k) for k, v in sorted(c.items()))


def members_ok(src, dst):
    """Input and stage have the same member list and differ only in CHANGED_OK members. -> [changed member names]."""
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise ValueError('%s: member list differs from %s' % (dst, src))
        changed = [m for m in a.namelist() if a.read(m) != b.read(m)]
    bad = [m for m in changed if not m.lower().endswith(CHANGED_OK)]
    if bad:
        raise ValueError('%s: members changed outside the allowed set: %s' % (dst, bad))
    return changed


def signatures_ok(src, dst, members):
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        for m in members:
            i, j = HM._member(a, m), HM._member(b, m)
            if i is None or j is None:
                raise ValueError('%s: %s missing' % (dst, m))
            if HM.signature(a.read(i).decode('latin-1')) != HM.signature(b.read(j).decode('latin-1')):
                raise ValueError('%s %s: table signature differs from the input' % (dst, m))


# ------------------------------------------------------------------ install template
INSTALL = r'''r"""Installs / undoes the DEAD MEN MENU LOOK stage @STAGE@ (tools/kl_menu_look_1109.py) on the live overlay menu files.

  python install.py            install: each live file -> <name>@TAG@ NEXT TO it (an existing backup is NEVER overwritten: refuses), then the
                               themed copy in its place. Order: Patch01.zip FIRST, then Patch01_rows12.zip, then the scene (klslot.c 981: a
                               rows12 file older than Overlay\Patch01.zip is not used).
  python install.py --undo     every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --variant  write <stem>_deadmen.<ext> BESIDE each live file instead (nothing live is touched; for the klslot.c [MenuLook]
                               variant step, re/menu_look_1109.md 4.2); --variant --undo removes those copies (md5-checked)
  python install.py --dry      read-only: every pin and what would happen (also with --undo / --variant)
  --game <dir>                 another Dog Days folder (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches a stock file
(<DD>\Patch01.zip, <DD>\Scenes\...) or KL_PortBackup: the overlay files are the mod's own copies."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG, VARIANT = '@TAG@', '@VARIANT@'
FILES = @FILES@          # (relative name under KLExpansion\Overlay, live md5 pinned at stage time, md5 of the themed copy)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def variant_name(live):
    stem, ext = os.path.splitext(live)
    return stem + VARIANT + ext


def main(a):
    undo, dry, variant = '--undo' in a, '--dry' in a, '--variant' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    ov = os.path.join(game, 'KLExpansion', 'Overlay')
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(ov, n), os.path.join(ov, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-28s live %s' % (n, cur))
        if variant:
            var = variant_name(live)
            if undo:
                if not os.path.isfile(var):
                    print('REFUSED: no variant %s' % var); return 1
                if md5(var) != new:
                    print('REFUSED: %s is not the staged md5 %s' % (var, new)); return 1
            else:
                if os.path.exists(var):
                    print('REFUSED: %s exists already (remove it with --variant --undo first)' % var); return 1
                if not os.path.isfile(src) or md5(src) != new:
                    print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
            plan.append((n, var, None, src)); continue
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or the overlay was rebuilt: re-stage with --accept-input)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) for p in plan) * 2 + (256 << 20)
        if shutil.disk_usage(ov).free < need:
            print('REFUSED: less than the files x2 + 256 MB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s%s' % ('remove' if (undo and variant) else 'restore' if undo else 'write' if variant else 'install', p[1], '' if variant else ' (backup %s)' % p[2]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if variant:
                if undo:
                    os.remove(live)
                else:
                    shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
                print('%s: %s %s' % (n, 'variant removed' if undo else 'variant written', live))
                continue
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo and not variant:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(stage_dir, files, log):
    src = (INSTALL.replace('@GAME@', GAME).replace('@TAG@', TAG).replace('@VARIANT@', VARIANT)
           .replace('@STAGE@', os.path.basename(stage_dir)).replace('@FILES@', repr(files)))
    open(os.path.join(stage_dir, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL menu look 1109.bat', ''), ('UNDO menu look 1109.bat', ' --undo')):
        open(os.path.join(stage_dir, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    log('  install.py + bats written (%d files)' % len(files))


# ------------------------------------------------------------------ commands
def inventory(overlay=OVERLAY, log=print):
    present = inputs_present(overlay)
    log('overlay %s' % overlay)
    for n, p in present:
        log('  %-22s md5 %s  %d bytes' % (n, fmd5(p), os.path.getsize(p)))
    if not any(n == ROWS12 for n, _p in present):
        log('  %-22s ABSENT (the game opens Patch01.zip itself while [Lobby] Rows12=1 says so in the log)' % ROWS12)
    elif not rows12_ok(overlay):
        log('  WARNING: %s is OLDER than %s: klslot.c does not use it (rebuild with tools/kl_lobby12.py)' % (ROWS12, PATCH))
    out = {}
    for n, p in present:
        z = zipfile.ZipFile(p)
        members = [HM.ONLINE] if n == SCENE else list(XML_PATCH)
        for m in members:
            i = HM._member(z, m)
            if i is None:
                log('  %s: no %s' % (n, m)); continue
            xml = z.read(i).decode('latin-1')
            _x, rows = restyle_colorsets(xml)
            log('  %s %s: %d colour sets' % (n, m, len(HM.colorset_list(xml))))
            for name, occ, attr, old, new, how in rows:
                log('    %-20s #%d %-12s %-12s -> %-12s %s' % (name, occ, attr, old, new, how))
            out[(n, m)] = rows
        if n == SCENE:
            stem = next(k for k in z.namelist() if k.lower().endswith('.gms'))[:-4]
            try:
                import kl_hud, kl_prmgraph as G
                p0 = G.read(z.read(stem + '.prm'), 'dd')
                for name, ci in sorted(HM.font_chunks(z, stem).items(), key=lambda kv: kv[1]):
                    h, recs, _t = kl_hud.parse(p0.chunks[ci])
                    cap = next((r[7] for r in recs if r[0] == ord('H')), 0)
                    log('  font %-9s chunk %d: %d px, capital H %d px, %d records' % (name, ci, h[2], cap, len(recs)))
            except Exception as e:                        # a scene without fonts (the test's), or a reader problem: say so
                log('  fonts: not read (%s)' % e)
    return out


def stage(overlay=OVERLAY, out=OUT, accept=False, fonts=True, body=True, bars=False, face='impact', log=print, have=None):
    present = inputs_present(overlay)
    stage_dir = os.path.join(out, STAGE)
    os.makedirs(stage_dir, exist_ok=True)
    pins = check_pins(present, stage_dir, accept, log)
    if not rows12_ok(overlay):
        log('  WARNING: %s is older than %s in the overlay: the game ignores it today (tools/kl_lobby12.py rebuilds it); staged anyway' % (ROWS12, PATCH))
    specs = font_specs(face, have) if fonts else None
    if specs:
        for k, v in specs.items():
            log('  spec %-9s %s w%d %d px track %d caps %s chip %.1f' % ((k,) + v))
    tmp = tempfile.mkdtemp(prefix='menulook_', dir=out)
    report = dict(overlay=overlay, pins=pins, fonts=fonts, body=body, bars=bars, face=face, colours={}, font_reports={}, changed={})
    files, xmls = [], []
    try:
        old_chunks = new_chunks = {}
        for n, p in present:
            dst = os.path.join(tmp, n)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            log('== %s' % n)
            if n == SCENE:
                rows, reps, old_chunks, new_chunks, xml2 = theme_scene(p, dst, body, fonts, bars, specs, log)
                report['colours'][n + '|' + HM.ONLINE] = rows
                report['font_reports'] = {k: {kk: vv for kk, vv in v.items() if kk != 'glyph list'} for k, v in reps.items()}
                xmls.append(xml2)
                sig_members = [HM.ONLINE]
            else:
                rep = theme_patch(p, dst, body, log)
                for m, rows in rep.items():
                    report['colours'][n + '|' + m] = rows
                with zipfile.ZipFile(dst) as zb:
                    xmls.append(zb.read(HM._member(zb, HM.FRONT)).decode('latin-1'))
                sig_members = list(XML_PATCH)
            changed = members_ok(p, dst)
            signatures_ok(p, dst, sig_members)
            report['changed'][n] = changed
            log('  %s: %d members changed (%s); table signature = input' % (n, len(changed), ', '.join(changed)))
        for n, p in present:
            final = os.path.join(stage_dir, n)
            os.makedirs(os.path.dirname(final), exist_ok=True)
            shutil.move(os.path.join(tmp, n), final)
            files.append((n, pins[n], fmd5(final)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(pins, open(os.path.join(stage_dir, 'pins.json'), 'w'), indent=1)
    if fonts and old_chunks:
        lines = widths_report(xmls, old_chunks, new_chunks, specs)
        open(os.path.join(stage_dir, 'widths.txt'), 'w').write('\n'.join(lines) + '\n')
        log('  widths.txt: %d rows (worst growth first)' % (len(lines) - 2))
        try:
            HM.fontsheet(overlay, stage_dir, os.path.join(stage_dir, 'fontsheet.png'), log)
        except Exception as e:                            # the sheet is a convenience: say why it is missing, do not fail the stage
            log('  fontsheet.png not written (%s)' % e)
    write_install(stage_dir, files, log)
    report['files'] = files
    json.dump(report, open(os.path.join(stage_dir, 'build_report.json'), 'w'), indent=1, default=str)
    for n, o, w in files:
        log('%-22s %s -> %s' % (n, o, w))
    return files


def check(stage_dir, overlay=OVERLAY, log=print):
    """A finished stage against the live overlay: pins, member lists, allowed members, table signatures, rows12 rule. -> [problems]."""
    bad = []
    pins_path = os.path.join(stage_dir, 'pins.json')
    if not os.path.isfile(pins_path):
        bad.append('no pins.json')
        pins = {}
    else:
        pins = json.load(open(pins_path))
    for n, p in inputs_present(overlay):
        s = os.path.join(stage_dir, n)
        if not os.path.isfile(s):
            bad.append('%s not staged' % n); continue
        if pins.get(n) != fmd5(p):
            bad.append('%s: live md5 %s is not the pin %s' % (n, fmd5(p), pins.get(n)))
        try:
            changed = members_ok(p, s)
            signatures_ok(p, s, [HM.ONLINE] if n == SCENE else list(XML_PATCH))
            log('  %s: ok (%d members changed: %s)' % (n, len(changed), ', '.join(changed)))
        except ValueError as e:
            bad.append(str(e))
    if not rows12_ok(overlay):
        bad.append('%s is older than %s in the overlay (klslot.c ignores it)' % (ROWS12, PATCH))
    if not os.path.isfile(os.path.join(stage_dir, 'install.py')):
        bad.append('no install.py')
    log('check: %s' % ('PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


def main(a):
    if not a or a[0] not in ('inventory', 'stage', 'check'):
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    overlay = opt('--overlay', OVERLAY)
    if a[0] == 'inventory':
        inventory(overlay); return 0
    if a[0] == 'check':
        return 1 if check(a[1], overlay) else 0
    stage(overlay, opt('--out', OUT), accept='--accept-input' in a, fonts='--no-fonts' not in a, body='--no-body' not in a,
          bars='--bars' in a, face=opt('--face', 'impact'))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as e:
        print(e); sys.exit(1)
