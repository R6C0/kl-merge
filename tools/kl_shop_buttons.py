"""kl_shop_buttons.py - '[F2] More guns' and '[F3] Heisters' entries next to Buy Weapons on the round-over pages (re\\shop_buttons_1105.md).

    python tools/kl_shop_buttons.py check <zip>                 prints the entries found + element table before/after, writes nothing
    python tools/kl_shop_buttons.py bake  <zip> <out>           one map: a copy of the zip with Menu/online.xml baked (the zip is only read)
    python tools/kl_shop_buttons.py stage [--out DIR]           the 9 stock FA maps + every KLExpansion\\Maps\\* zip: baked online.xml per map
                                                                (the zips are 250 MB: not copied), report.txt, INSTALL / UNDO .bat (default
                                                                <work>\\build\\shop_buttons)
    python tools/kl_shop_buttons.py install [--maps ..] / undo  (run by the .bat only: the OWNER installs; never run by an agent)
    options: --more-key F2 --hire-key F3 (the text of the two entries; the hook's keys are rebindable, the baked text is not: GUESS the defaults)

What it changes in every status window of Menu/online.xml (HeistStatus, HeistStatusLeaderboard, their _EndGame twins, FAStatus*):
  1. PC_KEYBOARD legend: after the 'Buy Weapons' legend line (Template BuyWeaponsButton_PC, AlignH Right, TakeFocus False) two plain text
     legend entries (Type TextBlock, GenericButtonPos_GT, ColorSet Legend, AlignH Right), no input: F2 / F3 already work through the hook
     ([ShopPage] PageQueue / AutoOpen), the entries only tell the player.
  2. PC_GC (mouse) bottom frame, only where it has a Buy Weapons focus bar: two text-only groups (W151 H40) to the LEFT of the leftmost
     existing group (step 218 like the stock groups). No focus bar, no click: the mouse click is a documented follow-up (the drawn rectangle
     is not known from the XML: BottomFrameButtons is AlignH Left X -130 in a space the engine lays out).
No ButtonGraphic is created (no F-key glyph exists), so the cost is plain table slots: 2 per keyboard block, 4 per PC_GC block.
Idempotent (marker comment). A level whose table would pass the budget (tools\\kl_menu_count.py, 5000) is not baked.
Originals: install MOVES <zip> to <zip>.before-shopbuttons (never KL_PortBackup, an existing backup is never overwritten) and re-bakes from it.
"""
import argparse, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_count as mc                      # noqa: E402

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = os.path.join(DD, 'KLExpansion', 'Maps')
STOCK_MAPS = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']
BAK = '.before-shopbuttons'
MARK = 'KLExpansion shop buttons'
WIN_RE = re.compile(r'^([ \t]*)<Window Name="((?:HeistStatus|FAStatus)[A-Za-z_]*)"[^\n]*\n', re.M)
KB_RE = re.compile(r'^([ \t]*)<GuiElement Template="BuyWeaponsButton_PC" AlignH="Right"[^\n]*TakeFocus="False" />[ \t]*\r?\n', re.M)
GC_RE = re.compile(r'^([ \t]*)<GuiElement Type="GUIGroup" W="151" H="40" X="(\d+)"', re.M)
STEP_X = 218                                    # stock groups sit at X 873 / 655 / 437


def entry(indent, text, nl):
    return '%s<GuiElement Type="TextBlock" Template="GenericButtonPos_GT" ColorSet="Legend" AlignH="Right" Text="%%%s" TakeFocus="False" />%s' % (indent, text, nl)


def gc_group(indent, x, text, nl):
    i2 = indent + '\t'
    return (('%s<GuiElement Type="GUIGroup" W="151" H="40" X="%d" Y="0" ShowDebug="True">%s' % (indent, x, nl)) +
            ('%s<GuiElement Type="TextBlock" Template="GenericButtonPos_GT" ColorSet="Legend" Text="%%%s" AlignH="Center" AlignV="Center" X="0" />%s' % (i2, text, nl)) +
            ('%s</GuiElement>%s' % (indent, nl)))


