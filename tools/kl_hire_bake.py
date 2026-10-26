"""kl_hire_bake.py - bake the HIRE window (re\\shop_hire.md option B, stage 1) into the level's Menu\\online.xml.

    python tools/kl_hire_bake.py stage   [--maps DM01 DM02 ..] [--out DIR]    staged copies of the zips + report (default)
    python tools/kl_hire_bake.py check   [--maps ..]                          only the element-table headroom, writes nothing
    python tools/kl_hire_bake.py install [--maps ..]                          re-bakes each LIVE zip, backup <zip>.before-1026hire
    python tools/kl_hire_bake.py undo    [--maps ..]                          puts the .before-1026hire files back

What it changes in Menu/online.xml of a map zip (KLExpansion\\Maps\\<name>\\F0x_Main.zip, the Dead Men maps by default):
  1. a <ColorSet Name="KLHireCS"> (white, red with focus: the stock focus colours are black, made for text on a focus bar),
  2. a <Window Name="FAHire"> after the Buy Weapons window: headline, FATotal (the money), 16 ToggleText rows bound to the options
     KLHire1..KLHire16 that klhook\\klhire.c answers, one data text per row (the HIRED mark), a Back button,
  3. a visible button "Hire a heister" (OpenWindow FAHire) in FABuyWeaponsNew, after the Secondary weapon button, in the same
     vertical group, so Up / Down / Select (keyboard) and the pad's stick / A reach it.
Idempotent (a level that has FAHire is left as it is). Texts are literal ('%' prefix): the price and rank on a row are
BAKED from klhire.c's default table (or the [Hire] Price<n> / Rank<n> of --ini); the hook enforces ITS table.
The element table (5096, budget 5000; tools\\kl_menu_count.py) is checked before and after with the level's Menu/ingame.xml +
online.xml, Arcade context; a map that would pass 5000 is not baked.
install / undo write into the game folder: run them from the INSTALL / UNDO .bat the stage step writes next to the staged
zips (they are for the OWNER; this tool is never run by the agent against the live folder).
"""
import argparse, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_count as mc                      # noqa: E402

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = os.path.join(DD, 'KLExpansion', 'Maps')
DM_DEFAULT = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B']
BAK = '.before-1026hire'
MEMBER = 'Menu/online.xml'

NAMES = ['J.C.', 'Tommy', 'Pierre', 'Liam', 'Jean', 'Elwood', 'Bud', 'Mitchel', 'Kane', 'Lynch', 'Ashkanan', 'Meldal', 'Red', 'Parker', 'Standen', 'Hutchison']
PRICE = [45000] * 4 + [90000] * 4 + [450000, 540000] + [180000, 180000, 225000, 225000, 270000, 270000]      # = klhire.c klhr_defp
RANK = [0, 0, 1, 1, 2, 2, 3, 3, 6, 7, 4, 4, 4, 5, 5, 5]                                                      # = klhr_defr
FIRST_Y, STEP_Y = 70, 24


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')


def read_ini(path):
    """[Hire] Price<n> / Rank<n> of a KLHook.ini, into copies of the tables."""
    price, rank = list(PRICE), list(RANK)
    if not path:
        return price, rank
    sec = ''
    for ln in open(path, encoding='latin-1'):
        ln = ln.strip()
        if ln.startswith('['):
            sec = ln.lower()
        elif sec == '[hire]' and '=' in ln and not ln.startswith(';'):
            k, _, v = ln.partition('=')
            m = re.fullmatch(r'(Price|Rank)(\d+)', k.strip(), re.I)
            if m and 1 <= int(m.group(2)) <= 16 and v.strip().lstrip('-').isdigit():
                (price if m.group(1).lower() == 'price' else rank)[int(m.group(2)) - 1] = int(v.strip())
    return price, rank


