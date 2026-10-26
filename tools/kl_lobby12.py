"""
kl_lobby12.py - FALobby with 12 player rows (re/lobby_12rows.md).

Reads <DD>\\KLExpansion\\Overlay\\Patch01.zip (the live overlay menu; falls back to <DD>\\Patch01.zip) and writes
<DD>\\KLExpansion\\Overlay\\Patch01_rows12.zip: the same archive with menu/frontend.xml changed in the window
FALobby only. klslot.c answers an open of Patch01.zip with that file while [Lobby] Rows12=1 and the file is not
older than Overlay\\Patch01.zip (so rebuild it after kl_lobbynames / kl_expansion rebuild the overlay).

What changes inside <Window Name="FALobby"> (the same window serves Fragile Alliance, Undercover Cop and, with
TeamIndex elements, Cops and Robbers):
  * the plain player list had PlayerIndex 0..7 in seven column groups (ready tick, not-ready tick, speaker, name,
    trust, play style, rank): PlayerIndex 8..11 are appended to each. The code behind the tags is index driven
    (kl2 0x631b56 / 0x58c238: 'PlayerIndex >= connected count' -> empty) and has no cap of 8.
  * the list is 8 x 32 px = 256 px tall in a box that ends at Y 545, so 12 rows need a row pitch of 20: the groups'
    GeomSpace (the gap added to the font / icon height, re/hud_board.md) 16 -> 4 (text), 14 -> 2 (ready ticks,
    18 px icons), 0 -> -12 (speaker icons, 32 px). GUESS: pitch = height + GeomSpace; negative GeomSpace accepted.
  * the row separators (Line_Long_01#02..#09 at Y 320 + 32k) become Line_Long_01#02..#13 at Y 308 + 20k.
  * the static fake focus bars LobbyFB#01.. / LobbyTeamFB#.. are moved to the new pitch; the selector's moving bar
    gets FocusBarBaseY 289 and FocusBarDeltaY 20 (GUESS: the selector places the bar at base + index * delta).
  * rows 9..12 get no FocusGraphic (all FocusBar_Long_02 instances are in use): the mouse cannot hover them.
  * rows 9..12 have NO ready / not-ready / speaker pictures (reusing the team instances #09..#12 crashed, S1 10-26):
    stock never names one #NN instance twice within a window, and FALobby already uses every FAStatus instance.
The team lists keep their six rows per column; they are compressed to the same pitch.

    python tools/kl_lobby12.py [--game <DD folder>] [--base <Patch01.zip>] [--out <zip>] [--check]
"""
import argparse, hashlib, os, re, sys, zipfile

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
PITCH = 20
NEW_GEOM = {'16': '4', '14': '2', '0': '-12'}
EXTRA = [8, 9, 10, 11]


def window_span(xml, name):
    m = re.search(r'<Window Name="%s"[^>]*>' % re.escape(name), xml)
    if not m:
        raise SystemExit('window %s not found' % name)
    e = xml.index('</Window>', m.end()) + len('</Window>')
    return m.start(), e


