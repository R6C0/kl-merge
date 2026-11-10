#!/usr/bin/env python3
"""kl_campui_menu.py - luvsic's Dead Men campaign menu pages, delivered as ONE extra row in Dog Days' CampaignMenu.

    py -I tools/kl_campui_menu.py --base <Patch01.zip> [--base <Patch01_deadmen.zip> ...] [--out-dir DIR]
                                  [--dd DIR] [--dm DIR] [--enable-all] [--check-only]

WHY not luvsic's own delivery (third_party/anp/tools/anp_menu.py -> ANP_Patch01.zip): that one rewrites Dog Days' MAIN menu
(8 rows: Dead Men / Dog Days / Dead Dogs / Arcade ...) and is served in place of Patch01.zip for EVERYTHING. The owner's ask
is "his UI only in his campaign": so this tool keeps every stock window as it is and changes exactly two things in
menu/frontend.xml of a COPY of the base archive:
  1. CampaignMenu (Main menu -> Play, the page that already holds Resume / Single player / Online) gets a fourth PC row
     "Dead Men Campaign" (+ its focus bar and separator line) that opens the page ANP_DeadMen.
  2. Two pages are appended just before </Windows> (no stock window moves, so the boot window is unchanged):
       ANP_DeadMen          New game (LoadScene M01) / Chapters / Difficulty (Dead Men's own names Aspirin..)
       ANP_DeadMenChapters  16 LoadScene buttons (titles from Dead Men's own LOC, <Locale> blocks for all nine languages)
     built by luvsic's own helpers (hub, chapters_page, dm_diff_row, CM_TEMPLATES) so the look is his.
NOT ported: Continue (pseudo scene id DMCN), the Dead Dogs page (DGNW/DGCN) and the intro movie pages - they need the loader
(campaign.inc) which klcampaign.c does not implement; New game / chapters rely on [Campaign] Routing=1 (scene id M01.. ->
converted level, klcampaign.c).
Output name: <base stem>_campui.zip beside --out-dir (default: next to the base), every other member byte for byte.
klhook (klcampui.c / klslot.c) opens that sibling INSTEAD of the base only when [CampaignUI] Menu=1 and [Campaign] Enable=1.
Checks (the build fails on any): added XML well-formed; Graphic / FocusGraphic / TextReceiver / HelpTextBlock / Template / Window
targets exist; templates defined before use; every Locale group covers the nine kl2 languages once; the output equals the
input outside the CampaignMenu row and the appended block; window names new; ASCII only.
"""
import argparse, json, os, re, sys, xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ANP_TOOLS = os.path.join(os.path.dirname(HERE), 'third_party', 'anp', 'tools')
sys.path.insert(0, ANP_TOOLS)
sys.dont_write_bytecode = True
import anp_menu as M                                                    # luvsic's builder (vendored, unchanged)
from zipraw import read_zip, read_entry, entry_from_bytes, write_zip

NL = M.NL
WINDOWS = ('ANP_DeadMen', 'ANP_DeadMenChapters')
ROW_ANCHOR = '<GuiElement Name="CMfbl#01" Y="177"'                       # the stock focus bars start here (all platforms)
ONLINE_PC_END = 'Option="MP_MultiPlayerMenu" OptionValue="1" DisableInDemo="True" DisableInPreviewBuild="True"/>'
ROW_Y = 288                                                             # 4th row, 34 px below the Online row (Y254)
FB_NAME = 'ANP_CMfbl#04'

def new_row():
    # GUESS: Template CM_Button is the PC row template (stock rows use it); ANP_CM_Button (X300) is luvsic's copy for pages
    # defined before CM_Button. In CampaignMenu itself CM_Button is already defined, so the stock template is used.
    return ('<Platform PC="True">' + NL +
            '        <GuiElement Type="OpenWindow" Template="CM_Button" Name="ANP_DM_Row" Window="ANP_DeadMen" Text="%%Dead Men Campaign"'
            ' FocusGraphic="%s" FadeInDelay="0.25" Y="%d" HelpText="%%Play the Dead Men campaign (levels converted into Dog Days)"'
            ' Option="MercsGameMode" OptionValue="0" DisableInDemo="True" />' % (FB_NAME, ROW_Y) + NL +
            '        <GuiElement AnimX="811" Template="Line" Graphic="Line_Short_01#04" AnimY="312" />' + NL +
            '      </Platform>' + NL + '      ')

def new_bar():
    return ('<Platform PC="True"><GuiElement Name="%s" Y="%d" Graphic="FocusBar_short#04" Template="CM_FocusBar" MouseFocusW="239" /></Platform>'
            % (FB_NAME, ROW_Y - 9) + NL + '      ')

