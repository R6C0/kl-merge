#!/usr/bin/env python3
r"""
Map-pool ICONS for the online lobby (mappool_1027a, track "random maps with the icons showing what maps in the pool"). Offline build, installs nothing.

    python kl_mappool.py build [<out folder>]     default <DM>\KL_PortTools\build\mappool_1027
    python kl_mappool.py check <out folder>       re-reads every built archive
    python kl_mappool.py thumbs [<out folder>]    only the hook overlay's thumbnails (klmappool_ov.c): <out>/overlay/<map>.kmi, 128 x 72, + overlay_ini.txt (build does this too)

WHAT IT BUILDS (one folder per pool: dm = Full Dead Men, dd = Full Dog Days, mix = Mix; sibling of kl_lobbynames.py, which it reuses)
  <out>\<pool>\Overlay\Scenes\kaneandlynch.zip   the menu scene + ONE new picture entity LobbyPool_<pool> (325 x 183): a grid of the thumbnail of
                                                 EVERY map in the pool (grid 4x3 / 4x3 / 5x5), and the six Title0k leaves of every language's .LOC
                                                 rewritten to the POOL LABEL ("Full Dead Men" / "Full Dog Days" / "Mix: Dead Men + Dog Days")
  <out>\<pool>\Overlay\Patch01.zip               menu/frontend.xml with all nine LobbyPictureF0k re-pointed at that entity, and the three Arcade lists
                                                 (HeistLevel, HeistLeaderboardScreen, HeistLocalLeaderboardScreen) turned into literal stock names
  <out>\preview\pool_<pool>.png                  what the lobby shows (not committed)
  <out>\manifest.json, <out>\install.py          md5 of the base and the variants; the installer the INSTALL bats call
  <out>\INSTALL_dm.bat INSTALL_dd.bat INSTALL_mix.bat UNDO.bat
WHY STATIC: the lobby picture is a toggler over the 9 slot pictures, its index is the replicated slot, and no safe live swap from the hook was found
(re\lobby_map_names.md). So the pool's picture is the same for every slot and is chosen at INSTALL time; klmappool.c's pool (host key Delete / ini)
must be the same one, otherwise the picture lies. The pool is the one klmappool.c builds: DM* folders = Dead Men, DD* folders and the stock levels
= Dog Days, read from KLHook.ini [Redirect] / [Redirect.N].
Base files: the pristine overlay (<file>.before-1025lobbynames if kl_lobbynames_install.py put a set over it, else the live file), read only.
"""
import json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_lobbynames as L
import kl_portraits as P

DM_ROOT = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
OUT = DM_ROOT + r'\KL_PortTools\build\mappool_1027'
TAG1025 = '.before-1025lobbynames'
POOLS = {'dm': 'Full Dead Men', 'dd': 'Full Dog Days', 'mix': 'Mix: Dead Men + Dog Days'}


def base_file(live):
    return live + TAG1025 if os.path.exists(live + TAG1025) else live


def read_rules(path=L.INI):
    """-> [(page, slot 'F03', folder)] for [Redirect] (page 0) and [Redirect.N]."""
    sect, out = None, []
    for line in open(path, 'rb').read().decode('latin-1').splitlines():
        line = line.split(';')[0].strip()
        m = re.match(r'\[Redirect(?:\.(\d))?\]$', line)
        if m:
            sect = int(m.group(1) or 0); continue
        if line.startswith('['):
            sect = None; continue
        if sect is not None and '=' in line:
            k, v = [x.strip() for x in line.split('=', 1)]
            if re.match(r'F\d\d$', k):
                out.append((sect, k, v))
    return out


def classify(folder):
    return 'dm' if folder.upper().startswith('DM') else 'dd' if folder.upper().startswith('DD') else 'other'


def pool_entries(rules):
    """-> {pool: [(label, slot, folder or None for the stock level, page)]}: the same membership as klmappool.c kmp_build/kmp_in_pool."""
    ent = {'dm': [], 'dd': [], 'mix': []}
    slots = sorted({s for _p, s, _f in rules})
    for s in slots:
        mine = [(p, f) for p, sl, f in rules if sl == s]
        if not any(p == 0 for p, _f in mine):
            ent['dd'].append(('stock ' + s, s, None, 0))
        for p, f in sorted(mine):
            if p == 1:
                continue
            ent[classify(f) if classify(f) != 'other' else 'mix'].append((f, s, f, p))
    ent['mix'] = ent['dm'] + ent['dd'] + ent['mix']
    return ent


