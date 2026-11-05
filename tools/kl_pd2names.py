#!/usr/bin/env python3
"""kl_pd2names.py - Payday 2 names and descriptions for the Page II guns of the Dog Days shop. OFFLINE; never writes the game folder.

The shop page II rows (klhook/klshoppage.c reads KLShopPage.ini: Pairs Pn=carrierRow|item|picRow|NAME, Desc Dn) carry a
name per Dead Men item. This rewrites those names and the one-line description to the nearest Payday 2 gun. DATA ONLY:
the hook already reads name (47 chars max, shown in the shop's name line) and desc (479 chars max, '\\n' = newline), so
no KLHook.ini toggle is needed (the page itself is [ShopPage] Enable).

    python tools/kl_pd2names.py stage [out_dir] [--live INI]   write out_dir/KLShopPage.ini + INSTALL/UNDO bats
                                                               (default <work>/build/pd2names_1105, live = the Dog Days one)
    python tools/kl_pd2names.py check [staged.ini] [--live INI] diff staged vs live (names, desc), exit 1 on a problem
    python tools/kl_pd2names.py show                           the table

PD2 names: every one marked VERIFIED was found as an English display string in Payday 2's strings/blackmarket
(extracted with tools/pd2_crate.py: `extract strings/blackmarket strings <file>`; e.g. "AK.762 Rifle", "KSP Light
Machine Gun", "HRL-7 Rocket Launcher", "GL40 Grenade Launcher", "RPK Light Machine Gun", "R700 Sniper Rifle",
"Bernetti 9 Pistol", "Chimano 88 Pistol", "AK Rifle", "Gewehr 3 Rifle"). GUESS = the name exists but the pairing
with the Dead Men gun is my choice, or the suffix is ours.
Shop font: upper-case ASCII, at most 18 characters (the longest stock page II name is 17).
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAXNAME = 18
MAXDESC = 479

# item -> (new name, status, PD2 flavour line)
PD2 = {
    62: ('CHIMANO 88 SHIELD', 'GUESS pairing (name verified)', 'Payday 2 sidearm: the Chimano 88 pistol. Held up behind a hostage.'),
    63: ('BERNETTI 9 SHIELD', 'VERIFIED (Beretta 92 = Bernetti 9)', 'Payday 2 sidearm: the Bernetti 9 pistol. Held up behind a hostage.'),
    54: ('GL40 FLARE', 'VERIFIED name, FLARE suffix ours', 'Payday 2 launcher: the GL40, loaded with a flare. Lights the sky, burns a little.'),
    53: ('GL40 GAS', 'VERIFIED name, GAS suffix ours', 'Payday 2 launcher: the GL40, loaded with gas. Clears a room.'),
    52: ('GL40', 'VERIFIED', 'Payday 2 launcher: the GL40 grenade launcher. One 40 mm grenade at a time.'),
    51: ('HRL-7 HIND', 'VERIFIED name, HIND suffix ours', 'Payday 2 rocket launcher: the HRL-7, helicopter pod version.'),
    50: ('HRL-7', 'VERIFIED', 'Payday 2 rocket launcher: the HRL-7. Not for the faint-hearted.'),
    45: ('KSP HELI P', 'VERIFIED name, suffix ours', 'Payday 2 light machine gun: the KSP, door-mounted, taken off its mount.'),
    47: ('KSP', 'VERIFIED', 'Payday 2 light machine gun: the KSP, lifted from an army depot.'),
    46: ('KSP L10', 'VERIFIED name, suffix ours', 'Payday 2 light machine gun: the KSP, rooftop stock.'),
    48: ('KSP HELI', 'VERIFIED name, suffix ours', 'Payday 2 light machine gun: the KSP, door-mounted, taken off its mount.'),
    42: ('RPK HELI', 'VERIFIED name, pairing GUESS', 'Payday 2 light machine gun: the RPK, door-mounted, taken off its mount.'),
    43: ('RPK HELI P', 'VERIFIED name, pairing GUESS', 'Payday 2 light machine gun: the RPK, door-mounted, taken off its mount.'),
    41: ('RPK L09', 'VERIFIED name, pairing GUESS; PD2 RPK model on the DM maps (pd2guns_1105)', 'Payday 2 light machine gun: the RPK. Belt of lead from a long barrel.'),
    40: ('RPK', 'VERIFIED name, pairing GUESS', 'Payday 2 light machine gun: the RPK, belt-fed and heavy.'),
    44: ('EAGLE HEAVY', 'VERIFIED name (PD2 SCAR-H = MK17 model on the DM maps, pd2guns_1105)', 'Payday 2 battle rifle: the Eagle Heavy. Heavy rounds, held like a machine gun.'),
    33: ('AK.762', 'VERIFIED (the AKM; owner asked for "the ak from payday")', 'Payday 2 assault rifle: the AK.762. Plain, rugged and everywhere.'),
    35: ('LITTLE FRIEND 7.62', 'VERIFIED name; GUESS that the chico NPC sg417 model on the DM maps (pd2guns_1105) is this rifle', 'Payday 2 rifle: the Little Friend 7.62, long barrel, long reach.'),
    38: ('JP36', 'VERIFIED name (PD2 G36 model on the DM maps, pd2guns_1105)', 'Payday 2 assault rifle: the JP36. Compact, light and quick.'),
    49: ('R700', 'VERIFIED', 'Payday 2 sniper rifle: the R700. A hunting rifle with a long reach.'),
}

TAIL = re.compile(r'(Page II: sold in the .+? row, same price, same rank\.)$')
HEAD = re.compile(r'^(Police reg\.: [^\\]+?)\\n(.*?)\. Origin: ([A-Za-z]+)\. ')
PAIR = re.compile(r'^(P(\d+))=(\d+)\|(\d+)\|(\d+)\|(.*)$')


def work():
    import kl_port_check
    return kl_port_check.workdir()


def default_out():
    return os.path.join(work(), 'build', 'pd2names_1105')


def live_ini():
    return os.path.join(GAME, 'KLShopPage.ini')


def rewrite(text):
    """KLShopPage.ini text -> (new text, [(item, old name, new name)]). Unknown items are left alone."""
    out, log, items = [], [], {}
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines()
    for ln in lines:
        m = PAIR.match(ln)
        if m:
            items[int(m.group(2))] = int(m.group(4))
    for ln in lines:
        m = PAIR.match(ln)
        if m and int(m.group(4)) in PD2:
            it = int(m.group(4))
            out.append('%s=%s|%d|%s|%s' % (m.group(1), m.group(3), it, m.group(5), PD2[it][0]))
            log.append((it, m.group(6), PD2[it][0]))
            continue
        d = re.match(r'^D(\d+)=(.*)$', ln)
        if d and items.get(int(d.group(1))) in PD2:
            it = items[int(d.group(1))]
            body = d.group(2)
            t = TAIL.search(body)
            h = HEAD.match(body)
            if t and h:
                kind = h.group(2)
                body = '%s\\n%s. %s %s' % (h.group(1), kind, PD2[it][2], t.group(1))
                if len(body.replace('\\n', '\n')) > MAXDESC:
                    raise ValueError('description of item %d is %d chars (max %d)' % (it, len(body), MAXDESC))
            elif 'Payday 2' not in body:
                raise ValueError('description D%s has an unexpected shape: %r' % (d.group(1), body[:60]))
            out.append('D%s=%s' % (d.group(1), body))
            continue
        out.append(ln)
    return nl.join(out) + nl, log


def parse(text):
    names, descs, items = {}, {}, {}
    for ln in text.splitlines():
        m = PAIR.match(ln)
        if m:
            items[int(m.group(2))] = int(m.group(4)); names[int(m.group(4))] = m.group(6)
        d = re.match(r'^D(\d+)=(.*)$', ln)
        if d:
            descs[int(d.group(1))] = d.group(2)
    bi = {n: it for n, it in items.items()}
    return names, {items[n]: s for n, s in descs.items() if n in items}


def problems(text):
    p = []
    names, descs = parse(text)
    for it, nm in names.items():
        if len(nm) > MAXNAME or not re.match(r'^[A-Z0-9 .\-]+$', nm):
            p.append('item %d name %r: over %d chars or outside upper-case ASCII' % (it, nm, MAXNAME))
    if len(set(names.values())) != len(names):
        p.append('two rows share a name: %r' % sorted(n for n in names.values() if list(names.values()).count(n) > 1))
    for it, ds in descs.items():
        if len(ds.replace('\\n', '\n')) > MAXDESC:
            p.append('item %d description too long' % it)
        if not TAIL.search(ds):
            p.append('item %d description lost its "Page II: sold in" tail' % it)
    return p


BAT_INSTALL = r'''@echo off
rem INSTALL pd2names: Payday 2 names on the shop page II rows (KLShopPage.ini only, data; no dll change).
rem Backs up the live KLShopPage.ini as KLShopPage.ini.before-pd2names (UNDO restores it). Close the game first.
set G=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days
tasklist /fi "imagename eq kl2.exe" | find /i "kl2.exe" >nul && (echo kl2.exe is running: close it first & exit /b 1)
if exist "%G%\KLShopPage.ini.before-pd2names" (echo KLShopPage.ini.before-pd2names exists: run UNDO first & exit /b 1)
if not exist "%G%\KLShopPage.ini" (echo no live KLShopPage.ini: install shop page II first & exit /b 1)
copy /y "%G%\KLShopPage.ini" "%G%\KLShopPage.ini.before-pd2names" >nul || exit /b 1
copy /y "%~dp0KLShopPage.ini" "%G%\KLShopPage.ini" >nul || exit /b 1
echo Installed the Payday 2 names. UNDO pd2names.bat puts the old ini back.
'''
BAT_UNDO = r'''@echo off
set G=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days
tasklist /fi "imagename eq kl2.exe" | find /i "kl2.exe" >nul && (echo kl2.exe is running: close it first & exit /b 1)
if not exist "%G%\KLShopPage.ini.before-pd2names" (echo nothing to undo & exit /b 1)
copy /y "%G%\KLShopPage.ini.before-pd2names" "%G%\KLShopPage.ini" >nul || exit /b 1
del "%G%\KLShopPage.ini.before-pd2names"
echo Restored the old KLShopPage.ini.
'''


def stage(out, live):
    with open(live, 'r', newline='') as f:
        src = f.read()
    new, log = rewrite(src)
    pr = problems(new)
    if pr:
        raise ValueError('; '.join(pr))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'KLShopPage.ini'), 'w', newline='') as f:
        f.write(new)
    with open(os.path.join(out, 'INSTALL pd2names.bat'), 'w', newline='') as f:
        f.write(BAT_INSTALL.replace('\n', '\r\n'))
    with open(os.path.join(out, 'UNDO pd2names.bat'), 'w', newline='') as f:
        f.write(BAT_UNDO.replace('\n', '\r\n'))
    return log


def check(staged, live):
    a = open(live, 'r', newline='').read()
    b = open(staged, 'r', newline='').read()
    na, da = parse(a)
    nb, db = parse(b)
    n = 0
    for it in sorted(na):
        if na[it] != nb.get(it):
            n += 1
            print('item %d: %s -> %s' % (it, na[it], nb.get(it)))
        if da.get(it) != db.get(it):
            print('        desc: %s' % (db.get(it) or '')[:110])
    pr = problems(b)
    for x in pr:
        print('PROBLEM: ' + x)
    print('%d names differ, %d problems' % (n, len(pr)))
    return 1 if pr else 0


def main(argv):
    a = [x for x in argv[1:] if not x.startswith('--')]
    live = live_ini()
    if '--live' in argv:
        live = argv[argv.index('--live') + 1]
        a = [x for x in a if x != live]
    cmd = a[0] if a else 'show'
    if cmd == 'stage':
        out = a[1] if len(a) > 1 else default_out()
        for it, o, n in stage(out, live):
            print('%2d  %-18s -> %-18s %s' % (it, o, n, PD2[it][1]))
        print('staged in ' + out)
        return 0
    if cmd == 'check':
        return check(a[1] if len(a) > 1 else os.path.join(default_out(), 'KLShopPage.ini'), live)
    for it, (n, s, f) in sorted(PD2.items()):
        print('%2d  %-18s %s' % (it, n, s))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