def window_xml(nl, price, rank):
    L = ['  <!-- KLExpansion: the Hire window (tools/kl_hire_bake.py; options KLHire1..16 by klhook/klhire.c) -->',
         '  <Window Name="FAHire" LocaleBasePath="AllLevels/Menu/Online/WeaponShop" Template="IngameWindowDefault">',
         '    <GuiElement Template="BackgroundTemplateNoFade"/>',
         '    <GuiElement Type="GUIGroup" Template="ScreenBaseSize" Navigation="Vertical">',
         '      <GuiElement Template="LongLineTop" />',
         '      <GuiElement Template="LongLineBottom" />',
         '      <GuiElement Type="TextBlock" Template="HeadlinePos" Text="%Hire a heister for the next round" TextWidth="900" />',
         '      <GuiElement Template="FATotal"/>']
    for i in range(16):
        y = FIRST_Y + STEP_Y * i
        L += ['      <GuiElement Type="TextBlock" Text="" Name="KLHr_Data%d" AlignH="Center" X="190" Y="%d" Font="Text" />' % (i + 1, y)]
    for i in range(16):
        y = FIRST_Y + STEP_Y * i
        label = '%s   $%s   rank %d' % (NAMES[i], format(price[i], ','), rank[i])
        L += ['      <GuiElement Type="ToggleText" Text="%%%s" Name="KLHr_Row%d" Option="KLHire%d" AlignH="Center" X="-190" Y="%d" Font="Text" ColorSet="KLHireCS"' % (esc(label), i + 1, i + 1, y),
              '          TextReceiver="KLHr_Data%d" UseTextReceiverAsFocus="True" RecCSFocus="Header" RecCSDefault="Default" Link="True">' % (i + 1),
              '        <Text Text="%-" />',
              '        <Text Text="%HIRED for the next round" />',
              '      </GuiElement>']
    L += ['      <GuiElement Type="GUIGroup" Template="BottomFramePosSize" ShowDebug="True" ReverseNavigation="True" Navigation="Horizontal">',
          '        <Platform PC_KEYBOARD="True">',
          '          <GuiElement Template="ButtonBack_INV_GT" />',
          '          <GuiElement Template="BackButtonNoXPos_PC" AlignH="Right" TakeFocus="False" X="0" />',
          '        </Platform>',
          '        <Platform PC_GC="True">',
          '          <GuiElement Template="ButtonBack_INV_GT" />',
          '        </Platform>',
          '      </GuiElement>',
          '    </GuiElement>',
          '  </Window>']
    return nl.join(L) + nl


def bake(xml, price, rank):
    """bytes -> bytes (or raises ValueError with the reason)."""
    if b'Name="FAHire"' in xml:
        return xml
    nl = '\r\n' if b'\r\n' in xml else '\n'
    t = xml.decode('latin-1')
    m = re.search(r'^[ \t]*<Window Name="FABuyWeaponsNew"', t, re.M)
    if not m:
        raise ValueError('no <Window Name="FABuyWeaponsNew">')
    e = t.index('</Window>', m.start())
    e = t.index('\n', e) + 1
    sec = re.search(r'^([ \t]*)<GuiElement[^\n]*PlayerIndex="-5"[^\n]*Text="Secondary"[^\n]*/>[ \t]*\r?\n', t[m.start():e], re.M)
    if not sec:
        raise ValueError('the Secondary weapon button line of FABuyWeaponsNew was not found')
    btn = ('      <GuiElement Type="OpenWindow" Window="FAHire" Text="%Hire a heister" Font="Text" AlignH="Center" X="-380" Y="335" ColorSet="KLHireCS" '
           'HelpText=" " />' + nl)
    cs = '  <ColorSet Name="KLHireCS" NormalColor="0xFFffffff" FocusColor="0xffd7373a" DisableColor="0xff888888" />' + nl
    s_end = m.start() + sec.end()
    out = t[:m.start()] + cs + t[m.start():s_end] + btn + t[s_end:e] + nl + window_xml(nl, price, rank) + t[e:]
    return out.encode('latin-1')


def count(ingame, online):
    c = mc.Counter(mc.Context(arcade=True))
    if ingame is not None:
        c.count_file('ingame.xml', text=ingame)
    c.count_file('online.xml', text=online)
    return len(c.entries)


def read_members(zpath):
    with zipfile.ZipFile(zpath) as z:
        names = {n.lower(): n for n in z.namelist()}
        on = z.read(names['menu/online.xml'])
        ig = z.read(names['menu/ingame.xml']) if 'menu/ingame.xml' in names else None
        return names['menu/online.xml'], on, ig