def grid(cells, cols, rows, w=L.LW, h=L.LH, gap=2):
    px = bytearray(bytes((20, 20, 24, 255)) * (w * h))
    cw, ch = (w - gap * (cols - 1)) // cols, (h - gap * (rows - 1)) // rows
    for i, (sw, sh, spx) in enumerate(cells[:cols * rows]):
        small = L.resize(spx, sw, sh, cw, ch)
        ox, oy = (i % cols) * (cw + gap), (i // cols) * (ch + gap)
        for y in range(ch):
            px[((oy + y) * w + ox) * 4:((oy + y) * w + ox + cw) * 4] = small[y * cw * 4:(y + 1) * cw * 4]
    return px


def dims(n):
    for cols, rows in ((4, 3), (4, 4), (5, 4), (5, 5), (6, 5), (6, 6)):
        if cols * rows >= n:
            return cols, rows
    return 6, 6


DIGITS = {   # 5 x 7 digits for the cards ("DM07"): kl_lobbynames' font has letters only
    '0': '01110 10001 10011 10101 11001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00110 01000 10000 11111', '3': '11110 00001 00001 01110 00001 00001 11110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    'B': '11110 10001 10001 11110 10001 10001 11110',
}
L.FONT.update(DIGITS)


def make_pic_fn(z):
    """-> (pic(label, slot, folder), mappic, fake): the 325 x 183 picture of a map (cached in mappic by folder / 'stock'+slot)."""
    stockpic = {s: L.stock_picture(z, 'LevelPicture_' + s) for s in L.SLOTS}
    mappic, fake = {}, []

    def pic(label, slot, folder):
        key = folder or 'stock' + slot
        if key in mappic:
            return mappic[key]
        px = None
        if folder is None or (re.match(r'DD\d\d$', folder) and folder[2:] == slot[1:]):      # the stock map of the slot
            w, h, p0 = stockpic[slot]; px = (L.LW, L.LH, L.resize(p0, w, h, L.LW, L.LH))
        else:
            try:
                w, h, p0 = L.stock_picture(z, 'LevelPicture_' + folder); px = (L.LW, L.LH, L.resize(p0, w, h, L.LW, L.LH))
            except SystemExit:
                words = folder.upper()
                px = (L.LW, L.LH, L.card(L.LW, L.LH, [words], 8)); fake.append(folder)
        mappic[key] = px
        return px
    return pic, mappic, fake


THUMB_W, THUMB_H = 128, 72


def kmi_bytes(w, h, rgba):
    """The hook's image file (klmappool_ov.c): 'KMI1', u32 w, u32 h, then w*h*4 bytes B,G,R,A (D3DFMT_A8R8G8B8 little endian)."""
    import struct
    bgra = bytearray(len(rgba))
    bgra[0::4], bgra[1::4], bgra[2::4], bgra[3::4] = rgba[2::4], rgba[1::4], rgba[0::4], bytes([255]) * (w * h)
    return b'KMI1' + struct.pack('<II', w, h) + bytes(bgra)


def kmi_name(label):
    """Same rule as kmpo_file in klmappool_ov.h: the pool entry's name, every other character an underscore ('stock F03' -> 'stock_F03.kmi')."""
    return re.sub(r'[^A-Za-z0-9_.-]', '_', label) + '.kmi'


def write_thumbs(out, ent, pic, log=print):
    """One small picture per map of every pool -> <out>/overlay/<name>.kmi (+ overlay_ini.txt: the [MapPool] lines to paste). Same pictures as the lobby grid."""
    d = os.path.join(out, 'overlay'); os.makedirs(d, exist_ok=True)
    done = {}
    for pool in POOLS:
        for lab, s, f, _p in ent[pool]:
            n = kmi_name(lab)
            if n in done:
                continue
            w, h, px = pic(lab, s, f)
            small = L.resize(px, w, h, THUMB_W, THUMB_H)
            open(os.path.join(d, n), 'wb').write(kmi_bytes(THUMB_W, THUMB_H, small)); done[n] = lab
    open(os.path.join(d, 'overlay_ini.txt'), 'w').write('[MapPool]\nOverlay=1\nOverlayDir=%s\n' % d)
    log('overlay thumbnails: %d files in %s' % (len(done), d))
    return sorted(done)


def build(out=OUT, log=print):
    import zipfile as zf
    live_s, live_p = L.BASE_SCENE, L.BASE_PATCH
    bs, bp = base_file(live_s), base_file(live_p)
    L.BASE_SCENE, L.BASE_PATCH = bs, bp                      # kl_lobbynames reads these module globals
    os.makedirs(out, exist_ok=True)
    z, zp = zf.ZipFile(bs), zf.ZipFile(bp)
    rules = read_rules()
    ent = pool_entries(rules)
    pic, mappic, fake = make_pic_fn(z)

    write_thumbs(out, ent, pic, log)
    pics, pool_cells = [], {}
    for pool in POOLS:
        cells = [pic(lab, s, f) for lab, s, f, _p in ent[pool]]
        pool_cells[pool] = len(cells)
        if not cells:
            log('pool %s is EMPTY (no matching rules in %s): skipped' % (pool, L.INI)); continue
        cols, rows = dims(len(cells))
        pics.append(('LobbyPool_' + pool, L.LW, L.LH, grid(cells, cols, rows)))
    log('pools: ' + ', '.join('%s=%d maps [%s]' % (p, len(ent[p]), ' '.join(e[0] for e in ent[p])) for p in POOLS) + '; cards drawn for ' + (', '.join(fake) or 'none'))
    new = L.scene_members(bs, pics)
    stock_titles = L.loc_titles(z.read('Scenes/kaneandlynchEnglish.LOC'))
    xml0 = zp.read('menu/frontend.xml').decode('latin-1')
    man = {'base_scene': L.md5(bs), 'base_patch': L.md5(bp), 'live_scene': L.md5(live_s), 'live_patch': L.md5(live_p), 'pools': {}}
    for pool, label, in POOLS.items():
        if not pool_cells.get(pool):
            continue
        repl = {L.STEM + ext: data for ext, data in new.items()}
        names = {s[1:]: label for s in L.SLOTS}
        for i in z.infolist():
            if re.match(r'Scenes/kaneandlynch\w+\.LOC$', i.filename):
                repl[i.filename] = L.loc_set(z.read(i), names)
        sz = os.path.join(out, pool, 'Overlay', 'Scenes', 'kaneandlynch.zip')
        L.write_zip(bs, sz, repl)
        xml, lit = L.frontend_set(xml0, {s: 'LobbyPool_' + pool for s in L.SLOTS}, stock_titles)
        pz = os.path.join(out, pool, 'Overlay', 'Patch01.zip')
        L.write_zip(bp, pz, {'menu/frontend.xml': xml.encode('latin-1')})
        man['pools'][pool] = {'scene': L.md5(sz), 'patch': L.md5(pz), 'label': label, 'maps': [e[0] for e in ent[pool]]}
        log('%s: "%s", %d maps | %d Arcade list entries literal | %s %.1f MB' % (pool, label, len(ent[pool]), lit, sz, os.path.getsize(sz) / 1e6))
    os.makedirs(os.path.join(out, 'preview'), exist_ok=True)
    for n, w, h, px in pics:
        P.png_write(os.path.join(out, 'preview', n + '.png'), w, h, px)
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    write_installers(out)
    bad = check(out, log)
    if bad:
        raise SystemExit('check failed:\n  ' + '\n  '.join(bad))
    return man


INSTALL_PY = r'''r"""Map-pool icons for the online lobby (kl_mappool.py output; this file is <out>\install.py, called by the INSTALL / UNDO bats).
usage: python install.py --pool dm|dd|mix [--dry]    puts <pool>\Overlay\Scenes\kaneandlynch.zip + Patch01.zip over the LIVE overlay copies in <DD>\KLExpansion\Overlay
       python install.py --undo                      puts the first backup back (what was there before the first pool install)
Backups: <file>.before-1027mappool, made ONCE (an existing backup is never overwritten, never deleted except by UNDO moving it back).
Refuses while kl2.exe runs. Never touches KL_PortBackup. The pool shown must be the pool klmappool.c plays ([MapPool] Pool / host key Delete)."""
import hashlib, json, os, shutil, subprocess, sys
D = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OV = os.path.join(D, 'KLExpansion', 'Overlay')
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '.before-1027mappool'
FILES = [os.path.join('Scenes', 'kaneandlynch.zip'), 'Patch01.zip']
a = sys.argv[1:]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


if '--dry' not in a and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    sys.exit('kl2.exe is running: close the game first')
live = [os.path.join(OV, f) for f in FILES]
if '--undo' in a:
    for p in live:
        if os.path.exists(p + TAG):
            os.remove(p)
            os.rename(p + TAG, p)
            print('restored', p, md5(p))
        else:
            print('no backup for', p, '- nothing to restore')
    sys.exit()
if '--pool' not in a:
    sys.exit(__doc__)
man = json.load(open(os.path.join(HERE, 'manifest.json')))
name = a[a.index('--pool') + 1]
if name not in man['pools']:
    sys.exit('unknown pool ' + name)
want = man['pools'][name]
known = {man['live_scene'], man['live_patch'], man['base_scene'], man['base_patch']} | {v[k] for v in man['pools'].values() for k in ('scene', 'patch')}
for p in live:                                       # the live file is what the build saw, a pool of ours, or the pristine file
    assert md5(p) in known, 'live file changed since the build (rebuild with kl_mappool.py): ' + p
src = [os.path.join(HERE, name, 'Overlay', f) for f in FILES]
for p, h in zip(src, (want['scene'], want['patch'])):
    assert md5(p) == h, 'built file changed: ' + p
if '--dry' in a:
    print('dry: checks pass; would install pool', name, want['label'], want['maps'])
    sys.exit()
for p, s in zip(live, src):
    if not os.path.exists(p + TAG):
        os.rename(p, p + TAG)
    elif os.path.exists(p):
        os.remove(p)                                 # the live file is replaced; the FIRST backup stays
    shutil.copyfile(s, p)
    print('installed pool', name, p, md5(p)[:8])
print('undo: UNDO.bat')
'''

BAT_INSTALL = r'''@echo off
rem Map-pool icons: pool "%POOL%". Replaces KLExpansion\Overlay\Scenes\kaneandlynch.zip + Patch01.zip (first backup kept as *.before-1027mappool).
rem Refuses while the game runs. Turn the matching pool on in KLHook.ini ([MapPool] Enable=1, Pool=%N%) so the icons tell the truth.
tasklist /FI "IMAGENAME eq kl2.exe" 2>nul | find /I "kl2.exe" >nul
if not errorlevel 1 (echo kl2.exe is running: close the game first. & exit /b 1)
cd /d "%~dp0"
python install.py --pool %POOL%
pause
'''

BAT_UNDO = r'''@echo off
rem Puts the overlay files back from *.before-1027mappool (refuses while the game runs).
tasklist /FI "IMAGENAME eq kl2.exe" 2>nul | find /I "kl2.exe" >nul
if not errorlevel 1 (echo kl2.exe is running: close the game first. & exit /b 1)
cd /d "%~dp0"
python install.py --undo
pause
'''


def write_installers(out):
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(INSTALL_PY)
    for i, pool in enumerate(POOLS, 1):
        open(os.path.join(out, 'INSTALL_%s.bat' % pool), 'w', newline='\r\n').write(BAT_INSTALL.replace('%POOL%', pool).replace('%N%', str(i)))
    open(os.path.join(out, 'UNDO.bat'), 'w', newline='\r\n').write(BAT_UNDO)


def check(out=OUT, log=print):
    man = json.load(open(os.path.join(out, 'manifest.json')))
    bad = []
    base = zipfile.ZipFile(base_file(L.BASE_SCENE))
    stock = L.loc_titles(base.read('Scenes/kaneandlynchEnglish.LOC'))
    for pool, info in man['pools'].items():
        sz = os.path.join(out, pool, 'Overlay', 'Scenes', 'kaneandlynch.zip'); pz = os.path.join(out, pool, 'Overlay', 'Patch01.zip')
        z, p = zipfile.ZipFile(sz), zipfile.ZipFile(pz)
        if z.testzip() or p.testzip():
            bad.append(pool + ': zip crc')
        if L.md5(sz) != info['scene'] or L.md5(pz) != info['patch']:
            bad.append(pool + ': md5 differs from the manifest')
        xml = p.read('menu/frontend.xml').decode('latin-1')
        for s in L.SLOTS:
            if 'Name="LobbyPicture%s"' % s not in xml:
                bad.append('%s: LobbyPicture%s missing' % (pool, s))
        if xml.count('Graphic="LobbyPool_%s"' % pool) != 9:
            bad.append('%s: expected 9 pictures named LobbyPool_%s, found %d' % (pool, pool, xml.count('Graphic="LobbyPool_%s"' % pool)))
        t = L.loc_titles(z.read('Scenes/kaneandlynchEnglish.LOC'))
        if any(t.get('%02d' % k) != info['label'] for k in range(1, 10)):
            bad.append('%s: English Title leaves are not the pool label: %s' % (pool, t))
        hl = re.search(r'Name="HeistLevel" .*?</GuiElement>', xml, re.S)
        if not hl or 'Scenarios/Title' in hl.group(0):
            bad.append(pool + ': HeistLevel still reads the LOC (Arcade would show the pool label)')
    log('check: %d problems' % len(bad))
    return bad


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if a and a[0] == 'build':
        build(a[1] if len(a) > 1 else OUT)
    elif a and a[0] == 'thumbs':
        o = a[1] if len(a) > 1 else OUT
        os.makedirs(o, exist_ok=True)
        write_thumbs(o, pool_entries(read_rules()), make_pic_fn(zipfile.ZipFile(base_file(L.BASE_SCENE)))[0])
    elif a and a[0] == 'check':
        for b in check(a[1] if len(a) > 1 else OUT):
            print('  ' + b)
    else:
        print(__doc__); sys.exit(1)
