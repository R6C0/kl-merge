"""flatraidname_1111: Flat Raid shows 'The Vault' and no picture on the Arcade 'Dead Men campaign' page.
CAUSE: [Lobby] Rows12=1 makes the game open Overlay\\Patch01_rows12*.zip (log: 'MountFirst ... Patch01_rows12_deadmen.zip'), and those 4 files were built
before the 11-05 Flat Raid fix: page 3 entries 6/7 have no pictures (H05 placeholder) and entry 7 reads the stock Title07 = 'The Vault'.
FIX: only these 3 spots of menu/frontend.xml, in each of the 4 rows12 zips: + H06/H07_LevelPicture_P3 (L06 = The Dig, L05 = Flat Raid), the toggler's
entries 6/7 -> them, entry 7 text -> '%Flat Raid' (exactly what Patch01.zip has). Nothing else changes (+2 GUI elements per file).
python install.py [--undo] [--dry]. Refuses while kl2.exe runs or when a file is not the pinned one. Backups *.before-flatraidname1111."""
import hashlib, os, shutil, subprocess, sys, zipfile

OV = os.environ.get('KL_OV') or r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Overlay'
FILES = {'Patch01_rows12.zip': '', 'Patch01_rows12_campui.zip': '', 'Patch01_rows12_deadmen.zip': '', 'Patch01_rows12_deadmen_campui.zip': ''}
PIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pins.txt')
TAG = '.before-flatraidname1111'
XML = 'menu/frontend.xml'
PIC5 = '        <GuiElement Type="Graphic" Name="H05_LevelPicture_P3" Template="LevelPicture_T" Graphic="LevelPicture_H05" />\r\n'
PICS = ('        <GuiElement Type="Graphic" Name="H06_LevelPicture_P3" Template="LevelPicture_T" Graphic="LevelPicture_L06" />\r\n'
        '        <GuiElement Type="Graphic" Name="H07_LevelPicture_P3" Template="LevelPicture_T" Graphic="LevelPicture_L05" />\r\n')
TOG4 = '        <Graphic Graphic="H04_LevelPicture_P3" />\r\n'
TOG5 = '        <Graphic Graphic="H05_LevelPicture_P3" />\r\n'
TOG67 = '        <Graphic Graphic="H06_LevelPicture_P3" />\r\n        <Graphic Graphic="H07_LevelPicture_P3" />\r\n'
DIG = '        <Text Text="%The Dig" />\r\n'
T07 = '        <Text Text="/Menu/Online/Scenarios/Title07" />\r\n'
FLAT = '        <Text Text="%Flat Raid" />\r\n'


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]


def running():
    ps = 'Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 } | Measure-Object | ForEach-Object Count'
    return subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.strip() not in ('', '0')


def once(t, old, new):
    if t.count(old) != 1:
        raise SystemExit('REFUSED: anchor found %d times: %r' % (t.count(old), old[:70]))
    return t.replace(old, new)


def patch(xml):
    t = xml.decode('latin1')
    if 'H07_LevelPicture_P3' in t:
        raise SystemExit('REFUSED: already has H07_LevelPicture_P3')
    t = once(t, PIC5, PIC5 + PICS)
    t = once(t, TOG4 + TOG5 + TOG5, TOG4 + TOG67)
    t = once(t, DIG + T07, DIG + FLAT)
    return t.encode('latin1')


def rewrite(src, dst):
    with zipfile.ZipFile(src) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    with zipfile.ZipFile(dst, 'w') as o:
        for i, data in items:
            o.writestr(i, patch(data) if i.filename == XML else data, compress_type=i.compress_type)


def main(a):
    if [x for x in a if x not in ('--undo', '--dry')]:
        print('REFUSED: unknown argument(s)', a)
        return 2
    dry = '--dry' in a
    pins = dict(l.split() for l in open(PIN)) if os.path.isfile(PIN) else {}
    if not dry and running():
        print('REFUSED: the game is running; close it first')
        return 1
    if '--undo' in a:
        for n in FILES:
            p = os.path.join(OV, n)
            if not os.path.isfile(p + TAG):
                print('REFUSED: no backup', p + TAG); return 1
            if md5(p) != pins.get(n + '.new'):
                print('REFUSED: %s is %s, not this kit\'s %s' % (n, md5(p), pins.get(n + '.new'))); return 1
        for n in FILES:
            p = os.path.join(OV, n)
            if not dry:
                os.replace(p + TAG, p)
            print('undone' if not dry else 'would undo', n, md5(p if dry else p))
        return 0
    for n in FILES:
        p = os.path.join(OV, n)
        if pins and md5(p) != pins.get(n):
            print('REFUSED: %s is %s, pinned %s' % (n, md5(p), pins.get(n))); return 1
        if os.path.exists(p + TAG):
            print('REFUSED: backup already there', p + TAG); return 1
    for n in FILES:
        p = os.path.join(OV, n)
        tmp = p + '.flatraidname1111.tmp'
        rewrite(p, tmp)
        if dry:
            print('would install', n, md5(p), '->', md5(tmp)); os.remove(tmp); continue
        shutil.copy2(p, p + TAG)
        os.replace(tmp, p)
        print('installed', n, md5(p + TAG), '->', md5(p))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