def transform(win):
    # 1. selector: moving focus bar base / delta
    n = 0
    def sel(m):
        nonlocal n
        n += 1
        s = m.group(0)
        s = s.replace('FocusBarBaseY="290"', 'FocusBarBaseY="289"').replace('FocusBarDeltaY="32"', 'FocusBarDeltaY="%d"' % PITCH)
        return s
    win = re.sub(r'<GuiElement Type="MercsFASelectorLobby"[^>]*>', sel, win)
    assert n == 1 and 'FocusBarDeltaY="20"' in win, 'selector element not found'

    # 2. fake focus bars: Y = 290 + 32 k -> 289 + 20 k
    def fb(m):
        y = int(m.group(2))
        return m.group(1) + str(289 + (y - 290) // 32 * PITCH) + m.group(3)
    win = re.sub(r'(<GuiElement Type="Graphic" Name="Lobby(?:Team)?FB#\d+"[^>]*? Y=")(\d+)(")',
                 lambda m: fb(m) if 290 <= int(m.group(2)) <= 514 else m.group(0), win)

    # 3. separators: replace the eight lines by twelve
    lines = re.findall(r'[ \t]*<GuiElement AnimX="385" Template="Line" Graphic="Line_Long_01#\d\d" AnimY="\d+" />\r?\n', win)
    assert len(lines) == 8, len(lines)
    nl = '\r\n' if lines[0].endswith('\r\n') else '\n'
    new = ''.join('      <GuiElement AnimX="385" Template="Line" Graphic="Line_Long_01#%02d" AnimY="%d" />%s' % (2 + k, 308 + PITCH * k, nl) for k in range(12))
    first = win.index(lines[0])
    for l in lines:
        win = win.replace(l, '', 1)
    win = win[:first] + new + win[first:]

    # 4. column groups of the list: GeomSpace to the new pitch; plain groups get rows 8..11
    def group(m):
        head, body = m.group(1), m.group(2)
        gs = re.search(r'GeomSpace="(-?\d+)"', head)
        if not gs or gs.group(1) not in NEW_GEOM:
            return m.group(0)
        if not re.search(r' Y="(296|297|290)"', head):
            return m.group(0)
        head = head.replace('GeomSpace="%s"' % gs.group(1), 'GeomSpace="%s"' % NEW_GEOM[gs.group(1)], 1)
        if 'TeamIndex=' not in body:
            kids = re.findall(r'[ \t]*<GuiElement Template="(Lobby\w+_T)"[^>]*PlayerIndex="7"[^>]*/>', body)
            if len(kids) == 1:
                last = re.search(r'([ \t]*)<GuiElement Template="(Lobby\w+_T)"([^>]*)PlayerIndex="7"([^>]*)/>', body)
                ind, tpl, pre, post = last.groups()
                add = ''
                for k, idx in enumerate(EXTRA):
                    pre2 = pre
                    post2 = post
                    if re.search(r'Graphic="FAStatus_(?:Ready|ReadyNot|Speak)#\d+"', pre2 + post2):
                        # S1 (2026-10-26) live: reusing the team lists' FAStatus_*#09..#12 in the same window
                        # asserted at kl2 0x51f1a9 ('FAStatus_Ready#18' not found) and crashed at 0x4be312 on
                        # SystemLinkCreate. Stock never names one instance twice within a window and FALobby
                        # already uses every instance, so rows 9..12 get no ready / speaker icon.
                        continue
                    post2 = re.sub(r'FadeInDelay="[\d.]+"', 'FadeInDelay="%.2f"' % (0.80 + 0.05 * k), post2)
                    pre2 = re.sub(r'FadeInDelay="[\d.]+"', 'FadeInDelay="%.2f"' % (0.80 + 0.05 * k), pre2)
                    post2 = re.sub(r'\s*FocusGraphic="[^"]*"', '', post2)
                    add += '%s<GuiElement Template="%s"%sPlayerIndex="%d"%s/>\n' % (ind, tpl, pre2, idx, post2)
                body = body.replace(last.group(0), last.group(0) + '\n' + add.rstrip('\n'), 1)
        return head + body + '</GuiElement>'
    a = win.index('Ready tick boxes')
    b = win.index('IsLevelAvailableLobby')
    mid = re.sub(r'(<GuiElement Type="GUIGroup" GeomSpace="(?:16|14|0)" Y="(?:296|297|290)"[^>]*>)((?:(?!</GuiElement>).)*)</GuiElement>',
                 group, win[a:b], flags=re.S)
    return win[:a] + mid + win[b:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=DD)
    ap.add_argument('--base')
    ap.add_argument('--out')
    ap.add_argument('--check', action='store_true', help='transform and print a summary, write nothing')
    a = ap.parse_args()
    ov = os.path.join(a.game, 'KLExpansion', 'Overlay')
    base = a.base or (os.path.join(ov, 'Patch01.zip') if os.path.isfile(os.path.join(ov, 'Patch01.zip')) else os.path.join(a.game, 'Patch01.zip'))
    out = a.out or os.path.join(ov, 'Patch01_rows12.zip')
    zin = zipfile.ZipFile(base)
    xml = zin.read('menu/frontend.xml').decode('latin-1')
    s, e = window_span(xml, 'FALobby')
    win = xml[s:e]
    new = transform(win)
    print('FALobby %d -> %d bytes; PlayerIndex 8..11 elements added: %d' % (len(win), len(new),
          len(re.findall(r'PlayerIndex="(?:8|9|10|11)"', new)) - len(re.findall(r'PlayerIndex="(?:8|9|10|11)"', win))))
    if a.check:
        return
    xml2 = (xml[:s] + new + xml[e:]).encode('latin-1')
    tmp = out + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for i in zin.infolist():
            data = xml2 if i.filename == 'menu/frontend.xml' else zin.read(i.filename)
            zo.writestr(i, data, compress_type=i.compress_type)
    os.replace(tmp, out)
    print(out, hashlib.md5(open(out, 'rb').read()).hexdigest())


if __name__ == '__main__':
    main()