def bake(xml, more='F2', hire='F3'):
    """bytes -> (bytes, report lines). Raises ValueError when no status window has a Buy Weapons legend line."""
    if MARK.encode() in xml:
        return xml, ['already baked']
    nl = '\r\n' if b'\r\n' in xml else '\n'
    t = xml.decode('latin-1')
    t_more, t_hire = '[%s] More guns' % more, '[%s] Heisters' % hire
    out, pos, rep, total, worst = [], 0, [], 0, 0
    for m in WIN_RE.finditer(t):
        e = t.find('</Window>', m.end())
        if e < 0 or m.start() < pos:
            continue
        body = t[m.end():e]
        nk = nb = 0
        # PC_GC first (positions), then keyboard; both by string splicing on the body
        gcs = []
        for p in re.finditer(r'<Platform PC_GC="True">(.*?)</Platform>', body, re.S):
            if 'BuyWeaponsButton_PC' not in p.group(1):
                continue
            g = list(GC_RE.finditer(p.group(1)))
            if g:
                gcs.append((p.start(1) + g[0].start(), g[0].group(1), min(int(x.group(2)) for x in g)))
        kbs = [(k.end(), k.group(1)) for k in KB_RE.finditer(body)]
        ins = []                                                    # (offset in body, text)
        for off, ind, minx in gcs:
            xs = [x for x in (minx - STEP_X, minx - 2 * STEP_X) if x >= 0]
            if xs:
                ins.append((off, gc_group(ind, xs[0], t_more, nl) + (gc_group(ind, xs[1], t_hire, nl) if len(xs) == 2 else '')))
                nb += 1
        for off, ind in kbs:
            ins.append((off, entry(ind, t_more, nl) + entry(ind, t_hire, nl)))
            nk += 1
        if not ins:
            continue
        ins.sort()
        b2, q = [], 0
        for off, txt in ins:
            b2.append(body[q:off]); b2.append(txt); q = off
        b2.append(body[q:])
        out.append(t[pos:m.end()]); out.append(''.join(b2)); pos = e
        rep.append('%-34s keyboard legends +%d, PC_GC frames +%d' % (m.group(2), nk, nb))
        worst += 2 * nk + 4 * nb
        total += nk + nb
    if not total:
        raise ValueError('no status window with a Buy Weapons legend line')
    out.append(t[pos:])
    s = ''.join(out)
    rep.append('worst case if the PC_GC (mouse) frames are counted too: +%d slots' % worst)
    i = WIN_RE.search(s).start()                                    # the marker comment (idempotence) goes before the first status window
    s = s[:i] + '  <!-- %s (tools/kl_shop_buttons.py) -->%s' % (MARK, nl) + s[i:]
    return s.encode('latin-1'), rep


def count(ingame, online):
    c = mc.Counter(mc.Context(arcade=True))
    if ingame is not None:
        c.count_file('ingame.xml', text=ingame)
    c.count_file('online.xml', text=online)
    return len(c.entries)


def read_members(zpath):
    with zipfile.ZipFile(zpath) as z:
        names = {n.lower(): n for n in z.namelist()}
        return names['menu/online.xml'], z.read(names['menu/online.xml']), (z.read(names['menu/ingame.xml']) if 'menu/ingame.xml' in names else None)


def rewrite(src, dst, member, newdata):
    tmp = dst + '.tmp'
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            if info.filename == member:
                zo.writestr(info, newdata, compress_type=info.compress_type)
            else:
                with zi.open(info) as f, zo.open(info, 'w') as g:
                    shutil.copyfileobj(f, g, 1 << 20)
    os.replace(tmp, dst)


def kl2_running():
    import subprocess
    try:
        return b'kl2.exe' in subprocess.run(['tasklist', '/fi', 'imagename eq kl2.exe'], capture_output=True).stdout.lower()
    except OSError:
        return False


def zip_in(d):
    for f in sorted(os.listdir(d)):
        if f.lower().endswith('_main.zip'):
            return os.path.join(d, f)
    return None


def targets(names):
    """name -> zip path. Default: the 9 stock maps + every KLExpansion map folder that has a *_Main.zip."""
    t = {}
    for n in STOCK_MAPS:
        z = zip_in(os.path.join(DD, 'Scenes', 'Locations', n)) if os.path.isdir(os.path.join(DD, 'Scenes', 'Locations', n)) else None
        if z:
            t[n] = z
    if os.path.isdir(MAPS):
        for n in sorted(os.listdir(MAPS)):
            z = zip_in(os.path.join(MAPS, n)) if os.path.isdir(os.path.join(MAPS, n)) else None
            if z:
                t[n] = z
    return {k: v for k, v in t.items() if not names or k in names}


