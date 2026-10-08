#!/usr/bin/env python3
"""
Build a Dead Men map as a Dog Days level archive, and install / restore it.

    python kl_package.py build   M01_FA_A F01     (Dead Men FA map -> Dog Days FA slot)
    python kl_package.py install F01              (backs up originals, then copies files in)
    python kl_package.py restore                  (puts every backed-up original back)

Inputs come from the work folder (kl_port_check.workdir): converted (entity data), build/FA (textures, models, materials),
./build/shared/union.fxc (shaders) and ./build/PC_Def.str (merged audio).
Sound definitions/banks are Dog Days' own for the slot until the sound converter is done.
Originals are moved (never deleted) into <Dog Days>/KL_PortBackup/.
"""
import os, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE
WORK = workdir()

DM_BASE = {'M01_FA_A': 'M01FAA', 'M02_FA_A': 'M02FAA', 'M03_FA_A': 'M03FAA', 'M06_FA_A': 'M06FAA'}
COPY_AS_IS = ['zgf', 'sup', 'HVK', 'sgp', 'sgd', 'hrd']
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
    bak = os.path.join(dd, BACKUP, 'Scenes', 'Locations', slot, slot + '_Main.zip')
    if os.path.isfile(bak):
        dd_zip = bak                               # the slot may already hold one of our builds
    out_zip = os.path.join(WORK, 'build', 'install', 'Scenes', 'Locations', slot, slot + '_Main.zip')
    os.makedirs(os.path.dirname(out_zip), exist_ok=True)
    pre = 'Scenes/Locations/%s/%s_Main' % (slot, slot)
    conv = os.path.join(WORK, 'build', 'FA', dm_level)
    with zipfile.ZipFile(src_zip) as s, zipfile.ZipFile(dd_zip) as o, \
            zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        sn = {n.rsplit('.', 1)[-1]: n for n in s.namelist() if '/%s_Main' % base in n}
        def put(name, data):
            z.writestr(name, data)
        for ext in COPY_AS_IS:
            put(pre + '.' + ext, s.read(sn[ext]))
        # Animations: Dead Men's .ANM cannot be read by Dog Days (clip headers are 0x50 bytes, Dog
        # Days' 0x68, and two offset fields differ; the load crashes in an event-name lookup at 79 %).
        # STOPGAP until it is converted: the slot's own .ANM. Only the clips both games name alike
        # exist in it, so Dead Men-only animations (the van, some civilians) are missing.
        put(pre + '.ANM', o.read([n for n in o.namelist() if n.endswith('.ANM')][0]))
        import struct, kl_gms, kl_oct, kl_rooms, kl_rtp
        dmc, ddc = kl_rtp.Schema.load('dm'), kl_rtp.Schema.load('dd')
        src_gms = kl_gms.unpack(s.read(sn['gms']))
        gms = kl_gms.convert(s.read(sn['gms']))
        put(pre + '.gms', gms)
        # The .oct, .rmi, .rmc and the gates in the .buf name entities by REF id, and ids follow
        # the cluster table: it has to come out as Dead Men had it.
        ct = struct.unpack_from('<I', src_gms, 0x14)[0]
        end = ct + 4 + 96 * struct.unpack_from('<I', src_gms, ct)[0]
        if kl_gms.unpack(gms)[ct:end] != src_gms[ct:end]:
            raise SystemExit('a retype in kl_gms.RETYPE moves entities to another pool: REF ids would be stale')
        tids = [e[1] for e in kl_gms.entities(src_gms)]
        dd_cls = ['ZROOM'] + [ddc.geoms[kl_gms.RETYPE.get(t, t)] for t in tids]
        # rooms that are retyped to groups must lose their trees in the .oct (see kl_oct.py)
        keep = [True] + ['ZROOM' in ddc.bases(c) for t, c in zip(tids, dd_cls[1:]) if 'ZROOM' in dmc.bases(dmc.geoms[t])]
        put(pre + '.oct', kl_oct.convert(s.read(sn['oct']), keep))
        if not all(keep):
            raise SystemExit('a Dead Men room is no longer a room: its .rmi/.rmc boxes would name a non-room')
        for ext in ('rmi', 'rmc'):
            put(pre + '.' + ext, kl_rooms.convert_index(s.read(sn[ext])))
        prp = open(os.path.join(WORK, 'converted', dm_level, base + '_Main.prp'), 'rb').read()
        prp, buf, ngates = kl_rooms.convert_gates(prp, dd_cls, ddc, s.read(sn['buf']))
        put(pre + '.prp', prp)
        put(pre + '.buf', buf)
        print('rooms: %d, gates converted: %d' % (len(keep), ngates))
        for ext in ('TEX', 'prm', 'MAT'):
            put(pre + '.' + ext, open(os.path.join(conv, base + '_Main.' + ext), 'rb').read())
        put(pre + '.fxc', open(os.path.join(WORK, 'build', 'shared', 'union.fxc'), 'rb').read())
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
    root = os.path.join(WORK, 'build', 'install')
    rel = os.path.join('Scenes', 'Locations', slot, slot + '_Main.zip')
    _backup_then_copy(dd, rel, os.path.join(root, rel))
    merged = os.path.join(WORK, 'build', 'PC_Def.str')
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
