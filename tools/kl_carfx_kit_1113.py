"""kl_carfx_kit_1113.py - stage the BLACK BOX fix (kl_fa_carfx 'apply': the Dead Men HeatShimmer mesh off) on the LIVE Dead Men maps
that still draw it, as one install kit (2026-11-13; tester pictures: an opaque black trapezoid round a burning police car).

  python tools/kl_carfx_kit_1113.py --plain <dir with <MAP>/F0x_Main.zip made by kl_fa_carfx apply> --out <kit dir> [--game <DD folder>]

Per map: the plain zip comes from `kl_fa_carfx.py apply` (only the .prm member differs, one or three vertex chunks); the .bots.zip is the
LIVE bots zip with that same .prm member put in (proven: live bots zip == live plain zip but for the .prp, and the new .prm is the plain
one); .bots.base.md5 = md5 of the new plain zip. Nothing is written into the game folder. Writes install.py (pins every live md5, backups are
HARD LINKS so no extra disk, --undo, --dry), INSTALL.bat, UNDO.bat, README.txt, pins.json."""
import hashlib, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_graft

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = ['DM01B', 'DM05A', 'DM06B', 'DM07', 'DM11B']


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def members(p):
    with zipfile.ZipFile(p) as z:
        return [(n, z.read(n)) for n in z.namelist()]


def slot_of(d):
    z = [f for f in os.listdir(d) if f.endswith('_Main.zip')]
    if len(z) != 1:
        raise ValueError('%s: expected one *_Main.zip' % d)
    return z[0][:-len('_Main.zip')]


def main(a):
    arg = lambda k, dflt=None: a[a.index(k) + 1] if k in a else dflt
    plain, out, game = arg('--plain'), arg('--out'), arg('--game', GAME)
    if not plain or not out:
        print(__doc__); return 2
    pins = {}
    for m in MAPS:
        live = os.path.join(game, 'KLExpansion', 'Maps', m)
        pd = os.path.join(plain, m)
        s = slot_of(pd)
        lz, lb, lbase = (os.path.join(live, s + e) for e in ('_Main.zip', '_Main.bots.zip', '_Main.bots.base.md5'))
        nz = os.path.join(pd, s + '_Main.zip')
        L, N, LB = members(lz), members(nz), members(lb)
        if [n for n, _ in L] != [n for n, _ in N] or [n for n, _ in L] != [n for n, _ in LB]:
            raise ValueError('%s: member lists differ' % m)
        ch = [n for (n, x), (_, y) in zip(L, N) if x != y]
        if len(ch) != 1 or not ch[0].endswith('.prm'):
            raise ValueError('%s: plain differs in %s (want only .prm)' % (m, ch))
        prm = ch[0]
        diffb = [n for (n, x), (_, y) in zip(L, LB) if x != y]
        if diffb != [n for n in diffb if n.endswith('.prp')]:
            raise ValueError('%s: live bots zip differs from live plain in more than the .prp: %s' % (m, diffb))
        nb = [(n, dict(N)[prm] if n == prm else d) for n, d in LB]
        od = os.path.join(out, 'files', m)
        os.makedirs(od, exist_ok=True)
        bz = kl_graft.write_zip(os.path.join(od, s + '_Main.bots.zip'), nb)
        pz = os.path.join(od, s + '_Main.zip')
        if os.path.exists(pz):
            os.remove(pz)
        os.link(nz, pz)
        with open(os.path.join(od, s + '_Main.bots.base.md5'), 'wb') as f:
            f.write((md5(pz) + '\n').encode('ascii'))
        # verify the written bots zip: only the .prm differs from the live bots zip
        W = members(bz)
        if [n for (n, x), (_, y) in zip(LB, W) if x != y] != [prm]:
            raise ValueError('%s: bots zip differs in more than the .prm' % m)
        pins[m] = dict(slot=s, files=[[s + e, md5(os.path.join(live, s + e)), md5(os.path.join(od, s + e))]
                                      for e in ('_Main.zip', '_Main.bots.zip', '_Main.bots.base.md5')])
        print(m, s, [(f[0], f[1][:8], f[2][:8]) for f in pins[m]['files']])
    json.dump(pins, open(os.path.join(out, 'pins.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
