r"""mkoverlay.py <KLHook.ini> <stock Patch01.zip> <out folder>   builds <out>\Overlay\Patch01.zip: the menu of the expansion.

The stock Patch01.zip is only READ. The result goes into <game>\KLExpansion\Overlay\ (copy it there yourself, or give
<game>\KLExpansion as <out>); klslot.c answers the game's open of Patch01.zip with it, so nothing stock is replaced.
It holds the stock members (menu/ingame.xml byte for byte) and a menu/frontend.xml changed in three places only:

 1. Arcade page (window HeistModeMenu): the stock 'Start' button gets  Option="Dummy" OptionValue="1";  one button per
    expansion page is added below the five stock ones:  Window="HeistPlayMenu<N>" Text="%<Title>" Option="Dummy"
    OptionValue="<N>", with a focus bar of its own (FocusBar_short#06.., graphics the frontend scene already has).
 2. One window HeistPlayMenu<N> per page: a copy of the stock map page HeistPlayMenu with
      - the headline replaced by the page title,
      - the title of every slot that has a map on the page replaced by literal text (a text that starts with '%' is
        shown as written, re\menus.md 2.6),
      - the picture of such a slot replaced if the ini names one (any graphic of the frontend scene; default: the
        slot's stock picture),
      - the element that prints the STOCK map's briefing for the slot removed.
    Everything else - element names, the selector 'HeistLevel', Accept - is the stock page's, so the keys, the gamepad
    template and klauto's scripts (msg HeistLevel StartGame) work on it unchanged. Element names are per window in
    stock too (e.g. 'CenterBox' is used by five windows).
 3. Nothing else.

'Dummy' is a spare menu option nothing in kl2.exe reads (re\menus.md 3.1); klslot.c reads it as the page number and
uses [Redirect.<N>] for a slot from the moment that slot's archive is opened. Entry k of a page is the engine's slot
{F01,F02,F03,F04,F06,F07,F05,F08,F09}[k]; a slot without a map on the page keeps its stock title and loads what
[Redirect] or the stock game gives it.

KLHook.ini (the same file the hook reads):
    [Redirect.2]            slot = map folder under KLExpansion\Maps (klslot.c)
    F01=DM03
    F02=DM01
    [Page.2]
    Title=Dead Men maps     button and headline (default: 'Expansion maps <N>')
    F01=Withdrawal          title of the entry (default: the map folder's name)
    F01.Picture=LevelPicture_H03      optional
Pages 2..5 (four focus bars are free below the stock buttons).

NOT SEEN IN THE GAME (nothing here was run): that the patch archive's frontend.xml is the one in effect (re\menus.md 1
says so for the stock Patch01.zip), that OptionValue is stored before the window opens (the stock main menu sets
MP_MultiPlayerMenu the same way), that a sixth button fits the Arcade page's layout, the menu system's element limit
(5096, re\menus.md 2.5; a page adds about 60), and a NEW picture: that needs a texture and an entity in the frontend
scene (Scenes\kaneandlynch.zip through the Overlay) - a packager job, not done here.
KNOWN: the lobby title, the briefing and the Steam leaderboard still belong to the stock map of the slot (klslot.c).
"""
import configparser, hashlib, io, os, re, sys, time, zipfile

ORDER = [1, 2, 3, 4, 6, 7, 5, 8, 9]            # menu entry k -> slot number (kl2 0x746570)
MEMBER = 'menu/frontend.xml'


def esc(t):
    """Text for an attribute. Whether the game's XML reader knows entities (&amp; ...) is not established, and the stock
    file uses none inside a literal text: characters that would need one are refused rather than guessed at."""
    bad = [c for c in '&"<>' if c in t] + [c for c in t if ord(c) < 32 or ord(c) > 126]
    if bad:
        raise SystemExit('title %r: the characters %s cannot be used (plain ASCII without & " < > only)' % (t, ' '.join(sorted(set(bad)))))
    return t


