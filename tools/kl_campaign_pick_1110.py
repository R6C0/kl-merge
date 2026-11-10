#!/usr/bin/env python3
r"""kl_campaign_pick_1110.py - the menu half of [CampaignPick]: patch menu/frontend.xml of the KLExpansion overlay zips.

WHAT THE OWNER SEES (design in klhook/klcamppick_logic.h): Campaign menu (the one with Resume / Single player / Online) gets a fourth row
"Dead Men levels". It opens the window KLCampPick: a headline "Dead Men campaign" and 16 buttons in two columns of 8 ("M01 Impact" ...
"M14 Consequence"). A button opens the tiny window KLCampGo<NN>; klcamppick.c (the hook) sees that window and starts the level.

Applied to every overlay zip given (Patch01.zip, Patch01_deadmen.zip, Patch01_rows12.zip, Patch01_rows12_deadmen.zip): the same text edit on
the same anchors; a zip whose frontend.xml lacks an anchor, already has KLCampPick, or would pass the menu manager's table (5096 entries,
mkoverlay.table_tags + LIVE_OFFSET) is refused. All other zip members are copied byte for byte; the member keeps its date.

  python kl_campaign_pick_1110.py patch  <in.zip> <out.zip>      one zip
  python kl_campaign_pick_1110.py check  <zip>                   already patched? (exit 0 yes, 1 no)
  python kl_campaign_pick_1110.py test                           self-test on a synthetic frontend.xml (and the live zips when found)

GUESSES (nothing here has run in the game): a Window with only a BackgroundTemplate child is legal; Icon_Heist is a free entity in CampaignMenu;
Template CM_FocusBar works with an explicit X; FocusBar_short#01..#16 exist (re/menus.md: #01..#20 do) and the Line_Short_01#04 entity exists.
"""
import os, re, sys, zipfile, shutil, hashlib, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'klhook'))

MEMBER = 'menu/frontend.xml'
IDS = ['M01', 'M02', 'M03', 'M03B', 'M05', 'M06', 'M07', 'M08', 'M09', 'M09B', 'M11', 'M11B', 'M12', 'M13', 'M13B', 'M14']
NAMES = ['Impact', 'Trial', 'Withdrawal', 'Cracking Up', 'The Mizuki', 'Exchange', 'Reunion', 'Breakout', 'Retomoto Tower',
         'Tokyo Streets', 'Freedom Fighters', 'El Capitol', "Bird's Eye View", 'Within The Walls', 'Choice', 'Consequence']
TITLE = 'Dead Men campaign'
BUTTON = 'Dead Men levels'
LIMIT = 5096
LIVE_OFFSET = 715                       # mkoverlay.LIVE_OFFSET: live table size minus table_tags of the installed overlay
MARGIN = 20                             # entries kept free after our additions


def table_tags(xml):
    plain = re.sub(r'<!--.*?-->', '', xml, flags=re.S)
    return len(re.findall(r'<(?:Window|GuiElement|ColorSet|ButtonGraphic)[\s/>]', plain))


def one(pattern, text, what, flags=0):
    m = list(re.finditer(pattern, text, flags))
    if len(m) != 1:
        raise SystemExit('frontend.xml is not the one this script knows: %d matches for %s' % (len(m), what))
    return m[0]


def go_windows(nl):
    out = ''
    for i in range(len(IDS)):
        out += ('  <Window Name="KLCampGo%02d" Template="WindowDefault">' % (i + 1) + nl +
                '    <GuiElement Template="BackgroundTemplate"/>' + nl + '  </Window>' + nl)
    return out


