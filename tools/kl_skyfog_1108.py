r"""DM05A fog trial (11-08), BENCH ONLY: a copy of the skyline_1108 stage with Last Call's scene fog pushed out.

Bench skyeast1108 (shots 12/20, 04:45) looked east from the roof pad: a cyan fog wall ~100 m out, only the two nearest towers show,
so the city looks empty (owner 11-07: 'show more of the city there too'). The scene block (kl_graft TAKE, byte-identical to Dead Men's
M05_A) holds CameraFar 30000, CameraFogBegin 0.65, CameraFogFull 0.95; stock DD maps run Far 60000..139264 (F06 80000/0.05/1.0).
GUESS: Begin/Full are fractions of CameraFar (the stock values only make sense that way), so a larger Far pushes the fog AND the clip plane out.
This trial sets Far/Begin/Full from the command line (default 80000 / 0.65 / 1.5) in both zips' .prp; every other byte is the stage's.

  python kl_skyfog_1108.py [--far 80000] [--begin 0.65] [--full 1.5] [--src C:/kl_build_1024/skyline_1108] [--out C:/kl_build_1024/skyfog_1108]
Never installs anything; the bench kit skyfog1108 (kl_bench_1106.py) swaps it in for one run and puts the live files back."""
import hashlib, os, shutil, struct, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_skyline_1108 as S

PRP = 'Scenes/Locations/F01/F01_Main.prp'
OLD = (30000.0, 0.65, 0.95)       # Dead Men M05_A's values, as staged
STEP = 0x1a                       # one scene-block entry (7c 0c id .. 0a float) = 26 bytes: Far, Begin, Full follow each other


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def patch(prp, new):
    # 30000.0 also occurs elsewhere: the scene block is the one place where Far, Begin, Full follow each other one entry apart
    seq = lambda i: all(prp[i + k * STEP:i + k * STEP + 5] == b'\x0a' + struct.pack('<f', o) for k, o in enumerate(OLD))
    hits, i = [], prp.find(b'\x0a' + struct.pack('<f', OLD[0]))
    while i >= 0:
        hits += [i] if seq(i) else []
        i = prp.find(b'\x0a' + struct.pack('<f', OLD[0]), i + 1)
    if len(hits) != 1:
        raise SystemExit('REFUSED: the Far/Begin/Full run found %d times in the .prp, not once' % len(hits))
    i = hits[0]
    b = bytearray(prp)
    for k, (o, n) in enumerate(zip(OLD, new)):
        at = i + k * STEP
        if b[at] != 0x0a or abs(struct.unpack('<f', b[at + 1:at + 5])[0] - o) > 1e-4:
            raise SystemExit('REFUSED: entry %d at 0x%x is not 0a %g' % (k, at, o))
        b[at + 1:at + 5] = struct.pack('<f', n)
        print('  0x%06x %g -> %g' % (at, o, n))
    return bytes(b)


def redo(src, dst, new):
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    members = [(n, patch(d, new) if n == PRP else d) for n, d in members]
    S.write_zip(dst, members, S.tex_level(src))
    return md5(dst)


def main(a):
    get = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    new = (get('--far', 80000.0), get('--begin', 0.65), get('--full', 1.5))
    src, out = get('--src', 'C:/kl_build_1024/skyline_1108'), get('--out', 'C:/kl_build_1024/skyfog_1108')
    os.makedirs(out, exist_ok=True)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        print(n)
        print('  md5 %s' % redo(os.path.join(src, n), os.path.join(out, n), new))
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w') as f:     # the bots zip was built on this plain zip
        f.write(md5(os.path.join(out, 'F01_Main.zip')) + '\n')
    shutil.copy2(os.path.join(src, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    # the bench runs the stage's install.py: the source's, with its own backup tag and the new staged md5s (the live pins stay)
    t = open(os.path.join(src, 'install.py'), encoding='utf-8').read()
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        old, new_ = md5(os.path.join(src, n)), md5(os.path.join(out, n))
        if t.count("'%s')" % old) != 1:
            raise SystemExit('REFUSED: install.py has no single staged pin %s for %s' % (old, n))
        t = t.replace("'%s')" % old, "'%s')" % new_)
    t = t.replace("'.before-skyline1108'", "'.before-skyfog1108'").replace('DM05A SKYLINE 1108', 'DM05A SKYFOG 1108 (bench only)')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    for n in sorted(os.listdir(out)):
        print('%-24s %s' % (n, md5(os.path.join(out, n))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