def analyse(zp, more, hire):
    member, on, ig = read_members(zp)
    new, rep = bake(on, more, hire)
    b0, b1 = count(ig, on), count(ig, new)
    return member, on, new, rep, b0, b1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['check', 'bake', 'stage', 'install', 'undo'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--maps', nargs='+', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--more-key', default='F2')
    ap.add_argument('--hire-key', default='F3')
    a = ap.parse_args(argv)
    if a.mode in ('check', 'bake'):
        if not a.paths or (a.mode == 'bake' and len(a.paths) != 2):
            print('usage: check <zip> | bake <zip> <out>'); return 2
        member, on, new, rep, b0, b1 = analyse(a.paths[0], a.more_key, a.hire_key)
        for r in rep:
            print('  ' + r)
        print('online.xml %d -> %d bytes; element table %d -> %d of budget %d (+%d)%s' % (len(on), len(new), b0, b1, mc.BUDGET, b1 - b0, '' if b1 <= mc.BUDGET else '  OVER BUDGET'))
        if b1 > mc.BUDGET:
            return 1
        if a.mode == 'bake':
            if os.path.abspath(a.paths[1]) == os.path.abspath(a.paths[0]):
                print('refusing: <out> is the source zip'); return 2
            rewrite(a.paths[0], a.paths[1], member, new); print('wrote %s' % a.paths[1])
        return 0
    if a.mode in ('install', 'undo') and kl2_running():
        print('kl2.exe is running: close the game first (nothing changed)'); return 2
    tg = targets(a.maps)
    out = a.out
    if a.mode == 'stage' and not out:
        import kl_port_check
        out = os.path.join(kl_port_check.workdir(), 'build', 'shop_buttons')
    bad, lines = 0, []
    for name, zp in tg.items():
        if a.mode == 'undo':
            if os.path.exists(zp + BAK):
                os.replace(zp + BAK, zp); print('%-6s restored %s' % (name, zp))
            else:
                print('%-6s no backup %s' % (name, zp + BAK))
            continue
        src = zp                                                                          # bake() is idempotent (marker): always from the LIVE zip so edits by other bakers (hire) are kept
        try:
            member, on, new, rep, b0, b1 = analyse(src, a.more_key, a.hire_key)
        except (ValueError, KeyError, zipfile.BadZipFile) as e:
            print('%-6s FAIL %s' % (name, e)); bad += 1; lines.append('%s FAIL %s' % (name, e)); continue
        msg = '%-6s %s; element table %d -> %d of %d (+%d)%s' % (name, rep[-1], b0, b1, mc.BUDGET, b1 - b0, '' if b1 <= mc.BUDGET else '  OVER BUDGET')
        print(msg); lines.append(msg)
        if b1 > mc.BUDGET:
            bad += 1; continue
        if rep == ['already baked']:
            continue
        if a.mode == 'stage':
            os.makedirs(os.path.join(out, name), exist_ok=True)
            open(os.path.join(out, name, 'online.xml'), 'wb').write(new)
        elif a.mode == 'install':
            if not os.path.exists(zp + BAK):
                os.replace(zp, zp + BAK)                                                   # MOVE the original (never KL_PortBackup)
                rsrc = zp + BAK
            else:
                rsrc = zp
            try:
                rewrite(rsrc, zp, member, new)
            except Exception:
                if not os.path.exists(zp):
                    os.replace(zp + BAK, zp)
                raise
            print('       installed %s (original: %s)' % (zp, os.path.basename(zp + BAK)))
    if a.mode == 'stage':
        open(os.path.join(out, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
        write_bats(out, list(tg))
    return 1 if bad else 0


def write_bats(out, maps):
    for f in ('kl_shop_buttons.py', 'kl_menu_count.py'):
        shutil.copy2(os.path.join(HERE, f), os.path.join(out, f))
    ml = ' '.join(maps)
    for nm, mode, txt in (('INSTALL shop buttons.bat', 'install', 'Moves each live map zip to <zip>%s and writes the baked zip in its place (an existing backup is never overwritten).' % BAK),
                          ('UNDO shop buttons.bat', 'undo', 'Moves the *%s files back.' % BAK)):
        with open(os.path.join(out, nm), 'w', newline='\r\n') as f:
            f.write('@echo off\nrem %s\nrem Needs python on the PATH. Re-bakes from the live zips, so other map edits are kept.\n' % txt)
            f.write('tasklist /fi "imagename eq kl2.exe" 2>nul | find /i "kl2.exe" >nul && (echo Kane and Lynch 2 is running: close it first. Nothing changed. & pause & exit /b 1)\n')
            f.write('python "%%~dp0kl_shop_buttons.py" %s --maps %s\npause\n' % (mode, ml))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
