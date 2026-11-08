r"""DM05A StreetGLOW trial (11-08), BENCH ONLY: a copy of the skyline_1108 stage with the StreetGLOW curtain's vertex colours zeroed.

skyfog1108 (scene fog) and postneutral1108 (colour grade) both left the cyan wall east of the roof pad unchanged, and its hard
straight edges say it is geometry. Research wf_933101f3-991: the first thing a ray from the pad hits at 33-39 m is the StreetGLOW
curtain (REF 25478, node 3851, vertex chunk 38553 = 85 vertices x 40 bytes), MAT 891 (flat white 2x2 texture, SCREEN blend,
colour 0.702/0.996/1.0). Its vertex colours (+16..+19) are opaque ffffffff at y=0 (the hard bottom edge), ffffff99 at 2256,
ffffff00 at 6526..9067. This trial writes 00000000 into all 85 vertex colours, in both zips' .prm (black RGB AND zero alpha: under
SCREEN neither then adds anything, whether or not the shader premultiplies; GUESS which one it does). Nothing moves, so no slot id shifts.

  python kl_streetglow_1108.py [--src C:/kl_build_1024/skyline_1108] [--out C:/kl_build_1024/streetglow_1108]
Wall gone = StreetGLOW is the wall (then fix the fade, MAT 891 gm_vAlphaFadeDistScaleOffset z -0.053 vs DD -1.105);
unchanged = MAT 891 v4DiffuseColor -> black next. Never installs anything; kit streetglow1108 (kl_bench_1106.py) swaps it in for one run."""
import os, shutil, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G
import kl_skyline_1108 as S
from kl_skyfog_1108 import md5

PRM = 'Scenes/Locations/F01/F01_Main.prm'
VERTS, NV, STRIDE, COL = 38553, 85, 40, 16       # StreetGLOW vertex chunk; vertex count; stride; colour offset
OLD = {b'\xff\xff\xff\xff', b'\xff\xff\xff\x99', b'\xff\xff\xff\x00'}


def patch(raw):
    c = bytes(G.read(raw, 'dd').chunks[VERTS])
    if len(c) != NV * STRIDE + 8 or raw.count(c) != 1:      # 3408 = 85 x 40 + 8 trailing bytes (meaning unknown, left alone)
        raise SystemExit('REFUSED: chunk %d (%d bytes) is not %d vertices found once in the .prm' % (VERTS, len(c), NV))
    base, b = raw.find(c), bytearray(raw)
    for v in range(NV):
        at = base + v * STRIDE + COL
        if bytes(b[at:at + 4]) not in OLD:
            raise SystemExit('REFUSED: vertex %d colour %s is not StreetGLOW\'s' % (v, b[at:at + 4].hex()))
        b[at:at + 4] = bytes(4)
    print('  %d StreetGLOW vertex colours -> 00000000' % NV)
    return bytes(b)


def redo(src, dst):
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    members = [(n, patch(d) if n == PRM else d) for n, d in members]
    S.write_zip(dst, members, S.tex_level(src))
    return md5(dst)


def main(a):
    get = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    src, out = get('--src', 'C:/kl_build_1024/skyline_1108'), get('--out', 'C:/kl_build_1024/streetglow_1108')
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
    t = t.replace("'.before-skyline1108'", "'.before-streetglow1108'").replace('DM05A SKYLINE 1108', 'DM05A STREETGLOW 1108 (bench only)')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for n in sorted(os.listdir(out)):
        print('%-24s %s' % (n, md5(os.path.join(out, n))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