def pages(ini):
    """[(n, title, {slot number: (map folder, entry title, picture or None)})] from [Redirect.N] / [Page.N]."""
    cp = configparser.RawConfigParser(strict=False, delimiters=('=',), comment_prefixes=(';', '#'), interpolation=None)
    cp.optionxform = str
    cp.read(ini)
    out = []
    for n in range(2, 6):
        r = 'Redirect.%d' % n
        if not cp.has_section(r):
            continue
        pg = dict(cp.items('Page.%d' % n)) if cp.has_section('Page.%d' % n) else {}
        ent = {}
        for k, v in cp.items(r):
            m = re.fullmatch(r'[Ff]0([1-9])', k)
            if not m:
                print('  [%s] %s: not one of F01..F09 - no menu entry for it' % (r, k)); continue
            ent[int(m.group(1))] = (v.strip(), pg.get(k, v.strip()), pg.get(k + '.Picture'))
        if ent:
            out.append((n, pg.get('Title', 'Expansion maps %d' % n), ent))
    for n in range(6, 10):
        if cp.has_section('Redirect.%d' % n):
            print('  [Redirect.%d]: the hook uses it, but the menu has room for pages 2..5 only - no button for it' % n)
    return out


def one(pattern, text, what, flags=0):
    m = list(re.finditer(pattern, text, flags))
    if len(m) != 1:
        raise SystemExit('frontend.xml is not the one this script knows: %d matches for %s' % (len(m), what))
    return m[0]