def rewrite(src, dst, member, newdata):
    """a copy of the zip with one member replaced (the others re-written as they were: same names, dates, compression)."""
    tmp = dst + '.tmp'
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp, 'w', allowZip64=True) as zo:
        for zi_info in zi.infolist():
            if zi_info.filename == member:
                zo.writestr(zi_info, newdata, compress_type=zi_info.compress_type)
            else:
                with zi.open(zi_info) as f, zo.open(zi_info, 'w') as g:
                    shutil.copyfileobj(f, g, 1 << 20)
    os.replace(tmp, dst)


def zpath_of(name):
    d = os.path.join(MAPS, name)
    for f in sorted(os.listdir(d)):
        if f.lower().endswith('_main.zip'):
            return os.path.join(d, f)
    raise FileNotFoundError(d)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', nargs='?', default='stage', choices=['stage', 'check', 'install', 'undo'])
    ap.add_argument('--maps', nargs='+', default=DM_DEFAULT)
    ap.add_argument('--out', default=None)
    ap.add_argument('--ini', default=os.path.join(HERE, '..', 'klhook', 'KLHook.ini'), help='KLHook.ini whose [Hire] Price/Rank the rows show')
    a = ap.parse_args(argv)
    price, rank = read_ini(a.ini if os.path.exists(a.ini) else None)
    out = a.out
    if a.mode == 'stage' and not out:
        import kl_port_check
        out = os.path.join(kl_port_check.workdir(), 'build', 'hire_1026')
    bad = 0
    for name in a.maps:
        try:
            zp = zpath_of(name)
        except (OSError, FileNotFoundError) as e:
            print('%-6s SKIP %s' % (name, e)); continue
        if a.mode == 'undo':
            if os.path.exists(zp + BAK):
                os.replace(zp + BAK, zp); print('%-6s restored %s' % (name, zp))
            else:
                print('%-6s no backup %s' % (name, zp + BAK))
            continue
        member, on, ig = read_members(zp)
        if b'Name="FAHire"' in on:
            print('%-6s already baked' % name); continue
        try:
            new = bake(on, price, rank)
        except ValueError as e:
            print('%-6s FAIL %s' % (name, e)); bad += 1; continue
        b0, b1 = count(ig, on), count(ig, new)
        print('%-6s online.xml %d -> %d bytes; element table %d -> %d of budget %d (+%d)%s' % (name, len(on), len(new), b0, b1, mc.BUDGET, b1 - b0, '' if b1 <= mc.BUDGET else '  OVER BUDGET'))
        if b1 > mc.BUDGET:
            bad += 1; continue
        if a.mode == 'check':
            continue
        if a.mode == 'stage':
            os.makedirs(os.path.join(out, name), exist_ok=True)
            dst = os.path.join(out, name, os.path.basename(zp))
            rewrite(zp, dst, member, new); print('       staged %s' % dst)
        else:                                          # install: re-bake from the LIVE zip (other work edits these zips concurrently)
            if not os.path.exists(zp + BAK):
                shutil.copy2(zp, zp + BAK)
            tmpz = zp + '.hire.tmp'
            rewrite(zp, tmpz, member, new); os.replace(tmpz, zp); print('       installed %s (backup %s)' % (zp, os.path.basename(zp + BAK)))
    if a.mode == 'stage' and out:
        write_bats(out, a.maps)
    return 1 if bad else 0


def write_bats(out, maps):
    for f in ('kl_hire_bake.py', 'kl_menu_count.py'):              # the bats run their own copies, so they outlive this checkout
        shutil.copy2(os.path.join(HERE, f), os.path.join(out, f))
    ml = ' '.join(maps)
    for nm, mode, txt in (('INSTALL hire window.bat', 'install', 'Bakes the Hire window into the LIVE Dead Men map zips (backups *%s next to each zip).' % BAK),
                          ('UNDO hire window.bat', 'undo', 'Puts the *%s backups back.' % BAK)):
        with open(os.path.join(out, nm), 'w', newline='\r\n') as f:
            f.write('@echo off\nrem %s\nrem Close Kane & Lynch 2 first. Needs python on the PATH. Re-bakes from the live zips, so other map edits are kept.\n' % txt)
            f.write('python "%s" %s --maps %s\npause\n' % (py, mode, ml))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
