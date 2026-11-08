r"""DM11B (Hasta) look fix, STAGED ONLY (11-08): two independent, switchable changes on the live DM11B archive.

Owner: 'the rooms load by chunks have massive lens glare effects' and 'the green lighting that happens outside'.
DATA (live F04_Main.zip b755b505, scratch copy):
 GLARE. Three ADD-blend volumes in the End Room / End Corridor rooms are absurdly large (vertex extents in world units, 
  alpha ff = full strength): mesh 24214 (MAT 804, vertex chunk 24211, 9 vertices, 14390 x 14668 x 10859), mesh 24218 (MAT 804, chunk 24215,
  9 vertices, 4760 x 13066 x 5575), mesh 24210 (MAT 818, chunk 24207, 20 vertices, 11581 x 6716 x 8803). The rooms are ~1000 units tall, so
  the camera is inside these volumes in the whole room and the additive layer washes the screen white when the room's group is drawn
  (rooms stream in by chunk = the glare appears as a room loads). PROVEN: they exist, are ADD, are that big. GUESS: they are what draws
  the glare in game (no bench was possible, owner playing).
 GREEN. The scene's CameraBackgroundColor is 0x00fffad2 (bytes d2 fa ff 00): every stock Dog Days map is dark or grey (F01 110f0a, F04
  c7c1b0, F09 c6d0c7 ...), DM11B's is a very bright pale cyan. PROVEN: the value. GUESS: it is the green/cyan cast outside (fog and
  backdrop colour; the 28 mint Omni_Right_Side lights c7fff9 are all INSIDE, Main Hall / End Room / End Corridor, so not the outside).
  No Dead Men colour grade is present (the one PostFilterBoxes record points at DD neutral set 56696), so a grade is ruled out.
CHANGES (each its own switch; the stage is 'on', UNDO.bat is 'off', both "(recommended on)"):
  --glow  zero the vertex colours of the three volumes (nothing moves, no id shifts)
  --fog   CameraBackgroundColor -> DD F04's c7c1b0 (a stock grey-blue)
  python kl_hastalook_1108.py [--live <DM11B dir>] [--out C:/kl_build_1024/hastalook_1108] [--no-glow] [--no-fog]
Never writes into the game folder."""
import hashlib, os, re, shutil, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G
import kl_skyline_1108 as S

LIVE = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\DM11B'
PRM, PRP = 'Scenes/Locations/F04/F04_Main.prm', 'Scenes/Locations/F04/F04_Main.prp'
VOLS = ((24211, 9), (24215, 9), (24207, 20))     # (vertex chunk, vertex count) of mesh 24214 / 24218 / 24210
STRIDE, COL = 40, 16
BG_OLD, BG_NEW = b'\x09\xd2\xfa\xff\x00', b'\x09\xc7\xc1\xb0\x00'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def patch_prm(raw):
    p, b = G.read(raw, 'dd'), bytearray(raw)
    for ch, n in VOLS:
        c = bytes(p.chunks[ch])
        if len(c) < n * STRIDE or raw.count(c) != 1:
            raise SystemExit('REFUSED: chunk %d is not %d vertices found once' % (ch, n))
        base = raw.find(c)
        for v in range(n):
            at = base + v * STRIDE + COL
            if b[at + 3] != 0xff:
                raise SystemExit('REFUSED: chunk %d vertex %d colour %s alpha is not ff' % (ch, v, b[at:at + 4].hex()))
            b[at:at + 4] = bytes(4)
    print('  3 glare volumes (%d vertices) colour -> 00000000' % sum(n for _, n in VOLS))
    return bytes(b)


def patch_prp(raw):
    if raw.count(BG_OLD) != 1:
        raise SystemExit('REFUSED: CameraBackgroundColor d2faff00 found %d times, not once' % raw.count(BG_OLD))
    print('  CameraBackgroundColor d2faff00 -> c7c1b000')
    return raw.replace(BG_OLD, BG_NEW)


def redo(src, dst, glow, fog):
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    out = []
    for n, d in members:
        if n == PRM and glow:
            d = patch_prm(d)
        elif n == PRP and fog:
            d = patch_prp(d)
        out.append((n, d))
    S.write_zip(dst, out, S.tex_level(src))
    return md5(dst)


def main(a):
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    live, out = get('--live', LIVE), get('--out', 'C:/kl_build_1024/hastalook_1108')
    glow, fog = '--no-glow' not in a, '--no-fog' not in a
    os.makedirs(out, exist_ok=True)
    for n in ('F04_Main.zip', 'F04_Main.bots.zip'):
        print(n, '(live md5 %s)' % md5(os.path.join(live, n)))
        print('  staged md5 %s' % redo(os.path.join(live, n), os.path.join(out, n), glow, fog))
    with open(os.path.join(out, 'F04_Main.bots.base.md5'), 'w') as f:
        f.write(md5(os.path.join(out, 'F04_Main.zip')) + '\n')
    shutil.copy2(os.path.join(live, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    files = []
    for n in ('F04_Main.zip', 'F04_Main.bots.zip', 'F04_Main.bots.base.md5', 'KLGuns.ini'):
        files.append((n, md5(os.path.join(live, n)), md5(os.path.join(out, n))))
    t = open('C:/kl_build_1024/citylights_1108/install.py', encoding='utf-8').read()
    t = re.sub(r"FILES = \[.*?\n\]\n", "FILES = [   # name, live md5 before, staged md5 after\n%s\n]\n" % '\n'.join("    (%r, %r, %r)," % f for f in files), t, flags=re.S)
    t = re.sub(r"MAP, TAG = 'DM05A', '[^']*'", "MAP, TAG = 'DM11B', '.before-hastalook1108'", t)
    t = re.sub(r"LIVE_ZIP_MD5 = '[0-9a-f]+'", "LIVE_ZIP_MD5 = '%s'" % files[0][1], t)
    t = t.replace("n == 'F01_Main.zip'", "n == 'F04_Main.zip'").replace('DM05A CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)', 'DM11B HASTALOOK1108 (tools/kl_hastalook_1108.py)').replace('DM05A', 'DM11B').replace('before-skyline1108', 'before-hastalook1108')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)
    open(os.path.join(out, 'UNDO.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo %*\r\npause\r\n')
    for n in sorted(os.listdir(out)):
        if os.path.isfile(os.path.join(out, n)):
            print('%-24s %s' % (n, md5(os.path.join(out, n))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
