r"""DM05A post-filter trial (11-08), BENCH ONLY: a copy of the skyline_1108 stage with Dead Men's colour grade switched off.

skyfog1108 (Far 80000, FogFull 1.5) left the cyan wall east of the roof pad unchanged, so the scene fog floats are not the cause.
Next suspect (research wf_5acf84d5-df8): the 20 PostFilterBoxes (scene block -> .prm chunk 53850, 20 x 88-byte records) point at
Dead Men's filter sets 53844..53849, whose floats 21..24 hold bluish values (53845 = 0.34 0.34 0.51 0.61).
The same .prm holds set 33189: Dog Days' neutral set (float 17 = 1, floats 21..24 = 0, identity curves).
This trial points every box's set (u32 at +0x30, GUESS: the set's chunk id, the values match 53844..53849 exactly) at 33189,
in both zips' .prm; every other byte is the stage's.

  python kl_postneutral_1108.py [--set 33189] [--src C:/kl_build_1024/skyline_1108] [--out C:/kl_build_1024/postneutral_1108]
Wall gone = the grade is the cause (then bisect the sets, 53845 first); unchanged = try FogMax 0 and a raw shot.
Never installs anything; the bench kit postneutral1108 (kl_bench_1106.py) swaps it in for one run and puts the live files back."""
import os, shutil, struct, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G
import kl_skyline_1108 as S
from kl_skyfog_1108 import md5

PRM = 'Scenes/Locations/F01/F01_Main.prm'
BOXES, REC, AT = 53850, 88, 0x30          # PostFilterBoxes chunk of the DM05A scene block; record size; set id offset
OLD = set(range(53844, 53850))            # Dead Men M05_A's filter sets, as staged


def patch(raw, to):
    prm = G.read(raw, 'dd')
    if len(prm.chunks[to] or b'') != 176:
        raise SystemExit('REFUSED: chunk %d is not a 176-byte filter set' % to)
    c = bytes(prm.chunks[BOXES])
    if len(c) % REC or raw.count(c) != 1:
        raise SystemExit('REFUSED: box chunk %d (%d bytes) not found exactly once in the .prm' % (BOXES, len(c)))
    base, b = raw.find(c), bytearray(raw)
    for r in range(len(c) // REC):
        at = base + r * REC + AT
        s = struct.unpack_from('<I', b, at)[0]
        if s not in OLD:
            raise SystemExit('REFUSED: box %d points at %d, not a Dead Men set' % (r, s))
        struct.pack_into('<I', b, at, to)
    print('  %d boxes -> set %d' % (len(c) // REC, to))
    return bytes(b)


def redo(src, dst, to):
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    members = [(n, patch(d, to) if n == PRM else d) for n, d in members]
    S.write_zip(dst, members, S.tex_level(src))
    return md5(dst)


def main(a):
    get = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    to = get('--set', 33189)
    src, out = get('--src', 'C:/kl_build_1024/skyline_1108'), get('--out', 'C:/kl_build_1024/postneutral_1108')
    os.makedirs(out, exist_ok=True)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        print(n)
        print('  md5 %s' % redo(os.path.join(src, n), os.path.join(out, n), to))
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w') as f:
        f.write(md5(os.path.join(out, 'F01_Main.zip')) + '\n')
    shutil.copy2(os.path.join(src, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    t = open(os.path.join(src, 'install.py'), encoding='utf-8').read()
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        old, new_ = md5(os.path.join(src, n)), md5(os.path.join(out, n))
        if t.count("'%s')" % old) != 1:
            raise SystemExit('REFUSED: install.py has no single staged pin %s for %s' % (old, n))
        t = t.replace("'%s')" % old, "'%s')" % new_)
    t = t.replace("'.before-skyline1108'", "'.before-postneutral1108'").replace('DM05A SKYLINE 1108', 'DM05A POSTNEUTRAL 1108 (bench only)')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for n in sorted(os.listdir(out)):
        print('%-24s %s' % (n, md5(os.path.join(out, n))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