def pages(titles, enabled, diff):
    rows = [
        '<GuiElement Type="LoadScene" Name="ANP_DM_New" Scene="M01" Text="%New game" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.10" HelpText="%Start Dead Men from chapter 1" HelpTextBlock="@H"/>',
        '<GuiElement Type="OpenWindow" Name="ANP_DM_Chapters" Window="ANP_DeadMenChapters" Text="%Chapters" Template="ANP_CM_Button" Y="@Y" FocusGraphic="@FB" FadeInDelay="0.15" Option="MercsGameMode" OptionValue="0" HelpTextBlock="@H" HelpText="%Pick any Dead Men chapter"/>',
        (M.dm_diff_row(diff) if diff else M.DIFF_ROW).replace('@N', 'ANP_DM'),
    ]
    blk = '\n'.join([
        '<!-- ===== Dead Men campaign pages (tools/kl_campui_menu.py, luvsic\'s anp_menu helpers) ===== -->',
        M.CM_TEMPLATES,
        M.hub('ANP_DeadMen', 'Dead Men', 'Icon_Campaign', rows),
        M.chapters_page(titles, enabled),
        '<!-- ===== end of Dead Men campaign pages ===== -->', '']).replace('\r\n', '\n').replace('\n', NL)
    return blk

def build(src, titles, enabled, diff=None):
    for w in WINDOWS:
        if 'Name="%s"' % w in src: raise SystemExit('base frontend.xml already has %s' % w)
    wi = src.index('<Window Name="CampaignMenu"')
    we = src.index('</Window>', wi)
    online = src.index(ONLINE_PC_END, wi)
    if online > we: raise SystemExit('CampaignMenu PC Online row not found where expected')
    p_end = src.index('</Platform>', online)
    # row: right after the PC platform block that holds the Online row
    p_end += len('</Platform>')
    row = NL + '      ' + new_row().rstrip(' ')
    bar_at = src.index('<GuiElement Name="CMfbl#03"', wi)
    bar_at = src.index(NL, bar_at) + len(NL)
    bar = '      ' + new_bar().rstrip(' ')
    out = src[:p_end] + row + src[p_end:bar_at] + bar + src[bar_at:]
    blk = pages(titles, enabled, diff)
    at = out.rindex('</Windows>'); at = out.rfind('\n', 0, at) + 1
    out = out[:at] + blk + out[at:]
    return out, (row, bar, blk)

def check(src, out, parts, scene_blob):
    errs, notes = [], []
    row, bar, blk = parts
    for nm, frag in (('CampaignMenu row', row), ('focus bar', bar), ('pages', blk)):
        try: xml.dom.minidom.parseString('<r>' + frag + '</r>')
        except Exception as e: errs.append('%s not well-formed: %s' % (nm, e))
    b = out.replace(blk, '', 1).replace(row, '', 1).replace(bar, '', 1)
    if b != src: errs.append('output differs from the input outside the added row, bar and pages')
    added = row + bar + blk
    nocomment = re.sub(r'<!--.*?-->', '', out, flags=re.S)
    names = set(re.findall(r'\bName="([^"]+)"', nocomment))
    templates = set(re.findall(r'<Template Name="([^"]+)"', nocomment))
    wins = M.windows_of(out)
    for g in sorted(set(re.findall(r'(?<![A-Za-z])Graphic="([^"]+)"', added))):
        if g.encode('latin1') + b'\0' not in scene_blob and g not in names:
            errs.append('Graphic "%s" is neither in the frontend scene nor an element name' % g)
    for w in WINDOWS + ('CampaignMenu',):
        if w not in wins: errs.append('window %s missing' % w); continue
        wt = wins[w]; wnames = set(re.findall(r'\bName="([^"]+)"', wt))
        for attr in ('FocusGraphic', 'TextReceiver', 'HelpTextBlock', 'Receiver'):
            for v in set(re.findall(r'\b%s="([^"]+)"' % attr, wt if w in WINDOWS else row + bar)):
                if v not in wnames and v not in templates and v not in names: errs.append('%s: %s="%s" names no element' % (w, attr, v))
    for t in sorted(set(re.findall(r'\bTemplate="([^"]+)"', added))):
        if t not in templates: errs.append('Template "%s" not defined' % t); continue
        d = out.find('<Template Name="%s"' % t)
        uses = [out.find(f) + f.find('Template="%s"' % t) for f in (row, bar, blk) if 'Template="%s"' % t in f and f in out]
        if uses and d > min(uses): errs.append('Template "%s" is used before it is defined' % t)
    for t in sorted(set(re.findall(r'\bWindow="([^"]+)"', added))):
        if t not in wins: errs.append('Window "%s" not defined' % t)
    groups = {}
    for m in re.finditer(r'<Locale ([^>]*)>(.*?)</Locale>', blk, re.S):
        for nm in re.findall(r'\bName="([^"]+)"', m.group(2)):
            groups.setdefault(nm, []).extend(re.findall(r'(\w+)="True"', m.group(1)))
    for nm, langs in groups.items():
        if sorted(langs) != sorted(M.KL2_LANGS): errs.append('Locale group of %s covers %s' % (nm, ','.join(langs)))
    for w in WINDOWS:
        if out.count('<Window Name="%s"' % w) != 1: errs.append('window %s defined %d times' % (w, out.count('<Window Name="%s"' % w)))
    if any(ord(c) > 126 for c in added): errs.append('non-ASCII text in the added XML')
    if 'Scene="DMCN"' in added or 'Scene="DGNW"' in added or 'Scene="DGCN"' in added: errs.append('pseudo scene id (needs the ANP loader) in the added XML')
    if 'MoviePlayer' in added: errs.append('MoviePlayer in the added XML (intro not ported)')
    notes.append('Locale groups: %d elements x %d languages' % (len(groups), len(M.KL2_LANGS)))
    return errs, notes