def list_window(nl):
    for t in NAMES + [TITLE, BUTTON]:
        if any(c in t for c in '&"<>') or any(ord(c) < 32 or ord(c) > 126 for c in t):
            raise SystemExit('text %r: plain ASCII without & " < > only' % t)
    L = ['  <Window Name="KLCampPick" LocaleBasePath="AllLevels/Menu/Campaign" Template="WindowDefault">',
         '    <GuiElement Template="BackgroundTemplate"/>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize">',
         '      <GuiElement Template="HeadlineIcon" Graphic="Icon_Campaign"/>',
         '      <GuiElement Template="HeadlineText" Text="%%%s"/>' % TITLE,
         '      <GuiElement Template="LongLineTop" />',
         '      <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="130" Y="144">']
    for i, (mid, nm) in enumerate(zip(IDS, NAMES)):
        col, row = divmod(i, 8)
        x = 170 + 380 * col
        y = 40 + 34 * row
        L.append('        <GuiElement Type="OpenWindow" Window="KLCampGo%02d" Text="%%%s %s" X="%d" Y="%d" FadeInTime="0.2" FadeInDelay="0.%02d" AlignH="Left"' % (i + 1, mid, nm, x, y + 9, 5 + 2 * row))
        L.append('            FocusGraphic="KLcpf#%02d" />' % (i + 1))
    for i in range(len(IDS)):
        col, row = divmod(i, 8)
        L.append('        <GuiElement Name="KLcpf#%02d" Y="%d" Graphic="FocusBar_short#%02d" Template="CM_FocusBar" X="%d" MouseFocusW="239" />' % (i + 1, 40 + 34 * row, i + 1, 160 + 380 * col))
    L += ['      </GuiElement>',
          '      <GuiElement Type="GUIGroup" Template="BottomFramePosSize" ShowDebug="True">',
          '        <Platform PC_GC="True">',
          '          <GuiElement Template="BottomFrameMenuBackButton"/>',
          '        </Platform>',
          '        <Platform PC_KEYBOARD="True">',
          '          <GuiElement Template="ButtonBack_INV_GT" />',
          '          <GuiElement Template="BackButtonNoXPos_PC" AlignH="Right" X="0" HelpTextBlock="HelpOnlineMain" HelpText=" " />',
          '        </Platform>',
          '      </GuiElement>',
          '    </GuiElement>',
          '  </Window>']
    return nl.join(L) + nl


def row_block(nl):
    return ('      <Platform PC="True">' + nl +
           '        <GuiElement Type="OpenWindow" Template="CM_Button" Window="KLCampPick" Text="%' + BUTTON + '"' + nl +
           '                    FocusGraphic="CMfbl#04" FadeInDelay="0.25" Y="288" />' + nl +
           '        <GuiElement Type="Graphic" Graphic="Icon_Heist" Y="279" X="250" AlphaMax="255" AlphaMin="10" FadeInTime="0.3" FadeInDelay="0.02"/>' + nl +
           '        <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#04" AnimY="312" />' + nl +
           '        <GuiElement Name="CMfbl#04" Y="279" Graphic="FocusBar_short#04" Template="CM_FocusBar" MouseFocusW="239" />' + nl +
           '      </Platform>' + nl)


def ins_block(nl):
    return nl + '  <!-- KLCampaignPick (kl_campaign_pick_1110.py): the list of the 16 Dead Men campaign levels, one wait window per level -->' + nl + list_window(nl) + go_windows(nl)


def patch_xml(xml):
    """-> new frontend.xml text. Refuses a file that already has the window, lacks an anchor, or would overfill the table."""
    if 'KLCampPick' in xml:
        raise SystemExit('frontend.xml already has KLCampPick')
    nl = '\r\n' if '\r\n' in xml else '\n'
    before = table_tags(xml)
    cm = one(r'[ \t]*<Window Name="CampaignMenu" [^>]*>.*?</Window>[ \t]*\r?\n', xml, 'the window CampaignMenu', re.S)
    w = cm.group(0)
    # 1. the row: after the PC block that holds the Online button (its last element), before the PC focus bars' end
    pcb = one(r'(<Platform PC="True">\s*<!--GuiElement Type="SendMessage" Template="CM_Button" Text="Button_SplitScreen".*?</Platform>)', w, 'the PC button block', re.S)
    row = row_block(nl)
    w2 = w[:pcb.end()] + nl + row + w[pcb.end():]
    xml2 = xml[:cm.start()] + w2 + xml[cm.end():]
    # 2. the new windows go behind CampaignMenu
    end = xml2.index('</Window>', xml2.index('<Window Name="CampaignMenu" ')) + len('</Window>')
    ins = ins_block(nl)
    xml2 = xml2[:end] + ins + xml2[end:]
    added = table_tags(xml2) - before
    free = LIMIT - (before + LIVE_OFFSET)
    if added > free - MARGIN:
        raise SystemExit('the menu manager table: %d entries added, %d free (margin %d): refused' % (added, free, MARGIN))
    return xml2


def patch_zip(src, dst):
    with zipfile.ZipFile(src) as zi:
        infos = zi.infolist()
        data = {i.filename: zi.read(i.filename) for i in infos if not i.is_dir()}
        if MEMBER not in data:
            raise SystemExit('%s: no %s' % (src, MEMBER))
        raw = data[MEMBER]
        new = patch_xml(raw.decode('utf-8')).encode('utf-8')
        tmp = dst + '.part'
        with zipfile.ZipFile(tmp, 'w') as zo:
            for i in infos:
                ni = zipfile.ZipInfo(i.filename, i.date_time)
                ni.compress_type = i.compress_type
                ni.external_attr = i.external_attr
                ni.create_system = i.create_system
                zo.writestr(ni, b'' if i.is_dir() else (new if i.filename == MEMBER else data[i.filename]))
        os.replace(tmp, dst)
    return table_tags(new.decode('utf-8')) - table_tags(raw.decode('utf-8'))


