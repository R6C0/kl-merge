#!/usr/bin/env python3
"""
Build a Dead Men map as a Dog Days level archive, and install / restore it.

    python kl_package.py build   M01_FA_A F01     (Dead Men FA map -> Dog Days FA slot)
    python kl_package.py install F01              (backs up originals, then copies files in)
    python kl_package.py restore                  (puts every backed-up original back)

Inputs come from ./converted (entity data), ./build/FA (textures, models, materials),
./build/shared/union.fxc (shaders) and ./build/PC_Def.str (merged audio).
Sound definitions/banks are Dog Days' own for the slot until the sound converter is done.
Originals are moved (never deleted) into <Dog Days>/KL_PortBackup/.
"""
import os, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

DM_BASE = {'M01_FA_A': 'M01FAA', 'M02_FA_A': 'M02FAA', 'M03_FA_A': 'M03FAA', 'M06_FA_A': 'M06FAA'}
COPY_AS_IS = ['zgf', 'sup', 'HVK', 'ANM', 'buf', 'oct', 'sgp', 'rmc', 'rmi', 'sgd', 'hrd']
LANGS = ['English', 'German', 'French', 'Spanish', 'Italian', 'Dutch', 'Russian', 'Polish', 'Japanese']
BACKUP = 'KL_PortBackup'


def games():
    dm, dd = find(DM_GUESSES, DM_EXE), find(DD_GUESSES, DD_EXE)
    if not dm or not dd:
        raise SystemExit('Could not find both games; edit DM_GUESSES / DD_GUESSES in kl_port_check.py')
    return dm, dd


def build(dm_level, slot, dm=None, dd=None):
    if not dm:
        dm, dd = games()
    base = DM_BASE[dm_level]
    src_zip = os.path.join(dm, 'Scenes', 'Locations', dm_level, base + '_Main.zip')
    dd_zip = os.path.join(dd, 'Scenes', 'Locations', slot, slot + '_Main.zip')
    out_zip = os.path.join(HERE, 'build', 'install', 'Scenes', 'Locations', slot, slot + '_Main.zip')
    os.makedirs(os.path.dirname(out_zip), exist_ok=True)
    pre = 'Scenes/Locations/%s/%s_Main' % (slot, slot)
    conv = os.path.join(HERE, 'build', 'FA', dm_level)
    with zipfile.ZipFile(src_zip) as s, zipfile.ZipFile(dd_zip) as o, \
            zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        sn = {n.rsplit('.', 1)[-1]: n for n in s.namelist() if '/%s_Main' % base in n}
        def put(name, data):
            z.writestr(name, data)
        for ext in COPY_AS_IS:
            put(pre + '.' + ext, s.read(sn[ext]))
        import kl_gms
        put(pre + '.gms', kl_gms.convert(s.read(sn['gms'])))
        put(pre + '.prp', open(os.path.join(HERE, 'converted', dm_level, base + '_Main.prp'), 'rb').read())
        for ext in ('TEX', 'prm', 'MAT'):
            put(pre + '.' + ext, open(os.path.join(conv, base + '_Main.' + ext), 'rb').read())
        put(pre + '.fxc', open(os.path.join(HERE, 'build', 'shared', 'union.fxc'), 'rb').read())
        eng = s.read([n for n in s.namelist() if n.endswith('English.LOC')][0])
        for lang in LANGS:
            mine = [n for n in s.namelist() if n.endswith(lang + '.LOC')]
            put('%s%s.LOC' % (pre, lang), s.read(mine[0]) if mine else eng)
        # Dog Days UI files and (for now) the slot's own sound definitions
        for n in o.namelist():
            if n.lower().endswith('.xml') or n.endswith('.SND'):
                put(n, o.read(n))
    print('built', out_zip, '%.0f MB' % (os.path.getsize(out_zip) / 1e6))
    return out_zip


def _backup_then_copy(dd, rel, src):
    dst = os.path.join(dd, rel)
    bak = os.path.join(dd, BACKUP, rel)
    if os.path.exists(dst) and not os.path.exists(bak):
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        os.replace(dst, bak)                       # move original into the backup folder
        print('backed up', rel)
    shutil.copyfile(src, dst)
    print('installed', rel)


def install(slot, dd=None):
    if not dd:
        _, dd = games()
    root = os.path.join(HERE, 'build', 'install')
    rel = os.path.join('Scenes', 'Locations', slot, slot + '_Main.zip')
    _backup_then_copy(dd, rel, os.path.join(root, rel))
    merged = os.path.join(HERE, 'build', 'PC_Def.str')
    if os.path.isfile(merged):
        _backup_then_copy(dd, 'PC_Def.str', merged)


def restore(dd=None):
    if not dd:
        _, dd = games()
    broot = os.path.join(dd, BACKUP)
    for dp, _, fs in os.walk(broot):
        for f in fs:
            bak = os.path.join(dp, f)
            rel = os.path.relpath(bak, broot)
            os.replace(bak, os.path.join(dd, rel))
            print('restored', rel)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] not in ('build', 'install', 'restore'):
        print(__doc__); sys.exit(1)
    if a[0] == 'build':
        build(a[1] if len(a) > 1 else 'M01_FA_A', a[2] if len(a) > 2 else 'F01')
    elif a[0] == 'install':
        install(a[1] if len(a) > 1 else 'F01')
    else:
        restore()