def variant_name(path):
    d, f = os.path.split(path); s, e = os.path.splitext(f)
    return s + '_campui' + e

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', action='append', required=True, help='menu archive to start from (repeat for Patch01.zip, Patch01_deadmen.zip ...)')
    ap.add_argument('--out-dir'); ap.add_argument('--dd'); ap.add_argument('--dm')
    ap.add_argument('--enable-all', action='store_true'); ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--dm-difficulty', choices=('on', 'off'), default='on')
    a = ap.parse_args()
    P = M.anp_paths
    dd = a.dd or P.game_dir('ANP_DD_GAME', P.DD_FOLDER)
    dm = a.dm or P.game_dir('ANP_DM_GAME', P.DM_FOLDER)
    installed = {sid for sid, _ in M.CHAPTERS if os.path.exists(os.path.join(dd, 'Scenes', 'Locations', sid, '%s_Main.zip' % sid))}
    enabled = {sid for sid, _ in M.CHAPTERS} if a.enable_all else installed
    titles = M.dm_titles(dm)
    diff = M.dm_difficulty(dm) if a.dm_difficulty == 'on' else None
    blob = M.scene_names_blob(dd)
    reps = []
    for base in a.base:
        ents = read_zip(base)
        fe = [e for e in ents if e.name.lower() == 'menu/frontend.xml']
        if len(fe) != 1: raise SystemExit('%s has no menu/frontend.xml' % base)
        src0 = read_entry(fe[0]).decode('latin1')
        src, dropped = M.strip_test_lines(src0)
        if dropped: raise SystemExit('%s carries ANP test lines (is it an ANP archive?)' % base)
        out, parts = build(src, titles, enabled, diff)
        errs, notes = check(src, out, parts, blob)
        rep = {'base': base, 'enabled': len(enabled), 'bytes': [len(src0), len(out)], 'notes': notes, 'errors': errs, 'out': None}
        if errs: print(json.dumps(rep, indent=1)); raise SystemExit('menu check FAILED (%d errors)' % len(errs))
        if not a.check_only:
            od = a.out_dir or os.path.dirname(os.path.abspath(base))
            dest = os.path.abspath(os.path.join(od, variant_name(base)))
            if os.path.abspath(dest).lower().startswith(os.path.abspath(dd).lower() + os.sep): raise SystemExit('refusing to write into the game folder: ' + dest)
            os.makedirs(od, exist_ok=True)
            new = []
            for e in ents:
                if e is fe[0]:
                    ne = entry_from_bytes(e.name, out.encode('latin1'), like=e); ne.flags = e.flags; ne.ver = e.ver; new.append(ne)
                else: new.append(e)
            write_zip(dest + '.tmp', new); os.replace(dest + '.tmp', dest)
            back = {e.name: read_entry(e) for e in read_zip(dest)}
            for e in ents:
                want = out.encode('latin1') if e is fe[0] else read_entry(e)
                if back.get(e.name) != want: raise SystemExit('read-back mismatch in %s' % e.name)
            rep['out'] = dest
        reps.append(rep)
    print(json.dumps(reps, indent=1))

if __name__ == '__main__':
    main()