def build(xml, pgs):
    nl = '\r\n' if '\r\n' in xml else '\n'
    # the stock map page, whole
    w = one(r'[ \t]*<Window Name="HeistPlayMenu" [^>]*>.*?</Window>[ \t]*\r?\n', xml, 'the window HeistPlayMenu', re.S)
    page = w.group(0)
    new = ''
    for n, title, ent in pgs:
        p = page.replace('<Window Name="HeistPlayMenu" ', '<Window Name="HeistPlayMenu%d" ' % n, 1)
        h = one(r'(<GuiElement Template="HeadlineText" Text=)"HeistTitle"', p, 'the headline')
        p = p[:h.start()] + h.group(1) + '"%%%s"' % esc(title) + p[h.end():]
        b = one(r'[ \t]*<GuiElement Type="MercsShowInfo" TagName="HeistBriefing"[^>]*/>[ \t]*\r?\n', p, 'the briefing element')
        p = p[:b.start()] + p[b.end():]
        for slot, (folder, name, pic) in sorted(ent.items()):
            t = one(r'<Text Text="/Menu/Online/Scenarios/Title%02d" />' % slot, p, 'the title of slot %d' % slot)
            p = p[:t.start()] + '<Text Text="%%%s" />' % esc(name) + p[t.end():]
            if pic:
                g = one(r'(Name="H%02d_LevelPicture" Template="LevelPicture_T" Graphic=)"LevelPicture_H%02d"' % (slot, slot), p, 'the picture of slot %d' % slot)
                p = p[:g.start()] + g.group(1) + '"%s"' % esc(pic) + p[g.end():]
        new += nl + '  <!-- KLExpansion page %d: a copy of HeistPlayMenu (mkoverlay.py) -->' % n + nl + p
    xml = xml[:w.end()] + new + xml[w.end():]
    # the Arcade page: option on the stock button, one more button and focus bar per page
    a = one(r'[ \t]*<Window Name="HeistModeMenu" [^>]*>.*?</Window>', xml, 'the window HeistModeMenu', re.S)
    arc = a.group(0)
    s = one(r'(<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu" Text="Button_StartHeist"\s+FocusGraphic="HMfbl#01" FadeInDelay="0\.15" Y="220")(/>)', arc, 'the Start button')
    arc = arc[:s.start()] + s.group(1) + ' Option="Dummy" OptionValue="1"' + s.group(2) + arc[s.end():]
    f1 = one(r'([ \t]*)<GuiElement Name="HMfbl#01" Y="211" [^>]*/>', arc, 'the first focus bar')
    f5 = one(r'[ \t]*<GuiElement Name="HMfbl#05" Y="347" [^>]*/>[ \t]*\r?\n', arc, 'the fifth focus bar')
    ind = f1.group(1); btn = bars = ''
    for i, (n, title, ent) in enumerate(pgs):
        k = 6 + i; y = 390 + 34 * i
        btn += (ind + '<GuiElement Type="OpenWindow" Template="HM_Button" Window="HeistPlayMenu%d" Text="%%%s"' % (n, esc(title)) + nl +
                ind + '            FocusGraphic="HMfbl#%02d" FadeInDelay="0.15" Y="%d" Option="Dummy" OptionValue="%d"/>' % (k, y, n) + nl + nl)
        bars += ind + '<GuiElement Name="HMfbl#%02d" Y="%d" Graphic="FocusBar_short#%02d" Template="HM_FocusBar" MouseFocusW="239" />' % (k, y - 9, k) + nl
    arc = arc[:f5.end()] + bars + arc[f5.end():]
    arc = arc[:f1.start()] + ind + '<!-- KLExpansion: one button per expansion page (mkoverlay.py) -->' + nl + btn + arc[f1.start():]
    return xml[:a.start()] + arc + xml[a.end():]


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    ini, stock, out = sys.argv[1:]
    pgs = pages(ini)
    if not pgs:
        raise SystemExit('no [Redirect.2] .. [Redirect.5] section with F01..F09 lines in %s: nothing to build' % ini)
    z = zipfile.ZipFile(stock)
    names = {i.filename.lower(): i for i in z.infolist()}
    if MEMBER not in names:
        raise SystemExit('%s has no %s' % (stock, MEMBER))
    raw = z.read(names[MEMBER]); xml = raw.decode('latin-1')
    res = build(xml, pgs).encode('latin-1')
    dst = os.path.join(out, 'Overlay'); os.makedirs(dst, exist_ok=True); path = os.path.join(dst, 'Patch01.zip')
    if os.path.exists(path) and os.path.samefile(path, stock):
        raise SystemExit('refusing to write over the stock archive')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():                       # same members, same order, same names
            if i.filename.lower() == MEMBER:
                n = zipfile.ZipInfo(i.filename, time.localtime()[:6]); n.compress_type = zipfile.ZIP_DEFLATED; n.external_attr = i.external_attr
                o.writestr(n, res)
            else:
                n = zipfile.ZipInfo(i.filename, i.date_time); n.compress_type = i.compress_type; n.external_attr = i.external_attr
                o.writestr(n, z.read(i))
    # read back and say what is in it
    c = zipfile.ZipFile(path); back = c.read(names[MEMBER].filename)
    assert back == res and all(c.read(i.filename) == z.read(i.filename) for i in z.infolist() if i.filename.lower() != MEMBER)
    print('%s: %d members, %s %d -> %d bytes (stock sha1 %s)' % (path, len(c.namelist()), MEMBER, len(raw), len(res), hashlib.sha1(raw).hexdigest()[:12]))
    for n, title, ent in pgs:
        print('  page %d "%s": Arcade button -> window HeistPlayMenu%d, Dummy = %d' % (n, title, n, n))
        for k, slot in enumerate(ORDER):
            if slot in ent:
                print('     entry %d = slot F%02d: "%s" from Maps\\%s%s' % (k, slot, ent[slot][1], ent[slot][0], ', picture ' + ent[slot][2] if ent[slot][2] else ''))
    print('  windows %d -> %d, elements <GuiElement %d -> %d' % (xml.count('<Window '), res.count(b'<Window '), xml.count('<GuiElement'), res.count(b'<GuiElement')))


if __name__ == '__main__':
    main()
