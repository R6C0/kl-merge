r"""DM05A city lights trial (11-08), BENCH ONLY: the glowfar_1108 stage with Dead Men's dark backdrop towers given lit windows.

glowfar1108 (StreetGLOW alpha x 0.25, Far 80000) turned the cyan wall into a soft haze, but the city around the roof is still mostly black
(owner 11-07: 'show more of the city'). The skyline model at 60000 sits behind the Distance shell and cannot be moved in (wf_1712af80-9e2;
plan --tx 30439 --tz 940 clips map geometry, route clearance 78 m < 98). So light up the shell itself.
The shell's towers use Dead Men M06 backdrop materials of one texture family 'Backdrop_Buildings_01_M06' (128x256, same layout):
  01d (855, 856, 876): diffuse 1563 only (a pale day facade), no illumination -> drawn near black at night
  01i (857, 877):      diffuse 1564 + mapIllumination 1565 (window strips) + v4IlluminationColor 1 -> the lit towers in the shots
This trial points every mesh object of a 01d material at its 01i twin (855, 856 -> 857; 876 -> 877): the u16 material id at object +0x12
in the .prm, and the .MAT ref table recomputed with kl_texmat.material_refs (the stock rule, equal to the stored table before the edit).
No material, shader or texture changes: 857/877 and their .fxc are already in the map. GUESS: 1564/1565 share 1563's UV layout (same name, size).

  python kl_citylights_1108.py [--src C:/kl_build_1024/glowfar_1108] [--out C:/kl_build_1024/citylights_1108]
Never installs anything; kit citylights1108 (kl_bench_1106.py) swaps it in for one run."""
import os, re, shutil, struct, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_texmat as T
import kl_skyline_1108 as S
from kl_skyfog_1108 import md5

PRM, MAT = 'Scenes/Locations/F01/F01_Main.prm', 'Scenes/Locations/F01/F01_Main.MAT'
SWAP = {855: 857, 856: 857, 876: 877}
NAMES = {855: '01d', 856: '01d', 876: '01d', 857: '01i', 877: '01i'}


def objects(prm):
    """(object chunk offset, material id) of every model root's objects, as kl_texmat.material_refs walks them"""
    t, n = struct.unpack_from('<II', prm, 0)
    tab = [struct.unpack_from('<4I', prm, t + 16 * i) for i in range(n)]
    seen = set()
    for o, size, rc, _z in tab[1:]:
        if size < 0x1c or struct.unpack_from('<H', prm, o + 2)[0] != 7 or prm[o] >= 16:
            continue
        nobj, ot = struct.unpack_from('<II', prm, o + 0x14)
        if not (nobj and 0 < ot < n and tab[ot][1] >= 4 * nobj):
            continue
        for oi in struct.unpack_from('<%dI' % nobj, prm, tab[ot][0]):
            if 0 < oi < n and tab[oi][1] >= 0x14 and oi not in seen:
                seen.add(oi)
                yield tab[oi][0], struct.unpack_from('<H', prm, tab[oi][0] + 0x12)[0]


def patch(members):
    d = dict(members)
    prm, m = bytearray(d[PRM]), T.read_mat(d[MAT])
    if T.material_refs(bytes(prm), m.ninst) != list(m.refs):
        raise SystemExit('REFUSED: the stored .MAT ref table does not match the .prm before the edit')
    for i, fam in NAMES.items():
        if not (m.insts[i].name or '').endswith('Backdrop_Buildings_%s_M06' % fam):
            raise SystemExit('REFUSED: material %d is %s, not Backdrop_Buildings_%s_M06' % (i, m.insts[i].name, fam))
    k = 0
    for at, mid in list(objects(bytes(prm))):
        if mid in SWAP:
            struct.pack_into('<H', prm, at + 0x12, SWAP[mid]); k += 1
    m.refs[:] = T.material_refs(bytes(prm), m.ninst)
    print('  %d objects 01d -> 01i; refs %s' % (k, {i: m.refs[i] for i in sorted(NAMES)}))
    d[PRM], d[MAT] = bytes(prm), T.write_mat(m)
    return [(n, d[n]) for n, _ in members]


def redo(src, dst):
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    S.write_zip(dst, patch(members), S.tex_level(src))
    return md5(dst)


def main(a):
    get = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    src, out = get('--src', 'C:/kl_build_1024/glowfar_1108'), get('--out', 'C:/kl_build_1024/citylights_1108')
    tag = 'citylights1108'
    os.makedirs(out, exist_ok=True)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        print(n)
        print('  md5 %s' % redo(os.path.join(src, n), os.path.join(out, n)))
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w') as f:
        f.write(md5(os.path.join(out, 'F01_Main.zip')) + '\n')
    shutil.copy2(os.path.join(src, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    t = open(os.path.join(src, 'install.py'), encoding='utf-8').read()
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        old, new_ = md5(os.path.join(src, n)), md5(os.path.join(out, n))
        if t.count("'%s')" % old) != 1:
            raise SystemExit('REFUSED: install.py has no single staged pin %s for %s' % (old, n))
        t = t.replace("'%s')" % old, "'%s')" % new_)
    t, k = re.subn(r"TAG = 'DM05A', '\.before-[a-z0-9]+'", "TAG = 'DM05A', '.before-%s'" % tag, t)
    if k != 1:
        raise SystemExit('REFUSED: install.py has no single TAG line')
    t = re.sub(r'DM05A \w+1108 \(bench only\)', 'DM05A %s (bench only)' % tag.upper(), t)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for n in sorted(os.listdir(out)):
        print('%-24s %s' % (n, md5(os.path.join(out, n))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