def is_patched(path):
    with zipfile.ZipFile(path) as z:
        return b'KLCampPick' in z.read(MEMBER)


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def selftest():
    import xml.etree.ElementTree as ET
    ok = fail = 0

    def check(what, cond):
        nonlocal ok, fail
        if cond: ok += 1
        else: fail += 1; print('FAIL', what)
    live = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Overlay'
    zips = [os.path.join(live, n) for n in ('Patch01.zip', 'Patch01_deadmen.zip', 'Patch01_rows12.zip', 'Patch01_rows12_deadmen.zip')]
    zips = [z for z in zips if os.path.isfile(z)]
    check('xml helpers', table_tags('<Window Name="a"><GuiElement/><!-- <GuiElement/> --></Window>') == 2)
    syn = ('<Root>\n<Window Name="CampaignMenu" X="1">\n<Platform PC="True">\n<!--GuiElement Type="SendMessage" Template="CM_Button" Text="Button_SplitScreen"\n/-->\n'
           '<GuiElement Name="CMfbl#03"/>\n</Platform>\n</Window>\n</Root>\n')
    out = patch_xml(syn)
    try:
        ET.fromstring(out); check('synthetic result is well-formed XML', True)
    except Exception as e:
        check('synthetic result is well-formed XML: %s' % e, False)
    check('synthetic: +79 table entries', table_tags(out) - table_tags(syn) == 79 or print(table_tags(out) - table_tags(syn)))
    check('one KLCampPick window, 16 go windows', out.count('<Window Name="KLCampPick"') == 1 and len(re.findall(r'<Window Name="KLCampGo\d\d"', out)) == 16)
    check('every button opens a go window that exists', all(('Window="KLCampGo%02d"' % i) in out and ('<Window Name="KLCampGo%02d"' % i) in out for i in range(1, 17)))
    check('focus bars unique', len(set(re.findall(r'Name="(KLcpf#\d\d)"', out))) == 16)
    check('button text carries id and name', '%M09B Tokyo Streets' in out and '%M14 Consequence' in out)
    check('CR LF kept', patch_xml(syn.replace('\n', '\r\n')).count('\r\n') >= out.count('\n') and '\n' not in patch_xml(syn.replace('\n', '\r\n')).replace('\r\n', ''))
    for bad in (out, syn.replace('CampaignMenu', 'Other')):
        try: patch_xml(bad); check('refuses', False)
        except SystemExit: check('refuses a patched or anchorless file', True)
    d = tempfile.mkdtemp(prefix='kcp_')
    try:
        for z in zips:
            o = os.path.join(d, os.path.basename(z))
            added = patch_zip(z, o)
            with zipfile.ZipFile(z) as a, zipfile.ZipFile(o) as b:
                same = all(a.read(n) == b.read(n) for n in a.namelist() if n != MEMBER) and a.namelist() == b.namelist()
                check('%s: other members identical, order kept' % os.path.basename(z), same)
                x = b.read(MEMBER).decode('utf-8')
                try: ET.fromstring('<R>' + ins_block(chr(10)) + '</R>'); wf = True
                except Exception as e: wf = False; print(e)
                check('%s: our windows well-formed; the stock file is not strict XML itself (+%d table entries)' % (os.path.basename(z), added), wf and is_patched(o) and not is_patched(z))
                check('%s: stays inside the table' % os.path.basename(z), table_tags(x) + LIVE_OFFSET <= LIMIT - MARGIN + 20)
                # the stock text is a prefix/suffix of the new one around the two insertions
                orig = a.read(MEMBER).decode('utf-8')
                check('%s: removing our blocks gives the original' % os.path.basename(z), strip_ours(x) == orig)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print('RESULT: %s (%d checks, %d failed)%s' % ('FAIL' if fail else 'PASS', ok + fail, fail, '' if zips else ' (live zips not found: synthetic only)'))
    return 1 if fail else 0


def strip_ours(x):
    """Inverse of patch_xml (for the self-test): drop the inserted blocks."""
    nl = chr(13) + chr(10) if chr(13) in x else chr(10)
    for blk in (nl + row_block(nl), ins_block(nl)):
        if x.count(blk) != 1:
            return None
        x = x.replace(blk, '', 1)
    return x


def main(argv):
    if len(argv) >= 2 and argv[1] == 'test':
        return selftest()
    if len(argv) == 4 and argv[1] == 'patch':
        n = patch_zip(argv[2], argv[3]); print('patched %s -> %s (+%d table entries) md5 %s' % (argv[2], argv[3], n, md5(argv[3]))); return 0
    if len(argv) == 3 and argv[1] == 'check':
        return 0 if is_patched(argv[2]) else 1
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
